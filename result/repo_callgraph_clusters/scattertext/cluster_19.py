# Cluster 19

class DeployedClassifierFactory:

    def __init__(self, term_doc_matrix, term_doc_matrix_factory, category, nlp=None):
        """This is a class that enables one to train and save a classification model.

		Parameters
		----------
		term_doc_matrix : TermDocMatrix
		term_doc_matrix_factory : TermDocMatrixFactory
		category : str
			Category name
		nlp : spacy parser
		"""
        self._term_doc_matrix = term_doc_matrix
        self._term_doc_matrix_factory = term_doc_matrix_factory
        assert term_doc_matrix_factory._nlp is None
        assert term_doc_matrix_factory.category_text_iter is None
        self._category = category
        self._clf = None
        self._proba = None

    def passive_aggressive_train(self):
        """Trains passive aggressive classifier

		"""
        self._clf = PassiveAggressiveClassifier(n_iter=50, C=0.2, n_jobs=-1, random_state=0)
        self._clf.fit(self._term_doc_matrix._X, self._term_doc_matrix._y)
        y_dist = self._clf.decision_function(self._term_doc_matrix._X)
        pos_ecdf = ECDF(y_dist[y_dist >= 0])
        neg_ecdf = ECDF(y_dist[y_dist <= 0])

        def proba_function(distance_from_hyperplane):
            if distance_from_hyperplane > 0:
                return pos_ecdf(distance_from_hyperplane) / 2.0 + 0.5
            elif distance_from_hyperplane < 0:
                return pos_ecdf(distance_from_hyperplane) / 2.0
            return 0.5
        self._proba = proba_function
        return self

    def build(self):
        """Builds Depoyed Classifier
		"""
        if self._clf is None:
            raise NeedToTrainExceptionBeforeDeployingException()
        return DeployedClassifier(self._category, self._term_doc_matrix._category_idx_store, self._term_doc_matrix._term_idx_store, self._term_doc_matrix_factory)

def build(self):
    """Builds Depoyed Classifier
		"""
    if self._clf is None:
        raise NeedToTrainExceptionBeforeDeployingException()
    return DeployedClassifier(self._category, self._term_doc_matrix._category_idx_store, self._term_doc_matrix._term_idx_store, self._term_doc_matrix_factory)

