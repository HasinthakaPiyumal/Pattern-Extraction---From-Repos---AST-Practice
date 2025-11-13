# Cluster 1

def get_log_scale_df(corpus, y_category, x_category):
    term_coord_df = corpus.get_term_freq_df('')
    coord_columns = []
    for category in [y_category, x_category]:
        col_name = category + '_coord'
        term_coord_df[col_name] = np.log(term_coord_df[category] + 1e-06) / np.log(2)
        coord_columns.append(col_name)
    min_offset = term_coord_df[coord_columns].min(axis=0).min()
    for coord_column in coord_columns:
        term_coord_df[coord_column] -= min_offset
    max_offset = term_coord_df[coord_columns].max(axis=0).max()
    for coord_column in coord_columns:
        term_coord_df[coord_column] /= max_offset
    return term_coord_df

def scale(ar):
    return (ar - ar.min()) / (ar.max() - ar.min())

class DocsAndLabelsFromCorpus:

    def __init__(self, corpus, alternative_text_field=None):
        """
        Parameters
        ----------
        corpus, Corpus: Corpus to extract documents and labels from
        alternative_text_field, str or None: if str, corpus must be parsed corpus
        """
        self._texts_to_display = None
        if alternative_text_field is not None:
            if not isinstance(corpus, ParsedCorpus):
                raise CorpusShouldBeParsedCorpusException('Corpus type needs to be ParsedCorpus to use the alternative text field.')
            self._texts_to_display = corpus.get_field(alternative_text_field)
        self._use_non_text_features = False
        self._use_terms_for_extra_features = False
        self._corpus = corpus

    def use_non_text_features(self):
        self._use_non_text_features = True
        return self

    def use_terms_for_extra_features(self):
        self._use_terms_for_extra_features = True
        return self

    def get_labels_and_texts(self):
        texts = self._get_texts_to_display()
        to_ret = {'categories': self._corpus.get_categories(), 'labels': self._corpus.get_doc_indices(), 'texts': self._get_list_from_texts(texts)}
        if self._use_non_text_features:
            to_ret['extra'] = self._corpus.list_extra_features(not self._use_terms_for_extra_features)
        return to_ret

    def _get_list_from_texts(self, texts):
        if sys.version_info[0] == 2:
            return texts.astype(unicode).tolist()
        else:
            return texts.astype(str).tolist()

    def _get_texts_to_display(self):
        if self._there_are_no_alternative_texts_to_display():
            return self._corpus.get_texts()
        else:
            return self._texts_to_display

    def _there_are_no_alternative_texts_to_display(self):
        return self._texts_to_display is None

    def get_labels_and_texts_and_meta(self, metadata):
        data = self.get_labels_and_texts()
        assert len(metadata) == len(data['labels'])
        data['meta'] = list(metadata)
        return data

def _get_list_from_texts(self, texts):
    if sys.version_info[0] == 2:
        return texts.astype(unicode).tolist()
    else:
        return texts.astype(str).tolist()

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

def _verify_coordinates(self, coords, name):
    if self.scatterchartdata.use_non_text_features and len(coords) != len(self.term_doc_matrix.get_metadata()):
        raise CoordinatesNotRightException('Length of %s_coords must be the same as the number of non-text features in the term_doc_matrix.' % name)
    if not self.scatterchartdata.use_non_text_features and len(coords) != self.term_doc_matrix.get_num_terms():
        raise CoordinatesNotRightException('Length of %s_coords must be the same as the number of terms in the term_doc_matrix.' % name)
    if max(coords) > 1:
        raise CoordinatesNotRightException('Max value of %s_coords must be <= 1.' % name)
    if min(coords) < 0:
        raise CoordinatesNotRightException('Min value of %s_coords must be >= 0.' % name)

def _preform_axis_rescale(self, json_df, rescaler, variable_to_rescale):
    if rescaler is not None:
        json_df.loc[:, variable_to_rescale] = rescaler(json_df[variable_to_rescale])
        assert json_df[variable_to_rescale].min() >= 0 and json_df[variable_to_rescale].max() <= 1

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

