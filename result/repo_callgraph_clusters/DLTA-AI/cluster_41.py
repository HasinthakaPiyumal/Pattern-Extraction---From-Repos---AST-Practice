# Cluster 41

class DummyONNXNMSop(torch.autograd.Function):
    """DummyONNXNMSop.

    This class is only for creating onnx::NonMaxSuppression.
    """

    @staticmethod
    def forward(ctx, boxes, scores, max_output_boxes_per_class, iou_threshold, score_threshold):
        return DummyONNXNMSop.output

    @staticmethod
    def symbolic(g, boxes, scores, max_output_boxes_per_class, iou_threshold, score_threshold):
        return g.op('NonMaxSuppression', boxes, scores, max_output_boxes_per_class, iou_threshold, score_threshold, outputs=1)

@staticmethod
def symbolic(g, boxes, scores, max_output_boxes_per_class, iou_threshold, score_threshold):
    return g.op('NonMaxSuppression', boxes, scores, max_output_boxes_per_class, iou_threshold, score_threshold, outputs=1)

