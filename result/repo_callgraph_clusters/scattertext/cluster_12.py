# Cluster 12

class CorpusFromScikit(TermDocMatrixFromScikit):
    """
	Tie-in to incorporate sckit-learn's various vectorizers into Scattertext
	>>> from sklearn.datasets import fetch_20newsgroups
	>>> from sklearn.feature_extraction.text import CountVectorizer
	>>> from scattertext.CorpusFromScikit import CorpusFromScikit
	>>> newsgroups_train = fetch_20newsgroups(subset='train', remove=('headers', 'footers', 'quotes'))
	>>> count_vectorizer = CountVectorizer()
	>>> X_counts = count_vectorizer.fit_transform(newsgroups_train.data)
	>>> corpus = CorpusFromScikit(
	...     X=X_counts,
	...     y=newsgroups_train.target,
	...     feature_vocabulary=count_vectorizer.vocabulary_,
	...     category_names=newsgroups_train.target_names,
	...     raw_texts=newsgroups_train.data
	... ).build()
	"""

    def __init__(self, X, y, feature_vocabulary, category_names, raw_texts, unigram_frequency_path=None):
        """
		Parameters
		----------
		X: sparse matrix integer, giving term-document-matrix counts
		y: list, integer categories
		feature_vocabulary: dict (feat_name -> idx)
		category_names: list of category names (len of y)
		raw_texts: array-like of raw texts
		unigram_frequency_path: str (see TermDocMatrix)

		"""
        TermDocMatrixFromScikit.__init__(self, X, y, feature_vocabulary, category_names, unigram_frequency_path)
        self.raw_texts = raw_texts

    def build(self):
        """
		Returns
		-------
		Corpus
		"""
        constructor_kwargs = self._get_build_kwargs()
        if type(self.raw_texts) == list:
            constructor_kwargs['raw_texts'] = np.array(self.raw_texts)
        else:
            constructor_kwargs['raw_texts'] = self.raw_texts
        return Corpus(**constructor_kwargs)

def build(self):
    """
		Returns
		-------
		Corpus
		"""
    constructor_kwargs = self._get_build_kwargs()
    if type(self.raw_texts) == list:
        constructor_kwargs['raw_texts'] = np.array(self.raw_texts)
    else:
        constructor_kwargs['raw_texts'] = self.raw_texts
    return Corpus(**constructor_kwargs)

def get_low_pmi_bigrams(threshold_coef, word_freq_df):
    is_bigram = np.array([' ' in word for word in word_freq_df.index])
    unigram_freq = word_freq_df[~is_bigram].sum(axis=1)
    bigram_freq = word_freq_df[is_bigram].sum(axis=1)
    bigram_prob = bigram_freq / bigram_freq.sum()
    unigram_prob = unigram_freq / unigram_freq.sum()

    def get_pmi(bigram):
        try:
            return np.log(bigram_prob[bigram] / np.product([unigram_prob[word] for word in bigram.split(' ')])) / np.log(2)
        except:
            return 0
    low_pmi_bigrams = bigram_prob[bigram_prob.index.map(get_pmi) < threshold_coef * 2]
    return low_pmi_bigrams

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

class CorpusFromFeatureDict(object):

    def __init__(self, df, category_col, text_col, feature_col, metadata_col=None, parsed_col=None):
        """
		Parameters
		----------
		df : pd.DataFrame
		 contains category_col, and parse_col, were parsed col is entirely spacy docs
		category_col : str
				name of category column in convention_df
		text_col : str
				The name of the column which contains each document's raw text.
		feature_col : str
				name of column in convention_df with a feature dictionary
		metadata_col : str, optional
				name of column in convention_df with a meatadata dictionary
		parsed_col : str, optional
				name of column in convention_df with parsed strings
		"""
        self._df = df.reset_index()
        self._category_col = category_col
        self._text_col = text_col
        self._feature_col = feature_col
        self._parsed_col = parsed_col
        self._metadata_col = metadata_col
        self._category_idx_store = IndexStore()
        self._X_factory = CSRMatrixFactory()
        self._mX_factory = CSRMatrixFactory()
        self._term_idx_store = IndexStore()
        self._metadata_idx_store = IndexStore()

    def build(self):
        """Constructs the term doc matrix.

		Returns
		-------
		scattertext.ParsedCorpus.ParsedCorpus
		"""
        self._y = self._get_y_and_populate_category_idx_store()
        self._df.apply(self._add_to_x_factory, axis=1)
        self._X = self._X_factory.set_last_row_idx(len(self._y) - 1).get_csr_matrix()
        self._mX = self._mX_factory.set_last_row_idx(len(self._y) - 1).get_csr_matrix()
        if self._parsed_col is not None and self._parsed_col in self._df:
            return ParsedCorpus(self._df, self._X, self._mX, self._y, self._term_idx_store, self._category_idx_store, self._metadata_idx_store, self._parsed_col, self._category_col)
        else:
            return CorpusDF(self._df, self._X, self._mX, self._y, self._text_col, self._term_idx_store, self._category_idx_store, self._metadata_idx_store)

    def _get_y_and_populate_category_idx_store(self):
        return np.array(self._df[self._category_col].apply(str).apply(self._category_idx_store.getidx))

    def _add_to_x_factory(self, row):
        for feat, count in row[self._feature_col].items():
            feat_idx = self._term_idx_store.getidx(feat)
            self._X_factory[row.name, feat_idx] = count
        if self._metadata_col in self._df:
            for meta, count in row[self._metadata_col].items():
                meta_idx = self._metadata_idx_store.getidx(meta)
                self._mX_factory[row.name, meta_idx] = count

    def _make_new_term_doc_matrix(self, new_X, new_mX, new_y, new_term_idx_store, new_category_idx_store, new_metadata_idx_store, new_y_mask):
        if self._parsed_col is not None and self._parsed_col in self._df:
            return ParsedCorpus(self._df[new_y_mask], new_X, new_mX, new_y, new_term_idx_store, new_category_idx_store, new_metadata_idx_store, self._parsed_col, self._category_col)
        else:
            return CorpusDF(self._df[new_y_mask], new_X, new_mX, new_y, self._text_col, new_term_idx_store, new_category_idx_store, new_metadata_idx_store, self._df[self._text_col][new_y_mask])

def _get_y_and_populate_category_idx_store(self):
    return np.array(self._df[self._category_col].apply(str).apply(self._category_idx_store.getidx))

def check_topic_model_string_format(term_dict):
    """
    Parameters
    ----------
    term_dict: dict {metadataname: [term1, term2, ....], ...}

    Returns
    -------
    None
    """
    if type(term_dict) != dict:
        raise TypeError('Argument for term_dict must be a dict, keyed on strings, and contain a list of strings.')
    for k, v in term_dict.items():
        if type(v) != list:
            raise TypeError('Values in term dict must only be lists.')
        if sys.version_info[0] == 2:
            if type(k) != str and type(k) != unicode:
                raise TypeError('Keys in term dict must be of type str or unicode.')
            for e in v:
                if type(k) != str and type(k) != unicode:
                    raise TypeError('Values in term lists must be str or unicode.')
        if sys.version_info[0] == 3:
            if type(k) != str:
                raise TypeError('Keys in term dict must be of type str.')
            for e in v:
                if type(e) != str:
                    raise TypeError('Values in term lists must be str.')

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

def _term_importance_ranks(self, category, df):
    return np.array([df['category score rank'], df['not category score rank']]).min(axis=0)

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

def _make_new_term_doc_matrix(self, new_X=None, new_mX=None, new_y=None, new_term_idx_store=None, new_category_idx_store=None, new_metadata_idx_store=None, new_y_mask=None):
    X, mX, y = self._update_X_mX_y(new_X, new_mX, new_y, new_y_mask)
    return Corpus(X=X, mX=mX, y=y, term_idx_store=new_term_idx_store if new_term_idx_store is not None else self._term_idx_store, category_idx_store=new_category_idx_store if new_category_idx_store is not None else self._category_idx_store, metadata_idx_store=new_metadata_idx_store if new_metadata_idx_store is not None else self._metadata_idx_store, raw_texts=np.array(self.get_texts())[new_y_mask] if new_y_mask is not None else self.get_texts(), unigram_frequency_path=self._unigram_frequency_path)

