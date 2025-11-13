# Cluster 19

class SAMBlock(nn.Module):

    def __init__(self, num_layers, num_fields, embedding_dim, use_residual=False, interaction_type='SAM2E', aggregation='concat', dropout=0):
        super(SAMBlock, self).__init__()
        assert aggregation in ['concat', 'weighted_pooling', 'mean_pooling', 'sum_pooling']
        self.aggregation = aggregation
        if self.aggregation == 'weighted_pooling':
            self.weight = nn.Parameter(torch.ones(num_fields, 1))
        if interaction_type == 'SAM2A':
            assert aggregation == 'concat', 'Only aggregation=concat is supported for SAM2A.'
            self.layers = nn.ModuleList([SAM2A(num_fields, embedding_dim, dropout)])
        elif interaction_type == 'SAM2E':
            assert aggregation == 'concat', 'Only aggregation=concat is supported for SAM2E.'
            self.layers = nn.ModuleList([SAM2E(embedding_dim, dropout)])
        elif interaction_type == 'SAM3A':
            self.layers = nn.ModuleList([SAM3A(num_fields, embedding_dim, use_residual, dropout) for _ in range(num_layers)])
        elif interaction_type == 'SAM3E':
            self.layers = nn.ModuleList([SAM3E(embedding_dim, use_residual, dropout) for _ in range(num_layers)])
        else:
            raise ValueError('interaction_type={} not supported.'.format(interaction_type))

    def forward(self, F):
        for layer in self.layers:
            F = layer(F)
        if self.aggregation == 'concat':
            out = F.flatten(start_dim=1)
        elif self.aggregation == 'weighted_pooling':
            out = (F * self.weight).sum(dim=1)
        elif self.aggregation == 'mean_pooling':
            out = F.mean(dim=1)
        elif self.aggregation == 'sum_pooling':
            out = F.sum(dim=1)
        return out

def __init__(self, num_layers, num_fields, embedding_dim, use_residual=False, interaction_type='SAM2E', aggregation='concat', dropout=0):
    super(SAMBlock, self).__init__()
    assert aggregation in ['concat', 'weighted_pooling', 'mean_pooling', 'sum_pooling']
    self.aggregation = aggregation
    if self.aggregation == 'weighted_pooling':
        self.weight = nn.Parameter(torch.ones(num_fields, 1))
    if interaction_type == 'SAM2A':
        assert aggregation == 'concat', 'Only aggregation=concat is supported for SAM2A.'
        self.layers = nn.ModuleList([SAM2A(num_fields, embedding_dim, dropout)])
    elif interaction_type == 'SAM2E':
        assert aggregation == 'concat', 'Only aggregation=concat is supported for SAM2E.'
        self.layers = nn.ModuleList([SAM2E(embedding_dim, dropout)])
    elif interaction_type == 'SAM3A':
        self.layers = nn.ModuleList([SAM3A(num_fields, embedding_dim, use_residual, dropout) for _ in range(num_layers)])
    elif interaction_type == 'SAM3E':
        self.layers = nn.ModuleList([SAM3E(embedding_dim, use_residual, dropout) for _ in range(num_layers)])
    else:
        raise ValueError('interaction_type={} not supported.'.format(interaction_type))

