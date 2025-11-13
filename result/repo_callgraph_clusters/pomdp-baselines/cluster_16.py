# Cluster 16

def create_env(env_id: str, no_terminal: bool=False, env_time_limit: int=27000, env_action_repeat: int=4, one_hot_actions: bool=False, flatten_img: bool=True):
    env = Atari(env_id.lower(), action_repeat=env_action_repeat, flatten_img=flatten_img)
    if hasattr(env.action_space, 'n') and one_hot_actions:
        env = OneHotActionWrapper(env)
    if env_time_limit > 0:
        env = TimeLimitWrapper(env, env_time_limit)
    return env

class ActionRewardResetWrapper(gym.Wrapper):

    def __init__(self, env, no_terminal):
        super().__init__(env)
        self.env = env
        self.no_terminal = no_terminal
        self.action_size = env.action_space.n if hasattr(env.action_space, 'n') else env.action_space.shape[0]

    def step(self, action):
        obs, reward, done, info = self.env.step(action)
        if isinstance(action, int):
            action_vec = np.zeros(self.action_size)
            action_vec[action] = 1.0
        else:
            assert isinstance(action, np.ndarray) and action.shape == (self.action_size,), 'Wrong one-hot action shape'
            action_vec = action
        obs['action'] = action_vec
        obs['reward'] = np.array(reward)
        obs['terminal'] = np.array(False if self.no_terminal or info.get('time_limit') else done)
        obs['reset'] = np.array(False)
        return (obs, reward, done, info)

    def reset(self):
        obs = self.env.reset()
        obs['action'] = np.zeros(self.action_size)
        obs['reward'] = np.array(0.0)
        obs['terminal'] = np.array(False)
        obs['reset'] = np.array(True)
        return obs

def __init__(self, env, no_terminal):
    super().__init__(env)
    self.env = env
    self.no_terminal = no_terminal
    self.action_size = env.action_space.n if hasattr(env.action_space, 'n') else env.action_space.shape[0]

