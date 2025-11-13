# Cluster 16

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

def forward(self, X):
    output = self.ffn(X)
    if self.use_residual:
        output += X
    if self.layer_norm is not None:
        output = self.layer_norm(output)
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

def forward(self, x):
    flatten_fm = self.optimized_fm(x)
    mlp_in = self.layer_norm(flatten_fm)
    mlp_out = self.mlp(mlp_in)
    return mlp_out.view(-1, self.output_features, self.embedding_dim)

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

def forward(self, x):
    fmb_out = self.fmb(x)
    lcb_out = self.lcb(x)
    concat_out = torch.cat([fmb_out, lcb_out], dim=1)
    out = self.residual(concat_out, x)
    if self.layer_norm is not None:
        out = self.layer_norm(out)
    return out

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

