# Cluster 1

def plot_reward(inpaths, outpath, legend, colors, cols=4, budget=1000000.0):
    runs = common.load_runs(inpaths, budget)
    percents, methods, seeds, tasks = common.compute_success_rates(runs, budget)
    if not legend:
        methods = sorted(set((run['method'] for run in runs)))
        legend = {x: x.replace('_', ' ').title() for x in methods}
    borders = np.arange(0, budget, 10000.0)
    fig, ax = plt.subplots(figsize=(4.5, 2.3))
    for j, (method, label) in enumerate(legend.items()):
        relevant = [run for run in runs if run['method'] == method]
        if not relevant:
            print(f'No runs found for method {method}.')
        binned_xs, binned_ys = ([], [])
        for run in relevant:
            xs, ys = common.binning(run['xs'], run['reward'], borders, np.nanmean)
            binned_xs.append(xs)
            binned_ys.append(ys)
        xs = np.concatenate(binned_xs)
        ys = np.concatenate(binned_ys)
        means = common.binning(xs, ys, borders, np.nanmean)[1]
        stds = common.binning(xs, ys, borders, np.nanstd)[1]
        kwargs = dict(alpha=0.2, linewidths=0, color=colors[j], zorder=10 - j)
        ax.fill_between(borders[1:], means - stds, means + stds, **kwargs)
        ax.plot(borders[1:], means, label=label, color=colors[j], zorder=100 - j)
    ax.axhline(y=22, c='#888888', ls='--', lw=1)
    ax.text(620000.0, 18, 'Optimal', c='#888888')
    ax.set_title('Crafter Reward')
    ax.set_xlim(0, budget)
    ax.ticklabel_format(axis='x', style='sci', scilimits=(0, 0))
    ax.grid(alpha=0.3)
    ax.xaxis.set_major_locator(ticker.MaxNLocator(5, steps=[1, 2, 2.5, 5, 10]))
    ax.yaxis.set_major_locator(ticker.MaxNLocator(6, steps=[1, 2, 2.5, 5, 10]))
    fig.tight_layout(rect=(0, 0, 0.55, 1))
    fig.legend(bbox_to_anchor=(0.52, 0.54), loc='center left', frameon=False)
    pathlib.Path(outpath).parent.mkdir(exist_ok=True, parents=True)
    fig.savefig(outpath)
    print(f'Saved {outpath}')

def plot_counts(inpath, outpath, color, budget=1000000.0, cols=4, size=(2, 1.8)):
    runs = common.load_runs([inpath], budget)
    percents, methods, seeds, tasks = common.compute_success_rates(runs, budget)
    borders = np.arange(0, budget, 10000.0)
    keys = ['reward', 'length'] + tasks
    rows = len(keys) // cols
    fig, axes = plt.subplots(nrows=rows, ncols=cols, figsize=(size[0] * cols, size[1] * rows))
    for ax, key in zip(axes.flatten(), keys):
        ax.set_title(key.replace('achievement_', '').replace('_', ' ').title())
        xs = np.concatenate([run['xs'] for run in runs])
        ys = np.concatenate([run[key] for run in runs])
        binxs, binys = common.binning(xs, ys, borders, np.nanmean)
        ax.plot(binxs, binys, color=color)
        mins = common.binning(xs, ys, borders, np.nanmin)[1]
        maxs = common.binning(xs, ys, borders, np.nanmax)[1]
        ax.fill_between(binxs, mins, maxs, linewidths=0, alpha=0.2, color=color)
        ax.ticklabel_format(axis='x', style='sci', scilimits=(0, 0))
        ax.xaxis.set_major_locator(ticker.MaxNLocator(4, steps=[1, 2, 2.5, 5, 10]))
        ax.yaxis.set_major_locator(ticker.MaxNLocator(5, steps=[1, 2, 2.5, 5, 10]))
        if maxs.max() == 0:
            ax.set_ylim(-0.05, 1.05)
    fig.tight_layout()
    pathlib.Path(outpath).parent.mkdir(exist_ok=True, parents=True)
    fig.savefig(outpath)
    print(f'Saved {outpath}')

