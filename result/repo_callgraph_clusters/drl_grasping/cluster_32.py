# Cluster 32

class Tf2Broadcaster:

    def __init__(self, node: Node):
        self._node = node
        self.__tf2_broadcaster = StaticTransformBroadcaster(node=self._node)
        self._transform_stamped = TransformStamped()

    def broadcast_tf(self, parent_frame_id: str, child_frame_id: str, translation: Tuple[float, float, float], rotation: Tuple[float, float, float, float], xyzw: bool=True):
        """
        Broadcast transformation of the camera
        """
        self._transform_stamped.header.frame_id = parent_frame_id
        self._transform_stamped.child_frame_id = child_frame_id
        self._transform_stamped.header.stamp = self._node.get_clock().now().to_msg()
        self._transform_stamped.transform.translation.x = float(translation[0])
        self._transform_stamped.transform.translation.y = float(translation[1])
        self._transform_stamped.transform.translation.z = float(translation[2])
        if xyzw:
            self._transform_stamped.transform.rotation.x = float(rotation[0])
            self._transform_stamped.transform.rotation.y = float(rotation[1])
            self._transform_stamped.transform.rotation.z = float(rotation[2])
            self._transform_stamped.transform.rotation.w = float(rotation[3])
        else:
            self._transform_stamped.transform.rotation.w = float(rotation[0])
            self._transform_stamped.transform.rotation.x = float(rotation[1])
            self._transform_stamped.transform.rotation.y = float(rotation[2])
            self._transform_stamped.transform.rotation.z = float(rotation[3])
        self.__tf2_broadcaster.sendTransform(self._transform_stamped)

def __init__(self, node: Node):
    self._node = node
    self.__tf2_broadcaster = StaticTransformBroadcaster(node=self._node)
    self._transform_stamped = TransformStamped()

