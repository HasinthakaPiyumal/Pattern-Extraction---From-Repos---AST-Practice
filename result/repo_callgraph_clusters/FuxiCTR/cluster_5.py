# Cluster 5

class RegulationModule(nn.Module):

    def __init__(self, num_fields, embedding_dim, tau=1, use_bn=False):
        super(RegulationModule, self).__init__()
        self.tau = tau
        self.embedding_dim = embedding_dim
        self.use_bn = use_bn
        self.g1 = nn.Parameter(torch.ones(num_fields))
        self.g2 = nn.Parameter(torch.ones(num_fields))
        if self.use_bn:
            self.bn1 = nn.BatchNorm1d(num_fields * embedding_dim)
            self.bn2 = nn.BatchNorm1d(num_fields * embedding_dim)

    def forward(self, X):
        g1 = (self.g1 / self.tau).softmax(dim=-1).unsqueeze(-1).repeat(1, self.embedding_dim).view(1, -1)
        g2 = (self.g2 / self.tau).softmax(dim=-1).unsqueeze(-1).repeat(1, self.embedding_dim).view(1, -1)
        out1, out2 = (g1 * X, g2 * X)
        if self.use_bn:
            out1, out2 = (self.bn1(out1), self.bn2(out2))
        return (out1, out2)

def forward(self, X):
    g1 = (self.g1 / self.tau).softmax(dim=-1).unsqueeze(-1).repeat(1, self.embedding_dim).view(1, -1)
    g2 = (self.g2 / self.tau).softmax(dim=-1).unsqueeze(-1).repeat(1, self.embedding_dim).view(1, -1)
    out1, out2 = (g1 * X, g2 * X)
    if self.use_bn:
        out1, out2 = (self.bn1(out1), self.bn2(out2))
    return (out1, out2)

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

class GraphLayer(nn.Module):

    def __init__(self, num_fields, embedding_dim):
        super(GraphLayer, self).__init__()
        self.W_in = torch.nn.Parameter(torch.Tensor(num_fields, embedding_dim, embedding_dim))
        self.W_out = torch.nn.Parameter(torch.Tensor(num_fields, embedding_dim, embedding_dim))
        nn.init.xavier_normal_(self.W_in)
        nn.init.xavier_normal_(self.W_out)
        self.bias_p = nn.Parameter(torch.zeros(embedding_dim))

    def forward(self, g, h):
        h_out = torch.matmul(self.W_out, h.unsqueeze(-1)).squeeze(-1)
        aggr = torch.bmm(g, h_out)
        a = torch.matmul(self.W_in, aggr.unsqueeze(-1)).squeeze(-1) + self.bias_p
        return a

def forward(self, g, h):
    h_out = torch.matmul(self.W_out, h.unsqueeze(-1)).squeeze(-1)
    aggr = torch.bmm(g, h_out)
    a = torch.matmul(self.W_in, aggr.unsqueeze(-1)).squeeze(-1) + self.bias_p
    return a

class HOFM(BaseModel):

    def __init__(self, feature_map, model_id='HOFM', gpu=-1, learning_rate=0.001, order=3, embedding_dim=10, reuse_embedding=False, embedding_dropout=0, regularizer=None, **kwargs):
        super(HOFM, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=regularizer, net_regularizer=regularizer, **kwargs)
        self.order = order
        assert order >= 2, 'order >= 2 is required in HOFM!'
        self.reuse_embedding = reuse_embedding
        if reuse_embedding:
            assert isinstance(embedding_dim, int), 'embedding_dim should be an integer when reuse_embedding=True.'
            self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        else:
            if not isinstance(embedding_dim, list):
                embedding_dim = [embedding_dim] * (order - 1)
            self.embedding_layers = nn.ModuleList([FeatureEmbedding(feature_map, embedding_dim[i]) for i in range(order - 1)])
        self.inner_product_layer = InnerProductInteraction(feature_map.num_fields)
        self.lr_layer = LogisticRegression(feature_map, use_bias=True)
        self.field_conjunction_dict = dict()
        for order_i in range(3, self.order + 1):
            order_i_conjunction = zip(*list(combinations(range(feature_map.num_fields), order_i)))
            for k, field_index in enumerate(order_i_conjunction):
                self.field_conjunction_dict[order_i, k] = torch.LongTensor(field_index)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        """
        Inputs: [X, y]
        """
        X = self.get_inputs(inputs)
        y_pred = self.lr_layer(X)
        if self.reuse_embedding:
            feature_emb = self.embedding_layer(X)
        for i in range(2, self.order + 1):
            order_i_out = self.high_order_interaction(feature_emb if self.reuse_embedding else self.embedding_layers[i - 2](X), order_i=i)
            y_pred += order_i_out
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred}
        return return_dict

    def high_order_interaction(self, feature_emb, order_i):
        if order_i == 2:
            interaction_out = self.inner_product_layer(feature_emb)
        elif order_i > 2:
            index = self.field_conjunction_dict[order_i, 0].to(self.device)
            hadamard_product = torch.index_select(feature_emb, 1, index)
            for k in range(1, order_i):
                index = self.field_conjunction_dict[order_i, k].to(self.device)
                hadamard_product = hadamard_product * torch.index_select(feature_emb, 1, index)
            interaction_out = hadamard_product.sum((1, 2)).view(-1, 1)
        return interaction_out

def high_order_interaction(self, feature_emb, order_i):
    if order_i == 2:
        interaction_out = self.inner_product_layer(feature_emb)
    elif order_i > 2:
        index = self.field_conjunction_dict[order_i, 0].to(self.device)
        hadamard_product = torch.index_select(feature_emb, 1, index)
        for k in range(1, order_i):
            index = self.field_conjunction_dict[order_i, k].to(self.device)
            hadamard_product = hadamard_product * torch.index_select(feature_emb, 1, index)
        interaction_out = hadamard_product.sum((1, 2)).view(-1, 1)
    return interaction_out

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

class SAM2A(nn.Module):

    def __init__(self, num_fields, embedding_dim, dropout=0):
        super(SAM2A, self).__init__()
        self.W = nn.Parameter(torch.ones(num_fields, num_fields, embedding_dim))
        self.dropout = nn.Dropout(p=dropout) if dropout > 0 else None

    def forward(self, F):
        S = torch.bmm(F, F.transpose(1, 2))
        out = S.unsqueeze(-1) * self.W
        if self.dropout:
            out = self.dropout(out)
        return out

def forward(self, F):
    S = torch.bmm(F, F.transpose(1, 2))
    out = S.unsqueeze(-1) * self.W
    if self.dropout:
        out = self.dropout(out)
    return out

class SAM2E(nn.Module):

    def __init__(self, embedding_dim, dropout=0):
        super(SAM2E, self).__init__()
        self.dropout = nn.Dropout(p=dropout) if dropout > 0 else None

    def forward(self, F):
        S = torch.bmm(F, F.transpose(1, 2))
        U = torch.einsum('bnd,bmd->bnmd', F, F)
        out = S.unsqueeze(-1) * U
        if self.dropout:
            out = self.dropout(out)
        return out

def forward(self, F):
    S = torch.bmm(F, F.transpose(1, 2))
    U = torch.einsum('bnd,bmd->bnmd', F, F)
    out = S.unsqueeze(-1) * U
    if self.dropout:
        out = self.dropout(out)
    return out

class SAM3A(nn.Module):

    def __init__(self, num_fields, embedding_dim, use_residual=True, dropout=0):
        super(SAM3A, self).__init__()
        self.W = nn.Parameter(torch.ones(num_fields, num_fields, embedding_dim))
        self.K = nn.Linear(embedding_dim, embedding_dim, bias=False)
        self.use_residual = use_residual
        if use_residual:
            self.Q = nn.Linear(embedding_dim, embedding_dim, bias=False)
        self.dropout = nn.Dropout(p=dropout) if dropout > 0 else None

    def forward(self, F):
        S = torch.bmm(F, self.K(F).transpose(1, 2))
        out = (S.unsqueeze(-1) * self.W).sum(dim=2)
        if self.use_residual:
            out += self.Q(F)
        if self.dropout:
            out = self.dropout(out)
        return out

def forward(self, F):
    S = torch.bmm(F, self.K(F).transpose(1, 2))
    out = (S.unsqueeze(-1) * self.W).sum(dim=2)
    if self.use_residual:
        out += self.Q(F)
    if self.dropout:
        out = self.dropout(out)
    return out

class SAM3E(nn.Module):

    def __init__(self, embedding_dim, use_residual=True, dropout=0):
        super(SAM3E, self).__init__()
        self.K = nn.Linear(embedding_dim, embedding_dim, bias=False)
        self.use_residual = use_residual
        if use_residual:
            self.Q = nn.Linear(embedding_dim, embedding_dim, bias=False)
        self.dropout = nn.Dropout(p=dropout) if dropout > 0 else None

    def forward(self, F):
        S = torch.bmm(F, self.K(F).transpose(1, 2))
        U = torch.einsum('bnd,bmd->bnmd', F, F)
        out = (S.unsqueeze(-1) * U).sum(dim=2)
        if self.use_residual:
            out += self.Q(F)
        if self.dropout:
            out = self.dropout(out)
        return out

def forward(self, F):
    S = torch.bmm(F, self.K(F).transpose(1, 2))
    U = torch.einsum('bnd,bmd->bnmd', F, F)
    out = (S.unsqueeze(-1) * U).sum(dim=2)
    if self.use_residual:
        out += self.Q(F)
    if self.dropout:
        out = self.dropout(out)
    return out

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

class MultiInterestExtractorLayer(nn.Module):

    def __init__(self, model_dim=64, ffn_dim=64, num_heads=4, attn_dropout=0.0, net_dropout=0.0, layer_norm=True, use_residual=True, attn_hidden_units=[80, 40], attn_activation='ReLU', use_pos_emb=True, pos_emb_dim=8, max_seq_len=10):
        super(MultiInterestExtractorLayer, self).__init__()
        assert model_dim % num_heads == 0, 'model_dim={} is not divisible by num_heads={}'.format(model_dim, num_heads)
        self.head_dim = model_dim // num_heads
        self.num_heads = num_heads
        self.use_residual = use_residual
        self.scale = self.head_dim ** 0.5
        self.W_qkv = nn.Linear(model_dim, 3 * model_dim, bias=False)
        self.attention = ScaledDotProductAttention(attn_dropout)
        self.W_o = nn.ModuleList([nn.Linear(self.head_dim, model_dim, bias=False) for _ in range(num_heads)])
        self.dropout = nn.ModuleList([nn.Dropout(net_dropout) for _ in range(num_heads)]) if net_dropout > 0 else None
        self.layer_norm = nn.ModuleList([nn.LayerNorm(model_dim) for _ in range(num_heads)]) if layer_norm else None
        self.ffn = nn.ModuleList([nn.Sequential(nn.Linear(model_dim, ffn_dim), nn.ReLU(), nn.Linear(ffn_dim, model_dim)) for _ in range(num_heads)])
        self.target_attention = nn.ModuleList([TargetAttention(model_dim, attention_hidden_units=attn_hidden_units, attention_activation=attn_activation, attention_dropout=attn_dropout, use_pos_emb=use_pos_emb, pos_emb_dim=pos_emb_dim, max_seq_len=max_seq_len) for _ in range(num_heads)])

    def forward(self, sequence_emb, target_emb, attn_mask=None, pad_mask=None):
        query, key, value = torch.chunk(self.W_qkv(sequence_emb), chunks=3, dim=-1)
        batch_size = query.size(0)
        query = query.view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
        key = key.view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
        value = value.view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
        attn, _ = self.attention(query, key, value, scale=self.scale, mask=attn_mask)
        attn_heads = torch.chunk(attn, chunks=self.num_heads, dim=1)
        interests = []
        for idx, h_head in enumerate(attn_heads):
            s = self.W_o[idx](h_head.squeeze(1))
            if self.dropout is not None:
                s = self.dropout[idx](s)
            if self.use_residual:
                s += sequence_emb
            if self.layer_norm is not None:
                s = self.layer_norm[idx](s)
            head_out = self.ffn[idx](s)
            if self.use_residual:
                head_out += s
            interest_emb = self.target_attention[idx](head_out, target_emb, mask=pad_mask)
            interests.append(interest_emb)
        return interests

def forward(self, sequence_emb, target_emb, attn_mask=None, pad_mask=None):
    query, key, value = torch.chunk(self.W_qkv(sequence_emb), chunks=3, dim=-1)
    batch_size = query.size(0)
    query = query.view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
    key = key.view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
    value = value.view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
    attn, _ = self.attention(query, key, value, scale=self.scale, mask=attn_mask)
    attn_heads = torch.chunk(attn, chunks=self.num_heads, dim=1)
    interests = []
    for idx, h_head in enumerate(attn_heads):
        s = self.W_o[idx](h_head.squeeze(1))
        if self.dropout is not None:
            s = self.dropout[idx](s)
        if self.use_residual:
            s += sequence_emb
        if self.layer_norm is not None:
            s = self.layer_norm[idx](s)
        head_out = self.ffn[idx](s)
        if self.use_residual:
            head_out += s
        interest_emb = self.target_attention[idx](head_out, target_emb, mask=pad_mask)
        interests.append(interest_emb)
    return interests

