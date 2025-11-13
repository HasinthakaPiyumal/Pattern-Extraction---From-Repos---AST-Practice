# Cluster 13

def get_dim(space):
    if isinstance(space, Box):
        return space.low.size
    elif isinstance(space, Discrete):
        return space.n
    elif isinstance(space, Tuple):
        return sum((get_dim(subspace) for subspace in space.spaces))
    elif hasattr(space, 'flat_dim'):
        return space.flat_dim
    else:
        raise NotImplementedError

class Logger(object):
    DEFAULT = None
    CURRENT = None

    def __init__(self, dir, output_formats, precision=None):
        self.name2val = OrderedDict()
        self.level = INFO
        self.dir = dir
        self.output_formats = output_formats
        self.precision = precision

    def logkv(self, key, val):
        if self.precision is not None and isinstance(val, float):
            self.name2val[key] = round(val, self.precision)
        else:
            self.name2val[key] = val

    def add_figure(self, *args):
        for fmt in self.output_formats:
            if isinstance(fmt, TensorBoardOutputFormat):
                fmt.add_figure(*args)

    def set_tb_step(self, step):
        for fmt in self.output_formats:
            if isinstance(fmt, TensorBoardOutputFormat):
                fmt.set_step(step)

    def dumpkvs(self):
        if self.level == DISABLED:
            return
        for fmt in self.output_formats:
            if isinstance(fmt, KVWriter):
                fmt.writekvs(self.name2val)
        self.name2val.clear()

    def log(self, *args, level=INFO):
        if self.level <= level:
            self._do_log(args)

    def set_level(self, level):
        self.level = level

    def get_dir(self):
        return self.dir

    def close(self):
        for fmt in self.output_formats:
            fmt.close()

    def _do_log(self, args):
        for fmt in self.output_formats:
            if isinstance(fmt, SeqWriter):
                fmt.writeseq(map(str, args))

def set_tb_step(self, step):
    for fmt in self.output_formats:
        if isinstance(fmt, TensorBoardOutputFormat):
            fmt.set_step(step)

def dumpkvs(self):
    if self.level == DISABLED:
        return
    for fmt in self.output_formats:
        if isinstance(fmt, KVWriter):
            fmt.writekvs(self.name2val)
    self.name2val.clear()

class OneHotActionWrapper(gym.Wrapper):
    """Allow to use one-hot action on a discrete action environment."""

    def __init__(self, env):
        super().__init__(env)
        self.env = env

    def step(self, action):
        if not isinstance(action, int):
            action = action.argmax()
        return self.env.step(action)

    def reset(self):
        return self.env.reset()

def step(self, action):
    if not isinstance(action, int):
        action = action.argmax()
    return self.env.step(action)

class InvaderMissile(Missile):
    """Invader's missile."""

    @classmethod
    def fire(cls, world, entity, impulse):
        """Fires a missile."""
        missile = cls(world=world, position=(entity.position[0], entity.position[1] - entity.height - 10))
        missile.apply_impulse((0, -impulse / world.physical_scale * missile.body.mass))
        return missile

    def should_collide(self, other):
        """Ignore collisions with invaders and own missiles."""
        return not isinstance(other, (Invader, InvaderMissile))

    def on_contact(self, other):
        if isinstance(other, PlayerShip):
            self._world._lives -= 1
        self.kill()

def should_collide(self, other):
    """Ignore collisions with invaders and own missiles."""
    return not isinstance(other, (Invader, InvaderMissile))

def on_contact(self, other):
    if isinstance(other, PlayerShip):
        self._world._lives -= 1
    self.kill()

class PlayerMissile(Missile):
    """Player's missile."""

    @classmethod
    def fire(cls, world, entity, impulse):
        """Fires a missile."""
        missile = cls(world=world, position=(entity.position[0], entity.position[1] + entity.height + 10))
        missile.apply_impulse((0, impulse / world.physical_scale * missile.body.mass))
        return missile

    def should_collide(self, other):
        """Ignore collisions with own missiles."""
        return not isinstance(other, PlayerMissile)

    def on_contact(self, other):
        if isinstance(other, (Invader, InvaderMissile)):
            other.kill()
        if isinstance(other, Invader):
            self._world.add_kill_score()
        self.kill()

