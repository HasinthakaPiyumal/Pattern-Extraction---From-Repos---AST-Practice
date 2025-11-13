# Cluster 3

class ParquetDataset(Dataset):

    def __init__(self, data_path):
        self.column_index = dict()
        self.darray = self.load_data(data_path)

    def __getitem__(self, index):
        return self.darray[index, :]

    def __len__(self):
        return self.darray.shape[0]

    def load_data(self, data_path):
        df = pd.read_parquet(data_path)
        data_arrays = []
        idx = 0
        for col in df.columns:
            if df[col].dtype == 'object':
                array = np.array(df[col].to_list())
                seq_len = array.shape[1]
                self.column_index[col] = [i + idx for i in range(seq_len)]
                idx += seq_len
            else:
                array = df[col].to_numpy()
                self.column_index[col] = idx
                idx += 1
            data_arrays.append(array)
        return np.column_stack(data_arrays)

def load_data(self, data_path):
    df = pd.read_parquet(data_path)
    data_arrays = []
    idx = 0
    for col in df.columns:
        if df[col].dtype == 'object':
            array = np.array(df[col].to_list())
            seq_len = array.shape[1]
            self.column_index[col] = [i + idx for i in range(seq_len)]
            idx += seq_len
        else:
            array = df[col].to_numpy()
            self.column_index[col] = idx
            idx += 1
        data_arrays.append(array)
    return np.column_stack(data_arrays)

class LongCTRDataLoader(DataLoader):

    def __init__(self, feature_map, data_path, user_info, item_info, batch_size=32, shuffle=False, num_workers=1, max_len=50, padding='pre', **kwargs):
        if not data_path.endswith('.parquet'):
            data_path += '.parquet'
        self.dataset = ParquetDataset(data_path)
        column_index = self.dataset.column_index
        super().__init__(dataset=self.dataset, batch_size=batch_size, shuffle=shuffle, num_workers=num_workers, collate_fn=BatchCollator(feature_map, max_len, column_index, user_info, item_info, padding))
        self.num_samples = len(self.dataset)
        self.num_blocks = 1
        self.num_batches = int(np.ceil(self.num_samples / self.batch_size))

    def __len__(self):
        return self.num_batches

def __init__(self, feature_map, data_path, user_info, item_info, batch_size=32, shuffle=False, num_workers=1, max_len=50, padding='pre', **kwargs):
    if not data_path.endswith('.parquet'):
        data_path += '.parquet'
    self.dataset = ParquetDataset(data_path)
    column_index = self.dataset.column_index
    super().__init__(dataset=self.dataset, batch_size=batch_size, shuffle=shuffle, num_workers=num_workers, collate_fn=BatchCollator(feature_map, max_len, column_index, user_info, item_info, padding))
    self.num_samples = len(self.dataset)
    self.num_blocks = 1
    self.num_batches = int(np.ceil(self.num_samples / self.batch_size))

class BatchCollator(object):

    def __init__(self, feature_map, max_len, column_index, user_info, item_info, padding='pre'):
        self.feature_map = feature_map
        self.user_info = pd.read_parquet(user_info)['full_item_seq'].values
        self.item_info = pd.read_parquet(item_info).set_index('item_index')
        self.max_len = max_len
        self.column_index = column_index
        self.padding = padding

    def __call__(self, batch):
        batch_tensor = default_collate(batch)
        all_cols = set(list(self.feature_map.features.keys()) + self.feature_map.labels)
        batch_dict = dict()
        for col, idx in self.column_index.items():
            if col in all_cols:
                batch_dict[col] = batch_tensor[:, idx]
        user_index = batch_dict['user_index'].numpy()
        user_seqs = self.user_info[user_index]
        seq_lens = batch_dict['seq_len'].int().numpy()
        batch_seqs = self.padding_seqs(user_seqs, seq_lens)
        mask = (torch.from_numpy(batch_seqs) > 0).float()
        item_index = batch_dict['item_index'].numpy().reshape(-1, 1)
        batch_items = np.hstack([batch_seqs, item_index]).flatten()
        item_info = self.item_info.iloc[batch_items]
        item_dict = dict()
        for col in item_info.columns:
            if col in all_cols:
                item_dict[col] = torch.from_numpy(np.array(item_info[col].to_list()))
        return (batch_dict, item_dict, mask)

    def padding_seqs(self, user_seqs, seq_lens):
        batch_seqs = []
        for seq, l in zip(user_seqs, seq_lens):
            batch_seqs.append(seq[:l])
        max_len = min(max(seq_lens), self.max_len)
        batch_seqs = pad_sequences(batch_seqs, maxlen=max_len, value=0, padding=self.padding, truncating=self.padding)
        return batch_seqs

def __init__(self, feature_map, max_len, column_index, user_info, item_info, padding='pre'):
    self.feature_map = feature_map
    self.user_info = pd.read_parquet(user_info)['full_item_seq'].values
    self.item_info = pd.read_parquet(item_info).set_index('item_index')
    self.max_len = max_len
    self.column_index = column_index
    self.padding = padding

def __call__(self, batch):
    batch_tensor = default_collate(batch)
    all_cols = set(list(self.feature_map.features.keys()) + self.feature_map.labels)
    batch_dict = dict()
    for col, idx in self.column_index.items():
        if col in all_cols:
            batch_dict[col] = batch_tensor[:, idx]
    user_index = batch_dict['user_index'].numpy()
    user_seqs = self.user_info[user_index]
    seq_lens = batch_dict['seq_len'].int().numpy()
    batch_seqs = self.padding_seqs(user_seqs, seq_lens)
    mask = (torch.from_numpy(batch_seqs) > 0).float()
    item_index = batch_dict['item_index'].numpy().reshape(-1, 1)
    batch_items = np.hstack([batch_seqs, item_index]).flatten()
    item_info = self.item_info.iloc[batch_items]
    item_dict = dict()
    for col in item_info.columns:
        if col in all_cols:
            item_dict[col] = torch.from_numpy(np.array(item_info[col].to_list()))
    return (batch_dict, item_dict, mask)

