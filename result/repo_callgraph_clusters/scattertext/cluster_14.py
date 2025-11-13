# Cluster 14

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

def list_extra_features(self):
    raise Exception('Not implemented in TermCategoryFrequencies')

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

def _validate_category(self, category):
    if category not in self.get_categories():
        raise Exception('Invalid category: %s, valid: %s' % (category, self.get_categories()))

def _get_chinese_tokenizer():
    global jieba
    if 'jieba' not in sys.modules:
        try:
            jieba = __import__('jieba')
        except:
            raise Exception('The package jieba is needed to perform Chinese text segmentation.')
    return jieba.cut

def _get_japanese_tokenizer():
    global japanese_tokenizer
    if 'tinysegmenter' not in sys.modules:
        tinysegmenter = __import__('tinysegmenter')
        try:
            japanese_tokenizer = tinysegmenter.TinySegmenter().tokenize
        except:
            japanese_tokenizer = tinysegmenter.tinysegmenter.tokenize
    else:
        import tinysegmenter
        try:
            japanese_tokenizer = tinysegmenter.TinySegmenter().tokenize
        except:
            japanese_tokenizer = tinysegmenter.tinysegmenter.tokenize
    return japanese_tokenizer

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

def __init__(self, nlp, X_factory, mX_factory, term_idx_store, metadata_idx_store, term_doc_mat_fact):
    if nlp == chinese_nlp:
        raise Exception('Chinese NLP not yet supported.  Preparse chinese documents, and use CorpusFromParsedDocuments or a similar class.')
    self.X_factory, self.mX_factory, self.term_idx_store, self.metadata_idx_store, self.nlp = (X_factory, mX_factory, term_idx_store, metadata_idx_store, nlp)
    self._term_doc_mat_fact = term_doc_mat_fact
    self._text_col = self._term_doc_mat_fact._text_col
    self._clean_function = self._term_doc_mat_fact._clean_function
    self._verbose = self._term_doc_mat_fact._verbose

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

def get_document_lengths_in_tokens(self):
    return self.get_parsed_docs().apply(len).values

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

def test_get_field(self):
    self.assertEqual(list(self.corpus.get_field('author')), list(self.df.author))

def test_get_parsed_docs(self):
    doc = [x for x in self.corpus.get_parsed_docs()][0]
    doc.sents

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

def offset_corpus_to_concatenated_inter_arrivals(corpus: OffsetCorpus, categories: Optional[List[str]]=None, generator: Optional[np.random._generator.Generator]=None, domains_to_preserve: Optional[List[str]]=None, join_text: str='\n', verbose: bool=False, nlp: Optional[spacy.Language]=None) -> Dict[str, List[int]]:
    if not isinstance(corpus, OffsetCorpus):
        raise Exception(f'The corpus argument was of type {type(corpus)}. Use offset_corpus_to_concatenated_inter_arrivals instead.')
    doc_df = __order_docs_to_concat(categories, corpus, domains_to_preserve, generator, join_text)
    doc = __concatenate_doc(corpus, doc_df, join_text, nlp)
    doc_id_to_offset = dict(doc_df[['_OrigIdx', 'StartOffset']].set_index('_OrigIdx')['StartOffset'])
    term_inter_arrivals = {}
    it = corpus.get_offsets().items()
    if verbose:
        it = tqdm(it, total=len(corpus.get_offsets()))
    for term, doc_offsets in it:
        new_offsets = _translate_offsets_to_concatenated_doc(doc_id_to_offset, doc_offsets)
        term_inter_arrivals[term] = _collect_term_inter_arrivals_on_concatenated_doc(doc, new_offsets)
    return term_inter_arrivals

def category_specific_inter_arrivals_from_offset_corpus(corpus: OffsetCorpus, weibull_fit_func: Optional[Callable]=None, verbose: bool=False) -> pd.DataFrame:
    if not isinstance(corpus, OffsetCorpus):
        raise Exception(f'The corpus argument was of type {type(corpus)}. Use offset_corpus_to_concatenated_inter_arrivals instead.')
    if weibull_fit_func is None:
        from reliability.Fitters import Fit_Weibull_2P
        weibull_fit_func = lambda failures: Fit_Weibull_2P(failures=failures, show_probability_plot=False, print_results=False)
    cat_term_ias = {cat: offset_corpus_to_concatenated_inter_arrivals(corpus, categories=[cat], verbose=verbose) for cat in corpus.get_categories()}
    data = []
    for cat, term_ias in cat_term_ias.items():
        for term, ias in tqdm(term_ias.items()):
            if len(ias) > 1:
                data.append({'term': term, 'cat': cat, 'freq': len(ias), **__get_term_stats(ias, weibull_fit_func)})
    return pd.DataFrame(data)

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