def should_collide(self, other):
    """Ignore collisions with own missiles."""
    return not isinstance(other, PlayerMissile)

def on_contact(self, other):
    if isinstance(other, (Invader, InvaderMissile)):
        other.kill()
    if isinstance(other, Invader):
        self._world.add_kill_score()
    self.kill()

class Shield(PhysicalObject):
    """Shield for the player."""

    def __init__(self, *args, **kwargs):
        self.health = kwargs.pop('health')
        kwargs.setdefault('color', (255, 240, 0))
        super(Shield, self).__init__('shield.png', *args, **kwargs)

    def create_physical_entity(self):
        body = self._engine.CreateStaticBody(position=self.physical_position)
        body.CreatePolygonFixture(box=(self.width / 2.0 / self._world.physical_scale, self.height / 2.0 / self._world.physical_scale), density=1.0, friction=0.0, restitution=0.0)
        return body

    def on_contact(self, other):
        """Shield loses health if anything touches it."""
        self.health -= 1
        if self.health <= 0:
            self.kill()

def on_contact(self, other):
    """Shield loses health if anything touches it."""
    self.health -= 1
    if self.health <= 0:
        self.kill()

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

def count_missiles(node):
    if not isinstance(node, parameters['class']):
        return
    return 1

def remove_nodes(node):
    if isinstance(node, (Missile, Invader, Shield)):
        node.kill()

def collect_invaders(node):
    if isinstance(node, self.invader_class):
        return node

def uniform_exclude_inner(np_uniform, a, b, a_i, b_i):
    """Draw sample from uniform distribution, excluding an inner range"""
    if not (a < a_i and b_i < b):
        raise ValueError('Bad range, inner: ({},{}), outer: ({},{})'.format(a, b, a_i, b_i))
    while True:
        result = np_uniform(a, b)
        if a <= result and result < a_i or (b_i <= result and result < b):
            return result

class PhysicalObject(cocos.sprite.Sprite):
    """Sprite which is backed by a physical object."""

    def __init__(self, image, **kwargs):
        world = kwargs.pop('world', None)
        super(PhysicalObject, self).__init__(image, **kwargs)
        if world is not None:
            self._world = world
            self._engine = world.engine
            self._body = self.create_physical_entity()
            self._body.userData = self
        else:
            self._world = None
            self._engine = None
            self._body = None

    @property
    def body(self):
        """Physical body."""
        return self._body

    @property
    def physical_position(self):
        """Returns physical object position."""
        if getattr(self, '_body', None) is not None:
            return self._body.position
        return (self.position[0] / self._world.physical_scale, self.position[1] / self._world.physical_scale)

    @property
    def physical_rotation(self):
        """Returns physical object rotation (in radians)."""
        if getattr(self, '_body', None) is not None:
            return self._body.angle
        return -np.deg2rad(self.rotation)

    @property
    def visual_position(self):
        """Return visual object position."""
        if getattr(self, '_body', None) is None:
            return self.position
        return self._body.position * self._world.physical_scale

    @property
    def visual_rotation(self):
        """Return visual object rotation (in degrees)."""
        if getattr(self, '_body', None) is None:
            return self.rotation
        return -np.rad2deg(self._body.angle)

    def set_body_position(self, position):
        """Set object position."""
        self._body.position = (position[0] / self._world.physical_scale, position[1] / self._world.physical_scale)

    def stop_body(self):
        """Stop body movement."""
        self._body.linearVelocity = (0, 0)

    def create_physical_entity(self):
        """Create the entity in the physics engine."""
        raise NotImplementedError

    def step(self):
        """Update actual object based on physical entity."""
        if not self._body:
            return
        self.position = self.visual_position
        self.rotation = self.visual_rotation

    def kill(self):
        """Kill the given object."""
        if not self._body:
            return
        if self._engine is not None:
            self._world.destroy_body(self._body)
            self._body.userData = None
            self._body = None
        super(PhysicalObject, self).kill()

    def apply_impulse(self, vector):
        """Apply linear impulse to center of mass."""
        self._body.ApplyLinearImpulse(vector, self._body.worldCenter, True)

    def on_contact(self, other):
        """Handle contact with another body."""
        pass

    def should_collide(self, other):
        """Handle collision filtering with another body."""
        return True

