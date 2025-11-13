# Cluster 19

class ScenarioManager(object):
    """
    Basic scenario manager class. This class holds all functionality
    required to start, run and stop a scenario.

    The user must not modify this class.

    To use the ScenarioManager:
    1. Create an object via manager = ScenarioManager()
    2. Load a scenario via manager.load_scenario()
    3. Trigger the execution of the scenario manager.run_scenario()
       This function is designed to explicitly control start and end of
       the scenario execution
    4. If needed, cleanup with manager.stop_scenario()
    """

    def __init__(self, timeout, debug_mode=False):
        """
        Setups up the parameters, which will be filled at load_scenario()
        """
        self.scenario = None
        self.scenario_tree = None
        self.scenario_class = None
        self.ego_vehicles = None
        self.other_actors = None
        self._debug_mode = debug_mode
        self._agent = None
        self._running = False
        self._timestamp_last_run = 0.0
        self._timeout = float(timeout)
        watchdog_timeout = max(5, self._timeout - 2)
        self._watchdog = Watchdog(watchdog_timeout)
        agent_timeout = watchdog_timeout - 1
        self._agent_watchdog = Watchdog(agent_timeout)
        self.scenario_duration_system = 0.0
        self.scenario_duration_game = 0.0
        self.start_system_time = None
        self.end_system_time = None
        self.end_game_time = None
        signal.signal(signal.SIGINT, self.signal_handler)

    def signal_handler(self, signum, frame):
        """
        Terminate scenario ticking when receiving a signal interrupt
        """
        self._running = False

    def cleanup(self):
        """
        Reset all parameters
        """
        self._timestamp_last_run = 0.0
        self.scenario_duration_system = 0.0
        self.scenario_duration_game = 0.0
        self.start_system_time = None
        self.end_system_time = None
        self.end_game_time = None

    def load_scenario(self, scenario, agent, rep_number):
        """
        Load a new scenario
        """
        GameTime.restart()
        self._agent = AgentWrapper(agent)
        self.scenario_class = scenario
        self.scenario = scenario.scenario
        self.scenario_tree = self.scenario.scenario_tree
        self.ego_vehicles = scenario.ego_vehicles
        self.other_actors = scenario.other_actors
        self.repetition_number = rep_number
        self._agent.setup_sensors(self.ego_vehicles[0], self._debug_mode)

    def run_scenario(self):
        """
        Trigger the start of the scenario and wait for it to finish/fail
        """
        self.start_system_time = time.time()
        self.start_game_time = GameTime.get_time()
        self._watchdog.start()
        self._running = True
        while self._running:
            timestamp = None
            world = CarlaDataProvider.get_world()
            if world:
                snapshot = world.get_snapshot()
                if snapshot:
                    timestamp = snapshot.timestamp
            if timestamp:
                self._tick_scenario(timestamp)

    def _tick_scenario(self, timestamp):
        """
        Run next tick of scenario and the agent and tick the world.
        """
        if self._timestamp_last_run < timestamp.elapsed_seconds and self._running:
            self._timestamp_last_run = timestamp.elapsed_seconds
            self._watchdog.update()
            GameTime.on_carla_tick(timestamp)
            CarlaDataProvider.on_carla_tick()
            try:
                ego_action = self._agent()
            except SensorReceivedNoData as e:
                raise RuntimeError(e)
            except Exception as e:
                raise AgentError(e)
            self.ego_vehicles[0].apply_control(ego_action)
            self.scenario_tree.tick_once()
            if self._debug_mode:
                print('\n')
                py_trees.display.print_ascii_tree(self.scenario_tree, show_status=True)
                sys.stdout.flush()
            if self.scenario_tree.status != py_trees.common.Status.RUNNING:
                self._running = False
            spectator = CarlaDataProvider.get_world().get_spectator()
            ego_trans = self.ego_vehicles[0].get_transform()
            spectator.set_transform(carla.Transform(ego_trans.location + carla.Location(z=50), carla.Rotation(pitch=-90)))
        if self._running and self.get_running_status():
            CarlaDataProvider.get_world().tick(self._timeout)

    def get_running_status(self):
        """
        returns:
           bool: False if watchdog exception occured, True otherwise
        """
        return self._watchdog.get_status()

    def stop_scenario(self):
        """
        This function triggers a proper termination of a scenario
        """
        self._watchdog.stop()
        self.end_system_time = time.time()
        self.end_game_time = GameTime.get_time()
        self.scenario_duration_system = self.end_system_time - self.start_system_time
        self.scenario_duration_game = self.end_game_time - self.start_game_time
        if self.get_running_status():
            if self.scenario is not None:
                self.scenario.terminate()
            if self._agent is not None:
                self._agent.cleanup()
                self._agent = None
            self.analyze_scenario()

    def analyze_scenario(self):
        """
        Analyzes and prints the results of the route
        """
        global_result = '\x1b[92m' + 'SUCCESS' + '\x1b[0m'
        for criterion in self.scenario.get_criteria():
            if criterion.test_status != 'SUCCESS':
                global_result = '\x1b[91m' + 'FAILURE' + '\x1b[0m'
        if self.scenario.timeout_node.timeout:
            global_result = '\x1b[91m' + 'FAILURE' + '\x1b[0m'
        ResultOutputProvider(self, global_result)

