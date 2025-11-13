# Cluster 6

def read_stats(indir, outdir, task, method, budget=int(1000000.0), verbose=False):
    indir = pathlib.Path(indir)
    outdir = pathlib.Path(outdir)
    runs = []
    print(f'Loading {indir.name}...')
    filenames = sorted(list(indir.glob('**/stats.jsonl')))
    for index, filename in enumerate(filenames):
        if not filename.is_file():
            continue
        rewards, lengths, achievements = load_stats(filename, budget)
        if sum(lengths) < budget - 10000.0:
            message = f'Skipping incomplete run ({sum(lengths)} < {budget} steps): '
            message += f'{filename.relative_to(indir.parent)}'
            print(f'==> {message}')
            continue
        runs.append(dict(task=task, method=method, seed=str(index), xs=np.cumsum(lengths).tolist(), reward=rewards, length=lengths, **achievements))
    if not runs:
        print('No completed runs.\n')
        return
    print_summary(runs, budget, verbose)
    outdir.mkdir(exist_ok=True, parents=True)
    filename = outdir / f'{task}-{method}.json'
    filename.write_text(json.dumps(runs))
    print('Wrote', filename)
    print('')

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

def _update_time(self):
    progress = self._step / 300 % 1 + 0.3
    daylight = 1 - np.abs(np.cos(np.pi * progress)) ** 3
    self._world.daylight = daylight

class Object:

    def __init__(self, world, pos):
        self.world = world
        self.pos = np.array(pos)
        self.random = world.random
        self.inventory = {'health': 0}
        self.removed = False

    @property
    def texture(self):
        raise 'unknown'

    @property
    def walkable(self):
        return constants.walkable

    @property
    def health(self):
        return self.inventory['health']

    @health.setter
    def health(self, value):
        self.inventory['health'] = max(0, value)

    @property
    def all_dirs(self):
        return ((-1, 0), (+1, 0), (0, -1), (0, +1))

    def move(self, direction):
        direction = np.array(direction)
        target = self.pos + direction
        if self.is_free(target):
            self.world.move(self, target)
            return True
        return False

    def is_free(self, target, materials=None):
        materials = self.walkable if materials is None else materials
        material, obj = self.world[target]
        return obj is None and material in materials

    def distance(self, target):
        if hasattr(target, 'pos'):
            target = target.pos
        return np.abs(target - self.pos).sum()

    def toward(self, target, long_axis=True):
        if hasattr(target, 'pos'):
            target = target.pos
        offset = target - self.pos
        dists = np.abs(offset)
        if dists[0] > dists[1] if long_axis else dists[0] <= dists[1]:
            return np.array((np.sign(offset[0]), 0))
        else:
            return np.array((0, np.sign(offset[1])))

    def random_dir(self):
        return self.all_dirs[self.random.randint(0, 4)]

def distance(self, target):
    if hasattr(target, 'pos'):
        target = target.pos
    return np.abs(target - self.pos).sum()

def toward(self, target, long_axis=True):
    if hasattr(target, 'pos'):
        target = target.pos
    offset = target - self.pos
    dists = np.abs(offset)
    if dists[0] > dists[1] if long_axis else dists[0] <= dists[1]:
        return np.array((np.sign(offset[0]), 0))
    else:
        return np.array((0, np.sign(offset[1])))

class StatsRecorder:

    def __init__(self, env, directory):
        self._env = env
        self._directory = pathlib.Path(directory).expanduser()
        self._directory.mkdir(exist_ok=True, parents=True)
        self._file = (self._directory / 'stats.jsonl').open('a')
        self._length = None
        self._reward = None
        self._unlocked = None
        self._stats = None

    def __getattr__(self, name):
        if name.startswith('__'):
            raise AttributeError(name)
        return getattr(self._env, name)

    def reset(self):
        obs = self._env.reset()
        self._length = 0
        self._reward = 0
        self._unlocked = None
        self._stats = None
        return obs

    def step(self, action):
        obs, reward, done, info = self._env.step(action)
        self._length += 1
        self._reward += info['reward']
        if done:
            self._stats = {'length': self._length, 'reward': round(self._reward, 1)}
            for key, value in info['achievements'].items():
                self._stats[f'achievement_{key}'] = value
            self._save()
        return (obs, reward, done, info)

    def _save(self):
        self._file.write(json.dumps(self._stats) + '\n')
        self._file.flush()

def __init__(self, env, directory):
    self._env = env
    self._directory = pathlib.Path(directory).expanduser()
    self._directory.mkdir(exist_ok=True, parents=True)
    self._file = (self._directory / 'stats.jsonl').open('a')
    self._length = None
    self._reward = None
    self._unlocked = None
    self._stats = None

