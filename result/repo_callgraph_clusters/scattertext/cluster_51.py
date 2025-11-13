# Cluster 51

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

def _get_word2vec_model(self, word2vec_model):
    return self._default_word2vec_model() if word2vec_model is None else word2vec_model

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

def _get_word2vec_model(self, word2vec_model):
    return self._default_word2vec_model() if word2vec_model is None else word2vec_model

