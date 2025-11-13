# Cluster 2

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

def build_data_handler():
    datahandler_name = 'data_handler_' + configs['data']['type']
    module_path = '.'.join(['data_utils', datahandler_name])
    if importlib.util.find_spec(module_path) is None:
        raise NotImplementedError('DataHandler {} is not implemented'.format(datahandler_name))
    module = importlib.import_module(module_path)
    for attr in dir(module):
        if attr.lower() == datahandler_name.lower().replace('_', ''):
            return getattr(module, attr)()
    else:
        raise NotImplementedError('DataHandler Class {} is not defined in {}'.format(datahandler_name, module_path))

def build_trainer(data_handler, logger):
    trainer_name = 'Trainer' if 'trainer' not in configs['train'] else configs['train']['trainer']
    trainer_name = trainer_name.replace('_', '')
    trainers = importlib.import_module('trainer.trainer')
    for attr in dir(trainers):
        if attr.lower() == trainer_name.lower():
            return getattr(trainers, attr)(data_handler, logger)
    else:
        raise NotImplementedError('Trainer Class {} is not defined in {}'.format(trainer_name, 'trainer.trainer'))

def wrapper(*args, **kwargs):
    logger = getLogger('train_logger')
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.exception(e)
        raise e

class Trainer(object):

    def __init__(self, data_handler, logger):
        self.data_handler = data_handler
        self.logger = logger
        self.metric = Metric()

    def create_optimizer(self, model):
        optim_config = configs['optimizer']
        if optim_config['name'] == 'adam':
            self.optimizer = optim.Adam(model.parameters(), lr=optim_config['lr'], weight_decay=optim_config['weight_decay'])

    def train_epoch(self, model, epoch_idx):
        train_dataloader = self.data_handler.train_dataloader
        train_dataloader.dataset.sample_negs()
        loss_log_dict = {}
        ep_loss = 0
        steps = len(train_dataloader.dataset) // configs['train']['batch_size']
        model.train()
        for _, tem in tqdm(enumerate(train_dataloader), desc='Training Recommender', total=len(train_dataloader)):
            self.optimizer.zero_grad()
            batch_data = list(map(lambda x: x.long().to(configs['device']), tem))
            loss, loss_dict = model.cal_loss(batch_data)
            ep_loss += loss.item()
            loss.backward()
            self.optimizer.step()
            for loss_name in loss_dict:
                _loss_val = float(loss_dict[loss_name]) / len(train_dataloader)
                if loss_name not in loss_log_dict:
                    loss_log_dict[loss_name] = _loss_val
                else:
                    loss_log_dict[loss_name] += _loss_val
        if 'log_loss' in configs['train'] and configs['train']['log_loss']:
            self.logger.log(loss_log_dict, save_to_log=False, print_to_console=True)

    @log_exceptions
    def train(self, model):
        now_patience = 0
        best_epoch = 0
        best_recall = -1000000000.0
        self.create_optimizer(model)
        train_config = configs['train']
        for epoch_idx in range(train_config['epoch']):
            self.train_epoch(model, epoch_idx)
            if epoch_idx % train_config['test_step'] == 0:
                eval_result = self.evaluate(model, epoch_idx)
                if eval_result['recall'][-1] > best_recall:
                    now_patience = 0
                    best_epoch = epoch_idx
                    best_recall = eval_result['recall'][-1]
                    best_state_dict = deepcopy(model.state_dict())
                else:
                    now_patience += 1
                if now_patience == configs['train']['patience']:
                    break
        model = build_model(self.data_handler).to(configs['device'])
        model.load_state_dict(best_state_dict)
        self.evaluate(model)
        model = build_model(self.data_handler).to(configs['device'])
        model.load_state_dict(best_state_dict)
        test_result = self.test(model)
        self.save_model(model)
        self.logger.log('Best Epoch {}. Final test result: {}.'.format(best_epoch, test_result))

    @log_exceptions
    def evaluate(self, model, epoch_idx=None):
        model.eval()
        eval_result = self.metric.eval(model, self.data_handler.valid_dataloader)
        self.logger.log_eval(eval_result, configs['test']['k'], data_type='Validation set', epoch_idx=epoch_idx)
        return eval_result

    @log_exceptions
    def test(self, model):
        model.eval()
        eval_result = self.metric.eval(model, self.data_handler.test_dataloader)
        self.logger.log_eval(eval_result, configs['test']['k'], data_type='Test set')
        return eval_result

    @log_exceptions
    def test_save(self, model):
        model.eval()
        eval_result, candidate_set = self.metric.eval_save(model, self.data_handler.test_dataloader)
        self.logger.log_eval(eval_result, configs['test']['k'], data_type='Test set')
        return (eval_result, candidate_set)

    def save_model(self, model):
        if configs['train']['save_model']:
            model_state_dict = model.state_dict()
            model_name = configs['model']['name']
            if not configs['tune']['enable']:
                save_dir_path = './encoder/checkpoint/{}'.format(model_name)
                if not os.path.exists(save_dir_path):
                    os.makedirs(save_dir_path)
                torch.save(model_state_dict, '{}/{}-{}-{}.pth'.format(save_dir_path, model_name, configs['data']['name'], configs['train']['seed']))
                self.logger.log('Save model parameters to {}'.format('{}/{}-{}-{}.pth'.format(save_dir_path, model_name, configs['data']['name'], configs['train']['seed'])))
            else:
                save_dir_path = './encoder/checkpoint/{}/tune'.format(model_name)
                if not os.path.exists(save_dir_path):
                    os.makedirs(save_dir_path)
                now_para_str = configs['tune']['now_para_str']
                torch.save(model_state_dict, '{}/{}-{}.pth'.format(save_dir_path, model_name, now_para_str))
                self.logger.log('Save model parameters to {}'.format('{}/{}-{}.pth'.format(save_dir_path, model_name, now_para_str)))

    def load_model(self, model):
        if 'pretrain_path' in configs['train']:
            pretrain_path = configs['train']['pretrain_path']
            model.load_state_dict(torch.load(pretrain_path))
            self.logger.log('Load model parameters from {}'.format(pretrain_path))

