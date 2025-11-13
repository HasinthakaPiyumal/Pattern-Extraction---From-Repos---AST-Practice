# Cluster 28

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

def _register_statistics(self, config, checkpoint, entry_status, crash_message=''):
    """
        Computes and saved the simulation statistics
        """
    current_stats_record = self.statistics_manager.compute_route_statistics(config, self.manager.scenario_duration_system, self.manager.scenario_duration_game, crash_message)
    print('\x1b[1m> Registering the route statistics\x1b[0m')
    self.statistics_manager.save_record(current_stats_record, config.index, checkpoint)
    self.statistics_manager.save_entry_status(entry_status, False, checkpoint)

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

def _register_statistics(self, config, checkpoint, entry_status, crash_message=''):
    """
        Computes and saved the simulation statistics
        """
    current_stats_record = self.statistics_manager.compute_route_statistics(config, self.manager.scenario_duration_system, self.manager.scenario_duration_game, crash_message)
    print('\x1b[1m> Registering the route statistics\x1b[0m')
    self.statistics_manager.save_record(current_stats_record, config.index, checkpoint)
    self.statistics_manager.save_entry_status(entry_status, False, checkpoint)

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

def convert_json_to_actor(actor_dict):
    """
    Convert a JSON string to an ActorConfigurationData dictionary
    """
    node = ET.Element('waypoint')
    node.set('x', actor_dict['x'])
    node.set('y', actor_dict['y'])
    node.set('z', actor_dict['z'])
    node.set('yaw', actor_dict['yaw'])
    return ActorConfigurationData.parse_from_node(node, 'simulation')

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

def convert_json_to_actor(actor_dict):
    """
    Convert a JSON string to an ActorConfigurationData dictionary
    """
    node = ET.Element('waypoint')
    node.set('x', actor_dict['x'])
    node.set('y', actor_dict['y'])
    node.set('z', actor_dict['z'])
    node.set('yaw', actor_dict['yaw'])
    return ActorConfigurationData.parse_from_node(node, 'simulation')

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

def to_route_record(record_dict):
    record = RouteRecord()
    for key, value in record_dict.items():
        setattr(record, key, value)
    return record

class StatisticsManager(object):
    """
    This is the statistics manager for the CARLA leaderboard.
    It gathers data at runtime via the scenario evaluation criteria.
    """

    def __init__(self):
        self._master_scenario = None
        self._registry_route_records = []

    def resume(self, endpoint):
        data = fetch_dict(endpoint)
        if data and dictor(data, '_checkpoint.records'):
            records = data['_checkpoint']['records']
            for record in records:
                self._registry_route_records.append(to_route_record(record))

    def set_route(self, route_id, index):
        self._master_scenario = None
        route_record = RouteRecord()
        route_record.route_id = route_id
        route_record.index = index
        if index < len(self._registry_route_records):
            self._registry_route_records[index] = route_record
        else:
            self._registry_route_records.append(route_record)

    def set_scenario(self, scenario):
        """
        Sets the scenario from which the statistics willb e taken
        """
        self._master_scenario = scenario

    def compute_route_statistics(self, config, duration_time_system=-1, duration_time_game=-1, failure=''):
        """
        Compute the current statistics by evaluating all relevant scenario criteria
        """
        index = config.index
        if not self._registry_route_records or index >= len(self._registry_route_records):
            raise Exception('Critical error with the route registry.')
        route_record = self._registry_route_records[index]
        target_reached = False
        score_penalty = 1.0
        score_route = 0.0
        route_record.meta['duration_system'] = duration_time_system
        route_record.meta['duration_game'] = duration_time_game
        route_record.meta['route_length'] = compute_route_length(config)
        if self._master_scenario:
            if self._master_scenario.timeout_node.timeout:
                route_record.infractions['route_timeout'].append('Route timeout.')
                failure = 'Agent timed out'
            for node in self._master_scenario.get_criteria():
                if node.list_traffic_events:
                    for event in node.list_traffic_events:
                        if event.get_type() == TrafficEventType.COLLISION_STATIC:
                            score_penalty *= PENALTY_COLLISION_STATIC
                            route_record.infractions['collisions_layout'].append(event.get_message())
                        elif event.get_type() == TrafficEventType.COLLISION_PEDESTRIAN:
                            score_penalty *= PENALTY_COLLISION_PEDESTRIAN
                            route_record.infractions['collisions_pedestrian'].append(event.get_message())
                        elif event.get_type() == TrafficEventType.COLLISION_VEHICLE:
                            score_penalty *= PENALTY_COLLISION_VEHICLE
                            route_record.infractions['collisions_vehicle'].append(event.get_message())
                        elif event.get_type() == TrafficEventType.OUTSIDE_ROUTE_LANES_INFRACTION:
                            score_penalty *= 1 - event.get_dict()['percentage'] / 100
                            route_record.infractions['outside_route_lanes'].append(event.get_message())
                        elif event.get_type() == TrafficEventType.TRAFFIC_LIGHT_INFRACTION:
                            score_penalty *= PENALTY_TRAFFIC_LIGHT
                            route_record.infractions['red_light'].append(event.get_message())
                        elif event.get_type() == TrafficEventType.ROUTE_DEVIATION:
                            route_record.infractions['route_dev'].append(event.get_message())
                            failure = 'Agent deviated from the route'
                        elif event.get_type() == TrafficEventType.STOP_INFRACTION:
                            score_penalty *= PENALTY_STOP
                            route_record.infractions['stop_infraction'].append(event.get_message())
                        elif event.get_type() == TrafficEventType.VEHICLE_BLOCKED:
                            route_record.infractions['vehicle_blocked'].append(event.get_message())
                            failure = 'Agent got blocked'
                        elif event.get_type() == TrafficEventType.ROUTE_COMPLETED:
                            score_route = 100.0
                            target_reached = True
                        elif event.get_type() == TrafficEventType.ROUTE_COMPLETION:
                            if not target_reached:
                                if event.get_dict():
                                    score_route = event.get_dict()['route_completed']
                                else:
                                    score_route = 0
        route_record.scores['score_route'] = score_route
        route_record.scores['score_penalty'] = score_penalty
        route_record.scores['score_composed'] = max(score_route * score_penalty, 0.0)
        if target_reached:
            route_record.status = 'Completed'
        else:
            route_record.status = 'Failed'
            if failure:
                route_record.status += ' - ' + failure
        return route_record

    def compute_global_statistics(self, total_routes):
        global_record = RouteRecord()
        global_record.route_id = -1
        global_record.index = -1
        global_record.status = 'Completed'
        if self._registry_route_records:
            for route_record in self._registry_route_records:
                global_record.scores['score_route'] += route_record.scores['score_route']
                global_record.scores['score_penalty'] += route_record.scores['score_penalty']
                global_record.scores['score_composed'] += route_record.scores['score_composed']
                for key in global_record.infractions.keys():
                    route_length_kms = max(route_record.scores['score_route'] * route_record.meta['route_length'] / 1000.0, 0.001)
                    if isinstance(global_record.infractions[key], list):
                        global_record.infractions[key] = len(route_record.infractions[key]) / route_length_kms
                    else:
                        global_record.infractions[key] += len(route_record.infractions[key]) / route_length_kms
                if route_record.status is not 'Completed':
                    global_record.status = 'Failed'
                    if 'exceptions' not in global_record.meta:
                        global_record.meta['exceptions'] = []
                    global_record.meta['exceptions'].append((route_record.route_id, route_record.index, route_record.status))
        global_record.scores['score_route'] /= float(total_routes)
        global_record.scores['score_penalty'] /= float(total_routes)
        global_record.scores['score_composed'] /= float(total_routes)
        return global_record

    @staticmethod
    def save_record(route_record, index, endpoint):
        data = fetch_dict(endpoint)
        if not data:
            data = create_default_json_msg()
        stats_dict = route_record.__dict__
        record_list = data['_checkpoint']['records']
        if index > len(record_list):
            print('Error! No enough entries in the list')
            sys.exit(-1)
        elif index == len(record_list):
            record_list.append(stats_dict)
        else:
            record_list[index] = stats_dict
        save_dict(endpoint, data)

    @staticmethod
    def save_global_record(route_record, sensors, total_routes, endpoint):
        data = fetch_dict(endpoint)
        if not data:
            data = create_default_json_msg()
        stats_dict = route_record.__dict__
        data['_checkpoint']['global_record'] = stats_dict
        data['values'] = ['{:.3f}'.format(stats_dict['scores']['score_composed']), '{:.3f}'.format(stats_dict['scores']['score_route']), '{:.3f}'.format(stats_dict['scores']['score_penalty']), '{:.3f}'.format(stats_dict['infractions']['collisions_pedestrian']), '{:.3f}'.format(stats_dict['infractions']['collisions_vehicle']), '{:.3f}'.format(stats_dict['infractions']['collisions_layout']), '{:.3f}'.format(stats_dict['infractions']['red_light']), '{:.3f}'.format(stats_dict['infractions']['stop_infraction']), '{:.3f}'.format(stats_dict['infractions']['outside_route_lanes']), '{:.3f}'.format(stats_dict['infractions']['route_dev']), '{:.3f}'.format(stats_dict['infractions']['route_timeout']), '{:.3f}'.format(stats_dict['infractions']['vehicle_blocked'])]
        data['labels'] = ['Avg. driving score', 'Avg. route completion', 'Avg. infraction penalty', 'Collisions with pedestrians', 'Collisions with vehicles', 'Collisions with layout', 'Red lights infractions', 'Stop sign infractions', 'Off-road infractions', 'Route deviations', 'Route timeouts', 'Agent blocked']
        entry_status = 'Finished'
        eligible = True
        route_records = data['_checkpoint']['records']
        progress = data['_checkpoint']['progress']
        if progress[1] != total_routes:
            raise Exception('Critical error with the route registry.')
        if len(route_records) != total_routes or progress[0] != progress[1]:
            entry_status = 'Finished with missing data'
            eligible = False
        else:
            for route in route_records:
                route_status = route['status']
                if 'Agent' in route_status:
                    entry_status = 'Finished with agent errors'
                    break
        data['entry_status'] = entry_status
        data['eligible'] = eligible
        save_dict(endpoint, data)

    @staticmethod
    def save_sensors(sensors, endpoint):
        data = fetch_dict(endpoint)
        if not data:
            data = create_default_json_msg()
        if not data['sensors']:
            data['sensors'] = sensors
            save_dict(endpoint, data)

    @staticmethod
    def save_entry_status(entry_status, eligible, endpoint):
        data = fetch_dict(endpoint)
        if not data:
            data = create_default_json_msg()
        data['entry_status'] = entry_status
        data['eligible'] = eligible
        save_dict(endpoint, data)

    @staticmethod
    def clear_record(endpoint):
        if not endpoint.startswith(('http:', 'https:', 'ftp:')):
            with open(endpoint, 'w') as fd:
                fd.truncate(0)

def set_route(self, route_id, index):
    self._master_scenario = None
    route_record = RouteRecord()
    route_record.route_id = route_id
    route_record.index = index
    if index < len(self._registry_route_records):
        self._registry_route_records[index] = route_record
    else:
        self._registry_route_records.append(route_record)

def compute_global_statistics(self, total_routes):
    global_record = RouteRecord()
    global_record.route_id = -1
    global_record.index = -1
    global_record.status = 'Completed'
    if self._registry_route_records:
        for route_record in self._registry_route_records:
            global_record.scores['score_route'] += route_record.scores['score_route']
            global_record.scores['score_penalty'] += route_record.scores['score_penalty']
            global_record.scores['score_composed'] += route_record.scores['score_composed']
            for key in global_record.infractions.keys():
                route_length_kms = max(route_record.scores['score_route'] * route_record.meta['route_length'] / 1000.0, 0.001)
                if isinstance(global_record.infractions[key], list):
                    global_record.infractions[key] = len(route_record.infractions[key]) / route_length_kms
                else:
                    global_record.infractions[key] += len(route_record.infractions[key]) / route_length_kms
            if route_record.status is not 'Completed':
                global_record.status = 'Failed'
                if 'exceptions' not in global_record.meta:
                    global_record.meta['exceptions'] = []
                global_record.meta['exceptions'].append((route_record.route_id, route_record.index, route_record.status))
    global_record.scores['score_route'] /= float(total_routes)
    global_record.scores['score_penalty'] /= float(total_routes)
    global_record.scores['score_composed'] /= float(total_routes)
    return global_record

@staticmethod
def clear_record(endpoint):
    if not endpoint.startswith(('http:', 'https:', 'ftp:')):
        with open(endpoint, 'w') as fd:
            fd.truncate(0)

def fetch_dict(endpoint):
    data = None
    if endpoint.startswith(('http:', 'https:', 'ftp:')):
        proxies = autodetect_proxy()
        if proxies:
            response = requests.get(url=endpoint, proxies=proxies)
        else:
            response = requests.get(url=endpoint)
        try:
            data = response.json()
        except json.decoder.JSONDecodeError:
            data = {}
    else:
        data = {}
        if os.path.exists(endpoint):
            with open(endpoint) as fd:
                try:
                    data = json.load(fd)
                except json.JSONDecodeError:
                    data = {}
    return data

def save_dict(endpoint, data):
    if endpoint.startswith(('http:', 'https:', 'ftp:')):
        proxies = autodetect_proxy()
        if proxies:
            _ = requests.patch(url=endpoint, headers={'content-type': 'application/json'}, data=json.dumps(data, indent=4, sort_keys=True), proxies=proxies)
        else:
            _ = requests.patch(url=endpoint, headers={'content-type': 'application/json'}, data=json.dumps(data, indent=4, sort_keys=True))
    else:
        with open(endpoint, 'w') as fd:
            json.dump(data, fd, indent=4, sort_keys=True)

class ResultOutputProvider(object):
    """
    This module contains the _result gatherer and write for CARLA scenarios.
    It shall be used from the ScenarioManager only.
    """

    def __init__(self, data, global_result):
        """
        - data contains all scenario-related information
        - global_result is overall pass/fail info
        """
        self._data = data
        self._global_result = global_result
        self._start_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self._data.start_system_time))
        self._end_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self._data.end_system_time))
        print(self.create_output_text())

    def create_output_text(self):
        """
        Creates the output message
        """
        output = '\n'
        output += '\x1b[1m========= Results of {} (repetition {}) ------ {} \x1b[1m=========\x1b[0m\n'.format(self._data.scenario_tree.name, self._data.repetition_number, self._global_result)
        output += '\n'
        system_time = round(self._data.scenario_duration_system, 2)
        game_time = round(self._data.scenario_duration_game, 2)
        ratio = round(self._data.scenario_duration_game / self._data.scenario_duration_system, 3)
        list_statistics = [['Start Time', '{}'.format(self._start_time)]]
        list_statistics.extend([['End Time', '{}'.format(self._end_time)]])
        list_statistics.extend([['Duration (System Time)', '{}s'.format(system_time)]])
        list_statistics.extend([['Duration (Game Time)', '{}s'.format(game_time)]])
        list_statistics.extend([['Ratio (System Time / Game Time)', '{}'.format(ratio)]])
        output += tabulate(list_statistics, tablefmt='fancy_grid')
        output += '\n\n'
        header = ['Criterion', 'Result', 'Value']
        list_statistics = [header]
        for criterion in self._data.scenario.get_criteria():
            actual_value = criterion.actual_value
            expected_value = criterion.expected_value_success
            name = criterion.name
            result = criterion.test_status
            if result == 'SUCCESS':
                result = '\x1b[92m' + 'SUCCESS' + '\x1b[0m'
            elif result == 'FAILURE':
                result = '\x1b[91m' + 'FAILURE' + '\x1b[0m'
            if name == 'RouteCompletionTest':
                actual_value = str(actual_value) + ' %'
            elif name == 'OutsideRouteLanesTest':
                actual_value = str(actual_value) + ' %'
            elif name == 'CollisionTest':
                actual_value = str(actual_value) + ' times'
            elif name == 'RunningRedLightTest':
                actual_value = str(actual_value) + ' times'
            elif name == 'RunningStopTest':
                actual_value = str(actual_value) + ' times'
            elif name == 'InRouteTest':
                actual_value = ''
            elif name == 'AgentBlockedTest':
                actual_value = ''
            list_statistics.extend([[name, result, actual_value]])
        name = 'Timeout'
        actual_value = self._data.scenario_duration_game
        expected_value = self._data.scenario.timeout
        if self._data.scenario_duration_game < self._data.scenario.timeout:
            result = '\x1b[92m' + 'SUCCESS' + '\x1b[0m'
        else:
            result = '\x1b[91m' + 'FAILURE' + '\x1b[0m'
        list_statistics.extend([[name, result, '']])
        output += tabulate(list_statistics, tablefmt='fancy_grid')
        output += '\n'
        return output

def __init__(self, data, global_result):
    """
        - data contains all scenario-related information
        - global_result is overall pass/fail info
        """
    self._data = data
    self._global_result = global_result
    self._start_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self._data.start_system_time))
    self._end_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self._data.end_system_time))
    print(self.create_output_text())

def _get_latlon_ref(world):
    """
    Convert from waypoints world coordinates to CARLA GPS coordinates
    :return: tuple with lat and lon coordinates
    """
    xodr = world.get_map().to_opendrive()
    tree = ET.ElementTree(ET.fromstring(xodr))
    lat_ref = 42.0
    lon_ref = 2.0
    for opendrive in tree.iter('OpenDRIVE'):
        for header in opendrive.iter('header'):
            for georef in header.iter('geoReference'):
                if georef.text:
                    str_list = georef.text.split(' ')
                    for item in str_list:
                        if '+lat_0' in item:
                            lat_ref = float(item.split('=')[1])
                        if '+lon_0' in item:
                            lon_ref = float(item.split('=')[1])
    return (lat_ref, lon_ref)

def downsample_route(route, sample_factor):
    """
    Downsample the route by some factor.
    :param route: the trajectory , has to contain the waypoints and the road options
    :param sample_factor: Maximum distance between samples
    :return: returns the ids of the final route that can
    """
    ids_to_sample = []
    prev_option = None
    dist = 0
    for i, point in enumerate(route):
        curr_option = point[1]
        if curr_option in (RoadOption.CHANGELANELEFT, RoadOption.CHANGELANERIGHT):
            ids_to_sample.append(i)
            dist = 0
        elif prev_option != curr_option and prev_option not in (RoadOption.CHANGELANELEFT, RoadOption.CHANGELANERIGHT):
            ids_to_sample.append(i)
            dist = 0
        elif dist > sample_factor:
            ids_to_sample.append(i)
            dist = 0
        elif i == len(route) - 1:
            ids_to_sample.append(i)
            dist = 0
        else:
            curr_location = point[0].location
            prev_location = route[i - 1][0].location
            dist += curr_location.distance(prev_location)
        prev_option = curr_option
    return ids_to_sample

class RouteIndexer:

    def __init__(self, routes_file, scenarios_file, repetitions):
        self._routes_file = routes_file
        self._scenarios_file = scenarios_file
        self._repetitions = repetitions
        self._configs_dict = OrderedDict()
        self._configs_list = []
        self.routes_length = []
        self._index = 0
        route_configurations = RouteParser.parse_routes_file(self._routes_file, self._scenarios_file, False)
        self.n_routes = len(route_configurations)
        self.total = self.n_routes * self._repetitions
        for i, config in enumerate(route_configurations):
            for repetition in range(repetitions):
                config.index = i * self._repetitions + repetition
                config.repetition_index = repetition
                self._configs_dict['{}.{}'.format(config.name, repetition)] = copy.copy(config)
        self._configs_list = list(self._configs_dict.items())

    def peek(self):
        return not self._index >= len(self._configs_list)

    def next(self):
        if self._index >= len(self._configs_list):
            return None
        key, config = self._configs_list[self._index]
        self._index += 1
        return config

    def resume(self, endpoint):
        data = fetch_dict(endpoint)
        if data:
            checkpoint_dict = dictor(data, '_checkpoint')
            if checkpoint_dict and 'progress' in checkpoint_dict:
                progress = checkpoint_dict['progress']
                if not progress:
                    current_route = 0
                else:
                    current_route, total_routes = progress
                if current_route <= self.total:
                    self._index = current_route
                else:
                    print('Problem reading checkpoint. Route id {} larger than maximum number of routes {}'.format(current_route, self.total))

    def save_state(self, endpoint):
        data = fetch_dict(endpoint)
        if not data:
            data = create_default_json_msg()
        data['_checkpoint']['progress'] = [self._index, self.total]
        save_dict(endpoint, data)

def __init__(self, routes_file, scenarios_file, repetitions):
    self._routes_file = routes_file
    self._scenarios_file = scenarios_file
    self._repetitions = repetitions
    self._configs_dict = OrderedDict()
    self._configs_list = []
    self.routes_length = []
    self._index = 0
    route_configurations = RouteParser.parse_routes_file(self._routes_file, self._scenarios_file, False)
    self.n_routes = len(route_configurations)
    self.total = self.n_routes * self._repetitions
    for i, config in enumerate(route_configurations):
        for repetition in range(repetitions):
            config.index = i * self._repetitions + repetition
            config.repetition_index = repetition
            self._configs_dict['{}.{}'.format(config.name, repetition)] = copy.copy(config)
    self._configs_list = list(self._configs_dict.items())

def peek(self):
    return not self._index >= len(self._configs_list)

def next(self):
    if self._index >= len(self._configs_list):
        return None
    key, config = self._configs_list[self._index]
    self._index += 1
    return config

class RouteParser(object):
    """
    Pure static class used to parse all the route and scenario configuration parameters.
    """

    @staticmethod
    def parse_annotations_file(annotation_filename):
        """
        Return the annotations of which positions where the scenarios are going to happen.
        :param annotation_filename: the filename for the anotations file
        :return:
        """
        with open(annotation_filename, 'r') as f:
            annotation_dict = json.loads(f.read(), object_pairs_hook=OrderedDict)
        final_dict = OrderedDict()
        for town_dict in annotation_dict['available_scenarios']:
            final_dict.update(town_dict)
        return final_dict

    @staticmethod
    def parse_routes_file(route_filename, scenario_file, single_route=None):
        """
        Returns a list of route elements.
        :param route_filename: the path to a set of routes.
        :param single_route: If set, only this route shall be returned
        :return: List of dicts containing the waypoints, id and town of the routes
        """
        list_route_descriptions = []
        tree = ET.parse(route_filename)
        for route in tree.iter('route'):
            route_id = route.attrib['id']
            if single_route and route_id != single_route:
                continue
            new_config = RouteScenarioConfiguration()
            new_config.town = route.attrib['town']
            new_config.name = 'RouteScenario_{}'.format(route_id)
            new_config.weather = RouteParser.parse_weather(route)
            new_config.scenario_file = scenario_file
            waypoint_list = []
            for waypoint in route.iter('waypoint'):
                waypoint_list.append(carla.Location(x=float(waypoint.attrib['x']), y=float(waypoint.attrib['y']), z=float(waypoint.attrib['z'])))
            new_config.trajectory = waypoint_list
            list_route_descriptions.append(new_config)
        return list_route_descriptions

    @staticmethod
    def parse_weather(route):
        """
        Returns a carla.WeatherParameters with the corresponding weather for that route. If the route
        has no weather attribute, the default one is triggered.
        """
        route_weather = route.find('weather')
        if route_weather is None:
            weather = carla.WeatherParameters(sun_altitude_angle=70, cloudiness=30)
        else:
            weather = carla.WeatherParameters()
            for weather_attrib in route.iter('weather'):
                if 'cloudiness' in weather_attrib.attrib:
                    weather.cloudiness = float(weather_attrib.attrib['cloudiness'])
                if 'precipitation' in weather_attrib.attrib:
                    weather.precipitation = float(weather_attrib.attrib['precipitation'])
                if 'precipitation_deposits' in weather_attrib.attrib:
                    weather.precipitation_deposits = float(weather_attrib.attrib['precipitation_deposits'])
                if 'wind_intensity' in weather_attrib.attrib:
                    weather.wind_intensity = float(weather_attrib.attrib['wind_intensity'])
                if 'sun_azimuth_angle' in weather_attrib.attrib:
                    weather.sun_azimuth_angle = float(weather_attrib.attrib['sun_azimuth_angle'])
                if 'sun_altitude_angle' in weather_attrib.attrib:
                    weather.sun_altitude_angle = float(weather_attrib.attrib['sun_altitude_angle'])
                if 'wetness' in weather_attrib.attrib:
                    weather.wetness = float(weather_attrib.attrib['wetness'])
                if 'fog_distance' in weather_attrib.attrib:
                    weather.fog_distance = float(weather_attrib.attrib['fog_distance'])
                if 'fog_density' in weather_attrib.attrib:
                    weather.fog_density = float(weather_attrib.attrib['fog_density'])
                if 'fog_falloff' in weather_attrib.attrib:
                    weather.fog_falloff = float(weather_attrib.attrib['fog_falloff'])
        return weather

    @staticmethod
    def check_trigger_position(new_trigger, existing_triggers):
        """
        Check if this trigger position already exists or if it is a new one.
        :param new_trigger:
        :param existing_triggers:
        :return:
        """
        for trigger_id in existing_triggers.keys():
            trigger = existing_triggers[trigger_id]
            dx = trigger['x'] - new_trigger['x']
            dy = trigger['y'] - new_trigger['y']
            distance = math.sqrt(dx * dx + dy * dy)
            dyaw = (trigger['yaw'] - new_trigger['yaw']) % 360
            if distance < TRIGGER_THRESHOLD and (dyaw < TRIGGER_ANGLE_THRESHOLD or dyaw > 360 - TRIGGER_ANGLE_THRESHOLD):
                return trigger_id
        return None

    @staticmethod
    def convert_waypoint_float(waypoint):
        """
        Convert waypoint values to float
        """
        waypoint['x'] = float(waypoint['x'])
        waypoint['y'] = float(waypoint['y'])
        waypoint['z'] = float(waypoint['z'])
        waypoint['yaw'] = float(waypoint['yaw'])

    @staticmethod
    def match_world_location_to_route(world_location, route_description):
        """
        We match this location to a given route.
            world_location:
            route_description:
        """

        def match_waypoints(waypoint1, wtransform):
            """
            Check if waypoint1 and wtransform are similar
            """
            dx = float(waypoint1['x']) - wtransform.location.x
            dy = float(waypoint1['y']) - wtransform.location.y
            dz = float(waypoint1['z']) - wtransform.location.z
            dpos = math.sqrt(dx * dx + dy * dy + dz * dz)
            dyaw = (float(waypoint1['yaw']) - wtransform.rotation.yaw) % 360
            return dpos < TRIGGER_THRESHOLD and (dyaw < TRIGGER_ANGLE_THRESHOLD or dyaw > 360 - TRIGGER_ANGLE_THRESHOLD)
        match_position = 0
        for route_waypoint in route_description:
            if match_waypoints(world_location, route_waypoint[0]):
                return match_position
            match_position += 1
        return None

    @staticmethod
    def get_scenario_type(scenario, match_position, trajectory):
        """
        Some scenarios have different types depending on the route.
        :param scenario: the scenario name
        :param match_position: the matching position for the scenarion
        :param trajectory: the route trajectory the ego is following
        :return: tag representing this subtype

        Also used to check which are not viable (Such as an scenario
        that triggers when turning but the route doesnt')
        WARNING: These tags are used at:
            - VehicleTurningRoute
            - SignalJunctionCrossingRoute
        and changes to these tags will affect them
        """

        def check_this_waypoint(tuple_wp_turn):
            """
            Decides whether or not the waypoint will define the scenario behavior
            """
            if RoadOption.LANEFOLLOW == tuple_wp_turn[1]:
                return False
            elif RoadOption.CHANGELANELEFT == tuple_wp_turn[1]:
                return False
            elif RoadOption.CHANGELANERIGHT == tuple_wp_turn[1]:
                return False
            return True
        subtype = 'valid'
        if scenario == 'Scenario4':
            for tuple_wp_turn in trajectory[match_position:]:
                if check_this_waypoint(tuple_wp_turn):
                    if RoadOption.LEFT == tuple_wp_turn[1]:
                        subtype = 'S4left'
                    elif RoadOption.RIGHT == tuple_wp_turn[1]:
                        subtype = 'S4right'
                    else:
                        subtype = None
                    break
                subtype = None
        if scenario == 'Scenario7':
            for tuple_wp_turn in trajectory[match_position:]:
                if check_this_waypoint(tuple_wp_turn):
                    if RoadOption.LEFT == tuple_wp_turn[1]:
                        subtype = 'S7left'
                    elif RoadOption.RIGHT == tuple_wp_turn[1]:
                        subtype = 'S7right'
                    elif RoadOption.STRAIGHT == tuple_wp_turn[1]:
                        subtype = 'S7opposite'
                    else:
                        subtype = None
                    break
                subtype = None
        if scenario == 'Scenario8':
            for tuple_wp_turn in trajectory[match_position:]:
                if check_this_waypoint(tuple_wp_turn):
                    if RoadOption.LEFT == tuple_wp_turn[1]:
                        subtype = 'S8left'
                    else:
                        subtype = None
                    break
                subtype = None
        if scenario == 'Scenario9':
            for tuple_wp_turn in trajectory[match_position:]:
                if check_this_waypoint(tuple_wp_turn):
                    if RoadOption.RIGHT == tuple_wp_turn[1]:
                        subtype = 'S9right'
                    else:
                        subtype = None
                    break
                subtype = None
        return subtype

    @staticmethod
    def scan_route_for_scenarios(route_name, trajectory, world_annotations):
        """
        Just returns a plain list of possible scenarios that can happen in this route by matching
        the locations from the scenario into the route description

        :return:  A list of scenario definitions with their correspondent parameters
        """
        existent_triggers = OrderedDict()
        possible_scenarios = OrderedDict()
        latest_trigger_id = 0
        for town_name in world_annotations.keys():
            if town_name != route_name:
                continue
            scenarios = world_annotations[town_name]
            for scenario in scenarios:
                scenario_name = scenario['scenario_type']
                for event in scenario['available_event_configurations']:
                    waypoint = event['transform']
                    RouteParser.convert_waypoint_float(waypoint)
                    match_position = RouteParser.match_world_location_to_route(waypoint, trajectory)
                    if match_position is not None:
                        if 'other_actors' in event:
                            other_vehicles = event['other_actors']
                        else:
                            other_vehicles = None
                        scenario_subtype = RouteParser.get_scenario_type(scenario_name, match_position, trajectory)
                        if scenario_subtype is None:
                            continue
                        scenario_description = {'name': scenario_name, 'other_actors': other_vehicles, 'trigger_position': waypoint, 'scenario_type': scenario_subtype}
                        trigger_id = RouteParser.check_trigger_position(waypoint, existent_triggers)
                        if trigger_id is None:
                            existent_triggers.update({latest_trigger_id: waypoint})
                            possible_scenarios.update({latest_trigger_id: []})
                            trigger_id = latest_trigger_id
                            latest_trigger_id += 1
                        possible_scenarios[trigger_id].append(scenario_description)
        return (possible_scenarios, existent_triggers)

