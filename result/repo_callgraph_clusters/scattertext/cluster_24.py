# Cluster 24

def y_axis_rescale(coords):
    return ((coords - 0.5) / np.abs(coords - 0.5).max() + 1) / 2

def generate_term_metadata(term_struct):
    if p_value_column + '_corr_x' in term_struct:
        x_p = term_struct[p_value_column + '_corr_x']
    elif p_value_column + '_x' in term_struct:
        x_p = term_struct[p_value_column + '_x']
    else:
        x_p = None
    if p_value_column + '_corr_y' in term_struct:
        y_p = term_struct[p_value_column + '_corr_y']
    elif p_value_column + '_y' in term_struct:
        y_p = term_struct[p_value_column + '_y']
    else:
        y_p = None
    if x_p is not None:
        x_p = min(x_p, 1.0 - x_p)
    if y_p is not None:
        y_p = min(y_p, 1.0 - y_p)
    x_d = term_struct[statistic_column + '_x']
    y_d = term_struct[statistic_column + '_y']
    tooltip = '%s: %s: %0.3f' % (x_tooltip_label, statistic_name, x_d)
    if x_p is not None:
        tooltip += '; p: %0.4f' % x_p
    tooltip += '<br/>'
    tooltip += '%s: %s: %0.3f' % (y_tooltip_label, statistic_name, y_d)
    if y_p is not None:
        tooltip += '; p: %0.4f' % y_p
    return {'tooltip': tooltip, 'color': pick_color(x_p, y_p, np.abs(x_d), np.abs(y_d))}

class BaseAssociationCompactor(object):

    def __init__(self, scorer=ScaledFScorePresetsNeg1To1, term_ranker=AbsoluteFrequencyRanker, use_non_text_features=False, target_category: Optional[str]=None):
        self.scorer = TermCategoryRanker(scorer, term_ranker, use_non_text_features, target_category)

    def set_use_non_text_features(self, use_non_text_features: bool) -> 'BaseAssociationCompactor':
        self.scorer = self.scorer.set_use_non_text_features(use_non_text_features)
        return self

    def _prune_higher_ranked_terms(self, term_doc_matrix, rank_df, rank):
        terms_to_remove = rank_df.index[np.isnan(rank_df[rank_df <= rank]).apply(lambda x: all(x), axis=1)]
        return self._remove_terms(term_doc_matrix, terms_to_remove)

    def _remove_terms(self, term_doc_matrix, terms_to_remove):
        return term_doc_matrix.remove_terms(terms_to_remove, non_text=self.scorer.use_non_text_features)

def __init__(self, scorer=ScaledFScorePresetsNeg1To1, term_ranker=AbsoluteFrequencyRanker, use_non_text_features=False, target_category: Optional[str]=None):
    self.scorer = TermCategoryRanker(scorer, term_ranker, use_non_text_features, target_category)

class TestAssociationCompactor(TestCase):

    def test_compact(self):
        term_doc_mat = get_hamlet_term_doc_matrix()
        new_tdm = AssociationCompactor(max_terms=213).compact(term_doc_mat)
        self.assertEqual(len(term_doc_mat.get_terms()), 26875)
        self.assertEqual(len(new_tdm.get_terms()), 213)

    def test_get_term_ranks(self):
        term_doc_mat = get_hamlet_term_doc_matrix()
        ranks = TermCategoryRanker().get_rank_df(term_doc_mat)
        self.assertEqual(len(ranks), term_doc_mat.get_num_terms())
        self.assertGreaterEqual(ranks.min().min(), 0)

    def test_compact_by_rank(self):
        term_doc_mat = get_hamlet_term_doc_matrix()
        compact_tdm4 = AssociationCompactorByRank(rank=4).compact(term_doc_mat)
        compact_tdm8 = AssociationCompactorByRank(rank=8).compact(term_doc_mat)
        self.assertLess(compact_tdm4.get_num_terms(), compact_tdm8.get_num_terms())
        self.assertLess(compact_tdm8.get_num_terms(), term_doc_mat.get_num_terms())

    def test_get_max_rank(self):
        term_doc_mat = get_hamlet_term_doc_matrix()
        self.assertEqual(TermCategoryRanker().get_max_rank(term_doc_mat), 322)

def test_get_max_rank(self):
    term_doc_mat = get_hamlet_term_doc_matrix()
    self.assertEqual(TermCategoryRanker().get_max_rank(term_doc_mat), 322)

