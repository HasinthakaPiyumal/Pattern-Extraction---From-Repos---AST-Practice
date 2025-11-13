# Cluster 6

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

def forward(self, feature_emb):
    gates = self.linear(feature_emb.transpose(1, 2)).transpose(1, 2)
    if self.gate_residual == 'concat':
        out = torch.cat([feature_emb, feature_emb * gates], dim=1)
    else:
        out = feature_emb + feature_emb * gates
    return out

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

def forward(self, x):
    h = self.linear(x)
    h2, h1 = torch.chunk(h, chunks=2, dim=-1)
    if self.residual_type == 'concat':
        h = torch.cat([h2, h1 * h2], dim=-1)
    elif self.residual_type == 'sum':
        h = h2 + h1 * h2
    return h

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

def get_zeroth_components(self, feature_emb):
    """
        compute the 0th component
        """
    sum_of_square = torch.sum(feature_emb ** 2, dim=-1)
    zeroth_components = torch.sqrt(sum_of_square + 1)
    return zeroth_components

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

def forward(self, x):
    u = x.mean(-1, keepdim=True)
    s = (x - u).pow(2).mean(-1, keepdim=True)
    x = (x - u) / torch.sqrt(s + self.variance_epsilon)
    return self.weight * x + self.bias

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

def forward(self, x, hx, attn):
    gate_x = self.x2h(x)
    gate_h = self.h2h(hx)
    i_u, i_r, i_n = gate_x.chunk(3, 1)
    h_u, h_r, h_n = gate_h.chunk(3, 1)
    reset_gate = torch.sigmoid(i_r + h_r)
    new_gate = torch.tanh(i_n + reset_gate * h_n)
    hy = hx + attn.view(-1, 1) * (new_gate - hx)
    return hy

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

class LinearCompressionBlock(nn.Module):
    """ Linear Compression Block (LCB) """

    def __init__(self, input_features=16, output_features=8):
        super(LinearCompressionBlock, self).__init__()
        self.linear = nn.Linear(input_features, output_features, bias=False)

    def forward(self, x):
        out = self.linear(x.transpose(1, 2))
        return out.transpose(1, 2)

def forward(self, x):
    out = self.linear(x.transpose(1, 2))
    return out.transpose(1, 2)

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

def forward(self, x, hx, attn):
    gate_x = self.x2h(x)
    gate_h = self.h2h(hx)
    i_u, i_r, i_n = gate_x.chunk(3, 1)
    h_u, h_r, h_n = gate_h.chunk(3, 1)
    reset_gate = F.sigmoid(i_r + h_r)
    new_gate = F.tanh(i_n + reset_gate * h_n)
    hy = hx + attn.view(-1, 1) * (new_gate - hx)
    return hy

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

class Linear(Layer):

    def __init__(self, output_dim, use_bias=True, initializer='glorot_normal', regularizer=None):
        super(Linear, self).__init__()
        self.linear = Dense(output_dim, use_bias=use_bias, kernel_initializer=get_initializer(initializer), kernel_regularizer=get_regularizer(regularizer), bias_regularizer=get_regularizer(regularizer))

    def call(self, inputs):
        return self.linear(inputs)

def call(self, inputs):
    return self.linear(inputs)

class Dice(nn.Module):

    def __init__(self, input_dim, eps=1e-09):
        super(Dice, self).__init__()
        self.bn = nn.BatchNorm1d(input_dim, affine=False, eps=eps, momentum=0.01)
        self.alpha = nn.Parameter(torch.zeros(input_dim))

    def forward(self, X):
        p = torch.sigmoid(self.bn(X))
        output = p * X + self.alpha * (1 - p) * X
        return output

def forward(self, X):
    p = torch.sigmoid(self.bn(X))
    output = p * X + self.alpha * (1 - p) * X
    return output

class GELU(nn.Module):

    def __init__(self):
        super(GELU, self).__init__()

    def forward(self, x):
        return 0.5 * x * (1 + torch.tanh(np.sqrt(2 / np.pi) * (x + 0.044715 * torch.pow(x, 3))))

def forward(self, x):
    return 0.5 * x * (1 + torch.tanh(np.sqrt(2 / np.pi) * (x + 0.044715 * torch.pow(x, 3))))

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

def second_order(self, p1, p2):
    return (p1.pow(2) - p2) / 2

def third_order(self, p1, p2, p3):
    return (p1.pow(3) - 3 * p1 * p2 + 2 * p3) / 6

def fourth_order(self, p1, p2, p3, p4):
    return (p1.pow(4) - 6 * p1.pow(2) * p2 + 3 * p2.pow(2) + 8 * p1 * p3 - 6 * p4) / 24

def fifth_order(self, p1, p2, p3, p4, p5):
    return (p1.pow(5) - 10 * p1.pow(3) * p2 + 20 * p1.pow(2) * p3 - 30 * p1 * p4 - 20 * p2 * p3 + 15 * p1 * p2.pow(2) + 24 * p5) / 120

