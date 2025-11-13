# Cluster 35

def main():
    description = 'CARLA AD Leaderboard Evaluation: evaluate your Agent in CARLA scenarios\n'
    parser = argparse.ArgumentParser(description=description, formatter_class=RawTextHelpFormatter)
    parser.add_argument('--host', default='localhost', help='IP of the host server (default: localhost)')
    parser.add_argument('--port', default='2000', help='TCP port to listen to (default: 2000)')
    parser.add_argument('--trafficManagerPort', default='8000', help='Port to use for the TrafficManager (default: 8000)')
    parser.add_argument('--trafficManagerSeed', default='0', help='Seed used by the TrafficManager (default: 0)')
    parser.add_argument('--debug', type=int, help='Run with debug output', default=0)
    parser.add_argument('--record', type=str, default='', help='Use CARLA recording feature to create a recording of the scenario')
    parser.add_argument('--timeout', default='60.0', help='Set the CARLA client timeout value in seconds')
    parser.add_argument('--routes', help='Name of the route to be executed. Point to the route_xml_file to be executed.', required=True)
    parser.add_argument('--scenarios', help='Name of the scenario annotation file to be mixed with the route.', required=True)
    parser.add_argument('--repetitions', type=int, default=1, help='Number of repetitions per route.')
    parser.add_argument('-a', '--agent', type=str, help="Path to Agent's py file to evaluate", required=True)
    parser.add_argument('--agent-config', type=str, help="Path to Agent's configuration file", default='')
    parser.add_argument('--track', type=str, default='SENSORS', help='Participation track: SENSORS, MAP')
    parser.add_argument('--resume', type=bool, default=False, help='Resume execution from last checkpoint?')
    parser.add_argument('--checkpoint', type=str, default='./simulation_results.json', help='Path to checkpoint used for saving statistics and resuming')
    arguments = parser.parse_args()
    statistics_manager = StatisticsManager()
    try:
        leaderboard_evaluator = LeaderboardEvaluator(arguments, statistics_manager)
        leaderboard_evaluator.run(arguments)
    except Exception as e:
        traceback.print_exc()
    finally:
        del leaderboard_evaluator

def main():
    description = 'CARLA AD Leaderboard Evaluation: evaluate your Agent in CARLA scenarios\n'
    parser = argparse.ArgumentParser(description=description, formatter_class=RawTextHelpFormatter)
    parser.add_argument('--host', default='localhost', help='IP of the host server (default: localhost)')
    parser.add_argument('--port', default='2000', help='TCP port to listen to (default: 2000)')
    parser.add_argument('--trafficManagerPort', default='8000', help='Port to use for the TrafficManager (default: 8000)')
    parser.add_argument('--trafficManagerSeed', default='0', help='Seed used by the TrafficManager (default: 0)')
    parser.add_argument('--debug', type=int, help='Run with debug output', default=0)
    parser.add_argument('--record', type=str, default='', help='Use CARLA recording feature to create a recording of the scenario')
    parser.add_argument('--timeout', default='60.0', help='Set the CARLA client timeout value in seconds')
    parser.add_argument('--routes', help='Name of the route to be executed. Point to the route_xml_file to be executed.', required=True)
    parser.add_argument('--scenarios', help='Name of the scenario annotation file to be mixed with the route.', required=True)
    parser.add_argument('--repetitions', type=int, default=1, help='Number of repetitions per route.')
    parser.add_argument('-a', '--agent', type=str, help="Path to Agent's py file to evaluate", required=True)
    parser.add_argument('--agent-config', type=str, help="Path to Agent's configuration file", default='')
    parser.add_argument('--track', type=str, default='SENSORS', help='Participation track: SENSORS, MAP')
    parser.add_argument('--resume', type=bool, default=False, help='Resume execution from last checkpoint?')
    parser.add_argument('--checkpoint', type=str, default='./simulation_results.json', help='Path to checkpoint used for saving statistics and resuming')
    arguments = parser.parse_args()
    statistics_manager = StatisticsManager()
    try:
        leaderboard_evaluator = LeaderboardEvaluator(arguments, statistics_manager)
        leaderboard_evaluator.run(arguments)
    except Exception as e:
        traceback.print_exc()
    finally:
        del leaderboard_evaluator

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

def __init__(self, vehicle, reading_frequency=1.0):
    self._vehicle = vehicle
    self._reading_frequency = reading_frequency
    self._callback = None
    self._run_ps = True
    self.run()

