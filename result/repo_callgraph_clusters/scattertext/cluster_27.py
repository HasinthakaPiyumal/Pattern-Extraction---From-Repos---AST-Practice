# Cluster 27

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

def test_total_unigram_count(self):
    self.assertEqual(self.tdm.get_total_unigram_count(), 36)

class TestLarge_int_format(TestCase):

    def test_large_int_format(self):
        self.assertEqual(large_int_format(1), '1')
        self.assertEqual(large_int_format(6), '6')
        self.assertEqual(large_int_format(10), '10')
        self.assertEqual(large_int_format(19), '10')
        self.assertEqual(large_int_format(88), '80')
        self.assertEqual(large_int_format(999), '900')
        self.assertEqual(large_int_format(1001), '1k')
        self.assertEqual(large_int_format(205001), '200k')
        self.assertEqual(large_int_format(2050010), '2mm')
        self.assertEqual(large_int_format(205000010), '200mm')
        self.assertEqual(large_int_format(2050000010), '2b')

def test_large_int_format(self):
    self.assertEqual(large_int_format(1), '1')
    self.assertEqual(large_int_format(6), '6')
    self.assertEqual(large_int_format(10), '10')
    self.assertEqual(large_int_format(19), '10')
    self.assertEqual(large_int_format(88), '80')
    self.assertEqual(large_int_format(999), '900')
    self.assertEqual(large_int_format(1001), '1k')
    self.assertEqual(large_int_format(205001), '200k')
    self.assertEqual(large_int_format(2050010), '2mm')
    self.assertEqual(large_int_format(205000010), '200mm')
    self.assertEqual(large_int_format(2050000010), '2b')

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

def make_assembler(self):
    scatterplot_structure = ScatterplotStructure(self.make_adapter())
    return BasicHTMLFromScatterplotStructure(scatterplot_structure)

def test_save_svg_button(self):
    scatterplot_structure = ScatterplotStructure(self.make_adapter(), save_svg_button=True)
    assembly = BasicHTMLFromScatterplotStructure(scatterplot_structure)
    html = assembly.to_html()
    self.assertEqual(scatterplot_structure.call_build_visualization_in_javascript(), self.get_params({11: 'true'}))
    self.assertFalse('<!-- INSERT SCRIPT -->' in html)

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

def get_js_to_call_build_scatterplot(self, object_name='plotInterface'):
    return object_name + ' = ' + self.call_build_visualization_in_javascript()

def get_js_to_call_build_scatterplot_with_a_function(self, object_name='plotInterface', function_name=None):
    if function_name is None:
        function_name = 'build' + object_name
    function_text = 'function ' + function_name + '() { return ' + self.call_build_visualization_in_javascript() + ';}'
    return function_text + '\n\n' + object_name + ' = ' + function_name + '();'

