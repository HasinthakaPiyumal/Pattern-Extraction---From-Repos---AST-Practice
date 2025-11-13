# Cluster 10

def get_heading(corpus: st.ParsedCorpus) -> str:
    return corpus.get_df().movie_name

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

def get_labels_and_texts(self):
    texts = self._get_texts_to_display()
    to_ret = {'categories': self._corpus.get_categories(), 'labels': self._corpus.get_doc_indices(), 'texts': self._get_list_from_texts(texts)}
    if self._use_non_text_features:
        to_ret['extra'] = self._corpus.list_extra_features(not self._use_terms_for_extra_features)
    return to_ret

def _get_texts_to_display(self):
    if self._there_are_no_alternative_texts_to_display():
        return self._corpus.get_texts()
    else:
        return self._texts_to_display

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

def _get_category_names(self, category):
    other_categories = [val + ' freq' for val in self.term_doc_matrix.get_categories() if val != category]
    all_categories = other_categories + [str(category) + ' freq']
    return (all_categories, other_categories)

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

def get_term_doc_mat_coo(self, non_text: bool=False) -> coo_matrix:
    """
        Returns sparse matrix representation of term-doc-matrix

        Returns
        -------
        scipy.sparse.coo_matrix
        """
    return self.get_term_doc_mat(non_text=non_text).astype(np.double).tocoo()

def get_metadata_from_index(self, index: int) -> str:
    return self._metadata_idx_store.getval(index)

def get_term_from_index(self, index: int) -> str:
    return self._term_idx_store.getval(index)

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

def produce_scattertext_table(corpus: TermDocMatrix, num_rows: int=10, non_text: bool=False, plot_width=800, plot_height=600, category_order: Optional[List]=None, heading_categories: Optional[List]=None, heading_category_order: Optional[List]=None, d3_url_struct: Optional[D3URLs]=None, all_category_scorer: Optional[Union[AllCategoryScorer, Callable]]=None, trend_plot_settings: Optional[TrendPlotSettings]=None, show_chart: bool=True, show_category_headings: bool=False, header_clickable: bool=False, category_term_scores: Optional[np.array]=None, category_term_freqs: Optional[np.array]=None, **kwargs):
    """
    Parameters
    -----

    corpus: TermDocMatrix
    num_rows: int, Num rows in table, default 10
    non_text: bool, Use non-text features in table, default False
    plot_width: int, Scatterplot width in pixels, default 800
    plot_height: int, Scatterplot height in pixels, default 600
    category_order: Optional[List], list of categories in chronological order, default to sorted list of cats
    heading_categories: Optional[List], list of new, compacted categories per document
    heading_category_order: Optional[List], order of new, cmpacted categories
    d3_url_struct: Optional[D3URLs]
    all_category_scorer: Optional[Union[AllCategoryScorer, Callable]] = None
    trend_plot_settings: Optional[TrendPlotSettings] = None, default dispersion
    show_chart: bool = True, default, show line chart of ordered categories
    show_category_headings: bool = False, show list of category headings
    header_clickable: bool = False, allow clicking on header to show category scores
    term_category_scores: Optional[np.array]
    term_category_freqs: Optional[np.array]
    """
    alternative_term_func = '(function(termDict) {\n       //document.querySelectorAll(".dotgraph").forEach(svg => svg.style.display = \'none\');\n       //showTermGraph(termDict[\'term\']);\n       //alert(termDict[\'term\'])\n       return true;\n    })'
    if 'use_non_text_features' in kwargs or 'non_text' in kwargs or 'use_metadata' in kwargs:
        non_text = kwargs['use_non_text_features']
    heading_corpus = corpus
    if heading_categories is not None:
        assert len(heading_categories) == corpus.get_num_docs()
        heading_corpus = heading_corpus.recategorize(heading_categories)
    else:
        heading_categories = corpus.get_category_names_by_row()
    if heading_category_order is not None:
        assert set(heading_categories) == set(heading_category_order)
        assert len(heading_category_order) == len(set(heading_categories))
    else:
        heading_category_order = list(sorted(set(heading_categories)))
    table_maker = CategoryTableMaker(corpus=heading_corpus, num_rows=num_rows, non_text=non_text, category_order=heading_category_order, all_category_scorer_factory=all_category_scorer, header_clickable=header_clickable, term_category_scores=category_term_scores, term_category_freqs=category_term_freqs)
    if header_clickable:
        kwargs['include_term_category_counts'] = True
    if trend_plot_settings is None:
        trend_plot_settings = DispersionPlotSettings(metric='DA', category_order=category_order)
    scatterplot_structure = get_trend_scatterplot_structure(corpus=corpus, trend_plot_settings=trend_plot_settings, d3_url_struct=d3_url_struct, non_text=non_text, plot_width=plot_width, plot_height=plot_height, show_chart=show_chart, show_category_headings=show_category_headings, category_order=heading_category_order, kwargs=kwargs)
    html = TableStructure(scatterplot_structure, graph_renderer=table_maker, d3_url_struct=d3_url_struct).to_html()
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

