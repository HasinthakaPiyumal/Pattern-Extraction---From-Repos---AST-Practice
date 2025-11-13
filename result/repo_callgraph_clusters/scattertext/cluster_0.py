# Cluster 0

def exclude_ngrams_which_do_not_start_and_end_with_function_words(ngram: spacy.tokens.Span) -> bool:
    return any([ngram[0].lower_.strip() in st.MY_ENGLISH_STOP_WORDS, ngram[-1].lower_.strip() in st.MY_ENGLISH_STOP_WORDS, word_number_matcher.match(ngram[0].lower_.strip()) is None, word_number_matcher.match(ngram[-1].lower_.strip()) is None])

def exclude_ngrams_which_do_not_start_and_end_with_function_words(ngram: spacy.tokens.Span) -> bool:
    return any([ngram[0].lower_.strip() in st.MY_ENGLISH_STOP_WORDS, ngram[-1].lower_.strip() in st.MY_ENGLISH_STOP_WORDS, word_number_matcher.match(ngram[0].lower_.strip()) is None, word_number_matcher.match(ngram[-1].lower_.strip()) is None])

def exclude_ngrams_which_do_not_start_and_end_with_function_words(ngram: spacy.tokens.Span) -> bool:
    return any([ngram[0].orth_ in st.MY_ENGLISH_STOP_WORDS, ngram[-1].orth_ in st.MY_ENGLISH_STOP_WORDS, word_number_matcher.match(ngram[0].orth_.strip()) is None, word_number_matcher.match(ngram[-1].orth_.strip()) is None])

def exclude_ngrams_which_do_not_start_and_end_with_function_words(ngram: spacy.tokens.Span) -> bool:
    return any([ngram[0].lower_.strip() in st.MY_ENGLISH_STOP_WORDS, ngram[-1].lower_.strip() in st.MY_ENGLISH_STOP_WORDS, word_number_matcher.match(ngram[0].lower_.strip()) is None, word_number_matcher.match(ngram[-1].lower_.strip()) is None])

def unigrams_that_only_occur_in_one_bigram(bigrams):
    tok_bigram_counts = Counter()
    for bigram in bigrams:
        for tok in bigram.split():
            tok_bigram_counts[tok] += 1
    return {tok for tok, count in tok_bigram_counts.items() if count == 1}

def get_pmi(bigram):
    try:
        return np.log(bigram_prob[bigram] / np.product([unigram_prob[word] for word in bigram.split(' ')])) / np.log(2)
    except:
        return 0

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
def _speaker_name_factory():
    name_re = re.compile(".*(\\n|^)(?P<name>[A-Z0-9 \\.\\']+):\\w*.+", re.M)

    def speaker_name(text):
        for _, name in name_re.findall(text):
            if name not in ('ANNOUNCER', 'AUDIENCE MEMBER', 'AUDIENCE MEMBERS'):
                return name
    return speaker_name

def speaker_name(text):
    for _, name in name_re.findall(text):
        if name not in ('ANNOUNCER', 'AUDIENCE MEMBER', 'AUDIENCE MEMBERS'):
            return name

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

def clean_document(text):
    return only_speaker_text_re.sub('', text)

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

def better_title(x):
    if title_case_names:
        return ' '.join([t[0].upper() + t[1:].lower() for t in x.split()])
    else:
        return x

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

def _get_corpus_unigram_freq(self, corpus_freq_df: pd.DataFrame) -> pd.DataFrame:
    unigram_validator = re.compile('^[A-Za-z]+$')
    corpus_unigram_freq = corpus_freq_df.loc[[term for term in corpus_freq_df.index if unigram_validator.match(term) is not None]]
    return corpus_unigram_freq

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

def get_hex_color(color):
    return '#' + ''.join([part if len(part) == 2 else '0' + part for part in [hex(part)[2:] for part in color]])

def round_to_1(x):
    if x == 0:
        return 0
    return round(x, -int(np.floor(np.log10(abs(x)))))

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

def _ensure_category_col_is_in_df(self):
    if self._category_col not in self._df:
        self._category_col = 'Category'
        while self._category_col in self._df:
            self._category_col = 'Category_' + ''.join((np.random.choice(string.ascii_letters) for _ in range(5)))
        self._df[self._category_col] = ''

class Doc(object):

    def __init__(self, sents, raw):
        self.sents = sents
        self.string = raw
        self.text = raw

    def __str__(self):
        return '\n'.join((str(sent) for sent in self.sents))

    def __repr__(self):
        return self.__str__()

    def __iter__(self):
        for sent in self.sents:
            for tok in sent:
                yield tok

def __str__(self):
    return '\n'.join((str(sent) for sent in self.sents))

class Sentence(object):

    def __init__(self, toks, raw):
        self.toks = toks
        self.raw = raw

    def __iter__(self):
        for tok in self.toks:
            yield tok

    def __str__(self):
        return ' '.join([str(tok) for tok in self.toks])

    def __repr__(self):
        return self.raw

def __str__(self):
    return ' '.join([str(tok) for tok in self.toks])

def _asian_tokenization(doc, entity_type, tag_type, tokenizer):
    sents = []
    for paragraph in doc.split('\n'):
        sent_splits = iter(re.split('(？|。|」|！)+', paragraph, flags=re.MULTILINE))
        for partial_sent in sent_splits:
            sent = partial_sent + next(sent_splits, '')
            if sent.strip() == '':
                continue
            toks = []
            for tok in tokenizer(sent):
                pos = 'WORD'
                if tok.strip() == '':
                    pos = 'SPACE'
                elif punct_re.match(tok):
                    pos = 'PUNCT'
                toks.append(Tok(pos, tok[:2].lower(), tok.lower(), tok, ent_type='' if entity_type is None else entity_type.get(tok, ''), tag='' if tag_type is None else tag_type.get(tok, '')))
            sents.append(Sentence(toks, sent))
    return Doc(sents, doc)

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

def __init__(self, pos, lem, token, ent_type, tag, is_punct=False, idx=None):
    self.pos_ = pos
    self.lemma_ = lem
    self.lower_ = token.lower()
    self.orth_ = token
    self.ent_type_ = ent_type
    self.tag_ = tag
    self.is_punct = is_punct
    self.idx = idx

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

def whitespace_nlp(doc, entity_type=None, tag_type=None):
    toks = _regex_parse_sentence(doc, entity_type, tag_type)
    return Doc([toks])

def _toks_from_sentence(doc, entity_type, tag_type):
    toks = []
    for tok in WHITESPACE_SPLITTER.split(doc):
        if len(tok) > 0:
            toks.append(Tok(_get_pos_tag(tok), tok[:2].lower(), tok.lower(), ent_type='' if entity_type is None else entity_type.get(tok, ''), tag='' if tag_type is None else tag_type.get(tok, '')))
    return toks

