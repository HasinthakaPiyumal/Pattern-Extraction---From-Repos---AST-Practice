# Cluster 4

def convert_transform_to_location(transform_vec):
    """
    Convert a vector of transforms to a vector of locations
    """
    location_vec = []
    for transform_tuple in transform_vec:
        location_vec.append((transform_tuple[0].location, transform_tuple[1]))
    return location_vec

def compare_scenarios(scenario_choice, existent_scenario):
    """
    Compare function for scenarios based on distance of the scenario start position
    """

    def transform_to_pos_vec(scenario):
        """
        Convert left/right/front to a meaningful CARLA position
        """
        position_vec = [scenario['trigger_position']]
        if scenario['other_actors'] is not None:
            if 'left' in scenario['other_actors']:
                position_vec += scenario['other_actors']['left']
            if 'front' in scenario['other_actors']:
                position_vec += scenario['other_actors']['front']
            if 'right' in scenario['other_actors']:
                position_vec += scenario['other_actors']['right']
        return position_vec
    choice_vec = transform_to_pos_vec(scenario_choice)
    existent_vec = transform_to_pos_vec(existent_scenario)
    for pos_choice in choice_vec:
        for pos_existent in existent_vec:
            dx = float(pos_choice['x']) - float(pos_existent['x'])
            dy = float(pos_choice['y']) - float(pos_existent['y'])
            dz = float(pos_choice['z']) - float(pos_existent['z'])
            dist_position = math.sqrt(dx * dx + dy * dy + dz * dz)
            dyaw = float(pos_choice['yaw']) - float(pos_choice['yaw'])
            dist_angle = math.sqrt(dyaw * dyaw)
            if dist_position < TRIGGER_THRESHOLD and dist_angle < TRIGGER_ANGLE_THRESHOLD:
                return True
    return False

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

def get_actors_from_list(list_of_actor_def):
    """
                Receives a list of actor definitions and creates an actual list of ActorConfigurationObjects
            """
    sublist_of_actors = []
    for actor_def in list_of_actor_def:
        sublist_of_actors.append(convert_json_to_actor(actor_def))
    return sublist_of_actors

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

class BackgroundActivity(BasicScenario):
    """
    Implementation of a scenario to spawn a set of background actors,
    and to remove traffic jams in background traffic

    This is a single ego vehicle scenario
    """
    category = 'BackgroundActivity'
    town_amount = {'Town01': 120, 'Town02': 100, 'Town03': 120, 'Town04': 200, 'Town05': 120, 'Town06': 150, 'Town07': 110, 'Town08': 180, 'Town09': 300, 'Town10': 120}

    def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, timeout=35 * 60):
        """
        Setup all relevant parameters and create scenario
        """
        self.config = config
        self.debug = debug_mode
        self.timeout = timeout
        super(BackgroundActivity, self).__init__('BackgroundActivity', ego_vehicles, config, world, debug_mode, terminate_on_failure=True, criteria_enable=True)

    def _initialize_actors(self, config):
        town_name = config.town
        if town_name in self.town_amount:
            amount = self.town_amount[town_name]
        else:
            amount = 0
        new_actors = CarlaDataProvider.request_new_batch_actors('vehicle.*', amount, carla.Transform(), autopilot=True, random_location=True, rolename='background')
        if new_actors is None:
            raise Exception('Error: Unable to add the background activity, all spawn points were occupied')
        for _actor in new_actors:
            self.other_actors.append(_actor)

    def _create_behavior(self):
        """
        Basic behavior do nothing, i.e. Idle
        """
        pass

    def _create_test_criteria(self):
        """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
        pass

    def __del__(self):
        """
        Remove all actors upon deletion
        """
        self.remove_all_actors()

def _initialize_actors(self, config):
    town_name = config.town
    if town_name in self.town_amount:
        amount = self.town_amount[town_name]
    else:
        amount = 0
    new_actors = CarlaDataProvider.request_new_batch_actors('vehicle.*', amount, carla.Transform(), autopilot=True, random_location=True, rolename='background')
    if new_actors is None:
        raise Exception('Error: Unable to add the background activity, all spawn points were occupied')
    for _actor in new_actors:
        self.other_actors.append(_actor)

def convert_transform_to_location(transform_vec):
    """
    Convert a vector of transforms to a vector of locations
    """
    location_vec = []
    for transform_tuple in transform_vec:
        location_vec.append((transform_tuple[0].location, transform_tuple[1]))
    return location_vec

def compare_scenarios(scenario_choice, existent_scenario):
    """
    Compare function for scenarios based on distance of the scenario start position
    """

    def transform_to_pos_vec(scenario):
        """
        Convert left/right/front to a meaningful CARLA position
        """
        position_vec = [scenario['trigger_position']]
        if scenario['other_actors'] is not None:
            if 'left' in scenario['other_actors']:
                position_vec += scenario['other_actors']['left']
            if 'front' in scenario['other_actors']:
                position_vec += scenario['other_actors']['front']
            if 'right' in scenario['other_actors']:
                position_vec += scenario['other_actors']['right']
        return position_vec
    choice_vec = transform_to_pos_vec(scenario_choice)
    existent_vec = transform_to_pos_vec(existent_scenario)
    for pos_choice in choice_vec:
        for pos_existent in existent_vec:
            dx = float(pos_choice['x']) - float(pos_existent['x'])
            dy = float(pos_choice['y']) - float(pos_existent['y'])
            dz = float(pos_choice['z']) - float(pos_existent['z'])
            dist_position = math.sqrt(dx * dx + dy * dy + dz * dz)
            dyaw = float(pos_choice['yaw']) - float(pos_choice['yaw'])
            dist_angle = math.sqrt(dyaw * dyaw)
            if dist_position < TRIGGER_THRESHOLD and dist_angle < TRIGGER_ANGLE_THRESHOLD:
                return True
    return False

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

def get_actors_from_list(list_of_actor_def):
    """
                Receives a list of actor definitions and creates an actual list of ActorConfigurationObjects
            """
    sublist_of_actors = []
    for actor_def in list_of_actor_def:
        sublist_of_actors.append(convert_json_to_actor(actor_def))
    return sublist_of_actors

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

class ActorSpeedAboveThresholdTest(Criterion):
    """
    This test will fail if the actor has had its linear velocity lower than a specific value for
    a specific amount of time

    Important parameters:
    - actor: CARLA actor to be used for this test
    - speed_threshold: speed required
    - below_threshold_max_time: Maximum time (in seconds) the actor can remain under the speed threshold
    - terminate_on_failure [optional]: If True, the complete scenario will terminate upon failure of this test
    """

    def __init__(self, actor, speed_threshold, below_threshold_max_time, name='ActorSpeedAboveThresholdTest', terminate_on_failure=False):
        """
        Class constructor.
        """
        super(ActorSpeedAboveThresholdTest, self).__init__(name, actor, 0, terminate_on_failure=terminate_on_failure)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._actor = actor
        self._speed_threshold = speed_threshold
        self._below_threshold_max_time = below_threshold_max_time
        self._time_last_valid_state = None

    def update(self):
        """
        Check if the actor speed is above the speed_threshold
        """
        new_status = py_trees.common.Status.RUNNING
        linear_speed = CarlaDataProvider.get_velocity(self._actor)
        if linear_speed is not None:
            if linear_speed < self._speed_threshold and self._time_last_valid_state:
                if GameTime.get_time() - self._time_last_valid_state > self._below_threshold_max_time:
                    self.test_status = 'FAILURE'
                    vehicle_location = CarlaDataProvider.get_location(self._actor)
                    blocked_event = TrafficEvent(event_type=TrafficEventType.VEHICLE_BLOCKED)
                    ActorSpeedAboveThresholdTest._set_event_message(blocked_event, vehicle_location)
                    ActorSpeedAboveThresholdTest._set_event_dict(blocked_event, vehicle_location)
                    self.list_traffic_events.append(blocked_event)
            else:
                self._time_last_valid_state = GameTime.get_time()
        if self._terminate_on_failure and self.test_status == 'FAILURE':
            new_status = py_trees.common.Status.FAILURE
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

    @staticmethod
    def _set_event_message(event, location):
        """
        Sets the message of the event
        """
        event.set_message('Agent got blocked at (x={}, y={}, z={})'.format(round(location.x, 3), round(location.y, 3), round(location.z, 3)))

    @staticmethod
    def _set_event_dict(event, location):
        """
        Sets the dictionary of the event
        """
        event.set_dict({'x': location.x, 'y': location.y, 'z': location.z})

def update(self):
    """
        Check if the actor speed is above the speed_threshold
        """
    new_status = py_trees.common.Status.RUNNING
    linear_speed = CarlaDataProvider.get_velocity(self._actor)
    if linear_speed is not None:
        if linear_speed < self._speed_threshold and self._time_last_valid_state:
            if GameTime.get_time() - self._time_last_valid_state > self._below_threshold_max_time:
                self.test_status = 'FAILURE'
                vehicle_location = CarlaDataProvider.get_location(self._actor)
                blocked_event = TrafficEvent(event_type=TrafficEventType.VEHICLE_BLOCKED)
                ActorSpeedAboveThresholdTest._set_event_message(blocked_event, vehicle_location)
                ActorSpeedAboveThresholdTest._set_event_dict(blocked_event, vehicle_location)
                self.list_traffic_events.append(blocked_event)
        else:
            self._time_last_valid_state = GameTime.get_time()
    if self._terminate_on_failure and self.test_status == 'FAILURE':
        new_status = py_trees.common.Status.FAILURE
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    return new_status

@staticmethod
def _set_event_message(event, location):
    """
        Sets the message of the event
        """
    event.set_message('Agent got blocked at (x={}, y={}, z={})'.format(round(location.x, 3), round(location.y, 3), round(location.z, 3)))

@staticmethod
def _set_event_dict(event, location):
    """
        Sets the dictionary of the event
        """
    event.set_dict({'x': location.x, 'y': location.y, 'z': location.z})

def compute_route_length(config):
    trajectory = config.trajectory
    route_length = 0.0
    previous_location = None
    for location in trajectory:
        if previous_location:
            dist = math.sqrt((location.x - previous_location.x) * (location.x - previous_location.x) + (location.y - previous_location.y) * (location.y - previous_location.y) + (location.z - previous_location.z) * (location.z - previous_location.z))
            route_length += dist
        previous_location = location
    return route_length

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

def location_route_to_gps(route, lat_ref, lon_ref):
    """
        Locate each waypoint of the route into gps, (lat long ) representations.
    :param route:
    :param lat_ref:
    :param lon_ref:
    :return:
    """
    gps_route = []
    for transform, connection in route:
        gps_point = _location_to_gps(lat_ref, lon_ref, transform.location)
        gps_route.append((gps_point, connection))
    return gps_route

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

def compute_route_length(config):
    trajectory = config.trajectory
    route_length = 0.0
    previous_location = None
    for location in trajectory:
        if previous_location:
            dist = math.sqrt((location.x - previous_location.x) * (location.x - previous_location.x) + (location.y - previous_location.y) * (location.y - previous_location.y) + (location.z - previous_location.z) * (location.z - previous_location.z))
            route_length += dist
        previous_location = location
    return route_length

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

def _record_control(self):
    new_record = {'control': {'throttle': self._control.throttle, 'steer': self._control.steer, 'brake': self._control.brake, 'hand_brake': self._control.hand_brake, 'reverse': self._control.reverse, 'manual_gear_shift': self._control.manual_gear_shift, 'gear': self._control.gear}}
    self._log_data['records'].append(new_record)

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
def length(v):
    return math.sqrt(v.x ** 2 + v.y ** 2 + v.z ** 2)

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

def register_module(self, module):
    self.modules.append(module)

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

def lateral_shift(transform, shift):
    transform.rotation.yaw += 90
    return transform.location + shift * transform.get_forward_vector()

class OtherLeadingVehicle(BasicScenario):
    """
    This class holds everything required for a simple "Other Leading Vehicle"
    scenario involving a user controlled vehicle and two other actors.
    Traffic Scenario 05

    This is a single ego vehicle scenario
    """

    def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, criteria_enable=True, timeout=80):
        """
        Setup all relevant parameters and create scenario
        """
        self._world = world
        self._map = CarlaDataProvider.get_map()
        self._first_vehicle_location = 35
        self._second_vehicle_location = self._first_vehicle_location + 1
        self._ego_vehicle_drive_distance = self._first_vehicle_location * 4
        self._first_vehicle_speed = 55
        self._second_vehicle_speed = 45
        self._reference_waypoint = self._map.get_waypoint(config.trigger_points[0].location)
        self._other_actor_max_brake = 1.0
        self._first_actor_transform = None
        self._second_actor_transform = None
        self.timeout = timeout
        super(OtherLeadingVehicle, self).__init__('VehicleDeceleratingInMultiLaneSetUp', ego_vehicles, config, world, debug_mode, criteria_enable=criteria_enable)

    def _initialize_actors(self, config):
        """
        Custom initialization
        """
        first_vehicle_waypoint, _ = get_waypoint_in_distance(self._reference_waypoint, self._first_vehicle_location)
        second_vehicle_waypoint, _ = get_waypoint_in_distance(self._reference_waypoint, self._second_vehicle_location)
        second_vehicle_waypoint = second_vehicle_waypoint.get_left_lane()
        first_vehicle_transform = carla.Transform(first_vehicle_waypoint.transform.location, first_vehicle_waypoint.transform.rotation)
        second_vehicle_transform = carla.Transform(second_vehicle_waypoint.transform.location, second_vehicle_waypoint.transform.rotation)
        first_vehicle = CarlaDataProvider.request_new_actor('vehicle.nissan.patrol', first_vehicle_transform)
        second_vehicle = CarlaDataProvider.request_new_actor('vehicle.audi.tt', second_vehicle_transform)
        self.other_actors.append(first_vehicle)
        self.other_actors.append(second_vehicle)
        self._first_actor_transform = first_vehicle_transform
        self._second_actor_transform = second_vehicle_transform

    def _create_behavior(self):
        """
        The scenario defined after is a "other leading vehicle" scenario. After
        invoking this scenario, the user controlled vehicle has to drive towards the
        moving other actors, then make the leading actor to decelerate when user controlled
        vehicle is at some close distance. Finally, the user-controlled vehicle has to change
        lane to avoid collision and follow other leading actor in other lane to end the scenario.
        If this does not happen within 90 seconds, a timeout stops the scenario or the ego vehicle
        drives certain distance and stops the scenario.
        """
        driving_in_same_direction = py_trees.composites.Parallel('All actors driving in same direction', policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)
        leading_actor_sequence_behavior = py_trees.composites.Sequence('Decelerating actor sequence behavior')
        keep_velocity = py_trees.composites.Parallel('Trigger condition for deceleration', policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)
        keep_velocity.add_child(WaypointFollower(self.other_actors[0], self._first_vehicle_speed, avoid_collision=True))
        keep_velocity.add_child(InTriggerDistanceToVehicle(self.other_actors[0], self.ego_vehicles[0], 55))
        decelerate = self._first_vehicle_speed / 3.2
        leading_actor_sequence_behavior.add_child(keep_velocity)
        leading_actor_sequence_behavior.add_child(WaypointFollower(self.other_actors[0], decelerate, avoid_collision=True))
        ego_drive_distance = DriveDistance(self.ego_vehicles[0], self._ego_vehicle_drive_distance)
        sequence = py_trees.composites.Sequence('Scenario behavior')
        parallel_root = py_trees.composites.Parallel(policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)
        parallel_root.add_child(ego_drive_distance)
        parallel_root.add_child(driving_in_same_direction)
        driving_in_same_direction.add_child(leading_actor_sequence_behavior)
        driving_in_same_direction.add_child(WaypointFollower(self.other_actors[1], self._second_vehicle_speed, avoid_collision=True))
        sequence.add_child(ActorTransformSetter(self.other_actors[0], self._first_actor_transform))
        sequence.add_child(ActorTransformSetter(self.other_actors[1], self._second_actor_transform))
        sequence.add_child(parallel_root)
        sequence.add_child(ActorDestroy(self.other_actors[0]))
        sequence.add_child(ActorDestroy(self.other_actors[1]))
        return sequence

    def _create_test_criteria(self):
        """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
        criteria = []
        collision_criterion = CollisionTest(self.ego_vehicles[0])
        criteria.append(collision_criterion)
        return criteria

    def __del__(self):
        self.remove_all_actors()

def _create_test_criteria(self):
    """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
    criteria = []
    collision_criterion = CollisionTest(self.ego_vehicles[0])
    criteria.append(collision_criterion)
    return criteria

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

class SignalizedJunctionRightTurn(BasicScenario):
    """
    Implementation class for Hero
    Vehicle turning right at signalized junction scenario,
    Traffic Scenario 09.

    This is a single ego vehicle scenario
    """

    def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, criteria_enable=True, timeout=80):
        """
        Setup all relevant parameters and create scenario
        """
        self._target_vel = 6.9
        self._brake_value = 0.5
        self._ego_distance = 40
        self._traffic_light = None
        self._other_actor_transform = None
        self.timeout = timeout
        super(SignalizedJunctionRightTurn, self).__init__('HeroActorTurningRightAtSignalizedJunction', ego_vehicles, config, world, debug_mode, criteria_enable=criteria_enable)
        self._traffic_light = CarlaDataProvider.get_next_traffic_light(self.ego_vehicles[0], False)
        if self._traffic_light is None:
            print('No traffic light for the given location of the ego vehicle found')
            sys.exit(-1)
        self._traffic_light.set_state(carla.TrafficLightState.Red)
        self._traffic_light.set_red_time(self.timeout)
        traffic_light_other = CarlaDataProvider.get_next_traffic_light(self.other_actors[0], False)
        if traffic_light_other is None:
            print('No traffic light for the given location of the other vehicle found')
            sys.exit(-1)
        traffic_light_other.set_state(carla.TrafficLightState.Green)
        traffic_light_other.set_green_time(self.timeout)

    def _initialize_actors(self, config):
        """
        Custom initialization
        """
        self._other_actor_transform = config.other_actors[0].transform
        first_vehicle_transform = carla.Transform(carla.Location(config.other_actors[0].transform.location.x, config.other_actors[0].transform.location.y, config.other_actors[0].transform.location.z - 500), config.other_actors[0].transform.rotation)
        first_vehicle = CarlaDataProvider.request_new_actor(config.other_actors[0].model, first_vehicle_transform)
        first_vehicle.set_simulate_physics(enabled=False)
        self.other_actors.append(first_vehicle)

    def _create_behavior(self):
        """
        Hero vehicle is turning right in an urban area,
        at a signalized intersection, while other actor coming straight
        from left.The hero actor may turn right either before other actor
        passes intersection or later, without any collision.
        After 80 seconds, a timeout stops the scenario.
        """
        location_of_collision_dynamic = get_geometric_linear_intersection(self.ego_vehicles[0], self.other_actors[0])
        crossing_point_dynamic = get_crossing_point(self.other_actors[0])
        sync_arrival = SyncArrival(self.other_actors[0], self.ego_vehicles[0], location_of_collision_dynamic)
        sync_arrival_stop = InTriggerDistanceToLocation(self.other_actors[0], crossing_point_dynamic, 5)
        sync_arrival_parallel = py_trees.composites.Parallel('Synchronize arrival times', policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)
        sync_arrival_parallel.add_child(sync_arrival)
        sync_arrival_parallel.add_child(sync_arrival_stop)
        target_waypoint = generate_target_waypoint(CarlaDataProvider.get_map().get_waypoint(self.other_actors[0].get_location()), 0)
        plan = []
        wp_choice = target_waypoint.next(1.0)
        while not wp_choice[0].is_intersection:
            target_waypoint = wp_choice[0]
            plan.append((target_waypoint, RoadOption.LANEFOLLOW))
            wp_choice = target_waypoint.next(1.0)
        move_actor = WaypointFollower(self.other_actors[0], self._target_vel, plan=plan)
        waypoint_follower_end = InTriggerDistanceToLocation(self.other_actors[0], plan[-1][0].transform.location, 10)
        move_actor_parallel = py_trees.composites.Parallel(policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)
        move_actor_parallel.add_child(move_actor)
        move_actor_parallel.add_child(waypoint_follower_end)
        stop = StopVehicle(self.other_actors[0], self._brake_value)
        end_condition = DriveDistance(self.ego_vehicles[0], self._ego_distance)
        sequence = py_trees.composites.Sequence()
        sequence.add_child(ActorTransformSetter(self.other_actors[0], self._other_actor_transform))
        sequence.add_child(sync_arrival_parallel)
        sequence.add_child(move_actor_parallel)
        sequence.add_child(stop)
        sequence.add_child(end_condition)
        sequence.add_child(ActorDestroy(self.other_actors[0]))
        return sequence

    def _create_test_criteria(self):
        """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
        criteria = []
        collison_criteria = CollisionTest(self.ego_vehicles[0])
        criteria.append(collison_criteria)
        return criteria

    def __del__(self):
        self._traffic_light = None
        self.remove_all_actors()

def _create_test_criteria(self):
    """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
    criteria = []
    collison_criteria = CollisionTest(self.ego_vehicles[0])
    criteria.append(collison_criteria)
    return criteria

class CutIn(BasicScenario):
    """
    The ego vehicle is driving on a highway and another car is cutting in just in front.
    This is a single ego vehicle scenario
    """
    timeout = 1200

    def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, criteria_enable=True, timeout=600):
        self.timeout = timeout
        self._map = CarlaDataProvider.get_map()
        self._reference_waypoint = self._map.get_waypoint(config.trigger_points[0].location)
        self._velocity = 40
        self._delta_velocity = 10
        self._trigger_distance = 30
        self._config = config
        self._direction = None
        self._transform_visible = None
        super(CutIn, self).__init__('CutIn', ego_vehicles, config, world, debug_mode, criteria_enable=criteria_enable)
        if randomize:
            self._velocity = random.randint(20, 60)
            self._trigger_distance = random.randint(10, 40)

    def _initialize_actors(self, config):
        if 'LEFT' in self._config.name.upper():
            self._direction = 'left'
        if 'RIGHT' in self._config.name.upper():
            self._direction = 'right'
        for actor in config.other_actors:
            vehicle = CarlaDataProvider.request_new_actor(actor.model, actor.transform)
            self.other_actors.append(vehicle)
            vehicle.set_simulate_physics(enabled=False)
        other_actor_transform = self.other_actors[0].get_transform()
        self._transform_visible = carla.Transform(carla.Location(other_actor_transform.location.x, other_actor_transform.location.y, other_actor_transform.location.z + 105), other_actor_transform.rotation)

    def _create_behavior(self):
        """
        Order of sequence:
        - car_visible: spawn car at a visible transform
        - just_drive: drive until in trigger distance to ego_vehicle
        - accelerate: accelerate to catch up distance to ego_vehicle
        - lane_change: change the lane
        - endcondition: drive for a defined distance
        """
        behaviour = py_trees.composites.Sequence('CarOn_{}_Lane'.format(self._direction))
        car_visible = ActorTransformSetter(self.other_actors[0], self._transform_visible)
        behaviour.add_child(car_visible)
        just_drive = py_trees.composites.Parallel('DrivingStraight', policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)
        car_driving = WaypointFollower(self.other_actors[0], self._velocity)
        just_drive.add_child(car_driving)
        trigger_distance = InTriggerDistanceToVehicle(self.other_actors[0], self.ego_vehicles[0], self._trigger_distance)
        just_drive.add_child(trigger_distance)
        behaviour.add_child(just_drive)
        accelerate = AccelerateToCatchUp(self.other_actors[0], self.ego_vehicles[0], throttle_value=1, delta_velocity=self._delta_velocity, trigger_distance=5, max_distance=500)
        behaviour.add_child(accelerate)
        if self._direction == 'left':
            lane_change = LaneChange(self.other_actors[0], speed=None, direction='right', distance_same_lane=5, distance_other_lane=300)
            behaviour.add_child(lane_change)
        else:
            lane_change = LaneChange(self.other_actors[0], speed=None, direction='left', distance_same_lane=5, distance_other_lane=300)
            behaviour.add_child(lane_change)
        endcondition = DriveDistance(self.other_actors[0], 200)
        root = py_trees.composites.Sequence('Behavior', policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)
        root.add_child(behaviour)
        root.add_child(endcondition)
        return root

    def _create_test_criteria(self):
        """
        A list of all test criteria is created, which is later used in the parallel behavior tree.
        """
        criteria = []
        collision_criterion = CollisionTest(self.ego_vehicles[0])
        criteria.append(collision_criterion)
        return criteria

    def __del__(self):
        """
        Remove all actors after deletion.
        """
        self.remove_all_actors()

def _create_test_criteria(self):
    """
        A list of all test criteria is created, which is later used in the parallel behavior tree.
        """
    criteria = []
    collision_criterion = CollisionTest(self.ego_vehicles[0])
    criteria.append(collision_criterion)
    return criteria

class StoryElementStatusToBlackboard(Decorator):
    """
    Reflect the status of the decorator's child story element to the blackboard.

    Args:
        child: the child behaviour or subtree
        story_element_type: the element type [act,scene,maneuver,event,action]
        element_name: the story element's name attribute
    """

    def __init__(self, child, story_element_type, element_name):
        super(StoryElementStatusToBlackboard, self).__init__(name=child.name, child=child)
        self.story_element_type = story_element_type
        self.element_name = element_name
        self.blackboard = py_trees.blackboard.Blackboard()

    def initialise(self):
        """
        Record the elements's start time on the blackboard
        """
        self.blackboard.set(name='({}){}-{}'.format(self.story_element_type.upper(), self.element_name, 'START'), value=GameTime.get_time(), overwrite=True)

    def update(self):
        """
        Reflect the decorated child's status
        Returns: the decorated child's status
        """
        return self.decorated.status

    def terminate(self, new_status):
        """
        Terminate and mark Blackboard entry with END
        """
        rules = []
        if new_status == py_trees.common.Status.INVALID:
            terminating_ancestor = self.parent
            while terminating_ancestor.status == py_trees.common.Status.INVALID:
                terminating_ancestor = terminating_ancestor.parent
            if terminating_ancestor.status == py_trees.common.Status.SUCCESS:
                successful_children = [child.name for child in terminating_ancestor.children if child.status == py_trees.common.Status.SUCCESS]
                if 'StopTrigger' in successful_children:
                    rules.append('END')
        rules = rules or ['END']
        for rule in rules:
            self.blackboard.set(name='({}){}-{}'.format(self.story_element_type.upper(), self.element_name, rule), value=GameTime.get_time(), overwrite=True)

def initialise(self):
    """
        Record the elements's start time on the blackboard
        """
    self.blackboard.set(name='({}){}-{}'.format(self.story_element_type.upper(), self.element_name, 'START'), value=GameTime.get_time(), overwrite=True)

def terminate(self, new_status):
    """
        Terminate and mark Blackboard entry with END
        """
    rules = []
    if new_status == py_trees.common.Status.INVALID:
        terminating_ancestor = self.parent
        while terminating_ancestor.status == py_trees.common.Status.INVALID:
            terminating_ancestor = terminating_ancestor.parent
        if terminating_ancestor.status == py_trees.common.Status.SUCCESS:
            successful_children = [child.name for child in terminating_ancestor.children if child.status == py_trees.common.Status.SUCCESS]
            if 'StopTrigger' in successful_children:
                rules.append('END')
    rules = rules or ['END']
    for rule in rules:
        self.blackboard.set(name='({}){}-{}'.format(self.story_element_type.upper(), self.element_name, rule), value=GameTime.get_time(), overwrite=True)

class ControlLoss(BasicScenario):
    """
    Implementation of "Control Loss Vehicle" (Traffic Scenario 01)

    This is a single ego vehicle scenario
    """

    def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, criteria_enable=True, timeout=60):
        """
        Setup all relevant parameters and create scenario
        """
        self._no_of_jitter = 10
        self._noise_mean = 0
        self._noise_std = 0.01
        self._dynamic_mean_for_steer = 0.001
        self._dynamic_mean_for_throttle = 0.045
        self._abort_distance_to_intersection = 10
        self._current_steer_noise = [0]
        self._current_throttle_noise = [0]
        self._start_distance = 20
        self._trigger_dist = 2
        self._end_distance = 30
        self._ego_vehicle_max_steer = 0.0
        self._ego_vehicle_max_throttle = 1.0
        self._ego_vehicle_target_velocity = 15
        self._map = CarlaDataProvider.get_map()
        self.timeout = timeout
        self._reference_waypoint = self._map.get_waypoint(config.trigger_points[0].location)
        self.loc_list = []
        self.obj = []
        self._randomize = randomize
        super(ControlLoss, self).__init__('ControlLoss', ego_vehicles, config, world, debug_mode, criteria_enable=criteria_enable)

    def _initialize_actors(self, config):
        """
        Custom initialization
        """
        if self._randomize:
            self._distance = random.randint(low=10, high=80, size=3)
            self._distance = sorted(self._distance)
        else:
            self._distance = [14, 48, 74]
        first_loc, _ = get_location_in_distance_from_wp(self._reference_waypoint, self._distance[0])
        second_loc, _ = get_location_in_distance_from_wp(self._reference_waypoint, self._distance[1])
        third_loc, _ = get_location_in_distance_from_wp(self._reference_waypoint, self._distance[2])
        self.loc_list.extend([first_loc, second_loc, third_loc])
        self._dist_prop = [x - 2 for x in self._distance]
        self.first_loc_prev, _ = get_location_in_distance_from_wp(self._reference_waypoint, self._dist_prop[0])
        self.sec_loc_prev, _ = get_location_in_distance_from_wp(self._reference_waypoint, self._dist_prop[1])
        self.third_loc_prev, _ = get_location_in_distance_from_wp(self._reference_waypoint, self._dist_prop[2])
        self.first_transform = carla.Transform(self.first_loc_prev)
        self.sec_transform = carla.Transform(self.sec_loc_prev)
        self.third_transform = carla.Transform(self.third_loc_prev)
        self.first_transform = carla.Transform(carla.Location(self.first_loc_prev.x, self.first_loc_prev.y, self.first_loc_prev.z))
        self.sec_transform = carla.Transform(carla.Location(self.sec_loc_prev.x, self.sec_loc_prev.y, self.sec_loc_prev.z))
        self.third_transform = carla.Transform(carla.Location(self.third_loc_prev.x, self.third_loc_prev.y, self.third_loc_prev.z))
        first_debris = CarlaDataProvider.request_new_actor('static.prop.dirtdebris01', self.first_transform, 'prop')
        second_debris = CarlaDataProvider.request_new_actor('static.prop.dirtdebris01', self.sec_transform, 'prop')
        third_debris = CarlaDataProvider.request_new_actor('static.prop.dirtdebris01', self.third_transform, 'prop')
        first_debris.set_transform(self.first_transform)
        second_debris.set_transform(self.sec_transform)
        third_debris.set_transform(self.third_transform)
        self.obj.extend([first_debris, second_debris, third_debris])
        for debris in self.obj:
            debris.set_simulate_physics(False)
        self.other_actors.append(first_debris)
        self.other_actors.append(second_debris)
        self.other_actors.append(third_debris)

    def _create_behavior(self):
        """
        The scenario defined after is a "control loss vehicle" scenario. After
        invoking this scenario, it will wait until the vehicle drove a few meters
        (_start_distance), and then perform a jitter action. Finally, the vehicle
        has to reach a target point (_end_distance). If this does not happen within
        60 seconds, a timeout stops the scenario
        """
        start_end_parallel = py_trees.composites.Parallel('Jitter', policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)
        start_condition = InTriggerDistanceToLocation(self.ego_vehicles[0], self.first_loc_prev, self._trigger_dist)
        for _ in range(self._no_of_jitter):
            turn = ChangeNoiseParameters(self._current_steer_noise, self._current_throttle_noise, self._noise_mean, self._noise_std, self._dynamic_mean_for_steer, self._dynamic_mean_for_throttle)
        noise_end = ChangeNoiseParameters(self._current_steer_noise, self._current_throttle_noise, 0, 0, 0, 0)
        jitter_action = py_trees.composites.Parallel('Jitter', policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)
        jitter_abort = InTriggerDistanceToNextIntersection(self.ego_vehicles[0], self._abort_distance_to_intersection)
        end_condition = DriveDistance(self.ego_vehicles[0], self._end_distance)
        start_end_parallel.add_child(start_condition)
        start_end_parallel.add_child(end_condition)
        sequence = py_trees.composites.Sequence('ControlLoss')
        sequence.add_child(ActorTransformSetter(self.other_actors[0], self.first_transform, physics=False))
        sequence.add_child(ActorTransformSetter(self.other_actors[1], self.sec_transform, physics=False))
        sequence.add_child(ActorTransformSetter(self.other_actors[2], self.third_transform, physics=False))
        jitter = py_trees.composites.Sequence('Jitter Behavior')
        jitter.add_child(turn)
        jitter.add_child(InTriggerDistanceToLocation(self.ego_vehicles[0], self.sec_loc_prev, self._trigger_dist))
        jitter.add_child(turn)
        jitter.add_child(InTriggerDistanceToLocation(self.ego_vehicles[0], self.third_loc_prev, self._trigger_dist))
        jitter.add_child(turn)
        jitter_action.add_child(jitter)
        jitter_action.add_child(jitter_abort)
        sequence.add_child(start_end_parallel)
        sequence.add_child(jitter_action)
        sequence.add_child(end_condition)
        sequence.add_child(noise_end)
        return sequence

    def _create_test_criteria(self):
        """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
        criteria = []
        collision_criterion = CollisionTest(self.ego_vehicles[0])
        criteria.append(collision_criterion)
        return criteria

    def change_control(self, control):
        """
        This is a function that changes the control based on the scenario determination
        :param control: a carla vehicle control
        :return: a control to be changed by the scenario.
        """
        control.steer += self._current_steer_noise[0]
        control.throttle += self._current_throttle_noise[0]
        return control

    def __del__(self):
        """
        Remove all actors upon deletion
        """
        self.remove_all_actors()

