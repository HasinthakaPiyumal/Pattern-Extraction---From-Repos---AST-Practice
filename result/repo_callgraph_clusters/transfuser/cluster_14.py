# Cluster 14

def oneshot_behavior(name, variable_name, behaviour):
    """
    This is taken from py_trees.idiom.oneshot.
    """
    blackboard = py_trees.blackboard.Blackboard()
    _ = blackboard.set(variable_name, False)
    subtree_root = py_trees.composites.Selector(name=name)
    check_flag = py_trees.blackboard.CheckBlackboardVariable(name=variable_name + ' Done?', variable_name=variable_name, expected_value=True, clearing_policy=py_trees.common.ClearingPolicy.ON_INITIALISE)
    set_flag = py_trees.blackboard.SetBlackboardVariable(name='Mark Done', variable_name=variable_name, variable_value=True)
    if isinstance(behaviour, py_trees.composites.Sequence):
        behaviour.add_child(set_flag)
        sequence = behaviour
    else:
        sequence = py_trees.composites.Sequence(name='OneShot')
        sequence.add_children([behaviour, set_flag])
    subtree_root.add_children([check_flag, sequence])
    return subtree_root

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

class MasterScenario(BasicScenario):
    """
    Implementation of a  Master scenario that controls the route.

    This is a single ego vehicle scenario
    """
    category = 'Master'
    radius = 10.0

    def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, criteria_enable=True, timeout=300):
        """
        Setup all relevant parameters and create scenario
        """
        self.config = config
        self.route = None
        self.timeout = timeout
        if hasattr(self.config, 'route'):
            self.route = self.config.route
        else:
            raise ValueError('Master scenario must have a route')
        super(MasterScenario, self).__init__('MasterScenario', ego_vehicles=ego_vehicles, config=config, world=world, debug_mode=debug_mode, terminate_on_failure=True, criteria_enable=criteria_enable)

    def _create_behavior(self):
        """
        Basic behavior do nothing, i.e. Idle
        """
        sequence = py_trees.composites.Sequence('MasterScenario')
        idle_behavior = Idle()
        sequence.add_child(idle_behavior)
        return sequence

    def _create_test_criteria(self):
        """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
        if isinstance(self.route, RouteConfiguration):
            route = self.route.data
        else:
            route = self.route
        collision_criterion = CollisionTest(self.ego_vehicles[0], terminate_on_failure=False)
        route_criterion = InRouteTest(self.ego_vehicles[0], route=route, offroad_max=30, terminate_on_failure=True)
        completion_criterion = RouteCompletionTest(self.ego_vehicles[0], route=route)
        outsidelane_criterion = OutsideRouteLanesTest(self.ego_vehicles[0], route=route)
        red_light_criterion = RunningRedLightTest(self.ego_vehicles[0])
        stop_criterion = RunningStopTest(self.ego_vehicles[0])
        blocked_criterion = ActorSpeedAboveThresholdTest(self.ego_vehicles[0], speed_threshold=0.1, below_threshold_max_time=90.0, terminate_on_failure=True)
        parallel_criteria = py_trees.composites.Parallel('group_criteria', policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)
        parallel_criteria.add_child(completion_criterion)
        parallel_criteria.add_child(collision_criterion)
        parallel_criteria.add_child(route_criterion)
        parallel_criteria.add_child(outsidelane_criterion)
        parallel_criteria.add_child(red_light_criterion)
        parallel_criteria.add_child(stop_criterion)
        parallel_criteria.add_child(blocked_criterion)
        return parallel_criteria

    def __del__(self):
        """
        Remove all actors upon deletion
        """
        self.remove_all_actors()

def _create_behavior(self):
    """
        Basic behavior do nothing, i.e. Idle
        """
    sequence = py_trees.composites.Sequence('MasterScenario')
    idle_behavior = Idle()
    sequence.add_child(idle_behavior)
    return sequence

def _create_test_criteria(self):
    """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
    if isinstance(self.route, RouteConfiguration):
        route = self.route.data
    else:
        route = self.route
    collision_criterion = CollisionTest(self.ego_vehicles[0], terminate_on_failure=False)
    route_criterion = InRouteTest(self.ego_vehicles[0], route=route, offroad_max=30, terminate_on_failure=True)
    completion_criterion = RouteCompletionTest(self.ego_vehicles[0], route=route)
    outsidelane_criterion = OutsideRouteLanesTest(self.ego_vehicles[0], route=route)
    red_light_criterion = RunningRedLightTest(self.ego_vehicles[0])
    stop_criterion = RunningStopTest(self.ego_vehicles[0])
    blocked_criterion = ActorSpeedAboveThresholdTest(self.ego_vehicles[0], speed_threshold=0.1, below_threshold_max_time=90.0, terminate_on_failure=True)
    parallel_criteria = py_trees.composites.Parallel('group_criteria', policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)
    parallel_criteria.add_child(completion_criterion)
    parallel_criteria.add_child(collision_criterion)
    parallel_criteria.add_child(route_criterion)
    parallel_criteria.add_child(outsidelane_criterion)
    parallel_criteria.add_child(red_light_criterion)
    parallel_criteria.add_child(stop_criterion)
    parallel_criteria.add_child(blocked_criterion)
    return parallel_criteria

def oneshot_behavior(name, variable_name, behaviour):
    """
    This is taken from py_trees.idiom.oneshot.
    """
    blackboard = py_trees.blackboard.Blackboard()
    _ = blackboard.set(variable_name, False)
    subtree_root = py_trees.composites.Selector(name=name)
    check_flag = py_trees.blackboard.CheckBlackboardVariable(name=variable_name + ' Done?', variable_name=variable_name, expected_value=True, clearing_policy=py_trees.common.ClearingPolicy.ON_INITIALISE)
    set_flag = py_trees.blackboard.SetBlackboardVariable(name='Mark Done', variable_name=variable_name, variable_value=True)
    if isinstance(behaviour, py_trees.composites.Sequence):
        behaviour.add_child(set_flag)
        sequence = behaviour
    else:
        sequence = py_trees.composites.Sequence(name='OneShot')
        sequence.add_children([behaviour, set_flag])
    subtree_root.add_children([check_flag, sequence])
    return subtree_root

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

