# Cluster 10

class PointTransformerSeg(nn.Module):

    def __init__(self, block, blocks, in_channels=6, num_classes=50, num_shape_classes=None):
        super().__init__()
        self.in_channels = in_channels
        self.num_classes = num_classes
        self.num_shape_classes = num_shape_classes
        self.in_planes, planes = (in_channels, [32, 64, 128, 256, 512])
        fpn_planes, fpnhead_planes, share_planes = (128, 64, 8)
        stride, nsample = ([1, 4, 4, 4, 4], [8, 16, 16, 16, 16])
        self.enc1 = self._make_enc(block, planes[0], blocks[0], share_planes, stride=stride[0], nsample=nsample[0])
        self.enc2 = self._make_enc(block, planes[1], blocks[1], share_planes, stride=stride[1], nsample=nsample[1])
        self.enc3 = self._make_enc(block, planes[2], blocks[2], share_planes, stride=stride[2], nsample=nsample[2])
        self.enc4 = self._make_enc(block, planes[3], blocks[3], share_planes, stride=stride[3], nsample=nsample[3])
        self.enc5 = self._make_enc(block, planes[4], blocks[4], share_planes, stride=stride[4], nsample=nsample[4])
        self.dec5 = self._make_dec(block, planes[4], 1, share_planes, num_shape_classes=num_shape_classes, nsample=nsample[4], is_head=True)
        self.dec4 = self._make_dec(block, planes[3], 1, share_planes, nsample=nsample[3])
        self.dec3 = self._make_dec(block, planes[2], 1, share_planes, nsample=nsample[2])
        self.dec2 = self._make_dec(block, planes[1], 1, share_planes, nsample=nsample[1])
        self.dec1 = self._make_dec(block, planes[0], 1, share_planes, nsample=nsample[0])
        self.cls = nn.Sequential(nn.Linear(planes[0], planes[0]), nn.BatchNorm1d(planes[0]), nn.ReLU(inplace=True), nn.Linear(planes[0], num_classes))

    def _make_enc(self, block, planes, blocks, share_planes=8, stride=1, nsample=16):
        layers = [TransitionDown(self.in_planes, planes * block.expansion, stride, nsample)]
        self.in_planes = planes * block.expansion
        for _ in range(blocks):
            layers.append(block(self.in_planes, self.in_planes, share_planes, nsample=nsample))
        return nn.Sequential(*layers)

    def _make_dec(self, block, planes, blocks, share_planes=8, num_shape_classes=None, nsample=16, is_head=False):
        layers = [TransitionUp(self.in_planes, None if is_head else planes * block.expansion, num_shape_classes)]
        self.in_planes = planes * block.expansion
        for _ in range(blocks):
            layers.append(block(self.in_planes, self.in_planes, share_planes, nsample=nsample))
        return nn.Sequential(*layers)

    def forward(self, input_dict):
        p0 = input_dict['coord']
        x0 = input_dict['feat']
        o0 = input_dict['offset'].int()
        if self.num_shape_classes is not None:
            y = input_dict['cls_token']
        p1, x1, o1 = self.enc1([p0, x0, o0])
        p2, x2, o2 = self.enc2([p1, x1, o1])
        p3, x3, o3 = self.enc3([p2, x2, o2])
        p4, x4, o4 = self.enc4([p3, x3, o3])
        p5, x5, o5 = self.enc5([p4, x4, o4])
        if self.num_shape_classes is not None:
            x5 = self.dec5[1:]([p5, self.dec5[0]([p5, x5, o5], y=y), o5])[1]
        else:
            x5 = self.dec5[1:]([p5, self.dec5[0]([p5, x5, o5]), o5])[1]
        x4 = self.dec4[1:]([p4, self.dec4[0]([p4, x4, o4], [p5, x5, o5]), o4])[1]
        x3 = self.dec3[1:]([p3, self.dec3[0]([p3, x3, o3], [p4, x4, o4]), o3])[1]
        x2 = self.dec2[1:]([p2, self.dec2[0]([p2, x2, o2], [p3, x3, o3]), o2])[1]
        x1 = self.dec1[1:]([p1, self.dec1[0]([p1, x1, o1], [p2, x2, o2]), o1])[1]
        x = self.cls(x1)
        return x

