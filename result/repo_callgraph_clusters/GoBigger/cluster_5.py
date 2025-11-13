# Cluster 5

class Server:

    @staticmethod
    def default_config():
        cfg = copy.deepcopy(server_default_config)
        return EasyDict(cfg)

    def __init__(self, cfg=None, seed=None):
        self.cfg = Server.default_config()
        if isinstance(cfg, dict):
            cfg = EasyDict(cfg)
            self.cfg = deep_merge_dicts(self.cfg, cfg)
        self.update_match_ratio()
        logging.debug(self.cfg)
        self.team_num = self.cfg.team_num
        self.player_num_per_team = self.cfg.player_num_per_team
        self.map_width = self.cfg.map_width
        self.map_height = self.cfg.map_height
        self.frame_limit = self.cfg.frame_limit
        self.fps = self.cfg.fps
        self.frame_duration = 1 / self.fps
        self.collision_detection_type = self.cfg.collision_detection_type
        self.eat_ratio = self.cfg.eat_ratio
        self.playback_settings = self.cfg.playback_settings
        self.opening_settings = self.cfg.opening_settings
        self.manager_settings = self.cfg.manager_settings
        self.obs_settings = self.cfg.obs_settings
        self.seed(seed)
        self.border = Border(0, 0, self.map_width, self.map_height, self._random)
        self.last_frame_count = 0
        self.init_playback()
        self.init_opening()
        self.sequence_generator = SequenceGenerator()
        self.food_manager = FoodManager(self.manager_settings.food_manager, border=self.border, random_generator=self._random, sequence_generator=self.sequence_generator)
        self.thorns_manager = ThornsManager(self.manager_settings.thorns_manager, border=self.border, random_generator=self._random, sequence_generator=self.sequence_generator)
        self.spore_manager = SporeManager(self.manager_settings.spore_manager, border=self.border, random_generator=self._random, sequence_generator=self.sequence_generator)
        self.player_manager = PlayerManager(self.manager_settings.player_manager, border=self.border, team_num=self.team_num, player_num_per_team=self.player_num_per_team, spore_manager_settings=self.cfg.manager_settings.spore_manager, random_generator=self._random, sequence_generator=self.sequence_generator)
        self.init_obs()
        self.collision_detection = create_collision_detection(self.collision_detection_type, border=self.border)

    def update_match_ratio(self):
        self.cfg.map_width = int(self.cfg.map_width * math.sqrt(self.cfg.match_ratio))
        self.cfg.map_height = int(self.cfg.map_height * math.sqrt(self.cfg.match_ratio))
        self.cfg.manager_settings.food_manager.num_init = int(self.cfg.manager_settings.food_manager.num_init * self.cfg.match_ratio)
        self.cfg.manager_settings.food_manager.num_min = int(self.cfg.manager_settings.food_manager.num_min * self.cfg.match_ratio)
        self.cfg.manager_settings.food_manager.num_max = int(self.cfg.manager_settings.food_manager.num_max * self.cfg.match_ratio)
        self.cfg.manager_settings.thorns_manager.num_init = int(self.cfg.manager_settings.thorns_manager.num_init * self.cfg.match_ratio)
        self.cfg.manager_settings.thorns_manager.num_min = int(self.cfg.manager_settings.thorns_manager.num_min * self.cfg.match_ratio)
        self.cfg.manager_settings.thorns_manager.num_max = int(self.cfg.manager_settings.thorns_manager.num_max * self.cfg.match_ratio)

    def init_playback(self):
        self.diff_balls_remove = [[], [], [], []]
        self.diff_balls_modify = [{}, {}, {}, {}]
        self.playback_type = self.playback_settings.playback_type
        self.save_video = self.playback_settings.by_video.save_video
        self.save_frame = self.playback_settings.by_frame.save_frame
        self.playback_util = create_pb(self.playback_settings, fps=self.fps, map_width=self.map_width, map_height=self.map_height)

    def init_opening(self):
        self.custom_init_food = []
        self.custom_init_thorns = []
        self.custom_init_spore = []
        self.custom_init_clone = []
        opening_type = self.opening_settings.opening_type
        if opening_type == 'none':
            pass
        elif opening_type == 'handcraft':
            self.custom_init_food = self.opening_settings.handcraft.food
            self.custom_init_thorns = self.opening_settings.handcraft.thorns
            self.custom_init_spore = self.opening_settings.handcraft.spore
            self.custom_init_clone = self.opening_settings.handcraft.clone
        elif opening_type == 'from_frame':
            if self.frame_path and os.path.isfile(self.frame_path):
                with open(self.frame_path, 'rb') as f:
                    data = pickle.load(f)
                self.custom_init_food = data['food']
                self.custom_init_thorns = data['thorns']
                self.custom_init_spore = data['spore']
                self.custom_init_clone = data['clone']

    def init_obs(self):
        self.eats = {player_id: {'food': 0, 'thorns': 0, 'spore': 0, 'clone_self': 0, 'clone_team': 0, 'clone_other': 0, 'eaten': 0} for player_id in self.player_manager.get_player_names()}
        self.player_states_util = PlayerStatesUtil(self.obs_settings)

    def spawn_balls(self):
        """
        Overview:
            Initialize all balls. If self.custom_init is set, initialize all balls based on it.
        """
        self.food_manager.init_balls(custom_init=self.custom_init_food)
        self.thorns_manager.init_balls(custom_init=self.custom_init_thorns)
        self.spore_manager.init_balls(custom_init=self.custom_init_spore)
        self.player_manager.init_balls(custom_init=self.custom_init_clone)
        if self.save_frame:
            for ball in self.food_manager.get_balls():
                self.diff_balls_modify[0][ball.ball_id] = ball.save()
            for ball in self.thorns_manager.get_balls():
                self.diff_balls_modify[1][ball.ball_id] = ball.save()
            for ball in self.spore_manager.get_balls():
                self.diff_balls_modify[2][ball.ball_id] = ball.save()
            for ball in self.player_manager.get_balls():
                self.diff_balls_modify[3][ball.ball_id] = ball.save()

    def step_one_frame(self, actions=None):
        moving_balls = []
        total_balls = []
        if actions is not None and isinstance(actions, dict):
            for player in self.player_manager.get_players():
                if player.player_id in actions:
                    direction_x, direction_y, action_type = actions[player.player_id]
                    if direction_x is None or direction_y is None:
                        direction = None
                    else:
                        direction = Vector2(direction_x, direction_y)
                        if direction.length() > 1:
                            direction = direction.normalize()
                    if action_type == 1:
                        tmp_spore_balls = player.eject(direction=direction)
                        for tmp_spore_ball in tmp_spore_balls:
                            if tmp_spore_ball:
                                self.spore_manager.add_balls(tmp_spore_ball)
                                if self.save_frame:
                                    self.diff_balls_modify[2][tmp_spore_ball.ball_id] = tmp_spore_ball.save()
                    elif action_type == 2:
                        self.player_manager.add_balls(player.split(direction=direction))
                    player.move(direction=direction, duration=self.frame_duration)
                    moving_balls.extend(player.get_balls())
                else:
                    player.move(duration=self.frame_duration)
                    moving_balls.extend(player.get_balls())
        else:
            for player in self.player_manager.get_players():
                player.move(duration=self.frame_duration)
                moving_balls.extend(player.get_balls())
        moving_balls = sorted(moving_balls, reverse=True)
        for thorns_ball in self.thorns_manager.get_balls():
            if thorns_ball.moving:
                thorns_ball.move(duration=self.frame_duration)
                if self.save_frame:
                    self.diff_balls_modify[1][thorns_ball.ball_id] = thorns_ball.save()
            moving_balls.append(thorns_ball)
        for spore_ball in self.spore_manager.get_balls():
            if spore_ball.moving:
                spore_ball.move(duration=self.frame_duration)
                if self.save_frame:
                    self.diff_balls_modify[2][spore_ball.ball_id] = spore_ball.save()
        eats = self.player_manager.adjust()
        for player_id, clone_self_num in eats.items():
            self.eats[player_id]['clone_self'] += clone_self_num
        total_balls.extend(self.player_manager.get_balls())
        total_balls.extend(self.thorns_manager.get_balls())
        total_balls.extend(self.spore_manager.get_balls())
        total_balls.extend(self.food_manager.get_balls())
        collisions_dict = self.collision_detection.solve(moving_balls, total_balls)
        for index, moving_ball in enumerate(moving_balls):
            if not moving_ball.is_remove and index in collisions_dict:
                for target_ball in collisions_dict[index]:
                    self.deal_with_collision(moving_ball, target_ball)
        new_food_balls = self.food_manager.step(duration=self.frame_duration)
        new_thorns_balls = self.thorns_manager.step(duration=self.frame_duration)
        self.spore_manager.step(duration=self.frame_duration)
        self.player_manager.step()
        self.last_frame_count += 1
        if self.save_frame:
            self.diff_balls_modify[0].update(new_food_balls)
            self.diff_balls_modify[1].update(new_thorns_balls)
            for ball in self.player_manager.get_balls():
                self.diff_balls_modify[3][ball.ball_id] = ball.save()

    def deal_with_collision(self, moving_ball, target_ball):
        if not moving_ball.is_remove and (not target_ball.is_remove):
            if isinstance(moving_ball, CloneBall):
                if isinstance(target_ball, CloneBall):
                    if moving_ball.team_id != target_ball.team_id:
                        if moving_ball.score > target_ball.score and self.can_eat(moving_ball.score, target_ball.score):
                            moving_ball.eat(target_ball)
                            self.eats[moving_ball.player_id]['clone_other'] += 1
                            self.eats[target_ball.player_id]['eaten'] += 1
                            self.player_manager.remove_balls(target_ball)
                        elif self.can_eat(target_ball.score, moving_ball.score):
                            target_ball.eat(moving_ball)
                            self.eats[target_ball.player_id]['clone_other'] += 1
                            self.eats[moving_ball.player_id]['eaten'] += 1
                            self.player_manager.remove_balls(moving_ball)
                    elif moving_ball.player_id != target_ball.player_id:
                        if moving_ball.score > target_ball.score and self.can_eat(moving_ball.score, target_ball.score):
                            if self.player_manager.get_clone_num(target_ball) > 1:
                                moving_ball.eat(target_ball)
                                self.eats[moving_ball.player_id]['clone_team'] += 1
                                self.eats[target_ball.player_id]['eaten'] += 1
                                self.player_manager.remove_balls(target_ball)
                        elif self.can_eat(target_ball.score, moving_ball.score):
                            if self.player_manager.get_clone_num(moving_ball) > 1:
                                target_ball.eat(moving_ball)
                                self.eats[target_ball.player_id]['clone_team'] += 1
                                self.eats[moving_ball.player_id]['eaten'] += 1
                                self.player_manager.remove_balls(moving_ball)
                elif isinstance(target_ball, FoodBall):
                    moving_ball.eat(target_ball)
                    self.eats[moving_ball.player_id]['food'] += 1
                    if self.save_frame:
                        self.diff_balls_remove[0].append(target_ball.ball_id)
                    self.food_manager.remove_balls(target_ball)
                elif isinstance(target_ball, SporeBall):
                    moving_ball.eat(target_ball)
                    self.eats[moving_ball.player_id]['spore'] += 1
                    if self.save_frame:
                        self.diff_balls_remove[2].append(target_ball.ball_id)
                    self.spore_manager.remove_balls(target_ball)
                elif isinstance(target_ball, ThornsBall):
                    if moving_ball.score > target_ball.score and self.can_eat(moving_ball.score, target_ball.score):
                        ret = moving_ball.eat(target_ball, clone_num=self.player_manager.get_clone_num(moving_ball))
                        self.eats[moving_ball.player_id]['thorns'] += 1
                        if self.save_frame:
                            self.diff_balls_remove[1].append(target_ball.ball_id)
                        self.thorns_manager.remove_balls(target_ball)
                        if isinstance(ret, list):
                            self.player_manager.add_balls(ret)
            elif isinstance(moving_ball, ThornsBall):
                if isinstance(target_ball, CloneBall):
                    if moving_ball.score < target_ball.score and self.can_eat(target_ball.score, moving_ball.score):
                        ret = target_ball.eat(moving_ball, clone_num=self.player_manager.get_clone_num(target_ball))
                        self.eats[target_ball.player_id]['thorns'] += 1
                        if self.save_frame:
                            self.diff_balls_remove[1].append(moving_ball.ball_id)
                        self.thorns_manager.remove_balls(moving_ball)
                        if isinstance(ret, list):
                            self.player_manager.add_balls(ret)
                elif isinstance(target_ball, SporeBall):
                    moving_ball.eat(target_ball)
                    if self.save_frame:
                        self.diff_balls_remove[2].append(target_ball.ball_id)
                    self.spore_manager.remove_balls(target_ball)
            elif isinstance(moving_ball, SporeBall):
                if isinstance(target_ball, CloneBall) or isinstance(target_ball, ThornsBall):
                    target_ball.eat(moving_ball)
                    if isinstance(target_ball, CloneBall):
                        self.eats[target_ball.player_id]['spore'] += 1
                    if self.save_frame:
                        self.diff_balls_remove[2].append(moving_ball.ball_id)
                        if isinstance(target_ball, ThornsBall):
                            self.diff_balls_modify[1][target_ball.ball_id] = target_ball.save()
                    self.spore_manager.remove_balls(moving_ball)
        else:
            return

    def can_eat(self, score1, score2):
        if score1 > self.eat_ratio * score2:
            return True
        else:
            return False

    def reset(self):
        self.last_frame_count = 0
        self.init_playback()
        self.init_opening()
        self.food_manager.reset()
        self.thorns_manager.reset()
        self.spore_manager.reset()
        self.player_manager.reset()
        self.spawn_balls()
        self.init_obs()
        self._end_flag = False

    def step(self, actions=None, save_frame_full_path='', **kwargs):
        if not self._end_flag:
            self.step_one_frame(actions)
            if self.playback_util.need_save(self.last_frame_count):
                if self.save_video:
                    self.playback_util.save_step(food_balls=self.food_manager.get_balls(), thorns_balls=self.thorns_manager.get_balls(), spore_balls=self.spore_manager.get_balls(), players=self.player_manager.get_players(), player_num_per_team=self.player_num_per_team)
                elif self.save_frame:
                    self.playback_util.save_step(diff_balls_remove=self.diff_balls_remove, diff_balls_modify=self.diff_balls_modify, leaderboard=self.leaderboard, last_frame_count=self.last_frame_count)
                    self.diff_balls_remove = [[], [], [], []]
                    self.diff_balls_modify = [{}, {}, {}, {}]
        if self.last_frame_count >= self.frame_limit:
            if not self._end_flag:
                self.playback_util.save_final(self.cfg)
            self._end_flag = True
        return self._end_flag

    def obs(self, obs_type='all'):
        assert obs_type in ['all', 'single']
        global_state = self.get_global_state()
        player_states = self.player_states_util.get_player_states(food_balls=self.food_manager.get_balls(), thorns_balls=self.thorns_manager.get_balls(), spore_balls=self.spore_manager.get_balls(), players=self.player_manager.get_players())
        self.leaderboard = global_state['leaderboard']
        return (global_state, player_states, {'eats': self.eats})

    def get_global_state(self):
        team_name_score = self.player_manager.get_teams_score()
        global_state = {'border': [self.map_width, self.map_height], 'total_frame': self.frame_limit, 'last_frame_count': self.last_frame_count, 'last_time': self.last_frame_count, 'leaderboard': {i: team_name_score[i] for i in range(self.team_num)}}
        return global_state

    def get_player_names(self):
        return self.player_manager.get_player_names()

    def get_team_names(self):
        return self.player_manager.get_team_names()

    def get_player_names_with_team(self):
        return self.player_manager.get_player_names_with_team()

    def get_team_infos(self):
        return self.player_manager.get_team_infos()

    def close(self):
        if hasattr(self, 'render'):
            self.render.close()

    def seed(self, seed=None):
        if seed is None:
            self._seed = random.randrange(sys.maxsize)
        else:
            self._seed = seed
        self._random = random.Random(self._seed)

def init_obs(self):
    self.eats = {player_id: {'food': 0, 'thorns': 0, 'spore': 0, 'clone_self': 0, 'clone_team': 0, 'clone_other': 0, 'eaten': 0} for player_id in self.player_manager.get_player_names()}
    self.player_states_util = PlayerStatesUtil(self.obs_settings)

def get_global_state(self):
    team_name_score = self.player_manager.get_teams_score()
    global_state = {'border': [self.map_width, self.map_height], 'total_frame': self.frame_limit, 'last_frame_count': self.last_frame_count, 'last_time': self.last_frame_count, 'leaderboard': {i: team_name_score[i] for i in range(self.team_num)}}
    return global_state

def get_player_names(self):
    return self.player_manager.get_player_names()

def get_team_infos(self):
    return self.player_manager.get_team_infos()

class ServerSP(Server):

    @staticmethod
    def default_config():
        cfg = copy.deepcopy(server_sp_default_config)
        return EasyDict(cfg)

    def __init__(self, cfg=None, seed=None):
        self.cfg = ServerSP.default_config()
        if isinstance(cfg, dict):
            cfg = EasyDict(cfg)
            self.cfg = deep_merge_dicts(self.cfg, cfg)
        self.update_match_ratio()
        logging.debug(self.cfg)
        self.team_num = self.cfg.team_num
        self.player_num_per_team = self.cfg.player_num_per_team
        self.map_width = self.cfg.map_width
        self.map_height = self.cfg.map_height
        self.frame_limit = self.cfg.frame_limit
        self.fps = self.cfg.fps
        self.frame_duration = 1 / self.fps
        self.collision_detection_type = self.cfg.collision_detection_type
        self.eat_ratio = self.cfg.eat_ratio
        self.playback_settings = self.cfg.playback_settings
        self.opening_settings = self.cfg.opening_settings
        self.manager_settings = self.cfg.manager_settings
        self.obs_settings = self.cfg.obs_settings
        self.seed(seed)
        self.border = Border(0, 0, self.map_width, self.map_height, self._random)
        self.last_frame_count = 0
        self.init_playback()
        self.init_opening()
        self.food_manager = FoodManager(self.manager_settings.food_manager, border=self.border, random_generator=self._random)
        self.thorns_manager = ThornsManager(self.manager_settings.thorns_manager, border=self.border, random_generator=self._random)
        self.spore_manager = SporeManager(self.manager_settings.spore_manager, border=self.border, random_generator=self._random)
        self.player_manager = PlayerSPManager(self.manager_settings.player_manager, border=self.border, team_num=self.team_num, player_num_per_team=self.player_num_per_team, spore_manager_settings=self.cfg.manager_settings.spore_manager, random_generator=self._random)
        self.init_obs()
        self.collision_detection = create_collision_detection(self.collision_detection_type, border=self.border)

    def init_obs(self):
        self.eats = {player_id: {'food': 0, 'thorns': 0, 'spore': 0, 'clone_self': 0, 'clone_team': 0, 'clone_other': 0, 'eaten': 0} for player_id in self.player_manager.get_player_names()}
        self.player_states_util = PlayerStatesSPUtil(self.obs_settings)

    def step_one_frame(self, actions=None):
        moving_balls = []
        total_balls = []
        if actions is not None and isinstance(actions, dict):
            for player in self.player_manager.get_players():
                if player.player_id in actions:
                    for ball_id, action in actions[player.player_id].items():
                        direction_x, direction_y, action_type = action
                        if direction_x is None or direction_y is None:
                            direction = None
                        else:
                            direction = Vector2(direction_x, direction_y)
                            if direction.length() > 1:
                                direction = direction.normalize()
                        if action_type == 1:
                            tmp_spore_balls = player.eject(ball_id, direction=direction)
                            for tmp_spore_ball in tmp_spore_balls:
                                if tmp_spore_ball:
                                    self.spore_manager.add_balls(tmp_spore_ball)
                        elif action_type == 2:
                            self.player_manager.add_balls(player.split(ball_id, direction=direction))
                        player.move(ball_id, direction=direction, duration=self.frame_duration)
                        moving_balls.extend(player.get_balls())
                else:
                    player.move(duration=self.frame_duration)
                    moving_balls.extend(player.get_balls())
        else:
            for player in self.player_manager.get_players():
                player.move(duration=self.frame_duration)
                moving_balls.extend(player.get_balls())
        moving_balls = sorted(moving_balls, reverse=True)
        for thorns_ball in self.thorns_manager.get_balls():
            if thorns_ball.moving:
                thorns_ball.move(duration=self.frame_duration)
            moving_balls.append(thorns_ball)
        for spore_ball in self.spore_manager.get_balls():
            if spore_ball.moving:
                spore_ball.move(duration=self.frame_duration)
        self.player_manager.adjust()
        total_balls.extend(self.player_manager.get_balls())
        total_balls.extend(self.thorns_manager.get_balls())
        total_balls.extend(self.spore_manager.get_balls())
        total_balls.extend(self.food_manager.get_balls())
        collisions_dict = self.collision_detection.solve(moving_balls, total_balls)
        for index, moving_ball in enumerate(moving_balls):
            if not moving_ball.is_remove and index in collisions_dict:
                for target_ball in collisions_dict[index]:
                    self.deal_with_collision(moving_ball, target_ball)
        self.food_manager.step(duration=self.frame_duration)
        self.spore_manager.step(duration=self.frame_duration)
        self.thorns_manager.step(duration=self.frame_duration)
        self.player_manager.step()
        self.last_frame_count += 1

def init_obs(self):
    self.eats = {player_id: {'food': 0, 'thorns': 0, 'spore': 0, 'clone_self': 0, 'clone_team': 0, 'clone_other': 0, 'eaten': 0} for player_id in self.player_manager.get_player_names()}
    self.player_states_util = PlayerStatesSPUtil(self.obs_settings)

