# Cluster 11

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

def __init__(self, corpus, max_per_category, alternative_text_field=None, seed=None):
    DocsAndLabelsFromCorpus.__init__(self, corpus, alternative_text_field)
    self.max_per_category = max_per_category
    if seed is not None:
        np.random.seed(seed)

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

def __init__(self, corpus, verbose=False, **kwargs):
    """See ScatterChart.  This lets you click on terms to see what contexts they tend to appear in.
        Running the `to_dict` function outputs
        """
    ScatterChart.__init__(self, corpus, verbose, **kwargs)
    self._term_metadata = None

class ParsePipelineFactory(ParsePipelineFactoryWithoutCategories):

    def __init__(self, nlp, X_factory, mX_factory, category_idx_store, term_idx_store, metadata_idx_store, y, term_doc_mat_fact):
        ParsePipelineFactoryWithoutCategories.__init__(self, nlp, X_factory, mX_factory, term_idx_store, metadata_idx_store, term_doc_mat_fact)
        self._register_doc_and_category = self._term_doc_mat_fact._register_doc_and_category
        self._category_col = self._term_doc_mat_fact._category_col
        self.category_idx_store = category_idx_store
        self.y = y

    def _register_document(self, parsed_text, row):
        self._register_doc_and_category(X_factory=self.X_factory, mX_factory=self.mX_factory, category=str(row[self._category_col]), category_idx_store=self.category_idx_store, document_index=row.name, parsed_text=parsed_text, term_idx_store=self.term_idx_store, metadata_idx_store=self.metadata_idx_store, y=self.y)

def __init__(self, nlp, X_factory, mX_factory, category_idx_store, term_idx_store, metadata_idx_store, y, term_doc_mat_fact):
    ParsePipelineFactoryWithoutCategories.__init__(self, nlp, X_factory, mX_factory, term_idx_store, metadata_idx_store, term_doc_mat_fact)
    self._register_doc_and_category = self._term_doc_mat_fact._register_doc_and_category
    self._category_col = self._term_doc_mat_fact._category_col
    self.category_idx_store = category_idx_store
    self.y = y

class ScatterChartData(object):

    def __init__(self, minimum_term_frequency=3, minimum_not_category_term_frequency=0, jitter=None, seed=0, pmi_threshold_coefficient=3, max_terms=None, filter_unigrams=False, term_ranker=AbsoluteFrequencyRanker, use_non_text_features=False, term_significance=None, terms_to_include=None, score_transform=percentile_min, dont_filter=False, add_extra_features=False):
        """

		Parameters
		----------
		term_doc_matrix : TermDocMatrix
			The term doc matrix to use for the scatter chart.
		minimum_term_frequency : int, optional
			Minimum times an ngram has to be seen to be included. Default is 3.
		minimum_not_category_term_frequency : int, optional
		  If an n-gram does not occur in the category, minimum times it
		   must been seen to be included. Default is 0.
		jitter : float, optional
			Maximum amount of noise to be added to points, 0.2 is a lot. Default is None to disable jitter.
		seed : float, optional
			Random seed. Default 0
		pmi_threshold_coefficient : int
			Filter out bigrams with a PMI of < 2 * pmi_threshold_coefficient. Default is 3
		max_terms : int, optional
			Maximum number of terms to include in visualization
		filter_unigrams : bool, optional
			If True, remove unigrams that are part of bigrams. Default is False.
		term_ranker : TermRanker, optional
			TermRanker class for determining term frequency ranks.
		use_non_text_features : bool, default = False
			Use non-BoW features (e.g., Empath) instead of text features
		term_significance : TermSignificance instance or None
			Way of getting significance scores.  If None, p values will not be added.
		terms_to_include : set or None
			Only annotate these terms in chart
		score_transform : function
			Transforms original scores into value between 0 and 1. Default is percentile_min
		dont_filter : bool, default is False
			Don't do any filtering of dataframe
		add_extra_features : bool, default is False
			Used in pairplot to add the extra doc structure
		"""
        self.jitter = jitter
        self.minimum_term_frequency = minimum_term_frequency
        self.minimum_not_category_term_frequency = minimum_not_category_term_frequency
        self.seed = seed
        self.pmi_threshold_coefficient = pmi_threshold_coefficient
        self.filter_unigrams = filter_unigrams
        self.term_ranker = term_ranker
        self.max_terms = max_terms
        self.use_non_text_features = use_non_text_features
        self.term_significance = term_significance
        self.terms_to_include = terms_to_include
        self.score_transform = score_transform
        self.dont_filter = dont_filter
        self.add_extra_features = add_extra_features
        np.random.seed(seed)