def tokenize(text):
    toks = []
    for tok in nltk_tokenizer.tokenize(text):
        if len(tok) > 0:
            toks.append(Tok(_get_pos_tag(tok), tok.lower(), tok.lower(), ent_type='', tag=''))
    return Doc([toks], text)

def _get_pos_tag(tok):
    pos = 'WORD'
    if tok.strip() == '':
        pos = 'SPACE'
    elif ord(tok[0]) in VALID_EMOJIS:
        pos = 'EMJOI'
    elif PUNCT_MATCHER.match(tok):
        pos = 'PUNCT'
    return pos

def whitespace_nlp_with_sentences(doc, entity_type=None, tag_type=None, tok_splitter_re=DEFAULT_TOK_SPLITTER_RE):
    sentence_split_pat = re.compile('([^\\.!?]*?[\\.!?$])', re.M)
    sents = []
    raw_sents = sentence_split_pat.findall(doc)
    if len(raw_sents) == 0:
        raw_sents = [doc]
    sent_start_idx = 0
    for sentence in raw_sents:
        toks = []
        start_idx_in_sentence = 0
        for tok in tok_splitter_re.split(sentence):
            if len(tok.strip()) > 0:
                toks.append(Tok(_get_pos_tag(tok), tok[:2].lower(), tok.lower(), ent_type='' if entity_type is None else entity_type.get(tok, ''), tag='' if tag_type is None else tag_type.get(tok, ''), idx=sent_start_idx + start_idx_in_sentence))
            start_idx_in_sentence += len(tok)
        sents.append(toks)
        sent_start_idx += len(sentence)
    return Doc(sents, doc)

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

def get_labels(self):
    a = self._get_default_a_label()
    b = self._get_default_b_label()
    default_labels = {'a': a, 'not_a': '' if a == '' else 'Not ' + a, 'b': b, 'not_b': '' if b == '' else 'Not ' + b, 'a_and_b': self.top_category_name_, 'not_a_and_not_b': self.bottom_category_name_, 'a_and_not_b': self.left_category_name_, 'b_and_not_a': self.right_category_name_}
    labels = self._labels
    if labels is None:
        labels = {}
    return {name + '_label': labels.get(name, default_labels[name]) for name in default_labels}

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

def get_labels(self):
    a = self._get_default_a_label()
    b = self._get_default_b_label()
    default_labels = {'a': a, 'not_a': 'Not ' + a, 'b': b, 'not_b': 'Not ' + b, 'a_and_b': a + ' + ' + b, 'not_a_and_not_b': 'Not ' + a + ' + Not ' + b, 'a_and_not_b': a + ' + Not ' + b, 'b_and_not_a': 'Not ' + a + ' + ' + b}
    labels = self._labels
    if labels is None:
        labels = {}
    return {name + '_label': labels.get(name, default_labels[name]) for name in default_labels}

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

def get_labels(self):
    """

        :return: dict
        """
    default_labels = {'a': 'not-%s; %s' % (self.x_axis_name, self.y_axis_name), 'not_a': '%s; not-%s' % (self.x_axis_name, self.y_axis_name), 'b': '%s; %s' % (self.x_axis_name, self.y_axis_name), 'not_b': 'not-%s; not-%s' % (self.x_axis_name, self.y_axis_name), 'a_and_b': '%s' % self.y_axis_name, 'not_a_and_not_b': 'not-%s' % self.y_axis_name, 'a_and_not_b': 'not-%s' % self.x_axis_name, 'b_and_not_a': '%s' % self.x_axis_name}
    return {name + '_label': self._labels.get(name, default_labels[name]) for name in default_labels}

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

def _assert_stoplisted_minus_joe(self, tdm, uni_tdm):
    term_df = tdm.get_term_freq_df()
    uni_term_df = uni_tdm.get_term_freq_df()
    (self.assertEqual(set((term for term in term_df.index if ' ' not in term and 'joe' != term.lower() and ("'" not in term) and (term not in MY_ENGLISH_STOP_WORDS))), set(uni_term_df.index)),)

def get_hamlet_snippet_binary_category(text):
    return 'hamlet' if 'hamlet' in text.lower() else 'not hamlet'

def bad_whitespace_nlp(doc):
    toks = []
    for tok in doc.split():
        pos = 'WORD'
        if tok.strip() == '':
            pos = 'SPACE'
        elif re.match('^\\W+$', tok):
            pos = 'PUNCT'
        toks.append(Tok(pos, tok[:2].lower(), tok.lower(), ent_type='', tag=''))
    return Doc([toks])

class Span:

    def __init__(self, toks):
        self.text = ' '.join([t.lower_ for t in toks])

    def __str__(self):
        return self.text

def __init__(self, toks):
    self.text = ' '.join([t.lower_ for t in toks])

def whitespace_nlp_with_fake_chunks(doc, entity_type=None, tag_type=None):
    toks = _regex_parse_sentence(doc, entity_type, tag_type)
    words = [t for t in toks if t.pos_ == 'WORD']
    if len(words) < 5:
        return Doc([toks])
    else:
        return Doc([toks], noun_chunks=[Span(words[:2]), Span(words[1:3])])

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

