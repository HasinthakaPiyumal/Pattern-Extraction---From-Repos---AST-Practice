# Cluster 3

class PairwiseTrnData(data.Dataset):

    def __init__(self, coomat):
        self.rows = coomat.row
        self.cols = coomat.col
        self.dokmat = coomat.todok()
        self.negs = np.zeros(len(self.rows)).astype(np.int32)

    def sample_negs(self):
        for i in range(len(self.rows)):
            u = self.rows[i]
            while True:
                iNeg = np.random.randint(configs['data']['item_num'])
                if (u, iNeg) not in self.dokmat:
                    break
            self.negs[i] = iNeg

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, idx):
        return (self.rows[idx], self.cols[idx], self.negs[idx])

def sample_negs(self):
    for i in range(len(self.rows)):
        u = self.rows[i]
        while True:
            iNeg = np.random.randint(configs['data']['item_num'])
            if (u, iNeg) not in self.dokmat:
                break
        self.negs[i] = iNeg

def __len__(self):
    return len(self.rows)

class AllRankTstData(data.Dataset):

    def __init__(self, coomat, trn_mat):
        self.csrmat = (trn_mat.tocsr() != 0) * 1.0
        user_pos_lists = [list() for i in range(coomat.shape[0])]
        test_users = set()
        for i in range(len(coomat.data)):
            row = coomat.row[i]
            col = coomat.col[i]
            user_pos_lists[row].append(col)
            test_users.add(row)
        self.test_users = np.array(list(test_users))
        self.user_pos_lists = user_pos_lists

    def __len__(self):
        return len(self.test_users)

    def __getitem__(self, idx):
        pck_user = self.test_users[idx]
        pck_mask = self.csrmat[pck_user].toarray()
        pck_mask = np.reshape(pck_mask, [-1])
        return (pck_user, pck_mask)

def __len__(self):
    return len(self.test_users)

