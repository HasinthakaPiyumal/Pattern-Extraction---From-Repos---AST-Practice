# Cluster 2

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

def obs(self, obs_type='all'):
    assert obs_type in ['all', 'single']
    global_state = self.get_global_state()
    player_states = self.player_states_util.get_player_states(food_balls=self.food_manager.get_balls(), thorns_balls=self.thorns_manager.get_balls(), spore_balls=self.spore_manager.get_balls(), players=self.player_manager.get_players())
    self.leaderboard = global_state['leaderboard']
    return (global_state, player_states, {'eats': self.eats})

def get_team_names(self):
    return self.player_manager.get_team_names()

def get_player_names_with_team(self):
    return self.player_manager.get_player_names_with_team()

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

def step(self):
    for player_id, player in self.players.items():
        if player.get_clone_num() == 0:
            player.respawn(position=self.border.sample())

def get_clone_num(self, ball):
    return self.players[ball.player_id].get_clone_num()

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

def refresh(self):
    left_num = self.cfg.num_max - len(self.balls)
    todo_num = min(math.ceil(self.cfg.refresh_percent * left_num), left_num)
    new_balls = {}
    for _ in range(todo_num):
        ball = self.spawn_ball()
        self.add_balls(ball)
        new_balls[ball.ball_id] = ball.save()
    return new_balls

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

def refresh(self):
    left_num = self.cfg.num_max - len(self.balls)
    todo_num = min(math.ceil(self.cfg.refresh_percent * left_num), left_num)
    new_balls = {}
    for _ in range(todo_num):
        ball = self.spawn_ball()
        self.add_balls(ball)
        new_balls[ball.ball_id] = ball.save()
    return new_balls

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

class SporeManager(BaseManager):

    def __init__(self, cfg, border, random_generator=None, sequence_generator=None):
        super(SporeManager, self).__init__(cfg, border)
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
        elif isinstance(balls, SporeBall):
            self.balls[balls.ball_id] = balls
        return True

    def remove_balls(self, balls):
        if isinstance(balls, list):
            for ball in balls:
                ball.remove()
                try:
                    del self.balls[ball.ball_id]
                except:
                    pass
        elif isinstance(balls, SporeBall):
            balls.remove()
            try:
                del self.balls[balls.ball_id]
            except:
                pass

    def spawn_ball(self, position=None):
        if position is None:
            position = self.border.sample()
        name = uuid.uuid1()
        return SporeBall(name=name, position=position, border=self.border, score=self.ball_settings.score_init, direction=Vector2(1, 0))

    def init_balls(self, custom_init=None):
        if custom_init is not None:
            for ball_cfg in custom_init:
                ball = self.spawn_ball(position=Vector2(*ball_cfg[:2]))
                if len(ball_cfg) > 2:
                    ball.direction = Vector2(*ball_cfg[2:4])
                    ball.vel = Vector2(*ball_cfg[4:6])
                    ball.move_frame = ball_cfg[6]
                    ball.moving = ball_cfg[7]
                    ball.owner = ball_cfg[8]
                self.balls[ball.name] = ball

    def step(self, duration):
        return

    def reset(self):
        self.balls = {}
        return True

def init_balls(self, custom_init=None):
    if custom_init is not None:
        for ball_cfg in custom_init:
            ball = self.spawn_ball(position=Vector2(*ball_cfg[:2]))
            if len(ball_cfg) > 2:
                ball.direction = Vector2(*ball_cfg[2:4])
                ball.vel = Vector2(*ball_cfg[4:6])
                ball.move_frame = ball_cfg[6]
                ball.moving = ball_cfg[7]
                ball.owner = ball_cfg[8]
            self.balls[ball.name] = ball

@pytest.mark.unittest
class TestSporeManager:

    def get_manager(self):
        cfg = Server.default_config()
        border = Border(0, 0, cfg.map_width, cfg.map_height)
        spore_manager = SporeManager(cfg=cfg.manager_settings.spore_manager, border=border)
        return spore_manager

    def get_spore_ball(self):
        ball_id = uuid.uuid1()
        border = Border(0, 0, 1000, 1000)
        position = Vector2(100, 100)
        score = SporeBall.default_config().score_init
        direction = Vector2(1, 0)
        return SporeBall(ball_id, position, border=border, score=score, direction=direction)

    def test_init(self):
        spore_manager = self.get_manager()
        assert True

    def test_get_balls(self):
        spore_manager = self.get_manager()
        for i in range(10):
            spore_manager.add_balls(self.get_spore_ball())
        spore_manager.add_balls([self.get_spore_ball(), self.get_spore_ball()])
        balls = spore_manager.get_balls()
        for i in range(10):
            logging.debug(balls[i])
        assert True

    def test_remove_balls(self):
        spore_manager = self.get_manager()
        for i in range(10):
            spore_manager.add_balls(self.get_spore_ball())
        balls = spore_manager.get_balls()
        original_len = len(balls)
        spore_manager.remove_balls(balls[:5])
        logging.debug('[SporeManager.remove_balls] init num: {}, now num {}'.format(original_len, len(spore_manager.get_balls())))
        assert True

    def test_reset(self):
        spore_manager = self.get_manager()
        for i in range(10):
            spore_manager.add_balls(self.get_spore_ball())
        balls = spore_manager.get_balls()
        spore_manager.reset()
        assert len(spore_manager.balls) == 0

def get_manager(self):
    cfg = Server.default_config()
    border = Border(0, 0, cfg.map_width, cfg.map_height)
    spore_manager = SporeManager(cfg=cfg.manager_settings.spore_manager, border=border)
    return spore_manager

