# Cluster 0

class ParallelTrainCallback(BaseCallback):
    """
    Callback to explore (collect experience) and train (do gradient steps)
    at the same time using two separate threads.
    Normally used with off-policy algorithms and `train_freq=(1, "episode")`.

    - blocking mode: wait for the model to finish updating the policy before collecting new experience
        at the end of a rollout
    - force sync mode: stop training to update to the latest policy for collecting
        new experience

    :param gradient_steps: Number of gradient steps to do before
        sending the new policy
    :param verbose: Verbosity level
    :param sleep_time: Limit the fps in the thread collecting experience.
    """

    def __init__(self, gradient_steps: int=100, verbose: int=0, sleep_time: float=0.0):
        super(ParallelTrainCallback, self).__init__(verbose)
        self.batch_size = 0
        self._model_ready = True
        self._model = None
        self.gradient_steps = gradient_steps
        self.process = None
        self.model_class = None
        self.sleep_time = sleep_time

    def _init_callback(self) -> None:
        temp_file = tempfile.TemporaryFile()
        if os.name == 'nt':
            temp_file = os.path.join('logs', 'model_tmp.zip')
        self.model.save(temp_file)
        for model_class in [SAC, TQC]:
            if isinstance(self.model, model_class):
                self.model_class = model_class
                break
        assert self.model_class is not None, f'{self.model} is not supported for parallel training'
        self._model = self.model_class.load(temp_file)
        self.batch_size = self._model.batch_size

        def patch_train(function):

            @wraps(function)
            def wrapper(*args, **kwargs):
                return
            return wrapper
        self._model.set_logger(self.model.logger)
        self.model.train = patch_train(self.model.train)

        def patch_save(function):

            @wraps(function)
            def wrapper(*args, **kwargs):
                return self._model.save(*args, **kwargs)
            return wrapper
        self.model.save = patch_save(self.model.save)

    def train(self) -> None:
        self._model_ready = False
        self.process = Thread(target=self._train_thread, daemon=True)
        self.process.start()

    def _train_thread(self) -> None:
        self._model.train(gradient_steps=self.gradient_steps, batch_size=self.batch_size)
        self._model_ready = True

    def _on_step(self) -> bool:
        if self.sleep_time > 0:
            time.sleep(self.sleep_time)
        return True

    def _on_rollout_end(self) -> None:
        if self._model_ready:
            self._model.replay_buffer = deepcopy(self.model.replay_buffer)
            self.model.set_parameters(deepcopy(self._model.get_parameters()))
            self.model.actor = self.model.policy.actor
            if self.num_timesteps >= self._model.learning_starts:
                self.train()

    def _on_training_end(self) -> None:
        if self.process is not None:
            if self.verbose > 0:
                print('Waiting for training thread to terminate')
            self.process.join()

def train(self) -> None:
    self._model_ready = False
    self.process = Thread(target=self._train_thread, daemon=True)
    self.process.start()

def _on_step(self) -> bool:
    if self.sleep_time > 0:
        time.sleep(self.sleep_time)
    return True

class Tf2BroadcasterStandalone(Node, Tf2Broadcaster):

    def __init__(self, node_name: str='drl_grasping_tf_broadcaster', use_sim_time: bool=True):
        try:
            rclpy.init()
        except Exception as e:
            if not rclpy.ok():
                sys.exit(f'ROS 2 context could not be initialised: {e}')
        Node.__init__(self, node_name)
        self.set_parameters([Parameter('use_sim_time', type_=Parameter.Type.BOOL, value=use_sim_time)])
        Tf2Broadcaster.__init__(self, node=self)

def __init__(self, node_name: str='drl_grasping_tf_broadcaster', use_sim_time: bool=True):
    try:
        rclpy.init()
    except Exception as e:
        if not rclpy.ok():
            sys.exit(f'ROS 2 context could not be initialised: {e}')
    Node.__init__(self, node_name)
    self.set_parameters([Parameter('use_sim_time', type_=Parameter.Type.BOOL, value=use_sim_time)])
    Tf2Broadcaster.__init__(self, node=self)

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

class Tf2ListenerStandalone(Node, Tf2Listener):

    def __init__(self, node_name: str='drl_grasping_tf_listener', use_sim_time: bool=True):
        try:
            rclpy.init()
        except Exception as e:
            if not rclpy.ok():
                sys.exit(f'ROS 2 context could not be initialised: {e}')
        Node.__init__(self, node_name)
        self.set_parameters([Parameter('use_sim_time', type_=Parameter.Type.BOOL, value=use_sim_time)])
        Tf2Listener.__init__(self, node=self)

def __init__(self, node_name: str='drl_grasping_tf_listener', use_sim_time: bool=True):
    try:
        rclpy.init()
    except Exception as e:
        if not rclpy.ok():
            sys.exit(f'ROS 2 context could not be initialised: {e}')
    Node.__init__(self, node_name)
    self.set_parameters([Parameter('use_sim_time', type_=Parameter.Type.BOOL, value=use_sim_time)])
    Tf2Listener.__init__(self, node=self)

class CameraSubscriberStandalone(Node, CameraSubscriber):

    def __init__(self, topic: str, is_point_cloud: bool, node_name: str='drl_grasping_camera_sub', use_sim_time: bool=True):
        try:
            rclpy.init()
        except Exception as e:
            if not rclpy.ok():
                sys.exit(f'ROS 2 context could not be initialised: {e}')
        Node.__init__(self, node_name)
        self.set_parameters([Parameter('use_sim_time', type_=Parameter.Type.BOOL, value=use_sim_time)])
        CameraSubscriber.__init__(self, node=self, topic=topic, is_point_cloud=is_point_cloud)
        self._executor = SingleThreadedExecutor()
        self._executor.add_node(self)
        self._executor_thread = Thread(target=self._executor.spin, daemon=True, args=())
        self._executor_thread.start()

def __init__(self, topic: str, is_point_cloud: bool, node_name: str='drl_grasping_camera_sub', use_sim_time: bool=True):
    try:
        rclpy.init()
    except Exception as e:
        if not rclpy.ok():
            sys.exit(f'ROS 2 context could not be initialised: {e}')
    Node.__init__(self, node_name)
    self.set_parameters([Parameter('use_sim_time', type_=Parameter.Type.BOOL, value=use_sim_time)])
    CameraSubscriber.__init__(self, node=self, topic=topic, is_point_cloud=is_point_cloud)
    self._executor = SingleThreadedExecutor()
    self._executor.add_node(self)
    self._executor_thread = Thread(target=self._executor.spin, daemon=True, args=())
    self._executor_thread.start()

