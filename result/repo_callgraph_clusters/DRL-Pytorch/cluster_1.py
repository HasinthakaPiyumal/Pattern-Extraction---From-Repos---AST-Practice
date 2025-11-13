# Cluster 1

class Q_Net(nn.Module):

    def __init__(self, action_dim, hidden):
        super(Q_Net, self).__init__()
        self.net = nn.Sequential(nn.Conv2d(4, 32, 8, stride=4), nn.ReLU(), nn.Conv2d(32, 64, 4, stride=2), nn.ReLU(), nn.Conv2d(64, 64, 3, stride=1), nn.ReLU(), nn.Flatten(), nn.Linear(64 * 7 * 7, hidden), nn.ReLU(), nn.Linear(hidden, action_dim))

    def forward(self, obs):
        s = obs.float() / 255
        q = self.net(s)
        return q

    def orthogonal_init(self, layer, gain=1.4142):
        for name, param in layer.named_parameters():
            if 'bias' in name:
                nn.init.constant_(param, 0)
            elif 'weight' in name:
                nn.init.orthogonal_(param, gain=gain)
        return layer

def orthogonal_init(self, layer, gain=1.4142):
    for name, param in layer.named_parameters():
        if 'bias' in name:
            nn.init.constant_(param, 0)
        elif 'weight' in name:
            nn.init.orthogonal_(param, gain=gain)
    return layer