def test_init(self):
    spore_manager = self.get_manager()
    assert True

def test_get_balls(self):
    spore_manager = self.get_manager()
    for i in range(10):
        spore_manager.add_balls(self.get_spore_ball())
    spore_manager.add_balls([self.get_spore_ball(), self.get_spore_ball()])
    balls = spore_manager.get_balls()
    for i in range(10):
        logging.debug(balls[i])
    assert True

def test_remove_balls(self):
    spore_manager = self.get_manager()
    for i in range(10):
        spore_manager.add_balls(self.get_spore_ball())
    balls = spore_manager.get_balls()
    original_len = len(balls)
    spore_manager.remove_balls(balls[:5])
    logging.debug('[SporeManager.remove_balls] init num: {}, now num {}'.format(original_len, len(spore_manager.get_balls())))
    assert True

def test_reset(self):
    spore_manager = self.get_manager()
    for i in range(10):
        spore_manager.add_balls(self.get_spore_ball())
    balls = spore_manager.get_balls()
    spore_manager.reset()
    assert len(spore_manager.balls) == 0

@pytest.mark.unittest
class TestFoodManager:

    def get_manager(self):
        cfg = Server.default_config()
        border = Border(0, 0, cfg.map_width, cfg.map_height)
        food_manager = FoodManager(cfg=cfg.manager_settings.food_manager, border=border)
        return food_manager

    def test_init(self):
        food_manager = self.get_manager()
        assert True

    def test_get_balls(self):
        food_manager = self.get_manager()
        food_manager.init_balls()
        balls = food_manager.get_balls()
        assert len(balls) == food_manager.cfg.num_init
        for i in range(10):
            logging.debug(balls[i])
        assert True

    def test_remove_balls(self):
        food_manager = self.get_manager()
        food_manager.init_balls()
        balls = food_manager.get_balls()
        assert len(balls) == food_manager.cfg.num_init
        food_manager.remove_balls(balls[:100])
        logging.debug('[FoodManager.remove_balls] init num: {}, now num {}'.format(food_manager.cfg.num_init, len(food_manager.get_balls())))
        assert True

    def test_step(self):
        food_manager = self.get_manager()
        food_manager.init_balls()
        balls = food_manager.get_balls()
        assert len(balls) == food_manager.cfg.num_init
        food_manager.remove_balls(balls[:100])
        logging.debug('[FoodManager.remove_balls] init num: {}, now num {}'.format(food_manager.cfg.num_init, len(food_manager.get_balls())))
        refresh_frame_freq = food_manager.cfg.refresh_frame_freq
        logging.debug('=================== test step ===================')
        for i in range(10):
            food_manager.step(duration=None)
            logging.debug('[FoodManager.step] {} food num = {}'.format(i, len(food_manager.get_balls())))

    def test_reset(self):
        food_manager = self.get_manager()
        food_manager.init_balls()
        balls = food_manager.get_balls()
        assert len(balls) == food_manager.cfg.num_init
        food_manager.reset()
        balls = food_manager.get_balls()
        assert len(balls) == 0

    def test_add_balls(self):
        to_add_list = []
        food_manager = self.get_manager()
        for _ in range(2):
            to_add_list.append(food_manager.spawn_ball())
        assert food_manager.add_balls(to_add_list)

    def test_init_balls_custom(self):
        custom_init = [[100, 100, 2]]
        food_manager = self.get_manager()
        food_manager.init_balls(custom_init)

def get_manager(self):
    cfg = Server.default_config()
    border = Border(0, 0, cfg.map_width, cfg.map_height)
    food_manager = FoodManager(cfg=cfg.manager_settings.food_manager, border=border)
    return food_manager

def test_init(self):
    food_manager = self.get_manager()
    assert True

def test_get_balls(self):
    food_manager = self.get_manager()
    food_manager.init_balls()
    balls = food_manager.get_balls()
    assert len(balls) == food_manager.cfg.num_init
    for i in range(10):
        logging.debug(balls[i])
    assert True

def test_remove_balls(self):
    food_manager = self.get_manager()
    food_manager.init_balls()
    balls = food_manager.get_balls()
    assert len(balls) == food_manager.cfg.num_init
    food_manager.remove_balls(balls[:100])
    logging.debug('[FoodManager.remove_balls] init num: {}, now num {}'.format(food_manager.cfg.num_init, len(food_manager.get_balls())))
    assert True

def test_step(self):
    food_manager = self.get_manager()
    food_manager.init_balls()
    balls = food_manager.get_balls()
    assert len(balls) == food_manager.cfg.num_init
    food_manager.remove_balls(balls[:100])
    logging.debug('[FoodManager.remove_balls] init num: {}, now num {}'.format(food_manager.cfg.num_init, len(food_manager.get_balls())))
    refresh_frame_freq = food_manager.cfg.refresh_frame_freq
    logging.debug('=================== test step ===================')
    for i in range(10):
        food_manager.step(duration=None)
        logging.debug('[FoodManager.step] {} food num = {}'.format(i, len(food_manager.get_balls())))

def test_reset(self):
    food_manager = self.get_manager()
    food_manager.init_balls()
    balls = food_manager.get_balls()
    assert len(balls) == food_manager.cfg.num_init
    food_manager.reset()
    balls = food_manager.get_balls()
    assert len(balls) == 0

def test_add_balls(self):
    to_add_list = []
    food_manager = self.get_manager()
    for _ in range(2):
        to_add_list.append(food_manager.spawn_ball())
    assert food_manager.add_balls(to_add_list)

def test_init_balls_custom(self):
    custom_init = [[100, 100, 2]]
    food_manager = self.get_manager()
    food_manager.init_balls(custom_init)

