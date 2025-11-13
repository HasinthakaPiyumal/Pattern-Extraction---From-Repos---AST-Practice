# Cluster 2

def filter_bigrams_by_pmis(word_freq_df, threshold_coef=DEFAULT_PMI_THRESHOLD_COEFFICIENT):
    if len(word_freq_df.index) == 0:
        return word_freq_df
    low_pmi_bigrams = get_low_pmi_bigrams(threshold_coef, word_freq_df)
    return word_freq_df.drop(low_pmi_bigrams.index)

class TermDocMatrixFilter(object):
    """
	Filter out terms below a particular frequency or pmi threshold.
	"""

    def __init__(self, pmi_threshold_coef=DEFAULT_PMI_THRESHOLD_COEFFICIENT, minimum_term_freq=3):
        """
		Parameters
		----------
		pmi_threshold_coef : float
			Bigram filtering threshold (2 * PMI). Default 2.
		minimum_term_freq : int
			Minimum number of times term has to appear.  Default 3.

		"""
        self._threshold_coef = pmi_threshold_coef
        self._min_freq = minimum_term_freq

    def filter(self, term_doc_matrix):
        """
		Parameters
		----------
		term_doc_matrix  : TermDocMatrix

		Returns
		-------
		TermDocMatrix pmi-filterd term doc matrix
		"""
        df = term_doc_matrix.get_term_freq_df()
        if len(df) == 0:
            return term_doc_matrix
        low_pmi_bigrams = get_low_pmi_bigrams(self._threshold_coef, df).index
        infrequent_terms = df[df.sum(axis=1) < self._min_freq].index
        filtered_term_doc_mat = term_doc_matrix.remove_terms(set(low_pmi_bigrams) | set(infrequent_terms))
        try:
            filtered_term_doc_mat.get_term_freq_df()
        except ValueError:
            raise AtLeastOneCategoryHasNoTermsException()
        return filtered_term_doc_mat

def filter(self, term_doc_matrix):
    """
		Parameters
		----------
		term_doc_matrix  : TermDocMatrix

		Returns
		-------
		TermDocMatrix pmi-filterd term doc matrix
		"""
    df = term_doc_matrix.get_term_freq_df()
    if len(df) == 0:
        return term_doc_matrix
    low_pmi_bigrams = get_low_pmi_bigrams(self._threshold_coef, df).index
    infrequent_terms = df[df.sum(axis=1) < self._min_freq].index
    filtered_term_doc_mat = term_doc_matrix.remove_terms(set(low_pmi_bigrams) | set(infrequent_terms))
    try:
        filtered_term_doc_mat.get_term_freq_df()
    except ValueError:
        raise AtLeastOneCategoryHasNoTermsException()
    return filtered_term_doc_mat

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

def get_num_terms(self):
    return len(self.term_category_freq_df)

def get_num_metadata(self):
    return len(self.metadata_frequency_df)

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

def inject_category_scores(self, category_scores: Union[np.array, List[List[float]]]) -> Self:
    if type(category_scores) == np.array:
        category_scores = category_scores.tolist()
    if not len(category_scores) == self.term_doc_matrix.get_num_categories():
        raise Exception('Number of rows in category scores must be the number of categories in corpus')
    if not all((len(scores) == self.term_doc_matrix.get_num_terms(non_text=self.scatterchartdata.use_non_text_features) for scores in category_scores)):
        raise Exception('Number of columns in category scores must be the number of terms or metadata in corpus')
    self.category_scores = category_scores
    return self

def _get_term_category_frequencies(self):
    return self.term_doc_matrix.get_term_category_frequencies(self.scatterchartdata)

def _add_jitter(self, vec):
    """
        :param vec: array to jitter
        :return: array, jittered version of arrays
        """
    if self.scatterchartdata.jitter == 0 or self.scatterchartdata.jitter is None:
        return vec
    return vec + np.random.rand(1, len(vec))[0] * self.scatterchartdata.jitter

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

def get_num_metadata(self) -> int:
    """
        Returns
        -------
        int, number of unique metadata items
        """
    return len(self.get_metadata())

def get_terms(self, use_metadata=False) -> List[str]:
    """
        Returns
        -------
        np.array of unique terms
        """
    if use_metadata:
        return self.get_metadata()
    return self._term_idx_store._i2val

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

def _make_new_term_doc_matrix(self, new_X=None, new_mX=None, new_y=None, new_term_idx_store=None, new_category_idx_store=None, new_metadata_idx_store=None, new_y_mask=None) -> Self:
    return TermDocMatrixWithoutCategories(X=new_X if new_X is not None else self._X, mX=new_mX if new_mX is not None else self._mX, term_idx_store=new_term_idx_store if new_term_idx_store is not None else self._term_idx_store, metadata_idx_store=new_metadata_idx_store if new_metadata_idx_store is not None else self._metadata_idx_store, unigram_frequency_path=self._unigram_frequency_path)

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

def metadata_in_use(self) -> bool:
    """
        Returns True if metadata values are in term doc matrix.

        Returns
        -------
        bool
        """
    return len(self._metadata_idx_store) > 0

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

def get_freq_df(self, use_metadata=False, label_append=' freq'):
    if use_metadata:
        return self.get_metadata_freq_df(label_append)
    return self.get_term_freq_df(label_append)

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

def _get_accuracy_and_baseline_accuracy(self, y, y_hat):
    acc = sum(y_hat == y) * 1.0 / len(y)
    baseline = max([sum(y), len(y) - sum(y)]) * 1.0 / len(y)
    return (acc, baseline)

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

class Tok:

    def __init__(self, pos, lem, token, ent_type, tag, is_punct=False, idx=None):
        self.pos_ = pos
        self.lemma_ = lem
        self.lower_ = token.lower()
        self.orth_ = token
        self.ent_type_ = ent_type
        self.tag_ = tag
        self.is_punct = is_punct
        self.idx = idx

    def __str__(self):
        return self.lower_

    def __len__(self):
        return len(self.lower_)