def load_scenario(self, scenario, agent, rep_number):
    """
        Load a new scenario
        """
    GameTime.restart()
    self._agent = AgentWrapper(agent)
    self.scenario_class = scenario
    self.scenario = scenario.scenario
    self.scenario_tree = self.scenario.scenario_tree
    self.ego_vehicles = scenario.ego_vehicles
    self.other_actors = scenario.other_actors
    self.repetition_number = rep_number
    self._agent.setup_sensors(self.ego_vehicles[0], self._debug_mode)

class ScenarioManager(object):
    """
    Basic scenario manager class. This class holds all functionality
    required to start, run and stop a scenario.

    The user must not modify this class.

    To use the ScenarioManager:
    1. Create an object via manager = ScenarioManager()
    2. Load a scenario via manager.load_scenario()
    3. Trigger the execution of the scenario manager.run_scenario()
       This function is designed to explicitly control start and end of
       the scenario execution
    4. If needed, cleanup with manager.stop_scenario()
    """

    def __init__(self, timeout, debug_mode=False):
        """
        Setups up the parameters, which will be filled at load_scenario()
        """
        self.scenario = None
        self.scenario_tree = None
        self.scenario_class = None
        self.ego_vehicles = None
        self.other_actors = None
        self._debug_mode = debug_mode
        self._agent = None
        self._running = False
        self._timestamp_last_run = 0.0
        self._timeout = float(timeout)
        watchdog_timeout = max(5, self._timeout - 2)
        self._watchdog = Watchdog(watchdog_timeout)
        agent_timeout = watchdog_timeout - 1
        self._agent_watchdog = Watchdog(agent_timeout)
        self.scenario_duration_system = 0.0
        self.scenario_duration_game = 0.0
        self.start_system_time = None
        self.end_system_time = None
        self.end_game_time = None
        signal.signal(signal.SIGINT, self.signal_handler)

    def signal_handler(self, signum, frame):
        """
        Terminate scenario ticking when receiving a signal interrupt
        """
        self._running = False

    def cleanup(self):
        """
        Reset all parameters
        """
        self._timestamp_last_run = 0.0
        self.scenario_duration_system = 0.0
        self.scenario_duration_game = 0.0
        self.start_system_time = None
        self.end_system_time = None
        self.end_game_time = None

    def load_scenario(self, scenario, agent, rep_number):
        """
        Load a new scenario
        """
        GameTime.restart()
        self._agent = AgentWrapper(agent)
        self.scenario_class = scenario
        self.scenario = scenario.scenario
        self.scenario_tree = self.scenario.scenario_tree
        self.ego_vehicles = scenario.ego_vehicles
        self.other_actors = scenario.other_actors
        self.repetition_number = rep_number
        self._agent.setup_sensors(self.ego_vehicles[0], self._debug_mode)

    def run_scenario(self):
        """
        Trigger the start of the scenario and wait for it to finish/fail
        """
        self.start_system_time = time.time()
        self.start_game_time = GameTime.get_time()
        self._watchdog.start()
        self._running = True
        while self._running:
            timestamp = None
            world = CarlaDataProvider.get_world()
            if world:
                snapshot = world.get_snapshot()
                if snapshot:
                    timestamp = snapshot.timestamp
            if timestamp:
                self._tick_scenario(timestamp)

    def _tick_scenario(self, timestamp):
        """
        Run next tick of scenario and the agent and tick the world.
        """
        if self._timestamp_last_run < timestamp.elapsed_seconds and self._running:
            self._timestamp_last_run = timestamp.elapsed_seconds
            self._watchdog.update()
            GameTime.on_carla_tick(timestamp)
            CarlaDataProvider.on_carla_tick()
            try:
                ego_action = self._agent()
            except SensorReceivedNoData as e:
                raise RuntimeError(e)
            except Exception as e:
                raise AgentError(e)
            self.ego_vehicles[0].apply_control(ego_action)
            self.scenario_tree.tick_once()
            if self._debug_mode:
                print('\n')
                py_trees.display.print_ascii_tree(self.scenario_tree, show_status=True)
                sys.stdout.flush()
            if self.scenario_tree.status != py_trees.common.Status.RUNNING:
                self._running = False
            spectator = CarlaDataProvider.get_world().get_spectator()
            ego_trans = self.ego_vehicles[0].get_transform()
            spectator.set_transform(carla.Transform(ego_trans.location + carla.Location(z=50), carla.Rotation(pitch=-90)))
        if self._running and self.get_running_status():
            CarlaDataProvider.get_world().tick(self._timeout)

    def get_running_status(self):
        """
        returns:
           bool: False if watchdog exception occured, True otherwise
        """
        return self._watchdog.get_status()

    def stop_scenario(self):
        """
        This function triggers a proper termination of a scenario
        """
        self._watchdog.stop()
        self.end_system_time = time.time()
        self.end_game_time = GameTime.get_time()
        self.scenario_duration_system = self.end_system_time - self.start_system_time
        self.scenario_duration_game = self.end_game_time - self.start_game_time
        if self.get_running_status():
            if self.scenario is not None:
                self.scenario.terminate()
            if self._agent is not None:
                self._agent.cleanup()
                self._agent = None
            self.analyze_scenario()

    def analyze_scenario(self):
        """
        Analyzes and prints the results of the route
        """
        global_result = '\x1b[92m' + 'SUCCESS' + '\x1b[0m'
        for criterion in self.scenario.get_criteria():
            if criterion.test_status != 'SUCCESS':
                global_result = '\x1b[91m' + 'FAILURE' + '\x1b[0m'
        if self.scenario.timeout_node.timeout:
            global_result = '\x1b[91m' + 'FAILURE' + '\x1b[0m'
        ResultOutputProvider(self, global_result)