def mock_empath_analyze(doc, **kwargs):
    doc.split()
    return {'disappointment': 0.0, 'violence': 0.0, 'ugliness': 0.0, 'legend': 0.0, 'farming': 0.0, 'hygiene': 0.0, 'help': 0.0, 'payment': 0.0, 'pride': 0.0, 'prison': 0.0, 'night': 2.0, 'warmth': 0.0, 'magic': 0.0, 'tourism': 0.0, 'play': 0.0, 'fight': 0.0, 'sympathy': 0.0, 'competing': 0.0, 'speaking': 2.0, 'politeness': 0.0, 'hipster': 0.0, 'blue_collar_job': 1.0, 'musical': 0.0, 'optimism': 0.0, 'power': 0.0, 'reading': 0.0, 'royalty': 0.0, 'noise': 0.0, 'rage': 0.0, 'work': 2.0, 'smell': 0.0, 'shame': 0.0, 'medieval': 0.0, 'terrorism': 1.0, 'health': 0.0, 'school': 0.0, 'poor': 1.0, 'money': 0.0, 'politics': 0.0, 'pain': 0.0, 'hearing': 0.0, 'rural': 0.0, 'economics': 1.0, 'eating': 0.0, 'leader': 0.0, 'hiking': 0.0, 'shape_and_size': 0.0, 'weakness': 0.0, 'friends': 0.0, 'strength': 1.0, 'ocean': 0.0, 'lust': 0.0, 'medical_emergency': 0.0, 'restaurant': 0.0, 'death': 0.0, 'morning': 1.0, 'cooking': 0.0, 'banking': 0.0, 'dominant_heirarchical': 0.0, 'party': 1.0, 'weapon': 0.0, 'nervousness': 0.0, 'anticipation': 0.0, 'hate': 0.0, 'vehicle': 4.0, 'art': 0.0, 'car': 4.0, 'leisure': 0.0, 'air_travel': 0.0, 'traveling': 0.0, 'animal': 0.0, 'dispute': 0.0, 'shopping': 1.0, 'monster': 0.0, 'pet': 0.0, 'science': 0.0, 'children': 0.0, 'ridicule': 1.0, 'affection': 0.0, 'superhero': 0.0, 'sexual': 0.0, 'celebration': 0.0, 'gain': 0.0, 'government': 1.0, 'beach': 0.0, 'law': 0.0, 'childish': 0.0, 'philosophy': 0.0, 'liquid': 0.0, 'fire': 0.0, 'war': 0.0, 'timidity': 0.0, 'love': 0.0, 'occupation': 1.0, 'achievement': 0.0, 'worship': 0.0, 'crime': 0.0, 'cheerfulness': 0.0, 'cold': 0.0, 'weather': 0.0, 'disgust': 0.0, 'phone': 0.0, 'journalism': 0.0, 'sadness': 0.0, 'contentment': 0.0, 'sound': 0.0, 'breaking': 0.0, 'neglect': 0.0, 'listen': 0.0, 'divine': 0.0, 'internet': 0.0, 'confusion': 0.0, 'religion': 0.0, 'exotic': 0.0, 'white_collar_job': 1.0, 'computer': 0.0, 'envy': 0.0, 'wealthy': 0.0, 'swimming': 0.0, 'ship': 0.0, 'suffering': 0.0, 'college': 0.0, 'sleep': 2.0, 'valuable': 0.0, 'real_estate': 0.0, 'sailing': 0.0, 'programming': 0.0, 'zest': 0.0, 'anger': 0.0, 'sports': 0.0, 'irritability': 0.0, 'exasperation': 0.0, 'independence': 0.0, 'torment': 0.0, 'dance': 0.0, 'order': 0.0, 'urban': 0.0, 'tool': 0.0, 'exercise': 0.0, 'negotiate': 0.0, 'wedding': 0.0, 'healing': 0.0, 'business': 1.0, 'social_media': 0.0, 'messaging': 1.0, 'swearing_terms': 0.0, 'stealing': 0.0, 'fabric': 0.0, 'driving': 4.0, 'fear': 0.0, 'fun': 1.0, 'office': 1.0, 'communication': 2.0, 'vacation': 0.0, 'emotional': 0.0, 'ancient': 0.0, 'music': 0.0, 'domestic_work': 1.0, 'giving': 1.0, 'deception': 0.0, 'beauty': 0.0, 'movement': 1.0, 'meeting': 0.0, 'alcohol': 0.0, 'heroic': 0.0, 'plant': 0.0, 'technology': 0.0, 'anonymity': 0.0, 'writing': 0.0, 'feminine': 0.0, 'surprise': 0.0, 'kill': 0.0, 'water': 0.0, 'joy': 0.0, 'dominant_personality': 0.0, 'toy': 0.0, 'positive_emotion': 1.0, 'appearance': 0.0, 'military': 0.0, 'aggression': 0.0, 'negative_emotion': 1.0, 'youth': 0.0, 'injury': 0.0, 'body': 0.0, 'clothing': 0.0, 'home': 0.0, 'family': 0.0, 'fashion': 0.0, 'furniture': 0.0, 'attractive': 0.0, 'trust': 0.0, 'cleaning': 0.0, 'masculine': 0.0, 'horror': 0.0}

def clean_function_factory():
    only_speaker_text_re = re.compile('((^|\\n)((ANNOUNCER|AUDIENCE MEMBERS?): .+)($|\\n)|(\\n|^)((([A-Z\\.()\\- ]+): ))|\\(.+\\) *)', re.M)
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

def clean_document(text):
    return only_speaker_text_re.sub('', text)

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

def get_params(self, param_dict={}):
    params = ['1000', '600', 'null', 'null', 'true', 'false', 'false', 'false', 'false', 'true', 'false', 'false', 'true', '0.1', 'false', 'undefined', 'undefined', 'getDataAndInfo()', 'true', 'false', 'null', 'null', 'null', 'null', 'true', 'false', 'true', 'false', 'null', 'null', '10', 'null', 'null', 'null', 'false', 'true', 'true', '"' + DEFAULT_DIV_ID + '"', 'null', 'false', 'false', '"' + DEFAULT_D3_AXIS_VALUE_FORMAT + '"', '"' + DEFAULT_D3_AXIS_VALUE_FORMAT + '"', 'false', '-1', 'true', 'false', 'true', 'false', 'false', 'false', 'true', 'null', 'null', 'null', 'false', 'null', 'undefined', 'undefined', 'undefined', 'undefined', 'undefined', 'undefined', 'undefined', '14', '0', 'null', '"Term"', 'true', 'false', 'false', 'undefined', 'null', '"document"', '"documents"', 'null', 'false', 'null', 'null', 'null', 'null', 'null', 'null', 'false']
    for i, val in param_dict.items():
        params[i] = val
    return 'buildViz(' + ',\n'.join(params) + ');\n'

class TestExtract_emoji(TestCase):

    def test_extract_emoji(self):
        text_ords = [128589, 127998, 97, 102, 100, 115, 128077, 128077, 127998, 127873, 128175]
        text = ''.join([chr(c) for c in text_ords])
        result = [[ord(c) for c in pic] for pic in extract_emoji(text)]
        self.assertEqual(result, [[128589, 127998], [128077], [128077, 127998], [127873], [128175]])

    def test_extract_emoji_ensure_no_numbers(self):
        text_ords = [50, 49, 51, 52, 50, 51, 128587, 127995, 128587, 127995, 97, 32, 97, 106, 97, 107, 115, 100, 108, 32, 102, 97, 115, 108, 107, 51, 32, 107, 32, 51, 32, 35, 32, 94, 32, 64, 32, 33, 32, 32, 35, 32, 42, 32, 60, 32, 62, 32, 63, 32, 32, 34, 32, 46, 32, 44, 32, 32, 41, 32, 40, 32, 36]
        text = ''.join([chr(c) for c in text_ords])
        result = [[ord(c) for c in pic] for pic in extract_emoji(text)]
        self.assertEqual(result, [[128587, 127995], [128587, 127995]])

