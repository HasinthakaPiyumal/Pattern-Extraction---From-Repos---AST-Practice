# Cluster 2

def convert_json_to_transform(actor_dict):
    """
    Convert a JSON string to a CARLA transform
    """
    return carla.Transform(location=carla.Location(x=float(actor_dict['x']), y=float(actor_dict['y']), z=float(actor_dict['z'])), rotation=carla.Rotation(roll=0.0, pitch=0.0, yaw=float(actor_dict['yaw'])))

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

def convert_json_to_transform(actor_dict):
    """
    Convert a JSON string to a CARLA transform
    """
    return carla.Transform(location=carla.Location(x=float(actor_dict['x']), y=float(actor_dict['y']), z=float(actor_dict['z'])), rotation=carla.Rotation(roll=0.0, pitch=0.0, yaw=float(actor_dict['yaw'])))

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
def convert_waypoint_float(waypoint):
    """
        Convert waypoint values to float
        """
    waypoint['x'] = float(waypoint['x'])
    waypoint['y'] = float(waypoint['y'])
    waypoint['z'] = float(waypoint['z'])
    waypoint['yaw'] = float(waypoint['yaw'])

class SpeedometerReader(BaseReader):
    """
    Sensor to measure the speed of the vehicle.
    """
    MAX_CONNECTION_ATTEMPTS = 10

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

    def __call__(self):
        """ We convert the vehicle physics information into a convenient dictionary """
        attempts = 0
        while attempts < self.MAX_CONNECTION_ATTEMPTS:
            try:
                velocity = self._vehicle.get_velocity()
                transform = self._vehicle.get_transform()
                break
            except Exception:
                attempts += 1
                time.sleep(0.2)
                continue
        return {'speed': self._get_forward_speed(transform=transform, velocity=velocity)}

def __call__(self):
    """ We convert the vehicle physics information into a convenient dictionary """
    attempts = 0
    while attempts < self.MAX_CONNECTION_ATTEMPTS:
        try:
            velocity = self._vehicle.get_velocity()
            transform = self._vehicle.get_transform()
            break
        except Exception:
            attempts += 1
            time.sleep(0.2)
            continue
    return {'speed': self._get_forward_speed(transform=transform, velocity=velocity)}

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

def __call__(self):
    """
        Pass the call directly to the agent
        """
    return self._agent()

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

def __call__(self):
    """
        Pass the call directly to the agent
        """
    return self._agent()

def apart_enough(world, _waypoint, scenario_waypoint):
    """
    Uses the same condition as in route_scenario to see if they will
    be differentiated
    """
    TRIGGER_THRESHOLD = 4.0
    TRIGGER_ANGLE_THRESHOLD = 10
    dx = float(_waypoint['x']) - scenario_waypoint.transform.location.x
    dy = float(_waypoint['y']) - scenario_waypoint.transform.location.y
    distance = math.sqrt(dx * dx + dy * dy)
    dyaw = float(_waypoint['yaw']) - scenario_waypoint.transform.rotation.yaw
    dist_angle = math.sqrt(dyaw * dyaw)
    if distance < TRIGGER_THRESHOLD and dist_angle < TRIGGER_ANGLE_THRESHOLD:
        world.debug.draw_point(scenario_waypoint.transform.location + carla.Location(z=1), size=float(0.15), color=carla.Color(255, 0, 0))
    else:
        world.debug.draw_point(scenario_waypoint.transform.location + carla.Location(z=1), size=float(0.15), color=carla.Color(0, 255, 0))

def draw_scenarios(world, scenarios, args):
    """
    Draws all the points related to args.scenarios
    """
    z = 3
    if scenarios['scenario_type'] in args.scenarios:
        number = float(scenarios['scenario_type'][8:])
        color = SCENARIO_COLOR[scenarios['scenario_type']][0]
        event_list = scenarios['available_event_configurations']
        for i in range(len(event_list)):
            event = event_list[i]
            _waypoint = event['transform']
            location = carla.Location(float(_waypoint['x']), float(_waypoint['y']), float(_waypoint['z']))
            scenario_location = location + carla.Location(z=number / z)
            world.debug.draw_point(scenario_location, size=float(0.15), color=color)
            world.debug.draw_string(scenario_location + carla.Location(z=0.1), text=str(i + 1), color=carla.Color(0, 0, 0), life_time=1000)
            if args.debug:
                save_from_dict(args.endpoint, _waypoint)
                spectator = world.get_spectator()
                spectator.set_transform(carla.Transform(location + carla.Location(z=50), carla.Rotation(pitch=-90)))
                print(' Scenario [{}/{}]. Press Enter for the next scenario'.format(i + 1, len(event_list)))
                input()
        world.wait_for_tick()