def main():
    description = 'Create a human readable version of the scores provided by the leaderboard.\n'
    parser = argparse.ArgumentParser(description=description, formatter_class=RawTextHelpFormatter)
    parser.add_argument('-f', '--file', help='JSON file containing the results of the leaderboard', required=True)
    parser.add_argument('--format', default='fancy_grid', help='Format in which the table will be printed, e.g.: fancy_grid, latex, github, html, jira')
    parser.add_argument('-o', '--output', help='Output file to print the results into')
    arguments = parser.parse_args()
    return prettify_json(arguments)

def main():
    """
    main function
    """
    description = 'CARLA Scenario Runner: Setup, Run and Evaluate scenarios using CARLA\nCurrent version: ' + VERSION
    parser = argparse.ArgumentParser(description=description, formatter_class=RawTextHelpFormatter)
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + VERSION)
    parser.add_argument('--host', default='127.0.0.1', help='IP of the host server (default: localhost)')
    parser.add_argument('--port', default='2000', help='TCP port to listen to (default: 2000)')
    parser.add_argument('--timeout', default='10.0', help='Set the CARLA client timeout value in seconds')
    parser.add_argument('--trafficManagerPort', default='8000', help='Port to use for the TrafficManager (default: 8000)')
    parser.add_argument('--sync', action='store_true', help='Forces the simulation to run synchronously')
    parser.add_argument('--list', action='store_true', help='List all supported scenarios and exit')
    parser.add_argument('--scenario', help="Name of the scenario to be executed. Use the preposition 'group:' to run all scenarios of one class, e.g. ControlLoss or FollowLeadingVehicle")
    parser.add_argument('--openscenario', help='Provide an OpenSCENARIO definition')
    parser.add_argument('--route', help='Run a route as a scenario (input: (route_file,scenario_file,[route id]))', nargs='+', type=str)
    parser.add_argument('--agent', help='Agent used to execute the scenario. Currently only compatible with route-based scenarios.')
    parser.add_argument('--agentConfig', type=str, help="Path to Agent's configuration file", default='')
    parser.add_argument('--output', action='store_true', help='Provide results on stdout')
    parser.add_argument('--file', action='store_true', help='Write results into a txt file')
    parser.add_argument('--junit', action='store_true', help='Write results into a junit file')
    parser.add_argument('--outputDir', default='', help='Directory for output files (default: this directory)')
    parser.add_argument('--configFile', default='', help='Provide an additional scenario configuration file (*.xml)')
    parser.add_argument('--additionalScenario', default='', help='Provide additional scenario implementations (*.py)')
    parser.add_argument('--debug', action='store_true', help='Run with debug output')
    parser.add_argument('--reloadWorld', action='store_true', help='Reload the CARLA world before starting a scenario (default=True)')
    parser.add_argument('--record', type=str, default='', help='Path were the files will be saved, relative to SCENARIO_RUNNER_ROOT.\nActivates the CARLA recording feature and saves to file all the criteria information.')
    parser.add_argument('--randomize', action='store_true', help='Scenario parameters are randomized')
    parser.add_argument('--repetitions', default=1, type=int, help='Number of scenario executions')
    parser.add_argument('--waitForEgo', action='store_true', help='Connect the scenario to an existing ego vehicle')
    arguments = parser.parse_args()
    if arguments.list:
        print('Currently the following scenarios are supported:')
        print(*ScenarioConfigurationParser.get_list_of_scenarios(arguments.configFile), sep='\n')
        return 1
    if not arguments.scenario and (not arguments.openscenario) and (not arguments.route):
        print('Please specify either a scenario or use the route mode\n\n')
        parser.print_help(sys.stdout)
        return 1
    if arguments.route and (arguments.openscenario or arguments.scenario):
        print("The route mode cannot be used together with a scenario (incl. OpenSCENARIO)'\n\n")
        parser.print_help(sys.stdout)
        return 1
    if arguments.agent and (arguments.openscenario or arguments.scenario):
        print("Agents are currently only compatible with route scenarios'\n\n")
        parser.print_help(sys.stdout)
        return 1
    if arguments.route:
        arguments.reloadWorld = True
    if arguments.agent:
        arguments.sync = True
    scenario_runner = None
    result = True
    try:
        scenario_runner = ScenarioRunner(arguments)
        result = scenario_runner.run()
    finally:
        if scenario_runner is not None:
            scenario_runner.destroy()
            del scenario_runner
    return not result