class TargetAttention(nn.Module):

    def __init__(self, model_dim=64, attention_hidden_units=[80, 40], attention_activation='ReLU', attention_dropout=0, use_pos_emb=True, pos_emb_dim=8, max_seq_len=10):
        super(TargetAttention, self).__init__()
        self.model_dim = model_dim
        self.use_pos_emb = use_pos_emb
        if self.use_pos_emb:
            self.pos_emb = nn.Parameter(torch.zeros(max_seq_len, pos_emb_dim))
            self.W_proj = nn.Linear(model_dim + pos_emb_dim, model_dim)
        self.attn_mlp = MLP_Block(input_dim=model_dim * 4, output_dim=1, hidden_units=attention_hidden_units, hidden_activations=attention_activation, output_activation=None, dropout_rates=attention_dropout, batch_norm=False)

    def forward(self, sequence_emb, target_emb, mask=None):
        """
        target_item: b x emd
        history_sequence: b x len x emb
        mask: mask of history_sequence, 0 for masked positions
        """
        seq_len = sequence_emb.size(1)
        target_emb = target_emb.unsqueeze(1).expand(-1, seq_len, -1)
        if self.use_pos_emb:
            target_emb = torch.cat([target_emb, self.pos_emb.expand(target_emb.size(0), -1, -1)], dim=-1)
            target_emb = self.W_proj(target_emb)
        din_concat = torch.cat([target_emb, sequence_emb, target_emb - sequence_emb, target_emb * sequence_emb], dim=-1)
        attn_score = self.attn_mlp(din_concat.view(-1, 4 * target_emb.size(-1)))
        attn_score = attn_score.view(-1, seq_len)
        if mask is not None:
            attn_score = attn_score.masked_fill_(mask.float() == 0, -1000000000.0)
            attn_score = attn_score.softmax(dim=-1)
        output = (attn_score.unsqueeze(-1) * sequence_emb).sum(dim=1)
        return output

def forward(self, sequence_emb, target_emb, mask=None):
    """
        target_item: b x emd
        history_sequence: b x len x emb
        mask: mask of history_sequence, 0 for masked positions
        """
    seq_len = sequence_emb.size(1)
    target_emb = target_emb.unsqueeze(1).expand(-1, seq_len, -1)
    if self.use_pos_emb:
        target_emb = torch.cat([target_emb, self.pos_emb.expand(target_emb.size(0), -1, -1)], dim=-1)
        target_emb = self.W_proj(target_emb)
    din_concat = torch.cat([target_emb, sequence_emb, target_emb - sequence_emb, target_emb * sequence_emb], dim=-1)
    attn_score = self.attn_mlp(din_concat.view(-1, 4 * target_emb.size(-1)))
    attn_score = attn_score.view(-1, seq_len)
    if mask is not None:
        attn_score = attn_score.masked_fill_(mask.float() == 0, -1000000000.0)
        attn_score = attn_score.softmax(dim=-1)
    output = (attn_score.unsqueeze(-1) * sequence_emb).sum(dim=1)
    return output

class FFMv2(BaseModel):

    def __init__(self, feature_map, model_id='FFMv2', gpu=-1, learning_rate=0.001, embedding_dim=2, regularizer=None, **kwargs):
        super(FFMv2, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=regularizer, net_regularizer=regularizer, **kwargs)
        self.num_fields = feature_map.num_fields
        self.embedding_dim = embedding_dim
        self.lr_layer = LogisticRegression(feature_map, use_bias=True)
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim * (self.num_fields - 1))
        self.triu_mask = torch.triu(torch.ones(self.num_fields, self.num_fields - 1), 0).bool().to(self.device)
        self.tril_mask = torch.tril(torch.ones(self.num_fields, self.num_fields - 1), -1).bool().to(self.device)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        """
        Inputs: [X, y]
        """
        X = self.get_inputs(inputs)
        lr_out = self.lr_layer(X)
        field_wise_emb = self.embedding_layer(X).view(-1, self.num_fields, self.num_fields - 1, self.embedding_dim)
        ffm_out = self.ffm_interaction(field_wise_emb)
        y_pred = lr_out + ffm_out
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred}
        return return_dict

    def ffm_interaction(self, field_wise_emb):
        batch_size = field_wise_emb.shape[0]
        upper_tensor = torch.masked_select(field_wise_emb, self.triu_mask.unsqueeze(-1))
        lower_tensor = torch.masked_select(field_wise_emb.transpose(1, 2), self.tril_mask.t().unsqueeze(-1))
        out = (upper_tensor * lower_tensor).view(batch_size, -1).sum(dim=-1, keepdim=True)
        return out

def ffm_interaction(self, field_wise_emb):
    batch_size = field_wise_emb.shape[0]
    upper_tensor = torch.masked_select(field_wise_emb, self.triu_mask.unsqueeze(-1))
    lower_tensor = torch.masked_select(field_wise_emb.transpose(1, 2), self.tril_mask.t().unsqueeze(-1))
    out = (upper_tensor * lower_tensor).view(batch_size, -1).sum(dim=-1, keepdim=True)
    return out

class LorentzFM(BaseModel):

    def __init__(self, feature_map, model_id='LorentzFM', gpu=-1, learning_rate=0.001, embedding_dim=10, embedding_dropout=0, regularizer=None, **kwargs):
        super(LorentzFM, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=regularizer, net_regularizer=regularizer, **kwargs)
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        self.inner_product_layer = InnerProductInteraction(feature_map.num_fields, output='inner_product')
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        X = self.get_inputs(inputs)
        feature_emb = self.embedding_layer(X)
        inner_product = self.inner_product_layer(feature_emb)
        zeroth_components = self.get_zeroth_components(feature_emb)
        y_pred = self.triangle_pooling(inner_product, zeroth_components)
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred}
        return return_dict

    def get_zeroth_components(self, feature_emb):
        """
        compute the 0th component
        """
        sum_of_square = torch.sum(feature_emb ** 2, dim=-1)
        zeroth_components = torch.sqrt(sum_of_square + 1)
        return zeroth_components

    def triangle_pooling(self, inner_product, zeroth_components):
        """
        T(u,v) = (1 - <u, v>L - u0 - v0) / (u0 * v0)
               = (1 + u0 * v0 - inner_product - u0 - v0) / (u0 * v0)
               = 1 + (1 - inner_product - u0 - v0) / (u0 * v0)
        """
        num_fields = zeroth_components.size(1)
        p, q = zip(*list(combinations(range(num_fields), 2)))
        u0, v0 = (zeroth_components[:, p], zeroth_components[:, q])
        score_tensor = 1 + torch.div(1 - inner_product - u0 - v0, u0 * v0)
        output = torch.sum(score_tensor, dim=1, keepdim=True)
        return output

def triangle_pooling(self, inner_product, zeroth_components):
    """
        T(u,v) = (1 - <u, v>L - u0 - v0) / (u0 * v0)
               = (1 + u0 * v0 - inner_product - u0 - v0) / (u0 * v0)
               = 1 + (1 - inner_product - u0 - v0) / (u0 * v0)
        """
    num_fields = zeroth_components.size(1)
    p, q = zip(*list(combinations(range(num_fields), 2)))
    u0, v0 = (zeroth_components[:, p], zeroth_components[:, q])
    score_tensor = 1 + torch.div(1 - inner_product - u0 - v0, u0 * v0)
    output = torch.sum(score_tensor, dim=1, keepdim=True)
    return output

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

def get_labels(self, inputs):
    """ Please override get_labels() when using multiple labels!
        """
    labels = self.feature_map.labels
    batch_dict = inputs[0]
    y = batch_dict[labels[0]].to(self.device)
    return y.float().view(-1, 1)

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

def get_labels(self, inputs):
    """ Please override get_labels() when using multiple labels!
        """
    labels = self.feature_map.labels
    batch_dict = inputs[0]
    y = batch_dict[labels[0]].to(self.device)
    return y.float().view(-1, 1)

class MultiHeadTopKAttention(nn.Module):

    def __init__(self, input_dim=64, Kc=0, embedding_dim=16, attention_dim=64, topk=50, num_heads=1, dropout_rate=0):
        super(MultiHeadTopKAttention, self).__init__()
        assert attention_dim % num_heads == 0, 'attention_dim={} is not divisible by num_heads={}'.format(attention_dim, num_heads)
        self.num_heads = num_heads
        self.topk = topk
        self.head_dim = attention_dim // num_heads
        self.scale = self.head_dim ** 0.5
        self.Kc = Kc
        self.Kc_dim = Kc * embedding_dim
        self.Kh_dim = input_dim - self.Kc_dim
        self.W_q = nn.Linear(self.Kh_dim, attention_dim, bias=False)
        self.W_h = nn.Linear(self.Kh_dim, attention_dim, bias=False)
        self.W_v = nn.Linear(input_dim, attention_dim, bias=False)
        self.W_o = nn.Linear(attention_dim, input_dim, bias=False)
        if self.Kc > 0:
            self.W_c = nn.Parameter(torch.Tensor(num_heads, Kc, embedding_dim))
            self.beta = nn.Linear(Kc, 1, bias=False)
        self.dropout = nn.Dropout(dropout_rate) if dropout_rate > 0 else None

    def forward(self, target_item, item_sequence, mask=None):
        """
        target_item: b x emb
        item_feat_seq: b x len x emb
        cross_feat_seq: b x len x emb
        mask: mask of history_sequence, 0 for masked positions
        """
        batch_size = target_item.size(0)
        if self.Kc > 0:
            item_feat_seq, cross_feat_seq = torch.split(item_sequence, [self.Kh_dim, self.Kc_dim], dim=-1)
            key_c = (cross_feat_seq.view(batch_size, self.Kc, -1).unsqueeze(1) * self.W_c.unsqueeze(0)).sum(-1)
            key_c_bias = self.beta(key_c)
        else:
            item_feat_seq = item_sequence
        query = self.W_q(target_item)
        key_h = self.W_h(item_feat_seq)
        value = self.W_v(item_sequence)
        query = query.view(batch_size, 1, self.num_heads, self.head_dim).transpose(1, 2)
        key_h = key_h.view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
        value = value.view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
        scores = torch.matmul(query, key_h.transpose(-1, -2)) / self.scale
        if self.Kc > 0:
            scores += key_c_bias.view(batch_size, self.num_heads, 1, 1)
        if mask is not None:
            mask = mask.view(batch_size, 1, 1, -1).expand(batch_size, self.num_heads, 1, -1)
            scores = scores.masked_fill_(mask.float() == 0, -1000000000.0)
        topk = min(self.topk, scores.shape[-1])
        topk_scores, topk_index = scores.topk(topk, dim=-1, largest=True, sorted=True)
        topk_value = torch.gather(value, 2, topk_index.transpose(-1, -2).expand(-1, -1, -1, value.shape[-1]))
        attention = topk_scores.softmax(dim=-1)
        if self.dropout is not None:
            attention = self.dropout(attention)
        output = torch.matmul(attention, topk_value)
        output = output.transpose(1, 2).contiguous().view(-1, self.num_heads * self.head_dim)
        output = self.W_o(output)
        return output

def forward(self, target_item, item_sequence, mask=None):
    """
        target_item: b x emb
        item_feat_seq: b x len x emb
        cross_feat_seq: b x len x emb
        mask: mask of history_sequence, 0 for masked positions
        """
    batch_size = target_item.size(0)
    if self.Kc > 0:
        item_feat_seq, cross_feat_seq = torch.split(item_sequence, [self.Kh_dim, self.Kc_dim], dim=-1)
        key_c = (cross_feat_seq.view(batch_size, self.Kc, -1).unsqueeze(1) * self.W_c.unsqueeze(0)).sum(-1)
        key_c_bias = self.beta(key_c)
    else:
        item_feat_seq = item_sequence
    query = self.W_q(target_item)
    key_h = self.W_h(item_feat_seq)
    value = self.W_v(item_sequence)
    query = query.view(batch_size, 1, self.num_heads, self.head_dim).transpose(1, 2)
    key_h = key_h.view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
    value = value.view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
    scores = torch.matmul(query, key_h.transpose(-1, -2)) / self.scale
    if self.Kc > 0:
        scores += key_c_bias.view(batch_size, self.num_heads, 1, 1)
    if mask is not None:
        mask = mask.view(batch_size, 1, 1, -1).expand(batch_size, self.num_heads, 1, -1)
        scores = scores.masked_fill_(mask.float() == 0, -1000000000.0)
    topk = min(self.topk, scores.shape[-1])
    topk_scores, topk_index = scores.topk(topk, dim=-1, largest=True, sorted=True)
    topk_value = torch.gather(value, 2, topk_index.transpose(-1, -2).expand(-1, -1, -1, value.shape[-1]))
    attention = topk_scores.softmax(dim=-1)
    if self.dropout is not None:
        attention = self.dropout(attention)
    output = torch.matmul(attention, topk_value)
    output = output.transpose(1, 2).contiguous().view(-1, self.num_heads * self.head_dim)
    output = self.W_o(output)
    return output

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

def get_labels(self, inputs):
    """ Please override get_labels() when using multiple labels!
        """
    labels = self.feature_map.labels
    batch_dict = inputs[0]
    y = batch_dict[labels[0]].to(self.device)
    return y.float().view(-1, 1)

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

def get_labels(self, inputs):
    """ Please override get_labels() when using multiple labels!
        """
    labels = self.feature_map.labels
    batch_dict = inputs[0]
    y = batch_dict[labels[0]].to(self.device)
    return y.float().view(-1, 1)

class FeatureSelection(nn.Module):

    def __init__(self, feature_map, feature_dim, embedding_dim, fs_hidden_units=[], fs1_context=[], fs2_context=[]):
        super(FeatureSelection, self).__init__()
        self.fs1_context = fs1_context
        if len(fs1_context) == 0:
            self.fs1_ctx_bias = nn.Parameter(torch.zeros(1, embedding_dim))
        else:
            self.fs1_ctx_emb = FeatureEmbedding(feature_map, embedding_dim, required_feature_columns=fs1_context)
        self.fs2_context = fs2_context
        if len(fs2_context) == 0:
            self.fs2_ctx_bias = nn.Parameter(torch.zeros(1, embedding_dim))
        else:
            self.fs2_ctx_emb = FeatureEmbedding(feature_map, embedding_dim, required_feature_columns=fs2_context)
        self.fs1_gate = MLP_Block(input_dim=embedding_dim * max(1, len(fs1_context)), output_dim=feature_dim, hidden_units=fs_hidden_units, hidden_activations='ReLU', output_activation='Sigmoid', batch_norm=False)
        self.fs2_gate = MLP_Block(input_dim=embedding_dim * max(1, len(fs2_context)), output_dim=feature_dim, hidden_units=fs_hidden_units, hidden_activations='ReLU', output_activation='Sigmoid', batch_norm=False)

    def forward(self, X, flat_emb):
        if len(self.fs1_context) == 0:
            fs1_input = self.fs1_ctx_bias.repeat(flat_emb.size(0), 1)
        else:
            fs1_input = self.fs1_ctx_emb(X).flatten(start_dim=1)
        gt1 = self.fs1_gate(fs1_input) * 2
        feature1 = flat_emb * gt1
        if len(self.fs2_context) == 0:
            fs2_input = self.fs2_ctx_bias.repeat(flat_emb.size(0), 1)
        else:
            fs2_input = self.fs2_ctx_emb(X).flatten(start_dim=1)
        gt2 = self.fs2_gate(fs2_input) * 2
        feature2 = flat_emb * gt2
        return (feature1, feature2)