def sensors(self):
    """
        Define the sensor suite required by the agent

        :return: a list containing the required sensors
        """
    raise NotImplementedError('This function has to be implemented by the derived classes')

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

def repeatable_behavior(behaviour, name=None):
    """
    This behaviour allows a composite with oneshot ancestors to run multiple
    times, resetting the oneshot variables after each execution
    """
    if not name:
        name = behaviour.name
    clear_descendant_variables = ClearBlackboardVariablesStartingWith(name='Clear Descendant Variables of {}'.format(name), variable_name_beginning=name + '>')
    if isinstance(behaviour, py_trees.composites.Sequence):
        behaviour.add_child(clear_descendant_variables)
        sequence = behaviour
    else:
        sequence = py_trees.composites.Sequence(name='RepeatableBehaviour of {}'.format(name))
        sequence.add_children([behaviour, clear_descendant_variables])
    return sequence

class OpenScenario(BasicScenario):
    """
    Implementation of the OpenSCENARIO scenario
    """

    def __init__(self, world, ego_vehicles, config, config_file, debug_mode=False, criteria_enable=True, timeout=300):
        """
        Setup all relevant parameters and create scenario
        """
        self.config = config
        self.route = None
        self.config_file = config_file
        self.timeout = timeout
        super(OpenScenario, self).__init__('OpenScenario', ego_vehicles=ego_vehicles, config=config, world=world, debug_mode=debug_mode, terminate_on_failure=False, criteria_enable=criteria_enable)

    def _initialize_environment(self, world):
        """
        Initialization of weather and road friction.
        """
        pass

    def _create_environment_behavior(self):
        env_behavior = py_trees.composites.Parallel(policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ALL, name='EnvironmentBehavior')
        weather_update = ChangeWeather(OpenScenarioParser.get_weather_from_env_action(self.config.init, self.config.catalogs))
        road_friction = ChangeRoadFriction(OpenScenarioParser.get_friction_from_env_action(self.config.init, self.config.catalogs))
        env_behavior.add_child(oneshot_behavior(variable_name='InitialWeather', behaviour=weather_update))
        env_behavior.add_child(oneshot_behavior(variable_name='InitRoadFriction', behaviour=road_friction))
        return env_behavior

    def _create_init_behavior(self):
        init_behavior = py_trees.composites.Parallel(policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ALL, name='InitBehaviour')
        for actor in self.config.other_actors + self.config.ego_vehicles:
            for carla_actor in self.other_actors + self.ego_vehicles:
                if 'role_name' in carla_actor.attributes and carla_actor.attributes['role_name'] == actor.rolename:
                    actor_init_behavior = py_trees.composites.Sequence(name='InitActor{}'.format(actor.rolename))
                    controller_atomic = None
                    for private in self.config.init.iter('Private'):
                        if private.attrib.get('entityRef', None) == actor.rolename:
                            for private_action in private.iter('PrivateAction'):
                                for controller_action in private_action.iter('ControllerAction'):
                                    module, args = OpenScenarioParser.get_controller(controller_action, self.config.catalogs)
                                    controller_atomic = ChangeActorControl(carla_actor, control_py_module=module, args=args)
                    if controller_atomic is None:
                        controller_atomic = ChangeActorControl(carla_actor, control_py_module=None, args={})
                    actor_init_behavior.add_child(controller_atomic)
                    if actor.speed > 0:
                        actor_init_behavior.add_child(ChangeActorTargetSpeed(carla_actor, actor.speed, init_speed=True))
                    init_behavior.add_child(actor_init_behavior)
                    break
        return init_behavior

    def _create_behavior(self):
        """
        Basic behavior do nothing, i.e. Idle
        """
        story_behavior = py_trees.composites.Parallel(policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ALL, name='Story')
        joint_actor_list = self.other_actors + self.ego_vehicles + [None]
        for act in self.config.story.iter('Act'):
            act_sequence = py_trees.composites.Sequence(name='Act StartConditions and behaviours')
            start_conditions = py_trees.composites.Parallel(policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE, name='StartConditions Group')
            parallel_behavior = py_trees.composites.Parallel(policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE, name='Maneuver + EndConditions Group')
            parallel_sequences = py_trees.composites.Parallel(policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ALL, name='Maneuvers')
            for sequence in act.iter('ManeuverGroup'):
                sequence_behavior = py_trees.composites.Sequence(name=sequence.attrib.get('name'))
                repetitions = sequence.attrib.get('maximumExecutionCount', 1)
                for _ in range(int(repetitions)):
                    actor_ids = []
                    for actor in sequence.iter('Actors'):
                        for entity in actor.iter('EntityRef'):
                            entity_name = entity.attrib.get('entityRef', None)
                            for k, _ in enumerate(joint_actor_list):
                                if joint_actor_list[k] and entity_name == joint_actor_list[k].attributes['role_name']:
                                    actor_ids.append(k)
                                    break
                    if not actor_ids:
                        print('Warning: Maneuvergroup {} does not use reference actors!'.format(sequence.attrib.get('name')))
                        actor_ids.append(len(joint_actor_list) - 1)
                    catalog_maneuver_list = []
                    for catalog_reference in sequence.iter('CatalogReference'):
                        catalog_maneuver = OpenScenarioParser.get_catalog_entry(self.config.catalogs, catalog_reference)
                        catalog_maneuver_list.append(catalog_maneuver)
                    all_maneuvers = itertools.chain(iter(catalog_maneuver_list), sequence.iter('Maneuver'))
                    single_sequence_iteration = py_trees.composites.Parallel(policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ALL, name=sequence_behavior.name)
                    for maneuver in all_maneuvers:
                        maneuver_parallel = py_trees.composites.Parallel(policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ALL, name='Maneuver ' + maneuver.attrib.get('name'))
                        for event in maneuver.iter('Event'):
                            event_sequence = py_trees.composites.Sequence(name='Event ' + event.attrib.get('name'))
                            parallel_actions = py_trees.composites.Parallel(policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ALL, name='Actions')
                            for child in event.iter():
                                if child.tag == 'Action':
                                    for actor_id in actor_ids:
                                        maneuver_behavior = OpenScenarioParser.convert_maneuver_to_atomic(child, joint_actor_list[actor_id], self.config.catalogs)
                                        maneuver_behavior = StoryElementStatusToBlackboard(maneuver_behavior, 'ACTION', child.attrib.get('name'))
                                        parallel_actions.add_child(oneshot_behavior(variable_name=get_xml_path(self.config.story, sequence) + '>' + get_xml_path(maneuver, child), behaviour=maneuver_behavior))
                                if child.tag == 'StartTrigger':
                                    parallel_condition_groups = self._create_condition_container(child, 'Parallel Condition Groups', sequence, maneuver)
                                    event_sequence.add_child(parallel_condition_groups)
                            parallel_actions = StoryElementStatusToBlackboard(parallel_actions, 'EVENT', event.attrib.get('name'))
                            event_sequence.add_child(parallel_actions)
                            maneuver_parallel.add_child(oneshot_behavior(variable_name=get_xml_path(self.config.story, sequence) + '>' + get_xml_path(maneuver, event), behaviour=event_sequence))
                        maneuver_parallel = StoryElementStatusToBlackboard(maneuver_parallel, 'MANEUVER', maneuver.attrib.get('name'))
                        single_sequence_iteration.add_child(oneshot_behavior(variable_name=get_xml_path(self.config.story, sequence) + '>' + maneuver.attrib.get('name'), behaviour=maneuver_parallel))
                    single_sequence_iteration = StoryElementStatusToBlackboard(single_sequence_iteration, 'SCENE', sequence.attrib.get('name'))
                    single_sequence_iteration = repeatable_behavior(single_sequence_iteration, get_xml_path(self.config.story, sequence))
                    sequence_behavior.add_child(single_sequence_iteration)
                if sequence_behavior.children:
                    parallel_sequences.add_child(oneshot_behavior(variable_name=get_xml_path(self.config.story, sequence), behaviour=sequence_behavior))
            if parallel_sequences.children:
                parallel_sequences = StoryElementStatusToBlackboard(parallel_sequences, 'ACT', act.attrib.get('name'))
                parallel_behavior.add_child(parallel_sequences)
            start_triggers = act.find('StartTrigger')
            if list(start_triggers) is not None:
                for start_condition in start_triggers:
                    parallel_start_criteria = self._create_condition_container(start_condition, 'StartConditions')
                    if parallel_start_criteria.children:
                        start_conditions.add_child(parallel_start_criteria)
            end_triggers = act.find('StopTrigger')
            if end_triggers is not None and list(end_triggers) is not None:
                for end_condition in end_triggers:
                    parallel_end_criteria = self._create_condition_container(end_condition, 'EndConditions', success_on_all=False)
                    if parallel_end_criteria.children:
                        parallel_behavior.add_child(parallel_end_criteria)
            if start_conditions.children:
                act_sequence.add_child(start_conditions)
            if parallel_behavior.children:
                act_sequence.add_child(parallel_behavior)
            if act_sequence.children:
                story_behavior.add_child(act_sequence)
        behavior = py_trees.composites.Parallel(policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ALL, name='behavior')
        env_behavior = self._create_environment_behavior()
        if env_behavior is not None:
            behavior.add_child(oneshot_behavior(variable_name='InitialEnvironmentSettings', behaviour=env_behavior))
        init_behavior = self._create_init_behavior()
        if init_behavior is not None:
            behavior.add_child(oneshot_behavior(variable_name='InitialActorSettings', behaviour=init_behavior))
        behavior.add_child(story_behavior)
        return behavior

    def _create_condition_container(self, node, name='Conditions Group', sequence=None, maneuver=None, success_on_all=True):
        """
        This is a generic function to handle conditions utilising ConditionGroups
        Each ConditionGroup is represented as a Sequence of Conditions
        The ConditionGroups are grouped under a SUCCESS_ON_ONE Parallel
        """
        parallel_condition_groups = py_trees.composites.Parallel(name, policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)
        for condition_group in node.iter('ConditionGroup'):
            if success_on_all:
                condition_group_sequence = py_trees.composites.Parallel(name='Condition Group', policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ALL)
            else:
                condition_group_sequence = py_trees.composites.Parallel(name='Condition Group', policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)
            for condition in condition_group.iter('Condition'):
                criterion = OpenScenarioParser.convert_condition_to_atomic(condition, self.other_actors + self.ego_vehicles)
                if sequence is not None and maneuver is not None:
                    xml_path = get_xml_path(self.config.story, sequence) + '>' + get_xml_path(maneuver, condition)
                else:
                    xml_path = get_xml_path(self.config.story, condition)
                criterion = oneshot_behavior(variable_name=xml_path, behaviour=criterion)
                condition_group_sequence.add_child(criterion)
            if condition_group_sequence.children:
                parallel_condition_groups.add_child(condition_group_sequence)
        return parallel_condition_groups

    def _create_test_criteria(self):
        """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
        parallel_criteria = py_trees.composites.Parallel('EndConditions (Criteria Group)', policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)
        criteria = []
        for endcondition in self.config.storyboard.iter('StopTrigger'):
            for condition in endcondition.iter('Condition'):
                if condition.attrib.get('name').startswith('criteria_'):
                    condition.set('name', condition.attrib.get('name')[9:])
                    criteria.append(condition)
        for condition in criteria:
            criterion = OpenScenarioParser.convert_condition_to_atomic(condition, self.ego_vehicles)
            parallel_criteria.add_child(criterion)
        return parallel_criteria

    def __del__(self):
        """
        Remove all actors upon deletion
        """
        self.remove_all_actors()

def _create_environment_behavior(self):
    env_behavior = py_trees.composites.Parallel(policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ALL, name='EnvironmentBehavior')
    weather_update = ChangeWeather(OpenScenarioParser.get_weather_from_env_action(self.config.init, self.config.catalogs))
    road_friction = ChangeRoadFriction(OpenScenarioParser.get_friction_from_env_action(self.config.init, self.config.catalogs))
    env_behavior.add_child(oneshot_behavior(variable_name='InitialWeather', behaviour=weather_update))
    env_behavior.add_child(oneshot_behavior(variable_name='InitRoadFriction', behaviour=road_friction))
    return env_behavior

def _create_init_behavior(self):
    init_behavior = py_trees.composites.Parallel(policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ALL, name='InitBehaviour')
    for actor in self.config.other_actors + self.config.ego_vehicles:
        for carla_actor in self.other_actors + self.ego_vehicles:
            if 'role_name' in carla_actor.attributes and carla_actor.attributes['role_name'] == actor.rolename:
                actor_init_behavior = py_trees.composites.Sequence(name='InitActor{}'.format(actor.rolename))
                controller_atomic = None
                for private in self.config.init.iter('Private'):
                    if private.attrib.get('entityRef', None) == actor.rolename:
                        for private_action in private.iter('PrivateAction'):
                            for controller_action in private_action.iter('ControllerAction'):
                                module, args = OpenScenarioParser.get_controller(controller_action, self.config.catalogs)
                                controller_atomic = ChangeActorControl(carla_actor, control_py_module=module, args=args)
                if controller_atomic is None:
                    controller_atomic = ChangeActorControl(carla_actor, control_py_module=None, args={})
                actor_init_behavior.add_child(controller_atomic)
                if actor.speed > 0:
                    actor_init_behavior.add_child(ChangeActorTargetSpeed(carla_actor, actor.speed, init_speed=True))
                init_behavior.add_child(actor_init_behavior)
                break
    return init_behavior

def _create_behavior(self):
    """
        Basic behavior do nothing, i.e. Idle
        """
    story_behavior = py_trees.composites.Parallel(policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ALL, name='Story')
    joint_actor_list = self.other_actors + self.ego_vehicles + [None]
    for act in self.config.story.iter('Act'):
        act_sequence = py_trees.composites.Sequence(name='Act StartConditions and behaviours')
        start_conditions = py_trees.composites.Parallel(policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE, name='StartConditions Group')
        parallel_behavior = py_trees.composites.Parallel(policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE, name='Maneuver + EndConditions Group')
        parallel_sequences = py_trees.composites.Parallel(policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ALL, name='Maneuvers')
        for sequence in act.iter('ManeuverGroup'):
            sequence_behavior = py_trees.composites.Sequence(name=sequence.attrib.get('name'))
            repetitions = sequence.attrib.get('maximumExecutionCount', 1)
            for _ in range(int(repetitions)):
                actor_ids = []
                for actor in sequence.iter('Actors'):
                    for entity in actor.iter('EntityRef'):
                        entity_name = entity.attrib.get('entityRef', None)
                        for k, _ in enumerate(joint_actor_list):
                            if joint_actor_list[k] and entity_name == joint_actor_list[k].attributes['role_name']:
                                actor_ids.append(k)
                                break
                if not actor_ids:
                    print('Warning: Maneuvergroup {} does not use reference actors!'.format(sequence.attrib.get('name')))
                    actor_ids.append(len(joint_actor_list) - 1)
                catalog_maneuver_list = []
                for catalog_reference in sequence.iter('CatalogReference'):
                    catalog_maneuver = OpenScenarioParser.get_catalog_entry(self.config.catalogs, catalog_reference)
                    catalog_maneuver_list.append(catalog_maneuver)
                all_maneuvers = itertools.chain(iter(catalog_maneuver_list), sequence.iter('Maneuver'))
                single_sequence_iteration = py_trees.composites.Parallel(policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ALL, name=sequence_behavior.name)
                for maneuver in all_maneuvers:
                    maneuver_parallel = py_trees.composites.Parallel(policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ALL, name='Maneuver ' + maneuver.attrib.get('name'))
                    for event in maneuver.iter('Event'):
                        event_sequence = py_trees.composites.Sequence(name='Event ' + event.attrib.get('name'))
                        parallel_actions = py_trees.composites.Parallel(policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ALL, name='Actions')
                        for child in event.iter():
                            if child.tag == 'Action':
                                for actor_id in actor_ids:
                                    maneuver_behavior = OpenScenarioParser.convert_maneuver_to_atomic(child, joint_actor_list[actor_id], self.config.catalogs)
                                    maneuver_behavior = StoryElementStatusToBlackboard(maneuver_behavior, 'ACTION', child.attrib.get('name'))
                                    parallel_actions.add_child(oneshot_behavior(variable_name=get_xml_path(self.config.story, sequence) + '>' + get_xml_path(maneuver, child), behaviour=maneuver_behavior))
                            if child.tag == 'StartTrigger':
                                parallel_condition_groups = self._create_condition_container(child, 'Parallel Condition Groups', sequence, maneuver)
                                event_sequence.add_child(parallel_condition_groups)
                        parallel_actions = StoryElementStatusToBlackboard(parallel_actions, 'EVENT', event.attrib.get('name'))
                        event_sequence.add_child(parallel_actions)
                        maneuver_parallel.add_child(oneshot_behavior(variable_name=get_xml_path(self.config.story, sequence) + '>' + get_xml_path(maneuver, event), behaviour=event_sequence))
                    maneuver_parallel = StoryElementStatusToBlackboard(maneuver_parallel, 'MANEUVER', maneuver.attrib.get('name'))
                    single_sequence_iteration.add_child(oneshot_behavior(variable_name=get_xml_path(self.config.story, sequence) + '>' + maneuver.attrib.get('name'), behaviour=maneuver_parallel))
                single_sequence_iteration = StoryElementStatusToBlackboard(single_sequence_iteration, 'SCENE', sequence.attrib.get('name'))
                single_sequence_iteration = repeatable_behavior(single_sequence_iteration, get_xml_path(self.config.story, sequence))
                sequence_behavior.add_child(single_sequence_iteration)
            if sequence_behavior.children:
                parallel_sequences.add_child(oneshot_behavior(variable_name=get_xml_path(self.config.story, sequence), behaviour=sequence_behavior))
        if parallel_sequences.children:
            parallel_sequences = StoryElementStatusToBlackboard(parallel_sequences, 'ACT', act.attrib.get('name'))
            parallel_behavior.add_child(parallel_sequences)
        start_triggers = act.find('StartTrigger')
        if list(start_triggers) is not None:
            for start_condition in start_triggers:
                parallel_start_criteria = self._create_condition_container(start_condition, 'StartConditions')
                if parallel_start_criteria.children:
                    start_conditions.add_child(parallel_start_criteria)
        end_triggers = act.find('StopTrigger')
        if end_triggers is not None and list(end_triggers) is not None:
            for end_condition in end_triggers:
                parallel_end_criteria = self._create_condition_container(end_condition, 'EndConditions', success_on_all=False)
                if parallel_end_criteria.children:
                    parallel_behavior.add_child(parallel_end_criteria)
        if start_conditions.children:
            act_sequence.add_child(start_conditions)
        if parallel_behavior.children:
            act_sequence.add_child(parallel_behavior)
        if act_sequence.children:
            story_behavior.add_child(act_sequence)
    behavior = py_trees.composites.Parallel(policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ALL, name='behavior')
    env_behavior = self._create_environment_behavior()
    if env_behavior is not None:
        behavior.add_child(oneshot_behavior(variable_name='InitialEnvironmentSettings', behaviour=env_behavior))
    init_behavior = self._create_init_behavior()
    if init_behavior is not None:
        behavior.add_child(oneshot_behavior(variable_name='InitialActorSettings', behaviour=init_behavior))
    behavior.add_child(story_behavior)
    return behavior

def _create_condition_container(self, node, name='Conditions Group', sequence=None, maneuver=None, success_on_all=True):
    """
        This is a generic function to handle conditions utilising ConditionGroups
        Each ConditionGroup is represented as a Sequence of Conditions
        The ConditionGroups are grouped under a SUCCESS_ON_ONE Parallel
        """
    parallel_condition_groups = py_trees.composites.Parallel(name, policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)
    for condition_group in node.iter('ConditionGroup'):
        if success_on_all:
            condition_group_sequence = py_trees.composites.Parallel(name='Condition Group', policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ALL)
        else:
            condition_group_sequence = py_trees.composites.Parallel(name='Condition Group', policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)
        for condition in condition_group.iter('Condition'):
            criterion = OpenScenarioParser.convert_condition_to_atomic(condition, self.other_actors + self.ego_vehicles)
            if sequence is not None and maneuver is not None:
                xml_path = get_xml_path(self.config.story, sequence) + '>' + get_xml_path(maneuver, condition)
            else:
                xml_path = get_xml_path(self.config.story, condition)
            criterion = oneshot_behavior(variable_name=xml_path, behaviour=criterion)
            condition_group_sequence.add_child(criterion)
        if condition_group_sequence.children:
            parallel_condition_groups.add_child(condition_group_sequence)
    return parallel_condition_groups

def _create_test_criteria(self):
    """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
    parallel_criteria = py_trees.composites.Parallel('EndConditions (Criteria Group)', policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)
    criteria = []
    for endcondition in self.config.storyboard.iter('StopTrigger'):
        for condition in endcondition.iter('Condition'):
            if condition.attrib.get('name').startswith('criteria_'):
                condition.set('name', condition.attrib.get('name')[9:])
                criteria.append(condition)
    for condition in criteria:
        criterion = OpenScenarioParser.convert_condition_to_atomic(condition, self.ego_vehicles)
        parallel_criteria.add_child(criterion)
    return parallel_criteria

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