def modify_junction_scenarios(world, scenarios, args):
    """
    Used to move scenario trigger points:
        1) a certain distance to the front (follows the lane)
        2) a certain distance to the back (does not follow the lane)
    """
    if scenarios['scenario_type'] in args.scenarios:
        event_list = scenarios['available_event_configurations']
        for i in range(len(event_list)):
            event = event_list[i]
            _waypoint = event['transform']
            location = carla.Location(float(_waypoint['x']), float(_waypoint['y']), float(_waypoint['z']))
            rotation = carla.Rotation(float(0), float(_waypoint['pitch']), float(_waypoint['yaw']))
            world.debug.draw_point(location, size=float(0.15), color=carla.Color(0, 255, 255))
            world.debug.draw_string(location + carla.Location(x=1), text=str(i + 1), color=carla.Color(0, 0, 0))
            DISTANCE = 5
            new_waypoint = world.get_map().get_waypoint(location)
            wp_vec = new_waypoint.transform.get_forward_vector()
            new_location = new_waypoint.transform.location - wp_vec * DISTANCE
            scenario_waypoint = world.get_map().get_waypoint(new_location)
            apart_enough(world, _waypoint, scenario_waypoint)
            save_from_wp(args.endpoint, scenario_waypoint)
            spectator = world.get_spectator()
            spectator.set_transform(carla.Transform(scenario_waypoint.transform.location + carla.Location(z=70), carla.Rotation(pitch=-90)))
            print(' Scenario [{}/{}]. Press Enter for the next scenario'.format(i + 1, len(event_list)))
            input()
        world.wait_for_tick()

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
def get_bounding_box(actor):
    bb = actor.trigger_volume.extent
    corners = [carla.Location(x=-bb.x, y=-bb.y), carla.Location(x=bb.x, y=-bb.y), carla.Location(x=bb.x, y=bb.y), carla.Location(x=-bb.x, y=bb.y), carla.Location(x=-bb.x, y=-bb.y)]
    corners = [x + actor.trigger_volume.location for x in corners]
    t = actor.get_transform()
    t.transform(corners)
    return corners

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

def tick(self, clock):
    actors = self.world.get_actors()
    self.actors_with_transforms = [(actor, actor.get_transform()) for actor in actors]
    if self.hero_actor is not None:
        self.hero_transform = self.hero_actor.get_transform()
    self.update_hud_info(clock)

def _render_walkers(self, surface, list_w, world_to_pixel):
    for w in list_w:
        color = COLOR_PLUM_0
        bb = w[0].bounding_box.extent
        corners = [carla.Location(x=-bb.x, y=-bb.y), carla.Location(x=bb.x, y=-bb.y), carla.Location(x=bb.x, y=bb.y), carla.Location(x=-bb.x, y=bb.y)]
        w[1].transform(corners)
        corners = [world_to_pixel(p) for p in corners]
        pygame.draw.polygon(surface, color, corners)

def _compute_scale(self, scale_factor):
    m = self.module_input.mouse_pos
    px = (m[0] - self.scale_offset[0]) / float(self.prev_scaled_size)
    py = (m[1] - self.scale_offset[1]) / float(self.prev_scaled_size)
    diff_between_scales = (float(self.prev_scaled_size) * px - float(self.scaled_size) * px, float(self.prev_scaled_size) * py - float(self.scaled_size) * py)
    self.scale_offset = (self.scale_offset[0] + diff_between_scales[0], self.scale_offset[1] + diff_between_scales[1])
    self.prev_scaled_size = self.scaled_size
    self.map_image.scale_map(scale_factor)

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

def _initialize_actors(self, config):
    """
        Custom initialization
        """
    self._other_actor_transform = config.other_actors[0].transform
    first_vehicle_transform = carla.Transform(carla.Location(config.other_actors[0].transform.location.x, config.other_actors[0].transform.location.y, config.other_actors[0].transform.location.z - 500), config.other_actors[0].transform.rotation)
    first_vehicle = CarlaDataProvider.request_new_actor(config.other_actors[0].model, first_vehicle_transform)
    first_vehicle.set_simulate_physics(enabled=False)
    self.other_actors.append(first_vehicle)

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

def _initialize_actors(self, config):
    """
        Custom initialization
        """
    self._other_actor_transform = config.other_actors[0].transform
    first_vehicle_transform = carla.Transform(carla.Location(config.other_actors[0].transform.location.x, config.other_actors[0].transform.location.y, config.other_actors[0].transform.location.z), config.other_actors[0].transform.rotation)
    first_vehicle = CarlaDataProvider.request_new_actor(config.other_actors[0].model, first_vehicle_transform)
    self.other_actors.append(first_vehicle)