class Dispersion(object):

    def __init__(self, corpus: Optional[TermDocMatrixWithoutCategories]=None, term_doc_mat: Optional[np.matrix]=None, non_text=False, use_categories_as_documents=False, tqdm=None, regressor=None, term_ranker: Optional[TermRanker]=None, vocabulary: Optional[List[str]]=None, add_smoothing_part: bool=False):
        """
        corpus, Optional ]TermDocMatrix type-object; if not present, pass an argument to the `term_doc_mat` parameter
        term_doc_mat, Optional[np.matrix]; use this term doc matrix
        non_text bool, default False; use metadata features
        use_categories_as_document, bool, default False; use categories in lieu of documents
        add_smoothing_part: add a part containing one of every terms

        From https://www.researchgate.net/publication/332120488_Analyzing_dispersion
        Stefan Th. Gries. Analyzing dispersion. April 2019. Practical handbook of corpus linguistics. Springer.

        Parts are considered documents, unless use_categories is True. Then categories are treated as parts.

        Term ranker is acttive is use_categories is True

        """
        "\n        following Gries' notation, for the following example:\n        b a m n i b e u p\n        b a s a t b e w q n\n        b c a g a b e s t a\n        b a g h a b e a a t\n        b a h a a b e a x a t\n\n        (1) l = 50 (the length of the corpus in words)\n        (2) n = 5 (the length of the corpus in parts)\n        (3) s = (0.18, 0.2, 0.2, 0.2, 0.22) (the percentages of the n corpus part sizes)\n        (4) f = 15 (the overall frequency of a in the corpus)\n        (5) v = (1, 2, 3, 4, 5) (the frequencies of a in each corpus part 1-n)\n        (6) p = (1/9, 2/10, 3/10, 4/10, 5 /11) (the percentages a makes up of each corpus part 1-n)\n        \n        Adapted from Burch: y is percentage of tokens which are a terms in a part   \n        "
        self.corpus = None
        self.use_metadata = non_text
        if corpus is None and term_doc_mat is None:
            raise Exception('Required non-None argument for corpus or term_doc_mat.')
        self.absent_vocab = []
        X = self.__get_X(corpus, non_text, term_doc_mat, term_ranker, use_categories_as_documents)
        if corpus:
            if vocabulary is not None:
                self.absent_vocab = [v for v in vocabulary if v not in set(corpus.get_terms(use_metadata=non_text))]
            if self.absent_vocab:
                X = hstack([X, np.zeros((X.shape[0], len(self.absent_vocab)))])
        if add_smoothing_part:
            X = vstack([X, np.ones((1, X.shape[1]))])
        part_sizes = X.sum(axis=1)
        self.l = X.sum().sum()
        self.n = X.shape[0]
        self.f = X.sum(axis=0)
        self.term_part_counts = X
        self.p_term_part = X.multiply(csc_matrix(1.0 / X.sum(axis=1)))
        self.prob_part = part_sizes / self.l
        self.tqdm = tqdm
        self.regressor = Lowess() if regressor is None else regressor

    def __get_X(self, corpus, non_text, term_doc_mat, term_ranker, use_categories):
        if term_doc_mat is not None:
            return term_doc_mat
        if corpus is not None:
            self.corpus = corpus
            if use_categories is True:
                if term_ranker is None:
                    term_ranker = AbsoluteFrequencyRanker
                term_ranker = term_ranker(term_doc_matrix=corpus).set_non_text(non_text=non_text)
                return csr_matrix(term_ranker.get_ranks('').values.T)
            else:
                X = corpus.get_term_doc_mat(non_text=non_text)
                return X
        raise Exception()

    def dispersion_range(self):
        """
        range: number of parts containing a
        """
        return (self.term_part_counts > 0).sum(axis=0).A1

    def sd_population(self):
        return np.sqrt(StandardScaler(with_mean=False).fit(self.term_part_counts).var_)

    def vc(self):
        """
        Direct quote from Gries (2019)
        A maybe more useful variant of this measure is its normalized version, the variation
        coefficient (vc, see (9)); the normalization consists of dividing sdpopulation by the mean frequency
        of the element in the corpus parts f/n:
        """
        ss = StandardScaler(with_mean=False).fit(self.term_part_counts)
        return np.sqrt(ss.var_) / ss.mean_

    def jullands_d(self):
        """
        Direct quote from Gries (2019)

        The version of Juilland's D that can handle differently large corpus parts is then computed
        as shown in (10). In order to accommodate the different sizes of the corpus parts, however, the
        variation coefficient is not computed using the observed frequencies v1-n (i.e. 1, 2, 3, 4, 5 in files
        1 to 5 respectively, see (5) above) but using the percentages in p1-n (i.e. how much of each corpus
        part is made up by the element in question, i.e. 1/9, 2/10, 3/10, 4/10, 5/11, see (6) above), which is what
        corrects for differently large corpus parts:
        """
        ss = StandardScaler(with_mean=False).fit(self.p_term_part)
        return 1 - np.sqrt(ss.var_) / ss.mean_ / np.sqrt(self.n - 1)

    def rosengrens(self):
        """
        Direct quote from Gries (2019)

        The version of Rosengren’s S that can handle differently large corpus parts is
        shown in (12). Each corpus part size’s in percent (in s) is multiplied with the
        frequencies of the element in question in each corpus part (in v1-n); of each product,
        one takes the square root, and those are summed up, that sum is squared, and divided
        by the overall frequency of the element in question in the corpus (f)"""
        vs = self.term_part_counts.multiply(self.prob_part)
        return np.power(np.sqrt(vs).sum(axis=0).A1, 2) * 1.0 / self.get_frequency()

    def dp(self):
        """
        Direct quote from Gries (2019)

        Finally, Gries (2008, 2010) and the follow-up by Lijffijt and Gries (2012)
        proposed a measure called DP (for deviation of proportions), which falls between
        1-min s (for an extremely even distribution) and 1 (for an extremely clumpy
        distribution) as well as a normalized version of DP, DPnorm, which falls between 0
        and 1, which are computed as shown in (13). For DP, one computes the differences
        between how much of the element in question is in each corpus file in percent on the
        one hand and the sizes of the corpus parts in percent on the other – i.e. the differences
        between observed and expected percentages. Then, one adds up the absolute values
        of those and multiplies by 0.5; the normalization then consists of dividing this values
        by the theoretically maximum value of DP given the number of corpus parts (in a
        way reminiscent of (11)"""
        return np.sum(np.abs(self.term_part_counts.multiply(1.0 / self.get_frequency()) - self.prob_part), axis=0).A1 / 2

    def dp_norm(self):
        return self.dp() / (1 - self.prob_part.min())

    def kl_divergence(self):
        """
        Direct quote from Gries (2019)
        The final measure to be discussed here is one that, as far as I can tell, has never
        been proposed as a measure of dispersion, but seems to me to be ideally suited to be
        one, namely the Kullback-Leibler (or KL-) divergence, a non-symmetric measure
        that quantifies how different one probability distribution (e.g., the distribution of
        all the occurrences of a across all corpus parts, i.e. v/f) is from another (e.g., the
        corpus part sizes s); the KL-divergence is computed as shown in (14) (with log2s of 167
        0 defined as 0):"""
        vf = self.term_part_counts.multiply(1.0 / self.f)
        vfs = vf.multiply(1.0 / self.prob_part)
        vfs.data = np.log(vfs.data) / np.log(2)
        return np.sum(vf.multiply(vfs), axis=0).A1

    def da(self):
        """
        Metric from Burch (2017).

        Brent Burch, Jesse Egbertb and Douglas Biber. Measuring Lexical Dispersion in Corpus Linguistics. JRDS. 2016.
        Article: https://journal.equinoxpub.com/JRDS/article/view/9480

        D_A = 1 - ((n * (n - 1))/2) * sum_{i in 0, n - 1} sum{j in i + 1, n} |v_i - v_j|/(2*mean(v))

        :return:
        """
        n = self.n
        constant = 1.0 / (n * (n - 1) / 2)
        ym = self.get_pct_of_term_in_part()
        it = range(self.term_part_counts.shape[1])
        if self.tqdm is not None:
            it = self.tqdm(it)
        da = []
        for word_i in it:
            y = ym.T[word_i]
            if type(y) != np.ndarray:
                y = y.todense().A1
            yt = np.tile(y, (n, 1))
            pairs_sum = np.sum(np.abs(yt - yt.T)) / 2
            da_score = 1 - pairs_sum * constant / (2 * y.mean())
            da.append(da_score)
        da_vec = np.array(da)
        da_vec[da_vec < 0] = 0
        return da_vec

    def get_pct_of_term_in_part(self) -> csr_matrix:
        C = self.term_part_counts
        D = self.term_part_counts.sum(axis=1).A1
        r, c = C.nonzero()
        rD_sp = csr_matrix(((1.0 / D)[r], (r, c)), shape=C.shape)
        return C.multiply(rD_sp)

    def dissemination(self) -> np.array:
        """
        Returns the dissemination metric D_w from Altmann et al. 2011

        Altmann EG, Pierrehumbert JB, Motter AE (2011) Niche as a Determinant of Word Fate in Online
        Groups. PLoS ONE 6(5): e19009. https://doi.org/10.1371/journal.pone.0019009.
        """
        U_w, Utilde_iw = self.__dissemination_components()
        return (U_w / Utilde_iw.sum(axis=0).A1).A1

    def delta_dissemination(self) -> np.array:
        """
        Returns a novel variation of dissemination metric D_w from Altmann et al. 2011
        where the expected dissemination is subtracted from the observed. This is more
        suited for plotting.
        """
        U_w, Utilde_iw = self.__dissemination_components()
        return (U_w - Utilde_iw.sum(axis=0).A1).A1

    def __dissemination_components(self):
        N_w = self.term_part_counts.sum(axis=0)
        U_w = (self.term_part_counts > 0).astype(int).sum(axis=0)
        m_i = self.term_part_counts.sum(axis=1)
        NA = self.term_part_counts.sum()
        f_w = N_w / NA
        Utilde_iw = 1 - np.exp(-1 * (m_i * f_w))
        return (U_w, Utilde_iw)

    def get_df(self, terms=None, include_da=False, no_freq_metrics: Optional[List]=None):
        if terms is None and self.corpus is not None:
            terms = self.get_names()
        freq = self.get_frequency()
        df_content = {'Frequency': freq, 'Range': self.dispersion_range(), 'SD': self.sd_population(), 'VC': self.vc(), "Juilland's D": self.jullands_d(), "Rosengren's S": self.rosengrens(), 'DP': self.dp(), 'DP norm': self.dp_norm(), 'KL-divergence': self.kl_divergence(), 'Dissemination': self.dissemination(), 'DeltaDissemination': self.delta_dissemination()}
        if include_da:
            df_content['DA'] = self.da()
        if terms is None:
            dispersion_df = pd.DataFrame(df_content)
        else:
            dispersion_df = pd.DataFrame(df_content, index=terms)
        if no_freq_metrics is not None:
            for metric in no_freq_metrics:
                dispersion_df = pd.merge(dispersion_df, dispersion_df.groupby('Frequency').apply(lambda gdf: pd.Series({'Low': gdf[metric].min(), 'Sup': gdf[metric].max()})), left_on='Frequency', right_index=True).assign(**{metric + '-nofreq': lambda df: ((df[metric] - df.Low) / (df.Sup - df.Low)).fillna(0.5)})
        return dispersion_df[lambda df: [c for c in df if c not in ['Low', 'Sups']]]

    def get_names(self):
        return self.corpus.get_terms(use_metadata=self.use_metadata) + self.absent_vocab

    def get_adjusted_metric(self, metric=None, freq=None):
        """
        Returns the difference between DA and the Lowess estimate of DP from frequency

        :param metric: Optional[np.array], metric to analyze, defaults to DP

        :param freq: Optional[np.array], Word frequencies
        :return: np.array, frequency-adjusted metric
        """
        if metric is None:
            observed = self.dp()
        elif metric == 'DA':
            observed = self.da()
        else:
            observed = self.get_df()[metric]
        if freq is None:
            freq = self.get_frequency()
        freq_est_metric = self.__fit_predict(freq, metric)
        return observed - freq_est_metric

    def get_adjusted_metric_df(self, metric: Optional[Union[str, np.array]]=None, freq: Optional[np.array]=None):
        """
        Returns the difference between the metric and the Lowess estimate of metric from frequency

        :param metric: Optional[np.array], metric to analyze, defaults to DP

        :param freq: Optional[np.array], Word frequencies
        :return: np.array, frequency-adjusted metric
        """
        if metric is None:
            metric = self.dp()
        elif metric == 'DA':
            metric = self.da()
        else:
            metric = self.get_df()[metric]
        if freq is None:
            freq = self.get_frequency()
        freq_est_metric = self.__fit_predict(freq, metric)
        adjusted_metric = metric - freq_est_metric
        return pd.DataFrame({'Frequency': freq, 'Metric': metric, 'Estimate': freq_est_metric, 'Residual': adjusted_metric}, index=self.get_names())

    def __fit_predict(self, freq: np.array, metric: np.array, regressor: Optional[object]=None) -> np.array:
        if regressor is None:
            regressor = self.regressor
        fit_regressor = self.regressor.fit(freq.reshape(-1, 1), metric)
        pred = fit_regressor.predict(freq.reshape(-1, 1))
        freq_est_metric = pred.T[0]
        return freq_est_metric

    def get_frequency(self):
        if len(self.f.shape) == 1:
            return self.f
        return self.f.A1