def forward(self, X, flat_emb):
    if len(self.fs1_context) == 0:
        fs1_input = self.fs1_ctx_bias.repeat(flat_emb.size(0), 1)
    else:
        fs1_input = self.fs1_ctx_emb(X).flatten(start_dim=1)
    gt1 = self.fs1_gate(fs1_input) * 2
    feature1 = flat_emb * gt1
    if len(self.fs2_context) == 0:
        fs2_input = self.fs2_ctx_bias.repeat(flat_emb.size(0), 1)
    else:
        fs2_input = self.fs2_ctx_emb(X).flatten(start_dim=1)
    gt2 = self.fs2_gate(fs2_input) * 2
    feature2 = flat_emb * gt2
    return (feature1, feature2)

class InteractionAggregation(nn.Module):

    def __init__(self, x_dim, y_dim, output_dim=1, num_heads=1):
        super(InteractionAggregation, self).__init__()
        assert x_dim % num_heads == 0 and y_dim % num_heads == 0, 'Input dim must be divisible by num_heads!'
        self.num_heads = num_heads
        self.output_dim = output_dim
        self.head_x_dim = x_dim // num_heads
        self.head_y_dim = y_dim // num_heads
        self.w_x = nn.Linear(x_dim, output_dim)
        self.w_y = nn.Linear(y_dim, output_dim)
        self.w_xy = nn.Parameter(torch.Tensor(num_heads * self.head_x_dim * self.head_y_dim, output_dim))
        nn.init.xavier_normal_(self.w_xy)

    def forward(self, x, y):
        output = self.w_x(x) + self.w_y(y)
        head_x = x.view(-1, self.num_heads, self.head_x_dim)
        head_y = y.view(-1, self.num_heads, self.head_y_dim)
        xy = torch.matmul(torch.matmul(head_x.unsqueeze(2), self.w_xy.view(self.num_heads, self.head_x_dim, -1)).view(-1, self.num_heads, self.output_dim, self.head_y_dim), head_y.unsqueeze(-1)).squeeze(-1)
        output += xy.sum(dim=1)
        return output

def forward(self, x, y):
    output = self.w_x(x) + self.w_y(y)
    head_x = x.view(-1, self.num_heads, self.head_x_dim)
    head_y = y.view(-1, self.num_heads, self.head_y_dim)
    xy = torch.matmul(torch.matmul(head_x.unsqueeze(2), self.w_xy.view(self.num_heads, self.head_x_dim, -1)).view(-1, self.num_heads, self.output_dim, self.head_y_dim), head_y.unsqueeze(-1)).squeeze(-1)
    output += xy.sum(dim=1)
    return output

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

def get_labels(self, inputs):
    """ Please override get_labels() when using multiple labels!
        """
    labels = self.feature_map.labels
    batch_dict = inputs[0]
    y = batch_dict[labels[0]].to(self.device)
    return y.float().view(-1, 1)

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

def get_labels(self, inputs):
    """ Please override get_labels() when using multiple labels!
        """
    labels = self.feature_map.labels
    batch_dict = inputs[0]
    y = batch_dict[labels[0]].to(self.device)
    return y.float().view(-1, 1)

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

def get_labels(self, inputs):
    """ Please override get_labels() when using multiple labels!
        """
    labels = self.feature_map.labels
    batch_dict = inputs[0]
    y = batch_dict[labels[0]].to(self.device)
    return y.float().view(-1, 1)

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

def get_labels(self, inputs):
    """ Please override get_labels() when using multiple labels!
        """
    labels = self.feature_map.labels
    batch_dict = inputs[0]
    y = batch_dict[labels[0]].to(self.device)
    return y.float().view(-1, 1)

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

def get_labels(self, inputs):
    """ Please override get_labels() when using multiple labels!
        """
    labels = self.feature_map.labels
    batch_dict = inputs[0]
    y = batch_dict[labels[0]].to(self.device)
    return y.float().view(-1, 1)

class TransActTransformer(nn.Module):

    def __init__(self, transformer_in_dim, dim_feedforward=64, num_heads=1, dropout=0, transformer_layers=1, use_time_window_mask=False, time_window_ms=86400000, first_k_cols=1, concat_max_pool=True):
        super(TransActTransformer, self).__init__()
        self.use_time_window_mask = use_time_window_mask
        self.time_window_ms = time_window_ms
        self.concat_max_pool = concat_max_pool
        self.first_k_cols = first_k_cols
        encoder_layer = nn.TransformerEncoderLayer(d_model=transformer_in_dim, nhead=num_heads, dim_feedforward=dim_feedforward, dropout=dropout, batch_first=True)
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=transformer_layers)
        if self.concat_max_pool:
            self.out_linear = nn.Linear(transformer_in_dim, transformer_in_dim)

    def forward(self, target_emb, sequence_emb, time_interval_seq=None, mask=None):
        seq_len = sequence_emb.size(1)
        concat_seq_emb = torch.cat([sequence_emb, target_emb.unsqueeze(1).expand(-1, seq_len, -1)], dim=-1)
        key_padding_mask = self.adjust_mask(mask)
        if self.use_time_window_mask and self.training:
            rand_time_window_ms = random.randint(0, self.time_window_ms)
            time_window_mask = time_interval_seq < rand_time_window_ms
            key_padding_mask = torch.bitwise_or(key_padding_mask, time_window_mask)
        tfmr_out = self.transformer_encoder(src=concat_seq_emb, src_key_padding_mask=key_padding_mask)
        tfmr_out = tfmr_out.masked_fill(key_padding_mask.unsqueeze(-1).repeat(1, 1, tfmr_out.shape[-1]), 0.0)
        output_concat = []
        output_concat.append(tfmr_out[:, -self.first_k_cols:].flatten(start_dim=1))
        if self.concat_max_pool:
            tfmr_out = tfmr_out.masked_fill(key_padding_mask.unsqueeze(-1).repeat(1, 1, tfmr_out.shape[-1]), -1000000000.0)
            pooled_out = self.out_linear(tfmr_out.max(dim=1).values)
            output_concat.append(pooled_out)
        return torch.cat(output_concat, dim=-1)

    def adjust_mask(self, mask):
        fully_masked = mask.all(dim=-1)
        mask[fully_masked, -1] = 0
        return mask

def forward(self, target_emb, sequence_emb, time_interval_seq=None, mask=None):
    seq_len = sequence_emb.size(1)
    concat_seq_emb = torch.cat([sequence_emb, target_emb.unsqueeze(1).expand(-1, seq_len, -1)], dim=-1)
    key_padding_mask = self.adjust_mask(mask)
    if self.use_time_window_mask and self.training:
        rand_time_window_ms = random.randint(0, self.time_window_ms)
        time_window_mask = time_interval_seq < rand_time_window_ms
        key_padding_mask = torch.bitwise_or(key_padding_mask, time_window_mask)
    tfmr_out = self.transformer_encoder(src=concat_seq_emb, src_key_padding_mask=key_padding_mask)
    tfmr_out = tfmr_out.masked_fill(key_padding_mask.unsqueeze(-1).repeat(1, 1, tfmr_out.shape[-1]), 0.0)
    output_concat = []
    output_concat.append(tfmr_out[:, -self.first_k_cols:].flatten(start_dim=1))
    if self.concat_max_pool:
        tfmr_out = tfmr_out.masked_fill(key_padding_mask.unsqueeze(-1).repeat(1, 1, tfmr_out.shape[-1]), -1000000000.0)
        pooled_out = self.out_linear(tfmr_out.max(dim=1).values)
        output_concat.append(pooled_out)
    return torch.cat(output_concat, dim=-1)

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

def get_labels(self, inputs):
    """ Please override get_labels() when using multiple labels!
        """
    labels = self.feature_map.labels
    batch_dict = inputs[0]
    y = batch_dict[labels[0]].to(self.device)
    return y.float().view(-1, 1)

class AttentionLayer(nn.Module):

    def __init__(self, model_dim, attention_type='bilinear_attention', attention_hidden_units=[80, 40], attention_activation='Dice', use_attention_softmax=True, attention_dropout=0.0):
        super(AttentionLayer, self).__init__()
        assert attention_type in ['bilinear_attention', 'dot_attention', 'din_attention'], 'attention_type={} is not supported.'.format(attention_type)
        self.attention_type = attention_type
        self.use_attention_softmax = use_attention_softmax
        if attention_type == 'bilinear_attention':
            self.W_kernel = nn.Parameter(torch.eye(model_dim))
        elif attention_type == 'din_attention':
            self.attn_mlp = MLP_Block(input_dim=model_dim * 4, output_dim=1, hidden_units=attention_hidden_units, hidden_activations=attention_activation, output_activation=None, dropout_rates=attention_dropout, batch_norm=False)

    def forward(self, sequence_emb, target_emb, mask=None):
        seq_len = sequence_emb.size(1)
        if self.attention_type == 'dot_attention':
            attn_score = sequence_emb @ target_emb.unsqueeze(-1)
        elif self.attention_type == 'bilinear_attention':
            attn_score = sequence_emb @ self.W_kernel @ target_emb.unsqueeze(-1)
        elif self.attention_type == 'din_attention':
            target_emb = target_emb.unsqueeze(1).expand(-1, seq_len, -1)
            din_concat = torch.cat([target_emb, sequence_emb, target_emb - sequence_emb, target_emb * sequence_emb], dim=-1)
            attn_score = self.attn_mlp(din_concat.view(-1, 4 * target_emb.size(-1)))
        attn_score = attn_score.view(-1, seq_len)
        if mask is not None:
            attn_score = attn_score * mask.float()
        if self.use_attention_softmax:
            if mask is not None:
                attn_score += -1000000000.0 * (1 - mask.float())
            attn_score = attn_score.softmax(dim=-1)
        return attn_score

def forward(self, sequence_emb, target_emb, mask=None):
    seq_len = sequence_emb.size(1)
    if self.attention_type == 'dot_attention':
        attn_score = sequence_emb @ target_emb.unsqueeze(-1)
    elif self.attention_type == 'bilinear_attention':
        attn_score = sequence_emb @ self.W_kernel @ target_emb.unsqueeze(-1)
    elif self.attention_type == 'din_attention':
        target_emb = target_emb.unsqueeze(1).expand(-1, seq_len, -1)
        din_concat = torch.cat([target_emb, sequence_emb, target_emb - sequence_emb, target_emb * sequence_emb], dim=-1)
        attn_score = self.attn_mlp(din_concat.view(-1, 4 * target_emb.size(-1)))
    attn_score = attn_score.view(-1, seq_len)
    if mask is not None:
        attn_score = attn_score * mask.float()
    if self.use_attention_softmax:
        if mask is not None:
            attn_score += -1000000000.0 * (1 - mask.float())
        attn_score = attn_score.softmax(dim=-1)
    return attn_score

class MultiHeadAttention(nn.Module):
    """ Multi-head attention module """

    def __init__(self, input_dim, attention_dim=None, num_heads=1, dropout_rate=0.0, use_residual=True, use_scale=False, layer_norm=False):
        super(MultiHeadAttention, self).__init__()
        if attention_dim is None:
            attention_dim = input_dim // num_heads
        self.attention_dim = attention_dim
        self.output_dim = num_heads * attention_dim
        self.num_heads = num_heads
        self.use_residual = use_residual
        self.scale = attention_dim ** 0.5 if use_scale else None
        self.W_q = nn.Linear(input_dim, self.output_dim, bias=False)
        self.W_k = nn.Linear(input_dim, self.output_dim, bias=False)
        self.W_v = nn.Linear(input_dim, self.output_dim, bias=False)
        if input_dim != self.output_dim:
            self.W_res = nn.Linear(self.output_dim, input_dim, bias=False)
        else:
            self.W_res = None
        self.dot_product_attention = ScaledDotProductAttention(dropout_rate)
        self.layer_norm = nn.LayerNorm(input_dim) if layer_norm else None
        self.dropout = nn.Dropout(dropout_rate) if dropout_rate > 0 else None

    def forward(self, query, key, value, mask=None):
        if mask:
            mask = mask.unsqueeze(1).repeat(1, self.num_heads, 1, 1).flatten(end_dim=1)
        residual = query
        query = self.W_q(query)
        key = self.W_k(key)
        value = self.W_v(value)
        batch_size = query.size(0)
        query = query.view(batch_size * self.num_heads, -1, self.attention_dim)
        key = key.view(batch_size * self.num_heads, -1, self.attention_dim)
        value = value.view(batch_size * self.num_heads, -1, self.attention_dim)
        output, attention = self.dot_product_attention(query, key, value, self.scale, mask)
        output = output.view(batch_size, -1, self.output_dim)
        if self.W_res is not None:
            output = self.W_res(output)
        output = output.relu()
        if self.dropout is not None:
            output = self.dropout(output)
        if self.use_residual:
            output = output + residual
        if self.layer_norm is not None:
            output = self.layer_norm(output)
        return (output, attention)

def forward(self, query, key, value, mask=None):
    if mask:
        mask = mask.unsqueeze(1).repeat(1, self.num_heads, 1, 1).flatten(end_dim=1)
    residual = query
    query = self.W_q(query)
    key = self.W_k(key)
    value = self.W_v(value)
    batch_size = query.size(0)
    query = query.view(batch_size * self.num_heads, -1, self.attention_dim)
    key = key.view(batch_size * self.num_heads, -1, self.attention_dim)
    value = value.view(batch_size * self.num_heads, -1, self.attention_dim)
    output, attention = self.dot_product_attention(query, key, value, self.scale, mask)
    output = output.view(batch_size, -1, self.output_dim)
    if self.W_res is not None:
        output = self.W_res(output)
    output = output.relu()
    if self.dropout is not None:
        output = self.dropout(output)
    if self.use_residual:
        output = output + residual
    if self.layer_norm is not None:
        output = self.layer_norm(output)
    return (output, attention)

