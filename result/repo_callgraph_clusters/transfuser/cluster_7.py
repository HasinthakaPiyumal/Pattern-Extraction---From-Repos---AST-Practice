# Cluster 7

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

def set_intersection_state(self, choice):
    """
        Changes the intersection to the desired state
        """
    prev_state = CarlaDataProvider.update_light_states(self.traffic_light, self.annotations, choice, freeze=True)
    return prev_state

