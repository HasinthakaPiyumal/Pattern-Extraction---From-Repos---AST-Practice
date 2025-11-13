# Cluster 3

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

def close(self):
    if hasattr(self, 'render'):
        self.render.close()

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

def add_balls(self, balls):
    if isinstance(balls, list):
        for ball in balls:
            self.balls[ball.ball_id] = ball
    elif isinstance(balls, FoodBall):
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
    elif isinstance(balls, FoodBall):
        balls.remove()
        try:
            del self.balls[balls.ball_id]
        except:
            pass

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

def add_balls(self, balls):
    if isinstance(balls, list):
        for ball in balls:
            self.balls[ball.ball_id] = ball
    elif isinstance(balls, ThornsBall):
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
    elif isinstance(balls, ThornsBall):
        balls.remove()
        try:
            del self.balls[balls.ball_id]
        except:
            pass

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

def deep_update(original: dict, new_dict: dict, new_keys_allowed: bool=False, whitelist: Optional[List[str]]=None, override_all_if_type_changes: Optional[List[str]]=None):
    """
    Overview:
        Update original dict with values from new_dict recursively.
    Arguments:
        - original (:obj:`dict`): Dictionary with default values.
        - new_dict (:obj:`dict`): Dictionary with values to be updated
        - new_keys_allowed (:obj:`bool`): Whether new keys are allowed.
        - whitelist (:obj:`Optional[List[str]]`):
            List of keys that correspond to dict
            values where new subkeys can be introduced. This is only at the top
            level.
        - override_all_if_type_changes(:obj:`Optional[List[str]]`):
            List of top level
            keys with value=dict, for which we always simply override the
            entire value (:obj:`dict`), if the "type" key in that value dict changes.

    .. note::

        If new key is introduced in new_dict, then if new_keys_allowed is not
        True, an error will be thrown. Further, for sub-dicts, if the key is
        in the whitelist, then new subkeys can be introduced.
    """
    whitelist = whitelist or []
    override_all_if_type_changes = override_all_if_type_changes or []
    for k, value in new_dict.items():
        if k not in original and (not new_keys_allowed):
            raise RuntimeError('Unknown config parameter `{}`. Base config have: {}.'.format(k, original.keys()))
        if isinstance(original.get(k), dict) and isinstance(value, dict):
            if k in override_all_if_type_changes and 'type' in value and ('type' in original[k]) and (value['type'] != original[k]['type']):
                original[k] = value
            elif k in whitelist:
                deep_update(original[k], value, True)
            else:
                deep_update(original[k], value, new_keys_allowed)
        else:
            original[k] = value
    return original

class PlayerStatesUtil:

    def __init__(self, obs_settings):
        self.obs_settings = obs_settings

    def get_player_states(self, food_balls, thorns_balls, spore_balls, players):
        player_states = {}
        if len(food_balls) > 0:
            food_radius = food_balls[0].radius
            food_score = food_balls[0].score
        else:
            food_radius = 0
            food_score = 0
        food_balls = np.array([[ball.position.x, ball.position.y] for ball in food_balls])
        for player in players:
            rectangle = self.get_rectangle_by_player(player)
            overlap = self.get_overlap(rectangle, food_balls, thorns_balls, spore_balls, players, food_radius, food_score)
            player_score, can_split, can_eject = player.get_info()
            player_states[player.player_id] = {'rectangle': rectangle, 'overlap': overlap, 'team_name': player.team_id, 'score': player_score, 'can_eject': can_eject, 'can_split': can_split}
        return player_states

    def get_rectangle_by_player(self, player):
        centroid = player.cal_centroid()
        xs_max = 0
        ys_max = 0
        for ball in player.get_balls():
            direction_center = centroid - ball.position
            if abs(direction_center.x) + ball.radius > xs_max:
                xs_max = abs(direction_center.x) + ball.radius
            if abs(direction_center.y) + ball.radius > ys_max:
                ys_max = abs(direction_center.y) + ball.radius
        xs_max = max(xs_max, self.obs_settings.partial.vision_x_min)
        ys_max = max(ys_max, self.obs_settings.partial.vision_y_min)
        scale_up_len = max(xs_max, ys_max)
        left_top_x = centroid.x - scale_up_len * self.obs_settings.partial.scale_up_ratio
        left_top_y = centroid.y - scale_up_len * self.obs_settings.partial.scale_up_ratio
        right_bottom_x = left_top_x + scale_up_len * self.obs_settings.partial.scale_up_ratio * 2
        right_bottom_y = left_top_y + scale_up_len * self.obs_settings.partial.scale_up_ratio * 2
        rectangle = (left_top_x, left_top_y, right_bottom_x, right_bottom_y)
        return rectangle

    def get_overlap(self, rectangle, food_balls, thorns_balls, spore_balls, players, food_radius=0, food_score=0):
        ret = {}
        food_count = 0
        thorns_count = 0
        spore_count = 0
        clone_count = 0
        assert len(players) > 0, 'len(players) = {} can not be 0'.format(len(players))
        food = len(food_balls) * [3 * [None]]
        thorns = len(thorns_balls) * [3 * [None]]
        spore = len(spore_balls) * [3 * [None]]
        clone = len(players) * players[0].ball_settings.part_num_max * [5 * [None]]
        if len(food) > 0:
            fr0 = rectangle[0] - food_radius
            fr1 = rectangle[1] - food_radius
            fr2 = rectangle[2] + food_radius
            fr3 = rectangle[3] + food_radius
            food_balls_x = food_balls[:, 0]
            food_balls_y = food_balls[:, 1]
            food_result = ne.evaluate('(food_balls_x>fr0) & (food_balls_x<fr2) & (food_balls_y>fr1) & (food_balls_y<fr3)')
            x = food_balls_x[food_result == True]
            y = food_balls_y[food_result == True]
            r_col = np.ones_like(x) * food_radius
            s_col = np.ones_like(x) * food_score
            res = np.stack((x, y, r_col, s_col), axis=-1)
            ret['food'] = res.tolist()
        else:
            ret['food'] = []
        for ball in thorns_balls:
            if ball.judge_in_rectangle(rectangle):
                thorns[thorns_count] = [ball.position.x, ball.position.y, ball.radius, ball.score, ball.vel.x, ball.vel.y]
                thorns_count += 1
        thorns = thorns[:thorns_count]
        ret['thorns'] = thorns
        for ball in spore_balls:
            if ball.judge_in_rectangle(rectangle):
                spore[spore_count] = [ball.position.x, ball.position.y, ball.radius, ball.score, ball.vel.x, ball.vel.y, ball.owner]
                spore_count += 1
        spore = spore[:spore_count]
        ret['spore'] = spore
        for player in players:
            for ball in player.get_balls():
                if ball.judge_in_rectangle(rectangle):
                    clone[clone_count] = [ball.position.x, ball.position.y, ball.radius, ball.score, ball.vel.x, ball.vel.y, ball.direction.x, ball.direction.y, player.player_id, player.team_id]
                    clone_count += 1
        clone = clone[:clone_count]
        ret['clone'] = clone
        return ret