def rotate_radians(y, x, radians):
    y = np.array(y)
    x = np.array(x)
    return Coordinates(x * np.cos(radians) - y * np.sin(radians), x * np.sin(radians) + y * np.cos(radians))

def _initialize_term_scorer_if_needed(category, corpus, neutral_categories, not_categories, show_neutral, term_scorer, use_non_text_features, term_ranker, term_scorer_kwargs):
    if inherits_from(term_scorer, 'CorpusBasedTermScorer') and type(term_scorer) == ABCMeta:
        term_scorer_kwargs = {} if term_scorer_kwargs is None else term_scorer_kwargs
        term_scorer = term_scorer(corpus, **term_scorer_kwargs)
    if inherits_from(type(term_scorer), 'CorpusBasedTermScorer'):
        if use_non_text_features:
            term_scorer = term_scorer.use_metadata()
        if term_ranker is not None:
            term_scorer = term_scorer.set_term_ranker(term_ranker=term_ranker)
        if not term_scorer.is_category_name_set():
            if show_neutral:
                term_scorer = term_scorer.set_categories(category, not_categories, neutral_categories)
            else:
                term_scorer = term_scorer.set_categories(category, not_categories)
    return term_scorer

def get_term_scorer_scores(category, corpus, neutral_categories, not_categories, show_neutral, term_ranker, term_scorer, use_non_text_features):
    tdf = corpus.apply_ranker(term_ranker, use_non_text_features)
    cat_freqs = tdf[str(category) + ' freq']
    if not_categories:
        not_cat_freqs = tdf[[str(c) + ' freq' for c in not_categories]].sum(axis=1)
    else:
        not_cat_freqs = tdf.sum(axis=1) - tdf[str(category) + ' freq']
    if inherits_from(type(term_scorer), 'CorpusBasedTermScorer'):
        return term_scorer.get_scores()
    return term_scorer.get_scores(cat_freqs, not_cat_freqs)

def word_similarity_explorer_gensim(corpus, category, target_term, category_name=None, not_category_name=None, word2vec=None, alpha=0.01, max_p_val=0.1, term_significance=None, **kwargs):
    """
        Parameters
        ----------
        corpus : Corpus
            Corpus to use.
        category : str
            Name of category column as it appears in original data frame.
        category_name : str
            Name of category to use.  E.g., "5-star reviews."
        not_category_name : str
            Name of everything that isn't in category.  E.g., "Below 5-star reviews".
        target_term : str
            Word or phrase for semantic similarity comparison
        word2vec : word2vec.Word2Vec
          Gensim-compatible Word2Vec model of lower-cased corpus. If none, o
          ne will be trained using Word2VecFromParsedCorpus(corpus).train()
        alpha : float, default = 0.01
            Uniform dirichlet prior for p-value calculation
        max_p_val : float, default = 0.1
            Max p-val to use find set of terms for similarity calculation
        term_significance : TermSignificance
            Significance finder

        Remaining arguments are from `produce_scattertext_explorer`.
        Returns
        -------
            str, html of visualization
        """
    if word2vec is None:
        word2vec = Word2VecFromParsedCorpus(corpus).train()
    if term_significance is None:
        term_significance = LogOddsRatioUninformativeDirichletPrior(alpha)
    assert issubclass(type(term_significance), TermSignificance)
    scores = []
    for tok in corpus._term_idx_store._i2val:
        try:
            scores.append(word2vec.similarity(target_term, tok.replace(' ', '_')))
        except:
            try:
                scores.append(np.mean([word2vec.similarity(target_term, tok_part) for tok_part in tok.split()]))
            except:
                scores.append(0)
    scores = np.array(scores)
    return produce_scattertext_explorer(corpus, category, category_name, not_category_name, scores=scores, sort_by_dist=False, reverse_sort_scores_for_not_category=False, word_vec_use_p_vals=True, term_significance=term_significance, max_p_val=max_p_val, p_value_colors=True, **kwargs)

def word_similarity_explorer(corpus, category, category_name, not_category_name, target_term, nlp=None, alpha=0.01, max_p_val=0.1, **kwargs):
    """
    Parameters
    ----------
    corpus : Corpus
        Corpus to use.
    category : str
        Name of category column as it appears in original data frame.
    category_name : str
        Name of category to use.  E.g., "5-star reviews."
    not_category_name : str
        Name of everything that isn't in category.  E.g., "Below 5-star reviews".
    target_term : str
        Word or phrase for semantic similarity comparison
    nlp : spaCy-like parsing function
        E.g., spacy.load('en_core_web_sm'), whitespace_nlp, etc...
    alpha : float, default = 0.01
        Uniform dirichlet prior for p-value calculation
    max_p_val : float, default = 0.1
        Max p-val to use find set of terms for similarity calculation
    Remaining arguments are from `produce_scattertext_explorer`.
    Returns
    -------
        str, html of visualization
    """
    if nlp is None:
        import spacy
        nlp = spacy.load('en_core_web_sm')
    base_term = nlp(target_term)
    scores = np.array([base_term.similarity(nlp(tok)) for tok in corpus._term_idx_store._i2val])
    return produce_scattertext_explorer(corpus, category, category_name, not_category_name, scores=scores, sort_by_dist=False, reverse_sort_scores_for_not_category=False, word_vec_use_p_vals=True, term_significance=LogOddsRatioUninformativeDirichletPrior(alpha), max_p_val=max_p_val, p_value_colors=True, **kwargs)

class OffsetCorpusFactory(object):

    def __init__(self, df, parsed_col, feat_and_offset_getter, category_col=None):
        """
        Parameters
        ----------
        df : pd.DataFrame
         contains category_col, and parse_col, were parsed col is entirely spacy docs
        parsed_col : str
            name of spacy parsed column in convention_df
        feats_from_spacy_doc : FeatsFromSpacyDoc
        category_col : str, Optional
            name of category column in df; if None, all category names will be '_'
        """
        self._df = df.reset_index()
        self._category_col = category_col
        self._parsed_col = parsed_col
        self._category_idx_store = IndexStore()
        self._X_factory = CSRMatrixFactory()
        self._mX_factory = CSRMatrixFactory()
        self._term_idx_store = IndexStore()
        self._metadata_idx_store = IndexStore()
        self._feat_and_offset_getter = feat_and_offset_getter
        self._term_offsets = {}
        self._metadata_offsets = {}

    def build(self, show_progress: bool=False) -> OffsetCorpus:
        """Constructs the term doc matrix.

        Returns
        -------
        scattertext.ParsedCorpus.ParsedCorpus
        """
        self._ensure_category_col_is_in_df()
        y = self._get_y_and_populate_category_idx_store(self._df[self._category_col])
        if show_progress is True:
            self._df.progress_apply(self._add_to_x_factory, axis=1)
        else:
            self._df.apply(self._add_to_x_factory, axis=1)
        self._mX = self._mX_factory.set_last_row_idx(len(y) - 1).get_csr_matrix()
        return OffsetCorpus(df=self._df, X=self._X_factory.set_last_row_idx(len(y) - 1).get_csr_matrix(), mX=self._mX_factory.set_last_row_idx(len(y) - 1).get_csr_matrix(), y=y, term_idx_store=self._term_idx_store, category_idx_store=self._category_idx_store, metadata_idx_store=self._metadata_idx_store, parsed_col=self._parsed_col, category_col=self._category_col, term_offsets=self._term_offsets, metadata_offsets=self._metadata_offsets)

    def _ensure_category_col_is_in_df(self):
        if self._category_col not in self._df:
            self._category_col = 'Category'
            while self._category_col in self._df:
                self._category_col = 'Category_' + ''.join((np.random.choice(string.ascii_letters) for _ in range(5)))
            self._df[self._category_col] = ''

    def _get_y_and_populate_category_idx_store(self, categories):
        return np.array(categories.apply(self._category_idx_store.getidx))

    def _add_to_x_factory(self, row):
        parsed_text = row[self._parsed_col]
        for term, (count, offsets) in self._feat_and_offset_getter.get_term_offsets(parsed_text):
            term_idx = self._term_idx_store.getidx(term)
            self._X_factory[row.name, term_idx] = count
            if offsets is not None:
                self._term_offsets.setdefault(term, {}).setdefault(row.name, []).extend(offsets)
        for meta, (val, offsets) in self._feat_and_offset_getter.get_metadata_offsets(parsed_text):
            self.__get_metadata_offsets(meta, offsets, row, val)
        for meta, (val, offsets) in self._feat_and_offset_getter.get_metadata_row_offsets(parsed_text, row):
            self.__get_metadata_offsets(meta, offsets, row, val)

    def __get_metadata_offsets(self, meta, offsets, row, val):
        meta_idx = self._metadata_idx_store.getidx(meta)
        self._mX_factory[row.name, meta_idx] = val
        if offsets is not None:
            self._metadata_offsets.setdefault(meta, {}).setdefault(row.name, []).extend(offsets)