def _save(self):
    self._file.write(json.dumps(self._stats) + '\n')
    self._file.flush()

class VideoRecorder:

    def __init__(self, env, directory, size=(512, 512)):
        if not hasattr(env, 'episode_name'):
            env = EpisodeName(env)
        self._env = env
        self._directory = pathlib.Path(directory).expanduser()
        self._directory.mkdir(exist_ok=True, parents=True)
        self._size = size
        self._frames = None

    def __getattr__(self, name):
        if name.startswith('__'):
            raise AttributeError(name)
        return getattr(self._env, name)

    def reset(self):
        obs = self._env.reset()
        self._frames = [self._env.render(self._size)]
        return obs

    def step(self, action):
        obs, reward, done, info = self._env.step(action)
        self._frames.append(self._env.render(self._size))
        if done:
            self._save()
        return (obs, reward, done, info)

    def _save(self):
        filename = str(self._directory / (self._env.episode_name + '.mp4'))
        imageio.mimsave(filename, self._frames)

def __init__(self, env, directory, size=(512, 512)):
    if not hasattr(env, 'episode_name'):
        env = EpisodeName(env)
    self._env = env
    self._directory = pathlib.Path(directory).expanduser()
    self._directory.mkdir(exist_ok=True, parents=True)
    self._size = size
    self._frames = None

class EpisodeRecorder:

    def __init__(self, env, directory):
        if not hasattr(env, 'episode_name'):
            env = EpisodeName(env)
        self._env = env
        self._directory = pathlib.Path(directory).expanduser()
        self._directory.mkdir(exist_ok=True, parents=True)
        self._episode = None

    def __getattr__(self, name):
        if name.startswith('__'):
            raise AttributeError(name)
        return getattr(self._env, name)

    def reset(self):
        obs = self._env.reset()
        self._episode = [{'image': obs}]
        return obs

    def step(self, action):
        obs, reward, done, info = self._env.step(action)
        transition = {'action': action, 'image': obs, 'reward': reward, 'done': done}
        for key, value in info.items():
            if key in ('inventory', 'achievements'):
                continue
            transition[key] = value
        for key, value in info['achievements'].items():
            transition[f'achievement_{key}'] = value
        for key, value in info['inventory'].items():
            transition[f'ainventory_{key}'] = value
        self._episode.append(transition)
        if done:
            self._save()
        return (obs, reward, done, info)

    def _save(self):
        filename = str(self._directory / (self._env.episode_name + '.npz'))
        for key, value in self._episode[1].items():
            if key not in self._episode[0]:
                self._episode[0][key] = np.zeros_like(value)
        episode = {k: np.array([step[k] for step in self._episode]) for k in self._episode[0]}
        np.savez_compressed(filename, **episode)

def __init__(self, env, directory):
    if not hasattr(env, 'episode_name'):
        env = EpisodeName(env)
    self._env = env
    self._directory = pathlib.Path(directory).expanduser()
    self._directory.mkdir(exist_ok=True, parents=True)
    self._episode = None

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

def nearby(self, pos, distance):
    (x, y), d = (pos, distance)
    ids = set(self._mat_map[x - d:x + d + 1, y - d:y + d + 1].flatten().tolist())
    materials = tuple((self._mat_names[x] for x in ids))
    indices = self._obj_map[x - d:x + d + 1, y - d:y + d + 1].flatten().tolist()
    objs = {self._objects[i] for i in indices if i > 0}
    return (materials, objs)

class Textures:

    def __init__(self, directory):
        self._originals = {}
        self._textures = {}
        for filename in pathlib.Path(directory).glob('*.png'):
            image = imageio.imread(filename.read_bytes())
            image = image.transpose((1, 0) + tuple(range(2, len(image.shape))))
            self._originals[filename.stem] = image
            self._textures[filename.stem, image.shape[:2]] = image

    def get(self, name, size):
        if name is None:
            name = 'unknown'
        size = (int(size[0]), int(size[1]))
        key = (name, size)
        if key not in self._textures:
            image = self._originals[name]
            image = Image.fromarray(image)
            image = image.resize(size[::-1], resample=Image.NEAREST)
            image = np.array(image)
            self._textures[key] = image
        return self._textures[key]

def __init__(self, directory):
    self._originals = {}
    self._textures = {}
    for filename in pathlib.Path(directory).glob('*.png'):
        image = imageio.imread(filename.read_bytes())
        image = image.transpose((1, 0) + tuple(range(2, len(image.shape))))
        self._originals[filename.stem] = image
        self._textures[filename.stem, image.shape[:2]] = image