def get_overlap(self, rectangle, food_balls, thorns_balls, spore_balls, players, food_radius=0, food_score=0):
    ret = {}
    food_count = 0
    thorns_count = 0
    spore_count = 0
    clone_count = 0
    assert len(players) > 0, 'len(players) = {} can not be 0'.format(len(players))
    food = len(food_balls) * [3 * [None]]
    thorns = len(thorns_balls) * [3 * [None]]
    spore = len(spore_balls) * [3 * [None]]
    clone = len(players) * players[0].ball_settings.part_num_max * [5 * [None]]
    if len(food) > 0:
        fr0 = rectangle[0] - food_radius
        fr1 = rectangle[1] - food_radius
        fr2 = rectangle[2] + food_radius
        fr3 = rectangle[3] + food_radius
        food_balls_x = food_balls[:, 0]
        food_balls_y = food_balls[:, 1]
        food_result = ne.evaluate('(food_balls_x>fr0) & (food_balls_x<fr2) & (food_balls_y>fr1) & (food_balls_y<fr3)')
        x = food_balls_x[food_result == True]
        y = food_balls_y[food_result == True]
        r_col = np.ones_like(x) * food_radius
        s_col = np.ones_like(x) * food_score
        res = np.stack((x, y, r_col, s_col), axis=-1)
        ret['food'] = res.tolist()
    else:
        ret['food'] = []
    for ball in thorns_balls:
        if ball.judge_in_rectangle(rectangle):
            thorns[thorns_count] = [ball.position.x, ball.position.y, ball.radius, ball.score, ball.vel.x, ball.vel.y]
            thorns_count += 1
    thorns = thorns[:thorns_count]
    ret['thorns'] = thorns
    for ball in spore_balls:
        if ball.judge_in_rectangle(rectangle):
            spore[spore_count] = [ball.position.x, ball.position.y, ball.radius, ball.score, ball.vel.x, ball.vel.y, ball.owner]
            spore_count += 1
    spore = spore[:spore_count]
    ret['spore'] = spore
    for player in players:
        for ball in player.get_balls():
            if ball.judge_in_rectangle(rectangle):
                clone[clone_count] = [ball.position.x, ball.position.y, ball.radius, ball.score, ball.vel.x, ball.vel.y, ball.direction.x, ball.direction.y, player.player_id, player.team_id]
                clone_count += 1
    clone = clone[:clone_count]
    ret['clone'] = clone
    return ret

