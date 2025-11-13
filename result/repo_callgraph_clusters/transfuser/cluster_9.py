# Cluster 9

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

def autodetect_proxy():
    proxies = {}
    proxy_https = os.getenv('HTTPS_PROXY', os.getenv('https_proxy', None))
    proxy_http = os.getenv('HTTP_PROXY', os.getenv('http_proxy', None))
    if proxy_https:
        proxies['https'] = proxy_https
    if proxy_http:
        proxies['http'] = proxy_http
    return proxies

class AgentWrapper(object):
    """
    Wrapper for autonomous agents required for tracking and checking of used sensors
    """
    allowed_sensors = ['sensor.opendrive_map', 'sensor.speedometer', 'sensor.camera.rgb', 'sensor.camera', 'sensor.lidar.ray_cast', 'sensor.other.radar', 'sensor.other.gnss', 'sensor.other.imu', 'sensor.stitch_camera.rgb', 'sensor.camera.depth', 'sensor.camera.semantic_segmentation']
    _agent = None
    _sensors_list = []

    def __init__(self, agent):
        """
        Set the autonomous agent
        """
        self._agent = agent

    def __call__(self):
        """
        Pass the call directly to the agent
        """
        return self._agent()

    def setup_sensors(self, vehicle, debug_mode=False):
        """
        Create the sensors defined by the user and attach them to the ego-vehicle
        :param vehicle: ego vehicle
        :return:
        """
        bp_library = CarlaDataProvider.get_world().get_blueprint_library()
        for sensor_spec in self._agent.sensors():
            if sensor_spec['type'].startswith('sensor.opendrive_map'):
                sensor = OpenDriveMapReader(vehicle, sensor_spec['reading_frequency'])
            elif sensor_spec['type'].startswith('sensor.speedometer'):
                delta_time = CarlaDataProvider.get_world().get_settings().fixed_delta_seconds
                frame_rate = 1 / delta_time
                sensor = SpeedometerReader(vehicle, frame_rate)
            elif sensor_spec['type'].startswith('sensor.stitch_camera'):
                delta_time = CarlaDataProvider.get_world().get_settings().fixed_delta_seconds
                frame_rate = 1 / delta_time
                sensor = StitchCameraReader(bp_library, vehicle, sensor_spec, frame_rate)
            else:
                bp = bp_library.find(str(sensor_spec['type']))
                if sensor_spec['type'].startswith('sensor.camera'):
                    bp.set_attribute('image_size_x', str(sensor_spec['width']))
                    bp.set_attribute('image_size_y', str(sensor_spec['height']))
                    bp.set_attribute('fov', str(sensor_spec['fov']))
                    if DATAGEN == 0:
                        bp.set_attribute('lens_circle_multiplier', str(3.0))
                        bp.set_attribute('lens_circle_falloff', str(3.0))
                    if sensor_spec['type'].startswith('sensor.camera.rgb'):
                        bp.set_attribute('chromatic_aberration_intensity', str(0.5))
                        bp.set_attribute('chromatic_aberration_offset', str(0))
                    sensor_location = carla.Location(x=sensor_spec['x'], y=sensor_spec['y'], z=sensor_spec['z'])
                    sensor_rotation = carla.Rotation(pitch=sensor_spec['pitch'], roll=sensor_spec['roll'], yaw=sensor_spec['yaw'])
                elif sensor_spec['type'].startswith('sensor.lidar'):
                    bp.set_attribute('range', str(85))
                    if DATAGEN == 1:
                        bp.set_attribute('rotation_frequency', str(sensor_spec['rotation_frequency']))
                        bp.set_attribute('points_per_second', str(sensor_spec['points_per_second']))
                    else:
                        bp.set_attribute('rotation_frequency', str(10))
                        bp.set_attribute('points_per_second', str(600000))
                    bp.set_attribute('channels', str(64))
                    bp.set_attribute('upper_fov', str(10))
                    bp.set_attribute('atmosphere_attenuation_rate', str(0.004))
                    bp.set_attribute('dropoff_general_rate', str(0.45))
                    bp.set_attribute('dropoff_intensity_limit', str(0.8))
                    bp.set_attribute('dropoff_zero_intensity', str(0.4))
                    sensor_location = carla.Location(x=sensor_spec['x'], y=sensor_spec['y'], z=sensor_spec['z'])
                    sensor_rotation = carla.Rotation(pitch=sensor_spec['pitch'], roll=sensor_spec['roll'], yaw=sensor_spec['yaw'])
                elif sensor_spec['type'].startswith('sensor.other.radar'):
                    bp.set_attribute('horizontal_fov', str(sensor_spec['fov']))
                    bp.set_attribute('vertical_fov', str(sensor_spec['fov']))
                    bp.set_attribute('points_per_second', '1500')
                    bp.set_attribute('range', '100')
                    sensor_location = carla.Location(x=sensor_spec['x'], y=sensor_spec['y'], z=sensor_spec['z'])
                    sensor_rotation = carla.Rotation(pitch=sensor_spec['pitch'], roll=sensor_spec['roll'], yaw=sensor_spec['yaw'])
                elif sensor_spec['type'].startswith('sensor.other.gnss'):
                    if DATAGEN == 0:
                        bp.set_attribute('noise_alt_stddev', str(5e-06))
                        bp.set_attribute('noise_lat_stddev', str(5e-06))
                        bp.set_attribute('noise_lon_stddev', str(5e-06))
                    bp.set_attribute('noise_alt_bias', str(0.0))
                    bp.set_attribute('noise_lat_bias', str(0.0))
                    bp.set_attribute('noise_lon_bias', str(0.0))
                    sensor_location = carla.Location(x=sensor_spec['x'], y=sensor_spec['y'], z=sensor_spec['z'])
                    sensor_rotation = carla.Rotation()
                elif sensor_spec['type'].startswith('sensor.other.imu'):
                    bp.set_attribute('noise_accel_stddev_x', str(0.001))
                    bp.set_attribute('noise_accel_stddev_y', str(0.001))
                    bp.set_attribute('noise_accel_stddev_z', str(0.015))
                    bp.set_attribute('noise_gyro_stddev_x', str(0.001))
                    bp.set_attribute('noise_gyro_stddev_y', str(0.001))
                    bp.set_attribute('noise_gyro_stddev_z', str(0.001))
                    sensor_location = carla.Location(x=sensor_spec['x'], y=sensor_spec['y'], z=sensor_spec['z'])
                    sensor_rotation = carla.Rotation(pitch=sensor_spec['pitch'], roll=sensor_spec['roll'], yaw=sensor_spec['yaw'])
                sensor_transform = carla.Transform(sensor_location, sensor_rotation)
                sensor = CarlaDataProvider.get_world().spawn_actor(bp, sensor_transform, vehicle)
            sensor.listen(CallBack(sensor_spec['id'], sensor_spec['type'], sensor, self._agent.sensor_interface))
            self._sensors_list.append(sensor)
        CarlaDataProvider.get_world().tick()

    @staticmethod
    def validate_sensor_configuration(sensors, agent_track, selected_track):
        """
        Ensure that the sensor configuration is valid, in case the challenge mode is used
        Returns true on valid configuration, false otherwise
        """
        if Track(selected_track) != agent_track:
            raise SensorConfigurationInvalid('You are submitting to the wrong track [{}]!'.format(Track(selected_track)))
        sensor_count = {}
        sensor_ids = []
        for sensor in sensors:
            sensor_id = sensor['id']
            if sensor_id in sensor_ids:
                raise SensorConfigurationInvalid('Duplicated sensor tag [{}]'.format(sensor_id))
            else:
                sensor_ids.append(sensor_id)
            if agent_track == Track.SENSORS:
                if sensor['type'].startswith('sensor.opendrive_map'):
                    raise SensorConfigurationInvalid('Illegal sensor used for Track [{}]!'.format(agent_track))
            if sensor['type'] not in AgentWrapper.allowed_sensors:
                raise SensorConfigurationInvalid('Illegal sensor used. {} are not allowed!'.format(sensor['type']))
            if 'x' in sensor and 'y' in sensor and ('z' in sensor):
                if math.sqrt(sensor['x'] ** 2 + sensor['y'] ** 2 + sensor['z'] ** 2) > MAX_ALLOWED_RADIUS_SENSOR:
                    raise SensorConfigurationInvalid('Illegal sensor extrinsics used for Track [{}]!'.format(agent_track))
            if sensor['type'] in sensor_count:
                sensor_count[sensor['type']] += 1
            else:
                sensor_count[sensor['type']] = 1
        for sensor_type, max_instances_allowed in SENSORS_LIMITS.items():
            if sensor_type in sensor_count and sensor_count[sensor_type] > max_instances_allowed:
                raise SensorConfigurationInvalid('Too many {} used! Maximum number allowed is {}, but {} were requested.'.format(sensor_type, max_instances_allowed, sensor_count[sensor_type]))

    def cleanup(self):
        """
        Remove and destroy all sensors
        """
        for i, _ in enumerate(self._sensors_list):
            if self._sensors_list[i] is not None:
                self._sensors_list[i].stop()
                self._sensors_list[i].destroy()
                self._sensors_list[i] = None
        self._sensors_list = []

def setup_sensors(self, vehicle, debug_mode=False):
    """
        Create the sensors defined by the user and attach them to the ego-vehicle
        :param vehicle: ego vehicle
        :return:
        """
    bp_library = CarlaDataProvider.get_world().get_blueprint_library()
    for sensor_spec in self._agent.sensors():
        if sensor_spec['type'].startswith('sensor.opendrive_map'):
            sensor = OpenDriveMapReader(vehicle, sensor_spec['reading_frequency'])
        elif sensor_spec['type'].startswith('sensor.speedometer'):
            delta_time = CarlaDataProvider.get_world().get_settings().fixed_delta_seconds
            frame_rate = 1 / delta_time
            sensor = SpeedometerReader(vehicle, frame_rate)
        elif sensor_spec['type'].startswith('sensor.stitch_camera'):
            delta_time = CarlaDataProvider.get_world().get_settings().fixed_delta_seconds
            frame_rate = 1 / delta_time
            sensor = StitchCameraReader(bp_library, vehicle, sensor_spec, frame_rate)
        else:
            bp = bp_library.find(str(sensor_spec['type']))
            if sensor_spec['type'].startswith('sensor.camera'):
                bp.set_attribute('image_size_x', str(sensor_spec['width']))
                bp.set_attribute('image_size_y', str(sensor_spec['height']))
                bp.set_attribute('fov', str(sensor_spec['fov']))
                if DATAGEN == 0:
                    bp.set_attribute('lens_circle_multiplier', str(3.0))
                    bp.set_attribute('lens_circle_falloff', str(3.0))
                if sensor_spec['type'].startswith('sensor.camera.rgb'):
                    bp.set_attribute('chromatic_aberration_intensity', str(0.5))
                    bp.set_attribute('chromatic_aberration_offset', str(0))
                sensor_location = carla.Location(x=sensor_spec['x'], y=sensor_spec['y'], z=sensor_spec['z'])
                sensor_rotation = carla.Rotation(pitch=sensor_spec['pitch'], roll=sensor_spec['roll'], yaw=sensor_spec['yaw'])
            elif sensor_spec['type'].startswith('sensor.lidar'):
                bp.set_attribute('range', str(85))
                if DATAGEN == 1:
                    bp.set_attribute('rotation_frequency', str(sensor_spec['rotation_frequency']))
                    bp.set_attribute('points_per_second', str(sensor_spec['points_per_second']))
                else:
                    bp.set_attribute('rotation_frequency', str(10))
                    bp.set_attribute('points_per_second', str(600000))
                bp.set_attribute('channels', str(64))
                bp.set_attribute('upper_fov', str(10))
                bp.set_attribute('atmosphere_attenuation_rate', str(0.004))
                bp.set_attribute('dropoff_general_rate', str(0.45))
                bp.set_attribute('dropoff_intensity_limit', str(0.8))
                bp.set_attribute('dropoff_zero_intensity', str(0.4))
                sensor_location = carla.Location(x=sensor_spec['x'], y=sensor_spec['y'], z=sensor_spec['z'])
                sensor_rotation = carla.Rotation(pitch=sensor_spec['pitch'], roll=sensor_spec['roll'], yaw=sensor_spec['yaw'])
            elif sensor_spec['type'].startswith('sensor.other.radar'):
                bp.set_attribute('horizontal_fov', str(sensor_spec['fov']))
                bp.set_attribute('vertical_fov', str(sensor_spec['fov']))
                bp.set_attribute('points_per_second', '1500')
                bp.set_attribute('range', '100')
                sensor_location = carla.Location(x=sensor_spec['x'], y=sensor_spec['y'], z=sensor_spec['z'])
                sensor_rotation = carla.Rotation(pitch=sensor_spec['pitch'], roll=sensor_spec['roll'], yaw=sensor_spec['yaw'])
            elif sensor_spec['type'].startswith('sensor.other.gnss'):
                if DATAGEN == 0:
                    bp.set_attribute('noise_alt_stddev', str(5e-06))
                    bp.set_attribute('noise_lat_stddev', str(5e-06))
                    bp.set_attribute('noise_lon_stddev', str(5e-06))
                bp.set_attribute('noise_alt_bias', str(0.0))
                bp.set_attribute('noise_lat_bias', str(0.0))
                bp.set_attribute('noise_lon_bias', str(0.0))
                sensor_location = carla.Location(x=sensor_spec['x'], y=sensor_spec['y'], z=sensor_spec['z'])
                sensor_rotation = carla.Rotation()
            elif sensor_spec['type'].startswith('sensor.other.imu'):
                bp.set_attribute('noise_accel_stddev_x', str(0.001))
                bp.set_attribute('noise_accel_stddev_y', str(0.001))
                bp.set_attribute('noise_accel_stddev_z', str(0.015))
                bp.set_attribute('noise_gyro_stddev_x', str(0.001))
                bp.set_attribute('noise_gyro_stddev_y', str(0.001))
                bp.set_attribute('noise_gyro_stddev_z', str(0.001))
                sensor_location = carla.Location(x=sensor_spec['x'], y=sensor_spec['y'], z=sensor_spec['z'])
                sensor_rotation = carla.Rotation(pitch=sensor_spec['pitch'], roll=sensor_spec['roll'], yaw=sensor_spec['yaw'])
            sensor_transform = carla.Transform(sensor_location, sensor_rotation)
            sensor = CarlaDataProvider.get_world().spawn_actor(bp, sensor_transform, vehicle)
        sensor.listen(CallBack(sensor_spec['id'], sensor_spec['type'], sensor, self._agent.sensor_interface))
        self._sensors_list.append(sensor)
    CarlaDataProvider.get_world().tick()

class AgentWrapper(object):
    """
    Wrapper for autonomous agents required for tracking and checking of used sensors
    """
    allowed_sensors = ['sensor.opendrive_map', 'sensor.speedometer', 'sensor.camera.rgb', 'sensor.camera', 'sensor.lidar.ray_cast', 'sensor.other.radar', 'sensor.other.gnss', 'sensor.other.imu']
    _agent = None
    _sensors_list = []

    def __init__(self, agent):
        """
        Set the autonomous agent
        """
        self._agent = agent

    def __call__(self):
        """
        Pass the call directly to the agent
        """
        return self._agent()

    def setup_sensors(self, vehicle, debug_mode=False):
        """
        Create the sensors defined by the user and attach them to the ego-vehicle
        :param vehicle: ego vehicle
        :return:
        """
        bp_library = CarlaDataProvider.get_world().get_blueprint_library()
        for sensor_spec in self._agent.sensors():
            if sensor_spec['type'].startswith('sensor.opendrive_map'):
                sensor = OpenDriveMapReader(vehicle, sensor_spec['reading_frequency'])
            elif sensor_spec['type'].startswith('sensor.speedometer'):
                delta_time = CarlaDataProvider.get_world().get_settings().fixed_delta_seconds
                frame_rate = 1 / delta_time
                sensor = SpeedometerReader(vehicle, frame_rate)
            else:
                bp = bp_library.find(str(sensor_spec['type']))
                if sensor_spec['type'].startswith('sensor.camera'):
                    bp.set_attribute('image_size_x', str(sensor_spec['width']))
                    bp.set_attribute('image_size_y', str(sensor_spec['height']))
                    bp.set_attribute('fov', str(sensor_spec['fov']))
                    bp.set_attribute('lens_circle_multiplier', str(3.0))
                    bp.set_attribute('lens_circle_falloff', str(3.0))
                    bp.set_attribute('chromatic_aberration_intensity', str(0.5))
                    bp.set_attribute('chromatic_aberration_offset', str(0))
                    sensor_location = carla.Location(x=sensor_spec['x'], y=sensor_spec['y'], z=sensor_spec['z'])
                    sensor_rotation = carla.Rotation(pitch=sensor_spec['pitch'], roll=sensor_spec['roll'], yaw=sensor_spec['yaw'])
                elif sensor_spec['type'].startswith('sensor.lidar'):
                    bp.set_attribute('range', str(85))
                    bp.set_attribute('rotation_frequency', str(10))
                    bp.set_attribute('channels', str(64))
                    bp.set_attribute('upper_fov', str(10))
                    bp.set_attribute('lower_fov', str(-30))
                    bp.set_attribute('points_per_second', str(600000))
                    bp.set_attribute('atmosphere_attenuation_rate', str(0.004))
                    bp.set_attribute('dropoff_general_rate', str(0.45))
                    bp.set_attribute('dropoff_intensity_limit', str(0.8))
                    bp.set_attribute('dropoff_zero_intensity', str(0.4))
                    sensor_location = carla.Location(x=sensor_spec['x'], y=sensor_spec['y'], z=sensor_spec['z'])
                    sensor_rotation = carla.Rotation(pitch=sensor_spec['pitch'], roll=sensor_spec['roll'], yaw=sensor_spec['yaw'])
                elif sensor_spec['type'].startswith('sensor.other.radar'):
                    bp.set_attribute('horizontal_fov', str(sensor_spec['fov']))
                    bp.set_attribute('vertical_fov', str(sensor_spec['fov']))
                    bp.set_attribute('points_per_second', '1500')
                    bp.set_attribute('range', '100')
                    sensor_location = carla.Location(x=sensor_spec['x'], y=sensor_spec['y'], z=sensor_spec['z'])
                    sensor_rotation = carla.Rotation(pitch=sensor_spec['pitch'], roll=sensor_spec['roll'], yaw=sensor_spec['yaw'])
                elif sensor_spec['type'].startswith('sensor.other.gnss'):
                    bp.set_attribute('noise_alt_stddev', str(5e-06))
                    bp.set_attribute('noise_lat_stddev', str(5e-06))
                    bp.set_attribute('noise_lon_stddev', str(5e-06))
                    bp.set_attribute('noise_alt_bias', str(0.0))
                    bp.set_attribute('noise_lat_bias', str(0.0))
                    bp.set_attribute('noise_lon_bias', str(0.0))
                    sensor_location = carla.Location(x=sensor_spec['x'], y=sensor_spec['y'], z=sensor_spec['z'])
                    sensor_rotation = carla.Rotation()
                elif sensor_spec['type'].startswith('sensor.other.imu'):
                    bp.set_attribute('noise_accel_stddev_x', str(0.001))
                    bp.set_attribute('noise_accel_stddev_y', str(0.001))
                    bp.set_attribute('noise_accel_stddev_z', str(0.015))
                    bp.set_attribute('noise_gyro_stddev_x', str(0.001))
                    bp.set_attribute('noise_gyro_stddev_y', str(0.001))
                    bp.set_attribute('noise_gyro_stddev_z', str(0.001))
                    sensor_location = carla.Location(x=sensor_spec['x'], y=sensor_spec['y'], z=sensor_spec['z'])
                    sensor_rotation = carla.Rotation(pitch=sensor_spec['pitch'], roll=sensor_spec['roll'], yaw=sensor_spec['yaw'])
                sensor_transform = carla.Transform(sensor_location, sensor_rotation)
                sensor = CarlaDataProvider.get_world().spawn_actor(bp, sensor_transform, vehicle)
            sensor.listen(CallBack(sensor_spec['id'], sensor_spec['type'], sensor, self._agent.sensor_interface))
            self._sensors_list.append(sensor)
        CarlaDataProvider.get_world().tick()

    @staticmethod
    def validate_sensor_configuration(sensors, agent_track, selected_track):
        """
        Ensure that the sensor configuration is valid, in case the challenge mode is used
        Returns true on valid configuration, false otherwise
        """
        if Track(selected_track) != agent_track:
            raise SensorConfigurationInvalid('You are submitting to the wrong track [{}]!'.format(Track(selected_track)))
        sensor_count = {}
        sensor_ids = []
        for sensor in sensors:
            sensor_id = sensor['id']
            if sensor_id in sensor_ids:
                raise SensorConfigurationInvalid('Duplicated sensor tag [{}]'.format(sensor_id))
            else:
                sensor_ids.append(sensor_id)
            if agent_track == Track.SENSORS:
                if sensor['type'].startswith('sensor.opendrive_map'):
                    raise SensorConfigurationInvalid('Illegal sensor used for Track [{}]!'.format(agent_track))
            if sensor['type'] not in AgentWrapper.allowed_sensors:
                raise SensorConfigurationInvalid('Illegal sensor used. {} are not allowed!'.format(sensor['type']))
            if 'x' in sensor and 'y' in sensor and ('z' in sensor):
                if math.sqrt(sensor['x'] ** 2 + sensor['y'] ** 2 + sensor['z'] ** 2) > MAX_ALLOWED_RADIUS_SENSOR:
                    raise SensorConfigurationInvalid('Illegal sensor extrinsics used for Track [{}]!'.format(agent_track))
            if sensor['type'] in sensor_count:
                sensor_count[sensor['type']] += 1
            else:
                sensor_count[sensor['type']] = 1
        for sensor_type, max_instances_allowed in SENSORS_LIMITS.items():
            if sensor_type in sensor_count and sensor_count[sensor_type] > max_instances_allowed:
                raise SensorConfigurationInvalid('Too many {} used! Maximum number allowed is {}, but {} were requested.'.format(sensor_type, max_instances_allowed, sensor_count[sensor_type]))

    def cleanup(self):
        """
        Remove and destroy all sensors
        """
        for i, _ in enumerate(self._sensors_list):
            if self._sensors_list[i] is not None:
                self._sensors_list[i].stop()
                self._sensors_list[i].destroy()
                self._sensors_list[i] = None
        self._sensors_list = []

