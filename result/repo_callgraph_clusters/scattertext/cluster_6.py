# Cluster 6

def filter_out_unigrams_that_only_occur_in_one_bigram(df):
    bigrams = {bigram for bigram in df.index if ' ' in bigram}
    unigrams_to_remove = unigrams_that_only_occur_in_one_bigram(bigrams)
    return df.drop(unigrams_to_remove)

class TermCategoryFrequencies(object):
    """
	This class allows you to produce scatter plots of raw term frequency counts.

	Occasionally, only term frequency statistics are available. This may happen in the case of very large,
	lost, or proprietary data sets. `TermCategoryFrequencies` is a corpus representation,that can accept this
	sort of data, along with any categorized documents that happen to be available.

	Let use the [Corpus of Contemporary American English](https://corpus.byu.edu/coca/) as an example.
	We'll construct a visualization
	to analyze the difference between spoken American English and English that occurs in fiction.

	```python
	convention_df = (pd.read_excel('https://www.wordfrequency.info/files/genres_sample.xls')
		      .dropna()
		      .set_index('lemma')[['SPOKEN', 'FICTION']]
		      .iloc[:1000])
	convention_df.head()
	          SPOKEN    FICTION
	lemma
	the    3859682.0  4092394.0
	I      1346545.0  1382716.0
	they   609735.0   352405.0
	she    212920.0   798208.0
	would  233766.0   229865.0
	```

	Transforming this into a visualization is extremely easy. Just pass a dataframe indexed on
	terms with columns indicating category-counts into the the `TermCategoryFrequencies` constructor.

	```python
	term_cat_freq = st.TermCategoryFrequencies(convention_df)
	```

	And call `produce_scattertext_explorer` normally:

	```python
	html = st.produce_scattertext_explorer(
		term_cat_freq,
		category='SPOKEN',
		category_name='Spoken',
		not_category_name='Fiction',
	)
	```


	[![demo_category_frequencies.html](https://jasonkessler.github.io/demo_category_frequencies.png)](https://jasonkessler.github.io/demo_category_frequencies.html)

	If you'd like to incorporate some documents into the visualization, you can add them into to the
	`TermCategoyFrequencies` object.

	First, let's extract some example Fiction and Spoken documents from the sample COCA corpus.

	```python
	import requests, zipfile, io
	coca_sample_url = 'http://corpus.byu.edu/cocatext/samples/text.zip'
	zip_file = zipfile.ZipFile(io.BytesIO(requests.get(coca_sample_url).content))

	document_df = pd.DataFrame(
		[{'text': zip_file.open(fn).read().decode('utf-8'),
		  'category': 'SPOKEN'}
		 for fn in zip_file.filelist if fn.filename.startswith('w_spok')][:2]
		+ [{'text': zip_file.open(fn).read().decode('utf-8'),
		    'category': 'FICTION'}
		   for fn in zip_file.filelist if fn.filename.startswith('w_fic')][:2])
	```

	And we'll pass the `documents_df` dataframe into `TermCategoryFrequencies` via the `document_category_df`
	parameter.  Ensure the dataframe has two columns, 'text' and 'category'.  Afterward, we can
	call `produce_scattertext_explorer` (or your visualization function of choice) normally.

	```python
	doc_term_cat_freq = st.TermCategoryFrequencies(convention_df, document_category_df=document_df)

	html = st.produce_scattertext_explorer(
		doc_term_cat_freq,
		category='SPOKEN',
		category_name='Spoken',
		not_category_name='Fiction',
	)
	```
	"""

    def __init__(self, category_frequency_df, document_category_df=None, metadata_frequency_df=None, unigram_frequency_path=None):
        """
		Parameters
		----------
		category_frequency_df : pd.DataFrame
			Index is term, columns are categories, values are counts
		document_category_df : pd.DataFrame, optional
			Columns are text, category. Values are text (string) and category (string)
		metadata_frequency_df : pd.DataFrame, optional
			Index is term, columns are categories, values are counts
		unigram_frequency_path : See TermDocMatrix, optional
		"""
        if document_category_df is not None:
            assert 'text' in document_category_df.columns and 'category' in document_category_df.columns
        self._document_category_df = document_category_df
        self.metadata_frequency_df = metadata_frequency_df
        self.term_category_freq_df = category_frequency_df
        self._unigram_frequency_path = unigram_frequency_path

    def get_num_terms(self):
        return len(self.term_category_freq_df)

    def get_categories(self):
        return list(self.term_category_freq_df.columns)

    def get_num_metadata(self):
        return len(self.metadata_frequency_df)

    def get_scaled_f_scores_vs_background(self, scaler_algo=DEFAULT_BACKGROUND_SCALER_ALGO, beta=DEFAULT_BACKGROUND_BETA):
        df = self.get_term_and_background_counts()
        df['Scaled f-score'] = ScaledFScore.get_scores_for_category(df['corpus'], df['background'], scaler_algo, beta)
        return df.sort_values(by='Scaled f-score', ascending=False)

    def get_term_and_background_counts(self):
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
        corpus_freq_df = pd.DataFrame({'corpus': self.term_category_freq_df.sum(axis=1)})
        corpus_unigram_freq = corpus_freq_df.loc[[w for w in corpus_freq_df.index if ' ' not in w]]
        df = corpus_unigram_freq.join(background_df, how='outer').fillna(0)
        return df

    def _get_background_unigram_frequencies(self):
        if self._unigram_frequency_path:
            unigram_freq_table_buf = open(self._unigram_frequency_path)
        else:
            unigram_freq_table_buf = StringIO(pkgutil.get_data('scattertext', 'data/count_1w.txt').decode('utf-8'))
        to_ret = pd.read_table(unigram_freq_table_buf, names=['word', 'background']).sort_values(ascending=False, by='background').drop_duplicates(['word']).set_index('word')
        return to_ret

    def list_extra_features(self):
        raise Exception('Not implemented in TermCategoryFrequencies')

    def get_doc_indices(self):
        """
		Returns
		-------
		np.array

		Integer document indices
		"""
        if self._document_category_df is None:
            return np.array([])
        categories_d = {d: i for i, d in enumerate(self.get_categories())}
        return self._document_category_df.category.apply(categories_d.get).values

    def get_texts(self):
        """
		Returns
		-------
		np.array

		Texts
		"""
        if self._document_category_df is None:
            return np.array([])
        return self._document_category_df.text.values

    def get_term_category_frequencies(self, scatterchartdata):
        """
		Parameters
		----------
		scatterchartdata : ScatterChartData

		Returns
		-------
		pd.DataFrame
		"""
        df = self.term_category_freq_df.rename(columns={c: str(c) + ' freq' for c in self.term_category_freq_df})
        df.index.name = 'term'
        return df

    def apply_ranker(self, term_ranker):
        """
		Parameters
		----------
		term_ranker : TermRanker
			We'll ignore this

		Returns
		-------
		pd.Dataframe
		"""
        return self.get_term_category_frequencies(None)

def get_categories(self):
    return list(self.term_category_freq_df.columns)

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

def hide_terms(self, terms):
    """
        Mark terms which won't be displayed in the visualization.

        :param terms: iter[str]
            Terms to mark as hidden.
        :return: ScatterChart
        """
    self.hidden_terms = set(terms)
    return self

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

def get_term_colors(self):
    """

        :return: dict, term -> color
        """
    term_color = pd.Series(self.category_colors[self.term_cat].values, index=self.term_cat.index)
    return term_color.apply(get_hex_color).to_dict()

def produce_scattertext_explorer(corpus: object, category: object, category_name: object=None, not_category_name: object=None, protocol: object='https', pmi_threshold_coefficient: object=DEFAULT_MINIMUM_TERM_FREQUENCY, minimum_term_frequency: object=DEFAULT_PMI_THRESHOLD_COEFFICIENT, minimum_not_category_term_frequency: object=0, max_terms: object=None, filter_unigrams: object=False, height_in_pixels: object=None, width_in_pixels: object=None, max_snippets: object=None, max_docs_per_category: object=None, metadata: object=None, scores: object=None, x_coords: object=None, y_coords: object=None, original_x: object=None, original_y: object=None, rescale_x: object=None, rescale_y: object=None, singleScoreMode: object=False, sort_by_dist: object=False, reverse_sort_scores_for_not_category: object=True, use_full_doc: object=False, transform: object=percentile_alphabetical, jitter: object=0, gray_zero_scores: object=False, term_ranker: object=None, asian_mode: object=False, match_full_line: object=False, use_non_text_features: object=False, show_top_terms: object=True, show_characteristic: object=None, word_vec_use_p_vals: object=False, max_p_val: object=0.1, p_value_colors: object=False, term_significance: object=None, save_svg_button: object=False, x_label: object=None, y_label: object=None, d3_url: object=None, d3_scale_chromatic_url: object=None, pmi_filter_thresold: object=None, alternative_text_field: object=None, terms_to_include: object=None, semiotic_square: object=None, num_terms_semiotic_square: object=None, not_categories: object=None, neutral_categories: object=[], extra_categories: object=[], show_neutral: object=False, neutral_category_name: object=None, get_tooltip_content: object=None, x_axis_values: object=None, y_axis_values: object=None, x_axis_values_format: object=None, y_axis_values_format: object=None, color_func: object=None, term_scorer: object=None, term_scorer_kwargs: object=None, show_axes: object=True, show_axes_and_cross_hairs: object=False, show_diagonal: object=False, use_global_scale: object=False, horizontal_line_y_position: object=None, vertical_line_x_position: object=None, show_cross_axes: object=True, show_extra: object=False, extra_category_name: object=None, censor_points: object=True, center_label_over_points: object=False, x_axis_labels: object=None, y_axis_labels: object=None, topic_model_term_lists: object=None, topic_model_preview_size: object=10, metadata_descriptions: object=None, vertical_lines: object=None, characteristic_scorer: object=None, term_colors: object=None, unified_context: object=False, show_category_headings: object=True, highlight_selected_category: object=False, include_term_category_counts: object=False, div_name: object=None, alternative_term_func: object=None, term_metadata: object=None, term_metadata_df: object=None, max_overlapping: object=-1, include_all_contexts: object=False, show_corpus_stats: object=True, sort_doc_labels_by_name: object=False, enable_term_category_description: object=True, always_jump: object=True, get_custom_term_html: object=None, header_names: object=None, header_sorting_algos: object=None, ignore_categories: object=False, d3_color_scale: object=None, background_labels: object=None, tooltip_columns: object=None, tooltip_column_names: object=None, term_description_columns: object=None, term_description_column_names: object=None, term_word_in_term_description: object='Term', color_column: object=None, color_score_column: object=None, label_priority_column: object=None, text_color_column: object=None, text_size_column: object=None, suppress_text_column: object=None, background_color: object=None, left_list_column: object=None, censor_point_column: object=None, right_order_column: object=None, line_coordinates: object=None, subword_encoding: object=None, top_terms_length: object=14, top_terms_left_buffer: object=0, dont_filter: object=False, use_offsets: object=False, get_column_header_html: object=None, show_term_etc: object=True, sort_contexts_by_meta: object=False, show_chart: object=False, return_data: object=False, suppress_circles: object=False, category_colors: object=None, document_word: object='document', document_word_plural: object=None, category_order: object=None, include_gradient: bool=False, left_gradient_term: Optional[str]=None, middle_gradient_term: Optional[str]=None, right_gradient_term: Optional[str]=None, gradient_text_color: Optional[str]=None, gradient_colors: Optional[List[str]]=None, category_term_scores: Optional[list[List[float]]]=None, category_term_score_scaler: Optional[str]=None, return_scatterplot_structure: object=False) -> object:
    """Returns html code of visualization.

    Parameters
    ----------
    corpus : Corpus
        Corpus to use.
    category : str
        Name of category column as it appears in original data frame.
    category_name : str
        Name of category to use.  E.g., "5-star reviews."
        Optional, defaults to category name.
    not_category_name : str
        Name of everything that isn't in category.  E.g., "Below 5-star reviews".
        Optional defaults to "N(n)ot " + category_name, with the case of the 'n' dependent
        on the case of the first letter in category_name.
    protocol : str, optional
        Protocol to use.  Either http or https.  Default is https.
    pmi_threshold_coefficient : int, optional
        Filter out bigrams with a PMI of < 2 * pmi_threshold_coefficient. Default is 6
    minimum_term_frequency : int, optional
        Minimum number of times word needs to appear to make it into visualization.
    minimum_not_category_term_frequency : int, optional
      If an n-gram does not occur in the category, minimum times it
       must be seen to be included. Default is 0.
    max_terms : int, optional
        Maximum number of terms to include in visualization.
    filter_unigrams : bool, optional
        Default False, do we filter out unigrams that only occur in one bigram
    width_in_pixels : int, optional
        Width of viz in pixels, if None, default to JS's choice
    height_in_pixels : int, optional
        Height of viz in pixels, if None, default to JS's choice
    max_snippets : int, optional
        Maximum number of snippets to show when term is clicked.  If None, all are shown.
    max_docs_per_category: int, optional
        Maximum number of documents to store per category.  If None, by default, all are stored.
    metadata : list or function, optional
        list of meta data strings that will be included for each document, if a function, called on corpus
    scores : np.array, optional
        Array of term scores or None.
    x_coords : np.array, optional
        Array of term x-axis positions or None.  Must be in [0,1].
        If present, y_coords must also be present.
    y_coords : np.array, optional
        Array of term y-axis positions or None.  Must be in [0,1].
        If present, x_coords must also be present.
    original_x : array-like
        Original, unscaled x-values.  Defaults to x_coords
    original_y : array-like
        Original, unscaled y-values.  Defaults to y_coords
    rescale_x : lambda list[0,1]: list[0,1], optional
        Array of term x-axis positions or None.  Must be in [0,1].
        Rescales x-axis after filtering
    rescale_y : lambda list[0,1]: list[0,1], optional
        Array of term y-axis positions or None.  Must be in [0,1].
        Rescales y-axis after filtering
    singleScoreMode : bool, optional
        Label terms based on score vs distance from corner.  Good for topic scores. Show only one color.
    sort_by_dist: bool, optional
        Label terms based distance from corner. True by default.  Negated by singleScoreMode.
    reverse_sort_scores_for_not_category: bool, optional
        If using a custom score, score the not-category class by
        lowest-score-as-most-predictive. Turn this off for word vector
        or topic similarity. Default True.
    use_full_doc : bool, optional
        Use the full document in snippets.  False by default.
    transform : function, optional
        not recommended for editing.  change the way terms are ranked.  default is st.Scalers.percentile_ordinal
    jitter : float, optional
        percentage of axis to jitter each point.  default is 0.
    gray_zero_scores : bool, optional
        If True, color points with zero-scores a light shade of grey.  False by default.
    term_ranker : TermRanker, optional
        TermRanker class for determining term frequency ranks.
    asian_mode : bool, optional
        Use a special Javascript regular expression that's specific to chinese or japanese
    match_full_line : bool, optional
        Has the javascript regex match the full line instead of part of it
    use_non_text_features : bool, optional
        Show non-bag-of-words features (e.g., Empath) instead of text.  False by default.
    show_top_terms : bool, default True
        Show top terms on the left-hand side of the visualization
    show_characteristic: bool, default None
        Show characteristic terms on the far left-hand side of the visualization
    word_vec_use_p_vals: bool, default False
        Sort by harmonic mean of score and distance.
    max_p_val : float, default 0.1
        If word_vec_use_p_vals, the minimum p val to use.
    p_value_colors : bool, default False
      Color points differently if p val is above 1-max_p_val, below max_p_val, or
       in between.
    term_significance : TermSignificance instance or None
        Way of getting signfiance scores.  If None, p values will not be added.
    save_svg_button : bool, default False
        Add a save as SVG button to the page.
    x_label : str, default None
        Custom x-axis label
    y_label : str, default None
        Custom y-axis label
    d3_url, str, None by default.  The url (or path) of d3.
        URL of d3, to be inserted into <script src="..."/>.  Overrides `protocol`.
      By default, this is `DEFAULT_D3_URL` declared in `ScatterplotStructure`.
    d3_scale_chromatic_url, str, None by default.  Overrides `protocol`.
      URL of d3 scale chromatic, to be inserted into <script src="..."/>
      By default, this is `DEFAULT_D3_SCALE_CHROMATIC` declared in `ScatterplotStructure`.
    pmi_filter_thresold : (DEPRECATED) int, None by default
      DEPRECATED.  Use pmi_threshold_coefficient instead.
    alternative_text_field : str or None, optional
        Field in from dataframe used to make corpus to display in place of parsed text. Only
        can be used if corpus is a ParsedCorpus instance.
    terms_to_include : list or None, optional
        Whitelist of terms to include in visualization.
    semiotic_square : SemioticSquareBase
        None by default.  SemioticSquare based on corpus.  Includes square above visualization.
    num_terms_semiotic_square : int
        10 by default. Number of terms to show in semiotic square.
        Only active if semiotic square is present.
    not_categories : list
        All categories other than category by default.  Documents labeled
        with remaining category.
    neutral_categories : list
        [] by default.  Documents labeled neutral.
    extra_categories : list
        [] by default.  Documents labeled extra.
    show_neutral : bool
        False by default.  Show a third column listing contexts in the
        neutral categories.
    neutral_category_name : str
        "Neutral" by default. Only active if show_neutral is True.  Name of the neutral
        column.
    get_tooltip_content : str
        Javascript function to control content of tooltip.  Function takes a parameter
        which is a dictionary entry produced by `ScatterChartExplorer.to_dict` and
        returns a string.
    x_axis_values : list, default None
        Value-labels to show on x-axis. Low, medium, high are defaults.
    y_axis_values : list, default None
        Value-labels to show on y-axis. Low, medium, high are defaults.
    x_axis_values_format : str, default None
        d3 format of x-axis values
    y_axis_values_format : str, default None
        d3 format of y-axis values
    color_func : str, default None
        Javascript function to control color of a point.  Function takes a parameter
        which is a dictionary entry produced by `ScatterChartExplorer.to_dict` and
        returns a string.
    term_scorer : Object, default None
        In lieu of scores, object with a get_scores(a,b) function that returns a set of scores,
        where a and b are term counts.  Scorer optionally has a get_term_freqs function. Also could be a
        CorpusBasedTermScorer instance.
    term_scorer_kwargs : Optional[Dict], default None
        Arguments to be placed in the term_scorer constructor after the corpus
    show_axes : bool, default True
        Show the ticked axes on the plot.  If false, show inner axes as a crosshair.
    show_axes_and_cross_hairs : bool, default False
        Show both peripheral axis labels and cross axes.
    show_diagonal : bool, default False
        Show a diagonal line leading from the lower-left ot the upper-right; only makes
        sense to use this if use_global_scale is true.
    use_global_scale : bool, default False
        Use same scale for both axes
    vertical_line_x_position : float, default None
    horizontal_line_y_position : float, default None
    show_cross_axes : bool, default True
        If show_axes is False, do we show cross-axes?
    show_extra : bool
        False by default.  Show a fourth column listing contexts in the
        extra categories.
    extra_category_name : str, default None
        "Extra" by default. Only active if show_neutral is True and show_extra is True.  Name
        of the extra column.
    censor_points : bool, default True
        Don't label over points.
    center_label_over_points : bool, default False
        Center a label over points, or try to find a position near a point that
        doesn't overlap anything else.
    x_axis_labels: list, default None
        List of string value-labels to show at evenly spaced intervals on the x-axis.
        Low, medium, high are defaults.
    y_axis_labels : list, default None
        List of string value-labels to show at evenly spaced intervals on the y-axis.
        Low, medium, high are defaults.
    topic_model_term_lists : dict default None
        Dict of metadata name (str) -> List of string terms in metadata. These will be bolded
        in query in context results.
    topic_model_preview_size : int default 10
        Number of terms in topic model to show as a preview.
    metadata_descriptions : dict default None
        Dict of metadata name (str) -> str of metadata description. These will be shown when a meta data term is
        clicked.
    vertical_lines : list default None
        List of floats corresponding to points on the x-axis to draw vertical lines
    characteristic_scorer : CharacteristicScorer default None
        Used for bg scores
    term_colors : dict, default None
        Dictionary mapping term to color
    unified_context : bool, default False
        Boolean displays contexts in a single pane as opposed to separate columns.
    show_category_headings : bool, default True
        Show category headings if unified_context is True.
    highlight_selected_category : bool, default False
        Highlight selected category if unified_context is True.
    include_term_category_counts : bool, default False
        Include the termCounts object in the plot definition.
    div_name : str, None by default
        Give the scatterplot div name a non-default value
    alternative_term_func: str, default None
        Javascript function which take a term JSON object and returns a bool.  If the return value is true,
        execute standard term click pipeline. Ex.: `'(function(termDict) {return true;})'`.
    term_metadata : dict, None by default
        Dict mapping terms to dictionaries containing additional information which can be used in the color_func
        or the get_tooltip_content function. These will appear in termDict.etc
    term_metadata_df : pd.DataFrame, None by default
        Dataframe version of term_metadata
    include_all_contexts: bool, default False
        Include all contexts, even non-matching ones, in interface
    max_overlapping: int, default -1
        Number of overlapping terms to dislay. If -1, display all. (default)
    show_corpus_stats: bool, default True
        Show the corpus stats div
    sort_doc_labels_by_name: bool default False
        If unified, sort the document labels by name
    always_jump: bool, default True
        Always jump to term contexts if a term is clicked
    enable_term_category_description: bool, default True
        List term/metadata statistics under category
    get_custom_term_html: str, default None
        Javascript function which displays term summary from term info
    header_names: Dict[str, str], default None
        Dictionary giving names of term lists shown to the right of the plot. Valid keys are
        upper, lower and right.
    header_sorting_algos: Dict[str, str], default None
        Dictionary giving javascript sorting algorithms for panes. Valid keys are upper, lower
        and right. Value is a JS function which takes the "data" object.
    ignore_categories: bool, default False
        Signals the plot shouldn't display category names. Used in single category plots.
    suppress_text_column: str, default None
        Column in term_metadata_df which indicates term should be hidden
    left_list_column: str, default None
        Column in term_metadata_df which should be used for sorting words into upper and lower
        parts of left word-list sections. Highest values in upper, lowest in lower.
    tooltip_columns: List[str]
    tooltip_column_names: Dict[str, str]
    term_description_columns: List[str]
    term_description_column_names: Dict[str]
    term_word_in_term_description: str, default None
    color_column: str, default None:
        column in term_metadata_df which indicates color
    color_score_column: str, default None
        column in term_metadata df; contains value between 0 and 1 which will be used to assign a color
    label_priority_column : str, default None
        Column in term_metadata_df; larger values in the column indicate a term should be labeled first
    censor_point_column : str, default None
        Should we allow labels to be drawn over point?
    right_order_column : str, default None
        Order for right column ("characteristic" by default); largest first
    background_color : str, default None
        Changes document.body's background color to background_color
    line_coordinates : list, default None
        Coordinates for drawing a line under the plot
    subword_encoding : str, default None
        Type of subword encoding to use, None if none, currently supports "RoBERTa"
    top_terms_length : int, default 14
        Number of words to list in most/least associated lists on left-hand side
    top_terms_left_buffer : int, default 0
        Number of pixels left to shift top terms list
    dont_filter : bool, default False
        Don't filter any terms when charting
    get_column_header_html : str, default None
        Javascript function to return html over each column. Matches header
        (Column Name, occurrences per 25k, occs, # occs * 1000/num docs, term info)
    show_term_etc: bool, default True
        Shows list of etc values after clicking term
    use_offsets : bool, default False
        Enable the use of metadata offsets
    sort_contexts_by_meta : bool, default False
        Sort context by meta instead of match strength
    suppress_circles : bool, default False
        Label terms over circles and hide circless
    show_chart : bool, default False
        Show line chart if unified context is true
    return_data : bool default False
        Return a dict containing the output of `ScatterChartExplosrer.to_dict` instead of
        an html.
    category_colors : dict, optional defaut None
        Dictionary matching category names to colors
    document_word : str, default "document"
    document_word_plural : Optional[str], default "document"
    category_order : Optional[list[str]], default None
        Order of categories in line chart
    include_gradient : bool, False
        Include gradient at the top of the chart
    left_gradient_term : Optional[str], None by default
        Text of left gradient label. category_name by default
    middle_gradient_term : Optional[str], None by default
        Text of middle grad label. If None, not shown.
    right_gradient_term: Optional[str], None by default
        Text of right gradient label, not_category_name by default
    gradient_text_color: str, white by default
        Color of text in gradient
    gradient_colors: Optional[List[str]], None by default, follows d3_color_scale
        Colors of gradient, as a list of hex values (e.g, ['#0000ff', '#fe0100', '#00ff00'])
    category_term_scores: Optional[List[List[float]], None by default
        score[category, term] for table visualization
    category_term_score_scaler: Optional[str], None by default
        Javascript function which scales a set of categories scores to between 0 and 1
    return_scatterplot_structure : bool, default False
        return ScatterplotStructure instead of html

    Returns
    -------
    str
    html of visualization

    """
    if singleScoreMode or word_vec_use_p_vals:
        d3_color_scale = 'd3.interpolatePurples'
    if singleScoreMode or not sort_by_dist:
        sort_by_dist = False
    else:
        sort_by_dist = True
    if term_ranker is None:
        term_ranker = termranking.AbsoluteFrequencyRanker
    category_name, not_category_name = get_category_names(category, category_name, not_categories, not_category_name)
    if not_categories is None:
        not_categories = [c for c in corpus.get_categories() if c != category]
    term_scorer = _initialize_term_scorer_if_needed(category, corpus, neutral_categories, not_categories, show_neutral, term_scorer, use_non_text_features, term_ranker, term_scorer_kwargs)
    if term_scorer:
        scores = get_term_scorer_scores(category, corpus, neutral_categories, not_categories, show_neutral, term_ranker, term_scorer, use_non_text_features)
    if pmi_filter_thresold is not None:
        pmi_threshold_coefficient = pmi_filter_thresold
        warnings.warn("The argument name 'pmi_filter_thresold' has been deprecated. Use 'pmi_threshold_coefficient' in its place", DeprecationWarning)
    if use_non_text_features:
        pmi_threshold_coefficient = 0
    scatter_chart_explorer = ScatterChartExplorer(corpus, minimum_term_frequency=minimum_term_frequency, minimum_not_category_term_frequency=minimum_not_category_term_frequency, pmi_threshold_coefficient=pmi_threshold_coefficient, filter_unigrams=filter_unigrams, jitter=jitter, max_terms=max_terms, term_ranker=term_ranker, use_non_text_features=use_non_text_features, term_significance=term_significance, terms_to_include=terms_to_include, dont_filter=dont_filter)
    if x_coords is None and y_coords is not None or (y_coords is None and x_coords is not None):
        raise Exception('Both x_coords and y_coords need to be passed or both left blank')
    if x_coords is not None:
        scatter_chart_explorer.inject_coordinates(x_coords, y_coords, rescale_x=rescale_x, rescale_y=rescale_y, original_x=original_x, original_y=original_y)
    if topic_model_term_lists is not None:
        scatter_chart_explorer.inject_metadata_term_lists(topic_model_term_lists)
    if metadata_descriptions is not None:
        scatter_chart_explorer.inject_metadata_descriptions(metadata_descriptions)
    if term_colors is not None:
        scatter_chart_explorer.inject_term_colors(term_colors)
        if color_func is None:
            color_func = '(function(d) {return modelInfo.term_colors[d.term]})'
    if term_metadata_df is not None and term_metadata is not None:
        raise Exception('Both term_metadata_df and term_metadata cannot be values which are not None.')
    if term_metadata_df is not None:
        scatter_chart_explorer.inject_term_metadata_df(term_metadata_df)
    if term_metadata is not None:
        scatter_chart_explorer.inject_term_metadata(term_metadata)
    html_base = None
    if semiotic_square:
        html_base = get_semiotic_square_html(num_terms_semiotic_square, semiotic_square)
    if category_term_scores is not None:
        scatter_chart_explorer.inject_category_scores(category_scores=category_term_scores)
    scatter_chart_data = scatter_chart_explorer.to_dict(category=category, category_name=category_name, not_category_name=not_category_name, not_categories=not_categories, transform=transform, scores=scores, max_docs_per_category=max_docs_per_category, metadata=metadata if not callable(metadata) else metadata(corpus), alternative_text_field=alternative_text_field, neutral_category_name=neutral_category_name, extra_category_name=extra_category_name, neutral_categories=neutral_categories, extra_categories=extra_categories, background_scorer=characteristic_scorer, include_term_category_counts=include_term_category_counts, use_offsets=use_offsets)
    if line_coordinates is not None:
        scatter_chart_data['line'] = line_coordinates
    if return_data:
        return scatter_chart_data
    if tooltip_columns is not None:
        assert get_tooltip_content is None
        get_tooltip_content = get_tooltip_js_function(term_metadata_df, tooltip_column_names, tooltip_columns)
    if term_description_columns is not None:
        assert get_custom_term_html is None
        get_custom_term_html = get_custom_term_info_js_function(term_metadata_df, term_description_column_names, term_description_columns, term_word_in_term_description)
    if color_column:
        assert color_func is None
        color_func = '(function(d) {return d.etc["%s"]})' % color_column
    if color_score_column:
        assert color_func is None
        color_func = '(function(d) {return %s(d.etc["%s"])})' % (d3_color_scale if d3_color_scale is not None else 'd3.interpolateRdYlBu', color_score_column)
    if header_sorting_algos is not None:
        assert 'upper' in header_sorting_algos
        assert 'lower' in header_sorting_algos
    if left_list_column is not None:
        assert term_metadata_df is not None
        assert left_list_column in term_metadata_df
        header_sorting_algos = {'upper': '((a,b) => b.etc["' + left_list_column + '"] - a.etc["' + left_list_column + '"])', 'lower': '((a,b) => a.etc["' + left_list_column + '"] - b.etc["' + left_list_column + '"])'}
    if right_order_column is not None:
        assert right_order_column in term_metadata_df
    if show_characteristic is None:
        show_characteristic = not (asian_mode or use_non_text_features)
    scatterplot_structure = ScatterplotStructure(VizDataAdapter(scatter_chart_data), width_in_pixels=width_in_pixels, height_in_pixels=height_in_pixels, max_snippets=max_snippets, color=d3_color_scale, grey_zero_scores=gray_zero_scores, sort_by_dist=sort_by_dist, reverse_sort_scores_for_not_category=reverse_sort_scores_for_not_category, use_full_doc=use_full_doc, asian_mode=asian_mode, match_full_line=match_full_line, use_non_text_features=use_non_text_features, show_characteristic=show_characteristic, word_vec_use_p_vals=word_vec_use_p_vals, max_p_val=max_p_val, save_svg_button=save_svg_button, p_value_colors=p_value_colors, x_label=x_label, y_label=y_label, show_top_terms=show_top_terms, show_neutral=show_neutral, get_tooltip_content=get_tooltip_content, x_axis_values=x_axis_values, y_axis_values=y_axis_values, color_func=color_func, show_axes=show_axes, horizontal_line_y_position=horizontal_line_y_position, vertical_line_x_position=vertical_line_x_position, show_extra=show_extra, do_censor_points=censor_points, center_label_over_points=center_label_over_points, x_axis_labels=x_axis_labels, y_axis_labels=y_axis_labels, topic_model_preview_size=topic_model_preview_size, vertical_lines=vertical_lines, unified_context=unified_context, show_category_headings=show_category_headings, highlight_selected_category=highlight_selected_category, show_cross_axes=show_cross_axes, div_name=div_name, alternative_term_func=alternative_term_func, include_all_contexts=include_all_contexts, show_axes_and_cross_hairs=show_axes_and_cross_hairs, show_diagonal=show_diagonal, use_global_scale=use_global_scale, x_axis_values_format=x_axis_values_format, y_axis_values_format=y_axis_values_format, max_overlapping=max_overlapping, show_corpus_stats=show_corpus_stats, sort_doc_labels_by_name=sort_doc_labels_by_name, enable_term_category_description=enable_term_category_description, always_jump=always_jump, get_custom_term_html=get_custom_term_html, header_names=header_names, header_sorting_algos=header_sorting_algos, ignore_categories=ignore_categories, background_labels=background_labels, label_priority_column=label_priority_column, text_color_column=text_color_column, text_size_column=text_size_column, suppress_text_column=suppress_text_column, background_color=background_color, censor_point_column=censor_point_column, right_order_column=right_order_column, subword_encoding=subword_encoding, top_terms_length=top_terms_length, top_terms_left_buffer=top_terms_left_buffer, get_column_header_html=get_column_header_html, term_word=term_word_in_term_description, show_term_etc=show_term_etc, sort_contexts_by_meta=sort_contexts_by_meta, suppress_circles=suppress_circles, category_colors=category_colors, document_word=document_word, document_word_plural=document_word_plural, category_order=category_order, include_gradient=include_gradient, left_gradient_term=left_gradient_term, middle_gradient_term=middle_gradient_term, right_gradient_term=right_gradient_term, gradient_text_color=gradient_text_color, gradient_colors=gradient_colors, category_term_score_scaler=category_term_score_scaler, show_chart=show_chart)
    if return_scatterplot_structure:
        return scatterplot_structure
    return BasicHTMLFromScatterplotStructure(scatterplot_structure).to_html(protocol=protocol, d3_url=d3_url, d3_scale_chromatic_url=d3_scale_chromatic_url, html_base=html_base)

