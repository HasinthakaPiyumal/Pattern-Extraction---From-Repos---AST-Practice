# Cluster 14

class LightGCN_plus(BaseModel):

    def __init__(self, data_handler):
        super(LightGCN_plus, self).__init__(data_handler)
        self.adj = data_handler.torch_adj
        self.keep_rate = configs['model']['keep_rate']
        self.user_embeds = nn.Parameter(init(t.empty(self.user_num, self.embedding_size)))
        self.item_embeds = nn.Parameter(init(t.empty(self.item_num, self.embedding_size)))
        self.edge_dropper = SpAdjEdgeDrop()
        self.final_embeds = None
        self.is_training = False
        self.layer_num = self.hyper_config['layer_num']
        self.reg_weight = self.hyper_config['reg_weight']
        self.kd_weight = self.hyper_config['kd_weight']
        self.kd_temperature = self.hyper_config['kd_temperature']
        self.usrprf_embeds = t.tensor(configs['usrprf_embeds']).float().cuda()
        self.itmprf_embeds = t.tensor(configs['itmprf_embeds']).float().cuda()
        self.mlp = nn.Sequential(nn.Linear(self.usrprf_embeds.shape[1], (self.usrprf_embeds.shape[1] + self.embedding_size) // 2), nn.LeakyReLU(), nn.Linear((self.usrprf_embeds.shape[1] + self.embedding_size) // 2, self.embedding_size))
        self._init_weight()

    def _init_weight(self):
        for m in self.mlp:
            if isinstance(m, nn.Linear):
                init(m.weight)

    def _propagate(self, adj, embeds):
        return t.spmm(adj, embeds)

    def forward(self, adj=None, keep_rate=1.0):
        if adj is None:
            adj = self.adj
        if not self.is_training and self.final_embeds is not None:
            return (self.final_embeds[:self.user_num], self.final_embeds[self.user_num:])
        embeds = t.concat([self.user_embeds, self.item_embeds], axis=0)
        embeds_list = [embeds]
        if self.is_training:
            adj = self.edge_dropper(adj, keep_rate)
        for i in range(self.layer_num):
            embeds = self._propagate(adj, embeds_list[-1])
            embeds_list.append(embeds)
        embeds = sum(embeds_list)
        self.final_embeds = embeds
        return (embeds[:self.user_num], embeds[self.user_num:])

    def _pick_embeds(self, user_embeds, item_embeds, batch_data):
        ancs, poss, negs = batch_data
        anc_embeds = user_embeds[ancs]
        pos_embeds = item_embeds[poss]
        neg_embeds = item_embeds[negs]
        return (anc_embeds, pos_embeds, neg_embeds)

    def cal_loss(self, batch_data):
        self.is_training = True
        user_embeds, item_embeds = self.forward(self.adj, self.keep_rate)
        anc_embeds, pos_embeds, neg_embeds = self._pick_embeds(user_embeds, item_embeds, batch_data)
        usrprf_embeds = self.mlp(self.usrprf_embeds)
        itmprf_embeds = self.mlp(self.itmprf_embeds)
        ancprf_embeds, posprf_embeds, negprf_embeds = self._pick_embeds(usrprf_embeds, itmprf_embeds, batch_data)
        bpr_loss = cal_bpr_loss(anc_embeds, pos_embeds, neg_embeds) / anc_embeds.shape[0]
        reg_loss = self.reg_weight * reg_params(self)
        kd_loss = cal_infonce_loss(anc_embeds, ancprf_embeds, usrprf_embeds, self.kd_temperature) + cal_infonce_loss(pos_embeds, posprf_embeds, posprf_embeds, self.kd_temperature) + cal_infonce_loss(neg_embeds, negprf_embeds, negprf_embeds, self.kd_temperature)
        kd_loss /= anc_embeds.shape[0]
        kd_loss *= self.kd_weight
        loss = bpr_loss + reg_loss + kd_loss
        losses = {'bpr_loss': bpr_loss, 'reg_loss': reg_loss, 'kd_loss': kd_loss}
        return (loss, losses)

    def full_predict(self, batch_data):
        user_embeds, item_embeds = self.forward(self.adj, 1.0)
        self.is_training = False
        pck_users, train_mask = batch_data
        pck_users = pck_users.long()
        pck_user_embeds = user_embeds[pck_users]
        full_preds = pck_user_embeds @ item_embeds.T
        full_preds = self._mask_predict(full_preds, train_mask)
        return full_preds

def _propagate(self, adj, embeds):
    return t.spmm(adj, embeds)

class LightGCN(BaseModel):

    def __init__(self, data_handler):
        super(LightGCN, self).__init__(data_handler)
        self.adj = data_handler.torch_adj
        self.keep_rate = configs['model']['keep_rate']
        self.user_embeds = nn.Parameter(init(t.empty(self.user_num, self.embedding_size)))
        self.item_embeds = nn.Parameter(init(t.empty(self.item_num, self.embedding_size)))
        self.edge_dropper = SpAdjEdgeDrop()
        self.final_embeds = None
        self.is_training = False
        self.layer_num = self.hyper_config['layer_num']
        self.reg_weight = self.hyper_config['reg_weight']

    def _propagate(self, adj, embeds):
        return t.spmm(adj, embeds)

    def forward(self, adj=None, keep_rate=1.0):
        if adj is None:
            adj = self.adj
        if not self.is_training and self.final_embeds is not None:
            return (self.final_embeds[:self.user_num], self.final_embeds[self.user_num:])
        embeds = t.concat([self.user_embeds, self.item_embeds], axis=0)
        embeds_list = [embeds]
        if self.is_training:
            adj = self.edge_dropper(adj, keep_rate)
        for i in range(self.layer_num):
            embeds = self._propagate(adj, embeds_list[-1])
            embeds_list.append(embeds)
        embeds = sum(embeds_list)
        self.final_embeds = embeds
        return (embeds[:self.user_num], embeds[self.user_num:])

    def cal_loss(self, batch_data):
        self.is_training = True
        user_embeds, item_embeds = self.forward(self.adj, self.keep_rate)
        ancs, poss, negs = batch_data
        anc_embeds = user_embeds[ancs]
        pos_embeds = item_embeds[poss]
        neg_embeds = item_embeds[negs]
        bpr_loss = cal_bpr_loss(anc_embeds, pos_embeds, neg_embeds) / anc_embeds.shape[0]
        reg_loss = self.reg_weight * reg_params(self)
        loss = bpr_loss + reg_loss
        losses = {'bpr_loss': bpr_loss, 'reg_loss': reg_loss}
        return (loss, losses)

    def full_predict(self, batch_data):
        user_embeds, item_embeds = self.forward(self.adj, 1.0)
        self.is_training = False
        pck_users, train_mask = batch_data
        pck_users = pck_users.long()
        pck_user_embeds = user_embeds[pck_users]
        full_preds = pck_user_embeds @ item_embeds.T
        full_preds = self._mask_predict(full_preds, train_mask)
        return full_preds

def _propagate(self, adj, embeds):
    return t.spmm(adj, embeds)

class LightGCN_gene(BaseModel):

    def __init__(self, data_handler):
        super(LightGCN_gene, self).__init__(data_handler)
        self.adj = data_handler.torch_adj
        self.keep_rate = configs['model']['keep_rate']
        self.user_embeds = nn.Parameter(init(t.empty(self.user_num, self.embedding_size)))
        self.item_embeds = nn.Parameter(init(t.empty(self.item_num, self.embedding_size)))
        self.edge_dropper = SpAdjEdgeDrop()
        self.final_embeds = None
        self.is_training = False
        self.layer_num = self.hyper_config['layer_num']
        self.reg_weight = self.hyper_config['reg_weight']
        self.mask_ratio = self.hyper_config['mask_ratio']
        self.recon_weight = self.hyper_config['recon_weight']
        self.re_temperature = self.hyper_config['re_temperature']
        usrprf_embeds = t.tensor(configs['usrprf_embeds']).float().cuda()
        itmprf_embeds = t.tensor(configs['itmprf_embeds']).float().cuda()
        self.prf_embeds = t.concat([usrprf_embeds, itmprf_embeds], dim=0)
        self.masker = NodeMask(self.mask_ratio, self.embedding_size)
        self.mlp = nn.Sequential(nn.Linear(self.embedding_size, (self.prf_embeds.shape[1] + self.embedding_size) // 2), nn.LeakyReLU(), nn.Linear((self.prf_embeds.shape[1] + self.embedding_size) // 2, self.prf_embeds.shape[1]))
        self._init_weight()

    def _init_weight(self):
        for m in self.mlp:
            if isinstance(m, nn.Linear):
                init(m.weight)

    def _propagate(self, adj, embeds):
        return t.spmm(adj, embeds)

    def _mask(self):
        embeds = t.concat([self.user_embeds, self.item_embeds], axis=0)
        masked_embeds, seeds = self.masker(embeds)
        return (masked_embeds[:self.user_num], masked_embeds[self.user_num:], seeds)

    def forward(self, adj=None, keep_rate=1.0, masked_user_embeds=None, masked_item_embeds=None):
        if adj is None:
            adj = self.adj
        if not self.is_training and self.final_embeds is not None:
            return (self.final_embeds[:self.user_num], self.final_embeds[self.user_num:])
        if masked_user_embeds is None or masked_item_embeds is None:
            embeds = t.concat([self.user_embeds, self.item_embeds], axis=0)
        else:
            embeds = t.concat([masked_user_embeds, masked_item_embeds], axis=0)
        embeds_list = [embeds]
        if self.is_training:
            adj = self.edge_dropper(adj, keep_rate)
        for i in range(self.layer_num):
            embeds = self._propagate(adj, embeds_list[-1])
            embeds_list.append(embeds)
        embeds = sum(embeds_list)
        self.final_embeds = embeds
        return (embeds[:self.user_num], embeds[self.user_num:])

    def _pick_embeds(self, user_embeds, item_embeds, batch_data):
        ancs, poss, negs = batch_data
        anc_embeds = user_embeds[ancs]
        pos_embeds = item_embeds[poss]
        neg_embeds = item_embeds[negs]
        return (anc_embeds, pos_embeds, neg_embeds)

    def _reconstruction(self, embeds, seeds):
        enc_embeds = embeds[seeds]
        prf_embeds = self.prf_embeds[seeds]
        enc_embeds = self.mlp(enc_embeds)
        recon_loss = ssl_con_loss(enc_embeds, prf_embeds, self.re_temperature)
        return recon_loss

    def cal_loss(self, batch_data):
        self.is_training = True
        masked_user_embeds, masked_item_embeds, seeds = self._mask()
        user_embeds, item_embeds = self.forward(self.adj, self.keep_rate, masked_user_embeds, masked_item_embeds)
        ancs, poss, negs = batch_data
        anc_embeds = user_embeds[ancs]
        pos_embeds = item_embeds[poss]
        neg_embeds = item_embeds[negs]
        bpr_loss = cal_bpr_loss(anc_embeds, pos_embeds, neg_embeds) / anc_embeds.shape[0]
        reg_loss = self.reg_weight * reg_params(self)
        recon_loss = self.recon_weight * self._reconstruction(t.concat([user_embeds, item_embeds], axis=0), seeds)
        loss = bpr_loss + reg_loss + recon_loss
        losses = {'bpr_loss': bpr_loss, 'reg_loss': reg_loss, 'recon_loss': recon_loss}
        return (loss, losses)

    def full_predict(self, batch_data):
        user_embeds, item_embeds = self.forward(self.adj, 1.0)
        self.is_training = False
        pck_users, train_mask = batch_data
        pck_users = pck_users.long()
        pck_user_embeds = user_embeds[pck_users]
        full_preds = pck_user_embeds @ item_embeds.T
        full_preds = self._mask_predict(full_preds, train_mask)
        return full_preds

def _propagate(self, adj, embeds):
    return t.spmm(adj, embeds)

class GCNLayer(nn.Module):

    def __init__(self):
        super(GCNLayer, self).__init__()

    def forward(self, adj, embeds):
        return t.spmm(adj, embeds)

def forward(self, adj, embeds):
    return t.spmm(adj, embeds)

class LocalGraph(nn.Module):

    def __init__(self):
        super(LocalGraph, self).__init__()
        self.seed_num = configs['model']['seed_num']

    def makeNoise(self, scores):
        noise = t.rand(scores.shape).cuda()
        noise[noise == 0] = 1e-08
        noise = -t.log(-t.log(noise))
        return t.log(scores) + noise

    def forward(self, allOneAdj, embeds):
        order = t.sparse.sum(allOneAdj, dim=-1).to_dense().view([-1, 1])
        fstEmbeds = t.spmm(allOneAdj, embeds) - embeds
        fstNum = order
        scdEmbeds = t.spmm(allOneAdj, fstEmbeds) - fstEmbeds - order * embeds
        scdNum = t.spmm(allOneAdj, fstNum) - fstNum - order
        subgraphEmbeds = (fstEmbeds + scdEmbeds) / (fstNum + scdNum + 1e-08)
        subgraphEmbeds = F.normalize(subgraphEmbeds, p=2)
        embeds = F.normalize(embeds, p=2)
        scores = t.sigmoid(t.sum(subgraphEmbeds * embeds, dim=-1))
        scores = self.makeNoise(scores)
        _, seeds = t.topk(scores, self.seed_num)
        return (scores, seeds)

def forward(self, allOneAdj, embeds):
    order = t.sparse.sum(allOneAdj, dim=-1).to_dense().view([-1, 1])
    fstEmbeds = t.spmm(allOneAdj, embeds) - embeds
    fstNum = order
    scdEmbeds = t.spmm(allOneAdj, fstEmbeds) - fstEmbeds - order * embeds
    scdNum = t.spmm(allOneAdj, fstNum) - fstNum - order
    subgraphEmbeds = (fstEmbeds + scdEmbeds) / (fstNum + scdNum + 1e-08)
    subgraphEmbeds = F.normalize(subgraphEmbeds, p=2)
    embeds = F.normalize(embeds, p=2)
    scores = t.sigmoid(t.sum(subgraphEmbeds * embeds, dim=-1))
    scores = self.makeNoise(scores)
    _, seeds = t.topk(scores, self.seed_num)
    return (scores, seeds)

class GCNLayer(nn.Module):

    def __init__(self, latdim):
        super(GCNLayer, self).__init__()
        self.W = nn.Parameter(init(t.empty(latdim, latdim)))

    def forward(self, adj, embeds):
        return t.spmm(adj, embeds)

def forward(self, adj, embeds):
    return t.spmm(adj, embeds)

class GCNLayer(nn.Module):

    def __init__(self, latdim):
        super(GCNLayer, self).__init__()
        self.W = nn.Parameter(init(t.empty(latdim, latdim)))

    def forward(self, adj, embeds):
        return t.spmm(adj, embeds)

def forward(self, adj, embeds):
    return t.spmm(adj, embeds)

class GCNLayer(nn.Module):

    def __init__(self):
        super(GCNLayer, self).__init__()

    def forward(self, adj, embeds):
        return t.spmm(adj, embeds)

def forward(self, adj, embeds):
    return t.spmm(adj, embeds)

class LocalGraph(nn.Module):

    def __init__(self):
        super(LocalGraph, self).__init__()
        self.seed_num = configs['model']['seed_num']

    def makeNoise(self, scores):
        noise = t.rand(scores.shape).cuda()
        noise[noise == 0] = 1e-08
        noise = -t.log(-t.log(noise))
        return t.log(scores) + noise

    def forward(self, allOneAdj, embeds):
        order = t.sparse.sum(allOneAdj, dim=-1).to_dense().view([-1, 1])
        fstEmbeds = t.spmm(allOneAdj, embeds) - embeds
        fstNum = order
        scdEmbeds = t.spmm(allOneAdj, fstEmbeds) - fstEmbeds - order * embeds
        scdNum = t.spmm(allOneAdj, fstNum) - fstNum - order
        subgraphEmbeds = (fstEmbeds + scdEmbeds) / (fstNum + scdNum + 1e-08)
        subgraphEmbeds = F.normalize(subgraphEmbeds, p=2)
        embeds = F.normalize(embeds, p=2)
        scores = t.sigmoid(t.sum(subgraphEmbeds * embeds, dim=-1))
        scores = self.makeNoise(scores)
        _, seeds = t.topk(scores, self.seed_num)
        return (scores, seeds)

def forward(self, allOneAdj, embeds):
    order = t.sparse.sum(allOneAdj, dim=-1).to_dense().view([-1, 1])
    fstEmbeds = t.spmm(allOneAdj, embeds) - embeds
    fstNum = order
    scdEmbeds = t.spmm(allOneAdj, fstEmbeds) - fstEmbeds - order * embeds
    scdNum = t.spmm(allOneAdj, fstNum) - fstNum - order
    subgraphEmbeds = (fstEmbeds + scdEmbeds) / (fstNum + scdNum + 1e-08)
    subgraphEmbeds = F.normalize(subgraphEmbeds, p=2)
    embeds = F.normalize(embeds, p=2)
    scores = t.sigmoid(t.sum(subgraphEmbeds * embeds, dim=-1))
    scores = self.makeNoise(scores)
    _, seeds = t.topk(scores, self.seed_num)
    return (scores, seeds)

class GCNLayer(nn.Module):

    def __init__(self):
        super(GCNLayer, self).__init__()

    def forward(self, adj, embeds):
        return t.spmm(adj, embeds)

def forward(self, adj, embeds):
    return t.spmm(adj, embeds)

class LocalGraph(nn.Module):

    def __init__(self):
        super(LocalGraph, self).__init__()
        self.seed_num = configs['model']['seed_num']

    def makeNoise(self, scores):
        noise = t.rand(scores.shape).cuda()
        noise[noise == 0] = 1e-08
        noise = -t.log(-t.log(noise))
        return t.log(scores) + noise

    def forward(self, allOneAdj, embeds):
        order = t.sparse.sum(allOneAdj, dim=-1).to_dense().view([-1, 1])
        fstEmbeds = t.spmm(allOneAdj, embeds) - embeds
        fstNum = order
        scdEmbeds = t.spmm(allOneAdj, fstEmbeds) - fstEmbeds - order * embeds
        scdNum = t.spmm(allOneAdj, fstNum) - fstNum - order
        subgraphEmbeds = (fstEmbeds + scdEmbeds) / (fstNum + scdNum + 1e-08)
        subgraphEmbeds = F.normalize(subgraphEmbeds, p=2)
        embeds = F.normalize(embeds, p=2)
        scores = t.sigmoid(t.sum(subgraphEmbeds * embeds, dim=-1))
        scores = self.makeNoise(scores)
        _, seeds = t.topk(scores, self.seed_num)
        return (scores, seeds)

def forward(self, allOneAdj, embeds):
    order = t.sparse.sum(allOneAdj, dim=-1).to_dense().view([-1, 1])
    fstEmbeds = t.spmm(allOneAdj, embeds) - embeds
    fstNum = order
    scdEmbeds = t.spmm(allOneAdj, fstEmbeds) - fstEmbeds - order * embeds
    scdNum = t.spmm(allOneAdj, fstNum) - fstNum - order
    subgraphEmbeds = (fstEmbeds + scdEmbeds) / (fstNum + scdNum + 1e-08)
    subgraphEmbeds = F.normalize(subgraphEmbeds, p=2)
    embeds = F.normalize(embeds, p=2)
    scores = t.sigmoid(t.sum(subgraphEmbeds * embeds, dim=-1))
    scores = self.makeNoise(scores)
    _, seeds = t.topk(scores, self.seed_num)
    return (scores, seeds)

class GCNLayer(nn.Module):

    def __init__(self, latdim):
        super(GCNLayer, self).__init__()
        self.W = nn.Parameter(init(t.empty(latdim, latdim)))

    def forward(self, adj, embeds):
        return t.spmm(adj, embeds)

def forward(self, adj, embeds):
    return t.spmm(adj, embeds)

