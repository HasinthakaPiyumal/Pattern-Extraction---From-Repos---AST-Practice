# Cluster 7

class BaseManager(ABC):
    """
    Overview:
        Base class for all ball managers
    """

    def __init__(self, cfg, border):
        self.cfg = cfg
        self.border = border
        self.balls = {}
        self.ball_settings = self.cfg.ball_settings

    def get_balls(self):
        """
        Overview:
            Get all balls currently managed
        """
        return self.balls.values()

    def add_balls(self, balls):
        """
        Overview:
            Add one (or more) balls
        """
        raise NotImplementedError

    def refresh(self):
        """
        Overview:
            Refresh. Used to refresh the balls in management. Such as replenishing eaten food balls
        """
        raise NotImplementedError

    def remove_balls(self, balls):
        """
        Overview:
            Remove managed balls
        """
        raise NotImplementedError

    def spawn_ball(self):
        raise NotImplementedError

    def init_balls(self):
        raise NotImplementedError

    def step(self, duration):
        """
        Overview:
            Perform a status update under the control of the server
        """
        raise NotImplementedError

    def obs(self):
        """
        Overview:
            Return data available for observation
        """
        raise NotImplementedError

    def reset(self):
        raise NotImplementedError

def get_balls(self):
    """
        Overview:
            Get all balls currently managed
        """
    return self.balls.values()

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

def get_players(self):
    return list(self.players.values())

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

def get_balls(self):
    return list(self.balls.values())

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

def get_balls(self):
    return list(self.balls.values())

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

def get_balls(self):
    return list(self.balls.values())

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

def get_probability(src, arr):
    diff = [abs(i - src) + 0.001 for i in arr]
    return [1 / i if 1 / i < 1 else 1 for i in diff]

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

def get_balls(self):
    """
        Overview:
            Get all the balls of the current player
        """
    return list(self.balls.values())

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

def move(self, ball_id=None, direction=None, duration=0.05):
    if ball_id is None:
        for ball_id, ball in self.balls.items():
            ball.move(given_acc=direction, duration=duration)
            ball.score_decay()
    elif ball_id in self.balls:
        self.balls[ball_id].move(given_acc=direction, duration=duration)
        self.balls[ball_id].score_decay()

