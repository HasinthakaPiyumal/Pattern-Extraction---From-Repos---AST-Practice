# Cluster 10

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

def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, timeout=35 * 60):
    """
        Setup all relevant parameters and create scenario
        """
    self.config = config
    self.debug = debug_mode
    self.timeout = timeout
    super(BackgroundActivity, self).__init__('BackgroundActivity', ego_vehicles, config, world, debug_mode, terminate_on_failure=True, criteria_enable=True)

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

def interpolate_trajectory(world, waypoints_trajectory, hop_resolution=1.0):
    """
    Given some raw keypoints interpolate a full dense trajectory to be used by the user.
    returns the full interpolated route both in GPS coordinates and also in its original form.
    
    Args:
        - world: an reference to the CARLA world so we can use the planner
        - waypoints_trajectory: the current coarse trajectory
        - hop_resolution: is the resolution, how dense is the provided trajectory going to be made
    """
    dao = GlobalRoutePlannerDAO(world.get_map(), hop_resolution)
    grp = GlobalRoutePlanner(dao)
    grp.setup()
    route = []
    for i in range(len(waypoints_trajectory) - 1):
        waypoint = waypoints_trajectory[i]
        waypoint_next = waypoints_trajectory[i + 1]
        interpolated_trace = grp.trace_route(waypoint, waypoint_next)
        for wp_tuple in interpolated_trace:
            route.append((wp_tuple[0].transform, wp_tuple[1]))
    lat_ref, lon_ref = _get_latlon_ref(world)
    return (location_route_to_gps(route, lat_ref, lon_ref), route)

class SensorConfigurationInvalid(Exception):
    """
    Exceptions thrown when the sensors used by the agent are not allowed for that specific submissions
    """

    def __init__(self, message):
        super(SensorConfigurationInvalid, self).__init__(message)

def __init__(self, message):
    super(SensorConfigurationInvalid, self).__init__(message)

class SensorReceivedNoData(Exception):
    """
    Exceptions thrown when the sensors used by the agent take too long to receive data
    """

    def __init__(self, message):
        super(SensorReceivedNoData, self).__init__(message)

def __init__(self, message):
    super(SensorReceivedNoData, self).__init__(message)

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

def __init__(self):
    self._sensors_objects = {}
    self._data_buffers = {}
    self._new_data_buffers = Queue()
    self._queue_timeout = 10
    self._opendrive_tag = None

class NpcAgent(AutonomousAgent):
    """
    NPC autonomous agent to control the ego vehicle
    """
    _agent = None
    _route_assigned = False

    def setup(self, path_to_conf_file):
        """
        Setup the agent parameters
        """
        self.track = Track.SENSORS
        self._route_assigned = False
        self._agent = None

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
        sensors = [{'type': 'sensor.camera.rgb', 'x': 0.7, 'y': -0.4, 'z': 1.6, 'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0, 'width': 300, 'height': 200, 'fov': 100, 'id': 'Left'}]
        return sensors

    def run_step(self, input_data, timestamp):
        """
        Execute one step of navigation.
        """
        control = carla.VehicleControl()
        control.steer = 0.0
        control.throttle = 0.0
        control.brake = 0.0
        control.hand_brake = False
        if not self._agent:
            hero_actor = None
            for actor in CarlaDataProvider.get_world().get_actors():
                if 'role_name' in actor.attributes and actor.attributes['role_name'] == 'hero':
                    hero_actor = actor
                    break
            if hero_actor:
                self._agent = BasicAgent(hero_actor)
            return control
        if not self._route_assigned:
            if self._global_plan:
                plan = []
                prev = None
                for transform, _ in self._global_plan_world_coord:
                    wp = CarlaDataProvider.get_map().get_waypoint(transform.location)
                    if prev:
                        route_segment = self._agent._trace_route(prev, wp)
                        plan.extend(route_segment)
                    prev = wp
                self._agent._local_planner.set_global_plan(plan)
                self._route_assigned = True
        else:
            control = self._agent.run_step()
        return control

def run_step(self, input_data, timestamp):
    """
        Execute one step of navigation.
        """
    control = carla.VehicleControl()
    control.steer = 0.0
    control.throttle = 0.0
    control.brake = 0.0
    control.hand_brake = False
    if not self._agent:
        hero_actor = None
        for actor in CarlaDataProvider.get_world().get_actors():
            if 'role_name' in actor.attributes and actor.attributes['role_name'] == 'hero':
                hero_actor = actor
                break
        if hero_actor:
            self._agent = BasicAgent(hero_actor)
        return control
    if not self._route_assigned:
        if self._global_plan:
            plan = []
            prev = None
            for transform, _ in self._global_plan_world_coord:
                wp = CarlaDataProvider.get_map().get_waypoint(transform.location)
                if prev:
                    route_segment = self._agent._trace_route(prev, wp)
                    plan.extend(route_segment)
                prev = wp
            self._agent._local_planner.set_global_plan(plan)
            self._route_assigned = True
    else:
        control = self._agent.run_step()
    return control

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

def __init__(self, path_to_conf_file, route_index=None):
    self.track = Track.SENSORS
    self._global_plan = None
    self._global_plan_world_coord = None
    self.sensor_interface = SensorInterface()
    self.setup(path_to_conf_file, route_index)
    self.wallclock_t0 = None

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

def __init__(self, path_to_conf_file):
    self.track = Track.SENSORS
    self._global_plan = None
    self._global_plan_world_coord = None
    self.sensor_interface = SensorInterface()
    self.setup(path_to_conf_file)
    self.wallclock_t0 = None

class AgentError(Exception):
    """
    Exceptions thrown when the agent returns an error during the simulation
    """

    def __init__(self, message):
        super(AgentError, self).__init__(message)

def __init__(self, message):
    super(AgentError, self).__init__(message)

class AgentError(Exception):
    """
    Exceptions thrown when the agent returns an error during the simulation
    """

    def __init__(self, message):
        super(AgentError, self).__init__(message)

def __init__(self, message):
    super(AgentError, self).__init__(message)

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

def distance(v):
    return location.distance(v.get_location())

class ModuleInput(object):

    def __init__(self, name):
        self.name = name
        self.mouse_pos = (0, 0)
        self.mouse_offset = [0.0, 0.0]
        self.wheel_offset = 0.1
        self.wheel_amount = 0.025
        self._steer_cache = 0.0
        self.control = None
        self._autopilot_enabled = False

    def start(self):
        hud = module_manager.get_module(MODULE_HUD)
        hud.notification("Press 'H' or '?' for help.", seconds=4.0)

    def render(self, display):
        pass

    def tick(self, clock):
        self.parse_input(clock)

    def _parse_events(self):
        self.mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit_game()
            elif event.type == pygame.KEYUP:
                if self._is_quit_shortcut(event.key):
                    exit_game()
                elif event.key == K_h or (event.key == K_SLASH and pygame.key.get_mods() & KMOD_SHIFT):
                    module_hud = module_manager.get_module(MODULE_HUD)
                    module_hud.help.toggle()
                elif event.key == K_TAB:
                    module_world = module_manager.get_module(MODULE_WORLD)
                    module_hud = module_manager.get_module(MODULE_HUD)
                    if module_world.hero_actor is None:
                        module_world.select_hero_actor()
                        self.wheel_offset = HERO_DEFAULT_SCALE
                        self.control = carla.VehicleControl()
                        module_hud.notification('Hero Mode')
                    else:
                        self.wheel_offset = MAP_DEFAULT_SCALE
                        self.mouse_offset = [0, 0]
                        self.mouse_pos = [0, 0]
                        module_world.scale_offset = [0, 0]
                        module_world.hero_actor = None
                        module_hud.notification('Map Mode')
                elif event.key == K_F1:
                    module_hud = module_manager.get_module(MODULE_HUD)
                    module_hud.show_info = not module_hud.show_info
                elif event.key == K_i:
                    module_hud = module_manager.get_module(MODULE_HUD)
                    module_hud.show_actor_ids = not module_hud.show_actor_ids
                elif isinstance(self.control, carla.VehicleControl):
                    if event.key == K_q:
                        self.control.gear = 1 if self.control.reverse else -1
                    elif event.key == K_m:
                        self.control.manual_gear_shift = not self.control.manual_gear_shift
                        world = module_manager.get_module(MODULE_WORLD)
                        self.control.gear = world.hero_actor.get_control().gear
                        module_hud = module_manager.get_module(MODULE_HUD)
                        module_hud.notification('%s Transmission' % ('Manual' if self.control.manual_gear_shift else 'Automatic'))
                    elif self.control.manual_gear_shift and event.key == K_COMMA:
                        self.control.gear = max(-1, self.control.gear - 1)
                    elif self.control.manual_gear_shift and event.key == K_PERIOD:
                        self.control.gear = self.control.gear + 1
                    elif event.key == K_p:
                        world = module_manager.get_module(MODULE_WORLD)
                        if world.hero_actor is not None:
                            self._autopilot_enabled = not self._autopilot_enabled
                            world.hero_actor.set_autopilot(self._autopilot_enabled)
                            module_hud = module_manager.get_module(MODULE_HUD)
                            module_hud.notification('Autopilot %s' % ('On' if self._autopilot_enabled else 'Off'))
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    self.wheel_offset += self.wheel_amount
                    if self.wheel_offset >= 1.0:
                        self.wheel_offset = 1.0
                elif event.button == 5:
                    self.wheel_offset -= self.wheel_amount
                    if self.wheel_offset <= 0.1:
                        self.wheel_offset = 0.1

    def _parse_keys(self, milliseconds):
        keys = pygame.key.get_pressed()
        self.control.throttle = 1.0 if keys[K_UP] or keys[K_w] else 0.0
        steer_increment = 0.0005 * milliseconds
        if keys[K_LEFT] or keys[K_a]:
            self._steer_cache -= steer_increment
        elif keys[K_RIGHT] or keys[K_d]:
            self._steer_cache += steer_increment
        else:
            self._steer_cache = 0.0
        self._steer_cache = min(0.7, max(-0.7, self._steer_cache))
        self.control.steer = round(self._steer_cache, 1)
        self.control.brake = 1.0 if keys[K_DOWN] or keys[K_s] else 0.0
        self.control.hand_brake = keys[K_SPACE]

    def _parse_mouse(self):
        if pygame.mouse.get_pressed()[0]:
            x, y = pygame.mouse.get_pos()
            self.mouse_offset[0] += 1.0 / self.wheel_offset * (x - self.mouse_pos[0])
            self.mouse_offset[1] += 1.0 / self.wheel_offset * (y - self.mouse_pos[1])
            self.mouse_pos = (x, y)

    def parse_input(self, clock):
        self._parse_events()
        self._parse_mouse()
        if not self._autopilot_enabled:
            if isinstance(self.control, carla.VehicleControl):
                self._parse_keys(clock.get_time())
                self.control.reverse = self.control.gear < 0
            world = module_manager.get_module(MODULE_WORLD)
            if world.hero_actor is not None:
                world.hero_actor.apply_control(self.control)

    @staticmethod
    def _is_quit_shortcut(key):
        return key == K_ESCAPE or (key == K_q and pygame.key.get_mods() & KMOD_CTRL)

def parse_input(self, clock):
    self._parse_events()
    self._parse_mouse()
    if not self._autopilot_enabled:
        if isinstance(self.control, carla.VehicleControl):
            self._parse_keys(clock.get_time())
            self.control.reverse = self.control.gear < 0
        world = module_manager.get_module(MODULE_WORLD)
        if world.hero_actor is not None:
            world.hero_actor.apply_control(self.control)

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

class ClearBlackboardVariablesStartingWith(py_trees.behaviours.Success):
    """
    Clear the values starting with the specified string from the blackboard.

    Args:
        name (:obj:`str`): name of the behaviour
        variable_name_beginning (:obj:`str`): beginning of the names of variable to clear
    """

    def __init__(self, name='Clear Blackboard Variable Starting With', variable_name_beginning='dummy'):
        super(ClearBlackboardVariablesStartingWith, self).__init__(name)
        self.variable_name_beginning = variable_name_beginning

    def initialise(self):
        """
        Delete the variables from the blackboard.
        """
        blackboard_variables = [key for key, _ in py_trees.blackboard.Blackboard().__dict__.items() if key.startswith(self.variable_name_beginning)]
        for variable in blackboard_variables:
            delattr(py_trees.blackboard.Blackboard(), variable)

def __init__(self, name='Clear Blackboard Variable Starting With', variable_name_beginning='dummy'):
    super(ClearBlackboardVariablesStartingWith, self).__init__(name)
    self.variable_name_beginning = variable_name_beginning

def initialise(self):
    """
        Delete the variables from the blackboard.
        """
    blackboard_variables = [key for key, _ in py_trees.blackboard.Blackboard().__dict__.items() if key.startswith(self.variable_name_beginning)]
    for variable in blackboard_variables:
        delattr(py_trees.blackboard.Blackboard(), variable)

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

def __init__(self, child, story_element_type, element_name):
    super(StoryElementStatusToBlackboard, self).__init__(name=child.name, child=child)
    self.story_element_type = story_element_type
    self.element_name = element_name
    self.blackboard = py_trees.blackboard.Blackboard()

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

def __init__(self, world, ego_vehicles, config, config_file, debug_mode=False, criteria_enable=True, timeout=300):
    """
        Setup all relevant parameters and create scenario
        """
    self.config = config
    self.route = None
    self.config_file = config_file
    self.timeout = timeout
    super(OpenScenario, self).__init__('OpenScenario', ego_vehicles=ego_vehicles, config=config, world=world, debug_mode=debug_mode, terminate_on_failure=False, criteria_enable=criteria_enable)

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

def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, timeout=35 * 60):
    """
        Setup all relevant parameters and create scenario
        """
    self.config = config
    self.debug = debug_mode
    self.timeout = timeout
    super(BackgroundActivity, self).__init__('BackgroundActivity', ego_vehicles, config, world, debug_mode, terminate_on_failure=True, criteria_enable=True)

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

def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, criteria_enable=True, timeout=60):
    """
        Setup all relevant parameters and create scenario
        """
    self._other_actor_transform = None
    self.timeout = timeout
    super(NoSignalJunctionCrossing, self).__init__('NoSignalJunctionCrossing', ego_vehicles, config, world, debug_mode, criteria_enable=criteria_enable)

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

def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, criteria_enable=True, timeout=10000000):
    """
        Setup all relevant parameters and create scenario
        """
    self.timeout = timeout
    super(FreeRide, self).__init__('FreeRide', ego_vehicles, config, world, debug_mode, criteria_enable=criteria_enable)

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

def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, criteria_enable=True, timeout=180):
    """
        Setup all relevant parameters and create scenario
        and instantiate scenario manager
        """
    self.timeout = timeout
    self.subtype = config.subtype
    super(SignalJunctionCrossingRoute, self).__init__('SignalJunctionCrossingRoute', ego_vehicles, config, world, debug_mode, criteria_enable=criteria_enable)

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

def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, criteria_enable=True, timeout=180):
    """
        Setup all relevant parameters and create scenario
        and instantiate scenario manager
        """
    self.timeout = timeout
    super(NoSignalJunctionCrossingRoute, self).__init__('NoSignalJunctionCrossingRoute', ego_vehicles, config, world, debug_mode, criteria_enable=criteria_enable)

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

class SimulationTimeCondition(py_trees.behaviour.Behaviour):
    """
    This class contains an atomic simulation time condition behavior.
    It uses the CARLA game time, not the system time which is used by
    the py_trees timer.

    Returns, if the provided success_rule (greaterThan, lessThan, equalTo)
    was successfully evaluated
    """

    def __init__(self, timeout, success_rule='greaterThan', name='SimulationTimeCondition'):
        """
        Setup timeout
        """
        super(SimulationTimeCondition, self).__init__(name)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._timeout_value = timeout
        self._start_time = 0.0
        self._success_rule = success_rule
        self._ops = {'greaterThan': lambda x, y: x > y, 'equalTo': lambda x, y: x == y, 'lessThan': lambda x, y: x < y}

    def initialise(self):
        """
        Set start_time to current GameTime
        """
        self._start_time = GameTime.get_time()
        self.logger.debug('%s.initialise()' % self.__class__.__name__)

    def update(self):
        """
        Get current game time, and compare it to the timeout value
        Upon successfully comparison using the provided success_rule operator,
        the status changes to SUCCESS
        """
        elapsed_time = GameTime.get_time() - self._start_time
        if not self._ops[self._success_rule](elapsed_time, self._timeout_value):
            new_status = py_trees.common.Status.RUNNING
        else:
            new_status = py_trees.common.Status.SUCCESS
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

def __init__(self, timeout, success_rule='greaterThan', name='SimulationTimeCondition'):
    """
        Setup timeout
        """
    super(SimulationTimeCondition, self).__init__(name)
    self.logger.debug('%s.__init__()' % self.__class__.__name__)
    self._timeout_value = timeout
    self._start_time = 0.0
    self._success_rule = success_rule
    self._ops = {'greaterThan': lambda x, y: x > y, 'equalTo': lambda x, y: x == y, 'lessThan': lambda x, y: x < y}

def initialise(self):
    """
        Set start_time to current GameTime
        """
    self._start_time = GameTime.get_time()
    self.logger.debug('%s.initialise()' % self.__class__.__name__)

def update(self):
    """
        Get current game time, and compare it to the timeout value
        Upon successfully comparison using the provided success_rule operator,
        the status changes to SUCCESS
        """
    elapsed_time = GameTime.get_time() - self._start_time
    if not self._ops[self._success_rule](elapsed_time, self._timeout_value):
        new_status = py_trees.common.Status.RUNNING
    else:
        new_status = py_trees.common.Status.SUCCESS
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    return new_status

class TimeOut(SimulationTimeCondition):
    """
    This class contains an atomic timeout behavior.
    It uses the CARLA game time, not the system time which is used by
    the py_trees timer.
    """

    def __init__(self, timeout, name='TimeOut'):
        """
        Setup timeout
        """
        super(TimeOut, self).__init__(timeout, name=name)
        self.timeout = False

    def update(self):
        """
        Upon reaching the timeout value the status changes to SUCCESS
        """
        new_status = super(TimeOut, self).update()
        if new_status == py_trees.common.Status.SUCCESS:
            self.timeout = True
        return new_status

def __init__(self, timeout, name='TimeOut'):
    """
        Setup timeout
        """
    super(TimeOut, self).__init__(timeout, name=name)
    self.timeout = False

class WeatherBehavior(py_trees.behaviour.Behaviour):
    """
    Atomic to read weather settings from the blackboard and apply these in CARLA.
    Used in combination with UpdateWeather() to have a continuous weather simulation.

    This behavior is always in a running state and must never terminate.
    The user must not add this behavior. It is automatically added by the ScenarioManager.

    This atomic also sets the datetime to blackboard variable, used by TimeOfDayComparison atomic

    Args:
        name (string): Name of the behavior.
            Defaults to 'WeatherBehavior'.

    Attributes:
        _weather (srunner.scenariomanager.weather_sim.Weather): Weather settings.
        _current_time (float): Current CARLA time [seconds].
    """

    def __init__(self, name='WeatherBehavior'):
        """
        Setup parameters
        """
        super(WeatherBehavior, self).__init__(name)
        self._weather = None
        self._current_time = None

    def initialise(self):
        """
        Set current time to current CARLA time
        """
        self._current_time = GameTime.get_time()

    def update(self):
        """
        Check if new weather settings are available on the blackboard, and if yes fetch these
        into the _weather attribute.

        Apply the weather settings from _weather to CARLA.

        Note:
            To minimize CARLA server interactions, the weather is only updated, when the blackboard
            is updated, or if the weather animation flag is true. In the latter case, the update
            frequency is 1 Hz.

        returns:
            py_trees.common.Status.RUNNING
        """
        weather = None
        try:
            check_weather = operator.attrgetter('CarlaWeather')
            weather = check_weather(py_trees.blackboard.Blackboard())
        except AttributeError:
            pass
        if weather:
            self._weather = weather
            delattr(py_trees.blackboard.Blackboard(), 'CarlaWeather')
            CarlaDataProvider.get_world().set_weather(self._weather.carla_weather)
            py_trees.blackboard.Blackboard().set('Datetime', self._weather.datetime, overwrite=True)
        if self._weather and self._weather.animation:
            new_time = GameTime.get_time()
            delta_time = new_time - self._current_time
            if delta_time > 1:
                self._weather.update(delta_time)
                self._current_time = new_time
                CarlaDataProvider.get_world().set_weather(self._weather.carla_weather)
                py_trees.blackboard.Blackboard().set('Datetime', self._weather.datetime, overwrite=True)
        return py_trees.common.Status.RUNNING

def __init__(self, name='WeatherBehavior'):
    """
        Setup parameters
        """
    super(WeatherBehavior, self).__init__(name)
    self._weather = None
    self._current_time = None

def initialise(self):
    """
        Set current time to current CARLA time
        """
    self._current_time = GameTime.get_time()

def update(self):
    """
        Check if new weather settings are available on the blackboard, and if yes fetch these
        into the _weather attribute.

        Apply the weather settings from _weather to CARLA.

        Note:
            To minimize CARLA server interactions, the weather is only updated, when the blackboard
            is updated, or if the weather animation flag is true. In the latter case, the update
            frequency is 1 Hz.

        returns:
            py_trees.common.Status.RUNNING
        """
    weather = None
    try:
        check_weather = operator.attrgetter('CarlaWeather')
        weather = check_weather(py_trees.blackboard.Blackboard())
    except AttributeError:
        pass
    if weather:
        self._weather = weather
        delattr(py_trees.blackboard.Blackboard(), 'CarlaWeather')
        CarlaDataProvider.get_world().set_weather(self._weather.carla_weather)
        py_trees.blackboard.Blackboard().set('Datetime', self._weather.datetime, overwrite=True)
    if self._weather and self._weather.animation:
        new_time = GameTime.get_time()
        delta_time = new_time - self._current_time
        if delta_time > 1:
            self._weather.update(delta_time)
            self._current_time = new_time
            CarlaDataProvider.get_world().set_weather(self._weather.carla_weather)
            py_trees.blackboard.Blackboard().set('Datetime', self._weather.datetime, overwrite=True)
    return py_trees.common.Status.RUNNING

class AtomicCondition(py_trees.behaviour.Behaviour):
    """
    Base class for all atomic conditions used to setup a scenario

    *All behaviors should use this class as parent*

    Important parameters:
    - name: Name of the atomic condition
    """

    def __init__(self, name):
        """
        Default init. Has to be called via super from derived class
        """
        super(AtomicCondition, self).__init__(name)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self.name = name

    def setup(self, unused_timeout=15):
        """
        Default setup
        """
        self.logger.debug('%s.setup()' % self.__class__.__name__)
        return True

    def initialise(self):
        """
        Initialise setup
        """
        self.logger.debug('%s.initialise()' % self.__class__.__name__)

    def terminate(self, new_status):
        """
        Default terminate. Can be extended in derived class
        """
        self.logger.debug('%s.terminate()[%s->%s]' % (self.__class__.__name__, self.status, new_status))

def __init__(self, name):
    """
        Default init. Has to be called via super from derived class
        """
    super(AtomicCondition, self).__init__(name)
    self.logger.debug('%s.__init__()' % self.__class__.__name__)
    self.name = name

def setup(self, unused_timeout=15):
    """
        Default setup
        """
    self.logger.debug('%s.setup()' % self.__class__.__name__)
    return True

def initialise(self):
    """
        Initialise setup
        """
    self.logger.debug('%s.initialise()' % self.__class__.__name__)

def terminate(self, new_status):
    """
        Default terminate. Can be extended in derived class
        """
    self.logger.debug('%s.terminate()[%s->%s]' % (self.__class__.__name__, self.status, new_status))

class InTriggerDistanceToOSCPosition(AtomicCondition):
    """
    OpenSCENARIO atomic
    This class contains the trigger condition for a distance to an OpenSCENARIO position

    Args:
        actor (carla.Actor): CARLA actor to execute the behavior
        osc_position (str): OpenSCENARIO position
        distance (float): Trigger distance between the actor and the target location in meters
        name (str): Name of the condition

    The condition terminates with SUCCESS, when the actor reached the target distance to the openSCENARIO position
    """

    def __init__(self, actor, osc_position, distance, along_route=False, comparison_operator=operator.lt, name='InTriggerDistanceToOSCPosition'):
        """
        Setup parameters
        """
        super(InTriggerDistanceToOSCPosition, self).__init__(name)
        self._actor = actor
        self._osc_position = osc_position
        self._distance = distance
        self._along_route = along_route
        self._comparison_operator = comparison_operator
        self._map = CarlaDataProvider.get_map()
        if self._along_route:
            dao = GlobalRoutePlannerDAO(self._map, 0.5)
            grp = GlobalRoutePlanner(dao)
            grp.setup()
            self._grp = grp
        else:
            self._grp = None

    def initialise(self):
        if self._distance < 0:
            raise ValueError('distance value must be positive')

    def update(self):
        """
        Check if actor is in trigger distance
        """
        new_status = py_trees.common.Status.RUNNING
        osc_transform = srunner.tools.openscenario_parser.OpenScenarioParser.convert_position_to_transform(self._osc_position)
        if osc_transform is not None:
            osc_location = osc_transform.location
            actor_location = CarlaDataProvider.get_location(self._actor)
            if self._along_route:
                actor_location = self._map.get_waypoint(actor_location).transform.location
                osc_location = self._map.get_waypoint(osc_location).transform.location
            distance = calculate_distance(actor_location, osc_location, self._grp)
            if self._comparison_operator(distance, self._distance):
                new_status = py_trees.common.Status.SUCCESS
        return new_status

def __init__(self, actor, osc_position, distance, along_route=False, comparison_operator=operator.lt, name='InTriggerDistanceToOSCPosition'):
    """
        Setup parameters
        """
    super(InTriggerDistanceToOSCPosition, self).__init__(name)
    self._actor = actor
    self._osc_position = osc_position
    self._distance = distance
    self._along_route = along_route
    self._comparison_operator = comparison_operator
    self._map = CarlaDataProvider.get_map()
    if self._along_route:
        dao = GlobalRoutePlannerDAO(self._map, 0.5)
        grp = GlobalRoutePlanner(dao)
        grp.setup()
        self._grp = grp
    else:
        self._grp = None

def initialise(self):
    if self._distance < 0:
        raise ValueError('distance value must be positive')

def update(self):
    """
        Check if actor is in trigger distance
        """
    new_status = py_trees.common.Status.RUNNING
    osc_transform = srunner.tools.openscenario_parser.OpenScenarioParser.convert_position_to_transform(self._osc_position)
    if osc_transform is not None:
        osc_location = osc_transform.location
        actor_location = CarlaDataProvider.get_location(self._actor)
        if self._along_route:
            actor_location = self._map.get_waypoint(actor_location).transform.location
            osc_location = self._map.get_waypoint(osc_location).transform.location
        distance = calculate_distance(actor_location, osc_location, self._grp)
        if self._comparison_operator(distance, self._distance):
            new_status = py_trees.common.Status.SUCCESS
    return new_status

class InTimeToArrivalToOSCPosition(AtomicCondition):
    """
    OpenSCENARIO atomic
    This class contains a trigger if an actor arrives within a given time to an OpenSCENARIO position

    Important parameters:
    - actor: CARLA actor to execute the behavior
    - osc_position: OpenSCENARIO position
    - time: The behavior is successful, if TTA is less than _time_ in seconds
    - name: Name of the condition

    The condition terminates with SUCCESS, when the actor can reach the position within the given time
    """

    def __init__(self, actor, osc_position, time, along_route=False, comparison_operator=operator.lt, name='InTimeToArrivalToOSCPosition'):
        """
        Setup parameters
        """
        super(InTimeToArrivalToOSCPosition, self).__init__(name)
        self._map = CarlaDataProvider.get_map()
        self._actor = actor
        self._osc_position = osc_position
        self._time = float(time)
        self._along_route = along_route
        self._comparison_operator = comparison_operator
        if self._along_route:
            dao = GlobalRoutePlannerDAO(self._map, 0.5)
            grp = GlobalRoutePlanner(dao)
            grp.setup()
            self._grp = grp
        else:
            self._grp = None

    def initialise(self):
        if self._time < 0:
            raise ValueError('time value must be positive')

    def update(self):
        """
        Check if actor can arrive within trigger time
        """
        new_status = py_trees.common.Status.RUNNING
        try:
            osc_transform = srunner.tools.openscenario_parser.OpenScenarioParser.convert_position_to_transform(self._osc_position)
        except AttributeError:
            return py_trees.common.Status.FAILURE
        target_location = osc_transform.location
        actor_location = CarlaDataProvider.get_location(self._actor)
        if target_location is None or actor_location is None:
            return new_status
        if self._along_route:
            actor_location = self._map.get_waypoint(actor_location).transform.location
            target_location = self._map.get_waypoint(target_location).transform.location
        distance = calculate_distance(actor_location, target_location, self._grp)
        actor_velocity = CarlaDataProvider.get_velocity(self._actor)
        if actor_velocity > 0:
            time_to_arrival = distance / actor_velocity
        elif distance == 0:
            time_to_arrival = 0
        else:
            time_to_arrival = float('inf')
        if self._comparison_operator(time_to_arrival, self._time):
            new_status = py_trees.common.Status.SUCCESS
        return new_status

def __init__(self, actor, osc_position, time, along_route=False, comparison_operator=operator.lt, name='InTimeToArrivalToOSCPosition'):
    """
        Setup parameters
        """
    super(InTimeToArrivalToOSCPosition, self).__init__(name)
    self._map = CarlaDataProvider.get_map()
    self._actor = actor
    self._osc_position = osc_position
    self._time = float(time)
    self._along_route = along_route
    self._comparison_operator = comparison_operator
    if self._along_route:
        dao = GlobalRoutePlannerDAO(self._map, 0.5)
        grp = GlobalRoutePlanner(dao)
        grp.setup()
        self._grp = grp
    else:
        self._grp = None

def initialise(self):
    if self._time < 0:
        raise ValueError('time value must be positive')

def update(self):
    """
        Check if actor can arrive within trigger time
        """
    new_status = py_trees.common.Status.RUNNING
    try:
        osc_transform = srunner.tools.openscenario_parser.OpenScenarioParser.convert_position_to_transform(self._osc_position)
    except AttributeError:
        return py_trees.common.Status.FAILURE
    target_location = osc_transform.location
    actor_location = CarlaDataProvider.get_location(self._actor)
    if target_location is None or actor_location is None:
        return new_status
    if self._along_route:
        actor_location = self._map.get_waypoint(actor_location).transform.location
        target_location = self._map.get_waypoint(target_location).transform.location
    distance = calculate_distance(actor_location, target_location, self._grp)
    actor_velocity = CarlaDataProvider.get_velocity(self._actor)
    if actor_velocity > 0:
        time_to_arrival = distance / actor_velocity
    elif distance == 0:
        time_to_arrival = 0
    else:
        time_to_arrival = float('inf')
    if self._comparison_operator(time_to_arrival, self._time):
        new_status = py_trees.common.Status.SUCCESS
    return new_status

class StandStill(AtomicCondition):
    """
    This class contains a standstill behavior of a scenario

    Important parameters:
    - actor: CARLA actor to execute the behavior
    - name: Name of the condition
    - duration: Duration of the behavior in seconds

    The condition terminates with SUCCESS, when the actor does not move
    """

    def __init__(self, actor, name, duration=float('inf')):
        """
        Setup actor
        """
        super(StandStill, self).__init__(name)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._actor = actor
        self._duration = duration
        self._start_time = 0

    def initialise(self):
        """
        Initialize the start time of this condition
        """
        self._start_time = GameTime.get_time()
        super(StandStill, self).initialise()

    def update(self):
        """
        Check if the _actor stands still (v=0)
        """
        new_status = py_trees.common.Status.RUNNING
        velocity = CarlaDataProvider.get_velocity(self._actor)
        if velocity > EPSILON:
            self._start_time = GameTime.get_time()
        if GameTime.get_time() - self._start_time > self._duration:
            new_status = py_trees.common.Status.SUCCESS
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

def __init__(self, actor, name, duration=float('inf')):
    """
        Setup actor
        """
    super(StandStill, self).__init__(name)
    self.logger.debug('%s.__init__()' % self.__class__.__name__)
    self._actor = actor
    self._duration = duration
    self._start_time = 0

def initialise(self):
    """
        Initialize the start time of this condition
        """
    self._start_time = GameTime.get_time()
    super(StandStill, self).initialise()

def update(self):
    """
        Check if the _actor stands still (v=0)
        """
    new_status = py_trees.common.Status.RUNNING
    velocity = CarlaDataProvider.get_velocity(self._actor)
    if velocity > EPSILON:
        self._start_time = GameTime.get_time()
    if GameTime.get_time() - self._start_time > self._duration:
        new_status = py_trees.common.Status.SUCCESS
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    return new_status

class RelativeVelocityToOtherActor(AtomicCondition):
    """
    Atomic containing a comparison between an actor's velocity
    and another actor's one. The behavior returns SUCCESS when the
    expected comparison (greater than / less than / equal to) is achieved

    Args:
        actor (carla.Actor): actor from which the velocity is taken
        other_actor (carla.Actor): The actor with the reference velocity
        speed (float): Difference of speed between the actors
        name (string): Name of the condition
        comparison_operator: Type "operator", used to compare the two velocities
    """

    def __init__(self, actor, other_actor, speed, comparison_operator=operator.gt, name='RelativeVelocityToOtherActor'):
        """
        Setup the parameters
        """
        super(RelativeVelocityToOtherActor, self).__init__(name)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._actor = actor
        self._other_actor = other_actor
        self._relative_speed = speed
        self._comparison_operator = comparison_operator

    def update(self):
        """
        Gets the speed of the two actors and compares them according to the comparison operator

        returns:
            py_trees.common.Status.RUNNING when the comparison fails and
            py_trees.common.Status.SUCCESS when it succeeds
        """
        new_status = py_trees.common.Status.RUNNING
        curr_speed = CarlaDataProvider.get_velocity(self._actor)
        other_speed = CarlaDataProvider.get_velocity(self._other_actor)
        relative_speed = curr_speed - other_speed
        if self._comparison_operator(relative_speed, self._relative_speed):
            new_status = py_trees.common.Status.SUCCESS
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

def __init__(self, actor, other_actor, speed, comparison_operator=operator.gt, name='RelativeVelocityToOtherActor'):
    """
        Setup the parameters
        """
    super(RelativeVelocityToOtherActor, self).__init__(name)
    self.logger.debug('%s.__init__()' % self.__class__.__name__)
    self._actor = actor
    self._other_actor = other_actor
    self._relative_speed = speed
    self._comparison_operator = comparison_operator

def update(self):
    """
        Gets the speed of the two actors and compares them according to the comparison operator

        returns:
            py_trees.common.Status.RUNNING when the comparison fails and
            py_trees.common.Status.SUCCESS when it succeeds
        """
    new_status = py_trees.common.Status.RUNNING
    curr_speed = CarlaDataProvider.get_velocity(self._actor)
    other_speed = CarlaDataProvider.get_velocity(self._other_actor)
    relative_speed = curr_speed - other_speed
    if self._comparison_operator(relative_speed, self._relative_speed):
        new_status = py_trees.common.Status.SUCCESS
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    return new_status

class TriggerVelocity(AtomicCondition):
    """
    Atomic containing a comparison between an actor's speed and a reference one.
    The behavior returns SUCCESS when the expected comparison (greater than /
    less than / equal to) is achieved.

    Args:
        actor (carla.Actor): CARLA actor from which the speed will be taken.
        name (string): Name of the atomic
        target_velocity (float): velcoity to be compared with the actor's one
        comparison_operator: Type "operator", used to compare the two velocities
    """

    def __init__(self, actor, target_velocity, comparison_operator=operator.gt, name='TriggerVelocity'):
        """
        Setup the atomic parameters
        """
        super(TriggerVelocity, self).__init__(name)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._actor = actor
        self._target_velocity = target_velocity
        self._comparison_operator = comparison_operator

    def update(self):
        """
        Gets the speed of the actor and compares it with the reference one

        returns:
            py_trees.common.Status.RUNNING when the comparison fails and
            py_trees.common.Status.SUCCESS when it succeeds
        """
        new_status = py_trees.common.Status.RUNNING
        actor_speed = CarlaDataProvider.get_velocity(self._actor)
        if self._comparison_operator(actor_speed, self._target_velocity):
            new_status = py_trees.common.Status.SUCCESS
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

def __init__(self, actor, target_velocity, comparison_operator=operator.gt, name='TriggerVelocity'):
    """
        Setup the atomic parameters
        """
    super(TriggerVelocity, self).__init__(name)
    self.logger.debug('%s.__init__()' % self.__class__.__name__)
    self._actor = actor
    self._target_velocity = target_velocity
    self._comparison_operator = comparison_operator

def update(self):
    """
        Gets the speed of the actor and compares it with the reference one

        returns:
            py_trees.common.Status.RUNNING when the comparison fails and
            py_trees.common.Status.SUCCESS when it succeeds
        """
    new_status = py_trees.common.Status.RUNNING
    actor_speed = CarlaDataProvider.get_velocity(self._actor)
    if self._comparison_operator(actor_speed, self._target_velocity):
        new_status = py_trees.common.Status.SUCCESS
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    return new_status

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

def __init__(self, actor, target_acceleration, comparison_operator=operator.gt, name='TriggerAcceleration'):
    """
        Setup trigger acceleration
        """
    super(TriggerAcceleration, self).__init__(name)
    self.logger.debug('%s.__init__()' % self.__class__.__name__)
    self._actor = actor
    self._target_acceleration = target_acceleration
    self._comparison_operator = comparison_operator

class TimeOfDayComparison(AtomicCondition):
    """
    Atomic containing a comparison between the current time of day of the simulation
    and a given one. The behavior returns SUCCESS when the
    expected comparison (greater than / less than / equal to) is achieved

    Args:
        datetime (datetime): CARLA actor to execute the behavior
        name (str): Name of the condition
        target_acceleration (float): Acceleration reference (in m/s^2) on which the success is dependent
        comparison_operator (operator): Type "operator", used to compare the two acceleration
    """

    def __init__(self, dattime, comparison_operator=operator.gt, name='TimeOfDayComparison'):
        """
        """
        super(TimeOfDayComparison, self).__init__(name)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._datetime = datetime.datetime.strptime(dattime, '%Y-%m-%dT%H:%M:%S')
        self._comparison_operator = comparison_operator

    def update(self):
        """
        Gets the time of day of the simulation and compares it with the reference one

        returns:
            py_trees.common.Status.RUNNING when the comparison fails and
            py_trees.common.Status.SUCCESS when it succeeds
        """
        new_status = py_trees.common.Status.RUNNING
        try:
            check_dtime = operator.attrgetter('Datetime')
            dtime = check_dtime(py_trees.blackboard.Blackboard())
        except AttributeError:
            pass
        if self._comparison_operator(dtime, self._datetime):
            new_status = py_trees.common.Status.SUCCESS
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

