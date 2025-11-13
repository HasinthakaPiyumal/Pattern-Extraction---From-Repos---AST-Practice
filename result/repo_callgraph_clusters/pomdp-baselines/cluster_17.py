# Cluster 17

def patch_deprecated_methods(env):
    """
    Methods renamed from '_method' to 'method', render() no longer has 'close' parameter, close is a separate method.
    For backward compatibility, this makes it possible to work with unmodified environments.
    """
    global warn_once
    if warn_once:
        logger.warn("Environment '%s' has deprecated methods '_step' and '_reset' rather than 'step' and 'reset'. Compatibility code invoked. Set _gym_disable_underscore_compat = True to disable this behavior." % str(type(env)))
        warn_once = False
    env.reset = env._reset
    env.step = env._step
    env.seed = env._seed

    def render(mode):
        return env._render(mode, close=False)

    def close():
        env._render('human', close=True)
    env.render = render
    env.close = close

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

def randomize_env(self):
    self.density = self.np_random.uniform(self.RANDOM_LOWER_DENSITY, self.RANDOM_UPPER_DENSITY)
    self.friction = self.np_random.uniform(self.RANDOM_LOWER_FRICTION, self.RANDOM_UPPER_FRICTION)
    self.power = self.np_random.uniform(self.RANDOM_LOWER_POWER, self.RANDOM_UPPER_POWER)
    with self.modify_xml('half_cheetah.xml') as tree:
        for elem in tree.iterfind('worldbody/body/geom'):
            elem.set('density', str(self.density))
        for elem in tree.iterfind('default/geom'):
            elem.set('friction', str(self.friction) + ' .1 .1')

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

def randomize_env(self):
    self.density = self.np_random.uniform(self.RANDOM_LOWER_DENSITY, self.RANDOM_UPPER_DENSITY)
    self.friction = self.np_random.uniform(self.RANDOM_LOWER_FRICTION, self.RANDOM_UPPER_FRICTION)
    self.power = self.np_random.uniform(self.RANDOM_LOWER_POWER, self.RANDOM_UPPER_POWER)
    with self.modify_xml('hopper.xml') as tree:
        for elem in tree.iterfind('worldbody/body/geom'):
            elem.set('density', str(self.density))
        for elem in tree.iterfind('default/geom'):
            elem.set('friction', str(self.friction) + ' .1 .1')

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

def randomize_env(self):
    self.density = self.np_random.uniform(self.RANDOM_LOWER_DENSITY, self.RANDOM_UPPER_DENSITY)
    self.friction = self.np_random.uniform(self.RANDOM_LOWER_FRICTION, self.RANDOM_UPPER_FRICTION)
    with self.modify_xml('walker2d.xml') as tree:
        for elem in tree.iterfind('default/geom'):
            elem.set('density', str(self.density) + ' .1 .1')
        for elem in tree.iterfind('default/geom'):
            elem.set('friction', str(self.friction) + ' .1 .1')

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

def randomize_env(self):
    self.density = self.np_random.uniform(self.RANDOM_LOWER_DENSITY, self.RANDOM_UPPER_DENSITY)
    self.friction = self.np_random.uniform(self.RANDOM_LOWER_FRICTION, self.RANDOM_UPPER_FRICTION)
    with self.modify_xml('half_cheetah.xml') as tree:
        for elem in tree.iterfind('worldbody/body/geom'):
            elem.set('density', str(self.density))
        for elem in tree.iterfind('default/geom'):
            elem.set('friction', str(self.friction) + ' .1 .1')

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

def randomize_env(self):
    self.density = self.np_random.uniform(self.RANDOM_LOWER_DENSITY, self.RANDOM_UPPER_DENSITY)
    self.friction = self.np_random.uniform(self.RANDOM_LOWER_FRICTION, self.RANDOM_UPPER_FRICTION)
    with self.modify_xml('hopper.xml') as tree:
        for elem in tree.iterfind('worldbody/body/geom'):
            elem.set('density', str(self.density))
        for elem in tree.iterfind('default/geom'):
            elem.set('friction', str(self.friction) + ' .1 .1')

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