class Manipulation(Task, Node, abc.ABC):
    _ids = count(0)

    def __init__(self, agent_rate: float, robot_model: str, workspace_frame_id: str, workspace_centre: Tuple[float, float, float], workspace_volume: Tuple[float, float, float], ignore_new_actions_while_executing: bool, use_servo: bool, scaling_factor_translation: float, scaling_factor_rotation: float, restrict_position_goal_to_workspace: bool, enable_gripper: bool, num_threads: int, **kwargs):
        self.id = next(self._ids)
        Task.__init__(self, agent_rate=agent_rate)
        try:
            rclpy.init()
        except Exception as e:
            if not rclpy.ok():
                sys.exit(f'ROS 2 context could not be initialised: {e}')
        Node.__init__(self, f'drl_grasping_{self.id}')
        self._callback_group = ReentrantCallbackGroup()
        if num_threads == 1:
            executor = SingleThreadedExecutor()
        elif num_threads > 1:
            executor = MultiThreadedExecutor(num_threads=num_threads)
        else:
            executor = MultiThreadedExecutor(num_threads=multiprocessing.cpu_count())
        executor.add_node(self)
        self._executor_thread = Thread(target=executor.spin, daemon=True, args=())
        self._executor_thread.start()
        self.robot_model_class = get_robot_model_class(robot_model)
        self.workspace_centre = (workspace_centre[0], workspace_centre[1], workspace_centre[2] + self.robot_model_class.BASE_LINK_Z_OFFSET)
        self.workspace_volume = workspace_volume
        self._restrict_position_goal_to_workspace = restrict_position_goal_to_workspace
        self._use_servo = use_servo
        self.__scaling_factor_translation = scaling_factor_translation
        self.__scaling_factor_rotation = scaling_factor_rotation
        self._enable_gripper = enable_gripper
        workspace_volume_half = (workspace_volume[0] / 2, workspace_volume[1] / 2, workspace_volume[2] / 2)
        self.workspace_min_bound = (self.workspace_centre[0] - workspace_volume_half[0], self.workspace_centre[1] - workspace_volume_half[1], self.workspace_centre[2] - workspace_volume_half[2])
        self.workspace_max_bound = (self.workspace_centre[0] + workspace_volume_half[0], self.workspace_centre[1] + workspace_volume_half[1], self.workspace_centre[2] + workspace_volume_half[2])
        self.robot_prefix = self.robot_model_class.DEFAULT_PREFIX
        if 0 == self.id:
            self.robot_name = self.robot_model_class.ROBOT_MODEL_NAME
        else:
            self.robot_name = f'{self.robot_model_class.ROBOT_MODEL_NAME}{self.id}'
            if self.robot_prefix.endswith('_'):
                self.robot_prefix = f'{self.robot_prefix[:-1]}{self.id}_'
            elif self.robot_prefix.empty():
                self.robot_prefix = f'robot{self.id}_'
        self.robot_base_link_name = self.robot_model_class.get_robot_base_link_name(self.robot_prefix)
        self.robot_arm_base_link_name = self.robot_model_class.get_arm_base_link_name(self.robot_prefix)
        self.robot_ee_link_name = self.robot_model_class.get_ee_link_name(self.robot_prefix)
        self.robot_arm_link_names = self.robot_model_class.get_arm_link_names(self.robot_prefix)
        self.robot_gripper_link_names = self.robot_model_class.get_gripper_link_names(self.robot_prefix)
        self.robot_arm_joint_names = self.robot_model_class.get_arm_joint_names(self.robot_prefix)
        self.robot_gripper_joint_names = self.robot_model_class.get_gripper_joint_names(self.robot_prefix)
        self.workspace_frame_id = self.substitute_special_frame(workspace_frame_id)
        self.initial_arm_joint_positions = self.robot_model_class.DEFAULT_ARM_JOINT_POSITIONS
        self.initial_gripper_joint_positions = self.robot_model_class.DEFAULT_GRIPPER_JOINT_POSITIONS
        self.terrain_name = 'terrain'
        self.object_names = []
        self.tf2_listener = Tf2Listener(node=self)
        self.tf2_broadcaster = Tf2Broadcaster(node=self)
        self.moveit2 = MoveIt2(node=self, joint_names=self.robot_arm_joint_names, base_link_name=self.robot_arm_base_link_name, end_effector_name=self.robot_ee_link_name, execute_via_moveit=False, ignore_new_calls_while_executing=ignore_new_actions_while_executing, callback_group=self._callback_group)
        if self._use_servo:
            self.servo = MoveIt2Servo(node=self, frame_id=self.robot_arm_base_link_name, linear_speed=scaling_factor_translation, angular_speed=scaling_factor_rotation, callback_group=self._callback_group)
        self.gripper = MoveIt2Gripper(node=self, gripper_joint_names=self.robot_gripper_joint_names, open_gripper_joint_positions=self.robot_model_class.OPEN_GRIPPER_JOINT_POSITIONS, closed_gripper_joint_positions=self.robot_model_class.CLOSED_GRIPPER_JOINT_POSITIONS, skip_planning=True, ignore_new_calls_while_executing=ignore_new_actions_while_executing, callback_group=self._callback_group)
        self.__task_parameter_overrides: Dict[str, any] = {}
        self._randomizer_parameter_overrides: Dict[str, any] = {}

    def create_spaces(self) -> Tuple[ActionSpace, ObservationSpace]:
        action_space = self.create_action_space()
        observation_space = self.create_observation_space()
        return (action_space, observation_space)

    def create_action_space(self) -> ActionSpace:
        raise NotImplementedError()

    def create_observation_space(self) -> ObservationSpace:
        raise NotImplementedError()

    def set_action(self, action: Action):
        raise NotImplementedError()

    def get_observation(self) -> Observation:
        raise NotImplementedError()

    def get_reward(self) -> Reward:
        raise NotImplementedError()

    def is_done(self) -> bool:
        raise NotImplementedError()

    def reset_task(self):
        self.__consume_parameter_overrides()

    def get_relative_ee_position(self, translation: Tuple[float, float, float]) -> Tuple[float, float, float]:
        translation = self.scale_relative_translation(translation)
        current_position = self.get_ee_position()
        target_position = (current_position[0] + translation[0], current_position[1] + translation[1], current_position[2] + translation[2])
        if self._restrict_position_goal_to_workspace:
            target_position = self.restrict_position_goal_to_workspace(target_position)
        return target_position

    def get_relative_ee_orientation(self, rotation: Union[float, Tuple[float, float, float, float], Tuple[float, float, float, float, float, float]], representation: str='quat') -> Tuple[float, float, float, float]:
        current_quat_xyzw = self.get_ee_orientation()
        if 'z' == representation:
            current_yaw = Rotation.from_quat(current_quat_xyzw).as_euler('xyz')[2]
            current_quat_xyzw = Rotation.from_euler('xyz', [np.pi, 0, current_yaw]).as_quat()
        relative_quat_xyzw = None
        if 'quat' == representation:
            relative_quat_xyzw = rotation
        elif '6d' == representation:
            vectors = tuple((rotation[x:x + 3] for x, _ in enumerate(rotation) if x % 3 == 0))
            relative_quat_xyzw = orientation_6d_to_quat(vectors[0], vectors[1])
        elif 'z' == representation:
            rotation = self.scale_relative_rotation(rotation)
            relative_quat_xyzw = Rotation.from_euler('xyz', [0, 0, rotation]).as_quat()
        target_quat_xyzw = quat_mul(current_quat_xyzw, relative_quat_xyzw)
        target_quat_xyzw /= np.linalg.norm(target_quat_xyzw)
        return target_quat_xyzw

    def scale_relative_translation(self, translation: Tuple[float, float, float]) -> Tuple[float, float, float]:
        return (self.__scaling_factor_translation * translation[0], self.__scaling_factor_translation * translation[1], self.__scaling_factor_translation * translation[2])

    def scale_relative_rotation(self, rotation: Union[float, Tuple[float, float, float], np.floating, np.ndarray]) -> float:
        if not hasattr(rotation, '__len__'):
            return self.__scaling_factor_rotation * rotation
        else:
            return (self.__scaling_factor_rotation * rotation[0], self.__scaling_factor_rotation * rotation[1], self.__scaling_factor_rotation * rotation[2])

    def restrict_position_goal_to_workspace(self, position: Tuple[float, float, float]) -> Tuple[float, float, float]:
        return (min(self.workspace_max_bound[0], max(self.workspace_min_bound[0], position[0])), min(self.workspace_max_bound[1], max(self.workspace_min_bound[1], position[1])), min(self.workspace_max_bound[2], max(self.workspace_min_bound[2], position[2])))

    def restrict_servo_translation_to_workspace(self, translation: Tuple[float, float, float]) -> Tuple[float, float, float]:
        current_ee_position = self.get_ee_position()
        translation = tuple((0.0 if current_ee_position[i] > self.workspace_max_bound[i] and translation[i] > 0.0 or (current_ee_position[i] < self.workspace_min_bound[i] and translation[i] < 0.0) else translation[i] for i in range(3)))
        return translation

    def get_ee_pose(self) -> Optional[Tuple[Tuple[float, float, float], Tuple[float, float, float, float]]]:
        """
        Return the current pose of the end effector with respect to arm base link.
        """
        try:
            robot_model = self.world.to_gazebo().get_model(self.robot_name).to_gazebo()
            ee_position, ee_quat_xyzw = get_model_pose(world=self.world, model=robot_model, link=self.robot_ee_link_name, xyzw=True)
            return transform_change_reference_frame_pose(world=self.world, position=ee_position, quat=ee_quat_xyzw, target_model=robot_model, target_link=self.robot_arm_base_link_name, xyzw=True)
        except Exception as e:
            self.get_logger().warn(f'Cannot get end effector pose from Gazebo ({e}), using tf2...')
            transform = self.tf2_listener.lookup_transform_sync(source_frame=self.robot_ee_link_name, target_frame=self.robot_arm_base_link_name, retry=False)
            if transform is not None:
                return ((transform.translation.x, transform.translation.y, transform.translation.z), (transform.rotation.x, transform.rotation.y, transform.rotation.z, transform.rotation.w))
            else:
                self.get_logger().error('Cannot get pose of the end effector (default values are returned)')
                return ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0))

    def get_ee_position(self) -> Tuple[float, float, float]:
        """
        Return the current position of the end effector with respect to arm base link.
        """
        try:
            robot_model = self.world.to_gazebo().get_model(self.robot_name).to_gazebo()
            ee_position = get_model_position(world=self.world, model=robot_model, link=self.robot_ee_link_name)
            return transform_change_reference_frame_position(world=self.world, position=ee_position, target_model=robot_model, target_link=self.robot_arm_base_link_name)
        except Exception as e:
            self.get_logger().warn(f'Cannot get end effector position from Gazebo ({e}), using tf2...')
            transform = self.tf2_listener.lookup_transform_sync(source_frame=self.robot_ee_link_name, target_frame=self.robot_arm_base_link_name, retry=False)
            if transform is not None:
                return (transform.translation.x, transform.translation.y, transform.translation.z)
            else:
                self.get_logger().error('Cannot get position of the end effector (default values are returned)')
                return (0.0, 0.0, 0.0)

    def get_ee_orientation(self) -> Tuple[float, float, float, float]:
        """
        Return the current xyzw quaternion of the end effector with respect to arm base link.
        """
        try:
            robot_model = self.world.to_gazebo().get_model(self.robot_name).to_gazebo()
            ee_quat_xyzw = get_model_orientation(world=self.world, model=robot_model, link=self.robot_ee_link_name, xyzw=True)
            return transform_change_reference_frame_orientation(world=self.world, quat=ee_quat_xyzw, target_model=robot_model, target_link=self.robot_arm_base_link_name, xyzw=True)
        except Exception as e:
            self.get_logger().warn(f'Cannot get end effector orientation from Gazebo ({e}), using tf2...')
            transform = self.tf2_listener.lookup_transform_sync(source_frame=self.robot_ee_link_name, target_frame=self.robot_arm_base_link_name, retry=False)
            if transform is not None:
                return (transform.rotation.x, transform.rotation.y, transform.rotation.z, transform.rotation.w)
            else:
                self.get_logger().error('Cannot get orientation of the end effector (default values are returned)')
                return (0.0, 0.0, 0.0, 1.0)

    def get_object_position(self, object_model: Union[ModelWrapper, str]) -> Tuple[float, float, float]:
        """
        Return the current position of an object with respect to arm base link.
        Note: Only simulated objects are currently supported.
        """
        try:
            object_position = get_model_position(world=self.world, model=object_model)
            return transform_change_reference_frame_position(world=self.world, position=object_position, target_model=self.robot_name, target_link=self.robot_arm_base_link_name)
        except Exception as e:
            self.get_logger().error(f'Cannot get position of {object_model} object (default values are returned): {e}')
            return (0.0, 0.0, 0.0)

    def get_object_positions(self) -> Dict[str, Tuple[float, float, float]]:
        """
        Return the current position of all objects with respect to arm base link.
        Note: Only simulated objects are currently supported.
        """
        object_positions = {}
        try:
            robot_model = self.world.to_gazebo().get_model(self.robot_name).to_gazebo()
            robot_arm_base_link = robot_model.get_link(link_name=self.robot_arm_base_link_name)
            for object_name in self.object_names:
                object_position = get_model_position(world=self.world, model=object_name)
                object_positions[object_name] = transform_change_reference_frame_position(world=self.world, position=object_position, target_model=robot_model, target_link=robot_arm_base_link)
        except Exception as e:
            self.get_logger().error(f'Cannot get positions of all objects (empty Dict is returned): {e}')
        return object_positions

    def substitute_special_frame(self, frame_id: str) -> str:
        if 'arm_base_link' == frame_id:
            return self.robot_arm_base_link_name
        elif 'base_link' == frame_id:
            return self.robot_base_link_name
        elif 'end_effector' == frame_id:
            return self.robot_ee_link_name
        elif 'world' == frame_id:
            try:
                return self.world.to_gazebo().name()
            except Exception as e:
                self.get_logger().warn(f'')
                return 'drl_grasping_world'
        else:
            return frame_id

    def wait_until_action_executed(self):
        if self._use_servo:
            rate = self.create_rate(self.agent_rate)
            try:
                if rclpy.ok():
                    rate.sleep()
            except KeyboardInterrupt:
                pass
        self.moveit2.wait_until_executed()
        if self._enable_gripper:
            self.gripper.wait_until_executed()

    def move_to_initial_joint_configuration(self):
        self.moveit2.move_to_configuration(self.initial_arm_joint_positions)
        if self.robot_model_class.CLOSED_GRIPPER_JOINT_POSITIONS == self.initial_gripper_joint_positions:
            self.gripper.reset_close()
        else:
            self.gripper.reset_open()

    def check_terrain_collision(self) -> bool:
        """
        Returns true if robot links are in collision with the ground.
        """
        robot_name_len = len(self.robot_name)
        for contact in self.world.get_model(self.terrain_name).contacts():
            if len(contact.body_b) > robot_name_len:
                if contact.body_b[:robot_name_len] == self.robot_name:
                    link = contact.body_b[len(self.robot_name) + 2:]
                    if not self.robot_base_link_name == link and (link in self.robot_arm_link_names or link in self.robot_gripper_link_names):
                        return True
        return False

    def check_all_objects_outside_workspace(self, object_positions: Dict[str, Tuple[float, float, float]]) -> bool:
        """
        Returns true if all objects are outside the workspace
        """
        return all([self.check_object_outside_workspace(object_position) for object_position in object_positions.values()])

    def check_object_outside_workspace(self, object_position: Tuple[float, float, float]) -> bool:
        """
        Returns true if the object is outside the workspace
        """
        return object_position[0] < self.workspace_min_bound[0] or object_position[1] < self.workspace_min_bound[1] or object_position[2] < self.workspace_min_bound[2] or (object_position[0] > self.workspace_max_bound[0]) or (object_position[1] > self.workspace_max_bound[1]) or (object_position[2] > self.workspace_max_bound[2])

    def add_parameter_overrides(self, parameter_overrides: Dict[str, any]):
        self.add_task_parameter_overrides(parameter_overrides)
        self.add_randomizer_parameter_overrides(parameter_overrides)

    def add_task_parameter_overrides(self, parameter_overrides: Dict[str, any]):
        self.__task_parameter_overrides.update(parameter_overrides)

    def add_randomizer_parameter_overrides(self, parameter_overrides: Dict[str, any]):
        self._randomizer_parameter_overrides.update(parameter_overrides)

    def __consume_parameter_overrides(self):
        for key, value in self.__task_parameter_overrides.items():
            if hasattr(self, key):
                setattr(self, key, value)
            elif hasattr(self, f'_{key}'):
                setattr(self, f'_{key}', value)
            elif hasattr(self, f'__{key}'):
                setattr(self, f'__{key}', value)
            else:
                self.get_logger().error(f"Override '{key}' is not supperted by the task.")
        self.__task_parameter_overrides.clear()

