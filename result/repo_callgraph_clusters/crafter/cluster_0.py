# Cluster 0

def compute_scores(percents):
    assert (0 <= percents).all() and (percents <= 100).all()
    if (percents <= 1.0).all():
        print('Warning: The input may not be in the right range.')
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', category=RuntimeWarning)
        scores = np.exp(np.nanmean(np.log(1 + percents), -1)) - 1
    return scores

def binning(xs, ys, borders, reducer=np.nanmean, fill='nan'):
    xs, ys = (np.array(xs), np.array(ys))
    order = np.argsort(xs)
    xs, ys = (xs[order], ys[order])
    binned = []
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', category=RuntimeWarning)
        for start, stop in zip(borders[:-1], borders[1:]):
            left = (xs <= start).sum()
            right = (xs <= stop).sum()
            if left < right:
                value = reducer(ys[left:right])
            elif binned:
                value = {'nan': np.nan, 'last': binned[-1]}[fill]
            else:
                value = np.nan
            binned.append(value)
    return (borders[1:], np.array(binned))

def _set_material(world, pos, player, tunnels, simplex):
    x, y = pos
    simplex = functools.partial(_simplex, simplex)
    uniform = world.random.uniform
    start = 4 - np.sqrt((x - player.pos[0]) ** 2 + (y - player.pos[1]) ** 2)
    start += 2 * simplex(x, y, 8, 3)
    start = 1 / (1 + np.exp(-start))
    water = simplex(x, y, 3, {15: 1, 5: 0.15}, False) + 0.1
    water -= 2 * start
    mountain = simplex(x, y, 0, {15: 1, 5: 0.3})
    mountain -= 4 * start + 0.3 * water
    if start > 0.5:
        world[x, y] = 'grass'
    elif mountain > 0.15:
        if simplex(x, y, 6, 7) > 0.15 and mountain > 0.3:
            world[x, y] = 'path'
        elif simplex(2 * x, y / 5, 7, 3) > 0.4:
            world[x, y] = 'path'
            tunnels[x, y] = True
        elif simplex(x / 5, 2 * y, 7, 3) > 0.4:
            world[x, y] = 'path'
            tunnels[x, y] = True
        elif simplex(x, y, 1, 8) > 0 and uniform() > 0.85:
            world[x, y] = 'coal'
        elif simplex(x, y, 2, 6) > 0.4 and uniform() > 0.75:
            world[x, y] = 'iron'
        elif mountain > 0.18 and uniform() > 0.994:
            world[x, y] = 'diamond'
        elif mountain > 0.3 and simplex(x, y, 6, 5) > 0.35:
            world[x, y] = 'lava'
        else:
            world[x, y] = 'stone'
    elif 0.25 < water <= 0.35 and simplex(x, y, 4, 9) > -0.2:
        world[x, y] = 'sand'
    elif 0.3 < water:
        world[x, y] = 'water'
    elif simplex(x, y, 5, 7) > 0 and uniform() > 0.8:
        world[x, y] = 'tree'
    else:
        world[x, y] = 'grass'

def _set_object(world, pos, player, tunnels):
    x, y = pos
    uniform = world.random.uniform
    dist = np.sqrt((x - player.pos[0]) ** 2 + (y - player.pos[1]) ** 2)
    material, _ = world[x, y]
    if material not in constants.walkable:
        pass
    elif dist > 3 and material == 'grass' and (uniform() > 0.985):
        world.add(objects.Cow(world, (x, y)))
    elif dist > 10 and uniform() > 0.993:
        world.add(objects.Zombie(world, (x, y), player))
    elif material == 'path' and tunnels[x, y] and (uniform() > 0.95):
        world.add(objects.Skeleton(world, (x, y), player))

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

def _balance_chunk(self, chunk, objs):
    light = self._world.daylight
    self._balance_object(chunk, objs, objects.Zombie, 'grass', 6, 0, 0.3, 0.4, lambda pos: objects.Zombie(self._world, pos, self._player), lambda num, space: (0 if space < 50 else 3.5 - 3 * light, 3.5 - 3 * light))
    self._balance_object(chunk, objs, objects.Skeleton, 'path', 7, 7, 0.1, 0.1, lambda pos: objects.Skeleton(self._world, pos, self._player), lambda num, space: (0 if space < 6 else 1, 2))
    self._balance_object(chunk, objs, objects.Cow, 'grass', 5, 5, 0.01, 0.1, lambda pos: objects.Cow(self._world, pos), lambda num, space: (0 if space < 30 else 1, 1.5 + light))

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

@functools.lru_cache(10)
def _vignette(self, shape, stddev):
    xs, ys = np.meshgrid(np.linspace(-1, 1, shape[0]), np.linspace(-1, 1, shape[1]))
    return 1 - np.exp(-0.5 * (xs ** 2 + ys ** 2) / stddev ** 2).T

