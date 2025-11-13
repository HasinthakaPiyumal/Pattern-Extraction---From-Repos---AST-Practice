# Cluster 4

class DictWrapper(gym.ObservationWrapper):

    def __init__(self, env):
        super().__init__(env)

    def observation(self, obs_img):
        if len(obs_img.shape) == 1:
            return {'vecobs': obs_img}
        else:
            return {'image': obs_img}

def __init__(self, env):
    super().__init__(env)

class TimeLimitWrapper(gym.Wrapper):

    def __init__(self, env, time_limit):
        super().__init__(env)
        self._max_episode_steps = time_limit

    def step(self, action):
        obs, reward, done, info = self.env.step(action)
        self.step_ += 1
        if self.step_ >= self._max_episode_steps:
            done = True
            info['TimeLimit.truncated'] = True
        return (obs, reward, done, info)

    def reset(self):
        self.step_ = 0
        return self.env.reset()

def __init__(self, env, time_limit):
    super().__init__(env)
    self._max_episode_steps = time_limit

def reset(self):
    self.step_ = 0
    return self.env.reset()

class CollectWrapper(gym.Wrapper):

    def __init__(self, env):
        super().__init__(env)
        self.env = env
        self.episode = []

    def step(self, action):
        obs, reward, done, info = self.env.step(action)
        self.episode.append(obs.copy())
        if done:
            episode = {k: np.array([t[k] for t in self.episode]) for k in self.episode[0]}
            info['episode'] = episode
        return (obs, reward, done, info)

    def reset(self):
        obs = self.env.reset()
        self.episode = [obs.copy()]
        return obs

def __init__(self, env):
    super().__init__(env)
    self.env = env
    self.episode = []

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

def __init__(self, env):
    super().__init__(env)
    self.env = env

def reset(self):
    return self.env.reset()

class VizDoomEnvironment(gym.Env):
    metadata = {'render.modes': ['rgb_array'], 'video.frames_per_second': 35}
    scenarios = {'basic': {'baseline': {'scenario': 'basic.wad', 'living_reward': 1, 'death_penalty': 0, 'reward': 'health'}, 'floor_ceiling_flipped': {'scenario': 'basic_floor_ceiling_flipped.wad'}, 'torches': {'scenario': 'basic_torches.wad'}, 'random_textures_set_a': {'sampler': sample_textures(TEXTURES_SET_A)}, 'random_textures_set_b': {'sampler': sample_textures(TEXTURES_SET_B)}, 'random_things_set_a': {'scenario': 'basic_torches.wad', 'sampler': sample_things(THINGS_SET_A, modify_things=[56])}, 'random_things_set_b': {'scenario': 'basic_torches.wad', 'sampler': sample_things(THINGS_SET_B, modify_things=[56])}}, 'navigation': {'baseline': {'scenario': 'navigation.wad', 'living_reward': 1, 'death_penalty': 0, 'reward': 'health'}, 'new_layout': {'scenario': 'navigation_new_layout.wad'}, 'floor_ceiling_flipped': {'scenario': 'navigation_floor_ceiling_flipped.wad'}, 'torches': {'scenario': 'navigation_torches.wad'}, 'random_textures_set_a': {'sampler': sample_textures(TEXTURES_SET_A)}, 'random_textures_set_b': {'sampler': sample_textures(TEXTURES_SET_B)}, 'random_things_set_a': {'scenario': 'navigation_torches.wad', 'sampler': sample_things(THINGS_SET_A, modify_things=[56])}, 'random_things_set_b': {'scenario': 'navigation_torches.wad', 'sampler': sample_things(THINGS_SET_B, modify_things=[56])}}}
    buttons = [vizdoom.Button.MOVE_FORWARD, vizdoom.Button.MOVE_BACKWARD, vizdoom.Button.MOVE_RIGHT, vizdoom.Button.MOVE_LEFT, vizdoom.Button.TURN_LEFT, vizdoom.Button.TURN_RIGHT, vizdoom.Button.ATTACK, vizdoom.Button.SPEED]
    opposite_button_pairs = [(vizdoom.Button.MOVE_FORWARD, vizdoom.Button.MOVE_BACKWARD), (vizdoom.Button.MOVE_RIGHT, vizdoom.Button.MOVE_LEFT), (vizdoom.Button.TURN_LEFT, vizdoom.Button.TURN_RIGHT)]

    def __init__(self, scenario, variant, obs_type='image', frameskip=4):
        if scenario not in self.scenarios:
            raise error.Error('Unsupported scenario: {}'.format(scenario))
        if variant not in self.scenarios[scenario]:
            raise error.Error('Unsupported scenario variant: {}'.format(variant))
        config = {}
        config.update(self.scenarios[scenario]['baseline'])
        config.update(self.scenarios[scenario][variant])
        self._config = config
        self._vizdoom = vizdoom.DoomGame()
        self._vizdoom.set_doom_scenario_path(os.path.join(ASSET_PATH, config['scenario']))
        self._vizdoom.set_doom_map(config.get('map', 'MAP01'))
        self._vizdoom.set_screen_resolution(vizdoom.ScreenResolution.RES_640X480)
        self._vizdoom.set_screen_format(vizdoom.ScreenFormat.BGR24)
        self._vizdoom.set_mode(vizdoom.Mode.PLAYER)
        self._width = 640
        self._height = 480
        self._depth = 3
        self._vizdoom.set_render_hud(False)
        self._vizdoom.set_render_minimal_hud(False)
        self._vizdoom.set_render_crosshair(False)
        self._vizdoom.set_render_weapon(False)
        self._vizdoom.set_render_decals(False)
        self._vizdoom.set_render_particles(False)
        self._vizdoom.set_render_effects_sprites(False)
        self._vizdoom.set_render_messages(False)
        self._vizdoom.set_render_corpses(False)
        self._vizdoom.set_window_visible(False)
        self._vizdoom.set_sound_enabled(False)
        self._vizdoom.set_living_reward(config.get('living_reward', 1))
        self._vizdoom.set_death_penalty(config.get('death_penalty', 100))
        self._vizdoom.set_episode_timeout(config.get('episode_timeout', 2100))
        for button in self.buttons:
            self._vizdoom.add_available_button(button)
        self._action_button_map = []
        for combination in itertools.product([False, True], repeat=len(self.buttons)):
            valid = True
            for a, b in self.opposite_button_pairs:
                if combination[self.buttons.index(a)] and combination[self.buttons.index(b)]:
                    valid = False
                    break
            if valid:
                self._action_button_map.append(list(combination))
        self.action_space = spaces.Discrete(len(self._action_button_map))
        if obs_type == 'image':
            self.observation_space = spaces.Box(low=0, high=255, shape=(self._height, self._width, self._depth))
        else:
            raise error.Error('Unrecognized observation type: {}'.format(obs_type))
        self._scenario = scenario
        self._variant = variant
        self._obs_type = obs_type
        self._frameskip = frameskip
        self._initialized = False
        self._temporary_scenario = None
        self._seed()

    def __getstate__(self):
        return {'scenario': self._scenario, 'variant': self._variant, 'obs_type': self._obs_type, 'frameskip': self._frameskip}

    def __setstate__(self, state):
        self.__init__(**state)

    def _seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        self._vizdoom.set_seed(seed % 2 ** 32)
        return [seed]

    def _get_observation(self):
        state = self._vizdoom.get_state()
        if self._obs_type == 'image':
            if not state:
                return np.zeros([self._height, self._width, self._depth])
            return state.screen_buffer
        raise NotImplementedError

    def _reset(self):
        sampler = self._config.get('sampler', None)
        if sampler:
            if self._temporary_scenario:
                try:
                    os.remove(self._temporary_scenario)
                except OSError:
                    pass
                self._temporary_scenario = None
            self._temporary_scenario = sampler(self, self._config)
            self._vizdoom.set_doom_scenario_path(self._temporary_scenario)
        if not self._initialized:
            self._vizdoom.init()
            self._initialized = True
        self._vizdoom.new_episode()
        return self._get_observation()

    def _get_state_variables(self):
        return {'health': self._vizdoom.get_game_variable(vizdoom.GameVariable.HEALTH), 'frags': self._vizdoom.get_game_variable(vizdoom.GameVariable.FRAGCOUNT)}

    def _step(self, action):
        previous_info = self._get_state_variables()
        action = self._action_button_map[action]
        scenario_reward = self._vizdoom.make_action(action, self._frameskip)
        terminal = self._vizdoom.is_episode_finished() or self._vizdoom.is_player_dead()
        observation = self._get_observation()
        info = self._get_state_variables()
        reward_value = self._config.get('reward', 'reward')
        if reward_value == 'reward':
            reward = scenario_reward
        else:
            reward = info[reward_value] - previous_info[reward_value]
        return (observation, reward, terminal, info)

    def get_keys_to_action(self):
        return {(): 0}

def __setstate__(self, state):
    self.__init__(**state)

class Missile(PhysicalObject):
    """Missile."""

    def __init__(self, *args, **kwargs):
        super(Missile, self).__init__('missile.png', *args, **kwargs)

    def create_physical_entity(self):
        body = self._engine.CreateDynamicBody(position=self.physical_position, fixedRotation=True)
        body.CreatePolygonFixture(box=(self.width / 2.0 / self._world.physical_scale, self.height / 2.0 / self._world.physical_scale), density=1.0, friction=0.0, restitution=0.0)
        joint = box_2d.b2PrismaticJointDef()
        joint.Initialize(body, self._world.ground, body.worldCenter, (0.0, 1.0))
        joint.collideConnected = True
        self._engine.CreateJoint(joint)
        return body

    @classmethod
    def fire(cls, world, entity, impulse):
        """Fires a missile."""
        raise NotImplementedError

def __init__(self, *args, **kwargs):
    super(Missile, self).__init__('missile.png', *args, **kwargs)

class Invader(PhysicalObject):
    """Invader."""
    TYPE_1 = 'invader_1'
    TYPE_2 = 'invader_2'
    TYPE_3 = 'invader_3'

    def __init__(self, *args, **kwargs):
        self._type = kwargs.pop('invader_type')
        kwargs.setdefault('color', (0, 255, 0))
        kwargs.setdefault('scale', 1)
        super(Invader, self).__init__('{}.png'.format(self._type), *args, **kwargs)

    def create_physical_entity(self):
        body = self._engine.CreateStaticBody(position=self.physical_position)
        body.CreatePolygonFixture(box=(self.width / 2.0 / self._world.physical_scale, self.height / 2.0 / self._world.physical_scale), density=1.0, friction=0.0, restitution=0.0)
        return body

def __init__(self, *args, **kwargs):
    self._type = kwargs.pop('invader_type')
    kwargs.setdefault('color', (0, 255, 0))
    kwargs.setdefault('scale', 1)
    super(Invader, self).__init__('{}.png'.format(self._type), *args, **kwargs)

class LeftRightMovingInvader(Invader):
    """Invader which moves left and right."""
    max_delta_x = 24

    def __init__(self, *args, **kwargs):
        super(LeftRightMovingInvader, self).__init__(*args, **kwargs)
        self._direction = 1
        self._initial_x = self.position[0]

    def step(self):
        if self.position[0] - self._initial_x >= self.max_delta_x:
            self._direction = -1
        elif self.position[0] - self._initial_x <= -self.max_delta_x:
            self._direction = 1
        self.set_body_position((self.position[0] + self._direction, self.position[1]))
        super(LeftRightMovingInvader, self).step()

def __init__(self, *args, **kwargs):
    super(LeftRightMovingInvader, self).__init__(*args, **kwargs)
    self._direction = 1
    self._initial_x = self.position[0]

class CrossScreenMovingInvader(Invader):
    """Invader which moves across the whole screen."""

    def __init__(self, *args, **kwargs):
        super(CrossScreenMovingInvader, self).__init__(*args, **kwargs)
        self._direction = 1

    def step(self):
        if self.position[0] >= self._world._width - self.width:
            self._direction = -1
        elif self.position[0] <= self.width:
            self._direction = 1
        self.set_body_position((self.position[0] + self._direction, self.position[1]))
        super(CrossScreenMovingInvader, self).step()

def __init__(self, *args, **kwargs):
    super(CrossScreenMovingInvader, self).__init__(*args, **kwargs)
    self._direction = 1

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

def __init__(self, *args, **kwargs):
    self.health = kwargs.pop('health')
    kwargs.setdefault('color', (255, 240, 0))
    super(Shield, self).__init__('shield.png', *args, **kwargs)

class PlayerShip(PhysicalObject):
    """Player ship."""

    def __init__(self, *args, **kwargs):
        super(PlayerShip, self).__init__('ship.png', *args, **kwargs)

    def create_physical_entity(self):
        body = self._engine.CreateDynamicBody(position=self.physical_position, linearDamping=0.99, fixedRotation=True)
        body.CreatePolygonFixture(box=(self.width / 2.0 / self._world.physical_scale, self.height / 2.0 / self._world.physical_scale), density=1.0, friction=0.0, restitution=0.0)
        joint = box_2d.b2PrismaticJointDef()
        joint.Initialize(body, self._world.ground, body.worldCenter, (1.0, 0.0))
        joint.collideConnected = True
        self._engine.CreateJoint(joint)
        return body

def __init__(self, *args, **kwargs):
    super(PlayerShip, self).__init__('ship.png', *args, **kwargs)

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

@property
def parameters(self):
    parameters = super(SpaceInvadersWorld, self).parameters
    parameters.update({'world': 'space_invaders'})
    return parameters

class RandomOffsetPlayerSpaceInvadersWorld(SpaceInvadersWorld):
    offset_range_start = 25
    offset_range_end = 125

    def initial_shield_configuration(self):
        return [{'health': 20, 'position': (self._width // 4, 200)}, {'health': 20, 'position': (2 * self._width // 4, 200)}, {'health': 20, 'position': (3 * self._width // 4, 200)}]

    def initial_player_ship_position(self):
        """Initial player ship position after reset."""
        self._player_offset = int(self.np_random.uniform(self.offset_range_start, self.offset_range_end))
        return (self._width / 2, self._player_offset)

    @property
    def parameters(self):
        parameters = super(RandomOffsetPlayerSpaceInvadersWorld, self).parameters
        parameters.update({'player_offset': self._player_offset})
        return parameters

@property
def parameters(self):
    parameters = super(RandomOffsetPlayerSpaceInvadersWorld, self).parameters
    parameters.update({'player_offset': self._player_offset})
    return parameters

class SideObstacle(PhysicalObject):
    """Side obstacle object."""

    def __init__(self, *args, **kwargs):
        kwargs['color'] = (80, 80, 80)
        super(SideObstacle, self).__init__('side_obstacle.png', *args, **kwargs)

    def create_physical_entity(self):
        body = self._engine.CreateStaticBody(position=self.physical_position)
        body.CreatePolygonFixture(box=(self.width / 2.0 / self._world.physical_scale, self.height / 2.0 / self._world.physical_scale), density=10.0, friction=0.0, restitution=0.0)
        return body

def __init__(self, *args, **kwargs):
    kwargs['color'] = (80, 80, 80)
    super(SideObstacle, self).__init__('side_obstacle.png', *args, **kwargs)

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

def reset_world(self):
    super(RandomSideObstacleSpaceInvadersWorld, self).reset_world()
    self.reset_obstacle()

class WhiteShield(Shield):
    """White shield for the player."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('color', (255, 255, 255))
        super(WhiteShield, self).__init__(*args, **kwargs)

def __init__(self, *args, **kwargs):
    kwargs.setdefault('color', (255, 255, 255))
    super(WhiteShield, self).__init__(*args, **kwargs)

class WhiteLeftRightMovingInvader(LeftRightMovingInvader):
    """White invader which moves left and right."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('color', (255, 255, 255))
        super(WhiteLeftRightMovingInvader, self).__init__(*args, **kwargs)

def __init__(self, *args, **kwargs):
    kwargs.setdefault('color', (255, 255, 255))
    super(WhiteLeftRightMovingInvader, self).__init__(*args, **kwargs)

class Scaled80SpaceInvadersWorld(SpaceInvadersWorld):

    def __init__(self, *args, **kwargs):
        super(Scaled80SpaceInvadersWorld, self).__init__(*args, **kwargs)
        self.scale = 0.8

def __init__(self, *args, **kwargs):
    super(Scaled80SpaceInvadersWorld, self).__init__(*args, **kwargs)
    self.scale = 0.8

class Scaled90SpaceInvadersWorld(SpaceInvadersWorld):

    def __init__(self, *args, **kwargs):
        super(Scaled90SpaceInvadersWorld, self).__init__(*args, **kwargs)
        self.scale = 0.9

def __init__(self, *args, **kwargs):
    super(Scaled90SpaceInvadersWorld, self).__init__(*args, **kwargs)
    self.scale = 0.9

class Scaled95SpaceInvadersWorld(SpaceInvadersWorld):

    def __init__(self, *args, **kwargs):
        super(Scaled95SpaceInvadersWorld, self).__init__(*args, **kwargs)
        self.scale = 0.95

def __init__(self, *args, **kwargs):
    super(Scaled95SpaceInvadersWorld, self).__init__(*args, **kwargs)
    self.scale = 0.95

class Scaled99SpaceInvadersWorld(SpaceInvadersWorld):

    def __init__(self, *args, **kwargs):
        super(Scaled99SpaceInvadersWorld, self).__init__(*args, **kwargs)
        self.scale = 0.99

def __init__(self, *args, **kwargs):
    super(Scaled99SpaceInvadersWorld, self).__init__(*args, **kwargs)
    self.scale = 0.99

class RandomScaledSpaceInvadersWorld(SpaceInvadersWorld):
    scale_range_start = 0.9
    scale_range_end = 1.0

    def reset_world(self):
        super(RandomScaledSpaceInvadersWorld, self).reset_world()
        self.scale = self.np_random.uniform(self.scale_range_start, self.scale_range_end)

    @property
    def parameters(self):
        parameters = super(RandomScaledSpaceInvadersWorld, self).parameters
        parameters.update({'scale': self.scale})
        return parameters

def reset_world(self):
    super(RandomScaledSpaceInvadersWorld, self).reset_world()
    self.scale = self.np_random.uniform(self.scale_range_start, self.scale_range_end)

@property
def parameters(self):
    parameters = super(RandomScaledSpaceInvadersWorld, self).parameters
    parameters.update({'scale': self.scale})
    return parameters

class RandomActionStrengthSpaceInvadersWorld(SpaceInvadersWorld):
    impulse_range_start = 30
    impulse_range_end = 170

    def reset_world(self):
        super(RandomActionStrengthSpaceInvadersWorld, self).reset_world()
        self._impulse_strength = self.np_random.uniform(self.impulse_range_start, self.impulse_range_end)

    def ship_impulse(self):
        return self._impulse_strength

    @property
    def parameters(self):
        parameters = super(RandomActionStrengthSpaceInvadersWorld, self).parameters
        parameters.update({'ship_impulse': self._impulse_strength})
        return parameters

def reset_world(self):
    super(RandomActionStrengthSpaceInvadersWorld, self).reset_world()
    self._impulse_strength = self.np_random.uniform(self.impulse_range_start, self.impulse_range_end)

@property
def parameters(self):
    parameters = super(RandomActionStrengthSpaceInvadersWorld, self).parameters
    parameters.update({'ship_impulse': self._impulse_strength})
    return parameters

class RandomNormalHalfCheetah(RoboschoolXMLModifierMixin, ModifiableRoboschoolHalfCheetah):

    def randomize_env(self):
        self.density = self.np_random.uniform(self.RANDOM_LOWER_DENSITY, self.RANDOM_UPPER_DENSITY)
        self.friction = self.np_random.uniform(self.RANDOM_LOWER_FRICTION, self.RANDOM_UPPER_FRICTION)
        self.power = self.np_random.uniform(self.RANDOM_LOWER_POWER, self.RANDOM_UPPER_POWER)
        with self.modify_xml('half_cheetah.xml') as tree:
            for elem in tree.iterfind('worldbody/body/geom'):
                elem.set('density', str(self.density))
            for elem in tree.iterfind('default/geom'):
                elem.set('friction', str(self.friction) + ' .1 .1')

    def _reset(self, new=True):
        if new:
            self.randomize_env()
        return super()._reset(new)

    @property
    def parameters(self):
        parameters = super().parameters
        parameters.update({'power': self.power, 'density': self.density, 'friction': self.friction})
        return parameters

@property
def parameters(self):
    parameters = super().parameters
    parameters.update({'power': self.power, 'density': self.density, 'friction': self.friction})
    return parameters

class RandomExtremeHalfCheetah(RoboschoolXMLModifierMixin, ModifiableRoboschoolHalfCheetah):

    def randomize_env(self):
        """
        # self.armature = self.np_random.uniform(0.2, 0.5)
        self.density = self.np_random.uniform(self.LOWER_DENSITY, self.UPPER_DENSITY)
        self.friction = self.np_random.uniform(self.LOWER_FRICTION, self.UPPER_FRICTION)
        self.power = self.np_random.uniform(self.LOWER_POWER, self.UPPER_POWER)
        """
        self.density = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_DENSITY, self.EXTREME_UPPER_DENSITY, self.RANDOM_LOWER_DENSITY, self.RANDOM_UPPER_DENSITY)
        self.friction = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_FRICTION, self.EXTREME_UPPER_FRICTION, self.RANDOM_LOWER_FRICTION, self.RANDOM_UPPER_FRICTION)
        self.power = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_POWER, self.EXTREME_UPPER_POWER, self.RANDOM_LOWER_POWER, self.RANDOM_UPPER_POWER)
        with self.modify_xml('half_cheetah.xml') as tree:
            for elem in tree.iterfind('worldbody/body/geom'):
                elem.set('density', str(self.density))
            for elem in tree.iterfind('default/geom'):
                elem.set('friction', str(self.friction) + ' .1 .1')

    def _reset(self, new=True):
        if new:
            self.randomize_env()
        return super()._reset(new)

    @property
    def parameters(self):
        parameters = super().parameters
        parameters.update({'power': self.power, 'density': self.density, 'friction': self.friction})
        return parameters

