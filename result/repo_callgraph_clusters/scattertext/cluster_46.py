# Cluster 46

def _parse_geutenberg(url):
    return urlopen(url).read().decode('utf-8').split("Transcriber's Notes")[0].split('-------------------------------------------------------')[-1]

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

def get_scaled_f_scores_vs_background(self, scaler_algo=DEFAULT_BACKGROUND_SCALER_ALGO, beta=DEFAULT_BACKGROUND_BETA):
    df = self.get_term_and_background_counts()
    df['Scaled f-score'] = ScaledFScore.get_scores_for_category(df['corpus'], df['background'], scaler_algo, beta)
    return df.sort_values(by='Scaled f-score', ascending=False)

def _get_background_unigram_frequencies(self):
    if self._unigram_frequency_path:
        unigram_freq_table_buf = open(self._unigram_frequency_path)
    else:
        unigram_freq_table_buf = StringIO(pkgutil.get_data('scattertext', 'data/count_1w.txt').decode('utf-8'))
    to_ret = pd.read_table(unigram_freq_table_buf, names=['word', 'background']).sort_values(ascending=False, by='background').drop_duplicates(['word']).set_index('word')
    return to_ret

class ConventionData2012(object):

    @staticmethod
    def _speaker_name_factory():
        name_re = re.compile(".*(\\n|^)(?P<name>[A-Z0-9 \\.\\']+):\\w*.+", re.M)

        def speaker_name(text):
            for _, name in name_re.findall(text):
                if name not in ('ANNOUNCER', 'AUDIENCE MEMBER', 'AUDIENCE MEMBERS'):
                    return name
        return speaker_name

    @staticmethod
    def _clean_function_factory():
        only_speaker_text_re = re.compile("((^|\\n)((ANNOUNCER|AUDIENCE MEMBERS?): .+)($|\\n)|(\\n|^)((([A-Z\\.()\\-\\' ]+): ))|\\(.+\\) *)", re.M)
        assert only_speaker_text_re.sub('', 'AUDIENCE MEMBERS: (Chanting.) USA! USA! USA! USA!') == ''
        assert only_speaker_text_re.sub('', 'AUDIENCE MEMBER: (Chanting.) USA! USA! USA! USA!') == ''
        assert only_speaker_text_re.sub('', 'ANNOUNCER: (Chanting.) USA! USA! USA! USA!') == ''
        assert only_speaker_text_re.sub('', 'TOM SMITH: (Chanting.) USA! USA! USA! USA!') == 'USA! USA! USA! USA!'
        assert only_speaker_text_re.sub('', 'DONALD TRUMP: blah blah blah!') == 'blah blah blah!'
        assert only_speaker_text_re.sub('', 'HILLARY CLINTON: (something parenthetical) blah blah blah!') == 'blah blah blah!'
        assert only_speaker_text_re.sub('', 'ANNOUNCER: (Chanting.) USA! USA! USA! USA!\nTOM SMITH: (Chanting.) ONLY INCLUDE THIS! ONLY KEEP THIS! \nAUDIENCE MEMBER: (Chanting.) USA! USA! USA! USA!').strip() == 'ONLY INCLUDE THIS! ONLY KEEP THIS!'

        def clean_document(text):
            return only_speaker_text_re.sub('', text)
        return clean_document

    @staticmethod
    def _convention_speech_iter():
        try:
            data_stream = pkgutil.get_data('scattertext', 'data/political_data.json').decode('utf-8')
        except:
            url = POLITICAL_DATA_URL
            data_stream = urlopen(url).read().decode('utf-8')
        return json.loads(data_stream)

    @staticmethod
    def _iter_party_speech_pairs():
        for speaker_obj in ConventionData2012._convention_speech_iter():
            political_party = speaker_obj['name']
            for speech in speaker_obj['speeches']:
                yield (political_party, speech)

    @staticmethod
    def get_data():
        clean = ConventionData2012._clean_function_factory()
        get_speaker_name = ConventionData2012._speaker_name_factory()
        data = []
        for party, speech in ConventionData2012._iter_party_speech_pairs():
            cleaned_speech = clean(speech)
            speaker_name = get_speaker_name(speech)
            if cleaned_speech and cleaned_speech != '' and (speaker_name != ''):
                data.append({'party': party, 'text': cleaned_speech, 'speaker': speaker_name})
        return pd.DataFrame(data)

