# Cluster 3

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

def _use_only_selected_terms(self, json_df):
    term_df = pd.DataFrame({'term': self.scatterchartdata.terms_to_include})
    return pd.merge(json_df, term_df, on='term', how='inner')

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

def to_dict_without_categories(self):
    if self.y_coords is None or self.x_coords is None or self.original_x is None or (self.original_y is None):
        raise NeedToInjectCoordinatesException('This function requires you run inject_coordinates.')
    return {'data': self._add_x_and_y_coords_to_term_df_if_injected(self.term_doc_matrix.get_term_count_df().rename(columns={'corpus': 'cat'}).assign(cat25k=lambda df: (df['cat'] * 1.0 / df['cat'].sum() * 25000).apply(np.round).astype(int))).reset_index().sort_values(by=['x', 'y', 'term']).to_dict(orient='records')}

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

def get_total_unigram_count(self) -> int:
    return self._get_unigram_term_freq_df().sum()

def _get_unigram_term_freq_df(self) -> pd.DataFrame:
    return self._get_corpus_unigram_freq(self.get_term_count_df()['corpus'])

def get_term_freqs(self, non_text: bool=False) -> np.array:
    return self.get_term_doc_mat(non_text=non_text).sum(axis=0).A1

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

def old_get_term_freq_df(self):
    d = {'term': self._term_idx_store._i2val}
    for i, category in self._category_idx_store.items():
        d[category + ' freq'] = self._X[self._y == i].sum(axis=0).A1
    return pd.DataFrame(d).set_index('term')

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

def remove_terms_used_in_less_than_num_categories(self, threshold, use_metadata=False):
    term_mask = (self.get_freq_df(use_metadata=use_metadata).values > 0).sum(axis=1) < threshold
    term_indices_to_remove = np.where(term_mask)[0]
    return self.remove_terms_by_indices(term_indices_to_remove, use_metadata)

class DataFrameCorpus(Corpus):

    def __init__(self, X, mX, y, term_idx_store, category_idx_store, metadata_idx_store, raw_texts, df, unigram_frequency_path=None):
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
        self._df = df
        Corpus.__init__(self, X, mX, y, term_idx_store, category_idx_store, metadata_idx_store, raw_texts, unigram_frequency_path)

    def _apply_mask_to_df(self, new_y_mask, new_df):
        df_to_ret = self._df if new_df is None else new_df
        if new_y_mask is None:
            return df_to_ret
        return df_to_ret[new_y_mask].reset_index(drop=True)

    def get_df(self):
        """
        Returns
        -------
        pd.DataFrame
        """
        return self._df

    def get_field(self, field):
        """
        Parameters
        ----------
        field: str, field name

        Returns
        -------
        pd.Series, all members of field
        """
        return self._df[field]

    def assign(self, **kwargs):
        """
        Runs assign in the internal dataframe

        :param kwargs:
        :return: Corpus
        """
        self._df = self._df.assign(**kwargs)
        return self

    def search(self, ngram, non_text: bool=False):
        """
        Parameters
        ----------
        ngram, str or unicode, string to search for

        Returns
        -------
        pd.DataFrame, {self._parsed_col: <matching texts>, self._category_col: <corresponding categories>, ...}

        """
        mask = self._document_index_mask(ngram, non_text)
        return self._df[mask]

    def make_column_metadata(self, column):
        """

        :param column: str
        :return: Corpus
        """
        return self.add_doc_names_as_metadata(self.get_df()[column])

def _apply_mask_to_df(self, new_y_mask, new_df):
    df_to_ret = self._df if new_df is None else new_df
    if new_y_mask is None:
        return df_to_ret
    return df_to_ret[new_y_mask].reset_index(drop=True)

def assign(self, **kwargs):
    """
        Runs assign in the internal dataframe

        :param kwargs:
        :return: Corpus
        """
    self._df = self._df.assign(**kwargs)
    return self

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

def use_all_categories(self):
    """
		Returns
		-------
		PriorFactory
		"""
    term_df = self.term_ranker.get_ranks()
    self.priors += term_df.sum(axis=1).fillna(0.0)
    return self

def _reindex_priors(self):
    self.priors = self.priors.reindex(self.term_doc_mat.get_terms()).dropna()

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

class TermDocMatrixFromPandas(TermDocMatrixFactory):

    def __init__(self, data_frame, category_col, text_col, clean_function=lambda x: x, nlp=None, feats_from_spacy_doc=None, verbose=False):
        """Creates a TermDocMatrix from a pandas data frame.

        Parameters
        ----------
        data_frame : pd.DataFrame
            The data frame that contains columns for the category of interest
            and the document text.
        text_col : str
            The name of the column which contains each document's raw text.
        category_col : str
            The name of the column which contains the category of interest.
        clean_function : function, optional
            A function that strips invalid characters out of the document text string,
            returning the new string.
        nlp : function, optional
        feats_from_spacy_doc : FeatsFromSpacyDoc or None
        verbose : boolean, optional
            If true, prints a message every time a document index % 100 is 0.

        See Also
        --------
        TermDocMatrixFactory
        """
        TermDocMatrixFactory.__init__(self, clean_function=clean_function, nlp=nlp, feats_from_spacy_doc=feats_from_spacy_doc)
        self.data_frame = data_frame.reset_index()
        self._text_col = text_col
        self._category_col = category_col
        self._verbose = verbose

    def build(self):
        """Constructs the term doc matrix.

        Returns
        -------
        TermDocMatrix
        """
        X_factory, mX_factory, category_idx_store, term_idx_store, metadata_idx_store, y = self._init_term_doc_matrix_variables()
        parse_pipeline = ParsePipelineFactory(self.get_nlp(), X_factory, mX_factory, category_idx_store, term_idx_store, metadata_idx_store, y, self)
        df = self._clean_and_filter_nulls_and_empties_from_dataframe()
        tdm = self._apply_pipeline_and_get_build_instance(X_factory, mX_factory, category_idx_store, df, parse_pipeline, term_idx_store, metadata_idx_store, y)
        return tdm

    def _apply_pipeline_and_get_build_instance(self, X_factory, mX_factory, category_idx_store, df, parse_pipeline, term_idx_store, metadata_idx_store, y):
        df.apply(parse_pipeline.parse, axis=1)
        y = np.array(y)
        X, mX = self._build_sparse_matrices(y, X_factory, mX_factory)
        tdm = TermDocMatrix(X, mX, y, term_idx_store, category_idx_store, metadata_idx_store)
        return tdm

    def _build_sparse_matrices(self, y, X_factory, mX_factory):
        return build_sparse_matrices(y, X_factory, mX_factory)

    def _init_term_doc_matrix_variables(self):
        return CorpusFactoryHelper.init_term_doc_matrix_variables()

    def _clean_and_filter_nulls_and_empties_from_dataframe(self):
        return self.data_frame.loc[lambda df: df[[self._category_col, self._text_col]].dropna().index][lambda df: df[self._text_col] != ''].reset_index()

def __init__(self, data_frame, category_col, text_col, clean_function=lambda x: x, nlp=None, feats_from_spacy_doc=None, verbose=False):
    """Creates a TermDocMatrix from a pandas data frame.

        Parameters
        ----------
        data_frame : pd.DataFrame
            The data frame that contains columns for the category of interest
            and the document text.
        text_col : str
            The name of the column which contains each document's raw text.
        category_col : str
            The name of the column which contains the category of interest.
        clean_function : function, optional
            A function that strips invalid characters out of the document text string,
            returning the new string.
        nlp : function, optional
        feats_from_spacy_doc : FeatsFromSpacyDoc or None
        verbose : boolean, optional
            If true, prints a message every time a document index % 100 is 0.

        See Also
        --------
        TermDocMatrixFactory
        """
    TermDocMatrixFactory.__init__(self, clean_function=clean_function, nlp=nlp, feats_from_spacy_doc=feats_from_spacy_doc)
    self.data_frame = data_frame.reset_index()
    self._text_col = text_col
    self._category_col = category_col
    self._verbose = verbose

def _clean_and_filter_nulls_and_empties_from_dataframe(self):
    return self.data_frame.loc[lambda df: df[[self._category_col, self._text_col]].dropna().index][lambda df: df[self._text_col] != ''].reset_index()

class TermDocMatrixWithoutCategoriesFromPandas(TermDocMatrixFactory):

    def __init__(self, data_frame, text_col, clean_function=lambda x: x, nlp=None, feats_from_spacy_doc=None, verbose=False):
        """Creates a TermDocMatrix from a pandas data frame.

        Parameters
        ----------
        data_frame : pd.DataFrame
            The data frame that contains columns for the category of interest
            and the document text.
        text_col : str
            The name of the column which contains each document's raw text.
        clean_function : function, optional
            A function that strips invalid characters out of the document text string,
            returning the new string.
        nlp : function, optional
        feats_from_spacy_doc : FeatsFromSpacyDoc or None
        verbose : boolean, optional
            If true, prints a message every time a document index % 100 is 0.

        See Also
        --------
        TermDocMatrixFactory
        """
        TermDocMatrixFactory.__init__(self, clean_function=clean_function, nlp=nlp, feats_from_spacy_doc=feats_from_spacy_doc)
        self.data_frame = data_frame.reset_index()
        self._text_col = text_col
        self._verbose = verbose

    def build(self):
        """Constructs the term doc matrix.

        Returns
        -------
        TermDocMatrix
        """
        X_factory = CSRMatrixFactory()
        mX_factory = CSRMatrixFactory()
        term_idx_store = IndexStore()
        metadata_idx_store = IndexStore()
        parse_pipeline = ParsePipelineFactoryWithoutCategories(self.get_nlp(), X_factory, mX_factory, term_idx_store, metadata_idx_store, self)
        df = self._clean_and_filter_nulls_and_empties_from_dataframe()
        tdm = self._apply_pipeline_and_get_build_instance(X_factory, mX_factory, df, parse_pipeline, term_idx_store, metadata_idx_store)
        return tdm

    def _apply_pipeline_and_get_build_instance(self, X_factory, mX_factory, df, parse_pipeline, term_idx_store, metadata_idx_store):
        df.apply(parse_pipeline.parse, axis=1)
        X, mX = build_sparse_matrices_with_num_docs(len(df), X_factory, mX_factory)
        tdm = TermDocMatrixWithoutCategories(X, mX, term_idx_store, metadata_idx_store)
        return tdm

    def _clean_and_filter_nulls_and_empties_from_dataframe(self):
        df = self.data_frame.loc[self.data_frame[[self._text_col]].dropna().index]
        df = df[df[self._text_col] != ''].reset_index()
        return df

def __init__(self, data_frame, text_col, clean_function=lambda x: x, nlp=None, feats_from_spacy_doc=None, verbose=False):
    """Creates a TermDocMatrix from a pandas data frame.

        Parameters
        ----------
        data_frame : pd.DataFrame
            The data frame that contains columns for the category of interest
            and the document text.
        text_col : str
            The name of the column which contains each document's raw text.
        clean_function : function, optional
            A function that strips invalid characters out of the document text string,
            returning the new string.
        nlp : function, optional
        feats_from_spacy_doc : FeatsFromSpacyDoc or None
        verbose : boolean, optional
            If true, prints a message every time a document index % 100 is 0.

        See Also
        --------
        TermDocMatrixFactory
        """
    TermDocMatrixFactory.__init__(self, clean_function=clean_function, nlp=nlp, feats_from_spacy_doc=feats_from_spacy_doc)
    self.data_frame = data_frame.reset_index()
    self._text_col = text_col
    self._verbose = verbose

def _clean_and_filter_nulls_and_empties_from_dataframe(self):
    df = self.data_frame.loc[self.data_frame[[self._text_col]].dropna().index]
    df = df[df[self._text_col] != ''].reset_index()
    return df

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
def _get_background_terms(num_term_to_keep, term_doc_matrix):
    return term_doc_matrix.get_scaled_f_scores_vs_background().iloc[:int(0.375 * num_term_to_keep)].index

class LogOddsRatioInformativeDirichletPrior(LogOddsRatioUninformativeDirichletPrior):
    """
	Implements the log-odds-ratio with an uninformative dirichlet prior from
		Monroe, B. L., Colaresi, M. P., & Quinn, K. M. (2008). Fightin' words: Lexical feature selection and evaluation for identifying the content of political conflict. Political Analysis, 16(4), 372–403.
	"""

    def __init__(self, priors, sigma=10, scale_type='none', prior_power=1):
        """
		Parameters
		----------
		priors : pd.Series
			term -> prior count

		sigma : np.float
			prior scale

		scale_type : str
			'none': Don't scale prior. Jurafsky approach.
			'class-size': Scale prior st the sum of the priors is the same as the word count
			  in the document-class being scaled
			'corpus-size': Scale prior to the size of the corpus
			'word': Original formulation from MCQ. Sum of priors will be sigma.
			'background-corpus-size': Scale corpus size to multiple of background-corpus.

		prior_power : numeric
			Exponent to apply to prior
			> 1 will shrink frequent words

		"""
        assert scale_type in ['none', 'class-size', 'corpus-size', 'background-corpus-size', 'word']
        self._priors = priors
        self._scale_type = scale_type
        self._prior_power = prior_power
        self._scale = sigma
        LogOddsRatioUninformativeDirichletPrior.__init__(self, sigma)

    def get_priors(self):
        return self._priors

    def get_name(self):
        return 'Log-Odds-Ratio w/ Informative Prior'

    def get_zeta_i_j_given_separate_counts(self, y_i, y_j):
        """
		Parameters
		----------
		y_i, np.array(int)
			Arrays of word counts of words occurring in positive class
		y_j, np.array(int)

		Returns
		-------
		np.array of z-scores
		"""
        n_i, n_j = (y_i.sum(), y_j.sum())
        prior_scale_j = prior_scale_i = 1
        if self._scale_type == 'class-size':
            prior_scale_i = n_i * self._scale * 1.0 / np.sum(self._priors)
            prior_scale_j = n_j * self._scale * 1.0 / np.sum(self._priors)
        elif self._scale_type == 'corpus-size':
            prior_scale_j = prior_scale_i = (n_i + n_j) * self._scale * 1.0 / np.sum(self._priors)
        elif self._scale_type == 'word':
            prior_scale_j = prior_scale_i = self._scale / np.sum(self._priors)
        elif self._scale_type == 'background-corpus-size':
            prior_scale_j = prior_scale_i = self._scale
        a_wj = (self._priors * prior_scale_j) ** self._prior_power
        a_0j = np.sum(a_wj)
        a_wi = (self._priors * prior_scale_i) ** self._prior_power
        a_0i = np.sum(a_wi)
        delta_i_j = np.log((y_i + a_wi) / (n_i + a_0i - y_i - a_wi)) - np.log((y_j + a_wj) / (n_j + a_0j - y_j - a_wj))
        var_delta_i_j = 1.0 / (y_i + a_wi) + 1.0 / (n_i + a_0i - y_i - a_wi) + 1.0 / (y_j + a_wj) + 1.0 / (n_j + a_0j - y_j - a_wj)
        zeta_i_j = delta_i_j / np.sqrt(var_delta_i_j)
        return zeta_i_j

def get_zeta_i_j_given_separate_counts(self, y_i, y_j):
    """
		Parameters
		----------
		y_i, np.array(int)
			Arrays of word counts of words occurring in positive class
		y_j, np.array(int)

		Returns
		-------
		np.array of z-scores
		"""
    n_i, n_j = (y_i.sum(), y_j.sum())
    prior_scale_j = prior_scale_i = 1
    if self._scale_type == 'class-size':
        prior_scale_i = n_i * self._scale * 1.0 / np.sum(self._priors)
        prior_scale_j = n_j * self._scale * 1.0 / np.sum(self._priors)
    elif self._scale_type == 'corpus-size':
        prior_scale_j = prior_scale_i = (n_i + n_j) * self._scale * 1.0 / np.sum(self._priors)
    elif self._scale_type == 'word':
        prior_scale_j = prior_scale_i = self._scale / np.sum(self._priors)
    elif self._scale_type == 'background-corpus-size':
        prior_scale_j = prior_scale_i = self._scale
    a_wj = (self._priors * prior_scale_j) ** self._prior_power
    a_0j = np.sum(a_wj)
    a_wi = (self._priors * prior_scale_i) ** self._prior_power
    a_0i = np.sum(a_wi)
    delta_i_j = np.log((y_i + a_wi) / (n_i + a_0i - y_i - a_wi)) - np.log((y_j + a_wj) / (n_j + a_0j - y_j - a_wj))
    var_delta_i_j = 1.0 / (y_i + a_wi) + 1.0 / (n_i + a_0i - y_i - a_wi) + 1.0 / (y_j + a_wj) + 1.0 / (n_j + a_0j - y_j - a_wj)
    zeta_i_j = delta_i_j / np.sqrt(var_delta_i_j)
    return zeta_i_j

