# Cluster 6

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

class BotAgent(BaseAgent):
    """
    Overview:
        A simple script bot
    """

    def __init__(self, name=None, level=3):
        self.name = name
        self.actions_queue = queue.Queue()
        self.last_clone_num = 1
        self.level = level

    def step(self, obs):
        if self.level == 1:
            return self.step_level_1(obs)
        if self.level == 2:
            return self.step_level_2(obs)
        if self.level == 3:
            return self.step_level_3(obs)

    def step_level_1(self, obs):
        if self.actions_queue.qsize() > 0:
            return self.actions_queue.get()
        overlap = obs['overlap']
        overlap = self.preprocess(overlap)
        food_balls = overlap['food']
        thorns_balls = overlap['thorns']
        spore_balls = overlap['spore']
        clone_balls = overlap['clone']
        my_clone_balls, others_clone_balls = self.process_clone_balls(clone_balls)
        min_distance, min_food_ball = self.process_food_balls(food_balls, my_clone_balls[0])
        if min_food_ball is not None:
            direction = (min_food_ball['position'] - my_clone_balls[0]['position']).normalize()
        else:
            direction = (Vector2(0, 0) - my_clone_balls[0]['position']).normalize()
        action_type = 0
        self.actions_queue.put([direction.x, direction.y, action_type])
        action_ret = self.actions_queue.get()
        return action_ret

    def step_level_2(self, obs):
        if self.actions_queue.qsize() > 0:
            return self.actions_queue.get()
        overlap = obs['overlap']
        overlap = self.preprocess(overlap)
        food_balls = overlap['food']
        thorns_balls = overlap['thorns']
        spore_balls = overlap['spore']
        clone_balls = overlap['clone']
        my_clone_balls, others_clone_balls = self.process_clone_balls(clone_balls)
        min_distance, min_thorns_ball = self.process_thorns_balls(thorns_balls, my_clone_balls[0])
        min_distance, min_food_ball = self.process_food_balls(food_balls, my_clone_balls[0])
        if min_thorns_ball is not None:
            direction = min_thorns_ball['position'] - my_clone_balls[0]['position']
        elif min_food_ball is not None:
            direction = min_food_ball['position'] - my_clone_balls[0]['position']
        else:
            direction = Vector2(0, 0) - my_clone_balls[0]['position']
        action_type = 0
        if direction.length() > 0:
            direction = direction.normalize()
        else:
            direction = Vector2(1, 1).normalize()
        self.actions_queue.put([direction.x, direction.y, action_type])
        action_ret = self.actions_queue.get()
        return action_ret

    def step_level_3(self, obs):
        if self.actions_queue.qsize() > 0:
            return self.actions_queue.get()
        overlap = obs['overlap']
        overlap = self.preprocess(overlap)
        food_balls = overlap['food']
        thorns_balls = overlap['thorns']
        spore_balls = overlap['spore']
        clone_balls = overlap['clone']
        my_clone_balls, others_clone_balls = self.process_clone_balls(clone_balls)
        if len(my_clone_balls) >= 9 and my_clone_balls[4]['radius'] > 4:
            self.actions_queue.put([0, 0, 0])
            self.actions_queue.put([0, 0, 0])
            self.actions_queue.put([0, 0, 0])
            self.actions_queue.put([0, 0, 0])
            self.actions_queue.put([0, 0, 0])
            self.actions_queue.put([0, 0, 0])
            self.actions_queue.put([0, 0, 0])
            self.actions_queue.put([None, None, 1])
            self.actions_queue.put([None, None, 1])
            self.actions_queue.put([None, None, 1])
            self.actions_queue.put([None, None, 1])
            self.actions_queue.put([None, None, 1])
            self.actions_queue.put([None, None, 1])
            self.actions_queue.put([None, None, 1])
            self.actions_queue.put([None, None, 1])
            action_ret = self.actions_queue.get()
            return action_ret
        if len(others_clone_balls) > 0 and self.can_eat(others_clone_balls[0]['radius'], my_clone_balls[0]['radius']):
            direction = my_clone_balls[0]['position'] - others_clone_balls[0]['position']
            action_type = 0
        else:
            min_distance, min_thorns_ball = self.process_thorns_balls(thorns_balls, my_clone_balls[0])
            if min_thorns_ball is not None:
                direction = min_thorns_ball['position'] - my_clone_balls[0]['position']
            else:
                min_distance, min_food_ball = self.process_food_balls(food_balls, my_clone_balls[0])
                if min_food_ball is not None:
                    direction = min_food_ball['position'] - my_clone_balls[0]['position']
                else:
                    direction = Vector2(0, 0) - my_clone_balls[0]['position']
            action_random = random.random()
            if action_random < 0.02:
                action_type = 1
            if action_random < 0.04 and action_random > 0.02:
                action_type = 2
            else:
                action_type = 0
        if direction.length() > 0:
            direction = direction.normalize()
        else:
            direction = Vector2(1, 1).normalize()
        direction = self.add_noise_to_direction(direction).normalize()
        self.actions_queue.put([direction.x, direction.y, action_type])
        action_ret = self.actions_queue.get()
        return action_ret

    def process_clone_balls(self, clone_balls):
        my_clone_balls = []
        others_clone_balls = []
        for clone_ball in clone_balls:
            if clone_ball['player'] == self.name:
                my_clone_balls.append(copy.deepcopy(clone_ball))
        my_clone_balls.sort(key=lambda a: a['radius'], reverse=True)
        for clone_ball in clone_balls:
            if clone_ball['player'] != self.name:
                others_clone_balls.append(copy.deepcopy(clone_ball))
        others_clone_balls.sort(key=lambda a: a['radius'], reverse=True)
        return (my_clone_balls, others_clone_balls)

    def process_thorns_balls(self, thorns_balls, my_max_clone_ball):
        min_distance = 10000
        min_thorns_ball = None
        for thorns_ball in thorns_balls:
            if self.can_eat(my_max_clone_ball['radius'], thorns_ball['radius']):
                distance = (thorns_ball['position'] - my_max_clone_ball['position']).length()
                if distance < min_distance:
                    min_distance = distance
                    min_thorns_ball = copy.deepcopy(thorns_ball)
        return (min_distance, min_thorns_ball)

    def process_food_balls(self, food_balls, my_max_clone_ball):
        min_distance = 10000
        min_food_ball = None
        for food_ball in food_balls:
            distance = (food_ball['position'] - my_max_clone_ball['position']).length()
            if distance < min_distance:
                min_distance = distance
                min_food_ball = copy.deepcopy(food_ball)
        return (min_distance, min_food_ball)

    def preprocess(self, overlap):
        new_overlap = {}
        for k, v in overlap.items():
            if k == 'clone':
                new_overlap[k] = []
                for index, vv in enumerate(v):
                    tmp = {}
                    tmp['position'] = Vector2(vv[0], vv[1])
                    tmp['radius'] = vv[2]
                    tmp['player'] = int(vv[-2])
                    tmp['team'] = int(vv[-1])
                    new_overlap[k].append(tmp)
            else:
                new_overlap[k] = []
                for index, vv in enumerate(v):
                    tmp = {}
                    tmp['position'] = Vector2(vv[0], vv[1])
                    tmp['radius'] = vv[2]
                    new_overlap[k].append(tmp)
        return new_overlap

    def preprocess_tuple2vector(self, overlap):
        new_overlap = {}
        for k, v in overlap.items():
            new_overlap[k] = []
            for index, vv in enumerate(v):
                new_overlap[k].append(vv)
                new_overlap[k][index]['position'] = Vector2(*vv['position'])
        return new_overlap

    def add_noise_to_direction(self, direction, noise_ratio=0.1):
        direction = direction + Vector2((random.random() * 2 - 1) * noise_ratio * direction.x, (random.random() * 2 - 1) * noise_ratio * direction.y)
        return direction

    def radius_to_score(self, radius):
        return (math.pow(radius, 2) - 0.15) / 0.042 * 100

    def can_eat(self, radius1, radius2):
        return self.radius_to_score(radius1) > 1.3 * self.radius_to_score(radius2)

def process_clone_balls(self, clone_balls):
    my_clone_balls = []
    others_clone_balls = []
    for clone_ball in clone_balls:
        if clone_ball['player'] == self.name:
            my_clone_balls.append(copy.deepcopy(clone_ball))
    my_clone_balls.sort(key=lambda a: a['radius'], reverse=True)
    for clone_ball in clone_balls:
        if clone_ball['player'] != self.name:
            others_clone_balls.append(copy.deepcopy(clone_ball))
    others_clone_balls.sort(key=lambda a: a['radius'], reverse=True)
    return (my_clone_balls, others_clone_balls)

def preprocess(self, overlap):
    new_overlap = {}
    for k, v in overlap.items():
        if k == 'clone':
            new_overlap[k] = []
            for index, vv in enumerate(v):
                tmp = {}
                tmp['position'] = Vector2(vv[0], vv[1])
                tmp['radius'] = vv[2]
                tmp['player'] = int(vv[-2])
                tmp['team'] = int(vv[-1])
                new_overlap[k].append(tmp)
        else:
            new_overlap[k] = []
            for index, vv in enumerate(v):
                tmp = {}
                tmp['position'] = Vector2(vv[0], vv[1])
                tmp['radius'] = vv[2]
                new_overlap[k].append(tmp)
    return new_overlap

def preprocess_tuple2vector(self, overlap):
    new_overlap = {}
    for k, v in overlap.items():
        new_overlap[k] = []
        for index, vv in enumerate(v):
            new_overlap[k].append(vv)
            new_overlap[k][index]['position'] = Vector2(*vv['position'])
    return new_overlap