@pytest.mark.unittest
class TestPlayerManager:

    def get_manager(self):
        cfg = Server.default_config()
        border = Border(0, 0, cfg.map_width, cfg.map_height)
        player_manager = PlayerManager(cfg=cfg.manager_settings.player_manager, border=border, team_num=cfg.team_num, player_num_per_team=cfg.player_num_per_team, spore_manager_settings=cfg.manager_settings.spore_manager)
        return player_manager

    def test_init(self):
        player_manager = self.get_manager()
        assert True

    def test_init_bals(self):
        cfg = Server.default_config()
        player_manager = self.get_manager()
        player_manager.init_balls()
        assert len(player_manager.players) == cfg.team_num * cfg.player_num_per_team

    def test_get_bals(self):
        player_manager = self.get_manager()
        player_manager.init_balls()
        balls = player_manager.get_balls()
        assert isinstance(balls, list)

    def test_get_players(self):
        cfg = Server.default_config()
        player_manager = self.get_manager()
        player_manager.init_balls()
        players = player_manager.get_players()
        assert len(players) == cfg.team_num * cfg.player_num_per_team

    def test_get_player_by_name(self):
        player_manager = self.get_manager()
        player_manager.init_balls()
        players = player_manager.get_players()
        player = player_manager.get_player_by_name(players[0].player_id)
        assert isinstance(player, HumanPlayer)

    def test_add_balls(self):
        cfg = Server.default_config()
        border = Border(0, 0, cfg.map_width, cfg.map_height)
        player_manager = self.get_manager()
        player_manager.init_balls()
        players = player_manager.get_players()
        player_id = players[0].player_id
        num_old = len(player_manager.get_balls())
        ball = CloneBall('name', border.sample(), border=border, score=4, team_id=players[0].team_id, player_id=player_id)
        player_manager.add_balls(ball)
        num_new = len(player_manager.get_balls())
        assert num_new - num_old == 1
        ball1 = CloneBall('name', border.sample(), border=border, score=4, team_id=players[0].team_id, player_id=player_id)
        ball2 = CloneBall('name', border.sample(), border=border, score=4, team_id=players[0].team_id, player_id=player_id)
        balls = [ball1, ball2]
        player_manager.add_balls(balls)

    def test_remove_balls(self):
        cfg = Server.default_config()
        border = Border(0, 0, cfg.map_width, cfg.map_height)
        player_manager = self.get_manager()
        player_manager.init_balls()
        players = player_manager.get_players()
        player_id = players[0].player_id
        ball = CloneBall('name', border.sample(), border=border, score=4, team_id=players[0].team_id, player_id=player_id)
        player_manager.add_balls(ball)
        num_old = len(player_manager.get_balls())
        player_manager.remove_balls(ball)
        num_new = len(player_manager.get_balls())
        assert num_new - num_old == -1
        ball1 = CloneBall('name', border.sample(), border=border, score=4, team_id=players[0].team_id, player_id=player_id)
        ball2 = CloneBall('name', border.sample(), border=border, score=4, team_id=players[0].team_id, player_id=player_id)
        balls = [ball1, ball2]
        player_manager.remove_balls(balls)

    def test_step(self):
        cfg = Server.default_config()
        border = Border(0, 0, cfg.map_width, cfg.map_height)
        player_manager = self.get_manager()
        player_manager.init_balls()
        balls = player_manager.get_balls()
        player_manager.remove_balls(balls[0])
        num_old = len(player_manager.get_balls())
        player_manager.step()
        num_new = len(player_manager.get_balls())
        assert num_new - num_old == 1

    def test_adjust(self):
        cfg = Server.default_config()
        border = Border(0, 0, cfg.map_width, cfg.map_height)
        player_manager = self.get_manager()
        player_manager.init_balls()
        player_manager.adjust()

    def test_get_clone_num(self):
        cfg = Server.default_config()
        border = Border(0, 0, cfg.map_width, cfg.map_height)
        player_manager = self.get_manager()
        player_manager.init_balls()
        balls = player_manager.get_balls()
        assert player_manager.get_clone_num(balls[0]) == 1
        player_manager.remove_balls(balls[0])
        assert player_manager.get_clone_num(balls[0]) == 0

    def test_get_player_names(self):
        cfg = Server.default_config()
        border = Border(0, 0, cfg.map_width, cfg.map_height)
        player_manager = self.get_manager()
        player_manager.init_balls()
        player_names = player_manager.get_player_names()
        assert len(player_names) == cfg.team_num * cfg.player_num_per_team

    def test_get_team_names(self):
        cfg = Server.default_config()
        border = Border(0, 0, cfg.map_width, cfg.map_height)
        player_manager = self.get_manager()
        player_manager.init_balls()
        team_names = player_manager.get_team_names()
        assert len(team_names) == cfg.team_num

    def test_get_player_names_with_team(self):
        cfg = Server.default_config()
        border = Border(0, 0, cfg.map_width, cfg.map_height)
        player_manager = self.get_manager()
        player_manager.init_balls()
        player_names_with_team = player_manager.get_player_names_with_team()
        assert len(player_names_with_team) == cfg.team_num
        assert len(player_names_with_team[0]) == cfg.player_num_per_team

    def test_reset(self):
        cfg = Server.default_config()
        border = Border(0, 0, cfg.map_width, cfg.map_height)
        player_manager = self.get_manager()
        player_manager.init_balls()
        player_names_with_team = player_manager.get_player_names_with_team()
        assert len(player_names_with_team) == cfg.team_num
        assert len(player_names_with_team[0]) == cfg.player_num_per_team
        player_manager.reset()
        assert len(player_manager.players) == 0

