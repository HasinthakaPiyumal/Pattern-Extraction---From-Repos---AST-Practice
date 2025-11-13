# Cluster 30

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

class RouteScenario(BasicScenario):
    """
    Implementation of a RouteScenario, i.e. a scenario that consists of driving along a pre-defined route,
    along which several smaller scenarios are triggered
    """
    category = 'RouteScenario'

    def __init__(self, world, config, debug_mode=0, criteria_enable=True):
        """
        Setup all relevant parameters and create scenarios along route
        """
        self.config = config
        self.route = None
        self.sampled_scenarios_definitions = None
        self._update_route(world, config, debug_mode > 0)
        ego_vehicle = self._update_ego_vehicle()
        self.list_scenarios = self._build_scenario_instances(world, ego_vehicle, self.sampled_scenarios_definitions, scenarios_per_tick=10, timeout=self.timeout, debug_mode=debug_mode > 1)
        super(RouteScenario, self).__init__(name=config.name, ego_vehicles=[ego_vehicle], config=config, world=world, debug_mode=debug_mode > 1, terminate_on_failure=False, criteria_enable=criteria_enable)

    def _update_route(self, world, config, debug_mode):
        """
        Update the input route, i.e. refine waypoint list, and extract possible scenario locations

        Parameters:
        - world: CARLA world
        - config: Scenario configuration (RouteConfiguration)
        """
        world_annotations = RouteParser.parse_annotations_file(config.scenario_file)
        gps_route, route = interpolate_trajectory(world, config.trajectory)
        potential_scenarios_definitions, _ = RouteParser.scan_route_for_scenarios(config.town, route, world_annotations)
        self.route = route
        CarlaDataProvider.set_ego_vehicle_route(convert_transform_to_location(self.route))
        config.agent.set_global_plan(gps_route, self.route)
        self.sampled_scenarios_definitions = self._scenario_sampling(potential_scenarios_definitions)
        self.timeout = self._estimate_route_timeout()
        if debug_mode:
            self._draw_waypoints(world, self.route, vertical_shift=1.0, persistency=50000.0)

    def _update_ego_vehicle(self):
        """
        Set/Update the start position of the ego_vehicle
        """
        elevate_transform = self.route[0][0]
        elevate_transform.location.z += 0.5
        ego_vehicle = CarlaDataProvider.request_new_actor('vehicle.lincoln.mkz2017', elevate_transform, rolename='hero')
        spectator = CarlaDataProvider.get_world().get_spectator()
        ego_trans = ego_vehicle.get_transform()
        spectator.set_transform(carla.Transform(ego_trans.location + carla.Location(z=50), carla.Rotation(pitch=-90)))
        return ego_vehicle

    def _estimate_route_timeout(self):
        """
        Estimate the duration of the route
        """
        route_length = 0.0
        prev_point = self.route[0][0]
        for current_point, _ in self.route[1:]:
            dist = current_point.location.distance(prev_point.location)
            route_length += dist
            prev_point = current_point
        return int(SECONDS_GIVEN_PER_METERS * route_length + INITIAL_SECONDS_DELAY)

    def _draw_waypoints(self, world, waypoints, vertical_shift, persistency=-1):
        """
        Draw a list of waypoints at a certain height given in vertical_shift.
        """
        for w in waypoints:
            wp = w[0].location + carla.Location(z=vertical_shift)
            size = 0.2
            if w[1] == RoadOption.LEFT:
                color = carla.Color(255, 255, 0)
            elif w[1] == RoadOption.RIGHT:
                color = carla.Color(0, 255, 255)
            elif w[1] == RoadOption.CHANGELANELEFT:
                color = carla.Color(255, 64, 0)
            elif w[1] == RoadOption.CHANGELANERIGHT:
                color = carla.Color(0, 64, 255)
            elif w[1] == RoadOption.STRAIGHT:
                color = carla.Color(128, 128, 128)
            else:
                color = carla.Color(0, 255, 0)
                size = 0.1
            world.debug.draw_point(wp, size=size, color=color, life_time=persistency)
        world.debug.draw_point(waypoints[0][0].location + carla.Location(z=vertical_shift), size=0.2, color=carla.Color(0, 0, 255), life_time=persistency)
        world.debug.draw_point(waypoints[-1][0].location + carla.Location(z=vertical_shift), size=0.2, color=carla.Color(255, 0, 0), life_time=persistency)

    def _scenario_sampling(self, potential_scenarios_definitions, random_seed=0):
        """
        The function used to sample the scenarios that are going to happen for this route.
        """
        rgn = random.RandomState(random_seed)

        def position_sampled(scenario_choice, sampled_scenarios):
            """
            Check if a position was already sampled, i.e. used for another scenario
            """
            for existent_scenario in sampled_scenarios:
                if compare_scenarios(scenario_choice, existent_scenario):
                    return True
            return False

        def select_scenario(list_scenarios):
            higher_id = -1
            selected_scenario = None
            for scenario in list_scenarios:
                try:
                    scenario_number = int(scenario['name'].split('Scenario')[1])
                except:
                    scenario_number = -1
                if scenario_number >= higher_id:
                    higher_id = scenario_number
                    selected_scenario = scenario
            return selected_scenario
        sampled_scenarios = []
        for trigger in potential_scenarios_definitions.keys():
            possible_scenarios = potential_scenarios_definitions[trigger]
            scenario_choice = select_scenario(possible_scenarios)
            del possible_scenarios[possible_scenarios.index(scenario_choice)]
            while position_sampled(scenario_choice, sampled_scenarios):
                if possible_scenarios is None or not possible_scenarios:
                    scenario_choice = None
                    break
                scenario_choice = rgn.choice(possible_scenarios)
                del possible_scenarios[possible_scenarios.index(scenario_choice)]
            if scenario_choice is not None:
                sampled_scenarios.append(scenario_choice)
        return sampled_scenarios

    def _build_scenario_instances(self, world, ego_vehicle, scenario_definitions, scenarios_per_tick=5, timeout=300, debug_mode=False):
        """
        Based on the parsed route and possible scenarios, build all the scenario classes.
        """
        scenario_instance_vec = []
        if debug_mode:
            for scenario in scenario_definitions:
                loc = carla.Location(scenario['trigger_position']['x'], scenario['trigger_position']['y'], scenario['trigger_position']['z']) + carla.Location(z=2.0)
                world.debug.draw_point(loc, size=0.3, color=carla.Color(255, 0, 0), life_time=100000)
                world.debug.draw_string(loc, str(scenario['name']), draw_shadow=False, color=carla.Color(0, 0, 255), life_time=100000, persistent_lines=True)
        for scenario_number, definition in enumerate(scenario_definitions):
            scenario_class = NUMBER_CLASS_TRANSLATION[definition['name']]
            if definition['other_actors'] is not None:
                list_of_actor_conf_instances = self._get_actors_instances(definition['other_actors'])
            else:
                list_of_actor_conf_instances = []
            egoactor_trigger_position = convert_json_to_transform(definition['trigger_position'])
            scenario_configuration = ScenarioConfiguration()
            scenario_configuration.other_actors = list_of_actor_conf_instances
            scenario_configuration.trigger_points = [egoactor_trigger_position]
            scenario_configuration.subtype = definition['scenario_type']
            scenario_configuration.ego_vehicles = [ActorConfigurationData('vehicle.lincoln.mkz2017', ego_vehicle.get_transform(), 'hero')]
            route_var_name = 'ScenarioRouteNumber{}'.format(scenario_number)
            scenario_configuration.route_var_name = route_var_name
            try:
                scenario_instance = scenario_class(world, [ego_vehicle], scenario_configuration, criteria_enable=False, timeout=timeout)
                if scenario_number % scenarios_per_tick == 0:
                    if CarlaDataProvider.is_sync_mode():
                        world.tick()
                    else:
                        world.wait_for_tick()
            except Exception as e:
                print("Skipping scenario '{}' due to setup error: {}".format(definition['name'], e))
                continue
            scenario_instance_vec.append(scenario_instance)
        return scenario_instance_vec

    def _get_actors_instances(self, list_of_antagonist_actors):
        """
        Get the full list of actor instances.
        """

        def get_actors_from_list(list_of_actor_def):
            """
                Receives a list of actor definitions and creates an actual list of ActorConfigurationObjects
            """
            sublist_of_actors = []
            for actor_def in list_of_actor_def:
                sublist_of_actors.append(convert_json_to_actor(actor_def))
            return sublist_of_actors
        list_of_actors = []
        if 'front' in list_of_antagonist_actors:
            list_of_actors += get_actors_from_list(list_of_antagonist_actors['front'])
        if 'left' in list_of_antagonist_actors:
            list_of_actors += get_actors_from_list(list_of_antagonist_actors['left'])
        if 'right' in list_of_antagonist_actors:
            list_of_actors += get_actors_from_list(list_of_antagonist_actors['right'])
        return list_of_actors

    def _initialize_actors(self, config):
        """
        Set other_actors to the superset of all scenario actors
        """
        if int(os.environ.get('DATAGEN')) == 1:
            town_amount = {'Town01': 130, 'Town02': 60, 'Town03': 135, 'Town04': 190, 'Town05': 120, 'Town06': 155, 'Town07': 60, 'Town08': 180, 'Town09': 300, 'Town10HD': 80}
            amount = town_amount[config.town] if config.town in town_amount else 0
            amount = random.randint(amount, 2 * amount)
        else:
            amount = 500
        new_actors = CarlaDataProvider.request_new_batch_actors('vehicle.*', amount, carla.Transform(), autopilot=True, random_location=True, rolename='background')
        if new_actors is None:
            raise Exception('Error: Unable to add the background activity, all spawn points were occupied')
        for _actor in new_actors:
            self.other_actors.append(_actor)
        for scenario in self.list_scenarios:
            self.other_actors.extend(scenario.other_actors)

    def _create_behavior(self):
        """
        Basic behavior do nothing, i.e. Idle
        """
        scenario_trigger_distance = 1.5
        behavior = py_trees.composites.Parallel(policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)
        subbehavior = py_trees.composites.Parallel(name='Behavior', policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ALL)
        scenario_behaviors = []
        blackboard_list = []
        for i, scenario in enumerate(self.list_scenarios):
            if scenario.scenario.behavior is not None:
                route_var_name = scenario.config.route_var_name
                if route_var_name is not None:
                    scenario_behaviors.append(scenario.scenario.behavior)
                    blackboard_list.append([scenario.config.route_var_name, scenario.config.trigger_points[0].location])
                else:
                    name = '{} - {}'.format(i, scenario.scenario.behavior.name)
                    oneshot_idiom = oneshot_behavior(name=name, variable_name=name, behaviour=scenario.scenario.behavior)
                    scenario_behaviors.append(oneshot_idiom)
        scenario_triggerer = ScenarioTriggerer(self.ego_vehicles[0], self.route, blackboard_list, scenario_trigger_distance, repeat_scenarios=False)
        subbehavior.add_child(scenario_triggerer)
        subbehavior.add_children(scenario_behaviors)
        subbehavior.add_child(Idle())
        behavior.add_child(subbehavior)
        return behavior

    def _create_test_criteria(self):
        """
        """
        criteria = []
        route = convert_transform_to_location(self.route)
        collision_criterion = CollisionTest(self.ego_vehicles[0], terminate_on_failure=False)
        route_criterion = InRouteTest(self.ego_vehicles[0], route=route, offroad_max=30, terminate_on_failure=True)
        completion_criterion = RouteCompletionTest(self.ego_vehicles[0], route=route)
        outsidelane_criterion = OutsideRouteLanesTest(self.ego_vehicles[0], route=route)
        red_light_criterion = RunningRedLightTest(self.ego_vehicles[0])
        stop_criterion = RunningStopTest(self.ego_vehicles[0])
        blocked_criterion = ActorSpeedAboveThresholdTest(self.ego_vehicles[0], speed_threshold=0.1, below_threshold_max_time=180.0, terminate_on_failure=True, name='AgentBlockedTest')
        criteria.append(completion_criterion)
        criteria.append(outsidelane_criterion)
        criteria.append(collision_criterion)
        criteria.append(red_light_criterion)
        criteria.append(stop_criterion)
        criteria.append(route_criterion)
        criteria.append(blocked_criterion)
        return criteria

    def __del__(self):
        """
        Remove all actors upon deletion
        """
        self.remove_all_actors()

def select_scenario(list_scenarios):
    higher_id = -1
    selected_scenario = None
    for scenario in list_scenarios:
        try:
            scenario_number = int(scenario['name'].split('Scenario')[1])
        except:
            scenario_number = -1
        if scenario_number >= higher_id:
            higher_id = scenario_number
            selected_scenario = scenario
    return selected_scenario

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

class RouteScenario(BasicScenario):
    """
    Implementation of a RouteScenario, i.e. a scenario that consists of driving along a pre-defined route,
    along which several smaller scenarios are triggered
    """
    category = 'RouteScenario'

    def __init__(self, world, config, debug_mode=0, criteria_enable=True):
        """
        Setup all relevant parameters and create scenarios along route
        """
        self.config = config
        self.route = None
        self.sampled_scenarios_definitions = None
        self._update_route(world, config, debug_mode > 0)
        ego_vehicle = self._update_ego_vehicle()
        self.list_scenarios = self._build_scenario_instances(world, ego_vehicle, self.sampled_scenarios_definitions, scenarios_per_tick=10, timeout=self.timeout, debug_mode=debug_mode > 1)
        super(RouteScenario, self).__init__(name=config.name, ego_vehicles=[ego_vehicle], config=config, world=world, debug_mode=debug_mode > 1, terminate_on_failure=False, criteria_enable=criteria_enable)

    def _update_route(self, world, config, debug_mode):
        """
        Update the input route, i.e. refine waypoint list, and extract possible scenario locations

        Parameters:
        - world: CARLA world
        - config: Scenario configuration (RouteConfiguration)
        """
        world_annotations = RouteParser.parse_annotations_file(config.scenario_file)
        gps_route, route = interpolate_trajectory(world, config.trajectory)
        potential_scenarios_definitions, _ = RouteParser.scan_route_for_scenarios(config.town, route, world_annotations)
        self.route = route
        CarlaDataProvider.set_ego_vehicle_route(convert_transform_to_location(self.route))
        config.agent.set_global_plan(gps_route, self.route)
        self.sampled_scenarios_definitions = self._scenario_sampling(potential_scenarios_definitions)
        self.timeout = self._estimate_route_timeout()
        if debug_mode:
            self._draw_waypoints(world, self.route, vertical_shift=1.0, persistency=50000.0)

    def _update_ego_vehicle(self):
        """
        Set/Update the start position of the ego_vehicle
        """
        elevate_transform = self.route[0][0]
        elevate_transform.location.z += 0.5
        ego_vehicle = CarlaDataProvider.request_new_actor('vehicle.lincoln.mkz2017', elevate_transform, rolename='hero')
        spectator = CarlaDataProvider.get_world().get_spectator()
        ego_trans = ego_vehicle.get_transform()
        spectator.set_transform(carla.Transform(ego_trans.location + carla.Location(z=50), carla.Rotation(pitch=-90)))
        return ego_vehicle

    def _estimate_route_timeout(self):
        """
        Estimate the duration of the route
        """
        route_length = 0.0
        prev_point = self.route[0][0]
        for current_point, _ in self.route[1:]:
            dist = current_point.location.distance(prev_point.location)
            route_length += dist
            prev_point = current_point
        return int(SECONDS_GIVEN_PER_METERS * route_length + INITIAL_SECONDS_DELAY)

    def _draw_waypoints(self, world, waypoints, vertical_shift, persistency=-1):
        """
        Draw a list of waypoints at a certain height given in vertical_shift.
        """
        for w in waypoints:
            wp = w[0].location + carla.Location(z=vertical_shift)
            size = 0.2
            if w[1] == RoadOption.LEFT:
                color = carla.Color(255, 255, 0)
            elif w[1] == RoadOption.RIGHT:
                color = carla.Color(0, 255, 255)
            elif w[1] == RoadOption.CHANGELANELEFT:
                color = carla.Color(255, 64, 0)
            elif w[1] == RoadOption.CHANGELANERIGHT:
                color = carla.Color(0, 64, 255)
            elif w[1] == RoadOption.STRAIGHT:
                color = carla.Color(128, 128, 128)
            else:
                color = carla.Color(0, 255, 0)
                size = 0.1
            world.debug.draw_point(wp, size=size, color=color, life_time=persistency)
        world.debug.draw_point(waypoints[0][0].location + carla.Location(z=vertical_shift), size=0.2, color=carla.Color(0, 0, 255), life_time=persistency)
        world.debug.draw_point(waypoints[-1][0].location + carla.Location(z=vertical_shift), size=0.2, color=carla.Color(255, 0, 0), life_time=persistency)

    def _scenario_sampling(self, potential_scenarios_definitions, random_seed=0):
        """
        The function used to sample the scenarios that are going to happen for this route.
        """
        rgn = random.RandomState(random_seed)

        def position_sampled(scenario_choice, sampled_scenarios):
            """
            Check if a position was already sampled, i.e. used for another scenario
            """
            for existent_scenario in sampled_scenarios:
                if compare_scenarios(scenario_choice, existent_scenario):
                    return True
            return False

        def select_scenario(list_scenarios):
            higher_id = -1
            selected_scenario = None
            for scenario in list_scenarios:
                try:
                    scenario_number = int(scenario['name'].split('Scenario')[1])
                except:
                    scenario_number = -1
                if scenario_number >= higher_id:
                    higher_id = scenario_number
                    selected_scenario = scenario
            return selected_scenario
        sampled_scenarios = []
        for trigger in potential_scenarios_definitions.keys():
            possible_scenarios = potential_scenarios_definitions[trigger]
            scenario_choice = select_scenario(possible_scenarios)
            del possible_scenarios[possible_scenarios.index(scenario_choice)]
            while position_sampled(scenario_choice, sampled_scenarios):
                if possible_scenarios is None or not possible_scenarios:
                    scenario_choice = None
                    break
                scenario_choice = rgn.choice(possible_scenarios)
                del possible_scenarios[possible_scenarios.index(scenario_choice)]
            if scenario_choice is not None:
                sampled_scenarios.append(scenario_choice)
        return sampled_scenarios

    def _build_scenario_instances(self, world, ego_vehicle, scenario_definitions, scenarios_per_tick=5, timeout=300, debug_mode=False):
        """
        Based on the parsed route and possible scenarios, build all the scenario classes.
        """
        scenario_instance_vec = []
        if debug_mode:
            for scenario in scenario_definitions:
                loc = carla.Location(scenario['trigger_position']['x'], scenario['trigger_position']['y'], scenario['trigger_position']['z']) + carla.Location(z=2.0)
                world.debug.draw_point(loc, size=0.3, color=carla.Color(255, 0, 0), life_time=100000)
                world.debug.draw_string(loc, str(scenario['name']), draw_shadow=False, color=carla.Color(0, 0, 255), life_time=100000, persistent_lines=True)
        for scenario_number, definition in enumerate(scenario_definitions):
            scenario_class = NUMBER_CLASS_TRANSLATION[definition['name']]
            if definition['other_actors'] is not None:
                list_of_actor_conf_instances = self._get_actors_instances(definition['other_actors'])
            else:
                list_of_actor_conf_instances = []
            egoactor_trigger_position = convert_json_to_transform(definition['trigger_position'])
            scenario_configuration = ScenarioConfiguration()
            scenario_configuration.other_actors = list_of_actor_conf_instances
            scenario_configuration.trigger_points = [egoactor_trigger_position]
            scenario_configuration.subtype = definition['scenario_type']
            scenario_configuration.ego_vehicles = [ActorConfigurationData('vehicle.lincoln.mkz2017', ego_vehicle.get_transform(), 'hero')]
            route_var_name = 'ScenarioRouteNumber{}'.format(scenario_number)
            scenario_configuration.route_var_name = route_var_name
            try:
                scenario_instance = scenario_class(world, [ego_vehicle], scenario_configuration, criteria_enable=False, timeout=timeout)
                if scenario_number % scenarios_per_tick == 0:
                    if CarlaDataProvider.is_sync_mode():
                        world.tick()
                    else:
                        world.wait_for_tick()
            except Exception as e:
                print("Skipping scenario '{}' due to setup error: {}".format(definition['name'], e))
                continue
            scenario_instance_vec.append(scenario_instance)
        return scenario_instance_vec

    def _get_actors_instances(self, list_of_antagonist_actors):
        """
        Get the full list of actor instances.
        """

        def get_actors_from_list(list_of_actor_def):
            """
                Receives a list of actor definitions and creates an actual list of ActorConfigurationObjects
            """
            sublist_of_actors = []
            for actor_def in list_of_actor_def:
                sublist_of_actors.append(convert_json_to_actor(actor_def))
            return sublist_of_actors
        list_of_actors = []
        if 'front' in list_of_antagonist_actors:
            list_of_actors += get_actors_from_list(list_of_antagonist_actors['front'])
        if 'left' in list_of_antagonist_actors:
            list_of_actors += get_actors_from_list(list_of_antagonist_actors['left'])
        if 'right' in list_of_antagonist_actors:
            list_of_actors += get_actors_from_list(list_of_antagonist_actors['right'])
        return list_of_actors

    def _initialize_actors(self, config):
        """
        Set other_actors to the superset of all scenario actors
        """
        town_amount = {'Town01': 120, 'Town02': 100, 'Town03': 120, 'Town04': 200, 'Town05': 120, 'Town06': 150, 'Town07': 110, 'Town08': 180, 'Town09': 300, 'Town10HD': 120}
        amount = town_amount[config.town] if config.town in town_amount else 0
        new_actors = CarlaDataProvider.request_new_batch_actors('vehicle.*', amount, carla.Transform(), autopilot=True, random_location=True, rolename='background')
        if new_actors is None:
            raise Exception('Error: Unable to add the background activity, all spawn points were occupied')
        for _actor in new_actors:
            self.other_actors.append(_actor)
        for scenario in self.list_scenarios:
            self.other_actors.extend(scenario.other_actors)

    def _create_behavior(self):
        """
        Basic behavior do nothing, i.e. Idle
        """
        scenario_trigger_distance = 1.5
        behavior = py_trees.composites.Parallel(policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)
        subbehavior = py_trees.composites.Parallel(name='Behavior', policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ALL)
        scenario_behaviors = []
        blackboard_list = []
        for i, scenario in enumerate(self.list_scenarios):
            if scenario.scenario.behavior is not None:
                route_var_name = scenario.config.route_var_name
                if route_var_name is not None:
                    scenario_behaviors.append(scenario.scenario.behavior)
                    blackboard_list.append([scenario.config.route_var_name, scenario.config.trigger_points[0].location])
                else:
                    name = '{} - {}'.format(i, scenario.scenario.behavior.name)
                    oneshot_idiom = oneshot_behavior(name=name, variable_name=name, behaviour=scenario.scenario.behavior)
                    scenario_behaviors.append(oneshot_idiom)
        scenario_triggerer = ScenarioTriggerer(self.ego_vehicles[0], self.route, blackboard_list, scenario_trigger_distance, repeat_scenarios=False)
        subbehavior.add_child(scenario_triggerer)
        subbehavior.add_children(scenario_behaviors)
        subbehavior.add_child(Idle())
        behavior.add_child(subbehavior)
        return behavior

    def _create_test_criteria(self):
        """
        """
        criteria = []
        route = convert_transform_to_location(self.route)
        collision_criterion = CollisionTest(self.ego_vehicles[0], terminate_on_failure=False)
        route_criterion = InRouteTest(self.ego_vehicles[0], route=route, offroad_max=30, terminate_on_failure=True)
        completion_criterion = RouteCompletionTest(self.ego_vehicles[0], route=route)
        outsidelane_criterion = OutsideRouteLanesTest(self.ego_vehicles[0], route=route)
        red_light_criterion = RunningRedLightTest(self.ego_vehicles[0])
        stop_criterion = RunningStopTest(self.ego_vehicles[0])
        blocked_criterion = ActorSpeedAboveThresholdTest(self.ego_vehicles[0], speed_threshold=0.1, below_threshold_max_time=180.0, terminate_on_failure=True, name='AgentBlockedTest')
        criteria.append(completion_criterion)
        criteria.append(outsidelane_criterion)
        criteria.append(collision_criterion)
        criteria.append(red_light_criterion)
        criteria.append(stop_criterion)
        criteria.append(route_criterion)
        criteria.append(blocked_criterion)
        return criteria

    def __del__(self):
        """
        Remove all actors upon deletion
        """
        self.remove_all_actors()

