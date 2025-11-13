# Cluster 17

class AFN(BaseModel):

    def __init__(self, feature_map, model_id='AFN', gpu=-1, learning_rate=0.001, embedding_dim=10, ensemble_dnn=True, dnn_hidden_units=[64, 64, 64], dnn_activations='ReLU', dnn_dropout=0, afn_hidden_units=[64, 64, 64], afn_activations='ReLU', afn_dropout=0, logarithmic_neurons=5, batch_norm=True, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(AFN, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.num_fields = feature_map.num_fields
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        self.coefficient_W = nn.Linear(self.num_fields, logarithmic_neurons, bias=False)
        self.dense_layer = MLP_Block(input_dim=embedding_dim * logarithmic_neurons, output_dim=1, hidden_units=afn_hidden_units, hidden_activations=afn_activations, output_activation=None, dropout_rates=afn_dropout, batch_norm=batch_norm)
        self.log_batch_norm = nn.BatchNorm1d(self.num_fields)
        self.exp_batch_norm = nn.BatchNorm1d(logarithmic_neurons)
        self.ensemble_dnn = ensemble_dnn
        if ensemble_dnn:
            self.embedding_layer2 = FeatureEmbedding(feature_map, embedding_dim)
            self.dnn = MLP_Block(input_dim=embedding_dim * self.num_fields, output_dim=1, hidden_units=dnn_hidden_units, hidden_activations=dnn_activations, output_activation=None, dropout_rates=dnn_dropout, batch_norm=batch_norm)
            self.fc = nn.Linear(2, 1)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        X = self.get_inputs(inputs)
        feature_emb = self.embedding_layer(X)
        dnn_input = self.logarithmic_net(feature_emb)
        afn_out = self.dense_layer(dnn_input)
        if self.ensemble_dnn:
            feature_emb2 = self.embedding_layer2(X)
            dnn_out = self.dnn(feature_emb2.flatten(start_dim=1))
            y_pred = self.fc(torch.cat([afn_out, dnn_out], dim=-1))
        else:
            y_pred = afn_out
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred}
        return return_dict

    def logarithmic_net(self, feature_emb):
        feature_emb = torch.abs(feature_emb)
        feature_emb = torch.clamp(feature_emb, min=1e-05)
        log_feature_emb = torch.log(feature_emb)
        log_feature_emb = self.log_batch_norm(log_feature_emb)
        logarithmic_out = self.coefficient_W(log_feature_emb.transpose(2, 1)).transpose(1, 2)
        cross_out = torch.exp(logarithmic_out)
        cross_out = self.exp_batch_norm(cross_out)
        concat_out = torch.flatten(cross_out, start_dim=1)
        return concat_out

def logarithmic_net(self, feature_emb):
    feature_emb = torch.abs(feature_emb)
    feature_emb = torch.clamp(feature_emb, min=1e-05)
    log_feature_emb = torch.log(feature_emb)
    log_feature_emb = self.log_batch_norm(log_feature_emb)
    logarithmic_out = self.coefficient_W(log_feature_emb.transpose(2, 1)).transpose(1, 2)
    cross_out = torch.exp(logarithmic_out)
    cross_out = self.exp_batch_norm(cross_out)
    concat_out = torch.flatten(cross_out, start_dim=1)
    return concat_out

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

def reset_parameters(self):
    seq_len = self.position_emb.size(0)
    pe = torch.zeros(seq_len, self.position_dim)
    position = torch.arange(0, seq_len).float().unsqueeze(1)
    div_term = torch.exp(torch.arange(0, self.position_dim, 2).float() * (-np.log(10000.0) / self.position_dim))
    pe[:, 0::2] = torch.sin(position * div_term)
    pe[:, 1::2] = torch.cos(position * div_term)
    self.position_emb.data = pe

class EulerNet(BaseModel):

    def __init__(self, feature_map, model_id='EulerNet', gpu=-1, shape=[3], learning_rate=0.001, embedding_dim=10, net_ex_dropout=0, net_im_dropout=0, layer_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(EulerNet, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        input_dim = feature_map.sum_emb_out_dim()
        field_num = feature_map.num_fields
        shape_list = [embedding_dim * field_num] + [num_neurons * embedding_dim for num_neurons in shape]
        self.reset_parameters()
        interaction_shapes = []
        for inshape, outshape in zip(shape_list[:-1], shape_list[1:]):
            interaction_shapes.append(EulerInteractionLayer(inshape, outshape, embedding_dim, layer_norm, net_ex_dropout, net_im_dropout))
        self.Euler_interaction_layers = nn.Sequential(*interaction_shapes)
        self.mu = nn.Parameter(torch.ones(1, field_num, 1))
        self.reg = nn.Linear(shape_list[-1], 1)
        nn.init.xavier_normal_(self.reg.weight)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.model_to_device()

    def forward(self, inputs):
        X = self.get_inputs(inputs)
        feature_emb = self.embedding_layer(X)
        r, p = (self.mu * torch.cos(feature_emb), self.mu * torch.sin(feature_emb))
        o_r, o_p = self.Euler_interaction_layers((r, p))
        o_r, o_p = (o_r.reshape(o_r.shape[0], -1), o_p.reshape(o_p.shape[0], -1))
        re, im = (self.reg(o_r), self.reg(o_p))
        y_pred = im + re
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred}
        return return_dict

def forward(self, inputs):
    X = self.get_inputs(inputs)
    feature_emb = self.embedding_layer(X)
    r, p = (self.mu * torch.cos(feature_emb), self.mu * torch.sin(feature_emb))
    o_r, o_p = self.Euler_interaction_layers((r, p))
    o_r, o_p = (o_r.reshape(o_r.shape[0], -1), o_p.reshape(o_p.shape[0], -1))
    re, im = (self.reg(o_r), self.reg(o_p))
    y_pred = im + re
    y_pred = self.output_activation(y_pred)
    return_dict = {'y_pred': y_pred}
    return return_dict

class EulerInteractionLayer(nn.Module):

    def __init__(self, inshape, outshape, embedding_dim, apply_norm, net_ex_dropout, net_im_dropout):
        super().__init__()
        self.inshape, self.outshape = (int(inshape), int(outshape))
        self.feature_dim = embedding_dim
        self.apply_norm = apply_norm
        if inshape == outshape:
            init_orders = torch.eye(inshape // self.feature_dim, outshape // self.feature_dim)
        else:
            init_orders = torch.softmax(torch.randn(inshape // self.feature_dim, outshape // self.feature_dim) / 0.01, dim=0)
        self.inter_orders = nn.Parameter(init_orders)
        self.im = nn.Linear(inshape, outshape)
        nn.init.xavier_uniform_(self.im.weight)
        self.bias_lam = nn.Parameter(torch.randn(1, self.feature_dim, outshape // self.feature_dim) * 0.01)
        self.bias_theta = nn.Parameter(torch.randn(1, self.feature_dim, outshape // self.feature_dim) * 0.01)
        self.drop_ex = nn.Dropout(p=net_ex_dropout)
        self.drop_im = nn.Dropout(p=net_im_dropout)
        self.norm_r = nn.LayerNorm([self.feature_dim])
        self.norm_p = nn.LayerNorm([self.feature_dim])

    def forward(self, complex_features):
        r, p = complex_features
        lam = r ** 2 + p ** 2 + 1e-08
        theta = torch.atan2(p, r)
        lam, theta = (lam.reshape(lam.shape[0], -1, self.feature_dim), theta.reshape(theta.shape[0], -1, self.feature_dim))
        lam = 0.5 * torch.log(lam)
        lam, theta = (self.drop_ex(lam), self.drop_ex(theta))
        lam, theta = (torch.transpose(lam, -2, -1), torch.transpose(theta, -2, -1))
        lam, theta = (lam @ self.inter_orders + self.bias_lam, theta @ self.inter_orders + self.bias_theta)
        lam = torch.exp(lam)
        lam, theta = (torch.transpose(lam, -2, -1), torch.transpose(theta, -2, -1))
        r, p = (r.reshape(r.shape[0], -1), p.reshape(p.shape[0], -1))
        r, p = (self.drop_im(r), self.drop_im(p))
        r, p = (self.im(r), self.im(p))
        r, p = (torch.relu(r), torch.relu(p))
        r, p = (r.reshape(r.shape[0], -1, self.feature_dim), p.reshape(p.shape[0], -1, self.feature_dim))
        o_r, o_p = (r + lam * torch.cos(theta), p + lam * torch.sin(theta))
        o_r, o_p = (o_r.reshape(o_r.shape[0], -1, self.feature_dim), o_p.reshape(o_p.shape[0], -1, self.feature_dim))
        if self.apply_norm:
            o_r, o_p = (self.norm_r(o_r), self.norm_p(o_p))
        return (o_r, o_p)

def forward(self, complex_features):
    r, p = complex_features
    lam = r ** 2 + p ** 2 + 1e-08
    theta = torch.atan2(p, r)
    lam, theta = (lam.reshape(lam.shape[0], -1, self.feature_dim), theta.reshape(theta.shape[0], -1, self.feature_dim))
    lam = 0.5 * torch.log(lam)
    lam, theta = (self.drop_ex(lam), self.drop_ex(theta))
    lam, theta = (torch.transpose(lam, -2, -1), torch.transpose(theta, -2, -1))
    lam, theta = (lam @ self.inter_orders + self.bias_lam, theta @ self.inter_orders + self.bias_theta)
    lam = torch.exp(lam)
    lam, theta = (torch.transpose(lam, -2, -1), torch.transpose(theta, -2, -1))
    r, p = (r.reshape(r.shape[0], -1), p.reshape(p.shape[0], -1))
    r, p = (self.drop_im(r), self.drop_im(p))
    r, p = (self.im(r), self.im(p))
    r, p = (torch.relu(r), torch.relu(p))
    r, p = (r.reshape(r.shape[0], -1, self.feature_dim), p.reshape(p.shape[0], -1, self.feature_dim))
    o_r, o_p = (r + lam * torch.cos(theta), p + lam * torch.sin(theta))
    o_r, o_p = (o_r.reshape(o_r.shape[0], -1, self.feature_dim), o_p.reshape(o_p.shape[0], -1, self.feature_dim))
    if self.apply_norm:
        o_r, o_p = (self.norm_r(o_r), self.norm_p(o_p))
    return (o_r, o_p)

def MRR(y_true, y_pred):
    order = np.argsort(y_pred)[::-1]
    y_true = np.take(y_true, order)
    rr_score = y_true / (np.arange(len(y_true)) + 1)
    mrr = np.sum(rr_score) / (np.sum(y_true) + 1e-12)
    return mrr

class NDCG(object):
    """Normalized discounted cumulative gain metric."""

    def __init__(self, k=1):
        self.topk = k

    def dcg_score(self, y_true, y_pred):
        order = np.argsort(y_pred)[::-1]
        y_true = np.take(y_true, order[:self.topk])
        gains = 2 ** y_true - 1
        discounts = np.log2(np.arange(len(y_true)) + 2)
        return np.sum(gains / discounts)

    def __call__(self, y_true, y_pred):
        idcg = self.dcg_score(y_true, y_true)
        dcg = self.dcg_score(y_true, y_pred)
        return dcg / (idcg + 1e-12)

def dcg_score(self, y_true, y_pred):
    order = np.argsort(y_pred)[::-1]
    y_true = np.take(y_true, order[:self.topk])
    gains = 2 ** y_true - 1
    discounts = np.log2(np.arange(len(y_true)) + 2)
    return np.sum(gains / discounts)

class CustomizedFeatureProcessor(FeatureProcessor):

    def convert_to_bucket(self, col_name):

        def _convert_to_bucket(value):
            if value > 2:
                value = int(np.floor(np.log(value) ** 2))
            else:
                value = int(value)
            return value
        return pl.col(col_name).apply(_convert_to_bucket).cast(pl.Int32)

def _convert_to_bucket(value):
    if value > 2:
        value = int(np.floor(np.log(value) ** 2))
    else:
        value = int(value)
    return value