def get_right_driving_lane(waypoint):
    """
    Gets the driving / parking lane that is most to the right of the waypoint
    as well as the number of lane changes done
    """
    lane_changes = 0
    while True:
        wp_next = waypoint.get_right_lane()
        lane_changes += 1
        if wp_next is None or wp_next.lane_type == carla.LaneType.Sidewalk:
            break
        elif wp_next.lane_type == carla.LaneType.Shoulder:
            if is_lane_a_parking(wp_next):
                lane_changes += 1
                waypoint = wp_next
            break
        else:
            waypoint = wp_next
    return (waypoint, lane_changes)

def is_lane_a_parking(waypoint):
    """
    This function filters false negative Shoulder which are in reality Parking lanes.
    These are differentiated from the others because, similar to the driving lanes,
    they have, on the right, a small Shoulder followed by a Sidewalk.
    """
    if waypoint.lane_width > 2:
        wp_next = waypoint.get_right_lane()
        if wp_next is not None and wp_next.lane_type == carla.LaneType.Shoulder:
            wp_next_next = wp_next.get_right_lane()
            if wp_next_next is not None and wp_next_next.lane_type == carla.LaneType.Sidewalk:
                return True
    return False

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

def _initialize_actors(self, config):
    for actor in config.other_actors:
        vehicle = CarlaDataProvider.request_new_actor(actor.model, actor.transform)
        self.other_actors.append(vehicle)
        vehicle.set_simulate_physics(enabled=False)
    fast_car_waypoint, _ = get_waypoint_in_distance(self._reference_waypoint, self._fast_vehicle_distance)
    self.fast_car_visible = carla.Transform(carla.Location(fast_car_waypoint.transform.location.x, fast_car_waypoint.transform.location.y, fast_car_waypoint.transform.location.z + 1), fast_car_waypoint.transform.rotation)
    slow_car_waypoint, _ = get_waypoint_in_distance(self._reference_waypoint, self._slow_vehicle_distance)
    self.slow_car_visible = carla.Transform(carla.Location(slow_car_waypoint.transform.location.x, slow_car_waypoint.transform.location.y, slow_car_waypoint.transform.location.z), slow_car_waypoint.transform.rotation)

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

def _initialize_actors(self, config):
    """
        Custom initialization
        """
    self._other_actor_transform = config.other_actors[0].transform
    first_vehicle_transform = carla.Transform(carla.Location(config.other_actors[0].transform.location.x, config.other_actors[0].transform.location.y, config.other_actors[0].transform.location.z - 500), config.other_actors[0].transform.rotation)
    first_vehicle = CarlaDataProvider.request_new_actor(config.other_actors[0].model, first_vehicle_transform)
    first_vehicle.set_simulate_physics(enabled=False)
    self.other_actors.append(first_vehicle)

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

def convert_json_to_transform(actor_dict):
    """
    Convert a JSON string to a CARLA transform
    """
    return carla.Transform(location=carla.Location(x=float(actor_dict['x']), y=float(actor_dict['y']), z=float(actor_dict['z'])), rotation=carla.Rotation(roll=0.0, pitch=0.0, yaw=float(actor_dict['yaw'])))

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

def _update_ego_vehicle(self):
    """
        Set/Update the start position of the ego_vehicle
        """
    elevate_transform = self.route[0][0]
    elevate_transform.location.z += 0.5
    ego_vehicle = CarlaDataProvider.request_new_actor('vehicle.lincoln.mkz2017', elevate_transform, rolename='hero')
    return ego_vehicle

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