class AttentionalAggregation(nn.Module):
    """
    agg attention for InterHAt
    """

    def __init__(self, embedding_dim, hidden_dim=None):
        super(AttentionalAggregation, self).__init__()
        if hidden_dim is None:
            hidden_dim = 4 * embedding_dim
        self.agg = nn.Sequential(nn.Linear(embedding_dim, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, 1, bias=False), nn.Softmax(dim=1))

    def forward(self, X):
        attentions = self.agg(X)
        attention_out = (attentions * X).sum(dim=1)
        return attention_out

def forward(self, X):
    attentions = self.agg(X)
    attention_out = (attentions * X).sum(dim=1)
    return attention_out

class FeatureSelection(nn.Module):

    def __init__(self, feature_map, feature_dim, embedding_dim, fs_hidden_units=[], fs1_context=[], fs2_context=[]):
        super(FeatureSelection, self).__init__()
        self.fs1_context = fs1_context
        if len(fs1_context) == 0:
            self.fs1_ctx_bias = nn.Parameter(torch.zeros(1, embedding_dim))
        else:
            self.fs1_ctx_emb = FeatureEmbedding(feature_map, embedding_dim, required_feature_columns=fs1_context)
        self.fs2_context = fs2_context
        if len(fs2_context) == 0:
            self.fs2_ctx_bias = nn.Parameter(torch.zeros(1, embedding_dim))
        else:
            self.fs2_ctx_emb = FeatureEmbedding(feature_map, embedding_dim, required_feature_columns=fs2_context)
        self.fs1_gate = MLP_Block(input_dim=embedding_dim * max(1, len(fs1_context)), output_dim=feature_dim, hidden_units=fs_hidden_units, hidden_activations='ReLU', output_activation='Sigmoid', batch_norm=False)
        self.fs2_gate = MLP_Block(input_dim=embedding_dim * max(1, len(fs2_context)), output_dim=feature_dim, hidden_units=fs_hidden_units, hidden_activations='ReLU', output_activation='Sigmoid', batch_norm=False)

    def forward(self, X, flat_emb):
        if len(self.fs1_context) == 0:
            fs1_input = self.fs1_ctx_bias.repeat(flat_emb.size(0), 1)
        else:
            fs1_input = self.fs1_ctx_emb(X).flatten(start_dim=1)
        gt1 = self.fs1_gate(fs1_input) * 2
        feature1 = flat_emb * gt1
        if len(self.fs2_context) == 0:
            fs2_input = self.fs2_ctx_bias.repeat(flat_emb.size(0), 1)
        else:
            fs2_input = self.fs2_ctx_emb(X).flatten(start_dim=1)
        gt2 = self.fs2_gate(fs2_input) * 2
        feature2 = flat_emb * gt2
        return (feature1, feature2)

def forward(self, X, flat_emb):
    if len(self.fs1_context) == 0:
        fs1_input = self.fs1_ctx_bias.repeat(flat_emb.size(0), 1)
    else:
        fs1_input = self.fs1_ctx_emb(X).flatten(start_dim=1)
    gt1 = self.fs1_gate(fs1_input) * 2
    feature1 = flat_emb * gt1
    if len(self.fs2_context) == 0:
        fs2_input = self.fs2_ctx_bias.repeat(flat_emb.size(0), 1)
    else:
        fs2_input = self.fs2_ctx_emb(X).flatten(start_dim=1)
    gt2 = self.fs2_gate(fs2_input) * 2
    feature2 = flat_emb * gt2
    return (feature1, feature2)

class InteractionAggregation(nn.Module):

    def __init__(self, x_dim, y_dim, output_dim=1, num_heads=1):
        super(InteractionAggregation, self).__init__()
        assert x_dim % num_heads == 0 and y_dim % num_heads == 0, 'Input dim must be divisible by num_heads!'
        self.num_heads = num_heads
        self.output_dim = output_dim
        self.head_x_dim = x_dim // num_heads
        self.head_y_dim = y_dim // num_heads
        self.w_x = nn.Linear(x_dim, output_dim)
        self.w_y = nn.Linear(y_dim, output_dim)
        self.w_xy = nn.Parameter(torch.Tensor(num_heads * self.head_x_dim * self.head_y_dim, output_dim))
        nn.init.xavier_normal_(self.w_xy)

    def forward(self, x, y):
        output = self.w_x(x) + self.w_y(y)
        head_x = x.view(-1, self.num_heads, self.head_x_dim)
        head_y = y.view(-1, self.num_heads, self.head_y_dim)
        xy = torch.matmul(torch.matmul(head_x.unsqueeze(2), self.w_xy.view(self.num_heads, self.head_x_dim, -1)).view(-1, self.num_heads, self.output_dim, self.head_y_dim), head_y.unsqueeze(-1)).squeeze(-1)
        output += xy.sum(dim=1)
        return output

def forward(self, x, y):
    output = self.w_x(x) + self.w_y(y)
    head_x = x.view(-1, self.num_heads, self.head_x_dim)
    head_y = y.view(-1, self.num_heads, self.head_y_dim)
    xy = torch.matmul(torch.matmul(head_x.unsqueeze(2), self.w_xy.view(self.num_heads, self.head_x_dim, -1)).view(-1, self.num_heads, self.output_dim, self.head_y_dim), head_y.unsqueeze(-1)).squeeze(-1)
    output += xy.sum(dim=1)
    return output

class FactorizationMachineBlock(nn.Module):
    """ Factorization Machine Block (FMB) """

    def __init__(self, input_features=16, output_features=16, embedding_dim=16, rank_k=8, mlp_hidden_units=[16, 16], mlp_hidden_activations='relu', mlp_dropout=0):
        super(FactorizationMachineBlock, self).__init__()
        self.embedding_dim = embedding_dim
        self.output_features = output_features
        self.rank_k = rank_k
        self.input_features = input_features
        if self.rank_k is not None:
            self.proj_Y = nn.Parameter(torch.randn(self.input_features, self.rank_k))
            fm_out_dim = input_features * rank_k
        else:
            fm_out_dim = input_features * input_features
        self.layer_norm = nn.LayerNorm(fm_out_dim)
        self.mlp = MLP_Block(input_dim=fm_out_dim, output_dim=output_features * embedding_dim, hidden_units=mlp_hidden_units, hidden_activations=mlp_hidden_activations, output_activation='relu', dropout_rates=mlp_dropout)

    def forward(self, x):
        flatten_fm = self.optimized_fm(x)
        mlp_in = self.layer_norm(flatten_fm)
        mlp_out = self.mlp(mlp_in)
        return mlp_out.view(-1, self.output_features, self.embedding_dim)

    def optimized_fm(self, x):
        _, n, d = x.shape
        if self.rank_k is not None:
            projected = x.transpose(1, 2) @ self.proj_Y
            fm_matrix = torch.bmm(x, projected)
        else:
            fm_matrix = torch.bmm(x, x.transpose(1, 2))
        return fm_matrix.flatten(start_dim=1)

def optimized_fm(self, x):
    _, n, d = x.shape
    if self.rank_k is not None:
        projected = x.transpose(1, 2) @ self.proj_Y
        fm_matrix = torch.bmm(x, projected)
    else:
        fm_matrix = torch.bmm(x, x.transpose(1, 2))
    return fm_matrix.flatten(start_dim=1)

class WuKongLayer(nn.Module):

    def __init__(self, input_features=16, lcb_features=8, fmb_features=8, embedding_dim=16, fmp_rank_k=4, fmb_mlp_units=[16, 16], fmb_mlp_activations='relu', fmb_dropout=0.1, layer_norm=True):
        super(WuKongLayer, self).__init__()
        self.fmb = FactorizationMachineBlock(input_features, fmb_features, embedding_dim, fmp_rank_k, fmb_mlp_units, fmb_mlp_activations, fmb_dropout)
        self.lcb = LinearCompressionBlock(input_features, lcb_features)
        self.layer_norm = nn.LayerNorm(embedding_dim) if layer_norm else None
        if input_features != lcb_features + fmb_features:
            self.residual_proj = nn.Linear(input_features, lcb_features + fmb_features)

    def forward(self, x):
        fmb_out = self.fmb(x)
        lcb_out = self.lcb(x)
        concat_out = torch.cat([fmb_out, lcb_out], dim=1)
        out = self.residual(concat_out, x)
        if self.layer_norm is not None:
            out = self.layer_norm(out)
        return out

    def residual(self, out, x):
        if out.shape[1] != x.shape[1]:
            res = self.residual_proj(x.transpose(1, 2)).transpose(1, 2)
        else:
            res = x
        return out + res

def residual(self, out, x):
    if out.shape[1] != x.shape[1]:
        res = self.residual_proj(x.transpose(1, 2)).transpose(1, 2)
    else:
        res = x
    return out + res

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

class ResidualBlock(nn.Module):

    def __init__(self, input_dim, hidden_dim, hidden_activation='ReLU', dropout_rate=0, use_residual=True, batch_norm=False):
        super(ResidualBlock, self).__init__()
        self.activation_layer = get_activation(hidden_activation)
        self.layer = nn.Sequential(nn.Linear(input_dim, hidden_dim), self.activation_layer, nn.Linear(hidden_dim, input_dim))
        self.use_residual = use_residual
        self.batch_norm = nn.BatchNorm1d(input_dim) if batch_norm else None
        self.dropout = nn.Dropout(dropout_rate) if dropout_rate > 0 else None

    def forward(self, X):
        X_out = self.layer(X)
        if self.use_residual:
            X_out = X_out + X
        if self.batch_norm is not None:
            X_out = self.batch_norm(X_out)
        output = self.activation_layer(X_out)
        if self.dropout is not None:
            output = self.dropout(output)
        return output

def forward(self, X):
    X_out = self.layer(X)
    if self.use_residual:
        X_out = X_out + X
    if self.batch_norm is not None:
        X_out = self.batch_norm(X_out)
    output = self.activation_layer(X_out)
    if self.dropout is not None:
        output = self.dropout(output)
    return output

class FmFM(BaseModel):
    """ The FmFM model
        Reference:
        - FM2: Field-matrixed Factorization Machines for Recommender Systems, WWW'2021.
    """

    def __init__(self, feature_map, model_id='FmFM', gpu=-1, learning_rate=0.001, embedding_dim=10, regularizer=None, field_interaction_type='matrixed', **kwargs):
        super(FmFM, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=regularizer, net_regularizer=regularizer, **kwargs)
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        num_fields = feature_map.num_fields
        interact_dim = int(num_fields * (num_fields - 1) / 2)
        self.field_interaction_type = field_interaction_type
        if self.field_interaction_type == 'vectorized':
            self.interaction_weight = nn.Parameter(torch.Tensor(interact_dim, embedding_dim))
        elif self.field_interaction_type == 'matrixed':
            self.interaction_weight = nn.Parameter(torch.Tensor(interact_dim, embedding_dim, embedding_dim))
        else:
            raise ValueError('field_interaction_type={} is not supported.'.format(self.field_interaction_type))
        nn.init.xavier_normal_(self.interaction_weight)
        self.lr_layer = LogisticRegression(feature_map)
        self.triu_index = torch.triu_indices(num_fields, num_fields, offset=1).to(self.device)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        """
        Inputs: [X, y]
        """
        X = self.get_inputs(inputs)
        feature_emb = self.embedding_layer(X)
        left_emb = torch.index_select(feature_emb, 1, self.triu_index[0])
        right_emb = torch.index_select(feature_emb, 1, self.triu_index[1])
        if self.field_interaction_type == 'vectorized':
            left_emb = left_emb * self.interaction_weight
        elif self.field_interaction_type == 'matrixed':
            left_emb = torch.matmul(left_emb.unsqueeze(2), self.interaction_weight).squeeze(2)
        y_pred = (left_emb * right_emb).sum(dim=-1).sum(dim=-1, keepdim=True)
        y_pred += self.lr_layer(X)
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred}
        return return_dict

def forward(self, inputs):
    """
        Inputs: [X, y]
        """
    X = self.get_inputs(inputs)
    feature_emb = self.embedding_layer(X)
    left_emb = torch.index_select(feature_emb, 1, self.triu_index[0])
    right_emb = torch.index_select(feature_emb, 1, self.triu_index[1])
    if self.field_interaction_type == 'vectorized':
        left_emb = left_emb * self.interaction_weight
    elif self.field_interaction_type == 'matrixed':
        left_emb = torch.matmul(left_emb.unsqueeze(2), self.interaction_weight).squeeze(2)
    y_pred = (left_emb * right_emb).sum(dim=-1).sum(dim=-1, keepdim=True)
    y_pred += self.lr_layer(X)
    y_pred = self.output_activation(y_pred)
    return_dict = {'y_pred': y_pred}
    return return_dict

class GeneralizedInteractionNet(nn.Module):

    def __init__(self, num_layers, num_subspaces, num_fields, embedding_dim):
        super(GeneralizedInteractionNet, self).__init__()
        self.layers = nn.ModuleList([GeneralizedInteraction(num_fields if i == 0 else num_subspaces, num_subspaces, num_fields, embedding_dim) for i in range(num_layers)])

    def forward(self, B_0):
        B_i = B_0
        for layer in self.layers:
            B_i = layer(B_0, B_i)
        return B_i

def forward(self, B_0):
    B_i = B_0
    for layer in self.layers:
        B_i = layer(B_0, B_i)
    return B_i

class GeneralizedInteraction(nn.Module):

    def __init__(self, input_subspaces, output_subspaces, num_fields, embedding_dim):
        super(GeneralizedInteraction, self).__init__()
        self.input_subspaces = input_subspaces
        self.num_fields = num_fields
        self.embedding_dim = embedding_dim
        self.W = nn.Parameter(torch.eye(embedding_dim, embedding_dim).unsqueeze(0).repeat(output_subspaces, 1, 1))
        self.alpha = nn.Parameter(torch.ones(input_subspaces * num_fields, output_subspaces))
        self.h = nn.Parameter(torch.ones(output_subspaces, embedding_dim, 1))

    def forward(self, B_0, B_i):
        outer_product = torch.einsum('bnh,bnd->bnhd', B_0.repeat(1, self.input_subspaces, 1), B_i.repeat(1, 1, self.num_fields).view(B_i.size(0), -1, self.embedding_dim))
        fusion = torch.matmul(outer_product.permute(0, 2, 3, 1), self.alpha)
        fusion = self.W * fusion.permute(0, 3, 1, 2)
        B_i = torch.matmul(fusion, self.h).squeeze(-1)
        return B_i

