# Cluster 23

class ObjectCountCurriculum:
    """
    Curriculum that increases the number of objects as the success rate increases.
    """
    INFO_CURRICULUM_PREFIX: str = 'curriculum/'

    def __init__(self, task: Task, success_rate_impl: SuccessRateImpl, object_count_min: int, object_count_max: int, max_object_count_success_rate_threshold: float, **kwargs):
        self.__task = task
        self.__success_rate_impl = success_rate_impl
        self.__object_count_min = object_count_min
        self.__object_count_max = object_count_max
        self.__max_object_count_success_rate_threshold = max_object_count_success_rate_threshold
        self.__object_count_min_max_diff = object_count_max - object_count_min
        if self.__object_count_min_max_diff < 0:
            raise Exception("'object_count_min' cannot be larger than 'object_count_max'")

    def get_info(self) -> Dict:
        info = {f'{self.INFO_CURRICULUM_PREFIX}object_count': self.__object_count}
        return info

    def reset_task(self):
        self.__update_object_count()

    def __update_object_count(self):
        self.__object_count = min(self.__object_count_max, math.floor(self.__object_count_min + self.__success_rate_impl.success_rate / self.__max_object_count_success_rate_threshold * self.__object_count_min_max_diff))
        self.__task.add_randomizer_parameter_overrides({'object_count': self.__object_count})

def reset_task(self):
    self.__update_object_count()