def __init__(self, dattime, comparison_operator=operator.gt, name='TimeOfDayComparison'):
    """
        """
    super(TimeOfDayComparison, self).__init__(name)
    self.logger.debug('%s.__init__()' % self.__class__.__name__)
    self._datetime = datetime.datetime.strptime(dattime, '%Y-%m-%dT%H:%M:%S')
    self._comparison_operator = comparison_operator

def update(self):
    """
        Gets the time of day of the simulation and compares it with the reference one

        returns:
            py_trees.common.Status.RUNNING when the comparison fails and
            py_trees.common.Status.SUCCESS when it succeeds
        """
    new_status = py_trees.common.Status.RUNNING
    try:
        check_dtime = operator.attrgetter('Datetime')
        dtime = check_dtime(py_trees.blackboard.Blackboard())
    except AttributeError:
        pass
    if self._comparison_operator(dtime, self._datetime):
        new_status = py_trees.common.Status.SUCCESS
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    return new_status

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

class InTriggerRegion(AtomicCondition):
    """
    This class contains the trigger region (condition) of a scenario

    Important parameters:
    - actor: CARLA actor to execute the behavior
    - name: Name of the condition
    - min_x, max_x, min_y, max_y: bounding box of the trigger region

    The condition terminates with SUCCESS, when the actor reached the target region
    """

    def __init__(self, actor, min_x, max_x, min_y, max_y, name='TriggerRegion'):
        """
        Setup trigger region (rectangle provided by
        [min_x,min_y] and [max_x,max_y]
        """
        super(InTriggerRegion, self).__init__(name)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._actor = actor
        self._min_x = min_x
        self._max_x = max_x
        self._min_y = min_y
        self._max_y = max_y

    def update(self):
        """
        Check if the _actor location is within trigger region
        """
        new_status = py_trees.common.Status.RUNNING
        location = CarlaDataProvider.get_location(self._actor)
        if location is None:
            return new_status
        not_in_region = (location.x < self._min_x or location.x > self._max_x) or (location.y < self._min_y or location.y > self._max_y)
        if not not_in_region:
            new_status = py_trees.common.Status.SUCCESS
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

def __init__(self, actor, min_x, max_x, min_y, max_y, name='TriggerRegion'):
    """
        Setup trigger region (rectangle provided by
        [min_x,min_y] and [max_x,max_y]
        """
    super(InTriggerRegion, self).__init__(name)
    self.logger.debug('%s.__init__()' % self.__class__.__name__)
    self._actor = actor
    self._min_x = min_x
    self._max_x = max_x
    self._min_y = min_y
    self._max_y = max_y

def update(self):
    """
        Check if the _actor location is within trigger region
        """
    new_status = py_trees.common.Status.RUNNING
    location = CarlaDataProvider.get_location(self._actor)
    if location is None:
        return new_status
    not_in_region = (location.x < self._min_x or location.x > self._max_x) or (location.y < self._min_y or location.y > self._max_y)
    if not not_in_region:
        new_status = py_trees.common.Status.SUCCESS
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    return new_status

class InTriggerDistanceToVehicle(AtomicCondition):
    """
    This class contains the trigger distance (condition) between to actors
    of a scenario

    Important parameters:
    - actor: CARLA actor to execute the behavior
    - reference_actor: Reference CARLA actor
    - name: Name of the condition
    - distance: Trigger distance between the two actors in meters
    - dx, dy, dz: distance to reference_location (location of reference_actor)

    The condition terminates with SUCCESS, when the actor reached the target distance to the other actor
    """

    def __init__(self, reference_actor, actor, distance, comparison_operator=operator.lt, name='TriggerDistanceToVehicle'):
        """
        Setup trigger distance
        """
        super(InTriggerDistanceToVehicle, self).__init__(name)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._reference_actor = reference_actor
        self._actor = actor
        self._distance = distance
        self._comparison_operator = comparison_operator

    def update(self):
        """
        Check if the ego vehicle is within trigger distance to other actor
        """
        new_status = py_trees.common.Status.RUNNING
        location = CarlaDataProvider.get_location(self._actor)
        reference_location = CarlaDataProvider.get_location(self._reference_actor)
        if location is None or reference_location is None:
            return new_status
        if self._comparison_operator(calculate_distance(location, reference_location), self._distance):
            new_status = py_trees.common.Status.SUCCESS
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

def __init__(self, reference_actor, actor, distance, comparison_operator=operator.lt, name='TriggerDistanceToVehicle'):
    """
        Setup trigger distance
        """
    super(InTriggerDistanceToVehicle, self).__init__(name)
    self.logger.debug('%s.__init__()' % self.__class__.__name__)
    self._reference_actor = reference_actor
    self._actor = actor
    self._distance = distance
    self._comparison_operator = comparison_operator

def update(self):
    """
        Check if the ego vehicle is within trigger distance to other actor
        """
    new_status = py_trees.common.Status.RUNNING
    location = CarlaDataProvider.get_location(self._actor)
    reference_location = CarlaDataProvider.get_location(self._reference_actor)
    if location is None or reference_location is None:
        return new_status
    if self._comparison_operator(calculate_distance(location, reference_location), self._distance):
        new_status = py_trees.common.Status.SUCCESS
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    return new_status

class InTriggerDistanceToLocation(AtomicCondition):
    """
    This class contains the trigger (condition) for a distance to a fixed
    location of a scenario

    Important parameters:
    - actor: CARLA actor to execute the behavior
    - target_location: Reference location (carla.location)
    - name: Name of the condition
    - distance: Trigger distance between the actor and the target location in meters

    The condition terminates with SUCCESS, when the actor reached the target distance to the given location
    """

    def __init__(self, actor, target_location, distance, comparison_operator=operator.lt, name='InTriggerDistanceToLocation'):
        """
        Setup trigger distance
        """
        super(InTriggerDistanceToLocation, self).__init__(name)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._target_location = target_location
        self._actor = actor
        self._distance = distance
        self._comparison_operator = comparison_operator

    def update(self):
        """
        Check if the actor is within trigger distance to the target location
        """
        new_status = py_trees.common.Status.RUNNING
        location = CarlaDataProvider.get_location(self._actor)
        if location is None:
            return new_status
        if self._comparison_operator(calculate_distance(location, self._target_location), self._distance):
            new_status = py_trees.common.Status.SUCCESS
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

def __init__(self, actor, target_location, distance, comparison_operator=operator.lt, name='InTriggerDistanceToLocation'):
    """
        Setup trigger distance
        """
    super(InTriggerDistanceToLocation, self).__init__(name)
    self.logger.debug('%s.__init__()' % self.__class__.__name__)
    self._target_location = target_location
    self._actor = actor
    self._distance = distance
    self._comparison_operator = comparison_operator

def update(self):
    """
        Check if the actor is within trigger distance to the target location
        """
    new_status = py_trees.common.Status.RUNNING
    location = CarlaDataProvider.get_location(self._actor)
    if location is None:
        return new_status
    if self._comparison_operator(calculate_distance(location, self._target_location), self._distance):
        new_status = py_trees.common.Status.SUCCESS
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    return new_status

class InTriggerDistanceToNextIntersection(AtomicCondition):
    """
    This class contains the trigger (condition) for a distance to the
    next intersection of a scenario

    Important parameters:
    - actor: CARLA actor to execute the behavior
    - name: Name of the condition
    - distance: Trigger distance between the actor and the next intersection in meters

    The condition terminates with SUCCESS, when the actor reached the target distance to the next intersection
    """

    def __init__(self, actor, distance, name='InTriggerDistanceToNextIntersection'):
        """
        Setup trigger distance
        """
        super(InTriggerDistanceToNextIntersection, self).__init__(name)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._actor = actor
        self._distance = distance
        self._map = CarlaDataProvider.get_map()
        waypoint = self._map.get_waypoint(self._actor.get_location())
        while waypoint and (not waypoint.is_intersection):
            waypoint = waypoint.next(1)[-1]
        self._final_location = waypoint.transform.location

    def update(self):
        """
        Check if the actor is within trigger distance to the intersection
        """
        new_status = py_trees.common.Status.RUNNING
        current_waypoint = self._map.get_waypoint(CarlaDataProvider.get_location(self._actor))
        distance = calculate_distance(current_waypoint.transform.location, self._final_location)
        if distance < self._distance:
            new_status = py_trees.common.Status.SUCCESS
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

def __init__(self, actor, distance, name='InTriggerDistanceToNextIntersection'):
    """
        Setup trigger distance
        """
    super(InTriggerDistanceToNextIntersection, self).__init__(name)
    self.logger.debug('%s.__init__()' % self.__class__.__name__)
    self._actor = actor
    self._distance = distance
    self._map = CarlaDataProvider.get_map()
    waypoint = self._map.get_waypoint(self._actor.get_location())
    while waypoint and (not waypoint.is_intersection):
        waypoint = waypoint.next(1)[-1]
    self._final_location = waypoint.transform.location

def update(self):
    """
        Check if the actor is within trigger distance to the intersection
        """
    new_status = py_trees.common.Status.RUNNING
    current_waypoint = self._map.get_waypoint(CarlaDataProvider.get_location(self._actor))
    distance = calculate_distance(current_waypoint.transform.location, self._final_location)
    if distance < self._distance:
        new_status = py_trees.common.Status.SUCCESS
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    return new_status

class InTriggerDistanceToLocationAlongRoute(AtomicCondition):
    """
    Implementation for a behavior that will check if a given actor
    is within a given distance to a given location considering a given route

    Important parameters:
    - actor: CARLA actor to execute the behavior
    - name: Name of the condition
    - distance: Trigger distance between the actor and the next intersection in meters
    - route: Route to be checked
    - location: Location on the route to be checked

    The condition terminates with SUCCESS, when the actor reached the target distance
    along its route to the given location
    """

    def __init__(self, actor, route, location, distance, name='InTriggerDistanceToLocationAlongRoute'):
        """
        Setup class members
        """
        super(InTriggerDistanceToLocationAlongRoute, self).__init__(name)
        self._map = CarlaDataProvider.get_map()
        self._actor = actor
        self._location = location
        self._route = route
        self._distance = distance
        self._location_distance, _ = get_distance_along_route(self._route, self._location)

    def update(self):
        new_status = py_trees.common.Status.RUNNING
        current_location = CarlaDataProvider.get_location(self._actor)
        if current_location is None:
            return new_status
        if current_location.distance(self._location) < self._distance + 20:
            actor_distance, _ = get_distance_along_route(self._route, current_location)
            if self._location_distance < actor_distance + self._distance and actor_distance < self._location_distance or self._location_distance < 1.0:
                new_status = py_trees.common.Status.SUCCESS
        return new_status

def __init__(self, actor, route, location, distance, name='InTriggerDistanceToLocationAlongRoute'):
    """
        Setup class members
        """
    super(InTriggerDistanceToLocationAlongRoute, self).__init__(name)
    self._map = CarlaDataProvider.get_map()
    self._actor = actor
    self._location = location
    self._route = route
    self._distance = distance
    self._location_distance, _ = get_distance_along_route(self._route, self._location)

def update(self):
    new_status = py_trees.common.Status.RUNNING
    current_location = CarlaDataProvider.get_location(self._actor)
    if current_location is None:
        return new_status
    if current_location.distance(self._location) < self._distance + 20:
        actor_distance, _ = get_distance_along_route(self._route, current_location)
        if self._location_distance < actor_distance + self._distance and actor_distance < self._location_distance or self._location_distance < 1.0:
            new_status = py_trees.common.Status.SUCCESS
    return new_status

class InTimeToArrivalToLocation(AtomicCondition):
    """
    This class contains a check if a actor arrives within a given time
    at a given location.

    Important parameters:
    - actor: CARLA actor to execute the behavior
    - name: Name of the condition
    - time: The behavior is successful, if TTA is less than _time_ in seconds
    - location: Location to be checked in this behavior

    The condition terminates with SUCCESS, when the actor can reach the target location within the given time
    """
    _max_time_to_arrival = float('inf')

    def __init__(self, actor, time, location, comparison_operator=operator.lt, name='TimeToArrival'):
        """
        Setup parameters
        """
        super(InTimeToArrivalToLocation, self).__init__(name)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._actor = actor
        self._time = time
        self._target_location = location
        self._comparison_operator = comparison_operator

    def update(self):
        """
        Check if the actor can arrive at target_location within time
        """
        new_status = py_trees.common.Status.RUNNING
        current_location = CarlaDataProvider.get_location(self._actor)
        if current_location is None:
            return new_status
        distance = calculate_distance(current_location, self._target_location)
        velocity = CarlaDataProvider.get_velocity(self._actor)
        time_to_arrival = self._max_time_to_arrival
        if velocity > EPSILON:
            time_to_arrival = distance / velocity
        if self._comparison_operator(time_to_arrival, self._time):
            new_status = py_trees.common.Status.SUCCESS
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

def __init__(self, actor, time, location, comparison_operator=operator.lt, name='TimeToArrival'):
    """
        Setup parameters
        """
    super(InTimeToArrivalToLocation, self).__init__(name)
    self.logger.debug('%s.__init__()' % self.__class__.__name__)
    self._actor = actor
    self._time = time
    self._target_location = location
    self._comparison_operator = comparison_operator

def update(self):
    """
        Check if the actor can arrive at target_location within time
        """
    new_status = py_trees.common.Status.RUNNING
    current_location = CarlaDataProvider.get_location(self._actor)
    if current_location is None:
        return new_status
    distance = calculate_distance(current_location, self._target_location)
    velocity = CarlaDataProvider.get_velocity(self._actor)
    time_to_arrival = self._max_time_to_arrival
    if velocity > EPSILON:
        time_to_arrival = distance / velocity
    if self._comparison_operator(time_to_arrival, self._time):
        new_status = py_trees.common.Status.SUCCESS
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    return new_status

class InTimeToArrivalToVehicle(AtomicCondition):
    """
    This class contains a check if a actor arrives within a given time
    at another actor.

    Important parameters:
    - actor: CARLA actor to execute the behavior
    - name: Name of the condition
    - time: The behavior is successful, if TTA is less than _time_ in seconds
    - other_actor: Reference actor used in this behavior

    The condition terminates with SUCCESS, when the actor can reach the other vehicle within the given time
    """
    _max_time_to_arrival = float('inf')

    def __init__(self, actor, other_actor, time, along_route=False, comparison_operator=operator.lt, name='TimeToArrival'):
        """
        Setup parameters
        """
        super(InTimeToArrivalToVehicle, self).__init__(name)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._map = CarlaDataProvider.get_map()
        self._actor = actor
        self._other_actor = other_actor
        self._time = time
        self._along_route = along_route
        self._comparison_operator = comparison_operator
        if self._along_route:
            dao = GlobalRoutePlannerDAO(self._map, 0.5)
            grp = GlobalRoutePlanner(dao)
            grp.setup()
            self._grp = grp
        else:
            self._grp = None

    def update(self):
        """
        Check if the ego vehicle can arrive at other actor within time
        """
        new_status = py_trees.common.Status.RUNNING
        current_location = CarlaDataProvider.get_location(self._actor)
        other_location = CarlaDataProvider.get_location(self._other_actor)
        if current_location is None or other_location is None:
            return new_status
        current_velocity = CarlaDataProvider.get_velocity(self._actor)
        other_velocity = CarlaDataProvider.get_velocity(self._other_actor)
        if self._along_route:
            current_location = self._map.get_waypoint(current_location).transform.location
            other_location = self._map.get_waypoint(other_location).transform.location
        distance = calculate_distance(current_location, other_location, self._grp)
        time_to_arrival = self._max_time_to_arrival
        if current_velocity > other_velocity:
            time_to_arrival = 2 * distance / (current_velocity - other_velocity)
        if self._comparison_operator(time_to_arrival, self._time):
            new_status = py_trees.common.Status.SUCCESS
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

def __init__(self, actor, other_actor, time, along_route=False, comparison_operator=operator.lt, name='TimeToArrival'):
    """
        Setup parameters
        """
    super(InTimeToArrivalToVehicle, self).__init__(name)
    self.logger.debug('%s.__init__()' % self.__class__.__name__)
    self._map = CarlaDataProvider.get_map()
    self._actor = actor
    self._other_actor = other_actor
    self._time = time
    self._along_route = along_route
    self._comparison_operator = comparison_operator
    if self._along_route:
        dao = GlobalRoutePlannerDAO(self._map, 0.5)
        grp = GlobalRoutePlanner(dao)
        grp.setup()
        self._grp = grp
    else:
        self._grp = None

def update(self):
    """
        Check if the ego vehicle can arrive at other actor within time
        """
    new_status = py_trees.common.Status.RUNNING
    current_location = CarlaDataProvider.get_location(self._actor)
    other_location = CarlaDataProvider.get_location(self._other_actor)
    if current_location is None or other_location is None:
        return new_status
    current_velocity = CarlaDataProvider.get_velocity(self._actor)
    other_velocity = CarlaDataProvider.get_velocity(self._other_actor)
    if self._along_route:
        current_location = self._map.get_waypoint(current_location).transform.location
        other_location = self._map.get_waypoint(other_location).transform.location
    distance = calculate_distance(current_location, other_location, self._grp)
    time_to_arrival = self._max_time_to_arrival
    if current_velocity > other_velocity:
        time_to_arrival = 2 * distance / (current_velocity - other_velocity)
    if self._comparison_operator(time_to_arrival, self._time):
        new_status = py_trees.common.Status.SUCCESS
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    return new_status

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

class DriveDistance(AtomicCondition):
    """
    This class contains an atomic behavior to drive a certain distance.

    Important parameters:
    - actor: CARLA actor to execute the condition
    - distance: Distance for this condition in meters

    The condition terminates with SUCCESS, when the actor drove at least the given distance
    """

    def __init__(self, actor, distance, name='DriveDistance'):
        """
        Setup parameters
        """
        super(DriveDistance, self).__init__(name)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._target_distance = distance
        self._distance = 0
        self._location = None
        self._actor = actor

    def initialise(self):
        self._location = CarlaDataProvider.get_location(self._actor)
        super(DriveDistance, self).initialise()

    def update(self):
        """
        Check driven distance
        """
        new_status = py_trees.common.Status.RUNNING
        new_location = CarlaDataProvider.get_location(self._actor)
        self._distance += calculate_distance(self._location, new_location)
        self._location = new_location
        if self._distance > self._target_distance:
            new_status = py_trees.common.Status.SUCCESS
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

def __init__(self, actor, distance, name='DriveDistance'):
    """
        Setup parameters
        """
    super(DriveDistance, self).__init__(name)
    self.logger.debug('%s.__init__()' % self.__class__.__name__)
    self._target_distance = distance
    self._distance = 0
    self._location = None
    self._actor = actor

def initialise(self):
    self._location = CarlaDataProvider.get_location(self._actor)
    super(DriveDistance, self).initialise()

def update(self):
    """
        Check driven distance
        """
    new_status = py_trees.common.Status.RUNNING
    new_location = CarlaDataProvider.get_location(self._actor)
    self._distance += calculate_distance(self._location, new_location)
    self._location = new_location
    if self._distance > self._target_distance:
        new_status = py_trees.common.Status.SUCCESS
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    return new_status

class AtRightmostLane(AtomicCondition):
    """
    This class contains an atomic behavior to check if the actor is at the rightest driving lane.

    Important parameters:
    - actor: CARLA actor to execute the condition

    The condition terminates with SUCCESS, when the actor enters the rightest lane
    """

    def __init__(self, actor, name='AtRightmostLane'):
        """
        Setup parameters
        """
        super(AtRightmostLane, self).__init__(name)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._actor = actor
        self._map = CarlaDataProvider.get_map()

    def update(self):
        """
        Check actor waypoints
        """
        new_status = py_trees.common.Status.RUNNING
        location = CarlaDataProvider.get_location(self._actor)
        waypoint = self._map.get_waypoint(location)
        if waypoint is None:
            return new_status
        right_waypoint = waypoint.get_right_lane()
        if right_waypoint is None:
            return new_status
        lane_type = right_waypoint.lane_type
        if lane_type != carla.LaneType.Driving:
            new_status = py_trees.common.Status.SUCCESS
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

def __init__(self, actor, name='AtRightmostLane'):
    """
        Setup parameters
        """
    super(AtRightmostLane, self).__init__(name)
    self.logger.debug('%s.__init__()' % self.__class__.__name__)
    self._actor = actor
    self._map = CarlaDataProvider.get_map()

def update(self):
    """
        Check actor waypoints
        """
    new_status = py_trees.common.Status.RUNNING
    location = CarlaDataProvider.get_location(self._actor)
    waypoint = self._map.get_waypoint(location)
    if waypoint is None:
        return new_status
    right_waypoint = waypoint.get_right_lane()
    if right_waypoint is None:
        return new_status
    lane_type = right_waypoint.lane_type
    if lane_type != carla.LaneType.Driving:
        new_status = py_trees.common.Status.SUCCESS
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    return new_status

class WaitForTrafficLightState(AtomicCondition):
    """
    This class contains an atomic behavior to wait for a given traffic light
    to have the desired state.

    Args:
        actor (carla.TrafficLight): CARLA traffic light to execute the condition
        state (carla.TrafficLightState): State to be checked in this condition

    The condition terminates with SUCCESS, when the traffic light switches to the desired state
    """

    def __init__(self, actor, state, name='WaitForTrafficLightState'):
        """
        Setup traffic_light
        """
        super(WaitForTrafficLightState, self).__init__(name)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._actor = actor if 'traffic_light' in actor.type_id else None
        self._state = state

    def update(self):
        """
        Set status to SUCCESS, when traffic light state matches the expected one
        """
        if self._actor is None:
            return py_trees.common.Status.FAILURE
        new_status = py_trees.common.Status.RUNNING
        if self._actor.state == self._state:
            new_status = py_trees.common.Status.SUCCESS
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

def __init__(self, actor, state, name='WaitForTrafficLightState'):
    """
        Setup traffic_light
        """
    super(WaitForTrafficLightState, self).__init__(name)
    self.logger.debug('%s.__init__()' % self.__class__.__name__)
    self._actor = actor if 'traffic_light' in actor.type_id else None
    self._state = state

def update(self):
    """
        Set status to SUCCESS, when traffic light state matches the expected one
        """
    if self._actor is None:
        return py_trees.common.Status.FAILURE
    new_status = py_trees.common.Status.RUNNING
    if self._actor.state == self._state:
        new_status = py_trees.common.Status.SUCCESS
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    return new_status

class WaitEndIntersection(AtomicCondition):
    """
    Atomic behavior that waits until the vehicles has gone outside the junction.
    If currently inside no intersection, it will wait until one is found
    """

    def __init__(self, actor, debug=False, name='WaitEndIntersection'):
        super(WaitEndIntersection, self).__init__(name)
        self.actor = actor
        self.debug = debug
        self.inside_junction = False
        self.logger.debug('%s.__init__()' % self.__class__.__name__)

    def update(self):
        new_status = py_trees.common.Status.RUNNING
        location = CarlaDataProvider.get_location(self.actor)
        waypoint = CarlaDataProvider.get_map().get_waypoint(location)
        if not self.inside_junction and waypoint.is_junction:
            self.inside_junction = True
        if self.inside_junction and (not waypoint.is_junction):
            if self.debug:
                print('--- Leaving the junction')
            new_status = py_trees.common.Status.SUCCESS
        return new_status

def __init__(self, actor, debug=False, name='WaitEndIntersection'):
    super(WaitEndIntersection, self).__init__(name)
    self.actor = actor
    self.debug = debug
    self.inside_junction = False
    self.logger.debug('%s.__init__()' % self.__class__.__name__)

def update(self):
    new_status = py_trees.common.Status.RUNNING
    location = CarlaDataProvider.get_location(self.actor)
    waypoint = CarlaDataProvider.get_map().get_waypoint(location)
    if not self.inside_junction and waypoint.is_junction:
        self.inside_junction = True
    if self.inside_junction and (not waypoint.is_junction):
        if self.debug:
            print('--- Leaving the junction')
        new_status = py_trees.common.Status.SUCCESS
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

def __init__(self, variable_name, variable_value, var_init_value=None, debug=False, name='WaitForBlackboardVariable'):
    super(WaitForBlackboardVariable, self).__init__(name)
    self._debug = debug
    self._variable_name = variable_name
    self._variable_value = variable_value
    self.logger.debug('%s.__init__()' % self.__class__.__name__)
    if var_init_value is not None:
        blackboard = py_trees.blackboard.Blackboard()
        _ = blackboard.set(variable_name, var_init_value)

class Criterion(py_trees.behaviour.Behaviour):
    """
    Base class for all criteria used to evaluate a scenario for success/failure

    Important parameters (PUBLIC):
    - name: Name of the criterion
    - expected_value_success:    Result in case of success
                                 (e.g. max_speed, zero collisions, ...)
    - expected_value_acceptable: Result that does not mean a failure,
                                 but is not good enough for a success
    - actual_value: Actual result after running the scenario
    - test_status: Used to access the result of the criterion
    - optional: Indicates if a criterion is optional (not used for overall analysis)
    """

    def __init__(self, name, actor, expected_value_success, expected_value_acceptable=None, optional=False, terminate_on_failure=False):
        super(Criterion, self).__init__(name)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._terminate_on_failure = terminate_on_failure
        self.name = name
        self.actor = actor
        self.test_status = 'INIT'
        self.expected_value_success = expected_value_success
        self.expected_value_acceptable = expected_value_acceptable
        self.actual_value = 0
        self.optional = optional
        self.list_traffic_events = []

    def initialise(self):
        """
        Initialise the criterion. Can be extended by the user-derived class
        """
        self.logger.debug('%s.initialise()' % self.__class__.__name__)

    def terminate(self, new_status):
        """
        Terminate the criterion. Can be extended by the user-derived class
        """
        if self.test_status == 'RUNNING' or self.test_status == 'INIT':
            self.test_status = 'SUCCESS'
        self.logger.debug('%s.terminate()[%s->%s]' % (self.__class__.__name__, self.status, new_status))

def __init__(self, name, actor, expected_value_success, expected_value_acceptable=None, optional=False, terminate_on_failure=False):
    super(Criterion, self).__init__(name)
    self.logger.debug('%s.__init__()' % self.__class__.__name__)
    self._terminate_on_failure = terminate_on_failure
    self.name = name
    self.actor = actor
    self.test_status = 'INIT'
    self.expected_value_success = expected_value_success
    self.expected_value_acceptable = expected_value_acceptable
    self.actual_value = 0
    self.optional = optional
    self.list_traffic_events = []

def initialise(self):
    """
        Initialise the criterion. Can be extended by the user-derived class
        """
    self.logger.debug('%s.initialise()' % self.__class__.__name__)

def terminate(self, new_status):
    """
        Terminate the criterion. Can be extended by the user-derived class
        """
    if self.test_status == 'RUNNING' or self.test_status == 'INIT':
        self.test_status = 'SUCCESS'
    self.logger.debug('%s.terminate()[%s->%s]' % (self.__class__.__name__, self.status, new_status))

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

def __init__(self, actor, max_velocity_allowed, optional=False, name='CheckMaximumVelocity'):
    """
        Setup actor and maximum allowed velovity
        """
    super(MaxVelocityTest, self).__init__(name, actor, max_velocity_allowed, None, optional)

class DrivenDistanceTest(Criterion):
    """
    This class contains an atomic test to check the driven distance

    Important parameters:
    - actor: CARLA actor to be used for this test
    - distance_success: If the actor's driven distance is more than this value (in meters),
                        the test result is SUCCESS
    - distance_acceptable: If the actor's driven distance is more than this value (in meters),
                           the test result is ACCEPTABLE
    - optional [optional]: If True, the result is not considered for an overall pass/fail result
    """

    def __init__(self, actor, distance_success, distance_acceptable=None, optional=False, name='CheckDrivenDistance'):
        """
        Setup actor
        """
        super(DrivenDistanceTest, self).__init__(name, actor, distance_success, distance_acceptable, optional)
        self._last_location = None

    def initialise(self):
        self._last_location = CarlaDataProvider.get_location(self.actor)
        super(DrivenDistanceTest, self).initialise()

    def update(self):
        """
        Check distance
        """
        new_status = py_trees.common.Status.RUNNING
        if self.actor is None:
            return new_status
        location = CarlaDataProvider.get_location(self.actor)
        if location is None:
            return new_status
        if self._last_location is None:
            self._last_location = location
            return new_status
        self.actual_value += location.distance(self._last_location)
        self._last_location = location
        if self.actual_value > self.expected_value_success:
            self.test_status = 'SUCCESS'
        elif self.expected_value_acceptable is not None and self.actual_value > self.expected_value_acceptable:
            self.test_status = 'ACCEPTABLE'
        else:
            self.test_status = 'RUNNING'
        if self._terminate_on_failure and self.test_status == 'FAILURE':
            new_status = py_trees.common.Status.FAILURE
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

    def terminate(self, new_status):
        """
        Set final status
        """
        if self.test_status != 'SUCCESS':
            self.test_status = 'FAILURE'
        self.actual_value = round(self.actual_value, 2)
        super(DrivenDistanceTest, self).terminate(new_status)

def __init__(self, actor, distance_success, distance_acceptable=None, optional=False, name='CheckDrivenDistance'):
    """
        Setup actor
        """
    super(DrivenDistanceTest, self).__init__(name, actor, distance_success, distance_acceptable, optional)
    self._last_location = None

def initialise(self):
    self._last_location = CarlaDataProvider.get_location(self.actor)
    super(DrivenDistanceTest, self).initialise()

def update(self):
    """
        Check distance
        """
    new_status = py_trees.common.Status.RUNNING
    if self.actor is None:
        return new_status
    location = CarlaDataProvider.get_location(self.actor)
    if location is None:
        return new_status
    if self._last_location is None:
        self._last_location = location
        return new_status
    self.actual_value += location.distance(self._last_location)
    self._last_location = location
    if self.actual_value > self.expected_value_success:
        self.test_status = 'SUCCESS'
    elif self.expected_value_acceptable is not None and self.actual_value > self.expected_value_acceptable:
        self.test_status = 'ACCEPTABLE'
    else:
        self.test_status = 'RUNNING'
    if self._terminate_on_failure and self.test_status == 'FAILURE':
        new_status = py_trees.common.Status.FAILURE
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    return new_status

class AverageVelocityTest(Criterion):
    """
    This class contains an atomic test for average velocity.

    Important parameters:
    - actor: CARLA actor to be used for this test
    - avg_velocity_success: If the actor's average velocity is more than this value (in m/s),
                            the test result is SUCCESS
    - avg_velocity_acceptable: If the actor's average velocity is more than this value (in m/s),
                               the test result is ACCEPTABLE
    - optional [optional]: If True, the result is not considered for an overall pass/fail result
    """

    def __init__(self, actor, avg_velocity_success, avg_velocity_acceptable=None, optional=False, name='CheckAverageVelocity'):
        """
        Setup actor and average velovity expected
        """
        super(AverageVelocityTest, self).__init__(name, actor, avg_velocity_success, avg_velocity_acceptable, optional)
        self._last_location = None
        self._distance = 0.0

    def initialise(self):
        self._last_location = CarlaDataProvider.get_location(self.actor)
        super(AverageVelocityTest, self).initialise()

    def update(self):
        """
        Check velocity
        """
        new_status = py_trees.common.Status.RUNNING
        if self.actor is None:
            return new_status
        location = CarlaDataProvider.get_location(self.actor)
        if location is None:
            return new_status
        if self._last_location is None:
            self._last_location = location
            return new_status
        self._distance += location.distance(self._last_location)
        self._last_location = location
        elapsed_time = GameTime.get_time()
        if elapsed_time > 0.0:
            self.actual_value = self._distance / elapsed_time
        if self.actual_value > self.expected_value_success:
            self.test_status = 'SUCCESS'
        elif self.expected_value_acceptable is not None and self.actual_value > self.expected_value_acceptable:
            self.test_status = 'ACCEPTABLE'
        else:
            self.test_status = 'RUNNING'
        if self._terminate_on_failure and self.test_status == 'FAILURE':
            new_status = py_trees.common.Status.FAILURE
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

    def terminate(self, new_status):
        """
        Set final status
        """
        if self.test_status == 'RUNNING':
            self.test_status = 'FAILURE'
        super(AverageVelocityTest, self).terminate(new_status)

def __init__(self, actor, avg_velocity_success, avg_velocity_acceptable=None, optional=False, name='CheckAverageVelocity'):
    """
        Setup actor and average velovity expected
        """
    super(AverageVelocityTest, self).__init__(name, actor, avg_velocity_success, avg_velocity_acceptable, optional)
    self._last_location = None
    self._distance = 0.0

def initialise(self):
    self._last_location = CarlaDataProvider.get_location(self.actor)
    super(AverageVelocityTest, self).initialise()

def update(self):
    """
        Check velocity
        """
    new_status = py_trees.common.Status.RUNNING
    if self.actor is None:
        return new_status
    location = CarlaDataProvider.get_location(self.actor)
    if location is None:
        return new_status
    if self._last_location is None:
        self._last_location = location
        return new_status
    self._distance += location.distance(self._last_location)
    self._last_location = location
    elapsed_time = GameTime.get_time()
    if elapsed_time > 0.0:
        self.actual_value = self._distance / elapsed_time
    if self.actual_value > self.expected_value_success:
        self.test_status = 'SUCCESS'
    elif self.expected_value_acceptable is not None and self.actual_value > self.expected_value_acceptable:
        self.test_status = 'ACCEPTABLE'
    else:
        self.test_status = 'RUNNING'
    if self._terminate_on_failure and self.test_status == 'FAILURE':
        new_status = py_trees.common.Status.FAILURE
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
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

class ReachedRegionTest(Criterion):
    """
    This class contains the reached region test
    The test is a success if the actor reaches a specified region

    Important parameters:
    - actor: CARLA actor to be used for this test
    - min_x, max_x, min_y, max_y: Bounding box of the checked region
    """

    def __init__(self, actor, min_x, max_x, min_y, max_y, name='ReachedRegionTest'):
        """
        Setup trigger region (rectangle provided by
        [min_x,min_y] and [max_x,max_y]
        """
        super(ReachedRegionTest, self).__init__(name, actor, 0)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._actor = actor
        self._min_x = min_x
        self._max_x = max_x
        self._min_y = min_y
        self._max_y = max_y

    def update(self):
        """
        Check if the actor location is within trigger region
        """
        new_status = py_trees.common.Status.RUNNING
        location = CarlaDataProvider.get_location(self._actor)
        if location is None:
            return new_status
        in_region = False
        if self.test_status != 'SUCCESS':
            in_region = (location.x > self._min_x and location.x < self._max_x) and (location.y > self._min_y and location.y < self._max_y)
            if in_region:
                self.test_status = 'SUCCESS'
            else:
                self.test_status = 'RUNNING'
        if self.test_status == 'SUCCESS':
            new_status = py_trees.common.Status.SUCCESS
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

def __init__(self, actor, min_x, max_x, min_y, max_y, name='ReachedRegionTest'):
    """
        Setup trigger region (rectangle provided by
        [min_x,min_y] and [max_x,max_y]
        """
    super(ReachedRegionTest, self).__init__(name, actor, 0)
    self.logger.debug('%s.__init__()' % self.__class__.__name__)
    self._actor = actor
    self._min_x = min_x
    self._max_x = max_x
    self._min_y = min_y
    self._max_y = max_y

def update(self):
    """
        Check if the actor location is within trigger region
        """
    new_status = py_trees.common.Status.RUNNING
    location = CarlaDataProvider.get_location(self._actor)
    if location is None:
        return new_status
    in_region = False
    if self.test_status != 'SUCCESS':
        in_region = (location.x > self._min_x and location.x < self._max_x) and (location.y > self._min_y and location.y < self._max_y)
        if in_region:
            self.test_status = 'SUCCESS'
        else:
            self.test_status = 'RUNNING'
    if self.test_status == 'SUCCESS':
        new_status = py_trees.common.Status.SUCCESS
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    return new_status

class OffRoadTest(Criterion):
    """
    Atomic containing a test to detect when an actor deviates from the driving lanes. This atomic can
    fail when actor has spent a specific time outside driving lanes (defined by OpenDRIVE). Simplified
    version of OnSidewalkTest, and doesn't relly on waypoints with *Sidewalk* lane types

    Args:
        actor (carla.Actor): CARLA actor to be used for this test
        duration (float): Time spent at sidewalks before the atomic fails.
            If terminate_on_failure isn't active, this is ignored.
        optional (bool): If True, the result is not considered for an overall pass/fail result
            when using the output argument
        terminate_on_failure (bool): If True, the atomic will fail when the duration condition has been met.
    """

    def __init__(self, actor, duration=0, optional=False, terminate_on_failure=False, name='OffRoadTest'):
        """
        Setup of the variables
        """
        super(OffRoadTest, self).__init__(name, actor, 0, None, optional, terminate_on_failure)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._map = CarlaDataProvider.get_map()
        self._offroad = False
        self._duration = duration
        self._prev_time = None
        self._time_offroad = 0

    def update(self):
        """
        First, transforms the actor's current position to its corresponding waypoint. This is
        filtered to only use waypoints of type Driving or Parking. Depending on these results,
        the actor will be considered to be outside (or inside) driving lanes.

        returns:
            py_trees.common.Status.FAILURE: when the actor has spent a given duration outside driving lanes
            py_trees.common.Status.RUNNING: the rest of the time
        """
        new_status = py_trees.common.Status.RUNNING
        current_location = CarlaDataProvider.get_location(self.actor)
        drive_waypoint = self._map.get_waypoint(current_location, project_to_road=False)
        park_waypoint = self._map.get_waypoint(current_location, project_to_road=False, lane_type=carla.LaneType.Parking)
        if drive_waypoint or park_waypoint:
            self._offroad = False
        else:
            self._offroad = True
        if self._offroad:
            if self._prev_time is None:
                self._prev_time = GameTime.get_time()
            else:
                curr_time = GameTime.get_time()
                self._time_offroad += curr_time - self._prev_time
                self._prev_time = curr_time
        else:
            self._prev_time = None
        if self._time_offroad > self._duration:
            self.test_status = 'FAILURE'
        if self._terminate_on_failure and self.test_status == 'FAILURE':
            new_status = py_trees.common.Status.FAILURE
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

def __init__(self, actor, duration=0, optional=False, terminate_on_failure=False, name='OffRoadTest'):
    """
        Setup of the variables
        """
    super(OffRoadTest, self).__init__(name, actor, 0, None, optional, terminate_on_failure)
    self.logger.debug('%s.__init__()' % self.__class__.__name__)
    self._map = CarlaDataProvider.get_map()
    self._offroad = False
    self._duration = duration
    self._prev_time = None
    self._time_offroad = 0