def _get_y_and_populate_category_idx_store(self, categories):
    return np.array(categories.apply(self._category_idx_store.getidx))

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

def _get_fisher_scores_from_counts(self, cat_word_counts, not_cat_word_counts):
    cat_not_word_counts = cat_word_counts.sum() - cat_word_counts
    not_cat_not_word_counts = not_cat_word_counts.sum() - not_cat_word_counts

    def do_fisher_exact(x):
        return fisher_exact([[x[0], x[1]], [x[2], x[3]]], alternative='greater')
    odds_ratio, p_values = np.apply_along_axis(do_fisher_exact, 0, np.array([cat_word_counts, cat_not_word_counts, not_cat_word_counts, not_cat_not_word_counts]))
    return (odds_ratio, p_values)

def _get_rudder_scores_for_percentile_pair(self, category_percentiles, not_category_percentiles):
    return np.linalg.norm(np.array([1, 0]) - np.array(list(zip(category_percentiles, not_category_percentiles))), axis=1)

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

def _get_y_and_populate_category_idx_store(self, categories):
    return np.array(categories.apply(self._category_idx_store.getidx))

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

def _get_x_axis(self, scorer, tdf):
    return scorer.get_scores(tdf[self.category_a_ + ' freq'], tdf[self.category_b_ + ' freq'])

def _get_y_axis(self, scorer, tdf):
    return scorer.get_scores(tdf[[t + ' freq' for t in [self.category_a_, self.category_b_]]].sum(axis=1), tdf[[t + ' freq' for t in self.neutral_categories_]].sum(axis=1))

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

class FourSquare(SemioticSquare):

    def __init__(self, term_doc_matrix, category_a_list, category_b_list, not_category_a_list, not_category_b_list, labels=None, term_ranker=AbsoluteFrequencyRanker, scorer=None, non_text=False):
        """
        Parameters
        ----------
        term_doc_matrix : TermDocMatrix
            TermDocMatrix (or descendant) which will be used in constructing square.
        category_a_list : list
            Category names for term A
        category_b_list : list
            Category names for term B (in opposition to A)
        not_category_a_list : list
            List of category names that belong to not A
        not_category_b_list : list
            List of category names that belong to not A
        labels : dict
            None by default. Labels are dictionary of {'a_and_b': 'A and B', ...} to be shown
            above each category.
        term_ranker : TermRanker
            Class for returning a term-frequency convention_df
        scorer : termscoring class, optional
            Term scoring class for lexicon mining. Default: `scattertext.termscoring.ScaledFScore`
        """
        self.category_a_list_ = category_a_list
        self.category_b_list_ = category_b_list
        self.not_category_a_list_ = not_category_a_list
        self.not_category_b_list_ = not_category_b_list
        assert set(self._get_all_categories()) & set(term_doc_matrix.get_categories()) == set(self._get_all_categories())
        self.non_text = non_text
        self._build_square(term_doc_matrix, term_ranker, labels, scorer)

    def _get_x_axis(self, scorer, tdf):
        return scorer.get_scores(tdf[[t + ' freq' for t in set(self.category_a_list_ + self.not_category_b_list_)]].sum(axis=1), tdf[[t + ' freq' for t in set(self.category_b_list_ + self.not_category_a_list_)]].sum(axis=1))

    def _get_y_axis(self, scorer, tdf):
        return scorer.get_scores(tdf[[t + ' freq' for t in set(self.category_a_list_ + self.category_b_list_)]].sum(axis=1), tdf[[t + ' freq' for t in set(self.not_category_b_list_ + self.not_category_a_list_)]].sum(axis=1))

    def _get_all_categories(self):
        return self.category_a_list_ + self.category_b_list_ + self.not_category_a_list_ + self.not_category_b_list_

    def _get_default_a_label(self):
        return self.category_a_list_[0]

    def _get_default_b_label(self):
        return self.category_b_list_[0]

def _get_x_axis(self, scorer, tdf):
    return scorer.get_scores(tdf[[t + ' freq' for t in set(self.category_a_list_ + self.not_category_b_list_)]].sum(axis=1), tdf[[t + ' freq' for t in set(self.category_b_list_ + self.not_category_a_list_)]].sum(axis=1))

def _get_y_axis(self, scorer, tdf):
    return scorer.get_scores(tdf[[t + ' freq' for t in set(self.category_a_list_ + self.category_b_list_)]].sum(axis=1), tdf[[t + ' freq' for t in set(self.not_category_b_list_ + self.not_category_a_list_)]].sum(axis=1))

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

def cosine(a: np.array, b: np.array) -> np.array:
    return np.linalg.norm(a * b) / (np.linalg.norm(a) * np.linalg.norm(b))

class MultiCategoryAssociationScorer(MultiCategoryAssociationBase):

    def get_category_association(self, ranker: Union[TermRanker, Type]=None, scorer=None, verbose=False):
        ranker, scorer = self._resolve_ranker_and_scorer(ranker, scorer)
        data = []
        it = self.corpus.get_categories()
        if verbose:
            it = tqdm(it)
        for cat in it:
            scores = self.__get_scores(cat=cat, scorer=scorer, ranker=ranker)
            for term_rank, (term, score) in enumerate(scores.sort_values(ascending=False).items()):
                data.append({'Category': cat, 'Term': term, 'Rank': term_rank, 'Score': score})
        return pd.DataFrame(data)

    def get_category_association_and_freqs(self, ranker: Union[TermRanker, Type]=None, scorer=None, verbose=False):
        ranker, scorer = self._resolve_ranker_and_scorer(ranker, scorer)
        data = []
        it = self.corpus.get_categories()
        if verbose:
            it = tqdm(it)
        term_freq_df = ranker.get_ranks('')
        for cat in it:
            scores = self.__get_scores(cat=cat, scorer=scorer, ranker=ranker)
            freqs = term_freq_df[str(cat)]
            for term_rank, (term, score) in enumerate(scores.sort_values(ascending=False).items()):
                data.append({'Category': cat, 'Term': term, 'Freq': freqs.loc[term], 'Rank': term_rank, 'Score': score})
        return pd.DataFrame(data)

    def __get_scores(self, cat, scorer, ranker) -> pd.Series:
        if inherits_from(type(scorer), 'CorpusBasedTermScorer'):
            if self.use_metadata:
                scorer = scorer.use_metadata()
            scorer = scorer.set_categories(category_name=cat)
            if ranker is not None:
                scorer = scorer.set_term_ranker(term_ranker=ranker)
            return scorer.get_scores()
        term_freq_df = ranker.get_ranks('')
        try:
            cat_freq = term_freq_df[cat]
        except KeyError:
            cat_freq = term_freq_df[str(cat)]
        global_freq = term_freq_df.sum(axis=1)
        return scorer.get_scores(cat_freq, global_freq - cat_freq)

