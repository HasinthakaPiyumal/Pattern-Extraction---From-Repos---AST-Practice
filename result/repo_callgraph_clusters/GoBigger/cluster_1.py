# Cluster 1

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

def deep_merge_dicts(original: dict, new_dict: dict) -> dict:
    """
    Overview:
        Merge two dicts by calling ``deep_update``
    Arguments:
        - original (:obj:`dict`): Dict 1.
        - new_dict (:obj:`dict`): Dict 2.
    Returns:
        - merged_dict (:obj:`dict`): A new dict that is d1 and d2 deeply merged.
    """
    original = original or {}
    new_dict = new_dict or {}
    merged = copy.deepcopy(original)
    if new_dict:
        deep_update(merged, new_dict, True, [])
    return merged

def format_vector(v, norm_max):
    """
    Overview:
        The maximum value of the given vector's modulus
         example:
             1) The maximum speed limit is 5, given that the current speed is (6,8), it will return (3,4)
             2) Limit the maximum acceleration and return to the acceleration after the limit
    """
    if v.length() == 0:
        return v
    elif v.length() < norm_max:
        return v
    else:
        return v.normalize() * norm_max

def test_format_vector():
    v = Vector2(6, 8)
    norm_max = 5
    v_format = format_vector(v, norm_max=norm_max)
    assert v_format.x == 3
    assert v_format.y == 4

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

def get_dis(self, ball):
    """
        Overview:
            Get the distance between the centers of the two balls
        Parameters:
            ball <BaseBall>: another ball
        """
    return (self.position - ball.position).length()

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

def deep_merge_dicts(original: dict, new_dict: dict) -> dict:
    """
    Overview:
        merge two dict using deep_update
    Arguments:
        - original (:obj:`dict`): Dict 1.
        - new_dict (:obj:`dict`): Dict 2.
    Returns:
        - (:obj:`dict`): A new dict that is d1 and d2 deeply merged.
    """
    original = original or {}
    new_dict = new_dict or {}
    merged = copy.deepcopy(original)
    if new_dict:
        deep_update(merged, new_dict, True, [])
    return merged

def deep_merge_dicts(original: dict, new_dict: dict) -> dict:
    """
    Overview:
        merge two dict using deep_update
    Arguments:
        - original (:obj:`dict`): Dict 1.
        - new_dict (:obj:`dict`): Dict 2.
    Returns:
        - (:obj:`dict`): A new dict that is d1 and d2 deeply merged.
    """
    original = original or {}
    new_dict = new_dict or {}
    merged = copy.deepcopy(original)
    if new_dict:
        deep_update(merged, new_dict, True, [])
    return merged

