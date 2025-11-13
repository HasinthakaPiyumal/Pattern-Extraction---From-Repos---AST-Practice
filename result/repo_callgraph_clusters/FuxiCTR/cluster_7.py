# Cluster 7

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

def forward(self, V_emb, V_hidden):
    V_mask = self.mask_layer(V_emb)
    v_out = self.hidden_layer(V_mask * V_hidden)
    return v_out

