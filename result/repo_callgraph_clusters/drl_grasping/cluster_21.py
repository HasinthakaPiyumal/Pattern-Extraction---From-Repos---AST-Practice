# Cluster 21

class WorkspaceScaleCurriculum:
    """
    Curriculum that increases the workspace size as the success rate increases.
    """
    INFO_CURRICULUM_PREFIX: str = 'curriculum/'

    def __init__(self, task: Task, success_rate_impl: SuccessRateImpl, min_workspace_scale: float, max_workspace_volume: Tuple[float, float, float], max_workspace_scale_success_rate_threshold: float, **kwargs):
        self.__task = task
        self.__success_rate_impl = success_rate_impl
        self.__min_workspace_scale = min_workspace_scale
        self.__max_workspace_volume = max_workspace_volume
        self.__max_workspace_scale_success_rate_threshold = max_workspace_scale_success_rate_threshold

    def get_info(self) -> Dict:
        info = {f'{self.INFO_CURRICULUM_PREFIX}{INFO_MEAN_EPISODE_KEY}workspace_scale': self.__workspace_scale}
        return info

    def reset_task(self):
        self.__update_workspace_size()

    def __update_workspace_size(self):
        self.__workspace_scale = min(1.0, max(self.__min_workspace_scale, self.__success_rate_impl.success_rate / self.__max_workspace_scale_success_rate_threshold))
        workspace_volume_new = (self.__workspace_scale * self.__max_workspace_volume[0], self.__workspace_scale * self.__max_workspace_volume[1], self.__max_workspace_volume[2])
        workspace_volume_half_new = (workspace_volume_new[0] / 2, workspace_volume_new[1] / 2, workspace_volume_new[2] / 2)
        workspace_min_bound_new = (self.__task.workspace_centre[0] - workspace_volume_half_new[0], self.__task.workspace_centre[1] - workspace_volume_half_new[1], self.__task.workspace_centre[2] - workspace_volume_half_new[2])
        workspace_max_bound_new = (self.__task.workspace_centre[0] + workspace_volume_half_new[0], self.__task.workspace_centre[1] + workspace_volume_half_new[1], self.__task.workspace_centre[2] + workspace_volume_half_new[2])
        self.__task.add_task_parameter_overrides({'workspace_volume': workspace_volume_new, 'workspace_min_bound': workspace_min_bound_new, 'workspace_max_bound': workspace_max_bound_new})

def reset_task(self):
    self.__update_workspace_size()

