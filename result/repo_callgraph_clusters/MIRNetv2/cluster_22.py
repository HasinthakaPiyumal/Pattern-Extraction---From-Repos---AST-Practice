# Cluster 22

class Down(nn.Module):

    def __init__(self, in_channels, chan_factor, bias=False):
        super(Down, self).__init__()
        self.bot = nn.Sequential(nn.AvgPool2d(2, ceil_mode=True, count_include_pad=False), nn.Conv2d(in_channels, int(in_channels * chan_factor), 1, stride=1, padding=0, bias=bias))

    def forward(self, x):
        return self.bot(x)

def forward(self, x):
    return self.bot(x)

class Up(nn.Module):

    def __init__(self, in_channels, chan_factor, bias=False):
        super(Up, self).__init__()
        self.bot = nn.Sequential(nn.Conv2d(in_channels, int(in_channels // chan_factor), 1, stride=1, padding=0, bias=bias), nn.Upsample(scale_factor=2, mode='bilinear', align_corners=bias))

    def forward(self, x):
        return self.bot(x)

def forward(self, x):
    return self.bot(x)