def add_noise_to_direction(self, direction, noise_ratio=0.1):
    direction = direction + Vector2((random.random() * 2 - 1) * noise_ratio * direction.x, (random.random() * 2 - 1) * noise_ratio * direction.y)
    return direction

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

def get_balls(self):
    balls = []
    for player_id, player in self.players.items():
        balls.extend(player.get_balls())
    return balls

def adjust(self):
    """
        Overview:
            Adjust all balls in all players
        """
    eats = {}
    for player in self.get_players():
        eats[player.player_id] = player.adjust()
    return eats

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

class Button(object):

    def __init__(self, x, y, text, half_w=8, half_h=8):
        self.text = text
        self.x = x
        self.y = y
        self.half_w = half_w
        self.half_h = half_h
        self.left = x - half_w
        self.top = y - half_h
        self.right = x + half_w
        self.bottom = y + half_h
        self.font = pygame.font.SysFont('arial', 11, True)

    def display(self, screen, text=None):
        if text is None:
            text = self.text
        txt = self.font.render(text, True, BLACK)
        bg_rect = pygame.Rect(self.left, self.top, self.half_w * 2, self.half_h * 2)
        pygame.draw.rect(screen, WHITE, bg_rect)
        screen.blit(txt, txt.get_rect(center=(self.x, self.y)))

    def check_click(self, position):
        x_match = position[0] > self.left and position[0] < self.right
        y_match = position[1] > self.top and position[1] < self.bottom
        if x_match and y_match:
            return True
        else:
            return False

def __init__(self, x, y, text, half_w=8, half_h=8):
    self.text = text
    self.x = x
    self.y = y
    self.half_w = half_w
    self.half_h = half_h
    self.left = x - half_w
    self.top = y - half_h
    self.right = x + half_w
    self.bottom = y + half_h
    self.font = pygame.font.SysFont('arial', 11, True)

def display(self, screen, text=None):
    if text is None:
        text = self.text
    txt = self.font.render(text, True, BLACK)
    bg_rect = pygame.Rect(self.left, self.top, self.half_w * 2, self.half_h * 2)
    pygame.draw.rect(screen, WHITE, bg_rect)
    screen.blit(txt, txt.get_rect(center=(self.x, self.y)))

class PlayButton(Button):

    def __init__(self, x, y, text, half_w=8, half_h=8):
        super(PlayButton, self).__init__(x, y, text, half_w=half_w, half_h=half_h)
        self.text_choices = ['>', '||']
        self.play = True if text == '||' else False

    def on_pressed(self):
        self.play = not self.play
        self.text = self.text_choices[int(self.play)]
        return self.play

def on_pressed(self):
    self.play = not self.play
    self.text = self.text_choices[int(self.play)]
    return self.play

class SpeedButton(Button):

    def __init__(self, x, y, text, half_w=8, half_h=8):
        super(SpeedButton, self).__init__(x, y, text, half_w=half_w, half_h=half_h)
        self.speed_choices = ['x1', 'x2', 'x4', 'x8']
        self.speed = 1
        self.speed_index = 0

    def on_pressed(self):
        self.speed_index = (self.speed_index + 1) % len(self.speed_choices)
        self.text = self.speed_choices[self.speed_index]
        self.speed = int(self.text[-1])
        return self.speed

def on_pressed(self):
    self.speed_index = (self.speed_index + 1) % len(self.speed_choices)
    self.text = self.speed_choices[self.speed_index]
    self.speed = int(self.text[-1])
    return self.speed

class Scrollbar(object):

    def __init__(self, x, y, length, width=8):
        self.x = x
        self.y = y
        self.length = length
        self.width = width
        self.top = self.y - width / 2
        self.bottom = self.y + width / 2
        self.rate = 0

    def on_pressed(self, position):
        self.rate = 1.0 * (position[0] - self.x) / self.length
        return self.rate

    def check_click(self, position):
        if position[0] > self.x and position[0] < self.x + self.length and (position[1] > self.top) and (position[1] < self.bottom):
            return True
        else:
            return False

    def display(self, screen, rate=None):
        if rate is None:
            rate = self.rate
        pygame.draw.line(screen, BLACK, (self.x, self.y), (self.x + self.length, self.y), width=3)
        pygame.draw.line(screen, YELLOW, (self.x + self.length * rate, self.top), (self.x + self.length * rate, self.bottom), width=4)

def display(self, screen, rate=None):
    if rate is None:
        rate = self.rate
    pygame.draw.line(screen, BLACK, (self.x, self.y), (self.x + self.length, self.y), width=3)
    pygame.draw.line(screen, YELLOW, (self.x + self.length * rate, self.top), (self.x + self.length * rate, self.bottom), width=4)

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

def on_pressed(self, position):
    if self.play_button.check_click(position):
        self.if_play = self.play_button.on_pressed()
    elif self.speed_button.check_click(position):
        self.speed = self.speed_button.on_pressed()
    elif self.scrollbar.check_click(position):
        self.rate = self.scrollbar.on_pressed(position)
        self.frame_target = int(self.rate * self.frame_total)

class EnvRender(BaseRender):
    """
    Overview:
        No need to use a new window, giving a global view and the view that each player can see
    """

    def __init__(self, game_screen_width=512, game_screen_height=512, info_width=60, info_height=0, with_show=False, padding=20, map_width=256, map_height=256):
        super(EnvRender, self).__init__(game_screen_width=game_screen_width, game_screen_height=game_screen_height, info_width=info_width, info_height=info_height, with_show=with_show)
        self.scale_ratio_w = (self.game_screen_width - padding * 2) / map_width
        self.scale_ratio_h = (self.game_screen_height - padding * 2) / map_height
        self.padding = padding

    def get_screen(self, food_balls, thorns_balls, spore_balls, players, player_num_per_team):
        screen_all = pygame.Surface((self.total_screen_width, self.total_screen_height))
        screen_all = self.render_all_balls_colorful(screen_all, food_balls, thorns_balls, spore_balls, players, player_num_per_team)
        screen_all = self.render_leaderboard_colorful(screen_all, players, player_num_per_team)
        screen_data_all = pygame.surfarray.array3d(screen_all)
        screen_data_all = np.rot90(np.fliplr(cv2.cvtColor(screen_data_all, cv2.COLOR_RGB2BGR)))
        return screen_data_all

    def render_all_balls_colorful(self, screen, food_balls, thorns_balls, spore_balls, players, player_num_per_team):
        screen.fill(BACKGROUND)
        pygame.draw.line(screen, RED, (self.padding, self.padding), (self.game_screen_width - self.padding, self.padding), width=1)
        pygame.draw.line(screen, RED, (self.padding, self.padding), (self.padding, self.game_screen_width - self.padding), width=1)
        pygame.draw.line(screen, RED, (self.padding, self.game_screen_width - self.padding), (self.game_screen_width - self.padding, self.game_screen_width - self.padding), width=1)
        pygame.draw.line(screen, RED, (self.game_screen_width - self.padding, self.padding), (self.game_screen_width - self.padding, self.game_screen_width - self.padding), width=1)
        pygame.draw.line(screen, BLACK, (self.game_screen_width, 0), (self.game_screen_width, self.game_screen_width + self.padding), width=1)
        for ball in food_balls:
            x = ball.position.x * self.scale_ratio_w + self.padding
            y = ball.position.y * self.scale_ratio_h + self.padding
            r = ball.radius * self.scale_ratio_w
            pygame.draw.circle(screen, FOOD_COLOR, Vector2(x, y), r)
        for ball in thorns_balls:
            x = ball.position.x * self.scale_ratio_w + self.padding
            y = ball.position.y * self.scale_ratio_h + self.padding
            r = ball.radius * self.scale_ratio_w
            pygame.draw.polygon(screen, THORNS_COLOR, to_aliased_circle(Vector2(x, y), r))
        for ball in spore_balls:
            x = ball.position.x * self.scale_ratio_w + self.padding
            y = ball.position.y * self.scale_ratio_h + self.padding
            r = ball.radius * self.scale_ratio_w
            pygame.draw.circle(screen, SPORE_COLOR, Vector2(x, y), r)
        for player in players:
            for ball in player.get_balls():
                x = ball.position.x * self.scale_ratio_w + self.padding
                y = ball.position.y * self.scale_ratio_h + self.padding
                r = ball.radius * self.scale_ratio_w
                pygame.draw.circle(screen, PLAYER_COLORS[int(ball.team_id)][0], Vector2(x, y), r)
                point_list = to_arrow(Vector2(x, y), r, ball.direction)
                pygame.draw.polygon(screen, PLAYER_COLORS[int(ball.team_id)][0], point_list)
                font_size = int(r / 1.6)
                font = pygame.font.SysFont('arial', max(font_size, 8), True)
                txt = font.render('{}'.format(chr(int(ball.player_id % player_num_per_team) + 65)), True, WHITE)
                txt_rect = txt.get_rect(center=(x, y))
                screen.blit(txt, txt_rect)
        return screen

    def render_leaderboard_colorful(self, screen, players, player_num_per_team):
        team_name_score = {}
        team_score = {}
        for player in players:
            if player.team_id not in team_name_score:
                team_name_score[player.team_id] = {}
                team_score[player.team_id] = 0
            team_name_score[player.team_id][player.player_id] = player.get_total_score()
            team_score[player.team_id] += team_name_score[player.team_id][player.player_id]
        team_score = sorted(team_score.items(), key=lambda d: d[1], reverse=True)
        start = 10
        for index, (team_id, score) in enumerate(team_score):
            start += 20
            font = pygame.font.SysFont('arial', 8, True)
            fps_txt = font.render('{} : {:.2f}'.format(team_id, score), True, PLAYER_COLORS[int(team_id)][0])
            screen.blit(fps_txt, (self.game_screen_width + 5, start))
            start += 20
            font = pygame.font.SysFont('arial', 7, True)
            for player_id, player_score in team_name_score[team_id].items():
                fps_txt = font.render('{} : {:.2f}'.format(chr(player_id % player_num_per_team + 65), player_score), True, PLAYER_COLORS[team_id][0])
                screen.blit(fps_txt, (self.game_screen_width + 5, start))
                start += 20
        return screen

    def show(self):
        raise NotImplementedError

    def close(self):
        pygame.quit()

