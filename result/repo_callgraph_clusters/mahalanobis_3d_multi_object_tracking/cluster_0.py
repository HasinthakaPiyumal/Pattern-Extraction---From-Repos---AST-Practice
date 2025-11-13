# Cluster 0

def get_mean(tracks):
    """
  Input:
    tracks: {scene_token:  {t: [TrackingBox]}}
  """
    print('len(tracks.keys()): ', len(tracks.keys()))
    gt_trajectory_map = {tracking_name: {scene_token: {} for scene_token in tracks.keys()} for tracking_name in NUSCENES_TRACKING_NAMES}
    gt_box_data = {tracking_name: [] for tracking_name in NUSCENES_TRACKING_NAMES}
    for scene_token in tracks.keys():
        for t_idx in range(len(tracks[scene_token].keys())):
            t = sorted(tracks[scene_token].keys())[t_idx]
            for box_id in range(len(tracks[scene_token][t])):
                box = tracks[scene_token][t][box_id]
                if box.tracking_name not in NUSCENES_TRACKING_NAMES:
                    continue
                box_data = np.array([box.size[2], box.size[0], box.size[1], box.translation[0], box.translation[1], box.translation[2], rotation_to_positive_z_angle(box.rotation), 0, 0, 0, 0, 0, 0, 0, 0])
                if box.tracking_id not in gt_trajectory_map[box.tracking_name][scene_token]:
                    gt_trajectory_map[box.tracking_name][scene_token][box.tracking_id] = {t_idx: box_data}
                else:
                    gt_trajectory_map[box.tracking_name][scene_token][box.tracking_id][t_idx] = box_data
                if box.tracking_id in gt_trajectory_map[box.tracking_name][scene_token] and t_idx - 1 in gt_trajectory_map[box.tracking_name][scene_token][box.tracking_id]:
                    residual_vel = box_data[3:7] - gt_trajectory_map[box.tracking_name][scene_token][box.tracking_id][t_idx - 1][3:7]
                    box_data[7:11] = residual_vel
                    gt_trajectory_map[box.tracking_name][scene_token][box.tracking_id][t_idx] = box_data
                    if gt_trajectory_map[box.tracking_name][scene_token][box.tracking_id][t_idx - 1][7] == 0:
                        gt_trajectory_map[box.tracking_name][scene_token][box.tracking_id][t_idx - 1][7:11] = residual_vel
                    if box.tracking_id in gt_trajectory_map[box.tracking_name][scene_token] and t_idx - 2 in gt_trajectory_map[box.tracking_name][scene_token][box.tracking_id]:
                        residual_a = residual_vel - (gt_trajectory_map[box.tracking_name][scene_token][box.tracking_id][t_idx - 1][3:7] - gt_trajectory_map[box.tracking_name][scene_token][box.tracking_id][t_idx - 2][3:7])
                        box_data[11:15] = residual_a
                        gt_trajectory_map[box.tracking_name][scene_token][box.tracking_id][t_idx] = box_data
                        if gt_trajectory_map[box.tracking_name][scene_token][box.tracking_id][t_idx - 1][11] == 0:
                            gt_trajectory_map[box.tracking_name][scene_token][box.tracking_id][t_idx - 1][11:15] = residual_a
                        if gt_trajectory_map[box.tracking_name][scene_token][box.tracking_id][t_idx - 2][11] == 0:
                            gt_trajectory_map[box.tracking_name][scene_token][box.tracking_id][t_idx - 2][11:15] = residual_a
                gt_box_data[box.tracking_name].append(box_data)
    gt_box_data = {tracking_name: np.stack(gt_box_data[tracking_name], axis=0) for tracking_name in NUSCENES_TRACKING_NAMES}
    mean = {tracking_name: np.mean(gt_box_data[tracking_name], axis=0) for tracking_name in NUSCENES_TRACKING_NAMES}
    std = {tracking_name: np.std(gt_box_data[tracking_name], axis=0) for tracking_name in NUSCENES_TRACKING_NAMES}
    var = {tracking_name: np.var(gt_box_data[tracking_name], axis=0) for tracking_name in NUSCENES_TRACKING_NAMES}
    return (mean, std, var)

