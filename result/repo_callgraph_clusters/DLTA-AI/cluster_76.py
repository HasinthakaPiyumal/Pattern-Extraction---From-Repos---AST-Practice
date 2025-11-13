# Cluster 76

def test_eval_recalls():
    gts = [gt_bboxes, gt_bboxes, gt_bboxes]
    proposals = [det_bboxes, det_bboxes, det_bboxes]
    recall = eval_recalls(gts, proposals, proposal_nums=2, use_legacy_coordinate=True)
    assert recall.shape == (1, 1)
    assert 0.66 < recall[0][0] < 0.667
    recall = eval_recalls(gts, proposals, proposal_nums=2, use_legacy_coordinate=False)
    assert recall.shape == (1, 1)
    assert 0.66 < recall[0][0] < 0.667
    recall = eval_recalls(gts, proposals, proposal_nums=2, use_legacy_coordinate=True)
    assert recall.shape == (1, 1)
    assert 0.66 < recall[0][0] < 0.667
    recall = eval_recalls(gts, proposals, iou_thrs=[0.1, 0.9], proposal_nums=2, use_legacy_coordinate=False)
    assert recall.shape == (1, 2)
    assert recall[0][1] <= recall[0][0]
    recall = eval_recalls(gts, proposals, iou_thrs=[0.1, 0.9], proposal_nums=2, use_legacy_coordinate=True)
    assert recall.shape == (1, 2)
    assert recall[0][1] <= recall[0][0]