def __len__(self):
    return len(self.lower_)

class Doc:

    def __init__(self, sents, raw=None, noun_chunks=[]):
        self.sents = sents
        if raw is None:
            self.string = ' '.join((''.join([tok.lower_ for tok in sent]) for sent in sents))
        else:
            self.string = raw
        self.text = self.string
        self.noun_chunks = noun_chunks
        self.toks = []
        for sent in sents:
            self.toks += sent

    def __str__(self):
        return self.string

    def __repr__(self):
        return self.string

    def __iter__(self):
        for sent in self.sents:
            for tok in sent:
                yield tok

    def __getitem__(self, idx):
        return self.toks[idx]

    def __len__(self):
        return len(self.toks)

def __len__(self):
    return len(self.toks)

def build_sparse_matrices(y, X_factory, mX_factory):
    return build_sparse_matrices_with_num_docs(len(y), X_factory, mX_factory)

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

def _apply_pipeline_and_get_build_instance(self, X_factory, mX_factory, df, parse_pipeline, term_idx_store, metadata_idx_store):
    df.apply(parse_pipeline.parse, axis=1)
    X, mX = build_sparse_matrices_with_num_docs(len(df), X_factory, mX_factory)
    tdm = TermDocMatrixWithoutCategories(X, mX, term_idx_store, metadata_idx_store)
    return tdm

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

class DomainCompactor(object):

    def __init__(self, doc_domains, min_domain_count=None, max_domain_count=None):
        """

		Parameters
		----------
		doc_domains : np.array like
			Length of documents in corpus. Specifies a single domain for each document.
		min_domain_count : int, None
			Term should appear in at least this number of domains
			Default 0
		max_domain_count : int, None
			Term should appear in at most this number of domains
			Default is the number of domains in doc_domains
		"""
        self.doc_domains = doc_domains
        if max_domain_count is None and min_domain_count is None:
            raise NeedsMaxOrMinDomainCountException('Either max_domain_count or min_domain_count must be entered')
        self.min_domain_count = 0 if min_domain_count is None else min_domain_count
        self.max_domain_count = len(doc_domains) if max_domain_count is None else max_domain_count

    def compact(self, term_doc_matrix, non_text=False):
        """
		Parameters
		----------
		term_doc_matrix : TermDocMatrix
			Term document matrix object to compact

		Returns
		-------
		New term doc matrix
		"""
        domain_mat = CombineDocsIntoDomains(term_doc_matrix).get_new_term_doc_mat(self.doc_domains, non_text)
        domain_count = (domain_mat > 0).sum(axis=0)
        valid_term_mask = (self.max_domain_count >= domain_count) & (domain_count >= self.min_domain_count)
        indices_to_compact = np.arange(self._get_num_terms(term_doc_matrix, non_text))[~valid_term_mask.A1]
        return term_doc_matrix.remove_terms_by_indices(indices_to_compact, non_text=non_text)

    def _get_num_terms(self, term_doc_matrix, non_text):
        return term_doc_matrix.get_num_metadata() if non_text else term_doc_matrix.get_num_terms()

def __init__(self, doc_domains, min_domain_count=None, max_domain_count=None):
    """

		Parameters
		----------
		doc_domains : np.array like
			Length of documents in corpus. Specifies a single domain for each document.
		min_domain_count : int, None
			Term should appear in at least this number of domains
			Default 0
		max_domain_count : int, None
			Term should appear in at most this number of domains
			Default is the number of domains in doc_domains
		"""
    self.doc_domains = doc_domains
    if max_domain_count is None and min_domain_count is None:
        raise NeedsMaxOrMinDomainCountException('Either max_domain_count or min_domain_count must be entered')
    self.min_domain_count = 0 if min_domain_count is None else min_domain_count
    self.max_domain_count = len(doc_domains) if max_domain_count is None else max_domain_count

def compact(self, term_doc_matrix, non_text=False):
    """
		Parameters
		----------
		term_doc_matrix : TermDocMatrix
			Term document matrix object to compact

		Returns
		-------
		New term doc matrix
		"""
    domain_mat = CombineDocsIntoDomains(term_doc_matrix).get_new_term_doc_mat(self.doc_domains, non_text)
    domain_count = (domain_mat > 0).sum(axis=0)
    valid_term_mask = (self.max_domain_count >= domain_count) & (domain_count >= self.min_domain_count)
    indices_to_compact = np.arange(self._get_num_terms(term_doc_matrix, non_text))[~valid_term_mask.A1]
    return term_doc_matrix.remove_terms_by_indices(indices_to_compact, non_text=non_text)

def _get_num_terms(self, term_doc_matrix, non_text):
    return term_doc_matrix.get_num_metadata() if non_text else term_doc_matrix.get_num_terms()

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

def _limit_to_redundant_unigrams(self, pairs, tdf_vals):
    return pairs[np.all(tdf_vals[pairs[:, 1]] <= tdf_vals[pairs[:, 0]] + self.redundancy_slack, axis=1)]

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

def set_use_non_text_features(self, use_non_text_features: bool) -> 'BaseAssociationCompactor':
    self.scorer = self.scorer.set_use_non_text_features(use_non_text_features)
    return self

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

def test_get_num_terms(self):
    self.assertEqual(self.term_cat_freq.get_num_terms(), 20)

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

class TestDenseRankCharacteristicness(TestCase):

    def test_get_scores(self):
        c = get_hamlet_term_doc_matrix()
        zero_point, scores = DenseRankCharacteristicness().get_scores(c)
        self.assertGreater(zero_point, 0)
        self.assertLessEqual(zero_point, 1)
        self.assertGreater(len(scores), 100)