class MasterScenario(BasicScenario):
    """
    Implementation of a  Master scenario that controls the route.

    This is a single ego vehicle scenario
    """
    radius = 10.0

    def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, criteria_enable=True, timeout=300):
        """
        Setup all relevant parameters and create scenario
        """
        self.config = config
        self.route = None
        self.timeout = timeout
        if hasattr(self.config, 'route'):
            self.route = self.config.route
        else:
            raise ValueError('Master scenario must have a route')
        super(MasterScenario, self).__init__('MasterScenario', ego_vehicles=ego_vehicles, config=config, world=world, debug_mode=debug_mode, terminate_on_failure=True, criteria_enable=criteria_enable)

    def _create_behavior(self):
        """
        Basic behavior do nothing, i.e. Idle
        """
        sequence = py_trees.composites.Sequence('MasterScenario')
        idle_behavior = Idle()
        sequence.add_child(idle_behavior)
        return sequence

    def _create_test_criteria(self):
        """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
        if isinstance(self.route, RouteConfiguration):
            route = self.route.data
        else:
            route = self.route
        collision_criterion = CollisionTest(self.ego_vehicles[0], terminate_on_failure=False)
        route_criterion = InRouteTest(self.ego_vehicles[0], route=route, offroad_max=30, terminate_on_failure=True)
        completion_criterion = RouteCompletionTest(self.ego_vehicles[0], route=route)
        outsidelane_criterion = OutsideRouteLanesTest(self.ego_vehicles[0], route=route)
        red_light_criterion = RunningRedLightTest(self.ego_vehicles[0])
        stop_criterion = RunningStopTest(self.ego_vehicles[0])
        blocked_criterion = ActorSpeedAboveThresholdTest(self.ego_vehicles[0], speed_threshold=0.1, below_threshold_max_time=90.0, terminate_on_failure=True)
        parallel_criteria = py_trees.composites.Parallel('group_criteria', policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)
        parallel_criteria.add_child(completion_criterion)
        parallel_criteria.add_child(collision_criterion)
        parallel_criteria.add_child(route_criterion)
        parallel_criteria.add_child(outsidelane_criterion)
        parallel_criteria.add_child(red_light_criterion)
        parallel_criteria.add_child(stop_criterion)
        parallel_criteria.add_child(blocked_criterion)
        return parallel_criteria

    def __del__(self):
        """
        Remove all actors upon deletion
        """
        self.remove_all_actors()

def _create_behavior(self):
    """
        Basic behavior do nothing, i.e. Idle
        """
    sequence = py_trees.composites.Sequence('MasterScenario')
    idle_behavior = Idle()
    sequence.add_child(idle_behavior)
    return sequence

def _create_test_criteria(self):
    """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
    if isinstance(self.route, RouteConfiguration):
        route = self.route.data
    else:
        route = self.route
    collision_criterion = CollisionTest(self.ego_vehicles[0], terminate_on_failure=False)
    route_criterion = InRouteTest(self.ego_vehicles[0], route=route, offroad_max=30, terminate_on_failure=True)
    completion_criterion = RouteCompletionTest(self.ego_vehicles[0], route=route)
    outsidelane_criterion = OutsideRouteLanesTest(self.ego_vehicles[0], route=route)
    red_light_criterion = RunningRedLightTest(self.ego_vehicles[0])
    stop_criterion = RunningStopTest(self.ego_vehicles[0])
    blocked_criterion = ActorSpeedAboveThresholdTest(self.ego_vehicles[0], speed_threshold=0.1, below_threshold_max_time=90.0, terminate_on_failure=True)
    parallel_criteria = py_trees.composites.Parallel('group_criteria', policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)
    parallel_criteria.add_child(completion_criterion)
    parallel_criteria.add_child(collision_criterion)
    parallel_criteria.add_child(route_criterion)
    parallel_criteria.add_child(outsidelane_criterion)
    parallel_criteria.add_child(red_light_criterion)
    parallel_criteria.add_child(stop_criterion)
    parallel_criteria.add_child(blocked_criterion)
    return parallel_criteria

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