def forward(self, input_dict):
    p0 = input_dict['coord']
    x0 = input_dict['feat']
    o0 = input_dict['offset'].int()
    if self.num_shape_classes is not None:
        y = input_dict['cls_token']
    p1, x1, o1 = self.enc1([p0, x0, o0])
    p2, x2, o2 = self.enc2([p1, x1, o1])
    p3, x3, o3 = self.enc3([p2, x2, o2])
    p4, x4, o4 = self.enc4([p3, x3, o3])
    p5, x5, o5 = self.enc5([p4, x4, o4])
    if self.num_shape_classes is not None:
        x5 = self.dec5[1:]([p5, self.dec5[0]([p5, x5, o5], y=y), o5])[1]
    else:
        x5 = self.dec5[1:]([p5, self.dec5[0]([p5, x5, o5]), o5])[1]
    x4 = self.dec4[1:]([p4, self.dec4[0]([p4, x4, o4], [p5, x5, o5]), o4])[1]
    x3 = self.dec3[1:]([p3, self.dec3[0]([p3, x3, o3], [p4, x4, o4]), o3])[1]
    x2 = self.dec2[1:]([p2, self.dec2[0]([p2, x2, o2], [p3, x3, o3]), o2])[1]
    x1 = self.dec1[1:]([p1, self.dec1[0]([p1, x1, o1], [p2, x2, o2]), o1])[1]
    x = self.cls(x1)
    return x

class PointTransformerSeg(nn.Module):

    def __init__(self, block, blocks, in_channels=6, num_classes=13):
        super().__init__()
        self.in_channels = in_channels
        self.in_planes, planes = (in_channels, [32, 64, 128, 256, 512])
        fpn_planes, fpnhead_planes, share_planes = (128, 64, 8)
        stride, nsample = ([1, 4, 4, 4, 4], [8, 16, 16, 16, 16])
        self.enc1 = self._make_enc(block, planes[0], blocks[0], share_planes, stride=stride[0], nsample=nsample[0])
        self.enc2 = self._make_enc(block, planes[1], blocks[1], share_planes, stride=stride[1], nsample=nsample[1])
        self.enc3 = self._make_enc(block, planes[2], blocks[2], share_planes, stride=stride[2], nsample=nsample[2])
        self.enc4 = self._make_enc(block, planes[3], blocks[3], share_planes, stride=stride[3], nsample=nsample[3])
        self.enc5 = self._make_enc(block, planes[4], blocks[4], share_planes, stride=stride[4], nsample=nsample[4])
        self.dec5 = self._make_dec(block, planes[4], 1, share_planes, nsample=nsample[4], is_head=True)
        self.dec4 = self._make_dec(block, planes[3], 1, share_planes, nsample=nsample[3])
        self.dec3 = self._make_dec(block, planes[2], 1, share_planes, nsample=nsample[2])
        self.dec2 = self._make_dec(block, planes[1], 1, share_planes, nsample=nsample[1])
        self.dec1 = self._make_dec(block, planes[0], 1, share_planes, nsample=nsample[0])
        self.cls = nn.Sequential(nn.Linear(planes[0], planes[0]), nn.BatchNorm1d(planes[0]), nn.ReLU(inplace=True), nn.Linear(planes[0], num_classes))

    def _make_enc(self, block, planes, blocks, share_planes=8, stride=1, nsample=16):
        layers = [TransitionDown(self.in_planes, planes * block.expansion, stride, nsample)]
        self.in_planes = planes * block.expansion
        for _ in range(blocks):
            layers.append(block(self.in_planes, self.in_planes, share_planes, nsample=nsample))
        return nn.Sequential(*layers)

    def _make_dec(self, block, planes, blocks, share_planes=8, nsample=16, is_head=False):
        layers = [TransitionUp(self.in_planes, None if is_head else planes * block.expansion)]
        self.in_planes = planes * block.expansion
        for _ in range(blocks):
            layers.append(block(self.in_planes, self.in_planes, share_planes, nsample=nsample))
        return nn.Sequential(*layers)

    def forward(self, input_dict):
        p0 = input_dict['coord']
        x0 = input_dict['feat']
        o0 = input_dict['offset'].int()
        p1, x1, o1 = self.enc1([p0, x0, o0])
        p2, x2, o2 = self.enc2([p1, x1, o1])
        p3, x3, o3 = self.enc3([p2, x2, o2])
        p4, x4, o4 = self.enc4([p3, x3, o3])
        p5, x5, o5 = self.enc5([p4, x4, o4])
        x5 = self.dec5[1:]([p5, self.dec5[0]([p5, x5, o5]), o5])[1]
        x4 = self.dec4[1:]([p4, self.dec4[0]([p4, x4, o4], [p5, x5, o5]), o4])[1]
        x3 = self.dec3[1:]([p3, self.dec3[0]([p3, x3, o3], [p4, x4, o4]), o3])[1]
        x2 = self.dec2[1:]([p2, self.dec2[0]([p2, x2, o2], [p3, x3, o3]), o2])[1]
        x1 = self.dec1[1:]([p1, self.dec1[0]([p1, x1, o1], [p2, x2, o2]), o1])[1]
        x = self.cls(x1)
        return x