def select_scenario(list_scenarios):
    higher_id = -1
    selected_scenario = None
    for scenario in list_scenarios:
        try:
            scenario_number = int(scenario['name'].split('Scenario')[1])
        except:
            scenario_number = -1
        if scenario_number >= higher_id:
            higher_id = scenario_number
            selected_scenario = scenario
    return selected_scenario

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

class HumanInterface(object):
    """
    Class to control a vehicle manually for debugging purposes
    """

    def __init__(self):
        self._width = 800
        self._height = 600
        self._surface = None
        pygame.init()
        pygame.font.init()
        self._clock = pygame.time.Clock()
        self._display = pygame.display.set_mode((self._width, self._height), pygame.HWSURFACE | pygame.DOUBLEBUF)
        pygame.display.set_caption('Human Agent')

    def run_interface(self, input_data):
        """
        Run the GUI
        """
        image_center = input_data['Center'][1][:, :, -2::-1]
        self._surface = pygame.surfarray.make_surface(image_center.swapaxes(0, 1))
        if self._surface is not None:
            self._display.blit(self._surface, (0, 0))
        pygame.display.flip()

    def _quit(self):
        pygame.quit()

def __init__(self):
    self._width = 800
    self._height = 600
    self._surface = None
    pygame.init()
    pygame.font.init()
    self._clock = pygame.time.Clock()
    self._display = pygame.display.set_mode((self._width, self._height), pygame.HWSURFACE | pygame.DOUBLEBUF)
    pygame.display.set_caption('Human Agent')

def run_interface(self, input_data):
    """
        Run the GUI
        """
    image_center = input_data['Center'][1][:, :, -2::-1]
    self._surface = pygame.surfarray.make_surface(image_center.swapaxes(0, 1))
    if self._surface is not None:
        self._display.blit(self._surface, (0, 0))
    pygame.display.flip()

