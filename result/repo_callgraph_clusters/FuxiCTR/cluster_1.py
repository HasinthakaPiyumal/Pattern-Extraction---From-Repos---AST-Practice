# Cluster 1

class SerialMaskNet(nn.Module):

    def __init__(self, input_dim, output_dim=None, output_activation=None, hidden_units=[], hidden_activations='ReLU', reduction_ratio=1, dropout_rates=0, layer_norm=True):
        super(SerialMaskNet, self).__init__()
        if not isinstance(dropout_rates, list):
            dropout_rates = [dropout_rates] * len(hidden_units)
        if not isinstance(hidden_activations, list):
            hidden_activations = [hidden_activations] * len(hidden_units)
        self.hidden_units = [input_dim] + hidden_units
        self.mask_blocks = nn.ModuleList()
        for idx in range(len(self.hidden_units) - 1):
            self.mask_blocks.append(MaskBlock(input_dim, self.hidden_units[idx], self.hidden_units[idx + 1], hidden_activations[idx], reduction_ratio, dropout_rates[idx], layer_norm))
        fc_layers = []
        if output_dim is not None:
            fc_layers.append(nn.Linear(self.hidden_units[-1], output_dim))
        if output_activation is not None:
            fc_layers.append(get_activation(output_activation))
        self.fc = None
        if len(fc_layers) > 0:
            self.fc = nn.Sequential(*fc_layers)

    def forward(self, V_emb, V_hidden):
        v_out = V_hidden
        for idx in range(len(self.hidden_units) - 1):
            v_out = self.mask_blocks[idx](V_emb, v_out)
        if self.fc is not None:
            v_out = self.fc(v_out)
        return v_out

def forward(self, V_emb, V_hidden):
    v_out = V_hidden
    for idx in range(len(self.hidden_units) - 1):
        v_out = self.mask_blocks[idx](V_emb, v_out)
    if self.fc is not None:
        v_out = self.fc(v_out)
    return v_out

class FiGNN_Layer(nn.Module):

    def __init__(self, num_fields, embedding_dim, gnn_layers=3, reuse_graph_layer=False, use_gru=True, use_residual=True):
        super(FiGNN_Layer, self).__init__()
        self.num_fields = num_fields
        self.embedding_dim = embedding_dim
        self.gnn_layers = gnn_layers
        self.use_residual = use_residual
        self.reuse_graph_layer = reuse_graph_layer
        if reuse_graph_layer:
            self.gnn = GraphLayer(num_fields, embedding_dim)
        else:
            self.gnn = nn.ModuleList([GraphLayer(num_fields, embedding_dim) for _ in range(gnn_layers)])
        self.gru = nn.GRUCell(embedding_dim, embedding_dim) if use_gru else None
        self.src_nodes, self.dst_nodes = zip(*list(product(range(num_fields), repeat=2)))
        self.leaky_relu = nn.LeakyReLU(negative_slope=0.01)
        self.W_attn = nn.Linear(embedding_dim * 2, 1, bias=False)

    def build_graph_with_attention(self, feature_emb):
        src_emb = feature_emb[:, self.src_nodes, :]
        dst_emb = feature_emb[:, self.dst_nodes, :]
        concat_emb = torch.cat([src_emb, dst_emb], dim=-1)
        alpha = self.leaky_relu(self.W_attn(concat_emb))
        alpha = alpha.view(-1, self.num_fields, self.num_fields)
        mask = torch.eye(self.num_fields).to(feature_emb.device)
        alpha = alpha.masked_fill(mask.bool(), float('-inf'))
        graph = F.softmax(alpha, dim=-1)
        return graph

    def forward(self, feature_emb):
        g = self.build_graph_with_attention(feature_emb)
        h = feature_emb
        for i in range(self.gnn_layers):
            if self.reuse_graph_layer:
                a = self.gnn(g, h)
            else:
                a = self.gnn[i](g, h)
            if self.gru is not None:
                a = a.view(-1, self.embedding_dim)
                h = h.view(-1, self.embedding_dim)
                h = self.gru(a, h)
                h = h.view(-1, self.num_fields, self.embedding_dim)
            else:
                h = a + h
            if self.use_residual:
                h += feature_emb
        return h

def __init__(self, num_fields, embedding_dim, gnn_layers=3, reuse_graph_layer=False, use_gru=True, use_residual=True):
    super(FiGNN_Layer, self).__init__()
    self.num_fields = num_fields
    self.embedding_dim = embedding_dim
    self.gnn_layers = gnn_layers
    self.use_residual = use_residual
    self.reuse_graph_layer = reuse_graph_layer
    if reuse_graph_layer:
        self.gnn = GraphLayer(num_fields, embedding_dim)
    else:
        self.gnn = nn.ModuleList([GraphLayer(num_fields, embedding_dim) for _ in range(gnn_layers)])
    self.gru = nn.GRUCell(embedding_dim, embedding_dim) if use_gru else None
    self.src_nodes, self.dst_nodes = zip(*list(product(range(num_fields), repeat=2)))
    self.leaky_relu = nn.LeakyReLU(negative_slope=0.01)
    self.W_attn = nn.Linear(embedding_dim * 2, 1, bias=False)

