# Cluster 10

@pytest.mark.unittest
class TestBaseAgent:

    def test_init(self):
        base_agent = BaseAgent()
        assert True

    def test_step(self):
        base_agent = BaseAgent()
        with pytest.raises(Exception) as e:
            base_agent.step(obs=None)

def test_init(self):
    base_agent = BaseAgent()
    assert True

def test_step(self):
    base_agent = BaseAgent()
    with pytest.raises(Exception) as e:
        base_agent.step(obs=None)

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

def spawn_ball(self, position=None):
    if position is None:
        position = self.border.sample()
    name = uuid.uuid1()
    return SporeBall(name=name, position=position, border=self.border, score=self.ball_settings.score_init, direction=Vector2(1, 0))

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

def get_spore_ball(self):
    ball_id = uuid.uuid1()
    border = Border(0, 0, 1000, 1000)
    position = Vector2(100, 100)
    score = SporeBall.default_config().score_init
    direction = Vector2(1, 0)
    return SporeBall(ball_id, position, border=border, score=score, direction=direction)

@pytest.mark.unittest
class TestBasePlayer:

    def test_all(self):
        base_player = BasePlayer(name='test')
        with pytest.raises(Exception) as e:
            base_player.move(direction=None)
        with pytest.raises(Exception) as e:
            base_player.eject()
        with pytest.raises(Exception) as e:
            base_player.eat(ball=None)
        with pytest.raises(Exception) as e:
            base_player.stop()
        with pytest.raises(Exception) as e:
            base_player.respawn()

def test_all(self):
    base_player = BasePlayer(name='test')
    with pytest.raises(Exception) as e:
        base_player.move(direction=None)
    with pytest.raises(Exception) as e:
        base_player.eject()
    with pytest.raises(Exception) as e:
        base_player.eat(ball=None)
    with pytest.raises(Exception) as e:
        base_player.stop()
    with pytest.raises(Exception) as e:
        base_player.respawn()

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

def test_naive(self):
    ball_id = uuid.uuid1()
    border = Border(0, 0, 100, 100)
    position = Vector2(10, 10)
    food_ball = FoodBall(ball_id, position, border=border, score=1)
    assert True

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

def test_eat(self):
    ball_id = uuid.uuid1()
    border = Border(0, 0, 1000, 1000)
    position = Vector2(100, 100)
    direction = Vector2(1, 0)
    spore_ball = SporeBall(ball_id, position, border=border, score=2, direction=direction)
    spore_ball.eat(ball=None)

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

def test_eat_baseball(self):
    border = Border(0, 0, 100, 100)
    position = Vector2(10, 10)
    ball_id = uuid.uuid1()
    base_ball = BaseBall(ball_id, position, border=border, score=1)
    clone_ball = self.get_clone()
    clone_ball.eat(base_ball)

@pytest.mark.unittest
class TestThornsBall:

    def test_init(self):
        ball_id = uuid.uuid1()
        border = Border(0, 0, 100, 100)
        position = Vector2(10, 10)
        thorns_ball = ThornsBall(ball_id, position, border=border, score=4)
        assert True

    def test_eat_move(self):
        ball_id = uuid.uuid1()
        border = Border(0, 0, 1000, 1000)
        thorns_position = Vector2(100, 100)
        thorns_score = ThornsBall.default_config().score_min
        thorns_ball = ThornsBall(ball_id, thorns_position, border=border, score=thorns_score)
        ball_id = uuid.uuid1()
        spore_position = Vector2(100, 100)
        spore_score = SporeBall.default_config().score_init
        direction = Vector2(1, 0)
        spore_ball = SporeBall(ball_id, spore_position, border=border, score=spore_score, direction=direction)
        logging.debug('=========================== before eat =============================')
        logging.debug('[thorns] position={}, score={}, vel={}, move_frame={}'.format(thorns_ball.position, thorns_ball.score, thorns_ball.vel, thorns_ball.move_frame))
        logging.debug('[spore]  position={}, score={}, vel={}'.format(spore_ball.position, spore_ball.score, spore_ball.vel))
        thorns_ball.eat(spore_ball)
        logging.debug('=========================== after eat  =============================')
        logging.debug('[thorns] position={}, score={}, vel={}, move_frame={}'.format(thorns_ball.position, thorns_ball.score, thorns_ball.vel, thorns_ball.move_frame))
        logging.debug('[spore]  position={}, score={}, vel={}'.format(spore_ball.position, spore_ball.score, spore_ball.vel))
        for i in range(10):
            thorns_ball.move(duration=0.05)
            logging.debug('=========================== after move {} ============================='.format(i))
            logging.debug('[thorns] position={}, score={}, vel={}, move_frame={}'.format(thorns_ball.position, thorns_ball.score, thorns_ball.vel, thorns_ball.move_frame))
        assert True

    def test_judge_in_rectangle(self):
        border = Border(0, 0, 800, 800)
        position = Vector2(400, 400)
        ball_id = uuid.uuid1()
        thorns_ball = ThornsBall(ball_id, position, border=border, score=10)
        rectangle = [300, 300, 500, 500]
        assert thorns_ball.judge_in_rectangle(rectangle)

    def test_eat_others(self):
        border = Border(0, 0, 800, 800)
        position = Vector2(400, 400)
        ball_id = uuid.uuid1()
        thorns_ball = ThornsBall(ball_id, position, border=border, score=10)
        position = Vector2(10, 10)
        ball_id = uuid.uuid1()
        base_ball = BaseBall(ball_id, position, border=border, score=1)
        thorns_ball.eat(base_ball)
        ball_id = uuid.uuid1()
        spore_position = Vector2(100, 100)
        spore_score = SporeBall.default_config().score_init
        direction = Vector2(1, 0)
        spore_ball = SporeBall(ball_id, spore_position, border=border, score=spore_score, direction=direction)
        thorns_ball.set_score(thorns_ball.score_max)
        thorns_ball.eat(spore_ball)

