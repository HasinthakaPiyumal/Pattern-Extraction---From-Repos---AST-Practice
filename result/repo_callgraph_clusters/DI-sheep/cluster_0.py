# Cluster 0

class SheepModel(nn.Module):
    mode = ['compute_actor', 'compute_critic', 'compute_actor_critic']

    def __init__(self, item_obs_size=60, item_num=30, item_encoder_type='TF', bucket_obs_size=30, global_obs_size=17, hidden_size=64, activation=nn.ReLU(), ttorch_return=False):
        super(SheepModel, self).__init__()
        self.item_encoder = ItemEncoder(item_obs_size, item_num, item_encoder_type, hidden_size, activation=activation)
        self.bucket_encoder = MLP(bucket_obs_size, hidden_size, hidden_size, layer_num=3, activation=activation)
        self.global_encoder = MLP(global_obs_size, hidden_size, hidden_size, layer_num=2, activation=activation)
        self.value_head = nn.Sequential(MLP(hidden_size, hidden_size, hidden_size, layer_num=2, activation=activation), nn.Linear(hidden_size, 1))
        self.ttorch_return = ttorch_return

    def compute_actor(self, x):
        item_embedding = self.item_encoder(x['item_obs'])
        bucket_embedding = self.bucket_encoder(x['bucket_obs'])
        global_embedding = self.global_encoder(x['global_obs'])
        key = item_embedding
        query = bucket_embedding + global_embedding
        query = query.unsqueeze(1)
        logit = (key * query).sum(2)
        logit.masked_fill_(~x['action_mask'].bool(), value=-1000000000.0)
        if self.ttorch_return:
            return logit
        else:
            return {'logit': logit}

    def compute_critic(self, x):
        item_embedding = self.item_encoder(x['item_obs'])
        bucket_embedding = self.bucket_encoder(x['bucket_obs'])
        global_embedding = self.global_encoder(x['global_obs'])
        embedding = item_embedding.mean(1) + bucket_embedding + global_embedding
        value = self.value_head(embedding)
        if self.ttorch_return:
            return value.squeeze(1)
        else:
            return {'value': value.squeeze(1)}

    def compute_actor_critic(self, x):
        item_embedding = self.item_encoder(x['item_obs'])
        bucket_embedding = self.bucket_encoder(x['bucket_obs'])
        global_embedding = self.global_encoder(x['global_obs'])
        key = item_embedding
        query = bucket_embedding + global_embedding
        query = query.unsqueeze(1)
        logit = (key * query).sum(2)
        logit.masked_fill_(~x['action_mask'].bool(), value=-1000000000.0)
        embedding = item_embedding.mean(1) + bucket_embedding + global_embedding
        value = self.value_head(embedding)
        if self.ttorch_return:
            return ttorch.as_tensor({'logit': logit, 'value': value.squeeze(1)})
        else:
            return {'logit': logit, 'value': value.squeeze(1)}

    def forward(self, x, mode):
        assert mode in self.mode, 'not support forward mode: {}/{}'.format(mode, self.mode)
        return getattr(self, mode)(x)

    def compute_action(self, x):
        x = unsqueeze(to_tensor(x))
        with torch.no_grad():
            logit = self.compute_actor(x)['logit']
            return logit.argmax(dim=-1)[0].item()

def compute_action(self, x):
    x = unsqueeze(to_tensor(x))
    with torch.no_grad():
        logit = self.compute_actor(x)['logit']
        return logit.argmax(dim=-1)[0].item()