def render_all_balls_colorful(self, screen, food_balls, thorns_balls, spore_balls, players, player_num_per_team):
    screen.fill(BACKGROUND)
    pygame.draw.line(screen, RED, (self.padding, self.padding), (self.game_screen_width - self.padding, self.padding), width=1)
    pygame.draw.line(screen, RED, (self.padding, self.padding), (self.padding, self.game_screen_width - self.padding), width=1)
    pygame.draw.line(screen, RED, (self.padding, self.game_screen_width - self.padding), (self.game_screen_width - self.padding, self.game_screen_width - self.padding), width=1)
    pygame.draw.line(screen, RED, (self.game_screen_width - self.padding, self.padding), (self.game_screen_width - self.padding, self.game_screen_width - self.padding), width=1)
    pygame.draw.line(screen, BLACK, (self.game_screen_width, 0), (self.game_screen_width, self.game_screen_width + self.padding), width=1)
    for ball in food_balls:
        x = ball.position.x * self.scale_ratio_w + self.padding
        y = ball.position.y * self.scale_ratio_h + self.padding
        r = ball.radius * self.scale_ratio_w
        pygame.draw.circle(screen, FOOD_COLOR, Vector2(x, y), r)
    for ball in thorns_balls:
        x = ball.position.x * self.scale_ratio_w + self.padding
        y = ball.position.y * self.scale_ratio_h + self.padding
        r = ball.radius * self.scale_ratio_w
        pygame.draw.polygon(screen, THORNS_COLOR, to_aliased_circle(Vector2(x, y), r))
    for ball in spore_balls:
        x = ball.position.x * self.scale_ratio_w + self.padding
        y = ball.position.y * self.scale_ratio_h + self.padding
        r = ball.radius * self.scale_ratio_w
        pygame.draw.circle(screen, SPORE_COLOR, Vector2(x, y), r)
    for player in players:
        for ball in player.get_balls():
            x = ball.position.x * self.scale_ratio_w + self.padding
            y = ball.position.y * self.scale_ratio_h + self.padding
            r = ball.radius * self.scale_ratio_w
            pygame.draw.circle(screen, PLAYER_COLORS[int(ball.team_id)][0], Vector2(x, y), r)
            point_list = to_arrow(Vector2(x, y), r, ball.direction)
            pygame.draw.polygon(screen, PLAYER_COLORS[int(ball.team_id)][0], point_list)
            font_size = int(r / 1.6)
            font = pygame.font.SysFont('arial', max(font_size, 8), True)
            txt = font.render('{}'.format(chr(int(ball.player_id % player_num_per_team) + 65)), True, WHITE)
            txt_rect = txt.get_rect(center=(x, y))
            screen.blit(txt, txt_rect)
    return screen

def render_leaderboard_colorful(self, screen, players, player_num_per_team):
    team_name_score = {}
    team_score = {}
    for player in players:
        if player.team_id not in team_name_score:
            team_name_score[player.team_id] = {}
            team_score[player.team_id] = 0
        team_name_score[player.team_id][player.player_id] = player.get_total_score()
        team_score[player.team_id] += team_name_score[player.team_id][player.player_id]
    team_score = sorted(team_score.items(), key=lambda d: d[1], reverse=True)
    start = 10
    for index, (team_id, score) in enumerate(team_score):
        start += 20
        font = pygame.font.SysFont('arial', 8, True)
        fps_txt = font.render('{} : {:.2f}'.format(team_id, score), True, PLAYER_COLORS[int(team_id)][0])
        screen.blit(fps_txt, (self.game_screen_width + 5, start))
        start += 20
        font = pygame.font.SysFont('arial', 7, True)
        for player_id, player_score in team_name_score[team_id].items():
            fps_txt = font.render('{} : {:.2f}'.format(chr(player_id % player_num_per_team + 65), player_score), True, PLAYER_COLORS[team_id][0])
            screen.blit(fps_txt, (self.game_screen_width + 5, start))
            start += 20
    return screen

def profile():
    ball_num = 2000
    border = 1000
    cx = 500
    cy = 500
    r = 100
    balls = []
    for _ in range(ball_num):
        balls.append(Vector2(random.random() * border, random.random() * border))
    t1 = time.time()
    for i in range(1000):
        res1 = method1(balls, cx, cy, r)
    t2 = time.time()
    tt1_all = 0
    tt2_all = 0
    count = 10000
    for i in range(count):
        res_x, res_y, tt1, tt2 = method2(balls, cx, cy, r)
        tt1_all += tt1
        tt2_all += tt2
    print(tt1_all / count, tt2_all / count)
    t3 = time.time()
    print((t2 - t1) / count, (t3 - t2) / count)
    import pdb
    pdb.set_trace()
    print('end')

class Border:
    """
    Overview:
        used to specify a rectangular range
    """

    def __init__(self, minx, miny, maxx, maxy, random_generator=None):
        self.minx = minx
        self.miny = miny
        self.maxx = maxx
        self.maxy = maxy
        self.width = self.maxx - self.minx
        self.height = self.maxy - self.miny
        if random_generator is not None:
            self._random = random_generator
        else:
            self._random = random.Random()

    def __repr__(self) -> str:
        return '[' + str(self.minx) + ',' + str(self.miny) + ',' + str(self.maxx) + ',' + str(self.maxy) + ']'

    def contains(self, position: Vector2) -> bool:
        """
        Overview:
            To judge whether a position in this border.
        Parameters:
            position <Vector2>: the position to be judged.
        Returns:
            bool: True or False, whether the position in this border.
        """
        return position.x > self.minx and position.x < self.maxx and (position.y > self.miny) and (position.y < self.maxy)

    def sample(self) -> Vector2:
        """
        Overview:
            Randomly sample a position in the border.
        Returns:
            Vector2: the sampled position.
        """
        x = self._random.uniform(self.minx, self.maxx)
        y = self._random.uniform(self.miny, self.maxy)
        return Vector2(x, y)

    def get_joint(self, border):
        new_minx = max(self.minx, border.minx)
        new_maxx = min(self.maxx, border.maxx)
        new_miny = max(self.miny, border.miny)
        new_maxy = min(self.maxy, border.maxy)
        if new_minx > new_maxx or new_miny > new_maxy:
            return None
        return Border(new_minx, new_maxx, new_miny, new_maxy, self._random)

def sample(self) -> Vector2:
    """
        Overview:
            Randomly sample a position in the border.
        Returns:
            Vector2: the sampled position.
        """
    x = self._random.uniform(self.minx, self.maxx)
    y = self._random.uniform(self.miny, self.maxy)
    return Vector2(x, y)

def get_joint(self, border):
    new_minx = max(self.minx, border.minx)
    new_maxx = min(self.maxx, border.maxx)
    new_miny = max(self.miny, border.miny)
    new_maxy = min(self.maxy, border.maxy)
    if new_minx > new_maxx or new_miny > new_maxy:
        return None
    return Border(new_minx, new_maxx, new_miny, new_maxy, self._random)

class QuadNode:

    def __init__(self, border, max_depth=32, max_num=64, parent=None) -> None:
        self.border = border
        self.max_depth = max_depth
        self.midx = (border.minx + border.maxx) / 2
        self.midy = (border.miny + border.maxy) / 2
        self.max_num = max_num
        self.children = None
        self.parent = parent
        self.items = []

    def get_quad(self, node):
        if node.position.x < self.midx:
            if node.position.y < self.midy:
                return 0
            else:
                return 1
        elif node.position.y < self.midy:
            return 2
        else:
            return 3

    def insert(self, node):
        if not self.children == None:
            self.children[self.get_quad(node)].insert(node)
        else:
            self.items.append(node)
            node.quad_node = self
            if len(self.items) > self.max_num and self.max_depth >= 1:
                b0 = Border(self.border.minx, self.border.miny, self.midx, self.midy)
                b1 = Border(self.border.minx, self.midy, self.midx, self.border.maxy)
                b2 = Border(self.midx, self.border.miny, self.border.maxx, self.midy)
                b3 = Border(self.midx, self.midy, self.border.maxx, self.border.maxy)
                self.children = []
                self.children.append(QuadNode(b0, max_depth=self.max_depth - 1, max_num=self.max_num, parent=self))
                self.children.append(QuadNode(b1, max_depth=self.max_depth - 1, max_num=self.max_num, parent=self))
                self.children.append(QuadNode(b2, max_depth=self.max_depth - 1, max_num=self.max_num, parent=self))
                self.children.append(QuadNode(b3, max_depth=self.max_depth - 1, max_num=self.max_num, parent=self))
                for item in self.items:
                    self.children[self.get_quad(item)].insert(item)
                self.items.clear()

    def find(self, border):
        ans = self.items
        if not self.children == None:
            for child in self.children:
                tmpBorder = border.get_joint(child.border)
                if not tmpBorder == None:
                    ans = ans + child.find(tmpBorder)
        return ans

    def clear(self):
        if self.children == None:
            return
        max_num = self.max_num
        for child in self.children:
            if not child.children == None:
                return
            max_num = max_num - len(child.items)
        if max_num >= 0:
            for child in self.children:
                for item in child.items:
                    item.quad_node = self
                    self.items.append(item)
            self.children = None
            if not self.parent == None:
                self.parent.clear()

    def remove(self, node):
        for i, item in enumerate(self.items):
            if item.ball_id == node.ball_id:
                del self.items[i]
                break
        node.quad_node = None
        if not self.parent == None:
            self.parent.clear()

