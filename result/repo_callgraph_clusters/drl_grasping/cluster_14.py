# Cluster 14

class Grasp(Manipulation, abc.ABC):

    def __init__(self, gripper_dead_zone: float, full_3d_orientation: bool, obs_n_stacked: int=1, preload_replay_buffer: bool=False, **kwargs):
        Manipulation.__init__(self, **kwargs)
        self.curriculum = GraspCurriculum(task=self, **kwargs)
        self.__gripper_dead_zone = gripper_dead_zone
        self.__full_3d_orientation = full_3d_orientation
        self.__preload_replay_buffer = preload_replay_buffer
        self._obs_n_stacked = obs_n_stacked
        self.__stacked_obs = deque([], maxlen=self._obs_n_stacked)

    def create_action_space(self) -> ActionSpace:
        if self.__full_3d_orientation:
            if self._use_servo:
                return gym.spaces.Box(low=-1.0, high=1.0, shape=(7,), dtype=np.float32)
            else:
                return gym.spaces.Box(low=-1.0, high=1.0, shape=(10,), dtype=np.float32)
        else:
            return gym.spaces.Box(low=-1.0, high=1.0, shape=(5,), dtype=np.float32)

    def create_observation_space(self) -> ObservationSpace:
        return gym.spaces.Box(low=np.array((-1.0, -np.inf, -np.inf, -np.inf, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -np.inf, -np.inf, -np.inf) * self._obs_n_stacked), high=np.array((1.0, np.inf, np.inf, np.inf, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, np.inf, np.inf, np.inf) * self._obs_n_stacked), shape=(13 * self._obs_n_stacked,), dtype=np.float32)

    def set_action(self, action: Action):
        if self.__preload_replay_buffer:
            action = self._demonstrate_action()
        self.get_logger().debug(f'action: {action}')
        gripper_action = action[0]
        if gripper_action < -self.__gripper_dead_zone:
            self.gripper.close()
        elif gripper_action > self.__gripper_dead_zone:
            self.gripper.open()
        else:
            pass
        if self._use_servo:
            linear = action[1:4]
            if self._restrict_position_goal_to_workspace:
                linear = self.restrict_servo_translation_to_workspace(linear)
            if self.__full_3d_orientation:
                angular = action[4:7]
            else:
                angular = [0.0, 0.0, action[4]]
            self.servo(linear=linear, angular=angular)
        else:
            position = self.get_relative_ee_position(action[1:4])
            if self.__full_3d_orientation:
                quat_xyzw = self.get_relative_ee_orientation(rotation=action[4:10], representation='6d')
            else:
                quat_xyzw = self.get_relative_ee_orientation(rotation=action[4], representation='z')
            self.moveit2.move_to_pose(position=position, quat_xyzw=quat_xyzw)

    def get_observation(self) -> Observation:
        ee_position, ee_orientation = self.get_ee_pose()
        ee_position = np.array(ee_position, dtype=np.float32)
        ee_orientation = np.array(orientation_quat_to_6d(quat_xyzw=ee_orientation), dtype=np.float32)
        object_positions = np.array(tuple(self.get_object_positions().values()), dtype=np.float32)
        nearest_object_position = get_nearest_point(origin=ee_position, points=object_positions)
        obs = np.concatenate([(1.0 if self.gripper.is_open else -1.0,), ee_position, ee_orientation[0], ee_orientation[1], nearest_object_position], dtype=np.float32)
        if self._obs_n_stacked > 1:
            self.__stacked_obs.append(obs)
            while not self._obs_n_stacked == len(self.__stacked_obs):
                self.__stacked_obs.append(obs)
            observation = Observation(np.concatenate(self.__stacked_obs, dtype=np.float32))
        else:
            observation = Observation(obs)
        self.get_logger().debug(f'\nobservation: {observation}')
        return observation

    def get_reward(self) -> Reward:
        return self.curriculum.get_reward()

    def is_done(self) -> bool:
        return self.curriculum.is_done()

    def get_info(self) -> Dict:
        info = self.curriculum.get_info()
        if self.__preload_replay_buffer:
            info.update({'actual_actions': self.__actual_actions})
        return info

    def reset_task(self):
        Manipulation.reset_task(self)
        self.curriculum.reset_task()

    def get_touched_objects(self) -> List[str]:
        """
        Returns list of all objects that are in contact with any finger.
        """
        robot = self.world.get_model(self.robot_name).to_gazebo()
        touched_objects = []
        for gripper_link_name in self.robot_gripper_link_names:
            finger = robot.get_link(link_name=gripper_link_name)
            finger_contacts = finger.contacts()
            for contact in finger_contacts:
                model_name = contact.body_b.split('::', 1)[0]
                if model_name not in touched_objects and any((object_name in model_name for object_name in self.object_names)):
                    touched_objects.append(model_name)
        return touched_objects

    def get_grasped_objects(self, min_angle_between_two_contact: float=np.pi / 8) -> List[str]:
        """
        Returns list of all currently grasped objects.
        Grasped object must be in contact with all gripper links (fingers) and their contact normals must be dissimilar.
        """
        if self.gripper.is_open:
            return []
        robot = self.world.get_model(self.robot_name)
        grasp_candidates = {}
        for gripper_link_name in self.robot_gripper_link_names:
            finger = robot.to_gazebo().get_link(link_name=gripper_link_name)
            finger_contacts = finger.contacts()
            if 0 == len(finger_contacts):
                continue
            for contact in finger_contacts:
                model_name = contact.body_b.split('::', 1)[0]
                if any((object_name in model_name for object_name in self.object_names)):
                    if model_name not in grasp_candidates:
                        grasp_candidates[model_name] = []
                    grasp_candidates[model_name].append(contact.points)
        grasped_objects = []
        for model_name, contact_points_list in grasp_candidates.items():
            if len(contact_points_list) < 2:
                continue
            average_normals = []
            for contact_points in contact_points_list:
                average_normal = np.array([0.0, 0.0, 0.0])
                for point in contact_points:
                    average_normal += point.normal
                average_normal /= np.linalg.norm(average_normal)
                average_normals.append(average_normal)
            normal_angles = []
            for n1, n2 in itertools.combinations(average_normals, 2):
                normal_angles.append(np.arccos(np.clip(np.dot(n1, n2), -1.0, 1.0)))
            sufficient_angle = min_angle_between_two_contact
            for angle in normal_angles:
                if angle > sufficient_angle:
                    grasped_objects.append(model_name)
                    break
        return grasped_objects

    def _demonstrate_action(self) -> np.ndarray:
        self.__actual_actions = np.zeros(self.action_space.shape)
        ee_position, ee_orientation = self.get_ee_pose()
        ee_position = np.array(ee_position)
        ee_orientation = np.array(ee_orientation)
        object_position = np.array(self.get_object_position(self.object_names[0]))
        distance = object_position - ee_position
        distance_mag = np.linalg.norm(distance)
        if distance_mag < 0.02:
            if self.gripper.is_open:
                self.__actual_actions[0] = -1.0
                self.__actual_actions[1:4] = np.zeros((3,))
            else:
                self.__actual_actions[0] = -1.0
                self.__actual_actions[1:4] = np.array((0.0, 0.0, 1.0))
            if self.__full_3d_orientation:
                pass
            else:
                self.__actual_actions[4] = 0.0
        else:
            self.__actual_actions[0] = 1.0
            if distance_mag > self._relative_position_scaling_factor:
                relative_position = distance / distance_mag
            else:
                relative_position = distance / self._relative_position_scaling_factor
            self.__actual_actions[1:4] = relative_position
            distance_mag_xy = np.linalg.norm(distance[:2])
            if distance_mag_xy > 0.01 and ee_position[2] < 0.1:
                self.__actual_actions[3] = max(0.0, self.__actual_actions[3])
            object_orientation = quat_to_xyzw(np.array(self.get_object_orientation(self.object_names[0])))
            if self.__full_3d_orientation:
                pass
            else:
                current_ee_yaw = Rotation.from_quat(ee_orientation).as_euler('xyz')[2]
                current_object_yaw = Rotation.from_quat(object_orientation).as_euler('xyz')[2]
                yaw_diff = current_object_yaw - current_ee_yaw
                if yaw_diff > np.pi:
                    yaw_diff -= np.pi / 2
                elif yaw_diff < -np.pi:
                    yaw_diff += np.pi / 2
                yaw_diff = min(1.0, 1.0 / (self._z_relative_orientation_scaling_factor / yaw_diff))
                self.__actual_actions[4] = yaw_diff
        if ee_position[2] < 0.025:
            self.__actual_actions[3] = max(0.0, self.__actual_actions[3])
        return self.__actual_actions