def __register_weibull_fit_funct(self, weibull_fit_func):
    if weibull_fit_func is None:
        from reliability.Fitters import Fit_Weibull_2P
        self.weibull_fit_func = lambda failures: Fit_Weibull_2P(failures=failures, show_probability_plot=False, print_results=False)
    else:
        self.weibull_fit_func = weibull_fit_func

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

class GensimPhraseAdder(object):

    def __init__(self, max_tokens_per_phrase=3, phrases=None):
        """
        Parameters
        ----------
        max_tokens_per_phrase: int, must be > 1.  Default 3
        phrases: Instance of Gensim phrases class, default None
        """
        self.max_tokens_per_phrase = max_tokens_per_phrase
        self.phrases = phrases

    def add_phrases(self, corpus):
        """
        Parameters
        ----------
        corpus: Corpus for phrase augmentation

        Returns
        -------
        New ParsedCorpus containing unigrams in corpus and new phrases
        """
        from gensim.models import Phrases
        assert isinstance(corpus, ParsedCorpus)
        self.phrases = [Phrases(CorpusAdapterForGensim.get_sentences(corpus), delimiter=' ')]
        for i in range(1, self.max_tokens_per_phrase):
            self.phrases.append(Phrases(self.phrases[-1][CorpusAdapterForGensim.get_sentences(corpus)]))
        return self

def add_phrases(self, corpus):
    """
        Parameters
        ----------
        corpus: Corpus for phrase augmentation

        Returns
        -------
        New ParsedCorpus containing unigrams in corpus and new phrases
        """
    from gensim.models import Phrases
    assert isinstance(corpus, ParsedCorpus)
    self.phrases = [Phrases(CorpusAdapterForGensim.get_sentences(corpus), delimiter=' ')]
    for i in range(1, self.max_tokens_per_phrase):
        self.phrases.append(Phrases(self.phrases[-1][CorpusAdapterForGensim.get_sentences(corpus)]))
    return self

class CorpusAdapterForGensim(object):

    @staticmethod
    def get_token_format(token):
        return token.lower_

    @classmethod
    def get_sentences(cls, corpus):
        """
        Parameters
        ----------
        corpus, ParsedCorpus

        Returns
        -------
        iter: [sentence1word1, ...], [sentence2word1, ...]
        """
        return itertools.chain(*[[[cls.get_token_format(t) for t in sent if not t.is_punct] for sent in doc.sents] for doc in corpus.get_parsed_docs()])

@classmethod
def get_sentences(cls, corpus):
    """
        Parameters
        ----------
        corpus, ParsedCorpus

        Returns
        -------
        iter: [sentence1word1, ...], [sentence2word1, ...]
        """
    return itertools.chain(*[[[cls.get_token_format(t) for t in sent if not t.is_punct] for sent in doc.sents] for doc in corpus.get_parsed_docs()])

class Word2VecDefault(object):

    def _default_word2vec_model(self):
        from gensim.models import word2vec
        return word2vec.Word2Vec(vector_size=100, alpha=0.025, window=5, min_count=5, max_vocab_size=None, sample=0, seed=1, workers=1, min_alpha=0.0001, sg=1, hs=1, negative=0, cbow_mean=0, null_word=0, trim_rule=None, sorted_vocab=1)

def _default_word2vec_model(self):
    from gensim.models import word2vec
    return word2vec.Word2Vec(vector_size=100, alpha=0.025, window=5, min_count=5, max_vocab_size=None, sample=0, seed=1, workers=1, min_alpha=0.0001, sg=1, hs=1, negative=0, cbow_mean=0, null_word=0, trim_rule=None, sorted_vocab=1)