def test_get_scores(self):
    c = get_hamlet_term_doc_matrix()
    zero_point, scores = DenseRankCharacteristicness().get_scores(c)
    self.assertGreater(zero_point, 0)
    self.assertLessEqual(zero_point, 1)
    self.assertGreater(len(scores), 100)

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

@classmethod
def setUp(cls):
    cls.tdm = make_a_test_term_doc_matrix()

def test_get_num_terms(self):
    self.assertEqual(self.tdm.get_num_terms(), self.tdm._X.shape[1])

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

def test_compact(self):
    x = get_hamlet_term_doc_matrix().compact(CompactTerms(minimum_term_count=3))
    self.assertEqual(type(x), TermDocMatrix)

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

def test_get_term_doc_mat(self):
    hamlet = get_hamlet_term_doc_matrix()
    X = hamlet.get_term_doc_mat()
    np.testing.assert_array_equal(X.shape, (hamlet.get_num_docs(), hamlet.get_num_terms()))

def test_get_metadata_doc_mat(self):
    hamlet_meta = build_hamlet_jz_corpus_with_meta()
    mX = hamlet_meta.get_metadata_doc_mat()
    np.testing.assert_array_equal(mX.shape, (hamlet_meta.get_num_docs(), len(hamlet_meta.get_metadata_freq_df())))

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

def test_extra_features(self):
    corpus = build_hamlet_jz_corpus_with_meta()
    d = DocsAndLabelsFromCorpus(corpus).use_non_text_features()
    metadata = ['meta%s' % i for i in range(corpus.get_num_docs())]
    output = d.get_labels_and_texts_and_meta(metadata)
    extra_val = [{'cat3': 1, 'cat4': 2}, {'cat4': 2}, {'cat5': 1, 'cat3': 2}, {'cat9': 1, 'cat6': 2}, {'cat3': 1, 'cat4': 2}, {'cat1': 2, 'cat2': 1}, {'cat5': 1, 'cat2': 2}, {'cat3': 2, 'cat4': 1}]
    extra_val = [{'cat1': 2}, {'cat1': 2}, {'cat1': 2}, {'cat1': 2}, {'cat1': 2}, {'cat1': 2}, {'cat1': 2}, {'cat1': 2}]
    output['labels'] = list(output['labels'])
    self.assertEqual(output, {'categories': ['hamlet', 'jay-z/r. kelly'], 'texts': ["what art thou that usurp'st this time of night,", 'together with that fair and warlike form', 'in which the majesty of buried denmark', 'did sometimes march? by heaven i charge thee, speak!', 'halt! who goes there?', 'it is i sire tone from brooklyn.', 'well, speak up man what is it?', 'news from the east sire! the best of both worlds has returned!'], 'meta': ['meta0', 'meta1', 'meta2', 'meta3', 'meta4', 'meta5', 'meta6', 'meta7'], 'labels': [0, 0, 0, 0, 1, 1, 1, 1], 'extra': extra_val})

class TestCorpusFromScikit(TestCase):

    def test_main(self):
        pass

    def _te_ss_t_build(self):
        from sklearn.datasets import fetch_20newsgroups
        from sklearn.feature_extraction.text import CountVectorizer
        newsgroups_train = fetch_20newsgroups(subset='train', remove=('headers', 'footers', 'quotes'))
        count_vectorizer = CountVectorizer()
        X_counts = count_vectorizer.fit_transform(newsgroups_train.data)
        corpus = CorpusFromScikit(X=X_counts, y=newsgroups_train.target, feature_vocabulary=count_vectorizer.vocabulary_, category_names=newsgroups_train.target_names, raw_texts=newsgroups_train.data).build()
        self.assertEqual(corpus.get_categories()[:2], ['alt.atheism', 'comp.graphics'])
        self.assertEqual(corpus.get_term_freq_df().assign(score=corpus.get_scaled_f_scores('alt.atheism')).sort_values(by='score', ascending=False).index.tolist()[:5], ['atheism', 'atheists', 'islam', 'atheist', 'belief'])
        self.assertGreater(len(corpus.get_texts()[0]), 5)

def _te_ss_t_build(self):
    from sklearn.datasets import fetch_20newsgroups
    from sklearn.feature_extraction.text import CountVectorizer
    newsgroups_train = fetch_20newsgroups(subset='train', remove=('headers', 'footers', 'quotes'))
    count_vectorizer = CountVectorizer()
    X_counts = count_vectorizer.fit_transform(newsgroups_train.data)
    corpus = CorpusFromScikit(X=X_counts, y=newsgroups_train.target, feature_vocabulary=count_vectorizer.vocabulary_, category_names=newsgroups_train.target_names, raw_texts=newsgroups_train.data).build()
    self.assertEqual(corpus.get_categories()[:2], ['alt.atheism', 'comp.graphics'])
    self.assertEqual(corpus.get_term_freq_df().assign(score=corpus.get_scaled_f_scores('alt.atheism')).sort_values(by='score', ascending=False).index.tolist()[:5], ['atheism', 'atheists', 'islam', 'atheist', 'belief'])
    self.assertGreater(len(corpus.get_texts()[0]), 5)

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

def test_japanese(self):
    try:
        __import__('tinysegmenter')
    except ImportError:
        return
    doc = japanese_nlp(self.japanese_text)
    sent1 = doc.sents[0]
    self.assertGreater(len(str(sent1)), 10)
    self.assertEqual(len(doc.sents), 7)

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