def setup_sensors(self, vehicle, debug_mode=False):
    """
        Create the sensors defined by the user and attach them to the ego-vehicle
        :param vehicle: ego vehicle
        :return:
        """
    bp_library = CarlaDataProvider.get_world().get_blueprint_library()
    for sensor_spec in self._agent.sensors():
        if sensor_spec['type'].startswith('sensor.opendrive_map'):
            sensor = OpenDriveMapReader(vehicle, sensor_spec['reading_frequency'])
        elif sensor_spec['type'].startswith('sensor.speedometer'):
            delta_time = CarlaDataProvider.get_world().get_settings().fixed_delta_seconds
            frame_rate = 1 / delta_time
            sensor = SpeedometerReader(vehicle, frame_rate)
        else:
            bp = bp_library.find(str(sensor_spec['type']))
            if sensor_spec['type'].startswith('sensor.camera'):
                bp.set_attribute('image_size_x', str(sensor_spec['width']))
                bp.set_attribute('image_size_y', str(sensor_spec['height']))
                bp.set_attribute('fov', str(sensor_spec['fov']))
                bp.set_attribute('lens_circle_multiplier', str(3.0))
                bp.set_attribute('lens_circle_falloff', str(3.0))
                bp.set_attribute('chromatic_aberration_intensity', str(0.5))
                bp.set_attribute('chromatic_aberration_offset', str(0))
                sensor_location = carla.Location(x=sensor_spec['x'], y=sensor_spec['y'], z=sensor_spec['z'])
                sensor_rotation = carla.Rotation(pitch=sensor_spec['pitch'], roll=sensor_spec['roll'], yaw=sensor_spec['yaw'])
            elif sensor_spec['type'].startswith('sensor.lidar'):
                bp.set_attribute('range', str(85))
                bp.set_attribute('rotation_frequency', str(10))
                bp.set_attribute('channels', str(64))
                bp.set_attribute('upper_fov', str(10))
                bp.set_attribute('lower_fov', str(-30))
                bp.set_attribute('points_per_second', str(600000))
                bp.set_attribute('atmosphere_attenuation_rate', str(0.004))
                bp.set_attribute('dropoff_general_rate', str(0.45))
                bp.set_attribute('dropoff_intensity_limit', str(0.8))
                bp.set_attribute('dropoff_zero_intensity', str(0.4))
                sensor_location = carla.Location(x=sensor_spec['x'], y=sensor_spec['y'], z=sensor_spec['z'])
                sensor_rotation = carla.Rotation(pitch=sensor_spec['pitch'], roll=sensor_spec['roll'], yaw=sensor_spec['yaw'])
            elif sensor_spec['type'].startswith('sensor.other.radar'):
                bp.set_attribute('horizontal_fov', str(sensor_spec['fov']))
                bp.set_attribute('vertical_fov', str(sensor_spec['fov']))
                bp.set_attribute('points_per_second', '1500')
                bp.set_attribute('range', '100')
                sensor_location = carla.Location(x=sensor_spec['x'], y=sensor_spec['y'], z=sensor_spec['z'])
                sensor_rotation = carla.Rotation(pitch=sensor_spec['pitch'], roll=sensor_spec['roll'], yaw=sensor_spec['yaw'])
            elif sensor_spec['type'].startswith('sensor.other.gnss'):
                bp.set_attribute('noise_alt_stddev', str(5e-06))
                bp.set_attribute('noise_lat_stddev', str(5e-06))
                bp.set_attribute('noise_lon_stddev', str(5e-06))
                bp.set_attribute('noise_alt_bias', str(0.0))
                bp.set_attribute('noise_lat_bias', str(0.0))
                bp.set_attribute('noise_lon_bias', str(0.0))
                sensor_location = carla.Location(x=sensor_spec['x'], y=sensor_spec['y'], z=sensor_spec['z'])
                sensor_rotation = carla.Rotation()
            elif sensor_spec['type'].startswith('sensor.other.imu'):
                bp.set_attribute('noise_accel_stddev_x', str(0.001))
                bp.set_attribute('noise_accel_stddev_y', str(0.001))
                bp.set_attribute('noise_accel_stddev_z', str(0.015))
                bp.set_attribute('noise_gyro_stddev_x', str(0.001))
                bp.set_attribute('noise_gyro_stddev_y', str(0.001))
                bp.set_attribute('noise_gyro_stddev_z', str(0.001))
                sensor_location = carla.Location(x=sensor_spec['x'], y=sensor_spec['y'], z=sensor_spec['z'])
                sensor_rotation = carla.Rotation(pitch=sensor_spec['pitch'], roll=sensor_spec['roll'], yaw=sensor_spec['yaw'])
            sensor_transform = carla.Transform(sensor_location, sensor_rotation)
            sensor = CarlaDataProvider.get_world().spawn_actor(bp, sensor_transform, vehicle)
        sensor.listen(CallBack(sensor_spec['id'], sensor_spec['type'], sensor, self._agent.sensor_interface))
        self._sensors_list.append(sensor)
    CarlaDataProvider.get_world().tick()

def main():
    """
    Used to help with the visualization of the scenario trigger points, as well as its
    modifications.
        --town: Selects the town
        --scenario: The scenario that will be printed. Use the number of the scenarios 1 2 3 ...
        --modify: Used to modify the trigger_points of the given scenario in args.scenarios.
          debug is auto-enabled here. It will be shown red if they aren't apart enough or green, if they are
        --debug: If debug is selected, the points will be shown one by one, and stored at --endpoint,
    in case some copy-pasting is required.
    """
    parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter)
    parser.add_argument('--town', default='Town08')
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--reload', action='store_true')
    parser.add_argument('--inipoint', default='')
    parser.add_argument('--endpoint', default='set_new_scenarios.json')
    parser.add_argument('--scenarios', nargs='+', default='Scenario7')
    parser.add_argument('--modify', action='store_true')
    parser.add_argument('--host', default='localhost', help='IP of the host server (default: localhost)')
    parser.add_argument('--port', default='2000', help='TCP port to listen to (default: 2000)')
    args = parser.parse_args()
    client = carla.Client(args.host, int(args.port))
    client.set_timeout(20)
    if args.reload:
        world = client.load_world(args.town)
    else:
        world = client.get_world()
    settings = world.get_settings()
    settings.fixed_delta_seconds = None
    settings.synchronous_mode = False
    world.apply_settings(settings)
    data = fetch_dict(args.inipoint)
    data = data['available_scenarios'][0]
    town_data = data[args.town]
    new_args_scenario = []
    for ar_sc in args.scenarios:
        new_args_scenario.append('Scenario' + ar_sc)
    args.scenarios = new_args_scenario
    for scenarios in town_data:
        if args.modify:
            modify_junction_scenarios(world, scenarios, args)
        else:
            draw_scenarios(world, scenarios, args)
    print(' ---------------------------- ')
    for ar_sc in args.scenarios:
        print(' {} is colored as {}'.format(ar_sc, SCENARIO_COLOR[ar_sc][1]))
    print(' ---------------------------- ')

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

def tick(self, clock):
    for module in self.modules:
        module.tick(clock)

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

def tick(self, clock):
    self._notifications.tick(clock)

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

class BasicScenario(object):
    """
    Base class for user-defined scenario
    """

    def __init__(self, name, ego_vehicles, config, world, debug_mode=False, terminate_on_failure=False, criteria_enable=False):
        """
        Setup all relevant parameters and create scenario
        and instantiate scenario manager
        """
        self.other_actors = []
        if not self.timeout:
            self.timeout = 60
        self.criteria_list = []
        self.scenario = None
        self.ego_vehicles = ego_vehicles
        self.name = name
        self.config = config
        self.terminate_on_failure = terminate_on_failure
        self._initialize_environment(world)
        self._initialize_actors(config)
        if CarlaDataProvider.is_sync_mode():
            world.tick()
        else:
            world.wait_for_tick()
        if debug_mode:
            py_trees.logging.level = py_trees.logging.Level.DEBUG
        behavior = self._create_behavior()
        criteria = None
        if criteria_enable:
            criteria = self._create_test_criteria()
        behavior_seq = py_trees.composites.Sequence()
        trigger_behavior = self._setup_scenario_trigger(config)
        if trigger_behavior:
            behavior_seq.add_child(trigger_behavior)
        if behavior is not None:
            behavior_seq.add_child(behavior)
            behavior_seq.name = behavior.name
        end_behavior = self._setup_scenario_end(config)
        if end_behavior:
            behavior_seq.add_child(end_behavior)
        self.scenario = Scenario(behavior_seq, criteria, self.name, self.timeout, self.terminate_on_failure)

    def _initialize_environment(self, world):
        """
        Default initialization of weather and road friction.
        Override this method in child class to provide custom initialization.
        """
        world.set_weather(self.config.weather)
        if self.config.friction is not None:
            friction_bp = world.get_blueprint_library().find('static.trigger.friction')
            extent = carla.Location(1000000.0, 1000000.0, 1000000.0)
            friction_bp.set_attribute('friction', str(self.config.friction))
            friction_bp.set_attribute('extent_x', str(extent.x))
            friction_bp.set_attribute('extent_y', str(extent.y))
            friction_bp.set_attribute('extent_z', str(extent.z))
            transform = carla.Transform()
            transform.location = carla.Location(-10000.0, -10000.0, 0.0)
            world.spawn_actor(friction_bp, transform)

    def _initialize_actors(self, config):
        """
        Default initialization of other actors.
        Override this method in child class to provide custom initialization.
        """
        if config.other_actors:
            new_actors = CarlaDataProvider.request_new_actors(config.other_actors)
            if not new_actors:
                raise Exception('Error: Unable to add actors')
            for new_actor in new_actors:
                self.other_actors.append(new_actor)

    def _setup_scenario_trigger(self, config):
        """
        This function creates a trigger maneuver, that has to be finished before the real scenario starts.
        This implementation focuses on the first available ego vehicle.

        The function can be overloaded by a user implementation inside the user-defined scenario class.
        """
        start_location = None
        if config.trigger_points and config.trigger_points[0]:
            start_location = config.trigger_points[0].location
        ego_vehicle_route = CarlaDataProvider.get_ego_vehicle_route()
        if start_location:
            if ego_vehicle_route:
                if config.route_var_name is None:
                    return conditions.InTriggerDistanceToLocationAlongRoute(self.ego_vehicles[0], ego_vehicle_route, start_location, 5)
                else:
                    check_name = 'WaitForBlackboardVariable: {}'.format(config.route_var_name)
                    return conditions.WaitForBlackboardVariable(name=check_name, variable_name=config.route_var_name, variable_value=True, var_init_value=False)
            return conditions.InTimeToArrivalToLocation(self.ego_vehicles[0], 2.0, start_location)
        return None

    def _setup_scenario_end(self, config):
        """
        This function adds and additional behavior to the scenario, which is triggered
        after it has ended.

        The function can be overloaded by a user implementation inside the user-defined scenario class.
        """
        ego_vehicle_route = CarlaDataProvider.get_ego_vehicle_route()
        if ego_vehicle_route:
            if config.route_var_name is not None:
                set_name = 'Reset Blackboard Variable: {} '.format(config.route_var_name)
                return py_trees.blackboard.SetBlackboardVariable(name=set_name, variable_name=config.route_var_name, variable_value=False)
        return None

    def _create_behavior(self):
        """
        Pure virtual function to setup user-defined scenario behavior
        """
        raise NotImplementedError('This function is re-implemented by all scenariosIf this error becomes visible the class hierarchy is somehow broken')

    def _create_test_criteria(self):
        """
        Pure virtual function to setup user-defined evaluation criteria for the
        scenario
        """
        raise NotImplementedError('This function is re-implemented by all scenariosIf this error becomes visible the class hierarchy is somehow broken')

    def change_control(self, control):
        """
        This is a function that changes the control based on the scenario determination
        :param control: a carla vehicle control
        :return: a control to be changed by the scenario.

        Note: This method should be overriden by the user-defined scenario behavior
        """
        return control

    def remove_all_actors(self):
        """
        Remove all actors
        """
        for i, _ in enumerate(self.other_actors):
            if self.other_actors[i] is not None:
                if CarlaDataProvider.actor_id_exists(self.other_actors[i].id):
                    CarlaDataProvider.remove_actor_by_id(self.other_actors[i].id)
                self.other_actors[i] = None
        self.other_actors = []

def __init__(self, name, ego_vehicles, config, world, debug_mode=False, terminate_on_failure=False, criteria_enable=False):
    """
        Setup all relevant parameters and create scenario
        and instantiate scenario manager
        """
    self.other_actors = []
    if not self.timeout:
        self.timeout = 60
    self.criteria_list = []
    self.scenario = None
    self.ego_vehicles = ego_vehicles
    self.name = name
    self.config = config
    self.terminate_on_failure = terminate_on_failure
    self._initialize_environment(world)
    self._initialize_actors(config)
    if CarlaDataProvider.is_sync_mode():
        world.tick()
    else:
        world.wait_for_tick()
    if debug_mode:
        py_trees.logging.level = py_trees.logging.Level.DEBUG
    behavior = self._create_behavior()
    criteria = None
    if criteria_enable:
        criteria = self._create_test_criteria()
    behavior_seq = py_trees.composites.Sequence()
    trigger_behavior = self._setup_scenario_trigger(config)
    if trigger_behavior:
        behavior_seq.add_child(trigger_behavior)
    if behavior is not None:
        behavior_seq.add_child(behavior)
        behavior_seq.name = behavior.name
    end_behavior = self._setup_scenario_end(config)
    if end_behavior:
        behavior_seq.add_child(end_behavior)
    self.scenario = Scenario(behavior_seq, criteria, self.name, self.timeout, self.terminate_on_failure)

def _initialize_environment(self, world):
    """
        Default initialization of weather and road friction.
        Override this method in child class to provide custom initialization.
        """
    world.set_weather(self.config.weather)
    if self.config.friction is not None:
        friction_bp = world.get_blueprint_library().find('static.trigger.friction')
        extent = carla.Location(1000000.0, 1000000.0, 1000000.0)
        friction_bp.set_attribute('friction', str(self.config.friction))
        friction_bp.set_attribute('extent_x', str(extent.x))
        friction_bp.set_attribute('extent_y', str(extent.y))
        friction_bp.set_attribute('extent_z', str(extent.z))
        transform = carla.Transform()
        transform.location = carla.Location(-10000.0, -10000.0, 0.0)
        world.spawn_actor(friction_bp, transform)

def get_xml_path(tree, node):
    """
    Extract the full path of a node within an XML tree

    Note: Catalogs are pulled from a separate file so the XML tree is split.
          This means that in order to get the XML path, it must be done in 2 steps.
          Some places in this python script do that by concatenating the results
          of 2 get_xml_path calls with another ">".
          Example: "Behavior>AutopilotSequence" + ">" + "StartAutopilot>StartAutopilot>StartAutopilot"
    """
    path = ''
    parent_map = {c: p for p in tree.iter() for c in p}
    cur_node = node
    while cur_node != tree:
        path = '{}>{}'.format(cur_node.attrib.get('name'), path)
        cur_node = parent_map[cur_node]
    path = path[:-1]
    return path

