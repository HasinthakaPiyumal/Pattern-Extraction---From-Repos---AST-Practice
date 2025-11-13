# Cluster 15

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

def get_labels_and_texts_and_meta(self, metadata):
    data = self.get_labels_and_texts()
    assert len(metadata) == len(data['labels'])
    data['meta'] = list(metadata)
    return data

class DocsAndLabelsFromCorpusSample(DocsAndLabelsFromCorpus):

    def __init__(self, corpus, max_per_category, alternative_text_field=None, seed=None):
        DocsAndLabelsFromCorpus.__init__(self, corpus, alternative_text_field)
        self.max_per_category = max_per_category
        if seed is not None:
            np.random.seed(seed)

    def get_labels_and_texts(self, metadata=None):
        """
        Parameters
        ----------
        metadata : (array like or None)

        Returns
        -------
        {'labels':[], 'texts': []} or {'labels':[], 'texts': [], 'meta': []}
        """
        to_ret = {'categories': self._corpus.get_categories(), 'labels': [], 'texts': []}
        labels = self._corpus._y.astype(int)
        texts = self._get_texts_to_display()
        if self._use_non_text_features:
            to_ret['extra'] = []
            extrafeats = self._corpus.list_extra_features()
        if metadata is not None:
            to_ret['meta'] = []
        for label_i in range(len(self._corpus._category_idx_store)):
            label_indices = np.arange(0, len(labels))[labels == label_i]
            if self.max_per_category < len(label_indices):
                label_indices = np.random.choice(label_indices, self.max_per_category, replace=False)
                to_ret['labels'] += list([int(e) for e in labels[label_indices]])
                to_ret['texts'] += list(texts[label_indices])
                if metadata is not None:
                    to_ret['meta'] += [metadata[i] for i in label_indices]
                if self._use_non_text_features:
                    to_ret['extra'] += [extrafeats[i] for i in label_indices]
        return to_ret

    def get_labels_and_texts_and_meta(self, metadata):
        return self.get_labels_and_texts(metadata)

def get_labels_and_texts_and_meta(self, metadata):
    return self.get_labels_and_texts(metadata)

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

def term_doc_lists(self) -> Dict:
    """
        Returns
        -------
        dict
        """
    doc_ids = self._X.transpose().tolil().rows
    terms = self._term_idx_store.values()
    return dict(zip(terms, doc_ids))

def get_semiotic_square_html(num_terms_semiotic_square, semiotic_square):
    """

    :param num_terms_semiotic_square: int
    :param semiotic_square: SemioticSquare
    :return: str
    """
    semiotic_square_html = None
    if semiotic_square:
        semiotic_square_viz = HTMLSemioticSquareViz(semiotic_square)
        if num_terms_semiotic_square:
            semiotic_square_html = semiotic_square_viz.get_html(num_terms_semiotic_square)
        else:
            semiotic_square_html = semiotic_square_viz.get_html()
    return semiotic_square_html

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

def get_categories(self):
    """
        Returns
        -------
        list
        Category names
        """
    return self._category_idx_store.values()

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

def _update_offsets(self, new_metadata_idx_store, new_metadata_offsets, new_term_idx_store, new_term_offsets):
    term_offsets = self._term_offsets if new_term_offsets is None else new_term_offsets
    metadata_offsets = self._metadata_offsets if new_metadata_offsets is None else new_metadata_offsets
    if new_term_idx_store is not None:
        term_offsets = {k: term_offsets[k] for k in new_term_idx_store.values()}
    if new_metadata_idx_store is not None:
        metadata_offsets = {k: metadata_offsets[k] for k in new_metadata_idx_store.values()}
    return (metadata_offsets, term_offsets)