class Word2VecFromParsedCorpus(Word2VecDefault):

    def __init__(self, corpus, word2vec_model=None):
        """
        Parameters
        ----------
        corpus: ParsedCorpus
          from which to build word2vec model
        word2vec_model: word2vec.Word2Vec
            Gensim instance to be used to train word2vec model
        """
        try:
            from gensim.models import word2vec
            assert word2vec_model is None or isinstance(word2vec_model, word2vec.Word2Vec)
        except:
            warnings.warn("You should really install gensim, but we're going to duck-type your model and pray it works")
        self.corpus = corpus
        self.model = self._get_word2vec_model(word2vec_model)

    def train(self, epochs=2000, super_epochs=5, tqdm=None):
        """
        Parameters
        ----------
        epochs : int
          Number of epochs to train for.  Default is 2000.
        super_epochs : int
            Number of times to repeat training process. Default is training_iterations.

        Returns
        -------
        A trained word2vec model.
        """
        self._scan_and_build_vocab()
        myiter = range(super_epochs)
        if tqdm:
            myiter = tqdm(myiter, total=super_epochs)
        for _ in myiter:
            self.model.train(CorpusAdapterForGensim.get_sentences(self.corpus), total_examples=self.model.corpus_count, epochs=epochs)
        return self.model

    def _get_word2vec_model(self, word2vec_model):
        return self._default_word2vec_model() if word2vec_model is None else word2vec_model

    def _scan_and_build_vocab(self):
        try:
            self.model.scan_vocab(CorpusAdapterForGensim.get_sentences(self.corpus))
        except:
            pass
        self.model.build_vocab(CorpusAdapterForGensim.get_sentences(self.corpus))

def __init__(self, corpus, word2vec_model=None):
    """
        Parameters
        ----------
        corpus: ParsedCorpus
          from which to build word2vec model
        word2vec_model: word2vec.Word2Vec
            Gensim instance to be used to train word2vec model
        """
    try:
        from gensim.models import word2vec
        assert word2vec_model is None or isinstance(word2vec_model, word2vec.Word2Vec)
    except:
        warnings.warn("You should really install gensim, but we're going to duck-type your model and pray it works")
    self.corpus = corpus
    self.model = self._get_word2vec_model(word2vec_model)

def train(self, epochs=2000, super_epochs=5, tqdm=None):
    """
        Parameters
        ----------
        epochs : int
          Number of epochs to train for.  Default is 2000.
        super_epochs : int
            Number of times to repeat training process. Default is training_iterations.

        Returns
        -------
        A trained word2vec model.
        """
    self._scan_and_build_vocab()
    myiter = range(super_epochs)
    if tqdm:
        myiter = tqdm(myiter, total=super_epochs)
    for _ in myiter:
        self.model.train(CorpusAdapterForGensim.get_sentences(self.corpus), total_examples=self.model.corpus_count, epochs=epochs)
    return self.model

def _scan_and_build_vocab(self):
    try:
        self.model.scan_vocab(CorpusAdapterForGensim.get_sentences(self.corpus))
    except:
        pass
    self.model.build_vocab(CorpusAdapterForGensim.get_sentences(self.corpus))

class Word2VecFromParsedCorpusBigrams(Word2VecFromParsedCorpus):

    def _scan_and_build_vocab(self):
        from gensim.models import Phrases
        bigram_transformer = Phrases(CorpusAdapterForGensim.get_sentences(self.corpus))
        try:
            self.model.scan_vocab(CorpusAdapterForGensim.get_sentences(self.corpus))
        except:
            pass
        self.model.build_vocab(bigram_transformer[CorpusAdapterForGensim.get_sentences(self.corpus)])

def _scan_and_build_vocab(self):
    from gensim.models import Phrases
    bigram_transformer = Phrases(CorpusAdapterForGensim.get_sentences(self.corpus))
    try:
        self.model.scan_vocab(CorpusAdapterForGensim.get_sentences(self.corpus))
    except:
        pass
    self.model.build_vocab(bigram_transformer[CorpusAdapterForGensim.get_sentences(self.corpus)])

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

def _verify_category(self, category):
    if category not in self.corpus_.get_categories():
        raise Exception('Category %s is not in corpus.' % category)
    if category in self.category_embeddings_:
        raise Exception('You have already set embeddings by running set_embeddings or set_embeddings_model.')

