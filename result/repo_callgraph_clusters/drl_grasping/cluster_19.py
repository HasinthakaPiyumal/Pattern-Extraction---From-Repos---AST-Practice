# Cluster 19

class StageRewardCurriculum:
    """
    Curriculum that begins to compute rewards for a stage once all previous stages are complete.
    """
    PERSISTENT_ID: str = 'PERSISTENT'
    INFO_CURRICULUM_PREFIX: str = 'curriculum/'

    def __init__(self, curriculum_stage: Type[CurriculumStage], stage_reward_multiplier: float, dense_reward: bool=False, **kwargs):
        if 0 == len(curriculum_stage):
            raise TypeException(f'{curriculum_stage} has length of 0')
        self.__use_dense_reward = dense_reward
        if self.__use_dense_reward:
            raise ValueError('Dense reward is currently not implemented for any curriculum')
        self._stage_type = curriculum_stage
        self._stage_reward_functions: Dict[curriculum_stage, Callable] = {curriculum_stage(stage): getattr(self, f'get_reward_{stage.name}') for stage in iter(curriculum_stage)}
        self.__stage_reward_multipliers: Dict[curriculum_stage, float] = {curriculum_stage(stage): stage_reward_multiplier ** (stage.value - 1) for stage in iter(curriculum_stage)}
        self.stages_completed_this_episode: Dict[curriculum_stage, bool] = {curriculum_stage(stage): False for stage in iter(curriculum_stage)}
        self.__stages_rewards_this_episode: Dict[curriculum_stage, float] = {curriculum_stage(stage): 0.0 for stage in iter(curriculum_stage)}
        self.__stages_rewards_this_episode[self.PERSISTENT_ID] = 0.0
        self.__episode_succeeded: bool = False
        self.__episode_failed: bool = False

    def get_reward(self, only_last_stage: bool=False, **kwargs) -> Reward:
        reward = 0.0
        if only_last_stage:
            first_stage_to_process = self._stage_type.last()
        else:
            for stage in iter(self._stage_type):
                if not self.stages_completed_this_episode[stage]:
                    first_stage_to_process = stage
                    break
        for stage in range(first_stage_to_process.value, len(self._stage_type) + 1):
            stage = self._stage_type(stage)
            stage_reward = self._stage_reward_functions[stage](**kwargs)
            stage_reward *= self.__stage_reward_multipliers[stage]
            reward += stage_reward
            self.__stages_rewards_this_episode[stage] += stage_reward
            if not self.stages_completed_this_episode[stage]:
                break
        self.__episode_succeeded = self.stages_completed_this_episode[self._stage_type.last()]
        if self.__episode_succeeded:
            return reward
        persistent_reward = self.get_persistent_reward(**kwargs)
        reward += persistent_reward
        self.__stages_rewards_this_episode[self.PERSISTENT_ID] += persistent_reward
        return reward

    def is_done(self) -> bool:
        if self.__episode_succeeded:
            self.on_episode_success()
            return True
        elif self.__episode_failed:
            self.on_episode_failure()
            return True
        else:
            return False

    def get_info(self) -> Dict:
        info = {'is_success': self.__episode_succeeded}
        for stage in iter(self._stage_type):
            reached_stage = stage
            if not self.stages_completed_this_episode[stage]:
                break
        info.update({f'{self.INFO_CURRICULUM_PREFIX}{INFO_MEAN_EPISODE_KEY}ep_reached_stage_mean': reached_stage.value})
        info.update({f'{self.INFO_CURRICULUM_PREFIX}{INFO_MEAN_EPISODE_KEY}ep_rew_mean_{stage.value}_{stage.name.lower()}': self.__stages_rewards_this_episode[stage] for stage in iter(self._stage_type)})
        info.update({f'{self.INFO_CURRICULUM_PREFIX}{INFO_MEAN_EPISODE_KEY}ep_rew_mean_{self.PERSISTENT_ID.lower()}': self.__stages_rewards_this_episode[self.PERSISTENT_ID]})
        return info

    def reset_task(self):
        if not (self.__episode_succeeded or self.__episode_failed):
            self.on_episode_timeout()
        self.stages_completed_this_episode = dict.fromkeys(self.stages_completed_this_episode, False)
        self.__stages_rewards_this_episode = dict.fromkeys(self.__stages_rewards_this_episode, 0.0)
        self.__stages_rewards_this_episode[self.PERSISTENT_ID] = 0.0
        self.__episode_succeeded = False
        self.__episode_failed = False

    @property
    def episode_succeeded(self) -> bool:
        return self.__episode_succeeded

    @episode_succeeded.setter
    def episode_succeeded(self, value: bool):
        self.__episode_succeeded = value

    @property
    def episode_failed(self) -> bool:
        return self.__episode_failed

    @episode_failed.setter
    def episode_failed(self, value: bool):
        self.__episode_failed = value

    @property
    def use_dense_reward(self) -> bool:
        return self.__use_dense_reward

    def get_persistent_reward(self, **kwargs) -> float:
        """
        Virtual method.
        """
        reward = 0.0
        return reward

    def on_episode_success(self):
        """
        Virtual method.
        """
        pass

    def on_episode_failure(self):
        """
        Virtual method.
        """
        pass

    def on_episode_timeout(self):
        """
        Virtual method.
        """
        pass

def is_done(self) -> bool:
    if self.__episode_succeeded:
        self.on_episode_success()
        return True
    elif self.__episode_failed:
        self.on_episode_failure()
        return True
    else:
        return False

