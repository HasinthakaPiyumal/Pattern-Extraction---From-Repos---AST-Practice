# Cluster 85

class MLP(nn.Module):
    """
    Copied from L5Kit's implementation `MLP`:
    https://github.com/woven-planet/l5kit/blob/master/l5kit/l5kit/planning/vectorized/global_graph.py.
    Changes:
        1. Add input & output description for `__init__`, `reset_parameters`, `forward`
        2. Change variable name `h` to `hidden_dims` in `__init__`
        3. Change variable name `i` to `layer_idx` in `forward`

    Very simple multi-layer perceptron (also called FFN)
    """

    def __init__(self, input_dim: int, hidden_dim: int, output_dim: int, num_layers: int):
        """
        Constructs MLP.
        :param input_dim: Input feature size.
        :param hidden_dim: Hidden layer size.
        :paran output_dim: Output feature size.
        :param num_layers: Number of model layers.
        """
        super().__init__()
        self.num_layers = num_layers
        hidden_dims = [hidden_dim] * (num_layers - 1)
        self.layers = nn.ModuleList((nn.Linear(n_in, n_out) for n_in, n_out in zip([input_dim] + hidden_dims, hidden_dims + [output_dim])))
        self.reset_parameters()

    def reset_parameters(self) -> None:
        """
        Re-initialize layer parameters.
        """
        for layer in self.layers.children():
            nn.init.zeros_(layer.bias)
            nn.init.kaiming_normal_(layer.weight, nonlinearity='relu')

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward of the module.
        :param x: Input tensor.
        :return: Output tensor.
        """
        for layer_idx, layer in enumerate(self.layers):
            x = F.relu(layer(x)) if layer_idx < self.num_layers - 1 else layer(x)
        return x

def reset_parameters(self) -> None:
    """
        Re-initialize layer parameters.
        """
    for layer in self.layers.children():
        nn.init.zeros_(layer.bias)
        nn.init.kaiming_normal_(layer.weight, nonlinearity='relu')