def matching_and_get_diff_stats(pred_boxes, gt_boxes, tracks_gt, matching_dist):
    """
  For each sample token, find matches of pred_boxes and gt_boxes, then get stats.
  tracks_gt has the temporal order info for each sample_token
  """
    diff = {tracking_name: [] for tracking_name in NUSCENES_TRACKING_NAMES}
    diff_vel = {tracking_name: [] for tracking_name in NUSCENES_TRACKING_NAMES}
    reorder = [3, 4, 5, 6, 2, 1, 0]
    reorder_back = [6, 5, 4, 0, 1, 2, 3]
    for scene_token in tracks_gt.keys():
        match_diff_t_map = {tracking_name: {} for tracking_name in NUSCENES_TRACKING_NAMES}
        for t_idx in range(len(tracks_gt[scene_token].keys())):
            t = sorted(tracks_gt[scene_token].keys())[t_idx]
            if len(tracks_gt[scene_token][t]) == 0:
                continue
            box = tracks_gt[scene_token][t][0]
            sample_token = box.sample_token
            for tracking_name in NUSCENES_TRACKING_NAMES:
                gt_all = [box for box in gt_boxes.boxes[sample_token] if box.tracking_name == tracking_name]
                if len(gt_all) == 0:
                    continue
                gts = np.stack([np.array([box.size[2], box.size[0], box.size[1], box.translation[0], box.translation[1], box.translation[2], rotation_to_positive_z_angle(box.rotation)]) for box in gt_all], axis=0)
                gts_ids = [box.tracking_id for box in gt_all]
                det_all = [box for box in pred_boxes.boxes[sample_token] if box.detection_name == tracking_name]
                if len(det_all) == 0:
                    continue
                dets = np.stack([np.array([box.size[2], box.size[0], box.size[1], box.translation[0], box.translation[1], box.translation[2], rotation_to_positive_z_angle(box.rotation)]) for box in det_all], axis=0)
                dets = dets[:, reorder]
                gts = gts[:, reorder]
                if matching_dist == '3d_iou':
                    dets_8corner = [convert_3dbox_to_8corner(det_tmp) for det_tmp in dets]
                    gts_8corner = [convert_3dbox_to_8corner(gt_tmp) for gt_tmp in gts]
                    iou_matrix = np.zeros((len(dets_8corner), len(gts_8corner)), dtype=np.float32)
                    for d, det in enumerate(dets_8corner):
                        for g, gt in enumerate(gts_8corner):
                            iou_matrix[d, g] = iou3d(det, gt)[0]
                    distance_matrix = -iou_matrix
                    threshold = -0.1
                elif matching_dist == '2d_center':
                    distance_matrix = np.zeros((dets.shape[0], gts.shape[0]), dtype=np.float32)
                    for d in range(dets.shape[0]):
                        for g in range(gts.shape[0]):
                            distance_matrix[d][g] = np.sqrt((dets[d][0] - gts[g][0]) ** 2 + (dets[d][1] - gts[g][1]) ** 2)
                    threshold = 2
                else:
                    assert False
                matched_indices = linear_assignment(distance_matrix)
                dets = dets[:, reorder_back]
                gts = gts[:, reorder_back]
                for pair_id in range(matched_indices.shape[0]):
                    if distance_matrix[matched_indices[pair_id][0]][matched_indices[pair_id][1]] < threshold:
                        diff_value = dets[matched_indices[pair_id][0]] - gts[matched_indices[pair_id][1]]
                        diff[tracking_name].append(diff_value)
                        gt_track_id = gts_ids[matched_indices[pair_id][1]]
                        if t_idx not in match_diff_t_map[tracking_name]:
                            match_diff_t_map[tracking_name][t_idx] = {gt_track_id: diff_value}
                        else:
                            match_diff_t_map[tracking_name][t_idx][gt_track_id] = diff_value
                        if t_idx > 0 and t_idx - 1 in match_diff_t_map[tracking_name] and (gt_track_id in match_diff_t_map[tracking_name][t_idx - 1]):
                            diff_vel_value = diff_value - match_diff_t_map[tracking_name][t_idx - 1][gt_track_id]
                            diff_vel[tracking_name].append(diff_vel_value)
    diff = {tracking_name: np.stack(diff[tracking_name], axis=0) for tracking_name in NUSCENES_TRACKING_NAMES}
    mean = {tracking_name: np.mean(diff[tracking_name], axis=0) for tracking_name in NUSCENES_TRACKING_NAMES}
    std = {tracking_name: np.std(diff[tracking_name], axis=0) for tracking_name in NUSCENES_TRACKING_NAMES}
    var = {tracking_name: np.var(diff[tracking_name], axis=0) for tracking_name in NUSCENES_TRACKING_NAMES}
    diff_vel = {tracking_name: np.stack(diff_vel[tracking_name], axis=0) for tracking_name in NUSCENES_TRACKING_NAMES}
    mean_vel = {tracking_name: np.mean(diff_vel[tracking_name], axis=0) for tracking_name in NUSCENES_TRACKING_NAMES}
    std_vel = {tracking_name: np.std(diff_vel[tracking_name], axis=0) for tracking_name in NUSCENES_TRACKING_NAMES}
    var_vel = {tracking_name: np.var(diff_vel[tracking_name], axis=0) for tracking_name in NUSCENES_TRACKING_NAMES}
    return (mean, std, var, mean_vel, std_vel, var_vel)