@staticmethod
def _convention_speech_iter():
    try:
        data_stream = pkgutil.get_data('scattertext', 'data/political_data.json').decode('utf-8')
    except:
        url = POLITICAL_DATA_URL
        data_stream = urlopen(url).read().decode('utf-8')
    return json.loads(data_stream)

class GuardianHeadlines(object):
    """
	Guardian financial headlines from year 2020. Data derived from
	https://www.kaggle.com/datasets/notlucasp/financial-news-headlines?resource=download
	"""

    @staticmethod
    def get_data():
        """
		Returns
		-------
		pd.DataFrame

		I.e.,
		>>> headline_df.iloc[0]
		Unnamed: 0                                                   0
		Text          Johnson is asking Santa for a Christmas recovery
		Date                                                2020-07-18
		"""
        data_stream = pkgutil.get_data('scattertext', 'data/guardian_headlines.csv.bz2')
        return pd.read_csv(io.BytesIO(bz2.decompress(data_stream))).assign(Date=lambda df: pd.to_datetime(df.Date))

@staticmethod
def get_data():
    """
		Returns
		-------
		pd.DataFrame

		I.e.,
		>>> headline_df.iloc[0]
		Unnamed: 0                                                   0
		Text          Johnson is asking Santa for a Christmas recovery
		Date                                                2020-07-18
		"""
    data_stream = pkgutil.get_data('scattertext', 'data/guardian_headlines.csv.bz2')
    return pd.read_csv(io.BytesIO(bz2.decompress(data_stream))).assign(Date=lambda df: pd.to_datetime(df.Date))

class RottenTomatoes(object):
    """
	Derived from the sentiment polarity/subjectivity datasets from
	http://www.cs.cornell.edu/people/pabo/movie-review-data/

	Bo Pang and Lillian Lee. ``A Sentimental Education: Sentiment Analysis Using Subjectivity
	 Summarization Based on Minimum Cuts'', Proceedings of the ACL, 2004.
	"""

    @staticmethod
    def get_data():
        """
		Returns
		-------
		pd.DataFrame

		I.e.,
		>>> convention_df.iloc[0]
		category                                                    plot
		filename                 subjectivity_html/obj/2002/Abandon.html
		text           A senior at an elite college (Katie Holmes), a...
		movie_name                                               abandon
		"""
        try:
            data_stream = pkgutil.get_data('scattertext', 'data/rotten_tomatoes_corpus.csv.bz2')
        except:
            url = ROTTEN_TOMATOES_DATA_URL
            data_stream = urlopen(url).read()
        return pd.read_csv(io.BytesIO(bz2.decompress(data_stream)))

    @staticmethod
    def get_full_data():
        """
		Returns all plots and reviews, not just the ones that appear in movies with both plot descriptions and reviews.

		Returns
		-------
		pd.DataFrame

		I.e.,
		>>> convention_df.iloc[0]
		category                                                             plot
		text                    Vijay Singh Rajput (Amitabh Bachchan) is a qui...
		movie_name                                                        aankhen
		has_plot_and_reviews                                                False
		Name: 0, dtype: object
		"""
        try:
            data_stream = pkgutil.get_data('scattertext', 'data/rotten_tomatoes_corpus_full.csv.bz2')
        except:
            url = ROTTEN_TOMATOES_DATA_URL
            data_stream = urlopen(url).read()
        return pd.read_csv(io.BytesIO(bz2.decompress(data_stream)))

@staticmethod
def get_data():
    """
		Returns
		-------
		pd.DataFrame

		I.e.,
		>>> convention_df.iloc[0]
		category                                                    plot
		filename                 subjectivity_html/obj/2002/Abandon.html
		text           A senior at an elite college (Katie Holmes), a...
		movie_name                                               abandon
		"""
    try:
        data_stream = pkgutil.get_data('scattertext', 'data/rotten_tomatoes_corpus.csv.bz2')
    except:
        url = ROTTEN_TOMATOES_DATA_URL
        data_stream = urlopen(url).read()
    return pd.read_csv(io.BytesIO(bz2.decompress(data_stream)))

