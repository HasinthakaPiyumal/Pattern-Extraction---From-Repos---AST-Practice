# Cluster 22

def _location_to_gps(lat_ref, lon_ref, location):
    """
    Convert from world coordinates to GPS coordinates
    :param lat_ref: latitude reference for the current map
    :param lon_ref: longitude reference for the current map
    :param location: location to translate
    :return: dictionary with lat, lon and height
    """
    EARTH_RADIUS_EQUA = 6378137.0
    scale = math.cos(lat_ref * math.pi / 180.0)
    mx = scale * lon_ref * math.pi * EARTH_RADIUS_EQUA / 180.0
    my = scale * EARTH_RADIUS_EQUA * math.log(math.tan((90.0 + lat_ref) * math.pi / 360.0))
    mx += location.x
    my -= location.y
    lon = mx * 180.0 / (math.pi * EARTH_RADIUS_EQUA * scale)
    lat = 360.0 * math.atan(math.exp(my / (EARTH_RADIUS_EQUA * scale))) / math.pi - 90.0
    z = location.z
    return {'lat': lat, 'lon': lon, 'z': z}

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

def get_opponent_transform(added_dist, waypoint, trigger_location):
    """
    Calculate the transform of the adversary
    """
    lane_width = waypoint.lane_width
    offset = {'orientation': 270, 'position': 90, 'k': 1.0}
    _wp = waypoint.next(added_dist)
    if _wp:
        _wp = _wp[-1]
    else:
        raise RuntimeError('Cannot get next waypoint !')
    location = _wp.transform.location
    orientation_yaw = _wp.transform.rotation.yaw + offset['orientation']
    position_yaw = _wp.transform.rotation.yaw + offset['position']
    offset_location = carla.Location(offset['k'] * lane_width * math.cos(math.radians(position_yaw)), offset['k'] * lane_width * math.sin(math.radians(position_yaw)))
    location += offset_location
    location.z = trigger_location.z
    transform = carla.Transform(location, carla.Rotation(yaw=orientation_yaw))
    return transform

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

def rotate_point(point, angle):
    """
            rotate a given point by a given angle
            """
    x_ = math.cos(math.radians(angle)) * point.x - math.sin(math.radians(angle)) * point.y
    y_ = math.sin(math.radians(angle)) * point.x - math.cos(math.radians(angle)) * point.y
    return carla.Vector3D(x_, y_, point.z)

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

def rotate_point(self, point, angle):
    """
        rotate a given point by a given angle
        """
    x_ = math.cos(math.radians(angle)) * point.x - math.sin(math.radians(angle)) * point.y
    y_ = math.sin(math.radians(angle)) * point.x + math.cos(math.radians(angle)) * point.y
    return carla.Vector3D(x_, y_, point.z)

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

def initialise(self):
    super(ActorTransformSetterToOSCPosition, self).initialise()
    if self._actor.is_alive:
        self._actor.set_target_velocity(carla.Vector3D(0, 0, 0))
        self._actor.set_target_angular_velocity(carla.Vector3D(0, 0, 0))

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

def initialise(self):
    """
        Initialize it's speed
        """
    transform = self._actor.get_transform()
    yaw = transform.rotation.yaw * (math.pi / 180)
    vx = math.cos(yaw) * self._init_speed
    vy = math.sin(yaw) * self._init_speed
    self._actor.set_target_velocity(carla.Vector3D(vx, vy, 0))

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

def initialise(self):
    if self._actor.is_alive:
        self._actor.set_target_velocity(carla.Vector3D(0, 0, 0))
        self._actor.set_target_angular_velocity(carla.Vector3D(0, 0, 0))
        self._actor.set_transform(self._transform)
    super(ActorTransformSetter, self).initialise()

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

def rotate_point(self, point, angle):
    """
        rotate a given point by a given angle
        """
    x_ = math.cos(math.radians(angle)) * point.x - math.sin(math.radians(angle)) * point.y
    y_ = math.sin(math.radians(angle)) * point.x + math.cos(math.radians(angle)) * point.y
    return carla.Vector3D(x_, y_, point.z)

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

def run_step(self):
    """
        Execute on tick of the controller's control loop
        """
    self.control_instance.run_step()

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

