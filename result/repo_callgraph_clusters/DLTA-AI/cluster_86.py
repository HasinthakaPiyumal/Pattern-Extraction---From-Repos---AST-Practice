# Cluster 86

class InceptionA(nn.Module):

    def __init__(self, in_channels, out_channels):
        super(InceptionA, self).__init__()
        mid_channels = out_channels // 4
        self.stream1 = nn.Sequential(ConvBlock(in_channels, mid_channels, 1), ConvBlock(mid_channels, mid_channels, 3, p=1))
        self.stream2 = nn.Sequential(ConvBlock(in_channels, mid_channels, 1), ConvBlock(mid_channels, mid_channels, 3, p=1))
        self.stream3 = nn.Sequential(ConvBlock(in_channels, mid_channels, 1), ConvBlock(mid_channels, mid_channels, 3, p=1))
        self.stream4 = nn.Sequential(nn.AvgPool2d(3, stride=1, padding=1), ConvBlock(in_channels, mid_channels, 1))

    def forward(self, x):
        s1 = self.stream1(x)
        s2 = self.stream2(x)
        s3 = self.stream3(x)
        s4 = self.stream4(x)
        y = torch.cat([s1, s2, s3, s4], dim=1)
        return y

def forward(self, x):
    s1 = self.stream1(x)
    s2 = self.stream2(x)
    s3 = self.stream3(x)
    s4 = self.stream4(x)
    y = torch.cat([s1, s2, s3, s4], dim=1)
    return y

class InceptionB(nn.Module):

    def __init__(self, in_channels, out_channels):
        super(InceptionB, self).__init__()
        mid_channels = out_channels // 4
        self.stream1 = nn.Sequential(ConvBlock(in_channels, mid_channels, 1), ConvBlock(mid_channels, mid_channels, 3, s=2, p=1))
        self.stream2 = nn.Sequential(ConvBlock(in_channels, mid_channels, 1), ConvBlock(mid_channels, mid_channels, 3, p=1), ConvBlock(mid_channels, mid_channels, 3, s=2, p=1))
        self.stream3 = nn.Sequential(nn.MaxPool2d(3, stride=2, padding=1), ConvBlock(in_channels, mid_channels * 2, 1))

    def forward(self, x):
        s1 = self.stream1(x)
        s2 = self.stream2(x)
        s3 = self.stream3(x)
        y = torch.cat([s1, s2, s3], dim=1)
        return y

def forward(self, x):
    s1 = self.stream1(x)
    s2 = self.stream2(x)
    s3 = self.stream3(x)
    y = torch.cat([s1, s2, s3], dim=1)
    return y

class MultiScaleA(nn.Module):
    """Multi-scale stream layer A (Sec.3.1)"""

    def __init__(self):
        super(MultiScaleA, self).__init__()
        self.stream1 = nn.Sequential(ConvBlock(96, 96, k=1, s=1, p=0), ConvBlock(96, 24, k=3, s=1, p=1))
        self.stream2 = nn.Sequential(nn.AvgPool2d(kernel_size=3, stride=1, padding=1), ConvBlock(96, 24, k=1, s=1, p=0))
        self.stream3 = ConvBlock(96, 24, k=1, s=1, p=0)
        self.stream4 = nn.Sequential(ConvBlock(96, 16, k=1, s=1, p=0), ConvBlock(16, 24, k=3, s=1, p=1), ConvBlock(24, 24, k=3, s=1, p=1))

    def forward(self, x):
        s1 = self.stream1(x)
        s2 = self.stream2(x)
        s3 = self.stream3(x)
        s4 = self.stream4(x)
        y = torch.cat([s1, s2, s3, s4], dim=1)
        return y

def forward(self, x):
    s1 = self.stream1(x)
    s2 = self.stream2(x)
    s3 = self.stream3(x)
    s4 = self.stream4(x)
    y = torch.cat([s1, s2, s3, s4], dim=1)
    return y

class Reduction(nn.Module):
    """Reduction layer (Sec.3.1)"""

    def __init__(self):
        super(Reduction, self).__init__()
        self.stream1 = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        self.stream2 = ConvBlock(96, 96, k=3, s=2, p=1)
        self.stream3 = nn.Sequential(ConvBlock(96, 48, k=1, s=1, p=0), ConvBlock(48, 56, k=3, s=1, p=1), ConvBlock(56, 64, k=3, s=2, p=1))

    def forward(self, x):
        s1 = self.stream1(x)
        s2 = self.stream2(x)
        s3 = self.stream3(x)
        y = torch.cat([s1, s2, s3], dim=1)
        return y

def forward(self, x):
    s1 = self.stream1(x)
    s2 = self.stream2(x)
    s3 = self.stream3(x)
    y = torch.cat([s1, s2, s3], dim=1)
    return y

class MultiScaleB(nn.Module):
    """Multi-scale stream layer B (Sec.3.1)"""

    def __init__(self):
        super(MultiScaleB, self).__init__()
        self.stream1 = nn.Sequential(nn.AvgPool2d(kernel_size=3, stride=1, padding=1), ConvBlock(256, 256, k=1, s=1, p=0))
        self.stream2 = nn.Sequential(ConvBlock(256, 64, k=1, s=1, p=0), ConvBlock(64, 128, k=(1, 3), s=1, p=(0, 1)), ConvBlock(128, 256, k=(3, 1), s=1, p=(1, 0)))
        self.stream3 = ConvBlock(256, 256, k=1, s=1, p=0)
        self.stream4 = nn.Sequential(ConvBlock(256, 64, k=1, s=1, p=0), ConvBlock(64, 64, k=(1, 3), s=1, p=(0, 1)), ConvBlock(64, 128, k=(3, 1), s=1, p=(1, 0)), ConvBlock(128, 128, k=(1, 3), s=1, p=(0, 1)), ConvBlock(128, 256, k=(3, 1), s=1, p=(1, 0)))

    def forward(self, x):
        s1 = self.stream1(x)
        s2 = self.stream2(x)
        s3 = self.stream3(x)
        s4 = self.stream4(x)
        return (s1, s2, s3, s4)

def forward(self, x):
    s1 = self.stream1(x)
    s2 = self.stream2(x)
    s3 = self.stream3(x)
    s4 = self.stream4(x)
    return (s1, s2, s3, s4)