def produce_scattertext_html(term_doc_matrix, category, category_name, not_category_name, protocol='https', minimum_term_frequency=DEFAULT_MINIMUM_TERM_FREQUENCY, pmi_threshold_coefficient=DEFAULT_PMI_THRESHOLD_COEFFICIENT, max_terms=None, filter_unigrams=False, height_in_pixels=None, width_in_pixels=None, term_ranker=termranking.AbsoluteFrequencyRanker):
    """Returns html code of visualization.

    Parameters
    ----------
    term_doc_matrix : TermDocMatrix
        Corpus to use
    category : str
        name of category column
    category_name: str
        name of category to mine for
    not_category_name: str
        name of everything that isn't in category
    protocol : str
        optional, used prototcol of , http or https
    minimum_term_frequency : int, optional
        Minimum number of times word needs to appear to make it into visualization.
    pmi_threshold_coefficient : int, optional
        Filter out bigrams with a PMI of < 2 * pmi_threshold_coefficient. Default is 6.
    max_terms : int, optional
        Maximum number of terms to include in visualization.
    filter_unigrams : bool
        default False, do we filter unigrams that only occur in one bigram
    width_in_pixels: int
        width of viz in pixels, if None, default to JS's choice
    height_in_pixels: int
        height of viz in pixels, if None, default to JS's choice
    term_ranker : TermRanker
        TermRanker class for determining term frequency ranks.

    Returns
    -------
        str, html of visualization
    """
    scatter_chart_data = ScatterChart(term_doc_matrix=term_doc_matrix, minimum_term_frequency=minimum_term_frequency, pmi_threshold_coefficient=pmi_threshold_coefficient, filter_unigrams=filter_unigrams, max_terms=max_terms, term_ranker=term_ranker).to_dict(category=category, category_name=category_name, not_category_name=not_category_name, transform=percentile_alphabetical)
    scatterplot_structure = ScatterplotStructure(VizDataAdapter(scatter_chart_data), width_in_pixels, height_in_pixels)
    return BasicHTMLFromScatterplotStructure(scatterplot_structure).to_html(protocol=protocol)

def produce_semiotic_square_explorer(semiotic_square: SemioticSquare, x_label, y_label, category_name=None, not_category_name=None, neutral_category_name=None, num_terms_semiotic_square=None, get_tooltip_content=None, x_axis_values=None, y_axis_values=None, color_func=None, axis_scaler=scale_neg_1_to_1_with_zero_mean, **kwargs):
    """
    Produces a semiotic square visualization.

    Parameters
    ----------
    semiotic_square : SemioticSquare
        The basis of the visualization
    x_label : str
        The x-axis label in the scatter plot.  Relationship between `category_a` and `category_b`.
    y_label
        The y-axis label in the scatter plot.  Relationship neutral term and complex term.
    category_name : str or None
        Name of category to use.  Defaults to category_a.
    not_category_name : str or None
        Name of everything that isn't in category.  Defaults to category_b.
    neutral_category_name : str or None
        Name of neutral set of data.  Defaults to "Neutral".
    num_terms_semiotic_square : int or None
        10 by default. Number of terms to show in semiotic square.
    get_tooltip_content : str or None
        Defaults to tooltip showing z-scores on both axes.
    x_axis_values : list, default None
        Value-labels to show on x-axis. [-2.58, -1.96, 0, 1.96, 2.58] is the default
    y_axis_values : list, default None
        Value-labels to show on y-axis. [-2.58, -1.96, 0, 1.96, 2.58] is the default
    color_func : str, default None
        Javascript function to control color of a point.  Function takes a parameter
        which is a dictionary entry produced by `ScatterChartExplorer.to_dict` and
        returns a string. Defaults to RdYlBl on x-axis, and varying saturation on y-axis.
    axis_scaler : lambda, default scale_neg_1_to_1_with_zero_mean_abs_max
        Scale values to fit axis
    Remaining arguments are from `produce_scattertext_explorer`.

    Returns
    -------
        str, html of visualization
    """
    if category_name is None:
        category_name = semiotic_square.category_a_
    if not_category_name is None:
        not_category_name = semiotic_square.category_b_
    if get_tooltip_content is None:
        get_tooltip_content = '(function(d) {return d.term + "<br/>%s: " + Math.round(d.ox*1000)/1000+"<br/>%s: " + Math.round(d.oy*1000)/1000})' % (x_label, y_label)
    if color_func is None:
        color_func = '(function(d) {return d3.interpolateRdYlBu(d.x)})'
    '\n    my_scaler = scale_neg_1_to_1_with_zero_mean_abs_max\n    if foveate:\n        my_scaler = scale_neg_1_to_1_with_zero_mean_rank_abs_max\n    '
    axes = semiotic_square.get_axes()
    return produce_scattertext_explorer(semiotic_square.term_doc_matrix_, category=semiotic_square.category_a_, category_name=category_name, not_category_name=not_category_name, not_categories=[semiotic_square.category_b_], scores=-axes['x'], sort_by_dist=False, x_coords=axis_scaler(-axes['x']), y_coords=axis_scaler(axes['y']), original_x=-axes['x'], original_y=axes['y'], show_characteristic=False, show_top_terms=False, x_label=x_label, y_label=y_label, semiotic_square=semiotic_square, neutral_categories=semiotic_square.neutral_categories_, show_neutral=True, neutral_category_name=neutral_category_name, num_terms_semiotic_square=num_terms_semiotic_square, get_tooltip_content=get_tooltip_content, x_axis_values=x_axis_values, y_axis_values=y_axis_values, term_colors=axes['color'].to_dict(), text_color_column='color', term_metadata_df=axes, show_axes=False, **kwargs)

def produce_four_square_explorer(four_square, x_label=None, y_label=None, a_category_name=None, b_category_name=None, not_a_category_name=None, not_b_category_name=None, num_terms_semiotic_square=None, get_tooltip_content=None, x_axis_values=None, y_axis_values=None, color_func=None, axis_scaler=scale_neg_1_to_1_with_zero_mean, **kwargs):
    """
    Produces a semiotic square visualization.

    Parameters
    ----------
    four_square : FourSquare
        The basis of the visualization
    x_label : str
        The x-axis label in the scatter plot.  Relationship between `category_a` and `category_b`.
    y_label
        The y-axis label in the scatter plot.  Relationship neutral term and complex term.
    a_category_name : str or None
        Name of category to use.  Defaults to category_a.
    b_category_name : str or None
        Name of everything that isn't in category.  Defaults to category_b.
    not_a_category_name : str or None
        Name of neutral set of data.  Defaults to "Neutral".
    not_b_category_name: str or None
        Name of neutral set of data.  Defaults to "Extra".
    num_terms_semiotic_square : int or None
        10 by default. Number of terms to show in semiotic square.
    get_tooltip_content : str or None
        Defaults to tooltip showing z-scores on both axes.
    x_axis_values : list, default None
        Value-labels to show on x-axis. [-2.58, -1.96, 0, 1.96, 2.58] is the default
    y_axis_values : list, default None
        Value-labels to show on y-axis. [-2.58, -1.96, 0, 1.96, 2.58] is the default
    color_func : str, default None
        Javascript function to control color of a point.  Function takes a parameter
        which is a dictionary entry produced by `ScatterChartExplorer.to_dict` and
        returns a string. Defaults to RdYlBl on x-axis, and varying saturation on y-axis.
    axis_scaler : lambda, default scale_neg_1_to_1_with_zero_mean_abs_max
        Scale values to fit axis
    Remaining arguments are from `produce_scattertext_explorer`.

    Returns
    -------
        str, html of visualization
    """
    if a_category_name is None:
        a_category_name = four_square.get_labels()['a_label']
        if a_category_name is None or a_category_name == '':
            a_category_name = four_square.category_a_list_[0]
    if b_category_name is None:
        b_category_name = four_square.get_labels()['b_label']
        if b_category_name is None or b_category_name == '':
            b_category_name = four_square.category_b_list_[0]
    if not_a_category_name is None:
        not_a_category_name = four_square.get_labels()['not_a_label']
        if not_a_category_name is None or not_a_category_name == '':
            not_a_category_name = four_square.not_category_a_list_[0]
    if not_b_category_name is None:
        not_b_category_name = four_square.get_labels()['not_b_label']
        if not_b_category_name is None or not_b_category_name == '':
            not_b_category_name = four_square.not_category_b_list_[0]
    if x_label is None:
        x_label = a_category_name + '-' + b_category_name
    if y_label is None:
        y_label = not_a_category_name + '-' + not_b_category_name
    if get_tooltip_content is None:
        get_tooltip_content = '(function(d) {return d.term + "<br/>%s: " + Math.round(d.ox*1000)/1000+"<br/>%s: " + Math.round(d.oy*1000)/1000})' % (x_label, y_label)
    "\n    # Commenting due to label color change in semiotic square viewer\n    if color_func is None:\n        # this desaturates\n        # color_func = '(function(d) {var c = d3.hsl(d3.interpolateRdYlBu(d.x)); c.s *= d.y; return c;})'\n        color_func = '(function(d) {return d3.interpolateRdYlBu(d.x)})'\n    "
    '\n    my_scaler = scale_neg_1_to_1_with_zero_mean_abs_max\n    if foveate:\n        my_scaler = scale_neg_1_to_1_with_zero_mean_rank_abs_max\n    '
    axes = four_square.get_axes()
    if 'scores' not in kwargs:
        kwargs['scores'] = -axes['x']
    return produce_scattertext_explorer(four_square.term_doc_matrix_, category=list(set(four_square.category_a_list_) - set(four_square.category_b_list_))[0], category_name=a_category_name, not_category_name=b_category_name, not_categories=four_square.category_b_list_, neutral_categories=four_square.not_category_a_list_, extra_categories=four_square.not_category_b_list_, sort_by_dist=False, x_coords=axis_scaler(-axes['x']), y_coords=axis_scaler(axes['y']), original_x=-axes['x'], original_y=axes['y'], show_characteristic=False, show_top_terms=False, x_label=x_label, y_label=y_label, semiotic_square=four_square, show_neutral=True, neutral_category_name=not_a_category_name, show_extra=True, extra_category_name=not_b_category_name, num_terms_semiotic_square=num_terms_semiotic_square, get_tooltip_content=get_tooltip_content, x_axis_values=x_axis_values, y_axis_values=y_axis_values, color_func=color_func, term_colors=axes['color'].to_dict(), text_color_column='color', term_metadata_df=axes, show_axes=False, **kwargs)