class CartegorySpecificCorpusAdapterForGensim(object):

    @staticmethod
    def get_sentences(corpus, category):
        """
        Parameters
        ----------
        corpus, ParsedCorpus
        category, str

        Returns
        -------
        iter: [sentence1word1, ...], [sentence2word1, ...]
        """
        return itertools.chain(*[[[t.lower_ for t in sent if not t.is_punct] for sent in doc.sents] for doc_catgory, doc in zip(corpus.get_category_names_by_row(), corpus.get_parsed_docs()) if category == doc_catgory])

@staticmethod
def get_sentences(corpus, category):
    """
        Parameters
        ----------
        corpus, ParsedCorpus
        category, str

        Returns
        -------
        iter: [sentence1word1, ...], [sentence2word1, ...]
        """
    return itertools.chain(*[[[t.lower_ for t in sent if not t.is_punct] for sent in doc.sents] for doc_catgory, doc in zip(corpus.get_category_names_by_row(), corpus.get_parsed_docs()) if category == doc_catgory])

class CategorySpecificWord2VecFromParsedCorpus(Word2VecDefault):

    def __init__(self, corpus, category, word2vec_model=None):
        """
        Parameters
        ----------
        corpus: ParsedCorpus
          from which to build word2vec model
        category, str
        word2vec_model: word2vec.Word2Vec
            Gensim instance to be used to train word2vec model
        """
        try:
            from gensim.models import word2vec
            assert word2vec_model is None or isinstance(word2vec_model, word2vec.Word2Vec)
        except:
            warnings.warn("You should really install gensim, but we're going to duck-type your model and hope it works")
        self.corpus = corpus
        self.category = category
        self.model = self._get_word2vec_model(word2vec_model)

    def train(self, epochs=2000, training_iterations=5):
        """
        Parameters
        ----------
        epochs : int
          Number of epochs to train for.  Default is 2000.
        training_iterations : int
            Number of times to repeat training process. Default is super_epochs.

        Returns
        -------
        A trained word2vec model.
        """
        self._scan_and_build_vocab()
        for _ in range(training_iterations):
            self.model.train(CartegorySpecificCorpusAdapterForGensim.get_sentences(self.corpus, self.category), total_examples=self.model.corpus_count, epochs=epochs)
        return self.model

    def _get_word2vec_model(self, word2vec_model):
        return self._default_word2vec_model() if word2vec_model is None else word2vec_model

    def _scan_and_build_vocab(self):
        try:
            self.model.scan_vocab(CartegorySpecificCorpusAdapterForGensim.get_sentences(self.corpus, self.category))
        except:
            pass
        self.model.build_vocab(CartegorySpecificCorpusAdapterForGensim.get_sentences(self.corpus, self.category))

def __init__(self, corpus, category, word2vec_model=None):
    """
        Parameters
        ----------
        corpus: ParsedCorpus
          from which to build word2vec model
        category, str
        word2vec_model: word2vec.Word2Vec
            Gensim instance to be used to train word2vec model
        """
    try:
        from gensim.models import word2vec
        assert word2vec_model is None or isinstance(word2vec_model, word2vec.Word2Vec)
    except:
        warnings.warn("You should really install gensim, but we're going to duck-type your model and hope it works")
    self.corpus = corpus
    self.category = category
    self.model = self._get_word2vec_model(word2vec_model)

def train(self, epochs=2000, training_iterations=5):
    """
        Parameters
        ----------
        epochs : int
          Number of epochs to train for.  Default is 2000.
        training_iterations : int
            Number of times to repeat training process. Default is super_epochs.

        Returns
        -------
        A trained word2vec model.
        """
    self._scan_and_build_vocab()
    for _ in range(training_iterations):
        self.model.train(CartegorySpecificCorpusAdapterForGensim.get_sentences(self.corpus, self.category), total_examples=self.model.corpus_count, epochs=epochs)
    return self.model

def _scan_and_build_vocab(self):
    try:
        self.model.scan_vocab(CartegorySpecificCorpusAdapterForGensim.get_sentences(self.corpus, self.category))
    except:
        pass
    self.model.build_vocab(CartegorySpecificCorpusAdapterForGensim.get_sentences(self.corpus, self.category))

