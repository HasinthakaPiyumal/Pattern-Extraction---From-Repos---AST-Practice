# Cluster 6

class GroupedVectorAttention(nn.Module):

    def __init__(self, embed_channels, groups, attn_drop_rate=0.0, qkv_bias=True, pe_multiplier=False, pe_bias=True):
        super(GroupedVectorAttention, self).__init__()
        self.embed_channels = embed_channels
        self.groups = groups
        assert embed_channels % groups == 0
        self.attn_drop_rate = attn_drop_rate
        self.qkv_bias = qkv_bias
        self.pe_multiplier = pe_multiplier
        self.pe_bias = pe_bias
        self.linear_q = nn.Sequential(nn.Linear(embed_channels, embed_channels, bias=qkv_bias), PointBatchNorm(embed_channels), nn.ReLU(inplace=True))
        self.linear_k = nn.Sequential(nn.Linear(embed_channels, embed_channels, bias=qkv_bias), PointBatchNorm(embed_channels), nn.ReLU(inplace=True))
        self.linear_v = nn.Linear(embed_channels, embed_channels, bias=qkv_bias)
        if self.pe_multiplier:
            self.linear_p_multiplier = nn.Sequential(nn.Linear(3, embed_channels), PointBatchNorm(embed_channels), nn.ReLU(inplace=True), nn.Linear(embed_channels, embed_channels))
        if self.pe_bias:
            self.linear_p_bias = nn.Sequential(nn.Linear(3, embed_channels), PointBatchNorm(embed_channels), nn.ReLU(inplace=True), nn.Linear(embed_channels, embed_channels))
        self.weight_encoding = nn.Sequential(GroupedLinear(embed_channels, groups, groups), PointBatchNorm(groups), nn.ReLU(inplace=True), nn.Linear(groups, groups))
        self.softmax = nn.Softmax(dim=1)
        self.attn_drop = nn.Dropout(attn_drop_rate)

    def forward(self, feat, coord, reference_index):
        query, key, value = (self.linear_q(feat), self.linear_k(feat), self.linear_v(feat))
        key = pointops.grouping(reference_index, key, coord, with_xyz=True)
        value = pointops.grouping(reference_index, value, coord, with_xyz=False)
        pos, key = (key[:, :, 0:3], key[:, :, 3:])
        relation_qk = key - query.unsqueeze(1)
        if self.pe_multiplier:
            pem = self.linear_p_multiplier(pos)
            relation_qk = relation_qk * pem
        if self.pe_bias:
            peb = self.linear_p_bias(pos)
            relation_qk = relation_qk + peb
            value = value + peb
        weight = self.weight_encoding(relation_qk)
        weight = self.attn_drop(self.softmax(weight))
        mask = torch.sign(reference_index + 1)
        weight = torch.einsum('n s g, n s -> n s g', weight, mask)
        value = einops.rearrange(value, 'n ns (g i) -> n ns g i', g=self.groups)
        feat = torch.einsum('n s g i, n s g -> n g i', value, weight)
        feat = einops.rearrange(feat, 'n g i -> n (g i)')
        return feat

def forward(self, feat, coord, reference_index):
    query, key, value = (self.linear_q(feat), self.linear_k(feat), self.linear_v(feat))
    key = pointops.grouping(reference_index, key, coord, with_xyz=True)
    value = pointops.grouping(reference_index, value, coord, with_xyz=False)
    pos, key = (key[:, :, 0:3], key[:, :, 3:])
    relation_qk = key - query.unsqueeze(1)
    if self.pe_multiplier:
        pem = self.linear_p_multiplier(pos)
        relation_qk = relation_qk * pem
    if self.pe_bias:
        peb = self.linear_p_bias(pos)
        relation_qk = relation_qk + peb
        value = value + peb
    weight = self.weight_encoding(relation_qk)
    weight = self.attn_drop(self.softmax(weight))
    mask = torch.sign(reference_index + 1)
    weight = torch.einsum('n s g, n s -> n s g', weight, mask)
    value = einops.rearrange(value, 'n ns (g i) -> n ns g i', g=self.groups)
    feat = torch.einsum('n s g i, n s g -> n g i', value, weight)
    feat = einops.rearrange(feat, 'n g i -> n (g i)')
    return feat

