# Cluster 22

@NECKS.register_module()
class YOLOV3Neck(BaseModule):
    """The neck of YOLOV3.

    It can be treated as a simplified version of FPN. It
    will take the result from Darknet backbone and do some upsampling and
    concatenation. It will finally output the detection result.

    Note:
        The input feats should be from top to bottom.
            i.e., from high-lvl to low-lvl
        But YOLOV3Neck will process them in reversed order.
            i.e., from bottom (high-lvl) to top (low-lvl)

    Args:
        num_scales (int): The number of scales / stages.
        in_channels (List[int]): The number of input channels per scale.
        out_channels (List[int]): The number of output channels  per scale.
        conv_cfg (dict, optional): Config dict for convolution layer.
            Default: None.
        norm_cfg (dict, optional): Dictionary to construct and config norm
            layer. Default: dict(type='BN', requires_grad=True)
        act_cfg (dict, optional): Config dict for activation layer.
            Default: dict(type='LeakyReLU', negative_slope=0.1).
        init_cfg (dict or list[dict], optional): Initialization config dict.
            Default: None
    """

    def __init__(self, num_scales, in_channels, out_channels, conv_cfg=None, norm_cfg=dict(type='BN', requires_grad=True), act_cfg=dict(type='LeakyReLU', negative_slope=0.1), init_cfg=None):
        super(YOLOV3Neck, self).__init__(init_cfg)
        assert num_scales == len(in_channels) == len(out_channels)
        self.num_scales = num_scales
        self.in_channels = in_channels
        self.out_channels = out_channels
        cfg = dict(conv_cfg=conv_cfg, norm_cfg=norm_cfg, act_cfg=act_cfg)
        self.detect1 = DetectionBlock(in_channels[0], out_channels[0], **cfg)
        for i in range(1, self.num_scales):
            in_c, out_c = (self.in_channels[i], self.out_channels[i])
            inter_c = out_channels[i - 1]
            self.add_module(f'conv{i}', ConvModule(inter_c, out_c, 1, **cfg))
            self.add_module(f'detect{i + 1}', DetectionBlock(in_c + out_c, out_c, **cfg))

    def forward(self, feats):
        assert len(feats) == self.num_scales
        outs = []
        out = self.detect1(feats[-1])
        outs.append(out)
        for i, x in enumerate(reversed(feats[:-1])):
            conv = getattr(self, f'conv{i + 1}')
            tmp = conv(out)
            tmp = F.interpolate(tmp, scale_factor=2)
            tmp = torch.cat((tmp, x), 1)
            detect = getattr(self, f'detect{i + 2}')
            out = detect(tmp)
            outs.append(out)
        return tuple(outs)

def forward(self, feats):
    assert len(feats) == self.num_scales
    outs = []
    out = self.detect1(feats[-1])
    outs.append(out)
    for i, x in enumerate(reversed(feats[:-1])):
        conv = getattr(self, f'conv{i + 1}')
        tmp = conv(out)
        tmp = F.interpolate(tmp, scale_factor=2)
        tmp = torch.cat((tmp, x), 1)
        detect = getattr(self, f'detect{i + 2}')
        out = detect(tmp)
        outs.append(out)
    return tuple(outs)

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