def plot_spectrum(inpaths, outpath, legend, colors, budget=1000000.0, sort=False):
    runs = common.load_runs(inpaths, budget)
    percents, methods, seeds, tasks = common.compute_success_rates(runs, budget, sortby=sort and legend and list(legend.keys())[0])
    if not legend:
        methods = sorted(set((run['method'] for run in runs)))
        legend = {x: x.replace('_', ' ').title() for x in methods}
    fig, ax = plt.subplots(figsize=(7, 3))
    centers = np.arange(len(tasks))
    width = 0.7
    for index, (method, label) in enumerate(legend.items()):
        heights = np.nanmean(percents[methods.index(method)], 0)
        pos = centers + width * (0.5 / len(methods) + index / len(methods) - 0.5)
        color = colors[index]
        ax.bar(pos, heights, width / len(methods), label=label, color=color)
    names = [x[len('achievement_'):].replace('_', ' ').title() for x in tasks]
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.tick_params(axis='x', which='both', width=14, length=0.8, direction='inout')
    ax.set_xlim(centers[0] - 2 * (1 - width), centers[-1] + 2 * (1 - width))
    ax.set_xticks(centers + 0.0)
    ax.set_xticklabels(names, rotation=45, ha='right', rotation_mode='anchor')
    ax.set_ylabel('Success Rate (%)')
    ax.set_yscale('log')
    ax.set_ylim(0.01, 100)
    ax.set_yticks([0.01, 0.1, 1, 10, 100])
    ax.set_yticklabels('0.01 0.1 1 10 100'.split())
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.legend(loc='upper center', ncol=10, frameon=False, borderpad=0, borderaxespad=0)
    pathlib.Path(outpath).parent.mkdir(exist_ok=True, parents=True)
    fig.savefig(outpath)
    print(f'Saved {outpath}')

def plot_scores(inpaths, outpath, legend, colors, budget=1000000.0, ylim=None):
    runs = common.load_runs(inpaths, budget)
    percents, methods, seeds, tasks = common.compute_success_rates(runs, budget)
    scores = common.compute_scores(percents)
    if not legend:
        methods = sorted(set((run['method'] for run in runs)))
        legend = {x: x.replace('_', ' ').title() for x in methods}
    legend = dict(reversed(legend.items()))
    scores = scores[np.array([methods.index(m) for m in legend.keys()])]
    mean = np.nanmean(scores, -1)
    std = np.nanstd(scores, -1)
    fig, ax = plt.subplots(figsize=(4, 3))
    centers = np.arange(len(legend))
    width = 0.7
    colors = list(reversed(colors[:len(legend)]))
    error_kw = dict(capsize=5, c='#000')
    ax.bar(centers, mean, yerr=std, color=colors, error_kw=error_kw)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.tick_params(axis='x', which='both', width=50, length=0.8, direction='inout')
    ax.set_xlim(centers[0] - 2 * (1 - width), centers[-1] + 2 * (1 - width))
    ax.set_xticks(centers + 0.0)
    ax.set_xticklabels(list(legend.values()), rotation=45, ha='right', rotation_mode='anchor')
    ax.set_ylabel('Crafter Score (%)')
    if ylim:
        ax.set_ylim(0, ylim)
    fig.tight_layout()
    pathlib.Path(outpath).parent.mkdir(exist_ok=True, parents=True)
    fig.savefig(outpath)
    print(f'Saved {outpath}')

def print_spectrum(inpaths, legend, budget=1000000.0, sort=False):
    runs = common.load_runs(inpaths, budget)
    percents, methods, seeds, tasks = common.compute_success_rates(runs, budget)
    scores = common.compute_scores(percents)
    if not legend:
        methods = sorted(set((run['method'] for run in runs)))
        legend = {x: x.replace('_', ' ').title() for x in methods}
    scores = np.nanmean(scores, 1)
    percents = np.nanmean(percents, 1)
    if sort:
        first = next(iter(legend.keys()))
        tasks = sorted(tasks, key=lambda task: -np.nanmean(percents[first, task]))
    legend = dict(reversed(legend.items()))
    cols = ''.join((f' & \\textbf{{{k}}}' for k in legend.values()))
    print('\\newcommand{\\o}{\\hphantom{0}}')
    print('\\newcommand{\\b}[1]{\\textbf{#1}}')
    print('')
    print(f'{'Achievement':<20}' + cols + ' \\\\')
    print('')
    wins = collections.defaultdict(int)
    for task in tasks:
        k = tasks.index(task)
        if task.startswith('achievement_'):
            name = task[len('achievement_'):].replace('_', ' ').title()
        else:
            name = task.replace('_', ' ').title()
        print(f'{name:<20}', end='')
        best = max((percents[methods.index(m), k] for m in legend.keys()))
        for method in legend.keys():
            i = methods.index(method)
            value = percents[i][k]
            winner = value >= 0.95 * best and value > 0
            fmt = f'{value:.1f}\\%'
            fmt = ('\\o' if len(fmt) < 6 else ' ') + fmt
            fmt = f'\\b{{{fmt}}}' if winner else f'   {fmt} '
            if winner:
                wins[method] += 1
            print(f' & ${fmt}$', end='')
        print(' \\\\')
    print('')
    print(f'{'Score':<20}', end='')
    best = max((scores[methods.index(m)] for m in legend.keys()))
    for method in legend.keys():
        value = scores[methods.index(method)]
        bold = value >= 0.95 * best and value > 0
        fmt = f'{value:.1f}\\%'
        fmt = ('\\o' if len(fmt) < 6 else ' ') + fmt
        fmt = f'\\b{{{fmt}}}' if bold else f'   {fmt} '
        print(f' & ${fmt}$', end='')
    print(' \\\\')