def __get_scores(self, cat, scorer, ranker) -> pd.Series:
    if inherits_from(type(scorer), 'CorpusBasedTermScorer'):
        if self.use_metadata:
            scorer = scorer.use_metadata()
        scorer = scorer.set_categories(category_name=cat)
        if ranker is not None:
            scorer = scorer.set_term_ranker(term_ranker=ranker)
        return scorer.get_scores()
    term_freq_df = ranker.get_ranks('')
    try:
        cat_freq = term_freq_df[cat]
    except KeyError:
        cat_freq = term_freq_df[str(cat)]
    global_freq = term_freq_df.sum(axis=1)
    return scorer.get_scores(cat_freq, global_freq - cat_freq)

class MultiCategoryAssociationBase:

    def __init__(self, corpus, use_metadata=False, non_text=False, use_non_text_features=False, ranker=None, scorer=None):
        self.corpus = corpus
        self.use_metadata = use_metadata or non_text or use_non_text_features
        self.ranker, self.scorer = self._resolve_ranker_and_scorer(ranker=ranker, scorer=scorer)

    def get_category_association(self, **kwargs):
        raise NotImplementedError()

    def get_category_association_and_freqs(self, **kwargs):
        raise NotImplementedError()

    def _resolve_ranker_and_scorer(self, ranker, scorer):
        if scorer is None:
            scorer = RankDifference()
        if inherits_from(scorer, 'CorpusBasedTermScorer'):
            scorer = scorer(self.corpus, use_metadata=self.use_metadata)
        elif type(scorer) == type:
            scorer = scorer()
        if ranker is None:
            ranker = AbsoluteFrequencyRanker(self.corpus)
        if inherits_from(ranker, 'TermRanker'):
            ranker = ranker(self.corpus)
        if self.use_metadata:
            ranker = ranker.use_non_text_features()
        return (ranker, scorer)

def _resolve_ranker_and_scorer(self, ranker, scorer):
    if scorer is None:
        scorer = RankDifference()
    if inherits_from(scorer, 'CorpusBasedTermScorer'):
        scorer = scorer(self.corpus, use_metadata=self.use_metadata)
    elif type(scorer) == type:
        scorer = scorer()
    if ranker is None:
        ranker = AbsoluteFrequencyRanker(self.corpus)
    if inherits_from(ranker, 'TermRanker'):
        ranker = ranker(self.corpus)
    if self.use_metadata:
        ranker = ranker.use_non_text_features()
    return (ranker, scorer)

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

def _limit_to_pairs_of_bigrams_and_a_constituent_unigram(self, pairs, terms):
    return pairs[np.array([terms[i[1]] in terms[i[0]] for i in pairs])]

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

def _initialize_scorer(self, term_doc_matrix):
    if issubclass(self.scorer, CorpusBasedTermScorer):
        my_scorer = self.scorer(term_doc_matrix)
        if self.use_non_text_features:
            return my_scorer.use_metadata()
        return my_scorer
    return self.scorer()

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

def test_term_doc_lists(self):
    term_doc_lists = self.tdm.term_doc_lists()
    self.assertEqual(type(term_doc_lists), dict)
    self.assertEqual(term_doc_lists['this'], [1, 2])
    self.assertEqual(term_doc_lists['another document'], [1])
    self.assertEqual(term_doc_lists['is'], [0, 1, 2])

class TestScalers(TestCase):

    def test_stretch_0_to_1(self):
        a = np.array([0.8, 0.5, 0.0, -0.2, -0.3, 0.4])
        out = stretch_0_to_1(a)
        np.testing.assert_almost_equal(out, np.array([1.0, 0.8125, 0.5, 0.16666667, 0.0, 0.75]))
        np.testing.assert_almost_equal(a, np.array([0.8, 0.5, 0.0, -0.2, -0.3, 0.4]))
        out = stretch_0_to_1(np.array([]))
        np.testing.assert_almost_equal(out, np.array([]))
        out = stretch_0_to_1(np.array([1, 0.5]))
        np.testing.assert_almost_equal(out, np.array([1.0, 0.75]))
        out = stretch_0_to_1(np.array([-1, -0.5]))
        np.testing.assert_almost_equal(out, np.array([0, 0.25]))

def test_stretch_0_to_1(self):
    a = np.array([0.8, 0.5, 0.0, -0.2, -0.3, 0.4])
    out = stretch_0_to_1(a)
    np.testing.assert_almost_equal(out, np.array([1.0, 0.8125, 0.5, 0.16666667, 0.0, 0.75]))
    np.testing.assert_almost_equal(a, np.array([0.8, 0.5, 0.0, -0.2, -0.3, 0.4]))
    out = stretch_0_to_1(np.array([]))
    np.testing.assert_almost_equal(out, np.array([]))
    out = stretch_0_to_1(np.array([1, 0.5]))
    np.testing.assert_almost_equal(out, np.array([1.0, 0.75]))
    out = stretch_0_to_1(np.array([-1, -0.5]))
    np.testing.assert_almost_equal(out, np.array([0, 0.25]))

class TestCohensD(TestCase):

    def test_get_cohens_d_scores(self):
        corpus = build_hamlet_jz_corpus()
        np.testing.assert_almost_equal(CohensD(corpus).set_term_ranker(OncePerDocFrequencyRanker).set_categories('hamlet').get_scores()[:5], [-0.2303607, 0.8838835, 0.8838835, 1.4028612, 0.8838835])

    def test_get_cohens_d_scores_zero_robust(self):
        corpus = build_hamlet_jz_corpus()
        corpus._X[1, :] = 0
        np.testing.assert_almost_equal(CohensD(corpus).set_term_ranker(OncePerDocFrequencyRanker).set_categories('hamlet').get_scores()[:5], [-0.2303607, 0.8838835, 0.8838835, 0.8838835, 0.8838835])

    def test_get_cohens_d_score_df(self):
        corpus = build_hamlet_jz_corpus()
        columns = CohensD(corpus).set_term_ranker(OncePerDocFrequencyRanker).set_categories('hamlet').get_score_df().columns
        self.assertEqual(set(columns), set(['cohens_d', 'cohens_d_se', 'cohens_d_z', 'cohens_d_p', 'hedges_g', 'hedges_g_se', 'hedges_g_z', 'hedges_g_p', 'm1', 'm2', 'count1', 'count2', 'docs1', 'docs2']))

    def test_get_cohens_d_score_df_p_vals(self):
        corpus = build_hamlet_jz_corpus()
        columns = CohensD(corpus).set_term_ranker(OncePerDocFrequencyRanker).set_categories('hamlet').get_score_df().columns
        self.assertEqual(set(columns), set(['cohens_d', 'cohens_d_se', 'cohens_d_z', 'cohens_d_p', 'hedges_g', 'hedges_g_se', 'hedges_g_z', 'hedges_g_p', 'm1', 'm2', 'count1', 'count2', 'docs1', 'docs2']))

    def test_get_name(self):
        corpus = build_hamlet_jz_corpus()
        self.assertEqual(CohensD(corpus).set_categories('hamlet').get_name(), "Cohen's d")

    def test_get_name_hedges(self):
        corpus = build_hamlet_jz_corpus()
        self.assertEqual(HedgesG(corpus).set_categories('hamlet').get_name(), "Hedge's g")
        self.assertEqual(len(HedgesG(corpus).set_categories('hamlet').get_scores()), corpus.get_num_terms())

def test_get_cohens_d_scores(self):
    corpus = build_hamlet_jz_corpus()
    np.testing.assert_almost_equal(CohensD(corpus).set_term_ranker(OncePerDocFrequencyRanker).set_categories('hamlet').get_scores()[:5], [-0.2303607, 0.8838835, 0.8838835, 1.4028612, 0.8838835])

def test_get_cohens_d_scores_zero_robust(self):
    corpus = build_hamlet_jz_corpus()
    corpus._X[1, :] = 0
    np.testing.assert_almost_equal(CohensD(corpus).set_term_ranker(OncePerDocFrequencyRanker).set_categories('hamlet').get_scores()[:5], [-0.2303607, 0.8838835, 0.8838835, 0.8838835, 0.8838835])