class PlayerStatesSPUtil(PlayerStatesUtil):

    def get_overlap(self, rectangle, food_balls, thorns_balls, spore_balls, players, food_radius=0, food_score=0):
        ret = {}
        food_count = 0
        thorns_count = 0
        spore_count = 0
        clone_count = 0
        assert len(players) > 0, 'len(players) = {} can not be 0'.format(len(players))
        food = len(food_balls) * [3 * [None]]
        thorns = len(thorns_balls) * [3 * [None]]
        spore = len(spore_balls) * [3 * [None]]
        clone = len(players) * players[0].ball_settings.part_num_max * [5 * [None]]
        if len(food) > 0:
            fr0 = rectangle[0] - food_radius
            fr1 = rectangle[1] - food_radius
            fr2 = rectangle[2] + food_radius
            fr3 = rectangle[3] + food_radius
            food_balls_x = food_balls[:, 0]
            food_balls_y = food_balls[:, 1]
            food_result = ne.evaluate('(food_balls_x>fr0) & (food_balls_x<fr2) & (food_balls_y>fr1) & (food_balls_y<fr3)')
            x = food_balls_x[food_result == True]
            y = food_balls_y[food_result == True]
            r_col = np.ones_like(x) * food_radius
            s_col = np.ones_like(x) * food_score
            res = np.stack((x, y, r_col, s_col), axis=-1)
            ret['food'] = res.tolist()
        else:
            ret['food'] = []
        for ball in thorns_balls:
            if ball.judge_in_rectangle(rectangle):
                thorns[thorns_count] = [ball.position.x, ball.position.y, ball.radius, ball.score, ball.vel.x, ball.vel.y]
                thorns_count += 1
        thorns = thorns[:thorns_count]
        ret['thorns'] = thorns
        for ball in spore_balls:
            if ball.judge_in_rectangle(rectangle):
                spore[spore_count] = [ball.position.x, ball.position.y, ball.radius, ball.score, ball.owner]
                spore_count += 1
        spore = spore[:spore_count]
        ret['spore'] = spore
        for player in players:
            for ball in player.get_balls():
                if ball.judge_in_rectangle(rectangle):
                    clone[clone_count] = [ball.position.x, ball.position.y, ball.radius, ball.score, ball.vel.x, ball.vel.y, ball.direction.x, ball.direction.y, player.player_id, player.team_id, ball.ball_id]
                    clone_count += 1
        clone = clone[:clone_count]
        ret['clone'] = clone
        return ret

def get_overlap(self, rectangle, food_balls, thorns_balls, spore_balls, players, food_radius=0, food_score=0):
    ret = {}
    food_count = 0
    thorns_count = 0
    spore_count = 0
    clone_count = 0
    assert len(players) > 0, 'len(players) = {} can not be 0'.format(len(players))
    food = len(food_balls) * [3 * [None]]
    thorns = len(thorns_balls) * [3 * [None]]
    spore = len(spore_balls) * [3 * [None]]
    clone = len(players) * players[0].ball_settings.part_num_max * [5 * [None]]
    if len(food) > 0:
        fr0 = rectangle[0] - food_radius
        fr1 = rectangle[1] - food_radius
        fr2 = rectangle[2] + food_radius
        fr3 = rectangle[3] + food_radius
        food_balls_x = food_balls[:, 0]
        food_balls_y = food_balls[:, 1]
        food_result = ne.evaluate('(food_balls_x>fr0) & (food_balls_x<fr2) & (food_balls_y>fr1) & (food_balls_y<fr3)')
        x = food_balls_x[food_result == True]
        y = food_balls_y[food_result == True]
        r_col = np.ones_like(x) * food_radius
        s_col = np.ones_like(x) * food_score
        res = np.stack((x, y, r_col, s_col), axis=-1)
        ret['food'] = res.tolist()
    else:
        ret['food'] = []
    for ball in thorns_balls:
        if ball.judge_in_rectangle(rectangle):
            thorns[thorns_count] = [ball.position.x, ball.position.y, ball.radius, ball.score, ball.vel.x, ball.vel.y]
            thorns_count += 1
    thorns = thorns[:thorns_count]
    ret['thorns'] = thorns
    for ball in spore_balls:
        if ball.judge_in_rectangle(rectangle):
            spore[spore_count] = [ball.position.x, ball.position.y, ball.radius, ball.score, ball.owner]
            spore_count += 1
    spore = spore[:spore_count]
    ret['spore'] = spore
    for player in players:
        for ball in player.get_balls():
            if ball.judge_in_rectangle(rectangle):
                clone[clone_count] = [ball.position.x, ball.position.y, ball.radius, ball.score, ball.vel.x, ball.vel.y, ball.direction.x, ball.direction.y, player.player_id, player.team_id, ball.ball_id]
                clone_count += 1
    clone = clone[:clone_count]
    ret['clone'] = clone
    return ret

def norm(arr):
    return [i / sum(arr) for i in arr]

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