def get_manager(self):
    cfg = Server.default_config()
    border = Border(0, 0, cfg.map_width, cfg.map_height)
    player_manager = PlayerManager(cfg=cfg.manager_settings.player_manager, border=border, team_num=cfg.team_num, player_num_per_team=cfg.player_num_per_team, spore_manager_settings=cfg.manager_settings.spore_manager)
    return player_manager

def test_init(self):
    player_manager = self.get_manager()
    assert True

def test_init_bals(self):
    cfg = Server.default_config()
    player_manager = self.get_manager()
    player_manager.init_balls()
    assert len(player_manager.players) == cfg.team_num * cfg.player_num_per_team

def test_get_bals(self):
    player_manager = self.get_manager()
    player_manager.init_balls()
    balls = player_manager.get_balls()
    assert isinstance(balls, list)

def test_get_players(self):
    cfg = Server.default_config()
    player_manager = self.get_manager()
    player_manager.init_balls()
    players = player_manager.get_players()
    assert len(players) == cfg.team_num * cfg.player_num_per_team

def test_get_player_by_name(self):
    player_manager = self.get_manager()
    player_manager.init_balls()
    players = player_manager.get_players()
    player = player_manager.get_player_by_name(players[0].player_id)
    assert isinstance(player, HumanPlayer)

def test_add_balls(self):
    cfg = Server.default_config()
    border = Border(0, 0, cfg.map_width, cfg.map_height)
    player_manager = self.get_manager()
    player_manager.init_balls()
    players = player_manager.get_players()
    player_id = players[0].player_id
    num_old = len(player_manager.get_balls())
    ball = CloneBall('name', border.sample(), border=border, score=4, team_id=players[0].team_id, player_id=player_id)
    player_manager.add_balls(ball)
    num_new = len(player_manager.get_balls())
    assert num_new - num_old == 1
    ball1 = CloneBall('name', border.sample(), border=border, score=4, team_id=players[0].team_id, player_id=player_id)
    ball2 = CloneBall('name', border.sample(), border=border, score=4, team_id=players[0].team_id, player_id=player_id)
    balls = [ball1, ball2]
    player_manager.add_balls(balls)

def test_remove_balls(self):
    cfg = Server.default_config()
    border = Border(0, 0, cfg.map_width, cfg.map_height)
    player_manager = self.get_manager()
    player_manager.init_balls()
    players = player_manager.get_players()
    player_id = players[0].player_id
    ball = CloneBall('name', border.sample(), border=border, score=4, team_id=players[0].team_id, player_id=player_id)
    player_manager.add_balls(ball)
    num_old = len(player_manager.get_balls())
    player_manager.remove_balls(ball)
    num_new = len(player_manager.get_balls())
    assert num_new - num_old == -1
    ball1 = CloneBall('name', border.sample(), border=border, score=4, team_id=players[0].team_id, player_id=player_id)
    ball2 = CloneBall('name', border.sample(), border=border, score=4, team_id=players[0].team_id, player_id=player_id)
    balls = [ball1, ball2]
    player_manager.remove_balls(balls)

def test_step(self):
    cfg = Server.default_config()
    border = Border(0, 0, cfg.map_width, cfg.map_height)
    player_manager = self.get_manager()
    player_manager.init_balls()
    balls = player_manager.get_balls()
    player_manager.remove_balls(balls[0])
    num_old = len(player_manager.get_balls())
    player_manager.step()
    num_new = len(player_manager.get_balls())
    assert num_new - num_old == 1

def test_adjust(self):
    cfg = Server.default_config()
    border = Border(0, 0, cfg.map_width, cfg.map_height)
    player_manager = self.get_manager()
    player_manager.init_balls()
    player_manager.adjust()

def test_get_clone_num(self):
    cfg = Server.default_config()
    border = Border(0, 0, cfg.map_width, cfg.map_height)
    player_manager = self.get_manager()
    player_manager.init_balls()
    balls = player_manager.get_balls()
    assert player_manager.get_clone_num(balls[0]) == 1
    player_manager.remove_balls(balls[0])
    assert player_manager.get_clone_num(balls[0]) == 0

def test_get_player_names(self):
    cfg = Server.default_config()
    border = Border(0, 0, cfg.map_width, cfg.map_height)
    player_manager = self.get_manager()
    player_manager.init_balls()
    player_names = player_manager.get_player_names()
    assert len(player_names) == cfg.team_num * cfg.player_num_per_team

def test_get_team_names(self):
    cfg = Server.default_config()
    border = Border(0, 0, cfg.map_width, cfg.map_height)
    player_manager = self.get_manager()
    player_manager.init_balls()
    team_names = player_manager.get_team_names()
    assert len(team_names) == cfg.team_num

def test_get_player_names_with_team(self):
    cfg = Server.default_config()
    border = Border(0, 0, cfg.map_width, cfg.map_height)
    player_manager = self.get_manager()
    player_manager.init_balls()
    player_names_with_team = player_manager.get_player_names_with_team()
    assert len(player_names_with_team) == cfg.team_num
    assert len(player_names_with_team[0]) == cfg.player_num_per_team

def test_reset(self):
    cfg = Server.default_config()
    border = Border(0, 0, cfg.map_width, cfg.map_height)
    player_manager = self.get_manager()
    player_manager.init_balls()
    player_names_with_team = player_manager.get_player_names_with_team()
    assert len(player_names_with_team) == cfg.team_num
    assert len(player_names_with_team[0]) == cfg.player_num_per_team
    player_manager.reset()
    assert len(player_manager.players) == 0