class GroupedVectorAttention(nn.Module):

    def __init__(self, embed_channels, groups, attn_drop_rate=0.0, qkv_bias=True, pe_multiplier=False, pe_bias=True):
        super(GroupedVectorAttention, self).__init__()
        self.embed_channels = embed_channels
        self.groups = groups
        assert embed_channels % groups == 0
        self.attn_drop_rate = attn_drop_rate
        self.qkv_bias = qkv_bias
        self.pe_multiplier = pe_multiplier
        self.pe_bias = pe_bias
        self.linear_q = nn.Sequential(nn.Linear(embed_channels, embed_channels, bias=qkv_bias), PointBatchNorm(embed_channels), nn.ReLU(inplace=True))
        self.linear_k = nn.Sequential(nn.Linear(embed_channels, embed_channels, bias=qkv_bias), PointBatchNorm(embed_channels), nn.ReLU(inplace=True))
        self.linear_v = nn.Linear(embed_channels, embed_channels, bias=qkv_bias)
        if self.pe_multiplier:
            self.linear_p_multiplier = nn.Sequential(nn.Linear(3, embed_channels), PointBatchNorm(embed_channels), nn.ReLU(inplace=True), nn.Linear(embed_channels, embed_channels))
        if self.pe_bias:
            self.linear_p_bias = nn.Sequential(nn.Linear(3, embed_channels), PointBatchNorm(embed_channels), nn.ReLU(inplace=True), nn.Linear(embed_channels, embed_channels))
        self.weight_encoding = nn.Sequential(nn.Linear(embed_channels, groups), PointBatchNorm(groups), nn.ReLU(inplace=True), nn.Linear(groups, groups))
        self.softmax = nn.Softmax(dim=1)
        self.attn_drop = nn.Dropout(attn_drop_rate)

    def forward(self, feat, coord, reference_index):
        query, key, value = (self.linear_q(feat), self.linear_k(feat), self.linear_v(feat))
        key = pointops.grouping(reference_index, key, coord, with_xyz=True)
        value = pointops.grouping(reference_index, value, coord, with_xyz=False)
        pos, key = (key[:, :, 0:3], key[:, :, 3:])
        relation_qk = key - query.unsqueeze(1)
        if self.pe_multiplier:
            pem = self.linear_p_multiplier(pos)
            relation_qk = relation_qk * pem
        if self.pe_bias:
            peb = self.linear_p_bias(pos)
            relation_qk = relation_qk + peb
            value = value + peb
        weight = self.weight_encoding(relation_qk)
        weight = self.attn_drop(self.softmax(weight))
        mask = torch.sign(reference_index + 1)
        weight = torch.einsum('n s g, n s -> n s g', weight, mask)
        value = einops.rearrange(value, 'n ns (g i) -> n ns g i', g=self.groups)
        feat = torch.einsum('n s g i, n s g -> n g i', value, weight)
        feat = einops.rearrange(feat, 'n g i -> n (g i)')
        return feat

def forward(self, feat, coord, reference_index):
    query, key, value = (self.linear_q(feat), self.linear_k(feat), self.linear_v(feat))
    key = pointops.grouping(reference_index, key, coord, with_xyz=True)
    value = pointops.grouping(reference_index, value, coord, with_xyz=False)
    pos, key = (key[:, :, 0:3], key[:, :, 3:])
    relation_qk = key - query.unsqueeze(1)
    if self.pe_multiplier:
        pem = self.linear_p_multiplier(pos)
        relation_qk = relation_qk * pem
    if self.pe_bias:
        peb = self.linear_p_bias(pos)
        relation_qk = relation_qk + peb
        value = value + peb
    weight = self.weight_encoding(relation_qk)
    weight = self.attn_drop(self.softmax(weight))
    mask = torch.sign(reference_index + 1)
    weight = torch.einsum('n s g, n s -> n s g', weight, mask)
    value = einops.rearrange(value, 'n ns (g i) -> n ns g i', g=self.groups)
    feat = torch.einsum('n s g i, n s g -> n g i', value, weight)
    feat = einops.rearrange(feat, 'n g i -> n (g i)')
    return feat

