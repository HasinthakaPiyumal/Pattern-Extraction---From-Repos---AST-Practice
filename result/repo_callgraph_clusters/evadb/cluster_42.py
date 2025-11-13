# Cluster 42

class DeleteExecutor(AbstractExecutor):
    """ """

    def __init__(self, db: EvaDBDatabase, node: ProjectPlan):
        super().__init__(db, node)
        self.predicate = node.where_clause

    def predicate_node_to_filter_clause(self, table: TableCatalogEntry, predicate_node: ComparisonExpression):
        filter_clause = None
        left = predicate_node.get_child(0)
        right = predicate_node.get_child(1)
        if isinstance(left, TupleValueExpression):
            column = left.name
            x = table.columns[column]
        elif isinstance(left, ConstantValueExpression):
            value = left.value
            x = value
        else:
            left_filter_clause = self.predicate_node_to_filter_clause(table, left)
        if isinstance(right, TupleValueExpression):
            column = right.name
            y = table.columns[column]
        elif isinstance(right, ConstantValueExpression):
            value = right.value
            y = value
        else:
            right_filter_clause = self.predicate_node_to_filter_clause(table, right)
        if isinstance(predicate_node, LogicalExpression):
            if predicate_node.etype == ExpressionType.LOGICAL_AND:
                filter_clause = and_(left_filter_clause, right_filter_clause)
            elif predicate_node.etype == ExpressionType.LOGICAL_OR:
                filter_clause = or_(left_filter_clause, right_filter_clause)
        elif isinstance(predicate_node, ComparisonExpression):
            assert predicate_node.etype != ExpressionType.COMPARE_CONTAINS and predicate_node.etype != ExpressionType.COMPARE_IS_CONTAINED, f'Predicate type {predicate_node.etype} not supported in delete'
            if predicate_node.etype == ExpressionType.COMPARE_EQUAL:
                filter_clause = x == y
            elif predicate_node.etype == ExpressionType.COMPARE_GREATER:
                filter_clause = x > y
            elif predicate_node.etype == ExpressionType.COMPARE_LESSER:
                filter_clause = x < y
            elif predicate_node.etype == ExpressionType.COMPARE_GEQ:
                filter_clause = x >= y
            elif predicate_node.etype == ExpressionType.COMPARE_LEQ:
                filter_clause = x <= y
            elif predicate_node.etype == ExpressionType.COMPARE_NEQ:
                filter_clause = x != y
        return filter_clause

    def exec(self, *args, **kwargs) -> Iterator[Batch]:
        table_catalog = self.node.table_ref.table.table_obj
        storage_engine = StorageEngine.factory(self.db, table_catalog)
        assert table_catalog.table_type == TableType.STRUCTURED_DATA, 'DELETE only implemented for structured data'
        table_to_delete_from = storage_engine._try_loading_table_via_reflection(table_catalog.name)
        sqlalchemy_filter_clause = self.predicate_node_to_filter_clause(table_to_delete_from, predicate_node=self.predicate)
        storage_engine.delete(table_catalog, sqlalchemy_filter_clause)
        yield Batch(pd.DataFrame(['Deleted rows']))

def predicate_node_to_filter_clause(self, table: TableCatalogEntry, predicate_node: ComparisonExpression):
    filter_clause = None
    left = predicate_node.get_child(0)
    right = predicate_node.get_child(1)
    if isinstance(left, TupleValueExpression):
        column = left.name
        x = table.columns[column]
    elif isinstance(left, ConstantValueExpression):
        value = left.value
        x = value
    else:
        left_filter_clause = self.predicate_node_to_filter_clause(table, left)
    if isinstance(right, TupleValueExpression):
        column = right.name
        y = table.columns[column]
    elif isinstance(right, ConstantValueExpression):
        value = right.value
        y = value
    else:
        right_filter_clause = self.predicate_node_to_filter_clause(table, right)
    if isinstance(predicate_node, LogicalExpression):
        if predicate_node.etype == ExpressionType.LOGICAL_AND:
            filter_clause = and_(left_filter_clause, right_filter_clause)
        elif predicate_node.etype == ExpressionType.LOGICAL_OR:
            filter_clause = or_(left_filter_clause, right_filter_clause)
    elif isinstance(predicate_node, ComparisonExpression):
        assert predicate_node.etype != ExpressionType.COMPARE_CONTAINS and predicate_node.etype != ExpressionType.COMPARE_IS_CONTAINED, f'Predicate type {predicate_node.etype} not supported in delete'
        if predicate_node.etype == ExpressionType.COMPARE_EQUAL:
            filter_clause = x == y
        elif predicate_node.etype == ExpressionType.COMPARE_GREATER:
            filter_clause = x > y
        elif predicate_node.etype == ExpressionType.COMPARE_LESSER:
            filter_clause = x < y
        elif predicate_node.etype == ExpressionType.COMPARE_GEQ:
            filter_clause = x >= y
        elif predicate_node.etype == ExpressionType.COMPARE_LEQ:
            filter_clause = x <= y
        elif predicate_node.etype == ExpressionType.COMPARE_NEQ:
            filter_clause = x != y
    return filter_clause

