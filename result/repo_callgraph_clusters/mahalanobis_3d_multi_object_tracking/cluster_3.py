# Cluster 3

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

def get_state(self):
    """
    Returns the current bounding box estimate.
    """
    return self.kf.x[:7].reshape((7,))

def associate_detections_to_trackers(detections, trackers, iou_threshold=0.1, use_mahalanobis=False, dets=None, trks=None, trks_S=None, mahalanobis_threshold=0.1, print_debug=False, match_algorithm='greedy'):
    """
  Assigns detections to tracked object (both represented as bounding boxes)

  detections:  N x 8 x 3
  trackers:    M x 8 x 3

  dets: N x 7
  trks: M x 7
  trks_S: N x 7 x 7

  Returns 3 lists of matches, unmatched_detections and unmatched_trackers
  """
    if len(trackers) == 0:
        return (np.empty((0, 2), dtype=int), np.arange(len(detections)), np.empty((0, 8, 3), dtype=int))
    iou_matrix = np.zeros((len(detections), len(trackers)), dtype=np.float32)
    distance_matrix = np.zeros((len(detections), len(trackers)), dtype=np.float32)
    if use_mahalanobis:
        assert dets is not None
        assert trks is not None
        assert trks_S is not None
    if use_mahalanobis and print_debug:
        print('dets.shape: ', dets.shape)
        print('dets: ', dets)
        print('trks.shape: ', trks.shape)
        print('trks: ', trks)
        print('trks_S.shape: ', trks_S.shape)
        print('trks_S: ', trks_S)
        S_inv = [np.linalg.inv(S_tmp) for S_tmp in trks_S]
        S_inv_diag = [S_inv_tmp.diagonal() for S_inv_tmp in S_inv]
        print('S_inv_diag: ', S_inv_diag)
    for d, det in enumerate(detections):
        for t, trk in enumerate(trackers):
            if use_mahalanobis:
                S_inv = np.linalg.inv(trks_S[t])
                diff = np.expand_dims(dets[d] - trks[t], axis=1)
                corrected_angle_diff = diff_orientation_correction(dets[d][3], trks[t][3])
                diff[3] = corrected_angle_diff
                distance_matrix[d, t] = np.sqrt(np.matmul(np.matmul(diff.T, S_inv), diff)[0][0])
            else:
                iou_matrix[d, t] = iou3d(det, trk)[0]
                distance_matrix = -iou_matrix
    if match_algorithm == 'greedy':
        matched_indices = greedy_match(distance_matrix)
    elif match_algorithm == 'pre_threshold':
        if use_mahalanobis:
            to_max_mask = distance_matrix > mahalanobis_threshold
            distance_matrix[to_max_mask] = mahalanobis_threshold + 1
        else:
            to_max_mask = iou_matrix < iou_threshold
            distance_matrix[to_max_mask] = 0
            iou_matrix[to_max_mask] = 0
        matched_indices = linear_assignment(distance_matrix)
    else:
        matched_indices = linear_assignment(distance_matrix)
    if print_debug:
        print('distance_matrix.shape: ', distance_matrix.shape)
        print('distance_matrix: ', distance_matrix)
        print('matched_indices: ', matched_indices)
    unmatched_detections = []
    for d, det in enumerate(detections):
        if d not in matched_indices[:, 0]:
            unmatched_detections.append(d)
    unmatched_trackers = []
    for t, trk in enumerate(trackers):
        if len(matched_indices) == 0 or t not in matched_indices[:, 1]:
            unmatched_trackers.append(t)
    matches = []
    for m in matched_indices:
        match = True
        if use_mahalanobis:
            if distance_matrix[m[0], m[1]] > mahalanobis_threshold:
                match = False
        elif iou_matrix[m[0], m[1]] < iou_threshold:
            match = False
        if not match:
            unmatched_detections.append(m[0])
            unmatched_trackers.append(m[1])
        else:
            matches.append(m.reshape(1, 2))
    if len(matches) == 0:
        matches = np.empty((0, 2), dtype=int)
    else:
        matches = np.concatenate(matches, axis=0)
    if print_debug:
        print('matches: ', matches)
        print('unmatched_detections: ', unmatched_detections)
        print('unmatched_trackers: ', unmatched_trackers)
    return (matches, np.array(unmatched_detections), np.array(unmatched_trackers))