def generate_target_waypoint_list(waypoint, turn=0):
    """
    This method follow waypoints to a junction and choose path based on turn input.
    Turn input: LEFT -> -1, RIGHT -> 1, STRAIGHT -> 0
    @returns a waypoint list from the starting point to the end point according to turn input
    """
    reached_junction = False
    threshold = math.radians(0.1)
    plan = []
    while True:
        wp_choice = waypoint.next(2)
        if len(wp_choice) > 1:
            reached_junction = True
            waypoint = choose_at_junction(waypoint, wp_choice, turn)
        else:
            waypoint = wp_choice[0]
        plan.append((waypoint, RoadOption.LANEFOLLOW))
        if turn != 0 and reached_junction and (len(plan) >= 3):
            v_1 = vector(plan[-2][0].transform.location, plan[-1][0].transform.location)
            v_2 = vector(plan[-3][0].transform.location, plan[-2][0].transform.location)
            angle_wp = math.acos(np.dot(v_1, v_2) / abs(np.linalg.norm(v_1) * np.linalg.norm(v_2)))
            if angle_wp < threshold:
                break
        elif reached_junction and (not plan[-1][0].is_intersection):
            break
    return (plan, plan[-1][0])

def choose_at_junction(current_waypoint, next_choices, direction=0):
    """
    This function chooses the appropriate waypoint from next_choices based on direction
    """
    current_transform = current_waypoint.transform
    current_location = current_transform.location
    projected_location = current_location + carla.Location(x=math.cos(math.radians(current_transform.rotation.yaw)), y=math.sin(math.radians(current_transform.rotation.yaw)))
    current_vector = vector(current_location, projected_location)
    cross_list = []
    cross_to_waypoint = dict()
    for waypoint in next_choices:
        waypoint = waypoint.next(10)[0]
        select_vector = vector(current_location, waypoint.transform.location)
        cross = np.cross(current_vector, select_vector)[2]
        cross_list.append(cross)
        cross_to_waypoint[cross] = waypoint
    select_cross = None
    if direction > 0:
        select_cross = max(cross_list)
    elif direction < 0:
        select_cross = min(cross_list)
    else:
        select_cross = min(cross_list, key=abs)
    return cross_to_waypoint[select_cross]

def get_intersection(ego_actor, other_actor):
    """
    Obtain a intersection point between two actor's location
    @return the intersection location
    """
    waypoint = CarlaDataProvider.get_map().get_waypoint(ego_actor.get_location())
    waypoint_other = CarlaDataProvider.get_map().get_waypoint(other_actor.get_location())
    max_dist = float('inf')
    distance = float('inf')
    while distance <= max_dist:
        max_dist = distance
        current_location = waypoint.transform.location
        waypoint_choice = waypoint.next(1)
        if len(waypoint_choice) > 1:
            max_dot = -1 * float('inf')
            loc_projection = current_location + carla.Location(x=math.cos(math.radians(waypoint.transform.rotation.yaw)), y=math.sin(math.radians(waypoint.transform.rotation.yaw)))
            v_current = vector(current_location, loc_projection)
            for wp_select in waypoint_choice:
                v_select = vector(current_location, wp_select.transform.location)
                dot_select = np.dot(v_current, v_select)
                if dot_select > max_dot:
                    max_dot = dot_select
                    waypoint = wp_select
        else:
            waypoint = waypoint_choice[0]
        distance = current_location.distance(waypoint_other.transform.location)
    return current_location

def _location_to_gps(lat_ref, lon_ref, location):
    """
    Convert from world coordinates to GPS coordinates
    :param lat_ref: latitude reference for the current map
    :param lon_ref: longitude reference for the current map
    :param location: location to translate
    :return: dictionary with lat, lon and height
    """
    EARTH_RADIUS_EQUA = 6378137.0
    scale = math.cos(lat_ref * math.pi / 180.0)
    mx = scale * lon_ref * math.pi * EARTH_RADIUS_EQUA / 180.0
    my = scale * EARTH_RADIUS_EQUA * math.log(math.tan((90.0 + lat_ref) * math.pi / 360.0))
    mx += location.x
    my -= location.y
    lon = mx * 180.0 / (math.pi * EARTH_RADIUS_EQUA * scale)
    lat = 360.0 * math.atan(math.exp(my / (EARTH_RADIUS_EQUA * scale))) / math.pi - 90.0
    z = location.z
    return {'lat': lat, 'lon': lon, 'z': z}

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

def parse_vehicle_lights(info):
    """
    Parses a list into a carla.VehicleLightState

    Args:
        info (list): list corresponding to a row of the recorder
    """
    srt_to_vlight = {'None': carla.VehicleLightState.NONE, 'Position': carla.VehicleLightState.Position, 'LowBeam': carla.VehicleLightState.LowBeam, 'HighBeam': carla.VehicleLightState.HighBeam, 'Brake': carla.VehicleLightState.Brake, 'RightBlinker': carla.VehicleLightState.RightBlinker, 'LeftBlinker': carla.VehicleLightState.LeftBlinker, 'Reverse': carla.VehicleLightState.Reverse, 'Fog': carla.VehicleLightState.Fog, 'Interior': carla.VehicleLightState.Interior, 'Special1': carla.VehicleLightState.Special1, 'Special2': carla.VehicleLightState.Special2}
    lights = []
    for i in range(2, len(info)):
        lights.append(srt_to_vlight[info[i]])
    return lights