class OCSort(object):

    def __init__(self, det_thresh, max_age=30, min_hits=3, iou_threshold=0.3, delta_t=3, asso_func='iou', inertia=0.2, use_byte=False):
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
        self.use_byte = use_byte
        KalmanBoxTracker.count = 0

    def update(self, dets, _):
        """
        Params:
          dets - a numpy array of detections in the format [[x1,y1,x2,y2,score],[x1,y1,x2,y2,score],...]
        Requires: this method must be called once for each frame even with empty detections (use np.empty((0, 5)) for frames without detections).
        Returns the a similar array, where the last column is the object ID.
        NOTE: The number of objects returned may differ from the number of detections provided.
        """
        self.frame_count += 1
        xyxys = dets[:, 0:4]
        confs = dets[:, 4]
        clss = dets[:, 5]
        classes = clss.numpy()
        xyxys = xyxys.numpy()
        confs = confs.numpy()
        output_results = np.column_stack((xyxys, confs, classes))
        inds_low = confs > 0.1
        inds_high = confs < self.det_thresh
        inds_second = np.logical_and(inds_low, inds_high)
        dets_second = output_results[inds_second]
        remain_inds = confs > self.det_thresh
        dets = output_results[remain_inds]
        trks = np.zeros((len(self.trackers), 5))
        to_del = []
        ret = []
        for t, trk in enumerate(trks):
            pos = self.trackers[t].predict()[0]
            trk[:] = [pos[0], pos[1], pos[2], pos[3], 0]
            if np.any(np.isnan(pos)):
                to_del.append(t)
        trks = np.ma.compress_rows(np.ma.masked_invalid(trks))
        for t in reversed(to_del):
            self.trackers.pop(t)
        velocities = np.array([trk.velocity if trk.velocity is not None else np.array((0, 0)) for trk in self.trackers])
        last_boxes = np.array([trk.last_observation for trk in self.trackers])
        k_observations = np.array([k_previous_obs(trk.observations, trk.age, self.delta_t) for trk in self.trackers])
        '\n            First round of association\n        '
        matched, unmatched_dets, unmatched_trks = associate(dets, trks, self.iou_threshold, velocities, k_observations, self.inertia)
        for m in matched:
            self.trackers[m[1]].update(dets[m[0], :5], dets[m[0], 5])
        '\n            Second round of associaton by OCR\n        '
        if self.use_byte and len(dets_second) > 0 and (unmatched_trks.shape[0] > 0):
            u_trks = trks[unmatched_trks]
            iou_left = self.asso_func(dets_second, u_trks)
            iou_left = np.array(iou_left)
            if iou_left.max() > self.iou_threshold:
                '\n                    NOTE: by using a lower threshold, e.g., self.iou_threshold - 0.1, you may\n                    get a higher performance especially on MOT17/MOT20 datasets. But we keep it\n                    uniform here for simplicity\n                '
                matched_indices = linear_assignment(-iou_left)
                to_remove_trk_indices = []
                for m in matched_indices:
                    det_ind, trk_ind = (m[0], unmatched_trks[m[1]])
                    if iou_left[m[0], m[1]] < self.iou_threshold:
                        continue
                    self.trackers[trk_ind].update(dets_second[det_ind, :5], dets_second[det_ind, 5])
                    to_remove_trk_indices.append(trk_ind)
                unmatched_trks = np.setdiff1d(unmatched_trks, np.array(to_remove_trk_indices))
        if unmatched_dets.shape[0] > 0 and unmatched_trks.shape[0] > 0:
            left_dets = dets[unmatched_dets]
            left_trks = last_boxes[unmatched_trks]
            iou_left = self.asso_func(left_dets, left_trks)
            iou_left = np.array(iou_left)
            if iou_left.max() > self.iou_threshold:
                '\n                    NOTE: by using a lower threshold, e.g., self.iou_threshold - 0.1, you may\n                    get a higher performance especially on MOT17/MOT20 datasets. But we keep it\n                    uniform here for simplicity\n                '
                rematched_indices = linear_assignment(-iou_left)
                to_remove_det_indices = []
                to_remove_trk_indices = []
                for m in rematched_indices:
                    det_ind, trk_ind = (unmatched_dets[m[0]], unmatched_trks[m[1]])
                    if iou_left[m[0], m[1]] < self.iou_threshold:
                        continue
                    self.trackers[trk_ind].update(dets[det_ind, :5], dets[det_ind, 5])
                    to_remove_det_indices.append(det_ind)
                    to_remove_trk_indices.append(trk_ind)
                unmatched_dets = np.setdiff1d(unmatched_dets, np.array(to_remove_det_indices))
                unmatched_trks = np.setdiff1d(unmatched_trks, np.array(to_remove_trk_indices))
        for m in unmatched_trks:
            self.trackers[m].update(None, None)
        for i in unmatched_dets:
            trk = KalmanBoxTracker(dets[i, :5], dets[i, 5], delta_t=self.delta_t)
            self.trackers.append(trk)
        i = len(self.trackers)
        for trk in reversed(self.trackers):
            if trk.last_observation.sum() < 0:
                d = trk.get_state()[0]
            else:
                "\n                    this is optional to use the recent observation or the kalman filter prediction,\n                    we didn't notice significant difference here\n                "
                d = trk.last_observation[:4]
            if trk.time_since_update < 1 and (trk.hit_streak >= self.min_hits or self.frame_count <= self.min_hits):
                ret.append(np.concatenate((d, [trk.id + 1], [trk.cls], [trk.conf])).reshape(1, -1))
            i -= 1
            if trk.time_since_update > self.max_age:
                self.trackers.pop(i)
        if len(ret) > 0:
            return np.concatenate(ret)
        return np.empty((0, 5))