def _create_test_criteria(self):
    """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
    criteria = []
    collision_criterion = CollisionTest(self.ego_vehicles[0])
    criteria.append(collision_criterion)
    return criteria

class OppositeVehicleRunningRedLight(BasicScenario):
    """
    This class holds everything required for a scenario,
    in which an other vehicle takes priority from the ego
    vehicle, by running a red traffic light (while the ego
    vehicle has green) (Traffic Scenario 7)

    This is a single ego vehicle scenario
    """
    _ego_max_velocity_allowed = 20
    _ego_avg_velocity_expected = 4
    _ego_expected_driven_distance = 70
    _ego_distance_to_traffic_light = 32
    _ego_distance_to_drive = 40
    _other_actor_target_velocity = 10
    _other_actor_max_brake = 1.0
    _other_actor_distance = 50
    _traffic_light = None

    def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, criteria_enable=True, timeout=180):
        """
        Setup all relevant parameters and create scenario
        and instantiate scenario manager
        """
        self._other_actor_transform = None
        self.timeout = timeout
        super(OppositeVehicleRunningRedLight, self).__init__('OppositeVehicleRunningRedLight', ego_vehicles, config, world, debug_mode, criteria_enable=criteria_enable)
        self._traffic_light = CarlaDataProvider.get_next_traffic_light(self.ego_vehicles[0], False)
        if self._traffic_light is None:
            print('No traffic light for the given location of the ego vehicle found')
            sys.exit(-1)
        self._traffic_light.set_state(carla.TrafficLightState.Green)
        self._traffic_light.set_green_time(self.timeout)
        traffic_light_other = CarlaDataProvider.get_next_traffic_light(self.other_actors[0], False)
        if traffic_light_other is None:
            print('No traffic light for the given location of the other vehicle found')
            sys.exit(-1)
        traffic_light_other.set_state(carla.TrafficLightState.Red)
        traffic_light_other.set_red_time(self.timeout)

    def _initialize_actors(self, config):
        """
        Custom initialization
        """
        self._other_actor_transform = config.other_actors[0].transform
        first_vehicle_transform = carla.Transform(carla.Location(config.other_actors[0].transform.location.x, config.other_actors[0].transform.location.y, config.other_actors[0].transform.location.z), config.other_actors[0].transform.rotation)
        first_vehicle = CarlaDataProvider.request_new_actor(config.other_actors[0].model, first_vehicle_transform)
        self.other_actors.append(first_vehicle)

    def _create_behavior(self):
        """
        Scenario behavior:
        The other vehicle waits until the ego vehicle is close enough to the
        intersection and that its own traffic light is red. Then, it will start
        driving and 'illegally' cross the intersection. After a short distance
        it should stop again, outside of the intersection. The ego vehicle has
        to avoid the crash, but continue driving after the intersection is clear.

        If this does not happen within 120 seconds, a timeout stops the scenario
        """
        crossing_point_dynamic = get_crossing_point(self.ego_vehicles[0])
        startcondition = InTriggerDistanceToLocation(self.ego_vehicles[0], crossing_point_dynamic, self._ego_distance_to_traffic_light, name='Waiting for start position')
        sync_arrival_parallel = py_trees.composites.Parallel('Synchronize arrival times', policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)
        location_of_collision_dynamic = get_geometric_linear_intersection(self.ego_vehicles[0], self.other_actors[0])
        sync_arrival = SyncArrival(self.other_actors[0], self.ego_vehicles[0], location_of_collision_dynamic)
        sync_arrival_stop = InTriggerDistanceToNextIntersection(self.other_actors[0], 5)
        sync_arrival_parallel.add_child(sync_arrival)
        sync_arrival_parallel.add_child(sync_arrival_stop)
        turn = 0
        plan = []
        plan, target_waypoint = generate_target_waypoint_list(CarlaDataProvider.get_map().get_waypoint(self.other_actors[0].get_location()), turn)
        wp_choice = target_waypoint.next(5.0)
        while len(wp_choice) == 1:
            target_waypoint = wp_choice[0]
            plan.append((target_waypoint, RoadOption.LANEFOLLOW))
            wp_choice = target_waypoint.next(5.0)
        continue_driving = py_trees.composites.Parallel('ContinueDriving', policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)
        continue_driving_waypoints = WaypointFollower(self.other_actors[0], self._other_actor_target_velocity, plan=plan, avoid_collision=False)
        continue_driving_distance = DriveDistance(self.other_actors[0], self._other_actor_distance, name='Distance')
        continue_driving_timeout = TimeOut(10)
        continue_driving.add_child(continue_driving_waypoints)
        continue_driving.add_child(continue_driving_distance)
        continue_driving.add_child(continue_driving_timeout)
        wait = DriveDistance(self.ego_vehicles[0], self._ego_distance_to_drive, name='DriveDistance')
        sequence = py_trees.composites.Sequence('Sequence Behavior')
        sequence.add_child(ActorTransformSetter(self.other_actors[0], self._other_actor_transform))
        sequence.add_child(startcondition)
        sequence.add_child(sync_arrival_parallel)
        sequence.add_child(continue_driving)
        sequence.add_child(wait)
        sequence.add_child(ActorDestroy(self.other_actors[0]))
        return sequence

    def _create_test_criteria(self):
        """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
        criteria = []
        max_velocity_criterion = MaxVelocityTest(self.ego_vehicles[0], self._ego_max_velocity_allowed, optional=True)
        collision_criterion = CollisionTest(self.ego_vehicles[0])
        driven_distance_criterion = DrivenDistanceTest(self.ego_vehicles[0], self._ego_expected_driven_distance)
        criteria.append(max_velocity_criterion)
        criteria.append(collision_criterion)
        criteria.append(driven_distance_criterion)
        for vehicle in self.other_actors:
            collision_criterion = CollisionTest(vehicle)
            criteria.append(collision_criterion)
        return criteria

    def __del__(self):
        """
        Remove all actors and traffic lights upon deletion
        """
        self._traffic_light = None
        self.remove_all_actors()

def _create_test_criteria(self):
    """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
    criteria = []
    max_velocity_criterion = MaxVelocityTest(self.ego_vehicles[0], self._ego_max_velocity_allowed, optional=True)
    collision_criterion = CollisionTest(self.ego_vehicles[0])
    driven_distance_criterion = DrivenDistanceTest(self.ego_vehicles[0], self._ego_expected_driven_distance)
    criteria.append(max_velocity_criterion)
    criteria.append(collision_criterion)
    criteria.append(driven_distance_criterion)
    for vehicle in self.other_actors:
        collision_criterion = CollisionTest(vehicle)
        criteria.append(collision_criterion)
    return criteria

class VehicleTurningRight(BasicScenario):
    """
    This class holds everything required for a simple object crash
    with prior vehicle action involving a vehicle and a cyclist.
    The ego vehicle is passing through a road and encounters
    a cyclist after taking a right turn. (Traffic Scenario 4)

    This is a single ego vehicle scenario
    """

    def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, criteria_enable=True, timeout=60):
        """
        Setup all relevant parameters and create scenario
        """
        self._other_actor_target_velocity = 10
        self._wmap = CarlaDataProvider.get_map()
        self._reference_waypoint = self._wmap.get_waypoint(config.trigger_points[0].location)
        self._trigger_location = config.trigger_points[0].location
        self._other_actor_transform = None
        self._num_lane_changes = 0
        self.timeout = timeout
        self._number_of_attempts = 6
        self._spawn_attempted = 0
        self._ego_route = CarlaDataProvider.get_ego_vehicle_route()
        super(VehicleTurningRight, self).__init__('VehicleTurningRight', ego_vehicles, config, world, debug_mode, criteria_enable=criteria_enable)

    def _initialize_actors(self, config):
        """
        Custom initialization
        """
        waypoint = generate_target_waypoint(self._reference_waypoint, 1)
        start_distance = 8
        waypoint = waypoint.next(start_distance)[0]
        waypoint, self._num_lane_changes = get_right_driving_lane(waypoint)
        added_dist = self._num_lane_changes
        while True:
            try:
                self._other_actor_transform = get_opponent_transform(added_dist, waypoint, self._trigger_location)
                first_vehicle = CarlaDataProvider.request_new_actor('vehicle.diamondback.century', self._other_actor_transform)
                first_vehicle.set_simulate_physics(enabled=False)
                break
            except RuntimeError as r:
                print(' Base transform is blocking objects ', self._other_actor_transform)
                added_dist += 0.5
                self._spawn_attempted += 1
                if self._spawn_attempted >= self._number_of_attempts:
                    raise r
        actor_transform = carla.Transform(carla.Location(self._other_actor_transform.location.x, self._other_actor_transform.location.y, self._other_actor_transform.location.z - 500), self._other_actor_transform.rotation)
        first_vehicle.set_transform(actor_transform)
        first_vehicle.set_simulate_physics(enabled=False)
        self.other_actors.append(first_vehicle)

    def _create_behavior(self):
        """
        After invoking this scenario, cyclist will wait for the user
        controlled vehicle to enter the in the trigger distance region,
        the cyclist starts crossing the road once the condition meets,
        ego vehicle has to avoid the crash after a right turn, but
        continue driving after the road is clear.If this does not happen
        within 90 seconds, a timeout stops the scenario.
        """
        root = py_trees.composites.Parallel(policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE, name='IntersectionRightTurn')
        lane_width = self._reference_waypoint.lane_width
        dist_to_travel = lane_width + 1.1 * lane_width * self._num_lane_changes
        bycicle_start_dist = 13 + dist_to_travel
        if self._ego_route is not None:
            trigger_distance = InTriggerDistanceToLocationAlongRoute(self.ego_vehicles[0], self._ego_route, self._other_actor_transform.location, bycicle_start_dist)
        else:
            trigger_distance = InTriggerDistanceToVehicle(self.other_actors[0], self.ego_vehicles[0], bycicle_start_dist)
        actor_velocity = KeepVelocity(self.other_actors[0], self._other_actor_target_velocity)
        actor_traverse = DriveDistance(self.other_actors[0], 0.3 * dist_to_travel)
        post_timer_velocity_actor = KeepVelocity(self.other_actors[0], self._other_actor_target_velocity)
        post_timer_traverse_actor = DriveDistance(self.other_actors[0], 0.7 * dist_to_travel)
        end_condition = TimeOut(5)
        scenario_sequence = py_trees.composites.Sequence()
        actor_ego_sync = py_trees.composites.Parallel('Synchronization of actor and ego vehicle', policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)
        after_timer_actor = py_trees.composites.Parallel('After timeout actor will cross the remaining lane_width', policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)
        root.add_child(scenario_sequence)
        scenario_sequence.add_child(ActorTransformSetter(self.other_actors[0], self._other_actor_transform, name='TransformSetterTS4'))
        scenario_sequence.add_child(HandBrakeVehicle(self.other_actors[0], True))
        scenario_sequence.add_child(trigger_distance)
        scenario_sequence.add_child(HandBrakeVehicle(self.other_actors[0], False))
        scenario_sequence.add_child(actor_ego_sync)
        scenario_sequence.add_child(after_timer_actor)
        scenario_sequence.add_child(end_condition)
        scenario_sequence.add_child(ActorDestroy(self.other_actors[0]))
        actor_ego_sync.add_child(actor_velocity)
        actor_ego_sync.add_child(actor_traverse)
        after_timer_actor.add_child(post_timer_velocity_actor)
        after_timer_actor.add_child(post_timer_traverse_actor)
        return root

    def _create_test_criteria(self):
        """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
        criteria = []
        collision_criterion = CollisionTest(self.ego_vehicles[0])
        criteria.append(collision_criterion)
        return criteria

    def __del__(self):
        """
        Remove all actors upon deletion
        """
        self.remove_all_actors()

def _create_test_criteria(self):
    """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
    criteria = []
    collision_criterion = CollisionTest(self.ego_vehicles[0])
    criteria.append(collision_criterion)
    return criteria

class VehicleTurningLeft(BasicScenario):
    """
    This class holds everything required for a simple object crash
    with prior vehicle action involving a vehicle and a cyclist.
    The ego vehicle is passing through a road and encounters
    a cyclist after taking a left turn. (Traffic Scenario 4)

    This is a single ego vehicle scenario
    """

    def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, criteria_enable=True, timeout=60):
        """
        Setup all relevant parameters and create scenario
        """
        self._other_actor_target_velocity = 10
        self._wmap = CarlaDataProvider.get_map()
        self._reference_waypoint = self._wmap.get_waypoint(config.trigger_points[0].location)
        self._trigger_location = config.trigger_points[0].location
        self._other_actor_transform = None
        self._num_lane_changes = 0
        self.timeout = timeout
        self._number_of_attempts = 6
        self._spawn_attempted = 0
        self._ego_route = CarlaDataProvider.get_ego_vehicle_route()
        super(VehicleTurningLeft, self).__init__('VehicleTurningLeft', ego_vehicles, config, world, debug_mode, criteria_enable=criteria_enable)

    def _initialize_actors(self, config):
        """
        Custom initialization
        """
        waypoint = generate_target_waypoint(self._reference_waypoint, -1)
        start_distance = 8
        waypoint = waypoint.next(start_distance)[0]
        waypoint, self._num_lane_changes = get_right_driving_lane(waypoint)
        added_dist = self._num_lane_changes
        while True:
            try:
                self._other_actor_transform = get_opponent_transform(added_dist, waypoint, self._trigger_location)
                first_vehicle = CarlaDataProvider.request_new_actor('vehicle.diamondback.century', self._other_actor_transform)
                first_vehicle.set_simulate_physics(enabled=False)
                break
            except RuntimeError as r:
                print(' Base transform is blocking objects ', self._other_actor_transform)
                added_dist += 0.5
                self._spawn_attempted += 1
                if self._spawn_attempted >= self._number_of_attempts:
                    raise r
        actor_transform = carla.Transform(carla.Location(self._other_actor_transform.location.x, self._other_actor_transform.location.y, self._other_actor_transform.location.z - 500), self._other_actor_transform.rotation)
        first_vehicle.set_transform(actor_transform)
        first_vehicle.set_simulate_physics(enabled=False)
        self.other_actors.append(first_vehicle)

    def _create_behavior(self):
        """
        After invoking this scenario, cyclist will wait for the user
        controlled vehicle to enter the in the trigger distance region,
        the cyclist starts crossing the road once the condition meets,
        ego vehicle has to avoid the crash after a left turn, but
        continue driving after the road is clear.If this does not happen
        within 90 seconds, a timeout stops the scenario.
        """
        root = py_trees.composites.Parallel(policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE, name='IntersectionLeftTurn')
        lane_width = self._reference_waypoint.lane_width
        dist_to_travel = lane_width + 1.1 * lane_width * self._num_lane_changes
        bycicle_start_dist = 13 + dist_to_travel
        if self._ego_route is not None:
            trigger_distance = InTriggerDistanceToLocationAlongRoute(self.ego_vehicles[0], self._ego_route, self._other_actor_transform.location, bycicle_start_dist)
        else:
            trigger_distance = InTriggerDistanceToVehicle(self.other_actors[0], self.ego_vehicles[0], bycicle_start_dist)
        actor_velocity = KeepVelocity(self.other_actors[0], self._other_actor_target_velocity)
        actor_traverse = DriveDistance(self.other_actors[0], 0.3 * dist_to_travel)
        post_timer_velocity_actor = KeepVelocity(self.other_actors[0], self._other_actor_target_velocity)
        post_timer_traverse_actor = DriveDistance(self.other_actors[0], 0.7 * dist_to_travel)
        end_condition = TimeOut(5)
        scenario_sequence = py_trees.composites.Sequence()
        actor_ego_sync = py_trees.composites.Parallel('Synchronization of actor and ego vehicle', policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)
        after_timer_actor = py_trees.composites.Parallel('After timeout actor will cross the remaining lane_width', policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)
        root.add_child(scenario_sequence)
        scenario_sequence.add_child(ActorTransformSetter(self.other_actors[0], self._other_actor_transform, name='TransformSetterTS4'))
        scenario_sequence.add_child(HandBrakeVehicle(self.other_actors[0], True))
        scenario_sequence.add_child(trigger_distance)
        scenario_sequence.add_child(HandBrakeVehicle(self.other_actors[0], False))
        scenario_sequence.add_child(actor_ego_sync)
        scenario_sequence.add_child(after_timer_actor)
        scenario_sequence.add_child(end_condition)
        scenario_sequence.add_child(ActorDestroy(self.other_actors[0]))
        actor_ego_sync.add_child(actor_velocity)
        actor_ego_sync.add_child(actor_traverse)
        after_timer_actor.add_child(post_timer_velocity_actor)
        after_timer_actor.add_child(post_timer_traverse_actor)
        return root

    def _create_test_criteria(self):
        """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
        criteria = []
        collision_criterion = CollisionTest(self.ego_vehicles[0])
        criteria.append(collision_criterion)
        return criteria

    def __del__(self):
        """
        Remove all actors upon deletion
        """
        self.remove_all_actors()

def _create_test_criteria(self):
    """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
    criteria = []
    collision_criterion = CollisionTest(self.ego_vehicles[0])
    criteria.append(collision_criterion)
    return criteria

class VehicleTurningRoute(BasicScenario):
    """
    This class holds everything required for a simple object crash
    with prior vehicle action involving a vehicle and a cyclist.
    The ego vehicle is passing through a road and encounters
    a cyclist after taking a turn. This is the version used when the ego vehicle
    is following a given route. (Traffic Scenario 4)

    This is a single ego vehicle scenario
    """

    def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, criteria_enable=True, timeout=60):
        """
        Setup all relevant parameters and create scenario
        """
        self._other_actor_target_velocity = 10
        self._wmap = CarlaDataProvider.get_map()
        self._reference_waypoint = self._wmap.get_waypoint(config.trigger_points[0].location)
        self._trigger_location = config.trigger_points[0].location
        self._other_actor_transform = None
        self._num_lane_changes = 0
        self.timeout = timeout
        self._number_of_attempts = 6
        self._spawn_attempted = 0
        self._ego_route = CarlaDataProvider.get_ego_vehicle_route()
        super(VehicleTurningRoute, self).__init__('VehicleTurningRoute', ego_vehicles, config, world, debug_mode, criteria_enable=criteria_enable)

    def _initialize_actors(self, config):
        """
        Custom initialization
        """
        waypoint = generate_target_waypoint_in_route(self._reference_waypoint, self._ego_route)
        start_distance = 8
        waypoint = waypoint.next(start_distance)[0]
        waypoint, self._num_lane_changes = get_right_driving_lane(waypoint)
        added_dist = self._num_lane_changes
        while True:
            try:
                self._other_actor_transform = get_opponent_transform(added_dist, waypoint, self._trigger_location)
                first_vehicle = CarlaDataProvider.request_new_actor('vehicle.diamondback.century', self._other_actor_transform)
                first_vehicle.set_simulate_physics(enabled=False)
                break
            except RuntimeError as r:
                print(' Base transform is blocking objects ', self._other_actor_transform)
                added_dist += 0.5
                self._spawn_attempted += 1
                if self._spawn_attempted >= self._number_of_attempts:
                    raise r
        actor_transform = carla.Transform(carla.Location(self._other_actor_transform.location.x, self._other_actor_transform.location.y, self._other_actor_transform.location.z - 500), self._other_actor_transform.rotation)
        first_vehicle.set_transform(actor_transform)
        first_vehicle.set_simulate_physics(enabled=False)
        self.other_actors.append(first_vehicle)

    def _create_behavior(self):
        """
        After invoking this scenario, cyclist will wait for the user
        controlled vehicle to enter the in the trigger distance region,
        the cyclist starts crossing the road once the condition meets,
        ego vehicle has to avoid the crash after a turn, but
        continue driving after the road is clear.If this does not happen
        within 90 seconds, a timeout stops the scenario.
        """
        root = py_trees.composites.Parallel(policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE, name='IntersectionRouteTurn')
        lane_width = self._reference_waypoint.lane_width
        dist_to_travel = lane_width + 1.1 * lane_width * self._num_lane_changes
        bycicle_start_dist = 13 + dist_to_travel
        if self._ego_route is not None:
            trigger_distance = InTriggerDistanceToLocationAlongRoute(self.ego_vehicles[0], self._ego_route, self._other_actor_transform.location, bycicle_start_dist)
        else:
            trigger_distance = InTriggerDistanceToVehicle(self.other_actors[0], self.ego_vehicles[0], bycicle_start_dist)
        actor_velocity = KeepVelocity(self.other_actors[0], self._other_actor_target_velocity)
        actor_traverse = DriveDistance(self.other_actors[0], 0.3 * dist_to_travel)
        post_timer_velocity_actor = KeepVelocity(self.other_actors[0], self._other_actor_target_velocity)
        post_timer_traverse_actor = DriveDistance(self.other_actors[0], 0.7 * dist_to_travel)
        end_condition = TimeOut(5)
        scenario_sequence = py_trees.composites.Sequence()
        actor_ego_sync = py_trees.composites.Parallel('Synchronization of actor and ego vehicle', policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)
        after_timer_actor = py_trees.composites.Parallel('After timeout actor will cross the remaining lane_width', policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)
        root.add_child(scenario_sequence)
        scenario_sequence.add_child(ActorTransformSetter(self.other_actors[0], self._other_actor_transform, name='TransformSetterTS4'))
        scenario_sequence.add_child(HandBrakeVehicle(self.other_actors[0], True))
        scenario_sequence.add_child(trigger_distance)
        scenario_sequence.add_child(HandBrakeVehicle(self.other_actors[0], False))
        scenario_sequence.add_child(actor_ego_sync)
        scenario_sequence.add_child(after_timer_actor)
        scenario_sequence.add_child(end_condition)
        scenario_sequence.add_child(ActorDestroy(self.other_actors[0]))
        actor_ego_sync.add_child(actor_velocity)
        actor_ego_sync.add_child(actor_traverse)
        after_timer_actor.add_child(post_timer_velocity_actor)
        after_timer_actor.add_child(post_timer_traverse_actor)
        return root

    def _create_test_criteria(self):
        """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
        criteria = []
        collision_criterion = CollisionTest(self.ego_vehicles[0])
        criteria.append(collision_criterion)
        return criteria

    def __del__(self):
        """
        Remove all actors upon deletion
        """
        self.remove_all_actors()

def _create_test_criteria(self):
    """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
    criteria = []
    collision_criterion = CollisionTest(self.ego_vehicles[0])
    criteria.append(collision_criterion)
    return criteria

class ManeuverOppositeDirection(BasicScenario):
    """
    "Vehicle Maneuvering In Opposite Direction" (Traffic Scenario 06)

    This is a single ego vehicle scenario
    """

    def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, criteria_enable=True, obstacle_type='barrier', timeout=120):
        """
        Setup all relevant parameters and create scenario
        obstacle_type -> flag to select type of leading obstacle. Values: vehicle, barrier
        """
        self._world = world
        self._map = CarlaDataProvider.get_map()
        self._first_vehicle_location = 50
        self._second_vehicle_location = self._first_vehicle_location + 60
        self._ego_vehicle_drive_distance = self._second_vehicle_location * 2
        self._start_distance = self._first_vehicle_location * 0.9
        self._opposite_speed = 5.56
        self._source_gap = 40
        self._reference_waypoint = self._map.get_waypoint(config.trigger_points[0].location)
        self._source_transform = None
        self._sink_location = None
        self._blackboard_queue_name = 'ManeuverOppositeDirection/actor_flow_queue'
        self._queue = py_trees.blackboard.Blackboard().set(self._blackboard_queue_name, Queue())
        self._obstacle_type = obstacle_type
        self._first_actor_transform = None
        self._second_actor_transform = None
        self._third_actor_transform = None
        self.timeout = timeout
        super(ManeuverOppositeDirection, self).__init__('ManeuverOppositeDirection', ego_vehicles, config, world, debug_mode, criteria_enable=criteria_enable)

    def _initialize_actors(self, config):
        """
        Custom initialization
        """
        first_actor_waypoint, _ = get_waypoint_in_distance(self._reference_waypoint, self._first_vehicle_location)
        second_actor_waypoint, _ = get_waypoint_in_distance(self._reference_waypoint, self._second_vehicle_location)
        second_actor_waypoint = second_actor_waypoint.get_left_lane()
        first_actor_transform = carla.Transform(first_actor_waypoint.transform.location, first_actor_waypoint.transform.rotation)
        if self._obstacle_type == 'vehicle':
            first_actor_model = 'vehicle.nissan.micra'
        else:
            first_actor_transform.rotation.yaw += 90
            first_actor_model = 'static.prop.streetbarrier'
            second_prop_waypoint = first_actor_waypoint.next(2.0)[0]
            position_yaw = second_prop_waypoint.transform.rotation.yaw + 90
            offset_location = carla.Location(0.5 * second_prop_waypoint.lane_width * math.cos(math.radians(position_yaw)), 0.5 * second_prop_waypoint.lane_width * math.sin(math.radians(position_yaw)))
            second_prop_transform = carla.Transform(second_prop_waypoint.transform.location + offset_location, first_actor_transform.rotation)
            second_prop_actor = CarlaDataProvider.request_new_actor(first_actor_model, second_prop_transform)
            second_prop_actor.set_simulate_physics(True)
        first_actor = CarlaDataProvider.request_new_actor(first_actor_model, first_actor_transform)
        first_actor.set_simulate_physics(True)
        second_actor = CarlaDataProvider.request_new_actor('vehicle.audi.tt', second_actor_waypoint.transform)
        self.other_actors.append(first_actor)
        self.other_actors.append(second_actor)
        if self._obstacle_type != 'vehicle':
            self.other_actors.append(second_prop_actor)
        self._source_transform = second_actor_waypoint.transform
        sink_waypoint = second_actor_waypoint.next(1)[0]
        while not sink_waypoint.is_intersection:
            sink_waypoint = sink_waypoint.next(1)[0]
        self._sink_location = sink_waypoint.transform.location
        self._first_actor_transform = first_actor_transform
        self._second_actor_transform = second_actor_waypoint.transform
        self._third_actor_transform = second_prop_transform

    def _create_behavior(self):
        """
        The behavior tree returned by this method is as follows:
        The ego vehicle is trying to pass a leading vehicle in the same lane
        by moving onto the oncoming lane while another vehicle is moving in the
        opposite direction in the oncoming lane.
        """
        actor_source = ActorSource(['vehicle.audi.tt', 'vehicle.tesla.model3', 'vehicle.nissan.micra'], self._source_transform, self._source_gap, self._blackboard_queue_name)
        actor_sink = ActorSink(self._sink_location, 10)
        ego_drive_distance = DriveDistance(self.ego_vehicles[0], self._ego_vehicle_drive_distance)
        waypoint_follower = WaypointFollower(self.other_actors[1], self._opposite_speed, blackboard_queue_name=self._blackboard_queue_name, avoid_collision=True)
        parallel_root = py_trees.composites.Parallel(policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)
        parallel_root.add_child(ego_drive_distance)
        parallel_root.add_child(actor_source)
        parallel_root.add_child(actor_sink)
        parallel_root.add_child(waypoint_follower)
        scenario_sequence = py_trees.composites.Sequence()
        scenario_sequence.add_child(ActorTransformSetter(self.other_actors[0], self._first_actor_transform))
        scenario_sequence.add_child(ActorTransformSetter(self.other_actors[1], self._second_actor_transform))
        scenario_sequence.add_child(ActorTransformSetter(self.other_actors[2], self._third_actor_transform))
        scenario_sequence.add_child(parallel_root)
        scenario_sequence.add_child(ActorDestroy(self.other_actors[0]))
        scenario_sequence.add_child(ActorDestroy(self.other_actors[1]))
        scenario_sequence.add_child(ActorDestroy(self.other_actors[2]))
        return scenario_sequence

    def _create_test_criteria(self):
        """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
        criteria = []
        collision_criterion = CollisionTest(self.ego_vehicles[0])
        criteria.append(collision_criterion)
        return criteria

    def __del__(self):
        """
        Remove all actors upon deletion
        """
        self.remove_all_actors()

def _create_test_criteria(self):
    """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
    criteria = []
    collision_criterion = CollisionTest(self.ego_vehicles[0])
    criteria.append(collision_criterion)
    return criteria

class BackgroundActivity(BasicScenario):
    """
    Implementation of a scenario to spawn a set of background actors,
    and to remove traffic jams in background traffic

    This is a single ego vehicle scenario
    """
    town_amount = {'Town01': 120, 'Town02': 100, 'Town03': 120, 'Town04': 200, 'Town05': 120, 'Town06': 150, 'Town07': 110, 'Town08': 180, 'Town09': 300, 'Town10': 120}

    def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, timeout=35 * 60):
        """
        Setup all relevant parameters and create scenario
        """
        self.config = config
        self.debug = debug_mode
        self.timeout = timeout
        super(BackgroundActivity, self).__init__('BackgroundActivity', ego_vehicles, config, world, debug_mode, terminate_on_failure=True, criteria_enable=True)

    def _initialize_actors(self, config):
        town_name = config.town
        if town_name in self.town_amount:
            amount = self.town_amount[town_name]
        else:
            amount = 0
        new_actors = CarlaDataProvider.request_new_batch_actors('vehicle.*', amount, carla.Transform(), autopilot=True, random_location=True, rolename='background')
        if new_actors is None:
            raise Exception('Error: Unable to add the background activity, all spawn points were occupied')
        for _actor in new_actors:
            self.other_actors.append(_actor)

    def _create_behavior(self):
        """
        Basic behavior do nothing, i.e. Idle
        """
        pass

    def _create_test_criteria(self):
        """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
        pass

    def __del__(self):
        """
        Remove all actors upon deletion
        """
        self.remove_all_actors()

def _initialize_actors(self, config):
    town_name = config.town
    if town_name in self.town_amount:
        amount = self.town_amount[town_name]
    else:
        amount = 0
    new_actors = CarlaDataProvider.request_new_batch_actors('vehicle.*', amount, carla.Transform(), autopilot=True, random_location=True, rolename='background')
    if new_actors is None:
        raise Exception('Error: Unable to add the background activity, all spawn points were occupied')
    for _actor in new_actors:
        self.other_actors.append(_actor)

class ChangeLane(BasicScenario):
    """
    This class holds everything required for a "change lane" scenario involving three vehicles.
    There are two vehicles driving in the same direction on the highway: A fast car and a slow car in front.
    The fast car will change the lane, when it is close to the slow car.

    The ego vehicle is driving right behind the fast car.

    This is a single ego vehicle scenario
    """
    timeout = 1200

    def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, criteria_enable=True, timeout=600):
        """
        Setup all relevant parameters and create scenario

        If randomize is True, the scenario parameters are randomized
        """
        self.timeout = timeout
        self._map = CarlaDataProvider.get_map()
        self._reference_waypoint = self._map.get_waypoint(config.trigger_points[0].location)
        self._fast_vehicle_velocity = 70
        self._slow_vehicle_velocity = 0
        self._change_lane_velocity = 15
        self._slow_vehicle_distance = 100
        self._fast_vehicle_distance = 20
        self._trigger_distance = 30
        self._max_brake = 1
        self.direction = 'left'
        self.lane_check = 'true'
        super(ChangeLane, self).__init__('ChangeLane', ego_vehicles, config, world, debug_mode, criteria_enable=criteria_enable)
        if randomize:
            self._fast_vehicle_distance = random.randint(10, 51)
            self._fast_vehicle_velocity = random.randint(100, 201)
            self._slow_vehicle_velocity = random.randint(1, 6)

    def _initialize_actors(self, config):
        for actor in config.other_actors:
            vehicle = CarlaDataProvider.request_new_actor(actor.model, actor.transform)
            self.other_actors.append(vehicle)
            vehicle.set_simulate_physics(enabled=False)
        fast_car_waypoint, _ = get_waypoint_in_distance(self._reference_waypoint, self._fast_vehicle_distance)
        self.fast_car_visible = carla.Transform(carla.Location(fast_car_waypoint.transform.location.x, fast_car_waypoint.transform.location.y, fast_car_waypoint.transform.location.z + 1), fast_car_waypoint.transform.rotation)
        slow_car_waypoint, _ = get_waypoint_in_distance(self._reference_waypoint, self._slow_vehicle_distance)
        self.slow_car_visible = carla.Transform(carla.Location(slow_car_waypoint.transform.location.x, slow_car_waypoint.transform.location.y, slow_car_waypoint.transform.location.z), slow_car_waypoint.transform.rotation)

    def _create_behavior(self):
        sequence_vw = py_trees.composites.Sequence('VW T2')
        vw_visible = ActorTransformSetter(self.other_actors[1], self.slow_car_visible)
        sequence_vw.add_child(vw_visible)
        brake = StopVehicle(self.other_actors[1], self._max_brake)
        sequence_vw.add_child(brake)
        sequence_vw.add_child(Idle())
        sequence_tesla = py_trees.composites.Sequence('Tesla')
        tesla_visible = ActorTransformSetter(self.other_actors[0], self.fast_car_visible)
        sequence_tesla.add_child(tesla_visible)
        just_drive = py_trees.composites.Parallel('DrivingTowardsSlowVehicle', policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)
        tesla_driving_fast = WaypointFollower(self.other_actors[0], self._fast_vehicle_velocity)
        just_drive.add_child(tesla_driving_fast)
        distance_to_vehicle = InTriggerDistanceToVehicle(self.other_actors[1], self.other_actors[0], self._trigger_distance)
        just_drive.add_child(distance_to_vehicle)
        sequence_tesla.add_child(just_drive)
        lane_change_atomic = LaneChange(self.other_actors[0], distance_other_lane=200)
        sequence_tesla.add_child(lane_change_atomic)
        sequence_tesla.add_child(Idle())
        endcondition = py_trees.composites.Parallel('Waiting for end position of ego vehicle', policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ALL)
        endcondition_part1 = InTriggerDistanceToVehicle(self.other_actors[1], self.ego_vehicles[0], distance=20, name='FinalDistance')
        endcondition_part2 = StandStill(self.ego_vehicles[0], name='FinalSpeed')
        endcondition.add_child(endcondition_part1)
        endcondition.add_child(endcondition_part2)
        root = py_trees.composites.Parallel('Parallel Behavior', policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)
        root.add_child(sequence_vw)
        root.add_child(sequence_tesla)
        root.add_child(endcondition)
        return root

    def _create_test_criteria(self):
        """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
        criteria = []
        collision_criterion = CollisionTest(self.ego_vehicles[0])
        criteria.append(collision_criterion)
        return criteria

    def __del__(self):
        """
        Remove all actors upon deletion
        """
        self.remove_all_actors()

def _create_test_criteria(self):
    """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
    criteria = []
    collision_criterion = CollisionTest(self.ego_vehicles[0])
    criteria.append(collision_criterion)
    return criteria

class NoSignalJunctionCrossing(BasicScenario):
    """
    Implementation class for
    'Non-signalized junctions: crossing negotiation' scenario,
    (Traffic Scenario 10).

    This is a single ego vehicle scenario
    """
    _ego_vehicle_max_velocity = 20
    _ego_vehicle_driven_distance = 105
    _other_actor_max_brake = 1.0
    _other_actor_target_velocity = 15

    def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, criteria_enable=True, timeout=60):
        """
        Setup all relevant parameters and create scenario
        """
        self._other_actor_transform = None
        self.timeout = timeout
        super(NoSignalJunctionCrossing, self).__init__('NoSignalJunctionCrossing', ego_vehicles, config, world, debug_mode, criteria_enable=criteria_enable)

    def _initialize_actors(self, config):
        """
        Custom initialization
        """
        self._other_actor_transform = config.other_actors[0].transform
        first_vehicle_transform = carla.Transform(carla.Location(config.other_actors[0].transform.location.x, config.other_actors[0].transform.location.y, config.other_actors[0].transform.location.z - 500), config.other_actors[0].transform.rotation)
        first_vehicle = CarlaDataProvider.request_new_actor(config.other_actors[0].model, first_vehicle_transform)
        first_vehicle.set_simulate_physics(enabled=False)
        self.other_actors.append(first_vehicle)

    def _create_behavior(self):
        """
        After invoking this scenario, it will wait for the user
        controlled vehicle to enter the start region,
        then make a traffic participant to accelerate
        until it is going fast enough to reach an intersection point.
        at the same time as the user controlled vehicle at the junction.
        Once the user controlled vehicle comes close to the junction,
        the traffic participant accelerates and passes through the junction.
        After 60 seconds, a timeout stops the scenario.
        """
        start_other_trigger = InTriggerRegion(self.ego_vehicles[0], -80, -70, -75, -60)
        sync_arrival = SyncArrival(self.other_actors[0], self.ego_vehicles[0], carla.Location(x=-74.63, y=-136.34))
        pass_through_trigger = InTriggerRegion(self.ego_vehicles[0], -90, -70, -124, -119)
        keep_velocity_other = KeepVelocity(self.other_actors[0], self._other_actor_target_velocity)
        stop_other_trigger = InTriggerRegion(self.other_actors[0], -45, -35, -140, -130)
        stop_other = StopVehicle(self.other_actors[0], self._other_actor_max_brake)
        end_condition = InTriggerRegion(self.ego_vehicles[0], -90, -70, -170, -156)
        root = py_trees.composites.Sequence()
        scenario_sequence = py_trees.composites.Sequence()
        sync_arrival_parallel = py_trees.composites.Parallel(policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)
        keep_velocity_other_parallel = py_trees.composites.Parallel(policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)
        root.add_child(scenario_sequence)
        scenario_sequence.add_child(ActorTransformSetter(self.other_actors[0], self._other_actor_transform))
        scenario_sequence.add_child(start_other_trigger)
        scenario_sequence.add_child(sync_arrival_parallel)
        scenario_sequence.add_child(keep_velocity_other_parallel)
        scenario_sequence.add_child(stop_other)
        scenario_sequence.add_child(end_condition)
        scenario_sequence.add_child(ActorDestroy(self.other_actors[0]))
        sync_arrival_parallel.add_child(sync_arrival)
        sync_arrival_parallel.add_child(pass_through_trigger)
        keep_velocity_other_parallel.add_child(keep_velocity_other)
        keep_velocity_other_parallel.add_child(stop_other_trigger)
        return root

    def _create_test_criteria(self):
        """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
        criteria = []
        collison_criteria = CollisionTest(self.ego_vehicles[0])
        criteria.append(collison_criteria)
        return criteria

    def __del__(self):
        """
        Remove all actors upon deletion
        """
        self.remove_all_actors()

def _create_test_criteria(self):
    """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
    criteria = []
    collison_criteria = CollisionTest(self.ego_vehicles[0])
    criteria.append(collison_criteria)
    return criteria