class Serializable(object):

    def __init__(self, *args, **kwargs):
        self.__args = args
        self.__kwargs = kwargs

    def quick_init(self, locals_):
        if getattr(self, '_serializable_initialized', False):
            return
        if sys.version_info >= (3, 0):
            spec = inspect.getfullargspec(self.__init__)
            if spec.varkw:
                kwargs = locals_[spec.varkw].copy()
            else:
                kwargs = dict()
            if spec.kwonlyargs:
                for key in spec.kwonlyargs:
                    kwargs[key] = locals_[key]
        else:
            spec = inspect.getargspec(self.__init__)
            if spec.keywords:
                kwargs = locals_[spec.keywords]
            else:
                kwargs = dict()
        if spec.varargs:
            varargs = locals_[spec.varargs]
        else:
            varargs = tuple()
        in_order_args = [locals_[arg] for arg in spec.args][1:]
        self.__args = tuple(in_order_args) + varargs
        self.__kwargs = kwargs
        setattr(self, '_serializable_initialized', True)

    def __getstate__(self):
        return {'__args': self.__args, '__kwargs': self.__kwargs}

    def __setstate__(self, d):
        if sys.version_info >= (3, 0):
            spec = inspect.getfullargspec(self.__init__)
        else:
            spec = inspect.getargspec(self.__init__)
        in_order_args = spec.args[1:]
        out = type(self)(**dict(zip(in_order_args, d['__args']), **d['__kwargs']))
        self.__dict__.update(out.__dict__)

    @classmethod
    def clone(cls, obj, **kwargs):
        assert isinstance(obj, Serializable)
        d = obj.__getstate__()
        d['__kwargs'] = dict(d['__kwargs'], **kwargs)
        out = type(obj).__new__(type(obj))
        out.__setstate__(d)
        return out

def quick_init(self, locals_):
    if getattr(self, '_serializable_initialized', False):
        return
    if sys.version_info >= (3, 0):
        spec = inspect.getfullargspec(self.__init__)
        if spec.varkw:
            kwargs = locals_[spec.varkw].copy()
        else:
            kwargs = dict()
        if spec.kwonlyargs:
            for key in spec.kwonlyargs:
                kwargs[key] = locals_[key]
    else:
        spec = inspect.getargspec(self.__init__)
        if spec.keywords:
            kwargs = locals_[spec.keywords]
        else:
            kwargs = dict()
    if spec.varargs:
        varargs = locals_[spec.varargs]
    else:
        varargs = tuple()
    in_order_args = [locals_[arg] for arg in spec.args][1:]
    self.__args = tuple(in_order_args) + varargs
    self.__kwargs = kwargs
    setattr(self, '_serializable_initialized', True)

def __setstate__(self, d):
    if sys.version_info >= (3, 0):
        spec = inspect.getfullargspec(self.__init__)
    else:
        spec = inspect.getargspec(self.__init__)
    in_order_args = spec.args[1:]
    out = type(self)(**dict(zip(in_order_args, d['__args']), **d['__kwargs']))
    self.__dict__.update(out.__dict__)

@classmethod
def clone(cls, obj, **kwargs):
    assert isinstance(obj, Serializable)
    d = obj.__getstate__()
    d['__kwargs'] = dict(d['__kwargs'], **kwargs)
    out = type(obj).__new__(type(obj))
    out.__setstate__(d)
    return out

def conv_output_shape(h_w, kernel_size=1, stride=1, pad=0, dilation=1):
    """
    Utility function for computing output of convolutions
    takes a tuple of (h,w) and returns a tuple of (h,w)
    """
    from math import floor
    if type(kernel_size) is not tuple:
        kernel_size = (kernel_size, kernel_size)
    h = floor((h_w[0] + 2 * pad - dilation * (kernel_size[0] - 1) - 1) / stride + 1)
    w = floor((h_w[1] + 2 * pad - dilation * (kernel_size[1] - 1) - 1) / stride + 1)
    return (h, w)

class PyTorchModule(nn.Module, Serializable, metaclass=abc.ABCMeta):

    def get_param_values(self):
        return self.state_dict()

    def set_param_values(self, param_values):
        self.load_state_dict(param_values)

    def get_param_values_np(self):
        state_dict = self.state_dict()
        np_dict = OrderedDict()
        for key, tensor in state_dict.items():
            np_dict[key] = ptu.get_numpy(tensor)
        return np_dict

    def set_param_values_np(self, param_values):
        torch_dict = OrderedDict()
        for key, tensor in param_values.items():
            torch_dict[key] = ptu.from_numpy(tensor)
        self.load_state_dict(torch_dict)

    def copy(self):
        copy = Serializable.clone(self)
        ptu.copy_model_params_from_to(self, copy)
        return copy

    def save_init_params(self, locals):
        """
        Should call this FIRST THING in the __init__ method if you ever want
        to serialize or clone this network.

        Usage:
        ```
        def __init__(self, ...):
            self.init_serialization(locals())
            ...
        ```
        :param locals:
        :return:
        """
        Serializable.quick_init(self, locals)

    def __getstate__(self):
        d = Serializable.__getstate__(self)
        d['params'] = self.get_param_values()
        return d

    def __setstate__(self, d):
        Serializable.__setstate__(self, d)
        self.set_param_values(d['params'])

    def regularizable_parameters(self):
        """
        Return generator of regularizable parameters. Right now, all non-flat
        vectors are assumed to be regularizabled, presumably because only
        biases are flat.

        :return:
        """
        for param in self.parameters():
            if len(param.size()) > 1:
                yield param

    def eval_np(self, *args, **kwargs):
        """
        Eval this module with a numpy interface

        Same as a call to __call__ except all Variable input/outputs are
        replaced with numpy equivalents.

        Assumes the output is either a single object or a tuple of objects.
        """
        torch_args = tuple((torch_ify(x) for x in args))
        torch_kwargs = {k: torch_ify(v) for k, v in kwargs.items()}
        outputs = self.__call__(*torch_args, **torch_kwargs)
        if isinstance(outputs, tuple):
            return tuple((np_ify(x) for x in outputs))
        else:
            return np_ify(outputs)

