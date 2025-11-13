# Cluster 10

def load_stats(filename, budget):
    steps = 0
    rewards = []
    lengths = []
    achievements = collections.defaultdict(list)
    for line in filename.read_text().split('\n'):
        if not line.strip():
            continue
        episode = json.loads(line)
        steps += episode['length']
        if steps > budget:
            break
        lengths.append(episode['length'])
        for key, value in episode.items():
            if key.startswith('achievement_'):
                achievements[key].append(value)
        unlocks = int(np.sum([v[-1] >= 1 for v in achievements.values()]))
        health = -0.9
        rewards.append(unlocks + health)
    return (rewards, lengths, achievements)

def load_runs(filenames, budget=1000000.0, verbose=True):
    verbose and print('')
    runs = []
    for filename in filenames:
        loaded = json.loads(pathlib.Path(filename).read_text())
        for run in [loaded] if isinstance(loaded, dict) else loaded:
            message = f'Loading {run['method']} seed {run['seed']}'
            verbose and print(message, flush=True)
            if run['xs'][-1] < budget - 10000.0:
                verbose and print(f'  Contains only {run['xs'][-1]} steps!')
            runs.append(run)
    verbose and print('')
    return runs

def _simplex(simplex, x, y, z, sizes, normalize=True):
    if not isinstance(sizes, dict):
        sizes = {sizes: 1}
    value = 0
    for size, weight in sizes.items():
        if hasattr(simplex, 'noise3d'):
            noise = simplex.noise3d(x / size, y / size, z)
        else:
            noise = simplex.noise3(x / size, y / size, z)
        value += weight * noise
    if normalize:
        value /= sum(sizes.values())
    return value

class Player(Object):

    def __init__(self, world, pos):
        super().__init__(world, pos)
        self.facing = (0, 1)
        self.inventory = {name: info['initial'] for name, info in constants.items.items()}
        self.achievements = {name: 0 for name in constants.achievements}
        self.action = 'noop'
        self.sleeping = False
        self._last_health = self.health
        self._hunger = 0
        self._thirst = 0
        self._fatigue = 0
        self._recover = 0

    @property
    def texture(self):
        if self.sleeping:
            return 'player-sleep'
        return {(-1, 0): 'player-left', (+1, 0): 'player-right', (0, -1): 'player-up', (0, +1): 'player-down'}[tuple(self.facing)]

    @property
    def walkable(self):
        return constants.walkable + ['lava']

    def update(self):
        target = (self.pos[0] + self.facing[0], self.pos[1] + self.facing[1])
        material, obj = self.world[target]
        action = self.action
        if self.sleeping:
            if self.inventory['energy'] < constants.items['energy']['max']:
                action = 'sleep'
            else:
                self.sleeping = False
                self.achievements['wake_up'] += 1
        if action == 'noop':
            pass
        elif action.startswith('move_'):
            self._move(action[len('move_'):])
        elif action == 'do' and obj:
            self._do_object(obj)
        elif action == 'do':
            self._do_material(target, material)
        elif action == 'sleep':
            if self.inventory['energy'] < constants.items['energy']['max']:
                self.sleeping = True
        elif action.startswith('place_'):
            self._place(action[len('place_'):], target, material)
        elif action.startswith('make_'):
            self._make(action[len('make_'):])
        self._update_life_stats()
        self._degen_or_regen_health()
        for name, amount in self.inventory.items():
            maxmium = constants.items[name]['max']
            self.inventory[name] = max(0, min(amount, maxmium))
        self._wake_up_when_hurt()

    def _update_life_stats(self):
        self._hunger += 0.5 if self.sleeping else 1
        if self._hunger > 25:
            self._hunger = 0
            self.inventory['food'] -= 1
        self._thirst += 0.5 if self.sleeping else 1
        if self._thirst > 20:
            self._thirst = 0
            self.inventory['drink'] -= 1
        if self.sleeping:
            self._fatigue = min(self._fatigue - 1, 0)
        else:
            self._fatigue += 1
        if self._fatigue < -10:
            self._fatigue = 0
            self.inventory['energy'] += 1
        if self._fatigue > 30:
            self._fatigue = 0
            self.inventory['energy'] -= 1

    def _degen_or_regen_health(self):
        necessities = (self.inventory['food'] > 0, self.inventory['drink'] > 0, self.inventory['energy'] > 0 or self.sleeping)
        if all(necessities):
            self._recover += 2 if self.sleeping else 1
        else:
            self._recover -= 0.5 if self.sleeping else 1
        if self._recover > 25:
            self._recover = 0
            self.health += 1
        if self._recover < -15:
            self._recover = 0
            self.health -= 1

    def _wake_up_when_hurt(self):
        if self.health < self._last_health:
            self.sleeping = False
        self._last_health = self.health

    def _move(self, direction):
        directions = dict(left=(-1, 0), right=(+1, 0), up=(0, -1), down=(0, +1))
        self.facing = directions[direction]
        self.move(self.facing)
        if self.world[self.pos][0] == 'lava':
            self.health = 0

    def _do_object(self, obj):
        damage = max([1, self.inventory['wood_sword'] and 2, self.inventory['stone_sword'] and 3, self.inventory['iron_sword'] and 5])
        if isinstance(obj, Plant):
            if obj.ripe:
                obj.grown = 0
                self.inventory['food'] += 4
                self.achievements['eat_plant'] += 1
        if isinstance(obj, Fence):
            self.world.remove(obj)
            self.inventory['fence'] += 1
            self.achievements['collect_fence'] += 1
        if isinstance(obj, Zombie):
            obj.health -= damage
            if obj.health <= 0:
                self.achievements['defeat_zombie'] += 1
        if isinstance(obj, Skeleton):
            obj.health -= damage
            if obj.health <= 0:
                self.achievements['defeat_skeleton'] += 1
        if isinstance(obj, Cow):
            obj.health -= damage
            if obj.health <= 0:
                self.inventory['food'] += 6
                self.achievements['eat_cow'] += 1
                self._hunger = 0

    def _do_material(self, target, material):
        if material == 'water':
            self._thirst = 0
        info = constants.collect.get(material)
        if not info:
            return
        for name, amount in info['require'].items():
            if self.inventory[name] < amount:
                return
        self.world[target] = info['leaves']
        if self.random.uniform() <= info.get('probability', 1):
            for name, amount in info['receive'].items():
                self.inventory[name] += amount
                self.achievements[f'collect_{name}'] += 1

    def _place(self, name, target, material):
        if self.world[target][1]:
            return
        info = constants.place[name]
        if material not in info['where']:
            return
        if any((self.inventory[k] < v for k, v in info['uses'].items())):
            return
        for item, amount in info['uses'].items():
            self.inventory[item] -= amount
        if info['type'] == 'material':
            self.world[target] = name
        elif info['type'] == 'object':
            cls = {'fence': Fence, 'plant': Plant}[name]
            self.world.add(cls(self.world, target))
        self.achievements[f'place_{name}'] += 1

    def _make(self, name):
        nearby, _ = self.world.nearby(self.pos, 1)
        info = constants.make[name]
        if not all((util in nearby for util in info['nearby'])):
            return
        if any((self.inventory[k] < v for k, v in info['uses'].items())):
            return
        for item, amount in info['uses'].items():
            self.inventory[item] -= amount
        self.inventory[name] += info['gives']
        self.achievements[f'make_{name}'] += 1