def get_num_categories(self):
    """
        Returns the number of categories in the term document matrix
        :return: int
        """
    return len(self.get_categories())

def get_metadata_doc_count_df(self, label_append=' freq'):
    """

        Returns
        -------
        pd.DataFrame indexed on metadata, with columns the number of documents
        each metadata appeared in each category
        """
    mat = self.get_metadata_count_mat()
    return pd.DataFrame(mat, index=self.get_metadata(), columns=[str(c) + label_append for c in self.get_categories()])

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

def get_category_names_by_row(self):
    """
        Returns
        -------
        np.array of the category name for each row
        """
    return np.array(self.get_categories())[self._y]

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

def _get_neutral_categories(self):
    return [c for c in self.term_doc_mat.get_categories() if c not in self.relevant_categories]

class ParsedDataFrameCorpus(DataFrameCorpus):

    def __init__(self, parsed_col, category_col):
        self._parsed_col = parsed_col
        self._category_col = category_col

    def get_texts(self):
        """
        Returns
        -------
        pd.Series, all raw documents
        """
        if sys.version_info[0] == 2:
            return self._df[self._parsed_col]
        return self._df[self._parsed_col].apply(str)

    def get_parsed_docs(self):
        """
        Returns
        -------
        pd.Series, Doc represententions of texts.
        """
        return self._df[self._parsed_col]

    def get_category_token_counts(self) -> Dict[str, int]:
        """

        :return: dict, maps category to count of tokens of all documents in that category
        """
        return dict(self.get_df().groupby(self.get_category_column()).apply(lambda gdf: gdf[self.get_parsed_column()].apply(lambda doc: sum([t.orth_.strip() != '' for t in doc])).sum()))

    def get_category_column(self) -> str:
        return self._category_col

    def get_parsed_column(self) -> str:
        return self._parsed_col

def get_category_token_counts(self) -> Dict[str, int]:
    """

        :return: dict, maps category to count of tokens of all documents in that category
        """
    return dict(self.get_df().groupby(self.get_category_column()).apply(lambda gdf: gdf[self.get_parsed_column()].apply(lambda doc: sum([t.orth_.strip() != '' for t in doc])).sum()))