def load_scenario(self, scenario, agent, rep_number):
    """
        Load a new scenario
        """
    GameTime.restart()
    self._agent = AgentWrapper(agent)
    self.scenario_class = scenario
    self.scenario = scenario.scenario
    self.scenario_tree = self.scenario.scenario_tree
    self.ego_vehicles = scenario.ego_vehicles
    self.other_actors = scenario.other_actors
    self.repetition_number = rep_number
    self._agent.setup_sensors(self.ego_vehicles[0], self._debug_mode)

class ScenarioManager(object):
    """
    Basic scenario manager class. This class holds all functionality
    required to start, and analyze a scenario.

    The user must not modify this class.

    To use the ScenarioManager:
    1. Create an object via manager = ScenarioManager()
    2. Load a scenario via manager.load_scenario()
    3. Trigger the execution of the scenario manager.run_scenario()
       This function is designed to explicitly control start and end of
       the scenario execution
    4. Trigger a result evaluation with manager.analyze_scenario()
    5. If needed, cleanup with manager.stop_scenario()
    """

    def __init__(self, debug_mode=False, sync_mode=False, timeout=2.0):
        """
        Setups up the parameters, which will be filled at load_scenario()

        """
        self.scenario = None
        self.scenario_tree = None
        self.scenario_class = None
        self.ego_vehicles = None
        self.other_actors = None
        self._debug_mode = debug_mode
        self._agent = None
        self._sync_mode = sync_mode
        self._running = False
        self._timestamp_last_run = 0.0
        self._timeout = timeout
        self._watchdog = Watchdog(float(self._timeout))
        self.scenario_duration_system = 0.0
        self.scenario_duration_game = 0.0
        self.start_system_time = None
        self.end_system_time = None

    def _reset(self):
        """
        Reset all parameters
        """
        self._running = False
        self._timestamp_last_run = 0.0
        self.scenario_duration_system = 0.0
        self.scenario_duration_game = 0.0
        self.start_system_time = None
        self.end_system_time = None
        GameTime.restart()

    def cleanup(self):
        """
        This function triggers a proper termination of a scenario
        """
        if self.scenario is not None:
            self.scenario.terminate()
        if self._agent is not None:
            self._agent.cleanup()
            self._agent = None
        CarlaDataProvider.cleanup()

    def load_scenario(self, scenario, agent=None):
        """
        Load a new scenario
        """
        self._reset()
        self._agent = AgentWrapper(agent) if agent else None
        if self._agent is not None:
            self._sync_mode = True
        self.scenario_class = scenario
        self.scenario = scenario.scenario
        self.scenario_tree = self.scenario.scenario_tree
        self.ego_vehicles = scenario.ego_vehicles
        self.other_actors = scenario.other_actors
        if self._agent is not None:
            self._agent.setup_sensors(self.ego_vehicles[0], self._debug_mode)

    def run_scenario(self):
        """
        Trigger the start of the scenario and wait for it to finish/fail
        """
        print('ScenarioManager: Running scenario {}'.format(self.scenario_tree.name))
        self.start_system_time = time.time()
        start_game_time = GameTime.get_time()
        self._watchdog.start()
        self._running = True
        while self._running:
            timestamp = None
            world = CarlaDataProvider.get_world()
            if world:
                snapshot = world.get_snapshot()
                if snapshot:
                    timestamp = snapshot.timestamp
            if timestamp:
                self._tick_scenario(timestamp)
        self._watchdog.stop()
        self.cleanup()
        self.end_system_time = time.time()
        end_game_time = GameTime.get_time()
        self.scenario_duration_system = self.end_system_time - self.start_system_time
        self.scenario_duration_game = end_game_time - start_game_time
        if self.scenario_tree.status == py_trees.common.Status.FAILURE:
            print('ScenarioManager: Terminated due to failure')

    def _tick_scenario(self, timestamp):
        """
        Run next tick of scenario and the agent.
        If running synchornously, it also handles the ticking of the world.
        """
        if self._timestamp_last_run < timestamp.elapsed_seconds and self._running:
            self._timestamp_last_run = timestamp.elapsed_seconds
            self._watchdog.update()
            if self._debug_mode:
                print('\n--------- Tick ---------\n')
            GameTime.on_carla_tick(timestamp)
            CarlaDataProvider.on_carla_tick()
            if self._agent is not None:
                ego_action = self._agent()
            self.scenario_tree.tick_once()
            if self._debug_mode:
                print('\n')
                py_trees.display.print_ascii_tree(self.scenario_tree, show_status=True)
                sys.stdout.flush()
            if self.scenario_tree.status != py_trees.common.Status.RUNNING:
                self._running = False
            if self._agent is not None:
                self.ego_vehicles[0].apply_control(ego_action)
        if self._sync_mode and self._running and self._watchdog.get_status():
            CarlaDataProvider.get_world().tick()

    def get_running_status(self):
        """
        returns:
           bool:  False if watchdog exception occured, True otherwise
        """
        return self._watchdog.get_status()

    def stop_scenario(self):
        """
        This function is used by the overall signal handler to terminate the scenario execution
        """
        self._running = False

    def analyze_scenario(self, stdout, filename, junit):
        """
        This function is intended to be called from outside and provide
        the final statistics about the scenario (human-readable, in form of a junit
        report, etc.)
        """
        failure = False
        timeout = False
        result = 'SUCCESS'
        if self.scenario.test_criteria is None:
            print('Nothing to analyze, this scenario has no criteria')
            return True
        for criterion in self.scenario.get_criteria():
            if not criterion.optional and criterion.test_status != 'SUCCESS' and (criterion.test_status != 'ACCEPTABLE'):
                failure = True
                result = 'FAILURE'
            elif criterion.test_status == 'ACCEPTABLE':
                result = 'ACCEPTABLE'
        if self.scenario.timeout_node.timeout and (not failure):
            timeout = True
            result = 'TIMEOUT'
        output = ResultOutputProvider(self, result, stdout, filename, junit)
        output.write()
        return failure or timeout

def _reset(self):
    """
        Reset all parameters
        """
    self._running = False
    self._timestamp_last_run = 0.0
    self.scenario_duration_system = 0.0
    self.scenario_duration_game = 0.0
    self.start_system_time = None
    self.end_system_time = None
    GameTime.restart()

def load_scenario(self, scenario, agent=None):
    """
        Load a new scenario
        """
    self._reset()
    self._agent = AgentWrapper(agent) if agent else None
    if self._agent is not None:
        self._sync_mode = True
    self.scenario_class = scenario
    self.scenario = scenario.scenario
    self.scenario_tree = self.scenario.scenario_tree
    self.ego_vehicles = scenario.ego_vehicles
    self.other_actors = scenario.other_actors
    if self._agent is not None:
        self._agent.setup_sensors(self.ego_vehicles[0], self._debug_mode)