@pytest.mark.unittest
class TestPlayerManager:

    def get_manager(self):
        cfg = Server.default_config()
        border = Border(0, 0, cfg.map_width, cfg.map_height)
        player_manager = PlayerSPManager(cfg=cfg.manager_settings.player_manager, border=border, team_num=cfg.team_num, player_num_per_team=cfg.player_num_per_team, spore_manager_settings=cfg.manager_settings.spore_manager)
        return player_manager

    def test_init(self):
        player_manager = self.get_manager()
        assert True

    def test_init_bals(self):
        cfg = Server.default_config()
        player_manager = self.get_manager()
        player_manager.init_balls()
        assert len(player_manager.players) == cfg.team_num * cfg.player_num_per_team

    def test_get_bals(self):
        player_manager = self.get_manager()
        player_manager.init_balls()
        balls = player_manager.get_balls()
        assert isinstance(balls, list)

    def test_get_players(self):
        cfg = Server.default_config()
        player_manager = self.get_manager()
        player_manager.init_balls()
        players = player_manager.get_players()
        assert len(players) == cfg.team_num * cfg.player_num_per_team

    def test_get_player_by_name(self):
        player_manager = self.get_manager()
        player_manager.init_balls()
        players = player_manager.get_players()
        player = player_manager.get_player_by_name(players[0].player_id)
        assert isinstance(player, HumanSPPlayer)

    def test_add_balls(self):
        cfg = Server.default_config()
        border = Border(0, 0, cfg.map_width, cfg.map_height)
        player_manager = self.get_manager()
        player_manager.init_balls()
        players = player_manager.get_players()
        player_id = players[0].player_id
        num_old = len(player_manager.get_balls())
        ball = CloneBall(player_manager.sequence_generator.get(), border.sample(), border=border, score=4, team_id=players[0].team_id, player_id=player_id, sequence_generator=player_manager.sequence_generator)
        player_manager.add_balls(ball)
        num_new = len(player_manager.get_balls())
        assert num_new - num_old == 1
        ball1 = CloneBall(player_manager.sequence_generator.get(), border.sample(), border=border, score=4, team_id=players[0].team_id, player_id=player_id, sequence_generator=player_manager.sequence_generator)
        ball2 = CloneBall(player_manager.sequence_generator.get(), border.sample(), border=border, score=4, team_id=players[0].team_id, player_id=player_id, sequence_generator=player_manager.sequence_generator)
        balls = [ball1, ball2]
        player_manager.add_balls(balls)

    def test_remove_balls(self):
        cfg = Server.default_config()
        border = Border(0, 0, cfg.map_width, cfg.map_height)
        player_manager = self.get_manager()
        player_manager.init_balls()
        players = player_manager.get_players()
        player_id = players[0].player_id
        ball = CloneBall(player_manager.sequence_generator.get(), border.sample(), border=border, score=4, team_id=players[0].team_id, player_id=player_id, sequence_generator=player_manager.sequence_generator)
        player_manager.add_balls(ball)
        num_old = len(player_manager.get_balls())
        player_manager.remove_balls(ball)
        num_new = len(player_manager.get_balls())
        assert num_new - num_old == -1
        ball1 = CloneBall(player_manager.sequence_generator.get(), border.sample(), border=border, score=4, team_id=players[0].team_id, player_id=player_id, sequence_generator=player_manager.sequence_generator)
        ball2 = CloneBall(player_manager.sequence_generator.get(), border.sample(), border=border, score=4, team_id=players[0].team_id, player_id=player_id, sequence_generator=player_manager.sequence_generator)
        balls = [ball1, ball2]
        player_manager.remove_balls(balls)

    def test_step(self):
        cfg = Server.default_config()
        border = Border(0, 0, cfg.map_width, cfg.map_height)
        player_manager = self.get_manager()
        player_manager.init_balls()
        balls = player_manager.get_balls()
        player_manager.remove_balls(balls[0])
        num_old = len(player_manager.get_balls())
        player_manager.step()
        num_new = len(player_manager.get_balls())
        assert num_new - num_old == 1

    def test_adjust(self):
        cfg = Server.default_config()
        border = Border(0, 0, cfg.map_width, cfg.map_height)
        player_manager = self.get_manager()
        player_manager.init_balls()
        player_manager.adjust()

    def test_get_clone_num(self):
        cfg = Server.default_config()
        border = Border(0, 0, cfg.map_width, cfg.map_height)
        player_manager = self.get_manager()
        player_manager.init_balls()
        balls = player_manager.get_balls()
        assert player_manager.get_clone_num(balls[0]) == 1
        player_manager.remove_balls(balls[0])
        assert player_manager.get_clone_num(balls[0]) == 0

    def test_get_player_names(self):
        cfg = Server.default_config()
        border = Border(0, 0, cfg.map_width, cfg.map_height)
        player_manager = self.get_manager()
        player_manager.init_balls()
        player_names = player_manager.get_player_names()
        assert len(player_names) == cfg.team_num * cfg.player_num_per_team

    def test_get_team_names(self):
        cfg = Server.default_config()
        border = Border(0, 0, cfg.map_width, cfg.map_height)
        player_manager = self.get_manager()
        player_manager.init_balls()
        team_names = player_manager.get_team_names()
        assert len(team_names) == cfg.team_num

    def test_get_player_names_with_team(self):
        cfg = Server.default_config()
        border = Border(0, 0, cfg.map_width, cfg.map_height)
        player_manager = self.get_manager()
        player_manager.init_balls()
        player_names_with_team = player_manager.get_player_names_with_team()
        assert len(player_names_with_team) == cfg.team_num
        assert len(player_names_with_team[0]) == cfg.player_num_per_team

    def test_reset(self):
        cfg = Server.default_config()
        border = Border(0, 0, cfg.map_width, cfg.map_height)
        player_manager = self.get_manager()
        player_manager.init_balls()
        player_names_with_team = player_manager.get_player_names_with_team()
        assert len(player_names_with_team) == cfg.team_num
        assert len(player_names_with_team[0]) == cfg.player_num_per_team
        player_manager.reset()
        assert len(player_manager.players) == 0