class RouteScenario(BasicScenario):
    """
    Implementation of a RouteScenario, i.e. a scenario that consists of driving along a pre-defined route,
    along which several smaller scenarios are triggered
    """

    def __init__(self, world, config, debug_mode=False, criteria_enable=True, timeout=300):
        """
        Setup all relevant parameters and create scenarios along route
        """
        self.config = config
        self.route = None
        self.sampled_scenarios_definitions = None
        self._update_route(world, config, debug_mode)
        ego_vehicle = self._update_ego_vehicle()
        self.list_scenarios = self._build_scenario_instances(world, ego_vehicle, self.sampled_scenarios_definitions, scenarios_per_tick=5, timeout=self.timeout, debug_mode=debug_mode)
        super(RouteScenario, self).__init__(name=config.name, ego_vehicles=[ego_vehicle], config=config, world=world, debug_mode=False, terminate_on_failure=False, criteria_enable=criteria_enable)

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
        return int(SECONDS_GIVEN_PER_METERS * route_length)

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
        rng = random.RandomState(random_seed)

        def position_sampled(scenario_choice, sampled_scenarios):
            """
            Check if a position was already sampled, i.e. used for another scenario
            """
            for existent_scenario in sampled_scenarios:
                if compare_scenarios(scenario_choice, existent_scenario):
                    return True
            return False
        sampled_scenarios = []
        for trigger in potential_scenarios_definitions.keys():
            possible_scenarios = potential_scenarios_definitions[trigger]
            scenario_choice = rng.choice(possible_scenarios)
            del possible_scenarios[possible_scenarios.index(scenario_choice)]
            while position_sampled(scenario_choice, sampled_scenarios):
                if possible_scenarios is None or not possible_scenarios:
                    scenario_choice = None
                    break
                scenario_choice = rng.choice(possible_scenarios)
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
                scenario_number += 1
            except Exception as e:
                if debug_mode:
                    traceback.print_exc()
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
        town_amount = {'Town01': 120, 'Town02': 100, 'Town03': 120, 'Town04': 200, 'Town05': 120, 'Town06': 150, 'Town07': 110, 'Town08': 180, 'Town09': 300, 'Town10': 120}
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
                    oneshot_idiom = oneshot_behavior(name, behaviour=scenario.scenario.behavior, name=name)
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
        blocked_criterion = ActorSpeedAboveThresholdTest(self.ego_vehicles[0], speed_threshold=0.1, below_threshold_max_time=90.0, terminate_on_failure=True)
        criteria.append(completion_criterion)
        criteria.append(collision_criterion)
        criteria.append(route_criterion)
        criteria.append(outsidelane_criterion)
        criteria.append(red_light_criterion)
        criteria.append(stop_criterion)
        criteria.append(blocked_criterion)
        return criteria

    def __del__(self):
        """
        Remove all actors upon deletion
        """
        self.remove_all_actors()

def _scenario_sampling(self, potential_scenarios_definitions, random_seed=0):
    """
        The function used to sample the scenarios that are going to happen for this route.
        """
    rng = random.RandomState(random_seed)

    def position_sampled(scenario_choice, sampled_scenarios):
        """
            Check if a position was already sampled, i.e. used for another scenario
            """
        for existent_scenario in sampled_scenarios:
            if compare_scenarios(scenario_choice, existent_scenario):
                return True
        return False
    sampled_scenarios = []
    for trigger in potential_scenarios_definitions.keys():
        possible_scenarios = potential_scenarios_definitions[trigger]
        scenario_choice = rng.choice(possible_scenarios)
        del possible_scenarios[possible_scenarios.index(scenario_choice)]
        while position_sampled(scenario_choice, sampled_scenarios):
            if possible_scenarios is None or not possible_scenarios:
                scenario_choice = None
                break
            scenario_choice = rng.choice(possible_scenarios)
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
            scenario_number += 1
        except Exception as e:
            if debug_mode:
                traceback.print_exc()
            print("Skipping scenario '{}' due to setup error: {}".format(definition['name'], e))
            continue
        scenario_instance_vec.append(scenario_instance)
    return scenario_instance_vec

class CarlaDataProvider(object):
    """
    This class provides access to various data of all registered actors
    It buffers the data and updates it on every CARLA tick

    Currently available data:
    - Absolute velocity
    - Location
    - Transform

    Potential additions:
    - Acceleration

    In addition it provides access to the map and the transform of all traffic lights
    """
    _actor_velocity_map = dict()
    _actor_location_map = dict()
    _actor_transform_map = dict()
    _traffic_light_map = dict()
    _carla_actor_pool = dict()
    _client = None
    _world = None
    _map = None
    _sync_flag = False
    _spawn_points = None
    _spawn_index = 0
    _blueprint_library = None
    _ego_vehicle_route = None
    _traffic_manager_port = 8000
    _rng = random.RandomState(2000)

    @staticmethod
    def register_actor(actor):
        """
        Add new actor to dictionaries
        If actor already exists, throw an exception
        """
        if actor in CarlaDataProvider._actor_velocity_map:
            raise KeyError("Vehicle '{}' already registered. Cannot register twice!".format(actor.id))
        else:
            CarlaDataProvider._actor_velocity_map[actor] = 0.0
        if actor in CarlaDataProvider._actor_location_map:
            raise KeyError("Vehicle '{}' already registered. Cannot register twice!".format(actor.id))
        else:
            CarlaDataProvider._actor_location_map[actor] = None
        if actor in CarlaDataProvider._actor_transform_map:
            raise KeyError("Vehicle '{}' already registered. Cannot register twice!".format(actor.id))
        else:
            CarlaDataProvider._actor_transform_map[actor] = None

    @staticmethod
    def register_actors(actors):
        """
        Add new set of actors to dictionaries
        """
        for actor in actors:
            CarlaDataProvider.register_actor(actor)

    @staticmethod
    def on_carla_tick():
        """
        Callback from CARLA
        """
        for actor in CarlaDataProvider._actor_velocity_map:
            if actor is not None and actor.is_alive:
                CarlaDataProvider._actor_velocity_map[actor] = calculate_velocity(actor)
        for actor in CarlaDataProvider._actor_location_map:
            if actor is not None and actor.is_alive:
                CarlaDataProvider._actor_location_map[actor] = actor.get_location()
        for actor in CarlaDataProvider._actor_transform_map:
            if actor is not None and actor.is_alive:
                CarlaDataProvider._actor_transform_map[actor] = actor.get_transform()
        world = CarlaDataProvider._world
        if world is None:
            print("WARNING: CarlaDataProvider couldn't find the world")

    @staticmethod
    def get_velocity(actor):
        """
        returns the absolute velocity for the given actor
        """
        for key in CarlaDataProvider._actor_velocity_map:
            if key.id == actor.id:
                return CarlaDataProvider._actor_velocity_map[key]
        print('{}.get_velocity: {} not found!'.format(__name__, actor))
        return 0.0

    @staticmethod
    def get_location(actor):
        """
        returns the location for the given actor
        """
        for key in CarlaDataProvider._actor_location_map:
            if key.id == actor.id:
                return CarlaDataProvider._actor_location_map[key]
        print('{}.get_location: {} not found!'.format(__name__, actor))
        return None

    @staticmethod
    def get_transform(actor):
        """
        returns the transform for the given actor
        """
        for key in CarlaDataProvider._actor_transform_map:
            if key.id == actor.id:
                return CarlaDataProvider._actor_transform_map[key]
        print('{}.get_transform: {} not found!'.format(__name__, actor))
        return None

    @staticmethod
    def set_client(client):
        """
        Set the CARLA client
        """
        CarlaDataProvider._client = client

    @staticmethod
    def get_client():
        """
        Get the CARLA client
        """
        return CarlaDataProvider._client

    @staticmethod
    def set_world(world):
        """
        Set the world and world settings
        """
        CarlaDataProvider._world = world
        CarlaDataProvider._sync_flag = world.get_settings().synchronous_mode
        CarlaDataProvider._map = world.get_map()
        CarlaDataProvider._blueprint_library = world.get_blueprint_library()
        CarlaDataProvider.generate_spawn_points()
        CarlaDataProvider.prepare_map()

    @staticmethod
    def get_world():
        """
        Return world
        """
        return CarlaDataProvider._world

    @staticmethod
    def get_map(world=None):
        """
        Get the current map
        """
        if CarlaDataProvider._map is None:
            if world is None:
                if CarlaDataProvider._world is None:
                    raise ValueError("class member 'world'' not initialized yet")
                else:
                    CarlaDataProvider._map = CarlaDataProvider._world.get_map()
            else:
                CarlaDataProvider._map = world.get_map()
        return CarlaDataProvider._map

    @staticmethod
    def is_sync_mode():
        """
        @return true if syncronuous mode is used
        """
        return CarlaDataProvider._sync_flag

    @staticmethod
    def find_weather_presets():
        """
        Get weather presets from CARLA
        """
        rgx = re.compile('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)')
        name = lambda x: ' '.join((m.group(0) for m in rgx.finditer(x)))
        presets = [x for x in dir(carla.WeatherParameters) if re.match('[A-Z].+', x)]
        return [(getattr(carla.WeatherParameters, x), name(x)) for x in presets]

    @staticmethod
    def prepare_map():
        """
        This function set the current map and loads all traffic lights for this map to
        _traffic_light_map
        """
        if CarlaDataProvider._map is None:
            CarlaDataProvider._map = CarlaDataProvider._world.get_map()
        CarlaDataProvider._traffic_light_map.clear()
        for traffic_light in CarlaDataProvider._world.get_actors().filter('*traffic_light*'):
            if traffic_light not in CarlaDataProvider._traffic_light_map.keys():
                CarlaDataProvider._traffic_light_map[traffic_light] = traffic_light.get_transform()
            else:
                raise KeyError("Traffic light '{}' already registered. Cannot register twice!".format(traffic_light.id))

    @staticmethod
    def annotate_trafficlight_in_group(traffic_light):
        """
        Get dictionary with traffic light group info for a given traffic light
        """
        dict_annotations = {'ref': [], 'opposite': [], 'left': [], 'right': []}
        ref_location = CarlaDataProvider.get_trafficlight_trigger_location(traffic_light)
        ref_waypoint = CarlaDataProvider.get_map().get_waypoint(ref_location)
        ref_yaw = ref_waypoint.transform.rotation.yaw
        group_tl = traffic_light.get_group_traffic_lights()
        for target_tl in group_tl:
            if traffic_light.id == target_tl.id:
                dict_annotations['ref'].append(target_tl)
            else:
                target_location = CarlaDataProvider.get_trafficlight_trigger_location(target_tl)
                target_waypoint = CarlaDataProvider.get_map().get_waypoint(target_location)
                target_yaw = target_waypoint.transform.rotation.yaw
                diff = (target_yaw - ref_yaw) % 360
                if diff > 330:
                    continue
                elif diff > 225:
                    dict_annotations['right'].append(target_tl)
                elif diff > 135.0:
                    dict_annotations['opposite'].append(target_tl)
                elif diff > 30:
                    dict_annotations['left'].append(target_tl)
        return dict_annotations

    @staticmethod
    def get_trafficlight_trigger_location(traffic_light):
        """
        Calculates the yaw of the waypoint that represents the trigger volume of the traffic light
        """

        def rotate_point(point, angle):
            """
            rotate a given point by a given angle
            """
            x_ = math.cos(math.radians(angle)) * point.x - math.sin(math.radians(angle)) * point.y
            y_ = math.sin(math.radians(angle)) * point.x - math.cos(math.radians(angle)) * point.y
            return carla.Vector3D(x_, y_, point.z)
        base_transform = traffic_light.get_transform()
        base_rot = base_transform.rotation.yaw
        area_loc = base_transform.transform(traffic_light.trigger_volume.location)
        area_ext = traffic_light.trigger_volume.extent
        point = rotate_point(carla.Vector3D(0, 0, area_ext.z), base_rot)
        point_location = area_loc + carla.Location(x=point.x, y=point.y)
        return carla.Location(point_location.x, point_location.y, point_location.z)

    @staticmethod
    def update_light_states(ego_light, annotations, states, freeze=False, timeout=1000000000):
        """
        Update traffic light states
        """
        reset_params = []
        for state in states:
            relevant_lights = []
            if state == 'ego':
                relevant_lights = [ego_light]
            else:
                relevant_lights = annotations[state]
            for light in relevant_lights:
                prev_state = light.get_state()
                prev_green_time = light.get_green_time()
                prev_red_time = light.get_red_time()
                prev_yellow_time = light.get_yellow_time()
                reset_params.append({'light': light, 'state': prev_state, 'green_time': prev_green_time, 'red_time': prev_red_time, 'yellow_time': prev_yellow_time})
                light.set_state(states[state])
                if freeze:
                    light.set_green_time(timeout)
                    light.set_red_time(timeout)
                    light.set_yellow_time(timeout)
        return reset_params

    @staticmethod
    def reset_lights(reset_params):
        """
        Reset traffic lights
        """
        for param in reset_params:
            param['light'].set_state(param['state'])
            param['light'].set_green_time(param['green_time'])
            param['light'].set_red_time(param['red_time'])
            param['light'].set_yellow_time(param['yellow_time'])

    @staticmethod
    def get_next_traffic_light(actor, use_cached_location=True):
        """
        returns the next relevant traffic light for the provided actor
        """
        if not use_cached_location:
            location = actor.get_transform().location
        else:
            location = CarlaDataProvider.get_location(actor)
        waypoint = CarlaDataProvider.get_map().get_waypoint(location)
        list_of_waypoints = []
        while waypoint and (not waypoint.is_intersection):
            list_of_waypoints.append(waypoint)
            waypoint = waypoint.next(2.0)[0]
        if not list_of_waypoints:
            return None
        relevant_traffic_light = None
        distance_to_relevant_traffic_light = float('inf')
        for traffic_light in CarlaDataProvider._traffic_light_map:
            if hasattr(traffic_light, 'trigger_volume'):
                tl_t = CarlaDataProvider._traffic_light_map[traffic_light]
                transformed_tv = tl_t.transform(traffic_light.trigger_volume.location)
                distance = carla.Location(transformed_tv).distance(list_of_waypoints[-1].transform.location)
                if distance < distance_to_relevant_traffic_light:
                    relevant_traffic_light = traffic_light
                    distance_to_relevant_traffic_light = distance
        return relevant_traffic_light

    @staticmethod
    def set_ego_vehicle_route(route):
        """
        Set the route of the ego vehicle

        @todo extend ego_vehicle_route concept to support multi ego_vehicle scenarios
        """
        CarlaDataProvider._ego_vehicle_route = route

    @staticmethod
    def get_ego_vehicle_route():
        """
        returns the currently set route of the ego vehicle
        Note: Can be None
        """
        return CarlaDataProvider._ego_vehicle_route

    @staticmethod
    def generate_spawn_points():
        """
        Generate spawn points for the current map
        """
        spawn_points = list(CarlaDataProvider.get_map(CarlaDataProvider._world).get_spawn_points())
        CarlaDataProvider._rng.shuffle(spawn_points)
        CarlaDataProvider._spawn_points = spawn_points
        CarlaDataProvider._spawn_index = 0

    @staticmethod
    def create_blueprint(model, rolename='scenario', color=None, actor_category='car'):
        """
        Function to setup the blueprint of an actor given its model and other relevant parameters
        """
        _actor_blueprint_categories = {'car': 'vehicle.tesla.model3', 'van': 'vehicle.volkswagen.t2', 'truck': 'vehicle.carlamotors.carlacola', 'trailer': '', 'semitrailer': '', 'bus': 'vehicle.volkswagen.t2', 'motorbike': 'vehicle.kawasaki.ninja', 'bicycle': 'vehicle.diamondback.century', 'train': '', 'tram': '', 'pedestrian': 'walker.pedestrian.0001'}
        try:
            blueprint = CarlaDataProvider._rng.choice(CarlaDataProvider._blueprint_library.filter(model))
        except ValueError:
            bp_filter = 'vehicle.*'
            new_model = _actor_blueprint_categories[actor_category]
            if new_model != '':
                bp_filter = new_model
            print('WARNING: Actor model {} not available. Using instead {}'.format(model, new_model))
            blueprint = CarlaDataProvider._rng.choice(CarlaDataProvider._blueprint_library.filter(bp_filter))
        if color:
            if not blueprint.has_attribute('color'):
                print('WARNING: Cannot set Color ({}) for actor {} due to missing blueprint attribute'.format(color, blueprint.id))
            else:
                default_color_rgba = blueprint.get_attribute('color').as_color()
                default_color = '({}, {}, {})'.format(default_color_rgba.r, default_color_rgba.g, default_color_rgba.b)
                try:
                    blueprint.set_attribute('color', color)
                except ValueError:
                    print('WARNING: Color ({}) cannot be set for actor {}. Using instead: ({})'.format(color, blueprint.id, default_color))
                    blueprint.set_attribute('color', default_color)
        elif blueprint.has_attribute('color') and rolename != 'hero':
            color = CarlaDataProvider._rng.choice(blueprint.get_attribute('color').recommended_values)
            blueprint.set_attribute('color', color)
        if blueprint.has_attribute('is_invincible'):
            blueprint.set_attribute('is_invincible', 'false')
        if blueprint.has_attribute('role_name'):
            blueprint.set_attribute('role_name', rolename)
        return blueprint

    @staticmethod
    def handle_actor_batch(batch):
        """
        Forward a CARLA command batch to spawn actors to CARLA, and gather the responses.
        Returns list of actors on success, none otherwise
        """
        actors = []
        sync_mode = CarlaDataProvider.is_sync_mode()
        if CarlaDataProvider._client and batch is not None:
            responses = CarlaDataProvider._client.apply_batch_sync(batch, sync_mode)
        else:
            return None
        if sync_mode:
            CarlaDataProvider._world.tick()
        else:
            CarlaDataProvider._world.wait_for_tick()
        actor_ids = []
        if responses:
            for response in responses:
                if not response.error:
                    actor_ids.append(response.actor_id)
        carla_actors = CarlaDataProvider._world.get_actors(actor_ids)
        for actor in carla_actors:
            actors.append(actor)
        return actors

    @staticmethod
    def request_new_actor(model, spawn_point, rolename='scenario', autopilot=False, random_location=False, color=None, actor_category='car'):
        """
        This method tries to create a new actor, returning it if successful (None otherwise).
        """
        blueprint = CarlaDataProvider.create_blueprint(model, rolename, color, actor_category)
        if random_location:
            actor = None
            while not actor:
                spawn_point = CarlaDataProvider._rng.choice(CarlaDataProvider._spawn_points)
                actor = CarlaDataProvider._world.try_spawn_actor(blueprint, spawn_point)
        else:
            _spawn_point = carla.Transform(carla.Location(), spawn_point.rotation)
            _spawn_point.location.x = spawn_point.location.x
            _spawn_point.location.y = spawn_point.location.y
            _spawn_point.location.z = spawn_point.location.z + 0.2
            actor = CarlaDataProvider._world.try_spawn_actor(blueprint, _spawn_point)
        if actor is None:
            raise RuntimeError('Error: Unable to spawn vehicle {} at {}'.format(blueprint.id, spawn_point))
        elif actor in CarlaDataProvider._blueprint_library.filter('vehicle.*'):
            actor.set_autopilot(autopilot)
        else:
            pass
        if CarlaDataProvider.is_sync_mode():
            CarlaDataProvider._world.tick()
        else:
            CarlaDataProvider._world.wait_for_tick()
        if actor is None:
            return None
        CarlaDataProvider._carla_actor_pool[actor.id] = actor
        CarlaDataProvider.register_actor(actor)
        return actor

    @staticmethod
    def request_new_actors(actor_list):
        """
        This method tries to series of actor in batch. If this was successful,
        the new actors are returned, None otherwise.

        param:
        - actor_list: list of ActorConfigurationData
        """
        SpawnActor = carla.command.SpawnActor
        PhysicsCommand = carla.command.SetSimulatePhysics
        FutureActor = carla.command.FutureActor
        ApplyTransform = carla.command.ApplyTransform
        SetAutopilot = carla.command.SetAutopilot
        batch = []
        actors = []
        CarlaDataProvider.generate_spawn_points()
        for actor in actor_list:
            blueprint = CarlaDataProvider.create_blueprint(actor.model, actor.rolename, actor.color, actor.category)
            transform = actor.transform
            if actor.random_location:
                if CarlaDataProvider._spawn_index >= len(CarlaDataProvider._spawn_points):
                    print('No more spawn points to use')
                    break
                else:
                    _spawn_point = CarlaDataProvider._spawn_points[CarlaDataProvider._spawn_index]
                    CarlaDataProvider._spawn_index += 1
            else:
                _spawn_point = carla.Transform()
                _spawn_point.rotation = transform.rotation
                _spawn_point.location.x = transform.location.x
                _spawn_point.location.y = transform.location.y
                _spawn_point.location.z = transform.location.z + 0.2
            command = SpawnActor(blueprint, _spawn_point)
            command.then(SetAutopilot(FutureActor, actor.autopilot, CarlaDataProvider._traffic_manager_port))
            if actor.category == 'misc':
                command.then(PhysicsCommand(FutureActor, True))
            elif actor.args is not None and 'physics' in actor.args and (actor.args['physics'] == 'off'):
                command.then(ApplyTransform(FutureActor, _spawn_point)).then(PhysicsCommand(FutureActor, False))
            batch.append(command)
        actors = CarlaDataProvider.handle_actor_batch(batch)
        if not actors:
            return None
        for actor in actors:
            if actor is None:
                continue
            CarlaDataProvider._carla_actor_pool[actor.id] = actor
            CarlaDataProvider.register_actor(actor)
        return actors

    @staticmethod
    def request_new_batch_actors(model, amount, spawn_points, autopilot=False, random_location=False, rolename='scenario'):
        """
        Simplified version of "request_new_actors". This method also create several actors in batch.

        Instead of needing a list of ActorConfigurationData, an "amount" parameter is used.
        This makes actor spawning easier but reduces the amount of configurability.

        Some parameters are the same for all actors (rolename, autopilot and random location)
        while others are randomized (color)
        """
        SpawnActor = carla.command.SpawnActor
        SetAutopilot = carla.command.SetAutopilot
        FutureActor = carla.command.FutureActor
        CarlaDataProvider.generate_spawn_points()
        batch = []
        for i in range(amount):
            blueprint = CarlaDataProvider.create_blueprint(model, rolename)
            if random_location:
                if CarlaDataProvider._spawn_index >= len(CarlaDataProvider._spawn_points):
                    print('No more spawn points to use. Spawned {} actors out of {}'.format(i + 1, amount))
                    break
                else:
                    spawn_point = CarlaDataProvider._spawn_points[CarlaDataProvider._spawn_index]
                    CarlaDataProvider._spawn_index += 1
            else:
                try:
                    spawn_point = spawn_points[i]
                except IndexError:
                    print('The amount of spawn points is lower than the amount of vehicles spawned')
                    break
            if spawn_point:
                batch.append(SpawnActor(blueprint, spawn_point).then(SetAutopilot(FutureActor, autopilot, CarlaDataProvider._traffic_manager_port)))
        actors = CarlaDataProvider.handle_actor_batch(batch)
        if actors is None:
            return None
        for actor in actors:
            if actor is None:
                continue
            CarlaDataProvider._carla_actor_pool[actor.id] = actor
            CarlaDataProvider.register_actor(actor)
        return actors

    @staticmethod
    def get_actors():
        """
        Return list of actors and their ids

        Note: iteritems from six is used to allow compatibility with Python 2 and 3
        """
        return iteritems(CarlaDataProvider._carla_actor_pool)

    @staticmethod
    def actor_id_exists(actor_id):
        """
        Check if a certain id is still at the simulation
        """
        if actor_id in CarlaDataProvider._carla_actor_pool:
            return True
        return False

    @staticmethod
    def get_hero_actor():
        """
        Get the actor object of the hero actor if it exists, returns none otherwise.
        """
        for actor_id in CarlaDataProvider._carla_actor_pool:
            if CarlaDataProvider._carla_actor_pool[actor_id].attributes['role_name'] == 'hero':
                return CarlaDataProvider._carla_actor_pool[actor_id]
        return None

    @staticmethod
    def get_actor_by_id(actor_id):
        """
        Get an actor from the pool by using its ID. If the actor
        does not exist, None is returned.
        """
        if actor_id in CarlaDataProvider._carla_actor_pool:
            return CarlaDataProvider._carla_actor_pool[actor_id]
        print('Non-existing actor id {}'.format(actor_id))
        return None

    @staticmethod
    def remove_actor_by_id(actor_id):
        """
        Remove an actor from the pool using its ID
        """
        if actor_id in CarlaDataProvider._carla_actor_pool:
            CarlaDataProvider._carla_actor_pool[actor_id].destroy()
            CarlaDataProvider._carla_actor_pool[actor_id] = None
            CarlaDataProvider._carla_actor_pool.pop(actor_id)
        else:
            print('Trying to remove a non-existing actor id {}'.format(actor_id))

    @staticmethod
    def remove_actors_in_surrounding(location, distance):
        """
        Remove all actors from the pool that are closer than distance to the
        provided location
        """
        for actor_id in CarlaDataProvider._carla_actor_pool.copy():
            if CarlaDataProvider._carla_actor_pool[actor_id].get_location().distance(location) < distance:
                CarlaDataProvider._carla_actor_pool[actor_id].destroy()
                CarlaDataProvider._carla_actor_pool.pop(actor_id)
        CarlaDataProvider._carla_actor_pool = dict({k: v for k, v in CarlaDataProvider._carla_actor_pool.items() if v})

    @staticmethod
    def get_traffic_manager_port():
        """
        Get the port of the traffic manager.
        """
        return CarlaDataProvider._traffic_manager_port

    @staticmethod
    def set_traffic_manager_port(tm_port):
        """
        Set the port to use for the traffic manager.
        """
        CarlaDataProvider._traffic_manager_port = tm_port

    @staticmethod
    def cleanup():
        """
        Cleanup and remove all entries from all dictionaries
        """
        DestroyActor = carla.command.DestroyActor
        batch = []
        for actor_id in CarlaDataProvider._carla_actor_pool.copy():
            actor = CarlaDataProvider._carla_actor_pool[actor_id]
            if actor.is_alive:
                batch.append(DestroyActor(actor))
        if CarlaDataProvider._client:
            try:
                CarlaDataProvider._client.apply_batch_sync(batch)
            except RuntimeError as e:
                if 'time-out' in str(e):
                    pass
                else:
                    raise e
        CarlaDataProvider._actor_velocity_map.clear()
        CarlaDataProvider._actor_location_map.clear()
        CarlaDataProvider._actor_transform_map.clear()
        CarlaDataProvider._traffic_light_map.clear()
        CarlaDataProvider._map = None
        CarlaDataProvider._world = None
        CarlaDataProvider._sync_flag = False
        CarlaDataProvider._ego_vehicle_route = None
        CarlaDataProvider._carla_actor_pool = dict()
        CarlaDataProvider._client = None
        CarlaDataProvider._spawn_points = None
        CarlaDataProvider._spawn_index = 0
        CarlaDataProvider._rng = random.RandomState(2000)