def insert(self, node):
    if not self.children == None:
        self.children[self.get_quad(node)].insert(node)
    else:
        self.items.append(node)
        node.quad_node = self
        if len(self.items) > self.max_num and self.max_depth >= 1:
            b0 = Border(self.border.minx, self.border.miny, self.midx, self.midy)
            b1 = Border(self.border.minx, self.midy, self.midx, self.border.maxy)
            b2 = Border(self.midx, self.border.miny, self.border.maxx, self.midy)
            b3 = Border(self.midx, self.midy, self.border.maxx, self.border.maxy)
            self.children = []
            self.children.append(QuadNode(b0, max_depth=self.max_depth - 1, max_num=self.max_num, parent=self))
            self.children.append(QuadNode(b1, max_depth=self.max_depth - 1, max_num=self.max_num, parent=self))
            self.children.append(QuadNode(b2, max_depth=self.max_depth - 1, max_num=self.max_num, parent=self))
            self.children.append(QuadNode(b3, max_depth=self.max_depth - 1, max_num=self.max_num, parent=self))
            for item in self.items:
                self.children[self.get_quad(item)].insert(item)
            self.items.clear()

def find(self, border):
    ans = self.items
    if not self.children == None:
        for child in self.children:
            tmpBorder = border.get_joint(child.border)
            if not tmpBorder == None:
                ans = ans + child.find(tmpBorder)
    return ans

def clear(self):
    if self.children == None:
        return
    max_num = self.max_num
    for child in self.children:
        if not child.children == None:
            return
        max_num = max_num - len(child.items)
    if max_num >= 0:
        for child in self.children:
            for item in child.items:
                item.quad_node = self
                self.items.append(item)
        self.children = None
        if not self.parent == None:
            self.parent.clear()

def remove(self, node):
    for i, item in enumerate(self.items):
        if item.ball_id == node.ball_id:
            del self.items[i]
            break
    node.quad_node = None
    if not self.parent == None:
        self.parent.clear()

class ExhaustiveCollisionDetection(BaseCollisionDetection):
    """
    Overview:
        Exhaustive Algorithm
    """

    def __init__(self, border: Border) -> None:
        super(ExhaustiveCollisionDetection, self).__init__(border=border)

    def solve(self, query_list: list, gallery_list: list):
        """
        Overview:
            For the balls in the query, enumerate each ball in the gallery to determine whether there is a collision
        Parameters:
            query_list <List[BaseBall]>: List of balls that need to be queried for collision
            gallery_list <List[BaseBall]>: List of all balls
        Returns:
            results <Dict[int: List[BaseBall]> return value
                int value denotes:
                    the subscript in query_list
                string value denotes:
                    List of balls that collided with the query corresponding to the subscript
        """
        results = {}
        for i, q in enumerate(query_list):
            results[i] = []
            for j, g in enumerate(gallery_list):
                if q.judge_cover(g):
                    results[i].append(g)
        return results

def solve(self, query_list: list, gallery_list: list):
    """
        Overview:
            For the balls in the query, enumerate each ball in the gallery to determine whether there is a collision
        Parameters:
            query_list <List[BaseBall]>: List of balls that need to be queried for collision
            gallery_list <List[BaseBall]>: List of all balls
        Returns:
            results <Dict[int: List[BaseBall]> return value
                int value denotes:
                    the subscript in query_list
                string value denotes:
                    List of balls that collided with the query corresponding to the subscript
        """
    results = {}
    for i, q in enumerate(query_list):
        results[i] = []
        for j, g in enumerate(gallery_list):
            if q.judge_cover(g):
                results[i].append(g)
    return results

class PrecisionCollisionDetection(BaseCollisionDetection):
    """
    Overview:
        Precision Approximation Algorithm
        Divide the map into several rows according to the accuracy that has been set, dynamically maintain the row information in each frame, and search by row
    """

    def __init__(self, border: Border, precision: int=50) -> None:
        """
        Parameter:
            precision <int>: the precision of dividing rows
        """
        super(PrecisionCollisionDetection, self).__init__(border=border)
        self.precision = precision

    def get_row(self, x) -> int:
        """
        Overview:
            Get the row coordinates of the ball
        Parameter:
            node <BaseBall>: The ball need to get its row coordinates
        """
        return int((x - self.border.minx) / self.border.height * self.precision)

    def solve(self, query_list: list, gallery_list: list):
        """
        Overview:
            First, you need to sort the balls in each row according to the ordinate. 
            For the balls in query_list, first abstract the boundary of the ball into 
            a rectangle, then traverse each row in the rectangle, and find the first 
            ball covered by the query through dichotomy in each row, and then Enumerate 
            the balls in sequence until the ordinate exceeds the boundary of the query 
            rectangle.
        Parameters:
            query_list <List[BaseBall]>: List of balls that need to be queried for collision
            gallery_list <List[BaseBall]>: List of all balls
        Returns:
            results <Dict[int: List[BaseBall]> return value
                int value denotes:
                    the subscript in query_list
                string value denotes:
                    List of balls that collided with the query corresponding to the subscript
        """
        vec = {}
        for id, node in enumerate(gallery_list):
            row_id = self.get_row(node.position.x)
            if row_id not in vec:
                vec[row_id] = []
            vec[row_id].append((id, node.position.y))
        for val in vec.values():
            val.sort(key=lambda x: x[1])
        results = {}
        for id, query in enumerate(query_list):
            results[id] = []
            left = query.position.y - query.radius
            right = query.position.y + query.radius
            top = self.get_row(query.position.x - query.radius)
            bottom = self.get_row(query.position.x + query.radius)
            for i in range(top, bottom + 1):
                if i not in vec:
                    continue
                l = len(vec[i])
                start_pos = 0
                for j in range(15, -1, -1):
                    if start_pos + 2 ** j < l and vec[i][start_pos + 2 ** j][1] < left:
                        start_pos += 2 ** j
                for j in range(start_pos, l):
                    if vec[i][j][1] > right:
                        break
                    if query.judge_cover(gallery_list[vec[i][j][0]]):
                        results[id].append(gallery_list[vec[i][j][0]])
        return results

def get_row(self, x) -> int:
    """
        Overview:
            Get the row coordinates of the ball
        Parameter:
            node <BaseBall>: The ball need to get its row coordinates
        """
    return int((x - self.border.minx) / self.border.height * self.precision)

def solve(self, query_list: list, gallery_list: list):
    """
        Overview:
            First, you need to sort the balls in each row according to the ordinate. 
            For the balls in query_list, first abstract the boundary of the ball into 
            a rectangle, then traverse each row in the rectangle, and find the first 
            ball covered by the query through dichotomy in each row, and then Enumerate 
            the balls in sequence until the ordinate exceeds the boundary of the query 
            rectangle.
        Parameters:
            query_list <List[BaseBall]>: List of balls that need to be queried for collision
            gallery_list <List[BaseBall]>: List of all balls
        Returns:
            results <Dict[int: List[BaseBall]> return value
                int value denotes:
                    the subscript in query_list
                string value denotes:
                    List of balls that collided with the query corresponding to the subscript
        """
    vec = {}
    for id, node in enumerate(gallery_list):
        row_id = self.get_row(node.position.x)
        if row_id not in vec:
            vec[row_id] = []
        vec[row_id].append((id, node.position.y))
    for val in vec.values():
        val.sort(key=lambda x: x[1])
    results = {}
    for id, query in enumerate(query_list):
        results[id] = []
        left = query.position.y - query.radius
        right = query.position.y + query.radius
        top = self.get_row(query.position.x - query.radius)
        bottom = self.get_row(query.position.x + query.radius)
        for i in range(top, bottom + 1):
            if i not in vec:
                continue
            l = len(vec[i])
            start_pos = 0
            for j in range(15, -1, -1):
                if start_pos + 2 ** j < l and vec[i][start_pos + 2 ** j][1] < left:
                    start_pos += 2 ** j
            for j in range(start_pos, l):
                if vec[i][j][1] > right:
                    break
                if query.judge_cover(gallery_list[vec[i][j][0]]):
                    results[id].append(gallery_list[vec[i][j][0]])
    return results

class RebuildQuadTreeCollisionDetection(BaseCollisionDetection):
    """
        Overview:
            Build a quadtree on a two-dimensional plane in every frame, and query collisions in the quadtree

    """

    def __init__(self, border: Border, node_capacity=64, tree_depth=32) -> None:
        """
        Parameter:
            node_capacity <int>: The capacity of each point in the quadtree
            tree_depth <int>: The max depth of the quadtree
        """
        super(RebuildQuadTreeCollisionDetection, self).__init__(border=border)
        self.node_capacity = node_capacity
        self.tree_depth = tree_depth
        self.border = border

    def solve(self, query_list: list, gallery_list: list):
        """
        Overview:
           Construct a quadtree from scratch based on gallery_list and complete the query
        Parameters:
            query_list <List[BaseBall]>: List of balls that need to be queried for collision
            gallery_list <List[BaseBall]>: List of all balls
        Returns:
            results <Dict[int: List[BaseBall]> return value
                int value denotes:
                    the subscript in query_list
                string value denotes:
                    List of balls that collided with the query corresponding to the subscript
        """
        quadTree = QuadNode(border=self.border, max_depth=self.tree_depth, max_num=self.node_capacity)
        for node in gallery_list:
            quadTree.insert(node)
        results = {}
        for i, query in enumerate(query_list):
            results[i] = []
            quadTree_results = quadTree.find(Border(max(query.position.x - query.radius, self.border.minx), max(query.position.y - query.radius, self.border.miny), min(query.position.x + query.radius, self.border.maxx), min(query.position.y + query.radius, self.border.maxy)))
            for result in quadTree_results:
                if query.judge_cover(result):
                    results[i].append(result)
        return results

