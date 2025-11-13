# Cluster 4

def main():
    convention_df = SampleCorpora.ConventionData2012.get_data()
    feat_builder = FeatsFromGeneralInquirer()
    corpus = CorpusFromPandas(convention_df, category_col='party', text_col='text', nlp=whitespace_nlp_with_sentences, feats_from_spacy_doc=feat_builder).build()
    html = produce_scattertext_explorer(corpus, category='democrat', category_name='Democratic', not_category_name='Republican', width_in_pixels=1000, metadata=convention_df['speaker'], use_non_text_features=True, use_full_doc=True, topic_model_term_lists=feat_builder.get_top_model_term_lists(), metadata_descriptions=feat_builder.get_definitions())
    open('./demo_general_inquirer.html', 'wb').write(html.encode('utf-8'))
    print('Open ./demo_general_inquirer.html in Chrome or Firefox.')

def main():
    nlp = spacy.load('en_core_web_sm')
    convention_df = SampleCorpora.ConventionData2012.get_data()
    convention_df['parsed'] = convention_df.text.apply(nlp)
    corpus = CorpusFromParsedDocuments(convention_df, category_col='party', parsed_col='parsed').build().get_unigram_corpus()
    model = word2vec.Word2Vec(vector_size=100, alpha=0.025, window=5, min_count=5, max_vocab_size=None, sample=0, seed=1, workers=1, min_alpha=0.0001, sg=1, hs=1, negative=0, cbow_mean=0, null_word=0, trim_rule=None, sorted_vocab=1)
    html = word_similarity_explorer_gensim(corpus, category='democrat', target_term='jobs', category_name='Democratic', not_category_name='Republican', minimum_term_frequency=5, width_in_pixels=1000, metadata=convention_df['speaker'], word2vec=Word2VecFromParsedCorpus(corpus, model).train(), term_significance=ScaledFScoreSignificance(), max_p_val=0.05, save_svg_button=True, d3_url='scattertext/data/viz/scripts/d3.min.js', d3_scale_chromatic_url='scattertext/data/viz/scripts/d3-scale-chromatic.v1.min.js')
    open('./demo_gensim_similarity.html', 'wb').write(html.encode('utf-8'))
    print('Open ./demo_gensim_similarity.html in Chrome or Firefox.')

def train_sentence_piece_tokenizer(documents, vocab_size):
    """
    :param documents: list-like, a list of str documents
    :vocab_size int: the size of the vocabulary to output

    :return sentencepiece.SentencePieceProcessor
    """
    sp = None
    with tempfile.NamedTemporaryFile(delete=True) as tempf:
        with tempfile.NamedTemporaryFile(delete=True) as tempm:
            tempf.write('\n'.join(documents).encode())
            mod = spm.SentencePieceTrainer.Train('--input=%s --model_prefix=%s --vocab_size=%s' % (tempf.name, tempm.name, vocab_size))
            sp = spm.SentencePieceProcessor()
            sp.load(tempm.name + '.model')
    return sp

def main():
    df = pd.read_csv('https://cdn.rawgit.com/JasonKessler/scattertext/e508bf32/scattertext/data/chinese.csv')
    df['text'] = df['text'].apply(chinese_nlp)
    corpus = CorpusFromParsedDocuments(df, category_col='novel', parsed_col='text').build()
    html = produce_scattertext_explorer(corpus, category='Tale of Two Cities', category_name='Tale of Two Cities', not_category_name='Ulysses', width_in_pixels=1000, metadata=df['novel'], asian_mode=True)
    open('./demo_chinese.html', 'w').write(html)
    print('Open ./demo_chinese.html in Chrome or Firefox.')

def main():
    convention_df = SampleCorpora.ConventionData2012.get_data()
    feat_builder = FeatsFromOnlyEmpath()
    corpus = CorpusFromParsedDocuments(convention_df, category_col='party', parsed_col='text', feats_from_spacy_doc=feat_builder).build()
    html = produce_scattertext_explorer(corpus, category='democrat', category_name='Democratic', not_category_name='Republican', width_in_pixels=1000, metadata=convention_df['speaker'], use_non_text_features=True, use_full_doc=True, topic_model_term_lists=feat_builder.get_top_model_term_lists())
    open('./Convention-Visualization-Empath.html', 'wb').write(html.encode('utf-8'))
    print('Open ./Convention-Visualization-Empath.html in Chrome or Firefox.')

def main():
    shisei = _parse_geutenberg('http://www.gutenberg.org/files/31617/31617-0.txt')
    horadanshaku = _parse_geutenberg('http://www.gutenberg.org/files/34084/34084-0.txt')
    df = pd.DataFrame({'text': [shisei, horadanshaku], 'title': ['Shisei', 'Horadanshaku tabimiyage'], 'author': ['Akutagawa Ryunosuke', 'Kuni Sasaki']})
    df['text'] = df['text'].apply(st.japanese_nlp)
    corpus = st.CorpusFromParsedDocuments(df, category_col='title', parsed_col='text').build()
    html = st.produce_scattertext_explorer(corpus, category='Shisei', category_name='Shisei', not_category_name='Horadanshaku tabimiyage', minimum_term_frequency=5, width_in_pixels=1000, metadata=df['title'] + ' by ' + df['author'], asian_mode=True)
    open('./demo_japanese.html', 'w').write(html)
    print('Open ./demo_japanese.html in Chrome or Firefox.')

def main():
    nlp = spacy.load('en_core_web_sm')
    convention_df = SampleCorpora.ConventionData2012.get_data()
    corpus = CorpusFromPandas(convention_df, category_col='party', text_col='text', nlp=nlp).build()
    html = word_similarity_explorer(corpus, category='democrat', category_name='Democratic', not_category_name='Republican', target_term='jobs', minimum_term_frequency=5, width_in_pixels=1000, metadata=convention_df['speaker'], alpha=0.01, max_p_val=0.1, save_svg_button=True)
    open('./demo_similarity.html', 'wb').write(html.encode('utf-8'))
    print('Open ./demo_similarlity.html in Chrome or Firefox.')

def main():
    parser = argparse.ArgumentParser(description='A primitive, incomplete commandline interface to Scattertext.')
    parser.add_argument('--datafile', action='store', dest='datafile', required=True, help="Path (or URL) of a CSV file with at least two columns.Text and category column names are indicated by the --text_columnand --category_column arguments.  By default, they are 'text', and 'category'. Optionally, a metadata column (named in the --metadata argument) can be present. ")
    parser.add_argument('--outputfile', action='store', dest='outputfile', default='-', help='Path of HTML file on which to store visualization. Pass in - (default) for stdout.')
    parser.add_argument('--text_column', action='store', dest='text_column', default='text', help='Name of the text column.')
    parser.add_argument('--category_column', action='store', dest='category_column', default='category', help='Name of the category column.')
    parser.add_argument('--metadata_column', action='store', dest='metadata_column', default=None, help='Name of the category column.')
    parser.add_argument('--positive_category', action='store', required=True, dest='positive_category', help='Postive category.  A value in category_column to be considered the positive class. All others will be considered negative.')
    parser.add_argument('--category_display_name', action='store', dest='category_display_name', default=None, help='Positive category name which will be used on the visualization. By default, it will just be thepostive category value.')
    parser.add_argument('--not_category_display_name', action='store', default=None, dest='not_category_display_name', help="Positive category name which will be used on the visualization. By default, it will just be the word 'not' in front of the positive value.")
    parser.add_argument('--pmi_threshold', action='store', dest='pmi_threshold', type=int, help='2 * minimum allowable PMI value.  Default 6.')
    parser.add_argument('--width_in_pixels', action='store', dest='width_in_pixels', type=int, default=1000, help='Width of the visualization in pixels.')
    parser.add_argument('--minimum_term_frequency', action='store', dest='minimum_term_frequency', type=int, default=3, help='Minimum number of times a term needs to appear. Default 3')
    parser.add_argument('--regex_parser', action='store_true', dest='regex_parser', default=False, help="If present, don't use spaCy for preprocessing.  Instead, use a simple, dumb, regex.")
    parser.add_argument('--spacy_language_model', action='store', dest='spacy_language_model', default='en_core_web_sm', help="If present, pick the spaCy language model to use. Default is 'en_core_web_sm'. Other valid values include 'de' and 'fr'. --regex_parser will override.Please see https://spacy.io/docs/api/language-models for moredetails")
    parser.add_argument('--one_use_per_doc', action='store_true', dest='one_use_per_doc', default=False, help='Only count one use per document.')
    args = parser.parse_args()
    df = pd.read_csv(args.datafile)
    if args.category_column not in df.columns:
        raise Exception('category_column (%s) must be a column name in csv. Must be one of %s' % (args.category_column, ', '.join(df.columns)))
    if args.text_column not in df.columns:
        raise Exception('text_column (%s) must be a column name in csv. Must be one of %s' % (args.text_column, ', '.join(df.columns)))
    if args.metadata_column is not None and args.metadata_column not in df.columns:
        raise Exception('metadata_column (%s) must be a column name in csv. Must be one of %s' % (args.metadata_column, ', '.join(df.columns)))
    if args.positive_category not in df[args.category_column].unique():
        raise Exception('positive_category (%s) must be in the column %s, with a case-sensitive match.' % (args.positive_category, args.category_column))
    if args.regex_parser:
        nlp = whitespace_nlp_with_sentences
    else:
        import spacy
        nlp = spacy.load(args.spacy_language_model)
    term_ranker = None
    if args.one_use_per_doc is True:
        term_ranker = OncePerDocFrequencyRanker
    category_display_name = args.category_display_name
    if category_display_name is None:
        category_display_name = args.positive_category
    not_category_display_name = args.not_category_display_name
    if not_category_display_name is None:
        not_category_display_name = 'Not ' + category_display_name
    corpus = CorpusFromPandas(df, category_col=args.category_column, text_col=args.text_column, nlp=nlp).build()
    html = produce_scattertext_explorer(corpus, category=args.positive_category, category_name=category_display_name, not_category_name=not_category_display_name, minimum_term_frequency=args.minimum_term_frequency, pmi_filter_thresold=args.pmi_threshold, width_in_pixels=args.width_in_pixels, term_ranker=term_ranker, metadata=None if args.metadata_column is None else df[args.metadata_column])
    if args.outputfile == '-':
        print(html)
    else:
        with open(args.outputfile, 'wb') as o:
            o.write(html.encode('utf-8'))

class DeployedClassifierFactory:

    def __init__(self, term_doc_matrix, term_doc_matrix_factory, category, nlp=None):
        """This is a class that enables one to train and save a classification model.

		Parameters
		----------
		term_doc_matrix : TermDocMatrix
		term_doc_matrix_factory : TermDocMatrixFactory
		category : str
			Category name
		nlp : spacy parser
		"""
        self._term_doc_matrix = term_doc_matrix
        self._term_doc_matrix_factory = term_doc_matrix_factory
        assert term_doc_matrix_factory._nlp is None
        assert term_doc_matrix_factory.category_text_iter is None
        self._category = category
        self._clf = None
        self._proba = None

    def passive_aggressive_train(self):
        """Trains passive aggressive classifier

		"""
        self._clf = PassiveAggressiveClassifier(n_iter=50, C=0.2, n_jobs=-1, random_state=0)
        self._clf.fit(self._term_doc_matrix._X, self._term_doc_matrix._y)
        y_dist = self._clf.decision_function(self._term_doc_matrix._X)
        pos_ecdf = ECDF(y_dist[y_dist >= 0])
        neg_ecdf = ECDF(y_dist[y_dist <= 0])

        def proba_function(distance_from_hyperplane):
            if distance_from_hyperplane > 0:
                return pos_ecdf(distance_from_hyperplane) / 2.0 + 0.5
            elif distance_from_hyperplane < 0:
                return pos_ecdf(distance_from_hyperplane) / 2.0
            return 0.5
        self._proba = proba_function
        return self

    def build(self):
        """Builds Depoyed Classifier
		"""
        if self._clf is None:
            raise NeedToTrainExceptionBeforeDeployingException()
        return DeployedClassifier(self._category, self._term_doc_matrix._category_idx_store, self._term_doc_matrix._term_idx_store, self._term_doc_matrix_factory)

def passive_aggressive_train(self):
    """Trains passive aggressive classifier

		"""
    self._clf = PassiveAggressiveClassifier(n_iter=50, C=0.2, n_jobs=-1, random_state=0)
    self._clf.fit(self._term_doc_matrix._X, self._term_doc_matrix._y)
    y_dist = self._clf.decision_function(self._term_doc_matrix._X)
    pos_ecdf = ECDF(y_dist[y_dist >= 0])
    neg_ecdf = ECDF(y_dist[y_dist <= 0])

    def proba_function(distance_from_hyperplane):
        if distance_from_hyperplane > 0:
            return pos_ecdf(distance_from_hyperplane) / 2.0 + 0.5
        elif distance_from_hyperplane < 0:
            return pos_ecdf(distance_from_hyperplane) / 2.0
        return 0.5
    self._proba = proba_function
    return self

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

def get_nlp(self):
    nlp = self._nlp
    if nlp is None:
        import spacy
        nlp = spacy.load('en_core_web_sm')
    return nlp

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

def _get_old_to_new_metadata_mapping_df(self, old_to_new_vals: List[Tuple[str, str]]) -> pd.DataFrame:
    old_to_new_vals = [(old, new) for old, new in old_to_new_vals if old in self._metadata_idx_store]
    return pd.DataFrame(old_to_new_vals, columns=['Old', 'New'])

def produce_projection_explorer(corpus, category, word2vec_model=None, projection_model=None, embeddings=None, term_acceptance_re=re.compile('[a-z]{3,}'), show_axes=False, **kwargs):
    """
    Parameters
    ----------
    corpus : ParsedCorpus
        It is highly recommended to use a stoplisted, unigram corpus-- `corpus.get_stoplisted_unigram_corpus()`
    category : str
    word2vec_model : Word2Vec
        A gensim word2vec model.  A default model will be used instead. See Word2VecFromParsedCorpus for the default
        model.
    projection_model : sklearn-style dimensionality reduction model.
        By default: umap.UMAP(min_dist=0.5, metric='cosine')
      You could also use, e.g., sklearn.manifold.TSNE(perplexity=10, n_components=2, init='pca', n_iter=2500, random_state=23)
    embeddings : array[len(corpus.get_terms()), X]
        Word embeddings.  If None (default), will train them using word2vec Model
    term_acceptance_re : SRE_Pattern,
        Regular expression to identify valid terms
    show_axes : bool, default False
        Show the ticked axes on the plot.  If false, show inner axes as a crosshair.
    kwargs : dict
        Remaining produce_scattertext_explorer keywords get_tooltip_content

    Returns
    -------
    str
    HTML of visualization

    """
    embeddings_resolover = EmbeddingsResolver(corpus)
    if embeddings is not None:
        embeddings_resolover.set_embeddings(embeddings)
    else:
        embeddings_resolover.set_embeddings_model(word2vec_model, term_acceptance_re)
    corpus, word_axes = embeddings_resolover.project_embeddings(projection_model, x_dim=0, y_dim=1)
    html = produce_scattertext_explorer(corpus=corpus, category=category, minimum_term_frequency=0, sort_by_dist=False, x_coords=scale(word_axes['x']), y_coords=scale(word_axes['y']), y_label='', x_label='', show_axes=show_axes, **kwargs)
    return html

def produce_pca_explorer(corpus, category, word2vec_model=None, projection_model=None, embeddings=None, projection=None, term_acceptance_re=re.compile('[a-z]{3,}'), x_dim=0, y_dim=1, scaler=scale, show_axes=False, show_dimensions_on_tooltip=True, x_label='', y_label='', **kwargs):
    """
    Parameters
    ----------
    corpus : ParsedCorpus
        It is highly recommended to use a stoplisted, unigram corpus-- `corpus.get_stoplisted_unigram_corpus()`
    category : str
    word2vec_model : Word2Vec
        A gensim word2vec model.  A default model will be used instead. See Word2VecFromParsedCorpus for the default
        model.
    projection_model : sklearn-style dimensionality reduction model. Ignored if 'projection' is presents
        By default: umap.UMAP(min_dist=0.5, metric='cosine') unless projection is present. If so,
        You could also use, e.g., sklearn.manifold.TSNE(perplexity=10, n_components=2, init='pca', n_iter=2500, random_state=23)
    embeddings : array[len(corpus.get_terms()), X]
        Word embeddings.  If None (default), and no value is passed into projection, use word2vec_model
    projection : DataFrame('x': array[len(corpus.get_terms())], 'y': array[len(corpus.get_terms())])
        If None (default), produced using projection_model
    term_acceptance_re : SRE_Pattern,
        Regular expression to identify valid terms
    x_dim : int, default 0
        Dimension of transformation matrix for x-axis
    y_dim : int, default 1
        Dimension of transformation matrix for y-axis
    scalers : function , default scattertext.Scalers.scale
        Function used to scale projection
    show_axes : bool, default False
        Show the ticked axes on the plot.  If false, show inner axes as a crosshair.
    show_dimensions_on_tooltip : bool, False by default
        If true, shows dimension positions on tooltip, along with term name. Otherwise, default to the
         get_tooltip_content parameter.
    kwargs : dict
        Remaining produce_scattertext_explorer keywords get_tooltip_content

    Returns
    -------
    str
    HTML of visualization
    """
    if projection is None:
        embeddings_resolover = EmbeddingsResolver(corpus)
        if embeddings is not None:
            embeddings_resolover.set_embeddings(embeddings)
        else:
            embeddings_resolover.set_embeddings_model(word2vec_model, term_acceptance_re)
        corpus, projection = embeddings_resolover.project_embeddings(projection_model, x_dim=x_dim, y_dim=y_dim)
    else:
        assert type(projection) == pd.DataFrame
        assert 'x' in projection and 'y' in projection
        if kwargs.get('use_non_text_features', False):
            assert set(projection.index) == set(corpus.get_metadata())
        else:
            assert set(projection.index) == set(corpus.get_terms())
    if show_dimensions_on_tooltip:
        kwargs['get_tooltip_content'] = '(function(d) {\n     return  d.term + "<br/>Dim %s: " + Math.round(d.ox*1000)/1000 + "<br/>Dim %s: " + Math.round(d.oy*1000)/1000 \n    })' % (x_dim, y_dim)
    html = produce_scattertext_explorer(corpus=corpus, category=category, minimum_term_frequency=0, sort_by_dist=False, original_x=projection['x'], original_y=projection['y'], x_coords=scaler(projection['x']), y_coords=scaler(projection['y']), y_label=y_label, x_label=x_label, show_axes=show_axes, horizontal_line_y_position=kwargs.get('horizontal_line_y_position', None), vertical_line_x_position=kwargs.get('vertical_line_x_position', None), **kwargs)
    return html