class FollowLeadingVehicle(BasicScenario):
    """
    This class holds everything required for a simple "Follow a leading vehicle"
    scenario involving two vehicles.  (Traffic Scenario 2)

    This is a single ego vehicle scenario
    """
    timeout = 120

    def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, criteria_enable=True, timeout=60):
        """
        Setup all relevant parameters and create scenario

        If randomize is True, the scenario parameters are randomized
        """
        self._map = CarlaDataProvider.get_map()
        self._first_vehicle_location = 25
        self._first_vehicle_speed = 10
        self._reference_waypoint = self._map.get_waypoint(config.trigger_points[0].location)
        self._other_actor_max_brake = 1.0
        self._other_actor_stop_in_front_intersection = 20
        self._other_actor_transform = None
        self.timeout = timeout
        super(FollowLeadingVehicle, self).__init__('FollowVehicle', ego_vehicles, config, world, debug_mode, criteria_enable=criteria_enable)
        if randomize:
            self._ego_other_distance_start = random.randint(4, 8)

    def _initialize_actors(self, config):
        """
        Custom initialization
        """
        first_vehicle_waypoint, _ = get_waypoint_in_distance(self._reference_waypoint, self._first_vehicle_location)
        self._other_actor_transform = carla.Transform(carla.Location(first_vehicle_waypoint.transform.location.x, first_vehicle_waypoint.transform.location.y, first_vehicle_waypoint.transform.location.z + 1), first_vehicle_waypoint.transform.rotation)
        first_vehicle_transform = carla.Transform(carla.Location(self._other_actor_transform.location.x, self._other_actor_transform.location.y, self._other_actor_transform.location.z - 500), self._other_actor_transform.rotation)
        first_vehicle = CarlaDataProvider.request_new_actor('vehicle.nissan.patrol', first_vehicle_transform)
        first_vehicle.set_simulate_physics(enabled=False)
        self.other_actors.append(first_vehicle)

    def _create_behavior(self):
        """
        The scenario defined after is a "follow leading vehicle" scenario. After
        invoking this scenario, it will wait for the user controlled vehicle to
        enter the start region, then make the other actor to drive until reaching
        the next intersection. Finally, the user-controlled vehicle has to be close
        enough to the other actor to end the scenario.
        If this does not happen within 60 seconds, a timeout stops the scenario
        """
        start_transform = ActorTransformSetter(self.other_actors[0], self._other_actor_transform)
        driving_to_next_intersection = py_trees.composites.Parallel('DrivingTowardsIntersection', policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)
        driving_to_next_intersection.add_child(WaypointFollower(self.other_actors[0], self._first_vehicle_speed))
        driving_to_next_intersection.add_child(InTriggerDistanceToNextIntersection(self.other_actors[0], self._other_actor_stop_in_front_intersection))
        stop = StopVehicle(self.other_actors[0], self._other_actor_max_brake)
        endcondition = py_trees.composites.Parallel('Waiting for end position', policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ALL)
        endcondition_part1 = InTriggerDistanceToVehicle(self.other_actors[0], self.ego_vehicles[0], distance=20, name='FinalDistance')
        endcondition_part2 = StandStill(self.ego_vehicles[0], name='StandStill', duration=1)
        endcondition.add_child(endcondition_part1)
        endcondition.add_child(endcondition_part2)
        sequence = py_trees.composites.Sequence('Sequence Behavior')
        sequence.add_child(start_transform)
        sequence.add_child(driving_to_next_intersection)
        sequence.add_child(stop)
        sequence.add_child(endcondition)
        sequence.add_child(ActorDestroy(self.other_actors[0]))
        return sequence

    def _create_test_criteria(self):
        """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
        criteria = []
        collision_criterion = CollisionTest(self.ego_vehicles[0])
        criteria.append(collision_criterion)
        return criteria

    def __del__(self):
        """
        Remove all actors upon deletion
        """
        self.remove_all_actors()

def _create_test_criteria(self):
    """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
    criteria = []
    collision_criterion = CollisionTest(self.ego_vehicles[0])
    criteria.append(collision_criterion)
    return criteria

class FollowLeadingVehicleWithObstacle(BasicScenario):
    """
    This class holds a scenario similar to FollowLeadingVehicle
    but there is an obstacle in front of the leading vehicle

    This is a single ego vehicle scenario
    """
    timeout = 120

    def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, criteria_enable=True):
        """
        Setup all relevant parameters and create scenario
        """
        self._map = CarlaDataProvider.get_map()
        self._first_actor_location = 25
        self._second_actor_location = self._first_actor_location + 41
        self._first_actor_speed = 10
        self._second_actor_speed = 1.5
        self._reference_waypoint = self._map.get_waypoint(config.trigger_points[0].location)
        self._other_actor_max_brake = 1.0
        self._first_actor_transform = None
        self._second_actor_transform = None
        super(FollowLeadingVehicleWithObstacle, self).__init__('FollowLeadingVehicleWithObstacle', ego_vehicles, config, world, debug_mode, criteria_enable=criteria_enable)
        if randomize:
            self._ego_other_distance_start = random.randint(4, 8)

    def _initialize_actors(self, config):
        """
        Custom initialization
        """
        first_actor_waypoint, _ = get_waypoint_in_distance(self._reference_waypoint, self._first_actor_location)
        second_actor_waypoint, _ = get_waypoint_in_distance(self._reference_waypoint, self._second_actor_location)
        first_actor_transform = carla.Transform(carla.Location(first_actor_waypoint.transform.location.x, first_actor_waypoint.transform.location.y, first_actor_waypoint.transform.location.z - 500), first_actor_waypoint.transform.rotation)
        self._first_actor_transform = carla.Transform(carla.Location(first_actor_waypoint.transform.location.x, first_actor_waypoint.transform.location.y, first_actor_waypoint.transform.location.z + 1), first_actor_waypoint.transform.rotation)
        yaw_1 = second_actor_waypoint.transform.rotation.yaw + 90
        second_actor_transform = carla.Transform(carla.Location(second_actor_waypoint.transform.location.x, second_actor_waypoint.transform.location.y, second_actor_waypoint.transform.location.z - 500), carla.Rotation(second_actor_waypoint.transform.rotation.pitch, yaw_1, second_actor_waypoint.transform.rotation.roll))
        self._second_actor_transform = carla.Transform(carla.Location(second_actor_waypoint.transform.location.x, second_actor_waypoint.transform.location.y, second_actor_waypoint.transform.location.z + 1), carla.Rotation(second_actor_waypoint.transform.rotation.pitch, yaw_1, second_actor_waypoint.transform.rotation.roll))
        first_actor = CarlaDataProvider.request_new_actor('vehicle.nissan.patrol', first_actor_transform)
        second_actor = CarlaDataProvider.request_new_actor('vehicle.diamondback.century', second_actor_transform)
        first_actor.set_simulate_physics(enabled=False)
        second_actor.set_simulate_physics(enabled=False)
        self.other_actors.append(first_actor)
        self.other_actors.append(second_actor)

    def _create_behavior(self):
        """
        The scenario defined after is a "follow leading vehicle" scenario. After
        invoking this scenario, it will wait for the user controlled vehicle to
        enter the start region, then make the other actor to drive towards obstacle.
        Once obstacle clears the road, make the other actor to drive towards the
        next intersection. Finally, the user-controlled vehicle has to be close
        enough to the other actor to end the scenario.
        If this does not happen within 60 seconds, a timeout stops the scenario
        """
        driving_to_next_intersection = py_trees.composites.Parallel('Driving towards Intersection', policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)
        obstacle_clear_road = py_trees.composites.Parallel('Obstalce clearing road', policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)
        obstacle_clear_road.add_child(DriveDistance(self.other_actors[1], 4))
        obstacle_clear_road.add_child(KeepVelocity(self.other_actors[1], self._second_actor_speed))
        stop_near_intersection = py_trees.composites.Parallel('Waiting for end position near Intersection', policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)
        stop_near_intersection.add_child(WaypointFollower(self.other_actors[0], 10))
        stop_near_intersection.add_child(InTriggerDistanceToNextIntersection(self.other_actors[0], 20))
        driving_to_next_intersection.add_child(WaypointFollower(self.other_actors[0], self._first_actor_speed))
        driving_to_next_intersection.add_child(InTriggerDistanceToVehicle(self.other_actors[1], self.other_actors[0], 15))
        endcondition = py_trees.composites.Parallel('Waiting for end position', policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ALL)
        endcondition_part1 = InTriggerDistanceToVehicle(self.other_actors[0], self.ego_vehicles[0], distance=20, name='FinalDistance')
        endcondition_part2 = StandStill(self.ego_vehicles[0], name='FinalSpeed', duration=1)
        endcondition.add_child(endcondition_part1)
        endcondition.add_child(endcondition_part2)
        sequence = py_trees.composites.Sequence('Sequence Behavior')
        sequence.add_child(ActorTransformSetter(self.other_actors[0], self._first_actor_transform))
        sequence.add_child(ActorTransformSetter(self.other_actors[1], self._second_actor_transform))
        sequence.add_child(driving_to_next_intersection)
        sequence.add_child(StopVehicle(self.other_actors[0], self._other_actor_max_brake))
        sequence.add_child(TimeOut(3))
        sequence.add_child(obstacle_clear_road)
        sequence.add_child(stop_near_intersection)
        sequence.add_child(StopVehicle(self.other_actors[0], self._other_actor_max_brake))
        sequence.add_child(endcondition)
        sequence.add_child(ActorDestroy(self.other_actors[0]))
        sequence.add_child(ActorDestroy(self.other_actors[1]))
        return sequence

    def _create_test_criteria(self):
        """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
        criteria = []
        collision_criterion = CollisionTest(self.ego_vehicles[0])
        criteria.append(collision_criterion)
        return criteria

    def __del__(self):
        """
        Remove all actors upon deletion
        """
        self.remove_all_actors()

def _create_test_criteria(self):
    """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
    criteria = []
    collision_criterion = CollisionTest(self.ego_vehicles[0])
    criteria.append(collision_criterion)
    return criteria

def convert_transform_to_location(transform_vec):
    """
    Convert a vector of transforms to a vector of locations
    """
    location_vec = []
    for transform_tuple in transform_vec:
        location_vec.append((transform_tuple[0].location, transform_tuple[1]))
    return location_vec

def compare_scenarios(scenario_choice, existent_scenario):
    """
    Compare function for scenarios based on distance of the scenario start position
    """

    def transform_to_pos_vec(scenario):
        """
        Convert left/right/front to a meaningful CARLA position
        """
        position_vec = [scenario['trigger_position']]
        if scenario['other_actors'] is not None:
            if 'left' in scenario['other_actors']:
                position_vec += scenario['other_actors']['left']
            if 'front' in scenario['other_actors']:
                position_vec += scenario['other_actors']['front']
            if 'right' in scenario['other_actors']:
                position_vec += scenario['other_actors']['right']
        return position_vec
    choice_vec = transform_to_pos_vec(scenario_choice)
    existent_vec = transform_to_pos_vec(existent_scenario)
    for pos_choice in choice_vec:
        for pos_existent in existent_vec:
            dx = float(pos_choice['x']) - float(pos_existent['x'])
            dy = float(pos_choice['y']) - float(pos_existent['y'])
            dz = float(pos_choice['z']) - float(pos_existent['z'])
            dist_position = math.sqrt(dx * dx + dy * dy + dz * dz)
            dyaw = float(pos_choice['yaw']) - float(pos_choice['yaw'])
            dist_angle = math.sqrt(dyaw * dyaw)
            if dist_position < TRIGGER_THRESHOLD and dist_angle < TRIGGER_ANGLE_THRESHOLD:
                return True
    return False

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

def get_actors_from_list(list_of_actor_def):
    """
                Receives a list of actor definitions and creates an actual list of ActorConfigurationObjects
            """
    sublist_of_actors = []
    for actor_def in list_of_actor_def:
        sublist_of_actors.append(convert_json_to_actor(actor_def))
    return sublist_of_actors

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

class SignalizedJunctionLeftTurn(BasicScenario):
    """
    Implementation class for Hero
    Vehicle turning left at signalized junction scenario,
    Traffic Scenario 08.

    This is a single ego vehicle scenario
    """
    timeout = 80

    def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, criteria_enable=True, timeout=80):
        """
        Setup all relevant parameters and create scenario
        """
        self._world = world
        self._map = CarlaDataProvider.get_map()
        self._target_vel = 6.9
        self._brake_value = 0.5
        self._ego_distance = 110
        self._traffic_light = None
        self._other_actor_transform = None
        self._blackboard_queue_name = 'SignalizedJunctionLeftTurn/actor_flow_queue'
        self._queue = py_trees.blackboard.Blackboard().set(self._blackboard_queue_name, Queue())
        self._initialized = True
        super(SignalizedJunctionLeftTurn, self).__init__('TurnLeftAtSignalizedJunction', ego_vehicles, config, world, debug_mode, criteria_enable=criteria_enable)
        self._traffic_light = CarlaDataProvider.get_next_traffic_light(self.ego_vehicles[0], False)
        traffic_light_other = CarlaDataProvider.get_next_traffic_light(self.other_actors[0], False)
        if self._traffic_light is None or traffic_light_other is None:
            raise RuntimeError('No traffic light for the given location found')
        self._traffic_light.set_state(carla.TrafficLightState.Green)
        self._traffic_light.set_green_time(self.timeout)
        traffic_light_other.set_state(carla.TrafficLightState.Green)
        traffic_light_other.set_green_time(self.timeout)

    def _initialize_actors(self, config):
        """
        Custom initialization
        """
        self._other_actor_transform = config.other_actors[0].transform
        first_vehicle_transform = carla.Transform(carla.Location(config.other_actors[0].transform.location.x, config.other_actors[0].transform.location.y, config.other_actors[0].transform.location.z - 500), config.other_actors[0].transform.rotation)
        first_vehicle = CarlaDataProvider.request_new_actor(config.other_actors[0].model, self._other_actor_transform)
        first_vehicle.set_transform(first_vehicle_transform)
        first_vehicle.set_simulate_physics(enabled=False)
        self.other_actors.append(first_vehicle)

    def _create_behavior(self):
        """
        Hero vehicle is turning left in an urban area,
        at a signalized intersection, while other actor coming straight
        .The hero actor may turn left either before other actor
        passes intersection or later, without any collision.
        After 80 seconds, a timeout stops the scenario.
        """
        sequence = py_trees.composites.Sequence('Sequence Behavior')
        target_waypoint = generate_target_waypoint(CarlaDataProvider.get_map().get_waypoint(self.other_actors[0].get_location()), 0)
        plan = []
        wp_choice = target_waypoint.next(1.0)
        while not wp_choice[0].is_intersection:
            target_waypoint = wp_choice[0]
            plan.append((target_waypoint, RoadOption.LANEFOLLOW))
            wp_choice = target_waypoint.next(1.0)
        actor_source = ActorSource(['vehicle.tesla.model3', 'vehicle.audi.tt'], self._other_actor_transform, 15, self._blackboard_queue_name)
        actor_sink = ActorSink(plan[-1][0].transform.location, 10)
        move_actor = WaypointFollower(self.other_actors[0], self._target_vel, plan=plan, blackboard_queue_name=self._blackboard_queue_name, avoid_collision=True)
        wait = DriveDistance(self.ego_vehicles[0], self._ego_distance)
        root = py_trees.composites.Parallel(policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)
        root.add_child(wait)
        root.add_child(actor_source)
        root.add_child(actor_sink)
        root.add_child(move_actor)
        sequence.add_child(ActorTransformSetter(self.other_actors[0], self._other_actor_transform))
        sequence.add_child(root)
        sequence.add_child(ActorDestroy(self.other_actors[0]))
        return sequence

    def _create_test_criteria(self):
        """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
        criteria = []
        collison_criteria = CollisionTest(self.ego_vehicles[0])
        criteria.append(collison_criteria)
        return criteria

    def __del__(self):
        self._traffic_light = None
        self.remove_all_actors()

def _create_test_criteria(self):
    """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
    criteria = []
    collison_criteria = CollisionTest(self.ego_vehicles[0])
    criteria.append(collison_criteria)
    return criteria

class StationaryObjectCrossing(BasicScenario):
    """
    This class holds everything required for a simple object crash
    without prior vehicle action involving a vehicle and a cyclist.
    The ego vehicle is passing through a road and encounters
    a stationary cyclist.

    This is a single ego vehicle scenario
    """

    def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, criteria_enable=True, timeout=60):
        """
        Setup all relevant parameters and create scenario
        """
        self._wmap = CarlaDataProvider.get_map()
        self._reference_waypoint = self._wmap.get_waypoint(config.trigger_points[0].location)
        self._ego_vehicle_distance_driven = 40
        self._other_actor_target_velocity = 10
        self.timeout = timeout
        super(StationaryObjectCrossing, self).__init__('Stationaryobjectcrossing', ego_vehicles, config, world, debug_mode, criteria_enable=criteria_enable)

    def _initialize_actors(self, config):
        """
        Custom initialization
        """
        _start_distance = 40
        lane_width = self._reference_waypoint.lane_width
        location, _ = get_location_in_distance_from_wp(self._reference_waypoint, _start_distance)
        waypoint = self._wmap.get_waypoint(location)
        offset = {'orientation': 270, 'position': 90, 'z': 0.4, 'k': 0.2}
        position_yaw = waypoint.transform.rotation.yaw + offset['position']
        orientation_yaw = waypoint.transform.rotation.yaw + offset['orientation']
        offset_location = carla.Location(offset['k'] * lane_width * math.cos(math.radians(position_yaw)), offset['k'] * lane_width * math.sin(math.radians(position_yaw)))
        location += offset_location
        location.z += offset['z']
        self.transform = carla.Transform(location, carla.Rotation(yaw=orientation_yaw))
        static = CarlaDataProvider.request_new_actor('static.prop.container', self.transform)
        static.set_simulate_physics(True)
        self.other_actors.append(static)

    def _create_behavior(self):
        """
        Only behavior here is to wait
        """
        lane_width = self.ego_vehicles[0].get_world().get_map().get_waypoint(self.ego_vehicles[0].get_location()).lane_width
        lane_width = lane_width + 1.25 * lane_width
        actor_stand = TimeOut(15)
        actor_removed = ActorDestroy(self.other_actors[0])
        end_condition = DriveDistance(self.ego_vehicles[0], self._ego_vehicle_distance_driven)
        root = py_trees.composites.Parallel(policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)
        scenario_sequence = py_trees.composites.Sequence()
        root.add_child(scenario_sequence)
        scenario_sequence.add_child(ActorTransformSetter(self.other_actors[0], self.transform))
        scenario_sequence.add_child(actor_stand)
        scenario_sequence.add_child(actor_removed)
        scenario_sequence.add_child(end_condition)
        return root

    def _create_test_criteria(self):
        """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
        criteria = []
        collision_criterion = CollisionTest(self.ego_vehicles[0])
        criteria.append(collision_criterion)
        return criteria

    def __del__(self):
        """
        Remove all actors upon deletion
        """
        self.remove_all_actors()

def _create_test_criteria(self):
    """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
    criteria = []
    collision_criterion = CollisionTest(self.ego_vehicles[0])
    criteria.append(collision_criterion)
    return criteria

class DynamicObjectCrossing(BasicScenario):
    """
    This class holds everything required for a simple object crash
    without prior vehicle action involving a vehicle and a cyclist/pedestrian,
    The ego vehicle is passing through a road,
    And encounters a cyclist/pedestrian crossing the road.

    This is a single ego vehicle scenario
    """

    def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, criteria_enable=True, adversary_type=False, timeout=60):
        """
        Setup all relevant parameters and create scenario
        """
        self._wmap = CarlaDataProvider.get_map()
        self._reference_waypoint = self._wmap.get_waypoint(config.trigger_points[0].location)
        self._ego_vehicle_distance_driven = 40
        self._other_actor_target_velocity = 5
        self._other_actor_max_brake = 1.0
        self._time_to_reach = 10
        self._adversary_type = adversary_type
        self._walker_yaw = 0
        self._num_lane_changes = 1
        self.transform = None
        self.transform2 = None
        self.timeout = timeout
        self._trigger_location = config.trigger_points[0].location
        self._number_of_attempts = 20
        self._spawn_attempted = 0
        self._ego_route = CarlaDataProvider.get_ego_vehicle_route()
        super(DynamicObjectCrossing, self).__init__('DynamicObjectCrossing', ego_vehicles, config, world, debug_mode, criteria_enable=criteria_enable)

    def _calculate_base_transform(self, _start_distance, waypoint):
        lane_width = waypoint.lane_width
        if self._reference_waypoint.is_junction:
            stop_at_junction = False
        else:
            stop_at_junction = True
        location, _ = get_location_in_distance_from_wp(waypoint, _start_distance, stop_at_junction)
        waypoint = self._wmap.get_waypoint(location)
        offset = {'orientation': 270, 'position': 90, 'z': 0.6, 'k': 1.0}
        position_yaw = waypoint.transform.rotation.yaw + offset['position']
        orientation_yaw = waypoint.transform.rotation.yaw + offset['orientation']
        offset_location = carla.Location(offset['k'] * lane_width * math.cos(math.radians(position_yaw)), offset['k'] * lane_width * math.sin(math.radians(position_yaw)))
        location += offset_location
        location.z = self._trigger_location.z + offset['z']
        return (carla.Transform(location, carla.Rotation(yaw=orientation_yaw)), orientation_yaw)

    def _spawn_adversary(self, transform, orientation_yaw):
        self._time_to_reach *= self._num_lane_changes
        if self._adversary_type is False:
            self._walker_yaw = orientation_yaw
            self._other_actor_target_velocity = 3 + 0.4 * self._num_lane_changes
            walker = CarlaDataProvider.request_new_actor('walker.*', transform)
            adversary = walker
        else:
            self._other_actor_target_velocity = self._other_actor_target_velocity * self._num_lane_changes
            first_vehicle = CarlaDataProvider.request_new_actor('vehicle.diamondback.century', transform)
            first_vehicle.set_simulate_physics(enabled=False)
            adversary = first_vehicle
        return adversary

    def _spawn_blocker(self, transform, orientation_yaw):
        """
        Spawn the blocker prop that blocks the vision from the egovehicle of the jaywalker
        :return:
        """
        shift = 0.9
        x_ego = self._reference_waypoint.transform.location.x
        y_ego = self._reference_waypoint.transform.location.y
        x_cycle = transform.location.x
        y_cycle = transform.location.y
        x_static = x_ego + shift * (x_cycle - x_ego)
        y_static = y_ego + shift * (y_cycle - y_ego)
        spawn_point_wp = self.ego_vehicles[0].get_world().get_map().get_waypoint(transform.location)
        self.transform2 = carla.Transform(carla.Location(x_static, y_static, spawn_point_wp.transform.location.z + 0.3), carla.Rotation(yaw=orientation_yaw + 180))
        static = CarlaDataProvider.request_new_actor('static.prop.vendingmachine', self.transform2)
        static.set_simulate_physics(enabled=False)
        return static

    def _initialize_actors(self, config):
        """
        Custom initialization
        """
        _start_distance = 12
        waypoint = self._reference_waypoint
        while True:
            wp_next = waypoint.get_right_lane()
            self._num_lane_changes += 1
            if wp_next is None or wp_next.lane_type == carla.LaneType.Sidewalk:
                break
            elif wp_next.lane_type == carla.LaneType.Shoulder:
                if wp_next.lane_width > 2:
                    _start_distance += 1.5
                    waypoint = wp_next
                break
            else:
                _start_distance += 1.5
                waypoint = wp_next
        while True:
            try:
                self.transform, orientation_yaw = self._calculate_base_transform(_start_distance, waypoint)
                first_vehicle = self._spawn_adversary(self.transform, orientation_yaw)
                blocker = self._spawn_blocker(self.transform, orientation_yaw)
                break
            except RuntimeError as r:
                print('Base transform is blocking objects ', self.transform)
                _start_distance += 0.4
                self._spawn_attempted += 1
                if self._spawn_attempted >= self._number_of_attempts:
                    raise r
        disp_transform = carla.Transform(carla.Location(self.transform.location.x, self.transform.location.y, self.transform.location.z - 500), self.transform.rotation)
        prop_disp_transform = carla.Transform(carla.Location(self.transform2.location.x, self.transform2.location.y, self.transform2.location.z - 500), self.transform2.rotation)
        first_vehicle.set_transform(disp_transform)
        blocker.set_transform(prop_disp_transform)
        first_vehicle.set_simulate_physics(enabled=False)
        blocker.set_simulate_physics(enabled=False)
        self.other_actors.append(first_vehicle)
        self.other_actors.append(blocker)

    def _create_behavior(self):
        """
        After invoking this scenario, cyclist will wait for the user
        controlled vehicle to enter trigger distance region,
        the cyclist starts crossing the road once the condition meets,
        then after 60 seconds, a timeout stops the scenario
        """
        root = py_trees.composites.Parallel(policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE, name='OccludedObjectCrossing')
        lane_width = self._reference_waypoint.lane_width
        lane_width = lane_width + 1.25 * lane_width * self._num_lane_changes
        dist_to_trigger = 12 + self._num_lane_changes
        if self._ego_route is not None:
            start_condition = InTriggerDistanceToLocationAlongRoute(self.ego_vehicles[0], self._ego_route, self.transform.location, dist_to_trigger)
        else:
            start_condition = InTimeToArrivalToVehicle(self.ego_vehicles[0], self.other_actors[0], self._time_to_reach)
        actor_velocity = KeepVelocity(self.other_actors[0], self._other_actor_target_velocity, name='walker velocity')
        actor_drive = DriveDistance(self.other_actors[0], 0.5 * lane_width, name='walker drive distance')
        actor_start_cross_lane = AccelerateToVelocity(self.other_actors[0], 1.0, self._other_actor_target_velocity, name='walker crossing lane accelerate velocity')
        actor_cross_lane = DriveDistance(self.other_actors[0], lane_width, name='walker drive distance for lane crossing ')
        actor_stop_crossed_lane = StopVehicle(self.other_actors[0], self._other_actor_max_brake, name='walker stop')
        ego_pass_machine = DriveDistance(self.ego_vehicles[0], 5, name='ego vehicle passed prop')
        actor_remove = ActorDestroy(self.other_actors[0], name='Destroying walker')
        static_remove = ActorDestroy(self.other_actors[1], name='Destroying Prop')
        end_condition = DriveDistance(self.ego_vehicles[0], self._ego_vehicle_distance_driven, name='End condition ego drive distance')
        scenario_sequence = py_trees.composites.Sequence()
        keep_velocity_other = py_trees.composites.Parallel(policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE, name='keep velocity other')
        keep_velocity = py_trees.composites.Parallel(policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE, name='keep velocity')
        root.add_child(scenario_sequence)
        scenario_sequence.add_child(ActorTransformSetter(self.other_actors[0], self.transform, name='TransformSetterTS3walker'))
        scenario_sequence.add_child(ActorTransformSetter(self.other_actors[1], self.transform2, name='TransformSetterTS3coca', physics=False))
        scenario_sequence.add_child(HandBrakeVehicle(self.other_actors[0], True))
        scenario_sequence.add_child(start_condition)
        scenario_sequence.add_child(HandBrakeVehicle(self.other_actors[0], False))
        scenario_sequence.add_child(keep_velocity)
        scenario_sequence.add_child(keep_velocity_other)
        scenario_sequence.add_child(actor_stop_crossed_lane)
        scenario_sequence.add_child(actor_remove)
        scenario_sequence.add_child(static_remove)
        scenario_sequence.add_child(end_condition)
        keep_velocity.add_child(actor_velocity)
        keep_velocity.add_child(actor_drive)
        keep_velocity_other.add_child(actor_start_cross_lane)
        keep_velocity_other.add_child(actor_cross_lane)
        keep_velocity_other.add_child(ego_pass_machine)
        return root

    def _create_test_criteria(self):
        """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
        criteria = []
        collision_criterion = CollisionTest(self.ego_vehicles[0])
        criteria.append(collision_criterion)
        return criteria

    def __del__(self):
        """
        Remove all actors upon deletion
        """
        self.remove_all_actors()

def _create_test_criteria(self):
    """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
    criteria = []
    collision_criterion = CollisionTest(self.ego_vehicles[0])
    criteria.append(collision_criterion)
    return criteria

class FreeRide(BasicScenario):
    """
    Implementation of a simple free ride scenario that consits only of the ego vehicle
    """

    def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, criteria_enable=True, timeout=10000000):
        """
        Setup all relevant parameters and create scenario
        """
        self.timeout = timeout
        super(FreeRide, self).__init__('FreeRide', ego_vehicles, config, world, debug_mode, criteria_enable=criteria_enable)

    def _setup_scenario_trigger(self, config):
        """
        """
        return None

    def _create_behavior(self):
        """
        """
        sequence = py_trees.composites.Sequence('Sequence Behavior')
        sequence.add_child(Idle())
        return sequence

    def _create_test_criteria(self):
        """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
        criteria = []
        for ego_vehicle in self.ego_vehicles:
            collision_criterion = CollisionTest(ego_vehicle)
            criteria.append(collision_criterion)
        return criteria

    def __del__(self):
        """
        Remove all actors upon deletion
        """
        self.remove_all_actors()

def _create_test_criteria(self):
    """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
    criteria = []
    for ego_vehicle in self.ego_vehicles:
        collision_criterion = CollisionTest(ego_vehicle)
        criteria.append(collision_criterion)
    return criteria

class SignalJunctionCrossingRoute(BasicScenario):
    """
    At routes, these scenarios are simplified, as they can be triggered making
    use of the background activity. To ensure interactions with this background
    activity, the traffic lights are modified, setting two of them to green
    """
    _ego_max_velocity_allowed = 20
    _ego_expected_driven_distance = 50
    _ego_distance_to_drive = 20
    _traffic_light = None

    def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, criteria_enable=True, timeout=180):
        """
        Setup all relevant parameters and create scenario
        and instantiate scenario manager
        """
        self.timeout = timeout
        self.subtype = config.subtype
        super(SignalJunctionCrossingRoute, self).__init__('SignalJunctionCrossingRoute', ego_vehicles, config, world, debug_mode, criteria_enable=criteria_enable)

    def _initialize_actors(self, config):
        """
        Custom initialization
        """

    def _create_behavior(self):
        """
        Scenario behavior:
        When close to an intersection, the traffic lights will turn green for
        both the ego_vehicle and another lane, allowing the background activity
        to "run" their red light, creating scenarios 7, 8 and 9.

        If this does not happen within 120 seconds, a timeout stops the scenario
        """
        traffic_hack = TrafficLightManipulator(self.ego_vehicles[0], self.subtype)
        wait = DriveDistance(self.ego_vehicles[0], self._ego_distance_to_drive, name='DriveDistance')
        sequence = py_trees.composites.Sequence('SignalJunctionCrossingRoute')
        sequence.add_child(traffic_hack)
        sequence.add_child(wait)
        return sequence

    def _create_test_criteria(self):
        """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
        criteria = []
        max_velocity_criterion = MaxVelocityTest(self.ego_vehicles[0], self._ego_max_velocity_allowed, optional=True)
        collision_criterion = CollisionTest(self.ego_vehicles[0])
        driven_distance_criterion = DrivenDistanceTest(self.ego_vehicles[0], self._ego_expected_driven_distance)
        criteria.append(max_velocity_criterion)
        criteria.append(collision_criterion)
        criteria.append(driven_distance_criterion)
        return criteria

    def __del__(self):
        """
        Remove all actors and traffic lights upon deletion
        """
        self._traffic_light = None
        self.remove_all_actors()

def _create_test_criteria(self):
    """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
    criteria = []
    max_velocity_criterion = MaxVelocityTest(self.ego_vehicles[0], self._ego_max_velocity_allowed, optional=True)
    collision_criterion = CollisionTest(self.ego_vehicles[0])
    driven_distance_criterion = DrivenDistanceTest(self.ego_vehicles[0], self._ego_expected_driven_distance)
    criteria.append(max_velocity_criterion)
    criteria.append(collision_criterion)
    criteria.append(driven_distance_criterion)
    return criteria

class NoSignalJunctionCrossingRoute(BasicScenario):
    """
    At routes, these scenarios are simplified, as they can be triggered making
    use of the background activity. For unsignalized intersections, just wait
    until the ego_vehicle has left the intersection.
    """
    _ego_max_velocity_allowed = 20
    _ego_expected_driven_distance = 50
    _ego_distance_to_drive = 20

    def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, criteria_enable=True, timeout=180):
        """
        Setup all relevant parameters and create scenario
        and instantiate scenario manager
        """
        self.timeout = timeout
        super(NoSignalJunctionCrossingRoute, self).__init__('NoSignalJunctionCrossingRoute', ego_vehicles, config, world, debug_mode, criteria_enable=criteria_enable)

    def _initialize_actors(self, config):
        """
        Custom initialization
        """

    def _create_behavior(self):
        """
        Scenario behavior:
        When close to an intersection, the traffic lights will turn green for
        both the ego_vehicle and another lane, allowing the background activity
        to "run" their red light.

        If this does not happen within 120 seconds, a timeout stops the scenario
        """
        wait = WaitEndIntersection(self.ego_vehicles[0], name='WaitEndIntersection')
        end_condition = DriveDistance(self.ego_vehicles[0], self._ego_distance_to_drive, name='DriveDistance')
        sequence = py_trees.composites.Sequence('NoSignalJunctionCrossingRoute')
        sequence.add_child(wait)
        sequence.add_child(end_condition)
        return sequence

    def _create_test_criteria(self):
        """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
        criteria = []
        max_velocity_criterion = MaxVelocityTest(self.ego_vehicles[0], self._ego_max_velocity_allowed, optional=True)
        collision_criterion = CollisionTest(self.ego_vehicles[0])
        driven_distance_criterion = DrivenDistanceTest(self.ego_vehicles[0], self._ego_expected_driven_distance)
        criteria.append(max_velocity_criterion)
        criteria.append(collision_criterion)
        criteria.append(driven_distance_criterion)
        return criteria

    def __del__(self):
        """
        Remove all actors and traffic lights upon deletion
        """
        self.remove_all_actors()

def _create_test_criteria(self):
    """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
    criteria = []
    max_velocity_criterion = MaxVelocityTest(self.ego_vehicles[0], self._ego_max_velocity_allowed, optional=True)
    collision_criterion = CollisionTest(self.ego_vehicles[0])
    driven_distance_criterion = DrivenDistanceTest(self.ego_vehicles[0], self._ego_expected_driven_distance)
    criteria.append(max_velocity_criterion)
    criteria.append(collision_criterion)
    criteria.append(driven_distance_criterion)
    return criteria