def test_get_cohens_d_score_df(self):
    corpus = build_hamlet_jz_corpus()
    columns = CohensD(corpus).set_term_ranker(OncePerDocFrequencyRanker).set_categories('hamlet').get_score_df().columns
    self.assertEqual(set(columns), set(['cohens_d', 'cohens_d_se', 'cohens_d_z', 'cohens_d_p', 'hedges_g', 'hedges_g_se', 'hedges_g_z', 'hedges_g_p', 'm1', 'm2', 'count1', 'count2', 'docs1', 'docs2']))

def test_get_cohens_d_score_df_p_vals(self):
    corpus = build_hamlet_jz_corpus()
    columns = CohensD(corpus).set_term_ranker(OncePerDocFrequencyRanker).set_categories('hamlet').get_score_df().columns
    self.assertEqual(set(columns), set(['cohens_d', 'cohens_d_se', 'cohens_d_z', 'cohens_d_p', 'hedges_g', 'hedges_g_se', 'hedges_g_z', 'hedges_g_p', 'm1', 'm2', 'count1', 'count2', 'docs1', 'docs2']))

def test_get_name(self):
    corpus = build_hamlet_jz_corpus()
    self.assertEqual(CohensD(corpus).set_categories('hamlet').get_name(), "Cohen's d")

def test_get_name_hedges(self):
    corpus = build_hamlet_jz_corpus()
    self.assertEqual(HedgesG(corpus).set_categories('hamlet').get_name(), "Hedge's g")
    self.assertEqual(len(HedgesG(corpus).set_categories('hamlet').get_scores()), corpus.get_num_terms())

class TestPercentile_lexicographic(TestCase):

    def test_percentile_lexicographic(self):
        scores = [1, 1, 5, 18, 1, 3]
        text = ['c', 'a', 'five', 'eighteen', 'b', 'three']
        ranking = percentile_alphabetical(scores, text)
        np.testing.assert_array_almost_equal(ranking, np.array([0.4, 0, 0.8, 1.0, 0.2, 0.6]))

def test_percentile_lexicographic(self):
    scores = [1, 1, 5, 18, 1, 3]
    text = ['c', 'a', 'five', 'eighteen', 'b', 'three']
    ranking = percentile_alphabetical(scores, text)
    np.testing.assert_array_almost_equal(ranking, np.array([0.4, 0, 0.8, 1.0, 0.2, 0.6]))

class TestBetaPosterior(TestCase):

    def test_get_score_df(self):
        corpus = build_hamlet_jz_corpus()
        beta_posterior = BetaPosterior(corpus).set_categories('hamlet')
        score_df = beta_posterior.get_score_df()
        scores = beta_posterior.get_scores()
        np.testing.assert_almost_equal(scores[:5], [-0.3194860824225506, 1.0294085051562822, 1.0294085051562822, 1.234664219528909, 1.0294085051562822])

    def test_get_name(self):
        corpus = build_hamlet_jz_corpus()
        self.assertEqual(BetaPosterior(corpus).get_name(), 'Beta Posterior')

def test_get_score_df(self):
    corpus = build_hamlet_jz_corpus()
    beta_posterior = BetaPosterior(corpus).set_categories('hamlet')
    score_df = beta_posterior.get_score_df()
    scores = beta_posterior.get_scores()
    np.testing.assert_almost_equal(scores[:5], [-0.3194860824225506, 1.0294085051562822, 1.0294085051562822, 1.234664219528909, 1.0294085051562822])

def test_get_name(self):
    corpus = build_hamlet_jz_corpus()
    self.assertEqual(BetaPosterior(corpus).get_name(), 'Beta Posterior')

class TestScaledFScore(TestCase):

    def test_get_scores(self):
        cat_counts, not_cat_counts = self._get_counts()
        scores = ScaledFScore.get_scores(cat_counts, not_cat_counts, beta=1.0)
        np.testing.assert_almost_equal(scores, np.array([0.2689108, 0.0, 0.2689108, 0.1266617, 1.0, 0.5, 0.5590517, 0.5, 0.5, 0.5720015]))

    def test_get_scores_zero_all_same(self):
        cat_counts = np.array([0, 0, 0, 0, 0, 0, 1, 2])
        not_cat_counts = np.array([1, 1, 2, 1, 1, 1, 1, 2])
        scores = ScaledFScore.get_scores(cat_counts, not_cat_counts)
        np.testing.assert_almost_equal(scores, [0.5, 0.5, 0, 0.5, 0.5, 0.5, 0.5, 1.0])

    def test_score_difference(self):
        cat_counts = np.array([0, 0, 0, 0, 0, 0, 1, 2])
        not_cat_counts = np.array([1, 1, 2, 1, 1, 1, 1, 2])
        scores = ScaledFScorePresets(use_score_difference=True).get_scores(cat_counts, not_cat_counts)
        np.testing.assert_almost_equal(scores, [0.4857218, 0.4857218, 0.1970024, 0.4857218, 0.4857218, 0.4857218, 0.8548192, 0.90317])

    def test_get_scores_zero_median(self):
        cat_counts = np.array([0, 0, 0, 0, 0, 0, 1, 2])
        not_cat_counts = np.array([1, 1, 2, 1, 1, 1, 1, 3])
        ScaledFScore.get_scores(cat_counts, not_cat_counts)

    def get_scores_for_category(self):
        cat_counts, not_cat_counts = self._get_counts()
        scores = ScaledFScore.get_scores_for_category(cat_counts, not_cat_counts)
        np.testing.assert_almost_equal(scores, [0.23991183969723384, 0.24969810634506373, 0.23991183969723384, 0.27646711056272855, 0.9288524483499752, 0.42010144843632563, 0.4916601710596672, 0.0, 0.0, 0.5026230405798466])

    def _get_counts(self):
        cat_counts = np.array([1, 5, 1, 9, 100, 1, 1, 0, 0, 2])
        not_cat_counts = np.array([100, 510, 100, 199, 0, 1, 0, 1, 1, 0])
        return (cat_counts, not_cat_counts)

def test_get_scores(self):
    cat_counts, not_cat_counts = self._get_counts()
    scores = ScaledFScore.get_scores(cat_counts, not_cat_counts, beta=1.0)
    np.testing.assert_almost_equal(scores, np.array([0.2689108, 0.0, 0.2689108, 0.1266617, 1.0, 0.5, 0.5590517, 0.5, 0.5, 0.5720015]))

def test_get_scores_zero_all_same(self):
    cat_counts = np.array([0, 0, 0, 0, 0, 0, 1, 2])
    not_cat_counts = np.array([1, 1, 2, 1, 1, 1, 1, 2])
    scores = ScaledFScore.get_scores(cat_counts, not_cat_counts)
    np.testing.assert_almost_equal(scores, [0.5, 0.5, 0, 0.5, 0.5, 0.5, 0.5, 1.0])

def test_score_difference(self):
    cat_counts = np.array([0, 0, 0, 0, 0, 0, 1, 2])
    not_cat_counts = np.array([1, 1, 2, 1, 1, 1, 1, 2])
    scores = ScaledFScorePresets(use_score_difference=True).get_scores(cat_counts, not_cat_counts)
    np.testing.assert_almost_equal(scores, [0.4857218, 0.4857218, 0.1970024, 0.4857218, 0.4857218, 0.4857218, 0.8548192, 0.90317])

def test_get_scores_zero_median(self):
    cat_counts = np.array([0, 0, 0, 0, 0, 0, 1, 2])
    not_cat_counts = np.array([1, 1, 2, 1, 1, 1, 1, 3])
    ScaledFScore.get_scores(cat_counts, not_cat_counts)

def get_scores_for_category(self):
    cat_counts, not_cat_counts = self._get_counts()
    scores = ScaledFScore.get_scores_for_category(cat_counts, not_cat_counts)
    np.testing.assert_almost_equal(scores, [0.23991183969723384, 0.24969810634506373, 0.23991183969723384, 0.27646711056272855, 0.9288524483499752, 0.42010144843632563, 0.4916601710596672, 0.0, 0.0, 0.5026230405798466])

def _get_counts(self):
    cat_counts = np.array([1, 5, 1, 9, 100, 1, 1, 0, 0, 2])
    not_cat_counts = np.array([100, 510, 100, 199, 0, 1, 0, 1, 1, 0])
    return (cat_counts, not_cat_counts)

