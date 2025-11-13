# Cluster 4

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

@health.setter
def health(self, value):
    self.inventory['health'] = max(0, value)

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

class Cow(Object):

    def __init__(self, world, pos):
        super().__init__(world, pos)
        self.health = 3

    @property
    def texture(self):
        return 'cow'

    def update(self):
        if self.health <= 0:
            self.world.remove(self)
        if self.random.uniform() < 0.5:
            direction = self.random_dir()
            self.move(direction)

def update(self):
    if self.health <= 0:
        self.world.remove(self)
    if self.random.uniform() < 0.5:
        direction = self.random_dir()
        self.move(direction)

class Zombie(Object):

    def __init__(self, world, pos, player):
        super().__init__(world, pos)
        self.player = player
        self.health = 5
        self.cooldown = 0

    @property
    def texture(self):
        return 'zombie'

    def update(self):
        if self.health <= 0:
            self.world.remove(self)
        dist = self.distance(self.player)
        if dist <= 8 and self.random.uniform() < 0.9:
            self.move(self.toward(self.player, self.random.uniform() < 0.8))
        else:
            self.move(self.random_dir())
        dist = self.distance(self.player)
        if dist <= 1:
            if self.cooldown:
                self.cooldown -= 1
            else:
                if self.player.sleeping:
                    damage = 7
                else:
                    damage = 2
                self.player.health -= damage
                self.cooldown = 5

def update(self):
    if self.health <= 0:
        self.world.remove(self)
    dist = self.distance(self.player)
    if dist <= 8 and self.random.uniform() < 0.9:
        self.move(self.toward(self.player, self.random.uniform() < 0.8))
    else:
        self.move(self.random_dir())
    dist = self.distance(self.player)
    if dist <= 1:
        if self.cooldown:
            self.cooldown -= 1
        else:
            if self.player.sleeping:
                damage = 7
            else:
                damage = 2
            self.player.health -= damage
            self.cooldown = 5

class Skeleton(Object):

    def __init__(self, world, pos, player):
        super().__init__(world, pos)
        self.player = player
        self.health = 3
        self.reload = 0

    @property
    def texture(self):
        return 'skeleton'

    def update(self):
        if self.health <= 0:
            self.world.remove(self)
        self.reload = max(0, self.reload - 1)
        dist = self.distance(self.player.pos)
        if dist <= 3:
            moved = self.move(-self.toward(self.player, self.random.uniform() < 0.6))
            if moved:
                return
        if dist <= 5 and self.random.uniform() < 0.5:
            self._shoot(self.toward(self.player))
        elif dist <= 8 and self.random.uniform() < 0.3:
            self.move(self.toward(self.player, self.random.uniform() < 0.6))
        elif self.random.uniform() < 0.2:
            self.move(self.random_dir())

    def _shoot(self, direction):
        if self.reload > 0:
            return
        if direction[0] == 0 and direction[1] == 0:
            return
        pos = self.pos + direction
        if self.is_free(pos, Arrow.walkable):
            self.world.add(Arrow(self.world, pos, direction))
            self.reload = 4

def update(self):
    if self.health <= 0:
        self.world.remove(self)
    self.reload = max(0, self.reload - 1)
    dist = self.distance(self.player.pos)
    if dist <= 3:
        moved = self.move(-self.toward(self.player, self.random.uniform() < 0.6))
        if moved:
            return
    if dist <= 5 and self.random.uniform() < 0.5:
        self._shoot(self.toward(self.player))
    elif dist <= 8 and self.random.uniform() < 0.3:
        self.move(self.toward(self.player, self.random.uniform() < 0.6))
    elif self.random.uniform() < 0.2:
        self.move(self.random_dir())

class Arrow(Object):

    def __init__(self, world, pos, facing):
        super().__init__(world, pos)
        self.facing = facing

    @property
    def texture(self):
        return {(-1, 0): 'arrow-left', (+1, 0): 'arrow-right', (0, -1): 'arrow-up', (0, +1): 'arrow-down'}[tuple(self.facing)]

    @engine.staticproperty
    def walkable():
        return constants.walkable + ['water', 'lava']

    def update(self):
        target = self.pos + self.facing
        material, obj = self.world[target]
        if obj:
            obj.health -= 2
            self.world.remove(self)
        elif material not in self.walkable:
            self.world.remove(self)
            if material in ['table', 'furnace']:
                self.world[target] = 'path'
        else:
            self.move(self.facing)