def da(self):
    """
        Metric from Burch (2017).

        Brent Burch, Jesse Egbertb and Douglas Biber. Measuring Lexical Dispersion in Corpus Linguistics. JRDS. 2016.
        Article: https://journal.equinoxpub.com/JRDS/article/view/9480

        D_A = 1 - ((n * (n - 1))/2) * sum_{i in 0, n - 1} sum{j in i + 1, n} |v_i - v_j|/(2*mean(v))

        :return:
        """
    n = self.n
    constant = 1.0 / (n * (n - 1) / 2)
    ym = self.get_pct_of_term_in_part()
    it = range(self.term_part_counts.shape[1])
    if self.tqdm is not None:
        it = self.tqdm(it)
    da = []
    for word_i in it:
        y = ym.T[word_i]
        if type(y) != np.ndarray:
            y = y.todense().A1
        yt = np.tile(y, (n, 1))
        pairs_sum = np.sum(np.abs(yt - yt.T)) / 2
        da_score = 1 - pairs_sum * constant / (2 * y.mean())
        da.append(da_score)
    da_vec = np.array(da)
    da_vec[da_vec < 0] = 0
    return da_vec

def produce_category_focused_pairplot(corpus, category, category_projector=CategoryProjector(projector=TruncatedSVD(20)), category_projection=None, **kwargs):
    """
    Produces a pair-plot which is focused on a single category.

    :param corpus: TermDocMatrix
    :param category: str, name of a category in the corpus
    :param category_projector: CategoryProjector, a factor analysis of the category/feature vector
    :param category_projection: CategoryProjection, None by default. If present, overrides category projector
    :param kwargs: remaining kwargs for produce_pairplot
    :return: str, HTML
    """
    category_num = corpus.get_categories().index(category)
    uncorrelated_components_projection = category_projection
    if category_projection is None:
        if 'use_metadata' in kwargs and kwargs['use_metadata']:
            uncorrelated_components_projection = category_projector.project_with_metadata(corpus)
        else:
            uncorrelated_components_projection = category_projector.project(corpus)
    distances = cosine_distances(uncorrelated_components_projection.get_category_embeddings().T)
    similarity_to_category_scores = -2 * (rankdata(distances[category_num]) - 0.5)
    uncorrelated_components = uncorrelated_components_projection.get_projection()
    least_correlated_dimension = min(([(np.abs(pearsonr(similarity_to_category_scores, uncorrelated_components.T[i])[0]), i)] for i in range(uncorrelated_components.shape[1])))[0][1]
    projection_to_plot = np.array([uncorrelated_components.T[least_correlated_dimension], similarity_to_category_scores]).T
    return produce_pairplot(corpus, initial_category=category, category_projection=uncorrelated_components_projection.use_alternate_projection(projection_to_plot), category_focused=True, **kwargs)

