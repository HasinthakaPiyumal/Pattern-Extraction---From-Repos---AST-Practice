# Cluster 4

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

def seed(self, seed=None):
    if seed is None:
        self._seed = random.randrange(sys.maxsize)
    else:
        self._seed = seed
    self._random = random.Random(self._seed)

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

def __init__(self, cfg, border, team_num, player_num_per_team, spore_manager_settings, random_generator=None, sequence_generator=None):
    super(PlayerSPManager, self).__init__(cfg, border, team_num, player_num_per_team, spore_manager_settings, random_generator=random_generator)
    if sequence_generator is not None:
        self.sequence_generator = sequence_generator
    else:
        self.sequence_generator = SequenceGenerator()

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

def __init__(self, game_screen_width=512, game_screen_height=512, info_width=0, info_height=0, with_show=True, padding=20, map_width=128, map_height=128):
    super(RealtimeRender, self).__init__(game_screen_width=game_screen_width, game_screen_height=game_screen_height, info_width=info_width, info_height=info_height, with_show=with_show)
    self.scale_ratio_w = (self.game_screen_width - padding * 2) / map_width
    self.scale_ratio_h = (self.game_screen_height - padding * 2) / map_height
    self.padding = padding

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

def __init__(self, game_screen_width=512, game_screen_height=512, info_width=0, info_height=0, with_show=True):
    super(RealtimePartialRender, self).__init__(game_screen_width=game_screen_width, game_screen_height=game_screen_height, info_width=info_width, info_height=info_height, with_show=with_show)

class PlayButton(Button):

    def __init__(self, x, y, text, half_w=8, half_h=8):
        super(PlayButton, self).__init__(x, y, text, half_w=half_w, half_h=half_h)
        self.text_choices = ['>', '||']
        self.play = True if text == '||' else False

    def on_pressed(self):
        self.play = not self.play
        self.text = self.text_choices[int(self.play)]
        return self.play

def __init__(self, x, y, text, half_w=8, half_h=8):
    super(PlayButton, self).__init__(x, y, text, half_w=half_w, half_h=half_h)
    self.text_choices = ['>', '||']
    self.play = True if text == '||' else False

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

def __init__(self, x, y, text, half_w=8, half_h=8):
    super(SpeedButton, self).__init__(x, y, text, half_w=half_w, half_h=half_h)
    self.speed_choices = ['x1', 'x2', 'x4', 'x8']
    self.speed = 1
    self.speed_index = 0

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

def __init__(self, game_screen_width=512, game_screen_height=512, info_width=60, info_height=0, with_show=False, padding=20, map_width=256, map_height=256):
    super(EnvRender, self).__init__(game_screen_width=game_screen_width, game_screen_height=game_screen_height, info_width=info_width, info_height=info_height, with_show=with_show)
    self.scale_ratio_w = (self.game_screen_width - padding * 2) / map_width
    self.scale_ratio_h = (self.game_screen_height - padding * 2) / map_height
    self.padding = padding

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

def __init__(self, border: Border) -> None:
    super(ExhaustiveCollisionDetection, self).__init__(border=border)

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

def __init__(self, border: Border, precision: int=50) -> None:
    """
        Parameter:
            precision <int>: the precision of dividing rows
        """
    super(PrecisionCollisionDetection, self).__init__(border=border)
    self.precision = precision

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

def test_sequence_generator():

    class Temp:

        def __init__(self, sequence_generator=None):
            self.sequence_generator = sequence_generator

        def generate(self):
            return self.sequence_generator.get()
    sequence_generator = SequenceGenerator(0)
    ts = [Temp(sequence_generator) for i in range(5)]
    for index, t in enumerate(ts):
        assert t.generate() == index

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

def __init__(self, cfg, team_id, player_id, border, spore_settings, sequence_generator=None):
    super(HumanSPPlayer, self).__init__(cfg, team_id, player_id, border, spore_settings)
    assert sequence_generator is not None
    self.sequence_generator = sequence_generator

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

def __init__(self, ball_id, position, score, border, **kwargs):
    super(FoodBall, self).__init__(ball_id, position, score=score, border=border, **kwargs)
    self.check_border()

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

def __repr__(self) -> str:
    return '{}, vel_given={}, acc_given={}, frame_since_last_split={:.3f}, player_id={}, direction={}, team_id={}'.format(super().__repr__(), self.vel_given, self.acc_given, self.frame_since_last_split, self.player_id, self.direction, self.team_id)

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

class Model(nn.Module):

    def __init__(self, cfg={}, use_value_network=False):
        super(Model, self).__init__()
        self.whole_cfg = deep_merge_dicts(default_config, cfg)
        self.model_cfg = self.whole_cfg.model
        self.use_value_network = use_value_network
        self.encoder = Encoder(self.whole_cfg)
        self.policy_head = PolicyHead(self.whole_cfg)
        self.temperature = self.whole_cfg.agent.get('temperature', 1)

    def compute_action(self, obs):
        action_mask = obs.pop('action_mask', None)
        embedding = self.encoder(obs)
        logit = self.policy_head(embedding, temperature=self.temperature)
        if action_mask is not None:
            logit.masked_fill_(mask=action_mask, value=-1000000000.0)
        dist = torch.distributions.Categorical(logits=logit)
        action = dist.sample()
        return {'action': action, 'logit': logit}

def __init__(self, cfg={}, use_value_network=False):
    super(Model, self).__init__()
    self.whole_cfg = deep_merge_dicts(default_config, cfg)
    self.model_cfg = self.whole_cfg.model
    self.use_value_network = use_value_network
    self.encoder = Encoder(self.whole_cfg)
    self.policy_head = PolicyHead(self.whole_cfg)
    self.temperature = self.whole_cfg.agent.get('temperature', 1)

class PolicyHead(nn.Module):

    def __init__(self, cfg):
        super(PolicyHead, self).__init__()
        self.whole_cfg = cfg
        self.cfg = self.whole_cfg.model.policy
        self.embedding_dim = self.cfg.embedding_dim
        self.project_cfg = self.cfg.project
        self.project = fc_block(in_channels=self.project_cfg.input_dim, out_channels=self.embedding_dim, activation=self.project_cfg.activation, norm_type=self.project_cfg.norm_type)
        self.resnet_cfg = self.cfg.resnet
        blocks = [ResFCBlock(in_channels=self.embedding_dim, activation=self.resnet_cfg.activation, norm_type=self.resnet_cfg.norm_type) for _ in range(self.resnet_cfg.res_num)]
        self.resnet = nn.Sequential(*blocks)
        self.direction_num = self.whole_cfg.agent.features.get('direction_num', 12)
        self.action_num = 2 * self.direction_num + 3
        self.output_layer = fc_block(in_channels=self.embedding_dim, out_channels=self.action_num, norm_type=None, activation=None)

    def forward(self, x, temperature=1):
        x = self.project(x)
        x = self.resnet(x)
        logit = self.output_layer(x)
        logit /= temperature
        return logit

def __init__(self, cfg):
    super(PolicyHead, self).__init__()
    self.whole_cfg = cfg
    self.cfg = self.whole_cfg.model.policy
    self.embedding_dim = self.cfg.embedding_dim
    self.project_cfg = self.cfg.project
    self.project = fc_block(in_channels=self.project_cfg.input_dim, out_channels=self.embedding_dim, activation=self.project_cfg.activation, norm_type=self.project_cfg.norm_type)
    self.resnet_cfg = self.cfg.resnet
    blocks = [ResFCBlock(in_channels=self.embedding_dim, activation=self.resnet_cfg.activation, norm_type=self.resnet_cfg.norm_type) for _ in range(self.resnet_cfg.res_num)]
    self.resnet = nn.Sequential(*blocks)
    self.direction_num = self.whole_cfg.agent.features.get('direction_num', 12)
    self.action_num = 2 * self.direction_num + 3
    self.output_layer = fc_block(in_channels=self.embedding_dim, out_channels=self.action_num, norm_type=None, activation=None)

class ValueHead(nn.Module):

    def __init__(self, cfg):
        super(ValueHead, self).__init__()
        self.whole_cfg = cfg
        self.cfg = self.whole_cfg.model.value
        self.embedding_dim = self.cfg.embedding_dim
        self.project_cfg = self.cfg.project
        self.project = fc_block(in_channels=self.project_cfg.input_dim, out_channels=self.embedding_dim, activation=self.project_cfg.activation, norm_type=self.project_cfg.norm_type)
        self.resnet_cfg = self.cfg.resnet
        blocks = [ResFCBlock(in_channels=self.embedding_dim, activation=self.resnet_cfg.activation, norm_type=self.resnet_cfg.norm_type) for _ in range(self.resnet_cfg.res_num)]
        self.resnet = nn.Sequential(*blocks)
        self.output_layer = fc_block(in_channels=self.embedding_dim, out_channels=1, norm_type=None, activation=None)

    def forward(self, x):
        x = self.project(x)
        x = self.resnet(x)
        x = self.output_layer(x)
        x = x.squeeze(1)
        return x

def __init__(self, cfg):
    super(ValueHead, self).__init__()
    self.whole_cfg = cfg
    self.cfg = self.whole_cfg.model.value
    self.embedding_dim = self.cfg.embedding_dim
    self.project_cfg = self.cfg.project
    self.project = fc_block(in_channels=self.project_cfg.input_dim, out_channels=self.embedding_dim, activation=self.project_cfg.activation, norm_type=self.project_cfg.norm_type)
    self.resnet_cfg = self.cfg.resnet
    blocks = [ResFCBlock(in_channels=self.embedding_dim, activation=self.resnet_cfg.activation, norm_type=self.resnet_cfg.norm_type) for _ in range(self.resnet_cfg.res_num)]
    self.resnet = nn.Sequential(*blocks)
    self.output_layer = fc_block(in_channels=self.embedding_dim, out_channels=1, norm_type=None, activation=None)

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

