# Cluster 53

class LadderRamp:

    def __init__(self, start_iters, values):
        self.start_iters = start_iters
        self.values = values
        assert len(values) == len(start_iters) + 1, (len(values), len(start_iters))

    def __call__(self, i):
        segment_i = bisect.bisect_right(self.start_iters, i)
        return self.values[segment_i]

def __call__(self, i):
    segment_i = bisect.bisect_right(self.start_iters, i)
    return self.values[segment_i]

class LadderRamp:

    def __init__(self, start_iters, values):
        self.start_iters = start_iters
        self.values = values
        assert len(values) == len(start_iters) + 1, (len(values), len(start_iters))

    def __call__(self, i):
        segment_i = bisect.bisect_right(self.start_iters, i)
        return self.values[segment_i]

def __call__(self, i):
    segment_i = bisect.bisect_right(self.start_iters, i)
    return self.values[segment_i]

