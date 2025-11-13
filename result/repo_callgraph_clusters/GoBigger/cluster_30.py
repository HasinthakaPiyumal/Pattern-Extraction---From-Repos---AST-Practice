# Cluster 30

class PositionEncoder(nn.Module):

    def __init__(self, num_embeddings, embedding_dim=None):
        super(PositionEncoder, self).__init__()
        self.n_position = num_embeddings
        self.embedding_dim = self.n_position if embedding_dim is None else embedding_dim
        self.position_enc = nn.Embedding.from_pretrained(self.position_encoding_init(self.n_position, self.embedding_dim), freeze=True, padding_idx=None)

    @staticmethod
    def position_encoding_init(n_position, embedding_dim):
        """ Init the sinusoid position encoding table """
        position_enc = np.array([[pos / np.power(10000, 2 * (j // 2) / embedding_dim) for j in range(embedding_dim)] for pos in range(n_position)])
        position_enc[:, 0::2] = np.sin(position_enc[:, 0::2])
        position_enc[:, 1::2] = np.cos(position_enc[:, 1::2])
        return torch.from_numpy(position_enc).type(torch.FloatTensor)

    def forward(self, x: torch.Tensor):
        return self.position_enc(x)

def forward(self, x: torch.Tensor):
    return self.position_enc(x)