@property
def parameters(self):
    parameters = super().parameters
    parameters.update({'power': self.power, 'density': self.density, 'friction': self.friction})
    return parameters

class RandomNormalHopper(RoboschoolXMLModifierMixin, ModifiableRoboschoolHopper):

    def randomize_env(self):
        self.density = self.np_random.uniform(self.RANDOM_LOWER_DENSITY, self.RANDOM_UPPER_DENSITY)
        self.friction = self.np_random.uniform(self.RANDOM_LOWER_FRICTION, self.RANDOM_UPPER_FRICTION)
        self.power = self.np_random.uniform(self.RANDOM_LOWER_POWER, self.RANDOM_UPPER_POWER)
        with self.modify_xml('hopper.xml') as tree:
            for elem in tree.iterfind('worldbody/body/geom'):
                elem.set('density', str(self.density))
            for elem in tree.iterfind('default/geom'):
                elem.set('friction', str(self.friction) + ' .1 .1')

    def _reset(self, new=True):
        if new:
            self.randomize_env()
        return super()._reset(new)

    @property
    def parameters(self):
        parameters = super().parameters
        parameters.update({'power': self.power, 'density': self.density, 'friction': self.friction})
        return parameters

@property
def parameters(self):
    parameters = super().parameters
    parameters.update({'power': self.power, 'density': self.density, 'friction': self.friction})
    return parameters

class RandomExtremeHopper(RoboschoolXMLModifierMixin, ModifiableRoboschoolHopper):

    def randomize_env(self):
        """
        self.density = self.np_random.uniform(self.LOWER_DENSITY, self.UPPER_DENSITY)
        self.friction = self.np_random.uniform(self.LOWER_FRICTION, self.UPPER_FRICTION)
        self.power = self.np_random.uniform(self.LOWER_POWER, self.UPPER_POWER)
        """
        self.density = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_DENSITY, self.EXTREME_UPPER_DENSITY, self.RANDOM_LOWER_DENSITY, self.RANDOM_UPPER_DENSITY)
        self.friction = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_FRICTION, self.EXTREME_UPPER_FRICTION, self.RANDOM_LOWER_FRICTION, self.RANDOM_UPPER_FRICTION)
        self.power = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_POWER, self.EXTREME_UPPER_POWER, self.RANDOM_LOWER_POWER, self.RANDOM_UPPER_POWER)
        with self.modify_xml('hopper.xml') as tree:
            for elem in tree.iterfind('worldbody/body/geom'):
                elem.set('density', str(self.density))
            for elem in tree.iterfind('default/geom'):
                elem.set('friction', str(self.friction) + ' .1 .1')

    def _reset(self, new=True):
        if new:
            self.randomize_env()
        return super()._reset(new)

    @property
    def parameters(self):
        parameters = super().parameters
        parameters.update({'power': self.power, 'density': self.density, 'friction': self.friction})
        return parameters

@property
def parameters(self):
    parameters = super().parameters
    parameters.update({'power': self.power, 'density': self.density, 'friction': self.friction})
    return parameters

class RandomNormalWalker2d_MRPO(RoboschoolXMLModifierMixin, ModifiableRoboschoolWalker2d_MRPO):

    def __init__(self, oracle: bool=False, **kwargs):
        super().__init__(**kwargs)
        self.oracle = oracle
        if oracle == True:
            print('WARNING! YOU ARE USING MDP, NOT POMDP!\n')
            self._reset()
            tmp_hidden_states = self.get_hidden_states()
            self.observation_space = spaces.Box(low=np.array([*self.observation_space.low, *[0] * len(tmp_hidden_states)]), high=np.array([*self.observation_space.high, *[1] * len(tmp_hidden_states)]), dtype=np.float32)

    def randomize_env(self):
        self.density = self.np_random.uniform(self.RANDOM_LOWER_DENSITY, self.RANDOM_UPPER_DENSITY)
        self.friction = self.np_random.uniform(self.RANDOM_LOWER_FRICTION, self.RANDOM_UPPER_FRICTION)
        with self.modify_xml('walker2d.xml') as tree:
            for elem in tree.iterfind('default/geom'):
                elem.set('density', str(self.density) + ' .1 .1')
            for elem in tree.iterfind('default/geom'):
                elem.set('friction', str(self.friction) + ' .1 .1')

    def get_obs(self, state):
        if self.oracle:
            hidden_states = self.get_hidden_states()
            state = np.concatenate([state, hidden_states])
            return state
        else:
            return state

    def _reset(self, new=True):
        if new:
            self.randomize_env()
        state = super(RandomNormalWalker2d_MRPO, self)._reset(new)
        return self.get_obs(state)

    def _step(self, a):
        state, reward, done, info = super(RandomNormalWalker2d_MRPO, self)._step(a)
        return (self.get_obs(state), reward, done, info)

    @property
    def parameters(self):
        parameters = super(RandomNormalWalker2d_MRPO, self).parameters
        parameters.update({'density': self.density, 'friction': self.friction})
        return parameters

    def get_hidden_states(self):
        hidden_states = np.array([(self.density - self.RANDOM_LOWER_DENSITY) / (self.RANDOM_UPPER_DENSITY - self.RANDOM_LOWER_DENSITY), (self.friction - self.RANDOM_LOWER_FRICTION) / (self.RANDOM_UPPER_FRICTION - self.RANDOM_LOWER_FRICTION)])
        return hidden_states.copy()

@property
def parameters(self):
    parameters = super(RandomNormalWalker2d_MRPO, self).parameters
    parameters.update({'density': self.density, 'friction': self.friction})
    return parameters

class RandomNormalHalfCheetah_MRPO(RoboschoolXMLModifierMixin, ModifiableRoboschoolHalfCheetah_MRPO):

    def __init__(self, oracle: bool=False, **kwargs):
        super().__init__(**kwargs)
        self.oracle = oracle
        if oracle == True:
            print('WARNING! YOU ARE USING MDP, NOT POMDP!\n')
            self._reset()
            tmp_hidden_states = self.get_hidden_states()
            self.observation_space = spaces.Box(low=np.array([*self.observation_space.low, *[0] * len(tmp_hidden_states)]), high=np.array([*self.observation_space.high, *[1] * len(tmp_hidden_states)]), dtype=np.float32)

    def randomize_env(self):
        self.density = self.np_random.uniform(self.RANDOM_LOWER_DENSITY, self.RANDOM_UPPER_DENSITY)
        self.friction = self.np_random.uniform(self.RANDOM_LOWER_FRICTION, self.RANDOM_UPPER_FRICTION)
        with self.modify_xml('half_cheetah.xml') as tree:
            for elem in tree.iterfind('worldbody/body/geom'):
                elem.set('density', str(self.density))
            for elem in tree.iterfind('default/geom'):
                elem.set('friction', str(self.friction) + ' .1 .1')

    def get_obs(self, state):
        if self.oracle:
            hidden_states = self.get_hidden_states()
            state = np.concatenate([state, hidden_states])
            return state
        else:
            return state

    def _reset(self, new=True):
        if new:
            self.randomize_env()
        state = super(RandomNormalHalfCheetah_MRPO, self)._reset(new)
        return self.get_obs(state)

    def _step(self, a):
        state, reward, done, info = super(RandomNormalHalfCheetah_MRPO, self)._step(a)
        return (self.get_obs(state), reward, done, info)

    @property
    def parameters(self):
        parameters = super(RandomNormalHalfCheetah_MRPO, self).parameters
        parameters.update({'density': self.density, 'friction': self.friction})
        return parameters

    def get_hidden_states(self):
        hidden_states = np.array([(self.density - self.RANDOM_LOWER_DENSITY) / (self.RANDOM_UPPER_DENSITY - self.RANDOM_LOWER_DENSITY), (self.friction - self.RANDOM_LOWER_FRICTION) / (self.RANDOM_UPPER_FRICTION - self.RANDOM_LOWER_FRICTION)])
        return hidden_states.copy()

@property
def parameters(self):
    parameters = super(RandomNormalHalfCheetah_MRPO, self).parameters
    parameters.update({'density': self.density, 'friction': self.friction})
    return parameters

class RandomNormalHopper_MRPO(RoboschoolXMLModifierMixin, ModifiableRoboschoolHopper_MRPO):

    def __init__(self, oracle: bool=False, **kwargs):
        super().__init__(**kwargs)
        self.oracle = oracle
        if oracle == True:
            print('WARNING! YOU ARE USING MDP, NOT POMDP!\n')
            self._reset()
            tmp_hidden_states = self.get_hidden_states()
            self.observation_space = spaces.Box(low=np.array([*self.observation_space.low, *[0] * len(tmp_hidden_states)]), high=np.array([*self.observation_space.high, *[1] * len(tmp_hidden_states)]), dtype=np.float32)

    def randomize_env(self):
        self.density = self.np_random.uniform(self.RANDOM_LOWER_DENSITY, self.RANDOM_UPPER_DENSITY)
        self.friction = self.np_random.uniform(self.RANDOM_LOWER_FRICTION, self.RANDOM_UPPER_FRICTION)
        with self.modify_xml('hopper.xml') as tree:
            for elem in tree.iterfind('worldbody/body/geom'):
                elem.set('density', str(self.density))
            for elem in tree.iterfind('default/geom'):
                elem.set('friction', str(self.friction) + ' .1 .1')

    def get_obs(self, state):
        if self.oracle:
            hidden_states = self.get_hidden_states()
            state = np.concatenate([state, hidden_states])
            return state
        else:
            return state

    def _reset(self, new=True):
        if new:
            self.randomize_env()
        state = super(RandomNormalHopper_MRPO, self)._reset(new)
        return self.get_obs(state)

    def _step(self, a):
        state, reward, done, info = super(RandomNormalHopper_MRPO, self)._step(a)
        return (self.get_obs(state), reward, done, info)

    @property
    def parameters(self):
        parameters = super(RandomNormalHopper_MRPO, self).parameters
        parameters.update({'density': self.density, 'friction': self.friction})
        return parameters

    def get_hidden_states(self):
        hidden_states = np.array([(self.density - self.RANDOM_LOWER_DENSITY) / (self.RANDOM_UPPER_DENSITY - self.RANDOM_LOWER_DENSITY), (self.friction - self.RANDOM_LOWER_FRICTION) / (self.RANDOM_UPPER_FRICTION - self.RANDOM_LOWER_FRICTION)])
        return hidden_states.copy()

@property
def parameters(self):
    parameters = super(RandomNormalHopper_MRPO, self).parameters
    parameters.update({'density': self.density, 'friction': self.friction})
    return parameters

class ModifiableCartPoleEnv(CartPoleEnv, EnvBinarySuccessMixin):
    RANDOM_LOWER_FORCE_MAG = 5.0
    RANDOM_UPPER_FORCE_MAG = 15.0
    EXTREME_LOWER_FORCE_MAG = 1.0
    EXTREME_UPPER_FORCE_MAG = 20.0
    RANDOM_LOWER_LENGTH = 0.25
    RANDOM_UPPER_LENGTH = 0.75
    EXTREME_LOWER_LENGTH = 0.05
    EXTREME_UPPER_LENGTH = 1.0
    RANDOM_LOWER_MASSPOLE = 0.05
    RANDOM_UPPER_MASSPOLE = 0.5
    EXTREME_LOWER_MASSPOLE = 0.01
    EXTREME_UPPER_MASSPOLE = 1.0

    def _followup(self):
        """Cascade values of new (variable) parameters"""
        self.total_mass = self.masspole + self.masscart
        self.polemass_length = self.masspole * self.length

    def reset(self, new=True):
        """new is a boolean variable telling whether to regenerate the environment parameters"""
        'Default is to just ignore it'
        self.nsteps = 0
        return super(ModifiableCartPoleEnv, self).reset()

    @property
    def parameters(self):
        return {'id': self.spec.id}

    def step(self, *args, **kwargs):
        """Wrapper to increment new variable nsteps"""
        self.nsteps += 1
        return super().step(*args, **kwargs)

    def is_success(self):
        """Returns True is current state indicates success, False otherwise
        Balance for at least 195 time steps ("definition" of success in Gym:
        https://github.com/openai/gym/wiki/CartPole-v0#solved-requirements)
        """
        target = 195
        if self.nsteps >= target:
            return True
        else:
            return False

def reset(self, new=True):
    """new is a boolean variable telling whether to regenerate the environment parameters"""
    'Default is to just ignore it'
    self.nsteps = 0
    return super(ModifiableCartPoleEnv, self).reset()

class StrongPushCartPole(ModifiableCartPoleEnv):

    def __init__(self):
        super(StrongPushCartPole, self).__init__()
        self.force_mag = self.EXTREME_UPPER_FORCE_MAG

    @property
    def parameters(self):
        parameters = super(StrongPushCartPole, self).parameters
        parameters.update({'force': self.force_mag})
        return parameters

def __init__(self):
    super(StrongPushCartPole, self).__init__()
    self.force_mag = self.EXTREME_UPPER_FORCE_MAG

@property
def parameters(self):
    parameters = super(StrongPushCartPole, self).parameters
    parameters.update({'force': self.force_mag})
    return parameters

class WeakPushCartPole(ModifiableCartPoleEnv):

    def __init__(self):
        super(WeakPushCartPole, self).__init__()
        self.force_mag = self.EXTREME_LOWER_FORCE_MAG

    @property
    def parameters(self):
        parameters = super(WeakPushCartPole, self).parameters
        parameters.update({'force': self.force_mag})
        return parameters

def __init__(self):
    super(WeakPushCartPole, self).__init__()
    self.force_mag = self.EXTREME_LOWER_FORCE_MAG

@property
def parameters(self):
    parameters = super(WeakPushCartPole, self).parameters
    parameters.update({'force': self.force_mag})
    return parameters