class InTimeToArrivalToVehicleSideLane(InTimeToArrivalToLocation):
    """
    This class contains a check if a actor arrives within a given time
    at another actor's side lane. Inherits from InTimeToArrivalToLocation

    Important parameters:
    - actor: CARLA actor to execute the behavior
    - name: Name of the condition
    - time: The behavior is successful, if TTA is less than _time_ in seconds
    - cut_in_lane: the lane from where the other_actor will do the cut in
    - other_actor: Reference actor used in this behavior

    The condition terminates with SUCCESS, when the actor can reach the other vehicle within the given time
    """
    _max_time_to_arrival = float('inf')

    def __init__(self, actor, other_actor, time, side_lane, comparison_operator=operator.lt, name='InTimeToArrivalToVehicleSideLane'):
        """
        Setup parameters
        """
        self._other_actor = other_actor
        self._side_lane = side_lane
        self._world = CarlaDataProvider.get_world()
        self._map = CarlaDataProvider.get_map(self._world)
        other_location = other_actor.get_transform().location
        other_waypoint = self._map.get_waypoint(other_location)
        if self._side_lane == 'right':
            other_side_waypoint = other_waypoint.get_left_lane()
        elif self._side_lane == 'left':
            other_side_waypoint = other_waypoint.get_right_lane()
        else:
            raise Exception("cut_in_lane must be either 'left' or 'right'")
        other_side_location = other_side_waypoint.transform.location
        super(InTimeToArrivalToVehicleSideLane, self).__init__(actor, time, other_side_location, comparison_operator, name)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)

    def update(self):
        """
        Check if the ego vehicle can arrive at other actor within time
        """
        new_status = py_trees.common.Status.RUNNING
        other_location = CarlaDataProvider.get_location(self._other_actor)
        other_waypoint = self._map.get_waypoint(other_location)
        if self._side_lane == 'right':
            other_side_waypoint = other_waypoint.get_left_lane()
        elif self._side_lane == 'left':
            other_side_waypoint = other_waypoint.get_right_lane()
        else:
            raise Exception("cut_in_lane must be either 'left' or 'right'")
        if other_side_waypoint is None:
            return new_status
        self._target_location = other_side_waypoint.transform.location
        if self._target_location is None:
            return new_status
        new_status = super(InTimeToArrivalToVehicleSideLane, self).update()
        return new_status

def update(self):
    """
        Check if the ego vehicle can arrive at other actor within time
        """
    new_status = py_trees.common.Status.RUNNING
    other_location = CarlaDataProvider.get_location(self._other_actor)
    other_waypoint = self._map.get_waypoint(other_location)
    if self._side_lane == 'right':
        other_side_waypoint = other_waypoint.get_left_lane()
    elif self._side_lane == 'left':
        other_side_waypoint = other_waypoint.get_right_lane()
    else:
        raise Exception("cut_in_lane must be either 'left' or 'right'")
    if other_side_waypoint is None:
        return new_status
    self._target_location = other_side_waypoint.transform.location
    if self._target_location is None:
        return new_status
    new_status = super(InTimeToArrivalToVehicleSideLane, self).update()
    return new_status

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

class ScenarioTriggerer(AtomicBehavior):
    """
    Handles the triggering of the scenarios that are part of a route.

    Initializes a list of blackboard variables to False, and only sets them to True when
    the ego vehicle is very close to the scenarios
    """
    WINDOWS_SIZE = 5

    def __init__(self, actor, route, blackboard_list, distance, repeat_scenarios=False, debug=False, name='ScenarioTriggerer'):
        """
        Setup class members
        """
        super(ScenarioTriggerer, self).__init__(name)
        self._world = CarlaDataProvider.get_world()
        self._map = CarlaDataProvider.get_map()
        self._repeat = repeat_scenarios
        self._debug = debug
        self._actor = actor
        self._route = route
        self._distance = distance
        self._blackboard_list = blackboard_list
        self._triggered_scenarios = []
        self._current_index = 0
        self._route_length = len(self._route)
        self._waypoints, _ = zip(*self._route)

    def update(self):
        new_status = py_trees.common.Status.RUNNING
        location = CarlaDataProvider.get_location(self._actor)
        if location is None:
            return new_status
        lower_bound = self._current_index
        upper_bound = min(self._current_index + self.WINDOWS_SIZE + 1, self._route_length)
        shortest_distance = float('inf')
        closest_index = -1
        for index in range(lower_bound, upper_bound):
            ref_waypoint = self._waypoints[index]
            ref_location = ref_waypoint.location
            dist_to_route = ref_location.distance(location)
            if dist_to_route <= shortest_distance:
                closest_index = index
                shortest_distance = dist_to_route
        if closest_index == -1 or shortest_distance == float('inf'):
            return new_status
        self._current_index = closest_index
        route_location = self._waypoints[closest_index].location
        blackboard = py_trees.blackboard.Blackboard()
        for black_var_name, scen_location in self._blackboard_list:
            scen_distance = route_location.distance(scen_location)
            condition1 = bool(scen_distance < self._distance)
            value = blackboard.get(black_var_name)
            condition2 = bool(not value)
            condition3 = bool(self._repeat or black_var_name not in self._triggered_scenarios)
            if condition1 and condition2 and condition3:
                _ = blackboard.set(black_var_name, True)
                self._triggered_scenarios.append(black_var_name)
                if self._debug:
                    self._world.debug.draw_point(scen_location + carla.Location(z=4), size=0.5, life_time=0.5, color=carla.Color(255, 255, 0))
                    self._world.debug.draw_string(scen_location + carla.Location(z=5), str(black_var_name), False, color=carla.Color(0, 0, 0), life_time=1000)
        return new_status

