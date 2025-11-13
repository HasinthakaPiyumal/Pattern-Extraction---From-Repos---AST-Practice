# Cluster 54

class CategoryProjection(CategoryProjectionBase):

    def __init__(self, category_corpus, category_counts, projection, x_dim=0, y_dim=1, term_projection=None):
        self._pseduo_init(category_corpus, category_counts, projection, x_dim, y_dim, term_projection)

    def get_category_embeddings(self):
        return self.category_counts.values

    def use_alternate_projection(self, projection):
        return CategoryProjection(self.category_corpus, self.category_counts, projection, self.x_dim, self.y_dim)

def __init__(self, category_corpus, category_counts, projection, x_dim=0, y_dim=1, term_projection=None):
    self._pseduo_init(category_corpus, category_counts, projection, x_dim, y_dim, term_projection)

class CategoryProjectionWithDoc2Vec(CategoryProjectionBase):

    def __init__(self, category_corpus, category_counts, projection, x_dim=0, y_dim=1, doc2vec_model=None, term_projection=None):
        self.doc2vec_model = doc2vec_model
        self._pseduo_init(category_corpus, category_counts, projection, x_dim, y_dim, term_projection)

    def project_with_alternative_dimensions(self, x_dim, y_dim):
        return CategoryProjectionWithDoc2Vec(self.category_corpus, self.category_counts, self.projection, x_dim, y_dim, doc2vec_model=self.doc2vec_model)

    def get_category_embeddings(self):
        return self.doc2vec_model.project()

    def use_alternate_projection(self, projection):
        return CategoryProjectionWithDoc2Vec(self.category_corpus, self.category_counts, projection, self.x_dim, self.y_dim, doc2vec_model=self.doc2vec_model)

def __init__(self, category_corpus, category_counts, projection, x_dim=0, y_dim=1, doc2vec_model=None, term_projection=None):
    self.doc2vec_model = doc2vec_model
    self._pseduo_init(category_corpus, category_counts, projection, x_dim, y_dim, term_projection)

class CategoryProjectionAlternateAxes(CategoryProjectionBase):

    def __init__(self, category_corpus, category_counts, projection, category_embeddings, x_dim=0, y_dim=1, x_axis=None, y_axis=None):
        self._pseduo_init(category_corpus, category_counts, projection, x_dim=x_dim, y_dim=y_dim)
        self.x_axis_ = x_axis
        self.y_axis_ = y_axis
        self.category_embeddings_ = category_embeddings

    def get_category_embeddings(self):
        return self.category_embeddings_

    def _get_x_axis(self):
        return self.x_axis_

    def _get_y_axis(self):
        return self.y_axis_

def __init__(self, category_corpus, category_counts, projection, category_embeddings, x_dim=0, y_dim=1, x_axis=None, y_axis=None):
    self._pseduo_init(category_corpus, category_counts, projection, x_dim=x_dim, y_dim=y_dim)
    self.x_axis_ = x_axis
    self.y_axis_ = y_axis
    self.category_embeddings_ = category_embeddings