def test_remove(self):
    border = Border(0, 0, 1000, 1000)
    quad_node = QuadNode(border)
    node = BaseBall('0', position=border.sample(), border=border, score=1)
    quad_node.remove(node=node)

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

def get_team_infos(self):
    assert hasattr(self, 'server'), 'Please call `reset()` first'
    return self.server.get_team_infos()

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

def remove_balls(self, ball):
    ball.remove()
    if ball.ball_id in self.balls:
        try:
            del self.balls[ball.ball_id]
        except:
            pass
    return True

@pytest.mark.unittest
class TestFoodBall:

    def test_naive(self):
        ball_id = uuid.uuid1()
        border = Border(0, 0, 100, 100)
        position = Vector2(10, 10)
        food_ball = FoodBall(ball_id, position, border=border, score=1)
        assert True

    def test_default_config(self):
        assert isinstance(FoodBall.default_config(), EasyDict)

    def test_move(self):
        ball_id = uuid.uuid1()
        border = Border(0, 0, 100, 100)
        position = Vector2(10, 10)
        food_ball = FoodBall(ball_id, position, border=border, score=1)
        food_ball.move(direction=None, duration=None)

    def test_eat(self):
        ball_id = uuid.uuid1()
        border = Border(0, 0, 100, 100)
        position = Vector2(10, 10)
        food_ball = FoodBall(ball_id, position, border=border, score=1)
        food_ball.eat(ball=None)

def test_default_config(self):
    assert isinstance(FoodBall.default_config(), EasyDict)

class Agent:

    def __init__(self, cfg):
        self.whole_cfg = cfg
        self.player_num = self.whole_cfg.env.player_num_per_team
        self.team_num = self.whole_cfg.env.team_num
        self.game_player_id = self.whole_cfg.agent.game_player_id
        self.game_team_id = self.game_player_id // self.player_num
        self.player_id = self.whole_cfg.agent.player_id
        self.features = Features(self.whole_cfg)
        self.eval_padding = self.whole_cfg.agent.get('eval_padding', False)
        self.use_action_mask = self.whole_cfg.agent.get('use_action_mask', False)
        self.model = Model(self.whole_cfg)

    def reset(self):
        self.last_action_type = self.features.direction_num * 2

    def preprocess(self, obs):
        self.last_player_score = obs[1][self.game_player_id]['score']
        if self.use_action_mask:
            can_eject = obs[1][self.game_player_id]['can_eject']
            can_split = obs[1][self.game_player_id]['can_split']
            action_mask = self.features.generate_action_mask(can_eject=can_eject, can_split=can_split)
        else:
            action_mask = self.features.generate_action_mask(can_eject=True, can_split=True)
        obs = self.features.transform_obs(obs, game_player_id=self.game_player_id, last_action_type=self.last_action_type, padding=self.eval_padding)
        obs = default_collate_with_dim([obs])
        obs['action_mask'] = action_mask.unsqueeze(0)
        return obs

    def step(self, obs):
        self.raw_obs = obs
        obs = self.preprocess(obs)
        self.model_input = obs
        with torch.no_grad():
            self.model_output = self.model.compute_action(self.model_input)
        actions = self.postprocess(self.model_output['action'].detach().numpy())
        return actions

    def postprocess(self, model_actions):
        actions = {}
        actions[self.game_player_id] = self.features.transform_action(model_actions[0])
        self.last_action_type = model_actions[0].item()
        return actions

def preprocess(self, obs):
    self.last_player_score = obs[1][self.game_player_id]['score']
    if self.use_action_mask:
        can_eject = obs[1][self.game_player_id]['can_eject']
        can_split = obs[1][self.game_player_id]['can_split']
        action_mask = self.features.generate_action_mask(can_eject=can_eject, can_split=can_split)
    else:
        action_mask = self.features.generate_action_mask(can_eject=True, can_split=True)
    obs = self.features.transform_obs(obs, game_player_id=self.game_player_id, last_action_type=self.last_action_type, padding=self.eval_padding)
    obs = default_collate_with_dim([obs])
    obs['action_mask'] = action_mask.unsqueeze(0)
    return obs

def step(self, obs):
    self.raw_obs = obs
    obs = self.preprocess(obs)
    self.model_input = obs
    with torch.no_grad():
        self.model_output = self.model.compute_action(self.model_input)
    actions = self.postprocess(self.model_output['action'].detach().numpy())
    return actions

def postprocess(self, model_actions):
    actions = {}
    actions[self.game_player_id] = self.features.transform_action(model_actions[0])
    self.last_action_type = model_actions[0].item()
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

def forward(self, x):
    scalar_info = self.scalar_encoder(x['scalar_info'])
    team_info = self.team_encoder(x['team_info'])
    ball_embeddings, ball_info = self.ball_encoder(x['ball_info'])
    spatial_info = self.spatial_encoder(x, ball_embeddings)
    x = torch.cat([scalar_info, team_info, ball_info, spatial_info], dim=1)
    return x

