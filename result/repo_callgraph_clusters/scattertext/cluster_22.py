# Cluster 22

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

class ScatterChartExplorer(ScatterChart):

    def __init__(self, corpus, verbose=False, **kwargs):
        """See ScatterChart.  This lets you click on terms to see what contexts they tend to appear in.
        Running the `to_dict` function outputs
        """
        ScatterChart.__init__(self, corpus, verbose, **kwargs)
        self._term_metadata = None

    def to_dict(self, category, category_name=None, not_category_name=None, scores=None, metadata=None, max_docs_per_category=None, transform=percentile_alphabetical, alternative_text_field=None, title_case_names=False, not_categories=None, neutral_categories=None, extra_categories=None, neutral_category_name=None, extra_category_name=None, background_scorer=None, include_term_category_counts=False, use_offsets=False, **kwargs):
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
        metadata, None or array-like.
          List of metadata for each document.  Defaults to a list of blank strings.
        max_docs_per_category, None or int, optional
          Maximum number of documents to store per category.  Defaults to 4.
        transform : function, optional
            Function for ranking terms.  Defaults to scattertext.Scalers.percentile_lexicographic.
        alternative_text_field : str or None, optional
            Field in from dataframe used to make corpus to display in place of parsed text. Only
            can be used if corpus is a ParsedCorpus instance.
        title_case_names : bool, default False
          Should the program title-case the category and not-category names?
        not_categories : list, optional
            List of categories to use as "not category".  Defaults to all others.
        neutral_categories : list, optional
            List of categories to use as neutral.  Defaults [].
        extra_categories : list, optional
            List of categories to use as extra.  Defaults [].
        neutral_category_name : str
            "Neutral" by default. Only active if show_neutral is True.  Name of the neutra l
            column.
        extra_category_name : str
            "Extra" by default. Only active if show_neutral and show_extra are true. Name of the
            extra column.
        background_scorer : CharacteristicScorer, optional
            Used for bg scores
        include_term_category_counts : bool, default False
            Includes term-category counts in keyed off 'term-category-count'. If use_non_text_features,
            use metadata counts instead.

        Returns
        -------
        dictionary {info: {'category_name': full category name, ...},
                    docs: {'texts': [doc1text, ...],
                            'labels': [1, 0, ...],
                            'meta': ['<b>blah</b>', '<b>blah</b>']},

                    // if include_term_category_counts
                    termCounts: [term num -> [total occurrences, total documents, variance], ... for the number of categories]

                    data: {term:term,
                           x:frequency [0-1],
                           y:frequency [0-1],
                           s: score,
                           bg: background score,
                           as: association score,
                           cat25k: freq per 25k in category,
                           cat: count in category,
                           ncat: count in non-category,
                           catdocs: [docnum, ...],
                           ncatdocs: [docnum, ...]
                           ncat25k: freq per 25k in non-category}
                           etc: term specific dictionary (if inject_term_metadata is called and contains terms)}
        """
        if kwargs is not {} and self.verbose:
            logging.info('Excessive arguments passed to ScatterChartExplorer.to_dict: ' + str(kwargs))
        json_data = ScatterChart.to_dict(self, category, category_name=category_name, not_category_name=not_category_name, scores=scores, transform=transform, title_case_names=title_case_names, not_categories=not_categories, neutral_categories=neutral_categories, extra_categories=extra_categories, background_scorer=background_scorer, use_offsets=use_offsets)
        docs_getter = self._make_docs_getter(max_docs_per_category, alternative_text_field)
        if neutral_category_name is None:
            neutral_category_name = 'Neutral'
        if extra_category_name is None:
            extra_category_name = 'Extra'
        metadata_series = metadata
        if callable(metadata):
            metadata_series = metadata(self.term_doc_matrix)
        json_data['docs'] = self._get_docs_structure(docs_getter, metadata_series)
        json_data['info']['neutral_category_name'] = neutral_category_name
        json_data['info']['extra_category_name'] = extra_category_name
        if include_term_category_counts:
            terms = np.array([term_struct['term'] for term_struct in json_data['data']])
            json_data['termCounts'] = self._get_term_doc_counts(terms)
        return json_data

    def _get_term_doc_counts(self, terms):
        term_counts = []
        if self.scatterchartdata.use_non_text_features:
            term_doc_counts = self.term_doc_matrix.get_metadata_doc_count_df('').loc[terms]
            term_doc_freq = self.term_doc_matrix.get_metadata_freq_df('').loc[terms]
        else:
            term_doc_counts = self.term_doc_matrix.get_term_doc_count_df('').loc[terms]
            term_doc_freq = self.term_doc_matrix.get_term_freq_df('').loc[terms]
        term2idx = pd.Series(np.arange(len(terms)), index=terms)
        for category_i, category in enumerate(self.term_doc_matrix.get_categories()):
            category = str(category)
            term_ser = term_doc_freq[category]
            doc_ser = term_doc_counts[category]
            term_ser = term_ser[term_ser.values > 0]
            doc_ser = doc_ser[doc_ser.values > 0]
            category_counts = pd.Series(np.array([term_ser.values, doc_ser.values]).T.tolist(), index=term2idx[term_ser.index].values).to_dict()
            term_counts.append(category_counts)
        return term_counts

    def _make_docs_getter(self, max_docs_per_category, alternative_text_field):
        if max_docs_per_category is None:
            docs_getter = DocsAndLabelsFromCorpus(self.term_doc_matrix, alternative_text_field=alternative_text_field)
        else:
            docs_getter = DocsAndLabelsFromCorpusSample(self.term_doc_matrix, max_docs_per_category, alternative_text_field=alternative_text_field)
        if self.scatterchartdata.use_non_text_features or self.scatterchartdata.add_extra_features:
            docs_getter = docs_getter.use_non_text_features()
            if self.scatterchartdata.add_extra_features:
                docs_getter = docs_getter.use_terms_for_extra_features()
        return docs_getter

    def _get_docs_structure(self, docs_getter, metadata):
        if metadata is not None:
            return docs_getter.get_labels_and_texts_and_meta(np.array(metadata))
        else:
            return docs_getter.get_labels_and_texts()

    def _add_term_freq_to_json_df(self, json_df, term_freq_df, category):
        json_df = ScatterChart._add_term_freq_to_json_df(self, json_df, term_freq_df, category).assign(cat=term_freq_df[str(category) + ' freq'].astype(int), ncat=term_freq_df['not cat freq'].astype(int))
        if self._term_metadata is not None:
            json_df = json_df.assign(etc=term_freq_df['term'].apply(lambda term: self._term_metadata.get(term, {})))
        return json_df

    def inject_term_metadata(self, metadata):
        """

        :param metadata: dict, maps terms to a dictionary which will be added to term's json structure
        :return: ScatterChartExplorer
        """
        self._term_metadata = metadata
        return self

    def inject_term_metadata_df(self, metadata_df):
        """

        :param metadata_df: pd.DataFrame, indexed on terms with columns as structure
        :return: ScatterChartExplorer
        """
        term_metadata_dict = metadata_df.T.to_dict()
        return self.inject_term_metadata(term_metadata_dict)

def _add_term_freq_to_json_df(self, json_df, term_freq_df, category):
    json_df = ScatterChart._add_term_freq_to_json_df(self, json_df, term_freq_df, category).assign(cat=term_freq_df[str(category) + ' freq'].astype(int), ncat=term_freq_df['not cat freq'].astype(int))
    if self._term_metadata is not None:
        json_df = json_df.assign(etc=term_freq_df['term'].apply(lambda term: self._term_metadata.get(term, {})))
    return json_df

def pyplot_from_scattertext_structure(scatterplot_structure, figsize, textsize, distance_margin_fraction, scatter_size, cmap, sample, xlabel, ylabel, dpi, draw_lines, linecolor, draw_all, nbr_candidates, num_top_terms: int=10):
    """
    Parameters
    ----------
    scatterplot_structure : ScatterplotStructure
    figsize : Tuple[int,int]
        Size of ouput pyplot figure
    textsize : int
        Size of text terms in plot
    distance_margin_fraction : float
        Fraction of the 2d space to use as margins for text bboxes
    scatter_size : int
        Size of scatter disks
    cmap : str
        Matplotlib compatible colormap string
    sample : int
        if >0 samples a subset from the scatterplot_structure, used for testing
    xlabel : str
        Overrides label from scatterplot_structure
    ylabel : str
        Overrides label from scatterplot_structure
    dpi : int
        Pyplot figure resolution
    num_top_terms : int
        Overrides scatterplot_structure.top_terms_length, default is 10

    Returns
    -------
    matplotlib.figure.Figure
    matplotlib figure that can be used with plt.show() or plt.savefig()

    """
    try:
        import matplotlib.pyplot as plt
        import textalloc as ta
    except:
        raise Exception('Ensure that the packages textalloc==0.0.3 and matplotlib>=3.6.0 have been installed.')
    if scatterplot_structure._top_terms_length != 14:
        print('Warning: set the number of top terms to using the `num_top_terms` parameter to this function. ' + 'The number of characteristic terms will be scaled accordingly.')
    scatterplot_structure.top_terms_length = num_top_terms
    if sample > 0:
        subset = random.sample(scatterplot_structure._visualization_data.word_dict['data'], sample)
    else:
        subset = scatterplot_structure._visualization_data.word_dict['data']
    df = pd.DataFrame(subset)
    if 'etc' in scatterplot_structure._visualization_data.word_dict['data'][0] and 'ColorScore' in scatterplot_structure._visualization_data.word_dict['data'][0]['etc']:
        df['s'] = [d['etc']['ColorScore'] for d in subset]
    info = scatterplot_structure._visualization_data.word_dict['info']
    n_docs = len(scatterplot_structure._visualization_data.word_dict['docs']['texts'])
    n_words = df.shape[0]
    if df.s.isna().sum() > 0:
        colors = 'k'
    else:
        colors = df.s
    ax_plot = None
    if scatterplot_structure._ignore_categories:
        if scatterplot_structure._show_characteristic:
            fig, axs = plt.subplots(1, 2, figsize=figsize, width_ratios=[5, 1], dpi=dpi)
            ax_char = axs[1]
        else:
            fig, ax_plot = plt.subplots(1, 1, figsize=figsize, dpi=dpi)
    elif scatterplot_structure._show_characteristic:
        fig, axs = plt.subplots(1, 3, figsize=figsize, width_ratios=[6, 1, 1], dpi=dpi)
        ax_cat = axs[1]
        ax_char = axs[2]
    else:
        fig, axs = plt.subplots(1, 2, figsize=figsize, width_ratios=[5, 1], dpi=dpi)
        ax_cat = axs[1]
    plt.tight_layout()
    if ax_plot is None:
        ax_plot = axs[0]
    ax_plot.scatter(df.x, df.y, c=colors, s=scatter_size, cmap=cmap)
    xlims = ax_plot.get_xlim()
    ylims = ax_plot.get_ylim()
    ta.allocate_text(fig, ax_plot, df.x, df.y, df.term, xlims, ylims, x_scatter=df.x, y_scatter=df.y, textsize=textsize, distance_margin_fraction=distance_margin_fraction, draw_lines=draw_lines, linecolor=linecolor, draw_all=draw_all, nbr_candidates=nbr_candidates)
    ax_plot.spines.right.set_visible(False)
    ax_plot.spines.top.set_visible(False)
    if xlabel is not None:
        ax_plot.set_xlabel(xlabel)
    elif scatterplot_structure._x_label is not None:
        ax_plot.set_xlabel(scatterplot_structure._x_label)
    elif not scatterplot_structure._ignore_categories:
        ax_plot.set_xlabel(info['not_category_name'])
    else:
        pass
    if ylabel is not None:
        ax_plot.set_ylabel(ylabel)
    elif scatterplot_structure._y_label is not None:
        ax_plot.set_ylabel(scatterplot_structure._y_label)
    elif not scatterplot_structure._ignore_categories:
        ax_plot.set_ylabel(info['category_name'])
    else:
        pass
    try:
        if scatterplot_structure._x_axis_labels is not None:
            ax_plot.locator_params(axis='x', nbins=len(scatterplot_structure._x_axis_labels))
            ax_plot.set_xticks(ax_plot.get_xticks()[1:-1], scatterplot_structure._x_axis_labels, size=7)
        else:
            ax_plot.locator_params(axis='x', nbins=3)
            ax_plot.set_xticks(ax_plot.get_xticks()[1:-1], ['Low', 'Medium', 'High'], size=7)
    except:
        pass
    try:
        if scatterplot_structure._y_axis_labels is not None:
            ax_plot.locator_params(axis='y', nbins=len(scatterplot_structure._y_axis_labels))
            ax_plot.set_yticks(ax_plot.get_yticks()[1:-1], scatterplot_structure._y_axis_labels, size=7, rotation=90)
        else:
            scatterplot_structure._y_axis_labels
            ax_plot.set_yticks(ax_plot.get_yticks()[1:-1], ['Low', 'Medium', 'High'], size=7, rotation=90)
    except:
        pass
    if scatterplot_structure._show_diagonal:
        ax_plot.plot([xlims[0], xlims[1]], [ylims[0], ylims[1]], color='k', linestyle='dashed', linewidth=1, alpha=0.3)
    alignment = {'horizontalalignment': 'left', 'verticalalignment': 'top'}
    total_top_terms = scatterplot_structure.top_terms_length * 2 + 2
    if not scatterplot_structure._ignore_categories:
        yp = [i / total_top_terms for i in range(total_top_terms)]
        yp.reverse()
        ax_cat.text(0.0, yp[0], 'Top ' + info['category_name'], weight='bold', size='medium', **alignment)
        for i, term in enumerate(info['category_terms']):
            ax_cat.text(0.0, yp[i + 1], term, size='small', **alignment)
        ax_cat.text(0.0, yp[scatterplot_structure.top_terms_length + 1], 'Top ' + info['not_category_name'], weight='bold', size='medium', **alignment)
        for i, term in enumerate(info['not_category_terms']):
            axs[1].text(0.0, yp[i + scatterplot_structure + 2], term, size='small', **alignment)
        ax_cat.spines.right.set_visible(False)
        ax_cat.spines.top.set_visible(False)
        ax_cat.spines.bottom.set_visible(False)
        ax_cat.spines.left.set_visible(False)
        ax_cat.set_xticks([])
        ax_cat.set_yticks([])
    if scatterplot_structure._show_characteristic:
        yp = [i / total_top_terms + 2 for i in range(total_top_terms + 2)]
        yp.reverse()
        ax_char.text(0.0, yp[0], 'Characteristic', weight='bold', size='medium', **alignment)
        characteristic_terms = list(df.sort_values('bg', axis=0, ascending=False).iloc[:total_top_terms + 1].term)
        for i, term in enumerate(characteristic_terms):
            ax_char.text(0.0, yp[i + 1], term, size='small', **alignment)
        ax_char.spines.right.set_visible(False)
        ax_char.spines.top.set_visible(False)
        ax_char.spines.bottom.set_visible(False)
        ax_char.spines.left.set_visible(False)
        ax_char.set_xticks([])
        ax_char.set_yticks([])
    fig.suptitle(f'Document count: {n_docs} - Word count: {n_words}', ha='right')
    return fig

