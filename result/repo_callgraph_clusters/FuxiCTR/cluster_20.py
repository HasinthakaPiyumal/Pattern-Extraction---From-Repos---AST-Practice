# Cluster 20

class FeatureGating(nn.Module):

    def __init__(self, num_fields, gate_residual='concat'):
        super(FeatureGating, self).__init__()
        self.linear = nn.Linear(num_fields, num_fields)
        assert gate_residual in ['concat', 'sum']
        self.gate_residual = gate_residual

    def init_weights(self):
        nn.init.zeros_(self.linear.weight)
        nn.init.ones_(self.linear.bias)

    def forward(self, feature_emb):
        gates = self.linear(feature_emb.transpose(1, 2)).transpose(1, 2)
        if self.gate_residual == 'concat':
            out = torch.cat([feature_emb, feature_emb * gates], dim=1)
        else:
            out = feature_emb + feature_emb * gates
        return out

def init_weights(self):
    nn.init.zeros_(self.linear.weight)
    nn.init.ones_(self.linear.bias)

class DIN(BaseModel):

    def __init__(self, feature_map, model_id='DIN', gpu=-1, dnn_hidden_units=[512, 128, 64], dnn_activations='ReLU', attention_hidden_units=[64], attention_hidden_activations='Dice', attention_output_activation=None, attention_dropout=0, learning_rate=0.001, embedding_dim=10, net_dropout=0, batch_norm=False, din_target_field=[('item_id', 'cate_id')], din_sequence_field=[('click_history', 'cate_history')], din_use_softmax=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(DIN, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        if not isinstance(din_target_field, list):
            din_target_field = [din_target_field]
        self.din_target_field = din_target_field
        if not isinstance(din_sequence_field, list):
            din_sequence_field = [din_sequence_field]
        self.din_sequence_field = din_sequence_field
        assert len(self.din_target_field) == len(self.din_sequence_field), 'len(din_target_field) != len(din_sequence_field)'
        if isinstance(dnn_activations, str) and dnn_activations.lower() == 'dice':
            dnn_activations = [Dice(units) for units in dnn_hidden_units]
        self.feature_map = feature_map
        self.embedding_dim = embedding_dim
        self.embedding_layer = FeatureEmbeddingDict(feature_map, embedding_dim)
        self.attention_layers = nn.ModuleList([DIN_Attention(embedding_dim * len(target_field) if type(target_field) == tuple else embedding_dim, attention_units=attention_hidden_units, hidden_activations=attention_hidden_activations, output_activation=attention_output_activation, dropout_rate=attention_dropout, use_softmax=din_use_softmax) for target_field in self.din_target_field])
        self.dnn = MLP_Block(input_dim=feature_map.sum_emb_out_dim(), output_dim=1, hidden_units=dnn_hidden_units, hidden_activations=dnn_activations, output_activation=self.output_activation, dropout_rates=net_dropout, batch_norm=batch_norm)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        X = self.get_inputs(inputs)
        feature_emb_dict = self.embedding_layer(X)
        for idx, (target_field, sequence_field) in enumerate(zip(self.din_target_field, self.din_sequence_field)):
            target_emb = self.get_embedding(target_field, feature_emb_dict)
            sequence_emb = self.get_embedding(sequence_field, feature_emb_dict)
            seq_field = list(flatten([sequence_field]))[0]
            mask = X[seq_field].long() != 0
            pooling_emb = self.attention_layers[idx](target_emb, sequence_emb, mask)
            for field, field_emb in zip(list(flatten([sequence_field])), pooling_emb.split(self.embedding_dim, dim=-1)):
                feature_emb_dict[field] = field_emb
        feature_emb = self.embedding_layer.dict2tensor(feature_emb_dict, flatten_emb=True)
        y_pred = self.dnn(feature_emb)
        return_dict = {'y_pred': y_pred}
        return return_dict

    def get_embedding(self, field, feature_emb_dict):
        if type(field) == tuple:
            emb_list = [feature_emb_dict[f] for f in field]
            return torch.cat(emb_list, dim=-1)
        else:
            return feature_emb_dict[field]

def get_embedding(self, field, feature_emb_dict):
    if type(field) == tuple:
        emb_list = [feature_emb_dict[f] for f in field]
        return torch.cat(emb_list, dim=-1)
    else:
        return feature_emb_dict[field]

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

def get_embedding(self, field, feature_emb_dict):
    if type(field) == tuple:
        emb_list = [feature_emb_dict[f] for f in field]
        return torch.cat(emb_list, dim=-1)
    else:
        return feature_emb_dict[field]

class BST(BaseModel):

    def __init__(self, feature_map, model_id='BST', gpu=-1, dnn_hidden_units=[256, 128, 64], dnn_activations='ReLU', num_heads=2, stacked_transformer_layers=1, attention_dropout=0, learning_rate=0.001, embedding_dim=10, net_dropout=0, batch_norm=False, layer_norm=True, use_residual=True, bst_target_field=[('item_id', 'cate_id')], bst_sequence_field=[('click_history', 'cate_history')], seq_pooling_type='mean', use_position_emb=True, use_causal_mask=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(BST, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        if type(bst_target_field) != list:
            bst_target_field = [bst_target_field]
        self.bst_target_field = bst_target_field
        if type(bst_sequence_field) != list:
            bst_sequence_field = [bst_sequence_field]
        self.bst_sequence_field = bst_sequence_field
        assert len(self.bst_target_field) == len(self.bst_sequence_field), 'len(self.bst_target_field) != len(self.bst_sequence_field)'
        self.use_causal_mask = use_causal_mask
        self.seq_pooling_type = seq_pooling_type
        self.feature_map = feature_map
        self.embedding_dim = embedding_dim
        self.num_heads = num_heads
        self.embedding_layer = FeatureEmbeddingDict(feature_map, embedding_dim)
        self.transformer_encoders = nn.ModuleList()
        seq_out_dim = 0
        for sequence_field in self.bst_sequence_field:
            if type(sequence_field) == tuple:
                model_dim = embedding_dim * (int(use_position_emb) + len(sequence_field))
                seq_len = feature_map.features[sequence_field[0]]['max_len'] + 1
            else:
                model_dim = embedding_dim * (1 + int(use_position_emb))
                seq_len = feature_map.features[sequence_field]['max_len'] + 1
            seq_out_dim += self.get_seq_out_dim(model_dim, seq_len, sequence_field, embedding_dim)
            self.transformer_encoders.append(BehaviorTransformer(seq_len=seq_len, model_dim=model_dim, num_heads=num_heads, stacked_transformer_layers=stacked_transformer_layers, attn_dropout=attention_dropout, net_dropout=net_dropout, position_dim=embedding_dim, use_position_emb=use_position_emb, layer_norm=layer_norm, use_residual=use_residual))
        self.dnn = MLP_Block(input_dim=feature_map.sum_emb_out_dim() + seq_out_dim, output_dim=1, hidden_units=dnn_hidden_units, hidden_activations=dnn_activations, output_activation=self.output_activation, dropout_rates=net_dropout, batch_norm=batch_norm)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def get_seq_out_dim(self, model_dim, seq_len, sequence_field, embedding_dim):
        num_seq_field = len(sequence_field) if type(sequence_field) == tuple else 1
        if self.seq_pooling_type == 'concat':
            seq_out_dim = seq_len * model_dim - num_seq_field * embedding_dim
        else:
            seq_out_dim = model_dim - num_seq_field * embedding_dim
        return seq_out_dim

    def forward(self, inputs):
        X = self.get_inputs(inputs)
        feature_emb_dict = self.embedding_layer(X)
        for idx, (target_field, sequence_field) in enumerate(zip(self.bst_target_field, self.bst_sequence_field)):
            target_emb = self.concat_embedding(target_field, feature_emb_dict)
            sequence_emb = self.concat_embedding(sequence_field, feature_emb_dict)
            concat_seq_emb = torch.cat([sequence_emb, target_emb.unsqueeze(1)], dim=1)
            seq_field = list(flatten([sequence_field]))[0]
            padding_mask, attn_mask = self.get_mask(X[seq_field])
            transformer_out = self.transformer_encoders[idx](concat_seq_emb, attn_mask)
            pooling_emb = self.sequence_pooling(transformer_out, padding_mask)
            feature_emb_dict[f'attn_{idx}'] = pooling_emb
            for field in flatten([sequence_field]):
                feature_emb_dict.pop(field, None)
        concat_emb = torch.cat(list(feature_emb_dict.values()), dim=-1)
        y_pred = self.dnn(concat_emb)
        return_dict = {'y_pred': y_pred}
        return return_dict

    def get_mask(self, x):
        """ padding_mask: B x L, 1 for masked positions
            attn_mask: (B*H) x L x L, 1 for masked positions in nn.MultiheadAttention
        """
        padding_mask = x == 0
        padding_mask = torch.cat([padding_mask, torch.zeros(x.size(0), 1).bool().to(x.device)], dim=-1)
        seq_len = padding_mask.size(1)
        attn_mask = padding_mask.unsqueeze(1).repeat(1, seq_len, 1)
        diag_zeros = ~torch.eye(seq_len, device=x.device).bool().unsqueeze(0).expand_as(attn_mask)
        attn_mask = attn_mask & diag_zeros
        if self.use_causal_mask:
            causal_mask = torch.triu(torch.ones(seq_len, seq_len, device=x.device), 1).bool().unsqueeze(0).expand_as(attn_mask)
            attn_mask = attn_mask | causal_mask
        attn_mask = attn_mask.unsqueeze(1).repeat(1, self.num_heads, 1, 1).flatten(end_dim=1)
        return (padding_mask, attn_mask)

    def sequence_pooling(self, transformer_out, mask):
        mask = (1 - mask.float()).unsqueeze(-1)
        if self.seq_pooling_type == 'mean':
            return (transformer_out * mask).sum(dim=1) / (mask.sum(dim=1) + 1e-12)
        elif self.seq_pooling_type == 'sum':
            return (transformer_out * mask).sum(dim=1)
        elif self.seq_pooling_type == 'target':
            return transformer_out[:, -1, :]
        elif self.seq_pooling_type == 'concat':
            return transformer_out.flatten(start_dim=1)
        else:
            raise ValueError('seq_pooling_type={} not supported.'.format(self.seq_pooling_type))

    def concat_embedding(self, field, feature_emb_dict):
        if type(field) == tuple:
            emb_list = [feature_emb_dict[f] for f in field]
            return torch.cat(emb_list, dim=-1)
        else:
            return feature_emb_dict[field]

def get_seq_out_dim(self, model_dim, seq_len, sequence_field, embedding_dim):
    num_seq_field = len(sequence_field) if type(sequence_field) == tuple else 1
    if self.seq_pooling_type == 'concat':
        seq_out_dim = seq_len * model_dim - num_seq_field * embedding_dim
    else:
        seq_out_dim = model_dim - num_seq_field * embedding_dim
    return seq_out_dim

def concat_embedding(self, field, feature_emb_dict):
    if type(field) == tuple:
        emb_list = [feature_emb_dict[f] for f in field]
        return torch.cat(emb_list, dim=-1)
    else:
        return feature_emb_dict[field]

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

    def __init__(self, feature_map, model_id='TransAct', gpu=-1, hidden_activations='ReLU', dcn_cross_layers=3, dcn_hidden_units=[256, 128, 64], mlp_hidden_units=[], num_heads=1, transformer_layers=1, transformer_dropout=0, dim_feedforward=512, learning_rate=0.001, embedding_dim=64, net_dropout=0, batch_norm=False, target_item_field=[('item_id', 'cate_id')], sequence_item_field=[('click_history', 'cate_history')], first_k_cols=1, use_time_window_mask=False, time_window_ms=86400000, concat_max_pool=True, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super().__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.target_item_field = target_item_field if type(target_item_field) == list else [target_item_field]
        self.sequence_item_field = sequence_item_field if type(sequence_item_field) == list else [sequence_item_field]
        self.feature_map = feature_map
        self.embedding_dim = embedding_dim
        self.embedding_layer = FeatureEmbeddingDict(feature_map, embedding_dim)
        self.transformer_encoders = nn.ModuleList()
        seq_out_dim = 0
        for sequence_field, item_field in zip(self.sequence_item_field, self.target_item_field):
            seq_emb_dim = embedding_dim * len(sequence_field) if type(sequence_field) == tuple else embedding_dim
            target_emb_dim = embedding_dim * len(item_field) if type(item_field) == tuple else embedding_dim
            transformer_in_dim = seq_emb_dim + target_emb_dim
            self.transformer_encoders.append(TransActTransformer(transformer_in_dim, dim_feedforward=dim_feedforward, num_heads=num_heads, dropout=transformer_dropout, transformer_layers=transformer_layers, use_time_window_mask=use_time_window_mask, time_window_ms=time_window_ms, first_k_cols=first_k_cols, concat_max_pool=concat_max_pool))
            seq_out_dim += (first_k_cols + int(concat_max_pool)) * transformer_in_dim - seq_emb_dim
        dcn_in_dim = feature_map.sum_emb_out_dim() + seq_out_dim
        self.crossnet = CrossNetV2(dcn_in_dim, dcn_cross_layers)
        self.parallel_dnn = MLP_Block(input_dim=dcn_in_dim, output_dim=None, hidden_units=dcn_hidden_units, hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm)
        dcn_out_dim = dcn_in_dim + dcn_hidden_units[-1]
        self.mlp = MLP_Block(input_dim=dcn_out_dim, output_dim=1, hidden_units=mlp_hidden_units, hidden_activations=hidden_activations, output_activation=self.output_activation)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        X = self.get_inputs(inputs)
        feature_emb_dict = self.embedding_layer(X)
        for idx, (target_field, sequence_field) in enumerate(zip(self.target_item_field, self.sequence_item_field)):
            target_emb = self.concat_embedding(target_field, feature_emb_dict)
            sequence_emb = self.concat_embedding(sequence_field, feature_emb_dict)
            seq_field = list(flatten([sequence_field]))[0]
            padding_mask = X[seq_field].long() == 0
            transformer_out = self.transformer_encoders[idx](target_emb, sequence_emb, mask=padding_mask)
            feature_emb_dict[f'transact_{idx}'] = transformer_out
        for feat in flatten(self.sequence_item_field):
            if self.feature_map.features[feat]['type'] == 'sequence':
                feature_emb_dict.pop(feat, None)
        dcn_in_emb = torch.cat(list(feature_emb_dict.values()), dim=-1)
        cross_out = self.crossnet(dcn_in_emb)
        dnn_out = self.parallel_dnn(dcn_in_emb)
        y_pred = self.mlp(torch.cat([cross_out, dnn_out], dim=-1))
        return_dict = {'y_pred': y_pred}
        return return_dict

    def concat_embedding(self, field, feature_emb_dict):
        if type(field) == tuple:
            emb_list = [feature_emb_dict[f] for f in field]
            return torch.cat(emb_list, dim=-1)
        else:
            return feature_emb_dict[field]

def concat_embedding(self, field, feature_emb_dict):
    if type(field) == tuple:
        emb_list = [feature_emb_dict[f] for f in field]
        return torch.cat(emb_list, dim=-1)
    else:
        return feature_emb_dict[field]

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

def get_embedding(self, field, feature_emb_dict):
    if type(field) == tuple:
        emb_list = [feature_emb_dict[f] for f in field]
        return torch.cat(emb_list, dim=-1)
    else:
        return feature_emb_dict[field]

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

def get_embedding(self, field, feature_emb_dict):
    if type(field) == tuple:
        emb_list = [feature_emb_dict[f] for f in field]
        return torch.cat(emb_list, dim=-1)
    else:
        return feature_emb_dict[field]

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

def get_value(self, logs):
    value = 0
    for k, v in self.kv_pairs.items():
        value += logs.get(k, 0) * v
    return value

def not_in_whitelist(element, whitelist=[]):
    if not whitelist:
        return False
    elif type(whitelist) == list:
        return element not in whitelist
    else:
        return element != whitelist

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

def update_feature_specs(self, feature_specs):
    for col in feature_specs:
        namelist = col['name']
        if type(namelist) != list:
            namelist = [namelist]
        for name in namelist:
            for k, v in col.items():
                if k != 'name':
                    self.features[name][k] = v

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

def evaluate_block(df, metric_funcs):
    res_list = []
    for fn in metric_funcs:
        v = fn(df.y_true.values, df.y_pred.values)
        if type(v) == tuple:
            res_list.append(v)
        else:
            res_list.append((v, 1))
    return res_list

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

class MLP_Block(Layer):

    def __init__(self, input_dim, hidden_units=[], hidden_activations='ReLU', output_dim=None, output_activation=None, dropout_rates=0.0, batch_norm=False, layer_norm=False, norm_before_activation=True, use_bias=True, initializer='glorot_normal', regularizer=None):
        super(MLP_Block, self).__init__()
        self.mlp = tf.keras.Sequential()
        if not isinstance(dropout_rates, list):
            dropout_rates = [dropout_rates] * len(hidden_units)
        if not isinstance(hidden_activations, list):
            hidden_activations = [hidden_activations] * len(hidden_units)
        hidden_activations = [get_activation(x) for x in hidden_activations]
        hidden_units = [input_dim] + hidden_units
        for idx in range(len(hidden_units) - 1):
            self.mlp.add(Dense(hidden_units[idx + 1], use_bias=use_bias, kernel_initializer=get_initializer(initializer), kernel_regularizer=get_regularizer(regularizer), bias_regularizer=get_regularizer(regularizer)))
            if norm_before_activation:
                if batch_norm:
                    self.mlp.add(BatchNormalization(hidden_units[idx + 1]))
                elif layer_norm:
                    self.mlp.add(LayerNormalization(hidden_units[idx + 1]))
            if hidden_activations[idx]:
                self.mlp.add(hidden_activations[idx])
            if not norm_before_activation:
                if batch_norm:
                    self.mlp.add(BatchNormalization(hidden_units[idx + 1]))
                elif layer_norm:
                    self.mlp.add(LayerNormalization(hidden_units[idx + 1]))
            if dropout_rates[idx] > 0:
                self.mlp.add(Dropout(p=dropout_rates[idx]))
        if output_dim is not None:
            self.mlp.add(Dense(output_dim, use_bias=use_bias, kernel_initializer=get_initializer(initializer), kernel_regularizer=get_regularizer(regularizer), bias_regularizer=get_regularizer(regularizer)))
        if output_activation is not None:
            self.mlp.add(get_activation(output_activation))

    def call(self, inputs, training=None):
        return self.mlp(inputs, training=training)

def __init__(self, input_dim, hidden_units=[], hidden_activations='ReLU', output_dim=None, output_activation=None, dropout_rates=0.0, batch_norm=False, layer_norm=False, norm_before_activation=True, use_bias=True, initializer='glorot_normal', regularizer=None):
    super(MLP_Block, self).__init__()
    self.mlp = tf.keras.Sequential()
    if not isinstance(dropout_rates, list):
        dropout_rates = [dropout_rates] * len(hidden_units)
    if not isinstance(hidden_activations, list):
        hidden_activations = [hidden_activations] * len(hidden_units)
    hidden_activations = [get_activation(x) for x in hidden_activations]
    hidden_units = [input_dim] + hidden_units
    for idx in range(len(hidden_units) - 1):
        self.mlp.add(Dense(hidden_units[idx + 1], use_bias=use_bias, kernel_initializer=get_initializer(initializer), kernel_regularizer=get_regularizer(regularizer), bias_regularizer=get_regularizer(regularizer)))
        if norm_before_activation:
            if batch_norm:
                self.mlp.add(BatchNormalization(hidden_units[idx + 1]))
            elif layer_norm:
                self.mlp.add(LayerNormalization(hidden_units[idx + 1]))
        if hidden_activations[idx]:
            self.mlp.add(hidden_activations[idx])
        if not norm_before_activation:
            if batch_norm:
                self.mlp.add(BatchNormalization(hidden_units[idx + 1]))
            elif layer_norm:
                self.mlp.add(LayerNormalization(hidden_units[idx + 1]))
        if dropout_rates[idx] > 0:
            self.mlp.add(Dropout(p=dropout_rates[idx]))
    if output_dim is not None:
        self.mlp.add(Dense(output_dim, use_bias=use_bias, kernel_initializer=get_initializer(initializer), kernel_regularizer=get_regularizer(regularizer), bias_regularizer=get_regularizer(regularizer)))
    if output_activation is not None:
        self.mlp.add(get_activation(output_activation))

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

def default_reset_params(m):
    if type(m) in [nn.Linear, nn.Conv1d]:
        nn.init.xavier_normal_(m.weight)
        if m.bias is not None:
            m.bias.data.fill_(0)

def custom_reset_params(m):
    if hasattr(m, 'init_weights'):
        m.init_weights()

def count_parameters(self, count_embedding=True):
    total_params = 0
    for name, param in self.named_parameters():
        if not count_embedding and 'embedding' in name:
            continue
        if param.requires_grad:
            total_params += param.numel()
    logging.info('Total number of parameters: {}.'.format(total_params))

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