@pytest.mark.unittest
class TestServer:

    def test_init(self):
        server = Server()
        assert True

    def test_spawn_balls(self):
        server = Server()
        server.reset()

    def test_step_control_random(self):
        server = Server()
        server.reset()
        fps_set = 20
        clock = pygame.time.Clock()
        render = RealtimePartialRender()
        for i in range(10):
            actions = {player_name: [random.uniform(-1, 1), random.uniform(-1, 1), -1] for player_name in server.get_player_names()}
            done = server.step(actions=actions)
            obs = server.obs()
            render.fill(obs[0], obs[1][0], player_num_per_team=1, fps=10)
            render.show()
            clock.tick(fps_set)
        server.close()

    def test_obs(self):
        server = Server()
        server.reset()
        for i in range(10):
            actions = {player_name: [random.uniform(-1, 1), random.uniform(-1, 1), -1] for player_name in server.get_player_names()}
            done = server.step(actions=actions)
            obs = server.obs()
            logging.debug(obs[0])

    def test_obs_multi_player(self):
        server = Server(dict(team_num=1, player_num_per_team=2))
        server.reset()
        for i in range(10):
            actions = {player_name: [random.uniform(-1, 1), random.uniform(-1, 1), -1] for player_name in server.get_player_names()}
            done = server.step(actions=actions)
            obs = server.obs()
            logging.debug(obs[0])

    def test_multiprocessing(self):
        """
        Overview:
            Test the server in a multi-process environment
        """
        server_num = 2
        servers = []
        for i in range(server_num):
            server = Server(dict(team_num=1, player_num_per_team=1, match_time=60 * 1))
            server.reset()
            servers.append(server)

        def run(server_index):
            for i in range(server_num):
                actions = {player_name: [random.uniform(-1, 1), random.uniform(-1, 1), -1] for player_name in servers[server_index].get_player_names()}
                done = servers[server_index].step(actions=actions)
                global_state, players_obs, info = servers[server_index].obs()
                logging.debug('{} {} {}'.format(server_index, i, global_state))
            logging.debug('{} start close'.format(server_index))
            logging.debug('{} finish'.format(server_index))
        ps = []
        for i in range(server_num):
            p = mp.Process(target=run, args=(i,), daemon=True)
            ps.append(p)
        for p in ps:
            p.start()
        for p in ps:
            p.join()

def test_init(self):
    server = Server()
    assert True

def test_spawn_balls(self):
    server = Server()
    server.reset()

def test_step_control_random(self):
    server = Server()
    server.reset()
    fps_set = 20
    clock = pygame.time.Clock()
    render = RealtimePartialRender()
    for i in range(10):
        actions = {player_name: [random.uniform(-1, 1), random.uniform(-1, 1), -1] for player_name in server.get_player_names()}
        done = server.step(actions=actions)
        obs = server.obs()
        render.fill(obs[0], obs[1][0], player_num_per_team=1, fps=10)
        render.show()
        clock.tick(fps_set)
    server.close()

def test_obs(self):
    server = Server()
    server.reset()
    for i in range(10):
        actions = {player_name: [random.uniform(-1, 1), random.uniform(-1, 1), -1] for player_name in server.get_player_names()}
        done = server.step(actions=actions)
        obs = server.obs()
        logging.debug(obs[0])

def test_obs_multi_player(self):
    server = Server(dict(team_num=1, player_num_per_team=2))
    server.reset()
    for i in range(10):
        actions = {player_name: [random.uniform(-1, 1), random.uniform(-1, 1), -1] for player_name in server.get_player_names()}
        done = server.step(actions=actions)
        obs = server.obs()
        logging.debug(obs[0])

def test_multiprocessing(self):
    """
        Overview:
            Test the server in a multi-process environment
        """
    server_num = 2
    servers = []
    for i in range(server_num):
        server = Server(dict(team_num=1, player_num_per_team=1, match_time=60 * 1))
        server.reset()
        servers.append(server)

    def run(server_index):
        for i in range(server_num):
            actions = {player_name: [random.uniform(-1, 1), random.uniform(-1, 1), -1] for player_name in servers[server_index].get_player_names()}
            done = servers[server_index].step(actions=actions)
            global_state, players_obs, info = servers[server_index].obs()
            logging.debug('{} {} {}'.format(server_index, i, global_state))
        logging.debug('{} start close'.format(server_index))
        logging.debug('{} finish'.format(server_index))
    ps = []
    for i in range(server_num):
        p = mp.Process(target=run, args=(i,), daemon=True)
        ps.append(p)
    for p in ps:
        p.start()
    for p in ps:
        p.join()

def run(server_index):
    for i in range(server_num):
        actions = {player_name: [random.uniform(-1, 1), random.uniform(-1, 1), -1] for player_name in servers[server_index].get_player_names()}
        done = servers[server_index].step(actions=actions)
        global_state, players_obs, info = servers[server_index].obs()
        logging.debug('{} {} {}'.format(server_index, i, global_state))
    logging.debug('{} start close'.format(server_index))
    logging.debug('{} finish'.format(server_index))

@pytest.mark.unittest
class TestServerSP:

    def test_init(self):
        server = ServerSP()
        assert True

    def test_spawn_balls(self):
        server = ServerSP()
        server.reset()

    def test_step_control_random(self):
        server = ServerSP()
        server.reset()
        obs = server.obs()
        fps_set = 20
        clock = pygame.time.Clock()
        render = RealtimePartialRender()
        for i in range(10):
            actions = {player_name: {ball[-1]: [random.uniform(-1, 1), random.uniform(-1, 1), -1] for ball in obs[1][0]['overlap']['clone']} for player_name in server.get_player_names()}
            done = server.step(actions=actions)
            obs = server.obs()
            render.fill(obs[0], obs[1][0], player_num_per_team=1, fps=10)
            render.show()
            clock.tick(fps_set)
        server.close()

    def test_obs(self):
        server = ServerSP()
        server.reset()
        obs = server.obs()
        for i in range(10):
            actions = {player_name: {ball[-1]: [random.uniform(-1, 1), random.uniform(-1, 1), -1] for ball in obs[1][0]['overlap']['clone']} for player_name in server.get_player_names()}
            done = server.step(actions=actions)
            obs = server.obs()
            logging.debug(obs[0])

    def test_obs_multi_player(self):
        server = ServerSP(dict(team_num=1, player_num_per_team=2))
        server.reset()
        obs = server.obs()
        for i in range(10):
            actions = {player_name: {ball[-1]: [random.uniform(-1, 1), random.uniform(-1, 1), -1] for ball in obs[1][0]['overlap']['clone']} for player_name in server.get_player_names()}
            done = server.step(actions=actions)
            obs = server.obs()
            logging.debug(obs[0])

def test_init(self):
    server = ServerSP()
    assert True

def test_spawn_balls(self):
    server = ServerSP()
    server.reset()

def test_step_control_random(self):
    server = ServerSP()
    server.reset()
    obs = server.obs()
    fps_set = 20
    clock = pygame.time.Clock()
    render = RealtimePartialRender()
    for i in range(10):
        actions = {player_name: {ball[-1]: [random.uniform(-1, 1), random.uniform(-1, 1), -1] for ball in obs[1][0]['overlap']['clone']} for player_name in server.get_player_names()}
        done = server.step(actions=actions)
        obs = server.obs()
        render.fill(obs[0], obs[1][0], player_num_per_team=1, fps=10)
        render.show()
        clock.tick(fps_set)
    server.close()

def test_obs(self):
    server = ServerSP()
    server.reset()
    obs = server.obs()
    for i in range(10):
        actions = {player_name: {ball[-1]: [random.uniform(-1, 1), random.uniform(-1, 1), -1] for ball in obs[1][0]['overlap']['clone']} for player_name in server.get_player_names()}
        done = server.step(actions=actions)
        obs = server.obs()
        logging.debug(obs[0])

def test_obs_multi_player(self):
    server = ServerSP(dict(team_num=1, player_num_per_team=2))
    server.reset()
    obs = server.obs()
    for i in range(10):
        actions = {player_name: {ball[-1]: [random.uniform(-1, 1), random.uniform(-1, 1), -1] for ball in obs[1][0]['overlap']['clone']} for player_name in server.get_player_names()}
        done = server.step(actions=actions)
        obs = server.obs()
        logging.debug(obs[0])

@pytest.mark.unittest
class TestBotAgent:

    def test_step(self):
        server = Server(dict(team_num=4, player_num_per_team=3, frame_limit=20))
        server.reset()
        bot_agents = []
        for index, player in enumerate(server.player_manager.get_players()):
            bot_agents.append(BotAgent(player.player_id, level=index % 3 + 1))
            logging.debug('players init: {}'.format(player.player_id))
        time_obs = 0
        time_step = 0
        time_fill_all = 0
        time_get_rectangle = 0
        time_get_clip = 0
        time_cvt = 0
        time_overlap = 0
        for i in range(100):
            t1 = time.time()
            obs = server.obs()
            t2 = time.time()
            if i % 4 == 0:
                actions = {bot_agent.name: bot_agent.step(obs[1][bot_agent.name]) for bot_agent in bot_agents}
            else:
                actions = None
            t3 = time.time()
            finish_flag = server.step(actions=actions)
            t4 = time.time()
            tmp_obs = t2 - t1
            tmp_step = t4 - t3
            time_obs += tmp_obs
            time_step += tmp_step
            logging.debug('{} {} obs: {:.3f} / {:.3f}, step: {:.3f} / {:.3f}'.format(i, server.last_frame_count, tmp_obs, time_obs / (i + 1), tmp_step, time_step / (i + 1)))
            if finish_flag:
                logging.debug('Game Over')
                break
        server.close()

def test_step(self):
    server = Server(dict(team_num=4, player_num_per_team=3, frame_limit=20))
    server.reset()
    bot_agents = []
    for index, player in enumerate(server.player_manager.get_players()):
        bot_agents.append(BotAgent(player.player_id, level=index % 3 + 1))
        logging.debug('players init: {}'.format(player.player_id))
    time_obs = 0
    time_step = 0
    time_fill_all = 0
    time_get_rectangle = 0
    time_get_clip = 0
    time_cvt = 0
    time_overlap = 0
    for i in range(100):
        t1 = time.time()
        obs = server.obs()
        t2 = time.time()
        if i % 4 == 0:
            actions = {bot_agent.name: bot_agent.step(obs[1][bot_agent.name]) for bot_agent in bot_agents}
        else:
            actions = None
        t3 = time.time()
        finish_flag = server.step(actions=actions)
        t4 = time.time()
        tmp_obs = t2 - t1
        tmp_step = t4 - t3
        time_obs += tmp_obs
        time_step += tmp_step
        logging.debug('{} {} obs: {:.3f} / {:.3f}, step: {:.3f} / {:.3f}'.format(i, server.last_frame_count, tmp_obs, time_obs / (i + 1), tmp_step, time_step / (i + 1)))
        if finish_flag:
            logging.debug('Game Over')
            break
    server.close()

class PlayerSPManager(PlayerManager):

    def __init__(self, cfg, border, team_num, player_num_per_team, spore_manager_settings, random_generator=None, sequence_generator=None):
        super(PlayerSPManager, self).__init__(cfg, border, team_num, player_num_per_team, spore_manager_settings, random_generator=random_generator)
        if sequence_generator is not None:
            self.sequence_generator = sequence_generator
        else:
            self.sequence_generator = SequenceGenerator()

    def init_balls(self, custom_init=None):
        if custom_init is None or len(custom_init) == 0:
            for i in range(self.team_num):
                team_id = i
                for j in range(self.player_num_per_team):
                    player_id = i * self.player_num_per_team + j
                    player = HumanSPPlayer(cfg=self.cfg.ball_settings, team_id=team_id, player_id=player_id, border=self.border, spore_settings=self.spore_settings, sequence_generator=self.sequence_generator)
                    player.respawn(position=self.border.sample())
                    self.players[player_id] = player
        else:
            raise NotImplementedError

def init_balls(self, custom_init=None):
    if custom_init is None or len(custom_init) == 0:
        for i in range(self.team_num):
            team_id = i
            for j in range(self.player_num_per_team):
                player_id = i * self.player_num_per_team + j
                player = HumanSPPlayer(cfg=self.cfg.ball_settings, team_id=team_id, player_id=player_id, border=self.border, spore_settings=self.spore_settings, sequence_generator=self.sequence_generator)
                player.respawn(position=self.border.sample())
                self.players[player_id] = player
    else:
        raise NotImplementedError

class PlayerManager(BaseManager):

    def __init__(self, cfg, border, team_num, player_num_per_team, spore_manager_settings, random_generator=None, sequence_generator=None):
        super(PlayerManager, self).__init__(cfg, border)
        self.players = {}
        self.team_num = team_num
        self.player_num_per_team = player_num_per_team
        self.player_num = self.team_num * self.player_num_per_team
        self.spore_manager_settings = spore_manager_settings
        self.spore_settings = self.spore_manager_settings.ball_settings
        if random_generator is not None:
            self._random = random_generator
        else:
            self._random = random.Random()
        if sequence_generator is not None:
            self.sequence_generator = sequence_generator
        else:
            self.sequence_generator = SequenceGenerator()

    def init_balls(self, custom_init=None):
        if custom_init is None or len(custom_init) == 0:
            for i in range(self.team_num):
                team_id = i
                for j in range(self.player_num_per_team):
                    player_id = i * self.player_num_per_team + j
                    player = HumanPlayer(cfg=self.cfg.ball_settings, team_id=team_id, player_id=player_id, border=self.border, spore_settings=self.spore_settings, sequence_generator=self.sequence_generator)
                    player.respawn(position=self.border.sample())
                    self.players[player_id] = player
        else:
            init_dict = {}
            for i in range(self.team_num):
                team_id = i
                init_dict[team_id] = {}
                for j in range(self.player_num_per_team):
                    player_id = i * self.player_num_per_team + j
                    player = HumanPlayer(cfg=self.cfg.ball_settings, team_id=team_id, player_id=player_id, border=self.border, spore_settings=self.spore_settings, sequence_generator=self.sequence_generator)
                    self.players[player_id] = player
                    init_dict[team_id][player_id] = False
            for ball_cfg in custom_init:
                position = Vector2(*ball_cfg[0:2])
                score = ball_cfg[2]
                player_id = ball_cfg[3]
                team_id = ball_cfg[4]
                ball = CloneBall(ball_id=self.sequence_generator.get(), position=position, border=self.border, score=score, team_id=team_id, player_id=player_id, spore_settings=self.spore_settings, **self.cfg.ball_settings)
                if len(ball_cfg) > 5:
                    ball.vel_given = Vector2(*ball_cfg[5:7])
                    ball.acc_given = Vector2(*ball_cfg[7:9])
                    ball.vel_split = Vector2(*ball_cfg[9:11])
                    ball.split_frame = Vector2(*ball_cfg[12])
                    ball.frame_since_last_split = ball_cfg[13]
                self.players[player_id].add_balls(ball)
                init_dict[team_id][player_id] = True
            for team_id, team in init_dict.items():
                for player_id, player_init_flag in team.items():
                    if not player_init_flag:
                        self.players[player_id].respawn(position=self.border.sample())

    def get_balls(self):
        balls = []
        for player_id, player in self.players.items():
            balls.extend(player.get_balls())
        return balls

    def get_players(self):
        return list(self.players.values())

    def get_player_by_name(self, player_id):
        assert player_id in self.players
        return self.players[player_id]

    def add_balls(self, balls):
        if isinstance(balls, list):
            for ball in balls:
                self.players[ball.player_id].add_balls(ball)
        elif isinstance(balls, CloneBall):
            self.players[balls.player_id].add_balls(balls)
        return True

    def remove_balls(self, balls):
        if isinstance(balls, list):
            for ball in balls:
                self.players[ball.player_id].remove_balls(ball)
        elif isinstance(balls, CloneBall):
            self.players[balls.player_id].remove_balls(balls)

    def step(self):
        for player_id, player in self.players.items():
            if player.get_clone_num() == 0:
                player.respawn(position=self.border.sample())

    def adjust(self):
        """
        Overview:
            Adjust all balls in all players
        """
        eats = {}
        for player in self.get_players():
            eats[player.player_id] = player.adjust()
        return eats

    def get_clone_num(self, ball):
        return self.players[ball.player_id].get_clone_num()

    def get_player_names(self):
        """
        Overview:
            get all names of players
        """
        return [player.player_id for player in self.get_players()]

    def get_team_names(self):
        """
        Overview:
            get all names of players by teams with team names
        """
        ret = {}
        for player in self.get_players():
            if player.team_id not in ret:
                ret[player.team_id] = []
            ret[player.team_id].append(player.player_id)
        return ret

    def get_player_names_with_team(self):
        """
        Overview:
            get all names of players by teams
        """
        ret = {}
        for player in self.get_players():
            if player.team_id not in ret:
                ret[player.team_id] = []
            ret[player.team_id].append(player.player_id)
        return list(ret.values())

    def get_team_infos(self):
        team_player_ids = {}
        for player in self.get_players():
            if player.team_id not in team_player_ids:
                team_player_ids[player.team_id] = []
            team_player_ids[player.team_id].append(player.player_id)
        return sorted(team_player_ids.items())

    def get_teams_score(self):
        team_name_score = {}
        for player in self.get_players():
            if player.team_id not in team_name_score:
                team_name_score[player.team_id] = player.get_total_score()
            else:
                team_name_score[player.team_id] += player.get_total_score()
        return team_name_score

    def reset(self):
        """
        Overview:
            reset manager
        """
        self.players = {}
        return True

def get_player_names(self):
    """
        Overview:
            get all names of players
        """
    return [player.player_id for player in self.get_players()]

class FoodManager(BaseManager):

    def __init__(self, cfg, border, random_generator=None, sequence_generator=None):
        super(FoodManager, self).__init__(cfg, border)
        self.refresh_frame_freq = self.cfg.refresh_frame_freq
        self.refresh_frame_count = 0
        if random_generator is not None:
            self._random = random_generator
        else:
            self._random = random.Random()
        if sequence_generator is not None:
            self.sequence_generator = sequence_generator
        else:
            self.sequence_generator = SequenceGenerator()

    def get_balls(self):
        return list(self.balls.values())

    def add_balls(self, balls):
        if isinstance(balls, list):
            for ball in balls:
                self.balls[ball.ball_id] = ball
        elif isinstance(balls, FoodBall):
            self.balls[balls.ball_id] = balls
        return True

    def refresh(self):
        left_num = self.cfg.num_max - len(self.balls)
        todo_num = min(math.ceil(self.cfg.refresh_percent * left_num), left_num)
        new_balls = {}
        for _ in range(todo_num):
            ball = self.spawn_ball()
            self.add_balls(ball)
            new_balls[ball.ball_id] = ball.save()
        return new_balls

    def remove_balls(self, balls):
        if isinstance(balls, list):
            for ball in balls:
                ball.remove()
                try:
                    del self.balls[ball.ball_id]
                except:
                    pass
        elif isinstance(balls, FoodBall):
            balls.remove()
            try:
                del self.balls[balls.ball_id]
            except:
                pass

    def spawn_ball(self, position=None, score=None):
        if position is None:
            position = self.border.sample()
        if score is None:
            score = self._random.uniform(self.ball_settings.score_min, self.ball_settings.score_max)
        ball_id = self.sequence_generator.get()
        return FoodBall(ball_id=ball_id, position=position, border=self.border, score=score, **self.ball_settings)

    def init_balls(self, custom_init=None):
        if custom_init is None or len(custom_init) == 0:
            for _ in range(self.cfg.num_init):
                ball = self.spawn_ball()
                self.balls[ball.ball_id] = ball
        else:
            for ball_cfg in custom_init:
                ball = self.spawn_ball(position=Vector2(*ball_cfg[:2]), score=ball_cfg[2])
                self.balls[ball.ball_id] = ball

    def step(self, duration):
        self.refresh_frame_count += 1
        new_balls = {}
        if self.refresh_frame_count >= self.refresh_frame_freq:
            new_balls = self.refresh()
            self.refresh_frame_count = 0
        return new_balls

    def reset(self):
        self.refresh_frame_count = 0
        self.balls = {}
        return True

def spawn_ball(self, position=None, score=None):
    if position is None:
        position = self.border.sample()
    if score is None:
        score = self._random.uniform(self.ball_settings.score_min, self.ball_settings.score_max)
    ball_id = self.sequence_generator.get()
    return FoodBall(ball_id=ball_id, position=position, border=self.border, score=score, **self.ball_settings)

class ThornsManager(BaseManager):

    def __init__(self, cfg, border, random_generator=None, sequence_generator=None):
        super(ThornsManager, self).__init__(cfg, border)
        self.refresh_frame_freq = self.cfg.refresh_frame_freq
        self.refresh_frame_count = 0
        if random_generator is not None:
            self._random = random_generator
        else:
            self._random = random.Random()
        if sequence_generator is not None:
            self.sequence_generator = sequence_generator
        else:
            self.sequence_generator = SequenceGenerator()

    def get_balls(self):
        return list(self.balls.values())

    def add_balls(self, balls):
        if isinstance(balls, list):
            for ball in balls:
                self.balls[ball.ball_id] = ball
        elif isinstance(balls, ThornsBall):
            self.balls[balls.ball_id] = balls
        return True

    def refresh(self):
        left_num = self.cfg.num_max - len(self.balls)
        todo_num = min(math.ceil(self.cfg.refresh_percent * left_num), left_num)
        new_balls = {}
        for _ in range(todo_num):
            ball = self.spawn_ball()
            self.add_balls(ball)
            new_balls[ball.ball_id] = ball.save()
        return new_balls

    def remove_balls(self, balls):
        if isinstance(balls, list):
            for ball in balls:
                ball.remove()
                try:
                    del self.balls[ball.ball_id]
                except:
                    pass
        elif isinstance(balls, ThornsBall):
            balls.remove()
            try:
                del self.balls[balls.ball_id]
            except:
                pass

    def spawn_ball(self, position=None, score=None):
        if position is None:
            position = self.border.sample()
        if score is None:
            score = self._random.uniform(self.ball_settings.score_min, self.ball_settings.score_max)
        ball_id = self.sequence_generator.get()
        return ThornsBall(ball_id=ball_id, position=position, border=self.border, score=score, **self.ball_settings)

    def init_balls(self, custom_init=None):
        if custom_init is None or len(custom_init) == 0:
            for _ in range(self.cfg.num_init):
                ball = self.spawn_ball()
                self.balls[ball.ball_id] = ball
        else:
            for ball_cfg in custom_init:
                ball = self.spawn_ball(position=Vector2(*ball_cfg[:2]), score=ball_cfg[2])
                if len(ball_cfg) > 3:
                    ball.vel = Vector2(*ball_cfg[3:5])
                    ball.move_frame = Vector2(*ball_cfg[5])
                    ball.moving = ball_cfg[6]
                self.balls[ball.ball_id] = ball

    def step(self, duration):
        self.refresh_frame_count += 1
        new_balls = {}
        if self.refresh_frame_count > self.refresh_frame_freq:
            new_balls = self.refresh()
            self.refresh_frame_count = 0
        return new_balls

    def reset(self):
        self.refresh_frame_count = 0
        self.balls = {}
        return True

