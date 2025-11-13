# Cluster 35

class Doc(object):

    def __init__(self, sents, raw):
        self.sents = sents
        self.string = raw
        self.text = raw

    def __str__(self):
        return '\n'.join((str(sent) for sent in self.sents))

    def __repr__(self):
        return self.__str__()

    def __iter__(self):
        for sent in self.sents:
            for tok in sent:
                yield tok

def __repr__(self):
    return self.__str__()

