# Cluster 1

def main():
    init_seed()
    data_handler = build_data_handler()
    data_handler.load_data()
    model = build_model(data_handler).to(configs['device'])
    logger = Logger()
    trainer = build_trainer(data_handler, logger)
    trainer.train(model)

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

class Tuner(object):

    def __init__(self, logger):
        self.logger = logger
        self.hyperparameters = configs['tune']['hyperparameters']
        self.tune_list = []
        self.search_length = 1
        for hyper_para in self.hyperparameters:
            self.tune_list.append(configs['tune'][hyper_para])
            self.search_length = self.search_length * len(configs['tune'][hyper_para])
        self.para_length = [len(para_list) for para_list in self.tune_list]
        self.hex_length = [1 for _ in range(len(self.tune_list))]
        for i in range(len(self.para_length) - 2, -1, -1):
            self.hex_length[i] = self.para_length[i + 1] * self.hex_length[i + 1]
        self.origin_model_para = configs['model'].copy()

    def zero_step(self):
        self.now_step = 0

    def step(self):
        self.now_step += 1

    def next_model(self, data_handler):
        init_seed()
        now_para = {}
        now_para_str = ''
        for i in range(len(self.hyperparameters)):
            para_name = self.hyperparameters[i]
            selected_idx = self.now_step // self.hex_length[i] % self.para_length[i]
            seleted_val = self.tune_list[i][selected_idx]
            now_para[para_name] = seleted_val
            now_para_str += '{}{}'.format(para_name, seleted_val)
            configs['model'][para_name] = seleted_val
            if configs['data']['name'] in configs['model']:
                configs['model'][configs['data']['name']][para_name] = seleted_val
        configs['tune']['now_para_str'] = now_para_str
        self.logger.log('hyperparameter: {}'.format(now_para))
        model = build_model(data_handler).cuda()
        return model

    def grid_search(self, data_handler, trainer):
        self.zero_step()
        for _ in range(self.search_length):
            model = self.next_model(data_handler)
            trainer.train(model)
            del model
            torch.cuda.empty_cache()
            self.step()
        configs['model'] = self.origin_model_para.copy()

def next_model(self, data_handler):
    init_seed()
    now_para = {}
    now_para_str = ''
    for i in range(len(self.hyperparameters)):
        para_name = self.hyperparameters[i]
        selected_idx = self.now_step // self.hex_length[i] % self.para_length[i]
        seleted_val = self.tune_list[i][selected_idx]
        now_para[para_name] = seleted_val
        now_para_str += '{}{}'.format(para_name, seleted_val)
        configs['model'][para_name] = seleted_val
        if configs['data']['name'] in configs['model']:
            configs['model'][configs['data']['name']][para_name] = seleted_val
    configs['tune']['now_para_str'] = now_para_str
    self.logger.log('hyperparameter: {}'.format(now_para))
    model = build_model(data_handler).cuda()
    return model

def grid_search(self, data_handler, trainer):
    self.zero_step()
    for _ in range(self.search_length):
        model = self.next_model(data_handler)
        trainer.train(model)
        del model
        torch.cuda.empty_cache()
        self.step()
    configs['model'] = self.origin_model_para.copy()

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

def forward(self, embeds):
    seeds = np.random.choice(embeds.shape[0], size=max(int(embeds.shape[0] * self.mask_ratio), 1), replace=False)
    seeds = t.LongTensor(seeds).to(configs['device'])
    mask = t.ones(embeds.shape[0]).to(configs['device'])
    mask[seeds] = 0
    mask = mask.view(-1, 1)
    masked_embeds = embeds * mask + self.mask_token * (1.0 - mask)
    return (masked_embeds, seeds)