def spawn_ball(self, position=None, score=None):
    if position is None:
        position = self.border.sample()
    if score is None:
        score = self._random.uniform(self.ball_settings.score_min, self.ball_settings.score_max)
    ball_id = self.sequence_generator.get()
    return ThornsBall(ball_id=ball_id, position=position, border=self.border, score=score, **self.ball_settings)

class RealtimeRender(BaseRender):
    """
    Overview:
        Used in real-time games, giving a global view
    """

    def __init__(self, game_screen_width=512, game_screen_height=512, info_width=0, info_height=0, with_show=True, padding=20, map_width=128, map_height=128):
        super(RealtimeRender, self).__init__(game_screen_width=game_screen_width, game_screen_height=game_screen_height, info_width=info_width, info_height=info_height, with_show=with_show)
        self.scale_ratio_w = (self.game_screen_width - padding * 2) / map_width
        self.scale_ratio_h = (self.game_screen_height - padding * 2) / map_height
        self.padding = padding

    def render_all_balls_colorful(self, food_balls, thorns_balls, spore_balls, players, player_num_per_team):
        for ball in food_balls:
            x = ball.position.x * self.scale_ratio_w + self.padding
            y = ball.position.y * self.scale_ratio_h + self.padding
            r = ball.radius * self.scale_ratio_w
            pygame.draw.circle(self.screen, FOOD_COLOR, Vector2(x, y), r)
        for ball in thorns_balls:
            x = ball.position.x * self.scale_ratio_w + self.padding
            y = ball.position.y * self.scale_ratio_h + self.padding
            r = ball.radius * self.scale_ratio_w
            pygame.draw.polygon(self.screen, THORNS_COLOR, to_aliased_circle(Vector2(x, y), r))
        for ball in spore_balls:
            x = ball.position.x * self.scale_ratio_w + self.padding
            y = ball.position.y * self.scale_ratio_h + self.padding
            r = ball.radius * self.scale_ratio_w
            pygame.draw.circle(self.screen, SPORE_COLOR, Vector2(x, y), r)
        for player in players:
            for ball in player.get_balls():
                x = ball.position.x * self.scale_ratio_w + self.padding
                y = ball.position.y * self.scale_ratio_h + self.padding
                r = ball.radius * self.scale_ratio_w
                pygame.draw.circle(self.screen, PLAYER_COLORS[int(ball.team_id)][0], Vector2(x, y), r)
                pygame.draw.polygon(self.screen, PLAYER_COLORS[int(ball.team_id)][0], to_arrow(Vector2(x, y), r, ball.direction))
                font_size = int(r / 1.6)
                font = pygame.font.SysFont('arial', max(font_size, 8), True)
                txt = font.render('{}'.format(chr(int(ball.player_id % player_num_per_team) + 65)), True, WHITE)
                txt_rect = txt.get_rect(center=(x, y))
                self.screen.blit(txt, txt_rect)

    def fill(self, food_balls, thorns_balls, spore_balls, players, player_num_per_team=1, fps=20, leaderboard=None):
        self.screen.fill(BACKGROUND)
        self.render_all_balls_colorful(food_balls, thorns_balls, spore_balls, players, player_num_per_team)
        pygame.draw.line(self.screen, RED, (self.padding, self.padding), (self.game_screen_width - self.padding, self.padding), width=1)
        pygame.draw.line(self.screen, RED, (self.padding, self.padding), (self.padding, self.game_screen_width - self.padding), width=1)
        pygame.draw.line(self.screen, RED, (self.padding, self.game_screen_width - self.padding), (self.game_screen_width - self.padding, self.game_screen_width - self.padding), width=1)
        pygame.draw.line(self.screen, RED, (self.game_screen_width - self.padding, self.padding), (self.game_screen_width - self.padding, self.game_screen_width - self.padding), width=1)
        font = pygame.font.SysFont('Menlo', 15, True)
        if leaderboard is not None:
            leaderboard = sorted(leaderboard.items(), key=lambda d: d[1], reverse=True)
            for index, (team_id, team_size) in enumerate(leaderboard):
                pos_txt = font.render('{}: {:.5f}'.format(team_id, team_size), 1, RED)
                self.screen.blit(pos_txt, (20, 10 + 10 * (index * 2 + 1)))

    def show(self):
        pygame.display.update()

    def close(self):
        pygame.quit()

def show(self):
    pygame.display.update()

class RealtimePartialRender(BaseRender):
    """
    Overview:
        Used in real-time games to give the player a visible field of view. The corresponding player can be obtained by specifying the player name. The default is the first player
    """

    def __init__(self, game_screen_width=512, game_screen_height=512, info_width=0, info_height=0, with_show=True):
        super(RealtimePartialRender, self).__init__(game_screen_width=game_screen_width, game_screen_height=game_screen_height, info_width=info_width, info_height=info_height, with_show=with_show)

    def render_all_balls_colorful(self, overlap, player_num_per_team=1, scale_ratio_w=1, scale_ratio_h=1, start_x=0, start_y=0):
        for ball in overlap['food']:
            x = (ball[0] - start_x) * scale_ratio_w
            y = (ball[1] - start_y) * scale_ratio_h
            r = ball[2] * scale_ratio_w
            pygame.draw.circle(self.screen, FOOD_COLOR, Vector2(x, y), r)
        for ball in overlap['thorns']:
            x = (ball[0] - start_x) * scale_ratio_w
            y = (ball[1] - start_y) * scale_ratio_h
            r = ball[2] * scale_ratio_w
            pygame.draw.polygon(self.screen, THORNS_COLOR, to_aliased_circle(Vector2(x, y), r))
        for ball in overlap['spore']:
            x = (ball[0] - start_x) * scale_ratio_w
            y = (ball[1] - start_y) * scale_ratio_h
            r = ball[2] * scale_ratio_w
            pygame.draw.circle(self.screen, SPORE_COLOR, Vector2(x, y), r)
        for ball in overlap['clone']:
            x = (ball[0] - start_x) * scale_ratio_w
            y = (ball[1] - start_y) * scale_ratio_h
            r = ball[2] * scale_ratio_w
            direction = Vector2(ball[6], ball[7])
            player_id = int(ball[8])
            team_id = int(ball[9])
            pygame.draw.circle(self.screen, PLAYER_COLORS[team_id][0], Vector2(x, y), r)
            point_list = to_arrow(Vector2(x, y), r, direction)
            pygame.draw.polygon(self.screen, PLAYER_COLORS[team_id][0], point_list)
            font_size = int(r / 1.6)
            font = pygame.font.SysFont('arial', max(font_size, 6), True)
            txt = font.render('{}'.format(chr(player_id % player_num_per_team + 65)), True, WHITE)
            txt_rect = txt.get_rect(center=(x, y))
            self.screen.blit(txt, txt_rect)

    def fill(self, global_state, player_state, player_num_per_team=1, fps=20):
        self.screen.fill(BACKGROUND)
        rectangle = player_state['rectangle']
        overlap = player_state['overlap']
        leaderboard = global_state['leaderboard']
        frame_count = global_state['last_frame_count']
        map_width, map_height = global_state['border']
        left, top, right, bottom = rectangle
        width_real, height_real, hw_ratio = (right - left, bottom - top, (right - left) / (bottom - top))
        scale_ratio_w = self.game_screen_width / width_real
        scale_ratio_h = self.game_screen_width / height_real
        start_x = left
        start_y = top
        self.render_all_balls_colorful(overlap, player_num_per_team=player_num_per_team, scale_ratio_w=scale_ratio_w, scale_ratio_h=scale_ratio_h, start_x=start_x, start_y=start_y)
        pygame.draw.line(self.screen, BLACK, ((map_width - start_x) * scale_ratio_w, (0 - start_y) * scale_ratio_h), ((map_width - start_x) * scale_ratio_w, (map_height - start_y) * scale_ratio_h), width=1)
        pygame.draw.line(self.screen, BLACK, ((0 - start_x) * scale_ratio_w, (map_height - start_y) * scale_ratio_h), ((map_width - start_x) * scale_ratio_w, (map_height - start_y) * scale_ratio_h), width=1)
        pygame.draw.line(self.screen, BLACK, ((0 - start_x) * scale_ratio_w, (0 - start_y) * scale_ratio_h), ((0 - start_x) * scale_ratio_w, (map_height - start_y) * scale_ratio_h), width=1)
        pygame.draw.line(self.screen, BLACK, ((0 - start_x) * scale_ratio_w, (0 - start_y) * scale_ratio_h), ((map_width - start_x) * scale_ratio_w, (0 - start_y) * scale_ratio_h), width=1)
        font = pygame.font.SysFont('Menlo', 15, True)
        assert len(leaderboard) > 0, 'leaderboard could not be None'
        leaderboard = sorted(leaderboard.items(), key=lambda d: d[1], reverse=True)
        for index, (team_id, team_score) in enumerate(leaderboard):
            pos_txt = font.render('{}: {:.5f}'.format(team_id, team_score), 1, RED)
            self.screen.blit(pos_txt, (20, 10 + 10 * (index * 2 + 1)))
        fps_txt = font.render('fps: ' + str(fps), 1, RED)
        last_frame_txt = font.render('frame_count: {} / {}'.format(frame_count, int(frame_count / 20)), 1, RED)
        self.screen.blit(fps_txt, (20, self.total_screen_height - 30))
        self.screen.blit(last_frame_txt, (20, self.total_screen_height - 50))

    def show(self):
        pygame.display.update()

    def close(self):
        pygame.quit()

def show(self):
    pygame.display.update()

class PBRender(BaseRender):

    def __init__(self, game_screen_width=512, game_screen_height=512, info_width=60, info_height=20, padding=20, map_width=128, map_height=128, pb_data=None, player_num_per_team=1):
        super(PBRender, self).__init__(game_screen_width=game_screen_width, game_screen_height=game_screen_height, info_width=info_width, info_height=info_height, with_show=True)
        self.padding = padding
        self.pb_data = pb_data
        assert pb_data is not None
        self.map_width = self.pb_data['cfg']['map_width']
        self.map_height = self.pb_data['cfg']['map_height']
        self.player_num_per_team = self.pb_data['cfg']['player_num_per_team']
        self.speed_button = SpeedButton(20, game_screen_height + info_height / 2, 'x1')
        self.play_button = PlayButton(40, game_screen_height + info_height / 2, '||')
        self.scrollbar = Scrollbar(60, game_screen_height + info_height / 2, game_screen_width - 80)
        self.if_play = True
        self.speed = 1
        self.frame_now = 1
        self.frame_target = self.frame_now + self.speed
        self.overlap = copy.deepcopy(self.pb_data[self.frame_now][0])
        self.leaderboard = self.pb_data[self.frame_now][2]
        self.frame_total = len(self.pb_data)
        self.rate = self.frame_now / self.frame_total

    def set_data(self):
        if self.if_play:
            if self.frame_target == self.frame_now:
                return
            if self.frame_target < self.frame_now:
                self.frame_now = 1
                self.overlap = copy.deepcopy(self.pb_data[self.frame_now][0])
                self.leaderboard = self.pb_data[self.frame_now][2]
            for i in range(self.frame_now + 1, self.frame_target + 1):
                if i in self.pb_data:
                    diff_balls_modify, diff_balls_remove, self.leaderboard = self.pb_data[i]
                    for index, balls in enumerate(diff_balls_modify[:-1]):
                        for ball_id, ball in balls.items():
                            self.overlap[index][ball_id] = ball
                    self.overlap[-1] = diff_balls_modify[-1]
                    for index, ball_ids in enumerate(diff_balls_remove):
                        for ball_id in ball_ids:
                            self.overlap[index].pop(ball_id, None)
        self.frame_now = self.frame_target

    def render_all_balls_colorful(self, scale_ratio_w=1, scale_ratio_h=1):
        pygame.draw.line(self.screen, RED, (self.padding, self.padding), (self.game_screen_width - self.padding, self.padding), width=1)
        pygame.draw.line(self.screen, RED, (self.padding, self.padding), (self.padding, self.game_screen_width - self.padding), width=1)
        pygame.draw.line(self.screen, RED, (self.padding, self.game_screen_width - self.padding), (self.game_screen_width - self.padding, self.game_screen_width - self.padding), width=1)
        pygame.draw.line(self.screen, RED, (self.game_screen_width - self.padding, self.padding), (self.game_screen_width - self.padding, self.game_screen_width - self.padding), width=1)
        pygame.draw.line(self.screen, BLACK, (self.game_screen_width, 0), (self.game_screen_width, self.game_screen_width + self.padding), width=1)
        for ball_id, ball in self.overlap[0].items():
            x = ball[0] * scale_ratio_w + self.padding
            y = ball[1] * scale_ratio_h + self.padding
            r = ball[2] * scale_ratio_w
            pygame.draw.circle(self.screen, FOOD_COLOR, Vector2(x, y), r)
        for ball_id, ball in self.overlap[1].items():
            x = ball[0] * scale_ratio_w + self.padding
            y = ball[1] * scale_ratio_h + self.padding
            r = ball[2] * scale_ratio_w
            pygame.draw.polygon(self.screen, THORNS_COLOR, to_aliased_circle(Vector2(x, y), r))
        for ball_id, ball in self.overlap[2].items():
            x = ball[0] * scale_ratio_w + self.padding
            y = ball[1] * scale_ratio_h + self.padding
            r = ball[2] * scale_ratio_w
            pygame.draw.circle(self.screen, SPORE_COLOR, Vector2(x, y), r)
        for ball_id, ball in self.overlap[3].items():
            x = ball[0] * scale_ratio_w + self.padding
            y = ball[1] * scale_ratio_h + self.padding
            r = ball[2] * scale_ratio_w
            direction = Vector2(ball[3], ball[4])
            player_id = int(ball[5])
            team_id = int(ball[6])
            pygame.draw.circle(self.screen, PLAYER_COLORS[team_id][0], Vector2(x, y), r)
            point_list = to_arrow(Vector2(x, y), r, direction)
            pygame.draw.polygon(self.screen, PLAYER_COLORS[team_id][0], point_list)
            font_size = int(r / 1.6)
            font = pygame.font.SysFont('arial', max(font_size, 6), True)
            txt = font.render('{}'.format(chr(player_id % self.player_num_per_team + 65)), True, WHITE)
            txt_rect = txt.get_rect(center=(x, y))
            self.screen.blit(txt, txt_rect)

    def render_rect_balls_colorful(self, scale_ratio_w=1, scale_ratio_h=1, start_x=0, start_y=0):
        pygame.draw.line(self.screen, BLACK, ((self.map_width - start_x) * scale_ratio_w, (0 - start_y) * scale_ratio_h), ((self.map_width - start_x) * scale_ratio_w, (self.map_height - start_y) * scale_ratio_h), width=1)
        pygame.draw.line(self.screen, BLACK, ((0 - start_x) * scale_ratio_w, (self.map_height - start_y) * scale_ratio_h), ((self.map_width - start_x) * scale_ratio_w, (self.map_height - start_y) * scale_ratio_h), width=1)
        pygame.draw.line(self.screen, BLACK, ((0 - start_x) * scale_ratio_w, (0 - start_y) * scale_ratio_h), ((0 - start_x) * scale_ratio_w, (self.map_height - start_y) * scale_ratio_h), width=1)
        pygame.draw.line(self.screen, BLACK, ((0 - start_x) * scale_ratio_w, (0 - start_y) * scale_ratio_h), ((self.map_width - start_x) * scale_ratio_w, (0 - start_y) * scale_ratio_h), width=1)
        for ball_id, ball in self.overlap[0].items():
            x = (ball[0] - start_x) * scale_ratio_w
            y = (ball[1] - start_y) * scale_ratio_h
            r = ball[2] * scale_ratio_w
            pygame.draw.circle(self.screen, FOOD_COLOR, Vector2(x, y), r)
        for ball_id, ball in self.overlap[1].items():
            x = (ball[0] - start_x) * scale_ratio_w
            y = (ball[1] - start_y) * scale_ratio_h
            r = ball[2] * scale_ratio_w
            pygame.draw.polygon(self.screen, THORNS_COLOR, to_aliased_circle(Vector2(x, y), r))
        for ball_id, ball in self.overlap[2].items():
            x = (ball[0] - start_x) * scale_ratio_w
            y = (ball[1] - start_y) * scale_ratio_h
            r = ball[2] * scale_ratio_w
            pygame.draw.circle(self.screen, SPORE_COLOR, Vector2(x, y), r)
        for ball_id, ball in self.overlap[3].items():
            x = (ball[0] - start_x) * scale_ratio_w
            y = (ball[1] - start_y) * scale_ratio_h
            r = ball[2] * scale_ratio_w
            direction = Vector2(ball[3], ball[4])
            player_id = int(ball[5])
            team_id = int(ball[6])
            pygame.draw.circle(self.screen, PLAYER_COLORS[team_id][0], Vector2(x, y), r)
            point_list = to_arrow(Vector2(x, y), r, direction)
            pygame.draw.polygon(self.screen, PLAYER_COLORS[team_id][0], point_list)
            font_size = int(r / 1.6)
            font = pygame.font.SysFont('arial', max(font_size, 6), True)
            txt = font.render('{}'.format(chr(player_id % self.player_num_per_team + 65)), True, WHITE)
            txt_rect = txt.get_rect(center=(x, y))
            self.screen.blit(txt, txt_rect)

    def render_leaderboard_colorful(self, leaderboard):
        start = 10
        team_score = sorted(leaderboard.items(), key=lambda d: d[1], reverse=True)
        for index, (team_id, score) in enumerate(team_score):
            start += 20
            font = pygame.font.SysFont('arial', 8, True)
            fps_txt = font.render('{} : {:.2f}'.format(team_id, score), True, PLAYER_COLORS[int(team_id)][0])
            self.screen.blit(fps_txt, (self.game_screen_width + 5, start))

    def fill(self, rectangle=None):
        self.screen.fill(BACKGROUND)
        if rectangle is not None:
            left, top, right, bottom = rectangle
            width_real, height_real, hw_ratio = (right - left, bottom - top, (right - left) / (bottom - top))
            scale_ratio_w = self.game_screen_width / width_real
            scale_ratio_h = self.game_screen_width / height_real
            start_x = left
            start_y = top
            self.render_rect_balls_colorful(scale_ratio_w=scale_ratio_w, scale_ratio_h=scale_ratio_h, start_x=start_x, start_y=start_y)
        else:
            scale_ratio_w = (self.game_screen_width - self.padding * 2) / self.map_width
            scale_ratio_h = (self.game_screen_height - self.padding * 2) / self.map_height
            start_x = 0
            start_y = 0
            self.render_all_balls_colorful(scale_ratio_w=scale_ratio_w, scale_ratio_h=scale_ratio_h)
        font = pygame.font.SysFont('Menlo', 15, True)
        assert len(self.leaderboard) > 0, 'leaderboard could not be None'
        self.render_leaderboard_colorful(self.leaderboard)
        self.speed_button.display(self.screen)
        self.play_button.display(self.screen)
        self.scrollbar.display(self.screen, self.rate)

    def show(self):
        self.fill()
        pygame.display.update()
        self.set_data()
        if self.if_play:
            self.frame_target = min(self.frame_now + self.speed, self.frame_total)
        self.rate = self.frame_now / self.frame_total

    def close(self):
        pygame.quit()

    def on_pressed(self, position):
        if self.play_button.check_click(position):
            self.if_play = self.play_button.on_pressed()
        elif self.speed_button.check_click(position):
            self.speed = self.speed_button.on_pressed()
        elif self.scrollbar.check_click(position):
            self.rate = self.scrollbar.on_pressed(position)
            self.frame_target = int(self.rate * self.frame_total)

def show(self):
    self.fill()
    pygame.display.update()
    self.set_data()
    if self.if_play:
        self.frame_target = min(self.frame_now + self.speed, self.frame_total)
    self.rate = self.frame_now / self.frame_total

@pytest.mark.unittest
class TestRealtimePartialRender:

    def test_init(self):
        render = RealtimeRender()
        render = RealtimePartialRender()
        assert True

def test_init(self):
    render = RealtimeRender()
    render = RealtimePartialRender()
    assert True

def play():
    select = TkSelect()
    if not hasattr(select, 'pb_path'):
        return
    pb_path = select.pb_path
    pb_data = read_pb(pb_path)
    clock = pygame.time.Clock()
    fps_set = 20
    pb_render = PBRender(pb_data=pb_data)
    while True:
        mouse_pos = None
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()
            elif event.type == pygame.MOUSEBUTTONUP:
                mouse_pos = pygame.mouse.get_pos()
        if mouse_pos is not None:
            pb_render.on_pressed(mouse_pos)
        pb_render.show()
        clock.tick(fps_set)