def _quit(self):
    pygame.quit()

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
        self.track = Track.SENSORS
        self.agent_engaged = False
        self._hic = HumanInterface()
        self._controller = KeyboardControl(path_to_conf_file)
        self._prev_timestamp = 0

    def sensors(self):
        """
        Define the sensor suite required by the agent

        :return: a list containing the required sensors in the following format:

        [
            {'type': 'sensor.camera.rgb', 'x': 0.7, 'y': -0.4, 'z': 1.60, 'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0,
                      'width': 300, 'height': 200, 'fov': 100, 'id': 'Left'},

            {'type': 'sensor.camera.rgb', 'x': 0.7, 'y': 0.4, 'z': 1.60, 'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0,
                      'width': 300, 'height': 200, 'fov': 100, 'id': 'Right'},

            {'type': 'sensor.lidar.ray_cast', 'x': 0.7, 'y': 0.0, 'z': 1.60, 'yaw': 0.0, 'pitch': 0.0, 'roll': 0.0,
             'id': 'LIDAR'}
        ]
        """
        sensors = [{'type': 'sensor.camera.rgb', 'x': 0.7, 'y': 0.0, 'z': 1.6, 'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0, 'width': 800, 'height': 600, 'fov': 100, 'id': 'Center'}, {'type': 'sensor.speedometer', 'reading_frequency': 20, 'id': 'speed'}]
        return sensors

    def run_step(self, input_data, timestamp):
        """
        Execute one step of navigation.
        """
        self.agent_engaged = True
        self._hic.run_interface(input_data)
        control = self._controller.parse_events(timestamp - self._prev_timestamp)
        self._prev_timestamp = timestamp
        return control

    def destroy(self):
        """
        Cleanup
        """
        self._hic._quit = True

def setup(self, path_to_conf_file):
    """
        Setup the agent parameters
        """
    self.track = Track.SENSORS
    self.agent_engaged = False
    self._hic = HumanInterface()
    self._controller = KeyboardControl(path_to_conf_file)
    self._prev_timestamp = 0

def run_step(self, input_data, timestamp):
    """
        Execute one step of navigation.
        """
    self.agent_engaged = True
    self._hic.run_interface(input_data)
    control = self._controller.parse_events(timestamp - self._prev_timestamp)
    self._prev_timestamp = timestamp
    return control

class KeyboardControl(object):
    """
    Keyboard control for the human agent
    """

    def __init__(self, path_to_conf_file):
        """
        Init
        """
        self._control = carla.VehicleControl()
        self._steer_cache = 0.0
        self._clock = pygame.time.Clock()
        if path_to_conf_file:
            with open(path_to_conf_file, 'r') as f:
                lines = f.read().split('\n')
                self._mode = lines[0].split(' ')[1]
                self._endpoint = lines[1].split(' ')[1]
            if self._mode == 'log':
                self._log_data = {'records': []}
            elif self._mode == 'playback':
                self._index = 0
                self._control_list = []
                with open(self._endpoint) as fd:
                    try:
                        self._records = json.load(fd)
                        self._json_to_control()
                    except json.JSONDecodeError:
                        pass
        else:
            self._mode = 'normal'
            self._endpoint = None

    def _json_to_control(self):
        for entry in self._records['records']:
            control = carla.VehicleControl(throttle=entry['control']['throttle'], steer=entry['control']['steer'], brake=entry['control']['brake'], hand_brake=entry['control']['hand_brake'], reverse=entry['control']['reverse'], manual_gear_shift=entry['control']['manual_gear_shift'], gear=entry['control']['gear'])
            self._control_list.append(control)

    def parse_events(self, timestamp):
        """
        Parse the keyboard events and set the vehicle controls accordingly
        """
        if self._mode == 'playback':
            self._parse_json_control()
        else:
            self._parse_vehicle_keys(pygame.key.get_pressed(), timestamp * 1000)
        if self._mode == 'log':
            self._record_control()
        return self._control

    def _parse_vehicle_keys(self, keys, milliseconds):
        """
        Calculate new vehicle controls based on input keys
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            elif event.type == pygame.KEYUP:
                if event.key == K_q:
                    self._control.gear = 1 if self._control.reverse else -1
                    self._control.reverse = self._control.gear < 0
        if keys[K_UP] or keys[K_w]:
            self._control.throttle = 0.6
        else:
            self._control.throttle = 0.0
        steer_increment = 0.0003 * milliseconds
        if keys[K_LEFT] or keys[K_a]:
            self._steer_cache -= steer_increment
        elif keys[K_RIGHT] or keys[K_d]:
            self._steer_cache += steer_increment
        else:
            self._steer_cache = 0.0
        steer_cache = min(0.95, max(-0.95, self._steer_cache))
        self._control.steer = round(self._steer_cache, 1)
        self._control.brake = 1.0 if keys[K_DOWN] or keys[K_s] else 0.0
        self._control.hand_brake = keys[K_SPACE]

    def _parse_json_control(self):
        if self._index < len(self._control_list):
            self._control = self._control_list[self._index]
            self._index += 1
        else:
            print('JSON file has no more entries')

    def _record_control(self):
        new_record = {'control': {'throttle': self._control.throttle, 'steer': self._control.steer, 'brake': self._control.brake, 'hand_brake': self._control.hand_brake, 'reverse': self._control.reverse, 'manual_gear_shift': self._control.manual_gear_shift, 'gear': self._control.gear}}
        self._log_data['records'].append(new_record)

    def __del__(self):
        if self._mode == 'log' and self._log_data:
            with open(self._endpoint, 'w') as fd:
                json.dump(self._log_data, fd, indent=4, sort_keys=True)

def _parse_vehicle_keys(self, keys, milliseconds):
    """
        Calculate new vehicle controls based on input keys
        """
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return
        elif event.type == pygame.KEYUP:
            if event.key == K_q:
                self._control.gear = 1 if self._control.reverse else -1
                self._control.reverse = self._control.gear < 0
    if keys[K_UP] or keys[K_w]:
        self._control.throttle = 0.6
    else:
        self._control.throttle = 0.0
    steer_increment = 0.0003 * milliseconds
    if keys[K_LEFT] or keys[K_a]:
        self._steer_cache -= steer_increment
    elif keys[K_RIGHT] or keys[K_d]:
        self._steer_cache += steer_increment
    else:
        self._steer_cache = 0.0
    steer_cache = min(0.95, max(-0.95, self._steer_cache))
    self._control.steer = round(self._steer_cache, 1)
    self._control.brake = 1.0 if keys[K_DOWN] or keys[K_s] else 0.0
    self._control.hand_brake = keys[K_SPACE]

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

class ScenarioRunner(object):
    """
    This is the core scenario runner module. It is responsible for
    running (and repeating) a single scenario or a list of scenarios.

    Usage:
    scenario_runner = ScenarioRunner(args)
    scenario_runner.run()
    del scenario_runner
    """
    ego_vehicles = []
    client_timeout = 10.0
    wait_for_world = 20.0
    frame_rate = 20.0
    world = None
    manager = None
    additional_scenario_module = None
    agent_instance = None
    module_agent = None

    def __init__(self, args):
        """
        Setup CARLA client and world
        Setup ScenarioManager
        """
        self._args = args
        if args.timeout:
            self.client_timeout = float(args.timeout)
        self.client = carla.Client(args.host, int(args.port))
        self.client.set_timeout(self.client_timeout)
        dist = pkg_resources.get_distribution('carla')
        if LooseVersion(dist.version) < LooseVersion('0.9.8'):
            raise ImportError('CARLA version 0.9.8 or newer required. CARLA version found: {}'.format(dist))
        if self._args.agent is not None:
            module_name = os.path.basename(args.agent).split('.')[0]
            sys.path.insert(0, os.path.dirname(args.agent))
            self.module_agent = importlib.import_module(module_name)
        self.manager = ScenarioManager(self._args.debug, self._args.sync, self._args.timeout)
        self._shutdown_requested = False
        if sys.platform != 'win32':
            signal.signal(signal.SIGHUP, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        self._start_wall_time = datetime.now()

    def destroy(self):
        """
        Cleanup and delete actors, ScenarioManager and CARLA world
        """
        self._cleanup()
        if self.manager is not None:
            del self.manager
        if self.world is not None:
            del self.world
        if self.client is not None:
            del self.client

    def _signal_handler(self, signum, frame):
        """
        Terminate scenario ticking when receiving a signal interrupt
        """
        self._shutdown_requested = True
        if self.manager:
            self.manager.stop_scenario()
            self._cleanup()
            if not self.manager.get_running_status():
                raise RuntimeError('Timeout occured during scenario execution')

    def _get_scenario_class_or_fail(self, scenario):
        """
        Get scenario class by scenario name
        If scenario is not supported or not found, exit script
        """
        scenarios_list = glob.glob('{}/srunner/scenarios/*.py'.format(os.getenv('SCENARIO_RUNNER_ROOT', './')))
        scenarios_list.append(self._args.additionalScenario)
        for scenario_file in scenarios_list:
            module_name = os.path.basename(scenario_file).split('.')[0]
            sys.path.insert(0, os.path.dirname(scenario_file))
            scenario_module = importlib.import_module(module_name)
            for member in inspect.getmembers(scenario_module, inspect.isclass):
                if scenario in member:
                    return member[1]
            sys.path.pop(0)
        print("Scenario '{}' not supported ... Exiting".format(scenario))
        sys.exit(-1)

    def _cleanup(self):
        """
        Remove and destroy all actors
        """
        if self.manager is not None and self.manager.get_running_status() and (self.world is not None) and self._args.sync:
            settings = self.world.get_settings()
            settings.synchronous_mode = False
            settings.fixed_delta_seconds = None
            self.world.apply_settings(settings)
        self.manager.cleanup()
        CarlaDataProvider.cleanup()
        for i, _ in enumerate(self.ego_vehicles):
            if self.ego_vehicles[i]:
                if not self._args.waitForEgo:
                    print('Destroying ego vehicle {}'.format(self.ego_vehicles[i].id))
                    self.ego_vehicles[i].destroy()
                self.ego_vehicles[i] = None
        self.ego_vehicles = []
        if self.agent_instance:
            self.agent_instance.destroy()
            self.agent_instance = None

    def _prepare_ego_vehicles(self, ego_vehicles):
        """
        Spawn or update the ego vehicles
        """
        if not self._args.waitForEgo:
            for vehicle in ego_vehicles:
                self.ego_vehicles.append(CarlaDataProvider.request_new_actor(vehicle.model, vehicle.transform, vehicle.rolename, color=vehicle.color, actor_category=vehicle.category))
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
                CarlaDataProvider.register_actor(self.ego_vehicles[i])
        if CarlaDataProvider.is_sync_mode():
            self.world.tick()
        else:
            self.world.wait_for_tick()

    def _analyze_scenario(self, config):
        """
        Provide feedback about success/failure of a scenario
        """
        current_time = str(datetime.now().strftime('%Y-%m-%d-%H-%M-%S'))
        junit_filename = None
        config_name = config.name
        if self._args.outputDir != '':
            config_name = os.path.join(self._args.outputDir, config_name)
        if self._args.junit:
            junit_filename = config_name + current_time + '.xml'
        filename = None
        if self._args.file:
            filename = config_name + current_time + '.txt'
        if not self.manager.analyze_scenario(self._args.output, filename, junit_filename):
            print('All scenario tests were passed successfully!')
        else:
            print('Not all scenario tests were successful')
            if not (self._args.output or filename or junit_filename):
                print('Please run with --output for further information')

    def _record_criteria(self, criteria, name):
        """
        Filter the JSON serializable attributes of the criterias and
        dumps them into a file. This will be used by the metrics manager,
        in case the user wants specific information about the criterias.
        """
        file_name = name[:-4] + '.json'
        with open('temp.json', 'w') as fp:
            criteria_dict = {}
            for criterion in criteria:
                criterion_dict = criterion.__dict__
                criteria_dict[criterion.name] = {}
                for key in criterion_dict:
                    if key != 'name':
                        try:
                            key_dict = {key: criterion_dict[key]}
                            json.dump(key_dict, fp, sort_keys=False, indent=4)
                            criteria_dict[criterion.name].update(key_dict)
                        except TypeError:
                            pass
        os.remove('temp.json')
        with open(file_name, 'w') as fp:
            json.dump(criteria_dict, fp, sort_keys=False, indent=4)

    def _load_and_wait_for_world(self, town, ego_vehicles=None):
        """
        Load a new CARLA world and provide data to CarlaDataProvider
        """
        if self._args.reloadWorld:
            self.world = self.client.load_world(town)
        else:
            ego_vehicle_found = False
            if self._args.waitForEgo:
                while not ego_vehicle_found and (not self._shutdown_requested):
                    vehicles = self.client.get_world().get_actors().filter('vehicle.*')
                    for ego_vehicle in ego_vehicles:
                        ego_vehicle_found = False
                        for vehicle in vehicles:
                            if vehicle.attributes['role_name'] == ego_vehicle.rolename:
                                ego_vehicle_found = True
                                break
                        if not ego_vehicle_found:
                            print('Not all ego vehicles ready. Waiting ... ')
                            time.sleep(1)
                            break
        self.world = self.client.get_world()
        if self._args.sync:
            settings = self.world.get_settings()
            settings.synchronous_mode = True
            settings.fixed_delta_seconds = 1.0 / self.frame_rate
            self.world.apply_settings(settings)
        CarlaDataProvider.set_client(self.client)
        CarlaDataProvider.set_world(self.world)
        CarlaDataProvider.set_traffic_manager_port(int(self._args.trafficManagerPort))
        if CarlaDataProvider.is_sync_mode():
            self.world.tick()
        else:
            self.world.wait_for_tick()
        if CarlaDataProvider.get_map().name != town and CarlaDataProvider.get_map().name != 'OpenDriveMap':
            print('The CARLA server uses the wrong map: {}'.format(CarlaDataProvider.get_map().name))
            print('This scenario requires to use map: {}'.format(town))
            return False
        return True

    def _load_and_run_scenario(self, config):
        """
        Load and run the scenario given by config
        """
        result = False
        if not self._load_and_wait_for_world(config.town, config.ego_vehicles):
            self._cleanup()
            return False
        if self._args.agent:
            agent_class_name = self.module_agent.__name__.title().replace('_', '')
            try:
                self.agent_instance = getattr(self.module_agent, agent_class_name)(self._args.agentConfig)
                config.agent = self.agent_instance
            except Exception as e:
                traceback.print_exc()
                print('Could not setup required agent due to {}'.format(e))
                self._cleanup()
                return False
        print('Preparing scenario: ' + config.name)
        try:
            self._prepare_ego_vehicles(config.ego_vehicles)
            if self._args.openscenario:
                scenario = OpenScenario(world=self.world, ego_vehicles=self.ego_vehicles, config=config, config_file=self._args.openscenario, timeout=100000)
            elif self._args.route:
                scenario = RouteScenario(world=self.world, config=config, debug_mode=self._args.debug)
            else:
                scenario_class = self._get_scenario_class_or_fail(config.type)
                scenario = scenario_class(self.world, self.ego_vehicles, config, self._args.randomize, self._args.debug)
        except Exception as exception:
            print('The scenario cannot be loaded')
            traceback.print_exc()
            print(exception)
            self._cleanup()
            return False
        try:
            if self._args.record:
                recorder_name = '{}/{}/{}.log'.format(os.getenv('SCENARIO_RUNNER_ROOT', './'), self._args.record, config.name)
                self.client.start_recorder(recorder_name, True)
            self.manager.load_scenario(scenario, self.agent_instance)
            self.manager.run_scenario()
            self._analyze_scenario(config)
            scenario.remove_all_actors()
            if self._args.record:
                self.client.stop_recorder()
                self._record_criteria(self.manager.scenario.get_criteria(), recorder_name)
            result = True
        except Exception as e:
            traceback.print_exc()
            print(e)
            result = False
        self._cleanup()
        return result

    def _run_scenarios(self):
        """
        Run conventional scenarios (e.g. implemented using the Python API of ScenarioRunner)
        """
        result = False
        scenario_configurations = ScenarioConfigurationParser.parse_scenario_configuration(self._args.scenario, self._args.configFile)
        if not scenario_configurations:
            print('Configuration for scenario {} cannot be found!'.format(self._args.scenario))
            return result
        for config in scenario_configurations:
            for _ in range(self._args.repetitions):
                result = self._load_and_run_scenario(config)
            self._cleanup()
        return result

    def _run_route(self):
        """
        Run the route scenario
        """
        result = False
        if self._args.route:
            routes = self._args.route[0]
            scenario_file = self._args.route[1]
            single_route = None
            if len(self._args.route) > 2:
                single_route = self._args.route[2]
        route_configurations = RouteParser.parse_routes_file(routes, scenario_file, single_route)
        for config in route_configurations:
            for _ in range(self._args.repetitions):
                result = self._load_and_run_scenario(config)
                self._cleanup()
        return result

    def _run_openscenario(self):
        """
        Run a scenario based on OpenSCENARIO
        """
        if not os.path.isfile(self._args.openscenario):
            print('File does not exist')
            self._cleanup()
            return False
        config = OpenScenarioConfiguration(self._args.openscenario, self.client)
        result = self._load_and_run_scenario(config)
        self._cleanup()
        return result

    def run(self):
        """
        Run all scenarios according to provided commandline args
        """
        result = True
        if self._args.openscenario:
            result = self._run_openscenario()
        elif self._args.route:
            result = self._run_route()
        else:
            result = self._run_scenarios()
        print('No more scenarios .... Exiting')
        return result

def __init__(self, args):
    """
        Setup CARLA client and world
        Setup ScenarioManager
        """
    self._args = args
    if args.timeout:
        self.client_timeout = float(args.timeout)
    self.client = carla.Client(args.host, int(args.port))
    self.client.set_timeout(self.client_timeout)
    dist = pkg_resources.get_distribution('carla')
    if LooseVersion(dist.version) < LooseVersion('0.9.8'):
        raise ImportError('CARLA version 0.9.8 or newer required. CARLA version found: {}'.format(dist))
    if self._args.agent is not None:
        module_name = os.path.basename(args.agent).split('.')[0]
        sys.path.insert(0, os.path.dirname(args.agent))
        self.module_agent = importlib.import_module(module_name)
    self.manager = ScenarioManager(self._args.debug, self._args.sync, self._args.timeout)
    self._shutdown_requested = False
    if sys.platform != 'win32':
        signal.signal(signal.SIGHUP, self._signal_handler)
    signal.signal(signal.SIGINT, self._signal_handler)
    signal.signal(signal.SIGTERM, self._signal_handler)
    self._start_wall_time = datetime.now()

def _get_scenario_class_or_fail(self, scenario):
    """
        Get scenario class by scenario name
        If scenario is not supported or not found, exit script
        """
    scenarios_list = glob.glob('{}/srunner/scenarios/*.py'.format(os.getenv('SCENARIO_RUNNER_ROOT', './')))
    scenarios_list.append(self._args.additionalScenario)
    for scenario_file in scenarios_list:
        module_name = os.path.basename(scenario_file).split('.')[0]
        sys.path.insert(0, os.path.dirname(scenario_file))
        scenario_module = importlib.import_module(module_name)
        for member in inspect.getmembers(scenario_module, inspect.isclass):
            if scenario in member:
                return member[1]
        sys.path.pop(0)
    print("Scenario '{}' not supported ... Exiting".format(scenario))
    sys.exit(-1)

def game_loop(args):
    pygame.init()
    pygame.font.init()
    world = None
    try:
        client = carla.Client(args.host, args.port)
        client.set_timeout(2.0)
        display = pygame.display.set_mode((args.width, args.height), pygame.HWSURFACE | pygame.DOUBLEBUF)
        hud = HUD(args.width, args.height)
        world = WorldSR(client.get_world(), hud, args)
        controller = KeyboardControl(world, args.autopilot)
        clock = pygame.time.Clock()
        while True:
            clock.tick_busy_loop(60)
            if controller.parse_events(client, world, clock):
                return
            if not world.tick(clock):
                return
            world.render(display)
            pygame.display.flip()
    finally:
        if world and world.recording_enabled:
            client.stop_recorder()
        if world is not None:
            world.destroy()
        pygame.quit()

class MetricsManager(object):
    """
    Main class of the metrics module. Handles the parsing and execution of
    the metrics.
    """

    def __init__(self, args):
        """
        Initialization of the metrics manager. This creates the client, needed to parse
        the information from the recorder, extract the metrics class, and runs it
        """
        self._args = args
        recorder_str = self._get_recorder(self._args.log)
        criteria_dict = self._get_criteria(self._args.criteria)
        map_name = self._get_recorder_map(recorder_str)
        world = self._client.load_world(map_name)
        town_map = world.get_map()
        log = MetricsLog(recorder_str)
        metric_class = self._get_metric_class(self._args.metric)
        metric_class(town_map, log, criteria_dict)

    def _get_recorder(self, log):
        """
        Parses the log argument into readable information
        """
        self._client = carla.Client(self._args.host, self._args.port)
        recorder_file = '{}/{}'.format(os.getenv('SCENARIO_RUNNER_ROOT', './'), log)
        if recorder_file[-4:] != '.log':
            print('ERROR: The log argument has to point to a .log file')
            sys.exit(-1)
        if not os.path.exists(recorder_file):
            print('ERROR: The specified log file does not exist')
            sys.exit(-1)
        recorder_str = self._client.show_recorder_file_info(recorder_file, True)
        return recorder_str

    def _get_criteria(self, criteria_file):
        """
        Parses the criteria argument into a dictionary
        """
        if criteria_file:
            with open(criteria_file) as fd:
                criteria_dict = json.load(fd)
        else:
            criteria_dict = None
        return criteria_dict

    def _get_metric_class(self, metric_file):
        """
        Function to extract the metrics class from the path given by the metrics
        argument. Returns the first class found that is a child of BasicMetric

        Args:
            metric_file (str): path to the metric's file.
        """
        module_name = os.path.basename(metric_file).split('.')[0]
        sys.path.insert(0, os.path.dirname(metric_file))
        metric_module = importlib.import_module(module_name)
        for member in inspect.getmembers(metric_module, inspect.isclass):
            member_parent = member[1].__bases__[0]
            if 'BasicMetric' in str(member_parent):
                return member[1]
        print('No child class of BasicMetric was found ... Exiting')
        sys.exit(-1)

    def _get_recorder_map(self, recorder_str):
        """
        Returns the name of the map the simulation took place in
        """
        header = recorder_str.split('\n')
        sim_map = header[1][5:]
        return sim_map

def _get_metric_class(self, metric_file):
    """
        Function to extract the metrics class from the path given by the metrics
        argument. Returns the first class found that is a child of BasicMetric

        Args:
            metric_file (str): path to the metric's file.
        """
    module_name = os.path.basename(metric_file).split('.')[0]
    sys.path.insert(0, os.path.dirname(metric_file))
    metric_module = importlib.import_module(module_name)
    for member in inspect.getmembers(metric_module, inspect.isclass):
        member_parent = member[1].__bases__[0]
        if 'BasicMetric' in str(member_parent):
            return member[1]
    print('No child class of BasicMetric was found ... Exiting')
    sys.exit(-1)

def _get_recorder_map(self, recorder_str):
    """
        Returns the name of the map the simulation took place in
        """
    header = recorder_str.split('\n')
    sim_map = header[1][5:]
    return sim_map

class Util(object):

    @staticmethod
    def blits(destination_surface, source_surfaces, rect=None, blend_mode=0):
        for surface in source_surfaces:
            destination_surface.blit(surface[0], surface[1], rect, blend_mode)

    @staticmethod
    def length(v):
        return math.sqrt(v.x ** 2 + v.y ** 2 + v.z ** 2)

    @staticmethod
    def get_bounding_box(actor):
        bb = actor.trigger_volume.extent
        corners = [carla.Location(x=-bb.x, y=-bb.y), carla.Location(x=bb.x, y=-bb.y), carla.Location(x=bb.x, y=bb.y), carla.Location(x=-bb.x, y=bb.y), carla.Location(x=-bb.x, y=-bb.y)]
        corners = [x + actor.trigger_volume.location for x in corners]
        t = actor.get_transform()
        t.transform(corners)
        return corners

@staticmethod
def blits(destination_surface, source_surfaces, rect=None, blend_mode=0):
    for surface in source_surfaces:
        destination_surface.blit(surface[0], surface[1], rect, blend_mode)

class ModuleManager(object):

    def __init__(self):
        self.modules = []

    def register_module(self, module):
        self.modules.append(module)

    def clear_modules(self):
        del self.modules[:]

    def tick(self, clock):
        for module in self.modules:
            module.tick(clock)

    def render(self, display):
        display.fill(COLOR_ALUMINIUM_4)
        for module in self.modules:
            module.render(display)

    def get_module(self, name):
        for module in self.modules:
            if module.name == name:
                return module

    def start_modules(self):
        for module in self.modules:
            module.start()

def render(self, display):
    display.fill(COLOR_ALUMINIUM_4)
    for module in self.modules:
        module.render(display)

class FadingText(object):

    def __init__(self, font, dim, pos):
        self.font = font
        self.dim = dim
        self.pos = pos
        self.seconds_left = 0
        self.surface = pygame.Surface(self.dim)

    def set_text(self, text, color=COLOR_WHITE, seconds=2.0):
        text_texture = self.font.render(text, True, color)
        self.surface = pygame.Surface(self.dim)
        self.seconds_left = seconds
        self.surface.fill(COLOR_BLACK)
        self.surface.blit(text_texture, (10, 11))

    def tick(self, clock):
        delta_seconds = 0.001 * clock.get_time()
        self.seconds_left = max(0.0, self.seconds_left - delta_seconds)
        self.surface.set_alpha(500.0 * self.seconds_left)

    def render(self, display):
        display.blit(self.surface, self.pos)

def __init__(self, font, dim, pos):
    self.font = font
    self.dim = dim
    self.pos = pos
    self.seconds_left = 0
    self.surface = pygame.Surface(self.dim)

def set_text(self, text, color=COLOR_WHITE, seconds=2.0):
    text_texture = self.font.render(text, True, color)
    self.surface = pygame.Surface(self.dim)
    self.seconds_left = seconds
    self.surface.fill(COLOR_BLACK)
    self.surface.blit(text_texture, (10, 11))

def tick(self, clock):
    delta_seconds = 0.001 * clock.get_time()
    self.seconds_left = max(0.0, self.seconds_left - delta_seconds)
    self.surface.set_alpha(500.0 * self.seconds_left)

def render(self, display):
    display.blit(self.surface, self.pos)

class HelpText(object):

    def __init__(self, font, width, height):
        lines = __doc__.split('\n')
        self.font = font
        self.dim = (680, len(lines) * 22 + 12)
        self.pos = (0.5 * width - 0.5 * self.dim[0], 0.5 * height - 0.5 * self.dim[1])
        self.seconds_left = 0
        self.surface = pygame.Surface(self.dim)
        self.surface.fill(COLOR_BLACK)
        for n, line in enumerate(lines):
            text_texture = self.font.render(line, True, COLOR_WHITE)
            self.surface.blit(text_texture, (22, n * 22))
            self._render = False
        self.surface.set_alpha(220)

    def toggle(self):
        self._render = not self._render

    def render(self, display):
        if self._render:
            display.blit(self.surface, self.pos)

def __init__(self, font, width, height):
    lines = __doc__.split('\n')
    self.font = font
    self.dim = (680, len(lines) * 22 + 12)
    self.pos = (0.5 * width - 0.5 * self.dim[0], 0.5 * height - 0.5 * self.dim[1])
    self.seconds_left = 0
    self.surface = pygame.Surface(self.dim)
    self.surface.fill(COLOR_BLACK)
    for n, line in enumerate(lines):
        text_texture = self.font.render(line, True, COLOR_WHITE)
        self.surface.blit(text_texture, (22, n * 22))
        self._render = False
    self.surface.set_alpha(220)

def render(self, display):
    if self._render:
        display.blit(self.surface, self.pos)

class ModuleHUD(object):

    def __init__(self, name, width, height):
        self.name = name
        self.dim = (width, height)
        self._init_hud_params()
        self._init_data_params()

    def start(self):
        pass

    def _init_hud_params(self):
        fonts = [x for x in pygame.font.get_fonts() if 'mono' in x]
        default_font = 'ubuntumono'
        mono = default_font if default_font in fonts else fonts[0]
        mono = pygame.font.match_font(mono)
        self._font_mono = pygame.font.Font(mono, 14)
        self._header_font = pygame.font.SysFont('Arial', 14, True)
        self.help = HelpText(pygame.font.Font(mono, 24), *self.dim)
        self._notifications = FadingText(pygame.font.Font(pygame.font.get_default_font(), 20), (self.dim[0], 40), (0, self.dim[1] - 40))

    def _init_data_params(self):
        self.show_info = True
        self.show_actor_ids = False
        self._info_text = {}

    def notification(self, text, seconds=2.0):
        self._notifications.set_text(text, seconds=seconds)

    def tick(self, clock):
        self._notifications.tick(clock)

    def add_info(self, module_name, info):
        self._info_text[module_name] = info

    def render_vehicles_ids(self, vehicle_id_surface, list_actors, world_to_pixel, hero_actor, hero_transform):
        vehicle_id_surface.fill(COLOR_BLACK)
        if self.show_actor_ids:
            vehicle_id_surface.set_alpha(150)
            for actor in list_actors:
                x, y = world_to_pixel(actor[1].location)
                angle = 0
                if hero_actor is not None:
                    angle = -hero_transform.rotation.yaw - 90
                color = COLOR_SKY_BLUE_0
                if int(actor[0].attributes['number_of_wheels']) == 2:
                    color = COLOR_CHOCOLATE_0
                if actor[0].attributes['role_name'] == 'hero':
                    color = COLOR_CHAMELEON_0
                font_surface = self._header_font.render(str(actor[0].id), True, color)
                rotated_font_surface = pygame.transform.rotate(font_surface, angle)
                rect = rotated_font_surface.get_rect(center=(x, y))
                vehicle_id_surface.blit(rotated_font_surface, rect)
        return vehicle_id_surface

    def render(self, display):
        if self.show_info:
            info_surface = pygame.Surface((240, self.dim[1]))
            info_surface.set_alpha(100)
            display.blit(info_surface, (0, 0))
            v_offset = 4
            bar_h_offset = 100
            bar_width = 106
            i = 0
            for module_name, module_info in self._info_text.items():
                if not module_info:
                    continue
                surface = self._header_font.render(module_name, True, COLOR_ALUMINIUM_0).convert_alpha()
                display.blit(surface, (8 + bar_width / 2, 18 * i + v_offset))
                v_offset += 12
                i += 1
                for item in module_info:
                    if v_offset + 18 > self.dim[1]:
                        break
                    if isinstance(item, list):
                        if len(item) > 1:
                            points = [(x + 8, v_offset + 8 + (1.0 - y) * 30) for x, y in enumerate(item)]
                            pygame.draw.lines(display, (255, 136, 0), False, points, 2)
                        item = None
                    elif isinstance(item, tuple):
                        if isinstance(item[1], bool):
                            rect = pygame.Rect((bar_h_offset, v_offset + 8), (6, 6))
                            pygame.draw.rect(display, COLOR_ALUMINIUM_0, rect, 0 if item[1] else 1)
                        else:
                            rect_border = pygame.Rect((bar_h_offset, v_offset + 8), (bar_width, 6))
                            pygame.draw.rect(display, COLOR_ALUMINIUM_0, rect_border, 1)
                            f = (item[1] - item[2]) / (item[3] - item[2])
                            if item[2] < 0.0:
                                rect = pygame.Rect((bar_h_offset + f * (bar_width - 6), v_offset + 8), (6, 6))
                            else:
                                rect = pygame.Rect((bar_h_offset, v_offset + 8), (f * bar_width, 6))
                            pygame.draw.rect(display, COLOR_ALUMINIUM_0, rect)
                        item = item[0]
                    if item:
                        surface = self._font_mono.render(item, True, COLOR_ALUMINIUM_0).convert_alpha()
                        display.blit(surface, (8, 18 * i + v_offset))
                    v_offset += 18
                v_offset += 24
        self._notifications.render(display)
        self.help.render(display)

def _init_hud_params(self):
    fonts = [x for x in pygame.font.get_fonts() if 'mono' in x]
    default_font = 'ubuntumono'
    mono = default_font if default_font in fonts else fonts[0]
    mono = pygame.font.match_font(mono)
    self._font_mono = pygame.font.Font(mono, 14)
    self._header_font = pygame.font.SysFont('Arial', 14, True)
    self.help = HelpText(pygame.font.Font(mono, 24), *self.dim)
    self._notifications = FadingText(pygame.font.Font(pygame.font.get_default_font(), 20), (self.dim[0], 40), (0, self.dim[1] - 40))

def render_vehicles_ids(self, vehicle_id_surface, list_actors, world_to_pixel, hero_actor, hero_transform):
    vehicle_id_surface.fill(COLOR_BLACK)
    if self.show_actor_ids:
        vehicle_id_surface.set_alpha(150)
        for actor in list_actors:
            x, y = world_to_pixel(actor[1].location)
            angle = 0
            if hero_actor is not None:
                angle = -hero_transform.rotation.yaw - 90
            color = COLOR_SKY_BLUE_0
            if int(actor[0].attributes['number_of_wheels']) == 2:
                color = COLOR_CHOCOLATE_0
            if actor[0].attributes['role_name'] == 'hero':
                color = COLOR_CHAMELEON_0
            font_surface = self._header_font.render(str(actor[0].id), True, color)
            rotated_font_surface = pygame.transform.rotate(font_surface, angle)
            rect = rotated_font_surface.get_rect(center=(x, y))
            vehicle_id_surface.blit(rotated_font_surface, rect)
    return vehicle_id_surface

def render(self, display):
    if self.show_info:
        info_surface = pygame.Surface((240, self.dim[1]))
        info_surface.set_alpha(100)
        display.blit(info_surface, (0, 0))
        v_offset = 4
        bar_h_offset = 100
        bar_width = 106
        i = 0
        for module_name, module_info in self._info_text.items():
            if not module_info:
                continue
            surface = self._header_font.render(module_name, True, COLOR_ALUMINIUM_0).convert_alpha()
            display.blit(surface, (8 + bar_width / 2, 18 * i + v_offset))
            v_offset += 12
            i += 1
            for item in module_info:
                if v_offset + 18 > self.dim[1]:
                    break
                if isinstance(item, list):
                    if len(item) > 1:
                        points = [(x + 8, v_offset + 8 + (1.0 - y) * 30) for x, y in enumerate(item)]
                        pygame.draw.lines(display, (255, 136, 0), False, points, 2)
                    item = None
                elif isinstance(item, tuple):
                    if isinstance(item[1], bool):
                        rect = pygame.Rect((bar_h_offset, v_offset + 8), (6, 6))
                        pygame.draw.rect(display, COLOR_ALUMINIUM_0, rect, 0 if item[1] else 1)
                    else:
                        rect_border = pygame.Rect((bar_h_offset, v_offset + 8), (bar_width, 6))
                        pygame.draw.rect(display, COLOR_ALUMINIUM_0, rect_border, 1)
                        f = (item[1] - item[2]) / (item[3] - item[2])
                        if item[2] < 0.0:
                            rect = pygame.Rect((bar_h_offset + f * (bar_width - 6), v_offset + 8), (6, 6))
                        else:
                            rect = pygame.Rect((bar_h_offset, v_offset + 8), (f * bar_width, 6))
                        pygame.draw.rect(display, COLOR_ALUMINIUM_0, rect)
                    item = item[0]
                if item:
                    surface = self._font_mono.render(item, True, COLOR_ALUMINIUM_0).convert_alpha()
                    display.blit(surface, (8, 18 * i + v_offset))
                v_offset += 18
            v_offset += 24
    self._notifications.render(display)
    self.help.render(display)

class TrafficLightSurfaces(object):
    """Holds the surfaces (scaled and rotated) for painting traffic lights"""

    def __init__(self):

        def make_surface(tl):
            w = 40
            surface = pygame.Surface((w, 3 * w), pygame.SRCALPHA)
            surface.fill(COLOR_ALUMINIUM_5 if tl != 'h' else COLOR_ORANGE_2)
            if tl != 'h':
                hw = int(w / 2)
                off = COLOR_ALUMINIUM_4
                red = COLOR_SCARLET_RED_0
                yellow = COLOR_BUTTER_0
                green = COLOR_CHAMELEON_0
                pygame.draw.circle(surface, red if tl == tls.Red else off, (hw, hw), int(0.4 * w))
                pygame.draw.circle(surface, yellow if tl == tls.Yellow else off, (hw, w + hw), int(0.4 * w))
                pygame.draw.circle(surface, green if tl == tls.Green else off, (hw, 2 * w + hw), int(0.4 * w))
            return pygame.transform.smoothscale(surface, (15, 45) if tl != 'h' else (19, 49))
        self._original_surfaces = {'h': make_surface('h'), tls.Red: make_surface(tls.Red), tls.Yellow: make_surface(tls.Yellow), tls.Green: make_surface(tls.Green), tls.Off: make_surface(tls.Off), tls.Unknown: make_surface(tls.Unknown)}
        self.surfaces = dict(self._original_surfaces)

    def rotozoom(self, angle, scale):
        for key, surface in self._original_surfaces.items():
            self.surfaces[key] = pygame.transform.rotozoom(surface, angle, scale)

def make_surface(tl):
    w = 40
    surface = pygame.Surface((w, 3 * w), pygame.SRCALPHA)
    surface.fill(COLOR_ALUMINIUM_5 if tl != 'h' else COLOR_ORANGE_2)
    if tl != 'h':
        hw = int(w / 2)
        off = COLOR_ALUMINIUM_4
        red = COLOR_SCARLET_RED_0
        yellow = COLOR_BUTTER_0
        green = COLOR_CHAMELEON_0
        pygame.draw.circle(surface, red if tl == tls.Red else off, (hw, hw), int(0.4 * w))
        pygame.draw.circle(surface, yellow if tl == tls.Yellow else off, (hw, w + hw), int(0.4 * w))
        pygame.draw.circle(surface, green if tl == tls.Green else off, (hw, 2 * w + hw), int(0.4 * w))
    return pygame.transform.smoothscale(surface, (15, 45) if tl != 'h' else (19, 49))

def __init__(self):

    def make_surface(tl):
        w = 40
        surface = pygame.Surface((w, 3 * w), pygame.SRCALPHA)
        surface.fill(COLOR_ALUMINIUM_5 if tl != 'h' else COLOR_ORANGE_2)
        if tl != 'h':
            hw = int(w / 2)
            off = COLOR_ALUMINIUM_4
            red = COLOR_SCARLET_RED_0
            yellow = COLOR_BUTTER_0
            green = COLOR_CHAMELEON_0
            pygame.draw.circle(surface, red if tl == tls.Red else off, (hw, hw), int(0.4 * w))
            pygame.draw.circle(surface, yellow if tl == tls.Yellow else off, (hw, w + hw), int(0.4 * w))
            pygame.draw.circle(surface, green if tl == tls.Green else off, (hw, 2 * w + hw), int(0.4 * w))
        return pygame.transform.smoothscale(surface, (15, 45) if tl != 'h' else (19, 49))
    self._original_surfaces = {'h': make_surface('h'), tls.Red: make_surface(tls.Red), tls.Yellow: make_surface(tls.Yellow), tls.Green: make_surface(tls.Green), tls.Off: make_surface(tls.Off), tls.Unknown: make_surface(tls.Unknown)}
    self.surfaces = dict(self._original_surfaces)

def rotozoom(self, angle, scale):
    for key, surface in self._original_surfaces.items():
        self.surfaces[key] = pygame.transform.rotozoom(surface, angle, scale)

class MapImage(object):

    def __init__(self, carla_world, carla_map, pixels_per_meter, show_triggers, show_connections, show_spawn_points):
        self._pixels_per_meter = pixels_per_meter
        self.scale = 1.0
        self.show_triggers = show_triggers
        self.show_connections = show_connections
        self.show_spawn_points = show_spawn_points
        waypoints = carla_map.generate_waypoints(2)
        margin = 50
        max_x = max(waypoints, key=lambda x: x.transform.location.x).transform.location.x + margin
        max_y = max(waypoints, key=lambda x: x.transform.location.y).transform.location.y + margin
        min_x = min(waypoints, key=lambda x: x.transform.location.x).transform.location.x - margin
        min_y = min(waypoints, key=lambda x: x.transform.location.y).transform.location.y - margin
        self.width = max(max_x - min_x, max_y - min_y)
        self._world_offset = (min_x, min_y)
        width_in_pixels = int(self._pixels_per_meter * self.width)
        self.big_map_surface = pygame.Surface((width_in_pixels, width_in_pixels)).convert()
        self.draw_road_map(self.big_map_surface, carla_world, carla_map, self.world_to_pixel, self.world_to_pixel_width)
        self.surface = self.big_map_surface

    def draw_road_map(self, map_surface, carla_world, carla_map, world_to_pixel, world_to_pixel_width):
        map_surface.fill(COLOR_ALUMINIUM_4)
        precision = 0.05

        def lane_marking_color_to_tango(lane_marking_color):
            tango_color = COLOR_BLACK
            if lane_marking_color == carla.LaneMarkingColor.White:
                tango_color = COLOR_ALUMINIUM_2
            elif lane_marking_color == carla.LaneMarkingColor.Blue:
                tango_color = COLOR_SKY_BLUE_0
            elif lane_marking_color == carla.LaneMarkingColor.Green:
                tango_color = COLOR_CHAMELEON_0
            elif lane_marking_color == carla.LaneMarkingColor.Red:
                tango_color = COLOR_SCARLET_RED_0
            elif lane_marking_color == carla.LaneMarkingColor.Yellow:
                tango_color = COLOR_ORANGE_0
            return tango_color

        def draw_solid_line(surface, color, closed, points, width):
            if len(points) >= 2:
                pygame.draw.lines(surface, color, closed, points, width)

        def draw_broken_line(surface, color, closed, points, width):
            broken_lines = [x for n, x in enumerate(zip(*(iter(points),) * 20)) if n % 3 == 0]
            for line in broken_lines:
                pygame.draw.lines(surface, color, closed, line, width)

        def get_lane_markings(lane_marking_type, lane_marking_color, waypoints, sign):
            margin = 0.2
            if lane_marking_type == carla.LaneMarkingType.Broken or lane_marking_type == carla.LaneMarkingType.Solid:
                marking_1 = [world_to_pixel(lateral_shift(w.transform, sign * w.lane_width * 0.5)) for w in waypoints]
                return [(lane_marking_type, lane_marking_color, marking_1)]
            elif lane_marking_type == carla.LaneMarkingType.SolidBroken or lane_marking_type == carla.LaneMarkingType.BrokenSolid:
                marking_1 = [world_to_pixel(lateral_shift(w.transform, sign * w.lane_width * 0.5)) for w in waypoints]
                marking_2 = [world_to_pixel(lateral_shift(w.transform, sign * (w.lane_width * 0.5 + margin * 2))) for w in waypoints]
                return [(carla.LaneMarkingType.Solid, lane_marking_color, marking_1), (carla.LaneMarkingType.Broken, lane_marking_color, marking_2)]
            elif lane_marking_type == carla.LaneMarkingType.BrokenBroken:
                marking = [world_to_pixel(lateral_shift(w.transform, sign * (w.lane_width * 0.5 - margin))) for w in waypoints]
                return [(carla.LaneMarkingType.Broken, lane_marking_color, marking)]
            elif lane_marking_type == carla.LaneMarkingType.SolidSolid:
                marking = [world_to_pixel(lateral_shift(w.transform, sign * (w.lane_width * 0.5 - margin))) for w in waypoints]
                return [(carla.LaneMarkingType.Solid, lane_marking_color, marking)]
            return [(carla.LaneMarkingType.NONE, carla.LaneMarkingColor.Other, [])]

        def draw_lane_marking(surface, waypoints, is_left):
            sign = -1 if is_left else 1
            lane_marking = None
            marking_type = carla.LaneMarkingType.NONE
            previous_marking_type = carla.LaneMarkingType.NONE
            marking_color = carla.LaneMarkingColor.Other
            previous_marking_color = carla.LaneMarkingColor.Other
            waypoints_list = []
            temp_waypoints = []
            current_lane_marking = carla.LaneMarkingType.NONE
            for sample in waypoints:
                lane_marking = sample.left_lane_marking if sign < 0 else sample.right_lane_marking
                if lane_marking is None:
                    continue
                marking_type = lane_marking.type
                marking_color = lane_marking.color
                if current_lane_marking != marking_type:
                    markings = get_lane_markings(previous_marking_type, lane_marking_color_to_tango(previous_marking_color), temp_waypoints, sign)
                    current_lane_marking = marking_type
                    for marking in markings:
                        waypoints_list.append(marking)
                    temp_waypoints = temp_waypoints[-1:]
                else:
                    temp_waypoints.append(sample)
                    previous_marking_type = marking_type
                    previous_marking_color = marking_color
            last_markings = get_lane_markings(previous_marking_type, lane_marking_color_to_tango(previous_marking_color), temp_waypoints, sign)
            for marking in last_markings:
                waypoints_list.append(marking)
            for markings in waypoints_list:
                if markings[0] == carla.LaneMarkingType.Solid:
                    draw_solid_line(surface, markings[1], False, markings[2], 2)
                elif markings[0] == carla.LaneMarkingType.Broken:
                    draw_broken_line(surface, markings[1], False, markings[2], 2)

        def draw_arrow(surface, transform, color=COLOR_ALUMINIUM_2):
            transform.rotation.yaw += 180
            forward = transform.get_forward_vector()
            transform.rotation.yaw += 90
            right_dir = transform.get_forward_vector()
            end = transform.location
            start = end - 2.0 * forward
            right = start + 0.8 * forward + 0.4 * right_dir
            left = start + 0.8 * forward - 0.4 * right_dir
            pygame.draw.lines(surface, color, False, [world_to_pixel(x) for x in [start, end]], 4)
            pygame.draw.lines(surface, color, False, [world_to_pixel(x) for x in [left, start, right]], 4)

        def draw_traffic_signs(surface, font_surface, actor, color=COLOR_ALUMINIUM_2, trigger_color=COLOR_PLUM_0):
            transform = actor.get_transform()
            waypoint = carla_map.get_waypoint(transform.location)
            angle = -waypoint.transform.rotation.yaw - 90.0
            font_surface = pygame.transform.rotate(font_surface, angle)
            pixel_pos = world_to_pixel(waypoint.transform.location)
            offset = font_surface.get_rect(center=(pixel_pos[0], pixel_pos[1]))
            surface.blit(font_surface, offset)
            forward_vector = carla.Location(waypoint.transform.get_forward_vector())
            left_vector = carla.Location(-forward_vector.y, forward_vector.x, forward_vector.z) * waypoint.lane_width / 2 * 0.7
            line = [waypoint.transform.location + forward_vector * 1.5 + left_vector, waypoint.transform.location + forward_vector * 1.5 - left_vector]
            line_pixel = [world_to_pixel(p) for p in line]
            pygame.draw.lines(surface, color, True, line_pixel, 2)
            if self.show_triggers:
                corners = Util.get_bounding_box(actor)
                corners = [world_to_pixel(p) for p in corners]
                pygame.draw.lines(surface, trigger_color, True, corners, 2)

        def lateral_shift(transform, shift):
            transform.rotation.yaw += 90
            return transform.location + shift * transform.get_forward_vector()

        def draw_topology(carla_topology, index):
            topology = [x[index] for x in carla_topology]
            topology = sorted(topology, key=lambda w: w.transform.location.z)
            for waypoint in topology:
                waypoints = [waypoint]
                nxt = waypoint.next(precision)
                if len(nxt) > 0:
                    nxt = nxt[0]
                    while nxt.road_id == waypoint.road_id:
                        waypoints.append(nxt)
                        nxt = nxt.next(precision)
                        if len(nxt) > 0:
                            nxt = nxt[0]
                        else:
                            break
                road_left_side = [lateral_shift(w.transform, -w.lane_width * 0.5) for w in waypoints]
                road_right_side = [lateral_shift(w.transform, w.lane_width * 0.5) for w in waypoints]
                polygon = road_left_side + [x for x in reversed(road_right_side)]
                polygon = [world_to_pixel(x) for x in polygon]
                if len(polygon) > 2:
                    pygame.draw.polygon(map_surface, COLOR_ALUMINIUM_5, polygon, 5)
                    pygame.draw.polygon(map_surface, COLOR_ALUMINIUM_5, polygon)
                PARKING_COLOR = COLOR_ALUMINIUM_4_5
                SHOULDER_COLOR = COLOR_ALUMINIUM_5
                final_color = SHOULDER_COLOR
                shoulder = []
                for w in waypoints:
                    r = w.get_right_lane()
                    if r is not None and (r.lane_type == carla.LaneType.Shoulder or r.lane_type == carla.LaneType.Parking):
                        if r.lane_type == carla.LaneType.Parking:
                            final_color = PARKING_COLOR
                        shoulder.append(r)
                shoulder_left_side = [lateral_shift(w.transform, -w.lane_width * 0.5) for w in shoulder]
                shoulder_right_side = [lateral_shift(w.transform, w.lane_width * 0.5) for w in shoulder]
                polygon = shoulder_left_side + [x for x in reversed(shoulder_right_side)]
                polygon = [world_to_pixel(x) for x in polygon]
                if len(polygon) > 2:
                    pygame.draw.polygon(map_surface, final_color, polygon, 5)
                    pygame.draw.polygon(map_surface, final_color, polygon)
                draw_lane_marking(map_surface, shoulder, False)
                shoulder = []
                for w in waypoints:
                    r = w.get_left_lane()
                    if r is not None and (r.lane_type == carla.LaneType.Shoulder or r.lane_type == carla.LaneType.Parking):
                        if r.lane_type == carla.LaneType.Parking:
                            final_color = PARKING_COLOR
                        shoulder.append(r)
                shoulder_left_side = [lateral_shift(w.transform, -w.lane_width * 0.5) for w in shoulder]
                shoulder_right_side = [lateral_shift(w.transform, w.lane_width * 0.5) for w in shoulder]
                polygon = shoulder_left_side + [x for x in reversed(shoulder_right_side)]
                polygon = [world_to_pixel(x) for x in polygon]
                if len(polygon) > 2:
                    pygame.draw.polygon(map_surface, final_color, polygon, 5)
                    pygame.draw.polygon(map_surface, final_color, polygon)
                draw_lane_marking(map_surface, shoulder, True)
                if not waypoint.is_intersection:
                    draw_lane_marking(map_surface, waypoints, True)
                    draw_lane_marking(map_surface, waypoints, False)
                    for n, wp in enumerate(waypoints):
                        if (n + 1) % 400 == 0:
                            draw_arrow(map_surface, wp.transform)
        topology = carla_map.get_topology()
        draw_topology(topology, 0)
        draw_topology(topology, 1)
        if self.show_spawn_points:
            for sp in carla_map.get_spawn_points():
                draw_arrow(map_surface, sp, color=COLOR_CHOCOLATE_0)
        if self.show_connections:
            dist = 1.5
            to_pixel = lambda wp: world_to_pixel(wp.transform.location)
            for wp in carla_map.generate_waypoints(dist):
                col = (0, 255, 255) if wp.is_intersection else (0, 255, 0)
                for nxt in wp.next(dist):
                    pygame.draw.line(map_surface, col, to_pixel(wp), to_pixel(nxt), 2)
                if wp.lane_change & carla.LaneChange.Right:
                    r = wp.get_right_lane()
                    if r and r.lane_type == carla.LaneType.Driving:
                        pygame.draw.line(map_surface, col, to_pixel(wp), to_pixel(r), 2)
                if wp.lane_change & carla.LaneChange.Left:
                    l = wp.get_left_lane()
                    if l and l.lane_type == carla.LaneType.Driving:
                        pygame.draw.line(map_surface, col, to_pixel(wp), to_pixel(l), 2)
        actors = carla_world.get_actors()
        font_size = world_to_pixel_width(1)
        font = pygame.font.SysFont('Arial', font_size, True)
        stops = [actor for actor in actors if 'stop' in actor.type_id]
        yields = [actor for actor in actors if 'yield' in actor.type_id]
        stop_font_surface = font.render('STOP', False, COLOR_ALUMINIUM_2)
        stop_font_surface = pygame.transform.scale(stop_font_surface, (stop_font_surface.get_width(), stop_font_surface.get_height() * 2))
        yield_font_surface = font.render('YIELD', False, COLOR_ALUMINIUM_2)
        yield_font_surface = pygame.transform.scale(yield_font_surface, (yield_font_surface.get_width(), yield_font_surface.get_height() * 2))
        for ts_stop in stops:
            draw_traffic_signs(map_surface, stop_font_surface, ts_stop, trigger_color=COLOR_SCARLET_RED_1)
        for ts_yield in yields:
            draw_traffic_signs(map_surface, yield_font_surface, ts_yield, trigger_color=COLOR_ORANGE_1)

    def world_to_pixel(self, location, offset=(0, 0)):
        x = self.scale * self._pixels_per_meter * (location.x - self._world_offset[0])
        y = self.scale * self._pixels_per_meter * (location.y - self._world_offset[1])
        return [int(x - offset[0]), int(y - offset[1])]

    def world_to_pixel_width(self, width):
        return int(self.scale * self._pixels_per_meter * width)

    def scale_map(self, scale):
        if scale != self.scale:
            self.scale = scale
            width = int(self.big_map_surface.get_width() * self.scale)
            self.surface = pygame.transform.smoothscale(self.big_map_surface, (width, width))

def __init__(self, carla_world, carla_map, pixels_per_meter, show_triggers, show_connections, show_spawn_points):
    self._pixels_per_meter = pixels_per_meter
    self.scale = 1.0
    self.show_triggers = show_triggers
    self.show_connections = show_connections
    self.show_spawn_points = show_spawn_points
    waypoints = carla_map.generate_waypoints(2)
    margin = 50
    max_x = max(waypoints, key=lambda x: x.transform.location.x).transform.location.x + margin
    max_y = max(waypoints, key=lambda x: x.transform.location.y).transform.location.y + margin
    min_x = min(waypoints, key=lambda x: x.transform.location.x).transform.location.x - margin
    min_y = min(waypoints, key=lambda x: x.transform.location.y).transform.location.y - margin
    self.width = max(max_x - min_x, max_y - min_y)
    self._world_offset = (min_x, min_y)
    width_in_pixels = int(self._pixels_per_meter * self.width)
    self.big_map_surface = pygame.Surface((width_in_pixels, width_in_pixels)).convert()
    self.draw_road_map(self.big_map_surface, carla_world, carla_map, self.world_to_pixel, self.world_to_pixel_width)
    self.surface = self.big_map_surface

def draw_road_map(self, map_surface, carla_world, carla_map, world_to_pixel, world_to_pixel_width):
    map_surface.fill(COLOR_ALUMINIUM_4)
    precision = 0.05

    def lane_marking_color_to_tango(lane_marking_color):
        tango_color = COLOR_BLACK
        if lane_marking_color == carla.LaneMarkingColor.White:
            tango_color = COLOR_ALUMINIUM_2
        elif lane_marking_color == carla.LaneMarkingColor.Blue:
            tango_color = COLOR_SKY_BLUE_0
        elif lane_marking_color == carla.LaneMarkingColor.Green:
            tango_color = COLOR_CHAMELEON_0
        elif lane_marking_color == carla.LaneMarkingColor.Red:
            tango_color = COLOR_SCARLET_RED_0
        elif lane_marking_color == carla.LaneMarkingColor.Yellow:
            tango_color = COLOR_ORANGE_0
        return tango_color

    def draw_solid_line(surface, color, closed, points, width):
        if len(points) >= 2:
            pygame.draw.lines(surface, color, closed, points, width)

    def draw_broken_line(surface, color, closed, points, width):
        broken_lines = [x for n, x in enumerate(zip(*(iter(points),) * 20)) if n % 3 == 0]
        for line in broken_lines:
            pygame.draw.lines(surface, color, closed, line, width)

    def get_lane_markings(lane_marking_type, lane_marking_color, waypoints, sign):
        margin = 0.2
        if lane_marking_type == carla.LaneMarkingType.Broken or lane_marking_type == carla.LaneMarkingType.Solid:
            marking_1 = [world_to_pixel(lateral_shift(w.transform, sign * w.lane_width * 0.5)) for w in waypoints]
            return [(lane_marking_type, lane_marking_color, marking_1)]
        elif lane_marking_type == carla.LaneMarkingType.SolidBroken or lane_marking_type == carla.LaneMarkingType.BrokenSolid:
            marking_1 = [world_to_pixel(lateral_shift(w.transform, sign * w.lane_width * 0.5)) for w in waypoints]
            marking_2 = [world_to_pixel(lateral_shift(w.transform, sign * (w.lane_width * 0.5 + margin * 2))) for w in waypoints]
            return [(carla.LaneMarkingType.Solid, lane_marking_color, marking_1), (carla.LaneMarkingType.Broken, lane_marking_color, marking_2)]
        elif lane_marking_type == carla.LaneMarkingType.BrokenBroken:
            marking = [world_to_pixel(lateral_shift(w.transform, sign * (w.lane_width * 0.5 - margin))) for w in waypoints]
            return [(carla.LaneMarkingType.Broken, lane_marking_color, marking)]
        elif lane_marking_type == carla.LaneMarkingType.SolidSolid:
            marking = [world_to_pixel(lateral_shift(w.transform, sign * (w.lane_width * 0.5 - margin))) for w in waypoints]
            return [(carla.LaneMarkingType.Solid, lane_marking_color, marking)]
        return [(carla.LaneMarkingType.NONE, carla.LaneMarkingColor.Other, [])]

    def draw_lane_marking(surface, waypoints, is_left):
        sign = -1 if is_left else 1
        lane_marking = None
        marking_type = carla.LaneMarkingType.NONE
        previous_marking_type = carla.LaneMarkingType.NONE
        marking_color = carla.LaneMarkingColor.Other
        previous_marking_color = carla.LaneMarkingColor.Other
        waypoints_list = []
        temp_waypoints = []
        current_lane_marking = carla.LaneMarkingType.NONE
        for sample in waypoints:
            lane_marking = sample.left_lane_marking if sign < 0 else sample.right_lane_marking
            if lane_marking is None:
                continue
            marking_type = lane_marking.type
            marking_color = lane_marking.color
            if current_lane_marking != marking_type:
                markings = get_lane_markings(previous_marking_type, lane_marking_color_to_tango(previous_marking_color), temp_waypoints, sign)
                current_lane_marking = marking_type
                for marking in markings:
                    waypoints_list.append(marking)
                temp_waypoints = temp_waypoints[-1:]
            else:
                temp_waypoints.append(sample)
                previous_marking_type = marking_type
                previous_marking_color = marking_color
        last_markings = get_lane_markings(previous_marking_type, lane_marking_color_to_tango(previous_marking_color), temp_waypoints, sign)
        for marking in last_markings:
            waypoints_list.append(marking)
        for markings in waypoints_list:
            if markings[0] == carla.LaneMarkingType.Solid:
                draw_solid_line(surface, markings[1], False, markings[2], 2)
            elif markings[0] == carla.LaneMarkingType.Broken:
                draw_broken_line(surface, markings[1], False, markings[2], 2)

    def draw_arrow(surface, transform, color=COLOR_ALUMINIUM_2):
        transform.rotation.yaw += 180
        forward = transform.get_forward_vector()
        transform.rotation.yaw += 90
        right_dir = transform.get_forward_vector()
        end = transform.location
        start = end - 2.0 * forward
        right = start + 0.8 * forward + 0.4 * right_dir
        left = start + 0.8 * forward - 0.4 * right_dir
        pygame.draw.lines(surface, color, False, [world_to_pixel(x) for x in [start, end]], 4)
        pygame.draw.lines(surface, color, False, [world_to_pixel(x) for x in [left, start, right]], 4)

    def draw_traffic_signs(surface, font_surface, actor, color=COLOR_ALUMINIUM_2, trigger_color=COLOR_PLUM_0):
        transform = actor.get_transform()
        waypoint = carla_map.get_waypoint(transform.location)
        angle = -waypoint.transform.rotation.yaw - 90.0
        font_surface = pygame.transform.rotate(font_surface, angle)
        pixel_pos = world_to_pixel(waypoint.transform.location)
        offset = font_surface.get_rect(center=(pixel_pos[0], pixel_pos[1]))
        surface.blit(font_surface, offset)
        forward_vector = carla.Location(waypoint.transform.get_forward_vector())
        left_vector = carla.Location(-forward_vector.y, forward_vector.x, forward_vector.z) * waypoint.lane_width / 2 * 0.7
        line = [waypoint.transform.location + forward_vector * 1.5 + left_vector, waypoint.transform.location + forward_vector * 1.5 - left_vector]
        line_pixel = [world_to_pixel(p) for p in line]
        pygame.draw.lines(surface, color, True, line_pixel, 2)
        if self.show_triggers:
            corners = Util.get_bounding_box(actor)
            corners = [world_to_pixel(p) for p in corners]
            pygame.draw.lines(surface, trigger_color, True, corners, 2)

    def lateral_shift(transform, shift):
        transform.rotation.yaw += 90
        return transform.location + shift * transform.get_forward_vector()

    def draw_topology(carla_topology, index):
        topology = [x[index] for x in carla_topology]
        topology = sorted(topology, key=lambda w: w.transform.location.z)
        for waypoint in topology:
            waypoints = [waypoint]
            nxt = waypoint.next(precision)
            if len(nxt) > 0:
                nxt = nxt[0]
                while nxt.road_id == waypoint.road_id:
                    waypoints.append(nxt)
                    nxt = nxt.next(precision)
                    if len(nxt) > 0:
                        nxt = nxt[0]
                    else:
                        break
            road_left_side = [lateral_shift(w.transform, -w.lane_width * 0.5) for w in waypoints]
            road_right_side = [lateral_shift(w.transform, w.lane_width * 0.5) for w in waypoints]
            polygon = road_left_side + [x for x in reversed(road_right_side)]
            polygon = [world_to_pixel(x) for x in polygon]
            if len(polygon) > 2:
                pygame.draw.polygon(map_surface, COLOR_ALUMINIUM_5, polygon, 5)
                pygame.draw.polygon(map_surface, COLOR_ALUMINIUM_5, polygon)
            PARKING_COLOR = COLOR_ALUMINIUM_4_5
            SHOULDER_COLOR = COLOR_ALUMINIUM_5
            final_color = SHOULDER_COLOR
            shoulder = []
            for w in waypoints:
                r = w.get_right_lane()
                if r is not None and (r.lane_type == carla.LaneType.Shoulder or r.lane_type == carla.LaneType.Parking):
                    if r.lane_type == carla.LaneType.Parking:
                        final_color = PARKING_COLOR
                    shoulder.append(r)
            shoulder_left_side = [lateral_shift(w.transform, -w.lane_width * 0.5) for w in shoulder]
            shoulder_right_side = [lateral_shift(w.transform, w.lane_width * 0.5) for w in shoulder]
            polygon = shoulder_left_side + [x for x in reversed(shoulder_right_side)]
            polygon = [world_to_pixel(x) for x in polygon]
            if len(polygon) > 2:
                pygame.draw.polygon(map_surface, final_color, polygon, 5)
                pygame.draw.polygon(map_surface, final_color, polygon)
            draw_lane_marking(map_surface, shoulder, False)
            shoulder = []
            for w in waypoints:
                r = w.get_left_lane()
                if r is not None and (r.lane_type == carla.LaneType.Shoulder or r.lane_type == carla.LaneType.Parking):
                    if r.lane_type == carla.LaneType.Parking:
                        final_color = PARKING_COLOR
                    shoulder.append(r)
            shoulder_left_side = [lateral_shift(w.transform, -w.lane_width * 0.5) for w in shoulder]
            shoulder_right_side = [lateral_shift(w.transform, w.lane_width * 0.5) for w in shoulder]
            polygon = shoulder_left_side + [x for x in reversed(shoulder_right_side)]
            polygon = [world_to_pixel(x) for x in polygon]
            if len(polygon) > 2:
                pygame.draw.polygon(map_surface, final_color, polygon, 5)
                pygame.draw.polygon(map_surface, final_color, polygon)
            draw_lane_marking(map_surface, shoulder, True)
            if not waypoint.is_intersection:
                draw_lane_marking(map_surface, waypoints, True)
                draw_lane_marking(map_surface, waypoints, False)
                for n, wp in enumerate(waypoints):
                    if (n + 1) % 400 == 0:
                        draw_arrow(map_surface, wp.transform)
    topology = carla_map.get_topology()
    draw_topology(topology, 0)
    draw_topology(topology, 1)
    if self.show_spawn_points:
        for sp in carla_map.get_spawn_points():
            draw_arrow(map_surface, sp, color=COLOR_CHOCOLATE_0)
    if self.show_connections:
        dist = 1.5
        to_pixel = lambda wp: world_to_pixel(wp.transform.location)
        for wp in carla_map.generate_waypoints(dist):
            col = (0, 255, 255) if wp.is_intersection else (0, 255, 0)
            for nxt in wp.next(dist):
                pygame.draw.line(map_surface, col, to_pixel(wp), to_pixel(nxt), 2)
            if wp.lane_change & carla.LaneChange.Right:
                r = wp.get_right_lane()
                if r and r.lane_type == carla.LaneType.Driving:
                    pygame.draw.line(map_surface, col, to_pixel(wp), to_pixel(r), 2)
            if wp.lane_change & carla.LaneChange.Left:
                l = wp.get_left_lane()
                if l and l.lane_type == carla.LaneType.Driving:
                    pygame.draw.line(map_surface, col, to_pixel(wp), to_pixel(l), 2)
    actors = carla_world.get_actors()
    font_size = world_to_pixel_width(1)
    font = pygame.font.SysFont('Arial', font_size, True)
    stops = [actor for actor in actors if 'stop' in actor.type_id]
    yields = [actor for actor in actors if 'yield' in actor.type_id]
    stop_font_surface = font.render('STOP', False, COLOR_ALUMINIUM_2)
    stop_font_surface = pygame.transform.scale(stop_font_surface, (stop_font_surface.get_width(), stop_font_surface.get_height() * 2))
    yield_font_surface = font.render('YIELD', False, COLOR_ALUMINIUM_2)
    yield_font_surface = pygame.transform.scale(yield_font_surface, (yield_font_surface.get_width(), yield_font_surface.get_height() * 2))
    for ts_stop in stops:
        draw_traffic_signs(map_surface, stop_font_surface, ts_stop, trigger_color=COLOR_SCARLET_RED_1)
    for ts_yield in yields:
        draw_traffic_signs(map_surface, yield_font_surface, ts_yield, trigger_color=COLOR_ORANGE_1)

def draw_solid_line(surface, color, closed, points, width):
    if len(points) >= 2:
        pygame.draw.lines(surface, color, closed, points, width)

def draw_arrow(surface, transform, color=COLOR_ALUMINIUM_2):
    transform.rotation.yaw += 180
    forward = transform.get_forward_vector()
    transform.rotation.yaw += 90
    right_dir = transform.get_forward_vector()
    end = transform.location
    start = end - 2.0 * forward
    right = start + 0.8 * forward + 0.4 * right_dir
    left = start + 0.8 * forward - 0.4 * right_dir
    pygame.draw.lines(surface, color, False, [world_to_pixel(x) for x in [start, end]], 4)
    pygame.draw.lines(surface, color, False, [world_to_pixel(x) for x in [left, start, right]], 4)

def draw_traffic_signs(surface, font_surface, actor, color=COLOR_ALUMINIUM_2, trigger_color=COLOR_PLUM_0):
    transform = actor.get_transform()
    waypoint = carla_map.get_waypoint(transform.location)
    angle = -waypoint.transform.rotation.yaw - 90.0
    font_surface = pygame.transform.rotate(font_surface, angle)
    pixel_pos = world_to_pixel(waypoint.transform.location)
    offset = font_surface.get_rect(center=(pixel_pos[0], pixel_pos[1]))
    surface.blit(font_surface, offset)
    forward_vector = carla.Location(waypoint.transform.get_forward_vector())
    left_vector = carla.Location(-forward_vector.y, forward_vector.x, forward_vector.z) * waypoint.lane_width / 2 * 0.7
    line = [waypoint.transform.location + forward_vector * 1.5 + left_vector, waypoint.transform.location + forward_vector * 1.5 - left_vector]
    line_pixel = [world_to_pixel(p) for p in line]
    pygame.draw.lines(surface, color, True, line_pixel, 2)
    if self.show_triggers:
        corners = Util.get_bounding_box(actor)
        corners = [world_to_pixel(p) for p in corners]
        pygame.draw.lines(surface, trigger_color, True, corners, 2)

def world_to_pixel(self, location, offset=(0, 0)):
    x = self.scale * self._pixels_per_meter * (location.x - self._world_offset[0])
    y = self.scale * self._pixels_per_meter * (location.y - self._world_offset[1])
    return [int(x - offset[0]), int(y - offset[1])]

def world_to_pixel_width(self, width):
    return int(self.scale * self._pixels_per_meter * width)

def scale_map(self, scale):
    if scale != self.scale:
        self.scale = scale
        width = int(self.big_map_surface.get_width() * self.scale)
        self.surface = pygame.transform.smoothscale(self.big_map_surface, (width, width))

class ModuleWorld(object):

    def __init__(self, name, args, timeout):
        self.client = None
        self.name = name
        self.args = args
        self.timeout = timeout
        self.server_fps = 0.0
        self.simulation_time = 0
        self.server_clock = pygame.time.Clock()
        self.world = None
        self.town_map = None
        self.actors_with_transforms = []
        self.module_hud = None
        self.module_input = None
        self.surface_size = [0, 0]
        self.prev_scaled_size = 0
        self.scaled_size = 0
        self.hero_actor = None
        self.spawned_hero = None
        self.hero_transform = None
        self.scale_offset = [0, 0]
        self.vehicle_id_surface = None
        self.result_surface = None
        self.traffic_light_surfaces = TrafficLightSurfaces()
        self.affected_traffic_light = None
        self.map_image = None
        self.border_round_surface = None
        self.original_surface_size = None
        self.hero_surface = None
        self.actors_surface = None

    def _get_data_from_carla(self):
        try:
            self.client = carla.Client(self.args.host, self.args.port)
            self.client.set_timeout(self.timeout)
            if self.args.map is None:
                world = self.client.get_world()
            else:
                world = self.client.load_world(self.args.map)
            town_map = world.get_map()
            return (world, town_map)
        except RuntimeError as ex:
            logging.error(ex)
            exit_game()

    def start(self):
        self.world, self.town_map = self._get_data_from_carla()
        self.map_image = MapImage(carla_world=self.world, carla_map=self.town_map, pixels_per_meter=PIXELS_PER_METER, show_triggers=self.args.show_triggers, show_connections=self.args.show_connections, show_spawn_points=self.args.show_spawn_points)
        self.module_hud = module_manager.get_module(MODULE_HUD)
        self.module_input = module_manager.get_module(MODULE_INPUT)
        self.original_surface_size = min(self.module_hud.dim[0], self.module_hud.dim[1])
        self.surface_size = self.map_image.big_map_surface.get_width()
        self.scaled_size = int(self.surface_size)
        self.prev_scaled_size = int(self.surface_size)
        self.actors_surface = pygame.Surface((self.map_image.surface.get_width(), self.map_image.surface.get_height()))
        self.actors_surface.set_colorkey(COLOR_BLACK)
        self.vehicle_id_surface = pygame.Surface((self.surface_size, self.surface_size)).convert()
        self.vehicle_id_surface.set_colorkey(COLOR_BLACK)
        self.border_round_surface = pygame.Surface(self.module_hud.dim, pygame.SRCALPHA).convert()
        self.border_round_surface.set_colorkey(COLOR_WHITE)
        self.border_round_surface.fill(COLOR_BLACK)
        center_offset = (int(self.module_hud.dim[0] / 2), int(self.module_hud.dim[1] / 2))
        pygame.draw.circle(self.border_round_surface, COLOR_ALUMINIUM_1, center_offset, int(self.module_hud.dim[1] / 2))
        pygame.draw.circle(self.border_round_surface, COLOR_WHITE, center_offset, int((self.module_hud.dim[1] - 8) / 2))
        scaled_original_size = self.original_surface_size * (1.0 / 0.9)
        self.hero_surface = pygame.Surface((scaled_original_size, scaled_original_size)).convert()
        self.result_surface = pygame.Surface((self.surface_size, self.surface_size)).convert()
        self.result_surface.set_colorkey(COLOR_BLACK)
        self.select_hero_actor()
        self.hero_actor.set_autopilot(False)
        self.module_input.wheel_offset = HERO_DEFAULT_SCALE
        self.module_input.control = carla.VehicleControl()
        weak_self = weakref.ref(self)
        self.world.on_tick(lambda timestamp: ModuleWorld.on_world_tick(weak_self, timestamp))

    def select_hero_actor(self):
        hero_vehicles = [actor for actor in self.world.get_actors() if 'vehicle' in actor.type_id and actor.attributes['role_name'] == 'hero']
        if len(hero_vehicles) > 0:
            self.hero_actor = random.choice(hero_vehicles)
            self.hero_transform = self.hero_actor.get_transform()
        else:
            self._spawn_hero()

    def _spawn_hero(self):
        blueprint = random.choice(self.world.get_blueprint_library().filter(self.args.filter))
        blueprint.set_attribute('role_name', 'hero')
        if blueprint.has_attribute('color'):
            color = random.choice(blueprint.get_attribute('color').recommended_values)
            blueprint.set_attribute('color', color)
        while self.hero_actor is None:
            spawn_points = self.world.get_map().get_spawn_points()
            spawn_point = random.choice(spawn_points) if spawn_points else carla.Transform()
            self.hero_actor = self.world.try_spawn_actor(blueprint, spawn_point)
        self.hero_transform = self.hero_actor.get_transform()
        self.spawned_hero = self.hero_actor

    def tick(self, clock):
        actors = self.world.get_actors()
        self.actors_with_transforms = [(actor, actor.get_transform()) for actor in actors]
        if self.hero_actor is not None:
            self.hero_transform = self.hero_actor.get_transform()
        self.update_hud_info(clock)

    def update_hud_info(self, clock):
        hero_mode_text = []
        if self.hero_actor is not None:
            hero_speed = self.hero_actor.get_velocity()
            hero_speed_text = 3.6 * math.sqrt(hero_speed.x ** 2 + hero_speed.y ** 2 + hero_speed.z ** 2)
            affected_traffic_light_text = 'None'
            if self.affected_traffic_light is not None:
                state = self.affected_traffic_light.state
                if state == carla.TrafficLightState.Green:
                    affected_traffic_light_text = 'GREEN'
                elif state == carla.TrafficLightState.Yellow:
                    affected_traffic_light_text = 'YELLOW'
                else:
                    affected_traffic_light_text = 'RED'
            affected_speed_limit_text = self.hero_actor.get_speed_limit()
            hero_mode_text = ['Hero Mode:                 ON', 'Hero ID:              %7d' % self.hero_actor.id, 'Hero Vehicle:  %14s' % get_actor_display_name(self.hero_actor, truncate=14), 'Hero Speed:          %3d km/h' % hero_speed_text, 'Hero Affected by:', '  Traffic Light: %12s' % affected_traffic_light_text, '  Speed Limit:       %3d km/h' % affected_speed_limit_text]
        else:
            hero_mode_text = ['Hero Mode:                OFF']
        self.server_fps = self.server_clock.get_fps()
        self.server_fps = 'inf' if self.server_fps == float('inf') else round(self.server_fps)
        module_info_text = ['Server:  % 16s FPS' % self.server_fps, 'Client:  % 16s FPS' % round(clock.get_fps()), 'Simulation Time: % 12s' % datetime.timedelta(seconds=int(self.simulation_time)), 'Map Name:          %10s' % self.town_map.name]
        module_info_text = module_info_text
        module_hud = module_manager.get_module(MODULE_HUD)
        module_hud.add_info(self.name, module_info_text)
        module_hud.add_info('HERO', hero_mode_text)

    @staticmethod
    def on_world_tick(weak_self, timestamp):
        self = weak_self()
        if not self:
            return
        self.server_clock.tick()
        self.server_fps = self.server_clock.get_fps()
        self.simulation_time = timestamp.elapsed_seconds

    def _split_actors(self):
        vehicles = []
        traffic_lights = []
        speed_limits = []
        walkers = []
        for actor_with_transform in self.actors_with_transforms:
            actor = actor_with_transform[0]
            if 'vehicle' in actor.type_id:
                vehicles.append(actor_with_transform)
            elif 'traffic_light' in actor.type_id:
                traffic_lights.append(actor_with_transform)
            elif 'speed_limit' in actor.type_id:
                speed_limits.append(actor_with_transform)
            elif 'walker' in actor.type_id:
                walkers.append(actor_with_transform)
        info_text = []
        if self.hero_actor is not None and len(vehicles) > 1:
            location = self.hero_transform.location
            vehicle_list = [x[0] for x in vehicles if x[0].id != self.hero_actor.id]

            def distance(v):
                return location.distance(v.get_location())
            for n, vehicle in enumerate(sorted(vehicle_list, key=distance)):
                if n > 15:
                    break
                vehicle_type = get_actor_display_name(vehicle, truncate=22)
                info_text.append('% 5d %s' % (vehicle.id, vehicle_type))
        module_manager.get_module(MODULE_HUD).add_info('NEARBY VEHICLES', info_text)
        return (vehicles, traffic_lights, speed_limits, walkers)

    def _render_traffic_lights(self, surface, list_tl, world_to_pixel):
        self.affected_traffic_light = None
        for tl in list_tl:
            world_pos = tl.get_location()
            pos = world_to_pixel(world_pos)
            if self.args.show_triggers:
                corners = Util.get_bounding_box(tl)
                corners = [world_to_pixel(p) for p in corners]
                pygame.draw.lines(surface, COLOR_BUTTER_1, True, corners, 2)
            if self.hero_actor is not None:
                corners = Util.get_bounding_box(tl)
                corners = [world_to_pixel(p) for p in corners]
                tl_t = tl.get_transform()
                transformed_tv = tl_t.transform(tl.trigger_volume.location)
                hero_location = self.hero_actor.get_location()
                d = hero_location.distance(transformed_tv)
                s = Util.length(tl.trigger_volume.extent) + Util.length(self.hero_actor.bounding_box.extent)
                if d <= s:
                    self.affected_traffic_light = tl
                    srf = self.traffic_light_surfaces.surfaces['h']
                    surface.blit(srf, srf.get_rect(center=pos))
            srf = self.traffic_light_surfaces.surfaces[tl.state]
            surface.blit(srf, srf.get_rect(center=pos))

    def _render_speed_limits(self, surface, list_sl, world_to_pixel, world_to_pixel_width):
        font_size = world_to_pixel_width(2)
        radius = world_to_pixel_width(2)
        font = pygame.font.SysFont('Arial', font_size)
        for sl in list_sl:
            x, y = world_to_pixel(sl.get_location())
            white_circle_radius = int(radius * 0.75)
            pygame.draw.circle(surface, COLOR_SCARLET_RED_1, (x, y), radius)
            pygame.draw.circle(surface, COLOR_ALUMINIUM_0, (x, y), white_circle_radius)
            limit = sl.type_id.split('.')[2]
            font_surface = font.render(limit, True, COLOR_ALUMINIUM_5)
            if self.args.show_triggers:
                corners = Util.get_bounding_box(sl)
                corners = [world_to_pixel(p) for p in corners]
                pygame.draw.lines(surface, COLOR_PLUM_2, True, corners, 2)
            if self.hero_actor is not None:
                angle = -self.hero_transform.rotation.yaw - 90.0
                font_surface = pygame.transform.rotate(font_surface, angle)
                offset = font_surface.get_rect(center=(x, y))
                surface.blit(font_surface, offset)
            else:
                surface.blit(font_surface, (x - radius / 2, y - radius / 2))

    def _render_walkers(self, surface, list_w, world_to_pixel):
        for w in list_w:
            color = COLOR_PLUM_0
            bb = w[0].bounding_box.extent
            corners = [carla.Location(x=-bb.x, y=-bb.y), carla.Location(x=bb.x, y=-bb.y), carla.Location(x=bb.x, y=bb.y), carla.Location(x=-bb.x, y=bb.y)]
            w[1].transform(corners)
            corners = [world_to_pixel(p) for p in corners]
            pygame.draw.polygon(surface, color, corners)

    def _render_vehicles(self, surface, list_v, world_to_pixel):
        for v in list_v:
            color = COLOR_SKY_BLUE_0
            if int(v[0].attributes['number_of_wheels']) == 2:
                color = COLOR_CHOCOLATE_1
            if v[0].attributes['role_name'] == 'hero':
                color = COLOR_CHAMELEON_0
            bb = v[0].bounding_box.extent
            corners = [carla.Location(x=-bb.x, y=-bb.y), carla.Location(x=bb.x - 0.8, y=-bb.y), carla.Location(x=bb.x, y=0), carla.Location(x=bb.x - 0.8, y=bb.y), carla.Location(x=-bb.x, y=bb.y), carla.Location(x=-bb.x, y=-bb.y)]
            v[1].transform(corners)
            corners = [world_to_pixel(p) for p in corners]
            pygame.draw.lines(surface, color, False, corners, int(math.ceil(4.0 * self.map_image.scale)))

    def render_actors(self, surface, vehicles, traffic_lights, speed_limits, walkers):
        self._render_traffic_lights(surface, [tl[0] for tl in traffic_lights], self.map_image.world_to_pixel)
        self._render_speed_limits(surface, [sl[0] for sl in speed_limits], self.map_image.world_to_pixel, self.map_image.world_to_pixel_width)
        self._render_vehicles(surface, vehicles, self.map_image.world_to_pixel)
        self._render_walkers(surface, walkers, self.map_image.world_to_pixel)

    def clip_surfaces(self, clipping_rect):
        self.actors_surface.set_clip(clipping_rect)
        self.vehicle_id_surface.set_clip(clipping_rect)
        self.result_surface.set_clip(clipping_rect)

    def _compute_scale(self, scale_factor):
        m = self.module_input.mouse_pos
        px = (m[0] - self.scale_offset[0]) / float(self.prev_scaled_size)
        py = (m[1] - self.scale_offset[1]) / float(self.prev_scaled_size)
        diff_between_scales = (float(self.prev_scaled_size) * px - float(self.scaled_size) * px, float(self.prev_scaled_size) * py - float(self.scaled_size) * py)
        self.scale_offset = (self.scale_offset[0] + diff_between_scales[0], self.scale_offset[1] + diff_between_scales[1])
        self.prev_scaled_size = self.scaled_size
        self.map_image.scale_map(scale_factor)

    def render(self, display):
        if self.actors_with_transforms is None:
            return
        self.result_surface.fill(COLOR_BLACK)
        vehicles, traffic_lights, speed_limits, walkers = self._split_actors()
        scale_factor = self.module_input.wheel_offset
        self.scaled_size = int(self.map_image.width * scale_factor)
        if self.scaled_size != self.prev_scaled_size:
            self._compute_scale(scale_factor)
        self.actors_surface.fill(COLOR_BLACK)
        self.render_actors(self.actors_surface, vehicles, traffic_lights, speed_limits, walkers)
        self.module_hud.render_vehicles_ids(self.vehicle_id_surface, vehicles, self.map_image.world_to_pixel, self.hero_actor, self.hero_transform)
        surfaces = ((self.map_image.surface, (0, 0)), (self.actors_surface, (0, 0)), (self.vehicle_id_surface, (0, 0)))
        angle = 0.0 if self.hero_actor is None else self.hero_transform.rotation.yaw + 90.0
        self.traffic_light_surfaces.rotozoom(-angle, self.map_image.scale)
        center_offset = (0, 0)
        if self.hero_actor is not None:
            hero_location_screen = self.map_image.world_to_pixel(self.hero_transform.location)
            hero_front = self.hero_transform.get_forward_vector()
            translation_offset = (hero_location_screen[0] - self.hero_surface.get_width() / 2 + hero_front.x * PIXELS_AHEAD_VEHICLE, hero_location_screen[1] - self.hero_surface.get_height() / 2 + hero_front.y * PIXELS_AHEAD_VEHICLE)
            clipping_rect = pygame.Rect(translation_offset[0], translation_offset[1], self.hero_surface.get_width(), self.hero_surface.get_height())
            self.clip_surfaces(clipping_rect)
            Util.blits(self.result_surface, surfaces)
            self.border_round_surface.set_clip(clipping_rect)
            self.hero_surface.fill(COLOR_ALUMINIUM_4)
            self.hero_surface.blit(self.result_surface, (-translation_offset[0], -translation_offset[1]))
            rotated_result_surface = pygame.transform.rotozoom(self.hero_surface, angle, 0.9).convert()
            center = (display.get_width() / 2, display.get_height() / 2)
            rotation_pivot = rotated_result_surface.get_rect(center=center)
            display.blit(rotated_result_surface, rotation_pivot)
            display.blit(self.border_round_surface, (0, 0))
        else:
            translation_offset = (self.module_input.mouse_offset[0] * scale_factor + self.scale_offset[0], self.module_input.mouse_offset[1] * scale_factor + self.scale_offset[1])
            center_offset = (abs(display.get_width() - self.surface_size) / 2 * scale_factor, 0)
            clipping_rect = pygame.Rect(-translation_offset[0] - center_offset[0], -translation_offset[1], self.module_hud.dim[0], self.module_hud.dim[1])
            self.clip_surfaces(clipping_rect)
            Util.blits(self.result_surface, surfaces)
            display.blit(self.result_surface, (translation_offset[0] + center_offset[0], translation_offset[1]))

    def destroy(self):
        if self.spawned_hero is not None:
            self.spawned_hero.destroy()

def __init__(self, name, args, timeout):
    self.client = None
    self.name = name
    self.args = args
    self.timeout = timeout
    self.server_fps = 0.0
    self.simulation_time = 0
    self.server_clock = pygame.time.Clock()
    self.world = None
    self.town_map = None
    self.actors_with_transforms = []
    self.module_hud = None
    self.module_input = None
    self.surface_size = [0, 0]
    self.prev_scaled_size = 0
    self.scaled_size = 0
    self.hero_actor = None
    self.spawned_hero = None
    self.hero_transform = None
    self.scale_offset = [0, 0]
    self.vehicle_id_surface = None
    self.result_surface = None
    self.traffic_light_surfaces = TrafficLightSurfaces()
    self.affected_traffic_light = None
    self.map_image = None
    self.border_round_surface = None
    self.original_surface_size = None
    self.hero_surface = None
    self.actors_surface = None

def start(self):
    self.world, self.town_map = self._get_data_from_carla()
    self.map_image = MapImage(carla_world=self.world, carla_map=self.town_map, pixels_per_meter=PIXELS_PER_METER, show_triggers=self.args.show_triggers, show_connections=self.args.show_connections, show_spawn_points=self.args.show_spawn_points)
    self.module_hud = module_manager.get_module(MODULE_HUD)
    self.module_input = module_manager.get_module(MODULE_INPUT)
    self.original_surface_size = min(self.module_hud.dim[0], self.module_hud.dim[1])
    self.surface_size = self.map_image.big_map_surface.get_width()
    self.scaled_size = int(self.surface_size)
    self.prev_scaled_size = int(self.surface_size)
    self.actors_surface = pygame.Surface((self.map_image.surface.get_width(), self.map_image.surface.get_height()))
    self.actors_surface.set_colorkey(COLOR_BLACK)
    self.vehicle_id_surface = pygame.Surface((self.surface_size, self.surface_size)).convert()
    self.vehicle_id_surface.set_colorkey(COLOR_BLACK)
    self.border_round_surface = pygame.Surface(self.module_hud.dim, pygame.SRCALPHA).convert()
    self.border_round_surface.set_colorkey(COLOR_WHITE)
    self.border_round_surface.fill(COLOR_BLACK)
    center_offset = (int(self.module_hud.dim[0] / 2), int(self.module_hud.dim[1] / 2))
    pygame.draw.circle(self.border_round_surface, COLOR_ALUMINIUM_1, center_offset, int(self.module_hud.dim[1] / 2))
    pygame.draw.circle(self.border_round_surface, COLOR_WHITE, center_offset, int((self.module_hud.dim[1] - 8) / 2))
    scaled_original_size = self.original_surface_size * (1.0 / 0.9)
    self.hero_surface = pygame.Surface((scaled_original_size, scaled_original_size)).convert()
    self.result_surface = pygame.Surface((self.surface_size, self.surface_size)).convert()
    self.result_surface.set_colorkey(COLOR_BLACK)
    self.select_hero_actor()
    self.hero_actor.set_autopilot(False)
    self.module_input.wheel_offset = HERO_DEFAULT_SCALE
    self.module_input.control = carla.VehicleControl()
    weak_self = weakref.ref(self)
    self.world.on_tick(lambda timestamp: ModuleWorld.on_world_tick(weak_self, timestamp))

def _render_traffic_lights(self, surface, list_tl, world_to_pixel):
    self.affected_traffic_light = None
    for tl in list_tl:
        world_pos = tl.get_location()
        pos = world_to_pixel(world_pos)
        if self.args.show_triggers:
            corners = Util.get_bounding_box(tl)
            corners = [world_to_pixel(p) for p in corners]
            pygame.draw.lines(surface, COLOR_BUTTER_1, True, corners, 2)
        if self.hero_actor is not None:
            corners = Util.get_bounding_box(tl)
            corners = [world_to_pixel(p) for p in corners]
            tl_t = tl.get_transform()
            transformed_tv = tl_t.transform(tl.trigger_volume.location)
            hero_location = self.hero_actor.get_location()
            d = hero_location.distance(transformed_tv)
            s = Util.length(tl.trigger_volume.extent) + Util.length(self.hero_actor.bounding_box.extent)
            if d <= s:
                self.affected_traffic_light = tl
                srf = self.traffic_light_surfaces.surfaces['h']
                surface.blit(srf, srf.get_rect(center=pos))
        srf = self.traffic_light_surfaces.surfaces[tl.state]
        surface.blit(srf, srf.get_rect(center=pos))

def _render_speed_limits(self, surface, list_sl, world_to_pixel, world_to_pixel_width):
    font_size = world_to_pixel_width(2)
    radius = world_to_pixel_width(2)
    font = pygame.font.SysFont('Arial', font_size)
    for sl in list_sl:
        x, y = world_to_pixel(sl.get_location())
        white_circle_radius = int(radius * 0.75)
        pygame.draw.circle(surface, COLOR_SCARLET_RED_1, (x, y), radius)
        pygame.draw.circle(surface, COLOR_ALUMINIUM_0, (x, y), white_circle_radius)
        limit = sl.type_id.split('.')[2]
        font_surface = font.render(limit, True, COLOR_ALUMINIUM_5)
        if self.args.show_triggers:
            corners = Util.get_bounding_box(sl)
            corners = [world_to_pixel(p) for p in corners]
            pygame.draw.lines(surface, COLOR_PLUM_2, True, corners, 2)
        if self.hero_actor is not None:
            angle = -self.hero_transform.rotation.yaw - 90.0
            font_surface = pygame.transform.rotate(font_surface, angle)
            offset = font_surface.get_rect(center=(x, y))
            surface.blit(font_surface, offset)
        else:
            surface.blit(font_surface, (x - radius / 2, y - radius / 2))

def _render_vehicles(self, surface, list_v, world_to_pixel):
    for v in list_v:
        color = COLOR_SKY_BLUE_0
        if int(v[0].attributes['number_of_wheels']) == 2:
            color = COLOR_CHOCOLATE_1
        if v[0].attributes['role_name'] == 'hero':
            color = COLOR_CHAMELEON_0
        bb = v[0].bounding_box.extent
        corners = [carla.Location(x=-bb.x, y=-bb.y), carla.Location(x=bb.x - 0.8, y=-bb.y), carla.Location(x=bb.x, y=0), carla.Location(x=bb.x - 0.8, y=bb.y), carla.Location(x=-bb.x, y=bb.y), carla.Location(x=-bb.x, y=-bb.y)]
        v[1].transform(corners)
        corners = [world_to_pixel(p) for p in corners]
        pygame.draw.lines(surface, color, False, corners, int(math.ceil(4.0 * self.map_image.scale)))

def clip_surfaces(self, clipping_rect):
    self.actors_surface.set_clip(clipping_rect)
    self.vehicle_id_surface.set_clip(clipping_rect)
    self.result_surface.set_clip(clipping_rect)

def render(self, display):
    if self.actors_with_transforms is None:
        return
    self.result_surface.fill(COLOR_BLACK)
    vehicles, traffic_lights, speed_limits, walkers = self._split_actors()
    scale_factor = self.module_input.wheel_offset
    self.scaled_size = int(self.map_image.width * scale_factor)
    if self.scaled_size != self.prev_scaled_size:
        self._compute_scale(scale_factor)
    self.actors_surface.fill(COLOR_BLACK)
    self.render_actors(self.actors_surface, vehicles, traffic_lights, speed_limits, walkers)
    self.module_hud.render_vehicles_ids(self.vehicle_id_surface, vehicles, self.map_image.world_to_pixel, self.hero_actor, self.hero_transform)
    surfaces = ((self.map_image.surface, (0, 0)), (self.actors_surface, (0, 0)), (self.vehicle_id_surface, (0, 0)))
    angle = 0.0 if self.hero_actor is None else self.hero_transform.rotation.yaw + 90.0
    self.traffic_light_surfaces.rotozoom(-angle, self.map_image.scale)
    center_offset = (0, 0)
    if self.hero_actor is not None:
        hero_location_screen = self.map_image.world_to_pixel(self.hero_transform.location)
        hero_front = self.hero_transform.get_forward_vector()
        translation_offset = (hero_location_screen[0] - self.hero_surface.get_width() / 2 + hero_front.x * PIXELS_AHEAD_VEHICLE, hero_location_screen[1] - self.hero_surface.get_height() / 2 + hero_front.y * PIXELS_AHEAD_VEHICLE)
        clipping_rect = pygame.Rect(translation_offset[0], translation_offset[1], self.hero_surface.get_width(), self.hero_surface.get_height())
        self.clip_surfaces(clipping_rect)
        Util.blits(self.result_surface, surfaces)
        self.border_round_surface.set_clip(clipping_rect)
        self.hero_surface.fill(COLOR_ALUMINIUM_4)
        self.hero_surface.blit(self.result_surface, (-translation_offset[0], -translation_offset[1]))
        rotated_result_surface = pygame.transform.rotozoom(self.hero_surface, angle, 0.9).convert()
        center = (display.get_width() / 2, display.get_height() / 2)
        rotation_pivot = rotated_result_surface.get_rect(center=center)
        display.blit(rotated_result_surface, rotation_pivot)
        display.blit(self.border_round_surface, (0, 0))
    else:
        translation_offset = (self.module_input.mouse_offset[0] * scale_factor + self.scale_offset[0], self.module_input.mouse_offset[1] * scale_factor + self.scale_offset[1])
        center_offset = (abs(display.get_width() - self.surface_size) / 2 * scale_factor, 0)
        clipping_rect = pygame.Rect(-translation_offset[0] - center_offset[0], -translation_offset[1], self.module_hud.dim[0], self.module_hud.dim[1])
        self.clip_surfaces(clipping_rect)
        Util.blits(self.result_surface, surfaces)
        display.blit(self.result_surface, (translation_offset[0] + center_offset[0], translation_offset[1]))

def game_loop(args):
    try:
        pygame.init()
        display = pygame.display.set_mode((args.width, args.height), pygame.HWSURFACE | pygame.DOUBLEBUF)
        pygame.display.set_caption(args.description)
        font = pygame.font.Font(pygame.font.get_default_font(), 20)
        text_surface = font.render('Rendering map...', True, COLOR_WHITE)
        display.blit(text_surface, text_surface.get_rect(center=(args.width / 2, args.height / 2)))
        pygame.display.flip()
        input_module = ModuleInput(MODULE_INPUT)
        hud_module = ModuleHUD(MODULE_HUD, args.width, args.height)
        world_module = ModuleWorld(MODULE_WORLD, args, timeout=2.0)
        module_manager.register_module(world_module)
        module_manager.register_module(hud_module)
        module_manager.register_module(input_module)
        module_manager.start_modules()
        clock = pygame.time.Clock()
        while True:
            clock.tick_busy_loop(60)
            module_manager.tick(clock)
            module_manager.render(display)
            pygame.display.flip()
    except KeyboardInterrupt:
        print('\nCancelled by user. Bye!')
    finally:
        if world_module is not None:
            world_module.destroy()

def exit_game():
    module_manager.clear_modules()
    pygame.quit()
    sys.exit()

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

class MaxVelocityTest(Criterion):
    """
    This class contains an atomic test for maximum velocity.

    Important parameters:
    - actor: CARLA actor to be used for this test
    - max_velocity_allowed: maximum allowed velocity in m/s
    - optional [optional]: If True, the result is not considered for an overall pass/fail result
    """

    def __init__(self, actor, max_velocity_allowed, optional=False, name='CheckMaximumVelocity'):
        """
        Setup actor and maximum allowed velovity
        """
        super(MaxVelocityTest, self).__init__(name, actor, max_velocity_allowed, None, optional)

    def update(self):
        """
        Check velocity
        """
        new_status = py_trees.common.Status.RUNNING
        if self.actor is None:
            return new_status
        velocity = CarlaDataProvider.get_velocity(self.actor)
        self.actual_value = max(velocity, self.actual_value)
        if velocity > self.expected_value_success:
            self.test_status = 'FAILURE'
        else:
            self.test_status = 'SUCCESS'
        if self._terminate_on_failure and self.test_status == 'FAILURE':
            new_status = py_trees.common.Status.FAILURE
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

def update(self):
    """
        Check velocity
        """
    new_status = py_trees.common.Status.RUNNING
    if self.actor is None:
        return new_status
    velocity = CarlaDataProvider.get_velocity(self.actor)
    self.actual_value = max(velocity, self.actual_value)
    if velocity > self.expected_value_success:
        self.test_status = 'FAILURE'
    else:
        self.test_status = 'SUCCESS'
    if self._terminate_on_failure and self.test_status == 'FAILURE':
        new_status = py_trees.common.Status.FAILURE
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    return new_status

class MaxVelocityTest(Criterion):
    """
    This class contains an atomic test for maximum velocity.

    Important parameters:
    - actor: CARLA actor to be used for this test
    - max_velocity_allowed: maximum allowed velocity in m/s
    - optional [optional]: If True, the result is not considered for an overall pass/fail result
    """

    def __init__(self, actor, max_velocity_allowed, optional=False, name='CheckMaximumVelocity'):
        """
        Setup actor and maximum allowed velovity
        """
        super(MaxVelocityTest, self).__init__(name, actor, max_velocity_allowed, None, optional)

    def update(self):
        """
        Check velocity
        """
        new_status = py_trees.common.Status.RUNNING
        if self.actor is None:
            return new_status
        velocity = CarlaDataProvider.get_velocity(self.actor)
        self.actual_value = max(velocity, self.actual_value)
        if velocity > self.expected_value_success:
            self.test_status = 'FAILURE'
        else:
            self.test_status = 'SUCCESS'
        if self._terminate_on_failure and self.test_status == 'FAILURE':
            new_status = py_trees.common.Status.FAILURE
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

def update(self):
    """
        Check velocity
        """
    new_status = py_trees.common.Status.RUNNING
    if self.actor is None:
        return new_status
    velocity = CarlaDataProvider.get_velocity(self.actor)
    self.actual_value = max(velocity, self.actual_value)
    if velocity > self.expected_value_success:
        self.test_status = 'FAILURE'
    else:
        self.test_status = 'SUCCESS'
    if self._terminate_on_failure and self.test_status == 'FAILURE':
        new_status = py_trees.common.Status.FAILURE
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    return new_status

class ActorControl(object):
    """
    This class provides a wrapper (access mechanism) for user-defined actor controls.
    The controllers are loaded via importlib. Therefore, the module name of the controller
    has to match the control class name (e.g. my_own_control.py and MyOwnControl()).

    At the moment only controllers implemented in Python are supported, or controllers that
    are completely implemented outside of ScenarioRunner (see ExternalControl).

    This wrapper is for example used to realize the OpenSCENARIO controllers.

    Note:
       If no controllers are provided in OpenSCENARIO a default controller for vehicles and
       pedestrians is instantiated. For vehicles the NpcVehicleControl is used, for pedestrians
       it is the PedestrianControl.

    Args:
        actor (carla.Actor): Actor that should be controlled by the controller.
        control_py_module (string): Fully qualified path to the controller python module.
        args (dict): A dictionary containing all parameters of the controller as (key, value) pairs.

    Attributes:
        control_instance: Instance of the user-defined controller.
        _last_longitudinal_command: Timestamp of the last issued longitudinal control command (e.g. target speed).
            Defaults to None. Used to avoid that 2 longitudinal control commands are issued at the same time.
        _last_waypoint_command: Timestamp of the last issued waypoint control command.
            Defaults to None. Used to avoid that 2 waypoint control commands are issued at the same time.
    """
    control_instance = None
    _last_longitudinal_command = None
    _last_waypoint_command = None

    def __init__(self, actor, control_py_module, args):
        if not control_py_module:
            if isinstance(actor, carla.Walker):
                self.control_instance = PedestrianControl(actor)
            elif isinstance(actor, carla.Vehicle):
                self.control_instance = NpcVehicleControl(actor)
            else:
                self.control_instance = ExternalControl(actor)
        else:
            if '.py' in control_py_module:
                module_name = os.path.basename(control_py_module).split('.')[0]
                sys.path.append(os.path.dirname(control_py_module))
                module_control = importlib.import_module(module_name)
                control_class_name = module_control.__name__.title().replace('_', '')
            else:
                sys.path.append(os.path.dirname(__file__))
                module_control = importlib.import_module(control_py_module)
                control_class_name = control_py_module.split('.')[-1].title().replace('_', '')
            self.control_instance = getattr(module_control, control_class_name)(actor, args)

    def reset(self):
        """
        Reset the controller
        """
        self.control_instance.reset()

    def update_target_speed(self, target_speed, start_time=None):
        """
        Update the actor's target speed.

        Args:
            target_speed (float): New target speed [m/s].
            start_time (float): Start time of the new "maneuver" [s].
        """
        self.control_instance.update_target_speed(target_speed)
        if start_time:
            self._last_longitudinal_command = start_time

    def update_waypoints(self, waypoints, start_time=None):
        """
        Update the actor's waypoints

        Args:
            waypoints (List of carla.Transform): List of new waypoints.
            start_time (float): Start time of the new "maneuver" [s].
        """
        self.control_instance.update_waypoints(waypoints)
        if start_time:
            self._last_waypoint_command = start_time

    def check_reached_waypoint_goal(self):
        """
        Check if the actor reached the end of the waypoint list

        returns:
            True if the end was reached, False otherwise.
        """
        return self.control_instance.check_reached_waypoint_goal()

    def get_last_longitudinal_command(self):
        """
        Get timestamp of the last issued longitudinal control command (target_speed)

        returns:
            Timestamp of last longitudinal control command
        """
        return self._last_longitudinal_command

    def get_last_waypoint_command(self):
        """
        Get timestamp of the last issued waypoint control command

        returns:
            Timestamp of last waypoint control command
        """
        return self._last_waypoint_command

    def set_init_speed(self):
        """
        Update the actor's initial speed setting
        """
        self.control_instance.set_init_speed()

    def run_step(self):
        """
        Execute on tick of the controller's control loop
        """
        self.control_instance.run_step()

def __init__(self, actor, control_py_module, args):
    if not control_py_module:
        if isinstance(actor, carla.Walker):
            self.control_instance = PedestrianControl(actor)
        elif isinstance(actor, carla.Vehicle):
            self.control_instance = NpcVehicleControl(actor)
        else:
            self.control_instance = ExternalControl(actor)
    else:
        if '.py' in control_py_module:
            module_name = os.path.basename(control_py_module).split('.')[0]
            sys.path.append(os.path.dirname(control_py_module))
            module_control = importlib.import_module(module_name)
            control_class_name = module_control.__name__.title().replace('_', '')
        else:
            sys.path.append(os.path.dirname(__file__))
            module_control = importlib.import_module(control_py_module)
            control_class_name = control_py_module.split('.')[-1].title().replace('_', '')
        self.control_instance = getattr(module_control, control_class_name)(actor, args)

def get_geometric_linear_intersection(ego_actor, other_actor):
    """
    Obtain a intersection point between two actor's location by using their waypoints (wp)

    @return point of intersection of the two vehicles
    """
    wp_ego_1 = CarlaDataProvider.get_map().get_waypoint(ego_actor.get_location())
    wp_ego_2 = wp_ego_1.next(1)[0]
    x_ego_1 = wp_ego_1.transform.location.x
    y_ego_1 = wp_ego_1.transform.location.y
    x_ego_2 = wp_ego_2.transform.location.x
    y_ego_2 = wp_ego_2.transform.location.y
    wp_other_1 = CarlaDataProvider.get_world().get_map().get_waypoint(other_actor.get_location())
    wp_other_2 = wp_other_1.next(1)[0]
    x_other_1 = wp_other_1.transform.location.x
    y_other_1 = wp_other_1.transform.location.y
    x_other_2 = wp_other_2.transform.location.x
    y_other_2 = wp_other_2.transform.location.y
    s = np.vstack([(x_ego_1, y_ego_1), (x_ego_2, y_ego_2), (x_other_1, y_other_1), (x_other_2, y_other_2)])
    h = np.hstack((s, np.ones((4, 1))))
    line1 = np.cross(h[0], h[1])
    line2 = np.cross(h[2], h[3])
    x, y, z = np.cross(line1, line2)
    if z == 0:
        return (float('inf'), float('inf'))
    intersection = carla.Location(x=x / z, y=y / z, z=0)
    return intersection

class RotatedRectangle(object):
    """
    This class contains method to draw rectangle and find intersection point.
    """

    def __init__(self, c_x, c_y, width, height, angle):
        self.c_x = c_x
        self.c_y = c_y
        self.w = width
        self.h = height
        self.angle = angle

    def get_contour(self):
        """
        create contour
        """
        w = self.w
        h = self.h
        c = shapely.geometry.box(-w / 2.0, -h / 2.0, w / 2.0, h / 2.0)
        rc = shapely.affinity.rotate(c, self.angle)
        return shapely.affinity.translate(rc, self.c_x, self.c_y)

    def intersection(self, other):
        """
        Obtain a intersection point between two contour.
        """
        return self.get_contour().intersection(other.get_contour())

def get_contour(self):
    """
        create contour
        """
    w = self.w
    h = self.h
    c = shapely.geometry.box(-w / 2.0, -h / 2.0, w / 2.0, h / 2.0)
    rc = shapely.affinity.rotate(c, self.angle)
    return shapely.affinity.translate(rc, self.c_x, self.c_y)

class OpenScenarioConfiguration(ScenarioConfiguration):
    """
    Limitations:
    - Only one Story + Init is supported per Storyboard
    """

    def __init__(self, filename, client):
        self.xml_tree = ET.parse(filename)
        self._filename = filename
        self._validate_openscenario_configuration()
        self.client = client
        self.catalogs = {}
        self.other_actors = []
        self.ego_vehicles = []
        self.trigger_points = []
        self.weather = carla.WeatherParameters()
        self.storyboard = self.xml_tree.find('Storyboard')
        self.story = self.storyboard.find('Story')
        self.init = self.storyboard.find('Init')
        logging.basicConfig()
        self.logger = logging.getLogger('[SR:OpenScenarioConfiguration]')
        self._global_parameters = {}
        self._set_parameters()
        self._parse_openscenario_configuration()

    def _validate_openscenario_configuration(self):
        """
        Validate the given OpenSCENARIO config against the 0.9.1 XSD

        Note: This will throw if the config is not valid. But this is fine here.
        """
        xsd_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../openscenario/OpenSCENARIO.xsd')
        xsd = xmlschema.XMLSchema(xsd_file)
        xsd.validate(self.xml_tree)

    def _validate_openscenario_catalog_configuration(self, catalog_xml_tree):
        """
        Validate the given OpenSCENARIO catalog config against the 0.9.1 XSD

        Note: This will throw if the catalog config is not valid. But this is fine here.
        """
        xsd_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../openscenario/OpenSCENARIO.xsd')
        xsd = xmlschema.XMLSchema(xsd_file)
        xsd.validate(catalog_xml_tree)

    def _parse_openscenario_configuration(self):
        """
        Parse the given OpenSCENARIO config file, set and validate parameters
        """
        OpenScenarioParser.set_osc_filepath(os.path.dirname(self._filename))
        self._check_version()
        self._load_catalogs()
        self._set_scenario_name()
        self._set_carla_town()
        self._set_actor_information()
        self._validate_result()

    def _check_version(self):
        """
        Ensure correct OpenSCENARIO version is used
        """
        header = self.xml_tree.find('FileHeader')
        if not (header.attrib.get('revMajor') == '1' and header.attrib.get('revMinor') == '0'):
            raise AttributeError('Only OpenSCENARIO 1.0 is supported')

    def _load_catalogs(self):
        """
        Read Catalog xml files into dictionary for later use

        NOTE: Catalogs must have distinct names, even across different types
        """
        catalogs = self.xml_tree.find('CatalogLocations')
        if list(catalogs) is None:
            return
        catalog_types = ['Vehicle', 'Controller', 'Pedestrian', 'MiscObject', 'Environment', 'Maneuver', 'Trajectory', 'Route']
        for catalog_type in catalog_types:
            catalog = catalogs.find(catalog_type + 'Catalog')
            if catalog is None:
                continue
            catalog_path = catalog.find('Directory').attrib.get('path') + '/' + catalog_type + 'Catalog.xosc'
            if not os.path.isabs(catalog_path) and 'xosc' in self._filename:
                catalog_path = os.path.dirname(os.path.abspath(self._filename)) + '/' + catalog_path
            if not os.path.isfile(catalog_path):
                self.logger.warning(' The %s path for the %s Catalog is invalid', catalog_path, catalog_type)
            else:
                xml_tree = ET.parse(catalog_path)
                self._validate_openscenario_catalog_configuration(xml_tree)
                catalog = xml_tree.find('Catalog')
                catalog_name = catalog.attrib.get('name')
                self.catalogs[catalog_name] = {}
                for entry in catalog:
                    self.catalogs[catalog_name][entry.attrib.get('name')] = entry

    def _set_scenario_name(self):
        """
        Extract the scenario name from the OpenSCENARIO header information
        """
        header = self.xml_tree.find('FileHeader')
        self.name = header.attrib.get('description', 'Unknown')
        if self.name.startswith('CARLA:'):
            OpenScenarioParser.set_use_carla_coordinate_system()

    def _set_carla_town(self):
        """
        Extract the CARLA town (level) from the RoadNetwork information from OpenSCENARIO

        Note: The specification allows multiple Logics elements within the RoadNetwork element.
              Hence, there can be multiple towns specified. We just use the _last_ one.
        """
        for logic in self.xml_tree.find('RoadNetwork').findall('LogicFile'):
            self.town = logic.attrib.get('filepath', None)
        if self.town is not None and '.xodr' in self.town:
            if not os.path.isabs(self.town):
                self.town = os.path.dirname(os.path.abspath(self._filename)) + '/' + self.town
            if not os.path.exists(self.town):
                raise AttributeError("The provided RoadNetwork '{}' does not exist".format(self.town))
        world = self.client.get_world()
        if world is None or world.get_map().name != self.town:
            self.logger.warning(' Wrong OpenDRIVE map in use. Forcing reload of CARLA world')
            if '.xodr' in self.town:
                with open(self.town) as od_file:
                    data = od_file.read()
                self.client.generate_opendrive_world(str(data))
            else:
                self.client.load_world(self.town)
            world = self.client.get_world()
            CarlaDataProvider.set_world(world)
            world.wait_for_tick()
        else:
            CarlaDataProvider.set_world(world)

    def _set_parameters(self):
        """
        Parse the complete scenario definition file, and replace all parameter references
        with the actual values

        Set _global_parameters.
        """
        self.xml_tree, self._global_parameters = OpenScenarioParser.set_parameters(self.xml_tree)
        for elem in self.xml_tree.iter():
            if elem.find('ParameterDeclarations') is not None:
                elem, _ = OpenScenarioParser.set_parameters(elem)
        OpenScenarioParser.set_global_parameters(self._global_parameters)

    def _set_actor_information(self):
        """
        Extract all actors and their corresponding specification

        NOTE: The rolename property has to be unique!
        """
        for entity in self.xml_tree.iter('Entities'):
            for obj in entity.iter('ScenarioObject'):
                rolename = obj.attrib.get('name', 'simulation')
                args = dict()
                for prop in obj.iter('Property'):
                    key = prop.get('name')
                    value = prop.get('value')
                    args[key] = value
                for catalog_reference in obj.iter('CatalogReference'):
                    entry = OpenScenarioParser.get_catalog_entry(self.catalogs, catalog_reference)
                    if entry.tag == 'Vehicle':
                        self._extract_vehicle_information(entry, rolename, entry, args)
                    elif entry.tag == 'Pedestrian':
                        self._extract_pedestrian_information(entry, rolename, entry, args)
                    elif entry.tag == 'MiscObject':
                        self._extract_misc_information(entry, rolename, entry, args)
                    else:
                        self.logger.error(' A CatalogReference specifies a reference that is not an Entity. Skipping...')
                for vehicle in obj.iter('Vehicle'):
                    self._extract_vehicle_information(obj, rolename, vehicle, args)
                for pedestrian in obj.iter('Pedestrian'):
                    self._extract_pedestrian_information(obj, rolename, pedestrian, args)
                for misc in obj.iter('MiscObject'):
                    self._extract_misc_information(obj, rolename, misc, args)
        all_actor_transforms_set = False
        while not all_actor_transforms_set:
            all_actor_transforms_set = True
            for actor in self.other_actors + self.ego_vehicles:
                if actor.transform is None:
                    try:
                        actor.transform = self._get_actor_transform(actor.rolename)
                    except AttributeError as e:
                        if "Object '" in str(e):
                            ref_actor_rolename = str(e).split("'")[1]
                            for ref_actor in self.other_actors + self.ego_vehicles:
                                if ref_actor.rolename == ref_actor_rolename:
                                    if ref_actor.transform is not None:
                                        raise e
                                    break
                    if actor.transform is None:
                        all_actor_transforms_set = False

    def _extract_vehicle_information(self, obj, rolename, vehicle, args):
        """
        Helper function to _set_actor_information for getting vehicle information from XML tree
        """
        color = None
        model = vehicle.attrib.get('name', 'vehicle.*')
        category = vehicle.attrib.get('vehicleCategory', 'car')
        ego_vehicle = False
        for prop in obj.iter('Property'):
            if prop.get('name', '') == 'type':
                ego_vehicle = prop.get('value') == 'ego_vehicle'
            if prop.get('name', '') == 'color':
                color = prop.get('value')
        speed = self._get_actor_speed(rolename)
        new_actor = ActorConfigurationData(model, None, rolename, speed, color=color, category=category, args=args)
        if ego_vehicle:
            self.ego_vehicles.append(new_actor)
        else:
            self.other_actors.append(new_actor)

    def _extract_pedestrian_information(self, obj, rolename, pedestrian, args):
        """
        Helper function to _set_actor_information for getting pedestrian information from XML tree
        """
        model = pedestrian.attrib.get('model', 'walker.*')
        speed = self._get_actor_speed(rolename)
        new_actor = ActorConfigurationData(model, None, rolename, speed, category='pedestrian', args=args)
        self.other_actors.append(new_actor)

    def _extract_misc_information(self, obj, rolename, misc, args):
        """
        Helper function to _set_actor_information for getting vehicle information from XML tree
        """
        category = misc.attrib.get('miscObjectCategory')
        if category == 'barrier':
            model = 'static.prop.streetbarrier'
        elif category == 'guardRail':
            model = 'static.prop.chainbarrier'
        else:
            model = misc.attrib.get('name')
        new_actor = ActorConfigurationData(model, None, rolename, category='misc', args=args)
        self.other_actors.append(new_actor)

    def _get_actor_transform(self, actor_name):
        """
        Get the initial actor transform provided by the Init section

        Note: - The OpenScenario specification allows multiple definitions. We use the _first_ one
              - The OpenScenario specification allows different ways of specifying a position.
                We currently support the specification with absolute world coordinates and the relative positions
                RelativeWorld, RelativeObject and RelativeLane
              - When using relative positions the relevant reference point (e.g. transform of another actor)
                should be defined before!
        """
        actor_transform = carla.Transform()
        actor_found = False
        for private_action in self.init.iter('Private'):
            if private_action.attrib.get('entityRef', None) == actor_name:
                if actor_found:
                    self.logger.warning(" Warning: The actor '%s' was already assigned an initial position. Overwriting pose!", actor_name)
                actor_found = True
                for position in private_action.iter('Position'):
                    transform = OpenScenarioParser.convert_position_to_transform(position, actor_list=self.other_actors + self.ego_vehicles)
                    if transform:
                        actor_transform = transform
        if not actor_found:
            self.logger.warning(" Warning: The actor '%s' was not assigned an initial position. Using (0,0,0)", actor_name)
        return actor_transform

    def _get_actor_speed(self, actor_name):
        """
        Get the initial actor speed provided by the Init section
        """
        actor_speed = 0
        actor_found = False
        for private_action in self.init.iter('Private'):
            if private_action.attrib.get('entityRef', None) == actor_name:
                if actor_found:
                    self.logger.warning(" Warning: The actor '%s' was already assigned an initial speed. Overwriting inital speed!", actor_name)
                actor_found = True
                for longitudinal_action in private_action.iter('LongitudinalAction'):
                    for speed in longitudinal_action.iter('SpeedAction'):
                        for target in speed.iter('SpeedActionTarget'):
                            for absolute in target.iter('AbsoluteTargetSpeed'):
                                speed = float(absolute.attrib.get('value', 0))
                                if speed >= 0:
                                    actor_speed = speed
                                else:
                                    raise AttributeError('Warning: Speed value of actor {} must be positive. Speed set to 0.'.format(actor_name))
        return actor_speed

    def _validate_result(self):
        """
        Check that the current scenario configuration is valid
        """
        if not self.name:
            raise AttributeError('No scenario name found')
        if not self.town:
            raise AttributeError('CARLA level not defined')
        if not self.ego_vehicles:
            self.logger.warning(' No ego vehicles defined in scenario')

def _validate_openscenario_configuration(self):
    """
        Validate the given OpenSCENARIO config against the 0.9.1 XSD

        Note: This will throw if the config is not valid. But this is fine here.
        """
    xsd_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../openscenario/OpenSCENARIO.xsd')
    xsd = xmlschema.XMLSchema(xsd_file)
    xsd.validate(self.xml_tree)

def _validate_openscenario_catalog_configuration(self, catalog_xml_tree):
    """
        Validate the given OpenSCENARIO catalog config against the 0.9.1 XSD

        Note: This will throw if the catalog config is not valid. But this is fine here.
        """
    xsd_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../openscenario/OpenSCENARIO.xsd')
    xsd = xmlschema.XMLSchema(xsd_file)
    xsd.validate(catalog_xml_tree)

def _parse_openscenario_configuration(self):
    """
        Parse the given OpenSCENARIO config file, set and validate parameters
        """
    OpenScenarioParser.set_osc_filepath(os.path.dirname(self._filename))
    self._check_version()
    self._load_catalogs()
    self._set_scenario_name()
    self._set_carla_town()
    self._set_actor_information()
    self._validate_result()

class HumanInterface(object):
    """
    Class to control a vehicle manually for debugging purposes
    """

    def __init__(self, parent):
        self.quit = False
        self._parent = parent
        self._width = 800
        self._height = 600
        self._throttle_delta = 0.05
        self._steering_delta = 0.01
        self._surface = None
        pygame.init()
        pygame.font.init()
        self._clock = pygame.time.Clock()
        self._display = pygame.display.set_mode((self._width, self._height), pygame.HWSURFACE | pygame.DOUBLEBUF)
        pygame.display.set_caption('Human Agent')

    def run(self):
        """
        Run the GUI
        """
        while not self._parent.agent_engaged and (not self.quit):
            time.sleep(0.5)
        controller = KeyboardControl()
        while not self.quit:
            self._clock.tick_busy_loop(20)
            controller.parse_events(self._parent.current_control, self._clock)
            pygame.event.pump()
            input_data = self._parent.sensor_interface.get_data()
            image_center = input_data['Center'][1][:, :, -2::-1]
            image_left = input_data['Left'][1][:, :, -2::-1]
            image_right = input_data['Right'][1][:, :, -2::-1]
            image_rear = input_data['Rear'][1][:, :, -2::-1]
            top_row = np.hstack((image_left, image_center, image_right))
            bottom_row = np.hstack((0 * image_rear, image_rear, 0 * image_rear))
            comp_image = np.vstack((top_row, bottom_row))
            image_rescaled = cv2.resize(comp_image, dsize=(self._width, self._height), interpolation=cv2.INTER_CUBIC)
            self._surface = pygame.surfarray.make_surface(image_rescaled.swapaxes(0, 1))
            if self._surface is not None:
                self._display.blit(self._surface, (0, 0))
            pygame.display.flip()
        pygame.quit()

def __init__(self, parent):
    self.quit = False
    self._parent = parent
    self._width = 800
    self._height = 600
    self._throttle_delta = 0.05
    self._steering_delta = 0.01
    self._surface = None
    pygame.init()
    pygame.font.init()
    self._clock = pygame.time.Clock()
    self._display = pygame.display.set_mode((self._width, self._height), pygame.HWSURFACE | pygame.DOUBLEBUF)
    pygame.display.set_caption('Human Agent')

def run(self):
    """
        Run the GUI
        """
    while not self._parent.agent_engaged and (not self.quit):
        time.sleep(0.5)
    controller = KeyboardControl()
    while not self.quit:
        self._clock.tick_busy_loop(20)
        controller.parse_events(self._parent.current_control, self._clock)
        pygame.event.pump()
        input_data = self._parent.sensor_interface.get_data()
        image_center = input_data['Center'][1][:, :, -2::-1]
        image_left = input_data['Left'][1][:, :, -2::-1]
        image_right = input_data['Right'][1][:, :, -2::-1]
        image_rear = input_data['Rear'][1][:, :, -2::-1]
        top_row = np.hstack((image_left, image_center, image_right))
        bottom_row = np.hstack((0 * image_rear, image_rear, 0 * image_rear))
        comp_image = np.vstack((top_row, bottom_row))
        image_rescaled = cv2.resize(comp_image, dsize=(self._width, self._height), interpolation=cv2.INTER_CUBIC)
        self._surface = pygame.surfarray.make_surface(image_rescaled.swapaxes(0, 1))
        if self._surface is not None:
            self._display.blit(self._surface, (0, 0))
        pygame.display.flip()
    pygame.quit()

class KeyboardControl(object):
    """
    Keyboard control for the human agent
    """

    def __init__(self):
        """
        Init
        """
        self._control = carla.VehicleControl()
        self._steer_cache = 0.0

    def parse_events(self, control, clock):
        """
        Parse the keyboard events and set the vehicle controls accordingly
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            self._parse_vehicle_keys(pygame.key.get_pressed(), clock.get_time())
            control.steer = self._control.steer
            control.throttle = self._control.throttle
            control.brake = self._control.brake
            control.hand_brake = self._control.hand_brake

    def _parse_vehicle_keys(self, keys, milliseconds):
        """
        Calculate new vehicle controls based on input keys
        """
        self._control.throttle = 0.6 if keys[K_UP] or keys[K_w] else 0.0
        steer_increment = 15.0 * 0.0005 * milliseconds
        if keys[K_LEFT] or keys[K_a]:
            self._steer_cache -= steer_increment
        elif keys[K_RIGHT] or keys[K_d]:
            self._steer_cache += steer_increment
        else:
            self._steer_cache = 0.0
        self._steer_cache = min(0.95, max(-0.95, self._steer_cache))
        self._control.steer = round(self._steer_cache, 1)
        self._control.brake = 1.0 if keys[K_DOWN] or keys[K_s] else 0.0
        self._control.hand_brake = keys[K_SPACE]

def _parse_vehicle_keys(self, keys, milliseconds):
    """
        Calculate new vehicle controls based on input keys
        """
    self._control.throttle = 0.6 if keys[K_UP] or keys[K_w] else 0.0
    steer_increment = 15.0 * 0.0005 * milliseconds
    if keys[K_LEFT] or keys[K_a]:
        self._steer_cache -= steer_increment
    elif keys[K_RIGHT] or keys[K_d]:
        self._steer_cache += steer_increment
    else:
        self._steer_cache = 0.0
    self._steer_cache = min(0.95, max(-0.95, self._steer_cache))
    self._control.steer = round(self._steer_cache, 1)
    self._control.brake = 1.0 if keys[K_DOWN] or keys[K_s] else 0.0
    self._control.hand_brake = keys[K_SPACE]

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

class MetricsParser(object):
    """
    Class used to parse the CARLA recorder into readable information
    """

    def __init__(self, recorder_info):
        self.recorder_info = recorder_info
        self.frame_list = None
        self.frame_row = None
        self.i = 0

    def get_row_elements(self, indent_num, split_string):
        """
        returns a list with the elements of the row
        """
        return self.frame_row[indent_num:].split(split_string)

    def next_row(self):
        """
        Gets the next row of the recorder
        """
        self.i += 1
        self.frame_row = self.frame_list[self.i]

    def parse_recorder_info(self):
        """
        Parses the recorder into readable information.

        Args:
            recorder_info (str): string given by the recorder
        """
        recorder_list = self.recorder_info.split('Frame')
        header = recorder_list[0].split('\n')
        sim_map = header[1][5:]
        sim_date = header[2][6:]
        annex = recorder_list[-1].split('\n')
        sim_frames = int(annex[0][3:])
        sim_duration = float(annex[1][10:-8])
        recorder_list = recorder_list[1:-1]
        simulation_info = {'map': sim_map, 'date:': sim_date, 'total_frames': sim_frames, 'duration': sim_duration}
        actors_info = {}
        frames_info = []
        for frame in recorder_list:
            self.frame_list = frame.split('\n')
            frame_info = self.frame_list[0].split(' ')
            frame_number = int(frame_info[1])
            frame_time = float(frame_info[3])
            try:
                prev_frame = frames_info[frame_number - 2]
                prev_time = prev_frame['frame']['elapsed_time']
                delta_time = round(frame_time - prev_time, 6)
            except IndexError:
                delta_time = 0
            frame_state = {'frame': {'elapsed_time': frame_time, 'delta_time': delta_time, 'platform_time': None}, 'actors': {}, 'events': {'scene_lights': {}, 'physics_control': {}, 'traffic_light_state_time': {}, 'collisions': {}}}
            self.i = 0
            self.next_row()
            while self.frame_row.startswith(' Create') or self.frame_row.startswith('  '):
                if self.frame_row.startswith(' Create'):
                    elements = self.get_row_elements(1, ' ')
                    actor_id = int(elements[1][:-1])
                    actor = parse_actor(elements)
                    actors_info.update({actor_id: actor})
                    actors_info[actor_id].update({'created': frame_number})
                else:
                    elements = self.get_row_elements(2, ' = ')
                    actors_info[actor_id].update({elements[0]: elements[1]})
                self.next_row()
            while self.frame_row.startswith(' Destroy'):
                elements = self.get_row_elements(1, ' ')
                actor_id = int(elements[1])
                actors_info[actor_id].update({'destroyed': frame_number})
                self.next_row()
            while self.frame_row.startswith(' Collision'):
                elements = self.get_row_elements(1, ' ')
                actor_id = int(elements[4])
                other_id = int(elements[-1])
                if actor_id not in frame_state['events']['collisions']:
                    frame_state['events']['collisions'][actor_id] = [other_id]
                else:
                    collisions = frame_state['events']['collisions'][actor_id]
                    collisions.append(other_id)
                    frame_state['events']['collisions'].update({actor_id: collisions})
                self.next_row()
            while self.frame_row.startswith(' Parenting'):
                elements = self.get_row_elements(1, ' ')
                actor_id = int(elements[1])
                parent_id = int(elements[3])
                actors_info[actor_id].update({'parent': parent_id})
                self.next_row()
            if self.frame_row.startswith(' Positions'):
                self.next_row()
                while self.frame_row.startswith('  '):
                    elements = self.get_row_elements(2, ' ')
                    actor_id = int(elements[1])
                    transform = parse_transform(elements)
                    frame_state['actors'].update({actor_id: {'transform': transform}})
                    self.next_row()
            if self.frame_row.startswith(' State traffic lights'):
                self.next_row()
                while self.frame_row.startswith('  '):
                    elements = self.get_row_elements(2, ' ')
                    actor_id = int(elements[1])
                    traffic_light = parse_traffic_light(elements)
                    frame_state['actors'].update({actor_id: traffic_light})
                    self.next_row()
            if self.frame_row.startswith(' Vehicle animations'):
                self.next_row()
                while self.frame_row.startswith('  '):
                    elements = self.get_row_elements(2, ' ')
                    actor_id = int(elements[1])
                    control = parse_control(elements)
                    frame_state['actors'][actor_id].update({'control': control})
                    self.next_row()
            if self.frame_row.startswith(' Walker animations'):
                self.next_row()
                while self.frame_row.startswith('  '):
                    elements = self.get_row_elements(2, ' ')
                    actor_id = int(elements[1])
                    frame_state['actors'][actor_id].update({'speed': elements[3]})
                    self.next_row()
            if self.frame_row.startswith(' Vehicle light animations'):
                self.next_row()
                while self.frame_row.startswith('  '):
                    elements = self.get_row_elements(2, ' ')
                    actor_id = int(elements[1])
                    lights = parse_vehicle_lights(elements)
                    frame_state['actors'][actor_id].update({'lights': lights})
                    self.next_row()
            if self.frame_row.startswith(' Scene light changes'):
                self.next_row()
                while self.frame_row.startswith('  '):
                    elements = self.get_row_elements(2, ' ')
                    actor_id = int(elements[1])
                    scene_light = parse_scene_lights(elements)
                    frame_state['events']['scene_lights'].update({actor_id: scene_light})
                    self.next_row()
            if self.frame_row.startswith(' Dynamic actors'):
                self.next_row()
                while self.frame_row.startswith('  '):
                    elements = self.get_row_elements(2, ' ')
                    actor_id = int(elements[1])
                    velocity = parse_velocity(elements)
                    frame_state['actors'][actor_id].update({'velocity': velocity})
                    angular_v = parse_angular_velocity(elements)
                    frame_state['actors'][actor_id].update({'angular_velocity': angular_v})
                    if delta_time == 0:
                        acceleration = carla.Vector3D(0, 0, 0)
                    else:
                        prev_velocity = frame_state['actors'][actor_id]['velocity']
                        acceleration = (velocity - prev_velocity) / delta_time
                    frame_state['actors'][actor_id].update({'acceleration': acceleration})
                    self.next_row()
            if self.frame_row.startswith(' Actor bounding boxes'):
                self.next_row()
                while self.frame_row.startswith('  '):
                    elements = self.get_row_elements(2, ' ')
                    actor_id = int(elements[1])
                    bbox = parse_bounding_box(elements)
                    actors_info[actor_id].update({'bounding_box': bbox})
                    self.next_row()
            if self.frame_row.startswith(' Actor trigger volumes'):
                self.next_row()
                while self.frame_row.startswith('  '):
                    elements = self.get_row_elements(2, ' ')
                    actor_id = int(elements[1])
                    trigvol = parse_bounding_box(elements)
                    actors_info[actor_id].update({'trigger_volume': trigvol})
                    self.next_row()
            if self.frame_row.startswith(' Current platform time'):
                elements = self.get_row_elements(1, ' ')
                platform_time = float(elements[-1])
                frame_state['frame']['platform_time'] = platform_time
                self.next_row()
            if self.frame_row.startswith(' Physics Control'):
                self.next_row()
                actor_id = None
                while self.frame_row.startswith('  '):
                    elements = self.get_row_elements(2, ' ')
                    actor_id = int(elements[1])
                    physics_control = carla.VehiclePhysicsControl()
                    self.next_row()
                    forward_gears = []
                    wheels = []
                    while self.frame_row.startswith('   '):
                        if self.frame_row.startswith('    '):
                            elements = self.get_row_elements(4, ' ')
                            if elements[0] == 'gear':
                                forward_gears.append(parse_gears_control(elements))
                            elif elements[0] == 'wheel':
                                wheels.append(parse_wheels_control(elements))
                        else:
                            elements = self.get_row_elements(3, ' = ')
                            name = elements[0]
                            if name == 'center_of_mass':
                                values = elements[1].split(' ')
                                value = carla.Vector3D(float(values[0][1:-1]), float(values[1][:-1]), float(values[2][:-1]))
                                setattr(physics_control, name, value)
                            elif name == 'torque_curve' or name == 'steering_curve':
                                values = elements[1].split(' ')
                                value = parse_vector_list(values)
                                setattr(physics_control, name, value)
                            elif name == 'use_gear_auto_box':
                                name = 'use_gear_autobox'
                                value = True if elements[1] == 'true' else False
                                setattr(physics_control, name, value)
                            elif 'forward_gears' in name or 'wheels' in name:
                                pass
                            else:
                                name = name.lower()
                                value = float(elements[1])
                                setattr(physics_control, name, value)
                        self.next_row()
                    setattr(physics_control, 'forward_gears', forward_gears)
                    setattr(physics_control, 'wheels', wheels)
                    frame_state['events']['physics_control'].update({actor_id: physics_control})
            if self.frame_row.startswith(' Traffic Light time events'):
                self.next_row()
                while self.frame_row.startswith('  '):
                    elements = self.get_row_elements(2, ' ')
                    actor_id = int(elements[1])
                    state_times = parse_state_times(elements)
                    frame_state['events']['traffic_light_state_time'].update({actor_id: state_times})
                    self.next_row()
            frames_info.append(frame_state)
        return (simulation_info, actors_info, frames_info)

def get_row_elements(self, indent_num, split_string):
    """
        returns a list with the elements of the row
        """
    return self.frame_row[indent_num:].split(split_string)

def parse_recorder_info(self):
    """
        Parses the recorder into readable information.

        Args:
            recorder_info (str): string given by the recorder
        """
    recorder_list = self.recorder_info.split('Frame')
    header = recorder_list[0].split('\n')
    sim_map = header[1][5:]
    sim_date = header[2][6:]
    annex = recorder_list[-1].split('\n')
    sim_frames = int(annex[0][3:])
    sim_duration = float(annex[1][10:-8])
    recorder_list = recorder_list[1:-1]
    simulation_info = {'map': sim_map, 'date:': sim_date, 'total_frames': sim_frames, 'duration': sim_duration}
    actors_info = {}
    frames_info = []
    for frame in recorder_list:
        self.frame_list = frame.split('\n')
        frame_info = self.frame_list[0].split(' ')
        frame_number = int(frame_info[1])
        frame_time = float(frame_info[3])
        try:
            prev_frame = frames_info[frame_number - 2]
            prev_time = prev_frame['frame']['elapsed_time']
            delta_time = round(frame_time - prev_time, 6)
        except IndexError:
            delta_time = 0
        frame_state = {'frame': {'elapsed_time': frame_time, 'delta_time': delta_time, 'platform_time': None}, 'actors': {}, 'events': {'scene_lights': {}, 'physics_control': {}, 'traffic_light_state_time': {}, 'collisions': {}}}
        self.i = 0
        self.next_row()
        while self.frame_row.startswith(' Create') or self.frame_row.startswith('  '):
            if self.frame_row.startswith(' Create'):
                elements = self.get_row_elements(1, ' ')
                actor_id = int(elements[1][:-1])
                actor = parse_actor(elements)
                actors_info.update({actor_id: actor})
                actors_info[actor_id].update({'created': frame_number})
            else:
                elements = self.get_row_elements(2, ' = ')
                actors_info[actor_id].update({elements[0]: elements[1]})
            self.next_row()
        while self.frame_row.startswith(' Destroy'):
            elements = self.get_row_elements(1, ' ')
            actor_id = int(elements[1])
            actors_info[actor_id].update({'destroyed': frame_number})
            self.next_row()
        while self.frame_row.startswith(' Collision'):
            elements = self.get_row_elements(1, ' ')
            actor_id = int(elements[4])
            other_id = int(elements[-1])
            if actor_id not in frame_state['events']['collisions']:
                frame_state['events']['collisions'][actor_id] = [other_id]
            else:
                collisions = frame_state['events']['collisions'][actor_id]
                collisions.append(other_id)
                frame_state['events']['collisions'].update({actor_id: collisions})
            self.next_row()
        while self.frame_row.startswith(' Parenting'):
            elements = self.get_row_elements(1, ' ')
            actor_id = int(elements[1])
            parent_id = int(elements[3])
            actors_info[actor_id].update({'parent': parent_id})
            self.next_row()
        if self.frame_row.startswith(' Positions'):
            self.next_row()
            while self.frame_row.startswith('  '):
                elements = self.get_row_elements(2, ' ')
                actor_id = int(elements[1])
                transform = parse_transform(elements)
                frame_state['actors'].update({actor_id: {'transform': transform}})
                self.next_row()
        if self.frame_row.startswith(' State traffic lights'):
            self.next_row()
            while self.frame_row.startswith('  '):
                elements = self.get_row_elements(2, ' ')
                actor_id = int(elements[1])
                traffic_light = parse_traffic_light(elements)
                frame_state['actors'].update({actor_id: traffic_light})
                self.next_row()
        if self.frame_row.startswith(' Vehicle animations'):
            self.next_row()
            while self.frame_row.startswith('  '):
                elements = self.get_row_elements(2, ' ')
                actor_id = int(elements[1])
                control = parse_control(elements)
                frame_state['actors'][actor_id].update({'control': control})
                self.next_row()
        if self.frame_row.startswith(' Walker animations'):
            self.next_row()
            while self.frame_row.startswith('  '):
                elements = self.get_row_elements(2, ' ')
                actor_id = int(elements[1])
                frame_state['actors'][actor_id].update({'speed': elements[3]})
                self.next_row()
        if self.frame_row.startswith(' Vehicle light animations'):
            self.next_row()
            while self.frame_row.startswith('  '):
                elements = self.get_row_elements(2, ' ')
                actor_id = int(elements[1])
                lights = parse_vehicle_lights(elements)
                frame_state['actors'][actor_id].update({'lights': lights})
                self.next_row()
        if self.frame_row.startswith(' Scene light changes'):
            self.next_row()
            while self.frame_row.startswith('  '):
                elements = self.get_row_elements(2, ' ')
                actor_id = int(elements[1])
                scene_light = parse_scene_lights(elements)
                frame_state['events']['scene_lights'].update({actor_id: scene_light})
                self.next_row()
        if self.frame_row.startswith(' Dynamic actors'):
            self.next_row()
            while self.frame_row.startswith('  '):
                elements = self.get_row_elements(2, ' ')
                actor_id = int(elements[1])
                velocity = parse_velocity(elements)
                frame_state['actors'][actor_id].update({'velocity': velocity})
                angular_v = parse_angular_velocity(elements)
                frame_state['actors'][actor_id].update({'angular_velocity': angular_v})
                if delta_time == 0:
                    acceleration = carla.Vector3D(0, 0, 0)
                else:
                    prev_velocity = frame_state['actors'][actor_id]['velocity']
                    acceleration = (velocity - prev_velocity) / delta_time
                frame_state['actors'][actor_id].update({'acceleration': acceleration})
                self.next_row()
        if self.frame_row.startswith(' Actor bounding boxes'):
            self.next_row()
            while self.frame_row.startswith('  '):
                elements = self.get_row_elements(2, ' ')
                actor_id = int(elements[1])
                bbox = parse_bounding_box(elements)
                actors_info[actor_id].update({'bounding_box': bbox})
                self.next_row()
        if self.frame_row.startswith(' Actor trigger volumes'):
            self.next_row()
            while self.frame_row.startswith('  '):
                elements = self.get_row_elements(2, ' ')
                actor_id = int(elements[1])
                trigvol = parse_bounding_box(elements)
                actors_info[actor_id].update({'trigger_volume': trigvol})
                self.next_row()
        if self.frame_row.startswith(' Current platform time'):
            elements = self.get_row_elements(1, ' ')
            platform_time = float(elements[-1])
            frame_state['frame']['platform_time'] = platform_time
            self.next_row()
        if self.frame_row.startswith(' Physics Control'):
            self.next_row()
            actor_id = None
            while self.frame_row.startswith('  '):
                elements = self.get_row_elements(2, ' ')
                actor_id = int(elements[1])
                physics_control = carla.VehiclePhysicsControl()
                self.next_row()
                forward_gears = []
                wheels = []
                while self.frame_row.startswith('   '):
                    if self.frame_row.startswith('    '):
                        elements = self.get_row_elements(4, ' ')
                        if elements[0] == 'gear':
                            forward_gears.append(parse_gears_control(elements))
                        elif elements[0] == 'wheel':
                            wheels.append(parse_wheels_control(elements))
                    else:
                        elements = self.get_row_elements(3, ' = ')
                        name = elements[0]
                        if name == 'center_of_mass':
                            values = elements[1].split(' ')
                            value = carla.Vector3D(float(values[0][1:-1]), float(values[1][:-1]), float(values[2][:-1]))
                            setattr(physics_control, name, value)
                        elif name == 'torque_curve' or name == 'steering_curve':
                            values = elements[1].split(' ')
                            value = parse_vector_list(values)
                            setattr(physics_control, name, value)
                        elif name == 'use_gear_auto_box':
                            name = 'use_gear_autobox'
                            value = True if elements[1] == 'true' else False
                            setattr(physics_control, name, value)
                        elif 'forward_gears' in name or 'wheels' in name:
                            pass
                        else:
                            name = name.lower()
                            value = float(elements[1])
                            setattr(physics_control, name, value)
                    self.next_row()
                setattr(physics_control, 'forward_gears', forward_gears)
                setattr(physics_control, 'wheels', wheels)
                frame_state['events']['physics_control'].update({actor_id: physics_control})
        if self.frame_row.startswith(' Traffic Light time events'):
            self.next_row()
            while self.frame_row.startswith('  '):
                elements = self.get_row_elements(2, ' ')
                actor_id = int(elements[1])
                state_times = parse_state_times(elements)
                frame_state['events']['traffic_light_state_time'].update({actor_id: state_times})
                self.next_row()
        frames_info.append(frame_state)
    return (simulation_info, actors_info, frames_info)

def getPixel(coord, town_name):
    x, y = coord
    pix_x = int((x - reference_coord[town_name][0]) * scale[town_name][0])
    pix_y = int(-(y - reference_coord[town_name][1]) * scale[town_name][1])
    if town_name == 'Town03' or town_name == 'Town04':
        pix_y = int(-(-y - reference_coord[town_name][1]) * scale[town_name][1])
    if town_name == 'Town01' or town_name == 'Town02' or town_name == 'Town06':
        pix_x = abs(pix_x)
        pix_y = abs(pix_y)
    return (pix_x, pix_y)

class MapImage(object):
    """
    Class encharged of rendering a 2D image from top view of a carla world. Please note that a cache system is used, so if the OpenDrive content
    of a Carla town has not changed, it will read and use the stored image if it was rendered in a previous execution
    """

    def __init__(self, carla_map_name, pixels_per_meter, map_dir, visualize=True):
        """
        Renders the map image generated based on the world, its map and additional flags that provide extra information about the road network
        """
        self._pixels_per_meter = pixels_per_meter
        self.scale = 1.0
        self.visualize = visualize
        self.map_dir = map_dir
        self.carla_map_name = carla_map_name
        with open(os.path.join(self.map_dir, f'{carla_map_name}_details.json'), 'r') as f:
            data_ = json.load(f)
        self._world_offset = data_['world_offset']
        self.viz_surface = None
        if self.visualize:
            filename = carla_map_name + '_.tga'
            self.viz_surface = pygame.image.load(os.path.join(self.map_dir, filename))

    def create_crop(self, surface, point_original, path_=None, np_array=False):
        point_ = self.world_to_pixel(point_original.location)
        temp_surface = pygame.Surface.copy(surface)
        if 'visualize' in path_:
            color_ = pygame.Color(0, 255, 0)
            self.draw_queried_points(temp_surface, self.world_to_pixel, [point_original], colors=[color_])
        rz = pygame.transform.rotozoom
        scaled_original_size = 500 * (1.0 / 0.2)
        hero_map_surface = pygame.Surface((scaled_original_size, scaled_original_size))
        angle = point_original.theta + np.pi / 2
        offset = [0, 0]
        hero_location_screen = point_
        hero_front = carla.Location(x=np.cos(point_original.theta), y=np.sin(point_original.theta))
        offset[0] += hero_location_screen[0] - hero_map_surface.get_width() / 2
        offset[0] += hero_front.x * PIXELS_AHEAD_VEHICLE
        offset[1] += hero_location_screen[1] - hero_map_surface.get_height() / 2
        offset[1] += hero_front.y * PIXELS_AHEAD_VEHICLE
        forward_pt = [hero_location_screen[0] + hero_front.x * PIXELS_AHEAD_VEHICLE, hero_location_screen[1] + hero_front.y * PIXELS_AHEAD_VEHICLE]
        if 'visualize' in path_:
            self.draw_points(temp_surface, forward_pt)
        pt_center = [forward_pt[0] - offset[0], forward_pt[1] - offset[1]]
        hero_map_surface.blit(temp_surface, (-offset[0], -offset[1]))
        rotated_map_surface = rz(hero_map_surface, np.degrees(angle), 1)
        top_left_in_pixels_final = [pt_center[0] - 128, pt_center[1]]
        center = (scaled_original_size / 2, scaled_original_size / 2)
        rotation_map_pivot = rotated_map_surface.get_rect(center=center)
        window_map_surface = pygame.Surface((scaled_original_size, scaled_original_size))
        window_map_surface.blit(rotated_map_surface, rotation_map_pivot)
        final_surface = pygame.Surface((256, 256), flags=pygame.HWSURFACE | pygame.DOUBLEBUF)
        final_surface.blit(window_map_surface, (0, 0), (top_left_in_pixels_final[0], top_left_in_pixels_final[1], 256, 256))
        if path_:
            pygame.image.save(final_surface, path_ + '.tga')
        if np_array:
            np_surface = pygame.surfarray.array3d(final_surface)
            return np_surface
        else:
            return final_surface

    def create_semlabels_offline(self, surface, points_, paths, suffix, save_dir):
        for i, (point_original, path_) in enumerate(zip(points_, paths)):
            crp_dir = os.path.join(save_dir, os.path.dirname(path_), suffix)
            if not os.path.exists(crp_dir):
                os.makedirs(crp_dir)
            _, crop_name = os.path.split(path_)
            crop_pth = os.path.join(crp_dir, crop_name)
            self.create_crop(surface, point_original, path_=crop_pth)

    def plot_points_nocrop_xml(self, surface, points_, filename, save_dir):
        temp_surface = pygame.Surface.copy(surface)
        rgbs_ = []
        for j, pth_ in enumerate(points_):
            print(f' Plotted route {j + 1}/{len(points_)}')
            rgb = (random.uniform(0, 1), random.uniform(0, 1), random.uniform(0, 1))
            rgbs_.append(rgb)
            color_pg = (int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))
            for i, point_original in enumerate(pth_[:-1]):
                sp_, ep_ = (pth_[i], pth_[i + 1])
                self.draw_queried_points(temp_surface, self.world_to_pixel, [point_original], colors=[color_pg])
                color_white = pygame.Color(255, 255, 255)
                pygame.draw.lines(temp_surface, color_white, False, [self.world_to_pixel(x.location) for x in [sp_, ep_]], 4)
        pygame.image.save_extended(temp_surface, os.path.join(save_dir, f'{filename}.png'))

    def plot_points_nocrop_json(self, surface, points_, filename, save_dir):
        temp_surface = pygame.Surface.copy(surface)
        rgbs_ = []
        for j, pth_ in enumerate(points_):
            rgb = (random.uniform(0, 1), random.uniform(0, 1), random.uniform(0, 1))
            rgbs_.append(rgb)
            color_pg = (int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))
            for i, point_original in enumerate(pth_):
                self.draw_queried_points(temp_surface, self.world_to_pixel, [point_original['ego']], colors=[color_pg])
        pygame.image.save_extended(temp_surface, os.path.join(save_dir, f'{filename}.png'))

    def draw_points(self, surface, transform, color=None):
        """ Draws an arrow with a specified color given a transform"""
        end = transform
        start = end
        color_tmp = [int(255) for c_ in range(3)] if not color else color
        color = pygame.Color(*color_tmp) if color is None else color
        pygame.draw.circle(surface, color, start, 5)

    def draw_queried_points(self, map_surface, world_to_pixel, points=[], colors=[]):

        def draw_points_local(surface, transform, color=None):
            """ Draws an arrow with a specified color given a transform"""
            start = transform.location
            pygame.draw.circle(surface, color, world_to_pixel(start), 18)

        def draw_arrow(surface, transform, color=pygame.Color(193, 125, 17)):
            """ Draws an arrow with a specified color given a transform"""
            begin = carla.Location(x=transform.location.x, y=transform.location.y)
            angle = math.radians(transform.theta)
            end = begin + carla.Location(x=math.cos(angle), y=math.sin(angle))
            forward = carla.Location(x=np.cos(angle), y=np.sin(angle))
            end = carla.Location(x=transform.location.x, y=transform.location.y)
            start = end + forward
            pygame.draw.lines(surface, color, False, [world_to_pixel(x) for x in [start, end]], 4)
        if len(points):
            for p_, color_ in zip(points, colors):
                draw_points_local(map_surface, p_, color=color_)
                draw_arrow(map_surface, p_)

    def world_to_pixel(self, location, offset=(0, 0)):
        """Converts the world coordinates to pixel coordinates"""
        x = self.scale * self._pixels_per_meter * (location.x - self._world_offset[0])
        y = self.scale * self._pixels_per_meter * (location.y - self._world_offset[1])
        return [int(x - offset[0]), int(y - offset[1])]

    def world_to_pixel_width(self, width):
        """Converts the world units to pixel units"""
        return int(self.scale * self._pixels_per_meter * width)

    def scale_map(self, scale):
        """Scales the map surface"""
        if scale != self.scale:
            self.scale = scale
            width = int(self.big_map_surface.get_width() * self.scale)
            self.surface = pygame.transform.smoothscale(self.big_map_surface, (width, width))