def solve(self, query_list: list, gallery_list: list):
    """
        Overview:
           Construct a quadtree from scratch based on gallery_list and complete the query
        Parameters:
            query_list <List[BaseBall]>: List of balls that need to be queried for collision
            gallery_list <List[BaseBall]>: List of all balls
        Returns:
            results <Dict[int: List[BaseBall]> return value
                int value denotes:
                    the subscript in query_list
                string value denotes:
                    List of balls that collided with the query corresponding to the subscript
        """
    quadTree = QuadNode(border=self.border, max_depth=self.tree_depth, max_num=self.node_capacity)
    for node in gallery_list:
        quadTree.insert(node)
    results = {}
    for i, query in enumerate(query_list):
        results[i] = []
        quadTree_results = quadTree.find(Border(max(query.position.x - query.radius, self.border.minx), max(query.position.y - query.radius, self.border.miny), min(query.position.x + query.radius, self.border.maxx), min(query.position.y + query.radius, self.border.maxy)))
        for result in quadTree_results:
            if query.judge_cover(result):
                results[i].append(result)
    return results

class RemoveQuadTreeCollisionDetection(BaseCollisionDetection):
    """
        Overview:
            Add delete operations for the quadtree, and dynamically maintain a quadtree

    """

    def __init__(self, border: Border, node_capacity=64, tree_depth=32) -> None:
        """
        Parameter:
            node_capacity <int>: The capacity of each point in the quadtree
            tree_depth <int>: The max depth of the quadtree
        """
        super(RemoveQuadTreeCollisionDetection, self).__init__(border=border)
        self.node_capacity = node_capacity
        self.tree_depth = tree_depth
        self.border = border
        self.quadTree = QuadNode(border=border, max_depth=tree_depth, max_num=node_capacity, parent=None)

    def solve(self, query_list: list, changed_node_list: list):
        """
        Overview:
           Update the points in the quadtree according to the changed_node_list and complete the query
        Parameters:
            query_list <List[BaseBall]>: List of balls that need to be queried for collision
            gallery_list <List[BaseBall]>: List of all balls
        Returns:
            results <Dict[int: List[BaseBall]> return value
                int value denotes:
                    the subscript in query_list
                string value denotes:
                    List of balls that collided with the query corresponding to the subscript
        """
        for node in changed_node_list:
            if not node.quad_node == None:
                node.quad_node.remove(node)
            if not node.is_remove:
                self.quadTree.insert(node)
        results = {}
        for i, query in enumerate(query_list):
            results[i] = []
            quadTree_results = self.quadTree.find(Border(max(query.position.x - query.radius, self.border.minx), max(query.position.y - query.radius, self.border.miny), min(query.position.x + query.radius, self.border.maxx), min(query.position.y + query.radius, self.border.maxy)))
            for result in quadTree_results:
                if query.judge_cover(result):
                    results[i].append(result)
        return results

def solve(self, query_list: list, changed_node_list: list):
    """
        Overview:
           Update the points in the quadtree according to the changed_node_list and complete the query
        Parameters:
            query_list <List[BaseBall]>: List of balls that need to be queried for collision
            gallery_list <List[BaseBall]>: List of all balls
        Returns:
            results <Dict[int: List[BaseBall]> return value
                int value denotes:
                    the subscript in query_list
                string value denotes:
                    List of balls that collided with the query corresponding to the subscript
        """
    for node in changed_node_list:
        if not node.quad_node == None:
            node.quad_node.remove(node)
        if not node.is_remove:
            self.quadTree.insert(node)
    results = {}
    for i, query in enumerate(query_list):
        results[i] = []
        quadTree_results = self.quadTree.find(Border(max(query.position.x - query.radius, self.border.minx), max(query.position.y - query.radius, self.border.miny), min(query.position.x + query.radius, self.border.maxx), min(query.position.y + query.radius, self.border.maxy)))
        for result in quadTree_results:
            if query.judge_cover(result):
                results[i].append(result)
    return results

@pytest.mark.unittest
class TestBorder:

    def test_init(self):
        border = Border(0, 0, 1000, 1000)
        assert border.minx == 0
        assert border.miny == 0
        assert border.maxx == 1000
        assert border.maxy == 1000
        assert border.width == 1000
        assert border.height == 1000

    def test_contains(self):
        border = Border(0, 0, 1000, 1000)
        assert border.contains(position=Vector2(300, 300))
        assert not border.contains(position=Vector2(1300, 300))

    def test_sample(self):
        border = Border(0, 0, 1000, 1000)
        s = border.sample()
        assert border.contains(s)

    def test_get_joint(self):
        border = Border(0, 0, 1000, 1000)
        border_new = border.get_joint(border=Border(300, 300, 600, 600))
        assert border_new.minx == 300
        assert border_new.maxx == 300
        assert border_new.miny == 600
        assert border_new.maxy == 600

def test_get_joint(self):
    border = Border(0, 0, 1000, 1000)
    border_new = border.get_joint(border=Border(300, 300, 600, 600))
    assert border_new.minx == 300
    assert border_new.maxx == 300
    assert border_new.miny == 600
    assert border_new.maxy == 600

@pytest.mark.unittest
class TestQuadNode:

    def test_init(self):
        border = Border(0, 0, 1000, 1000)
        quad_node = QuadNode(border)
        assert quad_node.max_depth == 32

    def test_get_quad(self):
        border = Border(0, 0, 1000, 1000)
        quad_node = QuadNode(border)
        node = BaseBall('0', position=border.sample(), border=border, score=1)
        assert isinstance(quad_node.get_quad(node=node), int)

    def test_insert(self):
        border = Border(0, 0, 1000, 1000)
        quad_node = QuadNode(border)
        node = BaseBall('0', position=border.sample(), border=border, score=1)
        quad_node.insert(node=node)

    def test_find(self):
        border = Border(0, 0, 1000, 1000)
        quad_node = QuadNode(border)
        node = BaseBall('0', position=border.sample(), border=border, score=1)
        quad_node.find(border)

    def test_clear(self):
        border = Border(0, 0, 1000, 1000)
        quad_node = QuadNode(border)
        node = BaseBall('0', position=border.sample(), border=border, score=1)
        quad_node.clear()

    def test_remove(self):
        border = Border(0, 0, 1000, 1000)
        quad_node = QuadNode(border)
        node = BaseBall('0', position=border.sample(), border=border, score=1)
        quad_node.remove(node=node)

def test_init(self):
    border = Border(0, 0, 1000, 1000)
    quad_node = QuadNode(border)
    assert quad_node.max_depth == 32

def test_get_quad(self):
    border = Border(0, 0, 1000, 1000)
    quad_node = QuadNode(border)
    node = BaseBall('0', position=border.sample(), border=border, score=1)
    assert isinstance(quad_node.get_quad(node=node), int)

def test_insert(self):
    border = Border(0, 0, 1000, 1000)
    quad_node = QuadNode(border)
    node = BaseBall('0', position=border.sample(), border=border, score=1)
    quad_node.insert(node=node)

def test_find(self):
    border = Border(0, 0, 1000, 1000)
    quad_node = QuadNode(border)
    node = BaseBall('0', position=border.sample(), border=border, score=1)
    quad_node.find(border)

def test_clear(self):
    border = Border(0, 0, 1000, 1000)
    quad_node = QuadNode(border)
    node = BaseBall('0', position=border.sample(), border=border, score=1)
    quad_node.clear()

@pytest.mark.unittest
class TestCollisionDection:

    def test_exhaustive(self):
        border = Border(0, 0, 1000, 1000)
        totol_num = 1000
        query_num = 200
        gallery_list = []
        for i in range(totol_num):
            x = random.randint(border.minx, border.maxx) + random.random()
            y = random.randint(border.miny, border.maxy) + random.random()
            gallery_list.append(BaseBall(i, position=Vector2(x, y), border=border, score=1))
        collision_detection = create_collision_detection('exhaustive', border=border)
        query_list = random.sample(gallery_list, query_num)
        collision_detection.solve(query_list, gallery_list)
        assert True

    def test_precision(self):
        border = Border(0, 0, 1000, 1000)
        totol_num = 1000
        query_num = 200
        gallery_list = []
        for i in range(totol_num):
            x = random.randint(border.minx, border.maxx) + random.random()
            y = random.randint(border.miny, border.maxy) + random.random()
            gallery_list.append(BaseBall(i, position=Vector2(x, y), border=border, score=1))
        collision_detection = create_collision_detection('precision', border=border)
        query_list = random.sample(gallery_list, query_num)
        collision_detection.solve(query_list, gallery_list)
        assert True

    def test_rebuild_quadtree(self):
        border = Border(0, 0, 1000, 1000)
        totol_num = 1000
        query_num = 200
        gallery_list = []
        for i in range(totol_num):
            x = random.randint(border.minx, border.maxx) + random.random()
            y = random.randint(border.miny, border.maxy) + random.random()
            gallery_list.append(BaseBall(i, position=Vector2(x, y), border=border, score=1))
        collision_detection = create_collision_detection('rebuild_quadtree', border=border)
        query_list = random.sample(gallery_list, query_num)
        collision_detection.solve(query_list, gallery_list)
        assert True

    def test_remove_quadtree(self):
        border = Border(0, 0, 1000, 1000)
        totol_num = 1000
        query_num = 200
        change_num = 100
        gallery_list = []
        for i in range(totol_num):
            x = random.randint(border.minx, border.maxx) + random.random()
            y = random.randint(border.miny, border.maxy) + random.random()
            gallery_list.append(BaseBall(i, position=Vector2(x, y), border=border, score=1))
        collision_detection = create_collision_detection('remove_quadtree', border=border)
        collision_detection.solve([], gallery_list)
        change_list = []
        for ball in gallery_list:
            p = random.random()
            if p < change_num / totol_num:
                x = random.randint(border.minx, border.maxx) + random.random()
                y = random.randint(border.miny, border.maxy) + random.random()
                ball.postion = Vector2(x, y)
                change_list.append(ball)
        query_list = random.sample(gallery_list, query_num)
        collision_detection.solve(query_list, change_list)
        assert True

