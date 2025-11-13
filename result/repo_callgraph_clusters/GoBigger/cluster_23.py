# Cluster 23

def method2(food_balls, cx, cy, r):
    t1 = time.time()
    X = np.array([ball.x for ball in food_balls])
    Y = np.array([ball.y for ball in food_balls])
    t2 = time.time()
    res = ne.evaluate('((X-cx)**2 + (Y-cy)**2)<r**2')
    res_x = X[res == True]
    res_y = Y[res == True]
    t3 = time.time()
    return (res_x, res_y, t2 - t1, t3 - t2)

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

def to_aliased_circle(position, radius, cut_num=8, decrease=1):
    point_list = []
    radius_decrease = radius - decrease
    assert radius_decrease > 0
    piece_angle = math.pi / cut_num
    for i in range(cut_num * 2):
        angle = piece_angle * i
        if i % 2 == 0:
            point_list.append([position.x + radius * math.cos(angle), position.y + radius * math.sin(angle)])
        else:
            point_list.append([position.x + radius_decrease * math.cos(angle), position.y + radius_decrease * math.sin(angle)])
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

def set_score(self, score: float) -> None:
    self.score = score
    if self.score > self.score_max:
        self.score = self.score_max
    elif self.score < self.score_min:
        self.score = self.score_min
    self.radius = self.score_to_radius(self.score)

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

def setup_action(self):
    theta = math.pi * 2 / self.direction_num
    self.x_y_action_List = [[0.3 * math.cos(theta * i), 0.3 * math.sin(theta * i), 0] for i in range(self.direction_num)] + [[math.cos(theta * i), math.sin(theta * i), 0] for i in range(self.direction_num)] + [[0, 0, 0], [0, 0, 1], [0, 0, 2]]

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

@staticmethod
def position_encoding_init(n_position, embedding_dim):
    """ Init the sinusoid position encoding table """
    position_enc = np.array([[pos / np.power(10000, 2 * (j // 2) / embedding_dim) for j in range(embedding_dim)] for pos in range(n_position)])
    position_enc[:, 0::2] = np.sin(position_enc[:, 0::2])
    position_enc[:, 1::2] = np.cos(position_enc[:, 1::2])
    return torch.from_numpy(position_enc).type(torch.FloatTensor)

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

def forward(self, x: torch.Tensor):
    v = torch.zeros(size=(x.shape[0], self.embedding_dim), dtype=torch.float, device=x.device)
    assert len(x.shape) == 1
    x = x.unsqueeze(dim=1)
    v[:, 0::2] = torch.sin(x * self.position_array[0::2])
    v[:, 1::2] = torch.cos(x * self.position_array[1::2])
    return v