def deep_update(original: dict, new_dict: dict, new_keys_allowed: bool=False, whitelist: Optional[List[str]]=None, override_all_if_type_changes: Optional[List[str]]=None):
    """
    Overview:
        Updates original dict with values from new_dict recursively.

    .. note::

        If new key is introduced in new_dict, then if new_keys_allowed is not
        True, an error will be thrown. Further, for sub-dicts, if the key is
        in the whitelist, then new subkeys can be introduced.

    Arguments:
        - original (:obj:`dict`): Dictionary with default values.
        - new_dict (:obj:`dict`): Dictionary with values to be updated
        - new_keys_allowed (:obj:`bool`): Whether new keys are allowed.
        - whitelist (Optional[List[str]]): List of keys that correspond to dict
            values where new subkeys can be introduced. This is only at the top
            level.
        - override_all_if_type_changes(Optional[List[str]]): List of top level
            keys with value=dict, for which we always simply override the
            entire value (:obj:`dict`), if the "type" key in that value dict changes.
    """
    whitelist = whitelist or []
    override_all_if_type_changes = override_all_if_type_changes or []
    for k, value in new_dict.items():
        if k not in original and (not new_keys_allowed):
            raise RuntimeError('Unknown config parameter `{}`. Base config have: {}.'.format(k, original.keys()))
        if isinstance(original.get(k), dict) and isinstance(value, dict):
            if k in override_all_if_type_changes and 'type' in value and ('type' in original[k]) and (value['type'] != original[k]['type']):
                original[k] = value
            elif k in whitelist:
                deep_update(original[k], value, True)
            else:
                deep_update(original[k], value, new_keys_allowed)
        else:
            original[k] = value
    return original

def default_collate_with_dim(batch, device='cpu', dim=0, k=None, cat=False):
    """Puts each data field into a tensor with outer dimension batch size"""
    elem = batch[0]
    elem_type = type(elem)
    if isinstance(elem, torch.Tensor):
        out = None
        if torch.utils.data.get_worker_info() is not None:
            numel = sum([x.numel() for x in batch])
            storage = elem.storage()._new_shared(numel)
            out = elem.new(storage)
        try:
            if cat == True:
                return torch.cat(batch, dim=dim, out=out).to(device=device)
            else:
                return torch.stack(batch, dim=dim, out=out).to(device=device)
        except:
            print(batch)
            if k is not None:
                print(k)
    elif elem_type.__module__ == 'numpy' and elem_type.__name__ != 'str_' and (elem_type.__name__ != 'string_'):
        if elem_type.__name__ == 'ndarray' or elem_type.__name__ == 'memmap':
            if np_str_obj_array_pattern.search(elem.dtype.str) is not None:
                raise TypeError(default_collate_err_msg_format.format(elem.dtype))
            return default_collate_with_dim([torch.as_tensor(b, device=device) for b in batch], device=device, dim=dim, cat=cat)
        elif elem.shape == ():
            try:
                return torch.as_tensor(batch, device=device)
            except:
                print(batch)
                if k is not None:
                    print(k)
    elif isinstance(elem, float):
        try:
            return torch.tensor(batch, device=device)
        except:
            print(batch)
            if k is not None:
                print(k)
    elif isinstance(elem, int_classes):
        try:
            return torch.tensor(batch, device=device)
        except:
            print(batch)
            if k is not None:
                print(k)
    elif isinstance(elem, string_classes):
        return batch
    elif isinstance(elem, container_abcs.Mapping):
        return {key: default_collate_with_dim([d[key] for d in batch if key in d.keys()], device=device, dim=dim, k=key, cat=cat) for key in elem}
    elif isinstance(elem, tuple) and hasattr(elem, '_fields'):
        return elem_type(*(default_collate_with_dim(samples, device=device, dim=dim, cat=cat) for samples in zip(*batch)))
    elif isinstance(elem, container_abcs.Sequence):
        it = iter(batch)
        elem_size = len(next(it))
        if not all((len(elem) == elem_size for elem in it)):
            raise RuntimeError('each element in list of batch should be of equal size')
        transposed = zip(*batch)
        return [default_collate_with_dim(samples, device=device, dim=dim, cat=cat) for samples in transposed]
    raise TypeError(default_collate_err_msg_format.format(elem_type))

def is_sequence(data):
    return isinstance(data, list) or isinstance(data, tuple)

def sequence_mask(lengths: torch.Tensor, max_len: Optional[int]=None):
    """
        Overview:
            create a mask for a batch sequences with different lengths
        Arguments:
            - lengths (:obj:`tensor`): lengths in each different sequences, shape could be (n, 1) or (n)
            - max_len (:obj:`int`): the padding size, if max_len is None, the padding size is the
                max length of sequences
        Returns:
            - masks (:obj:`torch.BoolTensor`): mask has the same device as lengths
    """
    if len(lengths.shape) == 1:
        lengths = lengths.unsqueeze(dim=1)
    bz = lengths.numel()
    if max_len is None:
        max_len = lengths.max()
    return torch.arange(0, max_len).type_as(lengths).repeat(bz, 1).lt(lengths).to(lengths.device)

