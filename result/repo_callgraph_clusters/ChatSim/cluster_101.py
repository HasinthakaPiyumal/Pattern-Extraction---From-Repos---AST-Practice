# Cluster 101

class ClassEmbedder(nn.Module):

    def __init__(self, embed_dim, n_classes=1000, key='class'):
        super().__init__()
        self.key = key
        self.embedding = nn.Embedding(n_classes, embed_dim)

    def forward(self, batch, key=None):
        if key is None:
            key = self.key
        c = batch[key][:, None]
        c = self.embedding(c)
        return c

def forward(self, batch, key=None):
    if key is None:
        key = self.key
    c = batch[key][:, None]
    c = self.embedding(c)
    return c