class KalmanBoxTracker(object):
    """
  This class represents the internel state of individual tracked objects observed as bbox.
  """
    count = 0

    def __init__(self, bbox3D, info, covariance_id=0, track_score=None, tracking_name='car', use_angular_velocity=False):
        """
    Initialises a tracker using initial bounding box.
    """
        if not use_angular_velocity:
            self.kf = KalmanFilter(dim_x=10, dim_z=7)
            self.kf.F = np.array([[1, 0, 0, 0, 0, 0, 0, 1, 0, 0], [0, 1, 0, 0, 0, 0, 0, 0, 1, 0], [0, 0, 1, 0, 0, 0, 0, 0, 0, 1], [0, 0, 0, 1, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 1, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 1, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 1, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 1, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 1, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 1]])
            self.kf.H = np.array([[1, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 1, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 1, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 1, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 1, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 1, 0, 0, 0]])
        else:
            self.kf = KalmanFilter(dim_x=11, dim_z=7)
            self.kf.F = np.array([[1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0], [0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0], [0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0], [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1], [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]])
            self.kf.H = np.array([[1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0]])
        if covariance_id == 0:
            self.kf.P[7:, 7:] *= 1000.0
            self.kf.P *= 10.0
            self.kf.Q[7:, 7:] *= 0.01
        elif covariance_id == 1:
            covariance = Covariance(covariance_id)
            self.kf.P = covariance.P
            self.kf.Q = covariance.Q
            self.kf.R = covariance.R
        elif covariance_id == 2:
            covariance = Covariance(covariance_id)
            self.kf.P = covariance.P[tracking_name]
            self.kf.Q = covariance.Q[tracking_name]
            self.kf.R = covariance.R[tracking_name]
            if not use_angular_velocity:
                self.kf.P = self.kf.P[:-1, :-1]
                self.kf.Q = self.kf.Q[:-1, :-1]
        else:
            assert False
        self.kf.x[:7] = bbox3D.reshape((7, 1))
        self.time_since_update = 0
        self.id = KalmanBoxTracker.count
        KalmanBoxTracker.count += 1
        self.history = []
        self.hits = 1
        self.hit_streak = 1
        self.first_continuing_hit = 1
        self.still_first = True
        self.age = 0
        self.info = info
        self.track_score = track_score
        self.tracking_name = tracking_name
        self.use_angular_velocity = use_angular_velocity

    def update(self, bbox3D, info):
        """ 
    Updates the state vector with observed bbox.
    """
        self.time_since_update = 0
        self.history = []
        self.hits += 1
        self.hit_streak += 1
        if self.still_first:
            self.first_continuing_hit += 1
        if self.kf.x[3] >= np.pi:
            self.kf.x[3] -= np.pi * 2
        if self.kf.x[3] < -np.pi:
            self.kf.x[3] += np.pi * 2
        new_theta = bbox3D[3]
        if new_theta >= np.pi:
            new_theta -= np.pi * 2
        if new_theta < -np.pi:
            new_theta += np.pi * 2
        bbox3D[3] = new_theta
        predicted_theta = self.kf.x[3]
        if abs(new_theta - predicted_theta) > np.pi / 2.0 and abs(new_theta - predicted_theta) < np.pi * 3 / 2.0:
            self.kf.x[3] += np.pi
            if self.kf.x[3] > np.pi:
                self.kf.x[3] -= np.pi * 2
            if self.kf.x[3] < -np.pi:
                self.kf.x[3] += np.pi * 2
        if abs(new_theta - self.kf.x[3]) >= np.pi * 3 / 2.0:
            if new_theta > 0:
                self.kf.x[3] += np.pi * 2
            else:
                self.kf.x[3] -= np.pi * 2
        self.kf.update(bbox3D)
        if self.kf.x[3] >= np.pi:
            self.kf.x[3] -= np.pi * 2
        if self.kf.x[3] < -np.pi:
            self.kf.x[3] += np.pi * 2
        self.info = info

    def predict(self):
        """
    Advances the state vector and returns the predicted bounding box estimate.
    """
        self.kf.predict()
        if self.kf.x[3] >= np.pi:
            self.kf.x[3] -= np.pi * 2
        if self.kf.x[3] < -np.pi:
            self.kf.x[3] += np.pi * 2
        self.age += 1
        if self.time_since_update > 0:
            self.hit_streak = 0
            self.still_first = False
        self.time_since_update += 1
        self.history.append(self.kf.x)
        return self.history[-1]

    def get_state(self):
        """
    Returns the current bounding box estimate.
    """
        return self.kf.x[:7].reshape((7,))