class ParsedCorpus(ParsedDataFrameCorpus):

    def __init__(self, df, X, mX, y, term_idx_store, category_idx_store, metadata_idx_store, parsed_col, category_col, unigram_frequency_path=None):
        """

        Parameters
        ----------
        convention_df pd.DataFrame, contains parsed_col and metadata
        X, csr_matrix
        mX csr_matrix
        y, np.array
        term_idx_store, IndexStore
        category_idx_store, IndexStore
        parsed_col str, column in convention_df containing parsed documents
        category_col str, columns in convention_df containing category
        unigram_frequency_path str, None by default, path of unigram counts file
        """
        ParsedDataFrameCorpus.__init__(self, parsed_col, category_col)
        DataFrameCorpus.__init__(self, X, mX, y, term_idx_store, category_idx_store, metadata_idx_store, df[self._parsed_col], df, unigram_frequency_path)

    def _make_new_term_doc_matrix(self, new_X=None, new_mX=None, new_y=None, new_term_idx_store=None, new_category_idx_store=None, new_metadata_idx_store=None, new_y_mask=None, new_df=None):
        X, mX, y = self._update_X_mX_y(new_X, new_mX, new_y, new_y_mask)
        return ParsedCorpus(X=X, mX=mX, y=y, parsed_col=self._parsed_col, category_col=self._category_col, term_idx_store=new_term_idx_store if new_term_idx_store is not None else self._term_idx_store, category_idx_store=new_category_idx_store if new_category_idx_store is not None else self._category_idx_store, metadata_idx_store=new_metadata_idx_store if new_metadata_idx_store is not None else self._metadata_idx_store, df=self._apply_mask_to_df(new_y_mask, new_df), unigram_frequency_path=self._unigram_frequency_path)

    def get_num_tokens_by_category(self) -> Dict[Hashable, int]:
        cat_to_num_toks = {cat: 0 for cat in self.get_categories()}
        for cat, cat_df in self.get_df().groupby(self.get_category_column()):
            cat_to_num_toks[cat] = cat_df[self.get_parsed_column()].apply(len).sum()
        return cat_to_num_toks

    def get_document_lengths_in_tokens(self):
        return self.get_parsed_docs().apply(len).values

    def get_document_lengths_in_tokens_and_categories(self):
        return pd.DataFrame({'Length': self.get_parsed_docs().apply(len).values, 'Category': self.get_category_names_by_row()})

    def term_group_freq_df(self, group_col):
        """
        Returns a dataframe indexed on the number of groups a term occured in.

        Parameters
        ----------
        group_col

        Returns
        -------
        pd.DataFrame
        """
        group_idx_store = IndexStore()
        X = self._X
        group_idx_to_cat_idx, row_group_cat = self._get_group_docids_and_index_store(X, group_col, group_idx_store)
        newX = self._change_document_type_in_matrix(X, row_group_cat)
        newX = self._make_all_positive_data_ones(newX)
        category_row = newX.tocoo().row
        for group_idx, cat_idx in group_idx_to_cat_idx.items():
            category_row[category_row == group_idx] = cat_idx
        catX = self._change_document_type_in_matrix(newX, category_row)
        return self._term_freq_df_from_matrix(catX)

    def _get_group_docids_and_index_store(self, X, group_col, group_idx_store):
        row_group_cat = X.tocoo().row
        group_idx_to_cat_idx = {}
        for doc_idx, row in self._df.iterrows():
            group_idx = group_idx_store.getidx(row[group_col] + '-' + row[self._category_col])
            row_group_cat[row_group_cat == doc_idx] = group_idx
            group_idx_to_cat_idx[group_idx] = self._y[doc_idx]
        return (group_idx_to_cat_idx, row_group_cat)

def get_num_tokens_by_category(self) -> Dict[Hashable, int]:
    cat_to_num_toks = {cat: 0 for cat in self.get_categories()}
    for cat, cat_df in self.get_df().groupby(self.get_category_column()):
        cat_to_num_toks[cat] = cat_df[self.get_parsed_column()].apply(len).sum()
    return cat_to_num_toks

def _get_group_docids_and_index_store(self, X, group_col, group_idx_store):
    row_group_cat = X.tocoo().row
    group_idx_to_cat_idx = {}
    for doc_idx, row in self._df.iterrows():
        group_idx = group_idx_store.getidx(row[group_col] + '-' + row[self._category_col])
        row_group_cat[row_group_cat == doc_idx] = group_idx
        group_idx_to_cat_idx[group_idx] = self._y[doc_idx]
    return (group_idx_to_cat_idx, row_group_cat)

class FeatureLister(object):

    def __init__(self, X, idx_store, num_docs):
        self.X = X
        self.idx_store = idx_store
        self.num_docs = num_docs

    def output(self) -> List[Dict[str, str]]:
        toret = [{} for i in range(self.num_docs)]
        X = self.X.tocoo()
        for row, col, val in zip(X.row, X.col, X.data):
            toret[row][self.idx_store.getval(col)] = val.item()
        return toret

def output(self) -> List[Dict[str, str]]:
    toret = [{} for i in range(self.num_docs)]
    X = self.X.tocoo()
    for row, col, val in zip(X.row, X.col, X.data):
        toret[row][self.idx_store.getval(col)] = val.item()
    return toret

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

def _get_term_doc_count_df(self):
    return self.term_ranker.get_ranks()[[t + ' freq' for t in self._get_all_categories()]]

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