class AggregationExpression(AbstractExpression):

    def __init__(self, exp_type: ExpressionType, left: AbstractExpression, right: AbstractExpression):
        children = []
        if left is not None:
            children.append(left)
        if right is not None:
            children.append(right)
        super().__init__(exp_type, rtype=ExpressionReturnType.INTEGER, children=children)

    def evaluate(self, *args, **kwargs):
        batch: Batch = self.get_child(0).evaluate(*args, **kwargs)
        if self.etype == ExpressionType.AGGREGATION_FIRST:
            batch = batch[0]
        elif self.etype == ExpressionType.AGGREGATION_LAST:
            batch = batch[-1]
        elif self.etype == ExpressionType.AGGREGATION_SEGMENT:
            batch = Batch.stack(batch)
        elif self.etype == ExpressionType.AGGREGATION_SUM:
            batch.aggregate('sum')
        elif self.etype == ExpressionType.AGGREGATION_COUNT:
            batch.aggregate('count')
        elif self.etype == ExpressionType.AGGREGATION_AVG:
            batch.aggregate('mean')
        elif self.etype == ExpressionType.AGGREGATION_MIN:
            batch.aggregate('min')
        elif self.etype == ExpressionType.AGGREGATION_MAX:
            batch.aggregate('max')
        batch.reset_index()
        column_name = self.etype.name
        if column_name.find('AGGREGATION_') != -1:
            updated_column_name = column_name.replace('AGGREGATION_', '')
            batch.modify_column_alias(updated_column_name)
        return batch

    def get_symbol(self) -> str:
        if self.etype == ExpressionType.AGGREGATION_FIRST:
            return 'FIRST'
        if self.etype == ExpressionType.AGGREGATION_LAST:
            return 'LAST'
        if self.etype == ExpressionType.AGGREGATION_SEGMENT:
            return 'SEGMENT'
        if self.etype == ExpressionType.AGGREGATION_SUM:
            return 'SUM'
        elif self.etype == ExpressionType.AGGREGATION_COUNT:
            return 'COUNT'
        elif self.etype == ExpressionType.AGGREGATION_AVG:
            return 'AVG'
        elif self.etype == ExpressionType.AGGREGATION_MIN:
            return 'MIN'
        elif self.etype == ExpressionType.AGGREGATION_MAX:
            return 'MAX'
        else:
            raise NotImplementedError

    def signature(self) -> str:
        child_sigs = []
        for child in self.children:
            child_sigs.append(child.signature())
        return f'{self.get_symbol().lower()}({','.join(child_sigs)})'

    def __str__(self) -> str:
        expr_str = ''
        if self.etype:
            expr_str = f'{str(self.get_symbol())}()'
        return expr_str

    def __eq__(self, other):
        is_subtree_equal = super().__eq__(other)
        if not isinstance(other, AggregationExpression):
            return False
        return is_subtree_equal and self.etype == other.etype

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.etype))

def signature(self) -> str:
    child_sigs = []
    for child in self.children:
        child_sigs.append(child.signature())
    return f'{self.get_symbol().lower()}({','.join(child_sigs)})'

def __str__(self) -> str:
    expr_str = ''
    if self.etype:
        expr_str = f'{str(self.get_symbol())}()'
    return expr_str