@staticmethod
def register_actors(actors):
    """
        Add new set of actors to dictionaries
        """
    for actor in actors:
        CarlaDataProvider.register_actor(actor)

@staticmethod
def set_world(world):
    """
        Set the world and world settings
        """
    CarlaDataProvider._world = world
    CarlaDataProvider._sync_flag = world.get_settings().synchronous_mode
    CarlaDataProvider._map = world.get_map()
    CarlaDataProvider._blueprint_library = world.get_blueprint_library()
    CarlaDataProvider.generate_spawn_points()
    CarlaDataProvider.prepare_map()

@staticmethod
def create_blueprint(model, rolename='scenario', color=None, actor_category='car'):
    """
        Function to setup the blueprint of an actor given its model and other relevant parameters
        """
    _actor_blueprint_categories = {'car': 'vehicle.tesla.model3', 'van': 'vehicle.volkswagen.t2', 'truck': 'vehicle.carlamotors.carlacola', 'trailer': '', 'semitrailer': '', 'bus': 'vehicle.volkswagen.t2', 'motorbike': 'vehicle.kawasaki.ninja', 'bicycle': 'vehicle.diamondback.century', 'train': '', 'tram': '', 'pedestrian': 'walker.pedestrian.0001'}
    try:
        blueprint = CarlaDataProvider._rng.choice(CarlaDataProvider._blueprint_library.filter(model))
    except ValueError:
        bp_filter = 'vehicle.*'
        new_model = _actor_blueprint_categories[actor_category]
        if new_model != '':
            bp_filter = new_model
        print('WARNING: Actor model {} not available. Using instead {}'.format(model, new_model))
        blueprint = CarlaDataProvider._rng.choice(CarlaDataProvider._blueprint_library.filter(bp_filter))
    if color:
        if not blueprint.has_attribute('color'):
            print('WARNING: Cannot set Color ({}) for actor {} due to missing blueprint attribute'.format(color, blueprint.id))
        else:
            default_color_rgba = blueprint.get_attribute('color').as_color()
            default_color = '({}, {}, {})'.format(default_color_rgba.r, default_color_rgba.g, default_color_rgba.b)
            try:
                blueprint.set_attribute('color', color)
            except ValueError:
                print('WARNING: Color ({}) cannot be set for actor {}. Using instead: ({})'.format(color, blueprint.id, default_color))
                blueprint.set_attribute('color', default_color)
    elif blueprint.has_attribute('color') and rolename != 'hero':
        color = CarlaDataProvider._rng.choice(blueprint.get_attribute('color').recommended_values)
        blueprint.set_attribute('color', color)
    if blueprint.has_attribute('is_invincible'):
        blueprint.set_attribute('is_invincible', 'false')
    if blueprint.has_attribute('role_name'):
        blueprint.set_attribute('role_name', rolename)
    return blueprint

@staticmethod
def handle_actor_batch(batch):
    """
        Forward a CARLA command batch to spawn actors to CARLA, and gather the responses.
        Returns list of actors on success, none otherwise
        """
    actors = []
    sync_mode = CarlaDataProvider.is_sync_mode()
    if CarlaDataProvider._client and batch is not None:
        responses = CarlaDataProvider._client.apply_batch_sync(batch, sync_mode)
    else:
        return None
    if sync_mode:
        CarlaDataProvider._world.tick()
    else:
        CarlaDataProvider._world.wait_for_tick()
    actor_ids = []
    if responses:
        for response in responses:
            if not response.error:
                actor_ids.append(response.actor_id)
    carla_actors = CarlaDataProvider._world.get_actors(actor_ids)
    for actor in carla_actors:
        actors.append(actor)
    return actors

@staticmethod
def request_new_actor(model, spawn_point, rolename='scenario', autopilot=False, random_location=False, color=None, actor_category='car'):
    """
        This method tries to create a new actor, returning it if successful (None otherwise).
        """
    blueprint = CarlaDataProvider.create_blueprint(model, rolename, color, actor_category)
    if random_location:
        actor = None
        while not actor:
            spawn_point = CarlaDataProvider._rng.choice(CarlaDataProvider._spawn_points)
            actor = CarlaDataProvider._world.try_spawn_actor(blueprint, spawn_point)
    else:
        _spawn_point = carla.Transform(carla.Location(), spawn_point.rotation)
        _spawn_point.location.x = spawn_point.location.x
        _spawn_point.location.y = spawn_point.location.y
        _spawn_point.location.z = spawn_point.location.z + 0.2
        actor = CarlaDataProvider._world.try_spawn_actor(blueprint, _spawn_point)
    if actor is None:
        raise RuntimeError('Error: Unable to spawn vehicle {} at {}'.format(blueprint.id, spawn_point))
    elif actor in CarlaDataProvider._blueprint_library.filter('vehicle.*'):
        actor.set_autopilot(autopilot)
    else:
        pass
    if CarlaDataProvider.is_sync_mode():
        CarlaDataProvider._world.tick()
    else:
        CarlaDataProvider._world.wait_for_tick()
    if actor is None:
        return None
    CarlaDataProvider._carla_actor_pool[actor.id] = actor
    CarlaDataProvider.register_actor(actor)
    return actor

@staticmethod
def request_new_actors(actor_list):
    """
        This method tries to series of actor in batch. If this was successful,
        the new actors are returned, None otherwise.

        param:
        - actor_list: list of ActorConfigurationData
        """
    SpawnActor = carla.command.SpawnActor
    PhysicsCommand = carla.command.SetSimulatePhysics
    FutureActor = carla.command.FutureActor
    ApplyTransform = carla.command.ApplyTransform
    SetAutopilot = carla.command.SetAutopilot
    batch = []
    actors = []
    CarlaDataProvider.generate_spawn_points()
    for actor in actor_list:
        blueprint = CarlaDataProvider.create_blueprint(actor.model, actor.rolename, actor.color, actor.category)
        transform = actor.transform
        if actor.random_location:
            if CarlaDataProvider._spawn_index >= len(CarlaDataProvider._spawn_points):
                print('No more spawn points to use')
                break
            else:
                _spawn_point = CarlaDataProvider._spawn_points[CarlaDataProvider._spawn_index]
                CarlaDataProvider._spawn_index += 1
        else:
            _spawn_point = carla.Transform()
            _spawn_point.rotation = transform.rotation
            _spawn_point.location.x = transform.location.x
            _spawn_point.location.y = transform.location.y
            _spawn_point.location.z = transform.location.z + 0.2
        command = SpawnActor(blueprint, _spawn_point)
        command.then(SetAutopilot(FutureActor, actor.autopilot, CarlaDataProvider._traffic_manager_port))
        if actor.category == 'misc':
            command.then(PhysicsCommand(FutureActor, True))
        elif actor.args is not None and 'physics' in actor.args and (actor.args['physics'] == 'off'):
            command.then(ApplyTransform(FutureActor, _spawn_point)).then(PhysicsCommand(FutureActor, False))
        batch.append(command)
    actors = CarlaDataProvider.handle_actor_batch(batch)
    if not actors:
        return None
    for actor in actors:
        if actor is None:
            continue
        CarlaDataProvider._carla_actor_pool[actor.id] = actor
        CarlaDataProvider.register_actor(actor)
    return actors

@staticmethod
def request_new_batch_actors(model, amount, spawn_points, autopilot=False, random_location=False, rolename='scenario'):
    """
        Simplified version of "request_new_actors". This method also create several actors in batch.

        Instead of needing a list of ActorConfigurationData, an "amount" parameter is used.
        This makes actor spawning easier but reduces the amount of configurability.

        Some parameters are the same for all actors (rolename, autopilot and random location)
        while others are randomized (color)
        """
    SpawnActor = carla.command.SpawnActor
    SetAutopilot = carla.command.SetAutopilot
    FutureActor = carla.command.FutureActor
    CarlaDataProvider.generate_spawn_points()
    batch = []
    for i in range(amount):
        blueprint = CarlaDataProvider.create_blueprint(model, rolename)
        if random_location:
            if CarlaDataProvider._spawn_index >= len(CarlaDataProvider._spawn_points):
                print('No more spawn points to use. Spawned {} actors out of {}'.format(i + 1, amount))
                break
            else:
                spawn_point = CarlaDataProvider._spawn_points[CarlaDataProvider._spawn_index]
                CarlaDataProvider._spawn_index += 1
        else:
            try:
                spawn_point = spawn_points[i]
            except IndexError:
                print('The amount of spawn points is lower than the amount of vehicles spawned')
                break
        if spawn_point:
            batch.append(SpawnActor(blueprint, spawn_point).then(SetAutopilot(FutureActor, autopilot, CarlaDataProvider._traffic_manager_port)))
    actors = CarlaDataProvider.handle_actor_batch(batch)
    if actors is None:
        return None
    for actor in actors:
        if actor is None:
            continue
        CarlaDataProvider._carla_actor_pool[actor.id] = actor
        CarlaDataProvider.register_actor(actor)
    return actors

@staticmethod
def cleanup():
    """
        Cleanup and remove all entries from all dictionaries
        """
    DestroyActor = carla.command.DestroyActor
    batch = []
    for actor_id in CarlaDataProvider._carla_actor_pool.copy():
        actor = CarlaDataProvider._carla_actor_pool[actor_id]
        if actor.is_alive:
            batch.append(DestroyActor(actor))
    if CarlaDataProvider._client:
        try:
            CarlaDataProvider._client.apply_batch_sync(batch)
        except RuntimeError as e:
            if 'time-out' in str(e):
                pass
            else:
                raise e
    CarlaDataProvider._actor_velocity_map.clear()
    CarlaDataProvider._actor_location_map.clear()
    CarlaDataProvider._actor_transform_map.clear()
    CarlaDataProvider._traffic_light_map.clear()
    CarlaDataProvider._map = None
    CarlaDataProvider._world = None
    CarlaDataProvider._sync_flag = False
    CarlaDataProvider._ego_vehicle_route = None
    CarlaDataProvider._carla_actor_pool = dict()
    CarlaDataProvider._client = None
    CarlaDataProvider._spawn_points = None
    CarlaDataProvider._spawn_index = 0
    CarlaDataProvider._rng = random.RandomState(2000)