def parse_velocity(info):
    """
    Parses a list into a carla.Vector3D with the velocity

    Args:
        info (list): list corresponding to a row of the recorder
    """
    velocity = carla.Vector3D(float(info[3][1:-1]), float(info[4][:-1]), float(info[5][:-1]))
    return velocity

def parse_angular_velocity(info):
    """
    Parses a list into a carla.Vector3D with the angular velocity

    Args:
        info (list): list corresponding to a row of the recorder
    """
    velocity = carla.Vector3D(float(info[7][1:-1]), float(info[8][:-1]), float(info[9][:-1]))
    return velocity

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

def tick(self, input_data):
    gps = input_data['gps'][1][:2]
    speed = input_data['speed'][1]['speed']
    compass = input_data['imu'][1][-1]
    if math.isnan(compass) == True:
        compass = 0.0
    result = {'gps': gps, 'speed': speed, 'compass': compass}
    return result

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

def cross_product(self, vector1, vector2):
    return carla.Vector3D(x=vector1.y * vector2.z - vector1.z * vector2.y, y=vector1.z * vector2.x - vector1.x * vector2.z, z=vector1.x * vector2.y - vector1.y * vector2.x)

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

class EgoModel:

    def __init__(self, dt=1.0 / 4):
        self.dt = dt
        self.front_wb = -0.090769015
        self.rear_wb = 1.4178275
        self.steer_gain = 0.36848336
        self.brake_accel = -4.952399
        self.throt_accel = 0.5633837

    def forward(self, locs, yaws, spds, acts):
        steer = acts[..., 0:1].item()
        throt = acts[..., 1:2].item()
        brake = acts[..., 2:3].astype(np.uint8)
        if brake:
            accel = self.brake_accel
        else:
            accel = self.throt_accel * throt
        wheel = self.steer_gain * steer
        beta = math.atan(self.rear_wb / (self.front_wb + self.rear_wb) * math.tan(wheel))
        yaws = yaws.item()
        spds = spds.item()
        next_locs_0 = locs[0].item() + spds * math.cos(yaws + beta) * self.dt
        next_locs_1 = locs[1].item() + spds * math.sin(yaws + beta) * self.dt
        next_yaws = yaws + spds / self.rear_wb * math.sin(beta) * self.dt
        next_spds = spds + accel * self.dt
        next_spds = next_spds * (next_spds > 0.0)
        next_locs = np.array([next_locs_0, next_locs_1])
        next_yaws = np.array(next_yaws)
        next_spds = np.array(next_spds)
        return (next_locs, next_yaws, next_spds)

def forward(self, locs, yaws, spds, acts):
    steer = acts[..., 0:1].item()
    throt = acts[..., 1:2].item()
    brake = acts[..., 2:3].astype(np.uint8)
    if brake:
        accel = self.brake_accel
    else:
        accel = self.throt_accel * throt
    wheel = self.steer_gain * steer
    beta = math.atan(self.rear_wb / (self.front_wb + self.rear_wb) * math.tan(wheel))
    yaws = yaws.item()
    spds = spds.item()
    next_locs_0 = locs[0].item() + spds * math.cos(yaws + beta) * self.dt
    next_locs_1 = locs[1].item() + spds * math.sin(yaws + beta) * self.dt
    next_yaws = yaws + spds / self.rear_wb * math.sin(beta) * self.dt
    next_spds = spds + accel * self.dt
    next_spds = next_spds * (next_spds > 0.0)
    next_locs = np.array([next_locs_0, next_locs_1])
    next_yaws = np.array(next_yaws)
    next_spds = np.array(next_spds)
    return (next_locs, next_yaws, next_spds)

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

def clear(self):
    from PIL import Image, ImageDraw
    self.img = Image.fromarray(np.zeros((self.size, self.size, 3), dtype=np.uint8))
    self.draw = ImageDraw.Draw(self.img)

def show(self):
    if not DEBUG:
        return
    import cv2
    cv2.imshow(self.title, cv2.cvtColor(np.array(self.img), cv2.COLOR_BGR2RGB))
    cv2.waitKey(1)

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