class AB3DMOT(object):

    def __init__(self, covariance_id=0, max_age=2, min_hits=3, tracking_name='car', use_angular_velocity=False, tracking_nuscenes=False):
        """              
    observation: 
      before reorder: [h, w, l, x, y, z, rot_y]
      after reorder:  [x, y, z, rot_y, l, w, h]
    state:
      [x, y, z, rot_y, l, w, h, x_dot, y_dot, z_dot]
    """
        self.max_age = max_age
        self.min_hits = min_hits
        self.trackers = []
        self.frame_count = 0
        self.reorder = [3, 4, 5, 6, 2, 1, 0]
        self.reorder_back = [6, 5, 4, 0, 1, 2, 3]
        self.covariance_id = covariance_id
        self.tracking_name = tracking_name
        self.use_angular_velocity = use_angular_velocity
        self.tracking_nuscenes = tracking_nuscenes

    def update(self, dets_all, match_distance, match_threshold, match_algorithm, seq_name):
        """
    Params:
      dets_all: dict
        dets - a numpy array of detections in the format [[x,y,z,theta,l,w,h],[x,y,z,theta,l,w,h],...]
        info: a array of other info for each det
    Requires: this method must be called once for each frame even with empty detections.
    Returns the a similar array, where the last column is the object ID.

    NOTE: The number of objects returned may differ from the number of detections provided.
    """
        dets, info = (dets_all['dets'], dets_all['info'])
        dets = dets[:, self.reorder]
        self.frame_count += 1
        print_debug = False
        if False and seq_name == '2f56eb47c64f43df8902d9f88aa8a019' and (self.frame_count >= 25) and (self.frame_count <= 30):
            print_debug = True
            print('self.frame_count: ', self.frame_count)
        if print_debug:
            for trk_tmp in self.trackers:
                print('trk_tmp.id: ', trk_tmp.id)
        trks = np.zeros((len(self.trackers), 7))
        to_del = []
        ret = []
        for t, trk in enumerate(trks):
            pos = self.trackers[t].predict().reshape((-1, 1))
            trk[:] = [pos[0], pos[1], pos[2], pos[3], pos[4], pos[5], pos[6]]
            if np.any(np.isnan(pos)):
                to_del.append(t)
        trks = np.ma.compress_rows(np.ma.masked_invalid(trks))
        for t in reversed(to_del):
            self.trackers.pop(t)
        if print_debug:
            for trk_tmp in self.trackers:
                print('trk_tmp.id: ', trk_tmp.id)
        dets_8corner = [convert_3dbox_to_8corner(det_tmp, match_distance == 'iou' and self.tracking_nuscenes) for det_tmp in dets]
        if len(dets_8corner) > 0:
            dets_8corner = np.stack(dets_8corner, axis=0)
        else:
            dets_8corner = []
        trks_8corner = [convert_3dbox_to_8corner(trk_tmp, match_distance == 'iou' and self.tracking_nuscenes) for trk_tmp in trks]
        trks_S = [np.matmul(np.matmul(tracker.kf.H, tracker.kf.P), tracker.kf.H.T) + tracker.kf.R for tracker in self.trackers]
        if len(trks_8corner) > 0:
            trks_8corner = np.stack(trks_8corner, axis=0)
            trks_S = np.stack(trks_S, axis=0)
        if match_distance == 'iou':
            matched, unmatched_dets, unmatched_trks = associate_detections_to_trackers(dets_8corner, trks_8corner, iou_threshold=match_threshold, print_debug=print_debug, match_algorithm=match_algorithm)
        else:
            matched, unmatched_dets, unmatched_trks = associate_detections_to_trackers(dets_8corner, trks_8corner, use_mahalanobis=True, dets=dets, trks=trks, trks_S=trks_S, mahalanobis_threshold=match_threshold, print_debug=print_debug, match_algorithm=match_algorithm)
        for t, trk in enumerate(self.trackers):
            if t not in unmatched_trks:
                d = matched[np.where(matched[:, 1] == t)[0], 0]
                trk.update(dets[d, :][0], info[d, :][0])
                detection_score = info[d, :][0][-1]
                trk.track_score = detection_score
        for i in unmatched_dets:
            detection_score = info[i][-1]
            track_score = detection_score
            trk = KalmanBoxTracker(dets[i, :], info[i, :], self.covariance_id, track_score, self.tracking_name, use_angular_velocity)
            self.trackers.append(trk)
        i = len(self.trackers)
        for trk in reversed(self.trackers):
            d = trk.get_state()
            d = d[self.reorder_back]
            if trk.time_since_update < self.max_age and (trk.hits >= self.min_hits or self.frame_count <= self.min_hits):
                ret.append(np.concatenate((d, [trk.id + 1], trk.info[:-1], [trk.track_score])).reshape(1, -1))
            i -= 1
            if trk.time_since_update >= self.max_age:
                self.trackers.pop(i)
        if len(ret) > 0:
            return np.concatenate(ret)
        return np.empty((0, 15 + 7))