def update(self):
    """
        First, transforms the actor's current position to its corresponding waypoint. This is
        filtered to only use waypoints of type Driving or Parking. Depending on these results,
        the actor will be considered to be outside (or inside) driving lanes.

        returns:
            py_trees.common.Status.FAILURE: when the actor has spent a given duration outside driving lanes
            py_trees.common.Status.RUNNING: the rest of the time
        """
    new_status = py_trees.common.Status.RUNNING
    current_location = CarlaDataProvider.get_location(self.actor)
    drive_waypoint = self._map.get_waypoint(current_location, project_to_road=False)
    park_waypoint = self._map.get_waypoint(current_location, project_to_road=False, lane_type=carla.LaneType.Parking)
    if drive_waypoint or park_waypoint:
        self._offroad = False
    else:
        self._offroad = True
    if self._offroad:
        if self._prev_time is None:
            self._prev_time = GameTime.get_time()
        else:
            curr_time = GameTime.get_time()
            self._time_offroad += curr_time - self._prev_time
            self._prev_time = curr_time
    else:
        self._prev_time = None
    if self._time_offroad > self._duration:
        self.test_status = 'FAILURE'
    if self._terminate_on_failure and self.test_status == 'FAILURE':
        new_status = py_trees.common.Status.FAILURE
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    return new_status

class EndofRoadTest(Criterion):
    """
    Atomic containing a test to detect when an actor has changed to a different road

    Args:
        actor (carla.Actor): CARLA actor to be used for this test
        duration (float): Time spent after ending the road before the atomic fails.
            If terminate_on_failure isn't active, this is ignored.
        optional (bool): If True, the result is not considered for an overall pass/fail result
            when using the output argument
        terminate_on_failure (bool): If True, the atomic will fail when the duration condition has been met.
    """

    def __init__(self, actor, duration=0, optional=False, terminate_on_failure=False, name='EndofRoadTest'):
        """
        Setup of the variables
        """
        super(EndofRoadTest, self).__init__(name, actor, 0, None, optional, terminate_on_failure)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._map = CarlaDataProvider.get_map()
        self._end_of_road = False
        self._duration = duration
        self._start_time = None
        self._time_end_road = 0
        self._road_id = None

    def update(self):
        """
        First, transforms the actor's current position to its corresponding waypoint. Then the road id
        is compared with the initial one and if that's the case, a time is started

        returns:
            py_trees.common.Status.FAILURE: when the actor has spent a given duration outside driving lanes
            py_trees.common.Status.RUNNING: the rest of the time
        """
        new_status = py_trees.common.Status.RUNNING
        current_location = CarlaDataProvider.get_location(self.actor)
        current_waypoint = self._map.get_waypoint(current_location)
        if self._road_id is None:
            self._road_id = current_waypoint.road_id
        elif self._road_id != current_waypoint.road_id or self._start_time:
            if self._start_time is None:
                self._start_time = GameTime.get_time()
                return new_status
            curr_time = GameTime.get_time()
            self._time_end_road = curr_time - self._start_time
            if self._time_end_road > self._duration:
                self.test_status = 'FAILURE'
                self.actual_value += 1
                return py_trees.common.Status.SUCCESS
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

def __init__(self, actor, duration=0, optional=False, terminate_on_failure=False, name='EndofRoadTest'):
    """
        Setup of the variables
        """
    super(EndofRoadTest, self).__init__(name, actor, 0, None, optional, terminate_on_failure)
    self.logger.debug('%s.__init__()' % self.__class__.__name__)
    self._map = CarlaDataProvider.get_map()
    self._end_of_road = False
    self._duration = duration
    self._start_time = None
    self._time_end_road = 0
    self._road_id = None

def update(self):
    """
        First, transforms the actor's current position to its corresponding waypoint. Then the road id
        is compared with the initial one and if that's the case, a time is started

        returns:
            py_trees.common.Status.FAILURE: when the actor has spent a given duration outside driving lanes
            py_trees.common.Status.RUNNING: the rest of the time
        """
    new_status = py_trees.common.Status.RUNNING
    current_location = CarlaDataProvider.get_location(self.actor)
    current_waypoint = self._map.get_waypoint(current_location)
    if self._road_id is None:
        self._road_id = current_waypoint.road_id
    elif self._road_id != current_waypoint.road_id or self._start_time:
        if self._start_time is None:
            self._start_time = GameTime.get_time()
            return new_status
        curr_time = GameTime.get_time()
        self._time_end_road = curr_time - self._start_time
        if self._time_end_road > self._duration:
            self.test_status = 'FAILURE'
            self.actual_value += 1
            return py_trees.common.Status.SUCCESS
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    return new_status

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

def __init__(self, actor, x, y, radius, name='InRadiusRegionTest'):
    """
        """
    super(InRadiusRegionTest, self).__init__(name, actor, 0)
    self.logger.debug('%s.__init__()' % self.__class__.__name__)
    self._actor = actor
    self._x = x
    self._y = y
    self._radius = radius

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

def calculate_distance(location, other_location, global_planner=None):
    """
    Method to calculate the distance between to locations

    Note: It uses the direct distance between the current location and the
          target location to estimate the time to arrival.
          To be accurate, it would have to use the distance along the
          (shortest) route between the two locations.
    """
    if global_planner:
        distance = 0
        route = global_planner.trace_route(location, other_location)
        for i in range(1, len(route)):
            curr_loc = route[i][0].transform.location
            prev_loc = route[i - 1][0].transform.location
            distance += curr_loc.distance(prev_loc)
        return distance
    return location.distance(other_location)

def get_actor_control(actor):
    """
    Method to return the type of control to the actor.
    """
    control = actor.get_control()
    actor_type = actor.type_id.split('.')[0]
    if not isinstance(actor, carla.Walker):
        control.steering = 0
    else:
        control.speed = 0
    return (control, actor_type)

class AtomicBehavior(py_trees.behaviour.Behaviour):
    """
    Base class for all atomic behaviors used to setup a scenario

    *All behaviors should use this class as parent*

    Important parameters:
    - name: Name of the atomic behavior
    """

    def __init__(self, name, actor=None):
        """
        Default init. Has to be called via super from derived class
        """
        super(AtomicBehavior, self).__init__(name)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self.name = name
        self._actor = actor

    def setup(self, unused_timeout=15):
        """
        Default setup
        """
        self.logger.debug('%s.setup()' % self.__class__.__name__)
        return True

    def initialise(self):
        """
        Initialise setup terminates WaypointFollowers
        Check whether WF for this actor is running and terminate all active WFs
        """
        if self._actor is not None:
            try:
                check_attr = operator.attrgetter('running_WF_actor_{}'.format(self._actor.id))
                terminate_wf = copy.copy(check_attr(py_trees.blackboard.Blackboard()))
                py_trees.blackboard.Blackboard().set('terminate_WF_actor_{}'.format(self._actor.id), terminate_wf, overwrite=True)
            except AttributeError:
                pass
        self.logger.debug('%s.initialise()' % self.__class__.__name__)

    def terminate(self, new_status):
        """
        Default terminate. Can be extended in derived class
        """
        self.logger.debug('%s.terminate()[%s->%s]' % (self.__class__.__name__, self.status, new_status))

def __init__(self, name, actor=None):
    """
        Default init. Has to be called via super from derived class
        """
    super(AtomicBehavior, self).__init__(name)
    self.logger.debug('%s.__init__()' % self.__class__.__name__)
    self.name = name
    self._actor = actor

def setup(self, unused_timeout=15):
    """
        Default setup
        """
    self.logger.debug('%s.setup()' % self.__class__.__name__)
    return True

def initialise(self):
    """
        Initialise setup terminates WaypointFollowers
        Check whether WF for this actor is running and terminate all active WFs
        """
    if self._actor is not None:
        try:
            check_attr = operator.attrgetter('running_WF_actor_{}'.format(self._actor.id))
            terminate_wf = copy.copy(check_attr(py_trees.blackboard.Blackboard()))
            py_trees.blackboard.Blackboard().set('terminate_WF_actor_{}'.format(self._actor.id), terminate_wf, overwrite=True)
        except AttributeError:
            pass
    self.logger.debug('%s.initialise()' % self.__class__.__name__)

def terminate(self, new_status):
    """
        Default terminate. Can be extended in derived class
        """
    self.logger.debug('%s.terminate()[%s->%s]' % (self.__class__.__name__, self.status, new_status))

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

def __init__(self, script, base_path=None, name='RunScript'):
    """
        Setup parameters
        """
    super(RunScript, self).__init__(name)
    self.logger.debug('%s.__init__()' % self.__class__.__name__)
    self._script = script
    self._base_path = base_path

class ChangeWeather(AtomicBehavior):
    """
    Atomic to write a new weather configuration into the blackboard.
    Used in combination with WeatherBehavior() to have a continuous weather simulation.

    The behavior immediately terminates with SUCCESS after updating the blackboard.

    Args:
        weather (srunner.scenariomanager.weather_sim.Weather): New weather settings.
        name (string): Name of the behavior.
            Defaults to 'UpdateWeather'.

    Attributes:
        _weather (srunner.scenariomanager.weather_sim.Weather): Weather settings.
    """

    def __init__(self, weather, name='ChangeWeather'):
        """
        Setup parameters
        """
        super(ChangeWeather, self).__init__(name)
        self._weather = weather

    def update(self):
        """
        Write weather into blackboard and exit with success

        returns:
            py_trees.common.Status.SUCCESS
        """
        py_trees.blackboard.Blackboard().set('CarlaWeather', self._weather, overwrite=True)
        return py_trees.common.Status.SUCCESS

def __init__(self, weather, name='ChangeWeather'):
    """
        Setup parameters
        """
    super(ChangeWeather, self).__init__(name)
    self._weather = weather

def update(self):
    """
        Write weather into blackboard and exit with success

        returns:
            py_trees.common.Status.SUCCESS
        """
    py_trees.blackboard.Blackboard().set('CarlaWeather', self._weather, overwrite=True)
    return py_trees.common.Status.SUCCESS

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

def __init__(self, friction, name='ChangeRoadFriction'):
    """
        Setup parameters
        """
    super(ChangeRoadFriction, self).__init__(name)
    self._friction = friction

class ChangeActorControl(AtomicBehavior):
    """
    Atomic to change the longitudinal/lateral control logic for an actor.
    The (actor, controller) pair is stored inside the Blackboard.

    The behavior immediately terminates with SUCCESS after the controller.

    Args:
        actor (carla.Actor): Actor that should be controlled by the controller.
        control_py_module (string): Name of the python module containing the implementation
            of the controller.
        args (dictionary): Additional arguments for the controller.
        name (string): Name of the behavior.
            Defaults to 'ChangeActorControl'.

    Attributes:
        _actor_control (ActorControl): Instance of the actor control.
    """

    def __init__(self, actor, control_py_module, args, name='ChangeActorControl'):
        """
        Setup actor controller.
        """
        super(ChangeActorControl, self).__init__(name, actor)
        self._actor_control = ActorControl(actor, control_py_module=control_py_module, args=args)

    def update(self):
        """
        Write (actor, controler) pair to Blackboard, or update the controller
        if actor already exists as a key.

        returns:
            py_trees.common.Status.SUCCESS
        """
        actor_dict = {}
        try:
            check_actors = operator.attrgetter('ActorsWithController')
            actor_dict = check_actors(py_trees.blackboard.Blackboard())
        except AttributeError:
            pass
        if actor_dict:
            if self._actor.id in actor_dict:
                actor_dict[self._actor.id].reset()
        actor_dict[self._actor.id] = self._actor_control
        py_trees.blackboard.Blackboard().set('ActorsWithController', actor_dict, overwrite=True)
        return py_trees.common.Status.SUCCESS

def __init__(self, actor, control_py_module, args, name='ChangeActorControl'):
    """
        Setup actor controller.
        """
    super(ChangeActorControl, self).__init__(name, actor)
    self._actor_control = ActorControl(actor, control_py_module=control_py_module, args=args)

def update(self):
    """
        Write (actor, controler) pair to Blackboard, or update the controller
        if actor already exists as a key.

        returns:
            py_trees.common.Status.SUCCESS
        """
    actor_dict = {}
    try:
        check_actors = operator.attrgetter('ActorsWithController')
        actor_dict = check_actors(py_trees.blackboard.Blackboard())
    except AttributeError:
        pass
    if actor_dict:
        if self._actor.id in actor_dict:
            actor_dict[self._actor.id].reset()
    actor_dict[self._actor.id] = self._actor_control
    py_trees.blackboard.Blackboard().set('ActorsWithController', actor_dict, overwrite=True)
    return py_trees.common.Status.SUCCESS

class UpdateAllActorControls(AtomicBehavior):
    """
    Atomic to update (run one control loop step) all actor controls.

    The behavior is always in RUNNING state.

    Args:
        name (string): Name of the behavior.
            Defaults to 'UpdateAllActorControls'.
    """

    def __init__(self, name='UpdateAllActorControls'):
        """
        Constructor
        """
        super(UpdateAllActorControls, self).__init__(name)

    def update(self):
        """
        Execute one control loop step for all actor controls.

        returns:
            py_trees.common.Status.RUNNING
        """
        actor_dict = {}
        try:
            check_actors = operator.attrgetter('ActorsWithController')
            actor_dict = check_actors(py_trees.blackboard.Blackboard())
        except AttributeError:
            pass
        for actor_id in actor_dict:
            actor_dict[actor_id].run_step()
        return py_trees.common.Status.RUNNING

def __init__(self, name='UpdateAllActorControls'):
    """
        Constructor
        """
    super(UpdateAllActorControls, self).__init__(name)

def update(self):
    """
        Execute one control loop step for all actor controls.

        returns:
            py_trees.common.Status.RUNNING
        """
    actor_dict = {}
    try:
        check_actors = operator.attrgetter('ActorsWithController')
        actor_dict = check_actors(py_trees.blackboard.Blackboard())
    except AttributeError:
        pass
    for actor_id in actor_dict:
        actor_dict[actor_id].run_step()
    return py_trees.common.Status.RUNNING

class ChangeActorTargetSpeed(AtomicBehavior):
    """
    Atomic to change the target speed for an actor controller.

    The behavior is in RUNNING state until the distance/duration
    conditions are satisfied, or if a second ChangeActorTargetSpeed atomic
    for the same actor is triggered.

    Args:
        actor (carla.Actor): Controlled actor.
        target_speed (float): New target speed [m/s].
        init_speed (boolean): Flag to indicate if the speed is the initial actor speed.
            Defaults to False.
        duration (float): Duration of the maneuver [s].
            Defaults to None.
        distance (float): Distance of the maneuver [m].
            Defaults to None.
        relative_actor (carla.Actor): If the target speed setting should be relative to another actor.
            Defaults to None.
        value (float): Offset, if the target speed setting should be relative to another actor.
            Defaults to None.
        value_type (string): Either 'Delta' or 'Factor' influencing how the offset to the reference actors
            velocity is applied. Defaults to None.
        continuous (boolean): If True, the atomic remains in RUNNING, independent of duration or distance.
            Defaults to False.
        name (string): Name of the behavior.
            Defaults to 'ChangeActorTargetSpeed'.

    Attributes:
        _target_speed (float): New target speed [m/s].
        _init_speed (boolean): Flag to indicate if the speed is the initial actor speed.
            Defaults to False.
        _start_time (float): Start time of the atomic [s].
            Defaults to None.
        _start_location (carla.Location): Start location of the atomic.
            Defaults to None.
        _duration (float): Duration of the maneuver [s].
            Defaults to None.
        _distance (float): Distance of the maneuver [m].
            Defaults to None.
        _relative_actor (carla.Actor): If the target speed setting should be relative to another actor.
            Defaults to None.
        _value (float): Offset, if the target speed setting should be relative to another actor.
            Defaults to None.
        _value_type (string): Either 'Delta' or 'Factor' influencing how the offset to the reference actors
            velocity is applied. Defaults to None.
        _continuous (boolean): If True, the atomic remains in RUNNING, independent of duration or distance.
            Defaults to False.
    """

    def __init__(self, actor, target_speed, init_speed=False, duration=None, distance=None, relative_actor=None, value=None, value_type=None, continuous=False, name='ChangeActorTargetSpeed'):
        """
        Setup parameters
        """
        super(ChangeActorTargetSpeed, self).__init__(name, actor)
        self._target_speed = target_speed
        self._init_speed = init_speed
        self._start_time = None
        self._start_location = None
        self._relative_actor = relative_actor
        self._value = value
        self._value_type = value_type
        self._continuous = continuous
        self._duration = duration
        self._distance = distance

    def initialise(self):
        """
        Set initial parameters such as _start_time and _start_location,
        and get (actor, controller) pair from Blackboard.

        May throw if actor is not available as key for the ActorsWithController
        dictionary from Blackboard.
        """
        actor_dict = {}
        try:
            check_actors = operator.attrgetter('ActorsWithController')
            actor_dict = check_actors(py_trees.blackboard.Blackboard())
        except AttributeError:
            pass
        if not actor_dict or not self._actor.id in actor_dict:
            raise RuntimeError('Actor not found in ActorsWithController BlackBoard')
        self._start_time = GameTime.get_time()
        self._start_location = CarlaDataProvider.get_location(self._actor)
        if self._relative_actor:
            relative_velocity = CarlaDataProvider.get_velocity(self._relative_actor)
            if self._value_type == 'delta':
                self._target_speed = relative_velocity + self._value
            elif self._value_type == 'factor':
                self._target_speed = relative_velocity * self._value
            else:
                print('self._value_type must be delta or factor')
        actor_dict[self._actor.id].update_target_speed(self._target_speed, start_time=self._start_time)
        if self._init_speed:
            actor_dict[self._actor.id].set_init_speed()
        super(ChangeActorTargetSpeed, self).initialise()

    def update(self):
        """
        Check the actor's current state and update target speed, if it is relative to another actor.

        returns:
            py_trees.common.Status.SUCCESS, if the duration or distance driven exceeded limits
                                            if another ChangeActorTargetSpeed atomic for the same actor was triggered.
            py_trees.common.Status.FAILURE, if the actor is not found in ActorsWithController Blackboard dictionary.
            py_trees.common.Status.FAILURE, else.
        """
        try:
            check_actors = operator.attrgetter('ActorsWithController')
            actor_dict = check_actors(py_trees.blackboard.Blackboard())
        except AttributeError:
            pass
        if not actor_dict or not self._actor.id in actor_dict:
            return py_trees.common.Status.FAILURE
        if actor_dict[self._actor.id].get_last_longitudinal_command() != self._start_time:
            return py_trees.common.Status.SUCCESS
        new_status = py_trees.common.Status.RUNNING
        if self._relative_actor:
            relative_velocity = CarlaDataProvider.get_velocity(self._relative_actor)
            if self._value_type == 'delta':
                actor_dict[self._actor.id].update_target_speed(relative_velocity + self._value)
            elif self._value_type == 'factor':
                actor_dict[self._actor.id].update_target_speed(relative_velocity * self._value)
            else:
                print('self._value_type must be delta or factor')
        if not self._continuous:
            if self._duration is not None and GameTime.get_time() - self._start_time > self._duration:
                new_status = py_trees.common.Status.SUCCESS
            driven_distance = CarlaDataProvider.get_location(self._actor).distance(self._start_location)
            if self._distance is not None and driven_distance > self._distance:
                new_status = py_trees.common.Status.SUCCESS
        if self._distance is None and self._duration is None:
            new_status = py_trees.common.Status.SUCCESS
        return new_status

def __init__(self, actor, target_speed, init_speed=False, duration=None, distance=None, relative_actor=None, value=None, value_type=None, continuous=False, name='ChangeActorTargetSpeed'):
    """
        Setup parameters
        """
    super(ChangeActorTargetSpeed, self).__init__(name, actor)
    self._target_speed = target_speed
    self._init_speed = init_speed
    self._start_time = None
    self._start_location = None
    self._relative_actor = relative_actor
    self._value = value
    self._value_type = value_type
    self._continuous = continuous
    self._duration = duration
    self._distance = distance

def initialise(self):
    """
        Set initial parameters such as _start_time and _start_location,
        and get (actor, controller) pair from Blackboard.

        May throw if actor is not available as key for the ActorsWithController
        dictionary from Blackboard.
        """
    actor_dict = {}
    try:
        check_actors = operator.attrgetter('ActorsWithController')
        actor_dict = check_actors(py_trees.blackboard.Blackboard())
    except AttributeError:
        pass
    if not actor_dict or not self._actor.id in actor_dict:
        raise RuntimeError('Actor not found in ActorsWithController BlackBoard')
    self._start_time = GameTime.get_time()
    self._start_location = CarlaDataProvider.get_location(self._actor)
    if self._relative_actor:
        relative_velocity = CarlaDataProvider.get_velocity(self._relative_actor)
        if self._value_type == 'delta':
            self._target_speed = relative_velocity + self._value
        elif self._value_type == 'factor':
            self._target_speed = relative_velocity * self._value
        else:
            print('self._value_type must be delta or factor')
    actor_dict[self._actor.id].update_target_speed(self._target_speed, start_time=self._start_time)
    if self._init_speed:
        actor_dict[self._actor.id].set_init_speed()
    super(ChangeActorTargetSpeed, self).initialise()

def update(self):
    """
        Check the actor's current state and update target speed, if it is relative to another actor.

        returns:
            py_trees.common.Status.SUCCESS, if the duration or distance driven exceeded limits
                                            if another ChangeActorTargetSpeed atomic for the same actor was triggered.
            py_trees.common.Status.FAILURE, if the actor is not found in ActorsWithController Blackboard dictionary.
            py_trees.common.Status.FAILURE, else.
        """
    try:
        check_actors = operator.attrgetter('ActorsWithController')
        actor_dict = check_actors(py_trees.blackboard.Blackboard())
    except AttributeError:
        pass
    if not actor_dict or not self._actor.id in actor_dict:
        return py_trees.common.Status.FAILURE
    if actor_dict[self._actor.id].get_last_longitudinal_command() != self._start_time:
        return py_trees.common.Status.SUCCESS
    new_status = py_trees.common.Status.RUNNING
    if self._relative_actor:
        relative_velocity = CarlaDataProvider.get_velocity(self._relative_actor)
        if self._value_type == 'delta':
            actor_dict[self._actor.id].update_target_speed(relative_velocity + self._value)
        elif self._value_type == 'factor':
            actor_dict[self._actor.id].update_target_speed(relative_velocity * self._value)
        else:
            print('self._value_type must be delta or factor')
    if not self._continuous:
        if self._duration is not None and GameTime.get_time() - self._start_time > self._duration:
            new_status = py_trees.common.Status.SUCCESS
        driven_distance = CarlaDataProvider.get_location(self._actor).distance(self._start_location)
        if self._distance is not None and driven_distance > self._distance:
            new_status = py_trees.common.Status.SUCCESS
    if self._distance is None and self._duration is None:
        new_status = py_trees.common.Status.SUCCESS
    return new_status

class ChangeActorWaypoints(AtomicBehavior):
    """
    Atomic to change the waypoints for an actor controller.

    The behavior is in RUNNING state until the last waypoint is reached, or if a
    second waypoint related atomic for the same actor is triggered. These are:
    - ChangeActorWaypoints
    - ChangeActorWaypointsToReachPosition
    - ChangeActorLateralMotion

    Args:
        actor (carla.Actor): Controlled actor.
        waypoints (List of carla.Transform): List of waypoints (CARLA transforms).
        name (string): Name of the behavior.
            Defaults to 'ChangeActorWaypoints'.

    Attributes:
        _waypoints (List of carla.Transform): List of waypoints (CARLA transforms).
        _start_time (float): Start time of the atomic [s].
            Defaults to None.
    """

    def __init__(self, actor, waypoints, name='ChangeActorWaypoints'):
        """
        Setup parameters
        """
        super(ChangeActorWaypoints, self).__init__(name, actor)
        self._waypoints = waypoints
        self._start_time = None

    def initialise(self):
        """
        Set _start_time and get (actor, controller) pair from Blackboard.

        Set waypoint list for actor controller.

        May throw if actor is not available as key for the ActorsWithController
        dictionary from Blackboard.
        """
        actor_dict = {}
        try:
            check_actors = operator.attrgetter('ActorsWithController')
            actor_dict = check_actors(py_trees.blackboard.Blackboard())
        except AttributeError:
            pass
        if not actor_dict or not self._actor.id in actor_dict:
            raise RuntimeError('Actor not found in ActorsWithController BlackBoard')
        self._start_time = GameTime.get_time()
        actor_dict[self._actor.id].update_waypoints(self._waypoints, start_time=self._start_time)
        super(ChangeActorWaypoints, self).initialise()

    def update(self):
        """
        Check the actor's state along the waypoint route.

        returns:
            py_trees.common.Status.SUCCESS, if the final waypoint was reached, or
                                            if another ChangeActorWaypoints atomic for the same actor was triggered.
            py_trees.common.Status.FAILURE, if the actor is not found in ActorsWithController Blackboard dictionary.
            py_trees.common.Status.FAILURE, else.
        """
        try:
            check_actors = operator.attrgetter('ActorsWithController')
            actor_dict = check_actors(py_trees.blackboard.Blackboard())
        except AttributeError:
            pass
        if not actor_dict or not self._actor.id in actor_dict:
            return py_trees.common.Status.FAILURE
        if actor_dict[self._actor.id].get_last_waypoint_command() != self._start_time:
            return py_trees.common.Status.SUCCESS
        new_status = py_trees.common.Status.RUNNING
        if actor_dict[self._actor.id].check_reached_waypoint_goal():
            new_status = py_trees.common.Status.SUCCESS
        return new_status

def __init__(self, actor, waypoints, name='ChangeActorWaypoints'):
    """
        Setup parameters
        """
    super(ChangeActorWaypoints, self).__init__(name, actor)
    self._waypoints = waypoints
    self._start_time = None

def initialise(self):
    """
        Set _start_time and get (actor, controller) pair from Blackboard.

        Set waypoint list for actor controller.

        May throw if actor is not available as key for the ActorsWithController
        dictionary from Blackboard.
        """
    actor_dict = {}
    try:
        check_actors = operator.attrgetter('ActorsWithController')
        actor_dict = check_actors(py_trees.blackboard.Blackboard())
    except AttributeError:
        pass
    if not actor_dict or not self._actor.id in actor_dict:
        raise RuntimeError('Actor not found in ActorsWithController BlackBoard')
    self._start_time = GameTime.get_time()
    actor_dict[self._actor.id].update_waypoints(self._waypoints, start_time=self._start_time)
    super(ChangeActorWaypoints, self).initialise()

def update(self):
    """
        Check the actor's state along the waypoint route.

        returns:
            py_trees.common.Status.SUCCESS, if the final waypoint was reached, or
                                            if another ChangeActorWaypoints atomic for the same actor was triggered.
            py_trees.common.Status.FAILURE, if the actor is not found in ActorsWithController Blackboard dictionary.
            py_trees.common.Status.FAILURE, else.
        """
    try:
        check_actors = operator.attrgetter('ActorsWithController')
        actor_dict = check_actors(py_trees.blackboard.Blackboard())
    except AttributeError:
        pass
    if not actor_dict or not self._actor.id in actor_dict:
        return py_trees.common.Status.FAILURE
    if actor_dict[self._actor.id].get_last_waypoint_command() != self._start_time:
        return py_trees.common.Status.SUCCESS
    new_status = py_trees.common.Status.RUNNING
    if actor_dict[self._actor.id].check_reached_waypoint_goal():
        new_status = py_trees.common.Status.SUCCESS
    return new_status

class ChangeActorWaypointsToReachPosition(ChangeActorWaypoints):
    """
    Atomic to change the waypoints for an actor controller in order to reach
    a given position.

    The behavior is in RUNNING state until the last waypoint is reached, or if a
    second waypoint related atomic for the same actor is triggered. These are:
    - ChangeActorWaypoints
    - ChangeActorWaypointsToReachPosition
    - ChangeActorLateralMotion

    Args:
        actor (carla.Actor): Controlled actor.
        position (carla.Transform): CARLA transform to be reached by the actor.
        name (string): Name of the behavior.
            Defaults to 'ChangeActorWaypointsToReachPosition'.

    Attributes:
        _waypoints (List of carla.Transform): List of waypoints (CARLA transforms).
        _end_transform (carla.Transform): Final position (CARLA transform).
        _start_time (float): Start time of the atomic [s].
            Defaults to None.
        _grp (GlobalPlanner): global planner instance of the town
    """

    def __init__(self, actor, position, name='ChangeActorWaypointsToReachPosition'):
        """
        Setup parameters
        """
        super(ChangeActorWaypointsToReachPosition, self).__init__(actor, [])
        self._end_transform = position
        town_map = CarlaDataProvider.get_map()
        dao = GlobalRoutePlannerDAO(town_map, 2)
        self._grp = GlobalRoutePlanner(dao)
        self._grp.setup()

    def initialise(self):
        """
        Set _start_time and get (actor, controller) pair from Blackboard.

        Generate a waypoint list (route) which representes the route. Set
        this waypoint list for the actor controller.

        May throw if actor is not available as key for the ActorsWithController
        dictionary from Blackboard.
        """
        position_actor = CarlaDataProvider.get_location(self._actor)
        plan = self._grp.trace_route(position_actor, self._end_transform.location)
        for elem in plan:
            self._waypoints.append(elem[0].transform)
        super(ChangeActorWaypointsToReachPosition, self).initialise()

def __init__(self, actor, position, name='ChangeActorWaypointsToReachPosition'):
    """
        Setup parameters
        """
    super(ChangeActorWaypointsToReachPosition, self).__init__(actor, [])
    self._end_transform = position
    town_map = CarlaDataProvider.get_map()
    dao = GlobalRoutePlannerDAO(town_map, 2)
    self._grp = GlobalRoutePlanner(dao)
    self._grp.setup()

def initialise(self):
    """
        Set _start_time and get (actor, controller) pair from Blackboard.

        Generate a waypoint list (route) which representes the route. Set
        this waypoint list for the actor controller.

        May throw if actor is not available as key for the ActorsWithController
        dictionary from Blackboard.
        """
    position_actor = CarlaDataProvider.get_location(self._actor)
    plan = self._grp.trace_route(position_actor, self._end_transform.location)
    for elem in plan:
        self._waypoints.append(elem[0].transform)
    super(ChangeActorWaypointsToReachPosition, self).initialise()

class ChangeActorLateralMotion(AtomicBehavior):
    """
    Atomic to change the waypoints for an actor controller.

    The behavior is in RUNNING state until the last waypoint is reached, or if a
    second waypoint related atomic for the same actor is triggered. These are:
    - ChangeActorWaypoints
    - ChangeActorWaypointsToReachPosition
    - ChangeActorLateralMotion

    Args:
        actor (carla.Actor): Controlled actor.
        direction (string): Lane change direction ('left' or 'right').
            Defaults to 'left'.
        distance_lane_change (float): Distance of the lance change [meters].
            Defaults to 25.
        distance_other_lane (float): Driven distance after the lange change [meters].
            Defaults to 100.
        name (string): Name of the behavior.
            Defaults to 'ChangeActorLateralMotion'.

    Attributes:
        _waypoints (List of carla.Transform): List of waypoints representing the lane change (CARLA transforms).
        _direction (string): Lane change direction ('left' or 'right').
        _distance_same_lane (float): Distance on the same lane before the lane change starts [meters]
            Constant to 5.
        _distance_other_lane (float): Max. distance on the target lane after the lance change [meters]
            Constant to 100.
        _distance_lane_change (float): Max. total distance of the lane change [meters].
        _pos_before_lane_change: carla.Location of the actor before the lane change.
            Defaults to None.
        _target_lane_id (int): Id of the target lane
            Defaults to None.
        _start_time (float): Start time of the atomic [s].
            Defaults to None.
    """

    def __init__(self, actor, direction='left', distance_lane_change=25, distance_other_lane=100, name='ChangeActorLateralMotion'):
        """
        Setup parameters
        """
        super(ChangeActorLateralMotion, self).__init__(name, actor)
        self._waypoints = []
        self._direction = direction
        self._distance_same_lane = 5
        self._distance_other_lane = distance_other_lane
        self._distance_lane_change = distance_lane_change
        self._pos_before_lane_change = None
        self._target_lane_id = None
        self._start_time = None

    def initialise(self):
        """
        Set _start_time and get (actor, controller) pair from Blackboard.

        Generate a waypoint list (route) which representes the lane change. Set
        this waypoint list for the actor controller.

        May throw if actor is not available as key for the ActorsWithController
        dictionary from Blackboard.
        """
        actor_dict = {}
        try:
            check_actors = operator.attrgetter('ActorsWithController')
            actor_dict = check_actors(py_trees.blackboard.Blackboard())
        except AttributeError:
            pass
        if not actor_dict or not self._actor.id in actor_dict:
            raise RuntimeError('Actor not found in ActorsWithController BlackBoard')
        self._start_time = GameTime.get_time()
        position_actor = CarlaDataProvider.get_map().get_waypoint(CarlaDataProvider.get_location(self._actor))
        plan, self._target_lane_id = generate_target_waypoint_list_multilane(position_actor, self._direction, self._distance_same_lane, self._distance_other_lane, self._distance_lane_change, check='false')
        for elem in plan:
            self._waypoints.append(elem[0].transform)
        actor_dict[self._actor.id].update_waypoints(self._waypoints, start_time=self._start_time)
        super(ChangeActorLateralMotion, self).initialise()

    def update(self):
        """
        Check the actor's current state and if the lane change was completed

        returns:
            py_trees.common.Status.SUCCESS, if lane change was successful, or
                                            if another ChangeActorLateralMotion atomic for the same actor was triggered.
            py_trees.common.Status.FAILURE, if the actor is not found in ActorsWithController Blackboard dictionary.
            py_trees.common.Status.FAILURE, else.
        """
        try:
            check_actors = operator.attrgetter('ActorsWithController')
            actor_dict = check_actors(py_trees.blackboard.Blackboard())
        except AttributeError:
            pass
        if not actor_dict or not self._actor.id in actor_dict:
            return py_trees.common.Status.FAILURE
        if actor_dict[self._actor.id].get_last_waypoint_command() != self._start_time:
            return py_trees.common.Status.SUCCESS
        new_status = py_trees.common.Status.RUNNING
        current_position_actor = CarlaDataProvider.get_map().get_waypoint(self._actor.get_location())
        current_lane_id = current_position_actor.lane_id
        if current_lane_id == self._target_lane_id:
            distance = current_position_actor.transform.location.distance(self._pos_before_lane_change)
            if distance > self._distance_other_lane:
                new_status = py_trees.common.Status.SUCCESS
        else:
            self._pos_before_lane_change = current_position_actor.transform.location
        return new_status

def __init__(self, actor, direction='left', distance_lane_change=25, distance_other_lane=100, name='ChangeActorLateralMotion'):
    """
        Setup parameters
        """
    super(ChangeActorLateralMotion, self).__init__(name, actor)
    self._waypoints = []
    self._direction = direction
    self._distance_same_lane = 5
    self._distance_other_lane = distance_other_lane
    self._distance_lane_change = distance_lane_change
    self._pos_before_lane_change = None
    self._target_lane_id = None
    self._start_time = None

def initialise(self):
    """
        Set _start_time and get (actor, controller) pair from Blackboard.

        Generate a waypoint list (route) which representes the lane change. Set
        this waypoint list for the actor controller.

        May throw if actor is not available as key for the ActorsWithController
        dictionary from Blackboard.
        """
    actor_dict = {}
    try:
        check_actors = operator.attrgetter('ActorsWithController')
        actor_dict = check_actors(py_trees.blackboard.Blackboard())
    except AttributeError:
        pass
    if not actor_dict or not self._actor.id in actor_dict:
        raise RuntimeError('Actor not found in ActorsWithController BlackBoard')
    self._start_time = GameTime.get_time()
    position_actor = CarlaDataProvider.get_map().get_waypoint(CarlaDataProvider.get_location(self._actor))
    plan, self._target_lane_id = generate_target_waypoint_list_multilane(position_actor, self._direction, self._distance_same_lane, self._distance_other_lane, self._distance_lane_change, check='false')
    for elem in plan:
        self._waypoints.append(elem[0].transform)
    actor_dict[self._actor.id].update_waypoints(self._waypoints, start_time=self._start_time)
    super(ChangeActorLateralMotion, self).initialise()

def update(self):
    """
        Check the actor's current state and if the lane change was completed

        returns:
            py_trees.common.Status.SUCCESS, if lane change was successful, or
                                            if another ChangeActorLateralMotion atomic for the same actor was triggered.
            py_trees.common.Status.FAILURE, if the actor is not found in ActorsWithController Blackboard dictionary.
            py_trees.common.Status.FAILURE, else.
        """
    try:
        check_actors = operator.attrgetter('ActorsWithController')
        actor_dict = check_actors(py_trees.blackboard.Blackboard())
    except AttributeError:
        pass
    if not actor_dict or not self._actor.id in actor_dict:
        return py_trees.common.Status.FAILURE
    if actor_dict[self._actor.id].get_last_waypoint_command() != self._start_time:
        return py_trees.common.Status.SUCCESS
    new_status = py_trees.common.Status.RUNNING
    current_position_actor = CarlaDataProvider.get_map().get_waypoint(self._actor.get_location())
    current_lane_id = current_position_actor.lane_id
    if current_lane_id == self._target_lane_id:
        distance = current_position_actor.transform.location.distance(self._pos_before_lane_change)
        if distance > self._distance_other_lane:
            new_status = py_trees.common.Status.SUCCESS
    else:
        self._pos_before_lane_change = current_position_actor.transform.location
    return new_status

class ActorTransformSetterToOSCPosition(AtomicBehavior):
    """
    OpenSCENARIO atomic
    This class contains an atomic behavior to set the transform of an OpenSCENARIO actor.

    Important parameters:
    - actor: CARLA actor to execute the behavior
    - osc_position: OpenSCENARIO position
    - physics [optional]: If physics is true, the actor physics will be reactivated upon success

    The behavior terminates when actor is set to the new actor transform (closer than 1 meter)

    NOTE:
    It is very important to ensure that the actor location is spawned to the new transform because of the
    appearence of a rare runtime processing error. WaypointFollower with LocalPlanner,
    might fail if new_status is set to success before the actor is really positioned at the new transform.
    Therefore: calculate_distance(actor, transform) < 1 meter
    """

    def __init__(self, actor, osc_position, physics=True, name='ActorTransformSetterToOSCPosition'):
        """
        Setup parameters
        """
        super(ActorTransformSetterToOSCPosition, self).__init__(name, actor)
        self._osc_position = osc_position
        self._physics = physics
        self._osc_transform = None

    def initialise(self):
        super(ActorTransformSetterToOSCPosition, self).initialise()
        if self._actor.is_alive:
            self._actor.set_target_velocity(carla.Vector3D(0, 0, 0))
            self._actor.set_target_angular_velocity(carla.Vector3D(0, 0, 0))

    def update(self):
        """
        Transform actor
        """
        new_status = py_trees.common.Status.RUNNING
        self._osc_transform = srunner.tools.openscenario_parser.OpenScenarioParser.convert_position_to_transform(self._osc_position)
        self._actor.set_transform(self._osc_transform)
        if not self._actor.is_alive:
            new_status = py_trees.common.Status.FAILURE
        if calculate_distance(self._actor.get_location(), self._osc_transform.location) < 1.0:
            if self._physics:
                self._actor.set_simulate_physics(enabled=True)
            new_status = py_trees.common.Status.SUCCESS
        return new_status

