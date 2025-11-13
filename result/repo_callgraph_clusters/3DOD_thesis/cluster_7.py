# Cluster 7

def draw_3dbbox_from_keypoints(img, keypoints):
    img = np.copy(img)
    color = [190, 0, 255]
    front_color = [255, 230, 0]
    lines = [[0, 3, 7, 4, 0], [1, 2, 6, 5, 1], [0, 1], [2, 3], [6, 7], [4, 5]]
    colors = [front_color, color, color, color, color, color]
    for n, line in enumerate(lines):
        bg = colors[n]
        cv2.polylines(img, np.int32([keypoints[line]]), False, bg, lineType=cv2.LINE_AA, thickness=2)
    return img

def draw_3dbbox_from_keypoints(img, keypoints):
    img = np.copy(img)
    color = [190, 0, 255]
    front_color = [255, 230, 0]
    lines = [[0, 3, 7, 4, 0], [1, 2, 6, 5, 1], [0, 1], [2, 3], [6, 7], [4, 5]]
    colors = [front_color, color, color, color, color, color]
    for n, line in enumerate(lines):
        bg = colors[n]
        cv2.polylines(img, np.int32([keypoints[line]]), False, bg, lineType=cv2.LINE_AA, thickness=2)
    return img

def draw_3dbbox_from_keypoints(img, keypoints):
    img = np.copy(img)
    color = [190, 0, 255]
    front_color = [255, 230, 0]
    lines = [[0, 3, 7, 4, 0], [1, 2, 6, 5, 1], [0, 1], [2, 3], [6, 7], [4, 5]]
    colors = [front_color, color, color, color, color, color]
    for n, line in enumerate(lines):
        bg = colors[n]
        cv2.polylines(img, np.int32([keypoints[line]]), False, bg, lineType=cv2.LINE_AA, thickness=2)
    return img