def forward(self, feature_emb):
    g = self.build_graph_with_attention(feature_emb)
    h = feature_emb
    for i in range(self.gnn_layers):
        if self.reuse_graph_layer:
            a = self.gnn(g, h)
        else:
            a = self.gnn[i](g, h)
        if self.gru is not None:
            a = a.view(-1, self.embedding_dim)
            h = h.view(-1, self.embedding_dim)
            h = self.gru(a, h)
            h = h.view(-1, self.num_fields, self.embedding_dim)
        else:
            h = a + h
        if self.use_residual:
            h += feature_emb
    return h

class FinalNet(BaseModel):

    def __init__(self, feature_map, model_id='FinalNet', gpu=-1, learning_rate=0.001, embedding_dim=10, block_type='2B', batch_norm=True, use_feature_gating=False, block1_hidden_units=[64, 64, 64], block1_hidden_activations=None, block1_dropout=0, block2_hidden_units=[64, 64, 64], block2_hidden_activations=None, block2_dropout=0, residual_type='concat', embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(FinalNet, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        assert block_type in ['1B', '2B'], 'block_type={} not supported.'.format(block_type)
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        num_fields = feature_map.num_fields
        self.use_feature_gating = use_feature_gating
        if use_feature_gating:
            self.feature_gating = FeatureGating(num_fields, gate_residual='concat')
            gate_out_dim = embedding_dim * num_fields * 2
        self.block_type = block_type
        self.block1 = FinalBlock(input_dim=gate_out_dim if use_feature_gating else embedding_dim * num_fields, hidden_units=block1_hidden_units, hidden_activations=block1_hidden_activations, dropout_rates=block1_dropout, batch_norm=batch_norm, residual_type=residual_type)
        self.fc1 = nn.Linear(block1_hidden_units[-1], 1)
        if block_type == '2B':
            self.block2 = FinalBlock(input_dim=embedding_dim * num_fields, hidden_units=block2_hidden_units, hidden_activations=block2_hidden_activations, dropout_rates=block2_dropout, batch_norm=batch_norm, residual_type=residual_type)
            self.fc2 = nn.Linear(block2_hidden_units[-1], 1)
        self.compile(kwargs['optimizer'], loss=kwargs['loss'], lr=learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        X = self.get_inputs(inputs)
        feature_emb = self.embedding_layer(X)
        y_pred, y1, y2 = (None, None, None)
        if self.block_type == '1B':
            y_pred = self.forward1(feature_emb)
        elif self.block_type == '2B':
            y1 = self.forward1(feature_emb)
            y2 = self.forward2(feature_emb)
            y_pred = 0.5 * (y1 + y2)
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred, 'y1': y1, 'y2': y2}
        return return_dict

    def forward1(self, X):
        if self.use_feature_gating:
            X = self.feature_gating(X)
        block1_out = self.block1(X.flatten(start_dim=1))
        y_pred = self.fc1(block1_out)
        return y_pred

    def forward2(self, X):
        block2_out = self.block2(X.flatten(start_dim=1))
        y_pred = self.fc2(block2_out)
        return y_pred

    def add_loss(self, return_dict, y_true):
        loss = self.loss_fn(return_dict['y_pred'], y_true, reduction='mean')
        if self.block_type == '2B':
            y1 = self.output_activation(return_dict['y1'])
            y2 = self.output_activation(return_dict['y2'])
            loss1 = self.loss_fn(y1, return_dict['y_pred'].detach(), reduction='mean')
            loss2 = self.loss_fn(y2, return_dict['y_pred'].detach(), reduction='mean')
            loss = loss + loss1 + loss2
        return loss

def add_loss(self, return_dict, y_true):
    loss = self.loss_fn(return_dict['y_pred'], y_true, reduction='mean')
    if self.block_type == '2B':
        y1 = self.output_activation(return_dict['y1'])
        y2 = self.output_activation(return_dict['y2'])
        loss1 = self.loss_fn(y1, return_dict['y_pred'].detach(), reduction='mean')
        loss2 = self.loss_fn(y2, return_dict['y_pred'].detach(), reduction='mean')
        loss = loss + loss1 + loss2
    return loss

class FinalBlock(nn.Module):

    def __init__(self, input_dim, hidden_units=[], hidden_activations=None, dropout_rates=[], batch_norm=True, residual_type='sum'):
        super(FinalBlock, self).__init__()
        if type(dropout_rates) != list:
            dropout_rates = [dropout_rates] * len(hidden_units)
        if type(hidden_activations) != list:
            hidden_activations = [hidden_activations] * len(hidden_units)
        self.layer = nn.ModuleList()
        self.norm = nn.ModuleList()
        self.dropout = nn.ModuleList()
        self.activation = nn.ModuleList()
        hidden_units = [input_dim] + hidden_units
        for idx in range(len(hidden_units) - 1):
            self.layer.append(FactorizedInteraction(hidden_units[idx], hidden_units[idx + 1], residual_type=residual_type))
            if batch_norm:
                self.norm.append(nn.BatchNorm1d(hidden_units[idx + 1]))
            if dropout_rates[idx] > 0:
                self.dropout.append(nn.Dropout(dropout_rates[idx]))
            self.activation.append(get_activation(hidden_activations[idx]))

    def forward(self, X):
        X_i = X
        for i in range(len(self.layer)):
            X_i = self.layer[i](X_i)
            if len(self.norm) > i:
                X_i = self.norm[i](X_i)
            if self.activation[i] is not None:
                X_i = self.activation[i](X_i)
            if len(self.dropout) > i:
                X_i = self.dropout[i](X_i)
        return X_i

def forward(self, X):
    X_i = X
    for i in range(len(self.layer)):
        X_i = self.layer[i](X_i)
        if len(self.norm) > i:
            X_i = self.norm[i](X_i)
        if self.activation[i] is not None:
            X_i = self.activation[i](X_i)
        if len(self.dropout) > i:
            X_i = self.dropout[i](X_i)
    return X_i

class DMIN(BaseModel):
    """ Implementation of DMIN model based on the reference code:
        https://github.com/mengxiaozhibo/DMIN
    """

    def __init__(self, feature_map, model_id='DMIN', gpu=-1, learning_rate=0.001, embedding_dim=10, dnn_hidden_units=[512, 128, 64], dnn_activations='Dice', aux_hidden_units=[100, 50], aux_activation='ReLU', net_dropout=0, target_field=('item_id', 'cate_id'), sequence_field=('click_history', 'cate_history'), neg_seq_field=('neg_click_history', 'neg_cate_history'), num_heads=4, enable_sum_pooling=False, attention_hidden_units=[80, 40], attention_activation='ReLU', attention_dropout=0, use_pos_emb=True, pos_emb_dim=8, use_behavior_refiner=True, aux_loss_lambda=0, batch_norm=True, bn_only_once=False, layer_norm=True, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(DMIN, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        if target_field and (not isinstance(target_field, list)):
            target_field = [target_field]
        self.target_field = target_field
        if sequence_field and (not isinstance(sequence_field, list)):
            sequence_field = [sequence_field]
        self.sequence_field = sequence_field
        if neg_seq_field and (not isinstance(neg_seq_field, list)):
            neg_seq_field = [neg_seq_field]
        self.neg_seq_field = neg_seq_field
        assert len(target_field) == len(sequence_field)
        if neg_seq_field:
            assert len(neg_seq_field) == len(sequence_field)
        self.aux_loss_lambda = aux_loss_lambda
        self.feature_map = feature_map
        self.embedding_dim = embedding_dim
        self.num_heads = num_heads
        self.enable_sum_pooling = enable_sum_pooling
        self.embedding_layer = FeatureEmbeddingDict(feature_map, embedding_dim)
        self.sum_pooling = MaskedSumPooling()
        self.behavior_refiner = nn.ModuleList() if use_behavior_refiner else None
        self.multi_interest_extractor = nn.ModuleList()
        self.aux_net = nn.ModuleList()
        self.model_dims = []
        feature_dim = feature_map.sum_emb_out_dim()
        for i in range(len(self.target_field)):
            model_dim = embedding_dim * len(list(flatten([self.target_field[i]])))
            max_seq_len = feature_map.features[list(flatten([self.sequence_field[i]]))[0]]['max_len']
            feature_dim += model_dim * (num_heads - 1)
            if self.enable_sum_pooling:
                feature_dim += model_dim * 2
            if use_behavior_refiner:
                self.behavior_refiner.append(BehaviorRefinerLayer(model_dim, ffn_dim=model_dim * 2, num_heads=num_heads, attn_dropout=attention_dropout, net_dropout=net_dropout, layer_norm=layer_norm))
            self.multi_interest_extractor.append(MultiInterestExtractorLayer(model_dim, ffn_dim=model_dim * 2, num_heads=num_heads, attn_dropout=attention_dropout, net_dropout=net_dropout, layer_norm=layer_norm, attn_hidden_units=attention_hidden_units, attn_activation=attention_activation, use_pos_emb=use_pos_emb, pos_emb_dim=pos_emb_dim, max_seq_len=max_seq_len))
            if self.aux_loss_lambda > 0:
                self.model_dims.append(model_dim)
                self.aux_net.append(MLP_Block(input_dim=model_dim * 2, output_dim=1, hidden_units=aux_hidden_units, hidden_activations=aux_activation, output_activation='Sigmoid', dropout_rates=net_dropout, batch_norm=batch_norm, bn_only_once=bn_only_once))
        if self.neg_seq_field is not None:
            feature_dim -= embedding_dim * len(set(flatten([self.neg_seq_field])))
        self.dnn = MLP_Block(input_dim=feature_dim, output_dim=1, hidden_units=dnn_hidden_units, hidden_activations=dnn_activations, output_activation=self.output_activation, dropout_rates=net_dropout, batch_norm=batch_norm, bn_only_once=bn_only_once)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        X = self.get_inputs(inputs)
        feature_emb_dict = self.embedding_layer(X)
        concat_emb = []
        refined_sequence_list = []
        sequence_emb_list = []
        neg_emb_list = []
        pad_mask_list = []
        for i in range(len(self.target_field)):
            target_emb = self.get_embedding(self.target_field[i], feature_emb_dict)
            sequence_emb = self.get_embedding(self.sequence_field[i], feature_emb_dict)
            neg_emb = self.get_embedding(self.neg_seq_field[i], feature_emb_dict) if self.aux_loss_lambda > 0 else None
            seq_field = list(flatten([self.sequence_field[i]]))[0]
            pad_mask, attn_mask = self.get_mask(X[seq_field])
            if self.behavior_refiner is not None:
                refined_sequence = self.behavior_refiner[i](sequence_emb, attn_mask=attn_mask)
            else:
                refined_sequence = sequence_emb
            interests = self.multi_interest_extractor[i](refined_sequence, target_emb, attn_mask=attn_mask, pad_mask=pad_mask)
            concat_emb += interests
            if self.enable_sum_pooling:
                sum_pool_emb = self.sum_pooling(sequence_emb)
                concat_emb += [sum_pool_emb, target_emb * sum_pool_emb]
            refined_sequence_list.append(refined_sequence)
            sequence_emb_list.append(sequence_emb)
            neg_emb_list.append(neg_emb)
            pad_mask_list.append(pad_mask)
        for feature, emb in feature_emb_dict.items():
            if emb.ndim == 2 and feature not in flatten([self.neg_seq_field]):
                concat_emb.append(emb)
        y_pred = self.dnn(torch.cat(concat_emb, dim=-1))
        return_dict = {'y_pred': y_pred, 'head_emb': refined_sequence_list, 'pos_emb': sequence_emb_list, 'neg_emb': neg_emb_list, 'pad_mask': pad_mask_list}
        return return_dict

    def get_mask(self, x):
        """ 
        Returns:
            padding_mask: 0 for masked positions
            attn_mask: 0 for masked positions
        """
        padding_mask = x == 0
        seq_len = padding_mask.size(1)
        attn_mask = padding_mask.unsqueeze(1).repeat(1, seq_len, 1)
        diag_zeros = ~torch.eye(seq_len, device=x.device).bool().unsqueeze(0).expand_as(attn_mask)
        attn_mask = attn_mask & diag_zeros
        causal_mask = torch.triu(torch.ones(seq_len, seq_len, device=x.device), 1).bool().unsqueeze(0).expand_as(attn_mask)
        attn_mask = attn_mask | causal_mask
        attn_mask = attn_mask.unsqueeze(1).repeat(1, self.num_heads, 1, 1).flatten(end_dim=1)
        padding_mask, attn_mask = (~padding_mask, ~attn_mask)
        return (padding_mask, attn_mask)

    def add_loss(self, return_dict, y_true):
        loss = self.loss_fn(return_dict['y_pred'], y_true, reduction='mean')
        if self.aux_loss_lambda > 0:
            for i in range(len(self.target_field)):
                head_emb, pos_emb, neg_emb, pad_mask = (return_dict['head_emb'][i], return_dict['pos_emb'][i], return_dict['neg_emb'][i], return_dict['pad_mask'][i])
                pos_prob = self.aux_net[i](torch.cat([head_emb[:, :-1, :], pos_emb[:, 1:, :]], dim=-1).view(-1, self.model_dim * 2))
                neg_prob = self.aux_net[i](torch.cat([head_emb[:, :-1, :], neg_emb[:, 1:, :]], dim=-1).view(-1, self.model_dim * 2))
                aux_prob = torch.cat([pos_prob, neg_prob], dim=0).view(-1, 1)
                aux_label = torch.cat([torch.ones_like(pos_prob, device=aux_prob.device), torch.zeros_like(neg_prob, device=aux_prob.device)], dim=0).view(-1, 1)
                aux_loss = F.binary_cross_entropy(aux_prob, aux_label, reduction='none')
                pad_mask = pad_mask[:, 1:].view(-1, 1)
                aux_loss = torch.sum(aux_loss * pad_mask, dim=-1) / (torch.sum(pad_mask, dim=-1) + 1e-09)
                loss += self.aux_loss_lambda * aux_loss
        return loss

    def get_embedding(self, field, feature_emb_dict):
        if type(field) == tuple:
            emb_list = [feature_emb_dict[f] for f in field]
            return torch.cat(emb_list, dim=-1)
        else:
            return feature_emb_dict[field]

def add_loss(self, return_dict, y_true):
    loss = self.loss_fn(return_dict['y_pred'], y_true, reduction='mean')
    if self.aux_loss_lambda > 0:
        for i in range(len(self.target_field)):
            head_emb, pos_emb, neg_emb, pad_mask = (return_dict['head_emb'][i], return_dict['pos_emb'][i], return_dict['neg_emb'][i], return_dict['pad_mask'][i])
            pos_prob = self.aux_net[i](torch.cat([head_emb[:, :-1, :], pos_emb[:, 1:, :]], dim=-1).view(-1, self.model_dim * 2))
            neg_prob = self.aux_net[i](torch.cat([head_emb[:, :-1, :], neg_emb[:, 1:, :]], dim=-1).view(-1, self.model_dim * 2))
            aux_prob = torch.cat([pos_prob, neg_prob], dim=0).view(-1, 1)
            aux_label = torch.cat([torch.ones_like(pos_prob, device=aux_prob.device), torch.zeros_like(neg_prob, device=aux_prob.device)], dim=0).view(-1, 1)
            aux_loss = F.binary_cross_entropy(aux_prob, aux_label, reduction='none')
            pad_mask = pad_mask[:, 1:].view(-1, 1)
            aux_loss = torch.sum(aux_loss * pad_mask, dim=-1) / (torch.sum(pad_mask, dim=-1) + 1e-09)
            loss += self.aux_loss_lambda * aux_loss
    return loss

class FFM(BaseModel):

    def __init__(self, feature_map, model_id='FFM', gpu=-1, task='binary_classification', learning_rate=0.001, embedding_dim=2, regularizer=None, **kwargs):
        super(FFM, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=regularizer, net_regularizer=regularizer, **kwargs)
        self.num_fields = feature_map.num_fields
        self.lr_layer = LogisticRegression(feature_map)
        self.embedding_layers = nn.ModuleList([FeatureEmbedding(feature_map, embedding_dim) for x in range(self.num_fields - 1)])
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        """
        Inputs: [X, y]
        """
        X = self.get_inputs(inputs)
        lr_out = self.lr_layer(X)
        field_wise_emb_list = [each_layer(X) for each_layer in self.embedding_layers]
        ffm_out = self.ffm_interaction(field_wise_emb_list)
        y_pred = lr_out + ffm_out
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred}
        return return_dict

    def ffm_interaction(self, field_wise_emb_list):
        dot = 0
        for i in range(self.num_fields - 1):
            for j in range(i + 1, self.num_fields):
                v_ij = field_wise_emb_list[j - 1][:, i, :]
                v_ji = field_wise_emb_list[i][:, j, :]
                dot += torch.sum(v_ij * v_ji, dim=1, keepdim=True)
        return dot

def ffm_interaction(self, field_wise_emb_list):
    dot = 0
    for i in range(self.num_fields - 1):
        for j in range(i + 1, self.num_fields):
            v_ij = field_wise_emb_list[j - 1][:, i, :]
            v_ji = field_wise_emb_list[i][:, j, :]
            dot += torch.sum(v_ij * v_ji, dim=1, keepdim=True)
    return dot

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

def __init__(self, data_path):
    self.column_index = dict()
    self.darray = self.load_data(data_path)

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

def add_loss(self, return_dict, y_true):
    loss_gsu = self.loss_fn(return_dict['y_aux'], y_true, reduction='mean')
    loss_esu = self.loss_fn(return_dict['y_pred'], y_true, reduction='mean')
    return self.alpha * loss_gsu + self.beta * loss_esu

class APG_MLP(nn.Module):

    def __init__(self, input_dim, hidden_units=[], hidden_activations='ReLU', output_dim=None, output_activation=None, dropout_rates=0.0, batch_norm=False, bn_only_once=False, use_bias=True, hypernet_config={}, condition_dim=None, condition_mode='self-wise', rank_k=None, overparam_p=None, generate_bias=True):
        super(APG_MLP, self).__init__()
        self.hidden_layers = len(hidden_units)
        if not isinstance(dropout_rates, list):
            dropout_rates = [dropout_rates] * self.hidden_layers
        if not isinstance(hidden_activations, list):
            hidden_activations = [hidden_activations] * self.hidden_layers
        hidden_activations = get_activation(hidden_activations, hidden_units)
        if not isinstance(rank_k, list):
            rank_k = [rank_k] * self.hidden_layers
        if not isinstance(overparam_p, list):
            overparam_p = [overparam_p] * self.hidden_layers
        assert self.hidden_layers == len(dropout_rates) == len(hidden_activations) == len(rank_k) == len(overparam_p)
        hidden_units = [input_dim] + hidden_units
        self.dense_layers = nn.ModuleDict()
        if batch_norm and bn_only_once:
            self.dense_layers['bn_0'] = nn.BatchNorm1d(input_dim)
        self.condition_mode = condition_mode
        assert condition_mode in ['self-wise', 'group-wise', 'mix-wise'], 'Invalid condition_mode={}'.format(condition_mode)
        for idx in range(self.hidden_layers):
            if self.condition_mode == 'self-wise':
                condition_dim = hidden_units[idx]
            self.dense_layers['linear_{}'.format(idx + 1)] = APG_Linear(hidden_units[idx], hidden_units[idx + 1], condition_dim, bias=use_bias, rank_k=rank_k[idx], overparam_p=overparam_p[idx], generate_bias=generate_bias, hypernet_config=hypernet_config)
            if batch_norm and (not bn_only_once):
                self.dense_layers['bn_{}'.format(idx + 1)] = nn.BatchNorm1d(hidden_units[idx + 1])
            if hidden_activations[idx]:
                self.dense_layers['act_{}'.format(idx + 1)] = hidden_activations[idx]
            if dropout_rates[idx] > 0:
                self.dense_layers['drop_{}'.format(idx + 1)] = nn.Dropout(p=dropout_rates[idx])
        if output_dim is not None:
            self.dense_layers['out_proj'] = nn.Linear(hidden_units[-1], output_dim, bias=use_bias)
        if output_activation is not None:
            self.dense_layers['out_act'] = get_activation(output_activation)

    def forward(self, x, condition_z=None):
        if 'bn_0' in self.dense_layers:
            x = self.dense_layers['bn_0'](x)
        for idx in range(self.hidden_layers):
            if self.condition_mode == 'self-wise':
                x = self.dense_layers['linear_{}'.format(idx + 1)](x, x)
            else:
                x = self.dense_layers['linear_{}'.format(idx + 1)](x, condition_z)
            if 'bn_{}'.format(idx + 1) in self.dense_layers:
                x = self.dense_layers['bn_{}'.format(idx + 1)](x)
            if 'act_{}'.format(idx + 1) in self.dense_layers:
                x = self.dense_layers['act_{}'.format(idx + 1)](x)
            if 'drop_{}'.format(idx + 1) in self.dense_layers:
                x = self.dense_layers['drop_{}'.format(idx + 1)](x)
        if 'out_proj' in self.dense_layers:
            x = self.dense_layers['out_proj'](x)
        if 'out_act' in self.dense_layers:
            x = self.dense_layers['out_act'](x)
        return x

def forward(self, x, condition_z=None):
    if 'bn_0' in self.dense_layers:
        x = self.dense_layers['bn_0'](x)
    for idx in range(self.hidden_layers):
        if self.condition_mode == 'self-wise':
            x = self.dense_layers['linear_{}'.format(idx + 1)](x, x)
        else:
            x = self.dense_layers['linear_{}'.format(idx + 1)](x, condition_z)
        if 'bn_{}'.format(idx + 1) in self.dense_layers:
            x = self.dense_layers['bn_{}'.format(idx + 1)](x)
        if 'act_{}'.format(idx + 1) in self.dense_layers:
            x = self.dense_layers['act_{}'.format(idx + 1)](x)
        if 'drop_{}'.format(idx + 1) in self.dense_layers:
            x = self.dense_layers['drop_{}'.format(idx + 1)](x)
    if 'out_proj' in self.dense_layers:
        x = self.dense_layers['out_proj'](x)
    if 'out_act' in self.dense_layers:
        x = self.dense_layers['out_act'](x)
    return x

class PPNet_MLP(nn.Module):

    def __init__(self, input_dim, output_dim=1, gate_input_dim=64, gate_hidden_dim=None, hidden_units=[], hidden_activations='ReLU', dropout_rates=0.0, batch_norm=False, use_bias=True):
        super(PPNet_MLP, self).__init__()
        if not isinstance(dropout_rates, list):
            dropout_rates = [dropout_rates] * len(hidden_units)
        if not isinstance(hidden_activations, list):
            hidden_activations = [hidden_activations] * len(hidden_units)
        hidden_activations = [get_activation(x) for x in hidden_activations]
        self.gate_layers = nn.ModuleList()
        self.mlp_layers = nn.ModuleList()
        hidden_units = [input_dim] + hidden_units
        for idx in range(len(hidden_units) - 1):
            layers = [nn.Linear(hidden_units[idx], hidden_units[idx + 1], bias=use_bias)]
            if batch_norm:
                layers.append(nn.BatchNorm1d(hidden_units[idx + 1]))
            if hidden_activations[idx] is not None:
                layers.append(hidden_activations[idx])
            if dropout_rates[idx] > 0:
                layers.append(nn.Dropout(p=dropout_rates[idx]))
            self.mlp_layers.append(nn.Sequential(*layers))
            self.gate_layers.append(GateNU(gate_input_dim, gate_hidden_dim, output_dim=hidden_units[idx + 1]))
        self.mlp_layers.append(nn.Linear(hidden_units[-1], output_dim, bias=use_bias))

    def forward(self, feature_emb, gate_emb):
        gate_input = torch.cat([feature_emb.detach(), gate_emb], dim=-1)
        h = feature_emb
        for i in range(len(self.gate_layers)):
            h = self.mlp_layers[i](h)
            g = self.gate_layers[i](gate_input)
            h = h * g
        out = self.mlp_layers[-1](h)
        return out

def forward(self, feature_emb, gate_emb):
    gate_input = torch.cat([feature_emb.detach(), gate_emb], dim=-1)
    h = feature_emb
    for i in range(len(self.gate_layers)):
        h = self.mlp_layers[i](h)
        g = self.gate_layers[i](gate_input)
        h = h * g
    out = self.mlp_layers[-1](h)
    return out

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

class DMR(BaseModel):
    """ Implementation of DMR model based on the following reference code:
        https://github.com/lvze92/DMR
        https://github.com/thinkall/Contrib/tree/master/DMR
    """

    def __init__(self, feature_map, model_id='DMR', gpu=-1, learning_rate=0.001, embedding_dim=10, dnn_hidden_units=[512, 128, 64], dnn_activations='ReLU', net_dropout=0, batch_norm=True, bn_only_once=False, target_field=('item_id', 'cate_id'), sequence_field=('click_history', 'cate_history'), neg_seq_field=('neg_click_history', 'neg_cate_history'), context_field='btag', enable_sum_pooling=False, enable_u2i_rel=True, enable_i2i_rel=False, attention_hidden_units=[80, 40], attention_activation='ReLU', attention_dropout=0, use_pos_emb=True, pos_emb_dim=8, aux_loss_beta=0, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(DMR, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        if target_field and (not isinstance(target_field, list)):
            target_field = [target_field]
        self.target_field = target_field
        if sequence_field and (not isinstance(sequence_field, list)):
            sequence_field = [sequence_field]
        self.sequence_field = sequence_field
        if neg_seq_field and (not isinstance(neg_seq_field, list)):
            neg_seq_field = [neg_seq_field]
        self.neg_seq_field = neg_seq_field
        if context_field and (not isinstance(context_field, list)):
            context_field = [context_field]
        self.context_field = context_field
        assert len(target_field) == len(sequence_field)
        if neg_seq_field:
            assert len(neg_seq_field) == len(sequence_field)
        if context_field:
            assert len(context_field) == len(sequence_field)
        self.aux_loss_beta = aux_loss_beta
        self.enable_sum_pooling = enable_sum_pooling
        self.feature_map = feature_map
        self.embedding_dim = embedding_dim
        self.embedding_layer = FeatureEmbeddingDict(feature_map, embedding_dim, not_required_feature_columns=flatten([self.neg_seq_field]) if self.neg_seq_field else None)
        self.sum_pooling = MaskedSumPooling()
        self.output_emb_layer = nn.ModuleDict()
        for feature in flatten([self.target_field]):
            feature_spec = feature_map.features[feature]
            self.output_emb_layer[feature] = nn.Embedding(feature_spec['vocab_size'], embedding_dim, padding_idx=feature_spec['padding_idx'])
        if self.context_field is not None:
            self.context_emb_layer = nn.ModuleDict()
            for feature in flatten([self.context_field]):
                feature_spec = feature_map.features[feature]
                self.context_emb_layer[feature] = nn.Embedding(feature_spec['vocab_size'], embedding_dim, padding_idx=feature_spec['padding_idx'])
        self.enable_u2i_rel = enable_u2i_rel
        self.enable_i2i_rel = enable_i2i_rel
        self.u2i_net = nn.ModuleList()
        self.i2i_net = nn.ModuleList()
        feature_dim = feature_map.sum_emb_out_dim()
        for i in range(len(self.target_field)):
            model_dim = embedding_dim * len(list(flatten([self.target_field[i]])))
            max_seq_len = feature_map.features[list(flatten([self.sequence_field[i]]))[0]]['max_len']
            if self.enable_sum_pooling:
                feature_dim += model_dim * 2
            if self.context_field:
                context_dim = embedding_dim * len(list(flatten([self.context_field[i]])))
            else:
                context_dim = 0
            if enable_u2i_rel:
                self.u2i_net.append(User2ItemNet(context_dim, model_dim, attention_hidden_units=attention_hidden_units, attention_activation=attention_activation, attention_dropout=attention_dropout, pos_emb_dim=pos_emb_dim, max_seq_len=max_seq_len))
                feature_dim += 1
            if enable_i2i_rel:
                feature_dim += 1
            self.i2i_net.append(Item2ItemNet(context_dim, model_dim, attention_hidden_units=attention_hidden_units, attention_activation=attention_activation, attention_dropout=attention_dropout, use_pos_emb=use_pos_emb, pos_emb_dim=pos_emb_dim, max_seq_len=max_seq_len))
        if self.neg_seq_field is not None:
            feature_dim -= embedding_dim * len(set(flatten([self.neg_seq_field])))
        self.dnn = MLP_Block(input_dim=feature_dim, output_dim=1, hidden_units=dnn_hidden_units, hidden_activations=dnn_activations, output_activation=self.output_activation, dropout_rates=net_dropout, batch_norm=batch_norm, bn_only_once=bn_only_once)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        X = self.get_inputs(inputs)
        feature_emb_dict = self.embedding_layer(X)
        concat_emb = []
        aux_loss_sum = 0
        for i in range(len(self.target_field)):
            target_emb = self.get_embedding(self.target_field[i], feature_emb_dict)
            sequence_emb = self.get_embedding(self.sequence_field[i], feature_emb_dict)
            seq_field = list(flatten([self.sequence_field[i]]))[0]
            pad_mask = X[seq_field].long() > 0
            context_emb = self.get_embedding(self.context_field[i], feature_emb_dict) if self.context_field else None
            attn_out, rel_i2i = self.i2i_net[i](target_emb, sequence_emb, context_emb, mask=pad_mask)
            concat_emb.append(attn_out)
            if self.enable_i2i_rel:
                concat_emb.append(rel_i2i)
            if self.enable_u2i_rel:
                neg_emb = self.get_out_embedding(self.neg_seq_field[i], self.target_field[i], X) if self.aux_loss_beta > 0 else None
                target_emb2 = self.get_out_embedding(self.target_field[i], self.target_field[i], X)
                sequence_emb2 = self.get_out_embedding(self.sequence_field[i], self.target_field[i], X)
                context_emb2 = self.get_context_embedding(self.context_field[i], X) if self.context_field else None
                rel_u2i, aux_loss = self.u2i_net[i](target_emb2, sequence_emb, context_emb2, sequence_emb2, neg_emb, mask=pad_mask)
                aux_loss_sum += aux_loss
                concat_emb.append(rel_u2i)
            if self.enable_sum_pooling:
                sum_pool_emb = self.sum_pooling(sequence_emb)
                concat_emb += [sum_pool_emb, target_emb * sum_pool_emb]
        for feature, emb in feature_emb_dict.items():
            if emb.ndim == 2 and feature not in set(flatten([self.neg_seq_field])):
                concat_emb.append(emb)
        y_pred = self.dnn(torch.cat(concat_emb, dim=-1))
        return_dict = {'y_pred': y_pred, 'aux_loss': aux_loss_sum}
        return return_dict

    def add_loss(self, return_dict, y_true):
        loss = self.loss_fn(return_dict['y_pred'], y_true, reduction='mean')
        if self.aux_loss_beta > 0:
            loss += self.aux_loss_beta * return_dict['aux_loss']
        return loss

    def get_embedding(self, field, feature_emb_dict):
        if type(field) == tuple:
            emb_list = [feature_emb_dict[f] for f in field]
            return torch.cat(emb_list, dim=-1)
        else:
            return feature_emb_dict[field]

    def get_out_embedding(self, field, target_field, X):
        emb_list = []
        for input_name, emb_name in zip(flatten([field]), flatten([target_field])):
            emb = self.output_emb_layer[emb_name](X[input_name].long())
            emb_list.append(emb)
        return torch.cat(emb_list, dim=-1)

    def get_context_embedding(self, field, X):
        emb_list = []
        for feature in zip(flatten([field])):
            emb = self.context_emb_layer[feature](X[feature].long())
            emb_list.append(emb)
        return torch.cat(emb_list, dim=-1)

def add_loss(self, return_dict, y_true):
    loss = self.loss_fn(return_dict['y_pred'], y_true, reduction='mean')
    if self.aux_loss_beta > 0:
        loss += self.aux_loss_beta * return_dict['aux_loss']
    return loss

class GateCorssLayer(nn.Module):

    def __init__(self, input_dim, cn_layers=3):
        super().__init__()
        self.cn_layers = cn_layers
        self.w = nn.ModuleList([nn.Linear(input_dim, input_dim, bias=False) for _ in range(cn_layers)])
        self.wg = nn.ModuleList([nn.Linear(input_dim, input_dim, bias=False) for _ in range(cn_layers)])
        self.b = nn.ParameterList([nn.Parameter(torch.zeros((input_dim,))) for _ in range(cn_layers)])
        for i in range(cn_layers):
            nn.init.uniform_(self.b[i].data)
        self.activation = nn.Sigmoid()

    def forward(self, x):
        x0 = x
        for i in range(self.cn_layers):
            xw = self.w[i](x)
            xg = self.activation(self.wg[i](x))
            x = x0 * (xw + self.b[i]) * xg + x
        return x

def forward(self, x):
    x0 = x
    for i in range(self.cn_layers):
        xw = self.w[i](x)
        xg = self.activation(self.wg[i](x))
        x = x0 * (xw + self.b[i]) * xg + x
    return x

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

class CrossNet(Layer):

    def __init__(self, input_dim, num_layers):
        super(CrossNet, self).__init__()
        self.num_layers = num_layers
        self.cross_net = []
        for _ in range(self.num_layers):
            self.cross_net.append(CrossInteraction(input_dim))

    def call(self, X_0):
        X_i = X_0
        for i in range(self.num_layers):
            X_i = X_i + self.cross_net[i](X_0, X_i)
        return X_i

def call(self, X_0):
    X_i = X_0
    for i in range(self.num_layers):
        X_i = X_i + self.cross_net[i](X_0, X_i)
    return X_i

class CrossNetV2(Layer):

    def __init__(self, input_dim, num_layers):
        super(CrossNetV2, self).__init__()
        self.num_layers = num_layers
        self.cross_layers = []
        for _ in range(self.num_layers):
            self.cross_layers.append(Dense(input_dim))

    def call(self, X_0):
        X_i = X_0
        for i in range(self.num_layers):
            X_i = X_i + X_0 * self.cross_layers[i](X_i)
        return X_i

def call(self, X_0):
    X_i = X_0
    for i in range(self.num_layers):
        X_i = X_i + X_0 * self.cross_layers[i](X_i)
    return X_i

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

def add_loss(self, inputs):
    return_dict = self(inputs, training=True)
    y_true = self.get_labels(inputs)
    loss = self.loss_fn(return_dict['y_pred'], y_true)
    return loss

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

def __init__(self, feature_map, data_path):
    self.feature_map = feature_map
    self.darray = self.load_data(data_path)

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

def __init__(self, feature_map, data_path):
    self.feature_map = feature_map
    self.darray = self.load_data(data_path)

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

def read_block(self, data_block):
    darray = self.load_data(data_block)
    for idx in range(darray.shape[0]):
        yield darray[idx, :]

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

def read_block(self, data_block):
    darray = self.load_data(data_block)
    for idx in range(darray.shape[0]):
        yield darray[idx, :]

class CrossNet(nn.Module):

    def __init__(self, input_dim, num_layers):
        super(CrossNet, self).__init__()
        self.num_layers = num_layers
        self.cross_net = nn.ModuleList((CrossInteraction(input_dim) for _ in range(self.num_layers)))

    def forward(self, X_0):
        X_i = X_0
        for i in range(self.num_layers):
            X_i = X_i + self.cross_net[i](X_0, X_i)
        return X_i

def forward(self, X_0):
    X_i = X_0
    for i in range(self.num_layers):
        X_i = X_i + self.cross_net[i](X_0, X_i)
    return X_i

class CrossNetV2(nn.Module):

    def __init__(self, input_dim, num_layers):
        super(CrossNetV2, self).__init__()
        self.num_layers = num_layers
        self.cross_layers = nn.ModuleList((nn.Linear(input_dim, input_dim) for _ in range(self.num_layers)))

    def forward(self, X_0):
        X_i = X_0
        for i in range(self.num_layers):
            X_i = X_i + X_0 * self.cross_layers[i](X_i)
        return X_i

def forward(self, X_0):
    X_i = X_0
    for i in range(self.num_layers):
        X_i = X_i + X_0 * self.cross_layers[i](X_i)
    return X_i

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

def add_loss(self, return_dict, y_true):
    loss = self.loss_fn(return_dict['y_pred'], y_true, reduction='mean')
    return loss

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

