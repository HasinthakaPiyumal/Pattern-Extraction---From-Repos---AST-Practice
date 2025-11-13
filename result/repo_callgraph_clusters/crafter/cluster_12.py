# Cluster 12

class staticproperty:

    def __init__(self, function):
        self.function = function

    def __get__(self, instance, owner=None):
        return self.function()

def __get__(self, instance, owner=None):
    return self.function()