def get_manager(self):
    cfg = Server.default_config()
    border = Border(0, 0, cfg.map_width, cfg.map_height)
    player_manager = PlayerSPManager(cfg=cfg.manager_settings.player_manager, border=border, team_num=cfg.team_num, player_num_per_team=cfg.player_num_per_team, spore_manager_settings=cfg.manager_settings.spore_manager)
    return player_manager

def test_init(self):
    player_manager = self.get_manager()
    assert True

def test_init_bals(self):
    cfg = Server.default_config()
    player_manager = self.get_manager()
    player_manager.init_balls()
    assert len(player_manager.players) == cfg.team_num * cfg.player_num_per_team

def test_get_bals(self):
    player_manager = self.get_manager()
    player_manager.init_balls()
    balls = player_manager.get_balls()
    assert isinstance(balls, list)

def test_get_players(self):
    cfg = Server.default_config()
    player_manager = self.get_manager()
    player_manager.init_balls()
    players = player_manager.get_players()
    assert len(players) == cfg.team_num * cfg.player_num_per_team

def test_get_player_by_name(self):
    player_manager = self.get_manager()
    player_manager.init_balls()
    players = player_manager.get_players()
    player = player_manager.get_player_by_name(players[0].player_id)
    assert isinstance(player, HumanSPPlayer)

def test_add_balls(self):
    cfg = Server.default_config()
    border = Border(0, 0, cfg.map_width, cfg.map_height)
    player_manager = self.get_manager()
    player_manager.init_balls()
    players = player_manager.get_players()
    player_id = players[0].player_id
    num_old = len(player_manager.get_balls())
    ball = CloneBall(player_manager.sequence_generator.get(), border.sample(), border=border, score=4, team_id=players[0].team_id, player_id=player_id, sequence_generator=player_manager.sequence_generator)
    player_manager.add_balls(ball)
    num_new = len(player_manager.get_balls())
    assert num_new - num_old == 1
    ball1 = CloneBall(player_manager.sequence_generator.get(), border.sample(), border=border, score=4, team_id=players[0].team_id, player_id=player_id, sequence_generator=player_manager.sequence_generator)
    ball2 = CloneBall(player_manager.sequence_generator.get(), border.sample(), border=border, score=4, team_id=players[0].team_id, player_id=player_id, sequence_generator=player_manager.sequence_generator)
    balls = [ball1, ball2]
    player_manager.add_balls(balls)

def test_remove_balls(self):
    cfg = Server.default_config()
    border = Border(0, 0, cfg.map_width, cfg.map_height)
    player_manager = self.get_manager()
    player_manager.init_balls()
    players = player_manager.get_players()
    player_id = players[0].player_id
    ball = CloneBall(player_manager.sequence_generator.get(), border.sample(), border=border, score=4, team_id=players[0].team_id, player_id=player_id, sequence_generator=player_manager.sequence_generator)
    player_manager.add_balls(ball)
    num_old = len(player_manager.get_balls())
    player_manager.remove_balls(ball)
    num_new = len(player_manager.get_balls())
    assert num_new - num_old == -1
    ball1 = CloneBall(player_manager.sequence_generator.get(), border.sample(), border=border, score=4, team_id=players[0].team_id, player_id=player_id, sequence_generator=player_manager.sequence_generator)
    ball2 = CloneBall(player_manager.sequence_generator.get(), border.sample(), border=border, score=4, team_id=players[0].team_id, player_id=player_id, sequence_generator=player_manager.sequence_generator)
    balls = [ball1, ball2]
    player_manager.remove_balls(balls)

def test_step(self):
    cfg = Server.default_config()
    border = Border(0, 0, cfg.map_width, cfg.map_height)
    player_manager = self.get_manager()
    player_manager.init_balls()
    balls = player_manager.get_balls()
    player_manager.remove_balls(balls[0])
    num_old = len(player_manager.get_balls())
    player_manager.step()
    num_new = len(player_manager.get_balls())
    assert num_new - num_old == 1

def test_adjust(self):
    cfg = Server.default_config()
    border = Border(0, 0, cfg.map_width, cfg.map_height)
    player_manager = self.get_manager()
    player_manager.init_balls()
    player_manager.adjust()

def test_get_clone_num(self):
    cfg = Server.default_config()
    border = Border(0, 0, cfg.map_width, cfg.map_height)
    player_manager = self.get_manager()
    player_manager.init_balls()
    balls = player_manager.get_balls()
    assert player_manager.get_clone_num(balls[0]) == 1
    player_manager.remove_balls(balls[0])
    assert player_manager.get_clone_num(balls[0]) == 0

def test_get_player_names(self):
    cfg = Server.default_config()
    border = Border(0, 0, cfg.map_width, cfg.map_height)
    player_manager = self.get_manager()
    player_manager.init_balls()
    player_names = player_manager.get_player_names()
    assert len(player_names) == cfg.team_num * cfg.player_num_per_team

