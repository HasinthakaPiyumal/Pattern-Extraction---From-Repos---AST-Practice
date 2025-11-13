# Cluster 34

class Tf2Listener:

    def __init__(self, node: Node):
        self._node = node
        self.__tf2_buffer = Buffer()
        TransformListener(buffer=self.__tf2_buffer, node=node)

    def lookup_transform_sync(self, target_frame: str, source_frame: str, retry: bool=True) -> Optional[Transform]:
        try:
            return self.__tf2_buffer.lookup_transform(target_frame=target_frame, source_frame=source_frame, time=rclpy.time.Time()).transform
        except:
            if retry:
                while rclpy.ok():
                    if self.__tf2_buffer.can_transform(target_frame=target_frame, source_frame=source_frame, time=rclpy.time.Time(), timeout=rclpy.time.Duration(seconds=1, nanoseconds=0)):
                        return self.__tf2_buffer.lookup_transform(target_frame=target_frame, source_frame=source_frame, time=rclpy.time.Time()).transform
                    self._node.get_logger().warn(f'Lookup of transform from "{source_frame}" to "{target_frame}" failed, retrying...')
            else:
                return None

def __init__(self, node: Node):
    self._node = node
    self.__tf2_buffer = Buffer()
    TransformListener(buffer=self.__tf2_buffer, node=node)

