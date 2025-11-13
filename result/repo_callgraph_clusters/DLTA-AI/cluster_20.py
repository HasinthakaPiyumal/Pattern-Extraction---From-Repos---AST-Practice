# Cluster 20

class StrongSORT(object):

    def __init__(self, model_weights, device, fp16, max_dist=0.2, max_iou_dist=0.7, max_age=70, max_unmatched_preds=7, n_init=3, nn_budget=100, mc_lambda=0.995, ema_alpha=0.9):
        self.model = ReIDDetectMultiBackend(weights=model_weights, device=device, fp16=fp16)
        self.max_dist = max_dist
        metric = NearestNeighborDistanceMetric('cosine', self.max_dist, nn_budget)
        self.tracker = Tracker(metric, max_iou_dist=max_iou_dist, max_age=max_age, n_init=n_init, max_unmatched_preds=max_unmatched_preds, mc_lambda=mc_lambda, ema_alpha=ema_alpha)

    def update(self, dets, ori_img):
        xyxys = dets[:, 0:4]
        confs = dets[:, 4]
        clss = dets[:, 5]
        classes = clss.numpy()
        xywhs = xyxy2xywh(xyxys.numpy())
        confs = confs.numpy()
        self.height, self.width = ori_img.shape[:2]
        features = self._get_features(xywhs, ori_img)
        bbox_tlwh = self._xywh_to_tlwh(xywhs)
        detections = [Detection(bbox_tlwh[i], conf, features[i]) for i, conf in enumerate(confs)]
        boxes = np.array([d.tlwh for d in detections])
        scores = np.array([d.confidence for d in detections])
        self.tracker.predict()
        self.tracker.update(detections, clss, confs)
        outputs = []
        for track in self.tracker.tracks:
            if not track.is_confirmed() or track.time_since_update > 1:
                continue
            box = track.to_tlwh()
            x1, y1, x2, y2 = self._tlwh_to_xyxy(box)
            track_id = track.track_id
            class_id = track.class_id
            conf = track.conf
            queue = track.q
            outputs.append(np.array([x1, y1, x2, y2, track_id, class_id, conf, queue], dtype=object))
        if len(outputs) > 0:
            outputs = np.stack(outputs, axis=0)
        return outputs
    '\n    TODO:\n        Convert bbox from xc_yc_w_h to xtl_ytl_w_h\n    Thanks JieChen91@github.com for reporting this bug!\n    '

    @staticmethod
    def _xywh_to_tlwh(bbox_xywh):
        if isinstance(bbox_xywh, np.ndarray):
            bbox_tlwh = bbox_xywh.copy()
        elif isinstance(bbox_xywh, torch.Tensor):
            bbox_tlwh = bbox_xywh.clone()
        bbox_tlwh[:, 0] = bbox_xywh[:, 0] - bbox_xywh[:, 2] / 2.0
        bbox_tlwh[:, 1] = bbox_xywh[:, 1] - bbox_xywh[:, 3] / 2.0
        return bbox_tlwh

    def _xywh_to_xyxy(self, bbox_xywh):
        x, y, w, h = bbox_xywh
        x1 = max(int(x - w / 2), 0)
        x2 = min(int(x + w / 2), self.width - 1)
        y1 = max(int(y - h / 2), 0)
        y2 = min(int(y + h / 2), self.height - 1)
        return (x1, y1, x2, y2)

    def _tlwh_to_xyxy(self, bbox_tlwh):
        """
        TODO:
            Convert bbox from xtl_ytl_w_h to xc_yc_w_h
        Thanks JieChen91@github.com for reporting this bug!
        """
        x, y, w, h = bbox_tlwh
        x1 = max(int(x), 0)
        x2 = min(int(x + w), self.width - 1)
        y1 = max(int(y), 0)
        y2 = min(int(y + h), self.height - 1)
        return (x1, y1, x2, y2)

    def increment_ages(self):
        self.tracker.increment_ages()

    def _xyxy_to_tlwh(self, bbox_xyxy):
        x1, y1, x2, y2 = bbox_xyxy
        t = x1
        l = y1
        w = int(x2 - x1)
        h = int(y2 - y1)
        return (t, l, w, h)

    def _get_features(self, bbox_xywh, ori_img):
        im_crops = []
        for box in bbox_xywh:
            x1, y1, x2, y2 = self._xywh_to_xyxy(box)
            im = ori_img[y1:y2, x1:x2]
            im_crops.append(im)
        if im_crops:
            features = self.model(im_crops)
        else:
            features = np.array([])
        return features

    def trajectory(self, im0, q, color):
        for i, p in enumerate(q):
            thickness = int(np.sqrt(float(i + 1)) * 1.5)
            if p[0] == 'observationupdate':
                cv2.circle(im0, p[1], 2, color=color, thickness=thickness)
            else:
                cv2.circle(im0, p[1], 2, color=(255, 255, 255), thickness=thickness)

def __init__(self, model_weights, device, fp16, max_dist=0.2, max_iou_dist=0.7, max_age=70, max_unmatched_preds=7, n_init=3, nn_budget=100, mc_lambda=0.995, ema_alpha=0.9):
    self.model = ReIDDetectMultiBackend(weights=model_weights, device=device, fp16=fp16)
    self.max_dist = max_dist
    metric = NearestNeighborDistanceMetric('cosine', self.max_dist, nn_budget)
    self.tracker = Tracker(metric, max_iou_dist=max_iou_dist, max_age=max_age, n_init=n_init, max_unmatched_preds=max_unmatched_preds, mc_lambda=mc_lambda, ema_alpha=ema_alpha)

class Tracker:
    """
    This is the multi-target tracker.
    Parameters
    ----------
    metric : nn_matching.NearestNeighborDistanceMetric
        A distance metric for measurement-to-track association.
    max_age : int
        Maximum number of missed misses before a track is deleted.
    n_init : int
        Number of consecutive detections before the track is confirmed. The
        track state is set to `Deleted` if a miss occurs within the first
        `n_init` frames.
    Attributes
    ----------
    metric : nn_matching.NearestNeighborDistanceMetric
        The distance metric used for measurement to track association.
    max_age : int
        Maximum number of missed misses before a track is deleted.
    n_init : int
        Number of frames that a track remains in initialization phase.
    kf : kalman_filter.KalmanFilter
        A Kalman filter to filter target trajectories in image space.
    tracks : List[Track]
        The list of active tracks at the current time step.
    """
    GATING_THRESHOLD = np.sqrt(kalman_filter.chi2inv95[4])

    def __init__(self, metric, max_iou_dist=0.9, max_age=30, max_unmatched_preds=7, n_init=3, _lambda=0, ema_alpha=0.9, mc_lambda=0.995):
        self.metric = metric
        self.max_iou_dist = max_iou_dist
        self.max_age = max_age
        self.n_init = n_init
        self._lambda = _lambda
        self.ema_alpha = ema_alpha
        self.mc_lambda = mc_lambda
        self.max_unmatched_preds = max_unmatched_preds
        self.kf = kalman_filter.KalmanFilter()
        self.tracks = []
        self._next_id = 1

    def predict(self):
        """Propagate track state distributions one time step forward.

        This function should be called once every time step, before `update`.
        """
        for track in self.tracks:
            track.predict(self.kf)

    def increment_ages(self):
        for track in self.tracks:
            track.increment_age()
            track.mark_missed()

    def camera_update(self, previous_img, current_img):
        for track in self.tracks:
            track.camera_update(previous_img, current_img)

    def pred_n_update_all_tracks(self):
        """Perform predictions and updates for all tracks by its own predicted state.

        """
        self.predict()
        for t in self.tracks:
            if self.max_unmatched_preds != 0 and t.updates_wo_assignment < t.max_num_updates_wo_assignment:
                bbox = t.to_tlwh()
                t.update_kf(detection.to_xyah_ext(bbox))

    def update(self, detections, classes, confidences):
        """Perform measurement update and track management.

        Parameters
        ----------
        detections : List[deep_sort.detection.Detection]
            A list of detections at the current time step.

        """
        matches, unmatched_tracks, unmatched_detections = self._match(detections)
        for track_idx, detection_idx in matches:
            self.tracks[track_idx].update(detections[detection_idx], classes[detection_idx], confidences[detection_idx])
        for track_idx in unmatched_tracks:
            self.tracks[track_idx].mark_missed()
            if self.max_unmatched_preds != 0 and self.tracks[track_idx].updates_wo_assignment < self.tracks[track_idx].max_num_updates_wo_assignment:
                bbox = self.tracks[track_idx].to_tlwh()
                self.tracks[track_idx].update_kf(detection.to_xyah_ext(bbox))
        for detection_idx in unmatched_detections:
            self._initiate_track(detections[detection_idx], classes[detection_idx].item(), confidences[detection_idx].item())
        self.tracks = [t for t in self.tracks if not t.is_deleted()]
        active_targets = [t.track_id for t in self.tracks if t.is_confirmed()]
        features, targets = ([], [])
        for track in self.tracks:
            if not track.is_confirmed():
                continue
            features += track.features
            targets += [track.track_id for _ in track.features]
        self.metric.partial_fit(np.asarray(features), np.asarray(targets), active_targets)

    def _full_cost_metric(self, tracks, dets, track_indices, detection_indices):
        """
        This implements the full lambda-based cost-metric. However, in doing so, it disregards
        the possibility to gate the position only which is provided by
        linear_assignment.gate_cost_matrix(). Instead, I gate by everything.
        Note that the Mahalanobis distance is itself an unnormalised metric. Given the cosine
        distance being normalised, we employ a quick and dirty normalisation based on the
        threshold: that is, we divide the positional-cost by the gating threshold, thus ensuring
        that the valid values range 0-1.
        Note also that the authors work with the squared distance. I also sqrt this, so that it
        is more intuitive in terms of values.
        """
        pos_cost = np.empty([len(track_indices), len(detection_indices)])
        msrs = np.asarray([dets[i].to_xyah() for i in detection_indices])
        for row, track_idx in enumerate(track_indices):
            pos_cost[row, :] = np.sqrt(self.kf.gating_distance(tracks[track_idx].mean, tracks[track_idx].covariance, msrs, False)) / self.GATING_THRESHOLD
        pos_gate = pos_cost > 1.0
        app_cost = self.metric.distance(np.array([dets[i].feature for i in detection_indices]), np.array([tracks[i].track_id for i in track_indices]))
        app_gate = app_cost > self.metric.matching_threshold
        cost_matrix = self._lambda * pos_cost + (1 - self._lambda) * app_cost
        cost_matrix[np.logical_or(pos_gate, app_gate)] = linear_assignment.INFTY_COST
        return cost_matrix

    def _match(self, detections):

        def gated_metric(tracks, dets, track_indices, detection_indices):
            features = np.array([dets[i].feature for i in detection_indices])
            targets = np.array([tracks[i].track_id for i in track_indices])
            cost_matrix = self.metric.distance(features, targets)
            cost_matrix = linear_assignment.gate_cost_matrix(cost_matrix, tracks, dets, track_indices, detection_indices, self.mc_lambda)
            return cost_matrix
        confirmed_tracks = [i for i, t in enumerate(self.tracks) if t.is_confirmed()]
        unconfirmed_tracks = [i for i, t in enumerate(self.tracks) if not t.is_confirmed()]
        matches_a, unmatched_tracks_a, unmatched_detections = linear_assignment.matching_cascade(gated_metric, self.metric.matching_threshold, self.max_age, self.tracks, detections, confirmed_tracks)
        iou_track_candidates = unconfirmed_tracks + [k for k in unmatched_tracks_a if self.tracks[k].time_since_update == 1]
        unmatched_tracks_a = [k for k in unmatched_tracks_a if self.tracks[k].time_since_update != 1]
        matches_b, unmatched_tracks_b, unmatched_detections = linear_assignment.min_cost_matching(iou_matching.iou_cost, self.max_iou_dist, self.tracks, detections, iou_track_candidates, unmatched_detections)
        matches = matches_a + matches_b
        unmatched_tracks = list(set(unmatched_tracks_a + unmatched_tracks_b))
        return (matches, unmatched_tracks, unmatched_detections)

    def _initiate_track(self, detection, class_id, conf):
        self.tracks.append(Track(detection.to_xyah(), self._next_id, class_id, conf, self.n_init, self.max_age, self.ema_alpha, detection.feature))
        self._next_id += 1