def _location_to_gps(lat_ref, lon_ref, location):
    """
    Convert from world coordinates to GPS coordinates
    :param lat_ref: latitude reference for the current map
    :param lon_ref: longitude reference for the current map
    :param location: location to translate
    :return: dictionary with lat, lon and height
    """
    EARTH_RADIUS_EQUA = 6378137.0
    scale = math.cos(lat_ref * math.pi / 180.0)
    mx = scale * lon_ref * math.pi * EARTH_RADIUS_EQUA / 180.0
    my = scale * EARTH_RADIUS_EQUA * math.log(math.tan((90.0 + lat_ref) * math.pi / 360.0))
    mx += location.x
    my -= location.y
    lon = mx * 180.0 / (math.pi * EARTH_RADIUS_EQUA * scale)
    lat = 360.0 * math.atan(math.exp(my / (EARTH_RADIUS_EQUA * scale))) / math.pi - 90.0
    z = location.z
    return {'lat': lat, 'lon': lon, 'z': z}

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

def save_points(self, filename, points):
    points_to_save = deepcopy(points[1])
    points_to_save[:, 1] = -points_to_save[:, 1]
    np.save(filename, points_to_save)
    return

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

def get_image_to_vehicle_transform(self):
    T = np.eye(4)
    T[0, 3] = 1.3
    T[1, 3] = 0.0
    T[2, 3] = 2.3
    rot = np.array([[0, -1, 0], [0, 0, -1], [1, 0, 0]], dtype=np.float32)
    T[:3, :3] = rot.T
    return T

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

def encode_npy_to_pil(bev_array):
    """
        Encode BEV array with 15 channels to 3 channels -> each channel is rpresented by one bit.
    """
    channels, width, height = (bev_array.shape[0], bev_array.shape[1], bev_array.shape[2])
    img = np.zeros([3, width, height]).astype('uint8')
    bev = np.ceil(bev_array).astype('uint8')
    for i in range(channels):
        if i <= 4 and i >= 0:
            img[0] = img[0] | bev[i] << 8 - i - 1
        elif i <= 9 and i >= 5:
            img[1] = img[1] | bev[i] << 8 - (i - 5) - 1
        elif i <= 14 and i >= 10:
            img[2] = img[2] | bev[i] << 8 - (i - 10) - 1
    return img

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

def normalize_imagenet(x):
    """ Normalize input images according to ImageNet standards.
    Args:
        x (tensor): input images
    """
    x = x.clone()
    x[:, 0] = (x[:, 0] / 255.0 - 0.485) / 0.229
    x[:, 1] = (x[:, 1] / 255.0 - 0.456) / 0.224
    x[:, 2] = (x[:, 2] / 255.0 - 0.406) / 0.225
    return x

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

def cross_product(self, vector1, vector2):
    return carla.Vector3D(x=vector1.y * vector2.z - vector1.z * vector2.y, y=vector1.z * vector2.x - vector1.x * vector2.z, z=vector1.x * vector2.y - vector1.y * vector2.x)

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

def __init__(self, min_distance, max_distance):
    self.saved_route = deque()
    self.route = deque()
    self.min_distance = min_distance
    self.max_distance = max_distance
    self.is_last = False
    self.mean = np.array([0.0, 0.0])
    self.scale = np.array([111324.60662786, 111319.490945])

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

class EgoModel:

    def __init__(self, dt=1.0 / 4):
        self.dt = dt
        self.front_wb = -0.090769015
        self.rear_wb = 1.4178275
        self.steer_gain = 0.36848336
        self.brake_accel = -4.952399
        self.throt_accel = 0.5633837

    def forward(self, locs, yaws, spds, acts):
        steer = acts[..., 0:1].item()
        throt = acts[..., 1:2].item()
        brake = acts[..., 2:3].astype(np.uint8)
        if brake:
            accel = self.brake_accel
        else:
            accel = self.throt_accel * throt
        wheel = self.steer_gain * steer
        beta = math.atan(self.rear_wb / (self.front_wb + self.rear_wb) * math.tan(wheel))
        yaws = yaws.item()
        spds = spds.item()
        next_locs_0 = locs[0].item() + spds * math.cos(yaws + beta) * self.dt
        next_locs_1 = locs[1].item() + spds * math.sin(yaws + beta) * self.dt
        next_yaws = yaws + spds / self.rear_wb * math.sin(beta) * self.dt
        next_spds = spds + accel * self.dt
        next_spds = next_spds * (next_spds > 0.0)
        next_locs = np.array([next_locs_0, next_locs_1])
        next_yaws = np.array(next_yaws)
        next_spds = np.array(next_spds)
        return (next_locs, next_yaws, next_spds)