def forward(self, B_0, B_i):
    outer_product = torch.einsum('bnh,bnd->bnhd', B_0.repeat(1, self.input_subspaces, 1), B_i.repeat(1, 1, self.num_fields).view(B_i.size(0), -1, self.embedding_dim))
    fusion = torch.matmul(outer_product.permute(0, 2, 3, 1), self.alpha)
    fusion = self.W * fusion.permute(0, 3, 1, 2)
    B_i = torch.matmul(fusion, self.h).squeeze(-1)
    return B_i

class DisentangledSelfAttention(nn.Module):
    """ Disentangle self-attention for DESTINE. 
        Reference:
        - The implementation totally follows the original code:
          https://github.com/CRIPAC-DIG/DESTINE/blob/c68e182aa220b444df73286e5e928e8a072ba75e/layers/activation.py#L90
    """

    def __init__(self, embedding_dim, attention_dim=64, num_heads=1, dropout_rate=0.1, use_residual=True, use_scale=False, relu_before_att=False):
        super(DisentangledSelfAttention, self).__init__()
        self.attention_dim = attention_dim
        self.head_dim = attention_dim // num_heads
        self.num_heads = num_heads
        self.use_scale = use_scale
        self.relu_before_att = relu_before_att
        self.W_q = nn.Linear(embedding_dim, self.attention_dim)
        self.W_k = nn.Linear(embedding_dim, self.attention_dim)
        self.W_v = nn.Linear(embedding_dim, self.attention_dim)
        self.W_unary = nn.Linear(embedding_dim, num_heads)
        if use_residual:
            self.W_res = nn.Linear(embedding_dim, self.attention_dim)
        else:
            self.W_res = None
        self.dropout = nn.Dropout(dropout_rate) if dropout_rate > 0 else None

    def forward(self, query, key, value):
        residual = query
        unary = self.W_unary(key)
        query = self.W_q(query)
        key = self.W_k(key)
        value = self.W_v(value)
        if self.relu_before_att:
            query = query.relu()
            key = key.relu()
            value = value.relu()
        batch_size = query.size(0)
        query = query.view(batch_size * self.num_heads, -1, self.head_dim)
        key = key.view(batch_size * self.num_heads, -1, self.head_dim)
        value = value.view(batch_size * self.num_heads, -1, self.head_dim)
        mu_query = query - query.mean(dim=1, keepdim=True)
        mu_key = key - key.mean(dim=1, keepdim=True)
        pair_weights = torch.bmm(mu_query, mu_key.transpose(1, 2))
        if self.use_scale:
            pair_weights /= self.head_dim ** 0.5
        pair_weights = F.softmax(pair_weights, dim=2)
        unary_weights = F.softmax(unary, dim=1)
        unary_weights = unary_weights.view(batch_size * self.num_heads, -1, 1)
        unary_weights = unary_weights.transpose(1, 2)
        attn_weights = pair_weights + unary_weights
        if self.dropout is not None:
            attn_weights = self.dropout(attn_weights)
        output = torch.bmm(attn_weights, value)
        output = output.view(batch_size, -1, self.attention_dim)
        if self.W_res is not None:
            output += self.W_res(residual)
        return output

def forward(self, query, key, value):
    residual = query
    unary = self.W_unary(key)
    query = self.W_q(query)
    key = self.W_k(key)
    value = self.W_v(value)
    if self.relu_before_att:
        query = query.relu()
        key = key.relu()
        value = value.relu()
    batch_size = query.size(0)
    query = query.view(batch_size * self.num_heads, -1, self.head_dim)
    key = key.view(batch_size * self.num_heads, -1, self.head_dim)
    value = value.view(batch_size * self.num_heads, -1, self.head_dim)
    mu_query = query - query.mean(dim=1, keepdim=True)
    mu_key = key - key.mean(dim=1, keepdim=True)
    pair_weights = torch.bmm(mu_query, mu_key.transpose(1, 2))
    if self.use_scale:
        pair_weights /= self.head_dim ** 0.5
    pair_weights = F.softmax(pair_weights, dim=2)
    unary_weights = F.softmax(unary, dim=1)
    unary_weights = unary_weights.view(batch_size * self.num_heads, -1, 1)
    unary_weights = unary_weights.transpose(1, 2)
    attn_weights = pair_weights + unary_weights
    if self.dropout is not None:
        attn_weights = self.dropout(attn_weights)
    output = torch.bmm(attn_weights, value)
    output = output.view(batch_size, -1, self.attention_dim)
    if self.W_res is not None:
        output += self.W_res(residual)
    return output

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

class BehaviorTransformer(nn.Module):

    def __init__(self, seq_len=1, model_dim=64, num_heads=8, stacked_transformer_layers=1, attn_dropout=0.0, net_dropout=0.0, use_position_emb=True, position_dim=4, layer_norm=True, use_residual=True):
        super(BehaviorTransformer, self).__init__()
        self.position_dim = position_dim
        self.use_position_emb = use_position_emb
        self.transformer_blocks = nn.ModuleList((TransformerBlock(model_dim=model_dim, ffn_dim=model_dim, num_heads=num_heads, attn_dropout=attn_dropout, net_dropout=net_dropout, layer_norm=layer_norm, use_residual=use_residual) for _ in range(stacked_transformer_layers)))
        if self.use_position_emb:
            self.position_emb = nn.Parameter(torch.Tensor(seq_len, position_dim))
            self.reset_parameters()

    def reset_parameters(self):
        seq_len = self.position_emb.size(0)
        pe = torch.zeros(seq_len, self.position_dim)
        position = torch.arange(0, seq_len).float().unsqueeze(1)
        div_term = torch.exp(torch.arange(0, self.position_dim, 2).float() * (-np.log(10000.0) / self.position_dim))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.position_emb.data = pe

    def forward(self, x, attn_mask=None):
        if self.use_position_emb:
            x = torch.cat([x, self.position_emb.unsqueeze(0).repeat(x.size(0), 1, 1)], dim=-1)
        for i in range(len(self.transformer_blocks)):
            x = self.transformer_blocks[i](x, attn_mask=attn_mask)
        return x

def forward(self, x, attn_mask=None):
    if self.use_position_emb:
        x = torch.cat([x, self.position_emb.unsqueeze(0).repeat(x.size(0), 1, 1)], dim=-1)
    for i in range(len(self.transformer_blocks)):
        x = self.transformer_blocks[i](x, attn_mask=attn_mask)
    return x

class TransActTransformer(nn.Module):

    def __init__(self, transformer_in_dim, dim_feedforward=64, num_heads=1, dropout=0, transformer_layers=1, use_time_window_mask=False, time_window_ms=86400000, first_k_cols=1, concat_max_pool=True):
        super(TransActTransformer, self).__init__()
        self.use_time_window_mask = use_time_window_mask
        self.time_window_ms = time_window_ms
        self.concat_max_pool = concat_max_pool
        self.first_k_cols = first_k_cols
        encoder_layer = nn.TransformerEncoderLayer(d_model=transformer_in_dim, nhead=num_heads, dim_feedforward=dim_feedforward, dropout=dropout, batch_first=True)
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=transformer_layers)
        if self.concat_max_pool:
            self.out_linear = nn.Linear(transformer_in_dim, transformer_in_dim)

    def forward(self, target_emb, sequence_emb, time_interval_seq=None, mask=None):
        seq_len = sequence_emb.size(1)
        concat_seq_emb = torch.cat([sequence_emb, target_emb.unsqueeze(1).expand(-1, seq_len, -1)], dim=-1)
        key_padding_mask = self.adjust_mask(mask)
        if self.use_time_window_mask and self.training:
            rand_time_window_ms = random.randint(0, self.time_window_ms)
            time_window_mask = time_interval_seq < rand_time_window_ms
            key_padding_mask = torch.bitwise_or(key_padding_mask, time_window_mask)
        tfmr_out = self.transformer_encoder(src=concat_seq_emb, src_key_padding_mask=key_padding_mask)
        tfmr_out = tfmr_out.masked_fill(key_padding_mask.unsqueeze(-1).repeat(1, 1, tfmr_out.shape[-1]), 0.0)
        output_concat = []
        output_concat.append(tfmr_out[:, -self.first_k_cols:].flatten(start_dim=1))
        if self.concat_max_pool:
            tfmr_out = tfmr_out.masked_fill(key_padding_mask.unsqueeze(-1).repeat(1, 1, tfmr_out.shape[-1]), -1000000000.0)
            pooled_out = self.out_linear(tfmr_out.max(dim=1).values)
            output_concat.append(pooled_out)
        return torch.cat(output_concat, dim=-1)

    def adjust_mask(self, mask):
        fully_masked = mask.all(dim=-1)
        mask[fully_masked, -1] = 0
        return mask

def forward(self, target_emb, sequence_emb, time_interval_seq=None, mask=None):
    seq_len = sequence_emb.size(1)
    concat_seq_emb = torch.cat([sequence_emb, target_emb.unsqueeze(1).expand(-1, seq_len, -1)], dim=-1)
    key_padding_mask = self.adjust_mask(mask)
    if self.use_time_window_mask and self.training:
        rand_time_window_ms = random.randint(0, self.time_window_ms)
        time_window_mask = time_interval_seq < rand_time_window_ms
        key_padding_mask = torch.bitwise_or(key_padding_mask, time_window_mask)
    tfmr_out = self.transformer_encoder(src=concat_seq_emb, src_key_padding_mask=key_padding_mask)
    tfmr_out = tfmr_out.masked_fill(key_padding_mask.unsqueeze(-1).repeat(1, 1, tfmr_out.shape[-1]), 0.0)
    output_concat = []
    output_concat.append(tfmr_out[:, -self.first_k_cols:].flatten(start_dim=1))
    if self.concat_max_pool:
        tfmr_out = tfmr_out.masked_fill(key_padding_mask.unsqueeze(-1).repeat(1, 1, tfmr_out.shape[-1]), -1000000000.0)
        pooled_out = self.out_linear(tfmr_out.max(dim=1).values)
        output_concat.append(pooled_out)
    return torch.cat(output_concat, dim=-1)

class CGC_Layer(nn.Module):

    def __init__(self, num_shared_experts, num_specific_experts, num_tasks, input_dim, expert_hidden_units, gate_hidden_units, hidden_activations, net_dropout, batch_norm):
        super(CGC_Layer, self).__init__()
        self.num_shared_experts = num_shared_experts
        self.num_specific_experts = num_specific_experts
        self.num_tasks = num_tasks
        self.shared_experts = nn.ModuleList([MLP_Block(input_dim=input_dim, hidden_units=expert_hidden_units, hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm) for _ in range(self.num_shared_experts)])
        self.specific_experts = nn.ModuleList([nn.ModuleList([MLP_Block(input_dim=input_dim, hidden_units=expert_hidden_units, hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm) for _ in range(self.num_specific_experts)]) for _ in range(num_tasks)])
        self.gate = nn.ModuleList([MLP_Block(input_dim=input_dim, output_dim=num_specific_experts + num_shared_experts if i < num_tasks else num_shared_experts, hidden_units=gate_hidden_units, hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm) for i in range(self.num_tasks + 1)])
        self.gate_activation = get_activation('softmax')

    def forward(self, x, require_gate=False):
        """
        x: list, len(x)==num_tasks+1
        """
        specific_expert_outputs = []
        shared_expert_outputs = []
        for i in range(self.num_tasks):
            task_expert_outputs = []
            for j in range(self.num_specific_experts):
                task_expert_outputs.append(self.specific_experts[i][j](x[i]))
            specific_expert_outputs.append(task_expert_outputs)
        for i in range(self.num_shared_experts):
            shared_expert_outputs.append(self.shared_experts[i](x[-1]))
        cgc_outputs = []
        gates = []
        for i in range(self.num_tasks + 1):
            if i < self.num_tasks:
                gate_input = torch.stack(specific_expert_outputs[i] + shared_expert_outputs, dim=1)
                gate = self.gate_activation(self.gate[i](x[i]))
                gates.append(gate.mean(0))
                cgc_output = torch.sum(gate.unsqueeze(-1) * gate_input, dim=1)
                cgc_outputs.append(cgc_output)
            else:
                gate_input = torch.stack(shared_expert_outputs, dim=1)
                gate = self.gate_activation(self.gate[i](x[-1]))
                gates.append(gate.mean(0))
                cgc_output = torch.sum(gate.unsqueeze(-1) * gate_input, dim=1)
                cgc_outputs.append(cgc_output)
        if require_gate:
            return (cgc_outputs, gates)
        else:
            return cgc_outputs

def forward(self, x, require_gate=False):
    """
        x: list, len(x)==num_tasks+1
        """
    specific_expert_outputs = []
    shared_expert_outputs = []
    for i in range(self.num_tasks):
        task_expert_outputs = []
        for j in range(self.num_specific_experts):
            task_expert_outputs.append(self.specific_experts[i][j](x[i]))
        specific_expert_outputs.append(task_expert_outputs)
    for i in range(self.num_shared_experts):
        shared_expert_outputs.append(self.shared_experts[i](x[-1]))
    cgc_outputs = []
    gates = []
    for i in range(self.num_tasks + 1):
        if i < self.num_tasks:
            gate_input = torch.stack(specific_expert_outputs[i] + shared_expert_outputs, dim=1)
            gate = self.gate_activation(self.gate[i](x[i]))
            gates.append(gate.mean(0))
            cgc_output = torch.sum(gate.unsqueeze(-1) * gate_input, dim=1)
            cgc_outputs.append(cgc_output)
        else:
            gate_input = torch.stack(shared_expert_outputs, dim=1)
            gate = self.gate_activation(self.gate[i](x[-1]))
            gates.append(gate.mean(0))
            cgc_output = torch.sum(gate.unsqueeze(-1) * gate_input, dim=1)
            cgc_outputs.append(cgc_output)
    if require_gate:
        return (cgc_outputs, gates)
    else:
        return cgc_outputs

