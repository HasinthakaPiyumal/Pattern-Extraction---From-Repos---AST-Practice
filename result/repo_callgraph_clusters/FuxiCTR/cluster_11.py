# Cluster 11

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

def forward(self, inputs):
    return self.gate(inputs) * 2