def test_pbutil():
    env = create_env('st_t2p2', dict(playback_settings=dict(playback_type='by_frame', by_frame=dict(save_frame=True))))
    obs = env.reset()
    bot_agents = []
    team_infos = env.get_team_infos()
    print(team_infos)
    for team_id, player_ids in team_infos:
        for player_id in player_ids:
            bot_agents.append(BotAgent(player_id, level=2))
    time_step_all = 0
    for i in range(100000):
        actions = {bot_agent.name: bot_agent.step(obs[1][bot_agent.name]) for bot_agent in bot_agents}
        t1 = time.time()
        obs, reward, done, info = env.step(actions=actions)
        t2 = time.time()
        time_step_all += t2 - t1
        logging.debug('{} {:.4f} envstep {:.3f} / {:.3f}, leaderboard={}'.format(i, obs[0]['last_frame_count'], t2 - t1, time_step_all / (i + 1), obs[0]['leaderboard']))
        if done:
            logging.debug('Game Over')
            break
    env.close()

def demo_bot():
    env = GoBiggerEnv(dict(team_num=4, player_num_per_team=3, frame_limit=60 * 20 * 1, playback_settings=dict(save_video=True, save_all=True, save_partial=True)))
    obs = env.reset()
    bot_agents = []
    team_infos = env.get_team_infos()
    for team_id, player_ids in team_infos:
        for player_id in player_ids:
            bot_agents.append(BotAgent(player_id, level=2))
    time_step_all = 0
    for i in range(100000):
        actions = {bot_agent.name: bot_agent.step(obs[1][bot_agent.name]) for bot_agent in bot_agents}
        t1 = time.time()
        obs, reward, done, info = env.step(actions=actions)
        t2 = time.time()
        time_step_all += t2 - t1
        logging.debug('{} {:.4f} envstep {:.3f} / {:.3f}, leaderboard={}'.format(i, obs[0]['last_frame_count'], t2 - t1, time_step_all / (i + 1), obs[0]['leaderboard']))
        if done:
            logging.debug('Game Over')
            break
    env.close()

def demo_bot_st_t2p2():
    env = create_env('st_t3p2', dict(playback_settings=dict(playback_type='by_frame', by_frame=dict(save_frame=True))), step_mul=10)
    obs = env.reset()
    bot_agents = []
    team_infos = env.get_team_infos()
    print(team_infos)
    for team_id, player_ids in team_infos:
        for player_id in player_ids:
            bot_agents.append(BotAgent(player_id, level=2))
    time_step_all = 0
    for i in range(100000):
        actions = {bot_agent.name: bot_agent.step(obs[1][bot_agent.name]) for bot_agent in bot_agents}
        t1 = time.time()
        obs, reward, done, info = env.step(actions=actions)
        t2 = time.time()
        time_step_all += t2 - t1
        logging.debug('{} {:.4f} envstep {:.3f} / {:.3f}, leaderboard={}'.format(i, obs[0]['last_frame_count'], t2 - t1, time_step_all / (i + 1), obs[0]['leaderboard']))
        if done:
            logging.debug('Game Over')
            break
    env.close()

def play_partial_against_bot():
    env = GoBiggerEnv(dict(team_num=3, player_num_per_team=1), step_mul=1)
    obs = env.reset()
    done = False
    render = RealtimePartialRender()
    fps_real = 0
    t1 = time.time()
    clock = pygame.time.Clock()
    fps_set = env.server.fps
    my_player_id = 0
    bot_agents = []
    for player in env.server.player_manager.get_players():
        if player.player_id != my_player_id:
            bot_agents.append(BotAgent(player.player_id))
    for i in range(100000):
        actions = None
        x, y = (None, None)
        action_type = 0
        mouse_pos = pygame.mouse.get_pos()
        x = (mouse_pos[0] - render.game_screen_width / 2) / (render.game_screen_width / 4)
        y = (mouse_pos[1] - render.game_screen_height / 2) / (render.game_screen_height / 4)
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    x, y = (None, None)
                    action_type = 1
                elif event.key == pygame.K_w:
                    x, y = (None, None)
                    action_type = 2
                elif event.key == pygame.K_e:
                    action_type = 0
                    env.server.player_manager.get_players()[0].get_balls()[0].set_score(100000)
        actions = {my_player_id: [x, y, action_type]}
        actions.update({agent.name: agent.step(obs[1][agent.name]) for agent in bot_agents})
        if not done:
            obs, reward, done, info = env.step(actions=actions)
            render.fill(obs[0], obs[1][0], player_num_per_team=1, fps=fps_real)
            render.show()
            if i % fps_set == 0:
                t2 = time.time()
                fps_real = fps_set / (t2 - t1)
                t1 = time.time()
        else:
            logging.debug('Game Over')
            break
        clock.tick(fps_set)
    render.close()

def play_all_against_bot():
    env = GoBiggerEnv(dict(team_num=3, player_num_per_team=1), step_mul=1)
    obs = env.reset()
    done = False
    render = RealtimeRender()
    fps_real = 0
    t1 = time.time()
    clock = pygame.time.Clock()
    fps_set = env.server.fps
    my_player_id = 0
    bot_agents = []
    for player in env.server.player_manager.get_players():
        if player.player_id != my_player_id:
            bot_agents.append(BotAgent(player.player_id))
    for i in range(100000):
        actions = None
        x, y = (None, None)
        action_type = 0
        mouse_pos = pygame.mouse.get_pos()
        x = (mouse_pos[0] - render.game_screen_width / 2) / (render.game_screen_width / 4)
        y = (mouse_pos[1] - render.game_screen_height / 2) / (render.game_screen_height / 4)
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    x, y = (None, None)
                    action_type = 1
                elif event.key == pygame.K_w:
                    x, y = (None, None)
                    action_type = 2
                elif event.key == pygame.K_e:
                    action_type = 0
                    env.server.player_manager.get_players()[0].get_balls()[0].set_score(100000)
        actions = {my_player_id: [x, y, action_type]}
        actions.update({agent.name: agent.step(obs[1][agent.name]) for agent in bot_agents})
        if not done:
            obs, reward, done, info = env.step(actions=actions)
            render.fill(food_balls=env.server.food_manager.get_balls(), thorns_balls=env.server.thorns_manager.get_balls(), spore_balls=env.server.spore_manager.get_balls(), players=env.server.player_manager.get_players(), player_num_per_team=env.server.player_num_per_team, fps=fps_real)
            render.show()
            if i % fps_set == 0:
                t2 = time.time()
                fps_real = fps_set / (t2 - t1)
                t1 = time.time()
        else:
            logging.debug('Game Over')
            break
        clock.tick(fps_set)
    render.close()

def play_partial_sp_against_bot():
    env = GoBiggerSPEnv(dict(team_num=1, player_num_per_team=1), step_mul=1)
    obs = env.reset()
    done = False
    render = RealtimePartialRender()
    fps_real = 0
    t1 = time.time()
    clock = pygame.time.Clock()
    fps_set = env.server.fps
    for i in range(100000):
        clone_balls = obs[1][0]['overlap']['clone']
        ball_ids = [ball[-1] for ball in clone_balls]
        actions = None
        x, y = (None, None)
        action_type = 0
        mouse_pos = pygame.mouse.get_pos()
        x = (mouse_pos[0] - render.game_screen_width / 2) / (render.game_screen_width / 4)
        y = (mouse_pos[1] - render.game_screen_height / 2) / (render.game_screen_height / 4)
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    x, y = (None, None)
                    action_type = 1
                elif event.key == pygame.K_w:
                    x, y = (None, None)
                    action_type = 2
                elif event.key == pygame.K_e:
                    action_type = 0
                    env.server.player_manager.get_players()[0].get_balls()[0].set_score(100000)
        actions = {player.player_id: {ball_id: [x, y, action_type] for ball_id in ball_ids} for player in env.server.player_manager.get_players()}
        if not done:
            obs, reward, done, info = env.step(actions=actions)
            render.fill(obs[0], obs[1][0], player_num_per_team=1, fps=fps_real)
            render.show()
            if i % fps_set == 0:
                t2 = time.time()
                fps_real = fps_set / (t2 - t1)
                t1 = time.time()
        else:
            logging.debug('Game Over')
            break
        clock.tick(fps_set)
    render.close()

def play_by_config(config_name):
    config_module = importlib.import_module('gobigger.hyper.configs.config_{}'.format(config_name))
    config = config_module.server_default_config
    server = Server(config)
    server.reset()
    render = RealtimeRender(server.map_width, server.map_height)
    server.set_render(render)
    human_team_name = '0'
    human_team_player_name = []
    bot_agents = []
    for player in server.player_manager.get_players():
        if player.team_name != human_team_name:
            bot_agents.append(BotAgent(player.name))
        else:
            human_team_player_name.append(player.name)
    fps_real = 0
    t1 = time.time()
    clock = pygame.time.Clock()
    fps_set = server.state_tick_per_second
    for i in range(100000):
        obs = server.obs()
        actions_bot = {bot_agent.name: [None, None, -1] for bot_agent in bot_agents}
        actions = {player_name: [None, None, -1] for player_name in human_team_player_name}
        x, y = (None, None)
        action_type = -1
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                x1, y1, x2, y2 = (None, None, None, None)
                action_type1 = -1
                action_type2 = -1
                if event.key == pygame.K_UP:
                    x1, y1 = (0, -1)
                if event.key == pygame.K_DOWN:
                    x1, y1 = (0, 1)
                if event.key == pygame.K_LEFT:
                    x1, y1 = (-1, 0)
                if event.key == pygame.K_RIGHT:
                    x1, y1 = (1, 0)
                if event.key == pygame.K_LEFTBRACKET:
                    action_type1 = 0
                if event.key == pygame.K_RIGHTBRACKET:
                    action_type1 = 1
                if event.key == pygame.K_BACKSLASH:
                    action_type1 = 2
                if event.key == pygame.K_w:
                    x2, y2 = (0, -1)
                if event.key == pygame.K_s:
                    x2, y2 = (0, 1)
                if event.key == pygame.K_a:
                    x2, y2 = (-1, 0)
                if event.key == pygame.K_d:
                    x2, y2 = (1, 0)
                if event.key == pygame.K_1:
                    action_type2 = 0
                if event.key == pygame.K_2:
                    action_type2 = 1
                if event.key == pygame.K_3:
                    action_type2 = 2
                actions = {human_team_player_name[0]: [x1, y1, action_type1], human_team_player_name[1]: [x2, y2, action_type2]}
        if server.last_time < server.match_time:
            actions.update(actions_bot)
            print(actions)
            server.step_state_tick(actions=actions)
            if actions is not None and x is not None and (y is not None):
                render.fill(server, direction=Vector2(x, y), fps=fps_real, last_time=server.last_time)
            else:
                render.fill(server, direction=None, fps=fps_real, last_time=server.last_time)
            render.show()
            if i % server.state_tick_per_second == 0:
                t2 = time.time()
                fps_real = server.state_tick_per_second / (t2 - t1)
                t1 = time.time()
        else:
            logging.debug('Game Over')
            break
        clock.tick(fps_set)
    render.close()

def test_add_score():
    score_old = 10
    score_add = 20
    score_new = add_score(score_old, score_add)
    assert score_new == 30

class Temp:

    def __init__(self, sequence_generator=None):
        self.sequence_generator = sequence_generator

    def generate(self):
        return self.sequence_generator.get()

def generate(self):
    return self.sequence_generator.get()

class GoBiggerEnv(gym.Env):

    def __init__(self, server_cfg=None, step_mul=2, **kwargs):
        self.server_cfg = server_cfg
        self.step_mul = step_mul
        self.init_server()

    def step(self, actions):
        for i in range(self.step_mul):
            if i == 0:
                done = self.server.step(actions=actions)
            else:
                done = self.server.step(actions=None)
        obs_raw = self.server.obs()
        global_state, player_states, info = obs_raw
        obs = [global_state, player_states]
        total_score = [global_state['leaderboard'][i] for i in range(len(global_state['leaderboard']))]
        assert len(self.last_total_score) == len(total_score)
        reward = [total_score[i] - self.last_total_score[i] for i in range(len(total_score))]
        self.last_total_score = total_score
        return (obs, reward, done, info)

    def reset(self):
        self.server.reset()
        obs_raw = self.server.obs()
        global_state, player_states, info = obs_raw
        obs = [global_state, player_states]
        self.last_total_score = [global_state['leaderboard'][i] for i in range(len(global_state['leaderboard']))]
        return obs

    def close(self):
        self.server.close()

    def seed(self, seed):
        self.server.seed(seed)

    def get_team_infos(self):
        assert hasattr(self, 'server'), 'Please call `reset()` first'
        return self.server.get_team_infos()

    def init_server(self):
        self.server = Server(cfg=self.server_cfg)

def step(self, actions):
    for i in range(self.step_mul):
        if i == 0:
            done = self.server.step(actions=actions)
        else:
            done = self.server.step(actions=None)
    obs_raw = self.server.obs()
    global_state, player_states, info = obs_raw
    obs = [global_state, player_states]
    total_score = [global_state['leaderboard'][i] for i in range(len(global_state['leaderboard']))]
    assert len(self.last_total_score) == len(total_score)
    reward = [total_score[i] - self.last_total_score[i] for i in range(len(total_score))]
    self.last_total_score = total_score
    return (obs, reward, done, info)

def reset(self):
    self.server.reset()
    obs_raw = self.server.obs()
    global_state, player_states, info = obs_raw
    obs = [global_state, player_states]
    self.last_total_score = [global_state['leaderboard'][i] for i in range(len(global_state['leaderboard']))]
    return obs

def close(self):
    self.server.close()

def init_server(self):
    self.server = Server(cfg=self.server_cfg)

def create_env_st(cfg, **kwargs):
    return GoBiggerEnv(cfg, **kwargs)

def create_env_sp(cfg, **kwargs):
    return GoBiggerSPEnv(cfg, **kwargs)

class GoBiggerSPEnv(GoBiggerEnv):

    def init_server(self):
        self.server = ServerSP(cfg=self.server_cfg)

def init_server(self):
    self.server = ServerSP(cfg=self.server_cfg)

@pytest.mark.unittest
class TestGoBiggerEnv:

    def test_env(self):
        env = GoBiggerSPEnv()
        obs = env.reset()
        env.seed(1000)
        obs, reward, done, info = env.step(actions=None)
        global_state, player_states = obs
        assert len(player_states) == env.server.team_num * env.server.player_num_per_team
        env.close()
        assert True

def test_env(self):
    env = GoBiggerSPEnv()
    obs = env.reset()
    env.seed(1000)
    obs, reward, done, info = env.step(actions=None)
    global_state, player_states = obs
    assert len(player_states) == env.server.team_num * env.server.player_num_per_team
    env.close()
    assert True

@pytest.mark.unittest
class TestGoBiggerEnv:

    def test_env(self):
        env = GoBiggerEnv()
        obs = env.reset()
        env.seed(1000)
        obs, reward, done, info = env.step(actions=None)
        global_state, player_states = obs
        assert len(player_states) == env.server.team_num * env.server.player_num_per_team
        env.close()
        assert True

def test_env(self):
    env = GoBiggerEnv()
    obs = env.reset()
    env.seed(1000)
    obs, reward, done, info = env.step(actions=None)
    global_state, player_states = obs
    assert len(player_states) == env.server.team_num * env.server.player_num_per_team
    env.close()
    assert True

@pytest.mark.unittest
class TestHumanSPPlayer:

    def get_player(self):
        cfg = Server.default_config()
        border = Border(0, 0, cfg.map_width, cfg.map_height)
        player_id = uuid.uuid1()
        return HumanSPPlayer(cfg=cfg.manager_settings.player_manager.ball_settings, team_id='0', player_id=player_id, border=border, spore_settings=cfg.manager_settings.spore_manager.ball_settings, sequence_generator=SequenceGenerator())

    def test_init(self):
        cfg = Server.default_config()
        border = Border(0, 0, cfg.map_width, cfg.map_height)
        player = self.get_player()
        player.respawn(position=border.sample())
        balls = player.get_balls()
        logging.debug('=================== test_init ===================')
        for index, ball in enumerate(balls):
            logging.debug('{} {}'.format(index, ball))

    def test_move(self):
        logging.debug('\n=================== test_move ===================')
        cfg = Server.default_config()
        border = Border(0, 0, cfg.map_width, cfg.map_height)
        player = self.get_player()
        player.respawn(position=border.sample())
        for index, ball in enumerate(player.get_balls()):
            logging.debug('{} {}'.format(index, ball))
        direction = Vector2(10, 0)
        player.move(direction=direction, duration=0.05)
        logging.debug('=================== after move ===================')
        for index, ball in enumerate(player.get_balls()):
            logging.debug('{} {}'.format(index, ball))
        for i in range(20):
            player.move()

    def test_split_move(self):
        logging.debug('\n=================== test_split_move ===================')
        cfg = Server.default_config()
        border = Border(0, 0, cfg.map_width, cfg.map_height)
        player = self.get_player()
        player.respawn(position=border.sample())
        for index, ball in enumerate(player.get_balls()):
            logging.debug('{} {}'.format(index, ball))
        food_ball = FoodBall(ball_id=uuid.uuid1(), position=border.sample(), border=border, score=40)
        player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
        player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
        player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
        player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
        player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
        player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
        player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
        player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
        logging.debug('=================== after eat ===================')
        for index, ball in enumerate(player.get_balls()):
            logging.debug('{} {}'.format(index, ball))
        player.split()
        logging.debug('=================== after split ===================')
        for index, ball in enumerate(player.get_balls()):
            logging.debug('{} {}'.format(index, ball))
        direction = Vector2(100, 0)
        for i in range(20):
            logging.debug('=================== after move {} ==================='.format(i))
            player.move(direction=direction, duration=0.05)
            for index, ball in enumerate(player.get_balls()):
                logging.debug('{} {}'.format(index, ball))
        player.split()
        player.move()

    def test_adjust(self):
        logging.debug('\n=================== test_adjust ===================')
        cfg = Server.default_config()
        border = Border(0, 0, cfg.map_width, cfg.map_height)
        player = self.get_player()
        player.respawn(position=Vector2(990, 990))
        for index, ball in enumerate(player.get_balls()):
            logging.debug('{} {}'.format(index, ball))
        player.adjust()
        logging.debug('=================== after adjust ===================')
        for index, ball in enumerate(player.get_balls()):
            logging.debug('{} {}'.format(index, ball))
        food_ball = FoodBall(ball_id=uuid.uuid1(), position=border.sample(), border=border, score=40)
        player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
        player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
        player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
        player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
        player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
        player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
        player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
        logging.debug('=================== after eat ===================')
        for index, ball in enumerate(player.get_balls()):
            logging.debug('{} {}'.format(index, ball))
        player.split()
        logging.debug('=================== after split ===================')
        for index, ball in enumerate(player.get_balls()):
            logging.debug('{} {}'.format(index, ball))
        for i in range(10):
            player.adjust()
            logging.debug('=================== after adjust {} ==================='.format(i))
            for index, ball in enumerate(player.get_balls()):
                logging.debug('{} {}'.format(index, ball))

    def test_eject(self):
        logging.debug('\n=================== test_eject ===================')
        cfg = Server.default_config()
        border = Border(0, 0, cfg.map_width, cfg.map_height)
        player = self.get_player()
        player.respawn(position=border.sample())
        for index, ball in enumerate(player.get_balls()):
            logging.debug('{} {}'.format(index, ball))
        assert isinstance(player.eject(), list)

    def test_add_balls(self):
        cfg = Server.default_config()
        border = Border(0, 0, cfg.map_width, cfg.map_height)
        player = self.get_player()
        player.respawn(position=border.sample())
        position = Vector2(100, 100)
        team_id = uuid.uuid1()
        ball_id = uuid.uuid1()
        score = CloneBall.default_config().score_init
        player_id = uuid.uuid1()
        ball1 = CloneBall(ball_id, position, border=border, score=score, team_id=team_id, player_id=player_id)
        position = Vector2(102, 102)
        team_id = uuid.uuid1()
        ball_id = uuid.uuid1()
        score = CloneBall.default_config().score_init
        player_id = uuid.uuid1()
        ball2 = CloneBall(ball_id, position, border=border, score=score, team_id=team_id, player_id=player_id)
        player.add_balls([ball1, ball2])

def test_init(self):
    cfg = Server.default_config()
    border = Border(0, 0, cfg.map_width, cfg.map_height)
    player = self.get_player()
    player.respawn(position=border.sample())
    balls = player.get_balls()
    logging.debug('=================== test_init ===================')
    for index, ball in enumerate(balls):
        logging.debug('{} {}'.format(index, ball))

def test_move(self):
    logging.debug('\n=================== test_move ===================')
    cfg = Server.default_config()
    border = Border(0, 0, cfg.map_width, cfg.map_height)
    player = self.get_player()
    player.respawn(position=border.sample())
    for index, ball in enumerate(player.get_balls()):
        logging.debug('{} {}'.format(index, ball))
    direction = Vector2(10, 0)
    player.move(direction=direction, duration=0.05)
    logging.debug('=================== after move ===================')
    for index, ball in enumerate(player.get_balls()):
        logging.debug('{} {}'.format(index, ball))
    for i in range(20):
        player.move()

def test_split_move(self):
    logging.debug('\n=================== test_split_move ===================')
    cfg = Server.default_config()
    border = Border(0, 0, cfg.map_width, cfg.map_height)
    player = self.get_player()
    player.respawn(position=border.sample())
    for index, ball in enumerate(player.get_balls()):
        logging.debug('{} {}'.format(index, ball))
    food_ball = FoodBall(ball_id=uuid.uuid1(), position=border.sample(), border=border, score=40)
    player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
    player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
    player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
    player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
    player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
    player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
    player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
    player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
    logging.debug('=================== after eat ===================')
    for index, ball in enumerate(player.get_balls()):
        logging.debug('{} {}'.format(index, ball))
    player.split()
    logging.debug('=================== after split ===================')
    for index, ball in enumerate(player.get_balls()):
        logging.debug('{} {}'.format(index, ball))
    direction = Vector2(100, 0)
    for i in range(20):
        logging.debug('=================== after move {} ==================='.format(i))
        player.move(direction=direction, duration=0.05)
        for index, ball in enumerate(player.get_balls()):
            logging.debug('{} {}'.format(index, ball))
    player.split()
    player.move()

