# Cluster 87

class HarmAttn(nn.Module):
    """Harmonious Attention (Sec. 3.1)"""

    def __init__(self, in_channels):
        super(HarmAttn, self).__init__()
        self.soft_attn = SoftAttn(in_channels)
        self.hard_attn = HardAttn(in_channels)

    def forward(self, x):
        y_soft_attn = self.soft_attn(x)
        theta = self.hard_attn(x)
        return (y_soft_attn, theta)

def forward(self, x):
    y_soft_attn = self.soft_attn(x)
    theta = self.hard_attn(x)
    return (y_soft_attn, theta)

