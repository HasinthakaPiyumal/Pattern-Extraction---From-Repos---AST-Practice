# Cluster 2

def T2S(T):
    S = abs(T / (1 + T ** 2) ** 0.5)
    return S

def T2C(T):
    C = abs(1 / (1 + T ** 2) ** 0.5)
    return C