def update(self):
    new_status = py_trees.common.Status.RUNNING
    location = CarlaDataProvider.get_location(self._actor)
    if location is None:
        return new_status
    lower_bound = self._current_index
    upper_bound = min(self._current_index + self.WINDOWS_SIZE + 1, self._route_length)
    shortest_distance = float('inf')
    closest_index = -1
    for index in range(lower_bound, upper_bound):
        ref_waypoint = self._waypoints[index]
        ref_location = ref_waypoint.location
        dist_to_route = ref_location.distance(location)
        if dist_to_route <= shortest_distance:
            closest_index = index
            shortest_distance = dist_to_route
    if closest_index == -1 or shortest_distance == float('inf'):
        return new_status
    self._current_index = closest_index
    route_location = self._waypoints[closest_index].location
    blackboard = py_trees.blackboard.Blackboard()
    for black_var_name, scen_location in self._blackboard_list:
        scen_distance = route_location.distance(scen_location)
        condition1 = bool(scen_distance < self._distance)
        value = blackboard.get(black_var_name)
        condition2 = bool(not value)
        condition3 = bool(self._repeat or black_var_name not in self._triggered_scenarios)
        if condition1 and condition2 and condition3:
            _ = blackboard.set(black_var_name, True)
            self._triggered_scenarios.append(black_var_name)
            if self._debug:
                self._world.debug.draw_point(scen_location + carla.Location(z=4), size=0.5, life_time=0.5, color=carla.Color(255, 255, 0))
                self._world.debug.draw_string(scen_location + carla.Location(z=5), str(black_var_name), False, color=carla.Color(0, 0, 0), life_time=1000)
    return new_status

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

def get_distance_along_route(route, target_location):
    """
    Calculate the distance of the given location along the route

    Note: If the location is not along the route, the route length will be returned
    """
    wmap = CarlaDataProvider.get_map()
    covered_distance = 0
    prev_position = None
    found = False
    target_location_from_wp = wmap.get_waypoint(target_location).transform.location
    for position, _ in route:
        location = target_location_from_wp
        if not prev_position:
            prev_position = position
            continue
        interval_length_squared = (prev_position.x - position.x) ** 2 + (prev_position.y - position.y) ** 2
        distance_squared = (location.x - prev_position.x) ** 2 + (location.y - prev_position.y) ** 2
        if distance_squared < 0.01:
            break
        if distance_squared < 400 and (not distance_squared < interval_length_squared):
            starting_wp = wmap.get_waypoint(location)
            wp = starting_wp.get_left_lane()
            while wp is not None:
                new_location = wp.transform.location
                new_distance_squared = (new_location.x - prev_position.x) ** 2 + (new_location.y - prev_position.y) ** 2
                if np.sign(starting_wp.lane_id) != np.sign(wp.lane_id):
                    break
                if new_distance_squared < distance_squared:
                    distance_squared = new_distance_squared
                    location = new_location
                else:
                    break
                wp = wp.get_left_lane()
            wp = starting_wp.get_right_lane()
            while wp is not None:
                new_location = wp.transform.location
                new_distance_squared = (new_location.x - prev_position.x) ** 2 + (new_location.y - prev_position.y) ** 2
                if np.sign(starting_wp.lane_id) != np.sign(wp.lane_id):
                    break
                if new_distance_squared < distance_squared:
                    distance_squared = new_distance_squared
                    location = new_location
                else:
                    break
                wp = wp.get_right_lane()
        if distance_squared < interval_length_squared:
            curr_wp = wmap.get_waypoint(position)
            prev_wp = wmap.get_waypoint(prev_position)
            wp = wmap.get_waypoint(location)
            if prev_wp and curr_wp and wp:
                if wp.road_id == prev_wp.road_id or wp.road_id == curr_wp.road_id:
                    if np.sign(wp.lane_id) == np.sign(prev_wp.lane_id) or np.sign(wp.lane_id) == np.sign(curr_wp.lane_id):
                        covered_distance += math.sqrt(distance_squared)
                        found = True
                        break
        covered_distance += math.sqrt(interval_length_squared)
        prev_position = position
    return (covered_distance, found)