class ProjectionQuality:

    def __init__(self, min_radius=0, max_radius=np.sqrt(2)):
        self.min_radius = min_radius
        self.max_radius = max_radius

    def ripley_poisson_difference(self, points):
        try:
            from astropy.stats import RipleysKEstimator
        except:
            raise Exception('Please install astropy')
        r = np.linspace(self.min_radius, self.max_radius, 100)
        ripley = RipleysKEstimator(area=1.0, x_max=1.0, y_max=1.0, x_min=0.0, y_min=0.0)
        return np.sum(np.abs(ripley(points, r, mode='ripley') - ripley.poisson(r)))

def ripley_poisson_difference(self, points):
    try:
        from astropy.stats import RipleysKEstimator
    except:
        raise Exception('Please install astropy')
    r = np.linspace(self.min_radius, self.max_radius, 100)
    ripley = RipleysKEstimator(area=1.0, x_max=1.0, y_max=1.0, x_min=0.0, y_min=0.0)
    return np.sum(np.abs(ripley(points, r, mode='ripley') - ripley.poisson(r)))

def get_optimal_category_projection(corpus, n_dims=3, n_steps=10, projector=lambda n_terms, n_dims: CategoryProjector(selector=AssociationCompactor(n_terms, scorer=RankDifference), projector=PCA(n_dims)), optimizer: Optional[Callable]=None, term_counts: Optional[np.array]=None, verbose=False):
    min_dev = None
    best_k = None
    best_x = None
    best_y = None
    best_projector = None
    optimizer = ProjectionQuality().ripley_poisson_difference if optimizer is None else optimizer
    term_counts = np.power(2, np.linspace(np.log(corpus.get_num_categories()) / np.log(2), np.log(corpus.get_num_terms()) / np.log(2), n_steps)).astype(int) if term_counts is None else term_counts
    for k in term_counts:
        category_projector = projector(k, n_dims)
        category_projection = category_projector.project(corpus)
        for dim_1 in range(0, n_dims):
            for dim_2 in range(dim_1 + 1, n_dims):
                proj = category_projection.projection[:, [dim_1, dim_2]]
                scaled_proj = np.array([stretch_0_to_1(proj.T[0]), stretch_0_to_1(proj.T[1])]).T
                dev = optimizer(scaled_proj)
                category_projection.x_dim = dim_1
                category_projection.y_dim = dim_2
                tproj = category_projection.get_term_projection().values
                print(proj.shape)
                print(tproj.shape)
                scaled_tproj = np.array([stretch_0_to_1(tproj.T[0]), stretch_0_to_1(tproj.T[1])]).T
                tdev = optimizer(scaled_tproj)
                print(dev, tdev)
                best = False
                if min_dev is None or dev < min_dev:
                    min_dev = dev
                    best_k = k
                    best_projector = category_projector
                    best_x, best_y = (dim_1, dim_2)
                    best = True
                if verbose:
                    print(k, dim_1, dim_2, dev, best_k, best_x, best_y, min_dev, f'best={best}')
    if verbose:
        print(best_k, best_x, best_y)
    return best_projector.project(corpus, best_x, best_y)