class MMoE_Layer(nn.Module):

    def __init__(self, num_experts, num_tasks, input_dim, expert_hidden_units, gate_hidden_units, hidden_activations, net_dropout, batch_norm):
        super(MMoE_Layer, self).__init__()
        self.num_experts = num_experts
        self.num_tasks = num_tasks
        self.experts = nn.ModuleList([MLP_Block(input_dim=input_dim, hidden_units=expert_hidden_units, hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm) for _ in range(self.num_experts)])
        self.gate = nn.ModuleList([MLP_Block(input_dim=input_dim, hidden_units=gate_hidden_units, output_dim=num_experts, hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm) for _ in range(self.num_tasks)])
        self.gate_activation = get_activation('softmax')

    def forward(self, x):
        experts_output = torch.stack([self.experts[i](x) for i in range(self.num_experts)], dim=1)
        mmoe_output = []
        for i in range(self.num_tasks):
            gate_output = self.gate[i](x)
            if self.gate_activation is not None:
                gate_output = self.gate_activation(gate_output)
            mmoe_output.append(torch.sum(torch.multiply(gate_output.unsqueeze(-1), experts_output), dim=1))
        return mmoe_output

def forward(self, x):
    experts_output = torch.stack([self.experts[i](x) for i in range(self.num_experts)], dim=1)
    mmoe_output = []
    for i in range(self.num_tasks):
        gate_output = self.gate[i](x)
        if self.gate_activation is not None:
            gate_output = self.gate_activation(gate_output)
        mmoe_output.append(torch.sum(torch.multiply(gate_output.unsqueeze(-1), experts_output), dim=1))
    return mmoe_output

class ONNv2(BaseModel):

    def __init__(self, feature_map, model_id='ONNv2', gpu=-1, learning_rate=0.001, embedding_dim=2, embedding_regularizer=None, net_regularizer=None, hidden_units=[64, 64, 64], hidden_activations='ReLU', net_dropout=0, batch_norm=False, **kwargs):
        super(ONNv2, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.num_fields = feature_map.num_fields
        self.embedding_dim = embedding_dim
        self.interact_units = int(self.num_fields * (self.num_fields - 1) / 2)
        self.dnn = MLP_Block(input_dim=embedding_dim * self.num_fields + self.interact_units, output_dim=1, hidden_units=hidden_units, hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm)
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim * self.num_fields)
        self.diag_mask = torch.eye(self.num_fields).bool().to(self.device)
        self.triu_mask = torch.triu(torch.ones(self.num_fields, self.num_fields), 1).bool().to(self.device)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        X = self.get_inputs(inputs)
        field_wise_emb = self.embedding_layer(X).view(-1, self.num_fields, self.num_fields, self.embedding_dim)
        batch_size = field_wise_emb.shape[0]
        diag_embedding = torch.masked_select(field_wise_emb, self.diag_mask.unsqueeze(-1)).view(batch_size, -1)
        ffm_out = self.ffm_interaction(field_wise_emb)
        dnn_input = torch.cat([diag_embedding, ffm_out], dim=1)
        y_pred = self.dnn(dnn_input)
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred}
        return return_dict

    def ffm_interaction(self, field_wise_emb):
        out = (field_wise_emb.transpose(1, 2) * field_wise_emb).sum(dim=-1)
        out = torch.masked_select(out, self.triu_mask).view(-1, self.interact_units)
        return out

def ffm_interaction(self, field_wise_emb):
    out = (field_wise_emb.transpose(1, 2) * field_wise_emb).sum(dim=-1)
    out = torch.masked_select(out, self.triu_mask).view(-1, self.interact_units)
    return out

class ONN(BaseModel):

    def __init__(self, feature_map, model_id='ONN', learning_rate=0.001, embedding_dim=10, hidden_units=[64, 64, 64], hidden_activations='ReLU', net_dropout=0, batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
        """ ONN model is also known as NFFM/DeepFFM
        """
        super(ONN, self).__init__(feature_map, model_id=model_id, **kwargs)
        self.num_fields = feature_map.num_fields
        self.embedding_dim = embedding_dim
        self.interact_units = int(self.num_fields * (self.num_fields - 1) / 2)
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim * self.num_fields, embedding_regularizer=embedding_regularizer)
        self.emb_out_dim = (embedding_dim * self.num_fields + self.interact_units,)
        self.mlp = MLP_Block(input_dim=self.emb_out_dim, output_dim=1, hidden_units=hidden_units, hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm, regularizer=net_regularizer)
        self.diag_mask = tf.eye(self.num_fields, dtype=tf.bool)
        self.triu_mask = tf.linalg.band_part(tf.ones(shape=(self.num_fields, self.num_fields)), 0, -1) - tf.eye(self.num_fields)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)

    def call(self, inputs, training=False):
        X = self.get_inputs(inputs)
        field_wise_emb = tf.reshape(self.embedding_layer(X), (-1, self.num_fields, self.num_fields, self.embedding_dim))
        diag_embedding = tf.boolean_mask(tf.transpose(field_wise_emb, (1, 2, 3, 0)), self.diag_mask)
        diag_embedding = tf.reshape(tf.transpose(diag_embedding, (2, 0, 1)), [-1, self.num_fields * self.embedding_dim])
        ffm_out = self.ffm_interaction(field_wise_emb)
        dnn_input = tf.concat([diag_embedding, ffm_out], axis=-1)
        y_pred = self.mlp(dnn_input, training=training)
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred}
        return return_dict

    def ffm_interaction(self, field_wise_emb):
        out = tf.reduce_sum(field_wise_emb * tf.transpose(field_wise_emb, (0, 2, 1, 3)), axis=-1)
        out = tf.boolean_mask(tf.transpose(out, (1, 2, 0)), self.triu_mask)
        out = tf.reshape(tf.transpose(out, (1, 0)), [-1, self.interact_units])
        return out

    def ffm_bi_interaction(self, field_wise_emb):
        out = field_wise_emb * tf.transpose(field_wise_emb, (0, 2, 1, 3))
        out = tf.boolean_mask(tf.transpose(out, (1, 2, 3, 0)), self.triu_mask)
        out = tf.reduce_sum(tf.transpose(out, (2, 0, 1)), axis=1)
        return out

def ffm_interaction(self, field_wise_emb):
    out = tf.reduce_sum(field_wise_emb * tf.transpose(field_wise_emb, (0, 2, 1, 3)), axis=-1)
    out = tf.boolean_mask(tf.transpose(out, (1, 2, 0)), self.triu_mask)
    out = tf.reshape(tf.transpose(out, (1, 0)), [-1, self.interact_units])
    return out

def ffm_bi_interaction(self, field_wise_emb):
    out = field_wise_emb * tf.transpose(field_wise_emb, (0, 2, 1, 3))
    out = tf.boolean_mask(tf.transpose(out, (1, 2, 3, 0)), self.triu_mask)
    out = tf.reduce_sum(tf.transpose(out, (2, 0, 1)), axis=1)
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

class AttentionLayer(nn.Module):

    def __init__(self, model_dim, attention_type='bilinear_attention', attention_hidden_units=[80, 40], attention_activation='Dice', use_attention_softmax=True, attention_dropout=0.0):
        super(AttentionLayer, self).__init__()
        assert attention_type in ['bilinear_attention', 'dot_attention', 'din_attention'], 'attention_type={} is not supported.'.format(attention_type)
        self.attention_type = attention_type
        self.use_attention_softmax = use_attention_softmax
        if attention_type == 'bilinear_attention':
            self.W_kernel = nn.Parameter(torch.eye(model_dim))
        elif attention_type == 'din_attention':
            self.attn_mlp = MLP_Block(input_dim=model_dim * 4, output_dim=1, hidden_units=attention_hidden_units, hidden_activations=attention_activation, output_activation=None, dropout_rates=attention_dropout, batch_norm=False)

    def forward(self, sequence_emb, target_emb, mask=None):
        seq_len = sequence_emb.size(1)
        if self.attention_type == 'dot_attention':
            attn_score = sequence_emb @ target_emb.unsqueeze(-1)
        elif self.attention_type == 'bilinear_attention':
            attn_score = sequence_emb @ self.W_kernel @ target_emb.unsqueeze(-1)
        elif self.attention_type == 'din_attention':
            target_emb = target_emb.unsqueeze(1).expand(-1, seq_len, -1)
            din_concat = torch.cat([target_emb, sequence_emb, target_emb - sequence_emb, target_emb * sequence_emb], dim=-1)
            attn_score = self.attn_mlp(din_concat.view(-1, 4 * target_emb.size(-1)))
        attn_score = attn_score.view(-1, seq_len)
        if mask is not None:
            attn_score = attn_score * mask.float()
        if self.use_attention_softmax:
            if mask is not None:
                attn_score += -1000000000.0 * (1 - mask.float())
            attn_score = attn_score.softmax(dim=-1)
        return attn_score

def forward(self, sequence_emb, target_emb, mask=None):
    seq_len = sequence_emb.size(1)
    if self.attention_type == 'dot_attention':
        attn_score = sequence_emb @ target_emb.unsqueeze(-1)
    elif self.attention_type == 'bilinear_attention':
        attn_score = sequence_emb @ self.W_kernel @ target_emb.unsqueeze(-1)
    elif self.attention_type == 'din_attention':
        target_emb = target_emb.unsqueeze(1).expand(-1, seq_len, -1)
        din_concat = torch.cat([target_emb, sequence_emb, target_emb - sequence_emb, target_emb * sequence_emb], dim=-1)
        attn_score = self.attn_mlp(din_concat.view(-1, 4 * target_emb.size(-1)))
    attn_score = attn_score.view(-1, seq_len)
    if mask is not None:
        attn_score = attn_score * mask.float()
    if self.use_attention_softmax:
        if mask is not None:
            attn_score += -1000000000.0 * (1 - mask.float())
        attn_score = attn_score.softmax(dim=-1)
    return attn_score

class User2ItemNet(nn.Module):

    def __init__(self, context_dim=64, model_dim=64, attention_hidden_units=[80, 40], attention_activation='ReLU', attention_dropout=0.0, pos_emb_dim=8, max_seq_len=50):
        """ We follow the code from the authors for this implementation.
        """
        super(User2ItemNet, self).__init__()
        self.model_dim = model_dim
        self.pos_emb = nn.Parameter(torch.zeros(max_seq_len, pos_emb_dim))
        self.context_dim = context_dim + pos_emb_dim
        self.W_q = nn.Sequential(nn.Linear(self.context_dim, model_dim), nn.ReLU())
        self.attn_mlp = MLP_Block(input_dim=model_dim * 4, output_dim=1, hidden_units=attention_hidden_units, hidden_activations=attention_activation, output_activation=None, dropout_rates=attention_dropout, batch_norm=False)
        self.W_o = nn.Sequential(nn.Linear(model_dim, model_dim), nn.ReLU())

    def forward(self, target_emb, sequence_emb, context_emb, sequence_emb2, neg_emb=None, mask=None):
        batch_size = target_emb.size(0)
        if context_emb is None:
            context_emb = self.pos_emb.unsqueeze(0).expand(batch_size, -1, -1)
        else:
            context_emb = torch.cat([self.pos_emb.unsqueeze(0).expand(batch_size, -1, -1), context_emb], dimi=-1)
        seq_len = sequence_emb.size(1)
        query = self.W_q(context_emb.reshape(-1, self.context_dim)).reshape(-1, seq_len, self.model_dim)
        inp_concat = torch.cat([query, sequence_emb, query - sequence_emb, query * sequence_emb], dim=-1)
        attn_score = self.attn_mlp(inp_concat.view(-1, 4 * self.model_dim))
        attn_score = attn_score.view(-1, seq_len)
        attn_mask = self.get_mask(mask)
        expand_score = attn_score.unsqueeze(1).repeat(1, seq_len, 1)
        expand_score = expand_score.masked_fill_(attn_mask == False, -1000000000.0)
        expand_score = expand_score.softmax(dim=-1)
        user_embs = torch.bmm(expand_score, sequence_emb)
        user_embs = self.W_o(user_embs.reshape(-1, self.model_dim)).reshape(-1, seq_len, self.model_dim)
        rel_u2i = torch.sum(user_embs[:, -1, :] * target_emb, dim=-1, keepdim=True)
        if neg_emb is not None:
            pos_prob = torch.sum(user_embs[:, -2, :] * sequence_emb2[:, -1, :], dim=-1).sigmoid()
            neg_prob = torch.sum(user_embs[:, -2, :] * neg_emb, dim=-1).sigmoid()
            aux_loss = -torch.log(pos_prob) - torch.log(1 - neg_prob)
            aux_loss = (aux_loss * mask[:, -1]).sum() / mask[:, -1].sum()
        else:
            aux_loss = 0
        return (rel_u2i, aux_loss)

    def get_mask(self, mask):
        """ attn_mask: B x L, 0 for masked positions
        """
        seq_len = mask.size(1)
        attn_mask = mask.unsqueeze(1).repeat(1, seq_len, 1)
        causal_mask = torch.tril(torch.ones(seq_len, seq_len, device=mask.device)).bool().unsqueeze(0).expand_as(attn_mask)
        attn_mask = attn_mask & causal_mask
        diag_ones = torch.eye(seq_len, device=mask.device).bool().unsqueeze(0).expand_as(attn_mask)
        attn_mask = attn_mask | diag_ones
        return attn_mask