def produce_four_square_axes_explorer(four_square_axes, x_label=None, y_label=None, num_terms_semiotic_square=None, get_tooltip_content=None, x_axis_values=None, y_axis_values=None, color_func=None, axis_scaler=scale_neg_1_to_1_with_zero_mean, **kwargs):
    """
    Produces a semiotic square visualization.

    Parameters
    ----------
    four_square : FourSquareAxes
        The basis of the visualization
    x_label : str
        The x-axis label in the scatter plot.  Relationship between `category_a` and `category_b`.
    y_label
        The y-axis label in the scatter plot.  Relationship neutral term and complex term.
    not_b_category_name: str or None
        Name of neutral set of data.  Defaults to "Extra".
    num_terms_semiotic_square : int or None
        10 by default. Number of terms to show in semiotic square.
    get_tooltip_content : str or None
        Defaults to tooltip showing z-scores on both axes.
    x_axis_values : list, default None
        Value-labels to show on x-axis. [-2.58, -1.96, 0, 1.96, 2.58] is the default
    y_axis_values : list, default None
        Value-labels to show on y-axis. [-2.58, -1.96, 0, 1.96, 2.58] is the default
    color_func : str, default None
        Javascript function to control color of a point.  Function takes a parameter
        which is a dictionary entry produced by `ScatterChartExplorer.to_dict` and
        returns a string. Defaults to RdYlBl on x-axis, and varying saturation on y-axis.
    axis_scaler : lambda, default scale_neg_1_to_1_with_zero_mean_abs_max
        Scale values to fit axis
    Remaining arguments are from `produce_scattertext_explorer`.

    Returns
    -------
        str, html of visualization
    """
    if x_label is None:
        x_label = four_square_axes.left_category_name_ + '-' + four_square_axes.right_category_name_
    if y_label is None:
        y_label = four_square_axes.top_category_name_ + '-' + four_square_axes.bottom_category_name_
    if get_tooltip_content is None:
        get_tooltip_content = '(function(d) {return d.term + "<br/>%s: " + Math.round(d.ox*1000)/1000+"<br/>%s: " + Math.round(d.oy*1000)/1000})' % (x_label, y_label)
    "\n    if color_func is None:\n        # this desaturates\n        # color_func = '(function(d) {var c = d3.hsl(d3.interpolateRdYlBu(d.x)); c.s *= d.y; return c;})'\n        color_func = '(function(d) {return d3.interpolateRdYlBu(d.x)})'\n    "
    axes = four_square_axes.get_axes()
    if 'scores' not in kwargs:
        kwargs['scores'] = -axes['x']
    '\n    my_scaler = scale_neg_1_to_1_with_zero_mean_abs_max\n    if foveate:\n        my_scaler = scale_neg_1_to_1_with_zero_mean_rank_abs_max\n    '
    return produce_scattertext_explorer(four_square_axes.term_doc_matrix_, category=four_square_axes.left_categories_[0], category_name=four_square_axes.left_category_name_, not_categories=four_square_axes.right_categories_, not_category_name=four_square_axes.right_category_name_, neutral_categories=four_square_axes.top_categories_, neutral_category_name=four_square_axes.top_category_name_, extra_categories=four_square_axes.bottom_categories_, extra_category_name=four_square_axes.bottom_category_name_, sort_by_dist=False, x_coords=axis_scaler(-axes['x']), y_coords=axis_scaler(axes['y']), original_x=-axes['x'], original_y=axes['y'], show_characteristic=False, show_top_terms=False, x_label=x_label, y_label=y_label, semiotic_square=four_square_axes, show_neutral=True, show_extra=True, num_terms_semiotic_square=num_terms_semiotic_square, get_tooltip_content=get_tooltip_content, x_axis_values=x_axis_values, y_axis_values=y_axis_values, color_func=color_func, term_colors=axes['color'].to_dict(), text_color_column='color', term_metadata_df=axes, show_axes=False, **kwargs)

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

def build(self):
    """
		Returns
		-------
		pd.Series, TermDocMatrix
		"""
    return (self.get_priors(), self.term_doc_mat)

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

def inject_term_metadata_df(self, metadata_df):
    """

        :param metadata_df: pd.DataFrame, indexed on terms with columns as structure
        :return: ScatterChartExplorer
        """
    term_metadata_dict = metadata_df.T.to_dict()
    return self.inject_term_metadata(term_metadata_dict)

class BackgroundFrequenciesFromCorpus(BackgroundFrequencyDataFramePreparer):

    def __init__(self, corpus, exclude_categories=[]):
        self.background_df = pd.DataFrame(corpus.remove_categories(exclude_categories).get_term_freq_df().sum(axis=1)).rename(columns={0: 'background'})

    def get_background_frequency_df(self):
        return self.background_df

    def get_background_rank_df(self):
        return self.prep_background_frequency(self.get_background_frequency_df())

def __init__(self, corpus, exclude_categories=[]):
    self.background_df = pd.DataFrame(corpus.remove_categories(exclude_categories).get_term_freq_df().sum(axis=1)).rename(columns={0: 'background'})

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

def test_get_unigram_corpus(self):
    tdm = make_a_test_term_doc_matrix()
    uni_tdm = tdm.get_unigram_corpus()
    term_df = tdm.get_term_freq_df()
    uni_term_df = uni_tdm.get_term_freq_df()
    self.assertEqual(set((term for term in term_df.index if ' ' not in term and "'" not in term)), set(uni_term_df.index))

def test_term_scores_background(self):
    hamlet = get_hamlet_term_doc_matrix()
    df = hamlet.get_scaled_f_scores_vs_background(scaler_algo='none')
    self.assertEqual({u'corpus', u'background', u'Scaled f-score'}, set(df.columns))
    self.assertEqual(list(df.index[:3]), ['polonius', 'laertes', 'osric'])
    df = hamlet.get_posterior_mean_ratio_scores_vs_background()
    self.assertEqual({u'corpus', u'background', u'Log Posterior Mean Ratio'}, set(df.columns))
    self.assertEqual(list(df.index[:3]), ['hamlet', 'horatio', 'claudius'])

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

def _test_get_background_corpus(self):
    tdm = get_hamlet_term_doc_matrix()
    back_df = pd.DataFrame({'word': ['a', 'bee'], 'background': [3, 1]})
    tdm.set_background_corpus(back_df)
    print(tdm.get_background_corpus().to_dict())
    self.assertEqual(tdm.get_background_corpus().to_dict(), back_df.to_dict())
    tdm.set_background_corpus(tdm)
    self.assertEqual(set(tdm.get_background_corpus().to_dict().keys()), set(['word', 'background']))

def test_get_metadata_freq_df(self):
    hamlet_meta = build_hamlet_jz_corpus_with_meta()
    mdf = hamlet_meta.get_metadata_freq_df()
    self.assertEqual(list(mdf.columns), ['hamlet freq', 'jay-z/r. kelly freq'])
    mdf = hamlet_meta.get_metadata_freq_df('')
    self.assertEqual(list(mdf.columns), ['hamlet', 'jay-z/r. kelly'])

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

def make_viz_data_adapter():
    return VizDataAdapter(PAYLOAD)

class TestSemioticSquareFromAxes(TestCase):

    @classmethod
    def setUp(cls):
        categories, documents = get_docs_categories()
        cls.df = pd.DataFrame({'category': categories, 'text': documents})
        cls.corpus = CorpusFromPandas(cls.df, 'category', 'text', nlp=whitespace_nlp).build()

    def test_main(self):
        terms = self.corpus.get_terms()
        axes = pd.DataFrame({'x': [len(x) for x in terms], 'y': [sum([ord(c) for c in x]) * 1.0 / len(x) for x in terms]}, index=terms)
        axes['x'] = axes['x'] - axes['x'].median()
        axes['y'] = axes['y'] - axes['y'].median()
        x_axis_label = 'len'
        y_axis_label = 'alpha'
        with self.assertRaises(AssertionError):
            SemioticSquareFromAxes(self.corpus, axes.iloc[:3], x_axis_label, y_axis_label)
        with self.assertRaises(AssertionError):
            axes2 = axes.copy()
            axes2.loc['asdjfksafjd'] = pd.Series({'x': 3, 'y': 3})
            SemioticSquareFromAxes(self.corpus, axes2, x_axis_label, y_axis_label)
        with self.assertRaises(AssertionError):
            SemioticSquareFromAxes(self.corpus, axes2[['x']], x_axis_label, y_axis_label)
        with self.assertRaises(AssertionError):
            axes2 = axes.copy()
            axes2['a'] = 1
            SemioticSquareFromAxes(self.corpus, axes2, x_axis_label, y_axis_label)
        semsq = SemioticSquareFromAxes(self.corpus, axes, x_axis_label, y_axis_label)
        self.assertEqual(semsq.get_labels(), {'a_and_b_label': 'alpha', 'a_and_not_b_label': 'not-len', 'a_label': 'not-len; alpha', 'b_and_not_a_label': 'len', 'b_label': 'len; alpha', 'not_a_and_not_b_label': 'not-alpha', 'not_a_label': 'len; not-alpha', 'not_b_label': 'not-len; not-alpha'})
        self.assertEqual(semsq.get_axes().to_csv(), axes.to_csv())
        self.assertEqual(semsq.get_lexicons(3), {'a': ['st', 'up', 'usurp'], 'a_and_b': ['usurp', 'worlds', 'thou'], 'a_and_not_b': ['and', 'did', 'i'], 'b': ['sometimes', 'brooklyn', 'returned'], 'b_and_not_a': ['sometimes march', 'together with', 'did sometimes'], 'not_a': ['i charge', 'fair and', 'charge thee'], 'not_a_and_not_b': ['is a', 'is i', 'i charge'], 'not_b': ['is a', 'is i', 'it is']})

def test_main(self):
    terms = self.corpus.get_terms()
    axes = pd.DataFrame({'x': [len(x) for x in terms], 'y': [sum([ord(c) for c in x]) * 1.0 / len(x) for x in terms]}, index=terms)
    axes['x'] = axes['x'] - axes['x'].median()
    axes['y'] = axes['y'] - axes['y'].median()
    x_axis_label = 'len'
    y_axis_label = 'alpha'
    with self.assertRaises(AssertionError):
        SemioticSquareFromAxes(self.corpus, axes.iloc[:3], x_axis_label, y_axis_label)
    with self.assertRaises(AssertionError):
        axes2 = axes.copy()
        axes2.loc['asdjfksafjd'] = pd.Series({'x': 3, 'y': 3})
        SemioticSquareFromAxes(self.corpus, axes2, x_axis_label, y_axis_label)
    with self.assertRaises(AssertionError):
        SemioticSquareFromAxes(self.corpus, axes2[['x']], x_axis_label, y_axis_label)
    with self.assertRaises(AssertionError):
        axes2 = axes.copy()
        axes2['a'] = 1
        SemioticSquareFromAxes(self.corpus, axes2, x_axis_label, y_axis_label)
    semsq = SemioticSquareFromAxes(self.corpus, axes, x_axis_label, y_axis_label)
    self.assertEqual(semsq.get_labels(), {'a_and_b_label': 'alpha', 'a_and_not_b_label': 'not-len', 'a_label': 'not-len; alpha', 'b_and_not_a_label': 'len', 'b_label': 'len; alpha', 'not_a_and_not_b_label': 'not-alpha', 'not_a_label': 'len; not-alpha', 'not_b_label': 'not-len; not-alpha'})
    self.assertEqual(semsq.get_axes().to_csv(), axes.to_csv())
    self.assertEqual(semsq.get_lexicons(3), {'a': ['st', 'up', 'usurp'], 'a_and_b': ['usurp', 'worlds', 'thou'], 'a_and_not_b': ['and', 'did', 'i'], 'b': ['sometimes', 'brooklyn', 'returned'], 'b_and_not_a': ['sometimes march', 'together with', 'did sometimes'], 'not_a': ['i charge', 'fair and', 'charge thee'], 'not_a_and_not_b': ['is a', 'is i', 'i charge'], 'not_b': ['is a', 'is i', 'it is']})

def get_test_semiotic_square():
    corpus = get_test_corpus()
    semsq = SemioticSquare(corpus, 'hamlet', 'jay-z/r. kelly', ['swift'])
    return semsq

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