def test_init(self):
    ball_id = uuid.uuid1()
    border = Border(0, 0, 100, 100)
    position = Vector2(10, 10)
    thorns_ball = ThornsBall(ball_id, position, border=border, score=4)
    assert True

def test_eat_move(self):
    ball_id = uuid.uuid1()
    border = Border(0, 0, 1000, 1000)
    thorns_position = Vector2(100, 100)
    thorns_score = ThornsBall.default_config().score_min
    thorns_ball = ThornsBall(ball_id, thorns_position, border=border, score=thorns_score)
    ball_id = uuid.uuid1()
    spore_position = Vector2(100, 100)
    spore_score = SporeBall.default_config().score_init
    direction = Vector2(1, 0)
    spore_ball = SporeBall(ball_id, spore_position, border=border, score=spore_score, direction=direction)
    logging.debug('=========================== before eat =============================')
    logging.debug('[thorns] position={}, score={}, vel={}, move_frame={}'.format(thorns_ball.position, thorns_ball.score, thorns_ball.vel, thorns_ball.move_frame))
    logging.debug('[spore]  position={}, score={}, vel={}'.format(spore_ball.position, spore_ball.score, spore_ball.vel))
    thorns_ball.eat(spore_ball)
    logging.debug('=========================== after eat  =============================')
    logging.debug('[thorns] position={}, score={}, vel={}, move_frame={}'.format(thorns_ball.position, thorns_ball.score, thorns_ball.vel, thorns_ball.move_frame))
    logging.debug('[spore]  position={}, score={}, vel={}'.format(spore_ball.position, spore_ball.score, spore_ball.vel))
    for i in range(10):
        thorns_ball.move(duration=0.05)
        logging.debug('=========================== after move {} ============================='.format(i))
        logging.debug('[thorns] position={}, score={}, vel={}, move_frame={}'.format(thorns_ball.position, thorns_ball.score, thorns_ball.vel, thorns_ball.move_frame))
    assert True

def test_judge_in_rectangle(self):
    border = Border(0, 0, 800, 800)
    position = Vector2(400, 400)
    ball_id = uuid.uuid1()
    thorns_ball = ThornsBall(ball_id, position, border=border, score=10)
    rectangle = [300, 300, 500, 500]
    assert thorns_ball.judge_in_rectangle(rectangle)

def test_eat_others(self):
    border = Border(0, 0, 800, 800)
    position = Vector2(400, 400)
    ball_id = uuid.uuid1()
    thorns_ball = ThornsBall(ball_id, position, border=border, score=10)
    position = Vector2(10, 10)
    ball_id = uuid.uuid1()
    base_ball = BaseBall(ball_id, position, border=border, score=1)
    thorns_ball.eat(base_ball)
    ball_id = uuid.uuid1()
    spore_position = Vector2(100, 100)
    spore_score = SporeBall.default_config().score_init
    direction = Vector2(1, 0)
    spore_ball = SporeBall(ball_id, spore_position, border=border, score=spore_score, direction=direction)
    thorns_ball.set_score(thorns_ball.score_max)
    thorns_ball.eat(spore_ball)