def get_optimal_category_projection_by_rank(corpus, n_dims=2, n_steps=20, projector=lambda rank, n_dims: CategoryProjector(AssociationCompactorByRank(rank), projector=PCA(n_dims)), verbose=False):
    try:
        from astropy.stats import RipleysKEstimator
    except:
        raise Exception('Please install astropy')
    ripley = RipleysKEstimator(area=1.0, x_max=1.0, y_max=1.0, x_min=0.0, y_min=0.0)
    min_dev = None
    best_rank = None
    best_x = None
    best_y = None
    best_projector = None
    for rank in np.linspace(1, TermCategoryRanker().get_max_rank(corpus), n_steps):
        r = np.linspace(0, np.sqrt(2), 100)
        category_projector = projector(rank, n_dims)
        category_projection = category_projector.project(corpus)
        for dim_1 in range(0, n_dims):
            for dim_2 in range(dim_1 + 1, n_dims):
                proj = category_projection.projection[:, [dim_1, dim_2]]
                scaled_proj = np.array([stretch_0_to_1(proj.T[0]), stretch_0_to_1(proj.T[1])]).T
                dev = np.sum(np.abs(ripley(scaled_proj, r, mode='ripley') - ripley.poisson(r)))
                if min_dev is None or dev < min_dev:
                    min_dev = dev
                    best_rank = rank
                    best_projector = category_projector
                    best_x, best_y = (dim_1, dim_2)
                if verbose:
                    print('rank', rank, 'dims', dim_1, dim_2, 'K', dev)
                    print('     best rank', best_rank, 'dims', best_x, best_y, 'K', min_dev)
    if verbose:
        print(best_rank, best_x, best_y)
    return best_projector.project(corpus, best_x, best_y)