@staticmethod
def parse_weather(route):
    """
        Returns a carla.WeatherParameters with the corresponding weather for that route. If the route
        has no weather attribute, the default one is triggered.
        """
    route_weather = route.find('weather')
    if route_weather is None:
        weather = carla.WeatherParameters(sun_altitude_angle=70, cloudiness=30)
    else:
        weather = carla.WeatherParameters()
        for weather_attrib in route.iter('weather'):
            if 'cloudiness' in weather_attrib.attrib:
                weather.cloudiness = float(weather_attrib.attrib['cloudiness'])
            if 'precipitation' in weather_attrib.attrib:
                weather.precipitation = float(weather_attrib.attrib['precipitation'])
            if 'precipitation_deposits' in weather_attrib.attrib:
                weather.precipitation_deposits = float(weather_attrib.attrib['precipitation_deposits'])
            if 'wind_intensity' in weather_attrib.attrib:
                weather.wind_intensity = float(weather_attrib.attrib['wind_intensity'])
            if 'sun_azimuth_angle' in weather_attrib.attrib:
                weather.sun_azimuth_angle = float(weather_attrib.attrib['sun_azimuth_angle'])
            if 'sun_altitude_angle' in weather_attrib.attrib:
                weather.sun_altitude_angle = float(weather_attrib.attrib['sun_altitude_angle'])
            if 'wetness' in weather_attrib.attrib:
                weather.wetness = float(weather_attrib.attrib['wetness'])
            if 'fog_distance' in weather_attrib.attrib:
                weather.fog_distance = float(weather_attrib.attrib['fog_distance'])
            if 'fog_density' in weather_attrib.attrib:
                weather.fog_density = float(weather_attrib.attrib['fog_density'])
            if 'fog_falloff' in weather_attrib.attrib:
                weather.fog_falloff = float(weather_attrib.attrib['fog_falloff'])
    return weather

def to_route_record(record_dict):
    record = RouteRecord()
    for key, value in record_dict.items():
        setattr(record, key, value)
    return record

class StatisticsManager(object):
    """
    This is the statistics manager for the CARLA leaderboard.
    It gathers data at runtime via the scenario evaluation criteria.
    """

    def __init__(self):
        self._master_scenario = None
        self._registry_route_records = []

    def resume(self, endpoint):
        data = fetch_dict(endpoint)
        if data and dictor(data, '_checkpoint.records'):
            records = data['_checkpoint']['records']
            for record in records:
                self._registry_route_records.append(to_route_record(record))

    def set_route(self, route_id, index):
        self._master_scenario = None
        route_record = RouteRecord()
        route_record.route_id = route_id
        route_record.index = index
        if index < len(self._registry_route_records):
            self._registry_route_records[index] = route_record
        else:
            self._registry_route_records.append(route_record)

    def set_scenario(self, scenario):
        """
        Sets the scenario from which the statistics willb e taken
        """
        self._master_scenario = scenario

    def compute_route_statistics(self, config, duration_time_system=-1, duration_time_game=-1, failure=''):
        """
        Compute the current statistics by evaluating all relevant scenario criteria
        """
        index = config.index
        if not self._registry_route_records or index >= len(self._registry_route_records):
            raise Exception('Critical error with the route registry.')
        route_record = self._registry_route_records[index]
        target_reached = False
        score_penalty = 1.0
        score_route = 0.0
        route_record.meta['duration_system'] = duration_time_system
        route_record.meta['duration_game'] = duration_time_game
        route_record.meta['route_length'] = compute_route_length(config)
        if self._master_scenario:
            if self._master_scenario.timeout_node.timeout:
                route_record.infractions['route_timeout'].append('Route timeout.')
                failure = 'Agent timed out'
            for node in self._master_scenario.get_criteria():
                if node.list_traffic_events:
                    for event in node.list_traffic_events:
                        if event.get_type() == TrafficEventType.COLLISION_STATIC:
                            score_penalty *= PENALTY_COLLISION_STATIC
                            route_record.infractions['collisions_layout'].append(event.get_message())
                        elif event.get_type() == TrafficEventType.COLLISION_PEDESTRIAN:
                            score_penalty *= PENALTY_COLLISION_PEDESTRIAN
                            route_record.infractions['collisions_pedestrian'].append(event.get_message())
                        elif event.get_type() == TrafficEventType.COLLISION_VEHICLE:
                            score_penalty *= PENALTY_COLLISION_VEHICLE
                            route_record.infractions['collisions_vehicle'].append(event.get_message())
                        elif event.get_type() == TrafficEventType.OUTSIDE_ROUTE_LANES_INFRACTION:
                            score_penalty *= 1 - event.get_dict()['percentage'] / 100
                            route_record.infractions['outside_route_lanes'].append(event.get_message())
                        elif event.get_type() == TrafficEventType.TRAFFIC_LIGHT_INFRACTION:
                            score_penalty *= PENALTY_TRAFFIC_LIGHT
                            route_record.infractions['red_light'].append(event.get_message())
                        elif event.get_type() == TrafficEventType.ROUTE_DEVIATION:
                            route_record.infractions['route_dev'].append(event.get_message())
                            failure = 'Agent deviated from the route'
                        elif event.get_type() == TrafficEventType.STOP_INFRACTION:
                            score_penalty *= PENALTY_STOP
                            route_record.infractions['stop_infraction'].append(event.get_message())
                        elif event.get_type() == TrafficEventType.VEHICLE_BLOCKED:
                            route_record.infractions['vehicle_blocked'].append(event.get_message())
                            failure = 'Agent got blocked'
                        elif event.get_type() == TrafficEventType.ROUTE_COMPLETED:
                            score_route = 100.0
                            target_reached = True
                        elif event.get_type() == TrafficEventType.ROUTE_COMPLETION:
                            if not target_reached:
                                if event.get_dict():
                                    score_route = event.get_dict()['route_completed']
                                else:
                                    score_route = 0
        route_record.scores['score_route'] = score_route
        route_record.scores['score_penalty'] = score_penalty
        route_record.scores['score_composed'] = max(score_route * score_penalty, 0.0)
        if target_reached:
            route_record.status = 'Completed'
        else:
            route_record.status = 'Failed'
            if failure:
                route_record.status += ' - ' + failure
        return route_record

    def compute_global_statistics(self, total_routes):
        global_record = RouteRecord()
        global_record.route_id = -1
        global_record.index = -1
        global_record.status = 'Completed'
        if self._registry_route_records:
            for route_record in self._registry_route_records:
                global_record.scores['score_route'] += route_record.scores['score_route']
                global_record.scores['score_penalty'] += route_record.scores['score_penalty']
                global_record.scores['score_composed'] += route_record.scores['score_composed']
                for key in global_record.infractions.keys():
                    route_length_kms = max(route_record.scores['score_route'] * route_record.meta['route_length'] / 1000.0, 0.001)
                    if isinstance(global_record.infractions[key], list):
                        global_record.infractions[key] = len(route_record.infractions[key]) / route_length_kms
                    else:
                        global_record.infractions[key] += len(route_record.infractions[key]) / route_length_kms
                if route_record.status is not 'Completed':
                    global_record.status = 'Failed'
                    if 'exceptions' not in global_record.meta:
                        global_record.meta['exceptions'] = []
                    global_record.meta['exceptions'].append((route_record.route_id, route_record.index, route_record.status))
        global_record.scores['score_route'] /= float(total_routes)
        global_record.scores['score_penalty'] /= float(total_routes)
        global_record.scores['score_composed'] /= float(total_routes)
        return global_record

    @staticmethod
    def save_record(route_record, index, endpoint):
        data = fetch_dict(endpoint)
        if not data:
            data = create_default_json_msg()
        stats_dict = route_record.__dict__
        record_list = data['_checkpoint']['records']
        if index > len(record_list):
            print('Error! No enough entries in the list')
            sys.exit(-1)
        elif index == len(record_list):
            record_list.append(stats_dict)
        else:
            record_list[index] = stats_dict
        save_dict(endpoint, data)

    @staticmethod
    def save_global_record(route_record, sensors, total_routes, endpoint):
        data = fetch_dict(endpoint)
        if not data:
            data = create_default_json_msg()
        stats_dict = route_record.__dict__
        data['_checkpoint']['global_record'] = stats_dict
        data['values'] = ['{:.3f}'.format(stats_dict['scores']['score_composed']), '{:.3f}'.format(stats_dict['scores']['score_route']), '{:.3f}'.format(stats_dict['scores']['score_penalty']), '{:.3f}'.format(stats_dict['infractions']['collisions_pedestrian']), '{:.3f}'.format(stats_dict['infractions']['collisions_vehicle']), '{:.3f}'.format(stats_dict['infractions']['collisions_layout']), '{:.3f}'.format(stats_dict['infractions']['red_light']), '{:.3f}'.format(stats_dict['infractions']['stop_infraction']), '{:.3f}'.format(stats_dict['infractions']['outside_route_lanes']), '{:.3f}'.format(stats_dict['infractions']['route_dev']), '{:.3f}'.format(stats_dict['infractions']['route_timeout']), '{:.3f}'.format(stats_dict['infractions']['vehicle_blocked'])]
        data['labels'] = ['Avg. driving score', 'Avg. route completion', 'Avg. infraction penalty', 'Collisions with pedestrians', 'Collisions with vehicles', 'Collisions with layout', 'Red lights infractions', 'Stop sign infractions', 'Off-road infractions', 'Route deviations', 'Route timeouts', 'Agent blocked']
        entry_status = 'Finished'
        eligible = True
        route_records = data['_checkpoint']['records']
        progress = data['_checkpoint']['progress']
        if progress[1] != total_routes:
            raise Exception('Critical error with the route registry.')
        if len(route_records) != total_routes or progress[0] != progress[1]:
            entry_status = 'Finished with missing data'
            eligible = False
        else:
            for route in route_records:
                route_status = route['status']
                if 'Agent' in route_status:
                    entry_status = 'Finished with agent errors'
                    break
        data['entry_status'] = entry_status
        data['eligible'] = eligible
        save_dict(endpoint, data)

    @staticmethod
    def save_sensors(sensors, endpoint):
        data = fetch_dict(endpoint)
        if not data:
            data = create_default_json_msg()
        if not data['sensors']:
            data['sensors'] = sensors
            save_dict(endpoint, data)

    @staticmethod
    def save_entry_status(entry_status, eligible, endpoint):
        data = fetch_dict(endpoint)
        if not data:
            data = create_default_json_msg()
        data['entry_status'] = entry_status
        data['eligible'] = eligible
        save_dict(endpoint, data)

    @staticmethod
    def clear_record(endpoint):
        if not endpoint.startswith(('http:', 'https:', 'ftp:')):
            with open(endpoint, 'w') as fd:
                fd.truncate(0)

def set_route(self, route_id, index):
    self._master_scenario = None
    route_record = RouteRecord()
    route_record.route_id = route_id
    route_record.index = index
    if index < len(self._registry_route_records):
        self._registry_route_records[index] = route_record
    else:
        self._registry_route_records.append(route_record)

def compute_global_statistics(self, total_routes):
    global_record = RouteRecord()
    global_record.route_id = -1
    global_record.index = -1
    global_record.status = 'Completed'
    if self._registry_route_records:
        for route_record in self._registry_route_records:
            global_record.scores['score_route'] += route_record.scores['score_route']
            global_record.scores['score_penalty'] += route_record.scores['score_penalty']
            global_record.scores['score_composed'] += route_record.scores['score_composed']
            for key in global_record.infractions.keys():
                route_length_kms = max(route_record.scores['score_route'] * route_record.meta['route_length'] / 1000.0, 0.001)
                if isinstance(global_record.infractions[key], list):
                    global_record.infractions[key] = len(route_record.infractions[key]) / route_length_kms
                else:
                    global_record.infractions[key] += len(route_record.infractions[key]) / route_length_kms
            if route_record.status is not 'Completed':
                global_record.status = 'Failed'
                if 'exceptions' not in global_record.meta:
                    global_record.meta['exceptions'] = []
                global_record.meta['exceptions'].append((route_record.route_id, route_record.index, route_record.status))
    global_record.scores['score_route'] /= float(total_routes)
    global_record.scores['score_penalty'] /= float(total_routes)
    global_record.scores['score_composed'] /= float(total_routes)
    return global_record

@staticmethod
def clear_record(endpoint):
    if not endpoint.startswith(('http:', 'https:', 'ftp:')):
        with open(endpoint, 'w') as fd:
            fd.truncate(0)

class OpenDriveMapReader(BaseReader):

    def __call__(self):
        return {'opendrive': CarlaDataProvider.get_map().to_opendrive()}

def __call__(self):
    return {'opendrive': CarlaDataProvider.get_map().to_opendrive()}

class SensorInterface(object):

    def __init__(self):
        self._sensors_objects = {}
        self._data_buffers = {}
        self._new_data_buffers = Queue()
        self._queue_timeout = 10
        self._opendrive_tag = None

    def register_sensor(self, tag, sensor_type, sensor):
        if tag in self._sensors_objects:
            raise SensorConfigurationInvalid('Duplicated sensor tag [{}]'.format(tag))
        self._sensors_objects[tag] = sensor
        if sensor_type == 'sensor.opendrive_map':
            self._opendrive_tag = tag

    def update_sensor(self, tag, data, timestamp):
        if tag not in self._sensors_objects:
            raise SensorConfigurationInvalid('The sensor with tag [{}] has not been created!'.format(tag))
        self._new_data_buffers.put((tag, timestamp, data))

    def get_data(self):
        try:
            data_dict = {}
            while len(data_dict.keys()) < len(self._sensors_objects.keys()):
                if self._opendrive_tag and self._opendrive_tag not in data_dict.keys() and (len(self._sensors_objects.keys()) == len(data_dict.keys()) + 1):
                    break
                sensor_data = self._new_data_buffers.get(True, self._queue_timeout)
                data_dict[sensor_data[0]] = (sensor_data[1], sensor_data[2])
        except Empty:
            raise SensorReceivedNoData('A sensor took too long to send their data')
        return data_dict

def get_data(self):
    try:
        data_dict = {}
        while len(data_dict.keys()) < len(self._sensors_objects.keys()):
            if self._opendrive_tag and self._opendrive_tag not in data_dict.keys() and (len(self._sensors_objects.keys()) == len(data_dict.keys()) + 1):
                break
            sensor_data = self._new_data_buffers.get(True, self._queue_timeout)
            data_dict[sensor_data[0]] = (sensor_data[1], sensor_data[2])
    except Empty:
        raise SensorReceivedNoData('A sensor took too long to send their data')
    return data_dict

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

def _parse_json_control(self):
    if self._index < len(self._control_list):
        self._control = self._control_list[self._index]
        self._index += 1
    else:
        print('JSON file has no more entries')

def __del__(self):
    if self._mode == 'log' and self._log_data:
        with open(self._endpoint, 'w') as fd:
            json.dump(self._log_data, fd, indent=4, sort_keys=True)

class AutonomousAgent(object):
    """
    Autonomous agent base class. All user agents have to be derived from this class
    """

    def __init__(self, path_to_conf_file, route_index=None):
        self.track = Track.SENSORS
        self._global_plan = None
        self._global_plan_world_coord = None
        self.sensor_interface = SensorInterface()
        self.setup(path_to_conf_file, route_index)
        self.wallclock_t0 = None

    def setup(self, path_to_conf_file):
        """
        Initialize everything needed by your agent and set the track attribute to the right type:
            Track.SENSORS : CAMERAS, LIDAR, RADAR, GPS and IMU sensors are allowed
            Track.MAP : OpenDRIVE map is also allowed
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
        if not self.wallclock_t0:
            self.wallclock_t0 = GameTime.get_wallclocktime()
        wallclock = GameTime.get_wallclocktime()
        wallclock_diff = (wallclock - self.wallclock_t0).total_seconds()
        control = self.run_step(input_data, timestamp)
        control.manual_gear_shift = False
        return control

    def set_global_plan(self, global_plan_gps, global_plan_world_coord):
        """
        Set the plan (route) for the agent
        """
        ds_ids = downsample_route(global_plan_world_coord, 50)
        self._global_plan_world_coord = [(global_plan_world_coord[x][0], global_plan_world_coord[x][1]) for x in ds_ids]
        self._global_plan = [global_plan_gps[x] for x in ds_ids]

def set_global_plan(self, global_plan_gps, global_plan_world_coord):
    """
        Set the plan (route) for the agent
        """
    ds_ids = downsample_route(global_plan_world_coord, 50)
    self._global_plan_world_coord = [(global_plan_world_coord[x][0], global_plan_world_coord[x][1]) for x in ds_ids]
    self._global_plan = [global_plan_gps[x] for x in ds_ids]

class AutonomousAgent(object):
    """
    Autonomous agent base class. All user agents have to be derived from this class
    """

    def __init__(self, path_to_conf_file):
        self.track = Track.SENSORS
        self._global_plan = None
        self._global_plan_world_coord = None
        self.sensor_interface = SensorInterface()
        self.setup(path_to_conf_file)
        self.wallclock_t0 = None

    def setup(self, path_to_conf_file):
        """
        Initialize everything needed by your agent and set the track attribute to the right type:
            Track.SENSORS : CAMERAS, LIDAR, RADAR, GPS and IMU sensors are allowed
            Track.MAP : OpenDRIVE map is also allowed
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
        if not self.wallclock_t0:
            self.wallclock_t0 = GameTime.get_wallclocktime()
        wallclock = GameTime.get_wallclocktime()
        wallclock_diff = (wallclock - self.wallclock_t0).total_seconds()
        control = self.run_step(input_data, timestamp)
        control.manual_gear_shift = False
        return control

    def set_global_plan(self, global_plan_gps, global_plan_world_coord):
        """
        Set the plan (route) for the agent
        """
        ds_ids = downsample_route(global_plan_world_coord, 50)
        self._global_plan_world_coord = [(global_plan_world_coord[x][0], global_plan_world_coord[x][1]) for x in ds_ids]
        self._global_plan = [global_plan_gps[x] for x in ds_ids]

def set_global_plan(self, global_plan_gps, global_plan_world_coord):
    """
        Set the plan (route) for the agent
        """
    ds_ids = downsample_route(global_plan_world_coord, 50)
    self._global_plan_world_coord = [(global_plan_world_coord[x][0], global_plan_world_coord[x][1]) for x in ds_ids]
    self._global_plan = [global_plan_gps[x] for x in ds_ids]

def save_from_wp(endpoint, wp):
    """
    Creates a mini json with the data from the scenario location.
    used to copy paste it to the .json
    """
    with open(endpoint, mode='w') as fd:
        entry = {}
        transform = {'x': str(round(wp.transform.location.x, 2)), 'y': str(round(wp.transform.location.y, 2)), 'z': '1.0', 'yaw': str(round(wp.transform.rotation.yaw, 0)), 'pitch': str(round(wp.transform.rotation.pitch, 0))}
        entry['transform'] = transform
        entry['other_actors'] = {}
        json.dump(entry, fd, indent=4)

def save_from_dict(endpoint, wp):
    """
    Creates a mini json with the data from the scenario waypoint.
    used to copy paste it to the .json
    """
    with open(endpoint, mode='w') as fd:
        entry = {}
        transform = {'x': str(round(float(wp['x']), 2)), 'y': str(round(float(wp['y']), 2)), 'z': '1.0', 'yaw': str(round(float(wp['yaw']), 0)), 'pitch': str(round(float(wp['pitch']), 0))}
        entry['transform'] = transform
        entry['other_actors'] = {}
        json.dump(entry, fd, indent=4)

def prettify_json(args):
    with open(args.file) as fd:
        json_dict = json.load(fd)
    if not json_dict:
        print('[Error] The file [{}] could not be parsed.'.format(args.file))
        return -1
    progress = dictor(json_dict, '_checkpoint.progress')
    records_table = dictor(json_dict, '_checkpoint.records')
    sensors = dictor(json_dict, 'sensors')
    labels_scores = dictor(json_dict, 'labels')
    scores = dictor(json_dict, 'values')
    output = ''
    if progress:
        output += '* {}% ({}/{}) routes completed\n'.format(100.0 * progress[0] / float(progress[1]), progress[0], progress[1])
    if sensors:
        output += '* The agent used the following sensors: {}\n\n'.format(', '.join(sensors))
    if scores and labels_scores:
        metrics = list(zip(*[labels_scores[0:3], scores[0:3]]))
        infractions = list(zip(*[labels_scores[3:], scores[3:]]))
        output += '=== Global average metrics: ===\n'
        output += tabulate(metrics, tablefmt=args.format)
        output += '\n\n'
        output += '=== Total infractions: ===\n'
        output += tabulate(infractions, tablefmt=args.format)
        output += '\n\n'
    if records_table:
        header = ['metric', 'value', 'additional information']
        list_statistics = [header]
        total_duration_game = 0
        total_duration_system = 0
        total_route_length = 0
        for route in records_table:
            route_completed_kms = 0.01 * route['scores']['score_route'] * route['meta']['route_length'] / 1000.0
            metrics_route = [[key, '{:.3f}'.format(values), ''] for key, values in route['scores'].items()]
            infractions_route = [[key, '{:.3f} ({} occurrences)'.format(len(values) / route_completed_kms, len(values)), '\n'.join(values)] for key, values in route['infractions'].items()]
            times = [['duration game', '{:.3f}'.format(route['meta']['duration_game']), 'seconds'], ['duration system', '{:.3f}'.format(route['meta']['duration_system']), 'seconds']]
            route_completed_length = [['distance driven', '{:.3f}'.format(route_completed_kms), 'Km']]
            total_duration_game += route['meta']['duration_game']
            total_duration_system += route['meta']['duration_system']
            total_route_length += route_completed_kms
            list_statistics.extend([['{}'.format(route['route_id']), '', '']])
            list_statistics.extend([*metrics_route, *infractions_route, *times, *route_completed_length])
            list_statistics.extend([['', '', '']])
        list_statistics.extend([['total duration_game', '{:.3f}'.format(total_duration_game), 'seconds']])
        list_statistics.extend([['total duration_system', '{:.3f}'.format(total_duration_system), 'seconds']])
        list_statistics.extend([['total distance driven', '{:.3f}'.format(total_route_length), 'Km']])
        output += '==== Per-route analysis: ===\n'.format()
        output += tabulate(list_statistics, tablefmt=args.format)
    if args.output:
        with open(args.output, 'w') as fd:
            fd.write(output)
    else:
        print(output)
    return 0

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

def get_actor_display_name(actor, truncate=250):
    name = ' '.join(actor.type_id.replace('_', '.').title().split('.')[1:])
    return name[:truncate - 1] + u'…' if len(name) > truncate else name

class WorldSR(World):
    restarted = False

    def restart(self):
        if self.restarted:
            return
        self.restarted = True
        self.player_max_speed = 1.589
        self.player_max_speed_fast = 3.713
        cam_index = self.camera_manager.index if self.camera_manager is not None else 0
        cam_pos_index = self.camera_manager.transform_index if self.camera_manager is not None else 0
        while self.player is None:
            print('Waiting for the ego vehicle...')
            time.sleep(1)
            possible_vehicles = self.world.get_actors().filter('vehicle.*')
            for vehicle in possible_vehicles:
                if vehicle.attributes['role_name'] == 'hero':
                    print('Ego vehicle found')
                    self.player = vehicle
                    break
        self.player_name = self.player.type_id
        self.collision_sensor = CollisionSensor(self.player, self.hud)
        self.lane_invasion_sensor = LaneInvasionSensor(self.player, self.hud)
        self.gnss_sensor = GnssSensor(self.player)
        self.imu_sensor = IMUSensor(self.player)
        self.camera_manager = CameraManager(self.player, self.hud, self._gamma)
        self.camera_manager.transform_index = cam_pos_index
        self.camera_manager.set_sensor(cam_index, notify=False)
        actor_type = get_actor_display_name(self.player)
        self.hud.notification(actor_type)

    def tick(self, clock):
        if len(self.world.get_actors().filter(self.player_name)) < 1:
            return False
        self.hud.tick(self, clock)
        return True

def tick(self, clock):
    if len(self.world.get_actors().filter(self.player_name)) < 1:
        return False
    self.hud.tick(self, clock)
    return True

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

def get_actor_display_name(actor, truncate=250):
    name = ' '.join(actor.type_id.replace('_', '.').title().split('.')[1:])
    return name[:truncate - 1] + u'…' if len(name) > truncate else name

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

def select_hero_actor(self):
    hero_vehicles = [actor for actor in self.world.get_actors() if 'vehicle' in actor.type_id and actor.attributes['role_name'] == 'hero']
    if len(hero_vehicles) > 0:
        self.hero_actor = random.choice(hero_vehicles)
        self.hero_transform = self.hero_actor.get_transform()
    else:
        self._spawn_hero()

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