class TestTermDocMat(TestCase):

    @classmethod
    def setUp(cls):
        cls.tdm = make_a_test_term_doc_matrix()

    def test_get_num_terms(self):
        self.assertEqual(self.tdm.get_num_terms(), self.tdm._X.shape[1])

    def test_get_term_freq_df(self):
        df = self.tdm.get_term_freq_df().sort_values('b freq', ascending=False)[:3]
        self.assertEqual(list(df.index), ['another', 'blah', 'blah blah'])
        self.assertEqual(list(df['a freq']), [0, 0, 0])
        self.assertEqual(list(df['b freq']), [4, 3, 2])
        self.assertEqual(list(self.tdm.get_term_freq_df().sort_values('a freq', ascending=False)[:3]['a freq']), [2, 2, 1])

    def test_single_category_term_doc_matrix_should_error(self):
        """
        with self.assertRaisesRegex(
                expected_exception=CannotCreateATermDocMatrixWithASignleCategoryException,
                expected_regex='Documents must be labeled with more than one category. '
                               'All documents were labeled with category: "a"'):
            single_category_tdm = build_from_category_whitespace_delimited_text(
                [['a', text]
                 for category, text
                 in get_test_categories_and_documents()]
            )
        """
        single_category_tdm = build_from_category_whitespace_delimited_text([['a', text] for category, text in get_test_categories_and_documents()])

    def test_total_unigram_count(self):
        self.assertEqual(self.tdm.get_total_unigram_count(), 36)

    def test_get_term_df(self):
        categories, documents = get_docs_categories()
        df = pd.DataFrame({'category': categories, 'text': documents})
        tdm_factory = TermDocMatrixFromPandas(df, 'category', 'text', nlp=whitespace_nlp)
        term_doc_matrix = tdm_factory.build()
        term_df = term_doc_matrix.get_term_freq_df()
        self.assertEqual(dict(term_df.loc['speak up']), {'??? freq': 2, 'hamlet freq': 0, 'jay-z/r. kelly freq': 1})
        self.assertEqual(dict(term_df.loc['that']), {'??? freq': 0, 'hamlet freq': 2, 'jay-z/r. kelly freq': 0})

    def test_get_terms(self):
        tdm = make_a_test_term_doc_matrix()
        self.assertEqual(tdm.get_terms(), ['hello', 'my', 'name', 'is', 'joe.', 'hello my', 'my name', 'name is', 'is joe.', "i've", 'got', 'a', 'wife', 'and', 'three', 'kids', "i'm", 'working.', "i've got", 'got a', 'a wife', 'wife and', 'and three', 'three kids', 'kids and', "and i'm", "i'm working.", 'in', 'button', 'factory', 'in a', 'a button', 'button factory', 'this', 'another', 'type', 'of', 'document', 'this is', 'is another', 'another type', 'type of', 'of document', 'sentence', 'another sentence', 'sentence in', 'in another', 'another document', "isn't", 'joe', 'here', "name isn't", "isn't joe", 'joe here', 'document.', 'another document.', 'blah', 'blah blah'])

    def test_get_unigram_corpus(self):
        tdm = make_a_test_term_doc_matrix()
        uni_tdm = tdm.get_unigram_corpus()
        term_df = tdm.get_term_freq_df()
        uni_term_df = uni_tdm.get_term_freq_df()
        self.assertEqual(set((term for term in term_df.index if ' ' not in term and "'" not in term)), set(uni_term_df.index))

    def test_remove_entity_tags(self):
        tdm = make_a_test_term_doc_matrix()
        removed_tags_tdm = tdm.remove_entity_tags()
        term_df = tdm.get_term_freq_df()
        removed_tags_term_df = removed_tags_tdm.get_term_freq_df()
        expected_terms = set((term for term in term_df.index if not any((t in SPACY_ENTITY_TAGS for t in term.split()))))
        removed_terms = set(removed_tags_term_df.index)
        (self.assertEqual(expected_terms, removed_terms),)

    def test_get_stoplisted_unigram_corpus(self):
        tdm = make_a_test_term_doc_matrix()
        uni_tdm = tdm.get_stoplisted_unigram_corpus()
        term_df = tdm.get_term_freq_df()
        uni_term_df = uni_tdm.get_term_freq_df()
        (self.assertEqual(set((term for term in term_df.index if ' ' not in term and "'" not in term and (term not in MY_ENGLISH_STOP_WORDS))), set(uni_term_df.index)),)

    def test_allow_single_quotes_in_unigrams(self):
        tdm = make_a_test_term_doc_matrix()
        self.assertEqual(type(tdm.allow_single_quotes_in_unigrams()), type(tdm))
        uni_tdm = tdm.get_stoplisted_unigram_corpus()
        term_df = tdm.get_term_freq_df()
        uni_term_df = uni_tdm.get_term_freq_df()
        (self.assertEqual(set((term for term in term_df.index if ' ' not in term and term not in MY_ENGLISH_STOP_WORDS)), set(uni_term_df.index)),)

    def test_get_stoplisted_unigram_corpus_and_custom(self):
        tdm = make_a_test_term_doc_matrix()
        uni_tdm = tdm.get_stoplisted_unigram_corpus_and_custom(['joe'])
        self._assert_stoplisted_minus_joe(tdm, uni_tdm)
        uni_tdm = tdm.get_stoplisted_unigram_corpus_and_custom('joe')
        self._assert_stoplisted_minus_joe(tdm, uni_tdm)

    def _assert_stoplisted_minus_joe(self, tdm, uni_tdm):
        term_df = tdm.get_term_freq_df()
        uni_term_df = uni_tdm.get_term_freq_df()
        (self.assertEqual(set((term for term in term_df.index if ' ' not in term and 'joe' != term.lower() and ("'" not in term) and (term not in MY_ENGLISH_STOP_WORDS))), set(uni_term_df.index)),)

    def test_term_doc_lists(self):
        term_doc_lists = self.tdm.term_doc_lists()
        self.assertEqual(type(term_doc_lists), dict)
        self.assertEqual(term_doc_lists['this'], [1, 2])
        self.assertEqual(term_doc_lists['another document'], [1])
        self.assertEqual(term_doc_lists['is'], [0, 1, 2])

    def test_remove_terms(self):
        tdm = make_a_test_term_doc_matrix()
        with self.assertRaises(KeyError):
            tdm.remove_terms(['elephant'])
        tdm_removed = tdm.remove_terms(['hello', 'this', 'is'])
        removed_df = tdm_removed.get_term_freq_df()
        df = tdm.get_term_freq_df()
        self.assertEqual(tdm_removed.get_num_docs(), tdm.get_num_docs())
        self.assertEqual(len(removed_df), len(df) - 3)
        self.assertNotIn('hello', removed_df.index)
        self.assertIn('hello', df.index)

    def test_remove_terms_non_text(self):
        hamlet = get_hamlet_term_doc_matrix()
        doc_names = [str(i) for i in range(hamlet.get_num_docs())]
        hamlet_meta = hamlet.add_doc_names_as_metadata(doc_names)
        with self.assertRaises(KeyError):
            hamlet_meta.remove_terms(['xzcljzxsdjlksd'], non_text=True)
        tdm_removed = hamlet_meta.remove_terms(['2', '4', '6'], non_text=True)
        removed_df = tdm_removed.get_metadata_freq_df()
        df = hamlet_meta.get_metadata_freq_df()
        self.assertEqual(tdm_removed.get_num_docs(), hamlet_meta.get_num_docs())
        self.assertEqual(len(removed_df), len(df) - 3)
        self.assertNotIn('2', removed_df.index)
        self.assertIn('2', df.index)

    def test_whitelist_terms(self):
        tdm = make_a_test_term_doc_matrix()
        tdm_removed = tdm.whitelist_terms(['hello', 'this', 'is'])
        removed_df = tdm_removed.get_term_freq_df()
        df = tdm.get_term_freq_df()
        self.assertEqual(tdm_removed.get_num_docs(), tdm.get_num_docs())
        self.assertEqual(len(removed_df), 3)
        self.assertIn('hello', removed_df.index)
        self.assertIn('hello', df.index)
        self.assertIn('my', df.index)
        self.assertNotIn('my', removed_df.index)

    def test_remove_terms_used_less_than_num_docs(self):
        tdm = make_a_test_term_doc_matrix()
        tdm2 = tdm.remove_terms_used_in_less_than_num_docs(2)
        self.assertTrue(all(tdm2.get_term_freq_df().sum(axis=1) >= 2))

    def test_term_scores(self):
        df = self.tdm.get_term_freq_df()
        df['posterior ratio'] = self.tdm.get_posterior_mean_ratio_scores('b')
        scores = self.tdm.get_scaled_f_scores('b', scaler_algo='percentile')
        df['scaled_f_score'] = np.array(scores)
        with self.assertRaises(InvalidScalerException):
            self.tdm.get_scaled_f_scores('a', scaler_algo='x')
        self.tdm.get_scaled_f_scores('a', scaler_algo='percentile')
        self.tdm.get_scaled_f_scores('a', scaler_algo='normcdf')
        df['rudder'] = self.tdm.get_rudder_scores('b')
        df['corner'] = self.tdm.get_corner_scores('b')
        df['fisher oddsratio'], df['fisher pval'] = self.tdm.get_fisher_scores('b')
        self.assertEqual(list(df.sort_values(by='posterior ratio', ascending=False).index[:3]), ['another', 'blah', 'blah blah'])
        self.assertEqual(list(df.sort_values(by='scaled_f_score', ascending=False).index[:3]), ['another', 'blah', 'blah blah'])
        self.assertEqual(list(df.sort_values(by='rudder', ascending=True).index[:3]), ['another', 'blah', 'blah blah'])

    def test_term_scores_background(self):
        hamlet = get_hamlet_term_doc_matrix()
        df = hamlet.get_scaled_f_scores_vs_background(scaler_algo='none')
        self.assertEqual({u'corpus', u'background', u'Scaled f-score'}, set(df.columns))
        self.assertEqual(list(df.index[:3]), ['polonius', 'laertes', 'osric'])
        df = hamlet.get_posterior_mean_ratio_scores_vs_background()
        self.assertEqual({u'corpus', u'background', u'Log Posterior Mean Ratio'}, set(df.columns))
        self.assertEqual(list(df.index[:3]), ['hamlet', 'horatio', 'claudius'])

    def test_keep_only_these_categories(self):
        df = pd.DataFrame(data=np.array(get_docs_categories_semiotic()).T, columns=['category', 'text'])
        corpus = CorpusFromPandas(df, 'category', 'text', nlp=whitespace_nlp).build()
        hamlet_swift_corpus = corpus.keep_only_these_categories(['hamlet', 'swift'])
        self.assertEqual(hamlet_swift_corpus.get_categories(), ['hamlet', 'swift'])
        self.assertGreater(len(corpus.get_terms()), len(hamlet_swift_corpus.get_terms()))
        with self.assertRaises(AssertionError):
            corpus.keep_only_these_categories(['hamlet', 'swift', 'asdjklasfd'])
        corpus.keep_only_these_categories(['hamlet', 'swift', 'asdjklasfd'], True)

    def test_remove_categories(self):
        df = pd.DataFrame(data=np.array(get_docs_categories_semiotic()).T, columns=['category', 'text'])
        corpus = CorpusFromPandas(df, 'category', 'text', nlp=whitespace_nlp).build()
        swiftless = corpus.remove_categories(['swift'])
        swiftless_constructed = CorpusFromPandas(df[df['category'] != 'swift'], 'category', 'text', nlp=whitespace_nlp).build()
        np.testing.assert_equal([i for i in corpus._y if i != corpus.get_categories().index('swift')], swiftless._y)
        self.assertEqual(swiftless._y.shape[0], swiftless._X.shape[0])
        self.assertEqual(swiftless_constructed._X.shape, swiftless._X.shape)
        self.assertEqual(set(swiftless_constructed.get_terms()), set(swiftless.get_terms()))
        pd.testing.assert_series_equal(swiftless_constructed.get_texts(), swiftless.get_texts())
        np.testing.assert_equal(swiftless.get_category_names_by_row(), swiftless_constructed.get_category_names_by_row())

    def test_get_category_names_by_row2(self):
        hamlet = get_hamlet_term_doc_matrix()
        returned = hamlet.get_category_names_by_row()
        self.assertEqual(len(hamlet._y), len(returned))
        np.testing.assert_almost_equal([hamlet.get_categories().index(x) for x in returned], hamlet._y)

    def test_set_background_corpus(self):
        tdm = get_hamlet_term_doc_matrix()
        with self.assertRaisesRegex(Exception, 'The argument.+'):
            tdm.set_background_corpus(1)
        with self.assertRaisesRegex(Exception, 'The argument.+'):
            back_df = pd.DataFrame()
            tdm.set_background_corpus(back_df)
        with self.assertRaisesRegex(Exception, 'The argument.+'):
            back_df = pd.DataFrame({'word': ['a', 'bee'], 'backgasdround': [3, 1]})
            tdm.set_background_corpus(back_df)
        back_df = pd.DataFrame({'word': ['a', 'bee'], 'background': [3, 1]})
        tdm.set_background_corpus(back_df)
        tdm.set_background_corpus(tdm)

    def test_compact(self):
        x = get_hamlet_term_doc_matrix().compact(CompactTerms(minimum_term_count=3))
        self.assertEqual(type(x), TermDocMatrix)

    def _test_get_background_corpus(self):
        tdm = get_hamlet_term_doc_matrix()
        back_df = pd.DataFrame({'word': ['a', 'bee'], 'background': [3, 1]})
        tdm.set_background_corpus(back_df)
        print(tdm.get_background_corpus().to_dict())
        self.assertEqual(tdm.get_background_corpus().to_dict(), back_df.to_dict())
        tdm.set_background_corpus(tdm)
        self.assertEqual(set(tdm.get_background_corpus().to_dict().keys()), set(['word', 'background']))

    def test_log_reg(self):
        hamlet = get_hamlet_term_doc_matrix()
        df = hamlet.get_term_freq_df()
        df['logreg'], acc, baseline = hamlet.get_logistic_regression_coefs_l2('hamlet', clf=LinearRegression())
        l1scores, acc, baseline = hamlet.get_logistic_regression_coefs_l1('hamlet', clf=LinearRegression())
        self.assertGreaterEqual(acc, 0)
        self.assertGreaterEqual(baseline, 0)
        self.assertGreaterEqual(1, acc)
        self.assertGreaterEqual(1, baseline)
        self.assertEqual(list(df.sort_values(by='logreg', ascending=False).index[:3]), ['the', 'starts', 'incorporal'])

    def test_get_category_ids(self):
        hamlet = get_hamlet_term_doc_matrix()
        np.testing.assert_array_equal(hamlet.get_category_ids(), hamlet._y)

    def test_add_metadata(self):
        hamlet = get_hamlet_term_doc_matrix()
        meta_index_store = IndexStore()
        meta_fact = CSRMatrixFactory()
        for i in range(hamlet.get_num_docs()):
            meta_fact[i, i] = meta_index_store.getidx(str(i))
        other_hamlet = hamlet.add_metadata(meta_fact.get_csr_matrix(), meta_index_store)
        assert other_hamlet != hamlet
        meta_index_store = IndexStore()
        meta_fact = CSRMatrixFactory()
        for i in range(hamlet.get_num_docs() - 5):
            meta_fact[i, i] = meta_index_store.getidx(str(i))
        with self.assertRaises(AssertionError):
            hamlet.add_metadata(meta_fact.get_csr_matrix(), meta_index_store)

    def test_add_doc_names_as_metadata(self):
        hamlet = get_hamlet_term_doc_matrix()
        doc_names = [str(i) for i in range(hamlet.get_num_docs())]
        hamlet_meta = hamlet.add_doc_names_as_metadata(doc_names)
        self.assertNotEqual(hamlet, hamlet_meta)
        self.assertEqual(hamlet.get_metadata(), [])
        self.assertEqual(hamlet_meta.get_metadata(), doc_names)
        self.assertEqual(hamlet_meta.get_metadata_doc_mat().shape, (hamlet.get_num_docs(), hamlet.get_num_docs()))
        self.assertNotEqual(hamlet.get_metadata_doc_mat().shape, (hamlet.get_num_docs(), hamlet.get_num_docs()))

    def test_use_doc_labeled_terms_as_metadata(self):
        hamlet = get_hamlet_term_doc_matrix()
        doc_labels = [str(i % 3) for i in range(hamlet.get_num_docs())]
        new_hamlet = hamlet.use_doc_labeled_terms_as_metadata(doc_labels, '++')
        np.testing.assert_array_equal(hamlet.get_term_doc_mat().sum(axis=1), new_hamlet.get_metadata_doc_mat().sum(axis=1))
        metadata_freq_df = new_hamlet.get_metadata_freq_df()
        term_freq_df = hamlet.get_term_freq_df()
        assert term_freq_df.loc['a'].sum() == metadata_freq_df.loc[['0++a', '1++a', '2++a']].values.sum()

    def test_metadata_in_use(self):
        hamlet = get_hamlet_term_doc_matrix()
        self.assertFalse(hamlet.metadata_in_use())
        hamlet_meta = build_hamlet_jz_corpus_with_meta()
        self.assertTrue(hamlet_meta.metadata_in_use())

    def test_get_term_doc_mat(self):
        hamlet = get_hamlet_term_doc_matrix()
        X = hamlet.get_term_doc_mat()
        np.testing.assert_array_equal(X.shape, (hamlet.get_num_docs(), hamlet.get_num_terms()))

    def test_get_metadata_doc_mat(self):
        hamlet_meta = build_hamlet_jz_corpus_with_meta()
        mX = hamlet_meta.get_metadata_doc_mat()
        np.testing.assert_array_equal(mX.shape, (hamlet_meta.get_num_docs(), len(hamlet_meta.get_metadata_freq_df())))

    def test_get_metadata_freq_df(self):
        hamlet_meta = build_hamlet_jz_corpus_with_meta()
        mdf = hamlet_meta.get_metadata_freq_df()
        self.assertEqual(list(mdf.columns), ['hamlet freq', 'jay-z/r. kelly freq'])
        mdf = hamlet_meta.get_metadata_freq_df('')
        self.assertEqual(list(mdf.columns), ['hamlet', 'jay-z/r. kelly'])

    def test_get_metadata(self):
        hamlet_meta = build_hamlet_jz_corpus_with_meta()
        self.assertEqual(hamlet_meta.get_metadata(), ['cat1'])

    def test_get_category_index_store(self):
        hamlet = get_hamlet_term_doc_matrix()
        idxstore = hamlet.get_category_index_store()
        self.assertIsInstance(idxstore, IndexStore)
        self.assertEquals(idxstore.getvals(), {'hamlet', 'not hamlet'})

    def test_use_categories_as_metadata(self):
        hamlet = get_hamlet_term_doc_matrix()
        meta_hamlet = hamlet.use_categories_as_metadata()
        self.assertEqual(hamlet.get_metadata_doc_mat().toarray(), [[0]])
        self.assertEqual(meta_hamlet.get_metadata(), ['hamlet', 'not hamlet'])
        self.assertEqual(meta_hamlet.get_metadata_doc_mat().shape, (meta_hamlet.get_num_docs(), len(meta_hamlet.get_metadata())))
        self.assertTrue(all(meta_hamlet.get_metadata_doc_mat().todense().T[0].astype(bool).A1 == (meta_hamlet.get_category_names_by_row() == 'hamlet')))
        self.assertTrue(all(meta_hamlet.get_metadata_doc_mat().todense().T[1].astype(bool).A1 == (meta_hamlet.get_category_names_by_row() == 'not hamlet')))

    def test_use_categories_as_metadata_and_replace_terms(self):
        hamlet = build_hamlet_jz_corpus_with_meta()
        meta_hamlet = hamlet.use_categories_as_metadata_and_replace_terms()
        np.testing.assert_array_almost_equal(hamlet.get_metadata_doc_mat().toarray(), np.array([[2] for _ in range(8)]))
        self.assertEqual(meta_hamlet.get_metadata(), ['hamlet', 'jay-z/r. kelly'])
        self.assertEqual(meta_hamlet.get_metadata_doc_mat().shape, (meta_hamlet.get_num_docs(), len(meta_hamlet.get_metadata())))
        self.assertTrue(all(meta_hamlet.get_metadata_doc_mat().todense().T[0].astype(bool).A1 == (meta_hamlet.get_category_names_by_row() == 'hamlet')))
        self.assertTrue(all(meta_hamlet.get_metadata_doc_mat().todense().T[1].astype(bool).A1 == (meta_hamlet.get_category_names_by_row() == 'jay-z/r. kelly')))
        np.testing.assert_array_equal(meta_hamlet.get_term_doc_mat().todense(), hamlet.get_metadata_doc_mat().toarray())

    def test_copy_terms_to_metadata(self):
        tdm = get_hamlet_term_doc_matrix()
        tdm_meta = tdm.copy_terms_to_metadata()
        self.assertEqual(tdm.get_metadata_doc_mat().shape, (1, 1))
        self.assertEqual(tdm.get_term_doc_mat().shape, (211, 26875))
        self.assertEqual(tdm_meta.get_term_doc_mat().shape, (211, 26875))
        self.assertEqual(tdm_meta.get_metadata_doc_mat().shape, (211, 26875))
        np.testing.assert_array_equal(tdm.get_term_freq_df().index, tdm_meta.get_metadata_freq_df().index)

    def test_get_num_metadata(self):
        self.assertEqual(get_hamlet_term_doc_matrix().use_categories_as_metadata().get_num_metadata(), 2)

    def test_get_num_categories(self):
        self.assertEqual(get_hamlet_term_doc_matrix().get_num_categories(), 2)

    def test_recategorize(self):
        hamlet = get_hamlet_term_doc_matrix()
        newcats = ['cat' + str(i % 3) for i in range(hamlet.get_num_docs())]
        newhamlet = hamlet.recategorize(newcats)
        self.assertEquals(set(newhamlet.get_term_freq_df('').columns), {'cat0', 'cat1', 'cat2'})
        self.assertEquals(set(hamlet.get_term_freq_df('').columns), {'hamlet', 'not hamlet'})

    def test_get_metadata_count_mat(self):
        corpus = build_hamlet_jz_corpus_with_meta()
        np.testing.assert_array_almost_equal(corpus.get_metadata_count_mat(), [[4, 4]])

    def test_get_metadata_doc_count_df(self):
        corpus = build_hamlet_jz_corpus_with_meta()
        np.testing.assert_array_almost_equal(corpus.get_metadata_doc_count_df(), [[4, 4]])
        self.assertEqual(list(corpus.get_metadata_doc_count_df().columns), ['hamlet freq', 'jay-z/r. kelly freq'])
        self.assertEqual(list(corpus.get_metadata_doc_count_df().index), ['cat1'])

    def test_change_categories(self):
        corpus = build_hamlet_jz_corpus_with_meta()
        with self.assertRaisesRegex(Exception, 'The number of category names passed \\(0\\) needs to equal the number of categories in the corpus \\(2\\)\\.'):
            corpus.change_category_names([])
        with self.assertRaisesRegex(Exception, 'The number of category names passed \\(1\\) needs to equal the number of categories in the corpus \\(2\\)\\.'):
            corpus.change_category_names(['a'])
        new_corpus = corpus.change_category_names(['aaa', 'bcd'])
        self.assertEquals(new_corpus.get_categories(), ['aaa', 'bcd'])
        self.assertEquals(corpus.get_categories(), ['hamlet', 'jay-z/r. kelly'])