class CategoryProjectionBase(ABC):
    """

    """

    def _pseduo_init(self, category_corpus, category_counts, projection, x_dim=0, y_dim=1, term_projection=None):
        self.category_corpus = category_corpus
        self.category_counts = category_counts
        self.x_dim = x_dim
        self.y_dim = y_dim
        self.projection = projection
        self.term_projection = term_projection

    def project_with_alternative_dimensions(self, x_dim, y_dim):
        return CategoryProjection(self.category_corpus, self.category_counts, self.projection, x_dim, y_dim)

    def project_with_alternate_axes(self, x_axis=None, y_axis=None):
        if x_axis is None:
            x_axis = self._get_x_axis()
        if y_axis is None:
            y_axis = self._get_y_axis()
        return CategoryProjectionAlternateAxes(self.category_corpus, self.category_counts, self.projection, self.get_category_embeddings(), self.x_dim, self.y_dim, x_axis=x_axis, y_axis=y_axis)

    def get_pandas_projection(self):
        """

        :param x_dim: int
        :param y_dim: int
        :return: pd.DataFrame
        """
        to_ret = pd.DataFrame({'term': self.category_corpus.get_metadata(), 'x': self._get_x_axis(), 'y': self._get_y_axis()}).set_index('term')
        return to_ret

    def _get_x_axis(self):
        try:
            return self.projection.T[self.x_dim]
        except:
            return self.projection.T.loc[self.x_dim]

    def _get_y_axis(self):
        try:
            return self.projection.T[self.y_dim]
        except:
            try:
                return self.projection.T.loc[self.y_dim]
            except:
                import pdb
                pdb.set_trace()
                raise e

    def get_axes_labels(self, num_terms=5):
        df = self.get_term_projection()
        return {'right': list(df.sort_values(by='x', ascending=False).index[:num_terms]), 'left': list(df.sort_values(by='x', ascending=True).index[:num_terms]), 'top': list(df.sort_values(by='y', ascending=False).index[:num_terms]), 'bottom': list(df.sort_values(by='y', ascending=True).index[:num_terms])}

    def get_nearest_terms(self, num_terms: int=5) -> dict:
        return term_coordinates_to_halo(term_coordinates_df=self.get_term_projection(), num_terms=num_terms)

    def get_term_projection(self):
        if self.term_projection is None:
            dim_term = np.matmul(self.category_counts.values, self._get_x_y_projection())
        else:
            dim_term = self.term_projection
        df = pd.DataFrame(dim_term, index=self.category_corpus.get_terms(), columns=['x', 'y'])
        return df

    def _get_x_y_projection(self):
        return np.array([self._get_x_axis(), self._get_y_axis()]).T

    def get_projection(self):
        return self.projection

    @abstractmethod
    def use_alternate_projection(self, projection):
        pass

    @abstractmethod
    def get_category_embeddings(self):
        pass

    def get_corpus(self):
        return self.category_corpus

def project_with_alternative_dimensions(self, x_dim, y_dim):
    return CategoryProjection(self.category_corpus, self.category_counts, self.projection, x_dim, y_dim)

