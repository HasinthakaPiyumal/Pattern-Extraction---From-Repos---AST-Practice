# Cluster 6

def getBinNumber4(angle):
    if angle >= -np.pi / 4 and angle < np.pi / 4:
        bin_number = 0
    elif angle >= np.pi / 4 and angle < 3 * np.pi / 4:
        bin_number = 1
    elif angle >= 3 * np.pi / 4 and angle < np.pi or (angle >= -np.pi and angle < -3 * np.pi / 4):
        bin_number = 2
    elif angle >= -3 * np.pi / 4 and angle < -np.pi / 4:
        bin_number = 3
    else:
        raise Exception('getBinNumber4: angle is not in [-pi, pi[')
    return bin_number

def getBinNumber(angle, NH):
    if NH == 4:
        return getBinNumber4(angle)
    else:
        raise Exception('getBinNumber: NH is not 4')

def getBinCenter(bin_number, NH):
    if NH == 4:
        bin_center = wrapToPi(bin_number * (np.pi / 2))
    else:
        raise Exception('getBinCenter: NH is not 4')
    return bin_center

def getBinCenters(bin_numbers, NH):
    if NH == 4:
        bin_centers = wrapToPi(bin_numbers * (np.pi / 2))
    else:
        raise Exception('getBinCenters: NH is not 4')
    return bin_centers

def getBinNumber4(angle):
    if angle >= -np.pi / 4 and angle < np.pi / 4:
        bin_number = 0
    elif angle >= np.pi / 4 and angle < 3 * np.pi / 4:
        bin_number = 1
    elif angle >= 3 * np.pi / 4 and angle < np.pi or (angle >= -np.pi and angle < -3 * np.pi / 4):
        bin_number = 2
    elif angle >= -3 * np.pi / 4 and angle < -np.pi / 4:
        bin_number = 3
    else:
        raise Exception('getBinNumber4: angle is not in [-pi, pi[')
    return bin_number

def getBinNumber(angle, NH):
    if NH == 4:
        return getBinNumber4(angle)
    else:
        raise Exception('getBinNumber: NH is not 4')

def getBinCenter(bin_number, NH):
    if NH == 4:
        bin_center = wrapToPi(bin_number * (np.pi / 2))
    else:
        raise Exception('getBinCenter: NH is not 4')
    return bin_center

def getBinCenters(bin_numbers, NH):
    if NH == 4:
        bin_centers = wrapToPi(bin_numbers * (np.pi / 2))
    else:
        raise Exception('getBinCenters: NH is not 4')
    return bin_centers