@staticmethod
def get_full_data():
    """
		Returns all plots and reviews, not just the ones that appear in movies with both plot descriptions and reviews.

		Returns
		-------
		pd.DataFrame

		I.e.,
		>>> convention_df.iloc[0]
		category                                                             plot
		text                    Vijay Singh Rajput (Amitabh Bachchan) is a qui...
		movie_name                                                        aankhen
		has_plot_and_reviews                                                False
		Name: 0, dtype: object
		"""
    try:
        data_stream = pkgutil.get_data('scattertext', 'data/rotten_tomatoes_corpus_full.csv.bz2')
    except:
        url = ROTTEN_TOMATOES_DATA_URL
        data_stream = urlopen(url).read()
    return pd.read_csv(io.BytesIO(bz2.decompress(data_stream)))

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

def _limit_max_terms(self, category, df):
    df['score'] = self._term_importance_ranks(category, df)
    df = df.loc[df.sort_values('score').iloc[:self.scatterchartdata.max_terms].index]
    return df[[c for c in df.columns if c != 'score']]

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

def _get_frequency_percentiles(self, mask):
    freqs = self._X[mask].sum(axis=0).A1
    percentiles = self._get_percentiles_from_freqs(freqs)
    return percentiles

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
def _get_score_terms(num_term_to_keep, term_doc_freq):
    sorted_tdf = term_doc_freq.sort_values(by='score', ascending=False)
    return sorted_tdf.iloc[:int(0.25 * num_term_to_keep)].index.union(sorted_tdf.iloc[-int(0.25 * num_term_to_keep):].index)

class WhissellsLexicon(object):
    """
    From http://www.cs.columbia.edu/~julia/papers/dict_of_affect/DictionaryofAffect.

    Developed by Cynthia Whissell at Laurentian University.

    Header:
    new dictionary with imagery (c) C Whissell


    comment w=word, ee=pleasantness, aa=activation, ii=imagery

    comment scores for pleasantness range from 1 (unpleasant) to 3 (pleasant)
            scores for activation range from 1 (passive) to 3 (active)
            scores for imagery range from 1 (difficult to form a meantal
              picture of this word) to 3 (easy to form a mental picture)

    comment pleasantness mean=1.84, sd=.44
            activation mean=1.85, sd=.39
            imagery (does word give you a clear mental picture) mean=1.94, sd=.63

    comment these values have been tested on 348,000 words of natural language
        the dictionary has a 90% matching rate for this corpus
        mean ee is 1.85, with an sd of .36
        mean aa is 1.67, with an sd of .36
        mean ii is 1.52, with an sd of .63

    """

    @staticmethod
    def get_data():
        """
        Returns
        -------
        pd.DataFrame

        I.e.,
        >>> print(WhissellsLexicon.get_data())
                     activation  imagery  pleasantness
        word
        a                1.3846      1.0        2.0000
        abandon          2.3750      2.4        1.0000
        abandoned        2.1000      3.0        1.1429
        abandonment      2.0000      1.4        1.0000
        abated           1.3333      1.2        1.6667
        """
        data_stream = pkgutil.get_data('scattertext', 'data/whissells_df.csv')
        return pd.read_csv(io.StringIO(data_stream.decode('utf8'))).set_index('word').astype(np.float64)

@staticmethod
def get_data():
    """
        Returns
        -------
        pd.DataFrame

        I.e.,
        >>> print(WhissellsLexicon.get_data())
                     activation  imagery  pleasantness
        word
        a                1.3846      1.0        2.0000
        abandon          2.3750      2.4        1.0000
        abandoned        2.1000      3.0        1.1429
        abandonment      2.0000      1.4        1.0000
        abated           1.3333      1.2        1.6667
        """
    data_stream = pkgutil.get_data('scattertext', 'data/whissells_df.csv')
    return pd.read_csv(io.StringIO(data_stream.decode('utf8'))).set_index('word').astype(np.float64)

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

def _build_lexicons(self):
    axes_parts_df = add_radial_parts_and_mag_to_term_coordinates(term_coordinates_df=self.axes)
    self.axes['color'] = axes_parts_df.Part.apply(lambda x: HALO_COLORS.get(x.replace('left', 'RIGHT').replace('right', 'left').replace('RIGHT', 'right')))
    self.lexicons = {semiotic_square_label: axes_parts_df[lambda df: df.Part == part].sort_values(by='Mag', ascending=False) for semiotic_square_label, part in SEMIOTIC_SQUARE_TO_PART.items()}
    return self.lexicons

def term_coordinates_to_halo(term_coordinates_df: pd.DataFrame, num_terms: int=5) -> dict:
    return dict(add_radial_parts_and_mag_to_term_coordinates(term_coordinates_df=term_coordinates_df).sort_values(by='Mag', ascending=False).groupby('Part').apply(lambda gdf: list(gdf.iloc[:num_terms].index)))

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