def sparse_explorer(corpus, category, scores, category_name=None, not_category_name=None, **kwargs):
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
    scores : np.array
        Scores to display in visualization.  Zero scores are grey.

    Remaining arguments are from `produce_scattertext_explorer`.

    Returns
    -------
        str, html of visualization
    """
    return produce_scattertext_explorer(corpus, category, category_name, not_category_name, scores=scores, sort_by_dist=False, gray_zero_scores=True, **kwargs)

def produce_two_axis_plot(corpus, x_score_df, y_score_df, x_label, y_label, statistic_column='cohens_d', p_value_column='cohens_d_p', statistic_name='d', use_non_text_features=False, pick_color=pick_color, axis_scaler=scale_neg_1_to_1_with_zero_mean, distance_measure=EuclideanDistance, semiotic_square_labels=None, x_tooltip_label=None, y_tooltip_label=None, **kwargs):
    """

    :param corpus: Corpus
    :param x_score_df: pd.DataFrame, contains effect_size_column, p_value_column. outputted by CohensD
    :param y_score_df: pd.DataFrame, contains effect_size_column, p_value_column. outputted by CohensD
    :param x_label: str
    :param y_label: str
    :param statistic_column: str, column in x_score_df, y_score_df giving statistics, default cohens_d
    :param p_value_column: str, column in x_score_df, y_score_df giving effect sizes, default cohens_d_p
    :param statistic_name: str, column which corresponds to statistic name, defauld d
    :param use_non_text_features: bool, default True
    :param pick_color: func, returns color, default is pick_color
    :param axis_scaler: func, scaler default is scale_neg_1_to_1_with_zero_mean
    :param distance_measure: DistanceMeasureBase, default EuclideanDistance
        This is how parts of the square are populated
    :param semiotic_square_labels: dict, semiotic square position labels
    :param x_tooltip_label: str, if None, x_label
    :param y_tooltip_label: str, if None, y_label
    :param kwargs: dict, other arguments
    :return: str, html
    """
    if use_non_text_features:
        terms = corpus.get_metadata()
    else:
        terms = corpus.get_terms()
    axes = pd.DataFrame({'x': x_score_df[statistic_column], 'y': y_score_df[statistic_column]}).loc[terms]
    merged_scores = pd.merge(x_score_df, y_score_df, left_index=True, right_index=True).loc[terms]
    x_tooltip_label = x_label if x_tooltip_label is None else x_tooltip_label
    y_tooltip_label = y_label if y_tooltip_label is None else y_tooltip_label

    def generate_term_metadata(term_struct):
        if p_value_column + '_corr_x' in term_struct:
            x_p = term_struct[p_value_column + '_corr_x']
        elif p_value_column + '_x' in term_struct:
            x_p = term_struct[p_value_column + '_x']
        else:
            x_p = None
        if p_value_column + '_corr_y' in term_struct:
            y_p = term_struct[p_value_column + '_corr_y']
        elif p_value_column + '_y' in term_struct:
            y_p = term_struct[p_value_column + '_y']
        else:
            y_p = None
        if x_p is not None:
            x_p = min(x_p, 1.0 - x_p)
        if y_p is not None:
            y_p = min(y_p, 1.0 - y_p)
        x_d = term_struct[statistic_column + '_x']
        y_d = term_struct[statistic_column + '_y']
        tooltip = '%s: %s: %0.3f' % (x_tooltip_label, statistic_name, x_d)
        if x_p is not None:
            tooltip += '; p: %0.4f' % x_p
        tooltip += '<br/>'
        tooltip += '%s: %s: %0.3f' % (y_tooltip_label, statistic_name, y_d)
        if y_p is not None:
            tooltip += '; p: %0.4f' % y_p
        return {'tooltip': tooltip, 'color': pick_color(x_p, y_p, np.abs(x_d), np.abs(y_d))}
    explanations = merged_scores.apply(generate_term_metadata, axis=1)
    semiotic_square = SemioticSquareFromAxes(corpus, axes, x_axis_name=x_label, y_axis_name=y_label, labels=semiotic_square_labels, distance_measure=distance_measure)
    get_tooltip_content = kwargs.get('get_tooltip_content', '(function(d) {return d.term + "<br/> " + d.etc.tooltip})')
    color_func = kwargs.get('color_func', '(function(d) {return d.etc.color})')
    html = produce_scattertext_explorer(corpus, category=corpus.get_categories()[0], sort_by_dist=False, x_coords=axis_scaler(axes['x']), y_coords=axis_scaler(axes['y']), original_x=axes['x'], original_y=axes['y'], show_characteristic=False, show_top_terms=False, show_category_headings=True, x_label=x_label, y_label=y_label, semiotic_square=semiotic_square, get_tooltip_content=get_tooltip_content, x_axis_values=None, y_axis_values=None, unified_context=True, color_func=color_func, show_axes=False, term_metadata=explanations.to_dict(), use_non_text_features=use_non_text_features, **kwargs)
    return html

def produce_scattertext_digraph(df, text_col, source_col, dest_col, source_name='Source', dest_name='Destination', graph_width=500, graph_height=500, metadata_func=None, enable_pan_and_zoom=True, engine='dot', graph_params=None, node_params=None, **kwargs):
    """

    :param df: pd.DataFrame
    :param text_col: str
    :param source_col: str
    :param dest_col: str
    :param source_name: str
    :param dest_name: str
    :param graph_width: int
    :param graph_height: int
    :param metadata_func: lambda
    :param enable_pan_and_zoom: bool
    :param engine: str, The graphviz engine (e.g., dot or neat)
    :param graph_params dict or None, graph parameters in graph viz
    :param node_params dict or None, node parameters in graph viz
    :param kwargs: dicdt
    :return:
    """
    graph_df = pd.concat([df.assign(__text=lambda df: df[source_col], __alttext=lambda df: df[text_col], __category='source'), df.assign(__text=lambda df: df[dest_col], __alttext=lambda df: df[text_col], __category='target')])
    corpus = CorpusFromParsedDocuments(graph_df, category_col='__category', parsed_col='__text', feats_from_spacy_doc=UseFullDocAsMetadata()).build()
    edges = corpus.get_df()[[source_col, dest_col]].rename(columns={source_col: 'source', dest_col: 'target'}).drop_duplicates()
    component_graph = SimpleDiGraph(edges).make_component_digraph(graph_params=graph_params, node_params=node_params)
    graph_renderer = ComponentDiGraphHTMLRenderer(component_graph, height=graph_height, width=graph_width, enable_pan_and_zoom=enable_pan_and_zoom, engine=engine)
    alternative_term_func = '(function(termDict) {\n        document.querySelectorAll(".dotgraph").forEach(svg => svg.style.display = \'none\');\n        showTermGraph(termDict[\'term\']);\n        return true;\n    })'
    scatterplot_structure = produce_scattertext_explorer(corpus, category='source', category_name=source_name, not_category_name=dest_name, minimum_term_frequency=0, pmi_threshold_coefficient=0, alternative_text_field='__alttext', use_non_text_features=True, transform=dense_rank, metadata=corpus.get_df().apply(metadata_func, axis=1) if metadata_func else None, return_scatterplot_structure=True, width_in_pixels=kwargs.get('width_in_pixels', 700), max_overlapping=kwargs.get('max_overlapping', 3), color_func=kwargs.get('color_func', '(function(x) {return "#5555FF"})'), alternative_term_func=alternative_term_func, **kwargs)
    html = GraphStructure(scatterplot_structure, graph_renderer=graph_renderer).to_html()
    return html

def dataframe_scattertext(corpus: Corpus, plot_df: pd.DataFrame, **kwargs):
    assert 'X' in plot_df
    assert 'Y' in plot_df
    if 'Xpos' not in plot_df:
        plot_df['Xpos'] = Scalers.scale(plot_df['X'])
    if 'Ypos' not in plot_df:
        plot_df['Ypos'] = Scalers.scale(plot_df['Y'])
    use_metadata = kwargs.get('use_non_text_features', False)
    excess_terms = list(set(corpus.get_terms(use_metadata=use_metadata)) - set(plot_df.index))
    if excess_terms:
        print(f'There are {('metadata' if use_metadata else 'terms')} in the corpus which are not in the index of plot_df. These will not be available in the visualization. These are: {excess_terms}.s')
        corpus = corpus.remove_terms(terms=excess_terms, non_text=True)
    plot_df = plot_df.reindex(corpus.get_terms(use_metadata=use_metadata))
    assert len(plot_df) > 0
    if 'term_description_columns' not in kwargs:
        kwargs['term_description_columns'] = [x for x in plot_df.columns if x not in ['X', 'Y', 'Xpos', 'Ypos', 'ColorScore']]
    if 'tooltip_columns' not in kwargs:
        kwargs['tooltip_columns'] = ['Xpos', 'Ypos']
        kwargs['tooltip_column_names'] = {'Xpos': kwargs.get('x_label', 'X'), 'Ypos': kwargs.get('y_label', 'Y')}
    (kwargs.setdefault('metadata', None),)
    (kwargs.setdefault('scores', plot_df['Score'] if 'Score' in plot_df else 0),)
    kwargs.setdefault('minimum_term_frequency', 0)
    kwargs.setdefault('pmi_threshold_coefficient', 0)
    kwargs.setdefault('category', corpus.get_categories()[0])
    kwargs.setdefault('original_x', plot_df['X'].values)
    kwargs.setdefault('original_y', plot_df['Y'].values)
    kwargs.setdefault('x_coords', plot_df['Xpos'].values)
    kwargs.setdefault('y_coords', plot_df['Ypos'].values)
    kwargs.setdefault('use_global_scale', True)
    kwargs.setdefault('ignore_categories', True)
    kwargs.setdefault('unified_context', kwargs['ignore_categories'])
    kwargs.setdefault('show_axes_and_cross_hairs', 0)
    kwargs.setdefault('show_top_terms', False)
    kwargs.setdefault('x_label', 'X')
    kwargs.setdefault('y_label', 'Y')
    return produce_scattertext_explorer(corpus, term_metadata_df=plot_df, **kwargs)

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

def get_term_doc_count_df(self, label_append=' freq'):
    """

        Returns
        -------
        pd.DataFrame indexed on terms, with columns the number of documents each term appeared in
        each category
        """
    mat = self.get_term_count_mat()
    return pd.DataFrame(mat, index=self.get_terms(), columns=[str(c) + label_append for c in self.get_categories()])

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

def build(self):
    """

        :return: ParsedCorpus
        """
    category_col = 'Category'
    while category_col in self.df:
        category_col = 'Category_' + ''.join((np.random.choice(string.ascii_letters) for _ in range(5)))
    return CorpusFromParsedDocuments(self.df.assign(**{category_col: '_'}), category_col, self.parsed_col, feats_from_spacy_doc=self.feats_from_spacy_doc).build()

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

def get_texts(self):
    """
        Returns
        -------
        pd.Series, all raw documents
        """
    if sys.version_info[0] == 2:
        return self._df[self._parsed_col]
    return self._df[self._parsed_col].apply(str)

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

def get_document_lengths_in_tokens_and_categories(self):
    return pd.DataFrame({'Length': self.get_parsed_docs().apply(len).values, 'Category': self.get_category_names_by_row()})

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

def get_frequencies(self, term_doc_matrix) -> pd.Series:
    return self.__get_term_ranks_and_frequencies(term_doc_matrix)[1]

class TestClassPercentageCompactor(TestCase):

    def test_compact(self):
        term_doc_mat = TermDocMatrixFromFrequencies(pd.DataFrame({'term': ['a', 'a b', 'a c', 'c', 'b', 'e b', 'e'], 'A freq': [6, 3, 3, 3, 50000, 0, 0], 'B freq': [600000, 3, 30, 3, 50, 1, 1]}).set_index('term')).build()
        new_tdm = ClassPercentageCompactor(term_count=10000).compact(term_doc_mat)
        self.assertEqual(term_doc_mat.get_terms(), ['a', 'a b', 'a c', 'c', 'b', 'e b', 'e'])
        self.assertEqual(set(new_tdm.get_terms()), {'a', 'b'})

def test_compact(self):
    term_doc_mat = TermDocMatrixFromFrequencies(pd.DataFrame({'term': ['a', 'a b', 'a c', 'c', 'b', 'e b', 'e'], 'A freq': [6, 3, 3, 3, 50000, 0, 0], 'B freq': [600000, 3, 30, 3, 50, 1, 1]}).set_index('term')).build()
    new_tdm = ClassPercentageCompactor(term_count=10000).compact(term_doc_mat)
    self.assertEqual(term_doc_mat.get_terms(), ['a', 'a b', 'a c', 'c', 'b', 'e b', 'e'])
    self.assertEqual(set(new_tdm.get_terms()), {'a', 'b'})

class TestDispersion(unittest.TestCase):

    def test_main(self):
        doc_df = pd.DataFrame({'Text': [x.strip() for x in 'b a m n i b e u p\n        b a s a t b e w q n\n        b c a g a b e s t a\n        b a g h a b e a a t\n        b a h a a b e a x a t'.split('\n')]}).assign(Parse=lambda df: df.Text.apply(whitespace_nlp))
        corpus = CorpusWithoutCategoriesFromParsedDocuments(doc_df, parsed_col='Parse').build().get_unigram_corpus()
        dispersion_df = Dispersion(corpus).get_df()
        dispersion_df = dispersion_df.loc[['b', 'i', 'q', 'x']]
        assert list(dispersion_df['Range'].values) == [5, 1, 1, 1]
        assert list(dispersion_df['SD'].values) == [0, 0.4, 0.4, 0.4]
        assert list(dispersion_df['VC'].values) == [0, 2, 2, 2]
        np.testing.assert_almost_equal(list(dispersion_df["Juilland's D"].values), np.array([0.968, 0, 0, 0]), decimal=3)
        np.testing.assert_almost_equal(list(dispersion_df["Rosengren's S"].values), np.array([0.999, 0.18, 0.2, 0.22]), decimal=3)
        np.testing.assert_almost_equal(list(dispersion_df['DP'].values), np.array([0.02, 0.82, 0.8, 0.78]), decimal=3)
        np.testing.assert_almost_equal(list(dispersion_df['DP norm'].values), np.array([0.024, 1, 0.976, 0.951]), decimal=3)
        np.testing.assert_almost_equal(list(dispersion_df['KL-divergence'].values), np.array([0.003, 2.474, 2.322, 2.184]), decimal=3)

def test_main(self):
    doc_df = pd.DataFrame({'Text': [x.strip() for x in 'b a m n i b e u p\n        b a s a t b e w q n\n        b c a g a b e s t a\n        b a g h a b e a a t\n        b a h a a b e a x a t'.split('\n')]}).assign(Parse=lambda df: df.Text.apply(whitespace_nlp))
    corpus = CorpusWithoutCategoriesFromParsedDocuments(doc_df, parsed_col='Parse').build().get_unigram_corpus()
    dispersion_df = Dispersion(corpus).get_df()
    dispersion_df = dispersion_df.loc[['b', 'i', 'q', 'x']]
    assert list(dispersion_df['Range'].values) == [5, 1, 1, 1]
    assert list(dispersion_df['SD'].values) == [0, 0.4, 0.4, 0.4]
    assert list(dispersion_df['VC'].values) == [0, 2, 2, 2]
    np.testing.assert_almost_equal(list(dispersion_df["Juilland's D"].values), np.array([0.968, 0, 0, 0]), decimal=3)
    np.testing.assert_almost_equal(list(dispersion_df["Rosengren's S"].values), np.array([0.999, 0.18, 0.2, 0.22]), decimal=3)
    np.testing.assert_almost_equal(list(dispersion_df['DP'].values), np.array([0.02, 0.82, 0.8, 0.78]), decimal=3)
    np.testing.assert_almost_equal(list(dispersion_df['DP norm'].values), np.array([0.024, 1, 0.976, 0.951]), decimal=3)
    np.testing.assert_almost_equal(list(dispersion_df['KL-divergence'].values), np.array([0.003, 2.474, 2.322, 2.184]), decimal=3)

class TestCorpusFromFeatureDict(TestCase):

    def test_build(self):
        df = pd.DataFrame([{'text': 'The President opened the speech by welcoming the Speaker, Vice President, Members of Congress, and fellow Americans. He noted that this was his eighth speech, and promised it would be shorter than usual, joking that he knew "some of you are antsy to get back to Iowa." He recognized people\'s generally low expectations for meaningful legislature due to 2016 being an election year, and thanked the House Speaker Paul Ryan for his help passing the budget and making tax cuts permanent for working families. He expressed hope that progress could be made on "bipartisan priorities like criminal justice reform, and helping people who are battling prescription drug abuse." He then listed proposals for the year ahead, per tradition. They included helping students learn to write computer code, personalizing medical treatments for patients, fixing the immigration system he called broken, protecting US children from gun violence, achieving equal pay for equal work in a nod towards gender equality, implementing paid leave, and raising the minimum wage.', 'feats': {'president': 3, 'he': 2}, 'category': '2016'}, {'text': 'He then addressed the third question, how to ensure America\'s safety without either becoming isolationist or having to nation-build across the world. He highlighted the strength of the US military, and criticized those who claimed America was getting weaker as its enemies were getting stronger. He pointed out that failing states were the biggest threat to the US, not evil empires. He listed as his top priority "protecting the American people and going after terrorist networks." He discussed the threat of al Qaeda and ISIL, but pointed out that they did not threaten "our national existence," and dismissed claims otherwise as harmful propaganda. He then detailed the American and 60 country coalition efforts to defeat terrorism and to "cut off ISIL’s financing, disrupt their plots, stop the flow of terrorist fighters, and stamp out their vicious ideology. With nearly 10,000 air strikes, we are taking out their leadership, their oil, their training camps, and their weapons. We are training, arming, and supporting forces who are steadily reclaiming territory in Iraq and Syria."', 'feats': {'addressed': 5, 'he': 2}, 'category': '2016'}, {'text': 'Senator Bernie Sanders of Vermont (an independent who caucuses with the Democrats in the Senate) responded to the speech in a 14-minute video posted to Facebook, in which he criticized Trump for failing to make any mention of income inequality, criminal justice reform, or climate change.[23] Sanders also stated: "President Trump once again made it clear he plans on working with Republicans in Congress who want to repeal the Affordable Care Act, throw 20 million Americans off of health insurance, privatize Medicare, make massive cuts in Medicaid, raise the cost of prescription drugs to seniors, eliminate funding for Planned Parenthood, while at the same time, he wants to give another massive tax break to the wealthiest Americans."[23]."', 'feats': {'medicare': 2, 'Trump': 3, 'senator bernie sanders': 8, 'he': 2}, 'category': '2017'}, {'text': 'The 45th President of the United States, Donald Trump, gave his first public address before a joint session of the United States Congress on Tuesday, February 28, 2017. Similar to a State of the Union address, it was delivered before the 115th United States Congress in the Chamber of the United States House of Representatives in the United States Capitol.[6] Presiding over this joint session was the House Speaker, Paul Ryan. Accompanying the Speaker of the House was the President of the United States Senate, Mike Pence, the Vice President of the United States."', 'feats': {'trump': 9, 'president': 8, 'he': 2}, 'category': '2017'}])
        corpus = CorpusFromFeatureDict(df=df, category_col='category', text_col='text', feature_col='feats').build()
        self.assertEquals(len(corpus.get_terms()), 7)
        self.assertEqual(len(corpus.get_categories()), 2)
        self.assertEqual(len(corpus.get_texts()), 4)
        self.assertEqual(corpus.get_texts()[0], df.text.iloc[0])
        self.assertEqual(corpus.get_texts()[3], df.text.iloc[3])
        self.assertFalse(np.array_equal(corpus._X[0, :], corpus._X[0, :]))
        corpus.get_df()

    def test_metadata(self):
        df = pd.DataFrame([{'text': 'The President opened the speech by welcoming the Speaker, Vice President, Members of Congress, and fellow Americans. He noted that this was his eighth speech, and promised it would be shorter than usual, joking that he knew "some of you are antsy to get back to Iowa." He recognized people\'s generally low expectations for meaningful legislature due to 2016 being an election year, and thanked the House Speaker Paul Ryan for his help passing the budget and making tax cuts permanent for working families. He expressed hope that progress could be made on "bipartisan priorities like criminal justice reform, and helping people who are battling prescription drug abuse." He then listed proposals for the year ahead, per tradition. They included helping students learn to write computer code, personalizing medical treatments for patients, fixing the immigration system he called broken, protecting US children from gun violence, achieving equal pay for equal work in a nod towards gender equality, implementing paid leave, and raising the minimum wage.', 'feats': {'president': 3, 'he': 2}, 'meta': {'word_count': 32}, 'category': '2016'}, {'text': 'He then addressed the third question, how to ensure America\'s safety without either becoming isolationist or having to nation-build across the world. He highlighted the strength of the US military, and criticized those who claimed America was getting weaker as its enemies were getting stronger. He pointed out that failing states were the biggest threat to the US, not evil empires. He listed as his top priority "protecting the American people and going after terrorist networks." He discussed the threat of al Qaeda and ISIL, but pointed out that they did not threaten "our national existence," and dismissed claims otherwise as harmful propaganda. He then detailed the American and 60 country coalition efforts to defeat terrorism and to "cut off ISIL’s financing, disrupt their plots, stop the flow of terrorist fighters, and stamp out their vicious ideology. With nearly 10,000 air strikes, we are taking out their leadership, their oil, their training camps, and their weapons. We are training, arming, and supporting forces who are steadily reclaiming territory in Iraq and Syria."', 'feats': {'addressed': 5, 'he': 2}, 'meta': {'word_count': 44}, 'category': '2016'}, {'text': 'Senator Bernie Sanders of Vermont (an independent who caucuses with the Democrats in the Senate) responded to the speech in a 14-minute video posted to Facebook, in which he criticized Trump for failing to make any mention of income inequality, criminal justice reform, or climate change.[23] Sanders also stated: "President Trump once again made it clear he plans on working with Republicans in Congress who want to repeal the Affordable Care Act, throw 20 million Americans off of health insurance, privatize Medicare, make massive cuts in Medicaid, raise the cost of prescription drugs to seniors, eliminate funding for Planned Parenthood, while at the same time, he wants to give another massive tax break to the wealthiest Americans."[23]."', 'feats': {'medicare': 2, 'Trump': 3, 'senator bernie sanders': 8, 'he': 2}, 'meta': {'word_count': 20}, 'category': '2017'}, {'text': 'The 45th President of the United States, Donald Trump, gave his first public address before a joint session of the United States Congress on Tuesday, February 28, 2017. Similar to a State of the Union address, it was delivered before the 115th United States Congress in the Chamber of the United States House of Representatives in the United States Capitol.[6] Presiding over this joint session was the House Speaker, Paul Ryan. Accompanying the Speaker of the House was the President of the United States Senate, Mike Pence, the Vice President of the United States."', 'feats': {'trump': 9, 'president': 8, 'he': 2}, 'meta': {'word_count': 10}, 'category': '2017'}])
        corpus = CorpusFromFeatureDict(df=df, category_col='category', text_col='text', feature_col='feats', metadata_col='meta').build()
        self.assertEquals(len(corpus.get_terms()), 7)
        self.assertEqual(len(corpus.get_categories()), 2)
        self.assertEqual(len(corpus.get_texts()), 4)
        self.assertEqual(corpus.get_texts()[0], df.text.iloc[0])
        self.assertEqual(corpus.get_texts()[3], df.text.iloc[3])
        self.assertFalse(np.array_equal(corpus._X[0, :], corpus._X[0, :]))
        expected = pd.DataFrame([{'term': 'word_count', '2016 freq': np.int32(76), '2017 freq': np.int32(30)}]).set_index('term').astype(np.int32)
        pd.testing.assert_frame_equal(corpus.get_metadata_freq_df(), expected)

def test_build(self):
    df = pd.DataFrame([{'text': 'The President opened the speech by welcoming the Speaker, Vice President, Members of Congress, and fellow Americans. He noted that this was his eighth speech, and promised it would be shorter than usual, joking that he knew "some of you are antsy to get back to Iowa." He recognized people\'s generally low expectations for meaningful legislature due to 2016 being an election year, and thanked the House Speaker Paul Ryan for his help passing the budget and making tax cuts permanent for working families. He expressed hope that progress could be made on "bipartisan priorities like criminal justice reform, and helping people who are battling prescription drug abuse." He then listed proposals for the year ahead, per tradition. They included helping students learn to write computer code, personalizing medical treatments for patients, fixing the immigration system he called broken, protecting US children from gun violence, achieving equal pay for equal work in a nod towards gender equality, implementing paid leave, and raising the minimum wage.', 'feats': {'president': 3, 'he': 2}, 'category': '2016'}, {'text': 'He then addressed the third question, how to ensure America\'s safety without either becoming isolationist or having to nation-build across the world. He highlighted the strength of the US military, and criticized those who claimed America was getting weaker as its enemies were getting stronger. He pointed out that failing states were the biggest threat to the US, not evil empires. He listed as his top priority "protecting the American people and going after terrorist networks." He discussed the threat of al Qaeda and ISIL, but pointed out that they did not threaten "our national existence," and dismissed claims otherwise as harmful propaganda. He then detailed the American and 60 country coalition efforts to defeat terrorism and to "cut off ISIL’s financing, disrupt their plots, stop the flow of terrorist fighters, and stamp out their vicious ideology. With nearly 10,000 air strikes, we are taking out their leadership, their oil, their training camps, and their weapons. We are training, arming, and supporting forces who are steadily reclaiming territory in Iraq and Syria."', 'feats': {'addressed': 5, 'he': 2}, 'category': '2016'}, {'text': 'Senator Bernie Sanders of Vermont (an independent who caucuses with the Democrats in the Senate) responded to the speech in a 14-minute video posted to Facebook, in which he criticized Trump for failing to make any mention of income inequality, criminal justice reform, or climate change.[23] Sanders also stated: "President Trump once again made it clear he plans on working with Republicans in Congress who want to repeal the Affordable Care Act, throw 20 million Americans off of health insurance, privatize Medicare, make massive cuts in Medicaid, raise the cost of prescription drugs to seniors, eliminate funding for Planned Parenthood, while at the same time, he wants to give another massive tax break to the wealthiest Americans."[23]."', 'feats': {'medicare': 2, 'Trump': 3, 'senator bernie sanders': 8, 'he': 2}, 'category': '2017'}, {'text': 'The 45th President of the United States, Donald Trump, gave his first public address before a joint session of the United States Congress on Tuesday, February 28, 2017. Similar to a State of the Union address, it was delivered before the 115th United States Congress in the Chamber of the United States House of Representatives in the United States Capitol.[6] Presiding over this joint session was the House Speaker, Paul Ryan. Accompanying the Speaker of the House was the President of the United States Senate, Mike Pence, the Vice President of the United States."', 'feats': {'trump': 9, 'president': 8, 'he': 2}, 'category': '2017'}])
    corpus = CorpusFromFeatureDict(df=df, category_col='category', text_col='text', feature_col='feats').build()
    self.assertEquals(len(corpus.get_terms()), 7)
    self.assertEqual(len(corpus.get_categories()), 2)
    self.assertEqual(len(corpus.get_texts()), 4)
    self.assertEqual(corpus.get_texts()[0], df.text.iloc[0])
    self.assertEqual(corpus.get_texts()[3], df.text.iloc[3])
    self.assertFalse(np.array_equal(corpus._X[0, :], corpus._X[0, :]))
    corpus.get_df()

def test_metadata(self):
    df = pd.DataFrame([{'text': 'The President opened the speech by welcoming the Speaker, Vice President, Members of Congress, and fellow Americans. He noted that this was his eighth speech, and promised it would be shorter than usual, joking that he knew "some of you are antsy to get back to Iowa." He recognized people\'s generally low expectations for meaningful legislature due to 2016 being an election year, and thanked the House Speaker Paul Ryan for his help passing the budget and making tax cuts permanent for working families. He expressed hope that progress could be made on "bipartisan priorities like criminal justice reform, and helping people who are battling prescription drug abuse." He then listed proposals for the year ahead, per tradition. They included helping students learn to write computer code, personalizing medical treatments for patients, fixing the immigration system he called broken, protecting US children from gun violence, achieving equal pay for equal work in a nod towards gender equality, implementing paid leave, and raising the minimum wage.', 'feats': {'president': 3, 'he': 2}, 'meta': {'word_count': 32}, 'category': '2016'}, {'text': 'He then addressed the third question, how to ensure America\'s safety without either becoming isolationist or having to nation-build across the world. He highlighted the strength of the US military, and criticized those who claimed America was getting weaker as its enemies were getting stronger. He pointed out that failing states were the biggest threat to the US, not evil empires. He listed as his top priority "protecting the American people and going after terrorist networks." He discussed the threat of al Qaeda and ISIL, but pointed out that they did not threaten "our national existence," and dismissed claims otherwise as harmful propaganda. He then detailed the American and 60 country coalition efforts to defeat terrorism and to "cut off ISIL’s financing, disrupt their plots, stop the flow of terrorist fighters, and stamp out their vicious ideology. With nearly 10,000 air strikes, we are taking out their leadership, their oil, their training camps, and their weapons. We are training, arming, and supporting forces who are steadily reclaiming territory in Iraq and Syria."', 'feats': {'addressed': 5, 'he': 2}, 'meta': {'word_count': 44}, 'category': '2016'}, {'text': 'Senator Bernie Sanders of Vermont (an independent who caucuses with the Democrats in the Senate) responded to the speech in a 14-minute video posted to Facebook, in which he criticized Trump for failing to make any mention of income inequality, criminal justice reform, or climate change.[23] Sanders also stated: "President Trump once again made it clear he plans on working with Republicans in Congress who want to repeal the Affordable Care Act, throw 20 million Americans off of health insurance, privatize Medicare, make massive cuts in Medicaid, raise the cost of prescription drugs to seniors, eliminate funding for Planned Parenthood, while at the same time, he wants to give another massive tax break to the wealthiest Americans."[23]."', 'feats': {'medicare': 2, 'Trump': 3, 'senator bernie sanders': 8, 'he': 2}, 'meta': {'word_count': 20}, 'category': '2017'}, {'text': 'The 45th President of the United States, Donald Trump, gave his first public address before a joint session of the United States Congress on Tuesday, February 28, 2017. Similar to a State of the Union address, it was delivered before the 115th United States Congress in the Chamber of the United States House of Representatives in the United States Capitol.[6] Presiding over this joint session was the House Speaker, Paul Ryan. Accompanying the Speaker of the House was the President of the United States Senate, Mike Pence, the Vice President of the United States."', 'feats': {'trump': 9, 'president': 8, 'he': 2}, 'meta': {'word_count': 10}, 'category': '2017'}])
    corpus = CorpusFromFeatureDict(df=df, category_col='category', text_col='text', feature_col='feats', metadata_col='meta').build()
    self.assertEquals(len(corpus.get_terms()), 7)
    self.assertEqual(len(corpus.get_categories()), 2)
    self.assertEqual(len(corpus.get_texts()), 4)
    self.assertEqual(corpus.get_texts()[0], df.text.iloc[0])
    self.assertEqual(corpus.get_texts()[3], df.text.iloc[3])
    self.assertFalse(np.array_equal(corpus._X[0, :], corpus._X[0, :]))
    expected = pd.DataFrame([{'term': 'word_count', '2016 freq': np.int32(76), '2017 freq': np.int32(30)}]).set_index('term').astype(np.int32)
    pd.testing.assert_frame_equal(corpus.get_metadata_freq_df(), expected)

def make_a_test_term_doc_matrix():
    return build_from_category_whitespace_delimited_text(get_test_categories_and_documents())

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

def get_hamlet_term_doc_matrix():
    hamlet_docs = get_hamlet_docs()
    hamlet_term_doc_matrix = build_from_category_whitespace_delimited_text([(get_hamlet_snippet_binary_category(text), text) for i, text in enumerate(hamlet_docs)])
    return hamlet_term_doc_matrix

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

@classmethod
def setUp(cls):
    cls.categories, cls.documents = get_docs_categories()
    cls.parsed_docs = []
    for doc in cls.documents:
        cls.parsed_docs.append(whitespace_nlp(doc))
    cls.df = pd.DataFrame({'category': cls.categories, 'parsed': cls.parsed_docs, 'orig': [d.upper() for d in cls.documents]})
    cls.parsed_corpus = CorpusFromParsedDocuments(cls.df, 'category', 'parsed').build()
    cls.corpus = CorpusFromPandas(cls.df, 'category', 'orig', nlp=whitespace_nlp).build()

class TestTermDocMatrixFromFrequencies(TestCase):

    def test_build(self):
        term_freq_df = pd.DataFrame({'term': ['a', 'a b', 'a c', 'c', 'b', 'e b', 'e'], 'A': [6, 3, 3, 3, 5, 0, 0], 'B': [6, 3, 3, 3, 5, 1, 1]}).set_index('term')[['A', 'B']]
        term_doc_mat = TermDocMatrixFromFrequencies(term_freq_df).build()
        self.assertEqual(list(term_doc_mat.get_categories()), ['A', 'B'])
        self.assertEqual(list(term_doc_mat.get_terms()), ['a', 'a b', 'a c', 'c', 'b', 'e b', 'e'])
        np.testing.assert_array_equal(term_freq_df.values, term_doc_mat.get_term_freq_df().values)

def test_build(self):
    term_freq_df = pd.DataFrame({'term': ['a', 'a b', 'a c', 'c', 'b', 'e b', 'e'], 'A': [6, 3, 3, 3, 5, 0, 0], 'B': [6, 3, 3, 3, 5, 1, 1]}).set_index('term')[['A', 'B']]
    term_doc_mat = TermDocMatrixFromFrequencies(term_freq_df).build()
    self.assertEqual(list(term_doc_mat.get_categories()), ['A', 'B'])
    self.assertEqual(list(term_doc_mat.get_terms()), ['a', 'a b', 'a c', 'c', 'b', 'e b', 'e'])
    np.testing.assert_array_equal(term_freq_df.values, term_doc_mat.get_term_freq_df().values)

class TestTermDocMatrixFromPandas(TestCase):

    def test_main(self):
        categories, documents = get_docs_categories()
        df = pd.DataFrame({'category': categories, 'text': documents})
        tdm_factory = TermDocMatrixFromPandas(df, 'category', 'text', nlp=whitespace_nlp)
        term_doc_matrix = tdm_factory.build()
        self.assertIsInstance(term_doc_matrix, TermDocMatrix)
        self.assertEqual(set(term_doc_matrix.get_categories()), set(['hamlet', 'jay-z/r. kelly']))
        self.assertEqual(term_doc_matrix.get_num_docs(), 9)
        term_doc_df = term_doc_matrix.get_term_freq_df()
        self.assertEqual(term_doc_df.loc['of'].sum(), 3)

    def test_one_word_per_docs(self):
        records = [(0, 'verified', 'RAs'), (1, 'view', 'RAs'), (2, 'laminectomy', 'RAs'), (3, 'recognition', 'RAs'), (4, 'possibility', 'RAs'), (5, 'possibility', 'RAs'), (6, 'possibility', 'RAs'), (7, 'observations', 'RAs'), (8, 'observation', 'RAs'), (9, 'observation', 'RAs'), (10, 'observation', 'RAs'), (11, 'observation', 'RAs'), (12, 'observation', 'RAs'), (13, 'implication', 'RAs'), (14, 'idea', 'RAs'), (15, 'hypothesis', 'RAs'), (16, 'fact', 'RAs'), (17, 'fact', 'RAs'), (18, 'fact', 'RAs'), (19, 'fact', 'RAs'), (20, 'fact', 'RAs'), (21, 'surprising', 'RAs'), (22, 'surprising', 'RAs'), (23, 'surprising', 'RAs'), (24, 'suggests', 'RAs'), (25, 'suggests', 'RAs'), (26, 'suggests', 'RAs'), (27, 'suggests', 'RAs'), (28, 'suggests', 'RAs'), (29, 'suggests', 'RAs'), (30, 'suggests', 'RAs'), (31, 'suggests', 'RAs'), (32, 'suggests', 'RAs'), (33, 'suggests', 'RAs'), (34, 'suggests', 'RAs'), (35, 'suggests', 'RAs'), (36, 'suggests', 'RAs'), (37, 'suggests', 'RAs'), (38, 'suggests', 'RAs'), (39, 'suggests', 'RAs'), (40, 'suggests', 'RAs'), (41, 'suggests', 'RAs'), (42, 'suggests', 'RAs'), (43, 'suggests', 'RAs'), (44, 'suggests', 'RAs'), (45, 'suggests', 'RAs'), (46, 'suggests', 'RAs'), (47, 'suggests', 'RAs'), (48, 'suggesting', 'RAs'), (49, 'suggesting', 'RAs'), (50, 'suggesting', 'RAs'), (51, 'suggesting', 'RAs'), (52, 'suggesting', 'RAs'), (53, 'suggesting', 'RAs'), (54, 'suggesting', 'RAs'), (55, 'suggesting', 'RAs'), (56, 'suggesting', 'RAs'), (57, 'suggesting', 'RAs'), (58, 'suggesting', 'RAs'), (59, 'suggesting', 'RAs'), (60, 'suggesting', 'RAs'), (61, 'suggesting', 'RAs'), (62, 'suggesting', 'RAs'), (63, 'suggesting', 'RAs'), (64, 'suggesting', 'RAs'), (65, 'suggesting', 'RAs'), (66, 'suggesting', 'RAs'), (67, 'suggesting', 'RAs'), (68, 'suggesting', 'RAs'), (69, 'suggesting', 'RAs'), (70, 'suggesting', 'RAs'), (71, 'suggesting', 'RAs'), (72, 'suggesting', 'RAs'), (73, 'suggesting', 'RAs'), (74, 'suggesting', 'RAs'), (75, 'suggested', 'RAs'), (76, 'suggested', 'RAs'), (77, 'suggested', 'RAs'), (78, 'suggested', 'RAs'), (79, 'suggested', 'RAs'), (80, 'suggest', 'RAs'), (81, 'suggest', 'RAs'), (82, 'suggest', 'RAs'), (83, 'suggest', 'RAs'), (84, 'suggest', 'RAs'), (85, 'suggest', 'RAs'), (86, 'suggest', 'RAs'), (87, 'suggest', 'RAs'), (88, 'suggest', 'RAs'), (89, 'suggest', 'RAs'), (90, 'suggest', 'RAs'), (91, 'suggest', 'RAs'), (92, 'suggest', 'RAs'), (93, 'suggest', 'RAs'), (94, 'suggest', 'RAs'), (95, 'suggest', 'RAs'), (96, 'suggest', 'RAs'), (97, 'suggest', 'RAs'), (98, 'suggest', 'RAs'), (99, 'suggest', 'RAs'), (100, 'suggest', 'RAs'), (101, 'suggest', 'RAs'), (102, 'suggest', 'RAs'), (103, 'suggest', 'RAs'), (104, 'suggest', 'RAs'), (105, 'suggest', 'RAs'), (106, 'suggest', 'RAs'), (107, 'suggest', 'RAs'), (108, 'suggest', 'RAs'), (109, 'suggest', 'RAs'), (110, 'suggest', 'RAs'), (111, 'suggest', 'RAs'), (112, 'suggest', 'RAs'), (113, 'suggest', 'RAs'), (114, 'suggest', 'RAs'), (115, 'suggest', 'RAs'), (116, 'suggest', 'RAs'), (117, 'suggest', 'RAs'), (118, 'suggest', 'RAs'), (119, 'suggest', 'RAs'), (120, 'suggest', 'RAs'), (121, 'suggest', 'RAs'), (122, 'suggest', 'RAs'), (123, 'suggest', 'RAs'), (124, 'suggest', 'RAs'), (125, 'suggest', 'RAs'), (126, 'suggest', 'RAs'), (127, 'suggest', 'RAs'), (128, 'speculate', 'RAs'), (129, 'speculate', 'RAs'), (130, 'speculate', 'RAs'), (131, 'shows', 'RAs'), (132, 'shows', 'RAs'), (133, 'shows', 'RAs'), (134, 'shows', 'RAs'), (135, 'shows', 'RAs'), (136, 'shown', 'RAs'), (137, 'shown', 'RAs'), (138, 'shown', 'RAs'), (139, 'shown', 'RAs'), (140, 'showing', 'RAs'), (141, 'showing', 'RAs'), (142, 'showing', 'RAs'), (143, 'showing', 'RAs'), (144, 'showing', 'RAs'), (145, 'showing', 'RAs'), (146, 'showed', 'RAs'), (147, 'showed', 'RAs'), (148, 'showed', 'RAs'), (149, 'showed', 'RAs'), (150, 'showed', 'RAs'), (151, 'showed', 'RAs'), (152, 'showed', 'RAs'), (153, 'showed', 'RAs'), (154, 'showed', 'RAs'), (155, 'showed', 'RAs'), (156, 'showed', 'RAs'), (157, 'showed', 'RAs'), (158, 'showed', 'RAs'), (159, 'showed', 'RAs'), (160, 'showed', 'RAs'), (161, 'showed', 'RAs'), (162, 'showed', 'RAs'), (163, 'showed', 'RAs'), (164, 'showed', 'RAs'), (165, 'showed', 'RAs'), (166, 'showed', 'RAs'), (167, 'showed', 'RAs'), (168, 'showed', 'RAs'), (169, 'show', 'RAs'), (170, 'show', 'RAs'), (171, 'show', 'RAs'), (172, 'show', 'RAs'), (173, 'show', 'RAs'), (174, 'show', 'RAs'), (175, 'show', 'RAs'), (176, 'show', 'RAs'), (177, 'show', 'RAs'), (178, 'show', 'RAs'), (179, 'show', 'RAs'), (180, 'show', 'RAs'), (181, 'show', 'RAs'), (182, 'show', 'RAs'), (183, 'show', 'RAs'), (184, 'show', 'RAs'), (185, 'show', 'RAs'), (186, 'show', 'RAs'), (187, 'show', 'RAs'), (188, 'show', 'RAs'), (189, 'show', 'RAs'), (190, 'show', 'RAs'), (191, 'show', 'RAs'), (192, 'revealing', 'RAs'), (193, 'revealed', 'RAs'), (194, 'revealed', 'RAs'), (195, 'revealed', 'RAs'), (196, 'revealed', 'RAs'), (197, 'revealed', 'RAs'), (198, 'revealed', 'RAs'), (199, 'reveal', 'RAs'), (200, 'requires', 'RAs'), (201, 'requires', 'RAs'), (202, 'requires', 'RAs'), (203, 'report', 'RAs'), (204, 'report', 'RAs'), (205, 'reasoned', 'RAs'), (206, 'reasoned', 'RAs'), (207, 'reasoned', 'RAs'), (208, 'reasoned', 'RAs'), (209, 'rationale', 'RAs'), (210, 'observations', 'RAs'), (211, 'findings', 'RAs'), (212, 'postulated', 'RAs'), (213, 'postulate', 'RAs'), (214, 'possible', 'RAs'), (215, 'possible', 'RAs'), (216, 'possible', 'RAs'), (217, 'possible', 'RAs'), (218, 'possible', 'RAs'), (219, 'possible', 'RAs'), (220, 'possible', 'RAs'), (221, 'possible', 'RAs'), (222, 'possible', 'RAs'), (223, 'possible', 'RAs'), (224, 'possible', 'RAs'), (225, 'possible', 'RAs'), (226, 'possible', 'RAs'), (227, 'possible', 'RAs'), (228, 'possibility', 'RAs'), (229, 'possibility', 'RAs'), (230, 'possibility', 'RAs'), (231, 'possibility', 'RAs'), (232, 'possibility', 'RAs'), (233, 'possibility', 'RAs'), (234, 'possibility', 'RAs'), (235, 'possibility', 'RAs'), (236, 'explanation', 'RAs'), (237, 'possibility', 'RAs'), (238, 'One', 'RAs'), (239, 'interpretation', 'RAs'), (240, 'observed', 'RAs'), (241, 'observed', 'RAs'), (242, 'observations', 'RAs'), (243, 'observations', 'RAs'), (244, 'observation', 'RAs'), (245, 'noteworthy', 'RAs'), (246, 'noted', 'RAs'), (247, 'noted', 'RAs'), (248, 'noted', 'RAs'), (249, 'note', 'RAs'), (250, 'known', 'RAs'), (251, 'evidence', 'RAs'), (252, 'doubt', 'RAs'), (253, 'means', 'RAs'), (254, 'means', 'RAs'), (255, 'likely', 'RAs'), (256, 'likely', 'RAs'), (257, 'likely', 'RAs'), (258, 'likely', 'RAs'), (259, 'likely', 'RAs'), (260, 'likely', 'RAs'), (261, 'likely', 'RAs'), (262, 'likely', 'RAs'), (263, 'likely', 'RAs'), (264, 'possible', 'RAs'), (265, 'possible', 'RAs'), (266, 'possible', 'RAs'), (267, 'interesting', 'RAs'), (268, 'infer', 'RAs'), (269, 'inevitable', 'RAs'), (270, 'indicating', 'RAs'), (271, 'indicating', 'RAs'), (272, 'indicating', 'RAs'), (273, 'indicating', 'RAs'), (274, 'indicating', 'RAs'), (275, 'indicating', 'RAs'), (276, 'indicating', 'RAs'), (277, 'indicating', 'RAs'), (278, 'indicating', 'RAs'), (279, 'indicates', 'RAs'), (280, 'indicates', 'RAs'), (281, 'indicates', 'RAs'), (282, 'indicates', 'RAs'), (283, 'indicates', 'RAs'), (284, 'indicates', 'RAs'), (285, 'indicated', 'RAs'), (286, 'indicated', 'RAs'), (287, 'indicated', 'RAs'), (288, 'indicated', 'RAs'), (289, 'indicated', 'RAs'), (290, 'indicated', 'RAs'), (291, 'indicated', 'RAs'), (292, 'indicate', 'RAs'), (293, 'indicate', 'RAs'), (294, 'indicate', 'RAs'), (295, 'indicate', 'RAs'), (296, 'indicate', 'RAs'), (297, 'indicate', 'RAs'), (298, 'indicate', 'RAs'), (299, 'indicate', 'RAs'), (300, 'indicate', 'RAs'), (301, 'indicate', 'RAs'), (302, 'indicate', 'RAs'), (303, 'indicate', 'RAs'), (304, 'indicate', 'RAs'), (305, 'indicate', 'RAs'), (306, 'indicate', 'RAs'), (307, 'indicate', 'RAs'), (308, 'indicate', 'RAs'), (309, 'indicate', 'RAs'), (310, 'indicate', 'RAs'), (311, 'indicate', 'RAs'), (312, 'indicate', 'RAs'), (313, 'indicate', 'RAs'), (314, 'implying', 'RAs'), (315, 'imply', 'RAs'), (316, 'imply', 'RAs'), (317, 'implies', 'RAs'), (318, 'idea', 'RAs'), (319, 'idea', 'RAs'), (320, 'hypothesized', 'RAs'), (321, 'hypothesized', 'RAs'), (322, 'hypothesized', 'RAs'), (323, 'shown', 'RAs'), (324, 'given', 'RAs'), (325, 'given', 'RAs'), (326, 'given', 'RAs'), (327, 'given', 'RAs'), (328, 'evidence', 'RAs'), (329, 'found', 'RAs'), (330, 'found', 'RAs'), (331, 'found', 'RAs'), (332, 'found', 'RAs'), (333, 'found', 'RAs'), (334, 'found', 'RAs'), (335, 'found', 'RAs'), (336, 'found', 'RAs'), (337, 'found', 'RAs'), (338, 'found', 'RAs'), (339, 'found', 'RAs'), (340, 'found', 'RAs'), (341, 'found', 'RAs'), (342, 'found', 'RAs'), (343, 'found', 'RAs'), (344, 'found', 'RAs'), (345, 'found', 'RAs'), (346, 'found', 'RAs'), (347, 'found', 'RAs'), (348, 'found', 'RAs'), (349, 'found', 'RAs'), (350, 'found', 'RAs'), (351, 'finding', 'RAs'), (352, 'find', 'RAs'), (353, 'feel', 'RAs'), (354, 'fact', 'RAs'), (355, 'extent', 'RAs'), (356, 'expected', 'RAs'), (357, 'evidence', 'RAs'), (358, 'evidence', 'RAs'), (359, 'evidence', 'RAs'), (360, 'evidence', 'RAs'), (361, 'estimated', 'RAs'), (362, 'estimated', 'RAs'), (363, 'estimated', 'RAs'), (364, 'estimate', 'RAs'), (365, 'established', 'RAs'), (366, 'established', 'RAs'), (367, 'emphasize', 'RAs'), (368, 'determined', 'RAs'), (369, 'demonstration', 'RAs'), (370, 'demonstrating', 'RAs'), (371, 'demonstrates', 'RAs'), (372, 'demonstrated', 'RAs'), (373, 'demonstrated', 'RAs'), (374, 'demonstrate', 'RAs'), (375, 'demonstrate', 'RAs'), (376, 'demonstrate', 'RAs'), (377, 'demonstrate', 'RAs'), (378, 'demonstrate', 'RAs'), (379, 'demonstrate', 'RAs'), (380, 'demonstrate', 'RAs'), (381, 'demonstrate', 'RAs'), (382, 'demonstrate', 'RAs'), (383, 'argued', 'RAs'), (384, 'confirming', 'RAs'), (385, 'confirming', 'RAs'), (386, 'confirming', 'RAs'), (387, 'confirming', 'RAs'), (388, 'confirmed', 'RAs'), (389, 'confirmed', 'RAs'), (390, 'confirmed', 'RAs'), (391, 'confirmed', 'RAs'), (392, 'confirmed', 'RAs'), (393, 'confirm', 'RAs'), (394, 'confirm', 'RAs'), (395, 'conclusion', 'RAs'), (396, 'conclude', 'RAs'), (397, 'conclude', 'RAs'), (398, 'conclude', 'RAs'), (399, 'conclude', 'RAs'), (400, 'conclude', 'RAs'), (401, 'conclude', 'RAs'), (402, 'conclude', 'RAs'), (403, 'conclude', 'RAs'), (404, 'believe', 'RAs'), (405, 'believe', 'RAs'), (406, 'believe', 'RAs'), (407, 'believe', 'RAs'), (408, 'believe', 'RAs'), (409, 'appears', 'RAs'), (410, 'appeared', 'RAs'), (411, 'appeared', 'RAs'), (412, 'anticipated', 'RAs'), (413, 'acknowledged', 'RAs'), (414, 'acknowledge', 'RAs'), (415, 'accept', 'RAs'), (416, 'limitation', 'RAs'), (417, 'explanation', 'RAs'), (418, 'finding', 'RAs'), (419, 'decision', 'RAs'), (420, 'well-known', 'RAs'), (421, 'view', 'RAs'), (422, 'observation', 'RAs'), (423, 'fact', 'RAs'), (424, 'fact', 'RAs'), (425, 'reports', 'RAs'), (426, 'possibility', 'RAs'), (427, 'indication', 'RAs'), (428, 'exclude', 'RAs'), (429, 'reported', 'RAs'), (430, 'indicated', 'RAs'), (431, 'observation', 'RAs'), (432, 'observation', 'RAs'), (433, 'suggests', 'RAs'), (434, 'suggesting', 'RAs'), (435, 'suggesting', 'RAs'), (436, 'suggesting', 'RAs'), (437, 'suggesting', 'RAs'), (438, 'suggesting', 'RAs'), (439, 'suggested', 'RAs'), (440, 'suggested', 'RAs'), (441, 'suggested', 'RAs'), (442, 'suggested', 'RAs'), (443, 'suggested', 'RAs'), (444, 'suggested', 'RAs'), (445, 'suggested', 'RAs'), (446, 'suggested', 'RAs'), (447, 'suggested', 'RAs'), (448, 'suggest', 'RAs'), (449, 'suggest', 'RAs'), (450, 'suggest', 'RAs'), (451, 'suggest', 'RAs'), (452, 'shown', 'RAs'), (453, 'shown', 'RAs'), (454, 'shown', 'RAs'), (455, 'shown', 'RAs'), (456, 'shown', 'RAs'), (457, 'shown', 'RAs'), (458, 'shown', 'RAs'), (459, 'shown', 'RAs'), (460, 'shown', 'RAs'), (461, 'shown', 'RAs'), (462, 'shown', 'RAs'), (463, 'shown', 'RAs'), (464, 'shown', 'RAs'), (465, 'showing', 'RAs'), (466, 'showed', 'RAs'), (467, 'showed', 'RAs'), (468, 'showed', 'RAs'), (469, 'showed', 'RAs'), (470, 'showed', 'RAs'), (471, 'show', 'RAs'), (472, 'show', 'RAs'), (473, 'show', 'RAs'), (474, 'revealed', 'RAs'), (475, 'revealed', 'RAs'), (476, 'revealed', 'RAs'), (477, 'reported', 'RAs'), (478, 'reported', 'RAs'), (479, 'reported', 'RAs'), (480, 'reported', 'RAs'), (481, 'reported', 'RAs'), (482, 'reported', 'RAs'), (483, 'evidence', 'RAs'), (484, 'proposed', 'RAs'), (485, 'reports', 'RAs'), (486, 'observations', 'RAs'), (487, 'postulated', 'RAs'), (488, 'observations', 'RAs'), (489, 'observations', 'RAs'), (490, 'observation', 'RAs'), (491, 'notion', 'RAs'), (492, 'noted', 'RAs'), (493, 'noted', 'RAs'), (494, 'thought', 'RAs'), (495, 'increasing', 'RAs'), (496, 'indicates', 'RAs'), (497, 'indicated', 'RAs'), (498, 'indicate', 'RAs'), (499, 'indicate', 'RAs'), (500, 'evidence', 'RAs'), (501, 'hypothesized', 'RAs'), (502, 'found', 'RAs'), (503, 'found', 'RAs'), (504, 'found', 'RAs'), (505, 'found', 'RAs'), (506, 'found', 'RAs'), (507, 'found', 'RAs'), (508, 'found', 'RAs'), (509, 'found', 'RAs'), (510, 'found', 'RAs'), (511, 'found', 'RAs'), (512, 'findings', 'RAs'), (513, 'findings', 'RAs'), (514, 'findings', 'RAs'), (515, 'find', 'RAs'), (516, 'evidence', 'RAs'), (517, 'evidence', 'RAs'), (518, 'established', 'RAs'), (519, 'established', 'RAs'), (520, 'documented', 'RAs'), (521, 'demonstrated', 'RAs'), (522, 'demonstrated', 'RAs'), (523, 'demonstrated', 'RAs'), (524, 'demonstrated', 'RAs'), (525, 'demonstrated', 'RAs'), (526, 'demonstrated', 'RAs'), (527, 'demonstrated', 'RAs'), (528, 'demonstrated', 'RAs'), (529, 'demonstrated', 'RAs'), (530, 'confirmed', 'RAs'), (531, 'concluded', 'RAs'), (532, 'claimed', 'RAs'), (533, 'believed', 'RAs'), (534, 'argued', 'RAs'), (535, 'reports', 'RAs'), (536, 'prove', 'RAs'), (537, 'confirm', 'RAs'), (538, 'show', 'RAs'), (539, 'types', 'RAs'), (540, 'analysis', 'RAs'), (541, 'fact', 'RAs'), (542, 'showing', 'RAs'), (543, 'recognize', 'RAs'), (544, 'reassuring', 'RAs'), (545, 'provided', 'RAs'), (546, 'note', 'RAs'), (547, 'limitation', 'RAs'), (548, 'knowing', 'RAs'), (549, 'expected', 'RAs'), (550, 'indicating', 'RAs'), (551, 'indicates', 'RAs'), (552, 'indicated', 'RAs'), (553, 'included', 'RAs'), (554, 'given', 'RAs'), (555, 'estimated', 'RAs'), (556, 'estimated', 'RAs'), (557, 'established', 'RAs'), (558, 'ensured', 'RAs'), (559, 'ensure', 'RAs'), (560, 'ensure', 'RAs'), (561, 'ensure', 'RAs'), (562, 'effect', 'RAs'), (563, 'dependence', 'RAs'), (564, 'confirm', 'RAs'), (565, 'confirm', 'RAs'), (566, 'condition', 'RAs'), (567, 'assuming', 'RAs'), (568, 'assumed', 'RAs'), (569, 'acknowledge', 'RAs'), (570, 'method', 'RAs'), (571, 'limitation', 'RAs'), (572, 'difference', 'RAs'), (573, 'length', 'RAs'), (574, 'view', 'RAs'), (575, 'theory', 'RAs'), (576, 'notion', 'RAs'), (577, 'notion', 'RAs'), (578, 'idea', 'RAs'), (579, 'hypothesis', 'RAs'), (580, 'suggests', 'RAs'), (581, 'recognises', 'RAs'), (582, 'probability', 'RAs'), (583, 'postulated', 'RAs'), (584, 'postulated', 'RAs'), (585, 'hypothesis', 'RAs'), (586, 'hypothesis', 'RAs'), (587, 'hypothesis', 'RAs'), (588, 'account', 'RAs'), (589, 'account', 'RAs'), (590, 'theory', 'RAs'), (591, 'idea', 'RAs'), (592, 'unlikely', 'RAs'), (593, 'understand', 'RAs'), (594, 'uncovered', 'RAs'), (595, 'time', 'RAs'), (596, 'potential', 'RAs'), (597, 'possibility', 'RAs'), (598, 'finding', 'RAs'), (599, 'fact', 'RAs'), (600, 'fact', 'RAs'), (601, 'plausibility', 'RAs'), (602, 'suggests', 'RAs'), (603, 'suggests', 'RAs'), (604, 'suggests', 'RAs'), (605, 'suggests', 'RAs'), (606, 'suggests', 'RAs'), (607, 'suggesting', 'RAs'), (608, 'suggesting', 'RAs'), (609, 'suggesting', 'RAs'), (610, 'suggesting', 'RAs'), (611, 'suggesting', 'RAs'), (612, 'suggesting', 'RAs'), (613, 'suggesting', 'RAs'), (614, 'suggesting', 'RAs'), (615, 'suggesting', 'RAs'), (616, 'suggesting', 'RAs'), (617, 'suggesting', 'RAs'), (618, 'suggested', 'RAs'), (619, 'suggest', 'RAs'), (620, 'suggest', 'RAs'), (621, 'suggest', 'RAs'), (622, 'suggest', 'RAs'), (623, 'suggest', 'RAs'), (624, 'suggest', 'RAs'), (625, 'suggest', 'RAs'), (626, 'suggest', 'RAs'), (627, 'suggest', 'RAs'), (628, 'suggest', 'RAs'), (629, 'suggest', 'RAs'), (630, 'suggest', 'RAs'), (631, 'suggest', 'RAs'), (632, 'suggest', 'RAs'), (633, 'suggest', 'RAs'), (634, 'suggest', 'RAs'), (635, 'suggest', 'RAs'), (636, 'shows', 'RAs'), (637, 'shown', 'RAs'), (638, 'shown', 'RAs'), (639, 'shown', 'RAs'), (640, 'shown', 'RAs'), (641, 'showing', 'RAs'), (642, 'showing', 'RAs'), (643, 'showing', 'RAs'), (644, 'showing', 'RAs'), (645, 'showing', 'RAs'), (646, 'showing', 'RAs'), (647, 'showing', 'RAs'), (648, 'showing', 'RAs'), (649, 'showed', 'RAs'), (650, 'showed', 'RAs'), (651, 'showed', 'RAs'), (652, 'showed', 'RAs'), (653, 'showed', 'RAs'), (654, 'show', 'RAs'), (655, 'show', 'RAs'), (656, 'show', 'RAs'), (657, 'show', 'RAs'), (658, 'show', 'RAs'), (659, 'show', 'RAs'), (660, 'show', 'RAs'), (661, 'revealed', 'RAs'), (662, 'revealed', 'RAs'), (663, 'revealed', 'RAs'), (664, 'revealed', 'RAs'), (665, 'revealed', 'RAs'), (666, 'reported', 'RAs'), (667, 'possible', 'RAs'), (668, 'possible', 'RAs'), (669, 'possible', 'RAs'), (670, 'possible', 'RAs'), (671, 'possible', 'RAs'), (672, 'possible', 'RAs'), (673, 'possible', 'RAs'), (674, 'possible', 'RAs'), (675, 'observation', 'RAs'), (676, 'hypothesis', 'RAs'), (677, 'observed', 'RAs'), (678, 'observed', 'RAs'), (679, 'observed', 'RAs'), (680, 'observed', 'RAs'), (681, 'observed', 'RAs'), (682, 'observed', 'RAs'), (683, 'observed', 'RAs'), (684, 'observed', 'RAs'), (685, 'observed', 'RAs'), (686, 'observed', 'RAs'), (687, 'observed', 'RAs'), (688, 'observed', 'RAs'), (689, 'observed', 'RAs'), (690, 'observed', 'RAs'), (691, 'noted', 'RAs'), (692, 'note', 'RAs'), (693, 'note', 'RAs'), (694, 'lower', 'RAs'), (695, 'likely', 'RAs'), (696, 'indicating', 'RAs'), (697, 'indicating', 'RAs'), (698, 'indicating', 'RAs'), (699, 'indicates', 'RAs'), (700, 'indicated', 'RAs'), (701, 'indicate', 'RAs'), (702, 'indicate', 'RAs'), (703, 'indicate', 'RAs'), (704, 'indicate', 'RAs'), (705, 'illustrate', 'RAs'), (706, 'illustrate', 'RAs'), (707, 'hypothesized', 'RAs'), (708, 'higher', 'RAs'), (709, 'given', 'RAs'), (710, 'Given', 'RAs'), (711, 'found', 'RAs'), (712, 'found', 'RAs'), (713, 'found', 'RAs'), (714, 'found', 'RAs'), (715, 'found', 'RAs'), (716, 'found', 'RAs'), (717, 'found', 'RAs'), (718, 'found', 'RAs'), (719, 'found', 'RAs'), (720, 'found', 'RAs'), (721, 'found', 'RAs'), (722, 'found', 'RAs'), (723, 'found', 'RAs'), (724, 'found', 'RAs'), (725, 'found', 'RAs'), (726, 'found', 'RAs'), (727, 'found', 'RAs'), (728, 'feasible', 'RAs'), (729, 'Evidence', 'RAs'), (730, 'established', 'RAs'), (731, 'discovered', 'RAs'), (732, 'determined', 'RAs'), (733, 'demonstrating', 'RAs'), (734, 'demonstrated', 'RAs'), (735, 'demonstrated', 'RAs'), (736, 'demonstrate', 'RAs'), (737, 'demonstrate', 'RAs'), (738, 'demonstrate', 'RAs'), (739, 'demonstrate', 'RAs'), (740, 'demonstrate', 'RAs'), (741, 'demonstrate', 'RAs'), (742, 'demonstrate', 'RAs'), (743, 'confirming', 'RAs'), (744, 'confirming', 'RAs'), (745, 'confirmed', 'RAs'), (746, 'confirm', 'RAs'), (747, 'confirm', 'RAs'), (748, 'conclude', 'RAs'), (749, 'conclude', 'RAs'), (750, 'conclude', 'RAs'), (751, 'interpretation', 'RAs'), (752, 'observed', 'RAs'), (753, 'Given', 'RAs'), (754, 'given', 'RAs'), (755, 'evidence', 'RAs'), (756, 'hypothesis', 'RAs'), (757, 'notion', 'RAs'), (758, 'fact', 'RAs'), (759, 'discovery', 'RAs'), (760, 'suggests', 'RAs'), (761, 'suggests', 'RAs'), (762, 'suggests', 'RAs'), (763, 'suggested', 'RAs'), (764, 'evidence', 'RAs'), (765, 'shown', 'RAs'), (766, 'shown', 'RAs'), (767, 'shown', 'RAs'), (768, 'shown', 'RAs'), (769, 'shown', 'RAs'), (770, 'shown', 'RAs'), (771, 'shown', 'RAs'), (772, 'shown', 'RAs'), (773, 'showed', 'RAs'), (774, 'show', 'RAs'), (775, 'show', 'RAs'), (776, 'revealed', 'RAs'), (777, 'revealed', 'RAs'), (778, 'reported', 'RAs'), (779, 'reported', 'RAs'), (780, 'reported', 'RAs'), (781, 'reported', 'RAs'), (782, 'recommending', 'RAs'), (783, 'reported', 'RAs'), (784, 'indicates', 'RAs'), (785, 'indicates', 'RAs'), (786, 'indicates', 'RAs'), (787, 'indicates', 'RAs'), (788, 'indicate', 'RAs'), (789, 'hypothesis', 'RAs'), (790, 'found', 'RAs'), (791, 'demonstrated', 'RAs'), (792, 'demonstrated', 'RAs'), (793, 'confirmed', 'RAs'), (794, 'confirm', 'RAs'), (795, 'awareness', 'RAs'), (796, 'caveat', 'RAs'), (797, 'fact', 'RAs'), (798, 'show', 'RAs'), (799, 'reasoned', 'RAs'), (800, 'posit', 'RAs'), (801, 'hypothesized', 'RAs'), (802, 'hypothesized', 'RAs'), (803, 'hypothesized', 'RAs'), (804, 'hypothesized', 'RAs'), (805, 'hypothesized', 'RAs'), (806, 'hypothesized', 'RAs'), (807, 'hypothesized', 'RAs'), (808, 'envision', 'RAs'), (809, 'believe', 'RAs'), (810, 'anticipated', 'RAs'), (811, 'anticipate', 'RAs'), (812, 'ensure', 'RAs'), (813, 'possibility', 'RAs'), (814, 'suggests', 'RAs'), (815, 'suggests', 'RAs'), (816, 'shown', 'RAs'), (817, 'seems', 'RAs'), (818, 'probability', 'RAs'), (819, 'possible', 'RAs'), (820, 'noting', 'RAs'), (821, 'note', 'RAs'), (822, 'given', 'RAs'), (823, 'exclude', 'RAs'), (824, 'assumption', 'RAs'), (825, 'assumption', 'RAs'), (826, 'assumption', 'RAs'), (827, 'assumed', 'RAs'), (828, 'acknowledge', 'RAs'), (829, 'limitation', 'RAs'), (830, 'hypothesis', 'RAs'), (831, 'suggesting', 'RAs'), (832, 'possibility', 'RAs'), (833, 'hypothesis ', 'RAs'), (834, 'What', 'Theses'), (835, 'unlikely', 'Theses'), (836, 'unlikely', 'Theses'), (837, 'unlikely', 'Theses'), (838, 'speculation', 'Theses'), (839, 'result', 'Theses'), (840, 'question', 'Theses'), (841, 'problem', 'Theses'), (842, 'possibility', 'Theses'), (843, 'observations', 'Theses'), (844, 'observation', 'Theses'), (845, 'indication', 'Theses'), (846, 'evidence', 'Theses'), (847, 'evidence', 'Theses'), (848, 'findings', 'Theses'), (849, 'fact', 'Theses'), (850, 'fact', 'Theses'), (851, 'fact', 'Theses'), (852, 'fact', 'Theses'), (853, 'fact', 'Theses'), (854, 'fact', 'Theses'), (855, 'expectation', 'Theses'), (856, 'observation', 'Theses'), (857, 'discordance', 'Theses'), (858, 'observation', 'Theses'), (859, 'evidence', 'Theses'), (860, 'conclusion', 'Theses'), (861, 'surprising', 'Theses'), (862, 'surprising', 'Theses'), (863, 'surprising', 'Theses'), (864, 'surprising', 'Theses'), (865, 'suggests', 'Theses'), (866, 'suggests', 'Theses'), (867, 'suggests', 'Theses'), (868, 'suggests', 'Theses'), (869, 'suggests', 'Theses'), (870, 'suggests', 'Theses'), (871, 'suggests', 'Theses'), (872, 'suggests', 'Theses'), (873, 'suggests', 'Theses'), (874, 'suggests', 'Theses'), (875, 'suggests', 'Theses'), (876, 'suggests', 'Theses'), (877, 'suggests', 'Theses'), (878, 'suggests', 'Theses'), (879, 'suggests', 'Theses'), (880, 'suggests', 'Theses'), (881, 'suggests', 'Theses'), (882, 'suggests', 'Theses'), (883, 'suggests', 'Theses'), (884, 'suggests', 'Theses'), (885, 'suggests', 'Theses'), (886, 'suggests', 'Theses'), (887, 'suggests', 'Theses'), (888, 'suggests', 'Theses'), (889, 'suggests', 'Theses'), (890, 'suggests', 'Theses'), (891, 'suggests', 'Theses'), (892, 'suggests', 'Theses'), (893, 'suggests', 'Theses'), (894, 'suggests', 'Theses'), (895, 'suggests', 'Theses'), (896, 'suggesting', 'Theses'), (897, 'suggesting', 'Theses'), (898, 'suggesting', 'Theses'), (899, 'suggesting', 'Theses'), (900, 'suggesting', 'Theses'), (901, 'suggesting', 'Theses'), (902, 'suggesting', 'Theses'), (903, 'suggesting', 'Theses'), (904, 'suggesting', 'Theses'), (905, 'suggesting', 'Theses'), (906, 'suggesting', 'Theses'), (907, 'suggesting', 'Theses'), (908, 'suggesting', 'Theses'), (909, 'suggesting', 'Theses'), (910, 'suggesting', 'Theses'), (911, 'suggested', 'Theses'), (912, 'suggested', 'Theses'), (913, 'suggested', 'Theses'), (914, 'suggested', 'Theses'), (915, 'suggested', 'Theses'), (916, 'suggested', 'Theses'), (917, 'suggested', 'Theses'), (918, 'suggested', 'Theses'), (919, 'suggested', 'Theses'), (920, 'suggest', 'Theses'), (921, 'suggest', 'Theses'), (922, 'suggest', 'Theses'), (923, 'suggest', 'Theses'), (924, 'suggest', 'Theses'), (925, 'suggest', 'Theses'), (926, 'suggest', 'Theses'), (927, 'suggest', 'Theses'), (928, 'suggest', 'Theses'), (929, 'suggest', 'Theses'), (930, 'suggest', 'Theses'), (931, 'suggest', 'Theses'), (932, 'suggest', 'Theses'), (933, 'suggest', 'Theses'), (934, 'suggest', 'Theses'), (935, 'suggest', 'Theses'), (936, 'suggest', 'Theses'), (937, 'suggest', 'Theses'), (938, 'suggest', 'Theses'), (939, 'suggest', 'Theses'), (940, 'suggest', 'Theses'), (941, 'suggest', 'Theses'), (942, 'suggest', 'Theses'), (943, 'suggest', 'Theses'), (944, 'suggest', 'Theses'), (945, 'suggest', 'Theses'), (946, 'suggest', 'Theses'), (947, 'striking', 'Theses'), (948, 'striking', 'Theses'), (949, 'speculated', 'Theses'), (950, 'speculated', 'Theses'), (951, 'speculated', 'Theses'), (952, 'speculate', 'Theses'), (953, 'signifying', 'Theses'), (954, 'shows', 'Theses'), (955, 'shows', 'Theses'), (956, 'shows', 'Theses'), (957, 'shows', 'Theses'), (958, 'shows', 'Theses'), (959, 'shows', 'Theses'), (960, 'shown', 'Theses'), (961, 'shown', 'Theses'), (962, 'shown', 'Theses'), (963, 'shown', 'Theses'), (964, 'shown', 'Theses'), (965, 'shown', 'Theses'), (966, 'shown', 'Theses'), (967, 'shown', 'Theses'), (968, 'shown', 'Theses'), (969, 'showing', 'Theses'), (970, 'showed', 'Theses'), (971, 'showed', 'Theses'), (972, 'showed', 'Theses'), (973, 'showed', 'Theses'), (974, 'showed', 'Theses'), (975, 'showed', 'Theses'), (976, 'showed', 'Theses'), (977, 'showed', 'Theses'), (978, 'showed', 'Theses'), (979, 'showed', 'Theses'), (980, 'showed', 'Theses'), (981, 'showed', 'Theses'), (982, 'showed', 'Theses'), (983, 'showed', 'Theses'), (984, 'showed', 'Theses'), (985, 'showed', 'Theses'), (986, 'showed', 'Theses'), (987, 'showed', 'Theses'), (988, 'showed', 'Theses'), (989, 'showed', 'Theses'), (990, 'showed', 'Theses'), (991, 'showed', 'Theses'), (992, 'show', 'Theses'), (993, 'show', 'Theses'), (994, 'show', 'Theses'), (995, 'show', 'Theses'), (996, 'seem', 'Theses'), (997, 'revealed', 'Theses'), (998, 'revealed', 'Theses'), (999, 'revealed', 'Theses'), (1000, 'report', 'Theses'), (1001, 'recognized', 'Theses'), (1002, 'proposed', 'Theses'), (1003, 'predicting', 'Theses'), (1004, 'possible', 'Theses'), (1005, 'possible', 'Theses'), (1006, 'possible', 'Theses'), (1007, 'possible', 'Theses'), (1008, 'possible', 'Theses'), (1009, 'possible', 'Theses'), (1010, 'possible', 'Theses'), (1011, 'possible', 'Theses'), (1012, 'plausible', 'Theses'), (1013, 'plausible', 'Theses'), (1014, 'observation', 'Theses'), (1015, 'observed', 'Theses'), (1016, 'observed', 'Theses'), (1017, 'observed', 'Theses'), (1018, 'observed', 'Theses'), (1019, 'noting', 'Theses'), (1020, 'noticeable', 'Theses'), (1021, 'noteworthy', 'Theses'), (1022, 'noteworthy', 'Theses'), (1023, 'noted', 'Theses'), (1024, 'noted', 'Theses'), (1025, 'noted', 'Theses'), (1026, 'Note', 'Theses'), (1027, 'note', 'Theses'), (1028, 'note', 'Theses'), (1029, 'note', 'Theses'), (1030, 'note', 'Theses'), (1031, 'means', 'Theses'), (1032, 'meaning', 'Theses'), (1033, 'meaning', 'Theses'), (1034, 'meaning', 'Theses'), (1035, 'mean', 'Theses'), (1036, 'mean', 'Theses'), (1037, 'likely', 'Theses'), (1038, 'likely', 'Theses'), (1039, 'likely', 'Theses'), (1040, 'likely', 'Theses'), (1041, 'likely', 'Theses'), (1042, 'likely', 'Theses'), (1043, 'suggested', 'Theses'), (1044, 'interesting', 'Theses'), (1045, 'interesting', 'Theses'), (1046, 'indicating', 'Theses'), (1047, 'indicating', 'Theses'), (1048, 'indicating', 'Theses'), (1049, 'indicating', 'Theses'), (1050, 'indicating', 'Theses'), (1051, 'indicating', 'Theses'), (1052, 'indicating', 'Theses'), (1053, 'indicating', 'Theses'), (1054, 'indicating', 'Theses'), (1055, 'indicating', 'Theses'), (1056, 'indicating', 'Theses'), (1057, 'indicating', 'Theses'), (1058, 'indicating', 'Theses'), (1059, 'indicating', 'Theses'), (1060, 'indicating', 'Theses'), (1061, 'indicates', 'Theses'), (1062, 'indicates', 'Theses'), (1063, 'indicates', 'Theses'), (1064, 'indicates', 'Theses'), (1065, 'indicates', 'Theses'), (1066, 'indicates', 'Theses'), (1067, 'indicates', 'Theses'), (1068, 'indicates', 'Theses'), (1069, 'indicates', 'Theses'), (1070, 'indicated', 'Theses'), (1071, 'indicated', 'Theses'), (1072, 'indicated', 'Theses'), (1073, 'indicated', 'Theses'), (1074, 'indicated', 'Theses'), (1075, 'indicated', 'Theses'), (1076, 'indicated', 'Theses'), (1077, 'indicate', 'Theses'), (1078, 'indicate', 'Theses'), (1079, 'indicate', 'Theses'), (1080, 'indicate', 'Theses'), (1081, 'indicate', 'Theses'), (1082, 'indicate', 'Theses'), (1083, 'indicate', 'Theses'), (1084, 'indicate', 'Theses'), (1085, 'indicate', 'Theses'), (1086, 'implying', 'Theses'), (1087, 'imply', 'Theses'), (1088, 'Given', 'Theses'), (1089, 'Given', 'Theses'), (1090, 'Given', 'Theses'), (1091, 'Given', 'Theses'), (1092, 'Given', 'Theses'), (1093, 'given', 'Theses'), (1094, 'given', 'Theses'), (1095, 'found', 'Theses'), (1096, 'found', 'Theses'), (1097, 'found', 'Theses'), (1098, 'found', 'Theses'), (1099, 'found', 'Theses'), (1100, 'found', 'Theses'), (1101, 'found', 'Theses'), (1102, 'found', 'Theses'), (1103, 'found', 'Theses'), (1104, 'found', 'Theses'), (1105, 'found', 'Theses'), (1106, 'found', 'Theses'), (1107, 'found', 'Theses'), (1108, 'found', 'Theses'), (1109, 'found', 'Theses'), (1110, 'evidence', 'Theses'), (1111, 'established', 'Theses'), (1112, 'established', 'Theses'), (1113, 'ensure', 'Theses'), (1114, 'doubt', 'Theses'), (1115, 'discovered', 'Theses'), (1116, 'determining', 'Theses'), (1117, 'demonstrating', 'Theses'), (1118, 'demonstrating', 'Theses'), (1119, 'demonstrating', 'Theses'), (1120, 'demonstrating', 'Theses'), (1121, 'demonstrating', 'Theses'), (1122, 'demonstrates', 'Theses'), (1123, 'demonstrates', 'Theses'), (1124, 'demonstrates', 'Theses'), (1125, 'demonstrates', 'Theses'), (1126, 'demonstrates', 'Theses'), (1127, 'demonstrated', 'Theses'), (1128, 'demonstrated', 'Theses'), (1129, 'demonstrated', 'Theses'), (1130, 'demonstrated', 'Theses'), (1131, 'demonstrated', 'Theses'), (1132, 'demonstrated', 'Theses'), (1133, 'demonstrated', 'Theses'), (1134, 'demonstrated', 'Theses'), (1135, 'demonstrated', 'Theses'), (1136, 'demonstrated', 'Theses'), (1137, 'demonstrated', 'Theses'), (1138, 'demonstrated', 'Theses'), (1139, 'demonstrated', 'Theses'), (1140, 'demonstrated', 'Theses'), (1141, 'demonstrated', 'Theses'), (1142, 'demonstrated', 'Theses'), (1143, 'demonstrated', 'Theses'), (1144, 'demonstrated', 'Theses'), (1145, 'demonstrated', 'Theses'), (1146, 'demonstrated', 'Theses'), (1147, 'demonstrated', 'Theses'), (1148, 'demonstrated', 'Theses'), (1149, 'demonstrated', 'Theses'), (1150, 'demonstrated', 'Theses'), (1151, 'demonstrated', 'Theses'), (1152, 'demonstrated', 'Theses'), (1153, 'demonstrated', 'Theses'), (1154, 'demonstrated', 'Theses'), (1155, 'demonstrated', 'Theses'), (1156, 'demonstrated', 'Theses'), (1157, 'demonstrated', 'Theses'), (1158, 'demonstrated', 'Theses'), (1159, 'demonstrated', 'Theses'), (1160, 'demonstrated', 'Theses'), (1161, 'demonstrated', 'Theses'), (1162, 'demonstrated', 'Theses'), (1163, 'demonstrated', 'Theses'), (1164, 'demonstrated', 'Theses'), (1165, 'demonstrated', 'Theses'), (1166, 'demonstrated', 'Theses'), (1167, 'demonstrated', 'Theses'), (1168, 'demonstrate', 'Theses'), (1169, 'demonstrate', 'Theses'), (1170, 'demonstrate', 'Theses'), (1171, 'demonstrate', 'Theses'), (1172, 'demonstrate', 'Theses'), (1173, 'corroborated', 'Theses'), (1174, 'Considering', 'Theses'), (1175, 'Considering', 'Theses'), (1176, 'confirms', 'Theses'), (1177, 'confirms', 'Theses'), (1178, 'confirming', 'Theses'), (1179, 'confirming', 'Theses'), (1180, 'confirmed', 'Theses'), (1181, 'confirmed', 'Theses'), (1182, 'confirmed', 'Theses'), (1183, 'confirmed', 'Theses'), (1184, 'concluded', 'Theses'), (1185, 'conclude', 'Theses'), (1186, 'conclude', 'Theses'), (1187, 'concerns', 'Theses'), (1188, 'clear', 'Theses'), (1189, 'assuming', 'Theses'), (1190, 'appears', 'Theses'), (1191, 'appears', 'Theses'), (1192, 'appears', 'Theses'), (1193, 'appears', 'Theses'), (1194, 'appeared', 'Theses'), (1195, 'apparent', 'Theses'), (1196, 'observation', 'Theses'), (1197, 'agrees', 'Theses'), (1198, 'agreed', 'Theses'), (1199, 'affirming', 'Theses'), (1200, 'thought', 'Theses'), (1201, 'thought', 'Theses'), (1202, 'thought', 'Theses'), (1203, 'thought', 'Theses'), (1204, 'thought', 'Theses'), (1205, 'thought', 'Theses'), (1206, 'thought', 'Theses'), (1207, 'thought', 'Theses'), (1208, 'thought', 'Theses'), (1209, 'thought', 'Theses'), (1210, 'thickened', 'Theses'), (1211, 'findings', 'Theses'), (1212, 'fact', 'Theses'), (1213, 'fact', 'Theses'), (1214, 'fact', 'Theses'), (1215, 'fact', 'Theses'), (1216, 'demonstration', 'Theses'), (1217, 'evidence', 'Theses'), (1218, 'surprising', 'Theses'), (1219, 'surprising', 'Theses'), (1220, 'surprise', 'Theses'), (1221, 'supported', 'Theses'), (1222, 'suggests', 'Theses'), (1223, 'suggests', 'Theses'), (1224, 'suggests', 'Theses'), (1225, 'suggests', 'Theses'), (1226, 'suggests', 'Theses'), (1227, 'suggests', 'Theses'), (1228, 'suggests', 'Theses'), (1229, 'suggests', 'Theses'), (1230, 'suggests', 'Theses'), (1231, 'suggests', 'Theses'), (1232, 'suggesting', 'Theses'), (1233, 'suggesting', 'Theses'), (1234, 'suggesting', 'Theses'), (1235, 'suggesting', 'Theses'), (1236, 'suggesting', 'Theses'), (1237, 'suggesting', 'Theses'), (1238, 'suggesting', 'Theses'), (1239, 'suggested', 'Theses'), (1240, 'suggested', 'Theses'), (1241, 'suggested', 'Theses'), (1242, 'suggested', 'Theses'), (1243, 'suggested', 'Theses'), (1244, 'suggested', 'Theses'), (1245, 'suggested', 'Theses'), (1246, 'suggested', 'Theses'), (1247, 'suggested', 'Theses'), (1248, 'suggested', 'Theses'), (1249, 'suggested', 'Theses'), (1250, 'suggested', 'Theses'), (1251, 'suggested', 'Theses'), (1252, 'suggest', 'Theses'), (1253, 'suggest', 'Theses'), (1254, 'suggest', 'Theses'), (1255, 'suggest', 'Theses'), (1256, 'suggest', 'Theses'), (1257, 'suggest', 'Theses'), (1258, 'submit', 'Theses'), (1259, 'stating', 'Theses'), (1260, 'shows', 'Theses'), (1261, 'shown', 'Theses'), (1262, 'shown', 'Theses'), (1263, 'shown', 'Theses'), (1264, 'shown', 'Theses'), (1265, 'shown', 'Theses'), (1266, 'shown', 'Theses'), (1267, 'shown', 'Theses'), (1268, 'shown', 'Theses'), (1269, 'shown', 'Theses'), (1270, 'shown', 'Theses'), (1271, 'shown', 'Theses'), (1272, 'shown', 'Theses'), (1273, 'shown', 'Theses'), (1274, 'shown', 'Theses'), (1275, 'shown', 'Theses'), (1276, 'shown', 'Theses'), (1277, 'showing', 'Theses'), (1278, 'showed', 'Theses'), (1279, 'showed', 'Theses'), (1280, 'showed', 'Theses'), (1281, 'showed', 'Theses'), (1282, 'showed', 'Theses'), (1283, 'showed', 'Theses'), (1284, 'showed', 'Theses'), (1285, 'showed', 'Theses'), (1286, 'showed', 'Theses'), (1287, 'showed', 'Theses'), (1288, 'showed', 'Theses'), (1289, 'showed', 'Theses'), (1290, 'showed', 'Theses'), (1291, 'showed', 'Theses'), (1292, 'showed', 'Theses'), (1293, 'showed', 'Theses'), (1294, 'seen', 'Theses'), (1295, 'seems', 'Theses'), (1296, 'revealed', 'Theses'), (1297, 'reveal', 'Theses'), (1298, 'reported', 'Theses'), (1299, 'reported', 'Theses'), (1300, 'reported', 'Theses'), (1301, 'reported', 'Theses'), (1302, 'reported', 'Theses'), (1303, 'reported', 'Theses'), (1304, 'reported', 'Theses'), (1305, 'reported', 'Theses'), (1306, 'reported', 'Theses'), (1307, 'reported', 'Theses'), (1308, 'reported', 'Theses'), (1309, 'reported', 'Theses'), (1310, 'reported', 'Theses'), (1311, 'data', 'Theses'), (1312, 'recommended', 'Theses'), (1313, 'recognised', 'Theses'), (1314, 'recognised', 'Theses'), (1315, 'recognised', 'Theses'), (1316, 'recognised', 'Theses'), (1317, 'proposed', 'Theses'), (1318, 'propose', 'Theses'), (1319, 'propose', 'Theses'), (1320, 'projected', 'Theses'), (1321, 'postulated', 'Theses'), (1322, 'plausible', 'Theses'), (1323, 'understanding', 'Theses'), (1324, 'observed', 'Theses'), (1325, 'mentioning', 'Theses'), (1326, 'means', 'Theses'), (1327, 'likely', 'Theses'), (1328, 'likely', 'Theses'), (1329, 'likely', 'Theses'), (1330, 'likely', 'Theses'), (1331, 'likely', 'Theses'), (1332, 'known', 'Theses'), (1333, 'known', 'Theses'), (1334, 'indicating', 'Theses'), (1335, 'indicates', 'Theses'), (1336, 'indicates', 'Theses'), (1337, 'indicates', 'Theses'), (1338, 'indicated', 'Theses'), (1339, 'indicated', 'Theses'), (1340, 'indicated', 'Theses'), (1341, 'indicate', 'Theses'), (1342, 'implying', 'Theses'), (1343, 'implying', 'Theses'), (1344, 'implicating', 'Theses'), (1345, 'highlight', 'Theses'), (1346, 'shown', 'Theses'), (1347, 'shown', 'Theses'), (1348, 'shown', 'Theses'), (1349, 'Given', 'Theses'), (1350, 'found', 'Theses'), (1351, 'found', 'Theses'), (1352, 'found', 'Theses'), (1353, 'found', 'Theses'), (1354, 'found', 'Theses'), (1355, 'found', 'Theses'), (1356, 'found', 'Theses'), (1357, 'evidence', 'Theses'), (1358, 'evidence', 'Theses'), (1359, 'evidence', 'Theses'), (1360, 'evidence', 'Theses'), (1361, 'evidence', 'Theses'), (1362, 'estimated', 'Theses'), (1363, 'estimated', 'Theses'), (1364, 'estimated', 'Theses'), (1365, 'established', 'Theses'), (1366, 'documented', 'Theses'), (1367, 'documented', 'Theses'), (1368, 'discovered', 'Theses'), (1369, 'described', 'Theses'), (1370, 'demonstrated', 'Theses'), (1371, 'demonstrated', 'Theses'), (1372, 'demonstrated', 'Theses'), (1373, 'demonstrated', 'Theses'), (1374, 'demonstrated', 'Theses'), (1375, 'demonstrated', 'Theses'), (1376, 'demonstrated', 'Theses'), (1377, 'demonstrated', 'Theses'), (1378, 'demonstrated', 'Theses'), (1379, 'demonstrated', 'Theses'), (1380, 'demonstrated', 'Theses'), (1381, 'demonstrated', 'Theses'), (1382, 'demonstrated', 'Theses'), (1383, 'demonstrated', 'Theses'), (1384, 'demonstrated', 'Theses'), (1385, 'demonstrated', 'Theses'), (1386, 'demonstrated', 'Theses'), (1387, 'demonstrated', 'Theses'), (1388, 'demonstrated', 'Theses'), (1389, 'demonstrated', 'Theses'), (1390, 'demonstrated', 'Theses'), (1391, 'demonstrate', 'Theses'), (1392, 'demonstrate', 'Theses'), (1393, 'credible', 'Theses'), (1394, 'consistent', 'Theses'), (1395, 'Considering', 'Theses'), (1396, 'Considering', 'Theses'), (1397, 'considering', 'Theses'), (1398, 'considering', 'Theses'), (1399, 'confirmed', 'Theses'), (1400, 'confirmed', 'Theses'), (1401, 'concluded', 'Theses'), (1402, 'concluded', 'Theses'), (1403, 'believed', 'Theses'), (1404, 'believed', 'Theses'), (1405, 'believed', 'Theses'), (1406, 'believed', 'Theses'), (1407, 'believed', 'Theses'), (1408, 'believe', 'Theses'), (1409, 'recognition', 'Theses'), (1410, 'acknowledging', 'Theses'), (1411, 'accepted', 'Theses'), (1412, 'accepted', 'Theses'), (1413, 'range', 'Theses'), (1414, 'hope', 'Theses'), (1415, 'hoped', 'Theses'), (1416, 'hoped', 'Theses'), (1417, 'hoped', 'Theses'), (1418, 'hoped', 'Theses'), (1419, 'hoped', 'Theses'), (1420, 'hoped', 'Theses'), (1421, 'hoped', 'Theses'), (1422, 'hoped', 'Theses'), (1423, 'hoped', 'Theses'), (1424, 'hoped', 'Theses'), (1425, 'expect', 'Theses'), (1426, 'confirm', 'Theses'), (1427, 'ensure', 'Theses'), (1428, 'affirm', 'Theses'), (1429, 'rationale', 'Theses'), (1430, 'probability', 'Theses'), (1431, 'observation', 'Theses'), (1432, 'fact', 'Theses'), (1433, 'difference', 'Theses'), (1434, 'difference', 'Theses'), (1435, 'suggests', 'Theses'), (1436, 'suggests', 'Theses'), (1437, 'showed', 'Theses'), (1438, 'recognize', 'Theses'), (1439, 'probability', 'Theses'), (1440, 'application', 'Theses'), (1441, 'noteworthy', 'Theses'), (1442, 'noteworthy', 'Theses'), (1443, 'noted', 'Theses'), (1444, 'noted', 'Theses'), (1445, 'doubt', 'Theses'), (1446, 'method', 'Theses'), (1447, 'insist', 'Theses'), (1448, 'found', 'Theses'), (1449, 'ensure', 'Theses'), (1450, 'ensure', 'Theses'), (1451, 'ensure', 'Theses'), (1452, 'ensure', 'Theses'), (1453, 'ensure    ', 'Theses'), (1454, 'ensure', 'Theses'), (1455, 'demonstrated', 'Theses'), (1456, 'corroborated', 'Theses'), (1457, 'concern', 'Theses'), (1458, 'check', 'Theses'), (1459, 'assumes', 'Theses'), (1460, 'assumes', 'Theses'), (1461, 'ascertained', 'Theses'), (1462, 'reason', 'Theses'), (1463, 'unlikely', 'Theses'), (1464, 'thought', 'Theses'), (1465, 'thought', 'Theses'), (1466, 'advantage', 'Theses'), (1467, 'idea', 'Theses'), (1468, 'hypothesis', 'Theses'), (1469, 'hypothesis', 'Theses'), (1470, 'hypothesis', 'Theses'), (1471, 'hypothesis', 'Theses'), (1472, 'hypothesis', 'Theses'), (1473, 'hypothesis', 'Theses'), (1474, 'fact', 'Theses'), (1475, 'hypothesis', 'Theses'), (1476, 'suggesting', 'Theses'), (1477, 'suggest', 'Theses'), (1478, 'proposed', 'Theses'), (1479, 'presumed', 'Theses'), (1480, 'postulate', 'Theses'), (1481, 'possible', 'Theses'), (1482, 'possible', 'Theses'), (1483, 'possibility', 'Theses'), (1484, 'model', 'Theses'), (1485, 'likely', 'Theses'), (1486, 'likely', 'Theses'), (1487, 'likely', 'Theses'), (1488, 'concern', 'Theses'), (1489, 'implies', 'Theses'), (1490, 'hypothesized', 'Theses'), (1491, 'hypothesized', 'Theses'), (1492, 'hypothesize', 'Theses'), (1493, 'hypothesize', 'Theses'), (1494, 'hypothesised', 'Theses'), (1495, 'hypothesised', 'Theses'), (1496, 'Hypothesis', 'Theses'), (1497, 'hypothesis', 'Theses'), (1498, 'hypothesis', 'Theses'), (1499, 'hypothesis', 'Theses'), (1500, 'hypothesis', 'Theses'), (1501, 'hoped', 'Theses'), (1502, 'hoped', 'Theses'), (1503, 'hoped', 'Theses'), (1504, 'hoped', 'Theses'), (1505, 'expected', 'Theses'), (1506, 'expected', 'Theses'), (1507, 'expected', 'Theses'), (1508, 'demonstrating', 'Theses'), (1509, 'Assuming', 'Theses'), (1510, 'anticipated', 'Theses'), (1511, 'theory', 'Theses'), (1512, 'hypothesise', 'Theses')]
        df = pd.DataFrame.from_records(records, columns=['index', 'Text', 'Genre']).set_index('index')
        c = TermDocMatrixFromPandas(df, category_col='Genre', text_col='Text', nlp=whitespace_nlp).build()
        c.get_term_freq_df()
        c = CorpusFromPandas(df, category_col='Genre', text_col='Text', nlp=whitespace_nlp).build()
        df = c.get_term_freq_df()

def test_main(self):
    categories, documents = get_docs_categories()
    df = pd.DataFrame({'category': categories, 'text': documents})
    tdm_factory = TermDocMatrixFromPandas(df, 'category', 'text', nlp=whitespace_nlp)
    term_doc_matrix = tdm_factory.build()
    self.assertIsInstance(term_doc_matrix, TermDocMatrix)
    self.assertEqual(set(term_doc_matrix.get_categories()), set(['hamlet', 'jay-z/r. kelly']))
    self.assertEqual(term_doc_matrix.get_num_docs(), 9)
    term_doc_df = term_doc_matrix.get_term_freq_df()
    self.assertEqual(term_doc_df.loc['of'].sum(), 3)

def test_one_word_per_docs(self):
    records = [(0, 'verified', 'RAs'), (1, 'view', 'RAs'), (2, 'laminectomy', 'RAs'), (3, 'recognition', 'RAs'), (4, 'possibility', 'RAs'), (5, 'possibility', 'RAs'), (6, 'possibility', 'RAs'), (7, 'observations', 'RAs'), (8, 'observation', 'RAs'), (9, 'observation', 'RAs'), (10, 'observation', 'RAs'), (11, 'observation', 'RAs'), (12, 'observation', 'RAs'), (13, 'implication', 'RAs'), (14, 'idea', 'RAs'), (15, 'hypothesis', 'RAs'), (16, 'fact', 'RAs'), (17, 'fact', 'RAs'), (18, 'fact', 'RAs'), (19, 'fact', 'RAs'), (20, 'fact', 'RAs'), (21, 'surprising', 'RAs'), (22, 'surprising', 'RAs'), (23, 'surprising', 'RAs'), (24, 'suggests', 'RAs'), (25, 'suggests', 'RAs'), (26, 'suggests', 'RAs'), (27, 'suggests', 'RAs'), (28, 'suggests', 'RAs'), (29, 'suggests', 'RAs'), (30, 'suggests', 'RAs'), (31, 'suggests', 'RAs'), (32, 'suggests', 'RAs'), (33, 'suggests', 'RAs'), (34, 'suggests', 'RAs'), (35, 'suggests', 'RAs'), (36, 'suggests', 'RAs'), (37, 'suggests', 'RAs'), (38, 'suggests', 'RAs'), (39, 'suggests', 'RAs'), (40, 'suggests', 'RAs'), (41, 'suggests', 'RAs'), (42, 'suggests', 'RAs'), (43, 'suggests', 'RAs'), (44, 'suggests', 'RAs'), (45, 'suggests', 'RAs'), (46, 'suggests', 'RAs'), (47, 'suggests', 'RAs'), (48, 'suggesting', 'RAs'), (49, 'suggesting', 'RAs'), (50, 'suggesting', 'RAs'), (51, 'suggesting', 'RAs'), (52, 'suggesting', 'RAs'), (53, 'suggesting', 'RAs'), (54, 'suggesting', 'RAs'), (55, 'suggesting', 'RAs'), (56, 'suggesting', 'RAs'), (57, 'suggesting', 'RAs'), (58, 'suggesting', 'RAs'), (59, 'suggesting', 'RAs'), (60, 'suggesting', 'RAs'), (61, 'suggesting', 'RAs'), (62, 'suggesting', 'RAs'), (63, 'suggesting', 'RAs'), (64, 'suggesting', 'RAs'), (65, 'suggesting', 'RAs'), (66, 'suggesting', 'RAs'), (67, 'suggesting', 'RAs'), (68, 'suggesting', 'RAs'), (69, 'suggesting', 'RAs'), (70, 'suggesting', 'RAs'), (71, 'suggesting', 'RAs'), (72, 'suggesting', 'RAs'), (73, 'suggesting', 'RAs'), (74, 'suggesting', 'RAs'), (75, 'suggested', 'RAs'), (76, 'suggested', 'RAs'), (77, 'suggested', 'RAs'), (78, 'suggested', 'RAs'), (79, 'suggested', 'RAs'), (80, 'suggest', 'RAs'), (81, 'suggest', 'RAs'), (82, 'suggest', 'RAs'), (83, 'suggest', 'RAs'), (84, 'suggest', 'RAs'), (85, 'suggest', 'RAs'), (86, 'suggest', 'RAs'), (87, 'suggest', 'RAs'), (88, 'suggest', 'RAs'), (89, 'suggest', 'RAs'), (90, 'suggest', 'RAs'), (91, 'suggest', 'RAs'), (92, 'suggest', 'RAs'), (93, 'suggest', 'RAs'), (94, 'suggest', 'RAs'), (95, 'suggest', 'RAs'), (96, 'suggest', 'RAs'), (97, 'suggest', 'RAs'), (98, 'suggest', 'RAs'), (99, 'suggest', 'RAs'), (100, 'suggest', 'RAs'), (101, 'suggest', 'RAs'), (102, 'suggest', 'RAs'), (103, 'suggest', 'RAs'), (104, 'suggest', 'RAs'), (105, 'suggest', 'RAs'), (106, 'suggest', 'RAs'), (107, 'suggest', 'RAs'), (108, 'suggest', 'RAs'), (109, 'suggest', 'RAs'), (110, 'suggest', 'RAs'), (111, 'suggest', 'RAs'), (112, 'suggest', 'RAs'), (113, 'suggest', 'RAs'), (114, 'suggest', 'RAs'), (115, 'suggest', 'RAs'), (116, 'suggest', 'RAs'), (117, 'suggest', 'RAs'), (118, 'suggest', 'RAs'), (119, 'suggest', 'RAs'), (120, 'suggest', 'RAs'), (121, 'suggest', 'RAs'), (122, 'suggest', 'RAs'), (123, 'suggest', 'RAs'), (124, 'suggest', 'RAs'), (125, 'suggest', 'RAs'), (126, 'suggest', 'RAs'), (127, 'suggest', 'RAs'), (128, 'speculate', 'RAs'), (129, 'speculate', 'RAs'), (130, 'speculate', 'RAs'), (131, 'shows', 'RAs'), (132, 'shows', 'RAs'), (133, 'shows', 'RAs'), (134, 'shows', 'RAs'), (135, 'shows', 'RAs'), (136, 'shown', 'RAs'), (137, 'shown', 'RAs'), (138, 'shown', 'RAs'), (139, 'shown', 'RAs'), (140, 'showing', 'RAs'), (141, 'showing', 'RAs'), (142, 'showing', 'RAs'), (143, 'showing', 'RAs'), (144, 'showing', 'RAs'), (145, 'showing', 'RAs'), (146, 'showed', 'RAs'), (147, 'showed', 'RAs'), (148, 'showed', 'RAs'), (149, 'showed', 'RAs'), (150, 'showed', 'RAs'), (151, 'showed', 'RAs'), (152, 'showed', 'RAs'), (153, 'showed', 'RAs'), (154, 'showed', 'RAs'), (155, 'showed', 'RAs'), (156, 'showed', 'RAs'), (157, 'showed', 'RAs'), (158, 'showed', 'RAs'), (159, 'showed', 'RAs'), (160, 'showed', 'RAs'), (161, 'showed', 'RAs'), (162, 'showed', 'RAs'), (163, 'showed', 'RAs'), (164, 'showed', 'RAs'), (165, 'showed', 'RAs'), (166, 'showed', 'RAs'), (167, 'showed', 'RAs'), (168, 'showed', 'RAs'), (169, 'show', 'RAs'), (170, 'show', 'RAs'), (171, 'show', 'RAs'), (172, 'show', 'RAs'), (173, 'show', 'RAs'), (174, 'show', 'RAs'), (175, 'show', 'RAs'), (176, 'show', 'RAs'), (177, 'show', 'RAs'), (178, 'show', 'RAs'), (179, 'show', 'RAs'), (180, 'show', 'RAs'), (181, 'show', 'RAs'), (182, 'show', 'RAs'), (183, 'show', 'RAs'), (184, 'show', 'RAs'), (185, 'show', 'RAs'), (186, 'show', 'RAs'), (187, 'show', 'RAs'), (188, 'show', 'RAs'), (189, 'show', 'RAs'), (190, 'show', 'RAs'), (191, 'show', 'RAs'), (192, 'revealing', 'RAs'), (193, 'revealed', 'RAs'), (194, 'revealed', 'RAs'), (195, 'revealed', 'RAs'), (196, 'revealed', 'RAs'), (197, 'revealed', 'RAs'), (198, 'revealed', 'RAs'), (199, 'reveal', 'RAs'), (200, 'requires', 'RAs'), (201, 'requires', 'RAs'), (202, 'requires', 'RAs'), (203, 'report', 'RAs'), (204, 'report', 'RAs'), (205, 'reasoned', 'RAs'), (206, 'reasoned', 'RAs'), (207, 'reasoned', 'RAs'), (208, 'reasoned', 'RAs'), (209, 'rationale', 'RAs'), (210, 'observations', 'RAs'), (211, 'findings', 'RAs'), (212, 'postulated', 'RAs'), (213, 'postulate', 'RAs'), (214, 'possible', 'RAs'), (215, 'possible', 'RAs'), (216, 'possible', 'RAs'), (217, 'possible', 'RAs'), (218, 'possible', 'RAs'), (219, 'possible', 'RAs'), (220, 'possible', 'RAs'), (221, 'possible', 'RAs'), (222, 'possible', 'RAs'), (223, 'possible', 'RAs'), (224, 'possible', 'RAs'), (225, 'possible', 'RAs'), (226, 'possible', 'RAs'), (227, 'possible', 'RAs'), (228, 'possibility', 'RAs'), (229, 'possibility', 'RAs'), (230, 'possibility', 'RAs'), (231, 'possibility', 'RAs'), (232, 'possibility', 'RAs'), (233, 'possibility', 'RAs'), (234, 'possibility', 'RAs'), (235, 'possibility', 'RAs'), (236, 'explanation', 'RAs'), (237, 'possibility', 'RAs'), (238, 'One', 'RAs'), (239, 'interpretation', 'RAs'), (240, 'observed', 'RAs'), (241, 'observed', 'RAs'), (242, 'observations', 'RAs'), (243, 'observations', 'RAs'), (244, 'observation', 'RAs'), (245, 'noteworthy', 'RAs'), (246, 'noted', 'RAs'), (247, 'noted', 'RAs'), (248, 'noted', 'RAs'), (249, 'note', 'RAs'), (250, 'known', 'RAs'), (251, 'evidence', 'RAs'), (252, 'doubt', 'RAs'), (253, 'means', 'RAs'), (254, 'means', 'RAs'), (255, 'likely', 'RAs'), (256, 'likely', 'RAs'), (257, 'likely', 'RAs'), (258, 'likely', 'RAs'), (259, 'likely', 'RAs'), (260, 'likely', 'RAs'), (261, 'likely', 'RAs'), (262, 'likely', 'RAs'), (263, 'likely', 'RAs'), (264, 'possible', 'RAs'), (265, 'possible', 'RAs'), (266, 'possible', 'RAs'), (267, 'interesting', 'RAs'), (268, 'infer', 'RAs'), (269, 'inevitable', 'RAs'), (270, 'indicating', 'RAs'), (271, 'indicating', 'RAs'), (272, 'indicating', 'RAs'), (273, 'indicating', 'RAs'), (274, 'indicating', 'RAs'), (275, 'indicating', 'RAs'), (276, 'indicating', 'RAs'), (277, 'indicating', 'RAs'), (278, 'indicating', 'RAs'), (279, 'indicates', 'RAs'), (280, 'indicates', 'RAs'), (281, 'indicates', 'RAs'), (282, 'indicates', 'RAs'), (283, 'indicates', 'RAs'), (284, 'indicates', 'RAs'), (285, 'indicated', 'RAs'), (286, 'indicated', 'RAs'), (287, 'indicated', 'RAs'), (288, 'indicated', 'RAs'), (289, 'indicated', 'RAs'), (290, 'indicated', 'RAs'), (291, 'indicated', 'RAs'), (292, 'indicate', 'RAs'), (293, 'indicate', 'RAs'), (294, 'indicate', 'RAs'), (295, 'indicate', 'RAs'), (296, 'indicate', 'RAs'), (297, 'indicate', 'RAs'), (298, 'indicate', 'RAs'), (299, 'indicate', 'RAs'), (300, 'indicate', 'RAs'), (301, 'indicate', 'RAs'), (302, 'indicate', 'RAs'), (303, 'indicate', 'RAs'), (304, 'indicate', 'RAs'), (305, 'indicate', 'RAs'), (306, 'indicate', 'RAs'), (307, 'indicate', 'RAs'), (308, 'indicate', 'RAs'), (309, 'indicate', 'RAs'), (310, 'indicate', 'RAs'), (311, 'indicate', 'RAs'), (312, 'indicate', 'RAs'), (313, 'indicate', 'RAs'), (314, 'implying', 'RAs'), (315, 'imply', 'RAs'), (316, 'imply', 'RAs'), (317, 'implies', 'RAs'), (318, 'idea', 'RAs'), (319, 'idea', 'RAs'), (320, 'hypothesized', 'RAs'), (321, 'hypothesized', 'RAs'), (322, 'hypothesized', 'RAs'), (323, 'shown', 'RAs'), (324, 'given', 'RAs'), (325, 'given', 'RAs'), (326, 'given', 'RAs'), (327, 'given', 'RAs'), (328, 'evidence', 'RAs'), (329, 'found', 'RAs'), (330, 'found', 'RAs'), (331, 'found', 'RAs'), (332, 'found', 'RAs'), (333, 'found', 'RAs'), (334, 'found', 'RAs'), (335, 'found', 'RAs'), (336, 'found', 'RAs'), (337, 'found', 'RAs'), (338, 'found', 'RAs'), (339, 'found', 'RAs'), (340, 'found', 'RAs'), (341, 'found', 'RAs'), (342, 'found', 'RAs'), (343, 'found', 'RAs'), (344, 'found', 'RAs'), (345, 'found', 'RAs'), (346, 'found', 'RAs'), (347, 'found', 'RAs'), (348, 'found', 'RAs'), (349, 'found', 'RAs'), (350, 'found', 'RAs'), (351, 'finding', 'RAs'), (352, 'find', 'RAs'), (353, 'feel', 'RAs'), (354, 'fact', 'RAs'), (355, 'extent', 'RAs'), (356, 'expected', 'RAs'), (357, 'evidence', 'RAs'), (358, 'evidence', 'RAs'), (359, 'evidence', 'RAs'), (360, 'evidence', 'RAs'), (361, 'estimated', 'RAs'), (362, 'estimated', 'RAs'), (363, 'estimated', 'RAs'), (364, 'estimate', 'RAs'), (365, 'established', 'RAs'), (366, 'established', 'RAs'), (367, 'emphasize', 'RAs'), (368, 'determined', 'RAs'), (369, 'demonstration', 'RAs'), (370, 'demonstrating', 'RAs'), (371, 'demonstrates', 'RAs'), (372, 'demonstrated', 'RAs'), (373, 'demonstrated', 'RAs'), (374, 'demonstrate', 'RAs'), (375, 'demonstrate', 'RAs'), (376, 'demonstrate', 'RAs'), (377, 'demonstrate', 'RAs'), (378, 'demonstrate', 'RAs'), (379, 'demonstrate', 'RAs'), (380, 'demonstrate', 'RAs'), (381, 'demonstrate', 'RAs'), (382, 'demonstrate', 'RAs'), (383, 'argued', 'RAs'), (384, 'confirming', 'RAs'), (385, 'confirming', 'RAs'), (386, 'confirming', 'RAs'), (387, 'confirming', 'RAs'), (388, 'confirmed', 'RAs'), (389, 'confirmed', 'RAs'), (390, 'confirmed', 'RAs'), (391, 'confirmed', 'RAs'), (392, 'confirmed', 'RAs'), (393, 'confirm', 'RAs'), (394, 'confirm', 'RAs'), (395, 'conclusion', 'RAs'), (396, 'conclude', 'RAs'), (397, 'conclude', 'RAs'), (398, 'conclude', 'RAs'), (399, 'conclude', 'RAs'), (400, 'conclude', 'RAs'), (401, 'conclude', 'RAs'), (402, 'conclude', 'RAs'), (403, 'conclude', 'RAs'), (404, 'believe', 'RAs'), (405, 'believe', 'RAs'), (406, 'believe', 'RAs'), (407, 'believe', 'RAs'), (408, 'believe', 'RAs'), (409, 'appears', 'RAs'), (410, 'appeared', 'RAs'), (411, 'appeared', 'RAs'), (412, 'anticipated', 'RAs'), (413, 'acknowledged', 'RAs'), (414, 'acknowledge', 'RAs'), (415, 'accept', 'RAs'), (416, 'limitation', 'RAs'), (417, 'explanation', 'RAs'), (418, 'finding', 'RAs'), (419, 'decision', 'RAs'), (420, 'well-known', 'RAs'), (421, 'view', 'RAs'), (422, 'observation', 'RAs'), (423, 'fact', 'RAs'), (424, 'fact', 'RAs'), (425, 'reports', 'RAs'), (426, 'possibility', 'RAs'), (427, 'indication', 'RAs'), (428, 'exclude', 'RAs'), (429, 'reported', 'RAs'), (430, 'indicated', 'RAs'), (431, 'observation', 'RAs'), (432, 'observation', 'RAs'), (433, 'suggests', 'RAs'), (434, 'suggesting', 'RAs'), (435, 'suggesting', 'RAs'), (436, 'suggesting', 'RAs'), (437, 'suggesting', 'RAs'), (438, 'suggesting', 'RAs'), (439, 'suggested', 'RAs'), (440, 'suggested', 'RAs'), (441, 'suggested', 'RAs'), (442, 'suggested', 'RAs'), (443, 'suggested', 'RAs'), (444, 'suggested', 'RAs'), (445, 'suggested', 'RAs'), (446, 'suggested', 'RAs'), (447, 'suggested', 'RAs'), (448, 'suggest', 'RAs'), (449, 'suggest', 'RAs'), (450, 'suggest', 'RAs'), (451, 'suggest', 'RAs'), (452, 'shown', 'RAs'), (453, 'shown', 'RAs'), (454, 'shown', 'RAs'), (455, 'shown', 'RAs'), (456, 'shown', 'RAs'), (457, 'shown', 'RAs'), (458, 'shown', 'RAs'), (459, 'shown', 'RAs'), (460, 'shown', 'RAs'), (461, 'shown', 'RAs'), (462, 'shown', 'RAs'), (463, 'shown', 'RAs'), (464, 'shown', 'RAs'), (465, 'showing', 'RAs'), (466, 'showed', 'RAs'), (467, 'showed', 'RAs'), (468, 'showed', 'RAs'), (469, 'showed', 'RAs'), (470, 'showed', 'RAs'), (471, 'show', 'RAs'), (472, 'show', 'RAs'), (473, 'show', 'RAs'), (474, 'revealed', 'RAs'), (475, 'revealed', 'RAs'), (476, 'revealed', 'RAs'), (477, 'reported', 'RAs'), (478, 'reported', 'RAs'), (479, 'reported', 'RAs'), (480, 'reported', 'RAs'), (481, 'reported', 'RAs'), (482, 'reported', 'RAs'), (483, 'evidence', 'RAs'), (484, 'proposed', 'RAs'), (485, 'reports', 'RAs'), (486, 'observations', 'RAs'), (487, 'postulated', 'RAs'), (488, 'observations', 'RAs'), (489, 'observations', 'RAs'), (490, 'observation', 'RAs'), (491, 'notion', 'RAs'), (492, 'noted', 'RAs'), (493, 'noted', 'RAs'), (494, 'thought', 'RAs'), (495, 'increasing', 'RAs'), (496, 'indicates', 'RAs'), (497, 'indicated', 'RAs'), (498, 'indicate', 'RAs'), (499, 'indicate', 'RAs'), (500, 'evidence', 'RAs'), (501, 'hypothesized', 'RAs'), (502, 'found', 'RAs'), (503, 'found', 'RAs'), (504, 'found', 'RAs'), (505, 'found', 'RAs'), (506, 'found', 'RAs'), (507, 'found', 'RAs'), (508, 'found', 'RAs'), (509, 'found', 'RAs'), (510, 'found', 'RAs'), (511, 'found', 'RAs'), (512, 'findings', 'RAs'), (513, 'findings', 'RAs'), (514, 'findings', 'RAs'), (515, 'find', 'RAs'), (516, 'evidence', 'RAs'), (517, 'evidence', 'RAs'), (518, 'established', 'RAs'), (519, 'established', 'RAs'), (520, 'documented', 'RAs'), (521, 'demonstrated', 'RAs'), (522, 'demonstrated', 'RAs'), (523, 'demonstrated', 'RAs'), (524, 'demonstrated', 'RAs'), (525, 'demonstrated', 'RAs'), (526, 'demonstrated', 'RAs'), (527, 'demonstrated', 'RAs'), (528, 'demonstrated', 'RAs'), (529, 'demonstrated', 'RAs'), (530, 'confirmed', 'RAs'), (531, 'concluded', 'RAs'), (532, 'claimed', 'RAs'), (533, 'believed', 'RAs'), (534, 'argued', 'RAs'), (535, 'reports', 'RAs'), (536, 'prove', 'RAs'), (537, 'confirm', 'RAs'), (538, 'show', 'RAs'), (539, 'types', 'RAs'), (540, 'analysis', 'RAs'), (541, 'fact', 'RAs'), (542, 'showing', 'RAs'), (543, 'recognize', 'RAs'), (544, 'reassuring', 'RAs'), (545, 'provided', 'RAs'), (546, 'note', 'RAs'), (547, 'limitation', 'RAs'), (548, 'knowing', 'RAs'), (549, 'expected', 'RAs'), (550, 'indicating', 'RAs'), (551, 'indicates', 'RAs'), (552, 'indicated', 'RAs'), (553, 'included', 'RAs'), (554, 'given', 'RAs'), (555, 'estimated', 'RAs'), (556, 'estimated', 'RAs'), (557, 'established', 'RAs'), (558, 'ensured', 'RAs'), (559, 'ensure', 'RAs'), (560, 'ensure', 'RAs'), (561, 'ensure', 'RAs'), (562, 'effect', 'RAs'), (563, 'dependence', 'RAs'), (564, 'confirm', 'RAs'), (565, 'confirm', 'RAs'), (566, 'condition', 'RAs'), (567, 'assuming', 'RAs'), (568, 'assumed', 'RAs'), (569, 'acknowledge', 'RAs'), (570, 'method', 'RAs'), (571, 'limitation', 'RAs'), (572, 'difference', 'RAs'), (573, 'length', 'RAs'), (574, 'view', 'RAs'), (575, 'theory', 'RAs'), (576, 'notion', 'RAs'), (577, 'notion', 'RAs'), (578, 'idea', 'RAs'), (579, 'hypothesis', 'RAs'), (580, 'suggests', 'RAs'), (581, 'recognises', 'RAs'), (582, 'probability', 'RAs'), (583, 'postulated', 'RAs'), (584, 'postulated', 'RAs'), (585, 'hypothesis', 'RAs'), (586, 'hypothesis', 'RAs'), (587, 'hypothesis', 'RAs'), (588, 'account', 'RAs'), (589, 'account', 'RAs'), (590, 'theory', 'RAs'), (591, 'idea', 'RAs'), (592, 'unlikely', 'RAs'), (593, 'understand', 'RAs'), (594, 'uncovered', 'RAs'), (595, 'time', 'RAs'), (596, 'potential', 'RAs'), (597, 'possibility', 'RAs'), (598, 'finding', 'RAs'), (599, 'fact', 'RAs'), (600, 'fact', 'RAs'), (601, 'plausibility', 'RAs'), (602, 'suggests', 'RAs'), (603, 'suggests', 'RAs'), (604, 'suggests', 'RAs'), (605, 'suggests', 'RAs'), (606, 'suggests', 'RAs'), (607, 'suggesting', 'RAs'), (608, 'suggesting', 'RAs'), (609, 'suggesting', 'RAs'), (610, 'suggesting', 'RAs'), (611, 'suggesting', 'RAs'), (612, 'suggesting', 'RAs'), (613, 'suggesting', 'RAs'), (614, 'suggesting', 'RAs'), (615, 'suggesting', 'RAs'), (616, 'suggesting', 'RAs'), (617, 'suggesting', 'RAs'), (618, 'suggested', 'RAs'), (619, 'suggest', 'RAs'), (620, 'suggest', 'RAs'), (621, 'suggest', 'RAs'), (622, 'suggest', 'RAs'), (623, 'suggest', 'RAs'), (624, 'suggest', 'RAs'), (625, 'suggest', 'RAs'), (626, 'suggest', 'RAs'), (627, 'suggest', 'RAs'), (628, 'suggest', 'RAs'), (629, 'suggest', 'RAs'), (630, 'suggest', 'RAs'), (631, 'suggest', 'RAs'), (632, 'suggest', 'RAs'), (633, 'suggest', 'RAs'), (634, 'suggest', 'RAs'), (635, 'suggest', 'RAs'), (636, 'shows', 'RAs'), (637, 'shown', 'RAs'), (638, 'shown', 'RAs'), (639, 'shown', 'RAs'), (640, 'shown', 'RAs'), (641, 'showing', 'RAs'), (642, 'showing', 'RAs'), (643, 'showing', 'RAs'), (644, 'showing', 'RAs'), (645, 'showing', 'RAs'), (646, 'showing', 'RAs'), (647, 'showing', 'RAs'), (648, 'showing', 'RAs'), (649, 'showed', 'RAs'), (650, 'showed', 'RAs'), (651, 'showed', 'RAs'), (652, 'showed', 'RAs'), (653, 'showed', 'RAs'), (654, 'show', 'RAs'), (655, 'show', 'RAs'), (656, 'show', 'RAs'), (657, 'show', 'RAs'), (658, 'show', 'RAs'), (659, 'show', 'RAs'), (660, 'show', 'RAs'), (661, 'revealed', 'RAs'), (662, 'revealed', 'RAs'), (663, 'revealed', 'RAs'), (664, 'revealed', 'RAs'), (665, 'revealed', 'RAs'), (666, 'reported', 'RAs'), (667, 'possible', 'RAs'), (668, 'possible', 'RAs'), (669, 'possible', 'RAs'), (670, 'possible', 'RAs'), (671, 'possible', 'RAs'), (672, 'possible', 'RAs'), (673, 'possible', 'RAs'), (674, 'possible', 'RAs'), (675, 'observation', 'RAs'), (676, 'hypothesis', 'RAs'), (677, 'observed', 'RAs'), (678, 'observed', 'RAs'), (679, 'observed', 'RAs'), (680, 'observed', 'RAs'), (681, 'observed', 'RAs'), (682, 'observed', 'RAs'), (683, 'observed', 'RAs'), (684, 'observed', 'RAs'), (685, 'observed', 'RAs'), (686, 'observed', 'RAs'), (687, 'observed', 'RAs'), (688, 'observed', 'RAs'), (689, 'observed', 'RAs'), (690, 'observed', 'RAs'), (691, 'noted', 'RAs'), (692, 'note', 'RAs'), (693, 'note', 'RAs'), (694, 'lower', 'RAs'), (695, 'likely', 'RAs'), (696, 'indicating', 'RAs'), (697, 'indicating', 'RAs'), (698, 'indicating', 'RAs'), (699, 'indicates', 'RAs'), (700, 'indicated', 'RAs'), (701, 'indicate', 'RAs'), (702, 'indicate', 'RAs'), (703, 'indicate', 'RAs'), (704, 'indicate', 'RAs'), (705, 'illustrate', 'RAs'), (706, 'illustrate', 'RAs'), (707, 'hypothesized', 'RAs'), (708, 'higher', 'RAs'), (709, 'given', 'RAs'), (710, 'Given', 'RAs'), (711, 'found', 'RAs'), (712, 'found', 'RAs'), (713, 'found', 'RAs'), (714, 'found', 'RAs'), (715, 'found', 'RAs'), (716, 'found', 'RAs'), (717, 'found', 'RAs'), (718, 'found', 'RAs'), (719, 'found', 'RAs'), (720, 'found', 'RAs'), (721, 'found', 'RAs'), (722, 'found', 'RAs'), (723, 'found', 'RAs'), (724, 'found', 'RAs'), (725, 'found', 'RAs'), (726, 'found', 'RAs'), (727, 'found', 'RAs'), (728, 'feasible', 'RAs'), (729, 'Evidence', 'RAs'), (730, 'established', 'RAs'), (731, 'discovered', 'RAs'), (732, 'determined', 'RAs'), (733, 'demonstrating', 'RAs'), (734, 'demonstrated', 'RAs'), (735, 'demonstrated', 'RAs'), (736, 'demonstrate', 'RAs'), (737, 'demonstrate', 'RAs'), (738, 'demonstrate', 'RAs'), (739, 'demonstrate', 'RAs'), (740, 'demonstrate', 'RAs'), (741, 'demonstrate', 'RAs'), (742, 'demonstrate', 'RAs'), (743, 'confirming', 'RAs'), (744, 'confirming', 'RAs'), (745, 'confirmed', 'RAs'), (746, 'confirm', 'RAs'), (747, 'confirm', 'RAs'), (748, 'conclude', 'RAs'), (749, 'conclude', 'RAs'), (750, 'conclude', 'RAs'), (751, 'interpretation', 'RAs'), (752, 'observed', 'RAs'), (753, 'Given', 'RAs'), (754, 'given', 'RAs'), (755, 'evidence', 'RAs'), (756, 'hypothesis', 'RAs'), (757, 'notion', 'RAs'), (758, 'fact', 'RAs'), (759, 'discovery', 'RAs'), (760, 'suggests', 'RAs'), (761, 'suggests', 'RAs'), (762, 'suggests', 'RAs'), (763, 'suggested', 'RAs'), (764, 'evidence', 'RAs'), (765, 'shown', 'RAs'), (766, 'shown', 'RAs'), (767, 'shown', 'RAs'), (768, 'shown', 'RAs'), (769, 'shown', 'RAs'), (770, 'shown', 'RAs'), (771, 'shown', 'RAs'), (772, 'shown', 'RAs'), (773, 'showed', 'RAs'), (774, 'show', 'RAs'), (775, 'show', 'RAs'), (776, 'revealed', 'RAs'), (777, 'revealed', 'RAs'), (778, 'reported', 'RAs'), (779, 'reported', 'RAs'), (780, 'reported', 'RAs'), (781, 'reported', 'RAs'), (782, 'recommending', 'RAs'), (783, 'reported', 'RAs'), (784, 'indicates', 'RAs'), (785, 'indicates', 'RAs'), (786, 'indicates', 'RAs'), (787, 'indicates', 'RAs'), (788, 'indicate', 'RAs'), (789, 'hypothesis', 'RAs'), (790, 'found', 'RAs'), (791, 'demonstrated', 'RAs'), (792, 'demonstrated', 'RAs'), (793, 'confirmed', 'RAs'), (794, 'confirm', 'RAs'), (795, 'awareness', 'RAs'), (796, 'caveat', 'RAs'), (797, 'fact', 'RAs'), (798, 'show', 'RAs'), (799, 'reasoned', 'RAs'), (800, 'posit', 'RAs'), (801, 'hypothesized', 'RAs'), (802, 'hypothesized', 'RAs'), (803, 'hypothesized', 'RAs'), (804, 'hypothesized', 'RAs'), (805, 'hypothesized', 'RAs'), (806, 'hypothesized', 'RAs'), (807, 'hypothesized', 'RAs'), (808, 'envision', 'RAs'), (809, 'believe', 'RAs'), (810, 'anticipated', 'RAs'), (811, 'anticipate', 'RAs'), (812, 'ensure', 'RAs'), (813, 'possibility', 'RAs'), (814, 'suggests', 'RAs'), (815, 'suggests', 'RAs'), (816, 'shown', 'RAs'), (817, 'seems', 'RAs'), (818, 'probability', 'RAs'), (819, 'possible', 'RAs'), (820, 'noting', 'RAs'), (821, 'note', 'RAs'), (822, 'given', 'RAs'), (823, 'exclude', 'RAs'), (824, 'assumption', 'RAs'), (825, 'assumption', 'RAs'), (826, 'assumption', 'RAs'), (827, 'assumed', 'RAs'), (828, 'acknowledge', 'RAs'), (829, 'limitation', 'RAs'), (830, 'hypothesis', 'RAs'), (831, 'suggesting', 'RAs'), (832, 'possibility', 'RAs'), (833, 'hypothesis ', 'RAs'), (834, 'What', 'Theses'), (835, 'unlikely', 'Theses'), (836, 'unlikely', 'Theses'), (837, 'unlikely', 'Theses'), (838, 'speculation', 'Theses'), (839, 'result', 'Theses'), (840, 'question', 'Theses'), (841, 'problem', 'Theses'), (842, 'possibility', 'Theses'), (843, 'observations', 'Theses'), (844, 'observation', 'Theses'), (845, 'indication', 'Theses'), (846, 'evidence', 'Theses'), (847, 'evidence', 'Theses'), (848, 'findings', 'Theses'), (849, 'fact', 'Theses'), (850, 'fact', 'Theses'), (851, 'fact', 'Theses'), (852, 'fact', 'Theses'), (853, 'fact', 'Theses'), (854, 'fact', 'Theses'), (855, 'expectation', 'Theses'), (856, 'observation', 'Theses'), (857, 'discordance', 'Theses'), (858, 'observation', 'Theses'), (859, 'evidence', 'Theses'), (860, 'conclusion', 'Theses'), (861, 'surprising', 'Theses'), (862, 'surprising', 'Theses'), (863, 'surprising', 'Theses'), (864, 'surprising', 'Theses'), (865, 'suggests', 'Theses'), (866, 'suggests', 'Theses'), (867, 'suggests', 'Theses'), (868, 'suggests', 'Theses'), (869, 'suggests', 'Theses'), (870, 'suggests', 'Theses'), (871, 'suggests', 'Theses'), (872, 'suggests', 'Theses'), (873, 'suggests', 'Theses'), (874, 'suggests', 'Theses'), (875, 'suggests', 'Theses'), (876, 'suggests', 'Theses'), (877, 'suggests', 'Theses'), (878, 'suggests', 'Theses'), (879, 'suggests', 'Theses'), (880, 'suggests', 'Theses'), (881, 'suggests', 'Theses'), (882, 'suggests', 'Theses'), (883, 'suggests', 'Theses'), (884, 'suggests', 'Theses'), (885, 'suggests', 'Theses'), (886, 'suggests', 'Theses'), (887, 'suggests', 'Theses'), (888, 'suggests', 'Theses'), (889, 'suggests', 'Theses'), (890, 'suggests', 'Theses'), (891, 'suggests', 'Theses'), (892, 'suggests', 'Theses'), (893, 'suggests', 'Theses'), (894, 'suggests', 'Theses'), (895, 'suggests', 'Theses'), (896, 'suggesting', 'Theses'), (897, 'suggesting', 'Theses'), (898, 'suggesting', 'Theses'), (899, 'suggesting', 'Theses'), (900, 'suggesting', 'Theses'), (901, 'suggesting', 'Theses'), (902, 'suggesting', 'Theses'), (903, 'suggesting', 'Theses'), (904, 'suggesting', 'Theses'), (905, 'suggesting', 'Theses'), (906, 'suggesting', 'Theses'), (907, 'suggesting', 'Theses'), (908, 'suggesting', 'Theses'), (909, 'suggesting', 'Theses'), (910, 'suggesting', 'Theses'), (911, 'suggested', 'Theses'), (912, 'suggested', 'Theses'), (913, 'suggested', 'Theses'), (914, 'suggested', 'Theses'), (915, 'suggested', 'Theses'), (916, 'suggested', 'Theses'), (917, 'suggested', 'Theses'), (918, 'suggested', 'Theses'), (919, 'suggested', 'Theses'), (920, 'suggest', 'Theses'), (921, 'suggest', 'Theses'), (922, 'suggest', 'Theses'), (923, 'suggest', 'Theses'), (924, 'suggest', 'Theses'), (925, 'suggest', 'Theses'), (926, 'suggest', 'Theses'), (927, 'suggest', 'Theses'), (928, 'suggest', 'Theses'), (929, 'suggest', 'Theses'), (930, 'suggest', 'Theses'), (931, 'suggest', 'Theses'), (932, 'suggest', 'Theses'), (933, 'suggest', 'Theses'), (934, 'suggest', 'Theses'), (935, 'suggest', 'Theses'), (936, 'suggest', 'Theses'), (937, 'suggest', 'Theses'), (938, 'suggest', 'Theses'), (939, 'suggest', 'Theses'), (940, 'suggest', 'Theses'), (941, 'suggest', 'Theses'), (942, 'suggest', 'Theses'), (943, 'suggest', 'Theses'), (944, 'suggest', 'Theses'), (945, 'suggest', 'Theses'), (946, 'suggest', 'Theses'), (947, 'striking', 'Theses'), (948, 'striking', 'Theses'), (949, 'speculated', 'Theses'), (950, 'speculated', 'Theses'), (951, 'speculated', 'Theses'), (952, 'speculate', 'Theses'), (953, 'signifying', 'Theses'), (954, 'shows', 'Theses'), (955, 'shows', 'Theses'), (956, 'shows', 'Theses'), (957, 'shows', 'Theses'), (958, 'shows', 'Theses'), (959, 'shows', 'Theses'), (960, 'shown', 'Theses'), (961, 'shown', 'Theses'), (962, 'shown', 'Theses'), (963, 'shown', 'Theses'), (964, 'shown', 'Theses'), (965, 'shown', 'Theses'), (966, 'shown', 'Theses'), (967, 'shown', 'Theses'), (968, 'shown', 'Theses'), (969, 'showing', 'Theses'), (970, 'showed', 'Theses'), (971, 'showed', 'Theses'), (972, 'showed', 'Theses'), (973, 'showed', 'Theses'), (974, 'showed', 'Theses'), (975, 'showed', 'Theses'), (976, 'showed', 'Theses'), (977, 'showed', 'Theses'), (978, 'showed', 'Theses'), (979, 'showed', 'Theses'), (980, 'showed', 'Theses'), (981, 'showed', 'Theses'), (982, 'showed', 'Theses'), (983, 'showed', 'Theses'), (984, 'showed', 'Theses'), (985, 'showed', 'Theses'), (986, 'showed', 'Theses'), (987, 'showed', 'Theses'), (988, 'showed', 'Theses'), (989, 'showed', 'Theses'), (990, 'showed', 'Theses'), (991, 'showed', 'Theses'), (992, 'show', 'Theses'), (993, 'show', 'Theses'), (994, 'show', 'Theses'), (995, 'show', 'Theses'), (996, 'seem', 'Theses'), (997, 'revealed', 'Theses'), (998, 'revealed', 'Theses'), (999, 'revealed', 'Theses'), (1000, 'report', 'Theses'), (1001, 'recognized', 'Theses'), (1002, 'proposed', 'Theses'), (1003, 'predicting', 'Theses'), (1004, 'possible', 'Theses'), (1005, 'possible', 'Theses'), (1006, 'possible', 'Theses'), (1007, 'possible', 'Theses'), (1008, 'possible', 'Theses'), (1009, 'possible', 'Theses'), (1010, 'possible', 'Theses'), (1011, 'possible', 'Theses'), (1012, 'plausible', 'Theses'), (1013, 'plausible', 'Theses'), (1014, 'observation', 'Theses'), (1015, 'observed', 'Theses'), (1016, 'observed', 'Theses'), (1017, 'observed', 'Theses'), (1018, 'observed', 'Theses'), (1019, 'noting', 'Theses'), (1020, 'noticeable', 'Theses'), (1021, 'noteworthy', 'Theses'), (1022, 'noteworthy', 'Theses'), (1023, 'noted', 'Theses'), (1024, 'noted', 'Theses'), (1025, 'noted', 'Theses'), (1026, 'Note', 'Theses'), (1027, 'note', 'Theses'), (1028, 'note', 'Theses'), (1029, 'note', 'Theses'), (1030, 'note', 'Theses'), (1031, 'means', 'Theses'), (1032, 'meaning', 'Theses'), (1033, 'meaning', 'Theses'), (1034, 'meaning', 'Theses'), (1035, 'mean', 'Theses'), (1036, 'mean', 'Theses'), (1037, 'likely', 'Theses'), (1038, 'likely', 'Theses'), (1039, 'likely', 'Theses'), (1040, 'likely', 'Theses'), (1041, 'likely', 'Theses'), (1042, 'likely', 'Theses'), (1043, 'suggested', 'Theses'), (1044, 'interesting', 'Theses'), (1045, 'interesting', 'Theses'), (1046, 'indicating', 'Theses'), (1047, 'indicating', 'Theses'), (1048, 'indicating', 'Theses'), (1049, 'indicating', 'Theses'), (1050, 'indicating', 'Theses'), (1051, 'indicating', 'Theses'), (1052, 'indicating', 'Theses'), (1053, 'indicating', 'Theses'), (1054, 'indicating', 'Theses'), (1055, 'indicating', 'Theses'), (1056, 'indicating', 'Theses'), (1057, 'indicating', 'Theses'), (1058, 'indicating', 'Theses'), (1059, 'indicating', 'Theses'), (1060, 'indicating', 'Theses'), (1061, 'indicates', 'Theses'), (1062, 'indicates', 'Theses'), (1063, 'indicates', 'Theses'), (1064, 'indicates', 'Theses'), (1065, 'indicates', 'Theses'), (1066, 'indicates', 'Theses'), (1067, 'indicates', 'Theses'), (1068, 'indicates', 'Theses'), (1069, 'indicates', 'Theses'), (1070, 'indicated', 'Theses'), (1071, 'indicated', 'Theses'), (1072, 'indicated', 'Theses'), (1073, 'indicated', 'Theses'), (1074, 'indicated', 'Theses'), (1075, 'indicated', 'Theses'), (1076, 'indicated', 'Theses'), (1077, 'indicate', 'Theses'), (1078, 'indicate', 'Theses'), (1079, 'indicate', 'Theses'), (1080, 'indicate', 'Theses'), (1081, 'indicate', 'Theses'), (1082, 'indicate', 'Theses'), (1083, 'indicate', 'Theses'), (1084, 'indicate', 'Theses'), (1085, 'indicate', 'Theses'), (1086, 'implying', 'Theses'), (1087, 'imply', 'Theses'), (1088, 'Given', 'Theses'), (1089, 'Given', 'Theses'), (1090, 'Given', 'Theses'), (1091, 'Given', 'Theses'), (1092, 'Given', 'Theses'), (1093, 'given', 'Theses'), (1094, 'given', 'Theses'), (1095, 'found', 'Theses'), (1096, 'found', 'Theses'), (1097, 'found', 'Theses'), (1098, 'found', 'Theses'), (1099, 'found', 'Theses'), (1100, 'found', 'Theses'), (1101, 'found', 'Theses'), (1102, 'found', 'Theses'), (1103, 'found', 'Theses'), (1104, 'found', 'Theses'), (1105, 'found', 'Theses'), (1106, 'found', 'Theses'), (1107, 'found', 'Theses'), (1108, 'found', 'Theses'), (1109, 'found', 'Theses'), (1110, 'evidence', 'Theses'), (1111, 'established', 'Theses'), (1112, 'established', 'Theses'), (1113, 'ensure', 'Theses'), (1114, 'doubt', 'Theses'), (1115, 'discovered', 'Theses'), (1116, 'determining', 'Theses'), (1117, 'demonstrating', 'Theses'), (1118, 'demonstrating', 'Theses'), (1119, 'demonstrating', 'Theses'), (1120, 'demonstrating', 'Theses'), (1121, 'demonstrating', 'Theses'), (1122, 'demonstrates', 'Theses'), (1123, 'demonstrates', 'Theses'), (1124, 'demonstrates', 'Theses'), (1125, 'demonstrates', 'Theses'), (1126, 'demonstrates', 'Theses'), (1127, 'demonstrated', 'Theses'), (1128, 'demonstrated', 'Theses'), (1129, 'demonstrated', 'Theses'), (1130, 'demonstrated', 'Theses'), (1131, 'demonstrated', 'Theses'), (1132, 'demonstrated', 'Theses'), (1133, 'demonstrated', 'Theses'), (1134, 'demonstrated', 'Theses'), (1135, 'demonstrated', 'Theses'), (1136, 'demonstrated', 'Theses'), (1137, 'demonstrated', 'Theses'), (1138, 'demonstrated', 'Theses'), (1139, 'demonstrated', 'Theses'), (1140, 'demonstrated', 'Theses'), (1141, 'demonstrated', 'Theses'), (1142, 'demonstrated', 'Theses'), (1143, 'demonstrated', 'Theses'), (1144, 'demonstrated', 'Theses'), (1145, 'demonstrated', 'Theses'), (1146, 'demonstrated', 'Theses'), (1147, 'demonstrated', 'Theses'), (1148, 'demonstrated', 'Theses'), (1149, 'demonstrated', 'Theses'), (1150, 'demonstrated', 'Theses'), (1151, 'demonstrated', 'Theses'), (1152, 'demonstrated', 'Theses'), (1153, 'demonstrated', 'Theses'), (1154, 'demonstrated', 'Theses'), (1155, 'demonstrated', 'Theses'), (1156, 'demonstrated', 'Theses'), (1157, 'demonstrated', 'Theses'), (1158, 'demonstrated', 'Theses'), (1159, 'demonstrated', 'Theses'), (1160, 'demonstrated', 'Theses'), (1161, 'demonstrated', 'Theses'), (1162, 'demonstrated', 'Theses'), (1163, 'demonstrated', 'Theses'), (1164, 'demonstrated', 'Theses'), (1165, 'demonstrated', 'Theses'), (1166, 'demonstrated', 'Theses'), (1167, 'demonstrated', 'Theses'), (1168, 'demonstrate', 'Theses'), (1169, 'demonstrate', 'Theses'), (1170, 'demonstrate', 'Theses'), (1171, 'demonstrate', 'Theses'), (1172, 'demonstrate', 'Theses'), (1173, 'corroborated', 'Theses'), (1174, 'Considering', 'Theses'), (1175, 'Considering', 'Theses'), (1176, 'confirms', 'Theses'), (1177, 'confirms', 'Theses'), (1178, 'confirming', 'Theses'), (1179, 'confirming', 'Theses'), (1180, 'confirmed', 'Theses'), (1181, 'confirmed', 'Theses'), (1182, 'confirmed', 'Theses'), (1183, 'confirmed', 'Theses'), (1184, 'concluded', 'Theses'), (1185, 'conclude', 'Theses'), (1186, 'conclude', 'Theses'), (1187, 'concerns', 'Theses'), (1188, 'clear', 'Theses'), (1189, 'assuming', 'Theses'), (1190, 'appears', 'Theses'), (1191, 'appears', 'Theses'), (1192, 'appears', 'Theses'), (1193, 'appears', 'Theses'), (1194, 'appeared', 'Theses'), (1195, 'apparent', 'Theses'), (1196, 'observation', 'Theses'), (1197, 'agrees', 'Theses'), (1198, 'agreed', 'Theses'), (1199, 'affirming', 'Theses'), (1200, 'thought', 'Theses'), (1201, 'thought', 'Theses'), (1202, 'thought', 'Theses'), (1203, 'thought', 'Theses'), (1204, 'thought', 'Theses'), (1205, 'thought', 'Theses'), (1206, 'thought', 'Theses'), (1207, 'thought', 'Theses'), (1208, 'thought', 'Theses'), (1209, 'thought', 'Theses'), (1210, 'thickened', 'Theses'), (1211, 'findings', 'Theses'), (1212, 'fact', 'Theses'), (1213, 'fact', 'Theses'), (1214, 'fact', 'Theses'), (1215, 'fact', 'Theses'), (1216, 'demonstration', 'Theses'), (1217, 'evidence', 'Theses'), (1218, 'surprising', 'Theses'), (1219, 'surprising', 'Theses'), (1220, 'surprise', 'Theses'), (1221, 'supported', 'Theses'), (1222, 'suggests', 'Theses'), (1223, 'suggests', 'Theses'), (1224, 'suggests', 'Theses'), (1225, 'suggests', 'Theses'), (1226, 'suggests', 'Theses'), (1227, 'suggests', 'Theses'), (1228, 'suggests', 'Theses'), (1229, 'suggests', 'Theses'), (1230, 'suggests', 'Theses'), (1231, 'suggests', 'Theses'), (1232, 'suggesting', 'Theses'), (1233, 'suggesting', 'Theses'), (1234, 'suggesting', 'Theses'), (1235, 'suggesting', 'Theses'), (1236, 'suggesting', 'Theses'), (1237, 'suggesting', 'Theses'), (1238, 'suggesting', 'Theses'), (1239, 'suggested', 'Theses'), (1240, 'suggested', 'Theses'), (1241, 'suggested', 'Theses'), (1242, 'suggested', 'Theses'), (1243, 'suggested', 'Theses'), (1244, 'suggested', 'Theses'), (1245, 'suggested', 'Theses'), (1246, 'suggested', 'Theses'), (1247, 'suggested', 'Theses'), (1248, 'suggested', 'Theses'), (1249, 'suggested', 'Theses'), (1250, 'suggested', 'Theses'), (1251, 'suggested', 'Theses'), (1252, 'suggest', 'Theses'), (1253, 'suggest', 'Theses'), (1254, 'suggest', 'Theses'), (1255, 'suggest', 'Theses'), (1256, 'suggest', 'Theses'), (1257, 'suggest', 'Theses'), (1258, 'submit', 'Theses'), (1259, 'stating', 'Theses'), (1260, 'shows', 'Theses'), (1261, 'shown', 'Theses'), (1262, 'shown', 'Theses'), (1263, 'shown', 'Theses'), (1264, 'shown', 'Theses'), (1265, 'shown', 'Theses'), (1266, 'shown', 'Theses'), (1267, 'shown', 'Theses'), (1268, 'shown', 'Theses'), (1269, 'shown', 'Theses'), (1270, 'shown', 'Theses'), (1271, 'shown', 'Theses'), (1272, 'shown', 'Theses'), (1273, 'shown', 'Theses'), (1274, 'shown', 'Theses'), (1275, 'shown', 'Theses'), (1276, 'shown', 'Theses'), (1277, 'showing', 'Theses'), (1278, 'showed', 'Theses'), (1279, 'showed', 'Theses'), (1280, 'showed', 'Theses'), (1281, 'showed', 'Theses'), (1282, 'showed', 'Theses'), (1283, 'showed', 'Theses'), (1284, 'showed', 'Theses'), (1285, 'showed', 'Theses'), (1286, 'showed', 'Theses'), (1287, 'showed', 'Theses'), (1288, 'showed', 'Theses'), (1289, 'showed', 'Theses'), (1290, 'showed', 'Theses'), (1291, 'showed', 'Theses'), (1292, 'showed', 'Theses'), (1293, 'showed', 'Theses'), (1294, 'seen', 'Theses'), (1295, 'seems', 'Theses'), (1296, 'revealed', 'Theses'), (1297, 'reveal', 'Theses'), (1298, 'reported', 'Theses'), (1299, 'reported', 'Theses'), (1300, 'reported', 'Theses'), (1301, 'reported', 'Theses'), (1302, 'reported', 'Theses'), (1303, 'reported', 'Theses'), (1304, 'reported', 'Theses'), (1305, 'reported', 'Theses'), (1306, 'reported', 'Theses'), (1307, 'reported', 'Theses'), (1308, 'reported', 'Theses'), (1309, 'reported', 'Theses'), (1310, 'reported', 'Theses'), (1311, 'data', 'Theses'), (1312, 'recommended', 'Theses'), (1313, 'recognised', 'Theses'), (1314, 'recognised', 'Theses'), (1315, 'recognised', 'Theses'), (1316, 'recognised', 'Theses'), (1317, 'proposed', 'Theses'), (1318, 'propose', 'Theses'), (1319, 'propose', 'Theses'), (1320, 'projected', 'Theses'), (1321, 'postulated', 'Theses'), (1322, 'plausible', 'Theses'), (1323, 'understanding', 'Theses'), (1324, 'observed', 'Theses'), (1325, 'mentioning', 'Theses'), (1326, 'means', 'Theses'), (1327, 'likely', 'Theses'), (1328, 'likely', 'Theses'), (1329, 'likely', 'Theses'), (1330, 'likely', 'Theses'), (1331, 'likely', 'Theses'), (1332, 'known', 'Theses'), (1333, 'known', 'Theses'), (1334, 'indicating', 'Theses'), (1335, 'indicates', 'Theses'), (1336, 'indicates', 'Theses'), (1337, 'indicates', 'Theses'), (1338, 'indicated', 'Theses'), (1339, 'indicated', 'Theses'), (1340, 'indicated', 'Theses'), (1341, 'indicate', 'Theses'), (1342, 'implying', 'Theses'), (1343, 'implying', 'Theses'), (1344, 'implicating', 'Theses'), (1345, 'highlight', 'Theses'), (1346, 'shown', 'Theses'), (1347, 'shown', 'Theses'), (1348, 'shown', 'Theses'), (1349, 'Given', 'Theses'), (1350, 'found', 'Theses'), (1351, 'found', 'Theses'), (1352, 'found', 'Theses'), (1353, 'found', 'Theses'), (1354, 'found', 'Theses'), (1355, 'found', 'Theses'), (1356, 'found', 'Theses'), (1357, 'evidence', 'Theses'), (1358, 'evidence', 'Theses'), (1359, 'evidence', 'Theses'), (1360, 'evidence', 'Theses'), (1361, 'evidence', 'Theses'), (1362, 'estimated', 'Theses'), (1363, 'estimated', 'Theses'), (1364, 'estimated', 'Theses'), (1365, 'established', 'Theses'), (1366, 'documented', 'Theses'), (1367, 'documented', 'Theses'), (1368, 'discovered', 'Theses'), (1369, 'described', 'Theses'), (1370, 'demonstrated', 'Theses'), (1371, 'demonstrated', 'Theses'), (1372, 'demonstrated', 'Theses'), (1373, 'demonstrated', 'Theses'), (1374, 'demonstrated', 'Theses'), (1375, 'demonstrated', 'Theses'), (1376, 'demonstrated', 'Theses'), (1377, 'demonstrated', 'Theses'), (1378, 'demonstrated', 'Theses'), (1379, 'demonstrated', 'Theses'), (1380, 'demonstrated', 'Theses'), (1381, 'demonstrated', 'Theses'), (1382, 'demonstrated', 'Theses'), (1383, 'demonstrated', 'Theses'), (1384, 'demonstrated', 'Theses'), (1385, 'demonstrated', 'Theses'), (1386, 'demonstrated', 'Theses'), (1387, 'demonstrated', 'Theses'), (1388, 'demonstrated', 'Theses'), (1389, 'demonstrated', 'Theses'), (1390, 'demonstrated', 'Theses'), (1391, 'demonstrate', 'Theses'), (1392, 'demonstrate', 'Theses'), (1393, 'credible', 'Theses'), (1394, 'consistent', 'Theses'), (1395, 'Considering', 'Theses'), (1396, 'Considering', 'Theses'), (1397, 'considering', 'Theses'), (1398, 'considering', 'Theses'), (1399, 'confirmed', 'Theses'), (1400, 'confirmed', 'Theses'), (1401, 'concluded', 'Theses'), (1402, 'concluded', 'Theses'), (1403, 'believed', 'Theses'), (1404, 'believed', 'Theses'), (1405, 'believed', 'Theses'), (1406, 'believed', 'Theses'), (1407, 'believed', 'Theses'), (1408, 'believe', 'Theses'), (1409, 'recognition', 'Theses'), (1410, 'acknowledging', 'Theses'), (1411, 'accepted', 'Theses'), (1412, 'accepted', 'Theses'), (1413, 'range', 'Theses'), (1414, 'hope', 'Theses'), (1415, 'hoped', 'Theses'), (1416, 'hoped', 'Theses'), (1417, 'hoped', 'Theses'), (1418, 'hoped', 'Theses'), (1419, 'hoped', 'Theses'), (1420, 'hoped', 'Theses'), (1421, 'hoped', 'Theses'), (1422, 'hoped', 'Theses'), (1423, 'hoped', 'Theses'), (1424, 'hoped', 'Theses'), (1425, 'expect', 'Theses'), (1426, 'confirm', 'Theses'), (1427, 'ensure', 'Theses'), (1428, 'affirm', 'Theses'), (1429, 'rationale', 'Theses'), (1430, 'probability', 'Theses'), (1431, 'observation', 'Theses'), (1432, 'fact', 'Theses'), (1433, 'difference', 'Theses'), (1434, 'difference', 'Theses'), (1435, 'suggests', 'Theses'), (1436, 'suggests', 'Theses'), (1437, 'showed', 'Theses'), (1438, 'recognize', 'Theses'), (1439, 'probability', 'Theses'), (1440, 'application', 'Theses'), (1441, 'noteworthy', 'Theses'), (1442, 'noteworthy', 'Theses'), (1443, 'noted', 'Theses'), (1444, 'noted', 'Theses'), (1445, 'doubt', 'Theses'), (1446, 'method', 'Theses'), (1447, 'insist', 'Theses'), (1448, 'found', 'Theses'), (1449, 'ensure', 'Theses'), (1450, 'ensure', 'Theses'), (1451, 'ensure', 'Theses'), (1452, 'ensure', 'Theses'), (1453, 'ensure    ', 'Theses'), (1454, 'ensure', 'Theses'), (1455, 'demonstrated', 'Theses'), (1456, 'corroborated', 'Theses'), (1457, 'concern', 'Theses'), (1458, 'check', 'Theses'), (1459, 'assumes', 'Theses'), (1460, 'assumes', 'Theses'), (1461, 'ascertained', 'Theses'), (1462, 'reason', 'Theses'), (1463, 'unlikely', 'Theses'), (1464, 'thought', 'Theses'), (1465, 'thought', 'Theses'), (1466, 'advantage', 'Theses'), (1467, 'idea', 'Theses'), (1468, 'hypothesis', 'Theses'), (1469, 'hypothesis', 'Theses'), (1470, 'hypothesis', 'Theses'), (1471, 'hypothesis', 'Theses'), (1472, 'hypothesis', 'Theses'), (1473, 'hypothesis', 'Theses'), (1474, 'fact', 'Theses'), (1475, 'hypothesis', 'Theses'), (1476, 'suggesting', 'Theses'), (1477, 'suggest', 'Theses'), (1478, 'proposed', 'Theses'), (1479, 'presumed', 'Theses'), (1480, 'postulate', 'Theses'), (1481, 'possible', 'Theses'), (1482, 'possible', 'Theses'), (1483, 'possibility', 'Theses'), (1484, 'model', 'Theses'), (1485, 'likely', 'Theses'), (1486, 'likely', 'Theses'), (1487, 'likely', 'Theses'), (1488, 'concern', 'Theses'), (1489, 'implies', 'Theses'), (1490, 'hypothesized', 'Theses'), (1491, 'hypothesized', 'Theses'), (1492, 'hypothesize', 'Theses'), (1493, 'hypothesize', 'Theses'), (1494, 'hypothesised', 'Theses'), (1495, 'hypothesised', 'Theses'), (1496, 'Hypothesis', 'Theses'), (1497, 'hypothesis', 'Theses'), (1498, 'hypothesis', 'Theses'), (1499, 'hypothesis', 'Theses'), (1500, 'hypothesis', 'Theses'), (1501, 'hoped', 'Theses'), (1502, 'hoped', 'Theses'), (1503, 'hoped', 'Theses'), (1504, 'hoped', 'Theses'), (1505, 'expected', 'Theses'), (1506, 'expected', 'Theses'), (1507, 'expected', 'Theses'), (1508, 'demonstrating', 'Theses'), (1509, 'Assuming', 'Theses'), (1510, 'anticipated', 'Theses'), (1511, 'theory', 'Theses'), (1512, 'hypothesise', 'Theses')]
    df = pd.DataFrame.from_records(records, columns=['index', 'Text', 'Genre']).set_index('index')
    c = TermDocMatrixFromPandas(df, category_col='Genre', text_col='Text', nlp=whitespace_nlp).build()
    c.get_term_freq_df()
    c = CorpusFromPandas(df, category_col='Genre', text_col='Text', nlp=whitespace_nlp).build()
    df = c.get_term_freq_df()

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

@classmethod
def setUp(cls):
    categories, documents = get_docs_categories()
    cls.df = pd.DataFrame({'category': categories, 'text': documents})
    cls.corpus = CorpusFromPandas(cls.df, 'category', 'text', nlp=whitespace_nlp).build()

def get_test_corpus():
    df = pd.DataFrame(data=np.array(get_docs_categories_semiotic()).T, columns=['category', 'text'])
    corpus = CorpusFromPandas(df, 'category', 'text', nlp=whitespace_nlp).build()
    return corpus

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

class TestCorpusWithoutCategoriesFromParsedDocuments(unittest.TestCase):

    def test_main(self):
        doc_df = pd.DataFrame({'Text': [x.strip() for x in 'b a m n i b e u p\n        b a s a t b e w q n\n        b c a g a b e s t a\n        b a g h a b e a a t\n        b a h a a b e a x a t'.split('\n')]}).assign(Parse=lambda df: df.Text.apply(whitespace_nlp))
        corpus = CorpusWithoutCategoriesFromParsedDocuments(doc_df, parsed_col='Parse').build()

def test_main(self):
    doc_df = pd.DataFrame({'Text': [x.strip() for x in 'b a m n i b e u p\n        b a s a t b e w q n\n        b c a g a b e s t a\n        b a g h a b e a a t\n        b a h a a b e a x a t'.split('\n')]}).assign(Parse=lambda df: df.Text.apply(whitespace_nlp))
    corpus = CorpusWithoutCategoriesFromParsedDocuments(doc_df, parsed_col='Parse').build()

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

@classmethod
def setUpClass(cls):
    df = pd.read_csv(io.StringIO("publish_date,headline_text,publish_yearmonth,publish_month\n20150409,rural sa rural reporter the tale of two orchards,201504,04\n20111206,roar get ulsan in champions league draw,201112,12\n20101201,130m annual cost to run desal plant,201012,12\n20040802,farmers worried about wto agreement loopholes,200408,08\n20170808,same sex marriage plebiscite attempt expected to be blocked,201708,08\n20130621,executives spend a night on the streets to experience homelessn,201306,06\n20070613,nsw govt signs pollution reduction agreement with,200706,06\n20060209,nt doctors show support for abortion drug,200602,02\n20130718,crash driver sought by police,201307,07\n20061119,howard disputes blairs iraq comments,200611,11\n20070725,german reporter released in afghanistan,200707,07\n20120224,hammer heal to coach kings,201202,02\n20090428,written apology over holocaust denial,200904,04\n20141024,unions hand tasmanian government alternative savings plan,201410,10\n20061118,shark gets some pride back,200611,11\n20130206,older watson concerned for jobe bombers,201302,02\n20140430,forum to showcase mid west mining developments,201404,04\n20140429,former wa treasurer buswell admits to driving offences,201404,04\n20070621,weather to determine sports fields opening,200706,06\n20140803,travel blamed for increasing rate of hiv in wa,201408,08\n20050715,stuey takes aim at green jersey,200507,07\n20061219,public urged to help combat fruit fly threat,200612,12\n20040302,robben chooses chelsea over united,200403,03\n20030820,jury to continue deliberations in hanson fraud,200308,08\n20030323,baghdads military facilities targeted in latest,200303,03\n20140417,an india holds biggest day of voting,201404,04\n20050102,car bomb attack kills 18 iraqi national guards,200501,01\n20080818,citation boosts vietnam veterans day significance,200808,08\n20131111,wenceslas magun speaks to pacific beat,201311,11\n20130325,an vanuatu gets new pm,201303,03\n20160423,woman killed in crash with stobie pole,201604,04\n20091006,message spread that attacks not tolerated brumby,200910,10\n20040707,iraq adopts new security laws,200407,07\n20030916,poland gets record case of the blues,200309,09\n20040406,jordan sentences eight to death over diplomat,200404,04\n20101022,arnold to relish cox plate pressure,201010,10\n20130610,lack of data creates concern over true extent of medical errors,201306,06\n20060317,labor warns on minority government,200603,03\n20100808,labor to ban truants from playing sport,201008,08\n20071210,sharks spotted in esperance port,200712,12\n20041224,aust troops to celebrate christmas in iraq,200412,12\n20090819,jail term for rsl theft,200908,08\n20070408,closer am1nodisplay,200704,04\n20161114,nt man jailed for crimes against children,201611,11\n20051003,union warns ir changes threaten australian way of,200510,10\n20041007,afghan children lose high court battle against,200410,10\n20130506,parkinsons test sought,201305,05\n20110329,police accused of not probing brutality claim,201103,03\n20090828,cairns trip ends in top end lsd bust,200908,08\n20120816,coroner criticises ambulance 'ramping',201208,08\n20130121,new recruits for womens cycling team,201301,01\n20050203,uni to hold tropical science precinct talks,200502,02\n20041110,jetstar asia prepares for launch,200411,11\n20090326,mccreadie granted immunity,200903,03\n20170821,one killed in france after car crashes into bus shelters,201708,08\n20081031,gambhir handed one test ban,200810,10\n20150527,school communities unsettled about prospect of school closures,201505,05\n20050829,man accused of ramming car with children inside,200508,08\n20130821,van park owner pursues legal options over free,201308,08\n20060406,national network to track pseudoephedrine sales,200604,04\n20040708,big sports complex planned near maitland,200407,07\n20100714,ex afl player paid nearly 80k to conman,201007,07\n20120711,victory retain milligans services,201207,07\n20080221,bad weather delays dalrymple bay coal terminal,200802,02\n20151021,govt department tests scales get what paid for,201510,10\n20090208,battered jets sign italian striker vignaroli,200902,02\n20130205,capital hill monday 4 february 2013,201302,02\n20161013,medicinal cannabis register considered tasmania,201610,10\n20041202,underwood sworn in as chief justice,200412,12\n20110701,rta heeds call for pedestrian safety upgrade,201107,07\n20120723,miners say cost of business too high,201207,07\n20090103,funding secures more aerial shark patrols,200901,01\n20170603,were australias first people nomadic,201706,06\n20031019,tributes pour in for spanish writer montalban,200310,10\n20080301,interview ricky ponting,200803,03\n20100831,forlan at the double for atletico,201008,08\n20060907,lawyers say vizards silence is unfair to hilliard,200609,09\n20060524,shoulder troubles for roddick ahead of french,200605,05\n20080809,tennis form guide mens singles,200808,08\n20171206,family of betty dixon still asking questions as cold case ends,201712,12\n20080715,fed court overturns annoying ban,200807,07\n20120131,rare earth industry developing rapidly,201201,01\n20131117,tremlett prior set to start for england,201311,11\n20121114,eltons latest book explores brothers relationship,201211,11\n20070316,evans a man of honesty and integrity,200703,03\n20040908,financial lobby criticises labor tax package,200409,09\n20030604,health service urged to review gp anaesthetist,200306,06\n20030410,restrictions for melbourne as water cost rises,200304,04\n20161022,pamela anderson speaks out about pornographys numbing effects,201610,10\n20120804,fire warning,201208,08\n20110329,paramedic gives evidence at road crash murder trial,201103,03\n20160711,response to labor mp call to ban fracking in south west,201607,07\n20111007,health razor gang disbands early,201110,10\n20141023,acid attacks on women spark protests in iran,201410,10\n20100401,mp airs fears for forestry jobs,201004,04\n20121124,interview rianna ponting,201211,11\n20120820,tony burke talks with four corners,201208,08\n20100815,20 million affected by pakistan floods,201008,08\n20091222,china planning to execute briton next week,200912,12\n20100819,woman granted bail over torso in bush find,201008,08\n20091103,christmas island locals forgotten in asylum debate,200911,11\n20071027,eden monaro headed for labor poll,200710,10\n20121027,alleged hijackers flown to sri lanka to face charges,201210,10\n20160320,powerlifting: watch a benchpress; a deadlift and a,201603,03\n20130913,new york jets' mark sanchez facing season ending shoulder sur,201309,09\n20120324,we have to put bligh legacy behind us,201203,03\n20050524,budget sees return of investment properties tax,200505,05\n20101117,germany increases security amid terrorist threat,201011,11\n20150713,newcastle man in coma after drunken argument,201507,07\n20140812,titans need help in afl battle,201408,08\n20170119,vegemite back in australian hands,201701,01\n20070508,utai out cutler in for dogs,200705,05\n20160818,artists opens up world of picture book illustrations,201608,08\n20150731,north queensland ports urge ports bill fine tuning,201507,07\n20060623,wimmera sheep sales increase,200606,06\n20120105,opposition queries extra senior bureaucrats,201201,01\n20120514,hume result,201205,05\n20070909,victorians going green,200709,09\n20121113,broken hill baby birds back in their nests,201211,11\n20111023,drunk driving police,201110,10\n20070806,four arrested over safe breaks,200708,08\n20131214,sri lanka retain twenty20 number one ranking,201312,12\n20061122,sydney tourism snubs regional areas,200611,11\n20070512,curbishley confident of players resolve,200705,05\n20050924,ten killed in gaza hamas rally blast,200509,09\n20080804,police dig for baby 12 years on,200808,08\n20090602,centenary show for gin gin,200906,06\n20090426,g20 ministers still cautious on global economy swan,200904,04\n20080918,david kidman from ferrier hodgson talks about the,200809,09\n20091101,beauty with a twist,200911,11\n20091203,henderson talks up brave 2030 plan,200912,12\n20070913,power in no rush to decide political future,200709,09\n20091209,swine flu far milder than feared,200912,12\n20091216,us house of reps honours miles davis album,200912,12\n20160816,two dead in crash on eyre highway near balladonia,201608,08\n20091022,worms linked to coeliac relief,200910,10\n20140401,wafarmers urges growers to decrease debt,201404,04\n20121115,fmg diversifies into oil and gas,201211,11\n20040121,leaders may need to resolve trade talks,200401,01\n20081207,tasmanians urged to spend within their means,200812,12\n20140822,sa police join search for missing warrnambool man,201408,08\n20051219,company fined after explosions injured workers,200512,12\n20081013,thai queen to attend protesters funeral,200810,10\n20111124,global stocks close,201111,11\n20051221,aquaculture group upset with course axing,200512,12\n20121224,somali troops end hostages' three year ordeal,201212,12\n20090804,bligh vows to refer email row to cmc,200908,08\n20100714,appointed to healths top job,201007,07\n20100128,remote schools low on my school site,201001,01\n20140505,festival visitors get taste for regions produce,201405,05\n20030413,canegrowers push for ethanol mix in all petrol,200304,04\n20110409,clarke ton helps aussies to victory,201104,04\n20151207,police seek witnesses to fatal tintinara road crash,201512,12\n20041013,tax relief tipped for wa home buyers,200410,10\n20050312,bulls charge towards home final,200503,03\n20151125,three men dead in perth workplace accidents,201511,11\n20160516,federal government considers assistance package dairy farmers,201605,05\n20130523,minister jeanette powell outlines strategy for victoria's abo,201305,05\n20140919,jackson primary school censorship,201409,09\n20090909,russians behind cyber crime says afp,200909,09\n20030709,indias congress considers coalition to oust bjp,200307,07\n20050425,council plans memorial to grassby,200504,04\n20090810,slovak mine blast traps 19 miners,200908,08\n20121123,some tourism operators say no to schoolies,201211,11\n20150507,australian farming families the feature of a new,201505,05\n20120322,young roos,201203,03\n20101206,katich has scans on achilles injury,201012,12\n20070627,pricey sydney tops census again,200706,06\n20060319,opals enjoy another big win,200603,03\n20160318,albany residents to be quizzed over muttonbird reserve,201603,03\n20150902,china fta senator colbeck trade,201509,09\n20160609,greyhound racing nsw charges 179 trainers owners,201606,06\n20060220,internet smss blamed for big crowd at party,200602,02\n20031203,renison mine to remain closed,200312,12\n20151215,newcastle giving tree finished for 2015,201512,12\n20070707,afp release five doctors after questioning,200707,07\n20121130,an bangladesh inspections,201211,11\n20121008,man quizzed over high speed chase,201210,10\n20080409,lennon under fire over kons resignation,200804,04\n20130510,compo concerns,201305,05\n20150730,police plead for clues to tenterden road crash,201507,07\n20081014,an open and shut case for nw road,200810,10\n20100511,scott daughters settle estate fight,201005,05\n20080523,suitability of hensons images depends on context,200805,05\n20060622,aged care group restructures decision making,200606,06\n20150204,nff wants banks to pass on interest rate cut to farmers,201502,02\n20041118,govts urged to act on commuter train service,200411,11\n20030323,worldwide protests demand peace,200303,03\n20040601,gillespie talks up worth of zimbabwe series,200406,06\n20050506,tribunal cracks down on video evidence,200505,05\n20151021,police make arrest missing mother linda sidon gold coast,201510,10\n20121012,scientists uncover mystery of ball lightning,201210,10\n20140430,encouraging girls in engineering jpbs,201404,04\n20160816,woman charged over assault of victorian labor mp jane garrett,201608,08\n20140224,cattle saleyards canteen ladies,201402,02\n20080726,final showdown looms for tour,200807,07\n20111229,pesce a rising tide of chaos,201112,12\n20040426,former us ambassador doubts iraq wmd focus,200404,04\n20080603,evicted aborigines finish training in sydney,200806,06\n20070412,cadets to attend sandakan dawn service,200704,04\n20100425,red shirts discarded ahead of crackdown,201004,04\n20070625,four to appear in court over coolgardie burglary,200706,06\n20140812,nrn graincorp ceo,201408,08\n20101230,interview michael clarke,201012,12\n20110506,workers to mine tafe for education needs,201105,05\n20130912,wafl player has bail varied to play,201309,09\n20120809,simpson elected murray irrigation shareholder,201208,08\n20121206,ice blamed for crime spike,201212,12\n20080622,opec divided on saudi summit and production boost,200806,06\n20050513,heroin bust in adelaide,200505,05\n20051004,nrma highlights need for pacific highway attention,200510,10\n20110706,public quizzed about closed inlet,201107,07\n20150225,herbicide resistance peter newman,201502,02\n20050216,push for second kakadu uranium mine,200502,02\n20040314,murali set to join warne in 500 wicket club,200403,03\n20131104,soil carbon climate change,201311,11\n20100208,the wwfs paul gamblin says a report should put,201002,02\n20040922,indonesian presidential hopeful plans peace in aceh,200409,09\n20170405,bushfire emergency downgraded near esperance in wa,201704,04\n20120724,injured sea birds washing up inland,201207,07\n20160729,donald trump v hillary clinton star power of the conventions,201607,07\n20120522,impact of bomb blasts on the brain,201205,05\n20140811,israel palestine agree to 72 hour cease fire in gaza,201408,08\n20130610,14yos accused of armed robbery,201306,06\n20051114,mp says tafe fees soaring,200511,11\n20050419,woolworths sales up more than 14pc,200504,04\n20080907,peter leek breaks butterfly world record,200809,09\n20080426,jones trickett set new world records,200804,04\n20041224,karzai removes warlords from afghan cabinet,200412,12\n20120329,no confidence showdown looming,201203,03\n20110114,brazil floods mudslides kill hundreds,201101,01\n20160918,hospital parking fees petition gains support on change org,201609,09\n20140716,china gdp growth hits expectations,201407,07\n20071206,pasha findings prompt port review,200712,12\n20080627,pigeons smuggle drugs phones into rio prison,200806,06\n20071228,plucky india fights back in melbourne,200712,12\n20150419,thousands in germany protest against ttip europe us trade deal,201504,04\n20100112,rain sets up new crop for cane farmers,201001,01\n20110110,peter andre named hardest working singer,201101,01\n20120830,search becomes rescue as asylum boat found,201208,08\n20050715,manslaughter charge dropped in bondage case,200507,07\n20120822,laurie daley interview,201208,08\n20030601,williams silent on sydney ji unit claim,200306,06\n20060226,govt offers to buy back sydney harbour fishing,200602,02\n20061115,reward offered to catch roo shooter,200611,11\n20121128,report suggests turnaround for struggling boxed,201211,11\n20081024,november execution for bali bombers,200810,10\n20040513,ethnic sounds unite eurovision,200405,05\n20111128,murray darling authority chairman craig knowles,201111,11\n20160122,brisbane artist helps fans pay tribute to idols through nail art,201601,01\n20120821,australia too complacent,201208,08\n20070829,rudd pressures howard to pick election date,200708,08\n20171203,cooper cronk goes out on top announcing retirement from rep,201712,12\n20140212,oz shares surge after ceo announces departure,201402,02\n20060630,council happy to receive community funds for,200606,06\n20131113,lifeline helping miners prevent suicide,201311,11\n20100701,authorities fear grass fires deliberately lit,201007,07\n20040827,family hires security guard for protection,200408,08\n20110315,contempt of court charge against paper dropped,201103,03\n20030416,full text 13 point plan for iraq,200304,04\n20090704,nrl interview neil henry,200907,07\n20120306,sa courts,201203,03\n20060119,australia west indies postpone 2007 test series,200601,01\n20140603,bosnia finalises cup squad,201406,06\n20121127,victorian government backs down on scrapping fruit,201211,11\n20050131,perth kalgoorlie line set to reopen on weekend,200501,01\n20150428,chile volcano calbuco economy 600 million tourism eruption,201504,04\n20130313,grain prices rabobank,201303,03\n20140415,fia upholds ricciardo disqualification,201404,04\n20100425,pies embarrass dons on big stage,201004,04\n20120213,shining path leader captured,201202,02\n20160715,rescue plane goes down in goldfields hunt for missing man,201607,07\n20110901,storm wont appeal blairs ban,201109,09\n20131108,today tonight twist in gittany trial,201311,11\n20070413,tour boat profits blown away,200704,04\n20170921,farmers open the farm gate to combat carrot glut,201709,09\n20130507,qdo resignation,201305,05\n20060531,australian teams join quake aid efforts,200605,05\n20110705,bartos the public service numbers game,201107,07\n20060705,patient no shows end specialist medical service,200607,07\n20150804,multi million dollar northern farming system project,201508,08\n20171229,china foreign ministry denies claims its still,201712,12\n20110807,masterchef winner,201108,08\n20161006,for better or worse: four corners,201610,10\n20070308,rsl investigates veterans home care service,200703,03\n20090212,keane at the double for ireland,200902,02\n20080102,pakistan issues photos of bhutto death offers,200801,01\n20121113,pair charged following police shooting,201211,11\n20040304,hope for business chamber turnaround,200403,03\n20050226,cabinet to consider nightclub lock out plan,200502,02\n20061220,illawarra schools do well in hsc,200612,12\n20121112,data reveals strong regional rental markets,201211,11\n20060629,teen found safe after missing in bush for three,200606,06\n20060110,star studded field confirmed for johnnie walker,200601,01\n20120113,abc sport,201201,01\n20140702,trade balance slumps to near 2 billion deficit on fall in iron,201407,07\n20090928,star to be born again,200909,09\n20100712,experts warn against growing diabetes threat,201007,07\n20031212,rampaging roy wins cultural recognition,200312,12\n20081221,chinese warships to join anti piracy force,200812,12\n20040603,mayor highlights hidden amalgamation costs,200406,06\n20091013,locals threaten to block kokoda over crash compo,200910,10\n20081211,connex told to fix industrial dispute,200812,12\n20141204,ronja huon aquaculture salmon,201412,12\n20161102,private investor interest in henty pub,201611,11\n20100324,councils face off over oakajee,201003,03\n20160407,the peasant prince,201604,04\n20171018,daphne caruana galizias son accuses malta pm of complicity,201710,10\n20151012,barns risky detention policy,201510,10\n20130102,under age drinking a big problem in manning great lakes,201301,01\n20150918,the rbas advice for the us fed on hiking rates,201509,09\n20151027,adelaide bite baseballer's assault charge may be dropped,201510,10\n20070207,survey normal govt procedure says minister,200702,02\n20170324,anz joins the rush to raise home loan interest rates,201703,03\n20110214,work to start on new adelaide airport parking,201102,02\n20130309,interview johnathan thurston,201303,03\n20101206,west coast abalone season winds up,201012,12\n20110705,westhoff injury gives cornes his chance,201107,07\n20100930,pyne sent from chamber for hopeless jibe,201009,09\n20120515,rocks to tackle foreshore erosion woes,201205,05\n20101217,storm threat eases in south east queensland,201012,12\n20041017,richmond slips away from anthony,200410,10\n20070910,rare nsw plant faces extinction,200709,09\n20140602,clunies ross science award for gravity separator,201406,06\n20090713,angelita pires on trial for conspiracy,200907,07\n20070916,nt comes to grips with alcohol bans,200709,09\n20040929,tourism award nomination for pioneer settlement,200409,09\n20100223,australia v west indies innings highlights,201002,02\n20080508,people must be across risks and benefits of gm,200805,05\n20080624,goodes accepts ban,200806,06\n20030619,capriati and rubin win at eastbourne,200306,06\n20100610,youth job agency to close doors,201006,06\n20051110,call made to cut infrastructure project red tape,200511,11\n20130530,adam scott not planning to sue over anchoring,201305,05\n20041216,toxicologist calls for more drink spiking evidence,200412,12\n20110605,police find teen detention centre escapee,201106,06\n20060727,memorial to honour murdered sisters,200607,07\n20150908,jason day heads presidents cup team to take on us in october,201509,09\n20040702,icc confirms postponement of zimbabwe tests,200407,07\n20120413,philips bob brown,201204,04\n20080318,newcastle building society passes on rate rise,200803,03\n20121121,emma roberts avery wines,201211,11\n20101218,vics take innings points,201012,12\n20130514,nt cattle sold to vic,201305,05\n20101122,art world welcomes indigenous recruits,201011,11\n20130227,hough eyeing off moscow berth,201302,02\n20120718,an thai military outpost and village attacked,201207,07\n20110331,labors downfall the machine and the split,201103,03\n20150715,tonga pm casts doubt on country's ability to host pacific games,201507,07\n20141002,accc approves sale of acttab to tabcorp group,201410,10\n20050930,hope for power station to attract new industries,200509,09\n20140317,hamelin wake,201403,03\n20101013,11 jailed over van gogh theft,201010,10\n20090418,20 hostages freed from pirate mother ship,200904,04\n20131121,probe into 2011 police shooting in coffs harbour still incomple,201311,11\n20090920,torres double gets liverpool home,200909,09\n20100502,mayfair holding firm at quail hollow,201005,05\n20041106,samarra car bombs kill 8 wound 20,200411,11\n20080923,ses under pressure as storms hit riverina,200809,09\n20150528,australians unaware they have chronic kidney disease report,201505,05\n20080929,court hears torres strait seas claim,200809,09\n20141118,abortion row erupts between coalition candidates in ballarat,201411,11\n20090211,tornado kills 8 people in oklahoma,200902,02\n20170623,danny noonan ex afl player jailed for stealing from clients,201706,06\n20151104,efficient housing a focus for aboriginal land council's new w,201511,11\n20070416,missing elderly man found safe,200704,04\n20060607,council includes road repair funds in draft budget,200606,06\n20090903,cba feels wrath over storm collapse,200909,09\n20121209,marquez knocks out pacquiao,201212,12\n20090619,sharks fraud claims parents charged,200906,06\n20121219,ambulance reforms written off by paramedic's union,201212,12\n20151221,water sharing arrangement could be fast tracked due to contamin,201512,12\n20070514,viduka in no rush to decide future,200705,05\n20100212,penn universitys climategate findings,201002,02\n20051014,bikers ride honours sheene,200510,10\n20090201,hotter drier january,200902,02\n20091231,capital fireworks to bring in new year,200912,12\n20150327,joeys to be released into the wild after adelaide bushfires,201503,03\n20100223,amcor profit beats expectations,201002,02\n20040813,sex charges highlight need for workplace education,200408,08\n20030326,libs claim south coast seat,200303,03\n20060502,federal govt to fund airport security upgrade,200605,05\n20100710,yacht murder case begins,201007,07\n20070305,carpenter vows to force grill out of alp,200703,03\n20051006,us senate moves to ban prisoner torture,200510,10\n20121223,tendulkar retires from odis,201212,12\n20141003,nobel peace summit 'suspended' over dalai lama visa row,201410,10\n20050601,schumacher dismisses quit questions,200506,06\n20040921,parents shy away from meningococcal vaccinations,200409,09\n20121023,prince charles australian travel plans revealed,201210,10\n20140509,new mental health centre to help patients,201405,05\n20030929,lisbie hat trick stuns liverpool,200309,09\n20060202,awb kickbacks scandal puts govt under us pressure,200602,02\n20050909,man killed in head on crash,200509,09\n20130725,nrn ag minister shepp,201307,07\n20070807,croydon council delivers budget,200708,08\n20121102,an worldbank earmarks $245m for burma,201211,11\n20110523,doubt behind the aggression,201105,05\n20100826,interview brett kimmorley,201008,08\n20040703,new disease threatens qld citrus crops,200407,07\n20080522,man charged with assaulting girls wanted in qld,200805,05\n20140709,mining ojbection legislation changes,201407,07\n20160308,efforts to get more women to become truck drivers in tasmania,201603,03\n20040706,crackdown on overseas trained country doctors,200407,07\n20151119,national rural news,201511,11\n20140321,sydney light rail extension to open next week,201403,03\n20151211,doris fenbows killer alexis katsis jailed for 15 years,201512,12\n20111012,waca ceo wood resigns,201110,10\n20060824,program cuts childhood obesity rate researchers say,200608,08\n20140130,hospital forced to use surge capacity beds on regular basis,201401,01\n20101006,red cross opens doors in kalgoorlie boulder,201010,10\n20030716,boyle praises freeman as best of her generation,200307,07\n20131114,ract takes over federal groups' tourism ventures,201311,11\n20170529,queensland government to play ball over adani loan: treasurer,201705,05\n20151021,milky way galaxy star forming clouds,201510,10\n20120511,van egmond admits informal talks about leaving jets,201205,05\n20110718,more groundwater trials at mount zero,201107,07\n20051212,angel wins murgon by election,200512,12\n20100301,record rain fills heart of australia,201003,03\n20090727,council to sign algae biodiesel agreement,200907,07\n20121207,uninterrupted grain harvest nears end,201212,12\n20160824,wesfarmers richard goyder defends business council,201608,08\n20051017,briefings to be held for would be councillors,200510,10\n20040623,hobart prepares for jim bacons funeral,200406,06\n20070807,second suspected foot and mouth outbreak in britain,200708,08\n20101010,qr national float details unveiled,201010,10\n20060919,brock funeral begins in melbourne,200609,09\n20170620,family road trip tells burke and wills story through theatre,201706,06\n20151109,china and australia to share antarctic sea ice research,201511,11\n20141119,victoria beats south australia in shield,201411,11\n20150930,tas country hour wednesday 21 september 2015,201509,09\n20141015,consumer sentiment negative in westpac survey,201410,10\n20090719,india can make its own decisions clinton says,200907,07\n20140320,council urged to crack down on illegal holiday,201403,03\n20080925,dog attacks policewoman in boulder,200809,09\n20080123,springborg attempting to rebadge the national,200801,01\n20050120,houses crack in canadian cold spell,200501,01\n20130923,mining company discovers second cement spill in sugarloaf,201309,09\n20031108,us jobs figures fail to bolster markets,200311,11\n20110519,boat tragedy video released,201105,05\n20121102,call for review of water concessions,201211,11\n20120616,interview michael maguire,201206,06\n20030413,death toll rises on nsw roads,200304,04\n20110330,no verdict in airport caterer drug case,201103,03\n20100921,study to probe field days value,201009,09\n20100912,resilience will help say dogs,201009,09\n20110607,boaties rescue sparks emergency beacon reminder,201106,06\n20110628,robinson re signs with reds,201106,06\n20040110,fleming ton seals kiwi win,200401,01\n20111123,holden recalls diesel cars,201111,11\n20041012,china may sign fta with nz first,200410,10\n20130417,new radar,201304,04\n20140304,nsw country hour 4 march 2014,201403,03\n20060807,stanhope rejects tax discrepancy claims,200608,08\n20070308,downpour cancels bemboka show,200703,03\n20160718,toowoomba south lnp david janetzki claims victory in by election,201607,07\n20101208,flood peak fears ease in rockhampton,201012,12\n20050525,dumped car not linked to missing schoolboy police,200505,05\n20071115,second stage of vegie industry water saving,200711,11\n20080908,aust paralympic swimmers miss out on medals,200809,09\n20150622,geelong star kills another dolphin prompting fishery closure,201506,06\n20050417,ofc backs socceroos asian move,200504,04\n20150316,islamic state militants claim attack on checkpoint in libya,201503,03\n20080729,luhrmann on transformative experiences,200807,07\n20111115,man jailed over beer bottle glassing,201111,11\n20051031,windies coach denies players have attitude problem,200510,10\n20101119,court jails driver for running down man,201011,11\n20110503,pakistan embarrassed by intelligence failure,201105,05\n20071121,security camera funding pledge for mackay,200711,11\n20110104,police suspect careless campers behind bushfire,201101,01\n20150825,san francisco coach attempts to hose down hayne hype,201508,08\n20030315,hewitt still top dog,200303,03\n20131227,ukraine protesters rally after journalist bashed,201312,12\n20080423,bryce bligh address students at brisbane anzac,200804,04\n20080902,domestic markets flat despite interest rate cut,200809,09\n20080113,bligh approval soars to 68pc,200801,01\n20080303,southern road fatality,200803,03\n20160127,tunarama 2016 highlights port lincoln,201601,01\n20141223,warner will be ready for boxing day test,201412,12\n20150707,75yo fraser coast woman dies after suspected,201507,07\n20090515,rees urges players to come forward,200905,05\n20140311,smith agrees to four year extension at storm,201403,03\n20120511,black caviar prepares for australian finale,201205,05\n20160929,sa weather fuel shortages eyre peninsula residents stranded,201609,09\n20151209,north coast victims tell stolen generations inquiry more suppor,201512,12\n20141204,ebola global toll rises further as virus spreads in sierra leone,201412,12\n20071101,bryan cousins lashes out at media,200711,11\n20070211,clashes flare again over jerusalem mosque,200702,02\n20101220,blisters and pimples clog 000,201012,12\n20140731,australian medical association regional queenslanders obese,201407,07\n20080213,apology welcome reconciliation the next goal tas,200802,02\n20050916,two injured in skydiving accident,200509,09\n20151211,captain of honduras soccer team shot dead,201512,12\n20090102,israels labour rebounds in polls after gaza blitz,200901,01\n20111115,karumba barra centre could close,201111,11\n20090826,nelson proud of saving propellant factory,200908,08\n20130330,couple wanted over sydney diamond heist,201303,03\n20090501,mp demands more police to fill shortages,200905,05\n20141010,glenn hall re signs with north queensland cowboys,201410,10\n20140425,projections illuminate anzacs,201404,04\n"))
    df['parse'] = df.headline_text.apply(whitespace_nlp_with_sentences)
    df['publish_yearmonth'] = df['publish_yearmonth'].astype(str)
    df['publish_month'] = df['publish_month'].astype(str)
    cls.corpus = CorpusFromParsedDocuments(df, category_col='publish_yearmonth', parsed_col='parse').build()

class TestEmbeddingsResolver(TestCase):

    @classmethod
    def setUp(cls):
        categories, documents = get_docs_categories()
        cls.df = pd.DataFrame({'category': categories, 'text': documents})
        cls.df['parsed'] = cls.df.text.apply(whitespace_nlp)
        cls.corpus = CorpusFromParsedDocuments(cls.df, 'category', 'parsed').build()

    def test_resolve_embeddings(self):
        tdm = self.corpus.get_unigram_corpus().select(ClassPercentageCompactor(term_count=1))
        embeddings_resolver = EmbeddingsResolver(tdm)
        embeddings_resolver = embeddings_resolver.set_embeddings(tdm.get_term_doc_mat())
        if self.assertRaisesRegex:
            with self.assertRaisesRegex(Exception, 'You have already set embeddings by running set_embeddings or set_embeddings_model.'):
                embeddings_resolver.set_embeddings_model(None)
        embeddings_resolver = EmbeddingsResolver(tdm)
        embeddings_resolver = embeddings_resolver.set_embeddings_model(MockWord2Vec(tdm.get_terms()))
        if self.assertRaisesRegex:
            with self.assertRaisesRegex(Exception, 'You have already set embeddings by running set_embeddings or set_embeddings_model.'):
                embeddings_resolver.set_embeddings(tdm.get_term_doc_mat())
        c, axes = embeddings_resolver.project_embeddings(projection_model=TruncatedSVD(3))
        self.assertIsInstance(c, ParsedCorpus)
        self.assertEqual(axes.to_dict(), pd.DataFrame(index=['speak'], data={'x': [0.0], 'y': [0.0]}).to_dict())

@classmethod
def setUp(cls):
    categories, documents = get_docs_categories()
    cls.df = pd.DataFrame({'category': categories, 'text': documents})
    cls.df['parsed'] = cls.df.text.apply(whitespace_nlp)
    cls.corpus = CorpusFromParsedDocuments(cls.df, 'category', 'parsed').build()

def test_resolve_embeddings(self):
    tdm = self.corpus.get_unigram_corpus().select(ClassPercentageCompactor(term_count=1))
    embeddings_resolver = EmbeddingsResolver(tdm)
    embeddings_resolver = embeddings_resolver.set_embeddings(tdm.get_term_doc_mat())
    if self.assertRaisesRegex:
        with self.assertRaisesRegex(Exception, 'You have already set embeddings by running set_embeddings or set_embeddings_model.'):
            embeddings_resolver.set_embeddings_model(None)
    embeddings_resolver = EmbeddingsResolver(tdm)
    embeddings_resolver = embeddings_resolver.set_embeddings_model(MockWord2Vec(tdm.get_terms()))
    if self.assertRaisesRegex:
        with self.assertRaisesRegex(Exception, 'You have already set embeddings by running set_embeddings or set_embeddings_model.'):
            embeddings_resolver.set_embeddings(tdm.get_term_doc_mat())
    c, axes = embeddings_resolver.project_embeddings(projection_model=TruncatedSVD(3))
    self.assertIsInstance(c, ParsedCorpus)
    self.assertEqual(axes.to_dict(), pd.DataFrame(index=['speak'], data={'x': [0.0], 'y': [0.0]}).to_dict())

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

@classmethod
def setUp(cls):
    cls.categories, cls.documents = get_docs_categories()
    cls.parsed_docs = []
    for doc in cls.documents:
        cls.parsed_docs.append(whitespace_nlp(doc))
    cls.df = pd.DataFrame({'category': cls.categories, 'author': ['a', 'a', 'c', 'c', 'c', 'c', 'd', 'd', 'e', 'e'], 'parsed': cls.parsed_docs, 'document_lengths': [len(doc) for doc in cls.documents]})
    cls.corpus = CorpusFromParsedDocuments(cls.df, 'category', 'parsed').build()

class TestCategoryColorAssigner(TestCase):

    def test_main(self):
        categories, documents = get_docs_categories()
        df = pd.DataFrame({'category': categories, 'text': documents})
        corpus = CorpusFromPandas(df, 'category', 'text', nlp=whitespace_nlp).build()
        self.assertEqual(CategoryColorAssigner(corpus).get_category_colors().to_dict(), {'???': [255, 127, 14], 'hamlet': [174, 199, 232], 'jay-z/r. kelly': [31, 119, 180]})
        term_colors = CategoryColorAssigner(corpus).get_term_colors()
        self.assertEqual(term_colors['this time'], '#aec7e8')
        self.assertEqual(term_colors['sire'], '#1f77b4')
        self.assertEqual(len(term_colors), corpus.get_num_terms())
        mfact = CSRMatrixFactory()
        mis = IndexStore()
        for i, c in enumerate(df['category']):
            mfact[i, mis.getidx(c)] = 1
        corpus = corpus.add_metadata(mfact.get_csr_matrix(), mis)
        meta_colors = CategoryColorAssigner(corpus, use_non_text_features=True).get_term_colors()
        self.assertEqual(meta_colors, {'hamlet': '#aec7e8', 'jay-z/r. kelly': '#1f77b4', '???': '#ff7f0e'})
        self.assertNotEqual(CategoryColorAssigner(corpus).get_term_colors(), meta_colors)

def test_main(self):
    categories, documents = get_docs_categories()
    df = pd.DataFrame({'category': categories, 'text': documents})
    corpus = CorpusFromPandas(df, 'category', 'text', nlp=whitespace_nlp).build()
    self.assertEqual(CategoryColorAssigner(corpus).get_category_colors().to_dict(), {'???': [255, 127, 14], 'hamlet': [174, 199, 232], 'jay-z/r. kelly': [31, 119, 180]})
    term_colors = CategoryColorAssigner(corpus).get_term_colors()
    self.assertEqual(term_colors['this time'], '#aec7e8')
    self.assertEqual(term_colors['sire'], '#1f77b4')
    self.assertEqual(len(term_colors), corpus.get_num_terms())
    mfact = CSRMatrixFactory()
    mis = IndexStore()
    for i, c in enumerate(df['category']):
        mfact[i, mis.getidx(c)] = 1
    corpus = corpus.add_metadata(mfact.get_csr_matrix(), mis)
    meta_colors = CategoryColorAssigner(corpus, use_non_text_features=True).get_term_colors()
    self.assertEqual(meta_colors, {'hamlet': '#aec7e8', 'jay-z/r. kelly': '#1f77b4', '???': '#ff7f0e'})
    self.assertNotEqual(CategoryColorAssigner(corpus).get_term_colors(), meta_colors)

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

def _get_test_corpus(self):
    cats, docs = get_docs_categories_four()
    df = pd.DataFrame({'category': cats, 'text': docs})
    corpus = CorpusFromPandas(df, 'category', 'text', nlp=whitespace_nlp).build()
    return corpus

def build_term_doc_matrix():
    term_doc_matrix = TermDocMatrixFactory(category_text_iter=iter_party_speech_pairs(), clean_function=clean_function_factory(), nlp=whitespace_nlp).build()
    return term_doc_matrix

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

@classmethod
def setUp(cls):
    cls.categories, cls.documents = get_docs_categories()
    cls.parsed_docs = []
    for doc in cls.documents:
        cls.parsed_docs.append(whitespace_nlp(doc))
    cls.df = pd.DataFrame({'category': cls.categories, 'parsed': cls.parsed_docs})
    cls.corpus_fact = CorpusFromParsedDocuments(cls.df, 'category', 'parsed')

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

class TestCompactTerms(TestCase):

    def test_get_term_indices_to_compact(self):
        """
		term_doc_matrix = TermDocMatrixFromPandas(ConventionData2012().get_data(),
		                                          category_col='party',
		                                          text_col='text',
		                                          nlp=whitespace_nlp_with_sentences).build()
		term_freq_df = term_doc_matrix.get_term_freq_df()
		"""
        term_doc_mat = TermDocMatrixFromFrequencies(pd.DataFrame({'term': ['a', 'a b', 'a c', 'c', 'b', 'e b', 'e'], 'A freq': [6, 3, 3, 3, 5, 0, 0], 'B freq': [6, 3, 3, 3, 5, 1, 1]}).set_index('term')).build()
        new_tdm = CompactTerms(minimum_term_count=2).compact(term_doc_mat)
        self.assertEqual(term_doc_mat.get_terms(), ['a', 'a b', 'a c', 'c', 'b', 'e b', 'e'])
        self.assertEqual(set(new_tdm.get_terms()), set(term_doc_mat.get_terms()) - {'c', 'e b', 'e'})
        new_tdm = CompactTerms(minimum_term_count=1).compact(term_doc_mat)
        self.assertEqual(set(new_tdm.get_terms()), set(term_doc_mat.get_terms()) - {'c', 'e'})
        term_doc_mat = TermDocMatrixFromFrequencies(pd.DataFrame({'term': ['a', 'a b', 'b'], 'A freq': [5, 4, 8], 'B freq': [1, 1, 1]}).set_index('term')).build()
        self.assertEqual(set(CompactTerms(minimum_term_count=0, slack=0).compact(term_doc_mat).get_terms()), set(['a', 'a b', 'b']))
        self.assertEqual(set(CompactTerms(minimum_term_count=0, slack=2).compact(term_doc_mat).get_terms()), set(['b', 'a b']))

def test_get_term_indices_to_compact(self):
    """
		term_doc_matrix = TermDocMatrixFromPandas(ConventionData2012().get_data(),
		                                          category_col='party',
		                                          text_col='text',
		                                          nlp=whitespace_nlp_with_sentences).build()
		term_freq_df = term_doc_matrix.get_term_freq_df()
		"""
    term_doc_mat = TermDocMatrixFromFrequencies(pd.DataFrame({'term': ['a', 'a b', 'a c', 'c', 'b', 'e b', 'e'], 'A freq': [6, 3, 3, 3, 5, 0, 0], 'B freq': [6, 3, 3, 3, 5, 1, 1]}).set_index('term')).build()
    new_tdm = CompactTerms(minimum_term_count=2).compact(term_doc_mat)
    self.assertEqual(term_doc_mat.get_terms(), ['a', 'a b', 'a c', 'c', 'b', 'e b', 'e'])
    self.assertEqual(set(new_tdm.get_terms()), set(term_doc_mat.get_terms()) - {'c', 'e b', 'e'})
    new_tdm = CompactTerms(minimum_term_count=1).compact(term_doc_mat)
    self.assertEqual(set(new_tdm.get_terms()), set(term_doc_mat.get_terms()) - {'c', 'e'})
    term_doc_mat = TermDocMatrixFromFrequencies(pd.DataFrame({'term': ['a', 'a b', 'b'], 'A freq': [5, 4, 8], 'B freq': [1, 1, 1]}).set_index('term')).build()
    self.assertEqual(set(CompactTerms(minimum_term_count=0, slack=0).compact(term_doc_mat).get_terms()), set(['a', 'a b', 'b']))
    self.assertEqual(set(CompactTerms(minimum_term_count=0, slack=2).compact(term_doc_mat).get_terms()), set(['b', 'a b']))

def get_term_doc_matrix_without_categories():
    categories, documents = get_docs_categories()
    df = pd.DataFrame({'text': documents})
    tdm = TermDocMatrixWithoutCategoriesFromPandas(df, 'text', nlp=whitespace_nlp).build()
    return tdm

class TestCorpusFromPandasWithoutCategories(TestCase):

    def test_term_category_matrix_from_pandas_without_categories(self):
        tdm = get_term_doc_matrix_without_categories()
        categories, documents = get_docs_categories()
        reg_tdm = TermDocMatrixFromPandas(pd.DataFrame({'text': documents, 'categories': categories}), text_col='text', category_col='categories', nlp=whitespace_nlp).build()
        self.assertIsInstance(tdm, TermDocMatrixWithoutCategories)
        self.assertEqual(tdm.get_terms(), reg_tdm.get_terms())
        self.assertEqual(tdm.get_num_docs(), reg_tdm.get_num_docs())
        np.testing.assert_equal(tdm.get_term_doc_mat().data, reg_tdm.get_term_doc_mat().data)

def test_term_category_matrix_from_pandas_without_categories(self):
    tdm = get_term_doc_matrix_without_categories()
    categories, documents = get_docs_categories()
    reg_tdm = TermDocMatrixFromPandas(pd.DataFrame({'text': documents, 'categories': categories}), text_col='text', category_col='categories', nlp=whitespace_nlp).build()
    self.assertIsInstance(tdm, TermDocMatrixWithoutCategories)
    self.assertEqual(tdm.get_terms(), reg_tdm.get_terms())
    self.assertEqual(tdm.get_num_docs(), reg_tdm.get_num_docs())
    np.testing.assert_equal(tdm.get_term_doc_mat().data, reg_tdm.get_term_doc_mat().data)

def build_hamlet_jz_term_doc_mat():
    categories, documents = get_docs_categories()
    clean_function = lambda text: '' if text.startswith('[') else text
    term_doc_mat = TermDocMatrixFactory(category_text_iter=zip(categories, documents), clean_function=clean_function, nlp=whitespace_nlp).build()
    return term_doc_mat

def build_hamlet_jz_corpus():
    df = build_hamlet_jz_df()
    return CorpusFromParsedDocuments(df=df, category_col='category', parsed_col='parsed').build()

def build_hamlet_jz_df():
    categories, documents = get_docs_categories()
    clean_function = lambda text: '' if text.startswith('[') else text
    df = pd.DataFrame({'category': categories, 'parsed': [whitespace_nlp(clean_function(doc)) for doc in documents]})
    df = df[df['parsed'].apply(lambda x: len(str(x).strip()) > 0)]
    return df

def build_hamlet_jz_corpus_with_alt_text():
    df = build_hamlet_jz_df_with_alt_text()
    return CorpusFromParsedDocuments(df=df, category_col='category', parsed_col='parsed').build()

def build_hamlet_jz_df_with_alt_text():
    categories, documents = get_docs_categories()
    clean_function = lambda text: '' if text.startswith('[') else text
    df = pd.DataFrame({'category': categories, 'parsed': [whitespace_nlp(clean_function(doc)) for doc in documents], 'alt': [doc.upper() for doc in documents]})
    df = df[df['parsed'].apply(lambda x: len(str(x).strip()) > 0)]
    return df

def build_hamlet_jz_corpus_with_meta():

    def empath_mock(doc, **kwargs):
        toks = list(doc)
        num_toks = min(3, len(toks))
        return {'cat' + str(len(tok)): val for val, tok in enumerate(toks[:num_toks])}
    categories, documents = get_docs_categories()
    clean_function = lambda text: '' if text.startswith('[') else text
    df = pd.DataFrame({'category': categories, 'parsed': [whitespace_nlp(clean_function(doc)) for doc in documents]})
    df = df[df['parsed'].apply(lambda x: len(str(x).strip()) > 0)]
    return CorpusFromParsedDocuments(df=df, category_col='category', parsed_col='parsed', feats_from_spacy_doc=FeatsFromSpacyDocAndEmpath(empath_analyze_function=empath_mock)).build()

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

def test_build_censor_entities(self):
    categories, documents = get_docs_categories()
    clean_function = lambda text: '' if text.startswith('[') else text
    term_doc_mat = TermDocMatrixFactory(category_text_iter=zip(categories, documents), clean_function=clean_function, nlp=_testing_nlp, feats_from_spacy_doc=FeatsFromSpacyDoc(entity_types_to_censor=set(['GPE']))).build()
    self.assertIn('_GPE', set(term_doc_mat.get_term_freq_df().index))
    self.assertNotIn('brooklyn', set(term_doc_mat.get_term_freq_df().index))

class TestFeatsFromDoc(TestCase):

    def test_main(self):
        categories, documents = get_docs_categories()
        clean_function = lambda text: '' if text.startswith('[') else text
        entity_types = set(['GPE'])
        term_doc_mat = TermDocMatrixFactory(category_text_iter=zip(categories, documents), clean_function=clean_function, nlp=_testing_nlp, feats_from_spacy_doc=FeatsFromSpacyDoc(entity_types_to_censor=entity_types)).build()
        clf = PassiveAggressiveClassifier()
        fdc = FeatsFromDoc(term_doc_mat._term_idx_store, clean_function=clean_function, feats_from_spacy_doc=FeatsFromSpacyDoc(entity_types_to_censor=entity_types)).set_nlp(_testing_nlp)
        tfidf = TfidfTransformer(norm='l1')
        X = tfidf.fit_transform(term_doc_mat._X)
        clf.fit(X, term_doc_mat._y)
        X_to_predict = fdc.feats_from_doc('Did sometimes march UNKNOWNWORD')
        pred = clf.predict(tfidf.transform(X_to_predict))
        dec = clf.decision_function(X_to_predict)

def test_main(self):
    categories, documents = get_docs_categories()
    clean_function = lambda text: '' if text.startswith('[') else text
    entity_types = set(['GPE'])
    term_doc_mat = TermDocMatrixFactory(category_text_iter=zip(categories, documents), clean_function=clean_function, nlp=_testing_nlp, feats_from_spacy_doc=FeatsFromSpacyDoc(entity_types_to_censor=entity_types)).build()
    clf = PassiveAggressiveClassifier()
    fdc = FeatsFromDoc(term_doc_mat._term_idx_store, clean_function=clean_function, feats_from_spacy_doc=FeatsFromSpacyDoc(entity_types_to_censor=entity_types)).set_nlp(_testing_nlp)
    tfidf = TfidfTransformer(norm='l1')
    X = tfidf.fit_transform(term_doc_mat._X)
    clf.fit(X, term_doc_mat._y)
    X_to_predict = fdc.feats_from_doc('Did sometimes march UNKNOWNWORD')
    pred = clf.predict(tfidf.transform(X_to_predict))
    dec = clf.decision_function(X_to_predict)

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

def test_chinese_error(self):
    with self.assertRaises(Exception):
        CorpusFromPandas(self.df, 'category', 'text', nlp=chinese_nlp).build()

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

@classmethod
def setUp(cls):
    categories, documents = get_docs_categories()
    cls.df = pd.DataFrame({'category': categories, 'text': documents})
    cls.corpus = CorpusFromPandas(cls.df, 'category', 'text', nlp=whitespace_nlp).build()

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

class TestGensimPhraseAdder(TestCase):

    @classmethod
    def setUp(cls):
        cls.categories, cls.documents = get_docs_categories()
        cls.parsed_docs = []
        for doc in cls.documents:
            cls.parsed_docs.append(whitespace_nlp(doc))
        cls.df = pd.DataFrame({'category': cls.categories, 'author': ['a', 'a', 'c', 'c', 'c', 'c', 'd', 'd', 'e', 'e'], 'parsed': cls.parsed_docs, 'document_lengths': [len(doc) for doc in cls.documents]})
        cls.corpus = CorpusFromParsedDocuments(cls.df, 'category', 'parsed').build()

    def test_add_phrase(self):
        adder = GensimPhraseAdder()

@classmethod
def setUp(cls):
    cls.categories, cls.documents = get_docs_categories()
    cls.parsed_docs = []
    for doc in cls.documents:
        cls.parsed_docs.append(whitespace_nlp(doc))
    cls.df = pd.DataFrame({'category': cls.categories, 'author': ['a', 'a', 'c', 'c', 'c', 'c', 'd', 'd', 'e', 'e'], 'parsed': cls.parsed_docs, 'document_lengths': [len(doc) for doc in cls.documents]})
    cls.corpus = CorpusFromParsedDocuments(cls.df, 'category', 'parsed').build()

class TestWord2VecFromParsedCorpus(TestCase):

    @classmethod
    def setUp(cls):
        cls.categories, cls.documents = get_docs_categories()
        cls.parsed_docs = []
        for doc in cls.documents:
            cls.parsed_docs.append(whitespace_nlp(doc))
        cls.df = pd.DataFrame({'category': cls.categories, 'author': ['a', 'a', 'c', 'c', 'c', 'c', 'd', 'd', 'e', 'e'], 'parsed': cls.parsed_docs, 'document_lengths': [len(doc) for doc in cls.documents]})
        cls.corpus = CorpusFromParsedDocuments(cls.df, 'category', 'parsed').build()

    def test_make(self):
        gensim_is_present_and_working = False
        try:
            from gensim.models import word2vec
            gensim_is_present_and_working = True
        except:
            pass
        if gensim_is_present_and_working:
            Word2VecFromParsedCorpus(self.corpus)
            Word2VecFromParsedCorpus(self.corpus, word2vec.Word2Vec())

    def test_train(self):
        gensim_is_present_and_working = False
        try:
            from gensim.models import word2vec
            gensim_is_present_and_working = True
        except:
            pass
        if gensim_is_present_and_working:
            Word2VecFromParsedCorpus(self.corpus).train()

    def test_bigrams(self):
        gensim_is_present_and_working = False
        try:
            from gensim.models import word2vec
            gensim_is_present_and_working = True
        except:
            pass
        if gensim_is_present_and_working:
            Word2VecFromParsedCorpusBigrams(self.corpus).train()

@classmethod
def setUp(cls):
    cls.categories, cls.documents = get_docs_categories()
    cls.parsed_docs = []
    for doc in cls.documents:
        cls.parsed_docs.append(whitespace_nlp(doc))
    cls.df = pd.DataFrame({'category': cls.categories, 'author': ['a', 'a', 'c', 'c', 'c', 'c', 'd', 'd', 'e', 'e'], 'parsed': cls.parsed_docs, 'document_lengths': [len(doc) for doc in cls.documents]})
    cls.corpus = CorpusFromParsedDocuments(cls.df, 'category', 'parsed').build()

class TestOneClassScatterChart(TestCase):

    def test_main(self):
        df = build_hamlet_jz_df()

def test_main(self):
    df = build_hamlet_jz_df()

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

def __init__(self, inter_arrival_counts: InterArrivalCounts, verbose: bool=False, weibull_fit_func: Optional[Callable[[List[int]], object]]=None):
    self.__register_weibull_fit_funct(weibull_fit_func)
    self.inter_arrival_counts = inter_arrival_counts
    data, data_cat = self.__collect_term_and_cat_data(inter_arrival_counts, verbose)
    self.term_df = pd.DataFrame(data).set_index('term')
    self.term_cat_df = pd.DataFrame(data_cat).set_index('term')

def __get_term_iterator(self, verbose):
    it = self.inter_arrival_counts.corpus.get_terms(use_metadata=True)
    if verbose:
        it = tqdm(it)
    return it

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

def get_names(self):
    return self.corpus.get_terms(use_metadata=self.use_metadata) + self.absent_vocab

def get_category_dispersion(corpus: TermDocMatrix, metric: str, corpus_to_parts: Optional[Callable[['TermDocMatrix'], List]]=None, include_residual: bool=False, include_residual_regressor: Optional[object]=None, non_text: bool=False) -> pd.DataFrame:
    """

    :param corpus:  TermDocMatrix to process
    :param metric: a metric present in Dispersion.get_df. May be "DA".
    :param corpus_to_parts: Optional function which takes a TermDocMatrix and returns a list of parts of each doc. None indicates each doc is a separate part.
    :param non_text: Use non text features. False by default
    :param include_residual: Include the residual
    :param include_residual_regressor: Use a regressor for the residual computation
    :return: Dataframe giving category-specific features
    """
    data = {}
    for category in corpus.get_categories():
        category_corpus = corpus.remove_categories([c for c in corpus.get_categories() if c != category])
        if corpus_to_parts is not None:
            category_corpus = category_corpus.recategorize(corpus_to_parts)
        dispersion = Dispersion(category_corpus, non_text=non_text, use_categories_as_documents=corpus_to_parts is not None, vocabulary=corpus.get_terms(use_metadata=non_text), add_smoothing_part=True)
        dispersion_df = dispersion.get_df(include_da=metric == 'DA')
        data[category + '_Frequency'] = dispersion_df.Frequency
        data[category + '_' + metric] = dispersion_df[metric]
        if include_residual:
            residual_df = dispersion.get_adjusted_metric_df(metric=metric)
            data[f'{category}_{metric}_Residual'] = residual_df['Residual']
            data[f'{category}_{metric}_Estimate'] = residual_df['Estimate']
    return pd.DataFrame(data)

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

def make_component_digraph(self, graph_params, node_params):
    components = self.get_connected_components()
    return ComponentDiGraph(edge_df=self.edge_df.assign(Component=lambda df: components[df.source_id]), orig_edge_df=self.orig_edge_df.assign(Component=components[self.edge_df.source_id]), node_df=self.node_df.assign(Component=lambda df: components[df['index']]), id_node_df=self.id_node_df.assign(Component=lambda df: components[df.index]), components=components, graph_params=graph_params, node_params=node_params)

def get_connected_subgraph_df(self):
    return pd.DataFrame({'component': self.get_connected_components(), 'nodes': self.node_df['index'].values, 'values': self.node_df.index}).groupby('component').agg(list).assign(size=lambda df: df.nodes.apply(len)).sort_values(by='size', ascending=False).reset_index(drop=True)

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

def get_components_at_least_size(self, min_size):
    component_sizes = pd.DataFrame({'component': self.components}).reset_index().groupby('component')[['index']].apply(len).where(lambda x: x >= min_size).dropna()
    return np.array(component_sizes.sort_values(ascending=False).index)

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

def get_term_projection(self):
    if self.term_projection is None:
        dim_term = np.matmul(self.category_counts.values, self._get_x_y_projection())
    else:
        dim_term = self.term_projection
    df = pd.DataFrame(dim_term, index=self.category_corpus.get_terms(), columns=['x', 'y'])
    return df

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

def get_topic_weights_df(self, pipe=None) -> pd.DataFrame:
    pipe = self._fit_model(pipe)
    return pd.DataFrame(pipe._final_estimator.components_.T, index=self.corpus.get_terms(use_metadata=self.use_offsets))

def logmsg(s):
    print('[phrasemachine] %s' % s, file=sys.stderr)

def get_stdeng_spacy_tagger(suppress_errors=False):
    global SPACY_WRAPPER
    if SPACY_WRAPPER is not None:
        return SPACY_WRAPPER
    try:
        import spacy
        SPACY_WRAPPER = SpacyTagger()
        SPACY_WRAPPER.spacy_object = spacy.load('en_core_web_sm', parser=False, entity=False)
        return SPACY_WRAPPER
    except ImportError:
        if not suppress_errors:
            raise
    except RuntimeError:
        if not suppress_errors:
            raise
    return None

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

def _get_terms(self):
    return self.corpus_.get_terms(use_metadata=self.use_metadata_)

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

def _get_terms(self):
    return self.corpus_.get_terms(use_metadata=self.use_metadata_)

class OncePerDocFrequencyRanker(TermRanker):

    def get_ranks(self, label_append=' freq'):
        mat = self._corpus.get_term_count_mat(non_text=self._use_non_text_features)
        return self.get_ranks_from_mat(mat, label_append)

    def get_ranks_from_mat(self, mat, label_append=' freq'):
        return pd.DataFrame(mat, index=pd.Series(self._corpus.get_terms(use_metadata=self._use_non_text_features), name='term'), columns=[str(c) + label_append for c in self._corpus.get_categories()])

def get_ranks(self, label_append=' freq'):
    mat = self._corpus.get_term_count_mat(non_text=self._use_non_text_features)
    return self.get_ranks_from_mat(mat, label_append)

def get_ranks_from_mat(self, mat, label_append=' freq'):
    return pd.DataFrame(mat, index=pd.Series(self._corpus.get_terms(use_metadata=self._use_non_text_features), name='term'), columns=[str(c) + label_append for c in self._corpus.get_categories()])

class TermRanker:
    __metaclass__ = ABCMeta

    def __init__(self, term_doc_matrix: 'TermDocMatrix'):
        """Initialize TermRanker

		Parameters
		----------
		term_doc_matrix : TermDocMatrix
			TermDocMatrix from which to find term ranks.
		"""
        self._corpus = term_doc_matrix
        self._use_non_text_features = False

    def set_non_text(self, non_text: bool=True):
        self._use_non_text_features = non_text
        return self

    def use_non_text_features(self):
        """
		Returns
		-------
		TermRanker

		Side Effect
		-------
		Use use_non_text_features instead of text
		"""
        self._use_non_text_features = True
        return self

    def are_non_text_features_in_use(self):
        return self._use_non_text_features

    def get_term_doc_mat(self):
        """
		:return: term freq matrix or metadata freq matrix
		"""
        if self._use_non_text_features:
            return self._corpus._mX
        else:
            return self._corpus._X

    def get_terms(self):
        return self._corpus.get_terms(use_metadata=self._use_non_text_features)

    def _get_freq_df(self, X, label_append=' freq'):
        if self._use_non_text_features:
            return self._corpus._metadata_freq_df_from_matrix(X, label_append=label_append)
        else:
            return self._corpus._term_freq_df_from_matrix(X, label_append=label_append)

    def _get_row_category_ids(self):
        if self._use_non_text_features:
            return self._corpus._row_category_ids_for_meta()
        else:
            return self._corpus._row_category_ids()

    @abstractmethod
    def get_ranks(self, label_append=' freq'):
        pass

def get_terms(self):
    return self._corpus.get_terms(use_metadata=self._use_non_text_features)