def _place(self, name, target, material):
    if self.world[target][1]:
        return
    info = constants.place[name]
    if material not in info['where']:
        return
    if any((self.inventory[k] < v for k, v in info['uses'].items())):
        return
    for item, amount in info['uses'].items():
        self.inventory[item] -= amount
    if info['type'] == 'material':
        self.world[target] = name
    elif info['type'] == 'object':
        cls = {'fence': Fence, 'plant': Plant}[name]
        self.world.add(cls(self.world, target))
    self.achievements[f'place_{name}'] += 1

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

def step(self, action):
    obs, reward, done, info = self._env.step(action)
    self._frames.append(self._env.render(self._size))
    if done:
        self._save()
    return (obs, reward, done, info)

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

class EpisodeName:

    def __init__(self, env):
        self._env = env
        self._timestamp = None
        self._unlocked = None
        self._length = None

    def __getattr__(self, name):
        if name.startswith('__'):
            raise AttributeError(name)
        return getattr(self._env, name)

    def reset(self):
        obs = self._env.reset()
        self._timestamp = None
        self._unlocked = None
        self._length = 0
        return obs

    def step(self, action):
        obs, reward, done, info = self._env.step(action)
        self._length += 1
        if done:
            self._timestamp = datetime.datetime.now().strftime('%Y%m%dT%H%M%S')
            self._unlocked = sum((int(v >= 1) for v in info['achievements'].values()))
        return (obs, reward, done, info)

    @property
    def episode_name(self):
        return f'{self._timestamp}-ach{self._unlocked}-len{self._length}'

def step(self, action):
    obs, reward, done, info = self._env.step(action)
    self._length += 1
    if done:
        self._timestamp = datetime.datetime.now().strftime('%Y%m%dT%H%M%S')
        self._unlocked = sum((int(v >= 1) for v in info['achievements'].values()))
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

def count(self, material):
    return (self._mat_map == self._mat_ids[material]).sum()