class ArithmeticExpression(AbstractExpression):

    def __init__(self, exp_type: ExpressionType, left: AbstractExpression, right: AbstractExpression):
        children = []
        if left is not None:
            children.append(left)
        if right is not None:
            children.append(right)
        super().__init__(exp_type, rtype=ExpressionReturnType.FLOAT, children=children)

    def evaluate(self, *args, **kwargs):
        vl = self.get_child(0).evaluate(*args, **kwargs)
        vr = self.get_child(1).evaluate(*args, **kwargs)
        return Batch.combine_batches(vl, vr, self.etype)

    def __eq__(self, other):
        is_subtree_equal = super().__eq__(other)
        if not isinstance(other, ArithmeticExpression):
            return False
        return is_subtree_equal and self.etype == other.etype

def evaluate(self, *args, **kwargs):
    vl = self.get_child(0).evaluate(*args, **kwargs)
    vr = self.get_child(1).evaluate(*args, **kwargs)
    return Batch.combine_batches(vl, vr, self.etype)

class LogicalExpression(AbstractExpression):

    def __init__(self, exp_type: ExpressionType, left: AbstractExpression, right: AbstractExpression):
        children = []
        if left is not None:
            children.append(left)
        if right is not None:
            children.append(right)
        super().__init__(exp_type, rtype=ExpressionReturnType.BOOLEAN, children=children)

    def evaluate(self, batch, **kwargs):
        if self.get_children_count() == 2:
            left_batch = self.get_child(0).evaluate(batch, **kwargs)
            if self.etype == ExpressionType.LOGICAL_AND:
                if left_batch.all_false():
                    return left_batch
                mask = left_batch.create_mask()
            elif self.etype == ExpressionType.LOGICAL_OR:
                if left_batch.all_true():
                    return left_batch
                mask = left_batch.create_inverted_mask()
            pushdown_batch = batch[mask]
            pushdown_batch.reset_index()
            right_batch = self.get_child(1).evaluate(pushdown_batch, **kwargs)
            left_batch.update_indices(mask, right_batch)
            return left_batch
        else:
            batch = self.get_child(0).evaluate(batch, **kwargs)
            if self.etype == ExpressionType.LOGICAL_NOT:
                batch.invert()
                return batch

    def __eq__(self, other):
        is_subtree_equal = super().__eq__(other)
        if not isinstance(other, LogicalExpression):
            return False
        return is_subtree_equal and self.etype == other.etype

    def get_symbol(self) -> str:
        if self.etype == ExpressionType.LOGICAL_AND:
            return 'AND'
        elif self.etype == ExpressionType.LOGICAL_OR:
            return 'OR'
        elif self.etype == ExpressionType.LOGICAL_NOT:
            return 'NOT'
        else:
            raise NotImplementedError

    def __str__(self) -> str:
        expr_str = '('
        if self.get_child(0):
            expr_str += f'{str(self.get_child(0))}'
        if self.etype:
            expr_str += f' {str(self.get_symbol())} '
        if self.get_child(1):
            expr_str += f'{str(self.get_child(1))}'
        expr_str += ')'
        return expr_str

    def __hash__(self) -> int:
        return super().__hash__()

def evaluate(self, batch, **kwargs):
    if self.get_children_count() == 2:
        left_batch = self.get_child(0).evaluate(batch, **kwargs)
        if self.etype == ExpressionType.LOGICAL_AND:
            if left_batch.all_false():
                return left_batch
            mask = left_batch.create_mask()
        elif self.etype == ExpressionType.LOGICAL_OR:
            if left_batch.all_true():
                return left_batch
            mask = left_batch.create_inverted_mask()
        pushdown_batch = batch[mask]
        pushdown_batch.reset_index()
        right_batch = self.get_child(1).evaluate(pushdown_batch, **kwargs)
        left_batch.update_indices(mask, right_batch)
        return left_batch
    else:
        batch = self.get_child(0).evaluate(batch, **kwargs)
        if self.etype == ExpressionType.LOGICAL_NOT:
            batch.invert()
            return batch

def __str__(self) -> str:
    expr_str = '('
    if self.get_child(0):
        expr_str += f'{str(self.get_child(0))}'
    if self.etype:
        expr_str += f' {str(self.get_symbol())} '
    if self.get_child(1):
        expr_str += f'{str(self.get_child(1))}'
    expr_str += ')'
    return expr_str