class Scenario(object):
    """
    Basic scenario class. This class holds the behavior_tree describing the
    scenario and the test criteria.

    The user must not modify this class.

    Important parameters:
    - behavior: User defined scenario with py_tree
    - criteria_list: List of user defined test criteria with py_tree
    - timeout (default = 60s): Timeout of the scenario in seconds
    - terminate_on_failure: Terminate scenario on first failure
    """

    def __init__(self, behavior, criteria, name, timeout=60, terminate_on_failure=False):
        self.behavior = behavior
        self.test_criteria = criteria
        self.timeout = timeout
        self.name = name
        if self.test_criteria is not None and (not isinstance(self.test_criteria, py_trees.composites.Parallel)):
            for criterion in self.test_criteria:
                criterion.terminate_on_failure = terminate_on_failure
            self.criteria_tree = py_trees.composites.Parallel(name='Test Criteria', policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)
            self.criteria_tree.add_children(self.test_criteria)
            self.criteria_tree.setup(timeout=1)
        else:
            self.criteria_tree = criteria
        self.timeout_node = TimeOut(self.timeout, name='TimeOut')
        self.scenario_tree = py_trees.composites.Parallel(name, policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)
        if behavior is not None:
            self.scenario_tree.add_child(self.behavior)
        self.scenario_tree.add_child(self.timeout_node)
        self.scenario_tree.add_child(WeatherBehavior())
        self.scenario_tree.add_child(UpdateAllActorControls())
        if criteria is not None:
            self.scenario_tree.add_child(self.criteria_tree)
        self.scenario_tree.setup(timeout=1)

    def _extract_nodes_from_tree(self, tree):
        """
        Returns the list of all nodes from the given tree
        """
        node_list = [tree]
        more_nodes_exist = True
        while more_nodes_exist:
            more_nodes_exist = False
            for node in node_list:
                if node.children:
                    node_list.remove(node)
                    more_nodes_exist = True
                    for child in node.children:
                        node_list.append(child)
        if len(node_list) == 1 and isinstance(node_list[0], py_trees.composites.Parallel):
            return []
        return node_list

    def get_criteria(self):
        """
        Return the list of test criteria (all leave nodes)
        """
        criteria_list = self._extract_nodes_from_tree(self.criteria_tree)
        return criteria_list

    def terminate(self):
        """
        This function sets the status of all leaves in the scenario tree to INVALID
        """
        node_list = self._extract_nodes_from_tree(self.scenario_tree)
        for node in node_list:
            node.terminate(py_trees.common.Status.INVALID)
        actor_dict = {}
        try:
            check_actors = operator.attrgetter('ActorsWithController')
            actor_dict = check_actors(py_trees.blackboard.Blackboard())
        except AttributeError:
            pass
        for actor_id in actor_dict:
            actor_dict[actor_id].reset()
        py_trees.blackboard.Blackboard().set('ActorsWithController', {}, overwrite=True)

def _extract_nodes_from_tree(self, tree):
    """
        Returns the list of all nodes from the given tree
        """
    node_list = [tree]
    more_nodes_exist = True
    while more_nodes_exist:
        more_nodes_exist = False
        for node in node_list:
            if node.children:
                node_list.remove(node)
                more_nodes_exist = True
                for child in node.children:
                    node_list.append(child)
    if len(node_list) == 1 and isinstance(node_list[0], py_trees.composites.Parallel):
        return []
    return node_list

def convert_json_to_actor(actor_dict):
    """
    Convert a JSON string to an ActorConfigurationData dictionary
    """
    node = ET.Element('waypoint')
    node.set('x', actor_dict['x'])
    node.set('y', actor_dict['y'])
    node.set('z', actor_dict['z'])
    node.set('yaw', actor_dict['yaw'])
    return ActorConfigurationData.parse_from_node(node, 'simulation')

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
def generate_spawn_points():
    """
        Generate spawn points for the current map
        """
    spawn_points = list(CarlaDataProvider.get_map(CarlaDataProvider._world).get_spawn_points())
    CarlaDataProvider._rng.shuffle(spawn_points)
    CarlaDataProvider._spawn_points = spawn_points
    CarlaDataProvider._spawn_index = 0

class ResultOutputProvider(object):
    """
    This module contains the _result gatherer and write for CARLA scenarios.
    It shall be used from the ScenarioManager only.
    """

    def __init__(self, data, result, stdout=True, filename=None, junit=None):
        """
        Setup all parameters
        - _data contains all scenario-related information
        - _result is overall pass/fail info
        - _stdout (True/False) is used to (de)activate terminal output
        - _filename is used to (de)activate file output in tabular form
        - _junit is used to (de)activate file output in _junit form
        """
        self._data = data
        self._result = result
        self._stdout = stdout
        self._filename = filename
        self._junit = junit
        self._start_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self._data.start_system_time))
        self._end_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self._data.end_system_time))

    def write(self):
        """
        Public write function
        """
        if self._junit is not None:
            self._write_to_junit()
        output = self.create_output_text()
        if self._filename is not None:
            with open(self._filename, 'w') as fd:
                fd.write(output)
        if self._stdout:
            print(output)

    def create_output_text(self):
        """
        Creates the output message
        """
        output = '\n'
        output += ' ======= Results of Scenario: {} ---- {} =======\n'.format(self._data.scenario_tree.name, self._result)
        end_line_length = len(output) - 3
        output += '\n'
        output += ' > Ego vehicles:\n'
        for ego_vehicle in self._data.ego_vehicles:
            output += '{}; '.format(ego_vehicle)
        output += '\n\n'
        output += ' > Other actors:\n'
        for actor in self._data.other_actors:
            output += '{}; '.format(actor)
        output += '\n\n'
        output += ' > Simulation Information\n'
        system_time = round(self._data.scenario_duration_system, 2)
        game_time = round(self._data.scenario_duration_game, 2)
        ratio = round(self._data.scenario_duration_game / self._data.scenario_duration_system, 3)
        list_statistics = [['Start Time', '{}'.format(self._start_time)]]
        list_statistics.extend([['End Time', '{}'.format(self._end_time)]])
        list_statistics.extend([['Duration (System Time)', '{}s'.format(system_time)]])
        list_statistics.extend([['Duration (Game Time)', '{}s'.format(game_time)]])
        list_statistics.extend([['Ratio (System Time / Game Time)', '{}s'.format(ratio)]])
        output += tabulate(list_statistics, tablefmt='fancy_grid')
        output += '\n\n'
        output += ' > Criteria Information\n'
        header = ['Actor', 'Criterion', 'Result', 'Actual Value', 'Expected Value']
        list_statistics = [header]
        for criterion in self._data.scenario.get_criteria():
            name_string = criterion.name
            if criterion.optional:
                name_string += ' (Opt.)'
            else:
                name_string += ' (Req.)'
            actor = '{} (id={})'.format(criterion.actor.type_id[8:], criterion.actor.id)
            criteria = name_string
            result = 'FAILURE' if criterion.test_status == 'RUNNING' else criterion.test_status
            actual_value = criterion.actual_value
            expected_value = criterion.expected_value_success
            list_statistics.extend([[actor, criteria, result, actual_value, expected_value]])
        actor = ''
        criteria = 'Timeout (Req.)'
        result = 'SUCCESS' if self._data.scenario_duration_game < self._data.scenario.timeout else 'FAILURE'
        actual_value = round(self._data.scenario_duration_game, 2)
        expected_value = round(self._data.scenario.timeout, 2)
        list_statistics.extend([[actor, criteria, result, actual_value, expected_value]])
        list_statistics.extend([['', 'GLOBAL RESULT', self._result, '', '']])
        output += tabulate(list_statistics, tablefmt='fancy_grid')
        output += '\n'
        output += ' ' + '=' * end_line_length + '\n'
        return output

    def _write_to_junit(self):
        """
        Writing to Junit XML
        """
        test_count = 0
        failure_count = 0
        for criterion in self._data.scenario.get_criteria():
            test_count += 1
            if criterion.test_status != 'SUCCESS':
                failure_count += 1
        test_count += 1
        if self._data.scenario_duration_game >= self._data.scenario.timeout:
            failure_count += 1
        junit_file = open(self._junit, 'w')
        junit_file.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        test_suites_string = '<testsuites tests="%d" failures="%d" disabled="0" errors="0" timestamp="%s" time="%5.2f" name="Simulation" package="Scenarios">\n' % (test_count, failure_count, self._start_time, self._data.scenario_duration_system)
        junit_file.write(test_suites_string)
        test_suite_string = '  <testsuite name="%s" tests="%d" failures="%d" disabled="0" errors="0" time="%5.2f">\n' % (self._data.scenario_tree.name, test_count, failure_count, self._data.scenario_duration_system)
        junit_file.write(test_suite_string)
        for criterion in self._data.scenario.get_criteria():
            testcase_name = criterion.name + '_' + criterion.actor.type_id[8:] + '_' + str(criterion.actor.id)
            result_string = '    <testcase name="{}" status="run" time="0" classname="Scenarios.{}">\n'.format(testcase_name, self._data.scenario_tree.name)
            if criterion.test_status != 'SUCCESS':
                result_string += '      <failure message="{}"  type=""><!\\[CDATA\\[\n'.format(criterion.name)
                result_string += '  Actual:   {}\n'.format(criterion.actual_value)
                result_string += '  Expected: {}\n'.format(criterion.expected_value_success)
                result_string += '\n'
                result_string += '  Exact Value: {} = {}\\]\\]></failure>\n'.format(criterion.name, criterion.actual_value)
            else:
                result_string += '  Exact Value: {} = {}\n'.format(criterion.name, criterion.actual_value)
            result_string += '    </testcase>\n'
            junit_file.write(result_string)
        result_string = '    <testcase name="Duration" status="run" time="{}" classname="Scenarios.{}">\n'.format(self._data.scenario_duration_system, self._data.scenario_tree.name)
        if self._data.scenario_duration_game >= self._data.scenario.timeout:
            result_string += '      <failure message="{}"  type=""><!\\[CDATA\\[\n'.format('Duration')
            result_string += '  Actual:   {}\n'.format(self._data.scenario_duration_game)
            result_string += '  Expected: {}\n'.format(self._data.scenario.timeout)
            result_string += '\n'
            result_string += '  Exact Value: {} = {}\\]\\]></failure>\n'.format('Duration', self._data.scenario_duration_game)
        else:
            result_string += '  Exact Value: {} = {}\n'.format('Duration', self._data.scenario_duration_game)
        result_string += '    </testcase>\n'
        junit_file.write(result_string)
        junit_file.write('  </testsuite>\n')
        junit_file.write('</testsuites>\n')
        junit_file.close()

def __init__(self, data, result, stdout=True, filename=None, junit=None):
    """
        Setup all parameters
        - _data contains all scenario-related information
        - _result is overall pass/fail info
        - _stdout (True/False) is used to (de)activate terminal output
        - _filename is used to (de)activate file output in tabular form
        - _junit is used to (de)activate file output in _junit form
        """
    self._data = data
    self._result = result
    self._stdout = stdout
    self._filename = filename
    self._junit = junit
    self._start_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self._data.start_system_time))
    self._end_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self._data.end_system_time))

def write(self):
    """
        Public write function
        """
    if self._junit is not None:
        self._write_to_junit()
    output = self.create_output_text()
    if self._filename is not None:
        with open(self._filename, 'w') as fd:
            fd.write(output)
    if self._stdout:
        print(output)

def _write_to_junit(self):
    """
        Writing to Junit XML
        """
    test_count = 0
    failure_count = 0
    for criterion in self._data.scenario.get_criteria():
        test_count += 1
        if criterion.test_status != 'SUCCESS':
            failure_count += 1
    test_count += 1
    if self._data.scenario_duration_game >= self._data.scenario.timeout:
        failure_count += 1
    junit_file = open(self._junit, 'w')
    junit_file.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    test_suites_string = '<testsuites tests="%d" failures="%d" disabled="0" errors="0" timestamp="%s" time="%5.2f" name="Simulation" package="Scenarios">\n' % (test_count, failure_count, self._start_time, self._data.scenario_duration_system)
    junit_file.write(test_suites_string)
    test_suite_string = '  <testsuite name="%s" tests="%d" failures="%d" disabled="0" errors="0" time="%5.2f">\n' % (self._data.scenario_tree.name, test_count, failure_count, self._data.scenario_duration_system)
    junit_file.write(test_suite_string)
    for criterion in self._data.scenario.get_criteria():
        testcase_name = criterion.name + '_' + criterion.actor.type_id[8:] + '_' + str(criterion.actor.id)
        result_string = '    <testcase name="{}" status="run" time="0" classname="Scenarios.{}">\n'.format(testcase_name, self._data.scenario_tree.name)
        if criterion.test_status != 'SUCCESS':
            result_string += '      <failure message="{}"  type=""><!\\[CDATA\\[\n'.format(criterion.name)
            result_string += '  Actual:   {}\n'.format(criterion.actual_value)
            result_string += '  Expected: {}\n'.format(criterion.expected_value_success)
            result_string += '\n'
            result_string += '  Exact Value: {} = {}\\]\\]></failure>\n'.format(criterion.name, criterion.actual_value)
        else:
            result_string += '  Exact Value: {} = {}\n'.format(criterion.name, criterion.actual_value)
        result_string += '    </testcase>\n'
        junit_file.write(result_string)
    result_string = '    <testcase name="Duration" status="run" time="{}" classname="Scenarios.{}">\n'.format(self._data.scenario_duration_system, self._data.scenario_tree.name)
    if self._data.scenario_duration_game >= self._data.scenario.timeout:
        result_string += '      <failure message="{}"  type=""><!\\[CDATA\\[\n'.format('Duration')
        result_string += '  Actual:   {}\n'.format(self._data.scenario_duration_game)
        result_string += '  Expected: {}\n'.format(self._data.scenario.timeout)
        result_string += '\n'
        result_string += '  Exact Value: {} = {}\\]\\]></failure>\n'.format('Duration', self._data.scenario_duration_game)
    else:
        result_string += '  Exact Value: {} = {}\n'.format('Duration', self._data.scenario_duration_game)
    result_string += '    </testcase>\n'
    junit_file.write(result_string)
    junit_file.write('  </testsuite>\n')
    junit_file.write('</testsuites>\n')
    junit_file.close()

class RunScript(AtomicBehavior):
    """
    This is an atomic behavior to start execution of an additional script.

    Args:
        script (str): String containing the interpreter, scriptpath and arguments
            Example: "python /path/to/script.py --arg1"
        base_path (str): String containing the base path of for the script

    Attributes:
        _script (str): String containing the interpreter, scriptpath and arguments
            Example: "python /path/to/script.py --arg1"
        _base_path (str): String containing the base path of for the script
            Example: "/path/to/"

    Note:
        This is intended for the use with OpenSCENARIO. Be aware of security side effects.
    """

    def __init__(self, script, base_path=None, name='RunScript'):
        """
        Setup parameters
        """
        super(RunScript, self).__init__(name)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._script = script
        self._base_path = base_path

    def update(self):
        """
        Start script
        """
        path = None
        script_components = self._script.split(' ')
        if len(script_components) > 1:
            path = script_components[1]
        if not os.path.isfile(path):
            path = os.path.join(self._base_path, path)
        if not os.path.isfile(path):
            new_status = py_trees.common.Status.FAILURE
            print('Script file does not exists {}'.format(path))
        else:
            subprocess.Popen(self._script, shell=True, cwd=self._base_path)
            new_status = py_trees.common.Status.SUCCESS
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

def update(self):
    """
        Start script
        """
    path = None
    script_components = self._script.split(' ')
    if len(script_components) > 1:
        path = script_components[1]
    if not os.path.isfile(path):
        path = os.path.join(self._base_path, path)
    if not os.path.isfile(path):
        new_status = py_trees.common.Status.FAILURE
        print('Script file does not exists {}'.format(path))
    else:
        subprocess.Popen(self._script, shell=True, cwd=self._base_path)
        new_status = py_trees.common.Status.SUCCESS
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    return new_status

class ChangeNoiseParameters(AtomicBehavior):
    """
    This class contains an atomic jitter behavior.
    To add noise to steer as well as throttle of the vehicle.

    This behavior should be used in conjuction with AddNoiseToVehicle

    The behavior terminates after one iteration
    """

    def __init__(self, new_steer_noise, new_throttle_noise, noise_mean, noise_std, dynamic_mean_for_steer, dynamic_mean_for_throttle, name='ChangeJittering'):
        """
        Setup actor , maximum steer value and throttle value
        """
        super(ChangeNoiseParameters, self).__init__(name)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._new_steer_noise = new_steer_noise
        self._new_throttle_noise = new_throttle_noise
        self._noise_mean = noise_mean
        self._noise_std = noise_std
        self._dynamic_mean_for_steer = dynamic_mean_for_steer
        self._dynamic_mean_for_throttle = dynamic_mean_for_throttle
        self._noise_to_apply = abs(random.gauss(self._noise_mean, self._noise_std))

    def update(self):
        """
        Change the noise parameters from the structure copy that it receives.
        """
        self._new_steer_noise[0] = min(0, -(self._noise_to_apply - self._dynamic_mean_for_steer))
        self._new_throttle_noise[0] = min(self._noise_to_apply + self._dynamic_mean_for_throttle, 1)
        new_status = py_trees.common.Status.SUCCESS
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

def update(self):
    """
        Change the noise parameters from the structure copy that it receives.
        """
    self._new_steer_noise[0] = min(0, -(self._noise_to_apply - self._dynamic_mean_for_steer))
    self._new_throttle_noise[0] = min(self._noise_to_apply + self._dynamic_mean_for_throttle, 1)
    new_status = py_trees.common.Status.SUCCESS
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    return new_status

class ActorDestroy(AtomicBehavior):
    """
    This class contains an actor destroy behavior.
    Given an actor this behavior will delete it.

    Important parameters:
    - actor: CARLA actor to be deleted

    The behavior terminates after removing the actor
    """

    def __init__(self, actor, name='ActorDestroy'):
        """
        Setup actor
        """
        super(ActorDestroy, self).__init__(name, actor)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)

    def update(self):
        new_status = py_trees.common.Status.RUNNING
        if self._actor:
            CarlaDataProvider.remove_actor_by_id(self._actor.id)
            self._actor = None
            new_status = py_trees.common.Status.SUCCESS
        return new_status

def update(self):
    new_status = py_trees.common.Status.RUNNING
    if self._actor:
        CarlaDataProvider.remove_actor_by_id(self._actor.id)
        self._actor = None
        new_status = py_trees.common.Status.SUCCESS
    return new_status

class ActorSource(AtomicBehavior):
    """
    Implementation for a behavior that will indefinitely create actors
    at a given transform if no other actor exists in a given radius
    from the transform.

    Important parameters:
    - actor_type_list: Type of CARLA actors to be spawned
    - transform: Spawn location
    - threshold: Min available free distance between other actors and the spawn location
    - blackboard_queue_name: Name of the blackboard used to control this behavior
    - actor_limit [optional]: Maximum number of actors to be spawned (default=7)

    A parallel termination behavior has to be used.
    """

    def __init__(self, actor_type_list, transform, threshold, blackboard_queue_name, actor_limit=7, name='ActorSource'):
        """
        Setup class members
        """
        super(ActorSource, self).__init__(name)
        self._world = CarlaDataProvider.get_world()
        self._actor_types = actor_type_list
        self._spawn_point = transform
        self._threshold = threshold
        self._queue = Blackboard().get(blackboard_queue_name)
        self._actor_limit = actor_limit
        self._last_blocking_actor = None

    def update(self):
        new_status = py_trees.common.Status.RUNNING
        if self._actor_limit > 0:
            world_actors = self._world.get_actors()
            spawn_point_blocked = False
            if self._last_blocking_actor and self._spawn_point.location.distance(self._last_blocking_actor.get_location()) < self._threshold:
                spawn_point_blocked = True
            if not spawn_point_blocked:
                for actor in world_actors:
                    if self._spawn_point.location.distance(actor.get_location()) < self._threshold:
                        spawn_point_blocked = True
                        self._last_blocking_actor = actor
                        break
            if not spawn_point_blocked:
                try:
                    new_actor = CarlaDataProvider.request_new_actor(np.random.choice(self._actor_types), self._spawn_point)
                    self._actor_limit -= 1
                    self._queue.put(new_actor)
                except:
                    print('ActorSource unable to spawn actor')
        return new_status

def update(self):
    new_status = py_trees.common.Status.RUNNING
    if self._actor_limit > 0:
        world_actors = self._world.get_actors()
        spawn_point_blocked = False
        if self._last_blocking_actor and self._spawn_point.location.distance(self._last_blocking_actor.get_location()) < self._threshold:
            spawn_point_blocked = True
        if not spawn_point_blocked:
            for actor in world_actors:
                if self._spawn_point.location.distance(actor.get_location()) < self._threshold:
                    spawn_point_blocked = True
                    self._last_blocking_actor = actor
                    break
        if not spawn_point_blocked:
            try:
                new_actor = CarlaDataProvider.request_new_actor(np.random.choice(self._actor_types), self._spawn_point)
                self._actor_limit -= 1
                self._queue.put(new_actor)
            except:
                print('ActorSource unable to spawn actor')
    return new_status

class TrafficLightManipulator(AtomicBehavior):
    """
    Atomic behavior that manipulates traffic lights around the ego_vehicle to trigger scenarios 7 to 10.
    This is done by setting 2 of the traffic light at the intersection to green (with some complex precomputation
    to set everything up).

    Important parameters:
    - ego_vehicle: CARLA actor that controls this behavior
    - subtype: string that gathers information of the route and scenario number
      (check SUBTYPE_CONFIG_TRANSLATION below)
    """
    RED = carla.TrafficLightState.Red
    YELLOW = carla.TrafficLightState.Yellow
    GREEN = carla.TrafficLightState.Green
    RED_TIME = 1.5
    YELLOW_TIME = 2
    RESET_TIME = 6
    TRIGGER_DISTANCE = 10
    DIST_TO_WAITING_TIME = 0.04
    INT_CONF_OPP1 = {'ego': RED, 'ref': RED, 'left': RED, 'right': RED, 'opposite': GREEN}
    INT_CONF_OPP2 = {'ego': GREEN, 'ref': GREEN, 'left': RED, 'right': RED, 'opposite': GREEN}
    INT_CONF_LFT1 = {'ego': RED, 'ref': RED, 'left': GREEN, 'right': RED, 'opposite': RED}
    INT_CONF_LFT2 = {'ego': GREEN, 'ref': GREEN, 'left': GREEN, 'right': RED, 'opposite': RED}
    INT_CONF_RGT1 = {'ego': RED, 'ref': RED, 'left': RED, 'right': GREEN, 'opposite': RED}
    INT_CONF_RGT2 = {'ego': GREEN, 'ref': GREEN, 'left': RED, 'right': GREEN, 'opposite': RED}
    INT_CONF_REF1 = {'ego': GREEN, 'ref': GREEN, 'left': RED, 'right': RED, 'opposite': RED}
    INT_CONF_REF2 = {'ego': YELLOW, 'ref': YELLOW, 'left': RED, 'right': RED, 'opposite': RED}
    SUBTYPE_CONFIG_TRANSLATION = {'S7left': ['left', 'opposite', 'right'], 'S7right': ['left', 'opposite'], 'S7opposite': ['right', 'left', 'opposite'], 'S8left': ['opposite'], 'S9right': ['left', 'opposite']}
    CONFIG_TLM_TRANSLATION = {'left': [INT_CONF_LFT1, INT_CONF_LFT2], 'right': [INT_CONF_RGT1, INT_CONF_RGT2], 'opposite': [INT_CONF_OPP1, INT_CONF_OPP2]}

    def __init__(self, ego_vehicle, subtype, debug=False, name='TrafficLightManipulator'):
        super(TrafficLightManipulator, self).__init__(name)
        self.ego_vehicle = ego_vehicle
        self.subtype = subtype
        self.current_step = 1
        self.debug = debug
        self.traffic_light = None
        self.annotations = None
        self.configuration = None
        self.prev_junction_state = None
        self.junction_location = None
        self.seconds_waited = 0
        self.prev_time = None
        self.max_trigger_distance = None
        self.waiting_time = None
        self.inside_junction = False
        self.logger.debug('%s.__init__()' % self.__class__.__name__)

    def update(self):
        new_status = py_trees.common.Status.RUNNING
        if self.current_step == 1:
            self.traffic_light = CarlaDataProvider.get_next_traffic_light(self.ego_vehicle, use_cached_location=False)
            if not self.traffic_light:
                return new_status
            self.annotations = CarlaDataProvider.annotate_trafficlight_in_group(self.traffic_light)
            self.configuration = self.get_traffic_light_configuration(self.subtype, self.annotations)
            if self.configuration is None:
                self.current_step = 0
                return new_status
            self.prev_junction_state = self.set_intersection_state(self.INT_CONF_REF1)
            self.current_step += 1
            if self.debug:
                print('--- All set up')
        elif self.current_step == 2:
            ego_location = CarlaDataProvider.get_location(self.ego_vehicle)
            if self.junction_location is None:
                ego_waypoint = CarlaDataProvider.get_map().get_waypoint(ego_location)
                junction_waypoint = ego_waypoint.next(0.5)[0]
                while not junction_waypoint.is_junction:
                    next_wp = junction_waypoint.next(0.5)[0]
                    junction_waypoint = next_wp
                self.junction_location = junction_waypoint.transform.location
            distance = ego_location.distance(self.junction_location)
            if self.max_trigger_distance is None:
                self.max_trigger_distance = distance + 1
            if distance > self.max_trigger_distance:
                self.current_step = 0
            elif distance < self.TRIGGER_DISTANCE:
                _ = self.set_intersection_state(self.INT_CONF_REF2)
                self.current_step += 1
            if self.debug:
                print('--- Distance until traffic light changes: {}'.format(distance))
        elif self.current_step == 3:
            if self.passed_enough_time(self.YELLOW_TIME):
                _ = self.set_intersection_state(self.CONFIG_TLM_TRANSLATION[self.configuration][0])
                self.current_step += 1
        elif self.current_step == 4:
            if self.waiting_time is None:
                self.waiting_time = self.get_waiting_time(self.annotations, self.configuration)
            if self.passed_enough_time(self.waiting_time):
                _ = self.set_intersection_state(self.CONFIG_TLM_TRANSLATION[self.configuration][1])
                self.current_step += 1
        elif self.current_step == 5:
            ego_location = CarlaDataProvider.get_location(self.ego_vehicle)
            ego_waypoint = CarlaDataProvider.get_map().get_waypoint(ego_location)
            if not self.inside_junction:
                if ego_waypoint.is_junction:
                    self.inside_junction = True
                elif self.debug:
                    print('--- Waiting to ENTER a junction')
            elif ego_waypoint.is_junction:
                if self.debug:
                    print('--- Waiting to EXIT a junction')
            else:
                self.inside_junction = False
                self.current_step += 1
        else:
            if self.prev_junction_state:
                CarlaDataProvider.reset_lights(self.prev_junction_state)
                if self.debug:
                    print('--- Returning the intersection to its previous state')
            self.variable_cleanup()
            new_status = py_trees.common.Status.SUCCESS
        return new_status

    def passed_enough_time(self, time_limit):
        """
        Returns true or false depending on the time that has passed from the
        first time this function was called
        """
        if self.prev_time is None:
            self.prev_time = GameTime.get_time()
        timestamp = GameTime.get_time()
        self.seconds_waited += timestamp - self.prev_time
        self.prev_time = timestamp
        if self.debug:
            print('--- Waited seconds: {}'.format(self.seconds_waited))
        if self.seconds_waited >= time_limit:
            self.seconds_waited = 0
            self.prev_time = None
            return True
        return False

    def set_intersection_state(self, choice):
        """
        Changes the intersection to the desired state
        """
        prev_state = CarlaDataProvider.update_light_states(self.traffic_light, self.annotations, choice, freeze=True)
        return prev_state

    def get_waiting_time(self, annotation, direction):
        """
        Calculates the time the ego traffic light will remain red
        to let vehicles enter the junction
        """
        tl = annotation[direction][0]
        ego_tl = annotation['ref'][0]
        tl_location = CarlaDataProvider.get_trafficlight_trigger_location(tl)
        ego_tl_location = CarlaDataProvider.get_trafficlight_trigger_location(ego_tl)
        distance = ego_tl_location.distance(tl_location)
        return self.RED_TIME + distance * self.DIST_TO_WAITING_TIME

    def get_traffic_light_configuration(self, subtype, annotations):
        """
        Checks the list of possible altered traffic lights and gets
        the first one that exists in the intersection

        Important parameters:
        - subtype: Subtype of the scenario
        - annotations: list of the traffic light of the junction, with their direction (right, left...)
        """
        configuration = None
        if subtype in self.SUBTYPE_CONFIG_TRANSLATION:
            possible_configurations = self.SUBTYPE_CONFIG_TRANSLATION[self.subtype]
            while possible_configurations:
                configuration = possible_configurations[0]
                possible_configurations = possible_configurations[1:]
                if configuration in annotations:
                    if annotations[configuration]:
                        break
                    else:
                        configuration = None
                else:
                    if self.debug:
                        print('This configuration name is wrong')
                    configuration = None
            if configuration is None and self.debug:
                print('This subtype has no traffic light available')
        elif self.debug:
            print('This subtype is unknown')
        return configuration

    def variable_cleanup(self):
        """
        Resets all variables to the intial state
        """
        self.current_step = 1
        self.traffic_light = None
        self.annotations = None
        self.configuration = None
        self.prev_junction_state = None
        self.junction_location = None
        self.max_trigger_distance = None
        self.waiting_time = None
        self.inside_junction = False