def __init__(self, actor, osc_position, physics=True, name='ActorTransformSetterToOSCPosition'):
    """
        Setup parameters
        """
    super(ActorTransformSetterToOSCPosition, self).__init__(name, actor)
    self._osc_position = osc_position
    self._physics = physics
    self._osc_transform = None

def update(self):
    """
        Transform actor
        """
    new_status = py_trees.common.Status.RUNNING
    self._osc_transform = srunner.tools.openscenario_parser.OpenScenarioParser.convert_position_to_transform(self._osc_position)
    self._actor.set_transform(self._osc_transform)
    if not self._actor.is_alive:
        new_status = py_trees.common.Status.FAILURE
    if calculate_distance(self._actor.get_location(), self._osc_transform.location) < 1.0:
        if self._physics:
            self._actor.set_simulate_physics(enabled=True)
        new_status = py_trees.common.Status.SUCCESS
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

class AccelerateToCatchUp(AtomicBehavior):
    """
    This class contains an atomic acceleration behavior.
    The car will accelerate until it is faster than another car, in order to catch up distance.
    This behaviour is especially useful before a lane change (e.g. LaneChange atom).

    Important parameters:
    - actor: CARLA actor to execute the behaviour
    - other_actor: Reference CARLA actor, actor you want to catch up to
    - throttle_value: acceleration value between 0.0 and 1.0
    - delta_velocity: speed up to the velocity of other actor plus delta_velocity
    - trigger_distance: distance between the actors
    - max_distance: driven distance to catch up has to be smaller than max_distance

    The behaviour will terminate succesful, when the two actors are in trigger_distance.
    If max_distance is driven by the actor before actors are in trigger_distance,
    then the behaviour ends with a failure.
    """

    def __init__(self, actor, other_actor, throttle_value=1, delta_velocity=10, trigger_distance=5, max_distance=500, name='AccelerateToCatchUp'):
        """
        Setup parameters
        The target_speet is calculated on the fly.
        """
        super(AccelerateToCatchUp, self).__init__(name, actor)
        self._other_actor = other_actor
        self._throttle_value = throttle_value
        self._delta_velocity = delta_velocity
        self._trigger_distance = trigger_distance
        self._max_distance = max_distance
        self._control, self._type = get_actor_control(actor)
        self._initial_actor_pos = None

    def initialise(self):
        self._initial_actor_pos = CarlaDataProvider.get_location(self._actor)
        super(AccelerateToCatchUp, self).initialise()

    def update(self):
        actor_speed = CarlaDataProvider.get_velocity(self._actor)
        target_speed = CarlaDataProvider.get_velocity(self._other_actor) + self._delta_velocity
        distance = CarlaDataProvider.get_location(self._actor).distance(CarlaDataProvider.get_location(self._other_actor))
        driven_distance = CarlaDataProvider.get_location(self._actor).distance(self._initial_actor_pos)
        if actor_speed < target_speed:
            self._control.throttle = self._throttle_value
        if actor_speed >= target_speed:
            self._control.throttle = 0
        self._actor.apply_control(self._control)
        if distance <= self._trigger_distance:
            new_status = py_trees.common.Status.SUCCESS
        elif driven_distance > self._max_distance:
            new_status = py_trees.common.Status.FAILURE
        else:
            new_status = py_trees.common.Status.RUNNING
        return new_status

def __init__(self, actor, other_actor, throttle_value=1, delta_velocity=10, trigger_distance=5, max_distance=500, name='AccelerateToCatchUp'):
    """
        Setup parameters
        The target_speet is calculated on the fly.
        """
    super(AccelerateToCatchUp, self).__init__(name, actor)
    self._other_actor = other_actor
    self._throttle_value = throttle_value
    self._delta_velocity = delta_velocity
    self._trigger_distance = trigger_distance
    self._max_distance = max_distance
    self._control, self._type = get_actor_control(actor)
    self._initial_actor_pos = None

def initialise(self):
    self._initial_actor_pos = CarlaDataProvider.get_location(self._actor)
    super(AccelerateToCatchUp, self).initialise()

def update(self):
    actor_speed = CarlaDataProvider.get_velocity(self._actor)
    target_speed = CarlaDataProvider.get_velocity(self._other_actor) + self._delta_velocity
    distance = CarlaDataProvider.get_location(self._actor).distance(CarlaDataProvider.get_location(self._other_actor))
    driven_distance = CarlaDataProvider.get_location(self._actor).distance(self._initial_actor_pos)
    if actor_speed < target_speed:
        self._control.throttle = self._throttle_value
    if actor_speed >= target_speed:
        self._control.throttle = 0
    self._actor.apply_control(self._control)
    if distance <= self._trigger_distance:
        new_status = py_trees.common.Status.SUCCESS
    elif driven_distance > self._max_distance:
        new_status = py_trees.common.Status.FAILURE
    else:
        new_status = py_trees.common.Status.RUNNING
    return new_status

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

class ChangeAutoPilot(AtomicBehavior):
    """
    This class contains an atomic behavior to disable/enable the use of the autopilot.

    Important parameters:
    - actor: CARLA actor to execute the behavior
    - activate: True (=enable autopilot) or False (=disable autopilot)
    - lane_change: Traffic Manager parameter. True (=enable lane changes) or False (=disable lane changes)
    - distance_between_vehicles: Traffic Manager parameter
    - max_speed: Traffic Manager parameter. Max speed of the actor. This will only work for road segments
                 with the same speed limit as the first one

    The behavior terminates after changing the autopilot state
    """

    def __init__(self, actor, activate, parameters=None, name='ChangeAutoPilot'):
        """
        Setup parameters
        """
        super(ChangeAutoPilot, self).__init__(name, actor)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._activate = activate
        self._tm = CarlaDataProvider.get_client().get_trafficmanager(CarlaDataProvider.get_traffic_manager_port())
        self._parameters = parameters

    def update(self):
        """
        De/activate autopilot
        """
        self._actor.set_autopilot(self._activate)
        if self._parameters is not None:
            if 'auto_lane_change' in self._parameters:
                lane_change = self._parameters['auto_lane_change']
                self._tm.auto_lane_change(self._actor, lane_change)
            if 'max_speed' in self._parameters:
                max_speed = self._parameters['max_speed']
                max_road_speed = self._actor.get_speed_limit()
                if max_road_speed is not None:
                    percentage = (max_road_speed - max_speed) / max_road_speed * 100.0
                    self._tm.vehicle_percentage_speed_difference(self._actor, percentage)
                else:
                    print("ChangeAutopilot: Unable to find the vehicle's speed limit")
            if 'distance_between_vehicles' in self._parameters:
                dist_vehicles = self._parameters['distance_between_vehicles']
                self._tm.distance_to_leading_vehicle(self._actor, dist_vehicles)
            if 'force_lane_change' in self._parameters:
                force_lane_change = self._parameters['force_lane_change']
                self._tm.force_lane_change(self._actor, force_lane_change)
            if 'ignore_vehicles_percentage' in self._parameters:
                ignore_vehicles = self._parameters['ignore_vehicles_percentage']
                self._tm.ignore_vehicles_percentage(self._actor, ignore_vehicles)
        new_status = py_trees.common.Status.SUCCESS
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

def __init__(self, actor, activate, parameters=None, name='ChangeAutoPilot'):
    """
        Setup parameters
        """
    super(ChangeAutoPilot, self).__init__(name, actor)
    self.logger.debug('%s.__init__()' % self.__class__.__name__)
    self._activate = activate
    self._tm = CarlaDataProvider.get_client().get_trafficmanager(CarlaDataProvider.get_traffic_manager_port())
    self._parameters = parameters

class StopVehicle(AtomicBehavior):
    """
    This class contains an atomic stopping behavior. The controlled traffic
    participant will decelerate with _bake_value_ until reaching a full stop.

    Important parameters:
    - actor: CARLA actor to execute the behavior
    - brake_value: Brake value in [0,1] applied

    The behavior terminates when the actor stopped moving
    """

    def __init__(self, actor, brake_value, name='Stopping'):
        """
        Setup _actor and maximum braking value
        """
        super(StopVehicle, self).__init__(name, actor)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._control, self._type = get_actor_control(actor)
        if self._type == 'walker':
            self._control.speed = 0
        self._brake_value = brake_value

    def update(self):
        """
        Set brake to brake_value until reaching full stop
        """
        new_status = py_trees.common.Status.RUNNING
        if self._type == 'vehicle':
            if CarlaDataProvider.get_velocity(self._actor) > EPSILON:
                self._control.brake = self._brake_value
            else:
                new_status = py_trees.common.Status.SUCCESS
                self._control.brake = 0
        else:
            new_status = py_trees.common.Status.SUCCESS
        self._actor.apply_control(self._control)
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

def __init__(self, actor, brake_value, name='Stopping'):
    """
        Setup _actor and maximum braking value
        """
    super(StopVehicle, self).__init__(name, actor)
    self.logger.debug('%s.__init__()' % self.__class__.__name__)
    self._control, self._type = get_actor_control(actor)
    if self._type == 'walker':
        self._control.speed = 0
    self._brake_value = brake_value

def update(self):
    """
        Set brake to brake_value until reaching full stop
        """
    new_status = py_trees.common.Status.RUNNING
    if self._type == 'vehicle':
        if CarlaDataProvider.get_velocity(self._actor) > EPSILON:
            self._control.brake = self._brake_value
        else:
            new_status = py_trees.common.Status.SUCCESS
            self._control.brake = 0
    else:
        new_status = py_trees.common.Status.SUCCESS
    self._actor.apply_control(self._control)
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    return new_status

class SyncArrival(AtomicBehavior):
    """
    This class contains an atomic behavior to
    set velocity of actor so that it reaches location at the same time as
    actor_reference. The behavior assumes that the two actors are moving
    towards location in a straight line.

    Important parameters:
    - actor: CARLA actor to execute the behavior
    - actor_reference: Reference actor with which arrival is synchronized
    - target_location: CARLA location where the actors should "meet"
    - gain[optional]: Coefficient for actor's throttle and break controls

    Note: In parallel to this behavior a termination behavior has to be used
          to keep continue synchronization for a certain duration, or for a
          certain distance, etc.
    """

    def __init__(self, actor, actor_reference, target_location, gain=1, name='SyncArrival'):
        """
        Setup required parameters
        """
        super(SyncArrival, self).__init__(name, actor)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._control = carla.VehicleControl()
        self._actor_reference = actor_reference
        self._target_location = target_location
        self._gain = gain
        self._control.steering = 0

    def update(self):
        """
        Dynamic control update for actor velocity
        """
        new_status = py_trees.common.Status.RUNNING
        distance_reference = calculate_distance(CarlaDataProvider.get_location(self._actor_reference), self._target_location)
        distance = calculate_distance(CarlaDataProvider.get_location(self._actor), self._target_location)
        velocity_reference = CarlaDataProvider.get_velocity(self._actor_reference)
        time_reference = float('inf')
        if velocity_reference > 0:
            time_reference = distance_reference / velocity_reference
        velocity_current = CarlaDataProvider.get_velocity(self._actor)
        time_current = float('inf')
        if velocity_current > 0:
            time_current = distance / velocity_current
        control_value = self._gain * (time_current - time_reference)
        if control_value > 0:
            self._control.throttle = min([control_value, 1])
            self._control.brake = 0
        else:
            self._control.throttle = 0
            self._control.brake = min([abs(control_value), 1])
        self._actor.apply_control(self._control)
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

    def terminate(self, new_status):
        """
        On termination of this behavior, the throttle should be set back to 0.,
        to avoid further acceleration.
        """
        if self._actor is not None and self._actor.is_alive:
            self._control.throttle = 0.0
            self._control.brake = 0.0
            self._actor.apply_control(self._control)
        super(SyncArrival, self).terminate(new_status)

def __init__(self, actor, actor_reference, target_location, gain=1, name='SyncArrival'):
    """
        Setup required parameters
        """
    super(SyncArrival, self).__init__(name, actor)
    self.logger.debug('%s.__init__()' % self.__class__.__name__)
    self._control = carla.VehicleControl()
    self._actor_reference = actor_reference
    self._target_location = target_location
    self._gain = gain
    self._control.steering = 0

def update(self):
    """
        Dynamic control update for actor velocity
        """
    new_status = py_trees.common.Status.RUNNING
    distance_reference = calculate_distance(CarlaDataProvider.get_location(self._actor_reference), self._target_location)
    distance = calculate_distance(CarlaDataProvider.get_location(self._actor), self._target_location)
    velocity_reference = CarlaDataProvider.get_velocity(self._actor_reference)
    time_reference = float('inf')
    if velocity_reference > 0:
        time_reference = distance_reference / velocity_reference
    velocity_current = CarlaDataProvider.get_velocity(self._actor)
    time_current = float('inf')
    if velocity_current > 0:
        time_current = distance / velocity_current
    control_value = self._gain * (time_current - time_reference)
    if control_value > 0:
        self._control.throttle = min([control_value, 1])
        self._control.brake = 0
    else:
        self._control.throttle = 0
        self._control.brake = min([abs(control_value), 1])
    self._actor.apply_control(self._control)
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    return new_status

def terminate(self, new_status):
    """
        On termination of this behavior, the throttle should be set back to 0.,
        to avoid further acceleration.
        """
    if self._actor is not None and self._actor.is_alive:
        self._control.throttle = 0.0
        self._control.brake = 0.0
        self._actor.apply_control(self._control)
    super(SyncArrival, self).terminate(new_status)

class AddNoiseToVehicle(AtomicBehavior):
    """
    This class contains an atomic jitter behavior.
    To add noise to steer as well as throttle of the vehicle.

    Important parameters:
    - actor: CARLA actor to execute the behavior
    - steer_value: Applied steering noise in [0,1]
    - throttle_value: Applied throttle noise in [0,1]

    The behavior terminates after setting the new actor controls
    """

    def __init__(self, actor, steer_value, throttle_value, name='Jittering'):
        """
        Setup actor , maximum steer value and throttle value
        """
        super(AddNoiseToVehicle, self).__init__(name, actor)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._control = carla.VehicleControl()
        self._steer_value = steer_value
        self._throttle_value = throttle_value

    def update(self):
        """
        Set steer to steer_value and throttle to throttle_value until reaching full stop
        """
        self._control = self._actor.get_control()
        self._control.steer = self._steer_value
        self._control.throttle = self._throttle_value
        new_status = py_trees.common.Status.SUCCESS
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        self._actor.apply_control(self._control)
        return new_status

def __init__(self, actor, steer_value, throttle_value, name='Jittering'):
    """
        Setup actor , maximum steer value and throttle value
        """
    super(AddNoiseToVehicle, self).__init__(name, actor)
    self.logger.debug('%s.__init__()' % self.__class__.__name__)
    self._control = carla.VehicleControl()
    self._steer_value = steer_value
    self._throttle_value = throttle_value

def update(self):
    """
        Set steer to steer_value and throttle to throttle_value until reaching full stop
        """
    self._control = self._actor.get_control()
    self._control.steer = self._steer_value
    self._control.throttle = self._throttle_value
    new_status = py_trees.common.Status.SUCCESS
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    self._actor.apply_control(self._control)
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

class BasicAgentBehavior(AtomicBehavior):
    """
    This class contains an atomic behavior, which uses the
    basic_agent from CARLA to control the actor until
    reaching a target location.

    Important parameters:
    - actor: CARLA actor to execute the behavior
    - target_location: Is the desired target location (carla.location),
                       the actor should move to

    The behavior terminates after reaching the target_location (within 2 meters)
    """
    _acceptable_target_distance = 2

    def __init__(self, actor, target_location, name='BasicAgentBehavior'):
        """
        Setup actor and maximum steer value
        """
        super(BasicAgentBehavior, self).__init__(name, actor)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._agent = BasicAgent(actor)
        self._agent.set_destination((target_location.x, target_location.y, target_location.z))
        self._control = carla.VehicleControl()
        self._target_location = target_location

    def update(self):
        new_status = py_trees.common.Status.RUNNING
        self._control = self._agent.run_step()
        location = CarlaDataProvider.get_location(self._actor)
        if calculate_distance(location, self._target_location) < self._acceptable_target_distance:
            new_status = py_trees.common.Status.SUCCESS
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        self._actor.apply_control(self._control)
        return new_status

    def terminate(self, new_status):
        self._control.throttle = 0.0
        self._control.brake = 0.0
        self._actor.apply_control(self._control)
        super(BasicAgentBehavior, self).terminate(new_status)

def __init__(self, actor, target_location, name='BasicAgentBehavior'):
    """
        Setup actor and maximum steer value
        """
    super(BasicAgentBehavior, self).__init__(name, actor)
    self.logger.debug('%s.__init__()' % self.__class__.__name__)
    self._agent = BasicAgent(actor)
    self._agent.set_destination((target_location.x, target_location.y, target_location.z))
    self._control = carla.VehicleControl()
    self._target_location = target_location

def update(self):
    new_status = py_trees.common.Status.RUNNING
    self._control = self._agent.run_step()
    location = CarlaDataProvider.get_location(self._actor)
    if calculate_distance(location, self._target_location) < self._acceptable_target_distance:
        new_status = py_trees.common.Status.SUCCESS
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    self._actor.apply_control(self._control)
    return new_status

def terminate(self, new_status):
    self._control.throttle = 0.0
    self._control.brake = 0.0
    self._actor.apply_control(self._control)
    super(BasicAgentBehavior, self).terminate(new_status)

class Idle(AtomicBehavior):
    """
    This class contains an idle behavior scenario

    Important parameters:
    - duration[optional]: Duration in seconds of this behavior

    A termination can be enforced by providing a duration value.
    Alternatively, a parallel termination behavior has to be used.
    """

    def __init__(self, duration=float('inf'), name='Idle'):
        """
        Setup actor
        """
        super(Idle, self).__init__(name)
        self._duration = duration
        self._start_time = 0
        self.logger.debug('%s.__init__()' % self.__class__.__name__)

    def initialise(self):
        """
        Set start time
        """
        self._start_time = GameTime.get_time()
        super(Idle, self).initialise()

    def update(self):
        """
        Keep running until termination condition is satisfied
        """
        new_status = py_trees.common.Status.RUNNING
        if GameTime.get_time() - self._start_time > self._duration:
            new_status = py_trees.common.Status.SUCCESS
        return new_status

def __init__(self, duration=float('inf'), name='Idle'):
    """
        Setup actor
        """
    super(Idle, self).__init__(name)
    self._duration = duration
    self._start_time = 0
    self.logger.debug('%s.__init__()' % self.__class__.__name__)

def initialise(self):
    """
        Set start time
        """
    self._start_time = GameTime.get_time()
    super(Idle, self).initialise()

def update(self):
    """
        Keep running until termination condition is satisfied
        """
    new_status = py_trees.common.Status.RUNNING
    if GameTime.get_time() - self._start_time > self._duration:
        new_status = py_trees.common.Status.SUCCESS
    return new_status

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

class LaneChange(WaypointFollower):
    """
     This class inherits from the class WaypointFollower.

     This class contains an atomic lane change behavior to a parallel lane.
     The vehicle follows a waypoint plan to the other lane, which is calculated in the initialise method.
     This waypoint plan is calculated with a scenario helper function.

    Important parameters:
    - actor: CARLA actor to execute the behavior
    - speed: speed of the actor for the lane change, in m/s
    - direction: 'right' or 'left', depending on which lane to change
    - distance_same_lane: straight distance before lane change, in m
    - distance_other_lane: straight distance after lane change, in m
    - distance_lane_change: straight distance for the lane change itself, in m

    The total distance driven is greater than the sum of distance_same_lane and distance_other_lane.
    It results from the lane change distance plus the distance_same_lane plus distance_other_lane.
    The lane change distance is set to 25m (straight), the driven distance is slightly greater.

    A parallel termination behavior has to be used.
    """

    def __init__(self, actor, speed=10, direction='left', distance_same_lane=5, distance_other_lane=100, distance_lane_change=25, name='LaneChange'):
        self._direction = direction
        self._distance_same_lane = distance_same_lane
        self._distance_other_lane = distance_other_lane
        self._distance_lane_change = distance_lane_change
        self._target_lane_id = None
        self._distance_new_lane = 0
        self._pos_before_lane_change = None
        super(LaneChange, self).__init__(actor, target_speed=speed, name=name)

    def initialise(self):
        position_actor = CarlaDataProvider.get_map().get_waypoint(self._actor.get_location())
        self._plan, self._target_lane_id = generate_target_waypoint_list_multilane(position_actor, self._direction, self._distance_same_lane, self._distance_other_lane, self._distance_lane_change, check='true')
        super(LaneChange, self).initialise()

    def update(self):
        status = super(LaneChange, self).update()
        current_position_actor = CarlaDataProvider.get_map().get_waypoint(self._actor.get_location())
        current_lane_id = current_position_actor.lane_id
        if current_lane_id == self._target_lane_id:
            distance = current_position_actor.transform.location.distance(self._pos_before_lane_change)
            if distance > self._distance_other_lane:
                status = py_trees.common.Status.SUCCESS
        else:
            self._pos_before_lane_change = current_position_actor.transform.location
        return status

def __init__(self, actor, speed=10, direction='left', distance_same_lane=5, distance_other_lane=100, distance_lane_change=25, name='LaneChange'):
    self._direction = direction
    self._distance_same_lane = distance_same_lane
    self._distance_other_lane = distance_other_lane
    self._distance_lane_change = distance_lane_change
    self._target_lane_id = None
    self._distance_new_lane = 0
    self._pos_before_lane_change = None
    super(LaneChange, self).__init__(actor, target_speed=speed, name=name)

def initialise(self):
    position_actor = CarlaDataProvider.get_map().get_waypoint(self._actor.get_location())
    self._plan, self._target_lane_id = generate_target_waypoint_list_multilane(position_actor, self._direction, self._distance_same_lane, self._distance_other_lane, self._distance_lane_change, check='true')
    super(LaneChange, self).initialise()

def update(self):
    status = super(LaneChange, self).update()
    current_position_actor = CarlaDataProvider.get_map().get_waypoint(self._actor.get_location())
    current_lane_id = current_position_actor.lane_id
    if current_lane_id == self._target_lane_id:
        distance = current_position_actor.transform.location.distance(self._pos_before_lane_change)
        if distance > self._distance_other_lane:
            status = py_trees.common.Status.SUCCESS
    else:
        self._pos_before_lane_change = current_position_actor.transform.location
    return status

class SetInitSpeed(AtomicBehavior):
    """
    This class contains an atomic behavior to set the init_speed of an actor,
    succeding immeditely after initializing
    """

    def __init__(self, actor, init_speed=10, name='SetInitSpeed'):
        self._init_speed = init_speed
        self._terminate = None
        self._actor = actor
        super(SetInitSpeed, self).__init__(name, actor)

    def initialise(self):
        """
        Initialize it's speed
        """
        transform = self._actor.get_transform()
        yaw = transform.rotation.yaw * (math.pi / 180)
        vx = math.cos(yaw) * self._init_speed
        vy = math.sin(yaw) * self._init_speed
        self._actor.set_target_velocity(carla.Vector3D(vx, vy, 0))

    def update(self):
        """
        Nothing to update, end the behavior
        """
        return py_trees.common.Status.SUCCESS

def __init__(self, actor, init_speed=10, name='SetInitSpeed'):
    self._init_speed = init_speed
    self._terminate = None
    self._actor = actor
    super(SetInitSpeed, self).__init__(name, actor)

class HandBrakeVehicle(AtomicBehavior):
    """
    This class contains an atomic hand brake behavior.
    To set the hand brake value of the vehicle.

    Important parameters:
    - vehicle: CARLA actor to execute the behavior
    - hand_brake_value to be applied in [0,1]

    The behavior terminates after setting the hand brake value
    """

    def __init__(self, vehicle, hand_brake_value, name='Braking'):
        """
        Setup vehicle control and brake value
        """
        super(HandBrakeVehicle, self).__init__(name)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._vehicle = vehicle
        self._control, self._type = get_actor_control(vehicle)
        self._hand_brake_value = hand_brake_value

    def update(self):
        """
        Set handbrake
        """
        new_status = py_trees.common.Status.SUCCESS
        if self._type == 'vehicle':
            self._control.hand_brake = self._hand_brake_value
            self._vehicle.apply_control(self._control)
        else:
            self._hand_brake_value = None
            self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
            self._vehicle.apply_control(self._control)
        return new_status

def __init__(self, vehicle, hand_brake_value, name='Braking'):
    """
        Setup vehicle control and brake value
        """
    super(HandBrakeVehicle, self).__init__(name)
    self.logger.debug('%s.__init__()' % self.__class__.__name__)
    self._vehicle = vehicle
    self._control, self._type = get_actor_control(vehicle)
    self._hand_brake_value = hand_brake_value

def update(self):
    """
        Set handbrake
        """
    new_status = py_trees.common.Status.SUCCESS
    if self._type == 'vehicle':
        self._control.hand_brake = self._hand_brake_value
        self._vehicle.apply_control(self._control)
    else:
        self._hand_brake_value = None
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        self._vehicle.apply_control(self._control)
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

def __init__(self, actor, name='ActorDestroy'):
    """
        Setup actor
        """
    super(ActorDestroy, self).__init__(name, actor)
    self.logger.debug('%s.__init__()' % self.__class__.__name__)

class ActorTransformSetter(AtomicBehavior):
    """
    This class contains an atomic behavior to set the transform
    of an actor.

    Important parameters:
    - actor: CARLA actor to execute the behavior
    - transform: New target transform (position + orientation) of the actor
    - physics [optional]: If physics is true, the actor physics will be reactivated upon success

    The behavior terminates when actor is set to the new actor transform (closer than 1 meter)

    NOTE:
    It is very important to ensure that the actor location is spawned to the new transform because of the
    appearence of a rare runtime processing error. WaypointFollower with LocalPlanner,
    might fail if new_status is set to success before the actor is really positioned at the new transform.
    Therefore: calculate_distance(actor, transform) < 1 meter
    """

    def __init__(self, actor, transform, physics=True, name='ActorTransformSetter'):
        """
        Init
        """
        super(ActorTransformSetter, self).__init__(name, actor)
        self._transform = transform
        self._physics = physics
        self.logger.debug('%s.__init__()' % self.__class__.__name__)

    def initialise(self):
        if self._actor.is_alive:
            self._actor.set_target_velocity(carla.Vector3D(0, 0, 0))
            self._actor.set_target_angular_velocity(carla.Vector3D(0, 0, 0))
            self._actor.set_transform(self._transform)
        super(ActorTransformSetter, self).initialise()

    def update(self):
        """
        Transform actor
        """
        new_status = py_trees.common.Status.RUNNING
        if not self._actor.is_alive:
            new_status = py_trees.common.Status.FAILURE
        if calculate_distance(self._actor.get_location(), self._transform.location) < 1.0:
            if self._physics:
                self._actor.set_simulate_physics(enabled=True)
            new_status = py_trees.common.Status.SUCCESS
        return new_status

def __init__(self, actor, transform, physics=True, name='ActorTransformSetter'):
    """
        Init
        """
    super(ActorTransformSetter, self).__init__(name, actor)
    self._transform = transform
    self._physics = physics
    self.logger.debug('%s.__init__()' % self.__class__.__name__)

def update(self):
    """
        Transform actor
        """
    new_status = py_trees.common.Status.RUNNING
    if not self._actor.is_alive:
        new_status = py_trees.common.Status.FAILURE
    if calculate_distance(self._actor.get_location(), self._transform.location) < 1.0:
        if self._physics:
            self._actor.set_simulate_physics(enabled=True)
        new_status = py_trees.common.Status.SUCCESS
    return new_status

class TrafficLightStateSetter(AtomicBehavior):
    """
    This class contains an atomic behavior to set the state of a given traffic light

    Args:
        actor (carla.TrafficLight): ID of the traffic light that shall be changed
        state (carla.TrafficLightState): New target state

    The behavior terminates after trying to set the new state
    """

    def __init__(self, actor, state, name='TrafficLightStateSetter'):
        """
        Init
        """
        super(TrafficLightStateSetter, self).__init__(name)
        self._actor = actor if 'traffic_light' in actor.type_id else None
        self._state = state
        self.logger.debug('%s.__init__()' % self.__class__.__name__)

    def update(self):
        """
        Change the state of the traffic light
        """
        if self._actor is None:
            return py_trees.common.Status.FAILURE
        new_status = py_trees.common.Status.RUNNING
        if self._actor.is_alive:
            self._actor.set_state(self._state)
            new_status = py_trees.common.Status.SUCCESS
        else:
            new_status = py_trees.common.Status.FAILURE
        return new_status

def __init__(self, actor, state, name='TrafficLightStateSetter'):
    """
        Init
        """
    super(TrafficLightStateSetter, self).__init__(name)
    self._actor = actor if 'traffic_light' in actor.type_id else None
    self._state = state
    self.logger.debug('%s.__init__()' % self.__class__.__name__)

def update(self):
    """
        Change the state of the traffic light
        """
    if self._actor is None:
        return py_trees.common.Status.FAILURE
    new_status = py_trees.common.Status.RUNNING
    if self._actor.is_alive:
        self._actor.set_state(self._state)
        new_status = py_trees.common.Status.SUCCESS
    else:
        new_status = py_trees.common.Status.FAILURE
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

class ActorSink(AtomicBehavior):
    """
    Implementation for a behavior that will indefinitely destroy actors
    that wander near a given location within a specified threshold.

    Important parameters:
    - actor_type_list: Type of CARLA actors to be spawned
    - sink_location: Location (carla.location) at which actors will be deleted
    - threshold: Distance around sink_location in which actors will be deleted

    A parallel termination behavior has to be used.
    """

    def __init__(self, sink_location, threshold, name='ActorSink'):
        """
        Setup class members
        """
        super(ActorSink, self).__init__(name)
        self._sink_location = sink_location
        self._threshold = threshold

    def update(self):
        new_status = py_trees.common.Status.RUNNING
        CarlaDataProvider.remove_actors_in_surrounding(self._sink_location, self._threshold)
        return new_status

def __init__(self, sink_location, threshold, name='ActorSink'):
    """
        Setup class members
        """
    super(ActorSink, self).__init__(name)
    self._sink_location = sink_location
    self._threshold = threshold

class StartRecorder(AtomicBehavior):
    """
    Atomic that starts the CARLA recorder. Only one can be active
    at a time, and if this isn't the case, the recorder will
    automatically stop the previous one.

    Args:
        recorder_name (str): name of the file to write the recorded data.
            Remember that a simple name will save the recording in
            'CarlaUE4/Saved/'. Otherwise, if some folder appears in the name,
            it will be considered an absolute path.
        name (str): name of the behavior
    """

    def __init__(self, recorder_name, name='StartRecorder'):
        """
        Setup class members
        """
        super(StartRecorder, self).__init__(name)
        self._client = CarlaDataProvider.get_client()
        self._recorder_name = recorder_name

    def update(self):
        self._client.start_recorder(self._recorder_name)
        return py_trees.common.Status.SUCCESS

def __init__(self, recorder_name, name='StartRecorder'):
    """
        Setup class members
        """
    super(StartRecorder, self).__init__(name)
    self._client = CarlaDataProvider.get_client()
    self._recorder_name = recorder_name

class StopRecorder(AtomicBehavior):
    """
    Atomic that stops the CARLA recorder.

    Args:
        name (str): name of the behavior
    """

    def __init__(self, name='StopRecorder'):
        """
        Setup class members
        """
        super(StopRecorder, self).__init__(name)
        self._client = CarlaDataProvider.get_client()

    def update(self):
        self._client.stop_recorder()
        return py_trees.common.Status.SUCCESS

def __init__(self, name='StopRecorder'):
    """
        Setup class members
        """
    super(StopRecorder, self).__init__(name)
    self._client = CarlaDataProvider.get_client()

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

class Criterion(py_trees.behaviour.Behaviour):
    """
    Base class for all criteria used to evaluate a scenario for success/failure

    Important parameters (PUBLIC):
    - name: Name of the criterion
    - expected_value_success:    Result in case of success
                                 (e.g. max_speed, zero collisions, ...)
    - expected_value_acceptable: Result that does not mean a failure,
                                 but is not good enough for a success
    - actual_value: Actual result after running the scenario
    - test_status: Used to access the result of the criterion
    - optional: Indicates if a criterion is optional (not used for overall analysis)
    """

    def __init__(self, name, actor, expected_value_success, expected_value_acceptable=None, optional=False, terminate_on_failure=False):
        super(Criterion, self).__init__(name)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._terminate_on_failure = terminate_on_failure
        self.name = name
        self.actor = actor
        self.test_status = 'INIT'
        self.expected_value_success = expected_value_success
        self.expected_value_acceptable = expected_value_acceptable
        self.actual_value = 0
        self.optional = optional
        self.list_traffic_events = []

    def initialise(self):
        """
        Initialise the criterion. Can be extended by the user-derived class
        """
        self.logger.debug('%s.initialise()' % self.__class__.__name__)

    def terminate(self, new_status):
        """
        Terminate the criterion. Can be extended by the user-derived class
        """
        if self.test_status == 'RUNNING' or self.test_status == 'INIT':
            self.test_status = 'SUCCESS'
        self.logger.debug('%s.terminate()[%s->%s]' % (self.__class__.__name__, self.status, new_status))

def __init__(self, name, actor, expected_value_success, expected_value_acceptable=None, optional=False, terminate_on_failure=False):
    super(Criterion, self).__init__(name)
    self.logger.debug('%s.__init__()' % self.__class__.__name__)
    self._terminate_on_failure = terminate_on_failure
    self.name = name
    self.actor = actor
    self.test_status = 'INIT'
    self.expected_value_success = expected_value_success
    self.expected_value_acceptable = expected_value_acceptable
    self.actual_value = 0
    self.optional = optional
    self.list_traffic_events = []

def initialise(self):
    """
        Initialise the criterion. Can be extended by the user-derived class
        """
    self.logger.debug('%s.initialise()' % self.__class__.__name__)

def terminate(self, new_status):
    """
        Terminate the criterion. Can be extended by the user-derived class
        """
    if self.test_status == 'RUNNING' or self.test_status == 'INIT':
        self.test_status = 'SUCCESS'
    self.logger.debug('%s.terminate()[%s->%s]' % (self.__class__.__name__, self.status, new_status))

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

def __init__(self, actor, max_velocity_allowed, optional=False, name='CheckMaximumVelocity'):
    """
        Setup actor and maximum allowed velovity
        """
    super(MaxVelocityTest, self).__init__(name, actor, max_velocity_allowed, None, optional)

class DrivenDistanceTest(Criterion):
    """
    This class contains an atomic test to check the driven distance

    Important parameters:
    - actor: CARLA actor to be used for this test
    - distance_success: If the actor's driven distance is more than this value (in meters),
                        the test result is SUCCESS
    - distance_acceptable: If the actor's driven distance is more than this value (in meters),
                           the test result is ACCEPTABLE
    - optional [optional]: If True, the result is not considered for an overall pass/fail result
    """

    def __init__(self, actor, distance_success, distance_acceptable=None, optional=False, name='CheckDrivenDistance'):
        """
        Setup actor
        """
        super(DrivenDistanceTest, self).__init__(name, actor, distance_success, distance_acceptable, optional)
        self._last_location = None

    def initialise(self):
        self._last_location = CarlaDataProvider.get_location(self.actor)
        super(DrivenDistanceTest, self).initialise()

    def update(self):
        """
        Check distance
        """
        new_status = py_trees.common.Status.RUNNING
        if self.actor is None:
            return new_status
        location = CarlaDataProvider.get_location(self.actor)
        if location is None:
            return new_status
        if self._last_location is None:
            self._last_location = location
            return new_status
        self.actual_value += location.distance(self._last_location)
        self._last_location = location
        if self.actual_value > self.expected_value_success:
            self.test_status = 'SUCCESS'
        elif self.expected_value_acceptable is not None and self.actual_value > self.expected_value_acceptable:
            self.test_status = 'ACCEPTABLE'
        else:
            self.test_status = 'RUNNING'
        if self._terminate_on_failure and self.test_status == 'FAILURE':
            new_status = py_trees.common.Status.FAILURE
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

    def terminate(self, new_status):
        """
        Set final status
        """
        if self.test_status != 'SUCCESS':
            self.test_status = 'FAILURE'
        self.actual_value = round(self.actual_value, 2)
        super(DrivenDistanceTest, self).terminate(new_status)

def __init__(self, actor, distance_success, distance_acceptable=None, optional=False, name='CheckDrivenDistance'):
    """
        Setup actor
        """
    super(DrivenDistanceTest, self).__init__(name, actor, distance_success, distance_acceptable, optional)
    self._last_location = None

def initialise(self):
    self._last_location = CarlaDataProvider.get_location(self.actor)
    super(DrivenDistanceTest, self).initialise()

def update(self):
    """
        Check distance
        """
    new_status = py_trees.common.Status.RUNNING
    if self.actor is None:
        return new_status
    location = CarlaDataProvider.get_location(self.actor)
    if location is None:
        return new_status
    if self._last_location is None:
        self._last_location = location
        return new_status
    self.actual_value += location.distance(self._last_location)
    self._last_location = location
    if self.actual_value > self.expected_value_success:
        self.test_status = 'SUCCESS'
    elif self.expected_value_acceptable is not None and self.actual_value > self.expected_value_acceptable:
        self.test_status = 'ACCEPTABLE'
    else:
        self.test_status = 'RUNNING'
    if self._terminate_on_failure and self.test_status == 'FAILURE':
        new_status = py_trees.common.Status.FAILURE
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    return new_status

class AverageVelocityTest(Criterion):
    """
    This class contains an atomic test for average velocity.

    Important parameters:
    - actor: CARLA actor to be used for this test
    - avg_velocity_success: If the actor's average velocity is more than this value (in m/s),
                            the test result is SUCCESS
    - avg_velocity_acceptable: If the actor's average velocity is more than this value (in m/s),
                               the test result is ACCEPTABLE
    - optional [optional]: If True, the result is not considered for an overall pass/fail result
    """

    def __init__(self, actor, avg_velocity_success, avg_velocity_acceptable=None, optional=False, name='CheckAverageVelocity'):
        """
        Setup actor and average velovity expected
        """
        super(AverageVelocityTest, self).__init__(name, actor, avg_velocity_success, avg_velocity_acceptable, optional)
        self._last_location = None
        self._distance = 0.0

    def initialise(self):
        self._last_location = CarlaDataProvider.get_location(self.actor)
        super(AverageVelocityTest, self).initialise()

    def update(self):
        """
        Check velocity
        """
        new_status = py_trees.common.Status.RUNNING
        if self.actor is None:
            return new_status
        location = CarlaDataProvider.get_location(self.actor)
        if location is None:
            return new_status
        if self._last_location is None:
            self._last_location = location
            return new_status
        self._distance += location.distance(self._last_location)
        self._last_location = location
        elapsed_time = GameTime.get_time()
        if elapsed_time > 0.0:
            self.actual_value = self._distance / elapsed_time
        if self.actual_value > self.expected_value_success:
            self.test_status = 'SUCCESS'
        elif self.expected_value_acceptable is not None and self.actual_value > self.expected_value_acceptable:
            self.test_status = 'ACCEPTABLE'
        else:
            self.test_status = 'RUNNING'
        if self._terminate_on_failure and self.test_status == 'FAILURE':
            new_status = py_trees.common.Status.FAILURE
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

    def terminate(self, new_status):
        """
        Set final status
        """
        if self.test_status == 'RUNNING':
            self.test_status = 'FAILURE'
        super(AverageVelocityTest, self).terminate(new_status)