def group_corpus_categories(self, category_order: Optional[List[str]]=None, number_of_splits: int=10) -> TermDocMatrix:
    new_categories, new_categories_order = self.get_new_doc_categories(category_order, number_of_splits)
    return self.corpus.recategorize(new_categories)

def _get_string_categories(self) -> List[str]:
    return [str(c) for c in self.corpus.get_categories()]

def _get_categories(self) -> List[str]:
    return self.corpus.get_categories()

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

def __init__(self, corpus, use_metadata=False, non_text=False, use_non_text_features=False, ranker=None, scorer=None):
    self.corpus = corpus
    self.use_metadata = use_metadata or non_text or use_non_text_features
    self.ranker, self.scorer = self._resolve_ranker_and_scorer(ranker=ranker, scorer=scorer)

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

def setUp(self):
    df = pd.DataFrame({'democrat': {'ago': 82, 'builds on': 1, 'filled': 3, 've got': 15, 'of natural': 2, 'and forged': 1, 'have built': 2, 's army': 4, 's protected': 1, 'the most': 28, 'gas alone': 1, 'you what': 9, 'few years': 8, 'gut education': 1, 's left': 2, 'for most': 1, 'raise': 18, 'problem can': 1, 'we the': 5, 'change will': 2}, 'republican': {'ago': 39, 'builds on': 0, 'filled': 5, 've got': 16, 'of natural': 0, 'and forged': 0, 'have built': 1, 's army': 0, 's protected': 0, 'the most': 23, 'gas alone': 0, 'you what': 8, 'few years': 13, 'gut education': 0, 's left': 1, 'for most': 2, 'raise': 11, 'problem can': 0, 'we the': 5, 'change will': 0}})
    self.term_cat_freq = TermCategoryFrequencies(df)

def test_get_categories(self):
    self.assertEqual(self.term_cat_freq.get_categories(), ['democrat', 'republican'])

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

def test_get_category_names_by_row2(self):
    hamlet = get_hamlet_term_doc_matrix()
    returned = hamlet.get_category_names_by_row()
    self.assertEqual(len(hamlet._y), len(returned))
    np.testing.assert_almost_equal([hamlet.get_categories().index(x) for x in returned], hamlet._y)

def test_get_metadata_count_mat(self):
    corpus = build_hamlet_jz_corpus_with_meta()
    np.testing.assert_array_almost_equal(corpus.get_metadata_count_mat(), [[4, 4]])

class WV:

    def __init__(self, vocab):
        self.key_to_index = {v: k for k, v in enumerate(vocab)}

    def __getitem__(self, item):
        assert item in self.key_to_index.keys()
        return np.zeros(30)

def __init__(self, vocab):
    self.key_to_index = {v: k for k, v in enumerate(vocab)}

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

def test_get_text(self):
    self.assertEqual(len([x for x in self.corpus.get_texts()]), len(self.documents))
    self.assertEqual([str(x) for x in self.corpus.get_texts()][0], "what art thou that usurp'st this time of night,")

def test_get_unigram_corpus(self):
    unicorp = self.corpus.get_unigram_corpus()
    self.assertEqual(len([x for x in unicorp.get_texts()]), len(self.documents))
    self.assertEqual([str(x) for x in unicorp.get_texts()][0], "what art thou that usurp'st this time of night,")

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

def test_get_y_and_populate_category_idx_store(self):
    corpus = self.corpus_fact.build()
    self.assertEqual([0, 0, 0, 0, 1, 1, 1, 1, 1, 2], list(corpus._y))
    self.assertEqual([(0, 'hamlet'), (1, 'jay-z/r. kelly'), (2, '???')], list(sorted(list(corpus._category_idx_store.items()))))

class TestTermDocMatrixFactory(TestCase):

    def test_build(self):
        term_doc_mat = build_hamlet_jz_term_doc_mat()
        self.assertEqual(term_doc_mat.get_num_docs(), 8)
        self.assertEqual(term_doc_mat.get_categories(), ['hamlet', 'jay-z/r. kelly'])

    def test_build_censor_entities(self):
        categories, documents = get_docs_categories()
        clean_function = lambda text: '' if text.startswith('[') else text
        term_doc_mat = TermDocMatrixFactory(category_text_iter=zip(categories, documents), clean_function=clean_function, nlp=_testing_nlp, feats_from_spacy_doc=FeatsFromSpacyDoc(entity_types_to_censor=set(['GPE']))).build()
        self.assertIn('_GPE', set(term_doc_mat.get_term_freq_df().index))
        self.assertNotIn('brooklyn', set(term_doc_mat.get_term_freq_df().index))