def get_traffic_light_configuration(self, subtype, annotations):
    """
        Checks the list of possible altered traffic lights and gets
        the first one that exists in the intersection

        Important parameters:
        - subtype: Subtype of the scenario
        - annotations: list of the traffic light of the junction, with their direction (right, left...)
        """
    configuration = None
    if subtype in self.SUBTYPE_CONFIG_TRANSLATION:
        possible_configurations = self.SUBTYPE_CONFIG_TRANSLATION[self.subtype]
        while possible_configurations:
            configuration = possible_configurations[0]
            possible_configurations = possible_configurations[1:]
            if configuration in annotations:
                if annotations[configuration]:
                    break
                else:
                    configuration = None
            else:
                if self.debug:
                    print('This configuration name is wrong')
                configuration = None
        if configuration is None and self.debug:
            print('This subtype has no traffic light available')
    elif self.debug:
        print('This subtype is unknown')
    return configuration

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

def generate_target_waypoint(waypoint, turn=0):
    """
    This method follow waypoints to a junction and choose path based on turn input.
    Turn input: LEFT -> -1, RIGHT -> 1, STRAIGHT -> 0
    @returns a waypoint list according to turn input
    """
    sampling_radius = 1
    reached_junction = False
    wp_list = []
    while True:
        wp_choice = waypoint.next(sampling_radius)
        if not reached_junction and (len(wp_choice) > 1 or wp_choice[0].is_junction):
            reached_junction = True
            waypoint = choose_at_junction(waypoint, wp_choice, turn)
        else:
            waypoint = wp_choice[0]
        wp_list.append(waypoint)
        if reached_junction and (not wp_list[-1].is_junction):
            break
    return wp_list[-1]

def generate_target_waypoint_in_route(waypoint, route):
    """
    This method follow waypoints to a junction
    @returns a waypoint list according to turn input
    """
    wmap = CarlaDataProvider.get_map()
    reached_junction = False
    shortest_distance = float('inf')
    for index, route_pos in enumerate(route):
        wp = route_pos[0]
        trigger_location = waypoint.transform.location
        dist_to_route = trigger_location.distance(wp)
        if dist_to_route <= shortest_distance:
            closest_index = index
            shortest_distance = dist_to_route
    route_location = route[closest_index][0]
    index = closest_index
    while True:
        index = min(index + 1, len(route))
        route_location = route[index][0]
        road_option = route[index][1]
        if not reached_junction and road_option in (RoadOption.LEFT, RoadOption.RIGHT, RoadOption.STRAIGHT):
            reached_junction = True
        if reached_junction and road_option not in (RoadOption.LEFT, RoadOption.RIGHT, RoadOption.STRAIGHT):
            break
    return wmap.get_waypoint(route_location)

def _get_latlon_ref(world):
    """
    Convert from waypoints world coordinates to CARLA GPS coordinates
    :return: tuple with lat and lon coordinates
    """
    xodr = world.get_map().to_opendrive()
    tree = ET.ElementTree(ET.fromstring(xodr))
    lat_ref = 42.0
    lon_ref = 2.0
    for opendrive in tree.iter('OpenDRIVE'):
        for header in opendrive.iter('header'):
            for georef in header.iter('geoReference'):
                if georef.text:
                    str_list = georef.text.split(' ')
                    for item in str_list:
                        if '+lat_0' in item:
                            lat_ref = float(item.split('=')[1])
                        if '+lon_0' in item:
                            lon_ref = float(item.split('=')[1])
    return (lat_ref, lon_ref)

def downsample_route(route, sample_factor):
    """
    Downsample the route by some factor.
    :param route: the trajectory , has to contain the waypoints and the road options
    :param sample_factor: Maximum distance between samples
    :return: returns the ids of the final route that can
    """
    ids_to_sample = []
    prev_option = None
    dist = 0
    for i, point in enumerate(route):
        curr_option = point[1]
        if curr_option in (RoadOption.CHANGELANELEFT, RoadOption.CHANGELANERIGHT):
            ids_to_sample.append(i)
            dist = 0
        elif prev_option != curr_option and prev_option not in (RoadOption.CHANGELANELEFT, RoadOption.CHANGELANERIGHT):
            ids_to_sample.append(i)
            dist = 0
        elif dist > sample_factor:
            ids_to_sample.append(i)
            dist = 0
        elif i == len(route) - 1:
            ids_to_sample.append(i)
            dist = 0
        else:
            curr_location = point[0].location
            prev_location = route[i - 1][0].location
            dist += curr_location.distance(prev_location)
        prev_option = curr_option
    return ids_to_sample

class RouteParser(object):
    """
    Pure static class used to parse all the route and scenario configuration parameters.
    """

    @staticmethod
    def parse_annotations_file(annotation_filename):
        """
        Return the annotations of which positions where the scenarios are going to happen.
        :param annotation_filename: the filename for the anotations file
        :return:
        """
        with open(annotation_filename, 'r') as f:
            annotation_dict = json.loads(f.read())
        final_dict = {}
        for town_dict in annotation_dict['available_scenarios']:
            final_dict.update(town_dict)
        return final_dict

    @staticmethod
    def parse_routes_file(route_filename, scenario_file, single_route=None):
        """
        Returns a list of route elements.
        :param route_filename: the path to a set of routes.
        :param single_route: If set, only this route shall be returned
        :return: List of dicts containing the waypoints, id and town of the routes
        """
        list_route_descriptions = []
        tree = ET.parse(route_filename)
        for route in tree.iter('route'):
            route_id = route.attrib['id']
            if single_route and route_id != single_route:
                continue
            new_config = RouteScenarioConfiguration()
            new_config.town = route.attrib['town']
            new_config.name = 'RouteScenario_{}'.format(route_id)
            new_config.weather = RouteParser.parse_weather(route)
            new_config.scenario_file = scenario_file
            waypoint_list = []
            for waypoint in route.iter('waypoint'):
                waypoint_list.append(carla.Location(x=float(waypoint.attrib['x']), y=float(waypoint.attrib['y']), z=float(waypoint.attrib['z'])))
            new_config.trajectory = waypoint_list
            list_route_descriptions.append(new_config)
        return list_route_descriptions

    @staticmethod
    def parse_weather(route):
        """
        Returns a carla.WeatherParameters with the corresponding weather for that route. If the route
        has no weather attribute, the default one is triggered.
        """
        route_weather = route.find('weather')
        if route_weather is None:
            weather = carla.WeatherParameters(sun_altitude_angle=70)
        else:
            weather = carla.WeatherParameters()
            for weather_attrib in route.iter('weather'):
                if 'cloudiness' in weather_attrib.attrib:
                    weather.cloudiness = float(weather_attrib.attrib['cloudiness'])
                if 'precipitation' in weather_attrib.attrib:
                    weather.precipitation = float(weather_attrib.attrib['precipitation'])
                if 'precipitation_deposits' in weather_attrib.attrib:
                    weather.precipitation_deposits = float(weather_attrib.attrib['precipitation_deposits'])
                if 'wind_intensity' in weather_attrib.attrib:
                    weather.wind_intensity = float(weather_attrib.attrib['wind_intensity'])
                if 'sun_azimuth_angle' in weather_attrib.attrib:
                    weather.sun_azimuth_angle = float(weather_attrib.attrib['sun_azimuth_angle'])
                if 'sun_altitude_angle' in weather_attrib.attrib:
                    weather.sun_altitude_angle = float(weather_attrib.attrib['sun_altitude_angle'])
                if 'wetness' in weather_attrib.attrib:
                    weather.wetness = float(weather_attrib.attrib['wetness'])
                if 'fog_distance' in weather_attrib.attrib:
                    weather.fog_distance = float(weather_attrib.attrib['fog_distance'])
                if 'fog_density' in weather_attrib.attrib:
                    weather.fog_density = float(weather_attrib.attrib['fog_density'])
        return weather

    @staticmethod
    def check_trigger_position(new_trigger, existing_triggers):
        """
        Check if this trigger position already exists or if it is a new one.
        :param new_trigger:
        :param existing_triggers:
        :return:
        """
        for trigger_id in existing_triggers.keys():
            trigger = existing_triggers[trigger_id]
            dx = trigger['x'] - new_trigger['x']
            dy = trigger['y'] - new_trigger['y']
            distance = math.sqrt(dx * dx + dy * dy)
            dyaw = (trigger['yaw'] - new_trigger['yaw']) % 360
            if distance < TRIGGER_THRESHOLD and (dyaw < TRIGGER_ANGLE_THRESHOLD or dyaw > 360 - TRIGGER_ANGLE_THRESHOLD):
                return trigger_id
        return None

    @staticmethod
    def convert_waypoint_float(waypoint):
        """
        Convert waypoint values to float
        """
        waypoint['x'] = float(waypoint['x'])
        waypoint['y'] = float(waypoint['y'])
        waypoint['z'] = float(waypoint['z'])
        waypoint['yaw'] = float(waypoint['yaw'])

    @staticmethod
    def match_world_location_to_route(world_location, route_description):
        """
        We match this location to a given route.
            world_location:
            route_description:
        """

        def match_waypoints(waypoint1, wtransform):
            """
            Check if waypoint1 and wtransform are similar
            """
            dx = float(waypoint1['x']) - wtransform.location.x
            dy = float(waypoint1['y']) - wtransform.location.y
            dz = float(waypoint1['z']) - wtransform.location.z
            dpos = math.sqrt(dx * dx + dy * dy + dz * dz)
            dyaw = (float(waypoint1['yaw']) - wtransform.rotation.yaw) % 360
            return dpos < TRIGGER_THRESHOLD and (dyaw < TRIGGER_ANGLE_THRESHOLD or dyaw > 360 - TRIGGER_ANGLE_THRESHOLD)
        match_position = 0
        for route_waypoint in route_description:
            if match_waypoints(world_location, route_waypoint[0]):
                return match_position
            match_position += 1
        return None

    @staticmethod
    def get_scenario_type(scenario, match_position, trajectory):
        """
        Some scenarios have different types depending on the route.
        :param scenario: the scenario name
        :param match_position: the matching position for the scenarion
        :param trajectory: the route trajectory the ego is following
        :return: tag representing this subtype

        Also used to check which are not viable (Such as an scenario
        that triggers when turning but the route doesnt')
        WARNING: These tags are used at:
            - VehicleTurningRoute
            - SignalJunctionCrossingRoute
        and changes to these tags will affect them
        """

        def check_this_waypoint(tuple_wp_turn):
            """
            Decides whether or not the waypoint will define the scenario behavior
            """
            if RoadOption.LANEFOLLOW == tuple_wp_turn[1]:
                return False
            elif RoadOption.CHANGELANELEFT == tuple_wp_turn[1]:
                return False
            elif RoadOption.CHANGELANERIGHT == tuple_wp_turn[1]:
                return False
            return True
        subtype = 'valid'
        if scenario == 'Scenario4':
            for tuple_wp_turn in trajectory[match_position:]:
                if check_this_waypoint(tuple_wp_turn):
                    if RoadOption.LEFT == tuple_wp_turn[1]:
                        subtype = 'S4left'
                    elif RoadOption.RIGHT == tuple_wp_turn[1]:
                        subtype = 'S4right'
                    else:
                        subtype = None
                    break
                subtype = None
        if scenario == 'Scenario7':
            for tuple_wp_turn in trajectory[match_position:]:
                if check_this_waypoint(tuple_wp_turn):
                    if RoadOption.LEFT == tuple_wp_turn[1]:
                        subtype = 'S7left'
                    elif RoadOption.RIGHT == tuple_wp_turn[1]:
                        subtype = 'S7right'
                    elif RoadOption.STRAIGHT == tuple_wp_turn[1]:
                        subtype = 'S7opposite'
                    else:
                        subtype = None
                    break
                subtype = None
        if scenario == 'Scenario8':
            for tuple_wp_turn in trajectory[match_position:]:
                if check_this_waypoint(tuple_wp_turn):
                    if RoadOption.LEFT == tuple_wp_turn[1]:
                        subtype = 'S8left'
                    else:
                        subtype = None
                    break
                subtype = None
        if scenario == 'Scenario9':
            for tuple_wp_turn in trajectory[match_position:]:
                if check_this_waypoint(tuple_wp_turn):
                    if RoadOption.RIGHT == tuple_wp_turn[1]:
                        subtype = 'S9right'
                    else:
                        subtype = None
                    break
                subtype = None
        return subtype

    @staticmethod
    def scan_route_for_scenarios(route_name, trajectory, world_annotations):
        """
        Just returns a plain list of possible scenarios that can happen in this route by matching
        the locations from the scenario into the route description

        :return:  A list of scenario definitions with their correspondent parameters
        """
        existent_triggers = {}
        possible_scenarios = {}
        latest_trigger_id = 0
        for town_name in world_annotations.keys():
            if town_name != route_name:
                continue
            scenarios = world_annotations[town_name]
            for scenario in scenarios:
                if 'scenario_type' not in scenario:
                    break
                scenario_name = scenario['scenario_type']
                for event in scenario['available_event_configurations']:
                    waypoint = event['transform']
                    RouteParser.convert_waypoint_float(waypoint)
                    match_position = RouteParser.match_world_location_to_route(waypoint, trajectory)
                    if match_position is not None:
                        if 'other_actors' in event:
                            other_vehicles = event['other_actors']
                        else:
                            other_vehicles = None
                        scenario_subtype = RouteParser.get_scenario_type(scenario_name, match_position, trajectory)
                        if scenario_subtype is None:
                            continue
                        scenario_description = {'name': scenario_name, 'other_actors': other_vehicles, 'trigger_position': waypoint, 'scenario_type': scenario_subtype}
                        trigger_id = RouteParser.check_trigger_position(waypoint, existent_triggers)
                        if trigger_id is None:
                            existent_triggers.update({latest_trigger_id: waypoint})
                            possible_scenarios.update({latest_trigger_id: []})
                            trigger_id = latest_trigger_id
                            latest_trigger_id += 1
                        possible_scenarios[trigger_id].append(scenario_description)
        return (possible_scenarios, existent_triggers)

@staticmethod
def parse_weather(route):
    """
        Returns a carla.WeatherParameters with the corresponding weather for that route. If the route
        has no weather attribute, the default one is triggered.
        """
    route_weather = route.find('weather')
    if route_weather is None:
        weather = carla.WeatherParameters(sun_altitude_angle=70)
    else:
        weather = carla.WeatherParameters()
        for weather_attrib in route.iter('weather'):
            if 'cloudiness' in weather_attrib.attrib:
                weather.cloudiness = float(weather_attrib.attrib['cloudiness'])
            if 'precipitation' in weather_attrib.attrib:
                weather.precipitation = float(weather_attrib.attrib['precipitation'])
            if 'precipitation_deposits' in weather_attrib.attrib:
                weather.precipitation_deposits = float(weather_attrib.attrib['precipitation_deposits'])
            if 'wind_intensity' in weather_attrib.attrib:
                weather.wind_intensity = float(weather_attrib.attrib['wind_intensity'])
            if 'sun_azimuth_angle' in weather_attrib.attrib:
                weather.sun_azimuth_angle = float(weather_attrib.attrib['sun_azimuth_angle'])
            if 'sun_altitude_angle' in weather_attrib.attrib:
                weather.sun_altitude_angle = float(weather_attrib.attrib['sun_altitude_angle'])
            if 'wetness' in weather_attrib.attrib:
                weather.wetness = float(weather_attrib.attrib['wetness'])
            if 'fog_distance' in weather_attrib.attrib:
                weather.fog_distance = float(weather_attrib.attrib['fog_distance'])
            if 'fog_density' in weather_attrib.attrib:
                weather.fog_density = float(weather_attrib.attrib['fog_density'])
    return weather

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

def destroy(self):
    """
        Cleanup
        """
    self._hic.quit = True
    self._thread.join()

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

def set_global_plan(self, global_plan_gps, global_plan_world_coord):
    """
        Set the plan (route) for the agent
        """
    ds_ids = downsample_route(global_plan_world_coord, 1)
    self._global_plan_world_coord = [(global_plan_world_coord[x][0], global_plan_world_coord[x][1]) for x in ds_ids]
    self._global_plan = [global_plan_gps[x] for x in ds_ids]

class CriteriaFilter(BasicMetric):
    """
    Metric class CriteriaFilter
    """

    def _create_metric(self, town_map, log, criteria):
        """
        Implementation of the metric. This is an example to show how to use the criteria
        """
        results = {}
        for criterion_name in criteria:
            criterion = criteria[criterion_name]
            results.update({criterion_name: {'test_status': criterion['test_status'], 'actual_value': criterion['actual_value'], 'success_value': criterion['expected_value_success']}})
        with open('srunner/metrics/data/CriteriaFilter_results.json', 'w') as fw:
            json.dump(results, fw, sort_keys=False, indent=4)

def _create_metric(self, town_map, log, criteria):
    """
        Implementation of the metric. This is an example to show how to use the criteria
        """
    results = {}
    for criterion_name in criteria:
        criterion = criteria[criterion_name]
        results.update({criterion_name: {'test_status': criterion['test_status'], 'actual_value': criterion['actual_value'], 'success_value': criterion['expected_value_success']}})
    with open('srunner/metrics/data/CriteriaFilter_results.json', 'w') as fw:
        json.dump(results, fw, sort_keys=False, indent=4)

def create_legend():
    symbols = [lines.Line2D([], [], color=col, marker=mark, markersize=15) for _, (col, mark) in infraction_to_symbol.items()]
    names = [infraction for infraction, _ in infraction_to_symbol.items()]
    figlegend = plt.figure(figsize=(3, int(0.34 * len(names))))
    figlegend.legend(handles=symbols, labels=names)
    figlegend.savefig(os.path.join(args.save_dir, 'legend.png'))

def get_infraction_coords(infraction_description):
    combined = re.findall('\\(x=.*\\)', infraction_description)
    if len(combined) > 0:
        coords_str = combined[0][1:-1].split(', ')
        coords = [float(coord[2:]) for coord in coords_str]
    else:
        coords = ['-', '-', '-']
    return coords

def main():
    root = ET.parse(args.xml).getroot()
    route_matching = {}
    if 'weather' in [elem.tag for elem in root.iter()]:
        for route, weather_daytime in zip(root.iter('route'), root.iter('weather')):
            combined = re.findall('[A-Z][^A-Z]*', weather_daytime.attrib['id'])
            weather = ''.join(combined[:-1])
            daytime = combined[-1]
            route_matching[route.attrib['id']] = {'town': route.attrib['town'], 'weather': weather, 'daytime': daytime}
    else:
        for route in root.iter('route'):
            route_matching[route.attrib['id']] = {'town': route.attrib['town'], 'weather': 'Clear', 'daytime': 'Noon'}
    filenames = []
    for foldername, _, cur_filenames in walk(args.results):
        paths = []
        for filename in cur_filenames:
            if filename.endswith('.json'):
                paths.append(os.path.join(foldername, filename))
        filenames += paths
    route_evaluation = []
    total_score_labels = []
    total_score_values = []
    total_km_driven = 0.0
    total_infractions = {}
    total_infractions_per_km = {}
    abort = False
    for f in filenames:
        with open(f) as json_file:
            evaluation_data = json.load(json_file)
            if len(total_infractions) == 0:
                for infraction_name in evaluation_data['_checkpoint']['global_record']['infractions']:
                    total_infractions[infraction_name] = 0
            for record in evaluation_data['_checkpoint']['records']:
                if record['scores']['score_route'] <= 1e-11:
                    print('Warning: There is a route where the agent did not start to drive.' + ' Route ID: ' + record['route_id'], file=sys.stderr)
                if record['status'] == "Failed - Agent couldn't be set up":
                    print('Error: There is at least one route where the agent could not be set up. Aborting.' + ' Route ID: ' + record['route_id'], file=sys.stderr)
                    abort = True
                if record['status'] == 'Failed':
                    print('Error: There is at least one route that failed. Aborting.' + ' Route ID: ' + record['route_id'], file=sys.stderr)
                    abort = True
                if record['status'] == 'Failed - Simulation crashed':
                    print('Error: There is at least one route where the simulation crashed. Aborting.' + ' Route ID: ' + record['route_id'], file=sys.stderr)
                    abort = True
                percentage_of_route_completed = record['scores']['score_route'] / 100.0
                route_length_km = record['meta']['route_length'] / 1000.0
                driven_km = percentage_of_route_completed * route_length_km
                total_km_driven += driven_km
                for infraction_name in evaluation_data['_checkpoint']['global_record']['infractions']:
                    if infraction_name == 'outside_route_lanes':
                        if len(record['infractions'][infraction_name]) > 0:
                            meters_off_road = re.findall('\\d+\\.\\d+', record['infractions'][infraction_name][0])[0]
                            km_off_road = float(meters_off_road) / 1000.0
                            total_infractions[infraction_name] += km_off_road
                    else:
                        num_infraction = len(record['infractions'][infraction_name])
                        total_infractions[infraction_name] += num_infraction
            eval_data = evaluation_data['_checkpoint']['records']
            total_scores = evaluation_data['values']
            route_evaluation += eval_data
            total_score_labels = evaluation_data['labels']
            total_score_values += [[float(score) * len(eval_data) for score in total_scores]]
    for key in total_infractions:
        total_infractions_per_km[key] = total_infractions[key] / total_km_driven
        if key == 'outside_route_lanes':
            total_infractions_per_km[key] = total_infractions_per_km[key] * 100.0
    total_score_values = np.array(total_score_values)
    if len(route_evaluation) % len(route_matching) != 0:
        print('Error: The number of completed routes (' + str(len(route_evaluation)) + ') is not a multiple of the total routes (' + str(len(route_matching)) + '). Check if there are missing results. Aborting.', file=sys.stderr)
        abort = True
    if abort == True:
        exit()
    total_score_values = total_score_values.sum(axis=0) / len(route_evaluation)
    for idx, value in enumerate(total_score_labels):
        if value == 'Collisions with pedestrians':
            total_score_values[idx] = total_infractions_per_km['collisions_pedestrian']
        elif value == 'Collisions with vehicles':
            total_score_values[idx] = total_infractions_per_km['collisions_vehicle']
        elif value == 'Collisions with layout':
            total_score_values[idx] = total_infractions_per_km['collisions_layout']
        elif value == 'Red lights infractions':
            total_score_values[idx] = total_infractions_per_km['red_light']
        elif value == 'Stop sign infractions':
            total_score_values[idx] = total_infractions_per_km['stop_infraction']
        elif value == 'Off-road infractions':
            total_score_values[idx] = total_infractions_per_km['outside_route_lanes']
        elif value == 'Route deviations':
            total_score_values[idx] = total_infractions_per_km['route_dev']
        elif value == 'Route timeouts':
            total_score_values[idx] = total_infractions_per_km['route_timeout']
        elif value == 'Agent blocked':
            total_score_values[idx] = total_infractions_per_km['vehicle_blocked']
    route_to_id = {}
    for route in route_evaluation:
        route_to_id[route['route_id']] = ''.join((i for i in route['route_id'] if i.isdigit()))
    total_score_info = [{'label': label, 'value': value} for label, value in zip(total_score_labels, total_score_values)]
    route_scenarios = [{'route': route['route_id'], 'town': route_matching[route_to_id[route['route_id']]]['town'], 'weather': route_matching[route_to_id[route['route_id']]]['weather'], 'daytime': route_matching[route_to_id[route['route_id']]]['daytime'], 'duration': route['meta']['duration_game'], 'length': route['meta']['route_length'], 'score': route['scores']['score_composed'], 'completion': route['scores']['score_route'], 'status': route['status'], 'infractions': [(key, len(item), [get_infraction_coords(description) for description in item]) for key, item in route['infractions'].items()]} for route in route_evaluation]
    filters = ['route', 'town', 'weather', 'daytime', 'status']
    evaluation_filtered = {}
    for filter in filters:
        subcategories = np.unique(np.array([scenario[filter] for scenario in route_scenarios]))
        route_scenarios_per_subcategory = {}
        evaluation_per_subcategory = {}
        for subcategory in subcategories:
            route_scenarios_per_subcategory[subcategory] = []
            evaluation_per_subcategory[subcategory] = {}
        for scenario in route_scenarios:
            route_scenarios_per_subcategory[scenario[filter]].append(scenario)
        for subcategory in subcategories:
            scores = np.array([scenario['score'] for scenario in route_scenarios_per_subcategory[subcategory]])
            completions = np.array([scenario['completion'] for scenario in route_scenarios_per_subcategory[subcategory]])
            durations = np.array([scenario['duration'] for scenario in route_scenarios_per_subcategory[subcategory]])
            lengths = np.array([scenario['length'] for scenario in route_scenarios_per_subcategory[subcategory]])
            infractions = np.array([[infraction[1] for infraction in scenario['infractions']] for scenario in route_scenarios_per_subcategory[subcategory]])
            scores_combined = (scores.mean(), scores.std())
            completions_combined = (completions.mean(), completions.std())
            durations_combined = (durations.mean(), durations.std())
            lengths_combined = (lengths.mean(), lengths.std())
            infractions_combined = [(mean, std) for mean, std in zip(infractions.mean(axis=0), infractions.std(axis=0))]
            evaluation_per_subcategory[subcategory] = {'score': scores_combined, 'completion': completions_combined, 'duration': durations_combined, 'length': lengths_combined, 'infractions': infractions_combined}
        evaluation_filtered[filter] = evaluation_per_subcategory
    if not os.path.isdir(args.save_dir):
        os.mkdir(args.save_dir)
    f = open(os.path.join(args.save_dir, 'results.csv'), 'w')
    csv_writer_object = csv.writer(f)
    for info in total_score_info:
        csv_writer_object.writerow([item for _, item in info.items()])
    csv_writer_object.writerow([''])
    for filter in filters:
        infractions_types = []
        for infraction in route_scenarios[0]['infractions']:
            infractions_types.append(infraction[0] + ' mean')
            infractions_types.append(infraction[0] + ' std')
        if filter == 'route':
            csv_writer_object.writerow([filter, 'town', 'weather', 'daytime', 'score mean', 'score std', 'completion mean', 'completion std', 'duration mean', 'duration std', 'length mean', 'length std'] + infractions_types)
        else:
            csv_writer_object.writerow([filter, 'score mean', 'score std', 'completion mean', 'completion std', 'duration mean', 'duration std', 'length mean', 'length std'] + infractions_types)
        sorted_keys = sorted(evaluation_filtered[filter].keys(), key=lambda x: int(x.split('_')[-1]) if len(x.split('_')) >= 2 else -1)
        for key in sorted_keys:
            item = evaluation_filtered[filter][key]
            infractions_output = []
            for infraction in item['infractions']:
                infractions_output.append(infraction[0])
                infractions_output.append(infraction[1])
            if filter == 'route':
                csv_writer_object.writerow([key, route_matching[route_to_id[key]]['town'], route_matching[route_to_id[key]]['weather'], route_matching[route_to_id[key]]['daytime'], item['score'][0], item['score'][1], item['completion'][0], item['completion'][1], item['duration'][0], item['duration'][1], item['length'][0], item['length'][1]] + infractions_output)
            else:
                csv_writer_object.writerow([key, item['score'][0], item['score'][1], item['completion'][0], item['completion'][1], item['duration'][0], item['duration'][1], item['length'][0], item['length'][1]] + infractions_output)
        csv_writer_object.writerow([''])
    csv_writer_object.writerow(['town', 'weather', 'daylight', 'infraction type', 'x', 'y', 'z'])
    for scenario in route_scenarios:
        for infraction in scenario['infractions']:
            for coord in infraction[2]:
                if type(coord[0]) != str:
                    csv_writer_object.writerow([scenario['town'], scenario['weather'], scenario['daytime'], infraction[0]] + coord)
    csv_writer_object.writerow([''])
    f.close()
    town_maps = {}
    for town_name in towns:
        town_maps[town_name] = np.array(Image.open(os.path.join(args.town_maps, town_name + '.png')))[:, :, :3]
    create_legend()
    for scenario in route_scenarios:
        for infraction in scenario['infractions']:
            for coord in infraction[2]:
                if type(coord[0]) != str:
                    x = coord[0]
                    y = coord[1]
                    town_name = scenario['town']
                    hex_str, _ = infraction_to_symbol[infraction[0]]
                    color = hex_to_list(hex_str)
                    town_maps[town_name] = plotPixel((x, y), town_name, town_maps[town_name], color)
    for town_name in towns:
        tmap = Image.fromarray(town_maps[town_name])
        tmap.save(os.path.join(args.save_dir, town_name + '.png'))

