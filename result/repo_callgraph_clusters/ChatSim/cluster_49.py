# Cluster 49

class PatchEmbed(nn.Module):

    def __init__(self, in_chans, embed_dim, resolution, activation):
        super().__init__()
        img_size: Tuple[int, int] = to_2tuple(resolution)
        self.patches_resolution = (img_size[0] // 4, img_size[1] // 4)
        self.num_patches = self.patches_resolution[0] * self.patches_resolution[1]
        self.in_chans = in_chans
        self.embed_dim = embed_dim
        n = embed_dim
        self.seq = nn.Sequential(Conv2d_BN(in_chans, n // 2, 3, 2, 1), activation(), Conv2d_BN(n // 2, n, 3, 2, 1))

    def forward(self, x):
        return self.seq(x)

def forward(self, x):
    return self.seq(x)