def test_adjust(self):
    logging.debug('\n=================== test_adjust ===================')
    cfg = Server.default_config()
    border = Border(0, 0, cfg.map_width, cfg.map_height)
    player = self.get_player()
    player.respawn(position=Vector2(990, 990))
    for index, ball in enumerate(player.get_balls()):
        logging.debug('{} {}'.format(index, ball))
    player.adjust()
    logging.debug('=================== after adjust ===================')
    for index, ball in enumerate(player.get_balls()):
        logging.debug('{} {}'.format(index, ball))
    food_ball = FoodBall(ball_id=uuid.uuid1(), position=border.sample(), border=border, score=40)
    player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
    player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
    player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
    player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
    player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
    player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
    player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
    logging.debug('=================== after eat ===================')
    for index, ball in enumerate(player.get_balls()):
        logging.debug('{} {}'.format(index, ball))
    player.split()
    logging.debug('=================== after split ===================')
    for index, ball in enumerate(player.get_balls()):
        logging.debug('{} {}'.format(index, ball))
    for i in range(10):
        player.adjust()
        logging.debug('=================== after adjust {} ==================='.format(i))
        for index, ball in enumerate(player.get_balls()):
            logging.debug('{} {}'.format(index, ball))

def test_eject(self):
    logging.debug('\n=================== test_eject ===================')
    cfg = Server.default_config()
    border = Border(0, 0, cfg.map_width, cfg.map_height)
    player = self.get_player()
    player.respawn(position=border.sample())
    for index, ball in enumerate(player.get_balls()):
        logging.debug('{} {}'.format(index, ball))
    assert isinstance(player.eject(), list)

@pytest.mark.unittest
class TestHumanPlayer:

    def get_player(self):
        cfg = Server.default_config()
        border = Border(0, 0, cfg.map_width, cfg.map_height)
        player_id = uuid.uuid1()
        return HumanPlayer(cfg=cfg.manager_settings.player_manager.ball_settings, team_id='0', player_id=player_id, border=border, spore_settings=cfg.manager_settings.spore_manager.ball_settings)

    def test_init(self):
        cfg = Server.default_config()
        border = Border(0, 0, cfg.map_width, cfg.map_height)
        player = self.get_player()
        player.respawn(position=border.sample())
        balls = player.get_balls()
        logging.debug('=================== test_init ===================')
        for index, ball in enumerate(balls):
            logging.debug('{} {}'.format(index, ball))

    def test_move(self):
        logging.debug('\n=================== test_move ===================')
        cfg = Server.default_config()
        border = Border(0, 0, cfg.map_width, cfg.map_height)
        player = self.get_player()
        player.respawn(position=border.sample())
        for index, ball in enumerate(player.get_balls()):
            logging.debug('{} {}'.format(index, ball))
        direction = Vector2(10, 0)
        player.move(direction=direction, duration=0.05)
        logging.debug('=================== after move ===================')
        for index, ball in enumerate(player.get_balls()):
            logging.debug('{} {}'.format(index, ball))
        for i in range(20):
            player.move()

    def test_split_move(self):
        logging.debug('\n=================== test_split_move ===================')
        cfg = Server.default_config()
        border = Border(0, 0, cfg.map_width, cfg.map_height)
        player = self.get_player()
        player.respawn(position=border.sample())
        for index, ball in enumerate(player.get_balls()):
            logging.debug('{} {}'.format(index, ball))
        food_ball = FoodBall(ball_id=uuid.uuid1(), position=border.sample(), border=border, score=40)
        player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
        player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
        player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
        player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
        player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
        player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
        player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
        player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
        logging.debug('=================== after eat ===================')
        for index, ball in enumerate(player.get_balls()):
            logging.debug('{} {}'.format(index, ball))
        player.split()
        logging.debug('=================== after split ===================')
        for index, ball in enumerate(player.get_balls()):
            logging.debug('{} {}'.format(index, ball))
        direction = Vector2(100, 0)
        for i in range(20):
            logging.debug('=================== after move {} ==================='.format(i))
            player.move(direction=direction, duration=0.05)
            for index, ball in enumerate(player.get_balls()):
                logging.debug('{} {}'.format(index, ball))
        player.split()
        player.move()

    def test_adjust(self):
        logging.debug('\n=================== test_adjust ===================')
        cfg = Server.default_config()
        border = Border(0, 0, cfg.map_width, cfg.map_height)
        player = self.get_player()
        player.respawn(position=Vector2(990, 990))
        for index, ball in enumerate(player.get_balls()):
            logging.debug('{} {}'.format(index, ball))
        player.adjust()
        logging.debug('=================== after adjust ===================')
        for index, ball in enumerate(player.get_balls()):
            logging.debug('{} {}'.format(index, ball))
        food_ball = FoodBall(ball_id=uuid.uuid1(), position=border.sample(), border=border, score=40)
        player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
        player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
        player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
        player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
        player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
        player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
        player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
        logging.debug('=================== after eat ===================')
        for index, ball in enumerate(player.get_balls()):
            logging.debug('{} {}'.format(index, ball))
        player.split()
        logging.debug('=================== after split ===================')
        for index, ball in enumerate(player.get_balls()):
            logging.debug('{} {}'.format(index, ball))
        for i in range(10):
            player.adjust()
            logging.debug('=================== after adjust {} ==================='.format(i))
            for index, ball in enumerate(player.get_balls()):
                logging.debug('{} {}'.format(index, ball))

    def test_eject(self):
        logging.debug('\n=================== test_eject ===================')
        cfg = Server.default_config()
        border = Border(0, 0, cfg.map_width, cfg.map_height)
        player = self.get_player()
        player.respawn(position=border.sample())
        for index, ball in enumerate(player.get_balls()):
            logging.debug('{} {}'.format(index, ball))
        assert isinstance(player.eject(), list)

    def test_add_balls(self):
        cfg = Server.default_config()
        border = Border(0, 0, cfg.map_width, cfg.map_height)
        player = self.get_player()
        player.respawn(position=border.sample())
        position = Vector2(100, 100)
        team_id = uuid.uuid1()
        ball_id = uuid.uuid1()
        score = CloneBall.default_config().score_init
        player_id = uuid.uuid1()
        ball1 = CloneBall(ball_id, position, border=border, score=score, team_id=team_id, player_id=player_id)
        position = Vector2(102, 102)
        team_id = uuid.uuid1()
        ball_id = uuid.uuid1()
        score = CloneBall.default_config().score_init
        player_id = uuid.uuid1()
        ball2 = CloneBall(ball_id, position, border=border, score=score, team_id=team_id, player_id=player_id)
        player.add_balls([ball1, ball2])

def test_init(self):
    cfg = Server.default_config()
    border = Border(0, 0, cfg.map_width, cfg.map_height)
    player = self.get_player()
    player.respawn(position=border.sample())
    balls = player.get_balls()
    logging.debug('=================== test_init ===================')
    for index, ball in enumerate(balls):
        logging.debug('{} {}'.format(index, ball))

def test_move(self):
    logging.debug('\n=================== test_move ===================')
    cfg = Server.default_config()
    border = Border(0, 0, cfg.map_width, cfg.map_height)
    player = self.get_player()
    player.respawn(position=border.sample())
    for index, ball in enumerate(player.get_balls()):
        logging.debug('{} {}'.format(index, ball))
    direction = Vector2(10, 0)
    player.move(direction=direction, duration=0.05)
    logging.debug('=================== after move ===================')
    for index, ball in enumerate(player.get_balls()):
        logging.debug('{} {}'.format(index, ball))
    for i in range(20):
        player.move()

def test_split_move(self):
    logging.debug('\n=================== test_split_move ===================')
    cfg = Server.default_config()
    border = Border(0, 0, cfg.map_width, cfg.map_height)
    player = self.get_player()
    player.respawn(position=border.sample())
    for index, ball in enumerate(player.get_balls()):
        logging.debug('{} {}'.format(index, ball))
    food_ball = FoodBall(ball_id=uuid.uuid1(), position=border.sample(), border=border, score=40)
    player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
    player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
    player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
    player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
    player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
    player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
    player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
    player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
    logging.debug('=================== after eat ===================')
    for index, ball in enumerate(player.get_balls()):
        logging.debug('{} {}'.format(index, ball))
    player.split()
    logging.debug('=================== after split ===================')
    for index, ball in enumerate(player.get_balls()):
        logging.debug('{} {}'.format(index, ball))
    direction = Vector2(100, 0)
    for i in range(20):
        logging.debug('=================== after move {} ==================='.format(i))
        player.move(direction=direction, duration=0.05)
        for index, ball in enumerate(player.get_balls()):
            logging.debug('{} {}'.format(index, ball))
    player.split()
    player.move()

def test_adjust(self):
    logging.debug('\n=================== test_adjust ===================')
    cfg = Server.default_config()
    border = Border(0, 0, cfg.map_width, cfg.map_height)
    player = self.get_player()
    player.respawn(position=Vector2(990, 990))
    for index, ball in enumerate(player.get_balls()):
        logging.debug('{} {}'.format(index, ball))
    player.adjust()
    logging.debug('=================== after adjust ===================')
    for index, ball in enumerate(player.get_balls()):
        logging.debug('{} {}'.format(index, ball))
    food_ball = FoodBall(ball_id=uuid.uuid1(), position=border.sample(), border=border, score=40)
    player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
    player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
    player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
    player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
    player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
    player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
    player.get_balls()[0].eat(food_ball, clone_num=len(player.get_balls()))
    logging.debug('=================== after eat ===================')
    for index, ball in enumerate(player.get_balls()):
        logging.debug('{} {}'.format(index, ball))
    player.split()
    logging.debug('=================== after split ===================')
    for index, ball in enumerate(player.get_balls()):
        logging.debug('{} {}'.format(index, ball))
    for i in range(10):
        player.adjust()
        logging.debug('=================== after adjust {} ==================='.format(i))
        for index, ball in enumerate(player.get_balls()):
            logging.debug('{} {}'.format(index, ball))

def test_eject(self):
    logging.debug('\n=================== test_eject ===================')
    cfg = Server.default_config()
    border = Border(0, 0, cfg.map_width, cfg.map_height)
    player = self.get_player()
    player.respawn(position=border.sample())
    for index, ball in enumerate(player.get_balls()):
        logging.debug('{} {}'.format(index, ball))
    assert isinstance(player.eject(), list)

class FoodBall(BaseBall):
    """
    Overview:
        - characteristic:
        * Can't move, can only be eaten, randomly generated
    """

    @staticmethod
    def default_config():
        cfg = BaseBall.default_config()
        cfg.update(dict(score_min=0.5, score_max=0.5))
        return EasyDict(cfg)

    def __init__(self, ball_id, position, score, border, **kwargs):
        super(FoodBall, self).__init__(ball_id, position, score=score, border=border, **kwargs)
        self.check_border()

    def move(self, direction, duration):
        logging.debug('FoodBall can not move')
        return

    def eat(self, ball):
        logging.debug('FoodBall can not eat others')
        return

    def save(self):
        return [self.position.x, self.position.y, self.radius]

@staticmethod
def default_config():
    cfg = BaseBall.default_config()
    cfg.update(dict(score_min=0.5, score_max=0.5))
    return EasyDict(cfg)

def move(self, direction, duration):
    logging.debug('FoodBall can not move')
    return

def eat(self, ball):
    logging.debug('FoodBall can not eat others')
    return

@total_ordering
class BaseBall(ABC):
    """
    Overview:
        Base class of all balls
    """

    @staticmethod
    def default_config():
        """
        Overview:
            Default config
        """
        cfg = dict()
        return EasyDict(cfg)

    def __init__(self, ball_id, position, score, border, **kwargs):
        """
        Parameters:
             vel <Vector2> : the direction of the ball's speed 
             acc <Vector2> : the direction of the ball's acceleration
        """
        self.ball_id = ball_id
        self.position = position
        kwargs = EasyDict(kwargs)
        cfg = BaseBall.default_config()
        cfg = deep_merge_dicts(cfg, kwargs)
        self.score = score
        self.border = border
        self.radius = self.score_to_radius(self.score)
        self.is_remove = False
        self.quad_node = None

    def set_score(self, score: float) -> None:
        self.score = score
        self.radius = self.score_to_radius(self.score)

    def radius_to_score(self, radius):
        return (math.pow(radius, 2) - 0.15) / 0.042 * 100

    def score_to_radius(self, score):
        return math.sqrt(score / 100 * 0.042 + 0.15)

    def move(self, direction, duration):
        """
        Overview:
            Realize the movement of the ball, pass in the direction and time parameters, and return the new position
        Parameters:
            direction <Vector2>: A point in the unit circle
            duration <float>: time
        Returns:
            position <Vector2>: position after moving 
        """
        raise NotImplementedError

    def eat(self, ball):
        """
        Overview:
            Describe the rules of eating and being eaten
        Parameters:
            ball <BaseBall>: Eaten ball
        """
        raise NotImplementedError

    def remove(self):
        """
        Overview:
            Things to do when being removed from the map
        """
        self.is_remove = True

    def check_border(self):
        """
        Overview:
            Check to see if the position of the ball exceeds the bounds of the map. 
            If it exceeds, the speed and acceleration in the corresponding direction will be zeroed, and the position will be edged
        """
        if self.position.x < self.border.minx or self.position.x > self.border.maxx:
            self.position.x = max(self.position.x, self.border.minx)
            self.position.x = min(self.position.x, self.border.maxx)
        if self.position.y < self.border.miny or self.position.y > self.border.maxy:
            self.position.y = max(self.position.y, self.border.miny)
            self.position.y = min(self.position.y, self.border.maxy)

    def get_dis(self, ball):
        """
        Overview:
            Get the distance between the centers of the two balls
        Parameters:
            ball <BaseBall>: another ball
        """
        return (self.position - ball.position).length()

    def judge_cover(self, ball):
        """
        Overview:
            Determine whether the center of the two balls is covered
        Parameters:
            ball <BaseBall>: another ball
        Returns:
            is_covered <bool>: covered or not
        """
        if ball.ball_id == self.ball_id:
            return False
        dis = self.get_dis(ball)
        if self.radius > dis or ball.radius > dis:
            return True
        else:
            return False

    def judge_in_rectangle(self, rectangle):
        """
        Overview:
            Determine if the ball and rectangle intersect
        Parameters:
            rectangle <List>: left_top_x, left_top_y, right_bottom_x, right_bottom_y
        Returns:
            <bool> : intersect or not
        """
        dx = rectangle[0] - self.position.x if rectangle[0] > self.position.x else self.position.x - rectangle[2] if self.position.x > rectangle[2] else 0
        dy = rectangle[1] - self.position.y if rectangle[1] > self.position.y else self.position.y - rectangle[3] if self.position.y > rectangle[3] else 0
        return dx ** 2 + dy ** 2 <= self.radius ** 2

    def __repr__(self) -> str:
        return 'position={}, score={:.3f}, radius={:.3f}'.format(self.position, self.score, self.radius)

    def __eq__(self, other):
        return self.score == other.score

    def __le__(self, other):
        return self.score < other.score

    def __gt__(self, other):
        return self.score > other.score

def __repr__(self) -> str:
    return 'position={}, score={:.3f}, radius={:.3f}'.format(self.position, self.score, self.radius)

class SporeBall(BaseBall):
    """
    Overview:
        Spores spit out by the player ball
        - characteristic:
        * Can't move actively
        * can not eat
        * Can be eaten by CloneBall and ThornsBall
        * There is an initial velocity at birth, and it decays to 0 within a period of time
    """

    @staticmethod
    def default_config():
        cfg = BaseBall.default_config()
        cfg.update(dict(score_init=1.5, vel_init=50, vel_zero_frame=10))
        return EasyDict(cfg)

    def __init__(self, ball_id, position, border, score, direction=Vector2(0, 0), owner=-1, **kwargs):
        kwargs = EasyDict(kwargs)
        cfg = SporeBall.default_config()
        cfg = deep_merge_dicts(cfg, kwargs)
        super(SporeBall, self).__init__(ball_id, position, score=score, border=border, **cfg)
        self.score_init = cfg.score_init
        self.vel_init = cfg.vel_init
        self.vel_zero_frame = cfg.vel_zero_frame
        self.direction = direction.normalize()
        self.vel = self.vel_init * self.direction
        self.vel_piece = self.vel / self.vel_zero_frame
        self.owner = owner
        self.move_frame = 0
        if self.score != self.score_init:
            self.set_score(self.score_init)
        self.moving = True
        self.check_border()

    def move(self, direction=None, duration=0.05):
        assert direction is None
        assert duration > 0
        if self.moving:
            self.position = self.position + self.vel * duration
            self.move_frame += 1
            if self.move_frame < self.vel_zero_frame:
                self.vel -= self.vel_piece
            else:
                self.vel = Vector2(0, 0)
                self.vel_piece = Vector2(0, 0)
                self.moving = False
        self.check_border()
        return True

    def eat(self, ball):
        logging.debug('SporeBall can not eat others')
        return

    def save(self):
        return [self.position.x, self.position.y, self.radius]

@staticmethod
def default_config():
    cfg = BaseBall.default_config()
    cfg.update(dict(score_init=1.5, vel_init=50, vel_zero_frame=10))
    return EasyDict(cfg)

def eat(self, ball):
    logging.debug('SporeBall can not eat others')
    return