def test_build(self):
    term_doc_mat = build_hamlet_jz_term_doc_mat()
    self.assertEqual(term_doc_mat.get_num_docs(), 8)
    self.assertEqual(term_doc_mat.get_categories(), ['hamlet', 'jay-z/r. kelly'])

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

def test_get_texts(self):
    self.assertTrue(all(self.df['text'] == self.corpus.get_texts()))

def __concatenate_doc(corpus, doc_df, join_text, nlp):
    doc_str = join_text.join(doc_df[corpus.get_parsed_column()].apply(str))
    if nlp is None:
        nlp = spacy.blank('en')
    doc = nlp(doc_str)
    return doc

def __order_docs_to_concat(categories, corpus, domains_to_preserve, generator, join_text):
    doc_df = corpus.get_df().assign(_OrigIdx=lambda df: np.arange(len(df)).astype(int))
    if categories is not None:
        doc_df = doc_df[lambda df: df[corpus.get_category_column()].isin(categories)]
    doc_df = doc_df.assign(_Order=lambda df: df.index if generator is None else generator.random(size=len(df)), _Len=lambda df: df[corpus.get_parsed_column()].apply(str).apply(len)).sort_values(by=[] if domains_to_preserve is None else domains_to_preserve + ['_Order']).assign(StartOffset=lambda df: (df._Len + len(join_text)).shift(1).cumsum().fillna(0))
    return doc_df

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

def __get_sorted_doc_df(categories, corpus, domains_to_preserve, generator):
    doc_df = corpus.get_df()
    if categories is not None:
        doc_df = doc_df[lambda df: df[corpus.get_category_column()].isin(categories)]
    doc_df = doc_df.assign(_Order=lambda df: df.index if generator is None else generator.random(size=len(df)), _OriginalOrder=lambda df: np.arange(len(df))).sort_values(by=([] if domains_to_preserve is None else domains_to_preserve) + ['_Order'])
    return doc_df

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

def embed_all_categories(self):
    for category in self.corpus_.get_categories():
        self.embed_category(category)
    return self

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

def __add_gmeans_to_coef_freq_df(self, coef_freq_df: pd.DataFrame) -> pd.DataFrame:
    for cat in self.corpus_.get_categories():
        freq = Scalers.dense_rank(coef_freq_df[str(cat) + ' freq'])
        coef = Scalers.scale_neg_1_to_1_with_zero_mean(coef_freq_df[str(cat) + ' coef'])
        coef_freq_df[str(cat) + ' gmean'] = gmean([freq] * self.freq_weight_ + [coef] * self.coef_weight_)
    return coef_freq_df

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

def get_score_df(self, score_append=' Score', freq_append=' Freq') -> pd.DataFrame:
    rank_df = self.term_ranker_.get_ranks(label_append=freq_append)
    for category in self.corpus_.get_categories():
        scores = self.term_scorer_.set_categories(category_name=category).get_scores()
        rank_df[category + score_append] = scores
    return rank_df[sorted(rank_df.columns)]

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

def items(self) -> Iterable[Tuple[int, Any]]:
    return enumerate(self._i2val)

def _regenerate_val2i_and_next_i(self) -> None:
    self._val2i = {val: idx for idx, val in enumerate(self._i2val)}
    self._next_i = len(self._i2val)

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

def limit_nodes(self, nodes):
    return SimpleDiGraph(self.edge_df[self.edge_df.target_id.isin(nodes) | self.edge_df.source_id.isin(nodes)][['source', 'target']])

class TrendPlotSettings(ABC):

    def __init__(self, category_order: Optional[List]=None, **kwargs):
        self.category_order = category_order

    def get_category_ranks(self, corpus: TermDocMatrix) -> np.array:
        if self.category_order is None:
            self.category_order = list(sorted(corpus.get_categories()))
        category_rank = {cat: i for i, cat in enumerate(self.category_order)}
        return np.array([category_rank[category] for category in corpus.get_category_names_by_row()])

    @abstractmethod
    def get_plot_params(self) -> TrendPlotPresets:
        pass