def test_exhaustive(self):
    border = Border(0, 0, 1000, 1000)
    totol_num = 1000
    query_num = 200
    gallery_list = []
    for i in range(totol_num):
        x = random.randint(border.minx, border.maxx) + random.random()
        y = random.randint(border.miny, border.maxy) + random.random()
        gallery_list.append(BaseBall(i, position=Vector2(x, y), border=border, score=1))
    collision_detection = create_collision_detection('exhaustive', border=border)
    query_list = random.sample(gallery_list, query_num)
    collision_detection.solve(query_list, gallery_list)
    assert True

def test_precision(self):
    border = Border(0, 0, 1000, 1000)
    totol_num = 1000
    query_num = 200
    gallery_list = []
    for i in range(totol_num):
        x = random.randint(border.minx, border.maxx) + random.random()
        y = random.randint(border.miny, border.maxy) + random.random()
        gallery_list.append(BaseBall(i, position=Vector2(x, y), border=border, score=1))
    collision_detection = create_collision_detection('precision', border=border)
    query_list = random.sample(gallery_list, query_num)
    collision_detection.solve(query_list, gallery_list)
    assert True

def test_rebuild_quadtree(self):
    border = Border(0, 0, 1000, 1000)
    totol_num = 1000
    query_num = 200
    gallery_list = []
    for i in range(totol_num):
        x = random.randint(border.minx, border.maxx) + random.random()
        y = random.randint(border.miny, border.maxy) + random.random()
        gallery_list.append(BaseBall(i, position=Vector2(x, y), border=border, score=1))
    collision_detection = create_collision_detection('rebuild_quadtree', border=border)
    query_list = random.sample(gallery_list, query_num)
    collision_detection.solve(query_list, gallery_list)
    assert True

def test_remove_quadtree(self):
    border = Border(0, 0, 1000, 1000)
    totol_num = 1000
    query_num = 200
    change_num = 100
    gallery_list = []
    for i in range(totol_num):
        x = random.randint(border.minx, border.maxx) + random.random()
        y = random.randint(border.miny, border.maxy) + random.random()
        gallery_list.append(BaseBall(i, position=Vector2(x, y), border=border, score=1))
    collision_detection = create_collision_detection('remove_quadtree', border=border)
    collision_detection.solve([], gallery_list)
    change_list = []
    for ball in gallery_list:
        p = random.random()
        if p < change_num / totol_num:
            x = random.randint(border.minx, border.maxx) + random.random()
            y = random.randint(border.miny, border.maxy) + random.random()
            ball.postion = Vector2(x, y)
            change_list.append(ball)
    query_list = random.sample(gallery_list, query_num)
    collision_detection.solve(query_list, change_list)
    assert True

class SpeedTest:

    def __init__(self, totol_num, border) -> None:
        self.border = border
        self.totol_num = totol_num
        self.gallery_list = []
        for i in range(totol_num):
            x = random.randint(border.minx, border.maxx) + random.random()
            y = random.randint(border.miny, border.maxy) + random.random()
            self.gallery_list.append(BaseBall(i, position=Vector2(x, y), border=border, score=1))
        self.exhaustive = create_collision_detection('exhaustive', border=border)
        self.precision = create_collision_detection('precision', border=border)
        self.rebuild_quadtree = create_collision_detection('rebuild_quadtree', border=border)
        self.remove_quadtree = create_collision_detection('remove_quadtree', border=border)

    def cal_speed(self, query_num: int, change_num: int, iters: int):
        exhustive_ava_time = 0
        precision_ava_time = 0
        rebuild_tree_ava_time = 0
        remove_tree_ava_time = 0
        self.remove_quadtree.solve([], self.gallery_list)
        for iter in range(iters):
            change_list = []
            for ball in self.gallery_list:
                p = random.random()
                if p < change_num / self.totol_num:
                    x = random.randint(self.border.minx, self.border.maxx) + random.random()
                    y = random.randint(self.border.miny, self.border.maxy) + random.random()
                    ball.postion = Vector2(x, y)
                    change_list.append(ball)
            query_list = random.sample(self.gallery_list, query_num)
            time1 = time.time()
            self.exhaustive.solve(query_list, self.gallery_list)
            time2 = time.time()
            self.precision.solve(query_list, self.gallery_list)
            time3 = time.time()
            self.rebuild_quadtree.solve(query_list, self.gallery_list)
            time4 = time.time()
            self.remove_quadtree.solve(query_list, change_list)
            time5 = time.time()
            exhustive_ava_time += time2 - time1
            precision_ava_time += time3 - time2
            rebuild_tree_ava_time += time4 - time3
            remove_tree_ava_time += time5 - time4
        exhustive_ava_time = int(round(exhustive_ava_time * 1000))
        precision_ava_time = int(round(precision_ava_time * 1000))
        rebuild_tree_ava_time = int(round(rebuild_tree_ava_time * 1000))
        remove_tree_ava_time = int(round(remove_tree_ava_time * 1000))
        return (exhustive_ava_time / iters, precision_ava_time / iters, rebuild_tree_ava_time / iters, remove_tree_ava_time / iters)

def __init__(self, totol_num, border) -> None:
    self.border = border
    self.totol_num = totol_num
    self.gallery_list = []
    for i in range(totol_num):
        x = random.randint(border.minx, border.maxx) + random.random()
        y = random.randint(border.miny, border.maxy) + random.random()
        self.gallery_list.append(BaseBall(i, position=Vector2(x, y), border=border, score=1))
    self.exhaustive = create_collision_detection('exhaustive', border=border)
    self.precision = create_collision_detection('precision', border=border)
    self.rebuild_quadtree = create_collision_detection('rebuild_quadtree', border=border)
    self.remove_quadtree = create_collision_detection('remove_quadtree', border=border)

def cal_speed(self, query_num: int, change_num: int, iters: int):
    exhustive_ava_time = 0
    precision_ava_time = 0
    rebuild_tree_ava_time = 0
    remove_tree_ava_time = 0
    self.remove_quadtree.solve([], self.gallery_list)
    for iter in range(iters):
        change_list = []
        for ball in self.gallery_list:
            p = random.random()
            if p < change_num / self.totol_num:
                x = random.randint(self.border.minx, self.border.maxx) + random.random()
                y = random.randint(self.border.miny, self.border.maxy) + random.random()
                ball.postion = Vector2(x, y)
                change_list.append(ball)
        query_list = random.sample(self.gallery_list, query_num)
        time1 = time.time()
        self.exhaustive.solve(query_list, self.gallery_list)
        time2 = time.time()
        self.precision.solve(query_list, self.gallery_list)
        time3 = time.time()
        self.rebuild_quadtree.solve(query_list, self.gallery_list)
        time4 = time.time()
        self.remove_quadtree.solve(query_list, change_list)
        time5 = time.time()
        exhustive_ava_time += time2 - time1
        precision_ava_time += time3 - time2
        rebuild_tree_ava_time += time4 - time3
        remove_tree_ava_time += time5 - time4
    exhustive_ava_time = int(round(exhustive_ava_time * 1000))
    precision_ava_time = int(round(precision_ava_time * 1000))
    rebuild_tree_ava_time = int(round(rebuild_tree_ava_time * 1000))
    remove_tree_ava_time = int(round(remove_tree_ava_time * 1000))
    return (exhustive_ava_time / iters, precision_ava_time / iters, rebuild_tree_ava_time / iters, remove_tree_ava_time / iters)