class Corpus(TermDocMatrix):

    def __init__(self, X, mX, y, term_idx_store, category_idx_store, metadata_idx_store, raw_texts, unigram_frequency_path=None):
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
        metadata_idx_store : IndexStore
          Document metadata indices
        raw_texts : np.array or pd.Series
            Raw texts
        unigram_frequency_path : str or None
            Path to term frequency file.
        """
        TermDocMatrix.__init__(self, X, mX, y, term_idx_store, category_idx_store, metadata_idx_store, unigram_frequency_path)
        self._raw_texts = raw_texts

    def get_texts(self):
        """
        Returns
        -------
        pd.Series, all raw documents
        """
        return self._raw_texts

    def get_doc_indices(self):
        return self._y.astype(int)

    def search(self, ngram, non_text: bool=False):
        """
        Parameters
        ----------
        ngram str or unicode, string to search for

        Returns
        -------
        pd.DataFrame, {'texts': <matching texts>, 'categories': <corresponding categories>}

        """
        mask = self._document_index_mask(ngram, non_text=non_text)
        return pd.DataFrame({'text': self.get_texts()[mask], 'category': [self._category_idx_store.getval(idx) for idx in self._y[mask]]})

    def search_index(self, term: str, non_text: bool=False):
        """
        Parameters
        ----------
        ngram str or unicode, string to search for

        Returns
        -------
        np.array, list of matching document indices
        """
        return nonzero(self._document_index_mask(term, non_text))[0]

    def _document_index_mask(self, feature: str, non_text: bool):
        term_idx_store = self.get_term_index_store(non_text=non_text)
        idx = term_idx_store.getidxstrict(feature.lower())
        mask = (self.get_term_doc_mat(non_text=non_text)[:, idx] > 0).todense().A1
        return mask

    def _make_new_term_doc_matrix(self, new_X=None, new_mX=None, new_y=None, new_term_idx_store=None, new_category_idx_store=None, new_metadata_idx_store=None, new_y_mask=None):
        X, mX, y = self._update_X_mX_y(new_X, new_mX, new_y, new_y_mask)
        return Corpus(X=X, mX=mX, y=y, term_idx_store=new_term_idx_store if new_term_idx_store is not None else self._term_idx_store, category_idx_store=new_category_idx_store if new_category_idx_store is not None else self._category_idx_store, metadata_idx_store=new_metadata_idx_store if new_metadata_idx_store is not None else self._metadata_idx_store, raw_texts=np.array(self.get_texts())[new_y_mask] if new_y_mask is not None else self.get_texts(), unigram_frequency_path=self._unigram_frequency_path)

def get_doc_indices(self):
    return self._y.astype(int)

def scale(vec, other_vec=None):
    if other_vec is None:
        other_vec = vec
    return (other_vec - vec.min()) / (vec.max() - vec.min())

def scale_jointly(x: List[float], y: List[float]) -> Coordinates:
    x, y = (np.array(x), np.array(y))
    global_max, global_min = (max(x.max(), y.max()), min(x.min(), y.min()))
    x_scaled = np.zeros(len(x), dtype=float)
    y_scaled = np.zeros(len(y), dtype=float)
    x_scaled[x < 0] = -(x[x < 0] / global_min)
    x_scaled[x > 0] = x[x > 0] / global_max
    y_scaled[y < 0] = -(y[y < 0] / global_min)
    y_scaled[y > 0] = y[y > 0] / global_max
    return Coordinates((x_scaled + 1) / 2, (y_scaled + 1) / 2)

def scale_jointly_positive(x: List[float], y: List[float]) -> Coordinates:
    x, y = (np.array(x), np.array(y))
    global_max, global_min = (max(x.max(), y.max()), min(x.min(), y.min()))
    x_scaled = (x - global_min) / (global_max - global_min)
    y_scaled = (y - global_min) / (global_max - global_min)
    return Coordinates(x=x_scaled, y=y_scaled)

def scale_center_zero(vec, other_vec=None):
    if other_vec is None:
        other_vec = vec
    return (other_vec > 0).astype(float) * (other_vec / vec.max()) * 0.5 + 0.5 + (other_vec < 0).astype(float) * (other_vec / -vec.min()) * 0.5

def scale_center_zero_abs(vec, other_vec=None):
    if other_vec is None:
        other_vec = vec
    max_abs = max(vec.max(), -vec.min())
    return (other_vec > 0).astype(float) * (other_vec / max_abs) * 0.5 + 0.5 + (other_vec < 0).astype(float) * (other_vec / max_abs) * 0.5

def scale_center_zero_separate_ranks(scores: np.array) -> np.array:
    scaled = np.zeros(len(scores), dtype=np.float64)
    scaled[scores > 0] = rankdata(scores[scores > 0]) / len(scores[scores > 0]) / 2 + 0.5
    scaled[scores < 0] = rankdata(scores[scores < 0]) / len(scores[scores < 0]) / 2
    return scaled

def scale_neg_1_to_1_with_zero_mean_abs_max(vec):
    max_abs = max(vec.max(), -vec.min())
    return (vec > 0).astype(float) * (vec / max_abs) * 0.5 + 0.5 + (vec < 0).astype(float) * (vec / max_abs) * 0.5

def scale_neg_1_to_1_with_zero_mean(vec):
    return (vec > 0).astype(float) * (vec / vec.max()) * 0.5 + 0.5 + (vec < 0).astype(float) * (vec / -vec.min()) * 0.5

def scale_neg_1_to_1_with_zero_mean_rank_abs_max(v):
    rankv = v * 2 - 1
    pos_v = rankv[rankv > 0]
    pos_v = rankdata(pos_v, 'dense')
    pos_v = pos_v / pos_v.max()
    neg_v = rankv[rankv < 0]
    neg_v = rankdata(neg_v, 'dense')
    neg_v = neg_v / neg_v.max()
    rankv[rankv > 0] = pos_v
    rankv[rankv < 0] = -(neg_v.max() - neg_v)
    return scale_neg_1_to_1_with_zero_mean_abs_max(rankv)

def scale_neg_1_to_1_with_zero_mean_log_abs_max(v):
    """
    !!! not working
    """
    df = pd.DataFrame({'v': v, 'sign': (v > 0) * 2 - 1})
    df['lg'] = np.log(np.abs(v)) / np.log(1.96)
    df['exclude'] = np.isinf(df.lg) | np.isneginf(df.lg)
    for mask in [(df['sign'] == -1) & (df['exclude'] == False), (df['sign'] == 1) & (df['exclude'] == False)]:
        df[mask]['lg'] = df[mask]['lg'].max() - df[mask]['lg']
    df['lg'] *= df['sign']
    df['lg'] = df['lg'].fillna(0)
    print(df[df['exclude']]['lg'].values)
    df['to_out'] = scale_neg_1_to_1_with_zero_mean_abs_max(df['lg'])
    print('right')
    print(df.sort_values(by='lg').iloc[:5])
    print(df.sort_values(by='lg').iloc[-5:])
    print('to_out')
    print(df.sort_values(by='to_out').iloc[:5])
    print(df.sort_values(by='to_out').iloc[-5:])
    print(len(df), len(df.dropna()))
    return df['to_out']

def scale_standardize(vec, terms=None, other_vec=None):
    to_ret = (vec - vec.mean()) / vec.std()
    to_ret += to_ret.min() + 1
    to_ret += to_ret.min()
    return to_ret

def log_scale_standardize(vec, terms=None, other_vec=None):
    vec_ss = np.log(vec + 1) / np.log(2)
    vec_ss = (vec_ss - vec_ss.mean()) / vec_ss.std()
    return scale_0_to_1(vec_ss)

def log_scale_with_negatives(in_vec: np.array) -> np.array:
    vec = in_vec.copy()
    pos_log = np.log(vec[vec > 0])
    neg_log = np.log(-vec[vec < 0])
    posnegmax = max(neg_log.max(), pos_log.max())
    posnegmin = min(neg_log.min(), pos_log.min())
    vec[in_vec < 0] = 0.499 * ((posnegmax - neg_log) / (posnegmax - posnegmin))
    vec[in_vec == 0] = 0.5
    vec[in_vec > 0] = 0.501 + 0.499 * (1 - (posnegmax - pos_log) / (posnegmax - posnegmin))
    return vec

def sqrt_scale_standardize(vec, terms=None, other_vec=None):
    vec_ss = np.sqrt(vec)
    vec_ss = (vec_ss - vec_ss.mean()) / vec_ss.std()
    return scale_0_to_1(vec_ss)

def f(vec, terms=None, other_vec=None):
    return scale_0_to_1(np.power(vec, 1.0 / alpha))

def sqrt_scale(vec, terms=None, other_vec=None):
    return scale_0_to_1(np.sqrt(vec))

def log_scale(vec, terms=None, other_vec=None):
    return scale_0_to_1(np.log(vec))

def percentile(vec, terms=None, other_vec=None):
    vec_ss = rankdata(vec, method='average') * (1.0 / len(vec))
    return scale_0_to_1(vec_ss)

def dense_rank(vec: np.array, terms=None, other_vec=None) -> np.array:
    ranks = rankdata(vec, method='dense') - 1
    if ranks.max() == 0:
        return np.ones(len(vec)) * 0.5
    return ranks / ranks.max()

def percentile_ordinal(vec, terms=None, other_vec=None):
    vec_ss = rankdata(vec, method='ordinal') * (1.0 / len(vec))
    return scale_0_to_1(vec_ss)

def percentile_min(vec, terms=None, other_vec=None):
    vec_ss = rankdata(vec, method='min') * (1.0 / len(vec))
    return scale_0_to_1(vec_ss)

def percentile_alphabetical(vec, terms, other_vec=None):
    scale_df = pd.DataFrame({'scores': vec, 'terms': terms})
    if other_vec is not None:
        scale_df['others'] = other_vec
    else:
        scale_df['others'] = 0
    vec_ss = scale_df.sort_values(by=['scores', 'terms', 'others'], ascending=[True, True, False]).reset_index().sort_values(by='index').index
    return scale_0_to_1(vec_ss)

def stretch_neg1_to_1(vec):
    a = np.copy(vec)
    if sum(a < 0):
        a[a < 0] = -a[a < 0] * 1.0 / a[a < 0].min()
    if sum(a > 0):
        a[a > 0] = a[a > 0] * 1.0 / a[a > 0].max()
    return a

def scale_0_to_1(vec_ss):
    if vec_ss.min() == vec_ss.max():
        return np.ones(len(vec_ss))
    my_vec_ss = np.nan_to_num(vec_ss, nan=0.0)
    vec_ss = (my_vec_ss - vec_ss.min()) * 1.0 / (my_vec_ss.max() - my_vec_ss.min())
    return vec_ss

def min_zero(vec):
    a = np.copy(vec)
    a[a < 0] = 0
    return a

def delete_columns(mat, columns_to_delete):
    """
	>>> a = csr_matrix(np.array([[0, 1, 3, 0, 1, 0],
		                           [0, 0, 1, 0, 1, 1]])
	>>> delete_columns(a, [1,2]).todense()
	matrix([[0, 0, 1, 0],
          [0, 0, 1, 1]])

	Parameters
	----------
	mat : csr_matrix
	columns_to_delete : list[int]

	Returns
	-------
	csr_matrix that is stripped of columns indices columns_to_delete
	"""
    column_mask = np.ones(mat.shape[1], dtype=bool)
    column_mask[columns_to_delete] = 0
    return mat.tocsc()[:, column_mask].tocsr()

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

def _get_percentiles_from_freqs(self, freqs):
    return rankdata(freqs) / len(freqs)

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

def copy_terms_to_metadata(self):
    """
        Returns a TermDocMatrix which is identical to self except the metadata values are now identical to the
        term document matrix.

        :return: TermDocMatrix
        """
    return self._make_new_term_doc_matrix(new_mX=copy(self._X), new_metadata_idx_store=copy(self._term_idx_store), new_y_mask=self._y == self._y)

def rename_metadata(self, old_to_new_vals: List[Tuple[str, str]], policy: MetadataReplacementRetentionPolicy=MetadataReplacementRetentionPolicy.KEEP_ONLY_NEW) -> Self:
    new_mX, new_metadata_idx_store = self._remap_metadata(old_to_new_vals)
    return self._make_new_term_doc_matrix(new_X=self._X, new_mX=new_mX, new_y=self._y, new_term_idx_store=self._term_idx_store, new_category_idx_store=self._category_idx_store, new_metadata_idx_store=new_metadata_idx_store, new_y_mask=self._y == self._y)

class OffsetCorpus(ParsedCorpus):

    def __init__(self, df, X, mX, y, term_idx_store, category_idx_store, metadata_idx_store, parsed_col, category_col, term_offsets, metadata_offsets, unigram_frequency_path=None):
        self._term_offsets = term_offsets
        self._metadata_offsets = metadata_offsets
        ParsedCorpus.__init__(self, df=df, X=X, mX=mX, y=y, term_idx_store=term_idx_store, category_idx_store=category_idx_store, metadata_idx_store=metadata_idx_store, parsed_col=parsed_col, category_col=category_col, unigram_frequency_path=unigram_frequency_path)

    def get_offsets(self):
        return self._metadata_offsets

    def _make_new_term_doc_matrix(self, new_X=None, new_mX=None, new_y=None, new_term_idx_store=None, new_category_idx_store=None, new_metadata_idx_store=None, new_y_mask=None, new_df=None, new_term_offsets=None, new_metadata_offsets=None):
        X, mX, y = self._update_X_mX_y(new_X, new_mX, new_y, new_y_mask)
        metadata_offsets, term_offsets = self._update_offsets(new_metadata_idx_store=new_metadata_idx_store, new_metadata_offsets=new_metadata_offsets, new_term_idx_store=new_term_idx_store, new_term_offsets=new_term_offsets)
        return OffsetCorpus(X=X, mX=mX, y=y, parsed_col=self._parsed_col, category_col=self._category_col, term_idx_store=new_term_idx_store if new_term_idx_store is not None else self._term_idx_store, category_idx_store=new_category_idx_store if new_category_idx_store is not None else self._category_idx_store, metadata_idx_store=new_metadata_idx_store if new_metadata_idx_store is not None else self._metadata_idx_store, df=self._apply_mask_to_df(new_y_mask, new_df), term_offsets=term_offsets, metadata_offsets=metadata_offsets, unigram_frequency_path=self._unigram_frequency_path)

    def _update_offsets(self, new_metadata_idx_store, new_metadata_offsets, new_term_idx_store, new_term_offsets):
        term_offsets = self._term_offsets if new_term_offsets is None else new_term_offsets
        metadata_offsets = self._metadata_offsets if new_metadata_offsets is None else new_metadata_offsets
        if new_term_idx_store is not None:
            term_offsets = {k: term_offsets[k] for k in new_term_idx_store.values()}
        if new_metadata_idx_store is not None:
            metadata_offsets = {k: metadata_offsets[k] for k in new_metadata_idx_store.values()}
        return (metadata_offsets, term_offsets)

    def rename_metadata(self, old_to_new_vals: List[Tuple[str, str]], policy: MetadataReplacementRetentionPolicy=MetadataReplacementRetentionPolicy.KEEP_ONLY_NEW) -> Self:
        new_mX, new_metadata_idx_store = self._remap_metadata(old_to_new_vals, policy=policy)
        new_metadata_offsets = self._remap_offsets(old_to_new_vals, policy)
        return self._make_new_term_doc_matrix(new_X=self._X, new_mX=new_mX, new_y=self._y, new_term_idx_store=self._term_idx_store, new_category_idx_store=self._category_idx_store, new_metadata_idx_store=new_metadata_idx_store, new_y_mask=self._y == self._y, new_metadata_offsets=new_metadata_offsets)

    def _remap_offsets(self, old_to_new_vals: List[Tuple[str, str]], policy: MetadataReplacementRetentionPolicy=MetadataReplacementRetentionPolicy.KEEP_ONLY_NEW) -> Dict[str, Dict[int, List[Tuple[int, int]]]]:
        old_to_new_df = self._get_old_to_new_metadata_mapping_df(old_to_new_vals)
        keep_vals = self._get_metadata_mapped_values_to_keep(old_to_new_df)
        new_metadata_offsets = {}
        for new_val, new_df in old_to_new_df.groupby('New'):
            new_count_offsets = {}
            for old in new_df.Old.values:
                old_offsets = self._metadata_offsets.get(old, [])
                for doc_id, offsets in old_offsets.items():
                    new_count_offsets.setdefault(doc_id, []).extend(offsets)
            new_metadata_offsets[new_val] = new_count_offsets
            if policy.value == MetadataReplacementRetentionPolicy.KEEP_UNMODIFIED.value:
                for keep_val in keep_vals:
                    new_metadata_offsets[keep_val] = self._metadata_offsets[keep_val]
            elif policy.value == MetadataReplacementRetentionPolicy.KEEP_ALL.value:
                for val in self.get_metadata():
                    new_metadata_offsets[val] = self._metadata_offsets[val]
        return new_metadata_offsets

    def use_categories_as_metadata_and_replace_terms(self):
        """
        Returns a TermDocMatrix which is identical to self except the metadata values are now identical to the
         categories present and term-doc-matrix is now the metadata matrix.

        :return: TermDocMatrix
        """
        new_tdm = self._make_new_term_doc_matrix(new_X=self._mX, new_mX=self._categories_to_metadata_factory(), new_y=self._y, new_term_idx_store=self._metadata_idx_store, new_category_idx_store=self._category_idx_store, new_metadata_idx_store=copy(self._category_idx_store), new_y_mask=self._y == self._y, new_term_offsets=self._metadata_offsets, new_metadata_offsets={k: [] for k in self.get_categories()})
        return new_tdm

def rename_metadata(self, old_to_new_vals: List[Tuple[str, str]], policy: MetadataReplacementRetentionPolicy=MetadataReplacementRetentionPolicy.KEEP_ONLY_NEW) -> Self:
    new_mX, new_metadata_idx_store = self._remap_metadata(old_to_new_vals, policy=policy)
    new_metadata_offsets = self._remap_offsets(old_to_new_vals, policy)
    return self._make_new_term_doc_matrix(new_X=self._X, new_mX=new_mX, new_y=self._y, new_term_idx_store=self._term_idx_store, new_category_idx_store=self._category_idx_store, new_metadata_idx_store=new_metadata_idx_store, new_y_mask=self._y == self._y, new_metadata_offsets=new_metadata_offsets)

def use_categories_as_metadata_and_replace_terms(self):
    """
        Returns a TermDocMatrix which is identical to self except the metadata values are now identical to the
         categories present and term-doc-matrix is now the metadata matrix.

        :return: TermDocMatrix
        """
    new_tdm = self._make_new_term_doc_matrix(new_X=self._mX, new_mX=self._categories_to_metadata_factory(), new_y=self._y, new_term_idx_store=self._metadata_idx_store, new_category_idx_store=self._category_idx_store, new_metadata_idx_store=copy(self._category_idx_store), new_y_mask=self._y == self._y, new_term_offsets=self._metadata_offsets, new_metadata_offsets={k: [] for k in self.get_categories()})
    return new_tdm

class ScaledFScoreSignificance(TermSignificance):

    def __init__(self, scaler_algo=DEFAULT_SCALER_ALGO, beta=DEFAULT_BETA):
        """
		Parameters
		----------
		scaler_algo : str
			Function that scales an array to a range \\in [0 and 1]. Use 'percentile', 'normcdf'. Default normcdf.
		beta : float
			Beta in (1+B^2) * (Scale(P(w|c)) * Scale(P(c|w)))/(B^2*Scale(P(w|c)) + Scale(P(c|w))). Defaults to 1.
		"""
        self.scaler_algo = scaler_algo
        self.beta = beta

    def get_name(self):
        return 'Scaled F-Score'

    def get_p_vals(self, X):
        """
		Imputes p-values from the Z-scores of `ScaledFScore` scores.  Assuming incorrectly
		that the scaled f-scores are normally distributed.

		Parameters
		----------
		X : np.array
			Array of word counts, shape (N, 2) where N is the vocab size.  X[:,0] is the
			positive class, while X[:,1] is the negative class.

		Returns
		-------
		np.array of p-values

		"""
        z_scores = ScaledFZScore(self.scaler_algo, self.beta).get_scores(X[:, 0], X[:, 1])
        return norm.cdf(z_scores)

def get_p_vals(self, X):
    """
		Imputes p-values from the Z-scores of `ScaledFScore` scores.  Assuming incorrectly
		that the scaled f-scores are normally distributed.

		Parameters
		----------
		X : np.array
			Array of word counts, shape (N, 2) where N is the vocab size.  X[:,0] is the
			positive class, while X[:,1] is the negative class.

		Returns
		-------
		np.array of p-values

		"""
    z_scores = ScaledFZScore(self.scaler_algo, self.beta).get_scores(X[:, 0], X[:, 1])
    return norm.cdf(z_scores)

class SemioticSquareFromAxes(SemioticSquareBase):

    def __init__(self, term_doc_matrix, axes, x_axis_name, y_axis_name, labels=None, distance_measure=EuclideanDistance):
        """

        :param term_doc_matrix: TermDocMatrix
        :param axes: pd.DataFrame
        :param x_axis_name: str
        :param y_axis_name: str
        :param labels: dict, optional
        :param distance_measure: DistanceMeasureBase, EuclideanDistance by default
        """
        self.term_doc_matrix = term_doc_matrix
        assert type(axes) == pd.DataFrame
        assert set(axes.columns) == set(['x', 'y'])
        assert set(axes.index) == set(term_doc_matrix.get_terms())
        self.axes = axes
        self.y_axis_name = y_axis_name
        self.x_axis_name = x_axis_name
        if labels is None:
            self._labels = {}
        else:
            self._labels = labels
        self._distance_measure = distance_measure

    def get_labels(self):
        """

        :return: dict
        """
        default_labels = {'a': 'not-%s; %s' % (self.x_axis_name, self.y_axis_name), 'not_a': '%s; not-%s' % (self.x_axis_name, self.y_axis_name), 'b': '%s; %s' % (self.x_axis_name, self.y_axis_name), 'not_b': 'not-%s; not-%s' % (self.x_axis_name, self.y_axis_name), 'a_and_b': '%s' % self.y_axis_name, 'not_a_and_not_b': 'not-%s' % self.y_axis_name, 'a_and_not_b': 'not-%s' % self.x_axis_name, 'b_and_not_a': '%s' % self.x_axis_name}
        return {name + '_label': self._labels.get(name, default_labels[name]) for name in default_labels}

    def get_axes(self, **kwargs):
        return self.axes

    def get_lexicons(self, num_terms=10):
        x_max = self.axes['x'].max()
        x_med = self.axes['x'].median()
        x_min = self.axes['x'].min()
        y_max = self.axes['y'].max()
        y_med = self.axes['y'].median()
        y_min = self.axes['y'].min()
        lexicons = {}
        for label, [x_coord, y_coord] in [['a', [x_min, y_max]], ['not_a', [x_max, y_min]], ['b', [x_max, y_max]], ['not_b', [x_min, y_min]], ['a_and_b', [x_med, y_max]], ['not_a_and_not_b', [x_med, y_min]], ['b_and_not_a', [x_max, y_med]], ['a_and_not_b', [x_min, y_med]]]:
            scores = self._distance_measure.distances(x_coord, y_coord, self.axes['x'], self.axes['y'])
            lexicons[label] = list(self.axes.index[np.argsort(scores)])[:num_terms]
        return lexicons

def get_lexicons(self, num_terms=10):
    x_max = self.axes['x'].max()
    x_med = self.axes['x'].median()
    x_min = self.axes['x'].min()
    y_max = self.axes['y'].max()
    y_med = self.axes['y'].median()
    y_min = self.axes['y'].min()
    lexicons = {}
    for label, [x_coord, y_coord] in [['a', [x_min, y_max]], ['not_a', [x_max, y_min]], ['b', [x_max, y_max]], ['not_b', [x_min, y_min]], ['a_and_b', [x_med, y_max]], ['not_a_and_not_b', [x_med, y_min]], ['b_and_not_a', [x_max, y_med]], ['a_and_not_b', [x_min, y_med]]]:
        scores = self._distance_measure.distances(x_coord, y_coord, self.axes['x'], self.axes['y'])
        lexicons[label] = list(self.axes.index[np.argsort(scores)])[:num_terms]
    return lexicons

def add_radial_parts_and_mag_to_term_coordinates(term_coordinates_df: pd.DataFrame) -> pd.DataFrame:
    assert 'x' in term_coordinates_df.columns
    assert 'y' in term_coordinates_df.columns
    radial_term_coordinates_df = term_coordinates_df.apply(stretch_neg1_to_1).assign(FinePart=lambda df: ((np.arctan2(df.x, df.y) + np.pi) * 360 / (2 * np.pi) // (45 / 2)).astype(int), Part=lambda df: df.FinePart.apply(FINE_PART_TO_SELECTION.get), Mag=lambda df: df.x ** 2 + df.y ** 2)
    return radial_term_coordinates_df

class BackgroundFrequencyDataFramePreparer(object):

    @staticmethod
    def prep_background_frequency(df):
        df['rank'] = rankdata(df.background, method='dense')
        df['background'] = df['rank'] / df['rank'].max()
        return df['background']

@staticmethod
def prep_background_frequency(df):
    df['rank'] = rankdata(df.background, method='dense')
    df['background'] = df['rank'] / df['rank'].max()
    return df['background']

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

class SimpleDiGraph(object):

    def __init__(self, orig_edge_df):
        self.orig_edge_df = orig_edge_df
        self.id_node_df = pd.DataFrame({'name': list(set(orig_edge_df.source.values) | set(orig_edge_df.target.values))})
        self.node_df = self.id_node_df.reset_index().set_index('name')
        self.edge_df = pd.merge(pd.merge(self.orig_edge_df, self.node_df, left_on='source', right_index=True).rename(columns={'index': 'source_id'}), self.node_df, left_on='target', right_index=True).rename(columns={'index': 'target_id'})

    def make_component_digraph(self, graph_params, node_params):
        components = self.get_connected_components()
        return ComponentDiGraph(edge_df=self.edge_df.assign(Component=lambda df: components[df.source_id]), orig_edge_df=self.orig_edge_df.assign(Component=components[self.edge_df.source_id]), node_df=self.node_df.assign(Component=lambda df: components[df['index']]), id_node_df=self.id_node_df.assign(Component=lambda df: components[df.index]), components=components, graph_params=graph_params, node_params=node_params)

    def get_connected_subgraph_df(self):
        return pd.DataFrame({'component': self.get_connected_components(), 'nodes': self.node_df['index'].values, 'values': self.node_df.index}).groupby('component').agg(list).assign(size=lambda df: df.nodes.apply(len)).sort_values(by='size', ascending=False).reset_index(drop=True)

    def get_connected_components(self):
        return connected_components(self.get_sparse_graph(), True)[1]

    def get_sparse_graph(self):
        return csr_matrix((np.ones(len(self.edge_df)), (self.edge_df.source_id.values, self.edge_df.target_id.values)), shape=(len(self.node_df), len(self.node_df)))

    def limit_nodes(self, nodes):
        return SimpleDiGraph(self.edge_df[self.edge_df.target_id.isin(nodes) | self.edge_df.source_id.isin(nodes)][['source', 'target']])

def get_sparse_graph(self):
    return csr_matrix((np.ones(len(self.edge_df)), (self.edge_df.source_id.values, self.edge_df.target_id.values)), shape=(len(self.node_df), len(self.node_df)))

class LengthNormalizeRobustScale(object):

    def fit_transform(self, X):
        compact_category_counts_catscale = X / X.sum(axis=0)
        compact_category_counts_catscale_std = (compact_category_counts_catscale.T - compact_category_counts_catscale.mean(axis=1)).T
        return RobustScaler().fit_transform(compact_category_counts_catscale_std)

def fit_transform(self, X):
    compact_category_counts_catscale = X / X.sum(axis=0)
    compact_category_counts_catscale_std = (compact_category_counts_catscale.T - compact_category_counts_catscale.mean(axis=1)).T
    return RobustScaler().fit_transform(compact_category_counts_catscale_std)

class RankDifferenceScorer(CorpusBasedTermScorer):

    def _set_scorer_args(self, **kwargs):
        """
        method : {'average', 'min', 'max', 'dense', 'ordinal'}, optional
        """
        self.method = kwargs.get('method', 'dense')

    def get_scores(self, *args):
        """
        In this case, args aren't used, since this information is taken
        directly from the corpus categories.

        Returns
        -------
        np.array, scores
        """
        if self.tdf_ is None:
            raise Exception("Use set_categories('category name', ['not category name', ...]) " + 'to set the category of interest')
        dense_rank_difference = self._dense_rank_difference(self.tdf_['cat'], self.tdf_['ncat'])
        if type(self.tdf_['cat']) == pd.Series:
            return pd.Series(dense_rank_difference, index=self.tdf_['cat'].index)
        return dense_rank_difference

    def _dense_rank_difference(self, a, b):
        a_ranks = rankdata(a, self.method)
        b_ranks = rankdata(b, self.method)
        to_ret = a_ranks / np.max(a_ranks) - b_ranks / np.max(b_ranks)
        return to_ret

    def get_default_score(self):
        return 0

    def get_name(self):
        return 'Rank Difference'

def _dense_rank_difference(self, a, b):
    a_ranks = rankdata(a, self.method)
    b_ranks = rankdata(b, self.method)
    to_ret = a_ranks / np.max(a_ranks) - b_ranks / np.max(b_ranks)
    return to_ret

class MannWhitneyU(CorpusBasedTermScorer):
    """

    term_scorer = (MannWhitneyU(corpus).set_categories('Positive', ['Negative'], ['Plot']))

    html = st.produce_frequency_explorer(
        corpus,
        category='Positive',
        not_categories=['Negative'],
        neutral_categories=['Plot'],
        term_scorer=term_scorer,
        metadata=rdf['movie_name'],
        grey_threshold=0,
        show_neutral=True
    )
    file_name = 'rotten_fresh_mwu.html'
    open(file_name, 'wb').write(html.encode('utf-8'))
    IFrame(src=file_name, width=1300, height=700)
    """

    def _set_scorer_args(self, *args, **kwargs):
        self.verbose = kwargs.get('verbose', False)

    def get_scores(self, *args):
        return self.get_score_df()['mwu_z']

    def get_score_df(self, correction_method=None):
        """
        Computes Mann Whitney corrected p, z-values.  Falls back to normal approximation when numerical limits are reached.

        :param correction_method: str or None, correction method from statsmodels.stats.multitest.multipletests
         'fdr_bh' is recommended.
        :return: pd.DataFrame
        """
        X = self._get_X().astype(np.float64)
        X_norm = X / X.sum(axis=1)
        cat_X, ncat_X = self._get_cat_and_ncat(X_norm)
        try:
            if cat_X.format == 'coo':
                cat_X = cat_X.tocsr()
                ncat_X = ncat_X.tocsr()
        except:
            pass

        def normal_apx(u, x, y):
            m_u = len(x) * len(y) / 2
            sigma_u = np.sqrt(len(x) * len(y) * (len(x) + len(y) + 1) / 12)
            z = (u - m_u) / sigma_u
            return 2 * norm.cdf(z)
        scores = []
        iter = range(cat_X.shape[1])
        if self.verbose:
            iter = tqdm(iter)
        for i in iter:
            try:
                cat_list = cat_X.T[i].A1
                ncat_list = ncat_X.T[i].A1
            except:
                cat_list = np.repeat(cat_X[:, i].todense(), cat_X.shape[0], axis=1).ravel().A1
                ncat_list = np.repeat(ncat_X[:, i].todense(), ncat_X.shape[0], axis=1).T.ravel().A1
            try:
                if cat_list.mean() > ncat_list.mean():
                    mw = mannwhitneyu(cat_list, ncat_list, alternative='greater')
                    if mw.pvalue in (0, 1):
                        mw.pvalue = normal_apx(mw.staistic, cat_list, ncat_list)
                    scores.append({'mwu': mw.statistic, 'mwu_p': mw.pvalue, 'mwu_z': norm.isf(float(mw.pvalue)), 'valid': True})
                else:
                    mw = mannwhitneyu(ncat_list, cat_list, alternative='greater')
                    if mw.pvalue in (0, 1):
                        mw.pvalue = normal_apx(mw.staistic, ncat_list, cat_list)
                    scores.append({'mwu': -mw.statistic, 'mwu_p': 1 - mw.pvalue, 'mwu_z': 1.0 - norm.isf(float(mw.pvalue)), 'valid': True})
            except:
                scores.append({'mwu': 0, 'mwu_p': 0, 'mwu_z': 0, 'valid': False})
        count_cat_X, count_ncat_X = self._get_cat_and_ncat(X)
        score_df = pd.DataFrame(scores, index=self._get_terms()).fillna(0).assign(TermCount1=count_cat_X.sum(axis=0).A1, TermCount2=count_ncat_X.sum(axis=0).A1, DocCount1=(count_cat_X > 0).sum(axis=0).A1, DocCount2=(count_ncat_X > 0).sum(axis=0).A1)
        if correction_method is not None:
            from statsmodels.stats.multitest import multipletests
            for method in ['mwu']:
                valid_pvals = score_df[score_df.valid].mwu_p
                valid_pvals_abs = np.min([valid_pvals, 1 - valid_pvals], axis=0)
                valid_pvals_abs_corr = multipletests(valid_pvals_abs, method=correction_method)[1]
                score_df[method + '_p_corr'] = 0.5
                valid_pvals_abs_corr[valid_pvals > 0.5] = 1.0 - valid_pvals_abs_corr[valid_pvals > 0.5]
                valid_pvals_abs_corr[valid_pvals < 0.5] = valid_pvals_abs_corr[valid_pvals < 0.5]
                score_df.loc[score_df.valid, method + '_p_corr'] = valid_pvals_abs_corr
                score_df[method + '_z'] = -norm.ppf(score_df[method + '_p_corr'])
        return score_df

    def get_name(self):
        return 'Mann Whitney Z'

def normal_apx(u, x, y):
    m_u = len(x) * len(y) / 2
    sigma_u = np.sqrt(len(x) * len(y) * (len(x) + len(y) + 1) / 12)
    z = (u - m_u) / sigma_u
    return 2 * norm.cdf(z)

class RankDifference(object):

    def get_scores(self, a, b):
        to_ret = rankdata(a, 'dense') / np.max(rankdata(a, 'dense')) - rankdata(b, 'dense') / np.max(rankdata(b, 'dense'))
        if type(a) == pd.Series:
            return pd.Series(to_ret, index=a.index)
        return to_ret

    def get_name(self):
        return 'Rank Difference'

    def get_default_score(self):
        return 0

def get_scores(self, a, b):
    to_ret = rankdata(a, 'dense') / np.max(rankdata(a, 'dense')) - rankdata(b, 'dense') / np.max(rankdata(b, 'dense'))
    if type(a) == pd.Series:
        return pd.Series(to_ret, index=a.index)
    return to_ret

def sparse_var(X):
    """
    Compute variance from
    :param X:
    :return:
    """
    Xc = X.copy()
    Xc.data **= 2
    return np.array(Xc.mean(axis=0) - np.power(X.mean(axis=0), 2))[0]

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

def _get_mean_delta(self, cat_X, ncat_X):
    return np.array(cat_X.mean(axis=0) - ncat_X.mean(axis=0))[0]

class CornerScore(object):

    @staticmethod
    def get_scores(cat_word_counts, not_cat_word_counts):
        pos = CornerScore.get_scores_for_category(cat_word_counts, not_cat_word_counts)
        neg = CornerScore.get_scores_for_category(not_cat_word_counts, cat_word_counts)
        scores = CornerScore._balance_scores(pos, neg)
        return scores

    @staticmethod
    def _balance_scores(cat_scores, not_cat_scores):
        scores = np.zeros(len(cat_scores))
        scores[cat_scores < not_cat_scores] = np.sqrt(2) - cat_scores[cat_scores < not_cat_scores]
        scores[not_cat_scores < cat_scores] = -(np.sqrt(2) - not_cat_scores[not_cat_scores < cat_scores])
        return (scores / np.sqrt(2) + 1.0) / 2

    @staticmethod
    def get_scores_for_category(cat_word_counts, not_cat_word_counts):
        cat_pctls = CornerScore._get_percentiles_from_freqs(cat_word_counts)
        not_cat_pctls = CornerScore._get_percentiles_from_freqs(not_cat_word_counts)
        return CornerScore._distance_from_upper_left(cat_pctls, not_cat_pctls)

    @staticmethod
    def _distance_from_upper_left(cat_pctls, not_cat_pctls):
        return np.linalg.norm(np.array([1, 0]) - np.array(list(zip(cat_pctls, not_cat_pctls))), axis=1)

    @staticmethod
    def _get_percentiles_from_freqs(freqs):
        return rankdata(freqs) * 1.0 / len(freqs)

@staticmethod
def _get_percentiles_from_freqs(freqs):
    return rankdata(freqs) * 1.0 / len(freqs)

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
def _scale(ar):
    if len(ar) == 0:
        return ar
    if ar.min() == ar.max():
        return np.full(len(ar), 0.5)
    return (ar - ar.min()) / (ar.max() - ar.min())

class ScaledFZScore(ScaledFScorePresets):

    @staticmethod
    def get_default_score():
        return 0

    def get_scores(self, cat_word_counts, not_cat_word_counts):
        sfs = ScaledFScorePresets.get_scores(self, cat_word_counts, not_cat_word_counts)
        return (sfs - sfs.mean()) / np.std(sfs)

    def get_name(self):
        return 'Scaled F-Score Z-Score'

    def get_score_deltas(self, cat_word_counts, not_cat_word_counts):
        cat_scores = ScaledFScorePresets.get_scores_for_category(self, cat_word_counts, not_cat_word_counts)
        not_cat_scores = ScaledFScorePresets.get_scores_for_category(self, not_cat_word_counts, cat_word_counts)
        return np.log(cat_scores) - np.log(not_cat_scores)

    def get_p_vals(self, X):
        """
        Parameters
        ----------
        X : np.array
            Array of word counts, shape (N, 2) where N is the vocab size.  X[:,0] is the
            positive class, while X[:,1] is the negative class. None by default

        Returns
        -------
        np.array of p-values

        """
        z_scores = self.get_scores(X[:, 0], X[:, 1])
        return norm.cdf(z_scores)

def get_scores(self, cat_word_counts, not_cat_word_counts):
    sfs = ScaledFScorePresets.get_scores(self, cat_word_counts, not_cat_word_counts)
    return (sfs - sfs.mean()) / np.std(sfs)

def get_p_vals(self, X):
    """
        Parameters
        ----------
        X : np.array
            Array of word counts, shape (N, 2) where N is the vocab size.  X[:,0] is the
            positive class, while X[:,1] is the negative class. None by default

        Returns
        -------
        np.array of p-values

        """
    z_scores = self.get_scores(X[:, 0], X[:, 1])
    return norm.cdf(z_scores)

class ScaledFZScorePrior(ScaledFZScore):

    def __init__(self, prior, alpha=1, scaler_algo=DEFAULT_SCALER_ALGO, beta=DEFAULT_BETA):
        self.prior = prior
        self.alpha = alpha
        ScaledFZScore.__init__(self, scaler_algo, beta)

    def get_name(self):
        return 'SFS w/ Informative Prior Z-Score'

    def apply_prior(self, c):
        n = np.sum(c)
        prior_scale = np.sum(c) * self.alpha * 1.0 / np.sum(self.prior)
        return c + self.prior * prior_scale

    def get_scores(self, cat_word_counts, not_cat_word_counts):
        sfs = ScaledFScorePresets.get_scores(self, self.apply_prior(cat_word_counts), self.apply_prior(not_cat_word_counts))
        return (sfs - sfs.mean()) / np.std(sfs)

    def get_name(self):
        return 'SFS Z-Scores'

    def get_score_deltas(self, cat_word_counts, not_cat_word_counts):
        cat_scores = ScaledFScorePresets.get_scores_for_category(self, self.apply_prior(cat_word_counts), self.apply_prior(not_cat_word_counts))
        not_cat_scores = ScaledFScorePresets.get_scores_for_category(self, self.apply_prior(not_cat_word_counts), self.apply_prior(cat_word_counts))
        return np.log(cat_scores) - np.log(not_cat_scores)

def get_scores(self, cat_word_counts, not_cat_word_counts):
    sfs = ScaledFScorePresets.get_scores(self, self.apply_prior(cat_word_counts), self.apply_prior(not_cat_word_counts))
    return (sfs - sfs.mean()) / np.std(sfs)

def get_score_deltas(self, cat_word_counts, not_cat_word_counts):
    cat_scores = ScaledFScorePresets.get_scores_for_category(self, self.apply_prior(cat_word_counts), self.apply_prior(not_cat_word_counts))
    not_cat_scores = ScaledFScorePresets.get_scores_for_category(self, self.apply_prior(not_cat_word_counts), self.apply_prior(cat_word_counts))
    return np.log(cat_scores) - np.log(not_cat_scores)

class ScaledFScore(object):

    @staticmethod
    def get_default_score():
        return 0.5

    @staticmethod
    def get_scores(cat_word_counts, not_cat_word_counts, scaler_algo=DEFAULT_SCALER_ALGO, beta=DEFAULT_BETA):
        """ Computes balanced scaled f-scores
        Parameters
        ----------
        cat_word_counts : np.array
            category counts
        not_cat_word_counts : np.array
            not category counts
        scaler_algo : str
            Function that scales an array to a range \\in [0 and 1]. Use 'percentile', 'normcdf'. Default.
        beta : float
            Beta in (1+B^2) * (Scale(P(w|c)) * Scale(P(c|w)))/(B^2*Scale(P(w|c)) + Scale(P(c|w))). Default.
        Returns
        -------
            np.array
            Harmonic means of scaled P(word|category)
             and scaled P(category|word) for >median half of scores.  Low scores are harmonic means
             of scaled P(word|~category) and scaled P(~category|word).  Array is squashed to between
             0 and 1, with 0.5 indicating a median score.
        """
        cat_scores = ScaledFScore.get_scores_for_category(cat_word_counts, not_cat_word_counts, scaler_algo, beta)
        not_cat_scores = ScaledFScore.get_scores_for_category(not_cat_word_counts, cat_word_counts, scaler_algo, beta)
        return ScoreBalancer.balance_scores(cat_scores, not_cat_scores)

    @staticmethod
    def get_scores_for_category(cat_word_counts, not_cat_word_counts, scaler_algo=DEFAULT_SCALER_ALGO, beta=DEFAULT_BETA):
        """ Computes unbalanced scaled-fscores
        Parameters
        ----------
        category : str
            category name to score
        scaler_algo : str
            Function that scales an array to a range \\in [0 and 1]. Use 'percentile', 'normcdf'. Default normcdf
        beta : float
            Beta in (1+B^2) * (Scale(P(w|c)) * Scale(P(c|w)))/(B^2*Scale(P(w|c)) + Scale(P(c|w))). Defaults to 1.
        Returns
        -------
            np.array of harmonic means of scaled P(word|category) and scaled P(category|word).
        """
        assert beta > 0
        old_cat_word_counts = None
        if type(cat_word_counts) == pd.Series:
            old_cat_word_counts = cat_word_counts
            cat_word_counts = cat_word_counts.values
        if type(not_cat_word_counts) == pd.Series:
            not_cat_word_counts = not_cat_word_counts.values
        precision = cat_word_counts * 1.0 / (cat_word_counts + not_cat_word_counts)
        recall = cat_word_counts * 1.0 / cat_word_counts.sum()
        precision_normcdf = ScaledFScore._safe_scaler(scaler_algo, precision)
        recall_normcdf = ScaledFScore._safe_scaler(scaler_algo, recall)
        scores_numerator = (1 + beta ** 2) * (precision_normcdf * recall_normcdf)
        scores_denominator = beta ** 2 * precision_normcdf + recall_normcdf
        scores_denominator[scores_denominator == 0] = 1
        scores = scores_numerator / scores_denominator
        scores[np.isnan(scores)] = 0.0
        if old_cat_word_counts is None:
            return scores
        else:
            return pd.Series(scores, index=old_cat_word_counts.index)

    @staticmethod
    def _get_scaled_f_score_from_counts(cat_word_counts, not_cat_word_counts, scaler_algo, beta=DEFAULT_BETA):
        p_word_given_category = cat_word_counts.astype(np.float) / cat_word_counts.sum()
        p_category_given_word = cat_word_counts * 1.0 / (cat_word_counts + not_cat_word_counts)
        scores = ScaledFScore._get_harmonic_mean_of_probabilities_over_non_zero_in_category_count_terms(cat_word_counts, p_category_given_word, p_word_given_category, scaler_algo, beta)
        return scores

    @staticmethod
    def _safe_scaler(algo, ar):
        if algo == 'none':
            return ar
        scaled_ar = ScaledFScore._get_scaler_function(algo)(ar)
        if np.isnan(scaled_ar).any():
            return ScaledFScore._get_scaler_function('percentile')(scaled_ar)
        return scaled_ar

    @staticmethod
    def _get_scaler_function(scaler_algo):
        scaler = None
        if scaler_algo == 'normcdf':
            scaler = lambda x: norm.cdf(x, x.mean(), x.std())
        elif scaler_algo == 'lognormcdf':
            scaler = lambda x: norm.cdf(np.log(x), np.log(x).mean(), np.log(x).std())
        elif scaler_algo == 'percentile':
            scaler = lambda x: rankdata(x).astype(np.float64) / len(x)
        elif scaler_algo == 'percentiledense':
            scaler = lambda x: rankdata(x, method='dense').astype(np.float64) / len(x)
        elif scaler_algo == 'ecdf':
            from statsmodels.distributions import ECDF
            scaler = lambda x: ECDF(x)
        elif scaler_algo == 'none':
            scaler = lambda x: x
        else:
            raise InvalidScalerException('Invalid scaler alogrithm.  Must be either percentile or normcdf.')
        return scaler

@staticmethod
def _get_scaled_f_score_from_counts(cat_word_counts, not_cat_word_counts, scaler_algo, beta=DEFAULT_BETA):
    p_word_given_category = cat_word_counts.astype(np.float) / cat_word_counts.sum()
    p_category_given_word = cat_word_counts * 1.0 / (cat_word_counts + not_cat_word_counts)
    scores = ScaledFScore._get_harmonic_mean_of_probabilities_over_non_zero_in_category_count_terms(cat_word_counts, p_category_given_word, p_word_given_category, scaler_algo, beta)
    return scores

@staticmethod
def _get_scaler_function(scaler_algo):
    scaler = None
    if scaler_algo == 'normcdf':
        scaler = lambda x: norm.cdf(x, x.mean(), x.std())
    elif scaler_algo == 'lognormcdf':
        scaler = lambda x: norm.cdf(np.log(x), np.log(x).mean(), np.log(x).std())
    elif scaler_algo == 'percentile':
        scaler = lambda x: rankdata(x).astype(np.float64) / len(x)
    elif scaler_algo == 'percentiledense':
        scaler = lambda x: rankdata(x, method='dense').astype(np.float64) / len(x)
    elif scaler_algo == 'ecdf':
        from statsmodels.distributions import ECDF
        scaler = lambda x: ECDF(x)
    elif scaler_algo == 'none':
        scaler = lambda x: x
    else:
        raise InvalidScalerException('Invalid scaler alogrithm.  Must be either percentile or normcdf.')
    return scaler

class BM25Difference(CorpusBasedTermScorer):
    """
	Designed for use only in the term_scorer argument.
	This should really be inherit specific type.

	term_scorer = (BM25Difference(corpus, k1 = 1.4, b=0.9)
		.set_categories('Positive', ['Negative'], ['Plot']))

	html = st.produce_frequency_explorer(
		corpus,
		category='Positive',
		not_categories=['Negative'],
		neutral_categories=['Plot'],
		term_scorer=term_scorer,
		metadata=rdf['movie_name'],
		grey_threshold=0,
		show_neutral=True
	)
	file_name = 'output/rotten_fresh_bm25.html'
	open(file_name, 'wb').write(html.encode('utf-8'))
	IFrame(src=file_name, width=1300, height=700)
	"""

    def _set_scorer_args(self, **kwargs):
        self.k1 = kwargs.get('k1', 1.2)
        self.b = kwargs.get('b', 0.95)

    def get_scores(self, *args) -> np.array:
        """
		In this case, args aren't used, since this information is taken
		directly from the corpus categories.

		Returns
		-------
		np.array, scores
		"""
        if self.tdf_ is None:
            raise Exception("Use set_category_name('category name', ['not category name', ...]) " + 'to set the category of interest')
        avgdl = self.tdf_.sum(axis=0).mean()

        def idf(cat):
            n_q = (self.tdf_ > 0).astype(int).max(axis=1).sum()
            N = len(self.tdf_)
            return (N - n_q + 0.5) / (n_q + 0.5)

        def length_adjusted_tf(cat):
            tf = self.tdf_[cat]
            dl = self.tdf_[cat].sum()
            return tf * (self.k1 + 1) / (tf + self.k1 * (1 - self.b + self.b * (dl / avgdl)))

        def bm25_score(cat):
            return -length_adjusted_tf(cat) * np.log(idf(cat))
        scores = bm25_score('cat') - bm25_score('ncat')
        return scores

    def get_name(self):
        return 'BM25 difference'

def get_scores(self, *args) -> np.array:
    """
		In this case, args aren't used, since this information is taken
		directly from the corpus categories.

		Returns
		-------
		np.array, scores
		"""
    if self.tdf_ is None:
        raise Exception("Use set_category_name('category name', ['not category name', ...]) " + 'to set the category of interest')
    avgdl = self.tdf_.sum(axis=0).mean()

    def idf(cat):
        n_q = (self.tdf_ > 0).astype(int).max(axis=1).sum()
        N = len(self.tdf_)
        return (N - n_q + 0.5) / (n_q + 0.5)

    def length_adjusted_tf(cat):
        tf = self.tdf_[cat]
        dl = self.tdf_[cat].sum()
        return tf * (self.k1 + 1) / (tf + self.k1 * (1 - self.b + self.b * (dl / avgdl)))

    def bm25_score(cat):
        return -length_adjusted_tf(cat) * np.log(idf(cat))
    scores = bm25_score('cat') - bm25_score('ncat')
    return scores

def idf(cat):
    n_q = (self.tdf_ > 0).astype(int).max(axis=1).sum()
    N = len(self.tdf_)
    return (N - n_q + 0.5) / (n_q + 0.5)

class OLSUngarStyle(object):

    def get_scores_and_p_values(self, tdm, category):
        """
		Parameters
		----------
		tdm: TermDocMatrix
		category: str, category name

		Returns
		-------
		pd.DataFrame(['coef', 'p-val'])
		"""
        X = tdm._X
        y = self._make_response_variable_1_or_negative_1(category, tdm)
        pX = X / X.sum(axis=1)
        ansX = self._anscombe_transform(pX.copy())
        B, istop, itn, r1norm, r2norm, anorm, acond, arnorm, xnorm, var = lsqr(A=ansX, b=y, calc_var=True)

    def _make_response_variable_1_or_negative_1(self, category, tdm):
        """
		Parameters
		----------
		category, str
		tdm, TermDocMatrix

		Returns
		-------
		np.array
		"""
        return (tdm.get_category_names_by_row() == category).astype(int) * 2 - 1

    def _anscombe_transform(self, X):
        """
		Parameters
		----------
		ansX

		Returns
		-------
		csr_matrix
		"""
        return 2 * np.sqrt(np.array(X) + 3.0 / 8)

def get_scores_and_p_values(self, tdm, category):
    """
		Parameters
		----------
		tdm: TermDocMatrix
		category: str, category name

		Returns
		-------
		pd.DataFrame(['coef', 'p-val'])
		"""
    X = tdm._X
    y = self._make_response_variable_1_or_negative_1(category, tdm)
    pX = X / X.sum(axis=1)
    ansX = self._anscombe_transform(pX.copy())
    B, istop, itn, r1norm, r2norm, anorm, acond, arnorm, xnorm, var = lsqr(A=ansX, b=y, calc_var=True)

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

def __segments_from_subtoken_offsets(self, subtoken_offset_df: pd.DataFrame) -> pd.DataFrame:
    return subtoken_offset_df[lambda df: df.SentenceId == df.SentenceId.apply(int)].groupby('SentenceId').apply(lambda gdf: pd.Series({'Length': len(gdf), 'Start': gdf.SubStart.min(), 'End': gdf.SubEnd.max(), 'InputId': gdf.InputId.values})).reset_index().assign(Segment=lambda df: self.__sentence_segments_from_subtokens(df)).groupby('Segment').agg({'Start': 'min', 'End': 'max', 'SentenceId': lambda x: list((int(x) for x in sorted(x))), 'InputId': np.hstack})

class CorpusRunningStats:

    def __init__(self, corpus: 'TermDocMatrix', embedding_width: Optional[int]=None):
        self.corpus = corpus
        self.embedding_width = embedding_width
        self.term_stats = {}
        self.cat_stats = {}
        self.term_cat_stats = {}

    def add(self, term: str, cat: str, embedding: np.array, add_to_category_embeddings: bool) -> 'CorpusRunningStats':
        if self.embedding_width is None:
            self.embedding_width = len(embedding)
        if term in self.term_stats:
            self.term_stats[term].push(embedding)
        else:
            self.term_cat_stats[term] = {}
            self.term_stats[term] = self._get_fresh_running_stats().push(embedding)
        if add_to_category_embeddings:
            if cat in self.cat_stats:
                self.cat_stats[cat].push(embedding)
            else:
                self.cat_stats[cat] = self._get_fresh_running_stats().push(embedding)
        if cat not in self.term_cat_stats[term]:
            self.term_cat_stats[term][cat] = self._get_fresh_running_stats()
        self.term_cat_stats[term][cat].push(embedding)
        return self

    def add_embeddings_to_category(self, embeddings: np.array, cat: str) -> None:
        if len(embeddings):
            embedding = embeddings.mean(axis=0)
            if embedding.shape[0] == self.embedding_width and (not np.any(np.isnan(embedding))):
                if cat in self.cat_stats:
                    self.cat_stats[cat].push(embedding)
                else:
                    self.cat_stats[cat] = self._get_fresh_running_stats().push(embedding)

    def _get_fresh_running_stats(self) -> RunningStatsArray:
        return RunningStatsArray(self.embedding_width)

    def get_term_category_stats(self, term: str, cat: str) -> Optional[RunningStatsArray]:
        return self.term_cat_stats.get(term, {}).get(cat, None)

    def get_category_stats(self, cat: str) -> Optional[RunningStatsArray]:
        return self.cat_stats.get(cat, None)

    def get_term_stats(self, cat: str) -> Optional[RunningStatsArray]:
        return self.term_stats.get(cat, None)

    def available_term_embeddings_from_corpus(self, corpus: 'TermDocMatrix') -> Tuple[List[str], np.array]:
        terms = [term for term in corpus.get_metadata() if term in self.term_stats]
        embeddings = np.array([self.term_stats[term].mean() for term in terms])
        return (terms, embeddings)

def add(self, term: str, cat: str, embedding: np.array, add_to_category_embeddings: bool) -> 'CorpusRunningStats':
    if self.embedding_width is None:
        self.embedding_width = len(embedding)
    if term in self.term_stats:
        self.term_stats[term].push(embedding)
    else:
        self.term_cat_stats[term] = {}
        self.term_stats[term] = self._get_fresh_running_stats().push(embedding)
    if add_to_category_embeddings:
        if cat in self.cat_stats:
            self.cat_stats[cat].push(embedding)
        else:
            self.cat_stats[cat] = self._get_fresh_running_stats().push(embedding)
    if cat not in self.term_cat_stats[term]:
        self.term_cat_stats[term][cat] = self._get_fresh_running_stats()
    self.term_cat_stats[term][cat].push(embedding)
    return self

def add_embeddings_to_category(self, embeddings: np.array, cat: str) -> None:
    if len(embeddings):
        embedding = embeddings.mean(axis=0)
        if embedding.shape[0] == self.embedding_width and (not np.any(np.isnan(embedding))):
            if cat in self.cat_stats:
                self.cat_stats[cat].push(embedding)
            else:
                self.cat_stats[cat] = self._get_fresh_running_stats().push(embedding)

def errfunc(p, x, y):
    return np.power(y - fitfunc(p, x), 2)

class PowerLaw(object):

    def __init__(self):
        self.partial_func = None

    def fit(self, xdata, ydata):
        self.params, _ = leastsq(errfunc, [max(ydata), -1, -0.5], args=(xdata, ydata), maxfev=500)
        return self

    def predict(self, x):
        return fitfunc(self.params, x)

def fit(self, xdata, ydata):
    self.params, _ = leastsq(errfunc, [max(ydata), -1, -0.5], args=(xdata, ydata), maxfev=500)
    return self

def predict(self, x):
    return fitfunc(self.params, x)

class Sigmoidal:

    def __init__(self):
        self.popt = None

    def fit(self, x, y):
        assert len(x) == len(y)
        p0 = [max(y), np.median(x), 1, min(y)]
        self.popt, pcov = curve_fit(sigmoid, x, y, p0, method='dogbox', maxfev=10000)
        return self

    def fit_predict(self, x, y):
        self.fit(x, y)
        return self.predict(x)

    def predict(self, x):
        return sigmoid(x, *self.popt)

def fit(self, x, y):
    assert len(x) == len(y)
    p0 = [max(y), np.median(x), 1, min(y)]
    self.popt, pcov = curve_fit(sigmoid, x, y, p0, method='dogbox', maxfev=10000)
    return self

class DiachronicTermMiner(object):

    def __init__(self, corpus, num_terms=40, start_category=None, timesteps_to_lag=5, seasonality_column=None, model=None):
        self.corpus_ = corpus
        self.num_terms_ = num_terms
        self.sorted_categores_ = np.array(sorted(corpus.get_categories()))
        if timesteps_to_lag > len(self.sorted_categores_):
            raise Exception('Too many timesteps to lag. There are only %s categories' % len(self.sorted_categores_))
        self.timesteps_to_lag_ = timesteps_to_lag
        if start_category is None:
            self.start_category_ = sorted(corpus.get_categories())[timesteps_to_lag]
        else:
            if start_category not in corpus.get_categories():
                raise Exception('start_category %s needs to be a category in corpus' % start_category)
            if start_category in self.sorted_categores_[:timesteps_to_lag]:
                raise Exception('start_category %s should have at least %s categories before it' % (start_category, timesteps_to_lag))
            self.start_category_ = start_category
        if seasonality_column:
            if seasonality_column not in self.corpus_.get_df().columns:
                raise Exception('seasonality_column should be none or a column in the source dataframe')
        self.seasonality_column_ = seasonality_column
        self.model_ = model

    def get_display_dataframe(self):
        """
        Gets list of terms to display that have some interesting diachronic variation.

        Returns
        -------
        pd.DataFrame

        e.g.,
                   term variable  frequency  trending
        2            in   200310        1.0  0.000000
        19          for   200310        1.0  0.000000
        20           to   200311        1.0  0.000000
        """
        X = self.corpus_.get_term_doc_mat()
        categories = pd.Series(self.corpus_.get_category_ids())
        cat_ar = np.array(self.corpus_.get_categories())
        cat_idx_sort = np.argsort(cat_ar)
        if self.seasonality_column_:
            seasonality_ar = np.array(self.corpus_.get_df()[self.seasonality_column_])
        terms = self.corpus_.get_terms()
        category_idx_store = self.corpus_.get_category_index_store()
        data = {}
        seasondata = {}
        for i, cati in enumerate(cat_idx_sort):
            cat = cat_ar[cati]
            if cat >= self.start_category_ and i > self.timesteps_to_lag_:
                neg_cats = self.sorted_categores_[i - self.timesteps_to_lag_:i]
                neg_mask = categories.isin(category_idx_store.getidxstrictbatch(neg_cats)).values
                scores = self._regress_terms(X, cat, categories, category_idx_store, neg_mask, terms)
                data[cat] = scores
                if self.seasonality_column_:
                    neg_cats = set(categories[(seasonality_ar == seasonality_ar[cati]) & (categories != categories[cati])])
                    neg_mask = categories.isin(neg_cats).values
                    scores = self._regress_terms(X, cat, categories, category_idx_store, neg_mask, terms)
                    seasondata[cat] = scores
        coefs = pd.DataFrame(data)
        pos_coefs = coefs.apply(lambda x: (x > 0) * x, axis=1).sum(axis=1).sort_values(ascending=False)
        term_cat_counts = self.corpus_.get_term_freq_df('')[coefs.columns]

        def dense_percentile(x):
            return pd.Series(x / x.max(), index=x.index)
        rank_df = pd.DataFrame({'coefr': dense_percentile(pos_coefs), 'freqr': dense_percentile(term_cat_counts.max(axis=1)), 'coef': pos_coefs, 'freq': term_cat_counts.max(axis=1)})
        if self.seasonality_column_:
            seasoncoefs = pd.DataFrame(seasondata).sum(axis=1)
            rank_df['seasoncoefr'] = dense_percentile(seasoncoefs.sort_values(ascending=False) + np.abs(seasoncoefs.min()))
            weights = [2, 1, 1]
            vals = ['freqr', 'coefr', 'seasoncoefr']

            def gethmean(x):
                if min(x[vals]) == 0:
                    return 0
                return sum(weights) * 1.0 / sum([weights[i] / x[val] for i, val in enumerate(vals)])
            rank_df['hmean'] = rank_df.apply(gethmean, axis=1)
        else:
            beta = 0.5
            rank_df['hmean'] = rank_df.apply(lambda x: 0 if min(x) == 0 else (1 + beta ** 2) * (x.coefr * x.freqr) / (beta ** 2 * x.coefr + x.freqr), axis=1)
        rank_df = rank_df.sort_values(by='hmean', ascending=False)
        display_df = pd.merge(term_cat_counts.loc[rank_df.iloc[:self.num_terms_].index].reset_index().melt(id_vars=['index']).rename(columns={'index': 'term', 'value': 'frequency'}), coefs.loc[rank_df.iloc[:self.num_terms_].index].reset_index().melt(id_vars=['index']).rename(columns={'index': 'term', 'value': 'trending'}), on=['term', 'variable'])
        display_df[display_df['frequency'] == 0] = np.nan
        display_df = display_df.dropna()
        return display_df[display_df.term.isin(rank_df.index)]

    def visualize(self, visualizer=BubbleDiachronicVisualization):
        assert issubclass(visualizer, DiachronicVisualizer)
        return visualizer.visualize(self.get_display_dataframe())

    def _regress_terms(self, X, cat, categories, category_idx_store, neg_mask, terms):
        pos_mask = categories.isin(category_idx_store.getidxstrictbatch([cat])).values
        catX = X[neg_mask | pos_mask, :]
        catY = np.zeros(catX.shape[0]).astype(bool)
        catY[pos_mask[neg_mask | pos_mask]] = True
        scores = pd.Series(self._get_model().fit(catX, catY).coef_[0], index=terms).sort_values(ascending=False)
        return scores

    def _get_model(self):
        return self.model_ if self.model_ is not None else LogisticRegression(penalty='l2')

def dense_percentile(x):
    return pd.Series(x / x.max(), index=x.index)

class BubbleDiachronicVisualization(DiachronicVisualizer):

    @staticmethod
    def visualize(display_df):
        viridis = ['#440154', '#472c7a', '#3b518b', '#2c718e', '#21908d', '#27ad81', '#5cc863', '#aadc32', '#fde725']
        import altair as alt
        color_scale = alt.Scale(domain=(display_df.dropna().trending.min(), 0, display_df.dropna().trending.max()), range=[viridis[0], viridis[len(viridis) // 2], viridis[-1]])
        return alt.Chart(display_df).mark_circle().encode(alt.X('variable'), alt.Y('term'), size='frequency', color=alt.Color('trending:Q', scale=color_scale))

@staticmethod
def visualize(display_df):
    viridis = ['#440154', '#472c7a', '#3b518b', '#2c718e', '#21908d', '#27ad81', '#5cc863', '#aadc32', '#fde725']
    import altair as alt
    color_scale = alt.Scale(domain=(display_df.dropna().trending.min(), 0, display_df.dropna().trending.max()), range=[viridis[0], viridis[len(viridis) // 2], viridis[-1]])
    return alt.Chart(display_df).mark_circle().encode(alt.X('variable'), alt.Y('term'), size='frequency', color=alt.Color('trending:Q', scale=color_scale))

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

class FlexibleNGramFeaturesBase:

    def __init__(self, exclude_ngram_filter: Optional[Callable[[str], bool]]=None, ngram_sizes: Optional[List[int]]=None, text_from_token: Optional[Callable[[str], str]]=None, validate_token: Optional[Callable[[spacy.tokens.Token], bool]]=None, whitespace_substitute: Optional[Callable[[str], str]]=None, exclude_sentence_filter: Optional[Callable[[str], bool]]=None):
        self.exclude_ngram_filter = (lambda x: False) if exclude_ngram_filter is None else exclude_ngram_filter
        self.ngram_sizes = [1, 2, 3] if ngram_sizes is None else ngram_sizes
        self.text_from_token = (lambda tok: tok.lower_) if text_from_token is None else text_from_token
        self.validate_token = (lambda tok: tok.tag_ != '_SP' and tok.orth_.strip() != '') if validate_token is None else validate_token
        self.whitespace_substitute = ' ' if whitespace_substitute is None else whitespace_substitute
        self.exclude_sentence_filter = (lambda s: False) if exclude_sentence_filter is None else exclude_sentence_filter

    def _doc_to_feature_representation(self, doc) -> Dict:
        offset_tokens = {}
        for sent in doc.sents:
            if not self.exclude_sentence_filter(sent):
                for ngram_size in self.ngram_sizes:
                    if len(sent) >= ngram_size:
                        for ngram in sequence_window(sent, ngram_size):
                            if not self.exclude_ngram_filter(ngram):
                                self._add_ngram_to_token_stats(ngram, offset_tokens)
        return offset_tokens

    def _add_ngram_to_token_stats(self, ngram, offset_tokens):
        toktext = self.whitespace_substitute.join((self.text_from_token(tok) for tok in ngram))
        token_stats = offset_tokens.setdefault(toktext, [0, []])
        token_stats[0] += 1
        start = ngram[0].idx
        end = ngram[-1].idx + len(ngram[-1].orth_)
        token_stats[1].append((start, end))

    def _sent_to_token_features(self, sent):
        sent_features = []
        for tok in sent:
            if self.validate_token(tok):
                sent_features.append([tok.idx, tok.idx + len(tok), self.text_from_token(tok)])
        return sent_features

def _doc_to_feature_representation(self, doc) -> Dict:
    offset_tokens = {}
    for sent in doc.sents:
        if not self.exclude_sentence_filter(sent):
            for ngram_size in self.ngram_sizes:
                if len(sent) >= ngram_size:
                    for ngram in sequence_window(sent, ngram_size):
                        if not self.exclude_ngram_filter(ngram):
                            self._add_ngram_to_token_stats(ngram, offset_tokens)
    return offset_tokens

class DispersionRanker(TermRanker):

    def get_ranks(self, label_append: str=f' {metric}') -> pd.DataFrame:
        compare_dispersion_df = get_category_dispersion(self._corpus, metric=metric, corpus_to_parts=corpus_to_parts, non_text=self._use_non_text_features)
        rank_df = pd.DataFrame({cat + label_append: compare_dispersion_df[f'{cat}_{metric}'] for cat_i, cat in enumerate(self._corpus.get_categories())})
        if metric in NULL_VALUES:
            rank_df = rank_df.fillna(NULL_VALUES[metric])
        else:
            for cat in self._corpus.get_categories():
                cat_compare_df = compare_dispersion_df[[f'{cat}_Frequency', f'{cat}_{metric}']].dropna()
                r = pearsonr(x=cat_compare_df.dropna()[f'{cat}_Frequency'], y=cat_compare_df.dropna()[f'{cat}_{metric}']).statistic
                if r < 0:
                    fill = compare_dispersion_df[f'{cat}_{metric}'].min() * impute_null_coef
                else:
                    fill = compare_dispersion_df[f'{cat}_{metric}'].max() / impute_null_coef
                rank_df[cat + label_append] = rank_df[cat + label_append].fillna(fill)
        return rank_df

def get_ranks(self, label_append: str=f' {metric}') -> pd.DataFrame:
    compare_dispersion_df = get_category_dispersion(self._corpus, metric=metric, corpus_to_parts=corpus_to_parts, non_text=self._use_non_text_features)
    rank_df = pd.DataFrame({cat + label_append: compare_dispersion_df[f'{cat}_{metric}'] for cat_i, cat in enumerate(self._corpus.get_categories())})
    if metric in NULL_VALUES:
        rank_df = rank_df.fillna(NULL_VALUES[metric])
    else:
        for cat in self._corpus.get_categories():
            cat_compare_df = compare_dispersion_df[[f'{cat}_Frequency', f'{cat}_{metric}']].dropna()
            r = pearsonr(x=cat_compare_df.dropna()[f'{cat}_Frequency'], y=cat_compare_df.dropna()[f'{cat}_{metric}']).statistic
            if r < 0:
                fill = compare_dispersion_df[f'{cat}_{metric}'].min() * impute_null_coef
            else:
                fill = compare_dispersion_df[f'{cat}_{metric}'].max() / impute_null_coef
            rank_df[cat + label_append] = rank_df[cat + label_append].fillna(fill)
    return rank_df

class CharacteristicScorer(object):

    def __init__(self, term_ranker=AbsoluteFrequencyRanker, background_frequencies=DefaultBackgroundFrequencies, rerank_ranks=False):
        """
		Parameters
		----------
		term_ranker : TermRanker, default is OncePerDocFrequencyRanker
		background_frequencies : BackgroundFrequencies
		rerank_ranks : bool, False by default
			orders scores from 0 to 1 by their dense rank
		"""
        self.term_ranker = term_ranker
        self.background_frequencies = background_frequencies
        self.rerank_ranks = rerank_ranks

    def get_scores(self, corpus):
        raise Exception()

    def _rerank_scores(self, scores):
        ranks = rankdata(scores, 'dense')
        ranks = ranks / ranks.max()
        return (ranks, 0.5)

def _rerank_scores(self, scores):
    ranks = rankdata(scores, 'dense')
    ranks = ranks / ranks.max()
    return (ranks, 0.5)