class TestAutoTermSelector(TestCase):

    def test_reduce_terms(self):
        tdm = make_a_test_term_doc_matrix()
        scores = tdm.get_term_freq_df().sum(axis=1) % 10
        new_tdm = AutoTermSelector.reduce_terms(tdm, scores, num_term_to_keep=10)
        self.assertLessEqual(len(new_tdm.get_term_freq_df().index), 10)
        self.assertEqual(len(tdm.get_term_freq_df().index), 58)

    def test_get_selected_terms(self):
        tdm = make_a_test_term_doc_matrix()
        scores = tdm.get_term_freq_df().sum(axis=1) % 10
        selected_terms = AutoTermSelector.get_selected_terms(tdm, scores, num_term_to_keep=10)
        self.assertLessEqual(len(selected_terms), 10)
        self.assertEqual(len(tdm.get_term_freq_df().index), 58)

def test_reduce_terms(self):
    tdm = make_a_test_term_doc_matrix()
    scores = tdm.get_term_freq_df().sum(axis=1) % 10
    new_tdm = AutoTermSelector.reduce_terms(tdm, scores, num_term_to_keep=10)
    self.assertLessEqual(len(new_tdm.get_term_freq_df().index), 10)
    self.assertEqual(len(tdm.get_term_freq_df().index), 58)

def test_get_selected_terms(self):
    tdm = make_a_test_term_doc_matrix()
    scores = tdm.get_term_freq_df().sum(axis=1) % 10
    selected_terms = AutoTermSelector.get_selected_terms(tdm, scores, num_term_to_keep=10)
    self.assertLessEqual(len(selected_terms), 10)
    self.assertEqual(len(tdm.get_term_freq_df().index), 58)

class TestDomainCompactor(TestCase):

    def test_compact(self):
        hamlet = get_hamlet_term_doc_matrix()
        domains = np.arange(hamlet.get_num_docs()) % 3
        with self.assertRaises(NeedsMaxOrMinDomainCountException):
            hamlet_compact = hamlet.compact(DomainCompactor(domains))
        hamlet_compact = hamlet.compact(DomainCompactor(domains, min_domain_count=2))
        self.assertLess(hamlet_compact.get_num_terms(), hamlet.get_num_terms())
        self.assertEqual(hamlet_compact.get_num_docs(), hamlet.get_num_docs())
        hamlet_compact = hamlet.compact(DomainCompactor(domains, max_domain_count=2))
        self.assertLess(hamlet_compact.get_num_terms(), hamlet.get_num_terms())
        self.assertEqual(hamlet_compact.get_num_docs(), hamlet.get_num_docs())
        hamlet_compact = hamlet.compact(DomainCompactor(domains, max_domain_count=2, min_domain_count=2))
        self.assertLess(hamlet_compact.get_num_terms(), hamlet.get_num_terms())
        self.assertEqual(hamlet_compact.get_num_docs(), hamlet.get_num_docs())

def test_compact(self):
    hamlet = get_hamlet_term_doc_matrix()
    domains = np.arange(hamlet.get_num_docs()) % 3
    with self.assertRaises(NeedsMaxOrMinDomainCountException):
        hamlet_compact = hamlet.compact(DomainCompactor(domains))
    hamlet_compact = hamlet.compact(DomainCompactor(domains, min_domain_count=2))
    self.assertLess(hamlet_compact.get_num_terms(), hamlet.get_num_terms())
    self.assertEqual(hamlet_compact.get_num_docs(), hamlet.get_num_docs())
    hamlet_compact = hamlet.compact(DomainCompactor(domains, max_domain_count=2))
    self.assertLess(hamlet_compact.get_num_terms(), hamlet.get_num_terms())
    self.assertEqual(hamlet_compact.get_num_docs(), hamlet.get_num_docs())
    hamlet_compact = hamlet.compact(DomainCompactor(domains, max_domain_count=2, min_domain_count=2))
    self.assertLess(hamlet_compact.get_num_terms(), hamlet.get_num_terms())
    self.assertEqual(hamlet_compact.get_num_docs(), hamlet.get_num_docs())

class WV:

    def __init__(self, vocab):
        self.key_to_index = {v: k for k, v in enumerate(vocab)}

    def __getitem__(self, item):
        assert item in self.key_to_index.keys()
        return np.zeros(30)

def __getitem__(self, item):
    assert item in self.key_to_index.keys()
    return np.zeros(30)

class MockWord2Vec:

    def __init__(self, vocab):
        self.wv = WV(vocab)
        self.corpus_count = 5

    def train(self, *args, **kwargs):
        pass

    def build_vocab(self, *args):
        pass

    def __getitem__(self, item):
        assert item in self.wv.key_to_index.keys()
        return np.zeros(30)

def __getitem__(self, item):
    assert item in self.wv.key_to_index.keys()
    return np.zeros(30)

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

class TestCombineDocsIntoDomains(TestCase):

    def test_get_new_term_doc_mat(self):
        hamlet = get_hamlet_term_doc_matrix()
        domains = np.arange(hamlet.get_num_docs()) % 3
        tdm = CombineDocsIntoDomains(hamlet).get_new_term_doc_mat(domains)
        self.assertEquals(tdm.shape, (3, hamlet.get_num_terms()))
        self.assertEquals(tdm.sum(), hamlet.get_term_doc_mat().sum())

def test_get_new_term_doc_mat(self):
    hamlet = get_hamlet_term_doc_matrix()
    domains = np.arange(hamlet.get_num_docs()) % 3
    tdm = CombineDocsIntoDomains(hamlet).get_new_term_doc_mat(domains)
    self.assertEquals(tdm.shape, (3, hamlet.get_num_terms()))
    self.assertEquals(tdm.sum(), hamlet.get_term_doc_mat().sum())

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

def test_absolute_frequency_ranker(self):
    tdm = make_a_test_term_doc_matrix()
    ranker = AbsoluteFrequencyRanker(tdm)
    rank_df = ranker.get_ranks()
    self.assertEqual(len(rank_df), 58)
    self.assertEqual(rank_df.loc['hello'].tolist(), [1, 0])
    self.assertEqual(rank_df.loc['blah'].tolist(), [0, 3])
    self.assertEqual(rank_df.loc['name'].tolist(), [1, 1])