class TestLogOddsUninformativePriorScore(TestCase):

    def test_get_score(self):
        cat_counts, not_cat_counts = self._get_counts()
        scores = LogOddsUninformativePriorScore.get_score(cat_counts, not_cat_counts)
        np.testing.assert_almost_equal(scores, np.array([0.4447054, 0.9433088, 0.4447054, -0.9971462]))
    '\n\tdef test_get_delta_hats(self):\n\t\tcat_counts, not_cat_counts = self._get_counts()\n\t\tscores = LogOddsUninformativePriorScore.get_delta_hats(cat_counts, not_cat_counts)\n\t\tnp.testing.assert_almost_equal(scores,\n\t\t                               np.array([-0.6095321, -1.0345766, -0.6095321,  1.5201005]))\n\t'

    def test_get_score_threshold(self):
        cat_counts = np.array([1, 5, 2, 7, 10])
        not_cat_counts = np.array([10, 10, 1, 5, 10])
        scores = LogOddsUninformativePriorScore.get_thresholded_score(cat_counts, not_cat_counts, alpha_w=0.01, threshold=0.1)
        np.testing.assert_almost_equal(scores, np.array([-0.9593012, -0.0, 0.0, 0.8197493, 0.0]))

    def test__turn_pvals_into_scores(self):
        p_vals = np.array([0.01, 0.99, 0.5, 0.1, 0.9])
        scores = LogOddsUninformativePriorScore._turn_pvals_into_scores(p_vals)
        np.testing.assert_almost_equal(scores, [0.98, -0.98, -0.0, 0.8, -0.8])

    def test__turn_counts_into_matrix(self):
        cat_counts, not_cat_counts = self._get_counts()
        X = LogOddsUninformativePriorScore._turn_counts_into_matrix(cat_counts, not_cat_counts)
        np.testing.assert_almost_equal(X, np.array([[1, 100], [5, 510], [1, 100], [9, 199]]))

    def _get_counts(self):
        cat_counts = np.array([1, 5, 1, 9])
        not_cat_counts = np.array([100, 510, 100, 199])
        return (cat_counts, not_cat_counts)

def test_get_score(self):
    cat_counts, not_cat_counts = self._get_counts()
    scores = LogOddsUninformativePriorScore.get_score(cat_counts, not_cat_counts)
    np.testing.assert_almost_equal(scores, np.array([0.4447054, 0.9433088, 0.4447054, -0.9971462]))

def test_get_score_threshold(self):
    cat_counts = np.array([1, 5, 2, 7, 10])
    not_cat_counts = np.array([10, 10, 1, 5, 10])
    scores = LogOddsUninformativePriorScore.get_thresholded_score(cat_counts, not_cat_counts, alpha_w=0.01, threshold=0.1)
    np.testing.assert_almost_equal(scores, np.array([-0.9593012, -0.0, 0.0, 0.8197493, 0.0]))

def test__turn_pvals_into_scores(self):
    p_vals = np.array([0.01, 0.99, 0.5, 0.1, 0.9])
    scores = LogOddsUninformativePriorScore._turn_pvals_into_scores(p_vals)
    np.testing.assert_almost_equal(scores, [0.98, -0.98, -0.0, 0.8, -0.8])

def test__turn_counts_into_matrix(self):
    cat_counts, not_cat_counts = self._get_counts()
    X = LogOddsUninformativePriorScore._turn_counts_into_matrix(cat_counts, not_cat_counts)
    np.testing.assert_almost_equal(X, np.array([[1, 100], [5, 510], [1, 100], [9, 199]]))

def _get_counts(self):
    cat_counts = np.array([1, 5, 1, 9])
    not_cat_counts = np.array([100, 510, 100, 199])
    return (cat_counts, not_cat_counts)

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

def test_get_scores(self):
    result = ZScores(self.corpus).set_categories('hamlet').get_scores()
    self.assertEquals(type(result), pd.Series)
    np.testing.assert_array_equal(np.array(result.index), self.corpus.get_terms())

def test_get_name(self):
    self.assertEquals(ZScores(self.corpus).set_categories('hamlet').get_name(), "Z-Score from Welch's T-Test")

def test_get_ranks_meta(self):
    corpus = build_hamlet_jz_corpus_with_meta()
    self.assertEquals(ZScores(corpus).set_term_ranker(OncePerDocFrequencyRanker).set_categories('hamlet').get_name(), "Z-Score from Welch's T-Test")

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

def test_get_scores(self):
    result = RelativeEntropy(self.corpus).set_categories('hamlet').get_scores()
    self.assertEquals(type(result), pd.Series)
    np.testing.assert_array_equal(np.array(result.index), self.corpus.get_terms())

def test_get_name(self):
    self.assertEquals(RelativeEntropy(self.corpus).set_categories('hamlet').get_name(), 'Frankhauser Relative Entropy')

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

def test_get_scores(self):
    result = BM25Difference(self.corpus).set_categories('hamlet').get_scores()
    self.assertEquals(type(result), pd.Series)
    np.testing.assert_array_equal(np.array(result.index), self.corpus.get_terms())

def test_get_name(self):
    self.assertEquals(BM25Difference(self.corpus).set_categories('hamlet').get_name(), 'BM25 difference')

class TestCornerScore(TestCase):

    def test_get_scores(self):
        cat_counts, not_cat_counts = self._get_counts()
        scores = CornerScore.get_scores(cat_counts, not_cat_counts)
        np.testing.assert_almost_equal(scores, np.array([0.1820027, 0.2828427, 0.1820027, 0.5, 0.9292893, 0.2378287, 0.7930882, 0.1845603, 0.1845603, 0.8725245]))

    def test_get_scores_for_category(self):
        cat_counts, not_cat_counts = self._get_counts()
        scores = CornerScore.get_scores_for_category(cat_counts, not_cat_counts)
        np.testing.assert_almost_equal(scores, np.array([0.9300538, 1.0198039, 0.9300538, 0.9055385, 0.2, 0.7433034, 0.585235, 0.9861541, 0.9861541, 0.3605551]))

    def test_get_scores_zero_all_same(self):
        cat_counts = np.array([0, 0, 0, 0, 0, 0, 1, 2])
        not_cat_counts = np.array([1, 1, 2, 1, 1, 1, 1, 2])
        scores = CornerScore.get_scores(cat_counts, not_cat_counts)
        np.testing.assert_almost_equal(scores, np.array([0.5, 0.5, 0.15625, 0.5, 0.5, 0.5, 0.8391308, 0.6685437]))

    def test_get_scores_zero_median(self):
        cat_counts = np.array([0, 0, 0, 0, 0, 0, 1, 2])
        not_cat_counts = np.array([1, 1, 2, 1, 1, 1, 1, 3])
        CornerScore.get_scores(cat_counts, not_cat_counts)

    def get_scores_for_category(self):
        cat_counts, not_cat_counts = self._get_counts()
        scores = CornerScore.get_scores_for_category(cat_counts, not_cat_counts)
        np.testing.assert_almost_equal(scores, np.array([0.9300538, 1.0198039, 0.9300538, 0.9055385, 0.2, 0.7433034, 0.585235, 0.9861541, 0.9861541, 0.3605551]))

    def _get_counts(self):
        cat_counts = np.array([1, 5, 1, 9, 100, 1, 1, 0, 0, 2])
        not_cat_counts = np.array([100, 510, 100, 199, 0, 1, 0, 1, 1, 0])
        return (cat_counts, not_cat_counts)

def test_get_scores(self):
    cat_counts, not_cat_counts = self._get_counts()
    scores = CornerScore.get_scores(cat_counts, not_cat_counts)
    np.testing.assert_almost_equal(scores, np.array([0.1820027, 0.2828427, 0.1820027, 0.5, 0.9292893, 0.2378287, 0.7930882, 0.1845603, 0.1845603, 0.8725245]))