class CloneBall(BaseBall):
    """
    Overview:
        One of the balls that a single player can control
        - characteristic:
        * Can move
        * Can eat any other ball smaller than itself
        * Under the control of the player, the movement can be stopped immediately and contracted towards the center of mass of the player
        * Skill 1: Split each unit into two equally
        * Skill 2: Spit spores forward
        * There is a percentage of weight attenuation, and the radius will shrink as the weight attenuates
    """

    @staticmethod
    def default_config():
        cfg = BaseBall.default_config()
        cfg.update(dict(acc_weight=100, vel_max=20, score_init=1, part_num_max=16, on_thorns_part_num=10, on_thorns_part_score_max=3, split_score_min=2.5, eject_score_min=2.5, recombine_frame=320, split_vel_zero_frame=40, score_decay_min=2600, score_decay_rate_per_frame=5e-05, center_acc_weight=10))
        return EasyDict(cfg)

    def __init__(self, ball_id, position, score, border, team_id, player_id, vel_given=Vector2(0, 0), acc_given=Vector2(0, 0), from_split=False, from_thorns=False, split_direction=Vector2(0, 0), spore_settings=SporeBall.default_config(), sequence_generator=None, **kwargs):
        kwargs = EasyDict(kwargs)
        cfg = CloneBall.default_config()
        cfg = deep_merge_dicts(cfg, kwargs)
        super(CloneBall, self).__init__(ball_id, position, score, border, **cfg)
        self.acc_weight = cfg.acc_weight
        self.vel_max = cfg.vel_max
        self.score_init = cfg.score_init
        self.part_num_max = cfg.part_num_max
        self.on_thorns_part_num = cfg.on_thorns_part_num
        self.on_thorns_part_score_max = cfg.on_thorns_part_score_max
        self.split_score_min = cfg.split_score_min
        self.eject_score_min = cfg.eject_score_min
        self.recombine_frame = cfg.recombine_frame
        self.split_vel_zero_frame = cfg.split_vel_zero_frame
        self.score_decay_min = cfg.score_decay_min
        self.score_decay_rate_per_frame = cfg.score_decay_rate_per_frame
        self.center_acc_weight = cfg.center_acc_weight
        self.spore_settings = spore_settings
        self.sequence_generator = sequence_generator
        self.cfg = cfg
        self.team_id = team_id
        self.player_id = player_id
        self.vel_given = vel_given
        self.acc_given = acc_given
        if from_split:
            self.vel_split = self.cal_split_vel_init_from_split(self.radius) * split_direction
        elif from_thorns:
            self.vel_split = self.cal_split_vel_init_from_thorns(self.radius) * split_direction
        else:
            self.vel_split = Vector2(0, 0)
        self.vel_split_piece = self.vel_split / self.split_vel_zero_frame
        self.split_frame = 0
        self.frame_since_last_split = 0
        self.vel = self.vel_given + self.vel_split
        self.update_direction()
        self.check_border()

    def update_direction(self):
        if self.vel.length() != 0:
            self.direction = copy.deepcopy(self.vel.normalize())
        else:
            self.direction = Vector2(random.random(), random.random()).normalize()

    def cal_vel_max(self, radius, ratio):
        return (2.35 + 5.66 / radius) * ratio

    def cal_split_vel_init_from_split(self, radius):
        return (4.75 + 0.95 * radius) / (self.split_vel_zero_frame / 20) * 2

    def cal_split_vel_init_from_thorns(self, radius):
        return (13.0 - radius) / (self.split_vel_zero_frame / 20) * 2

    def move(self, given_acc=None, given_acc_center=None, duration=0.05):
        """
        Overview:
            Realize the movement of the ball, pass in the direction and time parameters
        """
        if given_acc is not None:
            if given_acc.length != 0:
                given_acc = given_acc if given_acc.length() < 1 else given_acc.normalize()
                self.acc_given = given_acc * self.acc_weight
        else:
            given_acc = self.acc_given / self.acc_weight
        if given_acc_center is not None:
            given_acc_center = given_acc_center / self.radius
            if given_acc_center.length() != 0 and given_acc_center.length() > 1:
                given_acc_center = given_acc_center.normalize()
            self.acc_given_center = given_acc_center * self.center_acc_weight
        else:
            given_acc_center = Vector2(0, 0)
            self.acc_given_center = Vector2(0, 0)
        self.acc_given_total = self.acc_given + self.acc_given_center
        vel_max_ratio_given = given_acc.length()
        vel_max_ratio_center = given_acc_center.length()
        vel_max_ratio = max(vel_max_ratio_given, vel_max_ratio_center)
        if self.split_frame < self.split_vel_zero_frame:
            self.vel_split -= self.vel_split_piece
            self.split_frame += 1
        else:
            self.vel_split = Vector2(0, 0)
        self.vel_given = self.vel_given + self.acc_given_total * duration
        self.vel_max_ball = self.cal_vel_max(self.radius, ratio=vel_max_ratio)
        self.vel_given = format_vector(self.vel_given, self.vel_max_ball)
        self.vel = self.vel_given + self.vel_split
        self.position = self.position + self.vel * duration
        self.update_direction()
        self.frame_since_last_split += 1
        self.check_border()

    def eat(self, ball, clone_num=None):
        """
        Parameters:
            clone_num <int>: The total number of balls for the current player
        """
        if isinstance(ball, SporeBall) or isinstance(ball, FoodBall) or isinstance(ball, CloneBall):
            self.set_score(add_score(self.score, ball.score))
        elif isinstance(ball, ThornsBall):
            assert clone_num is not None
            self.set_score(add_score(self.score, ball.score))
            if clone_num < self.part_num_max:
                split_num = min(self.part_num_max - clone_num, self.on_thorns_part_num)
                return self.on_thorns(split_num=split_num)
        else:
            logging.debug('CloneBall can not eat {}'.format(type(ball)))
        self.check_border()
        return True

    def on_thorns(self, split_num) -> list:
        """
        Overview:
            Split after encountering thorns, calculate the score, position, speed, acceleration of each ball after splitting
        Parameters:
            split_num <int>: Number of splits added
        Returns:
            Return a list that contains the newly added balls after the split, the distribution of the split balls is a circle and the center of the circle has a ball
        """
        around_score = min(self.score / (split_num + 1), self.on_thorns_part_score_max)
        around_radius = self.score_to_radius(around_score)
        middle_score = self.score - around_score * split_num
        self.set_score(middle_score)
        around_positions = []
        around_split_directions = []
        for i in range(split_num):
            angle = 2 * math.pi * (i + 1) / split_num
            unit_x = math.cos(angle)
            unit_y = math.sin(angle)
            split_direction = Vector2(unit_x, unit_y)
            around_position = self.position + Vector2((self.radius + around_radius) * unit_x, (self.radius + around_radius) * unit_y)
            around_positions.append(around_position)
            around_split_directions.append(split_direction)
        balls = []
        for p, s in zip(around_positions, around_split_directions):
            ball_id = uuid.uuid1() if self.sequence_generator is None else self.sequence_generator.get()
            around_ball = CloneBall(ball_id=ball_id, position=p, score=around_score, border=self.border, team_id=self.team_id, player_id=self.player_id, vel_given=copy.deepcopy(self.vel_given), acc_given=copy.deepcopy(self.acc_given), from_split=False, from_thorns=True, split_direction=s, spore_settings=self.spore_settings, sequence_generator=self.sequence_generator, **self.cfg)
            balls.append(around_ball)
        return balls

    def eject(self, direction=None) -> list:
        """
        Overview:
            When spit out spores, the spores spit out must be in the moving direction of the ball, and the position is tangent to the original ball after spitting out
        Returns:
            Return a list containing the spores spit out
        """
        if direction is None or direction.length() == 0:
            direction = self.direction
        else:
            direction = direction.normalize()
        if self.score >= self.eject_score_min:
            spore_score = self.spore_settings.score_init
            self.set_score(self.score - spore_score)
            spore_radius = self.score_to_radius(spore_score)
            position = self.position + direction * (self.radius + spore_radius)
            return SporeBall(ball_id=uuid.uuid1(), position=position, border=self.border, score=spore_score, direction=direction, owner=self.player_id, **self.spore_settings)
        else:
            return False

    def split(self, clone_num, direction=None) -> list:
        """
        Overview:
            Active splitting, the two balls produced by splitting have the same volume, and their positions are tangent to the forward direction
        Parameters:
            clone_num <int>: The total number of balls for the current player
        Returns:
            The return value is the new ball after the split
        """
        if direction is None or direction.length() == 0:
            direction = self.direction
        else:
            direction = direction.normalize()
        if self.score >= self.split_score_min and clone_num < self.part_num_max:
            split_score = self.score / 2
            self.set_score(split_score)
            clone_num += 1
            position = self.position + direction * (self.radius * 2)
            ball_id = uuid.uuid1() if self.sequence_generator is None else self.sequence_generator.get()
            return CloneBall(ball_id=ball_id, position=position, score=self.score, border=self.border, team_id=self.team_id, player_id=self.player_id, vel_given=copy.deepcopy(self.vel_given), acc_given=copy.deepcopy(self.acc_given), from_split=True, from_thorns=False, split_direction=direction, spore_settings=self.spore_settings, sequence_generator=self.sequence_generator, **self.cfg)
        else:
            return False

    def rigid_collision(self, ball):
        """
        Overview:
            When two balls collide, We need to determine whether the two balls belong to the same player
            A. If not, do nothing until one party is eaten at the end
            B. If the two balls are the same owner, judge whether the age of the two is full or not meet the fusion condition, if they are satisfied, do nothing.
            C. If the two balls are the same owner, judge whether the age of the two is full or not meet the fusion condition, Then the two balls will collide with rigid bodies
            This function completes the C part: the rigid body collision part, the logic is as follows:
             1. To determine the degree of fusion of the two balls, use [the radius of both] and subtract [the distance between the two] as the magnitude of the force
             2. Calculate the coefficient according to the weight, the larger the weight, the smaller the coefficient will be
             3. Correct the position of the two according to the coefficient and force
        Parameters:
            ball <CloneBall>: another ball
        Returns:
            state <bool>: the operation is successful or not
        """
        if ball.ball_id == self.ball_id:
            return True
        assert isinstance(ball, CloneBall), 'ball is not CloneBall but {}'.format(type(ball))
        assert self.player_id == ball.player_id
        assert self.frame_since_last_split < self.recombine_frame or ball.frame_since_last_split < ball.recombine_frame
        p = ball.position - self.position
        d = p.length()
        if self.radius + ball.radius > d:
            f = min(self.radius + ball.radius - d, (self.radius + ball.radius - d) / (d + 1e-08))
            self.position = self.position - f * p * (ball.score / (self.score + ball.score))
            ball.position = ball.position + f * p * (self.score / (self.score + ball.score))
        else:
            print('WARNINGS: self.radius ({}) + ball.radius ({}) <= d ({})'.format(self.radius, ball.radius, d))
        self.check_border()
        ball.check_border()
        return True

    def judge_rigid(self, ball):
        """
        Overview:
            Determine whether two balls will collide with a rigid body
        Parameters:
            ball <CloneBall>: another ball
        Returns:
            <bool>: collide or not
        """
        return self.frame_since_last_split < self.recombine_frame or ball.frame_since_last_split < ball.recombine_frame

    def score_decay(self):
        """
        Overview: 
            Control the score of the ball to decay over time
        """
        if self.score > self.score_decay_min:
            self.set_score(self.score * (1 - self.score_decay_rate_per_frame * math.sqrt(self.radius)))
        return True

    def flush_frame_since_last_split(self):
        self.frame_since_last_split = 0
        return True

    def __repr__(self) -> str:
        return '{}, vel_given={}, acc_given={}, frame_since_last_split={:.3f}, player_id={}, direction={}, team_id={}'.format(super().__repr__(), self.vel_given, self.acc_given, self.frame_since_last_split, self.player_id, self.direction, self.team_id)

    def save(self):
        return [self.position.x, self.position.y, self.radius, self.direction.x, self.direction.y, self.player_id, self.team_id]

@staticmethod
def default_config():
    cfg = BaseBall.default_config()
    cfg.update(dict(acc_weight=100, vel_max=20, score_init=1, part_num_max=16, on_thorns_part_num=10, on_thorns_part_score_max=3, split_score_min=2.5, eject_score_min=2.5, recombine_frame=320, split_vel_zero_frame=40, score_decay_min=2600, score_decay_rate_per_frame=5e-05, center_acc_weight=10))
    return EasyDict(cfg)

def eat(self, ball, clone_num=None):
    """
        Parameters:
            clone_num <int>: The total number of balls for the current player
        """
    if isinstance(ball, SporeBall) or isinstance(ball, FoodBall) or isinstance(ball, CloneBall):
        self.set_score(add_score(self.score, ball.score))
    elif isinstance(ball, ThornsBall):
        assert clone_num is not None
        self.set_score(add_score(self.score, ball.score))
        if clone_num < self.part_num_max:
            split_num = min(self.part_num_max - clone_num, self.on_thorns_part_num)
            return self.on_thorns(split_num=split_num)
    else:
        logging.debug('CloneBall can not eat {}'.format(type(ball)))
    self.check_border()
    return True

class ThornsBall(BaseBall):
    """
    Overview:
        - characteristic:
        * Can't move actively
        * Can eat spores. When eating spores, it will inherit the momentum of the spores and move a certain distance.
        * Can only be eaten by balls heavier than him. After eating, it will split the host into multiple smaller units.
        * Nothing happens when a ball lighter than him passes by
    """

    @staticmethod
    def default_config():
        cfg = BaseBall.default_config()
        cfg.update(dict(score_min=3, score_max=5, eat_spore_vel_init=4, eat_spore_vel_zero_frame=10))
        return EasyDict(cfg)

    def __init__(self, ball_id, position, score, border, **kwargs):
        kwargs = EasyDict(kwargs)
        cfg = ThornsBall.default_config()
        cfg = deep_merge_dicts(cfg, kwargs)
        super(ThornsBall, self).__init__(ball_id, position, score=score, border=border, **cfg)
        self.score_min = cfg.score_min
        self.score_max = cfg.score_max
        self.eat_spore_vel_init = cfg.eat_spore_vel_init
        self.eat_spore_vel_zero_frame = cfg.eat_spore_vel_zero_frame
        self.move_frame = 0
        self.vel = Vector2(0, 0)
        self.vel_piece = Vector2(0, 0)
        self.moving = False
        self.check_border()

    def move(self, direction=None, duration=0.05, **kwargs):
        assert duration > 0
        if self.moving:
            self.position = self.position + self.vel * duration
            self.move_frame += 1
            if self.move_frame < self.eat_spore_vel_zero_frame:
                self.vel = self.vel - self.vel_piece
            else:
                self.vel = Vector2(0, 0)
                self.vel_piece = Vector2(0, 0)
                self.moving = False
        self.check_border()
        return True

    def eat(self, ball):
        if isinstance(ball, SporeBall):
            self.set_score(add_score(self.score, ball.score))
            if ball.vel.length() > 0:
                self.vel = self.eat_spore_vel_init * ball.vel.normalize()
                self.vel_piece = self.vel / self.eat_spore_vel_zero_frame
                self.move_time = 0
                self.moving = True
        else:
            logging.debug('ThornsBall can not eat {}'.format(type(ball)))
        return True

    def set_score(self, score: float) -> None:
        self.score = score
        if self.score > self.score_max:
            self.score = self.score_max
        elif self.score < self.score_min:
            self.score = self.score_min
        self.radius = self.score_to_radius(self.score)

    def save(self):
        return [self.position.x, self.position.y, self.radius]

@staticmethod
def default_config():
    cfg = BaseBall.default_config()
    cfg.update(dict(score_min=3, score_max=5, eat_spore_vel_init=4, eat_spore_vel_zero_frame=10))
    return EasyDict(cfg)

def eat(self, ball):
    if isinstance(ball, SporeBall):
        self.set_score(add_score(self.score, ball.score))
        if ball.vel.length() > 0:
            self.vel = self.eat_spore_vel_init * ball.vel.normalize()
            self.vel_piece = self.vel / self.eat_spore_vel_zero_frame
            self.move_time = 0
            self.moving = True
    else:
        logging.debug('ThornsBall can not eat {}'.format(type(ball)))
    return True

@pytest.mark.unittest
class TestSporesBall:

    def test_move(self):
        ball_id = uuid.uuid1()
        border = Border(0, 0, 1000, 1000)
        position = Vector2(100, 100)
        direction = Vector2(1, 0)
        spore_ball = SporeBall(ball_id, position, border=border, score=2, direction=direction)
        logging.debug('direction={}, position={}, vel={}, move_frame={}'.format(spore_ball.direction, spore_ball.position, spore_ball.vel, spore_ball.move_frame))
        for i in range(10):
            spore_ball.move(duration=0.05)
            logging.debug('[{}] direction={}, position={}, vel={}, move_frame={}'.format(i, spore_ball.direction, spore_ball.position, spore_ball.vel, spore_ball.move_frame))
        assert True

    def test_eat(self):
        ball_id = uuid.uuid1()
        border = Border(0, 0, 1000, 1000)
        position = Vector2(100, 100)
        direction = Vector2(1, 0)
        spore_ball = SporeBall(ball_id, position, border=border, score=2, direction=direction)
        spore_ball.eat(ball=None)

def test_move(self):
    ball_id = uuid.uuid1()
    border = Border(0, 0, 1000, 1000)
    position = Vector2(100, 100)
    direction = Vector2(1, 0)
    spore_ball = SporeBall(ball_id, position, border=border, score=2, direction=direction)
    logging.debug('direction={}, position={}, vel={}, move_frame={}'.format(spore_ball.direction, spore_ball.position, spore_ball.vel, spore_ball.move_frame))
    for i in range(10):
        spore_ball.move(duration=0.05)
        logging.debug('[{}] direction={}, position={}, vel={}, move_frame={}'.format(i, spore_ball.direction, spore_ball.position, spore_ball.vel, spore_ball.move_frame))
    assert True

@pytest.mark.unittest
class TestCloneBall:

    def get_clone(self, score=None):
        border = Border(0, 0, 1000, 1000)
        position = Vector2(100, 100)
        team_id = uuid.uuid1()
        ball_id = uuid.uuid1()
        score = CloneBall.default_config().score_init if score is None else score
        player_id = uuid.uuid1()
        return CloneBall(ball_id, position, border=border, score=score, team_id=team_id, player_id=player_id)

    def get_thorns(self):
        ball_id = uuid.uuid1()
        border = Border(0, 0, 1000, 1000)
        thorns_position = Vector2(100, 100)
        thorns_score = ThornsBall.default_config().score_min
        return ThornsBall(ball_id, thorns_position, border=border, score=thorns_score)

    def get_food(self):
        ball_id = uuid.uuid1()
        border = Border(0, 0, 1000, 1000)
        position = Vector2(200, 200)
        return FoodBall(ball_id, position, border=border, score=5)

    def test_init(self):
        clone_ball = self.get_clone()
        assert True

    def test_eat_food(self):
        clone_ball = self.get_clone()
        food_ball = self.get_food()
        clone_score = clone_ball.score
        food_score = food_ball.score
        clone_ball.eat(food_ball, clone_num=1)
        logging.debug('clone_score={}, food_score={}, now_score={}, now_score={}'.format(clone_score, food_score, clone_ball.score, clone_ball.score))
        assert True

    def test_eat_thorns(self):
        clone_ball = self.get_clone()
        thorns_ball = self.get_thorns()
        clone_score = clone_ball.score
        thorns_score = thorns_ball.score
        logging.debug('clone_ball={}'.format(clone_ball))
        logging.debug('===================== first eat =====================')
        rets = clone_ball.eat(thorns_ball, clone_num=1)
        logging.debug('[original] {} eat thorns_score={}'.format(clone_ball, thorns_score))
        for i, ret in enumerate(rets):
            logging.debug('[{}] {}'.format(i, ret))
        clone_num = 1 + len(rets)
        logging.debug('===================== second eat =====================')
        rets = clone_ball.eat(thorns_ball, clone_num=clone_num)
        logging.debug('[original] {} eat thorns_score={}'.format(clone_ball, thorns_score))
        for i, ret in enumerate(rets):
            logging.debug('[{}] {}'.format(i, ret))

    def test_move(self):
        border = Border(0, 0, 1000, 1000)
        clone_ball = self.get_clone(score=16)
        direction = Vector2(1, 0) * 1000
        logging.debug('===================== before move =====================')
        logging.debug('position={}, vel={}, vel_max={}'.format(clone_ball.position, clone_ball.vel, clone_ball.vel_max))
        for i in range(10):
            clone_ball.move(given_acc=direction, given_acc_center=Vector2(0, 0), duration=0.05)
            logging.debug('===================== after move =====================')
            logging.debug('position={}, vel={}, vel_max={}'.format(clone_ball.position, clone_ball.vel, clone_ball.vel_max))
        for i in range(20):
            clone_ball.move(given_acc=None, given_acc_center=None, duration=0.05)
            logging.debug('===================== move after stop =====================')
            logging.debug('position={}, vel={}, vel_max={}'.format(clone_ball.position, clone_ball.vel, clone_ball.vel_max))
        clone_ball.split(1)
        for i in range(20):
            clone_ball.move(given_acc=None, given_acc_center=None, duration=0.05)
            logging.debug('===================== move after stop =====================')
            logging.debug('position={}, vel={}, vel_max={}'.format(clone_ball.position, clone_ball.vel, clone_ball.vel_max))

    def test_eject(self):
        logging.debug('===================== test eject =====================')
        eject_score_min = CloneBall.default_config().eject_score_min
        clone_ball = self.get_clone(score=eject_score_min)
        rets = clone_ball.eject()
        logging.debug('clone_ball: {}, eject_score_min={}'.format(clone_ball, eject_score_min))
        if clone_ball.score < eject_score_min:
            assert rets
        else:
            logging.debug('spore_ball: {}'.format(rets))
        assert not clone_ball.eject()

    def test_split(self):
        logging.debug('===================== test split =====================')
        split_score_min = CloneBall.default_config().split_score_min
        clone_ball = self.get_clone(score=split_score_min)
        logging.debug('clone_ball: {}, split_score_min={}'.format(clone_ball, split_score_min))
        rets = clone_ball.split(1)
        logging.debug('===================== after split =====================')
        logging.debug('[original] {}'.format(clone_ball))
        logging.debug('[new     ] {}'.format(rets))
        clone_ball = self.get_clone()
        assert not clone_ball.split(1)

    def test_rigid_collision(self):
        border = Border(0, 0, 1000, 1000)
        position = Vector2(100, 100)
        player_id = uuid.uuid1()
        ball_id1 = uuid.uuid1()
        ball_id2 = uuid.uuid1()
        team_id = uuid.uuid1()
        clone_ball_1 = CloneBall(ball_id1, position=Vector2(100, 100), border=border, score=5, team_id=team_id, player_id=player_id)
        clone_ball_2 = CloneBall(ball_id2, position=Vector2(100, 110), border=border, score=6, team_id=team_id, player_id=player_id)
        logging.debug('===================== test rigid_collision =====================')
        logging.debug('clone_ball_1: {}'.format(clone_ball_1))
        logging.debug('clone_ball_2: {}'.format(clone_ball_2))
        clone_ball_1.rigid_collision(clone_ball_2)
        logging.debug('===================== after rigid_collision =====================')
        logging.debug('clone_ball_1: {}'.format(clone_ball_1))
        logging.debug('clone_ball_2: {}'.format(clone_ball_2))

    def test_move_wo_stop_flag(self):
        clone_ball = self.get_clone()
        clone_ball.move(given_acc=None, given_acc_center=None, duration=0.05)
        clone_ball.move(given_acc=None, given_acc_center=Vector2(1, 0), duration=0.05)
        clone_ball.move(given_acc=None, given_acc_center=None, duration=0.05)

    def test_eat_baseball(self):
        border = Border(0, 0, 100, 100)
        position = Vector2(10, 10)
        ball_id = uuid.uuid1()
        base_ball = BaseBall(ball_id, position, border=border, score=1)
        clone_ball = self.get_clone()
        clone_ball.eat(base_ball)

    def test_rigid_collision_self(self):
        clone_ball = self.get_clone()
        assert clone_ball.rigid_collision(clone_ball)

def test_init(self):
    clone_ball = self.get_clone()
    assert True

def test_eat_food(self):
    clone_ball = self.get_clone()
    food_ball = self.get_food()
    clone_score = clone_ball.score
    food_score = food_ball.score
    clone_ball.eat(food_ball, clone_num=1)
    logging.debug('clone_score={}, food_score={}, now_score={}, now_score={}'.format(clone_score, food_score, clone_ball.score, clone_ball.score))
    assert True

def test_eat_thorns(self):
    clone_ball = self.get_clone()
    thorns_ball = self.get_thorns()
    clone_score = clone_ball.score
    thorns_score = thorns_ball.score
    logging.debug('clone_ball={}'.format(clone_ball))
    logging.debug('===================== first eat =====================')
    rets = clone_ball.eat(thorns_ball, clone_num=1)
    logging.debug('[original] {} eat thorns_score={}'.format(clone_ball, thorns_score))
    for i, ret in enumerate(rets):
        logging.debug('[{}] {}'.format(i, ret))
    clone_num = 1 + len(rets)
    logging.debug('===================== second eat =====================')
    rets = clone_ball.eat(thorns_ball, clone_num=clone_num)
    logging.debug('[original] {} eat thorns_score={}'.format(clone_ball, thorns_score))
    for i, ret in enumerate(rets):
        logging.debug('[{}] {}'.format(i, ret))

def test_move(self):
    border = Border(0, 0, 1000, 1000)
    clone_ball = self.get_clone(score=16)
    direction = Vector2(1, 0) * 1000
    logging.debug('===================== before move =====================')
    logging.debug('position={}, vel={}, vel_max={}'.format(clone_ball.position, clone_ball.vel, clone_ball.vel_max))
    for i in range(10):
        clone_ball.move(given_acc=direction, given_acc_center=Vector2(0, 0), duration=0.05)
        logging.debug('===================== after move =====================')
        logging.debug('position={}, vel={}, vel_max={}'.format(clone_ball.position, clone_ball.vel, clone_ball.vel_max))
    for i in range(20):
        clone_ball.move(given_acc=None, given_acc_center=None, duration=0.05)
        logging.debug('===================== move after stop =====================')
        logging.debug('position={}, vel={}, vel_max={}'.format(clone_ball.position, clone_ball.vel, clone_ball.vel_max))
    clone_ball.split(1)
    for i in range(20):
        clone_ball.move(given_acc=None, given_acc_center=None, duration=0.05)
        logging.debug('===================== move after stop =====================')
        logging.debug('position={}, vel={}, vel_max={}'.format(clone_ball.position, clone_ball.vel, clone_ball.vel_max))