def __init__(self, minimum_term_frequency=3, minimum_not_category_term_frequency=0, jitter=None, seed=0, pmi_threshold_coefficient=3, max_terms=None, filter_unigrams=False, term_ranker=AbsoluteFrequencyRanker, use_non_text_features=False, term_significance=None, terms_to_include=None, score_transform=percentile_min, dont_filter=False, add_extra_features=False):
    """

		Parameters
		----------
		term_doc_matrix : TermDocMatrix
			The term doc matrix to use for the scatter chart.
		minimum_term_frequency : int, optional
			Minimum times an ngram has to be seen to be included. Default is 3.
		minimum_not_category_term_frequency : int, optional
		  If an n-gram does not occur in the category, minimum times it
		   must been seen to be included. Default is 0.
		jitter : float, optional
			Maximum amount of noise to be added to points, 0.2 is a lot. Default is None to disable jitter.
		seed : float, optional
			Random seed. Default 0
		pmi_threshold_coefficient : int
			Filter out bigrams with a PMI of < 2 * pmi_threshold_coefficient. Default is 3
		max_terms : int, optional
			Maximum number of terms to include in visualization
		filter_unigrams : bool, optional
			If True, remove unigrams that are part of bigrams. Default is False.
		term_ranker : TermRanker, optional
			TermRanker class for determining term frequency ranks.
		use_non_text_features : bool, default = False
			Use non-BoW features (e.g., Empath) instead of text features
		term_significance : TermSignificance instance or None
			Way of getting significance scores.  If None, p values will not be added.
		terms_to_include : set or None
			Only annotate these terms in chart
		score_transform : function
			Transforms original scores into value between 0 and 1. Default is percentile_min
		dont_filter : bool, default is False
			Don't do any filtering of dataframe
		add_extra_features : bool, default is False
			Used in pairplot to add the extra doc structure
		"""
    self.jitter = jitter
    self.minimum_term_frequency = minimum_term_frequency
    self.minimum_not_category_term_frequency = minimum_not_category_term_frequency
    self.seed = seed
    self.pmi_threshold_coefficient = pmi_threshold_coefficient
    self.filter_unigrams = filter_unigrams
    self.term_ranker = term_ranker
    self.max_terms = max_terms
    self.use_non_text_features = use_non_text_features
    self.term_significance = term_significance
    self.terms_to_include = terms_to_include
    self.score_transform = score_transform
    self.dont_filter = dont_filter
    self.add_extra_features = add_extra_features
    np.random.seed(seed)

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

def __init__(self, df, X, mX, y, term_idx_store, category_idx_store, metadata_idx_store, parsed_col, category_col, term_offsets, metadata_offsets, unigram_frequency_path=None):
    self._term_offsets = term_offsets
    self._metadata_offsets = metadata_offsets
    ParsedCorpus.__init__(self, df=df, X=X, mX=mX, y=y, term_idx_store=term_idx_store, category_idx_store=category_idx_store, metadata_idx_store=metadata_idx_store, parsed_col=parsed_col, category_col=category_col, unigram_frequency_path=unigram_frequency_path)

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

