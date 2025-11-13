# Cluster 1

@LOSSES.register_module()
class CrossEntropyLoss(nn.Module):

    def __init__(self, weight=None, size_average=None, reduce=None, reduction='mean', label_smoothing=0.0, loss_weight=1.0, ignore_index=255):
        super(CrossEntropyLoss, self).__init__()
        self.loss_weight = loss_weight
        self.loss = nn.CrossEntropyLoss(weight=weight, size_average=size_average, ignore_index=ignore_index, reduce=reduce, reduction=reduction, label_smoothing=label_smoothing)

    def forward(self, pred, target):
        return self.loss(pred, target) * self.loss_weight

def forward(self, pred, target):
    return self.loss(pred, target) * self.loss_weight

