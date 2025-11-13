# Cluster 5

class DataHandlerGeneralCF:

    def __init__(self):
        if configs['data']['name'] == 'amazon':
            predir = './data/amazon/'
        elif configs['data']['name'] == 'yelp':
            predir = './data/yelp/'
        elif configs['data']['name'] == 'steam':
            predir = './data/steam/'
        else:
            raise NotImplementedError
        self.trn_file = predir + 'trn_mat.pkl'
        self.val_file = predir + 'val_mat.pkl'
        self.tst_file = predir + 'tst_mat.pkl'

    def _load_one_mat(self, file):
        """Load one single adjacent matrix from file

        Args:
            file (string): path of the file to load

        Returns:
            scipy.sparse.coo_matrix: the loaded adjacent matrix
        """
        with open(file, 'rb') as fs:
            mat = (pickle.load(fs) != 0).astype(np.float32)
        if type(mat) != coo_matrix:
            mat = coo_matrix(mat)
        return mat

    def _normalize_adj(self, mat):
        """Laplacian normalization for mat in coo_matrix

        Args:
            mat (scipy.sparse.coo_matrix): the un-normalized adjacent matrix

        Returns:
            scipy.sparse.coo_matrix: normalized adjacent matrix
        """
        degree = np.array(mat.sum(axis=-1))
        d_inv_sqrt = np.reshape(np.power(degree, -0.5), [-1])
        d_inv_sqrt[np.isinf(d_inv_sqrt)] = 0.0
        d_inv_sqrt_mat = sp.diags(d_inv_sqrt)
        return mat.dot(d_inv_sqrt_mat).transpose().dot(d_inv_sqrt_mat).tocoo()

    def _make_torch_adj(self, mat, self_loop=False):
        """Transform uni-directional adjacent matrix in coo_matrix into bi-directional adjacent matrix in torch.sparse.FloatTensor

        Args:
            mat (coo_matrix): the uni-directional adjacent matrix

        Returns:
            torch.sparse.FloatTensor: the bi-directional matrix
        """
        if not self_loop:
            a = csr_matrix((configs['data']['user_num'], configs['data']['user_num']))
            b = csr_matrix((configs['data']['item_num'], configs['data']['item_num']))
        else:
            data = np.ones(configs['data']['user_num'])
            row_indices = np.arange(configs['data']['user_num'])
            column_indices = np.arange(configs['data']['user_num'])
            a = csr_matrix((data, (row_indices, column_indices)), shape=(configs['data']['user_num'], configs['data']['user_num']))
            data = np.ones(configs['data']['item_num'])
            row_indices = np.arange(configs['data']['item_num'])
            column_indices = np.arange(configs['data']['item_num'])
            b = csr_matrix((data, (row_indices, column_indices)), shape=(configs['data']['item_num'], configs['data']['item_num']))
        mat = sp.vstack([sp.hstack([a, mat]), sp.hstack([mat.transpose(), b])])
        mat = (mat != 0) * 1.0
        mat = self._normalize_adj(mat)
        idxs = t.from_numpy(np.vstack([mat.row, mat.col]).astype(np.int64))
        vals = t.from_numpy(mat.data.astype(np.float32))
        shape = t.Size(mat.shape)
        return t.sparse.FloatTensor(idxs, vals, shape).to(configs['device'])

    def load_data(self):
        trn_mat = self._load_one_mat(self.trn_file)
        val_mat = self._load_one_mat(self.val_file)
        tst_mat = self._load_one_mat(self.tst_file)
        self.trn_mat = trn_mat
        configs['data']['user_num'], configs['data']['item_num'] = trn_mat.shape
        self.torch_adj = self._make_torch_adj(trn_mat)
        if configs['model']['name'] == 'gccf':
            self.torch_adj = self._make_torch_adj(trn_mat, self_loop=True)
        if configs['train']['loss'] == 'pairwise':
            trn_data = PairwiseTrnData(trn_mat)
        elif configs['train']['loss'] == 'pairwise_with_epoch_flag':
            trn_data = PairwiseWEpochFlagTrnData(trn_mat)
        val_data = AllRankTstData(val_mat, trn_mat)
        tst_data = AllRankTstData(tst_mat, trn_mat)
        self.test_dataloader = data.DataLoader(tst_data, batch_size=configs['test']['batch_size'], shuffle=False, num_workers=0)
        self.valid_dataloader = data.DataLoader(val_data, batch_size=configs['test']['batch_size'], shuffle=False, num_workers=0)
        self.train_dataloader = data.DataLoader(trn_data, batch_size=configs['train']['batch_size'], shuffle=True, num_workers=0)

def _normalize_adj(self, mat):
    """Laplacian normalization for mat in coo_matrix

        Args:
            mat (scipy.sparse.coo_matrix): the un-normalized adjacent matrix

        Returns:
            scipy.sparse.coo_matrix: normalized adjacent matrix
        """
    degree = np.array(mat.sum(axis=-1))
    d_inv_sqrt = np.reshape(np.power(degree, -0.5), [-1])
    d_inv_sqrt[np.isinf(d_inv_sqrt)] = 0.0
    d_inv_sqrt_mat = sp.diags(d_inv_sqrt)
    return mat.dot(d_inv_sqrt_mat).transpose().dot(d_inv_sqrt_mat).tocoo()

def _make_torch_adj(self, mat, self_loop=False):
    """Transform uni-directional adjacent matrix in coo_matrix into bi-directional adjacent matrix in torch.sparse.FloatTensor

        Args:
            mat (coo_matrix): the uni-directional adjacent matrix

        Returns:
            torch.sparse.FloatTensor: the bi-directional matrix
        """
    if not self_loop:
        a = csr_matrix((configs['data']['user_num'], configs['data']['user_num']))
        b = csr_matrix((configs['data']['item_num'], configs['data']['item_num']))
    else:
        data = np.ones(configs['data']['user_num'])
        row_indices = np.arange(configs['data']['user_num'])
        column_indices = np.arange(configs['data']['user_num'])
        a = csr_matrix((data, (row_indices, column_indices)), shape=(configs['data']['user_num'], configs['data']['user_num']))
        data = np.ones(configs['data']['item_num'])
        row_indices = np.arange(configs['data']['item_num'])
        column_indices = np.arange(configs['data']['item_num'])
        b = csr_matrix((data, (row_indices, column_indices)), shape=(configs['data']['item_num'], configs['data']['item_num']))
    mat = sp.vstack([sp.hstack([a, mat]), sp.hstack([mat.transpose(), b])])
    mat = (mat != 0) * 1.0
    mat = self._normalize_adj(mat)
    idxs = t.from_numpy(np.vstack([mat.row, mat.col]).astype(np.int64))
    vals = t.from_numpy(mat.data.astype(np.float32))
    shape = t.Size(mat.shape)
    return t.sparse.FloatTensor(idxs, vals, shape).to(configs['device'])

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

def __getitem__(self, idx):
    pck_user = self.test_users[idx]
    pck_mask = self.csrmat[pck_user].toarray()
    pck_mask = np.reshape(pck_mask, [-1])
    return (pck_user, pck_mask)