def main():
    argparser = argparse.ArgumentParser(description='CARLA Manual Control Client')
    argparser.add_argument('-v', '--verbose', action='store_true', dest='debug', help='print debug information')
    argparser.add_argument('--host', metavar='H', default='127.0.0.1', help='IP of the host server (default: 127.0.0.1)')
    argparser.add_argument('-p', '--port', metavar='P', default=2000, type=int, help='TCP port to listen to (default: 2000)')
    argparser.add_argument('-a', '--autopilot', action='store_true', help='enable autopilot')
    argparser.add_argument('--res', metavar='WIDTHxHEIGHT', default='1280x720', help='window resolution (default: 1280x720)')
    args = argparser.parse_args()
    args.rolename = 'hero'
    args.filter = 'vehicle.*'
    args.gamma = 2.2
    args.width, args.height = [int(x) for x in args.res.split('x')]
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(format='%(levelname)s: %(message)s', level=log_level)
    logging.info('listening to server %s:%s', args.host, args.port)
    print(__doc__)
    try:
        game_loop(args)
    except KeyboardInterrupt:
        print('\nCancelled by user. Bye!')
    except Exception as error:
        logging.exception(error)

def main():
    """
    main function
    """
    description = "Scenario Runner's metrics module. Evaluate the execution of a specific scenario by developing your own metric.\n"
    parser = argparse.ArgumentParser(description=description, formatter_class=RawTextHelpFormatter)
    parser.add_argument('--host', default='127.0.0.1', help='IP of the host server (default: localhost)')
    parser.add_argument('--port', '-p', default=2000, help='TCP port to listen to (default: 2000)')
    parser.add_argument('--log', required=True, help='Path to the CARLA recorder .log file (relative to SCENARIO_RUNNER_ROOT).\nThis file is created by the record functionality at ScenarioRunner')
    parser.add_argument('--metric', required=True, help='Path to the .py file defining the used metric.\nSome examples at srunner/metrics')
    parser.add_argument('--criteria', default='', help='Path to the .json file with the criteria information.\nThis file is created by the record functionality at ScenarioRunner')
    args = parser.parse_args()
    MetricsManager(args)

def main():
    argparser = argparse.ArgumentParser(description='CARLA No Rendering Mode Visualizer')
    argparser.add_argument('-v', '--verbose', action='store_true', dest='debug', help='print debug information')
    argparser.add_argument('--host', metavar='H', default='127.0.0.1', help='IP of the host server (default: 127.0.0.1)')
    argparser.add_argument('-p', '--port', metavar='P', default=2000, type=int, help='TCP port to listen to (default: 2000)')
    argparser.add_argument('--res', metavar='WIDTHxHEIGHT', default='1280x720', help='window resolution (default: 1280x720)')
    argparser.add_argument('--filter', metavar='PATTERN', default='vehicle.*', help='actor filter (default: "vehicle.*")')
    argparser.add_argument('--map', metavar='TOWN', default=None, help='start a new episode at the given TOWN')
    argparser.add_argument('--no-rendering', action='store_true', default=True, help='switch off server rendering')
    argparser.add_argument('--show-triggers', action='store_true', help='show trigger boxes of traffic signs')
    argparser.add_argument('--show-connections', action='store_true', help='show waypoint connections')
    argparser.add_argument('--show-spawn-points', action='store_true', help='show recommended spawn points')
    args = argparser.parse_args()
    args.description = argparser.description
    args.width, args.height = [int(x) for x in args.res.split('x')]
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(format='%(levelname)s: %(message)s', level=log_level)
    logging.info('listening to server %s:%s', args.host, args.port)
    print(__doc__)
    game_loop(args)

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

