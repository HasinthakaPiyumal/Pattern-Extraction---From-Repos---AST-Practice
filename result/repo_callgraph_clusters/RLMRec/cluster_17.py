# Cluster 17

class SvdDecomposition(nn.Module):
    """ Utilize SVD to decompose matrix (used in LightGCL)
    """

    def __init__(self, svd_q):
        super(SvdDecomposition, self).__init__()
        self.svd_q = svd_q

    def forward(self, adj):
        """
        :param adj: torch sparse matrix
        :return: matrices obtained by SVD decomposition
        """
        svd_u, s, svd_v = t.svd_lowrank(adj, q=self.svd_q)
        u_mul_s = svd_u @ t.diag(s)
        v_mul_s = svd_v @ t.diag(s)
        del s
        return (svd_u.T, svd_v.T, u_mul_s, v_mul_s)

def forward(self, adj):
    """
        :param adj: torch sparse matrix
        :return: matrices obtained by SVD decomposition
        """
    svd_u, s, svd_v = t.svd_lowrank(adj, q=self.svd_q)
    u_mul_s = svd_u @ t.diag(s)
    v_mul_s = svd_v @ t.diag(s)
    del s
    return (svd_u.T, svd_v.T, u_mul_s, v_mul_s)