def project_with_alternate_axes(self, x_axis=None, y_axis=None):
    if x_axis is None:
        x_axis = self._get_x_axis()
    if y_axis is None:
        y_axis = self._get_y_axis()
    return CategoryProjectionAlternateAxes(self.category_corpus, self.category_counts, self.projection, self.get_category_embeddings(), self.x_dim, self.y_dim, x_axis=x_axis, y_axis=y_axis)

def get_pandas_projection(self):
    """

        :param x_dim: int
        :param y_dim: int
        :return: pd.DataFrame
        """
    to_ret = pd.DataFrame({'term': self.category_corpus.get_metadata(), 'x': self._get_x_axis(), 'y': self._get_y_axis()}).set_index('term')
    return to_ret

def _get_x_y_projection(self):
    return np.array([self._get_x_axis(), self._get_y_axis()]).T

class CategoryProjection(CategoryProjectionBase):

    def __init__(self, category_corpus, category_counts, projection, x_dim=0, y_dim=1, term_projection=None):
        self._pseduo_init(category_corpus, category_counts, projection, x_dim, y_dim, term_projection)

    def get_category_embeddings(self):
        return self.category_counts.values

    def use_alternate_projection(self, projection):
        return CategoryProjection(self.category_corpus, self.category_counts, projection, self.x_dim, self.y_dim)

def use_alternate_projection(self, projection):
    return CategoryProjection(self.category_corpus, self.category_counts, projection, self.x_dim, self.y_dim)

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

def get_category_embeddings(self):
    return self.doc2vec_model.project()

class RipleyKCategoryProjectorEvaluator(CategoryProjectionEvaluator):

    def __init__(self, max_distance=np.sqrt(2)):
        self.max_distance = max_distance

    def evaluate(self, category_projection):
        assert type(category_projection) == CategoryProjection
        try:
            from astropy.stats import RipleysKEstimator
        except:
            raise Exception('Please install astropy')
        assert issubclass(type(category_projection), CategoryProjectionBase)
        ripley_estimator = RipleysKEstimator(area=1.0, x_max=1.0, y_max=1.0, x_min=0.0, y_min=0.0)
        proj = category_projection.projection[:, [category_projection.x_dim, category_projection.y_dim]]
        scaled_proj = np.array([stretch_0_to_1(proj.T[0]), stretch_0_to_1(proj.T[1])]).T
        radii = np.linspace(0, self.max_distance, 1000)
        deviances = np.abs(ripley_estimator(scaled_proj, radii, mode='ripley') - ripley_estimator.poisson(radii))
        return np.trapz(deviances, x=radii)

def evaluate(self, category_projection):
    assert type(category_projection) == CategoryProjection
    try:
        from astropy.stats import RipleysKEstimator
    except:
        raise Exception('Please install astropy')
    assert issubclass(type(category_projection), CategoryProjectionBase)
    ripley_estimator = RipleysKEstimator(area=1.0, x_max=1.0, y_max=1.0, x_min=0.0, y_min=0.0)
    proj = category_projection.projection[:, [category_projection.x_dim, category_projection.y_dim]]
    scaled_proj = np.array([stretch_0_to_1(proj.T[0]), stretch_0_to_1(proj.T[1])]).T
    radii = np.linspace(0, self.max_distance, 1000)
    deviances = np.abs(ripley_estimator(scaled_proj, radii, mode='ripley') - ripley_estimator.poisson(radii))
    return np.trapz(deviances, x=radii)

