# Cluster 20

class Hourglass(nn.Module):
    """
    Hourglass architecture.
    """

    def __init__(self, block_expansion, in_features, out_features, num_blocks=3, max_features=256, temporal=False):
        super(Hourglass, self).__init__()
        self.encoder = Encoder(block_expansion, in_features, num_blocks, max_features, temporal=temporal)
        self.decoder = Decoder(block_expansion, in_features, out_features, num_blocks, max_features, temporal=temporal)

    def forward(self, x):
        return self.decoder(self.encoder(x))

def forward(self, x):
    return self.decoder(self.encoder(x))