class RandomStrongPushCartPole(ModifiableCartPoleEnv):

    def __init__(self):
        super(RandomStrongPushCartPole, self).__init__()
        self.force_mag = self.np_random.uniform(self.RANDOM_LOWER_FORCE_MAG, self.RANDOM_UPPER_FORCE_MAG)

    def reset(self, new=True):
        self.state = self.np_random.uniform(low=-0.05, high=0.05, size=(4,))
        self.steps_beyond_done = None
        if new:
            self.force_mag = self.np_random.uniform(self.RANDOM_LOWER_FORCE_MAG, self.RANDOM_UPPER_FORCE_MAG)
        return np.array(self.state)

    @property
    def parameters(self):
        parameters = super(RandomStrongPushCartPole, self).parameters
        parameters.update({'force': self.force_mag})
        return parameters

def __init__(self):
    super(RandomStrongPushCartPole, self).__init__()
    self.force_mag = self.np_random.uniform(self.RANDOM_LOWER_FORCE_MAG, self.RANDOM_UPPER_FORCE_MAG)

@property
def parameters(self):
    parameters = super(RandomStrongPushCartPole, self).parameters
    parameters.update({'force': self.force_mag})
    return parameters

class RandomWeakPushCartPole(ModifiableCartPoleEnv):

    def __init__(self):
        super(RandomWeakPushCartPole, self).__init__()
        self.force_mag = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_FORCE_MAG, self.EXTREME_UPPER_FORCE_MAG, self.RANDOM_LOWER_FORCE_MAG, self.RANDOM_UPPER_FORCE_MAG)

    def reset(self, new=True):
        self.state = self.np_random.uniform(low=-0.05, high=0.05, size=(4,))
        self.steps_beyond_done = None
        if new:
            self.force_mag = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_FORCE_MAG, self.EXTREME_UPPER_FORCE_MAG, self.RANDOM_LOWER_FORCE_MAG, self.RANDOM_UPPER_FORCE_MAG)
        return np.array(self.state)

    @property
    def parameters(self):
        parameters = super(RandomWeakPushCartPole, self).parameters
        parameters.update({'force': self.force_mag})
        return parameters

def __init__(self):
    super(RandomWeakPushCartPole, self).__init__()
    self.force_mag = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_FORCE_MAG, self.EXTREME_UPPER_FORCE_MAG, self.RANDOM_LOWER_FORCE_MAG, self.RANDOM_UPPER_FORCE_MAG)

@property
def parameters(self):
    parameters = super(RandomWeakPushCartPole, self).parameters
    parameters.update({'force': self.force_mag})
    return parameters

class ShortPoleCartPole(ModifiableCartPoleEnv):

    def __init__(self):
        super(ShortPoleCartPole, self).__init__()
        self.length = self.EXTREME_LOWER_LENGTH
        self._followup()

    @property
    def parameters(self):
        parameters = super(ShortPoleCartPole, self).parameters
        parameters.update({'length': self.length})
        return parameters

def __init__(self):
    super(ShortPoleCartPole, self).__init__()
    self.length = self.EXTREME_LOWER_LENGTH
    self._followup()

@property
def parameters(self):
    parameters = super(ShortPoleCartPole, self).parameters
    parameters.update({'length': self.length})
    return parameters

class LongPoleCartPole(ModifiableCartPoleEnv):

    def __init__(self):
        super(LongPoleCartPole, self).__init__()
        self.length = self.EXTREME_UPPER_LENGTH
        self._followup()

    @property
    def parameters(self):
        parameters = super(LongPoleCartPole, self).parameters
        parameters.update({'length': self.length})
        return parameters

def __init__(self):
    super(LongPoleCartPole, self).__init__()
    self.length = self.EXTREME_UPPER_LENGTH
    self._followup()

@property
def parameters(self):
    parameters = super(LongPoleCartPole, self).parameters
    parameters.update({'length': self.length})
    return parameters

class RandomLongPoleCartPole(ModifiableCartPoleEnv):

    def __init__(self):
        super(RandomLongPoleCartPole, self).__init__()
        self.length = self.np_random.uniform(self.RANDOM_LOWER_LENGTH, self.RANDOM_UPPER_LENGTH)
        self._followup()

    def reset(self, new=True):
        self.state = self.np_random.uniform(low=-0.05, high=0.05, size=(4,))
        self.steps_beyond_done = None
        if new:
            self.length = self.np_random.uniform(self.RANDOM_LOWER_LENGTH, self.RANDOM_UPPER_LENGTH)
            self._followup()
        return np.array(self.state)

    @property
    def parameters(self):
        parameters = super(RandomLongPoleCartPole, self).parameters
        parameters.update({'length': self.length})
        return parameters

def __init__(self):
    super(RandomLongPoleCartPole, self).__init__()
    self.length = self.np_random.uniform(self.RANDOM_LOWER_LENGTH, self.RANDOM_UPPER_LENGTH)
    self._followup()

def reset(self, new=True):
    self.state = self.np_random.uniform(low=-0.05, high=0.05, size=(4,))
    self.steps_beyond_done = None
    if new:
        self.length = self.np_random.uniform(self.RANDOM_LOWER_LENGTH, self.RANDOM_UPPER_LENGTH)
        self._followup()
    return np.array(self.state)

@property
def parameters(self):
    parameters = super(RandomLongPoleCartPole, self).parameters
    parameters.update({'length': self.length})
    return parameters

class RandomShortPoleCartPole(ModifiableCartPoleEnv):

    def __init__(self):
        super(RandomShortPoleCartPole, self).__init__()
        self.length = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_LENGTH, self.EXTREME_UPPER_LENGTH, self.RANDOM_LOWER_LENGTH, self.RANDOM_UPPER_LENGTH)
        self._followup()

    def reset(self, new=True):
        self.state = self.np_random.uniform(low=-0.05, high=0.05, size=(4,))
        self.steps_beyond_done = None
        if new:
            self.length = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_LENGTH, self.EXTREME_UPPER_LENGTH, self.RANDOM_LOWER_LENGTH, self.RANDOM_UPPER_LENGTH)
            self._followup()
        return np.array(self.state)

    @property
    def parameters(self):
        parameters = super(RandomShortPoleCartPole, self).parameters
        parameters.update({'length': self.length})
        return parameters

def __init__(self):
    super(RandomShortPoleCartPole, self).__init__()
    self.length = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_LENGTH, self.EXTREME_UPPER_LENGTH, self.RANDOM_LOWER_LENGTH, self.RANDOM_UPPER_LENGTH)
    self._followup()

def reset(self, new=True):
    self.state = self.np_random.uniform(low=-0.05, high=0.05, size=(4,))
    self.steps_beyond_done = None
    if new:
        self.length = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_LENGTH, self.EXTREME_UPPER_LENGTH, self.RANDOM_LOWER_LENGTH, self.RANDOM_UPPER_LENGTH)
        self._followup()
    return np.array(self.state)

@property
def parameters(self):
    parameters = super(RandomShortPoleCartPole, self).parameters
    parameters.update({'length': self.length})
    return parameters

class LightPoleCartPole(ModifiableCartPoleEnv):

    def __init__(self):
        super(LightPoleCartPole, self).__init__()
        self.masspole = self.EXTREME_LOWER_MASSPOLE
        self._followup()

    @property
    def parameters(self):
        parameters = super(LightPoleCartPole, self).parameters
        parameters.update({'mass': self.masspole})
        return parameters

def __init__(self):
    super(LightPoleCartPole, self).__init__()
    self.masspole = self.EXTREME_LOWER_MASSPOLE
    self._followup()

@property
def parameters(self):
    parameters = super(LightPoleCartPole, self).parameters
    parameters.update({'mass': self.masspole})
    return parameters

class HeavyPoleCartPole(ModifiableCartPoleEnv):

    def __init__(self):
        super(HeavyPoleCartPole, self).__init__()
        self.masspole = self.EXTREME_UPPER_MASSPOLE
        self._followup()

    @property
    def parameters(self):
        parameters = super(HeavyPoleCartPole, self).parameters
        parameters.update({'mass': self.masspole})
        return parameters

def __init__(self):
    super(HeavyPoleCartPole, self).__init__()
    self.masspole = self.EXTREME_UPPER_MASSPOLE
    self._followup()

@property
def parameters(self):
    parameters = super(HeavyPoleCartPole, self).parameters
    parameters.update({'mass': self.masspole})
    return parameters

class RandomHeavyPoleCartPole(ModifiableCartPoleEnv):

    def __init__(self):
        super(RandomHeavyPoleCartPole, self).__init__()
        self.masspole = self.np_random.uniform(self.RANDOM_LOWER_MASSPOLE, self.RANDOM_UPPER_MASSPOLE)
        self._followup()

    def reset(self, new=True):
        self.state = self.np_random.uniform(low=-0.05, high=0.05, size=(4,))
        self.steps_beyond_done = None
        if new:
            self.masspole = self.np_random.uniform(self.RANDOM_LOWER_MASSPOLE, self.RANDOM_UPPER_MASSPOLE)
            self._followup()
        return np.array(self.state)

    @property
    def parameters(self):
        parameters = super(RandomHeavyPoleCartPole, self).parameters
        parameters.update({'mass': self.masspole})
        return parameters

def __init__(self):
    super(RandomHeavyPoleCartPole, self).__init__()
    self.masspole = self.np_random.uniform(self.RANDOM_LOWER_MASSPOLE, self.RANDOM_UPPER_MASSPOLE)
    self._followup()

def reset(self, new=True):
    self.state = self.np_random.uniform(low=-0.05, high=0.05, size=(4,))
    self.steps_beyond_done = None
    if new:
        self.masspole = self.np_random.uniform(self.RANDOM_LOWER_MASSPOLE, self.RANDOM_UPPER_MASSPOLE)
        self._followup()
    return np.array(self.state)

@property
def parameters(self):
    parameters = super(RandomHeavyPoleCartPole, self).parameters
    parameters.update({'mass': self.masspole})
    return parameters

class RandomLightPoleCartPole(ModifiableCartPoleEnv):

    def __init__(self):
        super(RandomLightPoleCartPole, self).__init__()
        self.masspole = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_MASSPOLE, self.EXTREME_UPPER_MASSPOLE, self.RANDOM_LOWER_MASSPOLE, self.RANDOM_UPPER_MASSPOLE)
        self._followup()

    def reset(self, new=True):
        self.state = self.np_random.uniform(low=-0.05, high=0.05, size=(4,))
        self.steps_beyond_done = None
        if new:
            self.masspole = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_MASSPOLE, self.EXTREME_UPPER_MASSPOLE, self.RANDOM_LOWER_MASSPOLE, self.RANDOM_UPPER_MASSPOLE)
            self._followup()
        return np.array(self.state)

    @property
    def parameters(self):
        parameters = super(RandomLightPoleCartPole, self).parameters
        parameters.update({'mass': self.masspole})
        return parameters

def __init__(self):
    super(RandomLightPoleCartPole, self).__init__()
    self.masspole = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_MASSPOLE, self.EXTREME_UPPER_MASSPOLE, self.RANDOM_LOWER_MASSPOLE, self.RANDOM_UPPER_MASSPOLE)
    self._followup()

def reset(self, new=True):
    self.state = self.np_random.uniform(low=-0.05, high=0.05, size=(4,))
    self.steps_beyond_done = None
    if new:
        self.masspole = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_MASSPOLE, self.EXTREME_UPPER_MASSPOLE, self.RANDOM_LOWER_MASSPOLE, self.RANDOM_UPPER_MASSPOLE)
        self._followup()
    return np.array(self.state)

@property
def parameters(self):
    parameters = super(RandomLightPoleCartPole, self).parameters
    parameters.update({'mass': self.masspole})
    return parameters

class RandomNormalCartPole(ModifiableCartPoleEnv):

    def __init__(self):
        super(RandomNormalCartPole, self).__init__()
        self.force_mag = self.np_random.uniform(self.RANDOM_LOWER_FORCE_MAG, self.RANDOM_UPPER_FORCE_MAG)
        self.length = self.np_random.uniform(self.RANDOM_LOWER_LENGTH, self.RANDOM_UPPER_LENGTH)
        self.masspole = self.np_random.uniform(self.RANDOM_LOWER_MASSPOLE, self.RANDOM_UPPER_MASSPOLE)
        self._followup()

    def reset(self, new=True):
        self.nsteps = 0
        self.state = self.np_random.uniform(low=-0.05, high=0.05, size=(4,))
        self.steps_beyond_done = None
        if new:
            self.force_mag = self.np_random.uniform(self.RANDOM_LOWER_FORCE_MAG, self.RANDOM_UPPER_FORCE_MAG)
            self.length = self.np_random.uniform(self.RANDOM_LOWER_LENGTH, self.RANDOM_UPPER_LENGTH)
            self.masspole = self.np_random.uniform(self.RANDOM_LOWER_MASSPOLE, self.RANDOM_UPPER_MASSPOLE)
            self._followup()
        return np.array(self.state)

    @property
    def parameters(self):
        parameters = super(RandomNormalCartPole, self).parameters
        parameters.update({'force_mag': self.force_mag, 'length': self.length, 'masspole': self.masspole, 'total_mass': self.total_mass, 'polemass_length': self.polemass_length})
        return parameters

def __init__(self):
    super(RandomNormalCartPole, self).__init__()
    self.force_mag = self.np_random.uniform(self.RANDOM_LOWER_FORCE_MAG, self.RANDOM_UPPER_FORCE_MAG)
    self.length = self.np_random.uniform(self.RANDOM_LOWER_LENGTH, self.RANDOM_UPPER_LENGTH)
    self.masspole = self.np_random.uniform(self.RANDOM_LOWER_MASSPOLE, self.RANDOM_UPPER_MASSPOLE)
    self._followup()

def reset(self, new=True):
    self.nsteps = 0
    self.state = self.np_random.uniform(low=-0.05, high=0.05, size=(4,))
    self.steps_beyond_done = None
    if new:
        self.force_mag = self.np_random.uniform(self.RANDOM_LOWER_FORCE_MAG, self.RANDOM_UPPER_FORCE_MAG)
        self.length = self.np_random.uniform(self.RANDOM_LOWER_LENGTH, self.RANDOM_UPPER_LENGTH)
        self.masspole = self.np_random.uniform(self.RANDOM_LOWER_MASSPOLE, self.RANDOM_UPPER_MASSPOLE)
        self._followup()
    return np.array(self.state)

@property
def parameters(self):
    parameters = super(RandomNormalCartPole, self).parameters
    parameters.update({'force_mag': self.force_mag, 'length': self.length, 'masspole': self.masspole, 'total_mass': self.total_mass, 'polemass_length': self.polemass_length})
    return parameters

class RandomExtremeCartPole(ModifiableCartPoleEnv):

    def __init__(self):
        super(RandomExtremeCartPole, self).__init__()
        '\n        self.force_mag = self.np_random.uniform(self.LOWER_FORCE_MAG, self.UPPER_FORCE_MAG)\n        self.length = self.np_random.uniform(self.LOWER_LENGTH, self.UPPER_LENGTH)\n        self.masspole = self.np_random.uniform(self.LOWER_MASSPOLE, self.UPPER_MASSPOLE)\n        '
        self.force_mag = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_FORCE_MAG, self.EXTREME_UPPER_FORCE_MAG, self.RANDOM_LOWER_FORCE_MAG, self.RANDOM_UPPER_FORCE_MAG)
        self.length = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_LENGTH, self.EXTREME_UPPER_LENGTH, self.RANDOM_LOWER_LENGTH, self.RANDOM_UPPER_LENGTH)
        self.masspole = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_MASSPOLE, self.EXTREME_UPPER_MASSPOLE, self.RANDOM_LOWER_MASSPOLE, self.RANDOM_UPPER_MASSPOLE)
        self._followup()

    def reset(self, new=True):
        self.nsteps = 0
        self.state = self.np_random.uniform(low=-0.05, high=0.05, size=(4,))
        self.steps_beyond_done = None
        '\n        self.force_mag = self.np_random.uniform(self.LOWER_FORCE_MAG, self.UPPER_FORCE_MAG)\n        self.length = self.np_random.uniform(self.LOWER_LENGTH, self.UPPER_LENGTH)\n        self.masspole = self.np_random.uniform(self.LOWER_MASSPOLE, self.UPPER_MASSPOLE)\n        '
        if new:
            self.force_mag = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_FORCE_MAG, self.EXTREME_UPPER_FORCE_MAG, self.RANDOM_LOWER_FORCE_MAG, self.RANDOM_UPPER_FORCE_MAG)
            self.length = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_LENGTH, self.EXTREME_UPPER_LENGTH, self.RANDOM_LOWER_LENGTH, self.RANDOM_UPPER_LENGTH)
            self.masspole = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_MASSPOLE, self.EXTREME_UPPER_MASSPOLE, self.RANDOM_LOWER_MASSPOLE, self.RANDOM_UPPER_MASSPOLE)
            self._followup()
        return np.array(self.state)

    @property
    def parameters(self):
        parameters = super(RandomExtremeCartPole, self).parameters
        parameters.update({'force_mag': self.force_mag, 'length': self.length, 'masspole': self.masspole, 'total_mass': self.total_mass, 'polemass_length': self.polemass_length})
        return parameters

def __init__(self):
    super(RandomExtremeCartPole, self).__init__()
    '\n        self.force_mag = self.np_random.uniform(self.LOWER_FORCE_MAG, self.UPPER_FORCE_MAG)\n        self.length = self.np_random.uniform(self.LOWER_LENGTH, self.UPPER_LENGTH)\n        self.masspole = self.np_random.uniform(self.LOWER_MASSPOLE, self.UPPER_MASSPOLE)\n        '
    self.force_mag = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_FORCE_MAG, self.EXTREME_UPPER_FORCE_MAG, self.RANDOM_LOWER_FORCE_MAG, self.RANDOM_UPPER_FORCE_MAG)
    self.length = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_LENGTH, self.EXTREME_UPPER_LENGTH, self.RANDOM_LOWER_LENGTH, self.RANDOM_UPPER_LENGTH)
    self.masspole = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_MASSPOLE, self.EXTREME_UPPER_MASSPOLE, self.RANDOM_LOWER_MASSPOLE, self.RANDOM_UPPER_MASSPOLE)
    self._followup()