def update(self, dets, _):
    """
        Params:
          dets - a numpy array of detections in the format [[x1,y1,x2,y2,score],[x1,y1,x2,y2,score],...]
        Requires: this method must be called once for each frame even with empty detections (use np.empty((0, 5)) for frames without detections).
        Returns the a similar array, where the last column is the object ID.
        NOTE: The number of objects returned may differ from the number of detections provided.
        """
    self.frame_count += 1
    xyxys = dets[:, 0:4]
    confs = dets[:, 4]
    clss = dets[:, 5]
    classes = clss.numpy()
    xyxys = xyxys.numpy()
    confs = confs.numpy()
    output_results = np.column_stack((xyxys, confs, classes))
    inds_low = confs > 0.1
    inds_high = confs < self.det_thresh
    inds_second = np.logical_and(inds_low, inds_high)
    dets_second = output_results[inds_second]
    remain_inds = confs > self.det_thresh
    dets = output_results[remain_inds]
    trks = np.zeros((len(self.trackers), 5))
    to_del = []
    ret = []
    for t, trk in enumerate(trks):
        pos = self.trackers[t].predict()[0]
        trk[:] = [pos[0], pos[1], pos[2], pos[3], 0]
        if np.any(np.isnan(pos)):
            to_del.append(t)
    trks = np.ma.compress_rows(np.ma.masked_invalid(trks))
    for t in reversed(to_del):
        self.trackers.pop(t)
    velocities = np.array([trk.velocity if trk.velocity is not None else np.array((0, 0)) for trk in self.trackers])
    last_boxes = np.array([trk.last_observation for trk in self.trackers])
    k_observations = np.array([k_previous_obs(trk.observations, trk.age, self.delta_t) for trk in self.trackers])
    '\n            First round of association\n        '
    matched, unmatched_dets, unmatched_trks = associate(dets, trks, self.iou_threshold, velocities, k_observations, self.inertia)
    for m in matched:
        self.trackers[m[1]].update(dets[m[0], :5], dets[m[0], 5])
    '\n            Second round of associaton by OCR\n        '
    if self.use_byte and len(dets_second) > 0 and (unmatched_trks.shape[0] > 0):
        u_trks = trks[unmatched_trks]
        iou_left = self.asso_func(dets_second, u_trks)
        iou_left = np.array(iou_left)
        if iou_left.max() > self.iou_threshold:
            '\n                    NOTE: by using a lower threshold, e.g., self.iou_threshold - 0.1, you may\n                    get a higher performance especially on MOT17/MOT20 datasets. But we keep it\n                    uniform here for simplicity\n                '
            matched_indices = linear_assignment(-iou_left)
            to_remove_trk_indices = []
            for m in matched_indices:
                det_ind, trk_ind = (m[0], unmatched_trks[m[1]])
                if iou_left[m[0], m[1]] < self.iou_threshold:
                    continue
                self.trackers[trk_ind].update(dets_second[det_ind, :5], dets_second[det_ind, 5])
                to_remove_trk_indices.append(trk_ind)
            unmatched_trks = np.setdiff1d(unmatched_trks, np.array(to_remove_trk_indices))
    if unmatched_dets.shape[0] > 0 and unmatched_trks.shape[0] > 0:
        left_dets = dets[unmatched_dets]
        left_trks = last_boxes[unmatched_trks]
        iou_left = self.asso_func(left_dets, left_trks)
        iou_left = np.array(iou_left)
        if iou_left.max() > self.iou_threshold:
            '\n                    NOTE: by using a lower threshold, e.g., self.iou_threshold - 0.1, you may\n                    get a higher performance especially on MOT17/MOT20 datasets. But we keep it\n                    uniform here for simplicity\n                '
            rematched_indices = linear_assignment(-iou_left)
            to_remove_det_indices = []
            to_remove_trk_indices = []
            for m in rematched_indices:
                det_ind, trk_ind = (unmatched_dets[m[0]], unmatched_trks[m[1]])
                if iou_left[m[0], m[1]] < self.iou_threshold:
                    continue
                self.trackers[trk_ind].update(dets[det_ind, :5], dets[det_ind, 5])
                to_remove_det_indices.append(det_ind)
                to_remove_trk_indices.append(trk_ind)
            unmatched_dets = np.setdiff1d(unmatched_dets, np.array(to_remove_det_indices))
            unmatched_trks = np.setdiff1d(unmatched_trks, np.array(to_remove_trk_indices))
    for m in unmatched_trks:
        self.trackers[m].update(None, None)
    for i in unmatched_dets:
        trk = KalmanBoxTracker(dets[i, :5], dets[i, 5], delta_t=self.delta_t)
        self.trackers.append(trk)
    i = len(self.trackers)
    for trk in reversed(self.trackers):
        if trk.last_observation.sum() < 0:
            d = trk.get_state()[0]
        else:
            "\n                    this is optional to use the recent observation or the kalman filter prediction,\n                    we didn't notice significant difference here\n                "
            d = trk.last_observation[:4]
        if trk.time_since_update < 1 and (trk.hit_streak >= self.min_hits or self.frame_count <= self.min_hits):
            ret.append(np.concatenate((d, [trk.id + 1], [trk.cls], [trk.conf])).reshape(1, -1))
        i -= 1
        if trk.time_since_update > self.max_age:
            self.trackers.pop(i)
    if len(ret) > 0:
        return np.concatenate(ret)
    return np.empty((0, 5))

