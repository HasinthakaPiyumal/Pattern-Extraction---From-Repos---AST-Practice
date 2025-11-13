# Cluster 27

class Camera(model_wrapper.ModelWrapper):

    def __init__(self, world: scenario.World, name: Union[str, None]=None, position: List[float]=(0, 0, 0), orientation: List[float]=(1, 0, 0, 0), static: bool=True, camera_type: str='rgbd_camera', width: int=212, height: int=120, image_format: str='R8G8B8', update_rate: int=15, horizontal_fov: float=1.567821, vertical_fov: float=1.022238, clip_color: List[float]=(0.02, 1000.0), clip_depth: List[float]=(0.02, 10.0), noise_mean: float=None, noise_stddev: float=None, ros2_bridge_color: bool=False, ros2_bridge_depth: bool=False, ros2_bridge_points: bool=False, visibility_mask: int=0, visual: Optional[str]=None):
        if name is not None:
            model_name = get_unique_model_name(world, name)
        else:
            model_name = get_unique_model_name(world, camera_type)
        self._model_name = model_name
        initial_pose = scenario.Pose(position, orientation)
        if visual:
            use_mesh: bool = False
            if 'intel_realsense_d435' == visual:
                use_mesh = True
                model_path = ModelCollectionRandomizer.get_collection_paths(owner='OpenRobotics', collection='', model_name='Intel RealSense D435')[0]
                mesh_dir = os.path.join(model_path, 'meshes')
                texture_dir = os.path.join(model_path, 'materials', 'textures')
                mesh_path_visual = os.path.join(mesh_dir, 'realsense.dae')
                if not os.path.exists(mesh_path_visual):
                    raise ValueError(f"Visual mesh '{mesh_path_visual}' for Camera model is not a valid file.")
                albedo_map = None
                normal_map = None
                roughness_map = None
                metalness_map = None
                if texture_dir:
                    texture_files = os.listdir(texture_dir)
                    for texture in texture_files:
                        texture_lower = texture.lower()
                        if 'basecolor' in texture_lower or 'albedo' in texture_lower:
                            albedo_map = os.path.join(texture_dir, texture)
                        elif 'normal' in texture_lower:
                            normal_map = os.path.join(texture_dir, texture)
                        elif 'roughness' in texture_lower:
                            roughness_map = os.path.join(texture_dir, texture)
                        elif 'specular' in texture_lower or 'metalness' in texture_lower:
                            metalness_map = os.path.join(texture_dir, texture)
                if not (albedo_map and normal_map and roughness_map and metalness_map):
                    raise ValueError(f'Not all textures for Camera model were found.')
        sdf = f'<sdf version="1.9">\n            <model name="{model_name}">\n                <static>{static}</static>\n                <link name="{self.link_name}">\n                    <sensor name="camera" type="{camera_type}">\n                        <topic>{model_name}</topic>\n                        <always_on>true</always_on>\n                        <update_rate>{update_rate}</update_rate>\n                        <camera name="{model_name}_camera">\n                            <image>\n                                <width>{width}</width>\n                                <height>{height}</height>\n                                <format>{image_format}</format>\n                            </image>\n                            <horizontal_fov>{horizontal_fov}</horizontal_fov>\n                            <vertical_fov>{vertical_fov}</vertical_fov>\n                            <clip>\n                                <near>{clip_color[0]}</near>\n                                <far>{clip_color[1]}</far>\n                            </clip>\n                            {(f'<depth_camera>\n                                <clip>\n                                    <near>{clip_depth[0]}</near>\n                                    <far>{clip_depth[1]}</far>\n                                </clip>\n                            </depth_camera>' if 'rgbd' in model_name else '')}\n                            {(f'<noise>\n                                <type>gaussian</type>\n                                <mean>{noise_mean}</mean>\n                                <stddev>{noise_stddev}</stddev>\n                            </noise>' if noise_mean is not None and noise_stddev is not None else '')}\n                            <visibility_mask>{visibility_mask}</visibility_mask>\n                        </camera>\n                        <visualize>true</visualize>\n                    </sensor>\n                    {(f'\n                        <visual name="{model_name}_visual_lens">\n                            <pose>-0.01 0 0 0 1.5707963 0</pose>\n                            <geometry>\n                                <cylinder>\n                                    <radius>0.02</radius>\n                                    <length>0.02</length>\n                                </cylinder>\n                            </geometry>\n                            <material>\n                                <ambient>0.0 0.8 0.0</ambient>\n                                <diffuse>0.0 0.8 0.0</diffuse>\n                                <specular>0.0 0.8 0.0</specular>\n                            </material>\n                        </visual>\n                        <visual name="{model_name}_visual_body">\n                            <pose>-0.05 0 0 0 0 0</pose>\n                            <geometry>\n                                <box>\n                                    <size>0.06 0.05 0.05</size>\n                                </box>\n                            </geometry>\n                            <material>\n                                <ambient>0.0 0.8 0.0</ambient>\n                                <diffuse>0.0 0.8 0.0</diffuse>\n                                <specular>0.0 0.8 0.0</specular>\n                            </material>\n                        </visual>\n                        ' if visual and (not use_mesh) else '')}\n                        {(f'\n                        <inertial>\n                            <mass>0.0615752</mass>\n                            <inertia>\n                                <ixx>9.108e-05</ixx>\n                                <ixy>0.0</ixy>\n                                <ixz>0.0</ixz>\n                                <iyy>2.51e-06</iyy>\n                                <iyz>0.0</iyz>\n                                <izz>8.931e-05</izz>\n                            </inertia>\n                        </inertial>\n                        <visual name="{model_name}_visual">\n                            <pose>0 0 0 0 0 1.5707963</pose>\n                            <geometry>\n                                <mesh>\n                                    <uri>{mesh_path_visual}</uri>\n                                    <submesh>\n                                        <name>RealSense</name>\n                                        <center>false</center>\n                                    </submesh>\n                                </mesh>\n                            </geometry>\n                            <material>\n                                <diffuse>1 1 1 1</diffuse>\n                                <specular>1 1 1 1</specular>\n                                <pbr>\n                                    <metal>\n                                        <albedo_map>{albedo_map}</albedo_map>\n                                        <normal_map>{normal_map}</normal_map>\n                                        <roughness_map>{roughness_map}</roughness_map>\n                                        <metalness_map>{metalness_map}</metalness_map>\n                                    </metal>\n                                </pbr>\n                            </material>\n                        </visual>\n                        ' if visual and use_mesh else '')}\n                </link>\n            </model>\n        </sdf>'
        ok_model = world.to_gazebo().insert_model_from_string(sdf, initial_pose, model_name)
        if not ok_model:
            raise RuntimeError('Failed to insert ' + model_name)
        model = world.get_model(model_name)
        model_wrapper.ModelWrapper.__init__(self, model=model)
        if ros2_bridge_color or ros2_bridge_depth or ros2_bridge_points:
            self.__threads = []
            if ros2_bridge_color:
                self.__threads.append(Thread(target=self.construct_ros2_bridge, args=(self.color_topic, 'sensor_msgs/msg/Image', 'ignition.msgs.Image'), daemon=True))
            if ros2_bridge_depth:
                self.__threads.append(Thread(target=self.construct_ros2_bridge, args=(self.depth_topic, 'sensor_msgs/msg/Image', 'ignition.msgs.Image'), daemon=True))
            if ros2_bridge_points:
                self.__threads.append(Thread(target=self.construct_ros2_bridge, args=(self.points_topic, 'sensor_msgs/msg/PointCloud2', 'ignition.msgs.PointCloudPacked'), daemon=True))
            for thread in self.__threads:
                thread.start()

    def __del__(self):
        if hasattr(self, '__threads'):
            for thread in self.__threads:
                thread.join()

    @classmethod
    def construct_ros2_bridge(self, topic: str, ros_msg: str, ign_msg: str):
        node_name = 'parameter_bridge' + topic.replace('/', '_')
        command = f'ros2 run ros_ign_bridge parameter_bridge {topic}@{ros_msg}[{ign_msg} ' + f'--ros-args --remap __node:={node_name} --ros-args -p use_sim_time:=true'
        os.system(command)

    @classmethod
    def get_frame_id(cls, model_name: str) -> str:
        return f'{model_name}/{model_name}_link/camera'

    @property
    def frame_id(self) -> str:
        return self.get_frame_id(self._model_name)

    @classmethod
    def get_color_topic(cls, model_name: str) -> str:
        return f'/{model_name}/image' if 'rgbd' in model_name else f'/{model_name}'

    @property
    def color_topic(self) -> str:
        return self.get_color_topic(self._model_name)

    @classmethod
    def get_depth_topic(cls, model_name: str) -> str:
        return f'/{model_name}/depth_image' if 'rgbd' in model_name else f'/{model_name}'

    @property
    def depth_topic(self) -> str:
        return self.get_depth_topic(self._model_name)

    @classmethod
    def get_points_topic(cls, model_name: str) -> str:
        return f'/{model_name}/points'

    @property
    def points_topic(self) -> str:
        return self.get_points_topic(self._model_name)

    @classmethod
    def get_link_name(cls, model_name: str) -> str:
        return f'{model_name}_link'

    @property
    def link_name(self) -> str:
        return self.get_link_name(self._model_name)

@property
def link_name(self) -> str:
    return self.get_link_name(self._model_name)