@log_exceptions
def train(self, model):
    now_patience = 0
    best_epoch = 0
    best_recall = -1000000000.0
    self.create_optimizer(model)
    train_config = configs['train']
    for epoch_idx in range(train_config['epoch']):
        self.train_epoch(model, epoch_idx)
        if epoch_idx % train_config['test_step'] == 0:
            eval_result = self.evaluate(model, epoch_idx)
            if eval_result['recall'][-1] > best_recall:
                now_patience = 0
                best_epoch = epoch_idx
                best_recall = eval_result['recall'][-1]
                best_state_dict = deepcopy(model.state_dict())
            else:
                now_patience += 1
            if now_patience == configs['train']['patience']:
                break
    model = build_model(self.data_handler).to(configs['device'])
    model.load_state_dict(best_state_dict)
    self.evaluate(model)
    model = build_model(self.data_handler).to(configs['device'])
    model.load_state_dict(best_state_dict)
    test_result = self.test(model)
    self.save_model(model)
    self.logger.log('Best Epoch {}. Final test result: {}.'.format(best_epoch, test_result))

def save_model(self, model):
    if configs['train']['save_model']:
        model_state_dict = model.state_dict()
        model_name = configs['model']['name']
        if not configs['tune']['enable']:
            save_dir_path = './encoder/checkpoint/{}'.format(model_name)
            if not os.path.exists(save_dir_path):
                os.makedirs(save_dir_path)
            torch.save(model_state_dict, '{}/{}-{}-{}.pth'.format(save_dir_path, model_name, configs['data']['name'], configs['train']['seed']))
            self.logger.log('Save model parameters to {}'.format('{}/{}-{}-{}.pth'.format(save_dir_path, model_name, configs['data']['name'], configs['train']['seed'])))
        else:
            save_dir_path = './encoder/checkpoint/{}/tune'.format(model_name)
            if not os.path.exists(save_dir_path):
                os.makedirs(save_dir_path)
            now_para_str = configs['tune']['now_para_str']
            torch.save(model_state_dict, '{}/{}-{}.pth'.format(save_dir_path, model_name, now_para_str))
            self.logger.log('Save model parameters to {}'.format('{}/{}-{}.pth'.format(save_dir_path, model_name, now_para_str)))

def load_model(self, model):
    if 'pretrain_path' in configs['train']:
        pretrain_path = configs['train']['pretrain_path']
        model.load_state_dict(torch.load(pretrain_path))
        self.logger.log('Load model parameters from {}'.format(pretrain_path))

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

def parse_configure(model=None, dataset=None):
    parser = argparse.ArgumentParser(description='RLMRec')
    parser.add_argument('--model', type=str, default='LightGCN', help='Model name')
    parser.add_argument('--dataset', type=str, default='amazon', help='Dataset name')
    parser.add_argument('--device', type=str, default='cuda', help='cpu or cuda')
    parser.add_argument('--seed', type=int, default=None, help='Device number')
    parser.add_argument('--cuda', type=str, default='0', help='Device number')
    args, _ = parser.parse_known_args()
    if args.device == 'cuda':
        os.environ['CUDA_VISIBLE_DEVICES'] = args.cuda
    if model is not None:
        model_name = model.lower()
    elif args.model is not None:
        model_name = args.model.lower()
    else:
        model_name = 'default'
    if dataset is not None:
        args.dataset = dataset
    if not os.path.exists('./encoder/config/modelconf/{}.yml'.format(model_name)):
        raise Exception('Please create the yaml file for your model first.')
    with open('./encoder/config/modelconf/{}.yml'.format(model_name), encoding='utf-8') as f:
        config_data = f.read()
        configs = yaml.safe_load(config_data)
        configs['model']['name'] = configs['model']['name'].lower()
        if 'tune' not in configs:
            configs['tune'] = {'enable': False}
        configs['device'] = args.device
        if args.dataset is not None:
            configs['data']['name'] = args.dataset
        if args.seed is not None:
            configs['train']['seed'] = args.seed
        usrprf_embeds_path = './data/{}/usr_emb_np.pkl'.format(configs['data']['name'])
        itmprf_embeds_path = './data/{}/itm_emb_np.pkl'.format(configs['data']['name'])
        with open(usrprf_embeds_path, 'rb') as f:
            configs['usrprf_embeds'] = pickle.load(f)
        with open(itmprf_embeds_path, 'rb') as f:
            configs['itmprf_embeds'] = pickle.load(f)
        return configs

def build_model(data_handler):
    model_type = configs['data']['type']
    model_name = configs['model']['name']
    module_path = '.'.join(['models', model_type, model_name])
    if importlib.util.find_spec(module_path) is None:
        raise NotImplementedError('Model {} is not implemented'.format(model_name))
    module = importlib.import_module(module_path)
    for attr in dir(module):
        if attr.lower() == model_name.lower():
            return getattr(module, attr)(data_handler)
    else:
        raise NotImplementedError('Model Class {} is not defined in {}'.format(model_name, module_path))