def create_crop(self, surface, point_original, path_=None, np_array=False):
    point_ = self.world_to_pixel(point_original.location)
    temp_surface = pygame.Surface.copy(surface)
    if 'visualize' in path_:
        color_ = pygame.Color(0, 255, 0)
        self.draw_queried_points(temp_surface, self.world_to_pixel, [point_original], colors=[color_])
    rz = pygame.transform.rotozoom
    scaled_original_size = 500 * (1.0 / 0.2)
    hero_map_surface = pygame.Surface((scaled_original_size, scaled_original_size))
    angle = point_original.theta + np.pi / 2
    offset = [0, 0]
    hero_location_screen = point_
    hero_front = carla.Location(x=np.cos(point_original.theta), y=np.sin(point_original.theta))
    offset[0] += hero_location_screen[0] - hero_map_surface.get_width() / 2
    offset[0] += hero_front.x * PIXELS_AHEAD_VEHICLE
    offset[1] += hero_location_screen[1] - hero_map_surface.get_height() / 2
    offset[1] += hero_front.y * PIXELS_AHEAD_VEHICLE
    forward_pt = [hero_location_screen[0] + hero_front.x * PIXELS_AHEAD_VEHICLE, hero_location_screen[1] + hero_front.y * PIXELS_AHEAD_VEHICLE]
    if 'visualize' in path_:
        self.draw_points(temp_surface, forward_pt)
    pt_center = [forward_pt[0] - offset[0], forward_pt[1] - offset[1]]
    hero_map_surface.blit(temp_surface, (-offset[0], -offset[1]))
    rotated_map_surface = rz(hero_map_surface, np.degrees(angle), 1)
    top_left_in_pixels_final = [pt_center[0] - 128, pt_center[1]]
    center = (scaled_original_size / 2, scaled_original_size / 2)
    rotation_map_pivot = rotated_map_surface.get_rect(center=center)
    window_map_surface = pygame.Surface((scaled_original_size, scaled_original_size))
    window_map_surface.blit(rotated_map_surface, rotation_map_pivot)
    final_surface = pygame.Surface((256, 256), flags=pygame.HWSURFACE | pygame.DOUBLEBUF)
    final_surface.blit(window_map_surface, (0, 0), (top_left_in_pixels_final[0], top_left_in_pixels_final[1], 256, 256))
    if path_:
        pygame.image.save(final_surface, path_ + '.tga')
    if np_array:
        np_surface = pygame.surfarray.array3d(final_surface)
        return np_surface
    else:
        return final_surface

