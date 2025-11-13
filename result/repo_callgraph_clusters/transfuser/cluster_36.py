# Cluster 36

class DynamicPointNet(nn.Module):

    def __init__(self, num_input=9, num_features=[32, 32]):
        super().__init__()
        L = []
        for num_feature in num_features:
            L += [nn.Linear(num_input, num_feature), nn.BatchNorm1d(num_feature), nn.ReLU(inplace=True)]
            num_input = num_feature
        self.net = nn.Sequential(*L)

    def forward(self, points, inverse_indices):
        """
        TODO: multiple layers
        """
        feat = self.net(points)
        feat_max = scatter_max(feat, inverse_indices, dim=0)[0]
        return feat_max

def forward(self, points, inverse_indices):
    """
        TODO: multiple layers
        """
    feat = self.net(points)
    feat_max = scatter_max(feat, inverse_indices, dim=0)[0]
    return feat_max