class TestCorpusFromPandas(TestCase):

    def test_term_doc(self):
        self.assertIsInstance(self.corpus, CorpusDF)
        self.assertEqual(set(self.corpus.get_categories()), set(['hamlet', 'jay-z/r. kelly', '???']))
        self.assertEqual(self.corpus.get_num_docs(), 10)
        term_doc_df = self.corpus.get_term_freq_df()
        self.assertEqual(term_doc_df.loc['of'].sum(), 3)
        self.corpus.get_df()

    def test_chinese_error(self):
        with self.assertRaises(Exception):
            CorpusFromPandas(self.df, 'category', 'text', nlp=chinese_nlp).build()

    def test_get_texts(self):
        self.assertTrue(all(self.df['text'] == self.corpus.get_texts()))

    def test_search(self):
        expected = pd.DataFrame({'text': ["What art thou that usurp'st this time of night,", 'Together with that fair and warlike form'], 'category': ['hamlet', 'hamlet'], 'index': [0, 1]})
        self.assertIsInstance(self.corpus, CorpusDF)
        returned = self.corpus.search('that')
        pd.testing.assert_frame_equal(expected, returned[expected.columns])

    def test_search_bigram(self):
        expected = pd.DataFrame({'text': [u'Well, speak up man what is it?', u'Speak up, speak up, this is a repeat bigram.'], 'category': ['jay-z/r. kelly', '???'], 'index': [7, 9]}).reset_index(drop=True)
        self.assertIsInstance(self.corpus, CorpusDF)
        returned = self.corpus.search('speak up').reset_index(drop=True)
        pd.testing.assert_frame_equal(expected, returned[expected.columns])

    def test_search_index(self):
        expected = np.array([7, 9])
        self.assertIsInstance(self.corpus, CorpusDF)
        returned = self.corpus.search_index('speak up')
        np.testing.assert_array_equal(expected, returned)

    @classmethod
    def setUp(cls):
        categories, documents = get_docs_categories()
        cls.df = pd.DataFrame({'category': categories, 'text': documents})
        cls.corpus = CorpusFromPandas(cls.df, 'category', 'text', nlp=whitespace_nlp).build()

def test_term_doc(self):
    self.assertIsInstance(self.corpus, CorpusDF)
    self.assertEqual(set(self.corpus.get_categories()), set(['hamlet', 'jay-z/r. kelly', '???']))
    self.assertEqual(self.corpus.get_num_docs(), 10)
    term_doc_df = self.corpus.get_term_freq_df()
    self.assertEqual(term_doc_df.loc['of'].sum(), 3)
    self.corpus.get_df()

class TestLogOddsRatioUninformativeDirichletPrior(TestCase):

    def test_get_p_vals(self):
        tdm = build_hamlet_jz_term_doc_mat()
        df = tdm.get_term_freq_df()
        X = df[['hamlet freq', 'jay-z/r. kelly freq']].values
        pvals = LogOddsRatioUninformativeDirichletPrior().get_p_vals(X)
        self.assertGreaterEqual(min(pvals), 0)
        self.assertLessEqual(min(pvals), 1)

    def test_z_to_p_val(self):
        np.testing.assert_almost_equal(z_to_p_val(0), 0.5)
        np.testing.assert_almost_equal(z_to_p_val(1.96), 0.9750021048517795)
        np.testing.assert_almost_equal(z_to_p_val(-1.96), 0.024997895148220428)
        self.assertLessEqual(z_to_p_val(-0.1), z_to_p_val(0))
        self.assertLessEqual(z_to_p_val(0), z_to_p_val(0.1))
        self.assertLessEqual(z_to_p_val(0.1), z_to_p_val(0.2))

def test_get_p_vals(self):
    tdm = build_hamlet_jz_term_doc_mat()
    df = tdm.get_term_freq_df()
    X = df[['hamlet freq', 'jay-z/r. kelly freq']].values
    pvals = LogOddsRatioUninformativeDirichletPrior().get_p_vals(X)
    self.assertGreaterEqual(min(pvals), 0)
    self.assertLessEqual(min(pvals), 1)

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

class TestTermDocMatrixFromScikit(TestCase):

    def test_build(self):
        from sklearn.feature_extraction.text import CountVectorizer
        categories, docs = get_docs_categories_semiotic()
        idx_store = IndexStore()
        y = np.array([idx_store.getidx(c) for c in categories])
        count_vectorizer = CountVectorizer()
        X_counts = count_vectorizer.fit_transform(docs)
        term_doc_mat = TermDocMatrixFromScikit(X=X_counts, y=y, feature_vocabulary=count_vectorizer.vocabulary_, category_names=idx_store.values()).build()
        self.assertEqual(term_doc_mat.get_categories()[:2], ['hamlet', 'jay-z/r. kelly'])
        self.assertEqual(term_doc_mat.get_term_freq_df().assign(score=term_doc_mat.get_scaled_f_scores('hamlet')).sort_values(by='score', ascending=False).index.tolist()[:5], ['that', 'march', 'did', 'majesty', 'sometimes'])

def test_build(self):
    from sklearn.feature_extraction.text import CountVectorizer
    categories, docs = get_docs_categories_semiotic()
    idx_store = IndexStore()
    y = np.array([idx_store.getidx(c) for c in categories])
    count_vectorizer = CountVectorizer()
    X_counts = count_vectorizer.fit_transform(docs)
    term_doc_mat = TermDocMatrixFromScikit(X=X_counts, y=y, feature_vocabulary=count_vectorizer.vocabulary_, category_names=idx_store.values()).build()
    self.assertEqual(term_doc_mat.get_categories()[:2], ['hamlet', 'jay-z/r. kelly'])
    self.assertEqual(term_doc_mat.get_term_freq_df().assign(score=term_doc_mat.get_scaled_f_scores('hamlet')).sort_values(by='score', ascending=False).index.tolist()[:5], ['that', 'march', 'did', 'majesty', 'sometimes'])