class LogOddsRatioSmoothed(TermSignificance):

    def __init__(self, alpha_w=1, ranker=AbsoluteFrequencyRanker):
        """
		Parameters
		----------
		alpha_w : np.float
			The constant prior.
		"""
        self.alpha_w = alpha_w

    def use_metadata(self):
        self.use_metadata_ = True
        return self

    def get_name(self):
        return 'Log-Odds-Ratio w/ Add One Smoothing'

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
        return z_to_p_val(self.get_zeta_i_j(X))

    def get_p_vals_given_separate_counts(self, y_i, y_j):
        """
		Parameters
		----------
		y_i, np.array(int)
			Arrays of word counts of words occurring in positive class
		y_j, np.array(int)

		Returns
		np.array of p-values
		"""
        return z_to_p_val(self.get_zeta_i_j_given_separate_counts(y_i, y_j))

    def get_zeta_i_j_given_separate_counts(self, y_i, y_j):
        """
		Parameters
		----------
		y_i, np.array(int)
			Arrays of word counts of words occurring in positi ve class
		y_j, np.array(int)

		Returns
		-------
		np.array of z-scores
		"""
        n_i, n_j = (y_i.sum(), y_j.sum())
        delta_i_j = np.log((y_i + 1) / (1.0 + n_i - y_i)) - np.log((y_j + 1) / (1.0 + n_j - y_j))
        return delta_i_j

    def get_zeta_i_j(self, X):
        """
		Parameters
		----------
		X : np.array
			Array of word counts, shape (N, 2) where N is the vocab size.  X[:,0] is the
			positive class, while X[:,1] is the negative class. None by default

		Returns
		-------
		np.array of z-scores
		"""
        y_i, y_j = (X.T[0], X.T[1])
        return self.get_zeta_i_j_given_separate_counts(y_i, y_j)

    def get_default_score(self):
        return 0

    def get_scores(self, y_i, y_j):
        """
		Same function as get_zeta_i_j_given_separate_counts

		Parameters
		----------
		y_i, np.array(int)
			Arrays of word counts of words occurring in positive class
		y_j, np.array(int)

		Returns
		-------
		np.array of z-scores
		"""
        z_scores = self.get_zeta_i_j_given_separate_counts(y_i, y_j)
        return z_scores

def get_zeta_i_j_given_separate_counts(self, y_i, y_j):
    """
		Parameters
		----------
		y_i, np.array(int)
			Arrays of word counts of words occurring in positi ve class
		y_j, np.array(int)

		Returns
		-------
		np.array of z-scores
		"""
    n_i, n_j = (y_i.sum(), y_j.sum())
    delta_i_j = np.log((y_i + 1) / (1.0 + n_i - y_i)) - np.log((y_j + 1) / (1.0 + n_j - y_j))
    return delta_i_j

class LogOddsRatioUninformativeDirichletPrior(TermSignificance):
    """
	Implements the log-odds-ratio with an uninformative dirichlet prior from
		Monroe, B. L., Colaresi, M. P., & Quinn, K. M. (2008). Fightin' words: Lexical feature selection and evaluation for identifying the content of political conflict. Political Analysis, 16(4), 372–403.
	"""

    def __init__(self, alpha_w=0.001, ranker=AbsoluteFrequencyRanker):
        """
		Parameters
		----------
		alpha_w : np.float
			The constant prior.
		"""
        self.alpha_w = alpha_w

    def get_name(self):
        return 'Log-Odds-Ratio w/ Uninformative Prior Z-Score'

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
        return z_to_p_val(self.get_zeta_i_j(X))

    def get_p_vals_given_separate_counts(self, y_i, y_j):
        """
		Parameters
		----------
		y_i, np.array(int)
			Arrays of word counts of words occurring in positive class
		y_j, np.array(int)

		Returns
		np.array of p-values
		"""
        return z_to_p_val(self.get_zeta_i_j_given_separate_counts(y_i, y_j))

    def get_zeta_i_j_given_separate_counts(self, y_i, y_j):
        """
		Parameters
		----------
		y_i, np.array(int)
			Arrays of word counts of words occurring in positive class
		y_j, np.array(int)

		Returns
		-------
		np.array of z-scores
		"""
        yp_i = y_i + self.alpha_w
        yp_j = y_j + self.alpha_w
        np_i = np.sum(yp_i)
        np_j = np.sum(yp_j)
        delta_i_j = np.log(yp_i / (np_i - yp_i)) - np.log(yp_j / (np_j - yp_j))
        var_delta_i_j = 1.0 / yp_i + 1.0 / (np_i - yp_i) + 1.0 / yp_j + 1.0 / (np_j - yp_j)
        zeta_i_j = delta_i_j / np.sqrt(var_delta_i_j)
        return zeta_i_j

    def get_zeta_i_j(self, X):
        """
		Parameters
		----------
		X : np.array
			Array of word counts, shape (N, 2) where N is the vocab size.  X[:,0] is the
			positive class, while X[:,1] is the negative class. None by default

		Returns
		-------
		np.array of z-scores
		"""
        y_i, y_j = (X.T[0], X.T[1])
        return self.get_zeta_i_j_given_separate_counts(y_i, y_j)

    def get_default_score(self):
        return 0

    def get_p_values_from_counts(self, y_i, y_j):
        return ndtr(self.get_zeta_i_j_given_separate_counts(y_i, y_j))

    def get_scores(self, y_i, y_j):
        """
		Same function as get_zeta_i_j_given_separate_counts

		Parameters
		----------
		y_i, np.array(int)
			Arrays of word counts of words occurring in positive class
		y_j, np.array(int)

		Returns
		-------
		np.array of z-scores
		"""
        z_scores = self.get_zeta_i_j_given_separate_counts(y_i, y_j)
        return z_scores

def get_zeta_i_j_given_separate_counts(self, y_i, y_j):
    """
		Parameters
		----------
		y_i, np.array(int)
			Arrays of word counts of words occurring in positive class
		y_j, np.array(int)

		Returns
		-------
		np.array of z-scores
		"""
    yp_i = y_i + self.alpha_w
    yp_j = y_j + self.alpha_w
    np_i = np.sum(yp_i)
    np_j = np.sum(yp_j)
    delta_i_j = np.log(yp_i / (np_i - yp_i)) - np.log(yp_j / (np_j - yp_j))
    var_delta_i_j = 1.0 / yp_i + 1.0 / (np_i - yp_i) + 1.0 / yp_j + 1.0 / (np_j - yp_j)
    zeta_i_j = delta_i_j / np.sqrt(var_delta_i_j)
    return zeta_i_j

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