def test_get_team_names(self):
    cfg = Server.default_config()
    border = Border(0, 0, cfg.map_width, cfg.map_height)
    player_manager = self.get_manager()
    player_manager.init_balls()
    team_names = player_manager.get_team_names()
    assert len(team_names) == cfg.team_num

def test_get_player_names_with_team(self):
    cfg = Server.default_config()
    border = Border(0, 0, cfg.map_width, cfg.map_height)
    player_manager = self.get_manager()
    player_manager.init_balls()
    player_names_with_team = player_manager.get_player_names_with_team()
    assert len(player_names_with_team) == cfg.team_num
    assert len(player_names_with_team[0]) == cfg.player_num_per_team

def test_reset(self):
    cfg = Server.default_config()
    border = Border(0, 0, cfg.map_width, cfg.map_height)
    player_manager = self.get_manager()
    player_manager.init_balls()
    player_names_with_team = player_manager.get_player_names_with_team()
    assert len(player_names_with_team) == cfg.team_num
    assert len(player_names_with_team[0]) == cfg.player_num_per_team
    player_manager.reset()
    assert len(player_manager.players) == 0

@pytest.mark.unittest
class TestBaseManager:

    def test_init(self):
        cfg = Server.default_config()
        border = Border(0, 0, 100, 100)
        base_manager = BaseManager(cfg=cfg.manager_settings.food_manager, border=border)
        assert True

    def test_others(self):
        cfg = Server.default_config()
        border = Border(0, 0, 100, 100)
        base_manager = BaseManager(cfg=cfg.manager_settings.food_manager, border=border)
        base_manager.get_balls()
        with pytest.raises(Exception) as e:
            base_manager.add_balls([])
        with pytest.raises(Exception) as e:
            base_manager.refresh()
        with pytest.raises(Exception) as e:
            base_manager.remove_balls(balls=None)
        with pytest.raises(Exception) as e:
            base_manager.spawn_ball()
        with pytest.raises(Exception) as e:
            base_manager.init_balls()
        with pytest.raises(Exception) as e:
            base_manager.step(duration=None)
        with pytest.raises(Exception) as e:
            base_manager.obs()
        with pytest.raises(Exception) as e:
            base_manager.reset()

def test_init(self):
    cfg = Server.default_config()
    border = Border(0, 0, 100, 100)
    base_manager = BaseManager(cfg=cfg.manager_settings.food_manager, border=border)
    assert True

def test_others(self):
    cfg = Server.default_config()
    border = Border(0, 0, 100, 100)
    base_manager = BaseManager(cfg=cfg.manager_settings.food_manager, border=border)
    base_manager.get_balls()
    with pytest.raises(Exception) as e:
        base_manager.add_balls([])
    with pytest.raises(Exception) as e:
        base_manager.refresh()
    with pytest.raises(Exception) as e:
        base_manager.remove_balls(balls=None)
    with pytest.raises(Exception) as e:
        base_manager.spawn_ball()
    with pytest.raises(Exception) as e:
        base_manager.init_balls()
    with pytest.raises(Exception) as e:
        base_manager.step(duration=None)
    with pytest.raises(Exception) as e:
        base_manager.obs()
    with pytest.raises(Exception) as e:
        base_manager.reset()

@pytest.mark.unittest
class TestThornsManager:

    def get_manager(self):
        cfg = Server.default_config()
        border = Border(0, 0, cfg.map_width, cfg.map_height)
        thorns_manager = ThornsManager(cfg=cfg.manager_settings.thorns_manager, border=border)
        return thorns_manager

    def test_init(self):
        thorns_manager = self.get_manager()
        assert True

    def test_get_balls(self):
        thorns_manager = self.get_manager()
        thorns_manager.init_balls()
        balls = thorns_manager.get_balls()
        assert len(balls) == thorns_manager.cfg.num_init
        for i in range(2):
            logging.debug(balls[i])
        assert True

    def test_remove_balls(self):
        thorns_manager = self.get_manager()
        thorns_manager.init_balls()
        balls = thorns_manager.get_balls()
        assert len(balls) == thorns_manager.cfg.num_init
        thorns_manager.remove_balls(balls[:20])
        logging.debug('[ThornsManager.remove_balls] init num: {}, now num {}'.format(thorns_manager.cfg.num_init, len(thorns_manager.get_balls())))
        assert True

    def test_step(self):
        thorns_manager = self.get_manager()
        thorns_manager.init_balls()
        balls = thorns_manager.get_balls()
        assert len(balls) == thorns_manager.cfg.num_init
        thorns_manager.remove_balls(balls[:20])
        logging.debug('[ThornsManager.remove_balls] init num: {}, now num {}'.format(thorns_manager.cfg.num_init, len(thorns_manager.get_balls())))
        refresh_frame_freq = thorns_manager.cfg.refresh_frame_freq
        logging.debug('=================== test step ===================')
        for i in range(20):
            thorns_manager.step(duration=None)
            logging.debug('[FoodManager.step] {} food num = {}'.format(i, len(thorns_manager.get_balls())))

    def test_reset(self):
        thorns_manager = self.get_manager()
        thorns_manager.init_balls()
        balls = thorns_manager.get_balls()
        assert len(balls) == thorns_manager.cfg.num_init
        thorns_manager.reset()
        assert len(thorns_manager.balls) == 0

    def test_add_remove_list(self):
        thorns_manager = self.get_manager()
        thorns_manager.init_balls()
        balls = thorns_manager.get_balls()
        thorns_manager.add_balls(balls)
        thorns_manager.remove_balls(balls)

def get_manager(self):
    cfg = Server.default_config()
    border = Border(0, 0, cfg.map_width, cfg.map_height)
    thorns_manager = ThornsManager(cfg=cfg.manager_settings.thorns_manager, border=border)
    return thorns_manager