def get_category_ranks(self, corpus: TermDocMatrix) -> np.array:
    if self.category_order is None:
        self.category_order = list(sorted(corpus.get_categories()))
    category_rank = {cat: i for i, cat in enumerate(self.category_order)}
    return np.array([category_rank[category] for category in corpus.get_category_names_by_row()])

class TimePlotPositioner:

    def __init__(self, corpus: TermDocMatrix, category_order: List, non_text: bool=True, dispersion_metric: str='DA', use_residual: bool=False):
        self.corpus = corpus
        self.category_order = category_order
        assert set(category_order) == set(corpus.get_categories())
        self.non_text = non_text
        self.dispersion_metric = dispersion_metric
        self.use_residual = use_residual

    def get_position_df(self) -> pd.DataFrame:
        category_order_idx = IndexStoreFromList.build(self.category_order)
        category_values = np.array([category_order_idx.getidx(v) for v in self.corpus.get_category_names_by_row()])
        tdm = self.corpus.get_term_doc_mat(non_text=self.non_text)
        freq = tdm.sum(axis=0).A1
        dispersion = Dispersion(corpus=self.corpus, non_text=self.non_text, use_categories_as_documents=True)
        if self.use_residual:
            dispersion_df = dispersion.get_adjusted_metric_df(metric=self.dispersion_metric)
            dispersion_value = dispersion_df['Residual'].values
        else:
            dispersion_df = dispersion.get_df(include_da=self.dispersion_metric == 'DA')
            dispersion_value = dispersion_df[self.dispersion_metric].values
        position_df = pd.DataFrame({'Frequency': freq, 'Mean': category_values * tdm / freq, 'term': self.corpus.get_terms(use_metadata=self.non_text), 'Dispersion': dispersion_value}).set_index('term').assign(MeanCategory=lambda df: np.array(self.category_order)[df.Mean.round().astype(int)])
        return position_df

def __init__(self, corpus: TermDocMatrix, category_order: List, non_text: bool=True, dispersion_metric: str='DA', use_residual: bool=False):
    self.corpus = corpus
    self.category_order = category_order
    assert set(category_order) == set(corpus.get_categories())
    self.non_text = non_text
    self.dispersion_metric = dispersion_metric
    self.use_residual = use_residual

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

def get_sentence_word_mat(self):
    return self.sentX.astype(np.double).tocoo()

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

def _get_neut_row_mask(self):
    return np.isin(self.corpus_.get_category_names_by_row(), self.neutral_category_names)

def _get_ncat_x_row_mask(self):
    return np.isin(self.corpus_.get_category_names_by_row(), self.not_category_names)

def _get_cat_x_row_mask(self):
    return np.isin(self.corpus_.get_category_names_by_row(), [self.category_name])

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

def __iter_docs_and_cats(self, verbose: bool):
    it = self.corpus.get_df()[[self.corpus.get_category_column(), self.corpus.get_parsed_column()]].rename(columns={self.corpus.get_category_column(): 'Cat', self.corpus.get_parsed_column(): 'Doc'}).itertuples()
    if verbose:
        it = tqdm(it, total=self.corpus.get_num_docs())
    return enumerate(it)

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

def gethmean(x):
    if min(x[vals]) == 0:
        return 0
    return sum(weights) * 1.0 / sum([weights[i] / x[val] for i, val in enumerate(vals)])

def _regress_terms(self, X, cat, categories, category_idx_store, neg_mask, terms):
    pos_mask = categories.isin(category_idx_store.getidxstrictbatch([cat])).values
    catX = X[neg_mask | pos_mask, :]
    catY = np.zeros(catX.shape[0]).astype(bool)
    catY[pos_mask[neg_mask | pos_mask]] = True
    scores = pd.Series(self._get_model().fit(catX, catY).coef_[0], index=terms).sort_values(ascending=False)
    return scores

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

def _get_negative_categories(self, cat, tdf):
    return sorted([x for x in tdf.columns if x < cat])[-self.timesteps_to_lag:]

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