class RankEmbedder(CategoryEmbedderABC):

    def __init__(self, scorer_function: Optional[Callable[[np.array, np.array], np.array]]=None, term_scorer: Optional[CorpusBasedTermScorer]=None, rank_threshold: int=10, term_scorer_kwargs: Optional[Dict]=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scorer_function = RankDifference().get_scores if scorer_function is None else scorer_function
        self.term_scorer = term_scorer
        self.rank_threshold = rank_threshold
        self.term_scorer_kwargs = {} if term_scorer_kwargs is None else term_scorer_kwargs

    def embed_categories(self, corpus: TermDocMatrix, non_text: bool=False) -> np.array:
        tdf = corpus.get_freq_df(use_metadata=non_text, label_append='')
        term_freqs = tdf.sum(axis=1)
        score_df = pd.DataFrame({category: pd.Series(self.__get_scores_for_category(str(category), tdf, term_freqs, non_text, corpus), index=corpus.get_terms(use_metadata=non_text)).sort_values(ascending=False).head(self.rank_threshold) for category in corpus.get_categories()})
        return score_df.fillna(0).T.values

    def __get_scores_for_category(self, category, tdf, term_freqs, non_text, corpus):
        if self.term_scorer is not None:
            if inherits_from(self.term_scorer, 'CorpusBasedTermScorer') and type(self.term_scorer) == ABCMeta:
                scorer = self.term_scorer(corpus, **self.term_scorer_kwargs)
            else:
                scorer = self.term_scorer
            if non_text:
                scorer = scorer.use_metadata()
            scorer = scorer.set_categories(category_name=category)
            return scorer.get_scores()
        return self.scorer_function(tdf[str(category)], term_freqs - tdf[str(category)])

def embed_categories(self, corpus: TermDocMatrix, non_text: bool=False) -> np.array:
    tdf = corpus.get_freq_df(use_metadata=non_text, label_append='')
    term_freqs = tdf.sum(axis=1)
    score_df = pd.DataFrame({category: pd.Series(self.__get_scores_for_category(str(category), tdf, term_freqs, non_text, corpus), index=corpus.get_terms(use_metadata=non_text)).sort_values(ascending=False).head(self.rank_threshold) for category in corpus.get_categories()})
    return score_df.fillna(0).T.values

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

def __get_display_df(self):
    display_df = self.rank_df[lambda df: df.Rank < self.num_rows].assign(Frequency=lambda df: df.Frequency + 0.001)
    bin_boundaries = np.histogram_bin_edges(np.log(display_df.Frequency), bins=self.max_font_size - self.min_font_size)
    display_df = pd.merge(display_df.assign(FontSize=lambda df: df.Frequency.apply(np.log).apply(lambda x: bisect_left(bin_boundaries, x) + self.min_font_size)).assign(Category=lambda df: df.Category.apply(str)), pd.DataFrame({'Category': [str(c) for c in self.category_order_], 'CategoryNum': np.arange(len(self.category_order_))}), on='Category')
    return display_df

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

class JSDCompactor(BaseAssociationCompactor):

    def __init__(self, max_terms, term_ranker=AbsoluteFrequencyRanker, use_non_text_features=False, target_category: Optional[str]=None):
        self.max_terms = max_terms
        BaseAssociationCompactor.__init__(self, term_ranker=term_ranker, use_non_text_features=use_non_text_features, target_category=target_category)

    def compact(self, term_doc_matrix, verbose=False):
        rank_df = self.scorer.get_rank_df(term_doc_matrix)
        p_df = rank_df / rank_df.sum(axis=0) + 0.001
        m = p_df.sum(axis=1)

        def lg(x):
            return np.log(x) / np.log(2)
        rank_df['Score'] = m * lg(1 / m) - (p_df * lg(1 / p_df)).sum(axis=1)
        terms_to_remove = rank_df.sort_values(by='Score', ascending=False).iloc[self.max_terms:].index
        return term_doc_matrix.remove_terms(terms_to_remove, self.scorer.use_non_text_features)

def lg(x):
    return np.log(x) / np.log(2)

class AssociationCompactor(BaseAssociationCompactor):

    def __init__(self, max_terms, scorer=ScaledFScorePresetsNeg1To1, term_ranker=AbsoluteFrequencyRanker, use_non_text_features=False, include_n_most_frequent_terms=0, target_category: Optional[str]=None):
        self.max_terms = max_terms
        self.include_n_most_frequent_terms = include_n_most_frequent_terms
        BaseAssociationCompactor.__init__(self, scorer, term_ranker, use_non_text_features, target_category)

    def compact(self, term_doc_matrix, verbose=False):
        """
        Parameters
        ----------
        term_doc_matrix : TermDocMatrix
            Term document matrix object to compact
        Returns
        -------
        New term doc matrix
        """
        rank_df = self.scorer.get_rank_df(term_doc_matrix)
        optimal_rank = self._find_optimal_rank(rank_df)
        terms_to_remove = rank_df.index[np.isnan(rank_df[rank_df <= optimal_rank]).apply(lambda x: all(x), axis=1)]
        if self.include_n_most_frequent_terms > 0:
            most_frequent_terms = self.scorer.get_frequencies(term_doc_matrix).sort_values(ascending=False).index[:self.include_n_most_frequent_terms]
            terms_to_remove = set(terms_to_remove) - set(most_frequent_terms)
        compacted_term_doc_matrix = self._remove_terms(term_doc_matrix, terms_to_remove)
        if verbose:
            pass
        return compacted_term_doc_matrix

    def _get_num_terms_at_rank(self, rank_i, rank_df):
        return sum(np.isnan(rank_df[rank_df <= rank_i]).apply(lambda x: not all(x), axis=1))

    def _find_optimal_rank(self, ranks_df):
        max_rank = ranks_df.max().max()
        min_rank = 1
        last_max_rank = None
        last_min_rank = None
        while max_rank - 1 > min_rank:
            if last_max_rank is not None:
                if last_min_rank == min_rank and last_max_rank == max_rank:
                    raise Exception('Error. Potential infinite loop detected.')
            last_max_rank = max_rank
            last_min_rank = min_rank
            cur_rank = int((max_rank - min_rank) / 2) + min_rank
            num_terms = self._get_num_terms_at_rank(cur_rank, ranks_df)
            if num_terms > self.max_terms:
                max_rank = cur_rank
            elif num_terms < self.max_terms:
                min_rank = cur_rank
            else:
                return cur_rank
        return min_rank

def _get_num_terms_at_rank(self, rank_i, rank_df):
    return sum(np.isnan(rank_df[rank_df <= rank_i]).apply(lambda x: not all(x), axis=1))

def find_optimal_rank(rank_df, num_terms):
    max_rank = rank_df.max().max()
    min_rank = 1
    last_max_rank = None
    last_min_rank = None
    while max_rank - 1 > min_rank:
        if last_max_rank is not None:
            if last_min_rank == min_rank and last_max_rank == max_rank:
                raise Exception('Error. Potential infinite loop detected.')
        last_max_rank = max_rank
        last_min_rank = min_rank
        cur_rank = int((max_rank - min_rank) / 2) + min_rank
        cur_num_terms = sum(np.isnan(rank_df[rank_df <= cur_rank]).apply(lambda x: not all(x), axis=1))
        if cur_num_terms > num_terms:
            max_rank = cur_rank
        elif cur_num_terms < num_terms:
            min_rank = cur_rank
        else:
            return cur_rank
    return min_rank

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

def prob(ngram):
    if len(ngram) == 0:
        return 1
    joined_ngram = self.token_join_function(ngram)
    if joined_ngram in freqs:
        return freqs.loc[joined_ngram] / (wc[len(ngram)] - len(ngram) + 1)
    if ngram[0] in freqs.index:
        return freqs.loc[ngram[0]] / wc[1] * prob(ngram[1:])
    return backoff / wc[1] * prob(ngram[1:])

class TestTermCategoryFrequencies(TestCase):

    def setUp(self):
        df = pd.DataFrame({'democrat': {'ago': 82, 'builds on': 1, 'filled': 3, 've got': 15, 'of natural': 2, 'and forged': 1, 'have built': 2, 's army': 4, 's protected': 1, 'the most': 28, 'gas alone': 1, 'you what': 9, 'few years': 8, 'gut education': 1, 's left': 2, 'for most': 1, 'raise': 18, 'problem can': 1, 'we the': 5, 'change will': 2}, 'republican': {'ago': 39, 'builds on': 0, 'filled': 5, 've got': 16, 'of natural': 0, 'and forged': 0, 'have built': 1, 's army': 0, 's protected': 0, 'the most': 23, 'gas alone': 0, 'you what': 8, 'few years': 13, 'gut education': 0, 's left': 1, 'for most': 2, 'raise': 11, 'problem can': 0, 'we the': 5, 'change will': 0}})
        self.term_cat_freq = TermCategoryFrequencies(df)

    def test_get_num_terms(self):
        self.assertEqual(self.term_cat_freq.get_num_terms(), 20)

    def test_get_categories(self):
        self.assertEqual(self.term_cat_freq.get_categories(), ['democrat', 'republican'])

    def test_get_scaled_f_scores_vs_background(self):
        df = self.term_cat_freq.get_scaled_f_scores_vs_background()
        self.assertGreater(len(df), 20)
        self.assertEqual(sum(df.corpus > 0), 3)
        self.assertEqual(set(df.columns), {'corpus', 'background', 'Scaled f-score'})

    def test_get_term_and_background_counts(self):
        df = self.term_cat_freq.get_term_and_background_counts()
        self.assertGreater(len(df), 20)
        self.assertEqual(sum(df.corpus > 0), 3)
        self.assertEqual(set(df.columns), {'corpus', 'background'})

    def test_get_term_category_frequencies(self):
        df = self.term_cat_freq.get_term_category_frequencies(ScatterChartData())
        self.assertEqual(len(df), self.term_cat_freq.get_num_terms())
        self.assertEqual(set(df.columns), {'democrat freq', 'republican freq'})
        self.assertEqual(df.index.name, 'term')

    def test_docs(self):
        df = pd.DataFrame({'democrat': {'ago': 82, 'builds on': 1, 'filled': 3, 've got': 15, 'of natural': 2, 'and forged': 1, 'have built': 2, 's army': 4, 's protected': 1, 'the most': 28, 'gas alone': 1, 'you what': 9, 'few years': 8, 'gut education': 1, 's left': 2, 'for most': 1, 'raise': 18, 'problem can': 1, 'we the': 5, 'change will': 2}, 'republican': {'ago': 39, 'builds on': 0, 'filled': 5, 've got': 16, 'of natural': 0, 'and forged': 0, 'have built': 1, 's army': 0, 's protected': 0, 'the most': 23, 'gas alone': 0, 'you what': 8, 'few years': 13, 'gut education': 0, 's left': 1, 'for most': 2, 'raise': 11, 'problem can': 0, 'we the': 5, 'change will': 0}})
        doc_df = pd.DataFrame({'text': ['Blah blah gut education ve got filled ago', 'builds on most natural gas alone you what blah', "change will 's army the most"], 'category': ['republican', 'republican', 'democrat']})
        with self.assertRaises(AssertionError):
            TermCategoryFrequencies(df, doc_df.rename(columns={'text': 'te'}))
        with self.assertRaises(AssertionError):
            TermCategoryFrequencies(df, doc_df.rename(columns={'category': 'te'}))
        term_cat_freq = TermCategoryFrequencies(df, doc_df)
        np.testing.assert_array_equal(term_cat_freq.get_doc_indices(), [term_cat_freq.get_categories().index('republican'), term_cat_freq.get_categories().index('republican'), term_cat_freq.get_categories().index('democrat')])
        np.testing.assert_array_equal(term_cat_freq.get_texts(), ['Blah blah gut education ve got filled ago', 'builds on most natural gas alone you what blah', "change will 's army the most"])

    def test_no_docs(self):
        np.testing.assert_array_equal(self.term_cat_freq.get_doc_indices(), [])
        np.testing.assert_array_equal(self.term_cat_freq.get_texts(), [])

def test_get_scaled_f_scores_vs_background(self):
    df = self.term_cat_freq.get_scaled_f_scores_vs_background()
    self.assertGreater(len(df), 20)
    self.assertEqual(sum(df.corpus > 0), 3)
    self.assertEqual(set(df.columns), {'corpus', 'background', 'Scaled f-score'})

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

def dispersion_range(self):
    """
        range: number of parts containing a
        """
    return (self.term_part_counts > 0).sum(axis=0).A1

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

def get_score_df(self, score_append=' Score', freq_append=' Freq') -> pd.DataFrame:
    df = pd.pivot_table(self.get_rank_freq_df(), index='Term', values=['Score', 'Frequency'], columns=['Category'])
    df.columns = [category + {'Score': score_append, 'Frequency': freq_append}[metric_type] for metric_type, category in df.columns.to_flat_index()]
    return df[lambda df: list(sorted(df.columns))]

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

def __coefs_to_coef_freq_df(self, coef_df: pd.DataFrame) -> pd.DataFrame:
    coef_freq_df = pd.merge(self.corpus_.get_freq_df(use_metadata=self.non_text_), coef_df, left_index=True, right_index=True)
    return coef_freq_df

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

def __init__(self, orig_edge_df):
    self.orig_edge_df = orig_edge_df
    self.id_node_df = pd.DataFrame({'name': list(set(orig_edge_df.source.values) | set(orig_edge_df.target.values))})
    self.node_df = self.id_node_df.reset_index().set_index('name')
    self.edge_df = pd.merge(pd.merge(self.orig_edge_df, self.node_df, left_on='source', right_index=True).rename(columns={'index': 'source_id'}), self.node_df, left_on='target', right_index=True).rename(columns={'index': 'target_id'})

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

def component_to_node_list_dict(self):
    return self.id_node_df.groupby('Component')['name'].apply(list).to_dict()

class RidgeCoefficients(CoefficientBase):

    def get_coefficient_df(self, corpus, document_scores, pipeline=None):
        """

        :param corpus: TermDocMatrix, should just have unigrams
        :param document_scores: np.array, continuous value for each document score
        :return: pd.DataFrame
        """
        assert document_scores.shape == (corpus.get_num_docs(),)
        tdm = self._get_tdm(corpus)
        model = self._get_default_pipeline(pipeline)
        model.fit(X=tdm.toarray(), y=document_scores)
        df = pd.DataFrame({'Word': self._get_terms(corpus), 'Beta': model.named_steps['lr'].coef_, 'Frequency': self._get_tdm(corpus).sum(axis=0)[0].A1}).set_index('Word')
        return df

    def _get_default_pipeline(self, pipeline):
        return Pipeline([('tfidf', TfidfTransformer(sublinear_tf=True)), ('lr', RidgeCV())]) if pipeline is None else pipeline

def get_coefficient_df(self, corpus, document_scores, pipeline=None):
    """

        :param corpus: TermDocMatrix, should just have unigrams
        :param document_scores: np.array, continuous value for each document score
        :return: pd.DataFrame
        """
    assert document_scores.shape == (corpus.get_num_docs(),)
    tdm = self._get_tdm(corpus)
    model = self._get_default_pipeline(pipeline)
    model.fit(X=tdm.toarray(), y=document_scores)
    df = pd.DataFrame({'Word': self._get_terms(corpus), 'Beta': model.named_steps['lr'].coef_, 'Frequency': self._get_tdm(corpus).sum(axis=0)[0].A1}).set_index('Word')
    return df

def ungar_transform(tdm):
    pw = tdm.sum(axis=0).A1 / tdm.sum()
    tdmd = tdm.todense()
    tdmdpw = tdmd.T
    tdmdpwln = (tdmdpw / tdmdpw.sum(axis=1)).T
    print(tdmdpwln.shape, tdm.shape)
    X = 2 * np.sqrt(tdmdpwln + 3.0 / 8)
    return X.T

class UngarCoefficients(CoefficientBase):

    def get_coefficient_df(self, corpus, document_scores):
        from statsmodels.regression.linear_model import OLS
        '\n\n        :param corpus: TermDocMatrix, should just have unigrams\n        :param document_scores: np.array, continuous value for each document score\n        :return: pd.DataFrame\n        '
        assert document_scores.shape == (corpus.get_num_docs(),)
        if any((' ' in t for t in self._get_terms(corpus))):
            logging.warning('UngerCoefficients is currently designed for only unigram terms. Run corpus.get_unigram_corpus() before using this.')
        X = ungar_transform(self._get_tdm(corpus))
        model = OLS(document_scores, X.T).fit()
        df = pd.DataFrame({'Word': self._get_terms(corpus), 'Beta': model.params, 'Tstat': model.tvalues, 'Frequency': corpus.get_term_doc_mat().sum(axis=0)[0].A1}).set_index('Word')
        return df

def get_coefficient_df(self, corpus, document_scores):
    from statsmodels.regression.linear_model import OLS
    '\n\n        :param corpus: TermDocMatrix, should just have unigrams\n        :param document_scores: np.array, continuous value for each document score\n        :return: pd.DataFrame\n        '
    assert document_scores.shape == (corpus.get_num_docs(),)
    if any((' ' in t for t in self._get_terms(corpus))):
        logging.warning('UngerCoefficients is currently designed for only unigram terms. Run corpus.get_unigram_corpus() before using this.')
    X = ungar_transform(self._get_tdm(corpus))
    model = OLS(document_scores, X.T).fit()
    df = pd.DataFrame({'Word': self._get_terms(corpus), 'Beta': model.params, 'Tstat': model.tvalues, 'Frequency': corpus.get_term_doc_mat().sum(axis=0)[0].A1}).set_index('Word')
    return df

class Correlations(CoefficientBase):

    def __init__(self, use_non_text=False):
        self.set_correlation_type('pearsonr')
        CoefficientBase.__init__(self, use_non_text=use_non_text)

    def set_correlation_type(self, correlation_type: str='pearsonr') -> 'Correlations':
        assert correlation_type in ['pearsonr', 'spearmanr', 'kendalltau']
        self.correlation_type_ = correlation_type
        self.cols_ = [Correlations.get_notation_name(correlation_type=correlation_type), 'p']
        return self

    @classmethod
    def get_notation_name(cls, correlation_type):
        if correlation_type == 'pearsonr':
            return 'r'
        if correlation_type == 'spearmanr':
            return 'r'
        if correlation_type == 'kendalltau':
            return 'p'

    def __get_correlation_funct(self):
        if self.correlation_type_ == 'pearsonr':
            return pearsonr
        if self.correlation_type_ == 'spearmanr':
            return spearmanr
        if self.correlation_type_ == 'kendalltau':
            return kendalltau

    def get_correlation_df(self, corpus: TermDocMatrix, document_scores: np.array) -> pd.DataFrame:
        """

        :param corpus: TermDocMatrix, should just have unigrams
        :param document_scores: np.array, continuous value for each document score
        :return: pd.DataFrame
        """
        assert document_scores.shape == (corpus.get_num_docs(),)
        tdm = self._get_tdm(corpus)
        return pd.DataFrame([self.__get_correlation_funct()(tdm.T[i].todense().A1, document_scores) for i in range(tdm.shape[1])], columns=self.cols_).assign(Term=self._get_terms(corpus), Frequency=(tdm > 0).sum(axis=0).A1).set_index('Term').reindex(self._get_terms(corpus))

def get_correlation_df(self, corpus: TermDocMatrix, document_scores: np.array) -> pd.DataFrame:
    """

        :param corpus: TermDocMatrix, should just have unigrams
        :param document_scores: np.array, continuous value for each document score
        :return: pd.DataFrame
        """
    assert document_scores.shape == (corpus.get_num_docs(),)
    tdm = self._get_tdm(corpus)
    return pd.DataFrame([self.__get_correlation_funct()(tdm.T[i].todense().A1, document_scores) for i in range(tdm.shape[1])], columns=self.cols_).assign(Term=self._get_terms(corpus), Frequency=(tdm > 0).sum(axis=0).A1).set_index('Term').reindex(self._get_terms(corpus))

def morista_index(points):
    N = points.shape[1]
    ims = []
    for i in range(1, N):
        bins, _, _ = np.histogram2d(points[0], points[1], i)
        Q = len(bins)
        I_M = Q * np.sum(np.ravel(bins) * (np.ravel(bins) - 1)) / (N * (N - 1))
        ims.append([i, I_M])
    return np.array(ims).T[1].max()

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

def __init__(self, min_radius=0, max_radius=np.sqrt(2)):
    self.min_radius = min_radius
    self.max_radius = max_radius

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

def __init__(self, max_distance=np.sqrt(2)):
    self.max_distance = max_distance

class MeanMorisitaIndexEvaluator(CategoryProjectionEvaluator):

    def __init__(self, num_bin_range=None):
        self.num_bin_range = num_bin_range if num_bin_range is not None else [10, 1000]

    def evaluate(self, category_projection):
        assert issubclass(type(category_projection), CategoryProjectionBase)
        proj = category_projection.projection[:, [category_projection.x_dim, category_projection.y_dim]]
        scaled_proj = np.array([stretch_0_to_1(proj.T[0]), stretch_0_to_1(proj.T[1])]).T
        morista_sum = 0
        N = scaled_proj.shape[0]
        for i in range(self.num_bin_range[0], self.num_bin_range[1]):
            bins, _, _ = np.histogram2d(scaled_proj.T[0], scaled_proj.T[1], i)
            Q = len(bins)
            morista_sum += Q * np.sum(np.ravel(bins) * (np.ravel(bins) - 1)) / (N * (N - 1))
        return morista_sum / (self.num_bin_range[1] - self.num_bin_range[0])

def evaluate(self, category_projection):
    assert issubclass(type(category_projection), CategoryProjectionBase)
    proj = category_projection.projection[:, [category_projection.x_dim, category_projection.y_dim]]
    scaled_proj = np.array([stretch_0_to_1(proj.T[0]), stretch_0_to_1(proj.T[1])]).T
    morista_sum = 0
    N = scaled_proj.shape[0]
    for i in range(self.num_bin_range[0], self.num_bin_range[1]):
        bins, _, _ = np.histogram2d(scaled_proj.T[0], scaled_proj.T[1], i)
        Q = len(bins)
        morista_sum += Q * np.sum(np.ravel(bins) * (np.ravel(bins) - 1)) / (N * (N - 1))
    return morista_sum / (self.num_bin_range[1] - self.num_bin_range[0])

class LengthNormalizer(BaseEstimator, TransformerMixin):

    def fit_transform(self, X, y=None, **fit_params):
        return X - X.sum(axis=0)

def fit_transform(self, X, y=None, **fit_params):
    return X - X.sum(axis=0)

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

def _get_raw_category_counts(self, category_corpus):
    return category_corpus.get_freq_df(label_append='')

class SentencesForTopicModeling(object):
    """
	Creates a topic model from a set of key terms based on sentence level co-occurrence.
	"""

    def __init__(self, corpus, use_offsets=False):
        """

		Parameters
		----------
		corpus
		use_offsets

		"""
        assert isinstance(corpus, ParsedCorpus)
        self.corpus = corpus
        self.use_offsets = use_offsets
        if not use_offsets:
            self.termidxstore = corpus._term_idx_store
            matfact = CSRMatrixFactory()
            self.doclabs = []
            self.sentlabs = []
            self.sentdocs = []
            senti = 0
            for doci, doc in enumerate(corpus.get_parsed_docs()):
                for sent in doc.sents:
                    validsent = False
                    for t in sent:
                        try:
                            termi = self.termidxstore.getidxstrict(t.lower_)
                        except:
                            continue
                        if validsent is False:
                            senti += 1
                            self.sentlabs.append(corpus._y[doci])
                            self.sentdocs.append(doci)
                            validsent = True
                        matfact[senti, termi] = 1
            self.sentX = matfact.get_csr_matrix().astype(bool)
        else:
            self.termidxstore = corpus._metadata_idx_store
            doc_sent_offsets = [pd.IntervalIndex.from_breaks([sent[0].idx for sent in doc.sents] + [len(str(doc))], closed='left') for doc_i, doc in enumerate(corpus.get_parsed_docs())]
            doc_sent_count = []
            tally = 0
            for doc_offsets in doc_sent_offsets:
                doc_sent_count.append(tally)
                tally += len(doc_offsets)
            matfact = CSRMatrixFactory()
            for term, term_offsets in corpus.get_offsets().items():
                term_index = corpus.get_metadata_index(term)
                for doc_i, offsets in term_offsets.items():
                    for offset in offsets:
                        doc_sent_i = doc_sent_offsets[doc_i].get_loc(offset[0]) + doc_sent_count[doc_i]
                        matfact[doc_sent_i, term_index] = 1
            self.sentX = matfact.get_csr_matrix()

    def get_sentence_word_mat(self):
        return self.sentX.astype(np.double).tocoo()

    def get_topic_weights_df(self, pipe=None) -> pd.DataFrame:
        pipe = self._fit_model(pipe)
        return pd.DataFrame(pipe._final_estimator.components_.T, index=self.corpus.get_terms(use_metadata=self.use_offsets))

    def get_topics_from_model(self, pipe=None, num_terms_per_topic=10) -> dict:
        """

		Parameters
		----------
		pipe : Pipeline
			For example, `Pipeline([
				('tfidf', TfidfTransformer(sublinear_tf=True)),
				('nmf', (NMF(n_components=30, l1_ratio=.5, random_state=0)))])`
			The last transformer must populate a `components_` attribute when finished.
		num_terms_per_topic : int

		Returns
		-------
		dict: {term: [term1, ...], ...}
		"""
        pipe = self._fit_model(pipe)
        topic_model = {}
        for topic_idx, topic in enumerate(pipe._final_estimator.components_):
            term_list = [self.termidxstore.getval(i) for i in topic.argsort()[:-num_terms_per_topic - 1:-1] if topic[i] > 0]
            if len(term_list) > 0:
                topic_model['%s. %s' % (topic_idx, term_list[0])] = term_list
            else:
                Warning('Topic %s has no terms with scores > 0. Omitting.' % topic_idx)
        return topic_model

    def _fit_model(self, pipe):
        if pipe is None:
            pipe = Pipeline([('tfidf', TfidfTransformer(sublinear_tf=True)), ('nmf', NMF(n_components=30, l1_ratio=0.5, random_state=0))])
        pipe.fit_transform(self.sentX)
        return pipe

    def get_topics_from_terms(self, terms=None, num_terms_per_topic=10, scorer=RankDifference()):
        """
		Parameters
		----------
		terms : list or None
			If terms is list, make these the seed terms for the topoics
			If none, use the first 30 terms in get_scaled_f_scores_vs_background
		num_terms_per_topic : int, default 10
			Use this many terms per topic
		scorer : TermScorer
			Implements get_scores, default is RankDifferce, which tends to work best

		Returns
		-------
		dict: {term: [term1, ...], ...}
		"""
        topic_model = {}
        if terms is None:
            terms = self.corpus.get_scaled_f_scores_vs_background().index[:30]
        for term in terms:
            termidx = self.termidxstore.getidxstrict(term)
            labels = self.sentX[:, termidx].astype(bool).todense().A1
            poscnts = self.sentX[labels, :].astype(bool).sum(axis=0).A1
            negcnts = self.sentX[~labels, :].astype(bool).sum(axis=0).A1
            scores = scorer.get_scores(poscnts, negcnts)
            topic_model[term] = [self.termidxstore.getval(i) for i in np.argsort(-scores)[:num_terms_per_topic]]
        return topic_model

def get_topics_from_terms(self, terms=None, num_terms_per_topic=10, scorer=RankDifference()):
    """
		Parameters
		----------
		terms : list or None
			If terms is list, make these the seed terms for the topoics
			If none, use the first 30 terms in get_scaled_f_scores_vs_background
		num_terms_per_topic : int, default 10
			Use this many terms per topic
		scorer : TermScorer
			Implements get_scores, default is RankDifferce, which tends to work best

		Returns
		-------
		dict: {term: [term1, ...], ...}
		"""
    topic_model = {}
    if terms is None:
        terms = self.corpus.get_scaled_f_scores_vs_background().index[:30]
    for term in terms:
        termidx = self.termidxstore.getidxstrict(term)
        labels = self.sentX[:, termidx].astype(bool).todense().A1
        poscnts = self.sentX[labels, :].astype(bool).sum(axis=0).A1
        negcnts = self.sentX[~labels, :].astype(bool).sum(axis=0).A1
        scores = scorer.get_scores(poscnts, negcnts)
        topic_model[term] = [self.termidxstore.getval(i) for i in np.argsort(-scores)[:num_terms_per_topic]]
    return topic_model

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

class LogRelativeRisk(CorpusBasedTermScorer):
    """
    LogRatio from Hardie 2014

    Stephanie Evert. 2023. Measuring Keyness. https://osf.io/x8z9n.

    """

    def _set_scorer_args(self, **kwargs):
        self.lambda_ = kwargs.get('lambda_', 0.01)

    def get_scores(self, *args) -> pd.Series:
        """
        In this case, args aren't used, since this information is taken
        directly from the corpus categories.

        Returns
        -------
        np.array, scores
        """
        cat_X, ncat_X = self._get_cat_and_ncat(self._get_X())
        N1 = self._get_cat_size()
        N2 = self._get_ncat_size()
        if len(args) == 0:
            f1 = cat_X.sum(axis=0).A1
            f2 = ncat_X.sum(axis=0).A1
        else:
            f1, f2 = self.__get_f1_f2_from_args(args)
        res = np.log((f1 + self.lambda_) / N1) / np.log(2) - np.log((f2 + self.lambda_) / N2) / np.log(2)
        return pd.Series(res, index=self._get_terms())

    def get_name(self):
        return 'Log Relative Risk'

def get_scores(self, *args) -> pd.Series:
    """
        In this case, args aren't used, since this information is taken
        directly from the corpus categories.

        Returns
        -------
        np.array, scores
        """
    cat_X, ncat_X = self._get_cat_and_ncat(self._get_X())
    N1 = self._get_cat_size()
    N2 = self._get_ncat_size()
    if len(args) == 0:
        f1 = cat_X.sum(axis=0).A1
        f2 = ncat_X.sum(axis=0).A1
    else:
        f1, f2 = self.__get_f1_f2_from_args(args)
    res = np.log((f1 + self.lambda_) / N1) / np.log(2) - np.log((f2 + self.lambda_) / N2) / np.log(2)
    return pd.Series(res, index=self._get_terms())

class LogOddsRatio(CorpusBasedTermScorer):

    def _set_scorer_args(self, **kwargs):
        self.constant = kwargs.get('constant', 0.01)

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
        y_i = self.tdf_['cat']
        y_j = self.tdf_['ncat']
        n_i, n_j = (y_i.sum(), y_j.sum())
        delta_i_j = np.log((y_i + self.constant) / (self.constant + n_i - y_i)) - np.log((y_j + self.constant) / (self.constant + n_j - y_j))
        return delta_i_j

    def get_name(self):
        return 'Smoothed Log Odds Ratio'

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
    y_i = self.tdf_['cat']
    y_j = self.tdf_['ncat']
    n_i, n_j = (y_i.sum(), y_j.sum())
    delta_i_j = np.log((y_i + self.constant) / (self.constant + n_i - y_i)) - np.log((y_j + self.constant) / (self.constant + n_j - y_j))
    return delta_i_j

def log_odds_ratio_with_prior_from_counts(a: pd.Series, b: pd.Series) -> pd.Series:
    lor = np.log(a / (np.sum(a) - a)) - np.log(b / (np.sum(b) - b))
    lorstd = 1.0 / a + 1.0 / (np.sum(a) - a) + 1.0 / b + 1.0 / (np.sum(b) - b)
    log_odds_ratio_with_prior = lor / np.sqrt(lorstd)
    return log_odds_ratio_with_prior

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

def get_doc_sizes(self) -> np.array:
    if self._doc_sizes is None:
        return self._get_X().sum(axis=1)
    return self._doc_sizes

def _get_cat_size(self) -> float:
    return self.get_doc_sizes()[self._get_cat_x_row_mask()].sum()

def _get_ncat_size(self) -> float:
    return self.get_doc_sizes()[self._get_ncat_x_row_mask()].sum()

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

class RankSum(CorpusBasedTermScorer):
    """
    Wilcoxon Rank Sum (inspired by https://github.com/Zeta-and-Company/pydistinto/blob/main/scripts/measures/wilcoxon_ranksum.py)
    Pseudo counts of 0.0001 are added to each document.
    """

    def _set_scorer_args(self, **args):
        self.verbose = args.get('verbose', False)

    def get_scores(self, *args):
        """
        In this case, args aren't used, since this information is taken
        directly from the corpus categories.

        Returns
        -------
        np.array, scores
        """
        return self.get_score_df().Score

    def get_score_df(self, *args):
        """
        In this case, args aren't used, since this information is taken
        directly from the corpus categories.

        Returns
        -------
        np.array, scores
        """
        X = self._get_X() > 0
        cat_X, ncat_X = self._get_cat_and_ncat(X)
        cat_X = cat_X.todense().T
        cat_X = cat_X / cat_X.sum(axis=0)
        ncat_X = ncat_X.todense().T
        ncat_X = ncat_X / ncat_X.sum(axis=0)
        it = range(cat_X.shape[0])
        if self.verbose:
            from tqdm.auto import tqdm
            it = tqdm(range(cat_X.shape[0]), total=cat_X.shape[0])
        scores = []
        for i in it:
            a = cat_X[i].A1 + [0.0001]
            b = ncat_X[i].A1 + [0.0001]
            stat = mannwhitneyu(a, b)
            scores.append([stat.statistic, stat.pvalue, a.sum(), b.sum()])
        return pd.DataFrame(scores, columns=['Score', 'PValue', 'Base', 'Counter']).assign(Term=self.corpus_.get_terms(), Z=lambda df: norm.ppf(df.PValue)).set_index('Term')

    def get_name(self):
        return 'Man-Whitney U'

def get_score_df(self, *args):
    """
        In this case, args aren't used, since this information is taken
        directly from the corpus categories.

        Returns
        -------
        np.array, scores
        """
    X = self._get_X() > 0
    cat_X, ncat_X = self._get_cat_and_ncat(X)
    cat_X = cat_X.todense().T
    cat_X = cat_X / cat_X.sum(axis=0)
    ncat_X = ncat_X.todense().T
    ncat_X = ncat_X / ncat_X.sum(axis=0)
    it = range(cat_X.shape[0])
    if self.verbose:
        from tqdm.auto import tqdm
        it = tqdm(range(cat_X.shape[0]), total=cat_X.shape[0])
    scores = []
    for i in it:
        a = cat_X[i].A1 + [0.0001]
        b = ncat_X[i].A1 + [0.0001]
        stat = mannwhitneyu(a, b)
        scores.append([stat.statistic, stat.pvalue, a.sum(), b.sum()])
    return pd.DataFrame(scores, columns=['Score', 'PValue', 'Base', 'Counter']).assign(Term=self.corpus_.get_terms(), Z=lambda df: norm.ppf(df.PValue)).set_index('Term')

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

class ZScores(CorpusBasedTermScorer):
    """
	Z-scores from Welch's t-test

	term_scorer = (ZScores(corpus).set_categories('Positive', ['Negative'], ['Plot']))

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
	file_name = 'rotten_fresh_fre.html'
	open(file_name, 'wb').write(html.encode('utf-8'))
	IFrame(src=file_name, width=1300, height=700)
	"""

    def _set_scorer_args(self, **kwargs):
        pass

    def get_scores(self, *args):
        return pd.Series(self.get_t_statistics()[0], index=self._get_index())

    def get_name(self):
        return "Z-Score from Welch's T-Test"

def get_scores(self, *args):
    return pd.Series(self.get_t_statistics()[0], index=self._get_index())

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
def _balance_scores(cat_scores, not_cat_scores):
    scores = np.zeros(len(cat_scores))
    scores[cat_scores < not_cat_scores] = np.sqrt(2) - cat_scores[cat_scores < not_cat_scores]
    scores[not_cat_scores < cat_scores] = -(np.sqrt(2) - not_cat_scores[not_cat_scores < cat_scores])
    return (scores / np.sqrt(2) + 1.0) / 2

def whole_corpus_productivity_scores(tdm: TermDocMatrixWithoutCategories) -> pd.DataFrame:
    term_freqs = pd.Series(tdm.get_term_freqs(), index=tdm.get_terms())
    ngrams_mask = [' ' in x for x in tdm.get_terms()]
    data = []
    for ngram, ngram_freq in term_freqs[ngrams_mask].items():
        for term in ngram.split():
            try:
                tdm.get_term_index(term)
            except KeyError:
                continue
            data.append([tdm.get_term_index(term), ngram_freq])
    ngram_freq_df = pd.DataFrame(data, columns=['TermIndex', 'NgramFreq'])
    productivity_df = pd.merge(ngram_freq_df, ngram_freq_df.groupby(['TermIndex']).sum().rename(columns={'NgramFreq': 'TermCatFreq'}).reset_index(), on=['TermIndex']).assign(P=lambda df: df.NgramFreq / df.TermCatFreq).dropna().groupby(['TermIndex']).apply(lambda df: -np.sum(df.P * np.log(df.P) / np.log(2))).reset_index().rename(columns={0: 'Productivity'}).assign(Term=lambda df: np.array(tdm.get_terms())[df.TermIndex], Frequency=lambda df: term_freqs.loc[df.Term.values].values)[lambda df: [c for c in df.columns if c != 'TermIndex']].set_index('Term')
    return productivity_df

class ProductivityScorer(CorpusBasedTermScorer):
    """
    Citation: Anne-Kathrin Schumann. 2016. Brave new world: Uncovering topical dynamics in the ACL Anthology
    reference corpus using term life cycle information. In Proceedings of the 10th SIGHUM Workshop on Language
    Technology for Cultural Heritage, Social Sciences, and Humanities, pages 1–11, Berlin, Germany. Association
    for Computational Linguistics.

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
    """

    def _set_scorer_args(self, **kwargs):
        pass

    def get_scores(self, *args):
        return self.get_score_df()['Productivity']

    def get_score_df(self) -> pd.DataFrame:
        """
        Computes Schumann (2016) term productivity scores. Requires corpus to have both unigrams and ngrams. Corpus
        should not be compacted.
        """
        term_freq_df = self.corpus_.get_term_freq_df('')
        ngrams_mask = [' ' in x for x in self.corpus_.get_terms()]
        data = []
        for ngram, ngram_freqs in term_freq_df[ngrams_mask].iterrows():
            for term in ngram.split():
                term_index = self.corpus_.get_term_index(term)
                for category_index, ngram_freq in enumerate(ngram_freqs):
                    data.append([term_index, category_index, ngram_freq])
        ngram_freq_df = pd.DataFrame(data, columns=['TermIndex', 'CategoryIndex', 'NgramFreq'])
        productivity_df = pd.merge(ngram_freq_df, ngram_freq_df.groupby(['TermIndex', 'CategoryIndex']).sum().rename(columns={'NgramFreq': 'TermCatFreq'}).reset_index(), on=['TermIndex', 'CategoryIndex']).assign(P=lambda df: df.NgramFreq / df.TermCatFreq).dropna().groupby(['TermIndex', 'CategoryIndex']).apply(lambda df: -np.sum(df.P * np.log(df.P) / np.log(2))).reset_index().rename(columns={0: 'Productivity'})
        return pd.pivot_table(productivity_df.assign(Term=lambda df: np.array(self.corpus_.get_terms())[df.TermIndex], Category=lambda df: np.array(self.corpus_.get_categories())[df.CategoryIndex]), index='Term', columns='Category', values='Productivity').fillna(0).assign(Delta=lambda df: df[self.category_name] - df[self.not_category_names].mean(axis=1))

    def get_scores(self, *args) -> pd.Series:
        return self.get_score_df()['Delta']

    def get_name(self) -> str:
        return 'Delta Productivity'

def get_score_df(self) -> pd.DataFrame:
    """
        Computes Schumann (2016) term productivity scores. Requires corpus to have both unigrams and ngrams. Corpus
        should not be compacted.
        """
    term_freq_df = self.corpus_.get_term_freq_df('')
    ngrams_mask = [' ' in x for x in self.corpus_.get_terms()]
    data = []
    for ngram, ngram_freqs in term_freq_df[ngrams_mask].iterrows():
        for term in ngram.split():
            term_index = self.corpus_.get_term_index(term)
            for category_index, ngram_freq in enumerate(ngram_freqs):
                data.append([term_index, category_index, ngram_freq])
    ngram_freq_df = pd.DataFrame(data, columns=['TermIndex', 'CategoryIndex', 'NgramFreq'])
    productivity_df = pd.merge(ngram_freq_df, ngram_freq_df.groupby(['TermIndex', 'CategoryIndex']).sum().rename(columns={'NgramFreq': 'TermCatFreq'}).reset_index(), on=['TermIndex', 'CategoryIndex']).assign(P=lambda df: df.NgramFreq / df.TermCatFreq).dropna().groupby(['TermIndex', 'CategoryIndex']).apply(lambda df: -np.sum(df.P * np.log(df.P) / np.log(2))).reset_index().rename(columns={0: 'Productivity'})
    return pd.pivot_table(productivity_df.assign(Term=lambda df: np.array(self.corpus_.get_terms())[df.TermIndex], Category=lambda df: np.array(self.corpus_.get_categories())[df.CategoryIndex]), index='Term', columns='Category', values='Productivity').fillna(0).assign(Delta=lambda df: df[self.category_name] - df[self.not_category_names].mean(axis=1))

def g2_term(O, E):
    res = O.astype(np.float64) * (np.log(O) - np.log(E))
    res[O == 0] = 0
    return res

def qchisq(alpha: np.array, df: int) -> np.array:
    return chi2.ppf(1 - alpha, df=df)

class G2(CorpusBasedTermScorer):
    """
    G^2 (log likelihood ratio)s from (Rayson and Garside 2000)

    A direct translation of the R function from (Evert 2023)
    Stephanie Evert. 2023. Measuring Keyness. https://osf.io/x8z9n.
    G2.term <- function (O, E) {
      res <- O * log(O / E)
      res[O == 0] <- 0
      res
    }

    G2 <- function (f1, f2, N1, N2, alpha=NULL, correct=TRUE) {
      stopifnot(length(f1) == length(f2))

      ## observed and expected contingency tables
      N <- N1 + N2
      R1 <- f1 + f2
      O11 <- f1;      E11 <- R1 * N1 / N
      O12 <- f2;      E12 <- R1 * N2 / N
      O21 <- N1 - f1; E21 <- N1 - E11
      O22 <- N2 - f2; E22 <- N2 - E12

      ## log-likelihood statistic (simplest formula)
      G2 <- 2 * (G2.term(O11, E11) + G2.term(O12, E12) + G2.term(O21, E21) + G2.term(O22, E22))
      res <- sign(O11 - E11) * G2 # set sign to distinguish positive vs. negative keywords

      ## weed out non-significant items if alpha is specified
      if (!is.null(alpha)) {
        if (correct) alpha <- alpha / length(f1)
        theta <- qchisq(alpha, df=1, lower.tail=FALSE)
        res[G2 < theta] <- 0 # set to 0 if not significant at level alpha
      }

      res
    }
    """

    def _set_scorer_args(self, **kwargs):
        self.alpha_ = kwargs.get('alpha', None)
        self.correct_ = kwargs.get('correct', True)

    def get_score_df(self, label_append=''):
        N1, N2, f1, f2 = self._get_ns_and_fs(())
        gsquare, res = self._get_g2_and_res(N1, N2, f1, f2)
        df = pd.DataFrame({'G2': gsquare, 'Score': res, 'P': chi2.sf(gsquare, df=1)})
        return df.assign(CorrectedP=lambda df: fdrcorrection(pvals=df.P.values, alpha=self.alpha_, method='indep')[1])

    def get_scores(self, *args) -> pd.Series:
        N1, N2, f1, f2 = self._get_ns_and_fs(args)
        gsquare, res = self._get_g2_and_res(N1, N2, f1, f2)
        if self.alpha_ is not None:
            alpha = self.alpha_
            if self.correct_:
                alpha = alpha / len(f1)
            theta = qchisq(alpha, df=1)
            res[gsquare < theta] = 0
        return pd.Series(res, index=self._get_terms())

    def _get_g2_and_res(self, N1, N2, f1, f2):
        N = N1 + N2
        R1 = f1 + f2
        E11, E12, E21, E22, O11, O12, O21, O22 = self.__get_contingency_table(N, N1, N2, R1, f1, f2)
        gsquare = 2 * (g2_term(O11, E11) + g2_term(O12, E12) + g2_term(O21, E21) + g2_term(O22, E22))
        res = sign(O11 - E11) * gsquare
        return (gsquare, res)

    def __get_contingency_table(self, N, N1, N2, R1, f1, f2):
        O11 = f1
        E11 = R1 * N1 / N
        O12 = f2
        E12 = R1 * N2 / N
        O21 = N1 - f1
        E21 = N1 - E11
        O22 = N2 - f2
        E22 = N2 - E12
        return (E11, E12, E21, E22, O11, O12, O21, O22)

    def _get_ns_and_fs(self, args):
        cat_X, ncat_X = self._get_cat_and_ncat(self._get_X())
        N1 = self._get_cat_size()
        N2 = self._get_ncat_size()
        if len(args) == 0:
            f1 = cat_X.sum(axis=0).A1
            f2 = ncat_X.sum(axis=0).A1
        else:
            f1, f2 = self.__get_f1_f2_from_args(args)
        f1 = np.array(f1).astype(np.float64)
        f2 = np.array(f2).astype(np.float64)
        return (N1, N2, f1, f2)

    def get_name(self):
        return 'G2'

def get_score_df(self, label_append=''):
    N1, N2, f1, f2 = self._get_ns_and_fs(())
    gsquare, res = self._get_g2_and_res(N1, N2, f1, f2)
    df = pd.DataFrame({'G2': gsquare, 'Score': res, 'P': chi2.sf(gsquare, df=1)})
    return df.assign(CorrectedP=lambda df: fdrcorrection(pvals=df.P.values, alpha=self.alpha_, method='indep')[1])

def get_scores(self, *args) -> pd.Series:
    N1, N2, f1, f2 = self._get_ns_and_fs(args)
    gsquare, res = self._get_g2_and_res(N1, N2, f1, f2)
    if self.alpha_ is not None:
        alpha = self.alpha_
        if self.correct_:
            alpha = alpha / len(f1)
        theta = qchisq(alpha, df=1)
        res[gsquare < theta] = 0
    return pd.Series(res, index=self._get_terms())

def _get_ns_and_fs(self, args):
    cat_X, ncat_X = self._get_cat_and_ncat(self._get_X())
    N1 = self._get_cat_size()
    N2 = self._get_ncat_size()
    if len(args) == 0:
        f1 = cat_X.sum(axis=0).A1
        f2 = ncat_X.sum(axis=0).A1
    else:
        f1, f2 = self.__get_f1_f2_from_args(args)
    f1 = np.array(f1).astype(np.float64)
    f2 = np.array(f2).astype(np.float64)
    return (N1, N2, f1, f2)

class ScaledFScorePresets(TermScorer):

    def __init__(self, scaler_algo=DEFAULT_SCALER_ALGO, beta=DEFAULT_BETA, one_to_neg_one=False, priors=None, use_score_difference=False):
        self.scaler_algo_ = scaler_algo
        self.beta_ = beta
        self.one_to_neg_one_ = one_to_neg_one
        self.priors_ = priors
        self.use_score_difference_ = use_score_difference
        assert self.beta_ > 0

    def get_name(self):
        return 'Scaled F-Score'

    def get_default_score(self):
        if self.one_to_neg_one_:
            return 0
        return 0.5

    def get_scores(self, cat_word_counts, not_cat_word_counts):
        """
        Parameters
        ----------
        cat_word_counts : np.array
            category counts
        not_cat_word_counts : np.array
            not category counts

        Returns
        -------
        np.array
            scores
        """
        cat_scores = self.get_scores_for_category(cat_word_counts, not_cat_word_counts)
        not_cat_scores = self.get_scores_for_category(not_cat_word_counts, cat_word_counts)
        if self.use_score_difference_:
            scores = (cat_scores - not_cat_scores + 1.0) / 2.0
        else:
            scores = ScoreBalancer.balance_scores(cat_scores, not_cat_scores)
        if self.one_to_neg_one_:
            return 2 * scores - 1
        else:
            return scores

    def get_scores_for_category(self, cat_word_counts, not_cat_word_counts):
        """
        Parameters
        ----------
        cat_word_counts : np.array
            category counts
        not_cat_word_counts : np.array
            not category counts

        Returns
        -------
        np.array
            scores
        """
        beta = self.beta_
        assert len(cat_word_counts) == len(not_cat_word_counts)
        old_cat_word_counts = None
        if type(cat_word_counts) == pd.Series:
            assert all(cat_word_counts.index == not_cat_word_counts.index)
            old_cat_word_counts = cat_word_counts
            cat_word_counts = cat_word_counts.values
        if type(not_cat_word_counts) == pd.Series:
            not_cat_word_counts = not_cat_word_counts.values
        if self.priors_ is not None:
            p = self.priors_
            assert len(p) == len(cat_word_counts)
            precision = (cat_word_counts + p * 1.0) / (cat_word_counts + not_cat_word_counts + 2 * p)
            recall = (cat_word_counts + p) * 1.0 / (cat_word_counts.sum() + p.sum())
        else:
            precision = cat_word_counts * 1.0 / (cat_word_counts + not_cat_word_counts)
            recall = cat_word_counts * 1.0 / cat_word_counts.sum()
        precision_normcdf = ScaledFScore._safe_scaler(self.scaler_algo_, precision)
        recall_normcdf = ScaledFScore._safe_scaler(self.scaler_algo_, recall)
        scores = self._weighted_h_mean(precision_normcdf, recall_normcdf)
        scores[np.isnan(scores)] = 0.0
        if old_cat_word_counts is not None:
            return pd.Series(scores, index=old_cat_word_counts.index)
        return scores

    def _weighted_h_mean(self, precision_normcdf, recall_normcdf):
        scores = (1 + self.beta_ ** 2) * (precision_normcdf * recall_normcdf) / (self.beta_ ** 2 * precision_normcdf + recall_normcdf)
        return scores

def get_scores_for_category(self, cat_word_counts, not_cat_word_counts):
    """
        Parameters
        ----------
        cat_word_counts : np.array
            category counts
        not_cat_word_counts : np.array
            not category counts

        Returns
        -------
        np.array
            scores
        """
    beta = self.beta_
    assert len(cat_word_counts) == len(not_cat_word_counts)
    old_cat_word_counts = None
    if type(cat_word_counts) == pd.Series:
        assert all(cat_word_counts.index == not_cat_word_counts.index)
        old_cat_word_counts = cat_word_counts
        cat_word_counts = cat_word_counts.values
    if type(not_cat_word_counts) == pd.Series:
        not_cat_word_counts = not_cat_word_counts.values
    if self.priors_ is not None:
        p = self.priors_
        assert len(p) == len(cat_word_counts)
        precision = (cat_word_counts + p * 1.0) / (cat_word_counts + not_cat_word_counts + 2 * p)
        recall = (cat_word_counts + p) * 1.0 / (cat_word_counts.sum() + p.sum())
    else:
        precision = cat_word_counts * 1.0 / (cat_word_counts + not_cat_word_counts)
        recall = cat_word_counts * 1.0 / cat_word_counts.sum()
    precision_normcdf = ScaledFScore._safe_scaler(self.scaler_algo_, precision)
    recall_normcdf = ScaledFScore._safe_scaler(self.scaler_algo_, recall)
    scores = self._weighted_h_mean(precision_normcdf, recall_normcdf)
    scores[np.isnan(scores)] = 0.0
    if old_cat_word_counts is not None:
        return pd.Series(scores, index=old_cat_word_counts.index)
    return scores

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

def apply_prior(self, c):
    n = np.sum(c)
    prior_scale = np.sum(c) * self.alpha * 1.0 / np.sum(self.prior)
    return c + self.prior * prior_scale

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
def _safe_scaler(algo, ar):
    if algo == 'none':
        return ar
    scaled_ar = ScaledFScore._get_scaler_function(algo)(ar)
    if np.isnan(scaled_ar).any():
        return ScaledFScore._get_scaler_function('percentile')(scaled_ar)
    return scaled_ar

class BNSScorer(CorpusBasedTermScorer):

    def _set_scorer_args(self, **kwargs):
        self.alpha = kwargs.get('alpha', BNS_ALPHA_DEFAULT)
        if self.alpha is None:
            self.alpha = 1.0 / pd.Series(self.corpus_.get_category_ids()).value_counts().min()
        assert 0 <= self.alpha <= 1

    def get_score_df(self):
        data = {}
        X = self._get_X() > 0
        y = self.corpus_.get_category_ids()
        for cat_i, cat in enumerate(self.corpus_.get_categories()):
            n_cat_is = [x for x in range(len(self.corpus_.get_categories())) if x != cat_i]
            tp, fp, pos, neg, tpr, fpr, invn_tpr, invn_fpr = self._get_bns_score_for_category_index(cat_i, n_cat_is, X, y)
            data[cat + ' BNS'] = invn_tpr - invn_fpr
            data[cat + ' TP'] = tp
            data[cat + ' FP'] = fp
            data[cat + ' POS'] = pos
            data[cat + ' NEG'] = neg
            data[cat + ' TPR'] = tpr
            data[cat + ' FPR'] = fpr
            data[cat + ' INTPR'] = invn_tpr
            data[cat + ' INFPR'] = invn_fpr
        return pd.DataFrame(data, index=self._get_index())

    def _get_bns_score_for_category_index(self, cat_i, not_cat_is, X, y):
        cat_mask = y == cat_i
        not_cat_mask = np.logical_or.reduce([y == i for i in not_cat_is])
        tp = X[cat_mask].sum(axis=0).A1
        fp = X[not_cat_mask].sum(axis=0).A1
        pos = np.sum(cat_mask)
        neg = np.sum(not_cat_mask)
        tpr = tp / pos
        fpr = fp / neg
        invn_tpr = self._invnorm(tpr)
        invn_fpr = self._invnorm(fpr)
        return (tp, fp, pos, neg, tpr, fpr, invn_tpr, invn_fpr)

    def _invnorm(self, scores: np.array) -> np.array:
        scores[scores < self.alpha] = self.alpha
        scores[scores > 1 - self.alpha] = 1 - self.alpha
        return norm.ppf(scores)

    def get_scores(self, *args) -> pd.Series:
        categories = [str(c) for c in self.corpus_.get_categories()]
        tp, fp, pos, neg, tpr, fpr, invn_tpr, invn_fpr = self._get_bns_score_for_category_index(cat_i=categories.index(str(self.category_name)), not_cat_is=[categories.index(str(c)) for c in self.not_category_names], X=self._get_X() > 0, y=self.corpus_._y)
        return pd.Series(invn_tpr - invn_fpr, index=self._get_index())

    def get_name(self):
        return f'Bi-normal separation (alpha={self.alpha})'

def _set_scorer_args(self, **kwargs):
    self.alpha = kwargs.get('alpha', BNS_ALPHA_DEFAULT)
    if self.alpha is None:
        self.alpha = 1.0 / pd.Series(self.corpus_.get_category_ids()).value_counts().min()
    assert 0 <= self.alpha <= 1

def get_score_df(self):
    data = {}
    X = self._get_X() > 0
    y = self.corpus_.get_category_ids()
    for cat_i, cat in enumerate(self.corpus_.get_categories()):
        n_cat_is = [x for x in range(len(self.corpus_.get_categories())) if x != cat_i]
        tp, fp, pos, neg, tpr, fpr, invn_tpr, invn_fpr = self._get_bns_score_for_category_index(cat_i, n_cat_is, X, y)
        data[cat + ' BNS'] = invn_tpr - invn_fpr
        data[cat + ' TP'] = tp
        data[cat + ' FP'] = fp
        data[cat + ' POS'] = pos
        data[cat + ' NEG'] = neg
        data[cat + ' TPR'] = tpr
        data[cat + ' FPR'] = fpr
        data[cat + ' INTPR'] = invn_tpr
        data[cat + ' INFPR'] = invn_fpr
    return pd.DataFrame(data, index=self._get_index())

def _invnorm(self, scores: np.array) -> np.array:
    scores[scores < self.alpha] = self.alpha
    scores[scores > 1 - self.alpha] = 1 - self.alpha
    return norm.ppf(scores)

def get_scores(self, *args) -> pd.Series:
    categories = [str(c) for c in self.corpus_.get_categories()]
    tp, fp, pos, neg, tpr, fpr, invn_tpr, invn_fpr = self._get_bns_score_for_category_index(cat_i=categories.index(str(self.category_name)), not_cat_is=[categories.index(str(c)) for c in self.not_category_names], X=self._get_X() > 0, y=self.corpus_._y)
    return pd.Series(invn_tpr - invn_fpr, index=self._get_index())

class RelativeEntropy(CorpusBasedTermScorer):
    """
	Implements relative entropy approach from
	Peter Fankhauser, Jorg Knappen, Elke Teich. Exploring and visualizing variation in language resources.
	LREC 2014.

	```
	term_scorer = (RelativeEntropy(corpus, smoothing_lambda = 0.05, minimum_p_value=0.05)
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
	file_name = 'rotten_fresh_fre.html'
	open(file_name, 'wb').write(html.encode('utf-8'))
	IFrame(src=file_name, width=1300, height=700)
	```
	"""

    def _set_scorer_args(self, **kwargs):
        self.min_p_ = kwargs.get('minimum_p_value', 0.05)
        self.smoothing_lambda_ = kwargs.get('smoothing_lambda', 0.05)

    def get_scores(self, *args):
        """
		In this case, parameters a and b aren't used, since this information is taken
		directly from the corpus categories.

		Returns
		-------

		"""

        def jelinek_mercer_smoothing(cat):
            p_hat_w = self.tdf_[cat] * 1.0 / self.tdf_[cat].sum()
            c_hat_w = self.smoothing_lambda_ * self.tdf_.sum(axis=1) * 1.0 / self.tdf_.sum().sum()
            return (1 - self.smoothing_lambda_) * p_hat_w + self.smoothing_lambda_ * c_hat_w
        p_w = jelinek_mercer_smoothing('cat')
        q_w = jelinek_mercer_smoothing('ncat')
        kl_divergence = p_w * np.log(p_w / q_w) / np.log(2)
        tt, pvals = self.get_t_statistics()
        return kl_divergence * (pvals < self.min_p_)

    def get_name(self):
        return 'Frankhauser Relative Entropy'

def jelinek_mercer_smoothing(cat):
    p_hat_w = self.tdf_[cat] * 1.0 / self.tdf_[cat].sum()
    c_hat_w = self.smoothing_lambda_ * self.tdf_.sum(axis=1) * 1.0 / self.tdf_.sum().sum()
    return (1 - self.smoothing_lambda_) * p_hat_w + self.smoothing_lambda_ * c_hat_w

def get_scores(self, *args):
    """
		In this case, parameters a and b aren't used, since this information is taken
		directly from the corpus categories.

		Returns
		-------

		"""

    def jelinek_mercer_smoothing(cat):
        p_hat_w = self.tdf_[cat] * 1.0 / self.tdf_[cat].sum()
        c_hat_w = self.smoothing_lambda_ * self.tdf_.sum(axis=1) * 1.0 / self.tdf_.sum().sum()
        return (1 - self.smoothing_lambda_) * p_hat_w + self.smoothing_lambda_ * c_hat_w
    p_w = jelinek_mercer_smoothing('cat')
    q_w = jelinek_mercer_smoothing('ncat')
    kl_divergence = p_w * np.log(p_w / q_w) / np.log(2)
    tt, pvals = self.get_t_statistics()
    return kl_divergence * (pvals < self.min_p_)

class CohensDCalculator(object):

    def get_cohens_d_df(self, cat_X, ncat_X, orig_cat_X, orig_ncat_X, correction_method=None):
        empty_cat_X_smoothing_doc = np.zeros((1, cat_X.shape[1]))
        empty_ncat_X_smoothing_doc = np.zeros((1, ncat_X.shape[1]))
        try:
            smoothed_cat_X = np.vstack([empty_cat_X_smoothing_doc, cat_X])
            smoothed_ncat_X = np.vstack([empty_ncat_X_smoothing_doc, ncat_X])
        except:
            smoothed_cat_X = scipy.sparse.vstack([empty_cat_X_smoothing_doc, cat_X])
            smoothed_ncat_X = scipy.sparse.vstack([empty_ncat_X_smoothing_doc, ncat_X])
        n1, n2 = (float(smoothed_cat_X.shape[0]), float(smoothed_ncat_X.shape[0]))
        n = n1 + n2
        m1 = cat_X.mean(axis=0).A1 if type(cat_X) == np.matrix else cat_X.mean(axis=0)
        m2 = ncat_X.mean(axis=0).A1 if type(ncat_X) == np.matrix else ncat_X.mean(axis=0)
        v1 = smoothed_cat_X.var(axis=0).A1 if type(smoothed_cat_X) == np.matrix else smoothed_cat_X.mean(axis=0)
        v2 = smoothed_ncat_X.var(axis=0).A1 if type(smoothed_ncat_X) == np.matrix else smoothed_ncat_X.mean(axis=0)
        if len(m1.shape) == 2:
            m1 = m1.A1
            m2 = m2.A1
            v1 = v1.A1
            v2 = v2.A1
        s_pooled = np.sqrt(((n2 - 1) * v2 + (n1 - 1) * v1) / (n - 2.0))
        cohens_d = (m1 - m2) / s_pooled
        cohens_d_se = np.sqrt((n - 1.0) / (n - 3) * (4.0 / n) * (1 + np.square(cohens_d) / 8.0))
        cohens_d_z = cohens_d / cohens_d_se
        cohens_d_p = norm.sf(cohens_d_z)
        hedges_g = cohens_d * (1 - 3.0 / (4.0 * (n - 2) - 1))
        hedges_g_se = np.sqrt(n / (n1 * n2) + np.square(hedges_g) / (n - 2.0))
        hedges_g_z = hedges_g / hedges_g_se
        hedges_g_p = norm.sf(hedges_g_z)
        count1 = orig_cat_X.sum(axis=0).A1.astype(int)
        count2 = orig_ncat_X.sum(axis=0).A1.astype(int)
        docs1 = (orig_cat_X > 0).sum(axis=0).A1
        docs2 = (orig_ncat_X > 0).sum(axis=0).A1
        dict_to_df = {'cohens_d': cohens_d, 'cohens_d_se': cohens_d_se, 'cohens_d_z': cohens_d_z, 'cohens_d_p': cohens_d_p, 'hedges_g': hedges_g, 'hedges_g_se': hedges_g_se, 'hedges_g_z': hedges_g_z, 'hedges_g_p': hedges_g_p, 'm1': m1, 'm2': m2, 'count1': count1, 'count2': count2, 'docs1': docs1, 'docs2': docs2}
        score_df = pd.DataFrame(dict_to_df).fillna(0)
        if correction_method is not None:
            from statsmodels.stats.multitest import multipletests
            score_df['cohens_d_p_' + correction_method] = multipletests(np.array(score_df['cohens_d_p'], score_df['cohens_d_p'] - 1), method=correction_method)[1]
            "\n            score_df['hedges_g_p_corr'] = 0.5\n            for method in ['cohens_d', 'hedges_g']:\n                score_df[method + '_p_corr'] = 0.5\n                import pdb; pdb.set_trace()\n                pvals = score_df.loc[(score_df['m1'] != 0) | (score_df['m2'] != 0), method + '_p']\n                pvals = np.min(np.array([pvals, 1. - pvals])) * 2.\n                score_df.loc[(score_df['m1'] != 0) | (score_df['m2'] != 0), method + '_p_corr'] = (\n                    multipletests(pvals, method=correction_method)[1]\n                )\n            "
        return score_df

def get_cohens_d_df(self, cat_X, ncat_X, orig_cat_X, orig_ncat_X, correction_method=None):
    empty_cat_X_smoothing_doc = np.zeros((1, cat_X.shape[1]))
    empty_ncat_X_smoothing_doc = np.zeros((1, ncat_X.shape[1]))
    try:
        smoothed_cat_X = np.vstack([empty_cat_X_smoothing_doc, cat_X])
        smoothed_ncat_X = np.vstack([empty_ncat_X_smoothing_doc, ncat_X])
    except:
        smoothed_cat_X = scipy.sparse.vstack([empty_cat_X_smoothing_doc, cat_X])
        smoothed_ncat_X = scipy.sparse.vstack([empty_ncat_X_smoothing_doc, ncat_X])
    n1, n2 = (float(smoothed_cat_X.shape[0]), float(smoothed_ncat_X.shape[0]))
    n = n1 + n2
    m1 = cat_X.mean(axis=0).A1 if type(cat_X) == np.matrix else cat_X.mean(axis=0)
    m2 = ncat_X.mean(axis=0).A1 if type(ncat_X) == np.matrix else ncat_X.mean(axis=0)
    v1 = smoothed_cat_X.var(axis=0).A1 if type(smoothed_cat_X) == np.matrix else smoothed_cat_X.mean(axis=0)
    v2 = smoothed_ncat_X.var(axis=0).A1 if type(smoothed_ncat_X) == np.matrix else smoothed_ncat_X.mean(axis=0)
    if len(m1.shape) == 2:
        m1 = m1.A1
        m2 = m2.A1
        v1 = v1.A1
        v2 = v2.A1
    s_pooled = np.sqrt(((n2 - 1) * v2 + (n1 - 1) * v1) / (n - 2.0))
    cohens_d = (m1 - m2) / s_pooled
    cohens_d_se = np.sqrt((n - 1.0) / (n - 3) * (4.0 / n) * (1 + np.square(cohens_d) / 8.0))
    cohens_d_z = cohens_d / cohens_d_se
    cohens_d_p = norm.sf(cohens_d_z)
    hedges_g = cohens_d * (1 - 3.0 / (4.0 * (n - 2) - 1))
    hedges_g_se = np.sqrt(n / (n1 * n2) + np.square(hedges_g) / (n - 2.0))
    hedges_g_z = hedges_g / hedges_g_se
    hedges_g_p = norm.sf(hedges_g_z)
    count1 = orig_cat_X.sum(axis=0).A1.astype(int)
    count2 = orig_ncat_X.sum(axis=0).A1.astype(int)
    docs1 = (orig_cat_X > 0).sum(axis=0).A1
    docs2 = (orig_ncat_X > 0).sum(axis=0).A1
    dict_to_df = {'cohens_d': cohens_d, 'cohens_d_se': cohens_d_se, 'cohens_d_z': cohens_d_z, 'cohens_d_p': cohens_d_p, 'hedges_g': hedges_g, 'hedges_g_se': hedges_g_se, 'hedges_g_z': hedges_g_z, 'hedges_g_p': hedges_g_p, 'm1': m1, 'm2': m2, 'count1': count1, 'count2': count2, 'docs1': docs1, 'docs2': docs2}
    score_df = pd.DataFrame(dict_to_df).fillna(0)
    if correction_method is not None:
        from statsmodels.stats.multitest import multipletests
        score_df['cohens_d_p_' + correction_method] = multipletests(np.array(score_df['cohens_d_p'], score_df['cohens_d_p'] - 1), method=correction_method)[1]
        "\n            score_df['hedges_g_p_corr'] = 0.5\n            for method in ['cohens_d', 'hedges_g']:\n                score_df[method + '_p_corr'] = 0.5\n                import pdb; pdb.set_trace()\n                pvals = score_df.loc[(score_df['m1'] != 0) | (score_df['m2'] != 0), method + '_p']\n                pvals = np.min(np.array([pvals, 1. - pvals])) * 2.\n                score_df.loc[(score_df['m1'] != 0) | (score_df['m2'] != 0), method + '_p_corr'] = (\n                    multipletests(pvals, method=correction_method)[1]\n                )\n            "
    return score_df

class CohensD(CorpusBasedTermScorer, CohensDCalculator):
    """
    Cohen's d scores

    term_scorer = (CohensD(corpus).set_categories('Positive', ['Negative'], ['Plot']))

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
    file_name = 'rotten_fresh_fre.html'
    open(file_name, 'wb').write(html.encode('utf-8'))
    IFrame(src=file_name, width=1300, height=700)
    """

    def _set_scorer_args(self, **kwargs):
        pass

    def get_scores(self, *args):
        return self.get_score_df()['cohens_d']

    def get_score_df(self, correction_method=None):
        """

        :param correction_method: str or None, correction method from statsmodels.stats.multitest.multipletests
         'fdr_bh' is recommended.
        :return: pd.DataFrame
        """
        X = self._get_X().astype(np.float64)
        X_doc_len_norm = X / X.sum(axis=1)
        try:
            X_doc_len_norm[np.isnan(X_doc_len_norm)] = 0
        except:
            X_doc_len_norm.data = np.nan_to_num(X_doc_len_norm.data, nan=0)
            X_doc_len_norm = X_doc_len_norm.tocsr()
        cat_X, ncat_X = self._get_cat_and_ncat(X_doc_len_norm)
        orig_cat_X, orig_ncat_X = self._get_cat_and_ncat(X)
        score_df = self.get_cohens_d_df(cat_X, ncat_X, orig_cat_X, orig_ncat_X, correction_method).set_index(np.array(self._get_index()))
        score_df.index.name = 'term'
        return score_df

    def get_name(self):
        return "Cohen's d"

def get_score_df(self, correction_method=None):
    """

        :param correction_method: str or None, correction method from statsmodels.stats.multitest.multipletests
         'fdr_bh' is recommended.
        :return: pd.DataFrame
        """
    X = self._get_X().astype(np.float64)
    X_doc_len_norm = X / X.sum(axis=1)
    try:
        X_doc_len_norm[np.isnan(X_doc_len_norm)] = 0
    except:
        X_doc_len_norm.data = np.nan_to_num(X_doc_len_norm.data, nan=0)
        X_doc_len_norm = X_doc_len_norm.tocsr()
    cat_X, ncat_X = self._get_cat_and_ncat(X_doc_len_norm)
    orig_cat_X, orig_ncat_X = self._get_cat_and_ncat(X)
    score_df = self.get_cohens_d_df(cat_X, ncat_X, orig_cat_X, orig_ncat_X, correction_method).set_index(np.array(self._get_index()))
    score_df.index.name = 'term'
    return score_df

class LRC(CorpusBasedTermScorer):
    """
    LRC from Evert (2023).

    A direct translation of the R function from (Evert 2023)
    Stephanie Evert. 2023. Measuring Keyness. https://osf.io/x8z9n.
    """

    def _set_scorer_args(self, **kwargs):
        self.conf_level_ = kwargs.get('conf_level', 0.95)
        self.correct_ = kwargs.get('correct', True)
        self.alternative_ = kwargs.get('alternative', 'two sided')

    def _get_ns_and_fs(self, args):
        cat_X, ncat_X = self._get_cat_and_ncat(self._get_X())
        n1 = self._get_cat_size()
        n2 = self._get_ncat_size()
        if len(args) == 0:
            f1 = cat_X.sum(axis=0).A1
            f2 = ncat_X.sum(axis=0).A1
        else:
            f1, f2 = self.__get_f1_f2_from_args(args)
        f1 = np.array(f1).astype(np.float64)
        f2 = np.array(f2).astype(np.float64)
        return (n1, n2, f1, f2)

    def get_scores(self, *args) -> pd.Series:
        n1, n2, f1, f2 = self._get_ns_and_fs(args)
        scores = lrc(f1=f1, f2=f2, n1=n1, n2=n2, conf_level=self.conf_level_, correct=self.correct_, alternative=self.alternative_)
        return pd.Series(scores, index=self._get_terms())

    def get_score_df(self, *args) -> pd.DataFrame:
        n1, n2, f1, f2 = self._get_ns_and_fs(args)
        return lrc_df(f1=f1, f2=f2, n1=n1, n2=n2, conf_level=self.conf_level_, correct=self.correct_, alternative=self.alternative_)

    def get_name(self):
        return 'LRC'

def _get_ns_and_fs(self, args):
    cat_X, ncat_X = self._get_cat_and_ncat(self._get_X())
    n1 = self._get_cat_size()
    n2 = self._get_ncat_size()
    if len(args) == 0:
        f1 = cat_X.sum(axis=0).A1
        f2 = ncat_X.sum(axis=0).A1
    else:
        f1, f2 = self.__get_f1_f2_from_args(args)
    f1 = np.array(f1).astype(np.float64)
    f2 = np.array(f2).astype(np.float64)
    return (n1, n2, f1, f2)

def get_scores(self, *args) -> pd.Series:
    n1, n2, f1, f2 = self._get_ns_and_fs(args)
    scores = lrc(f1=f1, f2=f2, n1=n1, n2=n2, conf_level=self.conf_level_, correct=self.correct_, alternative=self.alternative_)
    return pd.Series(scores, index=self._get_terms())

def get_score_df(self, *args) -> pd.DataFrame:
    n1, n2, f1, f2 = self._get_ns_and_fs(args)
    return lrc_df(f1=f1, f2=f2, n1=n1, n2=n2, conf_level=self.conf_level_, correct=self.correct_, alternative=self.alternative_)

def lrc(f1: np.array, f2: np.array, n1: Union[int, np.array], n2: Union[int, np.array], conf_level: float=0.95, correct: bool=True, alternative: str='two sided') -> np.array:
    return lrc_df(f1=f1, f2=f2, n1=n1, n2=n2, conf_level=conf_level, correct=correct, alternative=alternative).Score.values

def pmax(a, b):
    assert type(a) in [list, np.array]
    return pd.DataFrame({'A': a}).assign(B=b).max(axis=1).values

def pmin(a, b):
    assert type(a) in [list, np.array]
    return pd.DataFrame({'A': a}).assign(B=b).min(axis=1).values

def qbeta(p, shape1, shape2, lower_tail=True):
    if lower_tail is False:
        p = 1 - p
    return beta.ppf(q=p, a=shape1, b=shape2, loc=0, scale=1)

class BetaPosterior(CorpusBasedTermScorer):
    """
    Beta Posterior Scoring. Code adapted from
    https://github.com/serinachang5/gender-associations/blob/master/score_words.py (Chang 2019).

    Serina Chang and Kathleen McKeown. Automatically Inferring Gender Associations from Language. To appear
    in Empirical Methods in Natural Language Processing (EMNLP) 2019 (Short Paper).

    Method was originally introduced in
    David Bamman, Jacob Eisenstein, and Tyler Schnoebelen.  GENDER IDENTITY AND LEXICAL VARIATION IN SOCIAL MEDIA. 2014.

    Direct quote from Bamman (2014)

    Identifying gender markers. Our goal is to identify words that are used with
    unusual frequency by authors of a single gender. Assume that each term has an
    unknown likelihood fi, indicating the proportion of authors who use term i. For
    gender j, there are Nj authors, of whom kji use term i; the total count of the term i
    is ki. We ask whether the count kji is significantly larger than expected. Assuming
    a non-informative prior distribution on fi, the posterior distribution (conditioned on
    the observations ki and N) is Beta(ki, N-ki). The distribution of the gender-specific
    counts can be described by an integral over all possible fi. This integral defines the
    Beta-Binomial distribution (Gelman, Carlin, Stern, and Rubin 2004), and has a
    closed form solution. We mark a term as having a significant gender association if
    the cumulative distribution at the count kji is p < .05.

    ```
    >>> term_scorer = BetaPosterior(corpus).set_categories('Positive', ['Negative'], ['Plot']).get_score_df()

    ```
    """

    def __init__(self, corpus, *args, **kwargs):
        CorpusBasedTermScorer.__init__(self, corpus, *args, **kwargs)
        self.set_term_ranker(OncePerDocFrequencyRanker)

    def _set_scorer_args(self, **kwargs):
        pass

    def get_scores(self, *args):
        return self.get_score_df()['score']

    def get_score_df(self):
        """


        :return: pd.DataFrame
        """
        term_freq_df = self.term_ranker_.get_ranks('')
        cat_freq_df = pd.DataFrame({'cat': term_freq_df[self.category_name], 'ncat': term_freq_df[self.not_category_names].sum(axis=1)})
        if self.neutral_category_names:
            cat_freq_df['neut'] = term_freq_df[self.neutral_category_names].sum(axis=1)
        cat_freq_df['all'] = cat_freq_df.sum(axis=1)
        N = cat_freq_df['all'].sum()
        catN = cat_freq_df['cat'].sum()
        ncatN = cat_freq_df['ncat'].sum()
        cat_freq_df = cat_freq_df.assign(cat_pct=lambda df: df['cat'] * 1.0 / catN, ncat_pct=lambda df: df['ncat'] * 1.0 / ncatN)

        def row_beta_posterior(row):
            return pd.Series({'cat_p': beta(row['all'], N - row['all']).sf(row['cat'] * 1.0 / catN), 'ncat_p': beta(row['all'], N - row['all']).sf(row['ncat'] * 1.0 / ncatN)})
        p_val_df = cat_freq_df.apply(row_beta_posterior, axis=1)
        cat_freq_df = cat_freq_df.assign(cat_p=p_val_df['cat_p'], ncat_p=p_val_df['ncat_p'], cat_z=norm.ppf(p_val_df['cat_p']), ncat_z=norm.ppf(p_val_df['ncat_p']))
        cat_freq_df['score'] = None
        cat_freq_df['score'][cat_freq_df['cat_pct'] == cat_freq_df['ncat_pct']] = 0
        cat_freq_df['score'][cat_freq_df['cat_pct'] < cat_freq_df['ncat_pct']] = cat_freq_df['ncat_z']
        cat_freq_df['score'][cat_freq_df['cat_pct'] > cat_freq_df['ncat_pct']] = -cat_freq_df['cat_z']
        return cat_freq_df

    def get_name(self):
        return 'Beta Posterior'

def row_beta_posterior(row):
    return pd.Series({'cat_p': beta(row['all'], N - row['all']).sf(row['cat'] * 1.0 / catN), 'ncat_p': beta(row['all'], N - row['all']).sf(row['ncat'] * 1.0 / ncatN)})

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

def length_adjusted_tf(cat):
    tf = self.tdf_[cat]
    dl = self.tdf_[cat].sum()
    return tf * (self.k1 + 1) / (tf + self.k1 * (1 - self.b + self.b * (dl / avgdl)))

def bm25_score(cat):
    return -length_adjusted_tf(cat) * np.log(idf(cat))

class CliffsDelta(CorpusBasedTermScorer):
    """
    Cliff's Delta from Cliff (1993).


    Cliff, N. (1993). Dominance statistics: Ordinal analyses to answer ordinal questions.
    Psychological Bulletin, 114(3), 494–509.

    https://real-statistics.com/non-parametric-tests/mann-whitney-test/cliffs-delta/ used as a resource

    For p-value calculation, the following were used:
    Neuhäuser, M., Lösch, C., & Jöckel, K.-H. (2007). The Chen–Luo test in case of heteroscedasticity.
    As cited by
    https://stats.stackexchange.com/questions/360496/how-do-you-interpret-the-cliffs-delta-95-confidence-interval-2%E2%88%92tailed-grap

    """

    def _set_scorer_args(self, alpha: float=0.05, *args, **kwargs):
        self.alpha = alpha
        self.verbose = kwargs.get('verbose', False)

    def get_scores(self, *args) -> pd.Series:
        """
        In this case, args aren't used, since this information is taken
        directly from the corpus categories.

        Returns
        -------
        np.array, scores
        """
        score_df = self.get_score_df()
        return score_df['Metric']

    def get_score_df(self, label_append=''):
        cat_X, ncat_X = self._get_cat_and_ncat(self._get_X())
        catXnorm = cat_X / cat_X.sum(axis=1)
        ncatXnorm = ncat_X / ncat_X.sum(axis=1)
        try:
            if catXnorm.format == 'coo':
                catXnorm = catXnorm.tocsr()
                ncatXnorm = ncatXnorm.tocsr()
        except:
            pass
        m = catXnorm.shape[0]
        n = ncatXnorm.shape[0]
        data = []
        iter = enumerate(self._get_terms())
        if self.verbose:
            iter = tqdm(iter, total=len(self._get_terms()))
        for i, term in iter:
            cati = np.repeat(catXnorm[:, i].todense(), n, axis=1).ravel().A1
            ncati = np.repeat(ncatXnorm[:, i].todense(), m, axis=1).T.ravel().A1
            deltai = np.zeros(n * m)
            deltai[cati > ncati] = 1
            deltai[cati < ncati] = -1
            delta = deltai.sum() / (m * n)
            deltars = deltai.reshape((n, m))
            delta_r = deltars.sum(axis=0) / n
            delta_c = deltars.sum(axis=1) / m
            sd = np.sqrt((m ** 2 * ((delta_r - delta) ** 2).sum() + n ** 2 * ((delta_c - delta) ** 2).sum() - ((deltai - delta) ** 2).sum()) / (m * n * (m - 1) * (n - 1)))
            zcrit = ndtri(self.alpha)
            lo = (delta - delta ** 3 - zcrit * sd * np.sqrt(1 - 2 * delta ** 2 + delta ** 4 + (zcrit * delta) ** 2)) / (1 - delta ** 2 - (zcrit * delta) ** 2)
            hi = (delta - delta ** 3 + zcrit * sd * np.sqrt(1 - 2 * delta ** 2 + delta ** 4 + (zcrit * delta) ** 2)) / (1 - delta ** 2 - (zcrit * delta) ** 2)
            datum = {'term': term, 'Metric': delta, 'Stddev': sd, f'Low-{(1 - self.alpha) * 100}% CI': lo, f'High-{(1 - self.alpha) * 100}% CI': hi}
            data.append(datum)
        return pd.DataFrame(data).set_index('term').assign(TermCount1=cat_X.sum(axis=0).A1, TermCount2=ncat_X.sum(axis=0).A1, DocCount1=(cat_X > 0).sum(axis=0).A1, DocCount2=(ncat_X > 0).sum(axis=0).A1)

    def get_name(self):
        return "Cliff's Delta"

def get_score_df(self, label_append=''):
    cat_X, ncat_X = self._get_cat_and_ncat(self._get_X())
    catXnorm = cat_X / cat_X.sum(axis=1)
    ncatXnorm = ncat_X / ncat_X.sum(axis=1)
    try:
        if catXnorm.format == 'coo':
            catXnorm = catXnorm.tocsr()
            ncatXnorm = ncatXnorm.tocsr()
    except:
        pass
    m = catXnorm.shape[0]
    n = ncatXnorm.shape[0]
    data = []
    iter = enumerate(self._get_terms())
    if self.verbose:
        iter = tqdm(iter, total=len(self._get_terms()))
    for i, term in iter:
        cati = np.repeat(catXnorm[:, i].todense(), n, axis=1).ravel().A1
        ncati = np.repeat(ncatXnorm[:, i].todense(), m, axis=1).T.ravel().A1
        deltai = np.zeros(n * m)
        deltai[cati > ncati] = 1
        deltai[cati < ncati] = -1
        delta = deltai.sum() / (m * n)
        deltars = deltai.reshape((n, m))
        delta_r = deltars.sum(axis=0) / n
        delta_c = deltars.sum(axis=1) / m
        sd = np.sqrt((m ** 2 * ((delta_r - delta) ** 2).sum() + n ** 2 * ((delta_c - delta) ** 2).sum() - ((deltai - delta) ** 2).sum()) / (m * n * (m - 1) * (n - 1)))
        zcrit = ndtri(self.alpha)
        lo = (delta - delta ** 3 - zcrit * sd * np.sqrt(1 - 2 * delta ** 2 + delta ** 4 + (zcrit * delta) ** 2)) / (1 - delta ** 2 - (zcrit * delta) ** 2)
        hi = (delta - delta ** 3 + zcrit * sd * np.sqrt(1 - 2 * delta ** 2 + delta ** 4 + (zcrit * delta) ** 2)) / (1 - delta ** 2 - (zcrit * delta) ** 2)
        datum = {'term': term, 'Metric': delta, 'Stddev': sd, f'Low-{(1 - self.alpha) * 100}% CI': lo, f'High-{(1 - self.alpha) * 100}% CI': hi}
        data.append(datum)
    return pd.DataFrame(data).set_index('term').assign(TermCount1=cat_X.sum(axis=0).A1, TermCount2=ncat_X.sum(axis=0).A1, DocCount1=(cat_X > 0).sum(axis=0).A1, DocCount2=(ncat_X > 0).sum(axis=0).A1)

class LogLikelihoodRatio(CorpusBasedTermScorer):
    """
    Log likelihood ratio (inspired by https://github.com/Zeta-and-Company/pydistinto/blob/main/scripts/measures/LLR.py)

    """

    def _set_scorer_args(self, *args):
        pass

    def get_scores(self, *args) -> pd.Series:
        """
        In this case, args aren't used, since this information is taken
        directly from the corpus categories.

        Returns
        -------
        np.array, scores
        """
        X = self._get_X() > 0
        cat_X, ncat_X = self._get_cat_and_ncat(X)
        return pd.Series(self._get_llr_score(cat_X, ncat_X).statistic, index=self._get_terms())

    def get_score_df(self, *args) -> pd.DataFrame:
        """
        In this case, args aren't used, since this information is taken
        directly from the corpus categories.

        Returns
        -------
        np.array, scores
        """
        X = self._get_X() > 0
        cat_X, ncat_X = self._get_cat_and_ncat(X)
        score = self._get_llr_score(cat_X, ncat_X)
        return pd.DataFrame({'Term': self._get_terms(), 'Base': cat_X.sum(axis=0).A1, 'Counter': ncat_X.sum(axis=0).A1, 'Score': score.statistic, 'PValue': score.pvalue}).set_index('Term')

    def _get_terms(self):
        return self.corpus_.get_terms(use_metadata=self.use_metadata_)

    def _get_llr_score(self, cat_X, ncat_X):
        a = cat_X.sum(axis=0).A1
        b = ncat_X.sum(axis=0).A1
        exp1 = sum(a) * (a + b) / (sum(a) + sum(b))
        exp2 = sum(b) * (a + b) / (sum(a) + sum(b))
        return power_divergence([a, b], f_exp=[exp1, exp2])

    def get_name(self):
        return 'Log likelihood ratio'

def get_scores(self, *args) -> pd.Series:
    """
        In this case, args aren't used, since this information is taken
        directly from the corpus categories.

        Returns
        -------
        np.array, scores
        """
    X = self._get_X() > 0
    cat_X, ncat_X = self._get_cat_and_ncat(X)
    return pd.Series(self._get_llr_score(cat_X, ncat_X).statistic, index=self._get_terms())

def get_score_df(self, *args) -> pd.DataFrame:
    """
        In this case, args aren't used, since this information is taken
        directly from the corpus categories.

        Returns
        -------
        np.array, scores
        """
    X = self._get_X() > 0
    cat_X, ncat_X = self._get_cat_and_ncat(X)
    score = self._get_llr_score(cat_X, ncat_X)
    return pd.DataFrame({'Term': self._get_terms(), 'Base': cat_X.sum(axis=0).A1, 'Counter': ncat_X.sum(axis=0).A1, 'Score': score.statistic, 'PValue': score.pvalue}).set_index('Term')

def _get_llr_score(self, cat_X, ncat_X):
    a = cat_X.sum(axis=0).A1
    b = ncat_X.sum(axis=0).A1
    exp1 = sum(a) * (a + b) / (sum(a) + sum(b))
    exp2 = sum(b) * (a + b) / (sum(a) + sum(b))
    return power_divergence([a, b], f_exp=[exp1, exp2])

class CredTFIDF(CorpusBasedTermScorer):
    """
    Yoon Kim and Owen Zhang. Implementation of Credibility Adjusted Term Frequency: A Supervised Term Weighting
    Scheme for Sentiment Analysis and Text Classification. WASSA 2014.
    http://www.people.fas.harvard.edu/~yoonkim/data/cred-tfidf.pdf
    """

    def get_score_df(self):
        """
        :return: pd.DataFrame
        """
        X = self._get_X().astype(np.float64)
        tf_i_d_pos, tf_i_d_neg = self._get_cat_and_ncat(X)
        return self._get_score_df_from_category_Xs(tf_i_d_neg, tf_i_d_pos)

    def _get_score_df_from_category_Xs(self, tf_i_d_neg, tf_i_d_pos):
        C_i_pos = tf_i_d_pos.sum(axis=0)
        C_i_neg = tf_i_d_neg.sum(axis=0)
        C_i = C_i_pos + C_i_neg
        s_hat_i = (np.power(C_i_pos, 2) + np.power(C_i_neg, 2)) / np.power(C_i, 2)
        C = C_i.sum()
        s_hat = (s_hat_i.A1 * C_i.A1 / C).sum()
        s_bar_i = (np.power(C_i_pos, 2) + np.power(C_i_neg, 2) + s_hat * self.eta) / (np.power(C_i, 2) + self.eta)
        if self.use_sublinear:
            if not type(tf_i_d_pos) in [np.matrix, np.array]:
                tf_i_d_pos = tf_i_d_pos.todense()
                tf_i_d_neg = tf_i_d_neg.todense()
            adjpos_tf_idf = np.asarray(np.log(tf_i_d_pos + 0.5))
            adjneg_tf_idf = np.asarray(np.log(tf_i_d_neg + 0.5))
        else:
            adjpos_tf_idf = np.asarray(tf_i_d_pos.todense())
            adjneg_tf_idf = np.asarray(tf_i_d_neg.todense())
        s_bar_i_coef = (0.5 + s_bar_i).A1
        tf_bar_i_pos = adjpos_tf_idf
        tf_bar_i_neg = adjneg_tf_idf
        if self.use_cred:
            tf_bar_i_pos *= s_bar_i_coef
            tf_bar_i_neg *= s_bar_i_coef
        N = 1.0 * tf_i_d_pos.shape[0] + tf_bar_i_neg.shape[0]
        df_i = (tf_i_d_pos > 0).astype(float).sum(axis=0) + (tf_i_d_neg > 0).astype(float).sum(axis=0)
        w_i_d_pos = tf_bar_i_pos * np.log(N / df_i).A1
        w_i_d_neg = tf_bar_i_neg * np.log(N / df_i).A1
        w_d_pos_l2 = 1.0
        w_d_neg_l2 = 1.0
        if self.use_l2_norm:
            w_d_pos_l2 = np.linalg.norm(w_i_d_pos, 2, axis=1)
            w_d_neg_l2 = np.linalg.norm(w_i_d_neg, 2, axis=1)
        pos_cred_tfidf = (w_i_d_pos.T / w_d_pos_l2).mean(axis=1)
        neg_cred_tfidf = (w_i_d_neg.T / w_d_neg_l2).mean(axis=1)
        score_df = pd.DataFrame({'pos_cred_tfidf': pos_cred_tfidf, 'neg_cred_tfidf': neg_cred_tfidf, 'delta_cred_tf_idf': pos_cred_tfidf - neg_cred_tfidf}, index=self._get_index())
        return score_df

    def _set_scorer_args(self, **kwargs):
        self.eta = kwargs.get('eta', 1.0)
        self.use_sublinear = kwargs.get('use_sublinear', True)
        self.use_cred = kwargs.get('use_cred', True)
        self.use_l2_norm = kwargs.get('use_l2_norm', True)

    def get_scores(self, *args):
        return self.get_score_df()['delta_cred_tf_idf']

    def get_name(self):
        return 'Delta mean %stf-idf' % ('cred-' if self.use_cred else '')

def get_score_df(self):
    """
        :return: pd.DataFrame
        """
    X = self._get_X().astype(np.float64)
    tf_i_d_pos, tf_i_d_neg = self._get_cat_and_ncat(X)
    return self._get_score_df_from_category_Xs(tf_i_d_neg, tf_i_d_pos)

def _get_score_df_from_category_Xs(self, tf_i_d_neg, tf_i_d_pos):
    C_i_pos = tf_i_d_pos.sum(axis=0)
    C_i_neg = tf_i_d_neg.sum(axis=0)
    C_i = C_i_pos + C_i_neg
    s_hat_i = (np.power(C_i_pos, 2) + np.power(C_i_neg, 2)) / np.power(C_i, 2)
    C = C_i.sum()
    s_hat = (s_hat_i.A1 * C_i.A1 / C).sum()
    s_bar_i = (np.power(C_i_pos, 2) + np.power(C_i_neg, 2) + s_hat * self.eta) / (np.power(C_i, 2) + self.eta)
    if self.use_sublinear:
        if not type(tf_i_d_pos) in [np.matrix, np.array]:
            tf_i_d_pos = tf_i_d_pos.todense()
            tf_i_d_neg = tf_i_d_neg.todense()
        adjpos_tf_idf = np.asarray(np.log(tf_i_d_pos + 0.5))
        adjneg_tf_idf = np.asarray(np.log(tf_i_d_neg + 0.5))
    else:
        adjpos_tf_idf = np.asarray(tf_i_d_pos.todense())
        adjneg_tf_idf = np.asarray(tf_i_d_neg.todense())
    s_bar_i_coef = (0.5 + s_bar_i).A1
    tf_bar_i_pos = adjpos_tf_idf
    tf_bar_i_neg = adjneg_tf_idf
    if self.use_cred:
        tf_bar_i_pos *= s_bar_i_coef
        tf_bar_i_neg *= s_bar_i_coef
    N = 1.0 * tf_i_d_pos.shape[0] + tf_bar_i_neg.shape[0]
    df_i = (tf_i_d_pos > 0).astype(float).sum(axis=0) + (tf_i_d_neg > 0).astype(float).sum(axis=0)
    w_i_d_pos = tf_bar_i_pos * np.log(N / df_i).A1
    w_i_d_neg = tf_bar_i_neg * np.log(N / df_i).A1
    w_d_pos_l2 = 1.0
    w_d_neg_l2 = 1.0
    if self.use_l2_norm:
        w_d_pos_l2 = np.linalg.norm(w_i_d_pos, 2, axis=1)
        w_d_neg_l2 = np.linalg.norm(w_i_d_neg, 2, axis=1)
    pos_cred_tfidf = (w_i_d_pos.T / w_d_pos_l2).mean(axis=1)
    neg_cred_tfidf = (w_i_d_neg.T / w_d_neg_l2).mean(axis=1)
    score_df = pd.DataFrame({'pos_cred_tfidf': pos_cred_tfidf, 'neg_cred_tfidf': neg_cred_tfidf, 'delta_cred_tf_idf': pos_cred_tfidf - neg_cred_tfidf}, index=self._get_index())
    return score_df

def lg(x):
    return np.log(x) / np.log(2)

class DeltaJSDivergence(object):

    def __init__(self, pi1=0.5, pi2=0.5):
        assert pi1 + pi2 == 1
        self.pi1 = pi1
        self.pi2 = pi2

    def get_scores(self, a, b):
        p1 = 0.001 + a / np.sum(a)
        p2 = 0.001 + b / np.sum(b)
        pi1, pi2 = (self.pi1, self.pi2)
        m = pi1 * p1 + pi2 * p2

        def lg(x):
            return np.log(x) / np.log(2)
        return m * lg(1 / m) - (pi1 * p2 * lg(1 / p1) + pi2 * p2 * lg(1 / p2))

    def get_default_score(self):
        return 0

    def get_name(self):
        return 'JS Divergence Shift'

def lg(x):
    return np.log(x) / np.log(2)

class DeltaJSDivergenceScorer(CorpusBasedTermScorer):

    def _set_scorer_args(self, **kwargs):
        self.pi1 = kwargs.get('pi1', 0.5)
        self.pi2 = kwargs.get('pi2', 0.5)
        assert self.pi1 + self.pi2 == 1

    def get_score_df(self):
        return pd.DataFrame({'Score': self.get_scores()})

    def get_scores(self):
        rank_df = self.term_ranker_.set_non_text(self.use_metadata_).get_ranks('')
        focus = rank_df[str(self.category_name)].values
        background = rank_df[[str(c) for c in self.corpus_.get_categories() if str(c) in self.not_category_names]].sum(axis=1).values
        scores = DeltaJSDivergence(self.pi1, self.pi2).get_scores(a=focus, b=background)
        return pd.Series(scores, index=self._get_index())

    def get_default_score(self):
        return 0

    def get_name(self):
        return 'JS Divergence Shift'

def get_scores(self):
    rank_df = self.term_ranker_.set_non_text(self.use_metadata_).get_ranks('')
    focus = rank_df[str(self.category_name)].values
    background = rank_df[[str(c) for c in self.corpus_.get_categories() if str(c) in self.not_category_names]].sum(axis=1).values
    scores = DeltaJSDivergence(self.pi1, self.pi2).get_scores(a=focus, b=background)
    return pd.Series(scores, index=self._get_index())

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

class SimpleMaths(CorpusBasedTermScorer):
    """
    Simple Maths from Kilgariff (2009).


    Stephanie Evert. 2023. Measuring Keyness. https://osf.io/x8z9n.

    Adam Kilgariff. 2009. Simple Maths for Keywords. Proc. Corpus Linguistics.
    https://www.semanticscholar.org/paper/Simple-Maths-for-Keywords-Kilgarriff/69bd0a8a964e9b3b0b4394fe0d9d602d6a5a0453
    """

    def _set_scorer_args(self, **kwargs):
        self.lambda_ = kwargs.get('lambda_', 1)
        self.log_ = kwargs.get('log', False)
        self.coef_ = kwargs.get('coef', 1000000.0)

    def get_scores(self, *args) -> pd.Series:
        """
        In this case, args aren't used, since this information is taken
        directly from the corpus categories.

        Returns
        -------
        np.array, scores
        """
        cat_X, ncat_X = self._get_cat_and_ncat(self._get_X())
        N1 = self._get_cat_size()
        N2 = self._get_ncat_size()
        if len(args) == 0:
            f1 = cat_X.sum(axis=0).A1
            f2 = ncat_X.sum(axis=0).A1
        else:
            f1, f2 = self.__get_f1_f2_from_args(args)
        p1 = f1 / N1
        p2 = f2 / N2
        res = (self.coef_ * p1 + self.lambda_) / (self.coef_ * p2 + self.lambda_)
        if self.log_:
            res = np.log(res) / np.log(2)
        return pd.Series(res, index=self._get_terms())

    def get_name(self):
        return 'Simple Maths'

def get_scores(self, *args) -> pd.Series:
    """
        In this case, args aren't used, since this information is taken
        directly from the corpus categories.

        Returns
        -------
        np.array, scores
        """
    cat_X, ncat_X = self._get_cat_and_ncat(self._get_X())
    N1 = self._get_cat_size()
    N2 = self._get_ncat_size()
    if len(args) == 0:
        f1 = cat_X.sum(axis=0).A1
        f2 = ncat_X.sum(axis=0).A1
    else:
        f1, f2 = self.__get_f1_f2_from_args(args)
    p1 = f1 / N1
    p2 = f2 / N2
    res = (self.coef_ * p1 + self.lambda_) / (self.coef_ * p2 + self.lambda_)
    if self.log_:
        res = np.log(res) / np.log(2)
    return pd.Series(res, index=self._get_terms())

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

class RunningStatsArray:

    def __init__(self, width: int, n: int=0):
        self.width = width
        self.n = 0
        self.old_m = np.zeros(width)
        self.new_m = np.zeros(width)
        self.old_s = np.zeros(width)
        self.new_s = np.zeros(width)

    def clear(self) -> None:
        self.n = 0

    def push(self, x: np.array) -> 'RunningStatsArray':
        self.n += 1
        if self.n == 1:
            self.old_m = self.new_m = x
            self.old_s = np.zeros(self.width)
        else:
            self.new_m = self.old_m + (x - self.old_m) / self.n
            self.new_s = self.old_s + (x - self.old_m) * (x - self.new_m)
            self.old_m = self.new_m
            self.old_s = self.new_s
        if np.any(np.isnan(self.new_m)):
            import pdb
            pdb.set_trace()
        return self

    def mean(self) -> np.array:
        return self.new_m if self.n else np.zeros(self.width)

    def variance(self) -> np.array:
        return self.new_s / (self.n - 1) if self.n > 1 else np.zeros(self.width)

    def standard_deviation(self) -> np.array:
        return np.sqrt(self.variance())

    def pooled_variance(self, other: 'RunningStatsArray') -> np.array:
        return (self.variance() * self.n + other.variance() * other.n) / (self.n + other.n)

def standard_deviation(self) -> np.array:
    return np.sqrt(self.variance())

def pooled_variance(self, other: 'RunningStatsArray') -> np.array:
    return (self.variance() * self.n + other.variance() * other.n) / (self.n + other.n)

def sigmoid(x, L, x0, k, b):
    y = L / (1 + np.exp(-k * (x - x0))) + b
    return y

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

def get_task_df(self):
    """
		Returns
		-------

		"""
    term_time_df = self._get_term_time_df()
    terms_to_include = term_time_df.groupby('term')['top'].sum().sort_values(ascending=False).iloc[:self.num_terms_to_include].index
    task_df = term_time_df[term_time_df.term.isin(terms_to_include)][['time', 'term']].groupby('term').apply(lambda x: pd.Series(self._find_sequences(x['time']))).reset_index().rename({0: 'sequence'}, axis=1).reset_index().assign(start=lambda x: x['sequence'].apply(lambda x: x[0])).assign(end=lambda x: x['sequence'].apply(lambda x: x[1]))[['term', 'start', 'end']]
    return task_df

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

def _get_lexicon_df_from_topic_model(self, topic_model):
    return pd.DataFrame(pd.Series(topic_model).apply(pd.Series).reset_index()).melt(id_vars=['index'])[['index', 'value']].rename(columns={'index': 'cat', 'value': 'term'}).set_index('term')

def _analyze(self, doc):
    text_df = pd.DataFrame(pd.Series(self._get_terms_from_doc(doc))).join(self._lexicon_df).dropna().groupby('cat').sum()
    return text_df

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

def _analyze(self, doc):
    text_df = pd.DataFrame(pd.Series(Counter((t for t in split('(\\W)', doc.lower()) if t.strip())))).join(self._lexicon_df).dropna().groupby('cat').sum()
    return text_df

def get_top_model_term_lists(self):
    return self._lexicon_df.reset_index().groupby('cat')['term'].apply(list).to_dict()

class FeatsFromScoredLexicon(FeatsFromSpacyDoc):

    def __init__(self, lexicon_df, use_lemmas=False, **kwargs):
        """
        Parameters
        ----------
        lexicon_df: pd.DataFrame, Indexed on terms, columns are scores for each category

        Other parameters from FeatsFromSpacyDoc.__init__

        Example:
        >>> print(lexicon_df)
                     activation  imagery  pleasantness
        word
        a                1.3846      1.0        2.0000
        abandon          2.3750      2.4        1.0000
        abandoned        2.1000      3.0        1.1429
        abandonment      2.0000      1.4        1.0000
        abated           1.3333      1.2        1.6667
        """
        assert type(lexicon_df) == pd.DataFrame
        self._lexicon_df = lexicon_df
        super(FeatsFromScoredLexicon, self).__init__(use_lemmas, **kwargs)

    def get_doc_metadata(self, doc, prefix=''):
        """

        :param doc: spacy.Doc
        :param prefix: str, default is ''
        :return: pd.Series
        """
        out_series = pd.merge(pd.DataFrame(pd.Series([tok.lemma_ if self._use_lemmas else tok.lower_ for tok in doc]).value_counts(), columns=['count']), self._lexicon_df, left_index=True, right_index=True).drop(columns=['count']).mean(axis=0)
        if prefix == '':
            return out_series
        return pd.Series(out_series.values, index=[prefix + x for x in out_series.index])

    def has_metadata_term_list(self):
        return True

    def get_top_model_term_lists(self):
        return {col: list(self._lexicon_df[col].sort_values(ascending=False).iloc[:10].index) for col in self._lexicon_df}

def get_doc_metadata(self, doc, prefix=''):
    """

        :param doc: spacy.Doc
        :param prefix: str, default is ''
        :return: pd.Series
        """
    out_series = pd.merge(pd.DataFrame(pd.Series([tok.lemma_ if self._use_lemmas else tok.lower_ for tok in doc]).value_counts(), columns=['count']), self._lexicon_df, left_index=True, right_index=True).drop(columns=['count']).mean(axis=0)
    if prefix == '':
        return out_series
    return pd.Series(out_series.values, index=[prefix + x for x in out_series.index])

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

def _analyze(self, doc):
    text_df = pd.DataFrame(pd.Series(Counter((t for t in split('(\\W)', doc.lower()) if t.strip())))).join(self._lexicon_df).dropna().groupby('cat').sum()
    return text_df

def get_top_model_term_lists(self):
    return self._lexicon_df.reset_index().groupby('cat')['term'].apply(list).to_dict()

class tfidf_ranker(TermRanker):

    def get_ranks(self, label_append: str=' freq') -> pd.DataFrame:
        tdm = self.get_term_doc_mat()
        sqrt_tf = scale_tf(tdm)
        idf = np.log(self._corpus.get_num_docs() / (tdm > 0).sum(axis=0).A1)
        tfidf = sqrt_tf.multiply(idf).tocsr()
        y = self._corpus.get_category_ids()
        for cat_i, cat in enumerate(self._corpus.get_categories()):
            tfidf[y == cat_i, :].mean(axis=0).A1
            cat + label_append
        rank_df = pd.DataFrame({cat + label_append: tfidf[y == cat_i, :].mean(axis=0).A1 for cat_i, cat in enumerate(self._corpus.get_categories())})
        rank_df['term'] = self.get_terms()
        return rank_df.set_index('term')

def get_ranks(self, label_append: str=' freq') -> pd.DataFrame:
    tdm = self.get_term_doc_mat()
    sqrt_tf = scale_tf(tdm)
    idf = np.log(self._corpus.get_num_docs() / (tdm > 0).sum(axis=0).A1)
    tfidf = sqrt_tf.multiply(idf).tocsr()
    y = self._corpus.get_category_ids()
    for cat_i, cat in enumerate(self._corpus.get_categories()):
        tfidf[y == cat_i, :].mean(axis=0).A1
        cat + label_append
    rank_df = pd.DataFrame({cat + label_append: tfidf[y == cat_i, :].mean(axis=0).A1 for cat_i, cat in enumerate(self._corpus.get_categories())})
    rank_df['term'] = self.get_terms()
    return rank_df.set_index('term')

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

def js_float(x):
    return str(float(x))

def scale_font_size(scores: np.array, min_size=9, max_size=20) -> np.array:
    bin_boundaries = np.histogram_bin_edges(np.log(scores), bins=max_size - min_size)
    return pd.Series(scores).apply(np.log).apply(lambda x: bisect_left(bin_boundaries, x) + min_size).values

