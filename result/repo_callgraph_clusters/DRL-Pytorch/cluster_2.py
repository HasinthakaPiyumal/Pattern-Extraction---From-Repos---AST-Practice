# Cluster 2

def evaluate_policy(env, agent, turns=3):
    total_scores = 0
    for j in range(turns):
        s, info = env.reset()
        done = False
        while not done:
            a = agent.select_action(s, deterministic=True)
            s_next, r, dw, tr, info = env.step(a)
            done = dw or tr
            total_scores += r
            s = s_next
    return int(total_scores / turns)

def main():
    EnvName = ['Pendulum-v1', 'LunarLanderContinuous-v2', 'Humanoid-v4', 'HalfCheetah-v4', 'BipedalWalker-v3', 'BipedalWalkerHardcore-v3']
    BrifEnvName = ['PV1', 'LLdV2', 'Humanv4', 'HCv4', 'BWv3', 'BWHv3']
    env = gym.make(EnvName[opt.EnvIdex], render_mode='human' if opt.render else None)
    eval_env = gym.make(EnvName[opt.EnvIdex])
    opt.state_dim = env.observation_space.shape[0]
    opt.action_dim = env.action_space.shape[0]
    opt.max_action = float(env.action_space.high[0])
    print(f'Env:{EnvName[opt.EnvIdex]}  state_dim:{opt.state_dim}  action_dim:{opt.action_dim}  max_a:{opt.max_action}  min_a:{env.action_space.low[0]}  max_e_steps:{env._max_episode_steps}')
    env_seed = opt.seed
    torch.manual_seed(opt.seed)
    torch.cuda.manual_seed(opt.seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    print('Random Seed: {}'.format(opt.seed))
    if opt.write:
        from torch.utils.tensorboard import SummaryWriter
        timenow = str(datetime.now())[0:-10]
        timenow = ' ' + timenow[0:13] + '_' + timenow[-2:]
        writepath = 'runs/{}'.format(BrifEnvName[opt.EnvIdex]) + timenow
        if os.path.exists(writepath):
            shutil.rmtree(writepath)
        writer = SummaryWriter(log_dir=writepath)
    if not os.path.exists('model'):
        os.mkdir('model')
    agent = DDPG_agent(**vars(opt))
    if opt.Loadmodel:
        agent.load(BrifEnvName[opt.EnvIdex], opt.ModelIdex)
    if opt.render:
        while True:
            score = evaluate_policy(env, agent, turns=1)
            print('EnvName:', BrifEnvName[opt.EnvIdex], 'score:', score)
    else:
        total_steps = 0
        while total_steps < opt.Max_train_steps:
            s, info = env.reset(seed=env_seed)
            env_seed += 1
            done = False
            'Interact & trian'
            while not done:
                if total_steps < opt.random_steps:
                    a = env.action_space.sample()
                else:
                    a = agent.select_action(s, deterministic=False)
                s_next, r, dw, tr, info = env.step(a)
                done = dw or tr
                agent.replay_buffer.add(s, a, r, s_next, dw)
                s = s_next
                total_steps += 1
                'train'
                if total_steps >= opt.random_steps:
                    agent.train()
                'record & log'
                if total_steps % opt.eval_interval == 0:
                    ep_r = evaluate_policy(eval_env, agent, turns=3)
                    if opt.write:
                        writer.add_scalar('ep_r', ep_r, global_step=total_steps)
                    print(f'EnvName:{BrifEnvName[opt.EnvIdex]}, Steps: {int(total_steps / 1000)}k, Episode Reward:{ep_r}')
                'save model'
                if total_steps % opt.save_interval == 0:
                    agent.save(BrifEnvName[opt.EnvIdex], int(total_steps / 1000))
        env.close()
        eval_env.close()

def evaluate_policy(env, model, turns=3):
    scores = 0
    for j in range(turns):
        s, info = env.reset()
        done = False
        while not done:
            a = model.select_action(s, deterministic=True)
            s_next, r, dw, tr, info = env.step(a)
            done = dw + tr
            scores += r
            s = s_next
    return int(scores / turns)

def main():
    EnvName = ['CartPole-v1', 'LunarLander-v2']
    BriefEnvName = ['CPV1', 'LLdV2']
    env = gym.make(EnvName[opt.EnvIdex])
    eval_env = gym.make(EnvName[opt.EnvIdex], render_mode='human' if opt.render else None)
    opt.state_dim = env.observation_space.shape[0]
    opt.action_dim = env.action_space.n
    opt.max_e_steps = env._max_episode_steps
    if opt.DDQN:
        algo_name = 'DDQN'
    else:
        algo_name = 'DQN'
    torch.manual_seed(opt.seed)
    np.random.seed(opt.seed)
    print('Algorithm:', algo_name, '  Env:', BriefEnvName[opt.EnvIdex], '  state_dim:', opt.state_dim, '  action_dim:', opt.action_dim, '  Random Seed:', opt.seed, '  max_e_steps:', opt.max_e_steps, '\n')
    if opt.write:
        timenow = str(datetime.now())[0:-10]
        timenow = ' ' + timenow[0:13] + '_' + timenow[-2:]
        writepath = 'runs/Prior{}_{}'.format(algo_name, BriefEnvName[opt.EnvIdex]) + timenow
        if os.path.exists(writepath):
            shutil.rmtree(writepath)
        writer = SummaryWriter(log_dir=writepath)
    if not os.path.exists('model'):
        os.mkdir('model')
    model = DQN_Agent(opt)
    if opt.Loadmodel:
        model.load(algo_name, BriefEnvName[opt.EnvIdex], opt.ModelIdex)
    buffer = PrioritizedReplayBuffer(opt)
    exp_noise_scheduler = LinearSchedule(opt.noise_decay_steps, opt.exp_noise_init, opt.exp_noise_end)
    beta_scheduler = LinearSchedule(opt.beta_gain_steps, opt.beta_init, 1.0)
    if opt.render:
        score = evaluate_policy(eval_env, model, 5)
        print('EnvName:', BriefEnvName[opt.EnvIdex], 'seed:', opt.seed, 'score:', score)
    else:
        total_steps = 0
        while total_steps < opt.Max_train_steps:
            s, info = env.reset()
            done, ep_step = (False, 0)
            while not done:
                ep_step += 1
                if buffer.size < opt.warmup:
                    a = env.action_space.sample()
                else:
                    a = model.select_action(s, deterministic=False)
                s_next, r, dw, tr, info = env.step(a)
                if r <= -100:
                    r = -10
                buffer.add(s, a, r, s_next, dw)
                done = dw + tr
                s = s_next
                model.exp_noise = exp_noise_scheduler.value(total_steps)
                buffer.beta = beta_scheduler.value(total_steps)
                'update if its time'
                if total_steps >= opt.warmup and total_steps % opt.update_every == 0:
                    for j in range(opt.update_every):
                        model.train(buffer)
                'record & log'
                if total_steps % opt.eval_interval == 0:
                    score = evaluate_policy(eval_env, model)
                    if opt.write:
                        writer.add_scalar('ep_r', score, global_step=total_steps)
                        writer.add_scalar('p_sum', buffer.sum_tree.priority_sum, global_step=total_steps)
                        writer.add_scalar('p_max', buffer.sum_tree.priority_max, global_step=total_steps)
                        writer.add_scalar('noise', model.exp_noise, global_step=total_steps)
                        writer.add_scalar('beta', buffer.beta, global_step=total_steps)
                    print('EnvName:', BriefEnvName[opt.EnvIdex], 'seed:', opt.seed, 'steps: {}k'.format(int(total_steps / 1000)), 'score:', int(score))
                total_steps += 1
                'save model'
                if total_steps % opt.save_interval == 0:
                    model.save(algo_name, BriefEnvName[opt.EnvIdex], total_steps)
    env.close()

def evaluate_policy(env, model, turns=3):
    scores = 0
    for j in range(turns):
        s, info = env.reset()
        done = False
        while not done:
            a = model.select_action(s, deterministic=True)
            s_next, r, dw, tr, info = env.step(a)
            done = dw + tr
            scores += r
            s = s_next
    return int(scores / turns)

def main():
    EnvName = ['CartPole-v1', 'LunarLander-v2']
    BriefEnvName = ['CPV1', 'LLdV2']
    Env_With_DW = [True, True]
    opt.env_with_dw = Env_With_DW[opt.EnvIdex]
    env = gym.make(EnvName[opt.EnvIdex])
    eval_env = gym.make(EnvName[opt.EnvIdex], render_mode='human' if opt.render else None)
    opt.state_dim = env.observation_space.shape[0]
    opt.action_dim = env.action_space.n
    opt.max_e_steps = env._max_episode_steps
    if opt.DDQN:
        algo_name = 'DDQN'
    else:
        algo_name = 'DQN'
    torch.manual_seed(opt.seed)
    np.random.seed(opt.seed)
    print('Algorithm:', algo_name, '  Env:', BriefEnvName[opt.EnvIdex], '  state_dim:', opt.state_dim, '  action_dim:', opt.action_dim, '  Random Seed:', opt.seed, '  max_e_steps:', opt.max_e_steps, '\n')
    if opt.write:
        timenow = str(datetime.now())[0:-10]
        timenow = ' ' + timenow[0:13] + '_' + timenow[-2:]
        writepath = 'runs/LightPrior{}_{}'.format(algo_name, BriefEnvName[opt.EnvIdex]) + timenow
        if os.path.exists(writepath):
            shutil.rmtree(writepath)
        writer = SummaryWriter(log_dir=writepath)
    if not os.path.exists('model'):
        os.mkdir('model')
    model = DQN_Agent(opt)
    if opt.Loadmodel:
        model.load(algo_name, BriefEnvName[opt.EnvIdex], opt.ModelIdex)
    buffer = LightPriorReplayBuffer(opt)
    exp_noise_scheduler = LinearSchedule(opt.noise_decay_steps, opt.exp_noise_init, opt.exp_noise_end)
    beta_scheduler = LinearSchedule(opt.beta_gain_steps, opt.beta_init, 1.0)
    lr_scheduler = LinearSchedule(opt.lr_decay_steps, opt.lr_init, opt.lr_end)
    if opt.render:
        score = evaluate_policy(eval_env, model, 20)
        print('EnvName:', BriefEnvName[opt.EnvIdex], 'seed:', opt.seed, 'score:', score)
    else:
        total_steps = 0
        while total_steps < opt.Max_train_steps:
            s, info = env.reset()
            a, q_a = model.select_action(s, deterministic=False)
            while True:
                s_next, r, dw, tr, info = env.step(a)
                if r <= -100:
                    r = -10
                a_next, q_a_next = model.select_action(s_next, deterministic=False)
                priority = (torch.abs(r + ~dw * opt.gamma * q_a_next - q_a) + 0.01) ** opt.alpha
                buffer.add(s, a, r, dw, tr, priority)
                s, a, q_a = (s_next, a_next, q_a_next)
                'update if its time'
                if total_steps >= opt.warmup and total_steps % opt.update_every == 0:
                    for j in range(opt.update_every):
                        model.train(buffer)
                    model.exp_noise = exp_noise_scheduler.value(total_steps)
                    buffer.beta = beta_scheduler.value(total_steps)
                    for p in model.q_net_optimizer.param_groups:
                        p['lr'] = lr_scheduler.value(total_steps)
                'record & log'
                if total_steps % opt.eval_interval == 0:
                    score = evaluate_policy(eval_env, model)
                    if opt.write:
                        writer.add_scalar('ep_r', score, global_step=total_steps)
                        writer.add_scalar('noise', model.exp_noise, global_step=total_steps)
                        writer.add_scalar('beta', buffer.beta, global_step=total_steps)
                    print('EnvName:', BriefEnvName[opt.EnvIdex], 'seed:', opt.seed, 'steps: {}k'.format(int(total_steps / 1000)), 'score:', int(score))
                total_steps += 1
                'save model'
                if total_steps % opt.save_interval == 0:
                    model.save(algo_name, BriefEnvName[opt.EnvIdex], int(total_steps / 1000))
                if dw or tr:
                    break
    env.close()
    eval_env.close()

def evaluate_policy(env, model, render, turns=3):
    scores = 0
    for j in range(turns):
        s, done, ep_r, steps = (env.reset(), False, 0, 0)
        while not done:
            a = model.select_action(s, deterministic=True)
            s_prime, r, done, info = env.step(a)
            ep_r += r
            steps += 1
            s = s_prime
            if render:
                env.render()
        scores += ep_r
    return int(scores / turns)

def main():
    EnvName = ['CartPole-v1', 'LunarLander-v2']
    BriefEnvName = ['CPV1', 'LLdV2']
    env = gym.make(EnvName[opt.EnvIdex])
    eval_env = gym.make(EnvName[opt.EnvIdex])
    opt.state_dim = env.observation_space.shape[0]
    opt.action_dim = env.action_space.n
    opt.max_e_steps = env._max_episode_steps
    if opt.DDQN:
        algo_name = 'DDQN'
    else:
        algo_name = 'DQN'
    torch.manual_seed(opt.seed)
    env.seed(opt.seed)
    env.action_space.seed(opt.seed)
    eval_env.seed(opt.seed)
    eval_env.action_space.seed(opt.seed)
    np.random.seed(opt.seed)
    print('Algorithm:', algo_name, '  Env:', BriefEnvName[opt.EnvIdex], '  state_dim:', opt.state_dim, '  action_dim:', opt.action_dim, '  Random Seed:', opt.seed, '  max_e_steps:', opt.max_e_steps, '\n')
    if opt.write:
        timenow = str(datetime.now())[0:-10]
        timenow = ' ' + timenow[0:13] + '_' + timenow[-2:]
        writepath = 'runs/Prior{}_{}'.format(algo_name, BriefEnvName[opt.EnvIdex]) + timenow
        if os.path.exists(writepath):
            shutil.rmtree(writepath)
        writer = SummaryWriter(log_dir=writepath)
    if not os.path.exists('model'):
        os.mkdir('model')
    model = DQN_Agent(opt)
    if opt.Loadmodel:
        model.load(algo_name, BriefEnvName[opt.EnvIdex], opt.ModelIdex)
    buffer = PrioritizedReplayBuffer(opt)
    exp_noise_scheduler = LinearSchedule(opt.noise_decay_steps, opt.exp_noise_init, opt.exp_noise_end)
    beta_scheduler = LinearSchedule(opt.beta_gain_steps, opt.beta_init, 1.0)
    if opt.render:
        score = evaluate_policy(eval_env, model, True, 20)
        print('EnvName:', BriefEnvName[opt.EnvIdex], 'seed:', opt.seed, 'score:', score)
    else:
        total_steps = 0
        while total_steps < opt.Max_train_steps:
            s, done, ep_r, steps = (env.reset(), False, 0, 0)
            while not done:
                steps += 1
                if buffer.size < opt.warmup:
                    a = env.action_space.sample()
                else:
                    a = model.select_action(s, deterministic=False)
                s_next, r, done, info = env.step(a)
                'Avoid impacts caused by reaching max episode steps'
                if done and steps != opt.max_e_steps:
                    dw = True
                    if opt.EnvIdex == 1:
                        if r <= -100:
                            r = -10
                else:
                    dw = False
                buffer.add(s, a, r, s_next, dw)
                s = s_next
                ep_r += r
                model.exp_noise = exp_noise_scheduler.value(total_steps)
                buffer.beta = beta_scheduler.value(total_steps)
                'update if its time'
                if total_steps >= opt.warmup and total_steps % opt.update_every == 0:
                    for j in range(opt.update_every):
                        model.train(buffer)
                'record & log'
                if total_steps % opt.eval_interval == 0:
                    score = evaluate_policy(eval_env, model, render=False)
                    if opt.write:
                        writer.add_scalar('ep_r', score, global_step=total_steps)
                        writer.add_scalar('p_sum', buffer.sum_tree.priority_sum, global_step=total_steps)
                        writer.add_scalar('p_max', buffer.sum_tree.priority_max, global_step=total_steps)
                        writer.add_scalar('noise', model.exp_noise, global_step=total_steps)
                        writer.add_scalar('beta', buffer.beta, global_step=total_steps)
                    print('EnvName:', BriefEnvName[opt.EnvIdex], 'seed:', opt.seed, 'steps: {}k'.format(int(total_steps / 1000)), 'score:', int(score))
                total_steps += 1
                'save model'
                if total_steps % opt.save_interval == 0:
                    model.save(algo_name, BriefEnvName[opt.EnvIdex], total_steps)
    env.close()

def evaluate_policy(env, agent, seed, turns=3):
    agent.q_net.eval()
    scores = 0
    for j in range(turns):
        s, info = env.reset(seed=seed)
        done = False
        while not done:
            a = agent.select_action(s, evaluate=True)
            s_next, r, dw, tr, info = env.step(a)
            done = dw or tr
            scores += r
            s = s_next
    agent.q_net.train()
    return int(scores / turns)

class NoopResetEnv(gym.Wrapper):
    """Sample initial states by taking random number of no-ops on reset.

    No-op is assumed to be action 0.

    :param gym.Env env: the environment to wrap.
    :param int noop_max: the maximum value of no-ops to run.
    """

    def __init__(self, env, noop_max=30) -> None:
        super().__init__(env)
        self.noop_max = noop_max
        self.noop_action = 0
        assert env.unwrapped.get_action_meanings()[0] == 'NOOP'

    def reset(self, **kwargs):
        _, info, return_info = _parse_reset_result(self.env.reset(**kwargs))
        if hasattr(self.unwrapped.np_random, 'integers'):
            noops = self.unwrapped.np_random.integers(1, self.noop_max + 1)
        else:
            noops = self.unwrapped.np_random.randint(1, self.noop_max + 1)
        for _ in range(noops):
            step_result = self.env.step(self.noop_action)
            if len(step_result) == 4:
                obs, rew, done, info = step_result
            else:
                obs, rew, term, trunc, info = step_result
                done = term or trunc
            if done:
                obs, info, _ = _parse_reset_result(self.env.reset())
        if return_info:
            return (obs, info)
        return obs

def reset(self, **kwargs):
    _, info, return_info = _parse_reset_result(self.env.reset(**kwargs))
    if hasattr(self.unwrapped.np_random, 'integers'):
        noops = self.unwrapped.np_random.integers(1, self.noop_max + 1)
    else:
        noops = self.unwrapped.np_random.randint(1, self.noop_max + 1)
    for _ in range(noops):
        step_result = self.env.step(self.noop_action)
        if len(step_result) == 4:
            obs, rew, done, info = step_result
        else:
            obs, rew, term, trunc, info = step_result
            done = term or trunc
        if done:
            obs, info, _ = _parse_reset_result(self.env.reset())
    if return_info:
        return (obs, info)
    return obs

class MaxAndSkipEnv(gym.Wrapper):
    """Return only every `skip`-th frame (frameskipping) using most recent raw observations (for max pooling across time steps).

    :param gym.Env env: the environment to wrap.
    :param int skip: number of `skip`-th frame.
    """

    def __init__(self, env, skip=4) -> None:
        super().__init__(env)
        self._skip = skip

    def step(self, action):
        """Step the environment with the given action.

        Repeat action, sum reward, and max over last observations.
        """
        obs_list, total_reward = ([], 0.0)
        new_step_api = False
        for _ in range(self._skip):
            step_result = self.env.step(action)
            if len(step_result) == 4:
                obs, reward, done, info = step_result
            else:
                obs, reward, term, trunc, info = step_result
                done = term or trunc
                new_step_api = True
            obs_list.append(obs)
            total_reward += reward
            if done:
                break
        max_frame = np.max(obs_list[-2:], axis=0)
        if new_step_api:
            return (max_frame, total_reward, term, trunc, info)
        return (max_frame, total_reward, done, info)

def step(self, action):
    """Step the environment with the given action.

        Repeat action, sum reward, and max over last observations.
        """
    obs_list, total_reward = ([], 0.0)
    new_step_api = False
    for _ in range(self._skip):
        step_result = self.env.step(action)
        if len(step_result) == 4:
            obs, reward, done, info = step_result
        else:
            obs, reward, term, trunc, info = step_result
            done = term or trunc
            new_step_api = True
        obs_list.append(obs)
        total_reward += reward
        if done:
            break
    max_frame = np.max(obs_list[-2:], axis=0)
    if new_step_api:
        return (max_frame, total_reward, term, trunc, info)
    return (max_frame, total_reward, done, info)

class EpisodicLifeEnv(gym.Wrapper):
    """Make end-of-life == end-of-episode, but only reset on true game over.

    It helps the value estimation.

    :param gym.Env env: the environment to wrap.
    """

    def __init__(self, env) -> None:
        super().__init__(env)
        self.lives = 0
        self.was_real_done = True
        self._return_info = False

    def step(self, action):
        step_result = self.env.step(action)
        if len(step_result) == 4:
            obs, reward, done, info = step_result
            new_step_api = False
        else:
            obs, reward, term, trunc, info = step_result
            done = term or trunc
            new_step_api = True
        self.was_real_done = done
        lives = self.env.unwrapped.ale.lives()
        if 0 < lives < self.lives:
            done = True
            term = True
        self.lives = lives
        if new_step_api:
            return (obs, reward, term, trunc, info)
        return (obs, reward, done, info)

    def reset(self, **kwargs):
        """Calls the Gym environment reset, only when lives are exhausted.

        This way all states are still reachable even though lives are episodic, and
        the learner need not know about any of this behind-the-scenes.
        """
        if self.was_real_done:
            obs, info, self._return_info = _parse_reset_result(self.env.reset(**kwargs))
        else:
            step_result = self.env.step(0)
            obs, info = (step_result[0], step_result[-1])
        self.lives = self.env.unwrapped.ale.lives()
        if self._return_info:
            return (obs, info)
        return obs

def step(self, action):
    step_result = self.env.step(action)
    if len(step_result) == 4:
        obs, reward, done, info = step_result
        new_step_api = False
    else:
        obs, reward, term, trunc, info = step_result
        done = term or trunc
        new_step_api = True
    self.was_real_done = done
    lives = self.env.unwrapped.ale.lives()
    if 0 < lives < self.lives:
        done = True
        term = True
    self.lives = lives
    if new_step_api:
        return (obs, reward, term, trunc, info)
    return (obs, reward, done, info)

def reset(self, **kwargs):
    """Calls the Gym environment reset, only when lives are exhausted.

        This way all states are still reachable even though lives are episodic, and
        the learner need not know about any of this behind-the-scenes.
        """
    if self.was_real_done:
        obs, info, self._return_info = _parse_reset_result(self.env.reset(**kwargs))
    else:
        step_result = self.env.step(0)
        obs, info = (step_result[0], step_result[-1])
    self.lives = self.env.unwrapped.ale.lives()
    if self._return_info:
        return (obs, info)
    return obs

class FireResetEnv(gym.Wrapper):
    """Take action on reset for environments that are fixed until firing.

    Related discussion: https://github.com/openai/baselines/issues/240.

    :param gym.Env env: the environment to wrap.
    """

    def __init__(self, env) -> None:
        super().__init__(env)
        assert env.unwrapped.get_action_meanings()[1] == 'FIRE'
        assert len(env.unwrapped.get_action_meanings()) >= 3

    def reset(self, **kwargs):
        _, _, return_info = _parse_reset_result(self.env.reset(**kwargs))
        obs = self.env.step(1)[0]
        return (obs, {}) if return_info else obs

def reset(self, **kwargs):
    _, _, return_info = _parse_reset_result(self.env.reset(**kwargs))
    obs = self.env.step(1)[0]
    return (obs, {}) if return_info else obs

class FrameStack(gym.Wrapper):
    """Stack n_frames last frames.

    :param gym.Env env: the environment to wrap.
    :param int n_frames: the number of frames to stack.
    """

    def __init__(self, env, n_frames) -> None:
        super().__init__(env)
        self.n_frames = n_frames
        self.frames = deque([], maxlen=n_frames)
        shape = (n_frames, *env.observation_space.shape)
        self.observation_space = gym.spaces.Box(low=np.min(env.observation_space.low), high=np.max(env.observation_space.high), shape=shape, dtype=env.observation_space.dtype)

    def reset(self, **kwargs):
        obs, info, return_info = _parse_reset_result(self.env.reset(**kwargs))
        for _ in range(self.n_frames):
            self.frames.append(obs)
        return (self._get_ob(), info) if return_info else self._get_ob()

    def step(self, action):
        step_result = self.env.step(action)
        if len(step_result) == 4:
            obs, reward, done, info = step_result
            new_step_api = False
        else:
            obs, reward, term, trunc, info = step_result
            new_step_api = True
        self.frames.append(obs)
        if new_step_api:
            return (self._get_ob(), reward, term, trunc, info)
        return (self._get_ob(), reward, done, info)

    def _get_ob(self):
        """Note that here is different from original Tianshou Wrapper"""
        return torch.tensor(np.stack(self.frames, axis=0), dtype=torch.uint8)

def reset(self, **kwargs):
    obs, info, return_info = _parse_reset_result(self.env.reset(**kwargs))
    for _ in range(self.n_frames):
        self.frames.append(obs)
    return (self._get_ob(), info) if return_info else self._get_ob()

def main():
    np.random.seed(opt.seed)
    torch.manual_seed(opt.seed)
    torch.cuda.manual_seed(opt.seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    render_mode = 'human' if opt.render else None
    eval_env = make_env_tianshou(opt.EnvName, noop_reset=opt.noop_reset, episode_life=False, clip_rewards=False, render_mode=render_mode)
    opt.action_dim = eval_env.action_space.n
    print('Algorithm:', opt.algo_name, '  Env:', opt.EnvName, '  Action_dim:', opt.action_dim, '  Seed:', opt.seed, '\n')
    if not os.path.exists('model'):
        os.mkdir('model')
    agent = DeepQ_Agent(opt)
    if opt.Loadmodel:
        agent.load(opt.ExperimentName, opt.ModelIdex)
    if opt.render:
        while True:
            score = evaluate_policy(eval_env, agent, seed=opt.seed, turns=1)
            print(opt.ExperimentName, 'seed:', opt.seed, 'score:', score)
    else:
        if opt.write:
            from torch.utils.tensorboard import SummaryWriter
            timenow = str(datetime.now())[0:-7]
            timenow = ' ' + timenow[0:13] + '_' + timenow[14:16] + '_' + timenow[-2:]
            writepath = f'runs/{opt.ExperimentName}_S{opt.seed}' + timenow
            if os.path.exists(writepath):
                shutil.rmtree(writepath)
            writer = SummaryWriter(log_dir=writepath)
        buffer = ReplayBuffer_torch(device=opt.dvc, max_size=opt.buffersize)
        env = make_env_tianshou(opt.EnvName, noop_reset=opt.noop_reset)
        schedualer = LinearSchedule(schedule_timesteps=opt.anneal_frac, final_p=opt.final_e, initial_p=opt.init_e)
        agent.exp_noise = opt.init_e
        seed = opt.seed
        total_steps = 0
        while total_steps < opt.Max_train_steps:
            s, info = env.reset(seed=seed)
            seed += 1
            done = False
            while not done:
                a = agent.select_action(s, evaluate=False)
                s_next, r, dw, tr, info = env.step(a)
                buffer.add(s, a, r, s_next, dw)
                done = dw + tr
                s = s_next
                if buffer.size >= opt.random_steps:
                    agent.train(buffer)
                    'record & log'
                    if total_steps % opt.eval_interval == 0:
                        score = evaluate_policy(eval_env, agent, seed=seed + 1)
                        if opt.write:
                            writer.add_scalar('ep_r', score, global_step=total_steps)
                            writer.add_scalar('noise', agent.exp_noise, global_step=total_steps)
                        print(f'{opt.ExperimentName}, Seed:{opt.seed}, Step:{int(total_steps / 1000)}k, Score:{score}')
                        agent.exp_noise = schedualer.value(total_steps)
                    total_steps += 1
                    'save model'
                    if total_steps % opt.save_interval == 0:
                        agent.save(opt.ExperimentName, int(total_steps / 1000))
    env.close()
    eval_env.close()

def evaluate_policy(env, agent, turns=3):
    total_scores = 0
    for j in range(turns):
        s, info = env.reset()
        done = False
        while not done:
            a = agent.select_action(s, deterministic=True)
            s_next, r, dw, tr, info = env.step(a)
            done = dw or tr
            total_scores += r
            s = s_next
    return int(total_scores / turns)

def main():
    EnvName = ['CartPole-v1', 'LunarLander-v2']
    BriefEnvName = ['CPV1', 'LLdV2']
    env = gym.make(EnvName[opt.EnvIdex], render_mode='human' if opt.render else None)
    eval_env = gym.make(EnvName[opt.EnvIdex])
    opt.state_dim = env.observation_space.shape[0]
    opt.action_dim = env.action_space.n
    opt.max_e_steps = env._max_episode_steps
    env_seed = opt.seed
    torch.manual_seed(opt.seed)
    torch.cuda.manual_seed(opt.seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    print('Random Seed: {}'.format(opt.seed))
    print('Algorithm: SACD', '  Env:', BriefEnvName[opt.EnvIdex], '  state_dim:', opt.state_dim, '  action_dim:', opt.action_dim, '  Random Seed:', opt.seed, '  max_e_steps:', opt.max_e_steps, '\n')
    if opt.write:
        from torch.utils.tensorboard import SummaryWriter
        timenow = str(datetime.now())[0:-10]
        timenow = ' ' + timenow[0:13] + '_' + timenow[-2:]
        writepath = 'runs/SACD_{}'.format(BriefEnvName[opt.EnvIdex]) + timenow
        if os.path.exists(writepath):
            shutil.rmtree(writepath)
        writer = SummaryWriter(log_dir=writepath)
    if not os.path.exists('model'):
        os.mkdir('model')
    agent = SACD_agent(**vars(opt))
    if opt.Loadmodel:
        agent.load(opt.ModelIdex, BriefEnvName[opt.EnvIdex])
    if opt.render:
        while True:
            score = evaluate_policy(env, agent, 1)
            print('EnvName:', BriefEnvName[opt.EnvIdex], 'seed:', opt.seed, 'score:', score)
    else:
        total_steps = 0
        while total_steps < opt.Max_train_steps:
            s, info = env.reset(seed=env_seed)
            env_seed += 1
            done = False
            'Interact & trian'
            while not done:
                if total_steps < opt.random_steps:
                    a = env.action_space.sample()
                else:
                    a = agent.select_action(s, deterministic=False)
                s_next, r, dw, tr, info = env.step(a)
                done = dw or tr
                if opt.EnvIdex == 1:
                    if r <= -100:
                        r = -10
                agent.replay_buffer.add(s, a, r, s_next, dw)
                s = s_next
                'update if its time'
                if total_steps >= opt.random_steps and total_steps % opt.update_every == 0:
                    for j in range(opt.update_every):
                        agent.train()
                'record & log'
                if total_steps % opt.eval_interval == 0:
                    score = evaluate_policy(eval_env, agent, turns=3)
                    if opt.write:
                        writer.add_scalar('ep_r', score, global_step=total_steps)
                        writer.add_scalar('alpha', agent.alpha, global_step=total_steps)
                        writer.add_scalar('H_mean', agent.H_mean, global_step=total_steps)
                    print('EnvName:', BriefEnvName[opt.EnvIdex], 'seed:', opt.seed, 'steps: {}k'.format(int(total_steps / 1000)), 'score:', int(score))
                total_steps += 1
                'save model'
                if total_steps % opt.save_interval == 0:
                    agent.save(int(total_steps / 1000), BriefEnvName[opt.EnvIdex])
    env.close()
    eval_env.close()

def evaluate_policy(env, agent, turns=3):
    total_scores = 0
    for j in range(turns):
        s, info = env.reset()
        done = False
        while not done:
            a = agent.select_action(s, deterministic=True)
            s_next, r, dw, tr, info = env.step(a)
            done = dw or tr
            total_scores += r
            s = s_next
    return int(total_scores / turns)

def main():
    EnvName = ['Pendulum-v1', 'LunarLanderContinuous-v2', 'Humanoid-v4', 'HalfCheetah-v4', 'BipedalWalker-v3', 'BipedalWalkerHardcore-v3']
    BrifEnvName = ['PV1', 'LLdV2', 'Humanv4', 'HCv4', 'BWv3', 'BWHv3']
    env = gym.make(EnvName[opt.EnvIdex], render_mode='human' if opt.render else None)
    eval_env = gym.make(EnvName[opt.EnvIdex])
    opt.state_dim = env.observation_space.shape[0]
    opt.action_dim = env.action_space.shape[0]
    opt.max_action = float(env.action_space.high[0])
    opt.max_e_steps = env._max_episode_steps
    print(f'Env:{EnvName[opt.EnvIdex]}  state_dim:{opt.state_dim}  action_dim:{opt.action_dim}  max_a:{opt.max_action}  min_a:{env.action_space.low[0]}  max_e_steps:{opt.max_e_steps}')
    env_seed = opt.seed
    np.random.seed(opt.seed)
    torch.manual_seed(opt.seed)
    torch.cuda.manual_seed(opt.seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    print('Random Seed: {}'.format(opt.seed))
    if opt.write:
        from torch.utils.tensorboard import SummaryWriter
        timenow = str(datetime.now())[0:-10]
        timenow = ' ' + timenow[0:13] + '_' + timenow[-2:]
        writepath = 'runs/{}'.format(BrifEnvName[opt.EnvIdex]) + timenow
        if os.path.exists(writepath):
            shutil.rmtree(writepath)
        writer = SummaryWriter(log_dir=writepath)
    if not os.path.exists('model'):
        os.mkdir('model')
    agent = TD3_agent(**vars(opt))
    if opt.Loadmodel:
        agent.load(BrifEnvName[opt.EnvIdex], opt.ModelIdex)
    if opt.render:
        while True:
            score = evaluate_policy(env, agent, turns=1)
            print('EnvName:', BrifEnvName[opt.EnvIdex], 'score:', score)
    else:
        total_steps = 0
        while total_steps < opt.Max_train_steps:
            s, info = env.reset(seed=env_seed)
            env_seed += 1
            done = False
            'Interact & trian'
            while not done:
                if total_steps < 10 * opt.max_e_steps:
                    a = env.action_space.sample()
                else:
                    a = agent.select_action(s, deterministic=False)
                s_next, r, dw, tr, info = env.step(a)
                r = Reward_adapter(r, opt.EnvIdex)
                done = dw or tr
                agent.replay_buffer.add(s, a, r, s_next, dw)
                s = s_next
                total_steps += 1
                'train if its time'
                if total_steps >= 2 * opt.max_e_steps and total_steps % opt.update_every == 0:
                    for j in range(opt.update_every):
                        agent.train()
                'record & log'
                if total_steps % opt.eval_interval == 0:
                    agent.explore_noise *= opt.explore_noise_decay
                    ep_r = evaluate_policy(eval_env, agent, turns=3)
                    if opt.write:
                        writer.add_scalar('ep_r', ep_r, global_step=total_steps)
                    print(f'EnvName:{BrifEnvName[opt.EnvIdex]}, Steps: {int(total_steps / 1000)}k, Episode Reward:{ep_r}')
                'save model'
                if total_steps % opt.save_interval == 0:
                    agent.save(BrifEnvName[opt.EnvIdex], int(total_steps / 1000))
        env.close()
        eval_env.close()

def evaluate_policy(env, agent, turns=3):
    total_scores = 0
    for j in range(turns):
        s, info = env.reset()
        done = False
        while not done:
            a = agent.select_action(s, deterministic=True)
            s_next, r, dw, tr, info = env.step(a)
            done = dw or tr
            total_scores += r
            s = s_next
    return int(total_scores / turns)

def main():
    EnvName = ['CartPole-v1', 'LunarLander-v2']
    BriefEnvName = ['CPV1', 'LLdV2']
    env = gym.make(EnvName[opt.EnvIdex], render_mode='human' if opt.render else None)
    eval_env = gym.make(EnvName[opt.EnvIdex])
    opt.state_dim = env.observation_space.shape[0]
    opt.action_dim = env.action_space.n
    opt.max_e_steps = env._max_episode_steps
    if opt.Duel:
        algo_name = 'Duel'
    else:
        algo_name = ''
    if opt.Double:
        algo_name += 'DDQN'
    else:
        algo_name += 'DQN'
    env_seed = opt.seed
    torch.manual_seed(opt.seed)
    torch.cuda.manual_seed(opt.seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    print('Random Seed: {}'.format(opt.seed))
    print('Algorithm:', algo_name, '  Env:', BriefEnvName[opt.EnvIdex], '  state_dim:', opt.state_dim, '  action_dim:', opt.action_dim, '  Random Seed:', opt.seed, '  max_e_steps:', opt.max_e_steps, '\n')
    if opt.write:
        from torch.utils.tensorboard import SummaryWriter
        timenow = str(datetime.now())[0:-10]
        timenow = ' ' + timenow[0:13] + '_' + timenow[-2:]
        writepath = 'runs/{}-{}_S{}_'.format(algo_name, BriefEnvName[opt.EnvIdex], opt.seed) + timenow
        if os.path.exists(writepath):
            shutil.rmtree(writepath)
        writer = SummaryWriter(log_dir=writepath)
    if not os.path.exists('model'):
        os.mkdir('model')
    agent = DQN_agent(**vars(opt))
    if opt.Loadmodel:
        agent.load(algo_name, BriefEnvName[opt.EnvIdex], opt.ModelIdex)
    if opt.render:
        while True:
            score = evaluate_policy(env, agent, 1)
            print('EnvName:', BriefEnvName[opt.EnvIdex], 'seed:', opt.seed, 'score:', score)
    else:
        total_steps = 0
        while total_steps < opt.Max_train_steps:
            s, info = env.reset(seed=env_seed)
            env_seed += 1
            done = False
            'Interact & trian'
            while not done:
                if total_steps < opt.random_steps:
                    a = env.action_space.sample()
                else:
                    a = agent.select_action(s, deterministic=False)
                s_next, r, dw, tr, info = env.step(a)
                done = dw or tr
                agent.replay_buffer.add(s, a, r, s_next, dw)
                s = s_next
                'Update'
                if total_steps >= opt.random_steps and total_steps % opt.update_every == 0:
                    for j in range(opt.update_every):
                        agent.train()
                'Noise decay & Record & Log'
                if total_steps % 1000 == 0:
                    agent.exp_noise *= opt.noise_decay
                if total_steps % opt.eval_interval == 0:
                    score = evaluate_policy(eval_env, agent, turns=3)
                    if opt.write:
                        writer.add_scalar('ep_r', score, global_step=total_steps)
                        writer.add_scalar('noise', agent.exp_noise, global_step=total_steps)
                    print('EnvName:', BriefEnvName[opt.EnvIdex], 'seed:', opt.seed, 'steps: {}k'.format(int(total_steps / 1000)), 'score:', int(score))
                total_steps += 1
                'save model'
                if total_steps % opt.save_interval == 0:
                    agent.save(algo_name, BriefEnvName[opt.EnvIdex], int(total_steps / 1000))
    env.close()
    eval_env.close()

def main():
    write = True
    Loadmodel = False
    Max_train_steps = 20000
    seed = 0
    np.random.seed(seed)
    print(f'Random Seed: {seed}')
    ' ↓↓↓ Build Env ↓↓↓ '
    EnvName = 'CliffWalking-v0'
    env = gym.make(EnvName)
    env = TimeLimit(env, max_episode_steps=500)
    eval_env = gym.make(EnvName)
    eval_env = TimeLimit(eval_env, max_episode_steps=100)
    ' ↓↓↓ Use tensorboard to record training curves ↓↓↓ '
    if write:
        timenow = str(datetime.now())[0:-7]
        timenow = ' ' + timenow[0:13] + '_' + timenow[14:16] + '_' + timenow[-2:]
        writepath = 'runs/{}'.format(EnvName) + timenow
        if os.path.exists(writepath):
            shutil.rmtree(writepath)
        writer = SummaryWriter(log_dir=writepath)
    ' ↓↓↓ Build Q-learning Agent ↓↓↓ '
    if not os.path.exists('model'):
        os.mkdir('model')
    agent = QLearningAgent(s_dim=env.observation_space.n, a_dim=env.action_space.n, lr=0.2, gamma=0.9, exp_noise=0.1)
    if Loadmodel:
        agent.restore()
    ' ↓↓↓ Iterate and Train ↓↓↓ '
    total_steps = 0
    while total_steps < Max_train_steps:
        s, info = env.reset(seed=seed)
        seed += 1
        done, steps = (False, 0)
        while not done:
            steps += 1
            a = agent.select_action(s, deterministic=False)
            s_next, r, dw, tr, info = env.step(a)
            agent.train(s, a, r, s_next, dw)
            done = dw or tr
            s = s_next
            total_steps += 1
            'record & log'
            if total_steps % 100 == 0:
                ep_r = evaluate_policy(eval_env, agent)
                if write:
                    writer.add_scalar('ep_r', ep_r, global_step=total_steps)
                print(f'EnvName:{EnvName}, Seed:{seed}, Steps:{total_steps}, Episode reward:{ep_r}')
            'save model'
            if total_steps % Max_train_steps == 0:
                agent.save()
    env.close()
    eval_env.close()

def evaluate_policy(env, agent):
    s, info = env.reset()
    done, ep_r, steps = (False, 0, 0)
    while not done:
        a = agent.select_action(s, deterministic=True)
        s_next, r, dw, tr, info = env.step(a)
        done = dw or tr
        ep_r += r
        steps += 1
        s = s_next
    return ep_r

class Recorder:
    """Because the running curve written by evaluator can be unsorted,
	we use a Recorder process to sort the running curve point and record it with tensorboard"""

    def __init__(self, opt, shared_data):
        self.shared_data = shared_data
        self.writer = SummaryWriter(log_dir=opt.writepath)

    def run(self):
        while True:
            time.sleep(60)
            curve = self.shared_data.get_curve()
            if len(curve) == 0:
                pass
            else:
                curve = torch.tensor(curve)
                score, steps, walltime = (curve[:, 0], curve[:, 1], curve[:, 2])
                steps, sort_ind = torch.sort(steps)
                score = score[sort_ind]
                walltime = walltime[sort_ind]
                for _ in range(len(curve)):
                    self.writer.add_scalar('ep_r', score[_], steps[_], walltime[_])

def __init__(self, opt, shared_data):
    self.shared_data = shared_data
    self.writer = SummaryWriter(log_dir=opt.writepath)

class Learner:

    def __init__(self, opt, shared_data):
        self.shared_data = shared_data
        self.device = torch.device(opt.L_dvc)
        self.max_train_steps = opt.max_train_steps
        self.explore_steps = opt.explore_steps
        self.lr = opt.lr
        self.gamma = opt.gamma
        self.DDQN = opt.DDQN
        self.hard_update_freq = opt.hard_update_freq
        self.upload_freq = opt.upload_freq
        self.eval_freq = opt.eval_freq
        self.train_counter = 0
        self.batch_size = opt.batch_size
        self.q_net = Q_Net(opt.action_dim, opt.fc_width).to(self.device)
        self.upload_model()
        self.q_target = copy.deepcopy(self.q_net)
        for p in self.q_target.parameters():
            p.requires_grad = False
        self.q_net_optimizer = torch.optim.Adam(self.q_net.parameters(), lr=opt.lr, eps=0.00015)
        self.lr_scheduler = LinearSchedule(15000000.0, opt.lr, opt.lr / 3)
        self.time_feedback = opt.time_feedback
        self.rho = opt.train_envs * opt.TPS / opt.batch_size

    def run(self):
        mean_t = 0
        while True:
            global_steps = self.shared_data.get_total_steps()
            if global_steps > self.max_train_steps:
                break
            if global_steps < self.explore_steps:
                time.sleep(0.1)
            else:
                t0 = time.time()
                self.train()
                self.train_counter += 1
                if self.train_counter % self.upload_freq == 0:
                    self.upload_model()
                    self.shared_data.set_should_download(True)
                if self.train_counter % self.hard_update_freq == 0:
                    self.hard_target_update()
                    self.lr_decay(global_steps)
                    print('(Learner) Actual TPS: ', self.train_counter * self.batch_size / (global_steps - self.explore_steps))
                if self.train_counter % self.eval_freq == 0:
                    self.shared_data.add_eval_model(deepcopy(self.q_net).cpu().state_dict(), global_steps - self.explore_steps, time.time())
                if self.time_feedback:
                    current_t = time.time() - t0
                    mean_t = mean_t + (current_t - mean_t) / self.train_counter
                    scalled_learner_time = self.rho * mean_t
                    self.shared_data.set_t(scalled_learner_time, 1)
                    t = self.shared_data.get_t()
                    if t[1] < t[0]:
                        hold_time = (t[0] - t[1]) / self.rho
                        if hold_time > 1:
                            hold_time = 1
                        time.sleep(hold_time)

    def train(self):
        s, a, r, s_next, dw, ct = self.shared_data.sample()
        'Compute target Q value'
        with torch.no_grad():
            if self.DDQN:
                argmax_a = self.q_net(s_next).argmax(dim=-1).unsqueeze(-1)
                max_q_next = self.q_target(s_next).gather(1, argmax_a)
            else:
                max_q_next = self.q_target(s_next).max(1)[0].unsqueeze(1)
            target_Q = r + ~dw * self.gamma * max_q_next
        'Collect Current Q value'
        current_q = self.q_net(s)
        current_q_a = current_q.gather(1, a)
        if ct.all():
            q_loss = F.mse_loss(current_q_a, target_Q)
        else:
            q_loss = torch.square(ct * (current_q_a - target_Q)).mean()
        self.q_net_optimizer.zero_grad()
        q_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.q_net.parameters(), 40)
        self.q_net_optimizer.step()

    def upload_model(self):
        self.shared_data.set_net_param(deepcopy(self.q_net).cpu().state_dict())

    def hard_target_update(self):
        for param, target_param in zip(self.q_net.parameters(), self.q_target.parameters()):
            target_param.data.copy_(param.data)
            target_param.requires_grad = False

    def lr_decay(self, global_step):
        for p in self.q_net_optimizer.param_groups:
            p['lr'] = self.lr_scheduler.value(global_step)

def lr_decay(self, global_step):
    for p in self.q_net_optimizer.param_groups:
        p['lr'] = self.lr_scheduler.value(global_step)

class Evaluator:

    def __init__(self, eid, opt, shared_data):
        self.eid = eid
        self.shared_data = shared_data
        self.device = torch.device(opt.E_dvc)
        self.envname = opt.ExpEnvName
        self.eval_envs = opt.eval_envs
        self.max_train_steps = opt.max_train_steps
        self.eval_net = Q_Net(opt.action_dim, opt.fc_width).to(self.device)
        self.envs = envpool.make_gym(self.envname, num_envs=opt.eval_envs, seed=opt.seed + 1, max_episode_steps=int(108000.0 / 4), episodic_life=False, reward_clip=False)

    def run(self):
        while True:
            data = self.shared_data.get_eval_model()
            global_steps = self.shared_data.get_total_steps()
            if global_steps > self.max_train_steps and data is None:
                break
            if data is None:
                time.sleep(5)
            else:
                self.eval_net.load_state_dict(data['model'])
                for eval_param in self.eval_net.parameters():
                    eval_param.requires_grad = False
                score = self.evaluate()
                self.shared_data.add_curvepoint([score, data['steps'], data['time']])
                print('(Evaluator {}) '.format(self.eid), self.envname, '  Tstep:{}k'.format(round(data['steps'] / 1000, 2)), '  score:', score)

    def evaluate(self):
        s, info = self.envs.reset()
        dones, total_r = (np.zeros(self.eval_envs, dtype=np.bool_), 0)
        while not dones.all():
            a = self.select_action(s)
            s, r, dw, tr, info = self.envs.step(a)
            total_r += (~dones * r).sum()
            dones += dw + tr
        return round(total_r / self.eval_envs, 1)

    def select_action(self, s):
        """for envpool"""
        with torch.no_grad():
            s = torch.from_numpy(s).to(self.device)
            return self.eval_net(s).argmax(dim=-1).cpu().numpy()

def evaluate(self):
    s, info = self.envs.reset()
    dones, total_r = (np.zeros(self.eval_envs, dtype=np.bool_), 0)
    while not dones.all():
        a = self.select_action(s)
        s, r, dw, tr, info = self.envs.step(a)
        total_r += (~dones * r).sum()
        dones += dw + tr
    return round(total_r / self.eval_envs, 1)

def evaluate_policy(env, agent, turns=3):
    agent.q_net.eval()
    total_scores = 0
    for j in range(turns):
        s, info = env.reset()
        done = False
        while not done:
            a = agent.select_action(s)
            s_next, r, dw, tr, info = env.step(a)
            done = dw or tr
            total_scores += r
            s = s_next
    agent.q_net.train()
    return int(total_scores / turns)

def main():
    EnvName = ['CartPole-v1', 'LunarLander-v2']
    BriefEnvName = ['CPV1', 'LLdV2']
    env = gym.make(EnvName[opt.EnvIdex], render_mode='human' if opt.render else None)
    eval_env = gym.make(EnvName[opt.EnvIdex])
    opt.state_dim = env.observation_space.shape[0]
    opt.action_dim = env.action_space.n
    opt.max_e_steps = env._max_episode_steps
    algo_name = 'NoisyNetDQN'
    env_seed = opt.seed
    torch.manual_seed(opt.seed)
    torch.cuda.manual_seed(opt.seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    print('Random Seed: {}'.format(opt.seed))
    print('Algorithm:', algo_name, '  Env:', BriefEnvName[opt.EnvIdex], '  state_dim:', opt.state_dim, '  action_dim:', opt.action_dim, '  Random Seed:', opt.seed, '  max_e_steps:', opt.max_e_steps, '\n')
    if opt.write:
        from torch.utils.tensorboard import SummaryWriter
        timenow = str(datetime.now())[0:-10]
        timenow = ' ' + timenow[0:13] + '_' + timenow[-2:]
        writepath = 'runs/{}-{}_S{}_'.format(algo_name, BriefEnvName[opt.EnvIdex], opt.seed) + timenow
        if os.path.exists(writepath):
            shutil.rmtree(writepath)
        writer = SummaryWriter(log_dir=writepath)
    if not os.path.exists('model'):
        os.mkdir('model')
    agent = NoisyNetDQN_agent(**vars(opt))
    if opt.Loadmodel:
        agent.load(algo_name, BriefEnvName[opt.EnvIdex], opt.ModelIdex)
    if opt.render:
        while True:
            score = evaluate_policy(env, agent, 1)
            print('EnvName:', BriefEnvName[opt.EnvIdex], 'seed:', opt.seed, 'score:', score)
    else:
        total_steps = 0
        while total_steps < opt.Max_train_steps:
            s, info = env.reset(seed=env_seed)
            env_seed += 1
            done = False
            'Interact & trian'
            while not done:
                if total_steps < opt.random_steps:
                    a = env.action_space.sample()
                else:
                    a = agent.select_action(s)
                s_next, r, dw, tr, info = env.step(a)
                done = dw or tr
                agent.replay_buffer.add(s, a, r, s_next, dw)
                s = s_next
                'Update'
                if total_steps >= opt.random_steps and total_steps % opt.update_every == 0:
                    for j in range(opt.update_every):
                        agent.train()
                'Record & Log'
                if total_steps % opt.eval_interval == 0:
                    score = evaluate_policy(eval_env, agent, turns=3)
                    if opt.write:
                        writer.add_scalar('ep_r', score, global_step=total_steps)
                    print('EnvName:', BriefEnvName[opt.EnvIdex], 'seed:', opt.seed, 'steps: {}k'.format(int(total_steps / 1000)), 'score:', int(score))
                total_steps += 1
                'Save model'
                if total_steps % opt.save_interval == 0:
                    agent.save(algo_name, BriefEnvName[opt.EnvIdex], int(total_steps / 1000))
    env.close()
    eval_env.close()

def evaluate_policy(env, agent, max_action, turns):
    total_scores = 0
    for j in range(turns):
        s, info = env.reset()
        done = False
        while not done:
            a, logprob_a = agent.select_action(s, deterministic=True)
            act = Action_adapter(a, max_action)
            s_next, r, dw, tr, info = env.step(act)
            done = dw or tr
            total_scores += r
            s = s_next
    return total_scores / turns

def main():
    EnvName = ['Pendulum-v1', 'LunarLanderContinuous-v2', 'Humanoid-v4', 'HalfCheetah-v4', 'BipedalWalker-v3', 'BipedalWalkerHardcore-v3']
    BrifEnvName = ['PV1', 'LLdV2', 'Humanv4', 'HCv4', 'BWv3', 'BWHv3']
    env = gym.make(EnvName[opt.EnvIdex], render_mode='human' if opt.render else None)
    eval_env = gym.make(EnvName[opt.EnvIdex])
    opt.state_dim = env.observation_space.shape[0]
    opt.action_dim = env.action_space.shape[0]
    opt.max_action = float(env.action_space.high[0])
    opt.max_steps = env._max_episode_steps
    print('Env:', EnvName[opt.EnvIdex], '  state_dim:', opt.state_dim, '  action_dim:', opt.action_dim, '  max_a:', opt.max_action, '  min_a:', env.action_space.low[0], 'max_steps', opt.max_steps)
    env_seed = opt.seed
    torch.manual_seed(opt.seed)
    torch.cuda.manual_seed(opt.seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    print('Random Seed: {}'.format(opt.seed))
    if opt.write:
        from torch.utils.tensorboard import SummaryWriter
        timenow = str(datetime.now())[0:-10]
        timenow = ' ' + timenow[0:13] + '_' + timenow[-2:]
        writepath = 'runs/{}'.format(BrifEnvName[opt.EnvIdex]) + timenow
        if os.path.exists(writepath):
            shutil.rmtree(writepath)
        writer = SummaryWriter(log_dir=writepath)
    if not os.path.exists('model'):
        os.mkdir('model')
    agent = PPO_agent(**vars(opt))
    if opt.Loadmodel:
        agent.load(BrifEnvName[opt.EnvIdex], opt.ModelIdex)
    if opt.render:
        while True:
            ep_r = evaluate_policy(env, agent, opt.max_action, 1)
            print(f'Env:{EnvName[opt.EnvIdex]}, Episode Reward:{ep_r}')
    else:
        traj_lenth, total_steps = (0, 0)
        while total_steps < opt.Max_train_steps:
            s, info = env.reset(seed=env_seed)
            env_seed += 1
            done = False
            'Interact & trian'
            while not done:
                'Interact with Env'
                a, logprob_a = agent.select_action(s, deterministic=False)
                act = Action_adapter(a, opt.max_action)
                s_next, r, dw, tr, info = env.step(act)
                r = Reward_adapter(r, opt.EnvIdex)
                done = dw or tr
                'Store the current transition'
                agent.put_data(s, a, r, s_next, logprob_a, done, dw, idx=traj_lenth)
                s = s_next
                traj_lenth += 1
                total_steps += 1
                'Update if its time'
                if traj_lenth % opt.T_horizon == 0:
                    agent.train()
                    traj_lenth = 0
                'Record & log'
                if total_steps % opt.eval_interval == 0:
                    score = evaluate_policy(eval_env, agent, opt.max_action, turns=3)
                    if opt.write:
                        writer.add_scalar('ep_r', score, global_step=total_steps)
                    print('EnvName:', EnvName[opt.EnvIdex], 'seed:', opt.seed, 'steps: {}k'.format(int(total_steps / 1000)), 'score:', score)
                'Save model'
                if total_steps % opt.save_interval == 0:
                    agent.save(BrifEnvName[opt.EnvIdex], int(total_steps / 1000))
        env.close()
        eval_env.close()

def evaluate_policy(env, agent, turns=3):
    total_scores = 0
    for j in range(turns):
        s, info = env.reset()
        done = False
        while not done:
            a, logprob_a = agent.select_action(s, deterministic=True)
            s_next, r, dw, tr, info = env.step(a)
            done = dw or tr
            total_scores += r
            s = s_next
    return int(total_scores / turns)

def main():
    EnvName = ['CartPole-v1', 'LunarLander-v2']
    BriefEnvName = ['CP-v1', 'LLd-v2']
    env = gym.make(EnvName[opt.EnvIdex], render_mode='human' if opt.render else None)
    eval_env = gym.make(EnvName[opt.EnvIdex])
    opt.state_dim = env.observation_space.shape[0]
    opt.action_dim = env.action_space.n
    opt.max_e_steps = env._max_episode_steps
    env_seed = opt.seed
    torch.manual_seed(opt.seed)
    torch.cuda.manual_seed(opt.seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    print('Random Seed: {}'.format(opt.seed))
    print('Env:', BriefEnvName[opt.EnvIdex], '  state_dim:', opt.state_dim, '  action_dim:', opt.action_dim, '   Random Seed:', opt.seed, '  max_e_steps:', opt.max_e_steps)
    print('\n')
    if opt.write:
        from torch.utils.tensorboard import SummaryWriter
        timenow = str(datetime.now())[0:-10]
        timenow = ' ' + timenow[0:13] + '_' + timenow[-2:]
        writepath = 'runs/{}'.format(BriefEnvName[opt.EnvIdex]) + timenow
        if os.path.exists(writepath):
            shutil.rmtree(writepath)
        writer = SummaryWriter(log_dir=writepath)
    if not os.path.exists('model'):
        os.mkdir('model')
    agent = PPO_discrete(**vars(opt))
    if opt.Loadmodel:
        agent.load(opt.ModelIdex)
    if opt.render:
        while True:
            ep_r = evaluate_policy(env, agent, turns=1)
            print(f'Env:{EnvName[opt.EnvIdex]}, Episode Reward:{ep_r}')
    else:
        traj_lenth, total_steps = (0, 0)
        while total_steps < opt.Max_train_steps:
            s, info = env.reset(seed=env_seed)
            env_seed += 1
            done = False
            'Interact & trian'
            while not done:
                'Interact with Env'
                a, logprob_a = agent.select_action(s, deterministic=False)
                s_next, r, dw, tr, info = env.step(a)
                if r <= -100:
                    r = -30
                done = dw or tr
                'Store the current transition'
                agent.put_data(s, a, r, s_next, logprob_a, done, dw, idx=traj_lenth)
                s = s_next
                traj_lenth += 1
                total_steps += 1
                'Update if its time'
                if traj_lenth % opt.T_horizon == 0:
                    agent.train()
                    traj_lenth = 0
                'Record & log'
                if total_steps % opt.eval_interval == 0:
                    score = evaluate_policy(eval_env, agent, turns=3)
                    if opt.write:
                        writer.add_scalar('ep_r', score, global_step=total_steps)
                    print('EnvName:', EnvName[opt.EnvIdex], 'seed:', opt.seed, 'steps: {}k'.format(int(total_steps / 1000)), 'score:', score)
                'Save model'
                if total_steps % opt.save_interval == 0:
                    agent.save(total_steps)
        env.close()
        eval_env.close()

def evaluate_policy(env, agent, turns=3):
    total_scores = 0
    for j in range(turns):
        s, info = env.reset()
        done = False
        while not done:
            a = agent.select_action(s, deterministic=True)
            s_next, r, dw, tr, info = env.step(a)
            done = dw or tr
            total_scores += r
            s = s_next
    return int(total_scores / turns)

def main():
    EnvName = ['CartPole-v1', 'LunarLander-v2']
    BriefEnvName = ['CPV1', 'LLdV2']
    env = gym.make(EnvName[opt.EnvIdex], render_mode='human' if opt.render else None)
    eval_env = gym.make(EnvName[opt.EnvIdex])
    opt.state_dim = env.observation_space.shape[0]
    opt.action_dim = env.action_space.n
    opt.max_e_steps = env._max_episode_steps
    opt.action_info = {0: ['Left', 'Right'], 1: ['Noop', 'LeftEngine', 'MainEngine', 'RightEngine']}
    algo_name = 'C51_' + 'DDQN' if opt.DQL else 'DQN'
    env_seed = opt.seed
    torch.manual_seed(opt.seed)
    torch.cuda.manual_seed(opt.seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    print('Random Seed: {}'.format(opt.seed))
    print('Algorithm:', algo_name, '  Env:', BriefEnvName[opt.EnvIdex], '  state_dim:', opt.state_dim, '  action_dim:', opt.action_dim, '  Random Seed:', opt.seed, '  max_e_steps:', opt.max_e_steps, '\n')
    if opt.write:
        from torch.utils.tensorboard import SummaryWriter
        timenow = str(datetime.now())[0:-10]
        timenow = ' ' + timenow[0:13] + '_' + timenow[-2:]
        writepath = 'runs/{}_{}'.format(algo_name, BriefEnvName[opt.EnvIdex]) + timenow
        if os.path.exists(writepath):
            shutil.rmtree(writepath)
        writer = SummaryWriter(log_dir=writepath)
    if not os.path.exists('model'):
        os.mkdir('model')
    agent = CDQN_agent(**vars(opt))
    if opt.Loadmodel:
        agent.load(algo_name, BriefEnvName[opt.EnvIdex], opt.ModelIdex)
    if opt.render:
        render_policy(env, agent, opt)
    else:
        total_steps = 0
        while total_steps < opt.Max_train_steps:
            s, info = env.reset(seed=env_seed)
            env_seed += 1
            done = False
            'Interact & trian'
            while not done:
                if total_steps < opt.random_steps:
                    a = env.action_space.sample()
                else:
                    a = agent.select_action(s, deterministic=False)
                s_next, r, dw, tr, info = env.step(a)
                done = dw or tr
                agent.replay_buffer.add(s, a, r, s_next, dw)
                s = s_next
                'update if its time'
                if total_steps >= opt.random_steps and total_steps % opt.update_every == 0:
                    for j in range(opt.update_every):
                        agent.train()
                'record & log'
                if total_steps % opt.eval_interval == 0:
                    agent.exp_noise *= opt.noise_decay
                    score = evaluate_policy(eval_env, agent, turns=3)
                    if opt.write:
                        writer.add_scalar('ep_r', score, global_step=total_steps)
                        writer.add_scalar('noise', agent.exp_noise, global_step=total_steps)
                    print('EnvName:', BriefEnvName[opt.EnvIdex], 'seed:', opt.seed, 'steps: {}k'.format(int(total_steps / 1000)), 'score:', int(score))
                total_steps += 1
                'save model'
                if total_steps % opt.save_interval == 0:
                    agent.save(algo_name, BriefEnvName[opt.EnvIdex], int(total_steps / 1000))
    env.close()
    eval_env.close()

def evaluate_policy(env, max_action, agent, turns=3):
    total_scores = 0
    for j in range(turns):
        s, info = env.reset()
        done = False
        while not done:
            a = agent.select_action(s, deterministic=True)
            act = Action_adapter(a, max_action)
            s_next, r, dw, tr, info = env.step(act)
            done = dw or tr
            total_scores += r
            s = s_next
    return int(total_scores / turns)

def main():
    EnvName = ['Pendulum-v1', 'LunarLanderContinuous-v2', 'Humanoid-v4', 'HalfCheetah-v4', 'BipedalWalker-v3', 'BipedalWalkerHardcore-v3']
    BrifEnvName = ['PV1', 'LLdV2', 'Humanv4', 'HCv4', 'BWv3', 'BWHv3']
    env = gym.make(EnvName[opt.EnvIdex], render_mode='human' if opt.render else None)
    eval_env = gym.make(EnvName[opt.EnvIdex])
    opt.state_dim = env.observation_space.shape[0]
    opt.action_dim = env.action_space.shape[0]
    opt.max_action = float(env.action_space.high[0])
    opt.max_e_steps = env._max_episode_steps
    print(f'Env:{EnvName[opt.EnvIdex]}  state_dim:{opt.state_dim}  action_dim:{opt.action_dim}  max_a:{opt.max_action}  min_a:{env.action_space.low[0]}  max_e_steps:{opt.max_e_steps}')
    env_seed = opt.seed
    torch.manual_seed(opt.seed)
    torch.cuda.manual_seed(opt.seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    print('Random Seed: {}'.format(opt.seed))
    if opt.write:
        from torch.utils.tensorboard import SummaryWriter
        timenow = str(datetime.now())[0:-10]
        timenow = ' ' + timenow[0:13] + '_' + timenow[-2:]
        writepath = 'runs/{}'.format(BrifEnvName[opt.EnvIdex]) + timenow
        if os.path.exists(writepath):
            shutil.rmtree(writepath)
        writer = SummaryWriter(log_dir=writepath)
    if not os.path.exists('model'):
        os.mkdir('model')
    agent = SAC_countinuous(**vars(opt))
    if opt.Loadmodel:
        agent.load(BrifEnvName[opt.EnvIdex], opt.ModelIdex)
    if opt.render:
        while True:
            score = evaluate_policy(env, opt.max_action, agent, turns=1)
            print('EnvName:', BrifEnvName[opt.EnvIdex], 'score:', score)
    else:
        total_steps = 0
        while total_steps < opt.Max_train_steps:
            s, info = env.reset(seed=env_seed)
            env_seed += 1
            done = False
            'Interact & trian'
            while not done:
                if total_steps < 5 * opt.max_e_steps:
                    act = env.action_space.sample()
                    a = Action_adapter_reverse(act, opt.max_action)
                else:
                    a = agent.select_action(s, deterministic=False)
                    act = Action_adapter(a, opt.max_action)
                s_next, r, dw, tr, info = env.step(act)
                r = Reward_adapter(r, opt.EnvIdex)
                done = dw or tr
                agent.replay_buffer.add(s, a, r, s_next, dw)
                s = s_next
                total_steps += 1
                "train if it's time"
                if total_steps >= 2 * opt.max_e_steps and total_steps % opt.update_every == 0:
                    for j in range(opt.update_every):
                        agent.train()
                'record & log'
                if total_steps % opt.eval_interval == 0:
                    ep_r = evaluate_policy(eval_env, opt.max_action, agent, turns=3)
                    if opt.write:
                        writer.add_scalar('ep_r', ep_r, global_step=total_steps)
                    print(f'EnvName:{BrifEnvName[opt.EnvIdex]}, Steps: {int(total_steps / 1000)}k, Episode Reward:{ep_r}')
                'save model'
                if total_steps % opt.save_interval == 0:
                    agent.save(BrifEnvName[opt.EnvIdex], int(total_steps / 1000))
        env.close()
        eval_env.close()

