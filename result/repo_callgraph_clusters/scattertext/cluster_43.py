# Cluster 43

class SemioticSquareBase(object):

    def get_labels(self):
        raise NotImplementedError()

    def get_axes(self, **kwargs):
        raise NotImplementedError()

    def get_lexicons(self, num_terms=10):
        raise NotImplementedError()

def get_labels(self):
    raise NotImplementedError()

def get_axes(self, **kwargs):
    raise NotImplementedError()

def get_lexicons(self, num_terms=10):
    raise NotImplementedError()

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

def get_category_association(self, **kwargs):
    raise NotImplementedError()

def get_category_association_and_freqs(self, **kwargs):
    raise NotImplementedError()

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

@abc.abstractmethod
def _get_surface_string(self, raw_token: str) -> str:
    raise NotImplementedError()

class AllCategoryScorer(abc.ABC):

    def __init__(self, corpus=Optional, non_text: bool=False, term_ranker: type=AbsoluteFrequencyRanker, term_ranker_kwargs: Optional[Dict]=None, **kwargs):
        self.term_ranker_kwargs_ = term_ranker_kwargs
        self.term_ranker_factory_ = term_ranker
        self.set_non_text(non_text)
        self._free_init(**kwargs)
        self.set_corpus(corpus)

    def set_corpus(self, corpus: Optional) -> 'AllCategoryScorer':
        self.corpus_ = corpus
        if corpus is None:
            self.term_ranker_ = None
        else:
            self.term_ranker_: Optional[TermRanker] = self.term_ranker_factory_(corpus, **self.term_ranker_kwargs_ if self.term_ranker_kwargs_ is not None else {})
        return self

    def set_non_text(self, non_text: bool) -> 'AllCategoryScorer':
        self.non_text_ = non_text
        return self

    def _free_init(self, **kwargs):
        pass

    @abc.abstractmethod
    def get_rank_freq_df(self) -> pd.DataFrame:
        raise NotImplementedError()

    def get_score_df(self, score_append=' Score', freq_append=' Freq') -> pd.DataFrame:
        df = pd.pivot_table(self.get_rank_freq_df(), index='Term', values=['Score', 'Frequency'], columns=['Category'])
        df.columns = [category + {'Score': score_append, 'Frequency': freq_append}[metric_type] for metric_type, category in df.columns.to_flat_index()]
        return df[lambda df: list(sorted(df.columns))]

@abc.abstractmethod
def get_rank_freq_df(self) -> pd.DataFrame:
    raise NotImplementedError()

class GraphRenderer(object):

    def get_graph(self):
        raise NotImplementedError()

    def get_javascript(self):
        raise NotImplementedError

def get_graph(self):
    raise NotImplementedError()

class CategoryProjectionEvaluator(object):

    def evaluate(self, category_projection):
        raise NotImplementedError()

def evaluate(self, category_projection):
    raise NotImplementedError()

class CategoryProjectorBase(object):

    def project(self, term_doc_mat, x_dim=0, y_dim=1):
        """
        Returns a projection of the categories

        :param term_doc_mat: a TermDocMatrix
        :return: CategoryProjection
        """
        return self._project_category_corpus(self._get_category_metadata_corpus(term_doc_mat), x_dim, y_dim)

    def project_with_metadata(self, term_doc_mat, x_dim=0, y_dim=1):
        """
        Returns a projection of the

        :param term_doc_mat: a TermDocMatrix
        :return: CategoryProjection
        """
        return self._project_category_corpus(self._get_category_metadata_corpus_and_replace_terms(term_doc_mat), x_dim, y_dim)

    def _project_category_corpus(self, category_corpus, x_dim=0, y_dim=1):
        raise NotImplementedError()

    def _get_category_metadata_corpus(self, corpus):
        raise NotImplementedError()

    def _get_category_metadata_corpus_and_replace_terms(self, corpus):
        raise NotImplementedError()

    def get_category_embeddings(self, corpus):
        """
        :param corpus: TermDocMatrix

        :return: np.array, matrix of (num categories, embedding dimension) dimensions
        """
        raise NotImplementedError()

def _project_category_corpus(self, category_corpus, x_dim=0, y_dim=1):
    raise NotImplementedError()

def _get_category_metadata_corpus(self, corpus):
    raise NotImplementedError()

def _get_category_metadata_corpus_and_replace_terms(self, corpus):
    raise NotImplementedError()

def get_category_embeddings(self, corpus):
    """
        :param corpus: TermDocMatrix

        :return: np.array, matrix of (num categories, embedding dimension) dimensions
        """
    raise NotImplementedError()

class TermScorer(ABC):

    @abstractmethod
    def get_scores(self, cat_word_counts: np.array, not_cat_word_counts: np.array) -> np.array:
        raise NotImplementedError()

@abstractmethod
def get_scores(self, cat_word_counts: np.array, not_cat_word_counts: np.array) -> np.array:
    raise NotImplementedError()

class DiachronicVisualizer(object):

    @staticmethod
    def visualize(display_df):
        raise NotImplementedError()

@staticmethod
def visualize(display_df):
    raise NotImplementedError()

class DistanceMeasureBase(object):

    @staticmethod
    def distances(fixed_x, fixed_y, x_vec, y_vec):
        """

        :param fixed_x: float
        :param fixed_y: float
        :param x_vec: np.array[float]
        :param y_vec: np.array[float]
        :return: np.array[float]
        """
        raise NotImplementedError()

@staticmethod
def distances(fixed_x, fixed_y, x_vec, y_vec):
    """

        :param fixed_x: float
        :param fixed_y: float
        :param x_vec: np.array[float]
        :param y_vec: np.array[float]
        :return: np.array[float]
        """
    raise NotImplementedError()

