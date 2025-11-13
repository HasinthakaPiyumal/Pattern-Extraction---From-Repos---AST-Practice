# Cluster 15

class ContextBlock(nn.Module):

    def __init__(self, n_feat, bias=False):
        super(ContextBlock, self).__init__()
        self.conv_mask = nn.Conv2d(n_feat, 1, kernel_size=1, bias=bias)
        self.softmax = nn.Softmax(dim=2)
        self.channel_add_conv = nn.Sequential(nn.Conv2d(n_feat, n_feat, kernel_size=1, bias=bias), nn.LeakyReLU(0.2), nn.Conv2d(n_feat, n_feat, kernel_size=1, bias=bias))

    def modeling(self, x):
        batch, channel, height, width = x.size()
        input_x = x
        input_x = input_x.view(batch, channel, height * width)
        input_x = input_x.unsqueeze(1)
        context_mask = self.conv_mask(x)
        context_mask = context_mask.view(batch, 1, height * width)
        context_mask = self.softmax(context_mask)
        context_mask = context_mask.unsqueeze(3)
        context = torch.matmul(input_x, context_mask)
        context = context.view(batch, channel, 1, 1)
        return context

    def forward(self, x):
        context = self.modeling(x)
        channel_add_term = self.channel_add_conv(context)
        x = x + channel_add_term
        return x

def forward(self, x):
    context = self.modeling(x)
    channel_add_term = self.channel_add_conv(context)
    x = x + channel_add_term
    return x