def plot_points_nocrop_xml(self, surface, points_, filename, save_dir):
    temp_surface = pygame.Surface.copy(surface)
    rgbs_ = []
    for j, pth_ in enumerate(points_):
        print(f' Plotted route {j + 1}/{len(points_)}')
        rgb = (random.uniform(0, 1), random.uniform(0, 1), random.uniform(0, 1))
        rgbs_.append(rgb)
        color_pg = (int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))
        for i, point_original in enumerate(pth_[:-1]):
            sp_, ep_ = (pth_[i], pth_[i + 1])
            self.draw_queried_points(temp_surface, self.world_to_pixel, [point_original], colors=[color_pg])
            color_white = pygame.Color(255, 255, 255)
            pygame.draw.lines(temp_surface, color_white, False, [self.world_to_pixel(x.location) for x in [sp_, ep_]], 4)
    pygame.image.save_extended(temp_surface, os.path.join(save_dir, f'{filename}.png'))

def plot_points_nocrop_json(self, surface, points_, filename, save_dir):
    temp_surface = pygame.Surface.copy(surface)
    rgbs_ = []
    for j, pth_ in enumerate(points_):
        rgb = (random.uniform(0, 1), random.uniform(0, 1), random.uniform(0, 1))
        rgbs_.append(rgb)
        color_pg = (int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))
        for i, point_original in enumerate(pth_):
            self.draw_queried_points(temp_surface, self.world_to_pixel, [point_original['ego']], colors=[color_pg])
    pygame.image.save_extended(temp_surface, os.path.join(save_dir, f'{filename}.png'))