def test_extract_emoji(self):
    text_ords = [128589, 127998, 97, 102, 100, 115, 128077, 128077, 127998, 127873, 128175]
    text = ''.join([chr(c) for c in text_ords])
    result = [[ord(c) for c in pic] for pic in extract_emoji(text)]
    self.assertEqual(result, [[128589, 127998], [128077], [128077, 127998], [127873], [128175]])

def test_extract_emoji_ensure_no_numbers(self):
    text_ords = [50, 49, 51, 52, 50, 51, 128587, 127995, 128587, 127995, 97, 32, 97, 106, 97, 107, 115, 100, 108, 32, 102, 97, 115, 108, 107, 51, 32, 107, 32, 51, 32, 35, 32, 94, 32, 64, 32, 33, 32, 32, 35, 32, 42, 32, 60, 32, 62, 32, 63, 32, 32, 34, 32, 46, 32, 44, 32, 32, 41, 32, 40, 32, 36]
    text = ''.join([chr(c) for c in text_ords])
    result = [[ord(c) for c in pic] for pic in extract_emoji(text)]
    self.assertEqual(result, [[128587, 127995], [128587, 127995]])

def _testing_nlp(doc):
    toks = []
    for tok in re.split('(\\W)', doc):
        pos = 'WORD'
        ent = ''
        tag = ''
        if tok.strip() == '':
            pos = 'SPACE'
        elif re.match('^\\W+$', tok):
            pos = 'PUNCT'
        if tok == 'Tone':
            ent = 'PERSON'
        if tok == 'Brooklyn':
            ent = 'GPE'
        toks.append(Tok(pos, tok[:2].lower(), tok.lower(), ent, tag))
    return Doc([toks])

def _translate_offsets_to_concatenated_doc(doc_id_to_offset, doc_offsets):
    new_offsets = []
    for orig_doc_idx, offsets in doc_offsets.items():
        doc_offset = doc_id_to_offset.get(orig_doc_idx, None)
        if doc_offset is not None:
            for offset in offsets:
                new_offsets.append((offset[0] + doc_offset, offset[1] + doc_offset))
    new_offsets.sort()
    return new_offsets

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

def __append_inter_arrival(self, cat: str, interarrival_cat: Dict, interarrivals, intervening_token_count: int) -> None:
    interarrivals.append(intervening_token_count)
    interarrival_cat[cat].append(intervening_token_count)

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

def __init__(self, corpus, term_acceptance_re=re.compile('[a-z]{3,}')):
    self.corpus_ = corpus
    self.category_embeddings_ = {}
    self.category_word2vec_model_ = {}
    self.term_acceptance_re = term_acceptance_re

class TransformerTokenizerWrapper(ABC):
    """
    Encapsulates the roberta tokenizer
    """

    def __init__(self, tokenizer, decoder=None, entity_type=None, tag_type=None, lower_case=False, name=None):
        self.tokenizer = tokenizer
        self.name = tokenizer.name_or_path if name is None else name
        if decoder is None:
            try:
                from text_unidecode import unidecode
            except:
                raise Exception("Please install the text_unicode package to preprocess documents. If you'd like to bypass this step, pass a text preprocessing (e.g., lambda x: x) function into the decode parameter of this class.")
            self.decoder = unidecode
        else:
            self.decoder = decoder
        self.entity_type = entity_type
        self.tag_type = tag_type
        self.lower_case = lower_case

    def tokenize(self, doc):
        """
        doc: str, text to be tokenized
        """
        sents = []
        if self.lower_case:
            doc = doc.lower()
        decoded_text = self.decoder(doc)
        tokens = self.tokenizer.convert_ids_to_tokens(self.tokenizer(decoded_text)['input_ids'], skip_special_tokens=True)
        last_idx = 0
        toks = []
        for raw_token in tokens:
            token_surface_string = self._get_surface_string(raw_token)
            if ord(raw_token[0]) == 266:
                last_idx += len(raw_token)
                continue
            try:
                token_idx = decoded_text.index(token_surface_string, last_idx)
            except Exception as e:
                print(decoded_text)
                print(token_surface_string)
                raise e
            toks.append(Tok(_get_pos_tag(token_surface_string), token_surface_string.lower(), raw_token.lower(), ent_type='' if self.entity_type is None else self.entity_type.get(token_surface_string, ''), tag='' if self.tag_type is None else self.tag_type.get(token_surface_string, ''), idx=token_idx))
            last_idx = token_idx + len(token_surface_string)
            if token_surface_string in ['.', '!', '?']:
                sents.append(toks)
                toks = []
        if len(toks) > 0:
            sents.append(toks)
        return Doc(sents, decoded_text)

    @abc.abstractmethod
    def _get_surface_string(self, raw_token: str) -> str:
        raise NotImplementedError()

    def get_subword_encoding_name(self) -> str:
        raise self.name

def tokenize(self, doc):
    """
        doc: str, text to be tokenized
        """
    sents = []
    if self.lower_case:
        doc = doc.lower()
    decoded_text = self.decoder(doc)
    tokens = self.tokenizer.convert_ids_to_tokens(self.tokenizer(decoded_text)['input_ids'], skip_special_tokens=True)
    last_idx = 0
    toks = []
    for raw_token in tokens:
        token_surface_string = self._get_surface_string(raw_token)
        if ord(raw_token[0]) == 266:
            last_idx += len(raw_token)
            continue
        try:
            token_idx = decoded_text.index(token_surface_string, last_idx)
        except Exception as e:
            print(decoded_text)
            print(token_surface_string)
            raise e
        toks.append(Tok(_get_pos_tag(token_surface_string), token_surface_string.lower(), raw_token.lower(), ent_type='' if self.entity_type is None else self.entity_type.get(token_surface_string, ''), tag='' if self.tag_type is None else self.tag_type.get(token_surface_string, ''), idx=token_idx))
        last_idx = token_idx + len(token_surface_string)
        if token_surface_string in ['.', '!', '?']:
            sents.append(toks)
            toks = []
    if len(toks) > 0:
        sents.append(toks)
    return Doc(sents, decoded_text)

class RobertaTokenizerWrapper(TransformerTokenizerWrapper):

    def _get_surface_string(self, raw_token: str) -> str:
        token_surface_string = raw_token
        if ord(raw_token[0]) == 288:
            token_surface_string = raw_token[1:]
        return token_surface_string

def _get_surface_string(self, raw_token: str) -> str:
    token_surface_string = raw_token
    if ord(raw_token[0]) == 288:
        token_surface_string = raw_token[1:]
    return token_surface_string

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

def _free_init(self, **kwargs):
    self.term_scorer_factory_: type = kwargs.get('term_scorer', RankDifferenceScorer)
    self.term_scorer_kwargs_: Dict = kwargs.get('term_scorer_kwargs', {})

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