def test_get_scores_for_category(self):
    cat_counts, not_cat_counts = self._get_counts()
    scores = CornerScore.get_scores_for_category(cat_counts, not_cat_counts)
    np.testing.assert_almost_equal(scores, np.array([0.9300538, 1.0198039, 0.9300538, 0.9055385, 0.2, 0.7433034, 0.585235, 0.9861541, 0.9861541, 0.3605551]))

def test_get_scores_zero_all_same(self):
    cat_counts = np.array([0, 0, 0, 0, 0, 0, 1, 2])
    not_cat_counts = np.array([1, 1, 2, 1, 1, 1, 1, 2])
    scores = CornerScore.get_scores(cat_counts, not_cat_counts)
    np.testing.assert_almost_equal(scores, np.array([0.5, 0.5, 0.15625, 0.5, 0.5, 0.5, 0.8391308, 0.6685437]))

def test_get_scores_zero_median(self):
    cat_counts = np.array([0, 0, 0, 0, 0, 0, 1, 2])
    not_cat_counts = np.array([1, 1, 2, 1, 1, 1, 1, 3])
    CornerScore.get_scores(cat_counts, not_cat_counts)

def get_scores_for_category(self):
    cat_counts, not_cat_counts = self._get_counts()
    scores = CornerScore.get_scores_for_category(cat_counts, not_cat_counts)
    np.testing.assert_almost_equal(scores, np.array([0.9300538, 1.0198039, 0.9300538, 0.9055385, 0.2, 0.7433034, 0.585235, 0.9861541, 0.9861541, 0.3605551]))

def _get_counts(self):
    cat_counts = np.array([1, 5, 1, 9, 100, 1, 1, 0, 0, 2])
    not_cat_counts = np.array([100, 510, 100, 199, 0, 1, 0, 1, 1, 0])
    return (cat_counts, not_cat_counts)

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

def test_search_index(self):
    expected = np.array([7, 9])
    self.assertIsInstance(self.corpus, CorpusDF)
    returned = self.corpus.search_index('speak up')
    np.testing.assert_array_equal(expected, returned)

class TestCredTFIDF(TestCase):

    def test_get_score_df(self):
        corpus = build_hamlet_jz_corpus()
        tfidf = CredTFIDF(corpus).set_term_ranker(OncePerDocFrequencyRanker).set_categories('hamlet')
        np.testing.assert_almost_equal(tfidf.get_scores()[:5], [3.0757237e-05, 0.041256023, 0.041256023, 0.055708409, 0.041256023])
        self.assertEqual(list(tfidf.get_score_df().columns), ['pos_cred_tfidf', 'neg_cred_tfidf', 'delta_cred_tf_idf'])

    def test_get_name(self):
        corpus = build_hamlet_jz_corpus()
        self.assertEqual(CredTFIDF(corpus).get_name(), 'Delta mean cred-tf-idf')

def test_get_score_df(self):
    corpus = build_hamlet_jz_corpus()
    tfidf = CredTFIDF(corpus).set_term_ranker(OncePerDocFrequencyRanker).set_categories('hamlet')
    np.testing.assert_almost_equal(tfidf.get_scores()[:5], [3.0757237e-05, 0.041256023, 0.041256023, 0.055708409, 0.041256023])
    self.assertEqual(list(tfidf.get_score_df().columns), ['pos_cred_tfidf', 'neg_cred_tfidf', 'delta_cred_tf_idf'])

def test_get_name(self):
    corpus = build_hamlet_jz_corpus()
    self.assertEqual(CredTFIDF(corpus).get_name(), 'Delta mean cred-tf-idf')

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

def __init__(self, corpus: OffsetCorpus, non_text: bool, domains_to_preserve: Optional[List[str]]=None, verbose: bool=False, random_generator: Optional[np.random._generator.Generator]=None):
    self.corpus = corpus
    self.rng = random_generator
    self.domains_to_preserve = domains_to_preserve
    if not non_text:
        assert inherits_from(type(corpus), 'OffsetCorpus')
    self.term_inter_arrivals = {}
    self.term_category_inter_arrivals = {}
    self.__populate_inter_arrival_stats(verbose=verbose)

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

def distinct_prefix(x, y):
    for i, (xc, yc) in enumerate(zip(x, y)):
        if xc != yc:
            return (x[:i + 1], y[:i + 1])
    return (x, y)

def latent_semantic_scale_from_word2vec(model, pos_seed_words=None, neg_seed_words=None, seed_words=None, seed_values=None):
    terms = [word for word in model.wv.key_to_index.keys()]
    embeddings = np.matrix([model.wv[word] for word in model.wv.key_to_index.keys()])
    return lss_terms(embeddings, terms, pos_seed_words, neg_seed_words, seed_words, seed_values)

def lss_terms(embeddings, terms, pos_seed_words=None, neg_seed_words=None, seed_words=None, seed_values=None):
    neg_seed_words = [] if neg_seed_words is None else neg_seed_words
    pos_seed_words = [] if pos_seed_words is None else pos_seed_words
    seed_words = [] if seed_words is None else seed_words
    seed_values = [] if seed_values is None else seed_values
    for word, value in zip(pos_seed_words + neg_seed_words, [1] * len(pos_seed_words) + [-1] * len(neg_seed_words)):
        seed_words.append(word)
        seed_values.append(value)
    assert seed_values
    assert embeddings.shape[0] == len(terms)
    assert len(seed_words) == len(seed_values)
    missing_words = []
    for word in seed_words:
        if word not in terms:
            missing_words.append(word)
    if missing_words:
        raise Exception(f'No embedding(s) exists for {','.join(missing_words)}.')
    term2i = {term: i for i, term in enumerate(terms)}
    seed_mat = embeddings[[term2i[term] for term in seed_words], :]
    seed_norm = np.matrix(np.linalg.norm(seed_mat, axis=1))
    term_norm = np.matrix(np.linalg.norm(embeddings, axis=1))
    cosine_mat = seed_mat.dot(embeddings.T).T / seed_norm / term_norm.T
    return pd.Series((cosine_mat * np.matrix(seed_values).T).A1, index=terms)

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

class EmbeddingsProjectorEvaluator(CategoryProjectionEvaluator):

    def __init__(self, get_vector):
        self.get_vector = get_vector

    def evaluate(self, category_projection):
        assert issubclass(type(category_projection), CategoryProjectionBase)
        topics = category_projection.get_nearest_terms()
        total_similarity = 0
        for topic in topics.values():
            topic_vectors = np.array([self.get_vector(term) for term in topic])
            sim_matrix = cosine_similarity(topic_vectors)
            tril_sim_matrix = np.tril(sim_matrix)
            mean_similarity = tril_sim_matrix.sum() / (tril_sim_matrix.shape[0] ** 2 - tril_sim_matrix.shape[0]) / 2
            total_similarity += mean_similarity
        return total_similarity / len(topics)

def evaluate(self, category_projection):
    assert issubclass(type(category_projection), CategoryProjectionBase)
    topics = category_projection.get_nearest_terms()
    total_similarity = 0
    for topic in topics.values():
        topic_vectors = np.array([self.get_vector(term) for term in topic])
        sim_matrix = cosine_similarity(topic_vectors)
        tril_sim_matrix = np.tril(sim_matrix)
        mean_similarity = tril_sim_matrix.sum() / (tril_sim_matrix.shape[0] ** 2 - tril_sim_matrix.shape[0]) / 2
        total_similarity += mean_similarity
    return total_similarity / len(topics)

def find_ngrams(input_list, num_):
    """get ngrams of len n from input list"""
    return zip(*[input_list[i:] for i in range(num_)])

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

def get_scores(self, *args):
    return self.get_score_df()['mwu_z']

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

def get_score_df(self, label_append=''):
    return self.get_term_ranker().get_ranks(label_append=label_append).assign(Metric=self.get_scores()).sort_values(by='Metric', ascending=True).rename(columns={'Metric': self.get_name()})

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

def get_scores(self, *args):
    """
        In this case, args aren't used, since this information is taken
        directly from the corpus categories.

        Returns
        -------
        np.array, scores
        """
    return self.get_score_df().Score

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
def get_scores(cat_word_counts, not_cat_word_counts):
    pos = CornerScore.get_scores_for_category(cat_word_counts, not_cat_word_counts)
    neg = CornerScore.get_scores_for_category(not_cat_word_counts, cat_word_counts)
    scores = CornerScore._balance_scores(pos, neg)
    return scores