class HumanPlayer(BasePlayer):

    def __init__(self, cfg, team_id, player_id, border, spore_settings, sequence_generator=None):
        self.team_id = team_id
        self.player_id = player_id
        self.border = border
        self.balls = {}
        self.ball_settings = cfg
        self.spore_settings = spore_settings
        self.first_respawn = True
        if sequence_generator is not None:
            self.sequence_generator = sequence_generator
        else:
            self.sequence_generator = SequenceGenerator()

    def get_clone_num(self):
        """
        Overview:
            Get how many avatars the current player has
        """
        return len(self.balls)

    def get_balls(self):
        """
        Overview:
            Get all the balls of the current player
        """
        return list(self.balls.values())

    def add_balls(self, balls):
        """
        Overview:
            Add new avatars
        Parameters:
            balls <List[CloneBall] or CloneBall>: It can be a list or a single doppelganger
        """
        if isinstance(balls, list):
            for ball in balls:
                self.balls[ball.ball_id] = ball
        elif isinstance(balls, CloneBall):
            self.balls[balls.ball_id] = balls
        return True

    def move(self, direction=None, duration=0.05):
        """
        Overview:
            Move all balls controlled by the player
            The main logic is
             1. Processing stopped state
             2. If it is stopping, control all balls to move closer to the center of mass
        Parameters:
            direction <Vector2>: A point in the unit circle
            duration <float>: time
        Returns:
            position <Vector2>: position after moving 
        """
        if self.get_clone_num() == 0:
            return True
        if self.get_clone_num() == 1:
            for ball in self.balls.values():
                ball.move(given_acc=direction, duration=duration)
        elif self.get_clone_num() >= 2:
            centroid = self.cal_centroid()
            for ball in self.balls.values():
                given_acc_center = centroid - ball.position
                ball.move(given_acc=direction, given_acc_center=given_acc_center, duration=duration)
        self.score_decay()

    def score_decay(self):
        """
        Overview: 
            The player’s balls' scor will decay over time
        """
        for ball in self.balls.values():
            ball.score_decay()
        return True

    def eject(self, direction=None):
        """
        Overview:
            All clones controlled by the player perform the spore-spitting action
        Return:
            <list>: list of new spores
        """
        ret = []
        ball_ids = list(self.balls.keys())
        for ball_id in ball_ids:
            if ball_id in self.balls:
                ball = self.balls[ball_id]
                ret.append(ball.eject(direction=direction))
        return ret

    def get_keys_sort_by_balls(self):
        """
        Overview:
            Sort by ball score from largest to smallest
        Return:
            <list>: list of names
        """
        items = self.balls.items()
        backitems = [[v[1], v[0]] for v in items]
        backitems.sort(reverse=True)
        return [backitems[i][1] for i in range(0, len(backitems))]

    def split(self, direction=None):
        """
        Overview:
            All avatars controlled by the player perform splits, from large to small
        """
        balls_keys = self.get_keys_sort_by_balls()
        for k in balls_keys:
            if k in self.balls:
                ret = self.balls[k].split(self.get_clone_num(), direction=direction)
                if ret and isinstance(ret, CloneBall):
                    self.add_balls(ret)
        return True

    def eat(self, ball):
        raise NotImplementedError

    def remove_balls(self, ball):
        ball.remove()
        if ball.ball_id in self.balls:
            try:
                del self.balls[ball.ball_id]
            except:
                pass
        return True

    def respawn(self, position):
        ball_id = self.sequence_generator.get()
        if self.first_respawn:
            score = self.ball_settings.score_init
            self.first_respawn = False
        else:
            score = self.ball_settings.score_respawn
        ball = CloneBall(ball_id=ball_id, position=position, border=self.border, score=score, team_id=self.team_id, player_id=self.player_id, spore_settings=self.spore_settings, sequence_generator=self.sequence_generator, **self.ball_settings)
        direction = Vector2(1, 0)
        self.balls = {}
        self.balls[ball.ball_id] = ball
        return True

    def cal_centroid(self):
        """
        Overview:
            Calculate the centroid
        """
        x = 0
        y = 0
        total_score = 0
        for ball in self.get_balls():
            x += ball.score * ball.position.x
            y += ball.score * ball.position.y
            total_score += ball.score
        return Vector2(x, y) / total_score

    def adjust(self):
        """
        Overview:
            Adjust all the balls controlled by the player, including two parts
            1. Possible Rigid Body Collision
            2. Possible ball-ball fusion
        """
        eats = 0
        balls = self.get_balls()
        balls = sorted(balls, reverse=True)
        balls_num = len(balls)
        to_remove_balls = []
        for i in range(balls_num - 1):
            if not balls[i].is_remove:
                for j in range(i + 1, balls_num):
                    if not balls[j].is_remove:
                        dis = balls[i].get_dis(balls[j])
                        if dis < balls[i].radius + balls[j].radius:
                            if balls[i].judge_rigid(balls[j]):
                                balls[i].rigid_collision(balls[j])
                            elif dis < balls[i].radius or dis < balls[j].radius:
                                eats += 1
                                if balls[i].score > balls[j].score:
                                    balls[i].eat(balls[j])
                                    balls[j].remove()
                                    to_remove_balls.append(balls[j])
                                else:
                                    balls[j].eat(balls[i])
                                    balls[i].remove()
                                    to_remove_balls.append(balls[i])
                                balls[i].flush_frame_since_last_split()
        for ball in to_remove_balls:
            self.remove_balls(ball)
        return eats

    def get_total_score(self):
        """
            Overview: 
                Get the total score of all balls of the current player
        """
        total_score = 0
        for ball in self.get_balls():
            total_score += ball.score
        return total_score

    def get_info(self):
        total_score = 0
        can_eject = False
        can_split = False
        for ball in self.get_balls():
            total_score += ball.score
            if ball.score > self.ball_settings.eject_score_min:
                can_eject = True
            if self.get_clone_num() < self.ball_settings.part_num_max and ball.score > self.ball_settings.split_score_min:
                can_split = True
        return (total_score, can_split, can_eject)

def eject(self, direction=None):
    """
        Overview:
            All clones controlled by the player perform the spore-spitting action
        Return:
            <list>: list of new spores
        """
    ret = []
    ball_ids = list(self.balls.keys())
    for ball_id in ball_ids:
        if ball_id in self.balls:
            ball = self.balls[ball_id]
            ret.append(ball.eject(direction=direction))
    return ret

def get_keys_sort_by_balls(self):
    """
        Overview:
            Sort by ball score from largest to smallest
        Return:
            <list>: list of names
        """
    items = self.balls.items()
    backitems = [[v[1], v[0]] for v in items]
    backitems.sort(reverse=True)
    return [backitems[i][1] for i in range(0, len(backitems))]

def respawn(self, position):
    ball_id = self.sequence_generator.get()
    if self.first_respawn:
        score = self.ball_settings.score_init
        self.first_respawn = False
    else:
        score = self.ball_settings.score_respawn
    ball = CloneBall(ball_id=ball_id, position=position, border=self.border, score=score, team_id=self.team_id, player_id=self.player_id, spore_settings=self.spore_settings, sequence_generator=self.sequence_generator, **self.ball_settings)
    direction = Vector2(1, 0)
    self.balls = {}
    self.balls[ball.ball_id] = ball
    return True

def cal_centroid(self):
    """
        Overview:
            Calculate the centroid
        """
    x = 0
    y = 0
    total_score = 0
    for ball in self.get_balls():
        x += ball.score * ball.position.x
        y += ball.score * ball.position.y
        total_score += ball.score
    return Vector2(x, y) / total_score

class HumanSPPlayer(HumanPlayer):

    def __init__(self, cfg, team_id, player_id, border, spore_settings, sequence_generator=None):
        super(HumanSPPlayer, self).__init__(cfg, team_id, player_id, border, spore_settings)
        assert sequence_generator is not None
        self.sequence_generator = sequence_generator

    def move(self, ball_id=None, direction=None, duration=0.05):
        if ball_id is None:
            for ball_id, ball in self.balls.items():
                ball.move(given_acc=direction, duration=duration)
                ball.score_decay()
        elif ball_id in self.balls:
            self.balls[ball_id].move(given_acc=direction, duration=duration)
            self.balls[ball_id].score_decay()

    def eject(self, ball_id=None, direction=None):
        ret = []
        if ball_id and ball_id in self.balls:
            ret.append(self.balls[ball_id].eject(direction=direction))
        return ret

    def split(self, ball_id=None, direction=None):
        if ball_id and ball_id in self.balls:
            ret = self.balls[ball_id].split(self.get_clone_num(), direction=direction)
            if ret and isinstance(ret, CloneBall):
                self.add_balls(ret)
        return True

    def respawn(self, position):
        ball = CloneBall(ball_id=self.sequence_generator.get(), position=position, border=self.border, score=self.ball_settings.score_respawn, team_id=self.team_id, player_id=self.player_id, spore_settings=self.spore_settings, sequence_generator=self.sequence_generator, **self.ball_settings)
        self.balls = {}
        self.balls[ball.ball_id] = ball
        return True

def eject(self, ball_id=None, direction=None):
    ret = []
    if ball_id and ball_id in self.balls:
        ret.append(self.balls[ball_id].eject(direction=direction))
    return ret

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

def update_direction(self):
    if self.vel.length() != 0:
        self.direction = copy.deepcopy(self.vel.normalize())
    else:
        self.direction = Vector2(random.random(), random.random()).normalize()

@pytest.mark.unittest
class TestBaseBall:

    def test_init(self):
        border = Border(0, 0, 100, 100)
        position = Vector2(10, 10)
        ball_id = uuid.uuid1()
        base_ball = BaseBall(ball_id, position, border=border, score=6)
        assert True

    def test_judge_in_rectangle(self):
        border = Border(0, 0, 800, 800)
        position = Vector2(400, 400)
        ball_id = uuid.uuid1()
        base_ball = BaseBall(ball_id, position, border=border, score=6)
        rectangle = [300, 300, 500, 500]
        assert base_ball.judge_in_rectangle(rectangle)

    def test_move(self):
        border = Border(0, 0, 800, 800)
        position = Vector2(400, 400)
        ball_id = uuid.uuid1()
        base_ball = BaseBall(ball_id, position, border=border, score=6)
        with pytest.raises(Exception) as e:
            base_ball.move(direction=None, duration=None)

    def test_eat(self):
        border = Border(0, 0, 800, 800)
        position = Vector2(400, 400)
        ball_id = uuid.uuid1()
        base_ball = BaseBall(ball_id, position, border=border, score=6)
        with pytest.raises(Exception) as e:
            base_ball.eat(ball=None)

    def test_op_override(self):
        border = Border(0, 0, 800, 800)
        base_ball_1 = BaseBall(uuid.uuid1(), border.sample(), border=border, score=6)
        base_ball_2 = BaseBall(uuid.uuid1(), border.sample(), border=border, score=7)
        assert not base_ball_1 == base_ball_2
        assert base_ball_1 < base_ball_2
        assert not base_ball_1 > base_ball_2

def test_init(self):
    border = Border(0, 0, 100, 100)
    position = Vector2(10, 10)
    ball_id = uuid.uuid1()
    base_ball = BaseBall(ball_id, position, border=border, score=6)
    assert True

def test_judge_in_rectangle(self):
    border = Border(0, 0, 800, 800)
    position = Vector2(400, 400)
    ball_id = uuid.uuid1()
    base_ball = BaseBall(ball_id, position, border=border, score=6)
    rectangle = [300, 300, 500, 500]
    assert base_ball.judge_in_rectangle(rectangle)