def __init__(self, agent_rate: float, robot_model: str, workspace_frame_id: str, workspace_centre: Tuple[float, float, float], workspace_volume: Tuple[float, float, float], ignore_new_actions_while_executing: bool, use_servo: bool, scaling_factor_translation: float, scaling_factor_rotation: float, restrict_position_goal_to_workspace: bool, enable_gripper: bool, num_threads: int, **kwargs):
    self.id = next(self._ids)
    Task.__init__(self, agent_rate=agent_rate)
    try:
        rclpy.init()
    except Exception as e:
        if not rclpy.ok():
            sys.exit(f'ROS 2 context could not be initialised: {e}')
    Node.__init__(self, f'drl_grasping_{self.id}')
    self._callback_group = ReentrantCallbackGroup()
    if num_threads == 1:
        executor = SingleThreadedExecutor()
    elif num_threads > 1:
        executor = MultiThreadedExecutor(num_threads=num_threads)
    else:
        executor = MultiThreadedExecutor(num_threads=multiprocessing.cpu_count())
    executor.add_node(self)
    self._executor_thread = Thread(target=executor.spin, daemon=True, args=())
    self._executor_thread.start()
    self.robot_model_class = get_robot_model_class(robot_model)
    self.workspace_centre = (workspace_centre[0], workspace_centre[1], workspace_centre[2] + self.robot_model_class.BASE_LINK_Z_OFFSET)
    self.workspace_volume = workspace_volume
    self._restrict_position_goal_to_workspace = restrict_position_goal_to_workspace
    self._use_servo = use_servo
    self.__scaling_factor_translation = scaling_factor_translation
    self.__scaling_factor_rotation = scaling_factor_rotation
    self._enable_gripper = enable_gripper
    workspace_volume_half = (workspace_volume[0] / 2, workspace_volume[1] / 2, workspace_volume[2] / 2)
    self.workspace_min_bound = (self.workspace_centre[0] - workspace_volume_half[0], self.workspace_centre[1] - workspace_volume_half[1], self.workspace_centre[2] - workspace_volume_half[2])
    self.workspace_max_bound = (self.workspace_centre[0] + workspace_volume_half[0], self.workspace_centre[1] + workspace_volume_half[1], self.workspace_centre[2] + workspace_volume_half[2])
    self.robot_prefix = self.robot_model_class.DEFAULT_PREFIX
    if 0 == self.id:
        self.robot_name = self.robot_model_class.ROBOT_MODEL_NAME
    else:
        self.robot_name = f'{self.robot_model_class.ROBOT_MODEL_NAME}{self.id}'
        if self.robot_prefix.endswith('_'):
            self.robot_prefix = f'{self.robot_prefix[:-1]}{self.id}_'
        elif self.robot_prefix.empty():
            self.robot_prefix = f'robot{self.id}_'
    self.robot_base_link_name = self.robot_model_class.get_robot_base_link_name(self.robot_prefix)
    self.robot_arm_base_link_name = self.robot_model_class.get_arm_base_link_name(self.robot_prefix)
    self.robot_ee_link_name = self.robot_model_class.get_ee_link_name(self.robot_prefix)
    self.robot_arm_link_names = self.robot_model_class.get_arm_link_names(self.robot_prefix)
    self.robot_gripper_link_names = self.robot_model_class.get_gripper_link_names(self.robot_prefix)
    self.robot_arm_joint_names = self.robot_model_class.get_arm_joint_names(self.robot_prefix)
    self.robot_gripper_joint_names = self.robot_model_class.get_gripper_joint_names(self.robot_prefix)
    self.workspace_frame_id = self.substitute_special_frame(workspace_frame_id)
    self.initial_arm_joint_positions = self.robot_model_class.DEFAULT_ARM_JOINT_POSITIONS
    self.initial_gripper_joint_positions = self.robot_model_class.DEFAULT_GRIPPER_JOINT_POSITIONS
    self.terrain_name = 'terrain'
    self.object_names = []
    self.tf2_listener = Tf2Listener(node=self)
    self.tf2_broadcaster = Tf2Broadcaster(node=self)
    self.moveit2 = MoveIt2(node=self, joint_names=self.robot_arm_joint_names, base_link_name=self.robot_arm_base_link_name, end_effector_name=self.robot_ee_link_name, execute_via_moveit=False, ignore_new_calls_while_executing=ignore_new_actions_while_executing, callback_group=self._callback_group)
    if self._use_servo:
        self.servo = MoveIt2Servo(node=self, frame_id=self.robot_arm_base_link_name, linear_speed=scaling_factor_translation, angular_speed=scaling_factor_rotation, callback_group=self._callback_group)
    self.gripper = MoveIt2Gripper(node=self, gripper_joint_names=self.robot_gripper_joint_names, open_gripper_joint_positions=self.robot_model_class.OPEN_GRIPPER_JOINT_POSITIONS, closed_gripper_joint_positions=self.robot_model_class.CLOSED_GRIPPER_JOINT_POSITIONS, skip_planning=True, ignore_new_calls_while_executing=ignore_new_actions_while_executing, callback_group=self._callback_group)
    self.__task_parameter_overrides: Dict[str, any] = {}
    self._randomizer_parameter_overrides: Dict[str, any] = {}