def update(self):
    target = self.pos + self.facing
    material, obj = self.world[target]
    if obj:
        obj.health -= 2
        self.world.remove(self)
    elif material not in self.walkable:
        self.world.remove(self)
        if material in ['table', 'furnace']:
            self.world[target] = 'path'
    else:
        self.move(self.facing)

class Plant(Object):

    def __init__(self, world, pos):
        super().__init__(world, pos)
        self.health = 1
        self.grown = 0

    @property
    def texture(self):
        if self.ripe:
            return 'plant-ripe'
        else:
            return 'plant'

    @property
    def ripe(self):
        return self.grown > 300

    def update(self):
        self.grown += 1
        objs = [self.world[self.pos + dir_][1] for dir_ in self.all_dirs]
        if any((isinstance(obj, (Zombie, Skeleton, Cow)) for obj in objs)):
            self.health -= 1
        if self.health <= 0:
            self.world.remove(self)

def update(self):
    self.grown += 1
    objs = [self.world[self.pos + dir_][1] for dir_ in self.all_dirs]
    if any((isinstance(obj, (Zombie, Skeleton, Cow)) for obj in objs)):
        self.health -= 1
    if self.health <= 0:
        self.world.remove(self)

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

def remove(self, obj):
    if obj.removed:
        return
    self._objects[self._obj_map[tuple(obj.pos)]] = None
    self._obj_map[tuple(obj.pos)] = 0
    self._chunks[self.chunk_key(obj.pos)].remove(obj)
    obj.removed = True

class LocalView:

    def __init__(self, world, textures, grid):
        self._world = world
        self._textures = textures
        self._grid = np.array(grid)
        self._offset = self._grid // 2
        self._area = np.array(self._world.area)
        self._center = None

    def __call__(self, player, unit):
        self._unit = np.array(unit)
        self._center = np.array(player.pos)
        canvas = np.zeros(tuple(self._grid * unit) + (3,), np.uint8) + 127
        for x in range(self._grid[0]):
            for y in range(self._grid[1]):
                pos = self._center + np.array([x, y]) - self._offset
                if not _inside((0, 0), pos, self._area):
                    continue
                texture = self._textures.get(self._world[pos][0], unit)
                _draw(canvas, np.array([x, y]) * unit, texture)
        for obj in self._world.objects:
            pos = obj.pos - self._center + self._offset
            if not _inside((0, 0), pos, self._grid):
                continue
            texture = self._textures.get(obj.texture, unit)
            _draw_alpha(canvas, pos * unit, texture)
        canvas = self._light(canvas, self._world.daylight)
        if player.sleeping:
            canvas = self._sleep(canvas)
        return canvas

    def _light(self, canvas, daylight):
        night = canvas
        if daylight < 0.5:
            night = self._noise(night, 2 * (0.5 - daylight), 0.5)
        night = np.array(ImageEnhance.Color(Image.fromarray(night.astype(np.uint8))).enhance(0.4))
        night = self._tint(night, (0, 16, 64), 0.5)
        return daylight * canvas + (1 - daylight) * night

    def _sleep(self, canvas):
        canvas = np.array(ImageEnhance.Color(Image.fromarray(canvas.astype(np.uint8))).enhance(0.0))
        canvas = self._tint(canvas, (0, 0, 16), 0.5)
        return canvas

    def _tint(self, canvas, color, amount):
        color = np.array(color)
        return (1 - amount) * canvas + amount * color

    def _noise(self, canvas, amount, stddev):
        noise = self._world.random.uniform(32, 127, canvas.shape[:2])[..., None]
        mask = amount * self._vignette(canvas.shape, stddev)[..., None]
        return (1 - mask) * canvas + mask * noise

    @functools.lru_cache(10)
    def _vignette(self, shape, stddev):
        xs, ys = np.meshgrid(np.linspace(-1, 1, shape[0]), np.linspace(-1, 1, shape[1]))
        return 1 - np.exp(-0.5 * (xs ** 2 + ys ** 2) / stddev ** 2).T

def _noise(self, canvas, amount, stddev):
    noise = self._world.random.uniform(32, 127, canvas.shape[:2])[..., None]
    mask = amount * self._vignette(canvas.shape, stddev)[..., None]
    return (1 - mask) * canvas + mask * noise