class OSCStartEndCondition(AtomicCondition):
    """
    This class contains a check if a named story element has started/terminated.

    Important parameters:
    - element_name: The story element's name attribute
    - element_type: The element type [act,scene,maneuver,event,action]
    - rule: Either START or END

    The condition terminates with SUCCESS, when the named story element starts
    """

    def __init__(self, element_type, element_name, rule, name='OSCStartEndCondition'):
        """
        Setup element details
        """
        super(OSCStartEndCondition, self).__init__(name)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._element_type = element_type.upper()
        self._element_name = element_name
        self._rule = rule.upper()
        self._start_time = None
        self._blackboard = py_trees.blackboard.Blackboard()

    def initialise(self):
        """
        Initialize the start time of this condition
        """
        self._start_time = GameTime.get_time()
        super(OSCStartEndCondition, self).initialise()

    def update(self):
        """
        Check if the specified story element has started/ended since the beginning of the condition
        """
        new_status = py_trees.common.Status.RUNNING
        if new_status == py_trees.common.Status.RUNNING:
            blackboard_variable_name = '({}){}-{}'.format(self._element_type, self._element_name, self._rule)
            element_start_time = self._blackboard.get(blackboard_variable_name)
            if element_start_time and element_start_time >= self._start_time:
                new_status = py_trees.common.Status.SUCCESS
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

def update(self):
    """
        Check if the specified story element has started/ended since the beginning of the condition
        """
    new_status = py_trees.common.Status.RUNNING
    if new_status == py_trees.common.Status.RUNNING:
        blackboard_variable_name = '({}){}-{}'.format(self._element_type, self._element_name, self._rule)
        element_start_time = self._blackboard.get(blackboard_variable_name)
        if element_start_time and element_start_time >= self._start_time:
            new_status = py_trees.common.Status.SUCCESS
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    return new_status

class WaitForBlackboardVariable(AtomicCondition):
    """
    Atomic behavior that keeps running until the blackboard variable is set to the corresponding value.
    Used to avoid returning FAILURE if the blackboard comparison fails.

    It also initially sets the variable to a given value, if given
    """

    def __init__(self, variable_name, variable_value, var_init_value=None, debug=False, name='WaitForBlackboardVariable'):
        super(WaitForBlackboardVariable, self).__init__(name)
        self._debug = debug
        self._variable_name = variable_name
        self._variable_value = variable_value
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        if var_init_value is not None:
            blackboard = py_trees.blackboard.Blackboard()
            _ = blackboard.set(variable_name, var_init_value)

    def update(self):
        new_status = py_trees.common.Status.RUNNING
        blackv = py_trees.blackboard.Blackboard()
        value = blackv.get(self._variable_name)
        if value == self._variable_value:
            if self._debug:
                print('Blackboard variable {} set to True'.format(self._variable_name))
            new_status = py_trees.common.Status.SUCCESS
        return new_status

def update(self):
    new_status = py_trees.common.Status.RUNNING
    blackv = py_trees.blackboard.Blackboard()
    value = blackv.get(self._variable_name)
    if value == self._variable_value:
        if self._debug:
            print('Blackboard variable {} set to True'.format(self._variable_name))
        new_status = py_trees.common.Status.SUCCESS
    return new_status

class CollisionTest(Criterion):
    """
    This class contains an atomic test for collisions.

    Args:
    - actor (carla.Actor): CARLA actor to be used for this test
    - other_actor (carla.Actor): only collisions with this actor will be registered
    - other_actor_type (str): only collisions with actors including this type_id will count.
        Additionally, the "miscellaneous" tag can also be used to include all static objects in the scene
    - terminate_on_failure [optional]: If True, the complete scenario will terminate upon failure of this test
    - optional [optional]: If True, the result is not considered for an overall pass/fail result
    """
    MIN_AREA_OF_COLLISION = 3
    MAX_AREA_OF_COLLISION = 5
    MAX_ID_TIME = 5

    def __init__(self, actor, other_actor=None, other_actor_type=None, optional=False, name='CollisionTest', terminate_on_failure=False):
        """
        Construction with sensor setup
        """
        super(CollisionTest, self).__init__(name, actor, 0, None, optional, terminate_on_failure)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        world = self.actor.get_world()
        blueprint = world.get_blueprint_library().find('sensor.other.collision')
        self._collision_sensor = world.spawn_actor(blueprint, carla.Transform(), attach_to=self.actor)
        self._collision_sensor.listen(lambda event: self._count_collisions(weakref.ref(self), event))
        self.other_actor = other_actor
        self.other_actor_type = other_actor_type
        self.registered_collisions = []
        self.last_id = None
        self.collision_time = None

    def update(self):
        """
        Check collision count
        """
        new_status = py_trees.common.Status.RUNNING
        if self._terminate_on_failure and self.test_status == 'FAILURE':
            new_status = py_trees.common.Status.FAILURE
        actor_location = CarlaDataProvider.get_location(self.actor)
        new_registered_collisions = []
        for collision_location in self.registered_collisions:
            distance_vector = actor_location - collision_location
            distance = math.sqrt(math.pow(distance_vector.x, 2) + math.pow(distance_vector.y, 2))
            if distance <= self.MAX_AREA_OF_COLLISION:
                new_registered_collisions.append(collision_location)
        self.registered_collisions = new_registered_collisions
        if self.last_id and GameTime.get_time() - self.collision_time > self.MAX_ID_TIME:
            self.last_id = None
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

    def terminate(self, new_status):
        """
        Cleanup sensor
        """
        if self._collision_sensor is not None:
            self._collision_sensor.destroy()
        self._collision_sensor = None
        super(CollisionTest, self).terminate(new_status)

    @staticmethod
    def _count_collisions(weak_self, event):
        """
        Callback to update collision count
        """
        self = weak_self()
        if not self:
            return
        actor_location = CarlaDataProvider.get_location(self.actor)
        if self.last_id == event.other_actor.id:
            return
        if self.other_actor and self.other_actor.id != event.other_actor.id:
            return
        if self.other_actor_type:
            if self.other_actor_type == 'miscellaneous':
                if 'traffic' not in event.other_actor.type_id and 'static' not in event.other_actor.type_id:
                    return
            elif self.other_actor_type not in event.other_actor.type_id:
                return
        for collision_location in self.registered_collisions:
            distance_vector = actor_location - collision_location
            distance = math.sqrt(math.pow(distance_vector.x, 2) + math.pow(distance_vector.y, 2))
            if distance <= self.MIN_AREA_OF_COLLISION:
                return
        if ('static' in event.other_actor.type_id or 'traffic' in event.other_actor.type_id) and 'sidewalk' not in event.other_actor.type_id:
            actor_type = TrafficEventType.COLLISION_STATIC
        elif 'vehicle' in event.other_actor.type_id:
            actor_type = TrafficEventType.COLLISION_VEHICLE
        elif 'walker' in event.other_actor.type_id:
            actor_type = TrafficEventType.COLLISION_PEDESTRIAN
        else:
            return
        collision_event = TrafficEvent(event_type=actor_type)
        collision_event.set_dict({'type': event.other_actor.type_id, 'id': event.other_actor.id, 'x': actor_location.x, 'y': actor_location.y, 'z': actor_location.z})
        collision_event.set_message('Agent collided against object with type={} and id={} at (x={}, y={}, z={})'.format(event.other_actor.type_id, event.other_actor.id, round(actor_location.x, 3), round(actor_location.y, 3), round(actor_location.z, 3)))
        self.test_status = 'FAILURE'
        self.actual_value += 1
        self.collision_time = GameTime.get_time()
        self.registered_collisions.append(actor_location)
        self.list_traffic_events.append(collision_event)
        if event.other_actor.id != 0:
            self.last_id = event.other_actor.id

def __init__(self, actor, other_actor=None, other_actor_type=None, optional=False, name='CollisionTest', terminate_on_failure=False):
    """
        Construction with sensor setup
        """
    super(CollisionTest, self).__init__(name, actor, 0, None, optional, terminate_on_failure)
    self.logger.debug('%s.__init__()' % self.__class__.__name__)
    world = self.actor.get_world()
    blueprint = world.get_blueprint_library().find('sensor.other.collision')
    self._collision_sensor = world.spawn_actor(blueprint, carla.Transform(), attach_to=self.actor)
    self._collision_sensor.listen(lambda event: self._count_collisions(weakref.ref(self), event))
    self.other_actor = other_actor
    self.other_actor_type = other_actor_type
    self.registered_collisions = []
    self.last_id = None
    self.collision_time = None

class KeepLaneTest(Criterion):
    """
    This class contains an atomic test for keeping lane.

    Important parameters:
    - actor: CARLA actor to be used for this test
    - optional [optional]: If True, the result is not considered for an overall pass/fail result
    """

    def __init__(self, actor, optional=False, name='CheckKeepLane'):
        """
        Construction with sensor setup
        """
        super(KeepLaneTest, self).__init__(name, actor, 0, None, optional)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        world = self.actor.get_world()
        blueprint = world.get_blueprint_library().find('sensor.other.lane_invasion')
        self._lane_sensor = world.spawn_actor(blueprint, carla.Transform(), attach_to=self.actor)
        self._lane_sensor.listen(lambda event: self._count_lane_invasion(weakref.ref(self), event))

    def update(self):
        """
        Check lane invasion count
        """
        new_status = py_trees.common.Status.RUNNING
        if self.actual_value > 0:
            self.test_status = 'FAILURE'
        else:
            self.test_status = 'SUCCESS'
        if self._terminate_on_failure and self.test_status == 'FAILURE':
            new_status = py_trees.common.Status.FAILURE
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

    def terminate(self, new_status):
        """
        Cleanup sensor
        """
        if self._lane_sensor is not None:
            self._lane_sensor.destroy()
        self._lane_sensor = None
        super(KeepLaneTest, self).terminate(new_status)

    @staticmethod
    def _count_lane_invasion(weak_self, event):
        """
        Callback to update lane invasion count
        """
        self = weak_self()
        if not self:
            return
        self.actual_value += 1

def __init__(self, actor, optional=False, name='CheckKeepLane'):
    """
        Construction with sensor setup
        """
    super(KeepLaneTest, self).__init__(name, actor, 0, None, optional)
    self.logger.debug('%s.__init__()' % self.__class__.__name__)
    world = self.actor.get_world()
    blueprint = world.get_blueprint_library().find('sensor.other.lane_invasion')
    self._lane_sensor = world.spawn_actor(blueprint, carla.Transform(), attach_to=self.actor)
    self._lane_sensor.listen(lambda event: self._count_lane_invasion(weakref.ref(self), event))

class ChangeRoadFriction(AtomicBehavior):
    """
    Atomic to update the road friction in CARLA.

    The behavior immediately terminates with SUCCESS after updating the friction.

    Args:
        friction (float): New friction coefficient.
        name (string): Name of the behavior.
            Defaults to 'UpdateRoadFriction'.

    Attributes:
        _friction (float): Friction coefficient.
    """

    def __init__(self, friction, name='ChangeRoadFriction'):
        """
        Setup parameters
        """
        super(ChangeRoadFriction, self).__init__(name)
        self._friction = friction

    def update(self):
        """
        Update road friction. Spawns new friction blueprint and removes the old one, if existing.

        returns:
            py_trees.common.Status.SUCCESS
        """
        for actor in CarlaDataProvider.get_world().get_actors().filter('static.trigger.friction'):
            actor.destroy()
        friction_bp = CarlaDataProvider.get_world().get_blueprint_library().find('static.trigger.friction')
        extent = carla.Location(1000000.0, 1000000.0, 1000000.0)
        friction_bp.set_attribute('friction', str(self._friction))
        friction_bp.set_attribute('extent_x', str(extent.x))
        friction_bp.set_attribute('extent_y', str(extent.y))
        friction_bp.set_attribute('extent_z', str(extent.z))
        transform = carla.Transform()
        transform.location = carla.Location(-10000.0, -10000.0, 0.0)
        CarlaDataProvider.get_world().spawn_actor(friction_bp, transform)
        return py_trees.common.Status.SUCCESS

def update(self):
    """
        Update road friction. Spawns new friction blueprint and removes the old one, if existing.

        returns:
            py_trees.common.Status.SUCCESS
        """
    for actor in CarlaDataProvider.get_world().get_actors().filter('static.trigger.friction'):
        actor.destroy()
    friction_bp = CarlaDataProvider.get_world().get_blueprint_library().find('static.trigger.friction')
    extent = carla.Location(1000000.0, 1000000.0, 1000000.0)
    friction_bp.set_attribute('friction', str(self._friction))
    friction_bp.set_attribute('extent_x', str(extent.x))
    friction_bp.set_attribute('extent_y', str(extent.y))
    friction_bp.set_attribute('extent_z', str(extent.z))
    transform = carla.Transform()
    transform.location = carla.Location(-10000.0, -10000.0, 0.0)
    CarlaDataProvider.get_world().spawn_actor(friction_bp, transform)
    return py_trees.common.Status.SUCCESS

class CollisionTest(Criterion):
    """
    This class contains an atomic test for collisions.

    Args:
    - actor (carla.Actor): CARLA actor to be used for this test
    - other_actor (carla.Actor): only collisions with this actor will be registered
    - other_actor_type (str): only collisions with actors including this type_id will count.
        Additionally, the "miscellaneous" tag can also be used to include all static objects in the scene
    - terminate_on_failure [optional]: If True, the complete scenario will terminate upon failure of this test
    - optional [optional]: If True, the result is not considered for an overall pass/fail result
    """
    MIN_AREA_OF_COLLISION = 3
    MAX_AREA_OF_COLLISION = 5
    MAX_ID_TIME = 5

    def __init__(self, actor, other_actor=None, other_actor_type=None, optional=False, name='CollisionTest', terminate_on_failure=False):
        """
        Construction with sensor setup
        """
        super(CollisionTest, self).__init__(name, actor, 0, None, optional, terminate_on_failure)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        world = self.actor.get_world()
        blueprint = world.get_blueprint_library().find('sensor.other.collision')
        self._collision_sensor = world.spawn_actor(blueprint, carla.Transform(), attach_to=self.actor)
        self._collision_sensor.listen(lambda event: self._count_collisions(weakref.ref(self), event))
        self.other_actor = other_actor
        self.other_actor_type = other_actor_type
        self.registered_collisions = []
        self.last_id = None
        self.collision_time = None

    def update(self):
        """
        Check collision count
        """
        new_status = py_trees.common.Status.RUNNING
        if self._terminate_on_failure and self.test_status == 'FAILURE':
            new_status = py_trees.common.Status.FAILURE
        actor_location = CarlaDataProvider.get_location(self.actor)
        new_registered_collisions = []
        for collision_location in self.registered_collisions:
            distance_vector = actor_location - collision_location
            distance = math.sqrt(math.pow(distance_vector.x, 2) + math.pow(distance_vector.y, 2))
            if distance <= self.MAX_AREA_OF_COLLISION:
                new_registered_collisions.append(collision_location)
        self.registered_collisions = new_registered_collisions
        if self.last_id and GameTime.get_time() - self.collision_time > self.MAX_ID_TIME:
            self.last_id = None
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

    def terminate(self, new_status):
        """
        Cleanup sensor
        """
        if self._collision_sensor is not None:
            self._collision_sensor.destroy()
        self._collision_sensor = None
        super(CollisionTest, self).terminate(new_status)

    @staticmethod
    def _count_collisions(weak_self, event):
        """
        Callback to update collision count
        """
        self = weak_self()
        if not self:
            return
        actor_location = CarlaDataProvider.get_location(self.actor)
        if self.last_id == event.other_actor.id:
            return
        if self.other_actor and self.other_actor.id != event.other_actor.id:
            return
        if self.other_actor_type:
            if self.other_actor_type == 'miscellaneous':
                if 'traffic' not in event.other_actor.type_id and 'static' not in event.other_actor.type_id:
                    return
            elif self.other_actor_type not in event.other_actor.type_id:
                return
        for collision_location in self.registered_collisions:
            distance_vector = actor_location - collision_location
            distance = math.sqrt(math.pow(distance_vector.x, 2) + math.pow(distance_vector.y, 2))
            if distance <= self.MIN_AREA_OF_COLLISION:
                return
        if ('static' in event.other_actor.type_id or 'traffic' in event.other_actor.type_id) and 'sidewalk' not in event.other_actor.type_id:
            actor_type = TrafficEventType.COLLISION_STATIC
        elif 'vehicle' in event.other_actor.type_id:
            actor_type = TrafficEventType.COLLISION_VEHICLE
        elif 'walker' in event.other_actor.type_id:
            actor_type = TrafficEventType.COLLISION_PEDESTRIAN
        else:
            return
        collision_event = TrafficEvent(event_type=actor_type)
        collision_event.set_dict({'type': event.other_actor.type_id, 'id': event.other_actor.id, 'x': actor_location.x, 'y': actor_location.y, 'z': actor_location.z})
        collision_event.set_message('Agent collided against object with type={} and id={} at (x={}, y={}, z={})'.format(event.other_actor.type_id, event.other_actor.id, round(actor_location.x, 3), round(actor_location.y, 3), round(actor_location.z, 3)))
        self.test_status = 'FAILURE'
        self.actual_value += 1
        self.collision_time = GameTime.get_time()
        self.registered_collisions.append(actor_location)
        self.list_traffic_events.append(collision_event)
        if event.other_actor.id != 0:
            self.last_id = event.other_actor.id

def __init__(self, actor, other_actor=None, other_actor_type=None, optional=False, name='CollisionTest', terminate_on_failure=False):
    """
        Construction with sensor setup
        """
    super(CollisionTest, self).__init__(name, actor, 0, None, optional, terminate_on_failure)
    self.logger.debug('%s.__init__()' % self.__class__.__name__)
    world = self.actor.get_world()
    blueprint = world.get_blueprint_library().find('sensor.other.collision')
    self._collision_sensor = world.spawn_actor(blueprint, carla.Transform(), attach_to=self.actor)
    self._collision_sensor.listen(lambda event: self._count_collisions(weakref.ref(self), event))
    self.other_actor = other_actor
    self.other_actor_type = other_actor_type
    self.registered_collisions = []
    self.last_id = None
    self.collision_time = None

class KeepLaneTest(Criterion):
    """
    This class contains an atomic test for keeping lane.

    Important parameters:
    - actor: CARLA actor to be used for this test
    - optional [optional]: If True, the result is not considered for an overall pass/fail result
    """

    def __init__(self, actor, optional=False, name='CheckKeepLane'):
        """
        Construction with sensor setup
        """
        super(KeepLaneTest, self).__init__(name, actor, 0, None, optional)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        world = self.actor.get_world()
        blueprint = world.get_blueprint_library().find('sensor.other.lane_invasion')
        self._lane_sensor = world.spawn_actor(blueprint, carla.Transform(), attach_to=self.actor)
        self._lane_sensor.listen(lambda event: self._count_lane_invasion(weakref.ref(self), event))

    def update(self):
        """
        Check lane invasion count
        """
        new_status = py_trees.common.Status.RUNNING
        if self.actual_value > 0:
            self.test_status = 'FAILURE'
        else:
            self.test_status = 'SUCCESS'
        if self._terminate_on_failure and self.test_status == 'FAILURE':
            new_status = py_trees.common.Status.FAILURE
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

    def terminate(self, new_status):
        """
        Cleanup sensor
        """
        if self._lane_sensor is not None:
            self._lane_sensor.destroy()
        self._lane_sensor = None
        super(KeepLaneTest, self).terminate(new_status)

    @staticmethod
    def _count_lane_invasion(weak_self, event):
        """
        Callback to update lane invasion count
        """
        self = weak_self()
        if not self:
            return
        self.actual_value += 1