def __init__(self, actor, avg_velocity_success, avg_velocity_acceptable=None, optional=False, name='CheckAverageVelocity'):
    """
        Setup actor and average velovity expected
        """
    super(AverageVelocityTest, self).__init__(name, actor, avg_velocity_success, avg_velocity_acceptable, optional)
    self._last_location = None
    self._distance = 0.0

def initialise(self):
    self._last_location = CarlaDataProvider.get_location(self.actor)
    super(AverageVelocityTest, self).initialise()

def update(self):
    """
        Check velocity
        """
    new_status = py_trees.common.Status.RUNNING
    if self.actor is None:
        return new_status
    location = CarlaDataProvider.get_location(self.actor)
    if location is None:
        return new_status
    if self._last_location is None:
        self._last_location = location
        return new_status
    self._distance += location.distance(self._last_location)
    self._last_location = location
    elapsed_time = GameTime.get_time()
    if elapsed_time > 0.0:
        self.actual_value = self._distance / elapsed_time
    if self.actual_value > self.expected_value_success:
        self.test_status = 'SUCCESS'
    elif self.expected_value_acceptable is not None and self.actual_value > self.expected_value_acceptable:
        self.test_status = 'ACCEPTABLE'
    else:
        self.test_status = 'RUNNING'
    if self._terminate_on_failure and self.test_status == 'FAILURE':
        new_status = py_trees.common.Status.FAILURE
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    return new_status

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

class ReachedRegionTest(Criterion):
    """
    This class contains the reached region test
    The test is a success if the actor reaches a specified region

    Important parameters:
    - actor: CARLA actor to be used for this test
    - min_x, max_x, min_y, max_y: Bounding box of the checked region
    """

    def __init__(self, actor, min_x, max_x, min_y, max_y, name='ReachedRegionTest'):
        """
        Setup trigger region (rectangle provided by
        [min_x,min_y] and [max_x,max_y]
        """
        super(ReachedRegionTest, self).__init__(name, actor, 0)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._actor = actor
        self._min_x = min_x
        self._max_x = max_x
        self._min_y = min_y
        self._max_y = max_y

    def update(self):
        """
        Check if the actor location is within trigger region
        """
        new_status = py_trees.common.Status.RUNNING
        location = CarlaDataProvider.get_location(self._actor)
        if location is None:
            return new_status
        in_region = False
        if self.test_status != 'SUCCESS':
            in_region = (location.x > self._min_x and location.x < self._max_x) and (location.y > self._min_y and location.y < self._max_y)
            if in_region:
                self.test_status = 'SUCCESS'
            else:
                self.test_status = 'RUNNING'
        if self.test_status == 'SUCCESS':
            new_status = py_trees.common.Status.SUCCESS
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

def __init__(self, actor, min_x, max_x, min_y, max_y, name='ReachedRegionTest'):
    """
        Setup trigger region (rectangle provided by
        [min_x,min_y] and [max_x,max_y]
        """
    super(ReachedRegionTest, self).__init__(name, actor, 0)
    self.logger.debug('%s.__init__()' % self.__class__.__name__)
    self._actor = actor
    self._min_x = min_x
    self._max_x = max_x
    self._min_y = min_y
    self._max_y = max_y

def update(self):
    """
        Check if the actor location is within trigger region
        """
    new_status = py_trees.common.Status.RUNNING
    location = CarlaDataProvider.get_location(self._actor)
    if location is None:
        return new_status
    in_region = False
    if self.test_status != 'SUCCESS':
        in_region = (location.x > self._min_x and location.x < self._max_x) and (location.y > self._min_y and location.y < self._max_y)
        if in_region:
            self.test_status = 'SUCCESS'
        else:
            self.test_status = 'RUNNING'
    if self.test_status == 'SUCCESS':
        new_status = py_trees.common.Status.SUCCESS
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    return new_status

class OffRoadTest(Criterion):
    """
    Atomic containing a test to detect when an actor deviates from the driving lanes. This atomic can
    fail when actor has spent a specific time outside driving lanes (defined by OpenDRIVE). Simplified
    version of OnSidewalkTest, and doesn't relly on waypoints with *Sidewalk* lane types

    Args:
        actor (carla.Actor): CARLA actor to be used for this test
        duration (float): Time spent at sidewalks before the atomic fails.
            If terminate_on_failure isn't active, this is ignored.
        optional (bool): If True, the result is not considered for an overall pass/fail result
            when using the output argument
        terminate_on_failure (bool): If True, the atomic will fail when the duration condition has been met.
    """

    def __init__(self, actor, duration=0, optional=False, terminate_on_failure=False, name='OffRoadTest'):
        """
        Setup of the variables
        """
        super(OffRoadTest, self).__init__(name, actor, 0, None, optional, terminate_on_failure)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._map = CarlaDataProvider.get_map()
        self._offroad = False
        self._duration = duration
        self._prev_time = None
        self._time_offroad = 0

    def update(self):
        """
        First, transforms the actor's current position to its corresponding waypoint. This is
        filtered to only use waypoints of type Driving or Parking. Depending on these results,
        the actor will be considered to be outside (or inside) driving lanes.

        returns:
            py_trees.common.Status.FAILURE: when the actor has spent a given duration outside driving lanes
            py_trees.common.Status.RUNNING: the rest of the time
        """
        new_status = py_trees.common.Status.RUNNING
        current_location = CarlaDataProvider.get_location(self.actor)
        drive_waypoint = self._map.get_waypoint(current_location, project_to_road=False)
        park_waypoint = self._map.get_waypoint(current_location, project_to_road=False, lane_type=carla.LaneType.Parking)
        if drive_waypoint or park_waypoint:
            self._offroad = False
        else:
            self._offroad = True
        if self._offroad:
            if self._prev_time is None:
                self._prev_time = GameTime.get_time()
            else:
                curr_time = GameTime.get_time()
                self._time_offroad += curr_time - self._prev_time
                self._prev_time = curr_time
        else:
            self._prev_time = None
        if self._time_offroad > self._duration:
            self.test_status = 'FAILURE'
        if self._terminate_on_failure and self.test_status == 'FAILURE':
            new_status = py_trees.common.Status.FAILURE
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

def __init__(self, actor, duration=0, optional=False, terminate_on_failure=False, name='OffRoadTest'):
    """
        Setup of the variables
        """
    super(OffRoadTest, self).__init__(name, actor, 0, None, optional, terminate_on_failure)
    self.logger.debug('%s.__init__()' % self.__class__.__name__)
    self._map = CarlaDataProvider.get_map()
    self._offroad = False
    self._duration = duration
    self._prev_time = None
    self._time_offroad = 0

def update(self):
    """
        First, transforms the actor's current position to its corresponding waypoint. This is
        filtered to only use waypoints of type Driving or Parking. Depending on these results,
        the actor will be considered to be outside (or inside) driving lanes.

        returns:
            py_trees.common.Status.FAILURE: when the actor has spent a given duration outside driving lanes
            py_trees.common.Status.RUNNING: the rest of the time
        """
    new_status = py_trees.common.Status.RUNNING
    current_location = CarlaDataProvider.get_location(self.actor)
    drive_waypoint = self._map.get_waypoint(current_location, project_to_road=False)
    park_waypoint = self._map.get_waypoint(current_location, project_to_road=False, lane_type=carla.LaneType.Parking)
    if drive_waypoint or park_waypoint:
        self._offroad = False
    else:
        self._offroad = True
    if self._offroad:
        if self._prev_time is None:
            self._prev_time = GameTime.get_time()
        else:
            curr_time = GameTime.get_time()
            self._time_offroad += curr_time - self._prev_time
            self._prev_time = curr_time
    else:
        self._prev_time = None
    if self._time_offroad > self._duration:
        self.test_status = 'FAILURE'
    if self._terminate_on_failure and self.test_status == 'FAILURE':
        new_status = py_trees.common.Status.FAILURE
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    return new_status

class EndofRoadTest(Criterion):
    """
    Atomic containing a test to detect when an actor has changed to a different road

    Args:
        actor (carla.Actor): CARLA actor to be used for this test
        duration (float): Time spent after ending the road before the atomic fails.
            If terminate_on_failure isn't active, this is ignored.
        optional (bool): If True, the result is not considered for an overall pass/fail result
            when using the output argument
        terminate_on_failure (bool): If True, the atomic will fail when the duration condition has been met.
    """

    def __init__(self, actor, duration=0, optional=False, terminate_on_failure=False, name='EndofRoadTest'):
        """
        Setup of the variables
        """
        super(EndofRoadTest, self).__init__(name, actor, 0, None, optional, terminate_on_failure)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._map = CarlaDataProvider.get_map()
        self._end_of_road = False
        self._duration = duration
        self._start_time = None
        self._time_end_road = 0
        self._road_id = None

    def update(self):
        """
        First, transforms the actor's current position to its corresponding waypoint. Then the road id
        is compared with the initial one and if that's the case, a time is started

        returns:
            py_trees.common.Status.FAILURE: when the actor has spent a given duration outside driving lanes
            py_trees.common.Status.RUNNING: the rest of the time
        """
        new_status = py_trees.common.Status.RUNNING
        current_location = CarlaDataProvider.get_location(self.actor)
        current_waypoint = self._map.get_waypoint(current_location)
        if self._road_id is None:
            self._road_id = current_waypoint.road_id
        elif self._road_id != current_waypoint.road_id or self._start_time:
            if self._start_time is None:
                self._start_time = GameTime.get_time()
                return new_status
            curr_time = GameTime.get_time()
            self._time_end_road = curr_time - self._start_time
            if self._time_end_road > self._duration:
                self.test_status = 'FAILURE'
                self.actual_value += 1
                return py_trees.common.Status.SUCCESS
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

def __init__(self, actor, duration=0, optional=False, terminate_on_failure=False, name='EndofRoadTest'):
    """
        Setup of the variables
        """
    super(EndofRoadTest, self).__init__(name, actor, 0, None, optional, terminate_on_failure)
    self.logger.debug('%s.__init__()' % self.__class__.__name__)
    self._map = CarlaDataProvider.get_map()
    self._end_of_road = False
    self._duration = duration
    self._start_time = None
    self._time_end_road = 0
    self._road_id = None

def update(self):
    """
        First, transforms the actor's current position to its corresponding waypoint. Then the road id
        is compared with the initial one and if that's the case, a time is started

        returns:
            py_trees.common.Status.FAILURE: when the actor has spent a given duration outside driving lanes
            py_trees.common.Status.RUNNING: the rest of the time
        """
    new_status = py_trees.common.Status.RUNNING
    current_location = CarlaDataProvider.get_location(self.actor)
    current_waypoint = self._map.get_waypoint(current_location)
    if self._road_id is None:
        self._road_id = current_waypoint.road_id
    elif self._road_id != current_waypoint.road_id or self._start_time:
        if self._start_time is None:
            self._start_time = GameTime.get_time()
            return new_status
        curr_time = GameTime.get_time()
        self._time_end_road = curr_time - self._start_time
        if self._time_end_road > self._duration:
            self.test_status = 'FAILURE'
            self.actual_value += 1
            return py_trees.common.Status.SUCCESS
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    return new_status

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

def __init__(self, actor, x, y, radius, name='InRadiusRegionTest'):
    """
        """
    super(InRadiusRegionTest, self).__init__(name, actor, 0)
    self.logger.debug('%s.__init__()' % self.__class__.__name__)
    self._actor = actor
    self._x = x
    self._y = y
    self._radius = radius

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

class VehicleLongitudinalControl(BasicControl):
    """
    Controller class for vehicles derived from BasicControl.

    The controller only controls the throttle of a vehicle, but not the steering.

    Args:
        actor (carla.Actor): Vehicle actor that should be controlled.
    """

    def __init__(self, actor, args=None):
        super(VehicleLongitudinalControl, self).__init__(actor)

    def reset(self):
        """
        Reset the controller
        """
        if self._actor and self._actor.is_alive:
            self._actor = None

    def run_step(self):
        """
        Execute on tick of the controller's control loop

        The control loop is very simplistic:
            If the actor speed is below the _target_speed, set throttle to 1.0,
            otherwise, set throttle to 0.0
        Note, that this is a longitudinal controller only.

        If _init_speed is True, the control command is post-processed to ensure that
        the initial actor velocity is maintained independent of physics.
        """
        control = self._actor.get_control()
        velocity = self._actor.get_velocity()
        current_speed = math.sqrt(velocity.x ** 2 + velocity.y ** 2)
        if current_speed < self._target_speed:
            control.throttle = 1.0
        else:
            control.throttle = 0.0
        self._actor.apply_control(control)
        if self._init_speed:
            if abs(self._target_speed - current_speed) > 3:
                yaw = self._actor.get_transform().rotation.yaw * (math.pi / 180)
                vx = math.cos(yaw) * self._target_speed
                vy = math.sin(yaw) * self._target_speed
                self._actor.set_target_velocity(carla.Vector3D(vx, vy, 0))

def __init__(self, actor, args=None):
    super(VehicleLongitudinalControl, self).__init__(actor)

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

def set_init_speed(self):
    """
        Update the actor's initial speed setting
        """
    self.control_instance.set_init_speed()

class PedestrianControl(BasicControl):
    """
    Controller class for pedestrians derived from BasicControl.

    Args:
        actor (carla.Actor): Pedestrian actor that should be controlled.
    """

    def __init__(self, actor, args=None):
        if not isinstance(actor, carla.Walker):
            raise RuntimeError('PedestrianControl: The to be controlled actor is not a pedestrian')
        super(PedestrianControl, self).__init__(actor)

    def reset(self):
        """
        Reset the controller
        """
        if self._actor and self._actor.is_alive:
            self._actor = None

    def run_step(self):
        """
        Execute on tick of the controller's control loop

        If _waypoints are provided, the pedestrian moves towards the next waypoint
        with the given _target_speed, until reaching the final waypoint. Upon reaching
        the final waypoint, _reached_goal is set to True.

        If _waypoints is empty, the pedestrians moves in its current direction with
        the given _target_speed.
        """
        if not self._actor or not self._actor.is_alive:
            return
        control = self._actor.get_control()
        control.speed = self._target_speed
        if self._waypoints:
            self._reached_goal = False
            location = self._waypoints[0].location
            direction = location - self._actor.get_location()
            direction_norm = math.sqrt(direction.x ** 2 + direction.y ** 2)
            control.direction = direction / direction_norm
            self._actor.apply_control(control)
            if direction_norm < 1.0:
                self._waypoints = self._waypoints[1:]
                if not self._waypoints:
                    self._reached_goal = True
        else:
            control.direction = self._actor.get_transform().rotation.get_forward_vector()
            self._actor.apply_control(control)

def __init__(self, actor, args=None):
    if not isinstance(actor, carla.Walker):
        raise RuntimeError('PedestrianControl: The to be controlled actor is not a pedestrian')
    super(PedestrianControl, self).__init__(actor)

def run_step(self):
    """
        Execute on tick of the controller's control loop

        If _waypoints are provided, the pedestrian moves towards the next waypoint
        with the given _target_speed, until reaching the final waypoint. Upon reaching
        the final waypoint, _reached_goal is set to True.

        If _waypoints is empty, the pedestrians moves in its current direction with
        the given _target_speed.
        """
    if not self._actor or not self._actor.is_alive:
        return
    control = self._actor.get_control()
    control.speed = self._target_speed
    if self._waypoints:
        self._reached_goal = False
        location = self._waypoints[0].location
        direction = location - self._actor.get_location()
        direction_norm = math.sqrt(direction.x ** 2 + direction.y ** 2)
        control.direction = direction / direction_norm
        self._actor.apply_control(control)
        if direction_norm < 1.0:
            self._waypoints = self._waypoints[1:]
            if not self._waypoints:
                self._reached_goal = True
    else:
        control.direction = self._actor.get_transform().rotation.get_forward_vector()
        self._actor.apply_control(control)

class NpcVehicleControl(BasicControl):
    """
    Controller class for vehicles derived from BasicControl.

    The controller makes use of the LocalPlanner implemented in CARLA.

    Args:
        actor (carla.Actor): Vehicle actor that should be controlled.
    """
    _args = {'K_P': 1.0, 'K_D': 0.01, 'K_I': 0.0, 'dt': 0.05}

    def __init__(self, actor, args=None):
        super(NpcVehicleControl, self).__init__(actor)
        self._local_planner = LocalPlanner(self._actor, opt_dict={'target_speed': self._target_speed * 3.6, 'lateral_control_dict': self._args})
        if self._waypoints:
            self._update_plan()

    def _update_plan(self):
        """
        Update the plan (waypoint list) of the LocalPlanner
        """
        plan = []
        for transform in self._waypoints:
            waypoint = CarlaDataProvider.get_map().get_waypoint(transform.location, project_to_road=True, lane_type=carla.LaneType.Any)
            plan.append((waypoint, RoadOption.LANEFOLLOW))
        self._local_planner.set_global_plan(plan)

    def reset(self):
        """
        Reset the controller
        """
        if self._actor and self._actor.is_alive:
            if self._local_planner:
                self._local_planner.reset_vehicle()
                self._local_planner = None
            self._actor = None

    def run_step(self):
        """
        Execute on tick of the controller's control loop

        If _waypoints are provided, the vehicle moves towards the next waypoint
        with the given _target_speed, until reaching the final waypoint. Upon reaching
        the final waypoint, _reached_goal is set to True.

        If _waypoints is empty, the vehicle moves in its current direction with
        the given _target_speed.

        If _init_speed is True, the control command is post-processed to ensure that
        the initial actor velocity is maintained independent of physics.
        """
        self._reached_goal = False
        if self._waypoints_updated:
            self._waypoints_updated = False
            self._update_plan()
        target_speed = self._target_speed
        self._local_planner.set_speed(target_speed * 3.6)
        control = self._local_planner.run_step(debug=False)
        if self._local_planner.done():
            self._reached_goal = True
        self._actor.apply_control(control)
        if self._init_speed:
            current_speed = math.sqrt(self._actor.get_velocity().x ** 2 + self._actor.get_velocity().y ** 2)
            if abs(target_speed - current_speed) > 3:
                yaw = self._actor.get_transform().rotation.yaw * (math.pi / 180)
                vx = math.cos(yaw) * target_speed
                vy = math.sin(yaw) * target_speed
                self._actor.set_target_velocity(carla.Vector3D(vx, vy, 0))

def __init__(self, actor, args=None):
    super(NpcVehicleControl, self).__init__(actor)
    self._local_planner = LocalPlanner(self._actor, opt_dict={'target_speed': self._target_speed * 3.6, 'lateral_control_dict': self._args})
    if self._waypoints:
        self._update_plan()

def _update_plan(self):
    """
        Update the plan (waypoint list) of the LocalPlanner
        """
    plan = []
    for transform in self._waypoints:
        waypoint = CarlaDataProvider.get_map().get_waypoint(transform.location, project_to_road=True, lane_type=carla.LaneType.Any)
        plan.append((waypoint, RoadOption.LANEFOLLOW))
    self._local_planner.set_global_plan(plan)

def reset(self):
    """
        Reset the controller
        """
    if self._actor and self._actor.is_alive:
        if self._local_planner:
            self._local_planner.reset_vehicle()
            self._local_planner = None
        self._actor = None

class ExternalControl(BasicControl):
    """
    Actor control class for actors, with externally implemented longitudinal and
    lateral controlers (e.g. Autoware).

    Args:
        actor (carla.Actor): Actor that should be controlled by the agent.
    """

    def __init__(self, actor, args=None):
        super(ExternalControl, self).__init__(actor)

    def reset(self):
        """
        Reset the controller
        """
        if self._actor and self._actor.is_alive:
            self._actor = None

    def run_step(self):
        """
        The control loop and setting the actor controls is implemented externally.
        """
        pass

def __init__(self, actor, args=None):
    super(ExternalControl, self).__init__(actor)

def get_crossing_point(actor):
    """
    Get the next crossing point location in front of the ego vehicle

    @return point of crossing
    """
    wp_cross = CarlaDataProvider.get_map().get_waypoint(actor.get_location())
    while not wp_cross.is_intersection:
        wp_cross = wp_cross.next(2)[0]
    crossing = carla.Location(x=wp_cross.transform.location.x, y=wp_cross.transform.location.y, z=wp_cross.transform.location.z)
    return crossing

def get_location_in_distance(actor, distance):
    """
    Obtain a location in a given distance from the current actor's location.
    Note: Search is stopped on first intersection.

    @return obtained location and the traveled distance
    """
    waypoint = CarlaDataProvider.get_map().get_waypoint(actor.get_location())
    traveled_distance = 0
    while not waypoint.is_intersection and traveled_distance < distance:
        waypoint_new = waypoint.next(1.0)[-1]
        traveled_distance += waypoint_new.transform.location.distance(waypoint.transform.location)
        waypoint = waypoint_new
    return (waypoint.transform.location, traveled_distance)

def get_location_in_distance_from_wp(waypoint, distance, stop_at_junction=True):
    """
    Obtain a location in a given distance from the current actor's location.
    Note: Search is stopped on first intersection.

    @return obtained location and the traveled distance
    """
    traveled_distance = 0
    while not (waypoint.is_intersection and stop_at_junction) and traveled_distance < distance:
        wp_next = waypoint.next(1.0)
        if wp_next:
            waypoint_new = wp_next[-1]
            traveled_distance += waypoint_new.transform.location.distance(waypoint.transform.location)
            waypoint = waypoint_new
        else:
            break
    return (waypoint.transform.location, traveled_distance)

def get_waypoint_in_distance(waypoint, distance):
    """
    Obtain a waypoint in a given distance from the current actor's location.
    Note: Search is stopped on first intersection.
    @return obtained waypoint and the traveled distance
    """
    traveled_distance = 0
    while not waypoint.is_intersection and traveled_distance < distance:
        waypoint_new = waypoint.next(1.0)[-1]
        traveled_distance += waypoint_new.transform.location.distance(waypoint.transform.location)
        waypoint = waypoint_new
    return (waypoint, traveled_distance)

def interpolate_trajectory(world, waypoints_trajectory, hop_resolution=1.0):
    """
        Given some raw keypoints interpolate a full dense trajectory to be used by the user.
    :param world: an reference to the CARLA world so we can use the planner
    :param waypoints_trajectory: the current coarse trajectory
    :param hop_resolution: is the resolution, how dense is the provided trajectory going to be made
    :return: the full interpolated route both in GPS coordinates and also in its original form.
    """
    dao = GlobalRoutePlannerDAO(world.get_map(), hop_resolution)
    grp = GlobalRoutePlanner(dao)
    grp.setup()
    route = []
    for i in range(len(waypoints_trajectory) - 1):
        waypoint = waypoints_trajectory[i]
        waypoint_next = waypoints_trajectory[i + 1]
        interpolated_trace = grp.trace_route(waypoint, waypoint_next)
        for wp_tuple in interpolated_trace:
            route.append((wp_tuple[0].transform, wp_tuple[1]))
    lat_ref, lon_ref = _get_latlon_ref(world)
    return (location_route_to_gps(route, lat_ref, lon_ref), route)

class Decorator(py_trees.behaviour.Behaviour):
    """
    A decorator is responsible for handling the lifecycle of a single
    child beneath

    This is taken from py_trees 1.2 to work with our current implementation
    that uses py_trees 0.8.2
    """

    def __init__(self, child, name):
        """
        Common initialisation steps for a decorator - type checks and
        name construction (if None is given).
        Args:
            name (:obj:`str`): the decorator name
            child (:class:`~py_trees.behaviour.Behaviour`): the child to be decorated
        Raises:
            TypeError: if the child is not an instance of :class:`~py_trees.behaviour.Behaviour`
        """
        if not isinstance(child, py_trees.behaviour.Behaviour):
            raise TypeError("A decorator's child must be an instance of py_trees.behaviours.Behaviour")
        super(Decorator, self).__init__(name=name)
        self.children.append(child)
        self.decorated = self.children[0]
        self.decorated.parent = self

    def tick(self):
        """
        A decorator's tick is exactly the same as a normal proceedings for
        a Behaviour's tick except that it also ticks the decorated child node.
        Yields:
            :class:`~py_trees.behaviour.Behaviour`: a reference to itself or one of its children
        """
        self.logger.debug('%s.tick()' % self.__class__.__name__)
        if self.status != py_trees.common.Status.RUNNING:
            self.initialise()
        for node in self.decorated.tick():
            yield node
        new_status = self.update()
        if new_status not in list(py_trees.common.Status):
            self.logger.error('A behaviour returned an invalid status, setting to INVALID [%s][%s]' % (new_status, self.name))
            new_status = py_trees.common.Status.INVALID
        if new_status != py_trees.common.Status.RUNNING:
            self.stop(new_status)
        self.status = new_status
        yield self

    def stop(self, new_status=py_trees.common.Status.INVALID):
        """
        As with other composites, it checks if the child is running
        and stops it if that is the case.
        Args:
            new_status (:class:`~py_trees.common.Status`): the behaviour is transitioning to this new status
        """
        self.logger.debug('%s.stop(%s)' % (self.__class__.__name__, new_status))
        self.terminate(new_status)
        if new_status == py_trees.common.Status.INVALID:
            self.decorated.stop(new_status)
        if self.decorated.status == py_trees.common.Status.RUNNING:
            self.decorated.stop(py_trees.common.Status.INVALID)
        self.status = new_status

    def tip(self):
        """
        Get the *tip* of this behaviour's subtree (if it has one) after it's last
        tick. This corresponds to the the deepest node that was running before the
        subtree traversal reversed direction and headed back to this node.
        """
        if self.decorated.status != py_trees.common.Status.INVALID:
            return self.decorated.tip()
        return super(Decorator, self).tip()

def __init__(self, child, name):
    """
        Common initialisation steps for a decorator - type checks and
        name construction (if None is given).
        Args:
            name (:obj:`str`): the decorator name
            child (:class:`~py_trees.behaviour.Behaviour`): the child to be decorated
        Raises:
            TypeError: if the child is not an instance of :class:`~py_trees.behaviour.Behaviour`
        """
    if not isinstance(child, py_trees.behaviour.Behaviour):
        raise TypeError("A decorator's child must be an instance of py_trees.behaviours.Behaviour")
    super(Decorator, self).__init__(name=name)
    self.children.append(child)
    self.decorated = self.children[0]
    self.decorated.parent = self

def tip(self):
    """
        Get the *tip* of this behaviour's subtree (if it has one) after it's last
        tick. This corresponds to the the deepest node that was running before the
        subtree traversal reversed direction and headed back to this node.
        """
    if self.decorated.status != py_trees.common.Status.INVALID:
        return self.decorated.tip()
    return super(Decorator, self).tip()

class SensorInterface(object):
    """
    Class that contains all sensor data
    """

    def __init__(self):
        """
        Initializes the class
        """
        self._sensors_objects = {}
        self._data_buffers = {}
        self._timestamps = {}

    def register_sensor(self, tag, sensor):
        """
        Registers the sensors
        """
        if tag in self._sensors_objects:
            raise ValueError('Duplicated sensor tag [{}]'.format(tag))
        self._sensors_objects[tag] = sensor
        self._data_buffers[tag] = None
        self._timestamps[tag] = -1

    def update_sensor(self, tag, data, timestamp):
        """
        Updates the sensor
        """
        if tag not in self._sensors_objects:
            raise ValueError('The sensor with tag [{}] has not been created!'.format(tag))
        self._data_buffers[tag] = data
        self._timestamps[tag] = timestamp

    def all_sensors_ready(self):
        """
        Checks if all the sensors have sent data at least once
        """
        for key in self._sensors_objects:
            if self._data_buffers[key] is None:
                return False
        return True

    def get_data(self):
        """
        Returns the data of a sensor
        """
        data_dict = {}
        for key in self._sensors_objects:
            data_dict[key] = (self._timestamps[key], self._data_buffers[key])
        return data_dict

def register_sensor(self, tag, sensor):
    """
        Registers the sensors
        """
    if tag in self._sensors_objects:
        raise ValueError('Duplicated sensor tag [{}]'.format(tag))
    self._sensors_objects[tag] = sensor
    self._data_buffers[tag] = None
    self._timestamps[tag] = -1

def update_sensor(self, tag, data, timestamp):
    """
        Updates the sensor
        """
    if tag not in self._sensors_objects:
        raise ValueError('The sensor with tag [{}] has not been created!'.format(tag))
    self._data_buffers[tag] = data
    self._timestamps[tag] = timestamp