def test_term_scores(self):
    df = self.tdm.get_term_freq_df()
    df['posterior ratio'] = self.tdm.get_posterior_mean_ratio_scores('b')
    scores = self.tdm.get_scaled_f_scores('b', scaler_algo='percentile')
    df['scaled_f_score'] = np.array(scores)
    with self.assertRaises(InvalidScalerException):
        self.tdm.get_scaled_f_scores('a', scaler_algo='x')
    self.tdm.get_scaled_f_scores('a', scaler_algo='percentile')
    self.tdm.get_scaled_f_scores('a', scaler_algo='normcdf')
    df['rudder'] = self.tdm.get_rudder_scores('b')
    df['corner'] = self.tdm.get_corner_scores('b')
    df['fisher oddsratio'], df['fisher pval'] = self.tdm.get_fisher_scores('b')
    self.assertEqual(list(df.sort_values(by='posterior ratio', ascending=False).index[:3]), ['another', 'blah', 'blah blah'])
    self.assertEqual(list(df.sort_values(by='scaled_f_score', ascending=False).index[:3]), ['another', 'blah', 'blah blah'])
    self.assertEqual(list(df.sort_values(by='rudder', ascending=True).index[:3]), ['another', 'blah', 'blah blah'])

def test_metadata_in_use(self):
    hamlet = get_hamlet_term_doc_matrix()
    self.assertFalse(hamlet.metadata_in_use())
    hamlet_meta = build_hamlet_jz_corpus_with_meta()
    self.assertTrue(hamlet_meta.metadata_in_use())

class TestDocsAndLabelsFromCorpus(TestCase):

    @classmethod
    def setUp(cls):
        cls.categories, cls.documents = get_docs_categories()
        cls.parsed_docs = []
        for doc in cls.documents:
            cls.parsed_docs.append(whitespace_nlp(doc))
        cls.df = pd.DataFrame({'category': cls.categories, 'parsed': cls.parsed_docs, 'orig': [d.upper() for d in cls.documents]})
        cls.parsed_corpus = CorpusFromParsedDocuments(cls.df, 'category', 'parsed').build()
        cls.corpus = CorpusFromPandas(cls.df, 'category', 'orig', nlp=whitespace_nlp).build()

    def test_categories(self):
        for obj in [DocsAndLabelsFromCorpusSample(self.parsed_corpus, 1), DocsAndLabelsFromCorpus(self.parsed_corpus)]:
            output = obj.get_labels_and_texts()
            self.assertEqual(output['categories'], ['hamlet', 'jay-z/r. kelly', '???'])
            metadata = ['element 0 0', 'element 1 0', 'element 2 0', 'element 3 0', 'element 4 1', 'element 5 1', 'element 6 1', 'element 7 1', 'element 8 1', 'element 9 2']
            output = obj.get_labels_and_texts_and_meta(metadata)
            self.assertEqual(output['categories'], ['hamlet', 'jay-z/r. kelly', '???'])

    def test_main(self):
        d = DocsAndLabelsFromCorpus(self.parsed_corpus)
        output = d.get_labels_and_texts()
        self.assertTrue('texts' in output)
        self.assertTrue('labels' in output)
        self.assertEqual(self.parsed_corpus._y.astype(int).tolist(), list(output['labels']))
        self.assertEqual(self.parsed_corpus.get_texts().tolist(), list(output['texts']))

    def test_extra_features(self):
        corpus = build_hamlet_jz_corpus_with_meta()
        d = DocsAndLabelsFromCorpus(corpus).use_non_text_features()
        metadata = ['meta%s' % i for i in range(corpus.get_num_docs())]
        output = d.get_labels_and_texts_and_meta(metadata)
        extra_val = [{'cat3': 1, 'cat4': 2}, {'cat4': 2}, {'cat5': 1, 'cat3': 2}, {'cat9': 1, 'cat6': 2}, {'cat3': 1, 'cat4': 2}, {'cat1': 2, 'cat2': 1}, {'cat5': 1, 'cat2': 2}, {'cat3': 2, 'cat4': 1}]
        extra_val = [{'cat1': 2}, {'cat1': 2}, {'cat1': 2}, {'cat1': 2}, {'cat1': 2}, {'cat1': 2}, {'cat1': 2}, {'cat1': 2}]
        output['labels'] = list(output['labels'])
        self.assertEqual(output, {'categories': ['hamlet', 'jay-z/r. kelly'], 'texts': ["what art thou that usurp'st this time of night,", 'together with that fair and warlike form', 'in which the majesty of buried denmark', 'did sometimes march? by heaven i charge thee, speak!', 'halt! who goes there?', 'it is i sire tone from brooklyn.', 'well, speak up man what is it?', 'news from the east sire! the best of both worlds has returned!'], 'meta': ['meta0', 'meta1', 'meta2', 'meta3', 'meta4', 'meta5', 'meta6', 'meta7'], 'labels': [0, 0, 0, 0, 1, 1, 1, 1], 'extra': extra_val})

    def test_alternative_text_field(self):
        DocsAndLabelsFromCorpus(self.corpus)
        DocsAndLabelsFromCorpus(self.parsed_corpus)
        with self.assertRaises(CorpusShouldBeParsedCorpusException):
            DocsAndLabelsFromCorpus(self.corpus, alternative_text_field='orig')
        d = DocsAndLabelsFromCorpus(self.parsed_corpus, alternative_text_field='orig')
        self.assertEqual(d.get_labels_and_texts()['texts'][0], d.get_labels_and_texts()['texts'][0].upper())
        d = DocsAndLabelsFromCorpus(self.parsed_corpus)
        self.assertNotEqual(d.get_labels_and_texts()['texts'][0], d.get_labels_and_texts()['texts'][0].upper())
        d = DocsAndLabelsFromCorpusSample(self.parsed_corpus, 2, alternative_text_field='orig', seed=0)
        texts = d.get_labels_and_texts()['texts']
        self.assertEqual(texts[0], texts[0].upper())
        d = DocsAndLabelsFromCorpusSample(self.parsed_corpus, 2)
        self.assertNotEqual(d.get_labels_and_texts()['texts'][0], d.get_labels_and_texts()['texts'][0].upper())

    def test_metadata(self):
        d = DocsAndLabelsFromCorpus(self.parsed_corpus)
        metadata = ['element 0 0', 'element 1 0', 'element 2 0', 'element 3 0', 'element 4 1', 'element 5 1', 'element 6 1', 'element 7 1', 'element 8 1', 'element 9 2']
        output = d.get_labels_and_texts_and_meta(metadata)
        self.assertTrue('texts' in output)
        self.assertTrue('labels' in output)
        self.assertTrue('meta' in output)
        self.assertEqual(output['meta'], metadata)

    def test_max_per_category(self):
        docs_and_labels = DocsAndLabelsFromCorpusSample(self.parsed_corpus, max_per_category=2, seed=0)
        metadata = np.array(['element 0 0', 'element 1 0', 'element 2 0', 'element 3 0', 'element 4 1', 'element 5 1', 'element 6 1', 'element 7 1', 'element 8 1', 'element 9 2'])
        output = docs_and_labels.get_labels_and_texts_and_meta(metadata)
        self.assertTrue('texts' in output)
        self.assertTrue('labels' in output)
        self.assertTrue('meta' in output)
        self.assertTrue('extra' not in output)
        d = {}
        for text, lab, meta in zip(output['texts'], output['labels'], output['meta']):
            d.setdefault(lab, []).append(text)
        for lab, documents in d.items():
            self.assertLessEqual(len(documents), 2)
        json.dumps(d)
        docs_and_labels = DocsAndLabelsFromCorpusSample(self.parsed_corpus, max_per_category=2)
        output = docs_and_labels.get_labels_and_texts()
        self.assertTrue('texts' in output)
        self.assertTrue('labels' in output)
        self.assertTrue('meta' not in output)
        self.assertTrue('extra' not in output)
        d = {}
        for text, lab in zip(output['texts'], output['labels']):
            d.setdefault(lab, []).append(text)
        for lab, documents in d.items():
            self.assertLessEqual(len(documents), 2)
        json.dumps(d)
        docs_and_labels = DocsAndLabelsFromCorpusSample(self.parsed_corpus, max_per_category=2).use_non_text_features()
        output = docs_and_labels.get_labels_and_texts()
        self.assertTrue('texts' in output)
        self.assertTrue('labels' in output)
        self.assertTrue('meta' not in output)
        self.assertTrue('extra' in output)
        d = {}
        for text, lab in zip(output['texts'], output['labels']):
            d.setdefault(lab, []).append(text)
        for lab, documents in d.items():
            self.assertLessEqual(len(documents), 2)
        json.dumps(d)