def kill(self):
    """Kill the given object."""
    if not self._body:
        return
    if self._engine is not None:
        self._world.destroy_body(self._body)
        self._body.userData = None
        self._body = None
    super(PhysicalObject, self).kill()

class Brick(PhysicalObject):
    """Brick object."""

    def __init__(self, *args, **kwargs):
        self.row = kwargs.pop('row')
        self.column = kwargs.pop('column')
        kwargs['color'] = self.get_color()
        super(Brick, self).__init__('brick.png', *args, **kwargs)

    def get_color(self):
        """Brick color."""
        colors = {0: (255, 0, 0), 1: (255, 174, 0), 2: (252, 255, 0), 3: (0, 255, 0), 4: (0, 0, 255)}
        return colors.get(self.row, (0, 0, 0))

    def get_score(self):
        """Score if the brick is destroyed."""
        scores = {0: 10, 1: 7, 2: 5, 3: 3, 4: 1}
        return scores.get(self.row, 0)

    def get_restitution(self):
        restitution = {0: 1.5, 1: 1.3, 2: 1.2, 3: 1.15, 4: 1.1}
        return restitution.get(self.row, 1.0)

    def create_physical_entity(self):
        body = self._engine.CreateStaticBody(position=self.physical_position)
        body.CreatePolygonFixture(box=(self.width / 2.0 / self._world.physical_scale, self.height / 2.0 / self._world.physical_scale), density=1.0, friction=0.0, restitution=self.get_restitution())
        return body

    def on_contact(self, other):
        """Destroy the brick on contact with the ball."""
        if not isinstance(other, Ball):
            return
        self.kill()
        ball_velocity_x = other.body.linearVelocity[0]
        if abs(ball_velocity_x) < 0.2:
            other.apply_impulse([0.2 * np.sign(ball_velocity_x), 0.0])
        self._world._score += self.get_score()

def on_contact(self, other):
    """Destroy the brick on contact with the ball."""
    if not isinstance(other, Ball):
        return
    self.kill()
    ball_velocity_x = other.body.linearVelocity[0]
    if abs(ball_velocity_x) < 0.2:
        other.apply_impulse([0.2 * np.sign(ball_velocity_x), 0.0])
    self._world._score += self.get_score()

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

def remove_bricks(node):
    if not isinstance(node, self.brick_class):
        return
    node.kill()

def count_bricks(node):
    if not isinstance(node, self.brick_class):
        return
    return 1

class KeyToDoor(gym.Env):

    def __init__(self, num_apples=10, apple_reward=1.0, fix_apple_reward_in_episode=True, final_reward=10.0, default_reward=0, respawn_every=20, REWARD_GRID=key_to_door.REWARD_GRID_SR, max_frames=key_to_door.MAX_FRAMES_PER_PHASE_SR, crop=True, flatten_img=True, one_hot_actions=False):
        super().__init__()
        self.pycolab_env = env.PycolabEnvironment(game='key_to_door', num_apples=num_apples, apple_reward=apple_reward, fix_apple_reward_in_episode=fix_apple_reward_in_episode, final_reward=final_reward, respawn_every=respawn_every, crop=crop, default_reward=default_reward, REWARD_GRID=REWARD_GRID, max_frames=max_frames)
        self.action_space = gym.spaces.Discrete(4)
        self.one_hot_actions = one_hot_actions
        self.img_size = (3, 5, 5)
        self.image_space = gym.spaces.Box(shape=self.img_size, low=0, high=255, dtype=np.uint8)
        self.flatten_img = flatten_img
        if flatten_img:
            self.observation_space = gym.spaces.Box(shape=(np.array(self.img_size).prod(),), low=0, high=255, dtype=np.uint8)
        else:
            self.observation_space = self.image_space

    def _convert_obs(self, obs):
        new_obs = np.transpose(obs, (-1, 0, 1))
        if self.flatten_img:
            new_obs = new_obs.flatten()
        return new_obs

    def step(self, action):
        if self.one_hot_actions:
            action = np.argmax(action)
        obs, r = self.pycolab_env.step(action)
        self._ret += r
        info = {}
        if self.pycolab_env._episode.game_over:
            done = True
            info['success'] = self.pycolab_env.last_phase_reward() > 0.0
        else:
            done = False
        return (self._convert_obs(obs), r, done, info)

    def reset(self):
        obs, _ = self.pycolab_env.reset()
        self._ret = 0.0
        return self._convert_obs(obs)