def calculate_velocity(actor):
    """
    Method to calculate the velocity of a actor
    """
    velocity_squared = actor.get_velocity().x ** 2
    velocity_squared += actor.get_velocity().y ** 2
    return math.sqrt(velocity_squared)

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
def get_actor_by_id(actor_id):
    """
        Get an actor from the pool by using its ID. If the actor
        does not exist, None is returned.
        """
    if actor_id in CarlaDataProvider._carla_actor_pool:
        return CarlaDataProvider._carla_actor_pool[actor_id]
    print('Non-existing actor id {}'.format(actor_id))
    return None

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

class TriggerAcceleration(AtomicCondition):
    """
    Atomic containing a comparison between an actor's acceleration
    and a reference one. The behavior returns SUCCESS when the
    expected comparison (greater than / less than / equal to) is achieved

    Args:
        actor (carla.Actor): CARLA actor to execute the behavior
        name (str): Name of the condition
        target_acceleration (float): Acceleration reference (in m/s^2) on which the success is dependent
        comparison_operator (operator): Type "operator", used to compare the two acceleration
    """

    def __init__(self, actor, target_acceleration, comparison_operator=operator.gt, name='TriggerAcceleration'):
        """
        Setup trigger acceleration
        """
        super(TriggerAcceleration, self).__init__(name)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._actor = actor
        self._target_acceleration = target_acceleration
        self._comparison_operator = comparison_operator

    def update(self):
        """
        Gets the accleration of the actor and compares it with the reference one

        returns:
            py_trees.common.Status.RUNNING when the comparison fails and
            py_trees.common.Status.SUCCESS when it succeeds
        """
        new_status = py_trees.common.Status.RUNNING
        acceleration = self._actor.get_acceleration()
        linear_accel = math.sqrt(math.pow(acceleration.x, 2) + math.pow(acceleration.y, 2) + math.pow(acceleration.z, 2))
        if self._comparison_operator(linear_accel, self._target_acceleration):
            new_status = py_trees.common.Status.SUCCESS
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

def update(self):
    """
        Gets the accleration of the actor and compares it with the reference one

        returns:
            py_trees.common.Status.RUNNING when the comparison fails and
            py_trees.common.Status.SUCCESS when it succeeds
        """
    new_status = py_trees.common.Status.RUNNING
    acceleration = self._actor.get_acceleration()
    linear_accel = math.sqrt(math.pow(acceleration.x, 2) + math.pow(acceleration.y, 2) + math.pow(acceleration.z, 2))
    if self._comparison_operator(linear_accel, self._target_acceleration):
        new_status = py_trees.common.Status.SUCCESS
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    return new_status

class WaitUntilInFront(AtomicCondition):
    """
    Behavior that support the creation of cut ins. It waits until the actor has passed another actor

    Parameters:
    - actor: the one getting in front of the other actor
    - other_actor: the reference vehicle that the actor will have to get in front of
    - factor: How much in front the actor will have to get (from 0 to infinity):
        0: They are right next to each other
        1: The front of the other_actor and the back of the actor are right next to each other
    """

    def __init__(self, actor, other_actor, factor=1, check_distance=True, name='WaitUntilInFront'):
        """
        Init
        """
        super(WaitUntilInFront, self).__init__(name)
        self._actor = actor
        self._other_actor = other_actor
        self._distance = 10
        self._factor = max(EPSILON, factor)
        self._check_distance = check_distance
        self._world = CarlaDataProvider.get_world()
        self._map = CarlaDataProvider.get_map(self._world)
        actor_extent = self._actor.bounding_box.extent.x
        other_extent = self._other_actor.bounding_box.extent.x
        self._length = self._factor * (actor_extent + other_extent)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)

    def update(self):
        """
        Checks if the two actors meet the requirements
        """
        new_status = py_trees.common.Status.RUNNING
        in_front = False
        close_by = False
        actor_location = CarlaDataProvider.get_location(self._actor)
        if actor_location is None:
            return new_status
        other_location = CarlaDataProvider.get_location(self._other_actor)
        other_waypoint = self._map.get_waypoint(other_location)
        if other_waypoint is None:
            return new_status
        other_next_waypoints = other_waypoint.next(self._length)
        if other_next_waypoints is None:
            return new_status
        other_next_waypoint = other_next_waypoints[0]
        other_dir = other_next_waypoint.transform.get_forward_vector()
        act_other_dir = actor_location - other_next_waypoint.transform.location
        dot_ve_wp = other_dir.x * act_other_dir.x + other_dir.y * act_other_dir.y + other_dir.z * act_other_dir.z
        if dot_ve_wp > 0.0:
            in_front = True
        if not self._check_distance:
            close_by = True
        elif actor_location.distance(other_next_waypoint.transform.location) < self._distance:
            close_by = True
        if in_front and close_by:
            new_status = py_trees.common.Status.SUCCESS
        return new_status

def update(self):
    """
        Checks if the two actors meet the requirements
        """
    new_status = py_trees.common.Status.RUNNING
    in_front = False
    close_by = False
    actor_location = CarlaDataProvider.get_location(self._actor)
    if actor_location is None:
        return new_status
    other_location = CarlaDataProvider.get_location(self._other_actor)
    other_waypoint = self._map.get_waypoint(other_location)
    if other_waypoint is None:
        return new_status
    other_next_waypoints = other_waypoint.next(self._length)
    if other_next_waypoints is None:
        return new_status
    other_next_waypoint = other_next_waypoints[0]
    other_dir = other_next_waypoint.transform.get_forward_vector()
    act_other_dir = actor_location - other_next_waypoint.transform.location
    dot_ve_wp = other_dir.x * act_other_dir.x + other_dir.y * act_other_dir.y + other_dir.z * act_other_dir.z
    if dot_ve_wp > 0.0:
        in_front = True
    if not self._check_distance:
        close_by = True
    elif actor_location.distance(other_next_waypoint.transform.location) < self._distance:
        close_by = True
    if in_front and close_by:
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

class ActorSpeedAboveThresholdTest(Criterion):
    """
    This test will fail if the actor has had its linear velocity lower than a specific value for
    a specific amount of time
    Important parameters:
    - actor: CARLA actor to be used for this test
    - speed_threshold: speed required
    - below_threshold_max_time: Maximum time (in seconds) the actor can remain under the speed threshold
    - terminate_on_failure [optional]: If True, the complete scenario will terminate upon failure of this test
    """

    def __init__(self, actor, speed_threshold, below_threshold_max_time, name='ActorSpeedAboveThresholdTest', terminate_on_failure=False):
        """
        Class constructor.
        """
        super(ActorSpeedAboveThresholdTest, self).__init__(name, actor, 0, terminate_on_failure=terminate_on_failure)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._actor = actor
        self._speed_threshold = speed_threshold
        self._below_threshold_max_time = below_threshold_max_time
        self._time_last_valid_state = None

    def update(self):
        """
        Check if the actor speed is above the speed_threshold
        """
        new_status = py_trees.common.Status.RUNNING
        linear_speed = CarlaDataProvider.get_velocity(self._actor)
        if linear_speed is not None:
            if linear_speed < self._speed_threshold and self._time_last_valid_state:
                if GameTime.get_time() - self._time_last_valid_state > self._below_threshold_max_time:
                    self.test_status = 'FAILURE'
                    vehicle_location = CarlaDataProvider.get_location(self._actor)
                    blocked_event = TrafficEvent(event_type=TrafficEventType.VEHICLE_BLOCKED)
                    ActorSpeedAboveThresholdTest._set_event_message(blocked_event, vehicle_location)
                    ActorSpeedAboveThresholdTest._set_event_dict(blocked_event, vehicle_location)
                    self.list_traffic_events.append(blocked_event)
            else:
                self._time_last_valid_state = GameTime.get_time()
        if self._terminate_on_failure and self.test_status == 'FAILURE':
            new_status = py_trees.common.Status.FAILURE
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

    @staticmethod
    def _set_event_message(event, location):
        """
        Sets the message of the event
        """
        event.set_message('Agent got blocked at (x={}, y={}, z={})'.format(round(location.x, 3), round(location.y, 3), round(location.z, 3)))

    @staticmethod
    def _set_event_dict(event, location):
        """
        Sets the dictionary of the event
        """
        event.set_dict({'x': location.x, 'y': location.y, 'z': location.z})

def update(self):
    """
        Check if the actor speed is above the speed_threshold
        """
    new_status = py_trees.common.Status.RUNNING
    linear_speed = CarlaDataProvider.get_velocity(self._actor)
    if linear_speed is not None:
        if linear_speed < self._speed_threshold and self._time_last_valid_state:
            if GameTime.get_time() - self._time_last_valid_state > self._below_threshold_max_time:
                self.test_status = 'FAILURE'
                vehicle_location = CarlaDataProvider.get_location(self._actor)
                blocked_event = TrafficEvent(event_type=TrafficEventType.VEHICLE_BLOCKED)
                ActorSpeedAboveThresholdTest._set_event_message(blocked_event, vehicle_location)
                ActorSpeedAboveThresholdTest._set_event_dict(blocked_event, vehicle_location)
                self.list_traffic_events.append(blocked_event)
        else:
            self._time_last_valid_state = GameTime.get_time()
    if self._terminate_on_failure and self.test_status == 'FAILURE':
        new_status = py_trees.common.Status.FAILURE
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    return new_status

@staticmethod
def _set_event_message(event, location):
    """
        Sets the message of the event
        """
    event.set_message('Agent got blocked at (x={}, y={}, z={})'.format(round(location.x, 3), round(location.y, 3), round(location.z, 3)))

@staticmethod
def _set_event_dict(event, location):
    """
        Sets the dictionary of the event
        """
    event.set_dict({'x': location.x, 'y': location.y, 'z': location.z})

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

@staticmethod
def _count_lane_invasion(weak_self, event):
    """
        Callback to update lane invasion count
        """
    self = weak_self()
    if not self:
        return
    self.actual_value += 1

class OnSidewalkTest(Criterion):
    """
    Atomic containing a test to detect sidewalk invasions of a specific actor. This atomic can
    fail when actor has spent a specific time outside driving lanes (defined by OpenDRIVE).

    Args:
        actor (carla.Actor): CARLA actor to be used for this test
        duration (float): Time spent at sidewalks before the atomic fails.
            If terminate_on_failure isn't active, this is ignored.
        optional (bool): If True, the result is not considered for an overall pass/fail result
            when using the output argument
        terminate_on_failure (bool): If True, the atomic will fail when the duration condition has been met.
    """

    def __init__(self, actor, duration=0, optional=False, terminate_on_failure=False, name='OnSidewalkTest'):
        """
        Construction with sensor setup
        """
        super(OnSidewalkTest, self).__init__(name, actor, 0, None, optional, terminate_on_failure)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._actor = actor
        self._map = CarlaDataProvider.get_map()
        self._onsidewalk_active = False
        self._outside_lane_active = False
        self._actor_location = self._actor.get_location()
        self._wrong_sidewalk_distance = 0
        self._wrong_outside_lane_distance = 0
        self._sidewalk_start_location = None
        self._outside_lane_start_location = None
        self._duration = duration
        self._prev_time = None
        self._time_outside_lanes = 0

    def update(self):
        """
        First, transforms the actor's current position as well as its four corners to their
        corresponding waypoints. Depending on their lane type, the actor will be considered to be
        outside (or inside) driving lanes.

        returns:
            py_trees.common.Status.FAILURE: when the actor has spent a given duration outside
                driving lanes and terminate_on_failure is active
            py_trees.common.Status.RUNNING: the rest of the time
        """
        new_status = py_trees.common.Status.RUNNING
        if self._terminate_on_failure and self.test_status == 'FAILURE':
            new_status = py_trees.common.Status.FAILURE
        current_tra = CarlaDataProvider.get_transform(self._actor)
        current_loc = current_tra.location
        current_wp = self._map.get_waypoint(current_loc, lane_type=carla.LaneType.Any)
        if current_wp.lane_type == carla.LaneType.Sidewalk:
            if not self._onsidewalk_active:
                self._onsidewalk_active = True
                self._sidewalk_start_location = current_loc
        elif current_wp.lane_type != carla.LaneType.Driving and current_wp.lane_type != carla.LaneType.Parking:
            heading_vec = current_tra.get_forward_vector()
            heading_vec.z = 0
            heading_vec = heading_vec / math.sqrt(math.pow(heading_vec.x, 2) + math.pow(heading_vec.y, 2))
            perpendicular_vec = carla.Vector3D(-heading_vec.y, heading_vec.x, 0)
            extent = self.actor.bounding_box.extent
            x_boundary_vector = heading_vec * extent.x
            y_boundary_vector = perpendicular_vec * extent.y
            bbox = [current_loc + carla.Location(x_boundary_vector - y_boundary_vector), current_loc + carla.Location(x_boundary_vector + y_boundary_vector), current_loc + carla.Location(-1 * x_boundary_vector - y_boundary_vector), current_loc + carla.Location(-1 * x_boundary_vector + y_boundary_vector)]
            bbox_wp = [self._map.get_waypoint(bbox[0], lane_type=carla.LaneType.Any), self._map.get_waypoint(bbox[1], lane_type=carla.LaneType.Any), self._map.get_waypoint(bbox[2], lane_type=carla.LaneType.Any), self._map.get_waypoint(bbox[3], lane_type=carla.LaneType.Any)]
            if bbox_wp[0].lane_type == (carla.LaneType.Driving or carla.LaneType.Parking) or bbox_wp[1].lane_type == (carla.LaneType.Driving or carla.LaneType.Parking) or bbox_wp[2].lane_type == (carla.LaneType.Driving or carla.LaneType.Parking) or (bbox_wp[3].lane_type == (carla.LaneType.Driving or carla.LaneType.Parking)):
                self._onsidewalk_active = False
                self._outside_lane_active = False
            elif bbox_wp[0].lane_type == carla.LaneType.Sidewalk or bbox_wp[1].lane_type == carla.LaneType.Sidewalk or bbox_wp[2].lane_type == carla.LaneType.Sidewalk or (bbox_wp[3].lane_type == carla.LaneType.Sidewalk):
                if not self._onsidewalk_active:
                    self._onsidewalk_active = True
                    self._sidewalk_start_location = current_loc
            else:
                distance_vehicle_wp = current_loc.distance(current_wp.transform.location)
                if distance_vehicle_wp >= current_wp.lane_width / 2:
                    if not self._outside_lane_active:
                        self._outside_lane_active = True
                        self._outside_lane_start_location = current_loc
                else:
                    self._onsidewalk_active = False
                    self._outside_lane_active = False
        elif current_wp.is_junction:
            distance_vehicle_wp = math.sqrt(math.pow(current_wp.transform.location.x - current_loc.x, 2) + math.pow(current_wp.transform.location.y - current_loc.y, 2))
            if distance_vehicle_wp <= current_wp.lane_width / 2:
                self._onsidewalk_active = False
                self._outside_lane_active = False
        else:
            self._onsidewalk_active = False
            self._outside_lane_active = False
        if self._onsidewalk_active or self._outside_lane_active:
            if self._prev_time is None:
                self._prev_time = GameTime.get_time()
            else:
                curr_time = GameTime.get_time()
                self._time_outside_lanes += curr_time - self._prev_time
                self._prev_time = curr_time
        else:
            self._prev_time = None
        if self._time_outside_lanes > self._duration:
            self.test_status = 'FAILURE'
        distance_vector = CarlaDataProvider.get_location(self._actor) - self._actor_location
        distance = math.sqrt(math.pow(distance_vector.x, 2) + math.pow(distance_vector.y, 2))
        if distance >= 0.02:
            self._actor_location = CarlaDataProvider.get_location(self._actor)
            if self._onsidewalk_active:
                self._wrong_sidewalk_distance += distance
            elif self._outside_lane_active:
                self._wrong_outside_lane_distance += distance
        if not self._onsidewalk_active and self._wrong_sidewalk_distance > 0:
            self.actual_value += 1
            onsidewalk_event = TrafficEvent(event_type=TrafficEventType.ON_SIDEWALK_INFRACTION)
            self._set_event_message(onsidewalk_event, self._sidewalk_start_location, self._wrong_sidewalk_distance)
            self._set_event_dict(onsidewalk_event, self._sidewalk_start_location, self._wrong_sidewalk_distance)
            self._onsidewalk_active = False
            self._wrong_sidewalk_distance = 0
            self.list_traffic_events.append(onsidewalk_event)
        if not self._outside_lane_active and self._wrong_outside_lane_distance > 0:
            self.actual_value += 1
            outsidelane_event = TrafficEvent(event_type=TrafficEventType.OUTSIDE_LANE_INFRACTION)
            self._set_event_message(outsidelane_event, self._outside_lane_start_location, self._wrong_outside_lane_distance)
            self._set_event_dict(outsidelane_event, self._outside_lane_start_location, self._wrong_outside_lane_distance)
            self._outside_lane_active = False
            self._wrong_outside_lane_distance = 0
            self.list_traffic_events.append(outsidelane_event)
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

    def terminate(self, new_status):
        """
        If there is currently an event running, it is registered
        """
        if self._onsidewalk_active:
            self.actual_value += 1
            onsidewalk_event = TrafficEvent(event_type=TrafficEventType.ON_SIDEWALK_INFRACTION)
            self._set_event_message(onsidewalk_event, self._sidewalk_start_location, self._wrong_sidewalk_distance)
            self._set_event_dict(onsidewalk_event, self._sidewalk_start_location, self._wrong_sidewalk_distance)
            self._onsidewalk_active = False
            self._wrong_sidewalk_distance = 0
            self.list_traffic_events.append(onsidewalk_event)
        if self._outside_lane_active:
            self.actual_value += 1
            outsidelane_event = TrafficEvent(event_type=TrafficEventType.OUTSIDE_LANE_INFRACTION)
            self._set_event_message(outsidelane_event, self._outside_lane_start_location, self._wrong_outside_lane_distance)
            self._set_event_dict(outsidelane_event, self._outside_lane_start_location, self._wrong_outside_lane_distance)
            self._outside_lane_active = False
            self._wrong_outside_lane_distance = 0
            self.list_traffic_events.append(outsidelane_event)
        super(OnSidewalkTest, self).terminate(new_status)

    def _set_event_message(self, event, location, distance):
        """
        Sets the message of the event
        """
        if event.get_type() == TrafficEventType.ON_SIDEWALK_INFRACTION:
            message_start = 'Agent invaded the sidewalk'
        else:
            message_start = 'Agent went outside the lane'
        event.set_message('{} for about {} meters, starting at (x={}, y={}, z={})'.format(message_start, round(distance, 3), round(location.x, 3), round(location.y, 3), round(location.z, 3)))

    def _set_event_dict(self, event, location, distance):
        """
        Sets the dictionary of the event
        """
        event.set_dict({'x': location.x, 'y': location.y, 'z': location.z, 'distance': distance})

def update(self):
    """
        First, transforms the actor's current position as well as its four corners to their
        corresponding waypoints. Depending on their lane type, the actor will be considered to be
        outside (or inside) driving lanes.

        returns:
            py_trees.common.Status.FAILURE: when the actor has spent a given duration outside
                driving lanes and terminate_on_failure is active
            py_trees.common.Status.RUNNING: the rest of the time
        """
    new_status = py_trees.common.Status.RUNNING
    if self._terminate_on_failure and self.test_status == 'FAILURE':
        new_status = py_trees.common.Status.FAILURE
    current_tra = CarlaDataProvider.get_transform(self._actor)
    current_loc = current_tra.location
    current_wp = self._map.get_waypoint(current_loc, lane_type=carla.LaneType.Any)
    if current_wp.lane_type == carla.LaneType.Sidewalk:
        if not self._onsidewalk_active:
            self._onsidewalk_active = True
            self._sidewalk_start_location = current_loc
    elif current_wp.lane_type != carla.LaneType.Driving and current_wp.lane_type != carla.LaneType.Parking:
        heading_vec = current_tra.get_forward_vector()
        heading_vec.z = 0
        heading_vec = heading_vec / math.sqrt(math.pow(heading_vec.x, 2) + math.pow(heading_vec.y, 2))
        perpendicular_vec = carla.Vector3D(-heading_vec.y, heading_vec.x, 0)
        extent = self.actor.bounding_box.extent
        x_boundary_vector = heading_vec * extent.x
        y_boundary_vector = perpendicular_vec * extent.y
        bbox = [current_loc + carla.Location(x_boundary_vector - y_boundary_vector), current_loc + carla.Location(x_boundary_vector + y_boundary_vector), current_loc + carla.Location(-1 * x_boundary_vector - y_boundary_vector), current_loc + carla.Location(-1 * x_boundary_vector + y_boundary_vector)]
        bbox_wp = [self._map.get_waypoint(bbox[0], lane_type=carla.LaneType.Any), self._map.get_waypoint(bbox[1], lane_type=carla.LaneType.Any), self._map.get_waypoint(bbox[2], lane_type=carla.LaneType.Any), self._map.get_waypoint(bbox[3], lane_type=carla.LaneType.Any)]
        if bbox_wp[0].lane_type == (carla.LaneType.Driving or carla.LaneType.Parking) or bbox_wp[1].lane_type == (carla.LaneType.Driving or carla.LaneType.Parking) or bbox_wp[2].lane_type == (carla.LaneType.Driving or carla.LaneType.Parking) or (bbox_wp[3].lane_type == (carla.LaneType.Driving or carla.LaneType.Parking)):
            self._onsidewalk_active = False
            self._outside_lane_active = False
        elif bbox_wp[0].lane_type == carla.LaneType.Sidewalk or bbox_wp[1].lane_type == carla.LaneType.Sidewalk or bbox_wp[2].lane_type == carla.LaneType.Sidewalk or (bbox_wp[3].lane_type == carla.LaneType.Sidewalk):
            if not self._onsidewalk_active:
                self._onsidewalk_active = True
                self._sidewalk_start_location = current_loc
        else:
            distance_vehicle_wp = current_loc.distance(current_wp.transform.location)
            if distance_vehicle_wp >= current_wp.lane_width / 2:
                if not self._outside_lane_active:
                    self._outside_lane_active = True
                    self._outside_lane_start_location = current_loc
            else:
                self._onsidewalk_active = False
                self._outside_lane_active = False
    elif current_wp.is_junction:
        distance_vehicle_wp = math.sqrt(math.pow(current_wp.transform.location.x - current_loc.x, 2) + math.pow(current_wp.transform.location.y - current_loc.y, 2))
        if distance_vehicle_wp <= current_wp.lane_width / 2:
            self._onsidewalk_active = False
            self._outside_lane_active = False
    else:
        self._onsidewalk_active = False
        self._outside_lane_active = False
    if self._onsidewalk_active or self._outside_lane_active:
        if self._prev_time is None:
            self._prev_time = GameTime.get_time()
        else:
            curr_time = GameTime.get_time()
            self._time_outside_lanes += curr_time - self._prev_time
            self._prev_time = curr_time
    else:
        self._prev_time = None
    if self._time_outside_lanes > self._duration:
        self.test_status = 'FAILURE'
    distance_vector = CarlaDataProvider.get_location(self._actor) - self._actor_location
    distance = math.sqrt(math.pow(distance_vector.x, 2) + math.pow(distance_vector.y, 2))
    if distance >= 0.02:
        self._actor_location = CarlaDataProvider.get_location(self._actor)
        if self._onsidewalk_active:
            self._wrong_sidewalk_distance += distance
        elif self._outside_lane_active:
            self._wrong_outside_lane_distance += distance
    if not self._onsidewalk_active and self._wrong_sidewalk_distance > 0:
        self.actual_value += 1
        onsidewalk_event = TrafficEvent(event_type=TrafficEventType.ON_SIDEWALK_INFRACTION)
        self._set_event_message(onsidewalk_event, self._sidewalk_start_location, self._wrong_sidewalk_distance)
        self._set_event_dict(onsidewalk_event, self._sidewalk_start_location, self._wrong_sidewalk_distance)
        self._onsidewalk_active = False
        self._wrong_sidewalk_distance = 0
        self.list_traffic_events.append(onsidewalk_event)
    if not self._outside_lane_active and self._wrong_outside_lane_distance > 0:
        self.actual_value += 1
        outsidelane_event = TrafficEvent(event_type=TrafficEventType.OUTSIDE_LANE_INFRACTION)
        self._set_event_message(outsidelane_event, self._outside_lane_start_location, self._wrong_outside_lane_distance)
        self._set_event_dict(outsidelane_event, self._outside_lane_start_location, self._wrong_outside_lane_distance)
        self._outside_lane_active = False
        self._wrong_outside_lane_distance = 0
        self.list_traffic_events.append(outsidelane_event)
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    return new_status

def terminate(self, new_status):
    """
        If there is currently an event running, it is registered
        """
    if self._onsidewalk_active:
        self.actual_value += 1
        onsidewalk_event = TrafficEvent(event_type=TrafficEventType.ON_SIDEWALK_INFRACTION)
        self._set_event_message(onsidewalk_event, self._sidewalk_start_location, self._wrong_sidewalk_distance)
        self._set_event_dict(onsidewalk_event, self._sidewalk_start_location, self._wrong_sidewalk_distance)
        self._onsidewalk_active = False
        self._wrong_sidewalk_distance = 0
        self.list_traffic_events.append(onsidewalk_event)
    if self._outside_lane_active:
        self.actual_value += 1
        outsidelane_event = TrafficEvent(event_type=TrafficEventType.OUTSIDE_LANE_INFRACTION)
        self._set_event_message(outsidelane_event, self._outside_lane_start_location, self._wrong_outside_lane_distance)
        self._set_event_dict(outsidelane_event, self._outside_lane_start_location, self._wrong_outside_lane_distance)
        self._outside_lane_active = False
        self._wrong_outside_lane_distance = 0
        self.list_traffic_events.append(outsidelane_event)
    super(OnSidewalkTest, self).terminate(new_status)

def _set_event_message(self, event, location, distance):
    """
        Sets the message of the event
        """
    if event.get_type() == TrafficEventType.ON_SIDEWALK_INFRACTION:
        message_start = 'Agent invaded the sidewalk'
    else:
        message_start = 'Agent went outside the lane'
    event.set_message('{} for about {} meters, starting at (x={}, y={}, z={})'.format(message_start, round(distance, 3), round(location.x, 3), round(location.y, 3), round(location.z, 3)))

def _set_event_dict(self, event, location, distance):
    """
        Sets the dictionary of the event
        """
    event.set_dict({'x': location.x, 'y': location.y, 'z': location.z, 'distance': distance})

class OutsideRouteLanesTest(Criterion):
    """
    Atomic to detect if the vehicle is either on a sidewalk or at a wrong lane. The distance spent outside
    is computed and it is returned as a percentage of the route distance traveled.

    Args:
        actor (carla.ACtor): CARLA actor to be used for this test
        route (list [carla.Location, connection]): series of locations representing the route waypoints
        optional (bool): If True, the result is not considered for an overall pass/fail result
    """
    ALLOWED_OUT_DISTANCE = 1.3
    MAX_ALLOWED_VEHICLE_ANGLE = 120.0
    MAX_ALLOWED_WAYPOINT_ANGLE = 150.0
    WINDOWS_SIZE = 3

    def __init__(self, actor, route, optional=False, name='OutsideRouteLanesTest'):
        """
        Constructor
        """
        super(OutsideRouteLanesTest, self).__init__(name, actor, 0, None, optional)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._actor = actor
        self._route = route
        self._current_index = 0
        self._route_length = len(self._route)
        self._waypoints, _ = zip(*self._route)
        self._map = CarlaDataProvider.get_map()
        self._pre_ego_waypoint = self._map.get_waypoint(self._actor.get_location())
        self._outside_lane_active = False
        self._wrong_lane_active = False
        self._last_road_id = None
        self._last_lane_id = None
        self._total_distance = 0
        self._wrong_distance = 0

    def update(self):
        """
        Transforms the actor location and its four corners to waypoints. Depending on its types,
        the actor will be considered to be at driving lanes, sidewalk or offroad.

        returns:
            py_trees.common.Status.FAILURE: when the actor has left driving and terminate_on_failure is active
            py_trees.common.Status.RUNNING: the rest of the time
        """
        new_status = py_trees.common.Status.RUNNING
        if self._terminate_on_failure and self.test_status == 'FAILURE':
            new_status = py_trees.common.Status.FAILURE
        location = CarlaDataProvider.get_location(self._actor)
        if location is None:
            return new_status
        self._is_outside_driving_lanes(location)
        self._is_at_wrong_lane(location)
        if self._outside_lane_active or self._wrong_lane_active:
            self.test_status = 'FAILURE'
        for index in range(self._current_index + 1, min(self._current_index + self.WINDOWS_SIZE + 1, self._route_length)):
            index_location = self._waypoints[index]
            index_waypoint = self._map.get_waypoint(index_location)
            wp_dir = index_waypoint.transform.get_forward_vector()
            wp_veh = location - index_location
            dot_ve_wp = wp_veh.x * wp_dir.x + wp_veh.y * wp_dir.y + wp_veh.z * wp_dir.z
            if dot_ve_wp > 0:
                index_location = self._waypoints[index]
                current_index_location = self._waypoints[self._current_index]
                new_dist = current_index_location.distance(index_location)
                self._current_index = index
                self._total_distance += new_dist
                if self._outside_lane_active or self._wrong_lane_active:
                    self._wrong_distance += new_dist
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

    def _is_outside_driving_lanes(self, location):
        """
        Detects if the ego_vehicle is outside driving lanes
        """
        current_driving_wp = self._map.get_waypoint(location, lane_type=carla.LaneType.Driving, project_to_road=True)
        current_parking_wp = self._map.get_waypoint(location, lane_type=carla.LaneType.Parking, project_to_road=True)
        driving_distance = location.distance(current_driving_wp.transform.location)
        if current_parking_wp is not None:
            parking_distance = location.distance(current_parking_wp.transform.location)
        else:
            parking_distance = float('inf')
        if driving_distance >= parking_distance:
            distance = parking_distance
            lane_width = current_parking_wp.lane_width
        else:
            distance = driving_distance
            lane_width = current_driving_wp.lane_width
        self._outside_lane_active = bool(distance > lane_width / 2 + self.ALLOWED_OUT_DISTANCE)

    def _is_at_wrong_lane(self, location):
        """
        Detects if the ego_vehicle has invaded a wrong lane
        """
        current_waypoint = self._map.get_waypoint(location, lane_type=carla.LaneType.Driving, project_to_road=True)
        current_lane_id = current_waypoint.lane_id
        current_road_id = current_waypoint.road_id
        if current_waypoint.is_junction:
            self._wrong_lane_active = False
        elif self._last_road_id != current_road_id or self._last_lane_id != current_lane_id:
            if self._pre_ego_waypoint.is_junction:
                yaw_waypt = current_waypoint.transform.rotation.yaw % 360
                yaw_actor = self._actor.get_transform().rotation.yaw % 360
                vehicle_lane_angle = (yaw_waypt - yaw_actor) % 360
                if vehicle_lane_angle < self.MAX_ALLOWED_VEHICLE_ANGLE or vehicle_lane_angle > 360 - self.MAX_ALLOWED_VEHICLE_ANGLE:
                    self._wrong_lane_active = False
                else:
                    self._wrong_lane_active = True
            else:
                yaw_pre_wp = self._pre_ego_waypoint.transform.rotation.yaw % 360
                yaw_cur_wp = current_waypoint.transform.rotation.yaw % 360
                waypoint_angle = (yaw_pre_wp - yaw_cur_wp) % 360
                if waypoint_angle >= self.MAX_ALLOWED_WAYPOINT_ANGLE and waypoint_angle <= 360 - self.MAX_ALLOWED_WAYPOINT_ANGLE:
                    self._wrong_lane_active = not bool(self._wrong_lane_active)
                else:
                    self._wrong_lane_active = False
        self._last_lane_id = current_lane_id
        self._last_road_id = current_road_id
        self._pre_ego_waypoint = current_waypoint

    def terminate(self, new_status):
        """
        If there is currently an event running, it is registered
        """
        if self._wrong_distance > 0:
            percentage = self._wrong_distance / self._total_distance * 100
            outside_lane = TrafficEvent(event_type=TrafficEventType.OUTSIDE_ROUTE_LANES_INFRACTION)
            outside_lane.set_message('Agent went outside its route lanes for about {} meters ({}% of the completed route)'.format(round(self._wrong_distance, 3), round(percentage, 2)))
            outside_lane.set_dict({'distance': self._wrong_distance, 'percentage': percentage})
            self._wrong_distance = 0
            self.list_traffic_events.append(outside_lane)
            self.actual_value = round(percentage, 2)
        super(OutsideRouteLanesTest, self).terminate(new_status)

def terminate(self, new_status):
    """
        If there is currently an event running, it is registered
        """
    if self._wrong_distance > 0:
        percentage = self._wrong_distance / self._total_distance * 100
        outside_lane = TrafficEvent(event_type=TrafficEventType.OUTSIDE_ROUTE_LANES_INFRACTION)
        outside_lane.set_message('Agent went outside its route lanes for about {} meters ({}% of the completed route)'.format(round(self._wrong_distance, 3), round(percentage, 2)))
        outside_lane.set_dict({'distance': self._wrong_distance, 'percentage': percentage})
        self._wrong_distance = 0
        self.list_traffic_events.append(outside_lane)
        self.actual_value = round(percentage, 2)
    super(OutsideRouteLanesTest, self).terminate(new_status)