def predict(self):
    """
    Advances the state vector and returns the predicted bounding box estimate.
    """
    self.kf.predict()
    if self.kf.x[3] >= np.pi:
        self.kf.x[3] -= np.pi * 2
    if self.kf.x[3] < -np.pi:
        self.kf.x[3] += np.pi * 2
    self.age += 1
    if self.time_since_update > 0:
        self.hit_streak = 0
        self.still_first = False
    self.time_since_update += 1
    self.history.append(self.kf.x)
    return self.history[-1]

def greedy_match(distance_matrix):
    """
  Find the one-to-one matching using greedy allgorithm choosing small distance
  distance_matrix: (num_detections, num_tracks)
  """
    matched_indices = []
    num_detections, num_tracks = distance_matrix.shape
    distance_1d = distance_matrix.reshape(-1)
    index_1d = np.argsort(distance_1d)
    index_2d = np.stack([index_1d // num_tracks, index_1d % num_tracks], axis=1)
    detection_id_matches_to_tracking_id = [-1] * num_detections
    tracking_id_matches_to_detection_id = [-1] * num_tracks
    for sort_i in range(index_2d.shape[0]):
        detection_id = int(index_2d[sort_i][0])
        tracking_id = int(index_2d[sort_i][1])
        if tracking_id_matches_to_detection_id[tracking_id] == -1 and detection_id_matches_to_tracking_id[detection_id] == -1:
            tracking_id_matches_to_detection_id[tracking_id] = detection_id
            detection_id_matches_to_tracking_id[detection_id] = tracking_id
            matched_indices.append([detection_id, tracking_id])
    matched_indices = np.array(matched_indices)
    return matched_indices