class AbstractExpression(ABC):

    def __init__(self, exp_type: ExpressionType, rtype: ExpressionReturnType=ExpressionReturnType.INVALID, children=None):
        self._etype = exp_type
        self._rtype = rtype
        self._children = children or []

    def get_child(self, index: int):
        assert self._children is not None
        assert index >= 0 and index < len(self._children)
        return self._children[index]

    @property
    def children(self):
        return self._children

    @children.setter
    def children(self, children):
        self._children = children

    def append_child(self, child):
        self._children.append(child)

    def get_children_count(self) -> int:
        return len(self._children)

    @property
    def etype(self) -> ExpressionType:
        return self._etype

    @property
    def rtype(self) -> ExpressionReturnType:
        return self._rtype

    @abstractmethod
    def evaluate(self, *args, **kwargs):
        pass

    def __eq__(self, other):
        is_subtree_equal = True
        if not isinstance(other, AbstractExpression):
            return False
        if self.get_children_count() != other.get_children_count():
            return False
        for child1, child2 in zip(self.children, other.children):
            is_subtree_equal = is_subtree_equal and child1 == child2
        return is_subtree_equal

    def __hash__(self) -> int:
        return hash((self.etype, self.rtype, tuple(self.children)))

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            setattr(result, k, deepcopy(v, memo))
        return result

    def copy(self):
        """Returns a deepcopy of the expression tree."""
        return deepcopy(self)

    def walk(self, bfs=True):
        """
        Returns a generator which visits all nodes in expression tree.

        Args:
            bfs (bool): if True, use breadth-first search (BFS) traversal order;
                if False, use the depth-first search (DFS) traversal order

        Returns:
            the generator object.
        """
        if bfs:
            yield from self.bfs()
        else:
            yield from self.dfs()

    def bfs(self):
        """Returns a generator which visits all nodes in expression tree in
        breadth-first search (BFS) traversal order.

        Returns:
            the generator object.
        """
        queue = deque([self])
        while queue:
            node = queue.popleft()
            yield node
            for child in node.children:
                queue.append(child)

    def dfs(self):
        """Returns a generator which visits all nodes in expression tree in depth-first
        search (DFS) traversal order.

        Returns:
            the generator object.
        """
        yield self
        for child in self.children:
            yield from child.dfs()

    def find_all(self, expression_type: Any):
        """Returns a generator which visits all the nodes in expression tree and yields one that matches the passed `expression_type`.

        Args:
            expression_type (Any): expression type to match with

        Returns:
            the generator object.
        """
        for node in self.bfs():
            if isinstance(node, expression_type):
                yield node

def __eq__(self, other):
    is_subtree_equal = True
    if not isinstance(other, AbstractExpression):
        return False
    if self.get_children_count() != other.get_children_count():
        return False
    for child1, child2 in zip(self.children, other.children):
        is_subtree_equal = is_subtree_equal and child1 == child2
    return is_subtree_equal