class WrongLaneTest(Criterion):
    """
    This class contains an atomic test to detect invasions to wrong direction lanes.

    Important parameters:
    - actor: CARLA actor to be used for this test
    - optional [optional]: If True, the result is not considered for an overall pass/fail result
    """
    MAX_ALLOWED_ANGLE = 120.0
    MAX_ALLOWED_WAYPOINT_ANGLE = 150.0

    def __init__(self, actor, optional=False, name='WrongLaneTest'):
        """
        Construction with sensor setup
        """
        super(WrongLaneTest, self).__init__(name, actor, 0, None, optional)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._actor = actor
        self._map = CarlaDataProvider.get_map()
        self._last_lane_id = None
        self._last_road_id = None
        self._in_lane = True
        self._wrong_distance = 0
        self._actor_location = self._actor.get_location()
        self._previous_lane_waypoint = self._map.get_waypoint(self._actor.get_location())
        self._wrong_lane_start_location = None

    def update(self):
        """
        Check lane invasion count
        """
        new_status = py_trees.common.Status.RUNNING
        if self._terminate_on_failure and self.test_status == 'FAILURE':
            new_status = py_trees.common.Status.FAILURE
        lane_waypoint = self._map.get_waypoint(self._actor.get_location())
        current_lane_id = lane_waypoint.lane_id
        current_road_id = lane_waypoint.road_id
        if (self._last_road_id != current_road_id or self._last_lane_id != current_lane_id) and (not lane_waypoint.is_junction):
            next_waypoint = lane_waypoint.next(2.0)[0]
            if not next_waypoint:
                return new_status
            previous_lane_direction = self._previous_lane_waypoint.transform.get_forward_vector()
            current_lane_direction = lane_waypoint.transform.get_forward_vector()
            p_lane_vector = np.array([previous_lane_direction.x, previous_lane_direction.y])
            c_lane_vector = np.array([current_lane_direction.x, current_lane_direction.y])
            waypoint_angle = math.degrees(math.acos(np.clip(np.dot(p_lane_vector, c_lane_vector) / (np.linalg.norm(p_lane_vector) * np.linalg.norm(c_lane_vector)), -1.0, 1.0)))
            if waypoint_angle > self.MAX_ALLOWED_WAYPOINT_ANGLE and self._in_lane:
                self.test_status = 'FAILURE'
                self._in_lane = False
                self.actual_value += 1
                self._wrong_lane_start_location = self._actor_location
            else:
                self._in_lane = True
            if self._previous_lane_waypoint.is_junction:
                vector_wp = np.array([next_waypoint.transform.location.x - lane_waypoint.transform.location.x, next_waypoint.transform.location.y - lane_waypoint.transform.location.y])
                vector_actor = np.array([math.cos(math.radians(self._actor.get_transform().rotation.yaw)), math.sin(math.radians(self._actor.get_transform().rotation.yaw))])
                vehicle_lane_angle = math.degrees(math.acos(np.clip(np.dot(vector_actor, vector_wp) / np.linalg.norm(vector_wp), -1.0, 1.0)))
                if vehicle_lane_angle > self.MAX_ALLOWED_ANGLE:
                    self.test_status = 'FAILURE'
                    self._in_lane = False
                    self.actual_value += 1
                    self._wrong_lane_start_location = self._actor.get_location()
        distance_vector = self._actor.get_location() - self._actor_location
        distance = math.sqrt(math.pow(distance_vector.x, 2) + math.pow(distance_vector.y, 2))
        if distance >= 0.02:
            self._actor_location = CarlaDataProvider.get_location(self._actor)
            if not self._in_lane and (not lane_waypoint.is_junction):
                self._wrong_distance += distance
        if self._in_lane and self._wrong_distance > 0:
            wrong_way_event = TrafficEvent(event_type=TrafficEventType.WRONG_WAY_INFRACTION)
            self._set_event_message(wrong_way_event, self._wrong_lane_start_location, self._wrong_distance, current_road_id, current_lane_id)
            self._set_event_dict(wrong_way_event, self._wrong_lane_start_location, self._wrong_distance, current_road_id, current_lane_id)
            self.list_traffic_events.append(wrong_way_event)
            self._wrong_distance = 0
        self._last_lane_id = current_lane_id
        self._last_road_id = current_road_id
        self._previous_lane_waypoint = lane_waypoint
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

    def terminate(self, new_status):
        """
        If there is currently an event running, it is registered
        """
        if not self._in_lane:
            lane_waypoint = self._map.get_waypoint(self._actor.get_location())
            current_lane_id = lane_waypoint.lane_id
            current_road_id = lane_waypoint.road_id
            wrong_way_event = TrafficEvent(event_type=TrafficEventType.WRONG_WAY_INFRACTION)
            self._set_event_message(wrong_way_event, self._wrong_lane_start_location, self._wrong_distance, current_road_id, current_lane_id)
            self._set_event_dict(wrong_way_event, self._wrong_lane_start_location, self._wrong_distance, current_road_id, current_lane_id)
            self._wrong_distance = 0
            self._in_lane = True
            self.list_traffic_events.append(wrong_way_event)
        super(WrongLaneTest, self).terminate(new_status)

    def _set_event_message(self, event, location, distance, road_id, lane_id):
        """
        Sets the message of the event
        """
        event.set_message('Agent invaded a lane in opposite direction for {} meters, starting at (x={}, y={}, z={}). road_id={}, lane_id={}'.format(round(distance, 3), round(location.x, 3), round(location.y, 3), round(location.z, 3), road_id, lane_id))

    def _set_event_dict(self, event, location, distance, road_id, lane_id):
        """
        Sets the dictionary of the event
        """
        event.set_dict({'x': location.x, 'y': location.y, 'z': location.y, 'distance': distance, 'road_id': road_id, 'lane_id': lane_id})

def terminate(self, new_status):
    """
        If there is currently an event running, it is registered
        """
    if not self._in_lane:
        lane_waypoint = self._map.get_waypoint(self._actor.get_location())
        current_lane_id = lane_waypoint.lane_id
        current_road_id = lane_waypoint.road_id
        wrong_way_event = TrafficEvent(event_type=TrafficEventType.WRONG_WAY_INFRACTION)
        self._set_event_message(wrong_way_event, self._wrong_lane_start_location, self._wrong_distance, current_road_id, current_lane_id)
        self._set_event_dict(wrong_way_event, self._wrong_lane_start_location, self._wrong_distance, current_road_id, current_lane_id)
        self._wrong_distance = 0
        self._in_lane = True
        self.list_traffic_events.append(wrong_way_event)
    super(WrongLaneTest, self).terminate(new_status)

def _set_event_message(self, event, location, distance, road_id, lane_id):
    """
        Sets the message of the event
        """
    event.set_message('Agent invaded a lane in opposite direction for {} meters, starting at (x={}, y={}, z={}). road_id={}, lane_id={}'.format(round(distance, 3), round(location.x, 3), round(location.y, 3), round(location.z, 3), road_id, lane_id))

def _set_event_dict(self, event, location, distance, road_id, lane_id):
    """
        Sets the dictionary of the event
        """
    event.set_dict({'x': location.x, 'y': location.y, 'z': location.y, 'distance': distance, 'road_id': road_id, 'lane_id': lane_id})

class InRadiusRegionTest(Criterion):
    """
    The test is a success if the actor is within a given radius of a specified region

    Important parameters:
    - actor: CARLA actor to be used for this test
    - x, y, radius: Position (x,y) and radius (in meters) used to get the checked region
    """

    def __init__(self, actor, x, y, radius, name='InRadiusRegionTest'):
        """
        """
        super(InRadiusRegionTest, self).__init__(name, actor, 0)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._actor = actor
        self._x = x
        self._y = y
        self._radius = radius

    def update(self):
        """
        Check if the actor location is within trigger region
        """
        new_status = py_trees.common.Status.RUNNING
        location = CarlaDataProvider.get_location(self._actor)
        if location is None:
            return new_status
        if self.test_status != 'SUCCESS':
            in_radius = math.sqrt((location.x - self._x) ** 2 + (location.y - self._y) ** 2) < self._radius
            if in_radius:
                route_completion_event = TrafficEvent(event_type=TrafficEventType.ROUTE_COMPLETED)
                route_completion_event.set_message('Destination was successfully reached')
                self.list_traffic_events.append(route_completion_event)
                self.test_status = 'SUCCESS'
            else:
                self.test_status = 'RUNNING'
        if self.test_status == 'SUCCESS':
            new_status = py_trees.common.Status.SUCCESS
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

def update(self):
    """
        Check if the actor location is within trigger region
        """
    new_status = py_trees.common.Status.RUNNING
    location = CarlaDataProvider.get_location(self._actor)
    if location is None:
        return new_status
    if self.test_status != 'SUCCESS':
        in_radius = math.sqrt((location.x - self._x) ** 2 + (location.y - self._y) ** 2) < self._radius
        if in_radius:
            route_completion_event = TrafficEvent(event_type=TrafficEventType.ROUTE_COMPLETED)
            route_completion_event.set_message('Destination was successfully reached')
            self.list_traffic_events.append(route_completion_event)
            self.test_status = 'SUCCESS'
        else:
            self.test_status = 'RUNNING'
    if self.test_status == 'SUCCESS':
        new_status = py_trees.common.Status.SUCCESS
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    return new_status

class InRouteTest(Criterion):
    """
    The test is a success if the actor is never outside route. The actor can go outside of the route
    but only for a certain amount of distance

    Important parameters:
    - actor: CARLA actor to be used for this test
    - route: Route to be checked
    - offroad_max: Maximum distance (in meters) the actor can deviate from the route
    - offroad_min: Maximum safe distance (in meters). Might eventually cause failure
    - terminate_on_failure [optional]: If True, the complete scenario will terminate upon failure of this test
    """
    MAX_ROUTE_PERCENTAGE = 30
    WINDOWS_SIZE = 5

    def __init__(self, actor, route, offroad_min=-1, offroad_max=30, name='InRouteTest', terminate_on_failure=False):
        """
        """
        super(InRouteTest, self).__init__(name, actor, 0, terminate_on_failure=terminate_on_failure)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._actor = actor
        self._route = route
        self._offroad_max = offroad_max
        if offroad_min == -1:
            self._offroad_min = self._offroad_max / 2
        else:
            self._offroad_min = self._offroad_min
        self._world = CarlaDataProvider.get_world()
        self._waypoints, _ = zip(*self._route)
        self._route_length = len(self._route)
        self._current_index = 0
        self._out_route_distance = 0
        self._in_safe_route = True
        self._accum_meters = []
        prev_wp = self._waypoints[0]
        for i, wp in enumerate(self._waypoints):
            d = wp.distance(prev_wp)
            if i > 0:
                accum = self._accum_meters[i - 1]
            else:
                accum = 0
            self._accum_meters.append(d + accum)
            prev_wp = wp
        blackv = py_trees.blackboard.Blackboard()
        _ = blackv.set('InRoute', True)

    def update(self):
        """
        Check if the actor location is within trigger region
        """
        new_status = py_trees.common.Status.RUNNING
        location = CarlaDataProvider.get_location(self._actor)
        if location is None:
            return new_status
        if self._terminate_on_failure and self.test_status == 'FAILURE':
            new_status = py_trees.common.Status.FAILURE
        elif self.test_status == 'RUNNING' or self.test_status == 'INIT':
            off_route = True
            shortest_distance = float('inf')
            closest_index = -1
            for index in range(self._current_index, min(self._current_index + self.WINDOWS_SIZE + 1, self._route_length)):
                ref_waypoint = self._waypoints[index]
                distance = math.sqrt((location.x - ref_waypoint.x) ** 2 + (location.y - ref_waypoint.y) ** 2)
                if distance <= shortest_distance:
                    closest_index = index
                    shortest_distance = distance
            if closest_index == -1 or shortest_distance == float('inf'):
                return new_status
            if shortest_distance < self._offroad_max:
                off_route = False
                self._in_safe_route = bool(shortest_distance < self._offroad_min)
            if self._current_index != closest_index:
                new_dist = self._accum_meters[closest_index] - self._accum_meters[self._current_index]
                if not self._in_safe_route:
                    self._out_route_distance += new_dist
                    out_route_percentage = 100 * self._out_route_distance / self._accum_meters[-1]
                    if out_route_percentage > self.MAX_ROUTE_PERCENTAGE:
                        off_route = True
                self._current_index = closest_index
            if off_route:
                blackv = py_trees.blackboard.Blackboard()
                _ = blackv.set('InRoute', False)
                route_deviation_event = TrafficEvent(event_type=TrafficEventType.ROUTE_DEVIATION)
                route_deviation_event.set_message('Agent deviated from the route at (x={}, y={}, z={})'.format(round(location.x, 3), round(location.y, 3), round(location.z, 3)))
                route_deviation_event.set_dict({'x': location.x, 'y': location.y, 'z': location.z})
                self.list_traffic_events.append(route_deviation_event)
                self.test_status = 'FAILURE'
                self.actual_value += 1
                new_status = py_trees.common.Status.FAILURE
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

def update(self):
    """
        Check if the actor location is within trigger region
        """
    new_status = py_trees.common.Status.RUNNING
    location = CarlaDataProvider.get_location(self._actor)
    if location is None:
        return new_status
    if self._terminate_on_failure and self.test_status == 'FAILURE':
        new_status = py_trees.common.Status.FAILURE
    elif self.test_status == 'RUNNING' or self.test_status == 'INIT':
        off_route = True
        shortest_distance = float('inf')
        closest_index = -1
        for index in range(self._current_index, min(self._current_index + self.WINDOWS_SIZE + 1, self._route_length)):
            ref_waypoint = self._waypoints[index]
            distance = math.sqrt((location.x - ref_waypoint.x) ** 2 + (location.y - ref_waypoint.y) ** 2)
            if distance <= shortest_distance:
                closest_index = index
                shortest_distance = distance
        if closest_index == -1 or shortest_distance == float('inf'):
            return new_status
        if shortest_distance < self._offroad_max:
            off_route = False
            self._in_safe_route = bool(shortest_distance < self._offroad_min)
        if self._current_index != closest_index:
            new_dist = self._accum_meters[closest_index] - self._accum_meters[self._current_index]
            if not self._in_safe_route:
                self._out_route_distance += new_dist
                out_route_percentage = 100 * self._out_route_distance / self._accum_meters[-1]
                if out_route_percentage > self.MAX_ROUTE_PERCENTAGE:
                    off_route = True
            self._current_index = closest_index
        if off_route:
            blackv = py_trees.blackboard.Blackboard()
            _ = blackv.set('InRoute', False)
            route_deviation_event = TrafficEvent(event_type=TrafficEventType.ROUTE_DEVIATION)
            route_deviation_event.set_message('Agent deviated from the route at (x={}, y={}, z={})'.format(round(location.x, 3), round(location.y, 3), round(location.z, 3)))
            route_deviation_event.set_dict({'x': location.x, 'y': location.y, 'z': location.z})
            self.list_traffic_events.append(route_deviation_event)
            self.test_status = 'FAILURE'
            self.actual_value += 1
            new_status = py_trees.common.Status.FAILURE
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    return new_status

class RouteCompletionTest(Criterion):
    """
    Check at which stage of the route is the actor at each tick

    Important parameters:
    - actor: CARLA actor to be used for this test
    - route: Route to be checked
    - terminate_on_failure [optional]: If True, the complete scenario will terminate upon failure of this test
    """
    DISTANCE_THRESHOLD = 10.0
    WINDOWS_SIZE = 2

    def __init__(self, actor, route, name='RouteCompletionTest', terminate_on_failure=False):
        """
        """
        super(RouteCompletionTest, self).__init__(name, actor, 100, terminate_on_failure=terminate_on_failure)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._actor = actor
        self._route = route
        self._map = CarlaDataProvider.get_map()
        self._wsize = self.WINDOWS_SIZE
        self._current_index = 0
        self._route_length = len(self._route)
        self._waypoints, _ = zip(*self._route)
        self.target = self._waypoints[-1]
        self._accum_meters = []
        prev_wp = self._waypoints[0]
        for i, wp in enumerate(self._waypoints):
            d = wp.distance(prev_wp)
            if i > 0:
                accum = self._accum_meters[i - 1]
            else:
                accum = 0
            self._accum_meters.append(d + accum)
            prev_wp = wp
        self._traffic_event = TrafficEvent(event_type=TrafficEventType.ROUTE_COMPLETION)
        self.list_traffic_events.append(self._traffic_event)
        self._percentage_route_completed = 0.0

    def update(self):
        """
        Check if the actor location is within trigger region
        """
        new_status = py_trees.common.Status.RUNNING
        location = CarlaDataProvider.get_location(self._actor)
        if location is None:
            return new_status
        if self._terminate_on_failure and self.test_status == 'FAILURE':
            new_status = py_trees.common.Status.FAILURE
        elif self.test_status == 'RUNNING' or self.test_status == 'INIT':
            for index in range(self._current_index, min(self._current_index + self._wsize + 1, self._route_length)):
                ref_waypoint = self._waypoints[index]
                wp = self._map.get_waypoint(ref_waypoint)
                wp_dir = wp.transform.get_forward_vector()
                wp_veh = location - ref_waypoint
                dot_ve_wp = wp_veh.x * wp_dir.x + wp_veh.y * wp_dir.y + wp_veh.z * wp_dir.z
                if dot_ve_wp > 0:
                    self._current_index = index
                    self._percentage_route_completed = 100.0 * float(self._accum_meters[self._current_index]) / float(self._accum_meters[-1])
                    self._traffic_event.set_dict({'route_completed': self._percentage_route_completed})
                    self._traffic_event.set_message('Agent has completed > {:.2f}% of the route'.format(self._percentage_route_completed))
            if self._percentage_route_completed > 99.0 and location.distance(self.target) < self.DISTANCE_THRESHOLD:
                route_completion_event = TrafficEvent(event_type=TrafficEventType.ROUTE_COMPLETED)
                route_completion_event.set_message('Destination was successfully reached')
                self.list_traffic_events.append(route_completion_event)
                self.test_status = 'SUCCESS'
                self._percentage_route_completed = 100
        elif self.test_status == 'SUCCESS':
            new_status = py_trees.common.Status.SUCCESS
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

    def terminate(self, new_status):
        """
        Set test status to failure if not successful and terminate
        """
        self.actual_value = round(self._percentage_route_completed, 2)
        if self.test_status == 'INIT':
            self.test_status = 'FAILURE'
        super(RouteCompletionTest, self).terminate(new_status)

def update(self):
    """
        Check if the actor location is within trigger region
        """
    new_status = py_trees.common.Status.RUNNING
    location = CarlaDataProvider.get_location(self._actor)
    if location is None:
        return new_status
    if self._terminate_on_failure and self.test_status == 'FAILURE':
        new_status = py_trees.common.Status.FAILURE
    elif self.test_status == 'RUNNING' or self.test_status == 'INIT':
        for index in range(self._current_index, min(self._current_index + self._wsize + 1, self._route_length)):
            ref_waypoint = self._waypoints[index]
            wp = self._map.get_waypoint(ref_waypoint)
            wp_dir = wp.transform.get_forward_vector()
            wp_veh = location - ref_waypoint
            dot_ve_wp = wp_veh.x * wp_dir.x + wp_veh.y * wp_dir.y + wp_veh.z * wp_dir.z
            if dot_ve_wp > 0:
                self._current_index = index
                self._percentage_route_completed = 100.0 * float(self._accum_meters[self._current_index]) / float(self._accum_meters[-1])
                self._traffic_event.set_dict({'route_completed': self._percentage_route_completed})
                self._traffic_event.set_message('Agent has completed > {:.2f}% of the route'.format(self._percentage_route_completed))
        if self._percentage_route_completed > 99.0 and location.distance(self.target) < self.DISTANCE_THRESHOLD:
            route_completion_event = TrafficEvent(event_type=TrafficEventType.ROUTE_COMPLETED)
            route_completion_event.set_message('Destination was successfully reached')
            self.list_traffic_events.append(route_completion_event)
            self.test_status = 'SUCCESS'
            self._percentage_route_completed = 100
    elif self.test_status == 'SUCCESS':
        new_status = py_trees.common.Status.SUCCESS
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    return new_status

class RunningRedLightTest(Criterion):
    """
    Check if an actor is running a red light

    Important parameters:
    - actor: CARLA actor to be used for this test
    - terminate_on_failure [optional]: If True, the complete scenario will terminate upon failure of this test
    """
    DISTANCE_LIGHT = 15

    def __init__(self, actor, name='RunningRedLightTest', terminate_on_failure=False):
        """
        Init
        """
        super(RunningRedLightTest, self).__init__(name, actor, 0, terminate_on_failure=terminate_on_failure)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._actor = actor
        self._world = actor.get_world()
        self._map = CarlaDataProvider.get_map()
        self._list_traffic_lights = []
        self._last_red_light_id = None
        self.actual_value = 0
        self.debug = False
        all_actors = self._world.get_actors()
        for _actor in all_actors:
            if 'traffic_light' in _actor.type_id:
                center, waypoints = self.get_traffic_light_waypoints(_actor)
                self._list_traffic_lights.append((_actor, center, waypoints))

    def is_vehicle_crossing_line(self, seg1, seg2):
        """
        check if vehicle crosses a line segment
        """
        line1 = shapely.geometry.LineString([(seg1[0].x, seg1[0].y), (seg1[1].x, seg1[1].y)])
        line2 = shapely.geometry.LineString([(seg2[0].x, seg2[0].y), (seg2[1].x, seg2[1].y)])
        inter = line1.intersection(line2)
        return not inter.is_empty

    def update(self):
        """
        Check if the actor is running a red light
        """
        new_status = py_trees.common.Status.RUNNING
        transform = CarlaDataProvider.get_transform(self._actor)
        location = transform.location
        if location is None:
            return new_status
        veh_extent = self._actor.bounding_box.extent.x
        tail_close_pt = self.rotate_point(carla.Vector3D(-0.8 * veh_extent, 0.0, location.z), transform.rotation.yaw)
        tail_close_pt = location + carla.Location(tail_close_pt)
        tail_far_pt = self.rotate_point(carla.Vector3D(-veh_extent - 1, 0.0, location.z), transform.rotation.yaw)
        tail_far_pt = location + carla.Location(tail_far_pt)
        for traffic_light, center, waypoints in self._list_traffic_lights:
            if self.debug:
                z = 2.1
                if traffic_light.state == carla.TrafficLightState.Red:
                    color = carla.Color(155, 0, 0)
                elif traffic_light.state == carla.TrafficLightState.Green:
                    color = carla.Color(0, 155, 0)
                else:
                    color = carla.Color(155, 155, 0)
                self._world.debug.draw_point(center + carla.Location(z=z), size=0.2, color=color, life_time=0.01)
                for wp in waypoints:
                    text = '{}.{}'.format(wp.road_id, wp.lane_id)
                    self._world.debug.draw_string(wp.transform.location + carla.Location(x=1, z=z), text, color=color, life_time=0.01)
                    self._world.debug.draw_point(wp.transform.location + carla.Location(z=z), size=0.1, color=color, life_time=0.01)
            center_loc = carla.Location(center)
            if self._last_red_light_id and self._last_red_light_id == traffic_light.id:
                continue
            if center_loc.distance(location) > self.DISTANCE_LIGHT:
                continue
            if traffic_light.state != carla.TrafficLightState.Red:
                continue
            for wp in waypoints:
                tail_wp = self._map.get_waypoint(tail_far_pt)
                ve_dir = CarlaDataProvider.get_transform(self._actor).get_forward_vector()
                wp_dir = wp.transform.get_forward_vector()
                dot_ve_wp = ve_dir.x * wp_dir.x + ve_dir.y * wp_dir.y + ve_dir.z * wp_dir.z
                if tail_wp.road_id == wp.road_id and tail_wp.lane_id == wp.lane_id and (dot_ve_wp > 0):
                    yaw_wp = wp.transform.rotation.yaw
                    lane_width = wp.lane_width
                    location_wp = wp.transform.location
                    lft_lane_wp = self.rotate_point(carla.Vector3D(0.4 * lane_width, 0.0, location_wp.z), yaw_wp + 90)
                    lft_lane_wp = location_wp + carla.Location(lft_lane_wp)
                    rgt_lane_wp = self.rotate_point(carla.Vector3D(0.4 * lane_width, 0.0, location_wp.z), yaw_wp - 90)
                    rgt_lane_wp = location_wp + carla.Location(rgt_lane_wp)
                    if self.is_vehicle_crossing_line((tail_close_pt, tail_far_pt), (lft_lane_wp, rgt_lane_wp)):
                        self.test_status = 'FAILURE'
                        self.actual_value += 1
                        location = traffic_light.get_transform().location
                        red_light_event = TrafficEvent(event_type=TrafficEventType.TRAFFIC_LIGHT_INFRACTION)
                        red_light_event.set_message('Agent ran a red light {} at (x={}, y={}, z={})'.format(traffic_light.id, round(location.x, 3), round(location.y, 3), round(location.z, 3)))
                        red_light_event.set_dict({'id': traffic_light.id, 'x': location.x, 'y': location.y, 'z': location.z})
                        self.list_traffic_events.append(red_light_event)
                        self._last_red_light_id = traffic_light.id
                        break
        if self._terminate_on_failure and self.test_status == 'FAILURE':
            new_status = py_trees.common.Status.FAILURE
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

    def rotate_point(self, point, angle):
        """
        rotate a given point by a given angle
        """
        x_ = math.cos(math.radians(angle)) * point.x - math.sin(math.radians(angle)) * point.y
        y_ = math.sin(math.radians(angle)) * point.x + math.cos(math.radians(angle)) * point.y
        return carla.Vector3D(x_, y_, point.z)

    def get_traffic_light_waypoints(self, traffic_light):
        """
        get area of a given traffic light
        """
        base_transform = traffic_light.get_transform()
        base_rot = base_transform.rotation.yaw
        area_loc = base_transform.transform(traffic_light.trigger_volume.location)
        area_ext = traffic_light.trigger_volume.extent
        x_values = np.arange(-0.9 * area_ext.x, 0.9 * area_ext.x, 1.0)
        area = []
        for x in x_values:
            point = self.rotate_point(carla.Vector3D(x, 0, area_ext.z), base_rot)
            point_location = area_loc + carla.Location(x=point.x, y=point.y)
            area.append(point_location)
        ini_wps = []
        for pt in area:
            wpx = self._map.get_waypoint(pt)
            if not ini_wps or ini_wps[-1].road_id != wpx.road_id or ini_wps[-1].lane_id != wpx.lane_id:
                ini_wps.append(wpx)
        wps = []
        for wpx in ini_wps:
            while not wpx.is_intersection:
                next_wp = wpx.next(0.5)[0]
                if next_wp and (not next_wp.is_intersection):
                    wpx = next_wp
                else:
                    break
            wps.append(wpx)
        return (area_loc, wps)

def update(self):
    """
        Check if the actor is running a red light
        """
    new_status = py_trees.common.Status.RUNNING
    transform = CarlaDataProvider.get_transform(self._actor)
    location = transform.location
    if location is None:
        return new_status
    veh_extent = self._actor.bounding_box.extent.x
    tail_close_pt = self.rotate_point(carla.Vector3D(-0.8 * veh_extent, 0.0, location.z), transform.rotation.yaw)
    tail_close_pt = location + carla.Location(tail_close_pt)
    tail_far_pt = self.rotate_point(carla.Vector3D(-veh_extent - 1, 0.0, location.z), transform.rotation.yaw)
    tail_far_pt = location + carla.Location(tail_far_pt)
    for traffic_light, center, waypoints in self._list_traffic_lights:
        if self.debug:
            z = 2.1
            if traffic_light.state == carla.TrafficLightState.Red:
                color = carla.Color(155, 0, 0)
            elif traffic_light.state == carla.TrafficLightState.Green:
                color = carla.Color(0, 155, 0)
            else:
                color = carla.Color(155, 155, 0)
            self._world.debug.draw_point(center + carla.Location(z=z), size=0.2, color=color, life_time=0.01)
            for wp in waypoints:
                text = '{}.{}'.format(wp.road_id, wp.lane_id)
                self._world.debug.draw_string(wp.transform.location + carla.Location(x=1, z=z), text, color=color, life_time=0.01)
                self._world.debug.draw_point(wp.transform.location + carla.Location(z=z), size=0.1, color=color, life_time=0.01)
        center_loc = carla.Location(center)
        if self._last_red_light_id and self._last_red_light_id == traffic_light.id:
            continue
        if center_loc.distance(location) > self.DISTANCE_LIGHT:
            continue
        if traffic_light.state != carla.TrafficLightState.Red:
            continue
        for wp in waypoints:
            tail_wp = self._map.get_waypoint(tail_far_pt)
            ve_dir = CarlaDataProvider.get_transform(self._actor).get_forward_vector()
            wp_dir = wp.transform.get_forward_vector()
            dot_ve_wp = ve_dir.x * wp_dir.x + ve_dir.y * wp_dir.y + ve_dir.z * wp_dir.z
            if tail_wp.road_id == wp.road_id and tail_wp.lane_id == wp.lane_id and (dot_ve_wp > 0):
                yaw_wp = wp.transform.rotation.yaw
                lane_width = wp.lane_width
                location_wp = wp.transform.location
                lft_lane_wp = self.rotate_point(carla.Vector3D(0.4 * lane_width, 0.0, location_wp.z), yaw_wp + 90)
                lft_lane_wp = location_wp + carla.Location(lft_lane_wp)
                rgt_lane_wp = self.rotate_point(carla.Vector3D(0.4 * lane_width, 0.0, location_wp.z), yaw_wp - 90)
                rgt_lane_wp = location_wp + carla.Location(rgt_lane_wp)
                if self.is_vehicle_crossing_line((tail_close_pt, tail_far_pt), (lft_lane_wp, rgt_lane_wp)):
                    self.test_status = 'FAILURE'
                    self.actual_value += 1
                    location = traffic_light.get_transform().location
                    red_light_event = TrafficEvent(event_type=TrafficEventType.TRAFFIC_LIGHT_INFRACTION)
                    red_light_event.set_message('Agent ran a red light {} at (x={}, y={}, z={})'.format(traffic_light.id, round(location.x, 3), round(location.y, 3), round(location.z, 3)))
                    red_light_event.set_dict({'id': traffic_light.id, 'x': location.x, 'y': location.y, 'z': location.z})
                    self.list_traffic_events.append(red_light_event)
                    self._last_red_light_id = traffic_light.id
                    break
    if self._terminate_on_failure and self.test_status == 'FAILURE':
        new_status = py_trees.common.Status.FAILURE
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    return new_status

class RunningStopTest(Criterion):
    """
    Check if an actor is running a stop sign

    Important parameters:
    - actor: CARLA actor to be used for this test
    - terminate_on_failure [optional]: If True, the complete scenario will terminate upon failure of this test
    """
    PROXIMITY_THRESHOLD = 50.0
    SPEED_THRESHOLD = 0.1
    WAYPOINT_STEP = 1.0

    def __init__(self, actor, name='RunningStopTest', terminate_on_failure=False):
        """
        """
        super(RunningStopTest, self).__init__(name, actor, 0, terminate_on_failure=terminate_on_failure)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._actor = actor
        self._world = CarlaDataProvider.get_world()
        self._map = CarlaDataProvider.get_map()
        self._list_stop_signs = []
        self._target_stop_sign = None
        self._stop_completed = False
        self._affected_by_stop = False
        self.actual_value = 0
        all_actors = self._world.get_actors()
        for _actor in all_actors:
            if 'traffic.stop' in _actor.type_id:
                self._list_stop_signs.append(_actor)

    @staticmethod
    def point_inside_boundingbox(point, bb_center, bb_extent):
        """
        X
        :param point:
        :param bb_center:
        :param bb_extent:
        :return:
        """
        A = carla.Vector2D(bb_center.x - bb_extent.x, bb_center.y - bb_extent.y)
        B = carla.Vector2D(bb_center.x + bb_extent.x, bb_center.y - bb_extent.y)
        D = carla.Vector2D(bb_center.x - bb_extent.x, bb_center.y + bb_extent.y)
        M = carla.Vector2D(point.x, point.y)
        AB = B - A
        AD = D - A
        AM = M - A
        am_ab = AM.x * AB.x + AM.y * AB.y
        ab_ab = AB.x * AB.x + AB.y * AB.y
        am_ad = AM.x * AD.x + AM.y * AD.y
        ad_ad = AD.x * AD.x + AD.y * AD.y
        return am_ab > 0 and am_ab < ab_ab and (am_ad > 0) and (am_ad < ad_ad)

    def is_actor_affected_by_stop(self, actor, stop, multi_step=20):
        """
        Check if the given actor is affected by the stop
        """
        affected = False
        current_location = actor.get_location()
        stop_location = stop.get_transform().location
        if stop_location.distance(current_location) > self.PROXIMITY_THRESHOLD:
            return affected
        stop_t = stop.get_transform()
        transformed_tv = stop_t.transform(stop.trigger_volume.location)
        list_locations = [current_location]
        waypoint = self._map.get_waypoint(current_location)
        for _ in range(multi_step):
            if waypoint:
                next_wps = waypoint.next(self.WAYPOINT_STEP)
                if not next_wps:
                    break
                waypoint = next_wps[0]
                if not waypoint:
                    break
                list_locations.append(waypoint.transform.location)
        for actor_location in list_locations:
            if self.point_inside_boundingbox(actor_location, transformed_tv, stop.trigger_volume.extent):
                affected = True
        return affected

    def _scan_for_stop_sign(self):
        target_stop_sign = None
        ve_tra = CarlaDataProvider.get_transform(self._actor)
        ve_dir = ve_tra.get_forward_vector()
        wp = self._map.get_waypoint(ve_tra.location)
        wp_dir = wp.transform.get_forward_vector()
        dot_ve_wp = ve_dir.x * wp_dir.x + ve_dir.y * wp_dir.y + ve_dir.z * wp_dir.z
        if dot_ve_wp > 0:
            for stop_sign in self._list_stop_signs:
                if self.is_actor_affected_by_stop(self._actor, stop_sign):
                    target_stop_sign = stop_sign
                    break
        return target_stop_sign

    def update(self):
        """
        Check if the actor is running a red light
        """
        new_status = py_trees.common.Status.RUNNING
        location = self._actor.get_location()
        if location is None:
            return new_status
        if not self._target_stop_sign:
            self._target_stop_sign = self._scan_for_stop_sign()
        else:
            if not self._stop_completed:
                current_speed = CarlaDataProvider.get_velocity(self._actor)
                if current_speed < self.SPEED_THRESHOLD:
                    self._stop_completed = True
            if not self._affected_by_stop:
                stop_location = self._target_stop_sign.get_location()
                stop_extent = self._target_stop_sign.trigger_volume.extent
                if self.point_inside_boundingbox(location, stop_location, stop_extent):
                    self._affected_by_stop = True
            if not self.is_actor_affected_by_stop(self._actor, self._target_stop_sign):
                if not self._stop_completed and self._affected_by_stop:
                    self.actual_value += 1
                    self.test_status = 'FAILURE'
                    stop_location = self._target_stop_sign.get_transform().location
                    running_stop_event = TrafficEvent(event_type=TrafficEventType.STOP_INFRACTION)
                    running_stop_event.set_message('Agent ran a stop with id={} at (x={}, y={}, z={})'.format(self._target_stop_sign.id, round(stop_location.x, 3), round(stop_location.y, 3), round(stop_location.z, 3)))
                    running_stop_event.set_dict({'id': self._target_stop_sign.id, 'x': stop_location.x, 'y': stop_location.y, 'z': stop_location.z})
                    self.list_traffic_events.append(running_stop_event)
                self._target_stop_sign = None
                self._stop_completed = False
                self._affected_by_stop = False
        if self._terminate_on_failure and self.test_status == 'FAILURE':
            new_status = py_trees.common.Status.FAILURE
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

@staticmethod
def point_inside_boundingbox(point, bb_center, bb_extent):
    """
        X
        :param point:
        :param bb_center:
        :param bb_extent:
        :return:
        """
    A = carla.Vector2D(bb_center.x - bb_extent.x, bb_center.y - bb_extent.y)
    B = carla.Vector2D(bb_center.x + bb_extent.x, bb_center.y - bb_extent.y)
    D = carla.Vector2D(bb_center.x - bb_extent.x, bb_center.y + bb_extent.y)
    M = carla.Vector2D(point.x, point.y)
    AB = B - A
    AD = D - A
    AM = M - A
    am_ab = AM.x * AB.x + AM.y * AB.y
    ab_ab = AB.x * AB.x + AB.y * AB.y
    am_ad = AM.x * AD.x + AM.y * AD.y
    ad_ad = AD.x * AD.x + AD.y * AD.y
    return am_ab > 0 and am_ab < ab_ab and (am_ad > 0) and (am_ad < ad_ad)

