# Cluster 34

def parse_labels(labels, rad=0):
    bboxes = {}
    for result in labels:
        num_points = result['num_points']
        distance = result['distance']
        x = result['position'][0]
        y = result['position'][1]
        bbox = result['extent'] + result['position'] + [result['yaw'], result['speed'], result['brake']]
        bbox = get_bbox_label(bbox, rad)
        if num_points <= 1 or bbox[0] <= 0.0 or bbox[0] >= 255.0 or (bbox[1] <= 0.0) or (bbox[1] >= 255.0):
            continue
        bboxes[result['id']] = bbox
    return bboxes