class FilterLayer2(nn.Module):

    def __init__(self, max_length, hidden_size, hidden_dropout_prob, n_block):
        super(FilterLayer2, self).__init__()
        self.complex_weight = nn.Parameter(torch.randn(n_block, hidden_size // n_block, hidden_size // n_block, 2, dtype=torch.float32) * 0.02)
        self.out_dropout = nn.Dropout(hidden_dropout_prob)
        self.LayerNorm = LayerNorm(hidden_size, eps=1e-12)
        self.n = n_block

    def forward(self, input_tensor):
        batch, seq_len, hidden = input_tensor.shape
        A = torch.fft.rfft(input_tensor, dim=1, norm='ortho')
        A = A.view(batch, seq_len // 2 + 1, self.n, hidden // self.n)
        B = torch.view_as_complex(self.complex_weight)
        C = torch.einsum('blnd,ndd->blnd', A, B)
        C = C.view(batch, seq_len // 2 + 1, hidden)
        sequence_emb_fft = torch.fft.irfft(C, n=seq_len, dim=1, norm='ortho')
        hidden_states = self.out_dropout(sequence_emb_fft)
        hidden_states = self.LayerNorm(hidden_states + input_tensor)
        return hidden_states

def forward(self, input_tensor):
    batch, seq_len, hidden = input_tensor.shape
    A = torch.fft.rfft(input_tensor, dim=1, norm='ortho')
    A = A.view(batch, seq_len // 2 + 1, self.n, hidden // self.n)
    B = torch.view_as_complex(self.complex_weight)
    C = torch.einsum('blnd,ndd->blnd', A, B)
    C = C.view(batch, seq_len // 2 + 1, hidden)
    sequence_emb_fft = torch.fft.irfft(C, n=seq_len, dim=1, norm='ortho')
    hidden_states = self.out_dropout(sequence_emb_fft)
    hidden_states = self.LayerNorm(hidden_states + input_tensor)
    return hidden_states

class DynamicGRU(nn.Module):
    """DynamicGRU with GRU, AIGRU, AGRU, and AUGRU choices
        Reference: https://github.com/GitHub-HongweiZhang/prediction-flow/blob/master/prediction_flow/pytorch/nn/rnn.py
    """

    def __init__(self, input_size, hidden_size, bias=True, gru_type='AUGRU'):
        super(DynamicGRU, self).__init__()
        self.hidden_size = hidden_size
        self.gru_type = gru_type
        if gru_type == 'AUGRU':
            self.gru_cell = AUGRUCell(input_size, hidden_size, bias=bias)
        elif gru_type == 'AGRU':
            self.gru_cell = AGRUCell(input_size, hidden_size, bias=bias)

    def forward(self, packed_seq_emb, attn_score=None, h=None):
        assert isinstance(packed_seq_emb, PackedSequence) and isinstance(attn_score, PackedSequence), 'DynamicGRU supports only `PackedSequence` input.'
        x, batch_sizes, sorted_indices, unsorted_indices = packed_seq_emb
        attn, _, _, _ = attn_score
        if h == None:
            h = torch.zeros(batch_sizes[0], self.hidden_size, device=x.device)
        output_h = torch.zeros(batch_sizes[0], self.hidden_size, device=x.device)
        outputs = torch.zeros(x.shape[0], self.hidden_size, device=x.device)
        start = 0
        for batch_size in batch_sizes:
            _x = x[start:start + batch_size]
            _h = h[:batch_size]
            _attn = attn[start:start + batch_size]
            h = self.gru_cell(_x, _h, _attn)
            outputs[start:start + batch_size] = h
            output_h[:batch_size] = h
            start += batch_size
        return (PackedSequence(outputs, batch_sizes, sorted_indices, unsorted_indices), output_h[unsorted_indices])

def forward(self, packed_seq_emb, attn_score=None, h=None):
    assert isinstance(packed_seq_emb, PackedSequence) and isinstance(attn_score, PackedSequence), 'DynamicGRU supports only `PackedSequence` input.'
    x, batch_sizes, sorted_indices, unsorted_indices = packed_seq_emb
    attn, _, _, _ = attn_score
    if h == None:
        h = torch.zeros(batch_sizes[0], self.hidden_size, device=x.device)
    output_h = torch.zeros(batch_sizes[0], self.hidden_size, device=x.device)
    outputs = torch.zeros(x.shape[0], self.hidden_size, device=x.device)
    start = 0
    for batch_size in batch_sizes:
        _x = x[start:start + batch_size]
        _h = h[:batch_size]
        _attn = attn[start:start + batch_size]
        h = self.gru_cell(_x, _h, _attn)
        outputs[start:start + batch_size] = h
        output_h[:batch_size] = h
        start += batch_size
    return (PackedSequence(outputs, batch_sizes, sorted_indices, unsorted_indices), output_h[unsorted_indices])

class CCPM_ConvLayer(nn.Module):
    """
    Input X: tensor of shape (batch_size, 1, num_fields, embedding_dim)
    """

    def __init__(self, num_fields, channels=[3], kernel_heights=[3], activation='Tanh'):
        super(CCPM_ConvLayer, self).__init__()
        if not isinstance(kernel_heights, list):
            kernel_heights = [kernel_heights] * len(channels)
        elif len(kernel_heights) != len(channels):
            raise ValueError('channels={} and kernel_heights={} should have the same length.'.format(channels, kernel_heights))
        module_list = []
        self.channels = [1] + channels
        layers = len(kernel_heights)
        for i in range(1, len(self.channels)):
            in_channels = self.channels[i - 1]
            out_channels = self.channels[i]
            kernel_height = kernel_heights[i - 1]
            module_list.append(nn.ZeroPad2d((0, 0, kernel_height - 1, kernel_height - 1)))
            module_list.append(nn.Conv2d(in_channels, out_channels, kernel_size=(kernel_height, 1)))
            if i < layers:
                k = max(3, int((1 - pow(float(i) / layers, layers - i)) * num_fields))
            else:
                k = 3
            module_list.append(KMaxPooling(k, dim=2))
            module_list.append(get_activation(activation))
        self.conv_layer = nn.Sequential(*module_list)

    def forward(self, X):
        return self.conv_layer(X)

def __init__(self, num_fields, channels=[3], kernel_heights=[3], activation='Tanh'):
    super(CCPM_ConvLayer, self).__init__()
    if not isinstance(kernel_heights, list):
        kernel_heights = [kernel_heights] * len(channels)
    elif len(kernel_heights) != len(channels):
        raise ValueError('channels={} and kernel_heights={} should have the same length.'.format(channels, kernel_heights))
    module_list = []
    self.channels = [1] + channels
    layers = len(kernel_heights)
    for i in range(1, len(self.channels)):
        in_channels = self.channels[i - 1]
        out_channels = self.channels[i]
        kernel_height = kernel_heights[i - 1]
        module_list.append(nn.ZeroPad2d((0, 0, kernel_height - 1, kernel_height - 1)))
        module_list.append(nn.Conv2d(in_channels, out_channels, kernel_size=(kernel_height, 1)))
        if i < layers:
            k = max(3, int((1 - pow(float(i) / layers, layers - i)) * num_fields))
        else:
            k = 3
        module_list.append(KMaxPooling(k, dim=2))
        module_list.append(get_activation(activation))
    self.conv_layer = nn.Sequential(*module_list)

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

class DynamicGRU(nn.Module):
    """DynamicGRU with GRU, AIGRU, AGRU, and AUGRU choices
        Reference: https://github.com/GitHub-HongweiZhang/prediction-flow/blob/master/prediction_flow/pytorch/nn/rnn.py
    """

    def __init__(self, input_size, hidden_size, bias=True, gru_type='AUGRU'):
        super(DynamicGRU, self).__init__()
        self.hidden_size = hidden_size
        self.gru_type = gru_type
        if gru_type == 'AUGRU':
            self.gru_cell = AUGRUCell(input_size, hidden_size, bias=bias)
        elif gru_type == 'AGRU':
            self.gru_cell = AGRUCell(input_size, hidden_size, bias=bias)

    def forward(self, packed_seq_emb, attn_score=None, h=None):
        assert isinstance(packed_seq_emb, PackedSequence) and isinstance(attn_score, PackedSequence), 'DynamicGRU supports only `PackedSequence` input.'
        x, batch_sizes, sorted_indices, unsorted_indices = packed_seq_emb
        attn, _, _, _ = attn_score
        if h == None:
            h = torch.zeros(batch_sizes[0], self.hidden_size, device=x.device)
        output_h = torch.zeros(batch_sizes[0], self.hidden_size, device=x.device)
        outputs = torch.zeros(x.shape[0], self.hidden_size, device=x.device)
        start = 0
        for batch_size in batch_sizes:
            _x = x[start:start + batch_size]
            _h = h[:batch_size]
            _attn = attn[start:start + batch_size]
            h = self.gru_cell(_x, _h, _attn)
            outputs[start:start + batch_size] = h
            output_h[:batch_size] = h
            start += batch_size
        return (PackedSequence(outputs, batch_sizes, sorted_indices, unsorted_indices), output_h[unsorted_indices])

def forward(self, packed_seq_emb, attn_score=None, h=None):
    assert isinstance(packed_seq_emb, PackedSequence) and isinstance(attn_score, PackedSequence), 'DynamicGRU supports only `PackedSequence` input.'
    x, batch_sizes, sorted_indices, unsorted_indices = packed_seq_emb
    attn, _, _, _ = attn_score
    if h == None:
        h = torch.zeros(batch_sizes[0], self.hidden_size, device=x.device)
    output_h = torch.zeros(batch_sizes[0], self.hidden_size, device=x.device)
    outputs = torch.zeros(x.shape[0], self.hidden_size, device=x.device)
    start = 0
    for batch_size in batch_sizes:
        _x = x[start:start + batch_size]
        _h = h[:batch_size]
        _attn = attn[start:start + batch_size]
        h = self.gru_cell(_x, _h, _attn)
        outputs[start:start + batch_size] = h
        output_h[:batch_size] = h
        start += batch_size
    return (PackedSequence(outputs, batch_sizes, sorted_indices, unsorted_indices), output_h[unsorted_indices])

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

def __init__(self, kv):
    if isinstance(kv, str):
        kv = {kv: 1}
    self.kv_pairs = kv

def evaluate_metrics(y_true, y_pred, metrics, group_id=None):
    return_dict = OrderedDict()
    group_metrics = []
    for metric in metrics:
        if metric in ['logloss', 'binary_crossentropy']:
            return_dict[metric] = log_loss(y_true, y_pred, eps=1e-07)
        elif metric == 'AUC':
            return_dict[metric] = roc_auc_score(y_true, y_pred)
        elif metric in ['gAUC', 'avgAUC', 'MRR'] or metric.startswith('NDCG'):
            return_dict[metric] = 0
            group_metrics.append(metric)
        else:
            raise ValueError('metric={} not supported.'.format(metric))
    if len(group_metrics) > 0:
        assert group_id is not None, 'group_index is required.'
        metric_funcs = []
        for metric in group_metrics:
            try:
                metric_funcs.append(eval(metric))
            except:
                raise NotImplementedError('metrics={} not implemented.'.format(metric))
        score_df = pd.DataFrame({'group_index': group_id, 'y_true': y_true, 'y_pred': y_pred})
        results = []
        pool = mp.Pool(processes=mp.cpu_count() // 2)
        for idx, df in score_df.groupby('group_index'):
            results.append(pool.apply_async(evaluate_block, args=(df, metric_funcs)))
        pool.close()
        pool.join()
        results = [res.get() for res in results]
        sum_results = np.array(results).sum(0)
        average_result = list(sum_results[:, 0] / sum_results[:, 1])
        return_dict.update(dict(zip(group_metrics, average_result)))
    return return_dict

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

def update_vocab(self, word_list):
    new_words = 0
    for word in word_list:
        if word not in self.vocab:
            self.vocab[word] = self.vocab.get('__OOV__', 0) + new_words
            new_words += 1
    if new_words > 0:
        self.vocab['__OOV__'] = self.vocab_size()

def load_pretrained_vocab(self, feature_dtype, pretrain_path, expand_vocab=True):
    keys = load_pretrain_emb(pretrain_path, keys=['key'])
    keys = keys.astype(feature_dtype)
    if expand_vocab:
        vocab_size = self.vocab_size()
        for word in keys:
            if word not in self.vocab:
                self.vocab[word] = vocab_size
                vocab_size += 1

def transform(feature_encoder, ddf, filename, block_size=0):
    ddf = ddf.collect().to_pandas()
    if block_size > 0:
        pool = mp.Pool(mp.cpu_count() // 2)
        block_id = 0
        for idx in range(0, len(ddf), block_size):
            df_block = ddf.iloc[idx:idx + block_size]
            pool.apply_async(transform_block, args=(feature_encoder, df_block, '{}/part_{:05d}.parquet'.format(filename, block_id)))
            block_id += 1
        pool.close()
        pool.join()
    else:
        transform_block(feature_encoder, ddf, filename + '.parquet')

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

def fit_meta_col(self, col):
    name = col['name']
    feature_type = col['type']
    self.feature_map.features[name] = {'type': feature_type}
    if col.get('remap', True):
        tokenizer = Tokenizer(min_freq=1, remap=True)
        self.processor_dict[name + '::tokenizer'] = tokenizer

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

def get_activation(activation):
    if isinstance(activation, str):
        if activation.lower() == 'relu':
            return tf.keras.layers.Activation('relu')
        elif activation.lower() == 'sigmoid':
            return tf.keras.layers.Activation('sigmoid')
        elif activation.lower() == 'tanh':
            return tf.keras.layers.Activation('tanh')
        elif activation.lower() == 'softmax':
            return tf.keras.layers.Softmax()
        else:
            return getattr(tf.keras.layers, activation)()
    else:
        return activation

def get_optimizer(optimizer, learning_rate=0.001):
    if isinstance(optimizer, str):
        if optimizer.lower() == 'adam':
            return optimizers.Adam(learning_rate=learning_rate)
        elif optimizer.lower() == 'ftrl':
            return optimizers.Ftrl(learning_rate=learning_rate, l1_regularization_strength=0.1)
        elif optimizer.lower() == 'adagrad':
            return optimizers.Adagrad(learning_rate=learning_rate)
        else:
            try:
                return getattr(optimizers, optimizer)(learning_rate=learning_rate)
            except:
                raise ValueError('optimizer={} is not supported.'.format(optimizer))
    return optimizer

def get_loss(loss):
    if isinstance(loss, str):
        if loss in ['bce', 'binary_crossentropy', 'binary_cross_entropy']:
            loss = tf.keras.losses.BinaryCrossentropy(from_logits=False)
        else:
            raise ValueError('loss={} is not supported.'.format(loss))
    return loss

def get_regularizer(reg):
    if type(reg) in [int, float]:
        return l2(reg)
    elif isinstance(reg, str):
        if '(' in reg:
            try:
                return eval(reg)
            except:
                raise ValueError('reg={} is not supported.'.format(reg))
    return reg

def get_initializer(initializer, seed=20222023):
    if isinstance(initializer, str):
        try:
            if '(' in initializer:
                return eval(initializer.rstrip(')') + ', seed={})'.format(seed))
            else:
                return eval(initializer)(seed=seed)
        except:
            raise ValueError('initializer={} not supported.'.format(initializer))
    return initializer

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

class InnerProductInteraction(Layer):
    """ output: product_sum (bs x 1), 
                bi_interaction (bs * dim), 
                inner_product (bs x f^2/2), 
                elementwise_product (bs x f^2/2 x emb_dim)
    """

    def __init__(self, num_fields, output='product_sum'):
        super(InnerProductInteraction, self).__init__()
        self.output_type = output
        if output not in ['product_sum', 'bi_interaction', 'inner_product', 'elementwise_product']:
            raise ValueError('InnerProductInteraction output={} is not supported.'.format(output))
        if output == 'inner_product':
            self.interaction_units = int(num_fields * (num_fields - 1) / 2)
            self.triu_mask = tf.Variable(np.triu(np.ones((num_fields, num_fields)), 1).astype(bool), trainable=False)
        elif output == 'elementwise_product':
            self.triu_index = tf.Variable(np.triu_indices(num_fields, 1), trainable=False)

    def call(self, feature_emb):
        if self.output_type in ['product_sum', 'bi_interaction']:
            sum_of_square = tf.reduce_sum(feature_emb, axis=1) ** 2
            square_of_sum = tf.reduce_sum(feature_emb ** 2, axis=1)
            bi_interaction = (sum_of_square - square_of_sum) * 0.5
            if self.output_type == 'bi_interaction':
                return bi_interaction
            else:
                return tf.reduce_sum(bi_interaction, axis=-1, keepdims=True)
        elif self.output_type == 'inner_product':
            inner_product_matrix = tf.einsum('bij,bji->bii', feature_emb, feature_emb.transpose(1, 2))
            triu_values = tf.boolean_mask(inner_product_matrix, self.triu_mask)
            return tf.reshape(triu_values, (-1, self.interaction_units))
        elif self.output_type == 'elementwise_product':
            emb1 = tf.gather(feature_emb, self.triu_index[0], axis=1)
            emb2 = tf.gather(feature_emb, self.triu_index[1], axis=1)
            return emb1 * emb2

def __init__(self, num_fields, output='product_sum'):
    super(InnerProductInteraction, self).__init__()
    self.output_type = output
    if output not in ['product_sum', 'bi_interaction', 'inner_product', 'elementwise_product']:
        raise ValueError('InnerProductInteraction output={} is not supported.'.format(output))
    if output == 'inner_product':
        self.interaction_units = int(num_fields * (num_fields - 1) / 2)
        self.triu_mask = tf.Variable(np.triu(np.ones((num_fields, num_fields)), 1).astype(bool), trainable=False)
    elif output == 'elementwise_product':
        self.triu_index = tf.Variable(np.triu_indices(num_fields, 1), trainable=False)

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

def get_output_activation(self, task):
    if task == 'binary_classification':
        return tf.keras.layers.Activation('sigmoid')
    elif task == 'regression':
        return tf.identity
    else:
        raise NotImplementedError('task={} is not supported.'.format(task))

def get_optimizer(optimizer, params, lr):
    if isinstance(optimizer, str):
        if optimizer.lower() == 'adam':
            optimizer = 'Adam'
    try:
        optimizer = getattr(torch.optim, optimizer)(params, lr=lr)
    except:
        raise NotImplementedError('optimizer={} is not supported.'.format(optimizer))
    return optimizer

def get_loss(loss):
    if isinstance(loss, str):
        if loss in ['bce', 'binary_crossentropy', 'binary_cross_entropy']:
            loss = 'binary_cross_entropy'
    try:
        loss_fn = getattr(torch.functional.F, loss)
    except:
        try:
            loss_fn = eval('losses.' + loss)
        except:
            raise NotImplementedError('loss={} is not supported.'.format(loss))
    return loss_fn

def get_regularizer(reg):
    reg_pair = []
    if isinstance(reg, float):
        reg_pair.append((2, reg))
    elif isinstance(reg, str):
        try:
            if reg.startswith('l1(') or reg.startswith('l2('):
                reg_pair.append((int(reg[1]), float(reg.rstrip(')').split('(')[-1])))
            elif reg.startswith('l1_l2'):
                l1_reg, l2_reg = reg.rstrip(')').split('(')[-1].split(',')
                reg_pair.append((1, float(l1_reg)))
                reg_pair.append((2, float(l2_reg)))
            else:
                raise NotImplementedError
        except:
            raise NotImplementedError('regularizer={} is not supported.'.format(reg))
    return reg_pair

def get_activation(activation, hidden_units=None):
    if isinstance(activation, str):
        if activation.lower() in ['prelu', 'dice']:
            assert type(hidden_units) == int
        if activation.lower() == 'relu':
            return nn.ReLU()
        elif activation.lower() == 'sigmoid':
            return nn.Sigmoid()
        elif activation.lower() == 'tanh':
            return nn.Tanh()
        elif activation.lower() == 'softmax':
            return nn.Softmax(dim=-1)
        elif activation.lower() == 'prelu':
            return nn.PReLU(hidden_units, init=0.1)
        elif activation.lower() == 'dice':
            from fuxictr.pytorch.layers.activations import Dice
            return Dice(hidden_units)
        else:
            return getattr(nn, activation)()
    elif isinstance(activation, list):
        if hidden_units is not None:
            assert len(activation) == len(hidden_units)
            return [get_activation(act, units) for act, units in zip(activation, hidden_units)]
        else:
            return [get_activation(act) for act in activation]
    return activation

def get_initializer(initializer):
    if isinstance(initializer, str):
        try:
            initializer = eval(initializer)
        except:
            raise ValueError('initializer={} is not supported.'.format(initializer))
    return initializer

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

class HolographicInteraction(nn.Module):

    def __init__(self, num_fields, interaction_type='circular_convolution'):
        super(HolographicInteraction, self).__init__()
        self.interaction_type = interaction_type
        if self.interaction_type == 'circular_correlation':
            self.conj_sign = nn.Parameter(torch.tensor([1.0, -1.0]), requires_grad=False)
        self.triu_index = nn.Parameter(torch.triu_indices(num_fields, num_fields, offset=1), requires_grad=False)

    def forward(self, feature_emb):
        emb1 = torch.index_select(feature_emb, 1, self.triu_index[0])
        emb2 = torch.index_select(feature_emb, 1, self.triu_index[1])
        if self.interaction_type == 'hadamard_product':
            interact_tensor = emb1 * emb2
        elif self.interaction_type == 'circular_convolution':
            fft1 = torch.view_as_real(torch.fft.fft(emb1))
            fft2 = torch.view_as_real(torch.fft.fft(emb2))
            fft_product = torch.stack([fft1[..., 0] * fft2[..., 0] - fft1[..., 1] * fft2[..., 1], fft1[..., 0] * fft2[..., 1] + fft1[..., 1] * fft2[..., 0]], dim=-1)
            interact_tensor = torch.view_as_real(torch.fft.ifft(torch.view_as_complex(fft_product)))[..., 0]
        elif self.interaction_type == 'circular_correlation':
            fft1_emb = torch.view_as_real(torch.fft.fft(emb1))
            fft1 = fft1_emb * self.conj_sign.expand_as(fft1_emb)
            fft2 = torch.view_as_real(torch.fft.fft(emb2))
            fft_product = torch.stack([fft1[..., 0] * fft2[..., 0] - fft1[..., 1] * fft2[..., 1], fft1[..., 0] * fft2[..., 1] + fft1[..., 1] * fft2[..., 0]], dim=-1)
            interact_tensor = torch.view_as_real(torch.fft.ifft(torch.view_as_complex(fft_product)))[..., 0]
        else:
            raise ValueError('interaction_type={} not supported.'.format(self.interaction_type))
        return interact_tensor

def forward(self, feature_emb):
    emb1 = torch.index_select(feature_emb, 1, self.triu_index[0])
    emb2 = torch.index_select(feature_emb, 1, self.triu_index[1])
    if self.interaction_type == 'hadamard_product':
        interact_tensor = emb1 * emb2
    elif self.interaction_type == 'circular_convolution':
        fft1 = torch.view_as_real(torch.fft.fft(emb1))
        fft2 = torch.view_as_real(torch.fft.fft(emb2))
        fft_product = torch.stack([fft1[..., 0] * fft2[..., 0] - fft1[..., 1] * fft2[..., 1], fft1[..., 0] * fft2[..., 1] + fft1[..., 1] * fft2[..., 0]], dim=-1)
        interact_tensor = torch.view_as_real(torch.fft.ifft(torch.view_as_complex(fft_product)))[..., 0]
    elif self.interaction_type == 'circular_correlation':
        fft1_emb = torch.view_as_real(torch.fft.fft(emb1))
        fft1 = fft1_emb * self.conj_sign.expand_as(fft1_emb)
        fft2 = torch.view_as_real(torch.fft.fft(emb2))
        fft_product = torch.stack([fft1[..., 0] * fft2[..., 0] - fft1[..., 1] * fft2[..., 1], fft1[..., 0] * fft2[..., 1] + fft1[..., 1] * fft2[..., 0]], dim=-1)
        interact_tensor = torch.view_as_real(torch.fft.ifft(torch.view_as_complex(fft_product)))[..., 0]
    else:
        raise ValueError('interaction_type={} not supported.'.format(self.interaction_type))
    return interact_tensor

class InnerProductInteraction(nn.Module):
    """ output: product_sum (bs x 1), 
                bi_interaction (bs * dim), 
                inner_product (bs x f^2/2), 
                elementwise_product (bs x f^2/2 x emb_dim)
    """

    def __init__(self, num_fields, output='product_sum'):
        super(InnerProductInteraction, self).__init__()
        self._output_type = output
        if output not in ['product_sum', 'bi_interaction', 'inner_product', 'elementwise_product']:
            raise ValueError('InnerProductInteraction output={} is not supported.'.format(output))
        if output == 'inner_product':
            self.interaction_units = int(num_fields * (num_fields - 1) / 2)
            self.triu_mask = nn.Parameter(torch.triu(torch.ones(num_fields, num_fields), 1).bool(), requires_grad=False)
        elif output == 'elementwise_product':
            self.triu_index = nn.Parameter(torch.triu_indices(num_fields, num_fields, offset=1), requires_grad=False)

    def forward(self, feature_emb):
        if self._output_type in ['product_sum', 'bi_interaction']:
            sum_of_square = torch.sum(feature_emb, dim=1) ** 2
            square_of_sum = torch.sum(feature_emb ** 2, dim=1)
            bi_interaction = (sum_of_square - square_of_sum) * 0.5
            if self._output_type == 'bi_interaction':
                return bi_interaction
            else:
                return bi_interaction.sum(dim=-1, keepdim=True)
        elif self._output_type == 'inner_product':
            inner_product_matrix = torch.bmm(feature_emb, feature_emb.transpose(1, 2))
            triu_values = torch.masked_select(inner_product_matrix, self.triu_mask)
            return triu_values.view(-1, self.interaction_units)
        elif self._output_type == 'elementwise_product':
            emb1 = torch.index_select(feature_emb, 1, self.triu_index[0])
            emb2 = torch.index_select(feature_emb, 1, self.triu_index[1])
            return emb1 * emb2

def __init__(self, num_fields, output='product_sum'):
    super(InnerProductInteraction, self).__init__()
    self._output_type = output
    if output not in ['product_sum', 'bi_interaction', 'inner_product', 'elementwise_product']:
        raise ValueError('InnerProductInteraction output={} is not supported.'.format(output))
    if output == 'inner_product':
        self.interaction_units = int(num_fields * (num_fields - 1) / 2)
        self.triu_mask = nn.Parameter(torch.triu(torch.ones(num_fields, num_fields), 1).bool(), requires_grad=False)
    elif output == 'elementwise_product':
        self.triu_index = nn.Parameter(torch.triu_indices(num_fields, num_fields, offset=1), requires_grad=False)

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

def get_output_activation(self, task):
    if task == 'binary_classification':
        return nn.Sigmoid()
    elif task == 'regression':
        return nn.Identity()
    else:
        raise NotImplementedError('task={} is not supported.'.format(task))