def __init__(self, actor, optional=False, name='CheckKeepLane'):
    """
        Construction with sensor setup
        """
    super(KeepLaneTest, self).__init__(name, actor, 0, None, optional)
    self.logger.debug('%s.__init__()' % self.__class__.__name__)
    world = self.actor.get_world()
    blueprint = world.get_blueprint_library().find('sensor.other.lane_invasion')
    self._lane_sensor = world.spawn_actor(blueprint, carla.Transform(), attach_to=self.actor)
    self._lane_sensor.listen(lambda event: self._count_lane_invasion(weakref.ref(self), event))

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

class ScenarioConfigurationParser(object):
    """
    Pure static class providing access to parser methods for scenario configuration files (*.xml)
    """

    @staticmethod
    def parse_scenario_configuration(scenario_name, config_file_name):
        """
        Parse all scenario configuration files at srunner/examples and the additional
        config files, providing a list of ScenarioConfigurations @return

        If scenario_name starts with "group:" all scenarios that
        have that type are parsed and returned. Otherwise only the
        scenario that matches the scenario_name is parsed and returned.
        """
        list_of_config_files = glob.glob('{}/srunner/examples/*.xml'.format(os.getenv('SCENARIO_RUNNER_ROOT', './')))
        if config_file_name != '':
            list_of_config_files.append(config_file_name)
        single_scenario_only = True
        if scenario_name.startswith('group:'):
            single_scenario_only = False
            scenario_name = scenario_name[6:]
        scenario_configurations = []
        for file_name in list_of_config_files:
            tree = ET.parse(file_name)
            for scenario in tree.iter('scenario'):
                scenario_config_name = scenario.attrib.get('name', None)
                scenario_config_type = scenario.attrib.get('type', None)
                if single_scenario_only:
                    if scenario_config_name != scenario_name:
                        continue
                elif scenario_config_type != scenario_name:
                    continue
                new_config = ScenarioConfiguration()
                new_config.town = scenario.attrib.get('town', None)
                new_config.name = scenario_config_name
                new_config.type = scenario_config_type
                new_config.other_actors = []
                new_config.ego_vehicles = []
                new_config.trigger_points = []
                for weather in scenario.iter('weather'):
                    new_config.weather.cloudiness = float(weather.attrib.get('cloudiness', 0))
                    new_config.weather.precipitation = float(weather.attrib.get('precipitation', 0))
                    new_config.weather.precipitation_deposits = float(weather.attrib.get('precipitation_deposits', 0))
                    new_config.weather.wind_intensity = float(weather.attrib.get('wind_intensity', 0.35))
                    new_config.weather.sun_azimuth_angle = float(weather.attrib.get('sun_azimuth_angle', 0.0))
                    new_config.weather.sun_altitude_angle = float(weather.attrib.get('sun_altitude_angle', 15.0))
                    new_config.weather.fog_density = float(weather.attrib.get('fog_density', 0.0))
                    new_config.weather.fog_distance = float(weather.attrib.get('fog_distance', 0.0))
                    new_config.weather.wetness = float(weather.attrib.get('wetness', 0.0))
                for ego_vehicle in scenario.iter('ego_vehicle'):
                    new_config.ego_vehicles.append(ActorConfigurationData.parse_from_node(ego_vehicle, 'hero'))
                    new_config.trigger_points.append(new_config.ego_vehicles[-1].transform)
                for route in scenario.iter('route'):
                    route_conf = RouteConfiguration()
                    route_conf.parse_xml(route)
                    new_config.route = route_conf
                for other_actor in scenario.iter('other_actor'):
                    new_config.other_actors.append(ActorConfigurationData.parse_from_node(other_actor, 'scenario'))
                scenario_configurations.append(new_config)
        return scenario_configurations

    @staticmethod
    def get_list_of_scenarios(config_file_name):
        """
        Parse *all* config files and provide a list with all scenarios @return
        """
        list_of_config_files = glob.glob('{}/srunner/examples/*.xml'.format(os.getenv('SCENARIO_RUNNER_ROOT', './')))
        list_of_config_files += glob.glob('{}/srunner/examples/*.xosc'.format(os.getenv('SCENARIO_RUNNER_ROOT', './')))
        if config_file_name != '':
            list_of_config_files.append(config_file_name)
        scenarios = []
        for file_name in list_of_config_files:
            if '.xosc' in file_name:
                tree = ET.parse(file_name)
                scenarios.append('{} (OpenSCENARIO)'.format(tree.find('FileHeader').attrib.get('description', None)))
            else:
                tree = ET.parse(file_name)
                for scenario in tree.iter('scenario'):
                    scenarios.append(scenario.attrib.get('name', None))
        return scenarios

@staticmethod
def parse_scenario_configuration(scenario_name, config_file_name):
    """
        Parse all scenario configuration files at srunner/examples and the additional
        config files, providing a list of ScenarioConfigurations @return

        If scenario_name starts with "group:" all scenarios that
        have that type are parsed and returned. Otherwise only the
        scenario that matches the scenario_name is parsed and returned.
        """
    list_of_config_files = glob.glob('{}/srunner/examples/*.xml'.format(os.getenv('SCENARIO_RUNNER_ROOT', './')))
    if config_file_name != '':
        list_of_config_files.append(config_file_name)
    single_scenario_only = True
    if scenario_name.startswith('group:'):
        single_scenario_only = False
        scenario_name = scenario_name[6:]
    scenario_configurations = []
    for file_name in list_of_config_files:
        tree = ET.parse(file_name)
        for scenario in tree.iter('scenario'):
            scenario_config_name = scenario.attrib.get('name', None)
            scenario_config_type = scenario.attrib.get('type', None)
            if single_scenario_only:
                if scenario_config_name != scenario_name:
                    continue
            elif scenario_config_type != scenario_name:
                continue
            new_config = ScenarioConfiguration()
            new_config.town = scenario.attrib.get('town', None)
            new_config.name = scenario_config_name
            new_config.type = scenario_config_type
            new_config.other_actors = []
            new_config.ego_vehicles = []
            new_config.trigger_points = []
            for weather in scenario.iter('weather'):
                new_config.weather.cloudiness = float(weather.attrib.get('cloudiness', 0))
                new_config.weather.precipitation = float(weather.attrib.get('precipitation', 0))
                new_config.weather.precipitation_deposits = float(weather.attrib.get('precipitation_deposits', 0))
                new_config.weather.wind_intensity = float(weather.attrib.get('wind_intensity', 0.35))
                new_config.weather.sun_azimuth_angle = float(weather.attrib.get('sun_azimuth_angle', 0.0))
                new_config.weather.sun_altitude_angle = float(weather.attrib.get('sun_altitude_angle', 15.0))
                new_config.weather.fog_density = float(weather.attrib.get('fog_density', 0.0))
                new_config.weather.fog_distance = float(weather.attrib.get('fog_distance', 0.0))
                new_config.weather.wetness = float(weather.attrib.get('wetness', 0.0))
            for ego_vehicle in scenario.iter('ego_vehicle'):
                new_config.ego_vehicles.append(ActorConfigurationData.parse_from_node(ego_vehicle, 'hero'))
                new_config.trigger_points.append(new_config.ego_vehicles[-1].transform)
            for route in scenario.iter('route'):
                route_conf = RouteConfiguration()
                route_conf.parse_xml(route)
                new_config.route = route_conf
            for other_actor in scenario.iter('other_actor'):
                new_config.other_actors.append(ActorConfigurationData.parse_from_node(other_actor, 'scenario'))
            scenario_configurations.append(new_config)
    return scenario_configurations

@staticmethod
def get_list_of_scenarios(config_file_name):
    """
        Parse *all* config files and provide a list with all scenarios @return
        """
    list_of_config_files = glob.glob('{}/srunner/examples/*.xml'.format(os.getenv('SCENARIO_RUNNER_ROOT', './')))
    list_of_config_files += glob.glob('{}/srunner/examples/*.xosc'.format(os.getenv('SCENARIO_RUNNER_ROOT', './')))
    if config_file_name != '':
        list_of_config_files.append(config_file_name)
    scenarios = []
    for file_name in list_of_config_files:
        if '.xosc' in file_name:
            tree = ET.parse(file_name)
            scenarios.append('{} (OpenSCENARIO)'.format(tree.find('FileHeader').attrib.get('description', None)))
        else:
            tree = ET.parse(file_name)
            for scenario in tree.iter('scenario'):
                scenarios.append(scenario.attrib.get('name', None))
    return scenarios