def world_to_pixel(self, location, offset=(0, 0)):
    """Converts the world coordinates to pixel coordinates"""
    x = self.scale * self._pixels_per_meter * (location.x - self._world_offset[0])
    y = self.scale * self._pixels_per_meter * (location.y - self._world_offset[1])
    return [int(x - offset[0]), int(y - offset[1])]

def world_to_pixel_width(self, width):
    """Converts the world units to pixel units"""
    return int(self.scale * self._pixels_per_meter * width)

def scale_map(self, scale):
    """Scales the map surface"""
    if scale != self.scale:
        self.scale = scale
        width = int(self.big_map_surface.get_width() * self.scale)
        self.surface = pygame.transform.smoothscale(self.big_map_surface, (width, width))

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

class ModuleManager(object):

    def __init__(self):
        self.modules = []

    def register_module(self, module):
        self.modules.append(module)

    def clear_modules(self):
        del self.modules[:]

    def tick(self, clock):
        for module in self.modules:
            module.tick(clock)

    def render(self, display, snapshot=None):
        display.fill(COLOR_ALUMINIUM_4)
        for module in self.modules:
            module.render(display, snapshot=snapshot)

    def get_module(self, name):
        for module in self.modules:
            if module.name == name:
                return module

    def start_modules(self):
        for module in self.modules:
            module.start()