class TestDiachronicTermMiner(TestCase):

    @classmethod
    def setUpClass(cls):
        df = pd.read_csv(io.StringIO("publish_date,headline_text,publish_yearmonth,publish_month\n20150409,rural sa rural reporter the tale of two orchards,201504,04\n20111206,roar get ulsan in champions league draw,201112,12\n20101201,130m annual cost to run desal plant,201012,12\n20040802,farmers worried about wto agreement loopholes,200408,08\n20170808,same sex marriage plebiscite attempt expected to be blocked,201708,08\n20130621,executives spend a night on the streets to experience homelessn,201306,06\n20070613,nsw govt signs pollution reduction agreement with,200706,06\n20060209,nt doctors show support for abortion drug,200602,02\n20130718,crash driver sought by police,201307,07\n20061119,howard disputes blairs iraq comments,200611,11\n20070725,german reporter released in afghanistan,200707,07\n20120224,hammer heal to coach kings,201202,02\n20090428,written apology over holocaust denial,200904,04\n20141024,unions hand tasmanian government alternative savings plan,201410,10\n20061118,shark gets some pride back,200611,11\n20130206,older watson concerned for jobe bombers,201302,02\n20140430,forum to showcase mid west mining developments,201404,04\n20140429,former wa treasurer buswell admits to driving offences,201404,04\n20070621,weather to determine sports fields opening,200706,06\n20140803,travel blamed for increasing rate of hiv in wa,201408,08\n20050715,stuey takes aim at green jersey,200507,07\n20061219,public urged to help combat fruit fly threat,200612,12\n20040302,robben chooses chelsea over united,200403,03\n20030820,jury to continue deliberations in hanson fraud,200308,08\n20030323,baghdads military facilities targeted in latest,200303,03\n20140417,an india holds biggest day of voting,201404,04\n20050102,car bomb attack kills 18 iraqi national guards,200501,01\n20080818,citation boosts vietnam veterans day significance,200808,08\n20131111,wenceslas magun speaks to pacific beat,201311,11\n20130325,an vanuatu gets new pm,201303,03\n20160423,woman killed in crash with stobie pole,201604,04\n20091006,message spread that attacks not tolerated brumby,200910,10\n20040707,iraq adopts new security laws,200407,07\n20030916,poland gets record case of the blues,200309,09\n20040406,jordan sentences eight to death over diplomat,200404,04\n20101022,arnold to relish cox plate pressure,201010,10\n20130610,lack of data creates concern over true extent of medical errors,201306,06\n20060317,labor warns on minority government,200603,03\n20100808,labor to ban truants from playing sport,201008,08\n20071210,sharks spotted in esperance port,200712,12\n20041224,aust troops to celebrate christmas in iraq,200412,12\n20090819,jail term for rsl theft,200908,08\n20070408,closer am1nodisplay,200704,04\n20161114,nt man jailed for crimes against children,201611,11\n20051003,union warns ir changes threaten australian way of,200510,10\n20041007,afghan children lose high court battle against,200410,10\n20130506,parkinsons test sought,201305,05\n20110329,police accused of not probing brutality claim,201103,03\n20090828,cairns trip ends in top end lsd bust,200908,08\n20120816,coroner criticises ambulance 'ramping',201208,08\n20130121,new recruits for womens cycling team,201301,01\n20050203,uni to hold tropical science precinct talks,200502,02\n20041110,jetstar asia prepares for launch,200411,11\n20090326,mccreadie granted immunity,200903,03\n20170821,one killed in france after car crashes into bus shelters,201708,08\n20081031,gambhir handed one test ban,200810,10\n20150527,school communities unsettled about prospect of school closures,201505,05\n20050829,man accused of ramming car with children inside,200508,08\n20130821,van park owner pursues legal options over free,201308,08\n20060406,national network to track pseudoephedrine sales,200604,04\n20040708,big sports complex planned near maitland,200407,07\n20100714,ex afl player paid nearly 80k to conman,201007,07\n20120711,victory retain milligans services,201207,07\n20080221,bad weather delays dalrymple bay coal terminal,200802,02\n20151021,govt department tests scales get what paid for,201510,10\n20090208,battered jets sign italian striker vignaroli,200902,02\n20130205,capital hill monday 4 february 2013,201302,02\n20161013,medicinal cannabis register considered tasmania,201610,10\n20041202,underwood sworn in as chief justice,200412,12\n20110701,rta heeds call for pedestrian safety upgrade,201107,07\n20120723,miners say cost of business too high,201207,07\n20090103,funding secures more aerial shark patrols,200901,01\n20170603,were australias first people nomadic,201706,06\n20031019,tributes pour in for spanish writer montalban,200310,10\n20080301,interview ricky ponting,200803,03\n20100831,forlan at the double for atletico,201008,08\n20060907,lawyers say vizards silence is unfair to hilliard,200609,09\n20060524,shoulder troubles for roddick ahead of french,200605,05\n20080809,tennis form guide mens singles,200808,08\n20171206,family of betty dixon still asking questions as cold case ends,201712,12\n20080715,fed court overturns annoying ban,200807,07\n20120131,rare earth industry developing rapidly,201201,01\n20131117,tremlett prior set to start for england,201311,11\n20121114,eltons latest book explores brothers relationship,201211,11\n20070316,evans a man of honesty and integrity,200703,03\n20040908,financial lobby criticises labor tax package,200409,09\n20030604,health service urged to review gp anaesthetist,200306,06\n20030410,restrictions for melbourne as water cost rises,200304,04\n20161022,pamela anderson speaks out about pornographys numbing effects,201610,10\n20120804,fire warning,201208,08\n20110329,paramedic gives evidence at road crash murder trial,201103,03\n20160711,response to labor mp call to ban fracking in south west,201607,07\n20111007,health razor gang disbands early,201110,10\n20141023,acid attacks on women spark protests in iran,201410,10\n20100401,mp airs fears for forestry jobs,201004,04\n20121124,interview rianna ponting,201211,11\n20120820,tony burke talks with four corners,201208,08\n20100815,20 million affected by pakistan floods,201008,08\n20091222,china planning to execute briton next week,200912,12\n20100819,woman granted bail over torso in bush find,201008,08\n20091103,christmas island locals forgotten in asylum debate,200911,11\n20071027,eden monaro headed for labor poll,200710,10\n20121027,alleged hijackers flown to sri lanka to face charges,201210,10\n20160320,powerlifting: watch a benchpress; a deadlift and a,201603,03\n20130913,new york jets' mark sanchez facing season ending shoulder sur,201309,09\n20120324,we have to put bligh legacy behind us,201203,03\n20050524,budget sees return of investment properties tax,200505,05\n20101117,germany increases security amid terrorist threat,201011,11\n20150713,newcastle man in coma after drunken argument,201507,07\n20140812,titans need help in afl battle,201408,08\n20170119,vegemite back in australian hands,201701,01\n20070508,utai out cutler in for dogs,200705,05\n20160818,artists opens up world of picture book illustrations,201608,08\n20150731,north queensland ports urge ports bill fine tuning,201507,07\n20060623,wimmera sheep sales increase,200606,06\n20120105,opposition queries extra senior bureaucrats,201201,01\n20120514,hume result,201205,05\n20070909,victorians going green,200709,09\n20121113,broken hill baby birds back in their nests,201211,11\n20111023,drunk driving police,201110,10\n20070806,four arrested over safe breaks,200708,08\n20131214,sri lanka retain twenty20 number one ranking,201312,12\n20061122,sydney tourism snubs regional areas,200611,11\n20070512,curbishley confident of players resolve,200705,05\n20050924,ten killed in gaza hamas rally blast,200509,09\n20080804,police dig for baby 12 years on,200808,08\n20090602,centenary show for gin gin,200906,06\n20090426,g20 ministers still cautious on global economy swan,200904,04\n20080918,david kidman from ferrier hodgson talks about the,200809,09\n20091101,beauty with a twist,200911,11\n20091203,henderson talks up brave 2030 plan,200912,12\n20070913,power in no rush to decide political future,200709,09\n20091209,swine flu far milder than feared,200912,12\n20091216,us house of reps honours miles davis album,200912,12\n20160816,two dead in crash on eyre highway near balladonia,201608,08\n20091022,worms linked to coeliac relief,200910,10\n20140401,wafarmers urges growers to decrease debt,201404,04\n20121115,fmg diversifies into oil and gas,201211,11\n20040121,leaders may need to resolve trade talks,200401,01\n20081207,tasmanians urged to spend within their means,200812,12\n20140822,sa police join search for missing warrnambool man,201408,08\n20051219,company fined after explosions injured workers,200512,12\n20081013,thai queen to attend protesters funeral,200810,10\n20111124,global stocks close,201111,11\n20051221,aquaculture group upset with course axing,200512,12\n20121224,somali troops end hostages' three year ordeal,201212,12\n20090804,bligh vows to refer email row to cmc,200908,08\n20100714,appointed to healths top job,201007,07\n20100128,remote schools low on my school site,201001,01\n20140505,festival visitors get taste for regions produce,201405,05\n20030413,canegrowers push for ethanol mix in all petrol,200304,04\n20110409,clarke ton helps aussies to victory,201104,04\n20151207,police seek witnesses to fatal tintinara road crash,201512,12\n20041013,tax relief tipped for wa home buyers,200410,10\n20050312,bulls charge towards home final,200503,03\n20151125,three men dead in perth workplace accidents,201511,11\n20160516,federal government considers assistance package dairy farmers,201605,05\n20130523,minister jeanette powell outlines strategy for victoria's abo,201305,05\n20140919,jackson primary school censorship,201409,09\n20090909,russians behind cyber crime says afp,200909,09\n20030709,indias congress considers coalition to oust bjp,200307,07\n20050425,council plans memorial to grassby,200504,04\n20090810,slovak mine blast traps 19 miners,200908,08\n20121123,some tourism operators say no to schoolies,201211,11\n20150507,australian farming families the feature of a new,201505,05\n20120322,young roos,201203,03\n20101206,katich has scans on achilles injury,201012,12\n20070627,pricey sydney tops census again,200706,06\n20060319,opals enjoy another big win,200603,03\n20160318,albany residents to be quizzed over muttonbird reserve,201603,03\n20150902,china fta senator colbeck trade,201509,09\n20160609,greyhound racing nsw charges 179 trainers owners,201606,06\n20060220,internet smss blamed for big crowd at party,200602,02\n20031203,renison mine to remain closed,200312,12\n20151215,newcastle giving tree finished for 2015,201512,12\n20070707,afp release five doctors after questioning,200707,07\n20121130,an bangladesh inspections,201211,11\n20121008,man quizzed over high speed chase,201210,10\n20080409,lennon under fire over kons resignation,200804,04\n20130510,compo concerns,201305,05\n20150730,police plead for clues to tenterden road crash,201507,07\n20081014,an open and shut case for nw road,200810,10\n20100511,scott daughters settle estate fight,201005,05\n20080523,suitability of hensons images depends on context,200805,05\n20060622,aged care group restructures decision making,200606,06\n20150204,nff wants banks to pass on interest rate cut to farmers,201502,02\n20041118,govts urged to act on commuter train service,200411,11\n20030323,worldwide protests demand peace,200303,03\n20040601,gillespie talks up worth of zimbabwe series,200406,06\n20050506,tribunal cracks down on video evidence,200505,05\n20151021,police make arrest missing mother linda sidon gold coast,201510,10\n20121012,scientists uncover mystery of ball lightning,201210,10\n20140430,encouraging girls in engineering jpbs,201404,04\n20160816,woman charged over assault of victorian labor mp jane garrett,201608,08\n20140224,cattle saleyards canteen ladies,201402,02\n20080726,final showdown looms for tour,200807,07\n20111229,pesce a rising tide of chaos,201112,12\n20040426,former us ambassador doubts iraq wmd focus,200404,04\n20080603,evicted aborigines finish training in sydney,200806,06\n20070412,cadets to attend sandakan dawn service,200704,04\n20100425,red shirts discarded ahead of crackdown,201004,04\n20070625,four to appear in court over coolgardie burglary,200706,06\n20140812,nrn graincorp ceo,201408,08\n20101230,interview michael clarke,201012,12\n20110506,workers to mine tafe for education needs,201105,05\n20130912,wafl player has bail varied to play,201309,09\n20120809,simpson elected murray irrigation shareholder,201208,08\n20121206,ice blamed for crime spike,201212,12\n20080622,opec divided on saudi summit and production boost,200806,06\n20050513,heroin bust in adelaide,200505,05\n20051004,nrma highlights need for pacific highway attention,200510,10\n20110706,public quizzed about closed inlet,201107,07\n20150225,herbicide resistance peter newman,201502,02\n20050216,push for second kakadu uranium mine,200502,02\n20040314,murali set to join warne in 500 wicket club,200403,03\n20131104,soil carbon climate change,201311,11\n20100208,the wwfs paul gamblin says a report should put,201002,02\n20040922,indonesian presidential hopeful plans peace in aceh,200409,09\n20170405,bushfire emergency downgraded near esperance in wa,201704,04\n20120724,injured sea birds washing up inland,201207,07\n20160729,donald trump v hillary clinton star power of the conventions,201607,07\n20120522,impact of bomb blasts on the brain,201205,05\n20140811,israel palestine agree to 72 hour cease fire in gaza,201408,08\n20130610,14yos accused of armed robbery,201306,06\n20051114,mp says tafe fees soaring,200511,11\n20050419,woolworths sales up more than 14pc,200504,04\n20080907,peter leek breaks butterfly world record,200809,09\n20080426,jones trickett set new world records,200804,04\n20041224,karzai removes warlords from afghan cabinet,200412,12\n20120329,no confidence showdown looming,201203,03\n20110114,brazil floods mudslides kill hundreds,201101,01\n20160918,hospital parking fees petition gains support on change org,201609,09\n20140716,china gdp growth hits expectations,201407,07\n20071206,pasha findings prompt port review,200712,12\n20080627,pigeons smuggle drugs phones into rio prison,200806,06\n20071228,plucky india fights back in melbourne,200712,12\n20150419,thousands in germany protest against ttip europe us trade deal,201504,04\n20100112,rain sets up new crop for cane farmers,201001,01\n20110110,peter andre named hardest working singer,201101,01\n20120830,search becomes rescue as asylum boat found,201208,08\n20050715,manslaughter charge dropped in bondage case,200507,07\n20120822,laurie daley interview,201208,08\n20030601,williams silent on sydney ji unit claim,200306,06\n20060226,govt offers to buy back sydney harbour fishing,200602,02\n20061115,reward offered to catch roo shooter,200611,11\n20121128,report suggests turnaround for struggling boxed,201211,11\n20081024,november execution for bali bombers,200810,10\n20040513,ethnic sounds unite eurovision,200405,05\n20111128,murray darling authority chairman craig knowles,201111,11\n20160122,brisbane artist helps fans pay tribute to idols through nail art,201601,01\n20120821,australia too complacent,201208,08\n20070829,rudd pressures howard to pick election date,200708,08\n20171203,cooper cronk goes out on top announcing retirement from rep,201712,12\n20140212,oz shares surge after ceo announces departure,201402,02\n20060630,council happy to receive community funds for,200606,06\n20131113,lifeline helping miners prevent suicide,201311,11\n20100701,authorities fear grass fires deliberately lit,201007,07\n20040827,family hires security guard for protection,200408,08\n20110315,contempt of court charge against paper dropped,201103,03\n20030416,full text 13 point plan for iraq,200304,04\n20090704,nrl interview neil henry,200907,07\n20120306,sa courts,201203,03\n20060119,australia west indies postpone 2007 test series,200601,01\n20140603,bosnia finalises cup squad,201406,06\n20121127,victorian government backs down on scrapping fruit,201211,11\n20050131,perth kalgoorlie line set to reopen on weekend,200501,01\n20150428,chile volcano calbuco economy 600 million tourism eruption,201504,04\n20130313,grain prices rabobank,201303,03\n20140415,fia upholds ricciardo disqualification,201404,04\n20100425,pies embarrass dons on big stage,201004,04\n20120213,shining path leader captured,201202,02\n20160715,rescue plane goes down in goldfields hunt for missing man,201607,07\n20110901,storm wont appeal blairs ban,201109,09\n20131108,today tonight twist in gittany trial,201311,11\n20070413,tour boat profits blown away,200704,04\n20170921,farmers open the farm gate to combat carrot glut,201709,09\n20130507,qdo resignation,201305,05\n20060531,australian teams join quake aid efforts,200605,05\n20110705,bartos the public service numbers game,201107,07\n20060705,patient no shows end specialist medical service,200607,07\n20150804,multi million dollar northern farming system project,201508,08\n20171229,china foreign ministry denies claims its still,201712,12\n20110807,masterchef winner,201108,08\n20161006,for better or worse: four corners,201610,10\n20070308,rsl investigates veterans home care service,200703,03\n20090212,keane at the double for ireland,200902,02\n20080102,pakistan issues photos of bhutto death offers,200801,01\n20121113,pair charged following police shooting,201211,11\n20040304,hope for business chamber turnaround,200403,03\n20050226,cabinet to consider nightclub lock out plan,200502,02\n20061220,illawarra schools do well in hsc,200612,12\n20121112,data reveals strong regional rental markets,201211,11\n20060629,teen found safe after missing in bush for three,200606,06\n20060110,star studded field confirmed for johnnie walker,200601,01\n20120113,abc sport,201201,01\n20140702,trade balance slumps to near 2 billion deficit on fall in iron,201407,07\n20090928,star to be born again,200909,09\n20100712,experts warn against growing diabetes threat,201007,07\n20031212,rampaging roy wins cultural recognition,200312,12\n20081221,chinese warships to join anti piracy force,200812,12\n20040603,mayor highlights hidden amalgamation costs,200406,06\n20091013,locals threaten to block kokoda over crash compo,200910,10\n20081211,connex told to fix industrial dispute,200812,12\n20141204,ronja huon aquaculture salmon,201412,12\n20161102,private investor interest in henty pub,201611,11\n20100324,councils face off over oakajee,201003,03\n20160407,the peasant prince,201604,04\n20171018,daphne caruana galizias son accuses malta pm of complicity,201710,10\n20151012,barns risky detention policy,201510,10\n20130102,under age drinking a big problem in manning great lakes,201301,01\n20150918,the rbas advice for the us fed on hiking rates,201509,09\n20151027,adelaide bite baseballer's assault charge may be dropped,201510,10\n20070207,survey normal govt procedure says minister,200702,02\n20170324,anz joins the rush to raise home loan interest rates,201703,03\n20110214,work to start on new adelaide airport parking,201102,02\n20130309,interview johnathan thurston,201303,03\n20101206,west coast abalone season winds up,201012,12\n20110705,westhoff injury gives cornes his chance,201107,07\n20100930,pyne sent from chamber for hopeless jibe,201009,09\n20120515,rocks to tackle foreshore erosion woes,201205,05\n20101217,storm threat eases in south east queensland,201012,12\n20041017,richmond slips away from anthony,200410,10\n20070910,rare nsw plant faces extinction,200709,09\n20140602,clunies ross science award for gravity separator,201406,06\n20090713,angelita pires on trial for conspiracy,200907,07\n20070916,nt comes to grips with alcohol bans,200709,09\n20040929,tourism award nomination for pioneer settlement,200409,09\n20100223,australia v west indies innings highlights,201002,02\n20080508,people must be across risks and benefits of gm,200805,05\n20080624,goodes accepts ban,200806,06\n20030619,capriati and rubin win at eastbourne,200306,06\n20100610,youth job agency to close doors,201006,06\n20051110,call made to cut infrastructure project red tape,200511,11\n20130530,adam scott not planning to sue over anchoring,201305,05\n20041216,toxicologist calls for more drink spiking evidence,200412,12\n20110605,police find teen detention centre escapee,201106,06\n20060727,memorial to honour murdered sisters,200607,07\n20150908,jason day heads presidents cup team to take on us in october,201509,09\n20040702,icc confirms postponement of zimbabwe tests,200407,07\n20120413,philips bob brown,201204,04\n20080318,newcastle building society passes on rate rise,200803,03\n20121121,emma roberts avery wines,201211,11\n20101218,vics take innings points,201012,12\n20130514,nt cattle sold to vic,201305,05\n20101122,art world welcomes indigenous recruits,201011,11\n20130227,hough eyeing off moscow berth,201302,02\n20120718,an thai military outpost and village attacked,201207,07\n20110331,labors downfall the machine and the split,201103,03\n20150715,tonga pm casts doubt on country's ability to host pacific games,201507,07\n20141002,accc approves sale of acttab to tabcorp group,201410,10\n20050930,hope for power station to attract new industries,200509,09\n20140317,hamelin wake,201403,03\n20101013,11 jailed over van gogh theft,201010,10\n20090418,20 hostages freed from pirate mother ship,200904,04\n20131121,probe into 2011 police shooting in coffs harbour still incomple,201311,11\n20090920,torres double gets liverpool home,200909,09\n20100502,mayfair holding firm at quail hollow,201005,05\n20041106,samarra car bombs kill 8 wound 20,200411,11\n20080923,ses under pressure as storms hit riverina,200809,09\n20150528,australians unaware they have chronic kidney disease report,201505,05\n20080929,court hears torres strait seas claim,200809,09\n20141118,abortion row erupts between coalition candidates in ballarat,201411,11\n20090211,tornado kills 8 people in oklahoma,200902,02\n20170623,danny noonan ex afl player jailed for stealing from clients,201706,06\n20151104,efficient housing a focus for aboriginal land council's new w,201511,11\n20070416,missing elderly man found safe,200704,04\n20060607,council includes road repair funds in draft budget,200606,06\n20090903,cba feels wrath over storm collapse,200909,09\n20121209,marquez knocks out pacquiao,201212,12\n20090619,sharks fraud claims parents charged,200906,06\n20121219,ambulance reforms written off by paramedic's union,201212,12\n20151221,water sharing arrangement could be fast tracked due to contamin,201512,12\n20070514,viduka in no rush to decide future,200705,05\n20100212,penn universitys climategate findings,201002,02\n20051014,bikers ride honours sheene,200510,10\n20090201,hotter drier january,200902,02\n20091231,capital fireworks to bring in new year,200912,12\n20150327,joeys to be released into the wild after adelaide bushfires,201503,03\n20100223,amcor profit beats expectations,201002,02\n20040813,sex charges highlight need for workplace education,200408,08\n20030326,libs claim south coast seat,200303,03\n20060502,federal govt to fund airport security upgrade,200605,05\n20100710,yacht murder case begins,201007,07\n20070305,carpenter vows to force grill out of alp,200703,03\n20051006,us senate moves to ban prisoner torture,200510,10\n20121223,tendulkar retires from odis,201212,12\n20141003,nobel peace summit 'suspended' over dalai lama visa row,201410,10\n20050601,schumacher dismisses quit questions,200506,06\n20040921,parents shy away from meningococcal vaccinations,200409,09\n20121023,prince charles australian travel plans revealed,201210,10\n20140509,new mental health centre to help patients,201405,05\n20030929,lisbie hat trick stuns liverpool,200309,09\n20060202,awb kickbacks scandal puts govt under us pressure,200602,02\n20050909,man killed in head on crash,200509,09\n20130725,nrn ag minister shepp,201307,07\n20070807,croydon council delivers budget,200708,08\n20121102,an worldbank earmarks $245m for burma,201211,11\n20110523,doubt behind the aggression,201105,05\n20100826,interview brett kimmorley,201008,08\n20040703,new disease threatens qld citrus crops,200407,07\n20080522,man charged with assaulting girls wanted in qld,200805,05\n20140709,mining ojbection legislation changes,201407,07\n20160308,efforts to get more women to become truck drivers in tasmania,201603,03\n20040706,crackdown on overseas trained country doctors,200407,07\n20151119,national rural news,201511,11\n20140321,sydney light rail extension to open next week,201403,03\n20151211,doris fenbows killer alexis katsis jailed for 15 years,201512,12\n20111012,waca ceo wood resigns,201110,10\n20060824,program cuts childhood obesity rate researchers say,200608,08\n20140130,hospital forced to use surge capacity beds on regular basis,201401,01\n20101006,red cross opens doors in kalgoorlie boulder,201010,10\n20030716,boyle praises freeman as best of her generation,200307,07\n20131114,ract takes over federal groups' tourism ventures,201311,11\n20170529,queensland government to play ball over adani loan: treasurer,201705,05\n20151021,milky way galaxy star forming clouds,201510,10\n20120511,van egmond admits informal talks about leaving jets,201205,05\n20110718,more groundwater trials at mount zero,201107,07\n20051212,angel wins murgon by election,200512,12\n20100301,record rain fills heart of australia,201003,03\n20090727,council to sign algae biodiesel agreement,200907,07\n20121207,uninterrupted grain harvest nears end,201212,12\n20160824,wesfarmers richard goyder defends business council,201608,08\n20051017,briefings to be held for would be councillors,200510,10\n20040623,hobart prepares for jim bacons funeral,200406,06\n20070807,second suspected foot and mouth outbreak in britain,200708,08\n20101010,qr national float details unveiled,201010,10\n20060919,brock funeral begins in melbourne,200609,09\n20170620,family road trip tells burke and wills story through theatre,201706,06\n20151109,china and australia to share antarctic sea ice research,201511,11\n20141119,victoria beats south australia in shield,201411,11\n20150930,tas country hour wednesday 21 september 2015,201509,09\n20141015,consumer sentiment negative in westpac survey,201410,10\n20090719,india can make its own decisions clinton says,200907,07\n20140320,council urged to crack down on illegal holiday,201403,03\n20080925,dog attacks policewoman in boulder,200809,09\n20080123,springborg attempting to rebadge the national,200801,01\n20050120,houses crack in canadian cold spell,200501,01\n20130923,mining company discovers second cement spill in sugarloaf,201309,09\n20031108,us jobs figures fail to bolster markets,200311,11\n20110519,boat tragedy video released,201105,05\n20121102,call for review of water concessions,201211,11\n20120616,interview michael maguire,201206,06\n20030413,death toll rises on nsw roads,200304,04\n20110330,no verdict in airport caterer drug case,201103,03\n20100921,study to probe field days value,201009,09\n20100912,resilience will help say dogs,201009,09\n20110607,boaties rescue sparks emergency beacon reminder,201106,06\n20110628,robinson re signs with reds,201106,06\n20040110,fleming ton seals kiwi win,200401,01\n20111123,holden recalls diesel cars,201111,11\n20041012,china may sign fta with nz first,200410,10\n20130417,new radar,201304,04\n20140304,nsw country hour 4 march 2014,201403,03\n20060807,stanhope rejects tax discrepancy claims,200608,08\n20070308,downpour cancels bemboka show,200703,03\n20160718,toowoomba south lnp david janetzki claims victory in by election,201607,07\n20101208,flood peak fears ease in rockhampton,201012,12\n20050525,dumped car not linked to missing schoolboy police,200505,05\n20071115,second stage of vegie industry water saving,200711,11\n20080908,aust paralympic swimmers miss out on medals,200809,09\n20150622,geelong star kills another dolphin prompting fishery closure,201506,06\n20050417,ofc backs socceroos asian move,200504,04\n20150316,islamic state militants claim attack on checkpoint in libya,201503,03\n20080729,luhrmann on transformative experiences,200807,07\n20111115,man jailed over beer bottle glassing,201111,11\n20051031,windies coach denies players have attitude problem,200510,10\n20101119,court jails driver for running down man,201011,11\n20110503,pakistan embarrassed by intelligence failure,201105,05\n20071121,security camera funding pledge for mackay,200711,11\n20110104,police suspect careless campers behind bushfire,201101,01\n20150825,san francisco coach attempts to hose down hayne hype,201508,08\n20030315,hewitt still top dog,200303,03\n20131227,ukraine protesters rally after journalist bashed,201312,12\n20080423,bryce bligh address students at brisbane anzac,200804,04\n20080902,domestic markets flat despite interest rate cut,200809,09\n20080113,bligh approval soars to 68pc,200801,01\n20080303,southern road fatality,200803,03\n20160127,tunarama 2016 highlights port lincoln,201601,01\n20141223,warner will be ready for boxing day test,201412,12\n20150707,75yo fraser coast woman dies after suspected,201507,07\n20090515,rees urges players to come forward,200905,05\n20140311,smith agrees to four year extension at storm,201403,03\n20120511,black caviar prepares for australian finale,201205,05\n20160929,sa weather fuel shortages eyre peninsula residents stranded,201609,09\n20151209,north coast victims tell stolen generations inquiry more suppor,201512,12\n20141204,ebola global toll rises further as virus spreads in sierra leone,201412,12\n20071101,bryan cousins lashes out at media,200711,11\n20070211,clashes flare again over jerusalem mosque,200702,02\n20101220,blisters and pimples clog 000,201012,12\n20140731,australian medical association regional queenslanders obese,201407,07\n20080213,apology welcome reconciliation the next goal tas,200802,02\n20050916,two injured in skydiving accident,200509,09\n20151211,captain of honduras soccer team shot dead,201512,12\n20090102,israels labour rebounds in polls after gaza blitz,200901,01\n20111115,karumba barra centre could close,201111,11\n20090826,nelson proud of saving propellant factory,200908,08\n20130330,couple wanted over sydney diamond heist,201303,03\n20090501,mp demands more police to fill shortages,200905,05\n20141010,glenn hall re signs with north queensland cowboys,201410,10\n20140425,projections illuminate anzacs,201404,04\n"))
        df['parse'] = df.headline_text.apply(whitespace_nlp_with_sentences)
        df['publish_yearmonth'] = df['publish_yearmonth'].astype(str)
        df['publish_month'] = df['publish_month'].astype(str)
        cls.corpus = CorpusFromParsedDocuments(df, category_col='publish_yearmonth', parsed_col='parse').build()

    def test_setup(self):
        DiachronicTermMiner(self.corpus)
        with self.assertRaises(Exception):
            DiachronicTermMiner(self.corpus, timesteps_to_lag=3999)
        DiachronicTermMiner(self.corpus, timesteps_to_lag=2)
        with self.assertRaises(Exception):
            DiachronicTermMiner(self.corpus, start_category='asd')
        with self.assertRaises(Exception):
            DiachronicTermMiner(self.corpus, start_category='200304')
        DiachronicTermMiner(self.corpus, start_category='201404')
        with self.assertRaises(Exception):
            DiachronicTermMiner(self.corpus, seasonality_column='publish_montha')
        DiachronicTermMiner(self.corpus, seasonality_column='publish_month')

    def test_get_terms_to_display(self):
        df = DiachronicTermMiner(self.corpus, num_terms=10).get_display_dataframe()
        self.assertEquals(list(df.columns), ['term', 'variable', 'frequency', 'trending'])
        self.assertEquals(len(set(df.term)), 10)
        df = DiachronicTermMiner(self.corpus, num_terms=20).get_display_dataframe()
        self.assertEquals(len(set(df.term)), 20)

    def test_get_visualization(self):
        try:
            import altair
        except:
            return
        DiachronicTermMiner(self.corpus, num_terms=10).visualize()

def test_setup(self):
    DiachronicTermMiner(self.corpus)
    with self.assertRaises(Exception):
        DiachronicTermMiner(self.corpus, timesteps_to_lag=3999)
    DiachronicTermMiner(self.corpus, timesteps_to_lag=2)
    with self.assertRaises(Exception):
        DiachronicTermMiner(self.corpus, start_category='asd')
    with self.assertRaises(Exception):
        DiachronicTermMiner(self.corpus, start_category='200304')
    DiachronicTermMiner(self.corpus, start_category='201404')
    with self.assertRaises(Exception):
        DiachronicTermMiner(self.corpus, seasonality_column='publish_montha')
    DiachronicTermMiner(self.corpus, seasonality_column='publish_month')