class Metric(object):

    def __init__(self):
        self.metrics = configs['test']['metrics']
        self.k = configs['test']['k']

    def recall(self, test_data, r, k):
        right_pred = r[:, :k].sum(1)
        recall_n = np.array([len(test_data[i]) for i in range(len(test_data))])
        recall = np.sum(right_pred / recall_n)
        return recall

    def precision(self, r, k):
        right_pred = r[:, :k].sum(1)
        precis_n = k
        precision = np.sum(right_pred) / precis_n
        return precision

    def mrr(self, r, k):
        pred_data = r[:, :k]
        scores = 1.0 / np.arange(1, k + 1)
        pred_data = pred_data * scores
        pred_data = pred_data.sum(1)
        return np.sum(pred_data)

    def ndcg(self, test_data, r, k):
        assert len(r) == len(test_data)
        pred_data = r[:, :k]
        test_matrix = np.zeros((len(pred_data), k))
        for i, items in enumerate(test_data):
            length = k if k <= len(items) else len(items)
            test_matrix[i, :length] = 1
        max_r = test_matrix
        idcg = np.sum(max_r * 1.0 / np.log2(np.arange(2, k + 2)), axis=1)
        dcg = pred_data * (1.0 / np.log2(np.arange(2, k + 2)))
        dcg = np.sum(dcg, axis=1)
        idcg[idcg == 0.0] = 1.0
        ndcg = dcg / idcg
        ndcg[np.isnan(ndcg)] = 0.0
        return np.sum(ndcg)

    def get_label(self, test_data, pred_data):
        r = []
        for i in range(len(test_data)):
            ground_true = test_data[i]
            predict_topk = pred_data[i]
            pred = list(map(lambda x: x in ground_true, predict_topk))
            pred = np.array(pred).astype('float')
            r.append(pred)
        return np.array(r).astype('float')

    def eval_batch(self, data, topks):
        sorted_items = data[0].numpy()
        ground_true = data[1]
        r = self.get_label(ground_true, sorted_items)
        result = {}
        for metric in self.metrics:
            result[metric] = []
        for k in topks:
            for metric in result:
                if metric == 'recall':
                    result[metric].append(self.recall(ground_true, r, k))
                if metric == 'ndcg':
                    result[metric].append(self.ndcg(ground_true, r, k))
                if metric == 'precision':
                    result[metric].append(self.precision(r, k))
                if metric == 'mrr':
                    result[metric].append(self.mrr(r, k))
        for metric in result:
            result[metric] = np.array(result[metric])
        return result

    def eval(self, model, test_dataloader):
        result = {}
        for metric in self.metrics:
            result[metric] = np.zeros(len(self.k))
        batch_ratings = []
        ground_truths = []
        test_user_count = 0
        test_user_num = len(test_dataloader.dataset.test_users)
        for _, tem in enumerate(test_dataloader):
            if not isinstance(tem, list):
                tem = [tem]
            test_user = tem[0].numpy().tolist()
            batch_data = list(map(lambda x: x.long().to(configs['device']), tem))
            with torch.no_grad():
                batch_pred = model.full_predict(batch_data)
            test_user_count += batch_pred.shape[0]
            batch_pred = self._mask_history_pos(batch_pred, test_user, test_dataloader)
            _, batch_rate = torch.topk(batch_pred, k=max(self.k))
            batch_ratings.append(batch_rate.cpu())
            ground_truth = []
            for user_idx in test_user:
                ground_truth.append(list(test_dataloader.dataset.user_pos_lists[user_idx]))
            ground_truths.append(ground_truth)
        assert test_user_count == test_user_num
        data_pair = zip(batch_ratings, ground_truths)
        eval_results = []
        for _data in data_pair:
            eval_results.append(self.eval_batch(_data, self.k))
        for batch_result in eval_results:
            for metric in self.metrics:
                result[metric] += batch_result[metric] / test_user_num
        return result

    def eval_save(self, model, test_dataloader):
        result = {}
        for metric in self.metrics:
            result[metric] = np.zeros(len(self.k))
        batch_ratings = []
        ground_truths = []
        test_user_count = 0
        test_user_num = len(test_dataloader.dataset.test_users)
        candidate_set = {}
        for _, tem in enumerate(test_dataloader):
            if not isinstance(tem, list):
                tem = [tem]
            test_user = tem[0].numpy().tolist()
            batch_data = list(map(lambda x: x.long().to(configs['device']), tem))
            with torch.no_grad():
                batch_pred = model.full_predict(batch_data)
            test_user_count += batch_pred.shape[0]
            batch_pred = self._mask_history_pos(batch_pred, test_user, test_dataloader)
            _, batch_rate = torch.topk(batch_pred, k=100)
            batch_ratings.append(batch_rate.cpu())
            ground_truth = []
            for user_idx in test_user:
                ground_truth.append(list(test_dataloader.dataset.user_pos_lists[user_idx]))
            for i in range(len(test_user)):
                user_idx = test_user[i]
                candidate_set[user_idx] = batch_rate[i].detach().cpu().numpy().tolist()
            ground_truths.append(ground_truth)
        assert test_user_count == test_user_num
        assert len(candidate_set) == test_user_num
        data_pair = zip(batch_ratings, ground_truths)
        eval_results = []
        for _data in data_pair:
            eval_results.append(self.eval_batch(_data, self.k))
        for batch_result in eval_results:
            for metric in self.metrics:
                result[metric] += batch_result[metric] / test_user_num
        return (result, candidate_set)

    def _mask_history_pos(self, batch_rate, test_user, test_dataloader):
        if not hasattr(test_dataloader.dataset, 'user_history_lists'):
            return batch_rate
        for i, user_idx in enumerate(test_user):
            pos_list = test_dataloader.dataset.user_history_lists[user_idx]
            batch_rate[i, pos_list] = -100000000.0
        return batch_rate

def mrr(self, r, k):
    pred_data = r[:, :k]
    scores = 1.0 / np.arange(1, k + 1)
    pred_data = pred_data * scores
    pred_data = pred_data.sum(1)
    return np.sum(pred_data)

def ndcg(self, test_data, r, k):
    assert len(r) == len(test_data)
    pred_data = r[:, :k]
    test_matrix = np.zeros((len(pred_data), k))
    for i, items in enumerate(test_data):
        length = k if k <= len(items) else len(items)
        test_matrix[i, :length] = 1
    max_r = test_matrix
    idcg = np.sum(max_r * 1.0 / np.log2(np.arange(2, k + 2)), axis=1)
    dcg = pred_data * (1.0 / np.log2(np.arange(2, k + 2)))
    dcg = np.sum(dcg, axis=1)
    idcg[idcg == 0.0] = 1.0
    ndcg = dcg / idcg
    ndcg[np.isnan(ndcg)] = 0.0
    return np.sum(ndcg)