def _collect_term_inter_arrivals_on_concatenated_doc(doc, new_offsets):
    num_tokens_before_first = None
    last_end = 0
    inter_arrivals = []
    for offset_i, (start_offset, end_offset) in enumerate(new_offsets):
        tokens = doc.char_span(last_end, start_offset, alignment_mode='contract')
        if tokens is None:
            tokens = []
        num_tokens_in_between = len(tokens)
        if num_tokens_in_between == 0:
            num_tokens_in_between = 1
        if offset_i == 0:
            num_tokens_before_first = num_tokens_in_between
        else:
            inter_arrivals.append(num_tokens_in_between)
        last_end = end_offset
    if num_tokens_before_first is not None:
        tokens = doc.char_span(last_end, len(str(doc)), alignment_mode='contract')
        if tokens is None:
            tokens = []
        last_token_count = num_tokens_before_first + len(tokens)
        if last_token_count is 0:
            last_token_count = 1
        inter_arrivals.append(last_token_count)
    return inter_arrivals

class InterArrivalCounts:

    def __init__(self, corpus: OffsetCorpus, non_text: bool, domains_to_preserve: Optional[List[str]]=None, verbose: bool=False, random_generator: Optional[np.random._generator.Generator]=None):
        self.corpus = corpus
        self.rng = random_generator
        self.domains_to_preserve = domains_to_preserve
        if not non_text:
            assert inherits_from(type(corpus), 'OffsetCorpus')
        self.term_inter_arrivals = {}
        self.term_category_inter_arrivals = {}
        self.__populate_inter_arrival_stats(verbose=verbose)

    def __populate_inter_arrival_stats(self, verbose: bool):
        it = enumerate(self.corpus.get_terms(use_metadata=True))
        if verbose:
            it = tqdm(it, total=self.corpus.get_num_metadata())
        for term_idx, term in it:
            term_offsets = self.corpus.get_offsets()[term]
            interarrivals = []
            interarrival_cat = {}
            for doc_i, row in self.corpus.get_df().iterrows():
                cat = row[self.corpus.get_category_column()]
                doc = row[self.corpus.get_parsed_column()]
                last_end = None
                interarrival_cat.setdefault(cat, [])
                term_doc_offsets = term_offsets.get(doc_i, [])
                if term_doc_offsets:
                    for offset_start, offset_end in term_doc_offsets:
                        if self.__not_the_first_example_of_a_term(last_end):
                            intervening_token_count = self.__get_intervening_token_count(doc, last_end, offset_start)
                            self.__append_inter_arrival(cat, interarrival_cat, interarrivals, intervening_token_count)
                        last_end = offset_end
                    end_inter_arrival_tokens = self.__get_intervening_tokens_for_final_term(doc, term_doc_offsets)
                    self.__append_inter_arrival(cat, interarrival_cat, interarrivals, end_inter_arrival_tokens)
            self.term_inter_arrivals[term] = interarrivals
            self.term_category_inter_arrivals[term] = copy(interarrival_cat)

    def __get_intervening_tokens_for_final_term(self, doc, term_doc_offsets):
        tokens_before_first = doc.char_span(0, term_doc_offsets[0][0], alignment_mode='contract')
        token_count_before_first = 0 if tokens_before_first is None else len(tokens_before_first)
        tokens_after_last = doc.char_span(term_doc_offsets[-1][1], len(str(doc)), alignment_mode='contract')
        token_count_after_last = 0 if tokens_after_last is None else len(tokens_after_last)
        end_inter_arrival_tokens = token_count_before_first + token_count_after_last + 1
        return end_inter_arrival_tokens

    def __get_intervening_token_count(self, doc, last_end, offset_start):
        intervening_tokens = doc.char_span(last_end, offset_start, alignment_mode='contract')
        intervening_token_count = (0 if intervening_tokens is None else len(intervening_tokens)) + 1
        return intervening_token_count

    def __not_the_first_example_of_a_term(self, last_end: Optional[int]) -> bool:
        return last_end is not None

    def __append_inter_arrival(self, cat: str, interarrival_cat: Dict, interarrivals, intervening_token_count: int) -> None:
        interarrivals.append(intervening_token_count)
        interarrival_cat[cat].append(intervening_token_count)

def __get_intervening_tokens_for_final_term(self, doc, term_doc_offsets):
    tokens_before_first = doc.char_span(0, term_doc_offsets[0][0], alignment_mode='contract')
    token_count_before_first = 0 if tokens_before_first is None else len(tokens_before_first)
    tokens_after_last = doc.char_span(term_doc_offsets[-1][1], len(str(doc)), alignment_mode='contract')
    token_count_after_last = 0 if tokens_after_last is None else len(tokens_after_last)
    end_inter_arrival_tokens = token_count_before_first + token_count_after_last + 1
    return end_inter_arrival_tokens

def __get_intervening_token_count(self, doc, last_end, offset_start):
    intervening_tokens = doc.char_span(last_end, offset_start, alignment_mode='contract')
    intervening_token_count = (0 if intervening_tokens is None else len(intervening_tokens)) + 1
    return intervening_token_count

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

def get_frequency(self):
    if len(self.f.shape) == 1:
        return self.f
    return self.f.A1

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

def __get_coef_df(self) -> pd.DataFrame:
    tdm = self.corpus_.get_term_doc_mat(non_text=self.non_text_)
    tdmtfidf = TfidfTransformer().fit_transform(tdm)
    coefs = np.zeros(shape=(self.corpus_.get_num_categories(), tdm.shape[1]), dtype=float)
    for i, cat in enumerate(self.corpus_.get_categories()):
        y = self.corpus_.get_category_ids() == i
        clf = LogisticRegression(penalty='l2', C=5.0, max_iter=4000, tol=1e-06, solver='liblinear').fit(tdmtfidf, y)
        coefs[i, :] = clf.coef_
    return pd.DataFrame(coefs.T, index=self.corpus_.get_terms(use_metadata=self.non_text_), columns=[str(x) + ' coef' for x in self.corpus_.get_categories()])

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