def __get_cat_df(self, display_df):
    cat_df = display_df[['Category', 'CategoryNum']].drop_duplicates().sort_values(by='CategoryNum')
    return cat_df

class DefaultBackgroundFrequencies(BackgroundFrequencies):

    @staticmethod
    def get_background_frequency_df(frequency_path=None):
        if frequency_path:
            unigram_freq_table_buf = open(frequency_path)
        else:
            unigram_freq_table_buf = StringIO(pkgutil.get_data('scattertext', 'data/count_1w.txt').decode('utf-8'))
        to_ret = pd.read_csv(unigram_freq_table_buf, sep='\t', names=['word', 'background']).sort_values(ascending=False, by='background').drop_duplicates(['word']).set_index('word')['background']
        return to_ret

@staticmethod
def get_background_frequency_df(frequency_path=None):
    if frequency_path:
        unigram_freq_table_buf = open(frequency_path)
    else:
        unigram_freq_table_buf = StringIO(pkgutil.get_data('scattertext', 'data/count_1w.txt').decode('utf-8'))
    to_ret = pd.read_csv(unigram_freq_table_buf, sep='\t', names=['word', 'background']).sort_values(ascending=False, by='background').drop_duplicates(['word']).set_index('word')['background']
    return to_ret

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

def get_max_rank(self, term_doc_matrix) -> float:
    """

        :param term_doc_matrix: TermDocMatrix
        :return: int
        """
    rank_df = self.get_rank_df(term_doc_matrix)
    return rank_df.max().max()

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

def _prune_higher_ranked_terms(self, term_doc_matrix, rank_df, rank):
    terms_to_remove = rank_df.index[np.isnan(rank_df[rank_df <= rank]).apply(lambda x: all(x), axis=1)]
    return self._remove_terms(term_doc_matrix, terms_to_remove)

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

def compact(self, term_doc_matrix, verbose=False):
    rank_df = self.scorer.get_rank_df(term_doc_matrix)
    p_df = rank_df / rank_df.sum(axis=0) + 0.001
    m = p_df.sum(axis=1)

    def lg(x):
        return np.log(x) / np.log(2)
    rank_df['Score'] = m * lg(1 / m) - (p_df * lg(1 / p_df)).sum(axis=1)
    terms_to_remove = rank_df.sort_values(by='Score', ascending=False).iloc[self.max_terms:].index
    return term_doc_matrix.remove_terms(terms_to_remove, self.scorer.use_non_text_features)

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

class AssociationCompactorByRank(BaseAssociationCompactor):

    def __init__(self, rank, scorer=ScaledFScorePresetsNeg1To1, term_ranker=AbsoluteFrequencyRanker, use_non_text_features=False, target_category: Optional[str]=None):
        self.rank = rank
        BaseAssociationCompactor.__init__(self, scorer, term_ranker, use_non_text_features, target_category)

    def compact(self, term_doc_matrix):
        """
        Parameters
        ----------
        term_doc_matrix : TermDocMatrix
            Term document matrix object to compact
        Returns
        -------
        TermDocMatrix


        """
        rank_df = self.scorer.get_rank_df(term_doc_matrix)
        return self._prune_higher_ranked_terms(term_doc_matrix, rank_df, self.rank)

def compact(self, term_doc_matrix):
    """
        Parameters
        ----------
        term_doc_matrix : TermDocMatrix
            Term document matrix object to compact
        Returns
        -------
        TermDocMatrix


        """
    rank_df = self.scorer.get_rank_df(term_doc_matrix)
    return self._prune_higher_ranked_terms(term_doc_matrix, rank_df, self.rank)

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

def test_get_term_freq_df(self):
    df = self.tdm.get_term_freq_df().sort_values('b freq', ascending=False)[:3]
    self.assertEqual(list(df.index), ['another', 'blah', 'blah blah'])
    self.assertEqual(list(df['a freq']), [0, 0, 0])
    self.assertEqual(list(df['b freq']), [4, 3, 2])
    self.assertEqual(list(self.tdm.get_term_freq_df().sort_values('a freq', ascending=False)[:3]['a freq']), [2, 2, 1])