def is_done(self) -> bool:
    return self.curriculum.is_done()

class GraspCurriculum(StageRewardCurriculum, SuccessRateImpl, WorkspaceScaleCurriculum, ObjectSpawnVolumeScaleCurriculum, ObjectCountCurriculum, ArmStuckChecker):
    """
    Curriculum learning implementation for grasp task that provides termination (success/fail) and reward for each stage of the task.
    """

    def __init__(self, task: Task, stages_base_reward: float, reach_required_distance: float, lift_required_height: float, persistent_reward_each_step: float, persistent_reward_terrain_collision: float, persistent_reward_all_objects_outside_workspace: float, persistent_reward_arm_stuck: float, enable_stage_reward_curriculum: bool, enable_workspace_scale_curriculum: bool, enable_object_spawn_volume_scale_curriculum: bool, enable_object_count_curriculum: bool, reach_required_distance_min: Optional[float]=None, reach_required_distance_max: Optional[float]=None, reach_required_distance_max_threshold: Optional[float]=None, lift_required_height_min: Optional[float]=None, lift_required_height_max: Optional[float]=None, lift_required_height_max_threshold: Optional[float]=None, **kwargs):
        StageRewardCurriculum.__init__(self, curriculum_stage=GraspStage, **kwargs)
        SuccessRateImpl.__init__(self, **kwargs)
        WorkspaceScaleCurriculum.__init__(self, task=task, success_rate_impl=self, **kwargs)
        ObjectSpawnVolumeScaleCurriculum.__init__(self, task=task, success_rate_impl=self, **kwargs)
        ObjectCountCurriculum.__init__(self, task=task, success_rate_impl=self, **kwargs)
        ArmStuckChecker.__init__(self, task=task, **kwargs)
        self.__task = task
        self.__stages_base_reward = stages_base_reward
        self.reach_required_distance = reach_required_distance
        self.lift_required_height = lift_required_height
        self.__persistent_reward_each_step = persistent_reward_each_step
        self.__persistent_reward_terrain_collision = persistent_reward_terrain_collision
        self.__persistent_reward_all_objects_outside_workspace = persistent_reward_all_objects_outside_workspace
        self.__persistent_reward_arm_stuck = persistent_reward_arm_stuck
        self.__enable_stage_reward_curriculum = enable_stage_reward_curriculum
        self.__enable_workspace_scale_curriculum = enable_workspace_scale_curriculum
        self.__enable_object_spawn_volume_scale_curriculum = enable_object_spawn_volume_scale_curriculum
        self.__enable_object_count_curriculum = enable_object_count_curriculum
        if self.__persistent_reward_each_step > 0.0:
            self.__persistent_reward_each_step *= -1.0
        if self.__persistent_reward_terrain_collision > 0.0:
            self.__persistent_reward_terrain_collision *= -1.0
        if self.__persistent_reward_all_objects_outside_workspace > 0.0:
            self.__persistent_reward_all_objects_outside_workspace *= -1.0
        if self.__persistent_reward_arm_stuck > 0.0:
            self.__persistent_reward_arm_stuck *= -1.0
        reach_required_distance_min = reach_required_distance_min if reach_required_distance_min is not None else reach_required_distance
        reach_required_distance_max = reach_required_distance_max if reach_required_distance_max is not None else reach_required_distance
        reach_required_distance_max_threshold = reach_required_distance_max_threshold if reach_required_distance_max_threshold is not None else 0.5
        self.__reach_required_distance_curriculum_enabled = not reach_required_distance_min == reach_required_distance_max
        if self.__reach_required_distance_curriculum_enabled:
            self.__reach_required_distance_curriculum = AttributeCurriculum(success_rate_impl=self, attribute_owner=self, attribute_name='reach_required_distance', initial_value=reach_required_distance_min, target_value=reach_required_distance_max, target_value_threshold=reach_required_distance_max_threshold)
        lift_required_height_min = lift_required_height_min if lift_required_height_min is not None else lift_required_height
        lift_required_height_max = lift_required_height_max if lift_required_height_max is not None else lift_required_height
        lift_required_height_max_threshold = lift_required_height_max_threshold if lift_required_height_max_threshold is not None else 0.5
        lift_required_height += task.robot_model_class.BASE_LINK_Z_OFFSET
        lift_required_height_min += task.robot_model_class.BASE_LINK_Z_OFFSET
        lift_required_height_max += task.robot_model_class.BASE_LINK_Z_OFFSET
        lift_required_height_max_threshold += task.robot_model_class.BASE_LINK_Z_OFFSET
        self.__lift_required_height_curriculum_enabled = not lift_required_height_min == lift_required_height_max
        if self.__lift_required_height_curriculum_enabled:
            self.__lift_required_height_curriculum = AttributeCurriculum(success_rate_impl=self, attribute_owner=self, attribute_name='lift_required_height', initial_value=lift_required_height_min, target_value=lift_required_height_max, target_value_threshold=lift_required_height_max_threshold)

    def get_reward(self) -> Reward:
        if self.__enable_stage_reward_curriculum:
            return StageRewardCurriculum.get_reward(self, ee_position=self.__task.get_ee_position(), object_positions=self.__task.get_object_positions(), touched_objects=self.__task.get_touched_objects(), grasped_objects=self.__task.get_grasped_objects())
        else:
            return StageRewardCurriculum.get_reward(self, only_last_stage=True, object_positions=self.__task.get_object_positions(), grasped_objects=self.__task.get_grasped_objects())

    def is_done(self) -> bool:
        return StageRewardCurriculum.is_done(self)

    def get_info(self) -> Dict:
        info = StageRewardCurriculum.get_info(self)
        info.update(SuccessRateImpl.get_info(self))
        if self.__enable_workspace_scale_curriculum:
            info.update(WorkspaceScaleCurriculum.get_info(self))
        if self.__enable_object_spawn_volume_scale_curriculum:
            info.update(ObjectSpawnVolumeScaleCurriculum.get_info(self))
        if self.__enable_object_count_curriculum:
            info.update(ObjectCountCurriculum.get_info(self))
        if self.__persistent_reward_arm_stuck:
            info.update(ArmStuckChecker.get_info(self))
        if self.__reach_required_distance_curriculum_enabled:
            info.update(self.__reach_required_distance_curriculum.get_info())
        if self.__lift_required_height_curriculum_enabled:
            info.update(self.__lift_required_height_curriculum.get_info())
        return info

    def reset_task(self):
        StageRewardCurriculum.reset_task(self)
        if self.__enable_workspace_scale_curriculum:
            WorkspaceScaleCurriculum.reset_task(self)
        if self.__enable_object_spawn_volume_scale_curriculum:
            ObjectSpawnVolumeScaleCurriculum.reset_task(self)
        if self.__enable_object_count_curriculum:
            ObjectCountCurriculum.reset_task(self)
        if self.__persistent_reward_arm_stuck:
            ArmStuckChecker.reset_task(self)
        if self.__reach_required_distance_curriculum_enabled:
            self.__reach_required_distance_curriculum.reset_task()
        if self.__lift_required_height_curriculum_enabled:
            self.__lift_required_height_curriculum.reset_task()

    def on_episode_success(self):
        self.update_success_rate(is_success=True)

    def on_episode_failure(self):
        self.update_success_rate(is_success=False)

    def on_episode_timeout(self):
        self.update_success_rate(is_success=False)

    def get_reward_REACH(self, ee_position: Tuple[float, float, float], object_positions: Dict[str, Tuple[float, float, float]], **kwargs) -> float:
        if not object_positions:
            return 0.0
        nearest_object_distance = distance_to_nearest_point(origin=ee_position, points=list(object_positions.values()))
        self.__task.get_logger().debug(f'[Curriculum] Distance to nearest object: {nearest_object_distance}')
        if nearest_object_distance < self.reach_required_distance:
            self.__task.get_logger().info(f'[Curriculum] An object is now closer than the required distance of {self.reach_required_distance}')
            self.stages_completed_this_episode[GraspStage.REACH] = True
            return self.__stages_base_reward
        else:
            return 0.0

    def get_reward_TOUCH(self, touched_objects: List[str], **kwargs) -> float:
        if touched_objects:
            self.__task.get_logger().info(f'[Curriculum] Touched objects: {touched_objects}')
            self.stages_completed_this_episode[GraspStage.TOUCH] = True
            return self.__stages_base_reward
        else:
            return 0.0

    def get_reward_GRASP(self, grasped_objects: List[str], **kwargs) -> float:
        if grasped_objects:
            self.__task.get_logger().info(f'[Curriculum] Grasped objects: {grasped_objects}')
            self.stages_completed_this_episode[GraspStage.GRASP] = True
            return self.__stages_base_reward
        else:
            return 0.0

    def get_reward_LIFT(self, object_positions: Dict[str, Tuple[float, float, float]], grasped_objects: List[str], **kwargs) -> float:
        if not (grasped_objects or object_positions):
            return 0.0
        for grasped_object in grasped_objects:
            grasped_object_height = object_positions[grasped_object][2]
            self.__task.get_logger().debug(f"[Curriculum] Height of grasped object '{grasped_objects}': {grasped_object_height}")
            if grasped_object_height > self.lift_required_height:
                self.__task.get_logger().info(f'[Curriculum] Lifted object: {grasped_object}')
                self.stages_completed_this_episode[GraspStage.LIFT] = True
                return self.__stages_base_reward
        return 0.0

    def get_persistent_reward(self, object_positions: Dict[str, Tuple[float, float, float]], **kwargs) -> float:
        reward = self.__persistent_reward_each_step
        if self.__persistent_reward_terrain_collision:
            if self.__task.check_terrain_collision():
                self.__task.get_logger().info('[Curriculum] Robot collided with the terrain')
                reward += self.__persistent_reward_terrain_collision
        if self.__persistent_reward_all_objects_outside_workspace:
            if self.__task.check_all_objects_outside_workspace(object_positions=object_positions):
                self.__task.get_logger().warn('[Curriculum] All objects are outside of the workspace')
                reward += self.__persistent_reward_all_objects_outside_workspace
                self.episode_failed = True
        if self.__persistent_reward_arm_stuck:
            if ArmStuckChecker.is_robot_stuck(self):
                self.__task.get_logger().error(f'[Curriculum] Robot appears to be stuck, resetting...')
                reward += self.__persistent_reward_arm_stuck
                self.episode_failed = True
        return reward

def is_done(self) -> bool:
    return StageRewardCurriculum.is_done(self)