class TeamEncoder(nn.Module):

    def __init__(self, cfg):
        super(TeamEncoder, self).__init__()
        self.whole_cfg = cfg
        self.cfg = self.whole_cfg.model.team_encoder
        self.encode_modules = nn.ModuleDict()
        for k, item in self.cfg.modules.items():
            if item['arc'] == 'one_hot':
                self.encode_modules[k] = OnehotEncoder(num_embeddings=item['num_embeddings'])
            elif item['arc'] == 'binary':
                self.encode_modules[k] = BinaryEncoder(num_embeddings=item['num_embeddings'])
            elif item['arc'] == 'sign_binary':
                self.encode_modules[k] = SignBinaryEncoder(num_embeddings=item['num_embeddings'])
            else:
                print(f'cant implement {k} for arc {item['arc']}')
                raise NotImplementedError
        self.embedding_dim = self.cfg.embedding_dim
        self.encoder_cfg = self.cfg.encoder
        self.encode_layers = MLP(in_channels=self.encoder_cfg.input_dim, hidden_channels=self.encoder_cfg.hidden_dim, out_channels=self.embedding_dim, layer_num=self.encoder_cfg.layer_num, layer_fn=fc_block, activation=self.encoder_cfg.activation, norm_type=self.encoder_cfg.norm_type, use_dropout=False)
        self.transformer_cfg = self.cfg.transformer
        self.transformer = Transformer(n_heads=self.transformer_cfg.head_num, embedding_size=self.embedding_dim, ffn_size=self.transformer_cfg.ffn_size, n_layers=self.transformer_cfg.layer_num, attention_dropout=0.0, relu_dropout=0.0, dropout=0.0, activation=self.transformer_cfg.activation, variant=self.transformer_cfg.variant)
        self.output_cfg = self.cfg.output
        self.output_fc = fc_block(self.embedding_dim, self.output_cfg.output_dim, norm_type=self.output_cfg.norm_type, activation=self.output_cfg.activation)

    def forward(self, x):
        embeddings = []
        player_num = x['player_num']
        mask = sequence_mask(player_num, max_len=x['view_x'].shape[1])
        for key, item in self.cfg.modules.items():
            assert key in x, f'{key} not implemented'
            x_input = x[key]
            embeddings.append(self.encode_modules[key](x_input))
        x = torch.cat(embeddings, dim=-1)
        x = self.encode_layers(x)
        x = self.transformer(x, mask=mask)
        team_info = self.output_fc(x.sum(dim=1) / player_num.unsqueeze(dim=-1))
        return team_info

def __init__(self, cfg):
    super(TeamEncoder, self).__init__()
    self.whole_cfg = cfg
    self.cfg = self.whole_cfg.model.team_encoder
    self.encode_modules = nn.ModuleDict()
    for k, item in self.cfg.modules.items():
        if item['arc'] == 'one_hot':
            self.encode_modules[k] = OnehotEncoder(num_embeddings=item['num_embeddings'])
        elif item['arc'] == 'binary':
            self.encode_modules[k] = BinaryEncoder(num_embeddings=item['num_embeddings'])
        elif item['arc'] == 'sign_binary':
            self.encode_modules[k] = SignBinaryEncoder(num_embeddings=item['num_embeddings'])
        else:
            print(f'cant implement {k} for arc {item['arc']}')
            raise NotImplementedError
    self.embedding_dim = self.cfg.embedding_dim
    self.encoder_cfg = self.cfg.encoder
    self.encode_layers = MLP(in_channels=self.encoder_cfg.input_dim, hidden_channels=self.encoder_cfg.hidden_dim, out_channels=self.embedding_dim, layer_num=self.encoder_cfg.layer_num, layer_fn=fc_block, activation=self.encoder_cfg.activation, norm_type=self.encoder_cfg.norm_type, use_dropout=False)
    self.transformer_cfg = self.cfg.transformer
    self.transformer = Transformer(n_heads=self.transformer_cfg.head_num, embedding_size=self.embedding_dim, ffn_size=self.transformer_cfg.ffn_size, n_layers=self.transformer_cfg.layer_num, attention_dropout=0.0, relu_dropout=0.0, dropout=0.0, activation=self.transformer_cfg.activation, variant=self.transformer_cfg.variant)
    self.output_cfg = self.cfg.output
    self.output_fc = fc_block(self.embedding_dim, self.output_cfg.output_dim, norm_type=self.output_cfg.norm_type, activation=self.output_cfg.activation)

class BallEncoder(nn.Module):

    def __init__(self, cfg):
        super(BallEncoder, self).__init__()
        self.whole_cfg = cfg
        self.cfg = self.whole_cfg.model.ball_encoder
        self.encode_modules = nn.ModuleDict()
        for k, item in self.cfg.modules.items():
            if item['arc'] == 'one_hot':
                self.encode_modules[k] = OnehotEncoder(num_embeddings=item['num_embeddings'])
            elif item['arc'] == 'binary':
                self.encode_modules[k] = BinaryEncoder(num_embeddings=item['num_embeddings'])
            elif item['arc'] == 'sign_binary':
                self.encode_modules[k] = SignBinaryEncoder(num_embeddings=item['num_embeddings'])
            elif item['arc'] == 'unsqueeze':
                self.encode_modules[k] = UnsqueezeEncoder()
            else:
                print(f'cant implement {k} for arc {item['arc']}')
                raise NotImplementedError
        self.embedding_dim = self.cfg.embedding_dim
        self.encoder_cfg = self.cfg.encoder
        self.encode_layers = MLP(in_channels=self.encoder_cfg.input_dim, hidden_channels=self.encoder_cfg.hidden_dim, out_channels=self.embedding_dim, layer_num=self.encoder_cfg.layer_num, layer_fn=fc_block, activation=self.encoder_cfg.activation, norm_type=self.encoder_cfg.norm_type, use_dropout=False)
        self.transformer_cfg = self.cfg.transformer
        self.transformer = Transformer(n_heads=self.transformer_cfg.head_num, embedding_size=self.embedding_dim, ffn_size=self.transformer_cfg.ffn_size, n_layers=self.transformer_cfg.layer_num, attention_dropout=0.0, relu_dropout=0.0, dropout=0.0, activation=self.transformer_cfg.activation, variant=self.transformer_cfg.variant)
        self.output_cfg = self.cfg.output
        self.output_fc = fc_block(self.embedding_dim, self.output_cfg.output_dim, norm_type=self.output_cfg.norm_type, activation=self.output_cfg.activation)

    def forward(self, x):
        ball_num = x['ball_num']
        embeddings = []
        mask = sequence_mask(ball_num, max_len=x['x'].shape[1])
        for key, item in self.cfg.modules.items():
            assert key in x, key
            x_input = x[key]
            embeddings.append(self.encode_modules[key](x_input))
        x = torch.cat(embeddings, dim=-1)
        x = self.encode_layers(x)
        x = self.transformer(x, mask=mask)
        ball_info = x.sum(dim=1) / ball_num.unsqueeze(dim=-1)
        ball_info = self.output_fc(ball_info)
        return (x, ball_info)

def __init__(self, cfg):
    super(BallEncoder, self).__init__()
    self.whole_cfg = cfg
    self.cfg = self.whole_cfg.model.ball_encoder
    self.encode_modules = nn.ModuleDict()
    for k, item in self.cfg.modules.items():
        if item['arc'] == 'one_hot':
            self.encode_modules[k] = OnehotEncoder(num_embeddings=item['num_embeddings'])
        elif item['arc'] == 'binary':
            self.encode_modules[k] = BinaryEncoder(num_embeddings=item['num_embeddings'])
        elif item['arc'] == 'sign_binary':
            self.encode_modules[k] = SignBinaryEncoder(num_embeddings=item['num_embeddings'])
        elif item['arc'] == 'unsqueeze':
            self.encode_modules[k] = UnsqueezeEncoder()
        else:
            print(f'cant implement {k} for arc {item['arc']}')
            raise NotImplementedError
    self.embedding_dim = self.cfg.embedding_dim
    self.encoder_cfg = self.cfg.encoder
    self.encode_layers = MLP(in_channels=self.encoder_cfg.input_dim, hidden_channels=self.encoder_cfg.hidden_dim, out_channels=self.embedding_dim, layer_num=self.encoder_cfg.layer_num, layer_fn=fc_block, activation=self.encoder_cfg.activation, norm_type=self.encoder_cfg.norm_type, use_dropout=False)
    self.transformer_cfg = self.cfg.transformer
    self.transformer = Transformer(n_heads=self.transformer_cfg.head_num, embedding_size=self.embedding_dim, ffn_size=self.transformer_cfg.ffn_size, n_layers=self.transformer_cfg.layer_num, attention_dropout=0.0, relu_dropout=0.0, dropout=0.0, activation=self.transformer_cfg.activation, variant=self.transformer_cfg.variant)
    self.output_cfg = self.cfg.output
    self.output_fc = fc_block(self.embedding_dim, self.output_cfg.output_dim, norm_type=self.output_cfg.norm_type, activation=self.output_cfg.activation)