def test_eject(self):
    logging.debug('===================== test eject =====================')
    eject_score_min = CloneBall.default_config().eject_score_min
    clone_ball = self.get_clone(score=eject_score_min)
    rets = clone_ball.eject()
    logging.debug('clone_ball: {}, eject_score_min={}'.format(clone_ball, eject_score_min))
    if clone_ball.score < eject_score_min:
        assert rets
    else:
        logging.debug('spore_ball: {}'.format(rets))
    assert not clone_ball.eject()

def test_split(self):
    logging.debug('===================== test split =====================')
    split_score_min = CloneBall.default_config().split_score_min
    clone_ball = self.get_clone(score=split_score_min)
    logging.debug('clone_ball: {}, split_score_min={}'.format(clone_ball, split_score_min))
    rets = clone_ball.split(1)
    logging.debug('===================== after split =====================')
    logging.debug('[original] {}'.format(clone_ball))
    logging.debug('[new     ] {}'.format(rets))
    clone_ball = self.get_clone()
    assert not clone_ball.split(1)

def test_move_wo_stop_flag(self):
    clone_ball = self.get_clone()
    clone_ball.move(given_acc=None, given_acc_center=None, duration=0.05)
    clone_ball.move(given_acc=None, given_acc_center=Vector2(1, 0), duration=0.05)
    clone_ball.move(given_acc=None, given_acc_center=None, duration=0.05)

@pytest.mark.unittest
class TestPlayback:

    def test_none_pb(self):
        env = create_env('st_t2p2', dict(frame_limit=100, playback_settings=dict(playback_type='none')))
        obs = env.reset()
        bot_agents = []
        team_infos = env.get_team_infos()
        print(team_infos)
        for team_id, player_ids in team_infos:
            for player_id in player_ids:
                bot_agents.append(BotAgent(player_id, level=2))
        time_step_all = 0
        for i in range(100000):
            actions = {bot_agent.name: bot_agent.step(obs[1][bot_agent.name]) for bot_agent in bot_agents}
            t1 = time.time()
            obs, reward, done, info = env.step(actions=actions)
            t2 = time.time()
            time_step_all += t2 - t1
            logging.debug('{} {:.4f} envstep {:.3f} / {:.3f}, leaderboard={}'.format(i, obs[0]['last_frame_count'], t2 - t1, time_step_all / (i + 1), obs[0]['leaderboard']))
            if done:
                logging.debug('Game Over')
                break
        env.close()

    def test_video_pb(self):
        env = create_env('st_t2p2', dict(frame_limit=100, playback_settings=dict(playback_type='by_video', by_video=dict(save_video=True))))
        obs = env.reset()
        bot_agents = []
        team_infos = env.get_team_infos()
        print(team_infos)
        for team_id, player_ids in team_infos:
            for player_id in player_ids:
                bot_agents.append(BotAgent(player_id, level=2))
        time_step_all = 0
        for i in range(100000):
            actions = {bot_agent.name: bot_agent.step(obs[1][bot_agent.name]) for bot_agent in bot_agents}
            t1 = time.time()
            obs, reward, done, info = env.step(actions=actions)
            t2 = time.time()
            time_step_all += t2 - t1
            logging.debug('{} {:.4f} envstep {:.3f} / {:.3f}, leaderboard={}'.format(i, obs[0]['last_frame_count'], t2 - t1, time_step_all / (i + 1), obs[0]['leaderboard']))
            if done:
                logging.debug('Game Over')
                break
        env.close()
        assert os.path.isfile('test-all.mp4')
        os.remove('test-all.mp4')

    def test_frame_pb(self):
        env = create_env('st_t2p2', dict(frame_limit=100, playback_settings=dict(playback_type='by_frame', by_frame=dict(save_frame=True))))
        obs = env.reset()
        bot_agents = []
        team_infos = env.get_team_infos()
        print(team_infos)
        for team_id, player_ids in team_infos:
            for player_id in player_ids:
                bot_agents.append(BotAgent(player_id, level=2))
        time_step_all = 0
        for i in range(100000):
            actions = {bot_agent.name: bot_agent.step(obs[1][bot_agent.name]) for bot_agent in bot_agents}
            t1 = time.time()
            obs, reward, done, info = env.step(actions=actions)
            t2 = time.time()
            time_step_all += t2 - t1
            logging.debug('{} {:.4f} envstep {:.3f} / {:.3f}, leaderboard={}'.format(i, obs[0]['last_frame_count'], t2 - t1, time_step_all / (i + 1), obs[0]['leaderboard']))
            if done:
                logging.debug('Game Over')
                break
        env.close()
        assert os.path.isfile('test.pb')
        os.remove('test.pb')

def test_none_pb(self):
    env = create_env('st_t2p2', dict(frame_limit=100, playback_settings=dict(playback_type='none')))
    obs = env.reset()
    bot_agents = []
    team_infos = env.get_team_infos()
    print(team_infos)
    for team_id, player_ids in team_infos:
        for player_id in player_ids:
            bot_agents.append(BotAgent(player_id, level=2))
    time_step_all = 0
    for i in range(100000):
        actions = {bot_agent.name: bot_agent.step(obs[1][bot_agent.name]) for bot_agent in bot_agents}
        t1 = time.time()
        obs, reward, done, info = env.step(actions=actions)
        t2 = time.time()
        time_step_all += t2 - t1
        logging.debug('{} {:.4f} envstep {:.3f} / {:.3f}, leaderboard={}'.format(i, obs[0]['last_frame_count'], t2 - t1, time_step_all / (i + 1), obs[0]['leaderboard']))
        if done:
            logging.debug('Game Over')
            break
    env.close()

def test_video_pb(self):
    env = create_env('st_t2p2', dict(frame_limit=100, playback_settings=dict(playback_type='by_video', by_video=dict(save_video=True))))
    obs = env.reset()
    bot_agents = []
    team_infos = env.get_team_infos()
    print(team_infos)
    for team_id, player_ids in team_infos:
        for player_id in player_ids:
            bot_agents.append(BotAgent(player_id, level=2))
    time_step_all = 0
    for i in range(100000):
        actions = {bot_agent.name: bot_agent.step(obs[1][bot_agent.name]) for bot_agent in bot_agents}
        t1 = time.time()
        obs, reward, done, info = env.step(actions=actions)
        t2 = time.time()
        time_step_all += t2 - t1
        logging.debug('{} {:.4f} envstep {:.3f} / {:.3f}, leaderboard={}'.format(i, obs[0]['last_frame_count'], t2 - t1, time_step_all / (i + 1), obs[0]['leaderboard']))
        if done:
            logging.debug('Game Over')
            break
    env.close()
    assert os.path.isfile('test-all.mp4')
    os.remove('test-all.mp4')

def test_frame_pb(self):
    env = create_env('st_t2p2', dict(frame_limit=100, playback_settings=dict(playback_type='by_frame', by_frame=dict(save_frame=True))))
    obs = env.reset()
    bot_agents = []
    team_infos = env.get_team_infos()
    print(team_infos)
    for team_id, player_ids in team_infos:
        for player_id in player_ids:
            bot_agents.append(BotAgent(player_id, level=2))
    time_step_all = 0
    for i in range(100000):
        actions = {bot_agent.name: bot_agent.step(obs[1][bot_agent.name]) for bot_agent in bot_agents}
        t1 = time.time()
        obs, reward, done, info = env.step(actions=actions)
        t2 = time.time()
        time_step_all += t2 - t1
        logging.debug('{} {:.4f} envstep {:.3f} / {:.3f}, leaderboard={}'.format(i, obs[0]['last_frame_count'], t2 - t1, time_step_all / (i + 1), obs[0]['leaderboard']))
        if done:
            logging.debug('Game Over')
            break
    env.close()
    assert os.path.isfile('test.pb')
    os.remove('test.pb')

def play_farm_single(step):
    cfg['player_num_per_team'] = 1
    cfg['team_num'] = 1
    cfg['frame_limit'] = step
    env = GoBiggerEnv(cfg)
    obs = env.reset()
    done = False
    render = RealtimeRender(map_width=64, map_height=64)
    fps_real = 0
    t1 = time.time()
    clock = pygame.time.Clock()
    fps_set = env.server.fps
    my_player_id = 0
    bot_agents = []
    for player in env.server.player_manager.get_players():
        if player.player_id != my_player_id:
            bot_agents.append(BotAgent(player.player_id))
    for i in range(100000):
        actions = None
        x1, y1 = (None, None)
        action_type = 0
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                action_type = -1
                action_type = -1
                if event.key == pygame.K_UP:
                    x1, y1 = (0, -1)
                if event.key == pygame.K_DOWN:
                    x1, y1 = (0, 1)
                if event.key == pygame.K_LEFT:
                    x1, y1 = (-1, 0)
                if event.key == pygame.K_RIGHT:
                    x1, y1 = (1, 0)
                if event.key == pygame.K_1:
                    action_type = 0
                if event.key == pygame.K_2:
                    action_type = 1
                if event.key == pygame.K_3:
                    action_type = 2
        actions = {my_player_id: [x1, y1, action_type]}
        actions.update({agent.name: agent.step(obs[1][agent.name]) for agent in bot_agents})
        if not done:
            obs, reward, done, info = env.step(actions=actions)
            print(obs[0]['leaderboard'])
            render.fill(food_balls=env.server.food_manager.get_balls(), thorns_balls=env.server.thorns_manager.get_balls(), spore_balls=env.server.spore_manager.get_balls(), players=env.server.player_manager.get_players(), player_num_per_team=env.server.player_num_per_team, fps=fps_real, leaderboard=obs[0]['leaderboard'])
            render.show()
            if i % fps_set == 0:
                t2 = time.time()
                fps_real = fps_set / (t2 - t1)
                t1 = time.time()
        else:
            logging.debug('Game Over')
            break
        clock.tick(fps_set)
    render.close()

def play_vsbot_single(step):
    cfg['player_num_per_team'] = 1
    cfg['frame_limit'] = step
    env = GoBiggerEnv(cfg)
    obs = env.reset()
    done = False
    render = RealtimeRender(map_width=64, map_height=64)
    fps_real = 0
    t1 = time.time()
    clock = pygame.time.Clock()
    fps_set = env.server.fps
    my_player_id = 0
    bot_agents = []
    for player in env.server.player_manager.get_players():
        if player.player_id != my_player_id:
            bot_agents.append(BotAgent(player.player_id))
    for i in range(100000):
        actions = None
        x1, y1 = (None, None)
        action_type = 0
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                action_type = -1
                action_type = -1
                if event.key == pygame.K_UP:
                    x1, y1 = (0, -1)
                if event.key == pygame.K_DOWN:
                    x1, y1 = (0, 1)
                if event.key == pygame.K_LEFT:
                    x1, y1 = (-1, 0)
                if event.key == pygame.K_RIGHT:
                    x1, y1 = (1, 0)
                if event.key == pygame.K_1:
                    action_type = 0
                if event.key == pygame.K_2:
                    action_type = 1
                if event.key == pygame.K_3:
                    action_type = 2
        actions = {my_player_id: [x1, y1, action_type]}
        actions.update({agent.name: agent.step(obs[1][agent.name]) for agent in bot_agents})
        if not done:
            obs, reward, done, info = env.step(actions=actions)
            print(obs[0]['leaderboard'])
            render.fill(food_balls=env.server.food_manager.get_balls(), thorns_balls=env.server.thorns_manager.get_balls(), spore_balls=env.server.spore_manager.get_balls(), players=env.server.player_manager.get_players(), player_num_per_team=env.server.player_num_per_team, fps=fps_real, leaderboard=obs[0]['leaderboard'])
            render.show()
            if i % fps_set == 0:
                t2 = time.time()
                fps_real = fps_set / (t2 - t1)
                t1 = time.time()
        else:
            logging.debug('Game Over')
            break
        clock.tick(fps_set)
    render.close()

def play_farm_team(step):
    cfg['player_num_per_team'] = 2
    cfg['team_num'] = 1
    cfg['frame_limit'] = step
    env = GoBiggerEnv(cfg)
    obs = env.reset()
    done = False
    render = RealtimeRender(map_width=64, map_height=64)
    fps_real = 0
    t1 = time.time()
    clock = pygame.time.Clock()
    fps_set = env.server.fps
    for i in range(100000):
        action_type1 = None
        action_type2 = None
        x1, y1, x2, y2 = (None, None, None, None)
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                action_type1 = -1
                action_type2 = -1
                if event.key == pygame.K_UP:
                    x1, y1 = (0, -1)
                if event.key == pygame.K_DOWN:
                    x1, y1 = (0, 1)
                if event.key == pygame.K_LEFT:
                    x1, y1 = (-1, 0)
                if event.key == pygame.K_RIGHT:
                    x1, y1 = (1, 0)
                if event.key == pygame.K_1:
                    action_type1 = 0
                if event.key == pygame.K_2:
                    action_type1 = 1
                if event.key == pygame.K_3:
                    action_type1 = 2
                if event.key == pygame.K_w:
                    x2, y2 = (0, -1)
                if event.key == pygame.K_s:
                    x2, y2 = (0, 1)
                if event.key == pygame.K_a:
                    x2, y2 = (-1, 0)
                if event.key == pygame.K_d:
                    x2, y2 = (1, 0)
                if event.key == pygame.K_j:
                    action_type2 = 0
                if event.key == pygame.K_k:
                    action_type2 = 1
                if event.key == pygame.K_l:
                    action_type2 = 2
        actions = {0: [x1, y1, action_type1], 1: [x2, y2, action_type2]}
        if not done:
            obs, reward, done, info = env.step(actions=actions)
            print(obs[0]['leaderboard'])
            render.fill(food_balls=env.server.food_manager.get_balls(), thorns_balls=env.server.thorns_manager.get_balls(), spore_balls=env.server.spore_manager.get_balls(), players=env.server.player_manager.get_players(), player_num_per_team=env.server.player_num_per_team, fps=fps_real, leaderboard=obs[0]['leaderboard'])
            render.show()
            if i % fps_set == 0:
                t2 = time.time()
                fps_real = fps_set / (t2 - t1)
                t1 = time.time()
        else:
            logging.debug('Game Over')
            break
        clock.tick(fps_set)
    render.close()

def play_vsbot_team(step):
    cfg['frame_limit'] = step
    env = GoBiggerEnv(cfg)
    obs = env.reset()
    done = False
    render = RealtimeRender(map_width=64, map_height=64)
    fps_real = 0
    t1 = time.time()
    clock = pygame.time.Clock()
    fps_set = env.server.fps
    bot_agents = []
    for player in env.server.player_manager.get_players():
        if player.player_id != 0 and player.player_id != 1:
            bot_agents.append(BotAgent(player.player_id))
    for i in range(100000):
        action_type1 = None
        action_type2 = None
        x1, y1, x2, y2 = (None, None, None, None)
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                action_type1 = -1
                action_type2 = -1
                if event.key == pygame.K_UP:
                    x1, y1 = (0, -1)
                if event.key == pygame.K_DOWN:
                    x1, y1 = (0, 1)
                if event.key == pygame.K_LEFT:
                    x1, y1 = (-1, 0)
                if event.key == pygame.K_RIGHT:
                    x1, y1 = (1, 0)
                if event.key == pygame.K_1:
                    action_type1 = 0
                if event.key == pygame.K_2:
                    action_type1 = 1
                if event.key == pygame.K_3:
                    action_type1 = 2
                if event.key == pygame.K_w:
                    x2, y2 = (0, -1)
                if event.key == pygame.K_s:
                    x2, y2 = (0, 1)
                if event.key == pygame.K_a:
                    x2, y2 = (-1, 0)
                if event.key == pygame.K_d:
                    x2, y2 = (1, 0)
                if event.key == pygame.K_j:
                    action_type2 = 0
                if event.key == pygame.K_k:
                    action_type2 = 1
                if event.key == pygame.K_l:
                    action_type2 = 2
        actions = {0: [x1, y1, action_type1], 1: [x2, y2, action_type2]}
        actions.update({agent.name: agent.step(obs[1][agent.name]) for agent in bot_agents})
        if not done:
            obs, reward, done, info = env.step(actions=actions)
            print(obs[0]['leaderboard'])
            render.fill(food_balls=env.server.food_manager.get_balls(), thorns_balls=env.server.thorns_manager.get_balls(), spore_balls=env.server.spore_manager.get_balls(), players=env.server.player_manager.get_players(), player_num_per_team=env.server.player_num_per_team, fps=fps_real, leaderboard=obs[0]['leaderboard'])
            render.show()
            if i % fps_set == 0:
                t2 = time.time()
                fps_real = fps_set / (t2 - t1)
                t1 = time.time()
        else:
            logging.debug('Game Over')
            break
        clock.tick(fps_set)
    render.close()

def play_vsai_single(step):
    cfg['frame_limit'] = step
    cfg['player_num_per_team'] = 1
    env = GoBiggerEnv(cfg)
    obs = env.reset()
    done = False
    render = RealtimeRender(map_width=64, map_height=64)
    fps_real = 0
    t1 = time.time()
    clock = pygame.time.Clock()
    fps_set = env.server.fps
    my_player_id = 0
    ai_player_id = 1
    from solo_agent.agent import AIAgent as AI
    ai = AI(team_name=1, player_names=[1])
    for i in range(100000):
        actions = None
        x1, y1 = (None, None)
        action_type = 0
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                action_type = -1
                action_type = -1
                if event.key == pygame.K_UP:
                    x1, y1 = (0, -1)
                if event.key == pygame.K_DOWN:
                    x1, y1 = (0, 1)
                if event.key == pygame.K_LEFT:
                    x1, y1 = (-1, 0)
                if event.key == pygame.K_RIGHT:
                    x1, y1 = (1, 0)
                if event.key == pygame.K_1:
                    action_type = 0
                if event.key == pygame.K_2:
                    action_type = 1
                if event.key == pygame.K_3:
                    action_type = 2
        ai_action = ai.get_actions(obs)
        actions = {my_player_id: [x1, y1, action_type]}
        actions.update(ai_action)
        if not done:
            obs, reward, done, info = env.step(actions=actions)
            print(obs[0]['leaderboard'])
            render.fill(food_balls=env.server.food_manager.get_balls(), thorns_balls=env.server.thorns_manager.get_balls(), spore_balls=env.server.spore_manager.get_balls(), players=env.server.player_manager.get_players(), player_num_per_team=env.server.player_num_per_team, fps=fps_real, leaderboard=obs[0]['leaderboard'])
            render.show()
            if i % fps_set == 0:
                t2 = time.time()
                fps_real = fps_set / (t2 - t1)
                t1 = time.time()
        else:
            logging.debug('Game Over')
            break
        clock.tick(fps_set)
    render.close()

def play_vsai_team(step):
    cfg['frame_limit'] = step
    env = GoBiggerEnv(cfg)
    obs = env.reset()
    done = False
    render = RealtimeRender(map_width=64, map_height=64)
    fps_real = 0
    t1 = time.time()
    clock = pygame.time.Clock()
    fps_set = env.server.fps
    from cooperative_agent.agent import AIAgent as AI
    ai = AI(team_name=1, player_names=[2, 3])
    for i in range(100000):
        action_type1 = None
        action_type2 = None
        x1, y1, x2, y2 = (None, None, None, None)
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                action_type1 = -1
                action_type2 = -1
                if event.key == pygame.K_UP:
                    x1, y1 = (0, -1)
                if event.key == pygame.K_DOWN:
                    x1, y1 = (0, 1)
                if event.key == pygame.K_LEFT:
                    x1, y1 = (-1, 0)
                if event.key == pygame.K_RIGHT:
                    x1, y1 = (1, 0)
                if event.key == pygame.K_1:
                    action_type1 = 0
                if event.key == pygame.K_2:
                    action_type1 = 1
                if event.key == pygame.K_3:
                    action_type1 = 2
                if event.key == pygame.K_w:
                    x2, y2 = (0, -1)
                if event.key == pygame.K_s:
                    x2, y2 = (0, 1)
                if event.key == pygame.K_a:
                    x2, y2 = (-1, 0)
                if event.key == pygame.K_d:
                    x2, y2 = (1, 0)
                if event.key == pygame.K_j:
                    action_type2 = 0
                if event.key == pygame.K_k:
                    action_type2 = 1
                if event.key == pygame.K_l:
                    action_type2 = 2
        actions = {0: [x1, y1, action_type1], 1: [x2, y2, action_type2]}
        ai_action = ai.get_actions(obs)
        actions.update(ai_action)
        if not done:
            obs, reward, done, info = env.step(actions=actions)
            print(obs[0]['leaderboard'])
            render.fill(food_balls=env.server.food_manager.get_balls(), thorns_balls=env.server.thorns_manager.get_balls(), spore_balls=env.server.spore_manager.get_balls(), players=env.server.player_manager.get_players(), player_num_per_team=env.server.player_num_per_team, fps=fps_real, leaderboard=obs[0]['leaderboard'])
            render.show()
            if i % fps_set == 0:
                t2 = time.time()
                fps_real = fps_set / (t2 - t1)
                t1 = time.time()
        else:
            logging.debug('Game Over')
            break
        clock.tick(fps_set)
    render.close()

def watch_vsai_only(step):
    cfg['frame_limit'] = step
    env = GoBiggerEnv(cfg)
    obs = env.reset()
    done = False
    render = RealtimeRender(map_width=64, map_height=64)
    fps_real = 0
    t1 = time.time()
    clock = pygame.time.Clock()
    fps_set = env.server.fps
    from cooperative_agent.agent import AIAgent as AI
    ai_0 = AI(team_name=0, player_names=[0, 1])
    ai_1 = AI(team_name=1, player_names=[2, 3])
    for i in range(100000):
        action_type1 = None
        action_type2 = None
        x1, y1, x2, y2 = (None, None, None, None)
        actions = {0: [x1, y1, action_type1], 1: [x2, y2, action_type2]}
        ai_action = ai_0.get_actions(obs)
        actions.update(ai_action)
        ai_action = ai_1.get_actions(obs)
        actions.update(ai_action)
        if not done:
            obs, reward, done, info = env.step(actions=actions)
            print(obs[0]['leaderboard'])
            render.fill(food_balls=env.server.food_manager.get_balls(), thorns_balls=env.server.thorns_manager.get_balls(), spore_balls=env.server.spore_manager.get_balls(), players=env.server.player_manager.get_players(), player_num_per_team=env.server.player_num_per_team, fps=fps_real, leaderboard=obs[0]['leaderboard'])
            render.show()
            if i % fps_set == 0:
                t2 = time.time()
                fps_real = fps_set / (t2 - t1)
                t1 = time.time()
        else:
            logging.debug('Game Over')
            break
        clock.tick(fps_set)
    render.close()