class LSTMForwardWrapper(object):
    """
    Overview:
        abstract class used to wrap the LSTM forward method
    Interface:
        _before_forward, _after_forward
    """

    def _before_forward(self, inputs, prev_state):
        """
        Overview:
            preprocess the inputs and previous states
        Arguments:
            - inputs (:obj:`tensor`): input vector of cell, tensor of size [seq_len, batch_size, input_size]
            - prev_state (:obj:`tensor` or :obj:`list`):
                None or tensor of size [num_directions*num_layers, batch_size, hidden_size], if None then prv_state
                will be initialized to all zeros.
        Returns:
            - prev_state (:obj:`tensor`): batch previous state in lstm
        """
        assert hasattr(self, 'num_layers')
        assert hasattr(self, 'hidden_size')
        seq_len, batch_size = inputs.shape[:2]
        if prev_state is None:
            num_directions = 1
            zeros = torch.zeros(num_directions * self.num_layers, batch_size, self.hidden_size, dtype=inputs.dtype, device=inputs.device)
            prev_state = (zeros, zeros)
        elif is_sequence(prev_state):
            if len(prev_state) == 2 and isinstance(prev_state[0], torch.Tensor):
                pass
            else:
                if len(prev_state) != batch_size:
                    raise RuntimeError('prev_state number is not equal to batch_size: {}/{}'.format(len(prev_state), batch_size))
                num_directions = 1
                zeros = torch.zeros(num_directions * self.num_layers, 1, self.hidden_size, dtype=inputs.dtype, device=inputs.device)
                state = []
                for prev in prev_state:
                    if prev is None:
                        state.append([zeros, zeros])
                    else:
                        state.append(prev)
                state = list(zip(*state))
                prev_state = [torch.cat(t, dim=1) for t in state]
        else:
            raise TypeError('not support prev_state type: {}'.format(type(prev_state)))
        return prev_state

    def _after_forward(self, next_state, list_next_state=False):
        """
        Overview:
            post process the next_state, return list or tensor type next_states
        Arguments:
            - next_state (:obj:`list` :obj:`Tuple` of :obj:`tensor`): list of Tuple contains the next (h, c)
            - list_next_state (:obj:`bool`): whether return next_state with list format, default set to False
        Returns:
            - next_state(:obj:`list` of :obj:`tensor` or :obj:`tensor`): the formated next_state
        """
        if list_next_state:
            h, c = [torch.stack(t, dim=0) for t in zip(*next_state)]
            batch_size = h.shape[1]
            next_state = [torch.chunk(h, batch_size, dim=1), torch.chunk(c, batch_size, dim=1)]
            next_state = list(zip(*next_state))
        else:
            next_state = [torch.stack(t, dim=0) for t in zip(*next_state)]
        return next_state

def _before_forward(self, inputs, prev_state):
    """
        Overview:
            preprocess the inputs and previous states
        Arguments:
            - inputs (:obj:`tensor`): input vector of cell, tensor of size [seq_len, batch_size, input_size]
            - prev_state (:obj:`tensor` or :obj:`list`):
                None or tensor of size [num_directions*num_layers, batch_size, hidden_size], if None then prv_state
                will be initialized to all zeros.
        Returns:
            - prev_state (:obj:`tensor`): batch previous state in lstm
        """
    assert hasattr(self, 'num_layers')
    assert hasattr(self, 'hidden_size')
    seq_len, batch_size = inputs.shape[:2]
    if prev_state is None:
        num_directions = 1
        zeros = torch.zeros(num_directions * self.num_layers, batch_size, self.hidden_size, dtype=inputs.dtype, device=inputs.device)
        prev_state = (zeros, zeros)
    elif is_sequence(prev_state):
        if len(prev_state) == 2 and isinstance(prev_state[0], torch.Tensor):
            pass
        else:
            if len(prev_state) != batch_size:
                raise RuntimeError('prev_state number is not equal to batch_size: {}/{}'.format(len(prev_state), batch_size))
            num_directions = 1
            zeros = torch.zeros(num_directions * self.num_layers, 1, self.hidden_size, dtype=inputs.dtype, device=inputs.device)
            state = []
            for prev in prev_state:
                if prev is None:
                    state.append([zeros, zeros])
                else:
                    state.append(prev)
            state = list(zip(*state))
            prev_state = [torch.cat(t, dim=1) for t in state]
    else:
        raise TypeError('not support prev_state type: {}'.format(type(prev_state)))
    return prev_state