class CorpusSentenceIterator(object):

    @staticmethod
    def get_sentences(corpus):
        """
        Parameters
        ----------
        corpus, ParsedCorpus

        Returns
        -------
        iter: [sentence1word1, ...], [sentence2word1, ...]
        """
        return itertools.chain(*[[[corpus._term_idx_store.getidxstrict(t.lower_) for t in sent if not t.is_punct] for sent in doc.sents] for doc in corpus.get_parsed_docs()])

@staticmethod
def get_sentences(corpus):
    """
        Parameters
        ----------
        corpus, ParsedCorpus

        Returns
        -------
        iter: [sentence1word1, ...], [sentence2word1, ...]
        """
    return itertools.chain(*[[[corpus._term_idx_store.getidxstrict(t.lower_) for t in sent if not t.is_punct] for sent in doc.sents] for doc in corpus.get_parsed_docs()])

class Doc2VecBuilder(object):

    def __init__(self, model, term_from_token=lambda tok: tok.lower_):
        self.model = model
        self.term_from_token = term_from_token
        self.cartegory2dvid = None
        self.corpus = None

    def train(self, corpus):
        assert isinstance(corpus, ParsedCorpus)
        tagged_docs = []
        try:
            import gensim
        except:
            raise Exception('Please install gensim before using Doc2VecCategoryProjector/')
        for doc, tag in zip(corpus.get_parsed_docs(), corpus.get_category_names_by_row()):
            words = list(itertools.chain(*[[t.lower_ for t in sent if not t.is_punct if t.lower_.strip()] for sent in doc.sents]))
            tagged_docs.append(gensim.models.doc2vec.TaggedDocument(words, [tag]))
        self.model.build_vocab(tagged_docs)
        self.cartegory2dvid = {}
        for i in range(corpus.get_num_categories()):
            self.cartegory2dvid[self.model.docvecs.index_to_doctag(i)] = i
        self.model.train(tagged_docs, total_examples=self.model.corpus_count, epochs=self.model.epochs)
        self.corpus = corpus
        return self.model

    def project(self):
        if self.corpus is None:
            raise Exception('Please run train before project.')
        return self.model.docvecs.vectors_docs[[self.cartegory2dvid[category] for category in self.corpus.get_categories()]]

def train(self, corpus):
    assert isinstance(corpus, ParsedCorpus)
    tagged_docs = []
    try:
        import gensim
    except:
        raise Exception('Please install gensim before using Doc2VecCategoryProjector/')
    for doc, tag in zip(corpus.get_parsed_docs(), corpus.get_category_names_by_row()):
        words = list(itertools.chain(*[[t.lower_ for t in sent if not t.is_punct if t.lower_.strip()] for sent in doc.sents]))
        tagged_docs.append(gensim.models.doc2vec.TaggedDocument(words, [tag]))
    self.model.build_vocab(tagged_docs)
    self.cartegory2dvid = {}
    for i in range(corpus.get_num_categories()):
        self.cartegory2dvid[self.model.docvecs.index_to_doctag(i)] = i
    self.model.train(tagged_docs, total_examples=self.model.corpus_count, epochs=self.model.epochs)
    self.corpus = corpus
    return self.model

def project(self):
    if self.corpus is None:
        raise Exception('Please run train before project.')
    return self.model.docvecs.vectors_docs[[self.cartegory2dvid[category] for category in self.corpus.get_categories()]]

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

def get_category_embeddings(self, category_corpus):
    raw_category_counts = self._get_raw_category_counts(category_corpus)
    weighted_counts = self.weight(raw_category_counts)
    normalized_counts = self.normalize(weighted_counts)
    if type(normalized_counts) is not pd.DataFrame:
        normalized_counts = pd.DataFrame(normalized_counts.todense() if scipy.sparse.issparse(normalized_counts) else normalized_counts, columns=raw_category_counts.columns, index=raw_category_counts.index)
    return normalized_counts

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

def gen():
    for s in xrange(len(ss)):
        for n in xrange(minlen, 1 + min(maxlen, len(ss) - s)):
            e = s + n
            substr = ss[s:e]
            if re.match(regex + '$', substr):
                yield (s, e)

def unicodify(s, encoding='utf8', errors='ignore'):
    if sys.version_info[0] < 3:
        if isinstance(s, unicode):
            return s
        if isinstance(s, str):
            return s.decode(encoding, errors)
        return unicode(s)
    elif type(s) == bytes:
        return s.decode('utf8')
    else:
        return s