def _scan_for_stop_sign(self):
    target_stop_sign = None
    ve_tra = CarlaDataProvider.get_transform(self._actor)
    ve_dir = ve_tra.get_forward_vector()
    wp = self._map.get_waypoint(ve_tra.location)
    wp_dir = wp.transform.get_forward_vector()
    dot_ve_wp = ve_dir.x * wp_dir.x + ve_dir.y * wp_dir.y + ve_dir.z * wp_dir.z
    if dot_ve_wp > 0:
        for stop_sign in self._list_stop_signs:
            if self.is_actor_affected_by_stop(self._actor, stop_sign):
                target_stop_sign = stop_sign
                break
    return target_stop_sign

def update(self):
    """
        Check if the actor is running a red light
        """
    new_status = py_trees.common.Status.RUNNING
    location = self._actor.get_location()
    if location is None:
        return new_status
    if not self._target_stop_sign:
        self._target_stop_sign = self._scan_for_stop_sign()
    else:
        if not self._stop_completed:
            current_speed = CarlaDataProvider.get_velocity(self._actor)
            if current_speed < self.SPEED_THRESHOLD:
                self._stop_completed = True
        if not self._affected_by_stop:
            stop_location = self._target_stop_sign.get_location()
            stop_extent = self._target_stop_sign.trigger_volume.extent
            if self.point_inside_boundingbox(location, stop_location, stop_extent):
                self._affected_by_stop = True
        if not self.is_actor_affected_by_stop(self._actor, self._target_stop_sign):
            if not self._stop_completed and self._affected_by_stop:
                self.actual_value += 1
                self.test_status = 'FAILURE'
                stop_location = self._target_stop_sign.get_transform().location
                running_stop_event = TrafficEvent(event_type=TrafficEventType.STOP_INFRACTION)
                running_stop_event.set_message('Agent ran a stop with id={} at (x={}, y={}, z={})'.format(self._target_stop_sign.id, round(stop_location.x, 3), round(stop_location.y, 3), round(stop_location.z, 3)))
                running_stop_event.set_dict({'id': self._target_stop_sign.id, 'x': stop_location.x, 'y': stop_location.y, 'z': stop_location.z})
                self.list_traffic_events.append(running_stop_event)
            self._target_stop_sign = None
            self._stop_completed = False
            self._affected_by_stop = False
    if self._terminate_on_failure and self.test_status == 'FAILURE':
        new_status = py_trees.common.Status.FAILURE
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    return new_status

class AccelerateToVelocity(AtomicBehavior):
    """
    This class contains an atomic acceleration behavior. The controlled
    traffic participant will accelerate with _throttle_value_ until reaching
    a given _target_velocity_

    Important parameters:
    - actor: CARLA actor to execute the behavior
    - throttle_value: The amount of throttle used to accelerate in [0,1]
    - target_velocity: The target velocity the actor should reach in m/s

    The behavior will terminate, if the actor's velocity is at least target_velocity
    """

    def __init__(self, actor, throttle_value, target_velocity, name='Acceleration'):
        """
        Setup parameters including acceleration value (via throttle_value)
        and target velocity
        """
        super(AccelerateToVelocity, self).__init__(name, actor)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._control, self._type = get_actor_control(actor)
        self._throttle_value = throttle_value
        self._target_velocity = target_velocity

    def initialise(self):
        if self._type == 'walker':
            self._control.speed = self._target_velocity
            self._control.direction = CarlaDataProvider.get_transform(self._actor).get_forward_vector()
        super(AccelerateToVelocity, self).initialise()

    def update(self):
        """
        Set throttle to throttle_value, as long as velocity is < target_velocity
        """
        new_status = py_trees.common.Status.RUNNING
        if self._type == 'vehicle':
            if CarlaDataProvider.get_velocity(self._actor) < self._target_velocity:
                self._control.throttle = self._throttle_value
            else:
                new_status = py_trees.common.Status.SUCCESS
                self._control.throttle = 0
        self._actor.apply_control(self._control)
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

def initialise(self):
    if self._type == 'walker':
        self._control.speed = self._target_velocity
        self._control.direction = CarlaDataProvider.get_transform(self._actor).get_forward_vector()
    super(AccelerateToVelocity, self).initialise()

class KeepVelocity(AtomicBehavior):
    """
    This class contains an atomic behavior to keep the provided velocity.
    The controlled traffic participant will accelerate as fast as possible
    until reaching a given _target_velocity_, which is then maintained for
    as long as this behavior is active.

    Important parameters:
    - actor: CARLA actor to execute the behavior
    - target_velocity: The target velocity the actor should reach
    - duration[optional]: Duration in seconds of this behavior
    - distance[optional]: Maximum distance in meters covered by the actor during this behavior

    A termination can be enforced by providing distance or duration values.
    Alternatively, a parallel termination behavior has to be used.
    """

    def __init__(self, actor, target_velocity, duration=float('inf'), distance=float('inf'), name='KeepVelocity'):
        """
        Setup parameters including acceleration value (via throttle_value)
        and target velocity
        """
        super(KeepVelocity, self).__init__(name, actor)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._target_velocity = target_velocity
        self._control, self._type = get_actor_control(actor)
        self._map = self._actor.get_world().get_map()
        self._waypoint = self._map.get_waypoint(self._actor.get_location())
        self._duration = duration
        self._target_distance = distance
        self._distance = 0
        self._start_time = 0
        self._location = None

    def initialise(self):
        self._location = CarlaDataProvider.get_location(self._actor)
        self._start_time = GameTime.get_time()
        if self._type == 'walker':
            self._control.speed = self._target_velocity
            self._control.direction = CarlaDataProvider.get_transform(self._actor).get_forward_vector()
        super(KeepVelocity, self).initialise()

    def update(self):
        """
        As long as the stop condition (duration or distance) is not violated, set a new vehicle control

        For vehicles: set throttle to throttle_value, as long as velocity is < target_velocity
        For walkers: simply apply the given self._control
        """
        new_status = py_trees.common.Status.RUNNING
        if self._type == 'vehicle':
            if CarlaDataProvider.get_velocity(self._actor) < self._target_velocity:
                self._control.throttle = 1.0
            else:
                self._control.throttle = 0.0
        self._actor.apply_control(self._control)
        new_location = CarlaDataProvider.get_location(self._actor)
        self._distance += calculate_distance(self._location, new_location)
        self._location = new_location
        if self._distance > self._target_distance:
            new_status = py_trees.common.Status.SUCCESS
        if GameTime.get_time() - self._start_time > self._duration:
            new_status = py_trees.common.Status.SUCCESS
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

    def terminate(self, new_status):
        """
        On termination of this behavior, the throttle should be set back to 0.,
        to avoid further acceleration.
        """
        if self._type == 'vehicle':
            self._control.throttle = 0.0
        elif self._type == 'walker':
            self._control.speed = 0.0
        if self._actor is not None and self._actor.is_alive:
            self._actor.apply_control(self._control)
        super(KeepVelocity, self).terminate(new_status)

def initialise(self):
    self._location = CarlaDataProvider.get_location(self._actor)
    self._start_time = GameTime.get_time()
    if self._type == 'walker':
        self._control.speed = self._target_velocity
        self._control.direction = CarlaDataProvider.get_transform(self._actor).get_forward_vector()
    super(KeepVelocity, self).initialise()

class WaypointFollower(AtomicBehavior):
    """
    This is an atomic behavior to follow waypoints while maintaining a given speed.
    If no plan is provided, the actor will follow its foward waypoints indefinetely.
    Otherwise, the behavior will end with SUCCESS upon reaching the end of the plan.
    If no target velocity is provided, the actor continues with its current velocity.

    Args:
        actor (carla.Actor):  CARLA actor to execute the behavior.
        target_speed (float, optional): Desired speed of the actor in m/s. Defaults to None.
        plan ([carla.Location] or [(carla.Waypoint, carla.agent.navigation.local_planner)], optional):
            Waypoint plan the actor should follow. Defaults to None.
        blackboard_queue_name (str, optional):
            Blackboard variable name, if additional actors should be created on-the-fly. Defaults to None.
        avoid_collision (bool, optional):
            Enable/Disable(=default) collision avoidance for vehicles/bikes. Defaults to False.
        name (str, optional): Name of the behavior. Defaults to "FollowWaypoints".

    Attributes:
        actor (carla.Actor):  CARLA actor to execute the behavior.
        name (str, optional): Name of the behavior.
        _target_speed (float, optional): Desired speed of the actor in m/s. Defaults to None.
        _plan ([carla.Location] or [(carla.Waypoint, carla.agent.navigation.local_planner)]):
            Waypoint plan the actor should follow. Defaults to None.
        _blackboard_queue_name (str):
            Blackboard variable name, if additional actors should be created on-the-fly. Defaults to None.
        _avoid_collision (bool): Enable/Disable(=default) collision avoidance for vehicles/bikes. Defaults to False.
        _actor_dict: Dictonary of all actors, and their corresponding plans (e.g. {actor: plan}).
        _local_planner_dict: Dictonary of all actors, and their corresponding local planners.
            Either "Walker" for pedestrians, or a carla.agent.navigation.LocalPlanner for other actors.
        _args_lateral_dict: Parameters for the PID of the used carla.agent.navigation.LocalPlanner.
        _unique_id: Unique ID of the behavior based on timestamp in nanoseconds.

    Note:
        OpenScenario:
        The WaypointFollower atomic must be called with an individual name if multiple consecutive WFs.
        Blackboard variables with lists are used for consecutive WaypointFollower behaviors.
        Termination of active WaypointFollowers in initialise of AtomicBehavior because any
        following behavior must terminate the WaypointFollower.
    """

    def __init__(self, actor, target_speed=None, plan=None, blackboard_queue_name=None, avoid_collision=False, name='FollowWaypoints'):
        """
        Set up actor and local planner
        """
        super(WaypointFollower, self).__init__(name, actor)
        self._actor_dict = {}
        self._actor_dict[actor] = None
        self._target_speed = target_speed
        self._local_planner_dict = {}
        self._local_planner_dict[actor] = None
        self._plan = plan
        self._blackboard_queue_name = blackboard_queue_name
        if blackboard_queue_name is not None:
            self._queue = Blackboard().get(blackboard_queue_name)
        self._args_lateral_dict = {'K_P': 1.0, 'K_D': 0.01, 'K_I': 0.0, 'dt': 0.05}
        self._avoid_collision = avoid_collision
        self._unique_id = 0

    def initialise(self):
        """
        Delayed one-time initialization

        Checks if another WaypointFollower behavior is already running for this actor.
        If this is the case, a termination signal is sent to the running behavior.
        """
        super(WaypointFollower, self).initialise()
        self._unique_id = int(round(time.time() * 1000000000.0))
        try:
            check_attr = operator.attrgetter('running_WF_actor_{}'.format(self._actor.id))
            running = check_attr(py_trees.blackboard.Blackboard())
            active_wf = copy.copy(running)
            active_wf.append(self._unique_id)
            py_trees.blackboard.Blackboard().set('running_WF_actor_{}'.format(self._actor.id), active_wf, overwrite=True)
        except AttributeError:
            py_trees.blackboard.Blackboard().set('terminate_WF_actor_{}'.format(self._actor.id), [], overwrite=True)
            py_trees.blackboard.Blackboard().set('running_WF_actor_{}'.format(self._actor.id), [self._unique_id], overwrite=True)
        for actor in self._actor_dict:
            self._apply_local_planner(actor)
        return True

    def _apply_local_planner(self, actor):
        """
        Convert the plan into locations for walkers (pedestrians), or to a waypoint list for other actors.
        For non-walkers, activate the carla.agent.navigation.LocalPlanner module.
        """
        if self._target_speed is None:
            self._target_speed = CarlaDataProvider.get_velocity(actor)
        else:
            self._target_speed = self._target_speed
        if isinstance(actor, carla.Walker):
            self._local_planner_dict[actor] = 'Walker'
            if self._plan is not None:
                if isinstance(self._plan[0], carla.Location):
                    self._actor_dict[actor] = self._plan
                else:
                    self._actor_dict[actor] = [element[0].transform.location for element in self._plan]
        else:
            local_planner = LocalPlanner(actor, opt_dict={'target_speed': self._target_speed * 3.6, 'lateral_control_dict': self._args_lateral_dict})
            if self._plan is not None:
                if isinstance(self._plan[0], carla.Location):
                    plan = []
                    for location in self._plan:
                        waypoint = CarlaDataProvider.get_map().get_waypoint(location, project_to_road=True, lane_type=carla.LaneType.Any)
                        plan.append((waypoint, RoadOption.LANEFOLLOW))
                    local_planner.set_global_plan(plan)
                else:
                    local_planner.set_global_plan(self._plan)
            self._local_planner_dict[actor] = local_planner
            self._actor_dict[actor] = self._plan

    def update(self):
        """
        Compute next control step for the given waypoint plan, obtain and apply control to actor
        """
        new_status = py_trees.common.Status.RUNNING
        check_term = operator.attrgetter('terminate_WF_actor_{}'.format(self._actor.id))
        terminate_wf = check_term(py_trees.blackboard.Blackboard())
        check_run = operator.attrgetter('running_WF_actor_{}'.format(self._actor.id))
        active_wf = check_run(py_trees.blackboard.Blackboard())
        if self._unique_id in terminate_wf:
            terminate_wf.remove(self._unique_id)
            if self._unique_id in active_wf:
                active_wf.remove(self._unique_id)
            py_trees.blackboard.Blackboard().set('terminate_WF_actor_{}'.format(self._actor.id), terminate_wf, overwrite=True)
            py_trees.blackboard.Blackboard().set('running_WF_actor_{}'.format(self._actor.id), active_wf, overwrite=True)
            new_status = py_trees.common.Status.SUCCESS
            return new_status
        if self._blackboard_queue_name is not None:
            while not self._queue.empty():
                actor = self._queue.get()
                if actor is not None and actor not in self._actor_dict:
                    self._apply_local_planner(actor)
        success = True
        for actor in self._local_planner_dict:
            local_planner = self._local_planner_dict[actor] if actor else None
            if actor is not None and actor.is_alive and (local_planner is not None):
                if not isinstance(actor, carla.Walker):
                    control = local_planner.run_step(debug=False)
                    if self._avoid_collision and detect_lane_obstacle(actor):
                        control.throttle = 0.0
                        control.brake = 1.0
                    actor.apply_control(control)
                    if local_planner._waypoints_queue:
                        success = False
                else:
                    actor_location = CarlaDataProvider.get_location(actor)
                    success = False
                    if self._actor_dict[actor]:
                        location = self._actor_dict[actor][0]
                        direction = location - actor_location
                        direction_norm = math.sqrt(direction.x ** 2 + direction.y ** 2)
                        control = actor.get_control()
                        control.speed = self._target_speed
                        control.direction = direction / direction_norm
                        actor.apply_control(control)
                        if direction_norm < 1.0:
                            self._actor_dict[actor] = self._actor_dict[actor][1:]
                            if self._actor_dict[actor] is None:
                                success = True
                    else:
                        control = actor.get_control()
                        control.speed = self._target_speed
                        control.direction = CarlaDataProvider.get_transform(actor).rotation.get_forward_vector()
                        actor.apply_control(control)
        if success:
            new_status = py_trees.common.Status.SUCCESS
        return new_status

    def terminate(self, new_status):
        """
        On termination of this behavior,
        the controls should be set back to 0.
        """
        for actor in self._local_planner_dict:
            if actor is not None and actor.is_alive:
                control, _ = get_actor_control(actor)
                actor.apply_control(control)
                local_planner = self._local_planner_dict[actor]
                if local_planner is not None and local_planner != 'Walker':
                    local_planner.reset_vehicle()
                    local_planner = None
        self._local_planner_dict = {}
        self._actor_dict = {}
        super(WaypointFollower, self).terminate(new_status)

def initialise(self):
    """
        Delayed one-time initialization

        Checks if another WaypointFollower behavior is already running for this actor.
        If this is the case, a termination signal is sent to the running behavior.
        """
    super(WaypointFollower, self).initialise()
    self._unique_id = int(round(time.time() * 1000000000.0))
    try:
        check_attr = operator.attrgetter('running_WF_actor_{}'.format(self._actor.id))
        running = check_attr(py_trees.blackboard.Blackboard())
        active_wf = copy.copy(running)
        active_wf.append(self._unique_id)
        py_trees.blackboard.Blackboard().set('running_WF_actor_{}'.format(self._actor.id), active_wf, overwrite=True)
    except AttributeError:
        py_trees.blackboard.Blackboard().set('terminate_WF_actor_{}'.format(self._actor.id), [], overwrite=True)
        py_trees.blackboard.Blackboard().set('running_WF_actor_{}'.format(self._actor.id), [self._unique_id], overwrite=True)
    for actor in self._actor_dict:
        self._apply_local_planner(actor)
    return True

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

class ActorSpeedAboveThresholdTest(Criterion):
    """
    This test will fail if the actor has had its linear velocity lower than a specific value for
    a specific amount of time
    Important parameters:
    - actor: CARLA actor to be used for this test
    - speed_threshold: speed required
    - below_threshold_max_time: Maximum time (in seconds) the actor can remain under the speed threshold
    - terminate_on_failure [optional]: If True, the complete scenario will terminate upon failure of this test
    """

    def __init__(self, actor, speed_threshold, below_threshold_max_time, name='ActorSpeedAboveThresholdTest', terminate_on_failure=False):
        """
        Class constructor.
        """
        super(ActorSpeedAboveThresholdTest, self).__init__(name, actor, 0, terminate_on_failure=terminate_on_failure)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._actor = actor
        self._speed_threshold = speed_threshold
        self._below_threshold_max_time = below_threshold_max_time
        self._time_last_valid_state = None

    def update(self):
        """
        Check if the actor speed is above the speed_threshold
        """
        new_status = py_trees.common.Status.RUNNING
        linear_speed = CarlaDataProvider.get_velocity(self._actor)
        if linear_speed is not None:
            if linear_speed < self._speed_threshold and self._time_last_valid_state:
                if GameTime.get_time() - self._time_last_valid_state > self._below_threshold_max_time:
                    self.test_status = 'FAILURE'
                    vehicle_location = CarlaDataProvider.get_location(self._actor)
                    blocked_event = TrafficEvent(event_type=TrafficEventType.VEHICLE_BLOCKED)
                    ActorSpeedAboveThresholdTest._set_event_message(blocked_event, vehicle_location)
                    ActorSpeedAboveThresholdTest._set_event_dict(blocked_event, vehicle_location)
                    self.list_traffic_events.append(blocked_event)
            else:
                self._time_last_valid_state = GameTime.get_time()
        if self._terminate_on_failure and self.test_status == 'FAILURE':
            new_status = py_trees.common.Status.FAILURE
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

    @staticmethod
    def _set_event_message(event, location):
        """
        Sets the message of the event
        """
        event.set_message('Agent got blocked at (x={}, y={}, z={})'.format(round(location.x, 3), round(location.y, 3), round(location.z, 3)))

    @staticmethod
    def _set_event_dict(event, location):
        """
        Sets the dictionary of the event
        """
        event.set_dict({'x': location.x, 'y': location.y, 'z': location.z})

def update(self):
    """
        Check if the actor speed is above the speed_threshold
        """
    new_status = py_trees.common.Status.RUNNING
    linear_speed = CarlaDataProvider.get_velocity(self._actor)
    if linear_speed is not None:
        if linear_speed < self._speed_threshold and self._time_last_valid_state:
            if GameTime.get_time() - self._time_last_valid_state > self._below_threshold_max_time:
                self.test_status = 'FAILURE'
                vehicle_location = CarlaDataProvider.get_location(self._actor)
                blocked_event = TrafficEvent(event_type=TrafficEventType.VEHICLE_BLOCKED)
                ActorSpeedAboveThresholdTest._set_event_message(blocked_event, vehicle_location)
                ActorSpeedAboveThresholdTest._set_event_dict(blocked_event, vehicle_location)
                self.list_traffic_events.append(blocked_event)
        else:
            self._time_last_valid_state = GameTime.get_time()
    if self._terminate_on_failure and self.test_status == 'FAILURE':
        new_status = py_trees.common.Status.FAILURE
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    return new_status

@staticmethod
def _set_event_message(event, location):
    """
        Sets the message of the event
        """
    event.set_message('Agent got blocked at (x={}, y={}, z={})'.format(round(location.x, 3), round(location.y, 3), round(location.z, 3)))

@staticmethod
def _set_event_dict(event, location):
    """
        Sets the dictionary of the event
        """
    event.set_dict({'x': location.x, 'y': location.y, 'z': location.z})

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

@staticmethod
def _count_lane_invasion(weak_self, event):
    """
        Callback to update lane invasion count
        """
    self = weak_self()
    if not self:
        return
    self.actual_value += 1

class OnSidewalkTest(Criterion):
    """
    Atomic containing a test to detect sidewalk invasions of a specific actor. This atomic can
    fail when actor has spent a specific time outside driving lanes (defined by OpenDRIVE).

    Args:
        actor (carla.Actor): CARLA actor to be used for this test
        duration (float): Time spent at sidewalks before the atomic fails.
            If terminate_on_failure isn't active, this is ignored.
        optional (bool): If True, the result is not considered for an overall pass/fail result
            when using the output argument
        terminate_on_failure (bool): If True, the atomic will fail when the duration condition has been met.
    """

    def __init__(self, actor, duration=0, optional=False, terminate_on_failure=False, name='OnSidewalkTest'):
        """
        Construction with sensor setup
        """
        super(OnSidewalkTest, self).__init__(name, actor, 0, None, optional, terminate_on_failure)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._actor = actor
        self._map = CarlaDataProvider.get_map()
        self._onsidewalk_active = False
        self._outside_lane_active = False
        self._actor_location = self._actor.get_location()
        self._wrong_sidewalk_distance = 0
        self._wrong_outside_lane_distance = 0
        self._sidewalk_start_location = None
        self._outside_lane_start_location = None
        self._duration = duration
        self._prev_time = None
        self._time_outside_lanes = 0

    def update(self):
        """
        First, transforms the actor's current position as well as its four corners to their
        corresponding waypoints. Depending on their lane type, the actor will be considered to be
        outside (or inside) driving lanes.

        returns:
            py_trees.common.Status.FAILURE: when the actor has spent a given duration outside
                driving lanes and terminate_on_failure is active
            py_trees.common.Status.RUNNING: the rest of the time
        """
        new_status = py_trees.common.Status.RUNNING
        if self._terminate_on_failure and self.test_status == 'FAILURE':
            new_status = py_trees.common.Status.FAILURE
        current_tra = CarlaDataProvider.get_transform(self._actor)
        current_loc = current_tra.location
        current_wp = self._map.get_waypoint(current_loc, lane_type=carla.LaneType.Any)
        if current_wp.lane_type == carla.LaneType.Sidewalk:
            if not self._onsidewalk_active:
                self._onsidewalk_active = True
                self._sidewalk_start_location = current_loc
        elif current_wp.lane_type != carla.LaneType.Driving and current_wp.lane_type != carla.LaneType.Parking:
            heading_vec = current_tra.get_forward_vector()
            heading_vec.z = 0
            heading_vec = heading_vec / math.sqrt(math.pow(heading_vec.x, 2) + math.pow(heading_vec.y, 2))
            perpendicular_vec = carla.Vector3D(-heading_vec.y, heading_vec.x, 0)
            extent = self.actor.bounding_box.extent
            x_boundary_vector = heading_vec * extent.x
            y_boundary_vector = perpendicular_vec * extent.y
            bbox = [current_loc + carla.Location(x_boundary_vector - y_boundary_vector), current_loc + carla.Location(x_boundary_vector + y_boundary_vector), current_loc + carla.Location(-1 * x_boundary_vector - y_boundary_vector), current_loc + carla.Location(-1 * x_boundary_vector + y_boundary_vector)]
            bbox_wp = [self._map.get_waypoint(bbox[0], lane_type=carla.LaneType.Any), self._map.get_waypoint(bbox[1], lane_type=carla.LaneType.Any), self._map.get_waypoint(bbox[2], lane_type=carla.LaneType.Any), self._map.get_waypoint(bbox[3], lane_type=carla.LaneType.Any)]
            if bbox_wp[0].lane_type == (carla.LaneType.Driving or carla.LaneType.Parking) or bbox_wp[1].lane_type == (carla.LaneType.Driving or carla.LaneType.Parking) or bbox_wp[2].lane_type == (carla.LaneType.Driving or carla.LaneType.Parking) or (bbox_wp[3].lane_type == (carla.LaneType.Driving or carla.LaneType.Parking)):
                self._onsidewalk_active = False
                self._outside_lane_active = False
            elif bbox_wp[0].lane_type == carla.LaneType.Sidewalk or bbox_wp[1].lane_type == carla.LaneType.Sidewalk or bbox_wp[2].lane_type == carla.LaneType.Sidewalk or (bbox_wp[3].lane_type == carla.LaneType.Sidewalk):
                if not self._onsidewalk_active:
                    self._onsidewalk_active = True
                    self._sidewalk_start_location = current_loc
            else:
                distance_vehicle_wp = current_loc.distance(current_wp.transform.location)
                if distance_vehicle_wp >= current_wp.lane_width / 2:
                    if not self._outside_lane_active:
                        self._outside_lane_active = True
                        self._outside_lane_start_location = current_loc
                else:
                    self._onsidewalk_active = False
                    self._outside_lane_active = False
        elif current_wp.is_junction:
            distance_vehicle_wp = math.sqrt(math.pow(current_wp.transform.location.x - current_loc.x, 2) + math.pow(current_wp.transform.location.y - current_loc.y, 2))
            if distance_vehicle_wp <= current_wp.lane_width / 2:
                self._onsidewalk_active = False
                self._outside_lane_active = False
        else:
            self._onsidewalk_active = False
            self._outside_lane_active = False
        if self._onsidewalk_active or self._outside_lane_active:
            if self._prev_time is None:
                self._prev_time = GameTime.get_time()
            else:
                curr_time = GameTime.get_time()
                self._time_outside_lanes += curr_time - self._prev_time
                self._prev_time = curr_time
        else:
            self._prev_time = None
        if self._time_outside_lanes > self._duration:
            self.test_status = 'FAILURE'
        distance_vector = CarlaDataProvider.get_location(self._actor) - self._actor_location
        distance = math.sqrt(math.pow(distance_vector.x, 2) + math.pow(distance_vector.y, 2))
        if distance >= 0.02:
            self._actor_location = CarlaDataProvider.get_location(self._actor)
            if self._onsidewalk_active:
                self._wrong_sidewalk_distance += distance
            elif self._outside_lane_active:
                self._wrong_outside_lane_distance += distance
        if not self._onsidewalk_active and self._wrong_sidewalk_distance > 0:
            self.actual_value += 1
            onsidewalk_event = TrafficEvent(event_type=TrafficEventType.ON_SIDEWALK_INFRACTION)
            self._set_event_message(onsidewalk_event, self._sidewalk_start_location, self._wrong_sidewalk_distance)
            self._set_event_dict(onsidewalk_event, self._sidewalk_start_location, self._wrong_sidewalk_distance)
            self._onsidewalk_active = False
            self._wrong_sidewalk_distance = 0
            self.list_traffic_events.append(onsidewalk_event)
        if not self._outside_lane_active and self._wrong_outside_lane_distance > 0:
            self.actual_value += 1
            outsidelane_event = TrafficEvent(event_type=TrafficEventType.OUTSIDE_LANE_INFRACTION)
            self._set_event_message(outsidelane_event, self._outside_lane_start_location, self._wrong_outside_lane_distance)
            self._set_event_dict(outsidelane_event, self._outside_lane_start_location, self._wrong_outside_lane_distance)
            self._outside_lane_active = False
            self._wrong_outside_lane_distance = 0
            self.list_traffic_events.append(outsidelane_event)
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

    def terminate(self, new_status):
        """
        If there is currently an event running, it is registered
        """
        if self._onsidewalk_active:
            self.actual_value += 1
            onsidewalk_event = TrafficEvent(event_type=TrafficEventType.ON_SIDEWALK_INFRACTION)
            self._set_event_message(onsidewalk_event, self._sidewalk_start_location, self._wrong_sidewalk_distance)
            self._set_event_dict(onsidewalk_event, self._sidewalk_start_location, self._wrong_sidewalk_distance)
            self._onsidewalk_active = False
            self._wrong_sidewalk_distance = 0
            self.list_traffic_events.append(onsidewalk_event)
        if self._outside_lane_active:
            self.actual_value += 1
            outsidelane_event = TrafficEvent(event_type=TrafficEventType.OUTSIDE_LANE_INFRACTION)
            self._set_event_message(outsidelane_event, self._outside_lane_start_location, self._wrong_outside_lane_distance)
            self._set_event_dict(outsidelane_event, self._outside_lane_start_location, self._wrong_outside_lane_distance)
            self._outside_lane_active = False
            self._wrong_outside_lane_distance = 0
            self.list_traffic_events.append(outsidelane_event)
        super(OnSidewalkTest, self).terminate(new_status)

    def _set_event_message(self, event, location, distance):
        """
        Sets the message of the event
        """
        if event.get_type() == TrafficEventType.ON_SIDEWALK_INFRACTION:
            message_start = 'Agent invaded the sidewalk'
        else:
            message_start = 'Agent went outside the lane'
        event.set_message('{} for about {} meters, starting at (x={}, y={}, z={})'.format(message_start, round(distance, 3), round(location.x, 3), round(location.y, 3), round(location.z, 3)))

    def _set_event_dict(self, event, location, distance):
        """
        Sets the dictionary of the event
        """
        event.set_dict({'x': location.x, 'y': location.y, 'z': location.z, 'distance': distance})

def update(self):
    """
        First, transforms the actor's current position as well as its four corners to their
        corresponding waypoints. Depending on their lane type, the actor will be considered to be
        outside (or inside) driving lanes.

        returns:
            py_trees.common.Status.FAILURE: when the actor has spent a given duration outside
                driving lanes and terminate_on_failure is active
            py_trees.common.Status.RUNNING: the rest of the time
        """
    new_status = py_trees.common.Status.RUNNING
    if self._terminate_on_failure and self.test_status == 'FAILURE':
        new_status = py_trees.common.Status.FAILURE
    current_tra = CarlaDataProvider.get_transform(self._actor)
    current_loc = current_tra.location
    current_wp = self._map.get_waypoint(current_loc, lane_type=carla.LaneType.Any)
    if current_wp.lane_type == carla.LaneType.Sidewalk:
        if not self._onsidewalk_active:
            self._onsidewalk_active = True
            self._sidewalk_start_location = current_loc
    elif current_wp.lane_type != carla.LaneType.Driving and current_wp.lane_type != carla.LaneType.Parking:
        heading_vec = current_tra.get_forward_vector()
        heading_vec.z = 0
        heading_vec = heading_vec / math.sqrt(math.pow(heading_vec.x, 2) + math.pow(heading_vec.y, 2))
        perpendicular_vec = carla.Vector3D(-heading_vec.y, heading_vec.x, 0)
        extent = self.actor.bounding_box.extent
        x_boundary_vector = heading_vec * extent.x
        y_boundary_vector = perpendicular_vec * extent.y
        bbox = [current_loc + carla.Location(x_boundary_vector - y_boundary_vector), current_loc + carla.Location(x_boundary_vector + y_boundary_vector), current_loc + carla.Location(-1 * x_boundary_vector - y_boundary_vector), current_loc + carla.Location(-1 * x_boundary_vector + y_boundary_vector)]
        bbox_wp = [self._map.get_waypoint(bbox[0], lane_type=carla.LaneType.Any), self._map.get_waypoint(bbox[1], lane_type=carla.LaneType.Any), self._map.get_waypoint(bbox[2], lane_type=carla.LaneType.Any), self._map.get_waypoint(bbox[3], lane_type=carla.LaneType.Any)]
        if bbox_wp[0].lane_type == (carla.LaneType.Driving or carla.LaneType.Parking) or bbox_wp[1].lane_type == (carla.LaneType.Driving or carla.LaneType.Parking) or bbox_wp[2].lane_type == (carla.LaneType.Driving or carla.LaneType.Parking) or (bbox_wp[3].lane_type == (carla.LaneType.Driving or carla.LaneType.Parking)):
            self._onsidewalk_active = False
            self._outside_lane_active = False
        elif bbox_wp[0].lane_type == carla.LaneType.Sidewalk or bbox_wp[1].lane_type == carla.LaneType.Sidewalk or bbox_wp[2].lane_type == carla.LaneType.Sidewalk or (bbox_wp[3].lane_type == carla.LaneType.Sidewalk):
            if not self._onsidewalk_active:
                self._onsidewalk_active = True
                self._sidewalk_start_location = current_loc
        else:
            distance_vehicle_wp = current_loc.distance(current_wp.transform.location)
            if distance_vehicle_wp >= current_wp.lane_width / 2:
                if not self._outside_lane_active:
                    self._outside_lane_active = True
                    self._outside_lane_start_location = current_loc
            else:
                self._onsidewalk_active = False
                self._outside_lane_active = False
    elif current_wp.is_junction:
        distance_vehicle_wp = math.sqrt(math.pow(current_wp.transform.location.x - current_loc.x, 2) + math.pow(current_wp.transform.location.y - current_loc.y, 2))
        if distance_vehicle_wp <= current_wp.lane_width / 2:
            self._onsidewalk_active = False
            self._outside_lane_active = False
    else:
        self._onsidewalk_active = False
        self._outside_lane_active = False
    if self._onsidewalk_active or self._outside_lane_active:
        if self._prev_time is None:
            self._prev_time = GameTime.get_time()
        else:
            curr_time = GameTime.get_time()
            self._time_outside_lanes += curr_time - self._prev_time
            self._prev_time = curr_time
    else:
        self._prev_time = None
    if self._time_outside_lanes > self._duration:
        self.test_status = 'FAILURE'
    distance_vector = CarlaDataProvider.get_location(self._actor) - self._actor_location
    distance = math.sqrt(math.pow(distance_vector.x, 2) + math.pow(distance_vector.y, 2))
    if distance >= 0.02:
        self._actor_location = CarlaDataProvider.get_location(self._actor)
        if self._onsidewalk_active:
            self._wrong_sidewalk_distance += distance
        elif self._outside_lane_active:
            self._wrong_outside_lane_distance += distance
    if not self._onsidewalk_active and self._wrong_sidewalk_distance > 0:
        self.actual_value += 1
        onsidewalk_event = TrafficEvent(event_type=TrafficEventType.ON_SIDEWALK_INFRACTION)
        self._set_event_message(onsidewalk_event, self._sidewalk_start_location, self._wrong_sidewalk_distance)
        self._set_event_dict(onsidewalk_event, self._sidewalk_start_location, self._wrong_sidewalk_distance)
        self._onsidewalk_active = False
        self._wrong_sidewalk_distance = 0
        self.list_traffic_events.append(onsidewalk_event)
    if not self._outside_lane_active and self._wrong_outside_lane_distance > 0:
        self.actual_value += 1
        outsidelane_event = TrafficEvent(event_type=TrafficEventType.OUTSIDE_LANE_INFRACTION)
        self._set_event_message(outsidelane_event, self._outside_lane_start_location, self._wrong_outside_lane_distance)
        self._set_event_dict(outsidelane_event, self._outside_lane_start_location, self._wrong_outside_lane_distance)
        self._outside_lane_active = False
        self._wrong_outside_lane_distance = 0
        self.list_traffic_events.append(outsidelane_event)
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    return new_status