def _after_forward(self, next_state, list_next_state=False):
    """
        Overview:
            post process the next_state, return list or tensor type next_states
        Arguments:
            - next_state (:obj:`list` :obj:`Tuple` of :obj:`tensor`): list of Tuple contains the next (h, c)
            - list_next_state (:obj:`bool`): whether return next_state with list format, default set to False
        Returns:
            - next_state(:obj:`list` of :obj:`tensor` or :obj:`tensor`): the formated next_state
        """
    if list_next_state:
        h, c = [torch.stack(t, dim=0) for t in zip(*next_state)]
        batch_size = h.shape[1]
        next_state = [torch.chunk(h, batch_size, dim=1), torch.chunk(c, batch_size, dim=1)]
        next_state = list(zip(*next_state))
    else:
        next_state = [torch.stack(t, dim=0) for t in zip(*next_state)]
    return next_state

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

class PytorchLSTM(nn.LSTM, LSTMForwardWrapper):
    """
    Overview:
        Wrap the nn.LSTM , format the input and output
    Interface:
        forward

    .. note::
        you can reference the <https://pytorch.org/docs/stable/generated/torch.nn.LSTM.html#torch.nn.LSTM>
    """

    def forward(self, inputs, prev_state, list_next_state=True):
        """
        Overview:
            wrapped nn.LSTM.forward
        Arguments:
            - inputs (:obj:`tensor`): input vector of cell, tensor of size [seq_len, batch_size, input_size]
            - prev_state (:obj:`tensor`): None or tensor of size [num_directions*num_layers, batch_size, hidden_size]
            - list_next_state (:obj:`bool`): whether return next_state with list format, default set to False
        Returns:
            - output (:obj:`tensor`): output from lstm
            - next_state (:obj:`tensor` or :obj:`list`): hidden state from lstm
        """
        prev_state = self._before_forward(inputs, prev_state)
        output, next_state = nn.LSTM.forward(self, inputs, prev_state)
        next_state = self._after_forward(next_state, list_next_state)
        return (output, next_state)

    def _after_forward(self, next_state, list_next_state=False):
        """
        Overview:
            process hidden state after lstm, make it list or remains tensor
        Arguments:
            - nex_state (:obj:`tensor`): hidden state from lstm
            - list_nex_state (:obj:`bool`): whether return next_state with list format, default set to False
        Returns:
            - next_state (:obj:`tensor` or :obj:`list`): hidden state from lstm
        """
        if list_next_state:
            h, c = next_state
            batch_size = h.shape[1]
            next_state = [torch.chunk(h, batch_size, dim=1), torch.chunk(c, batch_size, dim=1)]
            return list(zip(*next_state))
        else:
            return next_state

def forward(self, inputs, prev_state, list_next_state=True):
    """
        Overview:
            wrapped nn.LSTM.forward
        Arguments:
            - inputs (:obj:`tensor`): input vector of cell, tensor of size [seq_len, batch_size, input_size]
            - prev_state (:obj:`tensor`): None or tensor of size [num_directions*num_layers, batch_size, hidden_size]
            - list_next_state (:obj:`bool`): whether return next_state with list format, default set to False
        Returns:
            - output (:obj:`tensor`): output from lstm
            - next_state (:obj:`tensor` or :obj:`list`): hidden state from lstm
        """
    prev_state = self._before_forward(inputs, prev_state)
    output, next_state = nn.LSTM.forward(self, inputs, prev_state)
    next_state = self._after_forward(next_state, list_next_state)
    return (output, next_state)

def _after_forward(self, next_state, list_next_state=False):
    """
        Overview:
            process hidden state after lstm, make it list or remains tensor
        Arguments:
            - nex_state (:obj:`tensor`): hidden state from lstm
            - list_nex_state (:obj:`bool`): whether return next_state with list format, default set to False
        Returns:
            - next_state (:obj:`tensor` or :obj:`list`): hidden state from lstm
        """
    if list_next_state:
        h, c = next_state
        batch_size = h.shape[1]
        next_state = [torch.chunk(h, batch_size, dim=1), torch.chunk(c, batch_size, dim=1)]
        return list(zip(*next_state))
    else:
        return next_state

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

class Swish(nn.Module):

    def __init__(self):
        super(Swish, self).__init__()

    def forward(self, x):
        x = x * torch.sigmoid(x)
        return x

def forward(self, x):
    x = x * torch.sigmoid(x)
    return x

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

@staticmethod
def get_binary_embed_matrix(bit_num):
    embedding_matrix = []
    for n in range(2 ** bit_num):
        embedding = [n >> d & 1 for d in range(bit_num)][::-1]
        embedding_matrix.append(embedding)
    return torch.tensor(embedding_matrix, dtype=torch.float)

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

def forward(self, x: torch.Tensor):
    x = x.float().unsqueeze(dim=self.unsqueeze_dim)
    if self.norm_value != 1:
        x = x / self.norm_value
    return x

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

