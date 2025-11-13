# Cluster 10

class ItemEncoder(nn.Module):
    encoder_type = ['TF', 'MLP', 'two_stage_MLP']

    def __init__(self, item_obs_size=60, item_num=30, item_encoder_type='TF', hidden_size=64, activation=nn.ReLU()):
        super(ItemEncoder, self).__init__()
        assert item_encoder_type in self.encoder_type, 'not support item encoder type: {}/{}'.format(item_encoder_type, self.encoder_type)
        self.item_encoder_type = item_encoder_type
        self.item_num = item_num
        self.hidden_size = hidden_size
        if self.item_encoder_type == 'TF':
            self.encoder = Transformer(item_obs_size, hidden_dim=2 * hidden_size, output_dim=hidden_size, activation=activation)
        elif self.item_encoder_type == 'MLP':
            self.encoder = MLP(item_obs_size, hidden_size, hidden_size, layer_num=3, activation=activation)
        elif self.item_encoder_type == 'two_stage_MLP':
            self.trans_len = 16
            self.encoder_1 = MLP(item_obs_size, hidden_size, self.trans_len, layer_num=3, activation=activation)
            self.encoder_2 = MLP(self.trans_len * self.item_num, hidden_size, self.item_num * hidden_size, layer_num=2, activation=activation)

    def forward(self, item_obs):
        if self.item_encoder_type == 'two_stage_MLP':
            item_embedding_1 = self.encoder_1(item_obs)
            item_embedding_2 = torch.reshape(item_embedding_1, [-1, self.trans_len * self.item_num])
            item_embedding = self.encoder_2(item_embedding_2)
            item_embedding = torch.reshape(item_embedding, [-1, self.item_num, self.hidden_size])
        else:
            item_embedding = self.encoder(item_obs)
        return item_embedding

def forward(self, item_obs):
    if self.item_encoder_type == 'two_stage_MLP':
        item_embedding_1 = self.encoder_1(item_obs)
        item_embedding_2 = torch.reshape(item_embedding_1, [-1, self.trans_len * self.item_num])
        item_embedding = self.encoder_2(item_embedding_2)
        item_embedding = torch.reshape(item_embedding, [-1, self.item_num, self.hidden_size])
    else:
        item_embedding = self.encoder(item_obs)
    return item_embedding