def __getstate__(self):
    d = Serializable.__getstate__(self)
    d['params'] = self.get_param_values()
    return d

def __setstate__(self, d):
    Serializable.__setstate__(self, d)
    self.set_param_values(d['params'])

def eval_np(self, *args, **kwargs):
    """
        Eval this module with a numpy interface

        Same as a call to __call__ except all Variable input/outputs are
        replaced with numpy equivalents.

        Assumes the output is either a single object or a tuple of objects.
        """
    torch_args = tuple((torch_ify(x) for x in args))
    torch_kwargs = {k: torch_ify(v) for k, v in kwargs.items()}
    outputs = self.__call__(*torch_args, **torch_kwargs)
    if isinstance(outputs, tuple):
        return tuple((np_ify(x) for x in outputs))
    else:
        return np_ify(outputs)

def elem_or_tuple_to_variable(elem_or_tuple):
    if isinstance(elem_or_tuple, tuple):
        return tuple((elem_or_tuple_to_variable(e) for e in elem_or_tuple))
    return from_numpy(elem_or_tuple)

def np_to_pytorch_batch(np_batch):
    return {k: elem_or_tuple_to_variable(x) for k, x in filter_batch(np_batch) if x.dtype != np.dtype('O')}

class Serializable(object):

    def __init__(self, *args, **kwargs):
        self.__args = args
        self.__kwargs = kwargs

    def quick_init(self, locals_):
        if getattr(self, '_serializable_initialized', False):
            return
        if sys.version_info >= (3, 0):
            spec = inspect.getfullargspec(self.__init__)
            if spec.varkw:
                kwargs = locals_[spec.varkw].copy()
            else:
                kwargs = dict()
            if spec.kwonlyargs:
                for key in spec.kwonlyargs:
                    kwargs[key] = locals_[key]
        else:
            spec = inspect.getargspec(self.__init__)
            if spec.keywords:
                kwargs = locals_[spec.keywords]
            else:
                kwargs = dict()
        if spec.varargs:
            varargs = locals_[spec.varargs]
        else:
            varargs = tuple()
        in_order_args = [locals_[arg] for arg in spec.args][1:]
        self.__args = tuple(in_order_args) + varargs
        self.__kwargs = kwargs
        setattr(self, '_serializable_initialized', True)

    def __getstate__(self):
        return {'__args': self.__args, '__kwargs': self.__kwargs}

    def __setstate__(self, d):
        if sys.version_info >= (3, 0):
            spec = inspect.getfullargspec(self.__init__)
        else:
            spec = inspect.getargspec(self.__init__)
        in_order_args = spec.args[1:]
        out = type(self)(**dict(zip(in_order_args, d['__args']), **d['__kwargs']))
        self.__dict__.update(out.__dict__)

    @classmethod
    def clone(cls, obj, **kwargs):
        assert isinstance(obj, Serializable)
        d = obj.__getstate__()
        d['__kwargs'] = dict(d['__kwargs'], **kwargs)
        out = type(obj).__new__(type(obj))
        out.__setstate__(d)
        return out

def quick_init(self, locals_):
    if getattr(self, '_serializable_initialized', False):
        return
    if sys.version_info >= (3, 0):
        spec = inspect.getfullargspec(self.__init__)
        if spec.varkw:
            kwargs = locals_[spec.varkw].copy()
        else:
            kwargs = dict()
        if spec.kwonlyargs:
            for key in spec.kwonlyargs:
                kwargs[key] = locals_[key]
    else:
        spec = inspect.getargspec(self.__init__)
        if spec.keywords:
            kwargs = locals_[spec.keywords]
        else:
            kwargs = dict()
    if spec.varargs:
        varargs = locals_[spec.varargs]
    else:
        varargs = tuple()
    in_order_args = [locals_[arg] for arg in spec.args][1:]
    self.__args = tuple(in_order_args) + varargs
    self.__kwargs = kwargs
    setattr(self, '_serializable_initialized', True)

def __setstate__(self, d):
    if sys.version_info >= (3, 0):
        spec = inspect.getfullargspec(self.__init__)
    else:
        spec = inspect.getargspec(self.__init__)
    in_order_args = spec.args[1:]
    out = type(self)(**dict(zip(in_order_args, d['__args']), **d['__kwargs']))
    self.__dict__.update(out.__dict__)

@classmethod
def clone(cls, obj, **kwargs):
    assert isinstance(obj, Serializable)
    d = obj.__getstate__()
    d['__kwargs'] = dict(d['__kwargs'], **kwargs)
    out = type(obj).__new__(type(obj))
    out.__setstate__(d)
    return out

