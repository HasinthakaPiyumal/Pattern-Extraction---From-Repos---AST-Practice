# Cluster 19

class OrderedSet(Set):

    def __init__(self, iterable=()):
        self.d = OrderedDict.fromkeys(iterable)

    def __len__(self):
        return len(self.d)

    def __contains__(self, element):
        return element in self.d

    def __iter__(self):
        return iter(self.d)

def __init__(self, iterable=()):
    self.d = OrderedDict.fromkeys(iterable)