def forward(self, input_dict):
    p0 = input_dict['coord']
    x0 = input_dict['feat']
    o0 = input_dict['offset'].int()
    p1, x1, o1 = self.enc1([p0, x0, o0])
    p2, x2, o2 = self.enc2([p1, x1, o1])
    p3, x3, o3 = self.enc3([p2, x2, o2])
    p4, x4, o4 = self.enc4([p3, x3, o3])
    p5, x5, o5 = self.enc5([p4, x4, o4])
    x5 = self.dec5[1:]([p5, self.dec5[0]([p5, x5, o5]), o5])[1]
    x4 = self.dec4[1:]([p4, self.dec4[0]([p4, x4, o4], [p5, x5, o5]), o4])[1]
    x3 = self.dec3[1:]([p3, self.dec3[0]([p3, x3, o3], [p4, x4, o4]), o3])[1]
    x2 = self.dec2[1:]([p2, self.dec2[0]([p2, x2, o2], [p3, x3, o3]), o2])[1]
    x1 = self.dec1[1:]([p1, self.dec1[0]([p1, x1, o1], [p2, x2, o2]), o1])[1]
    x = self.cls(x1)
    return x

class PointTransformerCls(nn.Module):

    def __init__(self, block, blocks, in_channels=6, num_classes=40):
        super().__init__()
        self.in_channels = in_channels
        self.in_planes, planes = (in_channels, [32, 64, 128, 256, 512])
        fpn_planes, fpnhead_planes, share_planes = (128, 64, 8)
        stride, nsample = ([1, 4, 4, 4, 4], [8, 16, 16, 16, 16])
        self.enc1 = self._make_enc(block, planes[0], blocks[0], share_planes, stride=stride[0], nsample=nsample[0])
        self.enc2 = self._make_enc(block, planes[1], blocks[1], share_planes, stride=stride[1], nsample=nsample[1])
        self.enc3 = self._make_enc(block, planes[2], blocks[2], share_planes, stride=stride[2], nsample=nsample[2])
        self.enc4 = self._make_enc(block, planes[3], blocks[3], share_planes, stride=stride[3], nsample=nsample[3])
        self.enc5 = self._make_enc(block, planes[4], blocks[4], share_planes, stride=stride[4], nsample=nsample[4])
        self.cls = nn.Sequential(nn.Linear(planes[4], 256), nn.BatchNorm1d(256), nn.ReLU(inplace=True), nn.Dropout(p=0.5), nn.Linear(256, 128), nn.BatchNorm1d(128), nn.ReLU(inplace=True), nn.Dropout(p=0.5), nn.Linear(128, num_classes))

    def _make_enc(self, block, planes, blocks, share_planes=8, stride=1, nsample=16):
        layers = [TransitionDown(self.in_planes, planes * block.expansion, stride, nsample)]
        self.in_planes = planes * block.expansion
        for _ in range(1, blocks):
            layers.append(block(self.in_planes, self.in_planes, share_planes, nsample=nsample))
        return nn.Sequential(*layers)

    def forward(self, input_dict):
        p0 = input_dict['coord']
        x0 = input_dict['feat']
        o0 = input_dict['offset'].int()
        x0 = p0 if self.in_channels == 3 else torch.cat((p0, x0), 1)
        p1, x1, o1 = self.enc1([p0, x0, o0])
        p2, x2, o2 = self.enc2([p1, x1, o1])
        p3, x3, o3 = self.enc3([p2, x2, o2])
        p4, x4, o4 = self.enc4([p3, x3, o3])
        p5, x5, o5 = self.enc5([p4, x4, o4])
        x = []
        for i in range(o5.shape[0]):
            if i == 0:
                s_i, e_i, cnt = (0, o5[0], o5[0])
            else:
                s_i, e_i, cnt = (o5[i - 1], o5[i], o5[i] - o5[i - 1])
            x_b = x5[s_i:e_i, :].sum(0, True) / cnt
            x.append(x_b)
        x = torch.cat(x, 0)
        x = self.cls(x)
        return x

def forward(self, input_dict):
    p0 = input_dict['coord']
    x0 = input_dict['feat']
    o0 = input_dict['offset'].int()
    x0 = p0 if self.in_channels == 3 else torch.cat((p0, x0), 1)
    p1, x1, o1 = self.enc1([p0, x0, o0])
    p2, x2, o2 = self.enc2([p1, x1, o1])
    p3, x3, o3 = self.enc3([p2, x2, o2])
    p4, x4, o4 = self.enc4([p3, x3, o3])
    p5, x5, o5 = self.enc5([p4, x4, o4])
    x = []
    for i in range(o5.shape[0]):
        if i == 0:
            s_i, e_i, cnt = (0, o5[0], o5[0])
        else:
            s_i, e_i, cnt = (o5[i - 1], o5[i], o5[i] - o5[i - 1])
        x_b = x5[s_i:e_i, :].sum(0, True) / cnt
        x.append(x_b)
    x = torch.cat(x, 0)
    x = self.cls(x)
    return x