def stack(data):
    result = {}
    for k1 in data[0].keys():
        result[k1] = {}
        if isinstance(data[0][k1], dict):
            for k2 in data[0][k1].keys():
                result[k1][k2] = torch.stack([o[k1][k2] for o in data])
        else:
            result[k1] = torch.stack([o[k1] for o in data])
    return result

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

def flatten_data(data, start_dim=0, end_dim=1):
    if isinstance(data, dict):
        return {k: flatten_data(v, start_dim=start_dim, end_dim=end_dim) for k, v in data.items()}
    elif isinstance(data, torch.Tensor):
        return torch.flatten(data, start_dim=start_dim, end_dim=end_dim)

def deep_update(original: dict, new_dict: dict, new_keys_allowed: bool=False, whitelist: Optional[List[str]]=None, override_all_if_type_changes: Optional[List[str]]=None):
    """
    Overview:
        Updates original dict with values from new_dict recursively.

    .. note::

        If new key is introduced in new_dict, then if new_keys_allowed is not
        True, an error will be thrown. Further, for sub-dicts, if the key is
        in the whitelist, then new subkeys can be introduced.

    Arguments:
        - original (:obj:`dict`): Dictionary with default values.
        - new_dict (:obj:`dict`): Dictionary with values to be updated
        - new_keys_allowed (:obj:`bool`): Whether new keys are allowed.
        - whitelist (Optional[List[str]]): List of keys that correspond to dict
            values where new subkeys can be introduced. This is only at the top
            level.
        - override_all_if_type_changes(Optional[List[str]]): List of top level
            keys with value=dict, for which we always simply override the
            entire value (:obj:`dict`), if the "type" key in that value dict changes.
    """
    whitelist = whitelist or []
    override_all_if_type_changes = override_all_if_type_changes or []
    for k, value in new_dict.items():
        if k not in original and (not new_keys_allowed):
            raise RuntimeError('Unknown config parameter `{}`. Base config have: {}.'.format(k, original.keys()))
        if isinstance(original.get(k), dict) and isinstance(value, dict):
            if k in override_all_if_type_changes and 'type' in value and ('type' in original[k]) and (value['type'] != original[k]['type']):
                original[k] = value
            elif k in whitelist:
                deep_update(original[k], value, True)
            else:
                deep_update(original[k], value, new_keys_allowed)
        else:
            original[k] = value
    return original

def default_collate_with_dim(batch, device='cpu', dim=0, k=None, cat=False):
    """Puts each data field into a tensor with outer dimension batch size"""
    elem = batch[0]
    elem_type = type(elem)
    if isinstance(elem, torch.Tensor):
        out = None
        if torch.utils.data.get_worker_info() is not None:
            numel = sum([x.numel() for x in batch])
            storage = elem.storage()._new_shared(numel)
            out = elem.new(storage)
        try:
            if cat == True:
                return torch.cat(batch, dim=dim, out=out).to(device=device)
            else:
                return torch.stack(batch, dim=dim, out=out).to(device=device)
        except:
            print(batch)
            if k is not None:
                print(k)
    elif elem_type.__module__ == 'numpy' and elem_type.__name__ != 'str_' and (elem_type.__name__ != 'string_'):
        if elem_type.__name__ == 'ndarray' or elem_type.__name__ == 'memmap':
            if np_str_obj_array_pattern.search(elem.dtype.str) is not None:
                raise TypeError(default_collate_err_msg_format.format(elem.dtype))
            return default_collate_with_dim([torch.as_tensor(b, device=device) for b in batch], device=device, dim=dim, cat=cat)
        elif elem.shape == ():
            try:
                return torch.as_tensor(batch, device=device)
            except:
                print(batch)
                if k is not None:
                    print(k)
    elif isinstance(elem, float):
        try:
            return torch.tensor(batch, device=device)
        except:
            print(batch)
            if k is not None:
                print(k)
    elif isinstance(elem, int_classes):
        try:
            return torch.tensor(batch, device=device)
        except:
            print(batch)
            if k is not None:
                print(k)
    elif isinstance(elem, string_classes):
        return batch
    elif isinstance(elem, container_abcs.Mapping):
        return {key: default_collate_with_dim([d[key] for d in batch if key in d.keys()], device=device, dim=dim, k=key, cat=cat) for key in elem}
    elif isinstance(elem, tuple) and hasattr(elem, '_fields'):
        return elem_type(*(default_collate_with_dim(samples, device=device, dim=dim, cat=cat) for samples in zip(*batch)))
    elif isinstance(elem, container_abcs.Sequence):
        it = iter(batch)
        elem_size = len(next(it))
        if not all((len(elem) == elem_size for elem in it)):
            raise RuntimeError('each element in list of batch should be of equal size')
        transposed = zip(*batch)
        return [default_collate_with_dim(samples, device=device, dim=dim, cat=cat) for samples in transposed]
    raise TypeError(default_collate_err_msg_format.format(elem_type))

