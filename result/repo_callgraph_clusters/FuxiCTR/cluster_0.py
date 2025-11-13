# Cluster 0

class EDCN(BaseModel):
    """ The EDCN model
        References:
          - Bo Chen, Yichao Wang, Zhirong Liu, Ruiming Tang, Wei Guo, Hongkun Zheng, Weiwei Yao, Muyu Zhang, 
            Xiuqiang He: Enhancing Explicit and Implicit Feature Interactions via Information Sharing for Parallel 
            Deep CTR Models, CIKM 2021.
          - [PDF] https://dlp-kdd.github.io/assets/pdf/DLP-KDD_2021_paper_12.pdf
          - [Code] https://github.com/mindspore-ai/models/blob/master/research/recommend/EDCN/src/edcn.py 
    """

    def __init__(self, feature_map, model_id='EDCN', gpu=-1, learning_rate=0.001, embedding_dim=10, num_cross_layers=3, hidden_activations='ReLU', bridge_type='hadamard_product', temperature=1, net_dropout=0, batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(EDCN, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        hidden_dim = feature_map.num_fields * embedding_dim
        self.dense_layers = nn.ModuleList([MLP_Block(input_dim=hidden_dim, output_dim=None, hidden_units=[hidden_dim], hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=False) for _ in range(num_cross_layers)])
        self.cross_layers = nn.ModuleList([CrossInteraction(hidden_dim) for _ in range(num_cross_layers)])
        self.bridge_modules = nn.ModuleList([BridgeModule(hidden_dim, bridge_type) for _ in range(num_cross_layers)])
        self.regulation_modules = nn.ModuleList([RegulationModule(feature_map.num_fields, embedding_dim, tau=temperature, use_bn=batch_norm) for _ in range(num_cross_layers)])
        self.fc = nn.Linear(hidden_dim * 3, 1)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        """
        Inputs: [X,y]
        """
        X = self.get_inputs(inputs)
        feat_emb = self.embedding_layer(X)
        cross_i, deep_i = self.regulation_modules[0](feat_emb.flatten(start_dim=1))
        cross_0 = cross_i
        for i in range(len(self.cross_layers)):
            cross_i = self.cross_layers[i](cross_0, cross_i)
            deep_i = self.dense_layers[i](deep_i)
            bridge_i = self.bridge_modules[i](cross_i, deep_i)
            if i + 1 < len(self.cross_layers):
                cross_i, deep_i = self.regulation_modules[i + 1](bridge_i)
        y_pred = self.fc(torch.cat([cross_i, deep_i, bridge_i], dim=-1))
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred}
        return return_dict

def __init__(self, feature_map, model_id='EDCN', gpu=-1, learning_rate=0.001, embedding_dim=10, num_cross_layers=3, hidden_activations='ReLU', bridge_type='hadamard_product', temperature=1, net_dropout=0, batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
    super(EDCN, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
    self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
    hidden_dim = feature_map.num_fields * embedding_dim
    self.dense_layers = nn.ModuleList([MLP_Block(input_dim=hidden_dim, output_dim=None, hidden_units=[hidden_dim], hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=False) for _ in range(num_cross_layers)])
    self.cross_layers = nn.ModuleList([CrossInteraction(hidden_dim) for _ in range(num_cross_layers)])
    self.bridge_modules = nn.ModuleList([BridgeModule(hidden_dim, bridge_type) for _ in range(num_cross_layers)])
    self.regulation_modules = nn.ModuleList([RegulationModule(feature_map.num_fields, embedding_dim, tau=temperature, use_bn=batch_norm) for _ in range(num_cross_layers)])
    self.fc = nn.Linear(hidden_dim * 3, 1)
    self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
    self.reset_parameters()
    self.model_to_device()

class BridgeModule(nn.Module):

    def __init__(self, hidden_dim, bridge_type='hadamard_product'):
        super(BridgeModule, self).__init__()
        assert bridge_type in ['hadamard_product', 'pointwise_addition', 'concatenation', 'attention_pooling'], 'bridge_type={} is not supported.'.format(bridge_type)
        self.bridge_type = bridge_type
        if bridge_type == 'concatenation':
            self.concat_pooling = nn.Sequential(nn.Linear(hidden_dim * 2, hidden_dim), nn.ReLU())
        elif bridge_type == 'attention_pooling':
            self.attention1 = nn.Sequential(nn.Linear(hidden_dim, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, hidden_dim, bias=False), nn.Softmax(dim=-1))
            self.attention2 = nn.Sequential(nn.Linear(hidden_dim, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, hidden_dim, bias=False), nn.Softmax(dim=-1))

    def forward(self, X1, X2):
        out = None
        if self.bridge_type == 'hadamard_product':
            out = X1 * X2
        elif self.bridge_type == 'pointwise_addition':
            out = X1 + X2
        elif self.bridge_type == 'concatenation':
            out = self.concat_pooling(torch.cat([X1, X2], dim=-1))
        elif self.bridge_type == 'attention_pooling':
            out = self.attention1(X1) * X1 + self.attention1(X2) * X2
        return out

def __init__(self, hidden_dim, bridge_type='hadamard_product'):
    super(BridgeModule, self).__init__()
    assert bridge_type in ['hadamard_product', 'pointwise_addition', 'concatenation', 'attention_pooling'], 'bridge_type={} is not supported.'.format(bridge_type)
    self.bridge_type = bridge_type
    if bridge_type == 'concatenation':
        self.concat_pooling = nn.Sequential(nn.Linear(hidden_dim * 2, hidden_dim), nn.ReLU())
    elif bridge_type == 'attention_pooling':
        self.attention1 = nn.Sequential(nn.Linear(hidden_dim, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, hidden_dim, bias=False), nn.Softmax(dim=-1))
        self.attention2 = nn.Sequential(nn.Linear(hidden_dim, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, hidden_dim, bias=False), nn.Softmax(dim=-1))

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

class MaskNet(BaseModel):

    def __init__(self, feature_map, model_id='MaskNet', gpu=-1, learning_rate=0.001, embedding_dim=10, dnn_hidden_units=[64, 64, 64], dnn_hidden_activations='ReLU', model_type='SerialMaskNet', parallel_num_blocks=1, parallel_block_dim=64, reduction_ratio=1, embedding_regularizer=None, net_regularizer=None, net_dropout=0, emb_layernorm=True, net_layernorm=True, **kwargs):
        super(MaskNet, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        if model_type == 'SerialMaskNet':
            self.mask_net = SerialMaskNet(input_dim=feature_map.num_fields * embedding_dim, output_dim=1, output_activation=self.output_activation, hidden_units=dnn_hidden_units, hidden_activations=dnn_hidden_activations, reduction_ratio=reduction_ratio, dropout_rates=net_dropout, layer_norm=net_layernorm)
        elif model_type == 'ParallelMaskNet':
            self.mask_net = ParallelMaskNet(input_dim=feature_map.num_fields * embedding_dim, output_dim=1, output_activation=self.output_activation, num_blocks=parallel_num_blocks, block_dim=parallel_block_dim, hidden_units=dnn_hidden_units, hidden_activations=dnn_hidden_activations, reduction_ratio=reduction_ratio, dropout_rates=net_dropout, layer_norm=net_layernorm)
        self.num_fields = feature_map.num_fields
        if emb_layernorm:
            self.emb_norm = nn.ModuleList((nn.LayerNorm(embedding_dim) for _ in range(self.num_fields)))
        else:
            self.emb_norm = None
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        X = self.get_inputs(inputs)
        feature_emb = self.embedding_layer(X)
        if self.emb_norm is not None:
            feat_list = feature_emb.chunk(self.num_fields, dim=1)
            V_hidden = torch.cat([self.emb_norm[i](feat) for i, feat in enumerate(feat_list)], dim=1)
        else:
            V_hidden = feature_emb
        y_pred = self.mask_net(feature_emb.flatten(start_dim=1), V_hidden.flatten(start_dim=1))
        return_dict = {'y_pred': y_pred}
        return return_dict

def __init__(self, feature_map, model_id='MaskNet', gpu=-1, learning_rate=0.001, embedding_dim=10, dnn_hidden_units=[64, 64, 64], dnn_hidden_activations='ReLU', model_type='SerialMaskNet', parallel_num_blocks=1, parallel_block_dim=64, reduction_ratio=1, embedding_regularizer=None, net_regularizer=None, net_dropout=0, emb_layernorm=True, net_layernorm=True, **kwargs):
    super(MaskNet, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
    self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
    if model_type == 'SerialMaskNet':
        self.mask_net = SerialMaskNet(input_dim=feature_map.num_fields * embedding_dim, output_dim=1, output_activation=self.output_activation, hidden_units=dnn_hidden_units, hidden_activations=dnn_hidden_activations, reduction_ratio=reduction_ratio, dropout_rates=net_dropout, layer_norm=net_layernorm)
    elif model_type == 'ParallelMaskNet':
        self.mask_net = ParallelMaskNet(input_dim=feature_map.num_fields * embedding_dim, output_dim=1, output_activation=self.output_activation, num_blocks=parallel_num_blocks, block_dim=parallel_block_dim, hidden_units=dnn_hidden_units, hidden_activations=dnn_hidden_activations, reduction_ratio=reduction_ratio, dropout_rates=net_dropout, layer_norm=net_layernorm)
    self.num_fields = feature_map.num_fields
    if emb_layernorm:
        self.emb_norm = nn.ModuleList((nn.LayerNorm(embedding_dim) for _ in range(self.num_fields)))
    else:
        self.emb_norm = None
    self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
    self.reset_parameters()
    self.model_to_device()

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

class ParallelMaskNet(nn.Module):

    def __init__(self, input_dim, output_dim=None, output_activation=None, num_blocks=1, block_dim=64, hidden_units=[], hidden_activations='ReLU', reduction_ratio=1, dropout_rates=0, layer_norm=True):
        super(ParallelMaskNet, self).__init__()
        self.num_blocks = num_blocks
        self.mask_blocks = nn.ModuleList([MaskBlock(input_dim, input_dim, block_dim, hidden_activations, reduction_ratio, dropout_rates, layer_norm) for _ in range(num_blocks)])
        self.dnn = MLP_Block(input_dim=block_dim * num_blocks, output_dim=output_dim, hidden_units=hidden_units, hidden_activations=hidden_activations, output_activation=output_activation, dropout_rates=dropout_rates)

    def forward(self, V_emb, V_hidden):
        block_out = []
        for i in range(self.num_blocks):
            block_out.append(self.mask_blocks[i](V_emb, V_hidden))
        concat_out = torch.cat(block_out, dim=-1)
        v_out = self.dnn(concat_out)
        return v_out

def __init__(self, input_dim, output_dim=None, output_activation=None, num_blocks=1, block_dim=64, hidden_units=[], hidden_activations='ReLU', reduction_ratio=1, dropout_rates=0, layer_norm=True):
    super(ParallelMaskNet, self).__init__()
    self.num_blocks = num_blocks
    self.mask_blocks = nn.ModuleList([MaskBlock(input_dim, input_dim, block_dim, hidden_activations, reduction_ratio, dropout_rates, layer_norm) for _ in range(num_blocks)])
    self.dnn = MLP_Block(input_dim=block_dim * num_blocks, output_dim=output_dim, hidden_units=hidden_units, hidden_activations=hidden_activations, output_activation=output_activation, dropout_rates=dropout_rates)

class MaskBlock(nn.Module):

    def __init__(self, input_dim, hidden_dim, output_dim, hidden_activation='ReLU', reduction_ratio=1, dropout_rate=0, layer_norm=True):
        super(MaskBlock, self).__init__()
        self.mask_layer = nn.Sequential(nn.Linear(input_dim, int(hidden_dim * reduction_ratio)), nn.ReLU(), nn.Linear(int(hidden_dim * reduction_ratio), hidden_dim))
        hidden_layers = [nn.Linear(hidden_dim, output_dim, bias=False)]
        if layer_norm:
            hidden_layers.append(nn.LayerNorm(output_dim))
        hidden_layers.append(get_activation(hidden_activation))
        if dropout_rate > 0:
            hidden_layers.append(nn.Dropout(p=dropout_rate))
        self.hidden_layer = nn.Sequential(*hidden_layers)

    def forward(self, V_emb, V_hidden):
        V_mask = self.mask_layer(V_emb)
        v_out = self.hidden_layer(V_mask * V_hidden)
        return v_out

def __init__(self, input_dim, hidden_dim, output_dim, hidden_activation='ReLU', reduction_ratio=1, dropout_rate=0, layer_norm=True):
    super(MaskBlock, self).__init__()
    self.mask_layer = nn.Sequential(nn.Linear(input_dim, int(hidden_dim * reduction_ratio)), nn.ReLU(), nn.Linear(int(hidden_dim * reduction_ratio), hidden_dim))
    hidden_layers = [nn.Linear(hidden_dim, output_dim, bias=False)]
    if layer_norm:
        hidden_layers.append(nn.LayerNorm(output_dim))
    hidden_layers.append(get_activation(hidden_activation))
    if dropout_rate > 0:
        hidden_layers.append(nn.Dropout(p=dropout_rate))
    self.hidden_layer = nn.Sequential(*hidden_layers)

class DeepFM(BaseModel):

    def __init__(self, feature_map, model_id='DeepFM', gpu=-1, learning_rate=0.001, embedding_dim=10, hidden_units=[64, 64, 64], hidden_activations='ReLU', net_dropout=0, batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(DeepFM, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        self.fm = FactorizationMachine(feature_map)
        self.mlp = MLP_Block(input_dim=feature_map.sum_emb_out_dim(), output_dim=1, hidden_units=hidden_units, hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        """
        Inputs: [X,y]
        """
        X = self.get_inputs(inputs)
        feature_emb = self.embedding_layer(X)
        y_pred = self.fm(X, feature_emb)
        y_pred += self.mlp(feature_emb.flatten(start_dim=1))
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred}
        return return_dict

def __init__(self, feature_map, model_id='DeepFM', gpu=-1, learning_rate=0.001, embedding_dim=10, hidden_units=[64, 64, 64], hidden_activations='ReLU', net_dropout=0, batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
    super(DeepFM, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
    self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
    self.fm = FactorizationMachine(feature_map)
    self.mlp = MLP_Block(input_dim=feature_map.sum_emb_out_dim(), output_dim=1, hidden_units=hidden_units, hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm)
    self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
    self.reset_parameters()
    self.model_to_device()

class DeepFM(BaseModel):

    def __init__(self, feature_map, model_id='DeepFM', learning_rate=0.001, embedding_dim=10, hidden_units=[64, 64, 64], hidden_activations='ReLU', net_dropout=0, batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(DeepFM, self).__init__(feature_map, model_id=model_id, **kwargs)
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim, embedding_regularizer=embedding_regularizer)
        self.fm = FactorizationMachine(feature_map, regularizer=embedding_regularizer)
        self.emb_out_dim = feature_map.sum_emb_out_dim()
        self.mlp = MLP_Block(input_dim=self.emb_out_dim, output_dim=1, hidden_units=hidden_units, hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm, regularizer=net_regularizer)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)

    def call(self, inputs, training=False):
        X = self.get_inputs(inputs)
        feature_emb = self.embedding_layer(X)
        y_pred = self.fm(X, feature_emb)
        y_pred += self.mlp(tf.reshape(feature_emb, (-1, self.emb_out_dim)))
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred}
        return return_dict

def __init__(self, feature_map, model_id='DeepFM', learning_rate=0.001, embedding_dim=10, hidden_units=[64, 64, 64], hidden_activations='ReLU', net_dropout=0, batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
    super(DeepFM, self).__init__(feature_map, model_id=model_id, **kwargs)
    self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim, embedding_regularizer=embedding_regularizer)
    self.fm = FactorizationMachine(feature_map, regularizer=embedding_regularizer)
    self.emb_out_dim = feature_map.sum_emb_out_dim()
    self.mlp = MLP_Block(input_dim=self.emb_out_dim, output_dim=1, hidden_units=hidden_units, hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm, regularizer=net_regularizer)
    self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)

class FiGNN(BaseModel):

    def __init__(self, feature_map, model_id='FiGNN', gpu=-1, learning_rate=0.001, embedding_dim=10, gnn_layers=3, use_residual=True, use_gru=True, reuse_graph_layer=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(FiGNN, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        num_fields = feature_map.num_fields
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        self.fignn = FiGNN_Layer(num_fields, embedding_dim, gnn_layers=gnn_layers, reuse_graph_layer=reuse_graph_layer, use_gru=use_gru, use_residual=use_residual)
        self.fc = AttentionalPrediction(num_fields, embedding_dim)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        X = self.get_inputs(inputs)
        feature_emb = self.embedding_layer(X)
        h_out = self.fignn(feature_emb)
        y_pred = self.fc(h_out)
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred}
        return return_dict

def __init__(self, feature_map, model_id='FiGNN', gpu=-1, learning_rate=0.001, embedding_dim=10, gnn_layers=3, use_residual=True, use_gru=True, reuse_graph_layer=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
    super(FiGNN, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
    num_fields = feature_map.num_fields
    self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
    self.fignn = FiGNN_Layer(num_fields, embedding_dim, gnn_layers=gnn_layers, reuse_graph_layer=reuse_graph_layer, use_gru=use_gru, use_residual=use_residual)
    self.fc = AttentionalPrediction(num_fields, embedding_dim)
    self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
    self.reset_parameters()
    self.model_to_device()

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

def __init__(self, num_fields, embedding_dim):
    super(GraphLayer, self).__init__()
    self.W_in = torch.nn.Parameter(torch.Tensor(num_fields, embedding_dim, embedding_dim))
    self.W_out = torch.nn.Parameter(torch.Tensor(num_fields, embedding_dim, embedding_dim))
    nn.init.xavier_normal_(self.W_in)
    nn.init.xavier_normal_(self.W_out)
    self.bias_p = nn.Parameter(torch.zeros(embedding_dim))

class AttentionalPrediction(nn.Module):

    def __init__(self, num_fields, embedding_dim):
        super(AttentionalPrediction, self).__init__()
        self.mlp1 = nn.Linear(embedding_dim, 1, bias=False)
        self.mlp2 = nn.Sequential(nn.Linear(num_fields * embedding_dim, num_fields, bias=False), nn.Sigmoid())

    def forward(self, h):
        score = self.mlp1(h).squeeze(-1)
        weight = self.mlp2(h.flatten(start_dim=1))
        logit = (weight * score).sum(dim=1, keepdim=True)
        return logit

def __init__(self, num_fields, embedding_dim):
    super(AttentionalPrediction, self).__init__()
    self.mlp1 = nn.Linear(embedding_dim, 1, bias=False)
    self.mlp2 = nn.Sequential(nn.Linear(num_fields * embedding_dim, num_fields, bias=False), nn.Sigmoid())

class xDeepFM(BaseModel):

    def __init__(self, feature_map, model_id='xDeepFM', gpu=-1, learning_rate=0.001, embedding_dim=10, dnn_hidden_units=[64, 64, 64], dnn_activations='ReLU', cin_hidden_units=[16, 16, 16], net_dropout=0, batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(xDeepFM, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        self.dnn = MLP_Block(input_dim=feature_map.sum_emb_out_dim(), output_dim=1, hidden_units=dnn_hidden_units, hidden_activations=dnn_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm) if dnn_hidden_units else None
        self.lr_layer = LogisticRegression(feature_map, use_bias=False)
        self.cin = CompressedInteractionNet(feature_map.num_fields, cin_hidden_units, output_dim=1)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        X = self.get_inputs(inputs)
        feature_emb = self.embedding_layer(X)
        lr_logit = self.lr_layer(X)
        cin_logit = self.cin(feature_emb)
        y_pred = lr_logit + cin_logit
        if self.dnn is not None:
            dnn_logit = self.dnn(feature_emb.flatten(start_dim=1))
            y_pred += dnn_logit
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred}
        return return_dict

def __init__(self, feature_map, model_id='xDeepFM', gpu=-1, learning_rate=0.001, embedding_dim=10, dnn_hidden_units=[64, 64, 64], dnn_activations='ReLU', cin_hidden_units=[16, 16, 16], net_dropout=0, batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
    super(xDeepFM, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
    self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
    self.dnn = MLP_Block(input_dim=feature_map.sum_emb_out_dim(), output_dim=1, hidden_units=dnn_hidden_units, hidden_activations=dnn_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm) if dnn_hidden_units else None
    self.lr_layer = LogisticRegression(feature_map, use_bias=False)
    self.cin = CompressedInteractionNet(feature_map.num_fields, cin_hidden_units, output_dim=1)
    self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
    self.reset_parameters()
    self.model_to_device()

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

def __init__(self, num_fields, gate_residual='concat'):
    super(FeatureGating, self).__init__()
    self.linear = nn.Linear(num_fields, num_fields)
    assert gate_residual in ['concat', 'sum']
    self.gate_residual = gate_residual

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

class FactorizedInteraction(nn.Module):

    def __init__(self, input_dim, output_dim, bias=True, residual_type='sum'):
        """ FactorizedInteraction layer is an improvement of nn.Linear to capture quadratic 
            interactions between features.
            Setting `residual_type="concat"` keeps the same number of parameters as nn.Linear
            while `residual_type="sum"` doubles the number of parameters.
        """
        super(FactorizedInteraction, self).__init__()
        self.residual_type = residual_type
        if residual_type == 'sum':
            output_dim = output_dim * 2
        else:
            assert output_dim % 2 == 0, 'output_dim should be divisible by 2.'
        self.linear = nn.Linear(input_dim, output_dim, bias=bias)

    def forward(self, x):
        h = self.linear(x)
        h2, h1 = torch.chunk(h, chunks=2, dim=-1)
        if self.residual_type == 'concat':
            h = torch.cat([h2, h1 * h2], dim=-1)
        elif self.residual_type == 'sum':
            h = h2 + h1 * h2
        return h

def __init__(self, input_dim, output_dim, bias=True, residual_type='sum'):
    """ FactorizedInteraction layer is an improvement of nn.Linear to capture quadratic 
            interactions between features.
            Setting `residual_type="concat"` keeps the same number of parameters as nn.Linear
            while `residual_type="sum"` doubles the number of parameters.
        """
    super(FactorizedInteraction, self).__init__()
    self.residual_type = residual_type
    if residual_type == 'sum':
        output_dim = output_dim * 2
    else:
        assert output_dim % 2 == 0, 'output_dim should be divisible by 2.'
    self.linear = nn.Linear(input_dim, output_dim, bias=bias)

class NFM(BaseModel):

    def __init__(self, feature_map, model_id='NFM', gpu=-1, learning_rate=0.001, embedding_dim=10, hidden_units=[64, 64, 64], hidden_activations='ReLU', embedding_dropout=0, net_dropout=0, batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(NFM, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        self.lr_layer = LogisticRegression(feature_map, use_bias=False)
        self.bi_pooling_layer = InnerProductInteraction(feature_map.num_fields, output='bi_interaction')
        self.dnn = MLP_Block(input_dim=embedding_dim, output_dim=1, hidden_units=hidden_units, hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        """
        Inputs: [X, y]
        """
        X = self.get_inputs(inputs)
        y_pred = self.lr_layer(X)
        feature_emb = self.embedding_layer(X)
        bi_pooling_vec = self.bi_pooling_layer(feature_emb)
        y_pred += self.dnn(bi_pooling_vec)
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred}
        return return_dict

def __init__(self, feature_map, model_id='NFM', gpu=-1, learning_rate=0.001, embedding_dim=10, hidden_units=[64, 64, 64], hidden_activations='ReLU', embedding_dropout=0, net_dropout=0, batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
    super(NFM, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
    self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
    self.lr_layer = LogisticRegression(feature_map, use_bias=False)
    self.bi_pooling_layer = InnerProductInteraction(feature_map.num_fields, output='bi_interaction')
    self.dnn = MLP_Block(input_dim=embedding_dim, output_dim=1, hidden_units=hidden_units, hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm)
    self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
    self.reset_parameters()
    self.model_to_device()

class DCNv2(BaseModel):

    def __init__(self, feature_map, model_id='DCNv2', gpu=-1, model_structure='parallel', use_low_rank_mixture=False, low_rank=32, num_experts=4, learning_rate=0.001, embedding_dim=10, stacked_dnn_hidden_units=[], parallel_dnn_hidden_units=[], dnn_activations='ReLU', num_cross_layers=3, net_dropout=0, batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(DCNv2, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        input_dim = feature_map.sum_emb_out_dim()
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
        X = self.get_inputs(inputs)
        feature_emb = self.embedding_layer(X, flatten_emb=True)
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

def __init__(self, feature_map, model_id='DCNv2', gpu=-1, model_structure='parallel', use_low_rank_mixture=False, low_rank=32, num_experts=4, learning_rate=0.001, embedding_dim=10, stacked_dnn_hidden_units=[], parallel_dnn_hidden_units=[], dnn_activations='ReLU', num_cross_layers=3, net_dropout=0, batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
    super(DCNv2, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
    self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
    input_dim = feature_map.sum_emb_out_dim()
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

class FM(BaseModel):

    def __init__(self, feature_map, model_id='FM', gpu=-1, learning_rate=0.001, embedding_dim=10, regularizer=None, **kwargs):
        super(FM, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=regularizer, net_regularizer=regularizer, **kwargs)
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        self.fm = FactorizationMachine(feature_map)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        """
        Inputs: [X, y]
        """
        X = self.get_inputs(inputs)
        feature_emb = self.embedding_layer(X)
        y_pred = self.fm(X, feature_emb)
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred}
        return return_dict

def __init__(self, feature_map, model_id='FM', gpu=-1, learning_rate=0.001, embedding_dim=10, regularizer=None, **kwargs):
    super(FM, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=regularizer, net_regularizer=regularizer, **kwargs)
    self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
    self.fm = FactorizationMachine(feature_map)
    self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
    self.reset_parameters()
    self.model_to_device()

class DLRM(BaseModel):

    def __init__(self, feature_map, model_id='DLRM', gpu=-1, learning_rate=0.001, embedding_dim=10, top_mlp_units=[64, 64, 64], bottom_mlp_units=[64, 64, 64], top_mlp_activations='ReLU', bottom_mlp_activations='ReLU', top_mlp_dropout=0, bottom_mlp_dropout=0, interaction_op='dot', batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(DLRM, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.dense_feats = [feat for feat, feature_spec in feature_map.features.items() if feature_spec['type'] == 'numeric']
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim, not_required_feature_columns=self.dense_feats)
        if len(self.dense_feats) > 0:
            n_fields = feature_map.num_fields - len(self.dense_feats) + 1
            self.bottom_mlp = MLP_Block(input_dim=len(self.dense_feats), output_dim=embedding_dim, hidden_units=bottom_mlp_units, hidden_activations=bottom_mlp_activations, output_activation=bottom_mlp_activations, dropout_rates=bottom_mlp_dropout, batch_norm=batch_norm)
        else:
            n_fields = feature_map.num_fields
        self.interaction_op = interaction_op
        if self.interaction_op == 'dot':
            self.interact = InnerProductInteraction(num_fields=n_fields, output='inner_product')
            top_input_dim = n_fields * (n_fields - 1) // 2 + embedding_dim * int(len(self.dense_feats) > 0)
        elif self.interaction_op == 'cat':
            self.interact = nn.Flatten(start_dim=1)
            top_input_dim = n_fields * embedding_dim
        else:
            raise ValueError('interaction_op={} not supported.'.format(self.interaction_op))
        self.top_mlp = MLP_Block(input_dim=top_input_dim, output_dim=1, hidden_units=top_mlp_units, hidden_activations=top_mlp_activations, output_activation=self.output_activation, dropout_rates=top_mlp_dropout, batch_norm=batch_norm)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        """
        Inputs: [X,y]
        """
        X = self.get_inputs(inputs)
        feat_emb = self.embedding_layer(X)
        if len(self.dense_feats) > 0:
            dense_x = torch.cat([X[k] for k in self.dense_feats], dim=-1)
            dense_emb = self.bottom_mlp(dense_x)
            feat_emb = torch.cat([feat_emb, dense_emb.unsqueeze(1)], dim=1)
        interact_out = self.interact(feat_emb)
        if self.interaction_op == 'dot' and len(self.dense_feats) > 0:
            interact_out = torch.cat([interact_out, dense_emb], dim=-1)
        y_pred = self.top_mlp(interact_out)
        return_dict = {'y_pred': y_pred}
        return return_dict

def __init__(self, feature_map, model_id='DLRM', gpu=-1, learning_rate=0.001, embedding_dim=10, top_mlp_units=[64, 64, 64], bottom_mlp_units=[64, 64, 64], top_mlp_activations='ReLU', bottom_mlp_activations='ReLU', top_mlp_dropout=0, bottom_mlp_dropout=0, interaction_op='dot', batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
    super(DLRM, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
    self.dense_feats = [feat for feat, feature_spec in feature_map.features.items() if feature_spec['type'] == 'numeric']
    self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim, not_required_feature_columns=self.dense_feats)
    if len(self.dense_feats) > 0:
        n_fields = feature_map.num_fields - len(self.dense_feats) + 1
        self.bottom_mlp = MLP_Block(input_dim=len(self.dense_feats), output_dim=embedding_dim, hidden_units=bottom_mlp_units, hidden_activations=bottom_mlp_activations, output_activation=bottom_mlp_activations, dropout_rates=bottom_mlp_dropout, batch_norm=batch_norm)
    else:
        n_fields = feature_map.num_fields
    self.interaction_op = interaction_op
    if self.interaction_op == 'dot':
        self.interact = InnerProductInteraction(num_fields=n_fields, output='inner_product')
        top_input_dim = n_fields * (n_fields - 1) // 2 + embedding_dim * int(len(self.dense_feats) > 0)
    elif self.interaction_op == 'cat':
        self.interact = nn.Flatten(start_dim=1)
        top_input_dim = n_fields * embedding_dim
    else:
        raise ValueError('interaction_op={} not supported.'.format(self.interaction_op))
    self.top_mlp = MLP_Block(input_dim=top_input_dim, output_dim=1, hidden_units=top_mlp_units, hidden_activations=top_mlp_activations, output_activation=self.output_activation, dropout_rates=top_mlp_dropout, batch_norm=batch_norm)
    self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
    self.reset_parameters()
    self.model_to_device()

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

class DSSM(BaseModel):

    def __init__(self, feature_map, model_id='DSSM', gpu=-1, learning_rate=0.001, embedding_dim=10, user_tower_units=[64, 64, 64], item_tower_units=[64, 64, 64], user_tower_activations='ReLU', item_tower_activations='ReLU', user_tower_dropout=0, item_tower_dropout=0, batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(DSSM, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.embedding_layer = FeatureEmbeddingDict(feature_map, embedding_dim)
        user_fields = sum((1 if feature_spec['source'] == 'user' else 0 for _, feature_spec in feature_map.features.items()))
        item_fields = sum((1 if feature_spec['source'] == 'item' else 0 for _, feature_spec in feature_map.features.items()))
        assert user_fields > 0 and item_fields > 0, 'Feature source is not configured.'
        self.user_tower = MLP_Block(input_dim=embedding_dim * user_fields, output_dim=user_tower_units[-1], hidden_units=user_tower_units[0:-1], hidden_activations=user_tower_activations, output_activation=None, dropout_rates=user_tower_dropout, batch_norm=batch_norm)
        self.item_tower = MLP_Block(input_dim=embedding_dim * item_fields, output_dim=item_tower_units[-1], hidden_units=item_tower_units[0:-1], hidden_activations=item_tower_activations, output_activation=None, dropout_rates=item_tower_dropout, batch_norm=batch_norm)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        """
        Inputs: [X,y]
        """
        X = self.get_inputs(inputs)
        feat_emb_dict = self.embedding_layer(X)
        user_emb = self.embedding_layer.dict2tensor(feat_emb_dict, feature_source='user')
        item_emb = self.embedding_layer.dict2tensor(feat_emb_dict, feature_source='item')
        user_out = self.user_tower(user_emb.flatten(start_dim=1))
        item_out = self.item_tower(item_emb.flatten(start_dim=1))
        y_pred = (user_out * item_out).sum(dim=-1, keepdim=True)
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred}
        return return_dict

def __init__(self, feature_map, model_id='DSSM', gpu=-1, learning_rate=0.001, embedding_dim=10, user_tower_units=[64, 64, 64], item_tower_units=[64, 64, 64], user_tower_activations='ReLU', item_tower_activations='ReLU', user_tower_dropout=0, item_tower_dropout=0, batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
    super(DSSM, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
    self.embedding_layer = FeatureEmbeddingDict(feature_map, embedding_dim)
    user_fields = sum((1 if feature_spec['source'] == 'user' else 0 for _, feature_spec in feature_map.features.items()))
    item_fields = sum((1 if feature_spec['source'] == 'item' else 0 for _, feature_spec in feature_map.features.items()))
    assert user_fields > 0 and item_fields > 0, 'Feature source is not configured.'
    self.user_tower = MLP_Block(input_dim=embedding_dim * user_fields, output_dim=user_tower_units[-1], hidden_units=user_tower_units[0:-1], hidden_activations=user_tower_activations, output_activation=None, dropout_rates=user_tower_dropout, batch_norm=batch_norm)
    self.item_tower = MLP_Block(input_dim=embedding_dim * item_fields, output_dim=item_tower_units[-1], hidden_units=item_tower_units[0:-1], hidden_activations=item_tower_activations, output_activation=None, dropout_rates=item_tower_dropout, batch_norm=batch_norm)
    self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
    self.reset_parameters()
    self.model_to_device()

class SAM(BaseModel):

    def __init__(self, feature_map, model_id='SAM', gpu=-1, learning_rate=0.001, embedding_dim=10, interaction_type='SAM2E', aggregation='concat', num_interaction_layers=3, use_residual=False, embedding_regularizer=None, net_regularizer=None, net_dropout=0, **kwargs):
        super(SAM, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        self.block = SAMBlock(num_interaction_layers, feature_map.num_fields, embedding_dim, use_residual, interaction_type, aggregation, net_dropout)
        if aggregation == 'concat':
            if interaction_type in ['SAM2A', 'SAM2E']:
                self.fc = nn.Linear(embedding_dim * feature_map.num_fields ** 2, 1)
            else:
                self.fc = nn.Linear(feature_map.num_fields * embedding_dim, 1)
        else:
            self.fc = nn.Linear(embedding_dim, 1)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        X = self.get_inputs(inputs)
        feature_emb = self.embedding_layer(X)
        interact_out = self.block(feature_emb)
        y_pred = self.fc(interact_out)
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred}
        return return_dict

def __init__(self, feature_map, model_id='SAM', gpu=-1, learning_rate=0.001, embedding_dim=10, interaction_type='SAM2E', aggregation='concat', num_interaction_layers=3, use_residual=False, embedding_regularizer=None, net_regularizer=None, net_dropout=0, **kwargs):
    super(SAM, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
    self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
    self.block = SAMBlock(num_interaction_layers, feature_map.num_fields, embedding_dim, use_residual, interaction_type, aggregation, net_dropout)
    if aggregation == 'concat':
        if interaction_type in ['SAM2A', 'SAM2E']:
            self.fc = nn.Linear(embedding_dim * feature_map.num_fields ** 2, 1)
        else:
            self.fc = nn.Linear(feature_map.num_fields * embedding_dim, 1)
    else:
        self.fc = nn.Linear(embedding_dim, 1)
    self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
    self.reset_parameters()
    self.model_to_device()

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

def __init__(self, num_fields, embedding_dim, dropout=0):
    super(SAM2A, self).__init__()
    self.W = nn.Parameter(torch.ones(num_fields, num_fields, embedding_dim))
    self.dropout = nn.Dropout(p=dropout) if dropout > 0 else None

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

def __init__(self, embedding_dim, dropout=0):
    super(SAM2E, self).__init__()
    self.dropout = nn.Dropout(p=dropout) if dropout > 0 else None

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

def __init__(self, num_fields, embedding_dim, use_residual=True, dropout=0):
    super(SAM3A, self).__init__()
    self.W = nn.Parameter(torch.ones(num_fields, num_fields, embedding_dim))
    self.K = nn.Linear(embedding_dim, embedding_dim, bias=False)
    self.use_residual = use_residual
    if use_residual:
        self.Q = nn.Linear(embedding_dim, embedding_dim, bias=False)
    self.dropout = nn.Dropout(p=dropout) if dropout > 0 else None

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

def __init__(self, embedding_dim, use_residual=True, dropout=0):
    super(SAM3E, self).__init__()
    self.K = nn.Linear(embedding_dim, embedding_dim, bias=False)
    self.use_residual = use_residual
    if use_residual:
        self.Q = nn.Linear(embedding_dim, embedding_dim, bias=False)
    self.dropout = nn.Dropout(p=dropout) if dropout > 0 else None

class DNN(BaseModel):

    def __init__(self, feature_map, model_id='DNN', learning_rate=0.001, embedding_dim=10, hidden_units=[64, 64, 64], hidden_activations='ReLU', net_dropout=0, batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(DNN, self).__init__(feature_map, model_id=model_id, **kwargs)
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim, embedding_regularizer=embedding_regularizer)
        self.emb_out_dim = feature_map.sum_emb_out_dim()
        self.mlp = MLP_Block(input_dim=self.emb_out_dim, output_dim=1, hidden_units=hidden_units, hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm, regularizer=net_regularizer)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)

    def call(self, inputs, training=False):
        X = self.get_inputs(inputs)
        feature_emb = self.embedding_layer(X)
        y_pred = self.mlp(tf.reshape(feature_emb, (-1, self.emb_out_dim)))
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred}
        return return_dict

def __init__(self, feature_map, model_id='DNN', learning_rate=0.001, embedding_dim=10, hidden_units=[64, 64, 64], hidden_activations='ReLU', net_dropout=0, batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
    super(DNN, self).__init__(feature_map, model_id=model_id, **kwargs)
    self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim, embedding_regularizer=embedding_regularizer)
    self.emb_out_dim = feature_map.sum_emb_out_dim()
    self.mlp = MLP_Block(input_dim=self.emb_out_dim, output_dim=1, hidden_units=hidden_units, hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm, regularizer=net_regularizer)
    self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)

class DNN(BaseModel):

    def __init__(self, feature_map, model_id='DNN', gpu=-1, learning_rate=0.001, embedding_dim=10, hidden_units=[64, 64, 64], hidden_activations='ReLU', net_dropout=0, batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(DNN, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        self.mlp = MLP_Block(input_dim=feature_map.sum_emb_out_dim(), output_dim=1, hidden_units=hidden_units, hidden_activations=hidden_activations, output_activation=self.output_activation, dropout_rates=net_dropout, batch_norm=batch_norm)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        """
        Inputs: [X,y]
        """
        X = self.get_inputs(inputs)
        feature_emb = self.embedding_layer(X, flatten_emb=True)
        y_pred = self.mlp(feature_emb)
        return_dict = {'y_pred': y_pred}
        return return_dict

def __init__(self, feature_map, model_id='DNN', gpu=-1, learning_rate=0.001, embedding_dim=10, hidden_units=[64, 64, 64], hidden_activations='ReLU', net_dropout=0, batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
    super(DNN, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
    self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
    self.mlp = MLP_Block(input_dim=feature_map.sum_emb_out_dim(), output_dim=1, hidden_units=hidden_units, hidden_activations=hidden_activations, output_activation=self.output_activation, dropout_rates=net_dropout, batch_norm=batch_norm)
    self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
    self.reset_parameters()
    self.model_to_device()

class FiBiNET(BaseModel):

    def __init__(self, feature_map, model_id='FiBiNET', gpu=-1, learning_rate=0.001, embedding_dim=10, hidden_units=[], hidden_activations='ReLU', excitation_activation='ReLU', reduction_ratio=3, bilinear_type='field_interaction', net_dropout=0, batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(FiBiNET, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        num_fields = feature_map.num_fields
        self.senet_layer = SqueezeExcitation(num_fields, reduction_ratio, excitation_activation)
        self.bilinear_interaction1 = BilinearInteractionV2(num_fields, embedding_dim, bilinear_type)
        self.bilinear_interaction2 = BilinearInteractionV2(num_fields, embedding_dim, bilinear_type)
        self.lr_layer = LogisticRegression(feature_map, use_bias=False)
        input_dim = num_fields * (num_fields - 1) * embedding_dim
        self.dnn = MLP_Block(input_dim=input_dim, output_dim=1, hidden_units=hidden_units, hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        """
        Inputs: [X, y]
        """
        X = self.get_inputs(inputs)
        feature_emb = self.embedding_layer(X)
        senet_emb = self.senet_layer(feature_emb)
        bilinear_p = self.bilinear_interaction1(feature_emb)
        bilinear_q = self.bilinear_interaction2(senet_emb)
        comb_out = torch.flatten(torch.cat([bilinear_p, bilinear_q], dim=1), start_dim=1)
        dnn_out = self.dnn(comb_out)
        y_pred = self.lr_layer(X) + dnn_out
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred}
        return return_dict

def __init__(self, feature_map, model_id='FiBiNET', gpu=-1, learning_rate=0.001, embedding_dim=10, hidden_units=[], hidden_activations='ReLU', excitation_activation='ReLU', reduction_ratio=3, bilinear_type='field_interaction', net_dropout=0, batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
    super(FiBiNET, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
    self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
    num_fields = feature_map.num_fields
    self.senet_layer = SqueezeExcitation(num_fields, reduction_ratio, excitation_activation)
    self.bilinear_interaction1 = BilinearInteractionV2(num_fields, embedding_dim, bilinear_type)
    self.bilinear_interaction2 = BilinearInteractionV2(num_fields, embedding_dim, bilinear_type)
    self.lr_layer = LogisticRegression(feature_map, use_bias=False)
    input_dim = num_fields * (num_fields - 1) * embedding_dim
    self.dnn = MLP_Block(input_dim=input_dim, output_dim=1, hidden_units=hidden_units, hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm)
    self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
    self.reset_parameters()
    self.model_to_device()

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

class BehaviorRefinerLayer(nn.Module):

    def __init__(self, model_dim=64, ffn_dim=64, num_heads=4, attn_dropout=0.0, net_dropout=0.0, layer_norm=True, use_residual=True):
        super(BehaviorRefinerLayer, self).__init__()
        self.attention = MultiheadAttention(model_dim, num_heads=num_heads, dropout=attn_dropout, batch_first=True)
        self.ffn = nn.Sequential(nn.Linear(model_dim, ffn_dim), nn.ReLU(), nn.Linear(ffn_dim, model_dim))
        self.use_residual = use_residual
        self.dropout = nn.Dropout(net_dropout)
        self.layer_norm = nn.LayerNorm(model_dim) if layer_norm else None

    def forward(self, x, attn_mask=None):
        attn_mask = 1 - attn_mask.float()
        attn, _ = self.attention(x, x, x, attn_mask=attn_mask)
        s = self.dropout(attn)
        if self.use_residual:
            s += x
        if self.layer_norm is not None:
            s = self.layer_norm(s)
        out = self.ffn(s)
        if self.use_residual:
            out += s
        return out

def __init__(self, model_dim=64, ffn_dim=64, num_heads=4, attn_dropout=0.0, net_dropout=0.0, layer_norm=True, use_residual=True):
    super(BehaviorRefinerLayer, self).__init__()
    self.attention = MultiheadAttention(model_dim, num_heads=num_heads, dropout=attn_dropout, batch_first=True)
    self.ffn = nn.Sequential(nn.Linear(model_dim, ffn_dim), nn.ReLU(), nn.Linear(ffn_dim, model_dim))
    self.use_residual = use_residual
    self.dropout = nn.Dropout(net_dropout)
    self.layer_norm = nn.LayerNorm(model_dim) if layer_norm else None

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

def __init__(self, model_dim=64, attention_hidden_units=[80, 40], attention_activation='ReLU', attention_dropout=0, use_pos_emb=True, pos_emb_dim=8, max_seq_len=10):
    super(TargetAttention, self).__init__()
    self.model_dim = model_dim
    self.use_pos_emb = use_pos_emb
    if self.use_pos_emb:
        self.pos_emb = nn.Parameter(torch.zeros(max_seq_len, pos_emb_dim))
        self.W_proj = nn.Linear(model_dim + pos_emb_dim, model_dim)
    self.attn_mlp = MLP_Block(input_dim=model_dim * 4, output_dim=1, hidden_units=attention_hidden_units, hidden_activations=attention_activation, output_activation=None, dropout_rates=attention_dropout, batch_norm=False)

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

def __init__(self, feature_map, model_id='FFM', gpu=-1, task='binary_classification', learning_rate=0.001, embedding_dim=2, regularizer=None, **kwargs):
    super(FFM, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=regularizer, net_regularizer=regularizer, **kwargs)
    self.num_fields = feature_map.num_fields
    self.lr_layer = LogisticRegression(feature_map)
    self.embedding_layers = nn.ModuleList([FeatureEmbedding(feature_map, embedding_dim) for x in range(self.num_fields - 1)])
    self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
    self.reset_parameters()
    self.model_to_device()

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

def __init__(self, feature_map, model_id='LorentzFM', gpu=-1, learning_rate=0.001, embedding_dim=10, embedding_dropout=0, regularizer=None, **kwargs):
    super(LorentzFM, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=regularizer, net_regularizer=regularizer, **kwargs)
    self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
    self.inner_product_layer = InnerProductInteraction(feature_map.num_fields, output='inner_product')
    self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
    self.reset_parameters()
    self.model_to_device()

class FwFM(BaseModel):
    """ The FwFM model
        Reference:
          - Field-weighted Factorization Machines for Click-Through Rate Prediction in Display Advertising, WWW'2018.
    """

    def __init__(self, feature_map, model_id='FwFM', gpu=-1, learning_rate=0.001, embedding_dim=10, regularizer=None, linear_type='FiLV', **kwargs):
        """ 
        linear_type: `LW`, `FeLV`, or `FiLV`
        """
        super(FwFM, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=regularizer, net_regularizer=regularizer, **kwargs)
        interact_dim = int(feature_map.num_fields * (feature_map.num_fields - 1) / 2)
        self.interaction_weight = nn.Linear(interact_dim, 1)
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        self.inner_product_layer = InnerProductInteraction(feature_map.num_fields, output='inner_product')
        self._linear_type = linear_type
        if linear_type == 'LW':
            self.linear_weight_layer = FeatureEmbedding(feature_map, 1, use_pretrain=False)
        elif linear_type == 'FeLV':
            self.linear_weight_layer = FeatureEmbedding(feature_map, embedding_dim)
        elif linear_type == 'FiLV':
            self.linear_weight_layer = nn.Linear(feature_map.num_fields * embedding_dim, 1, bias=False)
        else:
            raise NotImplementedError('linear_type={} is not supported.'.format(linear_type))
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        """
        Inputs: [X, y]
        """
        X = self.get_inputs(inputs)
        feature_emb = self.embedding_layer(X)
        inner_product_vec = self.inner_product_layer(feature_emb)
        poly2_part = self.interaction_weight(inner_product_vec)
        if self._linear_type == 'LW':
            linear_weights = self.linear_weight_layer(X)
            linear_part = linear_weights.sum(dim=1)
        elif self._linear_type == 'FeLV':
            linear_weights = self.linear_weight_layer(X)
            linear_part = (feature_emb * linear_weights).sum((1, 2)).view(-1, 1)
        elif self._linear_type == 'FiLV':
            linear_part = self.linear_weight_layer(feature_emb.flatten(start_dim=1))
        y_pred = poly2_part + linear_part
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred}
        return return_dict

def __init__(self, feature_map, model_id='FwFM', gpu=-1, learning_rate=0.001, embedding_dim=10, regularizer=None, linear_type='FiLV', **kwargs):
    """ 
        linear_type: `LW`, `FeLV`, or `FiLV`
        """
    super(FwFM, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=regularizer, net_regularizer=regularizer, **kwargs)
    interact_dim = int(feature_map.num_fields * (feature_map.num_fields - 1) / 2)
    self.interaction_weight = nn.Linear(interact_dim, 1)
    self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
    self.inner_product_layer = InnerProductInteraction(feature_map.num_fields, output='inner_product')
    self._linear_type = linear_type
    if linear_type == 'LW':
        self.linear_weight_layer = FeatureEmbedding(feature_map, 1, use_pretrain=False)
    elif linear_type == 'FeLV':
        self.linear_weight_layer = FeatureEmbedding(feature_map, embedding_dim)
    elif linear_type == 'FiLV':
        self.linear_weight_layer = nn.Linear(feature_map.num_fields * embedding_dim, 1, bias=False)
    else:
        raise NotImplementedError('linear_type={} is not supported.'.format(linear_type))
    self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
    self.reset_parameters()
    self.model_to_device()

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

def __init__(self, max_length, hidden_size, hidden_dropout_prob, n_block):
    super(FilterLayer2, self).__init__()
    self.complex_weight = nn.Parameter(torch.randn(n_block, hidden_size // n_block, hidden_size // n_block, 2, dtype=torch.float32) * 0.02)
    self.out_dropout = nn.Dropout(hidden_dropout_prob)
    self.LayerNorm = LayerNorm(hidden_size, eps=1e-12)
    self.n = n_block

class LayerNorm(nn.Module):

    def __init__(self, hidden_size, eps=1e-12):
        """ Construct a layernorm module in the TF style (epsilon inside the square root).
        """
        super(LayerNorm, self).__init__()
        self.weight = nn.Parameter(torch.ones(hidden_size))
        self.bias = nn.Parameter(torch.zeros(hidden_size))
        self.variance_epsilon = eps

    def forward(self, x):
        u = x.mean(-1, keepdim=True)
        s = (x - u).pow(2).mean(-1, keepdim=True)
        x = (x - u) / torch.sqrt(s + self.variance_epsilon)
        return self.weight * x + self.bias

def __init__(self, hidden_size, eps=1e-12):
    """ Construct a layernorm module in the TF style (epsilon inside the square root).
        """
    super(LayerNorm, self).__init__()
    self.weight = nn.Parameter(torch.ones(hidden_size))
    self.bias = nn.Parameter(torch.zeros(hidden_size))
    self.variance_epsilon = eps

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

def __init__(self, model_dim, attention_type='bilinear_attention', attention_hidden_units=[80, 40], attention_activation='Dice', use_attention_softmax=True, attention_dropout=0.0):
    super(AttentionLayer, self).__init__()
    assert attention_type in ['bilinear_attention', 'dot_attention', 'din_attention'], 'attention_type={} is not supported.'.format(attention_type)
    self.attention_type = attention_type
    self.use_attention_softmax = use_attention_softmax
    if attention_type == 'bilinear_attention':
        self.W_kernel = nn.Parameter(torch.eye(model_dim))
    elif attention_type == 'din_attention':
        self.attn_mlp = MLP_Block(input_dim=model_dim * 4, output_dim=1, hidden_units=attention_hidden_units, hidden_activations=attention_activation, output_activation=None, dropout_rates=attention_dropout, batch_norm=False)

class AGRUCell(nn.Module):
    """AGRUCell with attentional update gate
        Reference: GRUCell from https://github.com/emadRad/lstm-gru-pytorch/blob/master/lstm_gru.ipynb

    """

    def __init__(self, input_size, hidden_size, bias=True):
        super(AGRUCell, self).__init__()
        self.x2h = nn.Linear(input_size, 3 * hidden_size, bias=bias)
        self.h2h = nn.Linear(hidden_size, 3 * hidden_size, bias=bias)

    def forward(self, x, hx, attn):
        gate_x = self.x2h(x)
        gate_h = self.h2h(hx)
        i_u, i_r, i_n = gate_x.chunk(3, 1)
        h_u, h_r, h_n = gate_h.chunk(3, 1)
        reset_gate = torch.sigmoid(i_r + h_r)
        new_gate = torch.tanh(i_n + reset_gate * h_n)
        hy = hx + attn.view(-1, 1) * (new_gate - hx)
        return hy

def __init__(self, input_size, hidden_size, bias=True):
    super(AGRUCell, self).__init__()
    self.x2h = nn.Linear(input_size, 3 * hidden_size, bias=bias)
    self.h2h = nn.Linear(hidden_size, 3 * hidden_size, bias=bias)

class AUGRUCell(nn.Module):
    """AUGRUCell with attentional update gate
        Reference: GRUCell from https://github.com/emadRad/lstm-gru-pytorch/blob/master/lstm_gru.ipynb

    """

    def __init__(self, input_size, hidden_size, bias=True):
        super(AUGRUCell, self).__init__()
        self.x2h = nn.Linear(input_size, 3 * hidden_size, bias=bias)
        self.h2h = nn.Linear(hidden_size, 3 * hidden_size, bias=bias)

    def forward(self, x, hx, attn):
        gate_x = self.x2h(x)
        gate_h = self.h2h(hx)
        i_u, i_r, i_n = gate_x.chunk(3, 1)
        h_u, h_r, h_n = gate_h.chunk(3, 1)
        update_gate = torch.sigmoid(i_u + h_u)
        update_gate = update_gate * attn.unsqueeze(-1)
        reset_gate = torch.sigmoid(i_r + h_r)
        new_gate = torch.tanh(i_n + reset_gate * h_n)
        hy = hx + update_gate * (new_gate - hx)
        return hy

def __init__(self, input_size, hidden_size, bias=True):
    super(AUGRUCell, self).__init__()
    self.x2h = nn.Linear(input_size, 3 * hidden_size, bias=bias)
    self.h2h = nn.Linear(hidden_size, 3 * hidden_size, bias=bias)

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

def __init__(self, input_size, hidden_size, bias=True, gru_type='AUGRU'):
    super(DynamicGRU, self).__init__()
    self.hidden_size = hidden_size
    self.gru_type = gru_type
    if gru_type == 'AUGRU':
        self.gru_cell = AUGRUCell(input_size, hidden_size, bias=bias)
    elif gru_type == 'AGRU':
        self.gru_cell = AGRUCell(input_size, hidden_size, bias=bias)

class InterHAt(BaseModel):

    def __init__(self, feature_map, model_id='InterHAt', gpu=-1, learning_rate=0.001, embedding_dim=10, hidden_dim=None, order=2, num_heads=1, attention_dim=10, hidden_units=[64, 64], hidden_activations='relu', batch_norm=False, layer_norm=True, use_residual=True, net_dropout=0, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(InterHAt, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.order = order
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        self.multi_head_attention = MultiHeadSelfAttention(embedding_dim, attention_dim, num_heads, dropout_rate=net_dropout, use_residual=use_residual, use_scale=True, layer_norm=layer_norm)
        self.feedforward = FeedForwardNetwork(embedding_dim, hidden_dim=hidden_dim, layer_norm=layer_norm, use_residual=use_residual)
        self.aggregation_layers = nn.ModuleList([AttentionalAggregation(embedding_dim, hidden_dim) for _ in range(order)])
        self.attentional_score = AttentionalAggregation(embedding_dim, hidden_dim)
        self.mlp = MLP_Block(input_dim=embedding_dim, output_dim=1, hidden_units=hidden_units, hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        """
        Inputs: [X, y]
        """
        X = self.get_inputs(inputs)
        X0 = self.embedding_layer(X)
        X1 = self.feedforward(self.multi_head_attention(X0))
        X_p = X1
        agg_u = []
        for p in range(self.order):
            u_p = self.aggregation_layers[p](X_p)
            agg_u.append(u_p)
            if p != self.order - 1:
                X_p = u_p.unsqueeze(1) * X1 + X_p
        U = torch.stack(agg_u, dim=1)
        u_f = self.attentional_score(U)
        y_pred = self.mlp(u_f)
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred}
        return return_dict

def __init__(self, feature_map, model_id='InterHAt', gpu=-1, learning_rate=0.001, embedding_dim=10, hidden_dim=None, order=2, num_heads=1, attention_dim=10, hidden_units=[64, 64], hidden_activations='relu', batch_norm=False, layer_norm=True, use_residual=True, net_dropout=0, embedding_regularizer=None, net_regularizer=None, **kwargs):
    super(InterHAt, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
    self.order = order
    self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
    self.multi_head_attention = MultiHeadSelfAttention(embedding_dim, attention_dim, num_heads, dropout_rate=net_dropout, use_residual=use_residual, use_scale=True, layer_norm=layer_norm)
    self.feedforward = FeedForwardNetwork(embedding_dim, hidden_dim=hidden_dim, layer_norm=layer_norm, use_residual=use_residual)
    self.aggregation_layers = nn.ModuleList([AttentionalAggregation(embedding_dim, hidden_dim) for _ in range(order)])
    self.attentional_score = AttentionalAggregation(embedding_dim, hidden_dim)
    self.mlp = MLP_Block(input_dim=embedding_dim, output_dim=1, hidden_units=hidden_units, hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm)
    self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
    self.reset_parameters()
    self.model_to_device()

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

def __init__(self, embedding_dim, hidden_dim=None):
    super(AttentionalAggregation, self).__init__()
    if hidden_dim is None:
        hidden_dim = 4 * embedding_dim
    self.agg = nn.Sequential(nn.Linear(embedding_dim, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, 1, bias=False), nn.Softmax(dim=1))

class FeedForwardNetwork(nn.Module):

    def __init__(self, input_dim, hidden_dim=None, layer_norm=True, use_residual=True):
        super(FeedForwardNetwork, self).__init__()
        self.use_residual = use_residual
        if hidden_dim is None:
            hidden_dim = 4 * input_dim
        self.ffn = nn.Sequential(nn.Linear(input_dim, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, input_dim))
        self.layer_norm = nn.LayerNorm(input_dim) if layer_norm else None

    def forward(self, X):
        output = self.ffn(X)
        if self.use_residual:
            output += X
        if self.layer_norm is not None:
            output = self.layer_norm(output)
        return output

def __init__(self, input_dim, hidden_dim=None, layer_norm=True, use_residual=True):
    super(FeedForwardNetwork, self).__init__()
    self.use_residual = use_residual
    if hidden_dim is None:
        hidden_dim = 4 * input_dim
    self.ffn = nn.Sequential(nn.Linear(input_dim, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, input_dim))
    self.layer_norm = nn.LayerNorm(input_dim) if layer_norm else None

class DualMLP(BaseModel):

    def __init__(self, feature_map, model_id='DualMLP', gpu=-1, learning_rate=0.001, embedding_dim=10, mlp1_hidden_units=[64, 64, 64], mlp1_hidden_activations='ReLU', mlp1_dropout=0, mlp1_batch_norm=False, mlp2_hidden_units=[64, 64, 64], mlp2_hidden_activations='ReLU', mlp2_dropout=0, mlp2_batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(DualMLP, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        self.mlp1 = MLP_Block(input_dim=embedding_dim * feature_map.num_fields, output_dim=1, hidden_units=mlp1_hidden_units, hidden_activations=mlp1_hidden_activations, output_activation=None, dropout_rates=mlp1_dropout, batch_norm=mlp1_batch_norm)
        self.mlp2 = MLP_Block(input_dim=embedding_dim * feature_map.num_fields, output_dim=1, hidden_units=mlp2_hidden_units, hidden_activations=mlp2_hidden_activations, output_activation=None, dropout_rates=mlp2_dropout, batch_norm=mlp2_batch_norm)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        X = self.get_inputs(inputs)
        flat_emb = self.embedding_layer(X).flatten(start_dim=1)
        y_pred = self.mlp1(flat_emb) + self.mlp2(flat_emb)
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred}
        return return_dict

def __init__(self, feature_map, model_id='DualMLP', gpu=-1, learning_rate=0.001, embedding_dim=10, mlp1_hidden_units=[64, 64, 64], mlp1_hidden_activations='ReLU', mlp1_dropout=0, mlp1_batch_norm=False, mlp2_hidden_units=[64, 64, 64], mlp2_hidden_activations='ReLU', mlp2_dropout=0, mlp2_batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
    super(DualMLP, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
    self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
    self.mlp1 = MLP_Block(input_dim=embedding_dim * feature_map.num_fields, output_dim=1, hidden_units=mlp1_hidden_units, hidden_activations=mlp1_hidden_activations, output_activation=None, dropout_rates=mlp1_dropout, batch_norm=mlp1_batch_norm)
    self.mlp2 = MLP_Block(input_dim=embedding_dim * feature_map.num_fields, output_dim=1, hidden_units=mlp2_hidden_units, hidden_activations=mlp2_hidden_activations, output_activation=None, dropout_rates=mlp2_dropout, batch_norm=mlp2_batch_norm)
    self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
    self.reset_parameters()
    self.model_to_device()

class FinalMLP(BaseModel):

    def __init__(self, feature_map, model_id='FinalMLP', gpu=-1, learning_rate=0.001, embedding_dim=10, mlp1_hidden_units=[64, 64, 64], mlp1_hidden_activations='ReLU', mlp1_dropout=0, mlp1_batch_norm=False, mlp2_hidden_units=[64, 64, 64], mlp2_hidden_activations='ReLU', mlp2_dropout=0, mlp2_batch_norm=False, use_fs=True, fs_hidden_units=[64], fs1_context=[], fs2_context=[], num_heads=1, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(FinalMLP, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        feature_dim = embedding_dim * feature_map.num_fields
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
        """
        Inputs: [X,y]
        """
        X = self.get_inputs(inputs)
        flat_emb = self.embedding_layer(X).flatten(start_dim=1)
        if self.use_fs:
            feat1, feat2 = self.fs_module(X, flat_emb)
        else:
            feat1, feat2 = (flat_emb, flat_emb)
        y_pred = self.fusion_module(self.mlp1(feat1), self.mlp2(feat2))
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred}
        return return_dict

def __init__(self, feature_map, model_id='FinalMLP', gpu=-1, learning_rate=0.001, embedding_dim=10, mlp1_hidden_units=[64, 64, 64], mlp1_hidden_activations='ReLU', mlp1_dropout=0, mlp1_batch_norm=False, mlp2_hidden_units=[64, 64, 64], mlp2_hidden_activations='ReLU', mlp2_dropout=0, mlp2_batch_norm=False, use_fs=True, fs_hidden_units=[64], fs1_context=[], fs2_context=[], num_heads=1, embedding_regularizer=None, net_regularizer=None, **kwargs):
    super(FinalMLP, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
    self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
    feature_dim = embedding_dim * feature_map.num_fields
    self.mlp1 = MLP_Block(input_dim=feature_dim, output_dim=None, hidden_units=mlp1_hidden_units, hidden_activations=mlp1_hidden_activations, output_activation=None, dropout_rates=mlp1_dropout, batch_norm=mlp1_batch_norm)
    self.mlp2 = MLP_Block(input_dim=feature_dim, output_dim=None, hidden_units=mlp2_hidden_units, hidden_activations=mlp2_hidden_activations, output_activation=None, dropout_rates=mlp2_dropout, batch_norm=mlp2_batch_norm)
    self.use_fs = use_fs
    if self.use_fs:
        self.fs_module = FeatureSelection(feature_map, feature_dim, embedding_dim, fs_hidden_units, fs1_context, fs2_context)
    self.fusion_module = InteractionAggregation(mlp1_hidden_units[-1], mlp2_hidden_units[-1], output_dim=1, num_heads=num_heads)
    self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
    self.reset_parameters()
    self.model_to_device()

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

class WuKong(BaseModel):
    """
    The WuKong model class that implements Meta's ICML'24 paper.

    Args:
        feature_map: A FeatureMap instance used to store feature specs (e.g., vocab_size).
        model_id: Equivalent to model class name by default, which is used in config to determine 
            which model to call.
        gpu: gpu device used to load model. -1 means cpu (default=-1).
        learning_rate: learning rate for training (default=1e-3).
        embedding_dim: embedding dimension of features (default=64).
        num_wukong_layers: number of WuKong layers (default=3).
        lcb_features: dimension of compressed features in LCB (default=40).
        fmb_features: dimension of FMB output (default=40).
        fmb_mlp_units: hidden MLP units of FMB (default=[32,32]).
        fmb_mlp_activations: hidden MLP activations of FMB (default=relu).
        fmp_rank_k: dimension of projection matrix in FMB (default=8).
        mlp_hidden_units: hidden units of MLP on top of WuKong (default=[32,32]).
        mlp_hidden_activations: hidden activations of MLP on top of WuKong (default=[32,32]).
        net_dropout: dropout rate used in Wukong (default=0).
        embedding_regularizer: regularization term used for embedding parameters (default=None).
        net_regularizer: regularization term used for network parameters (default=None).
    """

    def __init__(self, feature_map, model_id='WuKong', gpu=-1, learning_rate=0.001, embedding_dim=64, num_wukong_layers=3, lcb_features=40, fmb_features=40, fmb_mlp_units=[32, 32], fmb_mlp_activations='relu', fmp_rank_k=8, mlp_hidden_units=[32, 32], mlp_hidden_activations='relu', mlp_batch_norm=True, layer_norm=True, net_dropout=0, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(WuKong, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.feature_map = feature_map
        self.embedding_dim = embedding_dim
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        output_features = lcb_features + fmb_features
        self.wukong_stack = nn.Sequential(*[WuKongLayer(input_features=feature_map.num_fields if i == 0 else output_features, lcb_features=lcb_features, fmb_features=fmb_features, embedding_dim=embedding_dim, fmp_rank_k=fmp_rank_k, fmb_mlp_units=fmb_mlp_units, fmb_mlp_activations=fmb_mlp_activations, fmb_dropout=net_dropout, layer_norm=layer_norm) for i in range(num_wukong_layers)])
        self.fc = MLP_Block(input_dim=output_features * embedding_dim, output_dim=1, hidden_units=mlp_hidden_units, hidden_activations=mlp_hidden_activations, output_activation=self.output_activation, batch_norm=mlp_batch_norm)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        X = self.get_inputs(inputs)
        feature_emb = self.embedding_layer(X)
        wukong_out = self.wukong_stack(feature_emb)
        y_pred = self.fc(wukong_out.flatten(start_dim=1))
        return_dict = {'y_pred': y_pred}
        return return_dict

def __init__(self, feature_map, model_id='WuKong', gpu=-1, learning_rate=0.001, embedding_dim=64, num_wukong_layers=3, lcb_features=40, fmb_features=40, fmb_mlp_units=[32, 32], fmb_mlp_activations='relu', fmp_rank_k=8, mlp_hidden_units=[32, 32], mlp_hidden_activations='relu', mlp_batch_norm=True, layer_norm=True, net_dropout=0, embedding_regularizer=None, net_regularizer=None, **kwargs):
    super(WuKong, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
    self.feature_map = feature_map
    self.embedding_dim = embedding_dim
    self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
    output_features = lcb_features + fmb_features
    self.wukong_stack = nn.Sequential(*[WuKongLayer(input_features=feature_map.num_fields if i == 0 else output_features, lcb_features=lcb_features, fmb_features=fmb_features, embedding_dim=embedding_dim, fmp_rank_k=fmp_rank_k, fmb_mlp_units=fmb_mlp_units, fmb_mlp_activations=fmb_mlp_activations, fmb_dropout=net_dropout, layer_norm=layer_norm) for i in range(num_wukong_layers)])
    self.fc = MLP_Block(input_dim=output_features * embedding_dim, output_dim=1, hidden_units=mlp_hidden_units, hidden_activations=mlp_hidden_activations, output_activation=self.output_activation, batch_norm=mlp_batch_norm)
    self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
    self.reset_parameters()
    self.model_to_device()

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

class LinearCompressionBlock(nn.Module):
    """ Linear Compression Block (LCB) """

    def __init__(self, input_features=16, output_features=8):
        super(LinearCompressionBlock, self).__init__()
        self.linear = nn.Linear(input_features, output_features, bias=False)

    def forward(self, x):
        out = self.linear(x.transpose(1, 2))
        return out.transpose(1, 2)

def __init__(self, input_features=16, output_features=8):
    super(LinearCompressionBlock, self).__init__()
    self.linear = nn.Linear(input_features, output_features, bias=False)

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

def __init__(self, input_features=16, lcb_features=8, fmb_features=8, embedding_dim=16, fmp_rank_k=4, fmb_mlp_units=[16, 16], fmb_mlp_activations='relu', fmb_dropout=0.1, layer_norm=True):
    super(WuKongLayer, self).__init__()
    self.fmb = FactorizationMachineBlock(input_features, fmb_features, embedding_dim, fmp_rank_k, fmb_mlp_units, fmb_mlp_activations, fmb_dropout)
    self.lcb = LinearCompressionBlock(input_features, lcb_features)
    self.layer_norm = nn.LayerNorm(embedding_dim) if layer_norm else None
    if input_features != lcb_features + fmb_features:
        self.residual_proj = nn.Linear(input_features, lcb_features + fmb_features)

class LR(BaseModel):

    def __init__(self, feature_map, model_id='LR', gpu=-1, learning_rate=0.001, regularizer=None, **kwargs):
        super(LR, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=regularizer, net_regularizer=regularizer, **kwargs)
        self.lr_layer = LogisticRegression(feature_map, use_bias=True)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        """
        Inputs: [X, y]
        """
        X = self.get_inputs(inputs)
        y_pred = self.lr_layer(X)
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred}
        return return_dict

def __init__(self, feature_map, model_id='LR', gpu=-1, learning_rate=0.001, regularizer=None, **kwargs):
    super(LR, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=regularizer, net_regularizer=regularizer, **kwargs)
    self.lr_layer = LogisticRegression(feature_map, use_bias=True)
    self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
    self.reset_parameters()
    self.model_to_device()

class PNN(BaseModel):

    def __init__(self, feature_map, model_id='PNN', gpu=-1, learning_rate=0.001, embedding_dim=10, hidden_units=[64, 64, 64], hidden_activations='ReLU', net_dropout=0, batch_norm=False, product_type='inner', embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(PNN, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        if product_type != 'inner':
            raise NotImplementedError('product_type={} has not been implemented.'.format(product_type))
        self.inner_product_layer = InnerProductInteraction(feature_map.num_fields, output='inner_product')
        input_dim = int(feature_map.num_fields * (feature_map.num_fields - 1) / 2) + feature_map.num_fields * embedding_dim
        self.dnn = MLP_Block(input_dim=input_dim, output_dim=1, hidden_units=hidden_units, hidden_activations=hidden_activations, output_activation=self.output_activation, dropout_rates=net_dropout, batch_norm=batch_norm)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        """
        Inputs: [X, y]
        """
        X = self.get_inputs(inputs)
        feature_emb = self.embedding_layer(X)
        inner_products = self.inner_product_layer(feature_emb)
        dense_input = torch.cat([feature_emb.flatten(start_dim=1), inner_products], dim=1)
        y_pred = self.dnn(dense_input)
        return_dict = {'y_pred': y_pred}
        return return_dict

def __init__(self, feature_map, model_id='PNN', gpu=-1, learning_rate=0.001, embedding_dim=10, hidden_units=[64, 64, 64], hidden_activations='ReLU', net_dropout=0, batch_norm=False, product_type='inner', embedding_regularizer=None, net_regularizer=None, **kwargs):
    super(PNN, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
    self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
    if product_type != 'inner':
        raise NotImplementedError('product_type={} has not been implemented.'.format(product_type))
    self.inner_product_layer = InnerProductInteraction(feature_map.num_fields, output='inner_product')
    input_dim = int(feature_map.num_fields * (feature_map.num_fields - 1) / 2) + feature_map.num_fields * embedding_dim
    self.dnn = MLP_Block(input_dim=input_dim, output_dim=1, hidden_units=hidden_units, hidden_activations=hidden_activations, output_activation=self.output_activation, dropout_rates=net_dropout, batch_norm=batch_norm)
    self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
    self.reset_parameters()
    self.model_to_device()

class CCPM(BaseModel):

    def __init__(self, feature_map, model_id='CCPM', gpu=-1, learning_rate=0.001, embedding_dim=10, channels=[4, 4, 2], kernel_heights=[6, 5, 3], activation='Tanh', embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(CCPM, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        self.conv_layer = CCPM_ConvLayer(feature_map.num_fields, channels=channels, kernel_heights=kernel_heights, activation=activation)
        conv_out_dim = 3 * embedding_dim * channels[-1]
        self.fc = nn.Linear(conv_out_dim, 1)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        """
        Inputs: [X, y]
        """
        X = self.get_inputs(inputs)
        feature_emb = self.embedding_layer(X)
        conv_in = torch.unsqueeze(feature_emb, 1)
        conv_out = self.conv_layer(conv_in)
        flatten_out = torch.flatten(conv_out, start_dim=1)
        y_pred = self.fc(flatten_out)
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred}
        return return_dict

def __init__(self, feature_map, model_id='CCPM', gpu=-1, learning_rate=0.001, embedding_dim=10, channels=[4, 4, 2], kernel_heights=[6, 5, 3], activation='Tanh', embedding_regularizer=None, net_regularizer=None, **kwargs):
    super(CCPM, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
    self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
    self.conv_layer = CCPM_ConvLayer(feature_map.num_fields, channels=channels, kernel_heights=kernel_heights, activation=activation)
    conv_out_dim = 3 * embedding_dim * channels[-1]
    self.fc = nn.Linear(conv_out_dim, 1)
    self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
    self.reset_parameters()
    self.model_to_device()

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

class APG_DCNv2(BaseModel):

    def __init__(self, feature_map, model_id='APG_DCNv2', gpu=-1, model_structure='parallel', use_low_rank_mixture=False, low_rank=32, num_experts=4, learning_rate=0.001, embedding_dim=10, stacked_dnn_hidden_units=[], parallel_dnn_hidden_units=[], dnn_activations='ReLU', num_cross_layers=3, net_dropout=0, batch_norm=False, embedding_regularizer=None, net_regularizer=None, hypernet_config={}, condition_features=[], condition_mode='self-wise', new_condition_emb=False, rank_k=32, overparam_p=1024, generate_bias=True, **kwargs):
        super(APG_DCNv2, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.embedding_layer = FeatureEmbeddingDict(feature_map, embedding_dim)
        self.condition_mode = condition_mode
        self.condition_features = condition_features
        self.condition_emb_layer = None
        if condition_mode == 'self-wise':
            condition_dim = None
        else:
            assert len(condition_features) > 0
            condition_dim = len(condition_features) * embedding_dim
            if new_condition_emb:
                self.condition_emb_layer = FeatureEmbedding(feature_map, embedding_dim, required_feature_columns=condition_features)
        input_dim = feature_map.sum_emb_out_dim()
        if use_low_rank_mixture:
            self.crossnet = CrossNetMix(input_dim, num_cross_layers, low_rank=low_rank, num_experts=num_experts)
        else:
            self.crossnet = CrossNetV2(input_dim, num_cross_layers)
        self.model_structure = model_structure
        assert self.model_structure in ['crossnet_only', 'stacked', 'parallel', 'stacked_parallel'], 'model_structure={} not supported!'.format(self.model_structure)
        if self.model_structure in ['stacked', 'stacked_parallel']:
            self.stacked_dnn = APG_MLP(input_dim=input_dim, output_dim=None, hidden_units=stacked_dnn_hidden_units, hidden_activations=dnn_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm, hypernet_config=hypernet_config, condition_dim=condition_dim, condition_mode=condition_mode, rank_k=rank_k, overparam_p=overparam_p, generate_bias=generate_bias)
            final_dim = stacked_dnn_hidden_units[-1]
        if self.model_structure in ['parallel', 'stacked_parallel']:
            self.parallel_dnn = APG_MLP(input_dim=input_dim, output_dim=None, hidden_units=parallel_dnn_hidden_units, hidden_activations=dnn_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm, hypernet_config=hypernet_config, condition_dim=condition_dim, condition_mode=condition_mode, rank_k=rank_k, overparam_p=overparam_p, generate_bias=generate_bias)
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
        X = self.get_inputs(inputs)
        feature_emb_dict = self.embedding_layer(X)
        condition_z = self.get_condition_z(X, feature_emb_dict)
        feature_emb = self.embedding_layer.dict2tensor(feature_emb_dict, flatten_emb=True)
        cross_out = self.crossnet(feature_emb)
        if self.model_structure == 'crossnet_only':
            final_out = cross_out
        elif self.model_structure == 'stacked':
            final_out = self.stacked_dnn(cross_out, condition_z)
        elif self.model_structure == 'parallel':
            dnn_out = self.parallel_dnn(feature_emb, condition_z)
            final_out = torch.cat([cross_out, dnn_out], dim=-1)
        elif self.model_structure == 'stacked_parallel':
            final_out = torch.cat([self.stacked_dnn(cross_out, condition_z), self.parallel_dnn(feature_emb, condition_z)], dim=-1)
        y_pred = self.fc(final_out)
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred}
        return return_dict

    def get_condition_z(self, X, feature_emb_dict):
        condition_z = None
        if self.condition_mode != 'self-wise':
            if self.condition_emb_layer is not None:
                condition_z = self.condition_emb_layer(X, flatten_emb=True)
            else:
                condition_z = self.embedding_layer.dict2tensor(feature_emb_dict, feature_list=self.condition_features, flatten_emb=True)
        return condition_z

def __init__(self, feature_map, model_id='APG_DCNv2', gpu=-1, model_structure='parallel', use_low_rank_mixture=False, low_rank=32, num_experts=4, learning_rate=0.001, embedding_dim=10, stacked_dnn_hidden_units=[], parallel_dnn_hidden_units=[], dnn_activations='ReLU', num_cross_layers=3, net_dropout=0, batch_norm=False, embedding_regularizer=None, net_regularizer=None, hypernet_config={}, condition_features=[], condition_mode='self-wise', new_condition_emb=False, rank_k=32, overparam_p=1024, generate_bias=True, **kwargs):
    super(APG_DCNv2, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
    self.embedding_layer = FeatureEmbeddingDict(feature_map, embedding_dim)
    self.condition_mode = condition_mode
    self.condition_features = condition_features
    self.condition_emb_layer = None
    if condition_mode == 'self-wise':
        condition_dim = None
    else:
        assert len(condition_features) > 0
        condition_dim = len(condition_features) * embedding_dim
        if new_condition_emb:
            self.condition_emb_layer = FeatureEmbedding(feature_map, embedding_dim, required_feature_columns=condition_features)
    input_dim = feature_map.sum_emb_out_dim()
    if use_low_rank_mixture:
        self.crossnet = CrossNetMix(input_dim, num_cross_layers, low_rank=low_rank, num_experts=num_experts)
    else:
        self.crossnet = CrossNetV2(input_dim, num_cross_layers)
    self.model_structure = model_structure
    assert self.model_structure in ['crossnet_only', 'stacked', 'parallel', 'stacked_parallel'], 'model_structure={} not supported!'.format(self.model_structure)
    if self.model_structure in ['stacked', 'stacked_parallel']:
        self.stacked_dnn = APG_MLP(input_dim=input_dim, output_dim=None, hidden_units=stacked_dnn_hidden_units, hidden_activations=dnn_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm, hypernet_config=hypernet_config, condition_dim=condition_dim, condition_mode=condition_mode, rank_k=rank_k, overparam_p=overparam_p, generate_bias=generate_bias)
        final_dim = stacked_dnn_hidden_units[-1]
    if self.model_structure in ['parallel', 'stacked_parallel']:
        self.parallel_dnn = APG_MLP(input_dim=input_dim, output_dim=None, hidden_units=parallel_dnn_hidden_units, hidden_activations=dnn_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm, hypernet_config=hypernet_config, condition_dim=condition_dim, condition_mode=condition_mode, rank_k=rank_k, overparam_p=overparam_p, generate_bias=generate_bias)
        final_dim = input_dim + parallel_dnn_hidden_units[-1]
    if self.model_structure == 'stacked_parallel':
        final_dim = stacked_dnn_hidden_units[-1] + parallel_dnn_hidden_units[-1]
    if self.model_structure == 'crossnet_only':
        final_dim = input_dim
    self.fc = nn.Linear(final_dim, 1)
    self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
    self.reset_parameters()
    self.model_to_device()

class APG_DeepFM(BaseModel):

    def __init__(self, feature_map, model_id='APG_DeepFM', gpu=-1, learning_rate=0.001, embedding_dim=10, hidden_units=[64, 64, 64], hidden_activations='ReLU', net_dropout=0, batch_norm=False, embedding_regularizer=None, net_regularizer=None, hypernet_config={}, condition_features=[], condition_mode='self-wise', new_condition_emb=False, rank_k=32, overparam_p=1024, generate_bias=True, **kwargs):
        super(APG_DeepFM, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.embedding_layer = FeatureEmbeddingDict(feature_map, embedding_dim)
        self.fm = FactorizationMachine(feature_map)
        self.condition_mode = condition_mode
        self.condition_features = condition_features
        self.condition_emb_layer = None
        if condition_mode == 'self-wise':
            condition_dim = None
        else:
            assert len(condition_features) > 0
            condition_dim = len(condition_features) * embedding_dim
            if new_condition_emb:
                self.condition_emb_layer = FeatureEmbedding(feature_map, embedding_dim, required_feature_columns=condition_features)
        self.mlp = APG_MLP(input_dim=feature_map.sum_emb_out_dim(), output_dim=1, hidden_units=hidden_units, hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm, hypernet_config=hypernet_config, condition_dim=condition_dim, condition_mode=condition_mode, rank_k=rank_k, overparam_p=overparam_p, generate_bias=generate_bias)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        """
        Inputs: [X,y]
        """
        X = self.get_inputs(inputs)
        feature_emb_dict = self.embedding_layer(X)
        condition_z = self.get_condition_z(X, feature_emb_dict)
        feature_emb = self.embedding_layer.dict2tensor(feature_emb_dict)
        y_fm = self.fm(X, feature_emb)
        y_mlp = self.mlp(feature_emb.flatten(start_dim=1), condition_z)
        y_pred = y_fm + y_mlp
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred}
        return return_dict

    def get_condition_z(self, X, feature_emb_dict):
        condition_z = None
        if self.condition_mode != 'self-wise':
            if self.condition_emb_layer is not None:
                condition_z = self.condition_emb_layer(X, flatten_emb=True)
            else:
                condition_z = self.embedding_layer.dict2tensor(feature_emb_dict, feature_list=self.condition_features, flatten_emb=True)
        return condition_z

def __init__(self, feature_map, model_id='APG_DeepFM', gpu=-1, learning_rate=0.001, embedding_dim=10, hidden_units=[64, 64, 64], hidden_activations='ReLU', net_dropout=0, batch_norm=False, embedding_regularizer=None, net_regularizer=None, hypernet_config={}, condition_features=[], condition_mode='self-wise', new_condition_emb=False, rank_k=32, overparam_p=1024, generate_bias=True, **kwargs):
    super(APG_DeepFM, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
    self.embedding_layer = FeatureEmbeddingDict(feature_map, embedding_dim)
    self.fm = FactorizationMachine(feature_map)
    self.condition_mode = condition_mode
    self.condition_features = condition_features
    self.condition_emb_layer = None
    if condition_mode == 'self-wise':
        condition_dim = None
    else:
        assert len(condition_features) > 0
        condition_dim = len(condition_features) * embedding_dim
        if new_condition_emb:
            self.condition_emb_layer = FeatureEmbedding(feature_map, embedding_dim, required_feature_columns=condition_features)
    self.mlp = APG_MLP(input_dim=feature_map.sum_emb_out_dim(), output_dim=1, hidden_units=hidden_units, hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm, hypernet_config=hypernet_config, condition_dim=condition_dim, condition_mode=condition_mode, rank_k=rank_k, overparam_p=overparam_p, generate_bias=generate_bias)
    self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
    self.reset_parameters()
    self.model_to_device()

class DeepCrossing(BaseModel):

    def __init__(self, feature_map, model_id='DeepCrossing', gpu=-1, learning_rate=0.001, embedding_dim=10, residual_blocks=[64, 64, 64], hidden_activations='ReLU', net_dropout=0, batch_norm=False, use_residual=True, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(DeepCrossing, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        if not isinstance(hidden_activations, list):
            hidden_activations = [hidden_activations] * len(residual_blocks)
        layers = []
        input_dim = feature_map.num_fields * embedding_dim
        for hidden_dim, hidden_activation in zip(residual_blocks, hidden_activations):
            layers.append(ResidualBlock(input_dim, hidden_dim, hidden_activation, net_dropout, use_residual, batch_norm))
        layers.append(nn.Linear(input_dim, 1))
        self.crossing_layer = nn.Sequential(*layers)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        """
        Inputs: [X,y]
        """
        X = self.get_inputs(inputs)
        feature_emb = self.embedding_layer(X)
        y_pred = self.crossing_layer(feature_emb.flatten(start_dim=1))
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred}
        return return_dict

def __init__(self, feature_map, model_id='DeepCrossing', gpu=-1, learning_rate=0.001, embedding_dim=10, residual_blocks=[64, 64, 64], hidden_activations='ReLU', net_dropout=0, batch_norm=False, use_residual=True, embedding_regularizer=None, net_regularizer=None, **kwargs):
    super(DeepCrossing, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
    self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
    if not isinstance(hidden_activations, list):
        hidden_activations = [hidden_activations] * len(residual_blocks)
    layers = []
    input_dim = feature_map.num_fields * embedding_dim
    for hidden_dim, hidden_activation in zip(residual_blocks, hidden_activations):
        layers.append(ResidualBlock(input_dim, hidden_dim, hidden_activation, net_dropout, use_residual, batch_norm))
    layers.append(nn.Linear(input_dim, 1))
    self.crossing_layer = nn.Sequential(*layers)
    self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
    self.reset_parameters()
    self.model_to_device()

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

def __init__(self, input_dim, hidden_dim, hidden_activation='ReLU', dropout_rate=0, use_residual=True, batch_norm=False):
    super(ResidualBlock, self).__init__()
    self.activation_layer = get_activation(hidden_activation)
    self.layer = nn.Sequential(nn.Linear(input_dim, hidden_dim), self.activation_layer, nn.Linear(hidden_dim, input_dim))
    self.use_residual = use_residual
    self.batch_norm = nn.BatchNorm1d(input_dim) if batch_norm else None
    self.dropout = nn.Dropout(dropout_rate) if dropout_rate > 0 else None

class PPNet(BaseModel):

    def __init__(self, feature_map, model_id='PPNet', gpu=-1, learning_rate=0.001, embedding_dim=10, gate_emb_dim=10, gate_priors=[], gate_hidden_dim=64, hidden_units=[64, 64, 64], hidden_activations='ReLU', net_dropout=0, batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(PPNet, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        self.gate_embed_layer = FeatureEmbedding(feature_map, gate_emb_dim, required_feature_columns=gate_priors)
        gate_input_dim = feature_map.sum_emb_out_dim() + len(gate_priors) * gate_emb_dim
        self.ppn = PPNet_MLP(input_dim=feature_map.sum_emb_out_dim(), output_dim=1, gate_input_dim=gate_input_dim, gate_hidden_dim=gate_hidden_dim, hidden_units=hidden_units, hidden_activations=hidden_activations, dropout_rates=net_dropout, batch_norm=batch_norm)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        X = self.get_inputs(inputs)
        feature_emb = self.embedding_layer(X, flatten_emb=True)
        gate_emb = self.gate_embed_layer(X, flatten_emb=True)
        y_pred = self.ppn(feature_emb, gate_emb)
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred}
        return return_dict

def __init__(self, feature_map, model_id='PPNet', gpu=-1, learning_rate=0.001, embedding_dim=10, gate_emb_dim=10, gate_priors=[], gate_hidden_dim=64, hidden_units=[64, 64, 64], hidden_activations='ReLU', net_dropout=0, batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
    super(PPNet, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
    self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
    self.gate_embed_layer = FeatureEmbedding(feature_map, gate_emb_dim, required_feature_columns=gate_priors)
    gate_input_dim = feature_map.sum_emb_out_dim() + len(gate_priors) * gate_emb_dim
    self.ppn = PPNet_MLP(input_dim=feature_map.sum_emb_out_dim(), output_dim=1, gate_input_dim=gate_input_dim, gate_hidden_dim=gate_hidden_dim, hidden_units=hidden_units, hidden_activations=hidden_activations, dropout_rates=net_dropout, batch_norm=batch_norm)
    self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
    self.reset_parameters()
    self.model_to_device()

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

class GateNU(nn.Module):

    def __init__(self, input_dim, hidden_dim=None, output_dim=None, hidden_activation='ReLU', dropout_rate=0.0):
        super(GateNU, self).__init__()
        if hidden_dim is None:
            hidden_dim = output_dim
        layers = [nn.Linear(input_dim, hidden_dim)]
        layers.append(get_activation(hidden_activation))
        if dropout_rate > 0:
            layers.append(nn.Dropout(dropout_rate))
        layers.append(nn.Linear(hidden_dim, output_dim))
        layers.append(nn.Sigmoid())
        self.gate = nn.Sequential(*layers)

    def forward(self, inputs):
        return self.gate(inputs) * 2

def __init__(self, input_dim, hidden_dim=None, output_dim=None, hidden_activation='ReLU', dropout_rate=0.0):
    super(GateNU, self).__init__()
    if hidden_dim is None:
        hidden_dim = output_dim
    layers = [nn.Linear(input_dim, hidden_dim)]
    layers.append(get_activation(hidden_activation))
    if dropout_rate > 0:
        layers.append(nn.Dropout(dropout_rate))
    layers.append(nn.Linear(hidden_dim, output_dim))
    layers.append(nn.Sigmoid())
    self.gate = nn.Sequential(*layers)

class FLEN(BaseModel):

    def __init__(self, feature_map, model_id='FLEN', gpu=-1, learning_rate=0.001, embedding_dim=10, dnn_hidden_units=[64, 64, 64], dnn_activations='ReLU', net_dropout=0, batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(FLEN, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.embedding_layer = FeatureEmbeddingDict(feature_map, embedding_dim)
        self.lr_layer = LogisticRegression(feature_map)
        self.mf_interaction = InnerProductInteraction(num_fields=3, output='elementwise_product')
        self.fm_interaction = InnerProductInteraction(feature_map.num_fields, output='bi_interaction')
        self.dnn = MLP_Block(input_dim=embedding_dim * feature_map.num_fields, output_dim=None, hidden_units=dnn_hidden_units, hidden_activations=dnn_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm)
        self.r_ij = nn.Linear(3, 1, bias=False)
        self.r_mm = nn.Linear(3, 1, bias=False)
        self.w_FwBI = nn.Sequential(nn.Linear(embedding_dim + 1, embedding_dim + 1, bias=False), nn.ReLU())
        self.w_F = nn.Linear(dnn_hidden_units[-1] + embedding_dim + 1, 1, bias=False)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        """
        Inputs: [X,y]
        """
        X = self.get_inputs(inputs)
        feature_emb_dict = self.embedding_layer(X)
        emb_user = self.embedding_layer.dict2tensor(feature_emb_dict, feature_source='user')
        emb_item = self.embedding_layer.dict2tensor(feature_emb_dict, feature_source='item')
        emb_context = self.embedding_layer.dict2tensor(feature_emb_dict, feature_source='context')
        feature_emb = self.embedding_layer.dict2tensor(feature_emb_dict)
        lr_out = self.lr_layer(X)
        field_emb = torch.stack([emb_user.sum(dim=1), emb_item.sum(dim=1), emb_context.sum(dim=1)], dim=1)
        h_MF = self.r_ij(self.mf_interaction(field_emb).transpose(1, 2))
        h_FM = self.r_mm(torch.stack([self.fm_interaction(emb_user), self.fm_interaction(emb_item), self.fm_interaction(emb_context)], dim=1).transpose(1, 2))
        h_FwBI = self.w_FwBI(torch.cat([lr_out, (h_MF + h_FM).squeeze(-1)], dim=-1))
        h_L = self.dnn(feature_emb.flatten(start_dim=1))
        y_pred = self.w_F(torch.cat([h_FwBI, h_L], dim=-1))
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred}
        return return_dict

def __init__(self, feature_map, model_id='FLEN', gpu=-1, learning_rate=0.001, embedding_dim=10, dnn_hidden_units=[64, 64, 64], dnn_activations='ReLU', net_dropout=0, batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
    super(FLEN, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
    self.embedding_layer = FeatureEmbeddingDict(feature_map, embedding_dim)
    self.lr_layer = LogisticRegression(feature_map)
    self.mf_interaction = InnerProductInteraction(num_fields=3, output='elementwise_product')
    self.fm_interaction = InnerProductInteraction(feature_map.num_fields, output='bi_interaction')
    self.dnn = MLP_Block(input_dim=embedding_dim * feature_map.num_fields, output_dim=None, hidden_units=dnn_hidden_units, hidden_activations=dnn_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm)
    self.r_ij = nn.Linear(3, 1, bias=False)
    self.r_mm = nn.Linear(3, 1, bias=False)
    self.w_FwBI = nn.Sequential(nn.Linear(embedding_dim + 1, embedding_dim + 1, bias=False), nn.ReLU())
    self.w_F = nn.Linear(dnn_hidden_units[-1] + embedding_dim + 1, 1, bias=False)
    self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
    self.reset_parameters()
    self.model_to_device()

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

class AOANet(BaseModel):
    """ The AOANet model
        References:
          - Lang Lang, Zhenlong Zhu, Xuanye Liu, Jianxin Zhao, Jixing Xu, Minghui Shan: 
            Architecture and Operation Adaptive Network for Online Recommendations, KDD 2021.
          - [PDF] https://dl.acm.org/doi/pdf/10.1145/3447548.3467133
    """

    def __init__(self, feature_map, model_id='AOANet', gpu=-1, learning_rate=0.001, embedding_dim=10, dnn_hidden_units=[64, 64, 64], dnn_hidden_activations='ReLU', num_interaction_layers=3, num_subspaces=4, net_dropout=0, batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(AOANet, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        self.dnn = MLP_Block(input_dim=feature_map.sum_emb_out_dim(), output_dim=None, hidden_units=dnn_hidden_units, hidden_activations=dnn_hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm)
        self.gin = GeneralizedInteractionNet(num_interaction_layers, num_subspaces, feature_map.num_fields, embedding_dim)
        self.fc = nn.Linear(dnn_hidden_units[-1] + num_subspaces * embedding_dim, 1)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        """
        Inputs: [X,y]
        """
        X = self.get_inputs(inputs)
        feat_emb = self.embedding_layer(X)
        dnn_out = self.dnn(feat_emb.flatten(start_dim=1))
        interact_out = self.gin(feat_emb).flatten(start_dim=1)
        y_pred = self.fc(torch.cat([dnn_out, interact_out], dim=-1))
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred}
        return return_dict

def __init__(self, feature_map, model_id='AOANet', gpu=-1, learning_rate=0.001, embedding_dim=10, dnn_hidden_units=[64, 64, 64], dnn_hidden_activations='ReLU', num_interaction_layers=3, num_subspaces=4, net_dropout=0, batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
    super(AOANet, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
    self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
    self.dnn = MLP_Block(input_dim=feature_map.sum_emb_out_dim(), output_dim=None, hidden_units=dnn_hidden_units, hidden_activations=dnn_hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm)
    self.gin = GeneralizedInteractionNet(num_interaction_layers, num_subspaces, feature_map.num_fields, embedding_dim)
    self.fc = nn.Linear(dnn_hidden_units[-1] + num_subspaces * embedding_dim, 1)
    self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
    self.reset_parameters()
    self.model_to_device()

class GeneralizedInteractionNet(nn.Module):

    def __init__(self, num_layers, num_subspaces, num_fields, embedding_dim):
        super(GeneralizedInteractionNet, self).__init__()
        self.layers = nn.ModuleList([GeneralizedInteraction(num_fields if i == 0 else num_subspaces, num_subspaces, num_fields, embedding_dim) for i in range(num_layers)])

    def forward(self, B_0):
        B_i = B_0
        for layer in self.layers:
            B_i = layer(B_0, B_i)
        return B_i

def __init__(self, num_layers, num_subspaces, num_fields, embedding_dim):
    super(GeneralizedInteractionNet, self).__init__()
    self.layers = nn.ModuleList([GeneralizedInteraction(num_fields if i == 0 else num_subspaces, num_subspaces, num_fields, embedding_dim) for i in range(num_layers)])

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

def __init__(self, input_subspaces, output_subspaces, num_fields, embedding_dim):
    super(GeneralizedInteraction, self).__init__()
    self.input_subspaces = input_subspaces
    self.num_fields = num_fields
    self.embedding_dim = embedding_dim
    self.W = nn.Parameter(torch.eye(embedding_dim, embedding_dim).unsqueeze(0).repeat(output_subspaces, 1, 1))
    self.alpha = nn.Parameter(torch.ones(input_subspaces * num_fields, output_subspaces))
    self.h = nn.Parameter(torch.ones(output_subspaces, embedding_dim, 1))

class DESTINE(BaseModel):

    def __init__(self, feature_map, model_id='DESTINE', gpu=-1, learning_rate=0.001, embedding_dim=10, attention_dim=16, num_heads=2, attention_layers=2, dnn_hidden_units=[], dnn_activations='ReLU', net_dropout=0.1, att_dropout=0.1, relu_before_att=False, batch_norm=False, use_scale=False, use_wide=True, residual_mode='each_layer', embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(DESTINE, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        self.lr = LogisticRegression(feature_map) if use_wide else None
        self.dnn = MLP_Block(input_dim=feature_map.num_fields * embedding_dim, output_dim=1, hidden_units=dnn_hidden_units, hidden_activations=dnn_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm) if dnn_hidden_units else None
        self.self_attns = nn.ModuleList([DisentangledSelfAttention(embedding_dim if i == 0 else attention_dim, attention_dim, num_heads, att_dropout, residual_mode == 'each_layer', use_scale, relu_before_att) for i in range(attention_layers)])
        self.attn_fc = nn.Linear(feature_map.num_fields * attention_dim, 1)
        if residual_mode == 'last_layer':
            self.W_res = nn.Linear(embedding_dim, attention_dim)
        else:
            self.W_res = None
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        X = self.get_inputs(inputs)
        feature_emb = self.embedding_layer(X)
        cross_X = feature_emb
        for self_attn in self.self_attns:
            cross_X = self_attn(cross_X, cross_X, cross_X)
        if self.W_res is not None:
            cross_X += self.W_res(feature_emb)
        y_pred = self.attn_fc(cross_X.flatten(start_dim=1))
        if self.lr is not None:
            y_pred += self.lr(X)
        if self.dnn is not None:
            y_pred += self.dnn(feature_emb.flatten(start_dim=1))
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred}
        return return_dict

def __init__(self, feature_map, model_id='DESTINE', gpu=-1, learning_rate=0.001, embedding_dim=10, attention_dim=16, num_heads=2, attention_layers=2, dnn_hidden_units=[], dnn_activations='ReLU', net_dropout=0.1, att_dropout=0.1, relu_before_att=False, batch_norm=False, use_scale=False, use_wide=True, residual_mode='each_layer', embedding_regularizer=None, net_regularizer=None, **kwargs):
    super(DESTINE, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
    self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
    self.lr = LogisticRegression(feature_map) if use_wide else None
    self.dnn = MLP_Block(input_dim=feature_map.num_fields * embedding_dim, output_dim=1, hidden_units=dnn_hidden_units, hidden_activations=dnn_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm) if dnn_hidden_units else None
    self.self_attns = nn.ModuleList([DisentangledSelfAttention(embedding_dim if i == 0 else attention_dim, attention_dim, num_heads, att_dropout, residual_mode == 'each_layer', use_scale, relu_before_att) for i in range(attention_layers)])
    self.attn_fc = nn.Linear(feature_map.num_fields * attention_dim, 1)
    if residual_mode == 'last_layer':
        self.W_res = nn.Linear(embedding_dim, attention_dim)
    else:
        self.W_res = None
    self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
    self.reset_parameters()
    self.model_to_device()

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

class HFM(BaseModel):

    def __init__(self, feature_map, model_id='HFM', gpu=-1, learning_rate=0.001, embedding_dim=10, interaction_type='circular_convolution', use_dnn=True, hidden_units=[64, 64], hidden_activations=['relu', 'relu'], batch_norm=False, net_dropout=0, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(HFM, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        self.lr_layer = LogisticRegression(feature_map)
        self.hfm_layer = HolographicInteraction(feature_map.num_fields, interaction_type=interaction_type)
        self.use_dnn = use_dnn
        if self.use_dnn:
            input_dim = int(feature_map.num_fields * (feature_map.num_fields - 1) / 2) * embedding_dim
            self.dnn = MLP_Block(input_dim=input_dim, output_dim=1, hidden_units=hidden_units, hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm)
        else:
            self.proj_h = nn.Linear(embedding_dim, 1, bias=False)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        """
        Inputs: [X, y]
        """
        X = self.get_inputs(inputs)
        feature_emb = self.embedding_layer(X)
        interact_out = self.hfm_layer(feature_emb)
        if self.use_dnn:
            hfm_out = self.dnn(torch.flatten(interact_out, start_dim=1))
        else:
            hfm_out = self.proj_h(interact_out.sum(dim=1))
        y_pred = hfm_out + self.lr_layer(X)
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred}
        return return_dict

def __init__(self, feature_map, model_id='HFM', gpu=-1, learning_rate=0.001, embedding_dim=10, interaction_type='circular_convolution', use_dnn=True, hidden_units=[64, 64], hidden_activations=['relu', 'relu'], batch_norm=False, net_dropout=0, embedding_regularizer=None, net_regularizer=None, **kwargs):
    super(HFM, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
    self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
    self.lr_layer = LogisticRegression(feature_map)
    self.hfm_layer = HolographicInteraction(feature_map.num_fields, interaction_type=interaction_type)
    self.use_dnn = use_dnn
    if self.use_dnn:
        input_dim = int(feature_map.num_fields * (feature_map.num_fields - 1) / 2) * embedding_dim
        self.dnn = MLP_Block(input_dim=input_dim, output_dim=1, hidden_units=hidden_units, hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm)
    else:
        self.proj_h = nn.Linear(embedding_dim, 1, bias=False)
    self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
    self.reset_parameters()
    self.model_to_device()

class DeepIM(BaseModel):

    def __init__(self, feature_map, model_id='DeepIM', gpu=-1, learning_rate=0.001, embedding_dim=10, im_order=2, im_batch_norm=False, hidden_units=[64, 64, 64], hidden_activations='ReLU', net_dropout=0, net_batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(DeepIM, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        self.im_layer = InteractionMachine(embedding_dim, im_order, im_batch_norm)
        self.dnn = MLP_Block(input_dim=embedding_dim * feature_map.num_fields, output_dim=1, hidden_units=hidden_units, hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=net_batch_norm) if hidden_units is not None else None
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        """
        Inputs: [X,y]
        """
        X = self.get_inputs(inputs)
        feature_emb = self.embedding_layer(X)
        y_pred = self.im_layer(feature_emb)
        if self.dnn is not None:
            y_pred += self.dnn(feature_emb.flatten(start_dim=1))
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred}
        return return_dict

def __init__(self, feature_map, model_id='DeepIM', gpu=-1, learning_rate=0.001, embedding_dim=10, im_order=2, im_batch_norm=False, hidden_units=[64, 64, 64], hidden_activations='ReLU', net_dropout=0, net_batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
    super(DeepIM, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
    self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
    self.im_layer = InteractionMachine(embedding_dim, im_order, im_batch_norm)
    self.dnn = MLP_Block(input_dim=embedding_dim * feature_map.num_fields, output_dim=1, hidden_units=hidden_units, hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=net_batch_norm) if hidden_units is not None else None
    self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
    self.reset_parameters()
    self.model_to_device()

class AFM(BaseModel):

    def __init__(self, feature_map, model_id='AFM', gpu=-1, learning_rate=0.001, embedding_dim=10, attention_dropout=[0, 0], attention_dim=10, use_attention=True, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(AFM, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.use_attention = use_attention
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        self.product_layer = InnerProductInteraction(feature_map.num_fields, output='elementwise_product')
        self.lr_layer = LogisticRegression(feature_map, use_bias=True)
        self.attention = nn.Sequential(nn.Linear(embedding_dim, attention_dim), nn.ReLU(), nn.Linear(attention_dim, 1, bias=False), nn.Softmax(dim=1))
        self.weight_p = nn.Linear(embedding_dim, 1, bias=False)
        self.dropout1 = nn.Dropout(attention_dropout[0])
        self.dropout2 = nn.Dropout(attention_dropout[1])
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        X = self.get_inputs(inputs)
        feature_emb = self.embedding_layer(X)
        elementwise_product = self.product_layer(feature_emb)
        if self.use_attention:
            attention_weight = self.attention(elementwise_product)
            attention_weight = self.dropout1(attention_weight)
            attention_sum = torch.sum(attention_weight * elementwise_product, dim=1)
            attention_sum = self.dropout2(attention_sum)
            afm_out = self.weight_p(attention_sum)
        else:
            afm_out = torch.flatten(elementwise_product, start_dim=1).sum(dim=-1).unsqueeze(-1)
        y_pred = self.lr_layer(X) + afm_out
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred}
        return return_dict

def __init__(self, feature_map, model_id='AFM', gpu=-1, learning_rate=0.001, embedding_dim=10, attention_dropout=[0, 0], attention_dim=10, use_attention=True, embedding_regularizer=None, net_regularizer=None, **kwargs):
    super(AFM, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
    self.use_attention = use_attention
    self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
    self.product_layer = InnerProductInteraction(feature_map.num_fields, output='elementwise_product')
    self.lr_layer = LogisticRegression(feature_map, use_bias=True)
    self.attention = nn.Sequential(nn.Linear(embedding_dim, attention_dim), nn.ReLU(), nn.Linear(attention_dim, 1, bias=False), nn.Softmax(dim=1))
    self.weight_p = nn.Linear(embedding_dim, 1, bias=False)
    self.dropout1 = nn.Dropout(attention_dropout[0])
    self.dropout2 = nn.Dropout(attention_dropout[1])
    self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
    self.reset_parameters()
    self.model_to_device()

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

def __init__(self, seq_len=1, model_dim=64, num_heads=8, stacked_transformer_layers=1, attn_dropout=0.0, net_dropout=0.0, use_position_emb=True, position_dim=4, layer_norm=True, use_residual=True):
    super(BehaviorTransformer, self).__init__()
    self.position_dim = position_dim
    self.use_position_emb = use_position_emb
    self.transformer_blocks = nn.ModuleList((TransformerBlock(model_dim=model_dim, ffn_dim=model_dim, num_heads=num_heads, attn_dropout=attn_dropout, net_dropout=net_dropout, layer_norm=layer_norm, use_residual=use_residual) for _ in range(stacked_transformer_layers)))
    if self.use_position_emb:
        self.position_emb = nn.Parameter(torch.Tensor(seq_len, position_dim))
        self.reset_parameters()

class TransformerBlock(nn.Module):

    def __init__(self, model_dim=64, ffn_dim=64, num_heads=8, attn_dropout=0.0, net_dropout=0.0, layer_norm=True, use_residual=True):
        super(TransformerBlock, self).__init__()
        self.attention = MultiheadAttention(model_dim, num_heads=num_heads, dropout=attn_dropout, batch_first=True)
        self.ffn = nn.Sequential(nn.Linear(model_dim, ffn_dim), nn.LeakyReLU(), nn.Linear(ffn_dim, model_dim))
        self.use_residual = use_residual
        self.dropout1 = nn.Dropout(net_dropout)
        self.dropout2 = nn.Dropout(net_dropout)
        self.layer_norm1 = nn.LayerNorm(model_dim) if layer_norm else None
        self.layer_norm2 = nn.LayerNorm(model_dim) if layer_norm else None

    def forward(self, x, attn_mask=None):
        attn, _ = self.attention(x, x, x, attn_mask=attn_mask)
        s = self.dropout1(attn)
        if self.use_residual:
            s += x
        if self.layer_norm1 is not None:
            s = self.layer_norm1(s)
        out = self.dropout2(self.ffn(s))
        if self.use_residual:
            out += s
        if self.layer_norm2 is not None:
            out = self.layer_norm2(out)
        return out

def __init__(self, model_dim=64, ffn_dim=64, num_heads=8, attn_dropout=0.0, net_dropout=0.0, layer_norm=True, use_residual=True):
    super(TransformerBlock, self).__init__()
    self.attention = MultiheadAttention(model_dim, num_heads=num_heads, dropout=attn_dropout, batch_first=True)
    self.ffn = nn.Sequential(nn.Linear(model_dim, ffn_dim), nn.LeakyReLU(), nn.Linear(ffn_dim, model_dim))
    self.use_residual = use_residual
    self.dropout1 = nn.Dropout(net_dropout)
    self.dropout2 = nn.Dropout(net_dropout)
    self.layer_norm1 = nn.LayerNorm(model_dim) if layer_norm else None
    self.layer_norm2 = nn.LayerNorm(model_dim) if layer_norm else None

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

def __init__(self, num_shared_experts, num_specific_experts, num_tasks, input_dim, expert_hidden_units, gate_hidden_units, hidden_activations, net_dropout, batch_norm):
    super(CGC_Layer, self).__init__()
    self.num_shared_experts = num_shared_experts
    self.num_specific_experts = num_specific_experts
    self.num_tasks = num_tasks
    self.shared_experts = nn.ModuleList([MLP_Block(input_dim=input_dim, hidden_units=expert_hidden_units, hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm) for _ in range(self.num_shared_experts)])
    self.specific_experts = nn.ModuleList([nn.ModuleList([MLP_Block(input_dim=input_dim, hidden_units=expert_hidden_units, hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm) for _ in range(self.num_specific_experts)]) for _ in range(num_tasks)])
    self.gate = nn.ModuleList([MLP_Block(input_dim=input_dim, output_dim=num_specific_experts + num_shared_experts if i < num_tasks else num_shared_experts, hidden_units=gate_hidden_units, hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm) for i in range(self.num_tasks + 1)])
    self.gate_activation = get_activation('softmax')

class PLE(MultiTaskModel):

    def __init__(self, feature_map, task=['binary_classification'], num_tasks=1, model_id='PLE', gpu=-1, learning_rate=0.001, embedding_dim=10, num_layers=1, num_shared_experts=1, num_specific_experts=1, expert_hidden_units=[512, 256, 128], gate_hidden_units=[128, 64], tower_hidden_units=[128, 64], hidden_activations='ReLU', net_dropout=0, batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(PLE, self).__init__(feature_map, task=task, num_tasks=num_tasks, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        self.num_layers = num_layers
        self.cgc_layers = nn.ModuleList([CGC_Layer(num_shared_experts, num_specific_experts, num_tasks, input_dim=embedding_dim * feature_map.num_fields if i == 0 else expert_hidden_units[-1], expert_hidden_units=expert_hidden_units, gate_hidden_units=gate_hidden_units, hidden_activations=hidden_activations, net_dropout=net_dropout, batch_norm=batch_norm) for i in range(self.num_layers)])
        self.tower = nn.ModuleList([MLP_Block(input_dim=expert_hidden_units[-1], output_dim=1, hidden_units=tower_hidden_units, hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm) for _ in range(num_tasks)])
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        X = self.get_inputs(inputs)
        feature_emb = self.embedding_layer(X)
        cgc_inputs = [feature_emb.flatten(start_dim=1) for _ in range(self.num_tasks + 1)]
        for i in range(self.num_layers):
            cgc_outputs = self.cgc_layers[i](cgc_inputs)
            cgc_inputs = cgc_outputs
        tower_output = [self.tower[i](cgc_outputs[i]) for i in range(self.num_tasks)]
        y_pred = [self.output_activation[i](tower_output[i]) for i in range(self.num_tasks)]
        return_dict = {}
        labels = self.feature_map.labels
        for i in range(self.num_tasks):
            return_dict['{}_pred'.format(labels[i])] = y_pred[i]
        return return_dict

def __init__(self, feature_map, task=['binary_classification'], num_tasks=1, model_id='PLE', gpu=-1, learning_rate=0.001, embedding_dim=10, num_layers=1, num_shared_experts=1, num_specific_experts=1, expert_hidden_units=[512, 256, 128], gate_hidden_units=[128, 64], tower_hidden_units=[128, 64], hidden_activations='ReLU', net_dropout=0, batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
    super(PLE, self).__init__(feature_map, task=task, num_tasks=num_tasks, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
    self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
    self.num_layers = num_layers
    self.cgc_layers = nn.ModuleList([CGC_Layer(num_shared_experts, num_specific_experts, num_tasks, input_dim=embedding_dim * feature_map.num_fields if i == 0 else expert_hidden_units[-1], expert_hidden_units=expert_hidden_units, gate_hidden_units=gate_hidden_units, hidden_activations=hidden_activations, net_dropout=net_dropout, batch_norm=batch_norm) for i in range(self.num_layers)])
    self.tower = nn.ModuleList([MLP_Block(input_dim=expert_hidden_units[-1], output_dim=1, hidden_units=tower_hidden_units, hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm) for _ in range(num_tasks)])
    self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
    self.reset_parameters()
    self.model_to_device()

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

def __init__(self, num_experts, num_tasks, input_dim, expert_hidden_units, gate_hidden_units, hidden_activations, net_dropout, batch_norm):
    super(MMoE_Layer, self).__init__()
    self.num_experts = num_experts
    self.num_tasks = num_tasks
    self.experts = nn.ModuleList([MLP_Block(input_dim=input_dim, hidden_units=expert_hidden_units, hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm) for _ in range(self.num_experts)])
    self.gate = nn.ModuleList([MLP_Block(input_dim=input_dim, hidden_units=gate_hidden_units, output_dim=num_experts, hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm) for _ in range(self.num_tasks)])
    self.gate_activation = get_activation('softmax')

class MMoE(MultiTaskModel):

    def __init__(self, feature_map, task=['binary_classification'], num_tasks=1, model_id='MMoE', gpu=-1, learning_rate=0.001, embedding_dim=10, num_experts=4, expert_hidden_units=[512, 256, 128], gate_hidden_units=[128, 64], tower_hidden_units=[128, 64], hidden_activations='ReLU', net_dropout=0, batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(MMoE, self).__init__(feature_map, task=task, num_tasks=num_tasks, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        self.mmoe_layer = MMoE_Layer(num_experts=num_experts, num_tasks=self.num_tasks, input_dim=embedding_dim * feature_map.num_fields, expert_hidden_units=expert_hidden_units, gate_hidden_units=gate_hidden_units, hidden_activations=hidden_activations, net_dropout=net_dropout, batch_norm=batch_norm)
        self.tower = nn.ModuleList([MLP_Block(input_dim=expert_hidden_units[-1], output_dim=1, hidden_units=tower_hidden_units, hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm) for _ in range(num_tasks)])
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        X = self.get_inputs(inputs)
        feature_emb = self.embedding_layer(X)
        expert_output = self.mmoe_layer(feature_emb.flatten(start_dim=1))
        tower_output = [self.tower[i](expert_output[i]) for i in range(self.num_tasks)]
        y_pred = [self.output_activation[i](tower_output[i]) for i in range(self.num_tasks)]
        return_dict = {}
        labels = self.feature_map.labels
        for i in range(self.num_tasks):
            return_dict['{}_pred'.format(labels[i])] = y_pred[i]
        return return_dict

def __init__(self, feature_map, task=['binary_classification'], num_tasks=1, model_id='MMoE', gpu=-1, learning_rate=0.001, embedding_dim=10, num_experts=4, expert_hidden_units=[512, 256, 128], gate_hidden_units=[128, 64], tower_hidden_units=[128, 64], hidden_activations='ReLU', net_dropout=0, batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
    super(MMoE, self).__init__(feature_map, task=task, num_tasks=num_tasks, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
    self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
    self.mmoe_layer = MMoE_Layer(num_experts=num_experts, num_tasks=self.num_tasks, input_dim=embedding_dim * feature_map.num_fields, expert_hidden_units=expert_hidden_units, gate_hidden_units=gate_hidden_units, hidden_activations=hidden_activations, net_dropout=net_dropout, batch_norm=batch_norm)
    self.tower = nn.ModuleList([MLP_Block(input_dim=expert_hidden_units[-1], output_dim=1, hidden_units=tower_hidden_units, hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm) for _ in range(num_tasks)])
    self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
    self.reset_parameters()
    self.model_to_device()

class ShareBottom(MultiTaskModel):

    def __init__(self, feature_map, model_id='SharedBottom', gpu=-1, task=['binary_classification'], num_tasks=1, loss_weight='EQ', learning_rate=0.001, embedding_dim=10, bottom_hidden_units=[64, 64, 64], tower_hidden_units=[64], hidden_activations='ReLU', net_dropout=0, batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(ShareBottom, self).__init__(feature_map, task=task, loss_weight=loss_weight, num_tasks=num_tasks, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        self.bottom = MLP_Block(input_dim=embedding_dim * feature_map.num_fields, hidden_units=bottom_hidden_units, hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm)
        self.tower = nn.ModuleList([MLP_Block(input_dim=bottom_hidden_units[-1], output_dim=1, hidden_units=tower_hidden_units, hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm) for _ in range(num_tasks)])
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        X = self.get_inputs(inputs)
        feature_emb = self.embedding_layer(X)
        bottom_output = self.bottom(feature_emb.flatten(start_dim=1))
        tower_output = [self.tower[i](bottom_output) for i in range(self.num_tasks)]
        y_pred = [self.output_activation[i](tower_output[i]) for i in range(self.num_tasks)]
        return_dict = {}
        labels = self.feature_map.labels
        for i in range(self.num_tasks):
            return_dict['{}_pred'.format(labels[i])] = y_pred[i]
        return return_dict

def __init__(self, feature_map, model_id='SharedBottom', gpu=-1, task=['binary_classification'], num_tasks=1, loss_weight='EQ', learning_rate=0.001, embedding_dim=10, bottom_hidden_units=[64, 64, 64], tower_hidden_units=[64], hidden_activations='ReLU', net_dropout=0, batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
    super(ShareBottom, self).__init__(feature_map, task=task, loss_weight=loss_weight, num_tasks=num_tasks, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
    self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
    self.bottom = MLP_Block(input_dim=embedding_dim * feature_map.num_fields, hidden_units=bottom_hidden_units, hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm)
    self.tower = nn.ModuleList([MLP_Block(input_dim=bottom_hidden_units[-1], output_dim=1, hidden_units=tower_hidden_units, hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm) for _ in range(num_tasks)])
    self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
    self.reset_parameters()
    self.model_to_device()

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

class ONN(BaseModel):

    def __init__(self, feature_map, model_id='ONN', gpu=-1, learning_rate=0.001, embedding_dim=2, embedding_regularizer=None, net_regularizer=None, hidden_units=[64, 64, 64], hidden_activations='ReLU', embedding_dropout=0, net_dropout=0, batch_norm=False, **kwargs):
        super(ONN, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.num_fields = feature_map.num_fields
        input_dim = embedding_dim * self.num_fields + int(self.num_fields * (self.num_fields - 1) / 2)
        self.dnn = MLP_Block(input_dim=input_dim, output_dim=1, hidden_units=hidden_units, hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm)
        self.embedding_layers = nn.ModuleList([FeatureEmbedding(feature_map, embedding_dim) for _ in range(self.num_fields)])
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        """
        Inputs: [X, y]
        """
        X = self.get_inputs(inputs)
        field_aware_emb_list = [each_layer(X) for each_layer in self.embedding_layers]
        diag_embedding = field_aware_emb_list[0].flatten(start_dim=1)
        ffm_out = self.field_aware_interaction(field_aware_emb_list[1:])
        dnn_input = torch.cat([diag_embedding, ffm_out], dim=1)
        y_pred = self.dnn(dnn_input)
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred}
        return return_dict

    def field_aware_interaction(self, field_aware_emb_list):
        interaction = []
        for i in range(self.num_fields - 1):
            for j in range(i + 1, self.num_fields):
                v_ij = field_aware_emb_list[j - 1][:, i, :]
                v_ji = field_aware_emb_list[i][:, j, :]
                dot = torch.sum(v_ij * v_ji, dim=1, keepdim=True)
                interaction.append(dot)
        return torch.cat(interaction, dim=1)

def __init__(self, feature_map, model_id='ONN', gpu=-1, learning_rate=0.001, embedding_dim=2, embedding_regularizer=None, net_regularizer=None, hidden_units=[64, 64, 64], hidden_activations='ReLU', embedding_dropout=0, net_dropout=0, batch_norm=False, **kwargs):
    super(ONN, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
    self.num_fields = feature_map.num_fields
    input_dim = embedding_dim * self.num_fields + int(self.num_fields * (self.num_fields - 1) / 2)
    self.dnn = MLP_Block(input_dim=input_dim, output_dim=1, hidden_units=hidden_units, hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm)
    self.embedding_layers = nn.ModuleList([FeatureEmbedding(feature_map, embedding_dim) for _ in range(self.num_fields)])
    self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
    self.reset_parameters()
    self.model_to_device()

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

class WideDeep(BaseModel):

    def __init__(self, feature_map, model_id='WideDeep', gpu=-1, learning_rate=0.001, embedding_dim=10, hidden_units=[64, 64, 64], hidden_activations='ReLU', net_dropout=0, batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(WideDeep, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        self.lr_layer = LogisticRegression(feature_map, use_bias=False)
        self.dnn = MLP_Block(input_dim=embedding_dim * feature_map.num_fields, output_dim=1, hidden_units=hidden_units, hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        """
        Inputs: [X,y]
        """
        X = self.get_inputs(inputs)
        feature_emb = self.embedding_layer(X)
        y_pred = self.lr_layer(X)
        y_pred += self.dnn(feature_emb.flatten(start_dim=1))
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred}
        return return_dict

def __init__(self, feature_map, model_id='WideDeep', gpu=-1, learning_rate=0.001, embedding_dim=10, hidden_units=[64, 64, 64], hidden_activations='ReLU', net_dropout=0, batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
    super(WideDeep, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
    self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
    self.lr_layer = LogisticRegression(feature_map, use_bias=False)
    self.dnn = MLP_Block(input_dim=embedding_dim * feature_map.num_fields, output_dim=1, hidden_units=hidden_units, hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm)
    self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
    self.reset_parameters()
    self.model_to_device()

class WideDeep(BaseModel):

    def __init__(self, feature_map, model_id='WideDeep', wide_learning_rate=0.001, deep_learning_rate=0.001, embedding_dim=10, hidden_units=[64, 64, 64], hidden_activations='ReLU', net_dropout=0, batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(WideDeep, self).__init__(feature_map, model_id=model_id, **kwargs)
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim, embedding_regularizer=embedding_regularizer)
        self.lr_layer = LogisticRegression(feature_map, use_bias=True, regularizer=embedding_regularizer)
        self.emb_out_dim = feature_map.sum_emb_out_dim()
        self.mlp = MLP_Block(input_dim=self.emb_out_dim, output_dim=1, hidden_units=hidden_units, hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm, regularizer=net_regularizer)
        self.compile(kwargs['loss'], wide_learning_rate, deep_learning_rate, kwargs['deep_optimizer'])

    def compile(self, loss='bce', wide_lr=0.0001, deep_lr=0.001, deep_optimizer='adam'):
        super(BaseModel, self).compile(optimizer=[optimizers.Ftrl(learning_rate=wide_lr, l1_regularization_strength=0.1), get_optimizer(deep_optimizer, deep_lr)], loss=get_loss(loss))

    def lr_decay(self, factor=0.1, min_lr=1e-06):
        self.optimizer[1].learning_rate = max(self.optimizer[1].learning_rate * factor, min_lr)
        return self.optimizer[1].lr.numpy()

    @tf.function
    def train_step(self, batch_data):
        with tf.GradientTape(persistent=True) as tape:
            loss = self.get_total_loss(batch_data)
            wide_prefix = 'logistic'
            wide_variables = [var for var in self.trainable_variables if wide_prefix in var.name]
            wide_grads = tape.gradient(loss, wide_variables)
            wide_grads, _ = tf.clip_by_global_norm(wide_grads, self._max_gradient_norm)
            self.optimizer[0].apply_gradients(zip(wide_grads, wide_variables))
            deep_variables = [var for var in self.trainable_variables if wide_prefix not in var.name]
            deep_grads = tape.gradient(loss, deep_variables)
            deep_grads, _ = tf.clip_by_global_norm(deep_grads, self._max_gradient_norm)
            self.optimizer[1].apply_gradients(zip(deep_grads, deep_variables))
        return loss

    def call(self, inputs, training=False):
        X = self.get_inputs(inputs)
        y_pred = self.lr_layer(X)
        feature_emb = self.embedding_layer(X)
        y_pred += self.mlp(tf.reshape(feature_emb, [-1, self.emb_out_dim]))
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred}
        return return_dict

def __init__(self, feature_map, model_id='WideDeep', wide_learning_rate=0.001, deep_learning_rate=0.001, embedding_dim=10, hidden_units=[64, 64, 64], hidden_activations='ReLU', net_dropout=0, batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
    super(WideDeep, self).__init__(feature_map, model_id=model_id, **kwargs)
    self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim, embedding_regularizer=embedding_regularizer)
    self.lr_layer = LogisticRegression(feature_map, use_bias=True, regularizer=embedding_regularizer)
    self.emb_out_dim = feature_map.sum_emb_out_dim()
    self.mlp = MLP_Block(input_dim=self.emb_out_dim, output_dim=1, hidden_units=hidden_units, hidden_activations=hidden_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm, regularizer=net_regularizer)
    self.compile(kwargs['loss'], wide_learning_rate, deep_learning_rate, kwargs['deep_optimizer'])

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

def __init__(self, model_dim, attention_type='bilinear_attention', attention_hidden_units=[80, 40], attention_activation='Dice', use_attention_softmax=True, attention_dropout=0.0):
    super(AttentionLayer, self).__init__()
    assert attention_type in ['bilinear_attention', 'dot_attention', 'din_attention'], 'attention_type={} is not supported.'.format(attention_type)
    self.attention_type = attention_type
    self.use_attention_softmax = use_attention_softmax
    if attention_type == 'bilinear_attention':
        self.W_kernel = nn.Parameter(torch.eye(model_dim))
    elif attention_type == 'din_attention':
        self.attn_mlp = MLP_Block(input_dim=model_dim * 4, output_dim=1, hidden_units=attention_hidden_units, hidden_activations=attention_activation, output_activation=None, dropout_rates=attention_dropout, batch_norm=False)

class AGRUCell(nn.Module):
    """AGRUCell with attentional update gate
        Reference: GRUCell from https://github.com/emadRad/lstm-gru-pytorch/blob/master/lstm_gru.ipynb

    """

    def __init__(self, input_size, hidden_size, bias=True):
        super(AGRUCell, self).__init__()
        self.x2h = nn.Linear(input_size, 3 * hidden_size, bias=bias)
        self.h2h = nn.Linear(hidden_size, 3 * hidden_size, bias=bias)

    def forward(self, x, hx, attn):
        gate_x = self.x2h(x)
        gate_h = self.h2h(hx)
        i_u, i_r, i_n = gate_x.chunk(3, 1)
        h_u, h_r, h_n = gate_h.chunk(3, 1)
        reset_gate = F.sigmoid(i_r + h_r)
        new_gate = F.tanh(i_n + reset_gate * h_n)
        hy = hx + attn.view(-1, 1) * (new_gate - hx)
        return hy

def __init__(self, input_size, hidden_size, bias=True):
    super(AGRUCell, self).__init__()
    self.x2h = nn.Linear(input_size, 3 * hidden_size, bias=bias)
    self.h2h = nn.Linear(hidden_size, 3 * hidden_size, bias=bias)

class AUGRUCell(nn.Module):
    """AUGRUCell with attentional update gate
        Reference: GRUCell from https://github.com/emadRad/lstm-gru-pytorch/blob/master/lstm_gru.ipynb

    """

    def __init__(self, input_size, hidden_size, bias=True):
        super(AUGRUCell, self).__init__()
        self.x2h = nn.Linear(input_size, 3 * hidden_size, bias=bias)
        self.h2h = nn.Linear(hidden_size, 3 * hidden_size, bias=bias)

    def forward(self, x, hx, attn):
        gate_x = self.x2h(x)
        gate_h = self.h2h(hx)
        i_u, i_r, i_n = gate_x.chunk(3, 1)
        h_u, h_r, h_n = gate_h.chunk(3, 1)
        update_gate = torch.sigmoid(i_u + h_u)
        update_gate = update_gate * attn.unsqueeze(-1)
        reset_gate = torch.sigmoid(i_r + h_r)
        new_gate = torch.tanh(i_n + reset_gate * h_n)
        hy = hx + update_gate * (new_gate - hx)
        return hy

def __init__(self, input_size, hidden_size, bias=True):
    super(AUGRUCell, self).__init__()
    self.x2h = nn.Linear(input_size, 3 * hidden_size, bias=bias)
    self.h2h = nn.Linear(hidden_size, 3 * hidden_size, bias=bias)

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

def __init__(self, input_size, hidden_size, bias=True, gru_type='AUGRU'):
    super(DynamicGRU, self).__init__()
    self.hidden_size = hidden_size
    self.gru_type = gru_type
    if gru_type == 'AUGRU':
        self.gru_cell = AUGRUCell(input_size, hidden_size, bias=bias)
    elif gru_type == 'AGRU':
        self.gru_cell = AGRUCell(input_size, hidden_size, bias=bias)

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

class FGCNN_Layer(nn.Module):
    """
    Input X: tensor of shape (batch_size, 1, num_fields, embedding_dim)
    """

    def __init__(self, num_fields, embedding_dim, channels=[3], kernel_heights=[3], pooling_sizes=[2], recombined_channels=[2], activation='Tanh', batch_norm=True):
        super(FGCNN_Layer, self).__init__()
        self.embedding_dim = embedding_dim
        conv_list = []
        recombine_list = []
        self.channels = [1] + channels
        input_height = num_fields
        for i in range(1, len(self.channels)):
            in_channel = self.channels[i - 1]
            out_channel = self.channels[i]
            kernel_height = kernel_heights[i - 1]
            pooling_size = pooling_sizes[i - 1]
            recombined_channel = recombined_channels[i - 1]
            conv_layer = [nn.Conv2d(in_channel, out_channel, kernel_size=(kernel_height, 1), padding=(int((kernel_height - 1) / 2), 0))] + ([nn.BatchNorm2d(out_channel)] if batch_norm else []) + [get_activation(activation), nn.MaxPool2d((pooling_size, 1), padding=(input_height % pooling_size, 0))]
            conv_list.append(nn.Sequential(*conv_layer))
            input_height = int(np.ceil(input_height / pooling_size))
            input_dim = input_height * embedding_dim * out_channel
            output_dim = input_height * embedding_dim * recombined_channel
            recombine_layer = nn.Sequential(nn.Linear(input_dim, output_dim), get_activation(activation))
            recombine_list.append(recombine_layer)
        self.conv_layers = nn.ModuleList(conv_list)
        self.recombine_layers = nn.ModuleList(recombine_list)

    def forward(self, X):
        conv_out = X
        new_feature_list = []
        for i in range(len(self.channels) - 1):
            conv_out = self.conv_layers[i](conv_out)
            flatten_out = torch.flatten(conv_out, start_dim=1)
            recombine_out = self.recombine_layers[i](flatten_out)
            new_feature_list.append(recombine_out.reshape(X.size(0), -1, self.embedding_dim))
        new_feature_emb = torch.cat(new_feature_list, dim=1)
        return new_feature_emb

def __init__(self, num_fields, embedding_dim, channels=[3], kernel_heights=[3], pooling_sizes=[2], recombined_channels=[2], activation='Tanh', batch_norm=True):
    super(FGCNN_Layer, self).__init__()
    self.embedding_dim = embedding_dim
    conv_list = []
    recombine_list = []
    self.channels = [1] + channels
    input_height = num_fields
    for i in range(1, len(self.channels)):
        in_channel = self.channels[i - 1]
        out_channel = self.channels[i]
        kernel_height = kernel_heights[i - 1]
        pooling_size = pooling_sizes[i - 1]
        recombined_channel = recombined_channels[i - 1]
        conv_layer = [nn.Conv2d(in_channel, out_channel, kernel_size=(kernel_height, 1), padding=(int((kernel_height - 1) / 2), 0))] + ([nn.BatchNorm2d(out_channel)] if batch_norm else []) + [get_activation(activation), nn.MaxPool2d((pooling_size, 1), padding=(input_height % pooling_size, 0))]
        conv_list.append(nn.Sequential(*conv_layer))
        input_height = int(np.ceil(input_height / pooling_size))
        input_dim = input_height * embedding_dim * out_channel
        output_dim = input_height * embedding_dim * recombined_channel
        recombine_layer = nn.Sequential(nn.Linear(input_dim, output_dim), get_activation(activation))
        recombine_list.append(recombine_layer)
    self.conv_layers = nn.ModuleList(conv_list)
    self.recombine_layers = nn.ModuleList(recombine_list)

class AutoInt(BaseModel):

    def __init__(self, feature_map, model_id='AutoInt', gpu=-1, learning_rate=0.001, embedding_dim=10, dnn_hidden_units=[64, 64, 64], dnn_activations='ReLU', attention_layers=2, num_heads=1, attention_dim=8, net_dropout=0, batch_norm=False, layer_norm=False, use_scale=False, use_wide=False, use_residual=True, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(AutoInt, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        self.lr_layer = LogisticRegression(feature_map, use_bias=False) if use_wide else None
        self.dnn = MLP_Block(input_dim=feature_map.sum_emb_out_dim(), output_dim=1, hidden_units=dnn_hidden_units, hidden_activations=dnn_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm) if dnn_hidden_units else None
        self.self_attention = nn.Sequential(*[MultiHeadSelfAttention(embedding_dim if i == 0 else attention_dim, attention_dim=attention_dim, num_heads=num_heads, dropout_rate=net_dropout, use_residual=use_residual, use_scale=use_scale, layer_norm=layer_norm) for i in range(attention_layers)])
        self.fc = nn.Linear(feature_map.num_fields * attention_dim, 1)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        """
        Inputs: [X, y]
        """
        X = self.get_inputs(inputs)
        feature_emb = self.embedding_layer(X)
        attention_out = self.self_attention(feature_emb)
        attention_out = torch.flatten(attention_out, start_dim=1)
        y_pred = self.fc(attention_out)
        if self.dnn is not None:
            y_pred += self.dnn(feature_emb.flatten(start_dim=1))
        if self.lr_layer is not None:
            y_pred += self.lr_layer(X)
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred}
        return return_dict

def __init__(self, feature_map, model_id='AutoInt', gpu=-1, learning_rate=0.001, embedding_dim=10, dnn_hidden_units=[64, 64, 64], dnn_activations='ReLU', attention_layers=2, num_heads=1, attention_dim=8, net_dropout=0, batch_norm=False, layer_norm=False, use_scale=False, use_wide=False, use_residual=True, embedding_regularizer=None, net_regularizer=None, **kwargs):
    super(AutoInt, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
    self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
    self.lr_layer = LogisticRegression(feature_map, use_bias=False) if use_wide else None
    self.dnn = MLP_Block(input_dim=feature_map.sum_emb_out_dim(), output_dim=1, hidden_units=dnn_hidden_units, hidden_activations=dnn_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm) if dnn_hidden_units else None
    self.self_attention = nn.Sequential(*[MultiHeadSelfAttention(embedding_dim if i == 0 else attention_dim, attention_dim=attention_dim, num_heads=num_heads, dropout_rate=net_dropout, use_residual=use_residual, use_scale=use_scale, layer_norm=layer_norm) for i in range(attention_layers)])
    self.fc = nn.Linear(feature_map.num_fields * attention_dim, 1)
    self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
    self.reset_parameters()
    self.model_to_device()

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

class GDCNP(BaseModel):

    def __init__(self, feature_map, model_id='GDCNP', gpu=-1, learning_rate=0.001, embedding_dim=10, dnn_hidden_units=[], dnn_activations='ReLU', num_cross_layers=3, net_dropout=0, batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(GDCNP, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        input_dim = feature_map.sum_emb_out_dim()
        self.dnn = MLP_Block(input_dim=input_dim, output_dim=None, hidden_units=dnn_hidden_units, hidden_activations=dnn_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm) if dnn_hidden_units else None
        self.cross_net = GateCorssLayer(input_dim, num_cross_layers)
        self.fc = torch.nn.Linear(dnn_hidden_units[-1] + input_dim, 1)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        X = self.get_inputs(inputs)
        feature_emb = self.embedding_layer(X, flatten_emb=True)
        cross_cn = self.cross_net(feature_emb)
        cross_mlp = self.dnn(feature_emb)
        y_pred = self.fc(torch.cat([cross_cn, cross_mlp], dim=1))
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred}
        return return_dict

def __init__(self, feature_map, model_id='GDCNP', gpu=-1, learning_rate=0.001, embedding_dim=10, dnn_hidden_units=[], dnn_activations='ReLU', num_cross_layers=3, net_dropout=0, batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
    super(GDCNP, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
    self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
    input_dim = feature_map.sum_emb_out_dim()
    self.dnn = MLP_Block(input_dim=input_dim, output_dim=None, hidden_units=dnn_hidden_units, hidden_activations=dnn_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm) if dnn_hidden_units else None
    self.cross_net = GateCorssLayer(input_dim, num_cross_layers)
    self.fc = torch.nn.Linear(dnn_hidden_units[-1] + input_dim, 1)
    self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
    self.reset_parameters()
    self.model_to_device()

class GDCN(BaseModel):

    def __init__(self, feature_map, model_id='GDCN', gpu=-1, learning_rate=0.001, embedding_dim=10, dnn_hidden_units=[], dnn_activations='ReLU', num_cross_layers=3, net_dropout=0, batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(GDCN, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        input_dim = feature_map.sum_emb_out_dim()
        self.dnn = MLP_Block(input_dim=input_dim, output_dim=1, hidden_units=dnn_hidden_units, hidden_activations=dnn_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm) if dnn_hidden_units else None
        self.cross_net = GateCorssLayer(input_dim, num_cross_layers)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        X = self.get_inputs(inputs)
        feature_emb = self.embedding_layer(X, flatten_emb=True)
        cross_cn = self.cross_net(feature_emb)
        y_pred = self.dnn(cross_cn)
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred}
        return return_dict

def __init__(self, feature_map, model_id='GDCN', gpu=-1, learning_rate=0.001, embedding_dim=10, dnn_hidden_units=[], dnn_activations='ReLU', num_cross_layers=3, net_dropout=0, batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
    super(GDCN, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
    self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
    input_dim = feature_map.sum_emb_out_dim()
    self.dnn = MLP_Block(input_dim=input_dim, output_dim=1, hidden_units=dnn_hidden_units, hidden_activations=dnn_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm) if dnn_hidden_units else None
    self.cross_net = GateCorssLayer(input_dim, num_cross_layers)
    self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
    self.reset_parameters()
    self.model_to_device()

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

def __init__(self, input_dim, cn_layers=3):
    super().__init__()
    self.cn_layers = cn_layers
    self.w = nn.ModuleList([nn.Linear(input_dim, input_dim, bias=False) for _ in range(cn_layers)])
    self.wg = nn.ModuleList([nn.Linear(input_dim, input_dim, bias=False) for _ in range(cn_layers)])
    self.b = nn.ParameterList([nn.Parameter(torch.zeros((input_dim,))) for _ in range(cn_layers)])
    for i in range(cn_layers):
        nn.init.uniform_(self.b[i].data)
    self.activation = nn.Sigmoid()

class DCN(BaseModel):

    def __init__(self, feature_map, model_id='DCN', learning_rate=0.001, embedding_dim=10, dnn_hidden_units=[], dnn_activations='ReLU', net_dropout=0, num_cross_layers=3, batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(DCN, self).__init__(feature_map, model_id=model_id, **kwargs)
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim, embedding_regularizer=embedding_regularizer)
        input_dim = feature_map.sum_emb_out_dim()
        self.crossnet = CrossNet(input_dim, num_cross_layers)
        self.dnn = MLP_Block(input_dim=input_dim, output_dim=None, hidden_units=dnn_hidden_units, hidden_activations=dnn_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm, regularizer=net_regularizer) if dnn_hidden_units else None
        final_dim = input_dim
        if isinstance(dnn_hidden_units, list) and len(dnn_hidden_units) > 0:
            final_dim += dnn_hidden_units[-1]
        self.fc = Linear(1, regularizer=net_regularizer)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)

    def call(self, inputs, training=False):
        X = self.get_inputs(inputs)
        feature_emb = self.embedding_layer(X, flatten_emb=True)
        cross_out = self.crossnet(feature_emb)
        if self.dnn is not None:
            dnn_out = self.dnn(feature_emb)
            final_out = tf.concat([cross_out, dnn_out], axis=-1)
        else:
            final_out = cross_out
        y_pred = self.fc(final_out)
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred}
        return return_dict

def __init__(self, feature_map, model_id='DCN', learning_rate=0.001, embedding_dim=10, dnn_hidden_units=[], dnn_activations='ReLU', net_dropout=0, num_cross_layers=3, batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
    super(DCN, self).__init__(feature_map, model_id=model_id, **kwargs)
    self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim, embedding_regularizer=embedding_regularizer)
    input_dim = feature_map.sum_emb_out_dim()
    self.crossnet = CrossNet(input_dim, num_cross_layers)
    self.dnn = MLP_Block(input_dim=input_dim, output_dim=None, hidden_units=dnn_hidden_units, hidden_activations=dnn_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm, regularizer=net_regularizer) if dnn_hidden_units else None
    final_dim = input_dim
    if isinstance(dnn_hidden_units, list) and len(dnn_hidden_units) > 0:
        final_dim += dnn_hidden_units[-1]
    self.fc = Linear(1, regularizer=net_regularizer)
    self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)

class DCN(BaseModel):

    def __init__(self, feature_map, model_id='DCN', gpu=-1, learning_rate=0.001, embedding_dim=10, dnn_hidden_units=[], dnn_activations='ReLU', num_cross_layers=3, net_dropout=0, batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(DCN, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        input_dim = feature_map.sum_emb_out_dim()
        self.dnn = MLP_Block(input_dim=input_dim, output_dim=None, hidden_units=dnn_hidden_units, hidden_activations=dnn_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm) if dnn_hidden_units else None
        self.crossnet = CrossNet(input_dim, num_cross_layers)
        final_dim = input_dim
        if isinstance(dnn_hidden_units, list) and len(dnn_hidden_units) > 0:
            final_dim += dnn_hidden_units[-1]
        self.fc = nn.Linear(final_dim, 1)
        self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        X = self.get_inputs(inputs)
        feature_emb = self.embedding_layer(X, flatten_emb=True)
        cross_out = self.crossnet(feature_emb)
        if self.dnn is not None:
            dnn_out = self.dnn(feature_emb)
            final_out = torch.cat([cross_out, dnn_out], dim=-1)
        else:
            final_out = cross_out
        y_pred = self.fc(final_out)
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred}
        return return_dict

def __init__(self, feature_map, model_id='DCN', gpu=-1, learning_rate=0.001, embedding_dim=10, dnn_hidden_units=[], dnn_activations='ReLU', num_cross_layers=3, net_dropout=0, batch_norm=False, embedding_regularizer=None, net_regularizer=None, **kwargs):
    super(DCN, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
    self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
    input_dim = feature_map.sum_emb_out_dim()
    self.dnn = MLP_Block(input_dim=input_dim, output_dim=None, hidden_units=dnn_hidden_units, hidden_activations=dnn_activations, output_activation=None, dropout_rates=net_dropout, batch_norm=batch_norm) if dnn_hidden_units else None
    self.crossnet = CrossNet(input_dim, num_cross_layers)
    final_dim = input_dim
    if isinstance(dnn_hidden_units, list) and len(dnn_hidden_units) > 0:
        final_dim += dnn_hidden_units[-1]
    self.fc = nn.Linear(final_dim, 1)
    self.compile(kwargs['optimizer'], kwargs['loss'], learning_rate)
    self.reset_parameters()
    self.model_to_device()

class MaskedSumPooling(Model):

    def __init__(self):
        super(MaskedSumPooling, self).__init__()

    def forward(self, embedding_matrix):
        return tf.reduce_sum(embedding_matrix, axis=1)

def __init__(self):
    super(MaskedSumPooling, self).__init__()

class FeatureEmbedding(Layer):

    def __init__(self, feature_map, embedding_dim, embedding_initializer='random_normal(stddev=1e-4)', embedding_regularizer=None, required_feature_columns=None, not_required_feature_columns=None, use_pretrain=True, use_sharing=True, name_prefix='emb_'):
        super(FeatureEmbedding, self).__init__()
        self.embedding_layer = FeatureEmbeddingDict(feature_map, embedding_dim, embedding_initializer=embedding_initializer, embedding_regularizer=embedding_regularizer, required_feature_columns=required_feature_columns, not_required_feature_columns=not_required_feature_columns, use_pretrain=use_pretrain, use_sharing=use_sharing, name_prefix=name_prefix)

    def call(self, X, feature_source=[], feature_type=[], flatten_emb=False):
        feature_emb_dict = self.embedding_layer(X, feature_source=feature_source, feature_type=feature_type)
        feature_emb = self.embedding_layer.dict2tensor(feature_emb_dict, flatten_emb=flatten_emb)
        return feature_emb

def __init__(self, feature_map, embedding_dim, embedding_initializer='random_normal(stddev=1e-4)', embedding_regularizer=None, required_feature_columns=None, not_required_feature_columns=None, use_pretrain=True, use_sharing=True, name_prefix='emb_'):
    super(FeatureEmbedding, self).__init__()
    self.embedding_layer = FeatureEmbeddingDict(feature_map, embedding_dim, embedding_initializer=embedding_initializer, embedding_regularizer=embedding_regularizer, required_feature_columns=required_feature_columns, not_required_feature_columns=not_required_feature_columns, use_pretrain=use_pretrain, use_sharing=use_sharing, name_prefix=name_prefix)

class CrossInteraction(Layer):

    def __init__(self, input_dim):
        super(CrossInteraction, self).__init__()
        self.weight = Dense(1, use_bias=False)
        self.bias = tf.Variable(tf.zeros(input_dim))

    def call(self, X_0, X_i):
        interact_out = self.weight(X_i) * X_0 + self.bias
        return interact_out

def __init__(self, input_dim):
    super(CrossInteraction, self).__init__()
    self.weight = Dense(1, use_bias=False)
    self.bias = tf.Variable(tf.zeros(input_dim))

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

def __init__(self, input_dim, num_layers):
    super(CrossNet, self).__init__()
    self.num_layers = num_layers
    self.cross_net = []
    for _ in range(self.num_layers):
        self.cross_net.append(CrossInteraction(input_dim))

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

def __init__(self, input_dim, num_layers):
    super(CrossNetV2, self).__init__()
    self.num_layers = num_layers
    self.cross_layers = []
    for _ in range(self.num_layers):
        self.cross_layers.append(Dense(input_dim))

class FactorizationMachine(Layer):

    def __init__(self, feature_map, regularizer=None):
        super(FactorizationMachine, self).__init__()
        self.fm_layer = InnerProductInteraction(feature_map.num_fields, output='product_sum')
        self.lr_layer = LogisticRegression(feature_map, use_bias=True, regularizer=regularizer)

    def call(self, X, feature_emb):
        lr_out = self.lr_layer(X)
        fm_out = self.fm_layer(feature_emb)
        output = fm_out + lr_out
        return output

def __init__(self, feature_map, regularizer=None):
    super(FactorizationMachine, self).__init__()
    self.fm_layer = InnerProductInteraction(feature_map.num_fields, output='product_sum')
    self.lr_layer = LogisticRegression(feature_map, use_bias=True, regularizer=regularizer)

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

def __init__(self, feature_map, use_bias=True, regularizer=None):
    super(LogisticRegression, self).__init__()
    self.bias = tf.Variable(tf.zeros(1)) if use_bias else None
    self.embedding_layer = FeatureEmbedding(feature_map, 1, use_pretrain=False, use_sharing=False, embedding_regularizer=regularizer, name_prefix='lr_')

class Linear(Layer):

    def __init__(self, output_dim, use_bias=True, initializer='glorot_normal', regularizer=None):
        super(Linear, self).__init__()
        self.linear = Dense(output_dim, use_bias=use_bias, kernel_initializer=get_initializer(initializer), kernel_regularizer=get_regularizer(regularizer), bias_regularizer=get_regularizer(regularizer))

    def call(self, inputs):
        return self.linear(inputs)

def __init__(self, output_dim, use_bias=True, initializer='glorot_normal', regularizer=None):
    super(Linear, self).__init__()
    self.linear = Dense(output_dim, use_bias=use_bias, kernel_initializer=get_initializer(initializer), kernel_regularizer=get_regularizer(regularizer), bias_regularizer=get_regularizer(regularizer))

class MaskedAveragePooling(nn.Module):

    def __init__(self):
        super(MaskedAveragePooling, self).__init__()

    def forward(self, embedding_matrix, mask=None):
        sum_out = torch.sum(embedding_matrix, dim=1)
        if mask is None:
            mask = embedding_matrix.sum(dim=-1) != 0
        avg_out = sum_out / (mask.float().sum(-1, keepdim=True) + 1e-12)
        return avg_out

def __init__(self):
    super(MaskedAveragePooling, self).__init__()

class MaskedSumPooling(nn.Module):

    def __init__(self):
        super(MaskedSumPooling, self).__init__()

    def forward(self, embedding_matrix):
        return torch.sum(embedding_matrix, dim=1)

def __init__(self):
    super(MaskedSumPooling, self).__init__()

class KMaxPooling(nn.Module):

    def __init__(self, k, dim):
        super(KMaxPooling, self).__init__()
        self.k = k
        self.dim = dim

    def forward(self, X):
        index = X.topk(self.k, dim=self.dim)[1].sort(dim=self.dim)[0]
        output = X.gather(self.dim, index)
        return output

def __init__(self, k, dim):
    super(KMaxPooling, self).__init__()
    self.k = k
    self.dim = dim

class Dice(nn.Module):

    def __init__(self, input_dim, eps=1e-09):
        super(Dice, self).__init__()
        self.bn = nn.BatchNorm1d(input_dim, affine=False, eps=eps, momentum=0.01)
        self.alpha = nn.Parameter(torch.zeros(input_dim))

    def forward(self, X):
        p = torch.sigmoid(self.bn(X))
        output = p * X + self.alpha * (1 - p) * X
        return output

def __init__(self, input_dim, eps=1e-09):
    super(Dice, self).__init__()
    self.bn = nn.BatchNorm1d(input_dim, affine=False, eps=eps, momentum=0.01)
    self.alpha = nn.Parameter(torch.zeros(input_dim))

class GELU(nn.Module):

    def __init__(self):
        super(GELU, self).__init__()

    def forward(self, x):
        return 0.5 * x * (1 + torch.tanh(np.sqrt(2 / np.pi) * (x + 0.044715 * torch.pow(x, 3))))

def __init__(self):
    super(GELU, self).__init__()

class FeatureEmbedding(nn.Module):

    def __init__(self, feature_map, embedding_dim, embedding_initializer='partial(nn.init.normal_, std=1e-4)', required_feature_columns=None, not_required_feature_columns=None, use_pretrain=True, use_sharing=True):
        super(FeatureEmbedding, self).__init__()
        self.embedding_layer = FeatureEmbeddingDict(feature_map, embedding_dim, embedding_initializer=embedding_initializer, required_feature_columns=required_feature_columns, not_required_feature_columns=not_required_feature_columns, use_pretrain=use_pretrain, use_sharing=use_sharing)

    def forward(self, X, feature_source=[], feature_type=[], flatten_emb=False):
        feature_emb_dict = self.embedding_layer(X, feature_source=feature_source, feature_type=feature_type)
        feature_emb = self.embedding_layer.dict2tensor(feature_emb_dict, flatten_emb=flatten_emb)
        return feature_emb

def __init__(self, feature_map, embedding_dim, embedding_initializer='partial(nn.init.normal_, std=1e-4)', required_feature_columns=None, not_required_feature_columns=None, use_pretrain=True, use_sharing=True):
    super(FeatureEmbedding, self).__init__()
    self.embedding_layer = FeatureEmbeddingDict(feature_map, embedding_dim, embedding_initializer=embedding_initializer, required_feature_columns=required_feature_columns, not_required_feature_columns=not_required_feature_columns, use_pretrain=use_pretrain, use_sharing=use_sharing)

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

def __init__(self, dropout_rate=0.0):
    super(ScaledDotProductAttention, self).__init__()
    self.dropout = nn.Dropout(dropout_rate) if dropout_rate > 0 else None

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

def __init__(self, embedding_dim=64, attention_units=[32], hidden_activations='ReLU', output_activation=None, dropout_rate=0, batch_norm=False, use_softmax=False):
    super(DIN_Attention, self).__init__()
    self.embedding_dim = embedding_dim
    self.use_softmax = use_softmax
    if isinstance(hidden_activations, str) and hidden_activations.lower() == 'dice':
        hidden_activations = [Dice(units) for units in attention_units]
    self.attention_layer = MLP_Block(input_dim=4 * embedding_dim, output_dim=1, hidden_units=attention_units, hidden_activations=hidden_activations, output_activation=output_activation, dropout_rates=dropout_rate, batch_norm=batch_norm)

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

class BilinearInteraction(nn.Module):

    def __init__(self, num_fields, embedding_dim, bilinear_type='field_interaction'):
        super(BilinearInteraction, self).__init__()
        self.bilinear_type = bilinear_type
        self.interact_dim = int(num_fields * (num_fields - 1) / 2)
        if self.bilinear_type == 'field_all':
            self.bilinear_W = nn.Parameter(torch.Tensor(embedding_dim, embedding_dim))
        elif self.bilinear_type == 'field_each':
            self.bilinear_W = nn.Parameter(torch.Tensor(num_fields, embedding_dim, embedding_dim))
        elif self.bilinear_type == 'field_interaction':
            self.bilinear_W = nn.Parameter(torch.Tensor(self.interact_dim, embedding_dim, embedding_dim))
        else:
            raise NotImplementedError
        self.init_weights()

    def init_weights(self):
        nn.init.xavier_normal_(self.bilinear_W)

    def forward(self, feature_emb):
        feature_emb_list = torch.split(feature_emb, 1, dim=1)
        if self.bilinear_type == 'field_all':
            bilinear_list = [torch.matmul(v_i, self.bilinear_W) * v_j for v_i, v_j in combinations(feature_emb_list, 2)]
        elif self.bilinear_type == 'field_each':
            bilinear_W_list = torch.split(self.bilinear_W, 1, dim=0)
            bilinear_list = [torch.matmul(feature_emb_list[i], bilinear_W_list[i]) * feature_emb_list[j] for i, j in combinations(range(len(feature_emb_list)), 2)]
        elif self.bilinear_type == 'field_interaction':
            bilinear_W_list = torch.split(self.bilinear_W, 1, dim=0)
            bilinear_list = [torch.matmul(v[0], bilinear_W_list[i]) * v[1] for i, v in enumerate(combinations(feature_emb_list, 2))]
        return torch.cat(bilinear_list, dim=1)

def __init__(self, num_fields, embedding_dim, bilinear_type='field_interaction'):
    super(BilinearInteraction, self).__init__()
    self.bilinear_type = bilinear_type
    self.interact_dim = int(num_fields * (num_fields - 1) / 2)
    if self.bilinear_type == 'field_all':
        self.bilinear_W = nn.Parameter(torch.Tensor(embedding_dim, embedding_dim))
    elif self.bilinear_type == 'field_each':
        self.bilinear_W = nn.Parameter(torch.Tensor(num_fields, embedding_dim, embedding_dim))
    elif self.bilinear_type == 'field_interaction':
        self.bilinear_W = nn.Parameter(torch.Tensor(self.interact_dim, embedding_dim, embedding_dim))
    else:
        raise NotImplementedError
    self.init_weights()

def init_weights(self):
    nn.init.xavier_normal_(self.bilinear_W)

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

def __init__(self, num_fields, interaction_type='circular_convolution'):
    super(HolographicInteraction, self).__init__()
    self.interaction_type = interaction_type
    if self.interaction_type == 'circular_correlation':
        self.conj_sign = nn.Parameter(torch.tensor([1.0, -1.0]), requires_grad=False)
    self.triu_index = nn.Parameter(torch.triu_indices(num_fields, num_fields, offset=1), requires_grad=False)

class CrossInteraction(nn.Module):

    def __init__(self, input_dim):
        super(CrossInteraction, self).__init__()
        self.weight = nn.Linear(input_dim, 1, bias=False)
        self.bias = nn.Parameter(torch.zeros(input_dim))

    def forward(self, X_0, X_i):
        interact_out = self.weight(X_i) * X_0 + self.bias
        return interact_out

def __init__(self, input_dim):
    super(CrossInteraction, self).__init__()
    self.weight = nn.Linear(input_dim, 1, bias=False)
    self.bias = nn.Parameter(torch.zeros(input_dim))

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

def __init__(self, input_dim, num_layers):
    super(CrossNet, self).__init__()
    self.num_layers = num_layers
    self.cross_net = nn.ModuleList((CrossInteraction(input_dim) for _ in range(self.num_layers)))

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

def __init__(self, input_dim, num_layers):
    super(CrossNetV2, self).__init__()
    self.num_layers = num_layers
    self.cross_layers = nn.ModuleList((nn.Linear(input_dim, input_dim) for _ in range(self.num_layers)))

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

def __init__(self, in_features, layer_num=2, low_rank=32, num_experts=4):
    super(CrossNetMix, self).__init__()
    self.layer_num = layer_num
    self.num_experts = num_experts
    self.U_list = torch.nn.ParameterList([nn.Parameter(nn.init.xavier_normal_(torch.empty(num_experts, in_features, low_rank))) for i in range(self.layer_num)])
    self.V_list = torch.nn.ParameterList([nn.Parameter(nn.init.xavier_normal_(torch.empty(num_experts, in_features, low_rank))) for i in range(self.layer_num)])
    self.C_list = torch.nn.ParameterList([nn.Parameter(nn.init.xavier_normal_(torch.empty(num_experts, low_rank, low_rank))) for i in range(self.layer_num)])
    self.gating = nn.ModuleList([nn.Linear(in_features, 1, bias=False) for i in range(self.num_experts)])
    self.bias = torch.nn.ParameterList([nn.Parameter(nn.init.zeros_(torch.empty(in_features, 1))) for i in range(self.layer_num)])

class InteractionMachine(nn.Module):

    def __init__(self, embedding_dim, order=2, batch_norm=False):
        super(InteractionMachine, self).__init__()
        assert order < 6, 'order={} is not supported.'.format(order)
        self.order = order
        self.bn = nn.BatchNorm1d(embedding_dim * order) if batch_norm else None
        self.fc = nn.Linear(order * embedding_dim, 1)

    def second_order(self, p1, p2):
        return (p1.pow(2) - p2) / 2

    def third_order(self, p1, p2, p3):
        return (p1.pow(3) - 3 * p1 * p2 + 2 * p3) / 6

    def fourth_order(self, p1, p2, p3, p4):
        return (p1.pow(4) - 6 * p1.pow(2) * p2 + 3 * p2.pow(2) + 8 * p1 * p3 - 6 * p4) / 24

    def fifth_order(self, p1, p2, p3, p4, p5):
        return (p1.pow(5) - 10 * p1.pow(3) * p2 + 20 * p1.pow(2) * p3 - 30 * p1 * p4 - 20 * p2 * p3 + 15 * p1 * p2.pow(2) + 24 * p5) / 120

    def forward(self, X):
        out = []
        Q = X
        if self.order >= 1:
            p1 = Q.sum(dim=1)
            out.append(p1)
            if self.order >= 2:
                Q = Q * X
                p2 = Q.sum(dim=1)
                out.append(self.second_order(p1, p2))
                if self.order >= 3:
                    Q = Q * X
                    p3 = Q.sum(dim=1)
                    out.append(self.third_order(p1, p2, p3))
                    if self.order >= 4:
                        Q = Q * X
                        p4 = Q.sum(dim=1)
                        out.append(self.fourth_order(p1, p2, p3, p4))
                        if self.order == 5:
                            Q = Q * X
                            p5 = Q.sum(dim=1)
                            out.append(self.fifth_order(p1, p2, p3, p4, p5))
        out = torch.cat(out, dim=-1)
        if self.bn is not None:
            out = self.bn(out)
        y = self.fc(out)
        return y

def __init__(self, embedding_dim, order=2, batch_norm=False):
    super(InteractionMachine, self).__init__()
    assert order < 6, 'order={} is not supported.'.format(order)
    self.order = order
    self.bn = nn.BatchNorm1d(embedding_dim * order) if batch_norm else None
    self.fc = nn.Linear(order * embedding_dim, 1)

class FactorizationMachine(nn.Module):

    def __init__(self, feature_map):
        super(FactorizationMachine, self).__init__()
        self.fm_layer = InnerProductInteraction(feature_map.num_fields, output='product_sum')
        self.lr_layer = LogisticRegression(feature_map, use_bias=True)

    def forward(self, X, feature_emb):
        lr_out = self.lr_layer(X)
        fm_out = self.fm_layer(feature_emb)
        output = fm_out + lr_out
        return output

def __init__(self, feature_map):
    super(FactorizationMachine, self).__init__()
    self.fm_layer = InnerProductInteraction(feature_map.num_fields, output='product_sum')
    self.lr_layer = LogisticRegression(feature_map, use_bias=True)

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

def __init__(self, feature_map, use_bias=True):
    super(LogisticRegression, self).__init__()
    self.bias = nn.Parameter(torch.zeros(1), requires_grad=True) if use_bias else None
    self.embedding_layer = FeatureEmbedding(feature_map, 1, use_pretrain=False, use_sharing=False)

class MLP_Block(nn.Module):

    def __init__(self, input_dim, hidden_units=[], hidden_activations='ReLU', output_dim=None, output_activation=None, dropout_rates=0.0, batch_norm=False, bn_only_once=False, use_bias=True):
        super(MLP_Block, self).__init__()
        dense_layers = []
        if not isinstance(dropout_rates, list):
            dropout_rates = [dropout_rates] * len(hidden_units)
        if not isinstance(hidden_activations, list):
            hidden_activations = [hidden_activations] * len(hidden_units)
        hidden_activations = get_activation(hidden_activations, hidden_units)
        hidden_units = [input_dim] + hidden_units
        if batch_norm and bn_only_once:
            dense_layers.append(nn.BatchNorm1d(input_dim))
        for idx in range(len(hidden_units) - 1):
            dense_layers.append(nn.Linear(hidden_units[idx], hidden_units[idx + 1], bias=use_bias))
            if batch_norm and (not bn_only_once):
                dense_layers.append(nn.BatchNorm1d(hidden_units[idx + 1]))
            if hidden_activations[idx]:
                dense_layers.append(hidden_activations[idx])
            if dropout_rates[idx] > 0:
                dense_layers.append(nn.Dropout(p=dropout_rates[idx]))
        if output_dim is not None:
            dense_layers.append(nn.Linear(hidden_units[-1], output_dim, bias=use_bias))
        if output_activation is not None:
            dense_layers.append(get_activation(output_activation))
        self.mlp = nn.Sequential(*dense_layers)

    def forward(self, inputs):
        return self.mlp(inputs)

def __init__(self, input_dim, hidden_units=[], hidden_activations='ReLU', output_dim=None, output_activation=None, dropout_rates=0.0, batch_norm=False, bn_only_once=False, use_bias=True):
    super(MLP_Block, self).__init__()
    dense_layers = []
    if not isinstance(dropout_rates, list):
        dropout_rates = [dropout_rates] * len(hidden_units)
    if not isinstance(hidden_activations, list):
        hidden_activations = [hidden_activations] * len(hidden_units)
    hidden_activations = get_activation(hidden_activations, hidden_units)
    hidden_units = [input_dim] + hidden_units
    if batch_norm and bn_only_once:
        dense_layers.append(nn.BatchNorm1d(input_dim))
    for idx in range(len(hidden_units) - 1):
        dense_layers.append(nn.Linear(hidden_units[idx], hidden_units[idx + 1], bias=use_bias))
        if batch_norm and (not bn_only_once):
            dense_layers.append(nn.BatchNorm1d(hidden_units[idx + 1]))
        if hidden_activations[idx]:
            dense_layers.append(hidden_activations[idx])
        if dropout_rates[idx] > 0:
            dense_layers.append(nn.Dropout(p=dropout_rates[idx]))
    if output_dim is not None:
        dense_layers.append(nn.Linear(hidden_units[-1], output_dim, bias=use_bias))
    if output_activation is not None:
        dense_layers.append(get_activation(output_activation))
    self.mlp = nn.Sequential(*dense_layers)