def test_move(self):
    border = Border(0, 0, 800, 800)
    position = Vector2(400, 400)
    ball_id = uuid.uuid1()
    base_ball = BaseBall(ball_id, position, border=border, score=6)
    with pytest.raises(Exception) as e:
        base_ball.move(direction=None, duration=None)

class VideoPB(BasePB):

    def __init__(self, playback_settings, **kwargs):
        self.playback_settings = playback_settings
        self.fps = kwargs['fps']
        self.map_width = kwargs['map_width']
        self.map_height = kwargs['map_height']
        self.save_video = self.playback_settings.save_video
        self.save_fps = self.playback_settings.save_fps
        self.save_resolution = self.playback_settings.save_resolution
        self.save_all = self.playback_settings.save_all
        self.save_partial = self.playback_settings.save_partial
        self.save_dir = self.playback_settings.save_dir
        self.save_name_prefix = self.playback_settings.save_name_prefix
        if self.save_video:
            if not os.path.isdir(self.save_dir):
                try:
                    os.makedirs(self.save_dir)
                except:
                    pass
                logging.warning('save_dir={} must be an existed directory!'.format(self.save_dir))
            if not self.save_name_prefix:
                self.save_name_prefix = str(uuid.uuid1())
            self.save_fps = int(self.save_fps)
            self.save_resolution = int(self.save_resolution)
            self.save_freq = self.fps // self.save_fps
        self.render = EnvRender(game_screen_width=self.save_resolution, game_screen_height=self.save_resolution, map_width=self.map_width, map_height=self.map_width)
        self.screens_all = []
        self.screens_partial = []

    def get_clip_screen(self, screen_data, rectangle):
        rectangle_tmp = copy.deepcopy(rectangle)
        left_top_x, left_top_y, right_bottom_x, right_bottom_y = rectangle_tmp
        left_top_x_fix = max(left_top_x, 0)
        left_top_y_fix = max(left_top_y, 0)
        right_bottom_x_fix = min(right_bottom_x, self.width)
        right_bottom_y_fix = min(right_bottom_y, self.height)
        if len(screen_data.shape) == 3:
            screen_data_clip = screen_data[left_top_x_fix:right_bottom_x_fix, left_top_y_fix:right_bottom_y_fix, :]
            screen_data_clip = np.pad(screen_data_clip, ((left_top_x_fix - left_top_x, right_bottom_x - right_bottom_x_fix), (left_top_y_fix - left_top_y, right_bottom_y - right_bottom_y_fix), (0, 0)), mode='constant')
        elif len(screen_data.shape) == 2:
            screen_data_clip = screen_data[left_top_x_fix:right_bottom_x_fix, left_top_y_fix:right_bottom_y_fix]
            screen_data_clip = np.pad(screen_data_clip, ((left_top_x_fix - left_top_x, right_bottom_x - right_bottom_x_fix), (left_top_y_fix - left_top_y, right_bottom_y - right_bottom_y_fix)), mode='constant')
        else:
            raise NotImplementedError
        return screen_data_clip

    def need_save(self, last_frame_count, *args, **kwargs):
        return self.save_video and last_frame_count % self.save_freq == 0

    def save_step(self, food_balls, thorns_balls, spore_balls, players, player_num_per_team, *args, **kwargs):
        self.screens_all.append(self.render.get_screen(food_balls, thorns_balls, spore_balls, players, player_num_per_team))

    def save_final(self, *args, **kwargs):
        if self.save_video:
            if self.save_all:
                video_file_all = os.path.join(self.save_dir, '{}-all.mp4'.format(self.save_name_prefix))
                out = cv2.VideoWriter(video_file_all, cv2.VideoWriter_fourcc(*'mp4v'), self.save_fps, (self.screens_all[0].shape[1], self.screens_all[0].shape[0]))
                for index, screen in enumerate(self.screens_all):
                    out.write(screen)
                out.release()
                cv2.destroyAllWindows()
            if self.save_partial:
                for player_id, screens in self.screens_partial.items():
                    video_file_partial = os.path.join(self.save_dir, '{}-{:02d}.mp4'.format(self.save_name_prefix, player_id))
                    out = cv2.VideoWriter(video_file_partial, cv2.VideoWriter_fourcc(*'mp4v'), self.save_fps, (screens[0].shape[1], screens[0].shape[0]))
                    for index, screen in enumerate(self.screens):
                        if index % self.save_freq == 0:
                            out.write(screen)
                    out.release()
                    cv2.destroyAllWindows()

def get_clip_screen(self, screen_data, rectangle):
    rectangle_tmp = copy.deepcopy(rectangle)
    left_top_x, left_top_y, right_bottom_x, right_bottom_y = rectangle_tmp
    left_top_x_fix = max(left_top_x, 0)
    left_top_y_fix = max(left_top_y, 0)
    right_bottom_x_fix = min(right_bottom_x, self.width)
    right_bottom_y_fix = min(right_bottom_y, self.height)
    if len(screen_data.shape) == 3:
        screen_data_clip = screen_data[left_top_x_fix:right_bottom_x_fix, left_top_y_fix:right_bottom_y_fix, :]
        screen_data_clip = np.pad(screen_data_clip, ((left_top_x_fix - left_top_x, right_bottom_x - right_bottom_x_fix), (left_top_y_fix - left_top_y, right_bottom_y - right_bottom_y_fix), (0, 0)), mode='constant')
    elif len(screen_data.shape) == 2:
        screen_data_clip = screen_data[left_top_x_fix:right_bottom_x_fix, left_top_y_fix:right_bottom_y_fix]
        screen_data_clip = np.pad(screen_data_clip, ((left_top_x_fix - left_top_x, right_bottom_x - right_bottom_x_fix), (left_top_y_fix - left_top_y, right_bottom_y - right_bottom_y_fix)), mode='constant')
    else:
        raise NotImplementedError
    return screen_data_clip

def save_step(self, food_balls, thorns_balls, spore_balls, players, player_num_per_team, *args, **kwargs):
    self.screens_all.append(self.render.get_screen(food_balls, thorns_balls, spore_balls, players, player_num_per_team))

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

def transform_action(self, action_idx):
    return self.x_y_action_List[int(action_idx)]

class ScalarEncoder(nn.Module):

    def __init__(self, cfg):
        super(ScalarEncoder, self).__init__()
        self.whole_cfg = cfg
        self.cfg = self.whole_cfg.model.scalar_encoder
        self.encode_modules = nn.ModuleDict()
        for k, item in self.cfg.modules.items():
            if item['arc'] == 'time':
                self.encode_modules[k] = TimeEncoder(embedding_dim=item['embedding_dim'])
            elif item['arc'] == 'one_hot':
                self.encode_modules[k] = OnehotEncoder(num_embeddings=item['num_embeddings'])
            elif item['arc'] == 'binary':
                self.encode_modules[k] = BinaryEncoder(num_embeddings=item['num_embeddings'])
            elif item['arc'] == 'sign_binary':
                self.encode_modules[k] = SignBinaryEncoder(num_embeddings=item['num_embeddings'])
            else:
                print(f'cant implement {k} for arc {item['arc']}')
                raise NotImplementedError
        self.layers = MLP(in_channels=self.cfg.input_dim, hidden_channels=self.cfg.hidden_dim, out_channels=self.cfg.output_dim, layer_num=self.cfg.layer_num, layer_fn=fc_block, activation=self.cfg.activation, norm_type=self.cfg.norm_type, use_dropout=False)

    def forward(self, x: Dict[str, Tensor]):
        embeddings = []
        for key, item in self.cfg.modules.items():
            assert key in x, key
            embeddings.append(self.encode_modules[key](x[key]))
        out = torch.cat(embeddings, dim=-1)
        out = self.layers(out)
        return out

def forward(self, x: Dict[str, Tensor]):
    embeddings = []
    for key, item in self.cfg.modules.items():
        assert key in x, key
        embeddings.append(self.encode_modules[key](x[key]))
    out = torch.cat(embeddings, dim=-1)
    out = self.layers(out)
    return out

def MLP(in_channels: int, hidden_channels: int, out_channels: int, layer_num: int, layer_fn: Callable=None, activation: str=None, norm_type: str=None, use_dropout: bool=False, dropout_probability: float=0.5):
    """
    Overview:
        create a multi-layer perceptron using fully-connected blocks with activation, normalization and dropout,
        optional normalization can be done to the dim 1 (across the channels)
        x -> fc -> norm -> act -> dropout -> out
    Arguments:
        - in_channels (:obj:`int`): Number of channels in the input tensor
        - hidden_channels (:obj:`int`): Number of channels in the hidden tensor
        - out_channels (:obj:`int`): Number of channels in the output tensor
        - layer_num (:obj:`int`): Number of layers
        - layer_fn (:obj:`Callable`): layer function
        - activation (:obj:`nn.Module`): the optional activation function
        - norm_type (:obj:`str`): type of the normalization
        - use_dropout (:obj:`bool`): whether to use dropout in the fully-connected block
        - dropout_probability (:obj:`float`): probability of an element to be zeroed in the dropout. Default: 0.5
    Returns:
        - block (:obj:`nn.Sequential`): a sequential list containing the torch layers of the fully-connected block

    .. note::

        you can refer to nn.linear (https://pytorch.org/docs/master/generated/torch.nn.Linear.html)
    """
    assert layer_num >= 0, layer_num
    if layer_num == 0:
        return nn.Sequential(*[nn.Identity()])
    channels = [in_channels] + [hidden_channels] * (layer_num - 1) + [out_channels]
    if layer_fn is None:
        layer_fn = fc_block
    block = []
    for i, (in_channels, out_channels) in enumerate(zip(channels[:-1], channels[1:])):
        block.append(layer_fn(in_channels=in_channels, out_channels=out_channels, activation=activation, norm_type=norm_type, use_dropout=use_dropout, dropout_probability=dropout_probability))
    return nn.Sequential(*block)

