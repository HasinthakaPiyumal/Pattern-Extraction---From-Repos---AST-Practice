# Cluster 58

class ScoreBalancer(object):

    @staticmethod
    def balance_scores(cat_scores, not_cat_scores):
        scores = ScoreBalancer.balance_scores_and_dont_scale(cat_scores, not_cat_scores)
        return ScoreBalancer._zero_centered_scale(scores)

    @staticmethod
    def balance_scores_and_dont_scale(cat_scores, not_cat_scores):
        """
        median = np.median(cat_scores)
        scores = np.zeros(len(cat_scores)).astype(np.float)
        scores[cat_scores > median] = cat_scores[cat_scores > median]
        not_cat_mask = cat_scores < median if median != 0 else cat_scores <= median
        scores[not_cat_mask] = -not_cat_scores[not_cat_mask]
        """
        scores = np.zeros(len(cat_scores)).astype(np.float64)
        scores[cat_scores > not_cat_scores] = cat_scores[cat_scores > not_cat_scores]
        scores[cat_scores < not_cat_scores] = -not_cat_scores[cat_scores < not_cat_scores]
        return scores

    @staticmethod
    def _zero_centered_scale(ar):
        ar[ar > 0] = ScoreBalancer._scale(ar[ar > 0])
        ar[ar < 0] = -ScoreBalancer._scale(-ar[ar < 0])
        return (ar + 1) / 2.0

    @staticmethod
    def _scale(ar):
        if len(ar) == 0:
            return ar
        if ar.min() == ar.max():
            return np.full(len(ar), 0.5)
        return (ar - ar.min()) / (ar.max() - ar.min())

@staticmethod
def _zero_centered_scale(ar):
    ar[ar > 0] = ScoreBalancer._scale(ar[ar > 0])
    ar[ar < 0] = -ScoreBalancer._scale(-ar[ar < 0])
    return (ar + 1) / 2.0

