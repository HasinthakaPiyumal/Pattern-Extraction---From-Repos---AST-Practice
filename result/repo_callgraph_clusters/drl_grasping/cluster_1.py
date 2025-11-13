# Cluster 1

class RealEvaluationRuntime(Runtime):
    """
    Implementation of :py:class:`~gym_ignition.base.runtime.Runtime` for execution
    of trained agents on real robots (evaluation only).

    It is assumed that the task has an interface that is invariant to sim/real domain for both actions and observations (e.g. ROS 2 middleware).

    This runtime requires manual reset of the workspace as well as manual logging
    of success rate.

    Enable `manual_stepping` to manually step through the execution (safe mode).
    """

    def __init__(self, task_cls: type, agent_rate: float, manual_stepping: bool=True, **kwargs):
        task = task_cls(agent_rate=agent_rate, **kwargs)
        if not isinstance(task, Task):
            raise RuntimeError('The task is not compatible with the runtime')
        super().__init__(task=task, agent_rate=agent_rate)
        self.action_space, self.observation_space = self.task.create_spaces()
        self.task.action_space = self.action_space
        self.task.observation_space = self.observation_space
        self.seed()
        self._manual_stepping = manual_stepping
        if manual_stepping:
            print("Safety feature for manual stepping is enabled. 'Enter' must be pressed to perform each step.")
        print("Press 'ESC' to terminate.")
        print("Press 'd' once episode is done (either success of failure). Success rate must be logged manually.")
        self._manual_done = False
        self._manual_terminate = False
        listener = keyboard.Listener(on_press=self.on_press)
        listener.start()
        self.running_time = 0.0
        self.start_time = time.time()

    def timestamp(self, running_time: bool=True) -> float:
        if running_time:
            return self.running_time
        else:
            return time.time() - self.start_time

    def step(self, action: Action) -> State:
        if self._manual_stepping:
            input('Press a key to continue...')
        pre_step_time = time.time()
        if self._manual_terminate:
            print('Terminating...')
            sys.exit()
        if not self._manual_done:
            if not self.action_space.contains(action):
                logger.warn('The action does not belong to the action space')
            print('Performing action...')
            self.task.set_action(action)
            if isinstance(self.task, Manipulation):
                print('Waiting until the action is executed...')
                self.task.wait_until_action_executed()
        observation = self.task.get_observation()
        assert isinstance(observation, np.ndarray)
        if not self.observation_space.contains(observation):
            logger.warn('The observation does not belong to the observation space')
        reward = 0.0
        done = self._manual_done
        info = {}
        self.running_time += time.time() - pre_step_time
        return State((Observation(observation), Reward(reward), Done(done), Info(info)))

    def reset(self) -> Observation:
        input('Episode done, please reset the workspace for a new episode. Once the workspace is reset, press any key.')
        print('After 5 seconds, the robot will move to its initial joint configuration. Be ready...')
        time.sleep(5.0)
        if isinstance(self.task, Manipulation):
            print('Moving to the initial joint configuration...')
            self.task.move_to_initial_joint_configuration()
        input('Press any key to confirm that robot and workspace are reset...')
        self._manual_done = False
        self.task.reset_task()
        observation = self.task.get_observation()
        assert isinstance(observation, np.ndarray)
        if not self.observation_space.contains(observation):
            logger.warn('The observation does not belong to the observation space')
        return Observation(observation)

    def seed(self, seed: Optional[int]=None) -> SeedList:
        seed = self.task.seed_task(seed)
        return seed

    def render(self, mode: str='human'):
        pass

    def close(self):
        pass

    def on_press(self, key: keyboard.KeyCode):
        print('')
        if keyboard.KeyCode.from_char('d') == key:
            print("'d' pressed: This episode is now considered to be finished. Please log whether it was success or failure.")
            self._manual_done = True
        elif keyboard.Key.esc == key:
            print("'ESC' pressed: Termination signal received...")
            self._manual_terminate = True

def seed(self, seed: Optional[int]=None) -> SeedList:
    seed = self.task.seed_task(seed)
    return seed