class ComparisonExpression(AbstractExpression):

    def __init__(self, exp_type: ExpressionType, left: AbstractExpression, right: AbstractExpression):
        children = []
        if left is not None:
            children.append(left)
        if right is not None:
            children.append(right)
        super().__init__(exp_type, rtype=ExpressionReturnType.BOOLEAN, children=children)

    def evaluate(self, *args, **kwargs):
        lbatch = self.get_child(0).evaluate(*args, **kwargs)
        rbatch = self.get_child(1).evaluate(*args, **kwargs)
        assert len(lbatch) == len(rbatch), f'Left and Right batch does not have equal elements: left: {len(lbatch)} right: {len(rbatch)}'
        assert self.etype in [ExpressionType.COMPARE_EQUAL, ExpressionType.COMPARE_GREATER, ExpressionType.COMPARE_LESSER, ExpressionType.COMPARE_GEQ, ExpressionType.COMPARE_LEQ, ExpressionType.COMPARE_NEQ, ExpressionType.COMPARE_CONTAINS, ExpressionType.COMPARE_IS_CONTAINED, ExpressionType.COMPARE_LIKE], f'Expression type not supported {self.etype}'
        if self.etype == ExpressionType.COMPARE_EQUAL:
            return Batch.from_eq(lbatch, rbatch)
        elif self.etype == ExpressionType.COMPARE_GREATER:
            return Batch.from_greater(lbatch, rbatch)
        elif self.etype == ExpressionType.COMPARE_LESSER:
            return Batch.from_lesser(lbatch, rbatch)
        elif self.etype == ExpressionType.COMPARE_GEQ:
            return Batch.from_greater_eq(lbatch, rbatch)
        elif self.etype == ExpressionType.COMPARE_LEQ:
            return Batch.from_lesser_eq(lbatch, rbatch)
        elif self.etype == ExpressionType.COMPARE_NEQ:
            return Batch.from_not_eq(lbatch, rbatch)
        elif self.etype == ExpressionType.COMPARE_CONTAINS:
            return Batch.compare_contains(lbatch, rbatch)
        elif self.etype == ExpressionType.COMPARE_IS_CONTAINED:
            return Batch.compare_is_contained(lbatch, rbatch)
        elif self.etype == ExpressionType.COMPARE_LIKE:
            return Batch.compare_like(lbatch, rbatch)

    def get_symbol(self) -> str:
        if self.etype == ExpressionType.COMPARE_EQUAL:
            return '='
        elif self.etype == ExpressionType.COMPARE_GREATER:
            return '>'
        elif self.etype == ExpressionType.COMPARE_LESSER:
            return '<'
        elif self.etype == ExpressionType.COMPARE_GEQ:
            return '>='
        elif self.etype == ExpressionType.COMPARE_LEQ:
            return '<='
        elif self.etype == ExpressionType.COMPARE_NEQ:
            return '!='
        elif self.etype == ExpressionType.COMPARE_CONTAINS:
            return '@>'
        elif self.etype == ExpressionType.COMPARE_IS_CONTAINED:
            return '<@'

    def __str__(self) -> str:
        expr_str = '('
        if self.get_child(0):
            expr_str += f'{self.get_child(0)}'
        if self.etype:
            expr_str += f' {self.get_symbol()} '
        if self.get_child(1):
            expr_str += f'{self.get_child(1)}'
        expr_str += ')'
        return expr_str

    def __eq__(self, other):
        is_subtree_equal = super().__eq__(other)
        if not isinstance(other, ComparisonExpression):
            return False
        return is_subtree_equal and self.etype == other.etype

    def __hash__(self) -> int:
        return super().__hash__()

def evaluate(self, *args, **kwargs):
    lbatch = self.get_child(0).evaluate(*args, **kwargs)
    rbatch = self.get_child(1).evaluate(*args, **kwargs)
    assert len(lbatch) == len(rbatch), f'Left and Right batch does not have equal elements: left: {len(lbatch)} right: {len(rbatch)}'
    assert self.etype in [ExpressionType.COMPARE_EQUAL, ExpressionType.COMPARE_GREATER, ExpressionType.COMPARE_LESSER, ExpressionType.COMPARE_GEQ, ExpressionType.COMPARE_LEQ, ExpressionType.COMPARE_NEQ, ExpressionType.COMPARE_CONTAINS, ExpressionType.COMPARE_IS_CONTAINED, ExpressionType.COMPARE_LIKE], f'Expression type not supported {self.etype}'
    if self.etype == ExpressionType.COMPARE_EQUAL:
        return Batch.from_eq(lbatch, rbatch)
    elif self.etype == ExpressionType.COMPARE_GREATER:
        return Batch.from_greater(lbatch, rbatch)
    elif self.etype == ExpressionType.COMPARE_LESSER:
        return Batch.from_lesser(lbatch, rbatch)
    elif self.etype == ExpressionType.COMPARE_GEQ:
        return Batch.from_greater_eq(lbatch, rbatch)
    elif self.etype == ExpressionType.COMPARE_LEQ:
        return Batch.from_lesser_eq(lbatch, rbatch)
    elif self.etype == ExpressionType.COMPARE_NEQ:
        return Batch.from_not_eq(lbatch, rbatch)
    elif self.etype == ExpressionType.COMPARE_CONTAINS:
        return Batch.compare_contains(lbatch, rbatch)
    elif self.etype == ExpressionType.COMPARE_IS_CONTAINED:
        return Batch.compare_is_contained(lbatch, rbatch)
    elif self.etype == ExpressionType.COMPARE_LIKE:
        return Batch.compare_like(lbatch, rbatch)

def __str__(self) -> str:
    expr_str = '('
    if self.get_child(0):
        expr_str += f'{self.get_child(0)}'
    if self.etype:
        expr_str += f' {self.get_symbol()} '
    if self.get_child(1):
        expr_str += f'{self.get_child(1)}'
    expr_str += ')'
    return expr_str

