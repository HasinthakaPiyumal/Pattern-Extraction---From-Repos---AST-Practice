# Cluster 10

def diff_orientation_correction(det, trk):
    """
  return the angle diff = det - trk
  if angle diff > 90 or < -90, rotate trk and update the angle diff
  """
    diff = det - trk
    diff = angle_in_range(diff)
    if diff > np.pi / 2:
        diff -= np.pi
    if diff < -np.pi / 2:
        diff += np.pi
    diff = angle_in_range(diff)
    return diff