def forward(self, target_emb, sequence_emb, context_emb, sequence_emb2, neg_emb=None, mask=None):
    batch_size = target_emb.size(0)
    if context_emb is None:
        context_emb = self.pos_emb.unsqueeze(0).expand(batch_size, -1, -1)
    else:
        context_emb = torch.cat([self.pos_emb.unsqueeze(0).expand(batch_size, -1, -1), context_emb], dimi=-1)
    seq_len = sequence_emb.size(1)
    query = self.W_q(context_emb.reshape(-1, self.context_dim)).reshape(-1, seq_len, self.model_dim)
    inp_concat = torch.cat([query, sequence_emb, query - sequence_emb, query * sequence_emb], dim=-1)
    attn_score = self.attn_mlp(inp_concat.view(-1, 4 * self.model_dim))
    attn_score = attn_score.view(-1, seq_len)
    attn_mask = self.get_mask(mask)
    expand_score = attn_score.unsqueeze(1).repeat(1, seq_len, 1)
    expand_score = expand_score.masked_fill_(attn_mask == False, -1000000000.0)
    expand_score = expand_score.softmax(dim=-1)
    user_embs = torch.bmm(expand_score, sequence_emb)
    user_embs = self.W_o(user_embs.reshape(-1, self.model_dim)).reshape(-1, seq_len, self.model_dim)
    rel_u2i = torch.sum(user_embs[:, -1, :] * target_emb, dim=-1, keepdim=True)
    if neg_emb is not None:
        pos_prob = torch.sum(user_embs[:, -2, :] * sequence_emb2[:, -1, :], dim=-1).sigmoid()
        neg_prob = torch.sum(user_embs[:, -2, :] * neg_emb, dim=-1).sigmoid()
        aux_loss = -torch.log(pos_prob) - torch.log(1 - neg_prob)
        aux_loss = (aux_loss * mask[:, -1]).sum() / mask[:, -1].sum()
    else:
        aux_loss = 0
    return (rel_u2i, aux_loss)

def get_mask(self, mask):
    """ attn_mask: B x L, 0 for masked positions
        """
    seq_len = mask.size(1)
    attn_mask = mask.unsqueeze(1).repeat(1, seq_len, 1)
    causal_mask = torch.tril(torch.ones(seq_len, seq_len, device=mask.device)).bool().unsqueeze(0).expand_as(attn_mask)
    attn_mask = attn_mask & causal_mask
    diag_ones = torch.eye(seq_len, device=mask.device).bool().unsqueeze(0).expand_as(attn_mask)
    attn_mask = attn_mask | diag_ones
    return attn_mask

class Item2ItemNet(nn.Module):

    def __init__(self, context_dim=64, model_dim=64, attention_hidden_units=[80, 40], attention_activation='ReLU', attention_dropout=0.0, use_pos_emb=True, pos_emb_dim=8, max_seq_len=50):
        super(Item2ItemNet, self).__init__()
        self.model_dim = model_dim
        self.use_pos_emb = use_pos_emb
        if self.use_pos_emb:
            self.pos_emb = nn.Parameter(torch.zeros(max_seq_len, pos_emb_dim))
            context_dim += pos_emb_dim
        self.context_dim = context_dim + model_dim
        self.W_q = nn.Sequential(nn.Linear(self.context_dim, model_dim), nn.ReLU())
        self.attn_mlp = MLP_Block(input_dim=model_dim * 4, output_dim=1, hidden_units=attention_hidden_units, hidden_activations=attention_activation, output_activation=None, dropout_rates=attention_dropout, batch_norm=False)

    def forward(self, target_emb, sequence_emb, context_emb=None, mask=None):
        seq_len = sequence_emb.size(1)
        if context_emb is None:
            context_emb = target_emb.unsqueeze(1).expand(-1, seq_len, -1)
        else:
            context_emb = torch.cat([target_emb.unsqueeze(1).expand(-1, seq_len, -1), context_emb], dimi=-1)
        if self.use_pos_emb:
            context_emb = torch.cat([context_emb, self.pos_emb.unsqueeze(0).expand(context_emb.size(0), -1, -1)], dim=-1)
        query = self.W_q(context_emb.reshape(-1, self.context_dim)).view(-1, seq_len, self.model_dim)
        inp_concat = torch.cat([query, sequence_emb, query - sequence_emb, query * sequence_emb], dim=-1)
        attn_score = self.attn_mlp(inp_concat.view(-1, 4 * self.model_dim))
        attn_score = attn_score.view(-1, seq_len)
        score_softmax = attn_score.masked_fill_(mask.float() == 0, -1000000000.0)
        score_softmax = score_softmax.softmax(dim=-1)
        attn_out = (score_softmax.unsqueeze(-1) * sequence_emb).sum(dim=1)
        scores_no_softmax = attn_score * mask.float()
        rel_i2i = scores_no_softmax.sum(dim=1, keepdim=True)
        return (attn_out, rel_i2i)

def forward(self, target_emb, sequence_emb, context_emb=None, mask=None):
    seq_len = sequence_emb.size(1)
    if context_emb is None:
        context_emb = target_emb.unsqueeze(1).expand(-1, seq_len, -1)
    else:
        context_emb = torch.cat([target_emb.unsqueeze(1).expand(-1, seq_len, -1), context_emb], dimi=-1)
    if self.use_pos_emb:
        context_emb = torch.cat([context_emb, self.pos_emb.unsqueeze(0).expand(context_emb.size(0), -1, -1)], dim=-1)
    query = self.W_q(context_emb.reshape(-1, self.context_dim)).view(-1, seq_len, self.model_dim)
    inp_concat = torch.cat([query, sequence_emb, query - sequence_emb, query * sequence_emb], dim=-1)
    attn_score = self.attn_mlp(inp_concat.view(-1, 4 * self.model_dim))
    attn_score = attn_score.view(-1, seq_len)
    score_softmax = attn_score.masked_fill_(mask.float() == 0, -1000000000.0)
    score_softmax = score_softmax.softmax(dim=-1)
    attn_out = (score_softmax.unsqueeze(-1) * sequence_emb).sum(dim=1)
    scores_no_softmax = attn_score * mask.float()
    rel_i2i = scores_no_softmax.sum(dim=1, keepdim=True)
    return (attn_out, rel_i2i)

class MultiHeadSelfAttention(nn.Module):
    """ Multi-head attention module """

    def __init__(self, input_dim, attention_dim=None, num_heads=1, dropout_rate=0.0, use_residual=True, use_scale=False, layer_norm=False):
        super(MultiHeadSelfAttention, self).__init__()
        if attention_dim is None:
            attention_dim = input_dim
        assert attention_dim % num_heads == 0, 'attention_dim={} is not divisible by num_heads={}'.format(attention_dim, num_heads)
        self.head_dim = attention_dim // num_heads
        self.num_heads = num_heads
        self.use_residual = use_residual
        self.scale = self.head_dim ** 0.5 if use_scale else None
        self.W_q = nn.Linear(input_dim, attention_dim, bias=False)
        self.W_k = nn.Linear(input_dim, attention_dim, bias=False)
        self.W_v = nn.Linear(input_dim, attention_dim, bias=False)
        if self.use_residual and input_dim != attention_dim:
            self.W_res = nn.Linear(input_dim, attention_dim, bias=False)
        else:
            self.W_res = None
        self.dot_attention = ScaledDotProductAttention(dropout_rate)
        self.layer_norm = nn.LayerNorm(attention_dim) if layer_norm else None

    def forward(self, X):
        residual = X
        query = self.W_q(X)
        key = self.W_k(X)
        value = self.W_v(X)
        batch_size = query.size(0)
        query = query.view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
        key = key.view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
        value = value.view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
        output, attention = self.dot_attention(query, key, value, scale=self.scale)
        output = output.transpose(1, 2).contiguous().view(batch_size, -1, self.num_heads * self.head_dim)
        if self.W_res is not None:
            residual = self.W_res(residual)
        if self.use_residual:
            output += residual
        if self.layer_norm is not None:
            output = self.layer_norm(output)
        output = output.relu()
        return output

def forward(self, X):
    residual = X
    query = self.W_q(X)
    key = self.W_k(X)
    value = self.W_v(X)
    batch_size = query.size(0)
    query = query.view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
    key = key.view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
    value = value.view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
    output, attention = self.dot_attention(query, key, value, scale=self.scale)
    output = output.transpose(1, 2).contiguous().view(batch_size, -1, self.num_heads * self.head_dim)
    if self.W_res is not None:
        residual = self.W_res(residual)
    if self.use_residual:
        output += residual
    if self.layer_norm is not None:
        output = self.layer_norm(output)
    output = output.relu()
    return output

class MaskedSumPooling(Model):

    def __init__(self):
        super(MaskedSumPooling, self).__init__()

    def forward(self, embedding_matrix):
        return tf.reduce_sum(embedding_matrix, axis=1)

def forward(self, embedding_matrix):
    return tf.reduce_sum(embedding_matrix, axis=1)

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

class LogisticRegression(Layer):

    def __init__(self, feature_map, use_bias=True, regularizer=None):
        super(LogisticRegression, self).__init__()
        self.bias = tf.Variable(tf.zeros(1)) if use_bias else None
        self.embedding_layer = FeatureEmbedding(feature_map, 1, use_pretrain=False, use_sharing=False, embedding_regularizer=regularizer, name_prefix='lr_')

    def call(self, X):
        embed_weights = self.embedding_layer(X)
        output = tf.reduce_sum(embed_weights, axis=1)
        if self.bias is not None:
            output += self.bias
        return output

def call(self, X):
    embed_weights = self.embedding_layer(X)
    output = tf.reduce_sum(embed_weights, axis=1)
    if self.bias is not None:
        output += self.bias
    return output

class MaskedAveragePooling(nn.Module):

    def __init__(self):
        super(MaskedAveragePooling, self).__init__()

    def forward(self, embedding_matrix, mask=None):
        sum_out = torch.sum(embedding_matrix, dim=1)
        if mask is None:
            mask = embedding_matrix.sum(dim=-1) != 0
        avg_out = sum_out / (mask.float().sum(-1, keepdim=True) + 1e-12)
        return avg_out

def forward(self, embedding_matrix, mask=None):
    sum_out = torch.sum(embedding_matrix, dim=1)
    if mask is None:
        mask = embedding_matrix.sum(dim=-1) != 0
    avg_out = sum_out / (mask.float().sum(-1, keepdim=True) + 1e-12)
    return avg_out

class MaskedSumPooling(nn.Module):

    def __init__(self):
        super(MaskedSumPooling, self).__init__()

    def forward(self, embedding_matrix):
        return torch.sum(embedding_matrix, dim=1)

def forward(self, embedding_matrix):
    return torch.sum(embedding_matrix, dim=1)

class KMaxPooling(nn.Module):

    def __init__(self, k, dim):
        super(KMaxPooling, self).__init__()
        self.k = k
        self.dim = dim

    def forward(self, X):
        index = X.topk(self.k, dim=self.dim)[1].sort(dim=self.dim)[0]
        output = X.gather(self.dim, index)
        return output

def forward(self, X):
    index = X.topk(self.k, dim=self.dim)[1].sort(dim=self.dim)[0]
    output = X.gather(self.dim, index)
    return output

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

class SqueezeExcitation(nn.Module):

    def __init__(self, num_fields, reduction_ratio=3, excitation_activation='ReLU'):
        super(SqueezeExcitation, self).__init__()
        reduced_size = max(1, int(num_fields / reduction_ratio))
        excitation = [nn.Linear(num_fields, reduced_size, bias=False), nn.ReLU(), nn.Linear(reduced_size, num_fields, bias=False)]
        if excitation_activation.lower() == 'relu':
            excitation.append(nn.ReLU())
        elif excitation_activation.lower() == 'sigmoid':
            excitation.append(nn.Sigmoid())
        else:
            raise NotImplementedError
        self.excitation = nn.Sequential(*excitation)

    def forward(self, feature_emb):
        Z = torch.mean(feature_emb, dim=-1, out=None)
        A = self.excitation(Z)
        V = feature_emb * A.unsqueeze(-1)
        return V

def forward(self, feature_emb):
    Z = torch.mean(feature_emb, dim=-1, out=None)
    A = self.excitation(Z)
    V = feature_emb * A.unsqueeze(-1)
    return V

class ScaledDotProductAttention(nn.Module):
    """ Scaled Dot-Product Attention 
        Ref: https://zhuanlan.zhihu.com/p/47812375
    """

    def __init__(self, dropout_rate=0.0):
        super(ScaledDotProductAttention, self).__init__()
        self.dropout = nn.Dropout(dropout_rate) if dropout_rate > 0 else None

    def forward(self, Q, K, V, scale=None, mask=None):
        scores = torch.matmul(Q, K.transpose(-1, -2))
        if scale:
            scores = scores / scale
        if mask is not None:
            mask = mask.view_as(scores)
            scores = scores.masked_fill_(mask.float() == 0, -1000000000.0)
        attention = scores.softmax(dim=-1)
        if self.dropout is not None:
            attention = self.dropout(attention)
        output = torch.matmul(attention, V)
        return (output, attention)

def forward(self, Q, K, V, scale=None, mask=None):
    scores = torch.matmul(Q, K.transpose(-1, -2))
    if scale:
        scores = scores / scale
    if mask is not None:
        mask = mask.view_as(scores)
        scores = scores.masked_fill_(mask.float() == 0, -1000000000.0)
    attention = scores.softmax(dim=-1)
    if self.dropout is not None:
        attention = self.dropout(attention)
    output = torch.matmul(attention, V)
    return (output, attention)

class DIN_Attention(nn.Module):

    def __init__(self, embedding_dim=64, attention_units=[32], hidden_activations='ReLU', output_activation=None, dropout_rate=0, batch_norm=False, use_softmax=False):
        super(DIN_Attention, self).__init__()
        self.embedding_dim = embedding_dim
        self.use_softmax = use_softmax
        if isinstance(hidden_activations, str) and hidden_activations.lower() == 'dice':
            hidden_activations = [Dice(units) for units in attention_units]
        self.attention_layer = MLP_Block(input_dim=4 * embedding_dim, output_dim=1, hidden_units=attention_units, hidden_activations=hidden_activations, output_activation=output_activation, dropout_rates=dropout_rate, batch_norm=batch_norm)

    def forward(self, target_item, history_sequence, mask=None):
        """
        target_item: b x emd
        history_sequence: b x len x emb
        mask: mask of history_sequence, 0 for masked positions
        """
        seq_len = history_sequence.size(1)
        target_item = target_item.unsqueeze(1).expand(-1, seq_len, -1)
        attention_input = torch.cat([target_item, history_sequence, target_item - history_sequence, target_item * history_sequence], dim=-1)
        attention_weight = self.attention_layer(attention_input.view(-1, 4 * self.embedding_dim))
        attention_weight = attention_weight.view(-1, seq_len)
        if mask is not None:
            attention_weight = attention_weight * mask.float()
        if self.use_softmax:
            if mask is not None:
                attention_weight += -1000000000.0 * (1 - mask.float())
            attention_weight = attention_weight.softmax(dim=-1)
        output = (attention_weight.unsqueeze(-1) * history_sequence).sum(dim=1)
        return output