def gen_scenarios(args, scenario_type_dict, town_scenario_tp_gen):
    if args.towns == 'all':
        towns = ALL_TOWNS
    else:
        towns = [args.towns]
    for town_ in towns:
        client = carla.Client('localhost', 2000)
        client.set_timeout(200.0)
        world = client.load_world(town_)
        carla_map = world.get_map()
        save_dir = args.save_dir
        for scen_type, _ in scenario_type_dict.items():
            town_scenario_tp_gen(town_, carla_map, scen_type, save_dir, world)

def sample_junctions(world_map, route, scenarios_list, town, start_dist=20, end_dist=20, min_len=50, max_len=MAX_LEN):
    """
    Sample individual junctions from the interpolated routes
    Args:
        world_map: town map
        route: interpolated route
    Return:
        custom_routes: list of (start wp, end wp) each representing an individual junction
    """
    custom_routes = []
    start_id = -1
    end_id = -1
    for index in range(start_dist, len(route) - end_dist):
        if route[index - 1][1] == RoadOption.LANEFOLLOW and route[index][1] != RoadOption.LANEFOLLOW:
            start_id = index - start_dist
        elif start_id != -1 and route[index][1] == RoadOption.LANEFOLLOW:
            end_id = index + end_dist
            if end_id > start_id + min_len:
                start_wp = carla.Location(x=route[start_id][0].location.x, y=route[start_id][0].location.y, z=route[start_id][0].location.z)
                end_wp = carla.Location(x=route[end_id][0].location.x, y=route[end_id][0].location.y, z=route[end_id][0].location.z)
                waypoint_list = [start_wp, end_wp]
                extended_route = interpolate_trajectory(world_map, waypoint_list)
                potential_scenarios_definitions, _ = scan_route_for_scenarios(town, extended_route, scenarios_list)
                if len(extended_route) > max_len or len(extended_route) == 1 or len(potential_scenarios_definitions) == 0:
                    start_id = -1
                    end_id = -1
                    continue
                downsampled_route = downsample_route(extended_route, 50)
                custom_route = []
                for element in downsampled_route:
                    custom_transform = (route[start_id + element][0].location.x, route[start_id + element][0].location.y, route[start_id + element][0].location.z, route[start_id + element][0].rotation.yaw)
                    custom_route.append(custom_transform)
                custom_routes.append(custom_route)
            start_id = -1
            end_id = -1
    return custom_routes

def process_route(world_map, route, scenarios_list, return_dict):
    interpolated_route = interpolate_trajectory(world_map, route['trajectory'])
    wp_list = sample_junctions(world_map, interpolated_route, scenarios_list, route['town_name'])
    print('got {} junctions in route {} (interpolated {} waypoints to {} waypoints)'.format(len(wp_list), route['id'], len(route['trajectory']), len(interpolated_route)))
    return_dict[route['id']] = {'wp_list': wp_list, 'town_name': route['town_name'], 'length': len(interpolated_route)}

def main(args):
    client = carla.Client('localhost', 2000)
    client.set_timeout(200.0)
    routes_list = parse_routes_file(args.routes_file)
    scenarios_list = parse_annotations_file(args.scenarios_file)
    manager = multiprocessing.Manager()
    return_dict = manager.dict()
    jobs = []
    st = time.time()
    for index, route in enumerate(routes_list):
        if index == 0 or routes_list[index]['town_name'] != routes_list[index - 1]['town_name']:
            world = client.load_world(route['town_name'])
            world_map = world.get_map()
        p = multiprocessing.Process(target=process_route, args=(world_map, route, scenarios_list, return_dict))
        jobs.append(p)
        p.start()
    for process in jobs:
        process.join()
    print('{} routes processed in {} seconds'.format(len(return_dict), time.time() - st))
    route_id = 0
    total_junctions = 0
    route_lengths = []
    root = ET.Element('routes')
    for curr_route in return_dict.keys():
        wp_list = return_dict[curr_route]['wp_list']
        town_name = return_dict[curr_route]['town_name']
        total_junctions += len(wp_list)
        route_lengths.append(return_dict[curr_route]['length'])
        for wps in wp_list:
            add_route = ET.SubElement(root, 'route', id='%d' % route_id, town=town_name)
            for node in wps:
                ET.SubElement(add_route, 'waypoint', x='%f' % node[0], y='%f' % node[1], z='%f' % node[2], pitch='0.0', roll='0.0', yaw='%f' % node[3])
            route_id += 1
    print('\nSource File:')
    print('mean distance: ', np.array(route_lengths).mean())
    print('median distance: ', np.median(np.array(route_lengths)))
    if args.save_file is not None:
        tree = ET.ElementTree(root)
        tree.write(args.save_file, xml_declaration=True, encoding='utf-8', pretty_print=True)
        new_index = 0
        outliers = 0
        route_lengths = []
        duplicate_list = []
        new_routes_list = parse_routes_file(args.save_file)
        if args.duplicate_file:
            duplicate_file_list = parse_routes_file(args.duplicate_file)
            for index, route in enumerate(duplicate_file_list):
                if index == 0 or duplicate_file_list[index]['town_name'] != duplicate_file_list[index - 1]['town_name']:
                    world = client.load_world(route['town_name'])
                    world_map = world.get_map()
                new_interpolated_route = interpolate_trajectory(world_map, route['trajectory'])
                locations = (new_interpolated_route[0][0].location.x, new_interpolated_route[0][0].location.y, new_interpolated_route[-1][0].location.x, new_interpolated_route[-1][0].location.y)
                duplicate_list.append(locations)
        for index, route in enumerate(new_routes_list):
            if index == 0 or new_routes_list[index]['town_name'] != new_routes_list[index - 1]['town_name']:
                world = client.load_world(route['town_name'])
                world_map = world.get_map()
            new_interpolated_route = interpolate_trajectory(world_map, route['trajectory'])
            current_node = root.getchildren()[index - outliers]
            locations = (new_interpolated_route[0][0].location.x, new_interpolated_route[0][0].location.y, new_interpolated_route[-1][0].location.x, new_interpolated_route[-1][0].location.y)
            if len(new_interpolated_route) > MAX_LEN or locations in duplicate_list:
                root.remove(current_node)
                outliers += 1
            else:
                duplicate_list.append(locations)
                route_lengths.append(len(new_interpolated_route))
                current_node.set('id', '%d' % (ID_START + new_index))
                new_index += 1
        tree = ET.ElementTree(root)
        tree.write(args.save_file, xml_declaration=True, encoding='utf-8', pretty_print=True)
        new_routes_list = parse_routes_file(args.save_file)
        print('\nTarget File:')
        print('saved junctions: ', len(route_lengths))
        print('outliers/duplicates: ', outliers)
        print('file num junctions: ', len(new_routes_list))
        print('mean distance: ', np.array(route_lengths).mean())
        print('median distance: ', np.median(np.array(route_lengths)))

def downsample_route(route, sample_factor):
    """
    Downsample the route by some factor.
    :param route: the trajectory , has to contain the waypoints and the road options
    :param sample_factor: Maximum distance between samples
    :return: returns the ids of the final route that can
    """
    ids_to_sample = []
    prev_option = None
    dist = 0
    for i, point in enumerate(route):
        curr_option = point[1]
        if curr_option in (RoadOption.CHANGELANELEFT, RoadOption.CHANGELANERIGHT):
            ids_to_sample.append(i)
            dist = 0
        elif prev_option != curr_option and prev_option not in (RoadOption.CHANGELANELEFT, RoadOption.CHANGELANERIGHT):
            ids_to_sample.append(i)
            dist = 0
        elif dist > sample_factor:
            ids_to_sample.append(i)
            dist = 0
        elif i == len(route) - 1:
            ids_to_sample.append(i)
            dist = 0
        else:
            curr_location = point[0].location
            prev_location = route[i - 1][0].location
            dist += curr_location.distance(prev_location)
        prev_option = curr_option
    return ids_to_sample

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

def create_semlabels_offline(self, surface, points_, paths, suffix, save_dir):
    for i, (point_original, path_) in enumerate(zip(points_, paths)):
        crp_dir = os.path.join(save_dir, os.path.dirname(path_), suffix)
        if not os.path.exists(crp_dir):
            os.makedirs(crp_dir)
        _, crop_name = os.path.split(path_)
        crop_pth = os.path.join(crp_dir, crop_name)
        self.create_crop(surface, point_original, path_=crop_pth)

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

def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--map_dir', default='../../leaderboard/data/maps', help='folder with created map images')
    argparser.add_argument('--ppm', default=8, help='pixels per meter, should match the created map')
    argparser.add_argument('--in_path', type=str, help='input xmls or json file')
    argparser.add_argument('--save_dir', type=str, help='output folder with visualizations')
    args = argparser.parse_args()
    if not os.path.exists(args.save_dir):
        os.makedirs(args.save_dir)
    filename = args.in_path.split('/')[-1].split('.')[0]
    extension = args.in_path.split('/')[-1].split('.')[1]
    print(f'Processing {filename}, extension: {extension}')
    if extension == 'xml':
        root = ET.parse(args.in_path).getroot()
        points_ = []
        for type_tag in root.findall('route'):
            tmp_pts_ego = []
            town_ = type_tag.get('town')
            for wp_ in type_tag.findall('waypoint'):
                sp_x = float(wp_.get('x'))
                sp_y = float(wp_.get('y'))
                tmp_pts_ego.append(Point((sp_x, sp_y, 0)))
            points_.append(tmp_pts_ego)
        args.points = points_
        map_image = MapImage(carla_map_name=town_, pixels_per_meter=args.ppm, map_dir=args.map_dir)
        map_image.plot_points_nocrop_xml(map_image.viz_surface, args.points, filename + '_' + extension, args.save_dir)
    else:
        with open(args.in_path) as json_file:
            data = json.load(json_file)
        scenario_list = data['available_scenarios'][0]
        for town_, scenarios_list in scenario_list.items():
            args.points = []
            map_image = MapImage(carla_map_name=town_, pixels_per_meter=args.ppm, map_dir=args.map_dir)
            for scenario_ in scenarios_list:
                scenario_all_triggers = scenario_['available_event_configurations']
                tmp_pts_ego = []
                tmp_pts = []
                for scenario_trigger in scenario_all_triggers:
                    scenario_points = {}
                    scenario_ego_spawn = scenario_trigger['transform']
                    sp_x, sp_y, sp_yaw = (float(scenario_ego_spawn['x']), float(scenario_ego_spawn['y']), float(scenario_ego_spawn['yaw']))
                    scenario_points['ego'] = Point((sp_x, sp_y, sp_yaw))
                    tmp_pts.append(scenario_points)
                args.points.append(tmp_pts)
            map_image.plot_points_nocrop_json(map_image.viz_surface, args.points, filename + '_' + extension, args.save_dir)

def generate_scenario_7_8_9(carla_map, world=None):
    carla_topology = carla_map.get_topology()
    topology = [x[0] for x in carla_topology]
    topology = sorted(topology, key=lambda w: w.transform.location.z)
    other_actors = []
    count_all_routes = 0
    trigger_points = {'Scenario7': [], 'Scenario8': [], 'Scenario9': []}
    actors = world.get_actors()
    traffic_lights_list = actors.filter('*traffic_light')
    print('Got %d traffic lights' % len(traffic_lights_list))
    junction_bbs_centers = []
    junctions_ = []
    duplicate_list = []
    count_all_routes = 0
    for wp_it, waypoint in enumerate(topology):
        if waypoint.is_junction:
            junc_ = waypoint.get_junction()
            jbb_ = junc_.bounding_box
            jbb_center = [round(jbb_.location.x, 2), round(jbb_.location.y, 2)]
            if jbb_center not in junction_bbs_centers:
                junction_bbs_centers.append(jbb_center)
                junctions_.append(junc_)
    pole_ind = []
    grps_ = []
    for tl_ in traffic_lights_list:
        grp_tl = tl_.get_group_traffic_lights()
        grp_tl_locs = [(round(gtl_.get_transform().location.x, 2), round(gtl_.get_transform().location.y, 2)) for gtl_ in grp_tl]
        pole_ind.append(tl_.get_pole_index())
        if grp_tl_locs not in grps_:
            grps_.append(grp_tl_locs)
    bb_flags = []
    for grp_ in grps_:
        midpt_grp = [sum(i) / len(grp_) for i in zip(*grp_)]
        grp_bb_dist = [np.sqrt((bb_c[0] - midpt_grp[0]) ** 2 + (bb_c[1] - midpt_grp[1]) ** 2) for bb_c in junction_bbs_centers]
        bb_dist, bb_idx = min(((val, idx) for idx, val in enumerate(grp_bb_dist)))
        bb_flags.append(bb_idx)
    signalized_junctions = [junc_ for i, junc_ in enumerate(junctions_) if i in bb_flags]
    signalized_junctions_bbs = [(junc_.bounding_box.location.x, junc_.bounding_box.location.y) for i, junc_ in enumerate(junctions_) if i in bb_flags]
    if len(signalized_junctions):
        for wp_it, waypoint in enumerate(topology):
            if waypoint.is_junction:
                junc_ = waypoint.get_junction()
                jbb_ = (junc_.bounding_box.location.x, junc_.bounding_box.location.y)
                if jbb_ in signalized_junctions_bbs:
                    j_wps = junc_.get_waypoints(carla.LaneType.Driving)
                    for it_, j_wp in enumerate(j_wps):
                        wp_p = j_wp[0]
                        dist_prev = 0
                        wp_list_prev = []
                        while True:
                            wp_list_prev.append(wp_p)
                            try:
                                wp_p = wp_p.previous(PRECISION)[0]
                            except:
                                break
                            dist_prev += PRECISION
                            if dist_prev > SAMPLING_DISTANCE:
                                break
                        dist_nxt = 0
                        wp_n = j_wp[1]
                        wp_list_nxt = []
                        while True:
                            wp_list_nxt.append(wp_n)
                            try:
                                wp_n = wp_n.next(PRECISION)[0]
                            except:
                                break
                            dist_nxt += PRECISION
                            if dist_nxt > SAMPLING_DISTANCE:
                                break
                        final_wps_list = list(reversed(wp_list_prev[1:])) + wp_list_nxt
                        cur_wp = final_wps_list[int(len(final_wps_list) / 2)]
                        prev_wp = final_wps_list[0]
                        nxt_wp = final_wps_list[-1]
                        vec_wp_nxt = cur_wp.transform.location - nxt_wp.transform.location
                        vec_wp_prev = cur_wp.transform.location - prev_wp.transform.location
                        dot_ = vec_wp_nxt.x * vec_wp_prev.x + vec_wp_prev.y * vec_wp_nxt.y
                        det_ = vec_wp_nxt.x * vec_wp_prev.y - vec_wp_prev.x * vec_wp_nxt.y
                        angle_bet = math.atan2(det_, dot_)
                        if angle_bet < 0:
                            angle_bet += 2 * math.pi
                        angle_deg = angle_bet * 180 / math.pi
                        if 160 < angle_deg < 195:
                            trig_key = 'Scenario7'
                        elif 10 < angle_deg < 160:
                            trig_key = 'Scenario9'
                        elif 195 < angle_deg < 350:
                            trig_key = 'Scenario8'
                        truncated_wp_lst = [final_wps_list]
                        locations = []
                        for wps_sub in truncated_wp_lst:
                            locations.append((wps_sub[0].transform.location.x, wps_sub[0].transform.location.y, wps_sub[-1].transform.location.x, wps_sub[-1].transform.location.y))
                        are_loc_dups = []
                        for location_ in locations:
                            flag_cum_ctr = []
                            for loc_dp in duplicate_list:
                                flag_ctrs = [True if prev_loc - PRECISION <= curr_loc <= prev_loc + PRECISION else False for curr_loc, prev_loc in zip(location_, loc_dp)]
                                flag_AND_ctr = all(flag_ctrs)
                                flag_cum_ctr.append(flag_AND_ctr)
                            is_loc_dup = any(flag_cum_ctr)
                            are_loc_dups.append(is_loc_dup)
                        for j_, wps_ in enumerate(truncated_wp_lst):
                            if not are_loc_dups[j_]:
                                count_all_routes += 1
                                duplicate_list.append(locations[j_])
                                wps_tmp = [wps_[0].transform.location, wps_[-1].transform.location]
                                extended_route = interpolate_trajectory(carla_map, wps_tmp)
                                if len(extended_route) < PRUNE_ROUTES_MIN_LEN:
                                    continue
                                else:
                                    trigger_point = extended_route[2][0]
                                    trigger_points[trig_key] += [trigger_point]
    other_actors = {'Scenario7': [None] * len(trigger_points['Scenario7']), 'Scenario8': [None] * len(trigger_points['Scenario8']), 'Scenario9': [None] * len(trigger_points['Scenario9'])}
    return (trigger_points, other_actors)

def town_scenario_tp_gen(town_, carla_map, scen_type, save_dir, world):
    ego_triggers_789, other_triggers_789 = FUNC_SCENARIO_TYPE[scen_type](carla_map, world=world)
    for key_ in ego_triggers_789.keys():
        ego_triggers = ego_triggers_789[key_]
        other_triggers = other_triggers_789[key_]
        scen_type = key_
        town_x_scen_y_dict = gen_skeleton_dict([town_], [key_])
        trigger_point_dict_lst = []
        for ego_trig, oa_trig in zip(ego_triggers, other_triggers):
            trigger_pts_dict = {}
            if ego_trig:
                ego_trig_dict = {'pitch': ego_trig.rotation.pitch, 'yaw': ego_trig.rotation.yaw, 'x': ego_trig.location.x, 'y': ego_trig.location.y, 'z': ego_trig.location.z}
                trigger_pts_dict['transform'] = ego_trig_dict
            trigger_pts_dict['other_actors'] = oa_trig
            if oa_trig:
                oa_trig_dict = {'pitch': ego_trig.rotation.pitch, 'yaw': ego_trig.rotation.yaw, 'x': ego_trig.location.x, 'y': ego_trig.location.y, 'z': ego_trig.location.z}
                trigger_pts_dict['other_actors'] = oa_trig_dict
            trigger_point_dict_lst.append(trigger_pts_dict)
        for i, town_dict_ in enumerate(town_x_scen_y_dict['available_scenarios']):
            if town_ in town_dict_.keys():
                for j, scens_dict in enumerate(town_dict_[town_]):
                    if scens_dict['scenario_type'] == scen_type:
                        scens_dict['available_event_configurations'] = trigger_point_dict_lst
        print(f'Num trigger points for {town_} {scen_type}: {len(trigger_point_dict_lst)}')
        with open(os.path.join(save_dir[key_], f'{town_}_{scen_type}.json'), 'w') as f:
            json.dump(town_x_scen_y_dict, f, indent=2, sort_keys=True)

def generate_scenario_4(carla_map):
    carla_topology = carla_map.get_topology()
    topology = [x[0] for x in carla_topology]
    topology = sorted(topology, key=lambda w: w.transform.location.z)
    other_actors = []
    count_all_routes = 0
    trigger_points = []
    duplicate_list = []
    for wp_it, waypoint in enumerate(topology):
        if waypoint.is_junction:
            junc_ = waypoint.get_junction()
            j_wps = junc_.get_waypoints(carla.LaneType.Driving)
            for it_, j_wp in enumerate(j_wps):
                count_all_routes += 1
                wp_p = j_wp[0]
                dist_prev = 0
                wp_list_prev = []
                while True:
                    wp_list_prev.append(wp_p)
                    try:
                        wp_p = wp_p.previous(PRECISION)[0]
                    except:
                        break
                    dist_prev += PRECISION
                    if dist_prev > SAMPLING_DISTANCE:
                        break
                dist_nxt = 0
                wp_n = j_wp[1]
                wp_list_nxt = []
                while True:
                    wp_list_nxt.append(wp_n)
                    try:
                        wp_n = wp_n.next(PRECISION)[0]
                    except:
                        break
                    dist_nxt += PRECISION
                    if dist_nxt > SAMPLING_DISTANCE:
                        break
                final_wps_list = list(reversed(wp_list_prev[1:])) + wp_list_nxt
                truncated_wp_lst = [final_wps_list]
                locations = []
                for wps_sub in truncated_wp_lst:
                    locations.append((wps_sub[0].transform.location.x, wps_sub[0].transform.location.y, wps_sub[-1].transform.location.x, wps_sub[-1].transform.location.y))
                are_loc_dups = []
                for location_ in locations:
                    flag_cum_ctr = []
                    for loc_dp in duplicate_list:
                        flag_ctrs = [True if prev_loc - PRECISION <= curr_loc <= prev_loc + PRECISION else False for curr_loc, prev_loc in zip(location_, loc_dp)]
                        flag_AND_ctr = all(flag_ctrs)
                        flag_cum_ctr.append(flag_AND_ctr)
                    is_loc_dup = any(flag_cum_ctr)
                    are_loc_dups.append(is_loc_dup)
                for j_, wps_ in enumerate(truncated_wp_lst):
                    if not are_loc_dups[j_]:
                        duplicate_list.append(locations[j_])
                        wps_tmp = [wps_[0].transform.location, wps_[-1].transform.location]
                        extended_route = interpolate_trajectory(carla_map, wps_tmp)
                        if len(extended_route) < PRUNE_ROUTES_MIN_LEN:
                            continue
                        else:
                            trigger_point = extended_route[5][0]
                            trigger_points += [trigger_point]
    other_actors = [{}] * len(trigger_points)
    return (trigger_points, other_actors)

def town_scenario_tp_gen(town_, carla_map, scen_type, save_dir, world):
    scen_save_dir = os.path.join(save_dir, scen_type)
    if not os.path.exists(scen_save_dir):
        os.makedirs(scen_save_dir)
    ego_triggers, other_triggers = FUNC_SCENARIO_TYPE[scen_type](carla_map)
    town_x_scen_y_dict = []
    town_x_scen_y_dict = gen_skeleton_dict([town_], [scen_type]).copy()
    trigger_point_dict_lst = []
    for ego_trig, oa_trig in zip(ego_triggers, other_triggers):
        trigger_pts_dict = {}
        if ego_trig:
            ego_trig_dict = {'pitch': ego_trig.rotation.pitch, 'yaw': ego_trig.rotation.yaw, 'x': ego_trig.location.x, 'y': ego_trig.location.y, 'z': ego_trig.location.z}
            trigger_pts_dict['transform'] = ego_trig_dict
        trigger_pts_dict['other_actors'] = oa_trig
        if oa_trig:
            oa_trig_dict = {'pitch': ego_trig.rotation.pitch, 'yaw': ego_trig.rotation.yaw, 'x': ego_trig.location.x, 'y': ego_trig.location.y, 'z': ego_trig.location.z}
            trigger_pts_dict['other_actors'] = oa_trig_dict
        trigger_point_dict_lst.append(trigger_pts_dict)
    for i, town_dict_ in enumerate(town_x_scen_y_dict['available_scenarios']):
        if town_ in town_dict_.keys():
            for j, scens_dict in enumerate(town_dict_[town_]):
                if scens_dict['scenario_type'] == scen_type:
                    scens_dict['available_event_configurations'] = trigger_point_dict_lst
    print(f'Num trigger points for {town_} {scen_type}: {len(trigger_point_dict_lst)}')
    with open(os.path.join(scen_save_dir, f'{town_}_{scen_type}.json'), 'w') as f:
        json.dump(town_x_scen_y_dict, f, indent=2, sort_keys=True)

def generate_scenario_3(carla_map):
    carla_topology = carla_map.get_topology()
    topology = [x[0] for x in carla_topology]
    topology = sorted(topology, key=lambda w: w.transform.location.z)
    other_actors = []
    count_all_routes = 0
    trigger_points = []
    duplicate_list = []
    for wp_it, waypoint in enumerate(topology):
        cur_wp = waypoint
        wp_list_nxt = [cur_wp]
        if not cur_wp.is_junction:
            while True:
                cur_wp_ = wp_list_nxt[-1]
                try:
                    nxt_wp = cur_wp_.next(PRECISION)[0]
                except:
                    break
                if not nxt_wp.is_junction:
                    wp_list_nxt.append(nxt_wp)
                else:
                    break
        wp_list_prev = [cur_wp]
        if not cur_wp.is_junction:
            while True:
                cur_wp_ = wp_list_prev[-1]
                try:
                    nxt_wp = cur_wp_.previous(PRECISION)[0]
                except:
                    break
                if not nxt_wp.is_junction:
                    wp_list_prev.append(nxt_wp)
                else:
                    break
        if len(wp_list_prev) + len(wp_list_nxt) > MIN_ROUTE_LENGTH:
            final_wps_list = list(reversed(wp_list_prev[1:])) + wp_list_nxt
            cur_wp = final_wps_list[int(len(final_wps_list) / 2)]
            prev_wp = final_wps_list[0]
            nxt_wp = final_wps_list[-1]
            vec_wp_nxt = cur_wp.transform.location - nxt_wp.transform.location
            vec_wp_prev = cur_wp.transform.location - prev_wp.transform.location
            norm_ = math.sqrt(vec_wp_nxt.x * vec_wp_nxt.x + vec_wp_nxt.y * vec_wp_nxt.y) * math.sqrt(vec_wp_prev.x * vec_wp_prev.x + vec_wp_prev.y * vec_wp_prev.y)
            try:
                dot_ = (vec_wp_nxt.x * vec_wp_prev.x + vec_wp_prev.y * vec_wp_nxt.y) / norm_
            except:
                dot_ = -1
            if dot_ > -1 - DOT_PROD_SLACK and dot_ < -1 + DOT_PROD_SLACK:
                continue
            else:
                truncated_wp_lst = []
                count_all_routes += 1
                for i_ in range(len(final_wps_list)):
                    tmp_wps = final_wps_list[i_ * NUM_WAYPOINTS_DISTANCE:i_ * NUM_WAYPOINTS_DISTANCE + NUM_WAYPOINTS_DISTANCE]
                    if len(tmp_wps) > 1:
                        cur_wp = tmp_wps[int(len(tmp_wps) / 2)]
                        prev_wp = tmp_wps[0]
                        nxt_wp = tmp_wps[-1]
                        vec_wp_nxt = cur_wp.transform.location - nxt_wp.transform.location
                        vec_wp_prev = cur_wp.transform.location - prev_wp.transform.location
                        norm_ = math.sqrt(vec_wp_nxt.x * vec_wp_nxt.x + vec_wp_nxt.y * vec_wp_nxt.y) * math.sqrt(vec_wp_prev.x * vec_wp_prev.x + vec_wp_prev.y * vec_wp_prev.y)
                        try:
                            dot_ = (vec_wp_nxt.x * vec_wp_prev.x + vec_wp_prev.y * vec_wp_nxt.y) / norm_
                        except:
                            dot_ = -1
                        if not dot_ < -1 + DOT_PROD_SLACK:
                            truncated_wp_lst.append(tmp_wps)
                    locations = []
                    for wps_sub in truncated_wp_lst:
                        locations.append((wps_sub[0].transform.location.x, wps_sub[0].transform.location.y, wps_sub[-1].transform.location.x, wps_sub[-1].transform.location.y))
                    are_loc_dups = []
                    for location_ in locations:
                        flag_cum_ctr = []
                        for loc_dp in duplicate_list:
                            flag_ctrs = [True if prev_loc - PRECISION <= curr_loc <= prev_loc + PRECISION else False for curr_loc, prev_loc in zip(location_, loc_dp)]
                            flag_AND_ctr = all(flag_ctrs)
                            flag_cum_ctr.append(flag_AND_ctr)
                        is_loc_dup = any(flag_cum_ctr)
                        are_loc_dups.append(is_loc_dup)
                    for j_, wps_ in enumerate(truncated_wp_lst):
                        if not are_loc_dups[j_]:
                            duplicate_list.append(locations[j_])
                            wps_tmp = [wps_[0].transform.location, wps_[-1].transform.location]
                            extended_route = interpolate_trajectory(carla_map, wps_tmp)
                            if len(extended_route) < PRUNE_ROUTES_MIN_LEN:
                                continue
                            else:
                                trigger_point = extended_route[int(len(extended_route) / 2)][0]
                                trigger_points += [trigger_point]
    other_actors = [None] * len(trigger_points)
    return (trigger_points, other_actors)