def __init__(self, metric, max_iou_dist=0.9, max_age=30, max_unmatched_preds=7, n_init=3, _lambda=0, ema_alpha=0.9, mc_lambda=0.995):
    self.metric = metric
    self.max_iou_dist = max_iou_dist
    self.max_age = max_age
    self.n_init = n_init
    self._lambda = _lambda
    self.ema_alpha = ema_alpha
    self.mc_lambda = mc_lambda
    self.max_unmatched_preds = max_unmatched_preds
    self.kf = kalman_filter.KalmanFilter()
    self.tracks = []
    self._next_id = 1

class Track:
    """
    A single target track with state space `(x, y, a, h)` and associated
    velocities, where `(x, y)` is the center of the bounding box, `a` is the
    aspect ratio and `h` is the height.

    Parameters
    ----------
    mean : ndarray
        Mean vector of the initial state distribution.
    covariance : ndarray
        Covariance matrix of the initial state distribution.
    track_id : int
        A unique track identifier.
    n_init : int
        Number of consecutive detections before the track is confirmed. The
        track state is set to `Deleted` if a miss occurs within the first
        `n_init` frames.
    max_age : int
        The maximum number of consecutive misses before the track state is
        set to `Deleted`.
    feature : Optional[ndarray]
        Feature vector of the detection this track originates from. If not None,
        this feature is added to the `features` cache.

    Attributes
    ----------
    mean : ndarray
        Mean vector of the initial state distribution.
    covariance : ndarray
        Covariance matrix of the initial state distribution.
    track_id : int
        A unique track identifier.
    hits : int
        Total number of measurement updates.
    age : int
        Total number of frames since first occurance.
    time_since_update : int
        Total number of frames since last measurement update.
    state : TrackState
        The current track state.
    features : List[ndarray]
        A cache of features. On each measurement update, the associated feature
        vector is added to this list.

    """

    def __init__(self, detection, track_id, class_id, conf, n_init, max_age, ema_alpha, feature=None):
        self.track_id = track_id
        self.class_id = int(class_id)
        self.hits = 1
        self.age = 1
        self.time_since_update = 0
        self.max_num_updates_wo_assignment = 7
        self.updates_wo_assignment = 0
        self.ema_alpha = ema_alpha
        self.state = TrackState.Tentative
        self.features = []
        if feature is not None:
            feature /= np.linalg.norm(feature)
            self.features.append(feature)
        self.conf = conf
        self._n_init = n_init
        self._max_age = max_age
        self.kf = KalmanFilter()
        self.mean, self.covariance = self.kf.initiate(detection)
        self.q = deque(maxlen=25)

    def to_tlwh(self):
        """Get current position in bounding box format `(top left x, top left y,
        width, height)`.

        Returns
        -------
        ndarray
            The bounding box.

        """
        ret = self.mean[:4].copy()
        ret[2] *= ret[3]
        ret[:2] -= ret[2:] / 2
        return ret

    def to_tlbr(self):
        """Get kf estimated current position in bounding box format `(min x, miny, max x,
        max y)`.

        Returns
        -------
        ndarray
            The predicted kf bounding box.

        """
        ret = self.to_tlwh()
        ret[2:] = ret[:2] + ret[2:]
        return ret

    def ECC(self, src, dst, warp_mode=cv2.MOTION_EUCLIDEAN, eps=1e-05, max_iter=100, scale=0.1, align=False):
        """Compute the warp matrix from src to dst.
        Parameters
        ----------
        src : ndarray 
            An NxM matrix of source img(BGR or Gray), it must be the same format as dst.
        dst : ndarray
            An NxM matrix of target img(BGR or Gray).
        warp_mode: flags of opencv
            translation: cv2.MOTION_TRANSLATION
            rotated and shifted: cv2.MOTION_EUCLIDEAN
            affine(shift,rotated,shear): cv2.MOTION_AFFINE
            homography(3d): cv2.MOTION_HOMOGRAPHY
        eps: float
            the threshold of the increment in the correlation coefficient between two iterations
        max_iter: int
            the number of iterations.
        scale: float or [int, int]
            scale_ratio: float
            scale_size: [W, H]
        align: bool
            whether to warp affine or perspective transforms to the source image
        Returns
        -------
        warp matrix : ndarray
            Returns the warp matrix from src to dst.
            if motion models is homography, the warp matrix will be 3x3, otherwise 2x3
        src_aligned: ndarray
            aligned source image of gray
        """
        if src.ndim == 3:
            src = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
            dst = cv2.cvtColor(dst, cv2.COLOR_BGR2GRAY)
        if scale is not None:
            if isinstance(scale, float) or isinstance(scale, int):
                if scale != 1:
                    src_r = cv2.resize(src, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
                    dst_r = cv2.resize(dst, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
                    scale = [scale, scale]
                else:
                    src_r, dst_r = (src, dst)
                    scale = None
            elif scale[0] != src.shape[1] and scale[1] != src.shape[0]:
                src_r = cv2.resize(src, (scale[0], scale[1]), interpolation=cv2.INTER_LINEAR)
                dst_r = cv2.resize(dst, (scale[0], scale[1]), interpolation=cv2.INTER_LINEAR)
                scale = [scale[0] / src.shape[1], scale[1] / src.shape[0]]
            else:
                src_r, dst_r = (src, dst)
                scale = None
        else:
            src_r, dst_r = (src, dst)
        if warp_mode == cv2.MOTION_HOMOGRAPHY:
            warp_matrix = np.eye(3, 3, dtype=np.float32)
        else:
            warp_matrix = np.eye(2, 3, dtype=np.float32)
        criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, max_iter, eps)
        try:
            cc, warp_matrix = cv2.findTransformECC(src_r, dst_r, warp_matrix, warp_mode, criteria, None, 1)
        except cv2.error as e:
            print('ecc transform failed')
            return (None, None)
        if scale is not None:
            warp_matrix[0, 2] = warp_matrix[0, 2] / scale[0]
            warp_matrix[1, 2] = warp_matrix[1, 2] / scale[1]
        if align:
            sz = src.shape
            if warp_mode == cv2.MOTION_HOMOGRAPHY:
                src_aligned = cv2.warpPerspective(src, warp_matrix, (sz[1], sz[0]), flags=cv2.INTER_LINEAR)
            else:
                src_aligned = cv2.warpAffine(src, warp_matrix, (sz[1], sz[0]), flags=cv2.INTER_LINEAR)
            return (warp_matrix, src_aligned)
        else:
            return (warp_matrix, None)

    def get_matrix(self, matrix):
        eye = np.eye(3)
        dist = np.linalg.norm(eye - matrix)
        if dist < 100:
            return matrix
        else:
            return eye

    def camera_update(self, previous_frame, next_frame):
        warp_matrix, src_aligned = self.ECC(previous_frame, next_frame)
        if warp_matrix is None and src_aligned is None:
            return
        [a, b] = warp_matrix
        warp_matrix = np.array([a, b, [0, 0, 1]])
        warp_matrix = warp_matrix.tolist()
        matrix = self.get_matrix(warp_matrix)
        x1, y1, x2, y2 = self.to_tlbr()
        x1_, y1_, _ = matrix @ np.array([x1, y1, 1]).T
        x2_, y2_, _ = matrix @ np.array([x2, y2, 1]).T
        w, h = (x2_ - x1_, y2_ - y1_)
        cx, cy = (x1_ + w / 2, y1_ + h / 2)
        self.mean[:4] = [cx, cy, w / h, h]

    def increment_age(self):
        self.age += 1
        self.time_since_update += 1

    def predict(self, kf):
        """Propagate the state distribution to the current time step using a
        Kalman filter prediction step.

        Parameters
        ----------
        kf : kalman_filter.KalmanFilter
            The Kalman filter.

        """
        self.mean, self.covariance = self.kf.predict(self.mean, self.covariance)
        self.age += 1
        self.time_since_update += 1

    def update_kf(self, bbox, confidence=0.5):
        self.updates_wo_assignment = self.updates_wo_assignment + 1
        self.mean, self.covariance = self.kf.update(self.mean, self.covariance, bbox, confidence)
        tlbr = self.to_tlbr()
        x_c = int((tlbr[0] + tlbr[2]) / 2)
        y_c = int((tlbr[1] + tlbr[3]) / 2)
        self.q.append(('predupdate', (x_c, y_c)))

    def update(self, detection, class_id, conf):
        """Perform Kalman filter measurement update step and update the feature
        cache.
        Parameters
        ----------
        detection : Detection
            The associated detection.
        """
        self.conf = conf
        self.class_id = class_id.int()
        self.mean, self.covariance = self.kf.update(self.mean, self.covariance, detection.to_xyah(), detection.confidence)
        feature = detection.feature / np.linalg.norm(detection.feature)
        smooth_feat = self.ema_alpha * self.features[-1] + (1 - self.ema_alpha) * feature
        smooth_feat /= np.linalg.norm(smooth_feat)
        self.features = [smooth_feat]
        self.hits += 1
        self.time_since_update = 0
        if self.state == TrackState.Tentative and self.hits >= self._n_init:
            self.state = TrackState.Confirmed
        tlbr = self.to_tlbr()
        x_c = int((tlbr[0] + tlbr[2]) / 2)
        y_c = int((tlbr[1] + tlbr[3]) / 2)
        self.q.append(('observationupdate', (x_c, y_c)))

    def mark_missed(self):
        """Mark this track as missed (no association at the current time step).
        """
        if self.state == TrackState.Tentative:
            self.state = TrackState.Deleted
        elif self.time_since_update > self._max_age:
            self.state = TrackState.Deleted

    def is_tentative(self):
        """Returns True if this track is tentative (unconfirmed).
        """
        return self.state == TrackState.Tentative

    def is_confirmed(self):
        """Returns True if this track is confirmed."""
        return self.state == TrackState.Confirmed

    def is_deleted(self):
        """Returns True if this track is dead and should be deleted."""
        return self.state == TrackState.Deleted

def __init__(self, detection, track_id, class_id, conf, n_init, max_age, ema_alpha, feature=None):
    self.track_id = track_id
    self.class_id = int(class_id)
    self.hits = 1
    self.age = 1
    self.time_since_update = 0
    self.max_num_updates_wo_assignment = 7
    self.updates_wo_assignment = 0
    self.ema_alpha = ema_alpha
    self.state = TrackState.Tentative
    self.features = []
    if feature is not None:
        feature /= np.linalg.norm(feature)
        self.features.append(feature)
    self.conf = conf
    self._n_init = n_init
    self._max_age = max_age
    self.kf = KalmanFilter()
    self.mean, self.covariance = self.kf.initiate(detection)
    self.q = deque(maxlen=25)

class KalmanBoxTracker(object):
    """
    This class represents the internal state of individual tracked objects observed as bbox.
    """
    count = 0

    def __init__(self, bbox, cls, delta_t=3, orig=False, emb=None, alpha=0, new_kf=False):
        """
        Initialises a tracker using initial bounding box.

        """
        if not orig:
            from .kalmanfilter import KalmanFilterNew as KalmanFilter
        else:
            from filterpy.kalman import KalmanFilter
        self.cls = cls
        self.conf = bbox[-1]
        self.new_kf = new_kf
        if new_kf:
            self.kf = KalmanFilter(dim_x=8, dim_z=4)
            self.kf.F = np.array([[1, 0, 0, 0, 1, 0, 0, 0], [0, 1, 0, 0, 0, 1, 0, 0], [0, 0, 1, 0, 0, 0, 1, 0], [0, 0, 0, 1, 0, 0, 0, 1], [0, 0, 0, 0, 1, 0, 0, 0], [0, 0, 0, 0, 0, 1, 0, 0], [0, 0, 0, 0, 0, 0, 1, 0], [0, 0, 0, 0, 0, 0, 0, 1]])
            self.kf.H = np.array([[1, 0, 0, 0, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0, 0, 0], [0, 0, 1, 0, 0, 0, 0, 0], [0, 0, 0, 1, 0, 0, 0, 0]])
            _, _, w, h = convert_bbox_to_z_new(bbox).reshape(-1)
            self.kf.P = new_kf_process_noise(w, h)
            self.kf.P[:4, :4] *= 4
            self.kf.P[4:, 4:] *= 100
            self.bbox_to_z_func = convert_bbox_to_z_new
            self.x_to_bbox_func = convert_x_to_bbox_new
        else:
            self.kf = KalmanFilter(dim_x=7, dim_z=4)
            self.kf.F = np.array([[1, 0, 0, 0, 1, 0, 0], [0, 1, 0, 0, 0, 1, 0], [0, 0, 1, 0, 0, 0, 1], [0, 0, 0, 1, 0, 0, 0], [0, 0, 0, 0, 1, 0, 0], [0, 0, 0, 0, 0, 1, 0], [0, 0, 0, 0, 0, 0, 1]])
            self.kf.H = np.array([[1, 0, 0, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0, 0], [0, 0, 1, 0, 0, 0, 0], [0, 0, 0, 1, 0, 0, 0]])
            self.kf.R[2:, 2:] *= 10.0
            self.kf.P[4:, 4:] *= 1000.0
            self.kf.P *= 10.0
            self.kf.Q[-1, -1] *= 0.01
            self.kf.Q[4:, 4:] *= 0.01
            self.bbox_to_z_func = convert_bbox_to_z
            self.x_to_bbox_func = convert_x_to_bbox
        self.kf.x[:4] = self.bbox_to_z_func(bbox)
        self.time_since_update = 0
        self.id = KalmanBoxTracker.count
        KalmanBoxTracker.count += 1
        self.history = []
        self.hits = 0
        self.hit_streak = 0
        self.age = 0
        "\n        NOTE: [-1,-1,-1,-1,-1] is a compromising placeholder for non-observation status, the same for the return of \n        function k_previous_obs. It is ugly and I do not like it. But to support generate observation array in a \n        fast and unified way, which you would see below k_observations = np.array([k_previous_obs(...]]), let's bear it for now.\n        "
        self.last_observation = np.array([-1, -1, -1, -1, -1])
        self.history_observations = []
        self.observations = dict()
        self.velocity = None
        self.delta_t = delta_t
        self.emb = emb
        self.frozen = False

    def update(self, bbox, cls):
        """
        Updates the state vector with observed bbox.
        """
        if bbox is not None:
            self.frozen = False
            self.cls = cls
            if self.last_observation.sum() >= 0:
                previous_box = None
                for dt in range(self.delta_t, 0, -1):
                    if self.age - dt in self.observations:
                        previous_box = self.observations[self.age - dt]
                        break
                if previous_box is None:
                    previous_box = self.last_observation
                '\n                  Estimate the track speed direction with observations \\Delta t steps away\n                '
                self.velocity = speed_direction(previous_box, bbox)
            '\n              Insert new observations. This is a ugly way to maintain both self.observations\n              and self.history_observations. Bear it for the moment.\n            '
            self.last_observation = bbox
            self.observations[self.age] = bbox
            self.history_observations.append(bbox)
            self.time_since_update = 0
            self.history = []
            self.hits += 1
            self.hit_streak += 1
            if self.new_kf:
                R = new_kf_measurement_noise(self.kf.x[2, 0], self.kf.x[3, 0])
                self.kf.update(self.bbox_to_z_func(bbox), R=R)
            else:
                self.kf.update(self.bbox_to_z_func(bbox))
        else:
            self.kf.update(bbox)
            self.frozen = True

    def update_emb(self, emb, alpha=0.9):
        self.emb = alpha * self.emb + (1 - alpha) * emb
        self.emb /= np.linalg.norm(self.emb)

    def get_emb(self):
        return self.emb.cpu()

    def apply_affine_correction(self, affine):
        m = affine[:, :2]
        t = affine[:, 2].reshape(2, 1)
        if self.last_observation.sum() > 0:
            ps = self.last_observation[:4].reshape(2, 2).T
            ps = m @ ps + t
            self.last_observation[:4] = ps.T.reshape(-1)
        for dt in range(self.delta_t, -1, -1):
            if self.age - dt in self.observations:
                ps = self.observations[self.age - dt][:4].reshape(2, 2).T
                ps = m @ ps + t
                self.observations[self.age - dt][:4] = ps.T.reshape(-1)
        self.kf.apply_affine_correction(m, t, self.new_kf)

    def predict(self):
        """
        Advances the state vector and returns the predicted bounding box estimate.
        """
        if self.new_kf:
            if self.kf.x[2] + self.kf.x[6] <= 0:
                self.kf.x[6] = 0
            if self.kf.x[3] + self.kf.x[7] <= 0:
                self.kf.x[7] = 0
            if self.frozen:
                self.kf.x[6] = self.kf.x[7] = 0
            Q = new_kf_process_noise(self.kf.x[2, 0], self.kf.x[3, 0])
        else:
            if self.kf.x[6] + self.kf.x[2] <= 0:
                self.kf.x[6] *= 0.0
            Q = None
        self.kf.predict(Q=Q)
        self.age += 1
        if self.time_since_update > 0:
            self.hit_streak = 0
        self.time_since_update += 1
        self.history.append(self.x_to_bbox_func(self.kf.x))
        return self.history[-1]

    def get_state(self):
        """
        Returns the current bounding box estimate.
        """
        return self.x_to_bbox_func(self.kf.x)

    def mahalanobis(self, bbox):
        """Should be run after a predict() call for accuracy."""
        return self.kf.md_for_measurement(self.bbox_to_z_func(bbox))

def __init__(self, bbox, cls, delta_t=3, orig=False, emb=None, alpha=0, new_kf=False):
    """
        Initialises a tracker using initial bounding box.

        """
    if not orig:
        from .kalmanfilter import KalmanFilterNew as KalmanFilter
    else:
        from filterpy.kalman import KalmanFilter
    self.cls = cls
    self.conf = bbox[-1]
    self.new_kf = new_kf
    if new_kf:
        self.kf = KalmanFilter(dim_x=8, dim_z=4)
        self.kf.F = np.array([[1, 0, 0, 0, 1, 0, 0, 0], [0, 1, 0, 0, 0, 1, 0, 0], [0, 0, 1, 0, 0, 0, 1, 0], [0, 0, 0, 1, 0, 0, 0, 1], [0, 0, 0, 0, 1, 0, 0, 0], [0, 0, 0, 0, 0, 1, 0, 0], [0, 0, 0, 0, 0, 0, 1, 0], [0, 0, 0, 0, 0, 0, 0, 1]])
        self.kf.H = np.array([[1, 0, 0, 0, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0, 0, 0], [0, 0, 1, 0, 0, 0, 0, 0], [0, 0, 0, 1, 0, 0, 0, 0]])
        _, _, w, h = convert_bbox_to_z_new(bbox).reshape(-1)
        self.kf.P = new_kf_process_noise(w, h)
        self.kf.P[:4, :4] *= 4
        self.kf.P[4:, 4:] *= 100
        self.bbox_to_z_func = convert_bbox_to_z_new
        self.x_to_bbox_func = convert_x_to_bbox_new
    else:
        self.kf = KalmanFilter(dim_x=7, dim_z=4)
        self.kf.F = np.array([[1, 0, 0, 0, 1, 0, 0], [0, 1, 0, 0, 0, 1, 0], [0, 0, 1, 0, 0, 0, 1], [0, 0, 0, 1, 0, 0, 0], [0, 0, 0, 0, 1, 0, 0], [0, 0, 0, 0, 0, 1, 0], [0, 0, 0, 0, 0, 0, 1]])
        self.kf.H = np.array([[1, 0, 0, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0, 0], [0, 0, 1, 0, 0, 0, 0], [0, 0, 0, 1, 0, 0, 0]])
        self.kf.R[2:, 2:] *= 10.0
        self.kf.P[4:, 4:] *= 1000.0
        self.kf.P *= 10.0
        self.kf.Q[-1, -1] *= 0.01
        self.kf.Q[4:, 4:] *= 0.01
        self.bbox_to_z_func = convert_bbox_to_z
        self.x_to_bbox_func = convert_x_to_bbox
    self.kf.x[:4] = self.bbox_to_z_func(bbox)
    self.time_since_update = 0
    self.id = KalmanBoxTracker.count
    KalmanBoxTracker.count += 1
    self.history = []
    self.hits = 0
    self.hit_streak = 0
    self.age = 0
    "\n        NOTE: [-1,-1,-1,-1,-1] is a compromising placeholder for non-observation status, the same for the return of \n        function k_previous_obs. It is ugly and I do not like it. But to support generate observation array in a \n        fast and unified way, which you would see below k_observations = np.array([k_previous_obs(...]]), let's bear it for now.\n        "
    self.last_observation = np.array([-1, -1, -1, -1, -1])
    self.history_observations = []
    self.observations = dict()
    self.velocity = None
    self.delta_t = delta_t
    self.emb = emb
    self.frozen = False

def predict(self):
    """
        Advances the state vector and returns the predicted bounding box estimate.
        """
    if self.new_kf:
        if self.kf.x[2] + self.kf.x[6] <= 0:
            self.kf.x[6] = 0
        if self.kf.x[3] + self.kf.x[7] <= 0:
            self.kf.x[7] = 0
        if self.frozen:
            self.kf.x[6] = self.kf.x[7] = 0
        Q = new_kf_process_noise(self.kf.x[2, 0], self.kf.x[3, 0])
    else:
        if self.kf.x[6] + self.kf.x[2] <= 0:
            self.kf.x[6] *= 0.0
        Q = None
    self.kf.predict(Q=Q)
    self.age += 1
    if self.time_since_update > 0:
        self.hit_streak = 0
    self.time_since_update += 1
    self.history.append(self.x_to_bbox_func(self.kf.x))
    return self.history[-1]

def get_state(self):
    """
        Returns the current bounding box estimate.
        """
    return self.x_to_bbox_func(self.kf.x)

def mahalanobis(self, bbox):
    """Should be run after a predict() call for accuracy."""
    return self.kf.md_for_measurement(self.bbox_to_z_func(bbox))

class OCSort(object):

    def __init__(self, model_weights, device, fp16, det_thresh, max_age=30, min_hits=3, iou_threshold=0.3, delta_t=3, asso_func='iou', inertia=0.2, w_association_emb=0.75, alpha_fixed_emb=0.95, aw_param=0.5, embedding_off=False, cmc_off=False, aw_off=False, new_kf_off=False, **kwargs):
        """
        Sets key parameters for SORT
        """
        self.max_age = max_age
        self.min_hits = min_hits
        self.iou_threshold = iou_threshold
        self.trackers = []
        self.frame_count = 0
        self.det_thresh = det_thresh
        self.delta_t = delta_t
        self.asso_func = ASSO_FUNCS[asso_func]
        self.inertia = inertia
        self.w_association_emb = w_association_emb
        self.alpha_fixed_emb = alpha_fixed_emb
        self.aw_param = aw_param
        KalmanBoxTracker.count = 0
        self.embedder = ReIDDetectMultiBackend(weights=model_weights, device=device, fp16=fp16)
        self.cmc = CMCComputer()
        self.embedding_off = embedding_off
        self.cmc_off = cmc_off
        self.aw_off = aw_off
        self.new_kf_off = new_kf_off

    def update(self, dets, img_numpy, tag='blub'):
        """
        Params:
          dets - a numpy array of detections in the format [[x1,y1,x2,y2,score],[x1,y1,x2,y2,score],...]
        Requires: this method must be called once for each frame even with empty detections (use np.empty((0, 5)) for frames without detections).
        Returns the a similar array, where the last column is the object ID.
        NOTE: The number of objects returned may differ from the number of detections provided.
        """
        xyxys = dets[:, 0:4]
        scores = dets[:, 4]
        clss = dets[:, 5]
        classes = clss.numpy()
        xyxys = xyxys.numpy()
        scores = scores.numpy()
        dets = dets[:, 0:6].numpy()
        remain_inds = scores > self.det_thresh
        dets = dets[remain_inds]
        self.height, self.width = img_numpy.shape[:2]
        if self.embedding_off or dets.shape[0] == 0:
            dets_embs = np.ones((dets.shape[0], 1))
        else:
            dets_embs = self._get_features(dets[:, :4], img_numpy)
        if not self.cmc_off:
            transform = self.cmc.compute_affine(img_numpy, dets[:, :4], tag)
            for trk in self.trackers:
                trk.apply_affine_correction(transform)
        trust = (dets[:, 4] - self.det_thresh) / (1 - self.det_thresh)
        af = self.alpha_fixed_emb
        dets_alpha = af + (1 - af) * (1 - trust)
        trks = np.zeros((len(self.trackers), 5))
        trk_embs = []
        to_del = []
        ret = []
        for t, trk in enumerate(trks):
            pos = self.trackers[t].predict()[0]
            trk[:] = [pos[0], pos[1], pos[2], pos[3], 0]
            if np.any(np.isnan(pos)):
                to_del.append(t)
            else:
                trk_embs.append(self.trackers[t].get_emb())
        trks = np.ma.compress_rows(np.ma.masked_invalid(trks))
        if len(trk_embs) > 0:
            trk_embs = np.vstack(trk_embs)
        else:
            trk_embs = np.array(trk_embs)
        for t in reversed(to_del):
            self.trackers.pop(t)
        velocities = np.array([trk.velocity if trk.velocity is not None else np.array((0, 0)) for trk in self.trackers])
        last_boxes = np.array([trk.last_observation for trk in self.trackers])
        k_observations = np.array([k_previous_obs(trk.observations, trk.age, self.delta_t) for trk in self.trackers])
        '\n            First round of association\n        '
        if self.embedding_off or dets.shape[0] == 0 or trk_embs.shape[0] == 0:
            stage1_emb_cost = None
        else:
            stage1_emb_cost = dets_embs @ trk_embs.T
        matched, unmatched_dets, unmatched_trks = associate(dets, trks, self.iou_threshold, velocities, k_observations, self.inertia, stage1_emb_cost, self.w_association_emb, self.aw_off, self.aw_param)
        for m in matched:
            self.trackers[m[1]].update(dets[m[0], :5], dets[m[0], 5])
            self.trackers[m[1]].update_emb(dets_embs[m[0]], alpha=dets_alpha[m[0]])
        '\n            Second round of associaton by OCR\n        '
        if unmatched_dets.shape[0] > 0 and unmatched_trks.shape[0] > 0:
            left_dets = dets[unmatched_dets]
            left_dets_embs = dets_embs[unmatched_dets]
            left_trks = last_boxes[unmatched_trks]
            left_trks_embs = trk_embs[unmatched_trks]
            iou_left = self.asso_func(left_dets, left_trks)
            emb_cost_left = left_dets_embs @ left_trks_embs.T
            if self.embedding_off:
                emb_cost_left = np.zeros_like(emb_cost_left)
            iou_left = np.array(iou_left)
            if iou_left.max() > self.iou_threshold:
                '\n                NOTE: by using a lower threshold, e.g., self.iou_threshold - 0.1, you may\n                get a higher performance especially on MOT17/MOT20 datasets. But we keep it\n                uniform here for simplicity\n                '
                rematched_indices = linear_assignment(-iou_left)
                to_remove_det_indices = []
                to_remove_trk_indices = []
                for m in rematched_indices:
                    det_ind, trk_ind = (unmatched_dets[m[0]], unmatched_trks[m[1]])
                    if iou_left[m[0], m[1]] < self.iou_threshold:
                        continue
                    self.trackers[trk_ind].update(dets[det_ind, :5], dets[det_ind, 5])
                    self.trackers[trk_ind].update_emb(dets_embs[det_ind], alpha=dets_alpha[det_ind])
                    to_remove_det_indices.append(det_ind)
                    to_remove_trk_indices.append(trk_ind)
                unmatched_dets = np.setdiff1d(unmatched_dets, np.array(to_remove_det_indices))
                unmatched_trks = np.setdiff1d(unmatched_trks, np.array(to_remove_trk_indices))
        for m in unmatched_trks:
            self.trackers[m].update(None, None)
        for i in unmatched_dets:
            trk = KalmanBoxTracker(dets[i, :5], dets[i, 5], delta_t=self.delta_t, emb=dets_embs[i], alpha=dets_alpha[i], new_kf=not self.new_kf_off)
            self.trackers.append(trk)
        i = len(self.trackers)
        for trk in reversed(self.trackers):
            if trk.last_observation.sum() < 0:
                d = trk.get_state()[0]
            else:
                "\n                this is optional to use the recent observation or the kalman filter prediction,\n                we didn't notice significant difference here\n                "
                d = trk.last_observation[:4]
            if trk.time_since_update < 1 and (trk.hit_streak >= self.min_hits or self.frame_count <= self.min_hits):
                ret.append(np.concatenate((d, [trk.id + 1], [trk.cls], [trk.conf])).reshape(1, -1))
            i -= 1
            if trk.time_since_update > self.max_age:
                self.trackers.pop(i)
        if len(ret) > 0:
            return np.concatenate(ret)
        return np.empty((0, 5))

    def _xywh_to_xyxy(self, bbox_xywh):
        x, y, w, h = bbox_xywh
        x1 = max(int(x - w / 2), 0)
        x2 = min(int(x + w / 2), self.width - 1)
        y1 = max(int(y - h / 2), 0)
        y2 = min(int(y + h / 2), self.height - 1)
        return (x1, y1, x2, y2)

    def _get_features(self, bbox_xyxy, ori_img):
        im_crops = []
        for box in bbox_xyxy:
            x1, y1, x2, y2 = box.astype(int)
            im = ori_img[y1:y2, x1:x2]
            im_crops.append(im)
        if im_crops:
            features = self.embedder(im_crops).cpu()
        else:
            features = np.array([])
        return features

    def update_public(self, dets, cates, scores):
        self.frame_count += 1
        det_scores = np.ones((dets.shape[0], 1))
        dets = np.concatenate((dets, det_scores), axis=1)
        remain_inds = scores > self.det_thresh
        cates = cates[remain_inds]
        dets = dets[remain_inds]
        trks = np.zeros((len(self.trackers), 5))
        to_del = []
        ret = []
        for t, trk in enumerate(trks):
            pos = self.trackers[t].predict()[0]
            cat = self.trackers[t].cate
            trk[:] = [pos[0], pos[1], pos[2], pos[3], cat]
            if np.any(np.isnan(pos)):
                to_del.append(t)
        trks = np.ma.compress_rows(np.ma.masked_invalid(trks))
        for t in reversed(to_del):
            self.trackers.pop(t)
        velocities = np.array([trk.velocity if trk.velocity is not None else np.array((0, 0)) for trk in self.trackers])
        last_boxes = np.array([trk.last_observation for trk in self.trackers])
        k_observations = np.array([k_previous_obs(trk.observations, trk.age, self.delta_t) for trk in self.trackers])
        matched, unmatched_dets, unmatched_trks = associate_kitti(dets, trks, cates, self.iou_threshold, velocities, k_observations, self.inertia)
        for m in matched:
            self.trackers[m[1]].update(dets[m[0], :])
        if unmatched_dets.shape[0] > 0 and unmatched_trks.shape[0] > 0:
            '\n            The re-association stage by OCR.\n            NOTE: at this stage, adding other strategy might be able to continue improve\n            the performance, such as BYTE association by ByteTrack.\n            '
            left_dets = dets[unmatched_dets]
            left_trks = last_boxes[unmatched_trks]
            left_dets_c = left_dets.copy()
            left_trks_c = left_trks.copy()
            iou_left = self.asso_func(left_dets_c, left_trks_c)
            iou_left = np.array(iou_left)
            det_cates_left = cates[unmatched_dets]
            trk_cates_left = trks[unmatched_trks][:, 4]
            num_dets = unmatched_dets.shape[0]
            num_trks = unmatched_trks.shape[0]
            cate_matrix = np.zeros((num_dets, num_trks))
            for i in range(num_dets):
                for j in range(num_trks):
                    if det_cates_left[i] != trk_cates_left[j]:
                        '\n                        For some datasets, such as KITTI, there are different categories,\n                        we have to avoid associate them together.\n                        '
                        cate_matrix[i][j] = -1000000.0
            iou_left = iou_left + cate_matrix
            if iou_left.max() > self.iou_threshold - 0.1:
                rematched_indices = linear_assignment(-iou_left)
                to_remove_det_indices = []
                to_remove_trk_indices = []
                for m in rematched_indices:
                    det_ind, trk_ind = (unmatched_dets[m[0]], unmatched_trks[m[1]])
                    if iou_left[m[0], m[1]] < self.iou_threshold - 0.1:
                        continue
                    self.trackers[trk_ind].update(dets[det_ind, :])
                    to_remove_det_indices.append(det_ind)
                    to_remove_trk_indices.append(trk_ind)
                unmatched_dets = np.setdiff1d(unmatched_dets, np.array(to_remove_det_indices))
                unmatched_trks = np.setdiff1d(unmatched_trks, np.array(to_remove_trk_indices))
        for i in unmatched_dets:
            trk = KalmanBoxTracker(dets[i, :])
            trk.cate = cates[i]
            self.trackers.append(trk)
        i = len(self.trackers)
        for trk in reversed(self.trackers):
            if trk.last_observation.sum() > 0:
                d = trk.last_observation[:4]
            else:
                d = trk.get_state()[0]
            if trk.time_since_update < 1:
                if self.frame_count <= self.min_hits or trk.hit_streak >= self.min_hits:
                    ret.append(np.concatenate((d, [trk.id + 1], [trk.cls], [trk.conf])).reshape(1, -1))
                if trk.hit_streak == self.min_hits:
                    for prev_i in range(self.min_hits - 1):
                        prev_observation = trk.history_observations[-(prev_i + 2)]
                        ret.append(np.concatenate((prev_observation[:4], [trk.id + 1], [trk.cls], [trk.conf])).reshape(1, -1))
            i -= 1
            if trk.time_since_update > self.max_age:
                self.trackers.pop(i)
        if len(ret) > 0:
            return np.concatenate(ret)
        return np.empty((0, 7))

    def dump_cache(self):
        self.cmc.dump_cache()
        self.embedder.dump_cache()

def __init__(self, model_weights, device, fp16, det_thresh, max_age=30, min_hits=3, iou_threshold=0.3, delta_t=3, asso_func='iou', inertia=0.2, w_association_emb=0.75, alpha_fixed_emb=0.95, aw_param=0.5, embedding_off=False, cmc_off=False, aw_off=False, new_kf_off=False, **kwargs):
    """
        Sets key parameters for SORT
        """
    self.max_age = max_age
    self.min_hits = min_hits
    self.iou_threshold = iou_threshold
    self.trackers = []
    self.frame_count = 0
    self.det_thresh = det_thresh
    self.delta_t = delta_t
    self.asso_func = ASSO_FUNCS[asso_func]
    self.inertia = inertia
    self.w_association_emb = w_association_emb
    self.alpha_fixed_emb = alpha_fixed_emb
    self.aw_param = aw_param
    KalmanBoxTracker.count = 0
    self.embedder = ReIDDetectMultiBackend(weights=model_weights, device=device, fp16=fp16)
    self.cmc = CMCComputer()
    self.embedding_off = embedding_off
    self.cmc_off = cmc_off
    self.aw_off = aw_off
    self.new_kf_off = new_kf_off

class KalmanBoxTracker(object):
    """
    This class represents the internal state of individual tracked objects observed as bbox.
    """
    count = 0

    def __init__(self, bbox, cls, delta_t=3, orig=False):
        """
        Initialises a tracker using initial bounding box.

        """
        if not orig:
            from .kalmanfilter import KalmanFilterNew as KalmanFilter
            self.kf = KalmanFilter(dim_x=7, dim_z=4)
        else:
            from filterpy.kalman import KalmanFilter
            self.kf = KalmanFilter(dim_x=7, dim_z=4)
        self.kf.F = np.array([[1, 0, 0, 0, 1, 0, 0], [0, 1, 0, 0, 0, 1, 0], [0, 0, 1, 0, 0, 0, 1], [0, 0, 0, 1, 0, 0, 0], [0, 0, 0, 0, 1, 0, 0], [0, 0, 0, 0, 0, 1, 0], [0, 0, 0, 0, 0, 0, 1]])
        self.kf.H = np.array([[1, 0, 0, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0, 0], [0, 0, 1, 0, 0, 0, 0], [0, 0, 0, 1, 0, 0, 0]])
        self.kf.R[2:, 2:] *= 10.0
        self.kf.P[4:, 4:] *= 1000.0
        self.kf.P *= 10.0
        self.kf.Q[-1, -1] *= 0.01
        self.kf.Q[4:, 4:] *= 0.01
        self.kf.x[:4] = convert_bbox_to_z(bbox)
        self.time_since_update = 0
        self.id = KalmanBoxTracker.count
        KalmanBoxTracker.count += 1
        self.history = []
        self.hits = 0
        self.hit_streak = 0
        self.age = 0
        self.conf = bbox[-1]
        self.cls = cls
        "\n        NOTE: [-1,-1,-1,-1,-1] is a compromising placeholder for non-observation status, the same for the return of \n        function k_previous_obs. It is ugly and I do not like it. But to support generate observation array in a \n        fast and unified way, which you would see below k_observations = np.array([k_previous_obs(...]]), let's bear it for now.\n        "
        self.last_observation = np.array([-1, -1, -1, -1, -1])
        self.observations = dict()
        self.history_observations = []
        self.velocity = None
        self.delta_t = delta_t

    def update(self, bbox, cls):
        """
        Updates the state vector with observed bbox.
        """
        if bbox is not None:
            self.conf = bbox[-1]
            self.cls = cls
            if self.last_observation.sum() >= 0:
                previous_box = None
                for i in range(self.delta_t):
                    dt = self.delta_t - i
                    if self.age - dt in self.observations:
                        previous_box = self.observations[self.age - dt]
                        break
                if previous_box is None:
                    previous_box = self.last_observation
                '\n                  Estimate the track speed direction with observations \\Delta t steps away\n                '
                self.velocity = speed_direction(previous_box, bbox)
            '\n              Insert new observations. This is a ugly way to maintain both self.observations\n              and self.history_observations. Bear it for the moment.\n            '
            self.last_observation = bbox
            self.observations[self.age] = bbox
            self.history_observations.append(bbox)
            self.time_since_update = 0
            self.history = []
            self.hits += 1
            self.hit_streak += 1
            self.kf.update(convert_bbox_to_z(bbox))
        else:
            self.kf.update(bbox)

    def predict(self):
        """
        Advances the state vector and returns the predicted bounding box estimate.
        """
        if self.kf.x[6] + self.kf.x[2] <= 0:
            self.kf.x[6] *= 0.0
        self.kf.predict()
        self.age += 1
        if self.time_since_update > 0:
            self.hit_streak = 0
        self.time_since_update += 1
        self.history.append(convert_x_to_bbox(self.kf.x))
        return self.history[-1]

    def get_state(self):
        """
        Returns the current bounding box estimate.
        """
        return convert_x_to_bbox(self.kf.x)

def __init__(self, bbox, cls, delta_t=3, orig=False):
    """
        Initialises a tracker using initial bounding box.

        """
    if not orig:
        from .kalmanfilter import KalmanFilterNew as KalmanFilter
        self.kf = KalmanFilter(dim_x=7, dim_z=4)
    else:
        from filterpy.kalman import KalmanFilter
        self.kf = KalmanFilter(dim_x=7, dim_z=4)
    self.kf.F = np.array([[1, 0, 0, 0, 1, 0, 0], [0, 1, 0, 0, 0, 1, 0], [0, 0, 1, 0, 0, 0, 1], [0, 0, 0, 1, 0, 0, 0], [0, 0, 0, 0, 1, 0, 0], [0, 0, 0, 0, 0, 1, 0], [0, 0, 0, 0, 0, 0, 1]])
    self.kf.H = np.array([[1, 0, 0, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0, 0], [0, 0, 1, 0, 0, 0, 0], [0, 0, 0, 1, 0, 0, 0]])
    self.kf.R[2:, 2:] *= 10.0
    self.kf.P[4:, 4:] *= 1000.0
    self.kf.P *= 10.0
    self.kf.Q[-1, -1] *= 0.01
    self.kf.Q[4:, 4:] *= 0.01
    self.kf.x[:4] = convert_bbox_to_z(bbox)
    self.time_since_update = 0
    self.id = KalmanBoxTracker.count
    KalmanBoxTracker.count += 1
    self.history = []
    self.hits = 0
    self.hit_streak = 0
    self.age = 0
    self.conf = bbox[-1]
    self.cls = cls
    "\n        NOTE: [-1,-1,-1,-1,-1] is a compromising placeholder for non-observation status, the same for the return of \n        function k_previous_obs. It is ugly and I do not like it. But to support generate observation array in a \n        fast and unified way, which you would see below k_observations = np.array([k_previous_obs(...]]), let's bear it for now.\n        "
    self.last_observation = np.array([-1, -1, -1, -1, -1])
    self.observations = dict()
    self.history_observations = []
    self.velocity = None
    self.delta_t = delta_t

class STrack(BaseTrack):
    shared_kalman = KalmanFilter()

    def __init__(self, tlwh, score, cls):
        self._tlwh = np.asarray(tlwh, dtype=np.float32)
        self.kalman_filter = None
        self.mean, self.covariance = (None, None)
        self.is_activated = False
        self.score = score
        self.tracklet_len = 0
        self.cls = cls

    def predict(self):
        mean_state = self.mean.copy()
        if self.state != TrackState.Tracked:
            mean_state[7] = 0
        self.mean, self.covariance = self.kalman_filter.predict(mean_state, self.covariance)

    @staticmethod
    def multi_predict(stracks):
        if len(stracks) > 0:
            multi_mean = np.asarray([st.mean.copy() for st in stracks])
            multi_covariance = np.asarray([st.covariance for st in stracks])
            for i, st in enumerate(stracks):
                if st.state != TrackState.Tracked:
                    multi_mean[i][7] = 0
            multi_mean, multi_covariance = STrack.shared_kalman.multi_predict(multi_mean, multi_covariance)
            for i, (mean, cov) in enumerate(zip(multi_mean, multi_covariance)):
                stracks[i].mean = mean
                stracks[i].covariance = cov

    def activate(self, kalman_filter, frame_id):
        """Start a new tracklet"""
        self.kalman_filter = kalman_filter
        self.track_id = self.next_id()
        self.mean, self.covariance = self.kalman_filter.initiate(self.tlwh_to_xyah(self._tlwh))
        self.tracklet_len = 0
        self.state = TrackState.Tracked
        if frame_id == 1:
            self.is_activated = True
        self.frame_id = frame_id
        self.start_frame = frame_id

    def re_activate(self, new_track, frame_id, new_id=False):
        self.mean, self.covariance = self.kalman_filter.update(self.mean, self.covariance, self.tlwh_to_xyah(new_track.tlwh))
        self.tracklet_len = 0
        self.state = TrackState.Tracked
        self.is_activated = True
        self.frame_id = frame_id
        if new_id:
            self.track_id = self.next_id()
        self.score = new_track.score
        self.cls = new_track.cls

    def update(self, new_track, frame_id):
        """
        Update a matched track
        :type new_track: STrack
        :type frame_id: int
        :type update_feature: bool
        :return:
        """
        self.frame_id = frame_id
        self.tracklet_len += 1
        new_tlwh = new_track.tlwh
        self.mean, self.covariance = self.kalman_filter.update(self.mean, self.covariance, self.tlwh_to_xyah(new_tlwh))
        self.state = TrackState.Tracked
        self.is_activated = True
        self.score = new_track.score

    @property
    def tlwh(self):
        """Get current position in bounding box format `(top left x, top left y,
                width, height)`.
        """
        if self.mean is None:
            return self._tlwh.copy()
        ret = self.mean[:4].copy()
        ret[2] *= ret[3]
        ret[:2] -= ret[2:] / 2
        return ret

    @property
    def tlbr(self):
        """Convert bounding box to format `(min x, min y, max x, max y)`, i.e.,
        `(top left, bottom right)`.
        """
        ret = self.tlwh.copy()
        ret[2:] += ret[:2]
        return ret

    @staticmethod
    def tlwh_to_xyah(tlwh):
        """Convert bounding box to format `(center x, center y, aspect ratio,
        height)`, where the aspect ratio is `width / height`.
        """
        ret = np.asarray(tlwh).copy()
        ret[:2] += ret[2:] / 2
        ret[2] /= ret[3]
        return ret

    def to_xyah(self):
        return self.tlwh_to_xyah(self.tlwh)

    @staticmethod
    def tlbr_to_tlwh(tlbr):
        ret = np.asarray(tlbr).copy()
        ret[2:] -= ret[:2]
        return ret

    @staticmethod
    def tlwh_to_tlbr(tlwh):
        ret = np.asarray(tlwh).copy()
        ret[2:] += ret[:2]
        return ret

    def __repr__(self):
        return 'OT_{}_({}-{})'.format(self.track_id, self.start_frame, self.end_frame)

def activate(self, kalman_filter, frame_id):
    """Start a new tracklet"""
    self.kalman_filter = kalman_filter
    self.track_id = self.next_id()
    self.mean, self.covariance = self.kalman_filter.initiate(self.tlwh_to_xyah(self._tlwh))
    self.tracklet_len = 0
    self.state = TrackState.Tracked
    if frame_id == 1:
        self.is_activated = True
    self.frame_id = frame_id
    self.start_frame = frame_id

def re_activate(self, new_track, frame_id, new_id=False):
    self.mean, self.covariance = self.kalman_filter.update(self.mean, self.covariance, self.tlwh_to_xyah(new_track.tlwh))
    self.tracklet_len = 0
    self.state = TrackState.Tracked
    self.is_activated = True
    self.frame_id = frame_id
    if new_id:
        self.track_id = self.next_id()
    self.score = new_track.score
    self.cls = new_track.cls

def update(self, new_track, frame_id):
    """
        Update a matched track
        :type new_track: STrack
        :type frame_id: int
        :type update_feature: bool
        :return:
        """
    self.frame_id = frame_id
    self.tracklet_len += 1
    new_tlwh = new_track.tlwh
    self.mean, self.covariance = self.kalman_filter.update(self.mean, self.covariance, self.tlwh_to_xyah(new_tlwh))
    self.state = TrackState.Tracked
    self.is_activated = True
    self.score = new_track.score

def to_xyah(self):
    return self.tlwh_to_xyah(self.tlwh)

class BYTETracker(object):

    def __init__(self, track_thresh=0.45, match_thresh=0.8, track_buffer=25, frame_rate=30):
        self.tracked_stracks = []
        self.lost_stracks = []
        self.removed_stracks = []
        self.frame_id = 0
        self.track_buffer = track_buffer
        self.track_thresh = track_thresh
        self.match_thresh = match_thresh
        self.det_thresh = track_thresh + 0.1
        self.buffer_size = int(frame_rate / 30.0 * track_buffer)
        self.max_time_lost = self.buffer_size
        self.kalman_filter = KalmanFilter()

    def update(self, dets, _):
        self.frame_id += 1
        activated_starcks = []
        refind_stracks = []
        lost_stracks = []
        removed_stracks = []
        xyxys = dets[:, 0:4]
        xywh = xyxy2xywh(xyxys.numpy())
        confs = dets[:, 4]
        clss = dets[:, 5]
        classes = clss.numpy()
        xyxys = xyxys.numpy()
        confs = confs.numpy()
        remain_inds = confs > self.track_thresh
        inds_low = confs > 0.1
        inds_high = confs < self.track_thresh
        inds_second = np.logical_and(inds_low, inds_high)
        dets_second = xywh[inds_second]
        dets = xywh[remain_inds]
        scores_keep = confs[remain_inds]
        scores_second = confs[inds_second]
        clss_keep = classes[remain_inds]
        clss_second = classes[inds_second]
        if len(dets) > 0:
            'Detections'
            detections = [STrack(xyxy, s, c) for xyxy, s, c in zip(dets, scores_keep, clss_keep)]
        else:
            detections = []
        ' Add newly detected tracklets to tracked_stracks'
        unconfirmed = []
        tracked_stracks = []
        for track in self.tracked_stracks:
            if not track.is_activated:
                unconfirmed.append(track)
            else:
                tracked_stracks.append(track)
        ' Step 2: First association, with high score detection boxes'
        strack_pool = joint_stracks(tracked_stracks, self.lost_stracks)
        STrack.multi_predict(strack_pool)
        dists = matching.iou_distance(strack_pool, detections)
        dists = matching.fuse_score(dists, detections)
        matches, u_track, u_detection = matching.linear_assignment(dists, thresh=self.match_thresh)
        for itracked, idet in matches:
            track = strack_pool[itracked]
            det = detections[idet]
            if track.state == TrackState.Tracked:
                track.update(detections[idet], self.frame_id)
                activated_starcks.append(track)
            else:
                track.re_activate(det, self.frame_id, new_id=False)
                refind_stracks.append(track)
        ' Step 3: Second association, with low score detection boxes'
        if len(dets_second) > 0:
            'Detections'
            detections_second = [STrack(xywh, s, c) for xywh, s, c in zip(dets_second, scores_second, clss_second)]
        else:
            detections_second = []
        r_tracked_stracks = [strack_pool[i] for i in u_track if strack_pool[i].state == TrackState.Tracked]
        dists = matching.iou_distance(r_tracked_stracks, detections_second)
        matches, u_track, u_detection_second = matching.linear_assignment(dists, thresh=0.5)
        for itracked, idet in matches:
            track = r_tracked_stracks[itracked]
            det = detections_second[idet]
            if track.state == TrackState.Tracked:
                track.update(det, self.frame_id)
                activated_starcks.append(track)
            else:
                track.re_activate(det, self.frame_id, new_id=False)
                refind_stracks.append(track)
        for it in u_track:
            track = r_tracked_stracks[it]
            if not track.state == TrackState.Lost:
                track.mark_lost()
                lost_stracks.append(track)
        'Deal with unconfirmed tracks, usually tracks with only one beginning frame'
        detections = [detections[i] for i in u_detection]
        dists = matching.iou_distance(unconfirmed, detections)
        dists = matching.fuse_score(dists, detections)
        matches, u_unconfirmed, u_detection = matching.linear_assignment(dists, thresh=0.7)
        for itracked, idet in matches:
            unconfirmed[itracked].update(detections[idet], self.frame_id)
            activated_starcks.append(unconfirmed[itracked])
        for it in u_unconfirmed:
            track = unconfirmed[it]
            track.mark_removed()
            removed_stracks.append(track)
        ' Step 4: Init new stracks'
        for inew in u_detection:
            track = detections[inew]
            if track.score < self.det_thresh:
                continue
            track.activate(self.kalman_filter, self.frame_id)
            activated_starcks.append(track)
        ' Step 5: Update state'
        for track in self.lost_stracks:
            if self.frame_id - track.end_frame > self.max_time_lost:
                track.mark_removed()
                removed_stracks.append(track)
        self.tracked_stracks = [t for t in self.tracked_stracks if t.state == TrackState.Tracked]
        self.tracked_stracks = joint_stracks(self.tracked_stracks, activated_starcks)
        self.tracked_stracks = joint_stracks(self.tracked_stracks, refind_stracks)
        self.lost_stracks = sub_stracks(self.lost_stracks, self.tracked_stracks)
        self.lost_stracks.extend(lost_stracks)
        self.lost_stracks = sub_stracks(self.lost_stracks, self.removed_stracks)
        self.removed_stracks.extend(removed_stracks)
        self.tracked_stracks, self.lost_stracks = remove_duplicate_stracks(self.tracked_stracks, self.lost_stracks)
        output_stracks = [track for track in self.tracked_stracks if track.is_activated]
        outputs = []
        for t in output_stracks:
            output = []
            tlwh = t.tlwh
            tid = t.track_id
            tlwh = np.expand_dims(tlwh, axis=0)
            xyxy = xywh2xyxy(tlwh)
            xyxy = np.squeeze(xyxy, axis=0)
            output.extend(xyxy)
            output.append(tid)
            output.append(t.cls)
            output.append(t.score)
            outputs.append(output)
        return outputs

def __init__(self, track_thresh=0.45, match_thresh=0.8, track_buffer=25, frame_rate=30):
    self.tracked_stracks = []
    self.lost_stracks = []
    self.removed_stracks = []
    self.frame_id = 0
    self.track_buffer = track_buffer
    self.track_thresh = track_thresh
    self.match_thresh = match_thresh
    self.det_thresh = track_thresh + 0.1
    self.buffer_size = int(frame_rate / 30.0 * track_buffer)
    self.max_time_lost = self.buffer_size
    self.kalman_filter = KalmanFilter()

class STrack(BaseTrack):
    shared_kalman = KalmanFilter()

    def __init__(self, tlwh, score, cls, feat=None, feat_history=50):
        self._tlwh = np.asarray(tlwh, dtype=np.float32)
        self.kalman_filter = None
        self.mean, self.covariance = (None, None)
        self.is_activated = False
        self.cls = -1
        self.cls_hist = []
        self.update_cls(cls, score)
        self.score = score
        self.tracklet_len = 0
        self.smooth_feat = None
        self.curr_feat = None
        if feat is not None:
            self.update_features(feat)
        self.features = deque([], maxlen=feat_history)
        self.alpha = 0.9

    def update_features(self, feat):
        feat /= np.linalg.norm(feat)
        self.curr_feat = feat
        if self.smooth_feat is None:
            self.smooth_feat = feat
        else:
            self.smooth_feat = self.alpha * self.smooth_feat + (1 - self.alpha) * feat
        self.features.append(feat)
        self.smooth_feat /= np.linalg.norm(self.smooth_feat)

    def update_cls(self, cls, score):
        if len(self.cls_hist) > 0:
            max_freq = 0
            found = False
            for c in self.cls_hist:
                if cls == c[0]:
                    c[1] += score
                    found = True
                if c[1] > max_freq:
                    max_freq = c[1]
                    self.cls = c[0]
            if not found:
                self.cls_hist.append([cls, score])
                self.cls = cls
        else:
            self.cls_hist.append([cls, score])
            self.cls = cls

    def predict(self):
        mean_state = self.mean.copy()
        if self.state != TrackState.Tracked:
            mean_state[6] = 0
            mean_state[7] = 0
        self.mean, self.covariance = self.kalman_filter.predict(mean_state, self.covariance)

    @staticmethod
    def multi_predict(stracks):
        if len(stracks) > 0:
            multi_mean = np.asarray([st.mean.copy() for st in stracks])
            multi_covariance = np.asarray([st.covariance for st in stracks])
            for i, st in enumerate(stracks):
                if st.state != TrackState.Tracked:
                    multi_mean[i][6] = 0
                    multi_mean[i][7] = 0
            multi_mean, multi_covariance = STrack.shared_kalman.multi_predict(multi_mean, multi_covariance)
            for i, (mean, cov) in enumerate(zip(multi_mean, multi_covariance)):
                stracks[i].mean = mean
                stracks[i].covariance = cov

    @staticmethod
    def multi_gmc(stracks, H=np.eye(2, 3)):
        if len(stracks) > 0:
            multi_mean = np.asarray([st.mean.copy() for st in stracks])
            multi_covariance = np.asarray([st.covariance for st in stracks])
            R = H[:2, :2]
            R8x8 = np.kron(np.eye(4, dtype=float), R)
            t = H[:2, 2]
            for i, (mean, cov) in enumerate(zip(multi_mean, multi_covariance)):
                mean = R8x8.dot(mean)
                mean[:2] += t
                cov = R8x8.dot(cov).dot(R8x8.transpose())
                stracks[i].mean = mean
                stracks[i].covariance = cov

    def activate(self, kalman_filter, frame_id):
        """Start a new tracklet"""
        self.kalman_filter = kalman_filter
        self.track_id = self.next_id()
        self.mean, self.covariance = self.kalman_filter.initiate(self.tlwh_to_xywh(self._tlwh))
        self.tracklet_len = 0
        self.state = TrackState.Tracked
        if frame_id == 1:
            self.is_activated = True
        self.frame_id = frame_id
        self.start_frame = frame_id

    def re_activate(self, new_track, frame_id, new_id=False):
        self.mean, self.covariance = self.kalman_filter.update(self.mean, self.covariance, self.tlwh_to_xywh(new_track.tlwh))
        if new_track.curr_feat is not None:
            self.update_features(new_track.curr_feat)
        self.tracklet_len = 0
        self.state = TrackState.Tracked
        self.is_activated = True
        self.frame_id = frame_id
        if new_id:
            self.track_id = self.next_id()
        self.score = new_track.score
        self.update_cls(new_track.cls, new_track.score)

    def update(self, new_track, frame_id):
        """
        Update a matched track
        :type new_track: STrack
        :type frame_id: int
        :type update_feature: bool
        :return:
        """
        self.frame_id = frame_id
        self.tracklet_len += 1
        new_tlwh = new_track.tlwh
        self.mean, self.covariance = self.kalman_filter.update(self.mean, self.covariance, self.tlwh_to_xywh(new_tlwh))
        if new_track.curr_feat is not None:
            self.update_features(new_track.curr_feat)
        self.state = TrackState.Tracked
        self.is_activated = True
        self.score = new_track.score
        self.update_cls(new_track.cls, new_track.score)

    @property
    def tlwh(self):
        """Get current position in bounding box format `(top left x, top left y,
                width, height)`.
        """
        if self.mean is None:
            return self._tlwh.copy()
        ret = self.mean[:4].copy()
        ret[:2] -= ret[2:] / 2
        return ret

    @property
    def tlbr(self):
        """Convert bounding box to format `(min x, min y, max x, max y)`, i.e.,
        `(top left, bottom right)`.
        """
        ret = self.tlwh.copy()
        ret[2:] += ret[:2]
        return ret

    @property
    def xywh(self):
        """Convert bounding box to format `(min x, min y, max x, max y)`, i.e.,
        `(top left, bottom right)`.
        """
        ret = self.tlwh.copy()
        ret[:2] += ret[2:] / 2.0
        return ret

    @staticmethod
    def tlwh_to_xyah(tlwh):
        """Convert bounding box to format `(center x, center y, aspect ratio,
        height)`, where the aspect ratio is `width / height`.
        """
        ret = np.asarray(tlwh).copy()
        ret[:2] += ret[2:] / 2
        ret[2] /= ret[3]
        return ret

    @staticmethod
    def tlwh_to_xywh(tlwh):
        """Convert bounding box to format `(center x, center y, width,
        height)`.
        """
        ret = np.asarray(tlwh).copy()
        ret[:2] += ret[2:] / 2
        return ret

    def to_xywh(self):
        return self.tlwh_to_xywh(self.tlwh)

    @staticmethod
    def tlbr_to_tlwh(tlbr):
        ret = np.asarray(tlbr).copy()
        ret[2:] -= ret[:2]
        return ret

    @staticmethod
    def tlwh_to_tlbr(tlwh):
        ret = np.asarray(tlwh).copy()
        ret[2:] += ret[:2]
        return ret

    def __repr__(self):
        return 'OT_{}_({}-{})'.format(self.track_id, self.start_frame, self.end_frame)

def __init__(self, tlwh, score, cls, feat=None, feat_history=50):
    self._tlwh = np.asarray(tlwh, dtype=np.float32)
    self.kalman_filter = None
    self.mean, self.covariance = (None, None)
    self.is_activated = False
    self.cls = -1
    self.cls_hist = []
    self.update_cls(cls, score)
    self.score = score
    self.tracklet_len = 0
    self.smooth_feat = None
    self.curr_feat = None
    if feat is not None:
        self.update_features(feat)
    self.features = deque([], maxlen=feat_history)
    self.alpha = 0.9

def activate(self, kalman_filter, frame_id):
    """Start a new tracklet"""
    self.kalman_filter = kalman_filter
    self.track_id = self.next_id()
    self.mean, self.covariance = self.kalman_filter.initiate(self.tlwh_to_xywh(self._tlwh))
    self.tracklet_len = 0
    self.state = TrackState.Tracked
    if frame_id == 1:
        self.is_activated = True
    self.frame_id = frame_id
    self.start_frame = frame_id

def re_activate(self, new_track, frame_id, new_id=False):
    self.mean, self.covariance = self.kalman_filter.update(self.mean, self.covariance, self.tlwh_to_xywh(new_track.tlwh))
    if new_track.curr_feat is not None:
        self.update_features(new_track.curr_feat)
    self.tracklet_len = 0
    self.state = TrackState.Tracked
    self.is_activated = True
    self.frame_id = frame_id
    if new_id:
        self.track_id = self.next_id()
    self.score = new_track.score
    self.update_cls(new_track.cls, new_track.score)

def update(self, new_track, frame_id):
    """
        Update a matched track
        :type new_track: STrack
        :type frame_id: int
        :type update_feature: bool
        :return:
        """
    self.frame_id = frame_id
    self.tracklet_len += 1
    new_tlwh = new_track.tlwh
    self.mean, self.covariance = self.kalman_filter.update(self.mean, self.covariance, self.tlwh_to_xywh(new_tlwh))
    if new_track.curr_feat is not None:
        self.update_features(new_track.curr_feat)
    self.state = TrackState.Tracked
    self.is_activated = True
    self.score = new_track.score
    self.update_cls(new_track.cls, new_track.score)

def to_xywh(self):
    return self.tlwh_to_xywh(self.tlwh)

class BoTSORT(object):

    def __init__(self, model_weights, device, fp16, track_high_thresh: float=0.45, new_track_thresh: float=0.6, track_buffer: int=30, match_thresh: float=0.8, proximity_thresh: float=0.5, appearance_thresh: float=0.25, cmc_method: str='sparseOptFlow', frame_rate=30, lambda_=0.985):
        self.tracked_stracks = []
        self.lost_stracks = []
        self.removed_stracks = []
        BaseTrack.clear_count()
        self.frame_id = 0
        self.lambda_ = lambda_
        self.track_high_thresh = track_high_thresh
        self.new_track_thresh = new_track_thresh
        self.buffer_size = int(frame_rate / 30.0 * track_buffer)
        self.max_time_lost = self.buffer_size
        self.kalman_filter = KalmanFilter()
        self.proximity_thresh = proximity_thresh
        self.appearance_thresh = appearance_thresh
        self.match_thresh = match_thresh
        self.model = ReIDDetectMultiBackend(weights=model_weights, device=device, fp16=fp16)
        self.gmc = GMC(method=cmc_method, verbose=[None, False])

    def update(self, output_results, img):
        self.frame_id += 1
        activated_starcks = []
        refind_stracks = []
        lost_stracks = []
        removed_stracks = []
        xyxys = output_results[:, 0:4]
        xywh = xyxy2xywh(xyxys.numpy())
        confs = output_results[:, 4]
        clss = output_results[:, 5]
        classes = clss.numpy()
        xyxys = xyxys.numpy()
        confs = confs.numpy()
        remain_inds = confs > self.track_high_thresh
        inds_low = confs > 0.1
        inds_high = confs < self.track_high_thresh
        inds_second = np.logical_and(inds_low, inds_high)
        dets_second = xywh[inds_second]
        dets = xywh[remain_inds]
        scores_keep = confs[remain_inds]
        scores_second = confs[inds_second]
        classes_keep = classes[remain_inds]
        clss_second = classes[inds_second]
        self.height, self.width = img.shape[:2]
        'Extract embeddings '
        features_keep = self._get_features(dets, img)
        if len(dets) > 0:
            'Detections'
            detections = [STrack(xyxy, s, c, f.cpu().numpy()) for xyxy, s, c, f in zip(dets, scores_keep, classes_keep, features_keep)]
        else:
            detections = []
        ' Add newly detected tracklets to tracked_stracks'
        unconfirmed = []
        tracked_stracks = []
        for track in self.tracked_stracks:
            if not track.is_activated:
                unconfirmed.append(track)
            else:
                tracked_stracks.append(track)
        ' Step 2: First association, with high score detection boxes'
        strack_pool = joint_stracks(tracked_stracks, self.lost_stracks)
        STrack.multi_predict(strack_pool)
        warp = self.gmc.apply(img, dets)
        STrack.multi_gmc(strack_pool, warp)
        STrack.multi_gmc(unconfirmed, warp)
        raw_emb_dists = matching.embedding_distance(strack_pool, detections)
        dists = matching.fuse_motion(self.kalman_filter, raw_emb_dists, strack_pool, detections, only_position=False, lambda_=self.lambda_)
        matches, u_track, u_detection = matching.linear_assignment(dists, thresh=self.match_thresh)
        for itracked, idet in matches:
            track = strack_pool[itracked]
            det = detections[idet]
            if track.state == TrackState.Tracked:
                track.update(detections[idet], self.frame_id)
                activated_starcks.append(track)
            else:
                track.re_activate(det, self.frame_id, new_id=False)
                refind_stracks.append(track)
        ' Step 3: Second association, with low score detection boxes'
        if len(dets_second) > 0:
            'Detections'
            detections_second = [STrack(STrack.tlbr_to_tlwh(tlbr), s, c) for tlbr, s, c in zip(dets_second, scores_second, clss_second)]
        else:
            detections_second = []
        r_tracked_stracks = [strack_pool[i] for i in u_track if strack_pool[i].state == TrackState.Tracked]
        dists = matching.iou_distance(r_tracked_stracks, detections_second)
        matches, u_track, u_detection_second = matching.linear_assignment(dists, thresh=0.5)
        for itracked, idet in matches:
            track = r_tracked_stracks[itracked]
            det = detections_second[idet]
            if track.state == TrackState.Tracked:
                track.update(det, self.frame_id)
                activated_starcks.append(track)
            else:
                track.re_activate(det, self.frame_id, new_id=False)
                refind_stracks.append(track)
        for it in u_track:
            track = r_tracked_stracks[it]
            if not track.state == TrackState.Lost:
                track.mark_lost()
                lost_stracks.append(track)
        'Deal with unconfirmed tracks, usually tracks with only one beginning frame'
        detections = [detections[i] for i in u_detection]
        ious_dists = matching.iou_distance(unconfirmed, detections)
        ious_dists_mask = ious_dists > self.proximity_thresh
        ious_dists = matching.fuse_score(ious_dists, detections)
        emb_dists = matching.embedding_distance(unconfirmed, detections) / 2.0
        raw_emb_dists = emb_dists.copy()
        emb_dists[emb_dists > self.appearance_thresh] = 1.0
        emb_dists[ious_dists_mask] = 1.0
        dists = np.minimum(ious_dists, emb_dists)
        matches, u_unconfirmed, u_detection = matching.linear_assignment(dists, thresh=0.7)
        for itracked, idet in matches:
            unconfirmed[itracked].update(detections[idet], self.frame_id)
            activated_starcks.append(unconfirmed[itracked])
        for it in u_unconfirmed:
            track = unconfirmed[it]
            track.mark_removed()
            removed_stracks.append(track)
        ' Step 4: Init new stracks'
        for inew in u_detection:
            track = detections[inew]
            if track.score < self.new_track_thresh:
                continue
            track.activate(self.kalman_filter, self.frame_id)
            activated_starcks.append(track)
        ' Step 5: Update state'
        for track in self.lost_stracks:
            if self.frame_id - track.end_frame > self.max_time_lost:
                track.mark_removed()
                removed_stracks.append(track)
        ' Merge '
        self.tracked_stracks = [t for t in self.tracked_stracks if t.state == TrackState.Tracked]
        self.tracked_stracks = joint_stracks(self.tracked_stracks, activated_starcks)
        self.tracked_stracks = joint_stracks(self.tracked_stracks, refind_stracks)
        self.lost_stracks = sub_stracks(self.lost_stracks, self.tracked_stracks)
        self.lost_stracks.extend(lost_stracks)
        self.lost_stracks = sub_stracks(self.lost_stracks, self.removed_stracks)
        self.removed_stracks.extend(removed_stracks)
        self.tracked_stracks, self.lost_stracks = remove_duplicate_stracks(self.tracked_stracks, self.lost_stracks)
        output_stracks = [track for track in self.tracked_stracks if track.is_activated]
        outputs = []
        for t in output_stracks:
            output = []
            tlwh = t.tlwh
            tid = t.track_id
            tlwh = np.expand_dims(tlwh, axis=0)
            xyxy = xywh2xyxy(tlwh)
            xyxy = np.squeeze(xyxy, axis=0)
            output.extend(xyxy)
            output.append(tid)
            output.append(t.cls)
            output.append(t.score)
            outputs.append(output)
        return outputs

    def _xywh_to_xyxy(self, bbox_xywh):
        x, y, w, h = bbox_xywh
        x1 = max(int(x - w / 2), 0)
        x2 = min(int(x + w / 2), self.width - 1)
        y1 = max(int(y - h / 2), 0)
        y2 = min(int(y + h / 2), self.height - 1)
        return (x1, y1, x2, y2)

    def _get_features(self, bbox_xywh, ori_img):
        im_crops = []
        for box in bbox_xywh:
            x1, y1, x2, y2 = self._xywh_to_xyxy(box)
            im = ori_img[y1:y2, x1:x2]
            im_crops.append(im)
        if im_crops:
            features = self.model(im_crops)
        else:
            features = np.array([])
        return features

def __init__(self, model_weights, device, fp16, track_high_thresh: float=0.45, new_track_thresh: float=0.6, track_buffer: int=30, match_thresh: float=0.8, proximity_thresh: float=0.5, appearance_thresh: float=0.25, cmc_method: str='sparseOptFlow', frame_rate=30, lambda_=0.985):
    self.tracked_stracks = []
    self.lost_stracks = []
    self.removed_stracks = []
    BaseTrack.clear_count()
    self.frame_id = 0
    self.lambda_ = lambda_
    self.track_high_thresh = track_high_thresh
    self.new_track_thresh = new_track_thresh
    self.buffer_size = int(frame_rate / 30.0 * track_buffer)
    self.max_time_lost = self.buffer_size
    self.kalman_filter = KalmanFilter()
    self.proximity_thresh = proximity_thresh
    self.appearance_thresh = appearance_thresh
    self.match_thresh = match_thresh
    self.model = ReIDDetectMultiBackend(weights=model_weights, device=device, fp16=fp16)
    self.gmc = GMC(method=cmc_method, verbose=[None, False])