def get_hamlet_docs():
    try:
        cwd = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(cwd, '..', 'data', 'hamlet.txt')
        buf = open(path).read()
    except:
        buf = pkgutil.get_data('scattertext', os.path.join('data', 'hamlet.txt'))
    hamlet_docs = buf.split('\n\n')
    return hamlet_docs

class TestVizDataAdapter(TestCase):

    def test_to_javascript(self):
        js_str = make_viz_data_adapter().to_javascript()
        self.assertEqual(js_str[:34], 'function getDataAndInfo() { return')
        self.assertEqual(js_str[-3:], '; }')
        json_str = js_str[34:-3]
        self.assertEqual(PAYLOAD, json.loads(json_str))

    def test_to_json(self):
        json_str = make_viz_data_adapter().to_json()
        self.assertEqual(PAYLOAD, json.loads(json_str))

def test_to_javascript(self):
    js_str = make_viz_data_adapter().to_javascript()
    self.assertEqual(js_str[:34], 'function getDataAndInfo() { return')
    self.assertEqual(js_str[-3:], '; }')
    json_str = js_str[34:-3]
    self.assertEqual(PAYLOAD, json.loads(json_str))

def test_to_json(self):
    json_str = make_viz_data_adapter().to_json()
    self.assertEqual(PAYLOAD, json.loads(json_str))

def convention_speech_iter():
    relative_path = os.path.join('../scattertext/data', 'political_data.json')
    try:
        cwd = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(cwd, relative_path)
        return json.load(open(path))
    except:
        return json.loads(pkgutil.get_data('scattertext', relative_path).decode('utf-8'))

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

def get_svg(self, dot_str):
    import graphviz as gv
    return gv.Source(dot_str, format='svg', engine=self.engine).pipe().decode('utf-8')

class NLTKTagger:
    """
	class that supplies part of speech tags using NLTK
	note: avoids the NLTK downloader (see __init__ method)
	"""

    def __init__(self):
        import nltk
        from nltk.tag import PerceptronTagger
        from nltk.tokenize import TreebankWordTokenizer
        path = os.path.dirname(sys.modules['scattertext'].__file__) + '/data/'
        tokenizer_fn = path + 'punkt.english.pickle'
        tagger_fn = path + 'averaged_perceptron_tagger.pickle'
        self.tagger = PerceptronTagger(load=False)
        self.tagger.load(tagger_fn)
        self.tokenize = TreebankWordTokenizer().tokenize
        self.sent_detector = nltk.data.load(tokenizer_fn)

    def tag_text(self, text):
        """take input text and return tokens w/ part of speech tags using NLTK"""
        sents = self.sent_detector.tokenize(text)
        word_pos_pairs = []
        all_tokens = []
        for sent in sents:
            tokens = self.tokenize(sent)
            all_tokens = all_tokens + tokens
            word_pos_pairs = word_pos_pairs + self.tagger.tag(tokens)
        return {'tokens': all_tokens, 'pos': [tag for w, tag in word_pos_pairs]}

    def tag_tokens(self, tokens):
        word_pos_pairs = self.tagger.tag(tokens)
        return {'tokens': tokens, 'pos': [tag for w, tag in word_pos_pairs]}

def __init__(self):
    import nltk
    from nltk.tag import PerceptronTagger
    from nltk.tokenize import TreebankWordTokenizer
    path = os.path.dirname(sys.modules['scattertext'].__file__) + '/data/'
    tokenizer_fn = path + 'punkt.english.pickle'
    tagger_fn = path + 'averaged_perceptron_tagger.pickle'
    self.tagger = PerceptronTagger(load=False)
    self.tagger.load(tagger_fn)
    self.tokenize = TreebankWordTokenizer().tokenize
    self.sent_detector = nltk.data.load(tokenizer_fn)

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
def get_scores_for_category(cat_word_counts, not_cat_word_counts):
    cat_pctls = CornerScore._get_percentiles_from_freqs(cat_word_counts)
    not_cat_pctls = CornerScore._get_percentiles_from_freqs(not_cat_word_counts)
    return CornerScore._distance_from_upper_left(cat_pctls, not_cat_pctls)

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

def get_scores(self, a, b):
    p1 = 0.001 + a / np.sum(a)
    p2 = 0.001 + b / np.sum(b)
    pi1, pi2 = (self.pi1, self.pi2)
    m = pi1 * p1 + pi2 * p2

    def lg(x):
        return np.log(x) / np.log(2)
    return m * lg(1 / m) - (pi1 * p2 * lg(1 / p1) + pi2 * p2 * lg(1 / p2))

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