def generate_scenario_1(carla_map):
    carla_topology = carla_map.get_topology()
    topology = [x[0] for x in carla_topology]
    topology = sorted(topology, key=lambda w: w.transform.location.z)
    other_actors = []
    count_all_routes = 0
    trigger_points = []
    duplicate_list = []
    for wp_it, waypoint in enumerate(topology):
        cur_wp = waypoint
        wp_list_nxt = [cur_wp]
        if not cur_wp.is_junction:
            while True:
                cur_wp_ = wp_list_nxt[-1]
                try:
                    nxt_wp = cur_wp_.next(PRECISION)[0]
                except:
                    break
                if not nxt_wp.is_junction:
                    wp_list_nxt.append(nxt_wp)
                else:
                    break
        wp_list_prev = [cur_wp]
        if not cur_wp.is_junction:
            while True:
                cur_wp_ = wp_list_prev[-1]
                try:
                    nxt_wp = cur_wp_.previous(PRECISION)[0]
                except:
                    break
                if not nxt_wp.is_junction:
                    wp_list_prev.append(nxt_wp)
                else:
                    break
        if len(wp_list_prev) + len(wp_list_nxt) > MIN_ROUTE_LENGTH:
            final_wps_list = list(reversed(wp_list_prev[1:])) + wp_list_nxt
            cur_wp = final_wps_list[int(len(final_wps_list) / 2)]
            prev_wp = final_wps_list[0]
            nxt_wp = final_wps_list[-1]
            vec_wp_nxt = cur_wp.transform.location - nxt_wp.transform.location
            vec_wp_prev = cur_wp.transform.location - prev_wp.transform.location
            norm_ = math.sqrt(vec_wp_nxt.x * vec_wp_nxt.x + vec_wp_nxt.y * vec_wp_nxt.y) * math.sqrt(vec_wp_prev.x * vec_wp_prev.x + vec_wp_prev.y * vec_wp_prev.y)
            try:
                dot_ = (vec_wp_nxt.x * vec_wp_prev.x + vec_wp_prev.y * vec_wp_nxt.y) / norm_
            except:
                dot_ = -1
            if dot_ > -1 - DOT_PROD_SLACK and dot_ < -1 + DOT_PROD_SLACK:
                continue
            else:
                truncated_wp_lst = []
                count_all_routes += 1
                for i_ in range(len(final_wps_list)):
                    tmp_wps = final_wps_list[i_ * NUM_WAYPOINTS_DISTANCE:i_ * NUM_WAYPOINTS_DISTANCE + NUM_WAYPOINTS_DISTANCE]
                    if len(tmp_wps) > 1:
                        cur_wp = tmp_wps[int(len(tmp_wps) / 2)]
                        prev_wp = tmp_wps[0]
                        nxt_wp = tmp_wps[-1]
                        vec_wp_nxt = cur_wp.transform.location - nxt_wp.transform.location
                        vec_wp_prev = cur_wp.transform.location - prev_wp.transform.location
                        norm_ = math.sqrt(vec_wp_nxt.x * vec_wp_nxt.x + vec_wp_nxt.y * vec_wp_nxt.y) * math.sqrt(vec_wp_prev.x * vec_wp_prev.x + vec_wp_prev.y * vec_wp_prev.y)
                        try:
                            dot_ = (vec_wp_nxt.x * vec_wp_prev.x + vec_wp_prev.y * vec_wp_nxt.y) / norm_
                        except:
                            dot_ = -1
                        if not dot_ < -1 + DOT_PROD_SLACK:
                            truncated_wp_lst.append(tmp_wps)
                    locations = []
                    for wps_sub in truncated_wp_lst:
                        locations.append((wps_sub[0].transform.location.x, wps_sub[0].transform.location.y, wps_sub[-1].transform.location.x, wps_sub[-1].transform.location.y))
                    are_loc_dups = []
                    for location_ in locations:
                        flag_cum_ctr = []
                        for loc_dp in duplicate_list:
                            flag_ctrs = [True if prev_loc - PRECISION <= curr_loc <= prev_loc + PRECISION else False for curr_loc, prev_loc in zip(location_, loc_dp)]
                            flag_AND_ctr = all(flag_ctrs)
                            flag_cum_ctr.append(flag_AND_ctr)
                        is_loc_dup = any(flag_cum_ctr)
                        are_loc_dups.append(is_loc_dup)
                    for j_, wps_ in enumerate(truncated_wp_lst):
                        if not are_loc_dups[j_]:
                            duplicate_list.append(locations[j_])
                            wps_tmp = [wps_[0].transform.location, wps_[-1].transform.location]
                            extended_route = interpolate_trajectory(carla_map, wps_tmp)
                            if len(extended_route) < PRUNE_ROUTES_MIN_LEN:
                                continue
                            else:
                                trigger_point = extended_route[int(len(extended_route) / 2)][0]
                                trigger_points += [trigger_point]
    other_actors = [None] * len(trigger_points)
    return (trigger_points, other_actors)

def town_scenario_tp_gen(town_, carla_map, scen_type, save_dir, world):
    scen_save_dir = os.path.join(save_dir, scen_type)
    if not os.path.exists(scen_save_dir):
        os.makedirs(scen_save_dir)
    ego_triggers, other_triggers = FUNC_SCENARIO_TYPE[scen_type](carla_map)
    town_x_scen_y_dict = gen_skeleton_dict([town_], [scen_type])
    trigger_point_dict_lst = []
    for ego_trig, oa_trig in zip(ego_triggers, other_triggers):
        trigger_pts_dict = {}
        if ego_trig:
            ego_trig_dict = {'pitch': ego_trig.rotation.pitch, 'yaw': ego_trig.rotation.yaw, 'x': ego_trig.location.x, 'y': ego_trig.location.y, 'z': ego_trig.location.z}
            trigger_pts_dict['transform'] = ego_trig_dict
        if oa_trig:
            oa_trig_dict = {'pitch': ego_trig.rotation.pitch, 'yaw': ego_trig.rotation.yaw, 'x': ego_trig.location.x, 'y': ego_trig.location.y, 'z': ego_trig.location.z}
            trigger_pts_dict['other_actors'] = oa_trig_dict
        trigger_point_dict_lst.append(trigger_pts_dict)
    for i, town_dict_ in enumerate(town_x_scen_y_dict['available_scenarios']):
        if town_ in town_dict_.keys():
            for j, scens_dict in enumerate(town_dict_[town_]):
                if scens_dict['scenario_type'] == scen_type:
                    scens_dict['available_event_configurations'] = trigger_point_dict_lst
    print(f'Num trigger points for {town_} {scen_type}: {len(trigger_point_dict_lst)}')
    with open(os.path.join(scen_save_dir, f'{town_}_{scen_type}.json'), 'w') as f:
        json.dump(town_x_scen_y_dict, f, indent=2, sort_keys=True)

def generate_scenario_10(carla_map, world=None):
    carla_topology = carla_map.get_topology()
    topology = [x[0] for x in carla_topology]
    topology = sorted(topology, key=lambda w: w.transform.location.z)
    other_actors = []
    count_all_routes = 0
    duplicates = 0
    trigger_points = []
    actors = world.get_actors()
    traffic_lights_list = actors.filter('*traffic_light')
    print('got %d traffic lights' % len(traffic_lights_list))
    junction_bbs_centers = []
    junctions_ = []
    duplicate_list = []
    for wp_it, waypoint in enumerate(topology):
        if waypoint.is_junction:
            junc_ = waypoint.get_junction()
            jbb_ = junc_.bounding_box
            jbb_center = [round(jbb_.location.x, 2), round(jbb_.location.y, 2)]
            if jbb_center not in junction_bbs_centers:
                junction_bbs_centers.append(jbb_center)
                junctions_.append(junc_)
    pole_ind = []
    grps_ = []
    for tl_ in traffic_lights_list:
        grp_tl = tl_.get_group_traffic_lights()
        grp_tl_locs = [(round(gtl_.get_transform().location.x, 2), round(gtl_.get_transform().location.y, 2)) for gtl_ in grp_tl]
        pole_ind.append(tl_.get_pole_index())
        if grp_tl_locs not in grps_:
            grps_.append(grp_tl_locs)
    bb_flags = []
    for grp_ in grps_:
        midpt_grp = [sum(i) / len(grp_) for i in zip(*grp_)]
        grp_bb_dist = [np.sqrt((bb_c[0] - midpt_grp[0]) ** 2 + (bb_c[1] - midpt_grp[1]) ** 2) for bb_c in junction_bbs_centers]
        bb_dist, bb_idx = min(((val, idx) for idx, val in enumerate(grp_bb_dist)))
        bb_flags.append(bb_idx)
    unsignalized_junctions = [junc_ for i, junc_ in enumerate(junctions_) if i not in bb_flags]
    unsignalized_junctions_bbs = [(junc_.bounding_box.location.x, junc_.bounding_box.location.y) for i, junc_ in enumerate(junctions_) if i not in bb_flags]
    if len(unsignalized_junctions):
        count_all_routes = 0
        duplicates = 0
        PRECISION = 2
        SAMPLING_DISTANCE = 30
        duplicate_list = []
        for wp_it, waypoint in enumerate(topology):
            if waypoint.is_junction:
                junc_ = waypoint.get_junction()
                jbb_ = (junc_.bounding_box.location.x, junc_.bounding_box.location.y)
                if jbb_ in unsignalized_junctions_bbs:
                    j_wps = junc_.get_waypoints(carla.LaneType.Driving)
                    for it_, j_wp in enumerate(j_wps):
                        wp_p = j_wp[0]
                        dist_prev = 0
                        wp_list_prev = []
                        while True:
                            wp_list_prev.append(wp_p)
                            try:
                                wp_p = wp_p.previous(PRECISION)[0]
                            except:
                                break
                            dist_prev += PRECISION
                            if dist_prev > SAMPLING_DISTANCE:
                                break
                        dist_nxt = 0
                        wp_n = j_wp[1]
                        wp_list_nxt = []
                        while True:
                            wp_list_nxt.append(wp_n)
                            try:
                                wp_n = wp_n.next(PRECISION)[0]
                            except:
                                break
                            dist_nxt += PRECISION
                            if dist_nxt > SAMPLING_DISTANCE:
                                break
                        final_wps_list = list(reversed(wp_list_prev[1:])) + wp_list_nxt
                        truncated_wp_lst = [final_wps_list]
                        locations = []
                        for wps_sub in truncated_wp_lst:
                            locations.append((wps_sub[0].transform.location.x, wps_sub[0].transform.location.y, wps_sub[-1].transform.location.x, wps_sub[-1].transform.location.y))
                        are_loc_dups = []
                        for location_ in locations:
                            flag_cum_ctr = []
                            for loc_dp in duplicate_list:
                                flag_ctrs = [True if prev_loc - PRECISION <= curr_loc <= prev_loc + PRECISION else False for curr_loc, prev_loc in zip(location_, loc_dp)]
                                flag_AND_ctr = all(flag_ctrs)
                                flag_cum_ctr.append(flag_AND_ctr)
                            is_loc_dup = any(flag_cum_ctr)
                            are_loc_dups.append(is_loc_dup)
                        for j_, wps_ in enumerate(truncated_wp_lst):
                            if not are_loc_dups[j_]:
                                count_all_routes += 1
                                duplicate_list.append(locations[j_])
                                wps_tmp = [wps_[0].transform.location, wps_[-1].transform.location]
                                extended_route = interpolate_trajectory(carla_map, wps_tmp)
                                trigger_points += [extended_route[0][0]]
                            else:
                                duplicates += 1
            other_actors = [None] * len(trigger_points)
    return (trigger_points, other_actors)

def town_scenario_tp_gen(town_, carla_map, scen_type, save_dir, world):
    scen_save_dir = os.path.join(save_dir, scen_type)
    if not os.path.exists(scen_save_dir):
        os.makedirs(scen_save_dir)
    ego_triggers, other_triggers = FUNC_SCENARIO_TYPE[scen_type](carla_map, world)
    town_x_scen_y_dict = gen_skeleton_dict([town_], [scen_type])
    trigger_point_dict_lst = []
    for ego_trig, oa_trig in zip(ego_triggers, other_triggers):
        trigger_pts_dict = {}
        if ego_trig:
            ego_trig_dict = {'pitch': ego_trig.rotation.pitch, 'yaw': ego_trig.rotation.yaw, 'x': ego_trig.location.x, 'y': ego_trig.location.y, 'z': ego_trig.location.z}
            trigger_pts_dict['transform'] = ego_trig_dict
        trigger_pts_dict['other_actors'] = oa_trig
        if oa_trig:
            oa_trig_dict = {'pitch': ego_trig.rotation.pitch, 'yaw': ego_trig.rotation.yaw, 'x': ego_trig.location.x, 'y': ego_trig.location.y, 'z': ego_trig.location.z}
            trigger_pts_dict['other_actors'] = oa_trig_dict
        trigger_point_dict_lst.append(trigger_pts_dict)
    for i, town_dict_ in enumerate(town_x_scen_y_dict['available_scenarios']):
        if town_ in town_dict_.keys():
            for j, scens_dict in enumerate(town_dict_[town_]):
                if scens_dict['scenario_type'] == scen_type:
                    scens_dict['available_event_configurations'] = trigger_point_dict_lst
    print(f'Num trigger points for {town_} {scen_type}: {len(trigger_point_dict_lst)}')
    with open(os.path.join(scen_save_dir, f'{town_}_{scen_type}.json'), 'w') as f:
        json.dump(town_x_scen_y_dict, f, indent=2, sort_keys=True)

def main(args):
    scenarios_list = parse_annotations_file(args.scenarios_file)
    route_id = ID_START
    root = ET.Element('routes')
    client = carla.Client('localhost', 2000)
    client.set_timeout(200.0)
    world = client.load_world(args.town)
    carla_map = world.get_map()
    carla_topology = carla_map.get_topology()
    topology = [x[0] for x in carla_topology]
    topology = sorted(topology, key=lambda w: w.transform.location.z)
    count_all_routes = 0
    duplicates = 0
    actors = world.get_actors()
    traffic_lights_list = actors.filter('*traffic_light')
    print('got %d traffic lights' % len(traffic_lights_list))
    junction_bbs_centers = []
    junctions_ = []
    duplicate_list = []
    for wp_it, waypoint in enumerate(topology):
        if waypoint.is_junction:
            junc_ = waypoint.get_junction()
            jbb_ = junc_.bounding_box
            jbb_center = [round(jbb_.location.x, 2), round(jbb_.location.y, 2)]
            if jbb_center not in junction_bbs_centers:
                junction_bbs_centers.append(jbb_center)
                junctions_.append(junc_)
    pole_ind = []
    grps_ = []
    for tl_ in traffic_lights_list:
        grp_tl = tl_.get_group_traffic_lights()
        grp_tl_locs = [(round(gtl_.get_transform().location.x, 2), round(gtl_.get_transform().location.y, 2)) for gtl_ in grp_tl]
        pole_ind.append(tl_.get_pole_index())
        if grp_tl_locs not in grps_:
            grps_.append(grp_tl_locs)
    bb_flags = []
    for grp_ in grps_:
        midpt_grp = [sum(i) / len(grp_) for i in zip(*grp_)]
        grp_bb_dist = [np.sqrt((bb_c[0] - midpt_grp[0]) ** 2 + (bb_c[1] - midpt_grp[1]) ** 2) for bb_c in junction_bbs_centers]
        bb_dist, bb_idx = min(((val, idx) for idx, val in enumerate(grp_bb_dist)))
        bb_flags.append(bb_idx)
    unsignalized_junctions = [junc_ for i, junc_ in enumerate(junctions_) if i not in bb_flags]
    unsignalized_junctions_bbs = [(junc_.bounding_box.location.x, junc_.bounding_box.location.y) for i, junc_ in enumerate(junctions_) if i not in bb_flags]
    if len(unsignalized_junctions):
        count_all_routes = 0
        duplicates = 0
        PRECISION = 2
        SAMPLING_DISTANCE = 30
        duplicate_list = []
        for wp_it, waypoint in enumerate(topology):
            if waypoint.is_junction:
                junc_ = waypoint.get_junction()
                jbb_ = (junc_.bounding_box.location.x, junc_.bounding_box.location.y)
                if jbb_ in unsignalized_junctions_bbs:
                    j_wps = junc_.get_waypoints(carla.LaneType.Driving)
                    for it_, j_wp in enumerate(j_wps):
                        wp_p = j_wp[0]
                        dist_prev = 0
                        wp_list_prev = []
                        while True:
                            wp_list_prev.append(wp_p)
                            try:
                                wp_p = wp_p.previous(PRECISION)[0]
                            except:
                                break
                            dist_prev += PRECISION
                            if dist_prev > SAMPLING_DISTANCE:
                                break
                        dist_nxt = 0
                        wp_n = j_wp[1]
                        wp_list_nxt = []
                        while True:
                            wp_list_nxt.append(wp_n)
                            try:
                                wp_n = wp_n.next(PRECISION)[0]
                            except:
                                break
                            dist_nxt += PRECISION
                            if dist_nxt > SAMPLING_DISTANCE:
                                break
                        final_wps_list = list(reversed(wp_list_prev[1:])) + wp_list_nxt
                        truncated_wp_lst = [final_wps_list]
                        locations = []
                        for wps_sub in truncated_wp_lst:
                            locations.append((wps_sub[0].transform.location.x, wps_sub[0].transform.location.y, wps_sub[-1].transform.location.x, wps_sub[-1].transform.location.y))
                        are_loc_dups = []
                        for location_ in locations:
                            flag_cum_ctr = []
                            for loc_dp in duplicate_list:
                                flag_ctrs = [True if prev_loc - PRECISION <= curr_loc <= prev_loc + PRECISION else False for curr_loc, prev_loc in zip(location_, loc_dp)]
                                flag_AND_ctr = all(flag_ctrs)
                                flag_cum_ctr.append(flag_AND_ctr)
                            is_loc_dup = any(flag_cum_ctr)
                            are_loc_dups.append(is_loc_dup)
                        for j_, wps_ in enumerate(truncated_wp_lst):
                            if not are_loc_dups[j_]:
                                count_all_routes += 1
                                duplicate_list.append(locations[j_])
                                wps_tmp = [wps_[0].transform.location, wps_[-1].transform.location]
                                extended_route = interpolate_trajectory(carla_map, wps_tmp)
                                potential_scenarios_definitions, _ = scan_route_for_scenarios(carla_map.name, extended_route, scenarios_list)
                                wps_ = [wps_[0], wps_[-1]]
                                if len(potential_scenarios_definitions) > 0:
                                    route = ET.SubElement(root, 'route', id='%d' % route_id, town=args.town)
                                    for k_, wp_sub in enumerate(wps_):
                                        ET.SubElement(route, 'waypoint', x='%f' % wp_sub.transform.location.x, y='%f' % wp_sub.transform.location.y, z='0.0', pitch='0.0', roll='0.0', yaw='%f' % wp_sub.transform.rotation.yaw)
                                    route_id += 1
                            else:
                                duplicates += 1
        tree = ET.ElementTree(root)
        len_tree = 0
        for _ in tree.iter('route'):
            len_tree += 1
        print(f'Num routes for {args.town}: {len_tree}')
        if args.save_dir is not None and len_tree > 0:
            tree.write(args.save_file, xml_declaration=True, encoding='utf-8', pretty_print=True)

def main(args):
    route_id = 0
    duplicate_list = []
    count_all_routes = 0
    duplicates = 0
    distance_ = 100
    wp_length = 9
    PRECISION_small = 1
    WP_extended = 150
    root = {}
    root['lr'] = ET.Element('routes')
    root['ll'] = ET.Element('routes')
    root['rr'] = ET.Element('routes')
    root['rl'] = ET.Element('routes')
    final_save_dirs = {}
    for key_, _ in root.items():
        sub_path = os.path.join(args.save_dir, key_)
        if not os.path.exists(sub_path):
            os.makedirs(sub_path)
        final_save_dirs[key_] = sub_path
    client = carla.Client('localhost', 2000)
    client.set_timeout(200.0)
    world = client.load_world(args.town)
    carla_map = world.get_map()
    carla_topology = carla_map.get_topology()
    topology = [x[0] for x in carla_topology]
    topology = sorted(topology, key=lambda w: w.transform.location.z)
    print(f'Num waypoints for {args.town}: {len(topology)}')
    for wp_it, cur_wp in enumerate(topology):
        wp_list_nxt = [cur_wp]
        if not cur_wp.is_junction:
            tmp_distance_ = 0
            while True:
                cur_wp_ = wp_list_nxt[-1]
                try:
                    nxt_wp = cur_wp_.next(PRECISION)[0]
                except:
                    break
                if not nxt_wp.is_junction and tmp_distance_ < distance_:
                    wp_list_nxt.append(nxt_wp)
                    tmp_distance_ += PRECISION
                else:
                    break
        if len(wp_list_nxt) > wp_length:
            final_wps_list = wp_list_nxt
            end_point = final_wps_list[-1]
            mid_point = final_wps_list[int(len(final_wps_list) / 2)]
            try:
                all_choices_ep = get_possible_lane_changes(end_point)
                all_choices_mp = get_possible_lane_changes(mid_point)
                if not len(all_choices_ep) > 1 and (not len(all_choices_mp) > 1):
                    continue
            except:
                continue
            all_combs_split = {'lr': [], 'll': [], 'rr': [], 'rl': []}
            all_combs = []
            for key_ep, ep_ in all_choices_ep.items():
                for key_mp, mp_ in all_choices_mp.items():
                    if key_ep != key_mp:
                        if key_mp != 'n':
                            mp_direction_ = set(key_mp)
                            mp_cnt_ = len(key_mp)
                            ep_direction_ = set(key_ep)
                            ep_cnt_ = len(key_ep)
                            if mp_direction_ == {'l'}:
                                if ep_direction_ == {'r'} or ep_direction_ == {'n'}:
                                    lane_change_key = 'lr'
                                elif ep_direction_ == {'l'}:
                                    if mp_cnt_ > ep_cnt_:
                                        lane_change_key = 'lr'
                                    else:
                                        lane_change_key = 'll'
                            elif mp_direction_ == {'r'}:
                                if ep_direction_ == {'l'} or ep_direction_ == {'n'}:
                                    lane_change_key = 'rl'
                                elif ep_direction_ == {'r'}:
                                    if mp_cnt_ > ep_cnt_:
                                        lane_change_key = 'rl'
                                    else:
                                        lane_change_key = 'rr'
                            final_wps = [final_wps_list[0], mp_, ep_]
                            all_combs_split[lane_change_key].append(final_wps)
            truncated_wp_lst = [final_wps_list]
            locations = []
            for wps_sub in truncated_wp_lst:
                locations.append((wps_sub[0].transform.location.x, wps_sub[0].transform.location.y, wps_sub[-1].transform.location.x, wps_sub[-1].transform.location.y, wps_sub[0].transform.rotation.yaw))
            for location_ in locations:
                flag_cum_ctr = []
                for loc_dp in duplicate_list:
                    flag_ctrs = [True if prev_loc - PRECISION_small <= curr_loc <= prev_loc + PRECISION_small else False for curr_loc, prev_loc in zip(location_, loc_dp)]
                    flag_AND_ctr = all(flag_ctrs)
                    flag_cum_ctr.append(flag_AND_ctr)
                is_loc_dup = any(flag_cum_ctr)
                if not is_loc_dup:
                    duplicate_list.append(locations[0])
                    for all_combs_key, all_combs in all_combs_split.items():
                        for j_, wps_ in enumerate(all_combs):
                            count_all_routes += 1
                            wps_tmp = [wps_[0].transform.location, wps_[1].transform.location, wps_[-1].transform.location]
                            try:
                                extended_route = interpolate_trajectory(carla_map, wps_tmp)
                                if len(extended_route) > WP_extended or len(extended_route) < PRUNE_ROUTES_MIN_LEN:
                                    continue
                            except:
                                continue
                            wps_tmp2 = wps_
                            route = ET.SubElement(root[all_combs_key], 'route', id='%d' % route_id, town=args.town)
                            for k_, wp_sub in enumerate(wps_tmp2):
                                ET.SubElement(route, 'waypoint', x='%f' % wp_sub.transform.location.x, y='%f' % wp_sub.transform.location.y, z='%f' % wp_sub.transform.location.z, pitch='0.0', roll='0.0', yaw='%f' % wp_sub.transform.rotation.yaw)
                                route_id += 1
                else:
                    duplicates += 1
    tree = {}
    root_pruned = {}
    for key_ in ['rr', 'lr', 'll', 'rl']:
        root_pruned[key_] = ET.Element('routes')
        index_list = list(range(len(root[key_])))
        random.shuffle(index_list)
        index_list_pruned = index_list[:LIMIT_FINAL_ROUTES]
        route_id_pruned = 0
        for ind_, child_ in enumerate(root[key_]):
            if ind_ in index_list_pruned:
                route_new = ET.SubElement(root_pruned[key_], 'route', id='%d' % route_id_pruned, town=args.town)
                for subelement_ in child_.findall('waypoint'):
                    ET.SubElement(route_new, subelement_.tag, subelement_.attrib)
                route_id_pruned += 1
        tree = ET.ElementTree(root_pruned[key_])
        len_tree = 0
        for _ in tree.iter('route'):
            len_tree += 1
        print(f'Num routes for {args.town}: {len_tree}')
        if args.save_dir is not None and len_tree > 0:
            filename_ = os.path.join(final_save_dirs[key_], town_ + '_' + key_ + '.xml')
            tree.write(filename_, xml_declaration=True, encoding='utf-8', pretty_print=True)

