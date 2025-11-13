# Cluster 11

class Recorder:

    def __init__(self, env, directory, save_stats=True, save_video=True, save_episode=True, video_size=(512, 512)):
        if directory and save_stats:
            env = StatsRecorder(env, directory)
        if directory and save_video:
            env = VideoRecorder(env, directory, video_size)
        if directory and save_episode:
            env = EpisodeRecorder(env, directory)
        self._env = env

    def __getattr__(self, name):
        if name.startswith('__'):
            raise AttributeError(name)
        return getattr(self._env, name)

def __init__(self, env, directory, save_stats=True, save_video=True, save_episode=True, video_size=(512, 512)):
    if directory and save_stats:
        env = StatsRecorder(env, directory)
    if directory and save_video:
        env = VideoRecorder(env, directory, video_size)
    if directory and save_episode:
        env = EpisodeRecorder(env, directory)
    self._env = env