class DCNv2(BaseModel):

    def __init__(self, feature_map, model_id='DCNv2', gpu=-1, model_structure='parallel', use_low_rank_mixture=False, low_rank=32, num_experts=4, learning_rate=0.001, embedding_dim=10, stacked_dnn_hidden_units=[], parallel_dnn_hidden_units=[], dnn_activations='ReLU', num_cross_layers=3, net_dropout=0, batch_norm=False, accumulation_steps=1, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(DCNv2, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        self.item_info_dim = 0
        for feat, spec in self.feature_map.features.items():
            if spec.get('source') == 'item':
                self.item_info_dim += spec.get('embedding_dim', embedding_dim)
        self.accumulation_steps = accumulation_steps
        self.masked_avg_pooling = MaskedAveragePooling()
        input_dim = feature_map.sum_emb_out_dim() + self.item_info_dim
        if use_low_rank_mixture:
            self.crossnet = CrossNetMix(input_dim, num_cross_layers, low_rank=low_rank, num_experts=num_experts)
        else:
            self.crossnet = CrossNetV2(input_dim, num_cross_layers)
        self.model_structure = model_structure
        assert self.model_structure in ['crossnet_only', 'stacked', 'parallel', 'stacked_parallel'], 'model_structure={} not supported!'.format(self.model_structure)
        if self.model_structure in ['stacked', 'stacked_parallel']:
            self.stacked_dnn = MLP_Block(input_dim=input_dim, output_dim=None, hidden_units=stacked_dnn_hidden_units, hidden_activations=dnn_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm)
            final_dim = stacked_dnn_hidden_units[-1]
        if self.model_structure in ['parallel', 'stacked_parallel']:
            self.parallel_dnn = MLP_Block(input_dim=input_dim, output_dim=None, hidden_units=parallel_dnn_hidden_units, hidden_activations=dnn_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm)
            final_dim = input_dim + parallel_dnn_hidden_units[-1]
        if self.model_structure == 'stacked_parallel':
            final_dim = stacked_dnn_hidden_units[-1] + parallel_dnn_hidden_units[-1]
        if self.model_structure == 'crossnet_only':
            final_dim = input_dim
        self.fc = nn.Linear(final_dim, 1)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        batch_dict, item_dict, mask = self.get_inputs(inputs)
        emb_list = []
        if batch_dict:
            emb_out = self.embedding_layer(batch_dict, flatten_emb=True)
            emb_list.append(emb_out)
        item_feat_emb = self.embedding_layer(item_dict, flatten_emb=True)
        batch_size = mask.shape[0]
        item_feat_emb = item_feat_emb.view(batch_size, -1, self.item_info_dim)
        target_emb = item_feat_emb[:, -1, :]
        sequence_emb = item_feat_emb[:, 0:-1, :]
        pooling_emb = self.masked_avg_pooling(sequence_emb, mask)
        emb_list += [target_emb, pooling_emb]
        feature_emb = torch.cat(emb_list, dim=-1)
        cross_out = self.crossnet(feature_emb)
        if self.model_structure == 'crossnet_only':
            final_out = cross_out
        elif self.model_structure == 'stacked':
            final_out = self.stacked_dnn(cross_out)
        elif self.model_structure == 'parallel':
            dnn_out = self.parallel_dnn(feature_emb)
            final_out = torch.cat([cross_out, dnn_out], dim=-1)
        elif self.model_structure == 'stacked_parallel':
            final_out = torch.cat([self.stacked_dnn(cross_out), self.parallel_dnn(feature_emb)], dim=-1)
        y_pred = self.fc(final_out)
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred}
        return return_dict

    def get_inputs(self, inputs, feature_source=None):
        batch_dict, item_dict, mask = inputs
        X_dict = dict()
        for feature, value in batch_dict.items():
            if feature in self.feature_map.labels:
                continue
            feature_spec = self.feature_map.features[feature]
            if feature_spec['type'] == 'meta':
                continue
            if feature_source and not_in_whitelist(feature_spec['source'], feature_source):
                continue
            X_dict[feature] = value.to(self.device)
        for item, value in item_dict.items():
            item_dict[item] = value.to(self.device)
        return (X_dict, item_dict, mask.to(self.device))

    def get_labels(self, inputs):
        """ Please override get_labels() when using multiple labels!
        """
        labels = self.feature_map.labels
        batch_dict = inputs[0]
        y = batch_dict[labels[0]].to(self.device)
        return y.float().view(-1, 1)

    def get_group_id(self, inputs):
        return inputs[0][self.feature_map.group_id]

    def train_step(self, batch_data):
        return_dict = self.forward(batch_data)
        y_true = self.get_labels(batch_data)
        loss = self.compute_loss(return_dict, y_true)
        loss = loss / self.accumulation_steps
        loss.backward()
        if (self._batch_index + 1) % self.accumulation_steps == 0:
            nn.utils.clip_grad_norm_(self.parameters(), self._max_gradient_norm)
            self.optimizer.step()
            self.optimizer.zero_grad()
        return loss

def get_inputs(self, inputs, feature_source=None):
    batch_dict, item_dict, mask = inputs
    X_dict = dict()
    for feature, value in batch_dict.items():
        if feature in self.feature_map.labels:
            continue
        feature_spec = self.feature_map.features[feature]
        if feature_spec['type'] == 'meta':
            continue
        if feature_source and not_in_whitelist(feature_spec['source'], feature_source):
            continue
        X_dict[feature] = value.to(self.device)
    for item, value in item_dict.items():
        item_dict[item] = value.to(self.device)
    return (X_dict, item_dict, mask.to(self.device))

class TWIN(BaseModel):

    def __init__(self, feature_map, model_id='TWIN', gpu=-1, dnn_hidden_units=[512, 128, 64], dnn_activations='ReLU', attention_dropout=0, attention_dim=64, num_heads=1, short_seq_len=50, topk=50, Kc_cross_features=0, learning_rate=0.001, embedding_dim=10, net_dropout=0, batch_norm=False, accumulation_steps=1, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(TWIN, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.feature_map = feature_map
        self.embedding_dim = embedding_dim
        self.topk = topk
        self.short_seq_len = short_seq_len
        self.item_info_dim = 0
        for feat, spec in self.feature_map.features.items():
            if spec.get('source') == 'item':
                self.item_info_dim += spec.get('embedding_dim', embedding_dim)
        self.accumulation_steps = accumulation_steps
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        self.short_attention = MultiHeadTargetAttention(self.item_info_dim, attention_dim, num_heads, attention_dropout)
        self.long_attention = MultiHeadTopKAttention(self.item_info_dim, Kc_cross_features, embedding_dim, attention_dim, topk, num_heads, attention_dropout)
        input_dim = feature_map.sum_emb_out_dim() + self.item_info_dim * 2
        self.dnn = MLP_Block(input_dim=input_dim, output_dim=1, hidden_units=dnn_hidden_units, hidden_activations=dnn_activations, output_activation=self.output_activation, dropout_rates=net_dropout, batch_norm=batch_norm)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        batch_dict, item_dict, mask = self.get_inputs(inputs)
        emb_list = []
        if batch_dict:
            emb_out = self.embedding_layer(batch_dict, flatten_emb=True)
            emb_list.append(emb_out)
        item_feat_emb = self.embedding_layer(item_dict, flatten_emb=True)
        batch_size = mask.shape[0]
        item_feat_emb = item_feat_emb.view(batch_size, -1, self.item_info_dim)
        target_emb = item_feat_emb[:, -1, :]
        short_seq_emb = item_feat_emb[:, -self.short_seq_len:-1, :]
        short_mask = mask[:, -self.short_seq_len:-1]
        short_interest_emb = self.short_attention(target_emb, short_seq_emb, short_mask)
        long_seq_emb = item_feat_emb[:, 0:-1, :]
        long_interest_emb = self.long_attention(target_emb, long_seq_emb, mask)
        emb_list += [target_emb, short_interest_emb, long_interest_emb]
        feature_emb = torch.cat(emb_list, dim=-1)
        y_pred = self.dnn(feature_emb)
        return_dict = {'y_pred': y_pred}
        return return_dict

    def get_inputs(self, inputs, feature_source=None):
        batch_dict, item_dict, mask = inputs
        X_dict = dict()
        for feature, value in batch_dict.items():
            if feature in self.feature_map.labels:
                continue
            feature_spec = self.feature_map.features[feature]
            if feature_spec['type'] == 'meta':
                continue
            if feature_source and not_in_whitelist(feature_spec['source'], feature_source):
                continue
            X_dict[feature] = value.to(self.device)
        for item, value in item_dict.items():
            item_dict[item] = value.to(self.device)
        return (X_dict, item_dict, mask.to(self.device))

    def get_labels(self, inputs):
        """ Please override get_labels() when using multiple labels!
        """
        labels = self.feature_map.labels
        batch_dict = inputs[0]
        y = batch_dict[labels[0]].to(self.device)
        return y.float().view(-1, 1)

    def get_group_id(self, inputs):
        return inputs[0][self.feature_map.group_id]

    def train_step(self, batch_data):
        return_dict = self.forward(batch_data)
        y_true = self.get_labels(batch_data)
        loss = self.compute_loss(return_dict, y_true)
        loss = loss / self.accumulation_steps
        loss.backward()
        if (self._batch_index + 1) % self.accumulation_steps == 0:
            nn.utils.clip_grad_norm_(self.parameters(), self._max_gradient_norm)
            self.optimizer.step()
            self.optimizer.zero_grad()
        return loss

def get_inputs(self, inputs, feature_source=None):
    batch_dict, item_dict, mask = inputs
    X_dict = dict()
    for feature, value in batch_dict.items():
        if feature in self.feature_map.labels:
            continue
        feature_spec = self.feature_map.features[feature]
        if feature_spec['type'] == 'meta':
            continue
        if feature_source and not_in_whitelist(feature_spec['source'], feature_source):
            continue
        X_dict[feature] = value.to(self.device)
    for item, value in item_dict.items():
        item_dict[item] = value.to(self.device)
    return (X_dict, item_dict, mask.to(self.device))

class DIN(BaseModel):

    def __init__(self, feature_map, model_id='DIN', gpu=-1, dnn_hidden_units=[512, 128, 64], dnn_activations='ReLU', attention_hidden_units=[64], attention_hidden_activations='Dice', attention_output_activation=None, attention_dropout=0, learning_rate=0.001, embedding_dim=10, net_dropout=0, batch_norm=False, din_use_softmax=False, accumulation_steps=1, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(DIN, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        if isinstance(dnn_activations, str) and dnn_activations.lower() == 'dice':
            dnn_activations = [Dice(units) for units in dnn_hidden_units]
        self.feature_map = feature_map
        self.embedding_dim = embedding_dim
        self.item_info_dim = 0
        for feat, spec in self.feature_map.features.items():
            if spec.get('source') == 'item':
                self.item_info_dim += spec.get('embedding_dim', embedding_dim)
        self.accumulation_steps = accumulation_steps
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        self.attention_layers = DIN_Attention(self.item_info_dim, attention_units=attention_hidden_units, hidden_activations=attention_hidden_activations, output_activation=attention_output_activation, dropout_rate=attention_dropout, use_softmax=din_use_softmax)
        input_dim = feature_map.sum_emb_out_dim() + self.item_info_dim
        self.dnn = MLP_Block(input_dim=input_dim, output_dim=1, hidden_units=dnn_hidden_units, hidden_activations=dnn_activations, output_activation=self.output_activation, dropout_rates=net_dropout, batch_norm=batch_norm)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        batch_dict, item_dict, mask = self.get_inputs(inputs)
        emb_list = []
        if batch_dict:
            emb_out = self.embedding_layer(batch_dict, flatten_emb=True)
            emb_list.append(emb_out)
        item_feat_emb = self.embedding_layer(item_dict, flatten_emb=True)
        batch_size = mask.shape[0]
        item_feat_emb = item_feat_emb.view(batch_size, -1, self.item_info_dim)
        target_emb = item_feat_emb[:, -1, :]
        sequence_emb = item_feat_emb[:, 0:-1, :]
        pooling_emb = self.attention_layers(target_emb, sequence_emb, mask)
        emb_list += [target_emb, pooling_emb]
        feature_emb = torch.cat(emb_list, dim=-1)
        y_pred = self.dnn(feature_emb)
        return_dict = {'y_pred': y_pred}
        return return_dict

    def get_inputs(self, inputs, feature_source=None):
        batch_dict, item_dict, mask = inputs
        X_dict = dict()
        for feature, value in batch_dict.items():
            if feature in self.feature_map.labels:
                continue
            feature_spec = self.feature_map.features[feature]
            if feature_spec['type'] == 'meta':
                continue
            if feature_source and not_in_whitelist(feature_spec['source'], feature_source):
                continue
            X_dict[feature] = value.to(self.device)
        for item, value in item_dict.items():
            item_dict[item] = value.to(self.device)
        return (X_dict, item_dict, mask.to(self.device))

    def get_labels(self, inputs):
        """ Please override get_labels() when using multiple labels!
        """
        labels = self.feature_map.labels
        batch_dict = inputs[0]
        y = batch_dict[labels[0]].to(self.device)
        return y.float().view(-1, 1)

    def get_group_id(self, inputs):
        return inputs[0][self.feature_map.group_id]

    def train_step(self, batch_data):
        return_dict = self.forward(batch_data)
        y_true = self.get_labels(batch_data)
        loss = self.compute_loss(return_dict, y_true)
        loss = loss / self.accumulation_steps
        loss.backward()
        if (self._batch_index + 1) % self.accumulation_steps == 0:
            nn.utils.clip_grad_norm_(self.parameters(), self._max_gradient_norm)
            self.optimizer.step()
            self.optimizer.zero_grad()
        return loss

def get_inputs(self, inputs, feature_source=None):
    batch_dict, item_dict, mask = inputs
    X_dict = dict()
    for feature, value in batch_dict.items():
        if feature in self.feature_map.labels:
            continue
        feature_spec = self.feature_map.features[feature]
        if feature_spec['type'] == 'meta':
            continue
        if feature_source and not_in_whitelist(feature_spec['source'], feature_source):
            continue
        X_dict[feature] = value.to(self.device)
    for item, value in item_dict.items():
        item_dict[item] = value.to(self.device)
    return (X_dict, item_dict, mask.to(self.device))

class FinalMLP(BaseModel):

    def __init__(self, feature_map, model_id='FinalMLP', gpu=-1, learning_rate=0.001, embedding_dim=10, mlp1_hidden_units=[64, 64, 64], mlp1_hidden_activations='ReLU', mlp1_dropout=0, mlp1_batch_norm=False, mlp2_hidden_units=[64, 64, 64], mlp2_hidden_activations='ReLU', mlp2_dropout=0, mlp2_batch_norm=False, use_fs=True, fs_hidden_units=[64], fs1_context=[], fs2_context=[], num_heads=1, accumulation_steps=1, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(FinalMLP, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        self.item_info_dim = 0
        for feat, spec in self.feature_map.features.items():
            if spec.get('source') == 'item':
                self.item_info_dim += spec.get('embedding_dim', embedding_dim)
        self.accumulation_steps = accumulation_steps
        self.masked_avg_pooling = MaskedAveragePooling()
        feature_dim = feature_map.sum_emb_out_dim() + self.item_info_dim
        self.mlp1 = MLP_Block(input_dim=feature_dim, output_dim=None, hidden_units=mlp1_hidden_units, hidden_activations=mlp1_hidden_activations, output_activation=None, dropout_rates=mlp1_dropout, batch_norm=mlp1_batch_norm)
        self.mlp2 = MLP_Block(input_dim=feature_dim, output_dim=None, hidden_units=mlp2_hidden_units, hidden_activations=mlp2_hidden_activations, output_activation=None, dropout_rates=mlp2_dropout, batch_norm=mlp2_batch_norm)
        self.use_fs = use_fs
        if self.use_fs:
            self.fs_module = FeatureSelection(feature_map, feature_dim, embedding_dim, fs_hidden_units, fs1_context, fs2_context)
        self.fusion_module = InteractionAggregation(mlp1_hidden_units[-1], mlp2_hidden_units[-1], output_dim=1, num_heads=num_heads)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        batch_dict, item_dict, mask = self.get_inputs(inputs)
        emb_list = []
        if batch_dict:
            emb_out = self.embedding_layer(batch_dict, flatten_emb=True)
            emb_list.append(emb_out)
        item_feat_emb = self.embedding_layer(item_dict, flatten_emb=True)
        batch_size = mask.shape[0]
        item_feat_emb = item_feat_emb.view(batch_size, -1, self.item_info_dim)
        target_emb = item_feat_emb[:, -1, :]
        sequence_emb = item_feat_emb[:, 0:-1, :]
        pooling_emb = self.masked_avg_pooling(sequence_emb, mask)
        emb_list += [target_emb, pooling_emb]
        flat_emb = torch.cat(emb_list, dim=-1)
        feat1, feat2 = (flat_emb, flat_emb)
        y_pred = self.fusion_module(self.mlp1(feat1), self.mlp2(feat2))
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred}
        return return_dict

    def get_inputs(self, inputs, feature_source=None):
        batch_dict, item_dict, mask = inputs
        X_dict = dict()
        for feature, value in batch_dict.items():
            if feature in self.feature_map.labels:
                continue
            feature_spec = self.feature_map.features[feature]
            if feature_spec['type'] == 'meta':
                continue
            if feature_source and not_in_whitelist(feature_spec['source'], feature_source):
                continue
            X_dict[feature] = value.to(self.device)
        for item, value in item_dict.items():
            item_dict[item] = value.to(self.device)
        return (X_dict, item_dict, mask.to(self.device))

    def get_labels(self, inputs):
        """ Please override get_labels() when using multiple labels!
        """
        labels = self.feature_map.labels
        batch_dict = inputs[0]
        y = batch_dict[labels[0]].to(self.device)
        return y.float().view(-1, 1)

    def get_group_id(self, inputs):
        return inputs[0][self.feature_map.group_id]

    def train_step(self, batch_data):
        return_dict = self.forward(batch_data)
        y_true = self.get_labels(batch_data)
        loss = self.compute_loss(return_dict, y_true)
        loss = loss / self.accumulation_steps
        loss.backward()
        if (self._batch_index + 1) % self.accumulation_steps == 0:
            nn.utils.clip_grad_norm_(self.parameters(), self._max_gradient_norm)
            self.optimizer.step()
            self.optimizer.zero_grad()
        return loss

def get_inputs(self, inputs, feature_source=None):
    batch_dict, item_dict, mask = inputs
    X_dict = dict()
    for feature, value in batch_dict.items():
        if feature in self.feature_map.labels:
            continue
        feature_spec = self.feature_map.features[feature]
        if feature_spec['type'] == 'meta':
            continue
        if feature_source and not_in_whitelist(feature_spec['source'], feature_source):
            continue
        X_dict[feature] = value.to(self.device)
    for item, value in item_dict.items():
        item_dict[item] = value.to(self.device)
    return (X_dict, item_dict, mask.to(self.device))

class MIRRN(BaseModel):
    """
    Ref: https://github.com/USTC-StarTeam/MIRRN
    """

    def __init__(self, feature_map, model_id='MIRRN', gpu=-1, dnn_hidden_units=[512, 128, 64], dnn_activations='ReLU', attention_dim=64, num_heads=1, use_scale=True, attention_dropout=0, reuse_hash=True, hash_bits=32, topk=50, max_len=1000, learning_rate=0.001, embedding_dim=10, net_dropout=0, batch_norm=False, short_seq_len=50, accumulation_steps=1, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(MIRRN, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.feature_map = feature_map
        self.embedding_dim = embedding_dim
        self.reuse_hash = reuse_hash
        self.hash_bits = hash_bits
        self.topk = topk
        self.short_seq_len = short_seq_len
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        self.item_info_dim = 0
        for feat, spec in self.feature_map.features.items():
            if spec.get('source') == 'item':
                self.item_info_dim += spec.get('embedding_dim', embedding_dim)
        self.accumulation_steps = accumulation_steps
        self.short_attention = MultiHeadTargetAttention(self.item_info_dim, attention_dim, num_heads, attention_dropout, use_scale)
        self.pos = nn.Embedding(max_len + 1, self.item_info_dim)
        self.random_rotations = nn.Parameter(torch.randn(self.item_info_dim, self.hash_bits), requires_grad=False)
        self.MHFT_block = nn.ModuleList()
        self.MHFT_block.append(FilterLayer2(topk, self.item_info_dim, 0.1, 4))
        self.MHFT_block.append(FilterLayer2(topk, self.item_info_dim, 0.1, 4))
        self.MHFT_block.append(FilterLayer2(topk, self.item_info_dim, 0.1, 4))
        self.long_attention = MultiHeadTargetAttention(self.item_info_dim, attention_dim, num_heads, attention_dropout, use_scale)
        self.dnn = MLP_Block(input_dim=feature_map.sum_emb_out_dim() + self.item_info_dim * 2, output_dim=1, hidden_units=dnn_hidden_units, hidden_activations=dnn_activations, output_activation=self.output_activation, dropout_rates=net_dropout, batch_norm=batch_norm)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        batch_dict, item_dict, mask = self.get_inputs(inputs)
        emb_list = []
        if batch_dict:
            emb_out = self.embedding_layer(batch_dict, flatten_emb=True)
            emb_list.append(emb_out)
        item_feat_emb = self.embedding_layer(item_dict, flatten_emb=True)
        batch_size = mask.shape[0]
        item_feat_emb = item_feat_emb.view(batch_size, -1, self.item_info_dim)
        target_emb = item_feat_emb[:, -1, :]
        short_seq_emb = item_feat_emb[:, -self.short_seq_len:-1, :]
        short_mask = mask[:, -self.short_seq_len:-1]
        short_interest = self.short_attention(target_emb, short_seq_emb, short_mask)
        sequence_emb = item_feat_emb[:, 0:-1, :]
        topk_target_emb, topk_target_mask, topk_target_index = self.topk_retrieval(self.random_rotations, target_emb, sequence_emb, mask, self.topk)
        short_emb = sequence_emb[:, -16:]
        mean_short_emb = self.masked_mean(short_emb, mask[:, -16:], dim=1)
        topk_short_emb, topk_short_mask, topk_short_index = self.topk_retrieval(self.random_rotations, mean_short_emb, sequence_emb, mask, self.topk)
        mean_global_emb = self.masked_mean(sequence_emb, mask, dim=1)
        topk_global_emb, topk_global_mask, topk_global_index = self.topk_retrieval(self.random_rotations, mean_global_emb, sequence_emb, mask, self.topk)
        pos_mask_target = sequence_emb.shape[1] - topk_target_index
        pos_target = self.pos(pos_mask_target)
        topk_target_emb += pos_target * 0.02
        pos_mask_short = sequence_emb.shape[1] - topk_short_index
        pos_short = self.pos(pos_mask_short)
        topk_short_emb += pos_short * 0.02
        pos_mask_global = sequence_emb.shape[1] - topk_global_index
        pos_global = self.pos(pos_mask_global)
        topk_global_emb += pos_global * 0.02
        target_interest_emb = self.MHFT_block[0](topk_target_emb).mean(1)
        short_interest_emb = self.MHFT_block[1](topk_short_emb).mean(1)
        global_interest_emb = self.MHFT_block[2](topk_global_emb).mean(1)
        interest_emb = torch.stack((target_interest_emb, short_interest_emb, global_interest_emb), 1)
        long_interest = self.long_attention(target_emb, interest_emb)
        emb_list += [target_emb, short_interest, long_interest]
        feature_emb = torch.cat(emb_list, dim=-1)
        y_pred = self.dnn(feature_emb)
        return_dict = {'y_pred': y_pred}
        return return_dict

    def masked_mean(self, tensor, mask, dim=1):
        mask = mask.unsqueeze(-1)
        masked_sum = (tensor * mask).sum(dim)
        masked_count = mask.sum(dim)
        return masked_sum / (masked_count + 1e-09)

    def topk_retrieval(self, random_rotations, target_item, history_sequence, mask, topk=5):
        if not self.reuse_hash:
            random_rotations = torch.randn(target_item.size(1), self.hash_bits, device=target_item.device)
        target_hash = self.lsh_hash(target_item.unsqueeze(1), random_rotations)
        sequence_hash = self.lsh_hash(history_sequence, random_rotations)
        hash_sim = -torch.abs(sequence_hash - target_hash).sum(dim=-1)
        hash_sim = hash_sim.masked_fill_(mask.float() == 0, -(self.hash_bits + 1))
        topk = min(topk, hash_sim.shape[1])
        topk_index = hash_sim.topk(topk, dim=1, largest=True, sorted=True)[1]
        topk_index = topk_index.sort(-1)[0]
        topk_emb = torch.gather(history_sequence, 1, topk_index.unsqueeze(-1).expand(-1, -1, history_sequence.shape[-1]))
        topk_mask = torch.gather(mask, 1, topk_index)
        return (topk_emb, topk_mask, topk_index)

    def lsh_hash(self, vecs, random_rotations):
        """ See the tensorflow-lsh-functions for reference:
            https://github.com/brc7/tensorflow-lsh-functions/blob/main/lsh_functions.py

            Input: vecs, with hape B x seq_len x d
        """
        rotated_vecs = torch.matmul(vecs, random_rotations)
        hash_code = torch.relu(torch.sign(rotated_vecs))
        return hash_code

    def get_inputs(self, inputs, feature_source=None):
        batch_dict, item_dict, mask = inputs
        X_dict = dict()
        for feature, value in batch_dict.items():
            if feature in self.feature_map.labels:
                continue
            feature_spec = self.feature_map.features[feature]
            if feature_spec['type'] == 'meta':
                continue
            if feature_source and not_in_whitelist(feature_spec['source'], feature_source):
                continue
            X_dict[feature] = value.to(self.device)
        for item, value in item_dict.items():
            item_dict[item] = value.to(self.device)
        return (X_dict, item_dict, mask.to(self.device))

    def get_labels(self, inputs):
        """ Please override get_labels() when using multiple labels!
        """
        labels = self.feature_map.labels
        batch_dict = inputs[0]
        y = batch_dict[labels[0]].to(self.device)
        return y.float().view(-1, 1)

    def get_group_id(self, inputs):
        return inputs[0][self.feature_map.group_id]

    def train_step(self, batch_data):
        return_dict = self.forward(batch_data)
        y_true = self.get_labels(batch_data)
        loss = self.compute_loss(return_dict, y_true)
        loss = loss / self.accumulation_steps
        loss.backward()
        if (self._batch_index + 1) % self.accumulation_steps == 0:
            nn.utils.clip_grad_norm_(self.parameters(), self._max_gradient_norm)
            self.optimizer.step()
            self.optimizer.zero_grad()
        return loss

def get_inputs(self, inputs, feature_source=None):
    batch_dict, item_dict, mask = inputs
    X_dict = dict()
    for feature, value in batch_dict.items():
        if feature in self.feature_map.labels:
            continue
        feature_spec = self.feature_map.features[feature]
        if feature_spec['type'] == 'meta':
            continue
        if feature_source and not_in_whitelist(feature_spec['source'], feature_source):
            continue
        X_dict[feature] = value.to(self.device)
    for item, value in item_dict.items():
        item_dict[item] = value.to(self.device)
    return (X_dict, item_dict, mask.to(self.device))

class ETA(BaseModel):

    def __init__(self, feature_map, model_id='ETA', gpu=-1, dnn_hidden_units=[512, 128, 64], dnn_activations='ReLU', attention_dim=64, num_heads=1, use_scale=True, attention_dropout=0, reuse_hash=True, hash_bits=32, topk=50, learning_rate=0.001, embedding_dim=10, net_dropout=0, batch_norm=False, short_seq_len=50, accumulation_steps=1, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(ETA, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.feature_map = feature_map
        self.embedding_dim = embedding_dim
        self.reuse_hash = reuse_hash
        self.hash_bits = hash_bits
        self.topk = topk
        self.short_seq_len = short_seq_len
        self.item_info_dim = 0
        for feat, spec in self.feature_map.features.items():
            if spec.get('source') == 'item':
                self.item_info_dim += spec.get('embedding_dim', embedding_dim)
        self.accumulation_steps = accumulation_steps
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        self.short_attention = MultiHeadTargetAttention(self.item_info_dim, attention_dim, num_heads, attention_dropout, use_scale)
        self.random_rotations = nn.Parameter(torch.randn(1, self.item_info_dim, self.hash_bits), requires_grad=False)
        self.long_attention = MultiHeadTargetAttention(self.item_info_dim, attention_dim, num_heads, attention_dropout, use_scale)
        input_dim = feature_map.sum_emb_out_dim() + self.item_info_dim * 2
        self.dnn = MLP_Block(input_dim=input_dim, output_dim=1, hidden_units=dnn_hidden_units, hidden_activations=dnn_activations, output_activation=self.output_activation, dropout_rates=net_dropout, batch_norm=batch_norm)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        batch_dict, item_dict, mask = self.get_inputs(inputs)
        emb_list = []
        if batch_dict:
            emb_out = self.embedding_layer(batch_dict, flatten_emb=True)
            emb_list.append(emb_out)
        item_feat_emb = self.embedding_layer(item_dict, flatten_emb=True)
        batch_size = mask.shape[0]
        item_feat_emb = item_feat_emb.view(batch_size, -1, self.item_info_dim)
        target_emb = item_feat_emb[:, -1, :]
        short_seq_emb = item_feat_emb[:, -self.short_seq_len:-1, :]
        short_mask = mask[:, -self.short_seq_len:-1]
        short_interest_emb = self.short_attention(target_emb, short_seq_emb, short_mask)
        long_seq_emb = item_feat_emb[:, 0:-1, :]
        topk_emb, topk_mask = self.topk_retrieval(self.random_rotations, target_emb, long_seq_emb, mask, self.topk)
        long_interest_emb = self.long_attention(target_emb, topk_emb, topk_mask)
        emb_list += [target_emb, short_interest_emb, long_interest_emb]
        feature_emb = torch.cat(emb_list, dim=-1)
        y_pred = self.dnn(feature_emb)
        return_dict = {'y_pred': y_pred}
        return return_dict

    def topk_retrieval(self, random_rotations, target_item, history_sequence, mask, topk=5):
        if self.reuse_hash:
            random_rotations = random_rotations.repeat(target_item.size(0), 1, 1)
        else:
            random_rotations = torch.randn(target_item.size(0), target_item.size(1), self.hash_bits, device=target_item.device)
        sequence_hash = self.lsh_hash(history_sequence, random_rotations)
        target_hash = self.lsh_hash(target_item.unsqueeze(1), random_rotations)
        hash_dis = torch.abs(sequence_hash - target_hash).sum(dim=-1)
        hash_dis = hash_dis.masked_fill_(mask.float() == 0, 1 + self.hash_bits)
        topk = min(topk, hash_dis.shape[1])
        topk_index = hash_dis.topk(topk, dim=1, largest=False, sorted=True)[1]
        topk_emb = torch.gather(history_sequence, 1, topk_index.unsqueeze(-1).expand(-1, -1, history_sequence.shape[-1]))
        topk_mask = torch.gather(mask, 1, topk_index)
        return (topk_emb, topk_mask)

    def lsh_hash(self, vecs, random_rotations):
        """ See the tensorflow-lsh-functions for reference:
            https://github.com/brc7/tensorflow-lsh-functions/blob/main/lsh_functions.py
            
            Input: vecs, with shape B x seq_len x d
            Output: hash_code, with shape B x seq_len x hash_bits
        """
        rotated_vecs = torch.einsum('bld,bdh->blh', vecs, random_rotations).unsqueeze(-1)
        rotated_vecs = torch.cat([-rotated_vecs, rotated_vecs], dim=-1)
        hash_code = torch.argmax(rotated_vecs, dim=-1).float()
        return hash_code

    def get_inputs(self, inputs, feature_source=None):
        batch_dict, item_dict, mask = inputs
        X_dict = dict()
        for feature, value in batch_dict.items():
            if feature in self.feature_map.labels:
                continue
            feature_spec = self.feature_map.features[feature]
            if feature_spec['type'] == 'meta':
                continue
            if feature_source and not_in_whitelist(feature_spec['source'], feature_source):
                continue
            X_dict[feature] = value.to(self.device)
        for item, value in item_dict.items():
            item_dict[item] = value.to(self.device)
        return (X_dict, item_dict, mask.to(self.device))

    def get_labels(self, inputs):
        """ Please override get_labels() when using multiple labels!
        """
        labels = self.feature_map.labels
        batch_dict = inputs[0]
        y = batch_dict[labels[0]].to(self.device)
        return y.float().view(-1, 1)

    def get_group_id(self, inputs):
        return inputs[0][self.feature_map.group_id]

    def train_step(self, batch_data):
        return_dict = self.forward(batch_data)
        y_true = self.get_labels(batch_data)
        loss = self.compute_loss(return_dict, y_true)
        loss = loss / self.accumulation_steps
        loss.backward()
        if (self._batch_index + 1) % self.accumulation_steps == 0:
            nn.utils.clip_grad_norm_(self.parameters(), self._max_gradient_norm)
            self.optimizer.step()
            self.optimizer.zero_grad()
        return loss

def get_inputs(self, inputs, feature_source=None):
    batch_dict, item_dict, mask = inputs
    X_dict = dict()
    for feature, value in batch_dict.items():
        if feature in self.feature_map.labels:
            continue
        feature_spec = self.feature_map.features[feature]
        if feature_spec['type'] == 'meta':
            continue
        if feature_source and not_in_whitelist(feature_spec['source'], feature_source):
            continue
        X_dict[feature] = value.to(self.device)
    for item, value in item_dict.items():
        item_dict[item] = value.to(self.device)
    return (X_dict, item_dict, mask.to(self.device))

class SIM(BaseModel):

    def __init__(self, feature_map, model_id='SIM', gpu=-1, dnn_hidden_units=[512, 128, 64], dnn_activations='ReLU', attention_dropout=0, attention_dim=64, num_heads=1, gsu_type='soft', short_seq_len=50, topk=50, alpha=1, beta=1, learning_rate=0.001, embedding_dim=10, net_dropout=0, batch_norm=False, accumulation_steps=1, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(SIM, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.feature_map = feature_map
        self.embedding_dim = embedding_dim
        self.topk = topk
        self.short_seq_len = short_seq_len
        self.alpha = alpha
        self.beta = beta
        assert gsu_type == 'soft', 'Only support soft search currently!'
        self.item_info_dim = 0
        for feat, spec in self.feature_map.features.items():
            if spec.get('source') == 'item':
                self.item_info_dim += spec.get('embedding_dim', embedding_dim)
        self.accumulation_steps = accumulation_steps
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        self.W_a = nn.Linear(self.item_info_dim, attention_dim, bias=False)
        self.W_b = nn.Linear(self.item_info_dim, attention_dim, bias=False)
        self.short_attention = MultiHeadTargetAttention(self.item_info_dim, attention_dim, num_heads, attention_dropout)
        self.long_attention = MultiHeadTargetAttention(self.item_info_dim, attention_dim, num_heads, attention_dropout)
        input_dim = feature_map.sum_emb_out_dim() + self.item_info_dim
        self.dnn_aux = MLP_Block(input_dim=input_dim, output_dim=1, hidden_units=dnn_hidden_units, hidden_activations=dnn_activations, output_activation=self.output_activation, dropout_rates=net_dropout, batch_norm=batch_norm)
        input_dim = feature_map.sum_emb_out_dim() + self.item_info_dim * 2
        self.dnn = MLP_Block(input_dim=input_dim, output_dim=1, hidden_units=dnn_hidden_units, hidden_activations=dnn_activations, output_activation=self.output_activation, dropout_rates=net_dropout, batch_norm=batch_norm)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        batch_dict, item_dict, mask = self.get_inputs(inputs)
        emb_list = []
        if batch_dict:
            emb_out = self.embedding_layer(batch_dict, flatten_emb=True)
            emb_list.append(emb_out)
        item_feat_emb = self.embedding_layer(item_dict, flatten_emb=True)
        batch_size = mask.shape[0]
        item_feat_emb = item_feat_emb.view(batch_size, -1, self.item_info_dim)
        target_emb = item_feat_emb[:, -1, :]
        short_seq_emb = item_feat_emb[:, -self.short_seq_len:-1, :]
        short_mask = mask[:, -self.short_seq_len:-1]
        short_interest_emb = self.short_attention(target_emb, short_seq_emb, short_mask)
        long_seq_emb = item_feat_emb[:, 0:-1, :]
        q = self.W_a(target_emb).unsqueeze(1)
        k = self.W_b(long_seq_emb)
        qk = torch.bmm(q, k.transpose(-1, -2)).squeeze(1) * mask
        pooled_u_rep = torch.bmm(qk.unsqueeze(1), long_seq_emb).squeeze(1)
        emb_list += [target_emb, pooled_u_rep]
        y_aux = self.dnn_aux(torch.cat(emb_list, dim=-1))
        topk = min(self.topk, qk.shape[1])
        topk_index = qk.topk(topk, dim=1, largest=True, sorted=True)[1]
        topk_emb = torch.gather(long_seq_emb, 1, topk_index.unsqueeze(-1).expand(-1, -1, long_seq_emb.shape[-1]))
        topk_mask = torch.gather(mask, 1, topk_index)
        long_interest_emb = self.long_attention(target_emb, topk_emb, topk_mask)
        emb_list = emb_list[0:-1] + [short_interest_emb, long_interest_emb]
        feature_emb = torch.cat(emb_list, dim=-1)
        y_pred = self.dnn(feature_emb)
        return_dict = {'y_pred': y_pred, 'y_aux': y_aux}
        return return_dict

    def add_loss(self, return_dict, y_true):
        loss_gsu = self.loss_fn(return_dict['y_aux'], y_true, reduction='mean')
        loss_esu = self.loss_fn(return_dict['y_pred'], y_true, reduction='mean')
        return self.alpha * loss_gsu + self.beta * loss_esu

    def get_inputs(self, inputs, feature_source=None):
        batch_dict, item_dict, mask = inputs
        X_dict = dict()
        for feature, value in batch_dict.items():
            if feature in self.feature_map.labels:
                continue
            feature_spec = self.feature_map.features[feature]
            if feature_spec['type'] == 'meta':
                continue
            if feature_source and not_in_whitelist(feature_spec['source'], feature_source):
                continue
            X_dict[feature] = value.to(self.device)
        for item, value in item_dict.items():
            item_dict[item] = value.to(self.device)
        return (X_dict, item_dict, mask.to(self.device))

    def get_labels(self, inputs):
        """ Please override get_labels() when using multiple labels!
        """
        labels = self.feature_map.labels
        batch_dict = inputs[0]
        y = batch_dict[labels[0]].to(self.device)
        return y.float().view(-1, 1)

    def get_group_id(self, inputs):
        return inputs[0][self.feature_map.group_id]

    def train_step(self, batch_data):
        return_dict = self.forward(batch_data)
        y_true = self.get_labels(batch_data)
        loss = self.compute_loss(return_dict, y_true)
        loss = loss / self.accumulation_steps
        loss.backward()
        if (self._batch_index + 1) % self.accumulation_steps == 0:
            nn.utils.clip_grad_norm_(self.parameters(), self._max_gradient_norm)
            self.optimizer.step()
            self.optimizer.zero_grad()
        return loss

def get_inputs(self, inputs, feature_source=None):
    batch_dict, item_dict, mask = inputs
    X_dict = dict()
    for feature, value in batch_dict.items():
        if feature in self.feature_map.labels:
            continue
        feature_spec = self.feature_map.features[feature]
        if feature_spec['type'] == 'meta':
            continue
        if feature_source and not_in_whitelist(feature_spec['source'], feature_source):
            continue
        X_dict[feature] = value.to(self.device)
    for item, value in item_dict.items():
        item_dict[item] = value.to(self.device)
    return (X_dict, item_dict, mask.to(self.device))

class SDIM(BaseModel):

    def __init__(self, feature_map, model_id='SDIM', gpu=-1, dnn_hidden_units=[512, 128, 64], dnn_activations='ReLU', attention_dim=64, use_qkvo=True, num_heads=1, use_scale=True, attention_dropout=0, reuse_hash=True, num_hashes=1, hash_bits=4, learning_rate=0.001, embedding_dim=10, net_dropout=0, batch_norm=False, l2_norm=False, short_seq_len=50, accumulation_steps=1, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(SDIM, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.feature_map = feature_map
        self.embedding_dim = embedding_dim
        self.reuse_hash = reuse_hash
        self.num_hashes = num_hashes
        self.hash_bits = hash_bits
        self.short_seq_len = short_seq_len
        self.item_info_dim = 0
        for feat, spec in self.feature_map.features.items():
            if spec.get('source') == 'item':
                self.item_info_dim += spec.get('embedding_dim', embedding_dim)
        self.accumulation_steps = accumulation_steps
        self.l2_norm = l2_norm
        self.powers_of_two = nn.Parameter(torch.tensor([2.0 ** i for i in range(hash_bits)]), requires_grad=False)
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        self.short_attention = MultiHeadTargetAttention(self.item_info_dim, attention_dim, num_heads, attention_dropout, use_scale, use_qkvo)
        self.random_rotations = nn.Parameter(torch.randn(1, self.item_info_dim, self.num_hashes, self.hash_bits), requires_grad=False)
        input_dim = feature_map.sum_emb_out_dim() + self.item_info_dim * 2
        self.dnn = MLP_Block(input_dim=input_dim, output_dim=1, hidden_units=dnn_hidden_units, hidden_activations=dnn_activations, output_activation=self.output_activation, dropout_rates=net_dropout, batch_norm=batch_norm)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        batch_dict, item_dict, mask = self.get_inputs(inputs)
        emb_list = []
        if batch_dict:
            emb_out = self.embedding_layer(batch_dict, flatten_emb=True)
            emb_list.append(emb_out)
        item_feat_emb = self.embedding_layer(item_dict, flatten_emb=True)
        batch_size = mask.shape[0]
        item_feat_emb = item_feat_emb.view(batch_size, -1, self.item_info_dim)
        target_emb = item_feat_emb[:, -1, :]
        short_seq_emb = item_feat_emb[:, -self.short_seq_len:-1, :]
        short_mask = mask[:, -self.short_seq_len:-1]
        short_interest_emb = self.short_attention(target_emb, short_seq_emb, short_mask)
        long_seq_emb = item_feat_emb[:, 0:-1, :]
        long_interest_emb = self.lsh_attentioin(self.random_rotations, target_emb, long_seq_emb, mask)
        emb_list += [target_emb, long_interest_emb, short_interest_emb]
        feature_emb = torch.cat(emb_list, dim=-1)
        y_pred = self.dnn(feature_emb)
        return_dict = {'y_pred': y_pred}
        return return_dict

    def lsh_attentioin(self, random_rotations, target_item, history_sequence, mask):
        if self.reuse_hash:
            random_rotations = random_rotations.repeat(target_item.size(0), 1, 1, 1)
        else:
            random_rotations = torch.randn(target_item.size(0), target_item.size(1), self.num_hashes, self.hash_bits, device=target_item.device)
        sequence_bucket = self.lsh_hash(history_sequence, random_rotations)
        target_bucket = self.lsh_hash(target_item.unsqueeze(1), random_rotations).repeat(1, sequence_bucket.shape[1], 1)
        collide_mask = ((sequence_bucket == target_bucket) * mask.unsqueeze(-1)).float().permute(2, 0, 1)
        _, collide_index = torch.nonzero(collide_mask.flatten(start_dim=1), as_tuple=True)
        offsets = collide_mask.sum(dim=-1).flatten().cumsum(dim=0)
        offsets = torch.cat([torch.zeros(1, device=offsets.device), offsets]).long()
        attn_out = F.embedding_bag(collide_index, history_sequence.reshape(-1, target_item.size(1)), offsets, mode='sum', include_last_offset=True)
        if self.l2_norm:
            attn_out = F.normalize(attn_out, dim=-1)
        attn_out = attn_out.view(self.num_hashes, -1, target_item.size(1)).mean(dim=0)
        return attn_out

    def lsh_hash(self, vecs, random_rotations):
        """ See the tensorflow-lsh-functions for reference:
            https://github.com/brc7/tensorflow-lsh-functions/blob/main/lsh_functions.py
            
            Input: vecs, with shape B x seq_len x d
            Output: hash_bucket, with shape B x seq_len x num_hashes
        """
        rotated_vecs = torch.einsum('bld,bdht->blht', vecs, random_rotations).unsqueeze(-1)
        rotated_vecs = torch.cat([-rotated_vecs, rotated_vecs], dim=-1)
        hash_code = torch.argmax(rotated_vecs, dim=-1).float()
        hash_bucket = torch.matmul(hash_code, self.powers_of_two.unsqueeze(-1)).squeeze(-1)
        return hash_bucket

    def get_inputs(self, inputs, feature_source=None):
        batch_dict, item_dict, mask = inputs
        X_dict = dict()
        for feature, value in batch_dict.items():
            if feature in self.feature_map.labels:
                continue
            feature_spec = self.feature_map.features[feature]
            if feature_spec['type'] == 'meta':
                continue
            if feature_source and not_in_whitelist(feature_spec['source'], feature_source):
                continue
            X_dict[feature] = value.to(self.device)
        for item, value in item_dict.items():
            item_dict[item] = value.to(self.device)
        return (X_dict, item_dict, mask.to(self.device))

    def get_labels(self, inputs):
        """ Please override get_labels() when using multiple labels!
        """
        labels = self.feature_map.labels
        batch_dict = inputs[0]
        y = batch_dict[labels[0]].to(self.device)
        return y.float().view(-1, 1)

    def get_group_id(self, inputs):
        return inputs[0][self.feature_map.group_id]

    def train_step(self, batch_data):
        return_dict = self.forward(batch_data)
        y_true = self.get_labels(batch_data)
        loss = self.compute_loss(return_dict, y_true)
        loss = loss / self.accumulation_steps
        loss.backward()
        if (self._batch_index + 1) % self.accumulation_steps == 0:
            nn.utils.clip_grad_norm_(self.parameters(), self._max_gradient_norm)
            self.optimizer.step()
            self.optimizer.zero_grad()
        return loss

def get_inputs(self, inputs, feature_source=None):
    batch_dict, item_dict, mask = inputs
    X_dict = dict()
    for feature, value in batch_dict.items():
        if feature in self.feature_map.labels:
            continue
        feature_spec = self.feature_map.features[feature]
        if feature_spec['type'] == 'meta':
            continue
        if feature_source and not_in_whitelist(feature_spec['source'], feature_source):
            continue
        X_dict[feature] = value.to(self.device)
    for item, value in item_dict.items():
        item_dict[item] = value.to(self.device)
    return (X_dict, item_dict, mask.to(self.device))

class TransAct(BaseModel):
    """
    The TransAct model class that implements transformer-based realtime user action model.
    Make sure the behavior sequences are sorted in chronological order and padded in the left part.

    Args:
        feature_map: A FeatureMap instance used to store feature specs (e.g., vocab_size).
        model_id: Equivalent to model class name by default, which is used in config to determine 
            which model to call.
        gpu: gpu device used to load model.
        hidden_activations: hidden activations used in MLP blocks (default="ReLU").
        dcn_cross_layers: number of cross layers in DCNv2 (default=3).
        dcn_hidden_units: hidden units of deep part in DCNv2 (default=[256, 128, 64]).
        mlp_hidden_units: hidden units of MLP on top of DCNv2 (default=[]).
        num_heads: number of heads of transformer (default=1).
        transformer_layers: number of stacked transformer layers used in TransAct (default=1).
        transformer_dropout: dropout rate used in transformer (default=0).
        dim_feedforward: FFN dimension in transformer (default=512)
        learning_rate: learning rate for training (default=1e-3).
        embedding_dim: embedding dimension of features (default=64).
        net_dropout: dropout rate for deep part in DCNv2 (default=0).
        batch_norm: whether to apply batch normalization in DCNv2 (default=False).
        target_item_field (List[tuple] or List[str]): which field is used for target item
            embedding. When tuple is applied, the fields in each tuple are concatenated, e.g.,
            item_id and cate_id can be concatenated as target item embedding.
        sequence_item_field (List[tuple] or List[str]): which field is used for sequence item
            embedding. When tuple is applied, the fields in each tuple are concatenated.
        first_k_cols: number of hidden representations to pick as transformer output (default=1).
        use_time_window_mask (Boolean): whether to use time window mask in TransAct (default=False).
        time_window_ms: time window in ms to mask the most recent behaviors (default=86400000).
        concat_max_pool (Boolean): whether cancate max pooling result in transformer output
            (default=True).
        embedding_regularizer: regularization term used for embedding parameters (default=0).
        net_regularizer: regularization term used for network parameters (default=0).
    """

    def __init__(self, feature_map, model_id='TransAct', gpu=-1, hidden_activations='ReLU', dcn_cross_layers=3, dcn_hidden_units=[256, 128, 64], mlp_hidden_units=[], num_heads=1, transformer_layers=1, transformer_dropout=0, dim_feedforward=512, learning_rate=0.001, embedding_dim=64, net_dropout=0, batch_norm=False, first_k_cols=1, use_time_window_mask=False, time_window_ms=86400000, concat_max_pool=True, accumulation_steps=1, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super().__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.feature_map = feature_map
        self.embedding_dim = embedding_dim
        self.accumulation_steps = accumulation_steps
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        self.item_info_dim = 0
        for feat, spec in self.feature_map.features.items():
            if spec.get('source') == 'item':
                self.item_info_dim += spec.get('embedding_dim', embedding_dim)
        transformer_in_dim = self.item_info_dim * 2
        seq_out_dim = (first_k_cols + int(concat_max_pool)) * transformer_in_dim
        self.transformer_encoders = TransActTransformer(transformer_in_dim, dim_feedforward=dim_feedforward, num_heads=num_heads, dropout=transformer_dropout, transformer_layers=transformer_layers, use_time_window_mask=use_time_window_mask, time_window_ms=time_window_ms, first_k_cols=first_k_cols, concat_max_pool=concat_max_pool)
        dcn_in_dim = feature_map.sum_emb_out_dim() + seq_out_dim
        self.crossnet = CrossNetV2(dcn_in_dim, dcn_cross_layers)
        self.parallel_dnn = MLP_Block(input_dim=dcn_in_dim, output_dim=None, hidden_units=dcn_hidden_units, hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm)
        dcn_out_dim = dcn_in_dim + dcn_hidden_units[-1]
        self.mlp = MLP_Block(input_dim=dcn_out_dim, output_dim=1, hidden_units=mlp_hidden_units, hidden_activations=hidden_activations, output_activation=self.output_activation)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        batch_dict, item_dict, pad_mask = self.get_inputs(inputs)
        feature_emb = []
        if batch_dict:
            emb_out = self.embedding_layer(batch_dict, flatten_emb=True)
            feature_emb.append(emb_out)
        item_feat_emb = self.embedding_layer(item_dict, flatten_emb=True)
        batch_size = pad_mask.shape[0]
        item_feat_emb = item_feat_emb.view(batch_size, -1, self.item_info_dim)
        target_emb = item_feat_emb[:, -1, :]
        sequence_emb = item_feat_emb[:, 0:-1, :]
        transformer_out = self.transformer_encoders(target_emb, sequence_emb, mask=~pad_mask.bool())
        feature_emb += [target_emb, transformer_out]
        dcn_in_emb = torch.cat(feature_emb, dim=-1)
        cross_out = self.crossnet(dcn_in_emb)
        dnn_out = self.parallel_dnn(dcn_in_emb)
        y_pred = self.mlp(torch.cat([cross_out, dnn_out], dim=-1))
        return_dict = {'y_pred': y_pred}
        return return_dict

    def get_inputs(self, inputs, feature_source=None):
        batch_dict, item_dict, mask = inputs
        X_dict = dict()
        for feature, value in batch_dict.items():
            if feature in self.feature_map.labels:
                continue
            feature_spec = self.feature_map.features[feature]
            if feature_spec['type'] == 'meta':
                continue
            if feature_source and not_in_whitelist(feature_spec['source'], feature_source):
                continue
            X_dict[feature] = value.to(self.device)
        for item, value in item_dict.items():
            item_dict[item] = value.to(self.device)
        return (X_dict, item_dict, mask.to(self.device))

    def get_labels(self, inputs):
        """ Please override get_labels() when using multiple labels!
        """
        labels = self.feature_map.labels
        batch_dict = inputs[0]
        y = batch_dict[labels[0]].to(self.device)
        return y.float().view(-1, 1)

    def get_group_id(self, inputs):
        return inputs[0][self.feature_map.group_id]

    def train_step(self, batch_data):
        return_dict = self.forward(batch_data)
        y_true = self.get_labels(batch_data)
        loss = self.compute_loss(return_dict, y_true)
        loss = loss / self.accumulation_steps
        loss.backward()
        if (self._batch_index + 1) % self.accumulation_steps == 0:
            nn.utils.clip_grad_norm_(self.parameters(), self._max_gradient_norm)
            self.optimizer.step()
            self.optimizer.zero_grad()
        return loss

def get_inputs(self, inputs, feature_source=None):
    batch_dict, item_dict, mask = inputs
    X_dict = dict()
    for feature, value in batch_dict.items():
        if feature in self.feature_map.labels:
            continue
        feature_spec = self.feature_map.features[feature]
        if feature_spec['type'] == 'meta':
            continue
        if feature_source and not_in_whitelist(feature_spec['source'], feature_source):
            continue
        X_dict[feature] = value.to(self.device)
    for item, value in item_dict.items():
        item_dict[item] = value.to(self.device)
    return (X_dict, item_dict, mask.to(self.device))

class DIEN(BaseModel):
    """ Implementation of DIEN model based on the following reference code:
        https://github.com/mouna99/dien
    """

    def __init__(self, feature_map, model_id='DIEN', gpu=-1, dnn_hidden_units=[200, 80], dnn_activations='ReLU', learning_rate=0.001, embedding_dim=16, net_dropout=0, batch_norm=True, gru_type='AUGRU', enable_sum_pooling=False, attention_dropout=0, attention_type='bilinear_attention', attention_hidden_units=[80, 40], attention_activation='Dice', use_attention_softmax=True, item_info_fields=1, accumulation_steps=1, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(DIEN, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.feature_map = feature_map
        self.embedding_dim = embedding_dim
        self.item_info_dim = 0
        for feat, spec in self.feature_map.features.items():
            if spec.get('source') == 'item':
                self.item_info_dim += spec.get('embedding_dim', embedding_dim)
        self.accumulation_steps = accumulation_steps
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        self.sum_pooling = MaskedSumPooling()
        self.gru_type = gru_type
        self.extraction_modules = nn.ModuleList()
        self.evolving_modules = nn.ModuleList()
        self.attention_modules = nn.ModuleList()
        self.extraction_modules.append(nn.GRU(input_size=self.item_info_dim, hidden_size=self.item_info_dim, batch_first=True))
        if gru_type in ['AGRU', 'AUGRU']:
            self.evolving_modules.append(DynamicGRU(self.item_info_dim, self.item_info_dim, gru_type=gru_type))
        else:
            self.evolving_modules.append(nn.GRU(input_size=self.item_info_dim, hidden_size=self.item_info_dim, batch_first=True))
        if gru_type in ['AIGRU', 'AGRU', 'AUGRU']:
            self.attention_modules.append(AttentionLayer(self.item_info_dim, attention_type=attention_type, attention_hidden_units=attention_hidden_units, attention_activation=attention_activation, use_attention_softmax=use_attention_softmax, attention_dropout=attention_dropout))
        feature_dim = feature_map.sum_emb_out_dim() + self.item_info_dim * 3
        self.enable_sum_pooling = enable_sum_pooling
        if not self.enable_sum_pooling:
            feature_dim -= self.item_info_dim * 2
        self.dnn = MLP_Block(input_dim=feature_dim, output_dim=1, hidden_units=dnn_hidden_units, hidden_activations=dnn_activations, output_activation=self.output_activation, dropout_rates=net_dropout, batch_norm=batch_norm)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        batch_dict, item_dict, pad_mask = self.get_inputs(inputs)
        concat_emb = []
        if batch_dict:
            feature_emb = self.embedding_layer(batch_dict, flatten_emb=True)
            concat_emb.append(feature_emb)
        item_feat_emb = self.embedding_layer(item_dict, flatten_emb=True)
        batch_size = pad_mask.shape[0]
        item_feat_emb = item_feat_emb.view(batch_size, -1, self.item_info_dim)
        target_emb = item_feat_emb[:, -1, :]
        sequence_emb = item_feat_emb[:, 0:-1, :]
        non_zero_mask = pad_mask.sum(dim=1) > 0
        packed_interests, interest_emb = self.interest_extraction(0, sequence_emb[non_zero_mask], pad_mask[non_zero_mask])
        h_out = self.interest_evolution(0, packed_interests, interest_emb, target_emb[non_zero_mask], pad_mask[non_zero_mask])
        final_out = self.get_unmasked_tensor(h_out, non_zero_mask)
        concat_emb += [target_emb, final_out]
        if self.enable_sum_pooling:
            sum_pool_emb = self.sum_pooling(sequence_emb)
            concat_emb += [sum_pool_emb, target_emb * sum_pool_emb]
        y_pred = self.dnn(torch.cat(concat_emb, dim=-1))
        return_dict = {'y_pred': y_pred}
        return return_dict

    def get_unmasked_tensor(self, h, non_zero_mask):
        out = torch.zeros([non_zero_mask.size(0)] + list(h.shape[1:]), device=h.device)
        out[non_zero_mask] = h
        return out

    def interest_extraction(self, idx, sequence_emb, mask):
        seq_lens = mask.sum(dim=1).cpu()
        packed_seq = pack_padded_sequence(sequence_emb, seq_lens, batch_first=True, enforce_sorted=False)
        packed_interests, _ = self.extraction_modules[idx](packed_seq)
        interest_emb, _ = pad_packed_sequence(packed_interests, batch_first=True, padding_value=0.0, total_length=mask.size(1))
        return (packed_interests, interest_emb)

    def interest_evolution(self, idx, packed_interests, interest_emb, target_emb, mask):
        if self.gru_type == 'GRU':
            _, h_out = self.evolving_modules[idx](packed_interests)
        else:
            attn_scores = self.attention_modules[idx](interest_emb, target_emb, mask)
            seq_lens = mask.sum(dim=1).cpu()
            if self.gru_type == 'AIGRU':
                packed_inputs = pack_padded_sequence(interest_emb * attn_scores, seq_lens, batch_first=True, enforce_sorted=False)
                _, h_out = self.evolving_modules[idx](packed_inputs)
            else:
                packed_scores = pack_padded_sequence(attn_scores, seq_lens, batch_first=True, enforce_sorted=False)
                _, h_out = self.evolving_modules[idx](packed_interests, packed_scores)
        return h_out.squeeze()

    def get_inputs(self, inputs, feature_source=None):
        batch_dict, item_dict, mask = inputs
        X_dict = dict()
        for feature, value in batch_dict.items():
            if feature in self.feature_map.labels:
                continue
            feature_spec = self.feature_map.features[feature]
            if feature_spec['type'] == 'meta':
                continue
            if feature_source and not_in_whitelist(feature_spec['source'], feature_source):
                continue
            X_dict[feature] = value.to(self.device)
        for item, value in item_dict.items():
            item_dict[item] = value.to(self.device)
        return (X_dict, item_dict, mask.to(self.device))

    def get_labels(self, inputs):
        """ Please override get_labels() when using multiple labels!
        """
        labels = self.feature_map.labels
        batch_dict = inputs[0]
        y = batch_dict[labels[0]].to(self.device)
        return y.float().view(-1, 1)

    def get_group_id(self, inputs):
        return inputs[0][self.feature_map.group_id]

    def train_step(self, batch_data):
        return_dict = self.forward(batch_data)
        y_true = self.get_labels(batch_data)
        loss = self.compute_loss(return_dict, y_true)
        loss = loss / self.accumulation_steps
        loss.backward()
        if (self._batch_index + 1) % self.accumulation_steps == 0:
            nn.utils.clip_grad_norm_(self.parameters(), self._max_gradient_norm)
            self.optimizer.step()
            self.optimizer.zero_grad()
        return loss

def get_unmasked_tensor(self, h, non_zero_mask):
    out = torch.zeros([non_zero_mask.size(0)] + list(h.shape[1:]), device=h.device)
    out[non_zero_mask] = h
    return out

def get_inputs(self, inputs, feature_source=None):
    batch_dict, item_dict, mask = inputs
    X_dict = dict()
    for feature, value in batch_dict.items():
        if feature in self.feature_map.labels:
            continue
        feature_spec = self.feature_map.features[feature]
        if feature_spec['type'] == 'meta':
            continue
        if feature_source and not_in_whitelist(feature_spec['source'], feature_source):
            continue
        X_dict[feature] = value.to(self.device)
    for item, value in item_dict.items():
        item_dict[item] = value.to(self.device)
    return (X_dict, item_dict, mask.to(self.device))

class APG_Linear(nn.Module):

    def __init__(self, input_dim, output_dim, condition_dim, bias=True, rank_k=None, overparam_p=None, generate_bias=False, hypernet_config={}):
        super(APG_Linear, self).__init__()
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.generate_bias = generate_bias
        self.rank_k = rank_k
        self.use_low_rank = rank_k is not None
        self.use_over_param = overparam_p is not None
        self.use_bias = bias
        if self.use_low_rank:
            assert rank_k <= min(input_dim, output_dim), 'Invalid rank_k={}'.format(rank_k)
            if self.use_over_param:
                assert overparam_p >= rank_k, 'Invalid overparam_p={}'.format(overparam_p)
                self.U_l = nn.Parameter(nn.init.xavier_normal_(torch.empty(input_dim, overparam_p)))
                self.U_r = nn.Parameter(nn.init.xavier_normal_(torch.empty(overparam_p, rank_k)))
                self.V_l = nn.Parameter(nn.init.xavier_normal_(torch.empty(rank_k, overparam_p)))
                self.V_r = nn.Parameter(nn.init.xavier_normal_(torch.empty(overparam_p, output_dim)))
            else:
                self.U = nn.Parameter(nn.init.xavier_normal_(torch.empty(input_dim, rank_k)))
                self.V = nn.Parameter(nn.init.xavier_normal_(torch.empty(rank_k, output_dim)))
            self.hypernet = MLP_Block(input_dim=condition_dim, output_dim=rank_k ** 2 + int(generate_bias) * output_dim, hidden_units=hypernet_config.get('hidden_units', []), hidden_activations=hypernet_config.get('hidden_activations', 'ReLU'), output_activation=None, dropout_rates=hypernet_config.get('dropout_rates', 0), batch_norm=False)
        else:
            self.hypernet = MLP_Block(input_dim=condition_dim, output_dim=input_dim * output_dim + int(generate_bias) * output_dim, hidden_units=hypernet_config.get('hidden_units', []), hidden_activations=hypernet_config.get('hidden_activations', 'ReLU'), output_activation=None, dropout_rates=hypernet_config.get('dropout_rates', 0), batch_norm=False)
        if self.use_bias and (not self.generate_bias):
            self.bias = nn.Parameter(torch.zeros(1, output_dim))
        else:
            self.bias = None

    def generate_weight(self, condition_z):
        weight_S = self.hypernet(condition_z)
        bias = self.bias
        if self.generate_bias:
            if self.use_bias:
                bias = weight_S[:, 0:self.output_dim]
            weight_S = weight_S[:, self.output_dim:]
        if self.use_low_rank:
            weight_S = weight_S.reshape(-1, self.rank_k, self.rank_k)
        else:
            weight_S = weight_S.reshape(-1, self.input_dim, self.output_dim)
        return (weight_S, bias)

    def forward(self, input_h, condition_z):
        weight_S, bias = self.generate_weight(condition_z)
        if self.use_low_rank:
            if self.use_over_param:
                self.U = torch.matmul(self.U_l, self.U_r)
                self.V = torch.matmul(self.V_l, self.V_r)
            h = torch.matmul(input_h, self.U)
            h = torch.bmm(h.unsqueeze(1), weight_S).squeeze(1)
            out = torch.matmul(h, self.V)
        else:
            out = torch.bmm(input_h.unsqueeze(1), weight_S).squeeze(1)
        if bias is not None:
            out += bias
        return out

def generate_weight(self, condition_z):
    weight_S = self.hypernet(condition_z)
    bias = self.bias
    if self.generate_bias:
        if self.use_bias:
            bias = weight_S[:, 0:self.output_dim]
        weight_S = weight_S[:, self.output_dim:]
    if self.use_low_rank:
        weight_S = weight_S.reshape(-1, self.rank_k, self.rank_k)
    else:
        weight_S = weight_S.reshape(-1, self.input_dim, self.output_dim)
    return (weight_S, bias)

class DIEN(BaseModel):
    """ Implementation of DIEN model based on the following reference code:
        https://github.com/mouna99/dien
    """

    def __init__(self, feature_map, model_id='DIEN', gpu=-1, dnn_hidden_units=[200, 80], dnn_activations='ReLU', learning_rate=0.001, embedding_dim=16, net_dropout=0, batch_norm=True, dien_target_field=[('item_id', 'cate_id')], dien_sequence_field=[('click_history', 'cate_history')], dien_neg_seq_field=[('neg_click_history', 'neg_cate_history')], gru_type='AUGRU', enable_sum_pooling=False, attention_dropout=0, attention_type='bilinear_attention', attention_hidden_units=[80, 40], attention_activation='Dice', use_attention_softmax=True, aux_hidden_units=[100, 50], aux_activation='ReLU', aux_loss_alpha=0, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(DIEN, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        if not isinstance(dien_target_field, list):
            dien_target_field = [dien_target_field]
        self.dien_target_field = dien_target_field
        if not isinstance(dien_sequence_field, list):
            dien_sequence_field = [dien_sequence_field]
        self.dien_sequence_field = dien_sequence_field
        assert len(self.dien_target_field) == len(self.dien_sequence_field), 'dien_sequence_field or dien_target_field not supported.'
        self.aux_loss_alpha = aux_loss_alpha
        if not isinstance(dien_neg_seq_field, list):
            dien_neg_seq_field = [dien_neg_seq_field]
        self.dien_neg_seq_field = dien_neg_seq_field
        self.feature_map = feature_map
        self.embedding_dim = embedding_dim
        self.embedding_layer = FeatureEmbeddingDict(feature_map, embedding_dim)
        self.sum_pooling = MaskedSumPooling()
        self.gru_type = gru_type
        self.extraction_modules = nn.ModuleList()
        self.evolving_modules = nn.ModuleList()
        self.attention_modules = nn.ModuleList()
        feature_dim = 0
        for target_field in self.dien_target_field:
            model_dim = embedding_dim * len(list(flatten([target_field])))
            feature_dim += model_dim * 2
            self.extraction_modules.append(nn.GRU(input_size=model_dim, hidden_size=model_dim, batch_first=True))
            if gru_type in ['AGRU', 'AUGRU']:
                self.evolving_modules.append(DynamicGRU(model_dim, model_dim, gru_type=gru_type))
            else:
                self.evolving_modules.append(nn.GRU(input_size=model_dim, hidden_size=model_dim, batch_first=True))
            if gru_type in ['AIGRU', 'AGRU', 'AUGRU']:
                self.attention_modules.append(AttentionLayer(model_dim, attention_type=attention_type, attention_hidden_units=attention_hidden_units, attention_activation=attention_activation, use_attention_softmax=use_attention_softmax, attention_dropout=attention_dropout))
        feature_dim = feature_dim + feature_map.sum_emb_out_dim() - embedding_dim * len(list(flatten([self.dien_neg_seq_field])))
        self.enable_sum_pooling = enable_sum_pooling
        if not self.enable_sum_pooling:
            feature_dim -= embedding_dim * len(list(flatten([self.dien_target_field]))) * 2
        self.dnn = MLP_Block(input_dim=feature_dim, output_dim=1, hidden_units=dnn_hidden_units, hidden_activations=dnn_activations, output_activation=self.output_activation, dropout_rates=net_dropout, batch_norm=batch_norm)
        if self.aux_loss_alpha > 0:
            self.model_dim = model_dim
            self.aux_net = MLP_Block(input_dim=model_dim * 2, output_dim=1, hidden_units=aux_hidden_units, hidden_activations=aux_activation, output_activation='Sigmoid', dropout_rates=net_dropout)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        X = self.get_inputs(inputs)
        feature_emb_dict = self.embedding_layer(X)
        concat_emb = []
        for idx, (target_field, sequence_field) in enumerate(zip(self.dien_target_field, self.dien_sequence_field)):
            target_emb = self.get_embedding(target_field, feature_emb_dict)
            sequence_emb = self.get_embedding(sequence_field, feature_emb_dict)
            neg_emb = self.get_embedding(self.dien_neg_seq_field[idx], feature_emb_dict) if self.aux_loss_alpha > 0 else None
            seq_field = list(flatten([sequence_field]))[0]
            pad_mask = X[seq_field].long() > 0
            non_zero_mask = pad_mask.sum(dim=1) > 0
            packed_interests, interest_emb = self.interest_extraction(idx, sequence_emb[non_zero_mask], pad_mask[non_zero_mask])
            h_out = self.interest_evolution(idx, packed_interests, interest_emb, target_emb[non_zero_mask], pad_mask[non_zero_mask])
            final_out = self.get_unmasked_tensor(h_out, non_zero_mask)
            concat_emb.append(final_out)
            if self.enable_sum_pooling:
                sum_pool_emb = self.sum_pooling(sequence_emb)
                concat_emb += [sum_pool_emb, target_emb * sum_pool_emb]
        for feature, emb in feature_emb_dict.items():
            if emb.ndim == 2 and feature not in flatten([self.dien_neg_seq_field]):
                concat_emb.append(emb)
        y_pred = self.dnn(torch.cat(concat_emb, dim=-1))
        return_dict = {'y_pred': y_pred, 'interest_emb': self.get_unmasked_tensor(interest_emb, non_zero_mask), 'neg_emb': neg_emb, 'pad_mask': pad_mask, 'pos_emb': sequence_emb}
        return return_dict

    def get_unmasked_tensor(self, h, non_zero_mask):
        out = torch.zeros([non_zero_mask.size(0)] + list(h.shape[1:]), device=h.device)
        out[non_zero_mask] = h
        return out

    def add_loss(self, return_dict, y_true):
        loss = self.loss_fn(return_dict['y_pred'], y_true, reduction='mean')
        if self.aux_loss_alpha > 0:
            interest_emb, pos_emb, neg_emb, pad_mask = (return_dict['interest_emb'], return_dict['pos_emb'], return_dict['neg_emb'], return_dict['pad_mask'])
            pos_prob = self.aux_net(torch.cat([interest_emb[:, :-1, :], pos_emb[:, 1:, :]], dim=-1).view(-1, self.model_dim * 2))
            neg_prob = self.aux_net(torch.cat([interest_emb[:, :-1, :], neg_emb[:, 1:, :]], dim=-1).view(-1, self.model_dim * 2))
            aux_prob = torch.cat([pos_prob, neg_prob], dim=0).view(-1, 1)
            aux_label = torch.cat([torch.ones_like(pos_prob, device=aux_prob.device), torch.zeros_like(neg_prob, device=aux_prob.device)], dim=0).view(-1, 1)
            aux_loss = F.binary_cross_entropy(aux_prob, aux_label, reduction='none')
            pad_mask = pad_mask[:, 1:].view(-1, 1)
            aux_loss = torch.sum(aux_loss * pad_mask, dim=-1) / (torch.sum(pad_mask, dim=-1) + 1e-09)
            loss += self.aux_loss_alpha * aux_loss
        return loss

    def interest_extraction(self, idx, sequence_emb, mask):
        seq_lens = mask.sum(dim=1).cpu()
        packed_seq = pack_padded_sequence(sequence_emb, seq_lens, batch_first=True, enforce_sorted=False)
        packed_interests, _ = self.extraction_modules[idx](packed_seq)
        interest_emb, _ = pad_packed_sequence(packed_interests, batch_first=True, padding_value=0.0, total_length=mask.size(1))
        return (packed_interests, interest_emb)

    def interest_evolution(self, idx, packed_interests, interest_emb, target_emb, mask):
        if self.gru_type == 'GRU':
            _, h_out = self.evolving_modules[idx](packed_interests)
        else:
            attn_scores = self.attention_modules[idx](interest_emb, target_emb, mask)
            seq_lens = mask.sum(dim=1).cpu()
            if self.gru_type == 'AIGRU':
                packed_inputs = pack_padded_sequence(interest_emb * attn_scores, seq_lens, batch_first=True, enforce_sorted=False)
                _, h_out = self.evolving_modules[idx](packed_inputs)
            else:
                packed_scores = pack_padded_sequence(attn_scores, seq_lens, batch_first=True, enforce_sorted=False)
                _, h_out = self.evolving_modules[idx](packed_interests, packed_scores)
        return h_out.squeeze()

    def get_embedding(self, field, feature_emb_dict):
        if type(field) == tuple:
            emb_list = [feature_emb_dict[f] for f in field]
            return torch.cat(emb_list, dim=-1)
        else:
            return feature_emb_dict[field]

def get_unmasked_tensor(self, h, non_zero_mask):
    out = torch.zeros([non_zero_mask.size(0)] + list(h.shape[1:]), device=h.device)
    out[non_zero_mask] = h
    return out

class FGCNN(BaseModel):

    def __init__(self, feature_map, model_id='FGCNN', gpu=-1, learning_rate=0.001, embedding_dim=10, share_embedding=False, channels=[14, 16, 18, 20], kernel_heights=[7, 7, 7, 7], pooling_sizes=[2, 2, 2, 2], recombined_channels=[2, 2, 2, 2], conv_activation='Tanh', conv_batch_norm=True, dnn_hidden_units=[4096, 2048, 1024, 512], dnn_activations='ReLU', dnn_batch_norm=False, embedding_regularizer=None, net_regularizer=None, net_dropout=0, **kwargs):
        super(FGCNN, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.share_embedding = share_embedding
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        if not self.share_embedding:
            self.fg_embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        num_fields = feature_map.num_fields
        channels, kernel_heights, pooling_sizes, recombined_channels = self.validate_input(channels, kernel_heights, pooling_sizes, recombined_channels)
        self.fgcnn_layer = FGCNN_Layer(num_fields, embedding_dim, channels=channels, kernel_heights=kernel_heights, pooling_sizes=pooling_sizes, recombined_channels=recombined_channels, activation=conv_activation, batch_norm=conv_batch_norm)
        input_dim, total_features = self.compute_input_dim(embedding_dim, num_fields, channels, pooling_sizes, recombined_channels)
        self.inner_product_layer = InnerProductInteraction(total_features, output='inner_product')
        self.dnn = MLP_Block(input_dim=input_dim, output_dim=1, hidden_units=dnn_hidden_units, hidden_activations=dnn_activations, output_activation=self.output_activation, dropout_rates=net_dropout, batch_norm=dnn_batch_norm)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def compute_input_dim(self, embedding_dim, num_fields, channels, pooling_sizes, recombined_channels):
        total_features = num_fields
        input_height = num_fields
        for i in range(len(channels)):
            input_height = int(np.ceil(input_height / pooling_sizes[i]))
            total_features += input_height * recombined_channels[i]
        input_dim = int(total_features * (total_features - 1) / 2) + total_features * embedding_dim
        return (input_dim, total_features)

    def validate_input(self, channels, kernel_heights, pooling_sizes, recombined_channels):
        if not isinstance(kernel_heights, list):
            kernel_heights = [kernel_heights] * len(channels)
        if not isinstance(pooling_sizes, list):
            pooling_sizes = [pooling_sizes] * len(channels)
        if not isinstance(recombined_channels, list):
            recombined_channels = [recombined_channels] * len(channels)
        if not len(channels) == len(kernel_heights) == len(pooling_sizes) == len(recombined_channels):
            raise ValueError('channels, kernel_heights, pooling_sizes, and recombined_channels                               should have the same length.')
        return (channels, kernel_heights, pooling_sizes, recombined_channels)

    def forward(self, inputs):
        """
        Inputs: [X, y]
        """
        X = self.get_inputs(inputs)
        feature_emb = self.embedding_layer(X)
        if not self.share_embedding:
            feature_emb2 = self.fg_embedding_layer(X)
        else:
            feature_emb2 = feature_emb
        conv_in = torch.unsqueeze(feature_emb2, 1)
        new_feature_emb = self.fgcnn_layer(conv_in)
        combined_feature_emb = torch.cat([feature_emb, new_feature_emb], dim=1)
        inner_product_vec = self.inner_product_layer(combined_feature_emb)
        dense_input = torch.cat([combined_feature_emb.flatten(start_dim=1), inner_product_vec], dim=1)
        y_pred = self.dnn(dense_input)
        return_dict = {'y_pred': y_pred}
        return return_dict

def compute_input_dim(self, embedding_dim, num_fields, channels, pooling_sizes, recombined_channels):
    total_features = num_fields
    input_height = num_fields
    for i in range(len(channels)):
        input_height = int(np.ceil(input_height / pooling_sizes[i]))
        total_features += input_height * recombined_channels[i]
    input_dim = int(total_features * (total_features - 1) / 2) + total_features * embedding_dim
    return (input_dim, total_features)

def load_config(config_dir, experiment_id):
    params = load_model_config(config_dir, experiment_id)
    data_params = load_dataset_config(config_dir, params['dataset_id'])
    params.update(data_params)
    return params

def load_model_config(config_dir, experiment_id):
    model_configs = glob.glob(os.path.join(config_dir, 'model_config.yaml'))
    if not model_configs:
        model_configs = glob.glob(os.path.join(config_dir, 'model_config/*.yaml'))
    if not model_configs:
        raise RuntimeError('config_dir={} is not valid!'.format(config_dir))
    found_params = dict()
    for config in model_configs:
        with open(config, 'r') as cfg:
            config_dict = yaml.load(cfg, Loader=yaml.FullLoader)
            if 'Base' in config_dict:
                found_params['Base'] = config_dict['Base']
            if experiment_id in config_dict:
                found_params[experiment_id] = config_dict[experiment_id]
        if len(found_params) == 2:
            break
    params = found_params.get('Base', {})
    params.update(found_params.get(experiment_id, {}))
    assert 'dataset_id' in params, f'expid={experiment_id} is not valid in config.'
    params['model_id'] = experiment_id
    return params

def load_dataset_config(config_dir, dataset_id):
    params = {'dataset_id': dataset_id}
    dataset_configs = glob.glob(os.path.join(config_dir, 'dataset_config.yaml'))
    if not dataset_configs:
        dataset_configs = glob.glob(os.path.join(config_dir, 'dataset_config/*.yaml'))
    for config in dataset_configs:
        with open(config, 'r') as cfg:
            config_dict = yaml.load(cfg, Loader=yaml.FullLoader)
            if dataset_id in config_dict:
                params.update(config_dict[dataset_id])
                return params
    raise RuntimeError(f'dataset_id={dataset_id} is not found in config.')

def set_logger(params):
    dataset_id = params['dataset_id']
    model_id = params.get('model_id', '')
    log_dir = os.path.join(params.get('model_root', './checkpoints'), dataset_id)
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, model_id + '.log')
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s P%(process)d %(levelname)s %(message)s', handlers=[logging.FileHandler(log_file, mode='w'), logging.StreamHandler()])
    logging.info('FuxiCTR version: ' + fuxictr.__version__)

def print_to_json(data, sort_keys=True):
    new_data = dict(((k, str(v)) for k, v in data.items()))
    if sort_keys:
        new_data = OrderedDict(sorted(new_data.items(), key=lambda x: x[0]))
    return json.dumps(new_data, indent=4)

def print_to_list(data):
    return ' - '.join(('{}: {:.6f}'.format(k, v) for k, v in data.items()))

class Monitor(object):

    def __init__(self, kv):
        if isinstance(kv, str):
            kv = {kv: 1}
        self.kv_pairs = kv

    def get_value(self, logs):
        value = 0
        for k, v in self.kv_pairs.items():
            value += logs.get(k, 0) * v
        return value

    def get_metrics(self):
        return list(self.kv_pairs.keys())

def get_metrics(self):
    return list(self.kv_pairs.keys())

class FeatureMap(object):

    def __init__(self, dataset_id, data_dir):
        self.data_dir = data_dir
        self.dataset_id = dataset_id
        self.num_fields = 0
        self.total_features = 0
        self.input_length = 0
        self.features = OrderedDict()
        self.labels = []
        self.column_index = dict()
        self.group_id = None
        self.default_emb_dim = None

    def load(self, json_file, params):
        logging.info('Load feature_map from json: ' + json_file)
        with io.open(json_file, 'r', encoding='utf-8') as fd:
            feature_map = json.load(fd)
        if feature_map['dataset_id'] != self.dataset_id:
            raise RuntimeError('dataset_id={} does not match feature_map!'.format(self.dataset_id))
        self.labels = feature_map.get('labels', [])
        self.total_features = feature_map.get('total_features', 0)
        self.input_length = feature_map.get('input_length', 0)
        self.group_id = params.get('group_id', None)
        self.default_emb_dim = params.get('embedding_dim', None)
        self.features = OrderedDict(((k, v) for x in feature_map['features'] for k, v in x.items()))
        self.num_fields = self.get_num_fields()
        if params.get('use_features', None):
            self.features = OrderedDict(((x, self.features[x]) for x in params['use_features']))
        if params.get('feature_specs', None):
            self.update_feature_specs(params['feature_specs'])
        self.set_column_index()

    def update_feature_specs(self, feature_specs):
        for col in feature_specs:
            namelist = col['name']
            if type(namelist) != list:
                namelist = [namelist]
            for name in namelist:
                for k, v in col.items():
                    if k != 'name':
                        self.features[name][k] = v

    def save(self, json_file):
        logging.info('Save feature_map to json: ' + json_file)
        os.makedirs(os.path.dirname(json_file), exist_ok=True)
        feature_map = OrderedDict()
        feature_map['dataset_id'] = self.dataset_id
        feature_map['num_fields'] = self.num_fields
        feature_map['total_features'] = self.total_features
        feature_map['input_length'] = self.input_length
        feature_map['labels'] = self.labels
        feature_map['features'] = [{k: v} for k, v in self.features.items()]
        with open(json_file, 'w') as fd:
            json.dump(feature_map, fd, indent=4)

    def get_num_fields(self, feature_source=[]):
        if type(feature_source) != list:
            feature_source = [feature_source]
        num_fields = 0
        for feature, feature_spec in self.features.items():
            if feature_spec['type'] == 'meta':
                continue
            if len(feature_source) == 0 or feature_spec.get('source') in feature_source:
                num_fields += 1
        return num_fields

    def sum_emb_out_dim(self, feature_source=[]):
        if type(feature_source) != list:
            feature_source = [feature_source]
        total_dim = 0
        for feature, feature_spec in self.features.items():
            if feature_spec['type'] == 'meta':
                continue
            if len(feature_source) == 0 or feature_spec.get('source') in feature_source:
                total_dim += feature_spec.get('emb_output_dim', feature_spec.get('embedding_dim', self.default_emb_dim))
        return total_dim

    def set_column_index(self):
        logging.info('Set column index...')
        idx = 0
        for feature, feature_spec in self.features.items():
            if feature_spec['type'] == 'sequence':
                col_indexes = [i + idx for i in range(feature_spec['max_len'])]
                self.column_index[feature] = col_indexes
                idx += feature_spec['max_len']
            elif feature_spec['type'] == 'embedding':
                emb_dim = feature_spec['pretrain_dim']
                col_indexes = [i + idx for i in range(emb_dim)]
                self.column_index[feature] = col_indexes
                idx += emb_dim
            else:
                self.column_index[feature] = idx
                idx += 1
        self.input_length = idx
        for label in self.labels:
            self.column_index[label] = idx
            idx += 1

    def get_column_index(self, feature):
        if feature not in self.column_index:
            self.set_column_index()
        return self.column_index[feature]

def __init__(self, dataset_id, data_dir):
    self.data_dir = data_dir
    self.dataset_id = dataset_id
    self.num_fields = 0
    self.total_features = 0
    self.input_length = 0
    self.features = OrderedDict()
    self.labels = []
    self.column_index = dict()
    self.group_id = None
    self.default_emb_dim = None

def load(self, json_file, params):
    logging.info('Load feature_map from json: ' + json_file)
    with io.open(json_file, 'r', encoding='utf-8') as fd:
        feature_map = json.load(fd)
    if feature_map['dataset_id'] != self.dataset_id:
        raise RuntimeError('dataset_id={} does not match feature_map!'.format(self.dataset_id))
    self.labels = feature_map.get('labels', [])
    self.total_features = feature_map.get('total_features', 0)
    self.input_length = feature_map.get('input_length', 0)
    self.group_id = params.get('group_id', None)
    self.default_emb_dim = params.get('embedding_dim', None)
    self.features = OrderedDict(((k, v) for x in feature_map['features'] for k, v in x.items()))
    self.num_fields = self.get_num_fields()
    if params.get('use_features', None):
        self.features = OrderedDict(((x, self.features[x]) for x in params['use_features']))
    if params.get('feature_specs', None):
        self.update_feature_specs(params['feature_specs'])
    self.set_column_index()

def save(self, json_file):
    logging.info('Save feature_map to json: ' + json_file)
    os.makedirs(os.path.dirname(json_file), exist_ok=True)
    feature_map = OrderedDict()
    feature_map['dataset_id'] = self.dataset_id
    feature_map['num_fields'] = self.num_fields
    feature_map['total_features'] = self.total_features
    feature_map['input_length'] = self.input_length
    feature_map['labels'] = self.labels
    feature_map['features'] = [{k: v} for k, v in self.features.items()]
    with open(json_file, 'w') as fd:
        json.dump(feature_map, fd, indent=4)

def get_column_index(self, feature):
    if feature not in self.column_index:
        self.set_column_index()
    return self.column_index[feature]

def avgAUC(y_true, y_pred):
    """ avgAUC used in MIND news recommendation """
    if np.sum(y_true) > 0 and np.sum(y_true) < len(y_true):
        auc = roc_auc_score(y_true, y_pred)
        return (auc, 1)
    else:
        return (0, 0)

def gAUC(y_true, y_pred):
    """ gAUC defined in DIN paper """
    if np.sum(y_true) > 0 and np.sum(y_true) < len(y_true):
        auc = roc_auc_score(y_true, y_pred)
        n_samples = len(y_true)
        return (auc * n_samples, n_samples)
    else:
        return (0, 0)

def enumerate_params(config_file, exclude_expid=[]):
    with open(config_file, 'r') as cfg:
        config_dict = yaml.load(cfg, Loader=yaml.FullLoader)
    tune_dict = config_dict['tuner_space']
    for k, v in tune_dict.items():
        if not isinstance(v, list):
            tune_dict[k] = [v]
    experiment_id = config_dict['base_expid']
    if 'model_config' in config_dict:
        model_dict = config_dict['model_config'][experiment_id]
    else:
        base_config_dir = config_dict.get('base_config', os.path.dirname(config_file))
        model_dict = load_model_config(base_config_dir, experiment_id)
    dataset_id = config_dict.get('dataset_id', model_dict['dataset_id'])
    if 'dataset_config' in config_dict:
        dataset_dict = config_dict['dataset_config'][dataset_id]
    else:
        dataset_dict = load_dataset_config(base_config_dir, dataset_id)
    if model_dict['dataset_id'] == 'TBD':
        model_dict['dataset_id'] = dataset_id
        experiment_id = model_dict['model'] + '_' + dataset_id
    tuner_keys = set(tune_dict.keys())
    base_keys = set(model_dict.keys()).union(set(dataset_dict.keys()))
    if len(tuner_keys - base_keys) > 0:
        raise RuntimeError('Invalid params in tuner config: {}'.format(tuner_keys - base_keys))
    config_dir = config_file.replace('.yaml', '')
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    dataset_dict = {k: tune_dict[k] if k in tune_dict else [v] for k, v in dataset_dict.items()}
    dataset_para_keys = list(dataset_dict.keys())
    dataset_para_combs = dict()
    for idx, values in enumerate(itertools.product(*map(dataset_dict.get, dataset_para_keys))):
        dataset_params = dict(zip(dataset_para_keys, values))
        if dataset_params['data_format'] == 'npz' or (dataset_params['data_format'] == 'parquet' and dataset_params.get('rebuild_dataset') == False):
            dataset_para_combs[dataset_id] = dataset_params
        else:
            hash_id = hashlib.md5(''.join(sorted(print_to_json(dataset_params))).encode('utf-8')).hexdigest()[0:8]
            dataset_para_combs[dataset_id + '_{}'.format(hash_id)] = dataset_params
    dataset_config = os.path.join(config_dir, 'dataset_config.yaml')
    with open(dataset_config, 'w') as fw:
        yaml.dump(dataset_para_combs, fw, default_flow_style=None, indent=4)
    model_dict = {k: tune_dict[k] if k in tune_dict else [v] for k, v in model_dict.items()}
    model_para_keys = list(model_dict.keys())
    model_param_combs = dict()
    for idx, values in enumerate(itertools.product(*map(model_dict.get, model_para_keys))):
        model_param_combs[idx + 1] = dict(zip(model_para_keys, values))
    merged_param_combs = dict()
    for idx, item in enumerate(itertools.product(model_param_combs.values(), dataset_para_combs.keys())):
        para_dict = item[0]
        para_dict['dataset_id'] = item[1]
        del para_dict['model_id']
        random_str = ''
        if para_dict['debug_mode']:
            random_str = '{:06d}'.format(np.random.randint(1000000.0))
        hash_id = hashlib.md5((''.join(sorted(print_to_json(para_dict))) + random_str).encode('utf-8')).hexdigest()[0:8]
        hash_expid = experiment_id + '_{:03d}_{}'.format(idx + 1, hash_id)
        if hash_expid not in exclude_expid:
            merged_param_combs[hash_expid] = para_dict.copy()
    model_config = os.path.join(config_dir, 'model_config.yaml')
    with open(model_config, 'w') as fw:
        yaml.dump(merged_param_combs, fw, default_flow_style=None, indent=4)
    print('Enumerate all tuner configurations done.')
    return config_dir

def load_experiment_ids(config_dir):
    model_configs = glob.glob(os.path.join(config_dir, 'model_config.yaml'))
    if not model_configs:
        model_configs = glob.glob(os.path.join(config_dir, 'model_config/*.yaml'))
    experiment_id_list = []
    for config in model_configs:
        with open(config, 'r') as cfg:
            config_dict = yaml.load(cfg, Loader=yaml.FullLoader)
            experiment_id_list += config_dict.keys()
    return sorted(experiment_id_list)

def grid_search(config_dir, gpu_list, expid_tag=None, script='run_expid.py'):
    experiment_id_list = load_experiment_ids(config_dir)
    if expid_tag is not None:
        experiment_id_list = [expid for expid in experiment_id_list if str(expid_tag) in expid]
        assert len(experiment_id_list) > 0, 'tag={} does not match any expid.'
    gpu_list = list(gpu_list)
    idle_queue = list(range(len(gpu_list)))
    processes = dict()
    while len(experiment_id_list) > 0:
        if len(idle_queue) > 0:
            idle_idx = idle_queue.pop(0)
            gpu_id = gpu_list[idle_idx]
            expid = experiment_id_list.pop(0)
            cmd = 'python -u {} --config {} --expid {} --gpu {}'.format(script, config_dir, expid, gpu_id)
            p = subprocess.Popen(cmd.split())
            processes[idle_idx] = p
        else:
            time.sleep(3)
            for idle_idx, p in processes.items():
                if p.poll() is not None:
                    idle_queue.append(idle_idx)
    [p.wait() for p in processes.values()]

class Tokenizer(object):

    def __init__(self, max_features=None, na_value='', min_freq=1, splitter=None, remap=True, lower=False, max_len=0, padding='pre'):
        self._max_features = max_features
        self._na_value = na_value
        self._min_freq = min_freq
        self._lower = lower
        self._splitter = splitter
        self.vocab = dict()
        self.max_len = max_len
        self.padding = padding
        self.remap = remap

    def fit_on_texts(self, series):
        max_len = 0
        word_counts = Counter()
        with ProcessPoolExecutor(max_workers=mp.cpu_count() // 2) as executor:
            chunk_size = 1000000
            tasks = []
            for idx in range(0, len(series), chunk_size):
                data_chunk = series.iloc[idx:idx + chunk_size]
                tasks.append(executor.submit(count_tokens, data_chunk, self._splitter))
            for future in tqdm(as_completed(tasks), total=len(tasks)):
                chunk_word_counts, chunk_max_len = future.result()
                word_counts.update(chunk_word_counts)
                max_len = max(max_len, chunk_max_len)
        if self.max_len == 0:
            self.max_len = max_len
        self.build_vocab(word_counts)

    def build_vocab(self, word_counts):
        word_counts = word_counts.most_common()
        if self._max_features:
            word_counts = word_counts[0:self._max_features]
        words = []
        for token, count in word_counts:
            if count >= self._min_freq:
                if token != self._na_value:
                    words.append(token.lower() if self._lower else token)
            else:
                break
        if self.remap:
            self.vocab = dict(((token, idx) for idx, token in enumerate(words, 1)))
        else:
            self.vocab = dict(((token, int(token)) for token in words))
        self.vocab['__PAD__'] = 0
        self.vocab['__OOV__'] = self.vocab_size()

    def merge_vocab(self, shared_tokenizer):
        if self.remap:
            new_words = 0
            for word in self.vocab.keys():
                if word not in shared_tokenizer.vocab:
                    shared_tokenizer.vocab[word] = shared_tokenizer.vocab['__OOV__'] + new_words
                    new_words += 1
        else:
            shared_tokenizer.vocab.update(self.vocab)
        vocab_size = shared_tokenizer.vocab_size()
        if shared_tokenizer.vocab['__OOV__'] != vocab_size - 1 or shared_tokenizer.vocab['__OOV__'] != len(shared_tokenizer.vocab) - 1:
            shared_tokenizer.vocab['__OOV__'] = vocab_size
        self.vocab = shared_tokenizer.vocab
        return shared_tokenizer

    def vocab_size(self):
        return max(self.vocab.values()) + 1

    def update_vocab(self, word_list):
        new_words = 0
        for word in word_list:
            if word not in self.vocab:
                self.vocab[word] = self.vocab.get('__OOV__', 0) + new_words
                new_words += 1
        if new_words > 0:
            self.vocab['__OOV__'] = self.vocab_size()

    def encode_meta(self, series):
        word_counts = dict(series.value_counts())
        if len(self.vocab) == 0:
            self.build_vocab(word_counts)
        else:
            self.update_vocab(word_counts.keys())
        series = series.map(lambda x: self.vocab.get(x, self.vocab['__OOV__']))
        return series.values

    def encode_category(self, series):
        series = series.map(lambda x: self.vocab.get(x, self.vocab['__OOV__']))
        return series.values

    def encode_sequence(self, series):
        series = series.map(lambda text: [self.vocab.get(x, self.vocab['__OOV__']) if x != self._na_value else self.vocab['__PAD__'] for x in text.split(self._splitter)])
        seqs = pad_sequences(series.to_list(), maxlen=self.max_len, value=self.vocab['__PAD__'], padding=self.padding, truncating=self.padding)
        return seqs.tolist()

    def load_pretrained_vocab(self, feature_dtype, pretrain_path, expand_vocab=True):
        keys = load_pretrain_emb(pretrain_path, keys=['key'])
        keys = keys.astype(feature_dtype)
        if expand_vocab:
            vocab_size = self.vocab_size()
            for word in keys:
                if word not in self.vocab:
                    self.vocab[word] = vocab_size
                    vocab_size += 1

def __init__(self, max_features=None, na_value='', min_freq=1, splitter=None, remap=True, lower=False, max_len=0, padding='pre'):
    self._max_features = max_features
    self._na_value = na_value
    self._min_freq = min_freq
    self._lower = lower
    self._splitter = splitter
    self.vocab = dict()
    self.max_len = max_len
    self.padding = padding
    self.remap = remap

def merge_vocab(self, shared_tokenizer):
    if self.remap:
        new_words = 0
        for word in self.vocab.keys():
            if word not in shared_tokenizer.vocab:
                shared_tokenizer.vocab[word] = shared_tokenizer.vocab['__OOV__'] + new_words
                new_words += 1
    else:
        shared_tokenizer.vocab.update(self.vocab)
    vocab_size = shared_tokenizer.vocab_size()
    if shared_tokenizer.vocab['__OOV__'] != vocab_size - 1 or shared_tokenizer.vocab['__OOV__'] != len(shared_tokenizer.vocab) - 1:
        shared_tokenizer.vocab['__OOV__'] = vocab_size
    self.vocab = shared_tokenizer.vocab
    return shared_tokenizer

def load_pretrain_emb(pretrain_path, keys=['key', 'value']):
    if type(keys) != list:
        keys = [keys]
    if pretrain_path.endswith('h5'):
        with h5py.File(pretrain_path, 'r') as hf:
            values = [hf[k][:] for k in keys]
    elif pretrain_path.endswith('npz'):
        npz = np.load(pretrain_path)
        values = [npz[k] for k in keys]
    elif pretrain_path.endswith('parquet'):
        df = pd.read_parquet(pretrain_path)
        values = [df[k].values for k in keys]
    else:
        raise ValueError(f'Embedding format not supported: {pretrain_path}')
    return values[0] if len(values) == 1 else values

def split_train_test(train_ddf=None, valid_ddf=None, test_ddf=None, valid_size=0, test_size=0, split_type='sequential'):
    num_samples = len(train_ddf)
    train_size = num_samples
    instance_IDs = np.arange(num_samples)
    if split_type == 'random':
        np.random.shuffle(instance_IDs)
    if test_size > 0:
        if test_size < 1:
            test_size = int(num_samples * test_size)
        train_size = train_size - test_size
        test_ddf = train_ddf.loc[instance_IDs[train_size:], :].reset_index()
        instance_IDs = instance_IDs[0:train_size]
    if valid_size > 0:
        if valid_size < 1:
            valid_size = int(num_samples * valid_size)
        train_size = train_size - valid_size
        valid_ddf = train_ddf.loc[instance_IDs[train_size:], :].reset_index()
        instance_IDs = instance_IDs[0:train_size]
    if valid_size > 0 or test_size > 0:
        train_ddf = train_ddf.loc[instance_IDs, :].reset_index()
    return (train_ddf, valid_ddf, test_ddf)

def transform_block(feature_encoder, df_block, filename):
    df_block = feature_encoder.transform(df_block)
    data_path = os.path.join(feature_encoder.data_dir, filename)
    logging.info('Saving data to parquet: ' + data_path)
    os.makedirs(os.path.dirname(data_path), exist_ok=True)
    df_block.to_parquet(data_path, index=False, engine='pyarrow')

def build_dataset(feature_encoder, train_data=None, valid_data=None, test_data=None, valid_size=0, test_size=0, split_type='sequential', data_block_size=0, rebuild_dataset=True, **kwargs):
    """ Build feature_map and transform data """
    if rebuild_dataset:
        feature_map_path = os.path.join(feature_encoder.data_dir, 'feature_map.json')
        if os.path.exists(feature_map_path):
            logging.warn(f'Skip rebuilding {feature_map_path}. ' + 'Please delete it manually if rebuilding is required.')
        else:
            train_ddf = feature_encoder.read_data(train_data, **kwargs)
            valid_ddf = None
            test_ddf = None
            if valid_size > 0 or test_size > 0:
                valid_ddf = feature_encoder.read_data(valid_data, **kwargs)
                test_ddf = feature_encoder.read_data(test_data, **kwargs)
                train_ddf, valid_ddf, test_ddf = split_train_test(train_ddf, valid_ddf, test_ddf, valid_size, test_size, split_type)
            train_ddf = feature_encoder.preprocess(train_ddf)
            feature_encoder.fit(train_ddf, rebuild_dataset=True, **kwargs)
            transform(feature_encoder, train_ddf, 'train', block_size=data_block_size)
            del train_ddf
            gc.collect()
            if valid_ddf is None and valid_data is not None:
                valid_ddf = feature_encoder.read_data(valid_data, **kwargs)
            if valid_ddf is not None:
                valid_ddf = feature_encoder.preprocess(valid_ddf)
                transform(feature_encoder, valid_ddf, 'valid', block_size=data_block_size)
                del valid_ddf
                gc.collect()
            if test_ddf is None and test_data is not None:
                test_ddf = feature_encoder.read_data(test_data, **kwargs)
            if test_ddf is not None:
                test_ddf = feature_encoder.preprocess(test_ddf)
                transform(feature_encoder, test_ddf, 'test', block_size=data_block_size)
                del test_ddf
                gc.collect()
            logging.info('Transform csv data to parquet done.')
        train_data, valid_data, test_data = (os.path.join(feature_encoder.data_dir, 'train'), os.path.join(feature_encoder.data_dir, 'valid'), os.path.join(feature_encoder.data_dir, 'test') if test_data or test_size > 0 else None)
    else:
        feature_encoder.fit(train_ddf=None, rebuild_dataset=False, **kwargs)
    return (train_data, valid_data, test_data)

class Normalizer(object):

    def __init__(self, normalizer):
        if not callable(normalizer):
            self.callable = False
            if normalizer in ['StandardScaler', 'MinMaxScaler']:
                self.normalizer = getattr(sklearn_preprocess, normalizer)()
            else:
                raise NotImplementedError('normalizer={}'.format(normalizer))
        else:
            self.normalizer = normalizer
            self.callable = True

    def fit(self, X):
        if not self.callable:
            self.normalizer.fit(X.reshape(-1, 1))

    def transform(self, X):
        if self.callable:
            return self.normalizer(X)
        else:
            return self.normalizer.transform(X.reshape(-1, 1)).flatten()

def fit(self, X):
    if not self.callable:
        self.normalizer.fit(X.reshape(-1, 1))

def transform(self, X):
    if self.callable:
        return self.normalizer(X)
    else:
        return self.normalizer.transform(X.reshape(-1, 1)).flatten()

class FeatureProcessor(object):

    def __init__(self, feature_cols=[], label_col=[], dataset_id=None, data_root='../data/', **kwargs):
        logging.info('Set up feature processor...')
        self.data_dir = os.path.join(data_root, dataset_id)
        self.pickle_file = os.path.join(self.data_dir, 'feature_processor.pkl')
        self.json_file = os.path.join(self.data_dir, 'feature_map.json')
        self.vocab_file = os.path.join(self.data_dir, 'feature_vocab.json')
        self.feature_cols = self._complete_feature_cols(feature_cols)
        self.label_cols = label_col if type(label_col) == list else [label_col]
        self.feature_map = FeatureMap(dataset_id, self.data_dir)
        self.feature_map.labels = [col['name'] for col in self.label_cols]
        self.feature_map.group_id = kwargs.get('group_id', None)
        self.dtype_dict = dict(((feat['name'], eval(feat['dtype']) if type(feat['dtype']) == str else feat['dtype']) for feat in self.feature_cols + self.label_cols))
        self.processor_dict = dict()

    def _complete_feature_cols(self, feature_cols):
        full_feature_cols = []
        for col in feature_cols:
            name_or_namelist = col['name']
            if isinstance(name_or_namelist, list):
                for _name in name_or_namelist:
                    _col = col.copy()
                    _col['name'] = _name
                    full_feature_cols.append(_col)
            else:
                full_feature_cols.append(col)
        return full_feature_cols

    def read_data(self, data_path, data_format='csv', sep=',', n_rows=None, **kwargs):
        if not data_path.endswith(data_format):
            data_path = os.path.join(data_path, f'*.{data_format}')
        logging.info('Reading files: ' + data_path)
        file_names = sorted(glob.glob(data_path))
        assert len(file_names) > 0, f'Invalid data path: {data_path}'
        if data_format == 'csv':
            dfs = [pl.scan_csv(source=file_name, separator=sep, dtypes=self.dtype_dict, low_memory=False, n_rows=n_rows) for file_name in file_names]
            ddf = pl.concat(dfs)
        elif data_format == 'parquet':
            dfs = [pl.scan_parquet(source=file_name, low_memory=False, n_rows=n_rows) for file_name in file_names]
            ddf = pl.concat(dfs)
        else:
            NotImplementedError(f'data_format={data_format} not supported.')
        return ddf

    def preprocess(self, ddf):
        logging.info('Preprocess feature columns...')
        all_cols = self.label_cols + self.feature_cols[::-1]
        col_names = ddf.columns
        for col in all_cols:
            name = col['name']
            fill_na = None
            if col['dtype'] in ['str', str]:
                fill_na = col.get('fill_na', '')
            elif col['dtype'] in ['int', int]:
                fill_na = col.get('fill_na', 0)
            elif col['dtype'] in ['float', float]:
                fill_na = col.get('fill_na', 0.0)
            col_exist = name in col_names
            if fill_na is not None and col_exist:
                ddf = ddf.with_columns(pl.col(name).fill_null(fill_na))
            if col.get('preprocess'):
                preprocess_args = re.split('\\(|\\)', col['preprocess'])
                preprocess_fn = getattr(self, preprocess_args[0])
                if len(preprocess_args) == 1:
                    preprocess_args = [name]
                else:
                    preprocess_args = preprocess_args[1:-1]
                ddf = ddf.with_columns(preprocess_fn(*preprocess_args).alias(name).cast(self.dtype_dict[name]))
            if fill_na is not None and (not col_exist):
                ddf = ddf.with_columns(pl.col(name).fill_null(fill_na))
            if col.get('type') == 'sequence' and isinstance(ddf.select(name).dtypes[0], pl.List):
                ddf = ddf.with_columns(pl.col(name).apply(lambda x: '^'.join(map(str, x))))
        active_cols = [col['name'] for col in all_cols if col.get('active') != False]
        ddf = ddf.select(active_cols)
        return ddf

    def fit(self, train_ddf, min_categr_count=1, num_buckets=10, rebuild_dataset=True, **kwargs):
        logging.info('Fit feature processor...')
        self.rebuild_dataset = rebuild_dataset
        for col in self.feature_cols:
            name = col['name']
            if col['active']:
                logging.info('Processing column: {}'.format(col))
                col_series = train_ddf.select(name).collect().to_series().to_pandas() if self.rebuild_dataset else None
                if col['type'] == 'meta':
                    self.fit_meta_col(col)
                elif col['type'] == 'numeric':
                    self.fit_numeric_col(col, col_series)
                elif col['type'] == 'embedding':
                    self.fit_embedding_col(col)
                elif col['type'] == 'categorical':
                    self.fit_categorical_col(col, col_series, min_categr_count=min_categr_count, num_buckets=num_buckets)
                elif col['type'] == 'sequence':
                    self.fit_sequence_col(col, col_series, min_categr_count=min_categr_count)
                else:
                    raise NotImplementedError('feature type={}'.format(col['type']))
        os.makedirs(self.data_dir, exist_ok=True)
        for col in self.feature_cols:
            name = col['name']
            if 'pretrained_emb' in col:
                logging.info('Loading pretrained embedding: ' + name)
                if 'pretrain_dim' in col:
                    self.feature_map.features[name]['pretrain_dim'] = col['pretrain_dim']
                ext = Path(col['pretrained_emb']).suffix
                shutil.copy(col['pretrained_emb'], os.path.join(self.data_dir, 'pretrained_{}{}'.format(name, ext)))
                self.feature_map.features[name]['pretrained_emb'] = 'pretrained_{}{}'.format(name, ext)
                self.feature_map.features[name]['freeze_emb'] = col.get('freeze_emb', True)
                self.feature_map.features[name]['pretrain_usage'] = col.get('pretrain_usage', 'init')
                tokenizer = self.processor_dict[name + '::tokenizer']
                tokenizer.load_pretrained_vocab(self.dtype_dict[name], col['pretrained_emb'])
                self.processor_dict[name + '::tokenizer'] = tokenizer
                self.feature_map.features[name]['vocab_size'] = tokenizer.vocab_size()
        for name, spec in self.feature_map.features.items():
            if spec['type'] == 'numeric':
                self.feature_map.total_features += 1
            elif spec['type'] in ['categorical', 'sequence']:
                if 'share_embedding' in spec:
                    tokenizer = self.processor_dict[name + '::tokenizer']
                    tokenizer.vocab = self.processor_dict[spec['share_embedding'] + '::tokenizer'].vocab
                    self.processor_dict[name + '::tokenizer'] = tokenizer
                    self.feature_map.features[name].update({'oov_idx': tokenizer.vocab['__OOV__'], 'vocab_size': tokenizer.vocab_size()})
                else:
                    self.feature_map.total_features += self.feature_map.features[name]['vocab_size']
                if 'pretrained_emb' not in spec:
                    del self.feature_map.features[name]['oov_idx']
        self.feature_map.num_fields = self.feature_map.get_num_fields()
        self.feature_map.set_column_index()
        self.feature_map.save(self.json_file)
        self.save_pickle(self.pickle_file)
        self.save_vocab(self.vocab_file)
        logging.info('Set feature processor done.')

    def fit_meta_col(self, col):
        name = col['name']
        feature_type = col['type']
        self.feature_map.features[name] = {'type': feature_type}
        if col.get('remap', True):
            tokenizer = Tokenizer(min_freq=1, remap=True)
            self.processor_dict[name + '::tokenizer'] = tokenizer

    def fit_numeric_col(self, col, col_series):
        name = col['name']
        feature_type = col['type']
        feature_source = col.get('source', '')
        self.feature_map.features[name] = {'source': feature_source, 'type': feature_type}
        if 'feature_encoder' in col:
            self.feature_map.features[name]['feature_encoder'] = col['feature_encoder']
        if 'embedding_dim' in col:
            self.feature_map.features[name]['embedding_dim'] = col['embedding_dim']
        if 'normalizer' in col:
            normalizer = Normalizer(col['normalizer'])
            if self.rebuild_dataset:
                normalizer.fit(col_series.dropna().values)
            self.processor_dict[name + '::normalizer'] = normalizer

    def fit_embedding_col(self, col):
        name = col['name']
        feature_type = col['type']
        feature_source = col.get('source', '')
        self.feature_map.features[name] = {'source': feature_source, 'type': feature_type}
        if 'feature_encoder' in col:
            self.feature_map.features[name]['feature_encoder'] = col['feature_encoder']
        if 'embedding_dim' in col:
            self.feature_map.features[name]['embedding_dim'] = col['embedding_dim']
        if 'pretrain_dim' in col:
            self.feature_map.features[name]['pretrain_dim'] = col['pretrain_dim']

    def fit_categorical_col(self, col, col_series, min_categr_count=1, num_buckets=10):
        name = col['name']
        feature_type = col['type']
        feature_source = col.get('source', '')
        min_categr_count = col.get('min_categr_count', min_categr_count)
        self.feature_map.features[name] = {'source': feature_source, 'type': feature_type}
        if 'feature_encoder' in col:
            self.feature_map.features[name]['feature_encoder'] = col['feature_encoder']
        if 'embedding_dim' in col:
            self.feature_map.features[name]['embedding_dim'] = col['embedding_dim']
        if 'emb_output_dim' in col:
            self.feature_map.features[name]['emb_output_dim'] = col['emb_output_dim']
        if 'category_processor' not in col:
            tokenizer = Tokenizer(min_freq=min_categr_count, na_value=col.get('fill_na', ''), remap=col.get('remap', True))
            if self.rebuild_dataset:
                tokenizer.fit_on_texts(col_series)
            elif 'vocab_size' in col:
                tokenizer.update_vocab(range(col['vocab_size'] - 1))
            else:
                raise ValueError(f'{name}: vocab_size is required when rebuild_dataset=False')
            if 'share_embedding' in col:
                self.feature_map.features[name]['share_embedding'] = col['share_embedding']
                tknzr_name = col['share_embedding'] + '::tokenizer'
                self.processor_dict[tknzr_name] = tokenizer.merge_vocab(self.processor_dict[tknzr_name])
                self.feature_map.features[col['share_embedding']].update({'oov_idx': self.processor_dict[tknzr_name].vocab['__OOV__'], 'vocab_size': self.processor_dict[tknzr_name].vocab_size()})
            self.processor_dict[name + '::tokenizer'] = tokenizer
            self.feature_map.features[name].update({'padding_idx': 0, 'oov_idx': tokenizer.vocab['__OOV__'], 'vocab_size': tokenizer.vocab_size()})
        else:
            category_processor = col['category_processor']
            self.feature_map.features[name]['category_processor'] = category_processor
            if category_processor == 'quantile_bucket':
                num_buckets = col.get('num_buckets', num_buckets)
                qtf = sklearn_preprocess.QuantileTransformer(n_quantiles=num_buckets + 1)
                if self.rebuild_dataset:
                    qtf.fit(col_series.values)
                    boundaries = qtf.quantiles_[1:-1]
                    self.processor_dict[name + '::boundaries'] = boundaries
                self.feature_map.features[name]['vocab_size'] = num_buckets
            elif category_processor == 'hash_bucket':
                num_buckets = col.get('num_buckets', num_buckets)
                self.feature_map.features[name]['vocab_size'] = num_buckets
                self.processor_dict[name + '::num_buckets'] = num_buckets
            else:
                raise NotImplementedError('category_processor={} not supported.'.format(category_processor))

    def fit_sequence_col(self, col, col_series, min_categr_count=1):
        name = col['name']
        feature_type = col['type']
        feature_source = col.get('source', '')
        min_categr_count = col.get('min_categr_count', min_categr_count)
        self.feature_map.features[name] = {'source': feature_source, 'type': feature_type}
        feature_encoder = col.get('feature_encoder', 'layers.MaskedAveragePooling()')
        if feature_encoder not in [None, 'null', 'None', 'none']:
            self.feature_map.features[name]['feature_encoder'] = feature_encoder
        if 'embedding_dim' in col:
            self.feature_map.features[name]['embedding_dim'] = col['embedding_dim']
        if 'emb_output_dim' in col:
            self.feature_map.features[name]['emb_output_dim'] = col['emb_output_dim']
        splitter = col.get('splitter', '^')
        na_value = col.get('fill_na', '')
        max_len = col.get('max_len', 0)
        padding = col.get('padding', 'post')
        tokenizer = Tokenizer(min_freq=min_categr_count, splitter=splitter, na_value=na_value, max_len=max_len, padding=padding, remap=col.get('remap', True))
        if self.rebuild_dataset:
            tokenizer.fit_on_texts(col_series)
        elif 'vocab_size' in col:
            tokenizer.update_vocab(range(col['vocab_size'] - 1))
        else:
            raise ValueError(f'{name}: vocab_size is required when rebuild_dataset=False')
        if 'share_embedding' in col:
            self.feature_map.features[name]['share_embedding'] = col['share_embedding']
            tknzr_name = col['share_embedding'] + '::tokenizer'
            self.processor_dict[tknzr_name] = tokenizer.merge_vocab(self.processor_dict[tknzr_name])
            self.feature_map.features[col['share_embedding']].update({'oov_idx': self.processor_dict[tknzr_name].vocab['__OOV__'], 'vocab_size': self.processor_dict[tknzr_name].vocab_size()})
        self.processor_dict[name + '::tokenizer'] = tokenizer
        self.feature_map.features[name].update({'padding_idx': 0, 'oov_idx': tokenizer.vocab['__OOV__'], 'max_len': tokenizer.max_len, 'vocab_size': tokenizer.vocab_size()})

    def transform(self, ddf):
        logging.info('Transform feature columns to IDs...')
        for feature, feature_spec in self.feature_map.features.items():
            if feature in ddf.columns:
                feature_type = feature_spec['type']
                col_series = ddf[feature]
                if feature_type == 'meta':
                    if feature + '::tokenizer' in self.processor_dict:
                        tokenizer = self.processor_dict[feature + '::tokenizer']
                        ddf[feature] = tokenizer.encode_meta(col_series)
                        self.processor_dict[feature + '::tokenizer'] = tokenizer
                elif feature_type == 'numeric':
                    normalizer = self.processor_dict.get(feature + '::normalizer')
                    if normalizer:
                        ddf[feature] = normalizer.transform(col_series.values)
                elif feature_type == 'categorical':
                    category_processor = feature_spec.get('category_processor')
                    if category_processor is None:
                        ddf[feature] = self.processor_dict.get(feature + '::tokenizer').encode_category(col_series)
                    elif category_processor == 'numeric_bucket':
                        raise NotImplementedError
                    elif category_processor == 'hash_bucket':
                        raise NotImplementedError
                elif feature_type == 'sequence':
                    ddf[feature] = self.processor_dict.get(feature + '::tokenizer').encode_sequence(col_series)
                elif feature_type == 'embedding':
                    continue
                else:
                    raise NotImplementedError
        return ddf

    def load_pickle(self, pickle_file=None):
        """ Load feature processor from cache """
        if pickle_file is None:
            pickle_file = self.pickle_file
        logging.info('Load feature_processor from pickle: ' + pickle_file)
        if os.path.exists(pickle_file):
            pickled_feature_processor = pickle.load(open(pickle_file, 'rb'))
            if pickled_feature_processor.feature_map.dataset_id == self.feature_map.dataset_id:
                return pickled_feature_processor
        raise IOError('pickle_file={} not valid.'.format(pickle_file))

    def save_pickle(self, pickle_file):
        logging.info('Pickle feature_encode: ' + pickle_file)
        pickle.dump(self, open(pickle_file, 'wb'))

    def save_vocab(self, vocab_file):
        logging.info('Save feature_vocab to json: ' + vocab_file)
        vocab = dict()
        for feature, spec in self.feature_map.features.items():
            if spec['type'] in ['categorical', 'sequence']:
                vocab[feature] = OrderedDict(sorted(self.processor_dict[feature + '::tokenizer'].vocab.items(), key=lambda x: x[1]))
        with open(vocab_file, 'w') as fd:
            fd.write(json.dumps(vocab, indent=4))

    def copy_from(self, src_col):
        return pl.col(src_col)

def _complete_feature_cols(self, feature_cols):
    full_feature_cols = []
    for col in feature_cols:
        name_or_namelist = col['name']
        if isinstance(name_or_namelist, list):
            for _name in name_or_namelist:
                _col = col.copy()
                _col['name'] = _name
                full_feature_cols.append(_col)
        else:
            full_feature_cols.append(col)
    return full_feature_cols

def read_data(self, data_path, data_format='csv', sep=',', n_rows=None, **kwargs):
    if not data_path.endswith(data_format):
        data_path = os.path.join(data_path, f'*.{data_format}')
    logging.info('Reading files: ' + data_path)
    file_names = sorted(glob.glob(data_path))
    assert len(file_names) > 0, f'Invalid data path: {data_path}'
    if data_format == 'csv':
        dfs = [pl.scan_csv(source=file_name, separator=sep, dtypes=self.dtype_dict, low_memory=False, n_rows=n_rows) for file_name in file_names]
        ddf = pl.concat(dfs)
    elif data_format == 'parquet':
        dfs = [pl.scan_parquet(source=file_name, low_memory=False, n_rows=n_rows) for file_name in file_names]
        ddf = pl.concat(dfs)
    else:
        NotImplementedError(f'data_format={data_format} not supported.')
    return ddf

def fit(self, train_ddf, min_categr_count=1, num_buckets=10, rebuild_dataset=True, **kwargs):
    logging.info('Fit feature processor...')
    self.rebuild_dataset = rebuild_dataset
    for col in self.feature_cols:
        name = col['name']
        if col['active']:
            logging.info('Processing column: {}'.format(col))
            col_series = train_ddf.select(name).collect().to_series().to_pandas() if self.rebuild_dataset else None
            if col['type'] == 'meta':
                self.fit_meta_col(col)
            elif col['type'] == 'numeric':
                self.fit_numeric_col(col, col_series)
            elif col['type'] == 'embedding':
                self.fit_embedding_col(col)
            elif col['type'] == 'categorical':
                self.fit_categorical_col(col, col_series, min_categr_count=min_categr_count, num_buckets=num_buckets)
            elif col['type'] == 'sequence':
                self.fit_sequence_col(col, col_series, min_categr_count=min_categr_count)
            else:
                raise NotImplementedError('feature type={}'.format(col['type']))
    os.makedirs(self.data_dir, exist_ok=True)
    for col in self.feature_cols:
        name = col['name']
        if 'pretrained_emb' in col:
            logging.info('Loading pretrained embedding: ' + name)
            if 'pretrain_dim' in col:
                self.feature_map.features[name]['pretrain_dim'] = col['pretrain_dim']
            ext = Path(col['pretrained_emb']).suffix
            shutil.copy(col['pretrained_emb'], os.path.join(self.data_dir, 'pretrained_{}{}'.format(name, ext)))
            self.feature_map.features[name]['pretrained_emb'] = 'pretrained_{}{}'.format(name, ext)
            self.feature_map.features[name]['freeze_emb'] = col.get('freeze_emb', True)
            self.feature_map.features[name]['pretrain_usage'] = col.get('pretrain_usage', 'init')
            tokenizer = self.processor_dict[name + '::tokenizer']
            tokenizer.load_pretrained_vocab(self.dtype_dict[name], col['pretrained_emb'])
            self.processor_dict[name + '::tokenizer'] = tokenizer
            self.feature_map.features[name]['vocab_size'] = tokenizer.vocab_size()
    for name, spec in self.feature_map.features.items():
        if spec['type'] == 'numeric':
            self.feature_map.total_features += 1
        elif spec['type'] in ['categorical', 'sequence']:
            if 'share_embedding' in spec:
                tokenizer = self.processor_dict[name + '::tokenizer']
                tokenizer.vocab = self.processor_dict[spec['share_embedding'] + '::tokenizer'].vocab
                self.processor_dict[name + '::tokenizer'] = tokenizer
                self.feature_map.features[name].update({'oov_idx': tokenizer.vocab['__OOV__'], 'vocab_size': tokenizer.vocab_size()})
            else:
                self.feature_map.total_features += self.feature_map.features[name]['vocab_size']
            if 'pretrained_emb' not in spec:
                del self.feature_map.features[name]['oov_idx']
    self.feature_map.num_fields = self.feature_map.get_num_fields()
    self.feature_map.set_column_index()
    self.feature_map.save(self.json_file)
    self.save_pickle(self.pickle_file)
    self.save_vocab(self.vocab_file)
    logging.info('Set feature processor done.')

def transform(self, ddf):
    logging.info('Transform feature columns to IDs...')
    for feature, feature_spec in self.feature_map.features.items():
        if feature in ddf.columns:
            feature_type = feature_spec['type']
            col_series = ddf[feature]
            if feature_type == 'meta':
                if feature + '::tokenizer' in self.processor_dict:
                    tokenizer = self.processor_dict[feature + '::tokenizer']
                    ddf[feature] = tokenizer.encode_meta(col_series)
                    self.processor_dict[feature + '::tokenizer'] = tokenizer
            elif feature_type == 'numeric':
                normalizer = self.processor_dict.get(feature + '::normalizer')
                if normalizer:
                    ddf[feature] = normalizer.transform(col_series.values)
            elif feature_type == 'categorical':
                category_processor = feature_spec.get('category_processor')
                if category_processor is None:
                    ddf[feature] = self.processor_dict.get(feature + '::tokenizer').encode_category(col_series)
                elif category_processor == 'numeric_bucket':
                    raise NotImplementedError
                elif category_processor == 'hash_bucket':
                    raise NotImplementedError
            elif feature_type == 'sequence':
                ddf[feature] = self.processor_dict.get(feature + '::tokenizer').encode_sequence(col_series)
            elif feature_type == 'embedding':
                continue
            else:
                raise NotImplementedError
    return ddf

def load_pickle(self, pickle_file=None):
    """ Load feature processor from cache """
    if pickle_file is None:
        pickle_file = self.pickle_file
    logging.info('Load feature_processor from pickle: ' + pickle_file)
    if os.path.exists(pickle_file):
        pickled_feature_processor = pickle.load(open(pickle_file, 'rb'))
        if pickled_feature_processor.feature_map.dataset_id == self.feature_map.dataset_id:
            return pickled_feature_processor
    raise IOError('pickle_file={} not valid.'.format(pickle_file))

def save_pickle(self, pickle_file):
    logging.info('Pickle feature_encode: ' + pickle_file)
    pickle.dump(self, open(pickle_file, 'wb'))

def save_vocab(self, vocab_file):
    logging.info('Save feature_vocab to json: ' + vocab_file)
    vocab = dict()
    for feature, spec in self.feature_map.features.items():
        if spec['type'] in ['categorical', 'sequence']:
            vocab[feature] = OrderedDict(sorted(self.processor_dict[feature + '::tokenizer'].vocab.items(), key=lambda x: x[1]))
    with open(vocab_file, 'w') as fd:
        fd.write(json.dumps(vocab, indent=4))

class TFRecordDataLoader(object):

    def __init__(self, feature_map, stage='both', train_data=None, valid_data=None, test_data=None, batch_size=32, shuffle=True, drop_remainder=False, **kwargs):
        logging.info('Loading data...')
        self.stage = stage
        self.train_data = train_data
        self.valid_data = valid_data
        self.test_data = test_data
        self.batch_size = batch_size
        self.shuffle = shuffle
        self.drop_remainder = drop_remainder
        self.schema = dict()
        for feat, feat_spec in feature_map.features.items():
            if feat_spec['type'] == 'numeric':
                self.schema[feat] = tf.io.FixedLenFeature(dtype=tf.float32, shape=1)
            elif feat_spec['type'] in ['categorical', 'meta']:
                self.schema[feat] = tf.io.FixedLenFeature(dtype=tf.int64, shape=1)
            elif feat_spec['type'] == 'sequence':
                self.schema[feat] = tf.io.FixedLenFeature(dtype=tf.int64, shape=feat_spec['max_len'])
        for label in feature_map.labels:
            self.schema[label] = tf.io.FixedLenFeature(dtype=tf.float32, shape=1)

    def input_fn(self, filenames, batch_size=32, shuffle=True):

        def parse_example(example):
            example_dict = tf.io.parse_single_example(example, features=self.schema)
            return example_dict
        dataset = tf.data.TFRecordDataset(filenames).map(parse_example, num_parallel_calls=1)
        dataset = dataset.prefetch(buffer_size=1).batch(batch_size, drop_remainder=self.drop_remainder)
        if shuffle:
            dataset = dataset.shuffle(batch_size * 10)
        return dataset

    def make_iterator(self):
        if self.stage == 'train':
            logging.info('Loading train and validation data done.')
            return (self.input_fn(self.train_data, batch_size=self.batch_size, shuffle=self.shuffle), self.input_fn(self.valid_data, batch_size=self.batch_size, shuffle=False))
        elif self.stage == 'test':
            logging.info('Loading test data done.')
            return self.input_fn(self.test_data, batch_size=self.batch_size, shuffle=False)
        else:
            logging.info('Loading data done.')
            return (self.input_fn(self.train_data, batch_size=self.batch_size, shuffle=self.shuffle), self.input_fn(self.valid_data, batch_size=self.batch_size, shuffle=False), self.input_fn(self.test_data, batch_size=self.batch_size, shuffle=False))

def __init__(self, feature_map, stage='both', train_data=None, valid_data=None, test_data=None, batch_size=32, shuffle=True, drop_remainder=False, **kwargs):
    logging.info('Loading data...')
    self.stage = stage
    self.train_data = train_data
    self.valid_data = valid_data
    self.test_data = test_data
    self.batch_size = batch_size
    self.shuffle = shuffle
    self.drop_remainder = drop_remainder
    self.schema = dict()
    for feat, feat_spec in feature_map.features.items():
        if feat_spec['type'] == 'numeric':
            self.schema[feat] = tf.io.FixedLenFeature(dtype=tf.float32, shape=1)
        elif feat_spec['type'] in ['categorical', 'meta']:
            self.schema[feat] = tf.io.FixedLenFeature(dtype=tf.int64, shape=1)
        elif feat_spec['type'] == 'sequence':
            self.schema[feat] = tf.io.FixedLenFeature(dtype=tf.int64, shape=feat_spec['max_len'])
    for label in feature_map.labels:
        self.schema[label] = tf.io.FixedLenFeature(dtype=tf.float32, shape=1)

def make_iterator(self):
    if self.stage == 'train':
        logging.info('Loading train and validation data done.')
        return (self.input_fn(self.train_data, batch_size=self.batch_size, shuffle=self.shuffle), self.input_fn(self.valid_data, batch_size=self.batch_size, shuffle=False))
    elif self.stage == 'test':
        logging.info('Loading test data done.')
        return self.input_fn(self.test_data, batch_size=self.batch_size, shuffle=False)
    else:
        logging.info('Loading data done.')
        return (self.input_fn(self.train_data, batch_size=self.batch_size, shuffle=self.shuffle), self.input_fn(self.valid_data, batch_size=self.batch_size, shuffle=False), self.input_fn(self.test_data, batch_size=self.batch_size, shuffle=False))

class FeatureEmbeddingDict(Layer):

    def __init__(self, feature_map, embedding_dim, embedding_initializer='random_normal(stddev=1e-4)', embedding_regularizer=None, required_feature_columns=None, not_required_feature_columns=None, use_pretrain=True, use_sharing=True, name_prefix='emb_'):
        super(FeatureEmbeddingDict, self).__init__()
        self._feature_map = feature_map
        self.required_feature_columns = required_feature_columns
        self.not_required_feature_columns = not_required_feature_columns
        self.use_pretrain = use_pretrain
        self.embedding_initializer = embedding_initializer
        self.embedding_layers = OrderedDict()
        self.feature_encoders = OrderedDict()
        for feature, feature_spec in self._feature_map.features.items():
            if self.is_required(feature):
                if not (use_pretrain and use_sharing) and embedding_dim == 1:
                    feat_emb_dim = 1
                    if feature_spec['type'] == 'sequence':
                        self.feature_encoders[feature] = layers.MaskedSumPooling()
                else:
                    feat_emb_dim = feature_spec.get('embedding_dim', embedding_dim)
                    if feature_spec.get('feature_encoder', None):
                        self.feature_encoders[feature] = self.get_feature_encoder(feature_spec['feature_encoder'])
                if use_sharing and feature_spec.get('share_embedding') in self.embedding_layers:
                    self.embedding_layers[feature] = self.embedding_layers[feature_spec['share_embedding']]
                    continue
                if feature_spec['type'] == 'numeric':
                    self.embedding_layers[feature] = tf.keras.layers.Dense(feat_emb_dim, use_bias=False)
                elif feature_spec['type'] == 'categorical':
                    padding_idx = feature_spec.get('padding_idx', None)
                    embedding_matrix = Embedding(feature_spec['vocab_size'], feat_emb_dim, embeddings_initializer=get_initializer(embedding_initializer), embeddings_regularizer=get_regularizer(embedding_regularizer), mask_zero=True if padding_idx == 0 else False, input_length=1, name=name_prefix + feature)
                    if use_pretrain and 'pretrained_emb' in feature_spec:
                        embedding_matrix = self.load_pretrained_embedding(embedding_matrix, feature_map, feature, freeze=feature_spec['freeze_emb'], padding_idx=padding_idx)
                    self.embedding_layers[feature] = embedding_matrix
                elif feature_spec['type'] == 'sequence':
                    padding_idx = feature_spec.get('padding_idx', None)
                    embedding_matrix = Embedding(feature_spec['vocab_size'], feat_emb_dim, embeddings_initializer=get_initializer(embedding_initializer), embeddings_regularizer=get_regularizer(embedding_regularizer), mask_zero=True if padding_idx == 0 else False, input_length=feature_spec['max_len'], name=name_prefix + feature)
                    if use_pretrain and 'pretrained_emb' in feature_spec:
                        embedding_matrix = self.load_pretrained_embedding(embedding_matrix, feature_map, feature, freeze=feature_spec['freeze_emb'], padding_idx=padding_idx)
                    self.embedding_layers[feature] = embedding_matrix

    def get_feature_encoder(self, encoder):
        try:
            if type(encoder) == list:
                encoder_list = []
                for enc in encoder:
                    encoder_list.append(eval(enc))
                encoder_layer = tf.keras.Sequential(*encoder_list)
            else:
                encoder_layer = eval(encoder)
            return encoder_layer
        except:
            raise ValueError('feature_encoder={} is not supported.'.format(encoder))

    def is_required(self, feature):
        """ Check whether feature is required for embedding """
        feature_spec = self._feature_map.features[feature]
        if feature_spec['type'] == 'meta':
            return False
        elif self.required_feature_columns and feature not in self.required_feature_columns:
            return False
        elif self.not_required_feature_columns and feature in self.not_required_feature_columns:
            return False
        else:
            return True

    def get_pretrained_embedding(self, pretrained_path, feature_name):
        with h5py.File(pretrained_path, 'r') as hf:
            embeddings = hf[feature_name][:]
        return embeddings

    def load_pretrained_embedding(self, embedding_matrix, feature_map, feature_name, freeze=False, padding_idx=None):
        pretrained_path = os.path.join(feature_map.data_dir, feature_map.features[feature_name]['pretrained_emb'])
        embeddings = self.get_pretrained_embedding(pretrained_path, feature_name)
        if padding_idx is not None:
            embeddings[padding_idx] = np.zeros(embeddings.shape[-1])
        assert embeddings.shape[-1] == embedding_matrix.embedding_dim, "{}'s embedding_dim is not correctly set to match its pretrained_emb shape".format(feature_name)
        embedding_matrix.set_weights([embeddings])
        if freeze:
            embedding_matrix.trainable = False
        return embedding_matrix

    def dict2tensor(self, embedding_dict, feature_list=[], feature_source=[], feature_type=[], flatten_emb=False):
        if type(feature_source) != list:
            feature_source = [feature_source]
        if type(feature_type) != list:
            feature_type = [feature_type]
        feature_emb_list = []
        for feature, feature_spec in self._feature_map.features.items():
            if feature_source and feature_spec['source'] not in feature_source:
                continue
            if feature_type and feature_spec['type'] not in feature_type:
                continue
            if feature_list and feature not in feature_list:
                continue
            if feature in embedding_dict:
                feature_emb_list.append(embedding_dict[feature])
        if flatten_emb:
            feature_emb = tf.squeeze(tf.concat(feature_emb_list, axis=-1), axis=1)
        else:
            feature_emb = tf.concat(feature_emb_list, axis=1)
        return feature_emb

    def call(self, inputs, feature_source=[], feature_type=[]):
        if type(feature_source) != list:
            feature_source = [feature_source]
        if type(feature_type) != list:
            feature_type = [feature_type]
        feature_emb_dict = OrderedDict()
        for feature, feature_spec in self._feature_map.features.items():
            if feature_source and feature_spec['source'] not in feature_source:
                continue
            if feature_type and feature_spec['type'] not in feature_type:
                continue
            if feature in self.embedding_layers:
                if feature_spec['type'] == 'numeric':
                    inp = tf.reshape(inputs[feature], (-1, 1))
                    embeddings = self.embedding_layers[feature](inp)
                elif feature_spec['type'] == 'categorical':
                    inp = inputs[feature]
                    embeddings = self.embedding_layers[feature](inp)
                elif feature_spec['type'] == 'sequence':
                    inp = inputs[feature]
                    embeddings = self.embedding_layers[feature](inp)
                else:
                    raise NotImplementedError
                if feature in self.feature_encoders:
                    embeddings = self.feature_encoders[feature](embeddings)
                feature_emb_dict[feature] = embeddings
        return feature_emb_dict

def get_pretrained_embedding(self, pretrained_path, feature_name):
    with h5py.File(pretrained_path, 'r') as hf:
        embeddings = hf[feature_name][:]
    return embeddings

def call(self, inputs, feature_source=[], feature_type=[]):
    if type(feature_source) != list:
        feature_source = [feature_source]
    if type(feature_type) != list:
        feature_type = [feature_type]
    feature_emb_dict = OrderedDict()
    for feature, feature_spec in self._feature_map.features.items():
        if feature_source and feature_spec['source'] not in feature_source:
            continue
        if feature_type and feature_spec['type'] not in feature_type:
            continue
        if feature in self.embedding_layers:
            if feature_spec['type'] == 'numeric':
                inp = tf.reshape(inputs[feature], (-1, 1))
                embeddings = self.embedding_layers[feature](inp)
            elif feature_spec['type'] == 'categorical':
                inp = inputs[feature]
                embeddings = self.embedding_layers[feature](inp)
            elif feature_spec['type'] == 'sequence':
                inp = inputs[feature]
                embeddings = self.embedding_layers[feature](inp)
            else:
                raise NotImplementedError
            if feature in self.feature_encoders:
                embeddings = self.feature_encoders[feature](embeddings)
            feature_emb_dict[feature] = embeddings
    return feature_emb_dict

class BaseModel(Model):

    def __init__(self, feature_map, model_id='BaseModel', task='binary_classification', monitor='AUC', save_best_only=True, monitor_mode='max', early_stop_patience=2, eval_steps=None, reduce_lr_on_plateau=True, **kwargs):
        super(BaseModel, self).__init__()
        self.valid_gen = None
        self._monitor_mode = monitor_mode
        self._monitor = Monitor(kv=monitor)
        self._early_stop_patience = early_stop_patience
        self._eval_steps = eval_steps
        self._save_best_only = save_best_only
        self._verbose = kwargs['verbose']
        self._reduce_lr_on_plateau = reduce_lr_on_plateau
        self.feature_map = feature_map
        self.output_activation = self.get_output_activation(task)
        self.model_id = model_id
        self.model_dir = os.path.join(kwargs['model_root'], feature_map.dataset_id)
        self.checkpoint = os.path.abspath(os.path.join(self.model_dir, self.model_id + '.model'))
        self.validation_metrics = kwargs['metrics']

    def compile(self, optimizer, loss, lr):
        self.optimizer = get_optimizer(optimizer, lr)
        self.loss_fn = get_loss(loss)

    def add_loss(self, inputs):
        return_dict = self(inputs, training=True)
        y_true = self.get_labels(inputs)
        loss = self.loss_fn(return_dict['y_pred'], y_true)
        return loss

    def compute_loss(self, inputs):
        total_loss = self.add_loss(inputs) + sum(self.losses)
        return total_loss

    def get_inputs(self, inputs, feature_source=None):
        if feature_source and type(feature_source) == str:
            feature_source = [feature_source]
        X_dict = dict()
        for feature, spec in self.feature_map.features.items():
            if feature_source is not None and spec['source'] not in feature_source:
                continue
            if spec['type'] == 'meta':
                continue
            X_dict[feature] = inputs[feature]
        return X_dict

    def get_labels(self, inputs):
        """ assert len(labels) == 1, "Please override get_labels() when using multiple labels!"
        """
        labels = self.feature_map.labels
        y = inputs[labels[0]]
        return y

    def get_group_id(self, inputs):
        return inputs[self.feature_map.group_id]

    def lr_decay(self, factor=0.1, min_lr=1e-06):
        self.optimizer.learning_rate = max(self.optimizer.learning_rate * factor, min_lr)
        return self.optimizer.lr.numpy()

    def fit(self, data_generator, epochs=1, validation_data=None, max_gradient_norm=10.0, **kwargs):
        self.valid_gen = validation_data
        self._max_gradient_norm = max_gradient_norm
        self._best_metric = np.Inf if self._monitor_mode == 'min' else -np.Inf
        self._stopping_steps = 0
        self._stop_training = False
        self._total_steps = 0
        self._batch_index = 0
        self._epoch_index = 0
        logging.info('************ Epoch=1 start ************')
        for epoch in range(epochs):
            self._epoch_index = epoch
            self.train_epoch(data_generator)
            if self._stop_training:
                break
            else:
                logging.info('************ Epoch={} end ************'.format(self._epoch_index + 1))
        logging.info('Training finished.')
        logging.info('Load best model: {}'.format(self.checkpoint))
        self.load_weights(self.checkpoint)

    def train_epoch(self, data_generator):
        self._batch_index = 0
        train_loss = 0
        if self._verbose == 0:
            batch_iterator = data_generator
        else:
            batch_iterator = tqdm(data_generator, disable=False, file=sys.stdout)
        for batch_index, batch_data in enumerate(batch_iterator):
            self._batch_index = batch_index
            self._total_steps += 1
            loss = self.train_step(batch_data)
            train_loss += loss.numpy()
            if self._eval_steps is not None and self._total_steps % self._eval_steps == 0:
                logging.info('Train loss: {:.6f}'.format(train_loss / self._eval_steps))
                train_loss = 0
                self.eval_step()
            if self._stop_training:
                break
        if self._eval_steps is None:
            logging.info('Train loss: {:.6f}'.format(train_loss / (self._batch_index + 1)))
            self.eval_step()

    @tf.function
    def train_step(self, batch_data):
        with tf.GradientTape() as tape:
            loss = self.compute_loss(batch_data)
            grads = tape.gradient(loss, self.trainable_variables)
            grads, _ = tf.clip_by_global_norm(grads, self._max_gradient_norm)
            self.optimizer.apply_gradients(zip(grads, self.trainable_variables))
        return loss

    def eval_step(self):
        logging.info('Evaluation @epoch {} - batch {}: '.format(self._epoch_index + 1, self._batch_index + 1))
        val_logs = self.evaluate(self.valid_gen, metrics=self._monitor.get_metrics())
        self.checkpoint_and_earlystop(val_logs)

    def checkpoint_and_earlystop(self, logs, min_delta=1e-06):
        monitor_value = self._monitor.get_value(logs)
        if self._monitor_mode == 'min' and monitor_value > self._best_metric - min_delta or (self._monitor_mode == 'max' and monitor_value < self._best_metric + min_delta):
            self._stopping_steps += 1
            logging.info('Monitor({})={:.6f} STOP!'.format(self._monitor_mode, monitor_value))
            if self._reduce_lr_on_plateau:
                current_lr = self.lr_decay()
                logging.info('Reduce learning rate on plateau: {:.6f}'.format(current_lr))
        else:
            self._stopping_steps = 0
            self._best_metric = monitor_value
            if self._save_best_only:
                logging.info('Save best model: monitor({})={:.6f}'.format(self._monitor_mode, monitor_value))
                self.save_weights(self.checkpoint)
        if self._stopping_steps >= self._early_stop_patience:
            self._stop_training = True
            logging.info('********* Epoch=={} early stop *********'.format(self._epoch_index + 1))
        if not self._save_best_only:
            self.save_weights(self.checkpoint)

    def evaluate(self, data_generator, metrics=None):
        y_pred = []
        y_true = []
        group_id = []
        if self._verbose > 0:
            data_generator = tqdm(data_generator, disable=False, file=sys.stdout)
        for batch_data in data_generator:
            return_dict = self(batch_data, training=True)
            y_pred.extend(return_dict['y_pred'].numpy().reshape(-1))
            y_true.extend(self.get_labels(batch_data).numpy().reshape(-1))
            if self.feature_map.group_id is not None:
                group_id.extend(self.get_group_id(batch_data).numpy().reshape(-1))
        y_pred = np.array(y_pred, np.float64)
        y_true = np.array(y_true, np.float64)
        group_id = np.array(group_id) if len(group_id) > 0 else None
        if metrics is not None:
            val_logs = self.evaluate_metrics(y_true, y_pred, metrics, group_id)
        else:
            val_logs = self.evaluate_metrics(y_true, y_pred, self.validation_metrics, group_id)
        logging.info('[Metrics] ' + ' - '.join(('{}: {:.6f}'.format(k, v) for k, v in val_logs.items())))
        return val_logs

    def evaluate_metrics(self, y_true, y_pred, metrics, group_id=None):
        return evaluate_metrics(y_true, y_pred, metrics, group_id)

    def get_output_activation(self, task):
        if task == 'binary_classification':
            return tf.keras.layers.Activation('sigmoid')
        elif task == 'regression':
            return tf.identity
        else:
            raise NotImplementedError('task={} is not supported.'.format(task))

def get_inputs(self, inputs, feature_source=None):
    if feature_source and type(feature_source) == str:
        feature_source = [feature_source]
    X_dict = dict()
    for feature, spec in self.feature_map.features.items():
        if feature_source is not None and spec['source'] not in feature_source:
            continue
        if spec['type'] == 'meta':
            continue
        X_dict[feature] = inputs[feature]
    return X_dict

def train_epoch(self, data_generator):
    self._batch_index = 0
    train_loss = 0
    if self._verbose == 0:
        batch_iterator = data_generator
    else:
        batch_iterator = tqdm(data_generator, disable=False, file=sys.stdout)
    for batch_index, batch_data in enumerate(batch_iterator):
        self._batch_index = batch_index
        self._total_steps += 1
        loss = self.train_step(batch_data)
        train_loss += loss.numpy()
        if self._eval_steps is not None and self._total_steps % self._eval_steps == 0:
            logging.info('Train loss: {:.6f}'.format(train_loss / self._eval_steps))
            train_loss = 0
            self.eval_step()
        if self._stop_training:
            break
    if self._eval_steps is None:
        logging.info('Train loss: {:.6f}'.format(train_loss / (self._batch_index + 1)))
        self.eval_step()

def evaluate(self, data_generator, metrics=None):
    y_pred = []
    y_true = []
    group_id = []
    if self._verbose > 0:
        data_generator = tqdm(data_generator, disable=False, file=sys.stdout)
    for batch_data in data_generator:
        return_dict = self(batch_data, training=True)
        y_pred.extend(return_dict['y_pred'].numpy().reshape(-1))
        y_true.extend(self.get_labels(batch_data).numpy().reshape(-1))
        if self.feature_map.group_id is not None:
            group_id.extend(self.get_group_id(batch_data).numpy().reshape(-1))
    y_pred = np.array(y_pred, np.float64)
    y_true = np.array(y_true, np.float64)
    group_id = np.array(group_id) if len(group_id) > 0 else None
    if metrics is not None:
        val_logs = self.evaluate_metrics(y_true, y_pred, metrics, group_id)
    else:
        val_logs = self.evaluate_metrics(y_true, y_pred, self.validation_metrics, group_id)
    logging.info('[Metrics] ' + ' - '.join(('{}: {:.6f}'.format(k, v) for k, v in val_logs.items())))
    return val_logs

def evaluate_metrics(self, y_true, y_pred, metrics, group_id=None):
    return evaluate_metrics(y_true, y_pred, metrics, group_id)

class ParquetDataset(Dataset):

    def __init__(self, feature_map, data_path):
        self.feature_map = feature_map
        self.darray = self.load_data(data_path)

    def __getitem__(self, index):
        return self.darray[index, :]

    def __len__(self):
        return self.darray.shape[0]

    def load_data(self, data_path):
        df = pd.read_parquet(data_path)
        all_cols = list(self.feature_map.features.keys()) + self.feature_map.labels
        data_arrays = []
        for col in all_cols:
            if df[col].dtype == 'object':
                array = np.array(df[col].to_list())
            else:
                array = df[col].to_numpy()
            data_arrays.append(array)
        return np.column_stack(data_arrays)

def load_data(self, data_path):
    df = pd.read_parquet(data_path)
    all_cols = list(self.feature_map.features.keys()) + self.feature_map.labels
    data_arrays = []
    for col in all_cols:
        if df[col].dtype == 'object':
            array = np.array(df[col].to_list())
        else:
            array = df[col].to_numpy()
        data_arrays.append(array)
    return np.column_stack(data_arrays)

class ParquetDataLoader(DataLoader):

    def __init__(self, feature_map, data_path, batch_size=32, shuffle=False, num_workers=1, **kwargs):
        if not data_path.endswith('.parquet'):
            data_path += '.parquet'
        self.dataset = ParquetDataset(feature_map, data_path)
        super().__init__(dataset=self.dataset, batch_size=batch_size, shuffle=shuffle, num_workers=num_workers, collate_fn=BatchCollator(feature_map))
        self.num_samples = len(self.dataset)
        self.num_blocks = 1
        self.num_batches = int(np.ceil(self.num_samples / self.batch_size))

    def __len__(self):
        return self.num_batches

def __init__(self, feature_map, data_path, batch_size=32, shuffle=False, num_workers=1, **kwargs):
    if not data_path.endswith('.parquet'):
        data_path += '.parquet'
    self.dataset = ParquetDataset(feature_map, data_path)
    super().__init__(dataset=self.dataset, batch_size=batch_size, shuffle=shuffle, num_workers=num_workers, collate_fn=BatchCollator(feature_map))
    self.num_samples = len(self.dataset)
    self.num_blocks = 1
    self.num_batches = int(np.ceil(self.num_samples / self.batch_size))

class BatchCollator(object):

    def __init__(self, feature_map):
        self.feature_map = feature_map

    def __call__(self, batch):
        batch_tensor = default_collate(batch)
        all_cols = list(self.feature_map.features.keys()) + self.feature_map.labels
        batch_dict = dict()
        for col in all_cols:
            batch_dict[col] = batch_tensor[:, self.feature_map.get_column_index(col)]
        return batch_dict

def __call__(self, batch):
    batch_tensor = default_collate(batch)
    all_cols = list(self.feature_map.features.keys()) + self.feature_map.labels
    batch_dict = dict()
    for col in all_cols:
        batch_dict[col] = batch_tensor[:, self.feature_map.get_column_index(col)]
    return batch_dict

class NpzDataset(Dataset):

    def __init__(self, feature_map, data_path):
        self.feature_map = feature_map
        self.darray = self.load_data(data_path)

    def __getitem__(self, index):
        return self.darray[index, :]

    def __len__(self):
        return self.darray.shape[0]

    def load_data(self, data_path):
        data_dict = np.load(data_path)
        all_cols = list(self.feature_map.features.keys()) + self.feature_map.labels
        data_arrays = [data_dict[col] for col in all_cols]
        return np.column_stack(data_arrays)

def load_data(self, data_path):
    data_dict = np.load(data_path)
    all_cols = list(self.feature_map.features.keys()) + self.feature_map.labels
    data_arrays = [data_dict[col] for col in all_cols]
    return np.column_stack(data_arrays)

class NpzDataLoader(DataLoader):

    def __init__(self, feature_map, data_path, batch_size=32, shuffle=False, num_workers=1, **kwargs):
        if not data_path.endswith('.npz'):
            data_path += '.npz'
        self.dataset = NpzDataset(feature_map, data_path)
        super(NpzDataLoader, self).__init__(dataset=self.dataset, batch_size=batch_size, shuffle=shuffle, num_workers=num_workers, collate_fn=BatchCollator(feature_map))
        self.num_samples = len(self.dataset)
        self.num_blocks = 1
        self.num_batches = int(np.ceil(self.num_samples * 1.0 / self.batch_size))

    def __len__(self):
        return self.num_batches

def __init__(self, feature_map, data_path, batch_size=32, shuffle=False, num_workers=1, **kwargs):
    if not data_path.endswith('.npz'):
        data_path += '.npz'
    self.dataset = NpzDataset(feature_map, data_path)
    super(NpzDataLoader, self).__init__(dataset=self.dataset, batch_size=batch_size, shuffle=shuffle, num_workers=num_workers, collate_fn=BatchCollator(feature_map))
    self.num_samples = len(self.dataset)
    self.num_blocks = 1
    self.num_batches = int(np.ceil(self.num_samples * 1.0 / self.batch_size))

class BatchCollator(object):

    def __init__(self, feature_map):
        self.feature_map = feature_map

    def __call__(self, batch):
        batch_tensor = default_collate(batch)
        all_cols = list(self.feature_map.features.keys()) + self.feature_map.labels
        batch_dict = dict()
        for col in all_cols:
            batch_dict[col] = batch_tensor[:, self.feature_map.get_column_index(col)]
        return batch_dict

def __call__(self, batch):
    batch_tensor = default_collate(batch)
    all_cols = list(self.feature_map.features.keys()) + self.feature_map.labels
    batch_dict = dict()
    for col in all_cols:
        batch_dict[col] = batch_tensor[:, self.feature_map.get_column_index(col)]
    return batch_dict

class ParquetIterDataPipe(IterDataPipe):

    def __init__(self, data_blocks, feature_map):
        self.feature_map = feature_map
        self.data_blocks = data_blocks

    def load_data(self, data_path):
        df = pd.read_parquet(data_path)
        all_cols = list(self.feature_map.features.keys()) + self.feature_map.labels
        data_arrays = []
        for col in all_cols:
            if df[col].dtype == 'object':
                array = np.array(df[col].to_list())
            else:
                array = df[col].to_numpy()
            data_arrays.append(array)
        return np.column_stack(data_arrays)

    def read_block(self, data_block):
        darray = self.load_data(data_block)
        for idx in range(darray.shape[0]):
            yield darray[idx, :]

    def __iter__(self):
        worker_info = get_worker_info()
        if worker_info is None:
            block_list = self.data_blocks
        else:
            block_list = [block for idx, block in enumerate(self.data_blocks) if idx % worker_info.num_workers == worker_info.id]
        return chain.from_iterable(map(self.read_block, block_list))

def load_data(self, data_path):
    df = pd.read_parquet(data_path)
    all_cols = list(self.feature_map.features.keys()) + self.feature_map.labels
    data_arrays = []
    for col in all_cols:
        if df[col].dtype == 'object':
            array = np.array(df[col].to_list())
        else:
            array = df[col].to_numpy()
        data_arrays.append(array)
    return np.column_stack(data_arrays)

class ParquetBlockDataLoader(DataLoader):

    def __init__(self, feature_map, data_path, split='train', batch_size=32, shuffle=False, num_workers=1, buffer_size=100000, **kwargs):
        if not data_path.endswith('parquet'):
            data_path = os.path.join(data_path, '*.parquet')
        data_blocks = sorted(glob.glob(data_path))
        assert len(data_blocks) > 0, f'invalid data_path: {data_path}'
        self.data_blocks = data_blocks
        self.num_blocks = len(self.data_blocks)
        self.feature_map = feature_map
        self.batch_size = batch_size
        self.num_batches, self.num_samples = self.count_batches_and_samples()
        datapipe = ParquetIterDataPipe(self.data_blocks, feature_map)
        if shuffle:
            datapipe = datapipe.shuffle(buffer_size=buffer_size)
        elif split == 'test':
            num_workers = 1
        super().__init__(dataset=datapipe, batch_size=batch_size, num_workers=num_workers, collate_fn=BatchCollator(feature_map))

    def __len__(self):
        return self.num_batches

    def count_batches_and_samples(self):
        num_samples = 0
        for data_block in self.data_blocks:
            df = pl.scan_parquet(data_block)
            num_samples += df.select(pl.count()).collect().item()
        num_batches = int(np.ceil(num_samples / self.batch_size))
        return (num_batches, num_samples)

def __init__(self, feature_map, data_path, split='train', batch_size=32, shuffle=False, num_workers=1, buffer_size=100000, **kwargs):
    if not data_path.endswith('parquet'):
        data_path = os.path.join(data_path, '*.parquet')
    data_blocks = sorted(glob.glob(data_path))
    assert len(data_blocks) > 0, f'invalid data_path: {data_path}'
    self.data_blocks = data_blocks
    self.num_blocks = len(self.data_blocks)
    self.feature_map = feature_map
    self.batch_size = batch_size
    self.num_batches, self.num_samples = self.count_batches_and_samples()
    datapipe = ParquetIterDataPipe(self.data_blocks, feature_map)
    if shuffle:
        datapipe = datapipe.shuffle(buffer_size=buffer_size)
    elif split == 'test':
        num_workers = 1
    super().__init__(dataset=datapipe, batch_size=batch_size, num_workers=num_workers, collate_fn=BatchCollator(feature_map))

def count_batches_and_samples(self):
    num_samples = 0
    for data_block in self.data_blocks:
        df = pl.scan_parquet(data_block)
        num_samples += df.select(pl.count()).collect().item()
    num_batches = int(np.ceil(num_samples / self.batch_size))
    return (num_batches, num_samples)

class BatchCollator(object):

    def __init__(self, feature_map):
        self.feature_map = feature_map

    def __call__(self, batch):
        batch_tensor = default_collate(batch)
        all_cols = list(self.feature_map.features.keys()) + self.feature_map.labels
        batch_dict = dict()
        for col in all_cols:
            batch_dict[col] = batch_tensor[:, self.feature_map.get_column_index(col)]
        return batch_dict

def __call__(self, batch):
    batch_tensor = default_collate(batch)
    all_cols = list(self.feature_map.features.keys()) + self.feature_map.labels
    batch_dict = dict()
    for col in all_cols:
        batch_dict[col] = batch_tensor[:, self.feature_map.get_column_index(col)]
    return batch_dict

class RankDataLoader(object):

    def __init__(self, feature_map, stage='both', train_data=None, valid_data=None, test_data=None, batch_size=32, shuffle=True, streaming=False, data_format='npz', **kwargs):
        logging.info('Loading datasets...')
        train_gen = None
        valid_gen = None
        test_gen = None
        if kwargs.get('data_loader'):
            DataLoader = kwargs['data_loader']
        elif data_format == 'npz':
            DataLoader = NpzBlockDataLoader if streaming else NpzDataLoader
        else:
            DataLoader = ParquetBlockDataLoader if streaming else ParquetDataLoader
        self.stage = stage
        if stage in ['both', 'train']:
            train_gen = DataLoader(feature_map, train_data, split='train', batch_size=batch_size, shuffle=shuffle, **kwargs)
            logging.info('Train samples: total/{:d}, blocks/{:d}'.format(train_gen.num_samples, train_gen.num_blocks))
            if valid_data:
                valid_gen = DataLoader(feature_map, valid_data, split='valid', batch_size=batch_size, shuffle=False, **kwargs)
                logging.info('Validation samples: total/{:d}, blocks/{:d}'.format(valid_gen.num_samples, valid_gen.num_blocks))
        if stage in ['both', 'test']:
            if test_data:
                test_gen = DataLoader(feature_map, test_data, split='test', batch_size=batch_size, shuffle=False, **kwargs)
                logging.info('Test samples: total/{:d}, blocks/{:d}'.format(test_gen.num_samples, test_gen.num_blocks))
        self.train_gen, self.valid_gen, self.test_gen = (train_gen, valid_gen, test_gen)

    def make_iterator(self):
        if self.stage == 'train':
            logging.info('Loading train and validation data done.')
            return (self.train_gen, self.valid_gen)
        elif self.stage == 'test':
            logging.info('Loading test data done.')
            return self.test_gen
        else:
            logging.info('Loading data done.')
            return (self.train_gen, self.valid_gen, self.test_gen)

def make_iterator(self):
    if self.stage == 'train':
        logging.info('Loading train and validation data done.')
        return (self.train_gen, self.valid_gen)
    elif self.stage == 'test':
        logging.info('Loading test data done.')
        return self.test_gen
    else:
        logging.info('Loading data done.')
        return (self.train_gen, self.valid_gen, self.test_gen)

class NpzIterDataPipe(IterDataPipe):

    def __init__(self, data_blocks, feature_map):
        self.feature_map = feature_map
        self.data_blocks = data_blocks

    def load_data(self, data_path):
        data_dict = np.load(data_path)
        all_cols = list(self.feature_map.features.keys()) + self.feature_map.labels
        data_arrays = [data_dict[col] for col in all_cols]
        return np.column_stack(data_arrays)

    def read_block(self, data_block):
        darray = self.load_data(data_block)
        for idx in range(darray.shape[0]):
            yield darray[idx, :]

    def __iter__(self):
        worker_info = get_worker_info()
        if worker_info is None:
            block_list = self.data_blocks
        else:
            block_list = [block for idx, block in enumerate(self.data_blocks) if idx % worker_info.num_workers == worker_info.id]
        return chain.from_iterable(map(self.read_block, block_list))

def load_data(self, data_path):
    data_dict = np.load(data_path)
    all_cols = list(self.feature_map.features.keys()) + self.feature_map.labels
    data_arrays = [data_dict[col] for col in all_cols]
    return np.column_stack(data_arrays)

class NpzBlockDataLoader(DataLoader):

    def __init__(self, feature_map, data_path, split='train', batch_size=32, shuffle=False, num_workers=1, buffer_size=100000, **kwargs):
        if not data_path.endswith('npz'):
            data_path = os.path.join(data_path, '*.npz')
        data_blocks = sorted(glob.glob(data_path))
        assert len(data_blocks) > 0, f'invalid data_path: {data_path}'
        self.data_blocks = data_blocks
        self.num_blocks = len(self.data_blocks)
        self.feature_map = feature_map
        self.batch_size = batch_size
        self.num_batches, self.num_samples = self.count_batches_and_samples()
        datapipe = NpzIterDataPipe(self.data_blocks, feature_map)
        if shuffle:
            datapipe = datapipe.shuffle(buffer_size=buffer_size)
        elif split == 'test':
            num_workers = 1
        super().__init__(dataset=datapipe, batch_size=batch_size, num_workers=num_workers, collate_fn=BatchCollator(feature_map))

    def __len__(self):
        return self.num_batches

    def count_batches_and_samples(self):
        num_samples = 0
        for block_path in self.data_blocks:
            block_size = np.load(block_path)[self.feature_map.labels[0]].shape[0]
            num_samples += block_size
        num_batches = int(np.ceil(num_samples / self.batch_size))
        return (num_batches, num_samples)

def __init__(self, feature_map, data_path, split='train', batch_size=32, shuffle=False, num_workers=1, buffer_size=100000, **kwargs):
    if not data_path.endswith('npz'):
        data_path = os.path.join(data_path, '*.npz')
    data_blocks = sorted(glob.glob(data_path))
    assert len(data_blocks) > 0, f'invalid data_path: {data_path}'
    self.data_blocks = data_blocks
    self.num_blocks = len(self.data_blocks)
    self.feature_map = feature_map
    self.batch_size = batch_size
    self.num_batches, self.num_samples = self.count_batches_and_samples()
    datapipe = NpzIterDataPipe(self.data_blocks, feature_map)
    if shuffle:
        datapipe = datapipe.shuffle(buffer_size=buffer_size)
    elif split == 'test':
        num_workers = 1
    super().__init__(dataset=datapipe, batch_size=batch_size, num_workers=num_workers, collate_fn=BatchCollator(feature_map))

def count_batches_and_samples(self):
    num_samples = 0
    for block_path in self.data_blocks:
        block_size = np.load(block_path)[self.feature_map.labels[0]].shape[0]
        num_samples += block_size
    num_batches = int(np.ceil(num_samples / self.batch_size))
    return (num_batches, num_samples)

class BatchCollator(object):

    def __init__(self, feature_map):
        self.feature_map = feature_map

    def __call__(self, batch):
        batch_tensor = default_collate(batch)
        all_cols = list(self.feature_map.features.keys()) + self.feature_map.labels
        batch_dict = dict()
        for col in all_cols:
            batch_dict[col] = batch_tensor[:, self.feature_map.get_column_index(col)]
        return batch_dict

def __call__(self, batch):
    batch_tensor = default_collate(batch)
    all_cols = list(self.feature_map.features.keys()) + self.feature_map.labels
    batch_dict = dict()
    for col in all_cols:
        batch_dict[col] = batch_tensor[:, self.feature_map.get_column_index(col)]
    return batch_dict

class PretrainedEmbedding(nn.Module):

    def __init__(self, feature_name, feature_spec, pretrain_path, vocab_path, embedding_dim, pretrain_dim, pretrain_usage='init', embedding_initializer='partial(nn.init.normal_, std=1e-4)'):
        """
        Fusion pretrained embedding with ID embedding
        :param: fusion_type: init/sum/concat
        """
        super().__init__()
        assert pretrain_usage in ['init', 'sum', 'concat']
        self.pretrain_usage = pretrain_usage
        self.embedding_initializer = get_initializer(embedding_initializer)
        padding_idx = feature_spec.get('padding_idx', None)
        self.oov_idx = feature_spec['oov_idx']
        self.freeze_emb = feature_spec['freeze_emb']
        self.pretrain_embedding = self.load_pretrained_embedding(feature_spec['vocab_size'], pretrain_dim, pretrain_path, vocab_path, feature_name, freeze=self.freeze_emb, padding_idx=padding_idx)
        if pretrain_usage != 'init':
            self.id_embedding = nn.Embedding(feature_spec['vocab_size'], embedding_dim, padding_idx=padding_idx)
        self.proj = None
        if pretrain_usage in ['init', 'sum'] and embedding_dim != pretrain_dim:
            self.proj = nn.Linear(pretrain_dim, embedding_dim, bias=False)
        if pretrain_usage == 'concat':
            self.proj = nn.Linear(pretrain_dim + embedding_dim, embedding_dim, bias=False)

    def init_weights(self):
        if self.pretrain_usage in ['sum', 'concat']:
            nn.init.zeros_(self.id_embedding.weight)
            self.embedding_initializer(self.id_embedding.weight[1:self.oov_idx, :])

    def load_feature_vocab(self, vocab_path, feature_name):
        with io.open(vocab_path, 'r', encoding='utf-8') as fd:
            vocab = json.load(fd)
            vocab_type = type(list(vocab.items())[1][0])
        return (vocab[feature_name], vocab_type)

    def load_pretrained_embedding(self, vocab_size, pretrain_dim, pretrain_path, vocab_path, feature_name, freeze=False, padding_idx=None):
        embedding_layer = nn.Embedding(vocab_size, pretrain_dim, padding_idx=padding_idx)
        if freeze:
            embedding_matrix = np.zeros((vocab_size, pretrain_dim))
        else:
            embedding_matrix = np.random.normal(loc=0, scale=0.0001, size=(vocab_size, pretrain_dim))
            if padding_idx:
                embedding_matrix[padding_idx, :] = np.zeros(pretrain_dim)
        logging.info('Loading pretrained_emb: {}'.format(pretrain_path))
        keys, embeddings = load_pretrain_emb(pretrain_path, keys=['key', 'value'])
        assert embeddings.shape[-1] == pretrain_dim, f'pretrain_dim={pretrain_dim} not correct.'
        vocab, vocab_type = self.load_feature_vocab(vocab_path, feature_name)
        keys = keys.astype(vocab_type)
        for idx, word in enumerate(keys):
            if word in vocab:
                embedding_matrix[vocab[word]] = embeddings[idx]
        embedding_layer.weight = torch.nn.Parameter(torch.from_numpy(embedding_matrix).float())
        if freeze:
            embedding_layer.weight.requires_grad = False
        return embedding_layer

    def forward(self, inputs):
        mask = (inputs <= self.oov_idx).float()
        pretrain_emb = self.pretrain_embedding(inputs)
        if not self.freeze_emb:
            pretrain_emb = pretrain_emb * mask.unsqueeze(-1)
        if self.pretrain_usage == 'init':
            if self.proj is not None:
                feature_emb = self.proj(pretrain_emb)
            else:
                feature_emb = pretrain_emb
        else:
            id_emb = self.id_embedding(inputs)
            id_emb = id_emb * mask.unsqueeze(-1)
            if self.pretrain_usage == 'sum':
                if self.proj is not None:
                    feature_emb = self.proj(pretrain_emb) + id_emb
                else:
                    feature_emb = pretrain_emb + id_emb
            elif self.pretrain_usage == 'concat':
                feature_emb = torch.cat([pretrain_emb, id_emb], dim=-1)
                feature_emb = self.proj(feature_emb)
        return feature_emb

def load_feature_vocab(self, vocab_path, feature_name):
    with io.open(vocab_path, 'r', encoding='utf-8') as fd:
        vocab = json.load(fd)
        vocab_type = type(list(vocab.items())[1][0])
    return (vocab[feature_name], vocab_type)

class FeatureEmbeddingDict(nn.Module):

    def __init__(self, feature_map, embedding_dim, embedding_initializer='partial(nn.init.normal_, std=1e-4)', required_feature_columns=None, not_required_feature_columns=None, use_pretrain=True, use_sharing=True):
        super(FeatureEmbeddingDict, self).__init__()
        self._feature_map = feature_map
        self.required_feature_columns = required_feature_columns
        self.not_required_feature_columns = not_required_feature_columns
        self.use_pretrain = use_pretrain
        self.embedding_initializer = get_initializer(embedding_initializer)
        self.embedding_layers = nn.ModuleDict()
        self.feature_encoders = nn.ModuleDict()
        for feature, feature_spec in self._feature_map.features.items():
            if self.is_required(feature):
                if not (use_pretrain and use_sharing) and embedding_dim == 1:
                    feat_dim = 1
                    if feature_spec['type'] == 'sequence':
                        self.feature_encoders[feature] = layers.MaskedSumPooling()
                else:
                    feat_dim = feature_spec.get('embedding_dim', embedding_dim)
                    if feature_spec.get('feature_encoder', None):
                        self.feature_encoders[feature] = self.get_feature_encoder(feature_spec['feature_encoder'])
                    elif feature_spec['type'] == 'embedding':
                        pretrain_dim = feature_spec.get('pretrain_dim', feat_dim)
                        self.feature_encoders[feature] = nn.Linear(pretrain_dim, feat_dim, bias=False)
                if use_sharing and feature_spec.get('share_embedding') in self.embedding_layers:
                    self.embedding_layers[feature] = self.embedding_layers[feature_spec['share_embedding']]
                    continue
                if feature_spec['type'] == 'numeric':
                    self.embedding_layers[feature] = nn.Linear(1, feat_dim, bias=False)
                elif feature_spec['type'] in ['categorical', 'sequence']:
                    if use_pretrain and 'pretrained_emb' in feature_spec:
                        pretrain_path = os.path.join(feature_map.data_dir, feature_spec['pretrained_emb'])
                        vocab_path = os.path.join(feature_map.data_dir, 'feature_vocab.json')
                        pretrain_dim = feature_spec.get('pretrain_dim', feat_dim)
                        pretrain_usage = feature_spec.get('pretrain_usage', 'init')
                        self.embedding_layers[feature] = PretrainedEmbedding(feature, feature_spec, pretrain_path, vocab_path, feat_dim, pretrain_dim, pretrain_usage, embedding_initializer)
                    else:
                        padding_idx = feature_spec.get('padding_idx', None)
                        self.embedding_layers[feature] = nn.Embedding(feature_spec['vocab_size'], feat_dim, padding_idx=padding_idx)
                elif feature_spec['type'] == 'embedding':
                    self.embedding_layers[feature] = nn.Identity()
        self.init_weights()

    def get_feature_encoder(self, encoder):
        try:
            if type(encoder) == list:
                encoder_list = []
                for enc in encoder:
                    encoder_list.append(eval(enc))
                encoder_layer = nn.Sequential(*encoder_list)
            else:
                encoder_layer = eval(encoder)
            return encoder_layer
        except:
            raise ValueError('feature_encoder={} is not supported.'.format(encoder))

    def init_weights(self):
        for k, v in self.embedding_layers.items():
            if 'share_embedding' in self._feature_map.features[k]:
                continue
            if type(v) == PretrainedEmbedding:
                v.init_weights()
            elif type(v) == nn.Embedding:
                if v.padding_idx is not None:
                    self.embedding_initializer(v.weight[1:, :])
                else:
                    self.embedding_initializer(v.weight)

    def is_required(self, feature):
        """ Check whether feature is required for embedding """
        feature_spec = self._feature_map.features[feature]
        if feature_spec['type'] == 'meta':
            return False
        elif self.required_feature_columns and feature not in self.required_feature_columns:
            return False
        elif self.not_required_feature_columns and feature in self.not_required_feature_columns:
            return False
        else:
            return True

    def dict2tensor(self, embedding_dict, flatten_emb=False, feature_list=[], feature_source=[], feature_type=[]):
        feature_emb_list = []
        for feature, feature_spec in self._feature_map.features.items():
            if feature_list and not_in_whitelist(feature, feature_list):
                continue
            if feature_source and not_in_whitelist(feature_spec['source'], feature_source):
                continue
            if feature_type and not_in_whitelist(feature_spec['type'], feature_type):
                continue
            if feature in embedding_dict:
                feature_emb_list.append(embedding_dict[feature])
        if flatten_emb:
            feature_emb = torch.cat(feature_emb_list, dim=-1)
        else:
            feature_emb = torch.stack(feature_emb_list, dim=1)
        return feature_emb

    def forward(self, inputs, feature_source=[], feature_type=[]):
        feature_emb_dict = OrderedDict()
        for feature in inputs.keys():
            feature_spec = self._feature_map.features[feature]
            if feature_source and not_in_whitelist(feature_spec['source'], feature_source):
                continue
            if feature_type and not_in_whitelist(feature_spec['type'], feature_type):
                continue
            if feature in self.embedding_layers:
                if feature_spec['type'] == 'numeric':
                    inp = inputs[feature].float().view(-1, 1)
                    embeddings = self.embedding_layers[feature](inp)
                elif feature_spec['type'] == 'categorical':
                    inp = inputs[feature].long()
                    embeddings = self.embedding_layers[feature](inp)
                elif feature_spec['type'] == 'sequence':
                    inp = inputs[feature].long()
                    embeddings = self.embedding_layers[feature](inp)
                elif feature_spec['type'] == 'embedding':
                    inp = inputs[feature].float()
                    embeddings = self.embedding_layers[feature](inp)
                else:
                    raise NotImplementedError
                if feature in self.feature_encoders:
                    embeddings = self.feature_encoders[feature](embeddings)
                feature_emb_dict[feature] = embeddings
        return feature_emb_dict

def dict2tensor(self, embedding_dict, flatten_emb=False, feature_list=[], feature_source=[], feature_type=[]):
    feature_emb_list = []
    for feature, feature_spec in self._feature_map.features.items():
        if feature_list and not_in_whitelist(feature, feature_list):
            continue
        if feature_source and not_in_whitelist(feature_spec['source'], feature_source):
            continue
        if feature_type and not_in_whitelist(feature_spec['type'], feature_type):
            continue
        if feature in embedding_dict:
            feature_emb_list.append(embedding_dict[feature])
    if flatten_emb:
        feature_emb = torch.cat(feature_emb_list, dim=-1)
    else:
        feature_emb = torch.stack(feature_emb_list, dim=1)
    return feature_emb

def forward(self, inputs, feature_source=[], feature_type=[]):
    feature_emb_dict = OrderedDict()
    for feature in inputs.keys():
        feature_spec = self._feature_map.features[feature]
        if feature_source and not_in_whitelist(feature_spec['source'], feature_source):
            continue
        if feature_type and not_in_whitelist(feature_spec['type'], feature_type):
            continue
        if feature in self.embedding_layers:
            if feature_spec['type'] == 'numeric':
                inp = inputs[feature].float().view(-1, 1)
                embeddings = self.embedding_layers[feature](inp)
            elif feature_spec['type'] == 'categorical':
                inp = inputs[feature].long()
                embeddings = self.embedding_layers[feature](inp)
            elif feature_spec['type'] == 'sequence':
                inp = inputs[feature].long()
                embeddings = self.embedding_layers[feature](inp)
            elif feature_spec['type'] == 'embedding':
                inp = inputs[feature].float()
                embeddings = self.embedding_layers[feature](inp)
            else:
                raise NotImplementedError
            if feature in self.feature_encoders:
                embeddings = self.feature_encoders[feature](embeddings)
            feature_emb_dict[feature] = embeddings
    return feature_emb_dict

class BaseModel(nn.Module):

    def __init__(self, feature_map, model_id='BaseModel', task='binary_classification', gpu=-1, monitor='AUC', save_best_only=True, monitor_mode='max', early_stop_patience=2, eval_steps=None, embedding_regularizer=None, net_regularizer=None, reduce_lr_on_plateau=True, **kwargs):
        super(BaseModel, self).__init__()
        self.device = get_device(gpu)
        self._monitor = Monitor(kv=monitor)
        self._monitor_mode = monitor_mode
        self._early_stop_patience = early_stop_patience
        self._eval_steps = eval_steps
        self._save_best_only = save_best_only
        self._embedding_regularizer = embedding_regularizer
        self._net_regularizer = net_regularizer
        self._reduce_lr_on_plateau = reduce_lr_on_plateau
        self._verbose = kwargs['verbose']
        self.feature_map = feature_map
        self.output_activation = self.get_output_activation(task)
        self.model_id = model_id
        self.model_dir = os.path.join(kwargs['model_root'], feature_map.dataset_id)
        self.checkpoint = os.path.abspath(os.path.join(self.model_dir, self.model_id + '.model'))
        self.validation_metrics = kwargs['metrics']

    def compile(self, optimizer, loss, lr):
        self.optimizer = get_optimizer(optimizer, self.parameters(), lr)
        self.loss_fn = get_loss(loss)

    def regularization_loss(self):
        reg_term = 0
        if self._embedding_regularizer or self._net_regularizer:
            emb_reg = get_regularizer(self._embedding_regularizer)
            net_reg = get_regularizer(self._net_regularizer)
            emb_params = set()
            for m_name, module in self.named_modules():
                if type(module) == FeatureEmbeddingDict:
                    for p_name, param in module.named_parameters():
                        if param.requires_grad:
                            emb_params.add('.'.join([m_name, p_name]))
                            for emb_p, emb_lambda in emb_reg:
                                reg_term += emb_lambda / emb_p * torch.norm(param, emb_p) ** emb_p
            for name, param in self.named_parameters():
                if param.requires_grad:
                    if name not in emb_params:
                        for net_p, net_lambda in net_reg:
                            reg_term += net_lambda / net_p * torch.norm(param, net_p) ** net_p
        return reg_term

    def add_loss(self, return_dict, y_true):
        loss = self.loss_fn(return_dict['y_pred'], y_true, reduction='mean')
        return loss

    def compute_loss(self, return_dict, y_true):
        loss = self.add_loss(return_dict, y_true) + self.regularization_loss()
        return loss

    def reset_parameters(self):

        def default_reset_params(m):
            if type(m) in [nn.Linear, nn.Conv1d]:
                nn.init.xavier_normal_(m.weight)
                if m.bias is not None:
                    m.bias.data.fill_(0)

        def custom_reset_params(m):
            if hasattr(m, 'init_weights'):
                m.init_weights()
        self.apply(default_reset_params)
        self.apply(custom_reset_params)

    def get_inputs(self, inputs, feature_source=None):
        X_dict = dict()
        for feature in inputs.keys():
            if feature in self.feature_map.labels:
                continue
            spec = self.feature_map.features[feature]
            if spec['type'] == 'meta':
                continue
            if feature_source and not_in_whitelist(spec['source'], feature_source):
                continue
            X_dict[feature] = inputs[feature].to(self.device)
        return X_dict

    def get_labels(self, inputs):
        """ Please override get_labels() when using multiple labels!
        """
        labels = self.feature_map.labels
        y = inputs[labels[0]].to(self.device)
        return y.float().view(-1, 1)

    def get_group_id(self, inputs):
        return inputs[self.feature_map.group_id]

    def model_to_device(self):
        self.to(device=self.device)

    def lr_decay(self, factor=0.1, min_lr=1e-06):
        for param_group in self.optimizer.param_groups:
            reduced_lr = max(param_group['lr'] * factor, min_lr)
            param_group['lr'] = reduced_lr
        return reduced_lr

    def fit(self, data_generator, epochs=1, validation_data=None, max_gradient_norm=10.0, **kwargs):
        self.valid_gen = validation_data
        self._max_gradient_norm = max_gradient_norm
        self._best_metric = np.Inf if self._monitor_mode == 'min' else -np.Inf
        self._stopping_steps = 0
        self._steps_per_epoch = len(data_generator)
        self._stop_training = False
        self._total_steps = 0
        self._batch_index = 0
        self._epoch_index = 0
        if self._eval_steps is None:
            self._eval_steps = self._steps_per_epoch
        logging.info('Start training: {} batches/epoch'.format(self._steps_per_epoch))
        logging.info('************ Epoch=1 start ************')
        for epoch in range(epochs):
            self._epoch_index = epoch
            self.train_epoch(data_generator)
            if self._stop_training:
                break
            else:
                logging.info('************ Epoch={} end ************'.format(self._epoch_index + 1))
        logging.info('Training finished.')
        logging.info('Load best model: {}'.format(self.checkpoint))
        self.load_weights(self.checkpoint)

    def checkpoint_and_earlystop(self, logs, min_delta=1e-06):
        monitor_value = self._monitor.get_value(logs)
        if self._monitor_mode == 'min' and monitor_value > self._best_metric - min_delta or (self._monitor_mode == 'max' and monitor_value < self._best_metric + min_delta):
            self._stopping_steps += 1
            logging.info('Monitor({})={:.6f} STOP!'.format(self._monitor_mode, monitor_value))
            if self._reduce_lr_on_plateau:
                current_lr = self.lr_decay()
                logging.info('Reduce learning rate on plateau: {:.6f}'.format(current_lr))
        else:
            self._stopping_steps = 0
            self._best_metric = monitor_value
            if self._save_best_only:
                logging.info('Save best model: monitor({})={:.6f}'.format(self._monitor_mode, monitor_value))
                self.save_weights(self.checkpoint)
        if self._stopping_steps >= self._early_stop_patience:
            self._stop_training = True
            logging.info('********* Epoch={} early stop *********'.format(self._epoch_index + 1))
        if not self._save_best_only:
            self.save_weights(self.checkpoint)

    def eval_step(self):
        logging.info('Evaluation @epoch {} - batch {}: '.format(self._epoch_index + 1, self._batch_index + 1))
        val_logs = self.evaluate(self.valid_gen, metrics=self._monitor.get_metrics())
        self.checkpoint_and_earlystop(val_logs)
        self.train()

    def train_step(self, batch_data):
        self.optimizer.zero_grad()
        return_dict = self.forward(batch_data)
        y_true = self.get_labels(batch_data)
        loss = self.compute_loss(return_dict, y_true)
        loss.backward()
        nn.utils.clip_grad_norm_(self.parameters(), self._max_gradient_norm)
        self.optimizer.step()
        return loss

    def train_epoch(self, data_generator):
        self._batch_index = 0
        train_loss = 0
        self.train()
        if self._verbose == 0:
            batch_iterator = data_generator
        else:
            batch_iterator = tqdm(data_generator, disable=False, file=sys.stdout)
        for batch_index, batch_data in enumerate(batch_iterator):
            self._batch_index = batch_index
            self._total_steps += 1
            loss = self.train_step(batch_data)
            train_loss += loss.item()
            if self._total_steps % self._eval_steps == 0:
                logging.info('Train loss: {:.6f}'.format(train_loss / self._eval_steps))
                train_loss = 0
                self.eval_step()
            if self._stop_training:
                break

    def evaluate(self, data_generator, metrics=None):
        self.eval()
        with torch.no_grad():
            y_pred = []
            y_true = []
            group_id = []
            if self._verbose > 0:
                data_generator = tqdm(data_generator, disable=False, file=sys.stdout)
            for batch_data in data_generator:
                return_dict = self.forward(batch_data)
                y_pred.extend(return_dict['y_pred'].data.cpu().numpy().reshape(-1))
                y_true.extend(self.get_labels(batch_data).data.cpu().numpy().reshape(-1))
                if self.feature_map.group_id is not None:
                    group_id.extend(self.get_group_id(batch_data).numpy().reshape(-1))
            y_pred = np.array(y_pred, np.float64)
            y_true = np.array(y_true, np.float64)
            group_id = np.array(group_id) if len(group_id) > 0 else None
            if metrics is not None:
                val_logs = self.evaluate_metrics(y_true, y_pred, metrics, group_id)
            else:
                val_logs = self.evaluate_metrics(y_true, y_pred, self.validation_metrics, group_id)
            logging.info('[Metrics] ' + ' - '.join(('{}: {:.6f}'.format(k, v) for k, v in val_logs.items())))
            return val_logs

    def predict(self, data_generator):
        self.eval()
        with torch.no_grad():
            y_pred = []
            if self._verbose > 0:
                data_generator = tqdm(data_generator, disable=False, file=sys.stdout)
            for batch_data in data_generator:
                return_dict = self.forward(batch_data)
                y_pred.extend(return_dict['y_pred'].data.cpu().numpy().reshape(-1))
            y_pred = np.array(y_pred, np.float64)
            return y_pred

    def evaluate_metrics(self, y_true, y_pred, metrics, group_id=None):
        return evaluate_metrics(y_true, y_pred, metrics, group_id)

    def save_weights(self, checkpoint):
        torch.save(self.state_dict(), checkpoint)

    def load_weights(self, checkpoint):
        self.to(self.device)
        state_dict = torch.load(checkpoint, map_location='cpu')
        self.load_state_dict(state_dict)

    def get_output_activation(self, task):
        if task == 'binary_classification':
            return nn.Sigmoid()
        elif task == 'regression':
            return nn.Identity()
        else:
            raise NotImplementedError('task={} is not supported.'.format(task))

    def count_parameters(self, count_embedding=True):
        total_params = 0
        for name, param in self.named_parameters():
            if not count_embedding and 'embedding' in name:
                continue
            if param.requires_grad:
                total_params += param.numel()
        logging.info('Total number of parameters: {}.'.format(total_params))

def get_inputs(self, inputs, feature_source=None):
    X_dict = dict()
    for feature in inputs.keys():
        if feature in self.feature_map.labels:
            continue
        spec = self.feature_map.features[feature]
        if spec['type'] == 'meta':
            continue
        if feature_source and not_in_whitelist(spec['source'], feature_source):
            continue
        X_dict[feature] = inputs[feature].to(self.device)
    return X_dict

def train_epoch(self, data_generator):
    self._batch_index = 0
    train_loss = 0
    self.train()
    if self._verbose == 0:
        batch_iterator = data_generator
    else:
        batch_iterator = tqdm(data_generator, disable=False, file=sys.stdout)
    for batch_index, batch_data in enumerate(batch_iterator):
        self._batch_index = batch_index
        self._total_steps += 1
        loss = self.train_step(batch_data)
        train_loss += loss.item()
        if self._total_steps % self._eval_steps == 0:
            logging.info('Train loss: {:.6f}'.format(train_loss / self._eval_steps))
            train_loss = 0
            self.eval_step()
        if self._stop_training:
            break

def evaluate(self, data_generator, metrics=None):
    self.eval()
    with torch.no_grad():
        y_pred = []
        y_true = []
        group_id = []
        if self._verbose > 0:
            data_generator = tqdm(data_generator, disable=False, file=sys.stdout)
        for batch_data in data_generator:
            return_dict = self.forward(batch_data)
            y_pred.extend(return_dict['y_pred'].data.cpu().numpy().reshape(-1))
            y_true.extend(self.get_labels(batch_data).data.cpu().numpy().reshape(-1))
            if self.feature_map.group_id is not None:
                group_id.extend(self.get_group_id(batch_data).numpy().reshape(-1))
        y_pred = np.array(y_pred, np.float64)
        y_true = np.array(y_true, np.float64)
        group_id = np.array(group_id) if len(group_id) > 0 else None
        if metrics is not None:
            val_logs = self.evaluate_metrics(y_true, y_pred, metrics, group_id)
        else:
            val_logs = self.evaluate_metrics(y_true, y_pred, self.validation_metrics, group_id)
        logging.info('[Metrics] ' + ' - '.join(('{}: {:.6f}'.format(k, v) for k, v in val_logs.items())))
        return val_logs

def predict(self, data_generator):
    self.eval()
    with torch.no_grad():
        y_pred = []
        if self._verbose > 0:
            data_generator = tqdm(data_generator, disable=False, file=sys.stdout)
        for batch_data in data_generator:
            return_dict = self.forward(batch_data)
            y_pred.extend(return_dict['y_pred'].data.cpu().numpy().reshape(-1))
        y_pred = np.array(y_pred, np.float64)
        return y_pred

def evaluate_metrics(self, y_true, y_pred, metrics, group_id=None):
    return evaluate_metrics(y_true, y_pred, metrics, group_id)

def save_weights(self, checkpoint):
    torch.save(self.state_dict(), checkpoint)

def load_weights(self, checkpoint):
    self.to(self.device)
    state_dict = torch.load(checkpoint, map_location='cpu')
    self.load_state_dict(state_dict)

class MultiTaskModel(BaseModel):

    def __init__(self, feature_map, model_id='MultiTaskModel', task=['binary_classification'], num_tasks=1, loss_weight='EQ', gpu=-1, monitor='AUC', save_best_only=True, monitor_mode='max', early_stop_patience=2, eval_steps=None, embedding_regularizer=None, net_regularizer=None, reduce_lr_on_plateau=True, **kwargs):
        super(MultiTaskModel, self).__init__(feature_map=feature_map, model_id=model_id, task='binary_classification', gpu=gpu, loss_weight=loss_weight, monitor=monitor, save_best_only=save_best_only, monitor_mode=monitor_mode, early_stop_patience=early_stop_patience, eval_steps=eval_steps, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, reduce_lr_on_plateau=reduce_lr_on_plateau, **kwargs)
        self.device = get_device(gpu)
        self.num_tasks = num_tasks
        self.loss_weight = loss_weight
        if isinstance(task, list):
            assert len(task) == num_tasks, 'the number of tasks must equal the length of "task"'
            self.output_activation = nn.ModuleList([self.get_output_activation(str(t)) for t in task])
        else:
            self.output_activation = nn.ModuleList([self.get_output_activation(task) for _ in range(num_tasks)])

    def compile(self, optimizer, loss, lr):
        self.optimizer = get_optimizer(optimizer, self.parameters(), lr)
        if isinstance(loss, list):
            self.loss_fn = [get_loss(l) for l in loss]
        else:
            self.loss_fn = [get_loss(loss) for _ in range(self.num_tasks)]

    def get_labels(self, inputs):
        """ Override get_labels() to use multiple labels """
        labels = self.feature_map.labels
        y = [inputs[labels[i]].to(self.device).float().view(-1, 1) for i in range(len(labels))]
        return y

    def regularization_loss(self):
        reg_loss = 0
        if self._embedding_regularizer or self._net_regularizer:
            emb_reg = get_regularizer(self._embedding_regularizer)
            net_reg = get_regularizer(self._net_regularizer)
            for _, module in self.named_modules():
                for p_name, param in module.named_parameters():
                    if param.requires_grad:
                        if p_name in ['weight', 'bias']:
                            if type(module) == nn.Embedding:
                                if self._embedding_regularizer:
                                    for emb_p, emb_lambda in emb_reg:
                                        reg_loss += emb_lambda / emb_p * torch.norm(param, emb_p) ** emb_p
                            elif self._net_regularizer:
                                for net_p, net_lambda in net_reg:
                                    reg_loss += net_lambda / net_p * torch.norm(param, net_p) ** net_p
        return reg_loss

    def add_loss(self, return_dict, y_true):
        labels = self.feature_map.labels
        loss = [self.loss_fn[i](return_dict['{}_pred'.format(labels[i])], y_true[i], reduction='mean') for i in range(len(labels))]
        if self.loss_weight == 'EQ':
            loss = torch.sum(torch.stack(loss))
        return loss

    def compute_loss(self, return_dict, y_true):
        loss = self.add_loss(return_dict, y_true) + self.regularization_loss()
        return loss

    def evaluate(self, data_generator, metrics=None):
        self.eval()
        with torch.no_grad():
            y_pred_all = defaultdict(list)
            y_true_all = defaultdict(list)
            labels = self.feature_map.labels
            group_id = []
            if self._verbose > 0:
                data_generator = tqdm(data_generator, disable=False, file=sys.stdout)
            for batch_data in data_generator:
                return_dict = self.forward(batch_data)
                batch_y_true = self.get_labels(batch_data)
                for i in range(len(labels)):
                    y_pred_all[labels[i]].extend(return_dict['{}_pred'.format(labels[i])].data.cpu().numpy().reshape(-1))
                    y_true_all[labels[i]].extend(batch_y_true[i].data.cpu().numpy().reshape(-1))
                if self.feature_map.group_id is not None:
                    group_id.extend(self.get_group_id(batch_data).numpy().reshape(-1))
            all_val_logs = {}
            mean_val_logs = defaultdict(list)
            group_id = np.array(group_id) if len(group_id) > 0 else None
            for i in range(len(labels)):
                y_pred = np.array(y_pred_all[labels[i]], np.float64)
                y_true = np.array(y_true_all[labels[i]], np.float64)
                if metrics is not None:
                    val_logs = self.evaluate_metrics(y_true, y_pred, metrics, group_id)
                else:
                    val_logs = self.evaluate_metrics(y_true, y_pred, self.validation_metrics, group_id)
                logging.info('[Task: {}][Metrics] '.format(labels[i]) + ' - '.join(('{}: {:.6f}'.format(k, v) for k, v in val_logs.items())))
                for k, v in val_logs.items():
                    all_val_logs['{}_{}'.format(labels[i], k)] = v
                    mean_val_logs[k].append(v)
            for k, v in mean_val_logs.items():
                mean_val_logs[k] = np.mean(v)
            all_val_logs.update(mean_val_logs)
            return all_val_logs

    def predict(self, data_generator):
        self.eval()
        with torch.no_grad():
            y_pred_all = defaultdict(list)
            labels = self.feature_map.labels
            if self._verbose > 0:
                data_generator = tqdm(data_generator, disable=False, file=sys.stdout)
            for batch_data in data_generator:
                return_dict = self.forward(batch_data)
                for i in range(len(labels)):
                    y_pred_all[labels[i]].extend(return_dict['{}_pred'.format(labels[i])].data.cpu().numpy().reshape(-1))
        return y_pred_all

def evaluate(self, data_generator, metrics=None):
    self.eval()
    with torch.no_grad():
        y_pred_all = defaultdict(list)
        y_true_all = defaultdict(list)
        labels = self.feature_map.labels
        group_id = []
        if self._verbose > 0:
            data_generator = tqdm(data_generator, disable=False, file=sys.stdout)
        for batch_data in data_generator:
            return_dict = self.forward(batch_data)
            batch_y_true = self.get_labels(batch_data)
            for i in range(len(labels)):
                y_pred_all[labels[i]].extend(return_dict['{}_pred'.format(labels[i])].data.cpu().numpy().reshape(-1))
                y_true_all[labels[i]].extend(batch_y_true[i].data.cpu().numpy().reshape(-1))
            if self.feature_map.group_id is not None:
                group_id.extend(self.get_group_id(batch_data).numpy().reshape(-1))
        all_val_logs = {}
        mean_val_logs = defaultdict(list)
        group_id = np.array(group_id) if len(group_id) > 0 else None
        for i in range(len(labels)):
            y_pred = np.array(y_pred_all[labels[i]], np.float64)
            y_true = np.array(y_true_all[labels[i]], np.float64)
            if metrics is not None:
                val_logs = self.evaluate_metrics(y_true, y_pred, metrics, group_id)
            else:
                val_logs = self.evaluate_metrics(y_true, y_pred, self.validation_metrics, group_id)
            logging.info('[Task: {}][Metrics] '.format(labels[i]) + ' - '.join(('{}: {:.6f}'.format(k, v) for k, v in val_logs.items())))
            for k, v in val_logs.items():
                all_val_logs['{}_{}'.format(labels[i], k)] = v
                mean_val_logs[k].append(v)
        for k, v in mean_val_logs.items():
            mean_val_logs[k] = np.mean(v)
        all_val_logs.update(mean_val_logs)
        return all_val_logs

def predict(self, data_generator):
    self.eval()
    with torch.no_grad():
        y_pred_all = defaultdict(list)
        labels = self.feature_map.labels
        if self._verbose > 0:
            data_generator = tqdm(data_generator, disable=False, file=sys.stdout)
        for batch_data in data_generator:
            return_dict = self.forward(batch_data)
            for i in range(len(labels)):
                y_pred_all[labels[i]].extend(return_dict['{}_pred'.format(labels[i])].data.cpu().numpy().reshape(-1))
    return y_pred_all