def test_categories(self):
    for obj in [DocsAndLabelsFromCorpusSample(self.parsed_corpus, 1), DocsAndLabelsFromCorpus(self.parsed_corpus)]:
        output = obj.get_labels_and_texts()
        self.assertEqual(output['categories'], ['hamlet', 'jay-z/r. kelly', '???'])
        metadata = ['element 0 0', 'element 1 0', 'element 2 0', 'element 3 0', 'element 4 1', 'element 5 1', 'element 6 1', 'element 7 1', 'element 8 1', 'element 9 2']
        output = obj.get_labels_and_texts_and_meta(metadata)
        self.assertEqual(output['categories'], ['hamlet', 'jay-z/r. kelly', '???'])

def test_main(self):
    d = DocsAndLabelsFromCorpus(self.parsed_corpus)
    output = d.get_labels_and_texts()
    self.assertTrue('texts' in output)
    self.assertTrue('labels' in output)
    self.assertEqual(self.parsed_corpus._y.astype(int).tolist(), list(output['labels']))
    self.assertEqual(self.parsed_corpus.get_texts().tolist(), list(output['texts']))

def test_alternative_text_field(self):
    DocsAndLabelsFromCorpus(self.corpus)
    DocsAndLabelsFromCorpus(self.parsed_corpus)
    with self.assertRaises(CorpusShouldBeParsedCorpusException):
        DocsAndLabelsFromCorpus(self.corpus, alternative_text_field='orig')
    d = DocsAndLabelsFromCorpus(self.parsed_corpus, alternative_text_field='orig')
    self.assertEqual(d.get_labels_and_texts()['texts'][0], d.get_labels_and_texts()['texts'][0].upper())
    d = DocsAndLabelsFromCorpus(self.parsed_corpus)
    self.assertNotEqual(d.get_labels_and_texts()['texts'][0], d.get_labels_and_texts()['texts'][0].upper())
    d = DocsAndLabelsFromCorpusSample(self.parsed_corpus, 2, alternative_text_field='orig', seed=0)
    texts = d.get_labels_and_texts()['texts']
    self.assertEqual(texts[0], texts[0].upper())
    d = DocsAndLabelsFromCorpusSample(self.parsed_corpus, 2)
    self.assertNotEqual(d.get_labels_and_texts()['texts'][0], d.get_labels_and_texts()['texts'][0].upper())

def test_metadata(self):
    d = DocsAndLabelsFromCorpus(self.parsed_corpus)
    metadata = ['element 0 0', 'element 1 0', 'element 2 0', 'element 3 0', 'element 4 1', 'element 5 1', 'element 6 1', 'element 7 1', 'element 8 1', 'element 9 2']
    output = d.get_labels_and_texts_and_meta(metadata)
    self.assertTrue('texts' in output)
    self.assertTrue('labels' in output)
    self.assertTrue('meta' in output)
    self.assertEqual(output['meta'], metadata)

def test_max_per_category(self):
    docs_and_labels = DocsAndLabelsFromCorpusSample(self.parsed_corpus, max_per_category=2, seed=0)
    metadata = np.array(['element 0 0', 'element 1 0', 'element 2 0', 'element 3 0', 'element 4 1', 'element 5 1', 'element 6 1', 'element 7 1', 'element 8 1', 'element 9 2'])
    output = docs_and_labels.get_labels_and_texts_and_meta(metadata)
    self.assertTrue('texts' in output)
    self.assertTrue('labels' in output)
    self.assertTrue('meta' in output)
    self.assertTrue('extra' not in output)
    d = {}
    for text, lab, meta in zip(output['texts'], output['labels'], output['meta']):
        d.setdefault(lab, []).append(text)
    for lab, documents in d.items():
        self.assertLessEqual(len(documents), 2)
    json.dumps(d)
    docs_and_labels = DocsAndLabelsFromCorpusSample(self.parsed_corpus, max_per_category=2)
    output = docs_and_labels.get_labels_and_texts()
    self.assertTrue('texts' in output)
    self.assertTrue('labels' in output)
    self.assertTrue('meta' not in output)
    self.assertTrue('extra' not in output)
    d = {}
    for text, lab in zip(output['texts'], output['labels']):
        d.setdefault(lab, []).append(text)
    for lab, documents in d.items():
        self.assertLessEqual(len(documents), 2)
    json.dumps(d)
    docs_and_labels = DocsAndLabelsFromCorpusSample(self.parsed_corpus, max_per_category=2).use_non_text_features()
    output = docs_and_labels.get_labels_and_texts()
    self.assertTrue('texts' in output)
    self.assertTrue('labels' in output)
    self.assertTrue('meta' not in output)
    self.assertTrue('extra' in output)
    d = {}
    for text, lab in zip(output['texts'], output['labels']):
        d.setdefault(lab, []).append(text)
    for lab, documents in d.items():
        self.assertLessEqual(len(documents), 2)
    json.dumps(d)

class TestHTMLSemioticSquareViz(TestCase):

    def test_get_html(self):
        semsq = get_test_semiotic_square()
        html_default = HTMLSemioticSquareViz(semsq).get_html()
        html_6 = HTMLSemioticSquareViz(semsq).get_html(num_terms=6)
        self.assertNotEqual(html_default, html_6)

def test_get_html(self):
    semsq = get_test_semiotic_square()
    html_default = HTMLSemioticSquareViz(semsq).get_html()
    html_6 = HTMLSemioticSquareViz(semsq).get_html(num_terms=6)
    self.assertNotEqual(html_default, html_6)

class TestSemioticSquare(TestCase):

    def test_constructor(self):
        df = pd.DataFrame(data=np.array(get_docs_categories_semiotic()).T, columns=['category', 'text'])
        corpus = CorpusFromPandas(df, 'category', 'text', nlp=whitespace_nlp).build()
        SemioticSquare(corpus, 'hamlet', 'jay-z/r. kelly', ['swift'])
        with self.assertRaises(AssertionError):
            SemioticSquare(corpus, 'XXXhamlet', 'jay-z/r. kelly', ['swift'])
        with self.assertRaises(AssertionError):
            SemioticSquare(corpus, 'hamlet', 'jay-z/r. kellyXXX', ['swift'])
        with self.assertRaises(AssertionError):
            SemioticSquare(corpus, 'hamlet', 'jay-z/r. kelly', ['swift', 'asd'])
        with self.assertRaises(EmptyNeutralCategoriesError):
            SemioticSquare(corpus, 'hamlet', 'jay-z/r. kelly', [])

    def test_get_labels(self):
        corpus = get_test_corpus()
        semsq = SemioticSquare(corpus, 'hamlet', 'jay-z/r. kelly', ['swift'])
        a, b = ('hamlet', 'jay-z/r. kelly')
        default_labels = {'a': a, 'not_a': 'Not ' + a, 'b': b, 'not_b': 'Not ' + b, 'a_and_b': a + ' + ' + b, 'not_a_and_not_b': 'Not ' + a + ' + Not ' + b, 'a_and_not_b': a + ' + Not ' + b, 'b_and_not_a': 'Not ' + a + ' + ' + b}
        labels = semsq.get_labels()
        for name, default_label in default_labels.items():
            self.assertTrue(name + '_label' in labels)
            self.assertEqual(labels[name + '_label'], default_label)
        semsq = SemioticSquare(corpus, 'hamlet', 'jay-z/r. kelly', ['swift'], labels={'a': 'AAA'})
        labels = semsq.get_labels()
        for name, default_label in default_labels.items():
            if name == 'a':
                self.assertEqual(labels[name + '_label'], 'AAA')
            else:
                self.assertTrue(name + '_label' in labels)
                self.assertEqual(labels[name + '_label'], default_label)

    def test_get_lexicons(self):
        semsq = get_test_semiotic_square()
        lexicons = semsq.get_lexicons()
        for category in self.categories():
            self.assertIn(category, lexicons)
            self.assertLessEqual(len(lexicons[category]), 10)
        lexicons = semsq.get_lexicons(5)
        for category in self.categories():
            self.assertIn(category, lexicons)
            self.assertLessEqual(len(lexicons[category]), 5)

    def test_get_axes(self):
        semsq = get_test_semiotic_square()
        ax = semsq.get_axes()
        self.assertEqual(list(sorted(ax.index)), list(sorted(semsq.term_doc_matrix_.get_terms())))

    def categories(self):
        return ['a', 'b', 'not_a', 'not_b', 'a_and_not_b', 'b_and_not_a', 'a_and_b', 'not_a_and_not_b']