def getidx(self, val: Any) -> int:
    try:
        return self._val2i[val]
    except KeyError:
        self._val2i[val] = self._next_i
        self._i2val.append(val)
        self._next_i += 1
        return self._next_i - 1

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

def get_dot(self, component):
    graph = 'digraph  \n{\n graph [%s]\n node [%s] ;\n' % (self._format_graphviz_paramters(self.graph_params), self._format_graphviz_paramters(self.node_params))
    mynode_df = self.id_node_df[self.id_node_df['Component'] == component]
    nodes = '\n'.join(mynode_df.reset_index().apply(lambda x: '"%s" [label="%s"] ;' % (x['index'], x['name']), axis=1).values)
    edges = '\n'.join(self.edge_df[self.edge_df.Component == component].apply(lambda x: '"%s" -> "%s" ;' % (x.source_id, x.target_id), axis=1).values)
    return graph + nodes + '\n\n' + edges + '\n}'

def _format_graphviz_paramters(self, params):
    return ', '.join([k + '=' + ('"' if type(v) == str else '') + str(v) + ('"' if type(v) == str else '') for k, v in params.items()])

def _append_if_valid(found_emojis, candidate):
    for c in candidate:
        if ord(c) > 1000:
            found_emojis.append(candidate)
            return

def extract_emoji(text):
    """
	Parameters
	----------
	text, str

	Returns
	-------
	List of 5.0-compliant emojis that occur in text.
	"""
    found_emojis = []
    len_text = len(text)
    i = 0
    while i < len_text:
        cur_char = ord(text[i])
        try:
            VALID_EMOJIS[cur_char]
        except:
            i += 1
            continue
        found = False
        for dict_len, candidates in VALID_EMOJIS[cur_char]:
            if i + dict_len <= len_text:
                if dict_len == 0:
                    _append_if_valid(found_emojis, text[i])
                    i += 1
                    found = True
                    break
                candidate = tuple((ord(c) for c in text[i + 1:i + 1 + dict_len]))
                if candidate in candidates:
                    _append_if_valid(found_emojis, text[i:i + 1 + dict_len])
                    i += 1 + dict_len
                    found = True
                    break
            if found:
                break
        if not found:
            _append_if_valid(found_emojis, text[i])
            i += 1
    return found_emojis

class DispersionPlotSettings(TrendPlotSettings):

    def __init__(self, category_order: List=None, metric: str='DA', use_residual: bool=True, term_ranker: Optional[TermRanker]=None, frequency_scaler: Optional[Callable[[np.array], np.array]]=None, dispersion_scaler: Optional[Callable[[np.array], np.array]]=None, regressor: Optional=None):
        TrendPlotSettings.__init__(self, category_order=category_order)
        self.metric = metric
        self.use_residual = use_residual
        self.frequency_scaler = dense_rank if frequency_scaler is None else frequency_scaler
        self.dispersion_scaler = (scale_center_zero_abs if use_residual else scale) if dispersion_scaler is None else dispersion_scaler
        self.term_ranker = AbsoluteFrequencyRanker if term_ranker is None else term_ranker
        self.regressor = MeanIsotonic() if regressor is None else regressor

    def get_plot_params(self) -> TrendPlotPresets:
        return TrendPlotPresets(x_label=' '.join(['Frequency', get_scaler_name(self.frequency_scaler).strip()]), y_label=('Frequency-adjusted ' if self.use_residual else '') + self.metric, x_axis_labels=['Low', 'Medium', 'High'], y_axis_labels=['More Concentrated', 'Medium', 'More Dispersion'], tooltip_column_names={'Frequency': 'Frequency', 'Y': 'Residual ' + self.metric}, tooltip_columns=['Frequency', 'Y'], header_names={'upper': 'Dispersed', 'lower': 'Concentrated'}, left_list_column='Y')

    def get_x_axis(self, corpus: TermDocMatrix, non_text: bool=False) -> ScaledAxis:
        rank_df = self.term_ranker(corpus).set_non_text(non_text=non_text).get_ranks('')
        frequencies = rank_df.sum(axis=1)
        return ScaledAxis(orig=frequencies, scaled=self.frequency_scaler(frequencies))

def get_plot_params(self) -> TrendPlotPresets:
    return TrendPlotPresets(x_label=' '.join(['Frequency', get_scaler_name(self.frequency_scaler).strip()]), y_label=('Frequency-adjusted ' if self.use_residual else '') + self.metric, x_axis_labels=['Low', 'Medium', 'High'], y_axis_labels=['More Concentrated', 'Medium', 'More Dispersion'], tooltip_column_names={'Frequency': 'Frequency', 'Y': 'Residual ' + self.metric}, tooltip_columns=['Frequency', 'Y'], header_names={'upper': 'Dispersed', 'lower': 'Concentrated'}, left_list_column='Y')

class CorrelationPlotSettings(TrendPlotSettings):

    def __init__(self, category_order: List=None, correlation_type: str='spearmanr', term_ranker: Optional[TermRanker]=None, frequency_scaler: Optional[Callable[[np.array], np.array]]=None):
        TrendPlotSettings.__init__(self, category_order=category_order)
        self.correlation_type = correlation_type
        self.term_ranker = AbsoluteFrequencyRanker if term_ranker is None else term_ranker
        self.frequency_scaler = dense_rank if frequency_scaler is None else frequency_scaler

    def get_plot_params(self) -> TrendPlotPresets:
        return TrendPlotPresets(x_label=' '.join(['Frequency', get_scaler_name(self.frequency_scaler).strip()]), y_label=self.correlation_type.title(), x_axis_labels=['Low', 'Medium', 'High'], y_axis_labels=['Anti-correlated', 'No-correlation', 'Correlated'], tooltip_column_names={'Frequency': 'Frequency', 'Y': Correlations.get_notation_name(self.correlation_type)}, tooltip_columns=['Frequency', 'Y'], header_names={'upper': 'Most correlated', 'lower': 'Most anti-correlated'}, left_list_column='Y')

    def get_x_axis(self, corpus: TermDocMatrix, non_text: bool=False) -> ScaledAxis:
        rank_df = self.term_ranker(corpus).set_non_text(non_text=non_text).get_ranks('')
        frequencies = rank_df.sum(axis=1)
        return ScaledAxis(orig=frequencies, scaled=self.frequency_scaler(frequencies))