class Logger(object):

    def __init__(self, log_configs=True):
        model_name = configs['model']['name']
        log_dir_path = './encoder/log/{}'.format(model_name)
        if not os.path.exists(log_dir_path):
            os.makedirs(log_dir_path)
        self.logger = logging.getLogger('train_logger')
        self.logger.setLevel(logging.INFO)
        dataset_name = configs['data']['name']
        if not configs['tune']['enable']:
            log_file = logging.FileHandler('{}/{}_{}.log'.format(log_dir_path, dataset_name, get_local_time()), 'a', encoding='utf-8')
        else:
            log_file = logging.FileHandler('{}/{}-tune_{}.log'.format(log_dir_path, dataset_name, get_local_time()), 'a', encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        log_file.setFormatter(formatter)
        self.logger.addHandler(log_file)
        if log_configs:
            tmp_configs = {}
            tmp_configs['optimizer'] = configs['optimizer']
            tmp_configs['train'] = configs['train']
            tmp_configs['test'] = configs['test']
            tmp_configs['data'] = configs['data']
            tmp_configs['model'] = configs['model']
            self.log(tmp_configs)

    def log(self, message, save_to_log=True, print_to_console=True):
        if save_to_log:
            self.logger.info(message)
        if print_to_console:
            print(message)

    def log_loss(self, epoch_idx, loss_log_dict, save_to_log=True, print_to_console=True):
        epoch = configs['train']['epoch']
        message = '[Epoch {:3d} / {:3d}] '.format(epoch_idx, epoch)
        for loss_name in loss_log_dict:
            message += '{}: {:.4f} '.format(loss_name, loss_log_dict[loss_name])
        if save_to_log:
            self.logger.info(message)
        if print_to_console:
            print(message)

    def log_eval(self, eval_result, k, data_type, save_to_log=True, print_to_console=True, epoch_idx=None):
        if epoch_idx is not None:
            message = 'Epoch {:3d} {} '.format(epoch_idx, data_type)
        else:
            message = ''
        for metric in eval_result:
            message += '['
            for i in range(len(k)):
                message += '{}@{}: {:.4f} '.format(metric, k[i], eval_result[metric][i])
            message += '] '
        if save_to_log:
            self.logger.info(message)
        if print_to_console:
            print(message)

def log(self, message, save_to_log=True, print_to_console=True):
    if save_to_log:
        self.logger.info(message)
    if print_to_console:
        print(message)

def log_loss(self, epoch_idx, loss_log_dict, save_to_log=True, print_to_console=True):
    epoch = configs['train']['epoch']
    message = '[Epoch {:3d} / {:3d}] '.format(epoch_idx, epoch)
    for loss_name in loss_log_dict:
        message += '{}: {:.4f} '.format(loss_name, loss_log_dict[loss_name])
    if save_to_log:
        self.logger.info(message)
    if print_to_console:
        print(message)

def log_eval(self, eval_result, k, data_type, save_to_log=True, print_to_console=True, epoch_idx=None):
    if epoch_idx is not None:
        message = 'Epoch {:3d} {} '.format(epoch_idx, data_type)
    else:
        message = ''
    for metric in eval_result:
        message += '['
        for i in range(len(k)):
            message += '{}@{}: {:.4f} '.format(metric, k[i], eval_result[metric][i])
        message += '] '
    if save_to_log:
        self.logger.info(message)
    if print_to_console:
        print(message)

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

def make_all_one_adj(self):
    idxs = self.adj._indices()
    vals = t.ones_like(self.adj._values())
    shape = self.adj.shape
    return t.sparse.FloatTensor(idxs, vals, shape).cuda()

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

def make_all_one_adj(self):
    idxs = self.adj._indices()
    vals = t.ones_like(self.adj._values())
    shape = self.adj.shape
    return t.sparse.FloatTensor(idxs, vals, shape).cuda()

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

def make_all_one_adj(self):
    idxs = self.adj._indices()
    vals = t.ones_like(self.adj._values())
    shape = self.adj.shape
    return t.sparse.FloatTensor(idxs, vals, shape).cuda()

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

