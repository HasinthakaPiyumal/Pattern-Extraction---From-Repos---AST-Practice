# Cluster 9

class V2XTransformer(nn.Module):

    def __init__(self, args):
        super(V2XTransformer, self).__init__()
        encoder_args = args['encoder']
        self.encoder = V2XTEncoder(encoder_args)

    def forward(self, x, mask, spatial_correction_matrix):
        output = self.encoder(x, mask, spatial_correction_matrix)
        output = output[:, 0]
        return output

def forward(self, x, mask, spatial_correction_matrix):
    output = self.encoder(x, mask, spatial_correction_matrix)
    output = output[:, 0]
    return output

class NaiveCompressor(nn.Module):

    def __init__(self, input_dim, compress_raito):
        super().__init__()
        self.encoder = nn.Sequential(nn.Conv2d(input_dim, input_dim // compress_raito, kernel_size=3, stride=1, padding=1), nn.BatchNorm2d(input_dim // compress_raito, eps=0.001, momentum=0.01), nn.ReLU())
        self.decoder = nn.Sequential(nn.Conv2d(input_dim // compress_raito, input_dim, kernel_size=3, stride=1, padding=1), nn.BatchNorm2d(input_dim, eps=0.001, momentum=0.01), nn.ReLU(), nn.Conv2d(input_dim, input_dim, kernel_size=3, stride=1, padding=1), nn.BatchNorm2d(input_dim, eps=0.001, momentum=0.01), nn.ReLU())

    def forward(self, x):
        x = self.encoder(x)
        x = self.decoder(x)
        return x

def forward(self, x):
    x = self.encoder(x)
    x = self.decoder(x)
    return x

class BaseTransformer(nn.Module):

    def __init__(self, args):
        super().__init__()
        dim = args['dim']
        depth = args['depth']
        heads = args['heads']
        dim_head = args['dim_head']
        mlp_dim = args['mlp_dim']
        dropout = args['dropout']
        max_cav = args['max_cav']
        self.encoder = BaseEncoder(dim, depth, heads, dim_head, mlp_dim, dropout)

    def forward(self, x, mask):
        output = self.encoder(x, mask)
        output = output[:, 0]
        return output

def forward(self, x, mask):
    output = self.encoder(x, mask)
    output = output[:, 0]
    return output