def get_plot_params(self) -> TrendPlotPresets:
    return TrendPlotPresets(x_label=' '.join(['Frequency', get_scaler_name(self.frequency_scaler).strip()]), y_label=self.correlation_type.title(), x_axis_labels=['Low', 'Medium', 'High'], y_axis_labels=['Anti-correlated', 'No-correlation', 'Correlated'], tooltip_column_names={'Frequency': 'Frequency', 'Y': Correlations.get_notation_name(self.correlation_type)}, tooltip_columns=['Frequency', 'Y'], header_names={'upper': 'Most correlated', 'lower': 'Most anti-correlated'}, left_list_column='Y')

class TimePlotSettings(TrendPlotSettings):

    def __init__(self, category_order: List=None, dispersion_metric: str='DA', use_residual: bool=False, dispersion_scaler: Optional[Callable[[np.array], np.array]]=None, term_ranker: Optional[TermRanker]=None, regressor: Optional=None):
        TrendPlotSettings.__init__(self, category_order=category_order)
        self.y_axis_metric = dispersion_metric
        self.dispersion_scaler = dispersion_scaler
        self.use_residual = use_residual
        self.term_ranker = AbsoluteFrequencyRanker if term_ranker is None else term_ranker
        self.regressor = KNeighborsRegressor(weights='distance') if regressor is None else regressor

    def get_plot_params(self) -> TrendPlotPresets:
        return TrendPlotPresets(x_label='Mean Category Position', y_label=' '.join([get_scaler_name(self.dispersion_scaler), ('Residual ' if self.use_residual else '') + self.y_axis_metric]).strip(), y_axis_labels=['High ' + self.y_axis_metric, '', 'Low ' + self.y_axis_metric], x_axis_labels=[self.category_order[0], self.category_order[round(len(self.category_order) / 2)], self.category_order[-1]], tooltip_column_names={'Frequency': 'Frequency', 'MeanCategory': 'Mean'}, tooltip_columns=['Frequency', 'MeanCategory'], header_names={'upper': 'Most Dispersed', 'lower': 'Most Concentrated'}, left_list_column='Y')

def get_plot_params(self) -> TrendPlotPresets:
    return TrendPlotPresets(x_label='Mean Category Position', y_label=' '.join([get_scaler_name(self.dispersion_scaler), ('Residual ' if self.use_residual else '') + self.y_axis_metric]).strip(), y_axis_labels=['High ' + self.y_axis_metric, '', 'Low ' + self.y_axis_metric], x_axis_labels=[self.category_order[0], self.category_order[round(len(self.category_order) / 2)], self.category_order[-1]], tooltip_column_names={'Frequency': 'Frequency', 'MeanCategory': 'Mean'}, tooltip_columns=['Frequency', 'MeanCategory'], header_names={'upper': 'Most Dispersed', 'lower': 'Most Concentrated'}, left_list_column='Y')

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

def coarse_tag_str(pos_seq):
    """Convert POS sequence to our coarse system, formatted as a string."""
    global tag2coarse
    tags = [tag2coarse.get(tag, 'O') for tag in pos_seq]
    return ''.join(tags)

def stringify(s):
    return ''.join((a[1] for a in s))

def positionify(s):
    return tuple((a[0] for a in s))

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

def _set_scorer_args(self, **kwargs):
    """
        method : {'average', 'min', 'max', 'dense', 'ordinal'}, optional
        """
    self.method = kwargs.get('method', 'dense')

class FrequencyScorer(CorpusBasedTermScorer):

    def _set_scorer_args(self, **kwargs):
        self.constant = kwargs.get('constant', 0.01)

    def get_scores(self, *args):
        """
        Returns category frequencies

        Returns
        -------
        np.array, scores
        """
        if self.tdf_ is None:
            raise Exception("Use set_categories('category name', ['not category name', ...]) " + 'to set the category of interest')
        y_i = self.tdf_['cat']
        return y_i

    def get_name(self):
        return 'Frequency'

def _set_scorer_args(self, **kwargs):
    self.constant = kwargs.get('constant', 0.01)

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

def _set_scorer_args(self, *args, **kwargs):
    self.verbose = kwargs.get('verbose', False)

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

def _set_scorer_args(self, **kwargs):
    self.lambda_ = kwargs.get('lambda_', 0.01)

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

def _set_scorer_args(self, **kwargs):
    self.constant = kwargs.get('constant', 0.01)

class LogOddsRatioUninformativePriorScorer(CorpusBasedTermScorer):

    def get_name(self) -> str:
        return 'Log Odds Ratio w/ Uninformative Prior'

    def _set_scorer_args(self, **kwargs):
        self.alpha = kwargs.get('alpha', 0.01)

    def get_scores(self, *args) -> pd.Series:
        rank_df = self.term_ranker_.get_ranks('')
        a = rank_df[self.category_name] + self.alpha
        b = rank_df[self.not_category_names].sum(axis=1) + self.alpha
        return log_odds_ratio_with_prior_from_counts(a, b)

def _set_scorer_args(self, **kwargs):
    self.alpha = kwargs.get('alpha', 0.01)

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

def __init__(self, corpus: 'ParsedCorpus', *args, **kwargs):
    self.corpus_ = corpus
    self.category_ids_ = corpus._y
    self.tdf_ = None
    self.use_metadata_ = kwargs.get('non_text', False) or kwargs.get('use_metadata', False) or kwargs.get('use_non_text_features', False)
    self.category_name_is_set_ = False
    self._doc_sizes = None
    self._set_scorer_args(**kwargs)
    self.term_ranker_ = self._get_default_ranker(corpus)

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

def _set_scorer_args(self, **args):
    self.verbose = args.get('verbose', False)

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

def _set_scorer_args(self, **kwargs):
    self.constant = kwargs.get('constant', 0.01)

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

def _set_scorer_args(self, **kwargs):
    self.alpha_ = kwargs.get('alpha', None)
    self.correct_ = kwargs.get('correct', True)

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

def _set_scorer_args(self, **kwargs):
    self.min_p_ = kwargs.get('minimum_p_value', 0.05)
    self.smoothing_lambda_ = kwargs.get('smoothing_lambda', 0.05)

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

def _set_scorer_args(self, **kwargs):
    self.conf_level_ = kwargs.get('conf_level', 0.95)
    self.correct_ = kwargs.get('correct', True)
    self.alternative_ = kwargs.get('alternative', 'two sided')

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

def _set_scorer_args(self, **kwargs):
    self.k1 = kwargs.get('k1', 1.2)
    self.b = kwargs.get('b', 0.95)

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

def _set_scorer_args(self, alpha: float=0.05, *args, **kwargs):
    self.alpha = alpha
    self.verbose = kwargs.get('verbose', False)

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

def _set_scorer_args(self, **kwargs):
    self.eta = kwargs.get('eta', 1.0)
    self.use_sublinear = kwargs.get('use_sublinear', True)
    self.use_cred = kwargs.get('use_cred', True)
    self.use_l2_norm = kwargs.get('use_l2_norm', True)

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