@staticmethod
def _distance_from_upper_left(cat_pctls, not_cat_pctls):
    return np.linalg.norm(np.array([1, 0]) - np.array(list(zip(cat_pctls, not_cat_pctls))), axis=1)

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

def get_scores(self, *args) -> pd.Series:
    return self.get_score_df()['Delta']

class LogOddsUninformativePriorScore:

    @staticmethod
    def get_score(cat_word_counts, not_cat_word_counts, alpha_w=0.01):
        X = LogOddsUninformativePriorScore._turn_counts_into_matrix(cat_word_counts, not_cat_word_counts)
        p_vals = LogOddsRatioUninformativeDirichletPrior(alpha_w).get_p_vals(X)
        scores = LogOddsUninformativePriorScore._turn_pvals_into_scores(p_vals)
        return scores

    @staticmethod
    def get_delta_hats(cat_word_counts, not_cat_word_counts, alpha_w=0.01):
        return LogOddsRatioUninformativeDirichletPrior(alpha_w).get_log_odds_with_prior(LogOddsUninformativePriorScore._turn_counts_into_matrix(cat_word_counts, not_cat_word_counts))

    @staticmethod
    def get_delta_hats(cat_word_counts, not_cat_word_counts, alpha_w=0.01):
        return LogOddsRatioUninformativeDirichletPrior(alpha_w).get_log_odds_with_prior(LogOddsUninformativePriorScore._turn_counts_into_matrix(cat_word_counts, not_cat_word_counts))

    @staticmethod
    def get_thresholded_score(cat_word_counts, not_cat_word_counts, alpha_w=0.01, threshold=0.1):
        scores = LogOddsRatioUninformativeDirichletPrior(alpha_w).get_p_values_from_counts(cat_word_counts, not_cat_word_counts) * 2 - 1
        return scores * ((scores < -(1.0 - threshold * 2)) | (scores > 1.0 - threshold * 2))

    @staticmethod
    def _turn_counts_into_matrix(cat_word_counts, not_cat_word_counts):
        return np.array([cat_word_counts, not_cat_word_counts]).T

    @staticmethod
    def _turn_pvals_into_scores(p_vals):
        return -((p_vals - 0.5) * 2)

@staticmethod
def get_score(cat_word_counts, not_cat_word_counts, alpha_w=0.01):
    X = LogOddsUninformativePriorScore._turn_counts_into_matrix(cat_word_counts, not_cat_word_counts)
    p_vals = LogOddsRatioUninformativeDirichletPrior(alpha_w).get_p_vals(X)
    scores = LogOddsUninformativePriorScore._turn_pvals_into_scores(p_vals)
    return scores

@staticmethod
def get_delta_hats(cat_word_counts, not_cat_word_counts, alpha_w=0.01):
    return LogOddsRatioUninformativeDirichletPrior(alpha_w).get_log_odds_with_prior(LogOddsUninformativePriorScore._turn_counts_into_matrix(cat_word_counts, not_cat_word_counts))

@staticmethod
def get_thresholded_score(cat_word_counts, not_cat_word_counts, alpha_w=0.01, threshold=0.1):
    scores = LogOddsRatioUninformativeDirichletPrior(alpha_w).get_p_values_from_counts(cat_word_counts, not_cat_word_counts) * 2 - 1
    return scores * ((scores < -(1.0 - threshold * 2)) | (scores > 1.0 - threshold * 2))

@staticmethod
def _turn_counts_into_matrix(cat_word_counts, not_cat_word_counts):
    return np.array([cat_word_counts, not_cat_word_counts]).T

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

class ScaledFScorePresetsNeg1To1(ScaledFScorePresets):

    @staticmethod
    def get_default_score():
        return 0

    def get_scores(self, cat_word_counts, not_cat_word_counts):
        scores = ScaledFScorePresets.get_scores(self, cat_word_counts, not_cat_word_counts)
        return scores * 2 - 1

def get_scores(self, cat_word_counts, not_cat_word_counts):
    scores = ScaledFScorePresets.get_scores(self, cat_word_counts, not_cat_word_counts)
    return scores * 2 - 1

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

def get_score_deltas(self, cat_word_counts, not_cat_word_counts):
    cat_scores = ScaledFScorePresets.get_scores_for_category(self, cat_word_counts, not_cat_word_counts)
    not_cat_scores = ScaledFScorePresets.get_scores_for_category(self, not_cat_word_counts, cat_word_counts)
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

def get_scores(self, *args):
    return self.get_score_df()['cohens_d']

class HedgesG(CohensD):

    def get_scores(self, *args):
        return self.get_score_df()['hedges_g']

    def get_name(self):
        return "Hedge's g"

def get_scores(self, *args):
    return self.get_score_df()['hedges_g']

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

def __init__(self, corpus, *args, **kwargs):
    CorpusBasedTermScorer.__init__(self, corpus, *args, **kwargs)
    self.set_term_ranker(OncePerDocFrequencyRanker)

def get_scores(self, *args):
    return self.get_score_df()['score']

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

def get_scores(self, *args):
    return self.get_score_df()['delta_cred_tf_idf']

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

def get_score_df(self):
    return pd.DataFrame({'Score': self.get_scores()})

class MeanIsotonic:

    def __init__(self, n=1000, frac=0.2):
        self.n = n
        self.direction = 1
        self.frac = frac

    def fit(self, xdata, ydata):
        assert len(xdata.T[0]) == len(ydata)
        r, p = pearsonr(xdata.T[0], ydata)
        if r < 0:
            self.direction = -1
        df = pd.DataFrame({'x': xdata.T[0] * self.direction, 'y': ydata})
        pred = np.zeros(len(df), dtype=np.float64)
        for i in range(self.n):
            sample_df = df.sample(frac=self.frac)
            pred += 1 / self.n * IsotonicRegression(y_max=1, y_min=0, out_of_bounds='clip').fit(sample_df.x.values, sample_df.y.values).predict(df.x.values)
        self.output = pred * self.direction
        return self

    def predict(self, x):
        return np.array([self.output]).T * self.direction

    def fit_predict(self, x, y):
        assert len(x) == len(y)
        df = pd.DataFrame({'x': x, 'y': y})
        pred = np.zeros(len(df), dtype=np.float64)
        for i in range(self.n):
            sample_df = df.sample(frac=self.frac)
            pred += 1 / self.n * IsotonicRegression(y_max=1, y_min=0, out_of_bounds='clip').fit(sample_df.x.values, sample_df.y.values).predict(df.x.values)
        return pred

def predict(self, x):
    return np.array([self.output]).T * self.direction

class EuclideanDistance(DistanceMeasureBase):

    @staticmethod
    def distances(fixed_x, fixed_y, x_vec, y_vec):
        return np.linalg.norm(np.array([x_vec - fixed_x, y_vec - fixed_y]), 2, axis=0)

@staticmethod
def distances(fixed_x, fixed_y, x_vec, y_vec):
    return np.linalg.norm(np.array([x_vec - fixed_x, y_vec - fixed_y]), 2, axis=0)

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

def _get_bigram_feats(self, unigrams):
    if len(unigrams) > 1:
        bigrams = map(' '.join, zip(unigrams[:-1], unigrams[1:]))
    else:
        bigrams = []
    return bigrams

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

def get_js_reset_function(self, values_to_set, functions_to_reset, reset_function_name='reset'):
    """

        :param functions_to_reset: List[str]
        :param values_to_set: List[str]
        :param reset_function_name: str, default = rest
        :return: str
        """
    return 'function ' + reset_function_name + '() {' + "document.querySelectorAll('.scattertext').forEach(element=>element.innerHTML=null);\n" + "document.querySelectorAll('#d3-div-1-corpus-stats').forEach(element=>element.innerHTML=null);\n" + ' '.join([value + ' = ' + function_name + '();' for value, function_name in zip(values_to_set, functions_to_reset)]) + '}'