def reset(self, new=True):
    self.nsteps = 0
    self.state = self.np_random.uniform(low=-0.05, high=0.05, size=(4,))
    self.steps_beyond_done = None
    '\n        self.force_mag = self.np_random.uniform(self.LOWER_FORCE_MAG, self.UPPER_FORCE_MAG)\n        self.length = self.np_random.uniform(self.LOWER_LENGTH, self.UPPER_LENGTH)\n        self.masspole = self.np_random.uniform(self.LOWER_MASSPOLE, self.UPPER_MASSPOLE)\n        '
    if new:
        self.force_mag = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_FORCE_MAG, self.EXTREME_UPPER_FORCE_MAG, self.RANDOM_LOWER_FORCE_MAG, self.RANDOM_UPPER_FORCE_MAG)
        self.length = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_LENGTH, self.EXTREME_UPPER_LENGTH, self.RANDOM_LOWER_LENGTH, self.RANDOM_UPPER_LENGTH)
        self.masspole = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_MASSPOLE, self.EXTREME_UPPER_MASSPOLE, self.RANDOM_LOWER_MASSPOLE, self.RANDOM_UPPER_MASSPOLE)
        self._followup()
    return np.array(self.state)

@property
def parameters(self):
    parameters = super(RandomExtremeCartPole, self).parameters
    parameters.update({'force_mag': self.force_mag, 'length': self.length, 'masspole': self.masspole, 'total_mass': self.total_mass, 'polemass_length': self.polemass_length})
    return parameters

class ModifiableMountainCarEnv(MountainCarEnv):
    """A variant of mountain car without hardcoded force/mass."""
    RANDOM_LOWER_FORCE = 0.0005
    RANDOM_UPPER_FORCE = 0.005
    EXTREME_LOWER_FORCE = 0.0001
    EXTREME_UPPER_FORCE = 0.01
    RANDOM_LOWER_MASS = 0.001
    RANDOM_UPPER_MASS = 0.005
    EXTREME_LOWER_MASS = 0.0005
    EXTREME_UPPER_MASS = 0.01

    def __init__(self):
        super(ModifiableMountainCarEnv, self).__init__()
        self.force = 0.001
        self.mass = 0.0025

    def step(self, action):
        """Rewritten to remove hard-coding of values in original code"""
        assert self.action_space.contains(action), '%r (%s) invalid' % (action, type(action))
        position, velocity = self.state
        velocity += (action - 1) * self.force + math.cos(3 * position) * -self.mass
        velocity = np.clip(velocity, -self.max_speed, self.max_speed)
        position += velocity
        position = np.clip(position, self.min_position, self.max_position)
        if position == self.min_position and velocity < 0:
            velocity = 0
        done = bool(position >= self.goal_position)
        reward = -1.0
        self.nsteps += 1
        target = 110
        if self.nsteps <= target and done:
            self.success = True
        else:
            self.success = False
        self.state = (position, velocity)
        return (np.array(self.state), reward, done, {})

    def reset(self, new=True):
        self.nsteps = 0
        return super(ModifiableMountainCarEnv, self).reset()

    @property
    def parameters(self):
        return {'id': self.spec.id}

    def is_success(self):
        """Returns True is current state indicates success, False otherwise
        get to the top of the hill within 110 time steps (definition of success in Gym)

        MountainCar sets done=True once the car reaches the "top of the hill",
        so we can just check if done=True and nsteps<=110. See:
        https://github.com/openai/gym/blob/0ccb08dfa1535624b45645e141af9398e2eba416/gym/envs/classic_control/mountain_car.py#L49
        """
        return self.success

def __init__(self):
    super(ModifiableMountainCarEnv, self).__init__()
    self.force = 0.001
    self.mass = 0.0025

def reset(self, new=True):
    self.nsteps = 0
    return super(ModifiableMountainCarEnv, self).reset()

class WeakForceMountainCar(ModifiableMountainCarEnv):

    def __init__(self):
        super(WeakForceMountainCar, self).__init__()
        self.force = self.EXTREME_LOWER_FORCE

    @property
    def parameters(self):
        parameters = super(WeakForceMountainCar, self).parameters
        parameters.update({'force': self.force})
        return parameters

def __init__(self):
    super(WeakForceMountainCar, self).__init__()
    self.force = self.EXTREME_LOWER_FORCE

@property
def parameters(self):
    parameters = super(WeakForceMountainCar, self).parameters
    parameters.update({'force': self.force})
    return parameters

class StrongForceMountainCar(ModifiableMountainCarEnv):

    def __init__(self):
        super(StrongForceMountainCar, self).__init__()
        self.force = self.EXTREME_UPPER_FORCE

    @property
    def parameters(self):
        parameters = super(StrongForceMountainCar, self).parameters
        parameters.update({'force': self.force})
        return parameters

def __init__(self):
    super(StrongForceMountainCar, self).__init__()
    self.force = self.EXTREME_UPPER_FORCE

@property
def parameters(self):
    parameters = super(StrongForceMountainCar, self).parameters
    parameters.update({'force': self.force})
    return parameters

class RandomStrongForceMountainCar(ModifiableMountainCarEnv):

    def reset(self, new=True):
        if new:
            self.force = self.np_random.uniform(self.RANDOM_LOWER_FORCE, self.RANDOM_UPPER_FORCE)
        self.state = np.array([self.np_random.uniform(low=-0.6, high=-0.4), 0])
        return np.array(self.state)

    @property
    def parameters(self):
        parameters = super(RandomStrongForceMountainCar, self).parameters
        parameters.update({'force': self.force})
        return parameters

@property
def parameters(self):
    parameters = super(RandomStrongForceMountainCar, self).parameters
    parameters.update({'force': self.force})
    return parameters

class RandomWeakForceMountainCar(ModifiableMountainCarEnv):

    def reset(self, new=True):
        if new:
            self.force = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_FORCE, self.EXTREME_UPPER_FORCE, self.RANDOM_LOWER_FORCE, self.RANDOM_UPPER_FORCE)
        self.state = np.array([self.np_random.uniform(low=-0.6, high=-0.4), 0])
        return np.array(self.state)

    @property
    def parameters(self):
        parameters = super(RandomWeakForceMountainCar, self).parameters
        parameters.update({'force': self.force})
        return parameters

def reset(self, new=True):
    if new:
        self.force = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_FORCE, self.EXTREME_UPPER_FORCE, self.RANDOM_LOWER_FORCE, self.RANDOM_UPPER_FORCE)
    self.state = np.array([self.np_random.uniform(low=-0.6, high=-0.4), 0])
    return np.array(self.state)

@property
def parameters(self):
    parameters = super(RandomWeakForceMountainCar, self).parameters
    parameters.update({'force': self.force})
    return parameters

class LightCarMountainCar(ModifiableMountainCarEnv):

    def __init__(self):
        super(LightCarMountainCar, self).__init__()
        self.mass = self.EXTREME_LOWER_MASS

    @property
    def parameters(self):
        parameters = super(LightCarMountainCar, self).parameters
        parameters.update({'mass': self.mass})
        return parameters

def __init__(self):
    super(LightCarMountainCar, self).__init__()
    self.mass = self.EXTREME_LOWER_MASS

@property
def parameters(self):
    parameters = super(LightCarMountainCar, self).parameters
    parameters.update({'mass': self.mass})
    return parameters

class HeavyCarMountainCar(ModifiableMountainCarEnv):

    def __init__(self):
        super(HeavyCarMountainCar, self).__init__()
        self.mass = self.EXTREME_UPPER_MASS

    @property
    def parameters(self):
        parameters = super(HeavyCarMountainCar, self).parameters
        parameters.update({'mass': self.mass})
        return parameters

def __init__(self):
    super(HeavyCarMountainCar, self).__init__()
    self.mass = self.EXTREME_UPPER_MASS

@property
def parameters(self):
    parameters = super(HeavyCarMountainCar, self).parameters
    parameters.update({'mass': self.mass})
    return parameters

class RandomHeavyCarMountainCar(ModifiableMountainCarEnv):

    def reset(self, new=True):
        if new:
            self.mass = self.np_random.uniform(self.RANDOM_LOWER_MASS, self.RANDOM_UPPER_MASS)
        self.state = np.array([self.np_random.uniform(low=-0.6, high=-0.4), 0])
        return np.array(self.state)

    @property
    def parameters(self):
        parameters = super(RandomHeavyCarMountainCar, self).parameters
        parameters.update({'mass': self.mass})
        return parameters

@property
def parameters(self):
    parameters = super(RandomHeavyCarMountainCar, self).parameters
    parameters.update({'mass': self.mass})
    return parameters

class RandomLightCarMountainCar(ModifiableMountainCarEnv):

    def reset(self, new=True):
        if new:
            self.mass = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_MASS, self.EXTREME_UPPER_MASS, self.RANDOM_LOWER_MASS, self.RANDOM_UPPER_MASS)
        self.state = np.array([self.np_random.uniform(low=-0.6, high=-0.4), 0])
        return np.array(self.state)

    @property
    def parameters(self):
        parameters = super(RandomLightCarMountainCar, self).parameters
        parameters.update({'mass': self.mass})
        return parameters

def reset(self, new=True):
    if new:
        self.mass = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_MASS, self.EXTREME_UPPER_MASS, self.RANDOM_LOWER_MASS, self.RANDOM_UPPER_MASS)
    self.state = np.array([self.np_random.uniform(low=-0.6, high=-0.4), 0])
    return np.array(self.state)

@property
def parameters(self):
    parameters = super(RandomLightCarMountainCar, self).parameters
    parameters.update({'mass': self.mass})
    return parameters

class RandomNormalMountainCar(ModifiableMountainCarEnv):

    def reset(self, new=True):
        self.nsteps = 0
        if new:
            self.force = self.np_random.uniform(self.RANDOM_LOWER_FORCE, self.RANDOM_UPPER_FORCE)
            self.mass = self.np_random.uniform(self.RANDOM_LOWER_MASS, self.RANDOM_UPPER_MASS)
        self.state = np.array([self.np_random.uniform(low=-0.6, high=-0.4), 0])
        return np.array(self.state)

    @property
    def parameters(self):
        parameters = super(RandomNormalMountainCar, self).parameters
        parameters.update({'force': self.force, 'mass': self.mass})
        return parameters

@property
def parameters(self):
    parameters = super(RandomNormalMountainCar, self).parameters
    parameters.update({'force': self.force, 'mass': self.mass})
    return parameters

class RandomExtremeMountainCar(ModifiableMountainCarEnv):

    def reset(self, new=True):
        self.nsteps = 0
        if new:
            self.force = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_FORCE, self.EXTREME_UPPER_FORCE, self.RANDOM_LOWER_FORCE, self.RANDOM_UPPER_FORCE)
            self.mass = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_MASS, self.EXTREME_UPPER_MASS, self.RANDOM_LOWER_MASS, self.RANDOM_UPPER_MASS)
        self.state = np.array([self.np_random.uniform(low=-0.6, high=-0.4), 0])
        return np.array(self.state)

    @property
    def parameters(self):
        parameters = super(RandomExtremeMountainCar, self).parameters
        parameters.update({'force': self.force, 'mass': self.mass})
        return parameters

@property
def parameters(self):
    parameters = super(RandomExtremeMountainCar, self).parameters
    parameters.update({'force': self.force, 'mass': self.mass})
    return parameters

class ModifiablePendulumEnv(PendulumEnv):
    """The pendulum environment without length and mass of object hard-coded."""
    RANDOM_LOWER_MASS = 0.75
    RANDOM_UPPER_MASS = 1.25
    EXTREME_LOWER_MASS = 0.5
    EXTREME_UPPER_MASS = 1.5
    RANDOM_LOWER_LENGTH = 0.75
    RANDOM_UPPER_LENGTH = 1.25
    EXTREME_LOWER_LENGTH = 0.5
    EXTREME_UPPER_LENGTH = 1.5

    def __init__(self):
        super(ModifiablePendulumEnv, self).__init__()
        self.mass = 1.0
        self.length = 1.0

    def step(self, u):
        th, thdot = self.state
        g = 10.0
        dt = self.dt
        u = np.clip(u, -self.max_torque, self.max_torque)[0]
        self.last_u = u
        angle_normalize = (th + np.pi) % (2 * np.pi) - np.pi
        costs = angle_normalize ** 2 + 0.1 * thdot ** 2 + 0.001 * u ** 2
        newthdot = thdot + (-3 * g / (2 * self.length) * np.sin(th + np.pi) + 3.0 / (self.mass * self.length ** 2) * u) * dt
        newth = th + newthdot * dt
        newthdot = np.clip(newthdot, -self.max_speed, self.max_speed)
        normalized = (newth + np.pi) % (2 * np.pi) - np.pi
        self.state = np.array([newth, newthdot])
        self.nsteps += 1
        if -np.pi / 3 <= normalized and normalized <= np.pi / 3:
            self.nsteps_vertical += 1
        else:
            self.nsteps_vertical = 0
        target = 100
        if self.nsteps_vertical >= target:
            self.success = True
        else:
            self.success = False
        return (self._get_obs(), -costs, False, {})

    def reset(self, new=True):
        self.nsteps = 0
        self.nsteps_vertical = 0
        return super(ModifiablePendulumEnv, self).reset()

    @property
    def parameters(self):
        return {'id': self.spec.id}

    def is_success(self):
        """Returns True if current state indicates success, False otherwise

        Success: keep the angle of the pendulum at most pi/3 radians from
        vertical for the last 100 time steps of a trajectory with length 200
        (max_length is set to 200 in sunblaze_envs/__init__.py)
        """
        return self.success

def __init__(self):
    super(ModifiablePendulumEnv, self).__init__()
    self.mass = 1.0
    self.length = 1.0

def reset(self, new=True):
    self.nsteps = 0
    self.nsteps_vertical = 0
    return super(ModifiablePendulumEnv, self).reset()

class LightPendulum(ModifiablePendulumEnv):

    def __init__(self):
        super(LightPendulum, self).__init__()
        self.mass = self.EXTREME_LOWER_MASS

    @property
    def parameters(self):
        parameters = super(LightPendulum, self).parameters
        parameters.update({'mass': self.mass})
        return parameters

def __init__(self):
    super(LightPendulum, self).__init__()
    self.mass = self.EXTREME_LOWER_MASS

@property
def parameters(self):
    parameters = super(LightPendulum, self).parameters
    parameters.update({'mass': self.mass})
    return parameters

class HeavyPendulum(ModifiablePendulumEnv):

    def __init__(self):
        super(HeavyPendulum, self).__init__()
        self.mass = self.EXTREME_UPPER_MASS

    @property
    def parameters(self):
        parameters = super(HeavyPendulum, self).parameters
        parameters.update({'mass': self.mass})
        return parameters

def __init__(self):
    super(HeavyPendulum, self).__init__()
    self.mass = self.EXTREME_UPPER_MASS

@property
def parameters(self):
    parameters = super(HeavyPendulum, self).parameters
    parameters.update({'mass': self.mass})
    return parameters

class RandomHeavyPendulum(ModifiablePendulumEnv):

    def __init__(self):
        super(RandomHeavyPendulum, self).__init__()
        self.mass = self.np_random.uniform(self.RANDOM_LOWER_MASS, self.RANDOM_UPPER_MASS)

    def reset(self, new=True):
        if new:
            self.mass = self.np_random.uniform(self.RANDOM_LOWER_MASS, self.RANDOM_UPPER_MASS)
        return super(RandomHeavyPendulum, self).reset(new)

    @property
    def parameters(self):
        parameters = super(RandomHeavyPendulum, self).parameters
        parameters.update({'mass': self.mass})
        return parameters

def __init__(self):
    super(RandomHeavyPendulum, self).__init__()
    self.mass = self.np_random.uniform(self.RANDOM_LOWER_MASS, self.RANDOM_UPPER_MASS)

def reset(self, new=True):
    if new:
        self.mass = self.np_random.uniform(self.RANDOM_LOWER_MASS, self.RANDOM_UPPER_MASS)
    return super(RandomHeavyPendulum, self).reset(new)

@property
def parameters(self):
    parameters = super(RandomHeavyPendulum, self).parameters
    parameters.update({'mass': self.mass})
    return parameters

class RandomLightPendulum(ModifiablePendulumEnv):

    def __init__(self):
        super(RandomLightPendulum, self).__init__()
        self.mass = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_MASS, self.EXTREME_UPPER_MASS, self.RANDOM_LOWER_MASS, self.RANDOM_UPPER_MASS)

    def reset(self, new=True):
        if new:
            self.mass = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_MASS, self.EXTREME_UPPER_MASS, self.RANDOM_LOWER_MASS, self.RANDOM_UPPER_MASS)
        return super(RandomLightPendulum, self).reset(new)

    @property
    def parameters(self):
        parameters = super(RandomLightPendulum, self).parameters
        parameters.update({'mass': self.mass})
        return parameters

def __init__(self):
    super(RandomLightPendulum, self).__init__()
    self.mass = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_MASS, self.EXTREME_UPPER_MASS, self.RANDOM_LOWER_MASS, self.RANDOM_UPPER_MASS)

def reset(self, new=True):
    if new:
        self.mass = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_MASS, self.EXTREME_UPPER_MASS, self.RANDOM_LOWER_MASS, self.RANDOM_UPPER_MASS)
    return super(RandomLightPendulum, self).reset(new)

@property
def parameters(self):
    parameters = super(RandomLightPendulum, self).parameters
    parameters.update({'mass': self.mass})
    return parameters

class ShortPendulum(ModifiablePendulumEnv):

    def __init__(self):
        super(ShortPendulum, self).__init__()
        self.length = self.EXTREME_LOWER_LENGTH

    @property
    def parameters(self):
        parameters = super(ShortPendulum, self).parameters
        parameters.update({'length': self.length})
        return parameters

def __init__(self):
    super(ShortPendulum, self).__init__()
    self.length = self.EXTREME_LOWER_LENGTH

