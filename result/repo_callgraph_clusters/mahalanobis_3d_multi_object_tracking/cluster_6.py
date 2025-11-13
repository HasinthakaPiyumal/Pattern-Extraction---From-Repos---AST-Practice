# Cluster 6

@jit
def poly_area(x, y):
    return 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))

def convert_3dbox_to_8corner(bbox3d_input, nuscenes_to_kitti=False):
    """ Takes an object and a projection matrix (P) and projects the 3d
        bounding box into the image plane.
        Returns:
            corners_2d: (8,2) array in left image coord.
            corners_3d: (8,3) array in in rect camera coord.
        Note: the output of this function will be passed to the funciton iou3d
            for calculating the 3D-IOU. But the function iou3d was written for 
            kitti, so the caller needs to set nuscenes_to_kitti to True if 
            the input bbox3d_input is in nuscenes format.
    """
    bbox3d = copy.copy(bbox3d_input)
    if nuscenes_to_kitti:
        bbox3d_nuscenes = copy.copy(bbox3d)
        bbox3d[0] = bbox3d_nuscenes[1]
        bbox3d[1] = -bbox3d_nuscenes[2]
        bbox3d[2] = -bbox3d_nuscenes[0]
        bbox3d[3] = -bbox3d_nuscenes[3]
        bbox3d[4] = bbox3d_nuscenes[5]
        bbox3d[5] = bbox3d_nuscenes[4]
    R = roty(bbox3d[3])
    l = bbox3d[4]
    w = bbox3d[5]
    h = bbox3d[6]
    x_corners = [l / 2, l / 2, -l / 2, -l / 2, l / 2, l / 2, -l / 2, -l / 2]
    y_corners = [0, 0, 0, 0, -h, -h, -h, -h]
    z_corners = [w / 2, -w / 2, -w / 2, w / 2, w / 2, -w / 2, -w / 2, w / 2]
    corners_3d = np.dot(R, np.vstack([x_corners, y_corners, z_corners]))
    corners_3d[0, :] = corners_3d[0, :] + bbox3d[0]
    corners_3d[1, :] = corners_3d[1, :] + bbox3d[1]
    corners_3d[2, :] = corners_3d[2, :] + bbox3d[2]
    return np.transpose(corners_3d)

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