def _create_behavior(self):
    """
        """
    sequence = py_trees.composites.Sequence('Sequence Behavior')
    sequence.add_child(Idle())
    return sequence

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

class BasicControl(object):
    """
    This class is the base class for user-defined actor controllers
    All user-defined agents must be derived from this class.

    Args:
        actor (carla.Actor): Actor that should be controlled by the controller.

    Attributes:
        _actor (carla.Actor): Controlled actor.
            Defaults to None.
        _target_speed (float): Logitudinal target speed of the controller.
            Defaults to 0.
        _init_speed (float): Initial longitudinal speed of the controller.
            Defaults to 0.
        _waypoints (list of carla.Transform): List of target waypoints the actor
            should travel along. A waypoint here is of type carla.Transform!
            Defaults to [].
        _waypoints_updated (boolean):
            Defaults to False.
        _reached_goal (boolean):
            Defaults to False.
    """
    _actor = None
    _waypoints = []
    _waypoints_updated = False
    _target_speed = 0
    _reached_goal = False
    _init_speed = False

    def __init__(self, actor):
        """
        Initialize the actor
        """
        self._actor = actor

    def update_target_speed(self, speed):
        """
        Update the actor's target speed and set _init_speed to False.

        Args:
            speed (float): New target speed [m/s].
        """
        self._target_speed = speed
        self._init_speed = False

    def update_waypoints(self, waypoints, start_time=None):
        """
        Update the actor's waypoints

        Args:
            waypoints (List of carla.Transform): List of new waypoints.
        """
        self._waypoints = waypoints
        self._waypoints_updated = True

    def set_init_speed(self):
        """
        Set _init_speed to True
        """
        self._init_speed = True

    def check_reached_waypoint_goal(self):
        """
        Check if the actor reached the end of the waypoint list

        returns:
            True if the end was reached, False otherwise.
        """
        return self._reached_goal

    def reset(self):
        """
        Pure virtual function to reset the controller. This should be implemented
        in the user-defined agent implementation.
        """
        raise NotImplementedError('This function must be re-implemented by the user-defined actor control.If this error becomes visible the class hierarchy is somehow broken')

    def run_step(self):
        """
        Pure virtual function to run one step of the controllers's control loop.
        This should be implemented in the user-defined agent implementation.
        """
        raise NotImplementedError('This function must be re-implemented by the user-defined actor control.If this error becomes visible the class hierarchy is somehow broken')