@property
def parameters(self):
    parameters = super(ShortPendulum, self).parameters
    parameters.update({'length': self.length})
    return parameters

class LongPendulum(ModifiablePendulumEnv):

    def __init__(self):
        super(LongPendulum, self).__init__()
        self.length = self.EXTREME_UPPER_LENGTH

    @property
    def parameters(self):
        parameters = super(LongPendulum, self).parameters
        parameters.update({'length': self.length})
        return parameters

def __init__(self):
    super(LongPendulum, self).__init__()
    self.length = self.EXTREME_UPPER_LENGTH

@property
def parameters(self):
    parameters = super(LongPendulum, self).parameters
    parameters.update({'length': self.length})
    return parameters

class RandomLongPendulum(ModifiablePendulumEnv):

    def __init__(self):
        super(RandomLongPendulum, self).__init__()
        self.length = self.np_random.uniform(self.RANDOM_LOWER_LENGTH, self.RANDOM_UPPER_LENGTH)

    def reset(self, new=True):
        if new:
            self.length = self.np_random.uniform(self.RANDOM_LOWER_LENGTH, self.RANDOM_UPPER_LENGTH)
        return super(RandomLongPendulum, self).reset(new)

    @property
    def parameters(self):
        parameters = super(RandomLongPendulum, self).parameters
        parameters.update({'length': self.length})
        return parameters

def __init__(self):
    super(RandomLongPendulum, self).__init__()
    self.length = self.np_random.uniform(self.RANDOM_LOWER_LENGTH, self.RANDOM_UPPER_LENGTH)

def reset(self, new=True):
    if new:
        self.length = self.np_random.uniform(self.RANDOM_LOWER_LENGTH, self.RANDOM_UPPER_LENGTH)
    return super(RandomLongPendulum, self).reset(new)

@property
def parameters(self):
    parameters = super(RandomLongPendulum, self).parameters
    parameters.update({'length': self.length})
    return parameters

class RandomShortPendulum(ModifiablePendulumEnv):

    def __init__(self):
        super(RandomShortPendulum, self).__init__()
        self.length = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_LENGTH, self.EXTREME_UPPER_LENGTH, self.RANDOM_LOWER_LENGTH, self.RANDOM_UPPER_LENGTH)

    def reset(self, new=True):
        if new:
            self.length = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_LENGTH, self.EXTREME_UPPER_LENGTH, self.RANDOM_LOWER_LENGTH, self.RANDOM_UPPER_LENGTH)
        return super(RandomShortPendulum, self).reset(new)

    @property
    def parameters(self):
        parameters = super(RandomShortPendulum, self).parameters
        parameters.update({'length': self.length})
        return parameters

def __init__(self):
    super(RandomShortPendulum, self).__init__()
    self.length = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_LENGTH, self.EXTREME_UPPER_LENGTH, self.RANDOM_LOWER_LENGTH, self.RANDOM_UPPER_LENGTH)

def reset(self, new=True):
    if new:
        self.length = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_LENGTH, self.EXTREME_UPPER_LENGTH, self.RANDOM_LOWER_LENGTH, self.RANDOM_UPPER_LENGTH)
    return super(RandomShortPendulum, self).reset(new)

@property
def parameters(self):
    parameters = super(RandomShortPendulum, self).parameters
    parameters.update({'length': self.length})
    return parameters

class RandomNormalPendulum(ModifiablePendulumEnv):

    def __init__(self):
        super(RandomNormalPendulum, self).__init__()
        self.mass = self.np_random.uniform(self.RANDOM_LOWER_MASS, self.RANDOM_UPPER_MASS)
        self.length = self.np_random.uniform(self.RANDOM_LOWER_LENGTH, self.RANDOM_UPPER_LENGTH)

    def reset(self, new=True):
        if new:
            self.mass = self.np_random.uniform(self.RANDOM_LOWER_MASS, self.RANDOM_UPPER_MASS)
            self.length = self.np_random.uniform(self.RANDOM_LOWER_LENGTH, self.RANDOM_UPPER_LENGTH)
        return super(RandomNormalPendulum, self).reset(new)

    @property
    def parameters(self):
        parameters = super(RandomNormalPendulum, self).parameters
        parameters.update({'mass': self.mass, 'length': self.length})
        return parameters

def __init__(self):
    super(RandomNormalPendulum, self).__init__()
    self.mass = self.np_random.uniform(self.RANDOM_LOWER_MASS, self.RANDOM_UPPER_MASS)
    self.length = self.np_random.uniform(self.RANDOM_LOWER_LENGTH, self.RANDOM_UPPER_LENGTH)

def reset(self, new=True):
    if new:
        self.mass = self.np_random.uniform(self.RANDOM_LOWER_MASS, self.RANDOM_UPPER_MASS)
        self.length = self.np_random.uniform(self.RANDOM_LOWER_LENGTH, self.RANDOM_UPPER_LENGTH)
    return super(RandomNormalPendulum, self).reset(new)

@property
def parameters(self):
    parameters = super(RandomNormalPendulum, self).parameters
    parameters.update({'mass': self.mass, 'length': self.length})
    return parameters

class RandomExtremePendulum(ModifiablePendulumEnv):

    def __init__(self):
        super(RandomExtremePendulum, self).__init__()
        self.mass = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_MASS, self.EXTREME_UPPER_MASS, self.RANDOM_LOWER_MASS, self.RANDOM_UPPER_MASS)
        self.length = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_LENGTH, self.EXTREME_UPPER_LENGTH, self.RANDOM_LOWER_LENGTH, self.RANDOM_UPPER_LENGTH)

    def reset(self, new=True):
        if new:
            self.mass = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_MASS, self.EXTREME_UPPER_MASS, self.RANDOM_LOWER_MASS, self.RANDOM_UPPER_MASS)
            self.length = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_LENGTH, self.EXTREME_UPPER_LENGTH, self.RANDOM_LOWER_LENGTH, self.RANDOM_UPPER_LENGTH)
        return super(RandomExtremePendulum, self).reset(new)

    @property
    def parameters(self):
        parameters = super(RandomExtremePendulum, self).parameters
        parameters.update({'mass': self.mass, 'length': self.length})
        return parameters

def __init__(self):
    super(RandomExtremePendulum, self).__init__()
    self.mass = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_MASS, self.EXTREME_UPPER_MASS, self.RANDOM_LOWER_MASS, self.RANDOM_UPPER_MASS)
    self.length = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_LENGTH, self.EXTREME_UPPER_LENGTH, self.RANDOM_LOWER_LENGTH, self.RANDOM_UPPER_LENGTH)

def reset(self, new=True):
    if new:
        self.mass = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_MASS, self.EXTREME_UPPER_MASS, self.RANDOM_LOWER_MASS, self.RANDOM_UPPER_MASS)
        self.length = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_LENGTH, self.EXTREME_UPPER_LENGTH, self.RANDOM_LOWER_LENGTH, self.RANDOM_UPPER_LENGTH)
    return super(RandomExtremePendulum, self).reset(new)

@property
def parameters(self):
    parameters = super(RandomExtremePendulum, self).parameters
    parameters.update({'mass': self.mass, 'length': self.length})
    return parameters

class ModifiableAcrobotEnv(AcrobotEnv):
    RANDOM_LOWER_MASS = 0.75
    RANDOM_UPPER_MASS = 1.25
    EXTREME_LOWER_MASS = 0.5
    EXTREME_UPPER_MASS = 1.5
    RANDOM_LOWER_LENGTH = 0.75
    RANDOM_UPPER_LENGTH = 1.25
    EXTREME_LOWER_LENGTH = 0.5
    EXTREME_UPPER_LENGTH = 1.5
    RANDOM_LOWER_INERTIA = 0.75
    RANDOM_UPPER_INERTIA = 1.25
    EXTREME_LOWER_INERTIA = 0.5
    EXTREME_UPPER_INERTIA = 1.5

    def reset(self, new=True):
        self.nsteps = 0
        return super(ModifiableAcrobotEnv, self).reset()

    @property
    def parameters(self):
        return {'id': self.spec.id}

    def step(self, *args, **kwargs):
        """Wrapper to increment new variable nsteps"""
        self.nsteps += 1
        ret = super().step(*args, **kwargs)
        target = 90
        if self.nsteps <= target and self._terminal():
            self.success = True
        else:
            self.success = False
        return ret

    def is_success(self):
        """Returns True if current state indicates success, False otherwise

        Success: swing the end of the second link to the desired height within
        90 time steps
        """
        return self.success

def reset(self, new=True):
    self.nsteps = 0
    return super(ModifiableAcrobotEnv, self).reset()

class LightAcrobot(ModifiableAcrobotEnv):

    def __init__(self):
        super(LightAcrobot, self).__init__()
        self.mass = self.EXTREME_LOWER_MASS

    @property
    def LINK_MASS_1(self):
        return self.mass

    @property
    def LINK_MASS_2(self):
        return self.mass

    @property
    def parameters(self):
        parameters = super(LightAcrobot, self).parameters
        parameters.update({'mass': self.mass})
        return parameters

def __init__(self):
    super(LightAcrobot, self).__init__()
    self.mass = self.EXTREME_LOWER_MASS

@property
def parameters(self):
    parameters = super(LightAcrobot, self).parameters
    parameters.update({'mass': self.mass})
    return parameters

class HeavyAcrobot(ModifiableAcrobotEnv):

    def __init__(self):
        super(HeavyAcrobot, self).__init__()
        self.mass = self.EXTREME_UPPER_MASS

    @property
    def LINK_MASS_1(self):
        return self.mass

    @property
    def LINK_MASS_2(self):
        return self.mass

    @property
    def parameters(self):
        parameters = super(HeavyAcrobot, self).parameters
        parameters.update({'mass': self.mass})
        return parameters

def __init__(self):
    super(HeavyAcrobot, self).__init__()
    self.mass = self.EXTREME_UPPER_MASS

@property
def parameters(self):
    parameters = super(HeavyAcrobot, self).parameters
    parameters.update({'mass': self.mass})
    return parameters

class RandomHeavyAcrobot(ModifiableAcrobotEnv):

    def __init__(self):
        super(RandomHeavyAcrobot, self).__init__()
        self.mass = self.np_random.uniform(self.RANDOM_LOWER_MASS, self.RANDOM_UPPER_MASS)

    def reset(self, new=True):
        if new:
            self.mass = self.np_random.uniform(self.RANDOM_LOWER_MASS, self.RANDOM_UPPER_MASS)
        return super(RandomHeavyAcrobot, self).reset(new)

    @property
    def LINK_MASS_1(self):
        return self.mass

    @property
    def LINK_MASS_2(self):
        return self.mass

    @property
    def parameters(self):
        parameters = super(RandomHeavyAcrobot, self).parameters
        parameters.update({'mass': self.mass})
        return parameters

def __init__(self):
    super(RandomHeavyAcrobot, self).__init__()
    self.mass = self.np_random.uniform(self.RANDOM_LOWER_MASS, self.RANDOM_UPPER_MASS)

def reset(self, new=True):
    if new:
        self.mass = self.np_random.uniform(self.RANDOM_LOWER_MASS, self.RANDOM_UPPER_MASS)
    return super(RandomHeavyAcrobot, self).reset(new)

@property
def parameters(self):
    parameters = super(RandomHeavyAcrobot, self).parameters
    parameters.update({'mass': self.mass})
    return parameters

class RandomLightAcrobot(ModifiableAcrobotEnv):

    def __init__(self):
        super(RandomLightAcrobot, self).__init__()
        self.mass = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_MASS, self.EXTREME_UPPER_MASS, self.RANDOM_LOWER_MASS, self.RANDOM_UPPER_MASS)

    def reset(self, new=True):
        if new:
            self.mass = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_MASS, self.EXTREME_UPPER_MASS, self.RANDOM_LOWER_MASS, self.RANDOM_UPPER_MASS)
        return super(RandomLightAcrobot, self).reset(new)

    @property
    def LINK_MASS_1(self):
        return self.mass

    @property
    def LINK_MASS_2(self):
        return self.mass

    @property
    def parameters(self):
        parameters = super(RandomLightAcrobot, self).parameters
        parameters.update({'mass': self.mass})
        return parameters

def __init__(self):
    super(RandomLightAcrobot, self).__init__()
    self.mass = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_MASS, self.EXTREME_UPPER_MASS, self.RANDOM_LOWER_MASS, self.RANDOM_UPPER_MASS)

def reset(self, new=True):
    if new:
        self.mass = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_MASS, self.EXTREME_UPPER_MASS, self.RANDOM_LOWER_MASS, self.RANDOM_UPPER_MASS)
    return super(RandomLightAcrobot, self).reset(new)

@property
def parameters(self):
    parameters = super(RandomLightAcrobot, self).parameters
    parameters.update({'mass': self.mass})
    return parameters

class ShortAcrobot(ModifiableAcrobotEnv):

    def __init__(self):
        super(ShortAcrobot, self).__init__()
        self.length = self.EXTREME_LOWER_LENGTH

    @property
    def LINK_LENGTH_1(self):
        return self.length

    @property
    def LINK_LENGTH_2(self):
        return self.length

    @property
    def parameters(self):
        parameters = super(ShortAcrobot, self).parameters
        parameters.update({'length': self.length})
        return parameters

def __init__(self):
    super(ShortAcrobot, self).__init__()
    self.length = self.EXTREME_LOWER_LENGTH

@property
def parameters(self):
    parameters = super(ShortAcrobot, self).parameters
    parameters.update({'length': self.length})
    return parameters

class LongAcrobot(ModifiableAcrobotEnv):

    def __init__(self):
        super(LongAcrobot, self).__init__()
        self.length = self.EXTREME_UPPER_LENGTH

    @property
    def LINK_LENGTH_1(self):
        return self.length

    @property
    def LINK_LENGTH_2(self):
        return self.length

    @property
    def parameters(self):
        parameters = super(LongAcrobot, self).parameters
        parameters.update({'length': self.length})
        return parameters

def __init__(self):
    super(LongAcrobot, self).__init__()
    self.length = self.EXTREME_UPPER_LENGTH

@property
def parameters(self):
    parameters = super(LongAcrobot, self).parameters
    parameters.update({'length': self.length})
    return parameters

class RandomLongAcrobot(ModifiableAcrobotEnv):

    def __init__(self):
        super(RandomLongAcrobot, self).__init__()
        self.length = self.np_random.uniform(self.RANDOM_LOWER_LENGTH, self.RANDOM_UPPER_LENGTH)

    def reset(self, new=True):
        if new:
            self.length = self.np_random.uniform(self.RANDOM_LOWER_LENGTH, self.RANDOM_UPPER_LENGTH)
        return super(RandomLongAcrobot, self).reset(new)

    @property
    def LINK_LENGTH_1(self):
        return self.length

    @property
    def LINK_LENGTH_2(self):
        return self.length

    @property
    def parameters(self):
        parameters = super(RandomLongAcrobot, self).parameters
        parameters.update({'length': self.length})
        return parameters

def __init__(self):
    super(RandomLongAcrobot, self).__init__()
    self.length = self.np_random.uniform(self.RANDOM_LOWER_LENGTH, self.RANDOM_UPPER_LENGTH)

def reset(self, new=True):
    if new:
        self.length = self.np_random.uniform(self.RANDOM_LOWER_LENGTH, self.RANDOM_UPPER_LENGTH)
    return super(RandomLongAcrobot, self).reset(new)

@property
def parameters(self):
    parameters = super(RandomLongAcrobot, self).parameters
    parameters.update({'length': self.length})
    return parameters

class RandomShortAcrobot(ModifiableAcrobotEnv):

    def __init__(self):
        super(RandomShortAcrobot, self).__init__()
        self.length = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_LENGTH, self.EXTREME_UPPER_LENGTH, self.RANDOM_LOWER_LENGTH, self.RANDOM_UPPER_LENGTH)

    def reset(self, new=True):
        if new:
            self.length = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_LENGTH, self.EXTREME_UPPER_LENGTH, self.RANDOM_LOWER_LENGTH, self.RANDOM_UPPER_LENGTH)
        return super(RandomShortAcrobot, self).reset(new)

    @property
    def LINK_LENGTH_1(self):
        return self.length

    @property
    def LINK_LENGTH_2(self):
        return self.length

    @property
    def parameters(self):
        parameters = super(RandomShortAcrobot, self).parameters
        parameters.update({'length': self.length})
        return parameters

def __init__(self):
    super(RandomShortAcrobot, self).__init__()
    self.length = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_LENGTH, self.EXTREME_UPPER_LENGTH, self.RANDOM_LOWER_LENGTH, self.RANDOM_UPPER_LENGTH)

def reset(self, new=True):
    if new:
        self.length = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_LENGTH, self.EXTREME_UPPER_LENGTH, self.RANDOM_LOWER_LENGTH, self.RANDOM_UPPER_LENGTH)
    return super(RandomShortAcrobot, self).reset(new)

@property
def parameters(self):
    parameters = super(RandomShortAcrobot, self).parameters
    parameters.update({'length': self.length})
    return parameters

class LowInertiaAcrobot(ModifiableAcrobotEnv):

    def __init__(self):
        super(LowInertiaAcrobot, self).__init__()
        self.inertia = self.EXTREME_LOWER_INERTIA

    @property
    def LINK_MOI(self):
        return self.inertia

    @property
    def parameters(self):
        parameters = super(LowInertiaAcrobot, self).parameters
        parameters.update({'inertia': self.inertia})
        return parameters

def __init__(self):
    super(LowInertiaAcrobot, self).__init__()
    self.inertia = self.EXTREME_LOWER_INERTIA

@property
def parameters(self):
    parameters = super(LowInertiaAcrobot, self).parameters
    parameters.update({'inertia': self.inertia})
    return parameters

class HighInertiaAcrobot(ModifiableAcrobotEnv):

    def __init__(self):
        super(HighInertiaAcrobot, self).__init__()
        self.inertia = self.EXTREME_UPPER_INERTIA

    @property
    def LINK_MOI(self):
        return self.inertia

    @property
    def parameters(self):
        parameters = super(HighInertiaAcrobot, self).parameters
        parameters.update({'inertia': self.inertia})
        return parameters

