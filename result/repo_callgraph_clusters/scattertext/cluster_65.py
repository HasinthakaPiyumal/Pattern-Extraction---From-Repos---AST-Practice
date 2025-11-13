# Cluster 65

class FeatsFromTopicModelBase(ABC):

    def __init__(self, topic_model):
        self._topic_model = topic_model
        self._lexicon_df = self._get_lexicon_df_from_topic_model(topic_model)

    def _get_lexicon_df_from_topic_model(self, topic_model):
        return pd.DataFrame(pd.Series(topic_model).apply(pd.Series).reset_index()).melt(id_vars=['index'])[['index', 'value']].rename(columns={'index': 'cat', 'value': 'term'}).set_index('term')

    def _analyze(self, doc):
        text_df = pd.DataFrame(pd.Series(self._get_terms_from_doc(doc))).join(self._lexicon_df).dropna().groupby('cat').sum()
        return text_df

    def get_doc_metadata(self, doc, prefix=''):
        feature_counter = Counter()
        if version_info[0] >= 3:
            doc = str(doc)
        for category, score in self._analyze(doc).to_dict()[0].items():
            feature_counter[prefix + category] = int(score)
        return feature_counter

    @abstractmethod
    def _get_terms_from_doc(self, doc):
        pass

def __init__(self, topic_model):
    self._topic_model = topic_model
    self._lexicon_df = self._get_lexicon_df_from_topic_model(topic_model)

