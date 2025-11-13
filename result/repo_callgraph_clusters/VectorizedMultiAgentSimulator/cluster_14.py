# Cluster 14

class Action(TorchVectorizedObject):

    def __init__(self, u_range: Union[float, Sequence[float]], u_multiplier: Union[float, Sequence[float]], u_noise: Union[float, Sequence[float]], action_size: int):
        super().__init__()
        self._u_noise = u_noise
        self._u_range = u_range
        self._u_multiplier = u_multiplier
        self.action_size = action_size
        self._u = None
        self._c = None
        self._u_range_tensor = None
        self._u_multiplier_tensor = None
        self._u_noise_tensor = None
        self._check_action_init()

    def _check_action_init(self):
        for attr in (self.u_multiplier, self.u_range, self.u_noise):
            if isinstance(attr, List):
                assert len(attr) == self.action_size, 'Action attributes u_... must be either a float or a list of floats (one per action) all with same length'

    @property
    def u(self):
        return self._u

    @u.setter
    def u(self, u: Tensor):
        assert self._batch_dim is not None and self._device is not None, 'First add an agent to the world before setting its action'
        assert u.shape[0] == self._batch_dim, f'Action must match batch dim, got {u.shape[0]}, expected {self._batch_dim}'
        self._u = u.to(self._device)

    @property
    def c(self):
        return self._c

    @c.setter
    def c(self, c: Tensor):
        assert self._batch_dim is not None and self._device is not None, 'First add an agent to the world before setting its action'
        assert c.shape[0] == self._batch_dim, f'Action must match batch dim, got {c.shape[0]}, expected {self._batch_dim}'
        self._c = c.to(self._device)

    @property
    def u_range(self):
        return self._u_range

    @property
    def u_multiplier(self):
        return self._u_multiplier

    @property
    def u_noise(self):
        return self._u_noise

    @property
    def u_range_tensor(self):
        if self._u_range_tensor is None:
            self._u_range_tensor = self._to_tensor(self.u_range)
        return self._u_range_tensor

    @property
    def u_multiplier_tensor(self):
        if self._u_multiplier_tensor is None:
            self._u_multiplier_tensor = self._to_tensor(self.u_multiplier)
        return self._u_multiplier_tensor

    @property
    def u_noise_tensor(self):
        if self._u_noise_tensor is None:
            self._u_noise_tensor = self._to_tensor(self.u_noise)
        return self._u_noise_tensor

    def _to_tensor(self, value):
        return torch.tensor(value if isinstance(value, Sequence) else [value] * self.action_size, device=self.device, dtype=torch.float)

    def _reset(self, env_index: typing.Optional[int]):
        for attr_name in ['u', 'c']:
            attr = self.__getattribute__(attr_name)
            if attr is not None:
                if env_index is None:
                    self.__setattr__(attr_name, torch.zeros_like(attr))
                else:
                    self.__setattr__(attr_name, TorchUtils.where_from_index(env_index, 0, attr))

    def zero_grad(self):
        for attr_name in ['u', 'c']:
            attr = self.__getattribute__(attr_name)
            if attr is not None:
                self.__setattr__(attr_name, attr.detach())

@property
def u_range_tensor(self):
    if self._u_range_tensor is None:
        self._u_range_tensor = self._to_tensor(self.u_range)
    return self._u_range_tensor

@property
def u_multiplier_tensor(self):
    if self._u_multiplier_tensor is None:
        self._u_multiplier_tensor = self._to_tensor(self.u_multiplier)
    return self._u_multiplier_tensor

@property
def u_noise_tensor(self):
    if self._u_noise_tensor is None:
        self._u_noise_tensor = self._to_tensor(self.u_noise)
    return self._u_noise_tensor