def __init__(self):
    super(HighInertiaAcrobot, self).__init__()
    self.inertia = self.EXTREME_UPPER_INERTIA

@property
def parameters(self):
    parameters = super(HighInertiaAcrobot, self).parameters
    parameters.update({'inertia': self.inertia})
    return parameters

class RandomHighInertiaAcrobot(ModifiableAcrobotEnv):

    def __init__(self):
        super(RandomHighInertiaAcrobot, self).__init__()
        self.inertia = self.np_random.uniform(self.RANDOM_LOWER_INERTIA, self.RANDOM_UPPER_INERTIA)

    def reset(self, new=True):
        if new:
            self.inertia = self.np_random.uniform(self.RANDOM_LOWER_INERTIA, self.RANDOM_UPPER_INERTIA)
        return super(RandomHighInertiaAcrobot, self).reset(new)

    @property
    def LINK_MOI(self):
        return self.inertia

    @property
    def parameters(self):
        parameters = super(RandomHighInertiaAcrobot, self).parameters
        parameters.update({'inertia': self.inertia})
        return parameters

def __init__(self):
    super(RandomHighInertiaAcrobot, self).__init__()
    self.inertia = self.np_random.uniform(self.RANDOM_LOWER_INERTIA, self.RANDOM_UPPER_INERTIA)

def reset(self, new=True):
    if new:
        self.inertia = self.np_random.uniform(self.RANDOM_LOWER_INERTIA, self.RANDOM_UPPER_INERTIA)
    return super(RandomHighInertiaAcrobot, self).reset(new)

@property
def parameters(self):
    parameters = super(RandomHighInertiaAcrobot, self).parameters
    parameters.update({'inertia': self.inertia})
    return parameters

class RandomLowInertiaAcrobot(ModifiableAcrobotEnv):

    def __init__(self):
        super(RandomLowInertiaAcrobot, self).__init__()
        self.inertia = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_INERTIA, self.EXTREME_UPPER_INERTIA, self.RANDOM_LOWER_INERTIA, self.RANDOM_UPPER_INERTIA)

    def reset(self, new=True):
        if new:
            self.inertia = self.np_random.uniform(self.np_random.uniform, self.EXTREME_LOWER_INERTIA, self.EXTREME_UPPER_INERTIA, self.RANDOM_LOWER_INERTIA, self.RANDOM_UPPER_INERTIA)
        return super(RandomLowInertiaAcrobot, self).reset(new)

    @property
    def LINK_MOI(self):
        return self.inertia

    @property
    def parameters(self):
        parameters = super(RandomLowInertiaAcrobot, self).parameters
        parameters.update({'inertia': self.inertia})
        return parameters

def __init__(self):
    super(RandomLowInertiaAcrobot, self).__init__()
    self.inertia = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_INERTIA, self.EXTREME_UPPER_INERTIA, self.RANDOM_LOWER_INERTIA, self.RANDOM_UPPER_INERTIA)

def reset(self, new=True):
    if new:
        self.inertia = self.np_random.uniform(self.np_random.uniform, self.EXTREME_LOWER_INERTIA, self.EXTREME_UPPER_INERTIA, self.RANDOM_LOWER_INERTIA, self.RANDOM_UPPER_INERTIA)
    return super(RandomLowInertiaAcrobot, self).reset(new)

@property
def parameters(self):
    parameters = super(RandomLowInertiaAcrobot, self).parameters
    parameters.update({'inertia': self.inertia})
    return parameters

class RandomNormalAcrobot(ModifiableAcrobotEnv):

    @property
    def LINK_MASS_1(self):
        return self.mass

    @property
    def LINK_MASS_2(self):
        return self.mass

    @property
    def LINK_LENGTH_1(self):
        return self.length

    @property
    def LINK_LENGTH_2(self):
        return self.length

    @property
    def LINK_MOI(self):
        return self.inertia

    def __init__(self):
        super(RandomNormalAcrobot, self).__init__()
        self.mass = self.np_random.uniform(self.RANDOM_LOWER_MASS, self.RANDOM_UPPER_MASS)
        self.length = self.np_random.uniform(self.RANDOM_LOWER_LENGTH, self.RANDOM_UPPER_LENGTH)
        self.inertia = self.np_random.uniform(self.RANDOM_LOWER_INERTIA, self.RANDOM_UPPER_INERTIA)

    def reset(self, new=True):
        if new:
            self.mass = self.np_random.uniform(self.RANDOM_LOWER_MASS, self.RANDOM_UPPER_MASS)
            self.length = self.np_random.uniform(self.RANDOM_LOWER_LENGTH, self.RANDOM_UPPER_LENGTH)
            self.inertia = self.np_random.uniform(self.RANDOM_LOWER_INERTIA, self.RANDOM_UPPER_INERTIA)
        return super(RandomNormalAcrobot, self).reset()

    @property
    def parameters(self):
        parameters = super(RandomNormalAcrobot, self).parameters
        parameters.update({'mass': self.mass, 'length': self.length, 'inertia': self.inertia})
        return parameters

def __init__(self):
    super(RandomNormalAcrobot, self).__init__()
    self.mass = self.np_random.uniform(self.RANDOM_LOWER_MASS, self.RANDOM_UPPER_MASS)
    self.length = self.np_random.uniform(self.RANDOM_LOWER_LENGTH, self.RANDOM_UPPER_LENGTH)
    self.inertia = self.np_random.uniform(self.RANDOM_LOWER_INERTIA, self.RANDOM_UPPER_INERTIA)

def reset(self, new=True):
    if new:
        self.mass = self.np_random.uniform(self.RANDOM_LOWER_MASS, self.RANDOM_UPPER_MASS)
        self.length = self.np_random.uniform(self.RANDOM_LOWER_LENGTH, self.RANDOM_UPPER_LENGTH)
        self.inertia = self.np_random.uniform(self.RANDOM_LOWER_INERTIA, self.RANDOM_UPPER_INERTIA)
    return super(RandomNormalAcrobot, self).reset()

@property
def parameters(self):
    parameters = super(RandomNormalAcrobot, self).parameters
    parameters.update({'mass': self.mass, 'length': self.length, 'inertia': self.inertia})
    return parameters

class RandomExtremeAcrobot(ModifiableAcrobotEnv):

    @property
    def LINK_MASS_1(self):
        return self.mass

    @property
    def LINK_MASS_2(self):
        return self.mass

    @property
    def LINK_LENGTH_1(self):
        return self.length

    @property
    def LINK_LENGTH_2(self):
        return self.length

    @property
    def LINK_MOI(self):
        return self.inertia

    def __init__(self):
        super(RandomExtremeAcrobot, self).__init__()
        self.mass = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_MASS, self.EXTREME_UPPER_MASS, self.RANDOM_LOWER_MASS, self.RANDOM_UPPER_MASS)
        self.length = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_LENGTH, self.EXTREME_UPPER_LENGTH, self.RANDOM_LOWER_LENGTH, self.RANDOM_UPPER_LENGTH)
        self.inertia = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_INERTIA, self.EXTREME_UPPER_INERTIA, self.RANDOM_LOWER_INERTIA, self.RANDOM_UPPER_INERTIA)

    def reset(self, new=True):
        if new:
            self.mass = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_MASS, self.EXTREME_UPPER_MASS, self.RANDOM_LOWER_MASS, self.RANDOM_UPPER_MASS)
            self.length = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_LENGTH, self.EXTREME_UPPER_LENGTH, self.RANDOM_LOWER_LENGTH, self.RANDOM_UPPER_LENGTH)
            self.inertia = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_INERTIA, self.EXTREME_UPPER_INERTIA, self.RANDOM_LOWER_INERTIA, self.RANDOM_UPPER_INERTIA)
        return super(RandomExtremeAcrobot, self).reset(new)

    @property
    def parameters(self):
        parameters = super(RandomExtremeAcrobot, self).parameters
        parameters.update({'mass': self.mass, 'length': self.length, 'inertia': self.inertia})
        return parameters

def __init__(self):
    super(RandomExtremeAcrobot, self).__init__()
    self.mass = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_MASS, self.EXTREME_UPPER_MASS, self.RANDOM_LOWER_MASS, self.RANDOM_UPPER_MASS)
    self.length = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_LENGTH, self.EXTREME_UPPER_LENGTH, self.RANDOM_LOWER_LENGTH, self.RANDOM_UPPER_LENGTH)
    self.inertia = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_INERTIA, self.EXTREME_UPPER_INERTIA, self.RANDOM_LOWER_INERTIA, self.RANDOM_UPPER_INERTIA)

def reset(self, new=True):
    if new:
        self.mass = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_MASS, self.EXTREME_UPPER_MASS, self.RANDOM_LOWER_MASS, self.RANDOM_UPPER_MASS)
        self.length = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_LENGTH, self.EXTREME_UPPER_LENGTH, self.RANDOM_LOWER_LENGTH, self.RANDOM_UPPER_LENGTH)
        self.inertia = uniform_exclude_inner(self.np_random.uniform, self.EXTREME_LOWER_INERTIA, self.EXTREME_UPPER_INERTIA, self.RANDOM_LOWER_INERTIA, self.RANDOM_UPPER_INERTIA)
    return super(RandomExtremeAcrobot, self).reset(new)

@property
def parameters(self):
    parameters = super(RandomExtremeAcrobot, self).parameters
    parameters.update({'mass': self.mass, 'length': self.length, 'inertia': self.inertia})
    return parameters

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

class PhysicalEnvironment:
    """Physical environment based on Box2D/Cocos2D."""

    def __init__(self, world):
        width = 640
        height = 480
        window = getattr(cocos.director.director, 'window', None)
        if window is None:
            pyglet.resource.path = [ASSET_PATH]
            pyglet.resource.reindex()
            window = cocos.director.director.init(width=width, height=height)
        self._window = window
        self._width = width
        self._height = height
        self._world = world(width=width, height=height)
        self._scene = cocos.scene.Scene(cocos.layer.ColorLayer(0, 0, 0, 255), self._world)

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def world(self):
        return self._world

    @property
    def is_terminal(self):
        return self._world.is_terminal

    def step(self):
        """Perform one environment update step."""
        self._world.step()
        return self.is_terminal

    def reset(self):
        """Reset the world."""
        self._world.reset_world()

    def act(self, action):
        """Perform an action on the world."""
        self._world.act(action)

    def seed(self, seed=None):
        """Seed random number generator."""
        return self._world.seed(seed)

    def render(self, mode='human'):
        """Render the environment."""
        if cocos.director.director.scene != self._scene:
            cocos.director.director._set_scene(self._scene)
        self._window.switch_to()
        self._window.dispatch_events()
        self._window.dispatch_event('on_draw')
        if mode == 'human':
            self._window.flip()
        elif mode == 'rgb_array':
            color_buffer = pyglet.image.get_buffer_manager().get_color_buffer()
            image_data = color_buffer.get_image_data()
            data = np.fromstring(image_data.data, dtype=np.uint8, sep='')
            data = data.reshape(color_buffer.height, color_buffer.width, 4)
            data = data[::-1, :, 0:3]
            return data

def reset(self):
    """Reset the world."""
    self._world.reset_world()

class GymEnvironment(BaseGymEnvironment):
    metadata = {'render.modes': ['human', 'rgb_array'], 'video.frames_per_second': 50}
    worlds = None

    def __init__(self, obs_type='image', frameskip=4, world='baseline'):
        self._env = PhysicalEnvironment(world=self.worlds[world])
        self._world = world
        self.action_space = spaces.Discrete(self._env.world.n_actions)
        if obs_type == 'image':
            self.observation_space = spaces.Box(low=0, high=255, shape=(self._env.height, self._env.width, 3))
        else:
            raise error.Error('Unrecognized observation type: {}'.format(obs_type))
        self._obs_type = obs_type
        self._frameskip = frameskip

    def __getstate__(self):
        return {'obs_type': self._obs_type, 'frameskip': self._frameskip, 'world': self._world}

    def __setstate__(self, state):
        self.__init__(**state)

    def _get_observation(self):
        if self._obs_type == 'image':
            return self._env.render(mode='rgb_array')
        raise NotImplementedError

    def _reset(self):
        self._env.reset()
        self._env.step()
        return self._get_observation()

    def _seed(self, seed=None):
        seed = self._env.seed(seed)
        return [seed]

    def _step(self, action):
        score = self._env.world.score
        self._env.act(action)
        for _ in range(self._frameskip):
            terminal = self._env.step()
            if terminal:
                break
        observation = self._get_observation()
        reward = self._env.world.score - score
        info = {'lives': self._env.world.lives}
        return (observation, reward, terminal, info)

    def _render(self, mode='human', close=False):
        if close:
            return
        return self._env.render(mode)

    def get_action_meanings(self):
        return []

    @property
    def lives(self):
        return self._env.world.lives

    @property
    def parameters(self):
        parameters = super(GymEnvironment, self).parameters
        parameters.update(self._env.world.parameters)
        return parameters

def __setstate__(self, state):
    self.__init__(**state)

@property
def parameters(self):
    parameters = super(GymEnvironment, self).parameters
    parameters.update(self._env.world.parameters)
    return parameters

class Ball(PhysicalObject):
    """Ball object."""
    asset = 'ball.png'
    max_speed = 9.0

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('scale', 0.25)
        kwargs.setdefault('color', (208, 33, 82))
        super(Ball, self).__init__(self.asset, *args, **kwargs)

    def create_physical_entity(self):
        body = self._engine.CreateDynamicBody(position=self.physical_position, fixedRotation=True)
        body.CreateCircleFixture(radius=self.width / 2 / self._world.physical_scale, density=1.0, friction=0.0, restitution=1.0)
        return body

    def step(self):
        super(Ball, self).step()
        speed = self._body.linearVelocity.length
        if speed > self.max_speed:
            self._body.linearDamping = 0.5
        elif speed < self.max_speed:
            self._body.linearDamping = 0.0

    def on_contact(self, other):
        """Prevent the ball from bouncing in a straight line up and down."""
        velocity_x = self.body.linearVelocity[0]
        if abs(velocity_x) < 0.1:
            self.apply_impulse([self._world.np_random.uniform(-0.1, 0.1), 0.0])

def __init__(self, *args, **kwargs):
    kwargs.setdefault('scale', 0.25)
    kwargs.setdefault('color', (208, 33, 82))
    super(Ball, self).__init__(self.asset, *args, **kwargs)

class Paddle(PhysicalObject):
    """Paddle object."""
    asset = 'paddle.png'

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('color', (255, 168, 0))
        super(Paddle, self).__init__(self.asset, *args, **kwargs)

    def create_physical_entity(self):
        body = self._engine.CreateDynamicBody(position=self.physical_position, angle=self.physical_rotation, linearDamping=0.99, fixedRotation=True)
        body.CreatePolygonFixture(box=(self.width / 2.0 / self._world.physical_scale, self.height / 2.0 / self._world.physical_scale), density=1.0, friction=0.0, restitution=0.0)
        joint = box_2d.b2PrismaticJointDef()
        joint.Initialize(body, self._world.ground, body.worldCenter, (1.0, 0.0))
        joint.collideConnected = True
        self._engine.CreateJoint(joint)
        return body

def __init__(self, *args, **kwargs):
    kwargs.setdefault('color', (255, 168, 0))
    super(Paddle, self).__init__(self.asset, *args, **kwargs)

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

def __init__(self, *args, **kwargs):
    self.row = kwargs.pop('row')
    self.column = kwargs.pop('column')
    kwargs['color'] = self.get_color()
    super(Brick, self).__init__('brick.png', *args, **kwargs)

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

@property
def parameters(self):
    parameters = super(BreakoutWorld, self).parameters
    parameters.update({'world': 'breakout'})
    return parameters

class OffsetPaddleBreakoutWorld(BreakoutWorld):
    paddle_offset = 100

    def initial_paddle_position(self):
        """Initial paddle position after reset."""
        return (self._width / 2, self.paddle_offset)

    @property
    def parameters(self):
        parameters = super(OffsetPaddleBreakoutWorld, self).parameters
        parameters.update({'paddle_offset': self.paddle_offset})
        return parameters

@property
def parameters(self):
    parameters = super(OffsetPaddleBreakoutWorld, self).parameters
    parameters.update({'paddle_offset': self.paddle_offset})
    return parameters

class RandomOffsetPaddleBreakoutWorld(BreakoutWorld):
    offset_range_start = 25
    offset_range_end = 110

    def initial_paddle_position(self):
        """Initial paddle position after reset."""
        self._paddle_offset = int(self.np_random.uniform(self.offset_range_start, self.offset_range_end))
        return (self._width / 2, self._paddle_offset)

    @property
    def parameters(self):
        parameters = super(RandomOffsetPaddleBreakoutWorld, self).parameters
        parameters.update({'paddle_offset': self._paddle_offset})
        return parameters

@property
def parameters(self):
    parameters = super(RandomOffsetPaddleBreakoutWorld, self).parameters
    parameters.update({'paddle_offset': self._paddle_offset})
    return parameters

class VisuallyFixedOffsetPaddle(Paddle):
    """Paddle, which is visually at fixed offset, but physically at some other offset."""

    @property
    def visual_position(self):
        """Return visual object position."""
        position = super(VisuallyFixedOffsetPaddle, self).visual_position
        return (position[0], 25)

@property
def visual_position(self):
    """Return visual object position."""
    position = super(VisuallyFixedOffsetPaddle, self).visual_position
    return (position[0], 25)

class Obstacle(PhysicalObject):
    """Obstacle object."""

    def __init__(self, *args, **kwargs):
        kwargs['color'] = (80, 80, 80)
        super(Obstacle, self).__init__('obstacle.png', *args, **kwargs)

    def create_physical_entity(self):
        body = self._engine.CreateStaticBody(position=self.physical_position)
        body.CreatePolygonFixture(box=(self.width / 2.0 / self._world.physical_scale, self.height / 2.0 / self._world.physical_scale), density=10.0, friction=0.0, restitution=0.0)
        return body