def forward(self, locs, yaws, spds, acts):
    steer = acts[..., 0:1].item()
    throt = acts[..., 1:2].item()
    brake = acts[..., 2:3].astype(np.uint8)
    if brake:
        accel = self.brake_accel
    else:
        accel = self.throt_accel * throt
    wheel = self.steer_gain * steer
    beta = math.atan(self.rear_wb / (self.front_wb + self.rear_wb) * math.tan(wheel))
    yaws = yaws.item()
    spds = spds.item()
    next_locs_0 = locs[0].item() + spds * math.cos(yaws + beta) * self.dt
    next_locs_1 = locs[1].item() + spds * math.sin(yaws + beta) * self.dt
    next_yaws = yaws + spds / self.rear_wb * math.sin(beta) * self.dt
    next_spds = spds + accel * self.dt
    next_spds = next_spds * (next_spds > 0.0)
    next_locs = np.array([next_locs_0, next_locs_1])
    next_yaws = np.array(next_yaws)
    next_spds = np.array(next_spds)
    return (next_locs, next_yaws, next_spds)

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

def save(self):
    torch.save(self.model.state_dict(), os.path.join(self.args.logdir, 'model_%d.pth' % self.cur_epoch))
    torch.save(self.optimizer.state_dict(), os.path.join(self.args.logdir, 'optimizer_%d.pth' % self.cur_epoch))

def get_virtual_lidar_to_vehicle_transform():
    T = np.eye(4)
    T[0, 3] = 1.3
    T[1, 3] = 0.0
    T[2, 3] = 2.5
    return T

def get_lidar_to_vehicle_transform():
    rot = np.array([[0, 1, 0], [-1, 0, 0], [0, 0, 1]], dtype=np.float32)
    T = np.eye(4)
    T[:3, :3] = rot
    T[0, 3] = 1.3
    T[1, 3] = 0.0
    T[2, 3] = 2.5
    return T

def get_lidar_to_bevimage_transform():
    T = np.array([[0, -1, 16], [-1, 0, 32], [0, 0, 1]], dtype=np.float32)
    T[:2, :] *= 8
    return T

def normalize_imagenet(x):
    """ Normalize input images according to ImageNet standards.
    Args:
        x (tensor): input images
    """
    x = x.clone()
    x[:, 0] = (x[:, 0] / 255.0 - 0.485) / 0.229
    x[:, 1] = (x[:, 1] / 255.0 - 0.456) / 0.224
    x[:, 2] = (x[:, 2] / 255.0 - 0.406) / 0.225
    return x

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

def normalize_imagenet(x):
    """ Normalize input images according to ImageNet standards.
    Args:
        x (tensor): input images
    """
    x = x.clone()
    x[:, 0] = (x[:, 0] / 255.0 - 0.485) / 0.229
    x[:, 1] = (x[:, 1] / 255.0 - 0.456) / 0.224
    x[:, 2] = (x[:, 2] / 255.0 - 0.406) / 0.225
    return x

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

def get_depth(data):
    """
    Computes the normalized depth
    """
    data = np.transpose(data, (1, 2, 0))
    data = data.astype(np.float32)
    normalized = np.dot(data, [65536.0, 256.0, 1.0])
    normalized /= 256 * 256 * 256 - 1
    normalized = np.clip(normalized, a_min=0.0, a_max=0.05)
    normalized = normalized * 20.0
    return normalized