class SpaceInvadersWorld(PhysicalWorld):
    missile_class = Missile
    shield_class = Shield
    player_ship_class = PlayerShip
    invader_class = LeftRightMovingInvader
    n_actions = 4
    parameters_player_missile = {'class': PlayerMissile, 'fire_rate': 20, 'max_missiles': 2, 'missile_impulse': 100}
    parameters_invader_missile = {'class': InvaderMissile, 'fire_rate': 15, 'max_missiles': 10, 'missile_impulse': 100}
    invaders_per_row = 11

    def create_world(self, parent):
        p_width = self._width / self.physical_scale
        p_height = self._height / self.physical_scale
        ground = self._engine.CreateStaticBody(position=(0, 0))
        ground.CreateEdgeFixture(vertices=[(0, 0), (0, p_height)])
        ground.CreateEdgeFixture(vertices=[(0, 0), (p_width, 0)])
        ground.CreateEdgeFixture(vertices=[(0, p_height), (p_width, p_height)])
        ground.CreateEdgeFixture(vertices=[(p_width, p_height), (p_width, 0)])
        self._ground = ground
        self.create_invaders()
        self.create_shields()
        self.player_ship = self.player_ship_class(world=self, position=self.initial_player_ship_position())
        parent.add(self.player_ship)

    def create_shields(self):
        """Create protective shields."""
        for config in self.initial_shield_configuration():
            shield = self.shield_class(world=self, **config)
            self._batch.add(shield)

    def create_invaders(self):
        """Create invader grid."""
        offset_x = 80
        offset_y = self.initial_invader_row()
        for row, invader_type in enumerate(self.initial_invader_configuration()):
            for column in range(self.invaders_per_row):
                invader = self.invader_class(world=self, position=(offset_x, offset_y), invader_type=invader_type)
                self._batch.add(invader)
                offset_x += 48
            offset_x = 80
            offset_y -= invader.height * 2

    def fire_missile(self, entity, parameters):

        def count_missiles(node):
            if not isinstance(node, parameters['class']):
                return
            return 1
        if sum(self.walk(count_missiles)) >= parameters['max_missiles']:
            return
        last_fire_step = self._last_fire_step.get(parameters['class'], 0)
        if self._step - last_fire_step <= parameters['fire_rate']:
            return
        self._last_fire_step[parameters['class']] = self._step
        missile = parameters['class'].fire(world=self, entity=entity, impulse=parameters['missile_impulse'])
        self._batch.add(missile)

    @property
    def lives(self):
        return self._lives

    @property
    def score(self):
        return self._score

    @property
    def parameters(self):
        parameters = super(SpaceInvadersWorld, self).parameters
        parameters.update({'world': 'space_invaders'})
        return parameters

    def ship_impulse(self):
        """Relative paddle impulse strength on movement actions."""
        return 50

    def act(self, action):
        """Perform external action."""
        if action == 0:
            pass
        elif action == 1:
            self.player_ship.apply_impulse((-self.ship_impulse() / self.physical_scale * self.player_ship.body.mass, 0))
        elif action == 2:
            self.player_ship.apply_impulse((self.ship_impulse() / self.physical_scale * self.player_ship.body.mass, 0))
        elif action == 3:
            self.fire_missile(self.player_ship, self.parameters_player_missile)

    def initial_shield_configuration(self):
        return [{'health': 20, 'position': (self._width // 4, 200)}, {'health': 20, 'position': (2 * self._width // 4, 200)}, {'health': 20, 'position': (3 * self._width // 4, 200)}]

    def initial_invader_row(self):
        return self._height - 50

    def initial_invader_configuration(self):
        return [Invader.TYPE_1, Invader.TYPE_2, Invader.TYPE_2, Invader.TYPE_3, Invader.TYPE_3]

    def initial_player_ship_position(self):
        """Initial player ship position after reset."""
        return (self._width / 2, 25)

    def adjust_invader_missiles(self, n_invaders):
        """Adjust invader missile inventory."""
        if n_invaders >= 45:
            missiles = 10
        elif n_invaders >= 40:
            missiles = 9
        elif n_invaders >= 35:
            missiles = 8
        elif n_invaders >= 30:
            missiles = 7
        elif n_invaders >= 25:
            missiles = 6
        else:
            missiles = 5
        self.parameters_invader_missile['max_missiles'] = missiles

    def add_kill_score(self):
        """Add score when an invader is killed."""
        self._score += 1

    def reset_world(self):
        """Reset the game."""
        super(SpaceInvadersWorld, self).reset_world()
        self._lives = 3
        self._score = 0
        self._step = 0
        self._last_fire_step = {}

        def remove_nodes(node):
            if isinstance(node, (Missile, Invader, Shield)):
                node.kill()
        self.walk(remove_nodes)
        self.create_invaders()
        self.create_shields()
        self.player_ship.kill()
        self.player_ship = self.player_ship_class(world=self, position=self.initial_player_ship_position())
        self._batch.add(self.player_ship)

    def step(self):
        """Perform one environment update step."""
        if self._lives <= 0:
            self.reset_world()
        self._terminal = False
        self._step += 1

        def collect_invaders(node):
            if isinstance(node, self.invader_class):
                return node
        invaders = self.walk(collect_invaders)
        n_invaders = len(invaders)
        if invaders:
            invader = invaders[self.np_random.randint(0, n_invaders)]
            self.fire_missile(invader, self.parameters_invader_missile)
        self.adjust_invader_missiles(n_invaders)
        super(SpaceInvadersWorld, self).step()
        if self._lives <= 0 or not n_invaders:
            self._terminal = True

def create_world(self, parent):
    p_width = self._width / self.physical_scale
    p_height = self._height / self.physical_scale
    ground = self._engine.CreateStaticBody(position=(0, 0))
    ground.CreateEdgeFixture(vertices=[(0, 0), (0, p_height)])
    ground.CreateEdgeFixture(vertices=[(0, 0), (p_width, 0)])
    ground.CreateEdgeFixture(vertices=[(0, p_height), (p_width, p_height)])
    ground.CreateEdgeFixture(vertices=[(p_width, p_height), (p_width, 0)])
    self._ground = ground
    self.create_invaders()
    self.create_shields()
    self.player_ship = self.player_ship_class(world=self, position=self.initial_player_ship_position())
    parent.add(self.player_ship)

def create_shields(self):
    """Create protective shields."""
    for config in self.initial_shield_configuration():
        shield = self.shield_class(world=self, **config)
        self._batch.add(shield)

def fire_missile(self, entity, parameters):

    def count_missiles(node):
        if not isinstance(node, parameters['class']):
            return
        return 1
    if sum(self.walk(count_missiles)) >= parameters['max_missiles']:
        return
    last_fire_step = self._last_fire_step.get(parameters['class'], 0)
    if self._step - last_fire_step <= parameters['fire_rate']:
        return
    self._last_fire_step[parameters['class']] = self._step
    missile = parameters['class'].fire(world=self, entity=entity, impulse=parameters['missile_impulse'])
    self._batch.add(missile)

def reset_world(self):
    """Reset the game."""
    super(SpaceInvadersWorld, self).reset_world()
    self._lives = 3
    self._score = 0
    self._step = 0
    self._last_fire_step = {}

    def remove_nodes(node):
        if isinstance(node, (Missile, Invader, Shield)):
            node.kill()
    self.walk(remove_nodes)
    self.create_invaders()
    self.create_shields()
    self.player_ship.kill()
    self.player_ship = self.player_ship_class(world=self, position=self.initial_player_ship_position())
    self._batch.add(self.player_ship)

class SideObstacleSpaceInvadersWorld(SpaceInvadersWorld):

    def create_world(self, parent):
        super(SideObstacleSpaceInvadersWorld, self).create_world(parent)
        self.obstacle1 = SideObstacle(world=self, position=(10, self._height / 2))
        parent.add(self.obstacle1, z=1)
        self.obstacle2 = SideObstacle(world=self, position=(self._width - 10, self._height / 2))
        parent.add(self.obstacle2, z=1)

def create_world(self, parent):
    super(SideObstacleSpaceInvadersWorld, self).create_world(parent)
    self.obstacle1 = SideObstacle(world=self, position=(10, self._height / 2))
    parent.add(self.obstacle1, z=1)
    self.obstacle2 = SideObstacle(world=self, position=(self._width - 10, self._height / 2))
    parent.add(self.obstacle2, z=1)

class LeftSideObstacleSpaceInvadersWorld(SpaceInvadersWorld):

    def create_world(self, parent):
        super(LeftSideObstacleSpaceInvadersWorld, self).create_world(parent)
        self.obstacle = SideObstacle(world=self, position=(10, self._height / 2))
        parent.add(self.obstacle, z=1)

def create_world(self, parent):
    super(LeftSideObstacleSpaceInvadersWorld, self).create_world(parent)
    self.obstacle = SideObstacle(world=self, position=(10, self._height / 2))
    parent.add(self.obstacle, z=1)

class RightSideObstacleSpaceInvadersWorld(SpaceInvadersWorld):

    def create_world(self, parent):
        super(RightSideObstacleSpaceInvadersWorld, self).create_world(parent)
        self.obstacle = SideObstacle(world=self, position=(self._width - 10, self._height / 2))
        parent.add(self.obstacle, z=1)

def create_world(self, parent):
    super(RightSideObstacleSpaceInvadersWorld, self).create_world(parent)
    self.obstacle = SideObstacle(world=self, position=(self._width - 10, self._height / 2))
    parent.add(self.obstacle, z=1)

class RandomSideObstacleSpaceInvadersWorld(SpaceInvadersWorld):

    def reset_world(self):
        super(RandomSideObstacleSpaceInvadersWorld, self).reset_world()
        self.reset_obstacle()

    def reset_obstacle(self):
        """Reset obstacle width and position."""
        if hasattr(self, 'obstacle'):
            self.obstacle.kill()
        side = self.np_random.choice(['left', 'right'])
        width = int(self.np_random.uniform(-8, 2))
        if side == 'left':
            x = width
        elif side == 'right':
            x = self._width - width
        self.obstacle = SideObstacle(world=self, position=(x, self._height / 2))
        self._batch.add(self.obstacle, z=1)

def reset_obstacle(self):
    """Reset obstacle width and position."""
    if hasattr(self, 'obstacle'):
        self.obstacle.kill()
    side = self.np_random.choice(['left', 'right'])
    width = int(self.np_random.uniform(-8, 2))
    if side == 'left':
        x = width
    elif side == 'right':
        x = self._width - width
    self.obstacle = SideObstacle(world=self, position=(x, self._height / 2))
    self._batch.add(self.obstacle, z=1)

class PhysicalWorld(cocos.layer.Layer):
    """Physical world, which may be rendered."""
    fps = 50
    physical_scale = 32.0
    n_actions = 0

    def __init__(self, width, height):
        super(PhysicalWorld, self).__init__()
        self._contacts = ContactListener()
        self._filter = ContactFilter()
        self._engine = box_2d.b2World(gravity=(0, 0), contactListener=self._contacts, contactFilter=self._filter)
        self._width, self._height = (width, height)
        self._destroy_queue = []
        self.add(cocos.layer.ColorLayer(0, 0, 0, 255))
        self._batch = cocos.batch.BatchNode()
        self.add(self._batch)
        self.seed()
        self.create_world(self._batch)
        self.reset_world()
        self._terminal = False

    def create_world(self, parent):
        """Create the physical world."""
        raise NotImplementedError

    def reset_world(self):
        """Reset the world."""
        self._terminal = False

    def act(self, action):
        """Perform an external action in the world."""
        pass

    def seed(self, seed=None):
        """Setup random number generator."""
        self.np_random, seed = seeding.np_random(seed)
        return seed

    @property
    def is_terminal(self):
        return self._terminal

    @property
    def engine(self):
        """Physics engine world."""
        return self._engine

    @property
    def ground(self):
        """Ground body."""
        return self._ground

    @property
    def parameters(self):
        """World-defining parameters."""
        return {}

    def destroy_body(self, body):
        """Queue specific body for destruction."""
        self._destroy_queue.append(body)

    def process_destroy_queue(self):
        """Process any pending object destructions."""
        for body in self._destroy_queue:
            self._engine.DestroyBody(body)
        self._destroy_queue = []

    def step(self):
        """Perform one simulation step."""
        self.process_destroy_queue()
        self._engine.Step(1.0 / self.fps, 6 * 30, 2 * 30)
        self._engine.ClearForces()

        def step_node(node):
            if not isinstance(node, PhysicalObject):
                return
            node.step()
        self.walk(step_node)

def __init__(self, width, height):
    super(PhysicalWorld, self).__init__()
    self._contacts = ContactListener()
    self._filter = ContactFilter()
    self._engine = box_2d.b2World(gravity=(0, 0), contactListener=self._contacts, contactFilter=self._filter)
    self._width, self._height = (width, height)
    self._destroy_queue = []
    self.add(cocos.layer.ColorLayer(0, 0, 0, 255))
    self._batch = cocos.batch.BatchNode()
    self.add(self._batch)
    self.seed()
    self.create_world(self._batch)
    self.reset_world()
    self._terminal = False

def step(self):
    """Perform one simulation step."""
    self.process_destroy_queue()
    self._engine.Step(1.0 / self.fps, 6 * 30, 2 * 30)
    self._engine.ClearForces()

    def step_node(node):
        if not isinstance(node, PhysicalObject):
            return
        node.step()
    self.walk(step_node)

class BreakoutWorld(PhysicalWorld):
    paddle_class = Paddle
    brick_class = Brick
    ball_class = Ball
    n_actions = 3

    def create_world(self, parent):
        p_width = self._width / self.physical_scale
        p_height = self._height / self.physical_scale
        ground = self._engine.CreateStaticBody(position=(0, 0))
        ground.CreateEdgeFixture(vertices=[(0, 0), (0, p_height)])
        ground.CreateEdgeFixture(vertices=[(0, p_height), (p_width, p_height)])
        ground.CreateEdgeFixture(vertices=[(p_width, p_height), (p_width, 0)])
        self._ground = ground
        self.ball = self.ball_class(world=self, position=self.initial_ball_position())
        parent.add(self.ball)
        self.paddle = self.paddle_class(world=self, position=self.initial_paddle_position())
        parent.add(self.paddle)

    @property
    def lives(self):
        return self._lives

    @property
    def score(self):
        return self._score

    @property
    def parameters(self):
        parameters = super(BreakoutWorld, self).parameters
        parameters.update({'world': 'breakout'})
        return parameters

    def paddle_impulse(self):
        """Relative paddle impulse strength on movement actions."""
        return 50

    def act(self, action):
        """Perform external action."""
        if action == 0:
            pass
        elif action == 1:
            self.paddle.apply_impulse((-self.paddle_impulse() / self.physical_scale * self.paddle.body.mass, 0))
        elif action == 2:
            self.paddle.apply_impulse((self.paddle_impulse() / self.physical_scale * self.paddle.body.mass, 0))

    def initial_ball_position(self):
        """Initial ball position after reset."""
        return (self._width / 2, self._height / 2)

    def initial_paddle_position(self):
        """Initial paddle position after reset."""
        return (self._width / 2, 25)

    def initial_paddle_rotation(self):
        """Initial paddle rotation after reset (in degrees)."""
        return 0

    def initial_brick_position(self):
        """Initial brick row offset after reset."""
        return 40

    def create_bricks(self):
        """Create bricks."""
        dummy = self.brick_class(row=0, column=0)
        brick_x = dummy.width / 2
        brick_y = self._height - self.initial_brick_position()
        for row in range(5):
            for column in range(self._width // dummy.width):
                brick = self.brick_class(world=self, position=(brick_x, brick_y), row=row, column=column)
                self._batch.add(brick)
                brick_x += dummy.width
            brick_x = dummy.width / 2
            brick_y -= dummy.height

    def reset_world(self):
        """Reset the game."""
        super(BreakoutWorld, self).reset_world()
        self._lives = 5
        self._score = 0

        def remove_bricks(node):
            if not isinstance(node, self.brick_class):
                return
            node.kill()
        self.walk(remove_bricks)
        self.create_bricks()
        self.reset_paddle()
        self.reset_ball()

    def reset_paddle(self):
        """Reset paddle."""
        self.paddle.kill()
        self.paddle = self.paddle_class(world=self, position=self.initial_paddle_position(), rotation=self.initial_paddle_rotation())
        self._batch.add(self.paddle)

    def reset_ball(self):
        """Reset ball position."""
        self.ball.stop_body()
        self.ball.set_body_position(self.initial_ball_position())
        self.ball.apply_impulse(150.0 / self.physical_scale * self.ball.body.mass * np.asarray([self.np_random.uniform(-0.3, 0.3), -self.np_random.uniform(0.6, 1.0)]))

    def step(self):
        """Perform one environment update step."""
        if self._lives <= 0:
            self.reset_world()
        self._terminal = False
        super(BreakoutWorld, self).step()
        if self.ball.position[1] < 0:
            self.reset_ball()
            self._lives -= 1
            if self._lives <= 0:
                self._terminal = True

        def count_bricks(node):
            if not isinstance(node, self.brick_class):
                return
            return 1
        if not sum(self.walk(count_bricks)):
            self._terminal = True

def create_world(self, parent):
    p_width = self._width / self.physical_scale
    p_height = self._height / self.physical_scale
    ground = self._engine.CreateStaticBody(position=(0, 0))
    ground.CreateEdgeFixture(vertices=[(0, 0), (0, p_height)])
    ground.CreateEdgeFixture(vertices=[(0, p_height), (p_width, p_height)])
    ground.CreateEdgeFixture(vertices=[(p_width, p_height), (p_width, 0)])
    self._ground = ground
    self.ball = self.ball_class(world=self, position=self.initial_ball_position())
    parent.add(self.ball)
    self.paddle = self.paddle_class(world=self, position=self.initial_paddle_position())
    parent.add(self.paddle)

def create_bricks(self):
    """Create bricks."""
    dummy = self.brick_class(row=0, column=0)
    brick_x = dummy.width / 2
    brick_y = self._height - self.initial_brick_position()
    for row in range(5):
        for column in range(self._width // dummy.width):
            brick = self.brick_class(world=self, position=(brick_x, brick_y), row=row, column=column)
            self._batch.add(brick)
            brick_x += dummy.width
        brick_x = dummy.width / 2
        brick_y -= dummy.height

def reset_world(self):
    """Reset the game."""
    super(BreakoutWorld, self).reset_world()
    self._lives = 5
    self._score = 0

    def remove_bricks(node):
        if not isinstance(node, self.brick_class):
            return
        node.kill()
    self.walk(remove_bricks)
    self.create_bricks()
    self.reset_paddle()
    self.reset_ball()

def reset_paddle(self):
    """Reset paddle."""
    self.paddle.kill()
    self.paddle = self.paddle_class(world=self, position=self.initial_paddle_position(), rotation=self.initial_paddle_rotation())
    self._batch.add(self.paddle)

def step(self):
    """Perform one environment update step."""
    if self._lives <= 0:
        self.reset_world()
    self._terminal = False
    super(BreakoutWorld, self).step()
    if self.ball.position[1] < 0:
        self.reset_ball()
        self._lives -= 1
        if self._lives <= 0:
            self._terminal = True

    def count_bricks(node):
        if not isinstance(node, self.brick_class):
            return
        return 1
    if not sum(self.walk(count_bricks)):
        self._terminal = True

class ObstacleBreakoutWorld(BreakoutWorld):

    def create_world(self, parent):
        super(ObstacleBreakoutWorld, self).create_world(parent)
        self.obstacle = Obstacle(world=self, position=self.obstacle_position())
        parent.add(self.obstacle)

    def obstacle_position(self):
        """Position of the obstacle."""
        return (self._width / 2, 340)

def create_world(self, parent):
    super(ObstacleBreakoutWorld, self).create_world(parent)
    self.obstacle = Obstacle(world=self, position=self.obstacle_position())
    parent.add(self.obstacle)

class SideObstacleBreakoutWorld(BreakoutWorld):

    def create_world(self, parent):
        super(SideObstacleBreakoutWorld, self).create_world(parent)
        self.obstacle1 = SideObstacle(world=self, position=(10, self._height / 2))
        parent.add(self.obstacle1, z=1)
        self.obstacle2 = SideObstacle(world=self, position=(self._width - 10, self._height / 2))
        parent.add(self.obstacle2, z=1)

def create_world(self, parent):
    super(SideObstacleBreakoutWorld, self).create_world(parent)
    self.obstacle1 = SideObstacle(world=self, position=(10, self._height / 2))
    parent.add(self.obstacle1, z=1)
    self.obstacle2 = SideObstacle(world=self, position=(self._width - 10, self._height / 2))
    parent.add(self.obstacle2, z=1)

class LeftSideObstacleBreakoutWorld(BreakoutWorld):

    def create_world(self, parent):
        super(LeftSideObstacleBreakoutWorld, self).create_world(parent)
        self.obstacle = SideObstacle(world=self, position=(10, self._height / 2))
        parent.add(self.obstacle, z=1)

def create_world(self, parent):
    super(LeftSideObstacleBreakoutWorld, self).create_world(parent)
    self.obstacle = SideObstacle(world=self, position=(10, self._height / 2))
    parent.add(self.obstacle, z=1)

class RightSideObstacleBreakoutWorld(BreakoutWorld):

    def create_world(self, parent):
        super(RightSideObstacleBreakoutWorld, self).create_world(parent)
        self.obstacle = SideObstacle(world=self, position=(self._width - 10, self._height / 2))
        parent.add(self.obstacle, z=1)

def create_world(self, parent):
    super(RightSideObstacleBreakoutWorld, self).create_world(parent)
    self.obstacle = SideObstacle(world=self, position=(self._width - 10, self._height / 2))
    parent.add(self.obstacle, z=1)

class RandomSideObstacleBreakoutWorld(BreakoutWorld):
    side_obstacle_width_range_start = 0
    side_obstacle_width_range_end = 20

    def reset_world(self):
        super(RandomSideObstacleBreakoutWorld, self).reset_world()
        self.reset_obstacle()

    def reset_obstacle(self):
        """Reset obstacle width and position."""
        if hasattr(self, 'obstacle'):
            self.obstacle.kill()
        side = self.np_random.choice(['left', 'right'])
        width = int(self.np_random.uniform(self.side_obstacle_width_range_start, self.side_obstacle_width_range_end))
        if side == 'left':
            x = width / 2
        elif side == 'right':
            x = self._width - width / 2
        self.obstacle = SideObstacle(world=self, position=(x, self._height / 2), width=width)
        self._batch.add(self.obstacle, z=1)
        self._obstacle_side = side
        self._obstacle_width = width

    @property
    def parameters(self):
        parameters = super(RandomSideObstacleBreakoutWorld, self).parameters
        parameters.update({'obstacle_side': self._obstacle_side, 'obstacle_width': self._obstacle_width})
        return parameters

def reset_obstacle(self):
    """Reset obstacle width and position."""
    if hasattr(self, 'obstacle'):
        self.obstacle.kill()
    side = self.np_random.choice(['left', 'right'])
    width = int(self.np_random.uniform(self.side_obstacle_width_range_start, self.side_obstacle_width_range_end))
    if side == 'left':
        x = width / 2
    elif side == 'right':
        x = self._width - width / 2
    self.obstacle = SideObstacle(world=self, position=(x, self._height / 2), width=width)
    self._batch.add(self.obstacle, z=1)
    self._obstacle_side = side
    self._obstacle_width = width

