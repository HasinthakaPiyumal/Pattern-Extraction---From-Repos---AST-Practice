# Cluster 15

def make_env_tianshou(env_name, noop_reset=True, episode_life=True, clip_rewards=True, frame_stack=4, warp_frame=True, render_mode=None):
    """Configure environment for DeepMind-style Atari.
    Support both Gymnasium(s,r,term,trunc,info) and Gym(s,r,done,info)  API
    The observation is (4, 84, 84); torch.uint8; <class 'torch.Tensor'>
    # Here we do not normalize the observation to float in (0,1). Instead, we use uint8 to save memory.
    """
    assert 'NoFrameskip' in env_name
    env = gym.make(env_name, render_mode=render_mode)
    if noop_reset:
        env = NoopResetEnv(env, noop_max=30)
    env = MaxAndSkipEnv(env, skip=4)
    if episode_life:
        env = EpisodicLifeEnv(env)
    if 'FIRE' in env.unwrapped.get_action_meanings():
        env = FireResetEnv(env)
    if warp_frame:
        env = WarpFrame(env)
    if clip_rewards:
        env = ClipRewardEnv(env)
    if frame_stack:
        env = FrameStack(env, frame_stack)
    return env

