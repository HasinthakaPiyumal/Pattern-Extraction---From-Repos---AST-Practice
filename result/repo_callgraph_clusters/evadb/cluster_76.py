# Cluster 76

class TableRef:
    """
    Attributes:
        : can be one of the following based on the query type:
            TableInfo: expression of table name and database name,
            TableValuedExpression: lateral function calls
            SelectStatement: select statement in case of nested queries,
            JoinNode: join node in case of join queries
        sample_freq: sampling frequency for the table reference
    """

    def __init__(self, table: Union[TableInfo, TableValuedExpression, SelectStatement, JoinNode], alias: Alias=None, sample_freq: float=None, sample_type: str=None, get_audio: bool=False, get_video: bool=False, chunk_params: dict={}):
        self._ref_handle = table
        self._sample_freq = sample_freq
        self._sample_type = sample_type
        self._get_audio = get_audio
        self._get_video = get_video
        self.chunk_params = chunk_params
        self.alias = alias or self.generate_alias()

    @property
    def sample_freq(self):
        return self._sample_freq

    @property
    def sample_type(self):
        return self._sample_type

    @property
    def get_audio(self):
        return self._get_audio

    @property
    def get_video(self):
        return self._get_video

    @get_audio.setter
    def get_audio(self, get_audio):
        self._get_audio = get_audio

    @get_video.setter
    def get_video(self, get_video):
        self._get_video = get_video

    def is_table_atom(self) -> bool:
        return isinstance(self._ref_handle, TableInfo)

    def is_table_valued_expr(self) -> bool:
        return isinstance(self._ref_handle, TableValuedExpression)

    def is_select(self) -> bool:
        return isinstance(self._ref_handle, SelectStatement)

    def is_join(self) -> bool:
        return isinstance(self._ref_handle, JoinNode)

    @property
    def ref_handle(self) -> Union[TableInfo, TableValuedExpression, SelectStatement, JoinNode]:
        return self._ref_handle

    @property
    def table(self) -> TableInfo:
        assert isinstance(self._ref_handle, TableInfo), 'Expected                 TableInfo, got {}'.format(type(self._ref_handle))
        return self._ref_handle

    @property
    def table_valued_expr(self) -> TableValuedExpression:
        assert isinstance(self._ref_handle, TableValuedExpression), 'Expected                 TableValuedExpression, got {}'.format(type(self._ref_handle))
        return self._ref_handle

    @property
    def join_node(self) -> JoinNode:
        assert isinstance(self._ref_handle, JoinNode), 'Expected                 JoinNode, got {}'.format(type(self._ref_handle))
        return self._ref_handle

    @property
    def select_statement(self) -> SelectStatement:
        assert isinstance(self._ref_handle, SelectStatement), 'Expected                 SelectStatement, got{}'.format(type(self._ref_handle))
        return self._ref_handle

    def generate_alias(self) -> Alias:
        if isinstance(self._ref_handle, TableInfo):
            return Alias(self._ref_handle.table_name.lower())

    def __str__(self):
        parts = []
        if self.is_select():
            parts.append(f'( {str(self._ref_handle)} ) AS {self.alias}')
        else:
            parts.append(str(self._ref_handle))
        if self.sample_freq is not None:
            parts.append(str(self.sample_freq))
        if self.sample_type is not None:
            parts.append(str(self.sample_type))
        if self.chunk_params is not None:
            parts.append(' '.join([f'{key}: {value}' for key, value in self.chunk_params.items()]))
        return ' '.join(parts)

    def __eq__(self, other):
        if not isinstance(other, TableRef):
            return False
        return self._ref_handle == other._ref_handle and self.alias == other.alias and (self.sample_freq == other.sample_freq) and (self.sample_type == other.sample_type) and (self.get_video == other.get_video) and (self.get_audio == other.get_audio) and (self.chunk_params == other.chunk_params)

    def __hash__(self) -> int:
        return hash((self._ref_handle, self.alias, self.sample_freq, self.sample_type, self.get_video, self.get_audio, frozenset(self.chunk_params.items())))

def __init__(self, table: Union[TableInfo, TableValuedExpression, SelectStatement, JoinNode], alias: Alias=None, sample_freq: float=None, sample_type: str=None, get_audio: bool=False, get_video: bool=False, chunk_params: dict={}):
    self._ref_handle = table
    self._sample_freq = sample_freq
    self._sample_type = sample_type
    self._get_audio = get_audio
    self._get_video = get_video
    self.chunk_params = chunk_params
    self.alias = alias or self.generate_alias()

