# Cluster 37

class LeaderboardEvaluator(object):
    """
    TODO: document me!
    """
    ego_vehicles = []
    client_timeout = 10.0
    wait_for_world = 20.0
    frame_rate = 20.0

    def __init__(self, args, statistics_manager):
        """
        Setup CARLA client and world
        Setup ScenarioManager
        """
        self.statistics_manager = statistics_manager
        self.sensors = None
        self.sensor_icons = []
        self._vehicle_lights = carla.VehicleLightState.Position | carla.VehicleLightState.LowBeam
        self.client = carla.Client(args.host, int(args.port))
        if args.timeout:
            self.client_timeout = float(args.timeout)
        self.client.set_timeout(self.client_timeout)
        self.world = self.client.load_world('Town01')
        self.traffic_manager = self.client.get_trafficmanager(int(args.trafficManagerPort))
        dist = pkg_resources.get_distribution('carla')
        if dist.version != 'leaderboard':
            if LooseVersion(dist.version) < LooseVersion('0.9.10'):
                raise ImportError('CARLA version 0.9.10.1 or newer required. CARLA version found: {}'.format(dist))
        module_name = os.path.basename(args.agent).split('.')[0]
        sys.path.insert(0, os.path.dirname(args.agent))
        self.module_agent = importlib.import_module(module_name)
        self.manager = ScenarioManager(args.timeout, args.debug > 1)
        self._start_time = GameTime.get_time()
        self._end_time = None
        self._agent_watchdog = Watchdog(int(float(args.timeout)))
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """
        Terminate scenario ticking when receiving a signal interrupt
        """
        if self._agent_watchdog and (not self._agent_watchdog.get_status()):
            raise RuntimeError('Timeout: Agent took too long to setup')
        elif self.manager:
            self.manager.signal_handler(signum, frame)

    def __del__(self):
        """
        Cleanup and delete actors, ScenarioManager and CARLA world
        """
        self._cleanup()
        if hasattr(self, 'manager') and self.manager:
            del self.manager
        if hasattr(self, 'world') and self.world:
            del self.world

    def _cleanup(self):
        """
        Remove and destroy all actors
        """
        if self.manager and self.manager.get_running_status() and hasattr(self, 'world') and self.world:
            settings = self.world.get_settings()
            settings.synchronous_mode = False
            settings.fixed_delta_seconds = None
            self.world.apply_settings(settings)
            self.traffic_manager.set_synchronous_mode(False)
        if self.manager:
            self.manager.cleanup()
        CarlaDataProvider.cleanup()
        for i, _ in enumerate(self.ego_vehicles):
            if self.ego_vehicles[i]:
                self.ego_vehicles[i].destroy()
                self.ego_vehicles[i] = None
        self.ego_vehicles = []
        if self._agent_watchdog:
            self._agent_watchdog.stop()
        if hasattr(self, 'agent_instance') and self.agent_instance:
            self.agent_instance.destroy()
            self.agent_instance = None
        if hasattr(self, 'statistics_manager') and self.statistics_manager:
            self.statistics_manager.scenario = None

    def _prepare_ego_vehicles(self, ego_vehicles, wait_for_ego_vehicles=False):
        """
        Spawn or update the ego vehicles
        """
        if not wait_for_ego_vehicles:
            for vehicle in ego_vehicles:
                self.ego_vehicles.append(CarlaDataProvider.request_new_actor(vehicle.model, vehicle.transform, vehicle.rolename, color=vehicle.color, vehicle_category=vehicle.category))
        else:
            ego_vehicle_missing = True
            while ego_vehicle_missing:
                self.ego_vehicles = []
                ego_vehicle_missing = False
                for ego_vehicle in ego_vehicles:
                    ego_vehicle_found = False
                    carla_vehicles = CarlaDataProvider.get_world().get_actors().filter('vehicle.*')
                    for carla_vehicle in carla_vehicles:
                        if carla_vehicle.attributes['role_name'] == ego_vehicle.rolename:
                            ego_vehicle_found = True
                            self.ego_vehicles.append(carla_vehicle)
                            break
                    if not ego_vehicle_found:
                        ego_vehicle_missing = True
                        break
            for i, _ in enumerate(self.ego_vehicles):
                self.ego_vehicles[i].set_transform(ego_vehicles[i].transform)
        CarlaDataProvider.get_world().tick()

    def _load_and_wait_for_world(self, args, town, ego_vehicles=None):
        """
        Load a new CARLA world and provide data to CarlaDataProvider
        """
        self.world = self.client.load_world(town)
        settings = self.world.get_settings()
        settings.fixed_delta_seconds = 1.0 / self.frame_rate
        settings.synchronous_mode = True
        self.world.apply_settings(settings)
        self.world.reset_all_traffic_lights()
        CarlaDataProvider.set_client(self.client)
        CarlaDataProvider.set_world(self.world)
        CarlaDataProvider.set_traffic_manager_port(int(args.trafficManagerPort))
        self.traffic_manager.set_synchronous_mode(True)
        self.traffic_manager.set_random_device_seed(int(args.trafficManagerSeed))
        if CarlaDataProvider.is_sync_mode():
            self.world.tick()
        else:
            self.world.wait_for_tick()
        if CarlaDataProvider.get_map().name != town:
            raise Exception('The CARLA server uses the wrong map!This scenario requires to use map {}'.format(town))

    def _register_statistics(self, config, checkpoint, entry_status, crash_message=''):
        """
        Computes and saved the simulation statistics
        """
        current_stats_record = self.statistics_manager.compute_route_statistics(config, self.manager.scenario_duration_system, self.manager.scenario_duration_game, crash_message)
        print('\x1b[1m> Registering the route statistics\x1b[0m')
        self.statistics_manager.save_record(current_stats_record, config.index, checkpoint)
        self.statistics_manager.save_entry_status(entry_status, False, checkpoint)

    def _load_and_run_scenario(self, args, config):
        """
        Load and run the scenario given by config.

        Depending on what code fails, the simulation will either stop the route and
        continue from the next one, or report a crash and stop.
        """
        crash_message = ''
        entry_status = 'Started'
        print('\n\x1b[1m========= Preparing {} (repetition {}) ========='.format(config.name, config.repetition_index))
        print('> Setting up the agent\x1b[0m')
        self.statistics_manager.set_route(config.name, config.index)
        if int(os.environ['DATAGEN']) == 1:
            CarlaDataProvider._rng = random.RandomState(config.index)
        try:
            self._agent_watchdog.start()
            agent_class_name = getattr(self.module_agent, 'get_entry_point')()
            if int(os.environ['DATAGEN']) == 1:
                self.agent_instance = getattr(self.module_agent, agent_class_name)(args.agent_config, config.index)
            else:
                self.agent_instance = getattr(self.module_agent, agent_class_name)(args.agent_config)
            config.agent = self.agent_instance
            if not self.sensors:
                self.sensors = self.agent_instance.sensors()
                track = self.agent_instance.track
                AgentWrapper.validate_sensor_configuration(self.sensors, track, args.track)
                self.sensor_icons = [sensors_to_icons[sensor['type']] for sensor in self.sensors]
                self.statistics_manager.save_sensors(self.sensor_icons, args.checkpoint)
            self._agent_watchdog.stop()
        except SensorConfigurationInvalid as e:
            print("\n\x1b[91mThe sensor's configuration used is invalid:")
            print('> {}\x1b[0m\n'.format(e))
            traceback.print_exc()
            crash_message = "Agent's sensors were invalid"
            entry_status = 'Rejected'
            self._register_statistics(config, args.checkpoint, entry_status, crash_message)
            self._cleanup()
            sys.exit(-1)
        except Exception as e:
            print('\n\x1b[91mCould not set up the required agent:')
            print('> {}\x1b[0m\n'.format(e))
            traceback.print_exc()
            crash_message = "Agent couldn't be set up"
            self._register_statistics(config, args.checkpoint, entry_status, crash_message)
            self._cleanup()
            return
        print('\x1b[1m> Loading the world\x1b[0m')
        try:
            self._load_and_wait_for_world(args, config.town, config.ego_vehicles)
            self._prepare_ego_vehicles(config.ego_vehicles, False)
            scenario = RouteScenario(world=self.world, config=config, debug_mode=args.debug)
            self.statistics_manager.set_scenario(scenario.scenario)
            if config.weather.sun_altitude_angle < 0.0:
                for vehicle in scenario.ego_vehicles:
                    vehicle.set_light_state(carla.VehicleLightState(self._vehicle_lights))
            if args.record:
                self.client.start_recorder('{}/{}_rep{}.log'.format(args.record, config.name, config.repetition_index))
            self.manager.load_scenario(scenario, self.agent_instance, config.repetition_index)
        except Exception as e:
            print('\n\x1b[91mThe scenario could not be loaded:')
            print('> {}\x1b[0m\n'.format(e))
            traceback.print_exc()
            crash_message = 'Simulation crashed'
            entry_status = 'Crashed'
            self._register_statistics(config, args.checkpoint, entry_status, crash_message)
            if args.record:
                self.client.stop_recorder()
            self._cleanup()
            sys.exit(-1)
        print('\x1b[1m> Running the route\x1b[0m')
        try:
            self.manager.run_scenario()
        except AgentError as e:
            print('\n\x1b[91mStopping the route, the agent has crashed:')
            print('> {}\x1b[0m\n'.format(e))
            traceback.print_exc()
            crash_message = 'Agent crashed'
        except Exception as e:
            print('\n\x1b[91mError during the simulation:')
            print('> {}\x1b[0m\n'.format(e))
            traceback.print_exc()
            crash_message = 'Simulation crashed'
            entry_status = 'Crashed'
        try:
            print('\x1b[1m> Stopping the route\x1b[0m')
            self.manager.stop_scenario()
            self._register_statistics(config, args.checkpoint, entry_status, crash_message)
            if args.record:
                self.client.stop_recorder()
            scenario.remove_all_actors()
            self._cleanup()
        except Exception as e:
            print('\n\x1b[91mFailed to stop the scenario, the statistics might be empty:')
            print('> {}\x1b[0m\n'.format(e))
            traceback.print_exc()
            crash_message = 'Simulation crashed'
        if crash_message == 'Simulation crashed':
            sys.exit(-1)

    def run(self, args):
        """
        Run the challenge mode
        """
        route_indexer = RouteIndexer(args.routes, args.scenarios, args.repetitions)
        if args.resume:
            route_indexer.resume(args.checkpoint)
            self.statistics_manager.resume(args.checkpoint)
        else:
            self.statistics_manager.clear_record(args.checkpoint)
            route_indexer.save_state(args.checkpoint)
        while route_indexer.peek():
            config = route_indexer.next()
            self._load_and_run_scenario(args, config)
            route_indexer.save_state(args.checkpoint)
        print('\x1b[1m> Registering the global statistics\x1b[0m')
        global_stats_record = self.statistics_manager.compute_global_statistics(route_indexer.total)
        StatisticsManager.save_global_record(global_stats_record, self.sensor_icons, route_indexer.total, args.checkpoint)

def _signal_handler(self, signum, frame):
    """
        Terminate scenario ticking when receiving a signal interrupt
        """
    if self._agent_watchdog and (not self._agent_watchdog.get_status()):
        raise RuntimeError('Timeout: Agent took too long to setup')
    elif self.manager:
        self.manager.signal_handler(signum, frame)

class LeaderboardEvaluator(object):
    """
    TODO: document me!
    """
    ego_vehicles = []
    client_timeout = 10.0
    wait_for_world = 20.0
    frame_rate = 20.0

    def __init__(self, args, statistics_manager):
        """
        Setup CARLA client and world
        Setup ScenarioManager
        """
        self.statistics_manager = statistics_manager
        self.sensors = None
        self.sensor_icons = []
        self._vehicle_lights = carla.VehicleLightState.Position | carla.VehicleLightState.LowBeam
        self.client = carla.Client(args.host, int(args.port))
        if args.timeout:
            self.client_timeout = float(args.timeout)
        self.client.set_timeout(self.client_timeout)
        self.traffic_manager = self.client.get_trafficmanager(int(args.trafficManagerPort))
        dist = pkg_resources.get_distribution('carla')
        if dist.version != 'leaderboard':
            if LooseVersion(dist.version) < LooseVersion('0.9.10'):
                raise ImportError('CARLA version 0.9.10.1 or newer required. CARLA version found: {}'.format(dist))
        module_name = os.path.basename(args.agent).split('.')[0]
        sys.path.insert(0, os.path.dirname(args.agent))
        self.module_agent = importlib.import_module(module_name)
        self.manager = ScenarioManager(args.timeout, args.debug > 1)
        self._start_time = GameTime.get_time()
        self._end_time = None
        self._agent_watchdog = Watchdog(int(float(args.timeout)))
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """
        Terminate scenario ticking when receiving a signal interrupt
        """
        if self._agent_watchdog and (not self._agent_watchdog.get_status()):
            raise RuntimeError('Timeout: Agent took too long to setup')
        elif self.manager:
            self.manager.signal_handler(signum, frame)

    def __del__(self):
        """
        Cleanup and delete actors, ScenarioManager and CARLA world
        """
        self._cleanup()
        if hasattr(self, 'manager') and self.manager:
            del self.manager
        if hasattr(self, 'world') and self.world:
            del self.world

    def _cleanup(self):
        """
        Remove and destroy all actors
        """
        if self.manager and self.manager.get_running_status() and hasattr(self, 'world') and self.world:
            settings = self.world.get_settings()
            settings.synchronous_mode = False
            settings.fixed_delta_seconds = None
            self.world.apply_settings(settings)
            self.traffic_manager.set_synchronous_mode(False)
        if self.manager:
            self.manager.cleanup()
        CarlaDataProvider.cleanup()
        for i, _ in enumerate(self.ego_vehicles):
            if self.ego_vehicles[i]:
                self.ego_vehicles[i].destroy()
                self.ego_vehicles[i] = None
        self.ego_vehicles = []
        if self._agent_watchdog:
            self._agent_watchdog.stop()
        if hasattr(self, 'agent_instance') and self.agent_instance:
            self.agent_instance.destroy()
            self.agent_instance = None
        if hasattr(self, 'statistics_manager') and self.statistics_manager:
            self.statistics_manager.scenario = None

    def _prepare_ego_vehicles(self, ego_vehicles, wait_for_ego_vehicles=False):
        """
        Spawn or update the ego vehicles
        """
        if not wait_for_ego_vehicles:
            for vehicle in ego_vehicles:
                self.ego_vehicles.append(CarlaDataProvider.request_new_actor(vehicle.model, vehicle.transform, vehicle.rolename, color=vehicle.color, vehicle_category=vehicle.category))
        else:
            ego_vehicle_missing = True
            while ego_vehicle_missing:
                self.ego_vehicles = []
                ego_vehicle_missing = False
                for ego_vehicle in ego_vehicles:
                    ego_vehicle_found = False
                    carla_vehicles = CarlaDataProvider.get_world().get_actors().filter('vehicle.*')
                    for carla_vehicle in carla_vehicles:
                        if carla_vehicle.attributes['role_name'] == ego_vehicle.rolename:
                            ego_vehicle_found = True
                            self.ego_vehicles.append(carla_vehicle)
                            break
                    if not ego_vehicle_found:
                        ego_vehicle_missing = True
                        break
            for i, _ in enumerate(self.ego_vehicles):
                self.ego_vehicles[i].set_transform(ego_vehicles[i].transform)
        CarlaDataProvider.get_world().tick()

    def _load_and_wait_for_world(self, args, town, ego_vehicles=None):
        """
        Load a new CARLA world and provide data to CarlaDataProvider
        """
        self.world = self.client.load_world(town)
        settings = self.world.get_settings()
        settings.fixed_delta_seconds = 1.0 / self.frame_rate
        settings.synchronous_mode = True
        self.world.apply_settings(settings)
        self.world.reset_all_traffic_lights()
        CarlaDataProvider.set_client(self.client)
        CarlaDataProvider.set_world(self.world)
        CarlaDataProvider.set_traffic_manager_port(int(args.trafficManagerPort))
        self.traffic_manager.set_synchronous_mode(True)
        self.traffic_manager.set_random_device_seed(int(args.trafficManagerSeed))
        if CarlaDataProvider.is_sync_mode():
            self.world.tick()
        else:
            self.world.wait_for_tick()
        if CarlaDataProvider.get_map().name != town:
            raise Exception('The CARLA server uses the wrong map!This scenario requires to use map {}'.format(town))

    def _register_statistics(self, config, checkpoint, entry_status, crash_message=''):
        """
        Computes and saved the simulation statistics
        """
        current_stats_record = self.statistics_manager.compute_route_statistics(config, self.manager.scenario_duration_system, self.manager.scenario_duration_game, crash_message)
        print('\x1b[1m> Registering the route statistics\x1b[0m')
        self.statistics_manager.save_record(current_stats_record, config.index, checkpoint)
        self.statistics_manager.save_entry_status(entry_status, False, checkpoint)

    def _load_and_run_scenario(self, args, config):
        """
        Load and run the scenario given by config.

        Depending on what code fails, the simulation will either stop the route and
        continue from the next one, or report a crash and stop.
        """
        crash_message = ''
        entry_status = 'Started'
        print('\n\x1b[1m========= Preparing {} (repetition {}) ========='.format(config.name, config.repetition_index))
        print('> Setting up the agent\x1b[0m')
        self.statistics_manager.set_route(config.name, config.index)
        try:
            self._agent_watchdog.start()
            agent_class_name = getattr(self.module_agent, 'get_entry_point')()
            self.agent_instance = getattr(self.module_agent, agent_class_name)(args.agent_config)
            config.agent = self.agent_instance
            if not self.sensors:
                self.sensors = self.agent_instance.sensors()
                track = self.agent_instance.track
                AgentWrapper.validate_sensor_configuration(self.sensors, track, args.track)
                self.sensor_icons = [sensors_to_icons[sensor['type']] for sensor in self.sensors]
                self.statistics_manager.save_sensors(self.sensor_icons, args.checkpoint)
            self._agent_watchdog.stop()
        except SensorConfigurationInvalid as e:
            print("\n\x1b[91mThe sensor's configuration used is invalid:")
            print('> {}\x1b[0m\n'.format(e))
            traceback.print_exc()
            crash_message = "Agent's sensors were invalid"
            entry_status = 'Rejected'
            self._register_statistics(config, args.checkpoint, entry_status, crash_message)
            self._cleanup()
            sys.exit(-1)
        except Exception as e:
            print('\n\x1b[91mCould not set up the required agent:')
            print('> {}\x1b[0m\n'.format(e))
            traceback.print_exc()
            crash_message = "Agent couldn't be set up"
            self._register_statistics(config, args.checkpoint, entry_status, crash_message)
            self._cleanup()
            return
        print('\x1b[1m> Loading the world\x1b[0m')
        try:
            self._load_and_wait_for_world(args, config.town, config.ego_vehicles)
            self._prepare_ego_vehicles(config.ego_vehicles, False)
            scenario = RouteScenario(world=self.world, config=config, debug_mode=args.debug)
            self.statistics_manager.set_scenario(scenario.scenario)
            if config.weather.sun_altitude_angle < 0.0:
                for vehicle in scenario.ego_vehicles:
                    vehicle.set_light_state(carla.VehicleLightState(self._vehicle_lights))
            if args.record:
                self.client.start_recorder('{}/{}_rep{}.log'.format(args.record, config.name, config.repetition_index))
            self.manager.load_scenario(scenario, self.agent_instance, config.repetition_index)
        except Exception as e:
            print('\n\x1b[91mThe scenario could not be loaded:')
            print('> {}\x1b[0m\n'.format(e))
            traceback.print_exc()
            crash_message = 'Simulation crashed'
            entry_status = 'Crashed'
            self._register_statistics(config, args.checkpoint, entry_status, crash_message)
            if args.record:
                self.client.stop_recorder()
            self._cleanup()
            sys.exit(-1)
        print('\x1b[1m> Running the route\x1b[0m')
        try:
            self.manager.run_scenario()
        except AgentError as e:
            print('\n\x1b[91mStopping the route, the agent has crashed:')
            print('> {}\x1b[0m\n'.format(e))
            traceback.print_exc()
            crash_message = 'Agent crashed'
        except Exception as e:
            print('\n\x1b[91mError during the simulation:')
            print('> {}\x1b[0m\n'.format(e))
            traceback.print_exc()
            crash_message = 'Simulation crashed'
            entry_status = 'Crashed'
        try:
            print('\x1b[1m> Stopping the route\x1b[0m')
            self.manager.stop_scenario()
            self._register_statistics(config, args.checkpoint, entry_status, crash_message)
            if args.record:
                self.client.stop_recorder()
            scenario.remove_all_actors()
            self._cleanup()
        except Exception as e:
            print('\n\x1b[91mFailed to stop the scenario, the statistics might be empty:')
            print('> {}\x1b[0m\n'.format(e))
            traceback.print_exc()
            crash_message = 'Simulation crashed'
        if crash_message == 'Simulation crashed':
            sys.exit(-1)

    def run(self, args):
        """
        Run the challenge mode
        """
        route_indexer = RouteIndexer(args.routes, args.scenarios, args.repetitions)
        if args.resume:
            route_indexer.resume(args.checkpoint)
            self.statistics_manager.resume(args.checkpoint)
        else:
            self.statistics_manager.clear_record(args.checkpoint)
            route_indexer.save_state(args.checkpoint)
        while route_indexer.peek():
            config = route_indexer.next()
            self._load_and_run_scenario(args, config)
            route_indexer.save_state(args.checkpoint)
        print('\x1b[1m> Registering the global statistics\x1b[0m')
        global_stats_record = self.statistics_manager.compute_global_statistics(route_indexer.total)
        StatisticsManager.save_global_record(global_stats_record, self.sensor_icons, route_indexer.total, args.checkpoint)

def _signal_handler(self, signum, frame):
    """
        Terminate scenario ticking when receiving a signal interrupt
        """
    if self._agent_watchdog and (not self._agent_watchdog.get_status()):
        raise RuntimeError('Timeout: Agent took too long to setup')
    elif self.manager:
        self.manager.signal_handler(signum, frame)

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

def get_running_status(self):
    """
        returns:
           bool: False if watchdog exception occured, True otherwise
        """
    return self._watchdog.get_status()

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

def get_running_status(self):
    """
        returns:
           bool: False if watchdog exception occured, True otherwise
        """
    return self._watchdog.get_status()

class BaseReader(object):

    def __init__(self, vehicle, reading_frequency=1.0):
        self._vehicle = vehicle
        self._reading_frequency = reading_frequency
        self._callback = None
        self._run_ps = True
        self.run()

    def __call__(self):
        pass

    @threaded
    def run(self):
        first_time = True
        latest_time = GameTime.get_time()
        while self._run_ps:
            if self._callback is not None:
                current_time = GameTime.get_time()
                if current_time - latest_time > 1 / self._reading_frequency or (first_time and GameTime.get_frame() != 0):
                    self._callback(GenericMeasurement(self.__call__(), GameTime.get_frame()))
                    latest_time = GameTime.get_time()
                    first_time = False
                else:
                    time.sleep(0.001)

    def listen(self, callback):
        self._callback = callback

    def stop(self):
        self._run_ps = False

    def destroy(self):
        self._run_ps = False

@threaded
def run(self):
    first_time = True
    latest_time = GameTime.get_time()
    while self._run_ps:
        if self._callback is not None:
            current_time = GameTime.get_time()
            if current_time - latest_time > 1 / self._reading_frequency or (first_time and GameTime.get_frame() != 0):
                self._callback(GenericMeasurement(self.__call__(), GameTime.get_frame()))
                latest_time = GameTime.get_time()
                first_time = False
            else:
                time.sleep(0.001)

class CallBack(object):

    def __init__(self, tag, sensor_type, sensor, data_provider):
        self._tag = tag
        self._data_provider = data_provider
        self._data_provider.register_sensor(tag, sensor_type, sensor)

    def __call__(self, data):
        if isinstance(data, carla.libcarla.Image):
            self._parse_image_cb(data, self._tag)
        elif isinstance(data, carla.libcarla.LidarMeasurement):
            self._parse_lidar_cb(data, self._tag)
        elif isinstance(data, carla.libcarla.RadarMeasurement):
            self._parse_radar_cb(data, self._tag)
        elif isinstance(data, carla.libcarla.GnssMeasurement):
            self._parse_gnss_cb(data, self._tag)
        elif isinstance(data, carla.libcarla.IMUMeasurement):
            self._parse_imu_cb(data, self._tag)
        elif isinstance(data, GenericMeasurement):
            self._parse_pseudosensor(data, self._tag)
        else:
            logging.error('No callback method for this sensor.')

    def _parse_image_cb(self, image, tag):
        array = np.frombuffer(image.raw_data, dtype=np.dtype('uint8'))
        array = copy.deepcopy(array)
        array = np.reshape(array, (image.height, image.width, 4))
        self._data_provider.update_sensor(tag, array, image.frame)

    def _parse_lidar_cb(self, lidar_data, tag):
        points = np.frombuffer(lidar_data.raw_data, dtype=np.dtype('f4'))
        points = copy.deepcopy(points)
        points = np.reshape(points, (int(points.shape[0] / 4), 4))
        self._data_provider.update_sensor(tag, points, lidar_data.frame)

    def _parse_radar_cb(self, radar_data, tag):
        points = np.frombuffer(radar_data.raw_data, dtype=np.dtype('f4'))
        points = copy.deepcopy(points)
        points = np.reshape(points, (int(points.shape[0] / 4), 4))
        points = np.flip(points, 1)
        self._data_provider.update_sensor(tag, points, radar_data.frame)

    def _parse_gnss_cb(self, gnss_data, tag):
        array = np.array([gnss_data.latitude, gnss_data.longitude, gnss_data.altitude], dtype=np.float64)
        self._data_provider.update_sensor(tag, array, gnss_data.frame)

    def _parse_imu_cb(self, imu_data, tag):
        array = np.array([imu_data.accelerometer.x, imu_data.accelerometer.y, imu_data.accelerometer.z, imu_data.gyroscope.x, imu_data.gyroscope.y, imu_data.gyroscope.z, imu_data.compass], dtype=np.float64)
        self._data_provider.update_sensor(tag, array, imu_data.frame)

    def _parse_pseudosensor(self, package, tag):
        self._data_provider.update_sensor(tag, package.data, package.frame)

def _parse_image_cb(self, image, tag):
    array = np.frombuffer(image.raw_data, dtype=np.dtype('uint8'))
    array = copy.deepcopy(array)
    array = np.reshape(array, (image.height, image.width, 4))
    self._data_provider.update_sensor(tag, array, image.frame)

def _parse_lidar_cb(self, lidar_data, tag):
    points = np.frombuffer(lidar_data.raw_data, dtype=np.dtype('f4'))
    points = copy.deepcopy(points)
    points = np.reshape(points, (int(points.shape[0] / 4), 4))
    self._data_provider.update_sensor(tag, points, lidar_data.frame)

def _parse_radar_cb(self, radar_data, tag):
    points = np.frombuffer(radar_data.raw_data, dtype=np.dtype('f4'))
    points = copy.deepcopy(points)
    points = np.reshape(points, (int(points.shape[0] / 4), 4))
    points = np.flip(points, 1)
    self._data_provider.update_sensor(tag, points, radar_data.frame)

def _parse_gnss_cb(self, gnss_data, tag):
    array = np.array([gnss_data.latitude, gnss_data.longitude, gnss_data.altitude], dtype=np.float64)
    self._data_provider.update_sensor(tag, array, gnss_data.frame)

def _parse_imu_cb(self, imu_data, tag):
    array = np.array([imu_data.accelerometer.x, imu_data.accelerometer.y, imu_data.accelerometer.z, imu_data.gyroscope.x, imu_data.gyroscope.y, imu_data.gyroscope.z, imu_data.compass], dtype=np.float64)
    self._data_provider.update_sensor(tag, array, imu_data.frame)

def _parse_pseudosensor(self, package, tag):
    self._data_provider.update_sensor(tag, package.data, package.frame)