def wait_until_action_executed(self):
    if self._use_servo:
        rate = self.create_rate(self.agent_rate)
        try:
            if rclpy.ok():
                rate.sleep()
        except KeyboardInterrupt:
            pass
    self.moveit2.wait_until_executed()
    if self._enable_gripper:
        self.gripper.wait_until_executed()

class Panda(model_wrapper.ModelWrapper, model_with_file.ModelWithFile):
    ROBOT_MODEL_NAME: str = 'panda'
    DEFAULT_PREFIX: str = 'panda_'
    __DESCRIPTION_PACKAGE = ROBOT_MODEL_NAME + '_description'
    __DEFAULT_XACRO_FILE = path.join(get_package_share_directory(__DESCRIPTION_PACKAGE), 'urdf', ROBOT_MODEL_NAME + '.urdf.xacro')
    __DEFAULT_XACRO_MAPPINGS: Dict[str, any] = {'name': ROBOT_MODEL_NAME, 'gripper': True, 'collision_arm': False, 'collision_gripper': True, 'ros2_control': True, 'ros2_control_plugin': 'ign', 'ros2_control_command_interface': 'effort', 'gazebo_preserve_fixed_joint': True}
    __XACRO_MODEL_PATH_REMAP: Tuple[str, str] = (__DESCRIPTION_PACKAGE, ROBOT_MODEL_NAME)
    DEFAULT_ARM_JOINT_POSITIONS: List[float] = (0.0, -0.7853981633974483, 0.0, -2.356194490192345, 0.0, 1.5707963267948966, 0.7853981633974483)
    OPEN_GRIPPER_JOINT_POSITIONS: List[float] = (0.04, 0.04)
    CLOSED_GRIPPER_JOINT_POSITIONS: List[float] = (0.0, 0.0)
    DEFAULT_GRIPPER_JOINT_POSITIONS: List[float] = OPEN_GRIPPER_JOINT_POSITIONS
    BASE_LINK_Z_OFFSET: float = 0.0

    def __init__(self, world: scenario.World, name: str=ROBOT_MODEL_NAME, position: List[float]=(0, 0, 0), orientation: List[float]=(1, 0, 0, 0), model_file: str=None, use_fuel: bool=False, use_xacro: bool=True, xacro_file: str=__DEFAULT_XACRO_FILE, xacro_mappings: Dict[str, any]=__DEFAULT_XACRO_MAPPINGS, initial_arm_joint_positions: List[float]=DEFAULT_ARM_JOINT_POSITIONS, initial_gripper_joint_positions: List[float]=OPEN_GRIPPER_JOINT_POSITIONS, **kwargs):
        self.__prefix = f'{name}_'
        self.__initial_arm_joint_positions = initial_arm_joint_positions
        self.__initial_gripper_joint_positions = initial_gripper_joint_positions
        if model_file is None:
            if use_xacro:
                mappings = self.__DEFAULT_XACRO_MAPPINGS
                mappings.update(kwargs)
                mappings.update(xacro_mappings)
                model_file = xacro2sdf(input_file_path=xacro_file, mappings=mappings, model_path_remap=self.__XACRO_MODEL_PATH_REMAP)
            else:
                model_file = self.get_model_file(fuel=use_fuel)
        model_name = get_unique_model_name(world, name)
        initial_pose = scenario.Pose(position, orientation)
        if use_xacro:
            insert_fn = scenario_gazebo.World.insert_model_from_string
        else:
            insert_fn = scenario_gazebo.World.insert_model_from_file
        ok_model = insert_fn(world.to_gazebo(), model_file, initial_pose, model_name)
        if not ok_model:
            raise RuntimeError('Failed to insert ' + model_name)
        model = world.get_model(model_name)
        self.set_initial_joint_positions(model)
        super().__init__(model=model)

    def set_initial_joint_positions(self, model):
        model = model.to_gazebo()
        if not model.reset_joint_positions(self.initial_arm_joint_positions, self.arm_joint_names):
            raise RuntimeError("Failed to set initial positions of arm's joints")
        if not model.reset_joint_positions(self.initial_gripper_joint_positions, self.gripper_joint_names):
            raise RuntimeError("Failed to set initial positions of gripper's joints")

    @classmethod
    def get_model_file(cls, fuel: bool=False) -> str:
        if fuel:
            raise NotImplementedError
            return scenario_gazebo.get_model_file_from_fuel('https://fuel.ignitionrobotics.org/1.0/AndrejOrsula/models/' + cls.ROBOT_MODEL_NAME)
        else:
            return cls.ROBOT_MODEL_NAME

    @property
    def is_mobile(self) -> bool:
        return False

    @property
    def prefix(self) -> str:
        return self.__prefix

    @property
    def joint_names(self) -> List[str]:
        return self.move_base_joint_names + self.manipulator_joint_names

    @property
    def move_base_joint_names(self) -> List[str]:
        return []

    @property
    def manipulator_joint_names(self) -> List[str]:
        return self.arm_joint_names + self.gripper_joint_names

    @classmethod
    def get_arm_joint_names(cls, prefix: str='') -> List[str]:
        return [prefix + 'joint1', prefix + 'joint2', prefix + 'joint3', prefix + 'joint4', prefix + 'joint5', prefix + 'joint6', prefix + 'joint7']

    @property
    def arm_joint_names(self) -> List[str]:
        return self.get_arm_joint_names(self.prefix)

    @classmethod
    def get_gripper_joint_names(cls, prefix: str='') -> List[str]:
        return [prefix + 'finger_joint1', prefix + 'finger_joint2']

    @property
    def gripper_joint_names(self) -> List[str]:
        return self.get_gripper_joint_names(self.prefix)

    @property
    def move_base_joint_limits(self) -> Optional[List[Tuple[float, float]]]:
        return None

    @property
    def arm_joint_limits(self) -> Optional[List[Tuple[float, float]]]:
        return [(-2.897246558310587, 2.897246558310587), (-1.762782544514273, 1.762782544514273), (-2.897246558310587, 2.897246558310587), (-3.07177948351002, -0.06981317007977318), (-2.897246558310587, 2.897246558310587), (-0.0174532925199433, 3.752457891787809), (-2.897246558310587, 2.897246558310587)]

    @property
    def gripper_joint_limits(self) -> Optional[List[Tuple[float, float]]]:
        return [(0.0, 0.04), (0.0, 0.04)]

    @property
    def gripper_joints_close_towards_positive(self) -> bool:
        return self.OPEN_GRIPPER_JOINT_POSITIONS[0] < self.CLOSED_GRIPPER_JOINT_POSITIONS[0]

    @property
    def initial_arm_joint_positions(self) -> List[float]:
        return self.__initial_arm_joint_positions

    @property
    def initial_gripper_joint_positions(self) -> List[float]:
        return self.__initial_gripper_joint_positions

    @property
    def passive_joint_names(self) -> List[str]:
        return self.manipulator_passive_joint_names + self.move_base_passive_joint_names

    @property
    def move_base_passive_joint_names(self) -> List[str]:
        return []

    @property
    def manipulator_passive_joint_names(self) -> List[str]:
        return self.arm_passive_joint_names + self.gripper_passive_joint_names

    @property
    def arm_passive_joint_names(self) -> List[str]:
        return []

    @property
    def gripper_passive_joint_names(self) -> List[str]:
        return []

    @classmethod
    def get_robot_base_link_name(cls, prefix: str='') -> str:
        return cls.get_arm_base_link_name(prefix)

    @property
    def robot_base_link_name(self) -> str:
        return self.get_robot_base_link_name(self.prefix)

    @classmethod
    def get_arm_base_link_name(cls, prefix: str='') -> str:
        return prefix + 'link0'

    @property
    def arm_base_link_name(self) -> str:
        return self.get_arm_base_link_name(self.prefix)

    @classmethod
    def get_ee_link_name(cls, prefix: str='') -> str:
        return prefix + 'hand_tcp'

    @property
    def ee_link_name(self) -> str:
        return self.get_ee_link_name(self.prefix)

    @classmethod
    def get_wheel_link_names(cls, prefix: str='') -> List[str]:
        return []

    @property
    def wheel_link_names(self) -> List[str]:
        return self.get_wheel_link_names(self.prefix)

    @classmethod
    def get_arm_link_names(cls, prefix: str='') -> List[str]:
        return [prefix + 'link0', prefix + 'link1', prefix + 'link2', prefix + 'link3', prefix + 'link4', prefix + 'link5', prefix + 'link6', prefix + 'link7']

    @property
    def arm_link_names(self) -> List[str]:
        return self.get_arm_link_names(self.prefix)

    @classmethod
    def get_gripper_link_names(cls, prefix: str='') -> List[str]:
        return [prefix + 'leftfinger', prefix + 'rightfinger']

    @property
    def gripper_link_names(self) -> List[str]:
        return self.get_gripper_link_names(self.prefix)