def align(lidar_0, measurements_0, measurements_1, degree=0):
    matrix_0 = measurements_0['ego_matrix']
    matrix_1 = measurements_1['ego_matrix']
    matrix_0 = np.array(matrix_0)
    matrix_1 = np.array(matrix_1)
    Tr_lidar_to_vehicle = get_lidar_to_vehicle_transform()
    Tr_vehicle_to_lidar = get_vehicle_to_lidar_transform()
    transform_0_to_1 = Tr_vehicle_to_lidar @ np.linalg.inv(matrix_1) @ matrix_0 @ Tr_lidar_to_vehicle
    rad = np.deg2rad(degree)
    degree_matrix = np.array([[np.cos(rad), np.sin(rad), 0, 0], [-np.sin(rad), np.cos(rad), 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
    transform_0_to_1 = degree_matrix @ transform_0_to_1
    lidar = lidar_0.copy()
    lidar[:, -1] = 1.0
    lidar[:, 1] *= -1.0
    lidar = transform_0_to_1 @ lidar.T
    lidar = lidar.T
    lidar[:, -1] = lidar_0[:, -1]
    lidar[:, 1] *= -1.0
    return lidar

def lidar_to_histogram_features(lidar):
    """
    Convert LiDAR point cloud into 2-bin histogram over 256x256 grid
    """

    def splat_points(point_cloud):
        pixels_per_meter = 8
        hist_max_per_pixel = 5
        x_meters_max = 16
        y_meters_max = 32
        xbins = np.linspace(-x_meters_max, x_meters_max, 32 * pixels_per_meter + 1)
        ybins = np.linspace(-y_meters_max, 0, 32 * pixels_per_meter + 1)
        hist = np.histogramdd(point_cloud[..., :2], bins=(xbins, ybins))[0]
        hist[hist > hist_max_per_pixel] = hist_max_per_pixel
        overhead_splat = hist / hist_max_per_pixel
        return overhead_splat
    below = lidar[lidar[..., 2] <= -2.3]
    above = lidar[lidar[..., 2] > -2.3]
    below_features = splat_points(below)
    above_features = splat_points(above)
    features = np.stack([above_features, below_features], axis=-1)
    features = np.transpose(features, (2, 0, 1)).astype(np.float32)
    features = np.rot90(features, -1, axes=(1, 2)).copy()
    return features

def get_bbox_label(bbox, rad=0):
    dz, dx, dy, x, y, z, yaw, speed, brake = bbox
    pixels_per_meter = 8
    degree_matrix = np.array([[np.cos(rad), np.sin(rad), 0], [-np.sin(rad), np.cos(rad), 0], [0, 0, 1]])
    T = get_lidar_to_bevimage_transform() @ degree_matrix
    position = np.array([x, y, 1.0]).reshape([3, 1])
    position = T @ position
    position = np.clip(position, 0.0, 255.0)
    x, y = position[:2, 0]
    bbox = np.array([x, y, dy * pixels_per_meter, dx * pixels_per_meter, 0, 0, 0])
    bbox[4] = yaw + rad
    bbox[5] = speed
    bbox[6] = brake
    return bbox

def crop_image_cv2(image, crop=(128, 640), crop_shift=0):
    """
    Scale and crop a PIL image, returning a channels-first numpy array.
    """
    width = image.shape[1]
    height = image.shape[0]
    crop_h, crop_w = crop
    start_y = height // 2 - crop_h // 2
    start_x = width // 2 - crop_w // 2
    start_x += int(crop_shift)
    cropped_image = image[start_y:start_y + crop_h, start_x:start_x + crop_w]
    cropped_image = np.transpose(cropped_image, (2, 0, 1))
    return cropped_image

def load_crop_bev_npy(bev_array, degree):
    """
    Load and crop an Image.
    Crop depends on augmentation angle.
    """
    PIXELS_PER_METER_FOR_BEV = 5
    PIXLES = 32 * PIXELS_PER_METER_FOR_BEV
    start_x = 250 - PIXLES // 2
    start_y = 250 - PIXLES
    bev_array = np.moveaxis(bev_array, 0, -1).astype(np.float32)
    bev_shift = np.zeros_like(bev_array)
    bev_shift[7:] = bev_array[:-7]
    bev_shift = rotate(bev_shift, degree)
    cropped_image = bev_shift[start_y:start_y + PIXLES, start_x:start_x + PIXLES]
    cropped_image = np.moveaxis(cropped_image, -1, 0)
    cropped_image = np.concatenate((np.zeros_like(cropped_image[:1]), cropped_image[:1], cropped_image[:1] + cropped_image[1:2]), axis=0)
    cropped_image = np.argmax(cropped_image, axis=0)
    return cropped_image

def draw_target_point(target_point, color=(255, 255, 255)):
    image = np.zeros((256, 256), dtype=np.uint8)
    target_point = target_point.copy()
    target_point[1] += 1.3
    point = target_point * 8.0
    point[1] *= -1
    point[1] = 256 - point[1]
    point[0] += 128
    point = point.astype(np.int32)
    point = np.clip(point, 0, 256)
    cv2.circle(image, tuple(point), radius=5, color=color, thickness=3)
    image = image.reshape(1, 256, 256)
    return image.astype(np.float) / 255.0

def correspondences_at_one_scale(valid_bev_points, valid_cam_points, lidar_x, lidar_y, camera_x, camera_y, scale):
    """
    Compute projections between LiDAR BEV and image space
    """
    cam_to_bev_proj_locs = np.zeros((lidar_x, lidar_y, 5, 2))
    bev_to_cam_proj_locs = np.zeros((camera_x, camera_y, 5, 2))
    tmp_bev = np.empty((lidar_x, lidar_y), dtype=object)
    tmp_cam = np.empty((camera_x, camera_y), dtype=object)
    for i in range(lidar_x):
        for j in range(lidar_y):
            tmp_bev[i, j] = []
    for i in range(camera_x):
        for j in range(camera_y):
            tmp_cam[i, j] = []
    for i in range(valid_bev_points.shape[0]):
        tmp_bev[valid_bev_points[i][0] // scale, valid_bev_points[i][1] // scale].append(valid_cam_points[i] // scale)
        tmp_cam[valid_cam_points[i][0] // scale, valid_cam_points[i][1] // scale].append(valid_bev_points[i] // scale)
    for i in range(lidar_x):
        for j in range(lidar_y):
            cam_to_bev_points = tmp_bev[i, j]
            if len(cam_to_bev_points) > 5:
                cam_to_bev_proj_locs[i, j] = np.array(random.sample(cam_to_bev_points, 5))
            elif len(cam_to_bev_points) > 0:
                num_points = len(cam_to_bev_points)
                cam_to_bev_proj_locs[i, j, :num_points] = np.array(cam_to_bev_points)
    for i in range(camera_x):
        for j in range(camera_y):
            bev_to_cam_points = tmp_cam[i, j]
            if len(bev_to_cam_points) > 5:
                bev_to_cam_proj_locs[i, j] = np.array(random.sample(bev_to_cam_points, 5))
            elif len(bev_to_cam_points) > 0:
                num_points = len(bev_to_cam_points)
                bev_to_cam_proj_locs[i, j, :num_points] = np.array(bev_to_cam_points)
    return (cam_to_bev_proj_locs, bev_to_cam_proj_locs)

def lidar_bev_cam_correspondences(world, lidar_vis=None, image_vis=None, step=None, debug=False):
    """
    Convert LiDAR point cloud to camera co-ordinates

    world: Expects the point cloud from CARLA in the CARLA coordinate system: x left, y forward, z up (LiDAR rotated by 90 degree)
    lidar_vis: lidar prjected to BEV
    image_vis: RGB input image to the network
    step: current timestep
    debug: Whether to save the debug images. If false only world is required
    """
    pixels_per_meter = 8
    lidar_width = 256
    lidar_height = 256
    lidar_meters_x = lidar_width / pixels_per_meter / 2
    lidar_meters_y = lidar_height / pixels_per_meter
    downscale_factor = 32
    img_width = 352
    img_height = 160
    fov_width = 60
    left_camera_rotation = -60.0
    right_camera_rotation = 60.0
    fov_height = 2.0 * np.arctan(img_height / img_width * np.tan(0.5 * np.radians(fov_width)))
    fov_height = np.rad2deg(fov_height)
    focal_x = img_width / (2.0 * np.tan(np.deg2rad(fov_width) / 2.0))
    focal_y = img_height / (2.0 * np.tan(np.deg2rad(fov_height) / 2.0))
    cam_z = 2.3
    lidar_z = 2.5
    world[:, 0] *= -1
    lidar = world[abs(world[:, 0]) < lidar_meters_x]
    lidar = lidar[lidar[:, 1] < lidar_meters_y]
    lidar = lidar[lidar[:, 1] > 0]
    lidar[..., 2] = lidar[..., 2] + (lidar_z - cam_z)
    lidar_for_left_camera = deepcopy(lidar)
    lidar_for_right_camera = deepcopy(lidar)
    lidar_indices = np.arange(0, lidar.shape[0], 1)
    z = lidar[..., 1]
    x = focal_x * lidar[..., 0] / z + img_width / 2.0
    y = focal_y * lidar[..., 2] / z + img_height / 2.0
    result_center = np.stack([x, y, lidar_indices], 1)
    result_center = result_center[np.logical_and(result_center[..., 0] > 0, result_center[..., 0] < img_width)]
    result_center = result_center[np.logical_and(result_center[..., 1] > 0, result_center[..., 1] < img_height)]
    result_center_shifted = result_center
    result_center_shifted[..., 0] = result_center_shifted[..., 0] + img_width / 2.0
    theta = np.radians(left_camera_rotation)
    R = np.array([[np.cos(theta), -np.sin(theta), 0.0], [np.sin(theta), np.cos(theta), 0.0], [0.0, 0.0, 1.0]])
    lidar_for_left_camera = R.dot(lidar_for_left_camera.T).T
    z = lidar_for_left_camera[..., 1]
    x = focal_x * lidar_for_left_camera[..., 0] / z + img_width / 2.0
    y = focal_y * lidar_for_left_camera[..., 2] / z + img_height / 2.0
    result_left = np.stack([x, y, lidar_indices], 1)
    result_left = result_left[np.logical_and(result_left[..., 0] > 0, result_left[..., 0] < img_width)]
    result_left = result_left[np.logical_and(result_left[..., 1] > 0, result_left[..., 1] < img_height)]
    result_left_shifted = result_left[result_left[..., 0] >= img_width / 2.0]
    result_left_shifted[..., 0] = result_left_shifted[..., 0] - img_width / 2.0
    theta = np.radians(right_camera_rotation)
    R = np.array([[np.cos(theta), -np.sin(theta), 0.0], [np.sin(theta), np.cos(theta), 0.0], [0.0, 0.0, 1.0]])
    lidar_for_right_camera = R.dot(lidar_for_right_camera.T).T
    z = lidar_for_right_camera[..., 1]
    x = focal_x * lidar_for_right_camera[..., 0] / z + img_width / 2.0
    y = focal_y * lidar_for_right_camera[..., 2] / z + img_height / 2.0
    result_right = np.stack([x, y, lidar_indices], 1)
    result_right = result_right[np.logical_and(result_right[..., 0] > 0, result_right[..., 0] < img_width)]
    result_right = result_right[np.logical_and(result_right[..., 1] > 0, result_right[..., 1] < img_height)]
    result_right_shifted = result_right[result_right[..., 0] < img_width / 2.0]
    result_right_shifted[..., 0] = result_right_shifted[..., 0] + img_width / 2.0 + img_width
    results_total = np.concatenate((result_left_shifted, result_center_shifted, result_right_shifted), axis=0)
    if debug == True:
        vis = np.zeros([img_height, 2 * img_width])
        vis_bev = np.zeros([lidar_height, lidar_width])
        vis_original_image = image_vis[0].detach().cpu().numpy()
        vis_original_image = np.transpose(vis_original_image, (1, 2, 0)) / 255.0
        vis_original_lidar = np.zeros([lidar_height, lidar_width])
        lidar_vis = lidar_vis.detach().cpu().numpy()
        vis_original_lidar[np.greater(lidar_vis[0, 0], 0)] = 255
        vis_original_lidar[np.greater(lidar_vis[0, 1], 0)] = 255
    valid_bev_points = []
    valid_cam_points = []
    for i in range(results_total.shape[0]):
        lidar_index = int(results_total[i, 2])
        bev_x = int((lidar[lidar_index][0] + lidar_meters_x) * pixels_per_meter)
        bev_y = (int(lidar[lidar_index][1] * pixels_per_meter) - (lidar_height - 1)) * -1
        valid_bev_points.append([bev_x, bev_y])
        img_x = int(results_total[i][0])
        img_y = (int(results_total[i][1]) - (img_height - 1)) * -1
        valid_cam_points.append([img_x, img_y])
        if debug == True:
            vis_original_image[img_y, img_x] = np.array([0.0, 1.0, 0.0])
            vis_bev[bev_y, bev_x] = 255
            vis[img_y, img_x] = 255
    if debug == True:
        from matplotlib import pyplot as plt
        plt.ion()
        plt.imshow(vis_bev)
        plt.savefig('/home/hiwi/save folder/Visualizations/2/bev_lidar_{}.png'.format(step), bbox_inches='tight')
        plt.close()
        plt.imshow(vis_original_image)
        plt.savefig('/home/hiwi/save folder/Visualizations/2/image_with_lidar_{}.png'.format(step), bbox_inches='tight')
        plt.close()
        plt.ioff()
    valid_bev_points = np.array(valid_bev_points)
    valid_cam_points = np.array(valid_cam_points)
    bev_points, cam_points = correspondences_at_one_scale(valid_bev_points, valid_cam_points, lidar_width // downscale_factor, lidar_height // downscale_factor, img_width // downscale_factor * 2, img_height // downscale_factor, downscale_factor)
    return (bev_points, cam_points)

def decode_pil_to_npy(img):
    """
    """
    channels, width, height = (15, img.shape[1], img.shape[2])
    bev_array = np.zeros([channels, width, height])
    for ix in range(5):
        bit_pos = 8 - ix - 1
        bev_array[[ix, ix + 5, ix + 5 + 5]] = (img & 1 << bit_pos) >> bit_pos
    return bev_array[10:12]

def normalize_imagenet(x):
    """ Normalize input images according to ImageNet standards.
    Args:
        x (tensor): input images
    """
    x = x.clone()
    x[:, 0] = (x[:, 0] / 255.0 - 0.485) / 0.229
    x[:, 1] = (x[:, 1] / 255.0 - 0.456) / 0.224
    x[:, 2] = (x[:, 2] / 255.0 - 0.406) / 0.225
    return x

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

def scatter_points(self, features, coords, batch_size):
    canvas = torch.zeros(batch_size, features.shape[1], self.ny, self.nx, dtype=features.dtype, device=features.device)
    canvas[coords[:, 0], :, torch.clamp(self.ny - 1 - coords[:, 1], 0, self.ny - 1), torch.clamp(coords[:, 2], 0, self.nx - 1)] = features
    return canvas

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

def __init__(self, K_P=1.0, K_I=0.0, K_D=0.0, n=20):
    self._K_P = K_P
    self._K_I = K_I
    self._K_D = K_D
    self._window = deque([0 for _ in range(n)], maxlen=n)

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