def test_init(self):
    thorns_manager = self.get_manager()
    assert True

def test_get_balls(self):
    thorns_manager = self.get_manager()
    thorns_manager.init_balls()
    balls = thorns_manager.get_balls()
    assert len(balls) == thorns_manager.cfg.num_init
    for i in range(2):
        logging.debug(balls[i])
    assert True

def test_remove_balls(self):
    thorns_manager = self.get_manager()
    thorns_manager.init_balls()
    balls = thorns_manager.get_balls()
    assert len(balls) == thorns_manager.cfg.num_init
    thorns_manager.remove_balls(balls[:20])
    logging.debug('[ThornsManager.remove_balls] init num: {}, now num {}'.format(thorns_manager.cfg.num_init, len(thorns_manager.get_balls())))
    assert True

def test_step(self):
    thorns_manager = self.get_manager()
    thorns_manager.init_balls()
    balls = thorns_manager.get_balls()
    assert len(balls) == thorns_manager.cfg.num_init
    thorns_manager.remove_balls(balls[:20])
    logging.debug('[ThornsManager.remove_balls] init num: {}, now num {}'.format(thorns_manager.cfg.num_init, len(thorns_manager.get_balls())))
    refresh_frame_freq = thorns_manager.cfg.refresh_frame_freq
    logging.debug('=================== test step ===================')
    for i in range(20):
        thorns_manager.step(duration=None)
        logging.debug('[FoodManager.step] {} food num = {}'.format(i, len(thorns_manager.get_balls())))

def test_reset(self):
    thorns_manager = self.get_manager()
    thorns_manager.init_balls()
    balls = thorns_manager.get_balls()
    assert len(balls) == thorns_manager.cfg.num_init
    thorns_manager.reset()
    assert len(thorns_manager.balls) == 0

def test_add_remove_list(self):
    thorns_manager = self.get_manager()
    thorns_manager.init_balls()
    balls = thorns_manager.get_balls()
    thorns_manager.add_balls(balls)
    thorns_manager.remove_balls(balls)

@pytest.mark.unittest
class TestEnvRender:

    def test_init(self):
        render = EnvRender()
        assert True

    def test_fill_all(self):
        border = Border(0, 0, 1000, 1000)
        render = EnvRender()
        food_balls = [BaseBall('0', border.sample(), border=border, score=100)]
        thorns_balls = [BaseBall('0', border.sample(), border=border, score=10000)]
        spore_balls = [BaseBall('0', border.sample(), border=border, score=1400)]
        players = [HumanPlayer(cfg=Server.default_config().manager_settings.player_manager.ball_settings, team_id=0, player_id=0, border=border, spore_settings=Server.default_config().manager_settings.spore_manager.ball_settings)]
        screen_data_all = render.get_screen(food_balls, thorns_balls, spore_balls, players, 1)
        assert len(screen_data_all.shape) == 3

def test_fill_all(self):
    border = Border(0, 0, 1000, 1000)
    render = EnvRender()
    food_balls = [BaseBall('0', border.sample(), border=border, score=100)]
    thorns_balls = [BaseBall('0', border.sample(), border=border, score=10000)]
    spore_balls = [BaseBall('0', border.sample(), border=border, score=1400)]
    players = [HumanPlayer(cfg=Server.default_config().manager_settings.player_manager.ball_settings, team_id=0, player_id=0, border=border, spore_settings=Server.default_config().manager_settings.spore_manager.ball_settings)]
    screen_data_all = render.get_screen(food_balls, thorns_balls, spore_balls, players, 1)
    assert len(screen_data_all.shape) == 3

def method1(food_balls, cx, cy, r):
    food_count = 0
    food = len(food_balls) * [3 * [None]]
    food_radius = 2
    for ball in food_balls:
        x = ball.x
        y = ball.y
        if (x - cx) ** 2 + (y - cy) ** 2 < r ** 2:
            food[food_count] = [x, y, food_radius]
            food_count += 1
    return food[:food_count]

def chunks(arr, m):
    n = int(math.ceil(len(arr) / float(m)))
    return [arr[i:i + n] for i in range(0, len(arr), n)]

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

def get_clone_num(self):
    """
        Overview:
            Get how many avatars the current player has
        """
    return len(self.balls)

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

def get_player(self):
    cfg = Server.default_config()
    border = Border(0, 0, cfg.map_width, cfg.map_height)
    player_id = uuid.uuid1()
    return HumanSPPlayer(cfg=cfg.manager_settings.player_manager.ball_settings, team_id='0', player_id=player_id, border=border, spore_settings=cfg.manager_settings.spore_manager.ball_settings, sequence_generator=SequenceGenerator())

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

def get_player(self):
    cfg = Server.default_config()
    border = Border(0, 0, cfg.map_width, cfg.map_height)
    player_id = uuid.uuid1()
    return HumanPlayer(cfg=cfg.manager_settings.player_manager.ball_settings, team_id='0', player_id=player_id, border=border, spore_settings=cfg.manager_settings.spore_manager.ball_settings)

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

def get_clone(self, score=None):
    border = Border(0, 0, 1000, 1000)
    position = Vector2(100, 100)
    team_id = uuid.uuid1()
    ball_id = uuid.uuid1()
    score = CloneBall.default_config().score_init if score is None else score
    player_id = uuid.uuid1()
    return CloneBall(ball_id, position, border=border, score=score, team_id=team_id, player_id=player_id)

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

def test_rigid_collision_self(self):
    clone_ball = self.get_clone()
    assert clone_ball.rigid_collision(clone_ball)

