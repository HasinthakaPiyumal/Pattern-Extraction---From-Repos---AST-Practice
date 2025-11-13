# Cluster 48

class MockWord2Vec:

    def __init__(self, vocab):
        self.wv = WV(vocab)
        self.corpus_count = 5

    def train(self, *args, **kwargs):
        pass

    def build_vocab(self, *args):
        pass

    def __getitem__(self, item):
        assert item in self.wv.key_to_index.keys()
        return np.zeros(30)

def __init__(self, vocab):
    self.wv = WV(vocab)
    self.corpus_count = 5