class AIAgent:

    def __init__(self, team_name, player_names):
        cfg = EasyDict({'team_name': team_name, 'player_names': player_names, 'env': {'name': 'gobigger', 'player_num_per_team': 2, 'team_num': 2, 'step_mul': 8}, 'agent': {'player_id': None, 'game_player_id': None, 'features': {}}, 'checkpoint_path': 'PATH/MODEL_NAME.pth.tar'})
        self.agents = {}
        for player_name in player_names:
            cfg_cp = deepcopy(cfg)
            cfg_cp.agent.player_id = player_name
            cfg_cp.agent.game_player_id = player_name
            agent = Agent(cfg_cp)
            agent.reset()
            agent.model.load_state_dict(torch.load(cfg.checkpoint_path, map_location='cpu')['model'], strict=False)
            self.agents[player_name] = agent

    def get_actions(self, obs):
        global_state, player_states = obs
        actions = {}
        for player_name, agent in self.agents.items():
            action = agent.step([global_state, {player_name: player_states[player_name]}])
            actions.update(action)
        return actions

def get_actions(self, obs):
    global_state, player_states = obs
    actions = {}
    for player_name, agent in self.agents.items():
        action = agent.step([global_state, {player_name: player_states[player_name]}])
        actions.update(action)
    return actions

class Features:

    def __init__(self, cfg):
        self.cfg = cfg
        self.player_num_per_team = self.cfg.env.player_num_per_team
        self.team_num = self.cfg.env.team_num
        self.max_player_num = self.player_num_per_team
        self.max_team_num = self.team_num
        self.max_ball_num = self.cfg.agent.features.get('max_ball_num', 80)
        self.max_food_num = self.cfg.agent.features.get('max_food_num', 256)
        self.max_spore_num = self.cfg.agent.features.get('max_spore_num', 64)
        self.direction_num = self.cfg.agent.features.get('direction_num', 12)
        self.spatial_x = 64
        self.spatial_y = 64
        self.step_mul = self.cfg.env.get('step_mul', 5)
        self.second_per_frame = self.cfg.agent.features.get('second_per_frame', 0.05)
        self.action_num = self.direction_num * 2 + 3
        self.setup_action()
        self._init_fake_data()

    def get_augmentation_map(self):
        augmentation_mapping = {}
        for aug_type in ['ud', 'lr', 'lrud']:
            augmentation_mapping[aug_type] = {action: self.augmentation_action(action, aug_type=aug_type) for action in range(self.action_num)}
        return augmentation_mapping

    def setup_action(self):
        theta = math.pi * 2 / self.direction_num
        self.x_y_action_List = [[0.3 * math.cos(theta * i), 0.3 * math.sin(theta * i), 0] for i in range(self.direction_num)] + [[math.cos(theta * i), math.sin(theta * i), 0] for i in range(self.direction_num)] + [[0, 0, 0], [0, 0, 1], [0, 0, 2]]

    def _init_fake_data(self):
        self.SCALAR_INFO = {'view_x': (torch.long, ()), 'view_y': (torch.long, ()), 'view_width': (torch.long, ()), 'score': (torch.long, ()), 'team_score': (torch.long, ()), 'rank': (torch.long, ()), 'time': (torch.long, ()), 'last_action_type': (torch.long, ())}
        self.TEAM_INFO = {'alliance': (torch.long, (self.max_player_num,)), 'view_x': (torch.long, (self.max_player_num,)), 'view_y': (torch.long, (self.max_player_num,)), 'player_num': (torch.long, ())}
        self.BALL_INFO = {'alliance': (torch.long, (self.max_ball_num,)), 'score': (torch.long, (self.max_ball_num,)), 'radius': (torch.float, (self.max_ball_num,)), 'rank': (torch.long, (self.max_ball_num,)), 'x': (torch.long, (self.max_ball_num,)), 'y': (torch.long, (self.max_ball_num,)), 'next_x': (torch.long, (self.max_ball_num,)), 'next_y': (torch.long, (self.max_ball_num,)), 'ball_num': (torch.long, ())}
        self.SPATIAL_INFO = {'food_x': (torch.long, (self.max_food_num,)), 'food_y': (torch.long, (self.max_food_num,)), 'spore_x': (torch.long, (self.max_spore_num,)), 'spore_y': (torch.long, (self.max_spore_num,)), 'ball_x': (torch.long, (self.max_ball_num,)), 'ball_y': (torch.long, (self.max_ball_num,)), 'food_num': (torch.long, ()), 'spore_num': (torch.long, ())}
        self.REWARD_INFO = {'score': (torch.float, ()), 'spore': (torch.float, ()), 'mate_spore': (torch.float, ()), 'team_spore': (torch.float, ()), 'clone': (torch.float, ()), 'team_clone': (torch.float, ()), 'opponent': (torch.float, ()), 'team_opponent': (torch.float, ()), 'max_dist': (torch.float, ()), 'min_dist': (torch.float, ())}
        self.ACTION_INFO = {'action': (torch.long, ()), 'logit': (torch.float, (self.action_num,)), 'action_logp': (torch.long, ())}

    def get_rl_step_data(self, last=False):
        data = {}
        scalar_info = {k: torch.ones(size=v[1], dtype=v[0]) for k, v in self.SCALAR_INFO.items()}
        team_info = {k: torch.ones(size=v[1], dtype=v[0]) for k, v in self.TEAM_INFO.items()}
        ball_info = {k: torch.ones(size=v[1], dtype=v[0]) for k, v in self.BALL_INFO.items()}
        spatial_info = {k: torch.ones(size=v[1], dtype=v[0]) for k, v in self.SPATIAL_INFO.items()}
        action_mask = torch.zeros(size=(self.action_num,), dtype=torch.bool)
        data['obs'] = {'scalar_info': scalar_info, 'team_info': team_info, 'ball_info': ball_info, 'spatial_info': spatial_info, 'action_mask': action_mask}
        if not last:
            data['action'] = torch.zeros(size=(), dtype=torch.long)
            data['action_logp'] = torch.zeros(size=(), dtype=torch.float)
            data['reward'] = {k: torch.zeros(size=v[1], dtype=v[0]) for k, v in self.REWARD_INFO.items()}
            data['done'] = torch.zeros(size=(), dtype=torch.bool)
            data['model_last_iter'] = torch.zeros(size=(), dtype=torch.float)
        return data

    def get_player2team(self):
        player2team = {}
        for player_id in range(self.player_num_per_team * self.team_num):
            player2team[player_id] = player_id // self.player_num_per_team
        return player2team

    def transform_obs(self, obs, game_player_id=1, padding=True, last_action_type=None):
        global_state, player_observations = obs
        player2team = self.get_player2team()
        own_player_id = game_player_id
        leaderboard = global_state['leaderboard']
        team2rank = {key: rank for rank, key in enumerate(sorted(leaderboard, key=leaderboard.get, reverse=True))}
        own_player_obs = player_observations[own_player_id]
        own_team_id = player2team[own_player_id]
        scene_size = global_state['border'][0]
        own_left_top_x, own_left_top_y, own_right_bottom_x, own_right_bottom_y = own_player_obs['rectangle']
        own_view_center = [(own_left_top_x + own_right_bottom_x - scene_size) / 2, (own_left_top_y + own_right_bottom_y - scene_size) / 2]
        own_view_width = float(own_right_bottom_x - own_left_top_x)
        own_score = own_player_obs['score'] / 100
        own_team_score = global_state['leaderboard'][own_team_id] / 100
        own_rank = team2rank[own_team_id]
        scalar_info = {'view_x': torch.tensor(own_view_center[0]).round().long(), 'view_y': torch.tensor(own_view_center[1]).round().long(), 'view_width': torch.tensor(own_view_width).round().long(), 'score': torch.log(torch.tensor(own_score) / 10).round().long().clamp_(max=9), 'team_score': torch.log(torch.tensor(own_team_score / 10)).round().long().clamp_(max=9), 'time': torch.tensor(global_state['last_time'] // 20, dtype=torch.long), 'rank': torch.tensor(own_rank, dtype=torch.long), 'last_action_type': torch.tensor(last_action_type, dtype=torch.long)}
        all_players = []
        scene_size = global_state['border'][0]
        for game_player_id in player_observations.keys():
            game_team_id = player2team[game_player_id]
            game_player_left_top_x, game_player_left_top_y, game_player_right_bottom_x, game_player_right_bottom_y = player_observations[game_player_id]['rectangle']
            if game_player_id == own_player_id:
                alliance = 0
            elif game_team_id == own_team_id:
                alliance = 1
            else:
                alliance = 2
            if alliance != 2:
                game_player_view_x = (game_player_right_bottom_x + game_player_left_top_x - scene_size) / 2
                game_player_view_y = (game_player_right_bottom_y + game_player_left_top_y - scene_size) / 2
                all_players.append([alliance, game_player_view_x, game_player_view_y])
        all_players = torch.as_tensor(all_players)
        player_padding_num = self.max_player_num - len(all_players)
        player_num = len(all_players)
        all_players = torch.nn.functional.pad(all_players, (0, 0, 0, player_padding_num), 'constant', 0)
        team_info = {'alliance': all_players[:, 0].long(), 'view_x': all_players[:, 1].round().long(), 'view_y': all_players[:, 2].round().long(), 'player_num': torch.tensor(player_num, dtype=torch.long)}
        ball_type_map = {'clone': 1, 'food': 2, 'thorns': 3, 'spore': 4}
        clone = own_player_obs['overlap']['clone']
        thorns = own_player_obs['overlap']['thorns']
        food = own_player_obs['overlap']['food']
        spore = own_player_obs['overlap']['spore']
        neutral_team_id = self.team_num
        neutral_player_id = self.team_num * self.player_num_per_team
        neutral_team_rank = self.team_num
        clone = [[ball_type_map['clone'], bl[3], bl[-2], bl[-1], team2rank[bl[-1]], bl[0], bl[1], *self.next_position(bl[0], bl[1], bl[4], bl[5])] for bl in clone]
        thorns = [[ball_type_map['thorns'], bl[3], neutral_player_id, neutral_team_id, neutral_team_rank, bl[0], bl[1], *self.next_position(bl[0], bl[1], bl[4], bl[5])] for bl in thorns]
        food = [[ball_type_map['food'], bl[3], neutral_player_id, neutral_team_id, neutral_team_rank, bl[0], bl[1], bl[0], bl[1]] for bl in food]
        spore = [[ball_type_map['spore'], bl[3], bl[-1], player2team[bl[-1]], team2rank[player2team[bl[-1]]], bl[0], bl[1], *self.next_position(bl[0], bl[1], bl[4], bl[5])] for bl in spore]
        all_balls = clone + thorns + food + spore
        for b in all_balls:
            if b[2] == own_player_id and b[0] == 1:
                if b[5] < own_left_top_x or b[5] > own_right_bottom_x or b[6] < own_left_top_y or (b[6] > own_right_bottom_y):
                    b[5] = int((own_left_top_x + own_right_bottom_x) / 2)
                    b[6] = int((own_left_top_y + own_right_bottom_y) / 2)
                    b[7], b[8] = (b[5], b[6])
        all_balls = torch.as_tensor(all_balls, dtype=torch.float)
        origin_x = own_left_top_x
        origin_y = own_left_top_y
        all_balls[:, -4] = (all_balls[:, -4] - origin_x) / own_view_width * self.spatial_x
        all_balls[:, -3] = (all_balls[:, -3] - origin_y) / own_view_width * self.spatial_y
        all_balls[:, -2] = (all_balls[:, -2] - origin_x) / own_view_width * self.spatial_x
        all_balls[:, -1] = (all_balls[:, -1] - origin_y) / own_view_width * self.spatial_y
        ball_indices = torch.logical_and(all_balls[:, 0] != 2, all_balls[:, 0] != 4)
        balls = all_balls[ball_indices]
        balls_num = len(balls)
        if balls_num > self.max_ball_num:
            own_indices = balls[:, 3] == own_player_id
            teammate_indices = (balls[:, 4] == own_team_id) & ~own_indices
            enemy_indices = balls[:, 4] != own_team_id
            own_balls = balls[own_indices]
            teammate_balls = balls[teammate_indices]
            enemy_balls = balls[enemy_indices]
            if own_balls.shape[0] + teammate_balls.shape[0] >= self.max_ball_num:
                remain_ball_num = self.max_ball_num - own_balls.shape[0]
                teammate_ball_score = teammate_balls[:, 1]
                teammate_high_score_indices = teammate_ball_score.sort(descending=True)[1][:remain_ball_num]
                teammate_remain_balls = teammate_balls[teammate_high_score_indices]
                balls = torch.cat([own_balls, teammate_remain_balls])
            else:
                remain_ball_num = self.max_ball_num - own_balls.shape[0] - teammate_balls.shape[0]
                enemy_ball_score = enemy_balls[:, 1]
                enemy_high_score_ball_indices = enemy_ball_score.sort(descending=True)[1][:remain_ball_num]
                remain_enemy_balls = enemy_balls[enemy_high_score_ball_indices]
                balls = torch.cat([own_balls, teammate_balls, remain_enemy_balls])
        balls_num = len(balls)
        ball_padding_num = self.max_ball_num - len(balls)
        if padding or ball_padding_num < 0:
            balls = torch.nn.functional.pad(balls, (0, 0, 0, ball_padding_num), 'constant', 0)
            alliance = torch.zeros(self.max_ball_num)
            balls_num = min(self.max_ball_num, balls_num)
        else:
            alliance = torch.zeros(balls_num)
        alliance[balls[:, 3] == own_team_id] = 2
        alliance[balls[:, 2] == own_player_id] = 1
        alliance[balls[:, 3] != own_team_id] = 3
        alliance[balls[:, 0] == 3] = 0
        scale_score = balls[:, 1] / 100
        radius = (torch.sqrt(scale_score * 0.042 + 0.15) / own_view_width).clamp_(max=1)
        score = ((torch.sqrt(scale_score * 0.042 + 0.15) / own_view_width).clamp_(max=1) * 50).round().long().clamp_(max=49)
        ball_rank = balls[:, 4]
        x = balls[:, -4] - self.spatial_x // 2
        y = balls[:, -3] - self.spatial_y // 2
        next_x = balls[:, -2] - self.spatial_x // 2
        next_y = balls[:, -1] - self.spatial_y // 2
        ball_info = {'alliance': alliance.long(), 'score': score.long(), 'radius': radius, 'rank': ball_rank.long(), 'x': x.round().long(), 'y': y.round().long(), 'next_x': next_x.round().long(), 'next_y': next_y.round().long(), 'ball_num': torch.tensor(balls_num, dtype=torch.long)}
        ball_x = balls[:, -4]
        ball_y = balls[:, -3]
        food_indices = all_balls[:, 0] == 2
        food_x = all_balls[food_indices, -4]
        food_y = all_balls[food_indices, -3]
        food_num = len(food_x)
        food_padding_num = self.max_food_num - len(food_x)
        if padding or food_padding_num < 0:
            food_x = torch.nn.functional.pad(food_x, (0, food_padding_num), 'constant', 0)
            food_y = torch.nn.functional.pad(food_y, (0, food_padding_num), 'constant', 0)
        food_num = min(food_num, self.max_food_num)
        spore_indices = all_balls[:, 0] == 4
        spore_x = all_balls[spore_indices, -4]
        spore_y = all_balls[spore_indices, -3]
        spore_num = len(spore_x)
        spore_padding_num = self.max_spore_num - len(spore_x)
        if padding or spore_padding_num < 0:
            spore_x = torch.nn.functional.pad(spore_x, (0, spore_padding_num), 'constant', 0)
            spore_y = torch.nn.functional.pad(spore_y, (0, spore_padding_num), 'constant', 0)
        spore_num = min(spore_num, self.max_spore_num)
        spatial_info = {'food_x': food_x.round().clamp_(min=0, max=self.spatial_x - 1).long(), 'food_y': food_y.round().clamp_(min=0, max=self.spatial_y - 1).long(), 'spore_x': spore_x.round().clamp_(min=0, max=self.spatial_x - 1).long(), 'spore_y': spore_y.round().clamp_(min=0, max=self.spatial_y - 1).long(), 'ball_x': ball_x.round().clamp_(min=0, max=self.spatial_x - 1).long(), 'ball_y': ball_y.round().clamp_(min=0, max=self.spatial_y - 1).long(), 'food_num': torch.tensor(food_num, dtype=torch.long), 'spore_num': torch.tensor(spore_num, dtype=torch.long)}
        output_obs = {'scalar_info': scalar_info, 'team_info': team_info, 'ball_info': ball_info, 'spatial_info': spatial_info}
        return output_obs

    def generate_action_mask(self, can_eject, can_split):
        action_mask = torch.zeros(size=(self.action_num,), dtype=torch.bool)
        if not can_eject:
            action_mask[self.direction_num * 2 + 1] = True
        if not can_split:
            action_mask[self.direction_num * 2 + 2] = True
        return action_mask

    def transform_action(self, action_idx):
        return self.x_y_action_List[int(action_idx)]

    def next_position(self, x, y, vel_x, vel_y):
        next_x = x + self.second_per_frame * vel_x * self.step_mul
        next_y = y + self.second_per_frame * vel_y * self.step_mul
        return (next_x, next_y)

def get_augmentation_map(self):
    augmentation_mapping = {}
    for aug_type in ['ud', 'lr', 'lrud']:
        augmentation_mapping[aug_type] = {action: self.augmentation_action(action, aug_type=aug_type) for action in range(self.action_num)}
    return augmentation_mapping

def get_player2team(self):
    player2team = {}
    for player_id in range(self.player_num_per_team * self.team_num):
        player2team[player_id] = player_id // self.player_num_per_team
    return player2team

class AIAgent:

    def __init__(self, team_name, player_names):
        cfg = EasyDict({'env': {'name': 'gobigger', 'player_num_per_team': 1, 'team_num': 2}, 'agent': {'player_id': None, 'game_player_id': None, 'features': {}}, 'checkpoint_path': 'PATH/MODEL_NAME.pth.tar'})
        self.agents = {}
        for player_name in player_names:
            cfg_cp = deepcopy(cfg)
            cfg_cp.agent.player_id = player_name
            cfg_cp.agent.game_player_id = player_name
            agent = Agent(cfg_cp)
            agent.reset()
            agent.model.load_state_dict(torch.load(cfg.checkpoint_path, map_location='cpu')['model'], strict=False)
            self.agents[player_name] = agent

    def get_actions(self, obs):
        global_state, player_states = obs
        actions = {}
        for player_name, agent in self.agents.items():
            action = agent.step([global_state, {player_name: player_states[player_name]}])
            actions.update(action)
        return actions

def get_actions(self, obs):
    global_state, player_states = obs
    actions = {}
    for player_name, agent in self.agents.items():
        action = agent.step([global_state, {player_name: player_states[player_name]}])
        actions.update(action)
    return actions

class Agent:

    def __init__(self, cfg=None):
        self.whole_cfg = cfg
        self.cfg = self.whole_cfg.agent
        self.use_action_mask = self.whole_cfg.agent.get('use_action_mask', False)
        self.player_num = self.whole_cfg.env.player_num_per_team
        self.team_num = self.whole_cfg.env.team_num
        self.game_player_id = self.whole_cfg.agent.game_player_id
        self.game_team_id = self.game_player_id // self.player_num
        self.features = Features(self.whole_cfg)
        self.device = 'cpu'
        self.model = Model(self.whole_cfg)

    def transform_action(self, agent_outputs, env_status, eval_vsbot=False):
        env_num = len(env_status)
        actions_list = agent_outputs['action'].cpu().numpy().tolist()
        actions = {}
        for env_id in range(env_num):
            actions[env_id] = {}
            game_player_num = self.player_num if eval_vsbot else self.player_num * self.team_num
            for game_player_id in range(game_player_num):
                action_idx = actions_list[env_id * game_player_num + game_player_id]
                env_status[env_id].last_action_types[game_player_id] = action_idx
                actions[env_id][game_player_id] = self.features.transform_action(action_idx)
        return actions

    def reset(self):
        self.last_action_type = {}
        for player_id in range(self.player_num * self.game_team_id, self.player_num * (self.game_team_id + 1)):
            self.last_action_type[player_id] = self.features.direction_num * 2

    def step(self, obs):
        """
        Overview:
            Agent.step() in submission
        Arguments:
            - obs
        Returns:
            - action
        """
        env_team_obs = []
        for player_id in range(self.player_num * self.game_team_id, self.player_num * (self.game_team_id + 1)):
            game_player_obs = self.features.transform_obs(obs, game_player_id=player_id, last_action_type=self.last_action_type[player_id])
            env_team_obs.append(game_player_obs)
        env_team_obs = stack(env_team_obs)
        obs = default_collate_with_dim([env_team_obs], device=self.device)
        self.model_input = obs
        with torch.no_grad():
            model_output = self.model(self.model_input)['action'].cpu().detach().numpy()
        actions = []
        for i in range(len(model_output)):
            actions.append(self.features.transform_action(model_output[i]))
        ret = {}
        for player_id, act in zip(range(self.player_num * self.game_team_id, self.player_num * (self.game_team_id + 1)), actions):
            ret[player_id] = act
        for player_id, act in zip(range(self.player_num * self.game_team_id, self.player_num * (self.game_team_id + 1)), model_output):
            self.last_action_type[player_id] = act.item()
        return ret

def reset(self):
    self.last_action_type = {}
    for player_id in range(self.player_num * self.game_team_id, self.player_num * (self.game_team_id + 1)):
        self.last_action_type[player_id] = self.features.direction_num * 2