def __len__(self) -> int:
    return len(self._i2val)

class CoefficientBase:

    def __init__(self, use_non_text=False):
        self.use_non_text = use_non_text

    def _get_tdm(self, corpus):
        return corpus.get_metadata_doc_mat() if self.use_non_text else corpus.get_term_doc_mat()

    def _get_terms(self, corpus):
        return corpus.get_metadata() if self.use_non_text else corpus.get_terms()

def _get_tdm(self, corpus):
    return corpus.get_metadata_doc_mat() if self.use_non_text else corpus.get_term_doc_mat()

def _get_terms(self, corpus):
    return corpus.get_metadata() if self.use_non_text else corpus.get_terms()

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

def project_with_alternative_dimensions(self, x_dim, y_dim):
    return CategoryProjectionWithDoc2Vec(self.category_corpus, self.category_counts, self.projection, x_dim, y_dim, doc2vec_model=self.doc2vec_model)

def use_alternate_projection(self, projection):
    return CategoryProjectionWithDoc2Vec(self.category_corpus, self.category_counts, projection, self.x_dim, self.y_dim, doc2vec_model=self.doc2vec_model)

def project_raw_corpus(category_corpus, projection, projection_type=CategoryProjection, term_projection=None, x_dim=0, y_dim=1):
    return projection_type(category_corpus, category_corpus.get_term_freq_df(), projection, x_dim, y_dim, term_projection)

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

def weight(self, category_counts):
    if self.weighter_ is None:
        return category_counts
    return self.weighter_.fit_transform(category_counts)

def select(self, corpus):
    if self.selector_ is None:
        return corpus
    if self.use_metadata_:
        self.selector_ = self.selector_.set_use_non_text_features(self.use_metadata_)
    return corpus.select(self.selector_, non_text=self.use_metadata_)

def _get_category_metadata_corpus(self, corpus):
    return self.select(corpus).use_categories_as_metadata()

def _get_category_metadata_corpus_and_replace_terms(self, corpus):
    return self.select(corpus).use_categories_as_metadata_and_replace_terms()

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

class CombineDocsIntoDomains(object):

    def __init__(self, term_doc_matrix):
        """
		Parameters
		----------
		term_doc_matrix : TermDocMatrix
		"""
        self.term_doc_matrix = term_doc_matrix

    def get_new_term_doc_mat(self, doc_domains, non_text: bool=False):
        """
		Combines documents together that are in the same domain

		Parameters
		----------
		doc_domains : array-like
		non_text: bool

		Returns
		-------
		scipy.sparse.csr_matrix


		"""
        assert len(doc_domains) == self.term_doc_matrix.get_num_docs()
        doc_domain_set = set(doc_domains)
        num_terms = self.term_doc_matrix.get_num_metadata() if non_text else self.term_doc_matrix.get_num_terms()
        num_domains = len(doc_domain_set)
        domain_mat = lil_matrix((num_domains, num_terms), dtype=int)
        X = self.term_doc_matrix.get_metadata_doc_mat() if non_text else self.term_doc_matrix.get_term_doc_mat()
        for i, domain in enumerate(doc_domain_set):
            domain_mat[i, :] = X[np.array(doc_domains == domain)].sum(axis=0)
        return domain_mat.tocsr()

def get_new_term_doc_mat(self, doc_domains, non_text: bool=False):
    """
		Combines documents together that are in the same domain

		Parameters
		----------
		doc_domains : array-like
		non_text: bool

		Returns
		-------
		scipy.sparse.csr_matrix


		"""
    assert len(doc_domains) == self.term_doc_matrix.get_num_docs()
    doc_domain_set = set(doc_domains)
    num_terms = self.term_doc_matrix.get_num_metadata() if non_text else self.term_doc_matrix.get_num_terms()
    num_domains = len(doc_domain_set)
    domain_mat = lil_matrix((num_domains, num_terms), dtype=int)
    X = self.term_doc_matrix.get_metadata_doc_mat() if non_text else self.term_doc_matrix.get_term_doc_mat()
    for i, domain in enumerate(doc_domain_set):
        domain_mat[i, :] = X[np.array(doc_domains == domain)].sum(axis=0)
    return domain_mat.tocsr()

def extract_JK(pos_seq):
    """The 'JK' method in Handler et al. 2016.
	Returns token positions of valid ngrams."""

    def find_ngrams(input_list, num_):
        """get ngrams of len n from input list"""
        return zip(*[input_list[i:] for i in range(num_)])
    patterns = set(['AN', 'NN', 'AAN', 'ANN', 'NAN', 'NNN', 'NPN'])
    pos_seq = [tag2coarse.get(tag, 'O') for tag in pos_seq]
    pos_seq = [(i, p) for i, p in enumerate(pos_seq)]
    ngrams = [ngram for n in range(1, 4) for ngram in find_ngrams(pos_seq, n)]

    def stringify(s):
        return ''.join((a[1] for a in s))

    def positionify(s):
        return tuple((a[0] for a in s))
    ngrams = filter(lambda x: stringify(x) in patterns, ngrams)
    return [set(positionify(n)) for n in ngrams]

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

def set_doc_sizes(self, doc_sizes: np.array) -> 'CorpusBasedTermScorer':
    assert len(doc_sizes) == self.corpus_.get_num_docs()
    self._doc_sizes = doc_sizes
    return self

def _get_X(self):
    return self.term_ranker_.get_term_doc_mat()

