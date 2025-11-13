# Cluster 8

class FlashTextExtact(st.FeatsFromSpacyDoc):
    """

    """

    def set_keyword_processor(self, keyword_processor):
        """
    
        :param keyword_processor: set, phrases to look for
        :return: self
        """
        self.keyword_processor_ = keyword_processor
        return self

    def get_feats(self, doc):
        """
        Parameters
        ----------
        doc, Spacy Doc

        Returns
        -------
        Counter noun chunk -> count
        """
        return Counter(self.keyword_processor_.extract_keywords(str(doc)))

def get_feats(self, doc):
    """
        Parameters
        ----------
        doc, Spacy Doc

        Returns
        -------
        Counter noun chunk -> count
        """
    return Counter(self.keyword_processor_.extract_keywords(str(doc)))

def round_downer(x):
    power_of_ten = 10 ** (len(str(int(x))) - 1)
    num = power_of_ten * (x // power_of_ten)
    return num

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

def _get_coordinates_from_transform_and_jitter_frequencies(self, category, df, other_categories, transform):
    not_counts = df[[str(c) + ' freq' for c in other_categories]].sum(axis=1)
    counts = df[str(category) + ' freq']
    x_data_raw = transform(not_counts, df.index, counts)
    y_data_raw = transform(counts, df.index, not_counts)
    x_data = self._add_jitter(x_data_raw)
    y_data = self._add_jitter(y_data_raw)
    return (x_data, y_data)

def _filter_bigrams_by_minimum_not_category_term_freq(self, category_column_name, other_categories, df):
    if self.scatterchartdata.terms_to_include is None and self.scatterchartdata.dont_filter is False:
        return df[(df[str(category_column_name)] > 0) | (df[[str(c) + ' freq' for c in other_categories]].sum(axis=1) >= self.scatterchartdata.minimum_not_category_term_frequency)]
    else:
        return df

def _filter_by_minimum_term_frequency(self, all_categories, df):
    if self.scatterchartdata.terms_to_include is None and self.scatterchartdata.dont_filter is False:
        df = df[lambda df: df[[str(c) + ' freq' for c in all_categories]].sum(axis=1) > self.scatterchartdata.minimum_term_frequency]
    return df

class TermDocMatrixFactory(object):

    def __init__(self, category_text_iter=None, clean_function=lambda x: x, nlp=None, feats_from_spacy_doc=None):
        """
        Class for easy construction of a term document matrix.
       This class let's you define an iterator for each document (text_iter),
       an iterator for each document's category name (category_iter),
       and a document cleaning function that's applied to each document
       before it's parsed.

       Parameters
       ----------
       category_text_iter : iter<str: category, unicode: document)>
           An iterator of pairs. The first element is a string category
           name, the second the text of a document.  You can also set this
           using the function set_category_text_iter.
       clean_function : function (default lambda x: x)
           A function that strips invalid characters out of a string, returning
           the new string.
       post_nlp_clean_function : function (default lambda x: x)
           A function that takes a spaCy Doc
       nlp : spacy.load('en_core_web_sm') (default None)
           The spaCy parser used to parse documents.  If it's None,
           the class will go through the expensive operation of
           creating one to parse the text
       feats_from_spacy_doc : FeatsFromSpacyDoc (default None)
           Class for extraction of features from spacy
       Attributes
       ----------
       _clean_function : Callable
           function that takes a unicode document and returns
           a cleaned version of that document
       _text_iter : iter<unicode>
           an iterator that iterates through the unicode text of each
            document
       _category_iter : iter<str>
           an iterator the same size as text iter that gives a string or
           unicode name of each document catgory
       Examples
       --------
       >>> import scattertext as ST
       >>> documents = [u'What art thou that usurp''st this time of night,',
       ...u'Together with that fair and warlike form',
       ...u'In which the majesty of buried Denmark',
       ...u'Did sometimes march? by heaven I charge thee, speak!',
         ...u'Halt! Who goes there?',
         ...u'[Intro]',
         ...u'It is I sire Tone from Brooklyn.',
         ...u'Well, speak up man what is it?',
         ...u'News from the East sire! THE BEST OF BOTH WORLDS HAS RETURNED!']
       >>> categories = ['hamlet'] * 4 + ['jay-z/r. kelly'] * 5
       >>> clean_function = lambda text: '' if text.startswith('[') else text
       >>> term_doc_mat = ST.TermDocMatrixFactory(category_text_iter = zip(categories, documents),clean_function = clean_function).build()
        """
        self._category_text_iter = category_text_iter
        self._clean_function = clean_function
        self._nlp = nlp
        self._entity_types_to_censor = set()
        if feats_from_spacy_doc is None:
            self._feats_from_spacy_doc = FeatsFromSpacyDoc()
        else:
            self._feats_from_spacy_doc = feats_from_spacy_doc

    def set_category_text_iter(self, category_text_iter):
        """Initializes the category_text_iter

       Paramters
       ----------
       category_text_iter : iter<str: category, unicode: document)>
               An iterator of pairs. The first element is a string category
               name, the second the text of a document.

         Returns
         ----------
         self: TermDocMatrixFactory
        """
        self._category_text_iter = category_text_iter
        return self

    def set_nlp(self, nlp):
        """Adds a spaCy-compatible nlp function

       Paramters
       ----------
       nlp : spacy model

         Returns
         ----------
         self: TermDocMatrixFactory
        """
        self._nlp = nlp
        return self

    def build(self):
        """Generate a TermDocMatrix from data in parameters.

         Returns
         ----------
         term_doc_matrix : TermDocMatrix
            The object that this factory class builds.
        """
        if self._category_text_iter is None:
            raise CategoryTextIterNotSetError()
        nlp = self.get_nlp()
        category_document_iter = ((str(category), self._clean_function(raw_text)) for category, raw_text in self._category_text_iter)
        term_doc_matrix = self._build_from_category_spacy_doc_iter(((category, nlp(text)) for category, text in category_document_iter if text.strip() != ''))
        return term_doc_matrix

    def get_nlp(self):
        nlp = self._nlp
        if nlp is None:
            import spacy
            nlp = spacy.load('en_core_web_sm')
        return nlp

    def censor_entity_types(self, entity_types):
        """
        Entity types to exclude from feature construction. Terms matching
        specificed entities, instead of labeled by their lower case orthographic
        form or lemma, will be labeled by their entity type.

        Parameters
        ----------
        entity_types : set of entity types outputted by spaCy



        Returns
        ---------
        self
        """
        assert type(entity_types) == set
        self._entity_types_to_censor = entity_types
        self._feats_from_spacy_doc = FeatsFromSpacyDoc(use_lemmas=self._use_lemmas, entity_types_to_censor=self._entity_types_to_censor)
        return self

    def _build_from_category_spacy_doc_iter(self, category_doc_iter):
        """
        Parameters
        ----------
        category_doc_iter : iterator of (string category name, spacy.tokens.doc.Doc) pairs

        Returns
        ----------
        t : TermDocMatrix
        """
        term_idx_store = IndexStore()
        category_idx_store = IndexStore()
        metadata_idx_store = IndexStore()
        X, mX, y = self._get_features_and_labels_from_documents_and_indexes(category_doc_iter, category_idx_store, term_idx_store, metadata_idx_store)
        return TermDocMatrix(X, mX, y, term_idx_store=term_idx_store, category_idx_store=category_idx_store, metadata_idx_store=metadata_idx_store)

    def _get_features_and_labels_from_documents_and_indexes(self, category_doc_iter, category_idx_store, term_idx_store, metadata_idx_store):
        y = []
        X_factory = CSRMatrixFactory()
        mX_factory = CSRMatrixFactory()
        for document_index, (category, parsed_text) in enumerate(category_doc_iter):
            self._register_doc_and_category(X_factory, mX_factory, category, category_idx_store, document_index, parsed_text, term_idx_store, metadata_idx_store, y)
        X = X_factory.get_csr_matrix()
        mX = mX_factory.get_csr_matrix()
        y = np.array(y)
        return (X, mX, y)

    def _old_register_doc_and_category(self, X_factory, category, category_idx_store, document_index, parsed_text, term_idx_store, y):
        y.append(category_idx_store.getidx(category))
        document_features = self._get_features_from_parsed_text(parsed_text, term_idx_store)
        self._register_document_features_with_X_factory(X_factory, document_index, document_features)

    def _register_doc_and_category(self, X_factory, mX_factory, category, category_idx_store, document_index, parsed_text, term_idx_store, metadata_idx_store, y):
        self._register_doc(X_factory, mX_factory, document_index, parsed_text, term_idx_store, metadata_idx_store)
        self._register_category(category, category_idx_store, y)

    def _register_doc(self, X_factory, mX_factory, document_index, parsed_text, term_idx_store, metadata_idx_store):
        for term, count in self._feats_from_spacy_doc.get_feats(parsed_text).items():
            term_idx = term_idx_store.getidx(term)
            X_factory[document_index, term_idx] = count
        for term, val in self._feats_from_spacy_doc.get_doc_metadata(parsed_text).items():
            meta_idx = metadata_idx_store.getidx(term)
            mX_factory[document_index, meta_idx] = val

    def _register_category(self, category, category_idx_store, y):
        y.append(category_idx_store.getidx(category))

    def _register_document_features_with_X_factory(self, X_factory, doci, term_freq):
        for word_idx, freq in term_freq.items():
            X_factory[doci, word_idx] = freq

    def _get_features_from_parsed_text(self, parsed_text, term_idx_store):
        return {term_idx_store.getidxstrict(k): v for k, v in self._feats_from_spacy_doc.get_feats(parsed_text).items() if k in term_idx_store}

def __init__(self, category_text_iter=None, clean_function=lambda x: x, nlp=None, feats_from_spacy_doc=None):
    """
        Class for easy construction of a term document matrix.
       This class let's you define an iterator for each document (text_iter),
       an iterator for each document's category name (category_iter),
       and a document cleaning function that's applied to each document
       before it's parsed.

       Parameters
       ----------
       category_text_iter : iter<str: category, unicode: document)>
           An iterator of pairs. The first element is a string category
           name, the second the text of a document.  You can also set this
           using the function set_category_text_iter.
       clean_function : function (default lambda x: x)
           A function that strips invalid characters out of a string, returning
           the new string.
       post_nlp_clean_function : function (default lambda x: x)
           A function that takes a spaCy Doc
       nlp : spacy.load('en_core_web_sm') (default None)
           The spaCy parser used to parse documents.  If it's None,
           the class will go through the expensive operation of
           creating one to parse the text
       feats_from_spacy_doc : FeatsFromSpacyDoc (default None)
           Class for extraction of features from spacy
       Attributes
       ----------
       _clean_function : Callable
           function that takes a unicode document and returns
           a cleaned version of that document
       _text_iter : iter<unicode>
           an iterator that iterates through the unicode text of each
            document
       _category_iter : iter<str>
           an iterator the same size as text iter that gives a string or
           unicode name of each document catgory
       Examples
       --------
       >>> import scattertext as ST
       >>> documents = [u'What art thou that usurp''st this time of night,',
       ...u'Together with that fair and warlike form',
       ...u'In which the majesty of buried Denmark',
       ...u'Did sometimes march? by heaven I charge thee, speak!',
         ...u'Halt! Who goes there?',
         ...u'[Intro]',
         ...u'It is I sire Tone from Brooklyn.',
         ...u'Well, speak up man what is it?',
         ...u'News from the East sire! THE BEST OF BOTH WORLDS HAS RETURNED!']
       >>> categories = ['hamlet'] * 4 + ['jay-z/r. kelly'] * 5
       >>> clean_function = lambda text: '' if text.startswith('[') else text
       >>> term_doc_mat = ST.TermDocMatrixFactory(category_text_iter = zip(categories, documents),clean_function = clean_function).build()
        """
    self._category_text_iter = category_text_iter
    self._clean_function = clean_function
    self._nlp = nlp
    self._entity_types_to_censor = set()
    if feats_from_spacy_doc is None:
        self._feats_from_spacy_doc = FeatsFromSpacyDoc()
    else:
        self._feats_from_spacy_doc = feats_from_spacy_doc

def _register_doc(self, X_factory, mX_factory, document_index, parsed_text, term_idx_store, metadata_idx_store):
    for term, count in self._feats_from_spacy_doc.get_feats(parsed_text).items():
        term_idx = term_idx_store.getidx(term)
        X_factory[document_index, term_idx] = count
    for term, val in self._feats_from_spacy_doc.get_doc_metadata(parsed_text).items():
        meta_idx = metadata_idx_store.getidx(term)
        mX_factory[document_index, meta_idx] = val

def _register_document_features_with_X_factory(self, X_factory, doci, term_freq):
    for word_idx, freq in term_freq.items():
        X_factory[doci, word_idx] = freq

def get_category_names(category, category_name, not_categories, not_category_name):
    category_name = str(category_name)
    if category_name is None:
        category_name = category
    if not_category_name is None:
        if not_categories is not None and len(not_categories) == 1:
            not_category_name = not_categories[0]
        else:
            not_category_name = ('Not' if category_name[0].isupper() else 'not') + ' ' + category_name
    return (category_name, not_category_name)

class TableStructure(GraphStructure):

    def __init__(self, scatterplot_structure, graph_renderer, **kwargs):
        kwargs.setdefault('template_file_name', 'table_plot.html')
        GraphStructure.__init__(self, scatterplot_structure, graph_renderer, **kwargs)

    def get_font_import(self):
        return ''

    def get_zoom_script_import(self):
        return ''

def __init__(self, scatterplot_structure, graph_renderer, **kwargs):
    kwargs.setdefault('template_file_name', 'table_plot.html')
    GraphStructure.__init__(self, scatterplot_structure, graph_renderer, **kwargs)

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

def _get_freq_df_using_idx_store(self, catX, idx_store, label_append=' freq'):
    d = {'term': idx_store._i2val}
    for idx, cat in self._category_idx_store.items():
        try:
            d[str(cat) + label_append] = catX[idx, :].A[0]
        except IndexError:
            self._fix_problem_when_final_category_index_has_no_terms(cat, catX, d, label_append)
    return pd.DataFrame(d).set_index('term')

class CorpusWithoutCategoriesFromParsedDocuments(object):

    def __init__(self, df, parsed_col, feats_from_spacy_doc=FeatsFromSpacyDoc()):
        """
        Parameters
        ----------
        df : pd.DataFrame
         contains category_col, and parse_col, were parsed col is entirely spacy docs
        parsed_col : str
            name of spacy parsed column in convention_df
        feats_from_spacy_doc : FeatsFromSpacyDoc
        """
        self.df = df
        self.parsed_col = parsed_col
        self.feats_from_spacy_doc = feats_from_spacy_doc

    def build(self):
        """

        :return: ParsedCorpus
        """
        category_col = 'Category'
        while category_col in self.df:
            category_col = 'Category_' + ''.join((np.random.choice(string.ascii_letters) for _ in range(5)))
        return CorpusFromParsedDocuments(self.df.assign(**{category_col: '_'}), category_col, self.parsed_col, feats_from_spacy_doc=self.feats_from_spacy_doc).build()

def __init__(self, df, parsed_col, feats_from_spacy_doc=FeatsFromSpacyDoc()):
    """
        Parameters
        ----------
        df : pd.DataFrame
         contains category_col, and parse_col, were parsed col is entirely spacy docs
        parsed_col : str
            name of spacy parsed column in convention_df
        feats_from_spacy_doc : FeatsFromSpacyDoc
        """
    self.df = df
    self.parsed_col = parsed_col
    self.feats_from_spacy_doc = feats_from_spacy_doc

class TermDocMatrixFromScikit(object):
    """
	A factory class for building a TermDocMatrix from a scikit-learn-processed
	dataset.

	>>> from scattertext import TermDocMatrixFromScikit
	>>> from sklearn.datasets import fetch_20newsgroups
	>>> from sklearn.feature_extraction.text import CountVectorizer
	>>> newsgroups_train = fetch_20newsgroups(subset='train', remove=('headers', 'footers', 'quotes'))
	>>> count_vectorizer = CountVectorizer()
	>>> X_counts = count_vectorizer.fit_transform(newsgroups_train.data)
	>>> term_doc_mat = TermDocMatrixFromScikit(
	...   X = X_counts,
	...   y = newsgroups_train.target,
	...   feature_vocabulary=count_vectorizer.vocabulary_,
	...   category_names=newsgroups_train.target_names
	... ).build()
	>>> term_doc_mat.get_categories()[:2]
	['alt.atheism', 'comp.graphics']
	>>> term_doc_mat.get_term_freq_df().assign(score=term_doc_mat.get_scaled_f_scores('alt.atheism')).sort_values(by='score', ascending=False).index.tolist()[:5]
	['atheism', 'atheists', 'islam', 'atheist', 'matthew']
	"""

    def __init__(self, X, y, feature_vocabulary, category_names, unigram_frequency_path=None):
        """
		Parameters
		----------
		X: sparse matrix integer, giving term-document-matrix counts
		y: list, integer categories
		feature_vocabulary: dict (feat_name -> idx)
		category_names: list of category names (len of y)
		unigram_frequency_path: str (see TermDocMatrix)
		"""
        if X.shape != (len(y), len(feature_vocabulary)):
            raise DimensionMismatchException('The shape of X is expected to be ' + str((len(y), len(feature_vocabulary))) + 'but was actually: ' + str(X.shape))
        self.X = X
        self.y = y
        self.feature_vocabulary = feature_vocabulary
        self.category_names = category_names
        self.unigram_frequency_path = unigram_frequency_path

    def build(self):
        """
		Returns
		-------
		TermDocMatrix
		"""
        constructor_kwargs = self._get_build_kwargs()
        return TermDocMatrix(**constructor_kwargs)

    def _get_build_kwargs(self):
        constructor_kwargs = {'X': self.X, 'mX': csr_matrix((0, 0)), 'y': self.y, 'term_idx_store': IndexStoreFromDict.build(self.feature_vocabulary), 'metadata_idx_store': IndexStore(), 'category_idx_store': IndexStoreFromList.build(self.category_names), 'unigram_frequency_path': self.unigram_frequency_path}
        return constructor_kwargs

def __init__(self, X, y, feature_vocabulary, category_names, unigram_frequency_path=None):
    """
		Parameters
		----------
		X: sparse matrix integer, giving term-document-matrix counts
		y: list, integer categories
		feature_vocabulary: dict (feat_name -> idx)
		category_names: list of category names (len of y)
		unigram_frequency_path: str (see TermDocMatrix)
		"""
    if X.shape != (len(y), len(feature_vocabulary)):
        raise DimensionMismatchException('The shape of X is expected to be ' + str((len(y), len(feature_vocabulary))) + 'but was actually: ' + str(X.shape))
    self.X = X
    self.y = y
    self.feature_vocabulary = feature_vocabulary
    self.category_names = category_names
    self.unigram_frequency_path = unigram_frequency_path

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

def _get_relevant_term_freq(self):
    return pd.DataFrame({'corpus': self.term_ranker.get_ranks(label_append=' freq')[[str(c) + ' freq' for c in self.relevant_categories]].sum(axis=1)})

def use_categories(self, categories):
    self.priors += self.term_ranker.get_ranks()[[str(c) + ' freq' for c in categories]].sum(axis=1)
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
def _get_frequent_terms(num_term_to_keep, term_doc_freq):
    return term_doc_freq.sort_values(by='count', ascending=False).iloc[:int(0.125 * num_term_to_keep)].index

class CorpusFromParsedDocuments(object):

    def __init__(self, df, category_col, parsed_col, feats_from_spacy_doc=FeatsFromSpacyDoc()):
        """
        Parameters
        ----------
        df : pd.DataFrame
         contains category_col, and parse_col, were parsed col is entirely spacy docs
        category_col : str
            name of category column in convention_df
        parsed_col : str
            name of spacy parsed column in convention_df
        feats_from_spacy_doc : FeatsFromSpacyDoc
        """
        self._df = df.reset_index()
        self._category_col = category_col
        self._parsed_col = parsed_col
        self._category_idx_store = IndexStore()
        self._X_factory = CSRMatrixFactory()
        self._mX_factory = CSRMatrixFactory()
        self._term_idx_store = IndexStore()
        self._metadata_idx_store = IndexStore()
        self._feats_from_spacy_doc = feats_from_spacy_doc

    def build(self, show_progress=False) -> ParsedCorpus:
        """Constructs the term doc matrix.

        Returns
        -------
        scattertext.ParsedCorpus.ParsedCorpus
        """
        y = self._get_y_and_populate_category_idx_store(self._df[self._category_col].apply(str))
        if show_progress is True:
            self._df.progress_apply(self._add_to_x_factory, axis=1)
        else:
            self._df.apply(self._add_to_x_factory, axis=1)
        self._mX = self._mX_factory.set_last_row_idx(len(y) - 1).get_csr_matrix()
        return ParsedCorpus(df=self._df, X=self._X_factory.set_last_row_idx(len(y) - 1).get_csr_matrix(), mX=self._mX_factory.set_last_row_idx(len(y) - 1).get_csr_matrix(), y=y, term_idx_store=self._term_idx_store, category_idx_store=self._category_idx_store, metadata_idx_store=self._metadata_idx_store, parsed_col=self._parsed_col, category_col=self._category_col)

    def _get_y_and_populate_category_idx_store(self, categories):
        return np.array(categories.apply(self._category_idx_store.getidx))

    def _add_to_x_factory(self, row):
        parsed_text = row[self._parsed_col]
        for term, count in self._feats_from_spacy_doc.get_feats(parsed_text).items():
            term_idx = self._term_idx_store.getidx(term)
            self._X_factory[row.name, term_idx] = count
        for meta, val in self._feats_from_spacy_doc.get_doc_metadata(parsed_text).items():
            meta_idx = self._metadata_idx_store.getidx(meta)
            self._mX_factory[row.name, meta_idx] = val

def _add_to_x_factory(self, row):
    parsed_text = row[self._parsed_col]
    for term, count in self._feats_from_spacy_doc.get_feats(parsed_text).items():
        term_idx = self._term_idx_store.getidx(term)
        self._X_factory[row.name, term_idx] = count
    for meta, val in self._feats_from_spacy_doc.get_doc_metadata(parsed_text).items():
        meta_idx = self._metadata_idx_store.getidx(meta)
        self._mX_factory[row.name, meta_idx] = val

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

class CharacteristicGrouper:

    def __init__(self, corpus: TermDocMatrix, non_text: bool=False, window_size: int=1, to_text: str=' to<br/>', rank_embedder: Optional[CategoryEmbedderABC]=None, distance_measure: Callable[[np.array, np.array], float]=None):
        self.corpus = corpus
        self.window_size = window_size
        self.rank_embedder = RankEmbedder() if rank_embedder is None else rank_embedder
        self.distance_measure = spearman_distance if distance_measure is None else distance_measure
        self.non_text = non_text
        self.to_text = to_text

    def group_corpus_categories(self, category_order: Optional[List[str]]=None, number_of_splits: int=10) -> TermDocMatrix:
        new_categories, new_categories_order = self.get_new_doc_categories(category_order, number_of_splits)
        return self.corpus.recategorize(new_categories)

    def get_new_doc_categories(self, category_order: Optional[List[str]]=None, number_of_splits: int=10, verbose=False) -> Tuple[List, List]:
        category_to_bin_dict = self.get_category_group_dict(category_order, number_of_splits, verbose)
        new_categories = [category_to_bin_dict[cat] for cat in self.corpus.get_category_names_by_row()]
        seen = set()
        new_categories_order = [category_to_bin_dict[x] for x in category_order if not (category_to_bin_dict[x] in seen or seen.add(category_to_bin_dict[x]))]
        return (new_categories, new_categories_order)

    def get_category_group_dict(self, category_order: List[str]=None, number_of_splits: int=10, verbose=False) -> Dict[str, str]:
        category_order = sorted(self._get_categories()) if category_order is None else category_order
        assert len(category_order) == self.corpus.get_num_categories()
        embedding_mat = self.rank_embedder.embed_categories(corpus=self.corpus, non_text=self.non_text)
        cat_boundaries = self.get_change_point_candidates(embeddings=embedding_mat, ordered_category_names=category_order).iloc[:number_of_splits].sort_values(by='Order')
        intervals = []
        interval_names = []
        last = 0
        for _, row in cat_boundaries.iterrows():
            intervals.append((last, int(row.Order)))
            interval_names.append(str(category_order[last + 1 if last > 0 else 0]) + self.to_text + str(category_order[int(row.Order)]))
            last = int(row.Order)
        intervals.append((last, len(category_order)))
        interval_names.append(str(category_order[last + 1]) + self.to_text + str(category_order[-1]))
        interval_index = pd.IntervalIndex.from_tuples(intervals)
        category_to_bin_dict = {category: interval_names[interval_index.get_loc(i) if i > 0 else 0] for i, category in enumerate(category_order)}
        return category_to_bin_dict

    def _get_string_categories(self) -> List[str]:
        return [str(c) for c in self.corpus.get_categories()]

    def _get_categories(self) -> List[str]:
        return self.corpus.get_categories()

    def get_change_point_candidates(self, embeddings: np.array, ordered_category_names: List[str]) -> pd.DataFrame:
        category_index_df = pd.DataFrame({'Category': self._get_string_categories()}).reset_index().set_index('Category').loc[[str(x) for x in ordered_category_names]].assign(Order=lambda df: np.arange(len(df)))
        mat = embeddings[:, category_index_df['index'].values]
        dists = []
        for i in range(mat.shape[1] - self.window_size):
            a = mat[:, list(range(max(0, i - self.window_size + 1), i + 1))].mean(axis=1)
            b = mat[:, list(range(i + 1, max(i + 1 + self.window_size, mat.shape[1])))].mean(axis=1)
            distance = self.distance_measure(a, b)
            dists.append(distance)
        category_index_df = category_index_df.assign(Dist=dists + [0] * self.window_size).sort_values(by='Dist', ascending=True)
        return category_index_df

def get_new_doc_categories(self, category_order: Optional[List[str]]=None, number_of_splits: int=10, verbose=False) -> Tuple[List, List]:
    category_to_bin_dict = self.get_category_group_dict(category_order, number_of_splits, verbose)
    new_categories = [category_to_bin_dict[cat] for cat in self.corpus.get_category_names_by_row()]
    seen = set()
    new_categories_order = [category_to_bin_dict[x] for x in category_order if not (category_to_bin_dict[x] in seen or seen.add(category_to_bin_dict[x]))]
    return (new_categories, new_categories_order)

def get_category_group_dict(self, category_order: List[str]=None, number_of_splits: int=10, verbose=False) -> Dict[str, str]:
    category_order = sorted(self._get_categories()) if category_order is None else category_order
    assert len(category_order) == self.corpus.get_num_categories()
    embedding_mat = self.rank_embedder.embed_categories(corpus=self.corpus, non_text=self.non_text)
    cat_boundaries = self.get_change_point_candidates(embeddings=embedding_mat, ordered_category_names=category_order).iloc[:number_of_splits].sort_values(by='Order')
    intervals = []
    interval_names = []
    last = 0
    for _, row in cat_boundaries.iterrows():
        intervals.append((last, int(row.Order)))
        interval_names.append(str(category_order[last + 1 if last > 0 else 0]) + self.to_text + str(category_order[int(row.Order)]))
        last = int(row.Order)
    intervals.append((last, len(category_order)))
    interval_names.append(str(category_order[last + 1]) + self.to_text + str(category_order[-1]))
    interval_index = pd.IntervalIndex.from_tuples(intervals)
    category_to_bin_dict = {category: interval_names[interval_index.get_loc(i) if i > 0 else 0] for i, category in enumerate(category_order)}
    return category_to_bin_dict

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

class TestUseFullDocAsMetadata(TestCase):

    def test_get_feats(self):
        doc = whitespace_nlp_with_sentences('A a bb cc.')
        term_freq = UseFullDocAsMetadata().get_doc_metadata(doc)
        self.assertEqual(Counter({'A a bb cc.': 1}), term_freq)

def test_get_feats(self):
    doc = whitespace_nlp_with_sentences('A a bb cc.')
    term_freq = UseFullDocAsMetadata().get_doc_metadata(doc)
    self.assertEqual(Counter({'A a bb cc.': 1}), term_freq)

class TestAsianNLP(TestCase):

    def setUp(self):
        self.chinese_text = u'总理主持召开的这场座谈会，旨在听取专家学者和企业界人士对《政府工作报告（征求意见稿）》的意见建议。胡玮炜和另外6名不同专业、领域的专家、企业家受邀参加。\n李克强对胡玮炜的细致提问始终围绕虚拟经济和实体经济，以及新旧动能转换。他关心自行车制造材料，也询问所采用的互联网技术。 “摩拜单车听起来是经营方式的革命，但基础还是自行车，还是要靠实体经济支撑。反过来，实体经济也要靠服务变革来带动。”总理指出。\n当听到这家共享智能单车企业在不到一年的时间发展为拥有80万辆自行车的规模后，李克强充分肯定此类互联网企业对实体经济的带动作用，“某个自行车企业可能就被你带活了，新兴服务业的发展给制造业创造了巨大的市场空间”。\n相关资料显示，受益于共享单车，国内传统的自行车产业正在迎来春天，至少带动了160万辆以上自行车的制造生产。甚至有生产自行车零部件的上市公司因此股票涨停。美国彭博新闻社网站注意到这一现象，评价说“中国正重新成为自行车大国”。'
        self.japanese_text = u'（淸實《きよざね》）私共《わたくしども》は、唯《たゞ》君《きみ》の仰《おほ》せのままに、此處《こゝ》までお供《とも》致《いた》して參《まゐ》つたのでござります。丁度《ちやうど》今日《けふ》の午頃《ひるごろ》のこと、わが君《きみ》には急《きふ》に靑褪《あをざ》めた顏《かほ》をなすつて、「都《みやこ》に居《ゐ》ては命《いのち》が危《あやう》い故《ゆゑ》、一刻《いつこく》も早《はや》くわしを何處《どこ》かの山奧《やまおく》へ伴《つ》れて行《い》つて、隱《かく》してくれい。」と仰《おつ》しやりました。それで私共《わたくしども》は取《と》る物《もの》も取《と》り敢《あ》へず、深《ふか》い仔細《しさい》も承《うけたまは》らずに、君《きみ》をお伴《つ》れ申《まを》して、一《ひ》と先《ま》づ田原《たはら》の奧《おく》の大道寺《だいだうじ》の所領《しよりやう》まで逃《に》げのびたのでござりました。すると君《きみ》には、「いや、まだ此處《こゝ》では安心《あんしん》が出來《でき》ない。もつと人里《ひとざと》を離《はな》れた、もつと寂《さび》しい處《ところ》へ行《ゆ》かねばならぬ。」と仰《おつ》しやつて、たうとうこんな山奧《やまおく》へ參《まゐ》つたのでござります。'

    def test_chinese(self):
        try:
            doc = chinese_nlp(self.chinese_text)
        except:
            return
        sent1 = doc.sents[0]
        self.assertEqual(str(sent1), u'总理 主持 召开 的 这场 座谈会 ， 旨在 听取 专家学者 和 企业界 人士 对 《 政府 工作 报告 （ 征求意见 稿 ） 》 的 意见建议 。')
        self.assertEqual(len(doc.sents), 11)

    def test_japanese(self):
        try:
            __import__('tinysegmenter')
        except ImportError:
            return
        doc = japanese_nlp(self.japanese_text)
        sent1 = doc.sents[0]
        self.assertGreater(len(str(sent1)), 10)
        self.assertEqual(len(doc.sents), 7)

def test_chinese(self):
    try:
        doc = chinese_nlp(self.chinese_text)
    except:
        return
    sent1 = doc.sents[0]
    self.assertEqual(str(sent1), u'总理 主持 召开 的 这场 座谈会 ， 旨在 听取 专家学者 和 企业界 人士 对 《 政府 工作 报告 （ 征求意见 稿 ） 》 的 意见建议 。')
    self.assertEqual(len(doc.sents), 11)

class TestUseFullDocAsFeature(TestCase):

    def test_get_feats(self):
        doc = whitespace_nlp_with_sentences('A a bb cc.')
        term_freq = UseFullDocAsFeature().get_feats(doc)
        self.assertEqual(Counter({'A a bb cc.': 1}), term_freq)

def test_get_feats(self):
    doc = whitespace_nlp_with_sentences('A a bb cc.')
    term_freq = UseFullDocAsFeature().get_feats(doc)
    self.assertEqual(Counter({'A a bb cc.': 1}), term_freq)

class TestUnigramsFromSpacyDoc(TestCase):

    def test_get_feats(self):
        doc = whitespace_nlp('A a bb cc.')
        term_freq = UnigramsFromSpacyDoc().get_feats(doc)
        self.assertEqual(Counter({'a': 2, 'bb': 1, 'cc': 1}), term_freq)

def test_get_feats(self):
    doc = whitespace_nlp('A a bb cc.')
    term_freq = UnigramsFromSpacyDoc().get_feats(doc)
    self.assertEqual(Counter({'a': 2, 'bb': 1, 'cc': 1}), term_freq)

class TestFeatsFromSpacyDoc(TestCase):

    def test_main(self):
        doc = whitespace_nlp('A a bb cc.')
        term_freq = FeatsFromSpacyDoc().get_feats(doc)
        self.assertEqual(Counter({'a': 2, 'bb': 1, 'a bb': 1, 'cc': 1, 'a a': 1, 'bb cc': 1}), term_freq)

    def test_singleton_with_sentences(self):
        doc = whitespace_nlp_with_sentences('Blah')
        term_freq = FeatsFromSpacyDoc().get_feats(doc)
        self.assertEqual(Counter({'blah': 1}), term_freq)

    def test_lemmas(self):
        doc = whitespace_nlp('A a bb ddddd.')
        term_freq = FeatsFromSpacyDoc(use_lemmas=True).get_feats(doc)
        self.assertEqual(Counter({'a': 2, 'bb': 1, 'a bb': 1, 'dd': 1, 'a a': 1, 'bb dd': 1}), term_freq)

    def test_feats_from_spacy_doc_only_chunks(self):
        doc = whitespace_nlp_with_fake_chunks('This is a fake noun chunk generating sentence.')
        term_freq = FeatsFromSpacyDocOnlyNounChunks().get_feats(doc)
        self.assertEqual(term_freq, Counter({'this is': 1, 'is a': 1}))

    def test_empty(self):
        doc = whitespace_nlp('')
        term_freq = FeatsFromSpacyDoc().get_feats(doc)
        self.assertEqual(Counter(), term_freq)

    def test_entity_types_to_censor_not_a_set(self):
        doc = whitespace_nlp('A a bb cc.', {'bb': 'A'})
        with self.assertRaises(AssertionError):
            FeatsFromSpacyDoc(entity_types_to_censor='A').get_feats(doc)

    def test_entity_censor(self):
        doc = whitespace_nlp('A a bb cc.', {'bb': 'BAD'})
        term_freq = FeatsFromSpacyDoc(entity_types_to_censor=set(['BAD'])).get_feats(doc)
        self.assertEqual(Counter({'a': 2, 'a _BAD': 1, '_BAD cc': 1, 'cc': 1, 'a a': 1, '_BAD': 1}), term_freq)

    def test_entity_tags(self):
        doc = whitespace_nlp('A a bb cc Bob.', {'bb': 'BAD'}, {'Bob': 'NNP'})
        term_freq = FeatsFromSpacyDoc(entity_types_to_censor=set(['BAD'])).get_feats(doc)
        self.assertEqual(Counter({'a': 2, 'a _BAD': 1, '_BAD cc': 1, 'cc': 1, 'a a': 1, '_BAD': 1, 'bob': 1, 'cc bob': 1}), term_freq)
        term_freq = FeatsFromSpacyDoc(entity_types_to_censor=set(['BAD']), tag_types_to_censor=set(['NNP'])).get_feats(doc)
        self.assertEqual(Counter({'a': 2, 'a _BAD': 1, '_BAD cc': 1, 'cc': 1, 'a a': 1, '_BAD': 1, 'NNP': 1, 'cc NNP': 1}), term_freq)

    def test_strip_final_period(self):
        doc = bad_whitespace_nlp("I CAN'T ANSWER THAT\n QUESTION.\n I HAVE NOT ASKED THEM\n SPECIFICALLY IF THEY HAVE\n ENOUGH.")
        feats = FeatsFromSpacyDoc().get_feats(doc)
        self.assertEqual(feats, Counter({'i': 2, 'have': 2, 'that question.': 1, 'answer': 1, 'question.': 1, 'enough.': 1, 'i have': 1, 'them specifically': 1, 'have enough.': 1, 'not asked': 1, 'they have': 1, 'have not': 1, 'specifically': 1, 'answer that': 1, 'question. i': 1, "can't": 1, 'if': 1, 'they': 1, "can't answer": 1, 'asked': 1, 'them': 1, 'if they': 1, 'asked them': 1, 'that': 1, 'not': 1, "i can't": 1, 'specifically if': 1}))
        feats = FeatsFromSpacyDoc(strip_final_period=True).get_feats(doc)
        self.assertEqual(feats, Counter({'i': 2, 'have': 2, 'that question': 1, 'answer': 1, 'question': 1, 'enough': 1, 'i have': 1, 'them specifically': 1, 'have enough': 1, 'not asked': 1, 'they have': 1, 'have not': 1, 'specifically': 1, 'answer that': 1, 'question i': 1, "can't": 1, 'if': 1, 'they': 1, "can't answer": 1, 'asked': 1, 'them': 1, 'if they': 1, 'asked them': 1, 'that': 1, 'not': 1, "i can't": 1, 'specifically if': 1}))

def test_main(self):
    doc = whitespace_nlp('A a bb cc.')
    term_freq = FeatsFromSpacyDoc().get_feats(doc)
    self.assertEqual(Counter({'a': 2, 'bb': 1, 'a bb': 1, 'cc': 1, 'a a': 1, 'bb cc': 1}), term_freq)

def test_singleton_with_sentences(self):
    doc = whitespace_nlp_with_sentences('Blah')
    term_freq = FeatsFromSpacyDoc().get_feats(doc)
    self.assertEqual(Counter({'blah': 1}), term_freq)

def test_lemmas(self):
    doc = whitespace_nlp('A a bb ddddd.')
    term_freq = FeatsFromSpacyDoc(use_lemmas=True).get_feats(doc)
    self.assertEqual(Counter({'a': 2, 'bb': 1, 'a bb': 1, 'dd': 1, 'a a': 1, 'bb dd': 1}), term_freq)

def test_feats_from_spacy_doc_only_chunks(self):
    doc = whitespace_nlp_with_fake_chunks('This is a fake noun chunk generating sentence.')
    term_freq = FeatsFromSpacyDocOnlyNounChunks().get_feats(doc)
    self.assertEqual(term_freq, Counter({'this is': 1, 'is a': 1}))

def test_empty(self):
    doc = whitespace_nlp('')
    term_freq = FeatsFromSpacyDoc().get_feats(doc)
    self.assertEqual(Counter(), term_freq)

def test_entity_types_to_censor_not_a_set(self):
    doc = whitespace_nlp('A a bb cc.', {'bb': 'A'})
    with self.assertRaises(AssertionError):
        FeatsFromSpacyDoc(entity_types_to_censor='A').get_feats(doc)

def test_entity_censor(self):
    doc = whitespace_nlp('A a bb cc.', {'bb': 'BAD'})
    term_freq = FeatsFromSpacyDoc(entity_types_to_censor=set(['BAD'])).get_feats(doc)
    self.assertEqual(Counter({'a': 2, 'a _BAD': 1, '_BAD cc': 1, 'cc': 1, 'a a': 1, '_BAD': 1}), term_freq)

def test_entity_tags(self):
    doc = whitespace_nlp('A a bb cc Bob.', {'bb': 'BAD'}, {'Bob': 'NNP'})
    term_freq = FeatsFromSpacyDoc(entity_types_to_censor=set(['BAD'])).get_feats(doc)
    self.assertEqual(Counter({'a': 2, 'a _BAD': 1, '_BAD cc': 1, 'cc': 1, 'a a': 1, '_BAD': 1, 'bob': 1, 'cc bob': 1}), term_freq)
    term_freq = FeatsFromSpacyDoc(entity_types_to_censor=set(['BAD']), tag_types_to_censor=set(['NNP'])).get_feats(doc)
    self.assertEqual(Counter({'a': 2, 'a _BAD': 1, '_BAD cc': 1, 'cc': 1, 'a a': 1, '_BAD': 1, 'NNP': 1, 'cc NNP': 1}), term_freq)

def test_strip_final_period(self):
    doc = bad_whitespace_nlp("I CAN'T ANSWER THAT\n QUESTION.\n I HAVE NOT ASKED THEM\n SPECIFICALLY IF THEY HAVE\n ENOUGH.")
    feats = FeatsFromSpacyDoc().get_feats(doc)
    self.assertEqual(feats, Counter({'i': 2, 'have': 2, 'that question.': 1, 'answer': 1, 'question.': 1, 'enough.': 1, 'i have': 1, 'them specifically': 1, 'have enough.': 1, 'not asked': 1, 'they have': 1, 'have not': 1, 'specifically': 1, 'answer that': 1, 'question. i': 1, "can't": 1, 'if': 1, 'they': 1, "can't answer": 1, 'asked': 1, 'them': 1, 'if they': 1, 'asked them': 1, 'that': 1, 'not': 1, "i can't": 1, 'specifically if': 1}))
    feats = FeatsFromSpacyDoc(strip_final_period=True).get_feats(doc)
    self.assertEqual(feats, Counter({'i': 2, 'have': 2, 'that question': 1, 'answer': 1, 'question': 1, 'enough': 1, 'i have': 1, 'them specifically': 1, 'have enough': 1, 'not asked': 1, 'they have': 1, 'have not': 1, 'specifically': 1, 'answer that': 1, 'question i': 1, "can't": 1, 'if': 1, 'they': 1, "can't answer": 1, 'asked': 1, 'them': 1, 'if they': 1, 'asked them': 1, 'that': 1, 'not': 1, "i can't": 1, 'specifically if': 1}))

class TestWhitespaceNLP(TestCase):

    def test_whitespace_nlp(self):
        raw = 'Hi! My name\n\t\tis Jason.  You can call me\n\t\tMr. J.  Is that your name too?\n\t\tHa. Ha ha.\n\t\t'
        doc = whitespace_nlp(raw)
        self.assertEqual(len(list(doc)), 55)
        self.assertEqual(len(doc.sents), 1)
        tok = Tok('WORD', 'Jason', 'jason', 'Name', 'NNP')
        self.assertEqual(len(tok), 5)
        self.assertEqual(str(tok), 'jason')
        self.assertEqual(str(Doc([[Tok('WORD', 'Jason', 'jason', 'Name', 'NNP'), Tok('WORD', 'a', 'a', 'Name', 'NNP')]], raw='asdfbasdfasd')), 'asdfbasdfasd')
        self.assertEqual(str(Doc([[Tok('WORD', 'Blah', 'blah', 'Name', 'NNP'), Tok('Space', ' ', ' ', ' ', ' '), Tok('WORD', 'a', 'a', 'Name', 'NNP')]])), 'blah a')

    def test_whitespace_nlp_with_sentences(self):
        raw = 'Hi! My name\n\t\tis Jason.  You can call me\n\t\tMr. J.  Is that your name too?\n\t\tHa. Ha ha.\n\t\t'
        doc = whitespace_nlp_with_sentences(raw)
        self.assertEqual(doc.text, raw)
        self.assertEqual(len(doc.sents), 7)
        self.assertEqual(doc[3].orth_, 'name')
        self.assertEqual(doc[25].orth_, '.')
        self.assertEqual(len(doc), 26)
        self.assertEqual(doc[3].idx, 7)
        self.assertEqual(raw[doc[3].idx:doc[3].idx + len(doc[3].orth_)], 'name')

    def test_whitespace_nlp_with_sentences_singleton(self):
        raw = 'Blah'
        self.assertEqual(whitespace_nlp_with_sentences(raw).text, raw)
        self.assertEqual(len(whitespace_nlp_with_sentences(raw).sents), 1)
        self.assertEqual(len(whitespace_nlp_with_sentences(raw).sents[0]), 1)
        raw = 'Blah.'
        self.assertEqual(whitespace_nlp_with_sentences(raw).text, raw)
        self.assertEqual(len(whitespace_nlp_with_sentences(raw).sents), 1)
        self.assertEqual(len(whitespace_nlp_with_sentences(raw).sents[0]), 2)

def test_whitespace_nlp_with_sentences(self):
    raw = 'Hi! My name\n\t\tis Jason.  You can call me\n\t\tMr. J.  Is that your name too?\n\t\tHa. Ha ha.\n\t\t'
    doc = whitespace_nlp_with_sentences(raw)
    self.assertEqual(doc.text, raw)
    self.assertEqual(len(doc.sents), 7)
    self.assertEqual(doc[3].orth_, 'name')
    self.assertEqual(doc[25].orth_, '.')
    self.assertEqual(len(doc), 26)
    self.assertEqual(doc[3].idx, 7)
    self.assertEqual(raw[doc[3].idx:doc[3].idx + len(doc[3].orth_)], 'name')

def test_whitespace_nlp_with_sentences_singleton(self):
    raw = 'Blah'
    self.assertEqual(whitespace_nlp_with_sentences(raw).text, raw)
    self.assertEqual(len(whitespace_nlp_with_sentences(raw).sents), 1)
    self.assertEqual(len(whitespace_nlp_with_sentences(raw).sents[0]), 1)
    raw = 'Blah.'
    self.assertEqual(whitespace_nlp_with_sentences(raw).text, raw)
    self.assertEqual(len(whitespace_nlp_with_sentences(raw).sents), 1)
    self.assertEqual(len(whitespace_nlp_with_sentences(raw).sents[0]), 2)

class TestFeatsFsromSpacyDocAndEmpath(TestCase):

    def test_main(self):
        feat_getter = FeatsFromSpacyDocAndEmpath(empath_analyze_function=mock_empath_analyze)
        sys.modules['empath'] = Mock(analyze=mock_empath_analyze)
        FeatsFromSpacyDocAndEmpath()
        doc = whitespace_nlp('Hello this is a document.')
        term_freq = feat_getter.get_feats(doc)
        self.assertEqual(set(term_freq.items()), set({'document': 1, 'hello': 1, 'is': 1, 'this': 1, 'a document': 1, 'hello this': 1, 'is a': 1, 'a': 1, 'this is': 1}.items()))
        metadata_freq = feat_getter.get_doc_metadata(doc)
        self.assertEqual(metadata_freq['ridicule'], 1)
        self.assertNotIn('empath_fashion', metadata_freq)

    def test_empath_not_presesnt(self):
        sys.modules['empath'] = None
        if sys.version_info.major == 3:
            with self.assertRaisesRegex(Exception, 'Please install the empath library to use FeatsFromSpacyDocAndEmpath.'):
                FeatsFromSpacyDocAndEmpath()
        else:
            with self.assertRaises(Exception):
                FeatsFromSpacyDocAndEmpath()

def test_main(self):
    feat_getter = FeatsFromSpacyDocAndEmpath(empath_analyze_function=mock_empath_analyze)
    sys.modules['empath'] = Mock(analyze=mock_empath_analyze)
    FeatsFromSpacyDocAndEmpath()
    doc = whitespace_nlp('Hello this is a document.')
    term_freq = feat_getter.get_feats(doc)
    self.assertEqual(set(term_freq.items()), set({'document': 1, 'hello': 1, 'is': 1, 'this': 1, 'a document': 1, 'hello this': 1, 'is a': 1, 'a': 1, 'this is': 1}.items()))
    metadata_freq = feat_getter.get_doc_metadata(doc)
    self.assertEqual(metadata_freq['ridicule'], 1)
    self.assertNotIn('empath_fashion', metadata_freq)

class TestFeatsFromOnlyEmpath(TestCase):

    def test_main(self):
        sys.modules['empath'] = Mock(analyze=mock_empath_analyze)
        FeatsFromOnlyEmpath()
        feat_getter = FeatsFromOnlyEmpath(empath_analyze_function=mock_empath_analyze)
        doc = whitespace_nlp('Hello this is a document.')
        term_freq = feat_getter.get_feats(doc)
        metadata_freq = feat_getter.get_doc_metadata(doc)
        self.assertEqual(term_freq, Counter())
        self.assertEqual(metadata_freq['ridicule'], 1)
        self.assertNotIn('fashion', metadata_freq)
        self.assertNotIn('document', metadata_freq)
        self.assertNotIn('a document', metadata_freq)

    def test_empath_not_presesnt(self):
        sys.modules['empath'] = None
        if sys.version_info.major == 3:
            with self.assertRaisesRegex(Exception, 'Please install the empath library to use FeatsFromSpacyDocAndEmpath.'):
                FeatsFromSpacyDocAndEmpath()
        else:
            with self.assertRaises(Exception):
                FeatsFromSpacyDocAndEmpath()

def test_main(self):
    sys.modules['empath'] = Mock(analyze=mock_empath_analyze)
    FeatsFromOnlyEmpath()
    feat_getter = FeatsFromOnlyEmpath(empath_analyze_function=mock_empath_analyze)
    doc = whitespace_nlp('Hello this is a document.')
    term_freq = feat_getter.get_feats(doc)
    metadata_freq = feat_getter.get_doc_metadata(doc)
    self.assertEqual(term_freq, Counter())
    self.assertEqual(metadata_freq['ridicule'], 1)
    self.assertNotIn('fashion', metadata_freq)
    self.assertNotIn('document', metadata_freq)
    self.assertNotIn('a document', metadata_freq)

class TestFeatsFromTopicModel(TestCase):

    def test_get_doc_get_feats(self):
        expected = Counter({'a b': 2, 'c e f': 1, 'b': 1})
        actual = FeatsFromTopicModel(topic_model={'Topic A': ['A b', 'b', 'C e F'], 'Topic B': ['B', 'C e F']}).get_feats('A b A b C e F B')
        self.assertEqual(expected, actual)

    def test_get_doc_metadata(self):
        expected = Counter({'Topic A': 3, 'Topic B': 2})
        actual = FeatsFromTopicModel(topic_model={'Topic A': ['A b', 'b', 'C e F'], 'Topic B': ['B', 'C e F']}, keyword_processor_args={'case_sensitive': True}).get_doc_metadata('A b A b C e F B')
        self.assertEqual(expected, actual)

def test_get_doc_get_feats(self):
    expected = Counter({'a b': 2, 'c e f': 1, 'b': 1})
    actual = FeatsFromTopicModel(topic_model={'Topic A': ['A b', 'b', 'C e F'], 'Topic B': ['B', 'C e F']}).get_feats('A b A b C e F B')
    self.assertEqual(expected, actual)

def test_get_doc_metadata(self):
    expected = Counter({'Topic A': 3, 'Topic B': 2})
    actual = FeatsFromTopicModel(topic_model={'Topic A': ['A b', 'b', 'C e F'], 'Topic B': ['B', 'C e F']}, keyword_processor_args={'case_sensitive': True}).get_doc_metadata('A b A b C e F B')
    self.assertEqual(expected, actual)

def __get_term_stats(ias, weibull_fit_func):
    fit = weibull_fit_func(ias)
    return {k: v for k, v in vars(fit).items() if k in ['alpha', 'alpha_upper', 'alpha_lower', 'beta', 'beta_upper', 'beta_lower', 'alpha_SE', 'beta_SE']}

class WeibullInterArrivalStats:

    def __init__(self, inter_arrival_counts: InterArrivalCounts, verbose: bool=False, weibull_fit_func: Optional[Callable[[List[int]], object]]=None):
        self.__register_weibull_fit_funct(weibull_fit_func)
        self.inter_arrival_counts = inter_arrival_counts
        data, data_cat = self.__collect_term_and_cat_data(inter_arrival_counts, verbose)
        self.term_df = pd.DataFrame(data).set_index('term')
        self.term_cat_df = pd.DataFrame(data_cat).set_index('term')

    def __register_weibull_fit_funct(self, weibull_fit_func):
        if weibull_fit_func is None:
            from reliability.Fitters import Fit_Weibull_2P
            self.weibull_fit_func = lambda failures: Fit_Weibull_2P(failures=failures, show_probability_plot=False, print_results=False)
        else:
            self.weibull_fit_func = weibull_fit_func

    def get_inter_arrival_times(self) -> pd.DataFrame:
        return self.term_df

    def get_category_specific_inter_arrival_times(self) -> pd.DataFrame:
        return self.term_cat_df

    def __collect_term_and_cat_data(self, inter_arrival_counts: InterArrivalCounts, verbose: bool) -> Tuple[List, List]:
        data = []
        data_cat = []
        it = self.__get_term_iterator(verbose)
        for term in it:
            if len(set(inter_arrival_counts.term_inter_arrivals[term])) > 1:
                fit = self.weibull_fit_func(inter_arrival_counts.term_inter_arrivals[term])
                data.append({'term': term, **self.__metrics_of_interest_from_fit(fit)})
                for cat, values in inter_arrival_counts.term_category_inter_arrivals[term].items():
                    if len(set(values)) > 1:
                        fit = self.weibull_fit_func(values)
                        data_cat.append({'term': term, 'Cat': cat, **self.__metrics_of_interest_from_fit(fit)})
        return (data, data_cat)

    def __metrics_of_interest_from_fit(self, fit):
        return {k: v for k, v in vars(fit).items() if k in ['alpha', 'alpha_upper', 'alpha_lower', 'beta', 'beta_upper', 'beta_lower', 'alpha_SE', 'beta_SE']}

    def __get_term_iterator(self, verbose):
        it = self.inter_arrival_counts.corpus.get_terms(use_metadata=True)
        if verbose:
            it = tqdm(it)
        return it

def __collect_term_and_cat_data(self, inter_arrival_counts: InterArrivalCounts, verbose: bool) -> Tuple[List, List]:
    data = []
    data_cat = []
    it = self.__get_term_iterator(verbose)
    for term in it:
        if len(set(inter_arrival_counts.term_inter_arrivals[term])) > 1:
            fit = self.weibull_fit_func(inter_arrival_counts.term_inter_arrivals[term])
            data.append({'term': term, **self.__metrics_of_interest_from_fit(fit)})
            for cat, values in inter_arrival_counts.term_category_inter_arrivals[term].items():
                if len(set(values)) > 1:
                    fit = self.weibull_fit_func(values)
                    data_cat.append({'term': term, 'Cat': cat, **self.__metrics_of_interest_from_fit(fit)})
    return (data, data_cat)

def __metrics_of_interest_from_fit(self, fit):
    return {k: v for k, v in vars(fit).items() if k in ['alpha', 'alpha_upper', 'alpha_lower', 'beta', 'beta_upper', 'beta_lower', 'alpha_SE', 'beta_SE']}

class FeatsFromGensim(object):

    def __init__(self, phrases, gram_size):
        """
        Parameters
        ----------
        phrases : list[gensim.models.Phrases]
        gram_size : int, maximum number of words per phrase
        kwargs : parameters for FeatsFromSpacyDoc.init
        """
        from gensim.models import Phrases
        phrases = phrases
        gram_size = gram_size
        assert type(phrases) == Phrases
        self.gram_size = gram_size
        self.phrases = phrases

    def get_doc_metadata(self, doc):
        return Counter()

    def get_feats(self, doc):
        """
        Parameters
        ----------
        doc, Spacy Docs

        Returns
        -------
        Counter (unigram, bigram) -> count
        """
        ngram_counter = Counter()
        for sent in doc.sents:
            ngrams = self.phrases[str(sent)]
            for subphrases in self.phrases[1:]:
                ngrams = subphrases[str(sent)]
            for ngram in ngrams:
                ngram_counter[ngram] += 1
        return ngram_counter

def get_doc_metadata(self, doc):
    return Counter()

def get_feats(self, doc):
    """
        Parameters
        ----------
        doc, Spacy Docs

        Returns
        -------
        Counter (unigram, bigram) -> count
        """
    ngram_counter = Counter()
    for sent in doc.sents:
        ngrams = self.phrases[str(sent)]
        for subphrases in self.phrases[1:]:
            ngrams = subphrases[str(sent)]
        for ngram in ngrams:
            ngram_counter[ngram] += 1
    return ngram_counter

class AllCategoryScorerGMeanL2(AllCategoryScorer):

    def _free_init(self, **kwargs):
        if 'coef_weight' in kwargs:
            assert int(kwargs['coef_weight']) == kwargs['coef_weight']
            assert kwargs['coef_weight'] > 1
            self.coef_weight_ = kwargs['coef_weight']
        else:
            self.coef_weight_ = COEF_WEIGHT_DEFAULT
        if 'freq_weight' in kwargs:
            assert int(kwargs['freq_weight']) == kwargs['freq_weight']
            assert kwargs['freq_weight'] > 1
            self.freq_weight_ = kwargs['freq_weight']
        else:
            self.freq_weight_ = FREQ_WEIGHT_DEFAULT

    def get_rank_freq_df(self) -> pd.DataFrame:
        coef_freq_df = self.__coefs_to_coef_freq_df(coef_df=self.__get_coef_df())
        coef_freq_df = self.__add_gmeans_to_coef_freq_df(coef_freq_df)
        data = []
        for cat in self.corpus_.get_categories():
            cat = str(cat)
            for term_rank, (term, row) in enumerate(coef_freq_df[[cat + ' gmean', cat + ' freq']].sort_values(by=cat + ' gmean', ascending=False).iterrows()):
                data.append({'Category': cat, 'Term': term, 'Rank': term_rank, 'Score': row[cat + ' gmean'], 'Frequency': row[cat + ' freq']})
        return pd.DataFrame(data)

    def __add_gmeans_to_coef_freq_df(self, coef_freq_df: pd.DataFrame) -> pd.DataFrame:
        for cat in self.corpus_.get_categories():
            freq = Scalers.dense_rank(coef_freq_df[str(cat) + ' freq'])
            coef = Scalers.scale_neg_1_to_1_with_zero_mean(coef_freq_df[str(cat) + ' coef'])
            coef_freq_df[str(cat) + ' gmean'] = gmean([freq] * self.freq_weight_ + [coef] * self.coef_weight_)
        return coef_freq_df

    def __coefs_to_coef_freq_df(self, coef_df: pd.DataFrame) -> pd.DataFrame:
        coef_freq_df = pd.merge(self.corpus_.get_freq_df(use_metadata=self.non_text_), coef_df, left_index=True, right_index=True)
        return coef_freq_df

    def __get_coef_df(self) -> pd.DataFrame:
        tdm = self.corpus_.get_term_doc_mat(non_text=self.non_text_)
        tdmtfidf = TfidfTransformer().fit_transform(tdm)
        coefs = np.zeros(shape=(self.corpus_.get_num_categories(), tdm.shape[1]), dtype=float)
        for i, cat in enumerate(self.corpus_.get_categories()):
            y = self.corpus_.get_category_ids() == i
            clf = LogisticRegression(penalty='l2', C=5.0, max_iter=4000, tol=1e-06, solver='liblinear').fit(tdmtfidf, y)
            coefs[i, :] = clf.coef_
        return pd.DataFrame(coefs.T, index=self.corpus_.get_terms(use_metadata=self.non_text_), columns=[str(x) + ' coef' for x in self.corpus_.get_categories()])

def _free_init(self, **kwargs):
    if 'coef_weight' in kwargs:
        assert int(kwargs['coef_weight']) == kwargs['coef_weight']
        assert kwargs['coef_weight'] > 1
        self.coef_weight_ = kwargs['coef_weight']
    else:
        self.coef_weight_ = COEF_WEIGHT_DEFAULT
    if 'freq_weight' in kwargs:
        assert int(kwargs['freq_weight']) == kwargs['freq_weight']
        assert kwargs['freq_weight'] > 1
        self.freq_weight_ = kwargs['freq_weight']
    else:
        self.freq_weight_ = FREQ_WEIGHT_DEFAULT

def get_rank_freq_df(self) -> pd.DataFrame:
    coef_freq_df = self.__coefs_to_coef_freq_df(coef_df=self.__get_coef_df())
    coef_freq_df = self.__add_gmeans_to_coef_freq_df(coef_freq_df)
    data = []
    for cat in self.corpus_.get_categories():
        cat = str(cat)
        for term_rank, (term, row) in enumerate(coef_freq_df[[cat + ' gmean', cat + ' freq']].sort_values(by=cat + ' gmean', ascending=False).iterrows()):
            data.append({'Category': cat, 'Term': term, 'Rank': term_rank, 'Score': row[cat + ' gmean'], 'Frequency': row[cat + ' freq']})
    return pd.DataFrame(data)

class IndexStoreFromDict(object):

    @staticmethod
    def build(term_to_index_dict):
        """
		Parameters
		----------
		term_to_index_dict: term -> idx dictionary

		Returns
		-------
		IndexStore
		"""
        idxstore = IndexStore()
        idxstore._val2i = term_to_index_dict
        idxstore._next_i = len(term_to_index_dict)
        idxstore._i2val = [None for _ in range(idxstore._next_i)]
        for term, idx in idxstore._val2i.items():
            idxstore._i2val[idx] = term
        return idxstore

@staticmethod
def build(term_to_index_dict):
    """
		Parameters
		----------
		term_to_index_dict: term -> idx dictionary

		Returns
		-------
		IndexStore
		"""
    idxstore = IndexStore()
    idxstore._val2i = term_to_index_dict
    idxstore._next_i = len(term_to_index_dict)
    idxstore._i2val = [None for _ in range(idxstore._next_i)]
    for term, idx in idxstore._val2i.items():
        idxstore._i2val[idx] = term
    return idxstore

class ComponentDiGraphHTMLRenderer(GraphRenderer):

    def __init__(self, component_graph, width=1000, height=1000, enable_pan_and_zoom=True, engine='dot'):
        self.component_graph = component_graph
        self.width = width
        self.height = height
        self.enable_pan_and_zoom = enable_pan_and_zoom
        self.engine = engine

    def get_graph(self):
        selected_components = self.component_graph.get_components_at_least_size(0)
        all_svg = ''
        for i, component in enumerate(selected_components):
            dot_str = self.component_graph.get_dot(component)
            raw_svg = self.get_svg(dot_str)
            lines = raw_svg.split('\n')
            lines[9] = lines[9].replace('graph0', 'graph%s' % component)
            lines[6] = ('<svg easypz width="{width}pt" height="{height}pt" id="svg{component}"' + ' style="display: none" class="dotgraph"').format(width=self.width, height=self.height, component=component)
            for line in lines[6:]:
                if line.startswith('<!--') or line.endswith('-->'):
                    continue
                all_svg += line + '\n'
        return all_svg

    def get_svg(self, dot_str):
        import graphviz as gv
        return gv.Source(dot_str, format='svg', engine=self.engine).pipe().decode('utf-8')

    def get_javascript(self):
        return '\n        name_to_component = %s;\n        \n        name_to_coord = {}; // term -> {x, y, svg} \n        origViewBox = {}; // svgid -> viewbox\n        \n        Array.prototype.forEach.call(\n            document.querySelectorAll(".dotgraph"),\n            function(svg) {\n                origViewBox[svg.id] = svg.getAttribute(\'viewBox\');\n                \n                Array.prototype.forEach.call(\n                    svg.getElementsByTagName(\'text\'), \n                    function(text) {\n                        name_to_coord[text.textContent] = {\n                            "x": text.getAttribute("x"), \n                            "y": text.getAttribute("y"), \n                            "svg": svg.id\n                        };\n                    }\n                )\n            }\n        ) \n        \n        panZoomInstance = null;\n        \n        \n        function zoomToName(name) {\n        \n            //panZoomInstance.reset();\n                        \n                        \n            console.log("ZOOMING TO "); console.log(name);\n            panZoomInstance.fit();\n            panZoomInstance.center(); \n            \n            var pzSizes = panZoomInstance.getSizes();\n            var centerX = name_to_coord[name].x;\n            var centerY = -name_to_coord[name].y;\n            var newX = centerX*pzSizes["width"]/pzSizes["viewBox"]["width"];\n            var newY = centerY*pzSizes["height"]/pzSizes["viewBox"]["height"];\n            \n            //var zoomRatio = 1/(pzSizes["width"]/pzSizes["viewBox"]["width"]);\n            console.log(\'zr \'.concat(name, \' \', pzSizes, \' \', centerX, \' \', centerY, \' \', newX, \' \', newY));       \n            panZoomInstance.zoomAtPointBy(5, {\'x\':newX, \'y\':newY});\n        }\n        \n        function panToName(name) {\n            var x = name_to_coord[name].x; \n            var y = panZoomInstance.getSizes().viewBox.height + Number.parseInt(name_to_coord[name].y); \n            panZoomInstance.reset() \n            panZoomInstance.zoom(1/panZoomInstance.getSizes().realZoom, true)\n            panZoomInstance.pan({x:0,y:0});\n            var realZoom = panZoomInstance.getSizes().realZoom; \n            var destX = -((x * realZoom) - (panZoomInstance.getSizes().width/2));\n            var destY = -((y * realZoom) - (panZoomInstance.getSizes().height/2));\n            panZoomInstance.pan({\'x\':0,\'y\':0}); \n            panZoomInstance.pan({\'x\': destX, \'y\': destY})\n        }\n            \n        \n        function showTermGraph(term) {\n            var nodeName = \'svg\' + name_to_component[term];\n            document.getElementById(nodeName).style.display=\'block\'; \n            %s\n            panToName(term);\n        }\n\n        Array.from(document.querySelectorAll(\'.node\')).map(\n            function (node) {\n                node.addEventListener(\'mouseenter\', mouseEnterNode);\n                node.addEventListener(\'mouseleave\', mouseLeaveNode);\n                node.addEventListener(\'click\', clickNode);\n            }\n        )\n        \n        function clickNode() {\n            document.querySelectorAll(".dotgraph")\n                .forEach(node => node.style.display = \'none\');\n\n            var term = Array.prototype.filter\n                .call(this.children, (x => x.tagName === "text"))[0].textContent;\n\n            plotInterface.handleSearchTerm(term, true);\n        }\n\n        function mouseEnterNode(event) {\n            var term = Array.prototype.filter.call(this.children, (x => x.tagName === "text"))[0].textContent;\n            plotInterface.showTooltipSimple(term);\n            this.style.fill="red";\n        }\n\n        function mouseLeaveNode() {\n            plotInterface.tooltip.transition().style(\'opacity\', 0)\n            this.style.fill="black";\n        }' % (json.dumps(self.component_graph.get_node_to_component_dict()), self._get_pan_and_zoom_js())

    def _get_pan_and_zoom_js(self):
        if self.enable_pan_and_zoom:
            return "\n                panZoomInstance = svgPanZoom('#' + nodeName, {\n                    zoomEnabled: true,\n                    controlIconsEnabled: true,\n                    fit: true,\n                    center: true,\n                    maxZoom: 100000,\n                    minZoom: 0.1\n                  });\n            "
        else:
            return ''

def get_javascript(self):
    return '\n        name_to_component = %s;\n        \n        name_to_coord = {}; // term -> {x, y, svg} \n        origViewBox = {}; // svgid -> viewbox\n        \n        Array.prototype.forEach.call(\n            document.querySelectorAll(".dotgraph"),\n            function(svg) {\n                origViewBox[svg.id] = svg.getAttribute(\'viewBox\');\n                \n                Array.prototype.forEach.call(\n                    svg.getElementsByTagName(\'text\'), \n                    function(text) {\n                        name_to_coord[text.textContent] = {\n                            "x": text.getAttribute("x"), \n                            "y": text.getAttribute("y"), \n                            "svg": svg.id\n                        };\n                    }\n                )\n            }\n        ) \n        \n        panZoomInstance = null;\n        \n        \n        function zoomToName(name) {\n        \n            //panZoomInstance.reset();\n                        \n                        \n            console.log("ZOOMING TO "); console.log(name);\n            panZoomInstance.fit();\n            panZoomInstance.center(); \n            \n            var pzSizes = panZoomInstance.getSizes();\n            var centerX = name_to_coord[name].x;\n            var centerY = -name_to_coord[name].y;\n            var newX = centerX*pzSizes["width"]/pzSizes["viewBox"]["width"];\n            var newY = centerY*pzSizes["height"]/pzSizes["viewBox"]["height"];\n            \n            //var zoomRatio = 1/(pzSizes["width"]/pzSizes["viewBox"]["width"]);\n            console.log(\'zr \'.concat(name, \' \', pzSizes, \' \', centerX, \' \', centerY, \' \', newX, \' \', newY));       \n            panZoomInstance.zoomAtPointBy(5, {\'x\':newX, \'y\':newY});\n        }\n        \n        function panToName(name) {\n            var x = name_to_coord[name].x; \n            var y = panZoomInstance.getSizes().viewBox.height + Number.parseInt(name_to_coord[name].y); \n            panZoomInstance.reset() \n            panZoomInstance.zoom(1/panZoomInstance.getSizes().realZoom, true)\n            panZoomInstance.pan({x:0,y:0});\n            var realZoom = panZoomInstance.getSizes().realZoom; \n            var destX = -((x * realZoom) - (panZoomInstance.getSizes().width/2));\n            var destY = -((y * realZoom) - (panZoomInstance.getSizes().height/2));\n            panZoomInstance.pan({\'x\':0,\'y\':0}); \n            panZoomInstance.pan({\'x\': destX, \'y\': destY})\n        }\n            \n        \n        function showTermGraph(term) {\n            var nodeName = \'svg\' + name_to_component[term];\n            document.getElementById(nodeName).style.display=\'block\'; \n            %s\n            panToName(term);\n        }\n\n        Array.from(document.querySelectorAll(\'.node\')).map(\n            function (node) {\n                node.addEventListener(\'mouseenter\', mouseEnterNode);\n                node.addEventListener(\'mouseleave\', mouseLeaveNode);\n                node.addEventListener(\'click\', clickNode);\n            }\n        )\n        \n        function clickNode() {\n            document.querySelectorAll(".dotgraph")\n                .forEach(node => node.style.display = \'none\');\n\n            var term = Array.prototype.filter\n                .call(this.children, (x => x.tagName === "text"))[0].textContent;\n\n            plotInterface.handleSearchTerm(term, true);\n        }\n\n        function mouseEnterNode(event) {\n            var term = Array.prototype.filter.call(this.children, (x => x.tagName === "text"))[0].textContent;\n            plotInterface.showTooltipSimple(term);\n            this.style.fill="red";\n        }\n\n        function mouseLeaveNode() {\n            plotInterface.tooltip.transition().style(\'opacity\', 0)\n            this.style.fill="black";\n        }' % (json.dumps(self.component_graph.get_node_to_component_dict()), self._get_pan_and_zoom_js())

class ComponentDiGraph(object):

    def __init__(self, orig_edge_df, id_node_df, node_df, edge_df, components, graph_params=None, node_params=None):
        self.edge_df = edge_df
        self.orig_edge_df = orig_edge_df
        self.id_node_df = id_node_df
        self.node_df = node_df
        self.components = components
        self.graph_params = DEFAULT_GRAPH_PARAMS
        if graph_params is not None:
            for k, v in graph_params.items():
                self.graph_params[k] = v
        self.node_params = DEFAULT_NODE_PARAMS
        if node_params is not None:
            for k, v in node_params.items():
                self.node_params[k] = v

    def get_dot(self, component):
        graph = 'digraph  \n{\n graph [%s]\n node [%s] ;\n' % (self._format_graphviz_paramters(self.graph_params), self._format_graphviz_paramters(self.node_params))
        mynode_df = self.id_node_df[self.id_node_df['Component'] == component]
        nodes = '\n'.join(mynode_df.reset_index().apply(lambda x: '"%s" [label="%s"] ;' % (x['index'], x['name']), axis=1).values)
        edges = '\n'.join(self.edge_df[self.edge_df.Component == component].apply(lambda x: '"%s" -> "%s" ;' % (x.source_id, x.target_id), axis=1).values)
        return graph + nodes + '\n\n' + edges + '\n}'

    def get_components_at_least_size(self, min_size):
        component_sizes = pd.DataFrame({'component': self.components}).reset_index().groupby('component')[['index']].apply(len).where(lambda x: x >= min_size).dropna()
        return np.array(component_sizes.sort_values(ascending=False).index)

    def get_node_to_component_dict(self):
        return self.id_node_df.set_index('name')['Component'].to_dict()

    def component_to_node_list_dict(self):
        return self.id_node_df.groupby('Component')['name'].apply(list).to_dict()

    def _format_graphviz_paramters(self, params):
        return ', '.join([k + '=' + ('"' if type(v) == str else '') + str(v) + ('"' if type(v) == str else '') for k, v in params.items()])

def __init__(self, orig_edge_df, id_node_df, node_df, edge_df, components, graph_params=None, node_params=None):
    self.edge_df = edge_df
    self.orig_edge_df = orig_edge_df
    self.id_node_df = id_node_df
    self.node_df = node_df
    self.components = components
    self.graph_params = DEFAULT_GRAPH_PARAMS
    if graph_params is not None:
        for k, v in graph_params.items():
            self.graph_params[k] = v
    self.node_params = DEFAULT_NODE_PARAMS
    if node_params is not None:
        for k, v in node_params.items():
            self.node_params[k] = v

def _rebuild_suffixes(emoji_spec_url='http://www.unicode.org/Public/emoji/5.0/emoji-test.txt'):
    valid_seqs = pd.DataFrame(pd.read_csv(emoji_spec_url, sep=';', comment='#', names=['code_points', 'status'])['code_points'].apply(lambda x: pd.Series({'seq': [int(c, 16) for c in x.split()], 'len': len(x.split())}))).sort_values(by=['len'], ascending=False)['seq']
    suffixes_construct = {}
    for x in valid_seqs:
        suffix = tuple(x[1:])
        suffix_holder = suffixes_construct.setdefault(x[0], {})
        suffix_set = suffix_holder.setdefault(len(suffix), set())
        suffix_set.add(suffix)
    for k, v in suffixes_construct.items():
        suffixes_construct[k] = list(reversed(sorted(v.items())))
    return suffixes_construct

def retopt(x):
    our_options.add(x)
    return x in output

class SubwordSensitiveSentenceBoundedSplitter:

    def __init__(self, tokenizer: Callable, max_segment_size: int=100):
        self.tokenizer = tokenizer
        self.max_segment_size = max_segment_size

    def segment(self, doc: spacy.tokens.doc.Doc) -> Iterable[spacy.tokens.span.Span]:
        sent_interval_index = pd.IntervalIndex.from_tuples([(s[0].idx, s[0].idx + len(str(s))) for s in doc.sents])
        subtokens = self.tokenizer(str(doc), return_offsets_mapping=True)
        subtoken_offset_df = pd.DataFrame(subtokens['offset_mapping'], columns=['SubStart', 'SubEnd']).assign(InputId=subtokens['input_ids'], StartSentenceId=lambda df: sent_interval_index.get_indexer(df.SubStart), EndSentenceId=lambda df: sent_interval_index.get_indexer(df.SubEnd), SentenceId=lambda df: np.where((df.StartSentenceId > 0) & (df.EndSentenceId > 0), (df.EndSentenceId + df.StartSentenceId) / 2, df[['StartSentenceId', 'EndSentenceId']].max(axis=1)))[lambda df: (df.SubStart < df.SubEnd) & (df.SentenceId > -1)].assign(Count=lambda df: np.arange(len(df)) + 1)
        subtoken_subsent_offset_df = pd.merge(subtoken_offset_df, pd.DataFrame({'SentStart': subtoken_offset_df.groupby('SentenceId').Count.min()}), left_on='SentenceId', right_index=True).assign(SentCount=lambda df: df.Count - df.SentStart, SubsentenceId=lambda df: df.SentCount // self.max_segment_size)

        def limit_cum_sum_slow(x):
            if limit_cum_sum.prev + x > self.max_segment_size:
                limit_cum_sum.prev = x
                limit_cum_sum.segment_num += 1
                return limit_cum_sum.segment_num
            limit_cum_sum.prev += x
            return limit_cum_sum.segment_num
        limit_cum_sum = np.vectorize(limit_cum_sum_slow, otypes=[np.int32])
        limit_cum_sum.prev = 0
        limit_cum_sum.segment_num = 0
        for _, segment_df in subtoken_subsent_offset_df.groupby(['SentenceId', 'SubsentenceId']).apply(lambda gdf: pd.Series({'Length': len(gdf), 'Start': gdf.SubStart.min(), 'End': gdf.SubEnd.max()})).assign(Supersegment=lambda df: limit_cum_sum(df.Length.values)).reset_index().groupby('Supersegment'):
            if segment_df.Length.sum() > self.max_segment_size:
                import pdb
                pdb.set_trace()
            yield doc.char_span(segment_df.Start.min(), segment_df.End.max(), alignment_mode='expand')

    def __segments_from_subtoken_offsets(self, subtoken_offset_df: pd.DataFrame) -> pd.DataFrame:
        return subtoken_offset_df[lambda df: df.SentenceId == df.SentenceId.apply(int)].groupby('SentenceId').apply(lambda gdf: pd.Series({'Length': len(gdf), 'Start': gdf.SubStart.min(), 'End': gdf.SubEnd.max(), 'InputId': gdf.InputId.values})).reset_index().assign(Segment=lambda df: self.__sentence_segments_from_subtokens(df)).groupby('Segment').agg({'Start': 'min', 'End': 'max', 'SentenceId': lambda x: list((int(x) for x in sorted(x))), 'InputId': np.hstack})

    def __sentence_segments_from_subtokens(self, sentence_df: pd.DataFrame) -> pd.DataFrame:
        inside_segment = False
        current_segment = 0
        tokens_in_segment = 0
        sentence_segments = []
        for sentence_id, row in sentence_df.iterrows():
            if inside_segment:
                tokens_in_segment += row.Length
            if int(sentence_id) == sentence_id:
                if inside_segment is False:
                    inside_segment = True
                potential_additional_tokens = 0
                if sentence_id + 0.5 in sentence_df.index:
                    potential_additional_tokens += sentence_df.loc[sentence_id + 0.5].Length
                if sentence_id + 1 in sentence_df.index:
                    potential_additional_tokens += sentence_df.loc[sentence_id + 1].Length
                sentence_segments.append(current_segment)
                if tokens_in_segment + potential_additional_tokens <= self.max_segment_size:
                    tokens_in_segment += potential_additional_tokens
                else:
                    tokens_in_segment = potential_additional_tokens
                    current_segment += 1
                    inside_segment = False
            else:
                sentence_segments.append(current_segment if inside_segment else -1)
        return pd.DataFrame(sentence_segments)

def __sentence_segments_from_subtokens(self, sentence_df: pd.DataFrame) -> pd.DataFrame:
    inside_segment = False
    current_segment = 0
    tokens_in_segment = 0
    sentence_segments = []
    for sentence_id, row in sentence_df.iterrows():
        if inside_segment:
            tokens_in_segment += row.Length
        if int(sentence_id) == sentence_id:
            if inside_segment is False:
                inside_segment = True
            potential_additional_tokens = 0
            if sentence_id + 0.5 in sentence_df.index:
                potential_additional_tokens += sentence_df.loc[sentence_id + 0.5].Length
            if sentence_id + 1 in sentence_df.index:
                potential_additional_tokens += sentence_df.loc[sentence_id + 1].Length
            sentence_segments.append(current_segment)
            if tokens_in_segment + potential_additional_tokens <= self.max_segment_size:
                tokens_in_segment += potential_additional_tokens
            else:
                tokens_in_segment = potential_additional_tokens
                current_segment += 1
                inside_segment = False
        else:
            sentence_segments.append(current_segment if inside_segment else -1)
    return pd.DataFrame(sentence_segments)

class CorpusRunningStatsFactory:

    def __init__(self, corpus: Union[ParsedCorpus, OffsetCorpus], model: PreTrainedModel, tokenizer: PreTrainedTokenizerFast, feats_from_spacy_doc: Optional[FeatsFromSpacyDoc]=None, doc_segmenter: Optional[Callable[[spacy.tokens.doc.Doc], Iterable[spacy.tokens.span.Span]]]=None, token_normalizer: Optional[Callable[[spacy.tokens.Token], str]]=None, use_all_tokens_for_category_embeddings: bool=True, weights_to_embeddings: Callable=last_hidden_state_embeddings):
        """

        :param corpus:
        :param model:
        :param tokenizer:
        :param feats_from_spacy_doc: if none, use offsets
        :param doc_segmenter:
        :param token_normalizer: Function which takes spacy token and returns a string.
          Not used for embedding calculation, just feature representation. Lowercases all by default.
        :param use_all_tokens_for_category_embeddings: bool, Use all tokens in segment for category embeddings?
        """
        self.corpus = corpus
        self.model = model
        self.tokenizer = tokenizer
        self.feats_from_spacy_doc = feats_from_spacy_doc
        if not isinstance(corpus, OffsetCorpus):
            raise Exception('Since the corpus object is not an offset corpus, feats_from_spacy_doc needs to be passed.')
        self.doc_segmenter = doc_sentence_splitter if doc_segmenter is None else doc_segmenter
        self.token_normalizer = lambda x: x.lower_ if token_normalizer is None else token_normalizer
        self.weights_to_embeddings = weights_to_embeddings
        self.use_all_tokens_for_category_embeddings = use_all_tokens_for_category_embeddings

    def build(self, verbose: bool=True) -> CorpusRunningStats:
        running_stats = self.initialize_running_stats()
        offset_df = self.__build_offset_df()
        for i, row in self.__iter_docs_and_cats(verbose=verbose):
            if isinstance(self.corpus, OffsetCorpus):
                self._add_offsets_to_running_stats(doc_idx=i, doc=row.Doc, cat=row.Cat, running_stats=running_stats, offset_df=offset_df)
            else:
                raise Exception('Only implemented for OffsetCorpus. ParsedCorpus implementation will happen at some point in the future.')
        return running_stats

    def __build_offset_df(self):
        offset_data = []
        for term, values in self.corpus.get_offsets().items():
            term_idx = self.corpus.get_metadata_index(term)
            for doc_idx, offsets in values.items():
                for start, end in offsets:
                    offset_data.append([doc_idx, term_idx, start, end])
        offset_df = pd.DataFrame(offset_data, columns=['DocIdx', 'TermIdx', 'Start', 'End']).sort_values(by=['DocIdx', 'Start', 'End']).set_index('DocIdx')
        return offset_df

    def _add_offsets_to_running_stats(self, doc_idx, doc, cat, running_stats, offset_df) -> None:
        doc_offset_df = self.__query_for_doc_offset_df(offset_df, doc_idx)
        if len(doc_offset_df):
            for segment in self.doc_segmenter(doc):
                seg_start = segment[0].idx
                seg_end = seg_start + len(str(segment))
                try:
                    annots = doc_offset_df[lambda df: (df.Start >= seg_start) & (df.End <= seg_end)]
                except:
                    print('!!!')
                    print(doc_offset_df)
                    print(seg_start, seg_end)
                    print((doc_offset_df.Start >= seg_start) & (doc_offset_df.End <= seg_end))
                    mask = (doc_offset_df.Start >= seg_start) & (doc_offset_df.End <= seg_end)
                    import pdb
                    pdb.set_trace()
                embeddings = None
                if len(annots):
                    embeddings, subtoken_offsets = self.__embed_segment(segment, seg_start)
                    annots.apply(lambda r: self.__add_term_to_stats(term=self.corpus.get_metadata_from_index(r.TermIdx), kw_start=r.Start, kw_end=r.End, embeddings=embeddings, running_stats=running_stats, subtoken_offsets=subtoken_offsets, cat=cat, add_to_category_embeddings=not self.use_all_tokens_for_category_embeddings, segment=segment, seg_start=seg_start), axis=1)
                if self.use_all_tokens_for_category_embeddings:
                    if embeddings is None:
                        embeddings, _ = self.__embed_segment(segment, seg_start, adjust_offsets=False)
                    running_stats.add_embeddings_to_category(embeddings=embeddings, cat=cat)

    def __embed_segment(self, segment, seg_start, adjust_offsets=True):
        str_segment = str(segment)
        inputs = self.tokenizer(str_segment, return_tensors='pt', return_offsets_mapping=True)
        subtoken_offsets = inputs['offset_mapping'].cpu().detach().numpy()[0][1:-1]
        try:
            embeddings = self.__inputs_to_embeddings(inputs=inputs)
        except Exception as e:
            import pdb
            pdb.set_trace()
            raise e
        if adjust_offsets:
            subtoken_offsets_whitespace_stripped = []
            for s, e in subtoken_offsets:
                subtoken = str_segment[s:e]
                s += len(subtoken) - len(subtoken.lstrip())
                e -= len(subtoken) - len(subtoken.rstrip())
                if s != e:
                    subtoken_offsets_whitespace_stripped.append([s, e])
            subtoken_offsets = np.array(subtoken_offsets_whitespace_stripped)
        return (embeddings, subtoken_offsets.T + seg_start)

    def __query_for_doc_offset_df(self, offset_df: pd.DataFrame, doc_idx: int) -> pd.DataFrame:
        try:
            doc_offset_df = offset_df.loc[doc_idx]
        except KeyError:
            return pd.DataFrame([])
        if type(doc_offset_df) == pd.Series:
            return pd.DataFrame([dict(doc_offset_df)])
        return doc_offset_df

    def __add_term_to_stats(self, term: str, kw_start: int, kw_end: int, embeddings: np.array, running_stats: CorpusRunningStats, subtoken_offsets: np.array, cat: str, add_to_category_embeddings: bool, segment: str, seg_start: int):
        subtoken_start = np.searchsorted(subtoken_offsets[0], kw_start)
        subtoken_end = np.searchsorted(subtoken_offsets[1], kw_end, side='right')
        if subtoken_start == subtoken_end:
            if subtoken_start > 0:
                subtoken_start -= 1
            elif subtoken_end < subtoken_offsets.shape[1] - 1:
                subtoken_end += 1
            else:
                print([f'|{t}|' for t in segment])
                print(kw_start, kw_end)
                print('part', str(segment)[kw_start - seg_start:kw_end - seg_start])
                print('term', term)
                print('subtoken start end', subtoken_start, subtoken_end)
                print(seg_start)
                print(subtoken_offsets)
                for s, e in subtoken_offsets.T:
                    print(s, e, str(segment)[s - seg_start:e - seg_start])
                import pdb
                pdb.set_trace()
        kw_embedding = embeddings[subtoken_start:subtoken_end].mean(axis=0)
        if not np.isnan(kw_embedding).any():
            running_stats.add(term=term, cat=cat, embedding=kw_embedding, add_to_category_embeddings=add_to_category_embeddings)

    def __inputs_to_embeddings(self, inputs):
        return self.weights_to_embeddings(model=self.model, inputs=inputs)

    def __iter_docs_and_cats(self, verbose: bool):
        it = self.corpus.get_df()[[self.corpus.get_category_column(), self.corpus.get_parsed_column()]].rename(columns={self.corpus.get_category_column(): 'Cat', self.corpus.get_parsed_column(): 'Doc'}).itertuples()
        if verbose:
            it = tqdm(it, total=self.corpus.get_num_docs())
        return enumerate(it)

    def initialize_running_stats(self):
        running_stats = CorpusRunningStats(corpus=self.corpus, embedding_width=None)
        return running_stats

    def _get_segment_token_embeddings(self, segment: spacy.tokens.span.Span) -> np.array:
        inputs = self.tokenizer(str(segment), return_tensors='pt')
        return self.model(**inputs).last_hidden_state.detach().numpy()

def __add_term_to_stats(self, term: str, kw_start: int, kw_end: int, embeddings: np.array, running_stats: CorpusRunningStats, subtoken_offsets: np.array, cat: str, add_to_category_embeddings: bool, segment: str, seg_start: int):
    subtoken_start = np.searchsorted(subtoken_offsets[0], kw_start)
    subtoken_end = np.searchsorted(subtoken_offsets[1], kw_end, side='right')
    if subtoken_start == subtoken_end:
        if subtoken_start > 0:
            subtoken_start -= 1
        elif subtoken_end < subtoken_offsets.shape[1] - 1:
            subtoken_end += 1
        else:
            print([f'|{t}|' for t in segment])
            print(kw_start, kw_end)
            print('part', str(segment)[kw_start - seg_start:kw_end - seg_start])
            print('term', term)
            print('subtoken start end', subtoken_start, subtoken_end)
            print(seg_start)
            print(subtoken_offsets)
            for s, e in subtoken_offsets.T:
                print(s, e, str(segment)[s - seg_start:e - seg_start])
            import pdb
            pdb.set_trace()
    kw_embedding = embeddings[subtoken_start:subtoken_end].mean(axis=0)
    if not np.isnan(kw_embedding).any():
        running_stats.add(term=term, cat=cat, embedding=kw_embedding, add_to_category_embeddings=add_to_category_embeddings)

class UseFullDocAsMetadata(FeatsFromSpacyDoc):

    def get_feats(self, doc):
        return Counter()

    def get_doc_metadata(self, doc):
        """
        Parameters
        ----------
        doc, Spacy Docs

        Returns
        -------
        Counter str -> count
        """
        return Counter({str(doc): 1})

def get_feats(self, doc):
    return Counter()

def get_doc_metadata(self, doc):
    """
        Parameters
        ----------
        doc, Spacy Docs

        Returns
        -------
        Counter str -> count
        """
    return Counter({str(doc): 1})

class FeatsFromTopicModelBase(ABC):

    def __init__(self, topic_model):
        self._topic_model = topic_model
        self._lexicon_df = self._get_lexicon_df_from_topic_model(topic_model)

    def _get_lexicon_df_from_topic_model(self, topic_model):
        return pd.DataFrame(pd.Series(topic_model).apply(pd.Series).reset_index()).melt(id_vars=['index'])[['index', 'value']].rename(columns={'index': 'cat', 'value': 'term'}).set_index('term')

    def _analyze(self, doc):
        text_df = pd.DataFrame(pd.Series(self._get_terms_from_doc(doc))).join(self._lexicon_df).dropna().groupby('cat').sum()
        return text_df

    def get_doc_metadata(self, doc, prefix=''):
        feature_counter = Counter()
        if version_info[0] >= 3:
            doc = str(doc)
        for category, score in self._analyze(doc).to_dict()[0].items():
            feature_counter[prefix + category] = int(score)
        return feature_counter

    @abstractmethod
    def _get_terms_from_doc(self, doc):
        pass

def get_doc_metadata(self, doc, prefix=''):
    feature_counter = Counter()
    if version_info[0] >= 3:
        doc = str(doc)
    for category, score in self._analyze(doc).to_dict()[0].items():
        feature_counter[prefix + category] = int(score)
    return feature_counter

class FeatsFromTopicModel(FeatsFromTopicModelBase, FeatsFromSpacyDoc):

    def __init__(self, topic_model, use_lemmas=False, entity_types_to_censor=set(), entity_types_to_use=None, tag_types_to_censor=set(), strip_final_period=False, keyword_processor_args={'case_sensitive': False}):
        self._keyword_processor = KeywordProcessor(**keyword_processor_args)
        self._topic_model = topic_model.copy()
        if keyword_processor_args.get('case_sensitive', None) is False:
            for k, v in self._topic_model.items():
                self._topic_model[k] = [e.lower() for e in v]
        for keyphrase in reduce(lambda x, y: set(x) | set(y), self._topic_model.values()):
            self._keyword_processor.add_keyword(keyphrase)
        FeatsFromSpacyDoc.__init__(self, use_lemmas, entity_types_to_censor, tag_types_to_censor, strip_final_period)
        FeatsFromTopicModelBase.__init__(self, topic_model)

    def get_top_model_term_lists(self):
        return self._topic_model

    def _get_terms_from_doc(self, doc):
        return Counter(self._keyword_processor.extract_keywords(str(doc)))

    def get_feats(self, doc):
        return Counter(self._get_terms_from_doc(str(doc)))

def _get_terms_from_doc(self, doc):
    return Counter(self._keyword_processor.extract_keywords(str(doc)))

def get_feats(self, doc):
    return Counter(self._get_terms_from_doc(str(doc)))

class PyatePhrases(FeatsFromSpacyDoc):

    def __init__(self, extractor=None, **args):
        import pyate
        self._extractor = pyate.combo_basic if extractor is None else extractor
        FeatsFromSpacyDoc.__init__(self, **args)

    def get_feats(self, doc):
        return Counter(self._extractor(str(doc)).to_dict())

def get_feats(self, doc):
    return Counter(self._extractor(str(doc)).to_dict())

class FeatsFromMoralFoundationsDictionary(FeatsFromSpacyDoc):

    def __init__(self, use_lemmas=False, entity_types_to_censor=set(), tag_types_to_censor=set(), strip_final_period=False, **kwargs):
        """
        Parameters
        ----------
        Other parameters from FeatsFromSpacyDoc.__init__
        """
        self._lexicon_df = self._load_mfd()
        super(FeatsFromMoralFoundationsDictionary, self).__init__(use_lemmas, entity_types_to_censor, tag_types_to_censor, strip_final_period)

    def _load_mfd(self):
        return pd.read_csv(io.StringIO(pkgutil.get_data('scattertext', 'data/mfd2.0.csv').decode('utf-8'))).set_index('term')

    def _analyze(self, doc):
        text_df = pd.DataFrame(pd.Series(Counter((t for t in split('(\\W)', doc.lower()) if t.strip())))).join(self._lexicon_df).dropna().groupby('cat').sum()
        return text_df

    def get_definitions(self):
        """
        These definitions are from https://osf.io/xakyw/

        :return: dict
        """
        return {'care.virtue': '...acted with kindness, compassion, or empathy, or nurtured another person.', 'care.vice': '...acted with cruelty, or hurt or harmed another person/animal and caused suffering.', 'fairness.virtue': '...acted in a fair manner, promoting equality, justice, or rights.', 'fairness.vice': '...was unfair or cheated, or caused an injustice or engaged in fraud.', 'loyalty.virtue': '...acted with fidelity, or as a team player, or was loyal or patriotic.', 'loyalty.vice': '...acted disloyal, betrayed someone, was disloyal, or was a traitor.', 'authority.virtue': '...obeyed, or acted with respect for authority or tradition.', 'authority.vice': '...disobeyed or showed disrespect, or engaged in subversion or caused chaos', 'sanctity.virtue': '...acted in a way that was wholesome or sacred, or displayed purity or sanctity', 'sanctity.vice': '...was depraved, degrading, impure, or unnatural.'}

    def get_doc_metadata(self, doc, prefix=''):
        topic_counter = Counter()
        if version_info[0] >= 3:
            doc = str(doc)
        for topic_category, score in self._analyze(doc).to_dict()[0].items():
            topic_counter[prefix + topic_category] = int(score)
        return topic_counter

    def has_metadata_term_list(self):
        return True

    def get_top_model_term_lists(self):
        return self._lexicon_df.reset_index().groupby('cat')['term'].apply(list).to_dict()

def get_doc_metadata(self, doc, prefix=''):
    topic_counter = Counter()
    if version_info[0] >= 3:
        doc = str(doc)
    for topic_category, score in self._analyze(doc).to_dict()[0].items():
        topic_counter[prefix + topic_category] = int(score)
    return topic_counter

class UnigramsFromSpacyDoc(FeatsFromSpacyDoc):

    def get_feats(self, doc):
        """
		Parameters
		----------
		doc, Spacy Docs

		Returns
		-------
		Counter (unigram, bigram) -> count
		"""
        ngram_counter = Counter()
        for sent in doc.sents:
            ngram_counter += Counter(self._get_unigram_feats(sent))
        return ngram_counter

def get_feats(self, doc):
    """
		Parameters
		----------
		doc, Spacy Docs

		Returns
		-------
		Counter (unigram, bigram) -> count
		"""
    ngram_counter = Counter()
    for sent in doc.sents:
        ngram_counter += Counter(self._get_unigram_feats(sent))
    return ngram_counter

class UseFullDocAsFeature(FeatsFromSpacyDoc):

    def get_feats(self, doc):
        """
        Parameters
        ----------
        doc, Spacy Docs

        Returns
        -------
        Counter str -> count
        """
        return Counter({str(doc): 1})

def get_feats(self, doc):
    """
        Parameters
        ----------
        doc, Spacy Docs

        Returns
        -------
        Counter str -> count
        """
    return Counter({str(doc): 1})

class FeatsFromSpacyDocAndEmpath(FeatsFromSpacyDoc):

    def __init__(self, use_lemmas=False, entity_types_to_censor=set(), tag_types_to_censor=set(), strip_final_period=False, empath_analyze_function=None, **kwargs):
        """
        Parameters
        ----------
        empath_analyze_function: function (default=empath.Empath().analyze)
            Function that produces a dictionary mapping Empath categories to

        Other parameters from FeatsFromSpacyDoc.__init__
        """
        if empath_analyze_function is None:
            try:
                import empath
            except ImportError:
                raise Exception('Please install the empath library to use FeatsFromSpacyDocAndEmpath.')
            self._empath_analyze_function = empath.Empath().analyze
        else:
            self._empath_analyze_function = partial(empath_analyze_function, kwargs={'tokenizer': 'bigram'})
        FeatsFromSpacyDoc.__init__(self, use_lemmas, entity_types_to_censor, tag_types_to_censor, strip_final_period)

    def get_doc_metadata(self, doc, prefix=''):
        empath_counter = Counter()
        if version_info[0] >= 3:
            doc = str(doc)
        for empath_category, score in self._empath_analyze_function(doc).items():
            if score > 0:
                empath_counter[prefix + empath_category] = int(score)
        return empath_counter

    def has_metadata_term_list(self):
        return True

    def get_top_model_term_lists(self):
        try:
            import empath
        except ImportError:
            raise Exception('Please install the empath library to use FeatsFromSpacyDocAndEmpath.')
        return dict(empath.Empath().cats)

def get_doc_metadata(self, doc, prefix=''):
    empath_counter = Counter()
    if version_info[0] >= 3:
        doc = str(doc)
    for empath_category, score in self._empath_analyze_function(doc).items():
        if score > 0:
            empath_counter[prefix + empath_category] = int(score)
    return empath_counter

class FeatsFromOnlyEmpath(FeatsFromSpacyDocAndEmpath):

    def get_feats(self, doc):
        return Counter()

    def get_doc_metadata(self, doc, prefix=''):
        return FeatsFromSpacyDocAndEmpath.get_doc_metadata(self, doc, prefix=prefix)

def get_feats(self, doc):
    return Counter()

def get_doc_metadata(self, doc, prefix=''):
    return FeatsFromSpacyDocAndEmpath.get_doc_metadata(self, doc, prefix=prefix)

class PyTextRankPhrases(FeatsFromSpacyDoc):

    def __init__(self, use_lemmas=False, entity_types_to_censor=set(), tag_types_to_censor=set(), strip_final_period=False):
        FeatsFromSpacyDoc.__init__(self, use_lemmas, entity_types_to_censor, tag_types_to_censor, strip_final_period)
        self._include_chunks = False
        self._rank_smoothing_constant = 0

    def include_chunks(self):
        """
        Use each chunk in a phrase instead of just the span identified as a phrase
        :return: self
        """
        self._include_chunks = True
        return self

    def set_rank_smoothing_constant(self, rank_smoothing_constant):
        """
        Add a quantity

        :param rank_smoothing_constant: float
        :return: self
        """
        self._rank_smoothing_constant = rank_smoothing_constant
        return self

    def get_doc_metadata(self, doc):
        phrase_counter = Counter()
        try:
            for phrase in doc._.phrases:
                if self._include_chunks:
                    for chunk in phrase.chunks:
                        phrase_counter[str(chunk)] += phrase.rank + self._rank_smoothing_constant
                else:
                    phrase_counter[phrase.text] += phrase.count * (phrase.rank + self._rank_smoothing_constant)
        except:
            import pytextrank
            tr = pytextrank.TextRank()
            tr.doc = doc
            phrases = tr.calc_textrank()
            for phrase in phrases:
                if self._include_chunks:
                    for chunk in phrase.chunks:
                        phrase_counter[str(chunk)] += phrase.rank + self._rank_smoothing_constant
                else:
                    phrase_counter[phrase.text] += phrase.count * (phrase.rank + self._rank_smoothing_constant)
        return phrase_counter

    def get_feats(self, doc):
        return Counter()

def get_doc_metadata(self, doc):
    phrase_counter = Counter()
    try:
        for phrase in doc._.phrases:
            if self._include_chunks:
                for chunk in phrase.chunks:
                    phrase_counter[str(chunk)] += phrase.rank + self._rank_smoothing_constant
            else:
                phrase_counter[phrase.text] += phrase.count * (phrase.rank + self._rank_smoothing_constant)
    except:
        import pytextrank
        tr = pytextrank.TextRank()
        tr.doc = doc
        phrases = tr.calc_textrank()
        for phrase in phrases:
            if self._include_chunks:
                for chunk in phrase.chunks:
                    phrase_counter[str(chunk)] += phrase.rank + self._rank_smoothing_constant
            else:
                phrase_counter[phrase.text] += phrase.count * (phrase.rank + self._rank_smoothing_constant)
    return phrase_counter

def get_feats(self, doc):
    return Counter()

class PhraseMachinePhrases(FeatsFromSpacyDoc):
    """
	Returns unigrams and phrase machine phrases
	"""

    def get_feats(self, doc):
        """
		Parameters
		----------
		doc, Spacy Doc

		Returns
		-------
		Counter noun chunk -> count
		"""
        ngram_counter = Counter()
        for sent in doc.sents:
            ngram_counter += _phrase_counts(sent)
        return ngram_counter

def get_feats(self, doc):
    """
		Parameters
		----------
		doc, Spacy Doc

		Returns
		-------
		Counter noun chunk -> count
		"""
    ngram_counter = Counter()
    for sent in doc.sents:
        ngram_counter += _phrase_counts(sent)
    return ngram_counter

class PhraseMachinePhrasesAndUnigrams(FeatsFromSpacyDoc):
    """
	Returns unigrams and phrase machine phrases
	"""

    def get_feats(self, doc):
        """
		Parameters
		----------
		doc, Spacy Doc

		Returns
		-------
		Counter noun chunk -> count
		"""
        ngram_counter = Counter()
        for sent in doc.sents:
            unigrams = self._get_unigram_feats(sent)
            ngram_counter += Counter(unigrams) + _phrase_counts(sent)
        return ngram_counter

def get_feats(self, doc):
    """
		Parameters
		----------
		doc, Spacy Doc

		Returns
		-------
		Counter noun chunk -> count
		"""
    ngram_counter = Counter()
    for sent in doc.sents:
        unigrams = self._get_unigram_feats(sent)
        ngram_counter += Counter(unigrams) + _phrase_counts(sent)
    return ngram_counter

class LexiconFeatAndOffsetGetter(FeatAndOffsetGetter):

    def __init__(self, lexicons: Dict[str, List[List[str]]], definitions: Optional[Dict[str, str]]=None, case_sensitive: bool=False):
        """
        :param lexicons: Dict[str, List[List[str]]], maps a topic name to its list of word sequences
        :param definitions, Optional[Dict[str, str]], maps topic name to an explanation.
        :param case_sensitive: bool, are word sequences case-sensitive?
        """
        self.definitions = definitions
        self.keyword_processor = flashtext.KeywordProcessor(case_sensitive)
        self.keyword_processor.add_keywords_from_dict({topic: [' '.join(term_sequence) for term_sequence in term_sequences] for topic, term_sequences in lexicons.items()})

    def get_term_offsets(self, doc) -> List[Tuple[str, List[Tuple[int, int]]]]:
        return []

    def get_metadata_offsets(self, doc) -> List[Tuple[str, List[Tuple[int, int]]]]:
        text = str(doc)
        offset_tokens = {}
        for topic, start_index, end_index in self.keyword_processor.extract_keywords(text, span_info=True):
            token_stats = offset_tokens.setdefault(topic, [0, []])
            token_stats[0] += 1
            token_stats[1].append((start_index, end_index))
        return list(offset_tokens.items())

    def get_definitions(self):
        return self.definitions

def get_metadata_offsets(self, doc) -> List[Tuple[str, List[Tuple[int, int]]]]:
    text = str(doc)
    offset_tokens = {}
    for topic, start_index, end_index in self.keyword_processor.extract_keywords(text, span_info=True):
        token_stats = offset_tokens.setdefault(topic, [0, []])
        token_stats[0] += 1
        token_stats[1].append((start_index, end_index))
    return list(offset_tokens.items())

class RegexFeatAndOffsetGetter(FeatAndOffsetGetter):

    def __init__(self, regex_dict: Dict[str, str], flags: int=re.U | re.I | re.M, span_getter: Optional[Callable[[re.Match], Tuple[int, int]]]=None):
        """

        :param regex_dict: dict
            This should be a dictionary mapping a label to the text of a regular expression
            e.g., {'AorB': r'(a|b)', 'Number: r'\\d+'}
        :param flags: int, default re.U | re.I | re.M
            Same as re   flags
        :param span_getter : Optional[Callable[[re.Match], Tuple[int, int]]]
            Takes a match and returns a span. default: `lambda match: match.span()`
        """
        self.flags = flags
        self.labeled_regexes = [[k, re.compile(v, self.flags)] for k, v in regex_dict.items()]
        if span_getter is None:
            self.span_getter = lambda match: match.span()
        else:
            self.span_getter = span_getter

    def get_term_offsets(self, doc: Doc) -> List[Tuple[str, List[Tuple[int, int]]]]:
        return []

    def get_metadata_offsets(self, doc: Doc) -> List[Tuple[str, List[Tuple[int, int]]]]:
        text = str(doc)
        offset_tokens = {}
        for label, regex in self.labeled_regexes:
            for match in regex.finditer(text):
                token_stats = offset_tokens.setdefault(label, [0, []])
                token_stats[0] += 1
                span = self.span_getter(match)
                token_stats[1].append(span)
        return list(offset_tokens.items())

def get_metadata_offsets(self, doc: Doc) -> List[Tuple[str, List[Tuple[int, int]]]]:
    text = str(doc)
    offset_tokens = {}
    for label, regex in self.labeled_regexes:
        for match in regex.finditer(text):
            token_stats = offset_tokens.setdefault(label, [0, []])
            token_stats[0] += 1
            span = self.span_getter(match)
            token_stats[1].append(span)
    return list(offset_tokens.items())

class RogetOffsetGetter(FeatAndOffsetGetter):

    def __init__(self):
        self.lex_dict = pd.read_csv(io.BytesIO(bz2.decompress(pkgutil.get_data('scattertext', 'data/roget.csv.bz2'))), names=['term', 'category']).set_index('term')['category'].to_dict()

    def get_term_offsets(self, doc) -> List[Tuple[str, List[Tuple[int, int]]]]:
        return []

    def get_metadata_offsets(self, doc) -> List[Tuple[str, List[Tuple[int, int]]]]:
        offset_tokens = {}
        for tok in doc:
            match = self.lex_dict.get(tok.lower_)
            if match is not None:
                token_stats = offset_tokens.setdefault(match, [0, []])
                token_stats[0] += 1
                token_stats[1].append((tok.idx, tok.idx + len(tok)))
        return list(offset_tokens.items())

def get_metadata_offsets(self, doc) -> List[Tuple[str, List[Tuple[int, int]]]]:
    offset_tokens = {}
    for tok in doc:
        match = self.lex_dict.get(tok.lower_)
        if match is not None:
            token_stats = offset_tokens.setdefault(match, [0, []])
            token_stats[0] += 1
            token_stats[1].append((tok.idx, tok.idx + len(tok)))
    return list(offset_tokens.items())

class FeatsFromSentencePiece(FeatsFromSpacyDoc):

    def __init__(self, sp, *args, **kwargs):
        """
        :param sp: sentencepiece.SentencePieceProcessor
        """
        self._sp = sp
        super(FeatsFromSentencePiece, self).__init__(*args, **kwargs)

    def get_doc_metadata(self, doc):
        """

        :param doc: spacy.Doc
        :return: pd.Series
        """
        return Counter(self._sp.encode_as_pieces(str(doc)))

def get_doc_metadata(self, doc):
    """

        :param doc: spacy.Doc
        :return: pd.Series
        """
    return Counter(self._sp.encode_as_pieces(str(doc)))

class FeatsFromGeneralInquirer(FeatsFromSpacyDoc):

    def __init__(self, use_lemmas=False, entity_types_to_censor=set(), tag_types_to_censor=set(), strip_final_period=False, **kwargs):
        """
        Parameters
        ----------
        empath_analyze_function: function (default=empath.Empath().analyze)
            Function that produces a dictionary mapping Empath categories to

        Other parameters from FeatsFromSpacyDoc.__init__
        """
        self._lexicon_df = self._download_and_parse_general_inquirer()
        super(FeatsFromGeneralInquirer, self).__init__(use_lemmas, entity_types_to_censor, tag_types_to_censor, strip_final_period)

    def _download_and_parse_general_inquirer(self):
        df = pd.read_csv(GENERAL_INQUIRER_URL, sep='\t')
        return df.T[2:-4].apply(lambda x: list(df.Entry.apply(lambda x: x.split('#')[0]).loc[x.dropna().index].drop_duplicates().apply(str.lower)), axis=1).apply(pd.Series).stack().reset_index()[['level_0', 0]].rename(columns={'level_0': 'cat', 0: 'term'}).set_index('term')

    def _analyze(self, doc):
        text_df = pd.DataFrame(pd.Series(Counter((t for t in split('(\\W)', doc.lower()) if t.strip())))).join(self._lexicon_df).dropna().groupby('cat').sum()
        return text_df

    def get_definitions(self):
        """
        These definitions are from http://apmc.newmdsx.com/CATA/block3/General%20Inquirer%20Categories.txt

        :return: dict
        """
        return {'Positiv': '1,915 words of positive outlook. (It does not contain words for yes, which has been made a separate category of 20 entries.)', 'Negativ': '2,291 words of negative outlook (not including the separate category no in the sense of refusal).', 'Pstv': '1045 positive words, an earlier version of Positiv.', 'Affil': 'A subset of 557 Pstv words are also tagged for indicating affiliation or supportiveness.', 'Ngtv': '1160 negative words, an earlier version of Negativ.', 'Hostile': 'A subset of Ngtv 833 words are also tagged Hostile for words indicating an attitude or concern with hostility or aggressiveness.', 'Strong': '1902 words implying strength.', 'Power': 'A subset of 689 Strong words indicating a concern with power, control or authority.', 'Weak': '755 words implying weakness.', 'Submit': 'A subset of 284 Weak words connoting submission to authority or power, dependence on others, vulnerability to others, or withdrawal.', 'Active': '2045 words implying an active orientation.', 'Passive': '911 words indicating a passive orientation', 'Pleasur': '168 words indicating the enjoyment of a feeling, including words indicating confidence, interest and commitment.', 'Pain': '254 words indicating suffering, lack of confidence, or commitment.', 'Feel': '49 words describing particular feelings, including gratitude, apathy, and optimism, not those of pain or pleasure.', 'Arousal': '166 words indicating excitation, aside from pleasures or pains, but including arousal of affiliation and hostility.', 'EMOT': '311 words related to emotion that are used as a disambiguation category, but also available for general use.', 'Virtue': '719 words indicating an assessment of moral approval or good fortune, especially from the perspective of middle-class society.', 'Vice': '685 words indicating an assessment of moral disapproval or misfortune.', 'Ovrst': '"Overstated", 696 words indicating emphasis in realms of speed, frequency, causality, inclusiveness, quantity or quasi-quantity, accuracy, validity, scope, size, clarity, exceptionality, intensity, likelihood, certainty and extremity.', 'Undrst': '"Understated", 319 words indicating de-emphasis and caution in these realms.', 'Academ': '153 words relating to academic, intellectual or educational matters, including the names of major fields of study.', 'Doctrin': '217 words referring to organized systems of belief or knowledge, including those of applied knowledge, mystical beliefs, and arts that academics study.', 'Econ@': '510 words of an economic, commercial, industrial, or business orientation, including roles, collectivities, acts, abstract ideas, and symbols, including references to money. Includes names of common commodities in business.', 'Exch': '60 words concerned with buying, selling and trading.', 'ECON': '502 words (269 in common with Econ@) that is used by the General Inquirer in disambiguating.', 'Exprsv': '205 words associated with the arts, sports, and self-expression.', 'Legal': '192 words relating to legal, judicial, or police matters.', 'Milit': '88 words relating to military matters.', 'Polit@': '263 words having a clear political character, including political roles, collectivities, acts, ideas, ideologies, and symbols.', 'POLIT': 'broader category than Polit@ of 507 words that is used in disambiguation.', 'Relig': '103 words pertaining to religious, metaphysical, supernatural or relevant philosophical matters.', 'Role': '569 words referring to identifiable and standardized individual human behavior patterns, as used by sociologists.', 'COLL': '191 words referring to all human collectivities (not animal). Used in disambiguation.', 'Work': '261 words for socially defined ways for doing work.', 'Ritual': '134 words for non-work social rituals.', 'SocRel': '577 words for socially-defined interpersonal processes (formerly called "IntRel", for interpersonal relations).', 'Race': '15 words (with important use of words senses) referring to racial or ethnic characteristics.', 'Kin@': '50 terms denoting kinship.', 'MALE': '56 words referring to men and social roles associated with men. (Also used as a marker in disambiguation)', 'Female': '43 words referring to women and social roles associated with women.', 'HU': '795 general references to humans, including roles', 'ANI': '72 references to animals, fish, birds, and insects, including their collectivities.', 'Social': '111 words for created locations that typically provide for social interaction and occupy limited space', 'Region': '61 words', 'Route': '23 words', 'Aquatic': '20 words', 'Land': '63 words for places occurring in nature, such as desert or beach', 'Sky': '34 words for all aerial conditions, natural vapors and objects in outer space', 'Object': 'category with 661 words subdivided into', 'Tool': '318 word for tools', 'Food': '80 words for food', 'Vehicle': '39 words for vehcile', 'BldgPt': '46 words for buildings, rooms in buildings, and other building parts', 'ComnObj': '104 words for the tools of communication', 'NatObj': '61 words for natural objects including plants, minerals and other objects occurring in nature other than people or animals)', 'BodyPt': 'a list of 80 parts of the body', 'ComForm': '895 words relating to the form, format or media of the communication transaction.', 'COM': '412 communications words used in disambiguation.', 'Say': '4 words for say and tell.', 'Need': '76 words related to the expression of need or intent.', 'Goal': '53 names of end-states towards which muscular or mental striving is directed.', 'Try': '70 words indicating activities taken to reach a goal, but not including words indicating that the goals have been achieved.', 'Means': '244 words denoting objects, acts or methods utilized in attaining goals. Only 16 words overlap with Lasswell dictionary 77-word category MeansLw.', 'Persist': '64 words indicating "stick to it" and endurance.', 'Complet': '81 words indicating that goals have been achieved, apart from whether the action may continue. The termination of action is indicated by the category Finish.', 'Fail': '137 words indicating that goals have not been achieved.', 'NatrPro': '217 words for processes found in nature, birth to death.', 'Begin': '56 words', 'Vary': '98 words indicating change without connotation of increase, decrease, beginning or ending', 'Increas': 'increase, 111 words', 'Decreas': 'decrease, 82 words', 'Finish': '87 words Terminiation action of completion', 'Stay': '25 movement words relating to staying', 'Rise': '25 movement words relating to rising', 'Exert': '194 movement words relating to exertion', 'Fetch': '79 words, includes carrying', 'Travel': '209 words for all physical movement and travel from one place to another in a horizontal plane', 'Fall': '42 words referring to falling movement', 'Think': '81 words referring to the presence or absence of rational thought processes.', 'Know': '348 words indicating awareness or unawareness, certainty or uncertainty, similarity or difference, generality or specificity, importance or unimportance, presence or absence, as well as components of mental classes, concepts or ideas.', 'Causal': '112 words denoting presumption that occurrence of one phenomenon is necessarily preceded, accompanied or followed by the occurrence of another.', 'Ought': '26 words indicating moral imperative.', 'Perceiv': '192 words referring to the perceptual process of recognizing or identifying something by means of the senses.', 'Compare': '21 words of comparison.', 'Eval@': '205 words which imply judgment and evaluation, whether positive or negative, including means-ends judgments.', 'Solve': '189 words (mostly verbs) referring to the mental processes associated with problem solving.', 'Abs@': '185 words reflecting tendency to use abstract vocabulary. There is also an ABS category (276 words) used as a marker.', 'Quality': '344 words indicating qualities or degrees of qualities which can be detected or measured by the human senses. Virtues and vices are separate.', 'Quan': '314 words indicating the assessment of quantity, including the use of numbers. Numbers are also identified by the NUMBcategory (51 words) which in turn divides into ORDof 15 ordinal words and CARDfor 36 cardinal words.', 'FREQ': '46 words indicating an assessment of frequency or pattern of recurrences, as well as words indicating an assessment of nonoccurrence or low frequency. (Also used in disambiguation)', 'DIST': '19 words referring to distance and its measures. (Used in disambiguation)', 'Time@': '273 words indicating a time consciousness, including when events take place and time taken in an action. Includes velocity words as well. There is also a more restrictive TIME category (75 words) used as a marker for disambiguation.', 'Space': '302 words indicating a consciousness of location in space and spatial relationships. There are also two more specialized marker categories for disambiguation POS (35 words for position) and DIM (49 words for dimension).', 'COLOR': '21 words of color, used in disambiguation.', 'Self': '7 pronouns referring to the singular self', 'Our': '6 pronouns referring to the inclusive self ("we", etc.)', 'You': '9 pronouns indicating another person is being addressed directly.', 'Yes': '20 words directly indicating agreement, including word senses "of course", "to say the least", "all right".', 'No': '7 words directly indicating disagreement, with the word "no" itself disambiguated to separately identify absence or negation.', 'Negate': '217 words that refer to reversal or negation, including about 20 "dis" words, 40 "in" words, and 100 "un" words, as well as several senses of the word "no" itself; generally signals a downside view.', 'Intrj': '42 words and includes exclamations as well as casual and slang references, words categorized "yes" and "no" such as "amen" or "nope", as well as other words like "damn" and "farewell".', 'IAV': '1947 verbs giving an interpretative explanation of an action, such as "encourage, mislead, flatter".', 'DAV': '540 straight descriptive verbs of an action or feature of an action, such as "run, walk, write, read".', 'SV': '102 state verbs describing mental or emotional states. usually detached from specific observable events, such as "love, trust, abhor".', 'IPadj': '117 adjectives referring to relations between people, such as "unkind, aloof, supportive".', 'IndAdj': '637 adjectives describing people apart from their relations to one another, such as "thrifty, restless"', 'PowGain': 'Power Gain, 65 words about power increasing', 'PowLoss': 'Power Loss, 109 words of power decreasing.', 'PowEnds': 'Power Ends, 30 words about the goals of the power process.', 'PowAren': 'Power Arenas, 53 words referring to political places and environments except nation-states.', 'PowCon': 'Power conflict, 228 words for ways of conflicting.', 'PowCoop': 'Power cooperation, 118 words for ways of cooperating', 'PowAuPt': 'Power authoritative participants, 134 words for individual and collective actors in power process', 'PowPt': 'Power ordinary participants, 81 words for non-authoritative actors (such as followers) in the power process.', 'PowDoct': 'Power doctrine, 42 words for recognized ideas about power relations and practices.', 'PowAuth': 'Authoritative power, 79 words concerned with a tools or forms of invoking formal power.', 'PowOth': 'Residual category of 332 power words not in other subcategories', 'PowTot': '1,266 words for the whole domain', 'RcEthic': 'Ethics, 151 words of values concerning the social order.', 'RcRelig': 'Religion, 83 words that invoke transcendental, mystical or supernatural grounds for rectitude.', 'RcGain': 'Rectitude gain, 30 words such as worship and forgiveness.', 'RcLoss': 'Rectitude loss, 12 words such as sin and denounce.', 'RcEnds': 'Rectitude ends, 33 words including heaven and the high-frequency word "ought".', 'RcTot': 'Rectitude total, 310 words for the whole domain.', 'RspGain': '26 words for the garnering of respect, such as congratulations', 'RspLoss': '38 words for the losing of respect, such as shame.', 'RspOth': '182 words regarding respect that are neither gain nor loss', 'RspTot': '245 words in the domain.', 'AffGain': '35 words for reaping affect.', 'AffLoss': '11 words for affect loss and indifference', 'AffPt': 'Affect participant, 55 words for friends and family.', 'AffOth': '96 affect words not in other categories', 'AffTot': '196 words in the affect domain', 'WltPt': 'Wealth participant, 52 words for various roles in business and commerce.', 'WltTran': 'Wealth transaction, 53 words for pursuit of wealth, such as buying and selling.', 'WltOth': '271 wealth-related words not in the above, including economic domains and commodities.', 'WltTot': '378 words in wealth domain.', 'WlbGain': '37 various words related to a gain in well being.', 'WlbLoss': '60 words related to a loss in a state of well being, including being upset.', 'WlbPhys': '226 words connoting the physical aspects of well being, including its absence.', 'WlbPsyc': '139 words connoting the psychological aspects of well being, including its absence.', 'WlbPt': '27 roles that evoke a concern for well-being, including infants, doctors, and vacationers.', 'WlbTot': '487 words in well-being domain.', 'EnlGain': 'Enlightenment gain, 146 words likely to reflect a gain in enlightenment through thought, education, etc.', 'EnlLoss': 'Enlightenment loss, 27 words reflecting misunderstanding, being misguided, or oversimplified.', 'EnlEnds': 'Enlightenment ends, 18 words "denoting pursuit of intrinsic enlightenment ideas."', 'EnlPt': 'Enlightenment participant, 61 words referring to roles in the secular enlightenment sphere.', 'EnlOth': '585 other enlightenment words', 'EnlTot': 'total of about 835 words', 'SklAsth': 'Skill aesthetic, 35 words mostly of the arts', 'SklPt': 'Skill participant, 64 words mainly about trades and professions.', 'SklOth': '158 other skill-related words', 'SklTot': '257 skill words in all.', 'TrnGain': 'Transaction gain, 129 general words of accomplishment', 'TrnLoss': 'Transaction loss, 113 general words of not accomplishing, but having setbacks instead.', 'TranLw': '334 words of transaction or exchange in a broad sense, but not necessarily of gain or loss.', 'MeansLw': 'The Lasswell Means category, 78 general words referring to means and utility or lack of same. Overlaps little with Means category.', 'EndsLw': '270 words of desired or undesired ends or goals.', 'ArenaLw': '34 words for settings, other than power related arenas in PowAren.', 'PtLw': 'A list of 68 actors not otherwise defined by the dictionary.', 'Nation': 'A list of 169 nations, which needs updating.', 'Anomie': '30 words that usually show "a negation of value preference", nihilism, disappointment and futility.', 'NegAff': '193 words of negative affect "denoting negative feelings and emotional rejection.', 'PosAff': '126 words of positive affect "denoting positive feelings, acceptance, appreciation and emotional support."', 'SureLw': '175 words indicating "a feeling of sureness, certainty and firmness."', 'If': '132 words "denoting feelings of uncertainty, doubt and vagueness."', 'NotLw': '25 words "that show the denial of one sort or another. "'}

    def get_doc_metadata(self, doc, prefix=''):
        topic_counter = Counter()
        if version_info[0] >= 3:
            doc = str(doc)
        for topic_category, score in self._analyze(doc).to_dict()[0].items():
            topic_counter[prefix + topic_category] = int(score)
        return topic_counter

    def has_metadata_term_list(self):
        return True

    def get_top_model_term_lists(self):
        return self._lexicon_df.reset_index().groupby('cat')['term'].apply(list).to_dict()

def get_doc_metadata(self, doc, prefix=''):
    topic_counter = Counter()
    if version_info[0] >= 3:
        doc = str(doc)
    for topic_category, score in self._analyze(doc).to_dict()[0].items():
        topic_counter[prefix + topic_category] = int(score)
    return topic_counter

class FeatsFromSpacyDoc(object):

    def __init__(self, use_lemmas=False, entity_types_to_censor=set(), tag_types_to_censor=set(), strip_final_period=False):
        """
		Parameters
		----------
		use_lemmas : bool, optional
			False by default
		entity_types_to_censor : set, optional
			empty by default
		tag_types_to_censor : set, optional
			empty by default
		strip_final_period : bool, optional
			if you know that spacy is going to mess up parsing, strip final period.  default no.
		"""
        self._use_lemmas = use_lemmas
        assert type(entity_types_to_censor) == set
        assert type(tag_types_to_censor) == set
        self._entity_types_to_censor = entity_types_to_censor
        self._pos_types_to_censor = {}
        self._tag_types_to_censor = tag_types_to_censor
        self._strip_final_period = strip_final_period
        self._ignore_censored_types = False

    def _post_process_term(self, term):
        if self._strip_final_period and (term.strip().endswith('.') or term.strip().endswith(',')):
            term = term.strip()[:-1]
        return term

    def get_doc_metadata(self, doc):
        return Counter()

    def get_row_metadata(self, doc, row: pd.Series):
        return Counter()

    def ignore_censored_types(self):
        self._ignore_censored_types = True
        return self

    def censor_pos_types(self, pos_types):
        assert type(pos_types) == set
        self._pos_types_to_censor = pos_types
        return self

    def censor_entity_types(self, entity_types):
        assert type(entity_types) == set
        self._entity_types_to_censor = entity_types
        return self

    def censor_tag_types(self, tag_types):
        assert type(tag_types) == set
        self._tag_types_to_censor = tag_types
        return self

    def get_feats(self, doc):
        """
		Parameters
		----------
		doc, Spacy Docs

		Returns
		-------
		Counter (unigram, bigram) -> count
		"""
        ngram_counter = Counter()
        for sent in doc.sents:
            unigrams = self._get_unigram_feats(sent)
            bigrams = self._get_bigram_feats(unigrams)
            ngram_counter += Counter(chain(unigrams, bigrams))
        return ngram_counter

    def _get_bigram_feats(self, unigrams):
        if len(unigrams) > 1:
            bigrams = map(' '.join, zip(unigrams[:-1], unigrams[1:]))
        else:
            bigrams = []
        return bigrams

    def _get_unigram_feats(self, sent):
        unigrams = []
        for tok in sent:
            if tok.pos_ not in ('PUNCT', 'SPACE', 'X'):
                if tok.ent_type_ in self._entity_types_to_censor:
                    if not self._ignore_censored_types:
                        unigrams.append('_' + tok.ent_type_)
                elif tok.tag_ in self._tag_types_to_censor:
                    if not self._ignore_censored_types:
                        unigrams.append(tok.tag_)
                elif tok.pos_ in self._pos_types_to_censor:
                    if not self._ignore_censored_types:
                        unigrams.append(tok.pos_)
                elif self._use_lemmas and tok.lemma_.strip():
                    unigrams.append(self._post_process_term(tok.lemma_.strip().lower()))
                elif tok.lower_.strip():
                    unigrams.append(self._post_process_term(tok.lower_.strip()))
        return unigrams

    def has_metadata_term_list(self):
        """
		Returns True if there is a meta data term list associated with object, False if not.

		Returns
		-------
		bool
		"""
        return False

    def get_top_model_term_lists(self):
        raise Exception('No topic models associated with these features.')

def get_doc_metadata(self, doc):
    return Counter()

def get_row_metadata(self, doc, row: pd.Series):
    return Counter()

def get_feats(self, doc):
    """
		Parameters
		----------
		doc, Spacy Docs

		Returns
		-------
		Counter (unigram, bigram) -> count
		"""
    ngram_counter = Counter()
    for sent in doc.sents:
        unigrams = self._get_unigram_feats(sent)
        bigrams = self._get_bigram_feats(unigrams)
        ngram_counter += Counter(chain(unigrams, bigrams))
    return ngram_counter

class TokenFeatAndOffsetGetter(FeatAndOffsetGetter):

    def get_term_offsets(self, doc):
        return []

    def get_metadata_offsets(self, doc):
        offset_tokens = {}
        for sent in doc.sents:
            for tok in sent:
                token_stats = offset_tokens.setdefault(tok.lower_, [0, []])
                token_stats[0] += 1
                token_stats[1].append((tok.idx, tok.idx + len(tok.lower_)))
        return offset_tokens.items()

def get_metadata_offsets(self, doc):
    offset_tokens = {}
    for sent in doc.sents:
        for tok in sent:
            token_stats = offset_tokens.setdefault(tok.lower_, [0, []])
            token_stats[0] += 1
            token_stats[1].append((tok.idx, tok.idx + len(tok.lower_)))
    return offset_tokens.items()

class FlexibleNGramFeatures(FeatAndOffsetGetter, FlexibleNGramFeaturesBase):

    def get_term_offsets(self, doc):
        return []

    def get_metadata_offsets(self, doc) -> List[Tuple[str, List[Tuple[int, List[Tuple[int, int]]]]]]:
        offset_tokens = self._doc_to_feature_representation(doc)
        return list(offset_tokens.items())

def get_metadata_offsets(self, doc) -> List[Tuple[str, List[Tuple[int, List[Tuple[int, int]]]]]]:
    offset_tokens = self._doc_to_feature_representation(doc)
    return list(offset_tokens.items())

class FlexibleNGrams(FeatsFromSpacyDoc, FlexibleNGramFeaturesBase):

    def __init__(self, ngram_sizes: Optional[List[int]]=None, exclude_ngram_filter: Optional[Callable]=None, text_from_token: Optional[Callable]=None, validate_token: Optional[Callable]=None, exclude_sentence_filter: Optional[Callable[[str], bool]]=None):
        FeatsFromSpacyDoc.__init__(self)
        FlexibleNGramFeaturesBase.__init__(self, exclude_ngram_filter, ngram_sizes, text_from_token, validate_token, whitespace_substitute=None, exclude_sentence_filter=exclude_sentence_filter)

    def get_feats(self, doc):
        return self._doc_to_feature_representation(doc)

    def _add_ngram_to_token_stats(self, ngram, offset_tokens):
        toktext = ' '.join((self.text_from_token(tok) for tok in ngram))
        offset_tokens.setdefault(toktext, 0)
        offset_tokens[toktext] += 1

def get_feats(self, doc):
    return self._doc_to_feature_representation(doc)

def make_unique(lst, sep='-'):
    seen = Counter()
    out = []
    counts = Counter(lst)
    for el in lst:
        out.append(el + ('' if counts[el] == 1 else sep + str(seen[el] + 1)))
        seen[el] += 1
    return out

class VizDataAdapter:

    def __init__(self, words_dict):
        self._word_dict = words_dict

    @property
    def word_dict(self):
        return self._word_dict

    @word_dict.setter
    def word_dict(self, val):
        self._word_dict = val

    @word_dict.deleter
    def word_dict(self):
        del self._word_dict

    def to_javascript(self, function_name='getDataAndInfo'):
        return 'function ' + function_name + '() { return' + self.to_json() + '; }'

    def to_json(self):
        word_dict_json = json.dumps(self.word_dict, cls=MyEncoder)
        return word_dict_json

def to_json(self):
    word_dict_json = json.dumps(self.word_dict, cls=MyEncoder)
    return word_dict_json

class ScatterplotStructure(object):

    def __init__(self, visualization_data, width_in_pixels=None, height_in_pixels=None, max_snippets=None, color=None, grey_zero_scores=False, sort_by_dist=True, reverse_sort_scores_for_not_category=True, use_full_doc=False, asian_mode=False, match_full_line=False, use_non_text_features=False, show_characteristic=True, word_vec_use_p_vals=False, max_p_val=0.1, save_svg_button=False, p_value_colors=False, x_label=None, y_label=None, full_data=None, show_top_terms=True, show_neutral=False, get_tooltip_content=None, x_axis_values=None, y_axis_values=None, color_func=None, show_axes=True, horizontal_line_y_position=None, vertical_line_x_position=None, show_extra=False, do_censor_points=True, center_label_over_points=False, x_axis_labels=None, y_axis_labels=None, topic_model_preview_size=10, vertical_lines=None, unified_context=False, show_category_headings=True, highlight_selected_category=False, show_cross_axes=True, div_name=DEFAULT_DIV_ID, alternative_term_func=None, include_all_contexts=False, show_axes_and_cross_hairs=False, x_axis_values_format=None, y_axis_values_format=None, max_overlapping=-1, show_corpus_stats=True, sort_doc_labels_by_name=False, always_jump=True, show_diagonal=False, enable_term_category_description=True, use_global_scale=False, get_custom_term_html=None, header_names=None, header_sorting_algos=None, ignore_categories=False, background_labels=None, label_priority_column=None, text_color_column=None, suppress_text_column=None, censor_point_column=None, background_color=None, right_order_column=None, subword_encoding=None, top_terms_length=14, top_terms_left_buffer=0, get_column_header_html=None, term_word='Term', show_term_etc=True, sort_contexts_by_meta=False, suppress_circles=False, text_size_column=None, category_colors=None, document_word='document', document_word_plural=None, category_order=None, include_gradient: bool=False, left_gradient_term: Optional[str]=None, middle_gradient_term: Optional[str]=None, right_gradient_term: Optional[str]=None, gradient_text_color: Optional[str]=None, gradient_colors: Optional[List[str]]=None, category_term_score_scaler: Optional[str]=None, show_chart=False):
        """

        Parameters
        ----------
        visualization_data : VizDataAdapter
            From ScatterChart or a descendant
        width_in_pixels : int, optional
            width of viz in pixels, if None, default to 1000
        height_in_pixels : int, optional
            height of viz in pixels, if None, default to 600
        max_snippets : int, optional
            max snippets to snow when term is clicked, Defaults to show all
        color : str, optional
          d3 color scheme
        grey_zero_scores : bool, optional
          If True, color points with zero-scores a light shade of grey.  False by default.
        sort_by_dist : bool, optional
            sort by distance or score, default True
        reverse_sort_scores_for_not_category : bool, optional
            If using a custom score, score the not-category class by
            lowest-score-as-most-predictive. Turn this off for word vectory
            or topic similarity. Default True.
        use_full_doc : bool, optional
            use full document instead of sentence in snippeting
        use_non_text_features : bool, default False
            Show non-bag-of-words features (e.g., Empath) instaed of text.  False by default.
        show_characteristic: bool, default True
            Show characteristic terms on the far left-hand side of the visualization
        word_vec_use_p_vals: bool, default False
            Use category-associated p-values to determine which terms to give word
            vec scores.
        max_p_val : float, default = 0.1
            Max p-val to use find set of terms for similarity calculation, if
            word_vec_use_p_vals is True.
        save_svg_button : bool, default False
            Add a save as SVG button to the page.
        p_value_colors : bool, default False
          Color points differently if p val is above 1-max_p_val, below max_p_val, or
           in between.
        x_label : str, default None
            If present, use as the x-axis label
        y_label : str, default None
            If present, use as the y-axis label
        full_data : str, default None
            Data used to create chart. By default "getDataAndInfo()".
        show_top_terms : bool, default True
            Show the top terms sidebar
        show_neutral : bool, default False
            Show a third column for matches in neutral documents
        get_tooltip_content : str, default None
            Javascript function to control content of tooltip.  Function takes a parameter
            which is a dictionary entry produced by `ScatterChartExplorer.to_dict` and
            returns a string.
        x_axis_values : list, default None
            Numeric value-labels to show on x-axis which correspond to original x-values.
        y_axis_values : list, default None
            Numeric Value-labels to show on y-axis which correspond to original y-values.
        color_func : str, default None
            Javascript function to control color of a point.  Function takes a parameter
            which is a dictionary entry produced by `ScatterChartExplorer.to_dict` and
            returns a string.
        show_axes : bool, default True
            Show x and y axes
        horizontal_line_y_position : float, default None
            If x and y axes markers are shown, the position of the horizontal axis marker
        vertical_line_x_position : float, default None
            If x and y axes markers are shown, the position of the vertical axis marker
        show_extra : bool, default False
            Show extra fourth column
        do_censor_points  : bool, default True
            Don't label over dots
        center_label_over_points : bool, default False
            Only put labels centered over point
        x_axis_labels: list, default None
            List of string value-labels to show at evenly spaced intervals on the x-axis.
            Low, medium, high are defaults. This relies on d3's ticks function, which can
            behave unpredictable. Caveat usor.
        y_axis_labels : list, default None
            List of string value-labels to show at evenly spaced intervals on the y-axis.
            Low, medium, high are defaults.  This relies on d3's ticks function, which can
            behave unpredictable. Caveat usor.
        topic_model_preview_size : int, default 10
            If topic models are being visualized, show the first topic_model_preview_size topics
            in a preview.
        vertical_lines: list, default None
            List of scaled points along the x-axis to draw horizontal lines
        unified_context: bool, default False
            Display all context in a single column.
        show_category_headings: bool, default True
            If unified_context, should we show the category headings?
        highlight_selected_category: bool, default False
            Highlight selected category in unified view
        show_cross_axes: bool, default True
            If show_axes is False, do we show cross-axes?
        div_name: str, default DEFAULT_DIV_ID
            Div which holds scatterplot
        alternative_term_func: str, default None
            Javascript function which take a term JSON object and returns a bool.  If the return value is true,
            execute standard term click pipeline. Ex.: `'(function(termDict) {return true;})'`.
        include_all_contexts: bool, default False
            Include all contexts, even non-matching ones, in interface
        show_axes_and_cross_hairs: bool, default False
            Show both cross-axes and peripheral scales.
        x_axis_values_format: str, default None
            d3 format string for x-axis values (see https://github.com/d3/d3-format)
        y_axis_values_format: str, default None
            d3 format string for y-axis values (see https://github.com/d3/d3-format)
        max_overlapping: int, default -1
            Maximum number of overlapping terms to output.  Show all if -1 (default)
        show_corpus_stats: bool, default True
            Populate corpus stats div
        sort_doc_labels_by_name: bool, default False
            If unified document labels, sort the labels by name instead of value.
        always_jump: bool, default True
            Always jump to term contexts if a term is clicked.
        show_diagonal: bool, default False
            Show a diagonal line from the lower-left to the upper-right of the chart
        use_global_scale: bool, default False
            Use the same scaling for the x and y axis. Without this show_diagonal may not
            make sense.
        enable_term_category_description: bool, default True
            List term/metadata statistics under category
        get_custom_term_html: str, default None
            Javascript function which takes term info and outputs custom term HTML
        header_names: Dict[str, str], default None
            Dictionary giving names of term lists shown to the right of the plot. Valid keys are
            upper, lower and right.
        header_sorting_algos: Dict[str, str], default None
            Dictionary giving javascript sorting algorithms for panes. Valid keys are upper, lower
            and right. Value is a JS function which takes the "data" object.
        ignore_categories: bool, default False
            Signals plot should ignore category names.
        background_labels: List[Dict]: default None
            List of [{"Text": "Label", "X": xpos, "Y": ypos}, ...] to be background labels on plot
        label_priority_column : str, default None
            Column in term_metadata_df; larger values in the column indicate a term should be labeled first
        text_color_column: str, default None
            Column in term_metadata_df which supplies term colors
        suppress_text_column: str, default None
            Column in term_metadata_df which is of boolean value. Indicates if a term should be labeled.
        censor_point_column : str, default None
            Should we prevent labels from being drawn over a point?
        right_order_column : str, default None
            Order for right column ("characteristic" by default); largest first
        subword_encoding : str, default None
            Type of subword encoding to use, None if none, currently supports "RoBERTa"
        background_color: str, default None
            Color to set document.body's background
        sentence_piece: bool, default False
            Use sentence piece conventions from to search for terms in JS
        top_terms_length: int, default 14
            Number of top terms to show for left-hand side lists
        top_terms_lefft_buffer: int, default 0
            Number of pixels left to shift top terms list
        get_column_header_html : str, default None
            Javascript function to return html over each column. Matches header
            (Column Name, occurrences per 25k, occs, # occs * 1000/num docs, term info)
        term_word: str, default "Term"
            Word for term in visualization
        show_term_etc: bool, default True
            Shows contents of etc structure after clicking on term
        sort_contexts_by_meta : bool, default False
            Sort contexts by meta instead of match strength
        suppress_circles : bool, default False
            Label terms over circles and hide circles
        text_size_column : str, default None
            Font size of point column name. None of not exists
        category_colors : optional[dict], default None
            Dict mapping cateogry to #xxxxxx color
        document_word : str, default "document"
        document_word_plural : optional[str], default None -> document word + 's'
        category_order : optional[list[str]]
            order categories should be shown
        include_gradient : bool, False
            Include gradient at the top of the chart
        left_gradient_term : Optional[str], None by default
            Text of left gradient label. category_name by default
        middle_gradient_term : Optional[str], None by default
            Text of middle grad label. If None, not shown.
        right_gradient_term: Optional[str], None by default
            Text of right gradient label, not_category_name by default
        gradient_text_color: Optional[str], None by default
        category_term_score_scaler: Optional[str], None by default
            Javascript function which scales a set of categories scores to between 0 and 1
        show_chart : bool, default False
            Show line graph
        """
        self._visualization_data = visualization_data
        self._width_in_pixels = width_in_pixels if width_in_pixels is not None else 1000
        self._height_in_pixels = height_in_pixels if height_in_pixels is not None else 600
        self._max_snippets = max_snippets
        self._color = color
        self._sort_by_dist = sort_by_dist
        self._use_full_doc = use_full_doc
        self._asian_mode = asian_mode
        self._match_full_line = match_full_line
        self._grey_zero_scores = grey_zero_scores
        self._use_non_text_features = use_non_text_features
        self._show_characteristic = show_characteristic
        self._word_vec_use_p_vals = word_vec_use_p_vals
        self._max_p_val = max_p_val
        self._save_svg_button = save_svg_button
        self._reverse_sort_scores_for_not_category = reverse_sort_scores_for_not_category
        self._p_value_colors = p_value_colors
        self._x_label = x_label
        self._y_label = y_label
        self._full_data = full_data
        self._show_top_terms = show_top_terms
        self._show_neutral = show_neutral
        self._get_tooltip_content = get_tooltip_content
        self._x_axis_values = x_axis_values
        self._y_axis_values = y_axis_values
        self._x_axis_labels = x_axis_labels
        self._y_axis_labels = y_axis_labels
        self._color_func = color_func
        self._show_axes = show_axes
        self._horizontal_line_y_position = horizontal_line_y_position
        self._vertical_line_x_position = vertical_line_x_position
        self._show_extra = show_extra
        self._do_censor_points = do_censor_points
        self._center_label_over_points = center_label_over_points
        self._topic_model_preview_size = topic_model_preview_size
        self._vertical_lines = vertical_lines
        self._unified_context = unified_context
        self._show_category_headings = show_category_headings
        self._highlight_selected_category = highlight_selected_category
        self._show_cross_axes = show_cross_axes
        self._div_name = div_name
        self._alternative_term_func = alternative_term_func
        self._include_all_contexts = include_all_contexts
        self._show_axes_and_cross_hairs = show_axes_and_cross_hairs
        self._x_axis_values_format = x_axis_values_format
        self._y_axis_values_format = y_axis_values_format
        self._max_overlapping = max_overlapping
        self._show_corpus_stats = show_corpus_stats
        self._sort_doc_labels_by_name = sort_doc_labels_by_name
        self._always_jump = always_jump
        self._show_diagonal = show_diagonal
        self._use_global_scale = use_global_scale
        self._enable_term_category_description = enable_term_category_description
        self._get_custom_term_html = get_custom_term_html
        self._header_names = header_names
        self._header_sorting_algos = header_sorting_algos
        self._ignore_categories = ignore_categories
        self._background_labels = background_labels
        self._label_priority_column = label_priority_column
        self._text_color_column = text_color_column
        self._suppress_label_column = suppress_text_column
        self._censor_point_column = censor_point_column
        self._right_order_column = right_order_column
        self._background_color = background_color
        self._subword_encoding = subword_encoding
        self._top_terms_length = top_terms_length
        self._top_terms_left_buffer = top_terms_left_buffer
        self._get_column_header_html = get_column_header_html
        self._term_word = term_word
        self._show_term_etc = show_term_etc
        self._sort_contexts_by_meta = sort_contexts_by_meta
        self._suppress_circles = suppress_circles
        self._text_size_column = text_size_column
        self._category_colors = category_colors
        self._document_word = document_word
        self._document_word_plural = document_word_plural if document_word_plural is not None else document_word + 's'
        self._category_order = category_order
        self._show_chart = show_chart
        self._include_gradient = include_gradient
        self._left_gradient_term = left_gradient_term
        self._middle_gradient_term = middle_gradient_term
        self._right_gradient_term = right_gradient_term
        self._gradient_colors = gradient_colors
        self._gradient_text_color = gradient_text_color
        self._category_term_score_scaler = category_term_score_scaler

    def call_build_visualization_in_javascript(self):

        def js_default_value(x, default='undefined'):
            return default if x is None else str(x)

        def js_default_string(x, default_string=None):
            if x is not None:
                return json.dumps(str(x))
            if default_string is None:
                return 'undefined'
            return json.dumps(default_string)

        def js_default_value_to_null(x):
            return 'null' if x is None else str(x)

        def json_or_null(x):
            return 'null' if x is None else json.dumps(x)

        def json_or_null_or_str(x):
            if x is None:
                return 'null'
            try:
                return json.dumps(x)
            except TypeError:
                return str(x)

        def js_bool(x):
            return 'true' if x else 'false'

        def js_float(x):
            return str(float(x))

        def js_int(x):
            return str(int(x))

        def js_default_full_data(full_data):
            return full_data if full_data is not None else 'getDataAndInfo()'

        def json_with_jsvalue_or_null(x):
            if x is None:
                return 'null'
            to_ret = '{'
            first = True
            for key, val in sorted(x.items()):
                if not first:
                    to_ret += ', '
                to_ret += '"%s": %s' % (key, val)
                first = False
            to_ret += '}'
            return to_ret
        arguments = [js_default_value(self._width_in_pixels), js_default_value(self._height_in_pixels), js_default_value_to_null(self._max_snippets), js_default_value_to_null(self._color), js_bool(self._sort_by_dist), js_bool(self._use_full_doc), js_bool(self._grey_zero_scores), js_bool(self._asian_mode), js_bool(self._use_non_text_features), js_bool(self._show_characteristic), js_bool(self._word_vec_use_p_vals), js_bool(self._save_svg_button), js_bool(self._reverse_sort_scores_for_not_category), js_float(self._max_p_val), js_bool(self._p_value_colors), js_default_string(self._x_label), js_default_string(self._y_label), js_default_full_data(self._full_data), js_bool(self._show_top_terms), js_bool(self._show_neutral), js_default_value_to_null(self._get_tooltip_content), js_default_value_to_null(self._x_axis_values), js_default_value_to_null(self._y_axis_values), js_default_value_to_null(self._color_func), js_bool(self._show_axes), js_bool(self._show_extra), js_bool(self._do_censor_points), js_bool(self._center_label_over_points), json_or_null(self._x_axis_labels), json_or_null(self._y_axis_labels), js_default_value(self._topic_model_preview_size), json_or_null(self._vertical_lines), js_default_value_to_null(self._horizontal_line_y_position), js_default_value_to_null(self._vertical_line_x_position), js_bool(self._unified_context), js_bool(self._show_category_headings), js_bool(self._show_cross_axes), js_default_string(self._div_name), js_default_value_to_null(self._alternative_term_func), js_bool(self._include_all_contexts), js_bool(self._show_axes_and_cross_hairs), js_default_string(self._x_axis_values_format, DEFAULT_D3_AXIS_VALUE_FORMAT), js_default_string(self._y_axis_values_format, DEFAULT_D3_AXIS_VALUE_FORMAT), js_bool(self._match_full_line), js_int(self._max_overlapping), js_bool(self._show_corpus_stats), js_bool(self._sort_doc_labels_by_name), js_bool(self._always_jump), js_bool(self._highlight_selected_category), js_bool(self._show_diagonal), js_bool(self._use_global_scale), js_bool(self._enable_term_category_description), js_default_value_to_null(self._get_custom_term_html), json_or_null(self._header_names), json_with_jsvalue_or_null(self._header_sorting_algos), js_bool(self._ignore_categories), json_or_null(self._background_labels), js_default_string(self._label_priority_column), js_default_string(self._text_color_column), js_default_string(self._suppress_label_column), js_default_string(self._background_color), js_default_string(self._censor_point_column), js_default_string(self._right_order_column), js_default_string(self._subword_encoding), js_default_value(self._top_terms_length, '14'), js_default_value(self._top_terms_left_buffer, '0'), js_default_value_to_null(self._get_column_header_html), js_default_string(self._term_word), js_bool(self._show_term_etc), js_bool(self._sort_contexts_by_meta), js_bool(self._suppress_circles), js_default_string(self._text_size_column), json_or_null(self._category_colors), js_default_string(self._document_word), js_default_string(self._document_word_plural), json_or_null_or_str(self._category_order), js_bool(self._include_gradient), json_or_null(self._left_gradient_term), json_or_null(self._middle_gradient_term), json_or_null(self._right_gradient_term), json_or_null(self._gradient_text_color), json_or_null(self._gradient_colors), js_default_value_to_null(self._category_term_score_scaler), js_bool(self._show_chart)]
        return 'buildViz(' + ',\n'.join(arguments) + ');\n'

    def get_js_to_call_build_scatterplot(self, object_name='plotInterface'):
        return object_name + ' = ' + self.call_build_visualization_in_javascript()

    def get_js_to_call_build_scatterplot_with_a_function(self, object_name='plotInterface', function_name=None):
        if function_name is None:
            function_name = 'build' + object_name
        function_text = 'function ' + function_name + '() { return ' + self.call_build_visualization_in_javascript() + ';}'
        return function_text + '\n\n' + object_name + ' = ' + function_name + '();'

    def get_js_reset_function(self, values_to_set, functions_to_reset, reset_function_name='reset'):
        """

        :param functions_to_reset: List[str]
        :param values_to_set: List[str]
        :param reset_function_name: str, default = rest
        :return: str
        """
        return 'function ' + reset_function_name + '() {' + "document.querySelectorAll('.scattertext').forEach(element=>element.innerHTML=null);\n" + "document.querySelectorAll('#d3-div-1-corpus-stats').forEach(element=>element.innerHTML=null);\n" + ' '.join([value + ' = ' + function_name + '();' for value, function_name in zip(values_to_set, functions_to_reset)]) + '}'

def js_default_value(x, default='undefined'):
    return default if x is None else str(x)

def js_default_string(x, default_string=None):
    if x is not None:
        return json.dumps(str(x))
    if default_string is None:
        return 'undefined'
    return json.dumps(default_string)

def js_default_value_to_null(x):
    return 'null' if x is None else str(x)

def json_or_null(x):
    return 'null' if x is None else json.dumps(x)

def json_or_null_or_str(x):
    if x is None:
        return 'null'
    try:
        return json.dumps(x)
    except TypeError:
        return str(x)

def js_int(x):
    return str(int(x))

class BasicHTMLFromScatterplotStructure(object):

    def __init__(self, scatterplot_structure):
        """
        :param scatterplot_structure: ScatterplotStructure
        """
        self.scatterplot_structure = scatterplot_structure

    def to_html(self, protocol='http', d3_url=None, d3_scale_chromatic_url=None, html_base=None, search_input_id='searchInput', halo_colors: Optional[dict]=None):
        """
        Parameters
        ----------
        protocol : str
         'http' or 'https' for including external urls
        d3_url, str
          None by default.  The url (or path) of
          d3, to be inserted into <script src="..."/>
          By default, this is `DEFAULT_D3_URL` declared in `ScatterplotStructure`.
        d3_scale_chromatic_url : str
          None by default.
          URL of d3_scale_chromatic_url, to be inserted into <script src="..."/>
          By default, this is `DEFAULT_D3_SCALE_CHROMATIC` declared in `ScatterplotStructure`.
        html_base : str
            None by default.  HTML of semiotic square to be inserted above plot.
        search_input_id : str
            Id of search input. Default is 'searchInput'.
        halo_colors : Optional[Dict[str, str]]
            If None, defaults to HALO_COLORS. Maps halo position to background color
        Returns
        -------
        str, the html file representation

        """
        halo_colors = HALO_COLORS if halo_colors is None else halo_colors
        d3_url_struct = D3URLs(d3_url, d3_scale_chromatic_url)
        ExternalJSUtilts.ensure_valid_protocol(protocol)
        javascript_to_insert = '\n'.join([PackedDataUtils.full_content_of_javascript_files(), self.scatterplot_structure._visualization_data.to_javascript(), self.scatterplot_structure.get_js_to_call_build_scatterplot(), PackedDataUtils.javascript_post_build_viz(search_input_id, 'plotInterface')])
        html_template = PackedDataUtils.full_content_of_default_html_template() if html_base is None else self._format_html_base(html_base, halo_colors)
        html_content = HELLO + html_template.replace('<!-- INSERT SCRIPT -->', javascript_to_insert, 1).replace('<!-- INSERT SEARCH FORM -->', PackedDataUtils.full_content_of_default_search_form(search_input_id), 1).replace('<!--D3URL-->', d3_url_struct.get_d3_url(), 1).replace('<!--D3SCALECHROMATIC-->', d3_url_struct.get_d3_scale_chromatic_url())
        "\n        if html_base is not None:\n            html_file = html_file.replace('<!-- INSERT SEMIOTIC SQUARE -->',\n                                          html_base)\n        "
        extra_libs = ''
        if self.scatterplot_structure._save_svg_button:
            extra_libs = ''
        autocomplete_css = PackedDataUtils.full_content_of_default_autocomplete_css()
        html_content = html_content.replace('/***AUTOCOMPLETE CSS***/', autocomplete_css, 1).replace('<!-- EXTRA LIBS -->', extra_libs, 1).replace('http://', protocol + '://')
        return html_content

    def _format_html_base(self, html_base, halo_colors):
        height = self.scatterplot_structure._height_in_pixels
        cellheight, cellheightshort = cell_height_and_cell_height_short_from_height(height)
        html = html_base.replace('{width}', str(self.scatterplot_structure._width_in_pixels)).replace('{height}', str(height)).replace('{cellheight}', str(cellheight)).replace('{cellheightshort}', str(cellheightshort))
        for position, color in halo_colors.items():
            html = html.replace('{' + f'{position}_halo_color' + '}', color)
        return html

def _format_html_base(self, html_base, halo_colors):
    height = self.scatterplot_structure._height_in_pixels
    cellheight, cellheightshort = cell_height_and_cell_height_short_from_height(height)
    html = html_base.replace('{width}', str(self.scatterplot_structure._width_in_pixels)).replace('{height}', str(height)).replace('{cellheight}', str(cellheight)).replace('{cellheightshort}', str(cellheightshort))
    for position, color in halo_colors.items():
        html = html.replace('{' + f'{position}_halo_color' + '}', color)
    return html

def cell_height_and_cell_height_short_from_height(height: int) -> Tuple[int, int]:
    cellheight = int(height * (4.5 / 12))
    cellheightshort = height - 2 * cellheight
    return (cellheight, cellheightshort)

