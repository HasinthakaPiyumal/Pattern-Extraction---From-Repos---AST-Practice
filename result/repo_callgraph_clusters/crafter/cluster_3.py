# Cluster 3

class Env(BaseClass):

    def __init__(self, area=(64, 64), view=(9, 9), size=(64, 64), reward=True, length=10000, seed=None):
        view = np.array(view if hasattr(view, '__len__') else (view, view))
        size = np.array(size if hasattr(size, '__len__') else (size, size))
        seed = np.random.randint(0, 2 ** 31 - 1) if seed is None else seed
        self._area = area
        self._view = view
        self._size = size
        self._reward = reward
        self._length = length
        self._seed = seed
        self._episode = 0
        self._world = engine.World(area, constants.materials, (12, 12))
        self._textures = engine.Textures(constants.root / 'assets')
        item_rows = int(np.ceil(len(constants.items) / view[0]))
        self._local_view = engine.LocalView(self._world, self._textures, [view[0], view[1] - item_rows])
        self._item_view = engine.ItemView(self._textures, [view[0], item_rows])
        self._sem_view = engine.SemanticView(self._world, [objects.Player, objects.Cow, objects.Zombie, objects.Skeleton, objects.Arrow, objects.Plant])
        self._step = None
        self._player = None
        self._last_health = None
        self._unlocked = None
        self.reward_range = None
        self.metadata = None

    @property
    def observation_space(self):
        return BoxSpace(0, 255, tuple(self._size) + (3,), np.uint8)

    @property
    def action_space(self):
        return DiscreteSpace(len(constants.actions))

    @property
    def action_names(self):
        return constants.actions

    def reset(self):
        center = (self._world.area[0] // 2, self._world.area[1] // 2)
        self._episode += 1
        self._step = 0
        self._world.reset(seed=hash((self._seed, self._episode)) % (2 ** 31 - 1))
        self._update_time()
        self._player = objects.Player(self._world, center)
        self._last_health = self._player.health
        self._world.add(self._player)
        self._unlocked = set()
        worldgen.generate_world(self._world, self._player)
        return self._obs()

    def step(self, action):
        self._step += 1
        self._update_time()
        self._player.action = constants.actions[action]
        for obj in self._world.objects:
            if self._player.distance(obj) < 2 * max(self._view):
                obj.update()
        if self._step % 10 == 0:
            for chunk, objs in self._world.chunks.items():
                self._balance_chunk(chunk, objs)
        obs = self._obs()
        reward = (self._player.health - self._last_health) / 10
        self._last_health = self._player.health
        unlocked = {name for name, count in self._player.achievements.items() if count > 0 and name not in self._unlocked}
        if unlocked:
            self._unlocked |= unlocked
            reward += 1.0
        dead = self._player.health <= 0
        over = self._length and self._step >= self._length
        done = dead or over
        info = {'inventory': self._player.inventory.copy(), 'achievements': self._player.achievements.copy(), 'discount': 1 - float(dead), 'semantic': self._sem_view(), 'player_pos': self._player.pos, 'reward': reward}
        if not self._reward:
            reward = 0.0
        return (obs, reward, done, info)

    def render(self, size=None):
        size = size or self._size
        unit = size // self._view
        canvas = np.zeros(tuple(size) + (3,), np.uint8)
        local_view = self._local_view(self._player, unit)
        item_view = self._item_view(self._player.inventory, unit)
        view = np.concatenate([local_view, item_view], 1)
        border = (size - size // self._view * self._view) // 2
        (x, y), (w, h) = (border, view.shape[:2])
        canvas[x:x + w, y:y + h] = view
        return canvas.transpose((1, 0, 2))

    def _obs(self):
        return self.render()

    def _update_time(self):
        progress = self._step / 300 % 1 + 0.3
        daylight = 1 - np.abs(np.cos(np.pi * progress)) ** 3
        self._world.daylight = daylight

    def _balance_chunk(self, chunk, objs):
        light = self._world.daylight
        self._balance_object(chunk, objs, objects.Zombie, 'grass', 6, 0, 0.3, 0.4, lambda pos: objects.Zombie(self._world, pos, self._player), lambda num, space: (0 if space < 50 else 3.5 - 3 * light, 3.5 - 3 * light))
        self._balance_object(chunk, objs, objects.Skeleton, 'path', 7, 7, 0.1, 0.1, lambda pos: objects.Skeleton(self._world, pos, self._player), lambda num, space: (0 if space < 6 else 1, 2))
        self._balance_object(chunk, objs, objects.Cow, 'grass', 5, 5, 0.01, 0.1, lambda pos: objects.Cow(self._world, pos), lambda num, space: (0 if space < 30 else 1, 1.5 + light))

    def _balance_object(self, chunk, objs, cls, material, span_dist, despan_dist, spawn_prob, despawn_prob, ctor, target_fn):
        xmin, xmax, ymin, ymax = chunk
        random = self._world.random
        creatures = [obj for obj in objs if isinstance(obj, cls)]
        mask = self._world.mask(*chunk, material)
        target_min, target_max = target_fn(len(creatures), mask.sum())
        if len(creatures) < int(target_min) and random.uniform() < spawn_prob:
            xs = np.tile(np.arange(xmin, xmax)[:, None], [1, ymax - ymin])
            ys = np.tile(np.arange(ymin, ymax)[None, :], [xmax - xmin, 1])
            xs, ys = (xs[mask], ys[mask])
            i = random.randint(0, len(xs))
            pos = np.array((xs[i], ys[i]))
            empty = self._world[pos][1] is None
            away = self._player.distance(pos) >= span_dist
            if empty and away:
                self._world.add(ctor(pos))
        elif len(creatures) > int(target_max) and random.uniform() < despawn_prob:
            obj = creatures[random.randint(0, len(creatures))]
            away = self._player.distance(obj.pos) >= despan_dist
            if away:
                self._world.remove(obj)

def reset(self):
    center = (self._world.area[0] // 2, self._world.area[1] // 2)
    self._episode += 1
    self._step = 0
    self._world.reset(seed=hash((self._seed, self._episode)) % (2 ** 31 - 1))
    self._update_time()
    self._player = objects.Player(self._world, center)
    self._last_health = self._player.health
    self._world.add(self._player)
    self._unlocked = set()
    worldgen.generate_world(self._world, self._player)
    return self._obs()

def step(self, action):
    self._step += 1
    self._update_time()
    self._player.action = constants.actions[action]
    for obj in self._world.objects:
        if self._player.distance(obj) < 2 * max(self._view):
            obj.update()
    if self._step % 10 == 0:
        for chunk, objs in self._world.chunks.items():
            self._balance_chunk(chunk, objs)
    obs = self._obs()
    reward = (self._player.health - self._last_health) / 10
    self._last_health = self._player.health
    unlocked = {name for name, count in self._player.achievements.items() if count > 0 and name not in self._unlocked}
    if unlocked:
        self._unlocked |= unlocked
        reward += 1.0
    dead = self._player.health <= 0
    over = self._length and self._step >= self._length
    done = dead or over
    info = {'inventory': self._player.inventory.copy(), 'achievements': self._player.achievements.copy(), 'discount': 1 - float(dead), 'semantic': self._sem_view(), 'player_pos': self._player.pos, 'reward': reward}
    if not self._reward:
        reward = 0.0
    return (obs, reward, done, info)

class World:

    def __init__(self, area, materials, chunk_size):
        self.area = area
        self._chunk_size = chunk_size
        self._mat_names = {i: x for i, x in enumerate([None] + materials)}
        self._mat_ids = {x: i for i, x in enumerate([None] + materials)}
        self.reset()

    def reset(self, seed=None):
        self.random = np.random.RandomState(seed)
        self.daylight = 0.0
        self._chunks = collections.defaultdict(set)
        self._objects = [None]
        self._mat_map = np.zeros(self.area, np.uint8)
        self._obj_map = np.zeros(self.area, np.uint32)

    @property
    def objects(self):
        return [obj for obj in self._objects if obj]

    @property
    def chunks(self):
        return self._chunks.copy()

    def add(self, obj):
        assert hasattr(obj, 'pos')
        obj.pos = np.array(obj.pos)
        assert self._obj_map[tuple(obj.pos)] == 0
        index = len(self._objects)
        self._objects.append(obj)
        self._obj_map[tuple(obj.pos)] = index
        self._chunks[self.chunk_key(obj.pos)].add(obj)

    def remove(self, obj):
        if obj.removed:
            return
        self._objects[self._obj_map[tuple(obj.pos)]] = None
        self._obj_map[tuple(obj.pos)] = 0
        self._chunks[self.chunk_key(obj.pos)].remove(obj)
        obj.removed = True

    def move(self, obj, pos):
        if obj.removed:
            return
        pos = np.array(pos)
        assert self._obj_map[tuple(pos)] == 0
        index = self._obj_map[tuple(obj.pos)]
        self._obj_map[tuple(pos)] = index
        self._obj_map[tuple(obj.pos)] = 0
        old_chunk = self.chunk_key(obj.pos)
        new_chunk = self.chunk_key(pos)
        if old_chunk != new_chunk:
            self._chunks[old_chunk].remove(obj)
            self._chunks[new_chunk].add(obj)
        obj.pos = pos

    def __setitem__(self, pos, material):
        if material not in self._mat_ids:
            id_ = len(self._mat_ids)
            self._mat_ids[material] = id_
        self._mat_map[tuple(pos)] = self._mat_ids[material]

    def __getitem__(self, pos):
        if not _inside((0, 0), pos, self.area):
            return (None, None)
        material = self._mat_names[self._mat_map[tuple(pos)]]
        obj = self._objects[self._obj_map[tuple(pos)]]
        return (material, obj)

    def nearby(self, pos, distance):
        (x, y), d = (pos, distance)
        ids = set(self._mat_map[x - d:x + d + 1, y - d:y + d + 1].flatten().tolist())
        materials = tuple((self._mat_names[x] for x in ids))
        indices = self._obj_map[x - d:x + d + 1, y - d:y + d + 1].flatten().tolist()
        objs = {self._objects[i] for i in indices if i > 0}
        return (materials, objs)

    def mask(self, xmin, xmax, ymin, ymax, material):
        region = self._mat_map[xmin:xmax, ymin:ymax]
        return region == self._mat_ids[material]

    def count(self, material):
        return (self._mat_map == self._mat_ids[material]).sum()

    def chunk_key(self, pos):
        (x, y), (csx, csy) = (pos, self._chunk_size)
        xmin, ymin = (x // csx * csx, y // csy * csy)
        xmax = min(xmin + csx, self.area[0])
        ymax = min(ymin + csy, self.area[1])
        return (xmin, xmax, ymin, ymax)

def __init__(self, area, materials, chunk_size):
    self.area = area
    self._chunk_size = chunk_size
    self._mat_names = {i: x for i, x in enumerate([None] + materials)}
    self._mat_ids = {x: i for i, x in enumerate([None] + materials)}
    self.reset()

@property
def chunks(self):
    return self._chunks.copy()

class SemanticView:

    def __init__(self, world, obj_types):
        self._world = world
        self._mat_ids = world._mat_ids.copy()
        self._obj_ids = {c: len(self._mat_ids) + i for i, c in enumerate(obj_types)}

    def __call__(self):
        canvas = self._world._mat_map.copy()
        for obj in self._world.objects:
            canvas[tuple(obj.pos)] = self._obj_ids[type(obj)]
        return canvas

def __init__(self, world, obj_types):
    self._world = world
    self._mat_ids = world._mat_ids.copy()
    self._obj_ids = {c: len(self._mat_ids) + i for i, c in enumerate(obj_types)}

def __call__(self):
    canvas = self._world._mat_map.copy()
    for obj in self._world.objects:
        canvas[tuple(obj.pos)] = self._obj_ids[type(obj)]
    return canvas