def forward(self, target_item, history_sequence, mask=None):
    """
        target_item: b x emd
        history_sequence: b x len x emb
        mask: mask of history_sequence, 0 for masked positions
        """
    seq_len = history_sequence.size(1)
    target_item = target_item.unsqueeze(1).expand(-1, seq_len, -1)
    attention_input = torch.cat([target_item, history_sequence, target_item - history_sequence, target_item * history_sequence], dim=-1)
    attention_weight = self.attention_layer(attention_input.view(-1, 4 * self.embedding_dim))
    attention_weight = attention_weight.view(-1, seq_len)
    if mask is not None:
        attention_weight = attention_weight * mask.float()
    if self.use_softmax:
        if mask is not None:
            attention_weight += -1000000000.0 * (1 - mask.float())
        attention_weight = attention_weight.softmax(dim=-1)
    output = (attention_weight.unsqueeze(-1) * history_sequence).sum(dim=1)
    return output

class MultiHeadTargetAttention(nn.Module):

    def __init__(self, input_dim=64, attention_dim=64, num_heads=1, dropout_rate=0, use_scale=True, use_qkvo=True):
        super(MultiHeadTargetAttention, self).__init__()
        if not use_qkvo:
            attention_dim = input_dim
        assert attention_dim % num_heads == 0, 'attention_dim={} is not divisible by num_heads={}'.format(attention_dim, num_heads)
        self.num_heads = num_heads
        self.head_dim = attention_dim // num_heads
        self.scale = self.head_dim ** 0.5 if use_scale else None
        self.use_qkvo = use_qkvo
        if use_qkvo:
            self.W_q = nn.Linear(input_dim, attention_dim, bias=False)
            self.W_k = nn.Linear(input_dim, attention_dim, bias=False)
            self.W_v = nn.Linear(input_dim, attention_dim, bias=False)
            self.W_o = nn.Linear(attention_dim, input_dim, bias=False)
        self.dot_attention = ScaledDotProductAttention(dropout_rate)

    def forward(self, target_item, history_sequence, mask=None):
        """
        target_item: b x emd
        history_sequence: b x len x emb
        mask: mask of history_sequence, 0 for masked positions
        """
        if self.use_qkvo:
            query = self.W_q(target_item)
            key = self.W_k(history_sequence)
            value = self.W_v(history_sequence)
        else:
            query, key, value = (target_item, history_sequence, history_sequence)
        batch_size = query.size(0)
        query = query.view(batch_size, 1, self.num_heads, self.head_dim).transpose(1, 2)
        key = key.view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
        value = value.view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
        if mask is not None:
            mask = mask.view(batch_size, 1, 1, -1).expand(-1, self.num_heads, -1, -1)
        output, _ = self.dot_attention(query, key, value, scale=self.scale, mask=mask)
        output = output.transpose(1, 2).contiguous().view(-1, self.num_heads * self.head_dim)
        if self.use_qkvo:
            output = self.W_o(output)
        return output

def forward(self, target_item, history_sequence, mask=None):
    """
        target_item: b x emd
        history_sequence: b x len x emb
        mask: mask of history_sequence, 0 for masked positions
        """
    if self.use_qkvo:
        query = self.W_q(target_item)
        key = self.W_k(history_sequence)
        value = self.W_v(history_sequence)
    else:
        query, key, value = (target_item, history_sequence, history_sequence)
    batch_size = query.size(0)
    query = query.view(batch_size, 1, self.num_heads, self.head_dim).transpose(1, 2)
    key = key.view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
    value = value.view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
    if mask is not None:
        mask = mask.view(batch_size, 1, 1, -1).expand(-1, self.num_heads, -1, -1)
    output, _ = self.dot_attention(query, key, value, scale=self.scale, mask=mask)
    output = output.transpose(1, 2).contiguous().view(-1, self.num_heads * self.head_dim)
    if self.use_qkvo:
        output = self.W_o(output)
    return output

class BilinearInteractionV2(nn.Module):

    def __init__(self, num_fields, embedding_dim, bilinear_type='field_interaction'):
        super(BilinearInteractionV2, self).__init__()
        self.bilinear_type = bilinear_type
        self.num_fields = num_fields
        self.embedding_dim = embedding_dim
        self.interact_dim = int(num_fields * (num_fields - 1) / 2)
        if self.bilinear_type == 'field_all':
            self.bilinear_W = nn.Parameter(torch.Tensor(embedding_dim, embedding_dim))
        elif self.bilinear_type == 'field_each':
            self.bilinear_W = nn.Parameter(torch.Tensor(num_fields, embedding_dim, embedding_dim))
        elif self.bilinear_type == 'field_interaction':
            self.bilinear_W = nn.Parameter(torch.Tensor(self.interact_dim, embedding_dim, embedding_dim))
        else:
            raise NotImplementedError
        self.triu_index = nn.Parameter(torch.triu_indices(num_fields, num_fields, offset=1), requires_grad=False)
        self.init_weights()

    def init_weights(self):
        nn.init.xavier_normal_(self.bilinear_W)

    def forward(self, feature_emb):
        if self.bilinear_type == 'field_interaction':
            left_emb = torch.index_select(feature_emb, 1, self.triu_index[0])
            right_emb = torch.index_select(feature_emb, 1, self.triu_index[1])
            bilinear_out = torch.matmul(left_emb.unsqueeze(2), self.bilinear_W).squeeze(2) * right_emb
        else:
            if self.bilinear_type == 'field_all':
                hidden_emb = torch.matmul(feature_emb, self.bilinear_W)
            elif self.bilinear_type == 'field_each':
                hidden_emb = torch.matmul(feature_emb.unsqueeze(2), self.bilinear_W).squeeze(2)
            left_emb = torch.index_select(hidden_emb, 1, self.triu_index[0])
            right_emb = torch.index_select(feature_emb, 1, self.triu_index[1])
            bilinear_out = left_emb * right_emb
        return bilinear_out

def forward(self, feature_emb):
    if self.bilinear_type == 'field_interaction':
        left_emb = torch.index_select(feature_emb, 1, self.triu_index[0])
        right_emb = torch.index_select(feature_emb, 1, self.triu_index[1])
        bilinear_out = torch.matmul(left_emb.unsqueeze(2), self.bilinear_W).squeeze(2) * right_emb
    else:
        if self.bilinear_type == 'field_all':
            hidden_emb = torch.matmul(feature_emb, self.bilinear_W)
        elif self.bilinear_type == 'field_each':
            hidden_emb = torch.matmul(feature_emb.unsqueeze(2), self.bilinear_W).squeeze(2)
        left_emb = torch.index_select(hidden_emb, 1, self.triu_index[0])
        right_emb = torch.index_select(feature_emb, 1, self.triu_index[1])
        bilinear_out = left_emb * right_emb
    return bilinear_out

class CrossNetMix(nn.Module):
    """ CrossNetMix improves CrossNetV2 by:
        1. add MOE to learn feature interactions in different subspaces
        2. add nonlinear transformations in low-dimensional space
    """

    def __init__(self, in_features, layer_num=2, low_rank=32, num_experts=4):
        super(CrossNetMix, self).__init__()
        self.layer_num = layer_num
        self.num_experts = num_experts
        self.U_list = torch.nn.ParameterList([nn.Parameter(nn.init.xavier_normal_(torch.empty(num_experts, in_features, low_rank))) for i in range(self.layer_num)])
        self.V_list = torch.nn.ParameterList([nn.Parameter(nn.init.xavier_normal_(torch.empty(num_experts, in_features, low_rank))) for i in range(self.layer_num)])
        self.C_list = torch.nn.ParameterList([nn.Parameter(nn.init.xavier_normal_(torch.empty(num_experts, low_rank, low_rank))) for i in range(self.layer_num)])
        self.gating = nn.ModuleList([nn.Linear(in_features, 1, bias=False) for i in range(self.num_experts)])
        self.bias = torch.nn.ParameterList([nn.Parameter(nn.init.zeros_(torch.empty(in_features, 1))) for i in range(self.layer_num)])

    def forward(self, inputs):
        x_0 = inputs.unsqueeze(2)
        x_l = x_0
        for i in range(self.layer_num):
            output_of_experts = []
            gating_score_of_experts = []
            for expert_id in range(self.num_experts):
                gating_score_of_experts.append(self.gating[expert_id](x_l.squeeze(2)))
                v_x = torch.matmul(self.V_list[i][expert_id].t(), x_l)
                v_x = torch.tanh(v_x)
                v_x = torch.matmul(self.C_list[i][expert_id], v_x)
                v_x = torch.tanh(v_x)
                uv_x = torch.matmul(self.U_list[i][expert_id], v_x)
                dot_ = uv_x + self.bias[i]
                dot_ = x_0 * dot_
                output_of_experts.append(dot_.squeeze(2))
            output_of_experts = torch.stack(output_of_experts, 2)
            gating_score_of_experts = torch.stack(gating_score_of_experts, 1)
            moe_out = torch.matmul(output_of_experts, gating_score_of_experts.softmax(1))
            x_l = moe_out + x_l
        x_l = x_l.squeeze()
        return x_l

def forward(self, inputs):
    x_0 = inputs.unsqueeze(2)
    x_l = x_0
    for i in range(self.layer_num):
        output_of_experts = []
        gating_score_of_experts = []
        for expert_id in range(self.num_experts):
            gating_score_of_experts.append(self.gating[expert_id](x_l.squeeze(2)))
            v_x = torch.matmul(self.V_list[i][expert_id].t(), x_l)
            v_x = torch.tanh(v_x)
            v_x = torch.matmul(self.C_list[i][expert_id], v_x)
            v_x = torch.tanh(v_x)
            uv_x = torch.matmul(self.U_list[i][expert_id], v_x)
            dot_ = uv_x + self.bias[i]
            dot_ = x_0 * dot_
            output_of_experts.append(dot_.squeeze(2))
        output_of_experts = torch.stack(output_of_experts, 2)
        gating_score_of_experts = torch.stack(gating_score_of_experts, 1)
        moe_out = torch.matmul(output_of_experts, gating_score_of_experts.softmax(1))
        x_l = moe_out + x_l
    x_l = x_l.squeeze()
    return x_l

class CompressedInteractionNet(nn.Module):

    def __init__(self, num_fields, cin_hidden_units, output_dim=1):
        super(CompressedInteractionNet, self).__init__()
        self.cin_hidden_units = cin_hidden_units
        self.fc = nn.Linear(sum(cin_hidden_units), output_dim)
        self.cin_layer = nn.ModuleDict()
        for i, unit in enumerate(self.cin_hidden_units):
            in_channels = num_fields * self.cin_hidden_units[i - 1] if i > 0 else num_fields ** 2
            out_channels = unit
            self.cin_layer['layer_' + str(i + 1)] = nn.Conv1d(in_channels, out_channels, kernel_size=1)

    def forward(self, feature_emb):
        pooling_outputs = []
        X_0 = feature_emb
        batch_size = X_0.shape[0]
        embedding_dim = X_0.shape[-1]
        X_i = X_0
        for i in range(len(self.cin_hidden_units)):
            hadamard_tensor = torch.einsum('bhd,bmd->bhmd', X_0, X_i)
            hadamard_tensor = hadamard_tensor.view(batch_size, -1, embedding_dim)
            X_i = self.cin_layer['layer_' + str(i + 1)](hadamard_tensor).view(batch_size, -1, embedding_dim)
            pooling_outputs.append(X_i.sum(dim=-1))
        output = self.fc(torch.cat(pooling_outputs, dim=-1))
        return output

def forward(self, feature_emb):
    pooling_outputs = []
    X_0 = feature_emb
    batch_size = X_0.shape[0]
    embedding_dim = X_0.shape[-1]
    X_i = X_0
    for i in range(len(self.cin_hidden_units)):
        hadamard_tensor = torch.einsum('bhd,bmd->bhmd', X_0, X_i)
        hadamard_tensor = hadamard_tensor.view(batch_size, -1, embedding_dim)
        X_i = self.cin_layer['layer_' + str(i + 1)](hadamard_tensor).view(batch_size, -1, embedding_dim)
        pooling_outputs.append(X_i.sum(dim=-1))
    output = self.fc(torch.cat(pooling_outputs, dim=-1))
    return output

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

class LogisticRegression(nn.Module):

    def __init__(self, feature_map, use_bias=True):
        super(LogisticRegression, self).__init__()
        self.bias = nn.Parameter(torch.zeros(1), requires_grad=True) if use_bias else None
        self.embedding_layer = FeatureEmbedding(feature_map, 1, use_pretrain=False, use_sharing=False)

    def forward(self, X):
        embed_weights = self.embedding_layer(X)
        output = embed_weights.sum(dim=1)
        if self.bias is not None:
            output += self.bias
        return output

def forward(self, X):
    embed_weights = self.embedding_layer(X)
    output = embed_weights.sum(dim=1)
    if self.bias is not None:
        output += self.bias
    return output

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

def get_labels(self, inputs):
    """ Please override get_labels() when using multiple labels!
        """
    labels = self.feature_map.labels
    y = inputs[labels[0]].to(self.device)
    return y.float().view(-1, 1)

def model_to_device(self):
    self.to(device=self.device)

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

def get_labels(self, inputs):
    """ Override get_labels() to use multiple labels """
    labels = self.feature_map.labels
    y = [inputs[labels[i]].to(self.device).float().view(-1, 1) for i in range(len(labels))]
    return y

def add_loss(self, return_dict, y_true):
    labels = self.feature_map.labels
    loss = [self.loss_fn[i](return_dict['{}_pred'.format(labels[i])], y_true[i], reduction='mean') for i in range(len(labels))]
    if self.loss_weight == 'EQ':
        loss = torch.sum(torch.stack(loss))
    return loss