def _get_index(self):
    return self.corpus_.get_metadata() if self.use_metadata_ else self.corpus_.get_terms()

def _get_num_terms(self):
    return self.corpus_.get_num_terms(non_text=self.use_metadata_)

def __get_f1_f2_from_args(self, args) -> Tuple[np.array, np.array]:
    f1, f2 = args
    assert len(f1) == len(f2)
    assert len(f1) == len(self._get_terms())
    return (f1, f2)

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

def lrc_df(f1: np.array, f2: np.array, n1: Union[int, np.array], n2: Union[int, np.array], conf_level: float=0.95, correct: bool=True, alternative: str='two sided') -> np.array:
    assert len(f1) == len(f2)
    assert np.all(f1 + f2 >= 1)
    score_df = lrc_score_df(f1=f1, f2=f2, n1=n1, n2=n2, conf_level=conf_level, correct=correct, alternative=alternative)
    return score_df

def lrc_score_df(f1: np.array, f2: np.array, n1: Union[int, np.array], n2: Union[int, np.array], conf_level: float=0.95, correct: bool=True, alternative: str='two sided') -> pd.DataFrame:
    return binom_confint(k=f1, n=f1 + f2, conf_level=conf_level, correct=correct, alternative=alternative).assign(P1=f1 / n1, P2=f2 / n2, Score=lambda df: np.where(df.P1 > df.P2, np.maximum(np.log2(n2 / n1 * df.lower / (1 - df.lower)), np.zeros(len(df))), np.minimum(np.log2(n2 / n1 * df.upper / (1 - df.upper)), np.zeros(len(df)))))

def safe_qbeta(p, shape1, shape2, lower_tail=True):
    assert len(p) == len(shape1) and len(p) == len(shape2)
    is_0 = shape1 <= 0
    is_1 = shape2 <= 0
    ok = ~(is_0 | is_1)
    x = np.zeros(len(p))
    x[ok] = qbeta(p[ok], shape1[ok], shape2[ok], lower_tail=lower_tail)
    x[is_0 & ~is_1] = 0
    x[is_1 & ~is_0] = 1
    x[is_0 & is_1] = np.nan
    return x

def binom_confint(k, n, conf_level=0.95, correct=True, alternative='two sided'):
    assert alternative in ('two sided', 'less', 'greater')
    assert np.all(k >= 0) and np.all(k <= n) and np.all(n >= 1)
    assert np.all(conf_level >= 0) and np.all(conf_level <= 1)
    alpha = (1 - conf_level) / 2 if alternative == 'two sided' else 1 - conf_level
    if correct:
        alpha = alpha / len(k)
    alpha = np.array([alpha] * len(k))
    lower = safe_qbeta(alpha, k, n - k + 1)
    upper = safe_qbeta(alpha, k + 1, n - k, lower_tail=False)
    return pd.DataFrame({'lower': lower if alternative in ['two sided', 'greater'] else [0] * len(k), 'upper': upper if alternative in ['two sided', 'less'] else [0] * len(k)})

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

def available_term_embeddings_from_corpus(self, corpus: 'TermDocMatrix') -> Tuple[List[str], np.array]:
    terms = [term for term in corpus.get_metadata() if term in self.term_stats]
    embeddings = np.array([self.term_stats[term].mean() for term in terms])
    return (terms, embeddings)

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

def __init__(self, width: int, n: int=0):
    self.width = width
    self.n = 0
    self.old_m = np.zeros(width)
    self.new_m = np.zeros(width)
    self.old_s = np.zeros(width)
    self.new_s = np.zeros(width)

def mean(self) -> np.array:
    return self.new_m if self.n else np.zeros(self.width)

def variance(self) -> np.array:
    return self.new_s / (self.n - 1) if self.n > 1 else np.zeros(self.width)

class AbsoluteFrequencyRanker(TermRanker):
    """Ranks terms by the number of times they occur in each category.

	"""

    def get_ranks(self, label_append=' freq'):
        """
		Returns
		-------
		pd.DataFrame

		"""
        if self._use_non_text_features:
            return self._corpus.get_metadata_freq_df(label_append=label_append)
        else:
            return self._corpus.get_term_freq_df(label_append=label_append)

def get_ranks(self, label_append=' freq'):
    """
		Returns
		-------
		pd.DataFrame

		"""
    if self._use_non_text_features:
        return self._corpus.get_metadata_freq_df(label_append=label_append)
    else:
        return self._corpus.get_term_freq_df(label_append=label_append)

class DocLengthNormalizedFrequencyRanker(TermRanker):
    """Ranks terms by their document-length adjusted frequency instead of their raw frequency.
	This means that each term has a document-specific weight of  #(t,d)/|d|.
	"""

    def get_ranks(self, label_append: str=' freq') -> pd.DataFrame:
        X = self.get_term_doc_mat()
        y = self._corpus.get_category_ids()
        doc_lengths = X.sum(axis=1)
        norm_x = np.nan_to_num(X / doc_lengths, 0)
        data = {}
        for i in set(y):
            cat = self._corpus.get_category_index_store().getval(i)
            data[cat + label_append] = norm_x[y == i, :].sum(axis=0).A1
        return pd.DataFrame(data, index=self._corpus.get_terms(use_metadata=self._use_non_text_features))

def get_ranks(self, label_append: str=' freq') -> pd.DataFrame:
    X = self.get_term_doc_mat()
    y = self._corpus.get_category_ids()
    doc_lengths = X.sum(axis=1)
    norm_x = np.nan_to_num(X / doc_lengths, 0)
    data = {}
    for i in set(y):
        cat = self._corpus.get_category_index_store().getval(i)
        data[cat + label_append] = norm_x[y == i, :].sum(axis=0).A1
    return pd.DataFrame(data, index=self._corpus.get_terms(use_metadata=self._use_non_text_features))