class OpenScenarioParser(object):
    """
    Pure static class providing conversions from OpenSCENARIO elements to ScenarioRunner elements
    """
    operators = {'greaterThan': operator.gt, 'lessThan': operator.lt, 'equalTo': operator.eq}
    actor_types = {'pedestrian': 'walker', 'vehicle': 'vehicle', 'miscellaneous': 'miscellaneous'}
    tl_states = {'GREEN': carla.TrafficLightState.Green, 'YELLOW': carla.TrafficLightState.Yellow, 'RED': carla.TrafficLightState.Red, 'OFF': carla.TrafficLightState.Off}
    global_osc_parameters = dict()
    use_carla_coordinate_system = False
    osc_filepath = None

    @staticmethod
    def get_traffic_light_from_osc_name(name):
        """
        Returns a carla.TrafficLight instance that matches the name given
        """
        traffic_light = None
        if name.startswith('id='):
            tl_id = name[3:]
            for carla_tl in CarlaDataProvider.get_world().get_actors().filter('traffic.traffic_light'):
                if carla_tl.id == tl_id:
                    traffic_light = carla_tl
                    break
        elif name.startswith('pos='):
            tl_pos = name[4:]
            pos = tl_pos.split(',')
            for carla_tl in CarlaDataProvider.get_world().get_actors().filter('traffic.traffic_light'):
                carla_tl_location = carla_tl.get_transform().location
                distance = carla_tl_location.distance(carla.Location(float(pos[0]), float(pos[1]), carla_tl_location.z))
                if distance < 2.0:
                    traffic_light = carla_tl
                    break
        if traffic_light is None:
            raise AttributeError('Unknown  traffic light {}'.format(name))
        return traffic_light

    @staticmethod
    def set_osc_filepath(filepath):
        """
        Set path of OSC file. This is required if for example custom commands are provided with
        relative paths.
        """
        OpenScenarioParser.osc_filepath = filepath

    @staticmethod
    def set_use_carla_coordinate_system():
        """
        CARLA internally uses a left-hand coordinate system (Unreal), but OpenSCENARIO and OpenDRIVE
        are intended for right-hand coordinate system. Hence, we need to invert the coordinates, if
        the scenario does not use CARLA coordinates, but instead right-hand coordinates.
        """
        OpenScenarioParser.use_carla_coordinate_system = True

    @staticmethod
    def set_parameters(xml_tree, additional_parameter_dict=None):
        """
        Parse the xml_tree, and replace all parameter references
        with the actual values.

        Note: Parameter names must not start with "$", however when referencing a parameter the
              reference has to start with "$".
              https://releases.asam.net/OpenSCENARIO/1.0.0/ASAM_OpenSCENARIO_BS-1-2_User-Guide_V1-0-0.html#_re_use_mechanisms

        Args:
            xml_tree: Containing all nodes that should be updated
            additional_parameter_dict (dictionary): Additional parameters as dict (key, value). Optional.

        returns:
            updated xml_tree, dictonary containing all parameters and their values
        """
        parameter_dict = dict()
        if additional_parameter_dict is not None:
            parameter_dict = additional_parameter_dict
        parameters = xml_tree.find('ParameterDeclarations')
        if parameters is None and (not parameter_dict):
            return (xml_tree, parameter_dict)
        if parameters is None:
            parameters = []
        for parameter in parameters:
            name = parameter.attrib.get('name')
            value = parameter.attrib.get('value')
            parameter_dict[name] = value
        for node in xml_tree.iter():
            for key in node.attrib:
                for param in sorted(parameter_dict, key=len, reverse=True):
                    if '$' + param in node.attrib[key]:
                        node.attrib[key] = node.attrib[key].replace('$' + param, parameter_dict[param])
        return (xml_tree, parameter_dict)

    @staticmethod
    def set_global_parameters(parameter_dict):
        """
        Set global_osc_parameter dictionary

        Args:
            parameter_dict (Dictionary): Input for global_osc_parameter
        """
        OpenScenarioParser.global_osc_parameters = parameter_dict

    @staticmethod
    def get_catalog_entry(catalogs, catalog_reference):
        """
        Get catalog entry referenced by catalog_reference included correct parameter settings

        Args:
            catalogs (Dictionary of dictionaries): List of all catalogs and their entries
            catalog_reference (XML ElementTree): Reference containing the exact catalog to be used

        returns:
            Catalog entry (XML ElementTree)
        """
        entry = catalogs[catalog_reference.attrib.get('catalogName')][catalog_reference.attrib.get('entryName')]
        entry_copy = copy.deepcopy(entry)
        catalog_copy = copy.deepcopy(catalog_reference)
        entry = OpenScenarioParser.assign_catalog_parameters(entry_copy, catalog_copy)
        return entry

    @staticmethod
    def assign_catalog_parameters(entry_instance, catalog_reference):
        """
        Parse catalog_reference, and replace all parameter references
        in entry_instance by the values provided in catalog_reference.

        Not to be used from outside this class.

        Args:
            entry_instance (XML ElementTree): Entry to be updated
            catalog_reference (XML ElementTree): Reference containing the exact parameter values

        returns:
            updated entry_instance with updated parameter values
        """
        parameter_dict = dict()
        for elem in entry_instance.iter():
            if elem.find('ParameterDeclarations') is not None:
                parameters = elem.find('ParameterDeclarations')
                for parameter in parameters:
                    name = parameter.attrib.get('name')
                    value = parameter.attrib.get('value')
                    parameter_dict[name] = value
        for parameter_assignments in catalog_reference.iter('ParameterAssignments'):
            for parameter_assignment in parameter_assignments.iter('ParameterAssignment'):
                parameter = parameter_assignment.attrib.get('parameterRef')
                value = parameter_assignment.attrib.get('value')
                parameter_dict[parameter] = value
        for node in entry_instance.iter():
            for key in node.attrib:
                for param in sorted(parameter_dict, key=len, reverse=True):
                    if '$' + param in node.attrib[key]:
                        node.attrib[key] = node.attrib[key].replace('$' + param, parameter_dict[param])
        OpenScenarioParser.set_parameters(entry_instance, OpenScenarioParser.global_osc_parameters)
        return entry_instance

    @staticmethod
    def get_friction_from_env_action(xml_tree, catalogs):
        """
        Extract the CARLA road friction coefficient from an OSC EnvironmentAction

        Args:
            xml_tree: Containing the EnvironmentAction,
                or the reference to the catalog it is defined in.
            catalogs: XML Catalogs that could contain the EnvironmentAction

        returns:
           friction (float)
        """
        set_environment = next(xml_tree.iter('EnvironmentAction'))
        if sum((1 for _ in set_environment.iter('Weather'))) != 0:
            environment = set_environment.find('Environment')
        elif set_environment.find('CatalogReference') is not None:
            catalog_reference = set_environment.find('CatalogReference')
            environment = OpenScenarioParser.get_catalog_entry(catalogs, catalog_reference)
        friction = 1.0
        road_condition = environment.iter('RoadCondition')
        for condition in road_condition:
            friction = condition.attrib.get('frictionScaleFactor')
        return friction

    @staticmethod
    def get_weather_from_env_action(xml_tree, catalogs):
        """
        Extract the CARLA weather parameters from an OSC EnvironmentAction

        Args:
            xml_tree: Containing the EnvironmentAction,
                or the reference to the catalog it is defined in.
            catalogs: XML Catalogs that could contain the EnvironmentAction

        returns:
           Weather (srunner.scenariomanager.weather_sim.Weather)
        """
        set_environment = next(xml_tree.iter('EnvironmentAction'))
        if sum((1 for _ in set_environment.iter('Weather'))) != 0:
            environment = set_environment.find('Environment')
        elif set_environment.find('CatalogReference') is not None:
            catalog_reference = set_environment.find('CatalogReference')
            environment = OpenScenarioParser.get_catalog_entry(catalogs, catalog_reference)
        weather = environment.find('Weather')
        sun = weather.find('Sun')
        carla_weather = carla.WeatherParameters()
        carla_weather.sun_azimuth_angle = math.degrees(float(sun.attrib.get('azimuth', 0)))
        carla_weather.sun_altitude_angle = math.degrees(float(sun.attrib.get('elevation', 0)))
        carla_weather.cloudiness = 100 - float(sun.attrib.get('intensity', 0)) * 100
        fog = weather.find('Fog')
        carla_weather.fog_distance = float(fog.attrib.get('visualRange', 'inf'))
        if carla_weather.fog_distance < 1000:
            carla_weather.fog_density = 100
        carla_weather.precipitation = 0
        carla_weather.precipitation_deposits = 0
        carla_weather.wetness = 0
        carla_weather.wind_intensity = 0
        precepitation = weather.find('Precipitation')
        if precepitation.attrib.get('precipitationType') == 'rain':
            carla_weather.precipitation = float(precepitation.attrib.get('intensity')) * 100
            carla_weather.precipitation_deposits = 100
            carla_weather.wetness = carla_weather.precipitation
        elif precepitation.attrib.get('type') == 'snow':
            raise AttributeError('CARLA does not support snow precipitation')
        time_of_day = environment.find('TimeOfDay')
        weather_animation = strtobool(time_of_day.attrib.get('animation'))
        time = time_of_day.attrib.get('dateTime')
        dtime = datetime.datetime.strptime(time, '%Y-%m-%dT%H:%M:%S')
        return Weather(carla_weather, dtime, weather_animation)

    @staticmethod
    def get_controller(xml_tree, catalogs):
        """
        Extract the object controller from the OSC XML or a catalog

        Args:
            xml_tree: Containing the controller information,
                or the reference to the catalog it is defined in.
            catalogs: XML Catalogs that could contain the EnvironmentAction

        returns:
           module: Python module containing the controller implementation
           args: Dictonary with (key, value) parameters for the controller
        """
        assign_action = next(xml_tree.iter('AssignControllerAction'))
        properties = None
        if assign_action.find('Controller') is not None:
            properties = assign_action.find('Controller').find('Properties')
        elif assign_action.find('CatalogReference') is not None:
            catalog_reference = assign_action.find('CatalogReference')
            properties = OpenScenarioParser.get_catalog_entry(catalogs, catalog_reference).find('Properties')
        module = None
        args = {}
        for prop in properties:
            if prop.attrib.get('name') == 'module':
                module = prop.attrib.get('value')
            else:
                args[prop.attrib.get('name')] = prop.attrib.get('value')
        override_action = xml_tree.find('OverrideControllerValueAction')
        for child in override_action:
            if strtobool(child.attrib.get('active')):
                raise NotImplementedError('Controller override actions are not yet supported')
        return (module, args)

    @staticmethod
    def get_route(xml_tree, catalogs):
        """
        Extract the route from the OSC XML or a catalog

        Args:
            xml_tree: Containing the route information,
                or the reference to the catalog it is defined in.
            catalogs: XML Catalogs that could contain the Route

        returns:
           waypoints: List of route waypoints
        """
        route = None
        if xml_tree.find('Route') is not None:
            route = xml_tree.find('Route')
        elif xml_tree.find('CatalogReference') is not None:
            catalog_reference = xml_tree.find('CatalogReference')
            route = OpenScenarioParser.get_catalog_entry(catalogs, catalog_reference)
        else:
            raise AttributeError('Unknown private FollowRoute action')
        waypoints = []
        if route is not None:
            for waypoint in route.iter('Waypoint'):
                position = waypoint.find('Position')
                transform = OpenScenarioParser.convert_position_to_transform(position)
                waypoints.append(transform)
        return waypoints

    @staticmethod
    def convert_position_to_transform(position, actor_list=None):
        """
        Convert an OpenScenario position into a CARLA transform

        Not supported: Road, RelativeRoad, Lane, RelativeLane as the PythonAPI currently
                       does not provide sufficient access to OpenDrive information
                       Also not supported is Route. This can be added by checking additional
                       route information
        """
        if position.find('WorldPosition') is not None:
            world_pos = position.find('WorldPosition')
            x = float(world_pos.attrib.get('x', 0))
            y = float(world_pos.attrib.get('y', 0))
            z = float(world_pos.attrib.get('z', 0))
            yaw = math.degrees(float(world_pos.attrib.get('h', 0)))
            pitch = math.degrees(float(world_pos.attrib.get('p', 0)))
            roll = math.degrees(float(world_pos.attrib.get('r', 0)))
            if not OpenScenarioParser.use_carla_coordinate_system:
                y = y * -1.0
                yaw = yaw * -1.0
            return carla.Transform(carla.Location(x=x, y=y, z=z), carla.Rotation(yaw=yaw, pitch=pitch, roll=roll))
        elif position.find('RelativeWorldPosition') is not None or position.find('RelativeObjectPosition') is not None or position.find('RelativeLanePosition') is not None:
            if position.find('RelativeWorldPosition') is not None:
                rel_pos = position.find('RelativeWorldPosition')
            if position.find('RelativeObjectPosition') is not None:
                rel_pos = position.find('RelativeObjectPosition')
            if position.find('RelativeLanePosition') is not None:
                rel_pos = position.find('RelativeLanePosition')
            obj = rel_pos.attrib.get('entityRef')
            obj_actor = None
            actor_transform = None
            if actor_list is not None:
                for actor in actor_list:
                    if actor.rolename == obj:
                        obj_actor = actor
                        actor_transform = actor.transform
            else:
                for actor in CarlaDataProvider.get_world().get_actors():
                    if 'role_name' in actor.attributes and actor.attributes['role_name'] == obj:
                        obj_actor = actor
                        actor_transform = obj_actor.get_transform()
                        break
            if obj_actor is None:
                raise AttributeError("Object '{}' provided as position reference is not known".format(obj))
            is_absolute = False
            dyaw = 0
            dpitch = 0
            droll = 0
            if rel_pos.find('Orientation') is not None:
                orientation = rel_pos.find('Orientation')
                is_absolute = orientation.attrib.get('type') == 'absolute'
                dyaw = math.degrees(float(orientation.attrib.get('h', 0)))
                dpitch = math.degrees(float(orientation.attrib.get('p', 0)))
                droll = math.degrees(float(orientation.attrib.get('r', 0)))
            if not OpenScenarioParser.use_carla_coordinate_system:
                dyaw = dyaw * -1.0
            yaw = actor_transform.rotation.yaw
            pitch = actor_transform.rotation.pitch
            roll = actor_transform.rotation.roll
            if not is_absolute:
                yaw = yaw + dyaw
                pitch = pitch + dpitch
                roll = roll + droll
            else:
                yaw = dyaw
                pitch = dpitch
                roll = droll
            if position.find('RelativeWorldPosition') is not None or position.find('RelativeObjectPosition') is not None:
                dx = float(rel_pos.attrib.get('dx', 0))
                dy = float(rel_pos.attrib.get('dy', 0))
                dz = float(rel_pos.attrib.get('dz', 0))
                if not OpenScenarioParser.use_carla_coordinate_system:
                    dy = dy * -1.0
                x = actor_transform.location.x + dx
                y = actor_transform.location.y + dy
                z = actor_transform.location.z + dz
            elif position.find('RelativeLanePosition') is not None:
                dlane = float(rel_pos.attrib.get('dLane'))
                ds = float(rel_pos.attrib.get('ds'))
                offset = float(rel_pos.attrib.get('offset', 0.0))
                carla_map = CarlaDataProvider.get_map()
                relative_waypoint = carla_map.get_waypoint(actor_transform.location)
                if dlane == 0:
                    wp = relative_waypoint
                elif dlane == -1:
                    wp = relative_waypoint.get_left_lane()
                elif dlane == 1:
                    wp = relative_waypoint.get_right_lane()
                if wp is None:
                    raise AttributeError("Object '{}' position with dLane={} is not valid".format(obj, dlane))
                if ds < 0:
                    ds = -1.0 * ds
                    wp = wp.previous(ds)[-1]
                else:
                    wp = wp.next(ds)[-1]
                h = math.radians(wp.transform.rotation.yaw)
                x_offset = math.sin(h) * offset
                y_offset = math.cos(h) * offset
                if OpenScenarioParser.use_carla_coordinate_system:
                    x_offset = x_offset * -1.0
                    y_offset = y_offset * -1.0
                x = wp.transform.location.x + x_offset
                y = wp.transform.location.y + y_offset
                z = wp.transform.location.z
            return carla.Transform(carla.Location(x=x, y=y, z=z), carla.Rotation(yaw=yaw, pitch=pitch, roll=roll))
        elif position.find('RoadPosition') is not None:
            raise NotImplementedError('Road positions are not yet supported')
        elif position.find('RelativeRoadPosition') is not None:
            raise NotImplementedError('RelativeRoad positions are not yet supported')
        elif position.find('LanePosition') is not None:
            lane_pos = position.find('LanePosition')
            road_id = int(lane_pos.attrib.get('roadId', 0))
            lane_id = int(lane_pos.attrib.get('laneId', 0))
            offset = float(lane_pos.attrib.get('offset', 0))
            s = float(lane_pos.attrib.get('s', 0))
            is_absolute = True
            waypoint = CarlaDataProvider.get_map().get_waypoint_xodr(road_id, lane_id, s)
            if waypoint is None:
                raise AttributeError('Lane position cannot be found')
            transform = waypoint.transform
            if lane_pos.find('Orientation') is not None:
                orientation = lane_pos.find('Orientation')
                dyaw = math.degrees(float(orientation.attrib.get('h', 0)))
                dpitch = math.degrees(float(orientation.attrib.get('p', 0)))
                droll = math.degrees(float(orientation.attrib.get('r', 0)))
                if not OpenScenarioParser.use_carla_coordinate_system:
                    dyaw = dyaw * -1.0
                transform.rotation.yaw = transform.rotation.yaw + dyaw
                transform.rotation.pitch = transform.rotation.pitch + dpitch
                transform.rotation.roll = transform.rotation.roll + droll
            if offset != 0:
                forward_vector = transform.rotation.get_forward_vector()
                orthogonal_vector = carla.Vector3D(x=-forward_vector.y, y=forward_vector.x, z=forward_vector.z)
                transform.location.x = transform.location.x + offset * orthogonal_vector.x
                transform.location.y = transform.location.y + offset * orthogonal_vector.y
            return transform
        elif position.find('RoutePosition') is not None:
            raise NotImplementedError('Route positions are not yet supported')
        else:
            raise AttributeError('Unknown position')

    @staticmethod
    def convert_condition_to_atomic(condition, actor_list):
        """
        Convert an OpenSCENARIO condition into a Behavior/Criterion atomic

        If there is a delay defined in the condition, then the condition is checked after the delay time
        passed by, e.g. <Condition name="" delay="5">.

        Note: Not all conditions are currently supported.
        """
        atomic = None
        delay_atomic = None
        condition_name = condition.attrib.get('name')
        if condition.attrib.get('delay') is not None and str(condition.attrib.get('delay')) != '0':
            delay = float(condition.attrib.get('delay'))
            delay_atomic = TimeOut(delay)
        if condition.find('ByEntityCondition') is not None:
            trigger_actor = None
            triggered_actor = None
            for triggering_entities in condition.find('ByEntityCondition').iter('TriggeringEntities'):
                for entity in triggering_entities.iter('EntityRef'):
                    for actor in actor_list:
                        if entity.attrib.get('entityRef', None) == actor.attributes['role_name']:
                            trigger_actor = actor
                            break
            for entity_condition in condition.find('ByEntityCondition').iter('EntityCondition'):
                if entity_condition.find('EndOfRoadCondition') is not None:
                    end_road_condition = entity_condition.find('EndOfRoadCondition')
                    condition_duration = float(end_road_condition.attrib.get('duration'))
                    atomic_cls = py_trees.meta.inverter(EndofRoadTest)
                    atomic = atomic_cls(trigger_actor, condition_duration, terminate_on_failure=True, name=condition_name)
                elif entity_condition.find('CollisionCondition') is not None:
                    collision_condition = entity_condition.find('CollisionCondition')
                    if collision_condition.find('EntityRef') is not None:
                        collision_entity = collision_condition.find('EntityRef')
                        for actor in actor_list:
                            if collision_entity.attrib.get('entityRef', None) == actor.attributes['role_name']:
                                triggered_actor = actor
                                break
                        if triggered_actor is None:
                            raise AttributeError("Cannot find actor '{}' for condition".format(collision_condition.attrib.get('entityRef', None)))
                        atomic_cls = py_trees.meta.inverter(CollisionTest)
                        atomic = atomic_cls(trigger_actor, other_actor=triggered_actor, terminate_on_failure=True, name=condition_name)
                    elif collision_condition.find('ByType') is not None:
                        collision_type = collision_condition.find('ByType').attrib.get('type', None)
                        triggered_type = OpenScenarioParser.actor_types[collision_type]
                        atomic_cls = py_trees.meta.inverter(CollisionTest)
                        atomic = atomic_cls(trigger_actor, other_actor_type=triggered_type, terminate_on_failure=True, name=condition_name)
                    else:
                        atomic_cls = py_trees.meta.inverter(CollisionTest)
                        atomic = atomic_cls(trigger_actor, terminate_on_failure=True, name=condition_name)
                elif entity_condition.find('OffroadCondition') is not None:
                    off_condition = entity_condition.find('OffroadCondition')
                    condition_duration = float(off_condition.attrib.get('duration'))
                    atomic_cls = py_trees.meta.inverter(OffRoadTest)
                    atomic = atomic_cls(trigger_actor, condition_duration, terminate_on_failure=True, name=condition_name)
                elif entity_condition.find('TimeHeadwayCondition') is not None:
                    headtime_condition = entity_condition.find('TimeHeadwayCondition')
                    condition_value = float(headtime_condition.attrib.get('value'))
                    condition_rule = headtime_condition.attrib.get('rule')
                    condition_operator = OpenScenarioParser.operators[condition_rule]
                    condition_freespace = strtobool(headtime_condition.attrib.get('freespace', False))
                    if condition_freespace:
                        raise NotImplementedError('TimeHeadwayCondition: freespace attribute is currently not implemented')
                    condition_along_route = strtobool(headtime_condition.attrib.get('alongRoute', False))
                    for actor in actor_list:
                        if headtime_condition.attrib.get('entityRef', None) == actor.attributes['role_name']:
                            triggered_actor = actor
                            break
                    if triggered_actor is None:
                        raise AttributeError("Cannot find actor '{}' for condition".format(headtime_condition.attrib.get('entityRef', None)))
                    atomic = InTimeToArrivalToVehicle(trigger_actor, triggered_actor, condition_value, condition_along_route, condition_operator, condition_name)
                elif entity_condition.find('TimeToCollisionCondition') is not None:
                    ttc_condition = entity_condition.find('TimeToCollisionCondition')
                    condition_rule = ttc_condition.attrib.get('rule')
                    condition_operator = OpenScenarioParser.operators[condition_rule]
                    condition_value = ttc_condition.attrib.get('value')
                    condition_target = ttc_condition.find('TimeToCollisionConditionTarget')
                    condition_freespace = strtobool(ttc_condition.attrib.get('freespace', False))
                    if condition_freespace:
                        raise NotImplementedError('TimeToCollisionCondition: freespace attribute is currently not implemented')
                    condition_along_route = strtobool(ttc_condition.attrib.get('alongRoute', False))
                    if condition_target.find('Position') is not None:
                        position = condition_target.find('Position')
                        atomic = InTimeToArrivalToOSCPosition(trigger_actor, position, condition_value, condition_along_route, condition_operator)
                    else:
                        for actor in actor_list:
                            if ttc_condition.attrib.get('EntityRef', None) == actor.attributes['role_name']:
                                triggered_actor = actor
                                break
                        if triggered_actor is None:
                            raise AttributeError("Cannot find actor '{}' for condition".format(ttc_condition.attrib.get('EntityRef', None)))
                        atomic = InTimeToArrivalToVehicle(trigger_actor, triggered_actor, condition_value, condition_along_route, condition_operator, condition_name)
                elif entity_condition.find('AccelerationCondition') is not None:
                    accel_condition = entity_condition.find('AccelerationCondition')
                    condition_value = float(accel_condition.attrib.get('value'))
                    condition_rule = accel_condition.attrib.get('rule')
                    condition_operator = OpenScenarioParser.operators[condition_rule]
                    atomic = TriggerAcceleration(trigger_actor, condition_value, condition_operator, condition_name)
                elif entity_condition.find('StandStillCondition') is not None:
                    ss_condition = entity_condition.find('StandStillCondition')
                    duration = float(ss_condition.attrib.get('duration'))
                    atomic = StandStill(trigger_actor, condition_name, duration)
                elif entity_condition.find('SpeedCondition') is not None:
                    spd_condition = entity_condition.find('SpeedCondition')
                    condition_value = float(spd_condition.attrib.get('value'))
                    condition_rule = spd_condition.attrib.get('rule')
                    condition_operator = OpenScenarioParser.operators[condition_rule]
                    atomic = TriggerVelocity(trigger_actor, condition_value, condition_operator, condition_name)
                elif entity_condition.find('RelativeSpeedCondition') is not None:
                    relspd_condition = entity_condition.find('RelativeSpeedCondition')
                    condition_value = float(relspd_condition.attrib.get('value'))
                    condition_rule = relspd_condition.attrib.get('rule')
                    condition_operator = OpenScenarioParser.operators[condition_rule]
                    for actor in actor_list:
                        if relspd_condition.attrib.get('entityRef', None) == actor.attributes['role_name']:
                            triggered_actor = actor
                            break
                    if triggered_actor is None:
                        raise AttributeError("Cannot find actor '{}' for condition".format(relspd_condition.attrib.get('entityRef', None)))
                    atomic = RelativeVelocityToOtherActor(trigger_actor, triggered_actor, condition_value, condition_operator, condition_name)
                elif entity_condition.find('TraveledDistanceCondition') is not None:
                    distance_condition = entity_condition.find('TraveledDistanceCondition')
                    distance_value = float(distance_condition.attrib.get('value'))
                    atomic = DriveDistance(trigger_actor, distance_value, name=condition_name)
                elif entity_condition.find('ReachPositionCondition') is not None:
                    rp_condition = entity_condition.find('ReachPositionCondition')
                    distance_value = float(rp_condition.attrib.get('tolerance'))
                    position = rp_condition.find('Position')
                    atomic = InTriggerDistanceToOSCPosition(trigger_actor, position, distance_value, name=condition_name)
                elif entity_condition.find('DistanceCondition') is not None:
                    distance_condition = entity_condition.find('DistanceCondition')
                    distance_value = float(distance_condition.attrib.get('value'))
                    distance_rule = distance_condition.attrib.get('rule')
                    distance_operator = OpenScenarioParser.operators[distance_rule]
                    distance_freespace = strtobool(distance_condition.attrib.get('freespace', False))
                    if distance_freespace:
                        raise NotImplementedError('DistanceCondition: freespace attribute is currently not implemented')
                    distance_along_route = strtobool(distance_condition.attrib.get('alongRoute', False))
                    if distance_condition.find('Position') is not None:
                        position = distance_condition.find('Position')
                        atomic = InTriggerDistanceToOSCPosition(trigger_actor, position, distance_value, distance_along_route, distance_operator, name=condition_name)
                elif entity_condition.find('RelativeDistanceCondition') is not None:
                    distance_condition = entity_condition.find('RelativeDistanceCondition')
                    distance_value = float(distance_condition.attrib.get('value'))
                    distance_freespace = strtobool(distance_condition.attrib.get('freespace', False))
                    if distance_freespace:
                        raise NotImplementedError('RelativeDistanceCondition: freespace attribute is currently not implemented')
                    if distance_condition.attrib.get('relativeDistanceType') == 'cartesianDistance':
                        for actor in actor_list:
                            if distance_condition.attrib.get('entityRef', None) == actor.attributes['role_name']:
                                triggered_actor = actor
                                break
                        if triggered_actor is None:
                            raise AttributeError("Cannot find actor '{}' for condition".format(distance_condition.attrib.get('entityRef', None)))
                        condition_rule = distance_condition.attrib.get('rule')
                        condition_operator = OpenScenarioParser.operators[condition_rule]
                        atomic = InTriggerDistanceToVehicle(triggered_actor, trigger_actor, distance_value, condition_operator, name=condition_name)
                    else:
                        raise NotImplementedError('RelativeDistance condition with the given specification is not yet supported')
        elif condition.find('ByValueCondition') is not None:
            value_condition = condition.find('ByValueCondition')
            if value_condition.find('ParameterCondition') is not None:
                parameter_condition = value_condition.find('ParameterCondition')
                arg_name = parameter_condition.attrib.get('parameterRef')
                value = parameter_condition.attrib.get('value')
                if value != '':
                    arg_value = float(value)
                else:
                    arg_value = 0
                parameter_condition.attrib.get('rule')
                if condition_name in globals():
                    criterion_instance = globals()[condition_name]
                else:
                    raise AttributeError('The condition {} cannot be mapped to a criterion atomic'.format(condition_name))
                atomic = py_trees.composites.Parallel('Evaluation Criteria for multiple ego vehicles')
                for triggered_actor in actor_list:
                    if arg_name != '':
                        atomic.add_child(criterion_instance(triggered_actor, arg_value))
                    else:
                        atomic.add_child(criterion_instance(triggered_actor))
            elif value_condition.find('SimulationTimeCondition') is not None:
                simtime_condition = value_condition.find('SimulationTimeCondition')
                value = float(simtime_condition.attrib.get('value'))
                rule = simtime_condition.attrib.get('rule')
                atomic = SimulationTimeCondition(value, success_rule=rule)
            elif value_condition.find('TimeOfDayCondition') is not None:
                tod_condition = value_condition.find('TimeOfDayCondition')
                condition_date = tod_condition.attrib.get('dateTime')
                condition_rule = tod_condition.attrib.get('rule')
                condition_operator = OpenScenarioParser.operators[condition_rule]
                atomic = TimeOfDayComparison(condition_date, condition_operator, condition_name)
            elif value_condition.find('StoryboardElementStateCondition') is not None:
                state_condition = value_condition.find('StoryboardElementStateCondition')
                element_name = state_condition.attrib.get('storyboardElementRef')
                element_type = state_condition.attrib.get('storyboardElementType')
                state = state_condition.attrib.get('state')
                if state == 'startTransition':
                    atomic = OSCStartEndCondition(element_type, element_name, rule='START', name=state + 'Condition')
                elif state == 'stopTransition' or state == 'endTransition' or state == 'completeState':
                    atomic = OSCStartEndCondition(element_type, element_name, rule='END', name=state + 'Condition')
                else:
                    raise NotImplementedError('Only start, stop, endTransitions and completeState are currently supported')
            elif value_condition.find('UserDefinedValueCondition') is not None:
                raise NotImplementedError('ByValue UserDefinedValue conditions are not yet supported')
            elif value_condition.find('TrafficSignalCondition') is not None:
                tl_condition = value_condition.find('TrafficSignalCondition')
                name_condition = tl_condition.attrib.get('name')
                traffic_light = OpenScenarioParser.get_traffic_light_from_osc_name(name_condition)
                tl_state = tl_condition.attrib.get('state').upper()
                if tl_state not in OpenScenarioParser.tl_states:
                    raise KeyError('CARLA only supports Green, Red, Yellow or Off')
                state_condition = OpenScenarioParser.tl_states[tl_state]
                atomic = WaitForTrafficLightState(traffic_light, state_condition, name=condition_name)
            elif value_condition.find('TrafficSignalControllerCondition') is not None:
                raise NotImplementedError('ByValue TrafficSignalController conditions are not yet supported')
            else:
                raise AttributeError('Unknown ByValue condition')
        else:
            raise AttributeError('Unknown condition')
        if delay_atomic is not None and atomic is not None:
            new_atomic = py_trees.composites.Sequence('delayed sequence')
            new_atomic.add_child(delay_atomic)
            new_atomic.add_child(atomic)
        else:
            new_atomic = atomic
        return new_atomic

    @staticmethod
    def convert_maneuver_to_atomic(action, actor, catalogs):
        """
        Convert an OpenSCENARIO maneuver action into a Behavior atomic

        Note not all OpenSCENARIO actions are currently supported
        """
        maneuver_name = action.attrib.get('name', 'unknown')
        if action.find('GlobalAction') is not None:
            global_action = action.find('GlobalAction')
            if global_action.find('InfrastructureAction') is not None:
                infrastructure_action = global_action.find('InfrastructureAction').find('TrafficSignalAction')
                if infrastructure_action.find('TrafficSignalStateAction') is not None:
                    traffic_light_action = infrastructure_action.find('TrafficSignalStateAction')
                    name_condition = traffic_light_action.attrib.get('name')
                    traffic_light = OpenScenarioParser.get_traffic_light_from_osc_name(name_condition)
                    tl_state = traffic_light_action.attrib.get('state').upper()
                    if tl_state not in OpenScenarioParser.tl_states:
                        raise KeyError('CARLA only supports Green, Red, Yellow or Off')
                    traffic_light_state = OpenScenarioParser.tl_states[tl_state]
                    atomic = TrafficLightStateSetter(traffic_light, traffic_light_state, name=maneuver_name + '_' + str(traffic_light.id))
                else:
                    raise NotImplementedError('TrafficLights can only be influenced via TrafficSignalStateAction')
            elif global_action.find('EnvironmentAction') is not None:
                weather_behavior = ChangeWeather(OpenScenarioParser.get_weather_from_env_action(global_action, catalogs))
                friction_behavior = ChangeRoadFriction(OpenScenarioParser.get_friction_from_env_action(global_action, catalogs))
                env_behavior = py_trees.composites.Parallel(policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ALL, name=maneuver_name)
                env_behavior.add_child(oneshot_behavior(variable_name=maneuver_name + '>WeatherUpdate', behaviour=weather_behavior))
                env_behavior.add_child(oneshot_behavior(variable_name=maneuver_name + '>FrictionUpdate', behaviour=friction_behavior))
                return env_behavior
            else:
                raise NotImplementedError('Global actions are not yet supported')
        elif action.find('UserDefinedAction') is not None:
            user_defined_action = action.find('UserDefinedAction')
            if user_defined_action.find('CustomCommandAction') is not None:
                command = user_defined_action.find('CustomCommandAction').attrib.get('type')
                atomic = RunScript(command, base_path=OpenScenarioParser.osc_filepath, name=maneuver_name)
        elif action.find('PrivateAction') is not None:
            private_action = action.find('PrivateAction')
            if private_action.find('LongitudinalAction') is not None:
                private_action = private_action.find('LongitudinalAction')
                if private_action.find('SpeedAction') is not None:
                    long_maneuver = private_action.find('SpeedAction')
                    distance = float('inf')
                    duration = float('inf')
                    dimension = long_maneuver.find('SpeedActionDynamics').attrib.get('dynamicsDimension')
                    if dimension == 'distance':
                        distance = float(long_maneuver.find('SpeedActionDynamics').attrib.get('value', float('inf')))
                    else:
                        duration = float(long_maneuver.find('SpeedActionDynamics').attrib.get('value', float('inf')))
                    if long_maneuver.find('SpeedActionTarget').find('AbsoluteTargetSpeed') is not None:
                        target_speed = float(long_maneuver.find('SpeedActionTarget').find('AbsoluteTargetSpeed').attrib.get('value', 0))
                        atomic = ChangeActorTargetSpeed(actor, target_speed, distance=distance, duration=duration, name=maneuver_name)
                    if long_maneuver.find('SpeedActionTarget').find('RelativeTargetSpeed') is not None:
                        relative_speed = long_maneuver.find('SpeedActionTarget').find('RelativeTargetSpeed')
                        obj = relative_speed.attrib.get('entityRef')
                        value = float(relative_speed.attrib.get('value', 0))
                        value_type = relative_speed.attrib.get('speedTargetValueType')
                        continuous = relative_speed.attrib.get('continuous')
                        for traffic_actor in CarlaDataProvider.get_world().get_actors():
                            if 'role_name' in traffic_actor.attributes and traffic_actor.attributes['role_name'] == obj:
                                obj_actor = traffic_actor
                        atomic = ChangeActorTargetSpeed(actor, target_speed=0.0, relative_actor=obj_actor, value=value, value_type=value_type, continuous=continuous, distance=distance, duration=duration, name=maneuver_name)
                elif private_action.find('LongitudinalDistanceAction') is not None:
                    raise NotImplementedError('Longitudinal distance actions are not yet supported')
                else:
                    raise AttributeError('Unknown longitudinal action')
            elif private_action.find('LateralAction') is not None:
                private_action = private_action.find('LateralAction')
                if private_action.find('LaneChangeAction') is not None:
                    lat_maneuver = private_action.find('LaneChangeAction')
                    target_lane_rel = float(lat_maneuver.find('LaneChangeTarget').find('RelativeTargetLane').attrib.get('value', 0))
                    distance = float('inf')
                    duration = float('inf')
                    dimension = lat_maneuver.find('LaneChangeActionDynamics').attrib.get('dynamicsDimension')
                    if dimension == 'distance':
                        distance = float(lat_maneuver.find('LaneChangeActionDynamics').attrib.get('value', float('inf')))
                    else:
                        duration = float(lat_maneuver.find('LaneChangeActionDynamics').attrib.get('value', float('inf')))
                    atomic = ChangeActorLateralMotion(actor, direction='left' if target_lane_rel < 0 else 'right', distance_lane_change=distance, distance_other_lane=1000, name=maneuver_name)
                else:
                    raise AttributeError('Unknown lateral action')
            elif private_action.find('VisibilityAction') is not None:
                raise NotImplementedError('Visibility actions are not yet supported')
            elif private_action.find('SynchronizeAction') is not None:
                raise NotImplementedError('Synchronization actions are not yet supported')
            elif private_action.find('ActivateControllerAction') is not None:
                private_action = private_action.find('ActivateControllerAction')
                activate = strtobool(private_action.attrib.get('longitudinal'))
                atomic = ChangeAutoPilot(actor, activate, name=maneuver_name)
            elif private_action.find('ControllerAction') is not None:
                controller_action = private_action.find('ControllerAction')
                module, args = OpenScenarioParser.get_controller(controller_action, catalogs)
                atomic = ChangeActorControl(actor, control_py_module=module, args=args)
            elif private_action.find('TeleportAction') is not None:
                position = private_action.find('TeleportAction')
                atomic = ActorTransformSetterToOSCPosition(actor, position, name=maneuver_name)
            elif private_action.find('RoutingAction') is not None:
                private_action = private_action.find('RoutingAction')
                if private_action.find('AssignRouteAction') is not None:
                    route_action = private_action.find('AssignRouteAction')
                    waypoints = OpenScenarioParser.get_route(route_action, catalogs)
                    atomic = ChangeActorWaypoints(actor, waypoints=waypoints, name=maneuver_name)
                elif private_action.find('FollowTrajectoryAction') is not None:
                    raise NotImplementedError('Private FollowTrajectory actions are not yet supported')
                elif private_action.find('AcquirePositionAction') is not None:
                    route_action = private_action.find('AcquirePositionAction')
                    osc_position = route_action.find('Position')
                    position = OpenScenarioParser.convert_position_to_transform(osc_position)
                    atomic = ChangeActorWaypointsToReachPosition(actor, position=position, name=maneuver_name)
                else:
                    raise AttributeError('Unknown private routing action')
            else:
                raise AttributeError('Unknown private action')
        elif list(action):
            raise AttributeError('Unknown action: {}'.format(maneuver_name))
        else:
            return Idle(duration=0, name=maneuver_name)
        return atomic