def step(self, action):
    if self.one_hot_actions:
        action = np.argmax(action)
    obs, r = self.pycolab_env.step(action)
    self._ret += r
    info = {}
    if self.pycolab_env._episode.game_over:
        done = True
        info['success'] = self.pycolab_env.last_phase_reward() > 0.0
    else:
        done = False
    return (self._convert_obs(obs), r, done, info)

def reset(self):
    obs, _ = self.pycolab_env.reset()
    self._ret = 0.0
    return self._convert_obs(obs)

class PycolabEnvironment(object):
    """A simple environment adapter for pycolab games."""

    def __init__(self, game, num_apples=10, apple_reward=1.0, fix_apple_reward_in_episode=False, final_reward=10.0, respawn_every=20, crop=True, default_reward=0, REWARD_GRID=key_to_door.REWARD_GRID_SR, max_frames=key_to_door.MAX_FRAMES_PER_PHASE_SR):
        """Construct a `environment.Base` adapter that wraps a pycolab game."""
        rng = np.random.RandomState()
        if game == 'key_to_door':
            self._game = key_to_door.Game(rng=rng, num_apples=num_apples, apple_reward=apple_reward, fix_apple_reward_in_episode=fix_apple_reward_in_episode, final_reward=final_reward, respawn_every=respawn_every, crop=crop, REWARD_GRID=REWARD_GRID, max_frames=max_frames)
        else:
            raise ValueError('Unsupported game "%s".' % game)
        self._default_reward = default_reward
        self._num_actions = self._game.num_actions
        colours = nest.map_structure(lambda c: float(c) * 255 / 1000, self._game.colours)
        self._rgb_converter = rendering.ObservationToArray(value_mapping=colours, permute=(1, 2, 0), dtype=np.uint8)
        episode = self._game.make_episode()
        observation, _, _ = episode.its_showtime()
        self._image_shape = self._rgb_converter(observation).shape

    def _process_outputs(self, observation, reward):
        if reward is None:
            reward = self._default_reward
        image = self._rgb_converter(observation)
        return (image, reward)

    def reset(self):
        """Start a new episode."""
        self._episode = self._game.make_episode()
        observation, reward, _ = self._episode.its_showtime()
        return self._process_outputs(observation, reward)

    def step(self, action):
        """Take step in episode."""
        observation, reward, _ = self._episode.play(action)
        return self._process_outputs(observation, reward)

    @property
    def num_actions(self):
        return self._num_actions

    @property
    def observation_shape(self):
        return self._image_shape

    @property
    def episode_length(self):
        return self._game.episode_length

    def last_phase_reward(self):
        return float(self._episode.the_plot['chapter_reward'])

def __init__(self, game, num_apples=10, apple_reward=1.0, fix_apple_reward_in_episode=False, final_reward=10.0, respawn_every=20, crop=True, default_reward=0, REWARD_GRID=key_to_door.REWARD_GRID_SR, max_frames=key_to_door.MAX_FRAMES_PER_PHASE_SR):
    """Construct a `environment.Base` adapter that wraps a pycolab game."""
    rng = np.random.RandomState()
    if game == 'key_to_door':
        self._game = key_to_door.Game(rng=rng, num_apples=num_apples, apple_reward=apple_reward, fix_apple_reward_in_episode=fix_apple_reward_in_episode, final_reward=final_reward, respawn_every=respawn_every, crop=crop, REWARD_GRID=REWARD_GRID, max_frames=max_frames)
    else:
        raise ValueError('Unsupported game "%s".' % game)
    self._default_reward = default_reward
    self._num_actions = self._game.num_actions
    colours = nest.map_structure(lambda c: float(c) * 255 / 1000, self._game.colours)
    self._rgb_converter = rendering.ObservationToArray(value_mapping=colours, permute=(1, 2, 0), dtype=np.uint8)
    episode = self._game.make_episode()
    observation, _, _ = episode.its_showtime()
    self._image_shape = self._rgb_converter(observation).shape