def update(self, dets_all, match_distance, match_threshold, match_algorithm, seq_name):
    """
    Params:
      dets_all: dict
        dets - a numpy array of detections in the format [[x,y,z,theta,l,w,h],[x,y,z,theta,l,w,h],...]
        info: a array of other info for each det
    Requires: this method must be called once for each frame even with empty detections.
    Returns the a similar array, where the last column is the object ID.

    NOTE: The number of objects returned may differ from the number of detections provided.
    """
    dets, info = (dets_all['dets'], dets_all['info'])
    dets = dets[:, self.reorder]
    self.frame_count += 1
    print_debug = False
    if False and seq_name == '2f56eb47c64f43df8902d9f88aa8a019' and (self.frame_count >= 25) and (self.frame_count <= 30):
        print_debug = True
        print('self.frame_count: ', self.frame_count)
    if print_debug:
        for trk_tmp in self.trackers:
            print('trk_tmp.id: ', trk_tmp.id)
    trks = np.zeros((len(self.trackers), 7))
    to_del = []
    ret = []
    for t, trk in enumerate(trks):
        pos = self.trackers[t].predict().reshape((-1, 1))
        trk[:] = [pos[0], pos[1], pos[2], pos[3], pos[4], pos[5], pos[6]]
        if np.any(np.isnan(pos)):
            to_del.append(t)
    trks = np.ma.compress_rows(np.ma.masked_invalid(trks))
    for t in reversed(to_del):
        self.trackers.pop(t)
    if print_debug:
        for trk_tmp in self.trackers:
            print('trk_tmp.id: ', trk_tmp.id)
    dets_8corner = [convert_3dbox_to_8corner(det_tmp, match_distance == 'iou' and self.tracking_nuscenes) for det_tmp in dets]
    if len(dets_8corner) > 0:
        dets_8corner = np.stack(dets_8corner, axis=0)
    else:
        dets_8corner = []
    trks_8corner = [convert_3dbox_to_8corner(trk_tmp, match_distance == 'iou' and self.tracking_nuscenes) for trk_tmp in trks]
    trks_S = [np.matmul(np.matmul(tracker.kf.H, tracker.kf.P), tracker.kf.H.T) + tracker.kf.R for tracker in self.trackers]
    if len(trks_8corner) > 0:
        trks_8corner = np.stack(trks_8corner, axis=0)
        trks_S = np.stack(trks_S, axis=0)
    if match_distance == 'iou':
        matched, unmatched_dets, unmatched_trks = associate_detections_to_trackers(dets_8corner, trks_8corner, iou_threshold=match_threshold, print_debug=print_debug, match_algorithm=match_algorithm)
    else:
        matched, unmatched_dets, unmatched_trks = associate_detections_to_trackers(dets_8corner, trks_8corner, use_mahalanobis=True, dets=dets, trks=trks, trks_S=trks_S, mahalanobis_threshold=match_threshold, print_debug=print_debug, match_algorithm=match_algorithm)
    for t, trk in enumerate(self.trackers):
        if t not in unmatched_trks:
            d = matched[np.where(matched[:, 1] == t)[0], 0]
            trk.update(dets[d, :][0], info[d, :][0])
            detection_score = info[d, :][0][-1]
            trk.track_score = detection_score
    for i in unmatched_dets:
        detection_score = info[i][-1]
        track_score = detection_score
        trk = KalmanBoxTracker(dets[i, :], info[i, :], self.covariance_id, track_score, self.tracking_name, use_angular_velocity)
        self.trackers.append(trk)
    i = len(self.trackers)
    for trk in reversed(self.trackers):
        d = trk.get_state()
        d = d[self.reorder_back]
        if trk.time_since_update < self.max_age and (trk.hits >= self.min_hits or self.frame_count <= self.min_hits):
            ret.append(np.concatenate((d, [trk.id + 1], trk.info[:-1], [trk.track_score])).reshape(1, -1))
        i -= 1
        if trk.time_since_update >= self.max_age:
            self.trackers.pop(i)
    if len(ret) > 0:
        return np.concatenate(ret)
    return np.empty((0, 15 + 7))

