# Cluster 7

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

def _save(self):
    filename = str(self._directory / (self._env.episode_name + '.mp4'))
    imageio.mimsave(filename, self._frames)

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

def _save(self):
    filename = str(self._directory / (self._env.episode_name + '.npz'))
    for key, value in self._episode[1].items():
        if key not in self._episode[0]:
            self._episode[0][key] = np.zeros_like(value)
    episode = {k: np.array([step[k] for step in self._episode]) for k in self._episode[0]}
    np.savez_compressed(filename, **episode)

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

class ItemView:

    def __init__(self, textures, grid):
        self._textures = textures
        self._grid = np.array(grid)

    def __call__(self, inventory, unit):
        unit = np.array(unit)
        canvas = np.zeros(tuple(self._grid * unit) + (3,), np.uint8)
        for index, (item, amount) in enumerate(inventory.items()):
            if amount < 1:
                continue
            self._item(canvas, index, item, unit)
            self._amount(canvas, index, amount, unit)
        return canvas

    def _item(self, canvas, index, item, unit):
        pos = (index % self._grid[0], index // self._grid[0])
        pos = (pos * unit + 0.1 * unit).astype(np.int32)
        texture = self._textures.get(item, 0.8 * unit)
        _draw_alpha(canvas, pos, texture)

    def _amount(self, canvas, index, amount, unit):
        pos = (index % self._grid[0], index // self._grid[0])
        pos = (pos * unit + 0.4 * unit).astype(np.int32)
        text = str(amount) if amount in list(range(10)) else 'unknown'
        texture = self._textures.get(text, 0.6 * unit)
        _draw_alpha(canvas, pos, texture)

def _item(self, canvas, index, item, unit):
    pos = (index % self._grid[0], index // self._grid[0])
    pos = (pos * unit + 0.1 * unit).astype(np.int32)
    texture = self._textures.get(item, 0.8 * unit)
    _draw_alpha(canvas, pos, texture)

def _amount(self, canvas, index, amount, unit):
    pos = (index % self._grid[0], index // self._grid[0])
    pos = (pos * unit + 0.4 * unit).astype(np.int32)
    text = str(amount) if amount in list(range(10)) else 'unknown'
    texture = self._textures.get(text, 0.6 * unit)
    _draw_alpha(canvas, pos, texture)

def _draw_alpha(canvas, pos, texture):
    (x, y), (w, h) = (pos, texture.shape[:2])
    if texture.shape[-1] == 4:
        alpha = texture[..., 3:].astype(np.float32) / 255
        texture = texture[..., :3].astype(np.float32) / 255
        current = canvas[x:x + w, y:y + h].astype(np.float32) / 255
        blended = alpha * texture + (1 - alpha) * current
        texture = (255 * blended).astype(np.uint8)
    canvas[x:x + w, y:y + h] = texture

