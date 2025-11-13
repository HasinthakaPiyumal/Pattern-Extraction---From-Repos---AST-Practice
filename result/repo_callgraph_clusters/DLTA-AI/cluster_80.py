# Cluster 80

def construct_toy_data(poly2mask=True):
    img_info = dict(height=427, width=640)
    ann_info = _construct_ann_info(h=img_info['height'], w=img_info['width'])
    results = dict(img_info=img_info, ann_info=ann_info)
    _construct_img(results)
    _load_bboxes(results)
    _load_labels(results)
    _load_masks(results, poly2mask)
    _construct_semantic_seg(results)
    return results

