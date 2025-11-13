# Cluster 23

class Hardswish(nn.Module):

    @staticmethod
    def forward(x):
        return x * F.hardtanh(x + 3, 0.0, 6.0) / 6.0

@staticmethod
def forward(x):
    return x * F.hardtanh(x + 3, 0.0, 6.0) / 6.0

