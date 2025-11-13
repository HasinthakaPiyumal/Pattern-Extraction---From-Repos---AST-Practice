# Cluster 78

class WrapFunction(nn.Module):
    """Wrap the function to be tested for torch.onnx.export tracking."""

    def __init__(self, wrapped_function):
        super(WrapFunction, self).__init__()
        self.wrapped_function = wrapped_function

    def forward(self, *args, **kwargs):
        return self.wrapped_function(*args, **kwargs)

def forward(self, *args, **kwargs):
    return self.wrapped_function(*args, **kwargs)