def reset(self):
    """
        Pure virtual function to reset the controller. This should be implemented
        in the user-defined agent implementation.
        """
    raise NotImplementedError('This function must be re-implemented by the user-defined actor control.If this error becomes visible the class hierarchy is somehow broken')

def run_step(self):
    """
        Pure virtual function to run one step of the controllers's control loop.
        This should be implemented in the user-defined agent implementation.
        """
    raise NotImplementedError('This function must be re-implemented by the user-defined actor control.If this error becomes visible the class hierarchy is somehow broken')

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

def oneshot_behavior(variable_name, behaviour, name=None):
    """
    This is taken from py_trees.idiom.oneshot.
    """
    if not name:
        name = behaviour.name
    subtree_root = py_trees.composites.Selector(name=name)
    blackboard = py_trees.blackboard.Blackboard()
    _ = blackboard.set(variable_name, False)
    check_flag = py_trees.blackboard.CheckBlackboardVariable(name=variable_name + ' Done?', variable_name=variable_name, expected_value=True, clearing_policy=py_trees.common.ClearingPolicy.ON_INITIALISE)
    set_flag = py_trees.blackboard.SetBlackboardVariable(name='Mark Done', variable_name=variable_name, variable_value=True)
    if isinstance(behaviour, py_trees.composites.Sequence):
        behaviour.add_child(set_flag)
        sequence = behaviour
    else:
        sequence = py_trees.composites.Sequence(name='OneShot')
        sequence.add_children([behaviour, set_flag])
    subtree_root.add_children([check_flag, sequence])
    return subtree_root

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

