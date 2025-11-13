# Cluster 2

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', type=int, default=None)
    parser.add_argument('--area', nargs=2, type=int, default=(64, 64))
    parser.add_argument('--length', type=int, default=10000)
    parser.add_argument('--health', type=int, default=9)
    parser.add_argument('--record', type=pathlib.Path, default=None)
    parser.add_argument('--episodes', type=int, default=1)
    args = parser.parse_args()
    random = np.random.RandomState(args.seed)
    crafter.constants.items['health']['max'] = args.health
    crafter.constants.items['health']['initial'] = args.health
    env = crafter.Env(area=args.area, length=args.length, seed=args.seed)
    env = crafter.Recorder(env, args.record)
    for _ in range(args.episodes):
        start = time.time()
        obs = env.reset()
        print('')
        print(f'Reset time: {1000 * (time.time() - start):.2f}ms')
        print('Coal exist:    ', env._world.count('coal'))
        print('Iron exist:    ', env._world.count('iron'))
        print('Diamonds exist:', env._world.count('diamond'))
        start = time.time()
        done = False
        while not done:
            action = random.randint(0, env.action_space.n)
            obs, reward, done, info = env.step(action)
        duration = time.time() - start
        step = env._step
        print(f'Step time: {1000 * duration / step:.2f}ms ({int(step / duration)} FPS)')
        print('Episode length:', step)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', type=int, default=None)
    parser.add_argument('--amount', type=int, default=4)
    parser.add_argument('--cols', type=int, default=4)
    parser.add_argument('--area', nargs=2, type=int, default=(64, 64))
    parser.add_argument('--size', type=int, default=1024)
    parser.add_argument('--filename', type=str, default='terrain.png')
    args = parser.parse_args()
    env = crafter.Env(args.area, args.area, args.size, seed=args.seed)
    images = []
    for index in range(args.amount):
        images.append(env.reset())
        diamonds = env._world.count('diamond')
        print(f'Map: {index:>2}, diamonds: {diamonds:>2}')
    rows = len(images) // args.cols
    strips = []
    for row in range(rows):
        strip = []
        for col in range(args.cols):
            try:
                strip.append(images[row * args.cols + col])
            except IndexError:
                strip.append(np.zeros_like(strip[-1]))
        strips.append(np.concatenate(strip, 1))
    grid = np.concatenate(strips, 0)
    imageio.imsave(args.filename, grid)
    print('Saved', args.filename)

def generate_world(world, player):
    simplex = opensimplex.OpenSimplex(seed=world.random.randint(0, 2 ** 31 - 1))
    tunnels = np.zeros(world.area, bool)
    for x in range(world.area[0]):
        for y in range(world.area[1]):
            _set_material(world, (x, y), player, tunnels, simplex)
    for x in range(world.area[0]):
        for y in range(world.area[1]):
            _set_object(world, (x, y), player, tunnels)

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

def _obs(self):
    return self.render()

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

def random_dir(self):
    return self.all_dirs[self.random.randint(0, 4)]

def main():
    boolean = lambda x: bool(['False', 'True'].index(x))
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', type=int, default=None)
    parser.add_argument('--area', nargs=2, type=int, default=(64, 64))
    parser.add_argument('--view', type=int, nargs=2, default=(9, 9))
    parser.add_argument('--length', type=int, default=None)
    parser.add_argument('--health', type=int, default=9)
    parser.add_argument('--window', type=int, nargs=2, default=(600, 600))
    parser.add_argument('--size', type=int, nargs=2, default=(0, 0))
    parser.add_argument('--record', type=str, default=None)
    parser.add_argument('--fps', type=int, default=5)
    parser.add_argument('--wait', type=boolean, default=False)
    parser.add_argument('--death', type=str, default='reset', choices=['continue', 'reset', 'quit'])
    args = parser.parse_args()
    keymap = {pygame.K_a: 'move_left', pygame.K_d: 'move_right', pygame.K_w: 'move_up', pygame.K_s: 'move_down', pygame.K_SPACE: 'do', pygame.K_TAB: 'sleep', pygame.K_r: 'place_stone', pygame.K_t: 'place_table', pygame.K_f: 'place_furnace', pygame.K_p: 'place_plant', pygame.K_1: 'make_wood_pickaxe', pygame.K_2: 'make_stone_pickaxe', pygame.K_3: 'make_iron_pickaxe', pygame.K_4: 'make_wood_sword', pygame.K_5: 'make_stone_sword', pygame.K_6: 'make_iron_sword'}
    print('Actions:')
    for key, action in keymap.items():
        print(f'  {pygame.key.name(key)}: {action}')
    crafter.constants.items['health']['max'] = args.health
    crafter.constants.items['health']['initial'] = args.health
    size = list(args.size)
    size[0] = size[0] or args.window[0]
    size[1] = size[1] or args.window[1]
    env = crafter.Env(area=args.area, view=args.view, length=args.length, seed=args.seed)
    env = crafter.Recorder(env, args.record)
    env.reset()
    achievements = set()
    duration = 0
    return_ = 0
    was_done = False
    print('Diamonds exist:', env._world.count('diamond'))
    pygame.init()
    screen = pygame.display.set_mode(args.window)
    clock = pygame.time.Clock()
    running = True
    while running:
        image = env.render(size)
        if size != args.window:
            image = Image.fromarray(image)
            image = image.resize(args.window, resample=Image.NEAREST)
            image = np.array(image)
        surface = pygame.surfarray.make_surface(image.transpose((1, 0, 2)))
        screen.blit(surface, (0, 0))
        pygame.display.flip()
        clock.tick(args.fps)
        action = None
        pygame.event.pump()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.KEYDOWN and event.key in keymap.keys():
                action = keymap[event.key]
        if action is None:
            pressed = pygame.key.get_pressed()
            for key, action in keymap.items():
                if pressed[key]:
                    break
            else:
                if args.wait and (not env._player.sleeping):
                    continue
                else:
                    action = 'noop'
        _, reward, done, _ = env.step(env.action_names.index(action))
        duration += 1
        unlocked = {name for name, count in env._player.achievements.items() if count > 0 and name not in achievements}
        for name in unlocked:
            achievements |= unlocked
            total = len(env._player.achievements.keys())
            print(f'Achievement ({len(achievements)}/{total}): {name}')
        if env._step > 0 and env._step % 100 == 0:
            print(f'Time step: {env._step}')
        if reward:
            print(f'Reward: {reward}')
            return_ += reward
        if done and (not was_done):
            was_done = True
            print('Episode done!')
            print('Duration:', duration)
            print('Return:', return_)
            if args.death == 'quit':
                running = False
            if args.death == 'reset':
                print('\nStarting a new episode.')
                env.reset()
                achievements = set()
                was_done = False
                duration = 0
                return_ = 0
            if args.death == 'continue':
                pass
    pygame.quit()

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

def reset(self):
    obs = self._env.reset()
    self._length = 0
    self._reward = 0
    self._unlocked = None
    self._stats = None
    return obs

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

def reset(self):
    obs = self._env.reset()
    self._frames = [self._env.render(self._size)]
    return obs

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

def reset(self):
    obs = self._env.reset()
    self._episode = [{'image': obs}]
    return obs

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

def reset(self):
    obs = self._env.reset()
    self._timestamp = None
    self._unlocked = None
    self._length = 0
    return obs

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

