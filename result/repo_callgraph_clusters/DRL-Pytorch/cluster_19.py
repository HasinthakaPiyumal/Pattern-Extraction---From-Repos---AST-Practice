# Cluster 19

class Double_Q_Net(nn.Module):

    def __init__(self, state_dim, action_dim, hid_shape):
        super(Double_Q_Net, self).__init__()
        layers = [state_dim] + list(hid_shape) + [action_dim]
        self.Q1 = build_net(layers, nn.ReLU, nn.Identity)
        self.Q2 = build_net(layers, nn.ReLU, nn.Identity)

    def forward(self, s):
        q1 = self.Q1(s)
        q2 = self.Q2(s)
        return (q1, q2)

def forward(self, s):
    q1 = self.Q1(s)
    q2 = self.Q2(s)
    return (q1, q2)