def safejoin(list_of_str_or_unicode):
    xx = list_of_str_or_unicode
    if not xx:
        return u''
    if isinstance(xx[0], str):
        return ' '.join(xx)
    if isinstance(xx[0], bytes):
        return ' '.join(xx)
    if sys.version_info[0] < 3:
        if isinstance(xx[0], unicode):
            return u' '.join(xx)
    raise Exception('Bad input to safejoin:', list_of_str_or_unicode)

def get_stdeng_nltk_tagger(suppress_errors=False):
    try:
        tagger = NLTKTagger()
        throw_away = tagger.tag_text('The red cat sat down.')
        return NLTKTagger()
    except ImportError:
        if not suppress_errors:
            raise
    except LookupError:
        if not suppress_errors:
            raise
    return None

class SpacyTagger:

    def __init__(self):
        self.spacy_object = None

    def tag_text(self, text):
        text = unicodify(text)
        doc = self.spacy_object(text)
        return {'pos': [token.tag_ for token in doc], 'tokens': [token.text for token in doc]}

    def tag_tokens(self, tokens):
        newtext = safejoin(tokens)
        newtext = unicodify(newtext)
        return self.tag_text(newtext)

def tag_text(self, text):
    text = unicodify(text)
    doc = self.spacy_object(text)
    return {'pos': [token.tag_ for token in doc], 'tokens': [token.text for token in doc]}

def tag_tokens(self, tokens):
    newtext = safejoin(tokens)
    newtext = unicodify(newtext)
    return self.tag_text(newtext)

def get_phrases(text=None, tokens=None, postags=None, tagger='nltk', grammar='SimpleNP', regex=None, minlen=2, maxlen=8, output='counts'):
    """Give a text (or POS tag sequence), return the phrases matching the given
	grammar.  Works on documents or sentences.
	Returns a dict with one or more keys with the phrase information.

	text: the text of the document.  If supplied, we will try to POS tag it.

	You can also do your own tokenzation and/or tagging and supply them as
	'tokens' and/or 'postags', which are lists of strings (of the same length).
	 - Must supply both to get phrase counts back.
	 - With only postags, can get phrase token spans back.
	 - With only tokens, we will try to POS-tag them if possible.

	output: a string, or list of strings, of information to return. Options include:
	 - counts: a Counter with phrase frequencies.  (default)
	 - token_spans: a list of the token spans of each matched phrase.  This is
		 a list of (start,end) pairs of integers, which refer to token positions.
	 - pos, tokens can be returned too.

	tagger: if you're passing in raw text, can supply your own tagger, from one
	of the get_*_tagger() functions.  If this is not supplied, we will try to load one.

	grammar: the grammar to use.  Only one option right now...

	regex: a custom regex to use, instead of a premade grammar.  Currently,
	this must work on the 5-tag system described near the top of this file.

	"""
    global SimpleNP
    if postags is None:
        try:
            tagger = TAGGER_NAMES[tagger]()
        except:
            raise Exception("We don't support tagger %s" % tagger)
        d = None
        if tokens is not None:
            d = tagger.tag_tokens(tokens)
        elif text is not None:
            d = tagger.tag_text(text)
        else:
            raise Exception('Need to supply text or tokens.')
        postags = d['pos']
        tokens = d['tokens']
    if regex is None:
        if grammar == 'SimpleNP':
            regex = SimpleNP
        else:
            assert False, "Don't know grammar %s" % grammar
    phrase_tokspans = extract_ngram_filter(postags, minlen=minlen, maxlen=maxlen)
    if isinstance(output, str):
        output = [output]
    our_options = set()

    def retopt(x):
        our_options.add(x)
        return x in output
    ret = {}
    ret['num_tokens'] = len(postags)
    if retopt('token_spans'):
        ret['token_spans'] = phrase_tokspans
    if retopt('counts'):
        counts = Counter()
        for start, end in phrase_tokspans:
            phrase = safejoin([tokens[i] for i in xrange(start, end)])
            phrase = phrase.lower()
            counts[phrase] += 1
        ret['counts'] = counts
    if retopt('pos'):
        ret['pos'] = postags
    if retopt('tokens'):
        ret['tokens'] = tokens
    xx = set(output) - our_options
    if xx:
        raise Exception("Don't know how to handle output options: %s" % list(xx))
    return ret

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