class SpatialEncoder(nn.Module):

    def __init__(self, cfg):
        super(SpatialEncoder, self).__init__()
        self.whole_cfg = cfg
        self.cfg = self.whole_cfg.model.spatial_encoder
        self.spatial_x = 64
        self.spatial_y = 64
        self.scatter_cfg = self.cfg.scatter
        self.scatter_fc = fc_block(in_channels=self.scatter_cfg.input_dim, out_channels=self.scatter_cfg.output_dim, activation=self.scatter_cfg.activation, norm_type=self.scatter_cfg.norm_type)
        self.scatter_connection = ScatterConnection(self.scatter_cfg.scatter_type)
        self.resnet_cfg = self.cfg.resnet
        self.get_resnet_blocks()
        self.output_cfg = self.cfg.output
        self.output_fc = fc_block(in_channels=self.spatial_x // 8 * self.spatial_y // 8 * self.resnet_cfg.down_channels[-1], out_channels=self.output_cfg.output_dim, norm_type=self.output_cfg.norm_type, activation=self.output_cfg.activation)

    def get_resnet_blocks(self):
        project = conv2d_block(in_channels=self.scatter_cfg.output_dim + 2, out_channels=self.resnet_cfg.project_dim, kernel_size=1, stride=1, padding=0, activation=self.resnet_cfg.activation, norm_type=self.resnet_cfg.norm_type, bias=False)
        layers = [project]
        dims = [self.resnet_cfg.project_dim] + self.resnet_cfg.down_channels
        for i in range(len(dims) - 1):
            layer = conv2d_block(in_channels=dims[i], out_channels=dims[i + 1], kernel_size=4, stride=2, padding=1, activation=self.resnet_cfg.activation, norm_type=self.resnet_cfg.norm_type, bias=False)
            layers.append(layer)
            layers.append(ResBlock(in_channels=dims[i + 1], activation=self.resnet_cfg.activation, norm_type=self.resnet_cfg.norm_type))
        self.resnet = torch.nn.Sequential(*layers)

    def get_background_embedding(self, coord_x, coord_y, num):
        background_ones = torch.ones(size=(coord_x.shape[0], coord_x.shape[1]), device=coord_x.device)
        background_mask = sequence_mask(num, max_len=coord_x.shape[1])
        background_ones = (background_ones * background_mask).unsqueeze(-1)
        background_embedding = self.scatter_connection.xy_forward(background_ones, spatial_size=[self.spatial_x, self.spatial_y], coord_x=coord_x, coord_y=coord_y)
        return background_embedding

    def forward(self, inputs, ball_embeddings):
        spatial_info = inputs['spatial_info']
        food_embedding = self.get_background_embedding(coord_x=spatial_info['food_x'], coord_y=spatial_info['food_y'], num=spatial_info['food_num'])
        spore_embedding = self.get_background_embedding(coord_x=spatial_info['spore_x'], coord_y=spatial_info['spore_y'], num=spatial_info['spore_num'])
        ball_info = inputs['ball_info']
        ball_num = ball_info['ball_num']
        ball_mask = sequence_mask(ball_num, max_len=ball_embeddings.shape[1])
        ball_embedding = self.scatter_fc(ball_embeddings) * ball_mask.unsqueeze(dim=2)
        ball_embedding = self.scatter_connection.xy_forward(ball_embedding, spatial_size=[self.spatial_x, self.spatial_y], coord_x=spatial_info['ball_x'], coord_y=spatial_info['ball_y'])
        x = torch.cat([food_embedding, spore_embedding, ball_embedding], dim=1)
        x = self.resnet(x)
        x = torch.flatten(x, start_dim=1, end_dim=-1)
        x = self.output_fc(x)
        return x

def __init__(self, cfg):
    super(SpatialEncoder, self).__init__()
    self.whole_cfg = cfg
    self.cfg = self.whole_cfg.model.spatial_encoder
    self.spatial_x = 64
    self.spatial_y = 64
    self.scatter_cfg = self.cfg.scatter
    self.scatter_fc = fc_block(in_channels=self.scatter_cfg.input_dim, out_channels=self.scatter_cfg.output_dim, activation=self.scatter_cfg.activation, norm_type=self.scatter_cfg.norm_type)
    self.scatter_connection = ScatterConnection(self.scatter_cfg.scatter_type)
    self.resnet_cfg = self.cfg.resnet
    self.get_resnet_blocks()
    self.output_cfg = self.cfg.output
    self.output_fc = fc_block(in_channels=self.spatial_x // 8 * self.spatial_y // 8 * self.resnet_cfg.down_channels[-1], out_channels=self.output_cfg.output_dim, norm_type=self.output_cfg.norm_type, activation=self.output_cfg.activation)

def get_resnet_blocks(self):
    project = conv2d_block(in_channels=self.scatter_cfg.output_dim + 2, out_channels=self.resnet_cfg.project_dim, kernel_size=1, stride=1, padding=0, activation=self.resnet_cfg.activation, norm_type=self.resnet_cfg.norm_type, bias=False)
    layers = [project]
    dims = [self.resnet_cfg.project_dim] + self.resnet_cfg.down_channels
    for i in range(len(dims) - 1):
        layer = conv2d_block(in_channels=dims[i], out_channels=dims[i + 1], kernel_size=4, stride=2, padding=1, activation=self.resnet_cfg.activation, norm_type=self.resnet_cfg.norm_type, bias=False)
        layers.append(layer)
        layers.append(ResBlock(in_channels=dims[i + 1], activation=self.resnet_cfg.activation, norm_type=self.resnet_cfg.norm_type))
    self.resnet = torch.nn.Sequential(*layers)

class Encoder(nn.Module):

    def __init__(self, cfg):
        super(Encoder, self).__init__()
        self.whole_cfg = cfg
        self.scalar_encoder = ScalarEncoder(cfg)
        self.team_encoder = TeamEncoder(cfg)
        self.ball_encoder = BallEncoder(cfg)
        self.spatial_encoder = SpatialEncoder(cfg)

    def forward(self, x):
        scalar_info = self.scalar_encoder(x['scalar_info'])
        team_info = self.team_encoder(x['team_info'])
        ball_embeddings, ball_info = self.ball_encoder(x['ball_info'])
        spatial_info = self.spatial_encoder(x, ball_embeddings)
        x = torch.cat([scalar_info, team_info, ball_info, spatial_info], dim=1)
        return x

def __init__(self, cfg):
    super(Encoder, self).__init__()
    self.whole_cfg = cfg
    self.scalar_encoder = ScalarEncoder(cfg)
    self.team_encoder = TeamEncoder(cfg)
    self.ball_encoder = BallEncoder(cfg)
    self.spatial_encoder = SpatialEncoder(cfg)

class LSTM(nn.Module, LSTMForwardWrapper):
    """
    Overview:
        Implimentation of LSTM cell

        .. note::
            for begainners, you can reference <https://zhuanlan.zhihu.com/p/32085405> to learn the basics about lstm

    Interface:
        __init__, forward
    """

    def __init__(self, input_size, hidden_size, num_layers, norm_type=None, dropout=0.0):
        """
        Overview:
            initializate the LSTM cell

        Arguments:
            - input_size (:obj:`int`): size of the input vector
            - hidden_size (:obj:`int`): size of the hidden state vector
            - num_layers (:obj:`int`): number of lstm layers
            - norm_type (:obj:`str`): type of the normaliztion, (default: None)
            - dropout (:obj:float):  dropout rate, default set to .0
        """
        super(LSTM, self).__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        norm_func = build_normalization(norm_type)
        self.norm = nn.ModuleList([norm_func(hidden_size * 4) for _ in range(2 * num_layers)])
        self.wx = nn.ParameterList()
        self.wh = nn.ParameterList()
        dims = [input_size] + [hidden_size] * num_layers
        for l in range(num_layers):
            self.wx.append(nn.Parameter(torch.zeros(dims[l], dims[l + 1] * 4)))
            self.wh.append(nn.Parameter(torch.zeros(hidden_size, hidden_size * 4)))
        self.bias = nn.Parameter(torch.zeros(num_layers, hidden_size * 4))
        self.use_dropout = dropout > 0.0
        if self.use_dropout:
            self.dropout = nn.Dropout(dropout)
        self._init()

    def _init(self):
        gain = math.sqrt(1.0 / self.hidden_size)
        for l in range(self.num_layers):
            torch.nn.init.uniform_(self.wx[l], -gain, gain)
            torch.nn.init.uniform_(self.wh[l], -gain, gain)
            if self.bias is not None:
                torch.nn.init.uniform_(self.bias[l], -gain, gain)

    def forward(self, inputs, prev_state, list_next_state=True):
        """
        Overview:
            Take the previous state and the input and calculate the output and the nextstate
        Arguments:
            - inputs (:obj:`tensor`): input vector of cell, tensor of size [seq_len, batch_size, input_size]
            - prev_state (:obj:`tensor`): None or tensor of size [num_directions*num_layers, batch_size, hidden_size]
            - list_next_state (:obj:`bool`): whether return next_state with list format, default set to False
        Returns:
            - x (:obj:`tensor`): output from lstm
            - next_state (:obj:`tensor` or :obj:`list`): hidden state from lstm
        """
        seq_len, batch_size = inputs.shape[:2]
        prev_state = self._before_forward(inputs, prev_state)
        H, C = prev_state
        x = inputs
        next_state = []
        for l in range(self.num_layers):
            h, c = (H[l], C[l])
            new_x = []
            for s in range(seq_len):
                gate = self.norm[l * 2](torch.matmul(x[s], self.wx[l])) + self.norm[l * 2 + 1](torch.matmul(h, self.wh[l]))
                if self.bias is not None:
                    gate += self.bias[l]
                gate = list(torch.chunk(gate, 4, dim=1))
                i, f, o, u = gate
                i = torch.sigmoid(i)
                f = torch.sigmoid(f)
                o = torch.sigmoid(o)
                u = torch.tanh(u)
                c = f * c + i * u
                h = o * torch.tanh(c)
                new_x.append(h)
            next_state.append((h, c))
            x = torch.stack(new_x, dim=0)
            if self.use_dropout and l != self.num_layers - 1:
                x = self.dropout(x)
        next_state = self._after_forward(next_state, list_next_state)
        return (x, next_state)

def __init__(self, input_size, hidden_size, num_layers, norm_type=None, dropout=0.0):
    """
        Overview:
            initializate the LSTM cell

        Arguments:
            - input_size (:obj:`int`): size of the input vector
            - hidden_size (:obj:`int`): size of the hidden state vector
            - num_layers (:obj:`int`): number of lstm layers
            - norm_type (:obj:`str`): type of the normaliztion, (default: None)
            - dropout (:obj:float):  dropout rate, default set to .0
        """
    super(LSTM, self).__init__()
    self.input_size = input_size
    self.hidden_size = hidden_size
    self.num_layers = num_layers
    norm_func = build_normalization(norm_type)
    self.norm = nn.ModuleList([norm_func(hidden_size * 4) for _ in range(2 * num_layers)])
    self.wx = nn.ParameterList()
    self.wh = nn.ParameterList()
    dims = [input_size] + [hidden_size] * num_layers
    for l in range(num_layers):
        self.wx.append(nn.Parameter(torch.zeros(dims[l], dims[l + 1] * 4)))
        self.wh.append(nn.Parameter(torch.zeros(hidden_size, hidden_size * 4)))
    self.bias = nn.Parameter(torch.zeros(num_layers, hidden_size * 4))
    self.use_dropout = dropout > 0.0
    if self.use_dropout:
        self.dropout = nn.Dropout(dropout)
    self._init()

class SoftArgmax(nn.Module):
    """
    Overview:
        a nn.Module that computes SoftArgmax

        Note:
            for more softargmax info, you can reference the wiki page
            <https://wikimili.com/en/Softmax_function> or reference the lecture
            <https://mc.ai/softmax-function-beyond-the-basics/>

    Interface:
        __init__, forward
    """

    def __init__(self):
        """
        Overview:
            initialize the SoftArgmax module
        """
        super(SoftArgmax, self).__init__()

    def forward(self, x):
        """
        Overview:
            soft-argmax for location regression

        Arguments:
            - x (:obj:`Tensor`): predict heat map

        Returns:
            - location (:obj:`Tensor`): predict location

        Shapes:
            - x (:obj:`Tensor`): :math:`(B, C, H, W)`, while B is the batch size,
                C is number of channels , H and W stands for height and width
            - location (:obj:`Tensor`): :math:`(B, 2)`, while B is the batch size
        """
        B, C, H, W = x.shape
        device, dtype = (x.device, x.dtype)
        assert x.shape[1] == 1
        h_kernel = torch.arange(0, H, device=device).to(dtype)
        h_kernel = h_kernel.view(1, 1, H, 1).repeat(1, 1, 1, W)
        w_kernel = torch.arange(0, W, device=device).to(dtype)
        w_kernel = w_kernel.view(1, 1, 1, W).repeat(1, 1, H, 1)
        x = F.softmax(x.view(B, C, -1), dim=-1).view(B, C, H, W)
        h = (x * h_kernel).sum(dim=[1, 2, 3])
        w = (x * w_kernel).sum(dim=[1, 2, 3])
        return torch.stack([h, w], dim=1)

def __init__(self):
    """
        Overview:
            initialize the SoftArgmax module
        """
    super(SoftArgmax, self).__init__()

class ResBlock(nn.Module):
    """
    Overview:
        Residual Block with 2D convolution layers, including 2 types:
            basic block:
                input channel: C
                x -> 3*3*C -> norm -> act -> 3*3*C -> norm -> act -> out
                \\__________________________________________/+
            bottleneck block:
                x -> 1*1*(1/4*C) -> norm -> act -> 3*3*(1/4*C) -> norm -> act -> 1*1*C -> norm -> act -> out
                \\_____________________________________________________________________________/+

    Interface:
        __init__, forward
    """

    def __init__(self, in_channels, out_channels=None, stride=1, downsample=None, activation='relu', norm_type='LN'):
        """
        Overview:
            Init the Residual Block

        Arguments:
            - in_channels (:obj:`int`): Number of channels in the input tensor
            - activation (:obj:`nn.Module`): the optional activation function
            - norm_type (:obj:`str`): type of the normalization, defalut set to batch normalization,
                                      support ['BN', 'IN', 'SyncBN', None]
            - res_type (:obj:`str`): type of residual block, support ['basic', 'bottleneck'], see overview for details
        """
        super(ResBlock, self).__init__()
        self.in_channels = in_channels
        self.out_channels = self.in_channels if out_channels is None else out_channels
        self.activation_type = activation
        self.norm_type = norm_type
        self.stride = stride
        self.downsample = downsample
        self.conv1 = conv2d_block(in_channels=self.in_channels, out_channels=self.out_channels, kernel_size=3, stride=self.stride, padding=1, activation=self.activation_type, norm_type=self.norm_type)
        self.conv2 = conv2d_block(in_channels=self.out_channels, out_channels=self.out_channels, kernel_size=3, stride=self.stride, padding=1, activation=None, norm_type=self.norm_type)
        self.activation = build_activation(self.activation_type)

    def forward(self, x):
        """
        Overview:
            return the redisual block output

        Arguments:
            - x (:obj:`tensor`): the input tensor

        Returns:
            - x(:obj:`tensor`): the resblock output tensor
        """
        residual = x
        out = self.conv1(x)
        out = self.conv2(out)
        if self.downsample is not None:
            residual = self.downsample(x)
        out += residual
        out = self.activation(out)
        return out

def __init__(self, in_channels, out_channels=None, stride=1, downsample=None, activation='relu', norm_type='LN'):
    """
        Overview:
            Init the Residual Block

        Arguments:
            - in_channels (:obj:`int`): Number of channels in the input tensor
            - activation (:obj:`nn.Module`): the optional activation function
            - norm_type (:obj:`str`): type of the normalization, defalut set to batch normalization,
                                      support ['BN', 'IN', 'SyncBN', None]
            - res_type (:obj:`str`): type of residual block, support ['basic', 'bottleneck'], see overview for details
        """
    super(ResBlock, self).__init__()
    self.in_channels = in_channels
    self.out_channels = self.in_channels if out_channels is None else out_channels
    self.activation_type = activation
    self.norm_type = norm_type
    self.stride = stride
    self.downsample = downsample
    self.conv1 = conv2d_block(in_channels=self.in_channels, out_channels=self.out_channels, kernel_size=3, stride=self.stride, padding=1, activation=self.activation_type, norm_type=self.norm_type)
    self.conv2 = conv2d_block(in_channels=self.out_channels, out_channels=self.out_channels, kernel_size=3, stride=self.stride, padding=1, activation=None, norm_type=self.norm_type)
    self.activation = build_activation(self.activation_type)

class ResBlock2(nn.Module):
    """
    Overview:
        Residual Block with 2D convolution layers, including 2 types:
            basic block:
                input channel: C
                x -> 3*3*C -> norm -> act -> 3*3*C -> norm -> act -> out
                \\__________________________________________/+
            bottleneck block:
                x -> 1*1*(1/4*C) -> norm -> act -> 3*3*(1/4*C) -> norm -> act -> 1*1*C -> norm -> act -> out
                \\_____________________________________________________________________________/+

    Interface:
        __init__, forward
    """

    def __init__(self, in_channels, out_channels=None, stride=1, downsample=None, activation='relu', norm_type='LN'):
        """
        Overview:
            Init the Residual Block

        Arguments:
            - in_channels (:obj:`int`): Number of channels in the input tensor
            - activation (:obj:`nn.Module`): the optional activation function
            - norm_type (:obj:`str`): type of the normalization, defalut set to batch normalization,
                                      support ['BN', 'IN', 'SyncBN', None]
            - res_type (:obj:`str`): type of residual block, support ['basic', 'bottleneck'], see overview for details
        """
        super(ResBlock2, self).__init__()
        self.in_channels = in_channels
        self.out_channels = self.in_channels if out_channels is None else out_channels
        self.activation_type = activation
        self.norm_type = norm_type
        self.stride = stride
        self.downsample = downsample
        self.conv1 = conv2d_block2(in_channels=self.in_channels, out_channels=self.out_channels, kernel_size=3, stride=self.stride, padding=1, activation=self.activation_type, norm_type=self.norm_type)
        self.conv2 = conv2d_block2(in_channels=self.out_channels, out_channels=self.out_channels, kernel_size=3, stride=self.stride, padding=1, activation=self.activation_type, norm_type=self.norm_type)
        self.activation = build_activation(self.activation_type)

    def forward(self, x):
        """
        Overview:
            return the redisual block output

        Arguments:
            - x (:obj:`tensor`): the input tensor

        Returns:
            - x(:obj:`tensor`): the resblock output tensor
        """
        residual = x
        out = self.conv1(x)
        out = self.conv2(out)
        if self.downsample is not None:
            residual = self.downsample(x)
        out += residual
        return x

def __init__(self, in_channels, out_channels=None, stride=1, downsample=None, activation='relu', norm_type='LN'):
    """
        Overview:
            Init the Residual Block

        Arguments:
            - in_channels (:obj:`int`): Number of channels in the input tensor
            - activation (:obj:`nn.Module`): the optional activation function
            - norm_type (:obj:`str`): type of the normalization, defalut set to batch normalization,
                                      support ['BN', 'IN', 'SyncBN', None]
            - res_type (:obj:`str`): type of residual block, support ['basic', 'bottleneck'], see overview for details
        """
    super(ResBlock2, self).__init__()
    self.in_channels = in_channels
    self.out_channels = self.in_channels if out_channels is None else out_channels
    self.activation_type = activation
    self.norm_type = norm_type
    self.stride = stride
    self.downsample = downsample
    self.conv1 = conv2d_block2(in_channels=self.in_channels, out_channels=self.out_channels, kernel_size=3, stride=self.stride, padding=1, activation=self.activation_type, norm_type=self.norm_type)
    self.conv2 = conv2d_block2(in_channels=self.out_channels, out_channels=self.out_channels, kernel_size=3, stride=self.stride, padding=1, activation=self.activation_type, norm_type=self.norm_type)
    self.activation = build_activation(self.activation_type)

class ResFCBlock(nn.Module):

    def __init__(self, in_channels, activation='relu', norm_type=None):
        """
        Overview:
            Init the Residual Block

        Arguments:
            - activation (:obj:`nn.Module`): the optional activation function
            - norm_type (:obj:`str`): type of the normalization, defalut set to batch normalization
        """
        super(ResFCBlock, self).__init__()
        self.activation_type = activation
        self.norm_type = norm_type
        self.fc1 = fc_block(in_channels, in_channels, norm_type=self.norm_type, activation=self.activation_type)
        self.fc2 = fc_block(in_channels, in_channels, norm_type=self.norm_type, activation=None)
        self.activation = build_activation(self.activation_type)

    def forward(self, x):
        """
        Overview:
            return  output of  the residual block with 2 fully connected block

        Arguments:
            - x (:obj:`tensor`): the input tensor

        Returns:
            - x(:obj:`tensor`): the resblock output tensor
        """
        residual = x
        x = self.fc1(x)
        x = self.fc2(x)
        x = self.activation(x + residual)
        return x

def __init__(self, in_channels, activation='relu', norm_type=None):
    """
        Overview:
            Init the Residual Block

        Arguments:
            - activation (:obj:`nn.Module`): the optional activation function
            - norm_type (:obj:`str`): type of the normalization, defalut set to batch normalization
        """
    super(ResFCBlock, self).__init__()
    self.activation_type = activation
    self.norm_type = norm_type
    self.fc1 = fc_block(in_channels, in_channels, norm_type=self.norm_type, activation=self.activation_type)
    self.fc2 = fc_block(in_channels, in_channels, norm_type=self.norm_type, activation=None)
    self.activation = build_activation(self.activation_type)

class ResFCBlock2(nn.Module):
    """
    Overview:
        Residual Block with 2 fully connected block
        x -> fc1 -> norm -> act -> fc2 -> norm -> act -> out
        \\_____________________________________/+

    Interface:
        __init__, forward
    """

    def __init__(self, in_channels, activation='relu', norm_type='LN'):
        """
        Overview:
            Init the Residual Block

        Arguments:
            - activation (:obj:`nn.Module`): the optional activation function
            - norm_type (:obj:`str`): type of the normalization, defalut set to batch normalization
        """
        super(ResFCBlock2, self).__init__()
        self.activation_type = activation
        self.fc1 = fc_block2(in_channels, in_channels, activation=self.activation_type, norm_type=norm_type)
        self.fc2 = fc_block2(in_channels, in_channels, activation=self.activation_type, norm_type=norm_type)

    def forward(self, x):
        """
        Overview:
            return  output of  the residual block with 2 fully connected block

        Arguments:
            - x (:obj:`tensor`): the input tensor

        Returns:
            - x(:obj:`tensor`): the resblock output tensor
        """
        residual = x
        x = self.fc1(x)
        x = self.fc2(x)
        x = x + residual
        return x

def __init__(self, in_channels, activation='relu', norm_type='LN'):
    """
        Overview:
            Init the Residual Block

        Arguments:
            - activation (:obj:`nn.Module`): the optional activation function
            - norm_type (:obj:`str`): type of the normalization, defalut set to batch normalization
        """
    super(ResFCBlock2, self).__init__()
    self.activation_type = activation
    self.fc1 = fc_block2(in_channels, in_channels, activation=self.activation_type, norm_type=norm_type)
    self.fc2 = fc_block2(in_channels, in_channels, activation=self.activation_type, norm_type=norm_type)

class MultiHeadAttention(nn.Module):
    """
    Overview:
        For each entry embedding, compute individual attention across all entries, add them up to get output attention
    """

    def __init__(self, n_heads: int=None, dim: int=None, dropout: float=0):
        """
        Overview:
            Init attention
        Arguments:
            - input_dim (:obj:`int`): dimension of input
            - head_dim (:obj:`int`): dimension of each head
            - output_dim (:obj:`int`): dimension of output
            - head_num (:obj:`int`): head num for multihead attention
            - dropout (:obj:`nn.Module`): dropout layer
        """
        super(MultiHeadAttention, self).__init__()
        self.n_heads = n_heads
        self.dim = dim
        self.attn_dropout = nn.Dropout(p=dropout)
        self.q_lin = nn.Linear(dim, dim)
        self.k_lin = nn.Linear(dim, dim)
        self.v_lin = nn.Linear(dim, dim)
        nn.init.xavier_normal_(self.q_lin.weight)
        nn.init.xavier_normal_(self.k_lin.weight)
        nn.init.xavier_normal_(self.v_lin.weight)
        self.out_lin = nn.Linear(dim, dim)
        nn.init.xavier_normal_(self.out_lin.weight)

    def split(self, x, T=False):
        """
        Overview:
            Split input to get multihead queries, keys, values
        Arguments:
            - x (:obj:`tensor`): query or key or value
            - T (:obj:`bool`): whether to transpose output
        Returns:
            - x (:obj:`list`): list of output tensors for each head
        """
        B, N = x.shape[:2]
        x = x.view(B, N, self.head_num, self.head_dim)
        x = x.permute(0, 2, 1, 3).contiguous()
        if T:
            x = x.permute(0, 1, 3, 2).contiguous()
        return x

    def forward(self, query: torch.Tensor, key: Optional[torch.Tensor]=None, value: Optional[torch.Tensor]=None, mask: torch.Tensor=None) -> Tuple[torch.Tensor, Dict[str, torch.Tensor], torch.Tensor]:
        batch_size, query_len, dim = query.size()
        assert dim == self.dim, 'Dimensions do not match: {} query vs {} configured'.format(dim, self.dim)
        assert mask is not None, 'Mask is None, please specify a mask'
        n_heads = self.n_heads
        dim_per_head = dim // n_heads
        scale = math.sqrt(dim_per_head)

        def prepare_head(tensor):
            bsz, seq_len, _ = tensor.size()
            tensor = tensor.view(batch_size, tensor.size(1), n_heads, dim_per_head)
            tensor = tensor.transpose(1, 2).contiguous().view(batch_size * n_heads, seq_len, dim_per_head)
            return tensor
        if key is None and value is None:
            key = value = query
            _, _key_len, dim = query.size()
        elif value is None:
            value = key
        assert key is not None
        _, _key_len, dim = key.size()
        q = prepare_head(self.q_lin(query))
        k = prepare_head(self.k_lin(key))
        v = prepare_head(self.v_lin(value))
        full_key_len = k.size(1)
        dot_prod = q.div_(scale).bmm(k.transpose(1, 2))
        attn_mask = (mask == 0).view(batch_size, 1, -1, full_key_len).repeat(1, n_heads, 1, 1).expand(batch_size, n_heads, query_len, full_key_len).view(batch_size * n_heads, query_len, full_key_len)
        assert attn_mask.shape == dot_prod.shape
        dot_prod.masked_fill_(attn_mask, neginf(dot_prod.dtype))
        attn_weights = F.softmax(dot_prod, dim=-1, dtype=torch.float).type_as(query)
        attn_weights = self.attn_dropout(attn_weights)
        attentioned = attn_weights.bmm(v)
        attentioned = attentioned.type_as(query).view(batch_size, n_heads, query_len, dim_per_head).transpose(1, 2).contiguous().view(batch_size, query_len, dim)
        out = self.out_lin(attentioned)
        return (out, dot_prod)

def __init__(self, n_heads: int=None, dim: int=None, dropout: float=0):
    """
        Overview:
            Init attention
        Arguments:
            - input_dim (:obj:`int`): dimension of input
            - head_dim (:obj:`int`): dimension of each head
            - output_dim (:obj:`int`): dimension of output
            - head_num (:obj:`int`): head num for multihead attention
            - dropout (:obj:`nn.Module`): dropout layer
        """
    super(MultiHeadAttention, self).__init__()
    self.n_heads = n_heads
    self.dim = dim
    self.attn_dropout = nn.Dropout(p=dropout)
    self.q_lin = nn.Linear(dim, dim)
    self.k_lin = nn.Linear(dim, dim)
    self.v_lin = nn.Linear(dim, dim)
    nn.init.xavier_normal_(self.q_lin.weight)
    nn.init.xavier_normal_(self.k_lin.weight)
    nn.init.xavier_normal_(self.v_lin.weight)
    self.out_lin = nn.Linear(dim, dim)
    nn.init.xavier_normal_(self.out_lin.weight)

class TransformerFFN(nn.Module):
    """
    Implements the FFN part of the transformer.
    """

    def __init__(self, dim: int=None, dim_hidden: int=None, dropout: float=0, activation: str='relu', **kwargs):
        super(TransformerFFN, self).__init__(**kwargs)
        self.dim = dim
        self.dim_hidden = dim_hidden
        self.dropout_ratio = dropout
        self.relu_dropout = nn.Dropout(p=self.dropout_ratio)
        if activation == 'relu':
            self.nonlinear = F.relu
        elif activation == 'gelu':
            self.nonlinear = F.gelu
        else:
            raise ValueError("Don't know how to handle --activation {}".format(activation))
        self.lin1 = nn.Linear(self.dim, self.dim_hidden)
        self.lin2 = nn.Linear(self.dim_hidden, self.dim)
        nn.init.xavier_uniform_(self.lin1.weight)
        nn.init.xavier_uniform_(self.lin2.weight)

    def forward(self, x: torch.Tensor, **kwargs) -> torch.Tensor:
        """
        Forward pass.
        """
        x = self.nonlinear(self.lin1(x))
        x = self.relu_dropout(x)
        x = self.lin2(x)
        return x

def __init__(self, dim: int=None, dim_hidden: int=None, dropout: float=0, activation: str='relu', **kwargs):
    super(TransformerFFN, self).__init__(**kwargs)
    self.dim = dim
    self.dim_hidden = dim_hidden
    self.dropout_ratio = dropout
    self.relu_dropout = nn.Dropout(p=self.dropout_ratio)
    if activation == 'relu':
        self.nonlinear = F.relu
    elif activation == 'gelu':
        self.nonlinear = F.gelu
    else:
        raise ValueError("Don't know how to handle --activation {}".format(activation))
    self.lin1 = nn.Linear(self.dim, self.dim_hidden)
    self.lin2 = nn.Linear(self.dim_hidden, self.dim)
    nn.init.xavier_uniform_(self.lin1.weight)
    nn.init.xavier_uniform_(self.lin2.weight)

class TransformerLayer(nn.Module):
    """
    Overview:
        In transformer layer, first computes entries's attention and applies a feedforward layer
    """

    def __init__(self, n_heads: int=None, embedding_size: int=None, ffn_size: int=None, attention_dropout: float=0.0, relu_dropout: float=0.0, dropout: float=0.0, activation: str='relu', variant: Optional[str]=None):
        """
        Overview:
            Init transformer layer
        Arguments:
            - input_dim (:obj:`int`): dimension of input
            - head_dim (:obj:`int`): dimension of each head
            - hidden_dim (:obj:`int`): dimension of hidden layer in mlp
            - output_dim (:obj:`int`): dimension of output
            - head_num (:obj:`int`): number of heads for multihead attention
            - mlp_num (:obj:`int`): number of mlp layers
            - dropout (:obj:`nn.Module`): dropout layer
            - activation (:obj:`nn.Module`): activation function
        """
        super(TransformerLayer, self).__init__()
        self.n_heads = n_heads
        self.dim = embedding_size
        self.ffn_dim = ffn_size
        self.activation = activation
        self.variant = variant
        self.attention = MultiHeadAttention(n_heads=self.n_heads, dim=embedding_size, dropout=attention_dropout)
        self.norm1 = torch.nn.LayerNorm(embedding_size, eps=LAYER_NORM_EPS)
        self.ffn = TransformerFFN(dim=embedding_size, dim_hidden=ffn_size, dropout=relu_dropout, activation=activation)
        self.norm2 = torch.nn.LayerNorm(embedding_size, eps=LAYER_NORM_EPS)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x, mask):
        """
        Overview:
            transformer layer forward
        Arguments:
            - inputs (:obj:`tuple`): x and mask
        Returns:
            - output (:obj:`tuple`): x and mask
        """
        residual = x
        if self.variant == 'prenorm':
            x = self.norm1(x)
        attended_tensor = self.attention(x, mask=mask)[0]
        x = residual + self.dropout(attended_tensor)
        if self.variant == 'postnorm':
            x = self.norm1(x)
        residual = x
        if self.variant == 'prenorm':
            x = self.norm2(x)
        x = residual + self.dropout(self.ffn(x))
        if self.variant == 'postnorm':
            x = self.norm2(x)
        x *= mask.unsqueeze(-1).type_as(x)
        return x

def __init__(self, n_heads: int=None, embedding_size: int=None, ffn_size: int=None, attention_dropout: float=0.0, relu_dropout: float=0.0, dropout: float=0.0, activation: str='relu', variant: Optional[str]=None):
    """
        Overview:
            Init transformer layer
        Arguments:
            - input_dim (:obj:`int`): dimension of input
            - head_dim (:obj:`int`): dimension of each head
            - hidden_dim (:obj:`int`): dimension of hidden layer in mlp
            - output_dim (:obj:`int`): dimension of output
            - head_num (:obj:`int`): number of heads for multihead attention
            - mlp_num (:obj:`int`): number of mlp layers
            - dropout (:obj:`nn.Module`): dropout layer
            - activation (:obj:`nn.Module`): activation function
        """
    super(TransformerLayer, self).__init__()
    self.n_heads = n_heads
    self.dim = embedding_size
    self.ffn_dim = ffn_size
    self.activation = activation
    self.variant = variant
    self.attention = MultiHeadAttention(n_heads=self.n_heads, dim=embedding_size, dropout=attention_dropout)
    self.norm1 = torch.nn.LayerNorm(embedding_size, eps=LAYER_NORM_EPS)
    self.ffn = TransformerFFN(dim=embedding_size, dim_hidden=ffn_size, dropout=relu_dropout, activation=activation)
    self.norm2 = torch.nn.LayerNorm(embedding_size, eps=LAYER_NORM_EPS)
    self.dropout = nn.Dropout(dropout)

class Transformer(nn.Module):
    """
    Overview:
        Transformer implementation

        Note:
            For details refer to Attention is all you need: http://arxiv.org/abs/1706.03762
    """

    def __init__(self, n_heads=8, embedding_size: int=128, ffn_size: int=128, n_layers: int=3, attention_dropout: float=0.0, relu_dropout: float=0.0, dropout: float=0.0, activation: Optional[str]='relu', variant: Optional[str]='prenorm'):
        """
        Overview:
            Init transformer
        Arguments:
            - input_dim (:obj:`int`): dimension of input
            - head_dim (:obj:`int`): dimension of each head
            - hidden_dim (:obj:`int`): dimension of hidden layer in mlp
            - output_dim (:obj:`int`): dimension of output
            - head_num (:obj:`int`): number of heads for multihead attention
            - mlp_num (:obj:`int`): number of mlp layers
            - layer_num (:obj:`int`): number of transformer layers
            - dropout_ratio (:obj:`float`): dropout ratio
            - activation (:obj:`nn.Module`): activation function
        """
        super(Transformer, self).__init__()
        self.n_heads = n_heads
        self.dim = embedding_size
        self.ffn_size = ffn_size
        self.n_layers = n_layers
        self.dropout_ratio = dropout
        self.attention_dropout = attention_dropout
        self.relu_dropout = relu_dropout
        self.activation = activation
        self.variant = variant
        self.layers = self.build_layers()
        self.norm_embedding = torch.nn.LayerNorm(self.dim, eps=LAYER_NORM_EPS)

    def build_layers(self) -> nn.ModuleList:
        layers = nn.ModuleList()
        for _ in range(self.n_layers):
            layer = TransformerLayer(n_heads=self.n_heads, embedding_size=self.dim, ffn_size=self.ffn_size, attention_dropout=self.attention_dropout, relu_dropout=self.relu_dropout, dropout=self.dropout_ratio, variant=self.variant, activation=self.activation)
            layers.append(layer)
        return layers

    def forward(self, x, mask=None):
        """
        Overview:
            Transformer forward
        Arguments:
            - x (:obj:`tensor`): input tensor, shape (B, N, C), B is batch size, N is number of entries,
                C is feature dimension
            - mask (:obj:`tensor` or :obj:`None`): bool tensor, can be used to mask out invalid entries in attention,
                shape (B, N), B is batch size, N is number of entries
        Returns:
            - x (:obj:`tensor`): transformer output
        """
        if self.variant == 'postnorm':
            x = self.norm_embedding(x)
        if mask is not None:
            x *= mask.unsqueeze(-1).type_as(x)
        else:
            mask = torch.ones(size=x.shape[:2], dtype=torch.bool, device=x.device)
        if self.variant == 'postnorm':
            x = self.norm_embedding(x)
        for i in range(self.n_layers):
            x = self.layers[i](x, mask)
        if self.variant == 'prenorm':
            x = self.norm_embedding(x)
        return x

def __init__(self, n_heads=8, embedding_size: int=128, ffn_size: int=128, n_layers: int=3, attention_dropout: float=0.0, relu_dropout: float=0.0, dropout: float=0.0, activation: Optional[str]='relu', variant: Optional[str]='prenorm'):
    """
        Overview:
            Init transformer
        Arguments:
            - input_dim (:obj:`int`): dimension of input
            - head_dim (:obj:`int`): dimension of each head
            - hidden_dim (:obj:`int`): dimension of hidden layer in mlp
            - output_dim (:obj:`int`): dimension of output
            - head_num (:obj:`int`): number of heads for multihead attention
            - mlp_num (:obj:`int`): number of mlp layers
            - layer_num (:obj:`int`): number of transformer layers
            - dropout_ratio (:obj:`float`): dropout ratio
            - activation (:obj:`nn.Module`): activation function
        """
    super(Transformer, self).__init__()
    self.n_heads = n_heads
    self.dim = embedding_size
    self.ffn_size = ffn_size
    self.n_layers = n_layers
    self.dropout_ratio = dropout
    self.attention_dropout = attention_dropout
    self.relu_dropout = relu_dropout
    self.activation = activation
    self.variant = variant
    self.layers = self.build_layers()
    self.norm_embedding = torch.nn.LayerNorm(self.dim, eps=LAYER_NORM_EPS)

def build_layers(self) -> nn.ModuleList:
    layers = nn.ModuleList()
    for _ in range(self.n_layers):
        layer = TransformerLayer(n_heads=self.n_heads, embedding_size=self.dim, ffn_size=self.ffn_size, attention_dropout=self.attention_dropout, relu_dropout=self.relu_dropout, dropout=self.dropout_ratio, variant=self.variant, activation=self.activation)
        layers.append(layer)
    return layers

class GLU(nn.Module):
    """
    Overview:
        Gating Linear Unit.
        This class does a thing like this:

        .. code:: python

            # Inputs: input, context, output_size
            # The gate value is a learnt function of the input.
            gate = sigmoid(linear(input.size)(context))
            # Gate the input and return an output of desired size.
            gated_input = gate * input
            output = linear(output_size)(gated_input)
            return output
    Interfaces:
        forward

    .. tip::

        This module also supports 2D convolution, in which case, the input and context must have the same shape.
    """

    def __init__(self, input_dim: int, output_dim: int, context_dim: int, input_type: str='fc') -> None:
        """
        Overview:
            Init GLU
        Arguments:
            - input_dim (:obj:`int`): the input dimension
            - output_dim (:obj:`int`): the output dimension
            - context_dim (:obj:`int`): the context dimension
            - input_type (:obj:`str`): the type of input, now support ['fc', 'conv2d']
        """
        super(GLU, self).__init__()
        assert input_type in ['fc', 'conv2d']
        if input_type == 'fc':
            self.layer1 = nn.Linear(context_dim, input_dim)
            self.layer2 = nn.Linear(input_dim, output_dim)
        elif input_type == 'conv2d':
            self.layer1 = nn.Conv2d(context_dim, input_dim, 1, 1, 0)
            self.layer2 = nn.Conv2d(input_dim, output_dim, 1, 1, 0)

    def forward(self, x: torch.Tensor, context: torch.Tensor) -> torch.Tensor:
        """
        Overview:
            Return GLU computed tensor
        Arguments:
            - x (:obj:`torch.Tensor`) : the input tensor
            - context (:obj:`torch.Tensor`) : the context tensor
        Returns:
            - x (:obj:`torch.Tensor`): the computed tensor
        """
        gate = self.layer1(context)
        gate = torch.sigmoid(gate)
        x = gate * x
        x = self.layer2(x)
        return x

def __init__(self, input_dim: int, output_dim: int, context_dim: int, input_type: str='fc') -> None:
    """
        Overview:
            Init GLU
        Arguments:
            - input_dim (:obj:`int`): the input dimension
            - output_dim (:obj:`int`): the output dimension
            - context_dim (:obj:`int`): the context dimension
            - input_type (:obj:`str`): the type of input, now support ['fc', 'conv2d']
        """
    super(GLU, self).__init__()
    assert input_type in ['fc', 'conv2d']
    if input_type == 'fc':
        self.layer1 = nn.Linear(context_dim, input_dim)
        self.layer2 = nn.Linear(input_dim, output_dim)
    elif input_type == 'conv2d':
        self.layer1 = nn.Conv2d(context_dim, input_dim, 1, 1, 0)
        self.layer2 = nn.Conv2d(input_dim, output_dim, 1, 1, 0)

class Swish(nn.Module):

    def __init__(self):
        super(Swish, self).__init__()

    def forward(self, x):
        x = x * torch.sigmoid(x)
        return x

def __init__(self):
    super(Swish, self).__init__()

class ScatterConnection(nn.Module):
    """
        Overview:
            Scatter feature to its corresponding location
            In alphastar, each entity is embedded into a tensor, these tensors are scattered into a feature map
            with map size
    """

    def __init__(self, scatter_type='add') -> None:
        """
            Overview:
                Init class
            Arguments:
                - scatter_type (:obj:`str`): add or cover, if two entities have same location, scatter type decides the
                    first one should be covered or added to second one
        """
        super(ScatterConnection, self).__init__()
        self.scatter_type = scatter_type
        assert self.scatter_type in ['cover', 'add']

    def xy_forward(self, x: torch.Tensor, spatial_size: Tuple[int, int], coord_x: torch.Tensor, coord_y) -> torch.Tensor:
        device = x.device
        BatchSize, Num, EmbeddingSize = x.shape
        x = x.permute(0, 2, 1)
        H, W = spatial_size
        indices = (coord_x * W + coord_y).long()
        indices = indices.unsqueeze(dim=1).repeat(1, EmbeddingSize, 1)
        output = torch.zeros(size=(BatchSize, EmbeddingSize, H, W), device=device).view(BatchSize, EmbeddingSize, H * W)
        if self.scatter_type == 'cover':
            output.scatter_(dim=2, index=indices, src=x)
        elif self.scatter_type == 'add':
            output.scatter_add_(dim=2, index=indices, src=x)
        output = output.view(BatchSize, EmbeddingSize, H, W)
        return output

    def forward(self, x: torch.Tensor, spatial_size: Tuple[int, int], location: torch.Tensor) -> torch.Tensor:
        """
            Overview:
                scatter x into a spatial feature map
            Arguments:
                - x (:obj:`tensor`): input tensor :math: `(B, M, N)` where `M` means the number of entity, `N` means                  the dimension of entity attributes
                - spatial_size (:obj:`tuple`): Tuple[H, W], the size of spatial feature x will be scattered into
                - location (:obj:`tensor`): :math: `(B, M, 2)` torch.LongTensor, each location should be (y, x)
            Returns:
                - output (:obj:`tensor`): :math: `(B, N, H, W)` where `H` and `W` are spatial_size, return the                    scattered feature map
            Shapes:
                - Input: :math: `(B, M, N)` where `M` means the number of entity, `N` means                  the dimension of entity attributes
                - Size: Tuple[H, W]
                - Location: :math: `(B, M, 2)` torch.LongTensor, each location should be (y, x)
                - Output: :math: `(B, N, H, W)` where `H` and `W` are spatial_size

            .. note::
                when there are some overlapping in locations, ``cover`` mode will result in the loss of information, we
                use the addition as temporal substitute.
        """
        device = x.device
        BatchSize, Num, EmbeddingSize = x.shape
        x = x.permute(0, 2, 1)
        H, W = spatial_size
        indices = location[:, :, 1] + location[:, :, 0] * W
        indices = indices.unsqueeze(dim=1).repeat(1, EmbeddingSize, 1)
        output = torch.zeros(size=(BatchSize, EmbeddingSize, H, W), device=device).view(BatchSize, EmbeddingSize, H * W)
        if self.scatter_type == 'cover':
            output.scatter_(dim=2, index=indices, src=x)
        elif self.scatter_type == 'add':
            output.scatter_add_(dim=2, index=indices, src=x)
        output = output.view(BatchSize, EmbeddingSize, H, W)
        return output

def __init__(self, scatter_type='add') -> None:
    """
            Overview:
                Init class
            Arguments:
                - scatter_type (:obj:`str`): add or cover, if two entities have same location, scatter type decides the
                    first one should be covered or added to second one
        """
    super(ScatterConnection, self).__init__()
    self.scatter_type = scatter_type
    assert self.scatter_type in ['cover', 'add']

class OnehotEncoder(nn.Module):

    def __init__(self, num_embeddings: int):
        super(OnehotEncoder, self).__init__()
        self.num_embeddings = num_embeddings
        self.main = nn.Embedding.from_pretrained(torch.eye(self.num_embeddings), freeze=True, padding_idx=None)

    def forward(self, x: torch.Tensor):
        x = x.long().clamp_(max=self.num_embeddings - 1)
        return self.main(x)

def __init__(self, num_embeddings: int):
    super(OnehotEncoder, self).__init__()
    self.num_embeddings = num_embeddings
    self.main = nn.Embedding.from_pretrained(torch.eye(self.num_embeddings), freeze=True, padding_idx=None)

class OnehotEmbedding(nn.Module):

    def __init__(self, num_embeddings: int, embedding_dim: int):
        super(OnehotEmbedding, self).__init__()
        self.num_embeddings = num_embeddings
        self.embedding_dim = embedding_dim
        self.main = nn.Embedding(num_embeddings=self.num_embeddings, embedding_dim=self.embedding_dim)

    def forward(self, x: torch.Tensor):
        x = x.long().clamp_(max=self.num_embeddings - 1)
        return self.main(x)

def __init__(self, num_embeddings: int, embedding_dim: int):
    super(OnehotEmbedding, self).__init__()
    self.num_embeddings = num_embeddings
    self.embedding_dim = embedding_dim
    self.main = nn.Embedding(num_embeddings=self.num_embeddings, embedding_dim=self.embedding_dim)

class BinaryEncoder(nn.Module):

    def __init__(self, num_embeddings: int):
        super(BinaryEncoder, self).__init__()
        self.bit_num = num_embeddings
        self.main = nn.Embedding.from_pretrained(self.get_binary_embed_matrix(self.bit_num), freeze=True, padding_idx=None)

    @staticmethod
    def get_binary_embed_matrix(bit_num):
        embedding_matrix = []
        for n in range(2 ** bit_num):
            embedding = [n >> d & 1 for d in range(bit_num)][::-1]
            embedding_matrix.append(embedding)
        return torch.tensor(embedding_matrix, dtype=torch.float)

    def forward(self, x: torch.Tensor):
        x = x.long().clamp_(max=2 ** self.bit_num - 1)
        return self.main(x)

def __init__(self, num_embeddings: int):
    super(BinaryEncoder, self).__init__()
    self.bit_num = num_embeddings
    self.main = nn.Embedding.from_pretrained(self.get_binary_embed_matrix(self.bit_num), freeze=True, padding_idx=None)

class SignBinaryEncoder(nn.Module):

    def __init__(self, num_embeddings):
        super(SignBinaryEncoder, self).__init__()
        self.bit_num = num_embeddings
        self.main = nn.Embedding.from_pretrained(self.get_sign_binary_matrix(self.bit_num), freeze=True, padding_idx=None)
        self.max_val = 2 ** (self.bit_num - 1) - 1

    @staticmethod
    def get_sign_binary_matrix(bit_num):
        neg_embedding_matrix = []
        pos_embedding_matrix = []
        for n in range(1, 2 ** (bit_num - 1)):
            embedding = [n >> d & 1 for d in range(bit_num - 1)][::-1]
            neg_embedding_matrix.append([1] + embedding)
            pos_embedding_matrix.append([0] + embedding)
        embedding_matrix = neg_embedding_matrix[::-1] + [[0 for _ in range(bit_num)]] + pos_embedding_matrix
        return torch.tensor(embedding_matrix, dtype=torch.float)

    def forward(self, x: torch.Tensor):
        x = x.long().clamp_(max=self.max_val, min=-self.max_val)
        return self.main(x + self.max_val)

def __init__(self, num_embeddings):
    super(SignBinaryEncoder, self).__init__()
    self.bit_num = num_embeddings
    self.main = nn.Embedding.from_pretrained(self.get_sign_binary_matrix(self.bit_num), freeze=True, padding_idx=None)
    self.max_val = 2 ** (self.bit_num - 1) - 1

class PositionEncoder(nn.Module):

    def __init__(self, num_embeddings, embedding_dim=None):
        super(PositionEncoder, self).__init__()
        self.n_position = num_embeddings
        self.embedding_dim = self.n_position if embedding_dim is None else embedding_dim
        self.position_enc = nn.Embedding.from_pretrained(self.position_encoding_init(self.n_position, self.embedding_dim), freeze=True, padding_idx=None)

    @staticmethod
    def position_encoding_init(n_position, embedding_dim):
        """ Init the sinusoid position encoding table """
        position_enc = np.array([[pos / np.power(10000, 2 * (j // 2) / embedding_dim) for j in range(embedding_dim)] for pos in range(n_position)])
        position_enc[:, 0::2] = np.sin(position_enc[:, 0::2])
        position_enc[:, 1::2] = np.cos(position_enc[:, 1::2])
        return torch.from_numpy(position_enc).type(torch.FloatTensor)

    def forward(self, x: torch.Tensor):
        return self.position_enc(x)

def __init__(self, num_embeddings, embedding_dim=None):
    super(PositionEncoder, self).__init__()
    self.n_position = num_embeddings
    self.embedding_dim = self.n_position if embedding_dim is None else embedding_dim
    self.position_enc = nn.Embedding.from_pretrained(self.position_encoding_init(self.n_position, self.embedding_dim), freeze=True, padding_idx=None)

class TimeEncoder(nn.Module):

    def __init__(self, embedding_dim):
        super(TimeEncoder, self).__init__()
        self.embedding_dim = embedding_dim
        self.position_array = torch.nn.Parameter(self.get_position_array(), requires_grad=False)

    def get_position_array(self):
        x = torch.arange(0, self.embedding_dim, dtype=torch.float)
        x = x // 2 * 2
        x = torch.div(x, self.embedding_dim)
        x = torch.pow(10000.0, x)
        x = torch.div(1.0, x)
        return x

    def forward(self, x: torch.Tensor):
        v = torch.zeros(size=(x.shape[0], self.embedding_dim), dtype=torch.float, device=x.device)
        assert len(x.shape) == 1
        x = x.unsqueeze(dim=1)
        v[:, 0::2] = torch.sin(x * self.position_array[0::2])
        v[:, 1::2] = torch.cos(x * self.position_array[1::2])
        return v

def __init__(self, embedding_dim):
    super(TimeEncoder, self).__init__()
    self.embedding_dim = embedding_dim
    self.position_array = torch.nn.Parameter(self.get_position_array(), requires_grad=False)

class UnsqueezeEncoder(nn.Module):

    def __init__(self, unsqueeze_dim: int=-1, norm_value: float=1):
        super(UnsqueezeEncoder, self).__init__()
        self.unsqueeze_dim = unsqueeze_dim
        self.norm_value = norm_value

    def forward(self, x: torch.Tensor):
        x = x.float().unsqueeze(dim=self.unsqueeze_dim)
        if self.norm_value != 1:
            x = x / self.norm_value
        return x

def __init__(self, unsqueeze_dim: int=-1, norm_value: float=1):
    super(UnsqueezeEncoder, self).__init__()
    self.unsqueeze_dim = unsqueeze_dim
    self.norm_value = norm_value

def fc_block(in_channels: int, out_channels: int, activation: nn.Module=None, norm_type: str=None, use_dropout: bool=False, dropout_probability: float=0.5) -> nn.Sequential:
    """
    Overview:
        Create a fully-connected block with activation, normalization and dropout.
        Optional normalization can be done to the dim 1 (across the channels)
        x -> fc -> norm -> act -> dropout -> out
    Arguments:
        - in_channels (:obj:`int`): Number of channels in the input tensor
        - out_channels (:obj:`int`): Number of channels in the output tensor
        - activation (:obj:`nn.Module`): the optional activation function
        - norm_type (:obj:`str`): type of the normalization
        - use_dropout (:obj:`bool`) : whether to use dropout in the fully-connected block
        - dropout_probability (:obj:`float`) : probability of an element to be zeroed in the dropout. Default: 0.5
    Returns:
        - block (:obj:`nn.Sequential`): a sequential list containing the torch layers of the fully-connected block

    .. note::

        you can refer to nn.linear (https://pytorch.org/docs/master/generated/torch.nn.Linear.html)
    """
    block = []
    block.append(nn.Linear(in_channels, out_channels))
    if norm_type is not None and norm_type != 'none':
        block.append(build_normalization(norm_type, dim=1)(out_channels))
    if isinstance(activation, str) and activation != 'none':
        block.append(build_activation(activation))
    elif isinstance(activation, torch.nn.Module):
        block.append(activation)
    if use_dropout:
        block.append(nn.Dropout(dropout_probability))
    return nn.Sequential(*block)

def fc_block2(in_channels, out_channels, activation=None, norm_type=None, use_dropout=False, dropout_probability=0.5):
    """
    Overview:
        create a fully-connected block with activation, normalization and dropout
        optional normalization can be done to the dim 1 (across the channels)
        x -> fc -> norm -> act -> dropout -> out
    Arguments:
        - in_channels (:obj:`int`): Number of channels in the input tensor
        - out_channels (:obj:`int`): Number of channels in the output tensor
        - init_type (:obj:`str`): the type of init to implement
        - activation (:obj:`nn.Moduel`): the optional activation function
        - norm_type (:obj:`str`): type of the normalization
        - use_dropout (:obj:`bool`) : whether to use dropout in the fully-connected block
        - dropout_probability (:obj:`float`) : probability of an element to be zeroed in the dropout. Default: 0.5
    Returns:
        - block (:obj:`nn.Sequential`): a sequential list containing the torch layers of the fully-connected block

    .. note::
        you can refer to nn.linear (https://pytorch.org/docs/master/generated/torch.nn.Linear.html)
    """
    block = []
    if norm_type is not None and norm_type != 'none':
        block.append(build_normalization(norm_type, dim=1)(in_channels))
    if isinstance(activation, str) and activation != 'none':
        block.append(build_activation(activation))
    elif isinstance(activation, torch.nn.Module):
        block.append(activation)
    block.append(nn.Linear(in_channels, out_channels))
    if use_dropout:
        block.append(nn.Dropout(dropout_probability))
    return nn.Sequential(*block)

def conv2d_block(in_channels: int, out_channels: int, kernel_size: int, stride: int=1, padding: int=0, dilation: int=1, groups: int=1, activation: str=None, norm_type: str=None, bias: bool=True) -> nn.Sequential:
    """
    Overview:
        Create a 2-dim convlution layer with activation and normalization.
    Arguments:
        - in_channels (:obj:`int`): Number of channels in the input tensor
        - out_channels (:obj:`int`): Number of channels in the output tensor
        - kernel_size (:obj:`int`): Size of the convolving kernel
        - stride (:obj:`int`): Stride of the convolution
        - padding (:obj:`int`): Zero-padding added to both sides of the input
        - dilation (:obj:`int`): Spacing between kernel elements
        - groups (:obj:`int`): Number of blocked connections from input channels to output channels
        - pad_type (:obj:`str`): the way to add padding, include ['zero', 'reflect', 'replicate'], default: None
        - activation (:obj:`nn.Module`): the optional activation function
        - norm_type (:obj:`str`): type of the normalization, default set to None, now support ['BN', 'IN', 'SyncBN']
    Returns:
        - block (:obj:`nn.Sequential`): a sequential list containing the torch layers of the 2 dim convlution layer

    .. note::

        Conv2d (https://pytorch.org/docs/stable/generated/torch.nn.Conv2d.html#torch.nn.Conv2d)
    """
    block = []
    block.append(nn.Conv2d(in_channels=in_channels, out_channels=out_channels, kernel_size=kernel_size, stride=stride, padding=padding, dilation=dilation, groups=groups, bias=bias))
    if norm_type is not None:
        block.append(nn.GroupNorm(num_groups=1, num_channels=out_channels))
    if isinstance(activation, str) and activation != 'none':
        block.append(build_activation(activation))
    elif isinstance(activation, torch.nn.Module):
        block.append(activation)
    return nn.Sequential(*block)

def conv2d_block2(in_channels, out_channels, kernel_size, stride=1, padding=0, dilation=1, groups=1, activation: str=None, norm_type=None, bias: bool=True):
    """
    Overview:
        create a 2-dim convlution layer with activation and normalization.

        Note:
            Conv2d (https://pytorch.org/docs/stable/generated/torch.nn.Conv2d.html#torch.nn.Conv2d)

    Arguments:
        - in_channels (:obj:`int`): Number of channels in the input tensor
        - out_channels (:obj:`int`): Number of channels in the output tensor
        - kernel_size (:obj:`int`): Size of the convolving kernel
        - stride (:obj:`int`): Stride of the convolution
        - padding (:obj:`int`): Zero-padding added to both sides of the input
        - dilation (:obj:`int`): Spacing between kernel elements
        - groups (:obj:`int`): Number of blocked connections from input channels to output channels
        - init_type (:obj:`str`): the type of init to implement
        - pad_type (:obj:`str`): the way to add padding, include ['zero', 'reflect', 'replicate'], default: None
        - activation (:obj:`nn.Moduel`): the optional activation function
        - norm_type (:obj:`str`): type of the normalization, default set to None, now support ['BN', 'IN', 'SyncBN']

    Returns:
        - block (:obj:`nn.Sequential`): a sequential list containing the torch layers of the 2 dim convlution layer
    """
    block = []
    if norm_type is not None:
        block.append(nn.GroupNorm(num_groups=1, num_channels=out_channels))
    if isinstance(activation, str) and activation != 'none':
        block.append(build_activation(activation))
    elif isinstance(activation, torch.nn.Module):
        block.append(activation)
    block.append(nn.Conv2d(in_channels=in_channels, out_channels=out_channels, kernel_size=kernel_size, stride=stride, padding=padding, dilation=dilation, groups=groups, bias=bias))
    return nn.Sequential(*block)

class Model(nn.Module):

    def __init__(self, cfg={}, **kwargs):
        super(Model, self).__init__()
        self.whole_cfg = deep_merge_dicts(default_config, cfg)
        self.encoder = Encoder(self.whole_cfg)
        self.policy_head = PolicyHead(self.whole_cfg)
        self.value_head = ValueHead(self.whole_cfg)
        self.only_update_value = False
        self.ortho_init = self.whole_cfg.model.get('ortho_init', True)
        self.player_num = self.whole_cfg.env.player_num_per_team
        self.team_num = self.whole_cfg.env.team_num

    def forward(self, obs, temperature=0):
        obs = flatten_data(obs, start_dim=0, end_dim=1)
        embedding = self.encoder(obs)
        logit = self.policy_head(embedding)
        if temperature == 0:
            action = logit.argmax(dim=-1)
        else:
            logit = logit.div(temperature)
            dist = torch.distributions.Categorical(logits=logit)
            action = dist.sample()
        return {'action': action, 'logit': logit}

    def compute_value(self, obs):
        obs = flatten_data(obs, start_dim=0, end_dim=1)
        embedding = self.encoder(obs)
        batch_size = embedding.shape[0] // self.team_num // self.player_num
        team_embedding = embedding.reshape(batch_size * self.team_num, self.player_num, -1)
        team_embedding = self.transform_ctde(team_embedding, device=team_embedding.device)
        value = self.value_head(team_embedding)
        return {'value': value.reshape(-1)}

    def compute_logp_action(self, obs, **kwargs):
        obs = flatten_data(obs, start_dim=0, end_dim=1)
        embedding = self.encoder(obs)
        batch_size = embedding.shape[0] // self.team_num // self.player_num
        logit = self.policy_head(embedding)
        dist = torch.distributions.Categorical(logits=logit)
        action = dist.sample()
        action_log_probs = dist.log_prob(action)
        log_action_probs = action_log_probs
        team_embedding = embedding.reshape(batch_size * self.team_num, self.player_num, -1)
        team_embedding = self.transform_ctde(team_embedding, device=team_embedding.device)
        value = self.value_head(team_embedding)
        return {'action': action, 'action_logp': log_action_probs, 'logit': logit, 'value': value.reshape(-1)}

    def rl_train(self, inputs: dict, **kwargs) -> Dict[str, Any]:
        """
        Overview:
            Forward and backward function of learn mode.
        Arguments:
            - inputs (:obj:`dict`): Dict type data
        ArgumentsKeys:
            - obs shape     :math:`(T+1, B)`, where T is timestep, B is batch size
            - action_logp: behaviour logits, :math:`(T, B,action_size)`
            - action: behaviour actions, :math:`(T, B)`
            - reward: shape math:`(T, B)`
            - done:shape math:`(T, B)`
        Returns:
            - metric_dict (:obj:`Dict[str, Any]`):
              Including current total_loss, policy_gradient_loss, critic_loss and entropy_loss
        """
        obs = inputs['obs']
        obs = flatten_data(obs, start_dim=0, end_dim=1)
        embedding = self.encoder(obs)
        batch_size = embedding.shape[0] // self.player_num
        logits = self.policy_head(embedding)
        critic_input = embedding.reshape(batch_size, self.player_num, -1)
        critic_input = self.transform_ctde(critic_input, device=critic_input.device)
        if self.only_update_value:
            critic_input = detach_grad(critic_input)
        values = self.value_head(critic_input)
        outputs = {'value': values.squeeze(-1).reshape(-1), 'logit': logits, 'action': inputs['action'].reshape(-1), 'action_logp': inputs['action_logp'].reshape(-1), 'old_value': inputs['old_value'].reshape(-1), 'advantage': inputs['advantage'].reshape(-1), 'return': inputs['return'].reshape(-1)}
        return outputs

    def transform_ctde(self, array, device):
        ret = []
        for i in range(self.player_num):
            index = [i for i in range(self.player_num)]
            index.pop(i)
            other_array = torch.index_select(array, dim=1, index=torch.LongTensor(index).to(device))
            self_array = array[:, i, :].unsqueeze(dim=1)
            ret.append(torch.cat((self_array, other_array), dim=1).flatten(start_dim=1, end_dim=2).unsqueeze(1))
        ret = torch.cat(ret, dim=1)
        return ret

def __init__(self, cfg={}, **kwargs):
    super(Model, self).__init__()
    self.whole_cfg = deep_merge_dicts(default_config, cfg)
    self.encoder = Encoder(self.whole_cfg)
    self.policy_head = PolicyHead(self.whole_cfg)
    self.value_head = ValueHead(self.whole_cfg)
    self.only_update_value = False
    self.ortho_init = self.whole_cfg.model.get('ortho_init', True)
    self.player_num = self.whole_cfg.env.player_num_per_team
    self.team_num = self.whole_cfg.env.team_num

