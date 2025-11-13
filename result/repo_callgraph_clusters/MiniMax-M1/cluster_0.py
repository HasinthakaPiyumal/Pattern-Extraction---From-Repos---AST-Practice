# Cluster 0

def get_activation_fn(activation):
    if debug:
        logger.info(f'activation: {activation}')
    if activation == 'gelu':
        return F.gelu
    elif activation == 'relu':
        return F.relu
    elif activation == 'elu':
        return F.elu
    elif activation == 'sigmoid':
        return F.sigmoid
    elif activation == 'exp':

        def f(x):
            with torch.no_grad():
                x_max = torch.max(x, dim=-1, keepdims=True).values
            y = torch.exp(x - x_max)
            return y
        return f
    elif activation == 'leak':
        return F.leaky_relu
    elif activation == '1+elu':

        def f(x):
            return 1 + F.elu(x)
        return f
    elif activation == '2+elu':

        def f(x):
            return 2 + F.elu(x)
        return f
    elif activation == 'silu' or activation == 'swish':
        return F.silu
    elif activation == 'sine':
        return torch.sin
    else:
        logger.info(f'activation: does not support {activation}, use Identity!!!')
        return lambda x: x