def generate_target_waypoint_list_multilane(waypoint, change='left', distance_same_lane=10, distance_other_lane=25, total_lane_change_distance=25, check='true'):
    """
    This methods generates a waypoint list which leads the vehicle to a parallel lane.
    The change input must be 'left' or 'right', depending on which lane you want to change.

    The step distance between waypoints on the same lane is 2m.
    The step distance between the lane change is set to 25m.

    @returns a waypoint list from the starting point to the end point on a right or left parallel lane.
    """
    plan = []
    plan.append((waypoint, RoadOption.LANEFOLLOW))
    step_distance = 2
    if check == 'true':
        lane_change_possibilities = ['Left', 'Right', 'Both']
        if str(waypoint.lane_change) not in lane_change_possibilities:
            return None
    distance = 0
    while distance < distance_same_lane:
        next_wp = plan[-1][0].next(step_distance)
        distance += next_wp[0].transform.location.distance(plan[-1][0].transform.location)
        plan.append((next_wp[0], RoadOption.LANEFOLLOW))
    target_lane_id = None
    if change == 'left':
        wp_left = plan[-1][0].get_left_lane()
        target_lane_id = wp_left.lane_id
        next_wp = wp_left.next(total_lane_change_distance)
        plan.append((next_wp[0], RoadOption.LANEFOLLOW))
    elif change == 'right':
        wp_right = plan[-1][0].get_right_lane()
        target_lane_id = wp_right.lane_id
        next_wp = wp_right.next(total_lane_change_distance)
        plan.append((next_wp[0], RoadOption.LANEFOLLOW))
    else:
        return None
    distance = 0
    while distance < distance_other_lane:
        next_wp = plan[-1][0].next(step_distance)
        distance += next_wp[0].transform.location.distance(plan[-1][0].transform.location)
        plan.append((next_wp[0], RoadOption.LANEFOLLOW))
    return (plan, target_lane_id)

def detect_lane_obstacle(actor, extension_factor=3, margin=1.02):
    """
    This function identifies if an obstacle is present in front of the reference actor
    """
    world = CarlaDataProvider.get_world()
    world_actors = world.get_actors().filter('vehicle.*')
    actor_bbox = actor.bounding_box
    actor_transform = actor.get_transform()
    actor_location = actor_transform.location
    actor_vector = actor_transform.rotation.get_forward_vector()
    actor_vector = np.array([actor_vector.x, actor_vector.y])
    actor_vector = actor_vector / np.linalg.norm(actor_vector)
    actor_vector = actor_vector * (extension_factor - 1) * actor_bbox.extent.x
    actor_location = actor_location + carla.Location(actor_vector[0], actor_vector[1])
    actor_yaw = actor_transform.rotation.yaw
    is_hazard = False
    for adversary in world_actors:
        if adversary.id != actor.id and actor_transform.location.distance(adversary.get_location()) < 50:
            adversary_bbox = adversary.bounding_box
            adversary_transform = adversary.get_transform()
            adversary_loc = adversary_transform.location
            adversary_yaw = adversary_transform.rotation.yaw
            overlap_adversary = RotatedRectangle(adversary_loc.x, adversary_loc.y, 2 * margin * adversary_bbox.extent.x, 2 * margin * adversary_bbox.extent.y, adversary_yaw)
            overlap_actor = RotatedRectangle(actor_location.x, actor_location.y, 2 * margin * actor_bbox.extent.x * extension_factor, 2 * margin * actor_bbox.extent.y, actor_yaw)
            overlap_area = overlap_adversary.intersection(overlap_actor).area
            if overlap_area > 0:
                is_hazard = True
                break
    return is_hazard

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
def convert_waypoint_float(waypoint):
    """
        Convert waypoint values to float
        """
    waypoint['x'] = float(waypoint['x'])
    waypoint['y'] = float(waypoint['y'])
    waypoint['z'] = float(waypoint['z'])
    waypoint['yaw'] = float(waypoint['yaw'])

class ActorConfigurationData(object):
    """
    This is a configuration base class to hold model and transform attributes
    """

    def __init__(self, model, transform, rolename='other', speed=0, autopilot=False, random=False, color=None, category='car', args=None):
        self.model = model
        self.rolename = rolename
        self.transform = transform
        self.speed = speed
        self.autopilot = autopilot
        self.random_location = random
        self.color = color
        self.category = category
        self.args = args

    @staticmethod
    def parse_from_node(node, rolename):
        """
        static method to initialize an ActorConfigurationData from a given ET tree
        """
        model = node.attrib.get('model', 'vehicle.*')
        pos_x = float(node.attrib.get('x', 0))
        pos_y = float(node.attrib.get('y', 0))
        pos_z = float(node.attrib.get('z', 0))
        yaw = float(node.attrib.get('yaw', 0))
        transform = carla.Transform(carla.Location(x=pos_x, y=pos_y, z=pos_z), carla.Rotation(yaw=yaw))
        rolename = node.attrib.get('rolename', rolename)
        speed = node.attrib.get('speed', 0)
        autopilot = False
        if 'autopilot' in node.keys():
            autopilot = True
        random_location = False
        if 'random_location' in node.keys():
            random_location = True
        color = node.attrib.get('color', None)
        return ActorConfigurationData(model, transform, rolename, speed, autopilot, random_location, color)

