# Cluster 55

class CategoryProjectorBase(object):

    def project(self, term_doc_mat, x_dim=0, y_dim=1):
        """
        Returns a projection of the categories

        :param term_doc_mat: a TermDocMatrix
        :return: CategoryProjection
        """
        return self._project_category_corpus(self._get_category_metadata_corpus(term_doc_mat), x_dim, y_dim)

    def project_with_metadata(self, term_doc_mat, x_dim=0, y_dim=1):
        """
        Returns a projection of the

        :param term_doc_mat: a TermDocMatrix
        :return: CategoryProjection
        """
        return self._project_category_corpus(self._get_category_metadata_corpus_and_replace_terms(term_doc_mat), x_dim, y_dim)

    def _project_category_corpus(self, category_corpus, x_dim=0, y_dim=1):
        raise NotImplementedError()

    def _get_category_metadata_corpus(self, corpus):
        raise NotImplementedError()

    def _get_category_metadata_corpus_and_replace_terms(self, corpus):
        raise NotImplementedError()

    def get_category_embeddings(self, corpus):
        """
        :param corpus: TermDocMatrix

        :return: np.array, matrix of (num categories, embedding dimension) dimensions
        """
        raise NotImplementedError()

def project(self, term_doc_mat, x_dim=0, y_dim=1):
    """
        Returns a projection of the categories

        :param term_doc_mat: a TermDocMatrix
        :return: CategoryProjection
        """
    return self._project_category_corpus(self._get_category_metadata_corpus(term_doc_mat), x_dim, y_dim)

def project_with_metadata(self, term_doc_mat, x_dim=0, y_dim=1):
    """
        Returns a projection of the

        :param term_doc_mat: a TermDocMatrix
        :return: CategoryProjection
        """
    return self._project_category_corpus(self._get_category_metadata_corpus_and_replace_terms(term_doc_mat), x_dim, y_dim)