def test_get_terms_to_display(self):
    df = DiachronicTermMiner(self.corpus, num_terms=10).get_display_dataframe()
    self.assertEquals(list(df.columns), ['term', 'variable', 'frequency', 'trending'])
    self.assertEquals(len(set(df.term)), 10)
    df = DiachronicTermMiner(self.corpus, num_terms=20).get_display_dataframe()
    self.assertEquals(len(set(df.term)), 20)

def test_get_visualization(self):
    try:
        import altair
    except:
        return
    DiachronicTermMiner(self.corpus, num_terms=10).visualize()

class TestZScores(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.corpus = build_hamlet_jz_corpus()

    def test_get_scores(self):
        result = ZScores(self.corpus).set_categories('hamlet').get_scores()
        self.assertEquals(type(result), pd.Series)
        np.testing.assert_array_equal(np.array(result.index), self.corpus.get_terms())

    def test_get_name(self):
        self.assertEquals(ZScores(self.corpus).set_categories('hamlet').get_name(), "Z-Score from Welch's T-Test")

    def test_get_ranks_meta(self):
        corpus = build_hamlet_jz_corpus_with_meta()
        self.assertEquals(ZScores(corpus).set_term_ranker(OncePerDocFrequencyRanker).set_categories('hamlet').get_name(), "Z-Score from Welch's T-Test")

@classmethod
def setUpClass(cls):
    cls.corpus = build_hamlet_jz_corpus()

class TestPhraseSelector(TestCase):

    def test_compact(self):
        tdm = build_hamlet_jz_term_doc_mat()
        c = PhraseSelector(minimum_pmi=10).compact(tdm)
        bigrams = [t for t in tdm.get_terms() if ' ' in t]
        new_bigrams = [t for t in c.get_terms() if ' ' in t]
        self.assertLess(len(new_bigrams), len(bigrams))
        self.assertTrue(set(new_bigrams) - set(bigrams) == set())

def test_compact(self):
    tdm = build_hamlet_jz_term_doc_mat()
    c = PhraseSelector(minimum_pmi=10).compact(tdm)
    bigrams = [t for t in tdm.get_terms() if ' ' in t]
    new_bigrams = [t for t in c.get_terms() if ' ' in t]
    self.assertLess(len(new_bigrams), len(bigrams))
    self.assertTrue(set(new_bigrams) - set(bigrams) == set())

class TestRelativeEntropy(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.corpus = build_hamlet_jz_corpus()

    def test_get_scores(self):
        result = RelativeEntropy(self.corpus).set_categories('hamlet').get_scores()
        self.assertEquals(type(result), pd.Series)
        np.testing.assert_array_equal(np.array(result.index), self.corpus.get_terms())

    def test_get_name(self):
        self.assertEquals(RelativeEntropy(self.corpus).set_categories('hamlet').get_name(), 'Frankhauser Relative Entropy')

@classmethod
def setUpClass(cls):
    cls.corpus = build_hamlet_jz_corpus()

class TestFourSquareAxes(TestCase):

    def test_build(self):
        corpus = self._get_test_corpus()
        with self.assertRaises(AssertionError):
            fs = FourSquareAxes(corpus, 'hamlet', ['jay-z/r. kelly'], ['swift'], ['dylan'])
        with self.assertRaises(AssertionError):
            fs = FourSquareAxes(corpus, ['hamlet'], 'jay-z/r. kelly', ['swift'], ['dylan'])
        with self.assertRaises(AssertionError):
            fs = FourSquareAxes(corpus, ['hamlet'], ['jay-z/r. kelly'], 'swift', ['dylan'])
        with self.assertRaises(AssertionError):
            fs = FourSquareAxes(corpus, ['hamlet'], ['jay-z/r. kelly'], ['swift'], 'dylan')
        fs = FourSquareAxes(corpus, ['hamlet'], ['jay-z/r. kelly'], ['swift'], ['dylan'])
        self.assertEqual(fs.get_labels(), {'a_and_b_label': 'swift', 'a_and_not_b_label': 'hamlet', 'a_label': '', 'b_and_not_a_label': 'jay-z/r. kelly', 'b_label': '', 'not_a_and_not_b_label': 'dylan', 'not_a_label': '', 'not_b_label': ''})
        fs = FourSquareAxes(corpus, ['hamlet'], ['jay-z/r. kelly'], ['swift'], ['dylan'], labels={'a': 'swiftham', 'b': 'swiftj'})
        self.assertEqual(fs.get_labels(), {'a_and_b_label': 'swift', 'a_and_not_b_label': 'hamlet', 'a_label': 'swiftham', 'b_and_not_a_label': 'jay-z/r. kelly', 'b_label': 'swiftj', 'not_a_and_not_b_label': 'dylan', 'not_a_label': '', 'not_b_label': ''})
        axes = fs.get_axes()
        self.assertEqual(len(axes), len(corpus.get_terms()))
        self.assertEqual(set(axes.columns), {'x', 'y', 'counts'})
        fs.lexicons

    def _get_test_corpus(self):
        cats, docs = get_docs_categories_four()
        df = pd.DataFrame({'category': cats, 'text': docs})
        corpus = CorpusFromPandas(df, 'category', 'text', nlp=whitespace_nlp).build()
        return corpus

    def _get_test_semiotic_square(self):
        corpus = self._get_test_corpus()
        semsq = FourSquareAxes(corpus, ['hamlet'], ['jay-z/r. kelly'], ['swift'], ['dylan'])
        return semsq

def test_build(self):
    corpus = self._get_test_corpus()
    with self.assertRaises(AssertionError):
        fs = FourSquareAxes(corpus, 'hamlet', ['jay-z/r. kelly'], ['swift'], ['dylan'])
    with self.assertRaises(AssertionError):
        fs = FourSquareAxes(corpus, ['hamlet'], 'jay-z/r. kelly', ['swift'], ['dylan'])
    with self.assertRaises(AssertionError):
        fs = FourSquareAxes(corpus, ['hamlet'], ['jay-z/r. kelly'], 'swift', ['dylan'])
    with self.assertRaises(AssertionError):
        fs = FourSquareAxes(corpus, ['hamlet'], ['jay-z/r. kelly'], ['swift'], 'dylan')
    fs = FourSquareAxes(corpus, ['hamlet'], ['jay-z/r. kelly'], ['swift'], ['dylan'])
    self.assertEqual(fs.get_labels(), {'a_and_b_label': 'swift', 'a_and_not_b_label': 'hamlet', 'a_label': '', 'b_and_not_a_label': 'jay-z/r. kelly', 'b_label': '', 'not_a_and_not_b_label': 'dylan', 'not_a_label': '', 'not_b_label': ''})
    fs = FourSquareAxes(corpus, ['hamlet'], ['jay-z/r. kelly'], ['swift'], ['dylan'], labels={'a': 'swiftham', 'b': 'swiftj'})
    self.assertEqual(fs.get_labels(), {'a_and_b_label': 'swift', 'a_and_not_b_label': 'hamlet', 'a_label': 'swiftham', 'b_and_not_a_label': 'jay-z/r. kelly', 'b_label': 'swiftj', 'not_a_and_not_b_label': 'dylan', 'not_a_label': '', 'not_b_label': ''})
    axes = fs.get_axes()
    self.assertEqual(len(axes), len(corpus.get_terms()))
    self.assertEqual(set(axes.columns), {'x', 'y', 'counts'})
    fs.lexicons

def _get_test_semiotic_square(self):
    corpus = self._get_test_corpus()
    semsq = FourSquareAxes(corpus, ['hamlet'], ['jay-z/r. kelly'], ['swift'], ['dylan'])
    return semsq

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

def test_empath_not_presesnt(self):
    sys.modules['empath'] = None
    if sys.version_info.major == 3:
        with self.assertRaisesRegex(Exception, 'Please install the empath library to use FeatsFromSpacyDocAndEmpath.'):
            FeatsFromSpacyDocAndEmpath()
    else:
        with self.assertRaises(Exception):
            FeatsFromSpacyDocAndEmpath()

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

def test_empath_not_presesnt(self):
    sys.modules['empath'] = None
    if sys.version_info.major == 3:
        with self.assertRaisesRegex(Exception, 'Please install the empath library to use FeatsFromSpacyDocAndEmpath.'):
            FeatsFromSpacyDocAndEmpath()
    else:
        with self.assertRaises(Exception):
            FeatsFromSpacyDocAndEmpath()

class TestFeatsFromScoredLexicon(TestCase):

    def test_main(self):
        lexicon_df = pd.DataFrame({'activation': {'a': 1.3846, 'abandon': 2.375, 'abandoned': 2.1, 'abandonment': 2.0, 'abated': 1.3333}, 'imagery': {'a': 1.0, 'abandon': 2.4, 'abandoned': 3.0, 'abandonment': 1.4, 'abated': 1.2}, 'pleasantness': {'a': 2.0, 'abandon': 1.0, 'abandoned': 1.1429, 'abandonment': 1.0, 'abated': 1.6667}})
        with self.assertRaises(AssertionError):
            FeatsFromScoredLexicon(3)
        feats_from_scored_lexicon = FeatsFromScoredLexicon(lexicon_df)
        self.assertEqual(set(feats_from_scored_lexicon.get_top_model_term_lists().keys()), set(['activation', 'imagery', 'pleasantness']))
        features = feats_from_scored_lexicon.get_doc_metadata(whitespace_nlp_with_sentences('I abandoned a wallet.'))
        np.testing.assert_almost_equal(features[['activation', 'imagery', 'pleasantness']], np.array([1.7423, 2.0, 1.57145]))

def test_main(self):
    lexicon_df = pd.DataFrame({'activation': {'a': 1.3846, 'abandon': 2.375, 'abandoned': 2.1, 'abandonment': 2.0, 'abated': 1.3333}, 'imagery': {'a': 1.0, 'abandon': 2.4, 'abandoned': 3.0, 'abandonment': 1.4, 'abated': 1.2}, 'pleasantness': {'a': 2.0, 'abandon': 1.0, 'abandoned': 1.1429, 'abandonment': 1.0, 'abated': 1.6667}})
    with self.assertRaises(AssertionError):
        FeatsFromScoredLexicon(3)
    feats_from_scored_lexicon = FeatsFromScoredLexicon(lexicon_df)
    self.assertEqual(set(feats_from_scored_lexicon.get_top_model_term_lists().keys()), set(['activation', 'imagery', 'pleasantness']))
    features = feats_from_scored_lexicon.get_doc_metadata(whitespace_nlp_with_sentences('I abandoned a wallet.'))
    np.testing.assert_almost_equal(features[['activation', 'imagery', 'pleasantness']], np.array([1.7423, 2.0, 1.57145]))

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

def make_adapter(self):
    words_dict = {'info': {'not_category_name': 'Republican', 'category_name': 'Democratic'}, 'data': [{'y': 0.33763837638376387, 'term': 'crises', 'ncat25k': 0, 'cat25k': 1, 'x': 0.0, 's': 0.878755930416447}, {'y': 0.5, 'term': 'something else', 'ncat25k': 0, 'cat25k': 1, 'x': 0.0, 's': 0.5}]}
    visualization_data = VizDataAdapter(words_dict)
    return visualization_data

class TestScatterChart(TestCase):

    def test_to_json(self):
        tdm = build_hamlet_jz_term_doc_mat()
        j = ScatterChart(term_doc_matrix=tdm, minimum_term_frequency=0).to_dict('hamlet')
        self.assertEqual(set(j.keys()), set(['info', 'data']))
        self.assertEqual(set(j['info'].keys()), set(['not_category_name', 'category_name', 'category_terms', 'not_category_terms', 'category_internal_name', 'not_category_internal_names', 'neutral_category_internal_names', 'extra_category_internal_names', 'categories']))
        expected = {'x': 0.0, 'y': 0.42, 'ox': 0, 'oy': 0.42, 'term': 'art', 'cat25k': 758, 'ncat25k': 0, 'neut25k': 0, 'neut': 0, 'extra25k': 0, 'extra': 0, 's': 0.5, 'os': 3, 'bg': 3}
        datum = self._get_data_example(j)
        for var in ['cat25k', 'ncat25k']:
            np.testing.assert_almost_equal(expected[var], datum[var], decimal=1)
        self.assertEqual(set(expected.keys()), set(datum.keys()))
        self.assertEqual(expected['term'], datum['term'])

    def test_to_dict_without_categories(self):
        tdm = get_term_doc_matrix_without_categories()
        scatter_chart = ScatterChart(term_doc_matrix=tdm, minimum_term_frequency=0)
        with self.assertRaises(NeedToInjectCoordinatesException):
            scatter_chart.to_dict_without_categories()
        x_coords = tdm.get_term_doc_mat().sum(axis=0).A1
        y_coords = tdm.get_term_doc_mat().astype(bool).astype(int).sum(axis=0).A1
        scatter_chart.inject_coordinates(original_x=x_coords, original_y=y_coords, x_coords=scale(x_coords), y_coords=scale(y_coords))
        j = scatter_chart.to_dict_without_categories()
        self.assertIsInstance(j, dict)
        self.assertEqual(set(j.keys()), set(['data']))
        self.assertEqual(len(j['data']), tdm.get_num_terms())
        self.assertEqual(j['data'][-1], {'cat': 4, 'cat25k': 735, 'ox': 4, 'oy': 3, 'term': 'speak', 'x': 1.0, 'y': 1.0})

    def test_resuse_is_disabled(self):
        corpus = get_test_corpus()
        sc = ScatterChart(term_doc_matrix=corpus, minimum_term_frequency=0)
        sc.to_dict('hamlet')
        with self.assertRaises(Exception):
            sc.to_dict('hamlet')

    def test_score_transform(self):
        corpus = get_test_corpus()
        sc = ScatterChart(term_doc_matrix=corpus, minimum_term_frequency=0)
        d1 = sc.to_dict('hamlet')
        sc = ScatterChart(term_doc_matrix=corpus, minimum_term_frequency=0, score_transform=lambda x: x)
        d2 = sc.to_dict('hamlet')
        assert sum([datum['s'] for datum in d1['data']]) != sum([datum['s'] for datum in d2['data']])

    def test_multi_categories(self):
        corpus = get_test_corpus()
        j_vs_all = ScatterChart(term_doc_matrix=corpus, minimum_term_frequency=0).to_dict('hamlet')
        j_vs_swift = ScatterChart(term_doc_matrix=corpus, minimum_term_frequency=0).to_dict('hamlet', not_categories=['swift'])
        self.assertNotEqual(set(j_vs_all['info']['not_category_internal_names']), set(j_vs_swift['info']['not_category_internal_names']))
        self.assertEqual(j_vs_all['info']['categories'], corpus.get_categories())
        self.assertEqual(j_vs_swift['info']['categories'], corpus.get_categories())

    def test_title_case_names(self):
        tdm = build_hamlet_jz_term_doc_mat()
        j = ScatterChart(term_doc_matrix=tdm, minimum_term_frequency=0).to_dict('hamlet', 'HAMLET', 'NOT HAMLET')
        self.assertEqual(j['info']['category_name'], 'HAMLET')
        self.assertEqual(j['info']['not_category_name'], 'NOT HAMLET')
        tdm = build_hamlet_jz_term_doc_mat()
        j = ScatterChart(term_doc_matrix=tdm, minimum_term_frequency=0).to_dict('hamlet', 'HAMLET', 'NOT HAMLET', title_case_names=True)
        self.assertEqual(j['info']['category_name'], 'Hamlet')
        self.assertEqual(j['info']['not_category_name'], 'Not Hamlet')

    def _get_data_example(self, j):
        return [t for t in j['data'] if t['term'] == 'art'][0]

    def test_terms_to_include(self):
        tdm = build_hamlet_jz_term_doc_mat()
        terms_to_include = list(sorted(['both worlds', 'thou', 'the', 'of', 'st', 'returned', 'best']))
        j = ScatterChart(term_doc_matrix=tdm, minimum_term_frequency=0, terms_to_include=terms_to_include).to_dict('hamlet', 'HAMLET', 'NOT HAMLET')
        self.assertEqual(list(sorted((t['term'] for t in j['data']))), terms_to_include)

    def test_p_vals(self):
        tdm = build_hamlet_jz_term_doc_mat()
        j = ScatterChart(term_doc_matrix=tdm, minimum_term_frequency=0, term_significance=LogOddsRatioUninformativeDirichletPrior()).to_dict('hamlet')
        datum = self._get_data_example(j)
        self.assertIn('p', datum.keys())

    def test_inject_coordinates(self):
        tdm = build_hamlet_jz_term_doc_mat()
        freq_df = tdm.get_term_freq_df()
        scatter_chart = ScatterChart(term_doc_matrix=tdm, minimum_term_frequency=0)
        with self.assertRaises(CoordinatesNotRightException):
            scatter_chart.inject_coordinates([], [])
        with self.assertRaises(CoordinatesNotRightException):
            scatter_chart.inject_coordinates(freq_df[freq_df.columns[0]], [])
        with self.assertRaises(CoordinatesNotRightException):
            scatter_chart.inject_coordinates([], freq_df[freq_df.columns[0]])
        x = freq_df[freq_df.columns[1]].astype(np.float64)
        y = freq_df[freq_df.columns[0]].astype(np.float64)
        with self.assertRaises(CoordinatesNotRightException):
            scatter_chart.inject_coordinates(x, y)
        with self.assertRaises(CoordinatesNotRightException):
            scatter_chart.inject_coordinates(x, y / y.max())
        with self.assertRaises(CoordinatesNotRightException):
            scatter_chart.inject_coordinates(x / x.max(), y)
        with self.assertRaises(CoordinatesNotRightException):
            scatter_chart.inject_coordinates(-x / x.max(), -y / y.max())
        with self.assertRaises(CoordinatesNotRightException):
            scatter_chart.inject_coordinates(-x / x.max(), y / y.max())
        with self.assertRaises(CoordinatesNotRightException):
            scatter_chart.inject_coordinates(x / x.max(), -y / y.max())
        scatter_chart.inject_coordinates(x / x.max(), y / y.max())

    def test_inject_metadata_term_lists(self):
        tdm = build_hamlet_jz_term_doc_mat()
        scatter_chart = ScatterChart(term_doc_matrix=tdm, minimum_term_frequency=0)
        with self.assertRaises(TermDocMatrixHasNoMetadataException):
            scatter_chart.inject_metadata_term_lists({'blah': ['a', 'adsf', 'asfd']})
        scatter_chart = ScatterChart(term_doc_matrix=build_hamlet_jz_corpus_with_meta(), minimum_term_frequency=0, use_non_text_features=True)
        with self.assertRaises(TypeError):
            scatter_chart.inject_metadata_term_lists({'blash': [3, 1]})
        with self.assertRaises(TypeError):
            scatter_chart.inject_metadata_term_lists({3: ['a', 'b']})
        with self.assertRaises(TypeError):
            scatter_chart.inject_metadata_term_lists({'a': {'a', 'b'}})
        with self.assertRaises(TypeError):
            scatter_chart.inject_metadata_term_lists(3)
        self.assertEqual(type(scatter_chart.inject_metadata_term_lists({'a': ['a', 'b']})), ScatterChart)
        j = scatter_chart.to_dict('hamlet')
        self.assertEqual(set(j.keys()), set(['info', 'data', 'metalists']))
        self.assertEqual(set(j['info'].keys()), set(['not_category_name', 'category_name', 'category_terms', 'not_category_terms', 'category_internal_name', 'not_category_internal_names', 'extra_category_internal_names', 'neutral_category_internal_names', 'categories']))

    def test_inject_metadata_descriptions(self):
        tdm = build_hamlet_jz_corpus_with_meta()
        scatter_chart = ScatterChart(term_doc_matrix=tdm, minimum_term_frequency=0)
        with self.assertRaises(AssertionError):
            scatter_chart.inject_metadata_descriptions(3323)
        if sys.version_info > (3, 0):
            "\n            with self.assertRaisesRegex(Exception, 'The following meta data terms are not present: blah'):\n                scatter_chart.inject_metadata_descriptions({'blah': 'asjdkflasdjklfsadjk jsdkafsd'})\n            with self.assertRaisesRegex(Exception, 'The following meta data terms are not present: cat2'):\n                scatter_chart.inject_metadata_descriptions({'cat1': 'asjdkflasdjklfsadjk jsdkafsd', 'cat2': 'asdf'})\n            "
        assert scatter_chart == scatter_chart.inject_metadata_descriptions({'cat1': 'asjdkflasdjklfsadjk jsdkafsd'})
        j = scatter_chart.to_dict('hamlet')
        self.assertEqual(set(j.keys()), set(['info', 'data', 'metadescriptions']))

    def test_inject_term_colors(self):
        tdm = build_hamlet_jz_corpus_with_meta()
        freq_df = tdm.get_term_freq_df()
        scatter_chart = ScatterChart(term_doc_matrix=tdm, minimum_term_frequency=0)
        scatter_chart.inject_term_colors({'t1': '00ffee'})
        j = scatter_chart.to_dict('hamlet')
        self.assertIn('term_colors', j['info'])

    def test_inject_coordinates_original(self):
        tdm = build_hamlet_jz_term_doc_mat()
        freq_df = tdm.get_term_freq_df()
        scatter_chart = ScatterChart(term_doc_matrix=tdm, minimum_term_frequency=0)
        x = freq_df[freq_df.columns[1]].astype(np.float64)
        y = freq_df[freq_df.columns[0]].astype(np.float64)
        scatter_chart.inject_coordinates(x / x.max(), y / y.max(), original_x=x, original_y=y)
        j = scatter_chart.to_dict('hamlet')
        self.assertEqual(j['data'][0].keys(), {'x', 'os', 'y', 'ncat25k', 'neut', 'cat25k', 'ox', 'neut25k', 'extra25k', 'extra', 'oy', 'term', 's', 'bg'})
        and_term = [t for t in j['data'] if t['term'] == 'and'][0]
        self.assertEqual(and_term['ox'], 0)
        self.assertEqual(and_term['oy'], 1)

    def test_to_json_use_non_text_features(self):
        tdm = build_hamlet_jz_corpus_with_meta()
        j = ScatterChart(term_doc_matrix=tdm, minimum_term_frequency=0, use_non_text_features=True).to_dict('hamlet')
        self.assertEqual(set(j.keys()), set(['info', 'data']))
        self.assertEqual(set(j['info'].keys()), set(['not_category_name', 'category_name', 'category_terms', 'not_category_terms', 'category_internal_name', 'not_category_internal_names', 'extra_category_internal_names', 'neutral_category_internal_names', 'categories']))
        self.assertEqual({t['term'] for t in j['data']}, {'cat1'})

    def test_max_terms(self):
        tdm = build_hamlet_jz_term_doc_mat()
        j = ScatterChart(term_doc_matrix=tdm, minimum_term_frequency=0, max_terms=2).to_dict('hamlet')
        self.assertEqual(2, len(j['data']))
        j = ScatterChart(term_doc_matrix=tdm, minimum_term_frequency=0, max_terms=10).to_dict('hamlet')
        self.assertEqual(10, len(j['data']))
        j = ScatterChart(term_doc_matrix=tdm, minimum_term_frequency=0, pmi_threshold_coefficient=0, max_terms=10000).to_dict('hamlet')
        self.assertEqual(len(tdm.get_term_freq_df()), len(j['data']))
        j = ScatterChart(term_doc_matrix=tdm, minimum_term_frequency=0, pmi_threshold_coefficient=0, max_terms=None).to_dict('hamlet')
        self.assertEqual(len(tdm.get_term_freq_df()), len(j['data']))

def test_to_json(self):
    tdm = build_hamlet_jz_term_doc_mat()
    j = ScatterChart(term_doc_matrix=tdm, minimum_term_frequency=0).to_dict('hamlet')
    self.assertEqual(set(j.keys()), set(['info', 'data']))
    self.assertEqual(set(j['info'].keys()), set(['not_category_name', 'category_name', 'category_terms', 'not_category_terms', 'category_internal_name', 'not_category_internal_names', 'neutral_category_internal_names', 'extra_category_internal_names', 'categories']))
    expected = {'x': 0.0, 'y': 0.42, 'ox': 0, 'oy': 0.42, 'term': 'art', 'cat25k': 758, 'ncat25k': 0, 'neut25k': 0, 'neut': 0, 'extra25k': 0, 'extra': 0, 's': 0.5, 'os': 3, 'bg': 3}
    datum = self._get_data_example(j)
    for var in ['cat25k', 'ncat25k']:
        np.testing.assert_almost_equal(expected[var], datum[var], decimal=1)
    self.assertEqual(set(expected.keys()), set(datum.keys()))
    self.assertEqual(expected['term'], datum['term'])

def test_to_dict_without_categories(self):
    tdm = get_term_doc_matrix_without_categories()
    scatter_chart = ScatterChart(term_doc_matrix=tdm, minimum_term_frequency=0)
    with self.assertRaises(NeedToInjectCoordinatesException):
        scatter_chart.to_dict_without_categories()
    x_coords = tdm.get_term_doc_mat().sum(axis=0).A1
    y_coords = tdm.get_term_doc_mat().astype(bool).astype(int).sum(axis=0).A1
    scatter_chart.inject_coordinates(original_x=x_coords, original_y=y_coords, x_coords=scale(x_coords), y_coords=scale(y_coords))
    j = scatter_chart.to_dict_without_categories()
    self.assertIsInstance(j, dict)
    self.assertEqual(set(j.keys()), set(['data']))
    self.assertEqual(len(j['data']), tdm.get_num_terms())
    self.assertEqual(j['data'][-1], {'cat': 4, 'cat25k': 735, 'ox': 4, 'oy': 3, 'term': 'speak', 'x': 1.0, 'y': 1.0})

def test_resuse_is_disabled(self):
    corpus = get_test_corpus()
    sc = ScatterChart(term_doc_matrix=corpus, minimum_term_frequency=0)
    sc.to_dict('hamlet')
    with self.assertRaises(Exception):
        sc.to_dict('hamlet')

def test_score_transform(self):
    corpus = get_test_corpus()
    sc = ScatterChart(term_doc_matrix=corpus, minimum_term_frequency=0)
    d1 = sc.to_dict('hamlet')
    sc = ScatterChart(term_doc_matrix=corpus, minimum_term_frequency=0, score_transform=lambda x: x)
    d2 = sc.to_dict('hamlet')
    assert sum([datum['s'] for datum in d1['data']]) != sum([datum['s'] for datum in d2['data']])

def test_multi_categories(self):
    corpus = get_test_corpus()
    j_vs_all = ScatterChart(term_doc_matrix=corpus, minimum_term_frequency=0).to_dict('hamlet')
    j_vs_swift = ScatterChart(term_doc_matrix=corpus, minimum_term_frequency=0).to_dict('hamlet', not_categories=['swift'])
    self.assertNotEqual(set(j_vs_all['info']['not_category_internal_names']), set(j_vs_swift['info']['not_category_internal_names']))
    self.assertEqual(j_vs_all['info']['categories'], corpus.get_categories())
    self.assertEqual(j_vs_swift['info']['categories'], corpus.get_categories())

def test_title_case_names(self):
    tdm = build_hamlet_jz_term_doc_mat()
    j = ScatterChart(term_doc_matrix=tdm, minimum_term_frequency=0).to_dict('hamlet', 'HAMLET', 'NOT HAMLET')
    self.assertEqual(j['info']['category_name'], 'HAMLET')
    self.assertEqual(j['info']['not_category_name'], 'NOT HAMLET')
    tdm = build_hamlet_jz_term_doc_mat()
    j = ScatterChart(term_doc_matrix=tdm, minimum_term_frequency=0).to_dict('hamlet', 'HAMLET', 'NOT HAMLET', title_case_names=True)
    self.assertEqual(j['info']['category_name'], 'Hamlet')
    self.assertEqual(j['info']['not_category_name'], 'Not Hamlet')

def test_terms_to_include(self):
    tdm = build_hamlet_jz_term_doc_mat()
    terms_to_include = list(sorted(['both worlds', 'thou', 'the', 'of', 'st', 'returned', 'best']))
    j = ScatterChart(term_doc_matrix=tdm, minimum_term_frequency=0, terms_to_include=terms_to_include).to_dict('hamlet', 'HAMLET', 'NOT HAMLET')
    self.assertEqual(list(sorted((t['term'] for t in j['data']))), terms_to_include)

def test_p_vals(self):
    tdm = build_hamlet_jz_term_doc_mat()
    j = ScatterChart(term_doc_matrix=tdm, minimum_term_frequency=0, term_significance=LogOddsRatioUninformativeDirichletPrior()).to_dict('hamlet')
    datum = self._get_data_example(j)
    self.assertIn('p', datum.keys())

def test_inject_coordinates(self):
    tdm = build_hamlet_jz_term_doc_mat()
    freq_df = tdm.get_term_freq_df()
    scatter_chart = ScatterChart(term_doc_matrix=tdm, minimum_term_frequency=0)
    with self.assertRaises(CoordinatesNotRightException):
        scatter_chart.inject_coordinates([], [])
    with self.assertRaises(CoordinatesNotRightException):
        scatter_chart.inject_coordinates(freq_df[freq_df.columns[0]], [])
    with self.assertRaises(CoordinatesNotRightException):
        scatter_chart.inject_coordinates([], freq_df[freq_df.columns[0]])
    x = freq_df[freq_df.columns[1]].astype(np.float64)
    y = freq_df[freq_df.columns[0]].astype(np.float64)
    with self.assertRaises(CoordinatesNotRightException):
        scatter_chart.inject_coordinates(x, y)
    with self.assertRaises(CoordinatesNotRightException):
        scatter_chart.inject_coordinates(x, y / y.max())
    with self.assertRaises(CoordinatesNotRightException):
        scatter_chart.inject_coordinates(x / x.max(), y)
    with self.assertRaises(CoordinatesNotRightException):
        scatter_chart.inject_coordinates(-x / x.max(), -y / y.max())
    with self.assertRaises(CoordinatesNotRightException):
        scatter_chart.inject_coordinates(-x / x.max(), y / y.max())
    with self.assertRaises(CoordinatesNotRightException):
        scatter_chart.inject_coordinates(x / x.max(), -y / y.max())
    scatter_chart.inject_coordinates(x / x.max(), y / y.max())

def test_inject_metadata_term_lists(self):
    tdm = build_hamlet_jz_term_doc_mat()
    scatter_chart = ScatterChart(term_doc_matrix=tdm, minimum_term_frequency=0)
    with self.assertRaises(TermDocMatrixHasNoMetadataException):
        scatter_chart.inject_metadata_term_lists({'blah': ['a', 'adsf', 'asfd']})
    scatter_chart = ScatterChart(term_doc_matrix=build_hamlet_jz_corpus_with_meta(), minimum_term_frequency=0, use_non_text_features=True)
    with self.assertRaises(TypeError):
        scatter_chart.inject_metadata_term_lists({'blash': [3, 1]})
    with self.assertRaises(TypeError):
        scatter_chart.inject_metadata_term_lists({3: ['a', 'b']})
    with self.assertRaises(TypeError):
        scatter_chart.inject_metadata_term_lists({'a': {'a', 'b'}})
    with self.assertRaises(TypeError):
        scatter_chart.inject_metadata_term_lists(3)
    self.assertEqual(type(scatter_chart.inject_metadata_term_lists({'a': ['a', 'b']})), ScatterChart)
    j = scatter_chart.to_dict('hamlet')
    self.assertEqual(set(j.keys()), set(['info', 'data', 'metalists']))
    self.assertEqual(set(j['info'].keys()), set(['not_category_name', 'category_name', 'category_terms', 'not_category_terms', 'category_internal_name', 'not_category_internal_names', 'extra_category_internal_names', 'neutral_category_internal_names', 'categories']))

def test_inject_metadata_descriptions(self):
    tdm = build_hamlet_jz_corpus_with_meta()
    scatter_chart = ScatterChart(term_doc_matrix=tdm, minimum_term_frequency=0)
    with self.assertRaises(AssertionError):
        scatter_chart.inject_metadata_descriptions(3323)
    if sys.version_info > (3, 0):
        "\n            with self.assertRaisesRegex(Exception, 'The following meta data terms are not present: blah'):\n                scatter_chart.inject_metadata_descriptions({'blah': 'asjdkflasdjklfsadjk jsdkafsd'})\n            with self.assertRaisesRegex(Exception, 'The following meta data terms are not present: cat2'):\n                scatter_chart.inject_metadata_descriptions({'cat1': 'asjdkflasdjklfsadjk jsdkafsd', 'cat2': 'asdf'})\n            "
    assert scatter_chart == scatter_chart.inject_metadata_descriptions({'cat1': 'asjdkflasdjklfsadjk jsdkafsd'})
    j = scatter_chart.to_dict('hamlet')
    self.assertEqual(set(j.keys()), set(['info', 'data', 'metadescriptions']))

def test_inject_term_colors(self):
    tdm = build_hamlet_jz_corpus_with_meta()
    freq_df = tdm.get_term_freq_df()
    scatter_chart = ScatterChart(term_doc_matrix=tdm, minimum_term_frequency=0)
    scatter_chart.inject_term_colors({'t1': '00ffee'})
    j = scatter_chart.to_dict('hamlet')
    self.assertIn('term_colors', j['info'])

def test_inject_coordinates_original(self):
    tdm = build_hamlet_jz_term_doc_mat()
    freq_df = tdm.get_term_freq_df()
    scatter_chart = ScatterChart(term_doc_matrix=tdm, minimum_term_frequency=0)
    x = freq_df[freq_df.columns[1]].astype(np.float64)
    y = freq_df[freq_df.columns[0]].astype(np.float64)
    scatter_chart.inject_coordinates(x / x.max(), y / y.max(), original_x=x, original_y=y)
    j = scatter_chart.to_dict('hamlet')
    self.assertEqual(j['data'][0].keys(), {'x', 'os', 'y', 'ncat25k', 'neut', 'cat25k', 'ox', 'neut25k', 'extra25k', 'extra', 'oy', 'term', 's', 'bg'})
    and_term = [t for t in j['data'] if t['term'] == 'and'][0]
    self.assertEqual(and_term['ox'], 0)
    self.assertEqual(and_term['oy'], 1)

def test_to_json_use_non_text_features(self):
    tdm = build_hamlet_jz_corpus_with_meta()
    j = ScatterChart(term_doc_matrix=tdm, minimum_term_frequency=0, use_non_text_features=True).to_dict('hamlet')
    self.assertEqual(set(j.keys()), set(['info', 'data']))
    self.assertEqual(set(j['info'].keys()), set(['not_category_name', 'category_name', 'category_terms', 'not_category_terms', 'category_internal_name', 'not_category_internal_names', 'extra_category_internal_names', 'neutral_category_internal_names', 'categories']))
    self.assertEqual({t['term'] for t in j['data']}, {'cat1'})

def test_max_terms(self):
    tdm = build_hamlet_jz_term_doc_mat()
    j = ScatterChart(term_doc_matrix=tdm, minimum_term_frequency=0, max_terms=2).to_dict('hamlet')
    self.assertEqual(2, len(j['data']))
    j = ScatterChart(term_doc_matrix=tdm, minimum_term_frequency=0, max_terms=10).to_dict('hamlet')
    self.assertEqual(10, len(j['data']))
    j = ScatterChart(term_doc_matrix=tdm, minimum_term_frequency=0, pmi_threshold_coefficient=0, max_terms=10000).to_dict('hamlet')
    self.assertEqual(len(tdm.get_term_freq_df()), len(j['data']))
    j = ScatterChart(term_doc_matrix=tdm, minimum_term_frequency=0, pmi_threshold_coefficient=0, max_terms=None).to_dict('hamlet')
    self.assertEqual(len(tdm.get_term_freq_df()), len(j['data']))

def empath_mock(doc, **kwargs):
    toks = list(doc)
    num_toks = min(3, len(toks))
    return {'cat' + str(len(tok)): val for val, tok in enumerate(toks[:num_toks])}

class TestBM25Difference(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.corpus = build_hamlet_jz_corpus()

    def test_get_scores(self):
        result = BM25Difference(self.corpus).set_categories('hamlet').get_scores()
        self.assertEquals(type(result), pd.Series)
        np.testing.assert_array_equal(np.array(result.index), self.corpus.get_terms())

    def test_get_name(self):
        self.assertEquals(BM25Difference(self.corpus).set_categories('hamlet').get_name(), 'BM25 difference')

@classmethod
def setUpClass(cls):
    cls.corpus = build_hamlet_jz_corpus()

class TestPriorFactory(TestCase):

    def test_all_categories(self):
        corpus = get_test_corpus()
        priors, my_corpus = PriorFactory(corpus, starting_count=0, category='hamlet').use_all_categories().build()
        tdf = corpus.get_term_freq_df()
        self.assertEqual(len(priors), len(tdf))
        np.testing.assert_equal(priors.values, corpus.get_term_freq_df().sum(axis=1).values)

    def test_neutral_categories(self):
        corpus = get_test_corpus()
        priors = PriorFactory(corpus, 'hamlet', starting_count=0.001, not_categories=['swift']).use_neutral_categories().get_priors()
        self.assertEqual(priors.min(), 0.001)
        self.assertEqual(priors.shape[0], corpus._X.shape[1])
        corpus = get_test_corpus()
        priors = PriorFactory(corpus, 'hamlet', starting_count=0.001, not_categories=['swift']).use_neutral_categories().drop_zero_priors().get_priors()
        jzcnts = corpus.get_term_freq_df()['jay-z/r. kelly freq'].where(lambda x: x > 0).dropna()
        np.testing.assert_equal(priors.values, jzcnts.values + 0.001)

    def test_get_general_term_frequencies(self):
        corpus = get_test_corpus()
        fact = PriorFactory(corpus, category='hamlet', not_categories=['swift'], starting_count=0).use_general_term_frequencies().use_all_categories()
        priors, clean_corpus = fact.build()
        expected_prior = pd.merge(corpus.get_term_doc_count_df(), corpus.get_term_and_background_counts()[['background']], left_index=True, right_index=True, how='left').fillna(0.0).sum(axis=1)
        np.testing.assert_allclose(priors.values, expected_prior.values)

    def test_align_to_target(self):
        full_corpus = get_test_corpus()
        corpus = full_corpus.remove_categories(['swift'])
        priors = PriorFactory(full_corpus).use_all_categories().get_priors()
        with self.assertRaises(ValueError):
            LogOddsRatioInformativeDirichletPrior(priors).get_scores(*corpus.get_term_freq_df().values.T)
        priors = PriorFactory(full_corpus).use_all_categories().align_to_target(corpus).get_priors()
        LogOddsRatioInformativeDirichletPrior(priors).get_scores(*corpus.get_term_freq_df().values.T)

    def test_use_categories(self):
        full_corpus = get_test_corpus()
        priors = PriorFactory(full_corpus).use_categories(['swift']).get_priors()
        corpus = full_corpus.remove_categories(['swift'])
        with self.assertRaises(ValueError):
            LogOddsRatioInformativeDirichletPrior(priors).get_scores(*corpus.get_term_freq_df().values.T)
        priors = PriorFactory(full_corpus).use_all_categories().align_to_target(corpus).get_priors()
        LogOddsRatioInformativeDirichletPrior(priors).get_scores(*corpus.get_term_freq_df().values.T)

    def test_get_custom_term_frequencies(self):
        corpus = get_test_corpus()
        fact = PriorFactory(corpus, starting_count=0.04).use_custom_term_frequencies(pd.Series({'halt': 3, 'i': 8})).drop_zero_priors()
        priors, clean_corpus = fact.build()
        self.assertEqual(set(clean_corpus.get_terms()), {'i', 'halt'})
        np.testing.assert_equal(priors.sort_values().values, [3.04, 8.04])

def test_all_categories(self):
    corpus = get_test_corpus()
    priors, my_corpus = PriorFactory(corpus, starting_count=0, category='hamlet').use_all_categories().build()
    tdf = corpus.get_term_freq_df()
    self.assertEqual(len(priors), len(tdf))
    np.testing.assert_equal(priors.values, corpus.get_term_freq_df().sum(axis=1).values)

def test_neutral_categories(self):
    corpus = get_test_corpus()
    priors = PriorFactory(corpus, 'hamlet', starting_count=0.001, not_categories=['swift']).use_neutral_categories().get_priors()
    self.assertEqual(priors.min(), 0.001)
    self.assertEqual(priors.shape[0], corpus._X.shape[1])
    corpus = get_test_corpus()
    priors = PriorFactory(corpus, 'hamlet', starting_count=0.001, not_categories=['swift']).use_neutral_categories().drop_zero_priors().get_priors()
    jzcnts = corpus.get_term_freq_df()['jay-z/r. kelly freq'].where(lambda x: x > 0).dropna()
    np.testing.assert_equal(priors.values, jzcnts.values + 0.001)

def test_get_general_term_frequencies(self):
    corpus = get_test_corpus()
    fact = PriorFactory(corpus, category='hamlet', not_categories=['swift'], starting_count=0).use_general_term_frequencies().use_all_categories()
    priors, clean_corpus = fact.build()
    expected_prior = pd.merge(corpus.get_term_doc_count_df(), corpus.get_term_and_background_counts()[['background']], left_index=True, right_index=True, how='left').fillna(0.0).sum(axis=1)
    np.testing.assert_allclose(priors.values, expected_prior.values)

def test_align_to_target(self):
    full_corpus = get_test_corpus()
    corpus = full_corpus.remove_categories(['swift'])
    priors = PriorFactory(full_corpus).use_all_categories().get_priors()
    with self.assertRaises(ValueError):
        LogOddsRatioInformativeDirichletPrior(priors).get_scores(*corpus.get_term_freq_df().values.T)
    priors = PriorFactory(full_corpus).use_all_categories().align_to_target(corpus).get_priors()
    LogOddsRatioInformativeDirichletPrior(priors).get_scores(*corpus.get_term_freq_df().values.T)

def test_use_categories(self):
    full_corpus = get_test_corpus()
    priors = PriorFactory(full_corpus).use_categories(['swift']).get_priors()
    corpus = full_corpus.remove_categories(['swift'])
    with self.assertRaises(ValueError):
        LogOddsRatioInformativeDirichletPrior(priors).get_scores(*corpus.get_term_freq_df().values.T)
    priors = PriorFactory(full_corpus).use_all_categories().align_to_target(corpus).get_priors()
    LogOddsRatioInformativeDirichletPrior(priors).get_scores(*corpus.get_term_freq_df().values.T)

def test_get_custom_term_frequencies(self):
    corpus = get_test_corpus()
    fact = PriorFactory(corpus, starting_count=0.04).use_custom_term_frequencies(pd.Series({'halt': 3, 'i': 8})).drop_zero_priors()
    priors, clean_corpus = fact.build()
    self.assertEqual(set(clean_corpus.get_terms()), {'i', 'halt'})
    np.testing.assert_equal(priors.sort_values().values, [3.04, 8.04])

class TestPMIFiltering(TestCase):

    def test_main(self):
        term_doc_mat = get_hamlet_term_doc_matrix()
        pmi_filter = TermDocMatrixFilter(pmi_threshold_coef=4, minimum_term_freq=3)
        filtered_term_doc_mat = pmi_filter.filter(term_doc_mat)
        self.assertLessEqual(len(filtered_term_doc_mat.get_term_freq_df()), len(term_doc_mat.get_term_freq_df()))

    def _test_nothing_passes_filter_raise_error(self):
        term_doc_mat = get_hamlet_term_doc_matrix()
        pmi_filter = TermDocMatrixFilter(pmi_threshold_coef=4000, minimum_term_freq=3000)
        with self.assertRaises(AtLeastOneCategoryHasNoTermsException):
            pmi_filter.filter(term_doc_mat)

    def test_filter_bigrams_by_pmis(self):
        term_doc_mat = get_hamlet_term_doc_matrix()
        df = term_doc_mat.get_term_freq_df()
        filtered_df = filter_bigrams_by_pmis(df, threshold_coef=3)
        self.assertLess(len(filtered_df), len(df))

    def test_unigrams_that_only_occur_in_one_bigram(self):
        bigrams = set(['the cat', 'the saw', 'horses are', 'are pigs', 'pigs horses'])
        expected = {'cat', 'saw'}
        self.assertEqual(expected, unigrams_that_only_occur_in_one_bigram(bigrams))

    def test_filter_out_unigrams_that_only_occur_in_one_bigram(self):
        bigrams = ['the cat', 'the saw', 'horses are', 'are pigs', 'pigs horses']
        df = TermDocMatrixFromPandas(data_frame=pd.DataFrame({'text': bigrams, 'category': ['a', 'a', 'a', 'b', 'b']}), category_col='category', text_col='text', nlp=whitespace_nlp).build().get_term_freq_df()
        new_df = filter_out_unigrams_that_only_occur_in_one_bigram(df)
        self.assertFalse('cat' in new_df.index)
        self.assertFalse('saw' in new_df.index)
        self.assertTrue('the' in new_df.index)
        self.assertTrue('horses' in new_df.index)
        self.assertTrue('pigs' in new_df.index)
        self.assertEqual(set(bigrams) & set(new_df.index), set(bigrams))

def test_unigrams_that_only_occur_in_one_bigram(self):
    bigrams = set(['the cat', 'the saw', 'horses are', 'are pigs', 'pigs horses'])
    expected = {'cat', 'saw'}
    self.assertEqual(expected, unigrams_that_only_occur_in_one_bigram(bigrams))

class TestScatterChartExplorer(TestCase):

    def test_to_dict(self):
        np.random.seed(0)
        random.seed(0)
        corpus = build_hamlet_jz_corpus()
        j = ScatterChartExplorer(corpus, minimum_term_frequency=0).to_dict('hamlet')
        self.assertEqual(set(j.keys()), set(['info', 'data', 'docs']))
        self.assertEqual(set(j['info'].keys()), set(['not_category_name', 'category_name', 'category_terms', 'not_category_internal_names', 'not_category_terms', 'category_internal_name', 'categories', 'neutral_category_name', 'extra_category_name', 'neutral_category_internal_names', 'extra_category_internal_names']))
        self.assertEqual(list(j['docs']['labels']), [0, 0, 0, 0, 1, 1, 1, 1])
        self.assertEqual(list(j['docs']['texts']), ["what art thou that usurp'st this time of night,", 'together with that fair and warlike form', 'in which the majesty of buried denmark', 'did sometimes march? by heaven i charge thee, speak!', 'halt! who goes there?', 'it is i sire tone from brooklyn.', 'well, speak up man what is it?', 'news from the east sire! the best of both worlds has returned!'])
        expected = {'y': 0.5, 'ncat': 0, 'ncat25k': 0, 'bg': 5, 'cat': 1, 's': 0.5, 'term': 'art', 'os': 0.5192, 'extra': 0, 'extra25k': 0, 'cat25k': 758, 'x': 0.06, 'neut': 0, 'neut25k': 0, 'ox': 5, 'oy': 3}
        actual = [t for t in j['data'] if t['term'] == 'art'][0]
        '\n\t\tfor var in expected.keys():\n\t\t\ttry:\n\t\t\t\t#np.testing.assert_almost_equal(actual[var], expected[var],decimal=1)\n\t\t\texcept TypeError:\n\t\t\t\tself.assertEqual(actual[var], expected[var])\n\t\t'
        self.assertEqual(set(expected.keys()), set(actual.keys()))
        self.assertEqual(expected['term'], actual['term'])
        self.assertEqual(j['docs'].keys(), {'texts', 'labels', 'categories'})
        j = ScatterChartExplorer(corpus, minimum_term_frequency=0).inject_term_metadata({'art': {'display': 'blah blah blah', 'color': 'red'}}).to_dict('hamlet')
        actual = [t for t in j['data'] if t['term'] == 'art'][0]
        expected = {'y': 0.5, 'ncat': 0, 'ncat25k': 0, 'bg': 5, 'cat': 1, 's': 0.5, 'term': 'art', 'os': 0.5192, 'extra': 0, 'extra25k': 0, 'cat25k': 758, 'x': 0.06, 'neut': 0, 'neut25k': 0, 'ox': 5, 'oy': 3, 'etc': {'display': 'blah blah blah', 'color': 'red'}}
        self.assertEqual(set(actual.keys()), set(expected.keys()))
        self.assertEqual(actual['etc'], expected['etc'])
        actual = [t for t in j['data'] if t['term'] != 'art'][0]
        self.assertEqual(set(actual.keys()), set(expected.keys()))
        self.assertEqual(actual['etc'], {})

    def test_hide_terms(self):
        corpus = build_hamlet_jz_corpus().get_unigram_corpus()
        terms_to_hide = ['thou', 'heaven']
        sc = ScatterChartExplorer(corpus, minimum_term_frequency=0).hide_terms(terms_to_hide)
        self.assertEquals(type(sc), ScatterChartExplorer)
        j = sc.to_dict('hamlet', include_term_category_counts=True)
        self.assertTrue(all(['display' in t and t['display'] == False for t in j['data'] if t['term'] in terms_to_hide]))
        self.assertTrue(all(['display' not in t for t in j['data'] if t['term'] not in terms_to_hide]))

    def test_include_term_category_counts(self):
        corpus = build_hamlet_jz_corpus().get_unigram_corpus()
        j = ScatterChartExplorer(corpus, minimum_term_frequency=0).to_dict('hamlet', include_term_category_counts=True)
        self.assertEqual(set(j.keys()), set(['info', 'data', 'docs', 'termCounts']))
        self.assertEqual(len(j['termCounts']), corpus.get_num_categories())
        term_idx_set = set()
        for cat_counts in j['termCounts']:
            term_idx_set |= set(cat_counts.keys())
            self.assertTrue(all([freq >= docs for freq, docs in cat_counts.values()]))
        self.assertEqual(len(term_idx_set), corpus.get_num_terms())

    def test_multi_categories(self):
        corpus = get_test_corpus()
        j_vs_all = ScatterChartExplorer(corpus=corpus, minimum_term_frequency=0).to_dict('hamlet')
        j_vs_swift = ScatterChartExplorer(corpus=corpus, minimum_term_frequency=0).to_dict('hamlet', not_categories=['swift'])
        self.assertNotEqual(set(j_vs_all['info']['not_category_internal_names']), set(j_vs_swift['info']['not_category_internal_names']))
        self.assertEqual(list(j_vs_all['docs']['labels']), list(j_vs_swift['docs']['labels']))
        self.assertEqual(list(j_vs_all['docs']['categories']), list(j_vs_swift['docs']['categories']))

    def test_metadata(self):
        corpus = build_hamlet_jz_corpus()
        meta = ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight']
        j = ScatterChartExplorer(corpus, minimum_term_frequency=0).to_dict('hamlet', metadata=meta)
        self.maxDiff = None
        j['docs']['labels'] = list(j['docs']['labels'])
        self.assertEqual(j['docs'], {'labels': [0, 0, 0, 0, 1, 1, 1, 1], 'categories': ['hamlet', 'jay-z/r. kelly'], 'meta': ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight'], 'texts': ["what art thou that usurp'st this time of night,", 'together with that fair and warlike form', 'in which the majesty of buried denmark', 'did sometimes march? by heaven i charge thee, speak!', 'halt! who goes there?', 'it is i sire tone from brooklyn.', 'well, speak up man what is it?', 'news from the east sire! the best of both worlds has returned!']})

    def test_alternative_text(self):
        corpus = build_hamlet_jz_corpus_with_alt_text()
        j = ScatterChartExplorer(corpus, minimum_term_frequency=0).to_dict('hamlet', alternative_text_field='alt')
        self.assertEqual(j['docs']['texts'][0], j['docs']['texts'][0].upper())
        j = ScatterChartExplorer(corpus, minimum_term_frequency=0).to_dict('hamlet')
        self.assertNotEqual(j['docs']['texts'][0], j['docs']['texts'][0].upper())

    def test_extra_features(self):
        corpus = build_hamlet_jz_corpus_with_meta()
        meta = ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight']
        j = ScatterChartExplorer(corpus, minimum_term_frequency=0, use_non_text_features=True).to_dict('hamlet', metadata=meta)
        extras = [{'cat3': 1, 'cat4': 2}, {'cat4': 2}, {'cat3': 2, 'cat5': 1}, {'cat6': 2, 'cat9': 1}, {'cat3': 1, 'cat4': 2}, {'cat1': 2, 'cat2': 1}, {'cat2': 2, 'cat5': 1}, {'cat3': 2, 'cat4': 1}]
        extras = [{'cat1': 2}] * 8
        self.maxDiff = None
        j['docs']['labels'] = list(j['docs']['labels'])
        self.assertEqual(j['docs'], {'labels': [0, 0, 0, 0, 1, 1, 1, 1], 'categories': ['hamlet', 'jay-z/r. kelly'], 'extra': extras, 'meta': ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight'], 'texts': ["what art thou that usurp'st this time of night,", 'together with that fair and warlike form', 'in which the majesty of buried denmark', 'did sometimes march? by heaven i charge thee, speak!', 'halt! who goes there?', 'it is i sire tone from brooklyn.', 'well, speak up man what is it?', 'news from the east sire! the best of both worlds has returned!']})

def test_to_dict(self):
    np.random.seed(0)
    random.seed(0)
    corpus = build_hamlet_jz_corpus()
    j = ScatterChartExplorer(corpus, minimum_term_frequency=0).to_dict('hamlet')
    self.assertEqual(set(j.keys()), set(['info', 'data', 'docs']))
    self.assertEqual(set(j['info'].keys()), set(['not_category_name', 'category_name', 'category_terms', 'not_category_internal_names', 'not_category_terms', 'category_internal_name', 'categories', 'neutral_category_name', 'extra_category_name', 'neutral_category_internal_names', 'extra_category_internal_names']))
    self.assertEqual(list(j['docs']['labels']), [0, 0, 0, 0, 1, 1, 1, 1])
    self.assertEqual(list(j['docs']['texts']), ["what art thou that usurp'st this time of night,", 'together with that fair and warlike form', 'in which the majesty of buried denmark', 'did sometimes march? by heaven i charge thee, speak!', 'halt! who goes there?', 'it is i sire tone from brooklyn.', 'well, speak up man what is it?', 'news from the east sire! the best of both worlds has returned!'])
    expected = {'y': 0.5, 'ncat': 0, 'ncat25k': 0, 'bg': 5, 'cat': 1, 's': 0.5, 'term': 'art', 'os': 0.5192, 'extra': 0, 'extra25k': 0, 'cat25k': 758, 'x': 0.06, 'neut': 0, 'neut25k': 0, 'ox': 5, 'oy': 3}
    actual = [t for t in j['data'] if t['term'] == 'art'][0]
    '\n\t\tfor var in expected.keys():\n\t\t\ttry:\n\t\t\t\t#np.testing.assert_almost_equal(actual[var], expected[var],decimal=1)\n\t\t\texcept TypeError:\n\t\t\t\tself.assertEqual(actual[var], expected[var])\n\t\t'
    self.assertEqual(set(expected.keys()), set(actual.keys()))
    self.assertEqual(expected['term'], actual['term'])
    self.assertEqual(j['docs'].keys(), {'texts', 'labels', 'categories'})
    j = ScatterChartExplorer(corpus, minimum_term_frequency=0).inject_term_metadata({'art': {'display': 'blah blah blah', 'color': 'red'}}).to_dict('hamlet')
    actual = [t for t in j['data'] if t['term'] == 'art'][0]
    expected = {'y': 0.5, 'ncat': 0, 'ncat25k': 0, 'bg': 5, 'cat': 1, 's': 0.5, 'term': 'art', 'os': 0.5192, 'extra': 0, 'extra25k': 0, 'cat25k': 758, 'x': 0.06, 'neut': 0, 'neut25k': 0, 'ox': 5, 'oy': 3, 'etc': {'display': 'blah blah blah', 'color': 'red'}}
    self.assertEqual(set(actual.keys()), set(expected.keys()))
    self.assertEqual(actual['etc'], expected['etc'])
    actual = [t for t in j['data'] if t['term'] != 'art'][0]
    self.assertEqual(set(actual.keys()), set(expected.keys()))
    self.assertEqual(actual['etc'], {})

def test_hide_terms(self):
    corpus = build_hamlet_jz_corpus().get_unigram_corpus()
    terms_to_hide = ['thou', 'heaven']
    sc = ScatterChartExplorer(corpus, minimum_term_frequency=0).hide_terms(terms_to_hide)
    self.assertEquals(type(sc), ScatterChartExplorer)
    j = sc.to_dict('hamlet', include_term_category_counts=True)
    self.assertTrue(all(['display' in t and t['display'] == False for t in j['data'] if t['term'] in terms_to_hide]))
    self.assertTrue(all(['display' not in t for t in j['data'] if t['term'] not in terms_to_hide]))

def test_include_term_category_counts(self):
    corpus = build_hamlet_jz_corpus().get_unigram_corpus()
    j = ScatterChartExplorer(corpus, minimum_term_frequency=0).to_dict('hamlet', include_term_category_counts=True)
    self.assertEqual(set(j.keys()), set(['info', 'data', 'docs', 'termCounts']))
    self.assertEqual(len(j['termCounts']), corpus.get_num_categories())
    term_idx_set = set()
    for cat_counts in j['termCounts']:
        term_idx_set |= set(cat_counts.keys())
        self.assertTrue(all([freq >= docs for freq, docs in cat_counts.values()]))
    self.assertEqual(len(term_idx_set), corpus.get_num_terms())

def test_multi_categories(self):
    corpus = get_test_corpus()
    j_vs_all = ScatterChartExplorer(corpus=corpus, minimum_term_frequency=0).to_dict('hamlet')
    j_vs_swift = ScatterChartExplorer(corpus=corpus, minimum_term_frequency=0).to_dict('hamlet', not_categories=['swift'])
    self.assertNotEqual(set(j_vs_all['info']['not_category_internal_names']), set(j_vs_swift['info']['not_category_internal_names']))
    self.assertEqual(list(j_vs_all['docs']['labels']), list(j_vs_swift['docs']['labels']))
    self.assertEqual(list(j_vs_all['docs']['categories']), list(j_vs_swift['docs']['categories']))

def test_metadata(self):
    corpus = build_hamlet_jz_corpus()
    meta = ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight']
    j = ScatterChartExplorer(corpus, minimum_term_frequency=0).to_dict('hamlet', metadata=meta)
    self.maxDiff = None
    j['docs']['labels'] = list(j['docs']['labels'])
    self.assertEqual(j['docs'], {'labels': [0, 0, 0, 0, 1, 1, 1, 1], 'categories': ['hamlet', 'jay-z/r. kelly'], 'meta': ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight'], 'texts': ["what art thou that usurp'st this time of night,", 'together with that fair and warlike form', 'in which the majesty of buried denmark', 'did sometimes march? by heaven i charge thee, speak!', 'halt! who goes there?', 'it is i sire tone from brooklyn.', 'well, speak up man what is it?', 'news from the east sire! the best of both worlds has returned!']})

def test_alternative_text(self):
    corpus = build_hamlet_jz_corpus_with_alt_text()
    j = ScatterChartExplorer(corpus, minimum_term_frequency=0).to_dict('hamlet', alternative_text_field='alt')
    self.assertEqual(j['docs']['texts'][0], j['docs']['texts'][0].upper())
    j = ScatterChartExplorer(corpus, minimum_term_frequency=0).to_dict('hamlet')
    self.assertNotEqual(j['docs']['texts'][0], j['docs']['texts'][0].upper())

def test_extra_features(self):
    corpus = build_hamlet_jz_corpus_with_meta()
    meta = ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight']
    j = ScatterChartExplorer(corpus, minimum_term_frequency=0, use_non_text_features=True).to_dict('hamlet', metadata=meta)
    extras = [{'cat3': 1, 'cat4': 2}, {'cat4': 2}, {'cat3': 2, 'cat5': 1}, {'cat6': 2, 'cat9': 1}, {'cat3': 1, 'cat4': 2}, {'cat1': 2, 'cat2': 1}, {'cat2': 2, 'cat5': 1}, {'cat3': 2, 'cat4': 1}]
    extras = [{'cat1': 2}] * 8
    self.maxDiff = None
    j['docs']['labels'] = list(j['docs']['labels'])
    self.assertEqual(j['docs'], {'labels': [0, 0, 0, 0, 1, 1, 1, 1], 'categories': ['hamlet', 'jay-z/r. kelly'], 'extra': extras, 'meta': ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight'], 'texts': ["what art thou that usurp'st this time of night,", 'together with that fair and warlike form', 'in which the majesty of buried denmark', 'did sometimes march? by heaven i charge thee, speak!', 'halt! who goes there?', 'it is i sire tone from brooklyn.', 'well, speak up man what is it?', 'news from the east sire! the best of both worlds has returned!']})

class EmbeddingsResolver:

    def __init__(self, corpus):
        self.corpus_ = corpus
        self.embeddings_ = None
        self.word2vec_model_ = None

    def set_embeddings(self, embeddings):
        """
        Specifies fixed set of embeddings
        :param embeddings: array-like, sparse or dense, shape should be (embedding size, # terms)
        :return: EmbeddingsResolver
        """
        if self.embeddings_ is not None:
            raise Exception('You have already set embeddings by running set_embeddings or set_embeddings_model.')
        assert embeddings.shape[1] == self.corpus_.get_num_terms()
        self.embeddings_ = embeddings.T
        self.vocab_ = self.corpus_.get_terms()
        return self

    def set_embeddings_model(self, model=None, term_acceptance_re=re.compile('[a-z]{3,}')):
        """

        :param model: gensim word2vec.Word2Vec model
        :param term_acceptance_re : SRE_Pattern, Regular expression to identify
            valid terms, default re.compile('[a-z]{3,}')
        :return: EmbeddingsResolver
        """
        if self.embeddings_ is not None:
            raise Exception('You have already set embeddings by running set_embeddings or set_embeddings_model.')
        self.word2vec_model_ = model
        if term_acceptance_re is not None:
            acceptable_terms = set([t for t in self.corpus_.get_terms() if term_acceptance_re.match(t)])
        else:
            acceptable_terms = set(self.corpus_.get_terms())
        model = Word2VecFromParsedCorpus(self.corpus_, model).train()
        self.corpus_ = self.corpus_.remove_terms(set(self.corpus_.get_terms()) - acceptable_terms)
        weight_list = [model.wv[word] for word in model.wv.key_to_index.keys()]
        self.embeddings_ = np.stack(weight_list)
        self.vocab_ = list(model.wv.key_to_index.keys())
        return self

    def project_embeddings(self, projection_model=None, x_dim=0, y_dim=1):
        """

        :param projection_model: sklearn unsupervised model (e.g., PCA) by default the recommended model is umap.UMAP,
            which requires UMAP in to be installed
        :param x_dim: int, default 0, dimension of transformation matrix for x-axis
        :param y_dim: int, default 1, dimension of transformation matrix for y-axis
        :return:
        """
        axes = self.project(projection_model)
        word_axes = pd.DataFrame({'term': [w for w in self.vocab_], 'x': axes.T[x_dim], 'y': axes.T[y_dim]}).set_index('term').reindex(pd.Series(self.corpus_.get_terms())).dropna()
        self.corpus_ = self.corpus_.remove_terms(set(self.corpus_.get_terms()) - set(word_axes.index))
        word_axes = word_axes.reindex(self.corpus_.get_terms()).dropna()
        return (self.corpus_, word_axes)
    "\n    def get_svd(self, num_dims, category):\n        U, s, V = sparse.linalg.svds(self.corpus_._X.astype('d'), k=num_dims)\n        Y = self.corpus_.get_category_ids() == category\n        [pearsonr(U.T[i], ) for i in range(num_dims)]\n    "

    def project(self, projection_model=None):
        """
        :param projection_model: sklearn unsupervised model (e.g., PCA) by default the recommended model is umap.UMAP,
        which requires UMAP in to be installed

        :return: array, shape (num dimension, vocab size)
        """
        if self.embeddings_ is None:
            raise Exception('Run set_embeddings_model or set_embeddings to get embeddings')
        if projection_model is None:
            try:
                import umap
            except:
                raise Exception('Please install umap (pip install umap-learn) to use the default projection_model.')
            projection_model = umap.UMAP(min_dist=0.5, metric='cosine')
        axes = projection_model.fit_transform(self.embeddings_)
        return axes

def set_embeddings_model(self, model=None, term_acceptance_re=re.compile('[a-z]{3,}')):
    """

        :param model: gensim word2vec.Word2Vec model
        :param term_acceptance_re : SRE_Pattern, Regular expression to identify
            valid terms, default re.compile('[a-z]{3,}')
        :return: EmbeddingsResolver
        """
    if self.embeddings_ is not None:
        raise Exception('You have already set embeddings by running set_embeddings or set_embeddings_model.')
    self.word2vec_model_ = model
    if term_acceptance_re is not None:
        acceptable_terms = set([t for t in self.corpus_.get_terms() if term_acceptance_re.match(t)])
    else:
        acceptable_terms = set(self.corpus_.get_terms())
    model = Word2VecFromParsedCorpus(self.corpus_, model).train()
    self.corpus_ = self.corpus_.remove_terms(set(self.corpus_.get_terms()) - acceptable_terms)
    weight_list = [model.wv[word] for word in model.wv.key_to_index.keys()]
    self.embeddings_ = np.stack(weight_list)
    self.vocab_ = list(model.wv.key_to_index.keys())
    return self

class CategoryEmbeddingsResolver:

    def __init__(self, corpus, term_acceptance_re=re.compile('[a-z]{3,}')):
        self.corpus_ = corpus
        self.category_embeddings_ = {}
        self.category_word2vec_model_ = {}
        self.term_acceptance_re = term_acceptance_re

    def _verify_category(self, category):
        if category not in self.corpus_.get_categories():
            raise Exception('Category %s is not in corpus.' % category)
        if category in self.category_embeddings_:
            raise Exception('You have already set embeddings by running set_embeddings or set_embeddings_model.')

    def embed_category(self, category, model=None):
        """

        :param model: gensim word2vec.Word2Vec model
        :param term_acceptance_re : SRE_Pattern, Regular expression to identify
            valid terms, default re.compile('[a-z]{3,}')
        :return: EmbeddingsResolver
        """
        self._verify_category(category)
        if self.term_acceptance_re is not None:
            acceptable_terms = set([t for t in self.corpus_.get_terms() if self.term_acceptance_re.match(t)])
        else:
            acceptable_terms = set(self.corpus_.get_terms())
        trained_model = CategorySpecificWord2VecFromParsedCorpus(self.corpus_, category, model).train()
        self.category_word2vec_model_[category] = trained_model
        word2dwe = {word: trained_model.wv[word] for word in trained_model.wv.key_to_index.keys()}
        self.category_embeddings_[category] = word2dwe
        return self

    def embed_all_categories(self):
        for category in self.corpus_.get_categories():
            self.embed_category(category)
        return self

def embed_category(self, category, model=None):
    """

        :param model: gensim word2vec.Word2Vec model
        :param term_acceptance_re : SRE_Pattern, Regular expression to identify
            valid terms, default re.compile('[a-z]{3,}')
        :return: EmbeddingsResolver
        """
    self._verify_category(category)
    if self.term_acceptance_re is not None:
        acceptable_terms = set([t for t in self.corpus_.get_terms() if self.term_acceptance_re.match(t)])
    else:
        acceptable_terms = set(self.corpus_.get_terms())
    trained_model = CategorySpecificWord2VecFromParsedCorpus(self.corpus_, category, model).train()
    self.category_word2vec_model_[category] = trained_model
    word2dwe = {word: trained_model.wv[word] for word in trained_model.wv.key_to_index.keys()}
    self.category_embeddings_[category] = word2dwe
    return self

class EmbeddingAligner(object):

    def __init__(self, category_embedding_resolver, category1, category2, prefix1=None, prefix2=None):
        """

        :param category_embedding_resolver: CategoryEmbeddingsResolver
        :param category1: str
        :param category2: str
        :param prefix1: str
        :param prefix2: str
        """
        self.category_embedding_resolver = category_embedding_resolver
        valid_categories = category_embedding_resolver.corpus_.get_categories()
        assert category1 in valid_categories
        assert category2 in valid_categories
        self.category1 = category1
        self.category2 = category2
        cat1_dwe_dict = category_embedding_resolver.category_embeddings_[category1]
        cat2_dwe_dict = category_embedding_resolver.category_embeddings_[category2]
        self.terms = np.array(list(set(cat1_dwe_dict.keys()) & set(cat2_dwe_dict.keys())))
        self.cat1_dwe_ar = np.stack([cat1_dwe_dict[word] for word in self.terms])
        self.cat2_dwe_ar = np.stack([cat2_dwe_dict[word] for word in self.terms])
        self.pairwise_sim, sv = scipy.linalg.orthogonal_procrustes(self.cat1_dwe_ar, self.cat2_dwe_ar)
        import pdb
        pdb.set_trace()
        self.pairwise_sim_sort = np.argsort(-self.pairwise_sim, axis=1)

        def distinct_prefix(x, y):
            for i, (xc, yc) in enumerate(zip(x, y)):
                if xc != yc:
                    return (x[:i + 1], y[:i + 1])
            return (x, y)
        myprefix1, myprefix2 = distinct_prefix(category1, category2)
        self.prefix1 = myprefix1 if prefix1 is None else prefix1
        self.prefix2 = myprefix2 if prefix2 is None else prefix2
        self.labeled_terms = np.array([self.prefix1 + '_' + w for w in self.terms] + [self.prefix2 + '_' + w for w in self.terms])

    def get_terms(self):
        return self.terms

    def project_separate(self, projector=None):
        if projector is None:
            from umap import UMAP
            projector = UMAP(n_components=2, metric='cosine')
        both_category_embeddings = np.vstack([self.cat1_dwe_ar_norm, self.cat2_dwe_ar_norm])
        projected_ar = projector.fit_transform(both_category_embeddings)
        df = pd.DataFrame(projected_ar, columns=['x', 'y'], index=self.labeled_terms)
        df['category'] = [self.category1] * len(self.terms) + [self.category2] * len(self.terms)
        return df

    def get_report_df(self, n_terms=5):
        conterpart_idx = np.hstack([np.arange(len(self.terms)) + len(self.terms), np.arange(len(self.terms))])
        idx = np.arange(len(self.terms))
        similarity_df = pd.DataFrame({'cosine_distance': self.pairwise_sim[[idx], conterpart_idx[idx]][0], 'rank_' + self.prefix1: np.where(self.pairwise_sim_sort[idx] == conterpart_idx[idx][:, None])[1], 'rank_' + self.prefix2: np.where(self.pairwise_sim_sort[conterpart_idx[idx]] == idx[:, None])[1], 'context_' + self.prefix1: pd.DataFrame(self.labeled_terms[self.pairwise_sim_sort[idx, 1:1 + n_terms]]).apply(', '.join, axis=1).values, 'context_' + self.prefix2: pd.DataFrame(self.labeled_terms[self.pairwise_sim_sort[conterpart_idx[idx], 1:1 + n_terms]]).apply(', '.join, axis=1).values}, index=self.terms)
        return pd.merge(similarity_df.assign(min_rank=lambda x: np.max(x[['rank_' + self.prefix1, 'rank_' + self.prefix1]], axis=1)).sort_values(by='min_rank', ascending=False), self.category_embedding_resolver.corpus_.get_term_freq_df(), left_index=True, right_index=True)

def __init__(self, category_embedding_resolver, category1, category2, prefix1=None, prefix2=None):
    """

        :param category_embedding_resolver: CategoryEmbeddingsResolver
        :param category1: str
        :param category2: str
        :param prefix1: str
        :param prefix2: str
        """
    self.category_embedding_resolver = category_embedding_resolver
    valid_categories = category_embedding_resolver.corpus_.get_categories()
    assert category1 in valid_categories
    assert category2 in valid_categories
    self.category1 = category1
    self.category2 = category2
    cat1_dwe_dict = category_embedding_resolver.category_embeddings_[category1]
    cat2_dwe_dict = category_embedding_resolver.category_embeddings_[category2]
    self.terms = np.array(list(set(cat1_dwe_dict.keys()) & set(cat2_dwe_dict.keys())))
    self.cat1_dwe_ar = np.stack([cat1_dwe_dict[word] for word in self.terms])
    self.cat2_dwe_ar = np.stack([cat2_dwe_dict[word] for word in self.terms])
    self.pairwise_sim, sv = scipy.linalg.orthogonal_procrustes(self.cat1_dwe_ar, self.cat2_dwe_ar)
    import pdb
    pdb.set_trace()
    self.pairwise_sim_sort = np.argsort(-self.pairwise_sim, axis=1)

    def distinct_prefix(x, y):
        for i, (xc, yc) in enumerate(zip(x, y)):
            if xc != yc:
                return (x[:i + 1], y[:i + 1])
        return (x, y)
    myprefix1, myprefix2 = distinct_prefix(category1, category2)
    self.prefix1 = myprefix1 if prefix1 is None else prefix1
    self.prefix2 = myprefix2 if prefix2 is None else prefix2
    self.labeled_terms = np.array([self.prefix1 + '_' + w for w in self.terms] + [self.prefix2 + '_' + w for w in self.terms])

class IndexStore(object):

    def __init__(self):
        self._next_i = 0
        self._i2val = []
        self._val2i = {}

    def getval(self, idx: int) -> Any:
        return self._i2val[idx]

    def getvalbatch(self, y: Iterable) -> List[Any]:
        return [self._i2val[x] for x in y]

    def __len__(self) -> int:
        return len(self._i2val)

    def __contains__(self, val: Any) -> bool:
        return self._hasval(val)

    def _hasval(self, val: Any) -> bool:
        return val in self._val2i

    def getidxstrictbatch(self, vals: Iterable[Any]) -> List[int]:
        return [self._val2i[t] for t in vals]

    def getidx(self, val: Any) -> int:
        try:
            return self._val2i[val]
        except KeyError:
            self._val2i[val] = self._next_i
            self._i2val.append(val)
            self._next_i += 1
            return self._next_i - 1

    def getidxstrict(self, val: Any) -> int:
        return self._val2i[val]

    def getnumvals(self) -> int:
        return self._next_i

    def getvals(self) -> Set[Any]:
        return set(self._i2val)

    def hasidx(self, idx: int) -> bool:
        return 0 <= idx < self._next_i

    def items(self) -> Iterable[Tuple[int, Any]]:
        return enumerate(self._i2val)

    def batch_delete_vals(self, values: Iterable[any]) -> 'IndexStore':
        idx_delete_list = []
        for val in values:
            if not self._hasval(val):
                raise KeyError(str(val) + ' not found')
            idx_delete_list.append(self.getidx(val))
        return self.batch_delete_idx(idx_delete_list)

    def batch_delete_idx(self, idx_list: Iterable[int]) -> 'IndexStore':
        new_idxstore = IndexStore()
        last_idx_to_delete = -1
        number_of_values = self.getnumvals()
        for idx_to_delete in sorted(idx_list):
            if idx_to_delete >= number_of_values:
                raise ValueError('index ' + str(idx_to_delete) + ' not found')
            new_idxstore._i2val += self._i2val[last_idx_to_delete + 1:idx_to_delete]
            last_idx_to_delete = idx_to_delete
        new_idxstore._i2val += self._i2val[last_idx_to_delete + 1:]
        new_idxstore._val2i = {val: i for i, val in enumerate(new_idxstore._i2val)}
        new_idxstore._next_i = len(new_idxstore._val2i)
        return new_idxstore

    def _regenerate_val2i_and_next_i(self) -> None:
        self._val2i = {val: idx for idx, val in enumerate(self._i2val)}
        self._next_i = len(self._i2val)

    def values(self) -> List[Any]:
        """

		Returns
		-------
		list
			A list containing all values registered.
		"""
        return self._i2val

    def rename(self, old_to_new_vals: List[Tuple[str, str]]):
        for old_val, new_val in old_to_new_vals:
            cur_i = self._val2i[old_val]
            del self._val2i[old_val]
            self._val2i[new_val] = cur_i
            self._i2val[cur_i] = new_val

def getvals(self) -> Set[Any]:
    return set(self._i2val)

class IndexStoreFromList(object):

    @staticmethod
    def build(values):
        """
		Parameters
		----------
		values: [term, ...]

		Returns
		-------
		IndexStore
		"""
        idxstore = IndexStore()
        idxstore._i2val = list(values)
        idxstore._val2i = {term: i for i, term in enumerate(values)}
        idxstore._next_i = len(values)
        return idxstore

@staticmethod
def build(values):
    """
		Parameters
		----------
		values: [term, ...]

		Returns
		-------
		IndexStore
		"""
    idxstore = IndexStore()
    idxstore._i2val = list(values)
    idxstore._val2i = {term: i for i, term in enumerate(values)}
    idxstore._next_i = len(values)
    return idxstore

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

def get_node_to_component_dict(self):
    return self.id_node_df.set_index('name')['Component'].to_dict()

def produce_pairplot(corpus, asian_mode=False, category_width_in_pixels=500, category_height_in_pixels=700, term_width_in_pixels=500, term_height_in_pixels=700, terms_to_show=3000, scaler=scale_neg_1_to_1_with_zero_mean, term_ranker=AbsoluteFrequencyRanker, use_metadata=False, category_projector=CategoryProjector(), category_projection=None, topic_model_term_lists=None, topic_model_preview_size=10, metadata_descriptions=None, initial_category=None, x_dim=0, y_dim=1, show_halo=True, num_terms_in_halo=5, category_color_func='(function(x) {return "#5555FF"})', protocol='https', d3_url_struct=D3URLs(), category_focused=False, verbose=False, use_full_doc=True, default_to_term_comparison=True, category_x_label='', category_y_label='', category_tooltip_func='(function(d) {return d.term})', term_tooltip_func='(function(d) {return d.term})', category_show_axes_and_cross_hairs=False, highlight_selected_category=True, term_x_label=None, term_y_label=None, wordfish_style=False, category_metadata_df=None, return_structure=False, **kwargs):
    if category_projection is None:
        if use_metadata:
            category_projection = category_projector.use_metadata().project_with_metadata(corpus, x_dim=x_dim, y_dim=y_dim)
        else:
            category_projection = category_projector.project(corpus, x_dim=x_dim, y_dim=y_dim)
    if initial_category is None:
        initial_category = corpus.get_categories()[0]
    category_scatter_chart_explorer = _get_category_scatter_chart_explorer(category_projection, scaler, term_ranker, verbose)
    if category_metadata_df is not None:
        if type(category_metadata_df) != pd.DataFrame:
            category_metadata_df = category_metadata_df(corpus)
        category_scatter_chart_explorer = category_scatter_chart_explorer.inject_term_metadata_df(category_metadata_df)
    category_scatter_chart_data = category_scatter_chart_explorer.to_dict(category=initial_category, max_docs_per_category=0)
    term_plot_change_func = _get_term_plot_change_js_func(wordfish_style, category_focused, initial_category)
    category_scatterplot_structure = ScatterplotStructure(VizDataAdapter(category_scatter_chart_data), width_in_pixels=category_width_in_pixels, height_in_pixels=category_height_in_pixels, asian_mode=asian_mode, use_non_text_features=True, show_characteristic=False, x_label=category_x_label, y_label=category_y_label, show_axes_and_cross_hairs=category_show_axes_and_cross_hairs, full_data='getCategoryDataAndInfo()', show_top_terms=False, get_tooltip_content=category_tooltip_func, color_func=category_color_func, show_axes=False, horizontal_line_y_position=0, vertical_line_x_position=0, unified_context=not wordfish_style, show_category_headings=False, show_cross_axes=True, div_name='cat-plot', alternative_term_func=term_plot_change_func, highlight_selected_category=highlight_selected_category)
    compacted_corpus = AssociationCompactor(terms_to_show, use_non_text_features=use_metadata).compact(corpus)
    terms_to_hide = set(corpus.get_terms(use_metadata=use_metadata)) - set(compacted_corpus.get_terms(use_metadata=use_metadata))
    if verbose:
        print('num terms to hide', len(terms_to_hide))
        print('num terms to show', compacted_corpus.get_num_terms())
    term_corpus = category_projection.get_corpus()
    term_scatter_chart_explorer = ScatterChartExplorer(term_corpus, minimum_term_frequency=0, minimum_not_category_term_frequency=0, pmi_threshold_coefficient=0, term_ranker=term_ranker, use_non_text_features=False, add_extra_features=use_metadata, score_transform=stretch_0_to_1, verbose=verbose, dont_filter=True).hide_terms(terms_to_hide)
    if default_to_term_comparison:
        if topic_model_term_lists is not None:
            term_scatter_chart_explorer.inject_metadata_term_lists(topic_model_term_lists)
        if metadata_descriptions is not None:
            term_scatter_chart_explorer.inject_metadata_descriptions(metadata_descriptions)
        if use_metadata:
            tdf = corpus.get_metadata_freq_df('')
        else:
            tdf = corpus.get_term_freq_df('')
        scores = RankDifference().get_scores(tdf[initial_category], tdf[[c for c in corpus.get_categories() if c != initial_category]].sum(axis=1))
        term_scatter_chart_data = term_scatter_chart_explorer.to_dict(category=initial_category, scores=scores, include_term_category_counts=True, transform=dense_rank, **kwargs)
        y_label = (initial_category,)
        x_label = ('Not ' + initial_category,)
        color_func = None
        show_top_terms = True
        show_axes = False
    else:
        term_projection = category_projection.get_term_projection()
        original_x = term_projection['x']
        original_y = term_projection['y']
        x_coords = scaler(term_projection['x'])
        y_coords = scaler(term_projection['y'])
        x_label = term_x_label if term_x_label is not None else ''
        y_label = term_y_label if term_y_label is not None else ''
        show_axes = True
        horizontal_line_y_position = 0
        vertical_line_x_position = 0
        term_scatter_chart_explorer.inject_coordinates(x_coords, y_coords, original_x=original_x, original_y=original_y)
        if topic_model_term_lists is not None:
            term_scatter_chart_explorer.inject_metadata_term_lists(topic_model_term_lists)
        if metadata_descriptions is not None:
            term_scatter_chart_explorer.inject_metadata_descriptions(metadata_descriptions)
        term_scatter_chart_data = term_scatter_chart_explorer.to_dict(category=initial_category, category_name=initial_category, include_term_category_counts=True, **kwargs)
        color_func = '(function(x) {return "#5555FF"})'
        show_top_terms = False
    term_scatterplot_structure = ScatterplotStructure(VizDataAdapter(term_scatter_chart_data), width_in_pixels=term_width_in_pixels, height_in_pixels=term_height_in_pixels, use_full_doc=use_metadata or use_full_doc, asian_mode=asian_mode, use_non_text_features=use_metadata, show_characteristic=False, x_label=x_label, y_label=y_label, full_data='getTermDataAndInfo()', show_top_terms=show_top_terms, get_tooltip_content=term_tooltip_func, color_func=color_func, show_axes=show_axes, topic_model_preview_size=topic_model_preview_size, show_category_headings=False, div_name='d3-div-1', unified_context=not wordfish_style, highlight_selected_category=highlight_selected_category)
    pair_plot_structure = PairPlotFromScatterplotStructure(category_scatterplot_structure, term_scatterplot_structure, category_projection, category_width_in_pixels, category_height_in_pixels, num_terms=num_terms_in_halo, show_halo=show_halo, d3_url_struct=d3_url_struct, x_dim=x_dim, y_dim=y_dim, protocol=protocol)
    if return_structure:
        return pair_plot_structure
    return pair_plot_structure.to_html()

def _get_category_scatter_chart_explorer(category_projection, scaler, term_ranker, verbose):
    category_scatter_chart_explorer = ScatterChartExplorer(category_projection.get_corpus(), minimum_term_frequency=0, minimum_not_category_term_frequency=0, pmi_threshold_coefficient=0, filter_unigrams=False, jitter=0, max_terms=None, use_non_text_features=True, term_significance=None, terms_to_include=None, verbose=verbose, dont_filter=True)
    proj_df = category_projection.get_pandas_projection()
    category_scatter_chart_explorer.inject_coordinates(x_coords=scaler(proj_df['x']), y_coords=scaler(proj_df['y']), original_x=proj_df['x'], original_y=proj_df['y'])
    return category_scatter_chart_explorer

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

def get_axes_labels(self, num_terms=5):
    df = self.get_term_projection()
    return {'right': list(df.sort_values(by='x', ascending=False).index[:num_terms]), 'left': list(df.sort_values(by='x', ascending=True).index[:num_terms]), 'top': list(df.sort_values(by='y', ascending=False).index[:num_terms]), 'bottom': list(df.sort_values(by='y', ascending=True).index[:num_terms])}

def get_nearest_terms(self, num_terms: int=5) -> dict:
    return term_coordinates_to_halo(term_coordinates_df=self.get_term_projection(), num_terms=num_terms)

def extract_finditer(pos_seq, regex=SimpleNP):
    """The "GreedyFSA" method in Handler et al. 2016.
	Returns token position spans of valid ngrams."""
    ss = coarse_tag_str(pos_seq)

    def gen():
        for m in re.finditer(regex, ss):
            yield (m.start(), m.end())
    return list(gen())

def extract_ngram_filter(pos_seq, regex=SimpleNP, minlen=1, maxlen=8):
    """The "FilterFSA" method in Handler et al. 2016.
	Returns token position spans of valid ngrams."""
    ss = coarse_tag_str(pos_seq)

    def gen():
        for s in xrange(len(ss)):
            for n in xrange(minlen, 1 + min(maxlen, len(ss) - s)):
                e = s + n
                substr = ss[s:e]
                if re.match(regex + '$', substr):
                    yield (s, e)
    return list(gen())

class TestCredTFIDF(TestCase):

    def test_get_score_df(self):
        corpus = build_hamlet_jz_corpus()
        self.assertEqual(set(CredTFIDF(corpus).set_categories('hamlet').get_score_df().columns), set(['pos_cred_tfidf', 'neg_cred_tfidf', 'delta_cred_tf_idf']))

def test_get_score_df(self):
    corpus = build_hamlet_jz_corpus()
    self.assertEqual(set(CredTFIDF(corpus).set_categories('hamlet').get_score_df().columns), set(['pos_cred_tfidf', 'neg_cred_tfidf', 'delta_cred_tf_idf']))

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

def visualize(self, visualizer=BubbleDiachronicVisualization):
    assert issubclass(visualizer, DiachronicVisualizer)
    return visualizer.visualize(self.get_display_dataframe())

def get_ternary_colors(scores: np.array, negative_color='#d72d00', zero_color='#bdbdbd', positive_color='#2a3e63') -> np.array:
    colors = np.array([zero_color] * len(scores))
    colors[scores < 0] = negative_color
    colors[scores > 0] = positive_color
    return list(colors)

