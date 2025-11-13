# Cluster 16

class DeployedClassifier:

    def __init__(self, target_category, category_idx_store, term_idx_store, entity_types_to_censor, use_lemmas, clean_function):
        """Not working

		Parameters
		----------
		target_category
		category_idx_store
		term_idx_store
		entity_types_to_censor
		use_lemmas
		clean_function
		"""
        self._target_category = target_category
        self._category_idx_store = category_idx_store
        self._term_idx_store = (term_idx_store,)
        self._entity_types_to_censor = entity_types_to_censor
        self._use_lemmas = use_lemmas
        self._clean_function = clean_function

    def classify(self, text, nlp):
        X, y = self._get_features_and_labels_from_documents_and_indexes(self._category_doc_iter, self._category_idx_store, self._term_idx_store)

def classify(self, text, nlp):
    X, y = self._get_features_and_labels_from_documents_and_indexes(self._category_doc_iter, self._category_idx_store, self._term_idx_store)

class CorpusDF(DataFrameCorpus):

    def __init__(self, df, X, mX, y, text_col, term_idx_store, category_idx_store, metadata_idx_store, unigram_frequency_path=None):
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
        text_col: np.array or pd.Series
            Raw texts
        unigram_frequency_path : str or None
            Path to term frequency file.
        """
        self._text_col = text_col
        DataFrameCorpus.__init__(self, X, mX, y, term_idx_store, category_idx_store, metadata_idx_store, df[text_col], df, unigram_frequency_path)

    def get_texts(self):
        """
        Returns
        -------
        pd.Series, all raw documents
        """
        return self._df[self._text_col]

    def _make_new_term_doc_matrix(self, new_X=None, new_mX=None, new_y=None, new_term_idx_store=None, new_category_idx_store=None, new_metadata_idx_store=None, new_y_mask=None, new_df=None):
        X, mX, y = self._update_X_mX_y(new_X, new_mX, new_y, new_y_mask)
        return CorpusDF(df=self._apply_mask_to_df(new_y_mask, new_df), X=X, mX=mX, y=y, term_idx_store=new_term_idx_store if new_term_idx_store is not None else self._term_idx_store, category_idx_store=new_category_idx_store if new_category_idx_store is not None else self._category_idx_store, metadata_idx_store=new_metadata_idx_store if new_metadata_idx_store is not None else self._metadata_idx_store, text_col=self._text_col, unigram_frequency_path=self._unigram_frequency_path)

def _make_new_term_doc_matrix(self, new_X=None, new_mX=None, new_y=None, new_term_idx_store=None, new_category_idx_store=None, new_metadata_idx_store=None, new_y_mask=None, new_df=None):
    X, mX, y = self._update_X_mX_y(new_X, new_mX, new_y, new_y_mask)
    return CorpusDF(df=self._apply_mask_to_df(new_y_mask, new_df), X=X, mX=mX, y=y, term_idx_store=new_term_idx_store if new_term_idx_store is not None else self._term_idx_store, category_idx_store=new_category_idx_store if new_category_idx_store is not None else self._category_idx_store, metadata_idx_store=new_metadata_idx_store if new_metadata_idx_store is not None else self._metadata_idx_store, text_col=self._text_col, unigram_frequency_path=self._unigram_frequency_path)

class CorpusFromPandas(TermDocMatrixFromPandas):
    """Creates a Corpus from a pandas data frame.  A Corpus is a Term Document Matrix
	preserves the original texts.

	Parameters
	----------
	data_frame : pd.DataFrame
		The data frame that contains columns for the category of interest
		and the document text.
	text_col : str
		The name of the column which contains the document text.
	category_col : str
		The name of the column which contains the category of interest.
	clean_function : function, optional
		A function that strips invalid characters out of the document text string, returning
		a new string.
	nlp : function, optional
	verbose : boolean, optional
		If true, prints a message every time a document index % 100 is 0.

	See Also
	--------
	TermDocMatrixFromPandas
	"""

    def _apply_pipeline_and_get_build_instance(self, X_factory, mX_factory, category_idx_store, df, parse_pipeline, term_idx_store, metadata_idx_store, y):
        """
		Parameters
		----------
		X_factory
		mX_factory
		category_idx_store
		df
		parse_pipeline
		term_idx_store
		metadata_idx_store
		y

		Returns
		-------
		CorpusDF
		"""
        df.apply(parse_pipeline.parse, axis=1)
        y = np.array(y)
        X, mX = build_sparse_matrices(y, X_factory, mX_factory)
        return CorpusDF(df, X, mX, y, self._text_col, term_idx_store, category_idx_store, metadata_idx_store)

def _apply_pipeline_and_get_build_instance(self, X_factory, mX_factory, category_idx_store, df, parse_pipeline, term_idx_store, metadata_idx_store, y):
    """
		Parameters
		----------
		X_factory
		mX_factory
		category_idx_store
		df
		parse_pipeline
		term_idx_store
		metadata_idx_store
		y

		Returns
		-------
		CorpusDF
		"""
    df.apply(parse_pipeline.parse, axis=1)
    y = np.array(y)
    X, mX = build_sparse_matrices(y, X_factory, mX_factory)
    return CorpusDF(df, X, mX, y, self._text_col, term_idx_store, category_idx_store, metadata_idx_store)

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

def _register_category(self, category, category_idx_store, y):
    y.append(category_idx_store.getidx(category))

def _get_features_from_parsed_text(self, parsed_text, term_idx_store):
    return {term_idx_store.getidxstrict(k): v for k, v in self._feats_from_spacy_doc.get_feats(parsed_text).items() if k in term_idx_store}

class FeatsFromDoc(TermDocMatrixFactory):

    def __init__(self, term_idx_store, clean_function=lambda x: x, nlp=None, feats_from_spacy_doc=None):
        """Class for extracting features from a new document.

       Parameters
       ----------
       term_idx_store : IndexStore (index -> term)
       clean_function : function (default lambda x: x)
           A function that takes a unicode document and returns
           a cleaned version of that document
       post_nlp_clean_function : function (default lambda x: x)
           A function that takes a spaCy Doc
       nlp : spacy parser (default None)
           The spaCy parser used to parse documents.  If it's None,
           the class will go through the expensive operation of
           creating one to parse the text
       feats_from_spacy_doc : FeatsFromSpacyDoc (default None)
           Class for extraction of features from spacy

       """
        TermDocMatrixFactory.__init__(self, clean_function=clean_function, nlp=nlp, feats_from_spacy_doc=feats_from_spacy_doc)
        self._term_idx_store = term_idx_store

    def feats_from_doc(self, raw_text):
        """
        Parameters
        ----------
        raw_text, uncleaned text for parsing out features

        Returns
        -------
        csr_matrix, feature matrix
        """
        parsed_text = self._nlp(self._clean_function(raw_text))
        X_factory = CSRMatrixFactory()
        X_factory.set_last_col_idx(self._term_idx_store.getnumvals() - 1)
        term_freq = self._get_features_from_parsed_text(parsed_text, self._term_idx_store)
        self._register_document_features_with_X_factory(X_factory, 0, term_freq)
        return X_factory.get_csr_matrix()

    def _augment_term_freq_with_unigrams_and_bigrams(self, bigrams, term_freq, term_idx_store, unigrams):
        for term in unigrams + bigrams:
            if term in term_idx_store:
                term_freq[term_idx_store.getidx(term)] += 1

def feats_from_doc(self, raw_text):
    """
        Parameters
        ----------
        raw_text, uncleaned text for parsing out features

        Returns
        -------
        csr_matrix, feature matrix
        """
    parsed_text = self._nlp(self._clean_function(raw_text))
    X_factory = CSRMatrixFactory()
    X_factory.set_last_col_idx(self._term_idx_store.getnumvals() - 1)
    term_freq = self._get_features_from_parsed_text(parsed_text, self._term_idx_store)
    self._register_document_features_with_X_factory(X_factory, 0, term_freq)
    return X_factory.get_csr_matrix()

def _augment_term_freq_with_unigrams_and_bigrams(self, bigrams, term_freq, term_idx_store, unigrams):
    for term in unigrams + bigrams:
        if term in term_idx_store:
            term_freq[term_idx_store.getidx(term)] += 1

def build_from_category_whitespace_delimited_text(category_text_iter):
    """

    Parameters
    ----------
    category_text_iter iterator of (string category name, one line per sentence, whitespace-delimited text) pairs

    Returns
    -------
    TermDocMatrix
    """
    y = []
    X_factory = CSRMatrixFactory()
    term_idx_store = IndexStore()
    category_idx_store = IndexStore()
    mX_factory = CSRMatrixFactory()
    for doci, (category, text) in enumerate(category_text_iter):
        y.append(category_idx_store.getidx(category))
        term_freq = Counter()
        for sent in text.strip(string.punctuation).lower().split('\n'):
            unigrams = []
            for tok in sent.strip().split():
                unigrams.append(tok)
            bigrams = list(map(' '.join, zip(unigrams[:-1], unigrams[1:])))
            for term in unigrams + bigrams:
                term_freq[term_idx_store.getidx(term)] += 1
        for word_idx, freq in term_freq.items():
            X_factory[doci, word_idx] = freq
    metadata_idx_store = IndexStore()
    return TermDocMatrix(X=X_factory.get_csr_matrix(), mX=mX_factory.get_csr_matrix(), y=np.array(y), term_idx_store=term_idx_store, metadata_idx_store=metadata_idx_store, category_idx_store=category_idx_store)

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

def list_extra_features(self, use_metadata: bool=True) -> List[Dict[str, str]]:
    """
        Returns
        -------
        List of dicts.  One dict for each document, keys are metadata, values are counts
        """
    return FeatureLister(self._get_relevant_X(use_metadata), self._get_relevant_idx_store(use_metadata), self.get_num_docs()).output()

def _get_X_after_delete_terms(self, idx_to_delete_list: List[int], non_text: bool=False) -> Tuple[csr_matrix, IndexStore]:
    new_term_idx_store = self._get_relevant_idx_store(non_text).batch_delete_idx(idx_to_delete_list)
    new_X = delete_columns(self._get_relevant_X(non_text), idx_to_delete_list)
    return (new_X, new_term_idx_store)

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

def get_document_ids_with_terms(self, terms: List[str], use_non_text_features: bool=False) -> np.array:
    return np.where(self._get_relevant_X(use_non_text_features)[:, [self._term_idx_store.getidx(x) for x in terms if x in self._term_idx_store]].sum(axis=1).A1 > 0)[0]

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

def _document_index_mask(self, feature: str, non_text: bool):
    term_idx_store = self.get_term_index_store(non_text=non_text)
    idx = term_idx_store.getidxstrict(feature.lower())
    mask = (self.get_term_doc_mat(non_text=non_text)[:, idx] > 0).todense().A1
    return mask

class CSRMatrixFactory:
    """ Factory class to create a csr_matrix.
	"""

    def __init__(self, dtype=np.int32):
        self.rows = []
        self.cols = []
        self.data = []
        self._max_col = 0
        self._max_row = 0
        self._dtype = dtype

    def __setitem__(self, row_col, datum):
        """Insert a value into the matrix

		Parameters
		----------
		row_col : tuple
			Row and column indices
		datum : float or int
			Numeric value to insert into the matrix


		>>> mat_fact = CSRMatrixFactory()
		>>> mat_fact[3,1] = 1
		>>> mat_fact[3,1] = 1
		>>> mat_fact.get_csr_matrix().todense()
		matrix([[0, 0],
			[0, 0],
			[0, 0],
			[0, 2]], dtype=int32)


		Returns
		-------
		None
		"""
        row, col = row_col
        self.rows.append(row)
        self.cols.append(col)
        self.data.append(datum)
        if row > self._max_row:
            self._max_row = row
        if col > self._max_col:
            self._max_col = col
        if isinstance(datum, float):
            self._dtype = type(datum)

    def set_last_col_idx(self, last_col_idx):
        """
		Parameters
		----------
		param last_col_idx : int
			number of columns
		"""
        assert last_col_idx >= self._max_col
        self._max_col = last_col_idx
        return self

    def set_last_row_idx(self, last_row_idx):
        """
		Parameters
		----------
		param last_row_idx : int
			number of rows
		"""
        assert last_row_idx >= self._max_row
        self._max_row = last_row_idx
        return self

    def get_csr_matrix(self, dtype=None, make_square=False):
        shape = (self._max_row + 1, self._max_col + 1)
        if make_square:
            shape = (max(shape), max(shape))
        return csr_matrix((self.data, (self.rows, self.cols)), shape=shape, dtype=self._dtype if dtype is None else dtype)

def get_csr_matrix(self, dtype=None, make_square=False):
    shape = (self._max_row + 1, self._max_col + 1)
    if make_square:
        shape = (max(shape), max(shape))
    return csr_matrix((self.data, (self.rows, self.cols)), shape=shape, dtype=self._dtype if dtype is None else dtype)

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

def _change_document_type_in_matrix(self, X, new_doc_ids):
    new_data = self._make_all_positive_data_ones(X.data)
    newX = csr_matrix((new_data, (new_doc_ids, X.indices)))
    return newX

def _make_new_term_doc_matrix(self, new_X=None, new_mX=None, new_y=None, new_term_idx_store=None, new_category_idx_store=None, new_metadata_idx_store=None, new_y_mask=None):
    X, mX, y = self._update_X_mX_y(new_X, new_mX, new_y, new_y_mask)
    return TermDocMatrix(X=X, mX=mX, y=y, term_idx_store=new_term_idx_store if new_term_idx_store is not None else self._term_idx_store, category_idx_store=new_category_idx_store if new_category_idx_store is not None else self._category_idx_store, metadata_idx_store=new_metadata_idx_store if new_metadata_idx_store is not None else self._metadata_idx_store, unigram_frequency_path=self._unigram_frequency_path)

def _get_mask_from_category(self, category):
    return self._y == self._category_idx_store.getidx(category)

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

def _categories_to_metadata_factory(self):
    new_metadata_factory = CSRMatrixFactory()
    for i, category_idx in enumerate(self.get_category_ids()):
        new_metadata_factory[i, category_idx] = 1
    new_metadata = new_metadata_factory.get_csr_matrix()
    return new_metadata

class TermDocMatrixFromScikit(object):
    """
	A factory class for building a TermDocMatrix from a scikit-learn-processed
	dataset.

	>>> from scattertext import TermDocMatrixFromScikit
	>>> from sklearn.datasets import fetch_20newsgroups
	>>> from sklearn.feature_extraction.text import CountVectorizer
	>>> newsgroups_train = fetch_20newsgroups(subset='train', remove=('headers', 'footers', 'quotes'))
	>>> count_vectorizer = CountVectorizer()
	>>> X_counts = count_vectorizer.fit_transform(newsgroups_train.data)
	>>> term_doc_mat = TermDocMatrixFromScikit(
	...   X = X_counts,
	...   y = newsgroups_train.target,
	...   feature_vocabulary=count_vectorizer.vocabulary_,
	...   category_names=newsgroups_train.target_names
	... ).build()
	>>> term_doc_mat.get_categories()[:2]
	['alt.atheism', 'comp.graphics']
	>>> term_doc_mat.get_term_freq_df().assign(score=term_doc_mat.get_scaled_f_scores('alt.atheism')).sort_values(by='score', ascending=False).index.tolist()[:5]
	['atheism', 'atheists', 'islam', 'atheist', 'matthew']
	"""

    def __init__(self, X, y, feature_vocabulary, category_names, unigram_frequency_path=None):
        """
		Parameters
		----------
		X: sparse matrix integer, giving term-document-matrix counts
		y: list, integer categories
		feature_vocabulary: dict (feat_name -> idx)
		category_names: list of category names (len of y)
		unigram_frequency_path: str (see TermDocMatrix)
		"""
        if X.shape != (len(y), len(feature_vocabulary)):
            raise DimensionMismatchException('The shape of X is expected to be ' + str((len(y), len(feature_vocabulary))) + 'but was actually: ' + str(X.shape))
        self.X = X
        self.y = y
        self.feature_vocabulary = feature_vocabulary
        self.category_names = category_names
        self.unigram_frequency_path = unigram_frequency_path

    def build(self):
        """
		Returns
		-------
		TermDocMatrix
		"""
        constructor_kwargs = self._get_build_kwargs()
        return TermDocMatrix(**constructor_kwargs)

    def _get_build_kwargs(self):
        constructor_kwargs = {'X': self.X, 'mX': csr_matrix((0, 0)), 'y': self.y, 'term_idx_store': IndexStoreFromDict.build(self.feature_vocabulary), 'metadata_idx_store': IndexStore(), 'category_idx_store': IndexStoreFromList.build(self.category_names), 'unigram_frequency_path': self.unigram_frequency_path}
        return constructor_kwargs

def build(self):
    """
		Returns
		-------
		TermDocMatrix
		"""
    constructor_kwargs = self._get_build_kwargs()
    return TermDocMatrix(**constructor_kwargs)

def _get_build_kwargs(self):
    constructor_kwargs = {'X': self.X, 'mX': csr_matrix((0, 0)), 'y': self.y, 'term_idx_store': IndexStoreFromDict.build(self.feature_vocabulary), 'metadata_idx_store': IndexStore(), 'category_idx_store': IndexStoreFromList.build(self.category_names), 'unigram_frequency_path': self.unigram_frequency_path}
    return constructor_kwargs

class ParsePipelineFactoryWithoutCategories(object):

    def __init__(self, nlp, X_factory, mX_factory, term_idx_store, metadata_idx_store, term_doc_mat_fact):
        if nlp == chinese_nlp:
            raise Exception('Chinese NLP not yet supported.  Preparse chinese documents, and use CorpusFromParsedDocuments or a similar class.')
        self.X_factory, self.mX_factory, self.term_idx_store, self.metadata_idx_store, self.nlp = (X_factory, mX_factory, term_idx_store, metadata_idx_store, nlp)
        self._term_doc_mat_fact = term_doc_mat_fact
        self._text_col = self._term_doc_mat_fact._text_col
        self._clean_function = self._term_doc_mat_fact._clean_function
        self._verbose = self._term_doc_mat_fact._verbose

    def parse(self, row):
        cleaned_text = self._clean_function(self._get_raw_text_from_row(row))
        parsed_text = self.nlp(cleaned_text)
        if self._verbose and row.name % 100:
            print(row.name)
        self._register_document(parsed_text, row)

    def _get_raw_text_from_row(self, row):
        return row[self._text_col]

    def _register_document(self, parsed_text, row):
        self._term_doc_mat_fact._register_doc(X_factory=self.X_factory, mX_factory=self.mX_factory, document_index=row.name, parsed_text=parsed_text, term_idx_store=self.term_idx_store, metadata_idx_store=self.metadata_idx_store)
        for term, val in self._term_doc_mat_fact._feats_from_spacy_doc.get_row_metadata(parsed_text, row).items():
            self.mX_factory[row.name, self.metadata_idx_store.getidx(term)] = val

def parse(self, row):
    cleaned_text = self._clean_function(self._get_raw_text_from_row(row))
    parsed_text = self.nlp(cleaned_text)
    if self._verbose and row.name % 100:
        print(row.name)
    self._register_document(parsed_text, row)

def _register_document(self, parsed_text, row):
    self._term_doc_mat_fact._register_doc(X_factory=self.X_factory, mX_factory=self.mX_factory, document_index=row.name, parsed_text=parsed_text, term_idx_store=self.term_idx_store, metadata_idx_store=self.metadata_idx_store)
    for term, val in self._term_doc_mat_fact._feats_from_spacy_doc.get_row_metadata(parsed_text, row).items():
        self.mX_factory[row.name, self.metadata_idx_store.getidx(term)] = val

class ParsePipelineFactory(ParsePipelineFactoryWithoutCategories):

    def __init__(self, nlp, X_factory, mX_factory, category_idx_store, term_idx_store, metadata_idx_store, y, term_doc_mat_fact):
        ParsePipelineFactoryWithoutCategories.__init__(self, nlp, X_factory, mX_factory, term_idx_store, metadata_idx_store, term_doc_mat_fact)
        self._register_doc_and_category = self._term_doc_mat_fact._register_doc_and_category
        self._category_col = self._term_doc_mat_fact._category_col
        self.category_idx_store = category_idx_store
        self.y = y

    def _register_document(self, parsed_text, row):
        self._register_doc_and_category(X_factory=self.X_factory, mX_factory=self.mX_factory, category=str(row[self._category_col]), category_idx_store=self.category_idx_store, document_index=row.name, parsed_text=parsed_text, term_idx_store=self.term_idx_store, metadata_idx_store=self.metadata_idx_store, y=self.y)

def _register_document(self, parsed_text, row):
    self._register_doc_and_category(X_factory=self.X_factory, mX_factory=self.mX_factory, category=str(row[self._category_col]), category_idx_store=self.category_idx_store, document_index=row.name, parsed_text=parsed_text, term_idx_store=self.term_idx_store, metadata_idx_store=self.metadata_idx_store, y=self.y)

def build_sparse_matrices_with_num_docs(num_docs, X_factory, mX_factory):
    return (X_factory.set_last_row_idx(num_docs - 1).get_csr_matrix(), mX_factory.set_last_row_idx(num_docs - 1).get_csr_matrix())

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

class CorpusFactoryHelper(object):

    @staticmethod
    def init_term_doc_matrix_variables():
        y = []
        X_factory = CSRMatrixFactory()
        mX_factory = CSRMatrixFactory()
        category_idx_store = IndexStore()
        term_idx_store = IndexStore()
        metadata_idx_store = IndexStore()
        return (X_factory, mX_factory, category_idx_store, term_idx_store, metadata_idx_store, y)

@staticmethod
def init_term_doc_matrix_variables():
    y = []
    X_factory = CSRMatrixFactory()
    mX_factory = CSRMatrixFactory()
    category_idx_store = IndexStore()
    term_idx_store = IndexStore()
    metadata_idx_store = IndexStore()
    return (X_factory, mX_factory, category_idx_store, term_idx_store, metadata_idx_store, y)

class CorpusFromTermFrequencies(object):

    def __init__(self, X: csr_matrix, term_vocabulary: List[str], mX: Optional[csr_matrix]=None, y: Optional[np.array]=None, category_names: Optional[str]=None, metadata_vocabulary: Optional[List[str]]=None, text_df: Optional[pd.DataFrame]=None, text_col: Optional[str]=None, parsed_col: Optional[str]=None, category_col: Optional[str]=None, unigram_frequency_path: Optional[str]=None):
        """
        Parameters
        ----------
        X: csr_matrix; term-document frequency matrix; columns represent terms and rows documents
        term_vocabulary: List[str]; Each entry corresponds to a term
        mX: Optional[csr_matrix]; metadata csr matrix
        y: Optional[np.array[int]]; indices of category names for each document
        category_names: Optional[List[str]], names of categories for y
        text_df: pd.DataFrame with a row containing the raw document text
        text_col: str; name of row containing the text of each document
        parsed_col: str; name of row containing the parsed text of each document
        unigram_frequency_path: str (see TermDocMatrix)

        """
        self.X = X
        self.term_idx_store = IndexStoreFromList.build(term_vocabulary)
        assert self.X.shape[1] == len(term_vocabulary)
        self.metadata_idx_store = IndexStore()
        if y is None:
            self.y = np.zeros(self.X.shape[0], dtype=int)
            self.category_idx_store = IndexStoreFromList.build(['_'])
            assert category_names is None
        else:
            self.y = y
            assert len(category_names) == len(set(y))
            self.category_idx_store = IndexStoreFromList.build(category_names)
        if metadata_vocabulary is not None:
            assert mX.shape[1] == metadata_vocabulary
            self.mX = mX
            self.metadata_idx_store = IndexStoreFromList.build(metadata_vocabulary)
        else:
            assert metadata_vocabulary is None
            self.mX = csr_matrix((0, 0))
            self.metadata_idx_store = IndexStore()
        self.text_df = text_df
        if parsed_col is not None:
            assert parsed_col in text_df
        if text_col is not None:
            assert text_col in text_df
        if category_col is not None:
            assert category_col in text_df
        self.category_col = category_col
        self.text_col = text_col
        self.parsed_col = parsed_col
        self.unigram_frequency_path = unigram_frequency_path

    def build(self):
        """
        Returns
        -------
        CorpusDF
        """
        if self.text_df is not None:
            if self.parsed_col is not None:
                if self.category_col is None:
                    self.text_df = self.text_df.assign(Category=self.category_idx_store.getvalbatch(self.y))
                    self.category_col = 'Category'
                return ParsedCorpus(df=self.text_df, X=self.X, mX=self.mX, y=self.y, parsed_col=self.parsed_col, term_idx_store=self.term_idx_store, category_idx_store=self.category_idx_store, metadata_idx_store=self.metadata_idx_store, unigram_frequency_path=self.unigram_frequency_path, category_col=self.category_col)
            elif self.text_col is not None:
                return CorpusDF(df=self.text_df, X=self.X, mX=self.mX, y=self.y, text_col=self.text_col, term_idx_store=self.term_idx_store, category_idx_store=self.category_idx_store, metadata_idx_store=self.metadata_idx_store, unigram_frequency_path=self.unigram_frequency_path)
        return TermDocMatrix(X=self.X, mX=self.mX, y=self.y, term_idx_store=self.term_idx_store, category_idx_store=self.category_idx_store, metadata_idx_store=self.metadata_idx_store, unigram_frequency_path=self.unigram_frequency_path)

def __init__(self, X: csr_matrix, term_vocabulary: List[str], mX: Optional[csr_matrix]=None, y: Optional[np.array]=None, category_names: Optional[str]=None, metadata_vocabulary: Optional[List[str]]=None, text_df: Optional[pd.DataFrame]=None, text_col: Optional[str]=None, parsed_col: Optional[str]=None, category_col: Optional[str]=None, unigram_frequency_path: Optional[str]=None):
    """
        Parameters
        ----------
        X: csr_matrix; term-document frequency matrix; columns represent terms and rows documents
        term_vocabulary: List[str]; Each entry corresponds to a term
        mX: Optional[csr_matrix]; metadata csr matrix
        y: Optional[np.array[int]]; indices of category names for each document
        category_names: Optional[List[str]], names of categories for y
        text_df: pd.DataFrame with a row containing the raw document text
        text_col: str; name of row containing the text of each document
        parsed_col: str; name of row containing the parsed text of each document
        unigram_frequency_path: str (see TermDocMatrix)

        """
    self.X = X
    self.term_idx_store = IndexStoreFromList.build(term_vocabulary)
    assert self.X.shape[1] == len(term_vocabulary)
    self.metadata_idx_store = IndexStore()
    if y is None:
        self.y = np.zeros(self.X.shape[0], dtype=int)
        self.category_idx_store = IndexStoreFromList.build(['_'])
        assert category_names is None
    else:
        self.y = y
        assert len(category_names) == len(set(y))
        self.category_idx_store = IndexStoreFromList.build(category_names)
    if metadata_vocabulary is not None:
        assert mX.shape[1] == metadata_vocabulary
        self.mX = mX
        self.metadata_idx_store = IndexStoreFromList.build(metadata_vocabulary)
    else:
        assert metadata_vocabulary is None
        self.mX = csr_matrix((0, 0))
        self.metadata_idx_store = IndexStore()
    self.text_df = text_df
    if parsed_col is not None:
        assert parsed_col in text_df
    if text_col is not None:
        assert text_col in text_df
    if category_col is not None:
        assert category_col in text_df
    self.category_col = category_col
    self.text_col = text_col
    self.parsed_col = parsed_col
    self.unigram_frequency_path = unigram_frequency_path

def build(self):
    """
        Returns
        -------
        CorpusDF
        """
    if self.text_df is not None:
        if self.parsed_col is not None:
            if self.category_col is None:
                self.text_df = self.text_df.assign(Category=self.category_idx_store.getvalbatch(self.y))
                self.category_col = 'Category'
            return ParsedCorpus(df=self.text_df, X=self.X, mX=self.mX, y=self.y, parsed_col=self.parsed_col, term_idx_store=self.term_idx_store, category_idx_store=self.category_idx_store, metadata_idx_store=self.metadata_idx_store, unigram_frequency_path=self.unigram_frequency_path, category_col=self.category_col)
        elif self.text_col is not None:
            return CorpusDF(df=self.text_df, X=self.X, mX=self.mX, y=self.y, text_col=self.text_col, term_idx_store=self.term_idx_store, category_idx_store=self.category_idx_store, metadata_idx_store=self.metadata_idx_store, unigram_frequency_path=self.unigram_frequency_path)
    return TermDocMatrix(X=self.X, mX=self.mX, y=self.y, term_idx_store=self.term_idx_store, category_idx_store=self.category_idx_store, metadata_idx_store=self.metadata_idx_store, unigram_frequency_path=self.unigram_frequency_path)

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

def _make_new_term_doc_matrix(self, new_X=None, new_mX=None, new_y=None, new_term_idx_store=None, new_category_idx_store=None, new_metadata_idx_store=None, new_y_mask=None, new_df=None):
    X, mX, y = self._update_X_mX_y(new_X, new_mX, new_y, new_y_mask)
    return ParsedCorpus(X=X, mX=mX, y=y, parsed_col=self._parsed_col, category_col=self._category_col, term_idx_store=new_term_idx_store if new_term_idx_store is not None else self._term_idx_store, category_idx_store=new_category_idx_store if new_category_idx_store is not None else self._category_idx_store, metadata_idx_store=new_metadata_idx_store if new_metadata_idx_store is not None else self._metadata_idx_store, df=self._apply_mask_to_df(new_y_mask, new_df), unigram_frequency_path=self._unigram_frequency_path)

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

def _make_new_term_doc_matrix(self, new_X=None, new_mX=None, new_y=None, new_term_idx_store=None, new_category_idx_store=None, new_metadata_idx_store=None, new_y_mask=None, new_df=None, new_term_offsets=None, new_metadata_offsets=None):
    X, mX, y = self._update_X_mX_y(new_X, new_mX, new_y, new_y_mask)
    metadata_offsets, term_offsets = self._update_offsets(new_metadata_idx_store=new_metadata_idx_store, new_metadata_offsets=new_metadata_offsets, new_term_idx_store=new_term_idx_store, new_term_offsets=new_term_offsets)
    return OffsetCorpus(X=X, mX=mX, y=y, parsed_col=self._parsed_col, category_col=self._category_col, term_idx_store=new_term_idx_store if new_term_idx_store is not None else self._term_idx_store, category_idx_store=new_category_idx_store if new_category_idx_store is not None else self._category_idx_store, metadata_idx_store=new_metadata_idx_store if new_metadata_idx_store is not None else self._metadata_idx_store, df=self._apply_mask_to_df(new_y_mask, new_df), term_offsets=term_offsets, metadata_offsets=metadata_offsets, unigram_frequency_path=self._unigram_frequency_path)

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

class TermDocMatrixFromFrequencies(object):
    """
	A factory class for building a TermDocMatrix from a set of term-category frequencies.

	Note: the TermDocMatrix will assume that only K documents exist, where
	K is the number of categories.

	>>> from scattertext import TermDocMatrixFromFrequencies
	>>> from pandas import DataFrame
	>>> term_freq_df = DataFrame({
	...     'term': ['a', 'a b', 'a c', 'c', 'b', 'e b', 'e'],
	...     'A': [6, 3, 3, 3, 5, 0, 0],
	...     'B': [6, 3, 3, 3, 5, 1, 1],
	... }).set_index('term')[['A', 'B']]
	>>> term_doc_mat = TermDocMatrixFromFrequencies(term_freq_df).build()
	>>> term_doc_mat.get_categories()
	['A', 'B']
	>>> term_doc_mat.get_terms()
	['a', 'a b', 'a c', 'c', 'b', 'e b', 'e']
	"""

    def __init__(self, term_freq_df, unigram_frequency_path=None):
        """
		Parameters
		----------
		term_freq_df: DataFrame
			Indexed on term, columns are counts per category
		unigram_frequency_path: str (see TermDocMatrix)
		"""
        self.term_freq_df = term_freq_df
        self.unigram_frequency_path = unigram_frequency_path

    def build(self):
        """
		Returns
		-------
		TermDocMatrix
		"""
        constructor_kwargs = self._get_build_kwargs()
        return TermDocMatrix(**constructor_kwargs)

    def _get_build_kwargs(self):
        constructor_kwargs = {'X': csr_matrix(self.term_freq_df.values.T), 'mX': csr_matrix((0, 0)), 'y': np.array(range(len(self.term_freq_df.columns))), 'term_idx_store': IndexStoreFromList.build(self.term_freq_df.index.values), 'metadata_idx_store': IndexStore(), 'category_idx_store': IndexStoreFromList.build([str(x) for x in self.term_freq_df.columns]), 'unigram_frequency_path': self.unigram_frequency_path}
        return constructor_kwargs

def build(self):
    """
		Returns
		-------
		TermDocMatrix
		"""
    constructor_kwargs = self._get_build_kwargs()
    return TermDocMatrix(**constructor_kwargs)

def _get_build_kwargs(self):
    constructor_kwargs = {'X': csr_matrix(self.term_freq_df.values.T), 'mX': csr_matrix((0, 0)), 'y': np.array(range(len(self.term_freq_df.columns))), 'term_idx_store': IndexStoreFromList.build(self.term_freq_df.index.values), 'metadata_idx_store': IndexStore(), 'category_idx_store': IndexStoreFromList.build([str(x) for x in self.term_freq_df.columns]), 'unigram_frequency_path': self.unigram_frequency_path}
    return constructor_kwargs

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

class ScikitSupervisedCompactor(object):

    def __init__(self, pipeline):
        """

		Parameters
		----------
		pipeline : Pipeline
			sklearn.pipeline.Pipeline instance
		"""
        self.pipeline = pipeline

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

class TestCSRMatrixFactory(TestCase):

    def test_main(self):
        mat_factory = CSRMatrixFactory()
        mat_factory[0, 0] = 4
        mat_factory[1, 5] = 3
        mat = mat_factory.get_csr_matrix()
        self.assertEqual(type(mat), csr_matrix)
        np.testing.assert_array_almost_equal(np.array([[4, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 3]]), mat.todense())

    def test_delete_row(self):
        a = csr_matrix(np.array([[0, 1, 3, 0, 1, 0], [0, 0, 1, 0, 1, 1], [0, 5, 1, 0, 5, 5]]))
        b = scattertext.CSRMatrixTools.delete_columns(a, [0, 3])
        desired_array = np.array([[1, 3, 1, 0], [0, 1, 1, 1], [5, 1, 5, 5]])
        self.assertEqual(type(b), csr_matrix)
        np.testing.assert_array_almost_equal(b.todense(), desired_array)
        self.assertEqual(a.shape, (3, 6))

    def test_typing(self):
        mat_factory = CSRMatrixFactory()
        mat_factory[0, 0] = 4
        mat_factory[1, 5] = 3.1
        mat = mat_factory.get_csr_matrix()
        self.assertEqual(type(mat), csr_matrix)
        np.testing.assert_array_almost_equal(np.array([[4, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 3.1]]), mat.todense())
        mat = mat_factory.get_csr_matrix(dtype=bool)
        self.assertEqual(type(mat), csr_matrix)
        np.testing.assert_array_almost_equal(np.array([[1, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 1]]), mat.todense())
        mat = mat_factory.get_csr_matrix(dtype=np.int32)
        self.assertEqual(type(mat), csr_matrix)
        np.testing.assert_array_almost_equal(np.array([[4, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 3]]), mat.todense())

def test_main(self):
    mat_factory = CSRMatrixFactory()
    mat_factory[0, 0] = 4
    mat_factory[1, 5] = 3
    mat = mat_factory.get_csr_matrix()
    self.assertEqual(type(mat), csr_matrix)
    np.testing.assert_array_almost_equal(np.array([[4, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 3]]), mat.todense())

def test_delete_row(self):
    a = csr_matrix(np.array([[0, 1, 3, 0, 1, 0], [0, 0, 1, 0, 1, 1], [0, 5, 1, 0, 5, 5]]))
    b = scattertext.CSRMatrixTools.delete_columns(a, [0, 3])
    desired_array = np.array([[1, 3, 1, 0], [0, 1, 1, 1], [5, 1, 5, 5]])
    self.assertEqual(type(b), csr_matrix)
    np.testing.assert_array_almost_equal(b.todense(), desired_array)
    self.assertEqual(a.shape, (3, 6))

def test_typing(self):
    mat_factory = CSRMatrixFactory()
    mat_factory[0, 0] = 4
    mat_factory[1, 5] = 3.1
    mat = mat_factory.get_csr_matrix()
    self.assertEqual(type(mat), csr_matrix)
    np.testing.assert_array_almost_equal(np.array([[4, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 3.1]]), mat.todense())
    mat = mat_factory.get_csr_matrix(dtype=bool)
    self.assertEqual(type(mat), csr_matrix)
    np.testing.assert_array_almost_equal(np.array([[1, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 1]]), mat.todense())
    mat = mat_factory.get_csr_matrix(dtype=np.int32)
    self.assertEqual(type(mat), csr_matrix)
    np.testing.assert_array_almost_equal(np.array([[4, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 3]]), mat.todense())

class TestIndexStoreFromList(TestCase):

    def test_index_store_from_dict(self):
        values = ['a', 'b', 'c']
        idxstore = IndexStoreFromList.build(values)
        for idx, term in enumerate(values):
            self.assertEqual(idxstore.getidx(term), idx)
        self.assertEqual(idxstore._next_i, len(values))

def test_index_store_from_dict(self):
    values = ['a', 'b', 'c']
    idxstore = IndexStoreFromList.build(values)
    for idx, term in enumerate(values):
        self.assertEqual(idxstore.getidx(term), idx)
    self.assertEqual(idxstore._next_i, len(values))

class TestIndexStoreFromDict(TestCase):

    def test_index_store_from_dict(self):
        vocab = {'baloney': 0, 'by': 1, 'first': 2, 'has': 3, 'it': 4, 'meyer': 5, 'my': 6, 'name': 7, 'oscar': 8, 'second': 9}
        idxstore = IndexStoreFromDict.build(vocab)
        for term, idx in vocab.items():
            self.assertEqual(idxstore.getidx(term), idx)
        self.assertEqual(idxstore.getnumvals(), len(vocab))

def test_index_store_from_dict(self):
    vocab = {'baloney': 0, 'by': 1, 'first': 2, 'has': 3, 'it': 4, 'meyer': 5, 'my': 6, 'name': 7, 'oscar': 8, 'second': 9}
    idxstore = IndexStoreFromDict.build(vocab)
    for term, idx in vocab.items():
        self.assertEqual(idxstore.getidx(term), idx)
    self.assertEqual(idxstore.getnumvals(), len(vocab))

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

def assert_word_in_doc_cnt(doc, word, count):
    self.assertEqual(corpus._X[doc, corpus._term_idx_store.getidx(word)], count)

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

class TestFeatureList(TestCase):

    def test_main(self):
        tdm = build_hamlet_jz_corpus_with_meta()
        features = FeatureLister(tdm._mX, tdm._metadata_idx_store, tdm.get_num_docs()).output()
        expected = [{'cat4': 2, 'cat3': 1}, {'cat4': 2}, {'cat5': 1, 'cat3': 2}, {'cat6': 2, 'cat9': 1}, {'cat4': 2, 'cat3': 1}, {'cat2': 1, 'cat1': 2}, {'cat2': 2, 'cat5': 1}, {'cat4': 1, 'cat3': 2}]
        expected = [{'cat1': 2}, {'cat1': 2}, {'cat1': 2}, {'cat1': 2}, {'cat1': 2}, {'cat1': 2}, {'cat1': 2}, {'cat1': 2}]
        self.assertEqual(features, expected)

def test_main(self):
    tdm = build_hamlet_jz_corpus_with_meta()
    features = FeatureLister(tdm._mX, tdm._metadata_idx_store, tdm.get_num_docs()).output()
    expected = [{'cat4': 2, 'cat3': 1}, {'cat4': 2}, {'cat5': 1, 'cat3': 2}, {'cat6': 2, 'cat9': 1}, {'cat4': 2, 'cat3': 1}, {'cat2': 1, 'cat1': 2}, {'cat2': 2, 'cat5': 1}, {'cat4': 1, 'cat3': 2}]
    expected = [{'cat1': 2}, {'cat1': 2}, {'cat1': 2}, {'cat1': 2}, {'cat1': 2}, {'cat1': 2}, {'cat1': 2}, {'cat1': 2}]
    self.assertEqual(features, expected)

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

def __contains__(self, val: Any) -> bool:
    return self._hasval(val)

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

class DocLengthDividedFrequencyRanker(DocLengthNormalizedFrequencyRanker):

    def _get_normalized_X(self, X, doc_lengths):
        return csr_matrix(X.astype(np.float32) / doc_lengths)

def _get_normalized_X(self, X, doc_lengths):
    return csr_matrix(X.astype(np.float32) / doc_lengths)

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

def _get_freq_df(self, X, label_append=' freq'):
    if self._use_non_text_features:
        return self._corpus._metadata_freq_df_from_matrix(X, label_append=label_append)
    else:
        return self._corpus._term_freq_df_from_matrix(X, label_append=label_append)

