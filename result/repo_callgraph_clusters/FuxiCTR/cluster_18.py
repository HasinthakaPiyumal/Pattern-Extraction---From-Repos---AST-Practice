# Cluster 18

class CrossInteraction(Layer):

    def __init__(self, input_dim):
        super(CrossInteraction, self).__init__()
        self.weight = Dense(1, use_bias=False)
        self.bias = tf.Variable(tf.zeros(input_dim))

    def call(self, X_0, X_i):
        interact_out = self.weight(X_i) * X_0 + self.bias
        return interact_out

def call(self, X_0, X_i):
    interact_out = self.weight(X_i) * X_0 + self.bias
    return interact_out

class CrossInteraction(nn.Module):

    def __init__(self, input_dim):
        super(CrossInteraction, self).__init__()
        self.weight = nn.Linear(input_dim, 1, bias=False)
        self.bias = nn.Parameter(torch.zeros(input_dim))

    def forward(self, X_0, X_i):
        interact_out = self.weight(X_i) * X_0 + self.bias
        return interact_out

def forward(self, X_0, X_i):
    interact_out = self.weight(X_i) * X_0 + self.bias
    return interact_out

