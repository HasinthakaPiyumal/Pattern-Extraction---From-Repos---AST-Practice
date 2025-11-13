# Cluster 12

class NDCG(object):
    """Normalized discounted cumulative gain metric."""

    def __init__(self, k=1):
        self.topk = k

    def dcg_score(self, y_true, y_pred):
        order = np.argsort(y_pred)[::-1]
        y_true = np.take(y_true, order[:self.topk])
        gains = 2 ** y_true - 1
        discounts = np.log2(np.arange(len(y_true)) + 2)
        return np.sum(gains / discounts)

    def __call__(self, y_true, y_pred):
        idcg = self.dcg_score(y_true, y_true)
        dcg = self.dcg_score(y_true, y_pred)
        return dcg / (idcg + 1e-12)

def __call__(self, y_true, y_pred):
    idcg = self.dcg_score(y_true, y_true)
    dcg = self.dcg_score(y_true, y_pred)
    return dcg / (idcg + 1e-12)