def terminate(self, new_status):
    """
        If there is currently an event running, it is registered
        """
    if self._onsidewalk_active:
        self.actual_value += 1
        onsidewalk_event = TrafficEvent(event_type=TrafficEventType.ON_SIDEWALK_INFRACTION)
        self._set_event_message(onsidewalk_event, self._sidewalk_start_location, self._wrong_sidewalk_distance)
        self._set_event_dict(onsidewalk_event, self._sidewalk_start_location, self._wrong_sidewalk_distance)
        self._onsidewalk_active = False
        self._wrong_sidewalk_distance = 0
        self.list_traffic_events.append(onsidewalk_event)
    if self._outside_lane_active:
        self.actual_value += 1
        outsidelane_event = TrafficEvent(event_type=TrafficEventType.OUTSIDE_LANE_INFRACTION)
        self._set_event_message(outsidelane_event, self._outside_lane_start_location, self._wrong_outside_lane_distance)
        self._set_event_dict(outsidelane_event, self._outside_lane_start_location, self._wrong_outside_lane_distance)
        self._outside_lane_active = False
        self._wrong_outside_lane_distance = 0
        self.list_traffic_events.append(outsidelane_event)
    super(OnSidewalkTest, self).terminate(new_status)

def _set_event_message(self, event, location, distance):
    """
        Sets the message of the event
        """
    if event.get_type() == TrafficEventType.ON_SIDEWALK_INFRACTION:
        message_start = 'Agent invaded the sidewalk'
    else:
        message_start = 'Agent went outside the lane'
    event.set_message('{} for about {} meters, starting at (x={}, y={}, z={})'.format(message_start, round(distance, 3), round(location.x, 3), round(location.y, 3), round(location.z, 3)))

def _set_event_dict(self, event, location, distance):
    """
        Sets the dictionary of the event
        """
    event.set_dict({'x': location.x, 'y': location.y, 'z': location.z, 'distance': distance})

class OutsideRouteLanesTest(Criterion):
    """
    Atomic to detect if the vehicle is either on a sidewalk or at a wrong lane. The distance spent outside
    is computed and it is returned as a percentage of the route distance traveled.

    Args:
        actor (carla.ACtor): CARLA actor to be used for this test
        route (list [carla.Location, connection]): series of locations representing the route waypoints
        optional (bool): If True, the result is not considered for an overall pass/fail result
    """
    ALLOWED_OUT_DISTANCE = 1.3
    MAX_ALLOWED_VEHICLE_ANGLE = 120.0
    MAX_ALLOWED_WAYPOINT_ANGLE = 150.0
    WINDOWS_SIZE = 3

    def __init__(self, actor, route, optional=False, name='OutsideRouteLanesTest'):
        """
        Constructor
        """
        super(OutsideRouteLanesTest, self).__init__(name, actor, 0, None, optional)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._actor = actor
        self._route = route
        self._current_index = 0
        self._route_length = len(self._route)
        self._waypoints, _ = zip(*self._route)
        self._map = CarlaDataProvider.get_map()
        self._pre_ego_waypoint = self._map.get_waypoint(self._actor.get_location())
        self._outside_lane_active = False
        self._wrong_lane_active = False
        self._last_road_id = None
        self._last_lane_id = None
        self._total_distance = 0
        self._wrong_distance = 0

    def update(self):
        """
        Transforms the actor location and its four corners to waypoints. Depending on its types,
        the actor will be considered to be at driving lanes, sidewalk or offroad.

        returns:
            py_trees.common.Status.FAILURE: when the actor has left driving and terminate_on_failure is active
            py_trees.common.Status.RUNNING: the rest of the time
        """
        new_status = py_trees.common.Status.RUNNING
        if self._terminate_on_failure and self.test_status == 'FAILURE':
            new_status = py_trees.common.Status.FAILURE
        location = CarlaDataProvider.get_location(self._actor)
        if location is None:
            return new_status
        self._is_outside_driving_lanes(location)
        self._is_at_wrong_lane(location)
        if self._outside_lane_active or self._wrong_lane_active:
            self.test_status = 'FAILURE'
        for index in range(self._current_index + 1, min(self._current_index + self.WINDOWS_SIZE + 1, self._route_length)):
            index_location = self._waypoints[index]
            index_waypoint = self._map.get_waypoint(index_location)
            wp_dir = index_waypoint.transform.get_forward_vector()
            wp_veh = location - index_location
            dot_ve_wp = wp_veh.x * wp_dir.x + wp_veh.y * wp_dir.y + wp_veh.z * wp_dir.z
            if dot_ve_wp > 0:
                index_location = self._waypoints[index]
                current_index_location = self._waypoints[self._current_index]
                new_dist = current_index_location.distance(index_location)
                self._current_index = index
                self._total_distance += new_dist
                if self._outside_lane_active or self._wrong_lane_active:
                    self._wrong_distance += new_dist
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

    def _is_outside_driving_lanes(self, location):
        """
        Detects if the ego_vehicle is outside driving lanes
        """
        current_driving_wp = self._map.get_waypoint(location, lane_type=carla.LaneType.Driving, project_to_road=True)
        current_parking_wp = self._map.get_waypoint(location, lane_type=carla.LaneType.Parking, project_to_road=True)
        driving_distance = location.distance(current_driving_wp.transform.location)
        if current_parking_wp is not None:
            parking_distance = location.distance(current_parking_wp.transform.location)
        else:
            parking_distance = float('inf')
        if driving_distance >= parking_distance:
            distance = parking_distance
            lane_width = current_parking_wp.lane_width
        else:
            distance = driving_distance
            lane_width = current_driving_wp.lane_width
        self._outside_lane_active = bool(distance > lane_width / 2 + self.ALLOWED_OUT_DISTANCE)

    def _is_at_wrong_lane(self, location):
        """
        Detects if the ego_vehicle has invaded a wrong lane
        """
        current_waypoint = self._map.get_waypoint(location, lane_type=carla.LaneType.Driving, project_to_road=True)
        current_lane_id = current_waypoint.lane_id
        current_road_id = current_waypoint.road_id
        if current_waypoint.is_junction:
            self._wrong_lane_active = False
        elif self._last_road_id != current_road_id or self._last_lane_id != current_lane_id:
            if self._pre_ego_waypoint.is_junction:
                yaw_waypt = current_waypoint.transform.rotation.yaw % 360
                yaw_actor = self._actor.get_transform().rotation.yaw % 360
                vehicle_lane_angle = (yaw_waypt - yaw_actor) % 360
                if vehicle_lane_angle < self.MAX_ALLOWED_VEHICLE_ANGLE or vehicle_lane_angle > 360 - self.MAX_ALLOWED_VEHICLE_ANGLE:
                    self._wrong_lane_active = False
                else:
                    self._wrong_lane_active = True
            else:
                yaw_pre_wp = self._pre_ego_waypoint.transform.rotation.yaw % 360
                yaw_cur_wp = current_waypoint.transform.rotation.yaw % 360
                waypoint_angle = (yaw_pre_wp - yaw_cur_wp) % 360
                if waypoint_angle >= self.MAX_ALLOWED_WAYPOINT_ANGLE and waypoint_angle <= 360 - self.MAX_ALLOWED_WAYPOINT_ANGLE:
                    self._wrong_lane_active = not bool(self._wrong_lane_active)
                else:
                    self._wrong_lane_active = False
        self._last_lane_id = current_lane_id
        self._last_road_id = current_road_id
        self._pre_ego_waypoint = current_waypoint

    def terminate(self, new_status):
        """
        If there is currently an event running, it is registered
        """
        if self._wrong_distance > 0:
            percentage = self._wrong_distance / self._total_distance * 100
            outside_lane = TrafficEvent(event_type=TrafficEventType.OUTSIDE_ROUTE_LANES_INFRACTION)
            outside_lane.set_message('Agent went outside its route lanes for about {} meters ({}% of the completed route)'.format(round(self._wrong_distance, 3), round(percentage, 2)))
            outside_lane.set_dict({'distance': self._wrong_distance, 'percentage': percentage})
            self._wrong_distance = 0
            self.list_traffic_events.append(outside_lane)
            self.actual_value = round(percentage, 2)
        super(OutsideRouteLanesTest, self).terminate(new_status)

def terminate(self, new_status):
    """
        If there is currently an event running, it is registered
        """
    if self._wrong_distance > 0:
        percentage = self._wrong_distance / self._total_distance * 100
        outside_lane = TrafficEvent(event_type=TrafficEventType.OUTSIDE_ROUTE_LANES_INFRACTION)
        outside_lane.set_message('Agent went outside its route lanes for about {} meters ({}% of the completed route)'.format(round(self._wrong_distance, 3), round(percentage, 2)))
        outside_lane.set_dict({'distance': self._wrong_distance, 'percentage': percentage})
        self._wrong_distance = 0
        self.list_traffic_events.append(outside_lane)
        self.actual_value = round(percentage, 2)
    super(OutsideRouteLanesTest, self).terminate(new_status)

class WrongLaneTest(Criterion):
    """
    This class contains an atomic test to detect invasions to wrong direction lanes.

    Important parameters:
    - actor: CARLA actor to be used for this test
    - optional [optional]: If True, the result is not considered for an overall pass/fail result
    """
    MAX_ALLOWED_ANGLE = 120.0
    MAX_ALLOWED_WAYPOINT_ANGLE = 150.0

    def __init__(self, actor, optional=False, name='WrongLaneTest'):
        """
        Construction with sensor setup
        """
        super(WrongLaneTest, self).__init__(name, actor, 0, None, optional)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._actor = actor
        self._map = CarlaDataProvider.get_map()
        self._last_lane_id = None
        self._last_road_id = None
        self._in_lane = True
        self._wrong_distance = 0
        self._actor_location = self._actor.get_location()
        self._previous_lane_waypoint = self._map.get_waypoint(self._actor.get_location())
        self._wrong_lane_start_location = None

    def update(self):
        """
        Check lane invasion count
        """
        new_status = py_trees.common.Status.RUNNING
        if self._terminate_on_failure and self.test_status == 'FAILURE':
            new_status = py_trees.common.Status.FAILURE
        lane_waypoint = self._map.get_waypoint(self._actor.get_location())
        current_lane_id = lane_waypoint.lane_id
        current_road_id = lane_waypoint.road_id
        if (self._last_road_id != current_road_id or self._last_lane_id != current_lane_id) and (not lane_waypoint.is_junction):
            next_waypoint = lane_waypoint.next(2.0)[0]
            if not next_waypoint:
                return new_status
            previous_lane_direction = self._previous_lane_waypoint.transform.get_forward_vector()
            current_lane_direction = lane_waypoint.transform.get_forward_vector()
            p_lane_vector = np.array([previous_lane_direction.x, previous_lane_direction.y])
            c_lane_vector = np.array([current_lane_direction.x, current_lane_direction.y])
            waypoint_angle = math.degrees(math.acos(np.clip(np.dot(p_lane_vector, c_lane_vector) / (np.linalg.norm(p_lane_vector) * np.linalg.norm(c_lane_vector)), -1.0, 1.0)))
            if waypoint_angle > self.MAX_ALLOWED_WAYPOINT_ANGLE and self._in_lane:
                self.test_status = 'FAILURE'
                self._in_lane = False
                self.actual_value += 1
                self._wrong_lane_start_location = self._actor_location
            else:
                self._in_lane = True
            if self._previous_lane_waypoint.is_junction:
                vector_wp = np.array([next_waypoint.transform.location.x - lane_waypoint.transform.location.x, next_waypoint.transform.location.y - lane_waypoint.transform.location.y])
                vector_actor = np.array([math.cos(math.radians(self._actor.get_transform().rotation.yaw)), math.sin(math.radians(self._actor.get_transform().rotation.yaw))])
                vehicle_lane_angle = math.degrees(math.acos(np.clip(np.dot(vector_actor, vector_wp) / np.linalg.norm(vector_wp), -1.0, 1.0)))
                if vehicle_lane_angle > self.MAX_ALLOWED_ANGLE:
                    self.test_status = 'FAILURE'
                    self._in_lane = False
                    self.actual_value += 1
                    self._wrong_lane_start_location = self._actor.get_location()
        distance_vector = self._actor.get_location() - self._actor_location
        distance = math.sqrt(math.pow(distance_vector.x, 2) + math.pow(distance_vector.y, 2))
        if distance >= 0.02:
            self._actor_location = CarlaDataProvider.get_location(self._actor)
            if not self._in_lane and (not lane_waypoint.is_junction):
                self._wrong_distance += distance
        if self._in_lane and self._wrong_distance > 0:
            wrong_way_event = TrafficEvent(event_type=TrafficEventType.WRONG_WAY_INFRACTION)
            self._set_event_message(wrong_way_event, self._wrong_lane_start_location, self._wrong_distance, current_road_id, current_lane_id)
            self._set_event_dict(wrong_way_event, self._wrong_lane_start_location, self._wrong_distance, current_road_id, current_lane_id)
            self.list_traffic_events.append(wrong_way_event)
            self._wrong_distance = 0
        self._last_lane_id = current_lane_id
        self._last_road_id = current_road_id
        self._previous_lane_waypoint = lane_waypoint
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

    def terminate(self, new_status):
        """
        If there is currently an event running, it is registered
        """
        if not self._in_lane:
            lane_waypoint = self._map.get_waypoint(self._actor.get_location())
            current_lane_id = lane_waypoint.lane_id
            current_road_id = lane_waypoint.road_id
            wrong_way_event = TrafficEvent(event_type=TrafficEventType.WRONG_WAY_INFRACTION)
            self._set_event_message(wrong_way_event, self._wrong_lane_start_location, self._wrong_distance, current_road_id, current_lane_id)
            self._set_event_dict(wrong_way_event, self._wrong_lane_start_location, self._wrong_distance, current_road_id, current_lane_id)
            self._wrong_distance = 0
            self._in_lane = True
            self.list_traffic_events.append(wrong_way_event)
        super(WrongLaneTest, self).terminate(new_status)

    def _set_event_message(self, event, location, distance, road_id, lane_id):
        """
        Sets the message of the event
        """
        event.set_message('Agent invaded a lane in opposite direction for {} meters, starting at (x={}, y={}, z={}). road_id={}, lane_id={}'.format(round(distance, 3), round(location.x, 3), round(location.y, 3), round(location.z, 3), road_id, lane_id))

    def _set_event_dict(self, event, location, distance, road_id, lane_id):
        """
        Sets the dictionary of the event
        """
        event.set_dict({'x': location.x, 'y': location.y, 'z': location.y, 'distance': distance, 'road_id': road_id, 'lane_id': lane_id})

def terminate(self, new_status):
    """
        If there is currently an event running, it is registered
        """
    if not self._in_lane:
        lane_waypoint = self._map.get_waypoint(self._actor.get_location())
        current_lane_id = lane_waypoint.lane_id
        current_road_id = lane_waypoint.road_id
        wrong_way_event = TrafficEvent(event_type=TrafficEventType.WRONG_WAY_INFRACTION)
        self._set_event_message(wrong_way_event, self._wrong_lane_start_location, self._wrong_distance, current_road_id, current_lane_id)
        self._set_event_dict(wrong_way_event, self._wrong_lane_start_location, self._wrong_distance, current_road_id, current_lane_id)
        self._wrong_distance = 0
        self._in_lane = True
        self.list_traffic_events.append(wrong_way_event)
    super(WrongLaneTest, self).terminate(new_status)

def _set_event_message(self, event, location, distance, road_id, lane_id):
    """
        Sets the message of the event
        """
    event.set_message('Agent invaded a lane in opposite direction for {} meters, starting at (x={}, y={}, z={}). road_id={}, lane_id={}'.format(round(distance, 3), round(location.x, 3), round(location.y, 3), round(location.z, 3), road_id, lane_id))

def _set_event_dict(self, event, location, distance, road_id, lane_id):
    """
        Sets the dictionary of the event
        """
    event.set_dict({'x': location.x, 'y': location.y, 'z': location.y, 'distance': distance, 'road_id': road_id, 'lane_id': lane_id})

class InRadiusRegionTest(Criterion):
    """
    The test is a success if the actor is within a given radius of a specified region

    Important parameters:
    - actor: CARLA actor to be used for this test
    - x, y, radius: Position (x,y) and radius (in meters) used to get the checked region
    """

    def __init__(self, actor, x, y, radius, name='InRadiusRegionTest'):
        """
        """
        super(InRadiusRegionTest, self).__init__(name, actor, 0)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._actor = actor
        self._x = x
        self._y = y
        self._radius = radius

    def update(self):
        """
        Check if the actor location is within trigger region
        """
        new_status = py_trees.common.Status.RUNNING
        location = CarlaDataProvider.get_location(self._actor)
        if location is None:
            return new_status
        if self.test_status != 'SUCCESS':
            in_radius = math.sqrt((location.x - self._x) ** 2 + (location.y - self._y) ** 2) < self._radius
            if in_radius:
                route_completion_event = TrafficEvent(event_type=TrafficEventType.ROUTE_COMPLETED)
                route_completion_event.set_message('Destination was successfully reached')
                self.list_traffic_events.append(route_completion_event)
                self.test_status = 'SUCCESS'
            else:
                self.test_status = 'RUNNING'
        if self.test_status == 'SUCCESS':
            new_status = py_trees.common.Status.SUCCESS
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

def update(self):
    """
        Check if the actor location is within trigger region
        """
    new_status = py_trees.common.Status.RUNNING
    location = CarlaDataProvider.get_location(self._actor)
    if location is None:
        return new_status
    if self.test_status != 'SUCCESS':
        in_radius = math.sqrt((location.x - self._x) ** 2 + (location.y - self._y) ** 2) < self._radius
        if in_radius:
            route_completion_event = TrafficEvent(event_type=TrafficEventType.ROUTE_COMPLETED)
            route_completion_event.set_message('Destination was successfully reached')
            self.list_traffic_events.append(route_completion_event)
            self.test_status = 'SUCCESS'
        else:
            self.test_status = 'RUNNING'
    if self.test_status == 'SUCCESS':
        new_status = py_trees.common.Status.SUCCESS
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    return new_status

class InRouteTest(Criterion):
    """
    The test is a success if the actor is never outside route. The actor can go outside of the route
    but only for a certain amount of distance

    Important parameters:
    - actor: CARLA actor to be used for this test
    - route: Route to be checked
    - offroad_max: Maximum distance (in meters) the actor can deviate from the route
    - offroad_min: Maximum safe distance (in meters). Might eventually cause failure
    - terminate_on_failure [optional]: If True, the complete scenario will terminate upon failure of this test
    """
    MAX_ROUTE_PERCENTAGE = 30
    WINDOWS_SIZE = 5

    def __init__(self, actor, route, offroad_min=-1, offroad_max=30, name='InRouteTest', terminate_on_failure=False):
        """
        """
        super(InRouteTest, self).__init__(name, actor, 0, terminate_on_failure=terminate_on_failure)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._actor = actor
        self._route = route
        self._offroad_max = offroad_max
        if offroad_min == -1:
            self._offroad_min = self._offroad_max / 2
        else:
            self._offroad_min = self._offroad_min
        self._world = CarlaDataProvider.get_world()
        self._waypoints, _ = zip(*self._route)
        self._route_length = len(self._route)
        self._current_index = 0
        self._out_route_distance = 0
        self._in_safe_route = True
        self._accum_meters = []
        prev_wp = self._waypoints[0]
        for i, wp in enumerate(self._waypoints):
            d = wp.distance(prev_wp)
            if i > 0:
                accum = self._accum_meters[i - 1]
            else:
                accum = 0
            self._accum_meters.append(d + accum)
            prev_wp = wp
        blackv = py_trees.blackboard.Blackboard()
        _ = blackv.set('InRoute', True)

    def update(self):
        """
        Check if the actor location is within trigger region
        """
        new_status = py_trees.common.Status.RUNNING
        location = CarlaDataProvider.get_location(self._actor)
        if location is None:
            return new_status
        if self._terminate_on_failure and self.test_status == 'FAILURE':
            new_status = py_trees.common.Status.FAILURE
        elif self.test_status == 'RUNNING' or self.test_status == 'INIT':
            off_route = True
            shortest_distance = float('inf')
            closest_index = -1
            for index in range(self._current_index, min(self._current_index + self.WINDOWS_SIZE + 1, self._route_length)):
                ref_waypoint = self._waypoints[index]
                distance = math.sqrt((location.x - ref_waypoint.x) ** 2 + (location.y - ref_waypoint.y) ** 2)
                if distance <= shortest_distance:
                    closest_index = index
                    shortest_distance = distance
            if closest_index == -1 or shortest_distance == float('inf'):
                return new_status
            if shortest_distance < self._offroad_max:
                off_route = False
                self._in_safe_route = bool(shortest_distance < self._offroad_min)
            if self._current_index != closest_index:
                new_dist = self._accum_meters[closest_index] - self._accum_meters[self._current_index]
                if not self._in_safe_route:
                    self._out_route_distance += new_dist
                    out_route_percentage = 100 * self._out_route_distance / self._accum_meters[-1]
                    if out_route_percentage > self.MAX_ROUTE_PERCENTAGE:
                        off_route = True
                self._current_index = closest_index
            if off_route:
                blackv = py_trees.blackboard.Blackboard()
                _ = blackv.set('InRoute', False)
                route_deviation_event = TrafficEvent(event_type=TrafficEventType.ROUTE_DEVIATION)
                route_deviation_event.set_message('Agent deviated from the route at (x={}, y={}, z={})'.format(round(location.x, 3), round(location.y, 3), round(location.z, 3)))
                route_deviation_event.set_dict({'x': location.x, 'y': location.y, 'z': location.z})
                self.list_traffic_events.append(route_deviation_event)
                self.test_status = 'FAILURE'
                self.actual_value += 1
                new_status = py_trees.common.Status.FAILURE
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

def update(self):
    """
        Check if the actor location is within trigger region
        """
    new_status = py_trees.common.Status.RUNNING
    location = CarlaDataProvider.get_location(self._actor)
    if location is None:
        return new_status
    if self._terminate_on_failure and self.test_status == 'FAILURE':
        new_status = py_trees.common.Status.FAILURE
    elif self.test_status == 'RUNNING' or self.test_status == 'INIT':
        off_route = True
        shortest_distance = float('inf')
        closest_index = -1
        for index in range(self._current_index, min(self._current_index + self.WINDOWS_SIZE + 1, self._route_length)):
            ref_waypoint = self._waypoints[index]
            distance = math.sqrt((location.x - ref_waypoint.x) ** 2 + (location.y - ref_waypoint.y) ** 2)
            if distance <= shortest_distance:
                closest_index = index
                shortest_distance = distance
        if closest_index == -1 or shortest_distance == float('inf'):
            return new_status
        if shortest_distance < self._offroad_max:
            off_route = False
            self._in_safe_route = bool(shortest_distance < self._offroad_min)
        if self._current_index != closest_index:
            new_dist = self._accum_meters[closest_index] - self._accum_meters[self._current_index]
            if not self._in_safe_route:
                self._out_route_distance += new_dist
                out_route_percentage = 100 * self._out_route_distance / self._accum_meters[-1]
                if out_route_percentage > self.MAX_ROUTE_PERCENTAGE:
                    off_route = True
            self._current_index = closest_index
        if off_route:
            blackv = py_trees.blackboard.Blackboard()
            _ = blackv.set('InRoute', False)
            route_deviation_event = TrafficEvent(event_type=TrafficEventType.ROUTE_DEVIATION)
            route_deviation_event.set_message('Agent deviated from the route at (x={}, y={}, z={})'.format(round(location.x, 3), round(location.y, 3), round(location.z, 3)))
            route_deviation_event.set_dict({'x': location.x, 'y': location.y, 'z': location.z})
            self.list_traffic_events.append(route_deviation_event)
            self.test_status = 'FAILURE'
            self.actual_value += 1
            new_status = py_trees.common.Status.FAILURE
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    return new_status

class RouteCompletionTest(Criterion):
    """
    Check at which stage of the route is the actor at each tick

    Important parameters:
    - actor: CARLA actor to be used for this test
    - route: Route to be checked
    - terminate_on_failure [optional]: If True, the complete scenario will terminate upon failure of this test
    """
    DISTANCE_THRESHOLD = 10.0
    WINDOWS_SIZE = 2

    def __init__(self, actor, route, name='RouteCompletionTest', terminate_on_failure=False):
        """
        """
        super(RouteCompletionTest, self).__init__(name, actor, 100, terminate_on_failure=terminate_on_failure)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._actor = actor
        self._route = route
        self._map = CarlaDataProvider.get_map()
        self._wsize = self.WINDOWS_SIZE
        self._current_index = 0
        self._route_length = len(self._route)
        self._waypoints, _ = zip(*self._route)
        self.target = self._waypoints[-1]
        self._accum_meters = []
        prev_wp = self._waypoints[0]
        for i, wp in enumerate(self._waypoints):
            d = wp.distance(prev_wp)
            if i > 0:
                accum = self._accum_meters[i - 1]
            else:
                accum = 0
            self._accum_meters.append(d + accum)
            prev_wp = wp
        self._traffic_event = TrafficEvent(event_type=TrafficEventType.ROUTE_COMPLETION)
        self.list_traffic_events.append(self._traffic_event)
        self._percentage_route_completed = 0.0

    def update(self):
        """
        Check if the actor location is within trigger region
        """
        new_status = py_trees.common.Status.RUNNING
        location = CarlaDataProvider.get_location(self._actor)
        if location is None:
            return new_status
        if self._terminate_on_failure and self.test_status == 'FAILURE':
            new_status = py_trees.common.Status.FAILURE
        elif self.test_status == 'RUNNING' or self.test_status == 'INIT':
            for index in range(self._current_index, min(self._current_index + self._wsize + 1, self._route_length)):
                ref_waypoint = self._waypoints[index]
                wp = self._map.get_waypoint(ref_waypoint)
                wp_dir = wp.transform.get_forward_vector()
                wp_veh = location - ref_waypoint
                dot_ve_wp = wp_veh.x * wp_dir.x + wp_veh.y * wp_dir.y + wp_veh.z * wp_dir.z
                if dot_ve_wp > 0:
                    self._current_index = index
                    self._percentage_route_completed = 100.0 * float(self._accum_meters[self._current_index]) / float(self._accum_meters[-1])
                    self._traffic_event.set_dict({'route_completed': self._percentage_route_completed})
                    self._traffic_event.set_message('Agent has completed > {:.2f}% of the route'.format(self._percentage_route_completed))
            if int(os.environ.get('DATAGEN')) == 1:
                completion_percent = 85.0
            else:
                completion_percent = 99.0
            if self._percentage_route_completed > completion_percent and location.distance(self.target) < self.DISTANCE_THRESHOLD:
                route_completion_event = TrafficEvent(event_type=TrafficEventType.ROUTE_COMPLETED)
                route_completion_event.set_message('Destination was successfully reached')
                self.list_traffic_events.append(route_completion_event)
                self.test_status = 'SUCCESS'
                self._percentage_route_completed = 100
        elif self.test_status == 'SUCCESS':
            new_status = py_trees.common.Status.SUCCESS
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

    def terminate(self, new_status):
        """
        Set test status to failure if not successful and terminate
        """
        self.actual_value = round(self._percentage_route_completed, 2)
        if self.test_status == 'INIT':
            self.test_status = 'FAILURE'
        super(RouteCompletionTest, self).terminate(new_status)

def update(self):
    """
        Check if the actor location is within trigger region
        """
    new_status = py_trees.common.Status.RUNNING
    location = CarlaDataProvider.get_location(self._actor)
    if location is None:
        return new_status
    if self._terminate_on_failure and self.test_status == 'FAILURE':
        new_status = py_trees.common.Status.FAILURE
    elif self.test_status == 'RUNNING' or self.test_status == 'INIT':
        for index in range(self._current_index, min(self._current_index + self._wsize + 1, self._route_length)):
            ref_waypoint = self._waypoints[index]
            wp = self._map.get_waypoint(ref_waypoint)
            wp_dir = wp.transform.get_forward_vector()
            wp_veh = location - ref_waypoint
            dot_ve_wp = wp_veh.x * wp_dir.x + wp_veh.y * wp_dir.y + wp_veh.z * wp_dir.z
            if dot_ve_wp > 0:
                self._current_index = index
                self._percentage_route_completed = 100.0 * float(self._accum_meters[self._current_index]) / float(self._accum_meters[-1])
                self._traffic_event.set_dict({'route_completed': self._percentage_route_completed})
                self._traffic_event.set_message('Agent has completed > {:.2f}% of the route'.format(self._percentage_route_completed))
        if int(os.environ.get('DATAGEN')) == 1:
            completion_percent = 85.0
        else:
            completion_percent = 99.0
        if self._percentage_route_completed > completion_percent and location.distance(self.target) < self.DISTANCE_THRESHOLD:
            route_completion_event = TrafficEvent(event_type=TrafficEventType.ROUTE_COMPLETED)
            route_completion_event.set_message('Destination was successfully reached')
            self.list_traffic_events.append(route_completion_event)
            self.test_status = 'SUCCESS'
            self._percentage_route_completed = 100
    elif self.test_status == 'SUCCESS':
        new_status = py_trees.common.Status.SUCCESS
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    return new_status

class RunningRedLightTest(Criterion):
    """
    Check if an actor is running a red light

    Important parameters:
    - actor: CARLA actor to be used for this test
    - terminate_on_failure [optional]: If True, the complete scenario will terminate upon failure of this test
    """
    DISTANCE_LIGHT = 15

    def __init__(self, actor, name='RunningRedLightTest', terminate_on_failure=False):
        """
        Init
        """
        super(RunningRedLightTest, self).__init__(name, actor, 0, terminate_on_failure=terminate_on_failure)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._actor = actor
        self._world = actor.get_world()
        self._map = CarlaDataProvider.get_map()
        self._list_traffic_lights = []
        self._last_red_light_id = None
        self.actual_value = 0
        self.debug = False
        all_actors = self._world.get_actors()
        for _actor in all_actors:
            if 'traffic_light' in _actor.type_id:
                center, waypoints = self.get_traffic_light_waypoints(_actor)
                self._list_traffic_lights.append((_actor, center, waypoints))

    def is_vehicle_crossing_line(self, seg1, seg2):
        """
        check if vehicle crosses a line segment
        """
        line1 = shapely.geometry.LineString([(seg1[0].x, seg1[0].y), (seg1[1].x, seg1[1].y)])
        line2 = shapely.geometry.LineString([(seg2[0].x, seg2[0].y), (seg2[1].x, seg2[1].y)])
        inter = line1.intersection(line2)
        return not inter.is_empty

    def update(self):
        """
        Check if the actor is running a red light
        """
        new_status = py_trees.common.Status.RUNNING
        transform = CarlaDataProvider.get_transform(self._actor)
        location = transform.location
        if location is None:
            return new_status
        veh_extent = self._actor.bounding_box.extent.x
        tail_close_pt = self.rotate_point(carla.Vector3D(-0.8 * veh_extent, 0.0, location.z), transform.rotation.yaw)
        tail_close_pt = location + carla.Location(tail_close_pt)
        tail_far_pt = self.rotate_point(carla.Vector3D(-veh_extent - 1, 0.0, location.z), transform.rotation.yaw)
        tail_far_pt = location + carla.Location(tail_far_pt)
        for traffic_light, center, waypoints in self._list_traffic_lights:
            if self.debug:
                z = 2.1
                if traffic_light.state == carla.TrafficLightState.Red:
                    color = carla.Color(155, 0, 0)
                elif traffic_light.state == carla.TrafficLightState.Green:
                    color = carla.Color(0, 155, 0)
                else:
                    color = carla.Color(155, 155, 0)
                self._world.debug.draw_point(center + carla.Location(z=z), size=0.2, color=color, life_time=0.01)
                for wp in waypoints:
                    text = '{}.{}'.format(wp.road_id, wp.lane_id)
                    self._world.debug.draw_string(wp.transform.location + carla.Location(x=1, z=z), text, color=color, life_time=0.01)
                    self._world.debug.draw_point(wp.transform.location + carla.Location(z=z), size=0.1, color=color, life_time=0.01)
            center_loc = carla.Location(center)
            if self._last_red_light_id and self._last_red_light_id == traffic_light.id:
                continue
            if center_loc.distance(location) > self.DISTANCE_LIGHT:
                continue
            if traffic_light.state != carla.TrafficLightState.Red:
                continue
            for wp in waypoints:
                tail_wp = self._map.get_waypoint(tail_far_pt)
                ve_dir = CarlaDataProvider.get_transform(self._actor).get_forward_vector()
                wp_dir = wp.transform.get_forward_vector()
                dot_ve_wp = ve_dir.x * wp_dir.x + ve_dir.y * wp_dir.y + ve_dir.z * wp_dir.z
                if tail_wp.road_id == wp.road_id and tail_wp.lane_id == wp.lane_id and (dot_ve_wp > 0):
                    yaw_wp = wp.transform.rotation.yaw
                    lane_width = wp.lane_width
                    location_wp = wp.transform.location
                    lft_lane_wp = self.rotate_point(carla.Vector3D(0.4 * lane_width, 0.0, location_wp.z), yaw_wp + 90)
                    lft_lane_wp = location_wp + carla.Location(lft_lane_wp)
                    rgt_lane_wp = self.rotate_point(carla.Vector3D(0.4 * lane_width, 0.0, location_wp.z), yaw_wp - 90)
                    rgt_lane_wp = location_wp + carla.Location(rgt_lane_wp)
                    if self.is_vehicle_crossing_line((tail_close_pt, tail_far_pt), (lft_lane_wp, rgt_lane_wp)):
                        self.test_status = 'FAILURE'
                        self.actual_value += 1
                        location = traffic_light.get_transform().location
                        red_light_event = TrafficEvent(event_type=TrafficEventType.TRAFFIC_LIGHT_INFRACTION)
                        red_light_event.set_message('Agent ran a red light {} at (x={}, y={}, z={})'.format(traffic_light.id, round(location.x, 3), round(location.y, 3), round(location.z, 3)))
                        red_light_event.set_dict({'id': traffic_light.id, 'x': location.x, 'y': location.y, 'z': location.z})
                        self.list_traffic_events.append(red_light_event)
                        self._last_red_light_id = traffic_light.id
                        break
        if self._terminate_on_failure and self.test_status == 'FAILURE':
            new_status = py_trees.common.Status.FAILURE
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

    def rotate_point(self, point, angle):
        """
        rotate a given point by a given angle
        """
        x_ = math.cos(math.radians(angle)) * point.x - math.sin(math.radians(angle)) * point.y
        y_ = math.sin(math.radians(angle)) * point.x + math.cos(math.radians(angle)) * point.y
        return carla.Vector3D(x_, y_, point.z)

    def get_traffic_light_waypoints(self, traffic_light):
        """
        get area of a given traffic light
        """
        base_transform = traffic_light.get_transform()
        base_rot = base_transform.rotation.yaw
        area_loc = base_transform.transform(traffic_light.trigger_volume.location)
        area_ext = traffic_light.trigger_volume.extent
        x_values = np.arange(-0.9 * area_ext.x, 0.9 * area_ext.x, 1.0)
        area = []
        for x in x_values:
            point = self.rotate_point(carla.Vector3D(x, 0, area_ext.z), base_rot)
            point_location = area_loc + carla.Location(x=point.x, y=point.y)
            area.append(point_location)
        ini_wps = []
        for pt in area:
            wpx = self._map.get_waypoint(pt)
            if not ini_wps or ini_wps[-1].road_id != wpx.road_id or ini_wps[-1].lane_id != wpx.lane_id:
                ini_wps.append(wpx)
        wps = []
        for wpx in ini_wps:
            while not wpx.is_intersection:
                next_wp = wpx.next(0.5)[0]
                if next_wp and (not next_wp.is_intersection):
                    wpx = next_wp
                else:
                    break
            wps.append(wpx)
        return (area_loc, wps)

