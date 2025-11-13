# Cluster 9

def zero_centered_scale(ar):
    ar[ar > 0] = scale(ar[ar > 0])
    ar[ar < 0] = -scale(-ar[ar < 0])
    return (ar + 1) / 2.0

def zero_centered_scale(ar):
    ar[ar > 0] = scale(ar[ar > 0])
    ar[ar < 0] = -scale(-ar[ar < 0])
    return (ar + 1) / 2.0

def large_int_format(x):
    num = round_downer(x)
    if 1000000000 <= num:
        return str(num // 1000000000) + 'b'
    elif 1000000 <= num < 1000000000:
        return str(num // 1000000) + 'mm'
    elif 1000 <= num < 1000000:
        return str(num // 1000) + 'k'
    else:
        return str(num)

class ScatterChart:

    def __init__(self, term_doc_matrix, verbose=False, **kwargs):
        """
        Parameters
        ----------
        term_doc_matrix: term document matrix to create chart from

        Remaining parameters are from ScatterChartData
        """
        self.term_doc_matrix = term_doc_matrix
        self.scatterchartdata = ScatterChartData(**kwargs)
        self.x_coords = None
        self.y_coords = None
        self.original_x = None
        self.original_y = None
        self._rescale_x = None
        self._rescale_y = None
        self.used = False
        self.metadata_term_lists = None
        self.metadata_descriptions = None
        self.term_colors = None
        self.hidden_terms = None
        self.category_scores = None
        self.verbose = verbose

    def inject_metadata_term_lists(self, term_dict):
        """
        Inserts dictionary of meta data terms into object.

        Parameters
        ----------
        term_dict: dict {metadataname: [term1, term2, ....], ...}

        Returns
        -------
        self: ScatterChart
        """
        check_topic_model_string_format(term_dict)
        if not self.term_doc_matrix.metadata_in_use():
            raise TermDocMatrixHasNoMetadataException('No metadata is present in the term document matrix')
        self.metadata_term_lists = term_dict
        return self

    def inject_category_scores(self, category_scores: Union[np.array, List[List[float]]]) -> Self:
        if type(category_scores) == np.array:
            category_scores = category_scores.tolist()
        if not len(category_scores) == self.term_doc_matrix.get_num_categories():
            raise Exception('Number of rows in category scores must be the number of categories in corpus')
        if not all((len(scores) == self.term_doc_matrix.get_num_terms(non_text=self.scatterchartdata.use_non_text_features) for scores in category_scores)):
            raise Exception('Number of columns in category scores must be the number of terms or metadata in corpus')
        self.category_scores = category_scores
        return self

    def inject_metadata_descriptions(self, term_dict):
        """
        Inserts a set of descriptions of meta data terms.  These will be displayed
        below the scatter plot when a meta data term is clicked. All keys in the term dict
        must occur as meta data.

        Parameters
        ----------
        term_dict: dict {metadataname: str: 'explanation to insert', ...}

        Returns
        -------
        self: ScatterChart
        """
        assert type(term_dict) == dict
        if not self.term_doc_matrix.metadata_in_use():
            raise TermDocMatrixHasNoMetadataException('No metadata is present in the term document matrix')
        if sys.version_info[0] == 2:
            assert set([type(v) for v in term_dict.values()]) - set([str, unicode]) == set()
        else:
            assert set([type(v) for v in term_dict.values()]) - set([str]) == set()
        self.metadata_descriptions = term_dict
        return self

    def inject_term_colors(self, term_to_color_dict):
        """

        :param term_to_color_dict: dict, mapping a term to a color
        :return: self
        """
        self.term_colors = term_to_color_dict

    def inject_coordinates(self, x_coords, y_coords, rescale_x=None, rescale_y=None, original_x=None, original_y=None):
        """
        Inject custom x and y coordinates for each term into chart.

        Parameters
        ----------
        x_coords: array-like
            positions on x-axis \\in [0,1]
        y_coords: array-like
            positions on y-axis \\in [0,1]
        rescale_x: lambda list[0,1]: list[0,1], default identity
            Rescales x-axis after filtering
        rescale_y: lambda list[0,1]: list[0,1], default identity
            Rescales y-axis after filtering
        original_x : array-like, optional
            Original, unscaled x-values.  Defaults to x_coords
        original_y : array-like, optional
            Original, unscaled y-values.  Defaults to y_coords
        Returns
        -------
        self: ScatterChart

        """
        self._verify_coordinates(x_coords, 'x')
        self._verify_coordinates(y_coords, 'y')
        self.x_coords = x_coords
        self.y_coords = y_coords
        self._rescale_x = rescale_x
        self._rescale_y = rescale_y
        self.original_x = x_coords if original_x is None else original_x
        self.original_y = y_coords if original_y is None else original_y

    def _verify_coordinates(self, coords, name):
        if self.scatterchartdata.use_non_text_features and len(coords) != len(self.term_doc_matrix.get_metadata()):
            raise CoordinatesNotRightException('Length of %s_coords must be the same as the number of non-text features in the term_doc_matrix.' % name)
        if not self.scatterchartdata.use_non_text_features and len(coords) != self.term_doc_matrix.get_num_terms():
            raise CoordinatesNotRightException('Length of %s_coords must be the same as the number of terms in the term_doc_matrix.' % name)
        if max(coords) > 1:
            raise CoordinatesNotRightException('Max value of %s_coords must be <= 1.' % name)
        if min(coords) < 0:
            raise CoordinatesNotRightException('Min value of %s_coords must be >= 0.' % name)

    def hide_terms(self, terms):
        """
        Mark terms which won't be displayed in the visualization.

        :param terms: iter[str]
            Terms to mark as hidden.
        :return: ScatterChart
        """
        self.hidden_terms = set(terms)
        return self

    def to_dict(self, category, category_name=None, not_category_name=None, scores=None, transform=percentile_alphabetical, title_case_names=False, not_categories=None, neutral_categories=None, extra_categories=None, background_scorer=None, use_offsets=False, **kwargs):
        """

        Parameters
        ----------
        category : str
            Category to annotate.  Exact value of category.
        category_name : str, optional
            Name of category which will appear on web site. Default None is same as category.
        not_category_name : str, optional
            Name of ~category which will appear on web site. Default None is same as "not " + category.
        scores : np.array, optional
            Scores to use for coloring.  Defaults to None, or RankDifference scores
        transform : function, optional
            Function for ranking terms.  Defaults to scattertext.Scalers.percentile_lexicographic.
        title_case_names : bool, default False
          Title case category name and no-category name?
        not_categories : list, optional
            List of categories to use as "not category".  Defaults to all others.
        neutral_categories : list, optional
            List of categories to use as neutral.  Defaults [].
        extra_categories : list, optional
            List of categories to use as extra.  Defaults [].
        background_scorer : CharacteristicScorer, optional
            Used for bg scores

        Returns
        -------
        Dictionary that encodes the scatter chart
        information. The dictionary can be dumped as a json document, and
        used in scattertext.html
         {info: {category_name: ..., not_category_name},
          data: [{term:,
                  x:frequency [0-1],
                  y:frequency [0-1],
                  ox: score,
                  oy: score,
                  s: score,
                  os: original score,
                  p: p-val,
                  cat25k: freq per 25k in category,
                  cat: count in category,
                  ncat: count in non-category,
                  catdocs: [docnum, ...],
                  ncatdocs: [docnum, ...]
                  ncat25k: freq per 25k in non-category}, ...]}}

        """
        if self.used:
            raise Exception('Cannot reuse a ScatterChart constructor')
        if kwargs is not {} and self.verbose:
            logging.info('Excessive arguments passed to ScatterChart.to_dict: ' + str(kwargs))
        all_categories = self.term_doc_matrix.get_categories()
        assert category in all_categories
        if not_categories is None:
            not_categories = [c for c in all_categories if c != category]
            neutral_categories = []
            extra_categories = []
        elif neutral_categories is None:
            neutral_categories = [c for c in all_categories if c not in [category] + not_categories]
            extra_categories = []
        elif extra_categories is None:
            extra_categories = [c for c in all_categories if c not in [category] + not_categories + neutral_categories]
        all_categories = [category] + not_categories + neutral_categories + extra_categories
        df = self._add_x_and_y_coords_to_term_df_if_injected(self._get_term_category_frequencies())
        if scores is None:
            scores = self._get_default_scores(category, not_categories, df)
        category_column_name = str(category) + ' freq'
        df['category score'] = CornerScore.get_scores_for_category(df[category_column_name], df[[str(c) + ' freq' for c in not_categories]].sum(axis=1))
        if self.scatterchartdata.term_significance is not None:
            df['p'] = get_p_vals(df, category_column_name, self.scatterchartdata.term_significance)
        df['not category score'] = CornerScore.get_scores_for_category(df[[str(c) + ' freq' for c in not_categories]].sum(axis=1), df[category_column_name])
        df['color_scores'] = scores
        if self.scatterchartdata.terms_to_include is None and self.scatterchartdata.dont_filter is False:
            df = self._filter_bigrams_by_minimum_not_category_term_freq(category_column_name, not_categories, df)
            df = filter_bigrams_by_pmis(self._filter_by_minimum_term_frequency(all_categories, df), threshold_coef=self.scatterchartdata.pmi_threshold_coefficient)
        if self.scatterchartdata.filter_unigrams:
            df = filter_out_unigrams_that_only_occur_in_one_bigram(df)
        if len(df) == 0:
            raise NoWordMeetsTermFrequencyRequirementsError()
        df['category score rank'] = rankdata(df['category score'], method='ordinal')
        df['not category score rank'] = rankdata(df['not category score'], method='ordinal')
        if self.scatterchartdata.max_terms and self.scatterchartdata.max_terms < len(df):
            assert self.scatterchartdata.max_terms > 0
            df = self._limit_max_terms(category, df)
        df = df.reset_index()
        if self.x_coords is None:
            self.x_coords, self.y_coords = self._get_coordinates_from_transform_and_jitter_frequencies(category, df, not_categories, transform)
            df['x'], df['y'] = (self.x_coords, self.y_coords)
            df['ox'], df['oy'] = (self.x_coords, self.y_coords)
        df['not cat freq'] = df[[str(x) + ' freq' for x in not_categories]].sum(axis=1)
        if neutral_categories != []:
            df['neut cat freq'] = df[[str(x) + ' freq' for x in neutral_categories]].sum(axis=1).fillna(0)
        if extra_categories != []:
            df['extra cat freq'] = df[[str(x) + ' freq' for x in extra_categories]].sum(axis=1).fillna(0)
        json_df = df[['x', 'y', 'ox', 'oy', 'term'] + (['p'] if self.scatterchartdata.term_significance else [])]
        json_df = self._add_term_freq_to_json_df(json_df, df, category).assign(s=self.scatterchartdata.score_transform(df['color_scores']), os=df['color_scores'])
        if background_scorer:
            bg_scores = background_scorer.get_scores(self.term_doc_matrix)
            json_df = json_df.assign(bg=lambda json_df: bg_scores[1].loc[json_df.term].values)
        elif not self.scatterchartdata.use_non_text_features:
            json_df = json_df.assign(bg=lambda json_df: self._get_corpus_characteristic_scores(json_df))
        self._preform_axis_rescale(json_df, self._rescale_x, 'x')
        self._preform_axis_rescale(json_df, self._rescale_y, 'y')
        if self.scatterchartdata.terms_to_include is not None:
            json_df = self._use_only_selected_terms(json_df)
        category_terms = list(json_df.sort_values('s', ascending=False)['term'].iloc[:10])
        not_category_terms = list(json_df.sort_values('s', ascending=True)['term'].iloc[:10])
        if category_name is None:
            category_name = category
        if not_category_name is None:
            not_category_name = 'Not ' + str(category_name)

        def better_title(x):
            if title_case_names:
                return ' '.join([t[0].upper() + t[1:].lower() for t in x.split()])
            else:
                return x
        j = {'info': {'category_name': better_title(category_name), 'not_category_name': better_title(not_category_name), 'category_terms': category_terms, 'not_category_terms': not_category_terms, 'category_internal_name': category, 'not_category_internal_names': not_categories, 'categories': self.term_doc_matrix.get_categories(), 'neutral_category_internal_names': neutral_categories, 'extra_category_internal_names': extra_categories}}
        if self.metadata_term_lists is not None:
            j['metalists'] = self.metadata_term_lists
        if self.metadata_descriptions is not None:
            j['metadescriptions'] = self.metadata_descriptions
        if self.term_colors is not None:
            j['info']['term_colors'] = self.term_colors
        j['data'] = json_df.to_dict(orient='records')
        if self.hidden_terms is not None:
            for term_obj in j['data']:
                if term_obj['term'] in self.hidden_terms:
                    term_obj['display'] = False
        if use_offsets:
            j['offsets'] = self.term_doc_matrix.get_offsets()
        if self.category_scores is not None:
            j['category_scores'] = self.category_scores
        return j

    def _add_x_and_y_coords_to_term_df_if_injected(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.x_coords is not None:
            df = df.assign(x=self.x_coords, y=self.y_coords)
        if not self.original_x is None:
            try:
                df = df.assign(ox=self.original_x.values)
            except AttributeError:
                df = df.assign(ox=self.original_x)
        if not self.original_y is None:
            try:
                df = df.assign(oy=self.original_y.values)
            except AttributeError:
                df = df.assign(oy=self.original_y)
        return df

    def _get_term_category_frequencies(self):
        return self.term_doc_matrix.get_term_category_frequencies(self.scatterchartdata)

    def _use_only_selected_terms(self, json_df):
        term_df = pd.DataFrame({'term': self.scatterchartdata.terms_to_include})
        return pd.merge(json_df, term_df, on='term', how='inner')

    def _preform_axis_rescale(self, json_df, rescaler, variable_to_rescale):
        if rescaler is not None:
            json_df.loc[:, variable_to_rescale] = rescaler(json_df[variable_to_rescale])
            assert json_df[variable_to_rescale].min() >= 0 and json_df[variable_to_rescale].max() <= 1

    def _get_corpus_characteristic_scores(self, json_df):
        bg_terms = self.term_doc_matrix.get_scaled_f_scores_vs_background()
        bg_terms = bg_terms['Scaled f-score']
        bg_terms.name = 'bg'
        bg_terms = bg_terms.reset_index()
        bg_terms.columns = ['term' if x in ['index', 'word'] else x for x in bg_terms.columns]
        json_df = pd.merge(json_df, bg_terms, on='term', how='left')
        return json_df.loc[:, 'bg'].fillna(0)

    def _add_term_freq_to_json_df(self, json_df, term_freq_df, category) -> pd.DataFrame:
        """
        json_df['cat25k'] = (((term_freq_df[category + ' freq'] * 1.
                               / term_freq_df[category + ' freq'].sum()) * 25000).fillna(0)
                             .apply(np.round).astype(int))
        json_df['ncat25k'] = (((term_freq_df['not cat freq'] * 1.
                                / term_freq_df['not cat freq'].sum()) * 25000).fillna(0)
                              .apply(np.round).astype(int))
        """
        json_df = json_df.assign(cat25k=(term_freq_df[str(category) + ' freq'] * 1.0 / term_freq_df[str(category) + ' freq'].sum() * 25000).fillna(0).apply(np.round).astype(int), ncat25k=(term_freq_df['not cat freq'] * 1.0 / term_freq_df['not cat freq'].sum() * 25000).fillna(0).apply(np.round).astype(int), neut25k=0, neut=0, extra25k=0, extra=0)
        if 'neut cat freq' in term_freq_df:
            json_df = json_df.assign(neut25k=(term_freq_df['neut cat freq'] * 1.0 / term_freq_df['neut cat freq'].sum() * 25000).fillna(0).apply(np.round).astype(int), neut=term_freq_df['neut cat freq'])
        if 'extra cat freq' in term_freq_df:
            json_df = json_df.assign(extra25k=(term_freq_df['extra cat freq'] * 1.0 / term_freq_df['extra cat freq'].sum() * 25000).fillna(0).apply(np.round).astype(int), extra=term_freq_df['extra cat freq'])
        return json_df

    def _get_category_names(self, category):
        other_categories = [val + ' freq' for val in self.term_doc_matrix.get_categories() if val != category]
        all_categories = other_categories + [str(category) + ' freq']
        return (all_categories, other_categories)

    def _get_coordinates_from_transform_and_jitter_frequencies(self, category, df, other_categories, transform):
        not_counts = df[[str(c) + ' freq' for c in other_categories]].sum(axis=1)
        counts = df[str(category) + ' freq']
        x_data_raw = transform(not_counts, df.index, counts)
        y_data_raw = transform(counts, df.index, not_counts)
        x_data = self._add_jitter(x_data_raw)
        y_data = self._add_jitter(y_data_raw)
        return (x_data, y_data)

    def _add_jitter(self, vec):
        """
        :param vec: array to jitter
        :return: array, jittered version of arrays
        """
        if self.scatterchartdata.jitter == 0 or self.scatterchartdata.jitter is None:
            return vec
        return vec + np.random.rand(1, len(vec))[0] * self.scatterchartdata.jitter

    def _term_rank_score_and_frequency_df(self, all_categories, category, other_categories, scores):
        df = self._add_x_and_y_coords_to_term_df_if_injected(self._get_term_category_frequencies())
        if scores is None:
            scores = self._get_default_scores(category, other_categories, df)
        category_column_name = str(category) + ' freq'
        df = df['category score'] = CornerScore.get_scores_for_category(df[str(category_column_name)], df[[str(c) + ' freq' for c in other_categories]].sum(axis=1))
        if self.scatterchartdata.term_significance is not None:
            df = df.assign(p=get_p_vals(df, category_column_name, self.scatterchartdata.term_significance))
        df['not category score'] = CornerScore.get_scores_for_category(df[[str(c) + ' freq' for c in other_categories]].sum(axis=1), df[str(category_column_name)])
        df['color_scores', :] = scores
        if self.scatterchartdata.terms_to_include is None and self.scatterchartdata.dont_filter is False:
            df = self._filter_bigrams_by_minimum_not_category_term_freq(category_column_name, other_categories, df)
            df = filter_bigrams_by_pmis(self._filter_by_minimum_term_frequency(all_categories, df), threshold_coef=self.scatterchartdata.pmi_threshold_coefficient)
        if self.scatterchartdata.filter_unigrams:
            df = filter_out_unigrams_that_only_occur_in_one_bigram(df)
        if len(df) == 0:
            raise NoWordMeetsTermFrequencyRequirementsError()
        df['category score rank'] = rankdata(df['category score'], method='ordinal')
        df['not category score rank'] = rankdata(df['not category score'], method='ordinal')
        if self.scatterchartdata.max_terms and self.scatterchartdata.max_terms < len(df):
            assert self.scatterchartdata.max_terms > 0
            df = self._limit_max_terms(category, df)
        df = df.reset_index()
        return df

    def _filter_bigrams_by_minimum_not_category_term_freq(self, category_column_name, other_categories, df):
        if self.scatterchartdata.terms_to_include is None and self.scatterchartdata.dont_filter is False:
            return df[(df[str(category_column_name)] > 0) | (df[[str(c) + ' freq' for c in other_categories]].sum(axis=1) >= self.scatterchartdata.minimum_not_category_term_frequency)]
        else:
            return df

    def _filter_by_minimum_term_frequency(self, all_categories, df):
        if self.scatterchartdata.terms_to_include is None and self.scatterchartdata.dont_filter is False:
            df = df[lambda df: df[[str(c) + ' freq' for c in all_categories]].sum(axis=1) > self.scatterchartdata.minimum_term_frequency]
        return df

    def _limit_max_terms(self, category, df):
        df['score'] = self._term_importance_ranks(category, df)
        df = df.loc[df.sort_values('score').iloc[:self.scatterchartdata.max_terms].index]
        return df[[c for c in df.columns if c != 'score']]

    def _get_default_scores(self, category, other_categories, df):
        category_column_name = str(category) + ' freq'
        cat_word_counts = df[category_column_name]
        not_cat_word_counts = df[[str(c) + ' freq' for c in other_categories]].sum(axis=1)
        scores = RankDifference().get_scores(cat_word_counts, not_cat_word_counts)
        return scores

    def _term_importance_ranks(self, category, df):
        return np.array([df['category score rank'], df['not category score rank']]).min(axis=0)

    def draw(self, category, num_top_words_to_annotate=4, words_to_annotate=[], scores=None, transform=percentile_alphabetical):
        """Outdated.  MPLD3 drawing.

        Parameters
        ----------
        category
        num_top_words_to_annotate
        words_to_annotate
        scores
        transform

        Returns
        -------
        pd.DataFrame, html of fgure
        """
        try:
            import matplotlib.pyplot as plt
        except:
            raise Exception('matplotlib and mpld3 need to be installed to use this function.')
        try:
            from mpld3 import plugins, fig_to_html
        except:
            raise Exception('mpld3 need to be installed to use this function.')
        all_categories, other_categories = self._get_category_names(category)
        df = self._term_rank_score_and_frequency_df(all_categories, category, other_categories, scores)
        if self.x_coords is None:
            df['x'], df['y'] = self._get_coordinates_from_transform_and_jitter_frequencies(category, df, other_categories, transform)
        df_to_annotate = df[(df['not category score rank'] <= num_top_words_to_annotate) | (df['category score rank'] <= num_top_words_to_annotate) | df['term'].isin(words_to_annotate)]
        words = list(df['term'])
        font = {'family': 'sans-serif', 'color': 'black', 'weight': 'normal', 'size': 'large'}
        fig, ax = plt.subplots()
        plt.figure(figsize=(10, 10))
        plt.gcf().subplots_adjust(bottom=0.2)
        plt.gcf().subplots_adjust(right=0.2)
        points = ax.scatter(self.x_coords, self.y_coords, c=-df['color_scores'], cmap='seismic', s=10, edgecolors='none', alpha=0.9)
        tooltip = plugins.PointHTMLTooltip(points, ['<span id=a>%s</span>' % w for w in words], css='#a {background-color: white;}')
        plugins.connect(fig, tooltip)
        ax.set_ylim([-0.2, 1.2])
        ax.set_xlim([-0.2, 1.2])
        ax.xaxis.set_ticks([0.0, 0.5, 1.0])
        ax.yaxis.set_ticks([0.0, 0.5, 1.0])
        ax.set_ylabel(category.title() + ' Frequency Percentile', fontdict=font, labelpad=20)
        ax.set_xlabel('Not ' + category.title() + ' Frequency Percentile', fontdict=font, labelpad=20)
        for i, row in df_to_annotate.iterrows():
            alignment_criteria = i % 2 == 0
            horizontalalignment = 'right' if alignment_criteria else 'left'
            verticalalignment = 'bottom' if alignment_criteria else 'top'
            term = row['term']
            ax.annotate(term, (self.x_coords[i], self.y_data[i]), size=15, horizontalalignment=horizontalalignment, verticalalignment=verticalalignment)
        plt.show()
        return (df, fig_to_html(fig))

    def to_dict_without_categories(self):
        if self.y_coords is None or self.x_coords is None or self.original_x is None or (self.original_y is None):
            raise NeedToInjectCoordinatesException('This function requires you run inject_coordinates.')
        return {'data': self._add_x_and_y_coords_to_term_df_if_injected(self.term_doc_matrix.get_term_count_df().rename(columns={'corpus': 'cat'}).assign(cat25k=lambda df: (df['cat'] * 1.0 / df['cat'].sum() * 25000).apply(np.round).astype(int))).reset_index().sort_values(by=['x', 'y', 'term']).to_dict(orient='records')}

def _get_default_scores(self, category, other_categories, df):
    category_column_name = str(category) + ' freq'
    cat_word_counts = df[category_column_name]
    not_cat_word_counts = df[[str(c) + ' freq' for c in other_categories]].sum(axis=1)
    scores = RankDifference().get_scores(cat_word_counts, not_cat_word_counts)
    return scores

class TermDocMatrixWithoutCategories(object):

    def __init__(self, X: csr_matrix, mX: csr_matrix, term_idx_store: IndexStore, metadata_idx_store: IndexStore, unigram_frequency_path: str=None):
        """

        Parameters
        ----------
        X : csr_matrix
            term document matrix
        mX : csr_matrix
            metadata-document matrix
        term_idx_store : IndexStore
            Term indices
        metadata_idx_store : IndexStore
          Document metadata indices
        unigram_frequency_path : str or None
            Path to term frequency file.
        """
        self._X = X
        self._mX = mX
        self._term_idx_store = term_idx_store
        self._metadata_idx_store = metadata_idx_store
        self._unigram_frequency_path = unigram_frequency_path
        self._background_corpus = None
        self._strict_unigram_definition = True

    def get_default_stoplist(self):
        return MY_ENGLISH_STOP_WORDS

    def allow_single_quotes_in_unigrams(self) -> Self:
        """
        Don't filter out single quotes in unigrams
        :return: self
        """
        self._strict_unigram_definition = False
        return self

    def compact(self, compactor, non_text: bool=False) -> Self:
        """
        Compact term document matrix.

        Parameters
        ----------
        compactor : object
            Object that takes a Term Doc Matrix as its first argument, and has a compact function which returns a
            Term Doc Matrix like argument
        non_text : bool
            Use non text features. False by default.
        Returns
        -------
        TermDocMatrix
        """
        return compactor.compact(self, non_text)

    def select(self, compactor, non_text: bool=False) -> Self:
        """
        Same as compact
        """
        return compactor.compact(self, non_text)

    def get_num_terms(self, non_text: bool=False) -> int:
        """
        Returns
        -------
        The number of terms registered in the term doc matrix
        """
        if non_text:
            return self.get_num_metadata()
        return len(self._term_idx_store)

    def get_num_docs(self) -> int:
        """
        Returns
        -------
        int, number of documents
        """
        return self._X.shape[0]

    def get_num_metadata(self) -> int:
        """
        Returns
        -------
        int, number of unique metadata items
        """
        return len(self.get_metadata())

    def set_background_corpus(self, background) -> Self:
        """
        Parameters
        ----------
        background

        """
        if issubclass(type(background), TermDocMatrixWithoutCategories):
            self._background_corpus = pd.DataFrame(background.get_term_freq_df().sum(axis=1), columns=['background']).reset_index()
            self._background_corpus.columns = ['word', 'background']
        elif type(background) == pd.DataFrame and set(background.columns) == set(['word', 'background']):
            self._background_corpus = background
        elif type(background) == pd.Series:
            self._background_corpus = background
        else:
            raise Exception('The argument named background must be a subclass of TermDocMatrix or a ' + 'DataFrame with columns "word" and "background", where "word" ' + 'is the term text, and "background" is its frequency.')
        return self

    def get_background_corpus(self):
        if self._background_corpus is not None:
            if type(self._background_corpus) == pd.DataFrame:
                return self._background_corpus['background']
            elif type(self._background_corpus) == pd.Series:
                return self._background_corpus
            return self._background_corpus
        return DefaultBackgroundFrequencies.get_background_frequency_df(self._unigram_frequency_path)

    def get_term_and_background_counts(self) -> pd.DataFrame:
        """
        Returns
        -------
        A pd.DataFrame consisting of unigram term counts of words occurring
         in the TermDocumentMatrix and their corresponding background corpus
         counts.  The dataframe has two columns, corpus and background.

        >>> corpus.get_unigram_corpus().get_term_and_background_counts()
                          corpus  background
        obama              702.0    565739.0
        romney             570.0    695398.0
        barack             248.0    227861.0
        ...
        """
        background_df = self._get_background_unigram_frequencies()
        if type(background_df) == pd.DataFrame:
            background_df = background_df['background']
        corpus_freq_df = self.get_term_count_df()
        corpus_unigram_freq = self._get_corpus_unigram_freq(corpus_freq_df)
        return pd.DataFrame({'background': background_df, 'corpus': corpus_unigram_freq['corpus']}).fillna(0)

    def get_term_count_df(self):
        return pd.DataFrame({'corpus': self._X.sum(axis=0).A1, 'term': self.get_terms()}).set_index('term')

    def _get_corpus_unigram_freq(self, corpus_freq_df: pd.DataFrame) -> pd.DataFrame:
        unigram_validator = re.compile('^[A-Za-z]+$')
        corpus_unigram_freq = corpus_freq_df.loc[[term for term in corpus_freq_df.index if unigram_validator.match(term) is not None]]
        return corpus_unigram_freq

    def _get_background_unigram_frequencies(self) -> pd.DataFrame:
        if self.get_background_corpus() is not None:
            return self.get_background_corpus()
        return DefaultBackgroundFrequencies.get_background_frequency_df(self._unigram_frequency_path)

    def list_extra_features(self, use_metadata: bool=True) -> List[Dict[str, str]]:
        """
        Returns
        -------
        List of dicts.  One dict for each document, keys are metadata, values are counts
        """
        return FeatureLister(self._get_relevant_X(use_metadata), self._get_relevant_idx_store(use_metadata), self.get_num_docs()).output()

    def get_terms(self, use_metadata=False) -> List[str]:
        """
        Returns
        -------
        np.array of unique terms
        """
        if use_metadata:
            return self.get_metadata()
        return self._term_idx_store._i2val

    def get_metadata(self) -> List[str]:
        """
        Returns
        -------
        np.array of unique metadata
        """
        return self._metadata_idx_store._i2val

    def get_total_unigram_count(self) -> int:
        return self._get_unigram_term_freq_df().sum()

    def _get_unigram_term_freq_df(self) -> pd.DataFrame:
        return self._get_corpus_unigram_freq(self.get_term_count_df()['corpus'])

    def _get_X_after_delete_terms(self, idx_to_delete_list: List[int], non_text: bool=False) -> Tuple[csr_matrix, IndexStore]:
        new_term_idx_store = self._get_relevant_idx_store(non_text).batch_delete_idx(idx_to_delete_list)
        new_X = delete_columns(self._get_relevant_X(non_text), idx_to_delete_list)
        return (new_X, new_term_idx_store)

    def _get_relevant_X(self, non_text: bool) -> csr_matrix:
        return self._mX if non_text else self._X

    def _get_relevant_idx_store(self, non_text: bool) -> IndexStore:
        return self._metadata_idx_store if non_text else self._term_idx_store

    def remove_infrequent_words(self, minimum_term_count: int, term_ranker: Type[TermRanker]=AbsoluteFrequencyRanker, non_text: bool=False) -> Self:
        """
        Returns
        -------
        A new TermDocumentMatrix consisting of only terms which occur at least minimum_term_count.
        """
        ranker = term_ranker(self)
        if non_text:
            ranker = ranker.use_non_text_features()
        tdf = ranker.get_ranks().sum(axis=1)
        return self.remove_terms(list(tdf[tdf <= minimum_term_count].index), non_text=non_text)

    def remove_infrequent_terms(self, minimum_term_count: int, term_ranker: Type[TermRanker]=AbsoluteFrequencyRanker, non_text: bool=False) -> Self:
        return self.remove_infrequent_words(minimum_term_count=minimum_term_count, term_ranker=term_ranker, non_text=non_text)

    def remove_word_by_document_pct(self, min_document_pct: float=0.0, max_document_pct: float=1.0, non_text: bool=False) -> Self:
        """
        Returns a copy of the corpus with terms that occur in a document percentage range.

        :param min_document_pct: float, minimum document percentage. 0 by default
        :param max_document_pct: float, maximum document percentage. 1 by default
        :param non_text: bool, use metadata?
        :return: Corpus
        """
        tdm = self.get_term_doc_mat(non_text=non_text) > 0
        tdmpct = (tdm.sum(axis=0) / tdm.shape[0]).A1
        mask = (tdmpct >= min_document_pct) & (tdmpct <= max_document_pct)
        return self.whitelist_terms(np.array(self.get_terms(use_metadata=non_text))[mask], non_text=non_text)

    def remove_entity_tags(self, non_text: bool=False) -> Self:
        """
        Returns
        -------
        A new TermDocumentMatrix consisting of only terms in the current TermDocumentMatrix
         that aren't spaCy entity tags.

        Note: Used if entity types are censored using FeatsFromSpacyDoc(tag_types_to_censor=...).
        :param non_text: bool, use metadata?
        """
        terms_to_remove = [term for term in self.get_terms(use_metadata=non_text) if any([word in SPACY_ENTITY_TAGS for word in term.split()])]
        return self.remove_terms(terms_to_remove, non_text=non_text)

    def remove_terms(self, terms: List[str], ignore_absences: bool=False, non_text: bool=False) -> Self:
        """Non-destructive term removal.

        Parameters
        ----------
        terms : list
            list of terms to remove
        ignore_absences : bool, False by default
            If term does not appear, don't raise an error, just move on.
        non_text : bool, False by default
            Remove metadata terms instead of regular terms

        Returns
        -------
        TermDocMatrix, new object with terms removed.
        """
        idx_to_delete_list = self._build_term_index_list(ignore_absences, terms, non_text)
        return self.remove_terms_by_indices(idx_to_delete_list, non_text)

    def whitelist_terms(self, whitelist_terms: List[str], non_text: bool=False) -> Self:
        """

        :param whitelist_terms: list[str], terms to whitelist
        :param non_text: bool, use non text featurs, default False
        :return: TermDocMatrix, new object with only terms in parameter
        """
        return self.remove_terms(list(set(self.get_terms(use_metadata=non_text)) - set(whitelist_terms)), non_text=non_text)

    def _build_term_index_list(self, ignore_absences: bool, terms: List[str], non_text=False) -> List[int]:
        idx_to_delete_list = []
        my_term_idx_store = self._get_relevant_idx_store(non_text)
        for term in terms:
            if term not in my_term_idx_store:
                if not ignore_absences:
                    raise KeyError('Term %s not found' % term)
                continue
            idx_to_delete_list.append(my_term_idx_store.getidx(term))
        return idx_to_delete_list

    def _make_new_term_doc_matrix(self, new_X=None, new_mX=None, new_y=None, new_term_idx_store=None, new_category_idx_store=None, new_metadata_idx_store=None, new_y_mask=None) -> Self:
        return TermDocMatrixWithoutCategories(X=new_X if new_X is not None else self._X, mX=new_mX if new_mX is not None else self._mX, term_idx_store=new_term_idx_store if new_term_idx_store is not None else self._term_idx_store, metadata_idx_store=new_metadata_idx_store if new_metadata_idx_store is not None else self._metadata_idx_store, unigram_frequency_path=self._unigram_frequency_path)

    def remove_terms_used_in_less_than_num_docs(self, threshold: int, non_text: bool=False) -> Self:
        """
        Parameters
        ----------
        threshold: int
            Minimum number of documents term should appear in to be kept
        non_text: bool
            Use non-text features instead of terms

        Returns
        -------
        TermDocMatrix, new object with terms removed.
        """
        term_counts = self._get_relevant_X(non_text).astype(bool).astype(int).sum(axis=0).A[0]
        terms_to_remove = np.where(term_counts < threshold)[0]
        return self.remove_terms_by_indices(terms_to_remove, non_text)

    def remove_document_ids(self, document_ids: List[int], remove_unused_terms: bool=True, remove_unused_metadata: bool=False) -> Self:
        """

        :param document_ids: List[int], list of document ids to remove
        :return: Corpus
        """
        y_mask = ~np.isin(np.arange(self.get_num_docs()), np.array(document_ids))
        updated_tdm = self._make_new_term_doc_matrix(new_X=self._X, new_mX=self._mX, new_y=None, new_category_idx_store=None, new_term_idx_store=self._term_idx_store, new_metadata_idx_store=self._metadata_idx_store, new_y_mask=y_mask)
        if remove_unused_terms:
            unused_term_idx = np.where(self._X[y_mask, :].sum(axis=0) == 0)[1]
            updated_tdm = updated_tdm.remove_terms_by_indices(unused_term_idx, non_text=False)
        if remove_unused_metadata:
            unused_metadata_mask = np.mask(self._mX[y_mask, :].sum(axis=0) == 0)[0]
            updated_tdm = updated_tdm.remove_terms_by_indices(unused_metadata_mask, non_text=True)
        return updated_tdm

    def remove_documents_less_than_length(self, max_length: int, non_text: bool=False) -> Self:
        """
            `

        :param max_length: int, length of document in terms registered in corpus
        :return: Corpus
        """
        tdm = self.get_metadata_doc_mat() if non_text else self.get_term_doc_mat()
        doc_ids_to_remove = np.where(tdm.sum(axis=1).T.A1 < max_length)
        return self.remove_document_ids(doc_ids_to_remove)

    def get_unigram_corpus(self) -> Self:
        """
        Returns
        -------
        A new TermDocumentMatrix consisting of only unigrams in the current TermDocumentMatrix.
        """
        terms_to_ignore = self._get_non_unigrams()
        return self.remove_terms(terms_to_ignore)

    def _get_non_unigrams(self) -> List[str]:
        return [term for term in self._term_idx_store._i2val if ' ' in term or (self._strict_unigram_definition and "'" in term)]

    def get_stoplisted_unigram_corpus(self, stoplist: Optional[List[str]]=None, non_text: bool=False) -> Self:
        """
        Parameters
        -------
        stoplist : list, optional

        Returns
        -------
        A new TermDocumentMatrix consisting of only unigrams in the current TermDocumentMatrix.
        """
        if stoplist is None:
            stoplist = self.get_default_stoplist()
        else:
            stoplist = [w.lower() for w in stoplist]
        return self._remove_terms_from_list_and_all_non_unigrams(stoplist, non_text=non_text)

    def get_stoplisted_corpus(self, stoplist=None, non_text: bool=False):
        """
        Parameters
        -------
        stoplist : list, optional
        non_text : bool

        Returns
        -------
        A new TermDocumentMatrix consisting of only unigrams in the current TermDocumentMatrix.
        """
        if stoplist is None:
            stoplist = self.get_default_stoplist()
        return self.remove_terms([w.lower() for w in stoplist], ignore_absences=True, non_text=non_text)

    def get_stoplisted_unigram_corpus_and_custom(self, custom_stoplist, non_text: bool=False):
        """
        Parameters
        -------
        stoplist : list of lower-cased words, optional

        Returns
        -------
        A new TermDocumentMatrix consisting of only unigrams in the current TermDocumentMatrix.
        """
        if type(custom_stoplist) == str:
            custom_stoplist = [custom_stoplist]
        return self._remove_terms_from_list_and_all_non_unigrams(set(self.get_default_stoplist()) | set((w.lower() for w in custom_stoplist)), non_text=non_text)

    def filter_out(self, filter_func, non_text=False):
        """

        :param filter_func: function which takes a string and returns true or false
        :return: A new TermDocumentMatrix consisting of only unigrams in the current TermDocumentMatrix.
        """
        return self.remove_terms([x for x in self.get_terms(use_metadata=non_text) if filter_func(x)], non_text=non_text)

    def _remove_terms_from_list_and_all_non_unigrams(self, stoplist, non_text=False):
        terms_to_ignore = [term for term in (self._metadata_idx_store._i2val if non_text else self._term_idx_store._i2val) if ' ' in term or (self._strict_unigram_definition and ("'" in term or '’' in term)) or term in stoplist]
        return self.remove_terms(terms_to_ignore, non_text=non_text)

    def metadata_in_use(self) -> bool:
        """
        Returns True if metadata values are in term doc matrix.

        Returns
        -------
        bool
        """
        return len(self._metadata_idx_store) > 0

    def _make_all_positive_data_ones(self, new_x: csr_matrix) -> csr_matrix:
        return (new_x > 0).astype(np.int32)

    def remove_terms_by_indices(self, idx_to_delete_list: List[int], non_text: bool=False) -> Self:
        """
        Parameters
        ----------
        idx_to_delete_list, list
        non_text, bool
            Should we remove non text features or just terms?

        Returns
        -------
        TermDocMatrix
        """
        new_X, new_idx_store = self._get_X_after_delete_terms(idx_to_delete_list, non_text)
        return self._make_new_term_doc_matrix(new_X=self._X if non_text else new_X, new_mX=new_X if non_text else self._mX, new_y=None, new_category_idx_store=None, new_term_idx_store=self._term_idx_store if non_text else new_idx_store, new_metadata_idx_store=new_idx_store if non_text else self._metadata_idx_store, new_y_mask=np.ones(new_X.shape[0]).astype(np.bool))

    def get_scaled_f_scores_vs_background(self, scaler_algo: str=DEFAULT_BACKGROUND_SCALER_ALGO, beta: float=DEFAULT_BACKGROUND_BETA) -> pd.DataFrame:
        """
        Parameters
        ----------
        scaler_algo : str
            see get_scaled_f_scores, default 'none'
        beta : float
          default 1.
        Returns
        -------
        pd.DataFrame of scaled_f_score scores compared to background corpus
        """
        df = self.get_term_and_background_counts()
        df['Scaled f-score'] = ScaledFScore.get_scores_for_category(df['corpus'], df['background'], scaler_algo, beta)
        return df.sort_values(by='Scaled f-score', ascending=False)

    def get_term_doc_mat(self, non_text: bool=False) -> csr_matrix:
        """
        Returns sparse matrix representation of term-doc-matrix

        Returns
        -------
        scipy.sparse.csr_matrix
        """
        if non_text:
            return self.get_metadata_doc_mat()
        return self._X

    def get_term_freqs(self, non_text: bool=False) -> np.array:
        return self.get_term_doc_mat(non_text=non_text).sum(axis=0).A1

    def get_term_doc_mat_coo(self, non_text: bool=False) -> coo_matrix:
        """
        Returns sparse matrix representation of term-doc-matrix

        Returns
        -------
        scipy.sparse.coo_matrix
        """
        return self.get_term_doc_mat(non_text=non_text).astype(np.double).tocoo()

    def get_metadata_doc_mat(self) -> csr_matrix:
        """
        Returns sparse matrix representation of term-doc-matrix

        Returns
        -------
        scipy.sparse.csr_matrix
        """
        return self._mX

    def term_doc_lists(self) -> Dict:
        """
        Returns
        -------
        dict
        """
        doc_ids = self._X.transpose().tolil().rows
        terms = self._term_idx_store.values()
        return dict(zip(terms, doc_ids))

    def apply_ranker(self, term_ranker: Type[TermRanker], use_non_text_features: bool, label_append: str=' freq') -> pd.DataFrame:
        """
        Parameters
        ----------
        term_ranker : TermRanker

        Returns
        -------
        pd.Dataframe
        """
        if use_non_text_features:
            return term_ranker(self).use_non_text_features().get_ranks(label_append=label_append)
        return term_ranker(self).get_ranks(label_append=label_append)

    def add_doc_names_as_metadata(self, doc_names: List[str]) -> Self:
        """
        :param doc_names: array-like[str], document names of reach document
        :return: Corpus-like object with doc names as metadata. If two documents share the same name
        (doc number) will be appended to their names.
        """
        if len(doc_names) != self.get_num_docs():
            raise Exception('The parameter doc_names contains %s elements. It should have %s elements, one per document.' % (len(doc_names), self.get_num_docs()))
        doc_names_counter = collections.Counter(np.array(doc_names))
        metafact = CSRMatrixFactory()
        metaidxstore = IndexStore()
        doc_id_uses = collections.Counter()
        for i in range(self.get_num_docs()):
            doc_id = doc_names[i]
            if doc_names_counter[doc_id] > 1:
                doc_id_uses[doc_id] += 1
                doc_name_idx = metaidxstore.getidx('%s (%s)' % (doc_id, doc_id_uses[doc_id]))
            else:
                doc_name_idx = metaidxstore.getidx(doc_id)
            metafact[i, i] = doc_name_idx
        return self.add_metadata(metafact.get_csr_matrix(), metaidxstore)

    def get_term_index(self, term: str) -> int:
        return self._term_idx_store.getidxstrict(term)

    def get_metadata_index(self, term: str) -> int:
        return self._metadata_idx_store.getidxstrict(term)

    def get_metadata_from_index(self, index: int) -> str:
        return self._metadata_idx_store.getval(index)

    def get_term_from_index(self, index: int) -> str:
        return self._term_idx_store.getval(index)

    def get_term_index_store(self, non_text=False) -> IndexStore:
        return self._metadata_idx_store if non_text else self._term_idx_store

    def get_document_ids_with_terms(self, terms: List[str], use_non_text_features: bool=False) -> np.array:
        return np.where(self._get_relevant_X(use_non_text_features)[:, [self._term_idx_store.getidx(x) for x in terms if x in self._term_idx_store]].sum(axis=1).A1 > 0)[0]

    def add_metadata(self, metadata_matrix: csr_matrix, meta_index_store: IndexStore) -> Self:
        """
        Returns a new corpus with the metadata matrix and index store integrated.

        :param metadata_matrix: scipy.sparse matrix (# docs, # metadata)
        :param meta_index_store: IndexStore of metadata values
        :return: TermDocMatrixWithoutCategories
        """
        assert isinstance(meta_index_store, IndexStore)
        assert len(metadata_matrix.shape) == 2
        assert metadata_matrix.shape[0] == self.get_num_docs()
        return self._make_new_term_doc_matrix(new_X=self._X, new_y=None, new_category_idx_store=None, new_y_mask=np.ones(self.get_num_docs()).astype(bool), new_mX=metadata_matrix, new_term_idx_store=self._term_idx_store, new_metadata_idx_store=meta_index_store)

    def rename_metadata(self, old_to_new_vals: List[Tuple[str, str]], policy: MetadataReplacementRetentionPolicy=MetadataReplacementRetentionPolicy.KEEP_ONLY_NEW) -> Self:
        new_mX, new_metadata_idx_store = self._remap_metadata(old_to_new_vals, policy)
        return self._make_new_term_doc_matrix(new_X=self._X, new_mX=new_mX, new_term_idx_store=self._term_idx_store, new_metadata_idx_store=new_metadata_idx_store)

    def _remap_metadata(self, old_to_new_vals: List[Tuple[str, str]], policy: MetadataReplacementRetentionPolicy) -> Tuple[csr_matrix, IndexStore]:
        old_to_new_df = self._get_old_to_new_metadata_mapping_df(old_to_new_vals)
        keep_vals = self._get_metadata_mapped_values_to_keep(old_to_new_df)
        new_val_mX = np.zeros(shape=(self._mX.shape[0], old_to_new_df.New.nunique()))
        if policy.value == MetadataReplacementRetentionPolicy.KEEP_UNMODIFIED.value:
            new_metadata_idx_store = IndexStoreFromList.build(keep_vals)
        elif policy.value == MetadataReplacementRetentionPolicy.KEEP_ONLY_NEW.value:
            new_metadata_idx_store = IndexStore()
        else:
            raise Exception(f'Policy {policy} not supporteds')
        for new_val_i, (new_name, new_df) in enumerate(old_to_new_df.groupby('New')):
            new_metadata_idx_store.getidx(new_name)
            new_val_counts = self._mX[:, self._metadata_idx_store.getidxstrictbatch(new_df.Old.values)]
            new_val_mX[:, new_val_i] = new_val_counts.sum(axis=1).T[0]
        if policy.value == MetadataReplacementRetentionPolicy.KEEP_UNMODIFIED.value:
            keep_mX = self._mX[:, self._metadata_idx_store.getidxstrictbatch(keep_vals)]
            new_mX = scipy.sparse.hstack([keep_mX, new_val_mX], format='csr', dtype=self._mX.dtype)
        else:
            new_mX = scipy.sparse.csr_matrix(new_val_mX, dtype=self._mX.dtype)
        return (new_mX, new_metadata_idx_store)

    def _get_metadata_mapped_values_to_keep(self, old_to_new_df: pd.DataFrame) -> List[str]:
        keep_vals = [x for x in self.get_metadata() if x not in set(old_to_new_df.Old.unique()) | set(old_to_new_df.New.unique())]
        return keep_vals

    def _get_old_to_new_metadata_mapping_df(self, old_to_new_vals: List[Tuple[str, str]]) -> pd.DataFrame:
        old_to_new_vals = [(old, new) for old, new in old_to_new_vals if old in self._metadata_idx_store]
        return pd.DataFrame(old_to_new_vals, columns=['Old', 'New'])

def get_background_corpus(self):
    if self._background_corpus is not None:
        if type(self._background_corpus) == pd.DataFrame:
            return self._background_corpus['background']
        elif type(self._background_corpus) == pd.Series:
            return self._background_corpus
        return self._background_corpus
    return DefaultBackgroundFrequencies.get_background_frequency_df(self._unigram_frequency_path)

def _get_background_unigram_frequencies(self) -> pd.DataFrame:
    if self.get_background_corpus() is not None:
        return self.get_background_corpus()
    return DefaultBackgroundFrequencies.get_background_frequency_df(self._unigram_frequency_path)

def remove_infrequent_words(self, minimum_term_count: int, term_ranker: Type[TermRanker]=AbsoluteFrequencyRanker, non_text: bool=False) -> Self:
    """
        Returns
        -------
        A new TermDocumentMatrix consisting of only terms which occur at least minimum_term_count.
        """
    ranker = term_ranker(self)
    if non_text:
        ranker = ranker.use_non_text_features()
    tdf = ranker.get_ranks().sum(axis=1)
    return self.remove_terms(list(tdf[tdf <= minimum_term_count].index), non_text=non_text)

def remove_infrequent_terms(self, minimum_term_count: int, term_ranker: Type[TermRanker]=AbsoluteFrequencyRanker, non_text: bool=False) -> Self:
    return self.remove_infrequent_words(minimum_term_count=minimum_term_count, term_ranker=term_ranker, non_text=non_text)

def remove_entity_tags(self, non_text: bool=False) -> Self:
    """
        Returns
        -------
        A new TermDocumentMatrix consisting of only terms in the current TermDocumentMatrix
         that aren't spaCy entity tags.

        Note: Used if entity types are censored using FeatsFromSpacyDoc(tag_types_to_censor=...).
        :param non_text: bool, use metadata?
        """
    terms_to_remove = [term for term in self.get_terms(use_metadata=non_text) if any([word in SPACY_ENTITY_TAGS for word in term.split()])]
    return self.remove_terms(terms_to_remove, non_text=non_text)

def whitelist_terms(self, whitelist_terms: List[str], non_text: bool=False) -> Self:
    """

        :param whitelist_terms: list[str], terms to whitelist
        :param non_text: bool, use non text featurs, default False
        :return: TermDocMatrix, new object with only terms in parameter
        """
    return self.remove_terms(list(set(self.get_terms(use_metadata=non_text)) - set(whitelist_terms)), non_text=non_text)

def get_unigram_corpus(self) -> Self:
    """
        Returns
        -------
        A new TermDocumentMatrix consisting of only unigrams in the current TermDocumentMatrix.
        """
    terms_to_ignore = self._get_non_unigrams()
    return self.remove_terms(terms_to_ignore)

def filter_out(self, filter_func, non_text=False):
    """

        :param filter_func: function which takes a string and returns true or false
        :return: A new TermDocumentMatrix consisting of only unigrams in the current TermDocumentMatrix.
        """
    return self.remove_terms([x for x in self.get_terms(use_metadata=non_text) if filter_func(x)], non_text=non_text)

def _remove_terms_from_list_and_all_non_unigrams(self, stoplist, non_text=False):
    terms_to_ignore = [term for term in (self._metadata_idx_store._i2val if non_text else self._term_idx_store._i2val) if ' ' in term or (self._strict_unigram_definition and ("'" in term or '’' in term)) or term in stoplist]
    return self.remove_terms(terms_to_ignore, non_text=non_text)

def apply_ranker(self, term_ranker: Type[TermRanker], use_non_text_features: bool, label_append: str=' freq') -> pd.DataFrame:
    """
        Parameters
        ----------
        term_ranker : TermRanker

        Returns
        -------
        pd.Dataframe
        """
    if use_non_text_features:
        return term_ranker(self).use_non_text_features().get_ranks(label_append=label_append)
    return term_ranker(self).get_ranks(label_append=label_append)

class CategoryColorAssigner(object):

    def __init__(self, corpus, scorer=RankDifference(), ranker=AbsoluteFrequencyRanker, use_non_text_features=False, color_palette=QUALITATIVE_COLORS):
        """
        Assigns scores to colors for categories

        :param corpus: TermDocMatrix
        :param scorer: scorer
        :param color_palette: list of colors [[red, green, blue], ...]
        """
        self.corpus = corpus
        self.scorer = scorer
        self.color_palette = color_palette
        my_ranker = ranker(corpus)
        if use_non_text_features:
            my_ranker.use_non_text_features()
        tdf = my_ranker.get_ranks()
        tdf_sum = tdf.sum(axis=1)
        term_scores = {}
        for cat in tdf.columns:
            term_scores[cat[:-5]] = pd.Series(self.scorer.get_scores(tdf[cat], tdf_sum - tdf[cat]), index=tdf.index)
        self.term_cat = pd.DataFrame(term_scores).idxmax(axis=1)
        ranked_list_categories = pd.Series(corpus.get_category_names_by_row()).value_counts().index
        self.category_colors = pd.Series(self.color_palette[:len(ranked_list_categories)], index=ranked_list_categories)

    def get_category_colors(self):
        return self.category_colors

    def get_term_colors(self):
        """

        :return: dict, term -> color
        """
        term_color = pd.Series(self.category_colors[self.term_cat].values, index=self.term_cat.index)
        return term_color.apply(get_hex_color).to_dict()

def __init__(self, corpus, scorer=RankDifference(), ranker=AbsoluteFrequencyRanker, use_non_text_features=False, color_palette=QUALITATIVE_COLORS):
    """
        Assigns scores to colors for categories

        :param corpus: TermDocMatrix
        :param scorer: scorer
        :param color_palette: list of colors [[red, green, blue], ...]
        """
    self.corpus = corpus
    self.scorer = scorer
    self.color_palette = color_palette
    my_ranker = ranker(corpus)
    if use_non_text_features:
        my_ranker.use_non_text_features()
    tdf = my_ranker.get_ranks()
    tdf_sum = tdf.sum(axis=1)
    term_scores = {}
    for cat in tdf.columns:
        term_scores[cat[:-5]] = pd.Series(self.scorer.get_scores(tdf[cat], tdf_sum - tdf[cat]), index=tdf.index)
    self.term_cat = pd.DataFrame(term_scores).idxmax(axis=1)
    ranked_list_categories = pd.Series(corpus.get_category_names_by_row()).value_counts().index
    self.category_colors = pd.Series(self.color_palette[:len(ranked_list_categories)], index=ranked_list_categories)

def produce_frequency_explorer(corpus, category, category_name=None, not_category_name=None, term_ranker=termranking.AbsoluteFrequencyRanker, alpha=0.01, use_term_significance=False, term_scorer=None, not_categories=None, grey_threshold=0, y_axis_values=None, frequency_transform=lambda x: scale(np.log(x) - np.log(1)), score_scaler=None, **kwargs):
    """
    Produces a Monroe et al. style visualization, with the x-axis being the log frequency

    Parameters
    ----------
    corpus : Corpus
        Corpus to use.
    category : str
        Name of category column as it appears in original data frame.
    category_name : str or None
        Name of category to use.  E.g., "5-star reviews."
        Defaults to category
    not_category_name : str or None
        Name of everything that isn't in category.  E.g., "Below 5-star reviews".
        Defaults to "Not " + category_name
    term_ranker : TermRanker
        TermRanker class for determining term frequency ranks.
    alpha : float, default = 0.01
        Uniform dirichlet prior for p-value calculation
    use_term_significance : bool, True by default
        Use term scorer
    term_scorer : TermSignificance
        Subclass of TermSignificance to use as for scores and significance
    not_categories : list
        All categories other than category by default.  Documents labeled
        with remaining category.
    grey_threshold : float
        Score to grey points. Default is 1.96
    y_axis_values : list
        Custom y-axis values. Defaults to linspace
    frequency_transfom : lambda, default lambda x: scale(np.log(x) - np.log(1))
        Takes a vector of frequencies and returns their x-axis scale.
    score_scaler: lambda, default scale_neg_1_to_1_with_zero_mean_abs_max
    Remaining arguments are from `produce_scattertext_explorer`.'
    Returns
    -------
        str, html of visualization
    """
    if not_categories is None:
        not_categories = [c for c in corpus.get_categories() if c != category]
    if term_scorer is None:
        term_scorer = LogOddsRatioUninformativeDirichletPrior(alpha)
    my_term_ranker = term_ranker(corpus)
    term_scorer = _initialize_term_scorer_if_needed(category=category, corpus=corpus, neutral_categories=kwargs.get('neutral_categories', False), not_categories=not_categories, show_neutral=kwargs.get('show_neutral', False), term_scorer=term_scorer, use_non_text_features=kwargs.get('use_non_text_features', False), term_ranker=term_ranker, term_scorer_kwargs=kwargs.get('term_scorer_kwargs', None))
    if kwargs.get('use_non_text_features', False):
        my_term_ranker.use_non_text_features()
    term_freq_df = my_term_ranker.get_ranks() + 1
    freqs = term_freq_df[[str(c) + ' freq' for c in [category] + not_categories]].sum(axis=1).values
    x_axis_values = [round_downer(10 ** x) for x in np.linspace(0, np.log(freqs.max()) / np.log(10), 5)]
    x_axis_values = [x for x in x_axis_values if x > 1 and x <= freqs.max()]
    frequencies_log_scaled = frequency_transform(freqs)
    if 'scores' not in kwargs:
        kwargs['scores'] = get_term_scorer_scores(category, corpus, kwargs.get('neutral_categories', False), not_categories, kwargs.get('show_neutral', False), term_ranker, term_scorer, kwargs.get('use_non_text_features', False))
    if kwargs.get('rescale_y', None) is None:

        def y_axis_rescale(coords):
            return ((coords - 0.5) / np.abs(coords - 0.5).max() + 1) / 2
        kwargs['rescale_y'] = y_axis_rescale

    def round_to_1(x):
        if x == 0:
            return 0
        return round(x, -int(np.floor(np.log10(abs(x)))))
    if y_axis_values is None:
        max_score = np.floor(np.max(kwargs['scores']) * 100) / 100
        min_score = np.ceil(np.min(kwargs['scores']) * 100) / 100
        if min_score < 0 and max_score > 0:
            central = 0
        else:
            central = 0.5
        y_axis_values = [x for x in [min_score, central, max_score] if x >= min_score and x <= max_score]
    if score_scaler is None:
        score_scaler = scale_neg_1_to_1_with_zero_mean_abs_max
    scores_scaled_for_charting = score_scaler(kwargs['scores'])
    if use_term_significance:
        kwargs['term_significance'] = term_scorer
    kwargs['y_label'] = kwargs.get('y_label', term_scorer.get_name())
    kwargs['color_func'] = kwargs.get('color_func', '(function(d) {\n\treturn (Math.abs(d.os) < %s) \n\t ? d3.interpolate(d3.rgb(230, 230, 230), d3.rgb(130, 130, 130))(Math.abs(d.os)/%s) \n\t : d3.interpolateRdYlBu(d.y);\n\t})' % (grey_threshold, grey_threshold))
    return produce_scattertext_explorer(corpus, category=category, category_name=category_name, not_category_name=not_category_name, x_coords=frequencies_log_scaled, y_coords=scores_scaled_for_charting, original_x=freqs, original_y=kwargs['scores'], x_axis_values=x_axis_values, y_axis_values=y_axis_values, rescale_x=scale, sort_by_dist=False, term_ranker=term_ranker, not_categories=not_categories, x_label=kwargs.get('x_label', 'Log Frequency'), **kwargs)

def produce_characteristic_explorer(corpus, category, category_name=None, not_category_name=None, not_categories=None, characteristic_scorer=DenseRankCharacteristicness(), term_ranker=termranking.AbsoluteFrequencyRanker, term_scorer=RankDifference(), x_label='Characteristic to Corpus', y_label=None, y_axis_labels=None, scores=None, vertical_lines=None, **kwargs):
    """
    Parameters
    ----------
    corpus : Corpus
        It is highly recommended to use a stoplisted, unigram corpus-- `corpus.get_stoplisted_unigram_corpus()`
    category : str
    category_name : str
    not_category_name : str
    not_categories : list
    characteristic_scorer : CharacteristicScorer
    term_ranker
    term_scorer
    term_acceptance_re : SRE_Pattern
        Regular expression to identify valid terms
    kwargs : dict
        remaining produce_scattertext_explorer keywords

    Returns
    -------
    str HTML of visualization

    """
    if not_categories is None:
        not_categories = [c for c in corpus.get_categories() if c != category]
    category_name, not_category_name = get_category_names(category, category_name, not_categories, not_category_name)
    zero_point, characteristic_scores = characteristic_scorer.get_scores(corpus)
    corpus = corpus.remove_terms(set(corpus.get_terms()) - set(characteristic_scores.index))
    characteristic_scores = characteristic_scores.loc[corpus.get_terms()]
    term_freq_df = term_ranker(corpus).get_ranks()
    scores = term_scorer.get_scores(term_freq_df[str(category) + ' freq'], term_freq_df[[str(c) + ' freq' for c in not_categories]].sum(axis=1)) if scores is None else scores
    scores_scaled_for_charting = scale_neg_1_to_1_with_zero_mean_abs_max(scores)
    html = produce_scattertext_explorer(corpus=corpus, category=category, category_name=category_name, not_category_name=not_category_name, not_categories=not_categories, minimum_term_frequency=0, sort_by_dist=False, x_coords=characteristic_scores, y_coords=scores_scaled_for_charting, y_axis_labels=['More ' + not_category_name, 'Even', 'More ' + category_name] if y_axis_labels is None else y_axis_labels, x_label=x_label, y_label=term_scorer.get_name() if y_label is None else y_label, vertical_lines=[] if vertical_lines is None else vertical_lines, characteristic_scorer=characteristic_scorer, **kwargs)
    return html

class TermDocMatrix(TermDocMatrixWithoutCategories):
    """
    !!! to do: refactor score functions into classes
    """

    def __init__(self, X, mX, y, term_idx_store, category_idx_store, metadata_idx_store, unigram_frequency_path=None):
        """

        Parameters
        ----------
        X : csr_matrix
            term document matrix
        mX : csr_matrix
            metadata-document matrix
        y : np.array
            category index array
        term_idx_store : IndexStore
            Term indices
        category_idx_store : IndexStore
            Catgory indices
        metadata_idx : IndexStore
          Document metadata indices
        unigram_frequency_path : str or None
            Path to term frequency file.
        """
        TermDocMatrixWithoutCategories.__init__(self, X=X, mX=mX, term_idx_store=term_idx_store, metadata_idx_store=metadata_idx_store, unigram_frequency_path=unigram_frequency_path)
        self._y = y
        self._category_idx_store = category_idx_store

    def get_categories(self):
        """
        Returns
        -------
        list
        Category names
        """
        return self._category_idx_store.values()

    def get_num_categories(self) -> int:
        return len(self._category_idx_store)

    def old_get_term_freq_df(self):
        d = {'term': self._term_idx_store._i2val}
        for i, category in self._category_idx_store.items():
            d[category + ' freq'] = self._X[self._y == i].sum(axis=0).A1
        return pd.DataFrame(d).set_index('term')

    def get_all_category_frequencies(self, non_text: bool=False, term_ranker: Optional[TermRanker]=None) -> pd.Series:
        if term_ranker is None:
            term_ranker = AbsoluteFrequencyRanker(term_doc_matrix=self).set_non_text(non_text=non_text)
        return term_ranker.get_ranks().sum(axis=1)

    def get_freq_df(self, use_metadata=False, label_append=' freq'):
        if use_metadata:
            return self.get_metadata_freq_df(label_append)
        return self.get_term_freq_df(label_append)

    def get_term_freq_df(self, label_append=' freq'):
        """
        Parameters
        -------
        label_append : str

        Returns
        -------
        pd.DataFrame indexed on terms, with columns giving frequencies for each
        """
        '\n        row = self._row_category_ids()\n        newX = csr_matrix((self._X.data, (row, self._X.indices)))\n        return self._term_freq_df_from_matrix(newX)\n        '
        mat = self.get_term_freq_mat()
        return pd.DataFrame(mat, index=pd.Series(self.get_terms(), name='term'), columns=[str(c) + label_append for c in self.get_categories()])

    def get_term_freq_mat(self):
        """
        Returns
        -------
        np.array with columns as categories and rows as terms
        """
        freq_mat = np.zeros(shape=(self.get_num_terms(), self.get_num_categories()), dtype=self.get_term_doc_mat().dtype)
        for cat_i in range(self.get_num_categories()):
            freq_mat[:, cat_i] = self._X[self._y == cat_i, :].sum(axis=0)
        return freq_mat

    def get_term_count_mat(self, non_text: bool=False):
        """
        Parameters
        -------
        non_text : bool = False

        Returns
        -------
        np.array with columns as categories and rows as terms
        """
        freq_mat = np.zeros(shape=(self.get_num_terms(non_text=non_text), self.get_num_categories()), dtype=self.get_term_doc_mat(non_text=non_text).dtype)
        Xall = self.get_term_doc_mat(non_text=non_text)
        for cat_i in range(self.get_num_categories()):
            X = (Xall[self._y == cat_i, :] > 0).astype(int)
            freq_mat[:, cat_i] = X.sum(axis=0)
        return freq_mat

    def get_metadata_count_mat(self):
        """
        Returns
        -------
        np.array with columns as categories and rows as terms
        """
        freq_mat = np.zeros(shape=(self.get_num_metadata(), self.get_num_categories()), dtype=self.get_metadata_doc_mat().dtype)
        for cat_i in range(self.get_num_categories()):
            mX = (self._mX[self._y == cat_i, :] > 0).astype(int)
            freq_mat[:, cat_i] = mX.sum(axis=0)
        return freq_mat

    def get_term_doc_count_df(self, label_append=' freq'):
        """

        Returns
        -------
        pd.DataFrame indexed on terms, with columns the number of documents each term appeared in
        each category
        """
        mat = self.get_term_count_mat()
        return pd.DataFrame(mat, index=self.get_terms(), columns=[str(c) + label_append for c in self.get_categories()])

    def get_metadata_doc_count_df(self, label_append=' freq'):
        """

        Returns
        -------
        pd.DataFrame indexed on metadata, with columns the number of documents
        each metadata appeared in each category
        """
        mat = self.get_metadata_count_mat()
        return pd.DataFrame(mat, index=self.get_metadata(), columns=[str(c) + label_append for c in self.get_categories()])

    def _term_freq_df_from_matrix(self, catX, label_append=' freq'):
        return self._get_freq_df_using_idx_store(catX, self._term_idx_store, label_append=label_append)

    def _get_freq_df_using_idx_store(self, catX, idx_store, label_append=' freq'):
        d = {'term': idx_store._i2val}
        for idx, cat in self._category_idx_store.items():
            try:
                d[str(cat) + label_append] = catX[idx, :].A[0]
            except IndexError:
                self._fix_problem_when_final_category_index_has_no_terms(cat, catX, d, label_append)
        return pd.DataFrame(d).set_index('term')

    def _fix_problem_when_final_category_index_has_no_terms(self, cat, catX, d, label_append=' freq'):
        d[str(cat) + label_append] = np.zeros(catX.shape[1])

    def get_metadata_freq_df(self, label_append=' freq'):
        """
        Parameters
        -------
        label_append : str

        Returns
        -------
        pd.DataFrame indexed on metadata, with columns giving frequencies for each category
        """
        '\n        row = self._row_category_ids_for_meta()\n        newX = csr_matrix((self._mX.data, (row, self._mX.indices)))\n        return self._metadata_freq_df_from_matrix(newX, label_append)\n        '
        freq_mat = np.zeros(shape=(self.get_num_metadata(), self.get_num_categories()), dtype=self.get_metadata_doc_mat().dtype)
        mX = self._mX
        if any(np.isnan(mX.data)):
            mX = mX.copy()
            mX.data = np.nan_to_num(mX.data, copy=False)
        for cat_i in range(self.get_num_categories()):
            freq_mat[:, cat_i] = mX[self._y == cat_i, :].sum(axis=0)
        return pd.DataFrame(freq_mat, index=pd.Series(self.get_metadata(), name='term'), columns=[str(c) + label_append for c in self.get_categories()])

    def _row_category_ids(self):
        row = self._X.tocoo().row
        for i, cat in enumerate(self._y):
            row[row == i] = cat
        return row

    def _row_category_ids_for_meta(self):
        row = self._mX.tocoo().row
        for i, cat in enumerate(self._y):
            row[row == i] = cat
        return row

    def _metadata_freq_df_from_matrix(self, catX, label_append=' freq'):
        return self._get_freq_df_using_idx_store(catX, self._metadata_idx_store, label_append)

    def get_category_names_by_row(self):
        """
        Returns
        -------
        np.array of the category name for each row
        """
        return np.array(self.get_categories())[self._y]

    def _change_document_type_in_matrix(self, X, new_doc_ids):
        new_data = self._make_all_positive_data_ones(X.data)
        newX = csr_matrix((new_data, (new_doc_ids, X.indices)))
        return newX

    def keep_only_these_categories(self, categories, ignore_absences=False):
        """
        Non destructive category removal.

        Parameters
        ----------
        categories : list
            list of categories to keep
        ignore_absences : bool, False by default
            if categories does not appear, don't raise an error, just move on.

        Returns
        -------
        TermDocMatrix, new object with categories removed.
        """
        if not ignore_absences:
            assert set(self.get_categories()) & set(categories) == set(categories)
        categories_to_remove = [c for c in self.get_categories() if c not in categories]
        return self.remove_categories(categories_to_remove)

    def remove_categories(self, categories, ignore_absences=False):
        """
        Non-destructive category removal.

        Parameters
        ----------
        categories : list
            list of categories to remove
        ignore_absences : bool, False by default
            if categories does not appear, don't raise an error, just move on.

        Returns
        -------
        TermDocMatrix, new object with categories removed.
        """
        idx_to_delete_list = []
        existing_categories = set(self.get_categories())
        for category in categories:
            if category not in existing_categories:
                if not ignore_absences:
                    raise KeyError('Category %s not found' % category)
                continue
            idx_to_delete_list.append(self._category_idx_store.getidx(category))
        new_category_idx_store = self._category_idx_store.batch_delete_idx(idx_to_delete_list)
        columns_to_delete = np.nonzero(np.isin(self._y, idx_to_delete_list))
        new_X = delete_columns(self._X.T, columns_to_delete).T
        new_mX = delete_columns(self._mX.T, columns_to_delete).T
        intermediate_y = self._y[~np.isin(self._y, idx_to_delete_list)]
        old_y_to_new_y = [self._category_idx_store.getidx(x) for x in new_category_idx_store._i2val]
        new_y = np.array([old_y_to_new_y.index(i) if i in old_y_to_new_y else None for i in range(intermediate_y.max() + 1)])[intermediate_y]
        new_metadata_idx_store = self._metadata_idx_store
        if self.metadata_in_use():
            meta_idx_to_delete = np.nonzero(new_mX.sum(axis=0).A1 == 0)[0]
            new_metadata_idx_store = self._metadata_idx_store.batch_delete_idx(meta_idx_to_delete)
            new_mX = delete_columns(new_mX, meta_idx_to_delete)
        new_term_idx_store = self._term_idx_store
        if self.get_num_terms() > 0:
            term_idx_to_delete = np.nonzero(new_X.sum(axis=0).A1 == 0)[0]
            new_term_idx_store = new_term_idx_store.batch_delete_idx(term_idx_to_delete)
            new_X = delete_columns(new_X, term_idx_to_delete)
        term_doc_mat_to_ret = self._make_new_term_doc_matrix(new_X, new_mX, new_y.astype(int), new_term_idx_store, new_category_idx_store, new_metadata_idx_store, ~np.isin(self._y, idx_to_delete_list))
        return term_doc_mat_to_ret

    def remove_terms_by_indices(self, idx_to_delete_list, non_text=False):
        """
        Parameters
        ----------
        idx_to_delete_list, list
        non_text, bool

        Returns
        -------
        TermDocMatrix
        """
        new_X, new_idx_store = self._get_X_after_delete_terms(idx_to_delete_list, non_text)
        return self._make_new_term_doc_matrix(new_X=self._X if non_text else new_X, new_mX=new_X if non_text else self._mX, new_y=self._y, new_term_idx_store=self._term_idx_store if non_text else new_idx_store, new_category_idx_store=self._category_idx_store, new_metadata_idx_store=new_idx_store if non_text else self._metadata_idx_store, new_y_mask=self._y == self._y)

    def change_category_names(self, new_category_names):
        if len(new_category_names) != self.get_num_categories():
            raise Exception('The number of category names passed (%s) needs to equal the number of categories in the corpus (%s).' % (len(new_category_names), self.get_num_categories()))
        return self._make_new_term_doc_matrix(new_category_idx_store=IndexStoreFromList.build(new_category_names))

    def _make_new_term_doc_matrix(self, new_X=None, new_mX=None, new_y=None, new_term_idx_store=None, new_category_idx_store=None, new_metadata_idx_store=None, new_y_mask=None):
        X, mX, y = self._update_X_mX_y(new_X, new_mX, new_y, new_y_mask)
        return TermDocMatrix(X=X, mX=mX, y=y, term_idx_store=new_term_idx_store if new_term_idx_store is not None else self._term_idx_store, category_idx_store=new_category_idx_store if new_category_idx_store is not None else self._category_idx_store, metadata_idx_store=new_metadata_idx_store if new_metadata_idx_store is not None else self._metadata_idx_store, unigram_frequency_path=self._unigram_frequency_path)

    def _update_X_mX_y(self, new_X, new_mX, new_y, new_y_mask):
        X = new_X if new_X is not None else self._X
        mX = new_mX if new_mX is not None else self._mX
        y = new_y if new_y is not None else self._y
        if new_y_mask is not None:
            if len(y) == len(new_y_mask):
                y = y[new_y_mask]
            if X.shape[0] == len(new_y_mask):
                X = X[new_y_mask, :]
            if mX.shape[0] == len(new_y_mask):
                mX = mX[new_y_mask, :]
        return (X, mX, y)

    def get_posterior_mean_ratio_scores(self, category):
        """ Computes posterior mean score.
        Parameters
        ----------
        category : str
            category name to score

        Returns
        -------
            np.array
        """
        return self._get_posterior_mean_ratio_from_category(category)

    def get_corner_scores(self, category):
        """ Computes corner score, which is inversely correlated
        to the Rudder score to the nearest upper-left or lower-right corner.
        Parameters
        ----------
        category : str
            category name to score

        Returns
        -------
            np.array
        """
        return CornerScore.get_scores(*self._get_catetgory_and_non_category_word_counts(category))

    def get_rudder_scores(self, category):
        """ Computes Rudder score.
        Parameters
        ----------
        category : str
            category name to score

        Returns
        -------
            np.array
        """
        category_percentiles = self._get_term_percentiles_in_category(category)
        not_category_percentiles = self._get_term_percentiles_not_in_category(category)
        rudder_scores = self._get_rudder_scores_for_percentile_pair(category_percentiles, not_category_percentiles)
        return rudder_scores

    def _get_posterior_mean_ratio_from_category(self, category):
        cat_word_counts, not_cat_word_counts = self._get_catetgory_and_non_category_word_counts(category)
        return self._get_posterior_mean_ratio_from_counts(cat_word_counts, not_cat_word_counts)

    def _get_posterior_mean_ratio_from_counts(self, cat_word_counts, not_cat_word_counts):
        cat_posterior_mean = self._get_posterior_mean_from_counts(cat_word_counts, not_cat_word_counts)
        not_cat_posterior_mean = self._get_posterior_mean_from_counts(not_cat_word_counts, cat_word_counts)
        return np.log(cat_posterior_mean / not_cat_posterior_mean) / np.log(2)

    def _get_posterior_mean_from_counts(self, cat_word_counts, not_cat_word_counts):
        a = cat_word_counts
        b = cat_word_counts.sum() - cat_word_counts
        beta = (cat_word_counts.sum() + not_cat_word_counts.sum()) / (cat_word_counts + not_cat_word_counts) - 1
        posterior_mean = (1.0 + a) / (1.0 + a + b + beta)
        return posterior_mean

    def get_logistic_regression_coefs_l2(self, category, clf=RidgeClassifierCV()):
        """ Computes l2-penalized logistic regression score.
        Parameters
        ----------
        category : str
            category name to score

        category : str
            category name to score
        Returns
        -------
            (coefficient array, accuracy, majority class baseline accuracy)
        """
        try:
            from sklearn.cross_validation import cross_val_predict
        except:
            from sklearn.model_selection import cross_val_predict
        y = self._get_mask_from_category(category)
        X = TfidfTransformer().fit_transform(self._X)
        clf.fit(X, y)
        y_hat = cross_val_predict(clf, X, y)
        acc, baseline = self._get_accuracy_and_baseline_accuracy(y, y_hat)
        return (clf.coef_[0], acc, baseline)

    def _get_accuracy_and_baseline_accuracy(self, y, y_hat):
        acc = sum(y_hat == y) * 1.0 / len(y)
        baseline = max([sum(y), len(y) - sum(y)]) * 1.0 / len(y)
        return (acc, baseline)

    def get_logistic_regression_coefs_l1(self, category, clf=LassoCV(alphas=[0.1, 0.001], max_iter=10000, n_jobs=-1)):
        """ Computes l1-penalized logistic regression score.
        Parameters
        ----------
        category : str
            category name to score

        Returns
        -------
            (coefficient array, accuracy, majority class baseline accuracy)
        """
        try:
            from sklearn.cross_validation import cross_val_predict
        except:
            from sklearn.model_selection import cross_val_predict
        y = self._get_mask_from_category(category)
        y_continuous = self._get_continuous_version_boolean_y(y)
        X = self._X
        clf.fit(X, y_continuous)
        y_hat = cross_val_predict(clf, X, y_continuous) > 0
        acc, baseline = self._get_accuracy_and_baseline_accuracy(y, y_hat)
        clf.fit(X, y_continuous)
        return (clf.coef_, acc, baseline)

    def get_regression_coefs(self, category, clf=ElasticNet()):
        """ Computes regression score of tdfidf transformed features
        Parameters
        ----------
        category : str
            category name to score
        clf : sklearn regressor

        Returns
        -------
        coefficient array
        """
        self._fit_tfidf_model(category, clf)
        return clf.coef_

    def get_logreg_coefs(self, category, clf=LogisticRegression()):
        """ Computes regression score of tdfidf transformed features
        Parameters
        ----------
        category : str
            category name to score
        clf : sklearn regressor

        Returns
        -------
        coefficient array
        """
        self._fit_tfidf_model(category, clf)
        return clf.coef_[0]

    def _fit_tfidf_model(self, category, clf):
        y = self._get_mask_from_category(category)
        y_continuous = self._get_continuous_version_boolean_y(y)
        X = TfidfTransformer().fit_transform(self._X)
        clf.fit(X, y_continuous)

    def _get_continuous_version_boolean_y(self, y_bool):
        return 1000 * (y_bool * 2.0 - 1)

    def get_scaled_f_scores(self, category, scaler_algo=DEFAULT_SCALER_ALGO, beta=DEFAULT_BETA):
        """ Computes scaled-fscores
        Parameters
        ----------
        category : str
            category name to score
        scaler_algo : str
          Function that scales an array to a range \\in [0 and 1]. Use 'percentile', 'normcdf'. Default.
        beta : float
            Beta in (1+B^2) * (Scale(P(w|c)) * Scale(P(c|w)))/(B^2*Scale(P(w|c)) + Scale(P(c|w))). Default.
        Returns
        -------
            np.array of harmonic means of scaled P(word|category) and scaled P(category|word)
        """
        assert beta > 0
        cat_word_counts, not_cat_word_counts = self._get_catetgory_and_non_category_word_counts(category)
        scores = self._get_scaled_f_score_from_counts(cat_word_counts, not_cat_word_counts, scaler_algo, beta)
        return np.array(scores)

    def _get_scaled_f_score_from_counts(self, cat_word_counts, not_cat_word_counts, scaler_algo, beta=DEFAULT_BETA):
        """
        scaler = self._get_scaler_function(scaler_algo)
        p_word_given_category = cat_word_counts.astype(np.float64) / cat_word_counts.sum()
        p_category_given_word = cat_word_counts.astype(np.float64) / (cat_word_counts + not_cat_word_counts)
        scores             = self._computer_harmoic_mean_of_probabilities_over_non_zero_in_category_count_terms(
            cat_word_counts, p_category_given_word, p_word_given_category, scaler
        )
        """
        return ScaledFScore.get_scores(cat_word_counts, not_cat_word_counts, scaler_algo, beta=beta)

    def _computer_harmoic_mean_of_probabilities_over_non_zero_in_category_count_terms(self, cat_word_counts, p_category_given_word, p_word_given_category, scaler):
        df = pd.DataFrame({'cat_word_counts': cat_word_counts, 'p_word_given_category': p_word_given_category, 'p_category_given_word': p_category_given_word})
        df_with_count = df[df['cat_word_counts'] > 0]
        df_with_count['scale p_word_given_category'] = scaler(df_with_count['p_word_given_category'])
        df_with_count['scale p_category_given_word'] = scaler(df_with_count['p_category_given_word'])
        df['scale p_word_given_category'] = 0
        df.loc[df_with_count.index, 'scale p_word_given_category'] = df_with_count['scale p_word_given_category']
        df['scale p_category_given_word'] = 0
        df.loc[df_with_count.index, 'scale p_category_given_word'] = df_with_count['scale p_category_given_word']
        score = hmean([df_with_count['scale p_category_given_word'], df_with_count['scale p_word_given_category']])
        df['score'] = 0
        df.loc[df_with_count.index, 'score'] = score
        return df['score']

    def _get_scaler_function(self, scaler_algo):
        scaler = None
        if scaler_algo == 'percentile':
            scaler = lambda x: rankdata(x).astype(np.float64) / len(x)
        elif scaler_algo == 'normcdf':
            scaler = lambda x: norm.cdf(x, x.mean(), x.std())
        elif scaler_algo == 'none':
            scaler = lambda x: x
        else:
            raise InvalidScalerException('Invalid scaler alogrithm.  Must be either percentile or normcdf.')
        return scaler

    def get_fisher_scores(self, category):
        cat_word_counts, not_cat_word_counts = self._get_catetgory_and_non_category_word_counts(category)
        return self._get_fisher_scores_from_counts(cat_word_counts, not_cat_word_counts)

    def get_fisher_scores_vs_background(self):
        """
        Returns
        -------
            pd.DataFrame of fisher scores vs background
        """
        df = self.get_term_and_background_counts()
        odds_ratio, p_values = self._get_fisher_scores_from_counts(df['corpus'], df['background'])
        df['Odds ratio'] = odds_ratio
        df['Bonferroni-corrected p-values'] = p_values * len(df)
        df.sort_values(by=['Bonferroni-corrected p-values', 'Odds ratio'], ascending=[True, False])
        return df

    def get_posterior_mean_ratio_scores_vs_background(self):
        """
        Returns
        -------
            pd.DataFrame of posterior mean  scores vs background
        """
        df = self.get_term_and_background_counts()
        df['Log Posterior Mean Ratio'] = self._get_posterior_mean_ratio_from_counts(df['corpus'], df['background'])
        return df.sort_values('Log Posterior Mean Ratio', ascending=False)

    def _get_catetgory_and_non_category_word_counts(self, category):
        self._validate_category(category)
        cat_word_counts = self._X[self._get_mask_from_category(category)].sum(axis=0).A1
        not_cat_word_counts = self._X[self._y != self._category_idx_store.getidx(category)].sum(axis=0).A1
        return (cat_word_counts, not_cat_word_counts)

    def _validate_category(self, category):
        if category not in self.get_categories():
            raise Exception('Invalid category: %s, valid: %s' % (category, self.get_categories()))

    def _get_fisher_scores_from_counts(self, cat_word_counts, not_cat_word_counts):
        cat_not_word_counts = cat_word_counts.sum() - cat_word_counts
        not_cat_not_word_counts = not_cat_word_counts.sum() - not_cat_word_counts

        def do_fisher_exact(x):
            return fisher_exact([[x[0], x[1]], [x[2], x[3]]], alternative='greater')
        odds_ratio, p_values = np.apply_along_axis(do_fisher_exact, 0, np.array([cat_word_counts, cat_not_word_counts, not_cat_word_counts, not_cat_not_word_counts]))
        return (odds_ratio, p_values)

    def get_rudder_scores_vs_background(self):
        """
        Returns
        -------
        pd.DataFrame of rudder scores vs background
        """
        df = self.get_term_and_background_counts()
        corpus_percentiles = self._get_percentiles_from_freqs(df['corpus'])
        background_percentiles = self._get_percentiles_from_freqs(df['background'])
        df['Rudder'] = self._get_rudder_scores_for_percentile_pair(corpus_percentiles, background_percentiles)
        df = df.sort_values(by='Rudder', ascending=True)
        return df

    def _rescale_labels_to_neg_one_pos_one(self, category):
        return self._get_mask_from_category(category) * 2 - 1

    def _get_rudder_scores_for_percentile_pair(self, category_percentiles, not_category_percentiles):
        return np.linalg.norm(np.array([1, 0]) - np.array(list(zip(category_percentiles, not_category_percentiles))), axis=1)

    def _get_term_percentiles_in_category(self, category):
        mask = self._get_mask_from_category(category)
        return self._get_frequency_percentiles(mask)

    def _get_mask_from_category(self, category):
        return self._y == self._category_idx_store.getidx(category)

    def _get_term_percentiles_not_in_category(self, category):
        mask = self._y != self._category_idx_store.getidx(category)
        return self._get_frequency_percentiles(mask)

    def _get_frequency_percentiles(self, mask):
        freqs = self._X[mask].sum(axis=0).A1
        percentiles = self._get_percentiles_from_freqs(freqs)
        return percentiles

    def _get_percentiles_from_freqs(self, freqs):
        return rankdata(freqs) / len(freqs)

    def get_term_category_frequencies(self, scatterchartdata):
        """
        Applies the ranker in scatterchartdata to term-category frequencies.

        Parameters
        ----------
        scatterchartdata : ScatterChartData

        Returns
        -------
        pd.DataFrame
        """
        term_ranker = scatterchartdata.term_ranker(self)
        if scatterchartdata.use_non_text_features:
            term_ranker.use_non_text_features()
        return term_ranker.get_ranks()

    def get_category_ids(self):
        """
        Returns array of category ids

        Returns
        -------
        np.array
        """
        return self._y

    def get_category_index_store(self):
        """
        Returns IndexStore object mapping categories to ids

        Returns
        -------
        IndexStore
        """
        return self._category_idx_store

    def recategorize(self, new_categories: Union[List, Callable[['TermDocMatrix'], List]]):
        """
        Parameters
        ----------
        new_categories : array like or function which takes TermDocMatric and returns something list like
        String names of new categories. Length should be equal to number of documents

        Returns
        -------
        TermDocMatrix
        """
        if callable(new_categories):
            new_categories = new_categories(self)
        assert len(new_categories) == self.get_num_docs()
        new_category_idx_store = IndexStoreFromList.build(set(new_categories))
        new_y = np.array(new_category_idx_store.getidxstrictbatch(new_categories))
        new_tdm = self._make_new_term_doc_matrix(self._X, self._mX, new_y, self._term_idx_store, new_category_idx_store, self._metadata_idx_store, new_y == new_y)
        return new_tdm

    def use_external_metadata_lists(self, metadata_lists):
        """
        Takes a list of string lists. Each list corresponds to metadata to associate its corresponding document.
        :param metadata: List[List[str]]
        :return: new TermDocMatrix
        """
        metadata_index_store = IndexStore()
        metadata_csr_factory = CSRMatrixFactory()
        assert len(metadata_lists) == self.get_num_docs()
        for doc_i, metadata_list in enumerate(metadata_lists):
            for metadatum in metadata_list:
                metadata_csr_factory[doc_i, metadata_index_store.getidx(metadatum)] = 1
        return self._make_new_term_doc_matrix(new_mX=metadata_csr_factory.get_csr_matrix(dtype=int), new_metadata_idx_store=metadata_index_store, new_y_mask=self._y == self._y)

    def use_doc_labeled_terms_as_metadata(self, doc_labels, separator='_', replace_metadata=True):
        """
        Makes the metadata of a new TermDocMatrix a copy of the term-document matrix, except each term is prefixed
        by its document's label followed by the separator.

        :param doc_labels: list[str], should be the same size as the number of documents in the TermDocMatrix.
        :param separator: str, default is '_'
        :return: self
        """
        assert len(doc_labels) == self.get_num_docs()
        doc_labels = np.array(doc_labels)
        terms_in_corpus = np.array(self._term_idx_store.values())
        new_metadata_list = []
        new_meta_X = None
        ordered_doc_labels = list(sorted(set(doc_labels)))
        X = self._X
        if replace_metadata:
            X = self._X
        for doc_label in ordered_doc_labels:
            label_doc_mask = doc_labels == doc_label
            label_X = X[label_doc_mask, :]
            label_term_mask = (X.sum(axis=0) > 0).A1
            label_X = label_X[:, label_term_mask]
            cols_to_pad = len(new_metadata_list)
            new_metadata_list += [doc_label + separator + term for term in terms_in_corpus[label_term_mask]]
            if new_meta_X is None:
                new_meta_X = label_X
            else:
                label_X_pad = CSRMatrixFactory().set_last_col_idx(cols_to_pad - 1).set_last_row_idx(sum(label_doc_mask) - 1).get_csr_matrix()
                padded_label_X = scipy.sparse.hstack([label_X_pad, label_X])
                new_meta_X.resize(new_meta_X.shape[0], padded_label_X.shape[1])
                new_meta_X = scipy.sparse.vstack([new_meta_X, padded_label_X])
        new_metadata_idx_store = IndexStoreFromList.build(new_metadata_list)
        new_meta_X = new_meta_X.tocsr()
        new_mX = CSRMatrixFactory().set_last_col_idx(new_meta_X.shape[1] - 1).set_last_row_idx(new_meta_X.shape[0] - 1).get_csr_matrix().tolil()
        start_row = 0
        for doc_label in ordered_doc_labels:
            label_doc_mask = doc_labels == doc_label
            num_rows = sum(label_doc_mask)
            new_mX[label_doc_mask, :] = new_meta_X[start_row:start_row + num_rows, :]
            start_row += num_rows
        new_mX = new_mX.tocsr()
        new_tdm = self._make_new_term_doc_matrix(self._X, new_mX, self._y, self._term_idx_store, self._category_idx_store, new_metadata_idx_store, self._y == self._y)
        return new_tdm

    def use_categories_as_metadata(self):
        """
        Returns a TermDocMatrix which is identical to self except the metadata values are now identical to the
         categories present.

        :return: TermDocMatrix
        """
        new_metadata = self._categories_to_metadata_factory()
        new_tdm = self._make_new_term_doc_matrix(self._X, new_metadata, self._y, self._term_idx_store, self._category_idx_store, copy(self._category_idx_store), self._y == self._y)
        return new_tdm

    def use_categories_as_metadata_and_replace_terms(self):
        """
        Returns a TermDocMatrix which is identical to self except the metadata values are now identical to the
         categories present and term-doc-matrix is now the metadata matrix.

        :return: TermDocMatrix
        """
        new_metadata = self._categories_to_metadata_factory()
        new_tdm = self._make_new_term_doc_matrix(new_X=self._mX, new_mX=new_metadata, new_y=self._y, new_term_idx_store=self._metadata_idx_store, new_category_idx_store=self._category_idx_store, new_metadata_idx_store=copy(self._category_idx_store), new_y_mask=self._y == self._y)
        return new_tdm

    def _categories_to_metadata_factory(self):
        new_metadata_factory = CSRMatrixFactory()
        for i, category_idx in enumerate(self.get_category_ids()):
            new_metadata_factory[i, category_idx] = 1
        new_metadata = new_metadata_factory.get_csr_matrix()
        return new_metadata

    def copy_terms_to_metadata(self):
        """
        Returns a TermDocMatrix which is identical to self except the metadata values are now identical to the
        term document matrix.

        :return: TermDocMatrix
        """
        return self._make_new_term_doc_matrix(new_mX=copy(self._X), new_metadata_idx_store=copy(self._term_idx_store), new_y_mask=self._y == self._y)

    def get_num_categories(self):
        """
        Returns the number of categories in the term document matrix
        :return: int
        """
        return len(self.get_categories())

    def remove_terms_used_in_less_than_num_categories(self, threshold, use_metadata=False):
        term_mask = (self.get_freq_df(use_metadata=use_metadata).values > 0).sum(axis=1) < threshold
        term_indices_to_remove = np.where(term_mask)[0]
        return self.remove_terms_by_indices(term_indices_to_remove, use_metadata)

    def rename_metadata(self, old_to_new_vals: List[Tuple[str, str]], policy: MetadataReplacementRetentionPolicy=MetadataReplacementRetentionPolicy.KEEP_ONLY_NEW) -> Self:
        new_mX, new_metadata_idx_store = self._remap_metadata(old_to_new_vals)
        return self._make_new_term_doc_matrix(new_X=self._X, new_mX=new_mX, new_y=self._y, new_term_idx_store=self._term_idx_store, new_category_idx_store=self._category_idx_store, new_metadata_idx_store=new_metadata_idx_store, new_y_mask=self._y == self._y)

def get_all_category_frequencies(self, non_text: bool=False, term_ranker: Optional[TermRanker]=None) -> pd.Series:
    if term_ranker is None:
        term_ranker = AbsoluteFrequencyRanker(term_doc_matrix=self).set_non_text(non_text=non_text)
    return term_ranker.get_ranks().sum(axis=1)

def get_term_category_frequencies(self, scatterchartdata):
    """
        Applies the ranker in scatterchartdata to term-category frequencies.

        Parameters
        ----------
        scatterchartdata : ScatterChartData

        Returns
        -------
        pd.DataFrame
        """
    term_ranker = scatterchartdata.term_ranker(self)
    if scatterchartdata.use_non_text_features:
        term_ranker.use_non_text_features()
    return term_ranker.get_ranks()

class PriorFactory(object):

    def __init__(self, term_doc_mat, category=None, not_categories=None, starting_count=0.0001, term_ranker=AbsoluteFrequencyRanker):
        """
		Parameters
		----------
		term_doc_mat : TermDocMatrix
			Basis for scores
		category : str
			Category to score. Only important when finding neutral categories.
		not_categories : list
		  List of categories to score against.  If None (the default) the list
		   is the remaining
		starting_count : float
			Default 0.01. Add this count to each term seen. If zero, terms not in background counts will be removed.
		term_ranker : TermRanker
			Function to get term frequency convention_df
		"""
        self.term_doc_mat = term_doc_mat
        self.relevant_categories = []
        if category:
            self.category = category
            assert category in term_doc_mat.get_categories()
            self.relevant_categories += [category]
        else:
            self.category = None
        if not_categories == None:
            not_categories = [c for c in term_doc_mat.get_categories() if c != category]
        else:
            assert set(not_categories) - set(term_doc_mat.get_categories()) == set()
        self.relevant_categories += not_categories
        self.not_categories = not_categories
        self.starting_count = starting_count
        self.term_ranker = term_ranker(term_doc_mat)
        self.use_preset_term_frequencies = False
        self.priors = pd.Series(np.zeros(len(self.term_doc_mat.get_terms())), index=term_doc_mat.get_terms())

    def use_general_term_frequencies(self):
        """
		Returns
		-------
		PriorFactory
		"""
        tdf = self._get_relevant_term_freq()
        bg_df = self.term_doc_mat.get_term_and_background_counts()[['background']]
        bg_df = pd.merge(tdf, bg_df, left_index=True, right_index=True, how='left').fillna(0.0)
        self._store_priors_from_background_dataframe(bg_df)
        return self

    def _get_relevant_term_freq(self):
        return pd.DataFrame({'corpus': self.term_ranker.get_ranks(label_append=' freq')[[str(c) + ' freq' for c in self.relevant_categories]].sum(axis=1)})

    def _store_priors_from_background_dataframe(self, bg_df):
        self.priors += bg_df.reindex(self.priors.index).fillna(0)['background']

    def use_custom_term_frequencies(self, custom_term_frequencies):
        """
		Parameters
		----------
		pd.Series
		term -> frequency
		Returns
		-------
		PriorFactory
		"""
        self.priors += custom_term_frequencies.reindex(self.priors.index).fillna(0)
        return self

    def use_categories(self, categories):
        self.priors += self.term_ranker.get_ranks()[[str(c) + ' freq' for c in categories]].sum(axis=1)
        return self

    def use_all_categories(self):
        """
		Returns
		-------
		PriorFactory
		"""
        term_df = self.term_ranker.get_ranks()
        self.priors += term_df.sum(axis=1).fillna(0.0)
        return self

    def use_neutral_categories(self):
        """
		Returns
		-------
		PriorFactory
		"""
        term_df = self.term_ranker.get_ranks(label_append=' freq')
        self.priors += term_df[[str(c) + ' freq' for c in self._get_neutral_categories()]].sum(axis=1)
        return self

    def drop_neutral_categories_from_corpus(self):
        """
		Returns
		-------
		PriorFactory
		"""
        neutral_categories = self._get_neutral_categories()
        self.term_doc_mat = self.term_doc_mat.remove_categories(neutral_categories)
        self._reindex_priors()
        return self

    def _get_neutral_categories(self):
        return [c for c in self.term_doc_mat.get_categories() if c not in self.relevant_categories]

    def _reindex_priors(self):
        self.priors = self.priors.reindex(self.term_doc_mat.get_terms()).dropna()

    def drop_unused_terms(self):
        """
		Returns
		-------
		PriorFactory
		"""
        self.term_doc_mat = self.term_doc_mat.remove_terms(set(self.term_doc_mat.get_terms()) - set(self.priors.index))
        self._reindex_priors()
        return self

    def drop_zero_priors(self):
        """
		Returns
		-------
		PriorFactory
		"""
        self.term_doc_mat = self.term_doc_mat.remove_terms(self.priors[self.priors == 0].index)
        self._reindex_priors()
        return self

    def align_to_target(self, target_term_doc_mat):
        """
		Parameters
		----------
		target_term_doc_mat : TermDocMatrix

		Returns
		-------
		PriorFactory
		"""
        self.priors = self.priors[target_term_doc_mat.get_terms()].fillna(0)
        return self

    def build(self):
        """
		Returns
		-------
		pd.Series, TermDocMatrix
		"""
        return (self.get_priors(), self.term_doc_mat)

    def get_priors(self):
        """
		Returns
		-------
		pd.Series
		"""
        priors = self.priors
        priors[~np.isfinite(priors)] = 0
        priors += self.starting_count
        return priors

def use_neutral_categories(self):
    """
		Returns
		-------
		PriorFactory
		"""
    term_df = self.term_ranker.get_ranks(label_append=' freq')
    self.priors += term_df[[str(c) + ' freq' for c in self._get_neutral_categories()]].sum(axis=1)
    return self

def drop_neutral_categories_from_corpus(self):
    """
		Returns
		-------
		PriorFactory
		"""
    neutral_categories = self._get_neutral_categories()
    self.term_doc_mat = self.term_doc_mat.remove_categories(neutral_categories)
    self._reindex_priors()
    return self

def drop_unused_terms(self):
    """
		Returns
		-------
		PriorFactory
		"""
    self.term_doc_mat = self.term_doc_mat.remove_terms(set(self.term_doc_mat.get_terms()) - set(self.priors.index))
    self._reindex_priors()
    return self

def drop_zero_priors(self):
    """
		Returns
		-------
		PriorFactory
		"""
    self.term_doc_mat = self.term_doc_mat.remove_terms(self.priors[self.priors == 0].index)
    self._reindex_priors()
    return self

class AutoTermSelector(object):
    """
	Reduce corpus to the X most important terms.  Great for plotting a big corpus.
	Will return between X/2 and X terms.

	Returns the terms with the X highest absolute scores, background corpus scores, and term frequencies.
	"""

    @staticmethod
    def reduce_terms(term_doc_matrix, scores, num_term_to_keep=None):
        """
		Parameters
		----------
		term_doc_matrix: TermDocMatrix or descendant
		scores: array-like
			Same length as number of terms in TermDocMatrix.
		num_term_to_keep: int, default=4000.
			Should be> 0. Number of terms to keep. Will keep between num_terms_to_keep/2 and num_terms_to_keep.

		Returns
		-------
		TermDocMatrix stripped of non-important terms., array of scores
		"""
        terms_to_show = AutoTermSelector.get_selected_terms(term_doc_matrix, scores, num_term_to_keep)
        return term_doc_matrix.remove_terms(set(term_doc_matrix.get_terms()) - set(terms_to_show))

    @staticmethod
    def get_selected_terms(term_doc_matrix, scores, num_term_to_keep=None):
        """
		Parameters
		----------
		term_doc_matrix: TermDocMatrix or descendant
		scores: array-like
			Same length as number of terms in TermDocMatrix.
		num_term_to_keep: int, default=4000.
			Should be> 0. Number of terms to keep. Will keep between num_terms_to_keep/2 and num_terms_to_keep.

		Returns
		-------
		set, terms that should be shown
		"""
        num_term_to_keep = AutoTermSelector._add_default_num_terms_to_keep(num_term_to_keep)
        term_doc_freq = term_doc_matrix.get_term_freq_df()
        term_doc_freq['count'] = term_doc_freq.sum(axis=1)
        term_doc_freq['score'] = scores
        score_terms = AutoTermSelector._get_score_terms(num_term_to_keep, term_doc_freq)
        background_terms = AutoTermSelector._get_background_terms(num_term_to_keep, term_doc_matrix)
        frequent_terms = AutoTermSelector._get_frequent_terms(num_term_to_keep, term_doc_freq)
        terms_to_show = score_terms.union(background_terms).union(frequent_terms)
        return terms_to_show

    @staticmethod
    def _get_frequent_terms(num_term_to_keep, term_doc_freq):
        return term_doc_freq.sort_values(by='count', ascending=False).iloc[:int(0.125 * num_term_to_keep)].index

    @staticmethod
    def _get_background_terms(num_term_to_keep, term_doc_matrix):
        return term_doc_matrix.get_scaled_f_scores_vs_background().iloc[:int(0.375 * num_term_to_keep)].index

    @staticmethod
    def _get_score_terms(num_term_to_keep, term_doc_freq):
        sorted_tdf = term_doc_freq.sort_values(by='score', ascending=False)
        return sorted_tdf.iloc[:int(0.25 * num_term_to_keep)].index.union(sorted_tdf.iloc[-int(0.25 * num_term_to_keep):].index)

    @staticmethod
    def _add_default_num_terms_to_keep(num_term_to_keep):
        if num_term_to_keep is None:
            num_term_to_keep = 4000
        return num_term_to_keep

@staticmethod
def reduce_terms(term_doc_matrix, scores, num_term_to_keep=None):
    """
		Parameters
		----------
		term_doc_matrix: TermDocMatrix or descendant
		scores: array-like
			Same length as number of terms in TermDocMatrix.
		num_term_to_keep: int, default=4000.
			Should be> 0. Number of terms to keep. Will keep between num_terms_to_keep/2 and num_terms_to_keep.

		Returns
		-------
		TermDocMatrix stripped of non-important terms., array of scores
		"""
    terms_to_show = AutoTermSelector.get_selected_terms(term_doc_matrix, scores, num_term_to_keep)
    return term_doc_matrix.remove_terms(set(term_doc_matrix.get_terms()) - set(terms_to_show))

class FourSquareAxes(SemioticSquare):
    """
    This creates a semiotic square where the complex term is considered the "top" category, the
    neutral term is the "bottom" category, the positive dexis is the "left" category, and the
    negative dexis is the "right" category.
    """

    def __init__(self, term_doc_matrix, left_categories, right_categories, top_categories, bottom_categories, left_category_name=None, right_category_name=None, top_category_name=None, bottom_category_name=None, x_scorer=RankDifference(), y_scorer=RankDifference(), term_ranker=AbsoluteFrequencyRanker, labels=None):
        for param in [left_categories, right_categories, top_categories, bottom_categories]:
            assert type(param) == list
            assert set(param) - set(term_doc_matrix.get_categories()) == set()
            assert len(param) > 0
        self.term_doc_matrix_ = term_doc_matrix
        self._labels = labels
        self.left_category_name_ = left_category_name if left_category_name is not None else left_categories[0]
        self.right_category_name_ = right_category_name if right_category_name is not None else right_categories[0]
        self.top_category_name_ = top_category_name if top_category_name is not None else top_categories[0]
        self.bottom_category_name_ = bottom_category_name if bottom_category_name is not None else bottom_categories[0]
        self.x_scorer_ = x_scorer
        self.y_scorer_ = y_scorer
        self.term_ranker_ = term_ranker
        self.left_categories_, self.right_categories_, self.top_categories_, self.bottom_categories_ = (left_categories, right_categories, top_categories, bottom_categories)
        self.axes = self._build_axes()
        self.lexicons = self._build_lexicons()

    def _get_all_categories(self):
        return self.left_categories_ + self.right_categories_ + self.top_categories_ + self.bottom_categories_

    def _build_axes(self, scorer=None):
        tdf = self.term_ranker_(self.term_doc_matrix_).get_ranks()
        tdf.columns = [c[:-5] for c in tdf.columns]
        tdf = tdf[self._get_all_categories()]
        counts = tdf.sum(axis=1)
        tdf['x'] = self.x_scorer_.get_scores(tdf[self.left_categories_].sum(axis=1), tdf[self.right_categories_].sum(axis=1))
        tdf.loc[np.isnan(tdf['x']), 'x'] = self.x_scorer_.get_default_score()
        tdf['y'] = self.y_scorer_.get_scores(tdf[self.top_categories_].sum(axis=1), tdf[self.bottom_categories_].sum(axis=1))
        tdf.loc[np.isnan(tdf['y']), 'y'] = self.y_scorer_.get_default_score()
        tdf['counts'] = counts
        return tdf[['x', 'y', 'counts']]

    def get_labels(self):
        a = self._get_default_a_label()
        b = self._get_default_b_label()
        default_labels = {'a': a, 'not_a': '' if a == '' else 'Not ' + a, 'b': b, 'not_b': '' if b == '' else 'Not ' + b, 'a_and_b': self.top_category_name_, 'not_a_and_not_b': self.bottom_category_name_, 'a_and_not_b': self.left_category_name_, 'b_and_not_a': self.right_category_name_}
        labels = self._labels
        if labels is None:
            labels = {}
        return {name + '_label': labels.get(name, default_labels[name]) for name in default_labels}

    def _get_default_b_label(self):
        return ''

    def _get_default_a_label(self):
        return ''

def __init__(self, term_doc_matrix, left_categories, right_categories, top_categories, bottom_categories, left_category_name=None, right_category_name=None, top_category_name=None, bottom_category_name=None, x_scorer=RankDifference(), y_scorer=RankDifference(), term_ranker=AbsoluteFrequencyRanker, labels=None):
    for param in [left_categories, right_categories, top_categories, bottom_categories]:
        assert type(param) == list
        assert set(param) - set(term_doc_matrix.get_categories()) == set()
        assert len(param) > 0
    self.term_doc_matrix_ = term_doc_matrix
    self._labels = labels
    self.left_category_name_ = left_category_name if left_category_name is not None else left_categories[0]
    self.right_category_name_ = right_category_name if right_category_name is not None else right_categories[0]
    self.top_category_name_ = top_category_name if top_category_name is not None else top_categories[0]
    self.bottom_category_name_ = bottom_category_name if bottom_category_name is not None else bottom_categories[0]
    self.x_scorer_ = x_scorer
    self.y_scorer_ = y_scorer
    self.term_ranker_ = term_ranker
    self.left_categories_, self.right_categories_, self.top_categories_, self.bottom_categories_ = (left_categories, right_categories, top_categories, bottom_categories)
    self.axes = self._build_axes()
    self.lexicons = self._build_lexicons()

class SemioticSquare(SemioticSquareBase):
    """
    Create a visualization of a semiotic square.  Requires Corpus to have
    at least three categories.
    >>> newsgroups_train = fetch_20newsgroups(subset='train',
    ...   remove=('headers', 'footers', 'quotes'))
    >>> vectorizer = CountVectorizer()
    >>> X = vectorizer.fit_transform(newsgroups_train.data)
    >>> corpus = st.CorpusFromScikit(
    ... 	X=X,
    ... 	y=newsgroups_train.target,
    ... 	feature_vocabulary=vectorizer.vocabulary_,
    ... 	category_names=newsgroups_train.target_names,
    ... 	raw_texts=newsgroups_train.data
    ... 	).build()
    >>> semseq = SemioticSquare(corpus,
    ... 	category_a = 'alt.atheism',
    ... 	category_b = 'soc.religion.christian',
    ... 	neutral_categories = ['talk.religion.misc']
    ... )
    >>> # A simple HTML table
    >>> html = SemioticSquareViz(semseq).to_html()
    >>> # The table with an interactive scatterplot below it
    >>> html = st.produce_semiotic_square_explorer(semiotic_square,
    ...                                            x_label='More Atheism, Less Xtnity',
    ...                                            y_label='General Religious Talk')
    """

    def __init__(self, term_doc_matrix, category_a, category_b, neutral_categories, labels=None, term_ranker=AbsoluteFrequencyRanker, scorer=None, non_text=False):
        """
        Parameters
        ----------
        term_doc_matrix : TermDocMatrix
            TermDocMatrix (or descendant) which will be used in constructing square.
        category_a : str
            Category name for term A
        category_b : str
            Category name for term B (in opposition to A)
        neutral_categories : list[str]
            List of category names that A and B will be contrasted to.  Should be in same domain.
        labels : dict
            None by default. Labels are dictionary of {'a_and_b': 'A and B', ...} to be shown
            above each category.
        term_ranker : TermRanker
            Class for returning a term-frequency convention_df
        scorer : termscoring class, optional
            Term scoring class for lexicon mining. Default: `scattertext.termscoring.ScaledFScore`
        non_text : bool, default False
            Use metadata/non-text
        """
        assert category_a in term_doc_matrix.get_categories()
        assert category_b in term_doc_matrix.get_categories()
        for category in neutral_categories:
            assert category in term_doc_matrix.get_categories()
        if len(neutral_categories) == 0:
            raise EmptyNeutralCategoriesError()
        self.category_a_ = category_a
        self.category_b_ = category_b
        self.neutral_categories_ = neutral_categories
        self.non_text = non_text
        self._build_square(term_doc_matrix, term_ranker, labels, scorer)

    def _build_square(self, term_doc_matrix, term_ranker, labels, scorer):
        self.term_doc_matrix_ = term_doc_matrix
        self.term_ranker = term_ranker(term_doc_matrix).set_non_text(non_text=self.non_text)
        self.scorer = RankDifference() if scorer is None else scorer
        self.axes = self._build_axes(scorer)
        self.lexicons = self._build_lexicons()
        self._labels = labels

    def get_axes(self, scorer=None):
        """
        Returns
        -------
        pd.DataFrame
        """
        if scorer:
            return self._build_axes(scorer)
        return self.axes

    def get_lexicons(self, num_terms=10):
        """
        Parameters
        ----------
        num_terms, int

        Returns
        -------
        dict
        """
        return {k: v.index[:num_terms] for k, v in self.lexicons.items()}

    def get_labels(self):
        a = self._get_default_a_label()
        b = self._get_default_b_label()
        default_labels = {'a': a, 'not_a': 'Not ' + a, 'b': b, 'not_b': 'Not ' + b, 'a_and_b': a + ' + ' + b, 'not_a_and_not_b': 'Not ' + a + ' + Not ' + b, 'a_and_not_b': a + ' + Not ' + b, 'b_and_not_a': 'Not ' + a + ' + ' + b}
        labels = self._labels
        if labels is None:
            labels = {}
        return {name + '_label': labels.get(name, default_labels[name]) for name in default_labels}

    def _get_default_b_label(self):
        return self.category_b_

    def _get_default_a_label(self):
        return self.category_a_

    def _build_axes(self, scorer):
        if scorer is None:
            scorer = self.scorer
        tdf = self._get_term_doc_count_df()
        default_score = self.scorer.get_default_score()
        counts = tdf.sum(axis=1)
        tdf['x'] = self._get_x_axis(scorer, tdf)
        tdf.loc[np.isnan(tdf['x']), 'x'] = default_score
        tdf['y'] = self._get_y_axis(scorer, tdf)
        tdf.loc[np.isnan(tdf['y']), 'y'] = default_score
        tdf['counts'] = counts
        if default_score == 0.5:
            tdf['x'] = 2 * tdf['x'] - 1
            tdf['y'] = 2 * tdf['y'] - 1
        return tdf[['x', 'y', 'counts']]

    def _get_x_axis(self, scorer, tdf):
        return scorer.get_scores(tdf[self.category_a_ + ' freq'], tdf[self.category_b_ + ' freq'])

    def _get_y_axis(self, scorer, tdf):
        return scorer.get_scores(tdf[[t + ' freq' for t in [self.category_a_, self.category_b_]]].sum(axis=1), tdf[[t + ' freq' for t in self.neutral_categories_]].sum(axis=1))

    def _get_term_doc_count_df(self):
        return self.term_ranker.get_ranks()[[t + ' freq' for t in self._get_all_categories()]]

    def _get_all_categories(self):
        return [self.category_a_, self.category_b_] + self.neutral_categories_

    def _build_lexicons(self):
        axes_parts_df = add_radial_parts_and_mag_to_term_coordinates(term_coordinates_df=self.axes)
        self.axes['color'] = axes_parts_df.Part.apply(lambda x: HALO_COLORS.get(x.replace('left', 'RIGHT').replace('right', 'left').replace('RIGHT', 'right')))
        self.lexicons = {semiotic_square_label: axes_parts_df[lambda df: df.Part == part].sort_values(by='Mag', ascending=False) for semiotic_square_label, part in SEMIOTIC_SQUARE_TO_PART.items()}
        return self.lexicons

def _build_square(self, term_doc_matrix, term_ranker, labels, scorer):
    self.term_doc_matrix_ = term_doc_matrix
    self.term_ranker = term_ranker(term_doc_matrix).set_non_text(non_text=self.non_text)
    self.scorer = RankDifference() if scorer is None else scorer
    self.axes = self._build_axes(scorer)
    self.lexicons = self._build_lexicons()
    self._labels = labels

def get_axes(self, scorer=None):
    """
        Returns
        -------
        pd.DataFrame
        """
    if scorer:
        return self._build_axes(scorer)
    return self.axes

class CategoryTableMaker(GraphRenderer):

    def __init__(self, corpus, num_rows=10, non_text=False, category_order=None, all_category_scorer_factory: Optional[Callable[[TermDocMatrix], AllCategoryScorer]]=None, min_font_size=7, max_font_size=20, term_category_scores: Optional[np.array]=None, term_category_freqs: Optional[np.array]=None, header_clickable: bool=False):
        self.num_rows = num_rows
        self.corpus = corpus
        self.use_metadata = non_text
        self.term_category_scores_ = term_category_scores
        self.term_category_freqs_ = term_category_freqs
        self.all_category_scorer_ = self._get_all_category_scorer(all_category_scorer_factory, corpus, non_text)
        self.rank_df = self._get_term_category_associations()
        self.category_order_ = [str(x) for x in (sorted(self.corpus.get_categories()) if category_order is None else category_order)]
        self.min_font_size = min_font_size
        self.max_font_size = max_font_size
        self.header_clickable_ = header_clickable

    def _get_all_category_scorer(self, all_category_scorer_factory, corpus, use_metadata) -> Optional[AllCategoryScorer]:
        if self.term_category_freqs_ is not None and self.term_category_scores_ is not None:
            return None
        if all_category_scorer_factory is None:
            all_category_scorer_factory = lambda corpus: AllCategoryScorerGMeanL2(corpus=corpus, non_text=use_metadata)
        return all_category_scorer_factory(corpus).set_non_text(non_text=use_metadata)

    def _get_term_category_associations(self) -> pd.DataFrame:
        if self.all_category_scorer_ is None:
            terms = []
            cats = []
            ranks = []
            scores = []
            freqs = []
            single_terms = self.corpus.get_terms(self.use_metadata)
            for cat_i, cat in enumerate(self.corpus.get_categories()):
                cats += [str(cat)] * self.corpus.get_num_terms(self.use_metadata)
                terms += single_terms
                scores.append(self.term_category_scores_[cat_i])
                freqs.append(self.term_category_freqs_[cat_i])
                ranks.append(np.argsort(-self.term_category_scores_[cat_i]))
            return pd.DataFrame({'Term': terms, 'Category': cats, 'Frequency': np.hstack(np.array(freqs).T), 'Score': np.hstack(np.array(scores).T), 'Rank': np.hstack(np.array(ranks).T)})
        term_category_association = self.all_category_scorer_.get_rank_freq_df()
        return term_category_association

    def get_graph(self):
        table = '<div class="timelinecontainer"><table class="timelinetable">'
        category_headers = '</th><th>'.join(self.category_order_)
        if self.header_clickable_:
            category_headers = f'</th><th>'.join(['<span class="catnamehead" style="hover {background:#ff0000;}"' + ' onclick="termPlotInterface.drawCategoryScores(\'' + cat.replace('"', '\\"').replace("'", "\\'") + '\')">' + cat + '</span>' for cat in self.category_order_])
        table += '<tr><th>' + category_headers + '</th></tr>'
        display_df = self.__get_display_df()
        print(display_df.Rank.max())
        cat_df = self.__get_cat_df(display_df)
        for rank, group_df in display_df.groupby('Rank'):
            table += '<tr><td class="clickabletd">' + '</td><td class="clickabletd">'.join([ClickableTerms.get_clickable_term(row.Term, style='font-size: ' + str(row.FontSize)) for _, row in group_df.sort_values(by='CategoryNum').iterrows()]) + '</td></tr>'
        table += '<tr>' + ''.join([f'<td class="clickabletd" id="clickabletd-{row.CategoryNum}"></td>' for _, row in cat_df.iterrows()]) + '</tr>' + '</table></div>'
        return table

    def __get_display_df(self):
        display_df = self.rank_df[lambda df: df.Rank < self.num_rows].assign(Frequency=lambda df: df.Frequency + 0.001)
        bin_boundaries = np.histogram_bin_edges(np.log(display_df.Frequency), bins=self.max_font_size - self.min_font_size)
        display_df = pd.merge(display_df.assign(FontSize=lambda df: df.Frequency.apply(np.log).apply(lambda x: bisect_left(bin_boundaries, x) + self.min_font_size)).assign(Category=lambda df: df.Category.apply(str)), pd.DataFrame({'Category': [str(c) for c in self.category_order_], 'CategoryNum': np.arange(len(self.category_order_))}), on='Category')
        return display_df

    def __get_cat_df(self, display_df):
        cat_df = display_df[['Category', 'CategoryNum']].drop_duplicates().sort_values(by='CategoryNum')
        return cat_df

    def get_javascript(self):
        d = {}
        for category, cat_df in self.rank_df.assign(Frequency=lambda df: df.Frequency.astype(int)).groupby('Category'):
            cat_d = {}
            for _, row in cat_df.iterrows():
                cat_d[row['Term']] = {'Rank': row['Rank'], 'Freq': row['Frequency']}
            d[category] = cat_d
        js = 'categoryFrequency = ' + json.dumps(d) + '; \n\n'
        cat_dict = dict(self.__get_cat_df(display_df=self.__get_display_df()).set_index('Category')['CategoryNum'].astype(str))
        js += '\n        Array.from(document.querySelectorAll(\'.clickabletd\')).map(\n            function (node) {\n                node.addEventListener(\'mouseenter\', mouseEnterNode);\n                node.addEventListener(\'mouseleave\', mouseLeaveNode);    \n                node.addEventListener(\'click\', clickNode);\n            }\n        )\n        \n        function clickNode() {\n            //document.querySelectorAll(".dotgraph")\n            //    .forEach(node => node.style.display = \'none\');\n\n            //var term = Array.prototype.filter\n            //    .call(this.children, (x => x.tagName === "span"))[0].textContent;\n\n            //plotInterface.handleSearchTerm(term, true);\n            \n            \n        }\n\n        function mouseEnterNode(event) {\n            //console.log("THIS"); console.log(this)\n            var term = this.children[0].textContent;\n            plotInterface.showTooltipSimple(term);\n            var clickableTds = document.getElementsByClassName(\'clickabletd\');\n            \n            for(var i = 0; i < clickableTds.length; i++) {\n                var td = clickableTds[i];\n                if(Object.entries(td.children).length > 0 && td.children[0].textContent == term) \n                    td.style.backgroundColor = "#FFAAAA";\n                    \n            }\n            \n            var termStats = []; \n            Object.keys(categoryFrequency).map(function(cat) {\n                termStats[cat] = [\n                    categoryFrequency[cat][term][\'Rank\'], \n                    Object.values(categoryFrequency[cat]).map(y=>y.Rank).reduce((a,b)=>Math.max(a,b), 0),\n                    categoryFrequency[cat][term][\'Freq\'],\n                    Object.keys(categoryFrequency[cat]).length\n                ]\n            });\n            \n            Object.entries(getCatNumToCat()).flatMap(\n                function(kv) {\n                    if(false) {\n                        var td = document.getElementById(\'clickabletd-\' + kv[1]);\n                        var termStat = termStats[kv[0]];\n                        console.log(termStat)\n                        if(termStat[0] >= ' + str(self.num_rows) + ') { \n                            td.style.tableLayout = \'fixed\';\n                            //td.style.wordWrap = \'break-word\';\n                            td.style.flexWrap =  \'wrap\';\n                            //td.style.backgroundColor = "#FFAAAA";\n                            td.style.fontSize = "' + str(self.min_font_size) + 'px";  \n                            td.textContent = (termStat[2]) + " occs; rank: " + (termStat[0] + 1);\n                        } else {\n                            td.style.tableLayout = \'fixed\';\n                            //td.style.wordWrap = \'break-word\';\n                            td.style.flexWrap =  \'wrap\';\n                            td.style.backgroundColor = "#FFFFFF";\n                            td.style.fontSize = "' + str(self.min_font_size) + 'px";  \n                            td.textContent = (termStat[2]) + " occs; rank: " + (termStat[0] + 1);\n                        }\n                    }\n                }\n            );\n            \n        }\n        \n        function mouseLeaveNode(event) {\n            plotInterface.tooltip.transition().style(\'opacity\', 0)\n            var clickableTds = document.getElementsByClassName(\'clickabletd\');            \n            for(var i = 0; i < clickableTds.length; i++) \n                clickableTds[i].style.backgroundColor = "#FFFFFF";\n                \n            Object.entries(getCatNumToCat()).flatMap(\n                function(kv) {\n                    if(false) {\n                        var td = document.getElementById(\'clickabletd-\' + kv[1]);\n                \n                        td.style.tableLayout = \'fixed\';\n                        //td.style.wordWrap = \'break-word\';\n                        td.style.flexWrap =  \'wrap\';\n                        td.style.backgroundColor = "#FFFFFF";\n                        td.style.fontSize = "' + str(self.min_font_size) + 'px";  \n                        //td.innerHtml = \'&nbsp;\'.repeat(27);\n                        td.textContent = \'\';\n                    }\n                }\n            )                \n        }\n        \n        function getCatNumToCat() { return ' + json.dumps(cat_dict) + '}'
        return js

def _get_all_category_scorer(self, all_category_scorer_factory, corpus, use_metadata) -> Optional[AllCategoryScorer]:
    if self.term_category_freqs_ is not None and self.term_category_scores_ is not None:
        return None
    if all_category_scorer_factory is None:
        all_category_scorer_factory = lambda corpus: AllCategoryScorerGMeanL2(corpus=corpus, non_text=use_metadata)
    return all_category_scorer_factory(corpus).set_non_text(non_text=use_metadata)

class BackgroundFrequenciesFromCorpus(BackgroundFrequencyDataFramePreparer):

    def __init__(self, corpus, exclude_categories=[]):
        self.background_df = pd.DataFrame(corpus.remove_categories(exclude_categories).get_term_freq_df().sum(axis=1)).rename(columns={0: 'background'})

    def get_background_frequency_df(self):
        return self.background_df

    def get_background_rank_df(self):
        return self.prep_background_frequency(self.get_background_frequency_df())

def get_background_rank_df(self):
    return self.prep_background_frequency(self.get_background_frequency_df())

class BackgroundFrequencies(BackgroundFrequencyDataFramePreparer):

    @staticmethod
    def get_background_frequency_df(frequency_path=None):
        raise Exception

    @classmethod
    def get_background_rank_df(cls, frequency_path=None):
        return cls.prep_background_frequency(cls.get_background_frequency_df(frequency_path))

@classmethod
def get_background_rank_df(cls, frequency_path=None):
    return cls.prep_background_frequency(cls.get_background_frequency_df(frequency_path))

class PhraseSelector(object):

    def __init__(self, minimum_pmi=16):
        """
		Filter n-grams using PMI.

		Parameters
		----------
		alpha : float
		labmda_ : "cressie_read"
			See https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.power_divergence.html for
			options.
		"""
        self.minimum_pmi = minimum_pmi

    def compact(self, term_doc_matrix, non_text=False):
        """
		Parameters
		-------
		term_doc_matrix : TermDocMatrix

		Returns
		-------

		New term doc matrix
		"""
        count_df = self._get_statistics_dataframe(term_doc_matrix, non_text)
        return term_doc_matrix.remove_terms(count_df[count_df['pmi'] < self.minimum_pmi].index, non_text=non_text)

    def _get_statistics_dataframe(self, term_doc_matrix, non_text):
        tdf = term_doc_matrix.get_metadata_freq_df().sum(axis=1) if non_text else term_doc_matrix.get_term_freq_df().sum(axis=1)
        gram_df = pd.Series(tdf.index).apply(lambda x: pd.Series(list(reversed(x.split()))))
        gram_df['c'] = tdf.values
        gram_df['term'] = tdf.index
        gram_df = gram_df.set_index('term')
        unigram_df = gram_df[gram_df[1].isnull()][['c']]
        ngram_df = gram_df.dropna()
        count_df = pd.merge(pd.merge(ngram_df, unigram_df, left_on=0, right_index=True, suffixes=('', '0')), unigram_df, left_on=1, right_index=True, suffixes=('', '1'))
        p0 = count_df['c0'] / unigram_df['c'].sum()
        p1 = count_df['c1'] / unigram_df['c'].sum()
        p = count_df['c'] / ngram_df['c'].sum()
        count_df['pmi'] = np.log(p / (p0 * p1)) / np.log(2)
        return count_df

def compact(self, term_doc_matrix, non_text=False):
    """
		Parameters
		-------
		term_doc_matrix : TermDocMatrix

		Returns
		-------

		New term doc matrix
		"""
    count_df = self._get_statistics_dataframe(term_doc_matrix, non_text)
    return term_doc_matrix.remove_terms(count_df[count_df['pmi'] < self.minimum_pmi].index, non_text=non_text)

class ClassPercentageCompactor(object):

    def __init__(self, term_ranker=AbsoluteFrequencyRanker, term_count=2):
        """
		Limit terms to ones that make up a minimum percentage
		of documents in a category.  Given a term_count, set the threshold
		to that of the smallest class.

		Parameters
		----------
		term_ranker : TermRanker
		term_count : int
		"""
        self.term_ranker = term_ranker
        self.term_count = term_count

    def compact(self, term_doc_matrix, non_text=False):
        """
		Parameters
		-------
		term_doc_matrix : TermDocMatrix
		non_text : bool

		Returnss
		-------
		New term doc matrix
		"""
        ranker = self.term_ranker(term_doc_matrix)
        if non_text:
            ranker = ranker.use_non_text_features()
        tdf = ranker.get_ranks()
        tdf_sum = tdf.sum(axis=0)
        tdf_portions = tdf / tdf_sum
        threshold = np.max(self.term_count / tdf_sum)
        terms_to_remove = tdf_portions[~(tdf_portions > threshold).any(axis=1)].index
        return term_doc_matrix.remove_terms(terms_to_remove, non_text=non_text)

def compact(self, term_doc_matrix, non_text=False):
    """
		Parameters
		-------
		term_doc_matrix : TermDocMatrix
		non_text : bool

		Returnss
		-------
		New term doc matrix
		"""
    ranker = self.term_ranker(term_doc_matrix)
    if non_text:
        ranker = ranker.use_non_text_features()
    tdf = ranker.get_ranks()
    tdf_sum = tdf.sum(axis=0)
    tdf_portions = tdf / tdf_sum
    threshold = np.max(self.term_count / tdf_sum)
    terms_to_remove = tdf_portions[~(tdf_portions > threshold).any(axis=1)].index
    return term_doc_matrix.remove_terms(terms_to_remove, non_text=non_text)

class CompactTerms(object):

    def __init__(self, term_ranker=AbsoluteFrequencyRanker, minimum_term_count=0, slack=1):
        """

		Parameters
		----------
		term_ranker : TermRanker
			Default AbsoluteFrequencyRanker
		minimum_term_count : int
			Default 0
		slack : int
			Default 1

		"""
        self.term_ranker = term_ranker
        self.minimum_term_count = minimum_term_count
        self.redundancy_slack = slack

    def compact(self, term_doc_matrix, non_text=False):
        """
		Parameters
		----------
		term_doc_matrix : TermDocMatrix
			Term document matrix object to compact
		non_text : bool
			Use non-text features instead of terms

		Returns
		-------
		New term doc matrix
		"""
        return term_doc_matrix.remove_terms_by_indices(self._indices_to_compact(term_doc_matrix, non_text), non_text)

    def _indices_to_compact(self, term_doc_matrix, non_text=False):
        ranker = self.term_ranker(term_doc_matrix)
        if non_text:
            ranker = ranker.use_non_text_features()
        indicies = self._get_term_indices_to_compact_from_term_freqs(ranker.get_ranks(), term_doc_matrix, non_text)
        return list(indicies)

    def _get_term_indices_to_compact_from_term_freqs(self, term_freqs, term_doc_matrix, non_text):
        idx = IndexStore()
        tdf_vals = term_freqs.values
        valid_terms_mask = tdf_vals.sum(axis=1) >= self.minimum_term_count
        tdf_vals = term_freqs[valid_terms_mask].values
        terms = np.array(term_freqs.index)[valid_terms_mask]
        lengths = []
        fact = CSRMatrixFactory()
        for i, t in enumerate(terms):
            for tok in t.split():
                fact[i, idx.getidx(tok)] = 1
            lengths.append(len(t.split()))
        lengths = np.array(lengths)
        mat = fact.get_csr_matrix()
        coocs = lengths - mat * mat.T
        pairs = np.argwhere(coocs == 0).T
        pairs = self._limit_to_non_identical_terms(pairs)
        pairs = self._limit_to_pairs_of_bigrams_and_a_constituent_unigram(pairs, terms)
        pairs = self._limit_to_redundant_unigrams(pairs, tdf_vals)
        idx_store = term_doc_matrix._get_relevant_idx_store(non_text)
        redundant_terms = idx_store.getidxstrictbatch(terms[np.unique(pairs[:, 1])])
        infrequent_terms = np.argwhere(~valid_terms_mask).T[0]
        terms_to_remove = np.concatenate([redundant_terms, infrequent_terms])
        return terms_to_remove

    def _limit_to_redundant_unigrams(self, pairs, tdf_vals):
        return pairs[np.all(tdf_vals[pairs[:, 1]] <= tdf_vals[pairs[:, 0]] + self.redundancy_slack, axis=1)]

    def _limit_to_pairs_of_bigrams_and_a_constituent_unigram(self, pairs, terms):
        return pairs[np.array([terms[i[1]] in terms[i[0]] for i in pairs])]

    def _limit_to_non_identical_terms(self, pairs):
        return pairs.T[pairs[0] != pairs[1]]

def _indices_to_compact(self, term_doc_matrix, non_text=False):
    ranker = self.term_ranker(term_doc_matrix)
    if non_text:
        ranker = ranker.use_non_text_features()
    indicies = self._get_term_indices_to_compact_from_term_freqs(ranker.get_ranks(), term_doc_matrix, non_text)
    return list(indicies)

class TermCategoryRanker(object):

    def __init__(self, scorer: type=ScaledFScorePresetsNeg1To1, term_ranker: type=AbsoluteFrequencyRanker, use_non_text_features: bool=False, target_category: Optional[str]=None):
        self.scorer = scorer
        self.term_ranker = term_ranker
        self.use_non_text_features = use_non_text_features
        self.target_category = target_category

    def set_use_non_text_features(self, use_non_text_features: bool) -> 'TermCategoryRanker':
        self.use_non_text_features = use_non_text_features
        return self

    def get_rank_df(self, term_doc_matrix) -> pd.DataFrame:
        tdf, tdf_sum = self.__get_term_ranks_and_frequencies(term_doc_matrix)
        score_data = {}
        categories = term_doc_matrix.get_categories()
        my_scorer = self._initialize_scorer(term_doc_matrix)
        if self.target_category is not None:
            assert self.target_category in categories
            if issubclass(self.scorer, CorpusBasedTermScorer):
                score_data[str(self.target_category)] = my_scorer.set_categories(category_name=self.target_category).get_scores()
                score_data['Not ' + str(self.target_category)] = -1 * score_data[str(self.target_category)]
            else:
                focus = tdf[str(self.target_category)].values
                background = tdf_sum.values - focus
                score_data[str(self.target_category)] = my_scorer.get_scores(focus, background)
                score_data['Not ' + str(self.target_category)] = my_scorer.get_scores(background, focus)
        else:
            for category in categories:
                if issubclass(self.scorer, CorpusBasedTermScorer):
                    score_data[str(category)] = my_scorer.set_categories(category_name=category).get_scores()
                else:
                    focus = tdf[str(category)].values
                    background = tdf_sum.values - focus
                    score_data[str(category)] = my_scorer.get_scores(focus, background)
        return pd.DataFrame(score_data, index=tdf.index).apply(lambda x: rankdata(x, 'dense'))

    def _initialize_scorer(self, term_doc_matrix):
        if issubclass(self.scorer, CorpusBasedTermScorer):
            my_scorer = self.scorer(term_doc_matrix)
            if self.use_non_text_features:
                return my_scorer.use_metadata()
            return my_scorer
        return self.scorer()

    def __get_term_ranks_and_frequencies(self, term_doc_matrix) -> Tuple[pd.DataFrame, pd.Series]:
        ranker = self.term_ranker(term_doc_matrix)
        if self.use_non_text_features:
            ranker = ranker.use_non_text_features()
        tdf = ranker.get_ranks('')
        tdf_sum = tdf.sum(axis=1)
        return (tdf, tdf_sum)

    def get_frequencies(self, term_doc_matrix) -> pd.Series:
        return self.__get_term_ranks_and_frequencies(term_doc_matrix)[1]

    def get_max_rank(self, term_doc_matrix) -> float:
        """

        :param term_doc_matrix: TermDocMatrix
        :return: int
        """
        rank_df = self.get_rank_df(term_doc_matrix)
        return rank_df.max().max()

def __get_term_ranks_and_frequencies(self, term_doc_matrix) -> Tuple[pd.DataFrame, pd.Series]:
    ranker = self.term_ranker(term_doc_matrix)
    if self.use_non_text_features:
        ranker = ranker.use_non_text_features()
    tdf = ranker.get_ranks('')
    tdf_sum = tdf.sum(axis=1)
    return (tdf, tdf_sum)

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

def _remove_terms(self, term_doc_matrix, terms_to_remove):
    return term_doc_matrix.remove_terms(terms_to_remove, non_text=self.scorer.use_non_text_features)

class NgramPercentageCompactor(BaseTermCompactor):

    def __init__(self, term_ranker: type=AbsoluteFrequencyRanker, minimum_term_count: int=0, usage_portion: float=0.7, token_split_function: Callable[[str], List[str]]=lambda x: x.split(), token_join_function: Callable[[List[str]], str]=' '.join, verbose: bool=False):
        """

        Parameters
        ----------
        term_ranker : TermRanker
            Default AbsoluteFrequencyRanker
        minimum_term_count : int
            Default 0
        usage_portion : float
            Portion of times term is used in a containing n-gram for it to be eliminated
            Default 0.8
        token_split_function : Callable[[str], List[str]]
            Function to split string into parts,
            Default lambda x: x.split()
        token_join_function : Callable[[List[str]], str]
            Function to join parsts into a string
            Default lambda x: ' '.join(x)
        verbose : bool
            Show progress bar
        """
        self.term_ranker = term_ranker
        self.minimum_term_count = minimum_term_count
        self.usage_portion = usage_portion
        self.verbose = verbose
        self.token_split_function = token_split_function
        self.token_join_function = token_join_function

    def compact(self, term_doc_matrix, non_text=False):
        elim_df = self.get_elimination_df(term_doc_matrix, non_text)
        if self.verbose:
            print(f'Ngram percentage compactor removed {len(elim_df)} terms.')
        return term_doc_matrix.remove_terms(terms=elim_df.Eliminations, ignore_absences=True, non_text=non_text)

    def get_elimination_df(self, term_doc_matrix, non_text=False) -> pd.DataFrame:
        freq_df = pd.DataFrame({'Count': self.term_ranker(term_doc_matrix).set_non_text(non_text).get_ranks().sum(axis=1)})[lambda df: df.Count >= self.minimum_term_count]
        max_subgramsize = max((len(self.token_split_function(tok)) for tok in freq_df.index)) - 1
        eliminations = []
        eliminators = []
        it = freq_df.iterrows()
        if self.verbose:
            it = tqdm(freq_df.iterrows(), total=len(freq_df))
        for row_i, row in it:
            toks = self.token_split_function(row.name)
            gram_len = len(toks)
            if gram_len > 1:
                subgrams = []
                for i in range(min(max_subgramsize, gram_len - 1), 0, -1):
                    for subtoks in sequence_window(toks, i):
                        subgrams.append(self.token_join_function(subtoks))
                found_subgrams = freq_df.index.intersection(subgrams)
                to_elim = list(freq_df.loc[found_subgrams][lambda df: row.Count > df.Count * self.usage_portion].index)
                if to_elim:
                    eliminations += to_elim
                    eliminators += [row.name] * len(to_elim)
        return pd.DataFrame({'Eliminations': eliminations, 'Eliminators': eliminators})

def compact(self, term_doc_matrix, non_text=False):
    elim_df = self.get_elimination_df(term_doc_matrix, non_text)
    if self.verbose:
        print(f'Ngram percentage compactor removed {len(elim_df)} terms.')
    return term_doc_matrix.remove_terms(terms=elim_df.Eliminations, ignore_absences=True, non_text=non_text)

class NPMICompactor(object):

    def __init__(self, term_ranker: type=AbsoluteFrequencyRanker, minimum_term_count: int=2, number_terms_per_length: int=2000, token_split_function: Optional[Callable[[str], List[str]]]=None, token_join_function: Optional[Callable[[List[str]], str]]=None, show_progress: bool=True):
        """

        Parameters
        ----------
        term_ranker : TermRanker
            Default AbsoluteFrequencyRanker
        minimum_term_count : int
            Default 2
        number_terms_per_length : int
            Select X top PMI terms per ngram length
            Default 2000
        token_split_function: Optional[Callable[[str], List[str]]] = None
            Splits a term into ngrams, default lambda x: x.split()
        token_join_function: Optional[Callable[[List[str]], str]] = None
            Joins a sequence of tokens int a string, opposite of split function, default lambda x: x.join(' ')
        show_progress : bool
            Shows TQDM for PMI filtering


        """
        self.term_ranker = term_ranker
        self.minimum_term_count = minimum_term_count
        self.number_terms_per_length = number_terms_per_length
        self.show_progress = show_progress
        self.token_split_function = (lambda x: x.split()) if token_split_function is None else token_split_function
        self.token_join_function = (lambda x: ' '.join(x)) if token_join_function is None else token_join_function

    def compact(self, term_doc_matrix, non_text=False):
        """
        Parameters
        ----------
        term_doc_matrix : TermDocMatrix
            Term document matrix object to compact
        non_text : bool
            Use non-text features instead of terms

        Returns
        -------
        New term doc matrix
        """
        pmi_df = self.get_pmi_df(term_doc_matrix, non_text)
        threshold_df = self._get_ngram_length_pmi_thresholds(pmi_df)
        filtered_pmi_df = pd.merge(pmi_df, threshold_df, left_on='Len', right_index=True)[lambda df: df.NPMI < df.NPMIThreshold]
        terms_to_remove = list(filtered_pmi_df.Term)
        return term_doc_matrix.remove_terms(terms_to_remove, non_text).remove_infrequent_words(self.minimum_term_count - 1, term_ranker=self.term_ranker, non_text=non_text)

    def get_pmi_df(self, term_doc_matrix, non_text: bool=False):
        freqs = self._get_term_frequencies(non_text, term_doc_matrix)
        pmi_df = self._get_pmi_df(freqs)[lambda df: df.Count >= self.minimum_term_count]
        return pmi_df

    def _get_term_frequencies(self, non_text, term_doc_matrix):
        ranker = self.term_ranker(term_doc_matrix)
        if non_text:
            ranker = ranker.use_non_text_features()
        freqs = ranker.get_ranks().sum(axis=1)
        return freqs

    def _get_ngram_length_pmi_thresholds(self, pmi_df: pd.DataFrame) -> pd.DataFrame:
        return pmi_df[lambda df: (df.Len > 1) & (df.Count >= self.minimum_term_count)].groupby('Len').apply(lambda gdf: pd.Series({'NPMI': 0}) if len(gdf) <= self.number_terms_per_length else gdf.sort_values(by='NPMI', ascending=False).iloc[self.number_terms_per_length][['NPMI']]).rename(columns={'NPMI': 'NPMIThreshold'})

    def _get_pmi_df(self, freqs: pd.Series) -> pd.DataFrame:
        wc = dict(pd.DataFrame({'Len': [len(self.token_split_function(x)) for x in freqs.index], 'Freq': freqs}).groupby('Len').sum()['Freq'])
        backoff = freqs.mean()

        def prob(ngram):
            if len(ngram) == 0:
                return 1
            joined_ngram = self.token_join_function(ngram)
            if joined_ngram in freqs:
                return freqs.loc[joined_ngram] / (wc[len(ngram)] - len(ngram) + 1)
            if ngram[0] in freqs.index:
                return freqs.loc[ngram[0]] / wc[1] * prob(ngram[1:])
            return backoff / wc[1] * prob(ngram[1:])
        apply = lambda df: df.apply
        if self.show_progress:
            apply = lambda df: df.progress_apply
        return pd.DataFrame({'Count': freqs}).reset_index().rename(columns={'term': 'Term'}).assign(Len=lambda df: df.Term.apply(lambda x: len(self.token_split_function(x))))[lambda df: df.Len > 1].assign(WholeProb=lambda df: apply(df.Term)(lambda x: prob(self.token_split_function(x))), UniProb=lambda df: apply(df.Term)(lambda x: np.exp(sum((np.log(prob([tok])) for tok in self.token_split_function(x))))), PMI=lambda df: np.log(df.WholeProb) - np.log(df.UniProb), NPMI=lambda df: -df.PMI / np.log(df.WholeProb))

def compact(self, term_doc_matrix, non_text=False):
    """
        Parameters
        ----------
        term_doc_matrix : TermDocMatrix
            Term document matrix object to compact
        non_text : bool
            Use non-text features instead of terms

        Returns
        -------
        New term doc matrix
        """
    pmi_df = self.get_pmi_df(term_doc_matrix, non_text)
    threshold_df = self._get_ngram_length_pmi_thresholds(pmi_df)
    filtered_pmi_df = pd.merge(pmi_df, threshold_df, left_on='Len', right_index=True)[lambda df: df.NPMI < df.NPMIThreshold]
    terms_to_remove = list(filtered_pmi_df.Term)
    return term_doc_matrix.remove_terms(terms_to_remove, non_text).remove_infrequent_words(self.minimum_term_count - 1, term_ranker=self.term_ranker, non_text=non_text)

def _get_term_frequencies(self, non_text, term_doc_matrix):
    ranker = self.term_ranker(term_doc_matrix)
    if non_text:
        ranker = ranker.use_non_text_features()
    freqs = ranker.get_ranks().sum(axis=1)
    return freqs

class TestTermRanker(TestCase):

    def test_absolute_frequency_ranker(self):
        tdm = make_a_test_term_doc_matrix()
        ranker = AbsoluteFrequencyRanker(tdm)
        rank_df = ranker.get_ranks()
        self.assertEqual(len(rank_df), 58)
        self.assertEqual(rank_df.loc['hello'].tolist(), [1, 0])
        self.assertEqual(rank_df.loc['blah'].tolist(), [0, 3])
        self.assertEqual(rank_df.loc['name'].tolist(), [1, 1])

    def _test_doc_length_normalized_frequency_ranker(self):
        tdm = make_a_test_term_doc_matrix()
        len_ranker = DocLengthNormalizedFrequencyRanker(tdm)
        abs_ranker = AbsoluteFrequencyRanker(tdm)
        abs_rank_df = abs_ranker.get_ranks()
        len_ranker_df = len_ranker.get_ranks()
        self.assertEqual(len(abs_rank_df), len(len_ranker_df))
        doc_lengths = [12, 35, 29]
        avg_length = sum(doc_lengths) * 1.0 / len(doc_lengths)
        np.testing.assert_almost_equal(np.array(len_ranker_df.loc['blah']), [0, avg_length * 3.0 / 12])
        np.testing.assert_almost_equal(np.array(len_ranker_df.loc['name']), [avg_length * 1.0 / 35, avg_length * 1.0 / 29])

    def test_doc_length_divided_frequency_ranker(self):
        tdm = make_a_test_term_doc_matrix()
        len_ranker = DocLengthDividedFrequencyRanker(tdm)
        abs_ranker = AbsoluteFrequencyRanker(tdm)
        abs_rank_df = abs_ranker.get_ranks()
        len_ranker_df = len_ranker.get_ranks()
        self.assertEqual(len(abs_rank_df), len(len_ranker_df))
        doc_lengths = [12, 35, 29]
        np.testing.assert_almost_equal(np.array(len_ranker_df.loc['blah']), [0, 3.0 / 12])
        np.testing.assert_almost_equal(np.array(len_ranker_df.loc['name']), [1.0 / 35, 1.0 / 29])

    def test_once_per_doc_frequency_ranker(self):
        tdm = make_a_test_term_doc_matrix()
        abs_ranker = DocLengthDividedFrequencyRanker(tdm)
        one_ranker = OncePerDocFrequencyRanker(tdm)
        abs_rank_df = abs_ranker.get_ranks()
        len_ranker_df = one_ranker.get_ranks()
        self.assertEqual(len(abs_rank_df), len(len_ranker_df))
        np.testing.assert_almost_equal(np.array(len_ranker_df.loc['blah']), [0, 1])
        np.testing.assert_almost_equal(np.array(len_ranker_df.loc['name']), [1, 1])

def _test_doc_length_normalized_frequency_ranker(self):
    tdm = make_a_test_term_doc_matrix()
    len_ranker = DocLengthNormalizedFrequencyRanker(tdm)
    abs_ranker = AbsoluteFrequencyRanker(tdm)
    abs_rank_df = abs_ranker.get_ranks()
    len_ranker_df = len_ranker.get_ranks()
    self.assertEqual(len(abs_rank_df), len(len_ranker_df))
    doc_lengths = [12, 35, 29]
    avg_length = sum(doc_lengths) * 1.0 / len(doc_lengths)
    np.testing.assert_almost_equal(np.array(len_ranker_df.loc['blah']), [0, avg_length * 3.0 / 12])
    np.testing.assert_almost_equal(np.array(len_ranker_df.loc['name']), [avg_length * 1.0 / 35, avg_length * 1.0 / 29])

def test_doc_length_divided_frequency_ranker(self):
    tdm = make_a_test_term_doc_matrix()
    len_ranker = DocLengthDividedFrequencyRanker(tdm)
    abs_ranker = AbsoluteFrequencyRanker(tdm)
    abs_rank_df = abs_ranker.get_ranks()
    len_ranker_df = len_ranker.get_ranks()
    self.assertEqual(len(abs_rank_df), len(len_ranker_df))
    doc_lengths = [12, 35, 29]
    np.testing.assert_almost_equal(np.array(len_ranker_df.loc['blah']), [0, 3.0 / 12])
    np.testing.assert_almost_equal(np.array(len_ranker_df.loc['name']), [1.0 / 35, 1.0 / 29])

def test_once_per_doc_frequency_ranker(self):
    tdm = make_a_test_term_doc_matrix()
    abs_ranker = DocLengthDividedFrequencyRanker(tdm)
    one_ranker = OncePerDocFrequencyRanker(tdm)
    abs_rank_df = abs_ranker.get_ranks()
    len_ranker_df = one_ranker.get_ranks()
    self.assertEqual(len(abs_rank_df), len(len_ranker_df))
    np.testing.assert_almost_equal(np.array(len_ranker_df.loc['blah']), [0, 1])
    np.testing.assert_almost_equal(np.array(len_ranker_df.loc['name']), [1, 1])

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

class AllCategoryScorer(abc.ABC):

    def __init__(self, corpus=Optional, non_text: bool=False, term_ranker: type=AbsoluteFrequencyRanker, term_ranker_kwargs: Optional[Dict]=None, **kwargs):
        self.term_ranker_kwargs_ = term_ranker_kwargs
        self.term_ranker_factory_ = term_ranker
        self.set_non_text(non_text)
        self._free_init(**kwargs)
        self.set_corpus(corpus)

    def set_corpus(self, corpus: Optional) -> 'AllCategoryScorer':
        self.corpus_ = corpus
        if corpus is None:
            self.term_ranker_ = None
        else:
            self.term_ranker_: Optional[TermRanker] = self.term_ranker_factory_(corpus, **self.term_ranker_kwargs_ if self.term_ranker_kwargs_ is not None else {})
        return self

    def set_non_text(self, non_text: bool) -> 'AllCategoryScorer':
        self.non_text_ = non_text
        return self

    def _free_init(self, **kwargs):
        pass

    @abc.abstractmethod
    def get_rank_freq_df(self) -> pd.DataFrame:
        raise NotImplementedError()

    def get_score_df(self, score_append=' Score', freq_append=' Freq') -> pd.DataFrame:
        df = pd.pivot_table(self.get_rank_freq_df(), index='Term', values=['Score', 'Frequency'], columns=['Category'])
        df.columns = [category + {'Score': score_append, 'Frequency': freq_append}[metric_type] for metric_type, category in df.columns.to_flat_index()]
        return df[lambda df: list(sorted(df.columns))]

def __init__(self, corpus=Optional, non_text: bool=False, term_ranker: type=AbsoluteFrequencyRanker, term_ranker_kwargs: Optional[Dict]=None, **kwargs):
    self.term_ranker_kwargs_ = term_ranker_kwargs
    self.term_ranker_factory_ = term_ranker
    self.set_non_text(non_text)
    self._free_init(**kwargs)
    self.set_corpus(corpus)

class AllCategoryTermScorer(AllCategoryScorer):

    def _free_init(self, **kwargs):
        self.term_scorer_factory_: type = kwargs.get('term_scorer', RankDifferenceScorer)
        self.term_scorer_kwargs_: Dict = kwargs.get('term_scorer_kwargs', {})

    def set_corpus(self, corpus: Optional) -> 'AllCategoryScorer':
        AllCategoryScorer.set_corpus(self, corpus=corpus)
        self.term_scorer_ = None
        if self.corpus_ is not None:
            self.term_scorer_: CorpusBasedTermScorer = self.term_scorer_factory_(self.corpus_, **self.term_scorer_kwargs_ if self.term_scorer_kwargs_ is not None else {})
        return self

    def get_rank_freq_df(self) -> pd.DataFrame:
        if self.term_scorer_ is None:
            raise Exception('Ensure the corpus has been set.')
        freq_df = self.term_ranker_.set_non_text(self.non_text_).get_ranks(label_append='')
        if self.non_text_:
            self.term_scorer_ = self.term_scorer_.use_metadata()
        dfs = []
        for category in self.corpus_.get_categories():
            cat_df = pd.DataFrame({'Score': self.term_scorer_.set_categories(str(category)).get_scores().sort_values(ascending=False), 'Category': category})
            cat_df.index = cat_df.index.rename('Term')
            cat_df = cat_df.reset_index().assign(Rank=lambda df: np.arange(len(df), dtype=int), Frequency=lambda df: freq_df.loc[df.Term.values, str(category)].values)
            dfs.append(cat_df)
        return pd.concat(dfs).reset_index(drop=True)

    def get_score_df(self, score_append=' Score', freq_append=' Freq') -> pd.DataFrame:
        rank_df = self.term_ranker_.get_ranks(label_append=freq_append)
        for category in self.corpus_.get_categories():
            scores = self.term_scorer_.set_categories(category_name=category).get_scores()
            rank_df[category + score_append] = scores
        return rank_df[sorted(rank_df.columns)]

def set_corpus(self, corpus: Optional) -> 'AllCategoryScorer':
    AllCategoryScorer.set_corpus(self, corpus=corpus)
    self.term_scorer_ = None
    if self.corpus_ is not None:
        self.term_scorer_: CorpusBasedTermScorer = self.term_scorer_factory_(self.corpus_, **self.term_scorer_kwargs_ if self.term_scorer_kwargs_ is not None else {})
    return self

class DispersionPlotSettings(TrendPlotSettings):

    def __init__(self, category_order: List=None, metric: str='DA', use_residual: bool=True, term_ranker: Optional[TermRanker]=None, frequency_scaler: Optional[Callable[[np.array], np.array]]=None, dispersion_scaler: Optional[Callable[[np.array], np.array]]=None, regressor: Optional=None):
        TrendPlotSettings.__init__(self, category_order=category_order)
        self.metric = metric
        self.use_residual = use_residual
        self.frequency_scaler = dense_rank if frequency_scaler is None else frequency_scaler
        self.dispersion_scaler = (scale_center_zero_abs if use_residual else scale) if dispersion_scaler is None else dispersion_scaler
        self.term_ranker = AbsoluteFrequencyRanker if term_ranker is None else term_ranker
        self.regressor = MeanIsotonic() if regressor is None else regressor

    def get_plot_params(self) -> TrendPlotPresets:
        return TrendPlotPresets(x_label=' '.join(['Frequency', get_scaler_name(self.frequency_scaler).strip()]), y_label=('Frequency-adjusted ' if self.use_residual else '') + self.metric, x_axis_labels=['Low', 'Medium', 'High'], y_axis_labels=['More Concentrated', 'Medium', 'More Dispersion'], tooltip_column_names={'Frequency': 'Frequency', 'Y': 'Residual ' + self.metric}, tooltip_columns=['Frequency', 'Y'], header_names={'upper': 'Dispersed', 'lower': 'Concentrated'}, left_list_column='Y')

    def get_x_axis(self, corpus: TermDocMatrix, non_text: bool=False) -> ScaledAxis:
        rank_df = self.term_ranker(corpus).set_non_text(non_text=non_text).get_ranks('')
        frequencies = rank_df.sum(axis=1)
        return ScaledAxis(orig=frequencies, scaled=self.frequency_scaler(frequencies))

def get_x_axis(self, corpus: TermDocMatrix, non_text: bool=False) -> ScaledAxis:
    rank_df = self.term_ranker(corpus).set_non_text(non_text=non_text).get_ranks('')
    frequencies = rank_df.sum(axis=1)
    return ScaledAxis(orig=frequencies, scaled=self.frequency_scaler(frequencies))

class CorrelationPlotSettings(TrendPlotSettings):

    def __init__(self, category_order: List=None, correlation_type: str='spearmanr', term_ranker: Optional[TermRanker]=None, frequency_scaler: Optional[Callable[[np.array], np.array]]=None):
        TrendPlotSettings.__init__(self, category_order=category_order)
        self.correlation_type = correlation_type
        self.term_ranker = AbsoluteFrequencyRanker if term_ranker is None else term_ranker
        self.frequency_scaler = dense_rank if frequency_scaler is None else frequency_scaler

    def get_plot_params(self) -> TrendPlotPresets:
        return TrendPlotPresets(x_label=' '.join(['Frequency', get_scaler_name(self.frequency_scaler).strip()]), y_label=self.correlation_type.title(), x_axis_labels=['Low', 'Medium', 'High'], y_axis_labels=['Anti-correlated', 'No-correlation', 'Correlated'], tooltip_column_names={'Frequency': 'Frequency', 'Y': Correlations.get_notation_name(self.correlation_type)}, tooltip_columns=['Frequency', 'Y'], header_names={'upper': 'Most correlated', 'lower': 'Most anti-correlated'}, left_list_column='Y')

    def get_x_axis(self, corpus: TermDocMatrix, non_text: bool=False) -> ScaledAxis:
        rank_df = self.term_ranker(corpus).set_non_text(non_text=non_text).get_ranks('')
        frequencies = rank_df.sum(axis=1)
        return ScaledAxis(orig=frequencies, scaled=self.frequency_scaler(frequencies))

def get_x_axis(self, corpus: TermDocMatrix, non_text: bool=False) -> ScaledAxis:
    rank_df = self.term_ranker(corpus).set_non_text(non_text=non_text).get_ranks('')
    frequencies = rank_df.sum(axis=1)
    return ScaledAxis(orig=frequencies, scaled=self.frequency_scaler(frequencies))

class LogOddsRatioUninformativePriorScorer(CorpusBasedTermScorer):

    def get_name(self) -> str:
        return 'Log Odds Ratio w/ Uninformative Prior'

    def _set_scorer_args(self, **kwargs):
        self.alpha = kwargs.get('alpha', 0.01)

    def get_scores(self, *args) -> pd.Series:
        rank_df = self.term_ranker_.get_ranks('')
        a = rank_df[self.category_name] + self.alpha
        b = rank_df[self.not_category_names].sum(axis=1) + self.alpha
        return log_odds_ratio_with_prior_from_counts(a, b)

def get_scores(self, *args) -> pd.Series:
    rank_df = self.term_ranker_.get_ranks('')
    a = rank_df[self.category_name] + self.alpha
    b = rank_df[self.not_category_names].sum(axis=1) + self.alpha
    return log_odds_ratio_with_prior_from_counts(a, b)

class LogOddsRatioInformativePriorScorer(CorpusBasedTermScorer):
    """
    priors = (st.PriorFactory(unigram_corpus,
                          category='Positive',
                          not_categories=['Negative'],
                          starting_count=0.01)
          .use_neutral_categories()
              .get_priors())
    html = st.produce_frequency_explorer(
        unigram_corpus,
        category='Positive',
        category_name='Negative',
        not_category_name='Negative',
        term_scorer=st.LogOddsRatioInformativePriorScorer,
        term_scorer_kwargs={'prior_scale': 6},
        metadata=get_heading,
        minimum_term_frequency=0,
        grey_threshold=0,
    )
    """

    def _set_scorer_args(self, prior_counts, prior_scale):
        self.prior_counts = prior_counts
        self.prior_scale = prior_scale

    def get_scores(self):
        rank_df = self.term_ranker_.get_ranks('')
        a = rank_df[self.category_name] + self.prior_counts
        b = rank_df[self.not_category_names].sum(axis=1) + self.prior_counts
        ap = a + self.prior_counts * self.prior_scale * sum(a) / sum(self.prior_counts.values)
        bp = b + self.prior_counts * self.prior_scale * sum(b) / sum(self.prior_counts.values)
        return log_odds_ratio_with_prior_from_counts(ap, bp)

    def get_name(self):
        return 'Log Odds Ratio w/ Informative Prior'

def get_scores(self):
    rank_df = self.term_ranker_.get_ranks('')
    a = rank_df[self.category_name] + self.prior_counts
    b = rank_df[self.not_category_names].sum(axis=1) + self.prior_counts
    ap = a + self.prior_counts * self.prior_scale * sum(a) / sum(self.prior_counts.values)
    bp = b + self.prior_counts * self.prior_scale * sum(b) / sum(self.prior_counts.values)
    return log_odds_ratio_with_prior_from_counts(ap, bp)

class CorpusBasedTermScorer(with_metaclass(ABCMeta, object)):

    def __init__(self, corpus: 'ParsedCorpus', *args, **kwargs):
        self.corpus_ = corpus
        self.category_ids_ = corpus._y
        self.tdf_ = None
        self.use_metadata_ = kwargs.get('non_text', False) or kwargs.get('use_metadata', False) or kwargs.get('use_non_text_features', False)
        self.category_name_is_set_ = False
        self._doc_sizes = None
        self._set_scorer_args(**kwargs)
        self.term_ranker_ = self._get_default_ranker(corpus)

    def _get_default_ranker(self, corpus):
        return AbsoluteFrequencyRanker(corpus).set_non_text(non_text=self.use_metadata_)

    @abstractmethod
    def _set_scorer_args(self, **kwargs):
        pass

    def set_doc_sizes(self, doc_sizes: np.array) -> 'CorpusBasedTermScorer':
        assert len(doc_sizes) == self.corpus_.get_num_docs()
        self._doc_sizes = doc_sizes
        return self

    def use_token_counts_as_doc_sizes(self) -> 'CorpusBasedTermScorer':
        return self.set_doc_sizes(doc_sizes=self.corpus_.get_parsed_docs().apply(len).values)

    def get_doc_sizes(self) -> np.array:
        if self._doc_sizes is None:
            return self._get_X().sum(axis=1)
        return self._doc_sizes

    def _get_cat_size(self) -> float:
        return self.get_doc_sizes()[self._get_cat_x_row_mask()].sum()

    def _get_ncat_size(self) -> float:
        return self.get_doc_sizes()[self._get_ncat_x_row_mask()].sum()

    def use_metadata(self) -> 'CorpusBasedTermScorer':
        self.use_metadata_ = True
        self.term_ranker_ = self.term_ranker_.use_non_text_features()
        return self

    def set_term_ranker(self, term_ranker) -> 'CorpusBasedTermScorer':
        if inherits_from(term_ranker, 'TermRanker'):
            self.term_ranker_ = term_ranker(self.corpus_)
        else:
            self.term_ranker_ = term_ranker
        if self.use_metadata_:
            self.term_ranker_.use_non_text_features()
        return self

    def get_term_ranker(self) -> TermRanker:
        return self.term_ranker_

    def is_category_name_set(self):
        return self.category_name_is_set_

    def set_categories(self, category_name, not_category_names=[], neutral_category_names=[]):
        """
        Specify the category to score. Optionally, score against a specific set of categories.
        """
        tdf = self.term_ranker_.set_non_text(non_text=self.use_metadata_).get_ranks(label_append='')
        d = {'cat': tdf[str(category_name)]}
        if not_category_names == []:
            not_category_names = [str(c) for c in self.corpus_.get_categories() if c != category_name]
        else:
            not_category_names = [str(c) for c in not_category_names]
        d['ncat'] = tdf[not_category_names].sum(axis=1)
        if neutral_category_names == []:
            pass
        else:
            neutral_category_names = [str(c) for c in neutral_category_names]
        for i, c in enumerate(neutral_category_names):
            d['neut%s' % i] = tdf[c]
        self.tdf_ = pd.DataFrame(d)
        self.category_name = category_name
        self.not_category_names = [c for c in not_category_names]
        self.neutral_category_names = [c for c in neutral_category_names]
        self.category_name_is_set_ = True
        return self

    def _get_X(self):
        return self.term_ranker_.get_term_doc_mat()

    def get_t_statistics(self):
        """
        In this case, parameters a and b aren't used, since this information is taken
        directly from the corpus categories.

        Returns
        -------

        """
        X = self._get_X()
        cat_X, ncat_X = self._get_cat_and_ncat(X)
        mean_delta = self._get_mean_delta(cat_X, ncat_X)
        cat_var = sparse_var(cat_X)
        ncat_var = sparse_var(ncat_X)
        cat_n = cat_X.shape[0]
        ncat_n = ncat_X.shape[0]
        pooled_stderr = np.sqrt(cat_var / cat_n + ncat_var / ncat_n)
        tt = mean_delta / pooled_stderr
        degs_of_freedom = (cat_var ** 2 / cat_n + ncat_var ** 2 / ncat_n) ** 2 / ((cat_var ** 2 / cat_n) ** 2 / (cat_n - 1) + (ncat_var ** 2 / ncat_n) ** 2 / (ncat_n - 1))
        only_in_neutral_mask = self.tdf_[['cat', 'ncat']].sum(axis=1) == 0
        pvals = stats.t.sf(np.abs(tt), degs_of_freedom)
        tt[only_in_neutral_mask] = 0
        pvals[only_in_neutral_mask] = 0
        return (tt, pvals)

    def _get_mean_delta(self, cat_X, ncat_X):
        return np.array(cat_X.mean(axis=0) - ncat_X.mean(axis=0))[0]

    def _get_cat_and_ncat(self, X):
        if self.category_name_is_set_ is False:
            raise NeedToSetCategoriesException()
        try:
            if X.format == 'coo':
                X = X.tocsr()
        except:
            pass
        cat_X = X[self._get_cat_x_row_mask(), :]
        ncat_X = X[self._get_ncat_x_row_mask(), :]
        if self.neutral_category_names:
            neut_X = X[self._get_neut_row_mask(), :]
            cat_X = vstack([cat_X, neut_X])
            ncat_X = vstack([ncat_X, neut_X])
        return (cat_X, ncat_X)

    def _get_neut_row_mask(self):
        return np.isin(self.corpus_.get_category_names_by_row(), self.neutral_category_names)

    def _get_ncat_x_row_mask(self):
        return np.isin(self.corpus_.get_category_names_by_row(), self.not_category_names)

    def _get_cat_x_row_mask(self):
        return np.isin(self.corpus_.get_category_names_by_row(), [self.category_name])

    def _get_index(self):
        return self.corpus_.get_metadata() if self.use_metadata_ else self.corpus_.get_terms()

    @abstractmethod
    def get_scores(self, *args):
        """
        Args are ignored

        Returns
        -------
        """

    @abstractmethod
    def get_name(self):
        pass

    def _get_terms(self):
        return self.corpus_.get_terms(use_metadata=self.use_metadata_)

    def _get_num_terms(self):
        return self.corpus_.get_num_terms(non_text=self.use_metadata_)

    def get_score_df(self, label_append=''):
        return self.get_term_ranker().get_ranks(label_append=label_append).assign(Metric=self.get_scores()).sort_values(by='Metric', ascending=True).rename(columns={'Metric': self.get_name()})

    def __get_f1_f2_from_args(self, args) -> Tuple[np.array, np.array]:
        f1, f2 = args
        assert len(f1) == len(f2)
        assert len(f1) == len(self._get_terms())
        return (f1, f2)

def _get_default_ranker(self, corpus):
    return AbsoluteFrequencyRanker(corpus).set_non_text(non_text=self.use_metadata_)

def use_metadata(self) -> 'CorpusBasedTermScorer':
    self.use_metadata_ = True
    self.term_ranker_ = self.term_ranker_.use_non_text_features()
    return self

def set_term_ranker(self, term_ranker) -> 'CorpusBasedTermScorer':
    if inherits_from(term_ranker, 'TermRanker'):
        self.term_ranker_ = term_ranker(self.corpus_)
    else:
        self.term_ranker_ = term_ranker
    if self.use_metadata_:
        self.term_ranker_.use_non_text_features()
    return self

def set_categories(self, category_name, not_category_names=[], neutral_category_names=[]):
    """
        Specify the category to score. Optionally, score against a specific set of categories.
        """
    tdf = self.term_ranker_.set_non_text(non_text=self.use_metadata_).get_ranks(label_append='')
    d = {'cat': tdf[str(category_name)]}
    if not_category_names == []:
        not_category_names = [str(c) for c in self.corpus_.get_categories() if c != category_name]
    else:
        not_category_names = [str(c) for c in not_category_names]
    d['ncat'] = tdf[not_category_names].sum(axis=1)
    if neutral_category_names == []:
        pass
    else:
        neutral_category_names = [str(c) for c in neutral_category_names]
    for i, c in enumerate(neutral_category_names):
        d['neut%s' % i] = tdf[c]
    self.tdf_ = pd.DataFrame(d)
    self.category_name = category_name
    self.not_category_names = [c for c in not_category_names]
    self.neutral_category_names = [c for c in neutral_category_names]
    self.category_name_is_set_ = True
    return self

class CraigsZetaScorer(CorpusBasedTermScorer):
    """
    Zeta function from:

    Pervez Rizvi. The interpretation of Zeta test results.
    Digital Scholarship in the Humanities, Volume 34, Issue 2, June 2019, Pages 401–418,

    The score assumes that each document ("segment" in this literature) is approximately of equal size.
    Rizvi reports segment sizes being 900-6,000 words.

    Z_t = (# segments with type t labeled in the target category)/(# segments in target category) +
     (# segments with type t labeled not in the target category)/(# segments not in target category)

    """

    def _set_scorer_args(self, **kwargs):
        self.constant = kwargs.get('constant', 0.01)

    def _get_default_ranker(self, corpus):
        return OncePerDocFrequencyRanker(corpus)

    def get_scores(self, *args):
        """
        In this case, args aren't used, since this information is taken
        directly from the corpus categories.

        Returns
        -------
        np.array, scores
        """
        X = self._get_X() > 0
        cat_X, ncat_X = self._get_cat_and_ncat(X)
        return self._get_zeta_score(cat_X, ncat_X)

    def get_score_df(self, *args):
        """
        In this case, args aren't used, since this information is taken
        directly from the corpus categories.

        Returnss
        -------
        np.array, scores
        """
        X = self._get_X() > 0
        cat_X, ncat_X = self._get_cat_and_ncat(X)
        score = self._get_zeta_score(cat_X, ncat_X)
        return pd.DataFrame({'Term': self.corpus_.get_terms(use_metadata=self.use_metadata_), 'Base': cat_X.sum(axis=0).A1, 'Counter': ncat_X.sum(axis=0).A1, 'Score': score}).set_index('Term')

    def _get_zeta_score(self, cat_X, ncat_X):
        in_target_cat = cat_X.sum(axis=0) / cat_X.shape[1]
        not_in_non_target_cat = (ncat_X.shape[1] - ncat_X.sum(axis=0)) / ncat_X.shape[1]
        return (in_target_cat + not_in_non_target_cat).A1

    def get_name(self):
        return "Craig's Zeta"

def _get_default_ranker(self, corpus):
    return OncePerDocFrequencyRanker(corpus)

class GanttChart(object):
    """
	Note: the Gantt charts listed here are inspired by
	Dustin Arendt and Svitlana Volkova. ESTEEM: A Novel Framework for Qualitatively Evaluating and
	Visualizing Spatiotemporal Embeddings in Social Media. ACL System Demonstrations. 2017.
	http://www.aclweb.org/anthology/P/P17/P17-4005.pdf

	In order to use the make chart function, Altair must be installed.
	"""

    def __init__(self, term_doc_matrix, category_to_timestep_func, is_gap_between_sequences_func, timesteps_to_lag=4, num_top_terms_each_timestep=10, num_terms_to_include=40, starting_time_step=None, term_ranker=AbsoluteFrequencyRanker, term_scorer=RankDifference()):
        """
		Parameters
		----------
		term_doc_matrix : TermDocMatrix
		category_to_timestep_func : lambda
		is_gap_between_sequences_func : lambda
			timesteps_to_lag : int
		num_top_terms_each_timestep : int
		num_terms_to_include : int
		starting_time_step : object
		term_ranker : TermRanker
		term_scorer : TermScorer
		"""
        self.corpus = term_doc_matrix
        self.timesteps_to_lag = timesteps_to_lag
        self.num_top_terms_each_timestep = num_top_terms_each_timestep
        self.num_terms_to_include = num_terms_to_include
        self.is_gap_between_sequences_func = is_gap_between_sequences_func
        self.category_to_timestep_func = category_to_timestep_func
        self.term_ranker = term_ranker
        self.term_scorer = term_scorer
        categories = list(sorted(self.corpus.get_categories()))
        if len(categories) <= timesteps_to_lag:
            raise Exception('The number of categories in the term doc matrix is <= ' + str(timesteps_to_lag))
        if starting_time_step is None:
            starting_time_step = categories[timesteps_to_lag + 1]
        self.starting_time_step = starting_time_step

    def make_chart(self):
        """
		Returns
		-------
		altair.Chart
		"""
        task_df = self.get_task_df()
        import altair as alt
        chart = alt.Chart(task_df).mark_bar().encode(x='start', x2='end', y='term')
        return chart

    def get_temporal_score_df(self):
        """
		Returns
		-------

		"""
        scoredf = {}
        tdf = self.term_ranker(self.corpus).get_ranks()
        for cat in sorted(self.corpus.get_categories()):
            if cat >= self.starting_time_step:
                negative_categories = self._get_negative_categories(cat, tdf)
                scores = self.term_scorer.get_scores(tdf[cat + ' freq'].astype(int), tdf[negative_categories].sum(axis=1))
                scoredf[cat + ' score'] = scores
                scoredf[cat + ' freq'] = tdf[cat + ' freq'].astype(int)
        return pd.DataFrame(scoredf)

    def _get_negative_categories(self, cat, tdf):
        return sorted([x for x in tdf.columns if x < cat])[-self.timesteps_to_lag:]

    def _get_term_time_df(self):
        data = []
        tdf = self.term_ranker(self.corpus).get_ranks()
        for cat in sorted(self.corpus.get_categories()):
            if cat >= self.starting_time_step:
                negative_categories = self._get_negative_categories(cat, tdf)
                scores = self.term_scorer.get_scores(tdf[cat + ' freq'].astype(int), tdf[negative_categories].sum(axis=1))
                top_term_indices = np.argsort(-scores)[:self.num_top_terms_each_timestep]
                for term in tdf.index[top_term_indices]:
                    data.append({'time': self.category_to_timestep_func(cat), 'term': term, 'top': 1})
        return pd.DataFrame(data)

    def get_task_df(self):
        """
		Returns
		-------

		"""
        term_time_df = self._get_term_time_df()
        terms_to_include = term_time_df.groupby('term')['top'].sum().sort_values(ascending=False).iloc[:self.num_terms_to_include].index
        task_df = term_time_df[term_time_df.term.isin(terms_to_include)][['time', 'term']].groupby('term').apply(lambda x: pd.Series(self._find_sequences(x['time']))).reset_index().rename({0: 'sequence'}, axis=1).reset_index().assign(start=lambda x: x['sequence'].apply(lambda x: x[0])).assign(end=lambda x: x['sequence'].apply(lambda x: x[1]))[['term', 'start', 'end']]
        return task_df

    def _find_sequences(self, time_steps):
        min_timestep = None
        last_timestep = None
        sequences = []
        cur_sequence = []
        for cur_timestep in sorted(time_steps):
            if min_timestep is None:
                cur_sequence = [cur_timestep]
                min_timestep = cur_timestep
            elif not self.is_gap_between_sequences_func(last_timestep, cur_timestep):
                cur_sequence.append(cur_timestep)
                min_timestep = cur_timestep
            else:
                sequences.append([cur_sequence[0], cur_sequence[-1]])
                cur_sequence = [cur_timestep]
            last_timestep = cur_timestep
        if len(cur_sequence) != []:
            sequences.append([cur_sequence[0], cur_sequence[-1]])
        return sequences

def __init__(self, term_doc_matrix, category_to_timestep_func, is_gap_between_sequences_func, timesteps_to_lag=4, num_top_terms_each_timestep=10, num_terms_to_include=40, starting_time_step=None, term_ranker=AbsoluteFrequencyRanker, term_scorer=RankDifference()):
    """
		Parameters
		----------
		term_doc_matrix : TermDocMatrix
		category_to_timestep_func : lambda
		is_gap_between_sequences_func : lambda
			timesteps_to_lag : int
		num_top_terms_each_timestep : int
		num_terms_to_include : int
		starting_time_step : object
		term_ranker : TermRanker
		term_scorer : TermScorer
		"""
    self.corpus = term_doc_matrix
    self.timesteps_to_lag = timesteps_to_lag
    self.num_top_terms_each_timestep = num_top_terms_each_timestep
    self.num_terms_to_include = num_terms_to_include
    self.is_gap_between_sequences_func = is_gap_between_sequences_func
    self.category_to_timestep_func = category_to_timestep_func
    self.term_ranker = term_ranker
    self.term_scorer = term_scorer
    categories = list(sorted(self.corpus.get_categories()))
    if len(categories) <= timesteps_to_lag:
        raise Exception('The number of categories in the term doc matrix is <= ' + str(timesteps_to_lag))
    if starting_time_step is None:
        starting_time_step = categories[timesteps_to_lag + 1]
    self.starting_time_step = starting_time_step

def get_temporal_score_df(self):
    """
		Returns
		-------

		"""
    scoredf = {}
    tdf = self.term_ranker(self.corpus).get_ranks()
    for cat in sorted(self.corpus.get_categories()):
        if cat >= self.starting_time_step:
            negative_categories = self._get_negative_categories(cat, tdf)
            scores = self.term_scorer.get_scores(tdf[cat + ' freq'].astype(int), tdf[negative_categories].sum(axis=1))
            scoredf[cat + ' score'] = scores
            scoredf[cat + ' freq'] = tdf[cat + ' freq'].astype(int)
    return pd.DataFrame(scoredf)

def _get_term_time_df(self):
    data = []
    tdf = self.term_ranker(self.corpus).get_ranks()
    for cat in sorted(self.corpus.get_categories()):
        if cat >= self.starting_time_step:
            negative_categories = self._get_negative_categories(cat, tdf)
            scores = self.term_scorer.get_scores(tdf[cat + ' freq'].astype(int), tdf[negative_categories].sum(axis=1))
            top_term_indices = np.argsort(-scores)[:self.num_top_terms_each_timestep]
            for term in tdf.index[top_term_indices]:
                data.append({'time': self.category_to_timestep_func(cat), 'term': term, 'top': 1})
    return pd.DataFrame(data)

class DenseRankCharacteristicness(CharacteristicScorer):

    def get_scores(self, corpus):
        """
		Parameters
		----------
		corpus

		Returns
		-------
		(float, pd.Series)
		float: point on x-axis at even characteristicness
		pd.Series: term -> value between 0 and 1, sorted by score in a descending manner
			Background scores from corpus
		"""
        term_ranks = self.term_ranker(corpus).get_ranks()
        freq_df = pd.DataFrame({'corpus': term_ranks.sum(axis=1), 'standard': self.background_frequencies.get_background_frequency_df()['background']})
        freq_df = freq_df.loc[freq_df['corpus'].dropna().index].fillna(0)
        corpus_rank = rankdata(freq_df.corpus, 'dense')
        standard_rank = rankdata(freq_df.standard, 'dense')
        scores = corpus_rank / corpus_rank.max() - standard_rank / standard_rank.max()
        if self.rerank_ranks:
            rank_scores, zero_marker = self._rerank_scores(scores)
            freq_df['score'] = pd.Series(rank_scores, index=freq_df.index)
        else:
            if scores.min() < 0 and scores.max() > 0:
                zero_marker = -scores.min() / (scores.max() - scores.min())
            elif scores.min() > 0:
                zero_marker = 0
            else:
                zero_marker = 1
            freq_df['score'] = scale(scores)
        return (zero_marker, freq_df.sort_values(by='score', ascending=False)['score'])

def get_scores(self, corpus):
    """
		Parameters
		----------
		corpus

		Returns
		-------
		(float, pd.Series)
		float: point on x-axis at even characteristicness
		pd.Series: term -> value between 0 and 1, sorted by score in a descending manner
			Background scores from corpus
		"""
    term_ranks = self.term_ranker(corpus).get_ranks()
    freq_df = pd.DataFrame({'corpus': term_ranks.sum(axis=1), 'standard': self.background_frequencies.get_background_frequency_df()['background']})
    freq_df = freq_df.loc[freq_df['corpus'].dropna().index].fillna(0)
    corpus_rank = rankdata(freq_df.corpus, 'dense')
    standard_rank = rankdata(freq_df.standard, 'dense')
    scores = corpus_rank / corpus_rank.max() - standard_rank / standard_rank.max()
    if self.rerank_ranks:
        rank_scores, zero_marker = self._rerank_scores(scores)
        freq_df['score'] = pd.Series(rank_scores, index=freq_df.index)
    else:
        if scores.min() < 0 and scores.max() > 0:
            zero_marker = -scores.min() / (scores.max() - scores.min())
        elif scores.min() > 0:
            zero_marker = 0
        else:
            zero_marker = 1
        freq_df['score'] = scale(scores)
    return (zero_marker, freq_df.sort_values(by='score', ascending=False)['score'])

