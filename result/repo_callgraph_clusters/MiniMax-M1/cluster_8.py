# Cluster 8

class GLU(nn.Module):

    def __init__(self, d1, d2, bias=False):
        super().__init__()
        self.l1 = nn.Linear(d1, d2, bias=bias)
        self.l2 = nn.Linear(d1, d2, bias=bias)
        self.l3 = nn.Linear(d2, d1, bias=bias)

    def forward(self, x):
        o1 = self.l1(x)
        o2 = self.l2(x)
        output = o1 * o2
        output = self.l3(output)
        return output

def forward(self, x):
    o1 = self.l1(x)
    o2 = self.l2(x)
    output = o1 * o2
    output = self.l3(output)
    return output

