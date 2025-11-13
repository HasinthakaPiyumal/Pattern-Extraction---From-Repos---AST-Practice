# Cluster 33

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

def update_match_ratio(self):
    self.cfg.map_width = int(self.cfg.map_width * math.sqrt(self.cfg.match_ratio))
    self.cfg.map_height = int(self.cfg.map_height * math.sqrt(self.cfg.match_ratio))
    self.cfg.manager_settings.food_manager.num_init = int(self.cfg.manager_settings.food_manager.num_init * self.cfg.match_ratio)
    self.cfg.manager_settings.food_manager.num_min = int(self.cfg.manager_settings.food_manager.num_min * self.cfg.match_ratio)
    self.cfg.manager_settings.food_manager.num_max = int(self.cfg.manager_settings.food_manager.num_max * self.cfg.match_ratio)
    self.cfg.manager_settings.thorns_manager.num_init = int(self.cfg.manager_settings.thorns_manager.num_init * self.cfg.match_ratio)
    self.cfg.manager_settings.thorns_manager.num_min = int(self.cfg.manager_settings.thorns_manager.num_min * self.cfg.match_ratio)
    self.cfg.manager_settings.thorns_manager.num_max = int(self.cfg.manager_settings.thorns_manager.num_max * self.cfg.match_ratio)

def to_arrow(position, radius, direction, out=1.2):
    x0, y0 = (position.x, position.y)
    x, y = (direction.x, direction.y)
    point_list = [[x0 + out * radius * x, y0 + out * radius * y], [x0 - math.sqrt(2) / 2 * radius * (y - x), y0 + math.sqrt(2) / 2 * radius * (x + y)], [x0 + math.sqrt(2) / 2 * radius * (x + y), y0 + math.sqrt(2) / 2 * radius * (y - x)]]
    return point_list

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

def score_to_radius(self, score):
    return math.sqrt(score / 100 * 0.042 + 0.15)

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

def score_decay(self):
    """
        Overview: 
            Control the score of the ball to decay over time
        """
    if self.score > self.score_decay_min:
        self.set_score(self.score * (1 - self.score_decay_rate_per_frame * math.sqrt(self.radius)))
    return True

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

def generate_action_mask(self, can_eject, can_split):
    action_mask = torch.zeros(size=(self.action_num,), dtype=torch.bool)
    if not can_eject:
        action_mask[self.direction_num * 2 + 1] = True
    if not can_split:
        action_mask[self.direction_num * 2 + 2] = True
    return action_mask

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

def _init(self):
    gain = math.sqrt(1.0 / self.hidden_size)
    for l in range(self.num_layers):
        torch.nn.init.uniform_(self.wx[l], -gain, gain)
        torch.nn.init.uniform_(self.wh[l], -gain, gain)
        if self.bias is not None:
            torch.nn.init.uniform_(self.bias[l], -gain, gain)

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

def prepare_head(tensor):
    bsz, seq_len, _ = tensor.size()
    tensor = tensor.view(batch_size, tensor.size(1), n_heads, dim_per_head)
    tensor = tensor.transpose(1, 2).contiguous().view(batch_size * n_heads, seq_len, dim_per_head)
    return tensor

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

class OnehotEncoder(nn.Module):

    def __init__(self, num_embeddings: int):
        super(OnehotEncoder, self).__init__()
        self.num_embeddings = num_embeddings
        self.main = nn.Embedding.from_pretrained(torch.eye(self.num_embeddings), freeze=True, padding_idx=None)

    def forward(self, x: torch.Tensor):
        x = x.long().clamp_(max=self.num_embeddings - 1)
        return self.main(x)

def forward(self, x: torch.Tensor):
    x = x.long().clamp_(max=self.num_embeddings - 1)
    return self.main(x)

class OnehotEmbedding(nn.Module):

    def __init__(self, num_embeddings: int, embedding_dim: int):
        super(OnehotEmbedding, self).__init__()
        self.num_embeddings = num_embeddings
        self.embedding_dim = embedding_dim
        self.main = nn.Embedding(num_embeddings=self.num_embeddings, embedding_dim=self.embedding_dim)

    def forward(self, x: torch.Tensor):
        x = x.long().clamp_(max=self.num_embeddings - 1)
        return self.main(x)

def forward(self, x: torch.Tensor):
    x = x.long().clamp_(max=self.num_embeddings - 1)
    return self.main(x)

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

def forward(self, x: torch.Tensor):
    x = x.long().clamp_(max=2 ** self.bit_num - 1)
    return self.main(x)

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

def forward(self, x: torch.Tensor):
    x = x.long().clamp_(max=self.max_val, min=-self.max_val)
    return self.main(x + self.max_val)

