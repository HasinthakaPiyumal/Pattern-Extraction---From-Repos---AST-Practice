# Cluster 20

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

def update(self):
    """
        Upon reaching the timeout value the status changes to SUCCESS
        """
    new_status = super(TimeOut, self).update()
    if new_status == py_trees.common.Status.SUCCESS:
        self.timeout = True
    return new_status

class Weather(object):
    """
    Class to simulate weather in CARLA according to the astronomic behavior of the sun

    The sun position (azimuth and altitude angles) is obtained by calculating its
    astronomic position for the CARLA reference position (x=0, y=0, z=0) using the ephem
    library.

    Args:
        carla_weather (carla.WeatherParameters): Initial weather settings.
        dtime (datetime): Initial date and time in UTC (required for animation only).
            Defaults to None.
        animation (bool): Flag to allow animating the sun position over time.
            Defaults to False.

    Attributes:
        carla_weather (carla.WeatherParameters): Weather parameters for CARLA.
        animation (bool): Flag to allow animating the sun position over time.
        _sun (ephem.Sun): The sun as astronomic entity.
        _observer_location (ephem.Observer): Holds the geographical position (lat/lon/altitude)
            for which the sun position is obtained.
        datetime (datetime): Date and time in UTC (required for animation only).
    """

    def __init__(self, carla_weather, dtime=None, animation=False):
        """
        Class constructor
        """
        self.carla_weather = carla_weather
        self.animation = animation
        self._sun = ephem.Sun()
        self._observer_location = ephem.Observer()
        geo_location = CarlaDataProvider.get_map().transform_to_geolocation(carla.Location(0, 0, 0))
        self._observer_location.lon = str(geo_location.longitude)
        self._observer_location.lat = str(geo_location.latitude)
        self.datetime = dtime
        if self.datetime:
            self._observer_location.date = self.datetime
        self.update()

    def update(self, delta_time=0):
        """
        If the weather animation is true, the new sun position is calculated w.r.t delta_time

        Nothing happens if animation or datetime are None.

        Args:
            delta_time (float): Time passed since self.datetime [seconds].
        """
        if not self.animation or not self.datetime:
            return
        self.datetime = self.datetime + datetime.timedelta(seconds=delta_time)
        self._observer_location.date = self.datetime
        self._sun.compute(self._observer_location)
        self.carla_weather.sun_altitude_angle = math.degrees(self._sun.alt)
        self.carla_weather.sun_azimuth_angle = math.degrees(self._sun.az)

def __init__(self, carla_weather, dtime=None, animation=False):
    """
        Class constructor
        """
    self.carla_weather = carla_weather
    self.animation = animation
    self._sun = ephem.Sun()
    self._observer_location = ephem.Observer()
    geo_location = CarlaDataProvider.get_map().transform_to_geolocation(carla.Location(0, 0, 0))
    self._observer_location.lon = str(geo_location.longitude)
    self._observer_location.lat = str(geo_location.latitude)
    self.datetime = dtime
    if self.datetime:
        self._observer_location.date = self.datetime
    self.update()

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

def get_actor_velocity(self, actor_id, frame):
    """
        Returns the velocity of the actor at a given frame.
        """
    return self._get_actor_state(actor_id, 'velocity', frame)

def get_actor_angular_velocity(self, actor_id, frame):
    """
        Returns the angular velocity of the actor at a given frame.
        """
    return self._get_actor_state(actor_id, 'angular_velocity', frame)

def get_actor_acceleration(self, actor_id, frame):
    """
        Returns the acceleration of the actor at a given frame.
        """
    return self._get_actor_state(actor_id, 'acceleration', frame)

def get_vehicle_control(self, vehicle_id, frame):
    """
        Returns the control of the vehicle at a given frame.
        """
    return self._get_actor_state(vehicle_id, 'control', frame)

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

def get_vehicle_lights(self, vehicle_id, frame):
    """
        Returns the vehicle lights of the vehicle at a specific frame.
        """
    return self._get_actor_state(vehicle_id, 'lights', frame)

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
                convert_waypoint_float(waypoint)
                match_position = match_world_location_to_route(waypoint, trajectory)
                if match_position is not None:
                    if 'other_actors' in event:
                        other_vehicles = event['other_actors']
                    else:
                        other_vehicles = None
                    scenario_subtype = get_scenario_type(scenario_name, match_position, trajectory)
                    if scenario_subtype is None:
                        continue
                    scenario_description = {'name': scenario_name, 'other_actors': other_vehicles, 'trigger_position': waypoint, 'scenario_type': scenario_subtype}
                    trigger_id = check_trigger_position(waypoint, existent_triggers)
                    if trigger_id is None:
                        existent_triggers.update({latest_trigger_id: waypoint})
                        possible_scenarios.update({latest_trigger_id: []})
                        trigger_id = latest_trigger_id
                        latest_trigger_id += 1
                    possible_scenarios[trigger_id].append(scenario_description)
    return (possible_scenarios, existent_triggers)

