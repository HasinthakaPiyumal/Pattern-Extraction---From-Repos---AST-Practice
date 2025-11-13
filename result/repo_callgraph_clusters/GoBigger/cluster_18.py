# Cluster 18

class TransformerFFN(nn.Module):
    """
    Implements the FFN part of the transformer.
    """

    def __init__(self, dim: int=None, dim_hidden: int=None, dropout: float=0, activation: str='relu', **kwargs):
        super(TransformerFFN, self).__init__(**kwargs)
        self.dim = dim
        self.dim_hidden = dim_hidden
        self.dropout_ratio = dropout
        self.relu_dropout = nn.Dropout(p=self.dropout_ratio)
        if activation == 'relu':
            self.nonlinear = F.relu
        elif activation == 'gelu':
            self.nonlinear = F.gelu
        else:
            raise ValueError("Don't know how to handle --activation {}".format(activation))
        self.lin1 = nn.Linear(self.dim, self.dim_hidden)
        self.lin2 = nn.Linear(self.dim_hidden, self.dim)
        nn.init.xavier_uniform_(self.lin1.weight)
        nn.init.xavier_uniform_(self.lin2.weight)

    def forward(self, x: torch.Tensor, **kwargs) -> torch.Tensor:
        """
        Forward pass.
        """
        x = self.nonlinear(self.lin1(x))
        x = self.relu_dropout(x)
        x = self.lin2(x)
        return x

def forward(self, x: torch.Tensor, **kwargs) -> torch.Tensor:
    """
        Forward pass.
        """
    x = self.nonlinear(self.lin1(x))
    x = self.relu_dropout(x)
    x = self.lin2(x)
    return x

