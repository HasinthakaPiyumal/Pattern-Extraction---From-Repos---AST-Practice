# Cluster 3

class CameraSubscriber:

    def __init__(self, node: Node, topic: str, is_point_cloud: bool, callback_group: Optional[CallbackGroup]=None):
        self._node = node
        if is_point_cloud:
            camera_msg_type = PointCloud2
        else:
            camera_msg_type = Image
        self.__observation = camera_msg_type()
        self._node.create_subscription(msg_type=camera_msg_type, topic=topic, callback=self.observation_callback, qos_profile=QoSProfile(reliability=QoSReliabilityPolicy.RELIABLE, durability=QoSDurabilityPolicy.VOLATILE, history=QoSHistoryPolicy.KEEP_LAST, depth=1), callback_group=callback_group)
        self.__observation_mutex = Lock()
        self.__new_observation_available = False

    def observation_callback(self, msg):
        """
        Callback for getting observation.
        """
        self.__observation_mutex.acquire()
        self.__observation = msg
        self.__new_observation_available = True
        self._node.get_logger().debug('New observation received.')
        self.__observation_mutex.release()

    def get_observation(self) -> Union[PointCloud2, Image]:
        """
        Get the last received observation.
        """
        self.__observation_mutex.acquire()
        observation = self.__observation
        self.__observation_mutex.release()
        return observation

    def reset_new_observation_checker(self):
        """
        Reset checker of new observations, i.e. `self.new_observation_available()`
        """
        self.__observation_mutex.acquire()
        self.__new_observation_available = False
        self.__observation_mutex.release()

    @property
    def new_observation_available(self):
        """
        Check if new observation is available since `self.reset_new_observation_checker()` was called
        """
        return self.__new_observation_available

def __init__(self, node: Node, topic: str, is_point_cloud: bool, callback_group: Optional[CallbackGroup]=None):
    self._node = node
    if is_point_cloud:
        camera_msg_type = PointCloud2
    else:
        camera_msg_type = Image
    self.__observation = camera_msg_type()
    self._node.create_subscription(msg_type=camera_msg_type, topic=topic, callback=self.observation_callback, qos_profile=QoSProfile(reliability=QoSReliabilityPolicy.RELIABLE, durability=QoSDurabilityPolicy.VOLATILE, history=QoSHistoryPolicy.KEEP_LAST, depth=1), callback_group=callback_group)
    self.__observation_mutex = Lock()
    self.__new_observation_available = False