def test_get_axes(self):
    semsq = get_test_semiotic_square()
    ax = semsq.get_axes()
    self.assertEqual(list(sorted(ax.index)), list(sorted(semsq.term_doc_matrix_.get_terms())))

class TestParsedCorpus(TestCase):

    @classmethod
    def setUp(cls):
        cls.categories, cls.documents = get_docs_categories()
        cls.parsed_docs = []
        for doc in cls.documents:
            cls.parsed_docs.append(whitespace_nlp(doc))
        cls.df = pd.DataFrame({'category': cls.categories, 'author': ['a', 'a', 'c', 'c', 'c', 'c', 'd', 'd', 'e', 'e'], 'parsed': cls.parsed_docs, 'document_lengths': [len(doc) for doc in cls.documents]})
        cls.corpus = CorpusFromParsedDocuments(cls.df, 'category', 'parsed').build()

    def test_get_text(self):
        self.assertEqual(len([x for x in self.corpus.get_texts()]), len(self.documents))
        self.assertEqual([str(x) for x in self.corpus.get_texts()][0], "what art thou that usurp'st this time of night,")

    def test_get_field(self):
        self.assertEqual(list(self.corpus.get_field('author')), list(self.df.author))

    def test_get_parsed_docs(self):
        doc = [x for x in self.corpus.get_parsed_docs()][0]
        doc.sents

    def test_get_unigram_corpus(self):
        unicorp = self.corpus.get_unigram_corpus()
        self.assertEqual(len([x for x in unicorp.get_texts()]), len(self.documents))
        self.assertEqual([str(x) for x in unicorp.get_texts()][0], "what art thou that usurp'st this time of night,")

    def test_search(self):
        self.assertEqual(len(self.corpus.search('bigram')), 1)
        df = self.corpus.search('bigram')
        d = dict(df.iloc[0])
        self.assertEqual(d['category'], '???')
        self.assertEqual(d['document_lengths'], 44)
        self.assertEqual(str(d['parsed']), 'speak up, speak up, this is a repeat bigram.')
        self.assertEqual(len(self.corpus.search('the')), 2)

    def test_term_group_freq_df(self):
        """
		Returns
		-------
		return pd.DataFrame indexed on terms with columns giving how many attributes in convention_df

		"""
        group_df = self.corpus.term_group_freq_df('author')
        self.assertEqual(set(group_df.index), set(self.corpus._term_idx_store.values()))
        self.assertEqual(dict(group_df.loc['of']), {'??? freq': 0, 'hamlet freq': 2, 'jay-z/r. kelly freq': 1})
        self.assertEqual(dict(group_df.loc['speak up']), {'??? freq': 1, 'hamlet freq': 0, 'jay-z/r. kelly freq': 1})

def test_search(self):
    self.assertEqual(len(self.corpus.search('bigram')), 1)
    df = self.corpus.search('bigram')
    d = dict(df.iloc[0])
    self.assertEqual(d['category'], '???')
    self.assertEqual(d['document_lengths'], 44)
    self.assertEqual(str(d['parsed']), 'speak up, speak up, this is a repeat bigram.')
    self.assertEqual(len(self.corpus.search('the')), 2)

def test_term_group_freq_df(self):
    """
		Returns
		-------
		return pd.DataFrame indexed on terms with columns giving how many attributes in convention_df

		"""
    group_df = self.corpus.term_group_freq_df('author')
    self.assertEqual(set(group_df.index), set(self.corpus._term_idx_store.values()))
    self.assertEqual(dict(group_df.loc['of']), {'??? freq': 0, 'hamlet freq': 2, 'jay-z/r. kelly freq': 1})
    self.assertEqual(dict(group_df.loc['speak up']), {'??? freq': 1, 'hamlet freq': 0, 'jay-z/r. kelly freq': 1})

class TestCorpusFromParsedDocuments(TestCase):

    @classmethod
    def setUp(cls):
        cls.categories, cls.documents = get_docs_categories()
        cls.parsed_docs = []
        for doc in cls.documents:
            cls.parsed_docs.append(whitespace_nlp(doc))
        cls.df = pd.DataFrame({'category': cls.categories, 'parsed': cls.parsed_docs})
        cls.corpus_fact = CorpusFromParsedDocuments(cls.df, 'category', 'parsed')

    def test_same_as_term_doc_matrix(self):
        term_doc_matrix = build_term_doc_matrix()
        corpus = self._make_political_corpus()
        self.assertEqual(term_doc_matrix._X.shape, corpus._X.shape)
        self.assertEqual((corpus._X != term_doc_matrix._X).nnz, 0)
        corpus_scores = corpus.get_scaled_f_scores('democrat')
        term_doc_matrix_scores = corpus.get_scaled_f_scores('democrat')
        self.assertTrue(np.array_equal(term_doc_matrix_scores, corpus_scores))

    def _make_political_corpus(self):
        clean = clean_function_factory()
        data = []
        for party, speech in iter_party_speech_pairs():
            cleaned_speech = clean(speech)
            if cleaned_speech and cleaned_speech != '':
                parsed_speech = whitespace_nlp(cleaned_speech)
                data.append({'party': party, 'text': parsed_speech})
        corpus = CorpusFromParsedDocuments(pd.DataFrame(data), category_col='party', parsed_col='text').build()
        return corpus

    def test_get_y_and_populate_category_idx_store(self):
        corpus = self.corpus_fact.build()
        self.assertEqual([0, 0, 0, 0, 1, 1, 1, 1, 1, 2], list(corpus._y))
        self.assertEqual([(0, 'hamlet'), (1, 'jay-z/r. kelly'), (2, '???')], list(sorted(list(corpus._category_idx_store.items()))))

    def test_get_term_idx_and_x(self):
        docs = [whitespace_nlp('aa aa bb.'), whitespace_nlp('bb aa a.')]
        df = pd.DataFrame({'category': ['a', 'b'], 'parsed': docs})
        corpus_fact = CorpusFromParsedDocuments(df, category_col='category', parsed_col='parsed')
        corpus = corpus_fact.build()
        kvs = list(corpus_fact._term_idx_store.items())
        keys = [k for k, v in kvs]
        values = [v for k, v in kvs]
        self.assertEqual(sorted(keys), list(range(7)))
        self.assertEqual(sorted(values), ['a', 'aa', 'aa a', 'aa aa', 'aa bb', 'bb', 'bb aa'])

        def assert_word_in_doc_cnt(doc, word, count):
            self.assertEqual(corpus._X[doc, corpus._term_idx_store.getidx(word)], count)
        assert_word_in_doc_cnt(0, 'aa', 2)
        assert_word_in_doc_cnt(0, 'bb', 1)
        assert_word_in_doc_cnt(0, 'aa aa', 1)
        assert_word_in_doc_cnt(0, 'aa bb', 1)
        assert_word_in_doc_cnt(0, 'bb aa', 0)
        assert_word_in_doc_cnt(1, 'bb', 1)
        assert_word_in_doc_cnt(1, 'aa', 1)
        assert_word_in_doc_cnt(1, 'a', 1)
        assert_word_in_doc_cnt(1, 'bb aa', 1)
        assert_word_in_doc_cnt(1, 'aa aa', 0)
        assert_word_in_doc_cnt(1, 'aa a', 1)
        self.assertTrue(isinstance(corpus, ParsedCorpus))

    def test_hamlet(self):
        raw_docs = get_hamlet_docs()
        categories = [get_hamlet_snippet_binary_category(doc) for doc in raw_docs]
        docs = [whitespace_nlp(doc) for doc in raw_docs]
        df = pd.DataFrame({'category': categories, 'parsed': docs})
        corpus_fact = CorpusFromParsedDocuments(df, 'category', 'parsed')
        corpus = corpus_fact.build()
        tdf = corpus.get_term_freq_df()
        self.assertEqual(list(tdf.loc['play']), [37, 5])
        self.assertFalse(any(corpus.search('play').apply(lambda x: 'plfay' in str(x['parsed']), axis=1)))
        self.assertTrue(all(corpus.search('play').apply(lambda x: 'play' in str(x['parsed']), axis=1)))
        play_term_idx = corpus_fact._term_idx_store.getidx('play')
        play_X = corpus._X.todok()[:, play_term_idx]
        self.assertEqual(play_X.sum(), 37 + 5)

def test_same_as_term_doc_matrix(self):
    term_doc_matrix = build_term_doc_matrix()
    corpus = self._make_political_corpus()
    self.assertEqual(term_doc_matrix._X.shape, corpus._X.shape)
    self.assertEqual((corpus._X != term_doc_matrix._X).nnz, 0)
    corpus_scores = corpus.get_scaled_f_scores('democrat')
    term_doc_matrix_scores = corpus.get_scaled_f_scores('democrat')
    self.assertTrue(np.array_equal(term_doc_matrix_scores, corpus_scores))