class CategoryProjector(CategoryProjectorBase):

    def __init__(self, weighter=LengthNormalizer(), normalizer=StandardScaler(), selector=AssociationCompactor(1000, RankDifference), projector=PCA(2), fit_transform_kwargs=None, use_metadata=False):
        """

        :param weighter: instance of an sklearn class with fit_transform to weight X category corpus.
        :param normalizer: instance of an sklearn class with fit_transform to normalize term X category corpus.
        :param selector: instance of a compactor class, if None, no compaction will be done.
        :param projector: instance an sklearn class with fit_transform
        :param fit_transform_kwargs: optional, dict of kwargs to fit_transform
        :param use_metadata: bool, use metadata features
        """
        self.weighter_ = weighter
        self.normalizer_ = normalizer
        self.selector_ = selector
        self.projector_ = projector
        self.fit_transform_kwargs_ = {} if fit_transform_kwargs is None else fit_transform_kwargs
        self.use_metadata_ = use_metadata

    def use_metadata(self) -> 'CategoryProjector':
        self.use_metadata_ = True
        return self

    def get_category_embeddings(self, category_corpus):
        raw_category_counts = self._get_raw_category_counts(category_corpus)
        weighted_counts = self.weight(raw_category_counts)
        normalized_counts = self.normalize(weighted_counts)
        if type(normalized_counts) is not pd.DataFrame:
            normalized_counts = pd.DataFrame(normalized_counts.todense() if scipy.sparse.issparse(normalized_counts) else normalized_counts, columns=raw_category_counts.columns, index=raw_category_counts.index)
        return normalized_counts

    def _get_raw_category_counts(self, category_corpus):
        return category_corpus.get_freq_df(label_append='')

    def weight(self, category_counts):
        if self.weighter_ is None:
            return category_counts
        return self.weighter_.fit_transform(category_counts)

    def normalize(self, weighted_category_counts):
        if self.normalizer_ is not None:
            normalized_vals = self.normalizer_.fit_transform(weighted_category_counts)
            if issparse(normalized_vals):
                return normalized_vals
            if not isinstance(normalized_vals, DataFrame):
                return DataFrame(data=normalized_vals, columns=weighted_category_counts.columns, index=weighted_category_counts.index)
            else:
                return normalized_vals
        return weighted_category_counts

    def select(self, corpus):
        if self.selector_ is None:
            return corpus
        if self.use_metadata_:
            self.selector_ = self.selector_.set_use_non_text_features(self.use_metadata_)
        return corpus.select(self.selector_, non_text=self.use_metadata_)

    def _project_category_corpus(self, category_corpus, x_dim=0, y_dim=1):
        normalized_counts = self.get_category_embeddings(category_corpus)
        proj = self.projector_.fit_transform(normalized_counts.T, **self.fit_transform_kwargs_)
        return CategoryProjection(category_corpus, normalized_counts, proj, x_dim=x_dim, y_dim=y_dim)

    def _get_category_metadata_corpus(self, corpus):
        return self.select(corpus).use_categories_as_metadata()

    def _get_category_metadata_corpus_and_replace_terms(self, corpus):
        return self.select(corpus).use_categories_as_metadata_and_replace_terms()

def __init__(self, weighter=LengthNormalizer(), normalizer=StandardScaler(), selector=AssociationCompactor(1000, RankDifference), projector=PCA(2), fit_transform_kwargs=None, use_metadata=False):
    """

        :param weighter: instance of an sklearn class with fit_transform to weight X category corpus.
        :param normalizer: instance of an sklearn class with fit_transform to normalize term X category corpus.
        :param selector: instance of a compactor class, if None, no compaction will be done.
        :param projector: instance an sklearn class with fit_transform
        :param fit_transform_kwargs: optional, dict of kwargs to fit_transform
        :param use_metadata: bool, use metadata features
        """
    self.weighter_ = weighter
    self.normalizer_ = normalizer
    self.selector_ = selector
    self.projector_ = projector
    self.fit_transform_kwargs_ = {} if fit_transform_kwargs is None else fit_transform_kwargs
    self.use_metadata_ = use_metadata

def _project_category_corpus(self, category_corpus, x_dim=0, y_dim=1):
    normalized_counts = self.get_category_embeddings(category_corpus)
    proj = self.projector_.fit_transform(normalized_counts.T, **self.fit_transform_kwargs_)
    return CategoryProjection(category_corpus, normalized_counts, proj, x_dim=x_dim, y_dim=y_dim)

class Doc2VecCategoryProjector(CategoryProjectorBase):

    def __init__(self, doc2vec_builder=None, projector=PCA(2)):
        """

        :param doc2vec_builder: Doc2VecBuilder, optional
            If None, a default model will be used
        :param projector: object
            Has fit_transform method
        """
        if doc2vec_builder is None:
            try:
                import gensim
            except:
                raise Exception('Please install gensim before using Doc2VecCategoryProjector/')
            self.doc2vec_builder = Doc2VecBuilder(gensim.models.Doc2Vec(vector_size=100, window=5, min_count=5, workers=6, alpha=0.025, min_alpha=0.025, epochs=50))
        else:
            assert type(doc2vec_builder) == Doc2VecBuilder
            self.doc2vec_builder = doc2vec_builder
        self.projector = projector

    def _project_category_corpus(self, corpus, x_dim=0, y_dim=1):
        try:
            import gensim
        except:
            raise Exception('Please install gensim before using Doc2VecCategoryProjector/')
        category_corpus = corpus.use_categories_as_metadata()
        category_counts = corpus.get_term_freq_df('')
        self.doc2vec_builder.train(corpus)
        proj = self.projector.fit_transform(self.doc2vec_builder.project())
        return CategoryProjectionWithDoc2Vec(category_corpus, category_counts, proj, x_dim=x_dim, y_dim=y_dim, doc2vec_model=self.doc2vec_builder)

    def _get_category_metadata_corpus(self, corpus):
        return corpus.use_categories_as_metadata()

    def _get_category_metadata_corpus_and_replace_terms(self, corpus):
        return corpus.use_categories_as_metadata_and_replace_terms()

    def get_category_embeddings(self, corpus):
        return self.doc2vec_builder.project()

def get_category_embeddings(self, corpus):
    return self.doc2vec_builder.project()

def sign(a: np.array) -> np.array:
    return np.nan_to_num(a / np.abs(a), 0)