class PointTransformerLayer(nn.Module):

    def __init__(self, in_planes, out_planes, share_planes=8, nsample=16):
        super().__init__()
        self.mid_planes = mid_planes = out_planes // 1
        self.out_planes = out_planes
        self.share_planes = share_planes
        self.nsample = nsample
        self.linear_q = nn.Linear(in_planes, mid_planes)
        self.linear_k = nn.Linear(in_planes, mid_planes)
        self.linear_v = nn.Linear(in_planes, out_planes)
        self.linear_p = nn.Sequential(nn.Linear(3, 3), LayerNorm1d(3), nn.ReLU(inplace=True), nn.Linear(3, out_planes))
        self.linear_w = nn.Sequential(LayerNorm1d(mid_planes), nn.ReLU(inplace=True), nn.Linear(mid_planes, out_planes // share_planes), LayerNorm1d(out_planes // share_planes), nn.ReLU(inplace=True), nn.Linear(out_planes // share_planes, out_planes // share_planes))
        self.softmax = nn.Softmax(dim=1)

    def forward(self, pxo) -> torch.Tensor:
        p, x, o = pxo
        x_q, x_k, x_v = (self.linear_q(x), self.linear_k(x), self.linear_v(x))
        x_k, idx = pointops.knn_query_and_group(x_k, p, o, new_xyz=p, new_offset=o, nsample=self.nsample, with_xyz=True)
        x_v, _ = pointops.knn_query_and_group(x_v, p, o, new_xyz=p, new_offset=o, idx=idx, nsample=self.nsample, with_xyz=False)
        p_r, x_k = (x_k[:, :, 0:3], x_k[:, :, 3:])
        p_r = self.linear_p(p_r)
        r_qk = x_k - x_q.unsqueeze(1) + einops.reduce(p_r, 'n ns (i j) -> n ns j', reduction='sum', j=self.mid_planes)
        w = self.linear_w(r_qk)
        w = self.softmax(w)
        x = torch.einsum('n t s i, n t i -> n s i', einops.rearrange(x_v + p_r, 'n ns (s i) -> n ns s i', s=self.share_planes), w)
        x = einops.rearrange(x, 'n s i -> n (s i)')
        return x

def forward(self, pxo) -> torch.Tensor:
    p, x, o = pxo
    x_q, x_k, x_v = (self.linear_q(x), self.linear_k(x), self.linear_v(x))
    x_k, idx = pointops.knn_query_and_group(x_k, p, o, new_xyz=p, new_offset=o, nsample=self.nsample, with_xyz=True)
    x_v, _ = pointops.knn_query_and_group(x_v, p, o, new_xyz=p, new_offset=o, idx=idx, nsample=self.nsample, with_xyz=False)
    p_r, x_k = (x_k[:, :, 0:3], x_k[:, :, 3:])
    p_r = self.linear_p(p_r)
    r_qk = x_k - x_q.unsqueeze(1) + einops.reduce(p_r, 'n ns (i j) -> n ns j', reduction='sum', j=self.mid_planes)
    w = self.linear_w(r_qk)
    w = self.softmax(w)
    x = torch.einsum('n t s i, n t i -> n s i', einops.rearrange(x_v + p_r, 'n ns (s i) -> n ns s i', s=self.share_planes), w)
    x = einops.rearrange(x, 'n s i -> n (s i)')
    return x

class PointTransformerLayer(nn.Module):

    def __init__(self, in_planes, out_planes, share_planes=8, nsample=16):
        super().__init__()
        self.mid_planes = mid_planes = out_planes // 1
        self.out_planes = out_planes
        self.share_planes = share_planes
        self.nsample = nsample
        self.linear_q = nn.Linear(in_planes, mid_planes)
        self.linear_k = nn.Linear(in_planes, mid_planes)
        self.linear_v = nn.Linear(in_planes, out_planes)
        self.linear_p = nn.Sequential(nn.Linear(3, 3), LayerNorm1d(3), nn.ReLU(inplace=True), nn.Linear(3, out_planes))
        self.linear_w = nn.Sequential(LayerNorm1d(mid_planes), nn.ReLU(inplace=True), nn.Linear(mid_planes, out_planes // share_planes), LayerNorm1d(out_planes // share_planes), nn.ReLU(inplace=True), nn.Linear(out_planes // share_planes, out_planes // share_planes))
        self.softmax = nn.Softmax(dim=1)

    def forward(self, pxo) -> torch.Tensor:
        p, x, o = pxo
        x_q, x_k, x_v = (self.linear_q(x), self.linear_k(x), self.linear_v(x))
        x_k, idx = pointops.knn_query_and_group(x_k, p, o, new_xyz=p, new_offset=o, nsample=self.nsample, with_xyz=True)
        x_v, _ = pointops.knn_query_and_group(x_v, p, o, new_xyz=p, new_offset=o, idx=idx, nsample=self.nsample, with_xyz=False)
        p_r, x_k = (x_k[:, :, 0:3], x_k[:, :, 3:])
        p_r = self.linear_p(p_r)
        r_qk = x_k - x_q.unsqueeze(1) + einops.reduce(p_r, 'n ns (i j) -> n ns j', reduction='sum', j=self.mid_planes)
        w = self.linear_w(r_qk)
        w = self.softmax(w)
        x = torch.einsum('n t s i, n t i -> n s i', einops.rearrange(x_v + p_r, 'n ns (s i) -> n ns s i', s=self.share_planes), w)
        x = einops.rearrange(x, 'n s i -> n (s i)')
        return x

def forward(self, pxo) -> torch.Tensor:
    p, x, o = pxo
    x_q, x_k, x_v = (self.linear_q(x), self.linear_k(x), self.linear_v(x))
    x_k, idx = pointops.knn_query_and_group(x_k, p, o, new_xyz=p, new_offset=o, nsample=self.nsample, with_xyz=True)
    x_v, _ = pointops.knn_query_and_group(x_v, p, o, new_xyz=p, new_offset=o, idx=idx, nsample=self.nsample, with_xyz=False)
    p_r, x_k = (x_k[:, :, 0:3], x_k[:, :, 3:])
    p_r = self.linear_p(p_r)
    r_qk = x_k - x_q.unsqueeze(1) + einops.reduce(p_r, 'n ns (i j) -> n ns j', reduction='sum', j=self.mid_planes)
    w = self.linear_w(r_qk)
    w = self.softmax(w)
    x = torch.einsum('n t s i, n t i -> n s i', einops.rearrange(x_v + p_r, 'n ns (s i) -> n ns s i', s=self.share_planes), w)
    x = einops.rearrange(x, 'n s i -> n (s i)')
    return x