def _load_mfd(self):
    return pd.read_csv(io.StringIO(pkgutil.get_data('scattertext', 'data/mfd2.0.csv').decode('utf-8'))).set_index('term')

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

def get_top_model_term_lists(self):
    return {col: list(self._lexicon_df[col].sort_values(ascending=False).iloc[:10].index) for col in self._lexicon_df}

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

def __init__(self):
    self.lex_dict = pd.read_csv(io.BytesIO(bz2.decompress(pkgutil.get_data('scattertext', 'data/roget.csv.bz2'))), names=['term', 'category']).set_index('term')['category'].to_dict()

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

def _download_and_parse_general_inquirer(self):
    df = pd.read_csv(GENERAL_INQUIRER_URL, sep='\t')
    return df.T[2:-4].apply(lambda x: list(df.Entry.apply(lambda x: x.split('#')[0]).loc[x.dropna().index].drop_duplicates().apply(str.lower)), axis=1).apply(pd.Series).stack().reset_index()[['level_0', 0]].rename(columns={'level_0': 'cat', 0: 'term'}).set_index('term')

class HTMLSemioticSquareViz(object):

    def __init__(self, semiotic_square):
        """
		Parameters
		----------
		semiotic_square : SemioticSquare
		"""
        self.semiotic_square_ = semiotic_square

    def get_html(self, num_terms=10):
        return self._get_style() + self._get_table(num_terms)

    def _get_style(self):
        return get_halo_td_style()

    def _get_table(self, num_terms):
        lexicons = self.semiotic_square_.get_lexicons(num_terms=num_terms)
        template = self._get_template()
        formatters = {category: self._lexicon_to_html(lexicon) for category, lexicon in lexicons.items()}
        formatters.update(self.semiotic_square_.get_labels())
        for k, v in formatters.items():
            template = template.replace('{' + k + '}', v)
        return template

    def _lexicon_to_html(self, lexicon):
        return ClickableTerms.get_clickable_lexicon(lexicon)

    def _get_template(self):
        return pkgutil.get_data('scattertext', SEMIOTIC_SQUARE_HTML_PATH).decode('utf-8')

def _get_template(self):
    return pkgutil.get_data('scattertext', SEMIOTIC_SQUARE_HTML_PATH).decode('utf-8')

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

def to_javascript(self, function_name='getDataAndInfo'):
    return 'function ' + function_name + '() { return' + self.to_json() + '; }'

class PackedDataUtils:

    @staticmethod
    def full_content_of_default_html_template():
        return PackedDataUtils.get_packaged_html_template_content(DEFAULT_HTML_VIZ_FILE_NAME)

    @staticmethod
    def full_content_of_default_autocomplete_css():
        return PackedDataUtils.get_packaged_html_template_content(AUTOCOMPLETE_CSS_FILE_NAME)

    @staticmethod
    def full_content_of_default_search_form(input_id):
        return PackedDataUtils.get_packaged_html_template_content(SEARCH_FORM_FILE_NAME).replace('{{id}}', input_id)

    @staticmethod
    def full_content_of_javascript_files():
        return PackedDataUtils._load_script_file_names(['rectangle-holder.js', 'main.js', 'autocomplete_definition.js'])

    @staticmethod
    def _load_script_file_names(script_names):
        return '; \n \n '.join([PackedDataUtils.get_packaged_script_content(script_name) for script_name in script_names])

    @staticmethod
    def javascript_post_build_viz(input_id, plot_interface_name):
        return PackedDataUtils._load_script_file_names(['autocomplete_call.js']).replace('{{id}}', input_id).replace('__plotInterface__', plot_interface_name)

    @staticmethod
    def get_packaged_script_content(file_name):
        return pkgutil.get_data('scattertext', 'data/viz/scripts/' + file_name).decode('utf-8')

    @staticmethod
    def get_packaged_html_template_content(file_name):
        return pkgutil.get_data('scattertext', 'data/viz/' + file_name).decode('utf-8')

@staticmethod
def get_packaged_script_content(file_name):
    return pkgutil.get_data('scattertext', 'data/viz/scripts/' + file_name).decode('utf-8')

@staticmethod
def get_packaged_html_template_content(file_name):
    return pkgutil.get_data('scattertext', 'data/viz/' + file_name).decode('utf-8')