def __init__(self, scorer_function: Optional[Callable[[np.array, np.array], np.array]]=None, term_scorer: Optional[CorpusBasedTermScorer]=None, rank_threshold: int=10, term_scorer_kwargs: Optional[Dict]=None, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.scorer_function = RankDifference().get_scores if scorer_function is None else scorer_function
    self.term_scorer = term_scorer
    self.rank_threshold = rank_threshold
    self.term_scorer_kwargs = {} if term_scorer_kwargs is None else term_scorer_kwargs

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

def __init__(self, max_terms, term_ranker=AbsoluteFrequencyRanker, use_non_text_features=False, target_category: Optional[str]=None):
    self.max_terms = max_terms
    BaseAssociationCompactor.__init__(self, term_ranker=term_ranker, use_non_text_features=use_non_text_features, target_category=target_category)

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

def __init__(self, max_terms, scorer=ScaledFScorePresetsNeg1To1, term_ranker=AbsoluteFrequencyRanker, use_non_text_features=False, include_n_most_frequent_terms=0, target_category: Optional[str]=None):
    self.max_terms = max_terms
    self.include_n_most_frequent_terms = include_n_most_frequent_terms
    BaseAssociationCompactor.__init__(self, scorer, term_ranker, use_non_text_features, target_category)

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

def __init__(self, rank, scorer=ScaledFScorePresetsNeg1To1, term_ranker=AbsoluteFrequencyRanker, use_non_text_features=False, target_category: Optional[str]=None):
    self.rank = rank
    BaseAssociationCompactor.__init__(self, scorer, term_ranker, use_non_text_features, target_category)

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

def __init__(self, category_order: List=None, metric: str='DA', use_residual: bool=True, term_ranker: Optional[TermRanker]=None, frequency_scaler: Optional[Callable[[np.array], np.array]]=None, dispersion_scaler: Optional[Callable[[np.array], np.array]]=None, regressor: Optional=None):
    TrendPlotSettings.__init__(self, category_order=category_order)
    self.metric = metric
    self.use_residual = use_residual
    self.frequency_scaler = dense_rank if frequency_scaler is None else frequency_scaler
    self.dispersion_scaler = (scale_center_zero_abs if use_residual else scale) if dispersion_scaler is None else dispersion_scaler
    self.term_ranker = AbsoluteFrequencyRanker if term_ranker is None else term_ranker
    self.regressor = MeanIsotonic() if regressor is None else regressor

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

def __init__(self, category_order: List=None, correlation_type: str='spearmanr', term_ranker: Optional[TermRanker]=None, frequency_scaler: Optional[Callable[[np.array], np.array]]=None):
    TrendPlotSettings.__init__(self, category_order=category_order)
    self.correlation_type = correlation_type
    self.term_ranker = AbsoluteFrequencyRanker if term_ranker is None else term_ranker
    self.frequency_scaler = dense_rank if frequency_scaler is None else frequency_scaler

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

def __init__(self, category_order: List=None, dispersion_metric: str='DA', use_residual: bool=False, dispersion_scaler: Optional[Callable[[np.array], np.array]]=None, term_ranker: Optional[TermRanker]=None, regressor: Optional=None):
    TrendPlotSettings.__init__(self, category_order=category_order)
    self.y_axis_metric = dispersion_metric
    self.dispersion_scaler = dispersion_scaler
    self.use_residual = use_residual
    self.term_ranker = AbsoluteFrequencyRanker if term_ranker is None else term_ranker
    self.regressor = KNeighborsRegressor(weights='distance') if regressor is None else regressor

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

def __init__(self, use_non_text=False):
    self.set_correlation_type('pearsonr')
    CoefficientBase.__init__(self, use_non_text=use_non_text)

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

def __init__(self, prior, alpha=1, scaler_algo=DEFAULT_SCALER_ALGO, beta=DEFAULT_BETA):
    self.prior = prior
    self.alpha = alpha
    ScaledFZScore.__init__(self, scaler_algo, beta)

class TimeStructure(GraphStructure):

    def __init__(self, scatterplot_structure, graph_renderer, scatterplot_width=500, scatterplot_height=700, d3_url_struct=None, protocol='http', template_file_name='time_plot.html'):
        GraphStructure.__init__(self, scatterplot_structure, graph_renderer, scatterplot_width, scatterplot_height, d3_url_struct, protocol, template_file_name)

    def _replace_html_template(self, autocomplete_css, html_template, javascript_to_insert):
        html_template = html_template.replace('<!-- EXTRA LIBS -->', "<script src='../scattertext/scattertext/data/viz/scripts/timelines-chart.js'></script>\n<!--D3URL-->")
        return GraphStructure._replace_html_template(self, autocomplete_css, html_template, javascript_to_insert)

def __init__(self, scatterplot_structure, graph_renderer, scatterplot_width=500, scatterplot_height=700, d3_url_struct=None, protocol='http', template_file_name='time_plot.html'):
    GraphStructure.__init__(self, scatterplot_structure, graph_renderer, scatterplot_width, scatterplot_height, d3_url_struct, protocol, template_file_name)

class PyatePhrases(FeatsFromSpacyDoc):

    def __init__(self, extractor=None, **args):
        import pyate
        self._extractor = pyate.combo_basic if extractor is None else extractor
        FeatsFromSpacyDoc.__init__(self, **args)

    def get_feats(self, doc):
        return Counter(self._extractor(str(doc)).to_dict())

def __init__(self, extractor=None, **args):
    import pyate
    self._extractor = pyate.combo_basic if extractor is None else extractor
    FeatsFromSpacyDoc.__init__(self, **args)

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

def __init__(self, use_lemmas=False, entity_types_to_censor=set(), tag_types_to_censor=set(), strip_final_period=False, **kwargs):
    """
        Parameters
        ----------
        Other parameters from FeatsFromSpacyDoc.__init__
        """
    self._lexicon_df = self._load_mfd()
    super(FeatsFromMoralFoundationsDictionary, self).__init__(use_lemmas, entity_types_to_censor, tag_types_to_censor, strip_final_period)

class PyTextRankPhrases(FeatsFromSpacyDoc):

    def __init__(self, use_lemmas=False, entity_types_to_censor=set(), tag_types_to_censor=set(), strip_final_period=False):
        FeatsFromSpacyDoc.__init__(self, use_lemmas, entity_types_to_censor, tag_types_to_censor, strip_final_period)
        self._include_chunks = False
        self._rank_smoothing_constant = 0

    def include_chunks(self):
        """
        Use each chunk in a phrase instead of just the span identified as a phrase
        :return: self
        """
        self._include_chunks = True
        return self

    def set_rank_smoothing_constant(self, rank_smoothing_constant):
        """
        Add a quantity

        :param rank_smoothing_constant: float
        :return: self
        """
        self._rank_smoothing_constant = rank_smoothing_constant
        return self

    def get_doc_metadata(self, doc):
        phrase_counter = Counter()
        try:
            for phrase in doc._.phrases:
                if self._include_chunks:
                    for chunk in phrase.chunks:
                        phrase_counter[str(chunk)] += phrase.rank + self._rank_smoothing_constant
                else:
                    phrase_counter[phrase.text] += phrase.count * (phrase.rank + self._rank_smoothing_constant)
        except:
            import pytextrank
            tr = pytextrank.TextRank()
            tr.doc = doc
            phrases = tr.calc_textrank()
            for phrase in phrases:
                if self._include_chunks:
                    for chunk in phrase.chunks:
                        phrase_counter[str(chunk)] += phrase.rank + self._rank_smoothing_constant
                else:
                    phrase_counter[phrase.text] += phrase.count * (phrase.rank + self._rank_smoothing_constant)
        return phrase_counter

    def get_feats(self, doc):
        return Counter()

def __init__(self, use_lemmas=False, entity_types_to_censor=set(), tag_types_to_censor=set(), strip_final_period=False):
    FeatsFromSpacyDoc.__init__(self, use_lemmas, entity_types_to_censor, tag_types_to_censor, strip_final_period)
    self._include_chunks = False
    self._rank_smoothing_constant = 0

class SpacyEntities(FeatsFromSpacyDoc):

    def __init__(self, use_lemmas=False, entity_types_to_censor=set(), entity_types_to_use=None, tag_types_to_censor=set(), strip_final_period=False):
        self._entity_types_to_use = entity_types_to_use
        FeatsFromSpacyDoc.__init__(self, use_lemmas, entity_types_to_censor, tag_types_to_censor, strip_final_period)

    def get_feats(self, doc):
        return Counter([' '.join(str(ent).split()).lower() for ent in doc.ents if (self._entity_types_to_use is None or ent.label_ in self._entity_types_to_use) and ent.label_ not in self._entity_types_to_censor])

def __init__(self, use_lemmas=False, entity_types_to_censor=set(), entity_types_to_use=None, tag_types_to_censor=set(), strip_final_period=False):
    self._entity_types_to_use = entity_types_to_use
    FeatsFromSpacyDoc.__init__(self, use_lemmas, entity_types_to_censor, tag_types_to_censor, strip_final_period)

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

class FeatsFromSentencePiece(FeatsFromSpacyDoc):

    def __init__(self, sp, *args, **kwargs):
        """
        :param sp: sentencepiece.SentencePieceProcessor
        """
        self._sp = sp
        super(FeatsFromSentencePiece, self).__init__(*args, **kwargs)

    def get_doc_metadata(self, doc):
        """

        :param doc: spacy.Doc
        :return: pd.Series
        """
        return Counter(self._sp.encode_as_pieces(str(doc)))

def __init__(self, sp, *args, **kwargs):
    """
        :param sp: sentencepiece.SentencePieceProcessor
        """
    self._sp = sp
    super(FeatsFromSentencePiece, self).__init__(*args, **kwargs)

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

def __init__(self, ngram_sizes: Optional[List[int]]=None, exclude_ngram_filter: Optional[Callable]=None, text_from_token: Optional[Callable]=None, validate_token: Optional[Callable]=None, exclude_sentence_filter: Optional[Callable[[str], bool]]=None):
    FeatsFromSpacyDoc.__init__(self)
    FlexibleNGramFeaturesBase.__init__(self, exclude_ngram_filter, ngram_sizes, text_from_token, validate_token, whitespace_substitute=None, exclude_sentence_filter=exclude_sentence_filter)

class MyEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, WhitespaceNLP.Doc):
            return repr(obj)
        elif isinstance(obj, AsianNLP.Doc):
            return repr(obj)
        elif 'spacy' in sys.modules:
            import spacy
            if isinstance(obj, spacy.tokens.doc.Doc):
                return repr(obj)
        else:
            return super(MyEncoder, self).default(obj)

def default(self, obj):
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, WhitespaceNLP.Doc):
        return repr(obj)
    elif isinstance(obj, AsianNLP.Doc):
        return repr(obj)
    elif 'spacy' in sys.modules:
        import spacy
        if isinstance(obj, spacy.tokens.doc.Doc):
            return repr(obj)
    else:
        return super(MyEncoder, self).default(obj)

