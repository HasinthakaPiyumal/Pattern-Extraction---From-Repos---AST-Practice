# Cluster 11

def isstring(string_test):
    try:
        return isinstance(string_test, basestring)
    except NameError:
        return isinstance(string_test, str)

def islist(list_test):
    return isinstance(list_test, list)

def islogical(logical_test):
    return isinstance(logical_test, bool)

def isnparray(nparray_test):
    return isinstance(nparray_test, np.ndarray)

def isinteger(integer_test):
    if isnparray(integer_test):
        return False
    try:
        return isinstance(integer_test, int) or int(integer_test) == integer_test
    except (TypeError, ValueError):
        return False

def rotation_to_positive_z_angle(rotation):
    q = Quaternion(rotation)
    angle = q.angle if q.axis[2] > 0 else -q.angle
    return angle

def format_sample_result(sample_token, tracking_name, tracker):
    """
  Input:
    tracker: (9): [h, w, l, x, y, z, rot_y], tracking_id, tracking_score
  Output:
  sample_result {
    "sample_token":   <str>         -- Foreign key. Identifies the sample/keyframe for which objects are detected.
    "translation":    <float> [3]   -- Estimated bounding box location in meters in the global frame: center_x, center_y, center_z.
    "size":           <float> [3]   -- Estimated bounding box size in meters: width, length, height.
    "rotation":       <float> [4]   -- Estimated bounding box orientation as quaternion in the global frame: w, x, y, z.
    "velocity":       <float> [2]   -- Estimated bounding box velocity in m/s in the global frame: vx, vy.
    "tracking_id":    <str>         -- Unique object id that is used to identify an object track across samples.
    "tracking_name":  <str>         -- The predicted class for this sample_result, e.g. car, pedestrian.
                                       Note that the tracking_name cannot change throughout a track.
    "tracking_score": <float>       -- Object prediction score between 0 and 1 for the class identified by tracking_name.
                                       We average over frame level scores to compute the track level score.
                                       The score is used to determine positive and negative tracks via thresholding.
  }
  """
    rotation = Quaternion(axis=[0, 0, 1], angle=tracker[6]).elements
    sample_result = {'sample_token': sample_token, 'translation': [tracker[3], tracker[4], tracker[5]], 'size': [tracker[1], tracker[2], tracker[0]], 'rotation': [rotation[0], rotation[1], rotation[2], rotation[3]], 'velocity': [0, 0], 'tracking_id': str(int(tracker[7])), 'tracking_name': tracking_name, 'tracking_score': tracker[8]}
    return sample_result