def main(args):
    route_id = ID_START
    road_type = args.road_type
    root = ET.Element('routes')
    client = carla.Client('localhost', 2000)
    client.set_timeout(200.0)
    world = client.load_world(args.town)
    carla_map = world.get_map()
    carla_topology = carla_map.get_topology()
    topology = [x[0] for x in carla_topology]
    topology = sorted(topology, key=lambda w: w.transform.location.z)
    scenarios_list = parse_annotations_file(args.scenarios_file)
    count_all_routes = 0
    duplicates = 0
    if road_type == 'curved':
        DOT_PROD_SLACK = 0.02
        PRECISION = 2
        DISTANCE = 380
        PRUNE_ROUTES_MIN_LEN = 20
        NUM_WAYPOINTS_DISTANCE = int(DISTANCE / PRECISION)
        MIN_ROUTE_LENGTH = 4
        duplicate_list = []
        for wp_it, waypoint in enumerate(topology):
            cur_wp = waypoint
            wp_list_nxt = [cur_wp]
            if not cur_wp.is_junction:
                while True:
                    cur_wp_ = wp_list_nxt[-1]
                    try:
                        nxt_wp = cur_wp_.next(PRECISION)[0]
                    except:
                        break
                    if not nxt_wp.is_junction:
                        wp_list_nxt.append(nxt_wp)
                    else:
                        break
            wp_list_prev = [cur_wp]
            if not cur_wp.is_junction:
                while True:
                    cur_wp_ = wp_list_prev[-1]
                    try:
                        nxt_wp = cur_wp_.previous(PRECISION)[0]
                    except:
                        break
                    if not nxt_wp.is_junction:
                        wp_list_prev.append(nxt_wp)
                    else:
                        break
            if len(wp_list_prev) + len(wp_list_nxt) > MIN_ROUTE_LENGTH:
                final_wps_list = list(reversed(wp_list_prev[1:])) + wp_list_nxt
                cur_wp = final_wps_list[int(len(final_wps_list) / 2)]
                prev_wp = final_wps_list[0]
                nxt_wp = final_wps_list[-1]
                vec_wp_nxt = cur_wp.transform.location - nxt_wp.transform.location
                vec_wp_prev = cur_wp.transform.location - prev_wp.transform.location
                norm_ = math.sqrt(vec_wp_nxt.x * vec_wp_nxt.x + vec_wp_nxt.y * vec_wp_nxt.y) * math.sqrt(vec_wp_prev.x * vec_wp_prev.x + vec_wp_prev.y * vec_wp_prev.y)
                try:
                    dot_ = (vec_wp_nxt.x * vec_wp_prev.x + vec_wp_prev.y * vec_wp_nxt.y) / norm_
                except:
                    dot_ = -1
                if dot_ > -1 - DOT_PROD_SLACK and dot_ < -1 + DOT_PROD_SLACK:
                    continue
                else:
                    truncated_wp_lst = []
                    for i_ in range(len(final_wps_list)):
                        tmp_wps = final_wps_list[i_ * NUM_WAYPOINTS_DISTANCE:i_ * NUM_WAYPOINTS_DISTANCE + NUM_WAYPOINTS_DISTANCE]
                        if len(tmp_wps) > 1:
                            cur_wp = tmp_wps[int(len(tmp_wps) / 2)]
                            prev_wp = tmp_wps[0]
                            nxt_wp = tmp_wps[-1]
                            vec_wp_nxt = cur_wp.transform.location - nxt_wp.transform.location
                            vec_wp_prev = cur_wp.transform.location - prev_wp.transform.location
                            norm_ = math.sqrt(vec_wp_nxt.x * vec_wp_nxt.x + vec_wp_nxt.y * vec_wp_nxt.y) * math.sqrt(vec_wp_prev.x * vec_wp_prev.x + vec_wp_prev.y * vec_wp_prev.y)
                            try:
                                dot_ = (vec_wp_nxt.x * vec_wp_prev.x + vec_wp_prev.y * vec_wp_nxt.y) / norm_
                            except:
                                dot_ = -1
                            if not dot_ < -1 + DOT_PROD_SLACK:
                                truncated_wp_lst.append(tmp_wps)
                        locations = []
                        for wps_sub in truncated_wp_lst:
                            locations.append((wps_sub[0].transform.location.x, wps_sub[0].transform.location.y, wps_sub[-1].transform.location.x, wps_sub[-1].transform.location.y))
                        are_loc_dups = []
                        for location_ in locations:
                            flag_cum_ctr = []
                            for loc_dp in duplicate_list:
                                flag_ctrs = [True if prev_loc - PRECISION <= curr_loc <= prev_loc + PRECISION else False for curr_loc, prev_loc in zip(location_, loc_dp)]
                                flag_AND_ctr = all(flag_ctrs)
                                flag_cum_ctr.append(flag_AND_ctr)
                            is_loc_dup = any(flag_cum_ctr)
                            are_loc_dups.append(is_loc_dup)
                        for j_, wps_ in enumerate(truncated_wp_lst):
                            if not are_loc_dups[j_]:
                                count_all_routes += 1
                                duplicate_list.append(locations[j_])
                                wps_tmp = [wps_[0].transform.location, wps_[-1].transform.location]
                                extended_route = interpolate_trajectory(carla_map, wps_tmp)
                                potential_scenarios_definitions, _ = scan_route_for_scenarios(args.town, extended_route, scenarios_list)
                                wps_ = [wps_[0], wps_[-1]]
                                if (len(extended_route) <= MAX_LEN and len(potential_scenarios_definitions) > 0) and len(extended_route) > PRUNE_ROUTES_MIN_LEN:
                                    route = ET.SubElement(root, 'route', id='%d' % route_id, town=args.town)
                                    for k_, wp_sub in enumerate(wps_):
                                        ET.SubElement(route, 'waypoint', x='%f' % wp_sub.transform.location.x, y='%f' % wp_sub.transform.location.y, z='0.0', pitch='0.0', roll='0.0', yaw='%f' % wp_sub.transform.rotation.yaw)
                                    route_id += 1
                            else:
                                duplicates += 1
    else:
        PRECISION = 2
        SAMPLING_DISTANCE = 30
        duplicate_list = []
        for wp_it, waypoint in enumerate(topology):
            if waypoint.is_junction:
                junc_ = waypoint.get_junction()
                jbb_ = junc_.bounding_box
                j_wps = junc_.get_waypoints(carla.LaneType.Driving)
                for it_, j_wp in enumerate(j_wps):
                    wp_p = j_wp[0]
                    dist_prev = 0
                    wp_list_prev = []
                    while True:
                        wp_list_prev.append(wp_p)
                        try:
                            wp_p = wp_p.previous(PRECISION)[0]
                        except:
                            break
                        dist_prev += PRECISION
                        if dist_prev > SAMPLING_DISTANCE:
                            break
                    dist_nxt = 0
                    wp_n = j_wp[1]
                    wp_list_nxt = []
                    while True:
                        wp_list_nxt.append(wp_n)
                        try:
                            wp_n = wp_n.next(PRECISION)[0]
                        except:
                            break
                        dist_nxt += PRECISION
                        if dist_nxt > SAMPLING_DISTANCE:
                            break
                    final_wps_list = list(reversed(wp_list_prev[1:])) + wp_list_nxt
                    truncated_wp_lst = [final_wps_list]
                    locations = []
                    for wps_sub in truncated_wp_lst:
                        locations.append((wps_sub[0].transform.location.x, wps_sub[0].transform.location.y, wps_sub[-1].transform.location.x, wps_sub[-1].transform.location.y))
                    are_loc_dups = []
                    for location_ in locations:
                        flag_cum_ctr = []
                        for loc_dp in duplicate_list:
                            flag_ctrs = [True if prev_loc - PRECISION <= curr_loc <= prev_loc + PRECISION else False for curr_loc, prev_loc in zip(location_, loc_dp)]
                            flag_AND_ctr = all(flag_ctrs)
                            flag_cum_ctr.append(flag_AND_ctr)
                        is_loc_dup = any(flag_cum_ctr)
                        are_loc_dups.append(is_loc_dup)
                    for j_, wps_ in enumerate(truncated_wp_lst):
                        if not are_loc_dups[j_]:
                            count_all_routes += 1
                            duplicate_list.append(locations[j_])
                            wps_tmp = [wps_[0].transform.location, wps_[-1].transform.location]
                            extended_route = interpolate_trajectory(carla_map, wps_tmp)
                            potential_scenarios_definitions, _ = scan_route_for_scenarios(args.town, extended_route, scenarios_list)
                            if not len(potential_scenarios_definitions):
                                continue
                            wps_ = [wps_[0], wps_[-1]]
                            if len(extended_route) < MAX_LEN and len(potential_scenarios_definitions) > 0:
                                route = ET.SubElement(root, 'route', id='%d' % route_id, town=args.town)
                                for k_, wp_sub in enumerate(wps_):
                                    ET.SubElement(route, 'waypoint', x='%f' % wp_sub.transform.location.x, y='%f' % wp_sub.transform.location.y, z='0.0', pitch='0.0', roll='0.0', yaw='%f' % wp_sub.transform.rotation.yaw)
                                route_id += 1
                        else:
                            duplicates += 1
    tree = ET.ElementTree(root)
    len_tree = 0
    for _ in tree.iter('route'):
        len_tree += 1
    print(f'Num routes for {args.town}: {len_tree}')
    if args.save_dir is not None and len_tree > 0:
        tree.write(args.save_file, xml_declaration=True, encoding='utf-8', pretty_print=True)

def main(args):
    route_id = ID_START
    client = carla.Client('localhost', 2000)
    client.set_timeout(200.0)
    world = client.load_world(args.town)
    carla_map = world.get_map()
    actors = world.get_actors()
    traffic_lights_list = actors.filter('*traffic_light')
    print('got %d traffic lights' % len(traffic_lights_list))
    carla_topology = carla_map.get_topology()
    topology = [x[0] for x in carla_topology]
    topology = sorted(topology, key=lambda w: w.transform.location.z)
    root_7 = ET.Element('routes')
    root_8 = ET.Element('routes')
    root_9 = ET.Element('routes')
    roots_ = {'Scenario7': root_7, 'Scenario8': root_8, 'Scenario9': root_9}
    count_all_routes = 0
    duplicates = 0
    scenarios_list = {}
    scenarios_list['Scenario7'] = parse_annotations_file(args.scenarios_file['Scenario7'])
    scenarios_list['Scenario8'] = parse_annotations_file(args.scenarios_file['Scenario8'])
    scenarios_list['Scenario9'] = parse_annotations_file(args.scenarios_file['Scenario9'])
    junction_bbs_centers = []
    junctions_ = []
    duplicate_list = []
    for wp_it, waypoint in enumerate(topology):
        if waypoint.is_junction:
            junc_ = waypoint.get_junction()
            jbb_ = junc_.bounding_box
            jbb_center = [round(jbb_.location.x, 2), round(jbb_.location.y, 2)]
            if jbb_center not in junction_bbs_centers:
                junction_bbs_centers.append(jbb_center)
                junctions_.append(junc_)
    pole_ind = []
    grps_ = []
    for tl_ in traffic_lights_list:
        grp_tl = tl_.get_group_traffic_lights()
        grp_tl_locs = [(round(gtl_.get_transform().location.x, 2), round(gtl_.get_transform().location.y, 2)) for gtl_ in grp_tl]
        pole_ind.append(tl_.get_pole_index())
        if grp_tl_locs not in grps_:
            grps_.append(grp_tl_locs)
    bb_flags = []
    for grp_ in grps_:
        midpt_grp = [sum(i) / len(grp_) for i in zip(*grp_)]
        grp_bb_dist = [np.sqrt((bb_c[0] - midpt_grp[0]) ** 2 + (bb_c[1] - midpt_grp[1]) ** 2) for bb_c in junction_bbs_centers]
        bb_dist, bb_idx = min(((val, idx) for idx, val in enumerate(grp_bb_dist)))
        bb_flags.append(bb_idx)
    signalized_junctions = [junc_ for i, junc_ in enumerate(junctions_) if i in bb_flags]
    signalized_junctions_bbs = [(junc_.bounding_box.location.x, junc_.bounding_box.location.y) for i, junc_ in enumerate(junctions_) if i in bb_flags]
    if len(signalized_junctions):
        count_all_routes = 0
        duplicates = 0
        duplicate_list = []
        for wp_it, waypoint in enumerate(topology):
            if waypoint.is_junction:
                junc_ = waypoint.get_junction()
                jbb_ = (junc_.bounding_box.location.x, junc_.bounding_box.location.y)
                if jbb_ in signalized_junctions_bbs:
                    j_wps = junc_.get_waypoints(carla.LaneType.Driving)
                    for it_, j_wp in enumerate(j_wps):
                        wp_p = j_wp[0]
                        dist_prev = 0
                        wp_list_prev = []
                        while True:
                            wp_list_prev.append(wp_p)
                            try:
                                wp_p = wp_p.previous(PRECISION)[0]
                            except:
                                break
                            dist_prev += PRECISION
                            if dist_prev > SAMPLING_DISTANCE:
                                break
                        dist_nxt = 0
                        wp_n = j_wp[1]
                        wp_list_nxt = []
                        while True:
                            wp_list_nxt.append(wp_n)
                            try:
                                wp_n = wp_n.next(PRECISION)[0]
                            except:
                                break
                            dist_nxt += PRECISION
                            if dist_nxt > SAMPLING_DISTANCE:
                                break
                        final_wps_list = list(reversed(wp_list_prev[1:])) + wp_list_nxt
                        cur_wp = final_wps_list[int(len(final_wps_list) / 2)]
                        prev_wp = final_wps_list[0]
                        nxt_wp = final_wps_list[-1]
                        vec_wp_nxt = cur_wp.transform.location - nxt_wp.transform.location
                        vec_wp_prev = cur_wp.transform.location - prev_wp.transform.location
                        dot_ = vec_wp_nxt.x * vec_wp_prev.x + vec_wp_prev.y * vec_wp_nxt.y
                        det_ = vec_wp_nxt.x * vec_wp_prev.y - vec_wp_prev.x * vec_wp_nxt.y
                        angle_bet = math.atan2(det_, dot_)
                        if angle_bet < 0:
                            angle_bet += 2 * math.pi
                        angle_deg = angle_bet * 180 / math.pi
                        if 160 < angle_deg < 195:
                            key_ = 'Scenario7'
                            root = roots_['Scenario7']
                        elif 10 < angle_deg < 160:
                            key_ = 'Scenario9'
                            root = roots_['Scenario9']
                        elif 195 < angle_deg < 350:
                            key_ = 'Scenario8'
                            root = roots_['Scenario8']
                        truncated_wp_lst = [final_wps_list]
                        locations = []
                        for wps_sub in truncated_wp_lst:
                            locations.append((wps_sub[0].transform.location.x, wps_sub[0].transform.location.y, wps_sub[-1].transform.location.x, wps_sub[-1].transform.location.y))
                        are_loc_dups = []
                        for location_ in locations:
                            flag_cum_ctr = []
                            for loc_dp in duplicate_list:
                                flag_ctrs = [True if prev_loc - PRECISION <= curr_loc <= prev_loc + PRECISION else False for curr_loc, prev_loc in zip(location_, loc_dp)]
                                flag_AND_ctr = all(flag_ctrs)
                                flag_cum_ctr.append(flag_AND_ctr)
                            is_loc_dup = any(flag_cum_ctr)
                            are_loc_dups.append(is_loc_dup)
                        for j_, wps_ in enumerate(truncated_wp_lst):
                            if not are_loc_dups[j_]:
                                count_all_routes += 1
                                duplicate_list.append(locations[j_])
                                wps_tmp = [wps_[0].transform.location, wps_[-1].transform.location]
                                extended_route = interpolate_trajectory(carla_map, wps_tmp)
                                potential_scenarios_definitions, _ = scan_route_for_scenarios(carla_map.name, extended_route, scenarios_list[key_])
                                potential_scenarios_definitions = []
                                wps_ = [wps_[0], wps_[-1]]
                                if True or len(potential_scenarios_definitions) > 0:
                                    route = ET.SubElement(root, 'route', id='%d' % route_id, town=args.town)
                                    for k_, wp_sub in enumerate(wps_):
                                        ET.SubElement(route, 'waypoint', x='%f' % wp_sub.transform.location.x, y='%f' % wp_sub.transform.location.y, z='0.0', pitch='0.0', roll='0.0', yaw='%f' % wp_sub.transform.rotation.yaw)
                                    route_id += 1
                            else:
                                duplicates += 1
        tree_7 = ET.ElementTree(root_7)
        tree_8 = ET.ElementTree(root_8)
        tree_9 = ET.ElementTree(root_9)
        len_tree = 0
        for _ in tree_7.iter('route'):
            len_tree += 1
        print(f'Num routes for Scenario 7 for {args.town}: {len_tree}')
        if args.save_dir is not None and len_tree > 0:
            tree_7.write(args.save_file['Scenario7'], xml_declaration=True, encoding='utf-8', pretty_print=True)
        len_tree = 0
        for _ in tree_8.iter('route'):
            len_tree += 1
        print(f'Num routes for Scenario 8 for {args.town}: {len_tree}')
        if args.save_dir is not None and len_tree > 0:
            tree_8.write(args.save_file['Scenario8'], xml_declaration=True, encoding='utf-8', pretty_print=True)
        len_tree = 0
        for _ in tree_9.iter('route'):
            len_tree += 1
        print(f'Num routes for Scenario 9 for {args.town}: {len_tree}')
        if args.save_dir is not None and len_tree > 0:
            tree_9.write(args.save_file['Scenario9'], xml_declaration=True, encoding='utf-8', pretty_print=True)

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

def _get_latlon_ref(world_map):
    """
    Convert from waypoints world coordinates to CARLA GPS coordinates
    :return: tuple with lat and lon coordinates
    """
    xodr = world_map.to_opendrive()
    tree = ET.ElementTree(ET.fromstring(xodr))
    lat_ref = 42.0
    lon_ref = 2.0
    for opendrive in tree.iter('OpenDRIVE'):
        for header in opendrive.iter('header'):
            for georef in header.iter('geoReference'):
                if georef.text:
                    str_list = georef.text.split(' ')
                    for item in str_list:
                        if '+lat_0' in item:
                            lat_ref = float(item.split('=')[1])
                        if '+lon_0' in item:
                            lon_ref = float(item.split('=')[1])
    return (lat_ref, lon_ref)

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

def save_labels(self, filename, result):
    with open(filename, 'w') as f:
        json.dump(result, f, indent=4)
    return

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

def draw_lane_marking(surface, points, solid=True):
    if solid and len(points) > 1:
        pygame.draw.lines(surface, COLOR_WHITE, False, points, 2)
    else:
        broken_lines = [x for n, x in enumerate(zip(*(iter(points),) * 20)) if n % 3 == 0]
        for line in broken_lines:
            pygame.draw.lines(surface, COLOR_WHITE, False, line, 2)

def does_cross_solid_line(waypoint, shift):
    w = carla_map.get_waypoint(lateral_shift(waypoint.transform, shift), project_to_road=False)
    if w is None or w.road_id != waypoint.road_id:
        return True
    else:
        return w.lane_id * waypoint.lane_id < 0 or w.lane_id == waypoint.lane_id

class Renderer:

    def __init__(self, map_offset, map_dims, data_generation=True):
        self.args = {'device': 'cuda'}
        if data_generation:
            self.PIXELS_AHEAD_VEHICLE = 0
            self.local_view_dims = (500, 500)
            self.crop_dims = (500, 500)
        else:
            self.PIXELS_AHEAD_VEHICLE = 100 + 10
            self.local_view_dims = (320, 320)
            self.crop_dims = (192, 192)
        self.map_offset = map_offset
        self.map_dims = map_dims
        self.local_view_scale = (self.local_view_dims[1] / self.map_dims[1], self.local_view_dims[0] / self.map_dims[0])
        self.crop_scale = (self.crop_dims[1] / self.map_dims[1], self.crop_dims[0] / self.map_dims[0])

    def world_to_pix(self, pos):
        pos_px = (pos - self.map_offset) * PIXELS_PER_METER
        return pos_px

    def world_to_pix_crop_batched(self, query_pos, crop_pos, crop_yaw, offset=(0, 0)):
        crop_yaw = crop_yaw + np.pi / 2
        batch_size = crop_pos.shape[0]
        rotation = torch.stack([torch.cos(crop_yaw), -torch.sin(crop_yaw), torch.sin(crop_yaw), torch.cos(crop_yaw)], dim=-1).view(batch_size, 2, 2)
        crop_pos_px = self.world_to_pix(crop_pos)
        shift = torch.tensor([0.0, -self.PIXELS_AHEAD_VEHICLE], device=self.args['device'])
        query_pos_px_map = self.world_to_pix(query_pos)
        query_pos_px = torch.transpose(rotation, -2, -1).unsqueeze(1) @ (query_pos_px_map - crop_pos_px).unsqueeze(-1)
        query_pos_px = query_pos_px.squeeze(-1) - shift
        pos_px_crop = query_pos_px + torch.tensor([self.crop_dims[1] / 2, self.crop_dims[0] / 2], device=self.args['device'])
        return pos_px_crop

    def world_to_pix_crop(self, query_pos, crop_pos, crop_yaw, offset=(0, 0)):
        crop_yaw = crop_yaw + np.pi / 2
        rotation = torch.tensor([[torch.cos(crop_yaw), -torch.sin(crop_yaw)], [torch.sin(crop_yaw), torch.cos(crop_yaw)]], device=self.args['device'])
        crop_pos_px = self.world_to_pix(crop_pos)
        shift = torch.tensor([0.0, -self.PIXELS_AHEAD_VEHICLE], device=self.args['device'])
        query_pos_px_map = self.world_to_pix(query_pos)
        query_pos_px = rotation.T @ (query_pos_px_map - crop_pos_px) - shift
        pos_px_crop = query_pos_px + torch.tensor([self.crop_dims[1] / 2, self.crop_dims[0] / 2], device=self.args['device'])
        return pos_px_crop

    def world_to_rel(self, pos):
        pos_px = self.world_to_pix(pos)
        pos_rel = pos_px / torch.tensor([self.map_dims[1], self.map_dims[0]], device=self.args['device'])
        pos_rel = pos_rel * 2 - 1
        return pos_rel

    def render_agent(self, grid, vehicle, position, orientation):
        """
        """
        orientation = orientation - np.pi / 2
        scale_h = torch.tensor([grid.size(2) / vehicle.size(2)], device=self.args['device'])
        scale_w = torch.tensor([grid.size(3) / vehicle.size(3)], device=self.args['device'])
        position = self.world_to_rel(position) * -1
        scale_transform = torch.tensor([[scale_w, 0, 0], [0, scale_h, 0], [0, 0, 1]], device=self.args['device']).view(1, 3, 3)
        rotation_transform = torch.tensor([[torch.cos(orientation), torch.sin(orientation), 0], [-torch.sin(orientation), torch.cos(orientation), 0], [0, 0, 1]], device=self.args['device']).view(1, 3, 3)
        translation_transform = torch.tensor([[1, 0, position[0]], [0, 1, position[1]], [0, 0, 1]], device=self.args['device']).view(1, 3, 3)
        affine_transform = scale_transform @ rotation_transform @ translation_transform
        affine_grid = F.affine_grid(affine_transform[:, 0:2, :], (1, 1, grid.shape[2], grid.shape[3]), align_corners=True)
        vehicle_rendering = F.grid_sample(vehicle, affine_grid, align_corners=True)
        grid[:, 5, ...] += vehicle_rendering.squeeze()
        return grid

    def render_agent_bv(self, grid, grid_pos, grid_orientation, vehicle, position, orientation, channel=5, state=None):
        """
        """
        orientation = orientation + np.pi / 2
        pos_pix_bv = self.world_to_pix_crop(position, grid_pos, grid_orientation)
        h, w = (grid.size(-2), grid.size(-1))
        pos_rel_bv = pos_pix_bv / torch.tensor([h, w], device=self.args['device'])
        pos_rel_bv = pos_rel_bv * 2 - 1
        pos_rel_bv = pos_rel_bv * -1
        scale_h = torch.tensor([grid.size(2) / vehicle.size(2)], device=self.args['device'])
        scale_w = torch.tensor([grid.size(3) / vehicle.size(3)], device=self.args['device'])
        scale_transform = torch.tensor([[scale_w, 0, 0], [0, scale_h, 0], [0, 0, 1]], device=self.args['device']).view(1, 3, 3)
        grid_orientation = grid_orientation + np.pi / 2
        rotation_transform = torch.tensor([[torch.cos(orientation - grid_orientation), torch.sin(orientation - grid_orientation), 0], [-torch.sin(orientation - grid_orientation), torch.cos(orientation - grid_orientation), 0], [0, 0, 1]], device=self.args['device']).view(1, 3, 3)
        translation_transform = torch.tensor([[1, 0, pos_rel_bv[0]], [0, 1, pos_rel_bv[1]], [0, 0, 1]], device=self.args['device']).view(1, 3, 3)
        affine_transform = scale_transform @ rotation_transform @ translation_transform
        affine_grid = F.affine_grid(affine_transform[:, 0:2, :], (1, 1, grid.shape[2], grid.shape[3]), align_corners=True)
        vehicle_rendering = F.grid_sample(vehicle, affine_grid, align_corners=True)
        if state == 'Green':
            channel = 4
        elif state == 'Yellow':
            channel = 3
        elif state == 'Red':
            channel = 2
        grid[:, channel, ...] += vehicle_rendering.squeeze()

    def render_agent_bv_batched(self, grid, grid_pos, grid_orientation, vehicle, position, orientation, channel=5):
        """
        """
        orientation = orientation + np.pi / 2
        batch_size = position.shape[0]
        pos_pix_bv = self.world_to_pix_crop_batched(position, grid_pos, grid_orientation)
        h, w = (grid.size(-2), grid.size(-1))
        pos_rel_bv = pos_pix_bv / torch.tensor([h, w], device=self.args['device'])
        pos_rel_bv = pos_rel_bv * 2 - 1
        pos_rel_bv = pos_rel_bv * -1
        scale_h = torch.tensor([grid.size(2) / vehicle.size(2)], device=self.args['device'])
        scale_w = torch.tensor([grid.size(3) / vehicle.size(3)], device=self.args['device'])
        scale_transform = torch.tensor([[scale_w, 0, 0], [0, scale_h, 0], [0, 0, 1]], device=self.args['device']).view(1, 3, 3).expand(batch_size, -1, -1)
        grid_orientation = grid_orientation + np.pi / 2
        angle_delta = orientation - grid_orientation
        zeros = torch.zeros_like(angle_delta)
        ones = torch.ones_like(angle_delta)
        rotation_transform = torch.stack([torch.cos(angle_delta), torch.sin(angle_delta), zeros, -torch.sin(angle_delta), torch.cos(angle_delta), zeros, zeros, zeros, ones], dim=-1).view(batch_size, 3, 3)
        translation_transform = torch.stack([ones, zeros, pos_rel_bv[..., 0:1], zeros, ones, pos_rel_bv[..., 1:2], zeros, zeros, ones], dim=-1).view(batch_size, 3, 3)
        affine_transform = scale_transform @ rotation_transform @ translation_transform
        affine_grid = F.affine_grid(affine_transform[:, 0:2, :], (batch_size, 1, grid.shape[2], grid.shape[3]), align_corners=True)
        vehicle_rendering = F.grid_sample(vehicle, affine_grid, align_corners=True)
        for i in range(batch_size):
            grid[:, int(channel[i].item()), ...] += vehicle_rendering[i].squeeze()

    def get_local_birdview(self, grid, position, orientation):
        """
        """
        position = self.world_to_rel(position)
        orientation = orientation + np.pi / 2
        scale_transform = torch.tensor([[self.crop_scale[1], 0, 0], [0, self.crop_scale[0], 0], [0, 0, 1]], device=self.args['device']).view(1, 3, 3)
        rotation_transform = torch.tensor([[torch.cos(orientation), -torch.sin(orientation), 0], [torch.sin(orientation), torch.cos(orientation), 0], [0, 0, 1]], device=self.args['device']).view(1, 3, 3)
        shift = torch.tensor([0.0, -2 * self.PIXELS_AHEAD_VEHICLE / self.map_dims[0]], device=self.args['device'])
        position = position + rotation_transform[0, 0:2, 0:2] @ shift
        translation_transform = torch.tensor([[1, 0, position[0] / self.crop_scale[0]], [0, 1, position[1] / self.crop_scale[1]], [0, 0, 1]], device=self.args['device']).view(1, 3, 3)
        local_view_transform = scale_transform @ translation_transform @ rotation_transform
        affine_grid = F.affine_grid(local_view_transform[:, 0:2, :], (1, 1, self.crop_dims[0], self.crop_dims[0]), align_corners=True)
        local_view = F.grid_sample(grid, affine_grid, align_corners=True)
        return local_view

    def step(self, actions):
        """
        """
        print(self.ego.state, actions)
        self.ego.set_state(self.ego.motion_model(self.ego.state, actions=actions))
        self.adv.set_state(self.adv.motion_model(self.adv.state))
        self.timestep += 1

    def visualize_grid(self, grid, type='LTS_Reduced'):
        """
        """
        if type == 'LTS_Reduced':
            colors = [(102, 102, 102), (253, 253, 17), (0, 0, 142), (220, 20, 60)]
        elif type == 'Trajectory_planner':
            colors = [(102, 102, 102), (253, 253, 17)]
        elif type == 'LTS_Full':
            colors = [(102, 102, 102), (253, 253, 17), (204, 6, 5), (250, 210, 1), (39, 232, 51), (0, 0, 142), (220, 20, 60)]
        elif type == 'LTS_FullFuture':
            colors = [(102, 102, 102), (253, 253, 17), (204, 6, 5), (250, 210, 1), (39, 232, 51), (0, 0, 142), (220, 20, 60), *[(0, 0, 142 + 11 * i) for i in range(grid.shape[1] - 7)]]
        elif type == 'LTS_ReducedFuture':
            colors = [(102, 102, 102), (253, 253, 17), (0, 0, 142), (220, 20, 60), *[(0, 0, 142 + 11 * i) for i in range(grid.shape[1] - 7)]]
        grid = grid.detach().cpu()
        grid_img = np.zeros(grid.shape[2:4] + (3,), dtype=np.uint8)
        grid_img[...] = [0, 47, 0]
        for i in range(len(colors)):
            grid_img[grid[0, i, ...] > 0] = colors[i]
        pil_img = Image.fromarray(grid_img)
        return pil_img

    def bev_to_gray_img(self, grid):
        """
        """
        colors = [1, 2, 3, 4, 5, 6, 7]
        grid = grid.detach().cpu()
        grid_img = np.zeros(grid.shape[2:4], dtype=np.uint8)
        for i in range(len(colors)):
            grid_img[grid[0, i, ...] > 0] = colors[i]
        pil_img = Image.fromarray(grid_img)
        return pil_img

def step(self, actions):
    """
        """
    print(self.ego.state, actions)
    self.ego.set_state(self.ego.motion_model(self.ego.state, actions=actions))
    self.adv.set_state(self.adv.motion_model(self.adv.state))
    self.timestep += 1

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