class TestHTMLVisualizationAssembly(TestCase):

    def get_params(self, param_dict={}):
        params = ['1000', '600', 'null', 'null', 'true', 'false', 'false', 'false', 'false', 'true', 'false', 'false', 'true', '0.1', 'false', 'undefined', 'undefined', 'getDataAndInfo()', 'true', 'false', 'null', 'null', 'null', 'null', 'true', 'false', 'true', 'false', 'null', 'null', '10', 'null', 'null', 'null', 'false', 'true', 'true', '"' + DEFAULT_DIV_ID + '"', 'null', 'false', 'false', '"' + DEFAULT_D3_AXIS_VALUE_FORMAT + '"', '"' + DEFAULT_D3_AXIS_VALUE_FORMAT + '"', 'false', '-1', 'true', 'false', 'true', 'false', 'false', 'false', 'true', 'null', 'null', 'null', 'false', 'null', 'undefined', 'undefined', 'undefined', 'undefined', 'undefined', 'undefined', 'undefined', '14', '0', 'null', '"Term"', 'true', 'false', 'false', 'undefined', 'null', '"document"', '"documents"', 'null', 'false', 'null', 'null', 'null', 'null', 'null', 'null', 'false']
        for i, val in param_dict.items():
            params[i] = val
        return 'buildViz(' + ',\n'.join(params) + ');\n'

    def make_assembler(self):
        scatterplot_structure = ScatterplotStructure(self.make_adapter())
        return BasicHTMLFromScatterplotStructure(scatterplot_structure)

    def make_adapter(self):
        words_dict = {'info': {'not_category_name': 'Republican', 'category_name': 'Democratic'}, 'data': [{'y': 0.33763837638376387, 'term': 'crises', 'ncat25k': 0, 'cat25k': 1, 'x': 0.0, 's': 0.878755930416447}, {'y': 0.5, 'term': 'something else', 'ncat25k': 0, 'cat25k': 1, 'x': 0.0, 's': 0.5}]}
        visualization_data = VizDataAdapter(words_dict)
        return visualization_data

    def test_main(self):
        assembler = self.make_assembler()
        html = assembler.to_html()
        if sys.version_info.major == 2:
            self.assertEqual(type(html), unicode)
        else:
            self.assertEqual(type(html), str)
        self.assertFalse('<!-- EXTRA LIBS -->' in html)
        self.assertFalse('<!-- INSERT SCRIPT -->' in html)
        self.assertTrue('<!-- INSERT SEMIOTIC SQUARE -->' in html)
        self.assertTrue('Republican' in html)

    def test_semiotic_square(self):
        semsq = get_test_semiotic_square()
        assembler = self.make_assembler()
        html = assembler.to_html(html_base=HTMLSemioticSquareViz(semsq).get_html(num_terms=6))
        if sys.version_info.major == 2:
            self.assertEqual(type(html), unicode)
        else:
            self.assertEqual(type(html), str)
        self.assertFalse('<!-- EXTRA LIBS -->' in html)
        self.assertFalse('<!-- INSERT SCRIPT -->' in html)
        self.assertTrue('Republican' in html)

    def test_save_svg_button(self):
        scatterplot_structure = ScatterplotStructure(self.make_adapter(), save_svg_button=True)
        assembly = BasicHTMLFromScatterplotStructure(scatterplot_structure)
        html = assembly.to_html()
        self.assertEqual(scatterplot_structure.call_build_visualization_in_javascript(), self.get_params({11: 'true'}))
        self.assertFalse('<!-- INSERT SCRIPT -->' in html)

    def test_protocol_is_https(self):
        html = self.make_assembler().to_html(protocol='https')
        self.assertTrue(self._https_script_is_present(html))
        self.assertFalse(self._http_script_is_present(html))

    def _test_protocol_is_http(self):
        html = self.make_assembler().to_html(protocol='http')
        self.assertFalse(self._https_script_is_present(html))
        self.assertTrue(self._http_script_is_present(html))

    def _http_script_is_present(self, html):
        return 'src="http://' in html

    def _https_script_is_present(self, html):
        return 'src="https://' in html

    def test_protocol_default_d3_url(self):
        html = self.make_assembler().to_html()
        self.assertTrue(DEFAULT_D3_URL in html)
        html = self.make_assembler().to_html(d3_url='d3.js')
        self.assertTrue(DEFAULT_D3_URL not in html)
        self.assertTrue('d3.js' in html)

    def test_protocol_default_d3_chromatic_url(self):
        html = self.make_assembler().to_html()
        self.assertTrue(DEFAULT_D3_SCALE_CHROMATIC in html)
        html = self.make_assembler().to_html(d3_scale_chromatic_url='d3-scale-chromatic.v1.min.js')
        self.assertTrue(DEFAULT_D3_SCALE_CHROMATIC not in html)
        self.assertTrue('d3-scale-chromatic.v1.min.js' in html)

    def test_protocol_defaults_to_http(self):
        self.assertEqual(self.make_assembler().to_html(protocol='http'), self.make_assembler().to_html())

    def test_raise_invalid_protocol_exception(self):
        with self.assertRaisesRegexp(BaseException, 'Invalid protocol: ftp.  Protocol must be either http or https.'):
            self.make_assembler().to_html(protocol='ftp')

    def test_height_width_default(self):
        scatterplot_structure = ScatterplotStructure(self.make_adapter())
        self.assertEqual(scatterplot_structure.call_build_visualization_in_javascript(), self.get_params())

    def test_color(self):
        visualization_data = self.make_adapter()
        self.assertEqual(ScatterplotStructure(visualization_data, color='d3.interpolatePurples').call_build_visualization_in_javascript(), self.get_params({3: 'd3.interpolatePurples'}))

    def test_full_doc(self):
        visualization_data = self.make_adapter()
        self.assertEqual(ScatterplotStructure(visualization_data, use_full_doc=True).call_build_visualization_in_javascript(), self.get_params({5: 'true'}))

    def test_grey_zero_scores(self):
        visualization_data = self.make_adapter()
        self.assertEqual(ScatterplotStructure(visualization_data, grey_zero_scores=True).call_build_visualization_in_javascript(), self.get_params({6: 'true'}))

    def test_chinese_mode(self):
        visualization_data = self.make_adapter()
        self.assertEqual(ScatterplotStructure(visualization_data, asian_mode=True).call_build_visualization_in_javascript(), self.get_params({7: 'true'}))

    def test_reverse_sort_scores_for_not_category(self):
        visualization_data = self.make_adapter()
        self.assertEqual(ScatterplotStructure(visualization_data, reverse_sort_scores_for_not_category=False).call_build_visualization_in_javascript(), self.get_params({12: 'false'}))

    def test_height_width_nondefault(self):
        visualization_data = self.make_adapter()
        self.assertEqual(ScatterplotStructure(visualization_data, width_in_pixels=1000).call_build_visualization_in_javascript(), self.get_params({0: '1000'}))
        self.assertEqual(ScatterplotStructure(visualization_data, height_in_pixels=60).call_build_visualization_in_javascript(), self.get_params({1: '60'}))
        self.assertEqual(ScatterplotStructure(visualization_data, width_in_pixels=1000, height_in_pixels=60).call_build_visualization_in_javascript(), self.get_params({0: '1000', 1: '60'}))

    def test_use_non_text_features(self):
        visualization_data = self.make_adapter()
        self.assertEqual(ScatterplotStructure(visualization_data, width_in_pixels=1000, height_in_pixels=60, use_non_text_features=True).call_build_visualization_in_javascript(), self.get_params({0: '1000', 1: '60', 8: 'true'}))

    def test_show_characteristic(self):
        visualization_data = self.make_adapter()
        self.assertEqual(ScatterplotStructure(visualization_data, width_in_pixels=1000, height_in_pixels=60, show_characteristic=False).call_build_visualization_in_javascript(), self.get_params({0: '1000', 1: '60', 9: 'false'}))

    def test_max_snippets(self):
        visualization_data = self.make_adapter()
        self.assertEqual(ScatterplotStructure(visualization_data, width_in_pixels=1000, height_in_pixels=60, max_snippets=None).call_build_visualization_in_javascript(), self.get_params({0: '1000', 1: '60'}))
        self.assertEqual(ScatterplotStructure(visualization_data, width_in_pixels=1000, height_in_pixels=60, max_snippets=100).call_build_visualization_in_javascript(), self.get_params({0: '1000', 1: '60', 2: '100'}))

    def test_word_vec_use_p_vals(self):
        visualization_data = self.make_adapter()
        self.assertEqual(ScatterplotStructure(visualization_data, width_in_pixels=1000, height_in_pixels=60, word_vec_use_p_vals=True).call_build_visualization_in_javascript(), self.get_params({0: '1000', 1: '60', 10: 'true'}))

    def test_max_p_val(self):
        visualization_data = self.make_adapter()
        self.assertEqual(ScatterplotStructure(visualization_data, width_in_pixels=1000, height_in_pixels=60, word_vec_use_p_vals=True, max_p_val=0.01).call_build_visualization_in_javascript(), self.get_params({0: '1000', 1: '60', 10: 'true', 13: '0.01'}))

    def test_p_value_colors(self):
        visualization_data = self.make_adapter()
        self.assertEqual(ScatterplotStructure(visualization_data, width_in_pixels=1000, height_in_pixels=60, word_vec_use_p_vals=True, p_value_colors=True).call_build_visualization_in_javascript(), self.get_params({0: '1000', 1: '60', 10: 'true', 14: 'true'}))

    def test_x_label(self):
        visualization_data = self.make_adapter()
        self.assertEqual(ScatterplotStructure(visualization_data, width_in_pixels=1000, height_in_pixels=60, x_label='x label').call_build_visualization_in_javascript(), self.get_params({0: '1000', 1: '60', 15: '"x label"'}))

    def test_y_label(self):
        visualization_data = self.make_adapter()
        self.assertEqual(ScatterplotStructure(visualization_data, width_in_pixels=1000, height_in_pixels=60, y_label='y label').call_build_visualization_in_javascript(), self.get_params({0: '1000', 1: '60', 16: '"y label"'}))

    def test_full_data(self):
        visualization_data = self.make_adapter()
        full_data = 'customFullDataFunction()'
        self.assertEqual(ScatterplotStructure(visualization_data, full_data=full_data).call_build_visualization_in_javascript(), self.get_params({17: full_data}))

    def test_show_top_terms(self):
        visualization_data = self.make_adapter()
        self.assertEqual(ScatterplotStructure(visualization_data, show_top_terms=False).call_build_visualization_in_javascript(), self.get_params({18: 'false'}))
        visualization_data = self.make_adapter()
        self.assertEqual(ScatterplotStructure(visualization_data, show_top_terms=True).call_build_visualization_in_javascript(), self.get_params({18: 'true'}))
        self.assertEqual(ScatterplotStructure(visualization_data).call_build_visualization_in_javascript(), self.get_params({18: 'true'}))

    def test_show_neutral(self):
        visualization_data = self.make_adapter()
        self.assertEqual(ScatterplotStructure(visualization_data).call_build_visualization_in_javascript(), self.get_params({19: 'false'}))
        self.assertEqual(ScatterplotStructure(visualization_data, show_neutral=True).call_build_visualization_in_javascript(), self.get_params({19: 'true'}))

    def test_get_tooltip_content(self):
        visualization_data = self.make_adapter()
        f = "(function(x) {return 'Original X: ' + x.ox;})"
        self.assertEqual(ScatterplotStructure(visualization_data, get_tooltip_content=f).call_build_visualization_in_javascript(), self.get_params({20: f}))

    def test_x_axis_labels(self):
        visualization_data = self.make_adapter()
        self.assertEqual(ScatterplotStructure(visualization_data, x_axis_values=[1, 2, 3]).call_build_visualization_in_javascript(), self.get_params({21: '[1, 2, 3]'}))

    def test_y_axis_labels(self):
        visualization_data = self.make_adapter()
        self.assertEqual(ScatterplotStructure(visualization_data, y_axis_values=[4, 5, 6]).call_build_visualization_in_javascript(), self.get_params({22: '[4, 5, 6]'}))

    def test_color_func(self):
        visualization_data = self.make_adapter()
        color_func = 'function colorFunc(d) {var c = d3.hsl(d3.interpolateRdYlBu(d.x)); c.s *= d.y;\treturn c;}'
        self.assertEqual(ScatterplotStructure(visualization_data, color_func=color_func).call_build_visualization_in_javascript(), self.get_params({23: color_func}))

    def test_show_axes(self):
        visualization_data = self.make_adapter()
        self.assertEqual(ScatterplotStructure(visualization_data, show_axes=False).call_build_visualization_in_javascript(), self.get_params({24: 'false'}))

    def test_show_extra(self):
        visualization_data = self.make_adapter()
        self.assertEqual(ScatterplotStructure(visualization_data, show_extra=True).call_build_visualization_in_javascript(), self.get_params({25: 'true'}))

    def test_do_censor_points(self):
        visualization_data = self.make_adapter()
        self.assertEqual(ScatterplotStructure(visualization_data, do_censor_points=False).call_build_visualization_in_javascript(), self.get_params({26: 'false'}))

    def test_center_label_over_points(self):
        visualization_data = self.make_adapter()
        self.assertEqual(ScatterplotStructure(visualization_data, center_label_over_points=True).call_build_visualization_in_javascript(), self.get_params({27: 'true'}))

    def test_x_axis_labels_over_points(self):
        visualization_data = self.make_adapter()
        self.assertEqual(ScatterplotStructure(visualization_data, x_axis_labels=['Lo', 'Hi']).call_build_visualization_in_javascript(), self.get_params({28: '["Lo", "Hi"]'}))

    def test_y_axis_labels_over_points(self):
        visualization_data = self.make_adapter()
        self.assertEqual(ScatterplotStructure(visualization_data, y_axis_labels=['Lo', 'Hi']).call_build_visualization_in_javascript(), self.get_params({29: '["Lo", "Hi"]'}))

    def test_topic_model_preview_size(self):
        visualization_data = self.make_adapter()
        self.assertEqual(ScatterplotStructure(visualization_data, topic_model_preview_size=20).call_build_visualization_in_javascript(), self.get_params({30: '20'}))

    def test_vertical_lines(self):
        visualization_data = self.make_adapter()
        params = ScatterplotStructure(visualization_data, vertical_lines=[20, 31]).call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({31: '[20, 31]'}))

    def test_horizontal_line_y_position(self):
        visualization_data = self.make_adapter()
        params = ScatterplotStructure(visualization_data, horizontal_line_y_position=0).call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({32: '0'}))

    def test_vertical_line_x_position(self):
        visualization_data = self.make_adapter()
        params = ScatterplotStructure(visualization_data, vertical_line_x_position=3).call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({33: '3'}))

    def test_unifed_context(self):
        visualization_data = self.make_adapter()
        params = ScatterplotStructure(visualization_data, unified_context=True).call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({34: 'true'}))

    def test_show_category_headings(self):
        visualization_data = self.make_adapter()
        params = ScatterplotStructure(visualization_data, show_category_headings=False).call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({35: 'false'}))

    def test_show_cross_axes(self):
        visualization_data = self.make_adapter()
        params = ScatterplotStructure(visualization_data, show_cross_axes=False).call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({36: 'false'}))

    def test_div_name(self):
        visualization_data = self.make_adapter()
        params = ScatterplotStructure(visualization_data, div_name='divvydivvy').call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({37: '"divvydivvy"'}))

    def test_alternative_term_func(self):
        visualization_data = self.make_adapter()
        params = ScatterplotStructure(visualization_data, alternative_term_func='(function(termDict) {return true;})').call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({38: '(function(termDict) {return true;})'}))

    def test_include_all_contexts(self):
        visualization_data = self.make_adapter()
        params = ScatterplotStructure(visualization_data, include_all_contexts=True).call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({39: 'true'}))

    def test_show_axes_and_cross_hairs(self):
        visualization_data = self.make_adapter()
        params = ScatterplotStructure(visualization_data, show_axes_and_cross_hairs=True).call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({40: 'true'}))

    def test_x_axis_values_format(self):
        visualization_data = self.make_adapter()
        params = ScatterplotStructure(visualization_data, x_axis_values_format='.4f').call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({41: '".4f"'}))

    def test_y_axis_values_format(self):
        visualization_data = self.make_adapter()
        params = ScatterplotStructure(visualization_data, y_axis_values_format='.5f').call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({42: '".5f"'}))

    def test_match_full_line(self):
        visualization_data = self.make_adapter()
        params = ScatterplotStructure(visualization_data, match_full_line=True).call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({43: 'true'}))

    def test_max_overlapping(self):
        visualization_data = self.make_adapter()
        params = ScatterplotStructure(visualization_data, max_overlapping=10).call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({44: '10'}))

    def test_show_corpus_stats(self):
        visualization_data = self.make_adapter()
        params = ScatterplotStructure(visualization_data, show_corpus_stats=False).call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({45: 'false'}))

    def test_sort_doc_labels_by_name(self):
        visualization_data = self.make_adapter()
        params = ScatterplotStructure(visualization_data, sort_doc_labels_by_name=True).call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({46: 'true'}))

    def test_always_jump(self):
        visualization_data = self.make_adapter()
        params = ScatterplotStructure(visualization_data, always_jump=False).call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({47: 'false'}))

    def test_highlight_selected_category(self):
        visualization_data = self.make_adapter()
        params = ScatterplotStructure(visualization_data, highlight_selected_category=True).call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({48: 'true'}))

    def test_show_diagonal(self):
        visualization_data = self.make_adapter()
        params = ScatterplotStructure(visualization_data, show_diagonal=True).call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({49: 'true'}))

    def test_use_global_scale(self):
        visualization_data = self.make_adapter()
        params = ScatterplotStructure(visualization_data, use_global_scale=True).call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({50: 'true'}))

    def test_enable_term_category_description(self):
        visualization_data = self.make_adapter()
        params = ScatterplotStructure(visualization_data, enable_term_category_description=False).call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({51: 'false'}))

    def test_get_custom_term_html(self):
        visualization_data = self.make_adapter()
        html = '(function(x) {return "Term: " + x.term})'
        params = ScatterplotStructure(visualization_data, get_custom_term_html=html).call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({52: html}))

    def test_header_names(self):
        visualization_data = self.make_adapter()
        header_names = {'upper': 'Upper Header Name', 'lower': 'Lower Header Name'}
        params = ScatterplotStructure(visualization_data, header_names=header_names).call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({53: '{"upper": "Upper Header Name", "lower": "Lower Header Name"}'}))

    def test_header_sorting_algos(self):
        visualization_data = self.make_adapter()
        header_sorting_algos = {'upper': '(function(a, b) {return b.s - a.s})', 'lower': '(function(a, b) {return a.s - b.s})'}
        params = ScatterplotStructure(visualization_data, header_sorting_algos=header_sorting_algos).call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({54: '{"lower": (function(a, b) {return a.s - b.s}), "upper": (function(a, b) {return b.s - a.s})}'}))

    def test_ignore_categories(self):
        visualization_data = self.make_adapter()
        params = ScatterplotStructure(visualization_data, ignore_categories=True).call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({55: 'true'}))

    def test_background_labels(self):
        visualization_data = self.make_adapter()
        params = ScatterplotStructure(visualization_data, background_labels=[{'Text': 'Topic 0', 'X': 0.5242579971278757, 'Y': 0.8272937510221724}, {'Text': 'Topic 1', 'X': 0.7107755717675702, 'Y': 0.5034326824672314}, {'Text': 'Topic 2', 'X': 0.09014690078982, 'Y': 0.6261596586530888}]).call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({56: '[{"Text": "Topic 0", "X": 0.5242579971278757, "Y": 0.8272937510221724}, {"Text": "Topic 1", "X": 0.7107755717675702, "Y": 0.5034326824672314}, {"Text": "Topic 2", "X": 0.09014690078982, "Y": 0.6261596586530888}]'}))

    def test_label_priority_column(self):
        visualization_data = self.make_adapter()
        params = ScatterplotStructure(visualization_data, label_priority_column='LabelPriority').call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({57: '"LabelPriority"'}))

    def test_text_color_column(self):
        visualization_data = self.make_adapter()
        params = ScatterplotStructure(visualization_data, text_color_column='TextColor').call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({58: '"TextColor"'}))

    def test_suppress_label_column(self):
        visualization_data = self.make_adapter()
        params = ScatterplotStructure(visualization_data, suppress_text_column='Suppress').call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({59: '"Suppress"'}))

    def test_background_color(self):
        visualization_data = self.make_adapter()
        params = ScatterplotStructure(visualization_data, background_color='#444444').call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({60: '"#444444"'}))

    def test_censor_point_column(self):
        visualization_data = self.make_adapter()
        params = ScatterplotStructure(visualization_data, censor_point_column='CensorPoint').call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({61: '"CensorPoint"'}))

    def test_right_order_column(self):
        visualization_data = self.make_adapter()
        params = ScatterplotStructure(visualization_data, right_order_column='Priority').call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({62: '"Priority"'}))

    def test_sentence_piece(self):
        visualization_data = self.make_adapter()
        params = ScatterplotStructure(visualization_data, subword_encoding='RoBERTa').call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({63: '"RoBERTa"'}))

    def test_top_terms_length(self):
        visualization_data = self.make_adapter()
        params = ScatterplotStructure(visualization_data, top_terms_length=5).call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({64: '5'}))

    def test_top_terms_left_buffer(self):
        visualization_data = self.make_adapter()
        params = ScatterplotStructure(visualization_data, top_terms_left_buffer=10).call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({65: '10'}))

    def test_get_column_header_html(self):
        visualization_data = self.make_adapter()
        params = ScatterplotStructure(visualization_data, get_column_header_html='function(a,b,c,d,e) {return "X"}').call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({66: 'function(a,b,c,d,e) {return "X"}'}))

    def test_term_word(self):
        visualization_data = self.make_adapter()
        params = ScatterplotStructure(visualization_data, term_word='Phone').call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({67: '"Phone"'}))

    def test_show_term_etc(self):
        visualization_data = self.make_adapter()
        params = ScatterplotStructure(visualization_data, show_term_etc=False).call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({68: 'false'}))

    def test_sort_contexts_by_meta(self):
        visualization_data = self.make_adapter()
        params = ScatterplotStructure(visualization_data, sort_contexts_by_meta=True).call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({69: 'true'}))

    def test_suppress_circles(self):
        visualization_data = self.make_adapter()
        params = ScatterplotStructure(visualization_data, suppress_circles=True).call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({70: 'true'}))

    def test_text_size_column(self):
        visualization_data = self.make_adapter()
        params = ScatterplotStructure(visualization_data, text_size_column='TextSize').call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({71: '"TextSize"'}))

    def test_category_colors(self):
        visualization_data = self.make_adapter()
        params = ScatterplotStructure(visualization_data, category_colors={'Democratic': '0000FF', 'Republican': 'FF0000'}).call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({72: '{"Democratic": "0000FF", "Republican": "FF0000"}'}))

    def test_document_word(self):
        visualization_data = self.make_adapter()
        params = ScatterplotStructure(visualization_data, document_word='paragraph').call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({73: '"paragraph"', 74: '"paragraphs"'}))

    def test_document_word_plural(self):
        visualization_data = self.make_adapter()
        params = ScatterplotStructure(visualization_data, document_word_plural='multiple paragraphs').call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({74: '"multiple paragraphs"'}))

    def test_category_order(self):
        visualization_data = self.make_adapter()
        self.assertEqual(ScatterplotStructure(visualization_data, category_order=['Dem', 'Rep']).call_build_visualization_in_javascript(), self.get_params({75: '["Dem", "Rep"]'}))

    def test_include_gradient(self):
        visualization_data = self.make_adapter()
        params = ScatterplotStructure(visualization_data, include_gradient=True).call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({76: 'true'}))

    def test_left_gradient_term(self):
        visualization_data = self.make_adapter()
        params = ScatterplotStructure(visualization_data, left_gradient_term='Left Gradient').call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({77: '"Left Gradient"'}))

    def test_middle_gradient_term(self):
        visualization_data = self.make_adapter()
        params = ScatterplotStructure(visualization_data, middle_gradient_term='Middle Gradient').call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({78: '"Middle Gradient"'}))

    def test_right_gradient_term(self):
        visualization_data = self.make_adapter()
        params = ScatterplotStructure(visualization_data, right_gradient_term='Right Gradient').call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({79: '"Right Gradient"'}))

    def test_gradient_text_color(self):
        visualization_data = self.make_adapter()
        params = ScatterplotStructure(visualization_data, gradient_text_color='black').call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({80: '"black"'}))

    def test_gradient_colors(self):
        visualization_data = self.make_adapter()
        params = ScatterplotStructure(visualization_data, gradient_colors=['#0000ff', '#fe0100', '#00ff00']).call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({81: '["#0000ff", "#fe0100", "#00ff00"]'}))

    def test_category_term_score_scaler(self):
        visualization_data = self.make_adapter()
        cat_term_scaler = '(scores => (maxScore=>scores.flatMap(score=>-0.5*(1 + score/maxScore)))(Math.max(...scores.flatMap(Math.abs))))'
        params = ScatterplotStructure(visualization_data, category_term_score_scaler=cat_term_scaler).call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({82: cat_term_scaler}))

    def test_show_chart(self):
        visualization_data = self.make_adapter()
        params = ScatterplotStructure(visualization_data, show_chart=True).call_build_visualization_in_javascript()
        self.assertEqual(params, self.get_params({83: 'true'}))

