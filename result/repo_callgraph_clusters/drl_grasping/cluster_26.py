# Cluster 26

class DoneOnSuccessWrapper(gym.Wrapper):
    """
    Reset on success and offsets the reward.
    Useful for GoalEnv.
    """

    def __init__(self, env: gym.Env, reward_offset: float=0.0, n_successes: int=1):
        super(DoneOnSuccessWrapper, self).__init__(env)
        self.reward_offset = reward_offset
        self.n_successes = n_successes
        self.current_successes = 0

    def reset(self):
        self.current_successes = 0
        return self.env.reset()

    def step(self, action):
        obs, reward, done, info = self.env.step(action)
        if info.get('is_success', False):
            self.current_successes += 1
        else:
            self.current_successes = 0
        done = done or self.current_successes >= self.n_successes
        reward += self.reward_offset
        return (obs, reward, done, info)

    def compute_reward(self, achieved_goal, desired_goal, info):
        reward = self.env.compute_reward(achieved_goal, desired_goal, info)
        return reward + self.reward_offset

def compute_reward(self, achieved_goal, desired_goal, info):
    reward = self.env.compute_reward(achieved_goal, desired_goal, info)
    return reward + self.reward_offset