class GlobalConfig:
    """ base architecture configurations """
    seq_len = 1
    img_seq_len = 1
    lidar_seq_len = 1
    pred_len = 4
    scale = 1
    img_resolution = (160, 704)
    img_width = 320
    lidar_resolution_width = 256
    lidar_resolution_height = 256
    pixels_per_meter = 8.0
    lidar_pos = [1.3, 0.0, 2.5]
    lidar_rot = [0.0, 0.0, -90.0]
    camera_pos = [1.3, 0.0, 2.3]
    camera_width = 960
    camera_height = 480
    camera_fov = 120
    camera_rot_0 = [0.0, 0.0, 0.0]
    camera_rot_1 = [0.0, 0.0, -60.0]
    camera_rot_2 = [0.0, 0.0, 60.0]
    bev_resolution_width = 160
    bev_resolution_height = 160
    use_target_point_image = False
    gru_concat_target_point = True
    augment = True
    inv_augment_prob = 0.1
    aug_max_rotation = 20
    debug = False
    sync_batch_norm = False
    train_debug_save_freq = 50
    bb_confidence_threshold = 0.3
    use_point_pillars = False
    max_lidar_points = 40000
    min_x = -16
    max_x = 16
    min_y = -32
    max_y = 0
    num_input = 9
    num_features = [32, 32]
    backbone = 'transFuser'
    num_dir_bins = 12
    fp16_enabled = False
    center_net_bias_init_with_prob = 0.1
    center_net_normal_init_std = 0.001
    top_k_center_keypoints = 100
    center_net_max_pooling_kernel = 3
    channel = 64
    bounding_box_divisor = 2.0
    draw_brake_threshhold = 0.5
    gru_hidden_size = 64
    num_class = 7
    classes = {0: [0, 0, 0], 1: [0, 0, 255], 2: [128, 64, 128], 3: [255, 0, 0], 4: [0, 255, 0], 5: [157, 234, 50], 6: [255, 255, 255]}
    classes_list = [[0, 0, 0], [255, 0, 0], [128, 64, 128], [0, 0, 255], [0, 255, 0], [50, 234, 157], [255, 255, 255]]
    converter = [0, 0, 0, 0, 4, 0, 5, 2, 6, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 0, 0, 5]
    lr = 0.0001
    multitask = True
    ls_seg = 1.0
    ls_depth = 10.0
    img_vert_anchors = 5
    img_horz_anchors = 20 + 2
    lidar_vert_anchors = 8
    lidar_horz_anchors = 8
    img_anchors = img_vert_anchors * img_horz_anchors
    lidar_anchors = lidar_vert_anchors * lidar_horz_anchors
    detailed_losses = ['loss_wp', 'loss_bev', 'loss_depth', 'loss_semantic', 'loss_center_heatmap', 'loss_wh', 'loss_offset', 'loss_yaw_class', 'loss_yaw_res', 'loss_velocity', 'loss_brake']
    detailed_losses_weights = [1.0, 1.0, 1.0, 1.0, 0.2, 0.2, 0.2, 0.2, 0.2, 0.0, 0.0]
    perception_output_features = 512
    bev_features_chanels = 64
    bev_upsample_factor = 2
    deconv_channel_num_1 = 128
    deconv_channel_num_2 = 64
    deconv_channel_num_3 = 32
    deconv_scale_factor_1 = 8
    deconv_scale_factor_2 = 4
    gps_buffer_max_len = 100
    carla_frame_rate = 1.0 / 20.0
    carla_fps = 20
    iou_treshold_nms = 0.2
    steer_damping = 0.5
    route_planner_min_distance = 7.5
    route_planner_max_distance = 50.0
    action_repeat = 2
    stuck_threshold = 1100 / action_repeat
    creep_duration = 30 / action_repeat
    safety_box_z_min = -2.0
    safety_box_z_max = -1.05
    safety_box_y_min = -3.0
    safety_box_y_max = 0.0
    safety_box_x_min = -1.066
    safety_box_x_max = 1.066
    ego_extent_x = 2.4508416652679443
    ego_extent_y = 1.0641621351242065
    ego_extent_z = 0.7553732395172119
    n_embd = 512
    block_exp = 4
    n_layer = 8
    n_head = 4
    n_scale = 4
    embd_pdrop = 0.1
    resid_pdrop = 0.1
    attn_pdrop = 0.1
    gpt_linear_layer_init_mean = 0.0
    gpt_linear_layer_init_std = 0.02
    gpt_layer_norm_init_weight = 1.0
    turn_KP = 1.25
    turn_KI = 0.75
    turn_KD = 0.3
    turn_n = 20
    speed_KP = 5.0
    speed_KI = 0.5
    speed_KD = 1.0
    speed_n = 20
    default_speed = 4.0
    max_throttle = 0.75
    brake_speed = 0.4
    brake_ratio = 1.1
    clip_delta = 0.25
    clip_throttle = 0.75

    def __init__(self, root_dir='', setting='all', **kwargs):
        self.root_dir = root_dir
        if setting == 'all':
            self.train_towns = os.listdir(self.root_dir)
            self.val_towns = [self.train_towns[0]]
            self.train_data, self.val_data = ([], [])
            for town in self.train_towns:
                root_files = os.listdir(os.path.join(self.root_dir, town))
                for file in root_files:
                    if not os.path.isfile(os.path.join(self.root_dir, file)):
                        self.train_data.append(os.path.join(self.root_dir, town, file))
            for town in self.val_towns:
                root_files = os.listdir(os.path.join(self.root_dir, town))
                for file in root_files:
                    if not os.path.isfile(os.path.join(self.root_dir, file)):
                        self.val_data.append(os.path.join(self.root_dir, town, file))
        elif setting == '02_05_withheld':
            print('Skip Town02 and Town05')
            self.train_towns = os.listdir(self.root_dir)
            self.val_towns = self.train_towns
            self.train_data, self.val_data = ([], [])
            for town in self.train_towns:
                root_files = os.listdir(os.path.join(self.root_dir, town))
                for file in root_files:
                    if file.find('Town02') != -1 or file.find('Town05') != -1:
                        continue
                    if not os.path.isfile(os.path.join(self.root_dir, file)):
                        print('Train Folder: ', file)
                        self.train_data.append(os.path.join(self.root_dir, town, file))
            for town in self.val_towns:
                root_files = os.listdir(os.path.join(self.root_dir, town))
                for file in root_files:
                    if file.find('Town02') == -1 and file.find('Town05') == -1:
                        continue
                    if not os.path.isfile(os.path.join(self.root_dir, file)):
                        print('Val Folder: ', file)
                        self.val_data.append(os.path.join(self.root_dir, town, file))
        elif setting == 'eval':
            pass
        else:
            print('Error: Selected setting: ', setting, ' does not exist.')
        for k, v in kwargs.items():
            setattr(self, k, v)

def __init__(self, root_dir='', setting='all', **kwargs):
    self.root_dir = root_dir
    if setting == 'all':
        self.train_towns = os.listdir(self.root_dir)
        self.val_towns = [self.train_towns[0]]
        self.train_data, self.val_data = ([], [])
        for town in self.train_towns:
            root_files = os.listdir(os.path.join(self.root_dir, town))
            for file in root_files:
                if not os.path.isfile(os.path.join(self.root_dir, file)):
                    self.train_data.append(os.path.join(self.root_dir, town, file))
        for town in self.val_towns:
            root_files = os.listdir(os.path.join(self.root_dir, town))
            for file in root_files:
                if not os.path.isfile(os.path.join(self.root_dir, file)):
                    self.val_data.append(os.path.join(self.root_dir, town, file))
    elif setting == '02_05_withheld':
        print('Skip Town02 and Town05')
        self.train_towns = os.listdir(self.root_dir)
        self.val_towns = self.train_towns
        self.train_data, self.val_data = ([], [])
        for town in self.train_towns:
            root_files = os.listdir(os.path.join(self.root_dir, town))
            for file in root_files:
                if file.find('Town02') != -1 or file.find('Town05') != -1:
                    continue
                if not os.path.isfile(os.path.join(self.root_dir, file)):
                    print('Train Folder: ', file)
                    self.train_data.append(os.path.join(self.root_dir, town, file))
        for town in self.val_towns:
            root_files = os.listdir(os.path.join(self.root_dir, town))
            for file in root_files:
                if file.find('Town02') == -1 and file.find('Town05') == -1:
                    continue
                if not os.path.isfile(os.path.join(self.root_dir, file)):
                    print('Val Folder: ', file)
                    self.val_data.append(os.path.join(self.root_dir, town, file))
    elif setting == 'eval':
        pass
    else:
        print('Error: Selected setting: ', setting, ' does not exist.')
    for k, v in kwargs.items():
        setattr(self, k, v)

class CARLA_Data(Dataset):

    def __init__(self, root, config, shared_dict=None):
        self.seq_len = np.array(config.seq_len)
        assert config.img_seq_len == 1
        self.pred_len = np.array(config.pred_len)
        self.img_resolution = np.array(config.img_resolution)
        self.img_width = np.array(config.img_width)
        self.scale = np.array(config.scale)
        self.multitask = np.array(config.multitask)
        self.data_cache = shared_dict
        self.augment = np.array(config.augment)
        self.aug_max_rotation = np.array(config.aug_max_rotation)
        self.use_point_pillars = np.array(config.use_point_pillars)
        self.max_lidar_points = np.array(config.max_lidar_points)
        self.backbone = np.array(config.backbone).astype(np.string_)
        self.inv_augment_prob = np.array(config.inv_augment_prob)
        self.converter = np.uint8(config.converter)
        self.images = []
        self.bevs = []
        self.depths = []
        self.semantics = []
        self.lidars = []
        self.labels = []
        self.measurements = []
        for sub_root in tqdm(root, file=sys.stdout):
            sub_root = Path(sub_root)
            root_files = os.listdir(sub_root)
            routes = [folder for folder in root_files if not os.path.isfile(os.path.join(sub_root, folder))]
            for route in routes:
                route_dir = sub_root / route
                num_seq = len(os.listdir(route_dir / 'lidar'))
                for seq in range(2, num_seq - self.pred_len - self.seq_len - 2):
                    image = []
                    bev = []
                    depth = []
                    semantic = []
                    lidar = []
                    label = []
                    measurement = []
                    for idx in range(self.seq_len):
                        image.append(route_dir / 'rgb' / ('%04d.png' % (seq + idx)))
                        bev.append(route_dir / 'topdown' / ('encoded_%04d.png' % (seq + idx)))
                        depth.append(route_dir / 'depth' / ('%04d.png' % (seq + idx)))
                        semantic.append(route_dir / 'semantics' / ('%04d.png' % (seq + idx)))
                        lidar.append(route_dir / 'lidar' / ('%04d.npy' % (seq + idx)))
                        measurement.append(route_dir / 'measurements' / ('%04d.json' % (seq + idx)))
                    for idx in range(self.seq_len + self.pred_len):
                        label.append(route_dir / 'label_raw' / ('%04d.json' % (seq + idx)))
                    self.images.append(image)
                    self.bevs.append(bev)
                    self.depths.append(depth)
                    self.semantics.append(semantic)
                    self.lidars.append(lidar)
                    self.labels.append(label)
                    self.measurements.append(measurement)
        self.images = np.array(self.images).astype(np.string_)
        self.bevs = np.array(self.bevs).astype(np.string_)
        self.depths = np.array(self.depths).astype(np.string_)
        self.semantics = np.array(self.semantics).astype(np.string_)
        self.lidars = np.array(self.lidars).astype(np.string_)
        self.labels = np.array(self.labels).astype(np.string_)
        self.measurements = np.array(self.measurements).astype(np.string_)
        print('Loading %d lidars from %d folders' % (len(self.lidars), len(root)))

    def __len__(self):
        """Returns the length of the dataset. """
        return self.lidars.shape[0]

    def __getitem__(self, index):
        """Returns the item at index idx. """
        cv2.setNumThreads(0)
        data = dict()
        backbone = str(self.backbone, encoding='utf-8')
        images = self.images[index]
        bevs = self.bevs[index]
        depths = self.depths[index]
        semantics = self.semantics[index]
        lidars = self.lidars[index]
        labels = self.labels[index]
        measurements = self.measurements[index]
        loaded_images = []
        loaded_bevs = []
        loaded_depths = []
        loaded_semantics = []
        loaded_lidars = []
        loaded_labels = []
        loaded_measurements = []
        if backbone == 'geometric_fusion':
            loaded_lidars_raw = []
        for i in range(self.seq_len + self.pred_len):
            if not self.data_cache is None and str(labels[i], encoding='utf-8') in self.data_cache:
                labels_i = self.data_cache[str(labels[i], encoding='utf-8')]
            else:
                with open(str(labels[i], encoding='utf-8'), 'r') as f2:
                    labels_i = ujson.load(f2)
                if not self.data_cache is None:
                    self.data_cache[str(labels[i], encoding='utf-8')] = labels_i
            loaded_labels.append(labels_i)
        for i in range(self.seq_len):
            if not self.data_cache is None and str(measurements[i], encoding='utf-8') in self.data_cache:
                measurements_i, images_i, lidars_i, lidars_raw_i, bevs_i, depths_i, semantics_i = self.data_cache[str(measurements[i], encoding='utf-8')]
                images_i = cv2.imdecode(images_i, cv2.IMREAD_UNCHANGED)
                depths_i = cv2.imdecode(depths_i, cv2.IMREAD_UNCHANGED)
                semantics_i = cv2.imdecode(semantics_i, cv2.IMREAD_UNCHANGED)
                bevs_i.seek(0)
                bevs_i = np.load(bevs_i)['arr_0']
            else:
                with open(str(measurements[i], encoding='utf-8'), 'r') as f1:
                    measurements_i = ujson.load(f1)
                lidars_i = np.load(str(lidars[i], encoding='utf-8'), allow_pickle=True)[1]
                if backbone == 'geometric_fusion':
                    lidars_raw_i = np.load(str(lidars[i], encoding='utf-8'), allow_pickle=True)[1][..., :3]
                else:
                    lidars_raw_i = None
                lidars_i[:, 1] *= -1
                images_i = cv2.imread(str(images[i], encoding='utf-8'), cv2.IMREAD_COLOR)
                if images_i is None:
                    print('Error loading file: ', str(images[i], encoding='utf-8'))
                images_i = scale_image_cv2(cv2.cvtColor(images_i, cv2.COLOR_BGR2RGB), self.scale)
                bev_array = cv2.imread(str(bevs[i], encoding='utf-8'), cv2.IMREAD_UNCHANGED)
                bev_array = cv2.cvtColor(bev_array, cv2.COLOR_BGR2RGB)
                if bev_array is None:
                    print('Error loading file: ', str(bevs[i], encoding='utf-8'))
                bev_array = np.moveaxis(bev_array, -1, 0)
                bevs_i = decode_pil_to_npy(bev_array).astype(np.uint8)
                if self.multitask:
                    depths_i = cv2.imread(str(depths[i], encoding='utf-8'), cv2.IMREAD_COLOR)
                    if depths_i is None:
                        print('Error loading file: ', str(depths[i], encoding='utf-8'))
                    depths_i = scale_image_cv2(cv2.cvtColor(depths_i, cv2.COLOR_BGR2RGB), self.scale)
                    semantics_i = cv2.imread(str(semantics[i], encoding='utf-8'), cv2.IMREAD_UNCHANGED)
                    if semantics_i is None:
                        print('Error loading file: ', str(semantics[i], encoding='utf-8'))
                    semantics_i = scale_seg(semantics_i, self.scale)
                else:
                    depths_i = None
                    semantics_i = None
                if not self.data_cache is None:
                    result, compressed_imgage = cv2.imencode('.png', images_i)
                    result, compressed_depths = cv2.imencode('.png', depths_i)
                    result, compressed_semantics = cv2.imencode('.png', semantics_i)
                    compressed_bevs = io.BytesIO()
                    np.savez_compressed(compressed_bevs, bevs_i)
                    self.data_cache[str(measurements[i], encoding='utf-8')] = (measurements_i, compressed_imgage, lidars_i, lidars_raw_i, compressed_bevs, compressed_depths, compressed_semantics)
            loaded_images.append(images_i)
            loaded_bevs.append(bevs_i)
            loaded_depths.append(depths_i)
            loaded_semantics.append(semantics_i)
            loaded_lidars.append(lidars_i)
            loaded_measurements.append(measurements_i)
            if backbone == 'geometric_fusion':
                loaded_lidars_raw.append(lidars_raw_i)
        labels = loaded_labels
        measurements = loaded_measurements
        crop_shift = 0
        degree = 0
        rad = np.deg2rad(degree)
        do_augment = self.augment and random.random() > self.inv_augment_prob
        if do_augment:
            degree = (random.random() * 2.0 - 1.0) * self.aug_max_rotation
            rad = np.deg2rad(degree)
            crop_shift = degree / 60 * self.img_width / self.scale
        images_i = loaded_images[self.seq_len - 1]
        images_i = crop_image_cv2(images_i, crop=self.img_resolution, crop_shift=crop_shift)
        bevs_i = load_crop_bev_npy(loaded_bevs[self.seq_len - 1], degree)
        data['rgb'] = images_i
        data['bev'] = bevs_i
        if self.multitask:
            depths_i = loaded_depths[self.seq_len - 1]
            depths_i = get_depth(crop_image_cv2(depths_i, crop=self.img_resolution, crop_shift=crop_shift))
            semantics_i = loaded_semantics[self.seq_len - 1]
            semantics_i = self.converter[crop_seg(semantics_i, crop=self.img_resolution, crop_shift=crop_shift)]
            data['depth'] = depths_i
            data['semantic'] = semantics_i
        lidars = []
        if backbone == 'geometric_fusion':
            lidars_raw = []
        if self.use_point_pillars == True:
            lidars_pillar = []
        for i in range(self.seq_len):
            lidar = loaded_lidars[i]
            lidar = align(lidar, measurements[i], measurements[self.seq_len - 1], degree=degree)
            lidar_bev = lidar_to_histogram_features(lidar)
            lidars.append(lidar_bev)
            if backbone == 'geometric_fusion':
                lidar_raw = loaded_lidars_raw[i]
                lidars_raw.append(lidar_raw)
            if self.use_point_pillars == True:
                lidar_pillar = deepcopy(loaded_lidars[i])
                lidar_pillar = align(lidar_pillar, measurements[i], measurements[self.seq_len - 1], degree=degree)
                lidars_pillar.append(lidar_pillar)
        lidar_bev = np.concatenate(lidars[::-1], axis=0)
        if backbone == 'geometric_fusion':
            lidars_raw = np.concatenate(lidars_raw[::-1], axis=0)
        if self.use_point_pillars == True:
            lidars_pillar = np.concatenate(lidars_pillar[::-1], axis=0)
        if backbone == 'geometric_fusion':
            curr_bev_points, curr_cam_points = lidar_bev_cam_correspondences(deepcopy(lidars_raw), debug=False)
        ego_id = labels[self.seq_len - 1][0]['id']
        bboxes = parse_labels(labels[self.seq_len - 1], rad=-rad)
        waypoints = get_waypoints(labels[self.seq_len - 1:], self.pred_len + 1)
        waypoints = transform_waypoints(waypoints)
        filtered_waypoints = []
        for id in list(bboxes.keys()) + [ego_id]:
            waypoint = []
            for matrix, flag in waypoints[id][1:]:
                waypoint.append(matrix[:2, 3])
            filtered_waypoints.append(waypoint)
        waypoints = np.array(filtered_waypoints)
        label = []
        for id in bboxes.keys():
            label.append(bboxes[id])
        label = np.array(label)
        label_pad = np.zeros((20, 7), dtype=np.float32)
        ego_waypoint = waypoints[-1]
        degree_matrix = np.array([[np.cos(rad), np.sin(rad)], [-np.sin(rad), np.cos(rad)]])
        ego_waypoint = (degree_matrix @ ego_waypoint.T).T
        if label.shape[0] > 0:
            label_pad[:label.shape[0], :] = label
        if self.use_point_pillars == True:
            fixed_lidar_raw = np.empty((self.max_lidar_points, 4), dtype=np.float32)
            num_points = min(self.max_lidar_points, lidars_pillar.shape[0])
            fixed_lidar_raw[:num_points, :4] = lidars_pillar
            data['lidar_raw'] = fixed_lidar_raw
            data['num_points'] = num_points
        if backbone == 'geometric_fusion':
            data['bev_points'] = curr_bev_points
            data['cam_points'] = curr_cam_points
        data['lidar'] = lidar_bev
        data['label'] = label_pad
        data['ego_waypoint'] = ego_waypoint
        data['steer'] = measurements[self.seq_len - 1]['steer']
        data['throttle'] = measurements[self.seq_len - 1]['throttle']
        data['brake'] = measurements[self.seq_len - 1]['brake']
        data['light'] = measurements[self.seq_len - 1]['light_hazard']
        data['speed'] = measurements[self.seq_len - 1]['speed']
        data['theta'] = measurements[self.seq_len - 1]['theta']
        data['x_command'] = measurements[self.seq_len - 1]['x_command']
        data['y_command'] = measurements[self.seq_len - 1]['y_command']
        ego_theta = measurements[self.seq_len - 1]['theta'] + rad
        ego_x = measurements[self.seq_len - 1]['x']
        ego_y = measurements[self.seq_len - 1]['y']
        x_command = measurements[self.seq_len - 1]['x_command']
        y_command = measurements[self.seq_len - 1]['y_command']
        R = np.array([[np.cos(np.pi / 2 + ego_theta), -np.sin(np.pi / 2 + ego_theta)], [np.sin(np.pi / 2 + ego_theta), np.cos(np.pi / 2 + ego_theta)]])
        local_command_point = np.array([x_command - ego_x, y_command - ego_y])
        local_command_point = R.T.dot(local_command_point)
        data['target_point'] = local_command_point
        data['target_point_image'] = draw_target_point(local_command_point)
        return data

def __init__(self, root, config, shared_dict=None):
    self.seq_len = np.array(config.seq_len)
    assert config.img_seq_len == 1
    self.pred_len = np.array(config.pred_len)
    self.img_resolution = np.array(config.img_resolution)
    self.img_width = np.array(config.img_width)
    self.scale = np.array(config.scale)
    self.multitask = np.array(config.multitask)
    self.data_cache = shared_dict
    self.augment = np.array(config.augment)
    self.aug_max_rotation = np.array(config.aug_max_rotation)
    self.use_point_pillars = np.array(config.use_point_pillars)
    self.max_lidar_points = np.array(config.max_lidar_points)
    self.backbone = np.array(config.backbone).astype(np.string_)
    self.inv_augment_prob = np.array(config.inv_augment_prob)
    self.converter = np.uint8(config.converter)
    self.images = []
    self.bevs = []
    self.depths = []
    self.semantics = []
    self.lidars = []
    self.labels = []
    self.measurements = []
    for sub_root in tqdm(root, file=sys.stdout):
        sub_root = Path(sub_root)
        root_files = os.listdir(sub_root)
        routes = [folder for folder in root_files if not os.path.isfile(os.path.join(sub_root, folder))]
        for route in routes:
            route_dir = sub_root / route
            num_seq = len(os.listdir(route_dir / 'lidar'))
            for seq in range(2, num_seq - self.pred_len - self.seq_len - 2):
                image = []
                bev = []
                depth = []
                semantic = []
                lidar = []
                label = []
                measurement = []
                for idx in range(self.seq_len):
                    image.append(route_dir / 'rgb' / ('%04d.png' % (seq + idx)))
                    bev.append(route_dir / 'topdown' / ('encoded_%04d.png' % (seq + idx)))
                    depth.append(route_dir / 'depth' / ('%04d.png' % (seq + idx)))
                    semantic.append(route_dir / 'semantics' / ('%04d.png' % (seq + idx)))
                    lidar.append(route_dir / 'lidar' / ('%04d.npy' % (seq + idx)))
                    measurement.append(route_dir / 'measurements' / ('%04d.json' % (seq + idx)))
                for idx in range(self.seq_len + self.pred_len):
                    label.append(route_dir / 'label_raw' / ('%04d.json' % (seq + idx)))
                self.images.append(image)
                self.bevs.append(bev)
                self.depths.append(depth)
                self.semantics.append(semantic)
                self.lidars.append(lidar)
                self.labels.append(label)
                self.measurements.append(measurement)
    self.images = np.array(self.images).astype(np.string_)
    self.bevs = np.array(self.bevs).astype(np.string_)
    self.depths = np.array(self.depths).astype(np.string_)
    self.semantics = np.array(self.semantics).astype(np.string_)
    self.lidars = np.array(self.lidars).astype(np.string_)
    self.labels = np.array(self.labels).astype(np.string_)
    self.measurements = np.array(self.measurements).astype(np.string_)
    print('Loading %d lidars from %d folders' % (len(self.lidars), len(root)))

def get_waypoints(labels, len_labels):
    assert len(labels) == len_labels
    num = len_labels
    waypoints = {}
    for result in labels[0]:
        car_id = result['id']
        waypoints[car_id] = [[result['ego_matrix'], True]]
        for i in range(1, num):
            for to_match in labels[i]:
                if to_match['id'] == car_id:
                    waypoints[car_id].append([to_match['ego_matrix'], True])
    Identity = list((list(row) for row in np.eye(4)))
    for k in waypoints.keys():
        while len(waypoints[k]) < num:
            waypoints[k].append([Identity, False])
    return waypoints

def transform_waypoints(waypoints):
    """transform waypoints to be origin at ego_matrix"""
    T = get_vehicle_to_virtual_lidar_transform()
    for k in waypoints.keys():
        vehicle_matrix = np.array(waypoints[k][0][0])
        vehicle_matrix_inv = np.linalg.inv(vehicle_matrix)
        for i in range(1, len(waypoints[k])):
            matrix = np.array(waypoints[k][i][0])
            waypoints[k][i][0] = T @ vehicle_matrix_inv @ matrix
    return waypoints

class PointPillarNet(nn.Module):

    def __init__(self, num_input=9, num_features=[32, 32], min_x=-10, max_x=70, min_y=-40, max_y=40, pixels_per_meter=4):
        super().__init__()
        self.point_net = DynamicPointNet(num_input, num_features)
        self.nx = (max_x - min_x) * pixels_per_meter
        self.ny = (max_y - min_y) * pixels_per_meter
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y
        self.pixels_per_meter = pixels_per_meter

    def decorate(self, points, unique_coords, inverse_indices):
        dtype = points.dtype
        x_centers = unique_coords[inverse_indices][:, 2:3].to(dtype) / self.pixels_per_meter + self.min_x
        y_centers = unique_coords[inverse_indices][:, 1:2].to(dtype) / self.pixels_per_meter + self.min_y
        xyz = points[:, :3]
        points_cluster = xyz - scatter_mean(xyz, inverse_indices, dim=0)[inverse_indices]
        points_xp = xyz[:, :1] - x_centers
        points_yp = xyz[:, 1:2] - y_centers
        features = torch.cat([points, points_cluster, points_xp, points_yp], dim=-1)
        return features

    def grid_locations(self, points):
        keep = (points[:, 0] >= self.min_x) & (points[:, 0] < self.max_x) & (points[:, 1] >= self.min_y) & (points[:, 1] < self.max_y)
        points = points[keep, :]
        coords = (points[:, [0, 1]] - torch.tensor([self.min_x, self.min_y], device=points.device)) * self.pixels_per_meter
        coords = coords.long()
        return (points, coords)

    def pillar_generation(self, points, coords):
        unique_coords, inverse_indices = coords.unique(return_inverse=True, dim=0)
        decorated_points = self.decorate(points, unique_coords, inverse_indices)
        return (decorated_points, unique_coords, inverse_indices)

    def scatter_points(self, features, coords, batch_size):
        canvas = torch.zeros(batch_size, features.shape[1], self.ny, self.nx, dtype=features.dtype, device=features.device)
        canvas[coords[:, 0], :, torch.clamp(self.ny - 1 - coords[:, 1], 0, self.ny - 1), torch.clamp(coords[:, 2], 0, self.nx - 1)] = features
        return canvas

    def forward(self, lidar_list, num_points):
        batch_size = len(lidar_list)
        with torch.no_grad():
            coords = []
            filtered_points = []
            for batch_id, points in enumerate(lidar_list):
                points = points[:num_points[batch_id]]
                points, grid_yx = self.grid_locations(points)
                grid_byx = torch.nn.functional.pad(grid_yx, (1, 0), mode='constant', value=batch_id)
                coords.append(grid_byx)
                filtered_points.append(points)
            coords = torch.cat(coords, dim=0)
            filtered_points = torch.cat(filtered_points, dim=0)
            decorated_points, unique_coords, inverse_indices = self.pillar_generation(filtered_points, coords)
        features = self.point_net(decorated_points, inverse_indices)
        return self.scatter_points(features, unique_coords, batch_size)

def pillar_generation(self, points, coords):
    unique_coords, inverse_indices = coords.unique(return_inverse=True, dim=0)
    decorated_points = self.decorate(points, unique_coords, inverse_indices)
    return (decorated_points, unique_coords, inverse_indices)

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