def _process_outputs(self, observation, reward):
    if reward is None:
        reward = self._default_reward
    image = self._rgb_converter(observation)
    return (image, reward)

def reset(self):
    """Start a new episode."""
    self._episode = self._game.make_episode()
    observation, reward, _ = self._episode.its_showtime()
    return self._process_outputs(observation, reward)

def step(self, action):
    """Take step in episode."""
    observation, reward, _ = self._episode.play(action)
    return self._process_outputs(observation, reward)

class AppleDrape(plab_things.Drape):
    """Drape for the apples used in the distractor phase."""

    def __init__(self, curtain, character, respawn_every, reward, fix_apple_reward_in_episode):
        """Constructor.

        Args:
          curtain: Array specifying locations of apples. Obtained from ascii grid.
          character: Character representing the drape.
          respawn_every: respawn frequency of apples.
          reward: Can either be a scalar specifying the reward or a reward range
            [min, max), given as a list or tuple, to uniformly sample from.
          fix_apple_reward_in_episode: If set to True, then only sample the apple's
            reward once in the episode and then fix the value.
        """
        super(AppleDrape, self).__init__(curtain, character)
        self._respawn_every = respawn_every
        if not isinstance(reward, (list, tuple)):
            self._reward = [reward, reward]
        else:
            if len(reward) != 2:
                raise ValueError('Reward must be a scalar or a two element list/tuple.')
            self._reward = reward
        self._fix_apple_reward_in_episode = fix_apple_reward_in_episode
        self._last_pickup = np.where(curtain, np.inf * np.ones_like(curtain), -1.0 * np.ones_like(curtain))

    def update(self, actions, board, layers, backdrop, things, the_plot):
        player_position = things[PLAYER].position
        if self._fix_apple_reward_in_episode and (not the_plot.get('sampled_apple_reward', None)):
            the_plot['sampled_apple_reward'] = np.random.choice((self._reward[0], self._reward[1]))
        if self.curtain[player_position]:
            self._last_pickup[player_position] = the_plot.frame
            self.curtain[player_position] = False
            if not self._fix_apple_reward_in_episode:
                the_plot.add_reward(np.random.uniform(*self._reward))
            else:
                the_plot.add_reward(the_plot['sampled_apple_reward'])
        if self._respawn_every:
            respawn_cond = the_plot.frame > self._last_pickup + self._respawn_every
            respawn_cond &= self._last_pickup >= 0
            self.curtain[respawn_cond] = True

def __init__(self, curtain, character, respawn_every, reward, fix_apple_reward_in_episode):
    """Constructor.

        Args:
          curtain: Array specifying locations of apples. Obtained from ascii grid.
          character: Character representing the drape.
          respawn_every: respawn frequency of apples.
          reward: Can either be a scalar specifying the reward or a reward range
            [min, max), given as a list or tuple, to uniformly sample from.
          fix_apple_reward_in_episode: If set to True, then only sample the apple's
            reward once in the episode and then fix the value.
        """
    super(AppleDrape, self).__init__(curtain, character)
    self._respawn_every = respawn_every
    if not isinstance(reward, (list, tuple)):
        self._reward = [reward, reward]
    else:
        if len(reward) != 2:
            raise ValueError('Reward must be a scalar or a two element list/tuple.')
        self._reward = reward
    self._fix_apple_reward_in_episode = fix_apple_reward_in_episode
    self._last_pickup = np.where(curtain, np.inf * np.ones_like(curtain), -1.0 * np.ones_like(curtain))

class TimerSprite(plab_things.Sprite):
    """Sprite for the timer.

    The timer is in charge of stopping the current chapter. Timer sprite should be
    placed last in the update order to make sure everything is updated before the
    chapter terminates.
    """

    def __init__(self, corner, position, character, max_frames, track_chapter_reward=False):
        super(TimerSprite, self).__init__(corner, position, character)
        if not isinstance(max_frames, int):
            raise ValueError('max_frames must be of type integer.')
        self._max_frames = max_frames
        self._visible = False
        self._track_chapter_reward = track_chapter_reward
        self._total_chapter_reward = 0.0

    def update(self, actions, board, layers, backdrop, things, the_plot):
        directives = the_plot._get_engine_directives()
        if self._track_chapter_reward:
            self._total_chapter_reward += directives.summed_reward or 0.0
        if the_plot.frame >= self._max_frames or directives.game_over:
            if self._track_chapter_reward:
                the_plot['chapter_reward'] = self._total_chapter_reward
            the_plot.terminate_episode()

