# Cluster 0

class EmbedDrop(nn.Module):
    """ Drop embeddings by nn.Dropout
    """

    def __init__(self, p=0.2):
        super(EdgeDrop, self).__init__()
        self.dropout = nn.Dropout(p=p)

    def forward(self, embeds):
        """
        :param embeds: embedding matrix
        :return: embedding matrix after dropping
        """
        embeds = self.dropout(embeds)
        return embeds

def forward(self, embeds):
    """
        :param embeds: embedding matrix
        :return: embedding matrix after dropping
        """
    embeds = self.dropout(embeds)
    return embeds