def render(self, display, snapshot=None):
    display.fill(COLOR_ALUMINIUM_4)
    for module in self.modules:
        module.render(display, snapshot=snapshot)

class MapImage(object):

    def __init__(self, carla_world, carla_map, pixels_per_meter=10):
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        module_manager.clear_modules()
        pygame.init()
        display = pygame.display.set_mode((320, 320), 0, 32)
        pygame.display.flip()
        self._pixels_per_meter = pixels_per_meter
        self.scale = 1.0
        waypoints = carla_map.generate_waypoints(2)
        margin = 50
        max_x = max(waypoints, key=lambda x: x.transform.location.x).transform.location.x + margin
        max_y = max(waypoints, key=lambda x: x.transform.location.y).transform.location.y + margin
        min_x = min(waypoints, key=lambda x: x.transform.location.x).transform.location.x - margin
        min_y = min(waypoints, key=lambda x: x.transform.location.y).transform.location.y - margin
        self.width = max(max_x - min_x, max_y - min_y)
        self._world_offset = (min_x, min_y)
        width_in_pixels = int(self._pixels_per_meter * self.width)
        self.big_map_surface = pygame.Surface((width_in_pixels, width_in_pixels)).convert()
        self.big_lane_surface = pygame.Surface((width_in_pixels, width_in_pixels)).convert()
        self.draw_road_map(self.big_map_surface, self.big_lane_surface, carla_world, carla_map, self.world_to_pixel, self.world_to_pixel_width)
        self.map_surface = self.big_map_surface
        self.lane_surface = self.big_lane_surface

    def draw_road_map(self, map_surface, lane_surface, carla_world, carla_map, world_to_pixel, world_to_pixel_width):
        map_surface.fill(COLOR_BLACK)
        precision = 0.05

        def draw_lane_marking(surface, points, solid=True):
            if solid and len(points) > 1:
                pygame.draw.lines(surface, COLOR_WHITE, False, points, 2)
            else:
                broken_lines = [x for n, x in enumerate(zip(*(iter(points),) * 20)) if n % 3 == 0]
                for line in broken_lines:
                    pygame.draw.lines(surface, COLOR_WHITE, False, line, 2)

        def draw_arrow(surface, transform, color=COLOR_ALUMINIUM_2):
            transform.rotation.yaw += 180
            forward = transform.get_forward_vector()
            transform.rotation.yaw += 90
            right_dir = transform.get_forward_vector()
            start = transform.location
            end = start + 2.0 * forward
            right = start + 0.8 * forward + 0.4 * right_dir
            left = start + 0.8 * forward - 0.4 * right_dir
            pygame.draw.lines(surface, color, False, [world_to_pixel(x) for x in [start, end]], 4)
            pygame.draw.lines(surface, color, False, [world_to_pixel(x) for x in [left, start, right]], 4)

        def draw_stop(surface, font_surface, transform, color=COLOR_ALUMINIUM_2):
            waypoint = carla_map.get_waypoint(transform.location)
            angle = -waypoint.transform.rotation.yaw - 90.0
            font_surface = pygame.transform.rotate(font_surface, angle)
            pixel_pos = world_to_pixel(waypoint.transform.location)
            offset = font_surface.get_rect(center=(pixel_pos[0], pixel_pos[1]))
            surface.blit(font_surface, offset)
            forward_vector = carla.Location(waypoint.transform.get_forward_vector())
            left_vector = carla.Location(-forward_vector.y, forward_vector.x, forward_vector.z) * waypoint.lane_width / 2 * 0.7
            line = [waypoint.transform.location + forward_vector * 1.5 + left_vector, waypoint.transform.location + forward_vector * 1.5 - left_vector]
            line_pixel = [world_to_pixel(p) for p in line]
            pygame.draw.lines(surface, color, True, line_pixel, 2)

        def lateral_shift(transform, shift):
            transform.rotation.yaw += 90
            return transform.location + shift * transform.get_forward_vector()

        def does_cross_solid_line(waypoint, shift):
            w = carla_map.get_waypoint(lateral_shift(waypoint.transform, shift), project_to_road=False)
            if w is None or w.road_id != waypoint.road_id:
                return True
            else:
                return w.lane_id * waypoint.lane_id < 0 or w.lane_id == waypoint.lane_id
        topology = [x[0] for x in carla_map.get_topology()]
        topology = sorted(topology, key=lambda w: w.transform.location.z)
        for waypoint in topology:
            waypoints = [waypoint]
            nxt = waypoint.next(precision)[0]
            while nxt.road_id == waypoint.road_id:
                waypoints.append(nxt)
                nxt = nxt.next(precision)[0]
            left_marking = [lateral_shift(w.transform, -w.lane_width * 0.5) for w in waypoints]
            right_marking = [lateral_shift(w.transform, w.lane_width * 0.5) for w in waypoints]
            polygon = left_marking + [x for x in reversed(right_marking)]
            polygon = [world_to_pixel(x) for x in polygon]
            if len(polygon) > 2:
                pygame.draw.polygon(map_surface, COLOR_WHITE, polygon, 10)
                pygame.draw.polygon(map_surface, COLOR_WHITE, polygon)
            if not waypoint.is_intersection:
                sample = waypoints[int(len(waypoints) / 2)]
                draw_lane_marking(lane_surface, [world_to_pixel(x) for x in left_marking], does_cross_solid_line(sample, -sample.lane_width * 1.1))
                draw_lane_marking(lane_surface, [world_to_pixel(x) for x in right_marking], does_cross_solid_line(sample, sample.lane_width * 1.1))
        actors = carla_world.get_actors()
        stops_transform = [actor.get_transform() for actor in actors if 'stop' in actor.type_id]
        font_size = world_to_pixel_width(1)
        font = pygame.font.SysFont('Arial', font_size, True)
        font_surface = font.render('STOP', False, COLOR_ALUMINIUM_2)
        font_surface = pygame.transform.scale(font_surface, (font_surface.get_width(), font_surface.get_height() * 2))

    def world_to_pixel(self, location, offset=(0, 0)):
        x = self.scale * self._pixels_per_meter * (location.x - self._world_offset[0])
        y = self.scale * self._pixels_per_meter * (location.y - self._world_offset[1])
        return [int(x - offset[0]), int(y - offset[1])]

    def world_to_pixel_width(self, width):
        return int(self.scale * self._pixels_per_meter * width)

    def scale_map(self, scale):
        if scale != self.scale:
            self.scale = scale
            width = int(self.big_map_surface.get_width() * self.scale)
            self.surface = pygame.transform.smoothscale(self.big_map_surface, (width, width))