@staticmethod
def get_catalog_entry(catalogs, catalog_reference):
    """
        Get catalog entry referenced by catalog_reference included correct parameter settings

        Args:
            catalogs (Dictionary of dictionaries): List of all catalogs and their entries
            catalog_reference (XML ElementTree): Reference containing the exact catalog to be used

        returns:
            Catalog entry (XML ElementTree)
        """
    entry = catalogs[catalog_reference.attrib.get('catalogName')][catalog_reference.attrib.get('entryName')]
    entry_copy = copy.deepcopy(entry)
    catalog_copy = copy.deepcopy(catalog_reference)
    entry = OpenScenarioParser.assign_catalog_parameters(entry_copy, catalog_copy)
    return entry

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

class AutonomousAgent(object):
    """
    Autonomous agent base class. All user agents have to be derived from this class
    """

    def __init__(self, path_to_conf_file):
        self._global_plan = None
        self._global_plan_world_coord = None
        self.sensor_interface = SensorInterface()
        self.setup(path_to_conf_file)

    def setup(self, path_to_conf_file):
        """
        Initialize everything needed by your agent and set the track attribute to the right type:
        """
        pass

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
        sensors = []
        return sensors

    def run_step(self, input_data, timestamp):
        """
        Execute one step of navigation.
        :return: control
        """
        control = carla.VehicleControl()
        control.steer = 0.0
        control.throttle = 0.0
        control.brake = 0.0
        control.hand_brake = False
        return control

    def destroy(self):
        """
        Destroy (clean-up) the agent
        :return:
        """
        pass

    def __call__(self):
        """
        Execute the agent call, e.g. agent()
        Returns the next vehicle controls
        """
        input_data = self.sensor_interface.get_data()
        timestamp = GameTime.get_time()
        wallclock = GameTime.get_wallclocktime()
        print('======[Agent] Wallclock_time = {} / Sim_time = {}'.format(wallclock, timestamp))
        control = self.run_step(input_data, timestamp)
        control.manual_gear_shift = False
        return control

    def all_sensors_ready(self):
        """
        Check if all sensors are ready
        Returns true if sensors are ready
        """
        return self.sensor_interface.all_sensors_ready()

    def set_global_plan(self, global_plan_gps, global_plan_world_coord):
        """
        Set the plan (route) for the agent
        """
        ds_ids = downsample_route(global_plan_world_coord, 1)
        self._global_plan_world_coord = [(global_plan_world_coord[x][0], global_plan_world_coord[x][1]) for x in ds_ids]
        self._global_plan = [global_plan_gps[x] for x in ds_ids]

def all_sensors_ready(self):
    """
        Check if all sensors are ready
        Returns true if sensors are ready
        """
    return self.sensor_interface.all_sensors_ready()

class AgentWrapper(object):
    """
    Wrapper for autonomous agents required for tracking and checking of used sensors
    """
    _agent = None
    _sensors_list = []

    def __init__(self, agent):
        """
        Set the autonomous agent
        """
        self._agent = agent

    def __call__(self):
        """
        Pass the call directly to the agent
        """
        return self._agent()

    def setup_sensors(self, vehicle, debug_mode=False):
        """
        Create the sensors defined by the user and attach them to the ego-vehicle
        :param vehicle: ego vehicle
        :return:
        """
        bp_library = CarlaDataProvider.get_world().get_blueprint_library()
        for sensor_spec in self._agent.sensors():
            bp = bp_library.find(str(sensor_spec['type']))
            if sensor_spec['type'].startswith('sensor.camera'):
                bp.set_attribute('image_size_x', str(sensor_spec['width']))
                bp.set_attribute('image_size_y', str(sensor_spec['height']))
                bp.set_attribute('fov', str(sensor_spec['fov']))
                sensor_location = carla.Location(x=sensor_spec['x'], y=sensor_spec['y'], z=sensor_spec['z'])
                sensor_rotation = carla.Rotation(pitch=sensor_spec['pitch'], roll=sensor_spec['roll'], yaw=sensor_spec['yaw'])
            elif sensor_spec['type'].startswith('sensor.lidar'):
                bp.set_attribute('range', str(sensor_spec['range']))
                bp.set_attribute('rotation_frequency', str(sensor_spec['rotation_frequency']))
                bp.set_attribute('channels', str(sensor_spec['channels']))
                bp.set_attribute('upper_fov', str(sensor_spec['upper_fov']))
                bp.set_attribute('lower_fov', str(sensor_spec['lower_fov']))
                bp.set_attribute('points_per_second', str(sensor_spec['points_per_second']))
                sensor_location = carla.Location(x=sensor_spec['x'], y=sensor_spec['y'], z=sensor_spec['z'])
                sensor_rotation = carla.Rotation(pitch=sensor_spec['pitch'], roll=sensor_spec['roll'], yaw=sensor_spec['yaw'])
            elif sensor_spec['type'].startswith('sensor.other.gnss'):
                sensor_location = carla.Location(x=sensor_spec['x'], y=sensor_spec['y'], z=sensor_spec['z'])
                sensor_rotation = carla.Rotation()
            sensor_transform = carla.Transform(sensor_location, sensor_rotation)
            sensor = CarlaDataProvider.get_world().spawn_actor(bp, sensor_transform, vehicle)
            sensor.listen(CallBack(sensor_spec['id'], sensor, self._agent.sensor_interface))
            self._sensors_list.append(sensor)
        while not self._agent.all_sensors_ready():
            if debug_mode:
                print(' waiting for one data reading from sensors...')
            CarlaDataProvider.get_world().tick()

    def cleanup(self):
        """
        Remove and destroy all sensors
        """
        for i, _ in enumerate(self._sensors_list):
            if self._sensors_list[i] is not None:
                self._sensors_list[i].stop()
                self._sensors_list[i].destroy()
                self._sensors_list[i] = None
        self._sensors_list = []

def setup_sensors(self, vehicle, debug_mode=False):
    """
        Create the sensors defined by the user and attach them to the ego-vehicle
        :param vehicle: ego vehicle
        :return:
        """
    bp_library = CarlaDataProvider.get_world().get_blueprint_library()
    for sensor_spec in self._agent.sensors():
        bp = bp_library.find(str(sensor_spec['type']))
        if sensor_spec['type'].startswith('sensor.camera'):
            bp.set_attribute('image_size_x', str(sensor_spec['width']))
            bp.set_attribute('image_size_y', str(sensor_spec['height']))
            bp.set_attribute('fov', str(sensor_spec['fov']))
            sensor_location = carla.Location(x=sensor_spec['x'], y=sensor_spec['y'], z=sensor_spec['z'])
            sensor_rotation = carla.Rotation(pitch=sensor_spec['pitch'], roll=sensor_spec['roll'], yaw=sensor_spec['yaw'])
        elif sensor_spec['type'].startswith('sensor.lidar'):
            bp.set_attribute('range', str(sensor_spec['range']))
            bp.set_attribute('rotation_frequency', str(sensor_spec['rotation_frequency']))
            bp.set_attribute('channels', str(sensor_spec['channels']))
            bp.set_attribute('upper_fov', str(sensor_spec['upper_fov']))
            bp.set_attribute('lower_fov', str(sensor_spec['lower_fov']))
            bp.set_attribute('points_per_second', str(sensor_spec['points_per_second']))
            sensor_location = carla.Location(x=sensor_spec['x'], y=sensor_spec['y'], z=sensor_spec['z'])
            sensor_rotation = carla.Rotation(pitch=sensor_spec['pitch'], roll=sensor_spec['roll'], yaw=sensor_spec['yaw'])
        elif sensor_spec['type'].startswith('sensor.other.gnss'):
            sensor_location = carla.Location(x=sensor_spec['x'], y=sensor_spec['y'], z=sensor_spec['z'])
            sensor_rotation = carla.Rotation()
        sensor_transform = carla.Transform(sensor_location, sensor_rotation)
        sensor = CarlaDataProvider.get_world().spawn_actor(bp, sensor_transform, vehicle)
        sensor.listen(CallBack(sensor_spec['id'], sensor, self._agent.sensor_interface))
        self._sensors_list.append(sensor)
    while not self._agent.all_sensors_ready():
        if debug_mode:
            print(' waiting for one data reading from sensors...')
        CarlaDataProvider.get_world().tick()

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

def tick(self, clock):
    for module in self.modules:
        module.tick(clock)

