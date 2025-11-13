# Cluster 22

class ObjectSpawnVolumeScaleCurriculum:
    """
    Curriculum that increases the object spawn volume as the success rate increases.
    """
    INFO_CURRICULUM_PREFIX: str = 'curriculum/'

    def __init__(self, task: Task, success_rate_impl: SuccessRateImpl, min_object_spawn_volume_scale: float, max_object_spawn_volume: Tuple[float, float, float], max_object_spawn_volume_scale_success_rate_threshold: float, **kwargs):
        self.__task = task
        self.__success_rate_impl = success_rate_impl
        self.__min_object_spawn_volume_scale = min_object_spawn_volume_scale
        self.__max_object_spawn_volume = max_object_spawn_volume
        self.__max_object_spawn_volume_scale_success_rate_threshold = max_object_spawn_volume_scale_success_rate_threshold

    def get_info(self) -> Dict:
        info = {f'{self.INFO_CURRICULUM_PREFIX}{INFO_MEAN_EPISODE_KEY}object_spawn_volume_scale': self.__object_spawn_volume_scale}
        return info

    def reset_task(self):
        self.__update_object_spawn_volume_size()

    def __update_object_spawn_volume_size(self):
        self.__object_spawn_volume_scale = min(1.0, max(self.__min_object_spawn_volume_scale, self.__success_rate_impl.success_rate / self.__max_object_spawn_volume_scale_success_rate_threshold))
        object_spawn_volume_volume_new = (self.__object_spawn_volume_scale * self.__max_object_spawn_volume[0], self.__object_spawn_volume_scale * self.__max_object_spawn_volume[1], self.__object_spawn_volume_scale * self.__max_object_spawn_volume[2])
        self.__task.add_randomizer_parameter_overrides({'object_random_spawn_volume': object_spawn_volume_volume_new})

def reset_task(self):
    self.__update_object_spawn_volume_size()