def __init__(self, *args, **kwargs):
    kwargs['color'] = (80, 80, 80)
    super(Obstacle, self).__init__('obstacle.png', *args, **kwargs)

class SideObstacle(PhysicalObject):
    """Side obstacle object."""

    def __init__(self, *args, **kwargs):
        image = pyglet.resource.image('side_obstacle.png')
        width = kwargs.pop('width', None)
        if width is not None:
            image = image.get_region(0, 0, width, image.height)
        kwargs['color'] = (80, 80, 80)
        super(SideObstacle, self).__init__(image, *args, **kwargs)

    def create_physical_entity(self):
        body = self._engine.CreateStaticBody(position=self.physical_position)
        body.CreatePolygonFixture(box=(self.width / 2.0 / self._world.physical_scale, self.height / 2.0 / self._world.physical_scale), density=10.0, friction=0.0, restitution=0.0)
        return body

def __init__(self, *args, **kwargs):
    image = pyglet.resource.image('side_obstacle.png')
    width = kwargs.pop('width', None)
    if width is not None:
        image = image.get_region(0, 0, width, image.height)
    kwargs['color'] = (80, 80, 80)
    super(SideObstacle, self).__init__(image, *args, **kwargs)

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

def reset_world(self):
    super(RandomSideObstacleBreakoutWorld, self).reset_world()
    self.reset_obstacle()

@property
def parameters(self):
    parameters = super(RandomSideObstacleBreakoutWorld, self).parameters
    parameters.update({'obstacle_side': self._obstacle_side, 'obstacle_width': self._obstacle_width})
    return parameters

class BigBall(Ball):
    """A bigger ball object."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('scale', 0.5)
        super(BigBall, self).__init__(*args, **kwargs)

def __init__(self, *args, **kwargs):
    kwargs.setdefault('scale', 0.5)
    super(BigBall, self).__init__(*args, **kwargs)

class HugeBall(Ball):
    """A huge ball object."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('scale', 0.75)
        super(HugeBall, self).__init__(*args, **kwargs)

def __init__(self, *args, **kwargs):
    kwargs.setdefault('scale', 0.75)
    super(HugeBall, self).__init__(*args, **kwargs)

class WhiteBall(Ball):
    """White ball object."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('color', (255, 255, 255))
        super(WhiteBall, self).__init__(*args, **kwargs)

def __init__(self, *args, **kwargs):
    kwargs.setdefault('color', (255, 255, 255))
    super(WhiteBall, self).__init__(*args, **kwargs)

class WhitePaddle(Paddle):
    """White paddle object."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('color', (255, 255, 255))
        super(WhitePaddle, self).__init__(*args, **kwargs)

def __init__(self, *args, **kwargs):
    kwargs.setdefault('color', (255, 255, 255))
    super(WhitePaddle, self).__init__(*args, **kwargs)

class Scaled80BreakoutWorld(BreakoutWorld):

    def __init__(self, *args, **kwargs):
        super(Scaled80BreakoutWorld, self).__init__(*args, **kwargs)
        self.scale = 0.8

def __init__(self, *args, **kwargs):
    super(Scaled80BreakoutWorld, self).__init__(*args, **kwargs)
    self.scale = 0.8

class Scaled90BreakoutWorld(BreakoutWorld):

    def __init__(self, *args, **kwargs):
        super(Scaled90BreakoutWorld, self).__init__(*args, **kwargs)
        self.scale = 0.9

def __init__(self, *args, **kwargs):
    super(Scaled90BreakoutWorld, self).__init__(*args, **kwargs)
    self.scale = 0.9

class Scaled95BreakoutWorld(BreakoutWorld):

    def __init__(self, *args, **kwargs):
        super(Scaled95BreakoutWorld, self).__init__(*args, **kwargs)
        self.scale = 0.95

def __init__(self, *args, **kwargs):
    super(Scaled95BreakoutWorld, self).__init__(*args, **kwargs)
    self.scale = 0.95

class Scaled99BreakoutWorld(BreakoutWorld):

    def __init__(self, *args, **kwargs):
        super(Scaled99BreakoutWorld, self).__init__(*args, **kwargs)
        self.scale = 0.99

def __init__(self, *args, **kwargs):
    super(Scaled99BreakoutWorld, self).__init__(*args, **kwargs)
    self.scale = 0.99

class RandomScaledBreakoutWorld(BreakoutWorld):
    scale_range_start = 0.95
    scale_range_end = 1.0

    def reset_world(self):
        super(RandomScaledBreakoutWorld, self).reset_world()
        self.scale = self.np_random.uniform(self.scale_range_start, self.scale_range_end)

    @property
    def parameters(self):
        parameters = super(RandomScaledBreakoutWorld, self).parameters
        parameters.update({'scale': self.scale})
        return parameters

def reset_world(self):
    super(RandomScaledBreakoutWorld, self).reset_world()
    self.scale = self.np_random.uniform(self.scale_range_start, self.scale_range_end)

@property
def parameters(self):
    parameters = super(RandomScaledBreakoutWorld, self).parameters
    parameters.update({'scale': self.scale})
    return parameters

class RandomActionStrengthBreakoutWorld(BreakoutWorld):
    impulse_range_start = 30
    impulse_range_end = 170

    def reset_world(self):
        super(RandomActionStrengthBreakoutWorld, self).reset_world()
        self._impulse_strength = self.np_random.uniform(self.impulse_range_start, self.impulse_range_end)

    def paddle_impulse(self):
        return self._impulse_strength

    @property
    def parameters(self):
        parameters = super(RandomActionStrengthBreakoutWorld, self).parameters
        parameters.update({'impulse_strength': self._impulse_strength})
        return parameters

def reset_world(self):
    super(RandomActionStrengthBreakoutWorld, self).reset_world()
    self._impulse_strength = self.np_random.uniform(self.impulse_range_start, self.impulse_range_end)

@property
def parameters(self):
    parameters = super(RandomActionStrengthBreakoutWorld, self).parameters
    parameters.update({'impulse_strength': self._impulse_strength})
    return parameters

class RandomRotatedPaddleBreakoutWorld(BreakoutWorld):
    rotation_range_start = -90
    rotation_range_end = 90

    def initial_paddle_rotation(self):
        """Initial paddle rotation after reset."""
        self._paddle_rotation = self.np_random.uniform(self.rotation_range_start, self.rotation_range_end)
        return self._paddle_rotation

    @property
    def parameters(self):
        parameters = super(RandomRotatedPaddleBreakoutWorld, self).parameters
        parameters.update({'paddle_rotation': self._paddle_rotation})
        return parameters

def initial_paddle_rotation(self):
    """Initial paddle rotation after reset."""
    self._paddle_rotation = self.np_random.uniform(self.rotation_range_start, self.rotation_range_end)
    return self._paddle_rotation

@property
def parameters(self):
    parameters = super(RandomRotatedPaddleBreakoutWorld, self).parameters
    parameters.update({'paddle_rotation': self._paddle_rotation})
    return parameters

class RandomOffsetBricksBreakoutWorld(BreakoutWorld):
    brick_offset_range_start = 0
    brick_offset_range_end = 80

    def initial_brick_position(self):
        """Initial brick row offset after reset."""
        self._brick_offset = int(self.np_random.uniform(self.brick_offset_range_start, self.brick_offset_range_end))
        return self._brick_offset

    @property
    def parameters(self):
        parameters = super(RandomOffsetBricksBreakoutWorld, self).parameters
        parameters.update({'brick_offset': self._brick_offset})
        return parameters

@property
def parameters(self):
    parameters = super(RandomOffsetBricksBreakoutWorld, self).parameters
    parameters.update({'brick_offset': self._brick_offset})
    return parameters

class DoorSprite(plab_things.Sprite):
    """Sprite for the door."""

    def __init__(self, corner, position, character, pickup_reward):
        super(DoorSprite, self).__init__(corner, position, character)
        self._pickup_reward = pickup_reward

    def update(self, actions, board, layers, backdrop, things, the_plot):
        player_position = things[common.PLAYER].position
        pick_up = self.position == player_position
        if pick_up and the_plot.get('has_key'):
            the_plot.add_reward(self._pickup_reward)
            the_plot['has_key'] = False

def __init__(self, corner, position, character, pickup_reward):
    super(DoorSprite, self).__init__(corner, position, character)
    self._pickup_reward = pickup_reward

class PlayerSprite(common.PlayerSprite):
    """Sprite for the actor."""

    def __init__(self, corner, position, character):
        super(PlayerSprite, self).__init__(corner, position, character, impassable=common.BORDER + common.INDICATOR + common.DOOR)

    def update(self, actions, board, layers, backdrop, things, the_plot):
        if common.DOOR in self.impassable and the_plot.get('has_key'):
            self._impassable.remove(common.DOOR)
        super(PlayerSprite, self).update(actions, board, layers, backdrop, things, the_plot)

def __init__(self, corner, position, character):
    super(PlayerSprite, self).__init__(corner, position, character, impassable=common.BORDER + common.INDICATOR + common.DOOR)

def update(self, actions, board, layers, backdrop, things, the_plot):
    if common.DOOR in self.impassable and the_plot.get('has_key'):
        self._impassable.remove(common.DOOR)
    super(PlayerSprite, self).update(actions, board, layers, backdrop, things, the_plot)

class PlayerSprite(prefab_sprites.MazeWalker):
    """Sprite representing the agent."""

    def __init__(self, corner, position, character, max_steps_per_act, moving_player):
        """Indicates to the superclass that we can't walk off the board."""
        super(PlayerSprite, self).__init__(corner, position, character, impassable=[common.BORDER], confined_to_board=True)
        self._moving_player = moving_player
        self._max_steps_per_act = max_steps_per_act
        self._num_steps = 0

    def update(self, actions, board, layers, backdrop, things, the_plot):
        del backdrop
        if actions is not None:
            assert actions in common.ACTIONS
        the_plot.log('Step {} | Action {}'.format(self._num_steps, actions))
        the_plot.add_reward(0.0)
        self._num_steps += 1
        if actions == common.ACTION_QUIT:
            the_plot.terminate_episode()
        if self._moving_player:
            if actions == common.ACTION_WEST:
                self._west(board, the_plot)
            elif actions == common.ACTION_EAST:
                self._east(board, the_plot)
            elif actions == common.ACTION_NORTH:
                self._north(board, the_plot)
            elif actions == common.ACTION_SOUTH:
                self._south(board, the_plot)
        if self._max_steps_per_act == self._num_steps:
            the_plot.terminate_episode()

def __init__(self, corner, position, character, max_steps_per_act, moving_player):
    """Indicates to the superclass that we can't walk off the board."""
    super(PlayerSprite, self).__init__(corner, position, character, impassable=[common.BORDER], confined_to_board=True)
    self._moving_player = moving_player
    self._max_steps_per_act = max_steps_per_act
    self._num_steps = 0

class ObjectSprite(plab_things.Sprite):
    """Sprite for a generic object which can be collectable."""

    def __init__(self, corner, position, character, reward=0.0, collectable=True, terminate=True):
        super(ObjectSprite, self).__init__(corner, position, character)
        self._reward = reward
        self._collectable = collectable

    def set_visibility(self, visible):
        self._visible = visible

    def update(self, actions, board, layers, backdrop, things, the_plot):
        player_position = things[common.PLAYER].position
        pick_up = self.position == player_position
        if pick_up and self.visible:
            the_plot.add_reward(self._reward)
            if self._collectable:
                self.set_visibility(False)
                for v in itervalues(things):
                    if isinstance(v, ObjectSprite):
                        v.set_visibility(False)

def __init__(self, corner, position, character, reward=0.0, collectable=True, terminate=True):
    super(ObjectSprite, self).__init__(corner, position, character)
    self._reward = reward
    self._collectable = collectable

class IndicatorObjectSprite(plab_things.Sprite):
    """Sprite for the indicator object.

    The indicator object is an object that spawns at a designated position once
    the player picks up an object defined by the `char_to_track` argument.
    The indicator object is spawned for just a single frame.
    """

    def __init__(self, corner, position, character, char_to_track, override_position=None):
        super(IndicatorObjectSprite, self).__init__(corner, position, character)
        if override_position is not None:
            self._position = override_position
        self._char_to_track = char_to_track
        self._visible = False
        self._pickup_frame = None

    def update(self, actions, board, layers, backdrop, things, the_plot):
        player_position = things[common.PLAYER].position
        pick_up = things[self._char_to_track].position == player_position
        if self._pickup_frame:
            self._visible = False
        if pick_up and (not self._pickup_frame):
            self._visible = True
            self._pickup_frame = the_plot.frame

def __init__(self, corner, position, character, char_to_track, override_position=None):
    super(IndicatorObjectSprite, self).__init__(corner, position, character)
    if override_position is not None:
        self._position = override_position
    self._char_to_track = char_to_track
    self._visible = False
    self._pickup_frame = None

class PlayerSprite(prefab_sprites.MazeWalker):
    """Sprite for the actor."""

    def __init__(self, corner, position, character, impassable=BORDER):
        super(PlayerSprite, self).__init__(corner, position, character, impassable=impassable, confined_to_board=True)

    def update(self, actions, board, layers, backdrop, things, the_plot):
        the_plot.add_reward(0.0)
        if actions == ACTION_QUIT:
            the_plot.next_chapter = None
            the_plot.terminate_episode()
        if actions == ACTION_WEST:
            self._west(board, the_plot)
        elif actions == ACTION_EAST:
            self._east(board, the_plot)
        elif actions == ACTION_NORTH:
            self._north(board, the_plot)
        elif actions == ACTION_SOUTH:
            self._south(board, the_plot)

def __init__(self, corner, position, character, impassable=BORDER):
    super(PlayerSprite, self).__init__(corner, position, character, impassable=impassable, confined_to_board=True)

class ExampleEnv(gym.Env):

    def __init__(self):
        super(ExampleEnv, self).__init__()

    def get_task(self):
        """
        Return a task description, such as goal position or target velocity.
        """
        pass

    def set_goal(self, goal):
        """
        Sets goal manually. Mainly used for reward relabelling.
        """
        pass

    def reset_task(self, task=None):
        """
        Reset the task, either at random (if task=None) or the given task.
        """
        pass

    def step(self, action):
        """
        Execute one step in the environment.
        Should return: state, reward, done, info
        where info has to include a field 'task'.
        """
        pass

    def reward(self, state, action):
        """
        Computes reward function of task.
        Returns the reward
        """
        pass

    def reset(self):
        """
        Reset the environment. This should *NOT* reset the task!
        Resetting the task is handled in the varibad wrapper (see wrappers.py).
        """
        pass

def __init__(self):
    super(ExampleEnv, self).__init__()

class TimeLimitMask(gym.Wrapper):

    def step(self, action):
        obs, rew, done, info = self.env.step(action)
        if done and self.env._max_episode_steps == self.env._elapsed_steps:
            info['bad_transition'] = True
        return (obs, rew, done, info)

    def reset(self, **kwargs):
        return self.env.reset(**kwargs)

def reset(self, **kwargs):
    return self.env.reset(**kwargs)

class AntEnv(MujocoEnv):

    def __init__(self, use_low_gear_ratio=False):
        if use_low_gear_ratio:
            xml_path = 'low_gear_ratio_ant.xml'
        else:
            xml_path = 'ant.xml'
        super().__init__(xml_path, frame_skip=5, automatically_set_obs_and_action_space=True)

    def step(self, a):
        torso_xyz_before = self.get_body_com('torso')
        self.do_simulation(a, self.frame_skip)
        torso_xyz_after = self.get_body_com('torso')
        torso_velocity = torso_xyz_after - torso_xyz_before
        forward_reward = torso_velocity[0] / self.dt
        ctrl_cost = 0.0
        contact_cost = 0.5 * 0.001 * np.sum(np.square(np.clip(self.sim.data.cfrc_ext, -1, 1)))
        survive_reward = 0.0
        reward = forward_reward - ctrl_cost - contact_cost + survive_reward
        state = self.state_vector()
        notdone = np.isfinite(state).all() and state[2] >= 0.2 and (state[2] <= 1.0)
        done = not notdone
        ob = self._get_obs()
        return (ob, reward, done, dict(reward_forward=forward_reward, reward_ctrl=-ctrl_cost, reward_contact=-contact_cost, reward_survive=survive_reward, torso_velocity=torso_velocity))

    def _get_obs(self):
        return np.concatenate([self.sim.data.qpos.flat[2:], self.sim.data.qvel.flat])

    def reset_model(self):
        qpos = self.init_qpos + self.np_random.uniform(size=self.model.nq, low=-0.1, high=0.1)
        qvel = self.init_qvel + self.np_random.randn(self.model.nv) * 0.1
        self.set_state(qpos, qvel)
        return self._get_obs()

    def viewer_setup(self):
        self.viewer.cam.distance = self.model.stat.extent * 0.5

def __init__(self, use_low_gear_ratio=False):
    if use_low_gear_ratio:
        xml_path = 'low_gear_ratio_ant.xml'
    else:
        xml_path = 'ant.xml'
    super().__init__(xml_path, frame_skip=5, automatically_set_obs_and_action_space=True)