class NpcAgent(AutonomousAgent):
    """
    NPC autonomous agent to control the ego vehicle
    """
    _agent = None
    _route_assigned = False

    def setup(self, path_to_conf_file):
        """
        Setup the agent parameters
        """
        self._route_assigned = False
        self._agent = None

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


        """
        sensors = [{'type': 'sensor.camera.rgb', 'x': 0.7, 'y': -0.4, 'z': 1.6, 'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0, 'width': 300, 'height': 200, 'fov': 100, 'id': 'Left'}]
        return sensors

    def run_step(self, input_data, timestamp):
        """
        Execute one step of navigation.
        """
        control = carla.VehicleControl()
        control.steer = 0.0
        control.throttle = 0.0
        control.brake = 0.0
        control.hand_brake = False
        if not self._agent:
            hero_actor = None
            for actor in CarlaDataProvider.get_world().get_actors():
                if 'role_name' in actor.attributes and actor.attributes['role_name'] == 'hero':
                    hero_actor = actor
                    break
            if hero_actor:
                self._agent = BasicAgent(hero_actor)
            return control
        if not self._route_assigned:
            if self._global_plan:
                plan = []
                for transform, road_option in self._global_plan_world_coord:
                    wp = CarlaDataProvider.get_map().get_waypoint(transform.location)
                    plan.append((wp, road_option))
                self._agent._local_planner.set_global_plan(plan)
                self._route_assigned = True
        else:
            control = self._agent.run_step()
        return control

def run_step(self, input_data, timestamp):
    """
        Execute one step of navigation.
        """
    control = carla.VehicleControl()
    control.steer = 0.0
    control.throttle = 0.0
    control.brake = 0.0
    control.hand_brake = False
    if not self._agent:
        hero_actor = None
        for actor in CarlaDataProvider.get_world().get_actors():
            if 'role_name' in actor.attributes and actor.attributes['role_name'] == 'hero':
                hero_actor = actor
                break
        if hero_actor:
            self._agent = BasicAgent(hero_actor)
        return control
    if not self._route_assigned:
        if self._global_plan:
            plan = []
            for transform, road_option in self._global_plan_world_coord:
                wp = CarlaDataProvider.get_map().get_waypoint(transform.location)
                plan.append((wp, road_option))
            self._agent._local_planner.set_global_plan(plan)
            self._route_assigned = True
    else:
        control = self._agent.run_step()
    return control

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

def __init__(self, path_to_conf_file):
    self._global_plan = None
    self._global_plan_world_coord = None
    self.sensor_interface = SensorInterface()
    self.setup(path_to_conf_file)

def interpolate_trajectory(world_map, waypoints_trajectory, hop_resolution=1.0):
    """
    Given some raw keypoints interpolate a full dense trajectory to be used by the user.
    Args:
        world: an reference to the CARLA world so we can use the planner
        waypoints_trajectory: the current coarse trajectory
        hop_resolution: is the resolution, how dense is the provided trajectory going to be made
    Return: 
        route: full interpolated route both in GPS coordinates and also in its original form.
    """
    dao = GlobalRoutePlannerDAO(world_map, hop_resolution)
    grp = GlobalRoutePlanner(dao)
    grp.setup()
    route = []
    for i in range(len(waypoints_trajectory) - 1):
        waypoint = waypoints_trajectory[i]
        waypoint_next = waypoints_trajectory[i + 1]
        interpolated_trace = grp.trace_route(waypoint, waypoint_next)
        for wp_tuple in interpolated_trace:
            route.append((wp_tuple[0].transform, wp_tuple[1]))
    return route

def interpolate_trajectory(world_map, waypoints_trajectory, hop_resolution=1.0, max_len=100):
    """
    Given some raw keypoints interpolate a full dense trajectory to be used by the user.
    returns the full interpolated route both in GPS coordinates and also in its original form.
    
    Args:
        - world: an reference to the CARLA world so we can use the planner
        - waypoints_trajectory: the current coarse trajectory
        - hop_resolution: is the resolution, how dense is the provided trajectory going to be made
    """
    dao = GlobalRoutePlannerDAO(world_map, hop_resolution)
    grp = GlobalRoutePlanner(dao)
    grp.setup()
    route = []
    for i in range(len(waypoints_trajectory) - 1):
        waypoint = waypoints_trajectory[i]
        waypoint_next = waypoints_trajectory[i + 1]
        if waypoint.x != waypoint_next.x or waypoint.y != waypoint_next.y:
            interpolated_trace = grp.trace_route(waypoint, waypoint_next)
            if len(interpolated_trace) > max_len:
                waypoints_trajectory[i + 1] = waypoints_trajectory[i]
            else:
                for wp_tuple in interpolated_trace:
                    route.append((wp_tuple[0].transform, wp_tuple[1]))
    lat_ref, lon_ref = _get_latlon_ref(world_map)
    return (location_route_to_gps(route, lat_ref, lon_ref), route)

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

class TransfuserBackbone(nn.Module):
    """
    Multi-scale Fusion Transformer for image + LiDAR feature fusion
    image_architecture: Architecture used in the image branch. ResNet, RegNet and ConvNext are supported
    lidar_architecture: Architecture used in the lidar branch. ResNet, RegNet and ConvNext are supported
    use_velocity: Whether to use the velocity input in the transformer.
    """

    def __init__(self, config, image_architecture='resnet34', lidar_architecture='resnet18', use_velocity=True):
        super().__init__()
        self.config = config
        self.avgpool_img = nn.AdaptiveAvgPool2d((self.config.img_vert_anchors, self.config.img_horz_anchors))
        self.avgpool_lidar = nn.AdaptiveAvgPool2d((self.config.lidar_vert_anchors, self.config.lidar_horz_anchors))
        self.image_encoder = ImageCNN(architecture=image_architecture, normalize=True, out_features=self.config.perception_output_features)
        if config.use_point_pillars == True:
            in_channels = config.num_features[-1]
        else:
            in_channels = 2 * config.lidar_seq_len
        if self.config.use_target_point_image == True:
            in_channels += 1
        self.lidar_encoder = LidarEncoder(architecture=lidar_architecture, in_channels=in_channels, out_features=self.config.perception_output_features)
        self.transformer1 = GPT(n_embd=self.image_encoder.features.feature_info[1]['num_chs'], n_head=config.n_head, block_exp=config.block_exp, n_layer=config.n_layer, img_vert_anchors=config.img_vert_anchors, img_horz_anchors=config.img_horz_anchors, lidar_vert_anchors=config.lidar_vert_anchors, lidar_horz_anchors=config.lidar_horz_anchors, seq_len=config.seq_len, embd_pdrop=config.embd_pdrop, attn_pdrop=config.attn_pdrop, resid_pdrop=config.resid_pdrop, config=config, use_velocity=use_velocity)
        self.transformer2 = GPT(n_embd=self.image_encoder.features.feature_info[2]['num_chs'], n_head=config.n_head, block_exp=config.block_exp, n_layer=config.n_layer, img_vert_anchors=config.img_vert_anchors, img_horz_anchors=config.img_horz_anchors, lidar_vert_anchors=config.lidar_vert_anchors, lidar_horz_anchors=config.lidar_horz_anchors, seq_len=config.seq_len, embd_pdrop=config.embd_pdrop, attn_pdrop=config.attn_pdrop, resid_pdrop=config.resid_pdrop, config=config, use_velocity=use_velocity)
        self.transformer3 = GPT(n_embd=self.image_encoder.features.feature_info[3]['num_chs'], n_head=config.n_head, block_exp=config.block_exp, n_layer=config.n_layer, img_vert_anchors=config.img_vert_anchors, img_horz_anchors=config.img_horz_anchors, lidar_vert_anchors=config.lidar_vert_anchors, lidar_horz_anchors=config.lidar_horz_anchors, seq_len=config.seq_len, embd_pdrop=config.embd_pdrop, attn_pdrop=config.attn_pdrop, resid_pdrop=config.resid_pdrop, config=config, use_velocity=use_velocity)
        self.transformer4 = GPT(n_embd=self.image_encoder.features.feature_info[4]['num_chs'], n_head=config.n_head, block_exp=config.block_exp, n_layer=config.n_layer, img_vert_anchors=config.img_vert_anchors, img_horz_anchors=config.img_horz_anchors, lidar_vert_anchors=config.lidar_vert_anchors, lidar_horz_anchors=config.lidar_horz_anchors, seq_len=config.seq_len, embd_pdrop=config.embd_pdrop, attn_pdrop=config.attn_pdrop, resid_pdrop=config.resid_pdrop, config=config, use_velocity=use_velocity)
        if self.image_encoder.features.feature_info[4]['num_chs'] != self.config.perception_output_features:
            self.change_channel_conv_image = nn.Conv2d(self.image_encoder.features.feature_info[4]['num_chs'], self.config.perception_output_features, (1, 1))
            self.change_channel_conv_lidar = nn.Conv2d(self.image_encoder.features.feature_info[4]['num_chs'], self.config.perception_output_features, (1, 1))
        else:
            self.change_channel_conv_image = nn.Sequential()
            self.change_channel_conv_lidar = nn.Sequential()
        channel = self.config.bev_features_chanels
        self.relu = nn.ReLU(inplace=True)
        self.upsample = nn.Upsample(scale_factor=self.config.bev_upsample_factor, mode='bilinear', align_corners=False)
        self.up_conv5 = nn.Conv2d(channel, channel, (1, 1))
        self.up_conv4 = nn.Conv2d(channel, channel, (1, 1))
        self.up_conv3 = nn.Conv2d(channel, channel, (1, 1))
        self.c5_conv = nn.Conv2d(self.config.perception_output_features, channel, (1, 1))

    def top_down(self, x):
        p5 = self.relu(self.c5_conv(x))
        p4 = self.relu(self.up_conv5(self.upsample(p5)))
        p3 = self.relu(self.up_conv4(self.upsample(p4)))
        p2 = self.relu(self.up_conv3(self.upsample(p3)))
        return (p2, p3, p4, p5)

    def forward(self, image, lidar, velocity):
        """
        Image + LiDAR feature fusion using transformers
        Args:
            image_list (list): list of input images
            lidar_list (list): list of input LiDAR BEV
            velocity (tensor): input velocity from speedometer
        """
        if self.image_encoder.normalize:
            image_tensor = normalize_imagenet(image)
        else:
            image_tensor = image
        lidar_tensor = lidar
        image_features = self.image_encoder.features.conv1(image_tensor)
        image_features = self.image_encoder.features.bn1(image_features)
        image_features = self.image_encoder.features.act1(image_features)
        image_features = self.image_encoder.features.maxpool(image_features)
        lidar_features = self.lidar_encoder._model.conv1(lidar_tensor)
        lidar_features = self.lidar_encoder._model.bn1(lidar_features)
        lidar_features = self.lidar_encoder._model.act1(lidar_features)
        lidar_features = self.lidar_encoder._model.maxpool(lidar_features)
        image_features = self.image_encoder.features.layer1(image_features)
        lidar_features = self.lidar_encoder._model.layer1(lidar_features)
        image_embd_layer1 = self.avgpool_img(image_features)
        lidar_embd_layer1 = self.avgpool_lidar(lidar_features)
        image_features_layer1, lidar_features_layer1 = self.transformer1(image_embd_layer1, lidar_embd_layer1, velocity)
        image_features_layer1 = F.interpolate(image_features_layer1, size=(image_features.shape[2], image_features.shape[3]), mode='bilinear', align_corners=False)
        lidar_features_layer1 = F.interpolate(lidar_features_layer1, size=(lidar_features.shape[2], lidar_features.shape[3]), mode='bilinear', align_corners=False)
        image_features = image_features + image_features_layer1
        lidar_features = lidar_features + lidar_features_layer1
        image_features = self.image_encoder.features.layer2(image_features)
        lidar_features = self.lidar_encoder._model.layer2(lidar_features)
        image_embd_layer2 = self.avgpool_img(image_features)
        lidar_embd_layer2 = self.avgpool_lidar(lidar_features)
        image_features_layer2, lidar_features_layer2 = self.transformer2(image_embd_layer2, lidar_embd_layer2, velocity)
        image_features_layer2 = F.interpolate(image_features_layer2, size=(image_features.shape[2], image_features.shape[3]), mode='bilinear', align_corners=False)
        lidar_features_layer2 = F.interpolate(lidar_features_layer2, size=(lidar_features.shape[2], lidar_features.shape[3]), mode='bilinear', align_corners=False)
        image_features = image_features + image_features_layer2
        lidar_features = lidar_features + lidar_features_layer2
        image_features = self.image_encoder.features.layer3(image_features)
        lidar_features = self.lidar_encoder._model.layer3(lidar_features)
        image_embd_layer3 = self.avgpool_img(image_features)
        lidar_embd_layer3 = self.avgpool_lidar(lidar_features)
        image_features_layer3, lidar_features_layer3 = self.transformer3(image_embd_layer3, lidar_embd_layer3, velocity)
        image_features_layer3 = F.interpolate(image_features_layer3, size=(image_features.shape[2], image_features.shape[3]), mode='bilinear', align_corners=False)
        lidar_features_layer3 = F.interpolate(lidar_features_layer3, size=(lidar_features.shape[2], lidar_features.shape[3]), mode='bilinear', align_corners=False)
        image_features = image_features + image_features_layer3
        lidar_features = lidar_features + lidar_features_layer3
        image_features = self.image_encoder.features.layer4(image_features)
        lidar_features = self.lidar_encoder._model.layer4(lidar_features)
        image_embd_layer4 = self.avgpool_img(image_features)
        lidar_embd_layer4 = self.avgpool_lidar(lidar_features)
        image_features_layer4, lidar_features_layer4 = self.transformer4(image_embd_layer4, lidar_embd_layer4, velocity)
        image_features_layer4 = F.interpolate(image_features_layer4, size=(image_features.shape[2], image_features.shape[3]), mode='bilinear', align_corners=False)
        lidar_features_layer4 = F.interpolate(lidar_features_layer4, size=(lidar_features.shape[2], lidar_features.shape[3]), mode='bilinear', align_corners=False)
        image_features = image_features + image_features_layer4
        lidar_features = lidar_features + lidar_features_layer4
        image_features = self.change_channel_conv_image(image_features)
        lidar_features = self.change_channel_conv_lidar(lidar_features)
        x4 = lidar_features
        image_features_grid = image_features
        image_features = self.image_encoder.features.global_pool(image_features)
        image_features = torch.flatten(image_features, 1)
        lidar_features = self.lidar_encoder._model.global_pool(lidar_features)
        lidar_features = torch.flatten(lidar_features, 1)
        fused_features = image_features + lidar_features
        features = self.top_down(x4)
        return (features, image_features_grid, fused_features)

def __init__(self, config, image_architecture='resnet34', lidar_architecture='resnet18', use_velocity=True):
    super().__init__()
    self.config = config
    self.avgpool_img = nn.AdaptiveAvgPool2d((self.config.img_vert_anchors, self.config.img_horz_anchors))
    self.avgpool_lidar = nn.AdaptiveAvgPool2d((self.config.lidar_vert_anchors, self.config.lidar_horz_anchors))
    self.image_encoder = ImageCNN(architecture=image_architecture, normalize=True, out_features=self.config.perception_output_features)
    if config.use_point_pillars == True:
        in_channels = config.num_features[-1]
    else:
        in_channels = 2 * config.lidar_seq_len
    if self.config.use_target_point_image == True:
        in_channels += 1
    self.lidar_encoder = LidarEncoder(architecture=lidar_architecture, in_channels=in_channels, out_features=self.config.perception_output_features)
    self.transformer1 = GPT(n_embd=self.image_encoder.features.feature_info[1]['num_chs'], n_head=config.n_head, block_exp=config.block_exp, n_layer=config.n_layer, img_vert_anchors=config.img_vert_anchors, img_horz_anchors=config.img_horz_anchors, lidar_vert_anchors=config.lidar_vert_anchors, lidar_horz_anchors=config.lidar_horz_anchors, seq_len=config.seq_len, embd_pdrop=config.embd_pdrop, attn_pdrop=config.attn_pdrop, resid_pdrop=config.resid_pdrop, config=config, use_velocity=use_velocity)
    self.transformer2 = GPT(n_embd=self.image_encoder.features.feature_info[2]['num_chs'], n_head=config.n_head, block_exp=config.block_exp, n_layer=config.n_layer, img_vert_anchors=config.img_vert_anchors, img_horz_anchors=config.img_horz_anchors, lidar_vert_anchors=config.lidar_vert_anchors, lidar_horz_anchors=config.lidar_horz_anchors, seq_len=config.seq_len, embd_pdrop=config.embd_pdrop, attn_pdrop=config.attn_pdrop, resid_pdrop=config.resid_pdrop, config=config, use_velocity=use_velocity)
    self.transformer3 = GPT(n_embd=self.image_encoder.features.feature_info[3]['num_chs'], n_head=config.n_head, block_exp=config.block_exp, n_layer=config.n_layer, img_vert_anchors=config.img_vert_anchors, img_horz_anchors=config.img_horz_anchors, lidar_vert_anchors=config.lidar_vert_anchors, lidar_horz_anchors=config.lidar_horz_anchors, seq_len=config.seq_len, embd_pdrop=config.embd_pdrop, attn_pdrop=config.attn_pdrop, resid_pdrop=config.resid_pdrop, config=config, use_velocity=use_velocity)
    self.transformer4 = GPT(n_embd=self.image_encoder.features.feature_info[4]['num_chs'], n_head=config.n_head, block_exp=config.block_exp, n_layer=config.n_layer, img_vert_anchors=config.img_vert_anchors, img_horz_anchors=config.img_horz_anchors, lidar_vert_anchors=config.lidar_vert_anchors, lidar_horz_anchors=config.lidar_horz_anchors, seq_len=config.seq_len, embd_pdrop=config.embd_pdrop, attn_pdrop=config.attn_pdrop, resid_pdrop=config.resid_pdrop, config=config, use_velocity=use_velocity)
    if self.image_encoder.features.feature_info[4]['num_chs'] != self.config.perception_output_features:
        self.change_channel_conv_image = nn.Conv2d(self.image_encoder.features.feature_info[4]['num_chs'], self.config.perception_output_features, (1, 1))
        self.change_channel_conv_lidar = nn.Conv2d(self.image_encoder.features.feature_info[4]['num_chs'], self.config.perception_output_features, (1, 1))
    else:
        self.change_channel_conv_image = nn.Sequential()
        self.change_channel_conv_lidar = nn.Sequential()
    channel = self.config.bev_features_chanels
    self.relu = nn.ReLU(inplace=True)
    self.upsample = nn.Upsample(scale_factor=self.config.bev_upsample_factor, mode='bilinear', align_corners=False)
    self.up_conv5 = nn.Conv2d(channel, channel, (1, 1))
    self.up_conv4 = nn.Conv2d(channel, channel, (1, 1))
    self.up_conv3 = nn.Conv2d(channel, channel, (1, 1))
    self.c5_conv = nn.Conv2d(self.config.perception_output_features, channel, (1, 1))

class SegDecoder(nn.Module):

    def __init__(self, config, latent_dim=512):
        super().__init__()
        self.config = config
        self.latent_dim = latent_dim
        self.num_class = config.num_class
        self.deconv1 = nn.Sequential(nn.Conv2d(self.latent_dim, self.config.deconv_channel_num_1, 3, 1, 1), nn.ReLU(True), nn.Conv2d(self.config.deconv_channel_num_1, self.config.deconv_channel_num_2, 3, 1, 1), nn.ReLU(True))
        self.deconv2 = nn.Sequential(nn.Conv2d(self.config.deconv_channel_num_2, self.config.deconv_channel_num_3, 3, 1, 1), nn.ReLU(True), nn.Conv2d(self.config.deconv_channel_num_3, self.config.deconv_channel_num_3, 3, 1, 1), nn.ReLU(True))
        self.deconv3 = nn.Sequential(nn.Conv2d(self.config.deconv_channel_num_3, self.config.deconv_channel_num_3, 3, 1, 1), nn.ReLU(True), nn.Conv2d(self.config.deconv_channel_num_3, self.num_class, 3, 1, 1))

    def forward(self, x):
        x = self.deconv1(x)
        x = F.interpolate(x, scale_factor=self.config.deconv_scale_factor_1, mode='bilinear', align_corners=False)
        x = self.deconv2(x)
        x = F.interpolate(x, scale_factor=self.config.deconv_scale_factor_2, mode='bilinear', align_corners=False)
        x = self.deconv3(x)
        return x

def __init__(self, config, latent_dim=512):
    super().__init__()
    self.config = config
    self.latent_dim = latent_dim
    self.num_class = config.num_class
    self.deconv1 = nn.Sequential(nn.Conv2d(self.latent_dim, self.config.deconv_channel_num_1, 3, 1, 1), nn.ReLU(True), nn.Conv2d(self.config.deconv_channel_num_1, self.config.deconv_channel_num_2, 3, 1, 1), nn.ReLU(True))
    self.deconv2 = nn.Sequential(nn.Conv2d(self.config.deconv_channel_num_2, self.config.deconv_channel_num_3, 3, 1, 1), nn.ReLU(True), nn.Conv2d(self.config.deconv_channel_num_3, self.config.deconv_channel_num_3, 3, 1, 1), nn.ReLU(True))
    self.deconv3 = nn.Sequential(nn.Conv2d(self.config.deconv_channel_num_3, self.config.deconv_channel_num_3, 3, 1, 1), nn.ReLU(True), nn.Conv2d(self.config.deconv_channel_num_3, self.num_class, 3, 1, 1))

class DepthDecoder(nn.Module):

    def __init__(self, config, latent_dim=512):
        super().__init__()
        self.config = config
        self.latent_dim = latent_dim
        self.deconv1 = nn.Sequential(nn.Conv2d(self.latent_dim, self.config.deconv_channel_num_1, 3, 1, 1), nn.ReLU(True), nn.Conv2d(self.config.deconv_channel_num_1, self.config.deconv_channel_num_2, 3, 1, 1), nn.ReLU(True))
        self.deconv2 = nn.Sequential(nn.Conv2d(self.config.deconv_channel_num_2, self.config.deconv_channel_num_3, 3, 1, 1), nn.ReLU(True), nn.Conv2d(self.config.deconv_channel_num_3, self.config.deconv_channel_num_3, 3, 1, 1), nn.ReLU(True))
        self.deconv3 = nn.Sequential(nn.Conv2d(self.config.deconv_channel_num_3, self.config.deconv_channel_num_3, 3, 1, 1), nn.ReLU(True), nn.Conv2d(self.config.deconv_channel_num_3, 1, 3, 1, 1))

    def forward(self, x):
        x = self.deconv1(x)
        x = F.interpolate(x, scale_factor=self.config.deconv_scale_factor_1, mode='bilinear', align_corners=False)
        x = self.deconv2(x)
        x = F.interpolate(x, scale_factor=self.config.deconv_scale_factor_2, mode='bilinear', align_corners=False)
        x = self.deconv3(x)
        x = torch.sigmoid(x).squeeze(1)
        return x

def __init__(self, config, latent_dim=512):
    super().__init__()
    self.config = config
    self.latent_dim = latent_dim
    self.deconv1 = nn.Sequential(nn.Conv2d(self.latent_dim, self.config.deconv_channel_num_1, 3, 1, 1), nn.ReLU(True), nn.Conv2d(self.config.deconv_channel_num_1, self.config.deconv_channel_num_2, 3, 1, 1), nn.ReLU(True))
    self.deconv2 = nn.Sequential(nn.Conv2d(self.config.deconv_channel_num_2, self.config.deconv_channel_num_3, 3, 1, 1), nn.ReLU(True), nn.Conv2d(self.config.deconv_channel_num_3, self.config.deconv_channel_num_3, 3, 1, 1), nn.ReLU(True))
    self.deconv3 = nn.Sequential(nn.Conv2d(self.config.deconv_channel_num_3, self.config.deconv_channel_num_3, 3, 1, 1), nn.ReLU(True), nn.Conv2d(self.config.deconv_channel_num_3, 1, 3, 1, 1))

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

class ImageCNN(nn.Module):
    """ 
    Encoder network for image input list.
    Args:
        architecture (string): Vision architecture to be used from the TIMM model library.
        normalize (bool): whether the input images should be normalized
    """

    def __init__(self, architecture, normalize=True, out_features=512):
        super().__init__()
        self.normalize = normalize
        self.features = timm.create_model(architecture, pretrained=True)
        self.features.fc = None
        if architecture.startswith('regnet'):
            self.features.conv1 = self.features.stem.conv
            self.features.bn1 = self.features.stem.bn
            self.features.act1 = nn.Sequential()
            self.features.maxpool = nn.Sequential()
            self.features.layer1 = self.features.s1
            self.features.layer2 = self.features.s2
            self.features.layer3 = self.features.s3
            self.features.layer4 = self.features.s4
            self.features.global_pool = nn.AdaptiveAvgPool2d(output_size=1)
            self.features.head = nn.Sequential()
        elif architecture.startswith('convnext'):
            self.features.conv1 = self.features.stem._modules['0']
            self.features.bn1 = self.features.stem._modules['1']
            self.features.act1 = nn.Sequential()
            self.features.maxpool = nn.Sequential()
            self.features.layer1 = self.features.stages._modules['0']
            self.features.layer2 = self.features.stages._modules['1']
            self.features.layer3 = self.features.stages._modules['2']
            self.features.layer4 = self.features.stages._modules['3']
            self.features.global_pool = self.features.head
            self.features.global_pool.flatten = nn.Sequential()
            self.features.global_pool.fc = nn.Sequential()
            self.features.head = nn.Sequential()
            self.features.feature_info.append(self.features.feature_info[3])
            self.features.feature_info[3] = self.features.feature_info[2]
            self.features.feature_info[2] = self.features.feature_info[1]
            self.features.feature_info[1] = self.features.feature_info[0]
            _tmp = self.features.global_pool.norm
            self.features.global_pool.norm = nn.LayerNorm((out_features, 1, 1), _tmp.eps, _tmp.elementwise_affine)

def __init__(self, architecture, normalize=True, out_features=512):
    super().__init__()
    self.normalize = normalize
    self.features = timm.create_model(architecture, pretrained=True)
    self.features.fc = None
    if architecture.startswith('regnet'):
        self.features.conv1 = self.features.stem.conv
        self.features.bn1 = self.features.stem.bn
        self.features.act1 = nn.Sequential()
        self.features.maxpool = nn.Sequential()
        self.features.layer1 = self.features.s1
        self.features.layer2 = self.features.s2
        self.features.layer3 = self.features.s3
        self.features.layer4 = self.features.s4
        self.features.global_pool = nn.AdaptiveAvgPool2d(output_size=1)
        self.features.head = nn.Sequential()
    elif architecture.startswith('convnext'):
        self.features.conv1 = self.features.stem._modules['0']
        self.features.bn1 = self.features.stem._modules['1']
        self.features.act1 = nn.Sequential()
        self.features.maxpool = nn.Sequential()
        self.features.layer1 = self.features.stages._modules['0']
        self.features.layer2 = self.features.stages._modules['1']
        self.features.layer3 = self.features.stages._modules['2']
        self.features.layer4 = self.features.stages._modules['3']
        self.features.global_pool = self.features.head
        self.features.global_pool.flatten = nn.Sequential()
        self.features.global_pool.fc = nn.Sequential()
        self.features.head = nn.Sequential()
        self.features.feature_info.append(self.features.feature_info[3])
        self.features.feature_info[3] = self.features.feature_info[2]
        self.features.feature_info[2] = self.features.feature_info[1]
        self.features.feature_info[1] = self.features.feature_info[0]
        _tmp = self.features.global_pool.norm
        self.features.global_pool.norm = nn.LayerNorm((out_features, 1, 1), _tmp.eps, _tmp.elementwise_affine)

class LidarEncoder(nn.Module):
    """
    Encoder network for LiDAR input list
    Args:
        architecture (string): Vision architecture to be used from the TIMM model library.
        in_channels: input channels
    """

    def __init__(self, architecture, in_channels=2, out_features=512):
        super().__init__()
        self._model = timm.create_model(architecture, pretrained=False)
        self._model.fc = None
        if architecture.startswith('regnet'):
            self._model.conv1 = self._model.stem.conv
            self._model.bn1 = self._model.stem.bn
            self._model.act1 = nn.Sequential()
            self._model.maxpool = nn.Sequential()
            self._model.layer1 = self._model.s1
            self._model.layer2 = self._model.s2
            self._model.layer3 = self._model.s3
            self._model.layer4 = self._model.s4
            self._model.global_pool = nn.AdaptiveAvgPool2d(output_size=1)
            self._model.head = nn.Sequential()
        elif architecture.startswith('convnext'):
            self._model.conv1 = self._model.stem._modules['0']
            self._model.bn1 = self._model.stem._modules['1']
            self._model.act1 = nn.Sequential()
            self._model.maxpool = nn.Sequential()
            self._model.layer1 = self._model.stages._modules['0']
            self._model.layer2 = self._model.stages._modules['1']
            self._model.layer3 = self._model.stages._modules['2']
            self._model.layer4 = self._model.stages._modules['3']
            self._model.global_pool = self._model.head
            self._model.global_pool.flatten = nn.Sequential()
            self._model.global_pool.fc = nn.Sequential()
            self._model.head = nn.Sequential()
            _tmp = self._model.global_pool.norm
            self._model.global_pool.norm = nn.LayerNorm((out_features, 1, 1), _tmp.eps, _tmp.elementwise_affine)
        _tmp = self._model.conv1
        use_bias = _tmp.bias != None
        self._model.conv1 = nn.Conv2d(in_channels, out_channels=_tmp.out_channels, kernel_size=_tmp.kernel_size, stride=_tmp.stride, padding=_tmp.padding, bias=use_bias)
        if architecture.startswith('convnext'):
            del self._model.stem._modules['0']
        elif architecture.startswith('regnet'):
            del self._model.stem.conv
        torch.cuda.empty_cache()
        if use_bias:
            self._model.conv1.bias = _tmp.bias
        del _tmp

def __init__(self, architecture, in_channels=2, out_features=512):
    super().__init__()
    self._model = timm.create_model(architecture, pretrained=False)
    self._model.fc = None
    if architecture.startswith('regnet'):
        self._model.conv1 = self._model.stem.conv
        self._model.bn1 = self._model.stem.bn
        self._model.act1 = nn.Sequential()
        self._model.maxpool = nn.Sequential()
        self._model.layer1 = self._model.s1
        self._model.layer2 = self._model.s2
        self._model.layer3 = self._model.s3
        self._model.layer4 = self._model.s4
        self._model.global_pool = nn.AdaptiveAvgPool2d(output_size=1)
        self._model.head = nn.Sequential()
    elif architecture.startswith('convnext'):
        self._model.conv1 = self._model.stem._modules['0']
        self._model.bn1 = self._model.stem._modules['1']
        self._model.act1 = nn.Sequential()
        self._model.maxpool = nn.Sequential()
        self._model.layer1 = self._model.stages._modules['0']
        self._model.layer2 = self._model.stages._modules['1']
        self._model.layer3 = self._model.stages._modules['2']
        self._model.layer4 = self._model.stages._modules['3']
        self._model.global_pool = self._model.head
        self._model.global_pool.flatten = nn.Sequential()
        self._model.global_pool.fc = nn.Sequential()
        self._model.head = nn.Sequential()
        _tmp = self._model.global_pool.norm
        self._model.global_pool.norm = nn.LayerNorm((out_features, 1, 1), _tmp.eps, _tmp.elementwise_affine)
    _tmp = self._model.conv1
    use_bias = _tmp.bias != None
    self._model.conv1 = nn.Conv2d(in_channels, out_channels=_tmp.out_channels, kernel_size=_tmp.kernel_size, stride=_tmp.stride, padding=_tmp.padding, bias=use_bias)
    if architecture.startswith('convnext'):
        del self._model.stem._modules['0']
    elif architecture.startswith('regnet'):
        del self._model.stem.conv
    torch.cuda.empty_cache()
    if use_bias:
        self._model.conv1.bias = _tmp.bias
    del _tmp

class SelfAttention(nn.Module):
    """
    A vanilla multi-head masked self-attention layer with a projection at the end.
    """

    def __init__(self, n_embd, n_head, attn_pdrop, resid_pdrop):
        super().__init__()
        assert n_embd % n_head == 0
        self.key = nn.Linear(n_embd, n_embd)
        self.query = nn.Linear(n_embd, n_embd)
        self.value = nn.Linear(n_embd, n_embd)
        self.attn_drop = nn.Dropout(attn_pdrop)
        self.resid_drop = nn.Dropout(resid_pdrop)
        self.proj = nn.Linear(n_embd, n_embd)
        self.n_head = n_head

    def forward(self, x):
        B, T, C = x.size()
        k = self.key(x).view(B, T, self.n_head, C // self.n_head).transpose(1, 2)
        q = self.query(x).view(B, T, self.n_head, C // self.n_head).transpose(1, 2)
        v = self.value(x).view(B, T, self.n_head, C // self.n_head).transpose(1, 2)
        att = q @ k.transpose(-2, -1) * (1.0 / math.sqrt(k.size(-1)))
        att = F.softmax(att, dim=-1)
        att = self.attn_drop(att)
        y = att @ v
        y = y.transpose(1, 2).contiguous().view(B, T, C)
        y = self.resid_drop(self.proj(y))
        return y

def __init__(self, n_embd, n_head, attn_pdrop, resid_pdrop):
    super().__init__()
    assert n_embd % n_head == 0
    self.key = nn.Linear(n_embd, n_embd)
    self.query = nn.Linear(n_embd, n_embd)
    self.value = nn.Linear(n_embd, n_embd)
    self.attn_drop = nn.Dropout(attn_pdrop)
    self.resid_drop = nn.Dropout(resid_pdrop)
    self.proj = nn.Linear(n_embd, n_embd)
    self.n_head = n_head

class Block(nn.Module):
    """ an unassuming Transformer block """

    def __init__(self, n_embd, n_head, block_exp, attn_pdrop, resid_pdrop):
        super().__init__()
        self.ln1 = nn.LayerNorm(n_embd)
        self.ln2 = nn.LayerNorm(n_embd)
        self.attn = SelfAttention(n_embd, n_head, attn_pdrop, resid_pdrop)
        self.mlp = nn.Sequential(nn.Linear(n_embd, block_exp * n_embd), nn.ReLU(True), nn.Linear(block_exp * n_embd, n_embd), nn.Dropout(resid_pdrop))

    def forward(self, x):
        x = x + self.attn(self.ln1(x))
        x = x + self.mlp(self.ln2(x))
        return x

def __init__(self, n_embd, n_head, block_exp, attn_pdrop, resid_pdrop):
    super().__init__()
    self.ln1 = nn.LayerNorm(n_embd)
    self.ln2 = nn.LayerNorm(n_embd)
    self.attn = SelfAttention(n_embd, n_head, attn_pdrop, resid_pdrop)
    self.mlp = nn.Sequential(nn.Linear(n_embd, block_exp * n_embd), nn.ReLU(True), nn.Linear(block_exp * n_embd, n_embd), nn.Dropout(resid_pdrop))

class LateFusionBackbone(nn.Module):
    """
    image_architecture: Architecture used in the image branch. ResNet, RegNet and ConvNext are supported
    lidar_architecture: Architecture used in the lidar branch. ResNet, RegNet and ConvNext are supported
    use_velocity: Whether to use the velocity input in the transformer.
    """

    def __init__(self, config, image_architecture='resnet34', lidar_architecture='resnet18', use_velocity=0):
        super().__init__()
        self.config = config
        if config.use_point_pillars == True:
            in_channels = config.num_features[-1]
        else:
            in_channels = 2 * config.lidar_seq_len
        if self.config.use_target_point_image == True:
            in_channels += 1
        self.image_encoder = ImageCNN(architecture=image_architecture, normalize=True)
        self.lidar_encoder = LidarEncoder(architecture=lidar_architecture, in_channels=in_channels)
        if image_architecture.startswith('convnext'):
            self.norm_after_pool_img = nn.LayerNorm((self.config.perception_output_features,), eps=1e-06)
        else:
            self.norm_after_pool_img = nn.Sequential()
        if lidar_architecture.startswith('convnext'):
            self.norm_after_pool_lidar = nn.LayerNorm((self.config.perception_output_features,), eps=1e-06)
        else:
            self.norm_after_pool_lidar = nn.Sequential()
        self.use_velocity = use_velocity
        if use_velocity:
            self.vel_emb = nn.Linear(1, self.config.perception_output_features)
        channel = self.config.bev_features_chanels
        self.relu = nn.ReLU(inplace=True)
        if self.image_encoder.features.num_features != self.config.perception_output_features:
            self.reduce_channels_conv_image = nn.Conv2d(self.image_encoder.features.num_features, self.config.perception_output_features, (1, 1))
        else:
            self.reduce_channels_conv_image = nn.Sequential()
        if self.image_encoder.features.num_features != self.config.perception_output_features:
            self.reduce_channels_conv_lidar = nn.Conv2d(self.lidar_encoder._model.num_features, self.config.perception_output_features, (1, 1))
        else:
            self.reduce_channels_conv_lidar = nn.Sequential()
        self.upsample = nn.Upsample(scale_factor=self.config.bev_upsample_factor, mode='bilinear', align_corners=False)
        self.up_conv5 = nn.Conv2d(channel, channel, (1, 1))
        self.up_conv4 = nn.Conv2d(channel, channel, (1, 1))
        self.up_conv3 = nn.Conv2d(channel, channel, (1, 1))
        self.c5_conv = nn.Conv2d(self.config.perception_output_features, channel, (1, 1))

    def top_down(self, c5):
        p5 = self.relu(self.c5_conv(c5))
        p4 = self.relu(self.up_conv5(self.upsample(p5)))
        p3 = self.relu(self.up_conv4(self.upsample(p4)))
        p2 = self.relu(self.up_conv3(self.upsample(p3)))
        return (p2, p3, p4, p5)

    def forward(self, image, lidar, velocity):
        """
        Image + LiDAR feature fusion
        Args:
            image_list (list): list of input images
            lidar_list (list): list of input LiDAR BEV
            velocity (tensor): input velocity from speedometer
        """
        if self.image_encoder.normalize:
            image_tensor = normalize_imagenet(image)
        else:
            image_tensor = image
        output_features_image = self.image_encoder.features(image_tensor)
        output_features_image = self.reduce_channels_conv_image(output_features_image)
        image_features_grid = output_features_image
        image_features = torch.nn.AdaptiveAvgPool2d((1, 1))(output_features_image)
        image_features = torch.flatten(image_features, 1)
        image_features = self.norm_after_pool_img(image_features)
        output_features_lidar = self.lidar_encoder._model(lidar)
        output_features_lidar = self.reduce_channels_conv_lidar(output_features_lidar)
        lidar_features_grid = output_features_lidar
        features = self.top_down(lidar_features_grid)
        lidar_features = torch.nn.AdaptiveAvgPool2d((1, 1))(output_features_lidar)
        lidar_features = torch.flatten(lidar_features, 1)
        lidar_features = self.norm_after_pool_lidar(lidar_features)
        fused_features = torch.add(image_features, lidar_features)
        if self.use_velocity:
            velocity_embeddings = self.vel_emb(velocity)
            fused_features = torch.add(fused_features, velocity_embeddings)
        return (features, image_features_grid, fused_features)

def __init__(self, config, image_architecture='resnet34', lidar_architecture='resnet18', use_velocity=0):
    super().__init__()
    self.config = config
    if config.use_point_pillars == True:
        in_channels = config.num_features[-1]
    else:
        in_channels = 2 * config.lidar_seq_len
    if self.config.use_target_point_image == True:
        in_channels += 1
    self.image_encoder = ImageCNN(architecture=image_architecture, normalize=True)
    self.lidar_encoder = LidarEncoder(architecture=lidar_architecture, in_channels=in_channels)
    if image_architecture.startswith('convnext'):
        self.norm_after_pool_img = nn.LayerNorm((self.config.perception_output_features,), eps=1e-06)
    else:
        self.norm_after_pool_img = nn.Sequential()
    if lidar_architecture.startswith('convnext'):
        self.norm_after_pool_lidar = nn.LayerNorm((self.config.perception_output_features,), eps=1e-06)
    else:
        self.norm_after_pool_lidar = nn.Sequential()
    self.use_velocity = use_velocity
    if use_velocity:
        self.vel_emb = nn.Linear(1, self.config.perception_output_features)
    channel = self.config.bev_features_chanels
    self.relu = nn.ReLU(inplace=True)
    if self.image_encoder.features.num_features != self.config.perception_output_features:
        self.reduce_channels_conv_image = nn.Conv2d(self.image_encoder.features.num_features, self.config.perception_output_features, (1, 1))
    else:
        self.reduce_channels_conv_image = nn.Sequential()
    if self.image_encoder.features.num_features != self.config.perception_output_features:
        self.reduce_channels_conv_lidar = nn.Conv2d(self.lidar_encoder._model.num_features, self.config.perception_output_features, (1, 1))
    else:
        self.reduce_channels_conv_lidar = nn.Sequential()
    self.upsample = nn.Upsample(scale_factor=self.config.bev_upsample_factor, mode='bilinear', align_corners=False)
    self.up_conv5 = nn.Conv2d(channel, channel, (1, 1))
    self.up_conv4 = nn.Conv2d(channel, channel, (1, 1))
    self.up_conv3 = nn.Conv2d(channel, channel, (1, 1))
    self.c5_conv = nn.Conv2d(self.config.perception_output_features, channel, (1, 1))

class ImageCNN(nn.Module):
    """ 
    Encoder network for image input list.
    Args:
        architecture (string): Vision architecture to be used from the TIMM model library.
        c_dim (int): output dimension of the latent embedding
        normalize (bool): whether the input images should be normalized
    """

    def __init__(self, architecture, normalize=True):
        super().__init__()
        self.normalize = normalize
        self.features = timm.create_model(architecture, pretrained=True)
        self.features.fc = nn.Sequential()
        self.features.classifier = nn.Sequential()
        self.features.global_pool = nn.Sequential()
        self.features.head = nn.Sequential()

def __init__(self, architecture, normalize=True):
    super().__init__()
    self.normalize = normalize
    self.features = timm.create_model(architecture, pretrained=True)
    self.features.fc = nn.Sequential()
    self.features.classifier = nn.Sequential()
    self.features.global_pool = nn.Sequential()
    self.features.head = nn.Sequential()

class LidarEncoder(nn.Module):
    """
    Encoder network for LiDAR input list
    Args:
        architecture (string): Vision architecture to be used from the TIMM model library.
        num_classes: output feature dimension
        in_channels: input channels
    """

    def __init__(self, architecture, in_channels=2):
        super().__init__()
        self._model = timm.create_model(architecture, pretrained=False, in_chans=in_channels)
        self._model.fc = nn.Sequential()
        self._model.global_pool = nn.Sequential()
        self._model.classifier = nn.Sequential()
        self._model.head = nn.Sequential()

def __init__(self, architecture, in_channels=2):
    super().__init__()
    self._model = timm.create_model(architecture, pretrained=False, in_chans=in_channels)
    self._model.fc = nn.Sequential()
    self._model.global_pool = nn.Sequential()
    self._model.classifier = nn.Sequential()
    self._model.head = nn.Sequential()

class latentTFBackbone(nn.Module):
    """
    Multi-scale Fusion Transformer for image + pos_embedding feature fusion
    image_architecture: Architecture used in the image branch. ResNet, RegNet and ConvNext are supported
    lidar_architecture: Architecture used in the lidar branch. ResNet, RegNet and ConvNext are supported
    use_velocity: Whether to use the velocity input in the transformer.
    """

    def __init__(self, config, image_architecture='resnet34', lidar_architecture='resnet18', use_velocity=True):
        super().__init__()
        self.config = config
        self.avgpool_img = nn.AdaptiveAvgPool2d((self.config.img_vert_anchors, self.config.img_horz_anchors))
        self.avgpool_lidar = nn.AdaptiveAvgPool2d((self.config.lidar_vert_anchors, self.config.lidar_horz_anchors))
        if config.use_point_pillars == True:
            in_channels = config.num_features[-1]
        else:
            in_channels = 2 * config.lidar_seq_len
        if self.config.use_target_point_image == True:
            in_channels += 1
        self.image_encoder = ImageCNN(architecture=image_architecture, normalize=True)
        self.lidar_encoder = LidarEncoder(architecture=lidar_architecture, in_channels=in_channels)
        self.transformer1 = GPT(n_embd=self.image_encoder.features.feature_info[1]['num_chs'], n_head=config.n_head, block_exp=config.block_exp, n_layer=config.n_layer, img_vert_anchors=config.img_vert_anchors, img_horz_anchors=config.img_horz_anchors, lidar_vert_anchors=config.lidar_vert_anchors, lidar_horz_anchors=config.lidar_horz_anchors, seq_len=config.seq_len, embd_pdrop=config.embd_pdrop, attn_pdrop=config.attn_pdrop, resid_pdrop=config.resid_pdrop, config=config, use_velocity=use_velocity)
        self.transformer2 = GPT(n_embd=self.image_encoder.features.feature_info[2]['num_chs'], n_head=config.n_head, block_exp=config.block_exp, n_layer=config.n_layer, img_vert_anchors=config.img_vert_anchors, img_horz_anchors=config.img_horz_anchors, lidar_vert_anchors=config.lidar_vert_anchors, lidar_horz_anchors=config.lidar_horz_anchors, seq_len=config.seq_len, embd_pdrop=config.embd_pdrop, attn_pdrop=config.attn_pdrop, resid_pdrop=config.resid_pdrop, config=config, use_velocity=use_velocity)
        self.transformer3 = GPT(n_embd=self.image_encoder.features.feature_info[3]['num_chs'], n_head=config.n_head, block_exp=config.block_exp, n_layer=config.n_layer, img_vert_anchors=config.img_vert_anchors, img_horz_anchors=config.img_horz_anchors, lidar_vert_anchors=config.lidar_vert_anchors, lidar_horz_anchors=config.lidar_horz_anchors, seq_len=config.seq_len, embd_pdrop=config.embd_pdrop, attn_pdrop=config.attn_pdrop, resid_pdrop=config.resid_pdrop, config=config, use_velocity=use_velocity)
        self.transformer4 = GPT(n_embd=self.image_encoder.features.feature_info[4]['num_chs'], n_head=config.n_head, block_exp=config.block_exp, n_layer=config.n_layer, img_vert_anchors=config.img_vert_anchors, img_horz_anchors=config.img_horz_anchors, lidar_vert_anchors=config.lidar_vert_anchors, lidar_horz_anchors=config.lidar_horz_anchors, seq_len=config.seq_len, embd_pdrop=config.embd_pdrop, attn_pdrop=config.attn_pdrop, resid_pdrop=config.resid_pdrop, config=config, use_velocity=use_velocity)
        if self.image_encoder.features.feature_info[4]['num_chs'] != self.config.perception_output_features:
            self.change_channel_conv_image = nn.Conv2d(self.image_encoder.features.feature_info[4]['num_chs'], self.config.perception_output_features, (1, 1))
            self.change_channel_conv_lidar = nn.Conv2d(self.image_encoder.features.feature_info[4]['num_chs'], self.config.perception_output_features, (1, 1))
        else:
            self.change_channel_conv_image = nn.Sequential()
            self.change_channel_conv_lidar = nn.Sequential()
        channel = self.config.bev_features_chanels
        self.relu = nn.ReLU(inplace=True)
        self.upsample = nn.Upsample(scale_factor=self.config.bev_upsample_factor, mode='bilinear', align_corners=False)
        self.up_conv5 = nn.Conv2d(channel, channel, (1, 1))
        self.up_conv4 = nn.Conv2d(channel, channel, (1, 1))
        self.up_conv3 = nn.Conv2d(channel, channel, (1, 1))
        self.c5_conv = nn.Conv2d(self.config.perception_output_features, channel, (1, 1))

    def top_down(self, x):
        p5 = self.relu(self.c5_conv(x))
        p4 = self.relu(self.up_conv5(self.upsample(p5)))
        p3 = self.relu(self.up_conv4(self.upsample(p4)))
        p2 = self.relu(self.up_conv3(self.upsample(p3)))
        return (p2, p3, p4, p5)

    def forward(self, image, lidar, velocity):
        """
        Image + LiDAR feature fusion using transformers
        Args:
            image: input rgb image
            lidar: LiDAR input will be replaced by positional encoding. Third channel may contain target point.
            velocity (tensor): input velocity from speedometer
        """
        if self.image_encoder.normalize:
            image_tensor = normalize_imagenet(image)
        else:
            image_tensor = image
        x = torch.linspace(-1, 1, self.config.lidar_resolution_width)
        y = torch.linspace(-1, 1, self.config.lidar_resolution_height)
        y_grid, x_grid = torch.meshgrid(x, y, indexing='ij')
        lidar[:, 0] = y_grid.unsqueeze(0)
        lidar[:, 1] = x_grid.unsqueeze(0)
        lidar_tensor = lidar
        image_features = self.image_encoder.features.conv1(image_tensor)
        image_features = self.image_encoder.features.bn1(image_features)
        image_features = self.image_encoder.features.act1(image_features)
        image_features = self.image_encoder.features.maxpool(image_features)
        lidar_features = self.lidar_encoder._model.conv1(lidar_tensor)
        lidar_features = self.lidar_encoder._model.bn1(lidar_features)
        lidar_features = self.lidar_encoder._model.act1(lidar_features)
        lidar_features = self.lidar_encoder._model.maxpool(lidar_features)
        image_features = self.image_encoder.features.layer1(image_features)
        lidar_features = self.lidar_encoder._model.layer1(lidar_features)
        image_embd_layer1 = self.avgpool_img(image_features)
        lidar_embd_layer1 = self.avgpool_lidar(lidar_features)
        image_features_layer1, lidar_features_layer1 = self.transformer1(image_embd_layer1, lidar_embd_layer1, velocity)
        image_features_layer1 = F.interpolate(image_features_layer1, size=(image_features.shape[2], image_features.shape[3]), mode='bilinear', align_corners=False)
        lidar_features_layer1 = F.interpolate(lidar_features_layer1, size=(lidar_features.shape[2], lidar_features.shape[3]), mode='bilinear', align_corners=False)
        image_features = image_features + image_features_layer1
        lidar_features = lidar_features + lidar_features_layer1
        image_features = self.image_encoder.features.layer2(image_features)
        lidar_features = self.lidar_encoder._model.layer2(lidar_features)
        image_embd_layer2 = self.avgpool_img(image_features)
        lidar_embd_layer2 = self.avgpool_lidar(lidar_features)
        image_features_layer2, lidar_features_layer2 = self.transformer2(image_embd_layer2, lidar_embd_layer2, velocity)
        image_features_layer2 = F.interpolate(image_features_layer2, size=(image_features.shape[2], image_features.shape[3]), mode='bilinear', align_corners=False)
        lidar_features_layer2 = F.interpolate(lidar_features_layer2, size=(lidar_features.shape[2], lidar_features.shape[3]), mode='bilinear', align_corners=False)
        image_features = image_features + image_features_layer2
        lidar_features = lidar_features + lidar_features_layer2
        image_features = self.image_encoder.features.layer3(image_features)
        lidar_features = self.lidar_encoder._model.layer3(lidar_features)
        image_embd_layer3 = self.avgpool_img(image_features)
        lidar_embd_layer3 = self.avgpool_lidar(lidar_features)
        image_features_layer3, lidar_features_layer3 = self.transformer3(image_embd_layer3, lidar_embd_layer3, velocity)
        image_features_layer3 = F.interpolate(image_features_layer3, size=(image_features.shape[2], image_features.shape[3]), mode='bilinear', align_corners=False)
        lidar_features_layer3 = F.interpolate(lidar_features_layer3, size=(lidar_features.shape[2], lidar_features.shape[3]), mode='bilinear', align_corners=False)
        image_features = image_features + image_features_layer3
        lidar_features = lidar_features + lidar_features_layer3
        image_features = self.image_encoder.features.layer4(image_features)
        lidar_features = self.lidar_encoder._model.layer4(lidar_features)
        image_embd_layer4 = self.avgpool_img(image_features)
        lidar_embd_layer4 = self.avgpool_lidar(lidar_features)
        image_features_layer4, lidar_features_layer4 = self.transformer4(image_embd_layer4, lidar_embd_layer4, velocity)
        image_features_layer4 = F.interpolate(image_features_layer4, size=(image_features.shape[2], image_features.shape[3]), mode='bilinear', align_corners=False)
        lidar_features_layer4 = F.interpolate(lidar_features_layer4, size=(lidar_features.shape[2], lidar_features.shape[3]), mode='bilinear', align_corners=False)
        image_features = image_features + image_features_layer4
        lidar_features = lidar_features + lidar_features_layer4
        image_features = self.change_channel_conv_image(image_features)
        lidar_features = self.change_channel_conv_lidar(lidar_features)
        x4 = lidar_features
        image_features_grid = image_features
        image_features = self.image_encoder.features.global_pool(image_features)
        image_features = torch.flatten(image_features, 1)
        lidar_features = self.lidar_encoder._model.global_pool(lidar_features)
        lidar_features = torch.flatten(lidar_features, 1)
        fused_features = image_features + lidar_features
        features = self.top_down(x4)
        return (features, image_features_grid, fused_features)

def __init__(self, config, image_architecture='resnet34', lidar_architecture='resnet18', use_velocity=True):
    super().__init__()
    self.config = config
    self.avgpool_img = nn.AdaptiveAvgPool2d((self.config.img_vert_anchors, self.config.img_horz_anchors))
    self.avgpool_lidar = nn.AdaptiveAvgPool2d((self.config.lidar_vert_anchors, self.config.lidar_horz_anchors))
    if config.use_point_pillars == True:
        in_channels = config.num_features[-1]
    else:
        in_channels = 2 * config.lidar_seq_len
    if self.config.use_target_point_image == True:
        in_channels += 1
    self.image_encoder = ImageCNN(architecture=image_architecture, normalize=True)
    self.lidar_encoder = LidarEncoder(architecture=lidar_architecture, in_channels=in_channels)
    self.transformer1 = GPT(n_embd=self.image_encoder.features.feature_info[1]['num_chs'], n_head=config.n_head, block_exp=config.block_exp, n_layer=config.n_layer, img_vert_anchors=config.img_vert_anchors, img_horz_anchors=config.img_horz_anchors, lidar_vert_anchors=config.lidar_vert_anchors, lidar_horz_anchors=config.lidar_horz_anchors, seq_len=config.seq_len, embd_pdrop=config.embd_pdrop, attn_pdrop=config.attn_pdrop, resid_pdrop=config.resid_pdrop, config=config, use_velocity=use_velocity)
    self.transformer2 = GPT(n_embd=self.image_encoder.features.feature_info[2]['num_chs'], n_head=config.n_head, block_exp=config.block_exp, n_layer=config.n_layer, img_vert_anchors=config.img_vert_anchors, img_horz_anchors=config.img_horz_anchors, lidar_vert_anchors=config.lidar_vert_anchors, lidar_horz_anchors=config.lidar_horz_anchors, seq_len=config.seq_len, embd_pdrop=config.embd_pdrop, attn_pdrop=config.attn_pdrop, resid_pdrop=config.resid_pdrop, config=config, use_velocity=use_velocity)
    self.transformer3 = GPT(n_embd=self.image_encoder.features.feature_info[3]['num_chs'], n_head=config.n_head, block_exp=config.block_exp, n_layer=config.n_layer, img_vert_anchors=config.img_vert_anchors, img_horz_anchors=config.img_horz_anchors, lidar_vert_anchors=config.lidar_vert_anchors, lidar_horz_anchors=config.lidar_horz_anchors, seq_len=config.seq_len, embd_pdrop=config.embd_pdrop, attn_pdrop=config.attn_pdrop, resid_pdrop=config.resid_pdrop, config=config, use_velocity=use_velocity)
    self.transformer4 = GPT(n_embd=self.image_encoder.features.feature_info[4]['num_chs'], n_head=config.n_head, block_exp=config.block_exp, n_layer=config.n_layer, img_vert_anchors=config.img_vert_anchors, img_horz_anchors=config.img_horz_anchors, lidar_vert_anchors=config.lidar_vert_anchors, lidar_horz_anchors=config.lidar_horz_anchors, seq_len=config.seq_len, embd_pdrop=config.embd_pdrop, attn_pdrop=config.attn_pdrop, resid_pdrop=config.resid_pdrop, config=config, use_velocity=use_velocity)
    if self.image_encoder.features.feature_info[4]['num_chs'] != self.config.perception_output_features:
        self.change_channel_conv_image = nn.Conv2d(self.image_encoder.features.feature_info[4]['num_chs'], self.config.perception_output_features, (1, 1))
        self.change_channel_conv_lidar = nn.Conv2d(self.image_encoder.features.feature_info[4]['num_chs'], self.config.perception_output_features, (1, 1))
    else:
        self.change_channel_conv_image = nn.Sequential()
        self.change_channel_conv_lidar = nn.Sequential()
    channel = self.config.bev_features_chanels
    self.relu = nn.ReLU(inplace=True)
    self.upsample = nn.Upsample(scale_factor=self.config.bev_upsample_factor, mode='bilinear', align_corners=False)
    self.up_conv5 = nn.Conv2d(channel, channel, (1, 1))
    self.up_conv4 = nn.Conv2d(channel, channel, (1, 1))
    self.up_conv3 = nn.Conv2d(channel, channel, (1, 1))
    self.c5_conv = nn.Conv2d(self.config.perception_output_features, channel, (1, 1))

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

class ImageCNN(nn.Module):
    """ 
    Encoder network for image input list.
    Args:
        architecture (string): Vision architecture to be used from the TIMM model library.
        c_dim (int): output dimension of the latent embedding
        normalize (bool): whether the input images should be normalized
    """

    def __init__(self, architecture, normalize=True):
        super().__init__()
        self.normalize = normalize
        self.features = timm.create_model(architecture, pretrained=True)
        self.features.fc = None
        if architecture.startswith('regnet'):
            self.features.conv1 = self.features.stem.conv
            self.features.bn1 = self.features.stem.bn
            self.features.act1 = nn.Sequential()
            self.features.maxpool = nn.Sequential()
            self.features.layer1 = self.features.s1
            self.features.layer2 = self.features.s2
            self.features.layer3 = self.features.s3
            self.features.layer4 = self.features.s4
            self.features.global_pool = nn.AdaptiveAvgPool2d(output_size=1)
            self.features.head = nn.Sequential()
        elif architecture.startswith('convnext'):
            self.features.conv1 = self.features.stem._modules['0']
            self.features.bn1 = self.features.stem._modules['1']
            self.features.act1 = nn.Sequential()
            self.features.maxpool = nn.Sequential()
            self.features.layer1 = self.features.stages._modules['0']
            self.features.layer2 = self.features.stages._modules['1']
            self.features.layer3 = self.features.stages._modules['2']
            self.features.layer4 = self.features.stages._modules['3']
            self.features.global_pool = self.features.head
            self.features.global_pool.flatten = nn.Sequential()
            self.features.global_pool.fc = nn.Sequential()
            self.features.head = nn.Sequential()
            self.features.feature_info.append(self.features.feature_info[3])
            self.features.feature_info[3] = self.features.feature_info[2]
            self.features.feature_info[2] = self.features.feature_info[1]
            self.features.feature_info[1] = self.features.feature_info[0]
            _tmp = self.features.global_pool.norm
            self.features.global_pool.norm = nn.LayerNorm((512, 1, 1), _tmp.eps, _tmp.elementwise_affine)

def __init__(self, architecture, normalize=True):
    super().__init__()
    self.normalize = normalize
    self.features = timm.create_model(architecture, pretrained=True)
    self.features.fc = None
    if architecture.startswith('regnet'):
        self.features.conv1 = self.features.stem.conv
        self.features.bn1 = self.features.stem.bn
        self.features.act1 = nn.Sequential()
        self.features.maxpool = nn.Sequential()
        self.features.layer1 = self.features.s1
        self.features.layer2 = self.features.s2
        self.features.layer3 = self.features.s3
        self.features.layer4 = self.features.s4
        self.features.global_pool = nn.AdaptiveAvgPool2d(output_size=1)
        self.features.head = nn.Sequential()
    elif architecture.startswith('convnext'):
        self.features.conv1 = self.features.stem._modules['0']
        self.features.bn1 = self.features.stem._modules['1']
        self.features.act1 = nn.Sequential()
        self.features.maxpool = nn.Sequential()
        self.features.layer1 = self.features.stages._modules['0']
        self.features.layer2 = self.features.stages._modules['1']
        self.features.layer3 = self.features.stages._modules['2']
        self.features.layer4 = self.features.stages._modules['3']
        self.features.global_pool = self.features.head
        self.features.global_pool.flatten = nn.Sequential()
        self.features.global_pool.fc = nn.Sequential()
        self.features.head = nn.Sequential()
        self.features.feature_info.append(self.features.feature_info[3])
        self.features.feature_info[3] = self.features.feature_info[2]
        self.features.feature_info[2] = self.features.feature_info[1]
        self.features.feature_info[1] = self.features.feature_info[0]
        _tmp = self.features.global_pool.norm
        self.features.global_pool.norm = nn.LayerNorm((512, 1, 1), _tmp.eps, _tmp.elementwise_affine)

class LidarEncoder(nn.Module):
    """
    Encoder network for LiDAR input list
    Args:
        architecture (string): Vision architecture to be used from the TIMM model library.
        num_classes: output feature dimension
        in_channels: input channels
    """

    def __init__(self, architecture, in_channels=2):
        super().__init__()
        self._model = timm.create_model(architecture, pretrained=False)
        self._model.fc = None
        if architecture.startswith('regnet'):
            self._model.conv1 = self._model.stem.conv
            self._model.bn1 = self._model.stem.bn
            self._model.act1 = nn.Sequential()
            self._model.maxpool = nn.Sequential()
            self._model.layer1 = self._model.s1
            self._model.layer2 = self._model.s2
            self._model.layer3 = self._model.s3
            self._model.layer4 = self._model.s4
            self._model.global_pool = nn.AdaptiveAvgPool2d(output_size=1)
            self._model.head = nn.Sequential()
        elif architecture.startswith('convnext'):
            self._model.conv1 = self._model.stem._modules['0']
            self._model.bn1 = self._model.stem._modules['1']
            self._model.act1 = nn.Sequential()
            self._model.maxpool = nn.Sequential()
            self._model.layer1 = self._model.stages._modules['0']
            self._model.layer2 = self._model.stages._modules['1']
            self._model.layer3 = self._model.stages._modules['2']
            self._model.layer4 = self._model.stages._modules['3']
            self._model.global_pool = self._model.head
            self._model.global_pool.flatten = nn.Sequential()
            self._model.global_pool.fc = nn.Sequential()
            self._model.head = nn.Sequential()
            _tmp = self._model.global_pool.norm
            self._model.global_pool.norm = nn.LayerNorm((512, 1, 1), _tmp.eps, _tmp.elementwise_affine)
        _tmp = self._model.conv1
        use_bias = _tmp.bias != None
        self._model.conv1 = nn.Conv2d(in_channels, out_channels=_tmp.out_channels, kernel_size=_tmp.kernel_size, stride=_tmp.stride, padding=_tmp.padding, bias=use_bias)
        del _tmp
        del self._model.stem
        torch.cuda.empty_cache()
        if use_bias:
            self._model.conv1.bias = _tmp.bias

def __init__(self, architecture, in_channels=2):
    super().__init__()
    self._model = timm.create_model(architecture, pretrained=False)
    self._model.fc = None
    if architecture.startswith('regnet'):
        self._model.conv1 = self._model.stem.conv
        self._model.bn1 = self._model.stem.bn
        self._model.act1 = nn.Sequential()
        self._model.maxpool = nn.Sequential()
        self._model.layer1 = self._model.s1
        self._model.layer2 = self._model.s2
        self._model.layer3 = self._model.s3
        self._model.layer4 = self._model.s4
        self._model.global_pool = nn.AdaptiveAvgPool2d(output_size=1)
        self._model.head = nn.Sequential()
    elif architecture.startswith('convnext'):
        self._model.conv1 = self._model.stem._modules['0']
        self._model.bn1 = self._model.stem._modules['1']
        self._model.act1 = nn.Sequential()
        self._model.maxpool = nn.Sequential()
        self._model.layer1 = self._model.stages._modules['0']
        self._model.layer2 = self._model.stages._modules['1']
        self._model.layer3 = self._model.stages._modules['2']
        self._model.layer4 = self._model.stages._modules['3']
        self._model.global_pool = self._model.head
        self._model.global_pool.flatten = nn.Sequential()
        self._model.global_pool.fc = nn.Sequential()
        self._model.head = nn.Sequential()
        _tmp = self._model.global_pool.norm
        self._model.global_pool.norm = nn.LayerNorm((512, 1, 1), _tmp.eps, _tmp.elementwise_affine)
    _tmp = self._model.conv1
    use_bias = _tmp.bias != None
    self._model.conv1 = nn.Conv2d(in_channels, out_channels=_tmp.out_channels, kernel_size=_tmp.kernel_size, stride=_tmp.stride, padding=_tmp.padding, bias=use_bias)
    del _tmp
    del self._model.stem
    torch.cuda.empty_cache()
    if use_bias:
        self._model.conv1.bias = _tmp.bias

class SelfAttention(nn.Module):
    """
    A vanilla multi-head masked self-attention layer with a projection at the end.
    """

    def __init__(self, n_embd, n_head, attn_pdrop, resid_pdrop):
        super().__init__()
        assert n_embd % n_head == 0
        self.key = nn.Linear(n_embd, n_embd)
        self.query = nn.Linear(n_embd, n_embd)
        self.value = nn.Linear(n_embd, n_embd)
        self.attn_drop = nn.Dropout(attn_pdrop)
        self.resid_drop = nn.Dropout(resid_pdrop)
        self.proj = nn.Linear(n_embd, n_embd)
        self.n_head = n_head

    def forward(self, x):
        B, T, C = x.size()
        k = self.key(x).view(B, T, self.n_head, C // self.n_head).transpose(1, 2)
        q = self.query(x).view(B, T, self.n_head, C // self.n_head).transpose(1, 2)
        v = self.value(x).view(B, T, self.n_head, C // self.n_head).transpose(1, 2)
        att = q @ k.transpose(-2, -1) * (1.0 / math.sqrt(k.size(-1)))
        att = F.softmax(att, dim=-1)
        att = self.attn_drop(att)
        y = att @ v
        y = y.transpose(1, 2).contiguous().view(B, T, C)
        y = self.resid_drop(self.proj(y))
        return y

def __init__(self, n_embd, n_head, attn_pdrop, resid_pdrop):
    super().__init__()
    assert n_embd % n_head == 0
    self.key = nn.Linear(n_embd, n_embd)
    self.query = nn.Linear(n_embd, n_embd)
    self.value = nn.Linear(n_embd, n_embd)
    self.attn_drop = nn.Dropout(attn_pdrop)
    self.resid_drop = nn.Dropout(resid_pdrop)
    self.proj = nn.Linear(n_embd, n_embd)
    self.n_head = n_head

class Block(nn.Module):
    """ an unassuming Transformer block """

    def __init__(self, n_embd, n_head, block_exp, attn_pdrop, resid_pdrop):
        super().__init__()
        self.ln1 = nn.LayerNorm(n_embd)
        self.ln2 = nn.LayerNorm(n_embd)
        self.attn = SelfAttention(n_embd, n_head, attn_pdrop, resid_pdrop)
        self.mlp = nn.Sequential(nn.Linear(n_embd, block_exp * n_embd), nn.ReLU(True), nn.Linear(block_exp * n_embd, n_embd), nn.Dropout(resid_pdrop))

    def forward(self, x):
        x = x + self.attn(self.ln1(x))
        x = x + self.mlp(self.ln2(x))
        return x

def __init__(self, n_embd, n_head, block_exp, attn_pdrop, resid_pdrop):
    super().__init__()
    self.ln1 = nn.LayerNorm(n_embd)
    self.ln2 = nn.LayerNorm(n_embd)
    self.attn = SelfAttention(n_embd, n_head, attn_pdrop, resid_pdrop)
    self.mlp = nn.Sequential(nn.Linear(n_embd, block_exp * n_embd), nn.ReLU(True), nn.Linear(block_exp * n_embd, n_embd), nn.Dropout(resid_pdrop))

class GeometricFusionBackbone(nn.Module):
    """
    image_architecture: Architecture used in the image branch. ResNet, RegNet and ConvNext are supported
    lidar_architecture: Architecture used in the lidar branch. ResNet, RegNet and ConvNext are supported
    use_velocity: Whether to use the velocity input in the transformer.
    """

    def __init__(self, config, image_architecture='resnet34', lidar_architecture='resnet18', use_velocity=0):
        super().__init__()
        self.config = config
        self.use_velocity = use_velocity
        self.avgpool_img = nn.AdaptiveAvgPool2d((self.config.img_vert_anchors, self.config.img_horz_anchors))
        self.avgpool_lidar = nn.AdaptiveAvgPool2d((self.config.lidar_vert_anchors, self.config.lidar_horz_anchors))
        if config.use_point_pillars == True:
            in_channels = config.num_features[-1]
        else:
            in_channels = 2 * config.lidar_seq_len
        if self.config.use_target_point_image == True:
            in_channels += 1
        self.image_encoder = ImageCNN(architecture=image_architecture, normalize=True)
        self.lidar_encoder = LidarEncoder(architecture=lidar_architecture, in_channels=in_channels)
        self.image_conv1 = nn.Conv2d(self.image_encoder.features.feature_info[1]['num_chs'], config.n_embd, 1)
        self.image_conv2 = nn.Conv2d(self.image_encoder.features.feature_info[2]['num_chs'], config.n_embd, 1)
        self.image_conv3 = nn.Conv2d(self.image_encoder.features.feature_info[3]['num_chs'], config.n_embd, 1)
        self.image_conv4 = nn.Conv2d(self.image_encoder.features.feature_info[4]['num_chs'], config.n_embd, 1)
        self.image_deconv1 = nn.Conv2d(config.n_embd, self.image_encoder.features.feature_info[1]['num_chs'], 1)
        self.image_deconv2 = nn.Conv2d(config.n_embd, self.image_encoder.features.feature_info[2]['num_chs'], 1)
        self.image_deconv3 = nn.Conv2d(config.n_embd, self.image_encoder.features.feature_info[3]['num_chs'], 1)
        self.image_deconv4 = nn.Conv2d(config.n_embd, self.image_encoder.features.feature_info[4]['num_chs'], 1)
        if use_velocity:
            self.vel_emb1 = nn.Linear(1, self.image_encoder.features.feature_info[1]['num_chs'])
            self.vel_emb2 = nn.Linear(1, self.image_encoder.features.feature_info[2]['num_chs'])
            self.vel_emb3 = nn.Linear(1, self.image_encoder.features.feature_info[3]['num_chs'])
            self.vel_emb4 = nn.Linear(1, self.image_encoder.features.feature_info[4]['num_chs'])
        self.lidar_conv1 = nn.Conv2d(self.image_encoder.features.feature_info[1]['num_chs'], config.n_embd, 1)
        self.lidar_conv2 = nn.Conv2d(self.image_encoder.features.feature_info[2]['num_chs'], config.n_embd, 1)
        self.lidar_conv3 = nn.Conv2d(self.image_encoder.features.feature_info[3]['num_chs'], config.n_embd, 1)
        self.lidar_conv4 = nn.Conv2d(self.image_encoder.features.feature_info[4]['num_chs'], config.n_embd, 1)
        self.lidar_deconv1 = nn.Conv2d(config.n_embd, self.image_encoder.features.feature_info[1]['num_chs'], 1)
        self.lidar_deconv2 = nn.Conv2d(config.n_embd, self.image_encoder.features.feature_info[2]['num_chs'], 1)
        self.lidar_deconv3 = nn.Conv2d(config.n_embd, self.image_encoder.features.feature_info[3]['num_chs'], 1)
        self.lidar_deconv4 = nn.Conv2d(config.n_embd, self.image_encoder.features.feature_info[4]['num_chs'], 1)
        hid_dim = config.n_embd
        self.image_projection1 = nn.Sequential(nn.Linear(hid_dim, hid_dim), nn.ReLU(True), nn.Linear(hid_dim, hid_dim), nn.ReLU(True), nn.Linear(hid_dim, hid_dim), nn.ReLU(True))
        self.image_projection2 = nn.Sequential(nn.Linear(hid_dim, hid_dim), nn.ReLU(True), nn.Linear(hid_dim, hid_dim), nn.ReLU(True), nn.Linear(hid_dim, hid_dim), nn.ReLU(True))
        self.image_projection3 = nn.Sequential(nn.Linear(hid_dim, hid_dim), nn.ReLU(True), nn.Linear(hid_dim, hid_dim), nn.ReLU(True), nn.Linear(hid_dim, hid_dim), nn.ReLU(True))
        self.image_projection4 = nn.Sequential(nn.Linear(hid_dim, hid_dim), nn.ReLU(True), nn.Linear(hid_dim, hid_dim), nn.ReLU(True), nn.Linear(hid_dim, hid_dim), nn.ReLU(True))
        self.lidar_projection1 = nn.Sequential(nn.Linear(hid_dim, hid_dim), nn.ReLU(True), nn.Linear(hid_dim, hid_dim), nn.ReLU(True), nn.Linear(hid_dim, hid_dim), nn.ReLU(True))
        self.lidar_projection2 = nn.Sequential(nn.Linear(hid_dim, hid_dim), nn.ReLU(True), nn.Linear(hid_dim, hid_dim), nn.ReLU(True), nn.Linear(hid_dim, hid_dim), nn.ReLU(True))
        self.lidar_projection3 = nn.Sequential(nn.Linear(hid_dim, hid_dim), nn.ReLU(True), nn.Linear(hid_dim, hid_dim), nn.ReLU(True), nn.Linear(hid_dim, hid_dim), nn.ReLU(True))
        self.lidar_projection4 = nn.Sequential(nn.Linear(hid_dim, hid_dim), nn.ReLU(True), nn.Linear(hid_dim, hid_dim), nn.ReLU(True), nn.Linear(hid_dim, hid_dim), nn.ReLU(True))
        if self.image_encoder.features.feature_info[4]['num_chs'] != self.config.perception_output_features:
            self.change_channel_conv_image = nn.Conv2d(self.image_encoder.features.feature_info[4]['num_chs'], self.config.perception_output_features, (1, 1))
            self.change_channel_conv_lidar = nn.Conv2d(self.image_encoder.features.feature_info[4]['num_chs'], self.config.perception_output_features, (1, 1))
        else:
            self.change_channel_conv_image = nn.Sequential()
            self.change_channel_conv_lidar = nn.Sequential()
        channel = self.config.bev_features_chanels
        self.relu = nn.ReLU(inplace=True)
        self.upsample = nn.Upsample(scale_factor=self.config.bev_upsample_factor, mode='bilinear', align_corners=False)
        self.up_conv5 = nn.Conv2d(channel, channel, (1, 1))
        self.up_conv4 = nn.Conv2d(channel, channel, (1, 1))
        self.up_conv3 = nn.Conv2d(channel, channel, (1, 1))
        self.c5_conv = nn.Conv2d(self.config.perception_output_features, channel, (1, 1))

    def top_down(self, x):
        p5 = self.relu(self.c5_conv(x))
        p4 = self.relu(self.up_conv5(self.upsample(p5)))
        p3 = self.relu(self.up_conv4(self.upsample(p4)))
        p2 = self.relu(self.up_conv3(self.upsample(p3)))
        return (p2, p3, p4, p5)

    def forward(self, image, lidar, velocity, bev_points, img_points):
        """
        Image + LiDAR feature fusion using transformers
        Args:
            image_list (list): list of input images
            lidar_list (list): list of input LiDAR BEV
            velocity (tensor): input velocity from speedometer
            bev_points (tensor): projected image pixels onto the BEV grid
            cam_points (tensor): projected LiDAR point cloud onto the image space
        """
        if self.image_encoder.normalize:
            image_tensor = normalize_imagenet(image)
        else:
            image_tensor = image
        lidar_tensor = lidar
        bz = lidar_tensor.shape[0]
        image_features = self.image_encoder.features.conv1(image_tensor)
        image_features = self.image_encoder.features.bn1(image_features)
        image_features = self.image_encoder.features.act1(image_features)
        image_features = self.image_encoder.features.maxpool(image_features)
        lidar_features = self.lidar_encoder._model.conv1(lidar_tensor)
        lidar_features = self.lidar_encoder._model.bn1(lidar_features)
        lidar_features = self.lidar_encoder._model.act1(lidar_features)
        lidar_features = self.lidar_encoder._model.maxpool(lidar_features)
        image_features = self.image_encoder.features.layer1(image_features)
        lidar_features = self.lidar_encoder._model.layer1(lidar_features)
        if self.config.n_scale >= 4:
            image_embd_layer1 = self.image_conv1(image_features)
            image_embd_layer1 = self.avgpool_img(image_embd_layer1)
            lidar_embd_layer1 = self.lidar_conv1(lidar_features)
            lidar_embd_layer1 = self.avgpool_lidar(lidar_embd_layer1)
            curr_h_image, curr_w_image = image_embd_layer1.shape[-2:]
            curr_h_lidar, curr_w_lidar = lidar_embd_layer1.shape[-2:]
            bev_points_layer1 = bev_points.view(bz * curr_h_lidar * curr_w_lidar * 5, 2)
            bev_encoding_layer1 = image_embd_layer1.permute(0, 2, 3, 1).contiguous()[:, bev_points_layer1[:, 1], bev_points_layer1[:, 0]].view(bz, bz, curr_h_lidar, curr_w_lidar, 5, -1)
            bev_encoding_layer1 = torch.diagonal(bev_encoding_layer1, 0).permute(4, 3, 0, 1, 2).contiguous()
            bev_encoding_layer1 = torch.sum(bev_encoding_layer1, -1)
            bev_encoding_layer1 = self.image_projection1(bev_encoding_layer1.permute(0, 2, 3, 1)).permute(0, 3, 1, 2).contiguous()
            lidar_features_layer1 = F.interpolate(bev_encoding_layer1, scale_factor=8, mode='bilinear', align_corners=False)
            lidar_features_layer1 = self.lidar_deconv1(lidar_features_layer1)
            lidar_features = lidar_features + lidar_features_layer1
            if self.use_velocity:
                vel_embedding1 = self.vel_emb1(velocity).unsqueeze(-1).unsqueeze(-1)
                lidar_features = lidar_features + vel_embedding1
            img_points_layer1 = img_points.view(bz * curr_h_image * curr_w_image * 5, 2)
            img_encoding_layer1 = lidar_embd_layer1.permute(0, 2, 3, 1).contiguous()[:, img_points_layer1[:, 1], img_points_layer1[:, 0]].view(bz, bz, curr_h_image, curr_w_image, 5, -1)
            img_encoding_layer1 = torch.diagonal(img_encoding_layer1, 0).permute(4, 3, 0, 1, 2).contiguous()
            img_encoding_layer1 = torch.sum(img_encoding_layer1, -1)
            img_encoding_layer1 = self.lidar_projection1(img_encoding_layer1.permute(0, 2, 3, 1)).permute(0, 3, 1, 2).contiguous()
            image_features_layer1 = F.interpolate(img_encoding_layer1, scale_factor=8, mode='bilinear', align_corners=False)
            image_features_layer1 = self.image_deconv1(image_features_layer1)
            image_features = image_features + image_features_layer1
            if self.use_velocity:
                image_features = image_features + vel_embedding1
        image_features = self.image_encoder.features.layer2(image_features)
        lidar_features = self.lidar_encoder._model.layer2(lidar_features)
        if self.config.n_scale >= 3:
            image_embd_layer2 = self.image_conv2(image_features)
            image_embd_layer2 = self.avgpool_img(image_embd_layer2)
            lidar_embd_layer2 = self.lidar_conv2(lidar_features)
            lidar_embd_layer2 = self.avgpool_lidar(lidar_embd_layer2)
            curr_h_image, curr_w_image = image_embd_layer2.shape[-2:]
            curr_h_lidar, curr_w_lidar = lidar_embd_layer2.shape[-2:]
            bev_points_layer2 = bev_points.view(bz * curr_h_lidar * curr_w_lidar * 5, 2)
            bev_encoding_layer2 = image_embd_layer2.permute(0, 2, 3, 1).contiguous()[:, bev_points_layer2[:, 1], bev_points_layer2[:, 0]].view(bz, bz, curr_h_lidar, curr_w_lidar, 5, -1)
            bev_encoding_layer2 = torch.diagonal(bev_encoding_layer2, 0).permute(4, 3, 0, 1, 2).contiguous()
            bev_encoding_layer2 = torch.sum(bev_encoding_layer2, -1)
            bev_encoding_layer2 = self.image_projection2(bev_encoding_layer2.permute(0, 2, 3, 1)).permute(0, 3, 1, 2).contiguous()
            lidar_features_layer2 = F.interpolate(bev_encoding_layer2, scale_factor=4, mode='bilinear', align_corners=False)
            lidar_features_layer2 = self.lidar_deconv2(lidar_features_layer2)
            lidar_features = lidar_features + lidar_features_layer2
            if self.use_velocity:
                vel_embedding2 = self.vel_emb2(velocity).unsqueeze(-1).unsqueeze(-1)
                lidar_features = lidar_features + vel_embedding2
            img_points_layer2 = img_points.view(bz * curr_h_image * curr_w_image * 5, 2)
            img_encoding_layer2 = lidar_embd_layer2.permute(0, 2, 3, 1).contiguous()[:, img_points_layer2[:, 1], img_points_layer2[:, 0]].view(bz, bz, curr_h_image, curr_w_image, 5, -1)
            img_encoding_layer2 = torch.diagonal(img_encoding_layer2, 0).permute(4, 3, 0, 1, 2).contiguous()
            img_encoding_layer2 = torch.sum(img_encoding_layer2, -1)
            img_encoding_layer2 = self.lidar_projection2(img_encoding_layer2.permute(0, 2, 3, 1)).permute(0, 3, 1, 2).contiguous()
            image_features_layer2 = F.interpolate(img_encoding_layer2, scale_factor=4, mode='bilinear', align_corners=False)
            image_features_layer2 = self.image_deconv2(image_features_layer2)
            image_features = image_features + image_features_layer2
            if self.use_velocity:
                image_features = image_features + vel_embedding2
        image_features = self.image_encoder.features.layer3(image_features)
        lidar_features = self.lidar_encoder._model.layer3(lidar_features)
        if self.config.n_scale >= 2:
            image_embd_layer3 = self.image_conv3(image_features)
            image_embd_layer3 = self.avgpool_img(image_embd_layer3)
            lidar_embd_layer3 = self.lidar_conv3(lidar_features)
            lidar_embd_layer3 = self.avgpool_lidar(lidar_embd_layer3)
            curr_h_image, curr_w_image = image_embd_layer3.shape[-2:]
            curr_h_lidar, curr_w_lidar = lidar_embd_layer3.shape[-2:]
            bev_points_layer3 = bev_points.view(bz * curr_h_lidar * curr_w_lidar * 5, 2)
            bev_encoding_layer3 = image_embd_layer3.permute(0, 2, 3, 1).contiguous()[:, bev_points_layer3[:, 1], bev_points_layer3[:, 0]].view(bz, bz, curr_h_lidar, curr_w_lidar, 5, -1)
            bev_encoding_layer3 = torch.diagonal(bev_encoding_layer3, 0).permute(4, 3, 0, 1, 2).contiguous()
            bev_encoding_layer3 = torch.sum(bev_encoding_layer3, -1)
            bev_encoding_layer3 = self.image_projection3(bev_encoding_layer3.permute(0, 2, 3, 1)).permute(0, 3, 1, 2).contiguous()
            lidar_features_layer3 = F.interpolate(bev_encoding_layer3, scale_factor=2, mode='bilinear', align_corners=False)
            lidar_features_layer3 = self.lidar_deconv3(lidar_features_layer3)
            lidar_features = lidar_features + lidar_features_layer3
            if self.use_velocity:
                vel_embedding3 = self.vel_emb3(velocity).unsqueeze(-1).unsqueeze(-1)
                lidar_features = lidar_features + vel_embedding3
            img_points_layer3 = img_points.view(bz * curr_h_image * curr_w_image * 5, 2)
            img_encoding_layer3 = lidar_embd_layer3.permute(0, 2, 3, 1).contiguous()[:, img_points_layer3[:, 1], img_points_layer3[:, 0]].view(bz, bz, curr_h_image, curr_w_image, 5, -1)
            img_encoding_layer3 = torch.diagonal(img_encoding_layer3, 0).permute(4, 3, 0, 1, 2).contiguous()
            img_encoding_layer3 = torch.sum(img_encoding_layer3, -1)
            img_encoding_layer3 = self.lidar_projection3(img_encoding_layer3.permute(0, 2, 3, 1)).permute(0, 3, 1, 2).contiguous()
            image_features_layer3 = F.interpolate(img_encoding_layer3, scale_factor=2, mode='bilinear', align_corners=False)
            image_features_layer3 = self.image_deconv3(image_features_layer3)
            image_features = image_features + image_features_layer3
            if self.use_velocity:
                image_features = image_features + vel_embedding3
        image_features = self.image_encoder.features.layer4(image_features)
        lidar_features = self.lidar_encoder._model.layer4(lidar_features)
        if self.config.n_scale >= 1:
            image_embd_layer4 = self.image_conv4(image_features)
            image_embd_layer4 = self.avgpool_img(image_embd_layer4)
            lidar_embd_layer4 = self.lidar_conv4(lidar_features)
            lidar_embd_layer4 = self.avgpool_lidar(lidar_embd_layer4)
            curr_h_image, curr_w_image = image_embd_layer4.shape[-2:]
            curr_h_lidar, curr_w_lidar = lidar_embd_layer4.shape[-2:]
            bev_points_layer4 = bev_points.view(bz * curr_h_lidar * curr_w_lidar * 5, 2)
            bev_encoding_layer4 = image_embd_layer4.permute(0, 2, 3, 1).contiguous()[:, bev_points_layer4[:, 1], bev_points_layer4[:, 0]].view(bz, bz, curr_h_lidar, curr_w_lidar, 5, -1)
            bev_encoding_layer4 = torch.diagonal(bev_encoding_layer4, 0).permute(4, 3, 0, 1, 2).contiguous()
            bev_encoding_layer4 = torch.sum(bev_encoding_layer4, -1)
            bev_encoding_layer4 = self.image_projection4(bev_encoding_layer4.permute(0, 2, 3, 1)).permute(0, 3, 1, 2).contiguous()
            lidar_features_layer4 = self.lidar_deconv4(bev_encoding_layer4)
            lidar_features = lidar_features + lidar_features_layer4
            if self.use_velocity:
                vel_embedding4 = self.vel_emb4(velocity).unsqueeze(-1).unsqueeze(-1)
                lidar_features = lidar_features + vel_embedding4
            img_points_layer4 = img_points.view(bz * curr_h_image * curr_w_image * 5, 2)
            img_encoding_layer4 = lidar_embd_layer3.permute(0, 2, 3, 1).contiguous()[:, img_points_layer4[:, 1], img_points_layer4[:, 0]].view(bz, bz, curr_h_image, curr_w_image, 5, -1)
            img_encoding_layer4 = torch.diagonal(img_encoding_layer4, 0).permute(4, 3, 0, 1, 2).contiguous()
            img_encoding_layer4 = torch.sum(img_encoding_layer4, -1)
            img_encoding_layer4 = self.lidar_projection4(img_encoding_layer4.permute(0, 2, 3, 1)).permute(0, 3, 1, 2).contiguous()
            image_features_layer4 = self.image_deconv4(img_encoding_layer4)
            image_features = image_features + image_features_layer4
            if self.use_velocity:
                image_features = image_features + vel_embedding4
        image_features = self.change_channel_conv_image(image_features)
        lidar_features = self.change_channel_conv_lidar(lidar_features)
        x4 = lidar_features
        image_features_grid = image_features
        image_features = self.image_encoder.features.global_pool(image_features)
        image_features = torch.flatten(image_features, 1)
        lidar_features = self.lidar_encoder._model.global_pool(lidar_features)
        lidar_features = torch.flatten(lidar_features, 1)
        fused_features = image_features + lidar_features
        features = self.top_down(x4)
        return (features, image_features_grid, fused_features)

def __init__(self, config, image_architecture='resnet34', lidar_architecture='resnet18', use_velocity=0):
    super().__init__()
    self.config = config
    self.use_velocity = use_velocity
    self.avgpool_img = nn.AdaptiveAvgPool2d((self.config.img_vert_anchors, self.config.img_horz_anchors))
    self.avgpool_lidar = nn.AdaptiveAvgPool2d((self.config.lidar_vert_anchors, self.config.lidar_horz_anchors))
    if config.use_point_pillars == True:
        in_channels = config.num_features[-1]
    else:
        in_channels = 2 * config.lidar_seq_len
    if self.config.use_target_point_image == True:
        in_channels += 1
    self.image_encoder = ImageCNN(architecture=image_architecture, normalize=True)
    self.lidar_encoder = LidarEncoder(architecture=lidar_architecture, in_channels=in_channels)
    self.image_conv1 = nn.Conv2d(self.image_encoder.features.feature_info[1]['num_chs'], config.n_embd, 1)
    self.image_conv2 = nn.Conv2d(self.image_encoder.features.feature_info[2]['num_chs'], config.n_embd, 1)
    self.image_conv3 = nn.Conv2d(self.image_encoder.features.feature_info[3]['num_chs'], config.n_embd, 1)
    self.image_conv4 = nn.Conv2d(self.image_encoder.features.feature_info[4]['num_chs'], config.n_embd, 1)
    self.image_deconv1 = nn.Conv2d(config.n_embd, self.image_encoder.features.feature_info[1]['num_chs'], 1)
    self.image_deconv2 = nn.Conv2d(config.n_embd, self.image_encoder.features.feature_info[2]['num_chs'], 1)
    self.image_deconv3 = nn.Conv2d(config.n_embd, self.image_encoder.features.feature_info[3]['num_chs'], 1)
    self.image_deconv4 = nn.Conv2d(config.n_embd, self.image_encoder.features.feature_info[4]['num_chs'], 1)
    if use_velocity:
        self.vel_emb1 = nn.Linear(1, self.image_encoder.features.feature_info[1]['num_chs'])
        self.vel_emb2 = nn.Linear(1, self.image_encoder.features.feature_info[2]['num_chs'])
        self.vel_emb3 = nn.Linear(1, self.image_encoder.features.feature_info[3]['num_chs'])
        self.vel_emb4 = nn.Linear(1, self.image_encoder.features.feature_info[4]['num_chs'])
    self.lidar_conv1 = nn.Conv2d(self.image_encoder.features.feature_info[1]['num_chs'], config.n_embd, 1)
    self.lidar_conv2 = nn.Conv2d(self.image_encoder.features.feature_info[2]['num_chs'], config.n_embd, 1)
    self.lidar_conv3 = nn.Conv2d(self.image_encoder.features.feature_info[3]['num_chs'], config.n_embd, 1)
    self.lidar_conv4 = nn.Conv2d(self.image_encoder.features.feature_info[4]['num_chs'], config.n_embd, 1)
    self.lidar_deconv1 = nn.Conv2d(config.n_embd, self.image_encoder.features.feature_info[1]['num_chs'], 1)
    self.lidar_deconv2 = nn.Conv2d(config.n_embd, self.image_encoder.features.feature_info[2]['num_chs'], 1)
    self.lidar_deconv3 = nn.Conv2d(config.n_embd, self.image_encoder.features.feature_info[3]['num_chs'], 1)
    self.lidar_deconv4 = nn.Conv2d(config.n_embd, self.image_encoder.features.feature_info[4]['num_chs'], 1)
    hid_dim = config.n_embd
    self.image_projection1 = nn.Sequential(nn.Linear(hid_dim, hid_dim), nn.ReLU(True), nn.Linear(hid_dim, hid_dim), nn.ReLU(True), nn.Linear(hid_dim, hid_dim), nn.ReLU(True))
    self.image_projection2 = nn.Sequential(nn.Linear(hid_dim, hid_dim), nn.ReLU(True), nn.Linear(hid_dim, hid_dim), nn.ReLU(True), nn.Linear(hid_dim, hid_dim), nn.ReLU(True))
    self.image_projection3 = nn.Sequential(nn.Linear(hid_dim, hid_dim), nn.ReLU(True), nn.Linear(hid_dim, hid_dim), nn.ReLU(True), nn.Linear(hid_dim, hid_dim), nn.ReLU(True))
    self.image_projection4 = nn.Sequential(nn.Linear(hid_dim, hid_dim), nn.ReLU(True), nn.Linear(hid_dim, hid_dim), nn.ReLU(True), nn.Linear(hid_dim, hid_dim), nn.ReLU(True))
    self.lidar_projection1 = nn.Sequential(nn.Linear(hid_dim, hid_dim), nn.ReLU(True), nn.Linear(hid_dim, hid_dim), nn.ReLU(True), nn.Linear(hid_dim, hid_dim), nn.ReLU(True))
    self.lidar_projection2 = nn.Sequential(nn.Linear(hid_dim, hid_dim), nn.ReLU(True), nn.Linear(hid_dim, hid_dim), nn.ReLU(True), nn.Linear(hid_dim, hid_dim), nn.ReLU(True))
    self.lidar_projection3 = nn.Sequential(nn.Linear(hid_dim, hid_dim), nn.ReLU(True), nn.Linear(hid_dim, hid_dim), nn.ReLU(True), nn.Linear(hid_dim, hid_dim), nn.ReLU(True))
    self.lidar_projection4 = nn.Sequential(nn.Linear(hid_dim, hid_dim), nn.ReLU(True), nn.Linear(hid_dim, hid_dim), nn.ReLU(True), nn.Linear(hid_dim, hid_dim), nn.ReLU(True))
    if self.image_encoder.features.feature_info[4]['num_chs'] != self.config.perception_output_features:
        self.change_channel_conv_image = nn.Conv2d(self.image_encoder.features.feature_info[4]['num_chs'], self.config.perception_output_features, (1, 1))
        self.change_channel_conv_lidar = nn.Conv2d(self.image_encoder.features.feature_info[4]['num_chs'], self.config.perception_output_features, (1, 1))
    else:
        self.change_channel_conv_image = nn.Sequential()
        self.change_channel_conv_lidar = nn.Sequential()
    channel = self.config.bev_features_chanels
    self.relu = nn.ReLU(inplace=True)
    self.upsample = nn.Upsample(scale_factor=self.config.bev_upsample_factor, mode='bilinear', align_corners=False)
    self.up_conv5 = nn.Conv2d(channel, channel, (1, 1))
    self.up_conv4 = nn.Conv2d(channel, channel, (1, 1))
    self.up_conv3 = nn.Conv2d(channel, channel, (1, 1))
    self.c5_conv = nn.Conv2d(self.config.perception_output_features, channel, (1, 1))

class ImageCNN(nn.Module):
    """ 
    Encoder network for image input list.
    Args:
        architecture (string): Vision architecture to be used from the TIMM model library.
        c_dim (int): output dimension of the latent embedding
        normalize (bool): whether the input images should be normalized
    """

    def __init__(self, architecture, normalize=True):
        super().__init__()
        self.normalize = normalize
        self.features = timm.create_model(architecture, pretrained=True)
        self.features.fc = None
        if architecture.startswith('regnet'):
            self.features.conv1 = self.features.stem.conv
            self.features.bn1 = self.features.stem.bn
            self.features.act1 = nn.Sequential()
            self.features.maxpool = nn.Sequential()
            self.features.layer1 = self.features.s1
            self.features.layer2 = self.features.s2
            self.features.layer3 = self.features.s3
            self.features.layer4 = self.features.s4
            self.features.global_pool = nn.AdaptiveAvgPool2d(output_size=1)
            self.features.head = nn.Sequential()
        elif architecture.startswith('convnext'):
            self.features.conv1 = self.features.stem._modules['0']
            self.features.bn1 = self.features.stem._modules['1']
            self.features.act1 = nn.Sequential()
            self.features.maxpool = nn.Sequential()
            self.features.layer1 = self.features.stages._modules['0']
            self.features.layer2 = self.features.stages._modules['1']
            self.features.layer3 = self.features.stages._modules['2']
            self.features.layer4 = self.features.stages._modules['3']
            self.features.global_pool = self.features.head
            self.features.global_pool.flatten = nn.Sequential()
            self.features.global_pool.fc = nn.Sequential()
            self.features.head = nn.Sequential()
            self.features.feature_info.append(self.features.feature_info[3])
            self.features.feature_info[3] = self.features.feature_info[2]
            self.features.feature_info[2] = self.features.feature_info[1]
            self.features.feature_info[1] = self.features.feature_info[0]
            _tmp = self.features.global_pool.norm
            self.features.global_pool.norm = nn.LayerNorm((512, 1, 1), _tmp.eps, _tmp.elementwise_affine)

def __init__(self, architecture, normalize=True):
    super().__init__()
    self.normalize = normalize
    self.features = timm.create_model(architecture, pretrained=True)
    self.features.fc = None
    if architecture.startswith('regnet'):
        self.features.conv1 = self.features.stem.conv
        self.features.bn1 = self.features.stem.bn
        self.features.act1 = nn.Sequential()
        self.features.maxpool = nn.Sequential()
        self.features.layer1 = self.features.s1
        self.features.layer2 = self.features.s2
        self.features.layer3 = self.features.s3
        self.features.layer4 = self.features.s4
        self.features.global_pool = nn.AdaptiveAvgPool2d(output_size=1)
        self.features.head = nn.Sequential()
    elif architecture.startswith('convnext'):
        self.features.conv1 = self.features.stem._modules['0']
        self.features.bn1 = self.features.stem._modules['1']
        self.features.act1 = nn.Sequential()
        self.features.maxpool = nn.Sequential()
        self.features.layer1 = self.features.stages._modules['0']
        self.features.layer2 = self.features.stages._modules['1']
        self.features.layer3 = self.features.stages._modules['2']
        self.features.layer4 = self.features.stages._modules['3']
        self.features.global_pool = self.features.head
        self.features.global_pool.flatten = nn.Sequential()
        self.features.global_pool.fc = nn.Sequential()
        self.features.head = nn.Sequential()
        self.features.feature_info.append(self.features.feature_info[3])
        self.features.feature_info[3] = self.features.feature_info[2]
        self.features.feature_info[2] = self.features.feature_info[1]
        self.features.feature_info[1] = self.features.feature_info[0]
        _tmp = self.features.global_pool.norm
        self.features.global_pool.norm = nn.LayerNorm((512, 1, 1), _tmp.eps, _tmp.elementwise_affine)

class LidarEncoder(nn.Module):
    """
    Encoder network for LiDAR input list
    Args:
        architecture (string): Vision architecture to be used from the TIMM model library.
        num_classes: output feature dimension
        in_channels: input channels
    """

    def __init__(self, architecture, in_channels=2):
        super().__init__()
        self._model = timm.create_model(architecture, pretrained=False)
        self._model.fc = None
        if architecture.startswith('regnet'):
            self._model.conv1 = self._model.stem.conv
            self._model.bn1 = self._model.stem.bn
            self._model.act1 = nn.Sequential()
            self._model.maxpool = nn.Sequential()
            self._model.layer1 = self._model.s1
            self._model.layer2 = self._model.s2
            self._model.layer3 = self._model.s3
            self._model.layer4 = self._model.s4
            self._model.global_pool = nn.AdaptiveAvgPool2d(output_size=1)
            self._model.head = nn.Sequential()
        elif architecture.startswith('convnext'):
            self._model.conv1 = self._model.stem._modules['0']
            self._model.bn1 = self._model.stem._modules['1']
            self._model.act1 = nn.Sequential()
            self._model.maxpool = nn.Sequential()
            self._model.layer1 = self._model.stages._modules['0']
            self._model.layer2 = self._model.stages._modules['1']
            self._model.layer3 = self._model.stages._modules['2']
            self._model.layer4 = self._model.stages._modules['3']
            self._model.global_pool = self._model.head
            self._model.global_pool.flatten = nn.Sequential()
            self._model.global_pool.fc = nn.Sequential()
            self._model.head = nn.Sequential()
            _tmp = self._model.global_pool.norm
            self._model.global_pool.norm = nn.LayerNorm((self.config.perception_output_features, 1, 1), _tmp.eps, _tmp.elementwise_affine)
        _tmp = self._model.conv1
        use_bias = _tmp.bias != None
        self._model.conv1 = nn.Conv2d(in_channels, out_channels=_tmp.out_channels, kernel_size=_tmp.kernel_size, stride=_tmp.stride, padding=_tmp.padding, bias=use_bias)
        del _tmp
        del self._model.stem
        torch.cuda.empty_cache()
        if use_bias:
            self._model.conv1.bias = _tmp.bias

def __init__(self, architecture, in_channels=2):
    super().__init__()
    self._model = timm.create_model(architecture, pretrained=False)
    self._model.fc = None
    if architecture.startswith('regnet'):
        self._model.conv1 = self._model.stem.conv
        self._model.bn1 = self._model.stem.bn
        self._model.act1 = nn.Sequential()
        self._model.maxpool = nn.Sequential()
        self._model.layer1 = self._model.s1
        self._model.layer2 = self._model.s2
        self._model.layer3 = self._model.s3
        self._model.layer4 = self._model.s4
        self._model.global_pool = nn.AdaptiveAvgPool2d(output_size=1)
        self._model.head = nn.Sequential()
    elif architecture.startswith('convnext'):
        self._model.conv1 = self._model.stem._modules['0']
        self._model.bn1 = self._model.stem._modules['1']
        self._model.act1 = nn.Sequential()
        self._model.maxpool = nn.Sequential()
        self._model.layer1 = self._model.stages._modules['0']
        self._model.layer2 = self._model.stages._modules['1']
        self._model.layer3 = self._model.stages._modules['2']
        self._model.layer4 = self._model.stages._modules['3']
        self._model.global_pool = self._model.head
        self._model.global_pool.flatten = nn.Sequential()
        self._model.global_pool.fc = nn.Sequential()
        self._model.head = nn.Sequential()
        _tmp = self._model.global_pool.norm
        self._model.global_pool.norm = nn.LayerNorm((self.config.perception_output_features, 1, 1), _tmp.eps, _tmp.elementwise_affine)
    _tmp = self._model.conv1
    use_bias = _tmp.bias != None
    self._model.conv1 = nn.Conv2d(in_channels, out_channels=_tmp.out_channels, kernel_size=_tmp.kernel_size, stride=_tmp.stride, padding=_tmp.padding, bias=use_bias)
    del _tmp
    del self._model.stem
    torch.cuda.empty_cache()
    if use_bias:
        self._model.conv1.bias = _tmp.bias

class DynamicPointNet(nn.Module):

    def __init__(self, num_input=9, num_features=[32, 32]):
        super().__init__()
        L = []
        for num_feature in num_features:
            L += [nn.Linear(num_input, num_feature), nn.BatchNorm1d(num_feature), nn.ReLU(inplace=True)]
            num_input = num_feature
        self.net = nn.Sequential(*L)

    def forward(self, points, inverse_indices):
        """
        TODO: multiple layers
        """
        feat = self.net(points)
        feat_max = scatter_max(feat, inverse_indices, dim=0)[0]
        return feat_max

def __init__(self, num_input=9, num_features=[32, 32]):
    super().__init__()
    L = []
    for num_feature in num_features:
        L += [nn.Linear(num_input, num_feature), nn.BatchNorm1d(num_feature), nn.ReLU(inplace=True)]
        num_input = num_feature
    self.net = nn.Sequential(*L)

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

class LidarCenterNet(nn.Module):
    """
    Encoder network for LiDAR input list
    Args:
        in_channels: input channels
    """

    def __init__(self, config, device, backbone, image_architecture='resnet34', lidar_architecture='resnet18', use_velocity=True):
        super().__init__()
        self.device = device
        self.config = config
        self.pred_len = config.pred_len
        self.use_target_point_image = config.use_target_point_image
        self.gru_concat_target_point = config.gru_concat_target_point
        self.use_point_pillars = config.use_point_pillars
        if self.use_point_pillars == True:
            self.point_pillar_net = PointPillarNet(config.num_input, config.num_features, min_x=config.min_x, max_x=config.max_x, min_y=config.min_y, max_y=config.max_y, pixels_per_meter=int(config.pixels_per_meter))
        self.backbone = backbone
        if backbone == 'transFuser':
            self._model = TransfuserBackbone(config, image_architecture, lidar_architecture, use_velocity=use_velocity).to(self.device)
        elif backbone == 'late_fusion':
            self._model = LateFusionBackbone(config, image_architecture, lidar_architecture, use_velocity=use_velocity).to(self.device)
        elif backbone == 'geometric_fusion':
            self._model = GeometricFusionBackbone(config, image_architecture, lidar_architecture, use_velocity=use_velocity).to(self.device)
        elif backbone == 'latentTF':
            self._model = latentTFBackbone(config, image_architecture, lidar_architecture, use_velocity=use_velocity).to(self.device)
        else:
            raise 'The chosen vision backbone does not exist. The options are: transFuser, late_fusion, geometric_fusion, latentTF'
        if config.multitask:
            self.seg_decoder = SegDecoder(self.config, self.config.perception_output_features).to(self.device)
            self.depth_decoder = DepthDecoder(self.config, self.config.perception_output_features).to(self.device)
        channel = config.channel
        self.pred_bev = nn.Sequential(nn.Conv2d(channel, channel, kernel_size=(3, 3), stride=1, padding=(1, 1), bias=True), nn.ReLU(inplace=True), nn.Conv2d(channel, 3, kernel_size=(1, 1), stride=1, padding=0, bias=True)).to(self.device)
        self.head = LidarCenterNetHead(channel, channel, 1, train_cfg=config).to(self.device)
        self.i = 0
        self.join = nn.Sequential(nn.Linear(512, 256), nn.ReLU(inplace=True), nn.Linear(256, 128), nn.ReLU(inplace=True), nn.Linear(128, 64), nn.ReLU(inplace=True)).to(self.device)
        self.decoder = nn.GRUCell(input_size=4 if self.gru_concat_target_point else 2, hidden_size=self.config.gru_hidden_size).to(self.device)
        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
        self.output = nn.Linear(self.config.gru_hidden_size, 3).to(self.device)
        self.turn_controller = PIDController(K_P=config.turn_KP, K_I=config.turn_KI, K_D=config.turn_KD, n=config.turn_n)
        self.speed_controller = PIDController(K_P=config.speed_KP, K_I=config.speed_KI, K_D=config.speed_KD, n=config.speed_n)

    def forward_gru(self, z, target_point):
        z = self.join(z)
        output_wp = list()
        x = torch.zeros(size=(z.shape[0], 2), dtype=z.dtype).to(z.device)
        target_point = target_point.clone()
        target_point[:, 1] *= -1
        for _ in range(self.pred_len):
            if self.gru_concat_target_point:
                x_in = torch.cat([x, target_point], dim=1)
            else:
                x_in = x
            z = self.decoder(x_in, z)
            dx = self.output(z)
            x = dx[:, :2] + x
            output_wp.append(x[:, :2])
        pred_wp = torch.stack(output_wp, dim=1)
        pred_wp[:, :, 0] = pred_wp[:, :, 0] - self.config.lidar_pos[0]
        pred_brake = None
        steer = None
        throttle = None
        brake = None
        return (pred_wp, pred_brake, steer, throttle, brake)

    def control_pid(self, waypoints, velocity, is_stuck):
        """ Predicts vehicle control with a PID controller.
        Args:
            waypoints (tensor): output of self.plan()
            velocity (tensor): speedometer input
        """
        assert waypoints.size(0) == 1
        waypoints = waypoints[0].data.cpu().numpy()
        waypoints[:, 0] += self.config.lidar_pos[0]
        speed = velocity[0].data.cpu().numpy()
        desired_speed = np.linalg.norm(waypoints[0] - waypoints[1]) * 2.0
        if is_stuck:
            desired_speed = np.array(self.config.default_speed)
        brake = desired_speed < self.config.brake_speed or speed / desired_speed > self.config.brake_ratio
        delta = np.clip(desired_speed - speed, 0.0, self.config.clip_delta)
        throttle = self.speed_controller.step(delta)
        throttle = np.clip(throttle, 0.0, self.config.clip_throttle)
        throttle = throttle if not brake else 0.0
        aim = (waypoints[1] + waypoints[0]) / 2.0
        angle = np.degrees(np.arctan2(aim[1], aim[0])) / 90.0
        if speed < 0.01:
            angle = 0.0
        if brake:
            angle = 0.0
        steer = self.turn_controller.step(angle)
        steer = np.clip(steer, -1.0, 1.0)
        return (steer, throttle, brake)

    def forward_ego(self, rgb, lidar_bev, target_point, target_point_image, ego_vel, bev_points=None, cam_points=None, save_path=None, expert_waypoints=None, stuck_detector=0, forced_move=False, num_points=None, rgb_back=None, debug=False):
        if self.use_point_pillars == True:
            lidar_bev = self.point_pillar_net(lidar_bev, num_points)
            lidar_bev = torch.rot90(lidar_bev, -1, dims=(2, 3))
        if self.use_target_point_image:
            lidar_bev = torch.cat((lidar_bev, target_point_image), dim=1)
        if self.backbone == 'transFuser':
            features, image_features_grid, fused_features = self._model(rgb, lidar_bev, ego_vel)
        elif self.backbone == 'late_fusion':
            features, image_features_grid, fused_features = self._model(rgb, lidar_bev, ego_vel)
        elif self.backbone == 'geometric_fusion':
            features, image_features_grid, fused_features = self._model(rgb, lidar_bev, ego_vel, bev_points, cam_points)
        elif self.backbone == 'latentTF':
            features, image_features_grid, fused_features = self._model(rgb, lidar_bev, ego_vel)
        else:
            raise 'The chosen vision backbone does not exist. The options are: transFuser, late_fusion, geometric_fusion, latentTF'
        pred_wp, _, _, _, _ = self.forward_gru(fused_features, target_point)
        preds = self.head([features[0]])
        results = self.head.get_bboxes(preds[0], preds[1], preds[2], preds[3], preds[4], preds[5], preds[6])
        bboxes, _ = results[0]
        bboxes = bboxes[bboxes[:, -1] > self.config.bb_confidence_threshold]
        rotated_bboxes = []
        for bbox in bboxes.detach().cpu().numpy():
            bbox = self.get_bbox_local_metric(bbox)
            rotated_bboxes.append(bbox)
        self.i += 1
        if debug and self.i % 2 == 0 and (not save_path is None):
            pred_bev = self.pred_bev(features[0])
            pred_bev = F.interpolate(pred_bev, (self.config.bev_resolution_height, self.config.bev_resolution_width), mode='bilinear', align_corners=True)
            pred_semantic = self.seg_decoder(image_features_grid)
            pred_depth = self.depth_decoder(image_features_grid)
            self.visualize_model_io(save_path, self.i, self.config, rgb, lidar_bev, target_point, pred_wp, pred_bev, pred_semantic, pred_depth, bboxes, self.device, gt_bboxes=None, expert_waypoints=expert_waypoints, stuck_detector=stuck_detector, forced_move=forced_move)
        return (pred_wp, rotated_bboxes)

    def forward(self, rgb, lidar_bev, ego_waypoint, target_point, target_point_image, ego_vel, bev, label, depth, semantic, num_points=None, save_path=None, bev_points=None, cam_points=None):
        loss = {}
        if self.use_point_pillars == True:
            lidar_bev = self.point_pillar_net(lidar_bev, num_points)
            lidar_bev = torch.rot90(lidar_bev, -1, dims=(2, 3))
        if self.use_target_point_image:
            lidar_bev = torch.cat((lidar_bev, target_point_image), dim=1)
        if self.backbone == 'transFuser':
            features, image_features_grid, fused_features = self._model(rgb, lidar_bev, ego_vel)
        elif self.backbone == 'late_fusion':
            features, image_features_grid, fused_features = self._model(rgb, lidar_bev, ego_vel)
        elif self.backbone == 'geometric_fusion':
            features, image_features_grid, fused_features = self._model(rgb, lidar_bev, ego_vel, bev_points, cam_points)
        elif self.backbone == 'latentTF':
            features, image_features_grid, fused_features = self._model(rgb, lidar_bev, ego_vel)
        else:
            raise 'The chosen vision backbone does not exist. The options are: transFuser, late_fusion, geometric_fusion, latentTF'
        pred_wp, _, _, _, _ = self.forward_gru(fused_features, target_point)
        pred_bev = self.pred_bev(features[0])
        pred_bev = F.interpolate(pred_bev, (self.config.bev_resolution_height, self.config.bev_resolution_width), mode='bilinear', align_corners=True)
        weight = torch.from_numpy(np.array([1.0, 1.0, 3.0])).to(dtype=torch.float32, device=pred_bev.device)
        loss_bev = F.cross_entropy(pred_bev, bev, weight=weight).mean()
        loss_wp = torch.mean(torch.abs(pred_wp - ego_waypoint))
        loss.update({'loss_wp': loss_wp, 'loss_bev': loss_bev})
        preds = self.head([features[0]])
        gt_labels = torch.zeros_like(label[:, :, 0])
        gt_bboxes_ignore = label.sum(dim=-1) == 0.0
        loss_bbox = self.head.loss(preds[0], preds[1], preds[2], preds[3], preds[4], preds[5], preds[6], [label], gt_labels=[gt_labels], gt_bboxes_ignore=[gt_bboxes_ignore], img_metas=None)
        loss.update(loss_bbox)
        if self.config.multitask:
            pred_semantic = self.seg_decoder(image_features_grid)
            pred_depth = self.depth_decoder(image_features_grid)
            loss_semantic = self.config.ls_seg * F.cross_entropy(pred_semantic, semantic).mean()
            loss_depth = self.config.ls_depth * F.l1_loss(pred_depth, depth).mean()
            loss.update({'loss_depth': loss_depth, 'loss_semantic': loss_semantic})
        else:
            loss.update({'loss_depth': torch.zeros_like(loss_wp), 'loss_semantic': torch.zeros_like(loss_wp)})
        self.i += 1
        if self.config.debug == True and self.i % self.config.train_debug_save_freq == 0 and (save_path != None):
            with torch.no_grad():
                results = self.head.get_bboxes(preds[0], preds[1], preds[2], preds[3], preds[4], preds[5], preds[6])
                bboxes, _ = results[0]
                bboxes = bboxes[bboxes[:, -1] > self.config.bb_confidence_threshold]
                self.visualize_model_io(save_path, self.i, self.config, rgb, lidar_bev, target_point, pred_wp, pred_bev, pred_semantic, pred_depth, bboxes, self.device, gt_bboxes=label, expert_waypoints=ego_waypoint, stuck_detector=0, forced_move=False)
        return loss

    def get_bbox_local_metric(self, bbox):
        x, y, w, h, yaw, speed, brake, confidence = bbox
        w = w / self.config.bounding_box_divisor / self.config.pixels_per_meter
        h = h / self.config.bounding_box_divisor / self.config.pixels_per_meter
        T = get_lidar_to_bevimage_transform()
        T_inv = np.linalg.inv(T)
        center = np.array([x, y, 1.0])
        center_old_coordinate_sys = T_inv @ center
        center_old_coordinate_sys = center_old_coordinate_sys + np.array(self.config.lidar_pos)
        center_old_coordinate_sys[1] = -center_old_coordinate_sys[1]
        bbox = np.array([[-h, -w, 1], [-h, w, 1], [h, w, 1], [h, -w, 1], [0, 0, 1], [0, h * speed * 0.5, 1]])
        R = np.array([[np.cos(yaw), -np.sin(yaw), 0], [np.sin(yaw), np.cos(yaw), 0], [0, 0, 1]])
        for point_index in range(bbox.shape[0]):
            bbox[point_index] = R @ bbox[point_index]
            bbox[point_index] = bbox[point_index] + np.array([center_old_coordinate_sys[0], center_old_coordinate_sys[1], 0])
        return (bbox, brake, confidence)

    def get_rotated_bbox(self, bbox):
        x, y, w, h, yaw, speed, brake = bbox
        bbox = np.array([[h, w, 1], [h, -w, 1], [-h, -w, 1], [-h, w, 1], [0, 0, 1], [-h * speed * 0.5, 0, 1]])
        bbox[:, :2] /= self.config.bounding_box_divisor
        bbox[:, :2] = bbox[:, [1, 0]]
        c, s = (np.cos(yaw), np.sin(yaw))
        r1_to_world = np.array([[c, -s, x], [s, c, y], [0, 0, 1]])
        bbox = r1_to_world @ bbox.T
        bbox = bbox.T
        return (bbox, brake)

    def draw_bboxes(self, bboxes, image, color=(255, 255, 255), brake_color=(0, 0, 255)):
        idx = [[0, 1], [1, 2], [2, 3], [3, 0], [4, 5]]
        for bbox, brake in bboxes:
            bbox = bbox.astype(np.int32)[:, :2]
            for s, e in idx:
                if brake >= self.config.draw_brake_threshhold:
                    color = brake_color
                else:
                    color = color
                cv2.line(image, tuple(bbox[s]), tuple(bbox[e]), color=color, thickness=1)
        return image

    def draw_waypoints(self, label, waypoints, image, color=(255, 255, 255)):
        waypoints = waypoints.detach().cpu().numpy()
        label = label.detach().cpu().numpy()
        for bbox, points in zip(label, waypoints):
            x, y, w, h, yaw, speed, brake = bbox
            c, s = (np.cos(yaw), np.sin(yaw))
            r1_to_world = np.array([[c, -s, x], [s, c, y], [0, 0, 1]])
            points[:, 0] *= -1
            points = points * self.config.pixels_per_meter
            points = points[:, [1, 0]]
            points = np.concatenate((points, np.ones_like(points[:, :1])), axis=-1)
            points = r1_to_world @ points.T
            points = points.T
            points_to_draw = []
            for point in points[:, :2]:
                points_to_draw.append(point.copy())
                point = point.astype(np.int32)
                cv2.circle(image, tuple(point), radius=3, color=color, thickness=3)
        return image

    def draw_target_point(self, target_point, image, color=(255, 255, 255)):
        target_point = target_point.copy()
        target_point[1] += self.config.lidar_pos[0]
        point = target_point * self.config.pixels_per_meter
        point[1] *= -1
        point[1] = self.config.lidar_resolution_width - point[1]
        point[0] += int(self.config.lidar_resolution_height / 2.0)
        point = point.astype(np.int32)
        point = np.clip(point, 0, 512)
        cv2.circle(image, tuple(point), radius=5, color=color, thickness=3)
        return image

    def visualize_model_io(self, save_path, step, config, rgb, lidar_bev, target_point, pred_wp, pred_bev, pred_semantic, pred_depth, bboxes, device, gt_bboxes=None, expert_waypoints=None, stuck_detector=0, forced_move=False):
        font = ImageFont.load_default()
        i = 0
        if config.multitask:
            classes_list = config.classes_list
            converter = np.array(classes_list)
            depth_image = pred_depth[i].detach().cpu().numpy()
            indices = np.argmax(pred_semantic.detach().cpu().numpy(), axis=1)
            semantic_image = converter[indices[i, ...], ...].astype('uint8')
            ds_image = np.stack((depth_image, depth_image, depth_image), axis=2)
            ds_image = (ds_image * 255).astype(np.uint8)
            ds_image = np.concatenate((ds_image, semantic_image), axis=0)
            ds_image = cv2.resize(ds_image, (640, 256))
            ds_image = np.concatenate([ds_image, np.zeros_like(ds_image[:50])], axis=0)
        images = np.concatenate(list(lidar_bev.detach().cpu().numpy()[i][:2]), axis=1)
        images = (images * 255).astype(np.uint8)
        images = np.stack([images, images, images], axis=-1)
        images = np.concatenate([images, np.zeros_like(images[:50])], axis=0)
        if not gt_bboxes is None:
            rotated_bboxes_gt = []
            for bbox in gt_bboxes.detach().cpu().numpy()[i]:
                bbox = self.get_rotated_bbox(bbox)
                rotated_bboxes_gt.append(bbox)
            images = self.draw_bboxes(rotated_bboxes_gt, images, color=(0, 255, 0), brake_color=(0, 255, 128))
        rotated_bboxes = []
        for bbox in bboxes.detach().cpu().numpy():
            bbox = self.get_rotated_bbox(bbox[:7])
            rotated_bboxes.append(bbox)
        images = self.draw_bboxes(rotated_bboxes, images, color=(255, 0, 0), brake_color=(0, 255, 255))
        label = torch.zeros((1, 1, 7)).to(device)
        label[:, -1, 0] = 128.0
        label[:, -1, 1] = 256.0
        if not expert_waypoints is None:
            images = self.draw_waypoints(label[0], expert_waypoints[i:i + 1], images, color=(0, 0, 255))
        images = self.draw_waypoints(label[0], deepcopy(pred_wp[i:i + 1, 2:]), images, color=(255, 255, 255))
        images = self.draw_waypoints(label[0], deepcopy(pred_wp[i:i + 1, :2]), images, color=(255, 0, 0))
        images = self.draw_target_point(target_point[i].detach().cpu().numpy(), images)
        images = Image.fromarray(images)
        draw = ImageDraw.Draw(images)
        draw.text((10, 0), 'stuck detector:   %04d' % stuck_detector, font=font)
        draw.text((10, 30), 'forced move:      %s' % (' True' if forced_move else 'False'), font=font, fill=(255, 0, 0, 255) if forced_move else (255, 255, 255, 255))
        images = np.array(images)
        bev = pred_bev[i].detach().cpu().numpy().argmax(axis=0) / 2.0
        bev = np.stack([bev, bev, bev], axis=2) * 255.0
        bev_image = bev.astype(np.uint8)
        bev_image = cv2.resize(bev_image, (256, 256))
        bev_image = np.concatenate([bev_image, np.zeros_like(bev_image[:50])], axis=0)
        if not expert_waypoints is None:
            bev_image = self.draw_waypoints(label[0], expert_waypoints[i:i + 1], bev_image, color=(0, 0, 255))
        bev_image = self.draw_waypoints(label[0], deepcopy(pred_wp[i:i + 1, 2:]), bev_image, color=(255, 255, 255))
        bev_image = self.draw_waypoints(label[0], deepcopy(pred_wp[i:i + 1, :2]), bev_image, color=(255, 0, 0))
        bev_image = self.draw_target_point(target_point[i].detach().cpu().numpy(), bev_image)
        if not expert_waypoints is None:
            aim = expert_waypoints[i:i + 1, :2].detach().cpu().numpy()[0].mean(axis=0)
            expert_angle = np.degrees(np.arctan2(aim[1], aim[0] + self.config.lidar_pos[0]))
            aim = pred_wp[i:i + 1, :2].detach().cpu().numpy()[0].mean(axis=0)
            ego_angle = np.degrees(np.arctan2(aim[1], aim[0] + self.config.lidar_pos[0]))
            angle_error = normalize_angle_degree(expert_angle - ego_angle)
            bev_image = Image.fromarray(bev_image)
            draw = ImageDraw.Draw(bev_image)
            draw.text((0, 0), 'Angle error:        %.2f°' % angle_error, font=font)
        bev_image = np.array(bev_image)
        rgb_image = rgb[i].permute(1, 2, 0).detach().cpu().numpy()[:, :, [2, 1, 0]]
        rgb_image = cv2.resize(rgb_image, (1280 + 128, 320 + 32))
        assert config.multitask
        images = np.concatenate((bev_image, images, ds_image), axis=1)
        images = np.concatenate((rgb_image, images), axis=0)
        cv2.imwrite(str(save_path + '/%d.png' % (step // 2)), images)

def __init__(self, config, device, backbone, image_architecture='resnet34', lidar_architecture='resnet18', use_velocity=True):
    super().__init__()
    self.device = device
    self.config = config
    self.pred_len = config.pred_len
    self.use_target_point_image = config.use_target_point_image
    self.gru_concat_target_point = config.gru_concat_target_point
    self.use_point_pillars = config.use_point_pillars
    if self.use_point_pillars == True:
        self.point_pillar_net = PointPillarNet(config.num_input, config.num_features, min_x=config.min_x, max_x=config.max_x, min_y=config.min_y, max_y=config.max_y, pixels_per_meter=int(config.pixels_per_meter))
    self.backbone = backbone
    if backbone == 'transFuser':
        self._model = TransfuserBackbone(config, image_architecture, lidar_architecture, use_velocity=use_velocity).to(self.device)
    elif backbone == 'late_fusion':
        self._model = LateFusionBackbone(config, image_architecture, lidar_architecture, use_velocity=use_velocity).to(self.device)
    elif backbone == 'geometric_fusion':
        self._model = GeometricFusionBackbone(config, image_architecture, lidar_architecture, use_velocity=use_velocity).to(self.device)
    elif backbone == 'latentTF':
        self._model = latentTFBackbone(config, image_architecture, lidar_architecture, use_velocity=use_velocity).to(self.device)
    else:
        raise 'The chosen vision backbone does not exist. The options are: transFuser, late_fusion, geometric_fusion, latentTF'
    if config.multitask:
        self.seg_decoder = SegDecoder(self.config, self.config.perception_output_features).to(self.device)
        self.depth_decoder = DepthDecoder(self.config, self.config.perception_output_features).to(self.device)
    channel = config.channel
    self.pred_bev = nn.Sequential(nn.Conv2d(channel, channel, kernel_size=(3, 3), stride=1, padding=(1, 1), bias=True), nn.ReLU(inplace=True), nn.Conv2d(channel, 3, kernel_size=(1, 1), stride=1, padding=0, bias=True)).to(self.device)
    self.head = LidarCenterNetHead(channel, channel, 1, train_cfg=config).to(self.device)
    self.i = 0
    self.join = nn.Sequential(nn.Linear(512, 256), nn.ReLU(inplace=True), nn.Linear(256, 128), nn.ReLU(inplace=True), nn.Linear(128, 64), nn.ReLU(inplace=True)).to(self.device)
    self.decoder = nn.GRUCell(input_size=4 if self.gru_concat_target_point else 2, hidden_size=self.config.gru_hidden_size).to(self.device)
    self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
    self.output = nn.Linear(self.config.gru_hidden_size, 3).to(self.device)
    self.turn_controller = PIDController(K_P=config.turn_KP, K_I=config.turn_KI, K_D=config.turn_KD, n=config.turn_n)
    self.speed_controller = PIDController(K_P=config.speed_KP, K_I=config.speed_KI, K_D=config.speed_KD, n=config.speed_n)