def print_reward(inpaths, legend, budget=1000000.0, last=100000.0, sort=False):
    runs = common.load_runs(inpaths, budget)
    if not legend:
        methods = sorted(set((run['method'] for run in runs)))
        legend = {x: x.replace('_', ' ').title() for x in methods}
    seeds = sorted({x['seed'] for x in runs})
    rewards = np.empty((len(legend), len(seeds)))
    rewards[:] = np.nan
    for i, (method, label) in enumerate(legend.items()):
        relevant = [run for run in runs if run['method'] == method]
        if not relevant:
            print(f'No runs found for method {method}.')
        for run in relevant:
            j = seeds.index(run['seed'])
            xs = np.array(run['xs'])
            ys = np.array(run['reward'])
            rewards[i][j] = ys[-(xs >= xs.max() - last).sum()]
    means = np.nanmean(rewards, -1)
    stds = np.nanstd(rewards, -1)
    print('')
    print('\\textbf{Method} & \\textbf{Reward} \\\\')
    print('')
    for method, mean, std in zip(legend.values(), means, stds):
        mean = f'{mean:.1f}'
        mean = ('\\o' if len(mean) < 4 else ' ') + mean
        print(f'{method:<25} & ${mean} \\pm {std:4.1f}$ \\\\')
    print('')

def print_summary(runs, budget, verbose):
    episodes = np.array([len(x['length']) for x in runs])
    rewards = np.array([np.mean(x['reward']) for x in runs])
    lengths = np.array([np.mean(x['length']) for x in runs])
    percents, methods, seeds, tasks = common.compute_success_rates(runs, budget, sortby=0)
    scores = np.squeeze(common.compute_scores(percents))
    print(f'Score:        {np.mean(scores):10.2f} ± {np.std(scores):.2f}')
    print(f'Reward:       {np.mean(rewards):10.2f} ± {np.std(rewards):.2f}')
    print(f'Length:       {np.mean(lengths):10.2f} ± {np.std(lengths):.2f}')
    print(f'Episodes:     {np.mean(episodes):10.2f} ± {np.std(episodes):.2f}')
    if verbose:
        for task, percent in sorted(tasks, np.squeeze(percents).T):
            name = task[len('achievement_'):].replace('_', ' ').title()
            print(f'{name:<20}  {np.mean(percent):6.2f}%')

def compute_success_rates(runs, budget=1000000.0, sortby=None):
    methods = sorted(set((run['method'] for run in runs)))
    seeds = sorted(set((run['seed'] for run in runs)))
    tasks = sorted((key for key in runs[0] if key.startswith('achievement_')))
    percents = np.empty((len(methods), len(seeds), len(tasks)))
    percents[:] = np.nan
    for run in runs:
        episodes = (np.array(run['xs']) <= budget).sum()
        i = methods.index(run['method'])
        j = seeds.index(run['seed'])
        for key, values in run.items():
            if key in tasks:
                k = tasks.index(key)
                percent = 100 * (np.array(values[:episodes]) >= 1).mean()
                percents[i, j, k] = percent
    if isinstance(sortby, (str, int)):
        if isinstance(sortby, str):
            sortby = methods.index(sortby)
        order = np.argsort(-np.nanmean(percents[sortby], 0), -1)
        percents = percents[:, :, order]
        tasks = np.array(tasks)[order].tolist()
    return (percents, methods, seeds, tasks)

def print_scores(inpaths, legend, budget=1000000.0, sort=False):
    runs = common.load_runs(inpaths, budget)
    percents, methods, seeds, tasks = common.compute_success_rates(runs, budget)
    scores = common.compute_scores(percents)
    if not legend:
        methods = sorted(set((run['method'] for run in runs)))
        legend = {x: x.replace('_', ' ').title() for x in methods}
    scores = scores[np.array([methods.index(m) for m in legend.keys()])]
    means = np.nanmean(scores, -1)
    stds = np.nanstd(scores, -1)
    print('')
    print('\\textbf{Method} & \\textbf{Score} \\\\')
    print('')
    for method, mean, std in zip(legend.values(), means, stds):
        mean = f'{mean:.1f}'
        mean = ('\\o' if len(mean) < 4 else ' ') + mean
        print(f'{method:<25} & ${mean} \\pm {std:4.1f}\\%$ \\\\')
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

@property
def action_space(self):
    return DiscreteSpace(len(constants.actions))

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