def use_token_counts_as_doc_sizes(self) -> 'CorpusBasedTermScorer':
    return self.set_doc_sizes(doc_sizes=self.corpus_.get_parsed_docs().apply(len).values)

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

class FeatsFromSpacyDocAndEmpath(FeatsFromSpacyDoc):

    def __init__(self, use_lemmas=False, entity_types_to_censor=set(), tag_types_to_censor=set(), strip_final_period=False, empath_analyze_function=None, **kwargs):
        """
        Parameters
        ----------
        empath_analyze_function: function (default=empath.Empath().analyze)
            Function that produces a dictionary mapping Empath categories to

        Other parameters from FeatsFromSpacyDoc.__init__
        """
        if empath_analyze_function is None:
            try:
                import empath
            except ImportError:
                raise Exception('Please install the empath library to use FeatsFromSpacyDocAndEmpath.')
            self._empath_analyze_function = empath.Empath().analyze
        else:
            self._empath_analyze_function = partial(empath_analyze_function, kwargs={'tokenizer': 'bigram'})
        FeatsFromSpacyDoc.__init__(self, use_lemmas, entity_types_to_censor, tag_types_to_censor, strip_final_period)

    def get_doc_metadata(self, doc, prefix=''):
        empath_counter = Counter()
        if version_info[0] >= 3:
            doc = str(doc)
        for empath_category, score in self._empath_analyze_function(doc).items():
            if score > 0:
                empath_counter[prefix + empath_category] = int(score)
        return empath_counter

    def has_metadata_term_list(self):
        return True

    def get_top_model_term_lists(self):
        try:
            import empath
        except ImportError:
            raise Exception('Please install the empath library to use FeatsFromSpacyDocAndEmpath.')
        return dict(empath.Empath().cats)

def __init__(self, use_lemmas=False, entity_types_to_censor=set(), tag_types_to_censor=set(), strip_final_period=False, empath_analyze_function=None, **kwargs):
    """
        Parameters
        ----------
        empath_analyze_function: function (default=empath.Empath().analyze)
            Function that produces a dictionary mapping Empath categories to

        Other parameters from FeatsFromSpacyDoc.__init__
        """
    if empath_analyze_function is None:
        try:
            import empath
        except ImportError:
            raise Exception('Please install the empath library to use FeatsFromSpacyDocAndEmpath.')
        self._empath_analyze_function = empath.Empath().analyze
    else:
        self._empath_analyze_function = partial(empath_analyze_function, kwargs={'tokenizer': 'bigram'})
    FeatsFromSpacyDoc.__init__(self, use_lemmas, entity_types_to_censor, tag_types_to_censor, strip_final_period)

def get_top_model_term_lists(self):
    try:
        import empath
    except ImportError:
        raise Exception('Please install the empath library to use FeatsFromSpacyDocAndEmpath.')
    return dict(empath.Empath().cats)

def _phrase_counts(sent):
    pos_seq = [w.tag_ for w in sent]
    tokens = [w.lower_ for w in sent]
    counts = Counter()
    for start, end in phrasemachine.extract_ngram_filter(pos_seq, minlen=2, maxlen=8):
        phrase = phrasemachine.safejoin([tokens[i] for i in range(start, end)])
        phrase = phrase.lower()
        counts[phrase] += 1
    return counts

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

def get_top_model_term_lists(self):
    raise Exception('No topic models associated with these features.')

class CharacteristicScorer(object):

    def __init__(self, term_ranker=AbsoluteFrequencyRanker, background_frequencies=DefaultBackgroundFrequencies, rerank_ranks=False):
        """
		Parameters
		----------
		term_ranker : TermRanker, default is OncePerDocFrequencyRanker
		background_frequencies : BackgroundFrequencies
		rerank_ranks : bool, False by default
			orders scores from 0 to 1 by their dense rank
		"""
        self.term_ranker = term_ranker
        self.background_frequencies = background_frequencies
        self.rerank_ranks = rerank_ranks

    def get_scores(self, corpus):
        raise Exception()

    def _rerank_scores(self, scores):
        ranks = rankdata(scores, 'dense')
        ranks = ranks / ranks.max()
        return (ranks, 0.5)

def get_scores(self, corpus):
    raise Exception()