@property
def arm_joint_names(self) -> List[str]:
    return self.get_arm_joint_names(self.prefix)

@property
def gripper_joint_names(self) -> List[str]:
    return self.get_gripper_joint_names(self.prefix)

@classmethod
def get_robot_base_link_name(cls, prefix: str='') -> str:
    return cls.get_arm_base_link_name(prefix)

@property
def robot_base_link_name(self) -> str:
    return self.get_robot_base_link_name(self.prefix)

@property
def arm_base_link_name(self) -> str:
    return self.get_arm_base_link_name(self.prefix)

@property
def ee_link_name(self) -> str:
    return self.get_ee_link_name(self.prefix)

@property
def arm_link_names(self) -> List[str]:
    return self.get_arm_link_names(self.prefix)

@property
def gripper_link_names(self) -> List[str]:
    return self.get_gripper_link_names(self.prefix)

class LunalabSummitXlGen(model_wrapper.ModelWrapper, model_with_file.ModelWithFile):
    ROBOT_MODEL_NAME: str = 'lunalab_summit_xl_gen'
    DEFAULT_PREFIX: str = 'robot_'
    __PREFIX_MOBILE_BASE: str = 'summit_xl_'
    __PREFIX_MANIPULATOR: str = 'j2s7s300_'
    __DESCRIPTION_PACKAGE = ROBOT_MODEL_NAME + '_description'
    __DEFAULT_XACRO_FILE = path.join(get_package_share_directory(__DESCRIPTION_PACKAGE), 'urdf', ROBOT_MODEL_NAME + '.urdf.xacro')
    __DEFAULT_XACRO_MAPPINGS: Dict[str, any] = {'name': ROBOT_MODEL_NAME, 'prefix': DEFAULT_PREFIX, 'safety_limits': True, 'safety_soft_limit_margin': 0.17453293, 'safety_k_position': 20, 'collision_chassis': False, 'collision_wheels': True, 'collision_arm': False, 'collision_gripper': True, 'high_quality_mesh': True, 'mimic_gripper_joints': False, 'ros2_control': True, 'ros2_control_plugin': 'ign', 'ros2_control_command_interface': 'effort', 'gazebo_preserve_fixed_joint': True, 'gazebo_self_collide': False, 'gazebo_self_collide_fingers': True, 'gazebo_diff_drive': True, 'gazebo_joint_trajectory_controller': False, 'gazebo_joint_state_publisher': False, 'gazebo_pose_publisher': True}
    __XACRO_MODEL_PATH_REMAP: Tuple[str, str] = (__DESCRIPTION_PACKAGE, ROBOT_MODEL_NAME)
    DEFAULT_ARM_JOINT_POSITIONS: List[float] = (0.0, 3.141592653589793, 0.0, 4.71238898038469, 0.0, 1.5707963267948966, 0.0)
    OPEN_GRIPPER_JOINT_POSITIONS: List[float] = (0.2, 0.2, 0.2)
    CLOSED_GRIPPER_JOINT_POSITIONS: List[float] = (1.3, 1.3, 1.3)
    DEFAULT_GRIPPER_JOINT_POSITIONS: List[float] = OPEN_GRIPPER_JOINT_POSITIONS
    BASE_LINK_Z_OFFSET: float = -0.22

    def __init__(self, world: scenario.World, name: str=ROBOT_MODEL_NAME, prefix: str=DEFAULT_PREFIX, position: List[float]=(0, 0, 0), orientation: List[float]=(1, 0, 0, 0), model_file: str=None, use_fuel: bool=False, use_xacro: bool=True, xacro_file: str=__DEFAULT_XACRO_FILE, xacro_mappings: Dict[str, any]=__DEFAULT_XACRO_MAPPINGS, initial_arm_joint_positions: List[float]=DEFAULT_ARM_JOINT_POSITIONS, initial_gripper_joint_positions: List[float]=OPEN_GRIPPER_JOINT_POSITIONS, **kwargs):
        self.__prefix = prefix
        self.__initial_arm_joint_positions = initial_arm_joint_positions
        self.__initial_gripper_joint_positions = initial_gripper_joint_positions
        if model_file is None:
            if use_xacro:
                mappings = self.__DEFAULT_XACRO_MAPPINGS
                mappings.update(kwargs)
                mappings.update(xacro_mappings)
                mappings.update({'prefix': prefix})
                model_file = xacro2sdf(input_file_path=xacro_file, mappings=mappings, model_path_remap=self.__XACRO_MODEL_PATH_REMAP)
            else:
                model_file = self.get_model_file(fuel=use_fuel)
        model_name = get_unique_model_name(world, name)
        initial_pose = scenario.Pose(position, orientation)
        if use_xacro:
            insert_fn = scenario_gazebo.World.insert_model_from_string
        else:
            insert_fn = scenario_gazebo.World.insert_model_from_file
        ok_model = insert_fn(world.to_gazebo(), model_file, initial_pose, model_name)
        if not ok_model:
            raise RuntimeError('Failed to insert ' + model_name)
        model = world.get_model(model_name)
        self.set_initial_joint_positions(model)
        super().__init__(model=model)

    def set_initial_joint_positions(self, model):
        model = model.to_gazebo()
        if not model.reset_joint_positions(self.initial_arm_joint_positions, self.arm_joint_names):
            raise RuntimeError("Failed to set initial positions of arm's joints")
        if not model.reset_joint_positions(self.initial_gripper_joint_positions, self.gripper_joint_names):
            raise RuntimeError("Failed to set initial positions of gripper's joints")

    @classmethod
    def get_model_file(cls, fuel: bool=False) -> str:
        if fuel:
            raise NotImplementedError
            return scenario_gazebo.get_model_file_from_fuel('https://fuel.ignitionrobotics.org/1.0/AndrejOrsula/models/' + cls.ROBOT_MODEL_NAME)
        else:
            return cls.ROBOT_MODEL_NAME

    @property
    def is_mobile(self) -> bool:
        return True

    @property
    def prefix(self) -> str:
        return self.__prefix

    @property
    def joint_names(self) -> List[str]:
        return self.move_base_joint_names + self.manipulator_joint_names

    @property
    def move_base_joint_names(self) -> List[str]:
        return [self.prefix + self.__PREFIX_MOBILE_BASE + 'back_left_wheel_joint', self.prefix + self.__PREFIX_MOBILE_BASE + 'back_right_wheel_joint', self.prefix + self.__PREFIX_MOBILE_BASE + 'front_left_wheel_joint', self.prefix + self.__PREFIX_MOBILE_BASE + 'front_right_wheel_joint']

    @property
    def manipulator_joint_names(self) -> List[str]:
        return self.arm_joint_names + self.gripper_joint_names

    @classmethod
    def get_arm_joint_names(cls, prefix: str='') -> List[str]:
        return [prefix + cls.__PREFIX_MANIPULATOR + 'joint_1', prefix + cls.__PREFIX_MANIPULATOR + 'joint_2', prefix + cls.__PREFIX_MANIPULATOR + 'joint_3', prefix + cls.__PREFIX_MANIPULATOR + 'joint_4', prefix + cls.__PREFIX_MANIPULATOR + 'joint_5', prefix + cls.__PREFIX_MANIPULATOR + 'joint_6', prefix + cls.__PREFIX_MANIPULATOR + 'joint_7']

    @property
    def arm_joint_names(self) -> List[str]:
        return self.get_arm_joint_names(self.prefix)

    @classmethod
    def get_gripper_joint_names(cls, prefix: str='') -> List[str]:
        return [prefix + cls.__PREFIX_MANIPULATOR + 'joint_finger_1', prefix + cls.__PREFIX_MANIPULATOR + 'joint_finger_2', prefix + cls.__PREFIX_MANIPULATOR + 'joint_finger_3']

    @property
    def gripper_joint_names(self) -> List[str]:
        return self.get_gripper_joint_names(self.prefix)

    @property
    def move_base_joint_limits(self) -> Optional[List[Tuple[float, float]]]:
        return None

    @property
    def arm_joint_limits(self) -> Optional[List[Tuple[float, float]]]:
        return [(-6.283185307179586, 6.283185307179586), (0.8203047484373349, 5.462880558742252), (-6.283185307179586, 6.283185307179586), (0.5235987755982988, 5.759586531581287), (-6.283185307179586, 6.283185307179586), (1.1344640137963142, 5.148721293383272), (-6.283185307179586, 6.283185307179586)]

    @property
    def gripper_joint_limits(self) -> Optional[List[Tuple[float, float]]]:
        return [(0.0, 1.51), (0.0, 1.51), (0.0, 1.51)]

    @property
    def gripper_joints_close_towards_positive(self) -> bool:
        return self.OPEN_GRIPPER_JOINT_POSITIONS[0] < self.CLOSED_GRIPPER_JOINT_POSITIONS[0]

    @property
    def initial_arm_joint_positions(self) -> List[float]:
        return self.__initial_arm_joint_positions

    @property
    def initial_gripper_joint_positions(self) -> List[float]:
        return self.__initial_gripper_joint_positions

    @property
    def passive_joint_names(self) -> List[str]:
        return self.manipulator_passive_joint_names + self.move_base_passive_joint_names

    @property
    def move_base_passive_joint_names(self) -> List[str]:
        return []

    @property
    def manipulator_passive_joint_names(self) -> List[str]:
        return self.arm_passive_joint_names + self.gripper_passive_joint_names

    @property
    def arm_passive_joint_names(self) -> List[str]:
        return []

    @property
    def gripper_passive_joint_names(self) -> List[str]:
        return [self.prefix + self.__PREFIX_MANIPULATOR + 'joint_finger_tip_1', self.prefix + self.__PREFIX_MANIPULATOR + 'joint_finger_tip_2', self.prefix + self.__PREFIX_MANIPULATOR + 'joint_finger_tip_3']

    @classmethod
    def get_robot_base_link_name(cls, prefix: str='') -> str:
        return prefix + cls.__PREFIX_MOBILE_BASE + 'base_footprint'

    @property
    def robot_base_link_name(self) -> str:
        return self.get_robot_base_link_name(self.prefix)

    @classmethod
    def get_arm_base_link_name(cls, prefix: str='') -> str:
        return prefix + cls.__PREFIX_MANIPULATOR + 'link_base'

    @property
    def arm_base_link_name(self) -> str:
        return self.get_arm_base_link_name(self.prefix)

    @classmethod
    def get_ee_link_name(cls, prefix: str='') -> str:
        return prefix + cls.__PREFIX_MANIPULATOR + 'end_effector'

    @property
    def ee_link_name(self) -> str:
        return self.get_ee_link_name(self.prefix)

    @classmethod
    def get_wheel_link_names(cls, prefix: str='') -> List[str]:
        return [prefix + cls.__PREFIX_MOBILE_BASE + 'back_left_wheel', prefix + cls.__PREFIX_MOBILE_BASE + 'back_right_wheel', prefix + cls.__PREFIX_MOBILE_BASE + 'front_left_wheel', prefix + cls.__PREFIX_MOBILE_BASE + 'front_right_wheel']

    @property
    def wheel_link_names(self) -> List[str]:
        return self.get_wheel_link_names(self.prefix)

    @classmethod
    def get_arm_link_names(cls, prefix: str='') -> List[str]:
        return [prefix + cls.__PREFIX_MANIPULATOR + 'link_base', prefix + cls.__PREFIX_MANIPULATOR + 'link_1', prefix + cls.__PREFIX_MANIPULATOR + 'link_2', prefix + cls.__PREFIX_MANIPULATOR + 'link_3', prefix + cls.__PREFIX_MANIPULATOR + 'link_4', prefix + cls.__PREFIX_MANIPULATOR + 'link_5', prefix + cls.__PREFIX_MANIPULATOR + 'link_6', prefix + cls.__PREFIX_MANIPULATOR + 'link_7']

    @property
    def arm_link_names(self) -> List[str]:
        return self.get_arm_link_names(self.prefix)

    @classmethod
    def get_gripper_link_names(cls, prefix: str='') -> List[str]:
        return [prefix + cls.__PREFIX_MANIPULATOR + 'link_finger_1', prefix + cls.__PREFIX_MANIPULATOR + 'link_finger_2', prefix + cls.__PREFIX_MANIPULATOR + 'link_finger_3', prefix + cls.__PREFIX_MANIPULATOR + 'link_finger_tip_1', prefix + cls.__PREFIX_MANIPULATOR + 'link_finger_tip_2', prefix + cls.__PREFIX_MANIPULATOR + 'link_finger_tip_3']

    @property
    def gripper_link_names(self) -> List[str]:
        return self.get_gripper_link_names(self.prefix)

@property
def arm_joint_names(self) -> List[str]:
    return self.get_arm_joint_names(self.prefix)

@property
def gripper_joint_names(self) -> List[str]:
    return self.get_gripper_joint_names(self.prefix)

@property
def robot_base_link_name(self) -> str:
    return self.get_robot_base_link_name(self.prefix)

@property
def arm_base_link_name(self) -> str:
    return self.get_arm_base_link_name(self.prefix)

@property
def ee_link_name(self) -> str:
    return self.get_ee_link_name(self.prefix)

@property
def arm_link_names(self) -> List[str]:
    return self.get_arm_link_names(self.prefix)

@property
def gripper_link_names(self) -> List[str]:
    return self.get_gripper_link_names(self.prefix)