def test_main(self):
    assembler = self.make_assembler()
    html = assembler.to_html()
    if sys.version_info.major == 2:
        self.assertEqual(type(html), unicode)
    else:
        self.assertEqual(type(html), str)
    self.assertFalse('<!-- EXTRA LIBS -->' in html)
    self.assertFalse('<!-- INSERT SCRIPT -->' in html)
    self.assertTrue('<!-- INSERT SEMIOTIC SQUARE -->' in html)
    self.assertTrue('Republican' in html)

def test_semiotic_square(self):
    semsq = get_test_semiotic_square()
    assembler = self.make_assembler()
    html = assembler.to_html(html_base=HTMLSemioticSquareViz(semsq).get_html(num_terms=6))
    if sys.version_info.major == 2:
        self.assertEqual(type(html), unicode)
    else:
        self.assertEqual(type(html), str)
    self.assertFalse('<!-- EXTRA LIBS -->' in html)
    self.assertFalse('<!-- INSERT SCRIPT -->' in html)
    self.assertTrue('Republican' in html)

def test_protocol_is_https(self):
    html = self.make_assembler().to_html(protocol='https')
    self.assertTrue(self._https_script_is_present(html))
    self.assertFalse(self._http_script_is_present(html))

def _test_protocol_is_http(self):
    html = self.make_assembler().to_html(protocol='http')
    self.assertFalse(self._https_script_is_present(html))
    self.assertTrue(self._http_script_is_present(html))

