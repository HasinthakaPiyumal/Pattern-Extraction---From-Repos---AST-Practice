# Cluster 19

class TopK(tf.keras.Model, abc.ABC):
    """TopK layer 接口
    注意，必须实现两个方法
    1、index: 创建索引
    2、call: 检索索引
    """

    def __init__(self, k: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._k = k

    @abc.abstractmethod
    def index(self, candidates: Union[tf.Tensor, tf.data.Dataset], identifiers: Optional[Union[tf.Tensor, tf.data.Dataset]]=None) -> 'TopK':
        """创建索引 
        args:
            candidates: 候选 embeddings
            identifiers: 候选 embeddings对应标识 (Opt)
        returns:
            Self.
        """
        raise NotImplementedError('Implementers must provide `index` method.')

    @abc.abstractmethod
    def call(self, queries: Union[tf.Tensor, Dict[Text, tf.Tensor]], k: Optional[int]=None, **kwargs) -> Tuple[tf.Tensor, tf.Tensor]:
        """检索索引
        args:
            queries: queries embeddings,
            k: 返回候选个数
        returns:
            Tuple(top k candidates scores, top k candidates indentifiers)
        """
        raise NotImplementedError()

    @tf.function
    def query_with_exclusions(self, queries: Union[tf.Tensor, Dict[Text, tf.Tensor]], exclusions: tf.Tensor, k: Optional[int]=None) -> Tuple[tf.Tensor, tf.Tensor]:
        """检索索引并过滤exclusions
        Args:
            queries: queries embeddings,
            exclusions: candidates identifiers. 从TopK的候选集中过滤指定的item.
            k: 返回候选个数
        Returns:
            Tuple(top k candidates scores, top k candidates indetifiers)
        """
        k = k if k is not None else self._k
        adjusted_k = k + exclusions.shape[1]
        scores, identifiers = self(queries=queries, k=adjusted_k)
        return _exclude(scores, identifiers, exclusions, adjusted_k)

    def _reset_tf_function_cache(self):
        """Resets the tf.function cache."""
        if hasattr(self.query_with_exclusions, 'python_function'):
            self.query_with_exclusions = tf.function(self.query_with_exclusions.python_function)

def _reset_tf_function_cache(self):
    """Resets the tf.function cache."""
    if hasattr(self.query_with_exclusions, 'python_function'):
        self.query_with_exclusions = tf.function(self.query_with_exclusions.python_function)