def _set_scorer_args(self, **kwargs):
    self.pi1 = kwargs.get('pi1', 0.5)
    self.pi2 = kwargs.get('pi2', 0.5)
    assert self.pi1 + self.pi2 == 1

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

def _set_scorer_args(self, **kwargs):
    self.lambda_ = kwargs.get('lambda_', 1)
    self.log_ = kwargs.get('log', False)
    self.coef_ = kwargs.get('coef', 1000000.0)

def doc_sentence_splitter(doc: spacy.tokens.doc.Doc) -> Iterable[spacy.tokens.span.Span]:
    for sent in doc.sents:
        non_blank = [t.i for t in sent if t.orth_.strip() != '']
        if len(non_blank):
            yield doc[non_blank[0]:non_blank[-1] + 1]

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

def get_term_category_stats(self, term: str, cat: str) -> Optional[RunningStatsArray]:
    return self.term_cat_stats.get(term, {}).get(cat, None)

def get_category_stats(self, cat: str) -> Optional[RunningStatsArray]:
    return self.cat_stats.get(cat, None)

def get_term_stats(self, cat: str) -> Optional[RunningStatsArray]:
    return self.term_stats.get(cat, None)

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

def __build_offset_df(self):
    offset_data = []
    for term, values in self.corpus.get_offsets().items():
        term_idx = self.corpus.get_metadata_index(term)
        for doc_idx, offsets in values.items():
            for start, end in offsets:
                offset_data.append([doc_idx, term_idx, start, end])
    offset_df = pd.DataFrame(offset_data, columns=['DocIdx', 'TermIdx', 'Start', 'End']).sort_values(by=['DocIdx', 'Start', 'End']).set_index('DocIdx')
    return offset_df

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

class FeatsFromSpacyDocOnlyEmoji(FeatsFromSpacyDoc):
    """
	Strips away everything but emoji tokens from spaCy
	"""

    def get_feats(self, doc):
        """
		Parameters
		----------
		doc, Spacy Docs

		Returns
		-------
		Counter emoji -> count
		"""
        return Counter(extract_emoji(str(doc)))

def get_feats(self, doc):
    """
		Parameters
		----------
		doc, Spacy Docs

		Returns
		-------
		Counter emoji -> count
		"""
    return Counter(extract_emoji(str(doc)))

class SpacyEntities(FeatsFromSpacyDoc):

    def __init__(self, use_lemmas=False, entity_types_to_censor=set(), entity_types_to_use=None, tag_types_to_censor=set(), strip_final_period=False):
        self._entity_types_to_use = entity_types_to_use
        FeatsFromSpacyDoc.__init__(self, use_lemmas, entity_types_to_censor, tag_types_to_censor, strip_final_period)

    def get_feats(self, doc):
        return Counter([' '.join(str(ent).split()).lower() for ent in doc.ents if (self._entity_types_to_use is None or ent.label_ in self._entity_types_to_use) and ent.label_ not in self._entity_types_to_censor])

def get_feats(self, doc):
    return Counter([' '.join(str(ent).split()).lower() for ent in doc.ents if (self._entity_types_to_use is None or ent.label_ in self._entity_types_to_use) and ent.label_ not in self._entity_types_to_censor])

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

def __init__(self, lexicons: Dict[str, List[List[str]]], definitions: Optional[Dict[str, str]]=None, case_sensitive: bool=False):
    """
        :param lexicons: Dict[str, List[List[str]]], maps a topic name to its list of word sequences
        :param definitions, Optional[Dict[str, str]], maps topic name to an explanation.
        :param case_sensitive: bool, are word sequences case-sensitive?
        """
    self.definitions = definitions
    self.keyword_processor = flashtext.KeywordProcessor(case_sensitive)
    self.keyword_processor.add_keywords_from_dict({topic: [' '.join(term_sequence) for term_sequence in term_sequences] for topic, term_sequences in lexicons.items()})

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

class FeatsFromSpacyDocOnlyNounChunks(FeatsFromSpacyDoc):
    """
	Just returns noun chunks from spaCy
	"""

    def get_feats(self, doc):
        """
		Parameters
		----------
		doc, Spacy Docs

		Returns
		-------
		Counter noun chunk -> count
		"""
        return Counter([str(c).lower() for c in doc.noun_chunks])

def get_feats(self, doc):
    """
		Parameters
		----------
		doc, Spacy Docs

		Returns
		-------
		Counter noun chunk -> count
		"""
    return Counter([str(c).lower() for c in doc.noun_chunks])

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

def sequence_window(seq, n=2):
    it = iter(seq)
    win = deque((next(it, None) for _ in range(n)), maxlen=n)
    yield list(win)
    for e in it:
        win.append(e)
        yield list(win)

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

def __init__(self, exclude_ngram_filter: Optional[Callable[[str], bool]]=None, ngram_sizes: Optional[List[int]]=None, text_from_token: Optional[Callable[[str], str]]=None, validate_token: Optional[Callable[[spacy.tokens.Token], bool]]=None, whitespace_substitute: Optional[Callable[[str], str]]=None, exclude_sentence_filter: Optional[Callable[[str], bool]]=None):
    self.exclude_ngram_filter = (lambda x: False) if exclude_ngram_filter is None else exclude_ngram_filter
    self.ngram_sizes = [1, 2, 3] if ngram_sizes is None else ngram_sizes
    self.text_from_token = (lambda tok: tok.lower_) if text_from_token is None else text_from_token
    self.validate_token = (lambda tok: tok.tag_ != '_SP' and tok.orth_.strip() != '') if validate_token is None else validate_token
    self.whitespace_substitute = ' ' if whitespace_substitute is None else whitespace_substitute
    self.exclude_sentence_filter = (lambda s: False) if exclude_sentence_filter is None else exclude_sentence_filter

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

def _add_ngram_to_token_stats(self, ngram, offset_tokens):
    toktext = ' '.join((self.text_from_token(tok) for tok in ngram))
    offset_tokens.setdefault(toktext, 0)
    offset_tokens[toktext] += 1