def test_protocol_default_d3_url(self):
    html = self.make_assembler().to_html()
    self.assertTrue(DEFAULT_D3_URL in html)
    html = self.make_assembler().to_html(d3_url='d3.js')
    self.assertTrue(DEFAULT_D3_URL not in html)
    self.assertTrue('d3.js' in html)

def test_protocol_default_d3_chromatic_url(self):
    html = self.make_assembler().to_html()
    self.assertTrue(DEFAULT_D3_SCALE_CHROMATIC in html)
    html = self.make_assembler().to_html(d3_scale_chromatic_url='d3-scale-chromatic.v1.min.js')
    self.assertTrue(DEFAULT_D3_SCALE_CHROMATIC not in html)
    self.assertTrue('d3-scale-chromatic.v1.min.js' in html)

def test_protocol_defaults_to_http(self):
    self.assertEqual(self.make_assembler().to_html(protocol='http'), self.make_assembler().to_html())

def test_raise_invalid_protocol_exception(self):
    with self.assertRaisesRegexp(BaseException, 'Invalid protocol: ftp.  Protocol must be either http or https.'):
        self.make_assembler().to_html(protocol='ftp')

class TestIndexStore(TestCase):

    def test_main(self):
        index_store = IndexStore()
        self.assertEqual(index_store.getidx('a'), 0)
        self.assertEqual(index_store.getidx('b'), 1)
        self.assertEqual(index_store.getidx('a'), 0)
        self.assertEqual(index_store.getval(0), 'a')
        self.assertEqual(index_store.getval(1), 'b')
        self.assertTrue('a' in index_store)
        self.assertFalse('c' in index_store)
        self.assertEqual(set(index_store.values()), set(['a', 'b']))
        self.assertFalse(0 in index_store)
        self.assertTrue(index_store.hasidx(0))
        self.assertFalse(index_store.hasidx(2))
        self.assertEqual(index_store.getnumvals(), 2)
        self.assertEqual(list(index_store.items()), [(0, 'a'), (1, 'b')])

    def test_getidxstrict(self):
        index_store = IndexStore()
        self.assertEqual(index_store.getidx('a'), 0)
        self.assertEqual(index_store.getidx('b'), 1)
        self.assertEqual(index_store.getidx('a'), 0)
        with self.assertRaises(KeyError):
            index_store.getidxstrict('c')

    def test_batch_delete(self):
        index_store = IndexStore()
        self.assertEqual(index_store.getidx('a'), 0)
        self.assertEqual(index_store.getidx('b'), 1)
        self.assertEqual(index_store.getidx('c'), 2)
        self.assertEqual(index_store.getidx('d'), 3)
        with self.assertRaises(KeyError):
            new_idx_store = index_store.batch_delete_vals(['e', 'c'])
        new_idx_store = index_store.batch_delete_vals(['b', 'c'])
        self.assertEqual(new_idx_store.getidx('a'), 0)
        self.assertEqual(new_idx_store.getidx('c'), 2)
        self.assertEqual(new_idx_store.getidx('e'), 3)
        self.assertEqual(index_store.getidx('d'), 3)
        self.assertEqual(index_store.getidx('c'), 2)
        self.assertEqual(index_store.getidx('b'), 1)
        self.assertEqual(index_store.getidx('a'), 0)
        with self.assertRaises(ValueError):
            new_idx_store = index_store.batch_delete_idx([5, 1])
        new_idx_store = index_store.batch_delete_idx([2, 1])
        self.assertEqual(new_idx_store.getidx('a'), 0)
        self.assertEqual(new_idx_store.getidx('c'), 2)
        self.assertEqual(new_idx_store.getidx('e'), 3)

    def test_getidxstrictbatch(self):
        index_store = IndexStore()
        self.assertEqual(index_store.getidx('a'), 0)
        self.assertEqual(index_store.getidx('b'), 1)
        self.assertEqual(index_store.getidx('c'), 2)
        self.assertEqual(index_store.getidx('d'), 3)
        self.assertEqual(index_store.getidx('e'), 4)
        self.assertEqual(index_store.getidx('f'), 5)
        self.assertEqual(index_store.getidxstrictbatch(['b', 'f', 'b', 'a']), [1, 5, 1, 0])

    def test_batch_delete_extra(self):
        index_store = IndexStore()
        self.assertEqual(index_store.getidx('a'), 0)
        self.assertEqual(index_store.getidx('b'), 1)
        self.assertEqual(index_store.getidx('c'), 2)
        self.assertEqual(index_store.getidx('d'), 3)
        self.assertEqual(index_store.getidx('e'), 4)
        self.assertEqual(index_store.getidx('f'), 5)
        del_idxstore = index_store.batch_delete_vals(['b', 'e'])
        self.assertEqual(list(del_idxstore.items()), [(0, 'a'), (1, 'c'), (2, 'd'), (3, 'f')])
        del_idxstore2 = del_idxstore.batch_delete_vals([])
        self.assertEqual(list(del_idxstore.items()), list(del_idxstore2.items()))

    def test_rename(self):
        index_store = IndexStore()
        self.assertEqual(index_store.getidx('a'), 0)
        self.assertEqual(index_store.getidx('b'), 1)
        self.assertEqual(index_store.getidx('c'), 2)
        self.assertEqual(index_store.getidx('d'), 3)
        self.assertEqual(index_store.getidx('e'), 4)
        self.assertEqual(index_store.getidx('f'), 5)
        index_store.rename([('a', 'A'), ('f', 'F'), ('b', 'B')])
        self.assertFalse('a' in index_store)
        self.assertFalse('b' in index_store)
        self.assertFalse('f' in index_store)
        self.assertEqual(index_store.getidx('A'), 0)
        self.assertEqual(index_store.getidx('B'), 1)
        self.assertEqual(index_store.getidx('c'), 2)
        self.assertEqual(index_store.getidx('d'), 3)
        self.assertEqual(index_store.getidx('e'), 4)
        self.assertEqual(index_store.getidx('F'), 5)

def test_main(self):
    index_store = IndexStore()
    self.assertEqual(index_store.getidx('a'), 0)
    self.assertEqual(index_store.getidx('b'), 1)
    self.assertEqual(index_store.getidx('a'), 0)
    self.assertEqual(index_store.getval(0), 'a')
    self.assertEqual(index_store.getval(1), 'b')
    self.assertTrue('a' in index_store)
    self.assertFalse('c' in index_store)
    self.assertEqual(set(index_store.values()), set(['a', 'b']))
    self.assertFalse(0 in index_store)
    self.assertTrue(index_store.hasidx(0))
    self.assertFalse(index_store.hasidx(2))
    self.assertEqual(index_store.getnumvals(), 2)
    self.assertEqual(list(index_store.items()), [(0, 'a'), (1, 'b')])

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

def __query_for_doc_offset_df(self, offset_df: pd.DataFrame, doc_idx: int) -> pd.DataFrame:
    try:
        doc_offset_df = offset_df.loc[doc_idx]
    except KeyError:
        return pd.DataFrame([])
    if type(doc_offset_df) == pd.Series:
        return pd.DataFrame([dict(doc_offset_df)])
    return doc_offset_df