def __init__(self, carla_world, carla_map, pixels_per_meter=10):
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    module_manager.clear_modules()
    pygame.init()
    display = pygame.display.set_mode((320, 320), 0, 32)
    pygame.display.flip()
    self._pixels_per_meter = pixels_per_meter
    self.scale = 1.0
    waypoints = carla_map.generate_waypoints(2)
    margin = 50
    max_x = max(waypoints, key=lambda x: x.transform.location.x).transform.location.x + margin
    max_y = max(waypoints, key=lambda x: x.transform.location.y).transform.location.y + margin
    min_x = min(waypoints, key=lambda x: x.transform.location.x).transform.location.x - margin
    min_y = min(waypoints, key=lambda x: x.transform.location.y).transform.location.y - margin
    self.width = max(max_x - min_x, max_y - min_y)
    self._world_offset = (min_x, min_y)
    width_in_pixels = int(self._pixels_per_meter * self.width)
    self.big_map_surface = pygame.Surface((width_in_pixels, width_in_pixels)).convert()
    self.big_lane_surface = pygame.Surface((width_in_pixels, width_in_pixels)).convert()
    self.draw_road_map(self.big_map_surface, self.big_lane_surface, carla_world, carla_map, self.world_to_pixel, self.world_to_pixel_width)
    self.map_surface = self.big_map_surface
    self.lane_surface = self.big_lane_surface

def draw_arrow(surface, transform, color=COLOR_ALUMINIUM_2):
    transform.rotation.yaw += 180
    forward = transform.get_forward_vector()
    transform.rotation.yaw += 90
    right_dir = transform.get_forward_vector()
    start = transform.location
    end = start + 2.0 * forward
    right = start + 0.8 * forward + 0.4 * right_dir
    left = start + 0.8 * forward - 0.4 * right_dir
    pygame.draw.lines(surface, color, False, [world_to_pixel(x) for x in [start, end]], 4)
    pygame.draw.lines(surface, color, False, [world_to_pixel(x) for x in [left, start, right]], 4)

def draw_stop(surface, font_surface, transform, color=COLOR_ALUMINIUM_2):
    waypoint = carla_map.get_waypoint(transform.location)
    angle = -waypoint.transform.rotation.yaw - 90.0
    font_surface = pygame.transform.rotate(font_surface, angle)
    pixel_pos = world_to_pixel(waypoint.transform.location)
    offset = font_surface.get_rect(center=(pixel_pos[0], pixel_pos[1]))
    surface.blit(font_surface, offset)
    forward_vector = carla.Location(waypoint.transform.get_forward_vector())
    left_vector = carla.Location(-forward_vector.y, forward_vector.x, forward_vector.z) * waypoint.lane_width / 2 * 0.7
    line = [waypoint.transform.location + forward_vector * 1.5 + left_vector, waypoint.transform.location + forward_vector * 1.5 - left_vector]
    line_pixel = [world_to_pixel(p) for p in line]
    pygame.draw.lines(surface, color, True, line_pixel, 2)

def world_to_pixel(self, location, offset=(0, 0)):
    x = self.scale * self._pixels_per_meter * (location.x - self._world_offset[0])
    y = self.scale * self._pixels_per_meter * (location.y - self._world_offset[1])
    return [int(x - offset[0]), int(y - offset[1])]

def world_to_pixel_width(self, width):
    return int(self.scale * self._pixels_per_meter * width)

def scale_map(self, scale):
    if scale != self.scale:
        self.scale = scale
        width = int(self.big_map_surface.get_width() * self.scale)
        self.surface = pygame.transform.smoothscale(self.big_map_surface, (width, width))

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

def scale_image(image, scale):
    width, height = (int(image.width // scale), int(image.height // scale))
    im_resized = image.resize((width, height))
    return im_resized

def scale_image_cv2(image, scale):
    width, height = (int(image.shape[1] // scale), int(image.shape[0] // scale))
    im_resized = cv2.resize(image, (width, height))
    return im_resized

def crop_image(image, crop=(128, 640), crop_shift=0):
    """
    Scale and crop a PIL image, returning a channels-first numpy array.
    """
    width = image.width
    height = image.height
    crop_h, crop_w = crop
    start_y = height // 2 - crop_h // 2
    start_x = width // 2 - crop_w // 2
    start_x += int(crop_shift)
    image = np.asarray(image)
    cropped_image = image[start_y:start_y + crop_h, start_x:start_x + crop_w]
    cropped_image = np.transpose(cropped_image, (2, 0, 1))
    return cropped_image

def scale_seg(image, scale):
    width, height = (int(image.shape[1] / scale), int(image.shape[0] / scale))
    if scale != 1:
        im_resized = cv2.resize(image, (width, height), interpolation=cv2.INTER_NEAREST)
    else:
        im_resized = image
    return im_resized

def crop_seg(image, crop=(128, 640), crop_shift=0):
    """
    Scale and crop a seg image, returning a channels-first numpy array.
    """
    width = image.shape[1]
    height = image.shape[0]
    crop_h, crop_w = crop
    start_y = height // 2 - crop_h // 2
    start_x = width // 2 - crop_w // 2
    start_x += int(crop_shift)
    cropped_image = image[start_y:start_y + crop_h, start_x:start_x + crop_w]
    return cropped_image