def update(self):
    """
        Check if the actor is running a red light
        """
    new_status = py_trees.common.Status.RUNNING
    transform = CarlaDataProvider.get_transform(self._actor)
    location = transform.location
    if location is None:
        return new_status
    veh_extent = self._actor.bounding_box.extent.x
    tail_close_pt = self.rotate_point(carla.Vector3D(-0.8 * veh_extent, 0.0, location.z), transform.rotation.yaw)
    tail_close_pt = location + carla.Location(tail_close_pt)
    tail_far_pt = self.rotate_point(carla.Vector3D(-veh_extent - 1, 0.0, location.z), transform.rotation.yaw)
    tail_far_pt = location + carla.Location(tail_far_pt)
    for traffic_light, center, waypoints in self._list_traffic_lights:
        if self.debug:
            z = 2.1
            if traffic_light.state == carla.TrafficLightState.Red:
                color = carla.Color(155, 0, 0)
            elif traffic_light.state == carla.TrafficLightState.Green:
                color = carla.Color(0, 155, 0)
            else:
                color = carla.Color(155, 155, 0)
            self._world.debug.draw_point(center + carla.Location(z=z), size=0.2, color=color, life_time=0.01)
            for wp in waypoints:
                text = '{}.{}'.format(wp.road_id, wp.lane_id)
                self._world.debug.draw_string(wp.transform.location + carla.Location(x=1, z=z), text, color=color, life_time=0.01)
                self._world.debug.draw_point(wp.transform.location + carla.Location(z=z), size=0.1, color=color, life_time=0.01)
        center_loc = carla.Location(center)
        if self._last_red_light_id and self._last_red_light_id == traffic_light.id:
            continue
        if center_loc.distance(location) > self.DISTANCE_LIGHT:
            continue
        if traffic_light.state != carla.TrafficLightState.Red:
            continue
        for wp in waypoints:
            tail_wp = self._map.get_waypoint(tail_far_pt)
            ve_dir = CarlaDataProvider.get_transform(self._actor).get_forward_vector()
            wp_dir = wp.transform.get_forward_vector()
            dot_ve_wp = ve_dir.x * wp_dir.x + ve_dir.y * wp_dir.y + ve_dir.z * wp_dir.z
            if tail_wp.road_id == wp.road_id and tail_wp.lane_id == wp.lane_id and (dot_ve_wp > 0):
                yaw_wp = wp.transform.rotation.yaw
                lane_width = wp.lane_width
                location_wp = wp.transform.location
                lft_lane_wp = self.rotate_point(carla.Vector3D(0.4 * lane_width, 0.0, location_wp.z), yaw_wp + 90)
                lft_lane_wp = location_wp + carla.Location(lft_lane_wp)
                rgt_lane_wp = self.rotate_point(carla.Vector3D(0.4 * lane_width, 0.0, location_wp.z), yaw_wp - 90)
                rgt_lane_wp = location_wp + carla.Location(rgt_lane_wp)
                if self.is_vehicle_crossing_line((tail_close_pt, tail_far_pt), (lft_lane_wp, rgt_lane_wp)):
                    self.test_status = 'FAILURE'
                    self.actual_value += 1
                    location = traffic_light.get_transform().location
                    red_light_event = TrafficEvent(event_type=TrafficEventType.TRAFFIC_LIGHT_INFRACTION)
                    red_light_event.set_message('Agent ran a red light {} at (x={}, y={}, z={})'.format(traffic_light.id, round(location.x, 3), round(location.y, 3), round(location.z, 3)))
                    red_light_event.set_dict({'id': traffic_light.id, 'x': location.x, 'y': location.y, 'z': location.z})
                    self.list_traffic_events.append(red_light_event)
                    self._last_red_light_id = traffic_light.id
                    break
    if self._terminate_on_failure and self.test_status == 'FAILURE':
        new_status = py_trees.common.Status.FAILURE
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    return new_status

class RunningStopTest(Criterion):
    """
    Check if an actor is running a stop sign

    Important parameters:
    - actor: CARLA actor to be used for this test
    - terminate_on_failure [optional]: If True, the complete scenario will terminate upon failure of this test
    """
    PROXIMITY_THRESHOLD = 50.0
    SPEED_THRESHOLD = 0.1
    WAYPOINT_STEP = 1.0

    def __init__(self, actor, name='RunningStopTest', terminate_on_failure=False):
        """
        """
        super(RunningStopTest, self).__init__(name, actor, 0, terminate_on_failure=terminate_on_failure)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._actor = actor
        self._world = CarlaDataProvider.get_world()
        self._map = CarlaDataProvider.get_map()
        self._list_stop_signs = []
        self._target_stop_sign = None
        self._stop_completed = False
        self._affected_by_stop = False
        self.actual_value = 0
        all_actors = self._world.get_actors()
        for _actor in all_actors:
            if 'traffic.stop' in _actor.type_id:
                self._list_stop_signs.append(_actor)

    @staticmethod
    def point_inside_boundingbox(point, bb_center, bb_extent):
        """
        X
        :param point:
        :param bb_center:
        :param bb_extent:
        :return:
        """
        A = carla.Vector2D(bb_center.x - bb_extent.x, bb_center.y - bb_extent.y)
        B = carla.Vector2D(bb_center.x + bb_extent.x, bb_center.y - bb_extent.y)
        D = carla.Vector2D(bb_center.x - bb_extent.x, bb_center.y + bb_extent.y)
        M = carla.Vector2D(point.x, point.y)
        AB = B - A
        AD = D - A
        AM = M - A
        am_ab = AM.x * AB.x + AM.y * AB.y
        ab_ab = AB.x * AB.x + AB.y * AB.y
        am_ad = AM.x * AD.x + AM.y * AD.y
        ad_ad = AD.x * AD.x + AD.y * AD.y
        return am_ab > 0 and am_ab < ab_ab and (am_ad > 0) and (am_ad < ad_ad)

    def is_actor_affected_by_stop(self, actor, stop, multi_step=20):
        """
        Check if the given actor is affected by the stop
        """
        affected = False
        current_location = actor.get_location()
        stop_location = stop.get_transform().location
        if stop_location.distance(current_location) > self.PROXIMITY_THRESHOLD:
            return affected
        stop_t = stop.get_transform()
        transformed_tv = stop_t.transform(stop.trigger_volume.location)
        list_locations = [current_location]
        waypoint = self._map.get_waypoint(current_location)
        for _ in range(multi_step):
            if waypoint:
                next_wps = waypoint.next(self.WAYPOINT_STEP)
                if not next_wps:
                    break
                waypoint = next_wps[0]
                if not waypoint:
                    break
                list_locations.append(waypoint.transform.location)
        for actor_location in list_locations:
            if self.point_inside_boundingbox(actor_location, transformed_tv, stop.trigger_volume.extent):
                affected = True
        return affected

    def _scan_for_stop_sign(self):
        target_stop_sign = None
        ve_tra = CarlaDataProvider.get_transform(self._actor)
        ve_dir = ve_tra.get_forward_vector()
        wp = self._map.get_waypoint(ve_tra.location)
        wp_dir = wp.transform.get_forward_vector()
        dot_ve_wp = ve_dir.x * wp_dir.x + ve_dir.y * wp_dir.y + ve_dir.z * wp_dir.z
        if dot_ve_wp > 0:
            for stop_sign in self._list_stop_signs:
                if self.is_actor_affected_by_stop(self._actor, stop_sign):
                    target_stop_sign = stop_sign
                    break
        return target_stop_sign

    def update(self):
        """
        Check if the actor is running a red light
        """
        new_status = py_trees.common.Status.RUNNING
        location = self._actor.get_location()
        if location is None:
            return new_status
        if not self._target_stop_sign:
            self._target_stop_sign = self._scan_for_stop_sign()
        else:
            if not self._stop_completed:
                current_speed = CarlaDataProvider.get_velocity(self._actor)
                if current_speed < self.SPEED_THRESHOLD:
                    self._stop_completed = True
            if not self._affected_by_stop:
                stop_location = self._target_stop_sign.get_location()
                stop_extent = self._target_stop_sign.trigger_volume.extent
                if self.point_inside_boundingbox(location, stop_location, stop_extent):
                    self._affected_by_stop = True
            if not self.is_actor_affected_by_stop(self._actor, self._target_stop_sign):
                if not self._stop_completed and self._affected_by_stop:
                    self.actual_value += 1
                    self.test_status = 'FAILURE'
                    stop_location = self._target_stop_sign.get_transform().location
                    running_stop_event = TrafficEvent(event_type=TrafficEventType.STOP_INFRACTION)
                    running_stop_event.set_message('Agent ran a stop with id={} at (x={}, y={}, z={})'.format(self._target_stop_sign.id, round(stop_location.x, 3), round(stop_location.y, 3), round(stop_location.z, 3)))
                    running_stop_event.set_dict({'id': self._target_stop_sign.id, 'x': stop_location.x, 'y': stop_location.y, 'z': stop_location.z})
                    self.list_traffic_events.append(running_stop_event)
                self._target_stop_sign = None
                self._stop_completed = False
                self._affected_by_stop = False
        if self._terminate_on_failure and self.test_status == 'FAILURE':
            new_status = py_trees.common.Status.FAILURE
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

@staticmethod
def point_inside_boundingbox(point, bb_center, bb_extent):
    """
        X
        :param point:
        :param bb_center:
        :param bb_extent:
        :return:
        """
    A = carla.Vector2D(bb_center.x - bb_extent.x, bb_center.y - bb_extent.y)
    B = carla.Vector2D(bb_center.x + bb_extent.x, bb_center.y - bb_extent.y)
    D = carla.Vector2D(bb_center.x - bb_extent.x, bb_center.y + bb_extent.y)
    M = carla.Vector2D(point.x, point.y)
    AB = B - A
    AD = D - A
    AM = M - A
    am_ab = AM.x * AB.x + AM.y * AB.y
    ab_ab = AB.x * AB.x + AB.y * AB.y
    am_ad = AM.x * AD.x + AM.y * AD.y
    ad_ad = AD.x * AD.x + AD.y * AD.y
    return am_ab > 0 and am_ab < ab_ab and (am_ad > 0) and (am_ad < ad_ad)

def _scan_for_stop_sign(self):
    target_stop_sign = None
    ve_tra = CarlaDataProvider.get_transform(self._actor)
    ve_dir = ve_tra.get_forward_vector()
    wp = self._map.get_waypoint(ve_tra.location)
    wp_dir = wp.transform.get_forward_vector()
    dot_ve_wp = ve_dir.x * wp_dir.x + ve_dir.y * wp_dir.y + ve_dir.z * wp_dir.z
    if dot_ve_wp > 0:
        for stop_sign in self._list_stop_signs:
            if self.is_actor_affected_by_stop(self._actor, stop_sign):
                target_stop_sign = stop_sign
                break
    return target_stop_sign

def update(self):
    """
        Check if the actor is running a red light
        """
    new_status = py_trees.common.Status.RUNNING
    location = self._actor.get_location()
    if location is None:
        return new_status
    if not self._target_stop_sign:
        self._target_stop_sign = self._scan_for_stop_sign()
    else:
        if not self._stop_completed:
            current_speed = CarlaDataProvider.get_velocity(self._actor)
            if current_speed < self.SPEED_THRESHOLD:
                self._stop_completed = True
        if not self._affected_by_stop:
            stop_location = self._target_stop_sign.get_location()
            stop_extent = self._target_stop_sign.trigger_volume.extent
            if self.point_inside_boundingbox(location, stop_location, stop_extent):
                self._affected_by_stop = True
        if not self.is_actor_affected_by_stop(self._actor, self._target_stop_sign):
            if not self._stop_completed and self._affected_by_stop:
                self.actual_value += 1
                self.test_status = 'FAILURE'
                stop_location = self._target_stop_sign.get_transform().location
                running_stop_event = TrafficEvent(event_type=TrafficEventType.STOP_INFRACTION)
                running_stop_event.set_message('Agent ran a stop with id={} at (x={}, y={}, z={})'.format(self._target_stop_sign.id, round(stop_location.x, 3), round(stop_location.y, 3), round(stop_location.z, 3)))
                running_stop_event.set_dict({'id': self._target_stop_sign.id, 'x': stop_location.x, 'y': stop_location.y, 'z': stop_location.z})
                self.list_traffic_events.append(running_stop_event)
            self._target_stop_sign = None
            self._stop_completed = False
            self._affected_by_stop = False
    if self._terminate_on_failure and self.test_status == 'FAILURE':
        new_status = py_trees.common.Status.FAILURE
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    return new_status

def location_route_to_gps(route, lat_ref, lon_ref):
    """
        Locate each waypoint of the route into gps, (lat long ) representations.
    :param route:
    :param lat_ref:
    :param lon_ref:
    :return:
    """
    gps_route = []
    for transform, connection in route:
        gps_point = _location_to_gps(lat_ref, lon_ref, transform.location)
        gps_route.append((gps_point, connection))
    return gps_route

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

class MetricsLog(object):
    """
    Utility class to query the log.
    """

    def __init__(self, recorder):
        """
        Initializes the log class and parses it to extract the dictionaries.
        """
        parser = MetricsParser(recorder)
        self._simulation, self._actors, self._frames = parser.parse_recorder_info()

    def get_actor_collisions(self, actor_id):
        """
        Returns a dict where the keys are the frame number and the values,
        a list of actor ids the actor collided with.

        Args:
            actor_id (int): ID of the actor.
        """
        actor_collisions = {}
        for i, frame in enumerate(self._frames):
            collisions = frame['events']['collisions']
            if actor_id in collisions:
                actor_collisions.update({i: collisions[actor_id]})
        return actor_collisions

    def get_total_frame_count(self):
        """
        Returns an int with the total amount of frames the simulation lasted.
        """
        return self._simulation['total_frames']

    def get_elapsed_time(self, frame):
        """
        Returns a float with the elapsed time of a specific frame.
        """
        return self._frames[frame]['frame']['elapsed_time']

    def get_delta_time(self, frame):
        """
        Returns a float with the delta time of a specific frame.
        """
        return self._frames[frame]['frame']['delta_time']

    def get_platform_time(self, frame):
        """
        Returns a float with the platform time time of a specific frame.
        """
        return self._frames[frame]['frame']['platform_time']

    def get_ego_vehicle_id(self):
        """
        Returns the id of the ego vehicle.
        """
        return self.get_actor_ids_with_role_name('hero')[0]

    def get_actor_ids_with_role_name(self, role_name):
        """
        Returns a list of actor ids that match the given role_name.

        Args:
            role_name (str): string with the desired role_name to filter the actors.
        """
        actor_list = []
        for actor_id in self._actors:
            actor = self._actors[actor_id]
            if 'role_name' in actor and actor['role_name'] == role_name:
                actor_list.append(actor_id)
        return actor_list

    def get_actor_ids_with_type_id(self, type_id):
        """
        Returns a list of actor ids that match the given type_id, matching fnmatch standard.

        Args:
            type_id (str): string with the desired type id to filter the actors.
        """
        actor_list = []
        for actor_id in self._actors:
            actor = self._actors[actor_id]
            if 'type_id' in actor and fnmatch.fnmatch(actor['type_id'], type_id):
                actor_list.append(actor_id)
        return actor_list

    def get_actor_attributes(self, actor_id):
        """
        Returns a dictionary with all the attributes of an actor.

        Args:
            actor_id (int): ID of the actor.
        """
        if actor_id in self._actors:
            return self._actors[actor_id]
        return None

    def get_actor_bounding_box(self, actor_id):
        """
        Returns the bounding box of the specified actor

        Args:
            actor_id (int): Id of the actor
        """
        if actor_id in self._actors:
            if 'bounding_box' in self._actors[actor_id]:
                return self._actors[actor_id]['bounding_box']
            return None
        return None

    def get_traffic_light_trigger_volume(self, traffic_light_id):
        """
        Returns the trigger volume of the specified traffic light

        Args:
            actor_id (int): Id of the traffic light
        """
        if traffic_light_id in self._actors:
            if 'trigger_volume' in self._actors[traffic_light_id]:
                return self._actors[traffic_light_id]['trigger_volume']
            return None
        return None

    def get_actor_alive_frames(self, actor_id):
        """
        Returns a tuple with the first and last frame an actor was alive.
        It is important to note that frames start at 1, not 0.

        Args:
            actor_id (int): Id of the actor
        """
        if actor_id in self._actors:
            actor_info = self._actors[actor_id]
            first_frame = actor_info['created']
            if 'destroyed' in actor_info:
                last_frame = actor_info['destroyed'] - 1
            else:
                last_frame = self.get_total_frame_count()
            return (first_frame, last_frame)
        return (None, None)

    def _get_actor_state(self, actor_id, state, frame):
        """
        Given an actor id, returns the specific variable of that actor at a given frame.
        Returns None if the actor_id or the state are missing.

        Args:
            actor_id (int): Id of the actor to be checked.
            frame: (int): frame number of the simulation.
            attribute (str): name of the actor's attribute to be returned.
        """
        frame_state = self._frames[frame - 1]['actors']
        if actor_id in frame_state:
            if state not in frame_state[actor_id]:
                return None
            state_info = frame_state[actor_id][state]
            return state_info
        return None

    def _get_all_actor_states(self, actor_id, state, first_frame=None, last_frame=None):
        """
        Given an actor id, returns a list of the specific variable of that actor during
        a frame interval. Some elements might be None.

        By default, first_frame and last_frame are the start and end of the simulation, respectively.

        Args:
            actor_id (int): ID of the actor.
            attribute: name of the actor's attribute to be returned.
            first_frame (int): First frame checked. By default, 0.
            last_frame (int): Last frame checked. By default, max number of frames.
        """
        if first_frame is None:
            first_frame = 1
        if last_frame is None:
            last_frame = self.get_total_frame_count()
        state_list = []
        for frame_number in range(first_frame, last_frame + 1):
            state_info = self._get_actor_state(actor_id, state, frame_number)
            state_list.append(state_info)
        return state_list

    def _get_states_at_frame(self, frame, state, actor_list=None):
        """
        Returns a dict where the keys are the frame number, and the values are the
        carla.Transform of the actor at the given frame.

        By default, all actors will be considered.
        """
        states = {}
        actor_info = self._frames[frame]['actors']
        for actor_id in actor_info:
            if not actor_list:
                _state = self._get_actor_state(actor_id, state, frame)
                if _state:
                    states.update({actor_id: _state})
            elif actor_id in actor_list:
                _state = self._get_actor_state(actor_id, state, frame)
                states.update({actor_id: _state})
        return states

    def get_actor_transform(self, actor_id, frame):
        """
        Returns the transform of the actor at a given frame.
        """
        return self._get_actor_state(actor_id, 'transform', frame)

    def get_all_actor_transforms(self, actor_id, first_frame=None, last_frame=None):
        """
        Returns a list with all the transforms of the actor at the frame interval.
        """
        return self._get_all_actor_states(actor_id, 'transform', first_frame, last_frame)

    def get_actor_transforms_at_frame(self, frame, actor_list=None):
        """
        Returns a dictionary {int - carla.Transform} with the actor ID and transform
        at a given frame of all the actors at actor_list.
        """
        return self._get_states_at_frame(frame, 'transform', actor_list)

    def get_actor_velocity(self, actor_id, frame):
        """
        Returns the velocity of the actor at a given frame.
        """
        return self._get_actor_state(actor_id, 'velocity', frame)

    def get_all_actor_velocities(self, actor_id, first_frame=None, last_frame=None):
        """
        Returns a list with all the velocities of the actor at the frame interval.
        """
        return self._get_all_actor_states(actor_id, 'velocity', first_frame, last_frame)

    def get_actor_velocities_at_frame(self, frame, actor_list=None):
        """
        Returns a dictionary {int - carla.Vector3D} with the actor ID and velocity
        at a given frame of all the actors at actor_list.
        """
        return self._get_states_at_frame(frame, 'velocity', actor_list)

    def get_actor_angular_velocity(self, actor_id, frame):
        """
        Returns the angular velocity of the actor at a given frame.
        """
        return self._get_actor_state(actor_id, 'angular_velocity', frame)

    def get_all_actor_angular_velocities(self, actor_id, first_frame=None, last_frame=None):
        """
        Returns a list with all the angular velocities of the actor at the frame interval.
        """
        return self._get_all_actor_states(actor_id, 'angular_velocity', first_frame, last_frame)

    def get_actor_angular_velocities_at_frame(self, frame, actor_list=None):
        """
        Returns a dictionary {int - carla.Vector3D} with the actor ID and angular velocity
        at a given frame of all the actors at actor_list.
        """
        return self._get_states_at_frame(frame, 'angular_velocity', actor_list)

    def get_actor_acceleration(self, actor_id, frame):
        """
        Returns the acceleration of the actor at a given frame.
        """
        return self._get_actor_state(actor_id, 'acceleration', frame)

    def get_all_actor_accelerations(self, actor_id, first_frame=None, last_frame=None):
        """
        Returns a list with all the accelerations of the actor at the frame interval.
        """
        return self._get_all_actor_states(actor_id, 'acceleration', first_frame, last_frame)

    def get_actor_accelerations_at_frame(self, frame, actor_list=None):
        """
        Returns a dictionary {int - carla.Vector3D} with the actor ID and angular velocity
        at a given frame of all the actors at actor_list.
        """
        return self._get_states_at_frame(frame, 'acceleration', actor_list)

    def get_vehicle_control(self, vehicle_id, frame):
        """
        Returns the control of the vehicle at a given frame.
        """
        return self._get_actor_state(vehicle_id, 'control', frame)

    def get_vehicle_physics_control(self, vehicle_id, frame):
        """
        Returns the carla.VehiclePhysicsControl of a vehicle at a given frame.
        Returns None if the id can't be found.
        """
        for i in range(frame - 1, -1, -1):
            physics_info = self._frames[i]['events']['physics_control']
            if vehicle_id in physics_info:
                return physics_info[vehicle_id]
        return None

    def get_walker_speed(self, walker_id, frame):
        """
        Returns the speed of the walker at a specific frame.
        """
        return self._get_actor_state(walker_id, 'speed', frame)

    def get_traffic_light_state(self, traffic_light_id, frame):
        """
        Returns the state of the traffic light at a specific frame.
        """
        return self._get_actor_state(traffic_light_id, 'state', frame)

    def is_traffic_light_frozen(self, traffic_light_id, frame):
        """
        Returns whether or not the traffic light is frozen at a specific frame.
        """
        return self._get_actor_state(traffic_light_id, 'frozen', frame)

    def get_traffic_light_elapsed_time(self, traffic_light_id, frame):
        """
        Returns the elapsed time of the traffic light at a specific frame.
        """
        return self._get_actor_state(traffic_light_id, 'elapsed_time', frame)

    def get_traffic_light_state_time(self, traffic_light_id, state, frame):
        """
        Returns the state time of the traffic light at a specific frame.
        Returns None if the id can't be found.
        """
        for i in range(frame - 1, -1, -1):
            state_times_info = self._frames[i]['events']['traffic_light_state_time']
            if traffic_light_id in state_times_info:
                states = state_times_info[traffic_light_id]
                if state in states:
                    return state_times_info[traffic_light_id][state]
        return None

    def get_vehicle_lights(self, vehicle_id, frame):
        """
        Returns the vehicle lights of the vehicle at a specific frame.
        """
        return self._get_actor_state(vehicle_id, 'lights', frame)

    def is_vehicle_light_active(self, light, vehicle_id, frame):
        """
        Returns the elapsed time of the traffic light at a specific frame.
        """
        lights = self.get_vehicle_lights(vehicle_id, frame)
        if light in lights:
            return True
        return False

    def get_scene_light_state(self, light_id, frame):
        """
        Returns the state of the scene light at a specific frame.
        Returns None if the id can't be found.
        """
        for i in range(frame - 1, -1, -1):
            scene_lights_info = self._frames[i]['events']['scene_lights']
            if light_id in scene_lights_info:
                return scene_lights_info[light_id]
        return None

def get_ego_vehicle_id(self):
    """
        Returns the id of the ego vehicle.
        """
    return self.get_actor_ids_with_role_name('hero')[0]

def get_actor_ids_with_role_name(self, role_name):
    """
        Returns a list of actor ids that match the given role_name.

        Args:
            role_name (str): string with the desired role_name to filter the actors.
        """
    actor_list = []
    for actor_id in self._actors:
        actor = self._actors[actor_id]
        if 'role_name' in actor and actor['role_name'] == role_name:
            actor_list.append(actor_id)
    return actor_list

def get_actor_ids_with_type_id(self, type_id):
    """
        Returns a list of actor ids that match the given type_id, matching fnmatch standard.

        Args:
            type_id (str): string with the desired type id to filter the actors.
        """
    actor_list = []
    for actor_id in self._actors:
        actor = self._actors[actor_id]
        if 'type_id' in actor and fnmatch.fnmatch(actor['type_id'], type_id):
            actor_list.append(actor_id)
    return actor_list

def parse_vector_list(info):
    """
    Parses a list of string into a list of Vector2D

    Args:
        info (list): list corresponding to a row of the recorder
    """
    vector_list = []
    for i in range(0, len(info), 2):
        vector = carla.Vector2D(float(info[i][1:-1]), float(info[i + 1][:-1]))
        vector_list.append(vector)
    return vector_list

class DistanceBetweenVehicles(BasicMetric):
    """
    Metric class DistanceBetweenVehicles
    """

    def _create_metric(self, town_map, log, criteria):
        """
        Implementation of the metric. This is an example to show how to use the recorder,
        accessed via the log.
        """
        ego_id = log.get_ego_vehicle_id()
        adv_id = log.get_actor_ids_with_role_name('scenario')[0]
        dist_list = []
        frames_list = []
        start_ego, end_ego = log.get_actor_alive_frames(ego_id)
        start_adv, end_adv = log.get_actor_alive_frames(adv_id)
        start = max(start_ego, start_adv)
        end = min(end_ego, end_adv)
        for i in range(start, end):
            ego_location = log.get_actor_transform(ego_id, i).location
            adv_location = log.get_actor_transform(adv_id, i).location
            if adv_location.z < -10:
                continue
            dist_v = ego_location - adv_location
            dist = math.sqrt(dist_v.x * dist_v.x + dist_v.y * dist_v.y + dist_v.z * dist_v.z)
            dist_list.append(dist)
            frames_list.append(i)
        plt.plot(frames_list, dist_list)
        plt.ylabel('Distance [m]')
        plt.xlabel('Frame number')
        plt.title('Distance between the ego vehicle and the adversary over time')
        plt.show()

def _create_metric(self, town_map, log, criteria):
    """
        Implementation of the metric. This is an example to show how to use the recorder,
        accessed via the log.
        """
    ego_id = log.get_ego_vehicle_id()
    adv_id = log.get_actor_ids_with_role_name('scenario')[0]
    dist_list = []
    frames_list = []
    start_ego, end_ego = log.get_actor_alive_frames(ego_id)
    start_adv, end_adv = log.get_actor_alive_frames(adv_id)
    start = max(start_ego, start_adv)
    end = min(end_ego, end_adv)
    for i in range(start, end):
        ego_location = log.get_actor_transform(ego_id, i).location
        adv_location = log.get_actor_transform(adv_id, i).location
        if adv_location.z < -10:
            continue
        dist_v = ego_location - adv_location
        dist = math.sqrt(dist_v.x * dist_v.x + dist_v.y * dist_v.y + dist_v.z * dist_v.z)
        dist_list.append(dist)
        frames_list.append(i)
    plt.plot(frames_list, dist_list)
    plt.ylabel('Distance [m]')
    plt.xlabel('Frame number')
    plt.title('Distance between the ego vehicle and the adversary over time')
    plt.show()

class DistanceToLaneCenter(BasicMetric):
    """
    Metric class DistanceToLaneCenter
    """

    def _create_metric(self, town_map, log, criteria):
        """
        Implementation of the metric.
        """
        ego_id = log.get_ego_vehicle_id()
        dist_list = []
        frames_list = []
        start, end = log.get_actor_alive_frames(ego_id)
        for i in range(start, end + 1):
            ego_location = log.get_actor_transform(ego_id, i).location
            ego_waypoint = town_map.get_waypoint(ego_location)
            a = ego_location - ego_waypoint.transform.location
            b = ego_waypoint.transform.get_right_vector()
            b_norm = math.sqrt(b.x * b.x + b.y * b.y + b.z * b.z)
            ab_dot = a.x * b.x + a.y * b.y + a.z * b.z
            dist_v = ab_dot / (b_norm * b_norm) * b
            dist = math.sqrt(dist_v.x * dist_v.x + dist_v.y * dist_v.y + dist_v.z * dist_v.z)
            c = ego_waypoint.transform.get_forward_vector()
            ac_cross = c.x * a.y - c.y * a.x
            if ac_cross < 0:
                dist *= -1
            dist_list.append(dist)
            frames_list.append(i)
        results = {'frames': frames_list, 'distance': dist_list}
        with open('srunner/metrics/data/DistanceToLaneCenter_results.json', 'w') as fw:
            json.dump(results, fw, sort_keys=False, indent=4)

def _create_metric(self, town_map, log, criteria):
    """
        Implementation of the metric.
        """
    ego_id = log.get_ego_vehicle_id()
    dist_list = []
    frames_list = []
    start, end = log.get_actor_alive_frames(ego_id)
    for i in range(start, end + 1):
        ego_location = log.get_actor_transform(ego_id, i).location
        ego_waypoint = town_map.get_waypoint(ego_location)
        a = ego_location - ego_waypoint.transform.location
        b = ego_waypoint.transform.get_right_vector()
        b_norm = math.sqrt(b.x * b.x + b.y * b.y + b.z * b.z)
        ab_dot = a.x * b.x + a.y * b.y + a.z * b.z
        dist_v = ab_dot / (b_norm * b_norm) * b
        dist = math.sqrt(dist_v.x * dist_v.x + dist_v.y * dist_v.y + dist_v.z * dist_v.z)
        c = ego_waypoint.transform.get_forward_vector()
        ac_cross = c.x * a.y - c.y * a.x
        if ac_cross < 0:
            dist *= -1
        dist_list.append(dist)
        frames_list.append(i)
    results = {'frames': frames_list, 'distance': dist_list}
    with open('srunner/metrics/data/DistanceToLaneCenter_results.json', 'w') as fw:
        json.dump(results, fw, sort_keys=False, indent=4)

def scenarios_list():
    scen_type_dict_lst = []
    for scenario_ in scenarios_:
        scen_type_dict = {}
        scen_type_dict['available_event_configurations'] = []
        scen_type_dict['scenario_type'] = scenario_
        scen_type_dict_lst.append(scen_type_dict)
    return scen_type_dict_lst

def gen_skeleton_dict(towns_, scenarios_):

    def scenarios_list():
        scen_type_dict_lst = []
        for scenario_ in scenarios_:
            scen_type_dict = {}
            scen_type_dict['available_event_configurations'] = []
            scen_type_dict['scenario_type'] = scenario_
            scen_type_dict_lst.append(scen_type_dict)
        return scen_type_dict_lst
    skeleton = {'available_scenarios': []}
    for town_ in towns_:
        skeleton['available_scenarios'].append({town_: scenarios_list()})
    return skeleton

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

def location_route_to_gps(route, lat_ref, lon_ref):
    """
        Locate each waypoint of the route into gps, (lat long ) representations.
    :param route:
    :param lat_ref:
    :param lon_ref:
    :return:
    """
    gps_route = []
    for transform, connection in route:
        gps_point = _location_to_gps(lat_ref, lon_ref, transform.location)
        gps_route.append((gps_point, connection))
    return gps_route

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

def register_module(self, module):
    self.modules.append(module)

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

def lateral_shift(transform, shift):
    transform.rotation.yaw += 90
    return transform.location + shift * transform.get_forward_vector()

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

def sensors(self):
    sensors = [{'type': 'sensor.camera.rgb', 'x': self.config.camera_pos[0], 'y': self.config.camera_pos[1], 'z': self.config.camera_pos[2], 'roll': self.config.camera_rot_0[0], 'pitch': self.config.camera_rot_0[1], 'yaw': self.config.camera_rot_0[2], 'width': self.config.camera_width, 'height': self.config.camera_height, 'fov': self.config.camera_fov, 'id': 'rgb_front'}, {'type': 'sensor.camera.rgb', 'x': self.config.camera_pos[0], 'y': self.config.camera_pos[1], 'z': self.config.camera_pos[2], 'roll': self.config.camera_rot_1[0], 'pitch': self.config.camera_rot_1[1], 'yaw': self.config.camera_rot_1[2], 'width': self.config.camera_width, 'height': self.config.camera_height, 'fov': self.config.camera_fov, 'id': 'rgb_left'}, {'type': 'sensor.camera.rgb', 'x': self.config.camera_pos[0], 'y': self.config.camera_pos[1], 'z': self.config.camera_pos[2], 'roll': self.config.camera_rot_2[0], 'pitch': self.config.camera_rot_2[1], 'yaw': self.config.camera_rot_2[2], 'width': self.config.camera_width, 'height': self.config.camera_height, 'fov': self.config.camera_fov, 'id': 'rgb_right'}, {'type': 'sensor.other.imu', 'x': 0.0, 'y': 0.0, 'z': 0.0, 'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0, 'sensor_tick': self.config.carla_frame_rate, 'id': 'imu'}, {'type': 'sensor.other.gnss', 'x': 0.0, 'y': 0.0, 'z': 0.0, 'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0, 'sensor_tick': 0.01, 'id': 'gps'}, {'type': 'sensor.speedometer', 'reading_frequency': self.config.carla_fps, 'id': 'speed'}]
    if SAVE_PATH != None:
        sensors.append({'type': 'sensor.camera.rgb', 'x': -4.5, 'y': 0.0, 'z': 2.3, 'roll': 0.0, 'pitch': -15.0, 'yaw': 0.0, 'width': 960, 'height': 480, 'fov': 100, 'id': 'rgb_back'})
    if self.backbone != 'latentTF':
        sensors.append({'type': 'sensor.lidar.ray_cast', 'x': self.lidar_pos[0], 'y': self.lidar_pos[1], 'z': self.lidar_pos[2], 'roll': self.config.lidar_rot[0], 'pitch': self.config.lidar_rot[1], 'yaw': self.config.lidar_rot[2], 'id': 'lidar'})
    return sensors

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

class PIDController(object):

    def __init__(self, K_P=1.0, K_I=0.0, K_D=0.0, n=20):
        self._K_P = K_P
        self._K_I = K_I
        self._K_D = K_D
        self._window = deque([0 for _ in range(n)], maxlen=n)

    def step(self, error):
        self._window.append(error)
        if len(self._window) >= 2:
            integral = np.mean(self._window)
            derivative = self._window[-1] - self._window[-2]
        else:
            integral = 0.0
            derivative = 0.0
        return self._K_P * error + self._K_I * integral + self._K_D * derivative

def step(self, error):
    self._window.append(error)
    if len(self._window) >= 2:
        integral = np.mean(self._window)
        derivative = self._window[-1] - self._window[-2]
    else:
        integral = 0.0
        derivative = 0.0
    return self._K_P * error + self._K_I * integral + self._K_D * derivative