def __init__(self, corner, position, character, max_frames, track_chapter_reward=False):
    super(TimerSprite, self).__init__(corner, position, character)
    if not isinstance(max_frames, int):
        raise ValueError('max_frames must be of type integer.')
    self._max_frames = max_frames
    self._visible = False
    self._track_chapter_reward = track_chapter_reward
    self._total_chapter_reward = 0.0

class GridNavi(gym.Env):

    def __init__(self, num_cells=5, num_steps=15, n_tasks=2, modify_init_state_dist=False, is_sparse=False, return_belief_rewards=False, seed=None, **kwargs):
        super(GridNavi, self).__init__()
        if seed is not None:
            self.seed(seed)
        self.n_tasks = n_tasks
        self.num_cells = num_cells
        self.num_states = num_cells ** 2
        self.grid_size = (num_cells, num_cells)
        self.is_sparse = is_sparse
        self.return_belief_rewards = return_belief_rewards
        self.modify_init_state_dist = modify_init_state_dist
        self._max_episode_steps = num_steps
        self.step_count = 0
        self.observation_space = spaces.Box(low=0, high=self.num_cells - 1, shape=(2,), dtype=np.float32)
        self.action_space = spaces.Discrete(5)
        self.starting_states = [(0.0, 0.0)]
        self.states = [(x, y) for y in np.arange(0, num_cells) for x in np.arange(0, num_cells)]
        self.possible_goals = self.states.copy()
        for s in self.starting_states:
            self.possible_goals.remove(s)
        self.possible_goals.remove((0, 1))
        self.possible_goals.remove((1, 1))
        self.possible_goals.remove((1, 0))
        self.num_tasks = min(n_tasks, len(self.possible_goals))
        self.goals = random.sample(self.possible_goals, self.num_tasks)
        self.reset_task(0)
        if self.return_belief_rewards:
            self._belief_state = self._reset_belief()

    def seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        random.seed(seed)
        return [seed]

    def get_all_task_idx(self):
        return range(len(self.goals))

    def get_task(self):
        return self._goal

    def set_goal(self, goal):
        self._goal = np.asarray(goal)

    def reset_task(self, idx=None):
        """reset goal and state"""
        if idx is not None:
            self._goal = np.array(self.goals[idx])
        self.reset()

    def _reset_belief(self):
        self._belief_state = np.zeros(self.num_cells ** 2)
        for pg in self.possible_goals:
            idx = self.task_to_id(np.array(pg))
            self._belief_state[idx] = 1.0 / len(self.possible_goals)
        return self._belief_state

    def reset_model(self):
        if self.modify_init_state_dist:
            self._state = np.array(random.choice(self.states))
            while (self._state == self._goal).all():
                self._state = np.array(random.choice(self.states))
        else:
            self._state = np.array(random.choice(self.starting_states))
        self._belief_state = self._reset_belief()
        return self.get_obs()

    def get_obs(self):
        return np.copy(self._state)

    def update_belief(self, state):
        if self.is_goal_state():
            self._belief_state *= 0
            self._belief_state[self.task_to_id(self._goal)] = 1
        else:
            self._belief_state[self.task_to_id(state)] = 0
            self._belief_state = np.ceil(self._belief_state)
            self._belief_state /= sum(self._belief_state)

    def reset(self):
        self.step_count = 0
        return self.reset_model()

    def reward(self, state, action=None):
        if state[0] == self._goal[0] and state[1] == self._goal[1]:
            return 1.0
        else:
            return 0.0 if self.is_sparse else -0.1

    def state_transition(self, action):
        """
        Moving the agent between states
        """
        if action == 1:
            self._state[1] = min([self._state[1] + 1, self.num_cells - 1])
        elif action == 2:
            self._state[0] = min([self._state[0] + 1, self.num_cells - 1])
        elif action == 3:
            self._state[1] = max([self._state[1] - 1, 0])
        elif action == 4:
            self._state[0] = max([self._state[0] - 1, 0])

    def step(self, action):
        if isinstance(action, np.ndarray) and action.ndim == 1:
            action = action[0]
        assert self.action_space.contains(action)
        info = {'task': self.get_task()}
        done = False
        self.state_transition(action)
        self.step_count += 1
        if self.step_count >= self._max_episode_steps:
            done = True
        if self.return_belief_rewards:
            self.update_belief(self._state)
            belief_reward = self._compute_belief_reward()
            info.update({'belief_reward': belief_reward})
        reward = self.reward(self._state)
        return (self.get_obs(), reward, done, info)

    def _compute_belief_reward(self):
        num_possible_goal_belief = np.sum(self._belief_state != 0)
        non_goal_rew = 0.0 if self.is_sparse else -0.1
        belief_reward = (1.0 + non_goal_rew * (num_possible_goal_belief - 1)) / num_possible_goal_belief
        return belief_reward

    def is_goal_state(self):
        if self._state[0] == self._goal[0] and self._state[1] == self._goal[1]:
            return True
        else:
            return False

    def task_to_id(self, goals):
        mat = torch.arange(0, self.num_cells ** 2).long().reshape((self.num_cells, self.num_cells)).transpose(1, 0)
        if isinstance(goals, list) or isinstance(goals, tuple):
            goals = np.array(goals)
        if isinstance(goals, np.ndarray):
            goals = torch.from_numpy(goals)
        goals = goals.long()
        if goals.dim() == 1:
            goals = goals.unsqueeze(0)
        goal_shape = goals.shape
        if len(goal_shape) > 2:
            goals = goals.reshape(-1, goals.shape[-1])
        classes = mat[goals[:, 0], goals[:, 1]]
        classes = classes.reshape(goal_shape[:-1])
        return classes

    def id_to_task(self, classes):
        mat = torch.arange(0, self.num_cells ** 2).long().reshape((self.num_cells, self.num_cells)).numpy().T
        goals = np.zeros((len(classes), 2))
        classes = classes.numpy()
        for i in range(len(classes)):
            pos = np.where(classes[i] == mat)
            goals[i, 0] = float(pos[0][0])
            goals[i, 1] = float(pos[1][0])
        goals = torch.from_numpy(goals).to(ptu.device).float()
        return goals

    def goal_to_onehot_id(self, pos):
        cl = self.task_to_id(pos)
        if cl.dim() == 1:
            cl = cl.view(-1, 1)
        nb_digits = self.num_cells ** 2
        y_onehot = torch.FloatTensor(pos.shape[0], nb_digits).to(ptu.device)
        y_onehot.zero_()
        y_onehot.scatter_(1, cl, 1)
        return y_onehot

    def onehot_id_to_goal(self, pos):
        if isinstance(pos, list):
            pos = [self.id_to_task(p.argmax(dim=1)) for p in pos]
        else:
            pos = self.id_to_task(pos.argmax(dim=1))
        return pos

    def render(self, mode='human'):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError

    def plot_env(self):
        for i in range(self.num_cells):
            for j in range(self.num_cells):
                pos_i = i
                pos_j = j
                rec = Rectangle((pos_i, pos_j), 1, 1, facecolor='none', alpha=0.5, edgecolor='k')
                plt.gca().add_patch(rec)
        goal = np.array(self._goal) + 0.5
        plt.plot(goal[0], goal[1], 'kx')
        plt.plot(goal[0], goal[1], 'kx')

    def plot_behavior(self, observations, plot_env=True, **kwargs):
        if plot_env:
            self.plot_env()
        if isinstance(observations, tuple) or isinstance(observations, list):
            observations = torch.cat(observations)
        observations = observations + 0.5
        plt.plot(observations[:, 0], observations[:, 1], **kwargs)
        plt.plot(observations[-1, 0], observations[-1, 1], **kwargs)
        plt.xticks([])
        plt.yticks([])
        plt.xlim([0, self.num_cells])
        plt.ylim([0, self.num_cells])
        plt.axis('equal')

def onehot_id_to_goal(self, pos):
    if isinstance(pos, list):
        pos = [self.id_to_task(p.argmax(dim=1)) for p in pos]
    else:
        pos = self.id_to_task(pos.argmax(dim=1))
    return pos