@record
def main():
    torch.cuda.empty_cache()
    parser = argparse.ArgumentParser()
    parser.add_argument('--id', type=str, default='transfuser', help='Unique experiment identifier.')
    parser.add_argument('--epochs', type=int, default=41, help='Number of train epochs.')
    parser.add_argument('--lr', type=float, default=0.0001, help='Learning rate.')
    parser.add_argument('--batch_size', type=int, default=12, help='Batch size for one GPU. When training with multiple GPUs the effective batch size will be batch_size*num_gpus')
    parser.add_argument('--logdir', type=str, default='log', help='Directory to log data to.')
    parser.add_argument('--load_file', type=str, default=None, help='ckpt to load.')
    parser.add_argument('--start_epoch', type=int, default=0, help='Epoch to start with. Useful when continuing trainings via load_file.')
    parser.add_argument('--setting', type=str, default='all', help='What training setting to use. Options: all: Train on all towns no validation data. 02_05_withheld: Do not train on Town 02 and Town 05. Use the data as validation data.')
    parser.add_argument('--root_dir', type=str, default='/mnt/qb/geiger/kchitta31/datasets/carla/pami_v1_dataset_23_11', help='Root directory of your training data')
    parser.add_argument('--schedule', type=int, default=1, help='Whether to train with a learning rate schedule. 1 = True')
    parser.add_argument('--schedule_reduce_epoch_01', type=int, default=30, help='Epoch at which to reduce the lr by a factor of 10 the first time. Only used with --schedule 1')
    parser.add_argument('--schedule_reduce_epoch_02', type=int, default=40, help='Epoch at which to reduce the lr by a factor of 10 the second time. Only used with --schedule 1')
    parser.add_argument('--backbone', type=str, default='transFuser', help='Which Fusion backbone to use. Options: transFuser, late_fusion, latentTF, geometric_fusion')
    parser.add_argument('--image_architecture', type=str, default='regnety_032', help='Which architecture to use for the image branch. efficientnet_b0, resnet34, regnety_032 etc.')
    parser.add_argument('--lidar_architecture', type=str, default='regnety_032', help='Which architecture to use for the lidar branch. Tested: efficientnet_b0, resnet34, regnety_032 etc.')
    parser.add_argument('--use_velocity', type=int, default=0, help='Whether to use the velocity input. Currently only works with the TransFuser backbone. Expected values are 0:False, 1:True')
    parser.add_argument('--n_layer', type=int, default=4, help='Number of transformer layers used in the transfuser')
    parser.add_argument('--wp_only', type=int, default=0, help='Valid values are 0, 1. 1 = using only the wp loss; 0= using all losses')
    parser.add_argument('--use_target_point_image', type=int, default=1, help='Valid values are 0, 1. 1 = using target point in the LiDAR0; 0 = dont do it')
    parser.add_argument('--use_point_pillars', type=int, default=0, help='Whether to use the point_pillar lidar encoder instead of voxelization. 0:False, 1:True')
    parser.add_argument('--parallel_training', type=int, default=1, help='If this is true/1 you need to launch the train.py script with CUDA_VISIBLE_DEVICES=0,1 torchrun --nnodes=1 --nproc_per_node=2 --max_restarts=0 --rdzv_id=123456780 --rdzv_backend=c10d train.py  the code will be parallelized across GPUs. If set to false/0, you launch the script with python train.py and only 1 GPU will be used.')
    parser.add_argument('--val_every', type=int, default=5, help='At which epoch frequency to validate.')
    parser.add_argument('--no_bev_loss', type=int, default=0, help='If set to true the BEV loss will not be trained. 0: Train normally, 1: set training weight for BEV to 0')
    parser.add_argument('--sync_batch_norm', type=int, default=0, help='0: Compute batch norm for each GPU independently, 1: Synchronize Batch norms accross GPUs. Only use with --parallel_training 1')
    parser.add_argument('--zero_redundancy_optimizer', type=int, default=0, help='0: Normal AdamW Optimizer, 1: Use Zero Reduncdancy Optimizer to reduce memory footprint. Only use with --parallel_training 1')
    parser.add_argument('--use_disk_cache', type=int, default=0, help='0: Do not cache the dataset 1: Cache the dataset on the disk pointed to by the SCRATCH enironment variable. Useful if the dataset is stored on slow HDDs and can be temporarily stored on faster SSD storage.')
    args = parser.parse_args()
    args.logdir = os.path.join(args.logdir, args.id)
    parallel = bool(args.parallel_training)
    if bool(args.use_disk_cache) == True:
        if parallel == True:
            tmp_folder = str(os.environ.get('SCRATCH'))
            print('Tmp folder for dataset cache: ', tmp_folder)
            tmp_folder = tmp_folder + '/dataset_cache'
            shared_dict = Cache(directory=tmp_folder, size_limit=int(768 * 1024 ** 3))
        else:
            shared_dict = Cache(size_limit=int(768 * 1024 ** 3))
    else:
        shared_dict = None
    if parallel == True:
        rank = int(os.environ['RANK'])
        local_rank = int(os.environ['LOCAL_RANK'])
        world_size = int(os.environ['WORLD_SIZE'])
        print(f'RANK, LOCAL_RANK and WORLD_SIZE in environ: {rank}/{local_rank}/{world_size}')
        device = torch.device('cuda:{}'.format(local_rank))
        os.environ['CUDA_VISIBLE_DEVICES'] = str(local_rank)
        torch.distributed.init_process_group(backend='nccl', init_method='env://', world_size=world_size, rank=rank, timeout=datetime.timedelta(minutes=15))
        torch.distributed.barrier(device_ids=[local_rank])
    else:
        rank = 0
        local_rank = 0
        world_size = 1
        device = torch.device('cuda:{}'.format(local_rank))
    torch.cuda.set_device(device)
    torch.backends.cudnn.benchmark = True
    config = GlobalConfig(root_dir=args.root_dir, setting=args.setting)
    config.use_target_point_image = bool(args.use_target_point_image)
    config.n_layer = args.n_layer
    config.use_point_pillars = bool(args.use_point_pillars)
    config.backbone = args.backbone
    if bool(args.no_bev_loss):
        index_bev = config.detailed_losses.index('loss_bev')
        config.detailed_losses_weights[index_bev] = 0.0
    model = LidarCenterNet(config, device, args.backbone, args.image_architecture, args.lidar_architecture, bool(args.use_velocity))
    if parallel == True:
        if bool(args.sync_batch_norm) == True:
            model = torch.nn.SyncBatchNorm.convert_sync_batchnorm(model)
        model = torch.nn.parallel.DistributedDataParallel(model, device_ids=[local_rank], output_device=local_rank, broadcast_buffers=False, find_unused_parameters=False)
    model.cuda(device=device)
    if bool(args.zero_redundancy_optimizer) == True and parallel == True:
        optimizer = ZeroRedundancyOptimizer(model.parameters(), optimizer_class=optim.AdamW, lr=args.lr)
    else:
        optimizer = optim.AdamW(model.parameters(), lr=args.lr)
    model_parameters = filter(lambda p: p.requires_grad, model.parameters())
    params = sum([np.prod(p.size()) for p in model_parameters])
    print('Total trainable parameters: ', params)
    train_set = CARLA_Data(root=config.train_data, config=config, shared_dict=shared_dict)
    val_set = CARLA_Data(root=config.val_data, config=config, shared_dict=shared_dict)
    g_cuda = torch.Generator(device='cpu')
    g_cuda.manual_seed(torch.initial_seed())
    if parallel == True:
        sampler_train = torch.utils.data.distributed.DistributedSampler(train_set, shuffle=True, num_replicas=world_size, rank=rank)
        sampler_val = torch.utils.data.distributed.DistributedSampler(val_set, shuffle=True, num_replicas=world_size, rank=rank)
        dataloader_train = DataLoader(train_set, sampler=sampler_train, batch_size=args.batch_size, worker_init_fn=seed_worker, generator=g_cuda, num_workers=8, pin_memory=True)
        dataloader_val = DataLoader(val_set, sampler=sampler_val, batch_size=args.batch_size, worker_init_fn=seed_worker, generator=g_cuda, num_workers=8, pin_memory=True)
    else:
        dataloader_train = DataLoader(train_set, shuffle=True, batch_size=args.batch_size, worker_init_fn=seed_worker, generator=g_cuda, num_workers=0, pin_memory=True)
        dataloader_val = DataLoader(val_set, shuffle=True, batch_size=args.batch_size, worker_init_fn=seed_worker, generator=g_cuda, num_workers=0, pin_memory=True)
    if not os.path.isdir(args.logdir) and rank == 0:
        print('Created dir:', args.logdir, rank)
        os.makedirs(args.logdir, exist_ok=True)
    if rank == 0:
        writer = SummaryWriter(log_dir=args.logdir)
        with open(os.path.join(args.logdir, 'args.txt'), 'w') as f:
            json.dump(args.__dict__, f, indent=2)
    else:
        writer = None
    if not args.load_file is None:
        print('=============load=================')
        model.load_state_dict(torch.load(args.load_file, map_location=model.device))
        optimizer.load_state_dict(torch.load(args.load_file.replace('model_', 'optimizer_'), map_location=model.device))
    trainer = Engine(model=model, optimizer=optimizer, dataloader_train=dataloader_train, dataloader_val=dataloader_val, args=args, config=config, writer=writer, device=device, rank=rank, world_size=world_size, parallel=parallel, cur_epoch=args.start_epoch)
    for epoch in range(trainer.cur_epoch, args.epochs):
        if parallel == True:
            sampler_train.set_epoch(epoch)
        if (epoch == args.schedule_reduce_epoch_01 or epoch == args.schedule_reduce_epoch_02) and args.schedule == 1:
            current_lr = optimizer.param_groups[0]['lr']
            new_lr = current_lr * 0.1
            print('Reduce learning rate by factor 10 to:', new_lr)
            for g in optimizer.param_groups:
                g['lr'] = new_lr
        trainer.train()
        if args.setting != 'all' and epoch % args.val_every == 0:
            trainer.validate()
        if parallel == True:
            if bool(args.zero_redundancy_optimizer) == True:
                optimizer.consolidate_state_dict(0)
            if rank == 0:
                trainer.save()
        else:
            trainer.save()

def seed_worker(worker_id):
    worker_seed = torch.initial_seed() % 2 ** 32
    np.random.seed(worker_seed)
    random.seed(worker_seed)