def sensors(self):
    """
        Define the sensor suite required by the agent

        :return: a list containing the required sensors
        """
    raise NotImplementedError('This function has to be implemented by the derived classes')

class BasicMetric(object):
    """
    Base class of all the metrics.
    """

    def __init__(self, town_map, log, criteria=None):
        """
        Initialization of the metric class. This calls the metrics log and creates the metrics

        Args:
            town_map (carla.Map): Map of the simulation. Used to access the Waypoint API.
            log (srunner.metrics.tools.Metricslog): instance of a class used to access the recorder information
            criteria (dict): list of dictionaries with all the criteria information
        """
        self._create_metric(town_map, log, criteria)

    def _create_metric(self, town_map, log, criteria):
        """
        Pure virtual function to setup the metrics by the user.

        Args:
            town_map (carla.Map): Map of the simulation. Used to access the Waypoint API.
            log (srunner.metrics.tools.Metricslog): instance of a class used to access the recorder information
            criteria (dict): dictionaries with all the criteria information
        """
        raise NotImplementedError('This function should be re-implemented by all metricsIf this error becomes visible the class hierarchy is somehow broken')

def _create_metric(self, town_map, log, criteria):
    """
        Pure virtual function to setup the metrics by the user.

        Args:
            town_map (carla.Map): Map of the simulation. Used to access the Waypoint API.
            log (srunner.metrics.tools.Metricslog): instance of a class used to access the recorder information
            criteria (dict): dictionaries with all the criteria information
        """
    raise NotImplementedError('This function should be re-implemented by all metricsIf this error becomes visible the class hierarchy is somehow broken')