class RosAgent(AutonomousAgent):
    """
    Base class for ROS-based stacks.

    Derive from it and implement the sensors() method.

    Please define TEAM_CODE_ROOT in your environment.
    The stack is started by executing $TEAM_CODE_ROOT/start.sh

    The sensor data is published on similar topics as with the carla-ros-bridge. You can find details about
    the utilized datatypes there.

    This agent expects a roscore to be running.
    """
    speed = None
    current_control = None
    stack_process = None
    timestamp = None
    current_map_name = None
    step_mode_possible = None
    vehicle_info_publisher = None
    global_plan_published = None

    def setup(self, path_to_conf_file):
        """
        setup agent
        """
        self.track = Track.MAP
        self.stack_thread = None
        team_code_path = os.environ['TEAM_CODE_ROOT']
        if not team_code_path or not os.path.exists(team_code_path):
            raise IOError("Path '{}' defined by TEAM_CODE_ROOT invalid".format(team_code_path))
        start_script = '{}/start.sh'.format(team_code_path)
        if not os.path.exists(start_script):
            raise IOError("File '{}' defined by TEAM_CODE_ROOT invalid".format(start_script))
        process = subprocess.Popen('rosparam set use_sim_time true', shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        process.wait()
        if process.returncode:
            raise RuntimeError('Could not set use_sim_time')
        rospy.init_node('ros_agent', anonymous=True)
        self.clock_publisher = rospy.Publisher('clock', Clock, queue_size=10, latch=True)
        self.clock_publisher.publish(Clock(rospy.Time.from_sec(0)))
        rospy.loginfo('Executing stack...')
        self.stack_process = subprocess.Popen(start_script, shell=True, preexec_fn=os.setpgrp)
        self.vehicle_control_event = threading.Event()
        self.timestamp = None
        self.speed = 0
        self.global_plan_published = False
        self.vehicle_info_publisher = None
        self.vehicle_status_publisher = None
        self.odometry_publisher = None
        self.world_info_publisher = None
        self.map_file_publisher = None
        self.current_map_name = None
        self.tf_broadcaster = None
        self.step_mode_possible = False
        self.vehicle_control_subscriber = rospy.Subscriber('/carla/ego_vehicle/vehicle_control_cmd', CarlaEgoVehicleControl, self.on_vehicle_control)
        self.current_control = carla.VehicleControl()
        self.waypoint_publisher = rospy.Publisher('/carla/ego_vehicle/waypoints', Path, queue_size=1, latch=True)
        self.publisher_map = {}
        self.id_to_sensor_type_map = {}
        self.id_to_camera_info_map = {}
        self.cv_bridge = CvBridge()
        for sensor in self.sensors():
            self.id_to_sensor_type_map[sensor['id']] = sensor['type']
            if sensor['type'] == 'sensor.camera.rgb':
                self.publisher_map[sensor['id']] = rospy.Publisher('/carla/ego_vehicle/camera/rgb/' + sensor['id'] + '/image_color', Image, queue_size=1, latch=True)
                self.id_to_camera_info_map[sensor['id']] = self.build_camera_info(sensor)
                self.publisher_map[sensor['id'] + '_info'] = rospy.Publisher('/carla/ego_vehicle/camera/rgb/' + sensor['id'] + '/camera_info', CameraInfo, queue_size=1, latch=True)
            elif sensor['type'] == 'sensor.lidar.ray_cast':
                self.publisher_map[sensor['id']] = rospy.Publisher('/carla/ego_vehicle/lidar/' + sensor['id'] + '/point_cloud', PointCloud2, queue_size=1, latch=True)
            elif sensor['type'] == 'sensor.other.gnss':
                self.publisher_map[sensor['id']] = rospy.Publisher('/carla/ego_vehicle/gnss/' + sensor['id'] + '/fix', NavSatFix, queue_size=1, latch=True)
            elif sensor['type'] == 'sensor.can_bus':
                if not self.vehicle_info_publisher:
                    self.vehicle_info_publisher = rospy.Publisher('/carla/ego_vehicle/vehicle_info', CarlaEgoVehicleInfo, queue_size=1, latch=True)
                if not self.vehicle_status_publisher:
                    self.vehicle_status_publisher = rospy.Publisher('/carla/ego_vehicle/vehicle_status', CarlaEgoVehicleStatus, queue_size=1, latch=True)
            elif sensor['type'] == 'sensor.hd_map':
                if not self.odometry_publisher:
                    self.odometry_publisher = rospy.Publisher('/carla/ego_vehicle/odometry', Odometry, queue_size=1, latch=True)
                if not self.world_info_publisher:
                    self.world_info_publisher = rospy.Publisher('/carla/world_info', CarlaWorldInfo, queue_size=1, latch=True)
                if not self.map_file_publisher:
                    self.map_file_publisher = rospy.Publisher('/carla/map_file', String, queue_size=1, latch=True)
                if not self.tf_broadcaster:
                    self.tf_broadcaster = tf.TransformBroadcaster()
            else:
                raise TypeError('Invalid sensor type: {}'.format(sensor['type']))

    def destroy(self):
        """
        Cleanup of all ROS publishers
        """
        if self.stack_process and self.stack_process.poll() is None:
            rospy.loginfo('Sending SIGTERM to stack...')
            os.killpg(os.getpgid(self.stack_process.pid), signal.SIGTERM)
            rospy.loginfo('Waiting for termination of stack...')
            self.stack_process.wait()
            time.sleep(5)
            rospy.loginfo('Terminated stack.')
        rospy.loginfo('Stack is no longer running')
        self.world_info_publisher.unregister()
        self.map_file_publisher.unregister()
        self.vehicle_status_publisher.unregister()
        self.vehicle_info_publisher.unregister()
        self.waypoint_publisher.unregister()
        self.stack_process = None
        rospy.loginfo('Cleanup finished')

    def on_vehicle_control(self, data):
        """
        callback if a new vehicle control command is received
        """
        cmd = carla.VehicleControl()
        cmd.throttle = data.throttle
        cmd.steer = data.steer
        cmd.brake = data.brake
        cmd.hand_brake = data.hand_brake
        cmd.reverse = data.reverse
        cmd.gear = data.gear
        cmd.manual_gear_shift = data.manual_gear_shift
        self.current_control = cmd
        if not self.vehicle_control_event.is_set():
            self.vehicle_control_event.set()
        self.step_mode_possible = True

    def build_camera_info(self, attributes):
        """
        Private function to compute camera info

        camera info doesn't change over time
        """
        camera_info = CameraInfo()
        camera_info.header = None
        camera_info.width = int(attributes['width'])
        camera_info.height = int(attributes['height'])
        camera_info.distortion_model = 'plumb_bob'
        cx = camera_info.width / 2.0
        cy = camera_info.height / 2.0
        fx = camera_info.width / (2.0 * math.tan(float(attributes['fov']) * math.pi / 360.0))
        fy = fx
        camera_info.K = [fx, 0, cx, 0, fy, cy, 0, 0, 1]
        camera_info.D = [0, 0, 0, 0, 0]
        camera_info.R = [1.0, 0, 0, 0, 1.0, 0, 0, 0, 1.0]
        camera_info.P = [fx, 0, cx, 0, 0, fy, cy, 0, 0, 0, 1.0, 0]
        return camera_info

    def publish_plan(self):
        """
        publish the global plan
        """
        msg = Path()
        msg.header.frame_id = '/map'
        msg.header.stamp = rospy.Time.now()
        for wp in self._global_plan_world_coord:
            pose = PoseStamped()
            pose.pose.position.x = wp[0].location.x
            pose.pose.position.y = -wp[0].location.y
            pose.pose.position.z = wp[0].location.z
            quaternion = tf.transformations.quaternion_from_euler(0, 0, -math.radians(wp[0].rotation.yaw))
            pose.pose.orientation.x = quaternion[0]
            pose.pose.orientation.y = quaternion[1]
            pose.pose.orientation.z = quaternion[2]
            pose.pose.orientation.w = quaternion[3]
            msg.poses.append(pose)
        rospy.loginfo('Publishing Plan...')
        self.waypoint_publisher.publish(msg)

    def sensors(self):
        """
        Define the sensor suite required by the agent

        :return: a list containing the required sensors
        """
        raise NotImplementedError('This function has to be implemented by the derived classes')

    def get_header(self):
        """
        Returns ROS message header
        """
        header = Header()
        header.stamp = rospy.Time.from_sec(self.timestamp)
        return header

    def publish_lidar(self, sensor_id, data):
        """
        Function to publish lidar data
        """
        header = self.get_header()
        header.frame_id = 'ego_vehicle/lidar/{}'.format(sensor_id)
        lidar_data = numpy.frombuffer(data, dtype=numpy.float32)
        lidar_data = numpy.reshape(lidar_data, (int(lidar_data.shape[0] / 3), 3))
        lidar_data = -1.0 * lidar_data
        lidar_data = lidar_data[..., [1, 0, 2]]
        msg = create_cloud_xyz32(header, lidar_data)
        self.publisher_map[sensor_id].publish(msg)

    def publish_gnss(self, sensor_id, data):
        """
        Function to publish gnss data
        """
        msg = NavSatFix()
        msg.header = self.get_header()
        msg.header.frame_id = 'gps'
        msg.latitude = data[0]
        msg.longitude = data[1]
        msg.altitude = data[2]
        msg.status.status = NavSatStatus.STATUS_SBAS_FIX
        msg.status.service = NavSatStatus.SERVICE_GPS | NavSatStatus.SERVICE_GLONASS | NavSatStatus.SERVICE_COMPASS | NavSatStatus.SERVICE_GALILEO
        self.publisher_map[sensor_id].publish(msg)

    def publish_camera(self, sensor_id, data):
        """
        Function to publish camera data
        """
        msg = self.cv_bridge.cv2_to_imgmsg(data, encoding='bgra8')
        msg.header = self.get_header()
        msg.header.frame_id = 'ego_vehicle/camera/rgb/{}'.format(sensor_id)
        cam_info = self.id_to_camera_info_map[sensor_id]
        cam_info.header = msg.header
        self.publisher_map[sensor_id + '_info'].publish(cam_info)
        self.publisher_map[sensor_id].publish(msg)

    def publish_can(self, sensor_id, data):
        """
        publish can data
        """
        if not self.vehicle_info_publisher:
            self.vehicle_info_publisher = rospy.Publisher('/carla/ego_vehicle/vehicle_info', CarlaEgoVehicleInfo, queue_size=1, latch=True)
            info_msg = CarlaEgoVehicleInfo()
            for wheel in data['wheels']:
                wheel_info = CarlaEgoVehicleInfoWheel()
                wheel_info.tire_friction = wheel['tire_friction']
                wheel_info.damping_rate = wheel['damping_rate']
                wheel_info.steer_angle = wheel['steer_angle']
                wheel_info.disable_steering = wheel['disable_steering']
                info_msg.wheels.append(wheel_info)
            info_msg.max_rpm = data['max_rpm']
            info_msg.moi = data['moi']
            info_msg.damping_rate_full_throttle = data['damping_rate_full_throttle']
            info_msg.damping_rate_zero_throttle_clutch_disengaged = data['damping_rate_zero_throttle_clutch_disengaged']
            info_msg.use_gear_autobox = data['use_gear_autobox']
            info_msg.clutch_strength = data['clutch_strength']
            info_msg.mass = data['mass']
            info_msg.drag_coefficient = data['drag_coefficient']
            info_msg.center_of_mass.x = data['center_of_mass']['x']
            info_msg.center_of_mass.y = data['center_of_mass']['y']
            info_msg.center_of_mass.z = data['center_of_mass']['z']
            self.vehicle_info_publisher.publish(info_msg)
        msg = CarlaEgoVehicleStatus()
        msg.header = self.get_header()
        msg.velocity = data['speed']
        self.speed = data['speed']
        msg.control.throttle = self.current_control.throttle
        msg.control.steer = self.current_control.steer
        msg.control.brake = self.current_control.brake
        msg.control.hand_brake = self.current_control.hand_brake
        msg.control.reverse = self.current_control.reverse
        msg.control.gear = self.current_control.gear
        msg.control.manual_gear_shift = self.current_control.manual_gear_shift
        self.vehicle_status_publisher.publish(msg)

    def publish_hd_map(self, sensor_id, data):
        """
        publish hd map data
        """
        roll = -math.radians(data['transform']['roll'])
        pitch = -math.radians(data['transform']['pitch'])
        yaw = -math.radians(data['transform']['yaw'])
        quat = tf.transformations.quaternion_from_euler(roll, pitch, yaw)
        x = data['transform']['x']
        y = -data['transform']['y']
        z = data['transform']['z']
        if self.odometry_publisher:
            odometry = Odometry()
            odometry.header.frame_id = 'map'
            odometry.header.stamp = rospy.Time.from_sec(self.timestamp)
            odometry.child_frame_id = 'base_link'
            odometry.pose.pose.position.x = x
            odometry.pose.pose.position.y = y
            odometry.pose.pose.position.z = z
            odometry.pose.pose.orientation.x = quat[0]
            odometry.pose.pose.orientation.y = quat[1]
            odometry.pose.pose.orientation.z = quat[2]
            odometry.pose.pose.orientation.w = quat[3]
            odometry.twist.twist.linear.x = self.speed
            odometry.twist.twist.linear.y = 0
            odometry.twist.twist.linear.z = 0
            self.odometry_publisher.publish(odometry)
        if self.world_info_publisher:
            map_name = os.path.basename(data['map_file'])[:-4]
            if self.current_map_name != map_name:
                self.current_map_name = map_name
                world_info = CarlaWorldInfo()
                world_info.map_name = self.current_map_name
                world_info.opendrive = data['opendrive']
                self.world_info_publisher.publish(world_info)
        if self.map_file_publisher:
            self.map_file_publisher.publish(data['map_file'])

    def use_stepping_mode(self):
        """
        Overload this function to use stepping mode!
        """
        return False

    def run_step(self, input_data, timestamp):
        """
        Execute one step of navigation.
        """
        self.vehicle_control_event.clear()
        self.timestamp = timestamp
        self.clock_publisher.publish(Clock(rospy.Time.from_sec(timestamp)))
        if self.stack_process and self.stack_process.poll() is not None:
            raise RuntimeError('Stack exited with: {} {}'.format(self.stack_process.returncode, self.stack_process.communicate()[0]))
        if self._global_plan_world_coord and (not self.global_plan_published):
            self.global_plan_published = True
            self.publish_plan()
        new_data_available = False
        for key, val in input_data.items():
            new_data_available = True
            sensor_type = self.id_to_sensor_type_map[key]
            if sensor_type == 'sensor.camera.rgb':
                self.publish_camera(key, val[1])
            elif sensor_type == 'sensor.lidar.ray_cast':
                self.publish_lidar(key, val[1])
            elif sensor_type == 'sensor.other.gnss':
                self.publish_gnss(key, val[1])
            elif sensor_type == 'sensor.can_bus':
                self.publish_can(key, val[1])
            elif sensor_type == 'sensor.hd_map':
                self.publish_hd_map(key, val[1])
            else:
                raise TypeError('Invalid sensor type: {}'.format(sensor_type))
        if self.use_stepping_mode():
            if self.step_mode_possible and new_data_available:
                self.vehicle_control_event.wait()
        return self.current_control

def setup(self, path_to_conf_file):
    """
        setup agent
        """
    self.track = Track.MAP
    self.stack_thread = None
    team_code_path = os.environ['TEAM_CODE_ROOT']
    if not team_code_path or not os.path.exists(team_code_path):
        raise IOError("Path '{}' defined by TEAM_CODE_ROOT invalid".format(team_code_path))
    start_script = '{}/start.sh'.format(team_code_path)
    if not os.path.exists(start_script):
        raise IOError("File '{}' defined by TEAM_CODE_ROOT invalid".format(start_script))
    process = subprocess.Popen('rosparam set use_sim_time true', shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
    process.wait()
    if process.returncode:
        raise RuntimeError('Could not set use_sim_time')
    rospy.init_node('ros_agent', anonymous=True)
    self.clock_publisher = rospy.Publisher('clock', Clock, queue_size=10, latch=True)
    self.clock_publisher.publish(Clock(rospy.Time.from_sec(0)))
    rospy.loginfo('Executing stack...')
    self.stack_process = subprocess.Popen(start_script, shell=True, preexec_fn=os.setpgrp)
    self.vehicle_control_event = threading.Event()
    self.timestamp = None
    self.speed = 0
    self.global_plan_published = False
    self.vehicle_info_publisher = None
    self.vehicle_status_publisher = None
    self.odometry_publisher = None
    self.world_info_publisher = None
    self.map_file_publisher = None
    self.current_map_name = None
    self.tf_broadcaster = None
    self.step_mode_possible = False
    self.vehicle_control_subscriber = rospy.Subscriber('/carla/ego_vehicle/vehicle_control_cmd', CarlaEgoVehicleControl, self.on_vehicle_control)
    self.current_control = carla.VehicleControl()
    self.waypoint_publisher = rospy.Publisher('/carla/ego_vehicle/waypoints', Path, queue_size=1, latch=True)
    self.publisher_map = {}
    self.id_to_sensor_type_map = {}
    self.id_to_camera_info_map = {}
    self.cv_bridge = CvBridge()
    for sensor in self.sensors():
        self.id_to_sensor_type_map[sensor['id']] = sensor['type']
        if sensor['type'] == 'sensor.camera.rgb':
            self.publisher_map[sensor['id']] = rospy.Publisher('/carla/ego_vehicle/camera/rgb/' + sensor['id'] + '/image_color', Image, queue_size=1, latch=True)
            self.id_to_camera_info_map[sensor['id']] = self.build_camera_info(sensor)
            self.publisher_map[sensor['id'] + '_info'] = rospy.Publisher('/carla/ego_vehicle/camera/rgb/' + sensor['id'] + '/camera_info', CameraInfo, queue_size=1, latch=True)
        elif sensor['type'] == 'sensor.lidar.ray_cast':
            self.publisher_map[sensor['id']] = rospy.Publisher('/carla/ego_vehicle/lidar/' + sensor['id'] + '/point_cloud', PointCloud2, queue_size=1, latch=True)
        elif sensor['type'] == 'sensor.other.gnss':
            self.publisher_map[sensor['id']] = rospy.Publisher('/carla/ego_vehicle/gnss/' + sensor['id'] + '/fix', NavSatFix, queue_size=1, latch=True)
        elif sensor['type'] == 'sensor.can_bus':
            if not self.vehicle_info_publisher:
                self.vehicle_info_publisher = rospy.Publisher('/carla/ego_vehicle/vehicle_info', CarlaEgoVehicleInfo, queue_size=1, latch=True)
            if not self.vehicle_status_publisher:
                self.vehicle_status_publisher = rospy.Publisher('/carla/ego_vehicle/vehicle_status', CarlaEgoVehicleStatus, queue_size=1, latch=True)
        elif sensor['type'] == 'sensor.hd_map':
            if not self.odometry_publisher:
                self.odometry_publisher = rospy.Publisher('/carla/ego_vehicle/odometry', Odometry, queue_size=1, latch=True)
            if not self.world_info_publisher:
                self.world_info_publisher = rospy.Publisher('/carla/world_info', CarlaWorldInfo, queue_size=1, latch=True)
            if not self.map_file_publisher:
                self.map_file_publisher = rospy.Publisher('/carla/map_file', String, queue_size=1, latch=True)
            if not self.tf_broadcaster:
                self.tf_broadcaster = tf.TransformBroadcaster()
        else:
            raise TypeError('Invalid sensor type: {}'.format(sensor['type']))

def destroy(self):
    """
        Cleanup of all ROS publishers
        """
    if self.stack_process and self.stack_process.poll() is None:
        rospy.loginfo('Sending SIGTERM to stack...')
        os.killpg(os.getpgid(self.stack_process.pid), signal.SIGTERM)
        rospy.loginfo('Waiting for termination of stack...')
        self.stack_process.wait()
        time.sleep(5)
        rospy.loginfo('Terminated stack.')
    rospy.loginfo('Stack is no longer running')
    self.world_info_publisher.unregister()
    self.map_file_publisher.unregister()
    self.vehicle_status_publisher.unregister()
    self.vehicle_info_publisher.unregister()
    self.waypoint_publisher.unregister()
    self.stack_process = None
    rospy.loginfo('Cleanup finished')

def publish_plan(self):
    """
        publish the global plan
        """
    msg = Path()
    msg.header.frame_id = '/map'
    msg.header.stamp = rospy.Time.now()
    for wp in self._global_plan_world_coord:
        pose = PoseStamped()
        pose.pose.position.x = wp[0].location.x
        pose.pose.position.y = -wp[0].location.y
        pose.pose.position.z = wp[0].location.z
        quaternion = tf.transformations.quaternion_from_euler(0, 0, -math.radians(wp[0].rotation.yaw))
        pose.pose.orientation.x = quaternion[0]
        pose.pose.orientation.y = quaternion[1]
        pose.pose.orientation.z = quaternion[2]
        pose.pose.orientation.w = quaternion[3]
        msg.poses.append(pose)
    rospy.loginfo('Publishing Plan...')
    self.waypoint_publisher.publish(msg)

def get_header(self):
    """
        Returns ROS message header
        """
    header = Header()
    header.stamp = rospy.Time.from_sec(self.timestamp)
    return header

def publish_lidar(self, sensor_id, data):
    """
        Function to publish lidar data
        """
    header = self.get_header()
    header.frame_id = 'ego_vehicle/lidar/{}'.format(sensor_id)
    lidar_data = numpy.frombuffer(data, dtype=numpy.float32)
    lidar_data = numpy.reshape(lidar_data, (int(lidar_data.shape[0] / 3), 3))
    lidar_data = -1.0 * lidar_data
    lidar_data = lidar_data[..., [1, 0, 2]]
    msg = create_cloud_xyz32(header, lidar_data)
    self.publisher_map[sensor_id].publish(msg)

def publish_gnss(self, sensor_id, data):
    """
        Function to publish gnss data
        """
    msg = NavSatFix()
    msg.header = self.get_header()
    msg.header.frame_id = 'gps'
    msg.latitude = data[0]
    msg.longitude = data[1]
    msg.altitude = data[2]
    msg.status.status = NavSatStatus.STATUS_SBAS_FIX
    msg.status.service = NavSatStatus.SERVICE_GPS | NavSatStatus.SERVICE_GLONASS | NavSatStatus.SERVICE_COMPASS | NavSatStatus.SERVICE_GALILEO
    self.publisher_map[sensor_id].publish(msg)

def publish_camera(self, sensor_id, data):
    """
        Function to publish camera data
        """
    msg = self.cv_bridge.cv2_to_imgmsg(data, encoding='bgra8')
    msg.header = self.get_header()
    msg.header.frame_id = 'ego_vehicle/camera/rgb/{}'.format(sensor_id)
    cam_info = self.id_to_camera_info_map[sensor_id]
    cam_info.header = msg.header
    self.publisher_map[sensor_id + '_info'].publish(cam_info)
    self.publisher_map[sensor_id].publish(msg)

def publish_can(self, sensor_id, data):
    """
        publish can data
        """
    if not self.vehicle_info_publisher:
        self.vehicle_info_publisher = rospy.Publisher('/carla/ego_vehicle/vehicle_info', CarlaEgoVehicleInfo, queue_size=1, latch=True)
        info_msg = CarlaEgoVehicleInfo()
        for wheel in data['wheels']:
            wheel_info = CarlaEgoVehicleInfoWheel()
            wheel_info.tire_friction = wheel['tire_friction']
            wheel_info.damping_rate = wheel['damping_rate']
            wheel_info.steer_angle = wheel['steer_angle']
            wheel_info.disable_steering = wheel['disable_steering']
            info_msg.wheels.append(wheel_info)
        info_msg.max_rpm = data['max_rpm']
        info_msg.moi = data['moi']
        info_msg.damping_rate_full_throttle = data['damping_rate_full_throttle']
        info_msg.damping_rate_zero_throttle_clutch_disengaged = data['damping_rate_zero_throttle_clutch_disengaged']
        info_msg.use_gear_autobox = data['use_gear_autobox']
        info_msg.clutch_strength = data['clutch_strength']
        info_msg.mass = data['mass']
        info_msg.drag_coefficient = data['drag_coefficient']
        info_msg.center_of_mass.x = data['center_of_mass']['x']
        info_msg.center_of_mass.y = data['center_of_mass']['y']
        info_msg.center_of_mass.z = data['center_of_mass']['z']
        self.vehicle_info_publisher.publish(info_msg)
    msg = CarlaEgoVehicleStatus()
    msg.header = self.get_header()
    msg.velocity = data['speed']
    self.speed = data['speed']
    msg.control.throttle = self.current_control.throttle
    msg.control.steer = self.current_control.steer
    msg.control.brake = self.current_control.brake
    msg.control.hand_brake = self.current_control.hand_brake
    msg.control.reverse = self.current_control.reverse
    msg.control.gear = self.current_control.gear
    msg.control.manual_gear_shift = self.current_control.manual_gear_shift
    self.vehicle_status_publisher.publish(msg)

def publish_hd_map(self, sensor_id, data):
    """
        publish hd map data
        """
    roll = -math.radians(data['transform']['roll'])
    pitch = -math.radians(data['transform']['pitch'])
    yaw = -math.radians(data['transform']['yaw'])
    quat = tf.transformations.quaternion_from_euler(roll, pitch, yaw)
    x = data['transform']['x']
    y = -data['transform']['y']
    z = data['transform']['z']
    if self.odometry_publisher:
        odometry = Odometry()
        odometry.header.frame_id = 'map'
        odometry.header.stamp = rospy.Time.from_sec(self.timestamp)
        odometry.child_frame_id = 'base_link'
        odometry.pose.pose.position.x = x
        odometry.pose.pose.position.y = y
        odometry.pose.pose.position.z = z
        odometry.pose.pose.orientation.x = quat[0]
        odometry.pose.pose.orientation.y = quat[1]
        odometry.pose.pose.orientation.z = quat[2]
        odometry.pose.pose.orientation.w = quat[3]
        odometry.twist.twist.linear.x = self.speed
        odometry.twist.twist.linear.y = 0
        odometry.twist.twist.linear.z = 0
        self.odometry_publisher.publish(odometry)
    if self.world_info_publisher:
        map_name = os.path.basename(data['map_file'])[:-4]
        if self.current_map_name != map_name:
            self.current_map_name = map_name
            world_info = CarlaWorldInfo()
            world_info.map_name = self.current_map_name
            world_info.opendrive = data['opendrive']
            self.world_info_publisher.publish(world_info)
    if self.map_file_publisher:
        self.map_file_publisher.publish(data['map_file'])

def run_step(self, input_data, timestamp):
    """
        Execute one step of navigation.
        """
    self.vehicle_control_event.clear()
    self.timestamp = timestamp
    self.clock_publisher.publish(Clock(rospy.Time.from_sec(timestamp)))
    if self.stack_process and self.stack_process.poll() is not None:
        raise RuntimeError('Stack exited with: {} {}'.format(self.stack_process.returncode, self.stack_process.communicate()[0]))
    if self._global_plan_world_coord and (not self.global_plan_published):
        self.global_plan_published = True
        self.publish_plan()
    new_data_available = False
    for key, val in input_data.items():
        new_data_available = True
        sensor_type = self.id_to_sensor_type_map[key]
        if sensor_type == 'sensor.camera.rgb':
            self.publish_camera(key, val[1])
        elif sensor_type == 'sensor.lidar.ray_cast':
            self.publish_lidar(key, val[1])
        elif sensor_type == 'sensor.other.gnss':
            self.publish_gnss(key, val[1])
        elif sensor_type == 'sensor.can_bus':
            self.publish_can(key, val[1])
        elif sensor_type == 'sensor.hd_map':
            self.publish_hd_map(key, val[1])
        else:
            raise TypeError('Invalid sensor type: {}'.format(sensor_type))
    if self.use_stepping_mode():
        if self.step_mode_possible and new_data_available:
            self.vehicle_control_event.wait()
    return self.current_control

class GameTime(object):
    """
    This (static) class provides access to the CARLA game time.

    The elapsed game time can be simply retrieved by calling:
    GameTime.get_time()
    """
    _current_game_time = 0.0
    _carla_time = 0.0
    _last_frame = 0
    _platform_timestamp = 0
    _init = False

    @staticmethod
    def on_carla_tick(timestamp):
        """
        Callback receiving the CARLA time
        Update time only when frame is more recent that last frame
        """
        if GameTime._last_frame < timestamp.frame:
            frames = timestamp.frame - GameTime._last_frame if GameTime._init else 1
            GameTime._current_game_time += timestamp.delta_seconds * frames
            GameTime._last_frame = timestamp.frame
            GameTime._platform_timestamp = datetime.datetime.now()
            GameTime._init = True
            GameTime._carla_time = timestamp.elapsed_seconds

    @staticmethod
    def restart():
        """
        Reset game timer to 0
        """
        GameTime._current_game_time = 0.0
        GameTime._init = False

    @staticmethod
    def get_time():
        """
        Returns elapsed game time
        """
        return GameTime._current_game_time

    @staticmethod
    def get_carla_time():
        """
        Returns elapsed game time
        """
        return GameTime._carla_time

    @staticmethod
    def get_wallclocktime():
        """
        Returns elapsed game time
        """
        return GameTime._platform_timestamp

    @staticmethod
    def get_frame():
        """
        Returns elapsed game time
        """
        return GameTime._last_frame

@staticmethod
def on_carla_tick(timestamp):
    """
        Callback receiving the CARLA time
        Update time only when frame is more recent that last frame
        """
    if GameTime._last_frame < timestamp.frame:
        frames = timestamp.frame - GameTime._last_frame if GameTime._init else 1
        GameTime._current_game_time += timestamp.delta_seconds * frames
        GameTime._last_frame = timestamp.frame
        GameTime._platform_timestamp = datetime.datetime.now()
        GameTime._init = True
        GameTime._carla_time = timestamp.elapsed_seconds

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

def get_running_status(self):
    """
        returns:
           bool:  False if watchdog exception occured, True otherwise
        """
    return self._watchdog.get_status()

class SimpleVehicleControl(BasicControl):
    """
    Controller class for vehicles derived from BasicControl.

    The controller directly sets velocities in CARLA, therefore bypassing
    CARLA's vehicle engine. This allows a very precise speed control, but comes
    with limitations during cornering.

    In addition, the controller can consider blocking obstacles, which are
    classified as dynamic (i.e. vehicles, bikes, pedestrians). Activation of this
    features is controlled by passing proper arguments to the class constructor.
    The collision detection uses CARLA's obstacle sensor (sensor.other.obstacle),
    which checks for obstacles in the direct forward channel of the vehicle, i.e.
    there are limitation with sideways obstacles and while cornering.

    Args:
        actor (carla.Actor): Vehicle actor that should be controlled.
        args (dictionary): Dictonary of (key, value) arguments to be used by the controller.
                           May include: (consider_obstacles, true/false) - Enable consideration of obstacles
                                        (proximity_threshold, distance)  - Distance in front of actor in which
                                                                           obstacles are considered
                                        (attach_camera, true/false)      - Attach OpenCV display to actor
                                                                           (useful for debugging)

    Attributes:

        _generated_waypoint_list (list of carla.Transform): List of target waypoints the actor
            should travel along. A waypoint here is of type carla.Transform!
            Defaults to [].
        _last_update (float): Last time step the update function (tick()) was called.
            Defaults to None.
        _consider_obstacles (boolean): Enable/Disable consideration of obstacles
            Defaults to False.
        _proximity_threshold (float): Distance in front of actor in which obstacles are considered
            Defaults to infinity.
        _cv_image (CV Image): Contains the OpenCV image, in case a debug camera is attached to the actor
            Defaults to None.
        _camera (sensor.camera.rgb): Debug camera attached to actor
            Defaults to None.
        _obstacle_sensor (sensor.other.obstacle): Obstacle sensor attached to actor
            Defaults to None.
        _obstacle_distance (float): Distance of the closest obstacle returned by the obstacle sensor
            Defaults to infinity.
        _obstacle_actor (carla.Actor): Closest obstacle returned by the obstacle sensor
            Defaults to None.
    """

    def __init__(self, actor, args=None):
        super(SimpleVehicleControl, self).__init__(actor)
        self._generated_waypoint_list = []
        self._last_update = None
        self._consider_obstacles = False
        self._proximity_threshold = float('inf')
        self._cv_image = None
        self._camera = None
        self._obstacle_sensor = None
        self._obstacle_distance = float('inf')
        self._obstacle_actor = None
        if args and 'consider_obstacles' in args and strtobool(args['consider_obstacles']):
            self._consider_obstacles = strtobool(args['consider_obstacles'])
            bp = CarlaDataProvider.get_world().get_blueprint_library().find('sensor.other.obstacle')
            bp.set_attribute('distance', '250')
            if args and 'proximity_threshold' in args:
                self._proximity_threshold = float(args['proximity_threshold'])
                bp.set_attribute('distance', str(max(float(args['proximity_threshold']), 250)))
            bp.set_attribute('hit_radius', '1')
            bp.set_attribute('only_dynamics', 'True')
            self._obstacle_sensor = CarlaDataProvider.get_world().spawn_actor(bp, carla.Transform(carla.Location(x=self._actor.bounding_box.extent.x, z=1.0)), attach_to=self._actor)
            self._obstacle_sensor.listen(lambda event: self._on_obstacle(event))
        if args and 'attach_camera' in args and strtobool(args['attach_camera']):
            bp = CarlaDataProvider.get_world().get_blueprint_library().find('sensor.camera.rgb')
            self._camera = CarlaDataProvider.get_world().spawn_actor(bp, carla.Transform(carla.Location(x=0.0, z=30.0), carla.Rotation(pitch=-60)), attach_to=self._actor)
            self._camera.listen(lambda image: self._on_camera_update(image))

    def _on_obstacle(self, event):
        """
        Callback for the obstacle sensor

        Sets _obstacle_distance and _obstacle_actor according to the closest obstacle
        found by the sensor.
        """
        if not event:
            return
        self._obstacle_distance = event.distance
        self._obstacle_actor = event.other_actor

    def _on_camera_update(self, image):
        """
        Callback for the camera sensor

        Sets the OpenCV image (_cv_image). Requires conversion from BGRA to RGB.
        """
        if not image:
            return
        image_data = np.frombuffer(image.raw_data, dtype=np.dtype('uint8'))
        np_image = np.reshape(image_data, (image.height, image.width, 4))
        np_image = np_image[:, :, :3]
        np_image = np_image[:, :, ::-1]
        self._cv_image = cv2.cvtColor(np_image, cv2.COLOR_BGR2RGB)

    def reset(self):
        """
        Reset the controller
        """
        if self._camera:
            self._camera.destroy()
            self._camera = None
        if self._obstacle_sensor:
            self._obstacle_sensor.destroy()
            self._obstacle_sensor = None
        if self._actor and self._actor.is_alive:
            self._actor = None

    def run_step(self):
        """
        Execute on tick of the controller's control loop

        If _waypoints are provided, the vehicle moves towards the next waypoint
        with the given _target_speed, until reaching the final waypoint. Upon reaching
        the final waypoint, _reached_goal is set to True.

        If _waypoints is empty, the vehicle moves in its current direction with
        the given _target_speed.

        If _consider_obstacles is true, the speed is adapted according to the closest
        obstacle in front of the actor, if it is within the _proximity_threshold distance.
        """
        if self._cv_image is not None:
            cv2.imshow('', self._cv_image)
            cv2.waitKey(1)
        if self._reached_goal:
            velocity = carla.Vector3D(0, 0, 0)
            self._actor.set_target_velocity(velocity)
            return
        self._reached_goal = False
        if not self._waypoints:
            self._reached_goal = False
            map_wp = None
            if not self._generated_waypoint_list:
                map_wp = CarlaDataProvider.get_map().get_waypoint(CarlaDataProvider.get_location(self._actor))
            else:
                map_wp = CarlaDataProvider.get_map().get_waypoint(self._generated_waypoint_list[-1].location)
            while len(self._generated_waypoint_list) < 50:
                map_wps = map_wp.next(3.0)
                if map_wps:
                    self._generated_waypoint_list.append(map_wps[0].transform)
                    map_wp = map_wps[0]
                else:
                    break
            direction_norm = self._set_new_velocity(self._generated_waypoint_list[0].location)
            if direction_norm < 2.0:
                self._generated_waypoint_list = self._generated_waypoint_list[1:]
        else:
            while self._waypoints and self._waypoints[0].location.distance(self._actor.get_location()) < 0.5:
                self._waypoints = self._waypoints[1:]
            self._reached_goal = False
            direction_norm = self._set_new_velocity(self._waypoints[0].location)
            if direction_norm < 4.0:
                self._waypoints = self._waypoints[1:]
                if not self._waypoints:
                    self._reached_goal = True

    def _set_new_velocity(self, next_location):
        """
        Calculate and set the new actor veloctiy given the current actor
        location and the _next_location_

        If _consider_obstacles is true, the speed is adapted according to the closest
        obstacle in front of the actor, if it is within the _proximity_threshold distance.

        Args:
            next_location (carla.Location): Next target location of the actor

        returns:
            direction (carla.Vector3D): Length of direction vector of the actor
        """
        current_time = GameTime.get_time()
        target_speed = self._target_speed
        if not self._last_update:
            self._last_update = current_time
        if self._consider_obstacles:
            if self._obstacle_distance < self._proximity_threshold:
                distance = max(self._obstacle_distance, 0)
                if distance > 0:
                    current_speed = math.sqrt(self._actor.get_velocity().x ** 2 + self._actor.get_velocity().y ** 2)
                    current_speed_other = math.sqrt(self._obstacle_actor.get_velocity().x ** 2 + self._obstacle_actor.get_velocity().y ** 2)
                    if current_speed_other < current_speed:
                        acceleration = -0.5 * (current_speed - current_speed_other) ** 2 / distance
                        target_speed = max(acceleration * (current_time - self._last_update) + current_speed, 0)
                else:
                    target_speed = 0
        velocity = carla.Vector3D(0, 0, 0)
        direction = next_location - CarlaDataProvider.get_location(self._actor)
        direction_norm = math.sqrt(direction.x ** 2 + direction.y ** 2)
        velocity.x = direction.x / direction_norm * target_speed
        velocity.y = direction.y / direction_norm * target_speed
        self._actor.set_target_velocity(velocity)
        current_yaw = CarlaDataProvider.get_transform(self._actor).rotation.yaw
        if self._waypoints:
            delta_yaw = math.degrees(math.atan2(direction.y, direction.x)) - current_yaw
        else:
            new_yaw = CarlaDataProvider.get_map().get_waypoint(next_location).transform.rotation.yaw
            delta_yaw = new_yaw - current_yaw
        if math.fabs(delta_yaw) > 360:
            delta_yaw = delta_yaw % 360
        if delta_yaw > 180:
            delta_yaw = delta_yaw - 360
        elif delta_yaw < -180:
            delta_yaw = delta_yaw + 360
        angular_velocity = carla.Vector3D(0, 0, 0)
        if target_speed == 0:
            angular_velocity.z = 0
        else:
            angular_velocity.z = delta_yaw / (direction_norm / target_speed)
        self._actor.set_target_angular_velocity(angular_velocity)
        self._last_update = current_time
        return direction_norm

def _on_camera_update(self, image):
    """
        Callback for the camera sensor

        Sets the OpenCV image (_cv_image). Requires conversion from BGRA to RGB.
        """
    if not image:
        return
    image_data = np.frombuffer(image.raw_data, dtype=np.dtype('uint8'))
    np_image = np.reshape(image_data, (image.height, image.width, 4))
    np_image = np_image[:, :, :3]
    np_image = np_image[:, :, ::-1]
    self._cv_image = cv2.cvtColor(np_image, cv2.COLOR_BGR2RGB)

class HumanAgent(AutonomousAgent):
    """
    Human agent to control the ego vehicle via keyboard
    """
    current_control = None
    agent_engaged = False

    def setup(self, path_to_conf_file):
        """
        Setup the agent parameters
        """
        self.agent_engaged = False
        self.current_control = carla.VehicleControl()
        self.current_control.steer = 0.0
        self.current_control.throttle = 1.0
        self.current_control.brake = 0.0
        self.current_control.hand_brake = False
        self._hic = HumanInterface(self)
        self._thread = Thread(target=self._hic.run)
        self._thread.start()

    def sensors(self):
        """
        Define the sensor suite required by the agent

        :return: a list containing the required sensors in the following format:

        [
            ['sensor.camera.rgb', {'x':x_rel, 'y': y_rel, 'z': z_rel,
                                   'yaw': yaw, 'pitch': pitch, 'roll': roll,
                                   'width': width, 'height': height, 'fov': fov}, 'Sensor01'],
            ['sensor.camera.rgb', {'x':x_rel, 'y': y_rel, 'z': z_rel,
                                   'yaw': yaw, 'pitch': pitch, 'roll': roll,
                                   'width': width, 'height': height, 'fov': fov}, 'Sensor02'],

            ['sensor.lidar.ray_cast', {'x':x_rel, 'y': y_rel, 'z': z_rel,
                                       'yaw': yaw, 'pitch': pitch, 'roll': roll}, 'Sensor03']
        ]

        """
        sensors = [{'type': 'sensor.camera.rgb', 'x': 0.7, 'y': 0.0, 'z': 1.6, 'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0, 'width': 300, 'height': 200, 'fov': 100, 'id': 'Center'}, {'type': 'sensor.camera.rgb', 'x': 0.7, 'y': -0.4, 'z': 1.6, 'roll': 0.0, 'pitch': 0.0, 'yaw': -45.0, 'width': 300, 'height': 200, 'fov': 100, 'id': 'Left'}, {'type': 'sensor.camera.rgb', 'x': 0.7, 'y': 0.4, 'z': 1.6, 'roll': 0.0, 'pitch': 0.0, 'yaw': 45.0, 'width': 300, 'height': 200, 'fov': 100, 'id': 'Right'}, {'type': 'sensor.camera.rgb', 'x': -1.8, 'y': 0, 'z': 1.6, 'roll': 0.0, 'pitch': 0.0, 'yaw': 180.0, 'width': 300, 'height': 200, 'fov': 130, 'id': 'Rear'}, {'type': 'sensor.other.gnss', 'x': 0.7, 'y': -0.4, 'z': 1.6, 'id': 'GPS'}]
        return sensors

    def run_step(self, input_data, timestamp):
        """
        Execute one step of navigation.
        """
        self.agent_engaged = True
        time.sleep(0.1)
        return self.current_control

    def destroy(self):
        """
        Cleanup
        """
        self._hic.quit = True
        self._thread.join()

def run_step(self, input_data, timestamp):
    """
        Execute one step of navigation.
        """
    self.agent_engaged = True
    time.sleep(0.1)
    return self.current_control

class CallBack(object):
    """
    Class the sensors listen to in order to receive their data each frame
    """

    def __init__(self, tag, sensor, data_provider):
        """
        Initializes the call back
        """
        self._tag = tag
        self._data_provider = data_provider
        self._data_provider.register_sensor(tag, sensor)

    def __call__(self, data):
        """
        call function
        """
        if isinstance(data, carla.Image):
            self._parse_image_cb(data, self._tag)
        elif isinstance(data, carla.LidarMeasurement):
            self._parse_lidar_cb(data, self._tag)
        elif isinstance(data, carla.GnssMeasurement):
            self._parse_gnss_cb(data, self._tag)
        else:
            logging.error('No callback method for this sensor.')

    def _parse_image_cb(self, image, tag):
        """
        parses cameras
        """
        array = np.frombuffer(image.raw_data, dtype=np.dtype('uint8'))
        array = copy.deepcopy(array)
        array = np.reshape(array, (image.height, image.width, 4))
        self._data_provider.update_sensor(tag, array, image.frame)

    def _parse_lidar_cb(self, lidar_data, tag):
        """
        parses lidar sensors
        """
        points = np.frombuffer(lidar_data.raw_data, dtype=np.dtype('f4'))
        points = copy.deepcopy(points)
        points = np.reshape(points, (int(points.shape[0] / 3), 3))
        self._data_provider.update_sensor(tag, points, lidar_data.frame)

    def _parse_gnss_cb(self, gnss_data, tag):
        """
        parses gnss sensors
        """
        array = np.array([gnss_data.latitude, gnss_data.longitude, gnss_data.altitude], dtype=np.float64)
        self._data_provider.update_sensor(tag, array, gnss_data.frame)

def _parse_image_cb(self, image, tag):
    """
        parses cameras
        """
    array = np.frombuffer(image.raw_data, dtype=np.dtype('uint8'))
    array = copy.deepcopy(array)
    array = np.reshape(array, (image.height, image.width, 4))
    self._data_provider.update_sensor(tag, array, image.frame)

def _parse_lidar_cb(self, lidar_data, tag):
    """
        parses lidar sensors
        """
    points = np.frombuffer(lidar_data.raw_data, dtype=np.dtype('f4'))
    points = copy.deepcopy(points)
    points = np.reshape(points, (int(points.shape[0] / 3), 3))
    self._data_provider.update_sensor(tag, points, lidar_data.frame)

def _parse_gnss_cb(self, gnss_data, tag):
    """
        parses gnss sensors
        """
    array = np.array([gnss_data.latitude, gnss_data.longitude, gnss_data.altitude], dtype=np.float64)
    self._data_provider.update_sensor(tag, array, gnss_data.frame)

class RosAgent(AutonomousAgent):
    """
    Base class for ROS-based stacks.

    Derive from it and implement the sensors() method.

    Please define TEAM_CODE_ROOT in your environment.
    The stack is started by executing $TEAM_CODE_ROOT/start.sh

    The sensor data is published on similar topics as with the carla-ros-bridge. You can find details about
    the utilized datatypes there.

    This agent expects a roscore to be running.
    """
    speed = None
    current_control = None
    stack_process = None
    timestamp = None
    current_map_name = None
    step_mode_possible = None
    vehicle_info_publisher = None
    global_plan_published = None

    def setup(self, path_to_conf_file):
        """
        setup agent
        """
        self.stack_thread = None
        team_code_path = os.environ['TEAM_CODE_ROOT']
        if not team_code_path or not os.path.exists(team_code_path):
            raise IOError("Path '{}' defined by TEAM_CODE_ROOT invalid".format(team_code_path))
        start_script = '{}/start.sh'.format(team_code_path)
        if not os.path.exists(start_script):
            raise IOError("File '{}' defined by TEAM_CODE_ROOT invalid".format(start_script))
        process = subprocess.Popen('rosparam set use_sim_time true', shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        process.wait()
        if process.returncode:
            raise RuntimeError('Could not set use_sim_time')
        rospy.init_node('ros_agent', anonymous=True)
        self.clock_publisher = rospy.Publisher('clock', Clock, queue_size=10, latch=True)
        self.clock_publisher.publish(Clock(rospy.Time.from_sec(0)))
        rospy.loginfo('Executing stack...')
        self.stack_process = subprocess.Popen(start_script, shell=True, preexec_fn=os.setpgrp)
        self.vehicle_control_event = threading.Event()
        self.timestamp = None
        self.speed = 0
        self.global_plan_published = False
        self.vehicle_info_publisher = None
        self.vehicle_status_publisher = None
        self.odometry_publisher = None
        self.world_info_publisher = None
        self.map_file_publisher = None
        self.current_map_name = None
        self.tf_broadcaster = None
        self.step_mode_possible = False
        self.vehicle_control_subscriber = rospy.Subscriber('/carla/ego_vehicle/vehicle_control_cmd', CarlaEgoVehicleControl, self.on_vehicle_control)
        self.current_control = carla.VehicleControl()
        self.waypoint_publisher = rospy.Publisher('/carla/ego_vehicle/waypoints', Path, queue_size=1, latch=True)
        self.publisher_map = {}
        self.id_to_sensor_type_map = {}
        self.id_to_camera_info_map = {}
        self.cv_bridge = CvBridge()
        for sensor in self.sensors():
            self.id_to_sensor_type_map[sensor['id']] = sensor['type']
            if sensor['type'] == 'sensor.camera.rgb':
                self.publisher_map[sensor['id']] = rospy.Publisher('/carla/ego_vehicle/camera/rgb/' + sensor['id'] + '/image_color', Image, queue_size=1, latch=True)
                self.id_to_camera_info_map[sensor['id']] = self.build_camera_info(sensor)
                self.publisher_map[sensor['id'] + '_info'] = rospy.Publisher('/carla/ego_vehicle/camera/rgb/' + sensor['id'] + '/camera_info', CameraInfo, queue_size=1, latch=True)
            elif sensor['type'] == 'sensor.lidar.ray_cast':
                self.publisher_map[sensor['id']] = rospy.Publisher('/carla/ego_vehicle/lidar/' + sensor['id'] + '/point_cloud', PointCloud2, queue_size=1, latch=True)
            elif sensor['type'] == 'sensor.other.gnss':
                self.publisher_map[sensor['id']] = rospy.Publisher('/carla/ego_vehicle/gnss/' + sensor['id'] + '/fix', NavSatFix, queue_size=1, latch=True)
            elif sensor['type'] == 'sensor.can_bus':
                if not self.vehicle_info_publisher:
                    self.vehicle_info_publisher = rospy.Publisher('/carla/ego_vehicle/vehicle_info', CarlaEgoVehicleInfo, queue_size=1, latch=True)
                if not self.vehicle_status_publisher:
                    self.vehicle_status_publisher = rospy.Publisher('/carla/ego_vehicle/vehicle_status', CarlaEgoVehicleStatus, queue_size=1, latch=True)
            elif sensor['type'] == 'sensor.hd_map':
                if not self.odometry_publisher:
                    self.odometry_publisher = rospy.Publisher('/carla/ego_vehicle/odometry', Odometry, queue_size=1, latch=True)
                if not self.world_info_publisher:
                    self.world_info_publisher = rospy.Publisher('/carla/world_info', CarlaWorldInfo, queue_size=1, latch=True)
                if not self.map_file_publisher:
                    self.map_file_publisher = rospy.Publisher('/carla/map_file', String, queue_size=1, latch=True)
                if not self.tf_broadcaster:
                    self.tf_broadcaster = tf.TransformBroadcaster()
            else:
                raise TypeError('Invalid sensor type: {}'.format(sensor['type']))

    def destroy(self):
        """
        Cleanup of all ROS publishers
        """
        if self.stack_process and self.stack_process.poll() is None:
            rospy.loginfo('Sending SIGTERM to stack...')
            os.killpg(os.getpgid(self.stack_process.pid), signal.SIGTERM)
            rospy.loginfo('Waiting for termination of stack...')
            self.stack_process.wait()
            time.sleep(5)
            rospy.loginfo('Terminated stack.')
        rospy.loginfo('Stack is no longer running')
        self.world_info_publisher.unregister()
        self.map_file_publisher.unregister()
        self.vehicle_status_publisher.unregister()
        self.vehicle_info_publisher.unregister()
        self.waypoint_publisher.unregister()
        self.stack_process = None
        rospy.loginfo('Cleanup finished')

    def on_vehicle_control(self, data):
        """
        callback if a new vehicle control command is received
        """
        cmd = carla.VehicleControl()
        cmd.throttle = data.throttle
        cmd.steer = data.steer
        cmd.brake = data.brake
        cmd.hand_brake = data.hand_brake
        cmd.reverse = data.reverse
        cmd.gear = data.gear
        cmd.manual_gear_shift = data.manual_gear_shift
        self.current_control = cmd
        if not self.vehicle_control_event.is_set():
            self.vehicle_control_event.set()
        self.step_mode_possible = True

    def build_camera_info(self, attributes):
        """
        Private function to compute camera info

        camera info doesn't change over time
        """
        camera_info = CameraInfo()
        camera_info.header = None
        camera_info.width = int(attributes['width'])
        camera_info.height = int(attributes['height'])
        camera_info.distortion_model = 'plumb_bob'
        cx = camera_info.width / 2.0
        cy = camera_info.height / 2.0
        fx = camera_info.width / (2.0 * math.tan(float(attributes['fov']) * math.pi / 360.0))
        fy = fx
        camera_info.K = [fx, 0, cx, 0, fy, cy, 0, 0, 1]
        camera_info.D = [0, 0, 0, 0, 0]
        camera_info.R = [1.0, 0, 0, 0, 1.0, 0, 0, 0, 1.0]
        camera_info.P = [fx, 0, cx, 0, 0, fy, cy, 0, 0, 0, 1.0, 0]
        return camera_info

    def publish_plan(self):
        """
        publish the global plan
        """
        msg = Path()
        msg.header.frame_id = '/map'
        msg.header.stamp = rospy.Time.now()
        for wp in self._global_plan_world_coord:
            pose = PoseStamped()
            pose.pose.position.x = wp[0].location.x
            pose.pose.position.y = -wp[0].location.y
            pose.pose.position.z = wp[0].location.z
            quaternion = tf.transformations.quaternion_from_euler(0, 0, -math.radians(wp[0].rotation.yaw))
            pose.pose.orientation.x = quaternion[0]
            pose.pose.orientation.y = quaternion[1]
            pose.pose.orientation.z = quaternion[2]
            pose.pose.orientation.w = quaternion[3]
            msg.poses.append(pose)
        rospy.loginfo('Publishing Plan...')
        self.waypoint_publisher.publish(msg)

    def sensors(self):
        """
        Define the sensor suite required by the agent

        :return: a list containing the required sensors
        """
        raise NotImplementedError('This function has to be implemented by the derived classes')

    def get_header(self):
        """
        Returns ROS message header
        """
        header = Header()
        header.stamp = rospy.Time.from_sec(self.timestamp)
        return header

    def publish_lidar(self, sensor_id, data):
        """
        Function to publish lidar data
        """
        header = self.get_header()
        header.frame_id = 'ego_vehicle/lidar/{}'.format(sensor_id)
        lidar_data = numpy.frombuffer(data, dtype=numpy.float32)
        lidar_data = numpy.reshape(lidar_data, (int(lidar_data.shape[0] / 3), 3))
        lidar_data = -1.0 * lidar_data
        lidar_data = lidar_data[..., [1, 0, 2]]
        msg = create_cloud_xyz32(header, lidar_data)
        self.publisher_map[sensor_id].publish(msg)

    def publish_gnss(self, sensor_id, data):
        """
        Function to publish gnss data
        """
        msg = NavSatFix()
        msg.header = self.get_header()
        msg.header.frame_id = 'gps'
        msg.latitude = data[0]
        msg.longitude = data[1]
        msg.altitude = data[2]
        msg.status.status = NavSatStatus.STATUS_SBAS_FIX
        msg.status.service = NavSatStatus.SERVICE_GPS | NavSatStatus.SERVICE_GLONASS | NavSatStatus.SERVICE_COMPASS | NavSatStatus.SERVICE_GALILEO
        self.publisher_map[sensor_id].publish(msg)

    def publish_camera(self, sensor_id, data):
        """
        Function to publish camera data
        """
        msg = self.cv_bridge.cv2_to_imgmsg(data, encoding='bgra8')
        msg.header = self.get_header()
        msg.header.frame_id = 'ego_vehicle/camera/rgb/{}'.format(sensor_id)
        cam_info = self.id_to_camera_info_map[sensor_id]
        cam_info.header = msg.header
        self.publisher_map[sensor_id + '_info'].publish(cam_info)
        self.publisher_map[sensor_id].publish(msg)

    def publish_can(self, sensor_id, data):
        """
        publish can data
        """
        if not self.vehicle_info_publisher:
            self.vehicle_info_publisher = rospy.Publisher('/carla/ego_vehicle/vehicle_info', CarlaEgoVehicleInfo, queue_size=1, latch=True)
            info_msg = CarlaEgoVehicleInfo()
            for wheel in data['wheels']:
                wheel_info = CarlaEgoVehicleInfoWheel()
                wheel_info.tire_friction = wheel['tire_friction']
                wheel_info.damping_rate = wheel['damping_rate']
                wheel_info.steer_angle = wheel['steer_angle']
                wheel_info.disable_steering = wheel['disable_steering']
                info_msg.wheels.append(wheel_info)
            info_msg.max_rpm = data['max_rpm']
            info_msg.moi = data['moi']
            info_msg.damping_rate_full_throttle = data['damping_rate_full_throttle']
            info_msg.damping_rate_zero_throttle_clutch_disengaged = data['damping_rate_zero_throttle_clutch_disengaged']
            info_msg.use_gear_autobox = data['use_gear_autobox']
            info_msg.clutch_strength = data['clutch_strength']
            info_msg.mass = data['mass']
            info_msg.drag_coefficient = data['drag_coefficient']
            info_msg.center_of_mass.x = data['center_of_mass']['x']
            info_msg.center_of_mass.y = data['center_of_mass']['y']
            info_msg.center_of_mass.z = data['center_of_mass']['z']
            self.vehicle_info_publisher.publish(info_msg)
        msg = CarlaEgoVehicleStatus()
        msg.header = self.get_header()
        msg.velocity = data['speed']
        self.speed = data['speed']
        msg.control.throttle = self.current_control.throttle
        msg.control.steer = self.current_control.steer
        msg.control.brake = self.current_control.brake
        msg.control.hand_brake = self.current_control.hand_brake
        msg.control.reverse = self.current_control.reverse
        msg.control.gear = self.current_control.gear
        msg.control.manual_gear_shift = self.current_control.manual_gear_shift
        self.vehicle_status_publisher.publish(msg)

    def publish_hd_map(self, sensor_id, data):
        """
        publish hd map data
        """
        roll = -math.radians(data['transform']['roll'])
        pitch = -math.radians(data['transform']['pitch'])
        yaw = -math.radians(data['transform']['yaw'])
        quat = tf.transformations.quaternion_from_euler(roll, pitch, yaw)
        x = data['transform']['x']
        y = -data['transform']['y']
        z = data['transform']['z']
        if self.odometry_publisher:
            odometry = Odometry()
            odometry.header.frame_id = 'map'
            odometry.header.stamp = rospy.Time.from_sec(self.timestamp)
            odometry.child_frame_id = 'base_link'
            odometry.pose.pose.position.x = x
            odometry.pose.pose.position.y = y
            odometry.pose.pose.position.z = z
            odometry.pose.pose.orientation.x = quat[0]
            odometry.pose.pose.orientation.y = quat[1]
            odometry.pose.pose.orientation.z = quat[2]
            odometry.pose.pose.orientation.w = quat[3]
            odometry.twist.twist.linear.x = self.speed
            odometry.twist.twist.linear.y = 0
            odometry.twist.twist.linear.z = 0
            self.odometry_publisher.publish(odometry)
        if self.world_info_publisher:
            map_name = os.path.basename(data['map_file'])[:-4]
            if self.current_map_name != map_name:
                self.current_map_name = map_name
                world_info = CarlaWorldInfo()
                world_info.map_name = self.current_map_name
                world_info.opendrive = data['opendrive']
                self.world_info_publisher.publish(world_info)
        if self.map_file_publisher:
            self.map_file_publisher.publish(data['map_file'])

    def use_stepping_mode(self):
        """
        Overload this function to use stepping mode!
        """
        return False

    def run_step(self, input_data, timestamp):
        """
        Execute one step of navigation.
        """
        self.vehicle_control_event.clear()
        self.timestamp = timestamp
        self.clock_publisher.publish(Clock(rospy.Time.from_sec(timestamp)))
        if self.stack_process and self.stack_process.poll() is not None:
            raise RuntimeError('Stack exited with: {} {}'.format(self.stack_process.returncode, self.stack_process.communicate()[0]))
        if self._global_plan_world_coord and (not self.global_plan_published):
            self.global_plan_published = True
            self.publish_plan()
        new_data_available = False
        for key, val in input_data.items():
            new_data_available = True
            sensor_type = self.id_to_sensor_type_map[key]
            if sensor_type == 'sensor.camera.rgb':
                self.publish_camera(key, val[1])
            elif sensor_type == 'sensor.lidar.ray_cast':
                self.publish_lidar(key, val[1])
            elif sensor_type == 'sensor.other.gnss':
                self.publish_gnss(key, val[1])
            elif sensor_type == 'sensor.can_bus':
                self.publish_can(key, val[1])
            elif sensor_type == 'sensor.hd_map':
                self.publish_hd_map(key, val[1])
            else:
                raise TypeError('Invalid sensor type: {}'.format(sensor_type))
        if self.use_stepping_mode():
            if self.step_mode_possible and new_data_available:
                self.vehicle_control_event.wait()
        return self.current_control

def setup(self, path_to_conf_file):
    """
        setup agent
        """
    self.stack_thread = None
    team_code_path = os.environ['TEAM_CODE_ROOT']
    if not team_code_path or not os.path.exists(team_code_path):
        raise IOError("Path '{}' defined by TEAM_CODE_ROOT invalid".format(team_code_path))
    start_script = '{}/start.sh'.format(team_code_path)
    if not os.path.exists(start_script):
        raise IOError("File '{}' defined by TEAM_CODE_ROOT invalid".format(start_script))
    process = subprocess.Popen('rosparam set use_sim_time true', shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
    process.wait()
    if process.returncode:
        raise RuntimeError('Could not set use_sim_time')
    rospy.init_node('ros_agent', anonymous=True)
    self.clock_publisher = rospy.Publisher('clock', Clock, queue_size=10, latch=True)
    self.clock_publisher.publish(Clock(rospy.Time.from_sec(0)))
    rospy.loginfo('Executing stack...')
    self.stack_process = subprocess.Popen(start_script, shell=True, preexec_fn=os.setpgrp)
    self.vehicle_control_event = threading.Event()
    self.timestamp = None
    self.speed = 0
    self.global_plan_published = False
    self.vehicle_info_publisher = None
    self.vehicle_status_publisher = None
    self.odometry_publisher = None
    self.world_info_publisher = None
    self.map_file_publisher = None
    self.current_map_name = None
    self.tf_broadcaster = None
    self.step_mode_possible = False
    self.vehicle_control_subscriber = rospy.Subscriber('/carla/ego_vehicle/vehicle_control_cmd', CarlaEgoVehicleControl, self.on_vehicle_control)
    self.current_control = carla.VehicleControl()
    self.waypoint_publisher = rospy.Publisher('/carla/ego_vehicle/waypoints', Path, queue_size=1, latch=True)
    self.publisher_map = {}
    self.id_to_sensor_type_map = {}
    self.id_to_camera_info_map = {}
    self.cv_bridge = CvBridge()
    for sensor in self.sensors():
        self.id_to_sensor_type_map[sensor['id']] = sensor['type']
        if sensor['type'] == 'sensor.camera.rgb':
            self.publisher_map[sensor['id']] = rospy.Publisher('/carla/ego_vehicle/camera/rgb/' + sensor['id'] + '/image_color', Image, queue_size=1, latch=True)
            self.id_to_camera_info_map[sensor['id']] = self.build_camera_info(sensor)
            self.publisher_map[sensor['id'] + '_info'] = rospy.Publisher('/carla/ego_vehicle/camera/rgb/' + sensor['id'] + '/camera_info', CameraInfo, queue_size=1, latch=True)
        elif sensor['type'] == 'sensor.lidar.ray_cast':
            self.publisher_map[sensor['id']] = rospy.Publisher('/carla/ego_vehicle/lidar/' + sensor['id'] + '/point_cloud', PointCloud2, queue_size=1, latch=True)
        elif sensor['type'] == 'sensor.other.gnss':
            self.publisher_map[sensor['id']] = rospy.Publisher('/carla/ego_vehicle/gnss/' + sensor['id'] + '/fix', NavSatFix, queue_size=1, latch=True)
        elif sensor['type'] == 'sensor.can_bus':
            if not self.vehicle_info_publisher:
                self.vehicle_info_publisher = rospy.Publisher('/carla/ego_vehicle/vehicle_info', CarlaEgoVehicleInfo, queue_size=1, latch=True)
            if not self.vehicle_status_publisher:
                self.vehicle_status_publisher = rospy.Publisher('/carla/ego_vehicle/vehicle_status', CarlaEgoVehicleStatus, queue_size=1, latch=True)
        elif sensor['type'] == 'sensor.hd_map':
            if not self.odometry_publisher:
                self.odometry_publisher = rospy.Publisher('/carla/ego_vehicle/odometry', Odometry, queue_size=1, latch=True)
            if not self.world_info_publisher:
                self.world_info_publisher = rospy.Publisher('/carla/world_info', CarlaWorldInfo, queue_size=1, latch=True)
            if not self.map_file_publisher:
                self.map_file_publisher = rospy.Publisher('/carla/map_file', String, queue_size=1, latch=True)
            if not self.tf_broadcaster:
                self.tf_broadcaster = tf.TransformBroadcaster()
        else:
            raise TypeError('Invalid sensor type: {}'.format(sensor['type']))

def destroy(self):
    """
        Cleanup of all ROS publishers
        """
    if self.stack_process and self.stack_process.poll() is None:
        rospy.loginfo('Sending SIGTERM to stack...')
        os.killpg(os.getpgid(self.stack_process.pid), signal.SIGTERM)
        rospy.loginfo('Waiting for termination of stack...')
        self.stack_process.wait()
        time.sleep(5)
        rospy.loginfo('Terminated stack.')
    rospy.loginfo('Stack is no longer running')
    self.world_info_publisher.unregister()
    self.map_file_publisher.unregister()
    self.vehicle_status_publisher.unregister()
    self.vehicle_info_publisher.unregister()
    self.waypoint_publisher.unregister()
    self.stack_process = None
    rospy.loginfo('Cleanup finished')

def publish_plan(self):
    """
        publish the global plan
        """
    msg = Path()
    msg.header.frame_id = '/map'
    msg.header.stamp = rospy.Time.now()
    for wp in self._global_plan_world_coord:
        pose = PoseStamped()
        pose.pose.position.x = wp[0].location.x
        pose.pose.position.y = -wp[0].location.y
        pose.pose.position.z = wp[0].location.z
        quaternion = tf.transformations.quaternion_from_euler(0, 0, -math.radians(wp[0].rotation.yaw))
        pose.pose.orientation.x = quaternion[0]
        pose.pose.orientation.y = quaternion[1]
        pose.pose.orientation.z = quaternion[2]
        pose.pose.orientation.w = quaternion[3]
        msg.poses.append(pose)
    rospy.loginfo('Publishing Plan...')
    self.waypoint_publisher.publish(msg)

def get_header(self):
    """
        Returns ROS message header
        """
    header = Header()
    header.stamp = rospy.Time.from_sec(self.timestamp)
    return header

def publish_lidar(self, sensor_id, data):
    """
        Function to publish lidar data
        """
    header = self.get_header()
    header.frame_id = 'ego_vehicle/lidar/{}'.format(sensor_id)
    lidar_data = numpy.frombuffer(data, dtype=numpy.float32)
    lidar_data = numpy.reshape(lidar_data, (int(lidar_data.shape[0] / 3), 3))
    lidar_data = -1.0 * lidar_data
    lidar_data = lidar_data[..., [1, 0, 2]]
    msg = create_cloud_xyz32(header, lidar_data)
    self.publisher_map[sensor_id].publish(msg)

def publish_gnss(self, sensor_id, data):
    """
        Function to publish gnss data
        """
    msg = NavSatFix()
    msg.header = self.get_header()
    msg.header.frame_id = 'gps'
    msg.latitude = data[0]
    msg.longitude = data[1]
    msg.altitude = data[2]
    msg.status.status = NavSatStatus.STATUS_SBAS_FIX
    msg.status.service = NavSatStatus.SERVICE_GPS | NavSatStatus.SERVICE_GLONASS | NavSatStatus.SERVICE_COMPASS | NavSatStatus.SERVICE_GALILEO
    self.publisher_map[sensor_id].publish(msg)

def publish_camera(self, sensor_id, data):
    """
        Function to publish camera data
        """
    msg = self.cv_bridge.cv2_to_imgmsg(data, encoding='bgra8')
    msg.header = self.get_header()
    msg.header.frame_id = 'ego_vehicle/camera/rgb/{}'.format(sensor_id)
    cam_info = self.id_to_camera_info_map[sensor_id]
    cam_info.header = msg.header
    self.publisher_map[sensor_id + '_info'].publish(cam_info)
    self.publisher_map[sensor_id].publish(msg)

def publish_can(self, sensor_id, data):
    """
        publish can data
        """
    if not self.vehicle_info_publisher:
        self.vehicle_info_publisher = rospy.Publisher('/carla/ego_vehicle/vehicle_info', CarlaEgoVehicleInfo, queue_size=1, latch=True)
        info_msg = CarlaEgoVehicleInfo()
        for wheel in data['wheels']:
            wheel_info = CarlaEgoVehicleInfoWheel()
            wheel_info.tire_friction = wheel['tire_friction']
            wheel_info.damping_rate = wheel['damping_rate']
            wheel_info.steer_angle = wheel['steer_angle']
            wheel_info.disable_steering = wheel['disable_steering']
            info_msg.wheels.append(wheel_info)
        info_msg.max_rpm = data['max_rpm']
        info_msg.moi = data['moi']
        info_msg.damping_rate_full_throttle = data['damping_rate_full_throttle']
        info_msg.damping_rate_zero_throttle_clutch_disengaged = data['damping_rate_zero_throttle_clutch_disengaged']
        info_msg.use_gear_autobox = data['use_gear_autobox']
        info_msg.clutch_strength = data['clutch_strength']
        info_msg.mass = data['mass']
        info_msg.drag_coefficient = data['drag_coefficient']
        info_msg.center_of_mass.x = data['center_of_mass']['x']
        info_msg.center_of_mass.y = data['center_of_mass']['y']
        info_msg.center_of_mass.z = data['center_of_mass']['z']
        self.vehicle_info_publisher.publish(info_msg)
    msg = CarlaEgoVehicleStatus()
    msg.header = self.get_header()
    msg.velocity = data['speed']
    self.speed = data['speed']
    msg.control.throttle = self.current_control.throttle
    msg.control.steer = self.current_control.steer
    msg.control.brake = self.current_control.brake
    msg.control.hand_brake = self.current_control.hand_brake
    msg.control.reverse = self.current_control.reverse
    msg.control.gear = self.current_control.gear
    msg.control.manual_gear_shift = self.current_control.manual_gear_shift
    self.vehicle_status_publisher.publish(msg)

def publish_hd_map(self, sensor_id, data):
    """
        publish hd map data
        """
    roll = -math.radians(data['transform']['roll'])
    pitch = -math.radians(data['transform']['pitch'])
    yaw = -math.radians(data['transform']['yaw'])
    quat = tf.transformations.quaternion_from_euler(roll, pitch, yaw)
    x = data['transform']['x']
    y = -data['transform']['y']
    z = data['transform']['z']
    if self.odometry_publisher:
        odometry = Odometry()
        odometry.header.frame_id = 'map'
        odometry.header.stamp = rospy.Time.from_sec(self.timestamp)
        odometry.child_frame_id = 'base_link'
        odometry.pose.pose.position.x = x
        odometry.pose.pose.position.y = y
        odometry.pose.pose.position.z = z
        odometry.pose.pose.orientation.x = quat[0]
        odometry.pose.pose.orientation.y = quat[1]
        odometry.pose.pose.orientation.z = quat[2]
        odometry.pose.pose.orientation.w = quat[3]
        odometry.twist.twist.linear.x = self.speed
        odometry.twist.twist.linear.y = 0
        odometry.twist.twist.linear.z = 0
        self.odometry_publisher.publish(odometry)
    if self.world_info_publisher:
        map_name = os.path.basename(data['map_file'])[:-4]
        if self.current_map_name != map_name:
            self.current_map_name = map_name
            world_info = CarlaWorldInfo()
            world_info.map_name = self.current_map_name
            world_info.opendrive = data['opendrive']
            self.world_info_publisher.publish(world_info)
    if self.map_file_publisher:
        self.map_file_publisher.publish(data['map_file'])

def run_step(self, input_data, timestamp):
    """
        Execute one step of navigation.
        """
    self.vehicle_control_event.clear()
    self.timestamp = timestamp
    self.clock_publisher.publish(Clock(rospy.Time.from_sec(timestamp)))
    if self.stack_process and self.stack_process.poll() is not None:
        raise RuntimeError('Stack exited with: {} {}'.format(self.stack_process.returncode, self.stack_process.communicate()[0]))
    if self._global_plan_world_coord and (not self.global_plan_published):
        self.global_plan_published = True
        self.publish_plan()
    new_data_available = False
    for key, val in input_data.items():
        new_data_available = True
        sensor_type = self.id_to_sensor_type_map[key]
        if sensor_type == 'sensor.camera.rgb':
            self.publish_camera(key, val[1])
        elif sensor_type == 'sensor.lidar.ray_cast':
            self.publish_lidar(key, val[1])
        elif sensor_type == 'sensor.other.gnss':
            self.publish_gnss(key, val[1])
        elif sensor_type == 'sensor.can_bus':
            self.publish_can(key, val[1])
        elif sensor_type == 'sensor.hd_map':
            self.publish_hd_map(key, val[1])
        else:
            raise TypeError('Invalid sensor type: {}'.format(sensor_type))
    if self.use_stepping_mode():
        if self.step_mode_possible and new_data_available:
            self.vehicle_control_event.wait()
    return self.current_control

class AutoPilot(autonomous_agent_local.AutonomousAgent):

    def setup(self, path_to_conf_file, route_index=None):
        self.track = autonomous_agent.Track.MAP
        self.config_path = path_to_conf_file
        self.step = -1
        self.wall_start = time.time()
        self.initialized = False
        self.save_path = None
        self.render_bev = False
        self.route_index = route_index
        self.frame_rate_sim = 20
        self.gps_buffer = deque(maxlen=100)
        self.frame_rate = 20
        self.ego_model = EgoModel(dt=1.0 / self.frame_rate)
        self.ego_model_gps = EgoModel(dt=1.0 / self.frame_rate_sim)
        self.vehicle_model = EgoModel(dt=1.0 / self.frame_rate)
        self.visualize = int(os.environ['DEBUG_CHALLENGE'])
        self.save_freq = self.frame_rate_sim // 2
        self.steer_buffer_size = 1
        self.target_speed_slow = 3.0
        self.target_speed_fast = 4.0
        self.clip_delta = 0.25
        self.clip_throttle = 0.75
        self.steer_damping = 0.5
        self.slope_pitch = 10.0
        self.slope_throttle = 0.4
        self.angle_search_range = 0
        self.steer_noise = 0.001
        self.steer_buffer = deque(maxlen=self.steer_buffer_size)
        self._turn_controller = PIDController(K_P=1.25, K_I=0.75, K_D=0.3, n=40)
        self._turn_controller_extrapolation = PIDController(K_P=1.25, K_I=0.75, K_D=0.3, n=40)
        self._speed_controller = PIDController(K_P=5.0, K_I=0.5, K_D=1.0, n=40)
        self._speed_controller_extrapolation = PIDController(K_P=5.0, K_I=0.5, K_D=1.0, n=40)
        self.center_bb_light_x = -2.0
        self.center_bb_light_y = 0.0
        self.center_bb_light_z = 0.0
        self.extent_bb_light_x = 4.5
        self.extent_bb_light_y = 1.5
        self.extent_bb_light_z = 2.0
        self.extrapolation_seconds_no_junction = 1.0
        self.extrapolation_seconds = 4.0
        self.waypoint_seconds = 4.0
        self.detection_radius = 30.0
        self.light_radius = 15.0
        self.vehicle_speed_buffer = defaultdict(lambda: {'velocity': [], 'throttle': [], 'brake': []})
        self.stuck_buffer_size = 30
        self.stuck_vel_threshold = 0.1
        self.stuck_throttle_threshold = 0.1
        self.stuck_brake_threshold = 0.1
        self.commands = deque(maxlen=2)
        self.commands.append(4)
        self.commands.append(4)
        self.far_node_prev = [100000.0, 100000.0]
        self.steer = 0.0
        self.throttle = 0.0
        self.brake = 0.0
        self.target_speed = 4.0
        self.angle = 0.0
        self.stop_sign_hazard = False
        self.traffic_light_hazard = False
        self.walker_hazard = [False for i in range(int(self.extrapolation_seconds * self.frame_rate))]
        self.vehicle_hazard = [False for i in range(int(self.extrapolation_seconds * self.frame_rate))]
        self.junction = False
        self.ignore_stop_signs = True
        self.cleared_stop_signs = []
        self.future_states = {}
        self._vehicle_lights = carla.VehicleLightState.Position | carla.VehicleLightState.LowBeam
        if SAVE_PATH is not None:
            now = datetime.datetime.now()
            string = pathlib.Path(os.environ['ROUTES']).stem + '_'
            string += f'route{self.route_index}_'
            string += '_'.join(map(lambda x: '%02d' % x, (now.month, now.day, now.hour, now.minute, now.second)))
            print(string)
            self.save_path = pathlib.Path(os.environ['SAVE_PATH']) / string
            self.save_path.mkdir(parents=True, exist_ok=False)
            (self.save_path / 'measurements').mkdir()

    def _init(self, hd_map):
        self.world_map = carla.Map('RouteMap', hd_map[1]['opendrive'])
        trajectory = [item[0].location for item in self._global_plan_world_coord]
        self.dense_route, _ = interpolate_trajectory(self.world_map, trajectory)
        print('Sparse Waypoints:', len(self._global_plan))
        print('Dense Waypoints:', len(self.dense_route))
        self._waypoint_planner = RoutePlanner(3.5, 50)
        self._waypoint_planner.set_route(self.dense_route, True)
        self._waypoint_planner.save()
        self._waypoint_planner_extrapolation = RoutePlanner(3.5, 50)
        self._waypoint_planner_extrapolation.set_route(self.dense_route, True)
        self._waypoint_planner_extrapolation.save()
        self._command_planner = RoutePlanner(7.5, 50)
        self._command_planner.set_route(self._global_plan, True)
        self._vehicle = CarlaDataProvider.get_hero_actor()
        self._world = self._vehicle.get_world()
        self.initialized = True

    def sensors(self):
        return [{'type': 'sensor.opendrive_map', 'reading_frequency': 1e-06, 'id': 'hd_map'}, {'type': 'sensor.other.imu', 'x': 0.0, 'y': 0.0, 'z': 0.0, 'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0, 'sensor_tick': 0.05, 'id': 'imu'}, {'type': 'sensor.other.gnss', 'x': 0.0, 'y': 0.0, 'z': 0.0, 'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0, 'sensor_tick': 0.01, 'id': 'gps'}, {'type': 'sensor.speedometer', 'reading_frequency': 20, 'id': 'speed'}]

    def tick(self, input_data):
        gps = input_data['gps'][1][:2]
        speed = input_data['speed'][1]['speed']
        compass = input_data['imu'][1][-1]
        if math.isnan(compass) == True:
            compass = 0.0
        result = {'gps': gps, 'speed': speed, 'compass': compass}
        return result

    def run_step(self, input_data, timestamp):
        self.step += 1
        if not self.initialized:
            if 'hd_map' in input_data.keys():
                self._init(input_data['hd_map'])
            else:
                control = carla.VehicleControl()
                control.steer = 0.0
                control.throttle = 0.0
                control.brake = 1.0
                return control
        control = self._get_control(input_data)
        tick_data_tmp = self.tick(input_data)
        self.update_gps_buffer(control, tick_data_tmp['compass'], tick_data_tmp['speed'])
        return control

    def update_gps_buffer(self, control, theta, speed):
        yaw = np.array([theta - np.pi / 2.0])
        speed = np.array([speed])
        action = np.array(np.stack([control.steer, control.throttle, control.brake], axis=-1))
        for i in range(len(self.gps_buffer)):
            loc = self.gps_buffer[i]
            loc_temp = np.array([loc[1], -loc[0]])
            next_loc_tmp, _, _ = self.ego_model_gps.forward(loc_temp, yaw, speed, action)
            next_loc = np.array([-next_loc_tmp[1], next_loc_tmp[0]])
            self.gps_buffer[i] = next_loc
        return None

    def get_future_states(self):
        return self.future_states

    def _get_control(self, input_data, steer=None, throttle=None, vehicle_hazard=None, light_hazard=None, walker_hazard=None, stop_sign_hazard=None):
        if vehicle_hazard is None or light_hazard is None or walker_hazard is None or (stop_sign_hazard is None):
            brake = self._get_brake(vehicle_hazard, light_hazard, walker_hazard, stop_sign_hazard)
        else:
            brake = vehicle_hazard or light_hazard or walker_hazard or stop_sign_hazard
        ego_vehicle_waypoint = self.world_map.get_waypoint(self._vehicle.get_location())
        self.junction = ego_vehicle_waypoint.is_junction
        speed = input_data['speed'][1]['speed']
        target_speed = self.target_speed_slow if self.junction else self.target_speed_fast
        pos = self._get_position(input_data['gps'][1][:2])
        self.gps_buffer.append(pos)
        pos = np.average(self.gps_buffer, axis=0)
        self._waypoint_planner.load()
        waypoint_route = self._waypoint_planner.run_step(pos)
        near_node, near_command = waypoint_route[1] if len(waypoint_route) > 1 else waypoint_route[0]
        self._waypoint_planner.save()
        self._waypoint_planner_extrapolation.load()
        self.waypoint_route_extrapolation = self._waypoint_planner_extrapolation.run_step(pos)
        self._waypoint_planner_extrapolation.save()
        if throttle is None:
            throttle = self._get_throttle(brake, target_speed, speed)
            if self._vehicle.get_transform().rotation.pitch > self.slope_pitch:
                throttle += self.slope_throttle
        if steer is None:
            theta = input_data['imu'][1][-1]
            if math.isnan(theta):
                theta = 0.0
            steer = self._get_steer(brake, waypoint_route, pos, theta, speed)
            steer_extrapolation = self._get_steer_extrapolation(waypoint_route, pos, theta, speed)
        self.steer_buffer.append(steer)
        control = carla.VehicleControl()
        control.steer = np.mean(self.steer_buffer) + self.steer_noise * np.random.randn()
        control.throttle = throttle
        control.brake = float(brake)
        self.steer = control.steer
        self.throttle = control.throttle
        self.brake = control.brake
        self.target_speed = target_speed
        self._save_waypoints()
        if self.step % self.save_freq == 0 and self.save_path is not None:
            command_route = self._command_planner.run_step(pos)
            far_node, far_command = command_route[1] if len(command_route) > 1 else command_route[0]
            if (far_node != self.far_node_prev).all():
                self.far_node_prev = far_node
                self.commands.append(far_command.value)
            if self.render_bev == False:
                tick_data = self.tick(input_data)
            else:
                tick_data = self.tick(input_data, self.future_states)
            self.save(far_node, steer, throttle, brake, target_speed, tick_data)
        return control

    def save(self, far_node, steer, throttle, brake, target_speed, tick_data):
        frame = self.step // self.save_freq
        pos = self._get_position(tick_data['gps'])
        theta = tick_data['compass']
        speed = tick_data['speed']
        waypoints = []
        for i, box in enumerate(self.future_states['ego']):
            if (i + 1) % (self.frame_rate / 2) == 0:
                box_x = -box.location.y
                box_y = box.location.x
                box_theta = box.rotation.yaw * np.pi / 180.0 + np.pi / 2
                if box_theta < 0:
                    box_theta += 2 * np.pi
                waypoints.append((box_x, box_y, box_theta))
        data = {'x': pos[0], 'y': pos[1], 'theta': theta, 'speed': speed, 'target_speed': target_speed, 'x_command': far_node[0], 'y_command': far_node[1], 'command': self.commands[-2], 'waypoints': waypoints, 'steer': steer, 'throttle': throttle, 'brake': brake, 'junction': self.junction, 'vehicle_hazard': self.vehicle_hazard, 'light_hazard': self.traffic_light_hazard, 'walker_hazard': self.walker_hazard, 'stop_sign_hazard': self.stop_sign_hazard, 'angle': self.angle, 'ego_matrix': self._vehicle.get_transform().get_matrix()}
        measurements_file = self.save_path / 'measurements' / ('%04d.json' % frame)
        with open(measurements_file, 'w') as f:
            json.dump(data, f, indent=4)

    def destroy(self):
        pass

    def _get_steer(self, brake, route, pos, theta, speed, restore=True):
        if self._waypoint_planner.is_last:
            angle = 0.0
        if speed < 0.01 and brake == True:
            angle = 0.0
        if len(route) == 1:
            target = route[0][0]
            angle_unnorm = self._get_angle_to(pos, theta, target)
            angle = angle_unnorm / 90
        elif self.angle_search_range <= 2:
            target = route[1][0]
            angle_unnorm = self._get_angle_to(pos, theta, target)
            angle = angle_unnorm / 90
        else:
            search_range = min([len(route), self.angle_search_range])
            for i in range(1, search_range):
                target = route[i][0]
                angle_unnorm = self._get_angle_to(pos, theta, target)
                angle_new = angle_unnorm / 90
                if i == 1:
                    angle = angle_new
                if np.abs(angle_new) < np.abs(angle):
                    angle = angle_new
        self.angle = angle
        if restore:
            self._turn_controller.load()
        steer = self._turn_controller.step(angle)
        if restore:
            self._turn_controller.save()
        steer = np.clip(steer, -1.0, 1.0)
        steer = round(steer, 3)
        if brake:
            steer *= self.steer_damping
        return steer

    def _get_steer_extrapolation(self, route, pos, theta, speed, restore=True):
        if self._waypoint_planner_extrapolation.is_last:
            angle = 0.0
        if len(route) == 1:
            target = route[0][0]
            angle_unnorm = self._get_angle_to(pos, theta, target)
            angle = angle_unnorm / 90
        elif self.angle_search_range <= 2:
            target = route[1][0]
            angle_unnorm = self._get_angle_to(pos, theta, target)
            angle = angle_unnorm / 90
        else:
            search_range = min([len(route), self.angle_search_range])
            for i in range(1, search_range):
                target = route[i][0]
                angle_unnorm = self._get_angle_to(pos, theta, target)
                angle_new = angle_unnorm / 90
                if i == 1:
                    angle = angle_new
                if np.abs(angle_new) < np.abs(angle):
                    angle = angle_new
        self.angle = angle
        if restore:
            self._turn_controller_extrapolation.load()
        steer = self._turn_controller_extrapolation.step(angle)
        if restore:
            self._turn_controller_extrapolation.save()
        steer = np.clip(steer, -1.0, 1.0)
        steer = round(steer, 3)
        return steer

    def _get_throttle(self, brake, target_speed, speed, restore=True):
        target_speed = target_speed if not brake else 0.0
        if self._waypoint_planner.is_last:
            target_speed = 0.0
        delta = np.clip(target_speed - speed, 0.0, self.clip_delta)
        if restore:
            self._speed_controller.load()
        throttle = self._speed_controller.step(delta)
        if restore:
            self._speed_controller.save()
        throttle = np.clip(throttle, 0.0, self.clip_throttle)
        if brake:
            throttle = 0.0
        return throttle

    def _get_throttle_extrapolation(self, target_speed, speed, restore=True):
        if self._waypoint_planner_extrapolation.is_last:
            target_speed = 0.0
        delta = np.clip(target_speed - speed, 0.0, self.clip_delta)
        if restore:
            self._speed_controller_extrapolation.load()
        throttle = self._speed_controller_extrapolation.step(delta)
        if restore:
            self._speed_controller_extrapolation.save()
        throttle = np.clip(throttle, 0.0, self.clip_throttle)
        return throttle

    def _get_brake(self, vehicle_hazard=None, light_hazard=None, walker_hazard=None, stop_sign_hazard=None):
        actors = self._world.get_actors()
        speed = self._get_forward_speed()
        vehicle_location = self._vehicle.get_location()
        vehicle_transform = self._vehicle.get_transform()
        vehicles = actors.filter('*vehicle*')
        if light_hazard is None:
            light_hazard = False
            self._active_traffic_light = None
            _traffic_lights = self.get_nearby_object(vehicle_location, actors.filter('*traffic_light*'), self.light_radius)
            center_light_detector_bb = vehicle_transform.transform(carla.Location(x=self.center_bb_light_x, y=self.center_bb_light_y, z=self.center_bb_light_z))
            extent_light_detector_bb = carla.Vector3D(x=self.extent_bb_light_x, y=self.extent_bb_light_y, z=self.extent_bb_light_z)
            light_detector_bb = carla.BoundingBox(center_light_detector_bb, extent_light_detector_bb)
            light_detector_bb.rotation = vehicle_transform.rotation
            color2 = carla.Color(255, 255, 255, 255)
            for light in _traffic_lights:
                if light.state == carla.libcarla.TrafficLightState.Red:
                    color = carla.Color(255, 0, 0, 255)
                elif light.state == carla.libcarla.TrafficLightState.Yellow:
                    color = carla.Color(255, 255, 0, 255)
                elif light.state == carla.libcarla.TrafficLightState.Green:
                    color = carla.Color(0, 255, 0, 255)
                elif light.state == carla.libcarla.TrafficLightState.Off:
                    color = carla.Color(0, 0, 0, 255)
                else:
                    color = carla.Color(0, 0, 255, 255)
                size = 0.1
                center_bounding_box = light.get_transform().transform(light.trigger_volume.location)
                center_bounding_box = carla.Location(center_bounding_box.x, center_bounding_box.y, center_bounding_box.z)
                length_bounding_box = carla.Vector3D(light.trigger_volume.extent.x, light.trigger_volume.extent.y, light.trigger_volume.extent.z)
                transform = carla.Transform(center_bounding_box)
                bounding_box = carla.BoundingBox(transform.location, length_bounding_box)
                gloabl_rot = light.get_transform().rotation
                bounding_box.rotation = carla.Rotation(pitch=light.trigger_volume.rotation.pitch + gloabl_rot.pitch, yaw=light.trigger_volume.rotation.yaw + gloabl_rot.yaw, roll=light.trigger_volume.rotation.roll + gloabl_rot.roll)
                if self.visualize == 1:
                    self._world.debug.draw_box(box=bounding_box, rotation=bounding_box.rotation, thickness=0.1, color=color, life_time=1.0 / self.frame_rate_sim)
                if self.check_obb_intersection(light_detector_bb, bounding_box) == True:
                    if light.state == carla.libcarla.TrafficLightState.Red or light.state == carla.libcarla.TrafficLightState.Yellow:
                        self._active_traffic_light = light
                        light_hazard = True
                        color2 = carla.Color(255, 0, 0, 255)
            if self.visualize == 1:
                self._world.debug.draw_box(box=light_detector_bb, rotation=light_detector_bb.rotation, thickness=0.1, color=color2, life_time=1.0 / self.frame_rate_sim)
        if stop_sign_hazard is None:
            stop_sign_hazard = False
            if not self.ignore_stop_signs:
                stop_signs = self.get_nearby_object(vehicle_location, actors.filter('*stop*'), self.light_radius)
                center_vehicle_stop_sign_detector_bb = vehicle_transform.transform(self._vehicle.bounding_box.location)
                extent_vehicle_stop_sign_detector_bb = self._vehicle.bounding_box.extent
                vehicle_stop_sign_detector_bb = carla.BoundingBox(center_vehicle_stop_sign_detector_bb, extent_vehicle_stop_sign_detector_bb)
                vehicle_stop_sign_detector_bb.rotation = vehicle_transform.rotation
                for stop_sign in stop_signs:
                    center_bb_stop_sign = stop_sign.get_transform().transform(stop_sign.trigger_volume.location)
                    length_bb_stop_sign = carla.Vector3D(stop_sign.trigger_volume.extent.x, stop_sign.trigger_volume.extent.y, stop_sign.trigger_volume.extent.z)
                    transform_stop_sign = carla.Transform(center_bb_stop_sign)
                    bounding_box_stop_sign = carla.BoundingBox(transform_stop_sign.location, length_bb_stop_sign)
                    rotation_stop_sign = stop_sign.get_transform().rotation
                    bounding_box_stop_sign.rotation = carla.Rotation(pitch=stop_sign.trigger_volume.rotation.pitch + rotation_stop_sign.pitch, yaw=stop_sign.trigger_volume.rotation.yaw + rotation_stop_sign.yaw, roll=stop_sign.trigger_volume.rotation.roll + rotation_stop_sign.roll)
                    color = carla.Color(0, 255, 0, 255)
                    if self.check_obb_intersection(vehicle_stop_sign_detector_bb, bounding_box_stop_sign) == True:
                        if not stop_sign.id in self.cleared_stop_signs:
                            if speed * 3.6 > 0.0:
                                stop_sign_hazard = True
                                color = carla.Color(255, 0, 0, 255)
                            else:
                                self.cleared_stop_signs.append(stop_sign.id)
                    if self.visualize == 1:
                        self._world.debug.draw_box(box=bounding_box_stop_sign, rotation=bounding_box_stop_sign.rotation, thickness=0.1, color=color, life_time=1.0 / self.frame_rate_sim)
                for cleared_stop_sign in self.cleared_stop_signs:
                    remove_stop_sign = True
                    for stop_sign in stop_signs:
                        if stop_sign.id == cleared_stop_sign:
                            remove_stop_sign = False
                    if remove_stop_sign == True:
                        self.cleared_stop_signs.remove(cleared_stop_sign)
        if vehicle_hazard is None or walker_hazard is None:
            vehicle_hazard = False
            self.vehicle_hazard = [False for i in range(int(self.extrapolation_seconds * self.frame_rate))]
            extrapolation_seconds = self.extrapolation_seconds
            detection_radius = self.detection_radius
            number_of_future_frames = int(extrapolation_seconds * self.frame_rate)
            number_of_future_frames_no_junction = int(self.extrapolation_seconds_no_junction * self.frame_rate)
            color = carla.Color(0, 255, 0, 255)
            walkers = actors.filter('*walker*')
            walker_hazard = False
            self.walker_hazard = [False for i in range(int(self.extrapolation_seconds * self.frame_rate))]
            nearby_walkers = []
            for walker in walkers:
                if walker.get_location().distance(vehicle_location) < detection_radius:
                    walker_future_bbs = []
                    walker_transform = walker.get_transform()
                    walker_velocity = walker.get_velocity()
                    walker_speed = self._get_forward_speed(transform=walker_transform, velocity=walker_velocity)
                    walker_location = walker_transform.location
                    walker_direction = walker.get_control().direction
                    for i in range(number_of_future_frames):
                        if self.render_bev == False and self.junction == False and (i > number_of_future_frames_no_junction):
                            break
                        new_x = walker_location.x + walker_direction.x * walker_speed * (1.0 / self.frame_rate)
                        new_y = walker_location.y + walker_direction.y * walker_speed * (1.0 / self.frame_rate)
                        new_z = walker_location.z + walker_direction.z * walker_speed * (1.0 / self.frame_rate)
                        walker_location = carla.Location(new_x, new_y, new_z)
                        transform = carla.Transform(walker_location)
                        bounding_box = carla.BoundingBox(transform.location, walker.bounding_box.extent)
                        bounding_box.rotation = carla.Rotation(pitch=walker.bounding_box.rotation.pitch + walker_transform.rotation.pitch, yaw=walker.bounding_box.rotation.yaw + walker_transform.rotation.yaw, roll=walker.bounding_box.rotation.roll + walker_transform.rotation.roll)
                        color = carla.Color(0, 0, 255, 255)
                        if self.visualize == 1:
                            self._world.debug.draw_box(box=bounding_box, rotation=bounding_box.rotation, thickness=0.1, color=color, life_time=1.0 / self.frame_rate_sim)
                        walker_future_bbs.append(bounding_box)
                    nearby_walkers.append(walker_future_bbs)
            nearby_vehicles = {}
            tmp_near_vehicle_id = []
            tmp_stucked_vehicle_id = []
            for vehicle in vehicles:
                if vehicle.id == self._vehicle.id:
                    continue
                if vehicle.get_location().distance(vehicle_location) < detection_radius:
                    tmp_near_vehicle_id.append(vehicle.id)
                    veh_future_bbs = []
                    traffic_transform = vehicle.get_transform()
                    traffic_control = vehicle.get_control()
                    traffic_velocity = vehicle.get_velocity()
                    traffic_speed = self._get_forward_speed(transform=traffic_transform, velocity=traffic_velocity)
                    self.vehicle_speed_buffer[vehicle.id]['velocity'].append(traffic_speed)
                    self.vehicle_speed_buffer[vehicle.id]['throttle'].append(traffic_control.throttle)
                    self.vehicle_speed_buffer[vehicle.id]['brake'].append(traffic_control.brake)
                    if len(self.vehicle_speed_buffer[vehicle.id]['velocity']) > self.stuck_buffer_size:
                        self.vehicle_speed_buffer[vehicle.id]['velocity'] = self.vehicle_speed_buffer[vehicle.id]['velocity'][-self.stuck_buffer_size:]
                        self.vehicle_speed_buffer[vehicle.id]['throttle'] = self.vehicle_speed_buffer[vehicle.id]['throttle'][-self.stuck_buffer_size:]
                        self.vehicle_speed_buffer[vehicle.id]['brake'] = self.vehicle_speed_buffer[vehicle.id]['brake'][-self.stuck_buffer_size:]
                    next_loc = np.array([traffic_transform.location.x, traffic_transform.location.y])
                    action = np.array(np.stack([traffic_control.steer, traffic_control.throttle, traffic_control.brake], axis=-1))
                    next_yaw = np.array([traffic_transform.rotation.yaw / 180.0 * np.pi])
                    next_speed = np.array([traffic_speed])
                    for i in range(number_of_future_frames):
                        if self.render_bev == False and self.junction == False and (i > number_of_future_frames_no_junction):
                            break
                        next_loc, next_yaw, next_speed = self.vehicle_model.forward(next_loc, next_yaw, next_speed, action)
                        delta_yaws = next_yaw.item() * 180.0 / np.pi
                        transform = carla.Transform(carla.Location(x=next_loc[0].item(), y=next_loc[1].item(), z=traffic_transform.location.z))
                        bounding_box = carla.BoundingBox(transform.location, vehicle.bounding_box.extent)
                        bounding_box.rotation = carla.Rotation(pitch=float(traffic_transform.rotation.pitch), yaw=float(delta_yaws), roll=float(traffic_transform.rotation.roll))
                        color = carla.Color(0, 0, 255, 255)
                        if self.visualize == 1:
                            self._world.debug.draw_box(box=bounding_box, rotation=bounding_box.rotation, thickness=0.1, color=color, life_time=1.0 / self.frame_rate_sim)
                        veh_future_bbs.append(bounding_box)
                    if statistics.mean(self.vehicle_speed_buffer[vehicle.id]['velocity']) < self.stuck_vel_threshold and statistics.mean(self.vehicle_speed_buffer[vehicle.id]['throttle']) > self.stuck_throttle_threshold and (statistics.mean(self.vehicle_speed_buffer[vehicle.id]['brake']) < self.stuck_brake_threshold):
                        tmp_stucked_vehicle_id.append(vehicle.id)
                    nearby_vehicles[vehicle.id] = veh_future_bbs
            to_delete = set(self.vehicle_speed_buffer.keys()).difference(tmp_near_vehicle_id)
            for d in to_delete:
                del self.vehicle_speed_buffer[d]
            next_loc_no_brake = np.array([vehicle_transform.location.x, vehicle_transform.location.y])
            next_yaw_no_brake = np.array([vehicle_transform.rotation.yaw / 180.0 * np.pi])
            next_speed_no_brake = np.array([speed])
            throttle_extrapolation = self._get_throttle_extrapolation(self.target_speed, speed)
            action_no_brake = np.array(np.stack([self.steer, throttle_extrapolation, 0.0], axis=-1))
            back_only_vehicle_id = []
            ego_future = []
            for i in range(number_of_future_frames):
                if self.render_bev == False and self.junction == False and (i > number_of_future_frames_no_junction):
                    alpha = 255
                    color_value = 50
                    break
                else:
                    alpha = 50
                    color_value = 255
                next_loc_no_brake, next_yaw_no_brake, next_speed_no_brake = self.ego_model.forward(next_loc_no_brake, next_yaw_no_brake, next_speed_no_brake, action_no_brake)
                next_loc_no_brake_temp = np.array([-next_loc_no_brake[1], next_loc_no_brake[0]])
                next_yaw_no_brake_temp = next_yaw_no_brake.item() + np.pi / 2
                waypoint_route_extrapolation_temp = self._waypoint_planner_extrapolation.run_step(next_loc_no_brake_temp)
                steer_extrapolation_temp = self._get_steer_extrapolation(waypoint_route_extrapolation_temp, next_loc_no_brake_temp, next_yaw_no_brake_temp, next_speed_no_brake, restore=False)
                throttle_extrapolation_temp = self._get_throttle_extrapolation(self.target_speed, next_speed_no_brake, restore=False)
                brake_extrapolation_temp = 1.0 if self._waypoint_planner_extrapolation.is_last else 0.0
                action_no_brake = np.array(np.stack([steer_extrapolation_temp, float(throttle_extrapolation_temp), brake_extrapolation_temp], axis=-1))
                delta_yaws_no_brake = next_yaw_no_brake.item() * 180.0 / np.pi
                cosine = np.cos(next_yaw_no_brake.item())
                sine = np.sin(next_yaw_no_brake.item())
                extent = self._vehicle.bounding_box.extent
                extent_org = self._vehicle.bounding_box.extent
                extent.x = extent.x / 2.0
                transform = carla.Transform(carla.Location(x=next_loc_no_brake[0].item() + extent.x * cosine, y=next_loc_no_brake[1].item() + extent.y * sine, z=vehicle_transform.location.z))
                bounding_box = carla.BoundingBox(transform.location, extent)
                bounding_box.rotation = carla.Rotation(pitch=float(vehicle_transform.rotation.pitch), yaw=float(delta_yaws_no_brake), roll=float(vehicle_transform.rotation.roll))
                transform_back = carla.Transform(carla.Location(x=next_loc_no_brake[0].item() - extent.x * cosine, y=next_loc_no_brake[1].item() - extent.y * sine, z=vehicle_transform.location.z))
                bounding_box_back = carla.BoundingBox(transform_back.location, extent)
                bounding_box_back.rotation = carla.Rotation(pitch=float(vehicle_transform.rotation.pitch), yaw=float(delta_yaws_no_brake), roll=float(vehicle_transform.rotation.roll))
                color = carla.Color(0, color_value, 0, alpha)
                color2 = carla.Color(0, color_value, color_value, alpha)
                for id, traffic_participant in nearby_vehicles.items():
                    i_stuck = i
                    if self.render_bev == False and self.junction == False and (i > number_of_future_frames_no_junction):
                        break
                    if id in tmp_stucked_vehicle_id:
                        i_stuck = 0
                    back_intersect = self.check_obb_intersection(bounding_box_back, traffic_participant[i_stuck]) == True
                    front_intersect = self.check_obb_intersection(bounding_box, traffic_participant[i_stuck]) == True
                    if id in back_only_vehicle_id:
                        back_only_vehicle_id.remove(id)
                        if back_intersect:
                            back_only_vehicle_id.append(id)
                        continue
                    if back_intersect and (not front_intersect):
                        back_only_vehicle_id.append(id)
                    if front_intersect:
                        color = carla.Color(color_value, 0, 0, alpha)
                        if self.junction == True or i <= number_of_future_frames_no_junction:
                            vehicle_hazard = True
                        self.vehicle_hazard[i] = True
                for walker in nearby_walkers:
                    if self.render_bev == False and self.junction == False and (i > number_of_future_frames_no_junction):
                        break
                    if self.check_obb_intersection(bounding_box, walker[i]) == True:
                        color = carla.Color(color_value, 0, 0, alpha)
                        if self.junction == True or i <= number_of_future_frames_no_junction:
                            walker_hazard = True
                        self.walker_hazard[i] = True
                if self.visualize == 1:
                    self._world.debug.draw_box(box=bounding_box, rotation=bounding_box.rotation, thickness=0.1, color=color, life_time=1.0 / self.frame_rate_sim)
                    self._world.debug.draw_box(box=bounding_box_back, rotation=bounding_box.rotation, thickness=0.1, color=color2, life_time=1.0 / self.frame_rate_sim)
            color = carla.Color(0, 255, 0, 255)
            bremsweg = (speed * 3.6 / 10.0) ** 2 / 2.0
            safety_x = np.clip(bremsweg + 1.0, a_min=2.0, a_max=4.0)
            center_safety_box = vehicle_transform.transform(carla.Location(x=safety_x, y=0.0, z=0.0))
            bounding_box = carla.BoundingBox(center_safety_box, self._vehicle.bounding_box.extent)
            bounding_box.rotation = vehicle_transform.rotation
            for _, traffic_participant in nearby_vehicles.items():
                if self.check_obb_intersection(bounding_box, traffic_participant[0]) == True:
                    color = carla.Color(255, 0, 0, 255)
                    vehicle_hazard = True
                    self.vehicle_hazard[0] = True
            for walker in nearby_walkers:
                if self.check_obb_intersection(bounding_box, walker[0]) == True:
                    color = carla.Color(255, 0, 0, 255)
                    walker_hazard = True
                    self.walker_hazard[0] = True
            if self.visualize == 1:
                self._world.debug.draw_box(box=bounding_box, rotation=bounding_box.rotation, thickness=0.1, color=color, life_time=1.0 / self.frame_rate_sim)
            self.future_states = {'walker': nearby_walkers, 'vehicle': nearby_vehicles}
        else:
            self.vehicle_hazard = vehicle_hazard
            self.walker_hazard = walker_hazard
        self.stop_sign_hazard = stop_sign_hazard
        self.traffic_light_hazard = light_hazard
        return vehicle_hazard or light_hazard or walker_hazard or stop_sign_hazard

    def _intersection_check(self, ego_wps):
        actors = self._world.get_actors()
        speed = self._get_forward_speed()
        vehicle_location = self._vehicle.get_location()
        vehicle_transform = self._vehicle.get_transform()
        vehicles = actors.filter('*vehicle*')
        vehicle_hazard = False
        self.vehicle_hazard = [False for i in range(int(self.extrapolation_seconds * self.frame_rate))]
        extrapolation_seconds = self.extrapolation_seconds
        detection_radius = self.detection_radius
        number_of_future_frames = int(extrapolation_seconds * self.frame_rate)
        number_of_future_frames_no_junction = int(self.extrapolation_seconds_no_junction * self.frame_rate)
        color = carla.Color(0, 255, 0, 255)
        walkers = actors.filter('*walker*')
        walker_hazard = False
        self.walker_hazard = [False for i in range(int(self.extrapolation_seconds * self.frame_rate))]
        nearby_walkers = []
        for walker in walkers:
            if walker.get_location().distance(vehicle_location) < detection_radius:
                walker_future_bbs = []
                walker_transform = walker.get_transform()
                walker_velocity = walker.get_velocity()
                walker_speed = self._get_forward_speed(transform=walker_transform, velocity=walker_velocity)
                walker_location = walker_transform.location
                walker_direction = walker.get_control().direction
                for i in range(number_of_future_frames):
                    if self.render_bev == False and self.junction == False and (i > number_of_future_frames_no_junction):
                        break
                    new_x = walker_location.x + walker_direction.x * walker_speed * (1.0 / self.frame_rate)
                    new_y = walker_location.y + walker_direction.y * walker_speed * (1.0 / self.frame_rate)
                    new_z = walker_location.z + walker_direction.z * walker_speed * (1.0 / self.frame_rate)
                    walker_location = carla.Location(new_x, new_y, new_z)
                    transform = carla.Transform(walker_location)
                    bounding_box = carla.BoundingBox(transform.location, walker.bounding_box.extent)
                    bounding_box.rotation = carla.Rotation(pitch=walker.bounding_box.rotation.pitch + walker_transform.rotation.pitch, yaw=walker.bounding_box.rotation.yaw + walker_transform.rotation.yaw, roll=walker.bounding_box.rotation.roll + walker_transform.rotation.roll)
                    color = carla.Color(0, 0, 255, 255)
                    if self.visualize == 1:
                        self._world.debug.draw_box(box=bounding_box, rotation=bounding_box.rotation, thickness=0.1, color=color, life_time=1.0 / self.frame_rate_sim)
                    walker_future_bbs.append(bounding_box)
                nearby_walkers.append(walker_future_bbs)
        nearby_vehicles = {}
        tmp_near_vehicle_id = []
        tmp_stucked_vehicle_id = []
        for vehicle in vehicles:
            if vehicle.id == self._vehicle.id:
                continue
            if vehicle.get_location().distance(vehicle_location) < detection_radius:
                tmp_near_vehicle_id.append(vehicle.id)
                veh_future_bbs = []
                traffic_transform = vehicle.get_transform()
                traffic_control = vehicle.get_control()
                traffic_velocity = vehicle.get_velocity()
                traffic_speed = self._get_forward_speed(transform=traffic_transform, velocity=traffic_velocity)
                self.vehicle_speed_buffer[vehicle.id]['velocity'].append(traffic_speed)
                self.vehicle_speed_buffer[vehicle.id]['throttle'].append(traffic_control.throttle)
                self.vehicle_speed_buffer[vehicle.id]['brake'].append(traffic_control.brake)
                if len(self.vehicle_speed_buffer[vehicle.id]['velocity']) > self.stuck_buffer_size:
                    self.vehicle_speed_buffer[vehicle.id]['velocity'] = self.vehicle_speed_buffer[vehicle.id]['velocity'][-self.stuck_buffer_size:]
                    self.vehicle_speed_buffer[vehicle.id]['throttle'] = self.vehicle_speed_buffer[vehicle.id]['throttle'][-self.stuck_buffer_size:]
                    self.vehicle_speed_buffer[vehicle.id]['brake'] = self.vehicle_speed_buffer[vehicle.id]['brake'][-self.stuck_buffer_size:]
                next_loc = np.array([traffic_transform.location.x, traffic_transform.location.y])
                action = np.array(np.stack([traffic_control.steer, traffic_control.throttle, traffic_control.brake], axis=-1))
                next_yaw = np.array([traffic_transform.rotation.yaw / 180.0 * np.pi])
                next_speed = np.array([traffic_speed])
                for i in range(number_of_future_frames):
                    if self.render_bev == False and self.junction == False and (i > number_of_future_frames_no_junction):
                        break
                    next_loc, next_yaw, next_speed = self.vehicle_model.forward(next_loc, next_yaw, next_speed, action)
                    delta_yaws = next_yaw.item() * 180.0 / np.pi
                    transform = carla.Transform(carla.Location(x=next_loc[0].item(), y=next_loc[1].item(), z=traffic_transform.location.z))
                    bounding_box = carla.BoundingBox(transform.location, vehicle.bounding_box.extent)
                    bounding_box.rotation = carla.Rotation(pitch=float(traffic_transform.rotation.pitch), yaw=float(delta_yaws), roll=float(traffic_transform.rotation.roll))
                    color = carla.Color(0, 0, 255, 255)
                    if self.visualize == 1:
                        self._world.debug.draw_box(box=bounding_box, rotation=bounding_box.rotation, thickness=0.1, color=color, life_time=1.0 / self.frame_rate_sim)
                    veh_future_bbs.append(bounding_box)
                if statistics.mean(self.vehicle_speed_buffer[vehicle.id]['velocity']) < self.stuck_vel_threshold and statistics.mean(self.vehicle_speed_buffer[vehicle.id]['throttle']) > self.stuck_throttle_threshold and (statistics.mean(self.vehicle_speed_buffer[vehicle.id]['brake']) < self.stuck_brake_threshold):
                    tmp_stucked_vehicle_id.append(vehicle.id)
                nearby_vehicles[vehicle.id] = veh_future_bbs
        to_delete = set(self.vehicle_speed_buffer.keys()).difference(tmp_near_vehicle_id)
        for d in to_delete:
            del self.vehicle_speed_buffer[d]
        number_of_interpolation_frames = self.frame_rate // 2
        cur_loc = np.array([[vehicle_transform.location.x, vehicle_transform.location.y]])
        cur_loc_ego = np.array([[0, 0]])
        vehicl_yaw = (vehicle_transform.rotation.yaw + 90) * np.pi / 180
        rotation = np.array([[np.cos(vehicl_yaw), np.sin(vehicl_yaw)], [-np.sin(vehicl_yaw), np.cos(vehicl_yaw)]])
        future_loc = cur_loc + ego_wps[0] @ rotation
        all_locs = np.append(cur_loc, future_loc, axis=0)
        all_locs_ego = np.append(cur_loc_ego, ego_wps[0], axis=0)
        cur_yaw = np.array([vehicle_transform.rotation.yaw / 180.0 * np.pi])
        prev_yaw = cur_yaw
        back_only_vehicle_id = []
        for i in range(1, 1 + ego_wps.shape[1]):
            if self.render_bev == False and self.junction == False and (i > number_of_future_frames_no_junction):
                alpha = 255
                color_value = 50
                break
            else:
                alpha = 50
                color_value = 255
            delta_yaw = math.atan2(all_locs_ego[i][0] - all_locs_ego[i - 1][0], all_locs_ego[i][1] - all_locs_ego[i - 1][1])
            next_yaw = cur_yaw - delta_yaw
            for k in range(number_of_interpolation_frames):
                tmp_loc = all_locs[i - 1] + (all_locs[i] - all_locs[i - 1]) / number_of_interpolation_frames * k
                tmp_yaw = prev_yaw + (next_yaw - prev_yaw) / number_of_interpolation_frames * k
                next_yaw_deg = tmp_yaw.item() * 180.0 / np.pi
                cosine = np.cos(tmp_yaw.item())
                sine = np.sin(tmp_yaw.item())
                extent = self._vehicle.bounding_box.extent
                extent.x = extent.x / 2.0
                transform = carla.Transform(carla.Location(x=tmp_loc[0].item() + extent.x * cosine, y=tmp_loc[1].item() + extent.y * sine, z=vehicle_transform.location.z))
                bounding_box = carla.BoundingBox(transform.location, extent)
                bounding_box.rotation = carla.Rotation(pitch=float(vehicle_transform.rotation.pitch), yaw=float(next_yaw_deg), roll=float(vehicle_transform.rotation.roll))
                transform_back = carla.Transform(carla.Location(x=tmp_loc[0].item() - extent.x * cosine, y=tmp_loc[1].item() - extent.y * sine, z=vehicle_transform.location.z))
                bounding_box_back = carla.BoundingBox(transform_back.location, extent)
                bounding_box_back.rotation = carla.Rotation(pitch=float(vehicle_transform.rotation.pitch), yaw=float(next_yaw_deg), roll=float(vehicle_transform.rotation.roll))
                color = carla.Color(0, color_value, 0, alpha)
                color2 = carla.Color(0, color_value, color_value, alpha)
                index = k + (i - 1) * number_of_interpolation_frames
                i_stuck = index
                for id, traffic_participant in nearby_vehicles.items():
                    if self.render_bev == False and self.junction == False and (i > number_of_future_frames_no_junction):
                        break
                    if id in tmp_stucked_vehicle_id:
                        i_stuck = 0
                    back_intersect = self.check_obb_intersection(bounding_box_back, traffic_participant[i_stuck]) == True
                    front_intersect = self.check_obb_intersection(bounding_box, traffic_participant[i_stuck]) == True
                    if id in back_only_vehicle_id:
                        back_only_vehicle_id.remove(id)
                        if back_intersect:
                            back_only_vehicle_id.append(id)
                        continue
                    if back_intersect and (not front_intersect):
                        back_only_vehicle_id.append(id)
                    if front_intersect:
                        color = carla.Color(color_value, 0, 0, alpha)
                        if self.junction == True or i <= number_of_future_frames_no_junction:
                            vehicle_hazard = True
                        self.vehicle_hazard[i] = True
                for walker in nearby_walkers:
                    if self.render_bev == False and self.junction == False and (i > number_of_future_frames_no_junction):
                        break
                    if self.check_obb_intersection(bounding_box, walker[i]) == True:
                        color = carla.Color(color_value, 0, 0, alpha)
                        if self.junction == True or i <= number_of_future_frames_no_junction:
                            walker_hazard = True
                        self.walker_hazard[i] = True
                if self.visualize == 1:
                    self._world.debug.draw_box(box=bounding_box, rotation=bounding_box.rotation, thickness=0.1, color=color, life_time=1.0 / self.frame_rate_sim)
                    self._world.debug.draw_box(box=bounding_box_back, rotation=bounding_box.rotation, thickness=0.1, color=color2, life_time=1.0 / self.frame_rate_sim)
                prev_yaw = next_yaw
        if self.visualize == 1:
            self._world.debug.draw_box(box=bounding_box, rotation=bounding_box.rotation, thickness=0.1, color=color, life_time=1.0 / self.frame_rate_sim)
        return vehicle_hazard or walker_hazard

    def _save_waypoints(self):
        speed = self._get_forward_speed()
        number_of_future_frames = int(self.waypoint_seconds * self.frame_rate)
        vehicle_transform = self._vehicle.get_transform()
        next_loc = np.array([vehicle_transform.location.x, vehicle_transform.location.y])
        next_yaw = np.array([vehicle_transform.rotation.yaw / 180.0 * np.pi])
        next_speed = np.array([speed])
        action = np.array(np.stack([self.steer, self.throttle, self.brake], axis=-1))
        ego_future = []
        for i in range(number_of_future_frames):
            next_loc, next_yaw, next_speed = self.ego_model.forward(next_loc, next_yaw, next_speed, action)
            next_loc_temp = np.array([-next_loc[1], next_loc[0]])
            next_yaw_temp = next_yaw.item() + np.pi / 2
            waypoint_route_temp = self._waypoint_planner.run_step(next_loc_temp)
            steer_temp = self._get_steer(self.brake, waypoint_route_temp, next_loc_temp, next_yaw_temp, next_speed, restore=False)
            throttle_temp = self._get_throttle(self.brake, self.target_speed, next_speed, restore=False)
            brake_temp = 1.0 if self._waypoint_planner.is_last else self.brake
            action = np.array(np.stack([steer_temp, float(throttle_temp), brake_temp], axis=-1))
            delta_yaws = next_yaw.item() * 180.0 / np.pi
            extent = self._vehicle.bounding_box.extent
            extent_org = self._vehicle.bounding_box.extent
            extent.x = extent.x / 2.0
            transform_whole = carla.Transform(carla.Location(x=next_loc[0].item(), y=next_loc[1].item(), z=vehicle_transform.location.z))
            bounding_box_whole = carla.BoundingBox(transform_whole.location, extent_org)
            bounding_box_whole.rotation = carla.Rotation(pitch=float(vehicle_transform.rotation.pitch), yaw=float(delta_yaws), roll=float(vehicle_transform.rotation.roll))
            ego_future.append(bounding_box_whole)
        self.future_states['ego'] = ego_future

    def _get_forward_speed(self, transform=None, velocity=None):
        """ Convert the vehicle transform directly to forward speed """
        if not velocity:
            velocity = self._vehicle.get_velocity()
        if not transform:
            transform = self._vehicle.get_transform()
        vel_np = np.array([velocity.x, velocity.y, velocity.z])
        pitch = np.deg2rad(transform.rotation.pitch)
        yaw = np.deg2rad(transform.rotation.yaw)
        orientation = np.array([np.cos(pitch) * np.cos(yaw), np.cos(pitch) * np.sin(yaw), np.sin(pitch)])
        speed = np.dot(vel_np, orientation)
        return speed

    def _get_position(self, gps):
        gps = (gps - self._command_planner.mean) * self._command_planner.scale
        return gps

    def dot_product(self, vector1, vector2):
        return vector1.x * vector2.x + vector1.y * vector2.y + vector1.z * vector2.z

    def cross_product(self, vector1, vector2):
        return carla.Vector3D(x=vector1.y * vector2.z - vector1.z * vector2.y, y=vector1.z * vector2.x - vector1.x * vector2.z, z=vector1.x * vector2.y - vector1.y * vector2.x)

    def get_separating_plane(self, rPos, plane, obb1, obb2):
        """ Checks if there is a seperating plane
        rPos Vec3
        plane Vec3
        obb1  Bounding Box
        obb2 Bounding Box
        """
        return abs(self.dot_product(rPos, plane)) > abs(self.dot_product(obb1.rotation.get_forward_vector() * obb1.extent.x, plane)) + abs(self.dot_product(obb1.rotation.get_right_vector() * obb1.extent.y, plane)) + abs(self.dot_product(obb1.rotation.get_up_vector() * obb1.extent.z, plane)) + abs(self.dot_product(obb2.rotation.get_forward_vector() * obb2.extent.x, plane)) + abs(self.dot_product(obb2.rotation.get_right_vector() * obb2.extent.y, plane)) + abs(self.dot_product(obb2.rotation.get_up_vector() * obb2.extent.z, plane))

    def check_obb_intersection(self, obb1, obb2):
        RPos = obb2.location - obb1.location
        return not (self.get_separating_plane(RPos, obb1.rotation.get_forward_vector(), obb1, obb2) or self.get_separating_plane(RPos, obb1.rotation.get_right_vector(), obb1, obb2) or self.get_separating_plane(RPos, obb1.rotation.get_up_vector(), obb1, obb2) or self.get_separating_plane(RPos, obb2.rotation.get_forward_vector(), obb1, obb2) or self.get_separating_plane(RPos, obb2.rotation.get_right_vector(), obb1, obb2) or self.get_separating_plane(RPos, obb2.rotation.get_up_vector(), obb1, obb2) or self.get_separating_plane(RPos, self.cross_product(obb1.rotation.get_forward_vector(), obb2.rotation.get_forward_vector()), obb1, obb2) or self.get_separating_plane(RPos, self.cross_product(obb1.rotation.get_forward_vector(), obb2.rotation.get_right_vector()), obb1, obb2) or self.get_separating_plane(RPos, self.cross_product(obb1.rotation.get_forward_vector(), obb2.rotation.get_up_vector()), obb1, obb2) or self.get_separating_plane(RPos, self.cross_product(obb1.rotation.get_right_vector(), obb2.rotation.get_forward_vector()), obb1, obb2) or self.get_separating_plane(RPos, self.cross_product(obb1.rotation.get_right_vector(), obb2.rotation.get_right_vector()), obb1, obb2) or self.get_separating_plane(RPos, self.cross_product(obb1.rotation.get_right_vector(), obb2.rotation.get_up_vector()), obb1, obb2) or self.get_separating_plane(RPos, self.cross_product(obb1.rotation.get_up_vector(), obb2.rotation.get_forward_vector()), obb1, obb2) or self.get_separating_plane(RPos, self.cross_product(obb1.rotation.get_up_vector(), obb2.rotation.get_right_vector()), obb1, obb2) or self.get_separating_plane(RPos, self.cross_product(obb1.rotation.get_up_vector(), obb2.rotation.get_up_vector()), obb1, obb2))

    def _get_angle_to_slow(self, pos, theta, target):
        R = np.array([[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]])
        aim = R.T.dot(target - pos)
        angle = -np.degrees(np.arctan2(-aim[1], aim[0]))
        angle = 0.0 if np.isnan(angle) else angle
        return angle

    def _get_angle_to(self, pos, theta, target):
        cos_theta = math.cos(theta)
        sin_theta = math.sin(theta)
        diff = target - pos
        aim_0 = cos_theta * diff[0] + sin_theta * diff[1]
        aim_1 = -sin_theta * diff[0] + cos_theta * diff[1]
        angle = -math.degrees(math.atan2(-aim_1, aim_0))
        angle = np.float_(angle)
        return angle

    def get_nearby_object(self, vehicle_position, actor_list, radius):
        nearby_objects = []
        for actor in actor_list:
            trigger_box_global_pos = actor.get_transform().transform(actor.trigger_volume.location)
            trigger_box_global_pos = carla.Location(x=trigger_box_global_pos.x, y=trigger_box_global_pos.y, z=trigger_box_global_pos.z)
            if trigger_box_global_pos.distance(vehicle_position) < radius:
                nearby_objects.append(actor)
        return nearby_objects

def setup(self, path_to_conf_file, route_index=None):
    self.track = autonomous_agent.Track.MAP
    self.config_path = path_to_conf_file
    self.step = -1
    self.wall_start = time.time()
    self.initialized = False
    self.save_path = None
    self.render_bev = False
    self.route_index = route_index
    self.frame_rate_sim = 20
    self.gps_buffer = deque(maxlen=100)
    self.frame_rate = 20
    self.ego_model = EgoModel(dt=1.0 / self.frame_rate)
    self.ego_model_gps = EgoModel(dt=1.0 / self.frame_rate_sim)
    self.vehicle_model = EgoModel(dt=1.0 / self.frame_rate)
    self.visualize = int(os.environ['DEBUG_CHALLENGE'])
    self.save_freq = self.frame_rate_sim // 2
    self.steer_buffer_size = 1
    self.target_speed_slow = 3.0
    self.target_speed_fast = 4.0
    self.clip_delta = 0.25
    self.clip_throttle = 0.75
    self.steer_damping = 0.5
    self.slope_pitch = 10.0
    self.slope_throttle = 0.4
    self.angle_search_range = 0
    self.steer_noise = 0.001
    self.steer_buffer = deque(maxlen=self.steer_buffer_size)
    self._turn_controller = PIDController(K_P=1.25, K_I=0.75, K_D=0.3, n=40)
    self._turn_controller_extrapolation = PIDController(K_P=1.25, K_I=0.75, K_D=0.3, n=40)
    self._speed_controller = PIDController(K_P=5.0, K_I=0.5, K_D=1.0, n=40)
    self._speed_controller_extrapolation = PIDController(K_P=5.0, K_I=0.5, K_D=1.0, n=40)
    self.center_bb_light_x = -2.0
    self.center_bb_light_y = 0.0
    self.center_bb_light_z = 0.0
    self.extent_bb_light_x = 4.5
    self.extent_bb_light_y = 1.5
    self.extent_bb_light_z = 2.0
    self.extrapolation_seconds_no_junction = 1.0
    self.extrapolation_seconds = 4.0
    self.waypoint_seconds = 4.0
    self.detection_radius = 30.0
    self.light_radius = 15.0
    self.vehicle_speed_buffer = defaultdict(lambda: {'velocity': [], 'throttle': [], 'brake': []})
    self.stuck_buffer_size = 30
    self.stuck_vel_threshold = 0.1
    self.stuck_throttle_threshold = 0.1
    self.stuck_brake_threshold = 0.1
    self.commands = deque(maxlen=2)
    self.commands.append(4)
    self.commands.append(4)
    self.far_node_prev = [100000.0, 100000.0]
    self.steer = 0.0
    self.throttle = 0.0
    self.brake = 0.0
    self.target_speed = 4.0
    self.angle = 0.0
    self.stop_sign_hazard = False
    self.traffic_light_hazard = False
    self.walker_hazard = [False for i in range(int(self.extrapolation_seconds * self.frame_rate))]
    self.vehicle_hazard = [False for i in range(int(self.extrapolation_seconds * self.frame_rate))]
    self.junction = False
    self.ignore_stop_signs = True
    self.cleared_stop_signs = []
    self.future_states = {}
    self._vehicle_lights = carla.VehicleLightState.Position | carla.VehicleLightState.LowBeam
    if SAVE_PATH is not None:
        now = datetime.datetime.now()
        string = pathlib.Path(os.environ['ROUTES']).stem + '_'
        string += f'route{self.route_index}_'
        string += '_'.join(map(lambda x: '%02d' % x, (now.month, now.day, now.hour, now.minute, now.second)))
        print(string)
        self.save_path = pathlib.Path(os.environ['SAVE_PATH']) / string
        self.save_path.mkdir(parents=True, exist_ok=False)
        (self.save_path / 'measurements').mkdir()

class PIDController(object):

    def __init__(self, K_P=1.0, K_I=0.0, K_D=0.0, n=20):
        self._K_P = K_P
        self._K_I = K_I
        self._K_D = K_D
        self._saved_window = deque([0 for _ in range(n)], maxlen=n)
        self._window = deque([0 for _ in range(n)], maxlen=n)
        self._max = 0.0
        self._min = 0.0

    def step(self, error):
        self._window.append(error)
        if len(self._window) >= 2:
            integral = sum(self._window) / len(self._window)
            derivative = self._window[-1] - self._window[-2]
        else:
            integral = 0.0
            derivative = 0.0
        if DEBUG:
            self._max = max(self._max, abs(error))
            self._min = -abs(self._max)
            import cv2
            canvas = np.ones((100, 100, 3), dtype=np.uint8)
            w = int(canvas.shape[1] / len(self._window))
            h = 99
            for i in range(1, len(self._window)):
                y1 = (self._max - self._window[i - 1]) / (self._max - self._min + 1e-08)
                y2 = (self._max - self._window[i]) / (self._max - self._min + 1e-08)
                cv2.line(canvas, ((i - 1) * w, int(y1 * h)), (i * w, int(y2 * h)), (255, 255, 255), 2)
            canvas = np.pad(canvas, ((5, 5), (5, 5), (0, 0)))
            cv2.imshow('%.3f %.3f %.3f' % (self._K_P, self._K_I, self._K_D), canvas)
            cv2.waitKey(1)
        return self._K_P * error + self._K_I * integral + self._K_D * derivative

    def save(self):
        self._saved_window = deepcopy(self._window)

    def load(self):
        self._window = self._saved_window

def save(self):
    self._saved_window = deepcopy(self._window)

class Plotter(object):

    def __init__(self, size):
        self.size = size
        self.clear()
        self.title = str(self.size)

    def clear(self):
        from PIL import Image, ImageDraw
        self.img = Image.fromarray(np.zeros((self.size, self.size, 3), dtype=np.uint8))
        self.draw = ImageDraw.Draw(self.img)

    def dot(self, pos, node, color=(255, 255, 255), r=2):
        x, y = 5.5 * (pos - node)
        x += self.size / 2
        y += self.size / 2
        self.draw.ellipse((x - r, y - r, x + r, y + r), color)

    def show(self):
        if not DEBUG:
            return
        import cv2
        cv2.imshow(self.title, cv2.cvtColor(np.array(self.img), cv2.COLOR_BGR2RGB))
        cv2.waitKey(1)

def __init__(self, size):
    self.size = size
    self.clear()
    self.title = str(self.size)

class RoutePlanner(object):

    def __init__(self, min_distance, max_distance, debug_size=256):
        self.saved_route = deque()
        self.route = deque()
        self.saved_route_distances = deque()
        self.route_distances = deque()
        self.min_distance = min_distance
        self.max_distance = max_distance
        self.is_last = False
        self.mean = np.array([0.0, 0.0])
        self.scale = np.array([111324.60662786, 111319.490945])

    def set_route(self, global_plan, gps=False):
        self.route.clear()
        for pos, cmd in global_plan:
            if gps:
                pos = np.array([pos['lat'], pos['lon']])
                pos -= self.mean
                pos *= self.scale
            else:
                pos = np.array([pos.location.x, pos.location.y])
                pos -= self.mean
            self.route.append((pos, cmd))
        self.route_distances.append(0.0)
        for i in range(1, len(self.route)):
            diff = self.route[i][0] - self.route[i - 1][0]
            distance = (diff[0] ** 2 + diff[1] ** 2) ** 0.5
            self.route_distances.append(distance)

    def run_step(self, gps):
        if len(self.route) <= 2:
            self.is_last = True
            return self.route
        to_pop = 0
        farthest_in_range = -np.inf
        cumulative_distance = 0.0
        for i in range(1, len(self.route)):
            if cumulative_distance > self.max_distance:
                break
            cumulative_distance += self.route_distances[i]
            diff = self.route[i][0] - gps
            distance = (diff[0] ** 2 + diff[1] ** 2) ** 0.5
            if distance <= self.min_distance and distance > farthest_in_range:
                farthest_in_range = distance
                to_pop = i
        for _ in range(to_pop):
            if len(self.route) > 2:
                self.route.popleft()
                self.route_distances.popleft()
        return self.route

    def save(self):
        self.saved_route = deepcopy(self.route)
        self.saved_route_distances = deepcopy(self.route_distances)

    def load(self):
        self.route = self.saved_route
        self.route_distances = self.saved_route_distances
        self.is_last = False

def set_route(self, global_plan, gps=False):
    self.route.clear()
    for pos, cmd in global_plan:
        if gps:
            pos = np.array([pos['lat'], pos['lon']])
            pos -= self.mean
            pos *= self.scale
        else:
            pos = np.array([pos.location.x, pos.location.y])
            pos -= self.mean
        self.route.append((pos, cmd))
    self.route_distances.append(0.0)
    for i in range(1, len(self.route)):
        diff = self.route[i][0] - self.route[i - 1][0]
        distance = (diff[0] ** 2 + diff[1] ** 2) ** 0.5
        self.route_distances.append(distance)

def save(self):
    self.saved_route = deepcopy(self.route)
    self.saved_route_distances = deepcopy(self.route_distances)

class DataAgent(AutoPilot):

    def setup(self, path_to_conf_file, route_index=None):
        super().setup(path_to_conf_file, route_index)
        self.cam_config = {'width': 320, 'height': 160, 'fov': 60}
        self.weathers = {'Clear': carla.WeatherParameters.ClearNoon, 'Cloudy': carla.WeatherParameters.CloudySunset, 'Wet': carla.WeatherParameters.WetSunset, 'MidRain': carla.WeatherParameters.MidRainSunset, 'WetCloudy': carla.WeatherParameters.WetCloudySunset, 'HardRain': carla.WeatherParameters.HardRainNoon, 'SoftRain': carla.WeatherParameters.SoftRainSunset}
        self.azimuths = [45.0 * i for i in range(8)]
        self.daytimes = {'Night': -80.0, 'Twilight': 0.0, 'Dawn': 5.0, 'Sunset': 15.0, 'Morning': 35.0, 'Noon': 75.0}
        self.weathers_ids = list(self.weathers)
        if self.save_path is not None:
            (self.save_path / 'topdown').mkdir()
            (self.save_path / 'lidar').mkdir()
            (self.save_path / 'rgb').mkdir()
            (self.save_path / 'label_raw').mkdir()
            (self.save_path / 'semantics').mkdir()
            (self.save_path / 'depth').mkdir()
        self._active_traffic_light = None

    def _init(self, hd_map):
        super()._init(hd_map)
        self._sensors = self.sensor_interface._sensors_objects
        self.vehicle_template = torch.ones(1, 1, 22, 9, device='cuda')
        self.walker_template = torch.ones(1, 1, 10, 7, device='cuda')
        self.traffic_light_template = torch.ones(1, 1, 4, 4, device='cuda')
        map_image = MapImage(self._world, self.world_map, PIXELS_PER_METER)
        make_image = lambda x: np.swapaxes(pygame.surfarray.array3d(x), 0, 1).mean(axis=-1)
        road = make_image(map_image.map_surface)
        lane = make_image(map_image.lane_surface)
        self.global_map = np.zeros((1, 15) + road.shape)
        self.global_map[:, 0, ...] = road / 255.0
        self.global_map[:, 1, ...] = lane / 255.0
        self.global_map = torch.tensor(self.global_map, device='cuda', dtype=torch.float32)
        world_offset = torch.tensor(map_image._world_offset, device='cuda', dtype=torch.float32)
        self.map_dims = self.global_map.shape[2:4]
        self.renderer = lts_rendering.Renderer(world_offset, self.map_dims, data_generation=True)

    def sensors(self):
        result = super().sensors()
        if self.save_path is not None:
            result += [{'type': 'sensor.camera.rgb', 'x': 1.3, 'y': 0.0, 'z': 2.3, 'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0, 'width': self.cam_config['width'], 'height': self.cam_config['height'], 'fov': self.cam_config['fov'], 'id': 'rgb_front'}, {'type': 'sensor.camera.rgb', 'x': 1.3, 'y': 0.0, 'z': 2.3, 'roll': 0.0, 'pitch': 0.0, 'yaw': -60.0, 'width': self.cam_config['width'], 'height': self.cam_config['height'], 'fov': self.cam_config['fov'], 'id': 'rgb_left'}, {'type': 'sensor.camera.rgb', 'x': 1.3, 'y': 0.0, 'z': 2.3, 'roll': 0.0, 'pitch': 0.0, 'yaw': 60.0, 'width': self.cam_config['width'], 'height': self.cam_config['height'], 'fov': self.cam_config['fov'], 'id': 'rgb_right'}, {'type': 'sensor.lidar.ray_cast', 'x': 1.3, 'y': 0.0, 'z': 2.5, 'roll': 0.0, 'pitch': 0.0, 'yaw': -90.0, 'rotation_frequency': 20, 'points_per_second': 1200000, 'id': 'lidar'}, {'type': 'sensor.camera.semantic_segmentation', 'x': 1.3, 'y': 0.0, 'z': 2.3, 'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0, 'width': self.cam_config['width'], 'height': self.cam_config['height'], 'fov': self.cam_config['fov'], 'id': 'semantics_front'}, {'type': 'sensor.camera.semantic_segmentation', 'x': 1.3, 'y': 0.0, 'z': 2.3, 'roll': 0.0, 'pitch': 0.0, 'yaw': -60.0, 'width': self.cam_config['width'], 'height': self.cam_config['height'], 'fov': self.cam_config['fov'], 'id': 'semantics_left'}, {'type': 'sensor.camera.semantic_segmentation', 'x': 1.3, 'y': 0.0, 'z': 2.3, 'roll': 0.0, 'pitch': 0.0, 'yaw': 60.0, 'width': self.cam_config['width'], 'height': self.cam_config['height'], 'fov': self.cam_config['fov'], 'id': 'semantics_right'}, {'type': 'sensor.camera.depth', 'x': 1.3, 'y': 0.0, 'z': 2.3, 'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0, 'width': self.cam_config['width'], 'height': self.cam_config['height'], 'fov': self.cam_config['fov'], 'id': 'depth_front'}, {'type': 'sensor.camera.depth', 'x': 1.3, 'y': 0.0, 'z': 2.3, 'roll': 0.0, 'pitch': 0.0, 'yaw': -60.0, 'width': self.cam_config['width'], 'height': self.cam_config['height'], 'fov': self.cam_config['fov'], 'id': 'depth_left'}, {'type': 'sensor.camera.depth', 'x': 1.3, 'y': 0.0, 'z': 2.3, 'roll': 0.0, 'pitch': 0.0, 'yaw': 60.0, 'width': self.cam_config['width'], 'height': self.cam_config['height'], 'fov': self.cam_config['fov'], 'id': 'depth_right'}]
        return result

    def tick(self, input_data):
        result = super().tick(input_data)
        if self.save_path is not None:
            rgb = []
            semantics = []
            depth = []
            for pos in ['left', 'front', 'right']:
                rgb_cam = 'rgb_' + pos
                semantics_cam = 'semantics_' + pos
                depth_cam = 'depth_' + pos
                semantics_img = input_data[semantics_cam][1][:, :, 2]
                depth_img = input_data[depth_cam][1][:, :, :3]
                _semantics = np.copy(semantics_img)
                _depth = self._get_depth(depth_img)
                self._change_seg_tl(_semantics, _depth, self._active_traffic_light)
                rgb.append(cv2.cvtColor(input_data[rgb_cam][1][:, :, :3], cv2.COLOR_BGR2RGB))
                semantics.append(_semantics)
                depth.append(depth_img)
            rgb = np.concatenate(rgb, axis=1)
            semantics = np.concatenate(semantics, axis=1)
            depth = np.concatenate(depth, axis=1)
            result['topdown'] = self.render_BEV()
            lidar = input_data['lidar']
            cars = self.get_bev_cars(lidar=lidar)
            result.update({'lidar': lidar, 'rgb': rgb, 'cars': cars, 'semantics': semantics, 'depth': depth})
        return result

    @torch.no_grad()
    def run_step(self, input_data, timestamp):
        if not 'hd_map' in input_data.keys() and (not self.initialized):
            control = carla.VehicleControl()
            control.steer = 0.0
            control.throttle = 0.0
            control.brake = 1.0
            return control
        control = super().run_step(input_data, timestamp)
        if self.step % self.save_freq == 0:
            if self.save_path is not None:
                tick_data = self.tick(input_data)
                self.save_sensors(tick_data)
                self.shuffle_weather()
        return control

    def shuffle_weather(self):
        index = random.choice(range(len(self.weathers)))
        dtime, altitude = random.choice(list(self.daytimes.items()))
        altitude = np.random.normal(altitude, 10)
        self.weather_id = self.weathers_ids[index] + dtime
        weather = self.weathers[self.weathers_ids[index]]
        weather.sun_altitude_angle = altitude
        weather.sun_azimuth_angle = np.random.choice(self.azimuths)
        self._world.set_weather(weather)
        vehicles = self._world.get_actors().filter('*vehicle*')
        if weather.sun_altitude_angle < 0.0:
            for vehicle in vehicles:
                vehicle.set_light_state(carla.VehicleLightState(self._vehicle_lights))
        else:
            for vehicle in vehicles:
                vehicle.set_light_state(carla.VehicleLightState.NONE)

    def save_sensors(self, tick_data):
        frame = self.step // self.save_freq
        img = cv2.cvtColor(tick_data['rgb'], cv2.COLOR_RGB2BGR)
        cv2.imwrite(str(self.save_path / 'rgb' / ('%04d.png' % frame)), img)
        img = encode_npy_to_pil(np.asarray(tick_data['topdown'].squeeze().cpu()))
        img_save = np.moveaxis(img, 0, 2)
        cv2.imwrite(str(self.save_path / 'topdown' / ('encoded_%04d.png' % frame)), img_save)
        semantics = tick_data['semantics']
        cv2.imwrite(str(self.save_path / 'semantics' / ('%04d.png' % frame)), semantics)
        depth = cv2.cvtColor(tick_data['depth'], cv2.COLOR_RGB2BGR)
        cv2.imwrite(str(self.save_path / 'depth' / ('%04d.png' % frame)), depth)
        np.save(self.save_path / 'lidar' / ('%04d.npy' % frame), tick_data['lidar'], allow_pickle=True)
        self.save_labels(self.save_path / 'label_raw' / ('%04d.json' % frame), tick_data['cars'])

    def save_labels(self, filename, result):
        with open(filename, 'w') as f:
            json.dump(result, f, indent=4)
        return

    def save_points(self, filename, points):
        points_to_save = deepcopy(points[1])
        points_to_save[:, 1] = -points_to_save[:, 1]
        np.save(filename, points_to_save)
        return

    def destroy(self):
        del self.global_map
        del self.vehicle_template
        del self.walker_template
        del self.traffic_light_template
        del self.map_dims
        torch.cuda.empty_cache()

    def get_bev_cars(self, lidar=None):
        results = []
        ego_rotation = self._vehicle.get_transform().rotation
        ego_matrix = np.array(self._vehicle.get_transform().get_matrix())
        ego_extent = self._vehicle.bounding_box.extent
        ego_dx = np.array([ego_extent.x, ego_extent.y, ego_extent.z]) * 2.0
        ego_yaw = ego_rotation.yaw / 180 * np.pi
        relative_yaw = 0
        relative_pos = self.get_relative_transform(ego_matrix, ego_matrix)
        ego_transform = self._vehicle.get_transform()
        ego_control = self._vehicle.get_control()
        ego_velocity = self._vehicle.get_velocity()
        ego_speed = self._get_forward_speed(transform=ego_transform, velocity=ego_velocity)
        ego_brake = ego_control.brake
        result = {'class': 'Car', 'extent': [ego_dx[2], ego_dx[0], ego_dx[1]], 'position': [relative_pos[0], relative_pos[1], relative_pos[2]], 'yaw': relative_yaw, 'num_points': -1, 'distance': -1, 'speed': ego_speed, 'brake': ego_brake, 'id': int(self._vehicle.id), 'ego_matrix': self._vehicle.get_transform().get_matrix()}
        results.append(result)
        self._actors = self._world.get_actors()
        vehicles = self._actors.filter('*vehicle*')
        for vehicle in vehicles:
            if vehicle.get_location().distance(self._vehicle.get_location()) < 50:
                if vehicle.id != self._vehicle.id:
                    vehicle_rotation = vehicle.get_transform().rotation
                    vehicle_matrix = np.array(vehicle.get_transform().get_matrix())
                    vehicle_id = vehicle.id
                    vehicle_extent = vehicle.bounding_box.extent
                    dx = np.array([vehicle_extent.x, vehicle_extent.y, vehicle_extent.z]) * 2.0
                    yaw = vehicle_rotation.yaw / 180 * np.pi
                    relative_yaw = yaw - ego_yaw
                    relative_pos = self.get_relative_transform(ego_matrix, vehicle_matrix)
                    vehicle_transform = vehicle.get_transform()
                    vehicle_control = vehicle.get_control()
                    vehicle_velocity = vehicle.get_velocity()
                    vehicle_speed = self._get_forward_speed(transform=vehicle_transform, velocity=vehicle_velocity)
                    vehicle_brake = vehicle_control.brake
                    if not lidar is None:
                        num_in_bbox_points = self.get_points_in_bbox(ego_matrix, vehicle_matrix, dx, lidar)
                    else:
                        num_in_bbox_points = -1
                    distance = np.linalg.norm(relative_pos)
                    result = {'class': 'Car', 'extent': [dx[2], dx[0], dx[1]], 'position': [relative_pos[0], relative_pos[1], relative_pos[2]], 'yaw': relative_yaw, 'num_points': int(num_in_bbox_points), 'distance': distance, 'speed': vehicle_speed, 'brake': vehicle_brake, 'id': int(vehicle_id), 'ego_matrix': vehicle.get_transform().get_matrix()}
                    results.append(result)
        return results

    def get_points_in_bbox(self, ego_matrix, vehicle_matrix, dx, lidar):
        Tr_lidar_2_ego = self.get_lidar_to_vehicle_transform()
        Tr_lidar_2_vehicle = np.linalg.inv(vehicle_matrix) @ ego_matrix @ Tr_lidar_2_ego
        lidar_vehicle = Tr_lidar_2_vehicle[:3, :3] @ lidar[1][:, :3].T + Tr_lidar_2_vehicle[:3, 3:]
        x, y, z = dx / 2.0
        x, y = (y, x)
        num_points = ((lidar_vehicle[0] < x) & (lidar_vehicle[0] > -x) & (lidar_vehicle[1] < y) & (lidar_vehicle[1] > -y) & (lidar_vehicle[2] < z) & (lidar_vehicle[2] > -z)).sum()
        return num_points

    def get_relative_transform(self, ego_matrix, vehicle_matrix):
        """
        return the relative transform from ego_pose to vehicle pose
        """
        relative_pos = vehicle_matrix[:3, 3] - ego_matrix[:3, 3]
        rot = ego_matrix[:3, :3].T
        relative_pos = rot @ relative_pos
        relative_pos[1] = -relative_pos[1]
        rot = np.eye(3)
        trans = -np.array([1.3, 0.0, 2.5])
        relative_pos = rot @ relative_pos + trans
        return relative_pos

    def get_lidar_to_vehicle_transform(self):
        rot = np.array([[0, 1, 0], [-1, 0, 0], [0, 0, 1]], dtype=np.float32)
        T = np.eye(4)
        T[0, 3] = 1.3
        T[1, 3] = 0.0
        T[2, 3] = 2.5
        T[:3, :3] = rot
        return T

    def get_vehicle_to_lidar_transform(self):
        return np.linalg.inv(self.get_lidar_to_vehicle_transform())

    def get_image_to_vehicle_transform(self):
        T = np.eye(4)
        T[0, 3] = 1.3
        T[1, 3] = 0.0
        T[2, 3] = 2.3
        rot = np.array([[0, -1, 0], [0, 0, -1], [1, 0, 0]], dtype=np.float32)
        T[:3, :3] = rot.T
        return T

    def get_vehicle_to_image_transform(self):
        return np.linalg.inv(self.get_image_to_vehicle_transform())

    def get_lidar_to_image_transform(self):
        Tr_lidar_to_vehicle = self.get_lidar_to_vehicle_transform()
        Tr_image_to_vehicle = self.get_image_to_vehicle_transform()
        T_lidar_to_image = np.linalg.inv(Tr_image_to_vehicle) @ Tr_lidar_to_vehicle
        return T_lidar_to_image

    def render_BEV(self):
        semantic_grid = self.global_map
        vehicle_position = self._vehicle.get_location()
        ego_pos_list = [self._vehicle.get_transform().location.x, self._vehicle.get_transform().location.y]
        ego_yaw_list = [self._vehicle.get_transform().rotation.yaw / 180 * np.pi]
        ego_pos = torch.tensor([self._vehicle.get_transform().location.x, self._vehicle.get_transform().location.y], device='cuda', dtype=torch.float32)
        ego_yaw = torch.tensor([self._vehicle.get_transform().rotation.yaw / 180 * np.pi], device='cuda', dtype=torch.float32)
        birdview = self.renderer.get_local_birdview(semantic_grid, ego_pos, ego_yaw)
        self._actors = self._world.get_actors()
        vehicles = self._actors.filter('*vehicle*')
        for vehicle in vehicles:
            if vehicle.get_location().distance(self._vehicle.get_location()) < self.detection_radius:
                if vehicle.id != self._vehicle.id:
                    pos = torch.tensor([vehicle.get_transform().location.x, vehicle.get_transform().location.y], device='cuda', dtype=torch.float32)
                    yaw = torch.tensor([vehicle.get_transform().rotation.yaw / 180 * np.pi], device='cuda', dtype=torch.float32)
                    veh_x_extent = int(max(vehicle.bounding_box.extent.x * 2, 1) * PIXELS_PER_METER)
                    veh_y_extent = int(max(vehicle.bounding_box.extent.y * 2, 1) * PIXELS_PER_METER)
                    self.vehicle_template = torch.ones(1, 1, veh_x_extent, veh_y_extent, device='cuda')
                    self.renderer.render_agent_bv(birdview, ego_pos, ego_yaw, self.vehicle_template, pos, yaw, channel=5)
        ego_pos_batched = []
        ego_yaw_batched = []
        pos_batched = []
        yaw_batched = []
        template_batched = []
        channel_batched = []
        walkers = self._actors.filter('*walker*')
        for walker in walkers:
            ego_pos_batched.append(ego_pos_list)
            ego_yaw_batched.append(ego_yaw_list)
            pos_batched.append([walker.get_transform().location.x, walker.get_transform().location.y])
            yaw_batched.append([walker.get_transform().rotation.yaw / 180 * np.pi])
            channel_batched.append(6)
            template_batched.append(np.ones([20, 7]))
        if len(ego_pos_batched) > 0:
            ego_pos_batched_torch = torch.tensor(ego_pos_batched, device='cuda', dtype=torch.float32).unsqueeze(1)
            ego_yaw_batched_torch = torch.tensor(ego_yaw_batched, device='cuda', dtype=torch.float32).unsqueeze(1)
            pos_batched_torch = torch.tensor(pos_batched, device='cuda', dtype=torch.float32).unsqueeze(1)
            yaw_batched_torch = torch.tensor(yaw_batched, device='cuda', dtype=torch.float32).unsqueeze(1)
            template_batched_torch = torch.tensor(template_batched, device='cuda', dtype=torch.float32).unsqueeze(1)
            channel_batched_torch = torch.tensor(channel_batched, device='cuda', dtype=torch.float32)
            self.renderer.render_agent_bv_batched(birdview, ego_pos_batched_torch, ego_yaw_batched_torch, template_batched_torch, pos_batched_torch, yaw_batched_torch, channel=channel_batched_torch)
        ego_pos_batched = []
        ego_yaw_batched = []
        pos_batched = []
        yaw_batched = []
        template_batched = []
        channel_batched = []
        traffic_lights = self._actors.filter('*traffic_light*')
        for traffic_light in traffic_lights:
            trigger_box_global_pos = traffic_light.get_transform().transform(traffic_light.trigger_volume.location)
            trigger_box_global_pos = carla.Location(x=trigger_box_global_pos.x, y=trigger_box_global_pos.y, z=trigger_box_global_pos.z)
            if trigger_box_global_pos.distance(vehicle_position) > self.light_radius:
                continue
            ego_pos_batched.append(ego_pos_list)
            ego_yaw_batched.append(ego_yaw_list)
            pos_batched.append([traffic_light.get_transform().location.x, traffic_light.get_transform().location.y])
            yaw_batched.append([traffic_light.get_transform().rotation.yaw / 180 * np.pi])
            template_batched.append(np.ones([4, 4]))
            if str(traffic_light.state) == 'Green':
                channel_batched.append(4)
            elif str(traffic_light.state) == 'Yellow':
                channel_batched.append(3)
            elif str(traffic_light.state) == 'Red':
                channel_batched.append(2)
        if len(ego_pos_batched) > 0:
            ego_pos_batched_torch = torch.tensor(ego_pos_batched, device='cuda', dtype=torch.float32).unsqueeze(1)
            ego_yaw_batched_torch = torch.tensor(ego_yaw_batched, device='cuda', dtype=torch.float32).unsqueeze(1)
            pos_batched_torch = torch.tensor(pos_batched, device='cuda', dtype=torch.float32).unsqueeze(1)
            yaw_batched_torch = torch.tensor(yaw_batched, device='cuda', dtype=torch.float32).unsqueeze(1)
            template_batched_torch = torch.tensor(template_batched, device='cuda', dtype=torch.float32).unsqueeze(1)
            channel_batched_torch = torch.tensor(channel_batched, device='cuda', dtype=torch.int)
            self.renderer.render_agent_bv_batched(birdview, ego_pos_batched_torch, ego_yaw_batched_torch, template_batched_torch, pos_batched_torch, yaw_batched_torch, channel=channel_batched_torch)
        return birdview

    def _change_seg_tl(self, seg_img, depth_img, tl, _region_size=4):
        """Adds 3 traffic light classes (green, yellow, red) to the segmentation image
        Args:
            seg_img ([type]): [description]
            depth_img ([type]): [description]
            traffic_lights ([type]): [description]
            _region_size (int, optional): [description]. Defaults to 4.
        """
        if tl is not None:
            _dist = self._get_distance_from_camera(tl.get_transform().location)
            _region = np.abs(depth_img - _dist)
            if tl.get_state() == carla.TrafficLightState.Red:
                state = 23
            elif tl.get_state() == carla.TrafficLightState.Yellow:
                state = 24
            else:
                state = 18
            seg_img[(_region < _region_size) & (seg_img == 18)] = state

    def _get_distance_from_camera(self, target):
        """Returns the distance from the (rgb) camera to the target
        Args:
            target ([type]): [description]
        Returns:
            [type]: [description]
        """
        sensor_transform = self._sensors['rgb_front'].get_transform()
        distance = np.sqrt((sensor_transform.location.x - target.x) ** 2 + (sensor_transform.location.y - target.y) ** 2 + (sensor_transform.location.z - target.z) ** 2)
        return distance

    def _get_depth(self, data):
        """Transforms the depth image into meters
        Args:
            data ([type]): [description]
        Returns:
            [type]: [description]
        """
        data = data.astype(np.float32)
        normalized = np.dot(data, [65536.0, 256.0, 1.0])
        normalized /= 256 * 256 * 256 - 1
        in_meters = 1000 * normalized
        return in_meters

def sensors(self):
    result = super().sensors()
    if self.save_path is not None:
        result += [{'type': 'sensor.camera.rgb', 'x': 1.3, 'y': 0.0, 'z': 2.3, 'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0, 'width': self.cam_config['width'], 'height': self.cam_config['height'], 'fov': self.cam_config['fov'], 'id': 'rgb_front'}, {'type': 'sensor.camera.rgb', 'x': 1.3, 'y': 0.0, 'z': 2.3, 'roll': 0.0, 'pitch': 0.0, 'yaw': -60.0, 'width': self.cam_config['width'], 'height': self.cam_config['height'], 'fov': self.cam_config['fov'], 'id': 'rgb_left'}, {'type': 'sensor.camera.rgb', 'x': 1.3, 'y': 0.0, 'z': 2.3, 'roll': 0.0, 'pitch': 0.0, 'yaw': 60.0, 'width': self.cam_config['width'], 'height': self.cam_config['height'], 'fov': self.cam_config['fov'], 'id': 'rgb_right'}, {'type': 'sensor.lidar.ray_cast', 'x': 1.3, 'y': 0.0, 'z': 2.5, 'roll': 0.0, 'pitch': 0.0, 'yaw': -90.0, 'rotation_frequency': 20, 'points_per_second': 1200000, 'id': 'lidar'}, {'type': 'sensor.camera.semantic_segmentation', 'x': 1.3, 'y': 0.0, 'z': 2.3, 'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0, 'width': self.cam_config['width'], 'height': self.cam_config['height'], 'fov': self.cam_config['fov'], 'id': 'semantics_front'}, {'type': 'sensor.camera.semantic_segmentation', 'x': 1.3, 'y': 0.0, 'z': 2.3, 'roll': 0.0, 'pitch': 0.0, 'yaw': -60.0, 'width': self.cam_config['width'], 'height': self.cam_config['height'], 'fov': self.cam_config['fov'], 'id': 'semantics_left'}, {'type': 'sensor.camera.semantic_segmentation', 'x': 1.3, 'y': 0.0, 'z': 2.3, 'roll': 0.0, 'pitch': 0.0, 'yaw': 60.0, 'width': self.cam_config['width'], 'height': self.cam_config['height'], 'fov': self.cam_config['fov'], 'id': 'semantics_right'}, {'type': 'sensor.camera.depth', 'x': 1.3, 'y': 0.0, 'z': 2.3, 'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0, 'width': self.cam_config['width'], 'height': self.cam_config['height'], 'fov': self.cam_config['fov'], 'id': 'depth_front'}, {'type': 'sensor.camera.depth', 'x': 1.3, 'y': 0.0, 'z': 2.3, 'roll': 0.0, 'pitch': 0.0, 'yaw': -60.0, 'width': self.cam_config['width'], 'height': self.cam_config['height'], 'fov': self.cam_config['fov'], 'id': 'depth_left'}, {'type': 'sensor.camera.depth', 'x': 1.3, 'y': 0.0, 'z': 2.3, 'roll': 0.0, 'pitch': 0.0, 'yaw': 60.0, 'width': self.cam_config['width'], 'height': self.cam_config['height'], 'fov': self.cam_config['fov'], 'id': 'depth_right'}]
    return result

class HybridAgent(autonomous_agent.AutonomousAgent):

    def setup(self, path_to_conf_file, route_index=None):
        self.track = autonomous_agent.Track.SENSORS
        self.config_path = path_to_conf_file
        self.step = -1
        self.initialized = False
        args_file = open(os.path.join(path_to_conf_file, 'args.txt'), 'r')
        self.args = json.load(args_file)
        args_file.close()
        self.config = GlobalConfig(setting='eval')
        if 'sync_batch_norm' in self.args:
            self.config.sync_batch_norm = bool(self.args['sync_batch_norm'])
        if 'use_point_pillars' in self.args:
            self.config.use_point_pillars = self.args['use_point_pillars']
        if 'n_layer' in self.args:
            self.config.n_layer = self.args['n_layer']
        if 'use_target_point_image' in self.args:
            self.config.use_target_point_image = bool(self.args['use_target_point_image'])
        if 'use_velocity' in self.args:
            use_velocity = bool(self.args['use_velocity'])
        else:
            use_velocity = True
        if 'image_architecture' in self.args:
            image_architecture = self.args['image_architecture']
        else:
            image_architecture = 'resnet34'
        if 'lidar_architecture' in self.args:
            lidar_architecture = self.args['lidar_architecture']
        else:
            lidar_architecture = 'resnet18'
        if 'backbone' in self.args:
            self.backbone = self.args['backbone']
        else:
            self.backbone = 'transFuser'
        self.gps_buffer = deque(maxlen=self.config.gps_buffer_max_len)
        self.ego_model = EgoModel(dt=self.config.carla_frame_rate)
        self.bb_buffer = deque(maxlen=1)
        self.lidar_pos = self.config.lidar_pos
        self.iou_treshold_nms = self.config.iou_treshold_nms
        self.nets = []
        self.model_count = 0
        for file in os.listdir(path_to_conf_file):
            if file.endswith('.pth'):
                self.model_count += 1
                print(os.path.join(path_to_conf_file, file))
                net = LidarCenterNet(self.config, 'cuda', self.backbone, image_architecture, lidar_architecture, use_velocity)
                if self.config.sync_batch_norm == True:
                    net = torch.nn.SyncBatchNorm.convert_sync_batchnorm(net)
                state_dict = torch.load(os.path.join(path_to_conf_file, file), map_location='cuda:0')
                state_dict = {k[7:]: v for k, v in state_dict.items()}
                net.load_state_dict(state_dict, strict=False)
                net.cuda()
                net.eval()
                self.nets.append(net)
        self.stuck_detector = 0
        self.forced_move = 0
        self.use_lidar_safe_check = True
        self.aug_degrees = [0]
        self.steer_damping = self.config.steer_damping
        self.rgb_back = None

    def _init(self):
        self._route_planner = RoutePlanner(self.config.route_planner_min_distance, self.config.route_planner_max_distance)
        self._route_planner.set_route(self._global_plan, True)
        self.initialized = True

    def _get_position(self, tick_data):
        gps = tick_data['gps']
        gps = (gps - self._route_planner.mean) * self._route_planner.scale
        return gps

    def sensors(self):
        sensors = [{'type': 'sensor.camera.rgb', 'x': self.config.camera_pos[0], 'y': self.config.camera_pos[1], 'z': self.config.camera_pos[2], 'roll': self.config.camera_rot_0[0], 'pitch': self.config.camera_rot_0[1], 'yaw': self.config.camera_rot_0[2], 'width': self.config.camera_width, 'height': self.config.camera_height, 'fov': self.config.camera_fov, 'id': 'rgb_front'}, {'type': 'sensor.camera.rgb', 'x': self.config.camera_pos[0], 'y': self.config.camera_pos[1], 'z': self.config.camera_pos[2], 'roll': self.config.camera_rot_1[0], 'pitch': self.config.camera_rot_1[1], 'yaw': self.config.camera_rot_1[2], 'width': self.config.camera_width, 'height': self.config.camera_height, 'fov': self.config.camera_fov, 'id': 'rgb_left'}, {'type': 'sensor.camera.rgb', 'x': self.config.camera_pos[0], 'y': self.config.camera_pos[1], 'z': self.config.camera_pos[2], 'roll': self.config.camera_rot_2[0], 'pitch': self.config.camera_rot_2[1], 'yaw': self.config.camera_rot_2[2], 'width': self.config.camera_width, 'height': self.config.camera_height, 'fov': self.config.camera_fov, 'id': 'rgb_right'}, {'type': 'sensor.other.imu', 'x': 0.0, 'y': 0.0, 'z': 0.0, 'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0, 'sensor_tick': self.config.carla_frame_rate, 'id': 'imu'}, {'type': 'sensor.other.gnss', 'x': 0.0, 'y': 0.0, 'z': 0.0, 'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0, 'sensor_tick': 0.01, 'id': 'gps'}, {'type': 'sensor.speedometer', 'reading_frequency': self.config.carla_fps, 'id': 'speed'}]
        if SAVE_PATH != None:
            sensors.append({'type': 'sensor.camera.rgb', 'x': -4.5, 'y': 0.0, 'z': 2.3, 'roll': 0.0, 'pitch': -15.0, 'yaw': 0.0, 'width': 960, 'height': 480, 'fov': 100, 'id': 'rgb_back'})
        if self.backbone != 'latentTF':
            sensors.append({'type': 'sensor.lidar.ray_cast', 'x': self.lidar_pos[0], 'y': self.lidar_pos[1], 'z': self.lidar_pos[2], 'roll': self.config.lidar_rot[0], 'pitch': self.config.lidar_rot[1], 'yaw': self.config.lidar_rot[2], 'id': 'lidar'})
        return sensors

    def tick(self, input_data):
        rgb = []
        for pos in ['left', 'front', 'right']:
            rgb_cam = 'rgb_' + pos
            rgb_pos = cv2.cvtColor(input_data[rgb_cam][1][:, :, :3], cv2.COLOR_BGR2RGB)
            rgb_pos = self.scale_crop(Image.fromarray(rgb_pos), self.config.scale, self.config.img_width, self.config.img_width, self.config.img_resolution[0], self.config.img_resolution[0])
            rgb.append(rgb_pos)
        rgb = np.concatenate(rgb, axis=1)
        if SAVE_PATH != None:
            self.rgb_back = input_data['rgb_back'][1][:, :, :3]
        gps = input_data['gps'][1][:2]
        speed = input_data['speed'][1]['speed']
        compass = input_data['imu'][1][-1]
        if np.isnan(compass) == True:
            compass = 0.0
        result = {'rgb': rgb, 'gps': gps, 'speed': speed, 'compass': compass}
        if self.backbone != 'latentTF':
            lidar = input_data['lidar'][1][:, :3]
            result['lidar'] = lidar
        pos = self._get_position(result)
        result['gps'] = pos
        self.gps_buffer.append(pos)
        denoised_pos = np.average(self.gps_buffer, axis=0)
        waypoint_route = self._route_planner.run_step(denoised_pos)
        next_wp, next_cmd = waypoint_route[1] if len(waypoint_route) > 1 else waypoint_route[0]
        result['next_command'] = next_cmd.value
        theta = compass + np.pi / 2
        R = np.array([[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]])
        local_command_point = np.array([next_wp[0] - denoised_pos[0], next_wp[1] - denoised_pos[1]])
        local_command_point = R.T.dot(local_command_point)
        result['target_point'] = tuple(local_command_point)
        return result

    @torch.inference_mode()
    def run_step(self, input_data, timestamp):
        self.step += 1
        if not self.initialized:
            self._init()
            control = carla.VehicleControl()
            control.steer = 0.0
            control.throttle = 0.0
            control.brake = 1.0
            self.control = control
        tick_data = self.tick(input_data)
        if self.step % self.config.action_repeat == 1:
            self.update_gps_buffer(self.control, tick_data['compass'], tick_data['speed'])
            return self.control
        image = self.prepare_image(tick_data)
        num_points = None
        if self.backbone == 'latentTF':
            lidar_bev = torch.zeros((1, 2, self.config.lidar_resolution_width, self.config.lidar_resolution_height)).to('cuda', dtype=torch.float32)
        elif self.config.use_point_pillars == True:
            lidar_cloud = deepcopy(input_data['lidar'][1])
            lidar_cloud[:, 1] *= -1
            lidar_bev = [torch.tensor(lidar_cloud).to('cuda', dtype=torch.float32)]
            num_points = [torch.tensor(len(lidar_cloud)).to('cuda', dtype=torch.int32)]
        else:
            lidar_bev = self.prepare_lidar(tick_data)
        target_point_image, target_point = self.prepare_goal_location(tick_data)
        gt_velocity = torch.FloatTensor([tick_data['speed']]).to('cuda', dtype=torch.float32)
        velocity = gt_velocity.reshape(1, 1)
        is_stuck = False
        if self.stuck_detector > self.config.stuck_threshold and self.forced_move < self.config.creep_duration:
            print('Detected agent being stuck. Move for frame: ', self.forced_move)
            is_stuck = True
            self.forced_move += 1
        with torch.no_grad():
            pred_wps = []
            bounding_boxes = []
            for i in range(self.model_count):
                rotated_bb = []
                if self.backbone == 'transFuser':
                    pred_wp, _ = self.nets[i].forward_ego(image, lidar_bev, target_point, target_point_image, velocity, num_points=num_points, save_path=SAVE_PATH, stuck_detector=self.stuck_detector, forced_move=is_stuck, debug=self.config.debug, rgb_back=self.rgb_back)
                elif self.backbone == 'late_fusion':
                    pred_wp, _ = self.nets[i].forward_ego(image, lidar_bev, target_point, target_point_image, velocity, num_points=num_points)
                elif self.backbone == 'geometric_fusion':
                    bev_points = list()
                    cam_points = list()
                    curr_bev_points, curr_cam_points = lidar_bev_cam_correspondences(deepcopy(tick_data['lidar']), lidar_bev, image, self.step, False)
                    bev_points.append(torch.from_numpy(curr_bev_points).unsqueeze(0))
                    cam_points.append(torch.from_numpy(curr_cam_points).unsqueeze(0))
                    bev_points = bev_points[0].long().to('cuda', dtype=torch.int64)
                    cam_points = cam_points[0].long().to('cuda', dtype=torch.int64)
                    pred_wp, _ = self.nets[i].forward_ego(image, lidar_bev, target_point, target_point_image, velocity, bev_points, cam_points, num_points=num_points)
                elif self.backbone == 'latentTF':
                    pred_wp, rotated_bb = self.nets[i].forward_ego(image, lidar_bev, target_point, target_point_image, velocity, num_points=num_points)
                else:
                    raise 'The chosen vision backbone does not exist. The options are: transFuser, late_fusion, geometric_fusion, latentTF'
                pred_wps.append(pred_wp)
                bounding_boxes.append(rotated_bb)
        bbs_vehicle_coordinate_system = self.non_maximum_suppression(bounding_boxes, self.iou_treshold_nms)
        self.bb_buffer.append(bbs_vehicle_coordinate_system)
        self.pred_wp = torch.stack(pred_wps, dim=0).mean(dim=0)
        pred_wp_transformed = []
        for i, degree in enumerate(self.aug_degrees):
            rad = np.deg2rad(degree)
            degree_matrix = np.array([[np.cos(rad), np.sin(rad)], [-np.sin(rad), np.cos(rad)]])
            degree_matrix = degree_matrix.T
            cur_pred_wp = self.pred_wp[i].detach().cpu().numpy()
            transformed_wp = (degree_matrix @ cur_pred_wp.T).T
            pred_wp_transformed.append(transformed_wp)
        self.pred_wp = np.stack(pred_wp_transformed, axis=0)
        self.pred_wp = torch.median(torch.from_numpy(self.pred_wp).to('cuda', dtype=torch.float32), dim=0, keepdims=True)[0]
        if self.backbone == 'latentTF':
            safety_box = []
            if self.bb_detected_in_front_of_vehicle(gt_velocity) == True:
                safety_box.append(True)
        else:
            safety_box = deepcopy(tick_data['lidar'])
            safety_box[:, 1] *= -1
            safety_box = safety_box[safety_box[..., 2] > self.config.safety_box_z_min]
            safety_box = safety_box[safety_box[..., 2] < self.config.safety_box_z_max]
            safety_box = safety_box[safety_box[..., 1] > self.config.safety_box_y_min]
            safety_box = safety_box[safety_box[..., 1] < self.config.safety_box_y_max]
            safety_box = safety_box[safety_box[..., 0] > self.config.safety_box_x_min]
            safety_box = safety_box[safety_box[..., 0] < self.config.safety_box_x_max]
        steer, throttle, brake = self.nets[0].control_pid(self.pred_wp, gt_velocity, is_stuck)
        if is_stuck and self.forced_move == 1:
            steer = 0.0
        if brake or is_stuck:
            steer *= self.steer_damping
        if gt_velocity < 0.1:
            self.stuck_detector += 1
        elif gt_velocity > 0.1 and is_stuck == False:
            self.stuck_detector = 0
            self.forced_move = 0
        control = carla.VehicleControl()
        control.steer = float(steer)
        control.throttle = float(throttle)
        control.brake = float(brake)
        if self.use_lidar_safe_check:
            emergency_stop = len(safety_box) > 0
            if emergency_stop == True and is_stuck == True:
                print('Detected object directly in front of the vehicle. Stopping. Step:', self.step)
                control.steer = float(steer)
                control.throttle = float(0.0)
                control.brake = float(True)
        self.control = control
        self.update_gps_buffer(self.control, tick_data['compass'], tick_data['speed'])
        return control

    def bb_detected_in_front_of_vehicle(self, ego_speed):
        if len(self.bb_buffer) < 1:
            return False
        collision_predicted = False
        extent_x = self.config.ego_extent_x
        extent_y = self.config.ego_extent_y
        extent_z = self.config.ego_extent_z
        extent = carla.Vector3D(extent_x, extent_y, extent_z)
        bremsweg = (ego_speed.cpu().numpy().item() * 3.6 / 10.0) ** 2 / 2.0
        safety_x = np.clip(bremsweg + 1.0, a_min=2.0, a_max=4.0)
        center_safety_box = carla.Location(x=safety_x, y=0.0, z=1.0)
        safety_bounding_box = carla.BoundingBox(center_safety_box, extent)
        safety_bounding_box.rotation = carla.Rotation(0.0, 0.0, 0.0)
        for bb in self.bb_buffer[-1]:
            bb_orientation = self.get_bb_yaw(bb)
            bb_extent_x = 0.5 * np.sqrt((bb[3, 0] - bb[0, 0]) ** 2 + (bb[3, 1] - bb[0, 1]) ** 2)
            bb_extent_y = 0.5 * np.sqrt((bb[0, 0] - bb[1, 0]) ** 2 + (bb[0, 1] - bb[1, 1]) ** 2)
            bb_extent_z = 1.0
            loc_local = carla.Location(bb[4, 0], bb[4, 1], 0.0)
            extent_det = carla.Vector3D(bb_extent_x, bb_extent_y, bb_extent_z)
            bb_local = carla.BoundingBox(loc_local, extent_det)
            bb_local.rotation = carla.Rotation(0.0, np.rad2deg(bb_orientation).item(), 0.0)
            if self.check_obb_intersection(safety_bounding_box, bb_local) == True:
                collision_predicted = True
        return collision_predicted

    def non_maximum_suppression(self, bounding_boxes, iou_treshhold):
        filtered_boxes = []
        bounding_boxes = np.array(list(itertools.chain.from_iterable(bounding_boxes)), dtype=np.object)
        if bounding_boxes.size == 0:
            return filtered_boxes
        confidences_indices = np.argsort(bounding_boxes[:, 2])
        while len(confidences_indices) > 0:
            idx = confidences_indices[-1]
            current_bb = bounding_boxes[idx, 0]
            filtered_boxes.append(current_bb)
            confidences_indices = confidences_indices[:-1]
            if len(confidences_indices) == 0:
                break
            for idx2 in deepcopy(confidences_indices):
                if self.iou_bbs(current_bb, bounding_boxes[idx2, 0]) > iou_treshhold:
                    confidences_indices = confidences_indices[confidences_indices != idx2]
        return filtered_boxes

    def update_gps_buffer(self, control, theta, speed):
        yaw = np.array([theta - np.pi / 2.0])
        speed = np.array([speed])
        action = np.array(np.stack([control.steer, control.throttle, control.brake], axis=-1))
        for i in range(len(self.gps_buffer)):
            loc = self.gps_buffer[i]
            loc_temp = np.array([loc[1], -loc[0]])
            next_loc_tmp, _, _ = self.ego_model.forward(loc_temp, yaw, speed, action)
            next_loc = np.array([-next_loc_tmp[1], next_loc_tmp[0]])
            self.gps_buffer[i] = next_loc
        return None

    def get_bb_yaw(self, box):
        location_2 = box[2]
        location_3 = box[3]
        location_4 = box[4]
        center_top = 0.5 * (location_3 - location_2) + location_2
        vector_top = center_top - location_4
        rotation_yaw = np.arctan2(vector_top[1], vector_top[0])
        return rotation_yaw

    def prepare_image(self, tick_data):
        image = Image.fromarray(tick_data['rgb'])
        image_degrees = []
        for degree in self.aug_degrees:
            crop_shift = degree / 60 * self.config.img_width
            rgb = torch.from_numpy(self.shift_x_scale_crop(image, scale=self.config.scale, crop=self.config.img_resolution, crop_shift=crop_shift)).unsqueeze(0)
            image_degrees.append(rgb.to('cuda', dtype=torch.float32))
        image = torch.cat(image_degrees, dim=0)
        return image

    def iou_bbs(self, bb1, bb2):
        a = Polygon([(bb1[0, 0], bb1[0, 1]), (bb1[1, 0], bb1[1, 1]), (bb1[2, 0], bb1[2, 1]), (bb1[3, 0], bb1[3, 1])])
        b = Polygon([(bb2[0, 0], bb2[0, 1]), (bb2[1, 0], bb2[1, 1]), (bb2[2, 0], bb2[2, 1]), (bb2[3, 0], bb2[3, 1])])
        intersection_area = a.intersection(b).area
        union_area = a.union(b).area
        iou = intersection_area / union_area
        return iou

    def dot_product(self, vector1, vector2):
        return vector1.x * vector2.x + vector1.y * vector2.y + vector1.z * vector2.z

    def cross_product(self, vector1, vector2):
        return carla.Vector3D(x=vector1.y * vector2.z - vector1.z * vector2.y, y=vector1.z * vector2.x - vector1.x * vector2.z, z=vector1.x * vector2.y - vector1.y * vector2.x)

    def get_separating_plane(self, rPos, plane, obb1, obb2):
        """ Checks if there is a seperating plane
        rPos Vec3
        plane Vec3
        obb1  Bounding Box
        obb2 Bounding Box
        """
        return abs(self.dot_product(rPos, plane)) > abs(self.dot_product(obb1.rotation.get_forward_vector() * obb1.extent.x, plane)) + abs(self.dot_product(obb1.rotation.get_right_vector() * obb1.extent.y, plane)) + abs(self.dot_product(obb1.rotation.get_up_vector() * obb1.extent.z, plane)) + abs(self.dot_product(obb2.rotation.get_forward_vector() * obb2.extent.x, plane)) + abs(self.dot_product(obb2.rotation.get_right_vector() * obb2.extent.y, plane)) + abs(self.dot_product(obb2.rotation.get_up_vector() * obb2.extent.z, plane))

    def check_obb_intersection(self, obb1, obb2):
        RPos = obb2.location - obb1.location
        return not (self.get_separating_plane(RPos, obb1.rotation.get_forward_vector(), obb1, obb2) or self.get_separating_plane(RPos, obb1.rotation.get_right_vector(), obb1, obb2) or self.get_separating_plane(RPos, obb1.rotation.get_up_vector(), obb1, obb2) or self.get_separating_plane(RPos, obb2.rotation.get_forward_vector(), obb1, obb2) or self.get_separating_plane(RPos, obb2.rotation.get_right_vector(), obb1, obb2) or self.get_separating_plane(RPos, obb2.rotation.get_up_vector(), obb1, obb2) or self.get_separating_plane(RPos, self.cross_product(obb1.rotation.get_forward_vector(), obb2.rotation.get_forward_vector()), obb1, obb2) or self.get_separating_plane(RPos, self.cross_product(obb1.rotation.get_forward_vector(), obb2.rotation.get_right_vector()), obb1, obb2) or self.get_separating_plane(RPos, self.cross_product(obb1.rotation.get_forward_vector(), obb2.rotation.get_up_vector()), obb1, obb2) or self.get_separating_plane(RPos, self.cross_product(obb1.rotation.get_right_vector(), obb2.rotation.get_forward_vector()), obb1, obb2) or self.get_separating_plane(RPos, self.cross_product(obb1.rotation.get_right_vector(), obb2.rotation.get_right_vector()), obb1, obb2) or self.get_separating_plane(RPos, self.cross_product(obb1.rotation.get_right_vector(), obb2.rotation.get_up_vector()), obb1, obb2) or self.get_separating_plane(RPos, self.cross_product(obb1.rotation.get_up_vector(), obb2.rotation.get_forward_vector()), obb1, obb2) or self.get_separating_plane(RPos, self.cross_product(obb1.rotation.get_up_vector(), obb2.rotation.get_right_vector()), obb1, obb2) or self.get_separating_plane(RPos, self.cross_product(obb1.rotation.get_up_vector(), obb2.rotation.get_up_vector()), obb1, obb2))

    def prepare_lidar(self, tick_data):
        lidar_transformed = deepcopy(tick_data['lidar'])
        lidar_transformed[:, 1] *= -1
        lidar_transformed = torch.from_numpy(lidar_to_histogram_features(lidar_transformed)).unsqueeze(0)
        lidar_transformed_degrees = [lidar_transformed.to('cuda', dtype=torch.float32)]
        lidar_bev = torch.cat(lidar_transformed_degrees[::-1], dim=1)
        return lidar_bev

    def prepare_goal_location(self, tick_data):
        tick_data['target_point'] = [torch.FloatTensor([tick_data['target_point'][0]]), torch.FloatTensor([tick_data['target_point'][1]])]
        target_point = torch.stack(tick_data['target_point'], dim=1).to('cuda', dtype=torch.float32)
        target_point_image_degrees = []
        target_point_degrees = []
        for degree in self.aug_degrees:
            rad = np.deg2rad(degree)
            degree_matrix = np.array([[np.cos(rad), np.sin(rad)], [-np.sin(rad), np.cos(rad)]])
            current_target_point = (degree_matrix @ target_point[0].cpu().numpy().reshape(2, 1)).T
            target_point_image = draw_target_point(current_target_point[0])
            target_point_image = torch.from_numpy(target_point_image)[None].to('cuda', dtype=torch.float32)
            target_point_image_degrees.append(target_point_image)
            target_point_degrees.append(torch.from_numpy(current_target_point))
        target_point_image = torch.cat(target_point_image_degrees, dim=0)
        target_point = torch.cat(target_point_degrees, dim=0).to('cuda', dtype=torch.float32)
        return (target_point_image, target_point)

    def scale_crop(self, image, scale=1, start_x=0, crop_x=None, start_y=0, crop_y=None):
        width, height = (image.width // scale, image.height // scale)
        if scale != 1:
            image = image.resize((width, height))
        if crop_x is None:
            crop_x = width
        if crop_y is None:
            crop_y = height
        image = np.asarray(image)
        cropped_image = image[start_y:start_y + crop_y, start_x:start_x + crop_x]
        return cropped_image

    def shift_x_scale_crop(self, image, scale, crop, crop_shift=0):
        crop_h, crop_w = crop
        width, height = (int(image.width // scale), int(image.height // scale))
        im_resized = image.resize((width, height))
        image = np.array(im_resized)
        start_y = height // 2 - crop_h // 2
        start_x = width // 2 - crop_w // 2
        start_x += int(crop_shift // scale)
        cropped_image = image[start_y:start_y + crop_h, start_x:start_x + crop_w]
        cropped_image = np.transpose(cropped_image, (2, 0, 1))
        return cropped_image

    def destroy(self):
        del self.nets

def non_maximum_suppression(self, bounding_boxes, iou_treshhold):
    filtered_boxes = []
    bounding_boxes = np.array(list(itertools.chain.from_iterable(bounding_boxes)), dtype=np.object)
    if bounding_boxes.size == 0:
        return filtered_boxes
    confidences_indices = np.argsort(bounding_boxes[:, 2])
    while len(confidences_indices) > 0:
        idx = confidences_indices[-1]
        current_bb = bounding_boxes[idx, 0]
        filtered_boxes.append(current_bb)
        confidences_indices = confidences_indices[:-1]
        if len(confidences_indices) == 0:
            break
        for idx2 in deepcopy(confidences_indices):
            if self.iou_bbs(current_bb, bounding_boxes[idx2, 0]) > iou_treshhold:
                confidences_indices = confidences_indices[confidences_indices != idx2]
    return filtered_boxes

class RoutePlanner(object):

    def __init__(self, min_distance, max_distance):
        self.saved_route = deque()
        self.route = deque()
        self.min_distance = min_distance
        self.max_distance = max_distance
        self.is_last = False
        self.mean = np.array([0.0, 0.0])
        self.scale = np.array([111324.60662786, 111319.490945])

    def set_route(self, global_plan, gps=False):
        self.route.clear()
        for pos, cmd in global_plan:
            if gps:
                pos = np.array([pos['lat'], pos['lon']])
                pos -= self.mean
                pos *= self.scale
            else:
                pos = np.array([pos.location.x, pos.location.y])
                pos -= self.mean
            self.route.append((pos, cmd))

    def run_step(self, gps):
        if len(self.route) <= 2:
            self.is_last = True
            return self.route
        to_pop = 0
        farthest_in_range = -np.inf
        cumulative_distance = 0.0
        for i in range(1, len(self.route)):
            if cumulative_distance > self.max_distance:
                break
            cumulative_distance += np.linalg.norm(self.route[i][0] - self.route[i - 1][0])
            distance = np.linalg.norm(self.route[i][0] - gps)
            if distance <= self.min_distance and distance > farthest_in_range:
                farthest_in_range = distance
                to_pop = i
        for _ in range(to_pop):
            if len(self.route) > 2:
                self.route.popleft()
        return self.route

    def save(self):
        self.saved_route = deepcopy(self.route)

    def load(self):
        self.route = self.saved_route
        self.is_last = False

def set_route(self, global_plan, gps=False):
    self.route.clear()
    for pos, cmd in global_plan:
        if gps:
            pos = np.array([pos['lat'], pos['lon']])
            pos -= self.mean
            pos *= self.scale
        else:
            pos = np.array([pos.location.x, pos.location.y])
            pos -= self.mean
        self.route.append((pos, cmd))

def save(self):
    self.saved_route = deepcopy(self.route)

class Engine(object):
    """
    Engine that runs training.
    """

    def __init__(self, model, optimizer, dataloader_train, dataloader_val, args, config, writer, device, rank=0, world_size=1, parallel=False, cur_epoch=0):
        self.cur_epoch = cur_epoch
        self.bestval_epoch = cur_epoch
        self.train_loss = []
        self.val_loss = []
        self.bestval = 10000000000.0
        self.model = model
        self.optimizer = optimizer
        self.dataloader_train = dataloader_train
        self.dataloader_val = dataloader_val
        self.args = args
        self.config = config
        self.writer = writer
        self.device = device
        self.rank = rank
        self.world_size = world_size
        self.parallel = parallel
        self.vis_save_path = self.args.logdir + '/visualizations'
        if self.config.debug == True:
            pathlib.Path(self.vis_save_path).mkdir(parents=True, exist_ok=True)
        self.detailed_losses = config.detailed_losses
        if self.args.wp_only:
            detailed_losses_weights = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        else:
            detailed_losses_weights = config.detailed_losses_weights
        self.detailed_weights = {key: detailed_losses_weights[idx] for idx, key in enumerate(self.detailed_losses)}

    def load_data_compute_loss(self, data):
        rgb = data['rgb'].to(self.device, dtype=torch.float32)
        if self.config.multitask:
            depth = data['depth'].to(self.device, dtype=torch.float32)
            semantic = data['semantic'].squeeze(1).to(self.device, dtype=torch.long)
        else:
            depth = None
            semantic = None
        bev = data['bev'].to(self.device, dtype=torch.long)
        if self.config.use_point_pillars == True:
            lidar = data['lidar_raw'].to(self.device, dtype=torch.float32)
            num_points = data['num_points'].to(self.device, dtype=torch.int32)
        else:
            lidar = data['lidar'].to(self.device, dtype=torch.float32)
            num_points = None
        label = data['label'].to(self.device, dtype=torch.float32)
        ego_waypoint = data['ego_waypoint'].to(self.device, dtype=torch.float32)
        target_point = data['target_point'].to(self.device, dtype=torch.float32)
        target_point_image = data['target_point_image'].to(self.device, dtype=torch.float32)
        ego_vel = data['speed'].to(self.device, dtype=torch.float32)
        if self.args.backbone == 'transFuser' or self.args.backbone == 'late_fusion' or self.args.backbone == 'latentTF':
            losses = self.model(rgb, lidar, ego_waypoint=ego_waypoint, target_point=target_point, target_point_image=target_point_image, ego_vel=ego_vel.reshape(-1, 1), bev=bev, label=label, save_path=self.vis_save_path, depth=depth, semantic=semantic, num_points=num_points)
        elif self.args.backbone == 'geometric_fusion':
            bev_points = data['bev_points'].long().to('cuda', dtype=torch.int64)
            cam_points = data['cam_points'].long().to('cuda', dtype=torch.int64)
            losses = self.model(rgb, lidar, ego_waypoint=ego_waypoint, target_point=target_point, target_point_image=target_point_image, ego_vel=ego_vel.reshape(-1, 1), bev=bev, label=label, save_path=self.vis_save_path, depth=depth, semantic=semantic, num_points=num_points, bev_points=bev_points, cam_points=cam_points)
        else:
            raise 'The chosen vision backbone does not exist. The options are: transFuser, late_fusion, geometric_fusion, latentTF'
        return losses

    def train(self):
        self.model.train()
        num_batches = 0
        loss_epoch = 0.0
        detailed_losses_epoch = {key: 0.0 for key in self.detailed_losses}
        self.cur_epoch += 1
        for data in tqdm(self.dataloader_train):
            self.optimizer.zero_grad(set_to_none=True)
            losses = self.load_data_compute_loss(data)
            loss = torch.tensor(0.0).to(self.device, dtype=torch.float32)
            for key, value in losses.items():
                loss += self.detailed_weights[key] * value
                detailed_losses_epoch[key] += float(self.detailed_weights[key] * value.item())
            loss.backward()
            self.optimizer.step()
            num_batches += 1
            loss_epoch += float(loss.item())
        self.log_losses(loss_epoch, detailed_losses_epoch, num_batches, '')

    @torch.inference_mode()
    def validate(self):
        self.model.eval()
        num_batches = 0
        loss_epoch = 0.0
        detailed_val_losses_epoch = {key: 0.0 for key in self.detailed_losses}
        for data in tqdm(self.dataloader_val):
            losses = self.load_data_compute_loss(data)
            loss = torch.tensor(0.0).to(self.device, dtype=torch.float32)
            for key, value in losses.items():
                loss += self.detailed_weights[key] * value
                detailed_val_losses_epoch[key] += float(self.detailed_weights[key] * value.item())
            num_batches += 1
            loss_epoch += float(loss.item())
        self.log_losses(loss_epoch, detailed_val_losses_epoch, num_batches, 'val_')

    def log_losses(self, loss_epoch, detailed_losses_epoch, num_batches, prefix=''):
        loss_epoch = loss_epoch / num_batches
        for key, value in detailed_losses_epoch.items():
            detailed_losses_epoch[key] = value / num_batches
        gathered_detailed_losses = [None for _ in range(self.world_size)]
        gathered_loss = [None for _ in range(self.world_size)]
        if self.parallel == True:
            torch.distributed.gather_object(obj=detailed_losses_epoch, object_gather_list=gathered_detailed_losses if self.rank == 0 else None, dst=0)
            torch.distributed.gather_object(obj=loss_epoch, object_gather_list=gathered_loss if self.rank == 0 else None, dst=0)
        else:
            gathered_detailed_losses[0] = detailed_losses_epoch
            gathered_loss[0] = loss_epoch
        if self.rank == 0:
            aggregated_total_loss = sum(gathered_loss) / len(gathered_loss)
            self.writer.add_scalar(prefix + 'loss_total', aggregated_total_loss, self.cur_epoch)
            for key, value in detailed_losses_epoch.items():
                aggregated_value = 0.0
                for i in range(self.world_size):
                    aggregated_value += gathered_detailed_losses[i][key]
                aggregated_value = aggregated_value / self.world_size
                self.writer.add_scalar(prefix + key, aggregated_value, self.cur_epoch)

    def save(self):
        torch.save(self.model.state_dict(), os.path.join(self.args.logdir, 'model_%d.pth' % self.cur_epoch))
        torch.save(self.optimizer.state_dict(), os.path.join(self.args.logdir, 'optimizer_%d.pth' % self.cur_epoch))

def __init__(self, model, optimizer, dataloader_train, dataloader_val, args, config, writer, device, rank=0, world_size=1, parallel=False, cur_epoch=0):
    self.cur_epoch = cur_epoch
    self.bestval_epoch = cur_epoch
    self.train_loss = []
    self.val_loss = []
    self.bestval = 10000000000.0
    self.model = model
    self.optimizer = optimizer
    self.dataloader_train = dataloader_train
    self.dataloader_val = dataloader_val
    self.args = args
    self.config = config
    self.writer = writer
    self.device = device
    self.rank = rank
    self.world_size = world_size
    self.parallel = parallel
    self.vis_save_path = self.args.logdir + '/visualizations'
    if self.config.debug == True:
        pathlib.Path(self.vis_save_path).mkdir(parents=True, exist_ok=True)
    self.detailed_losses = config.detailed_losses
    if self.args.wp_only:
        detailed_losses_weights = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    else:
        detailed_losses_weights = config.detailed_losses_weights
    self.detailed_weights = {key: detailed_losses_weights[idx] for idx, key in enumerate(self.detailed_losses)}

@HEADS.register_module()
class LidarCenterNetHead(BaseDenseHead, BBoxTestMixin):
    """Objects as Points Head. CenterHead use center_point to indicate object's
    position. Paper link <https://arxiv.org/abs/1904.07850>

    Args:
        in_channel (int): Number of channel in the input feature map.
        feat_channel (int): Number of channel in the intermediate feature map.
        num_classes (int): Number of categories excluding the background
            category.
        loss_center_heatmap (dict | None): Config of center heatmap loss.
            Default: GaussianFocalLoss.
        loss_wh (dict | None): Config of wh loss. Default: L1Loss.
        loss_offset (dict | None): Config of offset loss. Default: L1Loss.
        train_cfg (dict | None): Training config. Useless in CenterNet,
            but we keep this variable for SingleStageDetector. Default: None.
        test_cfg (dict | None): Testing config of CenterNet. Default: None.
        init_cfg (dict or list[dict], optional): Initialization config dict.
            Default: None
    """

    def __init__(self, in_channel, feat_channel, num_classes, loss_center_heatmap=dict(type='GaussianFocalLoss', loss_weight=1.0), loss_wh=dict(type='L1Loss', loss_weight=0.1), loss_offset=dict(type='L1Loss', loss_weight=1.0), loss_dir_class=dict(type='CrossEntropyLoss', loss_weight=1.0), loss_dir_res=dict(type='SmoothL1Loss', loss_weight=1.0), loss_velocity=dict(type='L1Loss', loss_weight=1.0), loss_brake=dict(type='CrossEntropyLoss', loss_weight=1.0), train_cfg=None, test_cfg=None, init_cfg=None):
        super(LidarCenterNetHead, self).__init__(init_cfg)
        self.num_classes = num_classes
        self.heatmap_head = self._build_head(in_channel, feat_channel, num_classes)
        self.wh_head = self._build_head(in_channel, feat_channel, 2)
        self.offset_head = self._build_head(in_channel, feat_channel, 2)
        self.num_dir_bins = train_cfg.num_dir_bins
        self.yaw_class_head = self._build_head(in_channel, feat_channel, self.num_dir_bins)
        self.yaw_res_head = self._build_head(in_channel, feat_channel, 1)
        self.velocity_head = self._build_head(in_channel, feat_channel, 1)
        self.brake_head = self._build_head(in_channel, feat_channel, 2)
        self.loss_center_heatmap = build_loss(loss_center_heatmap)
        self.loss_wh = build_loss(loss_wh)
        self.loss_offset = build_loss(loss_offset)
        self.loss_dir_class = build_loss(loss_dir_class)
        self.loss_dir_res = build_loss(loss_dir_res)
        self.loss_velocity = build_loss(loss_velocity)
        self.loss_brake = build_loss(loss_brake)
        self.train_cfg = train_cfg
        self.test_cfg = test_cfg
        self.fp16_enabled = train_cfg.fp16_enabled
        self.i = 0

    def _build_head(self, in_channel, feat_channel, out_channel):
        """Build head for each branch."""
        layer = nn.Sequential(nn.Conv2d(in_channel, feat_channel, kernel_size=3, padding=1), nn.ReLU(inplace=True), nn.Conv2d(feat_channel, out_channel, kernel_size=1))
        return layer

    def init_weights(self):
        """Initialize weights of the head."""
        bias_init = bias_init_with_prob(self.train_cfg.center_net_bias_init_with_prob)
        self.heatmap_head[-1].bias.data.fill_(bias_init)
        for head in [self.wh_head, self.offset_head]:
            for m in head.modules():
                if isinstance(m, nn.Conv2d):
                    normal_init(m, std=self.train_cfg.center_net_normal_init_std)

    def forward(self, feats):
        """Forward features. Notice CenterNet head does not use FPN.

        Args:
            feats (tuple[Tensor]): Features from the upstream network, each is
                a 4D-tensor.

        Returns:
            center_heatmap_preds (List[Tensor]): center predict heatmaps for
                all levels, the channels number is num_classes.
            wh_preds (List[Tensor]): wh predicts for all levels, the channels
                number is 2.
            offset_preds (List[Tensor]): offset predicts for all levels, the
               channels number is 2.
        """
        return multi_apply(self.forward_single, feats)

    def forward_single(self, feat):
        """Forward feature of a single level.

        Args:
            feat (Tensor): Feature of a single level.

        Returns:
            center_heatmap_pred (Tensor): center predict heatmaps, the
               channels number is num_classes.
            wh_pred (Tensor): wh predicts, the channels number is 2.
            offset_pred (Tensor): offset predicts, the channels number is 2.
        """
        center_heatmap_pred = self.heatmap_head(feat).sigmoid()
        wh_pred = self.wh_head(feat)
        offset_pred = self.offset_head(feat)
        yaw_class_pred = self.yaw_class_head(feat)
        yaw_res_pred = self.yaw_res_head(feat)
        velocity_pred = self.velocity_head(feat)
        brake_pred = self.brake_head(feat)
        return (center_heatmap_pred, wh_pred, offset_pred, yaw_class_pred, yaw_res_pred, velocity_pred, brake_pred)

    @force_fp32(apply_to=('center_heatmap_preds', 'wh_preds', 'offset_preds', 'yaw_class_preds', 'yaw_res_preds', 'velocity_pred', 'brake_pred'))
    def loss(self, center_heatmap_preds, wh_preds, offset_preds, yaw_class_preds, yaw_res_preds, velocity_preds, brake_preds, gt_bboxes, gt_labels, img_metas, gt_bboxes_ignore=None):
        """Compute losses of the head.

        Args:
            center_heatmap_preds (list[Tensor]): center predict heatmaps for
               all levels with shape (B, num_classes, H, W).
            wh_preds (list[Tensor]): wh predicts for all levels with
               shape (B, 2, H, W).
            offset_preds (list[Tensor]): offset predicts for all levels
               with shape (B, 2, H, W).
            gt_bboxes (list[Tensor]): Ground truth bboxes for each image with
                shape (num_gts, 4) in [tl_x, tl_y, br_x, br_y] format.
            gt_labels (list[Tensor]): class indices corresponding to each box.
            img_metas (list[dict]): Meta information of each image, e.g.,
                image size, scaling factor, etc.
            gt_bboxes_ignore (None | list[Tensor]): specify which bounding
                boxes can be ignored when computing the loss. Default: None

        Returns:
            dict[str, Tensor]: which has components below:
                - loss_center_heatmap (Tensor): loss of center heatmap.
                - loss_wh (Tensor): loss of hw heatmap
                - loss_offset (Tensor): loss of offset heatmap.
        """
        assert len(center_heatmap_preds) == len(wh_preds) == len(offset_preds) == 1
        center_heatmap_pred = center_heatmap_preds[0]
        wh_pred = wh_preds[0]
        offset_pred = offset_preds[0]
        yaw_class_pred = yaw_class_preds[0]
        yaw_res_pred = yaw_res_preds[0]
        velocity_pred = velocity_preds[0]
        brake_pred = brake_preds[0]
        target_result, avg_factor = self.get_targets(gt_bboxes, gt_labels, gt_bboxes_ignore, center_heatmap_pred.shape)
        center_heatmap_target = target_result['center_heatmap_target']
        wh_target = target_result['wh_target']
        yaw_class_target = target_result['yaw_class_target']
        yaw_res_target = target_result['yaw_res_target']
        offset_target = target_result['offset_target']
        velocity_target = target_result['velocity_target']
        brake_target = target_result['brake_target']
        wh_offset_target_weight = target_result['wh_offset_target_weight']
        loss_center_heatmap = self.loss_center_heatmap(center_heatmap_pred, center_heatmap_target, avg_factor=avg_factor)
        loss_wh = self.loss_wh(wh_pred, wh_target, wh_offset_target_weight, avg_factor=avg_factor * 2)
        loss_offset = self.loss_offset(offset_pred, offset_target, wh_offset_target_weight, avg_factor=avg_factor * 2)
        loss_yaw_class = self.loss_dir_class(yaw_class_pred, yaw_class_target, wh_offset_target_weight[:, :1, ...], avg_factor=avg_factor)
        loss_yaw_res = self.loss_dir_res(yaw_res_pred, yaw_res_target, wh_offset_target_weight[:, :1, ...], avg_factor=avg_factor)
        loss_velocity = self.loss_velocity(velocity_pred, velocity_target, wh_offset_target_weight[:, :1, ...], avg_factor=avg_factor)
        loss_brake = self.loss_brake(brake_pred, brake_target, wh_offset_target_weight[:, :1, ...], avg_factor=avg_factor)
        return dict(loss_center_heatmap=loss_center_heatmap, loss_wh=loss_wh, loss_offset=loss_offset, loss_yaw_class=loss_yaw_class, loss_yaw_res=loss_yaw_res, loss_velocity=loss_velocity, loss_brake=loss_brake)

    def angle2class(self, angle):
        """Convert continuous angle to a discrete class and a residual.
        Convert continuous angle to a discrete class and a small
        regression number from class center angle to current angle.
        Args:
            angle (torch.Tensor): Angle is from 0-2pi (or -pi~pi),
                class center at 0, 1*(2pi/N), 2*(2pi/N) ...  (N-1)*(2pi/N).
        Returns:
            tuple: Encoded discrete class and residual.
        """
        angle = angle % (2 * np.pi)
        angle_per_class = 2 * np.pi / float(self.num_dir_bins)
        shifted_angle = (angle + angle_per_class / 2) % (2 * np.pi)
        angle_cls = torch.div(shifted_angle, angle_per_class, rounding_mode='trunc')
        angle_res = shifted_angle - (angle_cls * angle_per_class + angle_per_class / 2)
        return (angle_cls.long(), angle_res)

    def class2angle(self, angle_cls, angle_res, limit_period=True):
        """Inverse function to angle2class.
        Args:
            angle_cls (torch.Tensor): Angle class to decode.
            angle_res (torch.Tensor): Angle residual to decode.
            limit_period (bool): Whether to limit angle to [-pi, pi].
        Returns:
            torch.Tensor: Angle decoded from angle_cls and angle_res.
        """
        angle_per_class = 2 * np.pi / float(self.num_dir_bins)
        angle_center = angle_cls.float() * angle_per_class
        angle = angle_center + angle_res
        if limit_period:
            angle[angle > np.pi] -= 2 * np.pi
        return angle

    def get_targets(self, gt_bboxes, gt_labels, gt_ignores, feat_shape):
        """Compute regression and classification targets in multiple images.

        Args:
            gt_bboxes (list[Tensor]): Ground truth bboxes for each image with
                shape (num_gts, 4) in [tl_x, tl_y, br_x, br_y] format.
            gt_labels (list[Tensor]): class indices corresponding to each box.
            feat_shape (list[int]): feature map shape with value [B, _, H, W]
            img_shape (list[int]): image shape in [h, w] format.

        Returns:
            tuple[dict,float]: The float value is mean avg_factor, the dict has
               components below:
               - center_heatmap_target (Tensor): targets of center heatmap,                    shape (B, num_classes, H, W).
               - wh_target (Tensor): targets of wh predict, shape                    (B, 2, H, W).
               - offset_target (Tensor): targets of offset predict, shape                    (B, 2, H, W).
               - wh_offset_target_weight (Tensor): weights of wh and offset                    predict, shape (B, 2, H, W).
        """
        img_h, img_w = (self.train_cfg.lidar_resolution_height, self.train_cfg.lidar_resolution_width)
        bs, _, feat_h, feat_w = feat_shape
        width_ratio = float(feat_w / img_w)
        height_ratio = float(feat_h / img_h)
        center_heatmap_target = gt_bboxes[-1].new_zeros([bs, self.num_classes, feat_h, feat_w])
        wh_target = gt_bboxes[-1].new_zeros([bs, 2, feat_h, feat_w])
        offset_target = gt_bboxes[-1].new_zeros([bs, 2, feat_h, feat_w])
        yaw_class_target = gt_bboxes[-1].new_zeros([bs, 1, feat_h, feat_w]).long()
        yaw_res_target = gt_bboxes[-1].new_zeros([bs, 1, feat_h, feat_w])
        velocity_target = gt_bboxes[-1].new_zeros([bs, 1, feat_h, feat_w])
        brake_target = gt_bboxes[-1].new_zeros([bs, 1, feat_h, feat_w]).long()
        wh_offset_target_weight = gt_bboxes[-1].new_zeros([bs, 2, feat_h, feat_w])
        for batch_id in range(bs):
            gt_bbox = gt_bboxes[0][batch_id]
            gt_label = gt_labels[0][batch_id]
            gt_ignore = gt_ignores[0][batch_id]
            center_x = gt_bbox[:, [0]] * width_ratio
            center_y = gt_bbox[:, [1]] * width_ratio
            gt_centers = torch.cat((center_x, center_y), dim=1)
            for j, ct in enumerate(gt_centers):
                if gt_ignore[j]:
                    continue
                ctx_int, cty_int = ct.int()
                ctx, cty = ct
                scale_box_h = gt_bbox[j, 3] * height_ratio
                scale_box_w = gt_bbox[j, 2] * width_ratio
                radius = gaussian_radius([scale_box_h, scale_box_w], min_overlap=0.1)
                radius = max(2, int(radius))
                ind = gt_label[j].long()
                gen_gaussian_target(center_heatmap_target[batch_id, ind], [ctx_int, cty_int], radius)
                wh_target[batch_id, 0, cty_int, ctx_int] = scale_box_w
                wh_target[batch_id, 1, cty_int, ctx_int] = scale_box_h
                yaw_class, yaw_res = self.angle2class(gt_bbox[j, 4])
                yaw_class_target[batch_id, 0, cty_int, ctx_int] = yaw_class
                yaw_res_target[batch_id, 0, cty_int, ctx_int] = yaw_res
                velocity_target[batch_id, 0, cty_int, ctx_int] = gt_bbox[j, 5]
                brake_target[batch_id, 0, cty_int, ctx_int] = gt_bbox[j, 6].long()
                offset_target[batch_id, 0, cty_int, ctx_int] = ctx - ctx_int
                offset_target[batch_id, 1, cty_int, ctx_int] = cty - cty_int
                wh_offset_target_weight[batch_id, :, cty_int, ctx_int] = 1
        avg_factor = max(1, center_heatmap_target.eq(1).sum())
        target_result = dict(center_heatmap_target=center_heatmap_target, wh_target=wh_target, yaw_class_target=yaw_class_target.squeeze(1), yaw_res_target=yaw_res_target, offset_target=offset_target, velocity_target=velocity_target, brake_target=brake_target.squeeze(1), wh_offset_target_weight=wh_offset_target_weight)
        return (target_result, avg_factor)

    def get_bboxes(self, center_heatmap_preds, wh_preds, offset_preds, yaw_class_preds, yaw_res_preds, velocity_preds, brake_preds, rescale=True, with_nms=False):
        """Transform network output for a batch into bbox predictions.

        Args:
            center_heatmap_preds (list[Tensor]): center predict heatmaps for
                all levels with shape (B, num_classes, H, W).
            wh_preds (list[Tensor]): wh predicts for all levels with
                shape (B, 2, H, W).
            offset_preds (list[Tensor]): offset predicts for all levels
                with shape (B, 2, H, W).
            img_metas (list[dict]): Meta information of each image, e.g.,
                image size, scaling factor, etc.
            rescale (bool): If True, return boxes in original image space.
                Default: True.
            with_nms (bool): If True, do nms before return boxes.
                Default: False.

        Returns:
            list[tuple[Tensor, Tensor]]: Each item in result_list is 2-tuple.
                The first item is an (n, 5) tensor, where 5 represent
                (tl_x, tl_y, br_x, br_y, score) and the score between 0 and 1.
                The shape of the second tensor in the tuple is (n,), and
                each element represents the class label of the corresponding
                box.
        """
        assert len(center_heatmap_preds) == len(wh_preds) == len(offset_preds) == 1
        batch_det_bboxes, batch_labels = self.decode_heatmap(center_heatmap_preds[0], wh_preds[0], offset_preds[0], yaw_class_preds[0], yaw_res_preds[0], velocity_preds[0], brake_preds[0], k=self.train_cfg.top_k_center_keypoints, kernel=self.train_cfg.center_net_max_pooling_kernel)
        if with_nms:
            det_results = []
            for det_bboxes, det_labels in zip(batch_det_bboxes, batch_labels):
                det_bbox, det_label = self._bboxes_nms(det_bboxes, det_labels, self.test_cfg)
                det_results.append(tuple([det_bbox, det_label]))
        else:
            det_results = [tuple(bs) for bs in zip(batch_det_bboxes, batch_labels)]
        return det_results

    def decode_heatmap(self, center_heatmap_pred, wh_pred, offset_pred, yaw_class_pred, yaw_res_pred, velocity_pred, brake_pred, k=100, kernel=3):
        """Transform outputs into detections raw bbox prediction.

        Args:
            center_heatmap_pred (Tensor): center predict heatmap,
               shape (B, num_classes, H, W).
            wh_pred (Tensor): wh predict, shape (B, 2, H, W).
            offset_pred (Tensor): offset predict, shape (B, 2, H, W).
            img_shape (list[int]): image shape in [h, w] format.
            k (int): Get top k center keypoints from heatmap. Default 100.
            kernel (int): Max pooling kernel for extract local maximum pixels.
               Default 3.

        Returns:
            tuple[torch.Tensor]: Decoded output of CenterNetHead, containing
               the following Tensors:

              - batch_bboxes (Tensor): Coords of each box with shape (B, k, 5)
              - batch_topk_labels (Tensor): Categories of each box with                   shape (B, k)
        """
        center_heatmap_pred = get_local_maximum(center_heatmap_pred, kernel=kernel)
        *batch_dets, topk_ys, topk_xs = get_topk_from_heatmap(center_heatmap_pred, k=k)
        batch_scores, batch_index, batch_topk_labels = batch_dets
        wh = transpose_and_gather_feat(wh_pred, batch_index)
        offset = transpose_and_gather_feat(offset_pred, batch_index)
        yaw_class = transpose_and_gather_feat(yaw_class_pred, batch_index)
        yaw_res = transpose_and_gather_feat(yaw_res_pred, batch_index)
        velocity = transpose_and_gather_feat(velocity_pred, batch_index)
        brake = transpose_and_gather_feat(brake_pred, batch_index)
        brake = torch.argmax(brake, -1)
        velocity = velocity[..., 0]
        yaw_class = torch.argmax(yaw_class, -1)
        yaw = self.class2angle(yaw_class, yaw_res.squeeze(2))
        topk_xs = topk_xs + offset[..., 0]
        topk_ys = topk_ys + offset[..., 1]
        ratio = 4.0
        batch_bboxes = torch.stack([topk_xs, topk_ys, wh[..., 0], wh[..., 1], yaw, velocity, brake], dim=2)
        batch_bboxes = torch.cat((batch_bboxes, batch_scores[..., None]), dim=-1)
        batch_bboxes[:, :, :4] *= ratio
        return (batch_bboxes, batch_topk_labels)

    def _bboxes_nms(self, bboxes, labels, cfg):
        if labels.numel() == 0:
            return (bboxes, labels)
        out_bboxes, keep = batched_nms(bboxes[:, :4].contiguous(), bboxes[:, -1].contiguous(), labels, cfg.nms_cfg)
        out_labels = labels[keep]
        if len(out_bboxes) > 0:
            idx = torch.argsort(out_bboxes[:, -1], descending=True)
            idx = idx[:cfg.max_per_img]
            out_bboxes = out_bboxes[idx]
            out_labels = out_labels[idx]
        return (out_bboxes, out_labels)

def _bboxes_nms(self, bboxes, labels, cfg):
    if labels.numel() == 0:
        return (bboxes, labels)
    out_bboxes, keep = batched_nms(bboxes[:, :4].contiguous(), bboxes[:, -1].contiguous(), labels, cfg.nms_cfg)
    out_labels = labels[keep]
    if len(out_bboxes) > 0:
        idx = torch.argsort(out_bboxes[:, -1], descending=True)
        idx = idx[:cfg.max_per_img]
        out_bboxes = out_bboxes[idx]
        out_labels = out_labels[idx]
    return (out_bboxes, out_labels)

