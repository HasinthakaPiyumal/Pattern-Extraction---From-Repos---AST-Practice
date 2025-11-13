# Cluster 4

class PairwiseWEpochFlagTrnData(PairwiseTrnData):

    def __init__(self, coomat):
        super(PairwiseWEpochFlagTrnData, self).__init__(coomat)
        self.epoch_flag_counter = -1
        self.epoch_period = configs['model']['epoch_period']

    def __getitem__(self, idx):
        flag = 0
        if self.epoch_flag_counter == -1:
            flag = 1
            self.epoch_flag_counter = 0
        if idx == 0:
            self.epoch_flag_counter += 1
            if self.epoch_flag_counter % self.epoch_period == 0:
                flag = 1
        anc, pos, neg = super(PairwiseWEpochFlagTrnData, self).__getitem__(idx)
        return (anc, pos, neg, flag)

def __init__(self, coomat):
    super(PairwiseWEpochFlagTrnData, self).__init__(coomat)
    self.epoch_flag_counter = -1
    self.epoch_period = configs['model']['epoch_period']

def __getitem__(self, idx):
    flag = 0
    if self.epoch_flag_counter == -1:
        flag = 1
        self.epoch_flag_counter = 0
    if idx == 0:
        self.epoch_flag_counter += 1
        if self.epoch_flag_counter % self.epoch_period == 0:
            flag = 1
    anc, pos, neg = super(PairwiseWEpochFlagTrnData, self).__getitem__(idx)
    return (anc, pos, neg, flag)

class AutoCFTrainer(Trainer):

    def __init__(self, data_handler, logger):
        super(AutoCFTrainer, self).__init__(data_handler, logger)
        self.fix_steps = configs['model']['fix_steps']

    def train_epoch(self, model, epoch_idx):
        train_dataloader = self.data_handler.train_dataloader
        train_dataloader.dataset.sample_negs()
        loss_log_dict = {}
        ep_loss = 0
        steps = len(train_dataloader.dataset) // configs['train']['batch_size']
        model.train()
        for i, tem in tqdm(enumerate(train_dataloader), desc='Training Recommender', total=len(train_dataloader)):
            self.optimizer.zero_grad()
            batch_data = list(map(lambda x: x.long().to(configs['device']), tem))
            if i % self.fix_steps == 0:
                sampScores, seeds = model.sample_subgraphs()
                encoderAdj, decoderAdj = model.mask_subgraphs(seeds)
            loss, loss_dict = model.cal_loss(batch_data, encoderAdj, decoderAdj)
            if i % self.fix_steps == 0:
                localGlobalLoss = -sampScores.mean()
                loss += localGlobalLoss
                loss_dict['infomax_loss'] = localGlobalLoss
            ep_loss += loss.item()
            loss.backward()
            self.optimizer.step()
            for loss_name in loss_dict:
                _loss_val = float(loss_dict[loss_name]) / len(train_dataloader)
                if loss_name not in loss_log_dict:
                    loss_log_dict[loss_name] = _loss_val
                else:
                    loss_log_dict[loss_name] += _loss_val
        if configs['train']['log_loss']:
            self.logger.log_loss(epoch_idx, loss_log_dict)
        else:
            self.logger.log_loss(epoch_idx, loss_log_dict, save_to_log=False)

def __init__(self, data_handler, logger):
    super(AutoCFTrainer, self).__init__(data_handler, logger)
    self.fix_steps = configs['model']['fix_steps']

class SpAdjEdgeDrop(nn.Module):

    def __init__(self):
        super(SpAdjEdgeDrop, self).__init__()

    def forward(self, adj, keep_rate):
        if keep_rate == 1.0:
            return adj
        vals = adj._values()
        idxs = adj._indices()
        edgeNum = vals.size()
        mask = (t.rand(edgeNum) + keep_rate).floor().type(t.bool)
        newVals = vals[mask]
        newIdxs = idxs[:, mask]
        return t.sparse.FloatTensor(newIdxs, newVals, adj.shape)

def __init__(self):
    super(SpAdjEdgeDrop, self).__init__()

class NodeDrop(nn.Module):

    def __init__(self):
        super(NodeDrop, self).__init__()

    def forward(self, embeds, keep_rate):
        if keep_rate == 1.0:
            return embeds
        data_config = configs['data']
        node_num = data_config['user_num'] + data_config['item_num']
        mask = (t.rand(node_num) + keep_rate).floor().view([-1, 1])
        return embeds * mask

def __init__(self):
    super(NodeDrop, self).__init__()

class EdgeDrop(nn.Module):
    """ Drop edges in a graph.
    """

    def __init__(self, resize_val=False):
        super(EdgeDrop, self).__init__()
        self.resize_val = resize_val

    def forward(self, adj, keep_rate):
        """
        :param adj: torch_adj in data_handler
        :param keep_rate: ratio of preserved edges
        :return: adjacency matrix after dropping edges
        """
        if keep_rate == 1.0:
            return adj
        vals = adj._values()
        idxs = adj._indices()
        edgeNum = vals.size()
        mask = (t.rand(edgeNum) + keep_rate).floor().type(t.bool)
        newVals = vals[mask] / (keep_rate if self.resize_val else 1.0)
        newIdxs = idxs[:, mask]
        return t.sparse.FloatTensor(newIdxs, newVals, adj.shape)

def __init__(self, resize_val=False):
    super(EdgeDrop, self).__init__()
    self.resize_val = resize_val

class NodeDrop(nn.Module):
    """ Drop nodes in a graph.
        It is implemented by replace the embeddings of dropped nodes with random embeddings.
    """

    def __init__(self):
        super(NodeDrop, self).__init__()

    def forward(self, embeds, keep_rate):
        """
        :param embeds: the embedding matrix of nodes in the graph
        :param keep_rate: ratio of preserved nodes
        :return: the embeddings matrix after dropping nodes
        """
        if keep_rate == 1.0:
            return embeds
        data_config = configs['data']
        node_num = data_config['user_num'] + data_config['item_num']
        mask = (t.rand(node_num) + keep_rate).floor().view([-1, 1])
        return embeds * mask

def __init__(self):
    super(NodeDrop, self).__init__()

class NodeMask(nn.Module):
    """ Mask nodes with learnable tokens
    """

    def __init__(self, mask_ratio, embedding_size):
        super(NodeMask, self).__init__()
        self.mask_ratio = mask_ratio
        self.mask_token = nn.Parameter(t.zeros(1, embedding_size))

    def forward(self, embeds):
        seeds = np.random.choice(embeds.shape[0], size=max(int(embeds.shape[0] * self.mask_ratio), 1), replace=False)
        seeds = t.LongTensor(seeds).to(configs['device'])
        mask = t.ones(embeds.shape[0]).to(configs['device'])
        mask[seeds] = 0
        mask = mask.view(-1, 1)
        masked_embeds = embeds * mask + self.mask_token * (1.0 - mask)
        return (masked_embeds, seeds)

def __init__(self, mask_ratio, embedding_size):
    super(NodeMask, self).__init__()
    self.mask_ratio = mask_ratio
    self.mask_token = nn.Parameter(t.zeros(1, embedding_size))

class AdaptiveMask(nn.Module):
    """ Adaptively masking edges with learned weight (used in DCCF)
    """

    def __init__(self, head_list, tail_list, matrix_shape):
        """
        :param head_list: list of id about head nodes
        :param tail_list: list of id about tail nodes
        :param matrix_shape: shape of the matrix
        """
        super(AdaptiveMask, self).__init__()
        self.head_list = head_list
        self.tail_list = tail_list
        self.matrix_shape = matrix_shape

    def forward(self, head_embeds, tail_embeds):
        """
        :param head_embeds: embeddings of head nodes
        :param tail_embeds: embeddings of tail nodes
        :return: indices and values (representing a augmented graph in torch_sparse fashion)
        """
        import torch_sparse
        head_embeddings = t.nn.functional.normalize(head_embeds)
        tail_embeddings = t.nn.functional.normalize(tail_embeds)
        edge_alpha = (t.sum(head_embeddings * tail_embeddings, dim=1).view(-1) + 1) / 2
        A_tensor = torch_sparse.SparseTensor(row=self.head_list, col=self.tail_list, value=edge_alpha, sparse_sizes=self.matrix_shape).cuda()
        D_scores_inv = A_tensor.sum(dim=1).pow(-1).nan_to_num(0, 0, 0).view(-1)
        G_indices = t.stack([self.head_list, self.tail_list], dim=0)
        G_values = D_scores_inv[self.head_list] * edge_alpha
        return (G_indices, G_values)

def __init__(self, head_list, tail_list, matrix_shape):
    """
        :param head_list: list of id about head nodes
        :param tail_list: list of id about tail nodes
        :param matrix_shape: shape of the matrix
        """
    super(AdaptiveMask, self).__init__()
    self.head_list = head_list
    self.tail_list = tail_list
    self.matrix_shape = matrix_shape

class SvdDecomposition(nn.Module):
    """ Utilize SVD to decompose matrix (used in LightGCL)
    """

    def __init__(self, svd_q):
        super(SvdDecomposition, self).__init__()
        self.svd_q = svd_q

    def forward(self, adj):
        """
        :param adj: torch sparse matrix
        :return: matrices obtained by SVD decomposition
        """
        svd_u, s, svd_v = t.svd_lowrank(adj, q=self.svd_q)
        u_mul_s = svd_u @ t.diag(s)
        v_mul_s = svd_v @ t.diag(s)
        del s
        return (svd_u.T, svd_v.T, u_mul_s, v_mul_s)

def __init__(self, svd_q):
    super(SvdDecomposition, self).__init__()
    self.svd_q = svd_q

class EmbedDrop(nn.Module):
    """ Drop embeddings by nn.Dropout
    """

    def __init__(self, p=0.2):
        super(EdgeDrop, self).__init__()
        self.dropout = nn.Dropout(p=p)

    def forward(self, embeds):
        """
        :param embeds: embedding matrix
        :return: embedding matrix after dropping
        """
        embeds = self.dropout(embeds)
        return embeds

def __init__(self, p=0.2):
    super(EdgeDrop, self).__init__()
    self.dropout = nn.Dropout(p=p)

class EmbedPerturb(nn.Module):
    """ Perturb embeddings
    """

    def __init__(self, eps):
        super(EmbedPerturb, self).__init__()
        self.eps = eps

    def forward(self, embeds):
        """ Perturbing embeddings with noise
        :param embeds: embedding matrix
        :return: perturbed embedding matrix
        """
        noise = F.normalize(t.rand(embeds.shape).cuda(), p=2) * t.sign(embeds) * self.eps
        embeds = embeds + noise
        return embeds

def __init__(self, eps):
    super(EmbedPerturb, self).__init__()
    self.eps = eps

class KMeansClustering(nn.Module):
    """ Use KMeans to calculate cluster centers of embeddings (used in NCL)
    """

    def __init__(self, cluster_num, embedding_size):
        super(KMeansClustering, self).__init__()
        self.cluster_num = cluster_num
        self.embedding_size = embedding_size

    def forward(self, embeds):
        """
        :param embeds: embedding matrix
        :return: cluster information obtained by KMeans
        """
        centroids = t.rand([self.cluster_num, self.embedding_size]).cuda()
        ones = t.ones([embeds.shape[0], 1]).cuda()
        for i in range(1000):
            dists = (embeds.view([-1, 1, self.embedding_size]) - centroids.view([1, -1, self.embedding_size])).square().sum(-1)
            _, idxs = t.min(dists, dim=1)
            newCents = t.zeros_like(centroids)
            newCents.index_add_(0, idxs, embeds)
            clustNums = t.zeros([centroids.shape[0], 1]).cuda()
            clustNums.index_add_(0, idxs, ones)
            centroids = newCents / (clustNums + 1e-06)
        return (centroids, idxs, clustNums)

def __init__(self, cluster_num, embedding_size):
    super(KMeansClustering, self).__init__()
    self.cluster_num = cluster_num
    self.embedding_size = embedding_size

class BaseModel(nn.Module):

    def __init__(self, data_handler):
        super(BaseModel, self).__init__()
        self.user_num = configs['data']['user_num']
        self.item_num = configs['data']['item_num']
        self.embedding_size = configs['model']['embedding_size']
        if configs['data']['name'] in configs['model']:
            self.hyper_config = configs['model'][configs['data']['name']]
        else:
            self.hyper_config = configs['model']

    def forward(self):
        pass

    def cal_loss(self, batch_data):
        """return losses and weighted loss to training

        Args:
            batch_data (tuple): a batch of training samples already in cuda
        
        Return:
            loss (0-d torch.Tensor): the overall weighted loss
            losses (dict): dict for specific terms of losses for printing
        """
        pass

    def _mask_predict(self, full_preds, train_mask):
        return full_preds * (1 - train_mask) - 100000000.0 * train_mask

    def full_predict(self, batch_data):
        """return all-rank predictions to evaluation process, should call _mask_predict for masking the training pairs

        Args:
            batch_data (tuple): data in a test batch, e.g. batch_users, train_mask
        
        Return:
            full_preds (torch.Tensor): a [test_batch_size * item_num] prediction tensor
        """
        pass

def __init__(self, data_handler):
    super(BaseModel, self).__init__()
    self.user_num = configs['data']['user_num']
    self.item_num = configs['data']['item_num']
    self.embedding_size = configs['model']['embedding_size']
    if configs['data']['name'] in configs['model']:
        self.hyper_config = configs['model'][configs['data']['name']]
    else:
        self.hyper_config = configs['model']

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

class SGL_plus(LightGCN):

    def __init__(self, data_handler):
        super(SGL_plus, self).__init__(data_handler)
        self.augmentation = configs['model']['augmentation']
        self.node_dropper = NodeDrop()
        self.cl_weight = self.hyper_config['cl_weight']
        self.cl_temperature = self.hyper_config['cl_temperature']
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

    def forward(self, adj=None, keep_rate=1.0):
        if adj is None:
            adj = self.adj
        if not self.is_training and self.final_embeds is not None:
            return (self.final_embeds[:self.user_num], self.final_embeds[self.user_num:])
        embeds = t.concat([self.user_embeds, self.item_embeds], axis=0)
        if self.augmentation == 'node_drop':
            embeds = self.node_dropper(embeds, keep_rate)
        embeds_list = [embeds]
        if self.augmentation == 'edge_drop':
            adj = self.edge_dropper(adj, keep_rate)
        for i in range(configs['model']['layer_num']):
            random_walk = self.augmentation == 'random_walk'
            tem_adj = adj if not random_walk else self.edge_dropper(tem_adj, keep_rate)
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
        keep_rate = configs['model']['keep_rate']
        user_embeds1, item_embeds1 = self.forward(self.adj, keep_rate)
        user_embeds2, item_embeds2 = self.forward(self.adj, keep_rate)
        user_embeds3, item_embeds3 = self.forward(self.adj, 1.0)
        anc_embeds1, pos_embeds1, neg_embeds1 = self._pick_embeds(user_embeds1, item_embeds1, batch_data)
        anc_embeds2, pos_embeds2, neg_embeds2 = self._pick_embeds(user_embeds2, item_embeds2, batch_data)
        anc_embeds3, pos_embeds3, neg_embeds3 = self._pick_embeds(user_embeds3, item_embeds3, batch_data)
        usrprf_embeds = self.mlp(self.usrprf_embeds)
        itmprf_embeds = self.mlp(self.itmprf_embeds)
        ancprf_embeds, posprf_embeds, negprf_embeds = self._pick_embeds(usrprf_embeds, itmprf_embeds, batch_data)
        bpr_loss = cal_bpr_loss(anc_embeds3, pos_embeds3, neg_embeds3) / anc_embeds3.shape[0]
        cl_loss = cal_infonce_loss(anc_embeds1, anc_embeds2, user_embeds2, self.cl_temperature) + cal_infonce_loss(pos_embeds1, pos_embeds2, item_embeds2, self.cl_temperature) + cal_infonce_loss(neg_embeds1, neg_embeds2, item_embeds2, self.cl_temperature)
        cl_loss /= anc_embeds1.shape[0]
        cl_loss *= self.cl_weight
        kd_loss = cal_infonce_loss(anc_embeds3, ancprf_embeds, usrprf_embeds, self.kd_temperature) + cal_infonce_loss(pos_embeds3, posprf_embeds, posprf_embeds, self.kd_temperature) + cal_infonce_loss(neg_embeds3, negprf_embeds, negprf_embeds, self.kd_temperature)
        kd_loss /= anc_embeds3.shape[0]
        kd_loss *= self.kd_weight
        reg_loss = self.reg_weight * reg_params(self)
        loss = bpr_loss + reg_loss + cl_loss + kd_loss
        losses = {'bpr_loss': bpr_loss, 'reg_loss': reg_loss, 'cl_loss': cl_loss, 'kd_loss': kd_loss}
        return (loss, losses)