class HalfCheetahVelEnv(HalfCheetahEnv):
    """Half-cheetah environment with target velocity, as described in [1]. The
    code is adapted from
    https://github.com/cbfinn/maml_rl/blob/9c8e2ebd741cb0c7b8bf2d040c4caeeb8e06cc95/rllab/envs/mujoco/half_cheetah_env_rand.py
    The half-cheetah follows the dynamics from MuJoCo [2], and receives at each
    time step a reward composed of a control cost and a penalty equal to the
    difference between its current velocity and the target velocity. The tasks
    are generated by sampling the target velocities from the uniform
    distribution on [0, 3].
    [1] Chelsea Finn, Pieter Abbeel, Sergey Levine, "Model-Agnostic
        Meta-Learning for Fast Adaptation of Deep Networks", 2017
        (https://arxiv.org/abs/1703.03400)
    [2] Emanuel Todorov, Tom Erez, Yuval Tassa, "MuJoCo: A physics engine for
        model-based control", 2012
        (https://homes.cs.washington.edu/~todorov/papers/TodorovIROS12.pdf)
    """

    def __init__(self, task={}, n_tasks=2, max_episode_steps=200, **kwargs):
        self._task = task
        self.n_tasks = n_tasks
        self.tasks = self.sample_tasks(n_tasks)
        self._goal_vel = self.tasks[0].get('velocity', 0.0)
        self._goal = self._goal_vel
        self._max_episode_steps = max_episode_steps
        super(HalfCheetahVelEnv, self).__init__()

    def step(self, action):
        xposbefore = self.sim.data.qpos[0]
        self.do_simulation(action, self.frame_skip)
        xposafter = self.sim.data.qpos[0]
        forward_vel = (xposafter - xposbefore) / self.dt
        forward_reward = -1.0 * abs(forward_vel - self._goal_vel)
        ctrl_cost = 0.5 * 0.1 * np.sum(np.square(action))
        observation = self._get_obs()
        reward = forward_reward - ctrl_cost
        done = False
        infos = dict(reward_forward=forward_reward, reward_ctrl=-ctrl_cost, task=self._task)
        return (observation, reward, done, infos)

    def set_goal(self, goal):
        self._goal = np.asarray(goal)

    def sample_tasks(self, num_tasks):
        velocities = np.random.uniform(0.0, 3.0, size=(num_tasks,))
        tasks = [{'velocity': velocity} for velocity in velocities]
        return tasks

    def get_current_task(self):
        return np.array([self._goal_vel])

    def get_all_task_idx(self):
        return range(len(self.tasks))

    def reset_task(self, idx):
        self._task = self.tasks[idx]
        self._goal_vel = self._task['velocity']
        self._goal = self._goal_vel
        self.reset()

    def reward(self, state, action):
        """Here, state is previous state! r_t = r(s_{t-1}, a_t)
        NOTE: it should be r(st-1, at, st) though det dynamics
        """
        qpos = np.concatenate([np.array([0.0]), state[:8]])
        qvel = state[8:17]
        self.set_state(qpos, qvel)
        xposbefore = self.sim.data.qpos[0]
        self.do_simulation(action, self.frame_skip)
        xposafter = self.sim.data.qpos[0]
        forward_vel = (xposafter - xposbefore) / self.dt
        forward_reward = -1.0 * abs(forward_vel - self._goal_vel)
        ctrl_cost = 0.5 * 0.1 * np.sum(np.square(action))
        reward = forward_reward - ctrl_cost
        return reward

def __init__(self, task={}, n_tasks=2, max_episode_steps=200, **kwargs):
    self._task = task
    self.n_tasks = n_tasks
    self.tasks = self.sample_tasks(n_tasks)
    self._goal_vel = self.tasks[0].get('velocity', 0.0)
    self._goal = self._goal_vel
    self._max_episode_steps = max_episode_steps
    super(HalfCheetahVelEnv, self).__init__()

def sample_tasks(self, num_tasks):
    velocities = np.random.uniform(0.0, 3.0, size=(num_tasks,))
    tasks = [{'velocity': velocity} for velocity in velocities]
    return tasks

def reset_task(self, idx):
    self._task = self.tasks[idx]
    self._goal_vel = self._task['velocity']
    self._goal = self._goal_vel
    self.reset()

class HalfCheetahDirEnv(HalfCheetahEnv):
    """Half-cheetah environment with target direction, as described in [1]. The
    code is adapted from
    https://github.com/cbfinn/maml_rl/blob/9c8e2ebd741cb0c7b8bf2d040c4caeeb8e06cc95/rllab/envs/mujoco/half_cheetah_env_rand_direc.py

    The half-cheetah follows the dynamics from MuJoCo [2], and receives at each
    time step a reward composed of a control cost and a reward equal to its
    velocity in the target direction. The tasks are generated by sampling the
    target directions from a Bernoulli distribution on {-1, 1} with parameter
    0.5 (-1: backward, +1: forward).

    [1] Chelsea Finn, Pieter Abbeel, Sergey Levine, "Model-Agnostic
        Meta-Learning for Fast Adaptation of Deep Networks", 2017
        (https://arxiv.org/abs/1703.03400)
    [2] Emanuel Todorov, Tom Erez, Yuval Tassa, "MuJoCo: A physics engine for
        model-based control", 2012
        (https://homes.cs.washington.edu/~todorov/papers/TodorovIROS12.pdf)
    """

    def __init__(self, n_tasks=None, max_episode_steps=200):
        self.n_tasks = n_tasks
        assert n_tasks == None
        self._goal = self._sample_raw_task()['goal']
        self._max_episode_steps = max_episode_steps
        super(HalfCheetahDirEnv, self).__init__()

    def step(self, action):
        xposbefore = self.sim.data.qpos[0]
        self.do_simulation(action, self.frame_skip)
        xposafter = self.sim.data.qpos[0]
        forward_vel = (xposafter - xposbefore) / self.dt
        forward_reward = self._goal * forward_vel
        ctrl_cost = 0.5 * 0.1 * np.sum(np.square(action))
        observation = self._get_obs()
        reward = forward_reward - ctrl_cost
        done = False
        infos = dict(reward_forward=forward_reward, reward_ctrl=-ctrl_cost)
        return (observation, reward, done, infos)

    def get_current_task(self):
        return np.array([self._goal])

    def _sample_raw_task(self):
        direction = np.random.choice([-1.0, 1.0])
        task = {'goal': direction}
        return task

    def reset_task(self, task_info):
        assert task_info is None
        self._goal = self._sample_raw_task()['goal']
        self.reset()

def __init__(self, n_tasks=None, max_episode_steps=200):
    self.n_tasks = n_tasks
    assert n_tasks == None
    self._goal = self._sample_raw_task()['goal']
    self._max_episode_steps = max_episode_steps
    super(HalfCheetahDirEnv, self).__init__()

def reset_task(self, task_info):
    assert task_info is None
    self._goal = self._sample_raw_task()['goal']
    self.reset()

class HumanoidDirEnv(HumanoidEnv):

    def __init__(self, n_tasks=None, max_episode_steps=200):
        self.n_tasks = n_tasks
        assert n_tasks == None
        self._goal = self._sample_raw_task()['goal']
        self._max_episode_steps = max_episode_steps
        super(HumanoidDirEnv, self).__init__()

    def step(self, action):
        pos_before = np.copy(mass_center(self.model, self.sim)[:2])
        self.do_simulation(action, self.frame_skip)
        pos_after = mass_center(self.model, self.sim)[:2]
        alive_bonus = 5.0
        data = self.sim.data
        goal_direction = (np.cos(self._goal), np.sin(self._goal))
        lin_vel_cost = 0.25 * np.sum(goal_direction * (pos_after - pos_before)) / self.model.opt.timestep
        quad_ctrl_cost = 0.1 * np.square(data.ctrl).sum()
        quad_impact_cost = 5e-07 * np.square(data.cfrc_ext).sum()
        quad_impact_cost = min(quad_impact_cost, 10)
        reward = lin_vel_cost - quad_ctrl_cost - quad_impact_cost + alive_bonus
        qpos = self.sim.data.qpos
        done = bool(qpos[2] < 1.0 or qpos[2] > 2.0)
        return (self._get_obs(), reward, done, dict(reward_linvel=lin_vel_cost, reward_quadctrl=-quad_ctrl_cost, reward_alive=alive_bonus, reward_impact=-quad_impact_cost))

    def _get_obs(self):
        data = self.sim.data
        return np.concatenate([data.qpos.flat[2:], data.qvel.flat, data.cinert.flat, data.cvel.flat, data.qfrc_actuator.flat, data.cfrc_ext.flat])

    def get_current_task(self):
        return np.array([np.cos(self._goal), np.sin(self._goal)])

    def _sample_raw_task(self):
        direction = np.random.uniform(0.0, 2.0 * np.pi)
        task = {'goal': direction}
        return task

    def reset_task(self, task_info):
        assert task_info is None
        self._goal = self._sample_raw_task()['goal']
        self.reset()

def __init__(self, n_tasks=None, max_episode_steps=200):
    self.n_tasks = n_tasks
    assert n_tasks == None
    self._goal = self._sample_raw_task()['goal']
    self._max_episode_steps = max_episode_steps
    super(HumanoidDirEnv, self).__init__()

def _sample_raw_task(self):
    direction = np.random.uniform(0.0, 2.0 * np.pi)
    task = {'goal': direction}
    return task

def reset_task(self, task_info):
    assert task_info is None
    self._goal = self._sample_raw_task()['goal']
    self.reset()

class AntDirEnv(MultitaskAntEnv):
    """
    AntDir: forward_backward=True (unlimited tasks) from on-policy varibad code
    AntDir2D: forward_backward=False (limited tasks) from off-policy varibad code
    """

    def __init__(self, task={}, n_tasks=None, max_episode_steps=200, forward_backward=True, **kwargs):
        self.forward_backward = forward_backward
        self._max_episode_steps = max_episode_steps
        super(AntDirEnv, self).__init__(task, n_tasks, **kwargs)

    def step(self, action):
        torso_xyz_before = np.array(self.get_body_com('torso'))
        direct = (np.cos(self._goal), np.sin(self._goal))
        self.do_simulation(action, self.frame_skip)
        torso_xyz_after = np.array(self.get_body_com('torso'))
        torso_velocity = torso_xyz_after - torso_xyz_before
        forward_reward = np.dot(torso_velocity[:2] / self.dt, direct)
        ctrl_cost = 0.5 * np.square(action).sum()
        contact_cost = 0.5 * 0.001 * np.sum(np.square(np.clip(self.sim.data.cfrc_ext, -1, 1)))
        survive_reward = 1.0
        reward = forward_reward - ctrl_cost - contact_cost + survive_reward
        state = self.state_vector()
        notdone = np.isfinite(state).all() and state[2] >= 0.2 and (state[2] <= 1.0)
        done = not notdone
        ob = self._get_obs()
        return (ob, reward, done, dict(reward_forward=forward_reward, reward_ctrl=-ctrl_cost, reward_contact=-contact_cost, reward_survive=survive_reward, torso_velocity=torso_velocity))

    def sample_tasks(self, num_tasks: int):
        assert self.forward_backward == False
        velocities = np.random.uniform(0.0, 2.0 * np.pi, size=(num_tasks,))
        tasks = [{'goal': velocity} for velocity in velocities]
        return tasks

    def _sample_raw_task(self):
        assert self.forward_backward == True
        velocity = np.random.choice([-1.0, 1.0])
        task = {'goal': velocity}
        return task

def __init__(self, task={}, n_tasks=None, max_episode_steps=200, forward_backward=True, **kwargs):
    self.forward_backward = forward_backward
    self._max_episode_steps = max_episode_steps
    super(AntDirEnv, self).__init__(task, n_tasks, **kwargs)

def sample_tasks(self, num_tasks: int):
    assert self.forward_backward == False
    velocities = np.random.uniform(0.0, 2.0 * np.pi, size=(num_tasks,))
    tasks = [{'goal': velocity} for velocity in velocities]
    return tasks

class MultitaskAntEnv(AntEnv):

    def __init__(self, task={}, n_tasks=2, **kwargs):
        self._task = task
        self.n_tasks = n_tasks
        if n_tasks is None:
            self._goal = self._sample_raw_task()['goal']
        else:
            self.tasks = self.sample_tasks(n_tasks)
            self._goal = self.tasks[0]['goal']
        super(MultitaskAntEnv, self).__init__()

    def get_current_task(self):
        return np.array([self._goal])

    def get_all_task_idx(self):
        return range(len(self.tasks))

    def reset_task(self, task_info):
        if self.n_tasks is None:
            assert task_info is None
            self._task = self._sample_raw_task()
        else:
            self._task = self.tasks[task_info]
        self._goal = self._task['goal']
        self.reset()

def __init__(self, task={}, n_tasks=2, **kwargs):
    self._task = task
    self.n_tasks = n_tasks
    if n_tasks is None:
        self._goal = self._sample_raw_task()['goal']
    else:
        self.tasks = self.sample_tasks(n_tasks)
        self._goal = self.tasks[0]['goal']
    super(MultitaskAntEnv, self).__init__()

def reset_task(self, task_info):
    if self.n_tasks is None:
        assert task_info is None
        self._task = self._sample_raw_task()
    else:
        self._task = self.tasks[task_info]
    self._goal = self._task['goal']
    self.reset()

class AntGoalEnv(MultitaskAntEnv):

    def __init__(self, task={}, n_tasks=2, max_episode_steps=200, **kwargs):
        super(AntGoalEnv, self).__init__(task, n_tasks, **kwargs)
        self._max_episode_steps = max_episode_steps

    def step(self, action):
        self.do_simulation(action, self.frame_skip)
        xposafter = np.array(self.get_body_com('torso'))
        goal_reward = -np.sum(np.abs(xposafter[:2] - self._goal))
        ctrl_cost = 0.1 * np.square(action).sum()
        contact_cost = 0.5 * 0.001 * np.sum(np.square(np.clip(self.sim.data.cfrc_ext, -1, 1)))
        survive_reward = 0.0
        reward = goal_reward - ctrl_cost - contact_cost + survive_reward
        state = self.state_vector()
        done = False
        ob = self._get_obs()
        return (ob, reward, done, dict(goal_forward=goal_reward, reward_ctrl=-ctrl_cost, reward_contact=-contact_cost, reward_survive=survive_reward))

    def sample_tasks(self, num_tasks):
        a = np.random.random(num_tasks) * 2 * np.pi
        r = 3 * np.random.random(num_tasks) ** 0.5
        goals = np.stack((r * np.cos(a), r * np.sin(a)), axis=-1)
        tasks = [{'goal': goal} for goal in goals]
        return tasks

    def _get_obs(self):
        return np.concatenate([self.sim.data.qpos.flat, self.sim.data.qvel.flat, np.clip(self.sim.data.cfrc_ext, -1, 1).flat])

def __init__(self, task={}, n_tasks=2, max_episode_steps=200, **kwargs):
    super(AntGoalEnv, self).__init__(task, n_tasks, **kwargs)
    self._max_episode_steps = max_episode_steps

class SparsePointEnv(PointEnv):
    """
    - tasks sampled from unit half-circle
    - reward is L2 distance given only within goal radius
    NOTE that `step()` returns the dense reward because this is used during meta-training
    the algorithm should call `sparsify_rewards()` to get the sparse rewards
    """

    def __init__(self, max_episode_steps=60, n_tasks=2, goal_radius=0.2, modify_init_state_dist=True, on_circle_init_state=True, **kwargs):
        super().__init__(max_episode_steps, n_tasks)
        self.goal_radius = goal_radius
        self.modify_init_state_dist = modify_init_state_dist
        self.on_circle_init_state = on_circle_init_state
        radius = 1.0
        angles = np.random.uniform(0, np.pi, size=n_tasks)
        xs = radius * np.cos(angles)
        ys = radius * np.sin(angles)
        goals = np.stack([xs, ys], axis=1)
        np.random.shuffle(goals)
        goals = goals.tolist()
        self.goals = goals
        self.reset_task(0)

    def sparsify_rewards(self, r):
        """zero out rewards when outside the goal radius"""
        mask = (r >= -self.goal_radius).astype(np.float32)
        r = r * mask
        return r

    def reset_model(self):
        self.step_count = 0
        if self.modify_init_state_dist:
            self._state = np.array([np.random.uniform(-1.5, 1.5), np.random.uniform(-0.5, 1.5)])
            if not self.on_circle_init_state:
                while 1 - self.goal_radius <= np.linalg.norm(self._state) <= 1 + self.goal_radius:
                    self._state = np.array([np.random.uniform(-1.5, 1.5), np.random.uniform(-0.5, 1.5)])
        else:
            self._state = np.array([0, 0])
        return self._get_obs()

    def step(self, action):
        ob, reward, done, d = super().step(action)
        sparse_reward = self.sparsify_rewards(reward)
        if reward >= -self.goal_radius:
            sparse_reward = 1
        d.update({'sparse_reward': sparse_reward})
        return (ob, sparse_reward, done, d)

    def reward(self, state, action=None):
        return self.sparsify_rewards(super().reward(state, action))

    def is_goal_state(self):
        if np.linalg.norm(self._state - self._goal) <= self.goal_radius:
            return True
        else:
            return False

    def plot_env(self):
        ax = plt.gca()
        angles = np.linspace(0, np.pi, num=100)
        x, y = (np.cos(angles), np.sin(angles))
        plt.plot(x, y, color='k')
        plt.axis('scaled')
        ax.set_xlim(-2, 2)
        ax.set_ylim(-1, 2)
        plt.xticks([])
        plt.yticks([])
        circle = plt.Circle((self._goal[0], self._goal[1]), radius=self.goal_radius, alpha=0.3)
        ax.add_artist(circle)

    def plot_behavior(self, observations, plot_env=True, **kwargs):
        if plot_env:
            self.plot_env()
        plt.scatter(observations[[0], 0], observations[[0], 1], marker='x', **kwargs)
        plt.plot(observations[:, 0], observations[:, 1], **kwargs)

def step(self, action):
    ob, reward, done, d = super().step(action)
    sparse_reward = self.sparsify_rewards(reward)
    if reward >= -self.goal_radius:
        sparse_reward = 1
    d.update({'sparse_reward': sparse_reward})
    return (ob, sparse_reward, done, d)

class HuberLoss(nn.Module):

    def __init__(self, delta=1):
        super().__init__()
        self.huber_loss_delta1 = nn.SmoothL1Loss()
        self.delta = delta

    def forward(self, x, x_hat):
        loss = self.huber_loss_delta1(x / self.delta, x_hat / self.delta)
        return loss * self.delta * self.delta

def __init__(self, delta=1):
    super().__init__()
    self.huber_loss_delta1 = nn.SmoothL1Loss()
    self.delta = delta