class SentenceSequenceSegmenter:

    def __init__(self, segment_length: int=500):
        self.segment_length = segment_length

    def whole_df_to_segmented_df(self, df: pd.DataFrame, parsed_col: str, verbose: bool=False) -> pd.DataFrame:
        assert parsed_col in df.columns
        segment_data = []
        docit = enumerate(df[parsed_col])
        if verbose:
            docit = tqdm(docit, total=len(df))
        for doc_i, doc in docit:
            segment = []
            segment_len = 0
            segment_idx = 0
            for _, sent in enumerate(doc.sents):
                if segment_len == 0:
                    segment = [sent]
                    segment_len += len(sent)
                elif segment_len + len(sent) > self.segment_length:
                    segment_data.append({'Text': str(doc[segment[0][0].i:segment[-1][-1].i + 1]), 'DocIdx': doc_i, 'SegmentIdx': segment_idx})
                    segment_idx += 1
                    segment = []
                    segment_len = 0
                else:
                    segment.append(sent)
                    segment_len += len(sent)
            if segment_len > 0:
                segment_data.append({'Text': str(doc[segment[0][0].i:segment[-1][-1].i + 1]), 'DocIdx': doc_i, 'SegmentIdx': segment_idx})
        return pd.DataFrame(segment_data)

def whole_df_to_segmented_df(self, df: pd.DataFrame, parsed_col: str, verbose: bool=False) -> pd.DataFrame:
    assert parsed_col in df.columns
    segment_data = []
    docit = enumerate(df[parsed_col])
    if verbose:
        docit = tqdm(docit, total=len(df))
    for doc_i, doc in docit:
        segment = []
        segment_len = 0
        segment_idx = 0
        for _, sent in enumerate(doc.sents):
            if segment_len == 0:
                segment = [sent]
                segment_len += len(sent)
            elif segment_len + len(sent) > self.segment_length:
                segment_data.append({'Text': str(doc[segment[0][0].i:segment[-1][-1].i + 1]), 'DocIdx': doc_i, 'SegmentIdx': segment_idx})
                segment_idx += 1
                segment = []
                segment_len = 0
            else:
                segment.append(sent)
                segment_len += len(sent)
        if segment_len > 0:
            segment_data.append({'Text': str(doc[segment[0][0].i:segment[-1][-1].i + 1]), 'DocIdx': doc_i, 'SegmentIdx': segment_idx})
    return pd.DataFrame(segment_data)

class TokenSequenceSegmenter:

    def __init__(self, segment_length: int=500):
        self.segment_length = segment_length

    def whole_df_to_segmented_df(self, df: pd.DataFrame, parsed_col: str, verbose: bool=False) -> pd.DataFrame:
        assert parsed_col in df.columns
        segment_data = []
        docit = enumerate(df[parsed_col])
        if verbose:
            docit = tqdm(docit, total=len(df))
        for doc_i, doc in docit:
            for i in range(max(len(doc) // self.segment_length, 1)):
                start_token_idx = self.segment_length * i
                end_token_idx = -1 if self.segment_length * (i + 1) >= len(doc) else self.segment_length * (i + 1)
                start_idx = doc[start_token_idx].idx
                end_idx = doc[end_token_idx].idx + len(doc[end_token_idx])
                segment_text = str(doc)[start_idx:end_idx]
                segment_data.append({'Text': segment_text, 'DocIdx': doc_i, 'SegmentIdx': i})
        return pd.DataFrame(segment_data)

def whole_df_to_segmented_df(self, df: pd.DataFrame, parsed_col: str, verbose: bool=False) -> pd.DataFrame:
    assert parsed_col in df.columns
    segment_data = []
    docit = enumerate(df[parsed_col])
    if verbose:
        docit = tqdm(docit, total=len(df))
    for doc_i, doc in docit:
        for i in range(max(len(doc) // self.segment_length, 1)):
            start_token_idx = self.segment_length * i
            end_token_idx = -1 if self.segment_length * (i + 1) >= len(doc) else self.segment_length * (i + 1)
            start_idx = doc[start_token_idx].idx
            end_idx = doc[end_token_idx].idx + len(doc[end_token_idx])
            segment_text = str(doc)[start_idx:end_idx]
            segment_data.append({'Text': segment_text, 'DocIdx': doc_i, 'SegmentIdx': i})
    return pd.DataFrame(segment_data)