def __init__(self, data_handler):
    super(SGL_plus, self).__init__(data_handler)
    self.augmentation = configs['model']['augmentation']
    self.node_dropper = NodeDrop()
    self.cl_weight = self.hyper_config['cl_weight']
    self.cl_temperature = self.hyper_config['cl_temperature']
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

class DCCF_gene(BaseModel):

    def __init__(self, data_handler):
        super(DCCF_gene, self).__init__(data_handler)
        rows = data_handler.trn_mat.tocoo().row
        cols = data_handler.trn_mat.tocoo().col
        new_rows = np.concatenate([rows, cols + self.user_num], axis=0)
        new_cols = np.concatenate([cols + self.user_num, rows], axis=0)
        plain_adj = sp.coo_matrix((np.ones(len(new_rows)), (new_rows, new_cols)), shape=[self.user_num + self.item_num, self.user_num + self.item_num]).tocsr().tocoo()
        self.all_h_list = list(plain_adj.row)
        self.all_t_list = list(plain_adj.col)
        self.A_in_shape = plain_adj.shape
        self.A_indices = torch.tensor([self.all_h_list, self.all_t_list], dtype=torch.long).cuda()
        self.D_indices = torch.tensor([list(range(self.user_num + self.item_num)), list(range(self.user_num + self.item_num))], dtype=torch.long).cuda()
        self.all_h_list = torch.LongTensor(self.all_h_list).cuda()
        self.all_t_list = torch.LongTensor(self.all_t_list).cuda()
        self.G_indices, self.G_values = self._cal_sparse_adj()
        self.intent_num = configs['model']['intent_num']
        self.layer_num = self.hyper_config['layer_num']
        self.reg_weight = self.hyper_config['reg_weight']
        self.cl_weight = self.hyper_config['cl_weight']
        self.cl_temperature = self.hyper_config['cl_temperature']
        self.mask_ratio = self.hyper_config['mask_ratio']
        self.recon_weight = self.hyper_config['recon_weight']
        self.re_temperature = self.hyper_config['re_temperature']
        self.user_embeds = nn.Embedding(self.user_num, self.embedding_size)
        self.item_embeds = nn.Embedding(self.item_num, self.embedding_size)
        self.user_intent = torch.nn.Parameter(init(torch.empty(self.embedding_size, self.intent_num)), requires_grad=True)
        self.item_intent = torch.nn.Parameter(init(torch.empty(self.embedding_size, self.intent_num)), requires_grad=True)
        self.is_training = True
        self.final_embeds = False
        usrprf_embeds = torch.tensor(configs['usrprf_embeds']).float().cuda()
        itmprf_embeds = torch.tensor(configs['itmprf_embeds']).float().cuda()
        self.prf_embeds = torch.concat([usrprf_embeds, itmprf_embeds], dim=0)
        self.masker = NodeMask(self.mask_ratio, self.embedding_size)
        self.mlp = nn.Sequential(nn.Linear(self.embedding_size, (self.prf_embeds.shape[1] + self.embedding_size) // 2), nn.LeakyReLU(), nn.Linear((self.prf_embeds.shape[1] + self.embedding_size) // 2, self.prf_embeds.shape[1]))
        self._init_weight()

    def _init_weight(self):
        for m in self.mlp:
            if isinstance(m, nn.Linear):
                init(m.weight)
        init(self.user_embeds.weight)
        init(self.item_embeds.weight)

    def _cal_sparse_adj(self):
        A_values = torch.ones(size=(len(self.all_h_list), 1)).view(-1).cuda()
        A_tensor = torch_sparse.SparseTensor(row=self.all_h_list, col=self.all_t_list, value=A_values, sparse_sizes=self.A_in_shape).cuda()
        D_values = A_tensor.sum(dim=1).pow(-0.5)
        G_indices, G_values = torch_sparse.spspmm(self.D_indices, D_values, self.A_indices, A_values, self.A_in_shape[0], self.A_in_shape[1], self.A_in_shape[1])
        G_indices, G_values = torch_sparse.spspmm(G_indices, G_values, self.D_indices, D_values, self.A_in_shape[0], self.A_in_shape[1], self.A_in_shape[1])
        return (G_indices, G_values)

    def _adaptive_mask(self, head_embeddings, tail_embeddings):
        head_embeddings = torch.nn.functional.normalize(head_embeddings)
        tail_embeddings = torch.nn.functional.normalize(tail_embeddings)
        edge_alpha = (torch.sum(head_embeddings * tail_embeddings, dim=1).view(-1) + 1) / 2
        A_tensor = torch_sparse.SparseTensor(row=self.all_h_list, col=self.all_t_list, value=edge_alpha, sparse_sizes=self.A_in_shape).cuda()
        D_scores_inv = A_tensor.sum(dim=1).pow(-1).nan_to_num(0, 0, 0).view(-1)
        G_indices = torch.stack([self.all_h_list, self.all_t_list], dim=0)
        G_values = D_scores_inv[self.all_h_list] * edge_alpha
        return (G_indices, G_values)

    def _mask(self):
        embeds = torch.concat([self.user_embeds.weight, self.item_embeds.weight], axis=0)
        masked_embeds, seeds = self.masker(embeds)
        return (masked_embeds[:self.user_num], masked_embeds[self.user_num:], seeds)

    def forward(self, masked_user_embeds=None, masked_item_embeds=None):
        if not self.is_training and self.final_embeds is not None:
            return (self.final_embeds[:self.user_num], self.final_embeds[self.user_num:], None, None, None, None)
        if masked_user_embeds is None or masked_item_embeds is None:
            all_embeds = [torch.concat([self.user_embeds.weight, self.item_embeds.weight], dim=0)]
        else:
            all_embeds = [torch.concat([masked_user_embeds, masked_item_embeds], dim=0)]
        gnn_embeds, int_embeds, gaa_embeds, iaa_embeds = ([], [], [], [])
        for i in range(0, self.layer_num):
            gnn_layer_embeds = torch_sparse.spmm(self.G_indices, self.G_values, self.A_in_shape[0], self.A_in_shape[1], all_embeds[i])
            u_embeds, i_embeds = torch.split(all_embeds[i], [self.user_num, self.item_num], 0)
            u_int_embeds = torch.softmax(u_embeds @ self.user_intent, dim=1) @ self.user_intent.T
            i_int_embeds = torch.softmax(i_embeds @ self.item_intent, dim=1) @ self.item_intent.T
            int_layer_embeds = torch.concat([u_int_embeds, i_int_embeds], dim=0)
            gnn_head_embeds = torch.index_select(gnn_layer_embeds, 0, self.all_h_list)
            gnn_tail_embeds = torch.index_select(gnn_layer_embeds, 0, self.all_t_list)
            int_head_embeds = torch.index_select(int_layer_embeds, 0, self.all_h_list)
            int_tail_embeds = torch.index_select(int_layer_embeds, 0, self.all_t_list)
            G_graph_indices, G_graph_values = self._adaptive_mask(gnn_head_embeds, gnn_tail_embeds)
            G_inten_indices, G_inten_values = self._adaptive_mask(int_head_embeds, int_tail_embeds)
            gaa_layer_embeds = torch_sparse.spmm(G_graph_indices, G_graph_values, self.A_in_shape[0], self.A_in_shape[1], all_embeds[i])
            iaa_layer_embeds = torch_sparse.spmm(G_inten_indices, G_inten_values, self.A_in_shape[0], self.A_in_shape[1], all_embeds[i])
            gnn_embeds.append(gnn_layer_embeds)
            int_embeds.append(int_layer_embeds)
            gaa_embeds.append(gaa_layer_embeds)
            iaa_embeds.append(iaa_layer_embeds)
            all_embeds.append(gnn_layer_embeds + int_layer_embeds + gaa_layer_embeds + iaa_layer_embeds + all_embeds[i])
        all_embeds = torch.stack(all_embeds, dim=1)
        all_embeds = torch.sum(all_embeds, dim=1, keepdim=False)
        user_embeds, item_embeds = torch.split(all_embeds, [self.user_num, self.item_num], 0)
        self.final_embeds = all_embeds
        return (user_embeds, item_embeds, gnn_embeds, int_embeds, gaa_embeds, iaa_embeds)

    def _pick_embeds(self, user_embeds, item_embeds, batch_data):
        ancs, poss, negs = batch_data
        anc_embeds = user_embeds[ancs]
        pos_embeds = item_embeds[poss]
        neg_embeds = item_embeds[negs]
        return (anc_embeds, pos_embeds, neg_embeds)

    def _cal_cl_loss(self, users, items, gnn_emb, int_emb, gaa_emb, iaa_emb):
        users = torch.unique(users)
        items = torch.unique(items)
        cl_loss = 0.0
        for i in range(len(gnn_emb)):
            u_gnn_embs, i_gnn_embs = torch.split(gnn_emb[i], [self.user_num, self.item_num], 0)
            u_int_embs, i_int_embs = torch.split(int_emb[i], [self.user_num, self.item_num], 0)
            u_gaa_embs, i_gaa_embs = torch.split(gaa_emb[i], [self.user_num, self.item_num], 0)
            u_iaa_embs, i_iaa_embs = torch.split(iaa_emb[i], [self.user_num, self.item_num], 0)
            u_gnn_embs = u_gnn_embs[users]
            u_int_embs = u_int_embs[users]
            u_gaa_embs = u_gaa_embs[users]
            u_iaa_embs = u_iaa_embs[users]
            i_gnn_embs = i_gnn_embs[items]
            i_int_embs = i_int_embs[items]
            i_gaa_embs = i_gaa_embs[items]
            i_iaa_embs = i_iaa_embs[items]
            cl_loss += cal_infonce_loss(u_gnn_embs, u_int_embs, u_int_embs, self.cl_temperature) / u_gnn_embs.shape[0]
            cl_loss += cal_infonce_loss(u_gnn_embs, u_gaa_embs, u_gaa_embs, self.cl_temperature) / u_gnn_embs.shape[0]
            cl_loss += cal_infonce_loss(u_gnn_embs, u_iaa_embs, u_iaa_embs, self.cl_temperature) / u_gnn_embs.shape[0]
            cl_loss += cal_infonce_loss(i_gnn_embs, i_int_embs, i_int_embs, self.cl_temperature) / u_gnn_embs.shape[0]
            cl_loss += cal_infonce_loss(i_gnn_embs, i_gaa_embs, i_gaa_embs, self.cl_temperature) / u_gnn_embs.shape[0]
            cl_loss += cal_infonce_loss(i_gnn_embs, i_iaa_embs, i_iaa_embs, self.cl_temperature) / u_gnn_embs.shape[0]
        return cl_loss

    def _reconstruction(self, embeds, seeds):
        enc_embeds = embeds[seeds]
        prf_embeds = self.prf_embeds[seeds]
        enc_embeds = self.mlp(enc_embeds)
        recon_loss = ssl_con_loss(enc_embeds, prf_embeds, self.re_temperature)
        return recon_loss

    def cal_loss(self, batch_data):
        self.is_training = True
        masked_user_embeds, masked_item_embeds, seeds = self._mask()
        user_embeds, item_embeds, gnn_embeds, int_embeds, gaa_embeds, iaa_embeds = self.forward(masked_user_embeds, masked_item_embeds)
        ancs, poss, negs = batch_data
        anc_embeds = user_embeds[ancs]
        pos_embeds = item_embeds[poss]
        neg_embeds = item_embeds[negs]
        bpr_loss = cal_bpr_loss(anc_embeds, pos_embeds, neg_embeds) / anc_embeds.shape[0]
        reg_loss = self.reg_weight * reg_params(self)
        cl_loss = self.cl_weight * self._cal_cl_loss(ancs, poss, gnn_embeds, int_embeds, gaa_embeds, iaa_embeds)
        recon_loss = self.recon_weight * self._reconstruction(torch.concat([user_embeds, item_embeds], axis=0), seeds)
        loss = bpr_loss + reg_loss + cl_loss + recon_loss
        losses = {'bpr_loss': bpr_loss, 'reg_loss': reg_loss, 'cl_loss': cl_loss, 'recon_loss': recon_loss}
        return (loss, losses)

    def full_predict(self, batch_data):
        user_embeds, item_embeds, _, _, _, _ = self.forward()
        self.is_training = False
        pck_users, train_mask = batch_data
        pck_users = pck_users.long()
        pck_user_embeds = user_embeds[pck_users]
        full_preds = pck_user_embeds @ item_embeds.T
        full_preds = self._mask_predict(full_preds, train_mask)
        return full_preds

def __init__(self, data_handler):
    super(DCCF_gene, self).__init__(data_handler)
    rows = data_handler.trn_mat.tocoo().row
    cols = data_handler.trn_mat.tocoo().col
    new_rows = np.concatenate([rows, cols + self.user_num], axis=0)
    new_cols = np.concatenate([cols + self.user_num, rows], axis=0)
    plain_adj = sp.coo_matrix((np.ones(len(new_rows)), (new_rows, new_cols)), shape=[self.user_num + self.item_num, self.user_num + self.item_num]).tocsr().tocoo()
    self.all_h_list = list(plain_adj.row)
    self.all_t_list = list(plain_adj.col)
    self.A_in_shape = plain_adj.shape
    self.A_indices = torch.tensor([self.all_h_list, self.all_t_list], dtype=torch.long).cuda()
    self.D_indices = torch.tensor([list(range(self.user_num + self.item_num)), list(range(self.user_num + self.item_num))], dtype=torch.long).cuda()
    self.all_h_list = torch.LongTensor(self.all_h_list).cuda()
    self.all_t_list = torch.LongTensor(self.all_t_list).cuda()
    self.G_indices, self.G_values = self._cal_sparse_adj()
    self.intent_num = configs['model']['intent_num']
    self.layer_num = self.hyper_config['layer_num']
    self.reg_weight = self.hyper_config['reg_weight']
    self.cl_weight = self.hyper_config['cl_weight']
    self.cl_temperature = self.hyper_config['cl_temperature']
    self.mask_ratio = self.hyper_config['mask_ratio']
    self.recon_weight = self.hyper_config['recon_weight']
    self.re_temperature = self.hyper_config['re_temperature']
    self.user_embeds = nn.Embedding(self.user_num, self.embedding_size)
    self.item_embeds = nn.Embedding(self.item_num, self.embedding_size)
    self.user_intent = torch.nn.Parameter(init(torch.empty(self.embedding_size, self.intent_num)), requires_grad=True)
    self.item_intent = torch.nn.Parameter(init(torch.empty(self.embedding_size, self.intent_num)), requires_grad=True)
    self.is_training = True
    self.final_embeds = False
    usrprf_embeds = torch.tensor(configs['usrprf_embeds']).float().cuda()
    itmprf_embeds = torch.tensor(configs['itmprf_embeds']).float().cuda()
    self.prf_embeds = torch.concat([usrprf_embeds, itmprf_embeds], dim=0)
    self.masker = NodeMask(self.mask_ratio, self.embedding_size)
    self.mlp = nn.Sequential(nn.Linear(self.embedding_size, (self.prf_embeds.shape[1] + self.embedding_size) // 2), nn.LeakyReLU(), nn.Linear((self.prf_embeds.shape[1] + self.embedding_size) // 2, self.prf_embeds.shape[1]))
    self._init_weight()

def _init_weight(self):
    for m in self.mlp:
        if isinstance(m, nn.Linear):
            init(m.weight)
    init(self.user_embeds.weight)
    init(self.item_embeds.weight)

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

class SimGCL(LightGCN):

    def __init__(self, data_handler):
        super(SimGCL, self).__init__(data_handler)
        self.cl_weight = self.hyper_config['cl_weight']
        self.temperature = self.hyper_config['temperature']
        self.eps = self.hyper_config['eps']

    def _perturb_embedding(self, embeds):
        noise = F.normalize(t.rand(embeds.shape).cuda(), p=2) * t.sign(embeds) * self.eps
        return embeds + noise

    def forward(self, adj=None, perturb=False):
        if adj is None:
            adj = self.adj
        if not perturb:
            return super(SimGCL, self).forward(adj, 1.0)
        embeds = t.concat([self.user_embeds, self.item_embeds], dim=0)
        embeds_list = [embeds]
        for i in range(self.layer_num):
            embeds = self._propagate(adj, embeds_list[-1])
            embeds = self._perturb_embedding(embeds)
            embeds_list.append(embeds)
        embeds = sum(embeds_list)
        return (embeds[:self.user_num], embeds[self.user_num:])

    def _pick_embeds(self, user_embeds, item_embeds, batch_data):
        ancs, poss, negs = batch_data
        anc_embeds = user_embeds[ancs]
        pos_embeds = item_embeds[poss]
        neg_embeds = item_embeds[negs]
        return (anc_embeds, pos_embeds, neg_embeds)

    def cal_loss(self, batch_data):
        self.is_training = True
        user_embeds1, item_embeds1 = self.forward(self.adj, perturb=True)
        user_embeds2, item_embeds2 = self.forward(self.adj, perturb=True)
        user_embeds3, item_embeds3 = self.forward(self.adj, perturb=False)
        anc_embeds1, pos_embeds1, neg_embeds1 = self._pick_embeds(user_embeds1, item_embeds1, batch_data)
        anc_embeds2, pos_embeds2, neg_embeds2 = self._pick_embeds(user_embeds2, item_embeds2, batch_data)
        anc_embeds3, pos_embeds3, neg_embeds3 = self._pick_embeds(user_embeds3, item_embeds3, batch_data)
        bpr_loss = cal_bpr_loss(anc_embeds3, pos_embeds3, neg_embeds3) / anc_embeds3.shape[0]
        cl_loss = cal_infonce_loss(anc_embeds1, anc_embeds2, user_embeds2, self.temperature) + cal_infonce_loss(pos_embeds1, pos_embeds2, item_embeds2, self.temperature)
        cl_loss /= anc_embeds1.shape[0]
        reg_loss = self.reg_weight * reg_params(self)
        cl_loss *= self.cl_weight
        loss = bpr_loss + reg_loss + cl_loss
        losses = {'bpr_loss': bpr_loss, 'reg_loss': reg_loss, 'cl_loss': cl_loss}
        return (loss, losses)

    def full_predict(self, batch_data):
        user_embeds, item_embeds = self.forward(self.adj, False)
        self.is_training = False
        pck_users, train_mask = batch_data
        pck_users = pck_users.long()
        pck_user_embeds = user_embeds[pck_users]
        full_preds = pck_user_embeds @ item_embeds.T
        full_preds = self._mask_predict(full_preds, train_mask)
        return full_preds

def __init__(self, data_handler):
    super(SimGCL, self).__init__(data_handler)
    self.cl_weight = self.hyper_config['cl_weight']
    self.temperature = self.hyper_config['temperature']
    self.eps = self.hyper_config['eps']

class AutoCF_gene(BaseModel):

    def __init__(self, data_handler):
        super(AutoCF_gene, self).__init__(data_handler)
        self.user_embeds = nn.Parameter(init(t.empty(self.user_num, self.embedding_size)))
        self.item_embeds = nn.Parameter(init(t.empty(self.item_num, self.embedding_size)))
        self.adj = data_handler.torch_adj
        self.all_one_adj = self.make_all_one_adj()
        self.gt_layer = configs['model']['gt_layer']
        self.gcn_layer = self.hyper_config['gcn_layer']
        self.reg_weight = self.hyper_config['reg_weight']
        self.ssl_reg = self.hyper_config['ssl_reg']
        self.mask_ratio = self.hyper_config['mask_ratio']
        self.recon_weight = self.hyper_config['recon_weight']
        self.re_temperature = self.hyper_config['re_temperature']
        self.gcnLayers = nn.Sequential(*[GCNLayer() for i in range(self.gcn_layer)])
        self.gtLayers = nn.Sequential(*[GTLayer() for i in range(self.gt_layer)])
        self.masker = RandomMaskSubgraphs()
        self.sampler = LocalGraph()
        usrprf_embeds = t.tensor(configs['usrprf_embeds']).float().cuda()
        itmprf_embeds = t.tensor(configs['itmprf_embeds']).float().cuda()
        self.prf_embeds = t.concat([usrprf_embeds, itmprf_embeds], dim=0)
        self.gene_masker = NodeMask(self.mask_ratio, self.embedding_size)
        self.mlp = nn.Sequential(nn.Linear(self.embedding_size, (self.prf_embeds.shape[1] + self.embedding_size) // 2), nn.LeakyReLU(), nn.Linear((self.prf_embeds.shape[1] + self.embedding_size) // 2, self.prf_embeds.shape[1]))
        self._init_weight()

    def _init_weight(self):
        for m in self.mlp:
            if isinstance(m, nn.Linear):
                init(m.weight)

    def _mask(self):
        embeds = t.concat([self.user_embeds, self.item_embeds], axis=0)
        masked_embeds, seeds = self.gene_masker(embeds)
        return (masked_embeds[:self.user_num], masked_embeds[self.user_num:], seeds)

    def _reconstruction(self, embeds, seeds):
        enc_embeds = embeds[seeds]
        prf_embeds = self.prf_embeds[seeds]
        enc_embeds = self.mlp(enc_embeds)
        recon_loss = ssl_con_loss(enc_embeds, prf_embeds, self.re_temperature)
        return recon_loss

    def make_all_one_adj(self):
        idxs = self.adj._indices()
        vals = t.ones_like(self.adj._values())
        shape = self.adj.shape
        return t.sparse.FloatTensor(idxs, vals, shape).cuda()

    def get_ego_embeds(self):
        return t.concat([self.user_embeds, self.item_embeds], axis=0)

    def sample_subgraphs(self):
        return self.sampler(self.all_one_adj, self.get_ego_embeds())

    def mask_subgraphs(self, seeds):
        return self.masker(self.adj, seeds)

    def forward(self, encoder_adj, decoder_adj=None, masked_user_embeds=None, masked_item_embeds=None):
        if masked_user_embeds is None or masked_item_embeds is None:
            embeds = t.concat([self.user_embeds, self.item_embeds], axis=0)
        else:
            embeds = t.concat([masked_user_embeds, masked_item_embeds], axis=0)
        embedsLst = [embeds]
        for i, gcn in enumerate(self.gcnLayers):
            embeds = gcn(encoder_adj, embedsLst[-1])
            embedsLst.append(embeds)
        if decoder_adj is not None:
            for gt in self.gtLayers:
                embeds = gt(decoder_adj, embedsLst[-1])
                embedsLst.append(embeds)
        embeds = sum(embedsLst)
        return (embeds[:self.user_num], embeds[self.user_num:])

    def contrast(self, nodes, allEmbeds, allEmbeds2=None):
        if allEmbeds2 is not None:
            pckEmbeds = allEmbeds[nodes]
            scores = t.log(t.exp(pckEmbeds @ allEmbeds2.T).sum(-1)).mean()
        else:
            uniqNodes = t.unique(nodes)
            pckEmbeds = allEmbeds[uniqNodes]
            scores = t.log(t.exp(pckEmbeds @ allEmbeds.T).sum(-1)).mean()
        return scores

    def cal_loss(self, batch_data, encoder_adj, decoder_adj):
        masked_user_embeds, masked_item_embeds, seeds = self._mask()
        user_embeds, item_embeds = self.forward(encoder_adj, decoder_adj, masked_user_embeds, masked_item_embeds)
        ancs, poss, _ = batch_data
        anc_embeds = user_embeds[ancs]
        pos_embeds = item_embeds[poss]
        rec_loss = (-t.sum(anc_embeds * pos_embeds, dim=-1)).mean()
        reg_loss = reg_params(self) * self.reg_weight
        cl_loss = (self.contrast(ancs, user_embeds) + self.contrast(poss, item_embeds)) * self.ssl_reg + self.contrast(ancs, user_embeds, item_embeds)
        recon_loss = self.recon_weight * self._reconstruction(t.concat([user_embeds, item_embeds], axis=0), seeds)
        loss = rec_loss + reg_loss + cl_loss + recon_loss
        losses = {'rec_loss': rec_loss, 'reg_loss': reg_loss, 'cl_loss': cl_loss, 'recon_loss': recon_loss}
        return (loss, losses)

    def full_predict(self, batch_data):
        user_embeds, item_embeds = self.forward(self.adj, self.adj)
        pck_users, train_mask = batch_data
        pck_users = pck_users.long()
        pck_user_embeds = user_embeds[pck_users]
        full_preds = pck_user_embeds @ item_embeds.T
        full_preds = self._mask_predict(full_preds, train_mask)
        return full_preds

def __init__(self, data_handler):
    super(AutoCF_gene, self).__init__(data_handler)
    self.user_embeds = nn.Parameter(init(t.empty(self.user_num, self.embedding_size)))
    self.item_embeds = nn.Parameter(init(t.empty(self.item_num, self.embedding_size)))
    self.adj = data_handler.torch_adj
    self.all_one_adj = self.make_all_one_adj()
    self.gt_layer = configs['model']['gt_layer']
    self.gcn_layer = self.hyper_config['gcn_layer']
    self.reg_weight = self.hyper_config['reg_weight']
    self.ssl_reg = self.hyper_config['ssl_reg']
    self.mask_ratio = self.hyper_config['mask_ratio']
    self.recon_weight = self.hyper_config['recon_weight']
    self.re_temperature = self.hyper_config['re_temperature']
    self.gcnLayers = nn.Sequential(*[GCNLayer() for i in range(self.gcn_layer)])
    self.gtLayers = nn.Sequential(*[GTLayer() for i in range(self.gt_layer)])
    self.masker = RandomMaskSubgraphs()
    self.sampler = LocalGraph()
    usrprf_embeds = t.tensor(configs['usrprf_embeds']).float().cuda()
    itmprf_embeds = t.tensor(configs['itmprf_embeds']).float().cuda()
    self.prf_embeds = t.concat([usrprf_embeds, itmprf_embeds], dim=0)
    self.gene_masker = NodeMask(self.mask_ratio, self.embedding_size)
    self.mlp = nn.Sequential(nn.Linear(self.embedding_size, (self.prf_embeds.shape[1] + self.embedding_size) // 2), nn.LeakyReLU(), nn.Linear((self.prf_embeds.shape[1] + self.embedding_size) // 2, self.prf_embeds.shape[1]))
    self._init_weight()

def _init_weight(self):
    for m in self.mlp:
        if isinstance(m, nn.Linear):
            init(m.weight)

class GCNLayer(nn.Module):

    def __init__(self):
        super(GCNLayer, self).__init__()

    def forward(self, adj, embeds):
        return t.spmm(adj, embeds)

def __init__(self):
    super(GCNLayer, self).__init__()

class GTLayer(nn.Module):

    def __init__(self):
        super(GTLayer, self).__init__()
        self.head_num = configs['model']['head_num']
        self.embedding_size = configs['model']['embedding_size']
        self.qTrans = nn.Parameter(init(t.empty(self.embedding_size, self.embedding_size)))
        self.kTrans = nn.Parameter(init(t.empty(self.embedding_size, self.embedding_size)))
        self.vTrans = nn.Parameter(init(t.empty(self.embedding_size, self.embedding_size)))

    def forward(self, adj, embeds):
        indices = adj._indices()
        rows, cols = (indices[0, :], indices[1, :])
        rowEmbeds = embeds[rows]
        colEmbeds = embeds[cols]
        qEmbeds = (rowEmbeds @ self.qTrans).view([-1, self.head_num, self.embedding_size // self.head_num])
        kEmbeds = (colEmbeds @ self.kTrans).view([-1, self.head_num, self.embedding_size // self.head_num])
        vEmbeds = (colEmbeds @ self.vTrans).view([-1, self.head_num, self.embedding_size // self.head_num])
        att = t.einsum('ehd, ehd -> eh', qEmbeds, kEmbeds)
        att = t.clamp(att, -10.0, 10.0)
        expAtt = t.exp(att)
        tem = t.zeros([adj.shape[0], self.head_num]).cuda()
        attNorm = tem.index_add_(0, rows, expAtt)[rows]
        att = expAtt / (attNorm + 1e-08)
        resEmbeds = t.einsum('eh, ehd -> ehd', att, vEmbeds).view([-1, self.embedding_size])
        tem = t.zeros([adj.shape[0], self.embedding_size]).cuda()
        resEmbeds = tem.index_add_(0, rows, resEmbeds)
        return resEmbeds

def __init__(self):
    super(GTLayer, self).__init__()
    self.head_num = configs['model']['head_num']
    self.embedding_size = configs['model']['embedding_size']
    self.qTrans = nn.Parameter(init(t.empty(self.embedding_size, self.embedding_size)))
    self.kTrans = nn.Parameter(init(t.empty(self.embedding_size, self.embedding_size)))
    self.vTrans = nn.Parameter(init(t.empty(self.embedding_size, self.embedding_size)))

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

def __init__(self):
    super(LocalGraph, self).__init__()
    self.seed_num = configs['model']['seed_num']

class RandomMaskSubgraphs(nn.Module):

    def __init__(self):
        super(RandomMaskSubgraphs, self).__init__()
        self.flag = False
        self.mask_depth = configs['model']['mask_depth']
        self.keep_rate = configs['model']['keep_rate']
        self.user_num = configs['data']['user_num']
        self.item_num = configs['data']['item_num']

    def normalizeAdj(self, adj):
        degree = t.pow(t.sparse.sum(adj, dim=1).to_dense() + 1e-12, -0.5)
        newRows, newCols = (adj._indices()[0, :], adj._indices()[1, :])
        rowNorm, colNorm = (degree[newRows], degree[newCols])
        newVals = adj._values() * rowNorm * colNorm
        return t.sparse.FloatTensor(adj._indices(), newVals, adj.shape)

    def forward(self, adj, seeds):
        rows = adj._indices()[0, :]
        cols = adj._indices()[1, :]
        maskNodes = [seeds]
        for i in range(self.mask_depth):
            curSeeds = seeds if i == 0 else nxtSeeds
            nxtSeeds = list()
            for seed in curSeeds:
                rowIdct = rows == seed
                colIdct = cols == seed
                idct = t.logical_or(rowIdct, colIdct)
                if i != self.mask_depth - 1:
                    mskRows = rows[idct]
                    mskCols = cols[idct]
                    nxtSeeds.append(mskRows)
                    nxtSeeds.append(mskCols)
                rows = rows[t.logical_not(idct)]
                cols = cols[t.logical_not(idct)]
            if len(nxtSeeds) > 0:
                nxtSeeds = t.unique(t.concat(nxtSeeds))
                maskNodes.append(nxtSeeds)
        sampNum = int((self.user_num + self.item_num) * self.keep_rate)
        sampedNodes = t.randint(self.user_num + self.item_num, size=[sampNum]).cuda()
        if self.flag == False:
            l1 = adj._values().shape[0]
            l2 = rows.shape[0]
            print('-----')
            print('LENGTH CHANGE', '%.2f' % (l2 / l1), l2, l1)
            tem = t.unique(t.concat(maskNodes))
            print('Original SAMPLED NODES', '%.2f' % (tem.shape[0] / (self.user_num + self.item_num)), tem.shape[0], self.user_num + self.item_num)
        maskNodes.append(sampedNodes)
        maskNodes = t.unique(t.concat(maskNodes))
        if self.flag == False:
            print('AUGMENTED SAMPLED NODES', '%.2f' % (maskNodes.shape[0] / (self.user_num + self.item_num)), maskNodes.shape[0], self.user_num + self.item_num)
            self.flag = True
            print('-----')
        encoder_adj = self.normalizeAdj(t.sparse.FloatTensor(t.stack([rows, cols], dim=0), t.ones_like(rows).cuda(), adj.shape))
        temNum = maskNodes.shape[0]
        temRows = maskNodes[t.randint(temNum, size=[adj._values().shape[0]]).cuda()]
        temCols = maskNodes[t.randint(temNum, size=[adj._values().shape[0]]).cuda()]
        newRows = t.concat([temRows, temCols, t.arange(self.user_num + self.item_num).cuda(), rows])
        newCols = t.concat([temCols, temRows, t.arange(self.user_num + self.item_num).cuda(), cols])
        hashVal = newRows * (self.user_num + self.item_num) + newCols
        hashVal = t.unique(hashVal)
        newCols = hashVal % (self.user_num + self.item_num)
        newRows = ((hashVal - newCols) / (self.user_num + self.item_num)).long()
        decoder_adj = t.sparse.FloatTensor(t.stack([newRows, newCols], dim=0), t.ones_like(newRows).cuda().float(), adj.shape)
        return (encoder_adj, decoder_adj)

def __init__(self):
    super(RandomMaskSubgraphs, self).__init__()
    self.flag = False
    self.mask_depth = configs['model']['mask_depth']
    self.keep_rate = configs['model']['keep_rate']
    self.user_num = configs['data']['user_num']
    self.item_num = configs['data']['item_num']

class DCCF_plus(BaseModel):

    def __init__(self, data_handler):
        super(DCCF_plus, self).__init__(data_handler)
        rows = data_handler.trn_mat.tocoo().row
        cols = data_handler.trn_mat.tocoo().col
        new_rows = np.concatenate([rows, cols + self.user_num], axis=0)
        new_cols = np.concatenate([cols + self.user_num, rows], axis=0)
        plain_adj = sp.coo_matrix((np.ones(len(new_rows)), (new_rows, new_cols)), shape=[self.user_num + self.item_num, self.user_num + self.item_num]).tocsr().tocoo()
        self.all_h_list = list(plain_adj.row)
        self.all_t_list = list(plain_adj.col)
        self.A_in_shape = plain_adj.shape
        self.A_indices = torch.tensor([self.all_h_list, self.all_t_list], dtype=torch.long).cuda()
        self.D_indices = torch.tensor([list(range(self.user_num + self.item_num)), list(range(self.user_num + self.item_num))], dtype=torch.long).cuda()
        self.all_h_list = torch.LongTensor(self.all_h_list).cuda()
        self.all_t_list = torch.LongTensor(self.all_t_list).cuda()
        self.G_indices, self.G_values = self._cal_sparse_adj()
        self.intent_num = configs['model']['intent_num']
        self.layer_num = self.hyper_config['layer_num']
        self.reg_weight = self.hyper_config['reg_weight']
        self.cl_weight = self.hyper_config['cl_weight']
        self.cl_temperature = self.hyper_config['cl_temperature']
        self.kd_weight = self.hyper_config['kd_weight']
        self.kd_temperature = self.hyper_config['kd_temperature']
        self.user_embeds = nn.Embedding(self.user_num, self.embedding_size)
        self.item_embeds = nn.Embedding(self.item_num, self.embedding_size)
        self.user_intent = torch.nn.Parameter(init(torch.empty(self.embedding_size, self.intent_num)), requires_grad=True)
        self.item_intent = torch.nn.Parameter(init(torch.empty(self.embedding_size, self.intent_num)), requires_grad=True)
        self.is_training = True
        self.final_embeds = False
        self.usrprf_embeds = torch.tensor(configs['usrprf_embeds']).float().cuda()
        self.itmprf_embeds = torch.tensor(configs['itmprf_embeds']).float().cuda()
        self.mlp = nn.Sequential(nn.Linear(self.usrprf_embeds.shape[1], (self.usrprf_embeds.shape[1] + self.embedding_size) // 2), nn.LeakyReLU(), nn.Linear((self.usrprf_embeds.shape[1] + self.embedding_size) // 2, self.embedding_size))
        self._init_weight()

    def _init_weight(self):
        for m in self.mlp:
            if isinstance(m, nn.Linear):
                init(m.weight)
        init(self.user_embeds.weight)
        init(self.item_embeds.weight)

    def _cal_sparse_adj(self):
        A_values = torch.ones(size=(len(self.all_h_list), 1)).view(-1).cuda()
        A_tensor = torch_sparse.SparseTensor(row=self.all_h_list, col=self.all_t_list, value=A_values, sparse_sizes=self.A_in_shape).cuda()
        D_values = A_tensor.sum(dim=1).pow(-0.5)
        G_indices, G_values = torch_sparse.spspmm(self.D_indices, D_values, self.A_indices, A_values, self.A_in_shape[0], self.A_in_shape[1], self.A_in_shape[1])
        G_indices, G_values = torch_sparse.spspmm(G_indices, G_values, self.D_indices, D_values, self.A_in_shape[0], self.A_in_shape[1], self.A_in_shape[1])
        return (G_indices, G_values)

    def _adaptive_mask(self, head_embeddings, tail_embeddings):
        head_embeddings = torch.nn.functional.normalize(head_embeddings)
        tail_embeddings = torch.nn.functional.normalize(tail_embeddings)
        edge_alpha = (torch.sum(head_embeddings * tail_embeddings, dim=1).view(-1) + 1) / 2
        A_tensor = torch_sparse.SparseTensor(row=self.all_h_list, col=self.all_t_list, value=edge_alpha, sparse_sizes=self.A_in_shape).cuda()
        D_scores_inv = A_tensor.sum(dim=1).pow(-1).nan_to_num(0, 0, 0).view(-1)
        G_indices = torch.stack([self.all_h_list, self.all_t_list], dim=0)
        G_values = D_scores_inv[self.all_h_list] * edge_alpha
        return (G_indices, G_values)

    def forward(self):
        if not self.is_training and self.final_embeds is not None:
            return (self.final_embeds[:self.user_num], self.final_embeds[self.user_num:], None, None, None, None)
        all_embeds = [torch.concat([self.user_embeds.weight, self.item_embeds.weight], dim=0)]
        gnn_embeds, int_embeds, gaa_embeds, iaa_embeds = ([], [], [], [])
        for i in range(0, self.layer_num):
            gnn_layer_embeds = torch_sparse.spmm(self.G_indices, self.G_values, self.A_in_shape[0], self.A_in_shape[1], all_embeds[i])
            u_embeds, i_embeds = torch.split(all_embeds[i], [self.user_num, self.item_num], 0)
            u_int_embeds = torch.softmax(u_embeds @ self.user_intent, dim=1) @ self.user_intent.T
            i_int_embeds = torch.softmax(i_embeds @ self.item_intent, dim=1) @ self.item_intent.T
            int_layer_embeds = torch.concat([u_int_embeds, i_int_embeds], dim=0)
            gnn_head_embeds = torch.index_select(gnn_layer_embeds, 0, self.all_h_list)
            gnn_tail_embeds = torch.index_select(gnn_layer_embeds, 0, self.all_t_list)
            int_head_embeds = torch.index_select(int_layer_embeds, 0, self.all_h_list)
            int_tail_embeds = torch.index_select(int_layer_embeds, 0, self.all_t_list)
            G_graph_indices, G_graph_values = self._adaptive_mask(gnn_head_embeds, gnn_tail_embeds)
            G_inten_indices, G_inten_values = self._adaptive_mask(int_head_embeds, int_tail_embeds)
            gaa_layer_embeds = torch_sparse.spmm(G_graph_indices, G_graph_values, self.A_in_shape[0], self.A_in_shape[1], all_embeds[i])
            iaa_layer_embeds = torch_sparse.spmm(G_inten_indices, G_inten_values, self.A_in_shape[0], self.A_in_shape[1], all_embeds[i])
            gnn_embeds.append(gnn_layer_embeds)
            int_embeds.append(int_layer_embeds)
            gaa_embeds.append(gaa_layer_embeds)
            iaa_embeds.append(iaa_layer_embeds)
            all_embeds.append(gnn_layer_embeds + int_layer_embeds + gaa_layer_embeds + iaa_layer_embeds + all_embeds[i])
        all_embeds = torch.stack(all_embeds, dim=1)
        all_embeds = torch.sum(all_embeds, dim=1, keepdim=False)
        user_embeds, item_embeds = torch.split(all_embeds, [self.user_num, self.item_num], 0)
        self.final_embeds = all_embeds
        return (user_embeds, item_embeds, gnn_embeds, int_embeds, gaa_embeds, iaa_embeds)

    def _pick_embeds(self, user_embeds, item_embeds, batch_data):
        ancs, poss, negs = batch_data
        anc_embeds = user_embeds[ancs]
        pos_embeds = item_embeds[poss]
        neg_embeds = item_embeds[negs]
        return (anc_embeds, pos_embeds, neg_embeds)

    def _cal_cl_loss(self, users, items, gnn_emb, int_emb, gaa_emb, iaa_emb):
        users = torch.unique(users)
        items = torch.unique(items)
        cl_loss = 0.0
        for i in range(len(gnn_emb)):
            u_gnn_embs, i_gnn_embs = torch.split(gnn_emb[i], [self.user_num, self.item_num], 0)
            u_int_embs, i_int_embs = torch.split(int_emb[i], [self.user_num, self.item_num], 0)
            u_gaa_embs, i_gaa_embs = torch.split(gaa_emb[i], [self.user_num, self.item_num], 0)
            u_iaa_embs, i_iaa_embs = torch.split(iaa_emb[i], [self.user_num, self.item_num], 0)
            u_gnn_embs = u_gnn_embs[users]
            u_int_embs = u_int_embs[users]
            u_gaa_embs = u_gaa_embs[users]
            u_iaa_embs = u_iaa_embs[users]
            i_gnn_embs = i_gnn_embs[items]
            i_int_embs = i_int_embs[items]
            i_gaa_embs = i_gaa_embs[items]
            i_iaa_embs = i_iaa_embs[items]
            cl_loss += cal_infonce_loss(u_gnn_embs, u_int_embs, u_int_embs, self.cl_temperature) / u_gnn_embs.shape[0]
            cl_loss += cal_infonce_loss(u_gnn_embs, u_gaa_embs, u_gaa_embs, self.cl_temperature) / u_gnn_embs.shape[0]
            cl_loss += cal_infonce_loss(u_gnn_embs, u_iaa_embs, u_iaa_embs, self.cl_temperature) / u_gnn_embs.shape[0]
            cl_loss += cal_infonce_loss(i_gnn_embs, i_int_embs, i_int_embs, self.cl_temperature) / u_gnn_embs.shape[0]
            cl_loss += cal_infonce_loss(i_gnn_embs, i_gaa_embs, i_gaa_embs, self.cl_temperature) / u_gnn_embs.shape[0]
            cl_loss += cal_infonce_loss(i_gnn_embs, i_iaa_embs, i_iaa_embs, self.cl_temperature) / u_gnn_embs.shape[0]
        return cl_loss

    def cal_loss(self, batch_data):
        self.is_training = True
        user_embeds, item_embeds, gnn_embeds, int_embeds, gaa_embeds, iaa_embeds = self.forward()
        ancs, poss, negs = batch_data
        anc_embeds = user_embeds[ancs]
        pos_embeds = item_embeds[poss]
        neg_embeds = item_embeds[negs]
        bpr_loss = cal_bpr_loss(anc_embeds, pos_embeds, neg_embeds) / anc_embeds.shape[0]
        reg_loss = self.reg_weight * reg_params(self)
        cl_loss = self.cl_weight * self._cal_cl_loss(ancs, poss, gnn_embeds, int_embeds, gaa_embeds, iaa_embeds)
        usrprf_embeds = self.mlp(self.usrprf_embeds)
        itmprf_embeds = self.mlp(self.itmprf_embeds)
        ancprf_embeds, posprf_embeds, negprf_embeds = self._pick_embeds(usrprf_embeds, itmprf_embeds, batch_data)
        kd_loss = cal_infonce_loss(anc_embeds, ancprf_embeds, usrprf_embeds, self.kd_temperature) + cal_infonce_loss(pos_embeds, posprf_embeds, posprf_embeds, self.kd_temperature) + cal_infonce_loss(neg_embeds, negprf_embeds, negprf_embeds, self.kd_temperature)
        kd_loss /= anc_embeds.shape[0]
        kd_loss *= self.kd_weight
        loss = bpr_loss + reg_loss + cl_loss + kd_loss
        losses = {'bpr_loss': bpr_loss, 'reg_loss': reg_loss, 'cl_loss': cl_loss, 'kd_loss': kd_loss}
        return (loss, losses)

    def full_predict(self, batch_data):
        user_embeds, item_embeds, _, _, _, _ = self.forward()
        self.is_training = False
        pck_users, train_mask = batch_data
        pck_users = pck_users.long()
        pck_user_embeds = user_embeds[pck_users]
        full_preds = pck_user_embeds @ item_embeds.T
        full_preds = self._mask_predict(full_preds, train_mask)
        return full_preds

def __init__(self, data_handler):
    super(DCCF_plus, self).__init__(data_handler)
    rows = data_handler.trn_mat.tocoo().row
    cols = data_handler.trn_mat.tocoo().col
    new_rows = np.concatenate([rows, cols + self.user_num], axis=0)
    new_cols = np.concatenate([cols + self.user_num, rows], axis=0)
    plain_adj = sp.coo_matrix((np.ones(len(new_rows)), (new_rows, new_cols)), shape=[self.user_num + self.item_num, self.user_num + self.item_num]).tocsr().tocoo()
    self.all_h_list = list(plain_adj.row)
    self.all_t_list = list(plain_adj.col)
    self.A_in_shape = plain_adj.shape
    self.A_indices = torch.tensor([self.all_h_list, self.all_t_list], dtype=torch.long).cuda()
    self.D_indices = torch.tensor([list(range(self.user_num + self.item_num)), list(range(self.user_num + self.item_num))], dtype=torch.long).cuda()
    self.all_h_list = torch.LongTensor(self.all_h_list).cuda()
    self.all_t_list = torch.LongTensor(self.all_t_list).cuda()
    self.G_indices, self.G_values = self._cal_sparse_adj()
    self.intent_num = configs['model']['intent_num']
    self.layer_num = self.hyper_config['layer_num']
    self.reg_weight = self.hyper_config['reg_weight']
    self.cl_weight = self.hyper_config['cl_weight']
    self.cl_temperature = self.hyper_config['cl_temperature']
    self.kd_weight = self.hyper_config['kd_weight']
    self.kd_temperature = self.hyper_config['kd_temperature']
    self.user_embeds = nn.Embedding(self.user_num, self.embedding_size)
    self.item_embeds = nn.Embedding(self.item_num, self.embedding_size)
    self.user_intent = torch.nn.Parameter(init(torch.empty(self.embedding_size, self.intent_num)), requires_grad=True)
    self.item_intent = torch.nn.Parameter(init(torch.empty(self.embedding_size, self.intent_num)), requires_grad=True)
    self.is_training = True
    self.final_embeds = False
    self.usrprf_embeds = torch.tensor(configs['usrprf_embeds']).float().cuda()
    self.itmprf_embeds = torch.tensor(configs['itmprf_embeds']).float().cuda()
    self.mlp = nn.Sequential(nn.Linear(self.usrprf_embeds.shape[1], (self.usrprf_embeds.shape[1] + self.embedding_size) // 2), nn.LeakyReLU(), nn.Linear((self.usrprf_embeds.shape[1] + self.embedding_size) // 2, self.embedding_size))
    self._init_weight()

def _init_weight(self):
    for m in self.mlp:
        if isinstance(m, nn.Linear):
            init(m.weight)
    init(self.user_embeds.weight)
    init(self.item_embeds.weight)

class SGL(LightGCN):

    def __init__(self, data_handler):
        super(SGL, self).__init__(data_handler)
        self.augmentation = configs['model']['augmentation']
        self.node_dropper = NodeDrop()
        self.cl_weight = self.hyper_config['cl_weight']
        self.temperature = self.hyper_config['temperature']

    def forward(self, adj=None, keep_rate=1.0):
        if adj is None:
            adj = self.adj
        if not self.is_training and self.final_embeds is not None:
            return (self.final_embeds[:self.user_num], self.final_embeds[self.user_num:])
        embeds = t.concat([self.user_embeds, self.item_embeds], axis=0)
        if self.augmentation == 'node_drop':
            embeds = self.node_dropper(embeds, keep_rate)
        embeds_list = [embeds]
        if self.augmentation == 'edge_drop':
            adj = self.edge_dropper(adj, keep_rate)
        for i in range(configs['model']['layer_num']):
            random_walk = self.augmentation == 'random_walk'
            tem_adj = adj if not random_walk else self.edge_dropper(tem_adj, keep_rate)
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
        keep_rate = configs['model']['keep_rate']
        user_embeds1, item_embeds1 = self.forward(self.adj, keep_rate)
        user_embeds2, item_embeds2 = self.forward(self.adj, keep_rate)
        user_embeds3, item_embeds3 = self.forward(self.adj, 1.0)
        anc_embeds1, pos_embeds1, neg_embeds1 = self._pick_embeds(user_embeds1, item_embeds1, batch_data)
        anc_embeds2, pos_embeds2, neg_embeds2 = self._pick_embeds(user_embeds2, item_embeds2, batch_data)
        anc_embeds3, pos_embeds3, neg_embeds3 = self._pick_embeds(user_embeds3, item_embeds3, batch_data)
        bpr_loss = cal_bpr_loss(anc_embeds3, pos_embeds3, neg_embeds3) / anc_embeds3.shape[0]
        cl_loss = cal_infonce_loss(anc_embeds1, anc_embeds2, user_embeds2, self.temperature) + cal_infonce_loss(pos_embeds1, pos_embeds2, item_embeds2, self.temperature) + cal_infonce_loss(neg_embeds1, neg_embeds2, item_embeds2, self.temperature)
        cl_loss /= anc_embeds1.shape[0]
        reg_loss = self.reg_weight * reg_params(self)
        cl_loss *= self.cl_weight
        loss = bpr_loss + reg_loss + cl_loss
        losses = {'bpr_loss': bpr_loss, 'reg_loss': reg_loss, 'cl_loss': cl_loss}
        return (loss, losses)

def __init__(self, data_handler):
    super(SGL, self).__init__(data_handler)
    self.augmentation = configs['model']['augmentation']
    self.node_dropper = NodeDrop()
    self.cl_weight = self.hyper_config['cl_weight']
    self.temperature = self.hyper_config['temperature']

class GCNLayer(nn.Module):

    def __init__(self, latdim):
        super(GCNLayer, self).__init__()
        self.W = nn.Parameter(init(t.empty(latdim, latdim)))

    def forward(self, adj, embeds):
        return t.spmm(adj, embeds)

def __init__(self, latdim):
    super(GCNLayer, self).__init__()
    self.W = nn.Parameter(init(t.empty(latdim, latdim)))

class GCCF_gene(BaseModel):

    def __init__(self, data_handler):
        super(GCCF_gene, self).__init__(data_handler)
        self.adj = data_handler.torch_adj
        self.layer_num = self.hyper_config['layer_num']
        self.reg_weight = self.hyper_config['reg_weight']
        self.mask_ratio = self.hyper_config['mask_ratio']
        self.recon_weight = self.hyper_config['recon_weight']
        self.re_temperature = self.hyper_config['re_temperature']
        self.user_embeds = nn.Parameter(init(t.empty(self.user_num, self.embedding_size)))
        self.item_embeds = nn.Parameter(init(t.empty(self.item_num, self.embedding_size)))
        self.gcnLayers = nn.Sequential(*[GCNLayer(self.embedding_size) for i in range(self.layer_num)])
        self.is_training = True
        usrprf_embeds = t.tensor(configs['usrprf_embeds']).float().cuda()
        itmprf_embeds = t.tensor(configs['itmprf_embeds']).float().cuda()
        self.prf_embeds = t.concat([usrprf_embeds, itmprf_embeds], dim=0)
        self.masker = NodeMask(self.mask_ratio, self.embedding_size)
        output_size = int((self.layer_num + 1) * self.embedding_size)
        self.mlp = nn.Sequential(nn.Linear(output_size, (self.prf_embeds.shape[1] + output_size) // 2), nn.LeakyReLU(), nn.Linear((self.prf_embeds.shape[1] + output_size) // 2, self.prf_embeds.shape[1]))
        self._init_weight()

    def _init_weight(self):
        for m in self.mlp:
            if isinstance(m, nn.Linear):
                init(m.weight)

    def _mask(self):
        embeds = t.concat([self.user_embeds, self.item_embeds], axis=0)
        masked_embeds, seeds = self.masker(embeds)
        return (masked_embeds[:self.user_num], masked_embeds[self.user_num:], seeds)

    def forward(self, adj=None, masked_user_embeds=None, masked_item_embeds=None):
        if adj is None:
            adj = self.adj
        if not self.is_training:
            return (self.final_embeds[:self.user_num], self.final_embeds[self.user_num:], None)
        if masked_user_embeds is None or masked_item_embeds is None:
            embeds = t.concat([self.user_embeds, self.item_embeds], axis=0)
        else:
            embeds = t.concat([masked_user_embeds, masked_item_embeds], axis=0)
        embeds_list = [embeds]
        for gcn in self.gcnLayers:
            embeds = gcn(adj, embeds_list[-1])
            embeds_list.append(embeds)
        embeds = t.concat(embeds_list, dim=-1)
        self.final_embeds = embeds
        return (embeds[:self.user_num], embeds[self.user_num:], embeds_list[-1])

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
        user_embeds, item_embeds, _ = self.forward(self.adj, masked_user_embeds, masked_item_embeds)
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
        user_embeds, item_embeds, _ = self.forward(self.adj)
        self.is_training = False
        pck_users, train_mask = batch_data
        pck_users = pck_users.long()
        pck_user_embeds = user_embeds[pck_users]
        full_preds = pck_user_embeds @ item_embeds.T
        full_preds = self._mask_predict(full_preds, train_mask)
        return full_preds

def __init__(self, data_handler):
    super(GCCF_gene, self).__init__(data_handler)
    self.adj = data_handler.torch_adj
    self.layer_num = self.hyper_config['layer_num']
    self.reg_weight = self.hyper_config['reg_weight']
    self.mask_ratio = self.hyper_config['mask_ratio']
    self.recon_weight = self.hyper_config['recon_weight']
    self.re_temperature = self.hyper_config['re_temperature']
    self.user_embeds = nn.Parameter(init(t.empty(self.user_num, self.embedding_size)))
    self.item_embeds = nn.Parameter(init(t.empty(self.item_num, self.embedding_size)))
    self.gcnLayers = nn.Sequential(*[GCNLayer(self.embedding_size) for i in range(self.layer_num)])
    self.is_training = True
    usrprf_embeds = t.tensor(configs['usrprf_embeds']).float().cuda()
    itmprf_embeds = t.tensor(configs['itmprf_embeds']).float().cuda()
    self.prf_embeds = t.concat([usrprf_embeds, itmprf_embeds], dim=0)
    self.masker = NodeMask(self.mask_ratio, self.embedding_size)
    output_size = int((self.layer_num + 1) * self.embedding_size)
    self.mlp = nn.Sequential(nn.Linear(output_size, (self.prf_embeds.shape[1] + output_size) // 2), nn.LeakyReLU(), nn.Linear((self.prf_embeds.shape[1] + output_size) // 2, self.prf_embeds.shape[1]))
    self._init_weight()

def _init_weight(self):
    for m in self.mlp:
        if isinstance(m, nn.Linear):
            init(m.weight)

class GCNLayer(nn.Module):

    def __init__(self, latdim):
        super(GCNLayer, self).__init__()
        self.W = nn.Parameter(init(t.empty(latdim, latdim)))

    def forward(self, adj, embeds):
        return t.spmm(adj, embeds)

def __init__(self, latdim):
    super(GCNLayer, self).__init__()
    self.W = nn.Parameter(init(t.empty(latdim, latdim)))

class GCCF(BaseModel):

    def __init__(self, data_handler):
        super(GCCF, self).__init__(data_handler)
        self.adj = data_handler.torch_adj
        self.layer_num = self.hyper_config['layer_num']
        self.reg_weight = self.hyper_config['reg_weight']
        self.user_embeds = nn.Parameter(init(t.empty(self.user_num, self.embedding_size)))
        self.item_embeds = nn.Parameter(init(t.empty(self.item_num, self.embedding_size)))
        self.gcnLayers = nn.Sequential(*[GCNLayer(self.embedding_size) for i in range(self.layer_num)])
        self.is_training = True

    def forward(self, adj=None):
        if adj is None:
            adj = self.adj
        if not self.is_training:
            return (self.final_embeds[:self.user_num], self.final_embeds[self.user_num:], None)
        embeds = t.concat([self.user_embeds, self.item_embeds], axis=0)
        embeds_list = [embeds]
        for gcn in self.gcnLayers:
            embeds = gcn(adj, embeds_list[-1])
            embeds_list.append(embeds)
        embeds = t.concat(embeds_list, dim=-1)
        self.final_embeds = embeds
        return (embeds[:self.user_num], embeds[self.user_num:], embeds_list[-1])

    def cal_loss(self, batch_data):
        self.is_training = True
        user_embeds, item_embeds, _ = self.forward(self.adj)
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
        user_embeds, item_embeds, _ = self.forward(self.adj)
        self.is_training = False
        pck_users, train_mask = batch_data
        pck_users = pck_users.long()
        pck_user_embeds = user_embeds[pck_users]
        full_preds = pck_user_embeds @ item_embeds.T
        full_preds = self._mask_predict(full_preds, train_mask)
        return full_preds

def __init__(self, data_handler):
    super(GCCF, self).__init__(data_handler)
    self.adj = data_handler.torch_adj
    self.layer_num = self.hyper_config['layer_num']
    self.reg_weight = self.hyper_config['reg_weight']
    self.user_embeds = nn.Parameter(init(t.empty(self.user_num, self.embedding_size)))
    self.item_embeds = nn.Parameter(init(t.empty(self.item_num, self.embedding_size)))
    self.gcnLayers = nn.Sequential(*[GCNLayer(self.embedding_size) for i in range(self.layer_num)])
    self.is_training = True

class AutoCF(BaseModel):

    def __init__(self, data_handler):
        super(AutoCF, self).__init__(data_handler)
        self.user_embeds = nn.Parameter(init(t.empty(self.user_num, self.embedding_size)))
        self.item_embeds = nn.Parameter(init(t.empty(self.item_num, self.embedding_size)))
        self.adj = data_handler.torch_adj
        self.all_one_adj = self.make_all_one_adj()
        self.gt_layer = configs['model']['gt_layer']
        self.gcn_layer = self.hyper_config['gcn_layer']
        self.reg_weight = self.hyper_config['reg_weight']
        self.ssl_reg = self.hyper_config['ssl_reg']
        self.gcnLayers = nn.Sequential(*[GCNLayer() for i in range(self.gcn_layer)])
        self.gtLayers = nn.Sequential(*[GTLayer() for i in range(self.gt_layer)])
        self.masker = RandomMaskSubgraphs()
        self.sampler = LocalGraph()

    def make_all_one_adj(self):
        idxs = self.adj._indices()
        vals = t.ones_like(self.adj._values())
        shape = self.adj.shape
        return t.sparse.FloatTensor(idxs, vals, shape).cuda()

    def get_ego_embeds(self):
        return t.concat([self.user_embeds, self.item_embeds], axis=0)

    def sample_subgraphs(self):
        return self.sampler(self.all_one_adj, self.get_ego_embeds())

    def mask_subgraphs(self, seeds):
        return self.masker(self.adj, seeds)

    def forward(self, encoder_adj, decoder_adj=None):
        embeds = t.concat([self.user_embeds, self.item_embeds], axis=0)
        embedsLst = [embeds]
        for i, gcn in enumerate(self.gcnLayers):
            embeds = gcn(encoder_adj, embedsLst[-1])
            embedsLst.append(embeds)
        if decoder_adj is not None:
            for gt in self.gtLayers:
                embeds = gt(decoder_adj, embedsLst[-1])
                embedsLst.append(embeds)
        embeds = sum(embedsLst)
        return (embeds[:self.user_num], embeds[self.user_num:])

    def contrast(self, nodes, allEmbeds, allEmbeds2=None):
        if allEmbeds2 is not None:
            pckEmbeds = allEmbeds[nodes]
            scores = t.log(t.exp(pckEmbeds @ allEmbeds2.T).sum(-1)).mean()
        else:
            uniqNodes = t.unique(nodes)
            pckEmbeds = allEmbeds[uniqNodes]
            scores = t.log(t.exp(pckEmbeds @ allEmbeds.T).sum(-1)).mean()
        return scores

    def cal_loss(self, batch_data, encoder_adj, decoder_adj):
        user_embeds, item_embeds = self.forward(encoder_adj, decoder_adj)
        ancs, poss, _ = batch_data
        anc_embeds = user_embeds[ancs]
        pos_embeds = item_embeds[poss]
        rec_loss = (-t.sum(anc_embeds * pos_embeds, dim=-1)).mean()
        reg_loss = reg_params(self) * self.reg_weight
        cl_loss = (self.contrast(ancs, user_embeds) + self.contrast(poss, item_embeds)) * self.ssl_reg + self.contrast(ancs, user_embeds, item_embeds)
        loss = rec_loss + reg_loss + cl_loss
        losses = {'rec_loss': rec_loss, 'reg_loss': reg_loss, 'cl_loss': cl_loss}
        return (loss, losses)

    def full_predict(self, batch_data):
        user_embeds, item_embeds = self.forward(self.adj, self.adj)
        pck_users, train_mask = batch_data
        pck_users = pck_users.long()
        pck_user_embeds = user_embeds[pck_users]
        full_preds = pck_user_embeds @ item_embeds.T
        full_preds = self._mask_predict(full_preds, train_mask)
        return full_preds

def __init__(self, data_handler):
    super(AutoCF, self).__init__(data_handler)
    self.user_embeds = nn.Parameter(init(t.empty(self.user_num, self.embedding_size)))
    self.item_embeds = nn.Parameter(init(t.empty(self.item_num, self.embedding_size)))
    self.adj = data_handler.torch_adj
    self.all_one_adj = self.make_all_one_adj()
    self.gt_layer = configs['model']['gt_layer']
    self.gcn_layer = self.hyper_config['gcn_layer']
    self.reg_weight = self.hyper_config['reg_weight']
    self.ssl_reg = self.hyper_config['ssl_reg']
    self.gcnLayers = nn.Sequential(*[GCNLayer() for i in range(self.gcn_layer)])
    self.gtLayers = nn.Sequential(*[GTLayer() for i in range(self.gt_layer)])
    self.masker = RandomMaskSubgraphs()
    self.sampler = LocalGraph()

class GCNLayer(nn.Module):

    def __init__(self):
        super(GCNLayer, self).__init__()

    def forward(self, adj, embeds):
        return t.spmm(adj, embeds)

def __init__(self):
    super(GCNLayer, self).__init__()

class GTLayer(nn.Module):

    def __init__(self):
        super(GTLayer, self).__init__()
        self.head_num = configs['model']['head_num']
        self.embedding_size = configs['model']['embedding_size']
        self.qTrans = nn.Parameter(init(t.empty(self.embedding_size, self.embedding_size)))
        self.kTrans = nn.Parameter(init(t.empty(self.embedding_size, self.embedding_size)))
        self.vTrans = nn.Parameter(init(t.empty(self.embedding_size, self.embedding_size)))

    def forward(self, adj, embeds):
        indices = adj._indices()
        rows, cols = (indices[0, :], indices[1, :])
        rowEmbeds = embeds[rows]
        colEmbeds = embeds[cols]
        qEmbeds = (rowEmbeds @ self.qTrans).view([-1, self.head_num, self.embedding_size // self.head_num])
        kEmbeds = (colEmbeds @ self.kTrans).view([-1, self.head_num, self.embedding_size // self.head_num])
        vEmbeds = (colEmbeds @ self.vTrans).view([-1, self.head_num, self.embedding_size // self.head_num])
        att = t.einsum('ehd, ehd -> eh', qEmbeds, kEmbeds)
        att = t.clamp(att, -10.0, 10.0)
        expAtt = t.exp(att)
        tem = t.zeros([adj.shape[0], self.head_num]).cuda()
        attNorm = tem.index_add_(0, rows, expAtt)[rows]
        att = expAtt / (attNorm + 1e-08)
        resEmbeds = t.einsum('eh, ehd -> ehd', att, vEmbeds).view([-1, self.embedding_size])
        tem = t.zeros([adj.shape[0], self.embedding_size]).cuda()
        resEmbeds = tem.index_add_(0, rows, resEmbeds)
        return resEmbeds

def __init__(self):
    super(GTLayer, self).__init__()
    self.head_num = configs['model']['head_num']
    self.embedding_size = configs['model']['embedding_size']
    self.qTrans = nn.Parameter(init(t.empty(self.embedding_size, self.embedding_size)))
    self.kTrans = nn.Parameter(init(t.empty(self.embedding_size, self.embedding_size)))
    self.vTrans = nn.Parameter(init(t.empty(self.embedding_size, self.embedding_size)))

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

def __init__(self):
    super(LocalGraph, self).__init__()
    self.seed_num = configs['model']['seed_num']

class RandomMaskSubgraphs(nn.Module):

    def __init__(self):
        super(RandomMaskSubgraphs, self).__init__()
        self.flag = False
        self.mask_depth = configs['model']['mask_depth']
        self.keep_rate = configs['model']['keep_rate']
        self.user_num = configs['data']['user_num']
        self.item_num = configs['data']['item_num']

    def normalizeAdj(self, adj):
        degree = t.pow(t.sparse.sum(adj, dim=1).to_dense() + 1e-12, -0.5)
        newRows, newCols = (adj._indices()[0, :], adj._indices()[1, :])
        rowNorm, colNorm = (degree[newRows], degree[newCols])
        newVals = adj._values() * rowNorm * colNorm
        return t.sparse.FloatTensor(adj._indices(), newVals, adj.shape)

    def forward(self, adj, seeds):
        rows = adj._indices()[0, :]
        cols = adj._indices()[1, :]
        maskNodes = [seeds]
        for i in range(self.mask_depth):
            curSeeds = seeds if i == 0 else nxtSeeds
            nxtSeeds = list()
            for seed in curSeeds:
                rowIdct = rows == seed
                colIdct = cols == seed
                idct = t.logical_or(rowIdct, colIdct)
                if i != self.mask_depth - 1:
                    mskRows = rows[idct]
                    mskCols = cols[idct]
                    nxtSeeds.append(mskRows)
                    nxtSeeds.append(mskCols)
                rows = rows[t.logical_not(idct)]
                cols = cols[t.logical_not(idct)]
            if len(nxtSeeds) > 0:
                nxtSeeds = t.unique(t.concat(nxtSeeds))
                maskNodes.append(nxtSeeds)
        sampNum = int((self.user_num + self.item_num) * self.keep_rate)
        sampedNodes = t.randint(self.user_num + self.item_num, size=[sampNum]).cuda()
        if self.flag == False:
            l1 = adj._values().shape[0]
            l2 = rows.shape[0]
            print('-----')
            print('LENGTH CHANGE', '%.2f' % (l2 / l1), l2, l1)
            tem = t.unique(t.concat(maskNodes))
            print('Original SAMPLED NODES', '%.2f' % (tem.shape[0] / (self.user_num + self.item_num)), tem.shape[0], self.user_num + self.item_num)
        maskNodes.append(sampedNodes)
        maskNodes = t.unique(t.concat(maskNodes))
        if self.flag == False:
            print('AUGMENTED SAMPLED NODES', '%.2f' % (maskNodes.shape[0] / (self.user_num + self.item_num)), maskNodes.shape[0], self.user_num + self.item_num)
            self.flag = True
            print('-----')
        encoder_adj = self.normalizeAdj(t.sparse.FloatTensor(t.stack([rows, cols], dim=0), t.ones_like(rows).cuda(), adj.shape))
        temNum = maskNodes.shape[0]
        temRows = maskNodes[t.randint(temNum, size=[adj._values().shape[0]]).cuda()]
        temCols = maskNodes[t.randint(temNum, size=[adj._values().shape[0]]).cuda()]
        newRows = t.concat([temRows, temCols, t.arange(self.user_num + self.item_num).cuda(), rows])
        newCols = t.concat([temCols, temRows, t.arange(self.user_num + self.item_num).cuda(), cols])
        hashVal = newRows * (self.user_num + self.item_num) + newCols
        hashVal = t.unique(hashVal)
        newCols = hashVal % (self.user_num + self.item_num)
        newRows = ((hashVal - newCols) / (self.user_num + self.item_num)).long()
        decoder_adj = t.sparse.FloatTensor(t.stack([newRows, newCols], dim=0), t.ones_like(newRows).cuda().float(), adj.shape)
        return (encoder_adj, decoder_adj)

def __init__(self):
    super(RandomMaskSubgraphs, self).__init__()
    self.flag = False
    self.mask_depth = configs['model']['mask_depth']
    self.keep_rate = configs['model']['keep_rate']
    self.user_num = configs['data']['user_num']
    self.item_num = configs['data']['item_num']

class DCCF(BaseModel):

    def __init__(self, data_handler):
        super(DCCF, self).__init__(data_handler)
        rows = data_handler.trn_mat.tocoo().row
        cols = data_handler.trn_mat.tocoo().col
        new_rows = np.concatenate([rows, cols + self.user_num], axis=0)
        new_cols = np.concatenate([cols + self.user_num, rows], axis=0)
        plain_adj = sp.coo_matrix((np.ones(len(new_rows)), (new_rows, new_cols)), shape=[self.user_num + self.item_num, self.user_num + self.item_num]).tocsr().tocoo()
        self.all_h_list = list(plain_adj.row)
        self.all_t_list = list(plain_adj.col)
        self.A_in_shape = plain_adj.shape
        self.A_indices = torch.tensor([self.all_h_list, self.all_t_list], dtype=torch.long).cuda()
        self.D_indices = torch.tensor([list(range(self.user_num + self.item_num)), list(range(self.user_num + self.item_num))], dtype=torch.long).cuda()
        self.all_h_list = torch.LongTensor(self.all_h_list).cuda()
        self.all_t_list = torch.LongTensor(self.all_t_list).cuda()
        self.G_indices, self.G_values = self._cal_sparse_adj()
        self.intent_num = configs['model']['intent_num']
        self.layer_num = self.hyper_config['layer_num']
        self.reg_weight = self.hyper_config['reg_weight']
        self.cl_weight = self.hyper_config['cl_weight']
        self.temperature = self.hyper_config['temperature']
        self.user_embeds = nn.Embedding(self.user_num, self.embedding_size)
        self.item_embeds = nn.Embedding(self.item_num, self.embedding_size)
        self.user_intent = torch.nn.Parameter(init(torch.empty(self.embedding_size, self.intent_num)), requires_grad=True)
        self.item_intent = torch.nn.Parameter(init(torch.empty(self.embedding_size, self.intent_num)), requires_grad=True)
        self.is_training = True
        self.final_embeds = False
        self._init_weight()

    def _init_weight(self):
        init(self.user_embeds.weight)
        init(self.item_embeds.weight)

    def _cal_sparse_adj(self):
        A_values = torch.ones(size=(len(self.all_h_list), 1)).view(-1).cuda()
        A_tensor = torch_sparse.SparseTensor(row=self.all_h_list, col=self.all_t_list, value=A_values, sparse_sizes=self.A_in_shape).cuda()
        D_values = A_tensor.sum(dim=1).pow(-0.5)
        G_indices, G_values = torch_sparse.spspmm(self.D_indices, D_values, self.A_indices, A_values, self.A_in_shape[0], self.A_in_shape[1], self.A_in_shape[1])
        G_indices, G_values = torch_sparse.spspmm(G_indices, G_values, self.D_indices, D_values, self.A_in_shape[0], self.A_in_shape[1], self.A_in_shape[1])
        return (G_indices, G_values)

    def _adaptive_mask(self, head_embeddings, tail_embeddings):
        head_embeddings = torch.nn.functional.normalize(head_embeddings)
        tail_embeddings = torch.nn.functional.normalize(tail_embeddings)
        edge_alpha = (torch.sum(head_embeddings * tail_embeddings, dim=1).view(-1) + 1) / 2
        A_tensor = torch_sparse.SparseTensor(row=self.all_h_list, col=self.all_t_list, value=edge_alpha, sparse_sizes=self.A_in_shape).cuda()
        D_scores_inv = A_tensor.sum(dim=1).pow(-1).nan_to_num(0, 0, 0).view(-1)
        G_indices = torch.stack([self.all_h_list, self.all_t_list], dim=0)
        G_values = D_scores_inv[self.all_h_list] * edge_alpha
        return (G_indices, G_values)

    def forward(self):
        if not self.is_training and self.final_embeds is not None:
            return (self.final_embeds[:self.user_num], self.final_embeds[self.user_num:], None, None, None, None)
        all_embeds = [torch.concat([self.user_embeds.weight, self.item_embeds.weight], dim=0)]
        gnn_embeds, int_embeds, gaa_embeds, iaa_embeds = ([], [], [], [])
        for i in range(0, self.layer_num):
            gnn_layer_embeds = torch_sparse.spmm(self.G_indices, self.G_values, self.A_in_shape[0], self.A_in_shape[1], all_embeds[i])
            u_embeds, i_embeds = torch.split(all_embeds[i], [self.user_num, self.item_num], 0)
            u_int_embeds = torch.softmax(u_embeds @ self.user_intent, dim=1) @ self.user_intent.T
            i_int_embeds = torch.softmax(i_embeds @ self.item_intent, dim=1) @ self.item_intent.T
            int_layer_embeds = torch.concat([u_int_embeds, i_int_embeds], dim=0)
            gnn_head_embeds = torch.index_select(gnn_layer_embeds, 0, self.all_h_list)
            gnn_tail_embeds = torch.index_select(gnn_layer_embeds, 0, self.all_t_list)
            int_head_embeds = torch.index_select(int_layer_embeds, 0, self.all_h_list)
            int_tail_embeds = torch.index_select(int_layer_embeds, 0, self.all_t_list)
            G_graph_indices, G_graph_values = self._adaptive_mask(gnn_head_embeds, gnn_tail_embeds)
            G_inten_indices, G_inten_values = self._adaptive_mask(int_head_embeds, int_tail_embeds)
            gaa_layer_embeds = torch_sparse.spmm(G_graph_indices, G_graph_values, self.A_in_shape[0], self.A_in_shape[1], all_embeds[i])
            iaa_layer_embeds = torch_sparse.spmm(G_inten_indices, G_inten_values, self.A_in_shape[0], self.A_in_shape[1], all_embeds[i])
            gnn_embeds.append(gnn_layer_embeds)
            int_embeds.append(int_layer_embeds)
            gaa_embeds.append(gaa_layer_embeds)
            iaa_embeds.append(iaa_layer_embeds)
            all_embeds.append(gnn_layer_embeds + int_layer_embeds + gaa_layer_embeds + iaa_layer_embeds + all_embeds[i])
        all_embeds = torch.stack(all_embeds, dim=1)
        all_embeds = torch.sum(all_embeds, dim=1, keepdim=False)
        user_embeds, item_embeds = torch.split(all_embeds, [self.user_num, self.item_num], 0)
        self.final_embeds = all_embeds
        return (user_embeds, item_embeds, gnn_embeds, int_embeds, gaa_embeds, iaa_embeds)

    def _cal_cl_loss(self, users, items, gnn_emb, int_emb, gaa_emb, iaa_emb):
        users = torch.unique(users)
        items = torch.unique(items)
        cl_loss = 0.0
        for i in range(len(gnn_emb)):
            u_gnn_embs, i_gnn_embs = torch.split(gnn_emb[i], [self.user_num, self.item_num], 0)
            u_int_embs, i_int_embs = torch.split(int_emb[i], [self.user_num, self.item_num], 0)
            u_gaa_embs, i_gaa_embs = torch.split(gaa_emb[i], [self.user_num, self.item_num], 0)
            u_iaa_embs, i_iaa_embs = torch.split(iaa_emb[i], [self.user_num, self.item_num], 0)
            u_gnn_embs = u_gnn_embs[users]
            u_int_embs = u_int_embs[users]
            u_gaa_embs = u_gaa_embs[users]
            u_iaa_embs = u_iaa_embs[users]
            i_gnn_embs = i_gnn_embs[items]
            i_int_embs = i_int_embs[items]
            i_gaa_embs = i_gaa_embs[items]
            i_iaa_embs = i_iaa_embs[items]
            cl_loss += cal_infonce_loss(u_gnn_embs, u_int_embs, u_int_embs, self.temperature) / u_gnn_embs.shape[0]
            cl_loss += cal_infonce_loss(u_gnn_embs, u_gaa_embs, u_gaa_embs, self.temperature) / u_gnn_embs.shape[0]
            cl_loss += cal_infonce_loss(u_gnn_embs, u_iaa_embs, u_iaa_embs, self.temperature) / u_gnn_embs.shape[0]
            cl_loss += cal_infonce_loss(i_gnn_embs, i_int_embs, i_int_embs, self.temperature) / u_gnn_embs.shape[0]
            cl_loss += cal_infonce_loss(i_gnn_embs, i_gaa_embs, i_gaa_embs, self.temperature) / u_gnn_embs.shape[0]
            cl_loss += cal_infonce_loss(i_gnn_embs, i_iaa_embs, i_iaa_embs, self.temperature) / u_gnn_embs.shape[0]
        return cl_loss

    def cal_loss(self, batch_data):
        self.is_training = True
        user_embeds, item_embeds, gnn_embeds, int_embeds, gaa_embeds, iaa_embeds = self.forward()
        ancs, poss, negs = batch_data
        anc_embeds = user_embeds[ancs]
        pos_embeds = item_embeds[poss]
        neg_embeds = item_embeds[negs]
        bpr_loss = cal_bpr_loss(anc_embeds, pos_embeds, neg_embeds) / anc_embeds.shape[0]
        reg_loss = self.reg_weight * reg_params(self)
        cl_loss = self.cl_weight * self._cal_cl_loss(ancs, poss, gnn_embeds, int_embeds, gaa_embeds, iaa_embeds)
        loss = bpr_loss + reg_loss + cl_loss
        losses = {'bpr_loss': bpr_loss, 'reg_loss': reg_loss, 'cl_loss': cl_loss}
        return (loss, losses)

    def full_predict(self, batch_data):
        user_embeds, item_embeds, _, _, _, _ = self.forward()
        self.is_training = False
        pck_users, train_mask = batch_data
        pck_users = pck_users.long()
        pck_user_embeds = user_embeds[pck_users]
        full_preds = pck_user_embeds @ item_embeds.T
        full_preds = self._mask_predict(full_preds, train_mask)
        return full_preds

def __init__(self, data_handler):
    super(DCCF, self).__init__(data_handler)
    rows = data_handler.trn_mat.tocoo().row
    cols = data_handler.trn_mat.tocoo().col
    new_rows = np.concatenate([rows, cols + self.user_num], axis=0)
    new_cols = np.concatenate([cols + self.user_num, rows], axis=0)
    plain_adj = sp.coo_matrix((np.ones(len(new_rows)), (new_rows, new_cols)), shape=[self.user_num + self.item_num, self.user_num + self.item_num]).tocsr().tocoo()
    self.all_h_list = list(plain_adj.row)
    self.all_t_list = list(plain_adj.col)
    self.A_in_shape = plain_adj.shape
    self.A_indices = torch.tensor([self.all_h_list, self.all_t_list], dtype=torch.long).cuda()
    self.D_indices = torch.tensor([list(range(self.user_num + self.item_num)), list(range(self.user_num + self.item_num))], dtype=torch.long).cuda()
    self.all_h_list = torch.LongTensor(self.all_h_list).cuda()
    self.all_t_list = torch.LongTensor(self.all_t_list).cuda()
    self.G_indices, self.G_values = self._cal_sparse_adj()
    self.intent_num = configs['model']['intent_num']
    self.layer_num = self.hyper_config['layer_num']
    self.reg_weight = self.hyper_config['reg_weight']
    self.cl_weight = self.hyper_config['cl_weight']
    self.temperature = self.hyper_config['temperature']
    self.user_embeds = nn.Embedding(self.user_num, self.embedding_size)
    self.item_embeds = nn.Embedding(self.item_num, self.embedding_size)
    self.user_intent = torch.nn.Parameter(init(torch.empty(self.embedding_size, self.intent_num)), requires_grad=True)
    self.item_intent = torch.nn.Parameter(init(torch.empty(self.embedding_size, self.intent_num)), requires_grad=True)
    self.is_training = True
    self.final_embeds = False
    self._init_weight()

def _init_weight(self):
    init(self.user_embeds.weight)
    init(self.item_embeds.weight)

class SGL_gene(LightGCN):

    def __init__(self, data_handler):
        super(SGL_gene, self).__init__(data_handler)
        self.augmentation = configs['model']['augmentation']
        self.node_dropper = NodeDrop()
        self.cl_weight = self.hyper_config['cl_weight']
        self.cl_temperature = self.hyper_config['cl_temperature']
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
        if self.augmentation == 'node_drop':
            embeds = self.node_dropper(embeds, keep_rate)
        embeds_list = [embeds]
        if self.augmentation == 'edge_drop':
            adj = self.edge_dropper(adj, keep_rate)
        for i in range(configs['model']['layer_num']):
            random_walk = self.augmentation == 'random_walk'
            tem_adj = adj if not random_walk else self.edge_dropper(tem_adj, keep_rate)
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
        keep_rate = configs['model']['keep_rate']
        user_embeds1, item_embeds1 = self.forward(self.adj, keep_rate, masked_user_embeds, masked_item_embeds)
        user_embeds2, item_embeds2 = self.forward(self.adj, keep_rate, masked_user_embeds, masked_item_embeds)
        user_embeds3, item_embeds3 = self.forward(self.adj, 1.0, masked_user_embeds, masked_item_embeds)
        anc_embeds1, pos_embeds1, neg_embeds1 = self._pick_embeds(user_embeds1, item_embeds1, batch_data)
        anc_embeds2, pos_embeds2, neg_embeds2 = self._pick_embeds(user_embeds2, item_embeds2, batch_data)
        anc_embeds3, pos_embeds3, neg_embeds3 = self._pick_embeds(user_embeds3, item_embeds3, batch_data)
        bpr_loss = cal_bpr_loss(anc_embeds3, pos_embeds3, neg_embeds3) / anc_embeds3.shape[0]
        cl_loss = cal_infonce_loss(anc_embeds1, anc_embeds2, user_embeds2, self.cl_temperature) + cal_infonce_loss(pos_embeds1, pos_embeds2, item_embeds2, self.cl_temperature) + cal_infonce_loss(neg_embeds1, neg_embeds2, item_embeds2, self.cl_temperature)
        cl_loss /= anc_embeds1.shape[0]
        cl_loss *= self.cl_weight
        reg_loss = self.reg_weight * reg_params(self)
        recon_loss = self.recon_weight * self._reconstruction(t.concat([user_embeds3, item_embeds3], axis=0), seeds)
        loss = bpr_loss + reg_loss + cl_loss + recon_loss
        losses = {'bpr_loss': bpr_loss, 'reg_loss': reg_loss, 'cl_loss': cl_loss, 'recon_loss': recon_loss}
        return (loss, losses)

def __init__(self, data_handler):
    super(SGL_gene, self).__init__(data_handler)
    self.augmentation = configs['model']['augmentation']
    self.node_dropper = NodeDrop()
    self.cl_weight = self.hyper_config['cl_weight']
    self.cl_temperature = self.hyper_config['cl_temperature']
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

class AutoCF_plus(BaseModel):

    def __init__(self, data_handler):
        super(AutoCF_plus, self).__init__(data_handler)
        self.user_embeds = nn.Parameter(init(t.empty(self.user_num, self.embedding_size)))
        self.item_embeds = nn.Parameter(init(t.empty(self.item_num, self.embedding_size)))
        self.adj = data_handler.torch_adj
        self.all_one_adj = self.make_all_one_adj()
        self.gt_layer = configs['model']['gt_layer']
        self.gcn_layer = self.hyper_config['gcn_layer']
        self.reg_weight = self.hyper_config['reg_weight']
        self.ssl_reg = self.hyper_config['ssl_reg']
        self.kd_weight = self.hyper_config['kd_weight']
        self.kd_temperature = self.hyper_config['kd_temperature']
        self.gcnLayers = nn.Sequential(*[GCNLayer() for i in range(self.gcn_layer)])
        self.gtLayers = nn.Sequential(*[GTLayer() for i in range(self.gt_layer)])
        self.masker = RandomMaskSubgraphs()
        self.sampler = LocalGraph()
        self.usrprf_embeds = t.tensor(configs['usrprf_embeds']).float().cuda()
        self.itmprf_embeds = t.tensor(configs['itmprf_embeds']).float().cuda()
        self.mlp = nn.Sequential(nn.Linear(self.usrprf_embeds.shape[1], (self.usrprf_embeds.shape[1] + self.embedding_size) // 2), nn.LeakyReLU(), nn.Linear((self.usrprf_embeds.shape[1] + self.embedding_size) // 2, self.embedding_size))
        self._init_weight()

    def _init_weight(self):
        for m in self.mlp:
            if isinstance(m, nn.Linear):
                init(m.weight)

    def make_all_one_adj(self):
        idxs = self.adj._indices()
        vals = t.ones_like(self.adj._values())
        shape = self.adj.shape
        return t.sparse.FloatTensor(idxs, vals, shape).cuda()

    def get_ego_embeds(self):
        return t.concat([self.user_embeds, self.item_embeds], axis=0)

    def sample_subgraphs(self):
        return self.sampler(self.all_one_adj, self.get_ego_embeds())

    def mask_subgraphs(self, seeds):
        return self.masker(self.adj, seeds)

    def forward(self, encoder_adj, decoder_adj=None):
        embeds = t.concat([self.user_embeds, self.item_embeds], axis=0)
        embedsLst = [embeds]
        for i, gcn in enumerate(self.gcnLayers):
            embeds = gcn(encoder_adj, embedsLst[-1])
            embedsLst.append(embeds)
        if decoder_adj is not None:
            for gt in self.gtLayers:
                embeds = gt(decoder_adj, embedsLst[-1])
                embedsLst.append(embeds)
        embeds = sum(embedsLst)
        return (embeds[:self.user_num], embeds[self.user_num:])

    def contrast(self, nodes, allEmbeds, allEmbeds2=None):
        if allEmbeds2 is not None:
            pckEmbeds = allEmbeds[nodes]
            scores = t.log(t.exp(pckEmbeds @ allEmbeds2.T).sum(-1)).mean()
        else:
            uniqNodes = t.unique(nodes)
            pckEmbeds = allEmbeds[uniqNodes]
            scores = t.log(t.exp(pckEmbeds @ allEmbeds.T).sum(-1)).mean()
        return scores

    def cal_loss(self, batch_data, encoder_adj, decoder_adj):
        user_embeds, item_embeds = self.forward(encoder_adj, decoder_adj)
        ancs, poss, _ = batch_data
        anc_embeds = user_embeds[ancs]
        pos_embeds = item_embeds[poss]
        rec_loss = (-t.sum(anc_embeds * pos_embeds, dim=-1)).mean()
        reg_loss = reg_params(self) * self.reg_weight
        cl_loss = (self.contrast(ancs, user_embeds) + self.contrast(poss, item_embeds)) * self.ssl_reg + self.contrast(ancs, user_embeds, item_embeds)
        usrprf_embeds = self.mlp(self.usrprf_embeds)
        itmprf_embeds = self.mlp(self.itmprf_embeds)
        ancprf_embeds = usrprf_embeds[ancs]
        posprf_embeds = itmprf_embeds[poss]
        kd_loss = cal_infonce_loss(anc_embeds, ancprf_embeds, usrprf_embeds, self.kd_temperature) + cal_infonce_loss(pos_embeds, posprf_embeds, posprf_embeds, self.kd_temperature)
        kd_loss /= anc_embeds.shape[0]
        kd_loss *= self.kd_weight
        loss = rec_loss + reg_loss + cl_loss + kd_loss
        losses = {'rec_loss': rec_loss, 'reg_loss': reg_loss, 'cl_loss': cl_loss, 'kd_loss': kd_loss}
        return (loss, losses)

    def full_predict(self, batch_data):
        user_embeds, item_embeds = self.forward(self.adj, self.adj)
        pck_users, train_mask = batch_data
        pck_users = pck_users.long()
        pck_user_embeds = user_embeds[pck_users]
        full_preds = pck_user_embeds @ item_embeds.T
        full_preds = self._mask_predict(full_preds, train_mask)
        return full_preds

def __init__(self, data_handler):
    super(AutoCF_plus, self).__init__(data_handler)
    self.user_embeds = nn.Parameter(init(t.empty(self.user_num, self.embedding_size)))
    self.item_embeds = nn.Parameter(init(t.empty(self.item_num, self.embedding_size)))
    self.adj = data_handler.torch_adj
    self.all_one_adj = self.make_all_one_adj()
    self.gt_layer = configs['model']['gt_layer']
    self.gcn_layer = self.hyper_config['gcn_layer']
    self.reg_weight = self.hyper_config['reg_weight']
    self.ssl_reg = self.hyper_config['ssl_reg']
    self.kd_weight = self.hyper_config['kd_weight']
    self.kd_temperature = self.hyper_config['kd_temperature']
    self.gcnLayers = nn.Sequential(*[GCNLayer() for i in range(self.gcn_layer)])
    self.gtLayers = nn.Sequential(*[GTLayer() for i in range(self.gt_layer)])
    self.masker = RandomMaskSubgraphs()
    self.sampler = LocalGraph()
    self.usrprf_embeds = t.tensor(configs['usrprf_embeds']).float().cuda()
    self.itmprf_embeds = t.tensor(configs['itmprf_embeds']).float().cuda()
    self.mlp = nn.Sequential(nn.Linear(self.usrprf_embeds.shape[1], (self.usrprf_embeds.shape[1] + self.embedding_size) // 2), nn.LeakyReLU(), nn.Linear((self.usrprf_embeds.shape[1] + self.embedding_size) // 2, self.embedding_size))
    self._init_weight()

def _init_weight(self):
    for m in self.mlp:
        if isinstance(m, nn.Linear):
            init(m.weight)

class GCNLayer(nn.Module):

    def __init__(self):
        super(GCNLayer, self).__init__()

    def forward(self, adj, embeds):
        return t.spmm(adj, embeds)

def __init__(self):
    super(GCNLayer, self).__init__()

class GTLayer(nn.Module):

    def __init__(self):
        super(GTLayer, self).__init__()
        self.head_num = configs['model']['head_num']
        self.embedding_size = configs['model']['embedding_size']
        self.qTrans = nn.Parameter(init(t.empty(self.embedding_size, self.embedding_size)))
        self.kTrans = nn.Parameter(init(t.empty(self.embedding_size, self.embedding_size)))
        self.vTrans = nn.Parameter(init(t.empty(self.embedding_size, self.embedding_size)))

    def forward(self, adj, embeds):
        indices = adj._indices()
        rows, cols = (indices[0, :], indices[1, :])
        rowEmbeds = embeds[rows]
        colEmbeds = embeds[cols]
        qEmbeds = (rowEmbeds @ self.qTrans).view([-1, self.head_num, self.embedding_size // self.head_num])
        kEmbeds = (colEmbeds @ self.kTrans).view([-1, self.head_num, self.embedding_size // self.head_num])
        vEmbeds = (colEmbeds @ self.vTrans).view([-1, self.head_num, self.embedding_size // self.head_num])
        att = t.einsum('ehd, ehd -> eh', qEmbeds, kEmbeds)
        att = t.clamp(att, -10.0, 10.0)
        expAtt = t.exp(att)
        tem = t.zeros([adj.shape[0], self.head_num]).cuda()
        attNorm = tem.index_add_(0, rows, expAtt)[rows]
        att = expAtt / (attNorm + 1e-08)
        resEmbeds = t.einsum('eh, ehd -> ehd', att, vEmbeds).view([-1, self.embedding_size])
        tem = t.zeros([adj.shape[0], self.embedding_size]).cuda()
        resEmbeds = tem.index_add_(0, rows, resEmbeds)
        return resEmbeds

def __init__(self):
    super(GTLayer, self).__init__()
    self.head_num = configs['model']['head_num']
    self.embedding_size = configs['model']['embedding_size']
    self.qTrans = nn.Parameter(init(t.empty(self.embedding_size, self.embedding_size)))
    self.kTrans = nn.Parameter(init(t.empty(self.embedding_size, self.embedding_size)))
    self.vTrans = nn.Parameter(init(t.empty(self.embedding_size, self.embedding_size)))

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

def __init__(self):
    super(LocalGraph, self).__init__()
    self.seed_num = configs['model']['seed_num']

class RandomMaskSubgraphs(nn.Module):

    def __init__(self):
        super(RandomMaskSubgraphs, self).__init__()
        self.flag = False
        self.mask_depth = configs['model']['mask_depth']
        self.keep_rate = configs['model']['keep_rate']
        self.user_num = configs['data']['user_num']
        self.item_num = configs['data']['item_num']

    def normalizeAdj(self, adj):
        degree = t.pow(t.sparse.sum(adj, dim=1).to_dense() + 1e-12, -0.5)
        newRows, newCols = (adj._indices()[0, :], adj._indices()[1, :])
        rowNorm, colNorm = (degree[newRows], degree[newCols])
        newVals = adj._values() * rowNorm * colNorm
        return t.sparse.FloatTensor(adj._indices(), newVals, adj.shape)

    def forward(self, adj, seeds):
        rows = adj._indices()[0, :]
        cols = adj._indices()[1, :]
        maskNodes = [seeds]
        for i in range(self.mask_depth):
            curSeeds = seeds if i == 0 else nxtSeeds
            nxtSeeds = list()
            for seed in curSeeds:
                rowIdct = rows == seed
                colIdct = cols == seed
                idct = t.logical_or(rowIdct, colIdct)
                if i != self.mask_depth - 1:
                    mskRows = rows[idct]
                    mskCols = cols[idct]
                    nxtSeeds.append(mskRows)
                    nxtSeeds.append(mskCols)
                rows = rows[t.logical_not(idct)]
                cols = cols[t.logical_not(idct)]
            if len(nxtSeeds) > 0:
                nxtSeeds = t.unique(t.concat(nxtSeeds))
                maskNodes.append(nxtSeeds)
        sampNum = int((self.user_num + self.item_num) * self.keep_rate)
        sampedNodes = t.randint(self.user_num + self.item_num, size=[sampNum]).cuda()
        if self.flag == False:
            l1 = adj._values().shape[0]
            l2 = rows.shape[0]
            print('-----')
            print('LENGTH CHANGE', '%.2f' % (l2 / l1), l2, l1)
            tem = t.unique(t.concat(maskNodes))
            print('Original SAMPLED NODES', '%.2f' % (tem.shape[0] / (self.user_num + self.item_num)), tem.shape[0], self.user_num + self.item_num)
        maskNodes.append(sampedNodes)
        maskNodes = t.unique(t.concat(maskNodes))
        if self.flag == False:
            print('AUGMENTED SAMPLED NODES', '%.2f' % (maskNodes.shape[0] / (self.user_num + self.item_num)), maskNodes.shape[0], self.user_num + self.item_num)
            self.flag = True
            print('-----')
        encoder_adj = self.normalizeAdj(t.sparse.FloatTensor(t.stack([rows, cols], dim=0), t.ones_like(rows).cuda(), adj.shape))
        temNum = maskNodes.shape[0]
        temRows = maskNodes[t.randint(temNum, size=[adj._values().shape[0]]).cuda()]
        temCols = maskNodes[t.randint(temNum, size=[adj._values().shape[0]]).cuda()]
        newRows = t.concat([temRows, temCols, t.arange(self.user_num + self.item_num).cuda(), rows])
        newCols = t.concat([temCols, temRows, t.arange(self.user_num + self.item_num).cuda(), cols])
        hashVal = newRows * (self.user_num + self.item_num) + newCols
        hashVal = t.unique(hashVal)
        newCols = hashVal % (self.user_num + self.item_num)
        newRows = ((hashVal - newCols) / (self.user_num + self.item_num)).long()
        decoder_adj = t.sparse.FloatTensor(t.stack([newRows, newCols], dim=0), t.ones_like(newRows).cuda().float(), adj.shape)
        return (encoder_adj, decoder_adj)

def __init__(self):
    super(RandomMaskSubgraphs, self).__init__()
    self.flag = False
    self.mask_depth = configs['model']['mask_depth']
    self.keep_rate = configs['model']['keep_rate']
    self.user_num = configs['data']['user_num']
    self.item_num = configs['data']['item_num']

class GCNLayer(nn.Module):

    def __init__(self, latdim):
        super(GCNLayer, self).__init__()
        self.W = nn.Parameter(init(t.empty(latdim, latdim)))

    def forward(self, adj, embeds):
        return t.spmm(adj, embeds)

def __init__(self, latdim):
    super(GCNLayer, self).__init__()
    self.W = nn.Parameter(init(t.empty(latdim, latdim)))

class GCCF_plus(BaseModel):

    def __init__(self, data_handler):
        super(GCCF_plus, self).__init__(data_handler)
        self.adj = data_handler.torch_adj
        self.layer_num = self.hyper_config['layer_num']
        self.reg_weight = self.hyper_config['reg_weight']
        self.kd_weight = self.hyper_config['kd_weight']
        self.kd_temperature = self.hyper_config['kd_temperature']
        self.user_embeds = nn.Parameter(init(t.empty(self.user_num, self.embedding_size)))
        self.item_embeds = nn.Parameter(init(t.empty(self.item_num, self.embedding_size)))
        self.gcnLayers = nn.Sequential(*[GCNLayer(self.embedding_size) for i in range(self.layer_num)])
        self.is_training = True
        self.usrprf_embeds = t.tensor(configs['usrprf_embeds']).float().cuda()
        self.itmprf_embeds = t.tensor(configs['itmprf_embeds']).float().cuda()
        output_size = int((self.layer_num + 1) * self.embedding_size)
        self.mlp = nn.Sequential(nn.Linear(self.usrprf_embeds.shape[1], (self.usrprf_embeds.shape[1] + output_size) // 2), nn.LeakyReLU(), nn.Linear((self.usrprf_embeds.shape[1] + output_size) // 2, output_size))
        self._init_weight()

    def _init_weight(self):
        for m in self.mlp:
            if isinstance(m, nn.Linear):
                init(m.weight)

    def forward(self, adj=None):
        if adj is None:
            adj = self.adj
        if not self.is_training:
            return (self.final_embeds[:self.user_num], self.final_embeds[self.user_num:], None)
        embeds = t.concat([self.user_embeds, self.item_embeds], axis=0)
        embeds_list = [embeds]
        for gcn in self.gcnLayers:
            embeds = gcn(adj, embeds_list[-1])
            embeds_list.append(embeds)
        embeds = t.concat(embeds_list, dim=-1)
        self.final_embeds = embeds
        return (embeds[:self.user_num], embeds[self.user_num:], embeds_list[-1])

    def _pick_embeds(self, user_embeds, item_embeds, batch_data):
        ancs, poss, negs = batch_data
        anc_embeds = user_embeds[ancs]
        pos_embeds = item_embeds[poss]
        neg_embeds = item_embeds[negs]
        return (anc_embeds, pos_embeds, neg_embeds)

    def cal_loss(self, batch_data):
        self.is_training = True
        user_embeds, item_embeds, _ = self.forward(self.adj)
        ancs, poss, negs = batch_data
        anc_embeds = user_embeds[ancs]
        pos_embeds = item_embeds[poss]
        neg_embeds = item_embeds[negs]
        bpr_loss = cal_bpr_loss(anc_embeds, pos_embeds, neg_embeds) / anc_embeds.shape[0]
        reg_loss = self.reg_weight * reg_params(self)
        usrprf_embeds = self.mlp(self.usrprf_embeds)
        itmprf_embeds = self.mlp(self.itmprf_embeds)
        ancprf_embeds, posprf_embeds, negprf_embeds = self._pick_embeds(usrprf_embeds, itmprf_embeds, batch_data)
        kd_loss = cal_infonce_loss(anc_embeds, ancprf_embeds, usrprf_embeds, self.kd_temperature) + cal_infonce_loss(pos_embeds, posprf_embeds, posprf_embeds, self.kd_temperature) + cal_infonce_loss(neg_embeds, negprf_embeds, negprf_embeds, self.kd_temperature)
        kd_loss /= anc_embeds.shape[0]
        kd_loss *= self.kd_weight
        loss = bpr_loss + reg_loss + kd_loss
        losses = {'bpr_loss': bpr_loss, 'reg_loss': reg_loss, 'kd_loss': kd_loss}
        return (loss, losses)

    def full_predict(self, batch_data):
        user_embeds, item_embeds, _ = self.forward(self.adj)
        self.is_training = False
        pck_users, train_mask = batch_data
        pck_users = pck_users.long()
        pck_user_embeds = user_embeds[pck_users]
        full_preds = pck_user_embeds @ item_embeds.T
        full_preds = self._mask_predict(full_preds, train_mask)
        return full_preds

def __init__(self, data_handler):
    super(GCCF_plus, self).__init__(data_handler)
    self.adj = data_handler.torch_adj
    self.layer_num = self.hyper_config['layer_num']
    self.reg_weight = self.hyper_config['reg_weight']
    self.kd_weight = self.hyper_config['kd_weight']
    self.kd_temperature = self.hyper_config['kd_temperature']
    self.user_embeds = nn.Parameter(init(t.empty(self.user_num, self.embedding_size)))
    self.item_embeds = nn.Parameter(init(t.empty(self.item_num, self.embedding_size)))
    self.gcnLayers = nn.Sequential(*[GCNLayer(self.embedding_size) for i in range(self.layer_num)])
    self.is_training = True
    self.usrprf_embeds = t.tensor(configs['usrprf_embeds']).float().cuda()
    self.itmprf_embeds = t.tensor(configs['itmprf_embeds']).float().cuda()
    output_size = int((self.layer_num + 1) * self.embedding_size)
    self.mlp = nn.Sequential(nn.Linear(self.usrprf_embeds.shape[1], (self.usrprf_embeds.shape[1] + output_size) // 2), nn.LeakyReLU(), nn.Linear((self.usrprf_embeds.shape[1] + output_size) // 2, output_size))
    self._init_weight()

def _init_weight(self):
    for m in self.mlp:
        if isinstance(m, nn.Linear):
            init(m.weight)

class SimGCL_gene(LightGCN_gene):

    def __init__(self, data_handler):
        super(SimGCL_gene, self).__init__(data_handler)
        self.cl_weight = self.hyper_config['cl_weight']
        self.cl_temperature = self.hyper_config['cl_temperature']
        self.eps = self.hyper_config['eps']
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

    def _mask(self):
        embeds = t.concat([self.user_embeds, self.item_embeds], axis=0)
        masked_embeds, seeds = self.masker(embeds)
        return (masked_embeds[:self.user_num], masked_embeds[self.user_num:], seeds)

    def _perturb_embedding(self, embeds):
        noise = F.normalize(t.rand(embeds.shape).cuda(), p=2) * t.sign(embeds) * self.eps
        return embeds + noise

    def forward(self, adj=None, perturb=False, masked_user_embeds=None, masked_item_embeds=None):
        if adj is None:
            adj = self.adj
        if not perturb:
            return super(SimGCL_gene, self).forward(adj, 1.0, masked_user_embeds=masked_user_embeds, masked_item_embeds=masked_item_embeds)
        if masked_user_embeds is None or masked_item_embeds is None:
            embeds = t.concat([self.user_embeds, self.item_embeds], axis=0)
        else:
            embeds = t.concat([masked_user_embeds, masked_item_embeds], axis=0)
        embeds_list = [embeds]
        for i in range(self.layer_num):
            embeds = self._propagate(adj, embeds_list[-1])
            embeds = self._perturb_embedding(embeds)
            embeds_list.append(embeds)
        embeds = sum(embeds_list)
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
        user_embeds1, item_embeds1 = self.forward(self.adj, perturb=True, masked_user_embeds=masked_user_embeds, masked_item_embeds=masked_item_embeds)
        user_embeds2, item_embeds2 = self.forward(self.adj, perturb=True, masked_user_embeds=masked_user_embeds, masked_item_embeds=masked_item_embeds)
        user_embeds3, item_embeds3 = self.forward(self.adj, perturb=False, masked_user_embeds=masked_user_embeds, masked_item_embeds=masked_item_embeds)
        anc_embeds1, pos_embeds1, neg_embeds1 = self._pick_embeds(user_embeds1, item_embeds1, batch_data)
        anc_embeds2, pos_embeds2, neg_embeds2 = self._pick_embeds(user_embeds2, item_embeds2, batch_data)
        anc_embeds3, pos_embeds3, neg_embeds3 = self._pick_embeds(user_embeds3, item_embeds3, batch_data)
        bpr_loss = cal_bpr_loss(anc_embeds3, pos_embeds3, neg_embeds3) / anc_embeds3.shape[0]
        cl_loss = cal_infonce_loss(anc_embeds1, anc_embeds2, user_embeds2, self.cl_temperature) + cal_infonce_loss(pos_embeds1, pos_embeds2, item_embeds2, self.cl_temperature)
        cl_loss /= anc_embeds1.shape[0]
        cl_loss *= self.cl_weight
        recon_loss = self.recon_weight * self._reconstruction(t.concat([user_embeds3, item_embeds3], axis=0), seeds)
        reg_loss = self.reg_weight * reg_params(self)
        loss = bpr_loss + reg_loss + cl_loss + recon_loss
        losses = {'bpr_loss': bpr_loss, 'reg_loss': reg_loss, 'cl_loss': cl_loss, 'recon_loss': recon_loss}
        return (loss, losses)

    def full_predict(self, batch_data):
        user_embeds, item_embeds = self.forward(self.adj, False)
        self.is_training = False
        pck_users, train_mask = batch_data
        pck_users = pck_users.long()
        pck_user_embeds = user_embeds[pck_users]
        full_preds = pck_user_embeds @ item_embeds.T
        full_preds = self._mask_predict(full_preds, train_mask)
        return full_preds

def __init__(self, data_handler):
    super(SimGCL_gene, self).__init__(data_handler)
    self.cl_weight = self.hyper_config['cl_weight']
    self.cl_temperature = self.hyper_config['cl_temperature']
    self.eps = self.hyper_config['eps']
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

class SimGCL_plus(LightGCN):

    def __init__(self, data_handler):
        super(SimGCL_plus, self).__init__(data_handler)
        self.cl_weight = self.hyper_config['cl_weight']
        self.cl_temperature = self.hyper_config['cl_temperature']
        self.kd_weight = self.hyper_config['kd_weight']
        self.kd_temperature = self.hyper_config['kd_temperature']
        self.eps = self.hyper_config['eps']
        self.usrprf_embeds = t.tensor(configs['usrprf_embeds']).float().cuda()
        self.itmprf_embeds = t.tensor(configs['itmprf_embeds']).float().cuda()
        self.mlp = nn.Sequential(nn.Linear(self.usrprf_embeds.shape[1], (self.usrprf_embeds.shape[1] + self.embedding_size) // 2), nn.LeakyReLU(), nn.Linear((self.usrprf_embeds.shape[1] + self.embedding_size) // 2, self.embedding_size))
        self._init_weight()

    def _init_weight(self):
        for m in self.mlp:
            if isinstance(m, nn.Linear):
                init(m.weight)

    def _perturb_embedding(self, embeds):
        noise = F.normalize(t.rand(embeds.shape).cuda(), p=2) * t.sign(embeds) * self.eps
        return embeds + noise

    def forward(self, adj=None, perturb=False):
        if adj is None:
            adj = self.adj
        if not perturb:
            return super(SimGCL_plus, self).forward(adj, 1.0)
        embeds = t.concat([self.user_embeds, self.item_embeds], dim=0)
        embeds_list = [embeds]
        for i in range(self.layer_num):
            embeds = self._propagate(adj, embeds_list[-1])
            embeds = self._perturb_embedding(embeds)
            embeds_list.append(embeds)
        embeds = sum(embeds_list)
        return (embeds[:self.user_num], embeds[self.user_num:])

    def _pick_embeds(self, user_embeds, item_embeds, batch_data):
        ancs, poss, negs = batch_data
        anc_embeds = user_embeds[ancs]
        pos_embeds = item_embeds[poss]
        neg_embeds = item_embeds[negs]
        return (anc_embeds, pos_embeds, neg_embeds)

    def cal_loss(self, batch_data):
        self.is_training = True
        user_embeds1, item_embeds1 = self.forward(self.adj, perturb=True)
        user_embeds2, item_embeds2 = self.forward(self.adj, perturb=True)
        user_embeds3, item_embeds3 = self.forward(self.adj, perturb=False)
        anc_embeds1, pos_embeds1, neg_embeds1 = self._pick_embeds(user_embeds1, item_embeds1, batch_data)
        anc_embeds2, pos_embeds2, neg_embeds2 = self._pick_embeds(user_embeds2, item_embeds2, batch_data)
        anc_embeds3, pos_embeds3, neg_embeds3 = self._pick_embeds(user_embeds3, item_embeds3, batch_data)
        usrprf_embeds = self.mlp(self.usrprf_embeds)
        itmprf_embeds = self.mlp(self.itmprf_embeds)
        ancprf_embeds, posprf_embeds, negprf_embeds = self._pick_embeds(usrprf_embeds, itmprf_embeds, batch_data)
        bpr_loss = cal_bpr_loss(anc_embeds3, pos_embeds3, neg_embeds3) / anc_embeds3.shape[0]
        cl_loss = cal_infonce_loss(anc_embeds1, anc_embeds2, user_embeds2, self.cl_temperature) + cal_infonce_loss(pos_embeds1, pos_embeds2, item_embeds2, self.cl_temperature)
        cl_loss /= anc_embeds1.shape[0]
        cl_loss *= self.cl_weight
        kd_loss = cal_infonce_loss(anc_embeds3, ancprf_embeds, usrprf_embeds, self.kd_temperature) + cal_infonce_loss(pos_embeds3, posprf_embeds, posprf_embeds, self.kd_temperature) + cal_infonce_loss(neg_embeds3, negprf_embeds, negprf_embeds, self.kd_temperature)
        kd_loss /= anc_embeds3.shape[0]
        kd_loss *= self.kd_weight
        reg_loss = self.reg_weight * reg_params(self)
        loss = bpr_loss + reg_loss + cl_loss + kd_loss
        losses = {'bpr_loss': bpr_loss, 'reg_loss': reg_loss, 'cl_loss': cl_loss, 'kd_loss': kd_loss}
        return (loss, losses)

    def full_predict(self, batch_data):
        user_embeds, item_embeds = self.forward(self.adj, False)
        self.is_training = False
        pck_users, train_mask = batch_data
        pck_users = pck_users.long()
        pck_user_embeds = user_embeds[pck_users]
        full_preds = pck_user_embeds @ item_embeds.T
        full_preds = self._mask_predict(full_preds, train_mask)
        return full_preds

def __init__(self, data_handler):
    super(SimGCL_plus, self).__init__(data_handler)
    self.cl_weight = self.hyper_config['cl_weight']
    self.cl_temperature = self.hyper_config['cl_temperature']
    self.kd_weight = self.hyper_config['kd_weight']
    self.kd_temperature = self.hyper_config['kd_temperature']
    self.eps = self.hyper_config['eps']
    self.usrprf_embeds = t.tensor(configs['usrprf_embeds']).float().cuda()
    self.itmprf_embeds = t.tensor(configs['itmprf_embeds']).float().cuda()
    self.mlp = nn.Sequential(nn.Linear(self.usrprf_embeds.shape[1], (self.usrprf_embeds.shape[1] + self.embedding_size) // 2), nn.LeakyReLU(), nn.Linear((self.usrprf_embeds.shape[1] + self.embedding_size) // 2, self.embedding_size))
    self._init_weight()

def _init_weight(self):
    for m in self.mlp:
        if isinstance(m, nn.Linear):
            init(m.weight)