class GPT(nn.Module):
    """  the full GPT language model, with a context size of block_size """

    def __init__(self, n_embd, n_head, block_exp, n_layer, img_vert_anchors, img_horz_anchors, lidar_vert_anchors, lidar_horz_anchors, seq_len, embd_pdrop, attn_pdrop, resid_pdrop, config, use_velocity=True):
        super().__init__()
        self.n_embd = n_embd
        self.seq_len = 1
        self.img_vert_anchors = img_vert_anchors
        self.img_horz_anchors = img_horz_anchors
        self.lidar_vert_anchors = lidar_vert_anchors
        self.lidar_horz_anchors = lidar_horz_anchors
        self.config = config
        self.pos_emb = nn.Parameter(torch.zeros(1, self.seq_len * img_vert_anchors * img_horz_anchors + self.seq_len * lidar_vert_anchors * lidar_horz_anchors, n_embd))
        self.use_velocity = use_velocity
        if use_velocity == True:
            self.vel_emb = nn.Linear(self.seq_len, n_embd)
        self.drop = nn.Dropout(embd_pdrop)
        self.blocks = nn.Sequential(*[Block(n_embd, n_head, block_exp, attn_pdrop, resid_pdrop) for layer in range(n_layer)])
        self.ln_f = nn.LayerNorm(n_embd)
        self.block_size = self.seq_len
        self.apply(self._init_weights)

    def _init_weights(self, module):
        if isinstance(module, nn.Linear):
            module.weight.data.normal_(mean=self.config.gpt_linear_layer_init_mean, std=self.config.gpt_linear_layer_init_std)
            if module.bias is not None:
                module.bias.data.zero_()
        elif isinstance(module, nn.LayerNorm):
            module.bias.data.zero_()
            module.weight.data.fill_(self.config.gpt_layer_norm_init_weight)

    def forward(self, image_tensor, lidar_tensor, velocity):
        """
        Args:
            image_tensor (tensor): B*4*seq_len, C, H, W
            lidar_tensor (tensor): B*seq_len, C, H, W
            velocity (tensor): ego-velocity
        """
        bz = lidar_tensor.shape[0]
        lidar_h, lidar_w = lidar_tensor.shape[2:4]
        img_h, img_w = image_tensor.shape[2:4]
        assert self.seq_len == 1
        image_tensor = image_tensor.view(bz, self.seq_len, -1, img_h, img_w).permute(0, 1, 3, 4, 2).contiguous().view(bz, -1, self.n_embd)
        lidar_tensor = lidar_tensor.view(bz, self.seq_len, -1, lidar_h, lidar_w).permute(0, 1, 3, 4, 2).contiguous().view(bz, -1, self.n_embd)
        token_embeddings = torch.cat((image_tensor, lidar_tensor), dim=1)
        if self.use_velocity == True:
            velocity_embeddings = self.vel_emb(velocity)
            x = self.drop(self.pos_emb + token_embeddings + velocity_embeddings.unsqueeze(1))
        else:
            x = self.drop(self.pos_emb + token_embeddings)
        x = self.blocks(x)
        x = self.ln_f(x)
        x = x.view(bz, self.seq_len * self.img_vert_anchors * self.img_horz_anchors + self.seq_len * self.lidar_vert_anchors * self.lidar_horz_anchors, self.n_embd)
        image_tensor_out = x[:, :self.seq_len * self.img_vert_anchors * self.img_horz_anchors, :].contiguous().view(bz * self.seq_len, -1, img_h, img_w)
        lidar_tensor_out = x[:, self.seq_len * self.img_vert_anchors * self.img_horz_anchors:, :].contiguous().view(bz * self.seq_len, -1, lidar_h, lidar_w)
        return (image_tensor_out, lidar_tensor_out)