@staticmethod
def parse_from_node(node, rolename):
    """
        static method to initialize an ActorConfigurationData from a given ET tree
        """
    model = node.attrib.get('model', 'vehicle.*')
    pos_x = float(node.attrib.get('x', 0))
    pos_y = float(node.attrib.get('y', 0))
    pos_z = float(node.attrib.get('z', 0))
    yaw = float(node.attrib.get('yaw', 0))
    transform = carla.Transform(carla.Location(x=pos_x, y=pos_y, z=pos_z), carla.Rotation(yaw=yaw))
    rolename = node.attrib.get('rolename', rolename)
    speed = node.attrib.get('speed', 0)
    autopilot = False
    if 'autopilot' in node.keys():
        autopilot = True
    random_location = False
    if 'random_location' in node.keys():
        random_location = True
    color = node.attrib.get('color', None)
    return ActorConfigurationData(model, transform, rolename, speed, autopilot, random_location, color)

class RouteConfiguration(object):
    """
    This class provides the basic  configuration for a route
    """

    def __init__(self, route=None):
        self.data = route

    def parse_xml(self, node):
        """
        Parse route config XML
        """
        self.data = []
        for waypoint in node.iter('waypoint'):
            x = float(waypoint.attrib.get('x', 0))
            y = float(waypoint.attrib.get('y', 0))
            z = float(waypoint.attrib.get('z', 0))
            c = waypoint.attrib.get('connection', '')
            connection = RoadOption[c.split('.')[1]]
            self.data.append((carla.Location(x, y, z), connection))

def parse_xml(self, node):
    """
        Parse route config XML
        """
    self.data = []
    for waypoint in node.iter('waypoint'):
        x = float(waypoint.attrib.get('x', 0))
        y = float(waypoint.attrib.get('y', 0))
        z = float(waypoint.attrib.get('z', 0))
        c = waypoint.attrib.get('connection', '')
        connection = RoadOption[c.split('.')[1]]
        self.data.append((carla.Location(x, y, z), connection))

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

def __call__(self):
    """
        Pass the call directly to the agent
        """
    return self._agent()

def parse_actor(info):
    """
    Returns a dictionary with the basic actor information

    Args:
        info (list): list corresponding to a row of the recorder
    """
    actor = {'type_id': info[2], 'location': carla.Location(float(info[5][1:-1]) / 100, float(info[6][:-1]) / 100, float(info[7][:-1]) / 100)}
    return actor

def parse_transform(info):
    """
    Parses a list into a carla.Transform

    Args:
        info (list): list corresponding to a row of the recorder
    """
    transform = carla.Transform(carla.Location(float(info[3][1:-1]) / 100, float(info[4][:-1]) / 100, float(info[5][:-1]) / 100), carla.Rotation(float(info[8][:-1]), float(info[9][:-1]), float(info[7][1:-1])))
    return transform

def parse_control(info):
    """
    Parses a list into a carla.VehicleControl

    Args:
        info (list): list corresponding to a row of the recorder
    """
    control = carla.VehicleControl(float(info[5]), float(info[3]), float(info[7]), bool(int(info[9])), int(info[11]) < 0, False, int(info[11]))
    return control

def parse_traffic_light(info):
    """
    Parses a list into a dictionary with all the traffic light's information

    Args:
        info (list): list corresponding to a row of the recorder
    """
    number_to_state = {'0': carla.TrafficLightState.Red, '1': carla.TrafficLightState.Yellow, '2': carla.TrafficLightState.Green, '3': carla.TrafficLightState.Off, '4': carla.TrafficLightState.Unknown}
    traffic_light = {'state': number_to_state[info[3]], 'frozen': bool(int(info[5])), 'elapsed_time': float(info[7])}
    return traffic_light

def parse_scene_lights(info):
    """
    Parses a list into a carla.VehicleLightState

    Args:
        info (list): list corresponding to a row of the recorder
    """
    red = int(float(info[7][1:-1]) * 255)
    green = int(float(info[8][:-1]) * 255)
    blue = int(float(info[9][:-1]) * 255)
    scene_light = carla.LightState(int(float(info[5])), carla.Color(red, green, blue), carla.LightGroup.NONE, bool(info[3]))
    return scene_light

def parse_bounding_box(info):
    """
    Parses a list into a carla.BoundingBox

    Args:
        info (list): list corresponding to a row of the recorder
    """
    location = carla.Location(float(info[3][1:-1]) / 100, float(info[4][:-1]) / 100, float(info[5][:-1]) / 100)
    extent = carla.Vector3D(float(info[7][1:-1]) / 100, float(info[8][:-1]) / 100, float(info[9][:-1]) / 100)
    bbox = carla.BoundingBox(location, extent)
    return bbox