class ClickableTerms:

    @staticmethod
    def get_clickable_lexicon(lexicon, plot_interface='plotInterface'):
        out = []
        for term in lexicon:
            clickable_term = ClickableTerms.get_clickable_term(term, plot_interface)
            out.append(clickable_term)
        return ',\n'.join(out)

    @staticmethod
    def get_clickable_term(term, plot_interface='plotInterface', other_plot_interface=None, style=None):
        onclick_js = ClickableTerms._get_onclick_js(term.replace("'", "\\'"), plot_interface, other_plot_interface)
        onmouseover_js = "{plot_interface}.showToolTipForTerm({plot_interface}.data, {plot_interface}.svg, '%s'," % term.replace("'", "\\'") + "{plot_interface}.termDict['%s'])" % term.replace("'", "\\'")
        onmouseout_js = "{plot_interface}.tooltip.transition().style('opacity', 0)"
        template = '<span onclick="' + onclick_js + '" onmouseover="' + onmouseover_js + '" onmouseout="' + onmouseout_js + '" ' + ('' if style is None else 'style="' + style + '"') + '>{term}</span>'
        clickable_term = template.format(term=term, plot_interface=plot_interface)
        return clickable_term

    @staticmethod
    def _get_onclick_js(term, plot_interface, other_plot_interface=None):
        if other_plot_interface:
            return "{other_plot_interface}.drawCategoryAssociation({plot_interface}.termDict['{term}'].ci); return false;".format(other_plot_interface=other_plot_interface, plot_interface=plot_interface, term=term.replace("'", "\\'"))
        return "{plot_interface}.displayTermContexts({plot_interface}.data, {plot_interface}.gatherTermContexts({plot_interface}.termDict['%s']));" % term.replace("'", "'")

@staticmethod
def get_clickable_lexicon(lexicon, plot_interface='plotInterface'):
    out = []
    for term in lexicon:
        clickable_term = ClickableTerms.get_clickable_term(term, plot_interface)
        out.append(clickable_term)
    return ',\n'.join(out)

class PairPlotFromScatterplotStructure(object):

    def __init__(self, category_scatterplot_structure, term_scatterplot_structure, category_projection, category_width, category_height, include_category_labels=True, show_halo=True, num_terms=5, d3_url_struct=None, x_dim=0, y_dim=1, protocol='http', term_plot_interface='termPlotInterface', category_plot_interface='categoryPlotInterface'):
        """,
        Parameters
        ----------
        category_scatterplot_structure: ScatterplotStructure
        term_scatterplot_structure: ScatterplotStructure,
        category_projection: CategoryProjection
        category_height: int
        category_width: int
        show_halo: bool
        num_terms: int, default 5
        include_category_labels: bool, default True
        d3_url_struct: D3URLs
        x_dim: int, 0
        y_dim: int, 1
        protocol: str
            http or https
        term_plot_interface : str
        category_plot_interface : str
        """
        self.category_scatterplot_structure = category_scatterplot_structure
        self.term_scatterplot_structure = term_scatterplot_structure
        self.category_projection = category_projection
        self.d3_url_struct = d3_url_struct if d3_url_struct else D3URLs()
        ExternalJSUtilts.ensure_valid_protocol(protocol)
        self.protocol = protocol
        self.category_width = category_width
        self.category_height = category_height
        self.num_terms = num_terms
        self.show_halo = show_halo
        self.x_dim = x_dim
        self.y_dim = y_dim
        self.include_category_labels = include_category_labels
        self.term_plot_interface = term_plot_interface
        self.category_plot_interface = category_plot_interface

    def to_html(self):
        """
        Returns
        -------
        str, the html file representation

        """
        javascript_to_insert = '\n'.join([PackedDataUtils.full_content_of_javascript_files(), self.category_scatterplot_structure._visualization_data.to_javascript('getCategoryDataAndInfo'), self.category_scatterplot_structure.get_js_to_call_build_scatterplot_with_a_function(self.category_plot_interface), self.term_scatterplot_structure._visualization_data.to_javascript('getTermDataAndInfo'), self.term_scatterplot_structure.get_js_to_call_build_scatterplot_with_a_function(self.term_plot_interface), self.term_scatterplot_structure.get_js_reset_function(values_to_set=[self.category_plot_interface, self.term_plot_interface], functions_to_reset=['build' + self.category_plot_interface, 'build' + self.term_plot_interface]), PackedDataUtils.javascript_post_build_viz('categorySearch', self.category_plot_interface), PackedDataUtils.javascript_post_build_viz('termSearch', self.term_plot_interface)])
        autocomplete_css = PackedDataUtils.full_content_of_default_autocomplete_css()
        html_template = self._get_html_template()
        html_content = HELLO + html_template.replace('/***AUTOCOMPLETE CSS***/', autocomplete_css, 1).replace('<!-- INSERT SCRIPT -->', javascript_to_insert, 1).replace('<!--D3URL-->', self.d3_url_struct.get_d3_url(), 1).replace('<!--D3SCALECHROMATIC-->', self.d3_url_struct.get_d3_scale_chromatic_url())
        html_content = html_content.replace('http://', self.protocol + '://')
        if self.show_halo:
            axes_labels = self.category_projection.get_nearest_terms(num_terms=self.num_terms)
            for position, terms in axes_labels.items():
                html_content = html_content.replace('{%s}' % position, self._get_lexicon_html(terms))
        cellheight, cellheightshort = cell_height_and_cell_height_short_from_height(self.category_height)
        return html_content.replace('{width}', str(self.category_width)).replace('{height}', str(self.category_height)).replace('{cellheight}', str(cellheight)).replace('{cellheightshort}', str(cellheightshort))

    def _get_html_template(self):
        if self.show_halo:
            return PackedDataUtils.get_packaged_html_template_content(PAIR_PLOT_HTML_VIZ_FILE_NAME)
        return PackedDataUtils.get_packaged_html_template_content(PAIR_PLOT_WITHOUT_HALO_HTML_VIZ_FILE_NAME)

    def _get_lexicon_html(self, terms):
        lexicon_html = ''
        for i, term in enumerate(terms):
            lexicon_html += '<b>' + ClickableTerms.get_clickable_term(term, self.term_plot_interface) + '</b>'
            if self.include_category_labels:
                category = self.category_projection.category_counts.loc[term].idxmax()
                lexicon_html += ' (<i>%s</i>)' % ClickableTerms.get_clickable_term(category, self.category_plot_interface, self.term_plot_interface)
            if i != len(terms) - 1:
                lexicon_html += ',\n'
        return lexicon_html

def _get_lexicon_html(self, terms):
    lexicon_html = ''
    for i, term in enumerate(terms):
        lexicon_html += '<b>' + ClickableTerms.get_clickable_term(term, self.term_plot_interface) + '</b>'
        if self.include_category_labels:
            category = self.category_projection.category_counts.loc[term].idxmax()
            lexicon_html += ' (<i>%s</i>)' % ClickableTerms.get_clickable_term(category, self.category_plot_interface, self.term_plot_interface)
        if i != len(terms) - 1:
            lexicon_html += ',\n'
    return lexicon_html

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
def _load_script_file_names(script_names):
    return '; \n \n '.join([PackedDataUtils.get_packaged_script_content(script_name) for script_name in script_names])