def _init_weights(self, module):
    if isinstance(module, nn.Linear):
        module.weight.data.normal_(mean=self.config.gpt_linear_layer_init_mean, std=self.config.gpt_linear_layer_init_std)
        if module.bias is not None:
            module.bias.data.zero_()
    elif isinstance(module, nn.LayerNorm):
        module.bias.data.zero_()
        module.weight.data.fill_(self.config.gpt_layer_norm_init_weight)

class GPT(nn.Module):
    """  the full GPT language model, with a context size of block_size """

    def __init__(self, n_embd, n_head, block_exp, n_layer, img_vert_anchors, img_horz_anchors, lidar_vert_anchors, lidar_horz_anchors, seq_len, embd_pdrop, attn_pdrop, resid_pdrop, config, use_velocity=True):
        super().__init__()
        self.n_embd = n_embd
        self.seq_len = 1
        self.img_vert_anchors = img_vert_anchors
        self.img_horz_anchors = img_horz_anchors
        self.lidar_vert_anchors = lidar_vert_anchors
        self.lidar_horz_anchors = lidar_horz_anchors
        self.config = config
        self.pos_emb = nn.Parameter(torch.zeros(1, self.seq_len * img_vert_anchors * img_horz_anchors + self.seq_len * lidar_vert_anchors * lidar_horz_anchors, n_embd))
        self.use_velocity = use_velocity
        if use_velocity == True:
            self.vel_emb = nn.Linear(self.seq_len, n_embd)
        self.drop = nn.Dropout(embd_pdrop)
        self.blocks = nn.Sequential(*[Block(n_embd, n_head, block_exp, attn_pdrop, resid_pdrop) for layer in range(n_layer)])
        self.ln_f = nn.LayerNorm(n_embd)
        self.block_size = self.seq_len
        self.apply(self._init_weights)

    def _init_weights(self, module):
        if isinstance(module, nn.Linear):
            module.weight.data.normal_(mean=self.config.gpt_linear_layer_init_mean, std=self.config.gpt_linear_layer_init_std)
            if module.bias is not None:
                module.bias.data.zero_()
        elif isinstance(module, nn.LayerNorm):
            module.bias.data.zero_()
            module.weight.data.fill_(self.config.gpt_layer_norm_init_weight)

    def forward(self, image_tensor, lidar_tensor, velocity):
        """
        Args:
            image_tensor (tensor): B*4*seq_len, C, H, W
            lidar_tensor (tensor): B*seq_len, C, H, W
            velocity (tensor): ego-velocity
        """
        bz = lidar_tensor.shape[0]
        lidar_h, lidar_w = lidar_tensor.shape[2:4]
        img_h, img_w = image_tensor.shape[2:4]
        assert self.seq_len == 1
        image_tensor = image_tensor.view(bz, self.seq_len, -1, img_h, img_w).permute(0, 1, 3, 4, 2).contiguous().view(bz, -1, self.n_embd)
        lidar_tensor = lidar_tensor.view(bz, self.seq_len, -1, lidar_h, lidar_w).permute(0, 1, 3, 4, 2).contiguous().view(bz, -1, self.n_embd)
        token_embeddings = torch.cat((image_tensor, lidar_tensor), dim=1)
        if self.use_velocity == True:
            velocity_embeddings = self.vel_emb(velocity)
            x = self.drop(self.pos_emb + token_embeddings + velocity_embeddings.unsqueeze(1))
        else:
            x = self.drop(self.pos_emb + token_embeddings)
        x = self.blocks(x)
        x = self.ln_f(x)
        x = x.view(bz, self.seq_len * self.img_vert_anchors * self.img_horz_anchors + self.seq_len * self.lidar_vert_anchors * self.lidar_horz_anchors, self.n_embd)
        image_tensor_out = x[:, :self.seq_len * self.img_vert_anchors * self.img_horz_anchors, :].contiguous().view(bz * self.seq_len, -1, img_h, img_w)
        lidar_tensor_out = x[:, self.seq_len * self.img_vert_anchors * self.img_horz_anchors:, :].contiguous().view(bz * self.seq_len, -1, lidar_h, lidar_w)
        return (image_tensor_out, lidar_tensor_out)

def _init_weights(self, module):
    if isinstance(module, nn.Linear):
        module.weight.data.normal_(mean=self.config.gpt_linear_layer_init_mean, std=self.config.gpt_linear_layer_init_std)
        if module.bias is not None:
            module.bias.data.zero_()
    elif isinstance(module, nn.LayerNorm):
        module.bias.data.zero_()
        module.weight.data.fill_(self.config.gpt_layer_norm_init_weight)

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

def init_weights(self):
    """Initialize weights of the head."""
    bias_init = bias_init_with_prob(self.train_cfg.center_net_bias_init_with_prob)
    self.heatmap_head[-1].bias.data.fill_(bias_init)
    for head in [self.wh_head, self.offset_head]:
        for m in head.modules():
            if isinstance(m, nn.Conv2d):
                normal_init(m, std=self.train_cfg.center_net_normal_init_std)