def parse_state_times(info):
    """
    Parses a list into a dict containing the state times of the traffic lights

    Args:
        info (list): list corresponding to a row of the recorder
    """
    state_times = {carla.TrafficLightState.Green: float(info[3]), carla.TrafficLightState.Yellow: float(info[5]), carla.TrafficLightState.Red: float(info[7])}
    return state_times

def parse_gears_control(info):
    """
    Parses a list into a GearPhysicsControl

    Args:
        info (list): list corresponding to a row of the recorder
    """
    gears_control = carla.GearPhysicsControl(float(info[3]), float(info[5]), float(info[7]))
    return gears_control

def parse_wheels_control(info):
    """
    Parses a list into a WheelsPhysicsControl

    Args:
        info (list): list corresponding to a row of the recorder
    """
    gears_control = carla.WheelPhysicsControl(float(info[3]), float(info[5]), float(info[7]), float(info[9]), float(info[11]), float(info[13]), carla.Vector3D())
    return gears_control

def parse_routes_file(route_filename, single_route=None):
    """
    Returns a list of route elements that is where the challenge is going to happen.
    Args:
        route_filename: the path to a set of routes.
        single_route: If set, only this route shall be returned
    Return:
        list_route_descriptions: List of dicts containing the waypoints, id and town of the routes
    """
    list_route_descriptions = []
    tree = ET.parse(route_filename)
    for route in tree.iter('route'):
        route_town = route.attrib['town']
        route_id = route.attrib['id']
        if single_route and route_id != single_route:
            continue
        waypoint_list = []
        for waypoint in route.iter('waypoint'):
            waypoint_list.append(carla.Location(x=float(waypoint.attrib['x']), y=float(waypoint.attrib['y']), z=float(waypoint.attrib['z'])))
        list_route_descriptions.append({'id': route_id, 'town_name': route_town, 'trajectory': waypoint_list})
    return list_route_descriptions

def convert_waypoint_float(waypoint):
    """
    Convert waypoint values to float
    """
    waypoint['x'] = float(waypoint['x'])
    waypoint['y'] = float(waypoint['y'])
    waypoint['z'] = float(waypoint['z'])
    waypoint['yaw'] = float(waypoint['yaw'])

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

def draw_points(self, surface, transform, color=None):
    """ Draws an arrow with a specified color given a transform"""
    end = transform
    start = end
    color_tmp = [int(255) for c_ in range(3)] if not color else color
    color = pygame.Color(*color_tmp) if color is None else color
    pygame.draw.circle(surface, color, start, 5)

class Point(object):

    def __init__(self, point):
        self.location = Location(point[:2])
        self.theta = point[2]
        self.theta_real = point[2]

def __init__(self, point):
    self.location = Location(point[:2])
    self.theta = point[2]
    self.theta_real = point[2]

def get_possible_lane_changes(current_waypoint):
    all_lefts = {}
    all_rights = {}
    tmp_wp = current_waypoint
    lane_side = 'l'
    while True:
        left_w = tmp_wp.get_left_lane()
        if left_w and left_w.lane_type == carla.LaneType.Driving and (0 <= abs(left_w.transform.rotation.yaw - tmp_wp.transform.rotation.yaw) <= 10):
            all_lefts[lane_side] = left_w
            tmp_wp = left_w
            lane_side += 'l'
        else:
            break
    tmp_wp = current_waypoint
    lane_side = 'r'
    while True:
        right_w = tmp_wp.get_right_lane()
        if right_w and right_w.lane_type == carla.LaneType.Driving and (0 <= abs(right_w.transform.rotation.yaw - tmp_wp.transform.rotation.yaw) <= 10):
            all_rights[lane_side] = right_w
            tmp_wp = right_w
            lane_side += 'r'
        else:
            break
    current_dict = {'n': current_waypoint}
    all_choices = {**all_lefts, **all_rights, **current_dict}
    return all_choices

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

def get_nearby_object(self, vehicle_position, actor_list, radius):
    nearby_objects = []
    for actor in actor_list:
        trigger_box_global_pos = actor.get_transform().transform(actor.trigger_volume.location)
        trigger_box_global_pos = carla.Location(x=trigger_box_global_pos.x, y=trigger_box_global_pos.y, z=trigger_box_global_pos.z)
        if trigger_box_global_pos.distance(vehicle_position) < radius:
            nearby_objects.append(actor)
    return nearby_objects

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

