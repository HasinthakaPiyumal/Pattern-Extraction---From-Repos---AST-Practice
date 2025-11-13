# Cluster 17

class WarpFrame(gym.ObservationWrapper):
    """Warp frames to 84x84 as done in the Nature paper and later work.

    :param gym.Env env: the environment to wrap.
    """

    def __init__(self, env) -> None:
        super().__init__(env)
        self.size = 84
        self.observation_space = gym.spaces.Box(low=np.min(env.observation_space.low), high=np.max(env.observation_space.high), shape=(self.size, self.size), dtype=env.observation_space.dtype)

    def observation(self, frame):
        """Returns the current observation from a frame."""
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        return cv2.resize(frame, (self.size, self.size), interpolation=cv2.INTER_AREA)

def observation(self, frame):
    """Returns the current observation from a frame."""
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    return cv2.resize(frame, (self.size, self.size), interpolation=cv2.INTER_AREA)

