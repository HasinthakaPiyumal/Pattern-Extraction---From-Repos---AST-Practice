# Cluster 35

@pytest.mark.notparallel
class NativeExecutorTest(unittest.TestCase):

    def setUp(self):
        self.evadb = get_evadb_for_testing()
        self.evadb.catalog().reset()

    def tearDown(self):
        shutdown_ray()
        self._drop_table_in_native_database()
        self._drop_table_in_evadb_database()

    def _create_table_in_native_database(self):
        execute_query_fetch_all(self.evadb, 'USE test_data_source {\n                CREATE TABLE test_table (\n                    name VARCHAR(10),\n                    Age INT,\n                    comment VARCHAR (100)\n                )\n            }')

    def _insert_value_into_native_database(self, col1, col2, col3):
        execute_query_fetch_all(self.evadb, f"USE test_data_source {{\n                INSERT INTO test_table (\n                    name, Age, comment\n                ) VALUES (\n                    '{col1}', {col2}, '{col3}'\n                )\n            }}")

    def _drop_table_in_native_database(self):
        execute_query_fetch_all(self.evadb, 'USE test_data_source {\n                DROP TABLE IF EXISTS test_table\n            }')
        execute_query_fetch_all(self.evadb, 'USE test_data_source {\n                DROP TABLE IF EXISTS derived_table\n            }')

    def _drop_table_in_evadb_database(self):
        execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS eva_table;')

    def _create_evadb_table_using_select_query(self):
        execute_query_fetch_all(self.evadb, 'CREATE TABLE eva_table AS SELECT name, Age FROM test_data_source.test_table;')
        res_batch = execute_query_fetch_all(self.evadb, 'Select * from eva_table')
        self.assertEqual(len(res_batch), 2)
        self.assertEqual(res_batch.frames['eva_table.name'][0], 'aa')
        self.assertEqual(res_batch.frames['eva_table.age'][0], 1)
        self.assertEqual(res_batch.frames['eva_table.name'][1], 'bb')
        self.assertEqual(res_batch.frames['eva_table.age'][1], 2)

    def _create_native_table_using_select_query(self):
        execute_query_fetch_all(self.evadb, 'CREATE TABLE test_data_source.derived_table AS SELECT name, age FROM test_data_source.test_table;')
        res_batch = execute_query_fetch_all(self.evadb, 'SELECT * FROM test_data_source.derived_table')
        self.assertEqual(len(res_batch), 2)
        self.assertEqual(res_batch.frames['derived_table.name'][0], 'aa')
        self.assertEqual(res_batch.frames['derived_table.age'][0], 1)
        self.assertEqual(res_batch.frames['derived_table.name'][1], 'bb')
        self.assertEqual(res_batch.frames['derived_table.age'][1], 2)

    def _execute_evadb_query(self):
        self._create_table_in_native_database()
        self._insert_value_into_native_database('aa', 1, 'aaaa')
        self._insert_value_into_native_database('bb', 2, 'bbbb')
        res_batch = execute_query_fetch_all(self.evadb, 'SELECT * FROM test_data_source.test_table')
        self.assertEqual(len(res_batch), 2)
        self.assertEqual(res_batch.frames['test_table.name'][0], 'aa')
        self.assertEqual(res_batch.frames['test_table.age'][0], 1)
        self.assertEqual(res_batch.frames['test_table.name'][1], 'bb')
        self.assertEqual(res_batch.frames['test_table.age'][1], 2)
        self._create_evadb_table_using_select_query()
        self._create_native_table_using_select_query()
        self._drop_table_in_native_database()
        self._drop_table_in_evadb_database()

    def _execute_native_query(self):
        self._create_table_in_native_database()
        self._insert_value_into_native_database('aa', 1, 'aaaa')
        res_batch = execute_query_fetch_all(self.evadb, 'USE test_data_source {\n                SELECT * FROM test_table\n            }')
        self.assertEqual(len(res_batch), 1)
        self.assertEqual(res_batch.frames['name'][0], 'aa')
        self.assertEqual(res_batch.frames['age'][0], 1)
        self.assertEqual(res_batch.frames['comment'][0], 'aaaa')
        self._drop_table_in_native_database()

    def _raise_error_on_multiple_creation(self):
        params = {'user': 'eva', 'password': 'password', 'host': 'localhost', 'port': '5432', 'database': 'evadb'}
        query = f'CREATE DATABASE test_data_source\n                    WITH ENGINE = "postgres",\n                    PARAMETERS = {params};'
        with self.assertRaises(ExecutorError):
            execute_query_fetch_all(self.evadb, query)

    def _raise_error_on_invalid_connection(self):
        params = {'user': 'xxxxxx', 'password': 'xxxxxx', 'host': 'localhost', 'port': '5432', 'database': 'evadb'}
        query = f'CREATE DATABASE invaid\n                    WITH ENGINE = "postgres",\n                    PARAMETERS = {params};'
        with self.assertRaises(ExecutorError):
            execute_query_fetch_all(self.evadb, query)

    def test_should_run_query_in_postgres(self):
        params = {'user': 'eva', 'password': 'password', 'host': 'localhost', 'port': '5432', 'database': 'evadb'}
        query = f'CREATE DATABASE test_data_source\n                    WITH ENGINE = "postgres",\n                    PARAMETERS = {params};'
        execute_query_fetch_all(self.evadb, query)
        self._execute_native_query()
        self._execute_evadb_query()
        self._raise_error_on_multiple_creation()
        self._raise_error_on_invalid_connection()

    def test_should_run_query_in_mariadb(self):
        params = {'user': 'eva', 'password': 'password', 'database': 'evadb'}
        query = f'CREATE DATABASE test_data_source\n                    WITH ENGINE = "mariadb",\n                    PARAMETERS = {params};'
        execute_query_fetch_all(self.evadb, query)
        self._execute_native_query()
        self._execute_evadb_query()

    def test_should_run_query_in_clickhouse(self):
        params = {'user': 'eva', 'password': 'password', 'host': 'localhost', 'port': '9000', 'database': 'evadb'}
        query = f'CREATE DATABASE test_data_source\n                    WITH ENGINE = "clickhouse",\n                    PARAMETERS = {params};'
        execute_query_fetch_all(self.evadb, query)
        self._execute_native_query()
        self._execute_evadb_query()

    @pytest.mark.skip(reason='Snowflake does not come with a free version of account, so integration test is not feasible')
    def test_should_run_query_in_snowflake(self):
        params = {'user': 'eva', 'password': 'password', 'account': 'account_number', 'database': 'EVADB', 'schema': 'SAMPLE_DATA', 'warehouse': 'warehouse'}
        query = f'CREATE DATABASE test_data_source\n                    WITH ENGINE = "snowflake",\n                    PARAMETERS = {params};'
        execute_query_fetch_all(self.evadb, query)
        self._execute_native_query()
        self._execute_evadb_query()

    def test_should_run_query_in_sqlite(self):
        import os
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        params = {'database': f'{current_file_dir}/evadb.db'}
        query = f'CREATE DATABASE test_data_source\n                    WITH ENGINE = "sqlite",\n                    PARAMETERS = {params};'
        execute_query_fetch_all(self.evadb, query)
        self._execute_native_query()
        self._execute_evadb_query()

    def test_should_run_query_in_mysql(self):
        params = {'user': 'eva', 'password': 'password', 'host': 'localhost', 'port': '3306', 'database': 'evadb'}
        query = f'CREATE DATABASE test_data_source\n                    WITH ENGINE = "mysql",\n                    PARAMETERS = {params};'
        execute_query_fetch_all(self.evadb, query)
        self._execute_native_query()
        self._execute_evadb_query()

def tearDown(self):
    shutdown_ray()
    self._drop_table_in_native_database()
    self._drop_table_in_evadb_database()

def _execute_evadb_query(self):
    self._create_table_in_native_database()
    self._insert_value_into_native_database('aa', 1, 'aaaa')
    self._insert_value_into_native_database('bb', 2, 'bbbb')
    res_batch = execute_query_fetch_all(self.evadb, 'SELECT * FROM test_data_source.test_table')
    self.assertEqual(len(res_batch), 2)
    self.assertEqual(res_batch.frames['test_table.name'][0], 'aa')
    self.assertEqual(res_batch.frames['test_table.age'][0], 1)
    self.assertEqual(res_batch.frames['test_table.name'][1], 'bb')
    self.assertEqual(res_batch.frames['test_table.age'][1], 2)
    self._create_evadb_table_using_select_query()
    self._create_native_table_using_select_query()
    self._drop_table_in_native_database()
    self._drop_table_in_evadb_database()

def _execute_native_query(self):
    self._create_table_in_native_database()
    self._insert_value_into_native_database('aa', 1, 'aaaa')
    res_batch = execute_query_fetch_all(self.evadb, 'USE test_data_source {\n                SELECT * FROM test_table\n            }')
    self.assertEqual(len(res_batch), 1)
    self.assertEqual(res_batch.frames['name'][0], 'aa')
    self.assertEqual(res_batch.frames['age'][0], 1)
    self.assertEqual(res_batch.frames['comment'][0], 'aaaa')
    self._drop_table_in_native_database()

class EvaDBQuery:

    def __init__(self, evadb: EvaDBDatabase, query_node: Union[AbstractStatement, TableRef], alias: Alias=None):
        self._evadb = evadb
        self._query_node = query_node
        self._alias = alias

    def alias(self, alias: str) -> 'EvaDBQuery':
        """Returns a new Relation with an alias set.

        Args:
            alias (str): an alias name to be set for the Relation.

        Returns:
            EvaDBQuery: Aliased Relation.

        Examples:
            >>> relation = cursor.table("sample_table")
            >>> relation.alias('table')
        """
        self._alias = Alias(alias)

    def cross_apply(self, expr: str, alias: str) -> 'EvaDBQuery':
        """Execute a expr on all the rows of the relation

        Args:
            expr (str): sql expression
            alias (str): alias of the output of the expr

        Returns:
            `EvaDBQuery`: relation

        Examples:

            Runs Yolo on all the frames of the input table

            >>> relation = cursor.table("videos")
            >>> relation.cross_apply("Yolo(data)", "objs(labels, bboxes, scores)")

            Runs Yolo on all the frames of the input table and unnest each object as separate row.

            >>> relation.cross_apply("unnest(Yolo(data))", "obj(label, bbox, score)")
        """
        assert self._query_node.from_table is not None
        table_ref = string_to_lateral_join(expr, alias=alias)
        join_table = TableRef(JoinNode(TableRef(self._query_node, alias=self._alias), table_ref, join_type=JoinType.LATERAL_JOIN))
        self._query_node = SelectStatement(target_list=create_star_expression(), from_table=join_table)
        self._alias = Alias('Relation')
        try_binding(self._evadb.catalog, self._query_node)
        return self

    def df(self, drop_alias: bool=True) -> pandas.DataFrame:
        """
        Execute and fetch all rows as a pandas DataFrame

        Args:
            drop_alias (bool): whether to drop the table name in the output dataframe. Default: True.

        Returns:
            pandas.DataFrame:

        Example:

        Runs a SQL query and get a panda Dataframe.
            >>> cursor.query("SELECT * FROM MyTable;").df()
                col1  col2
            0      1     2
            1      3     4
            2      5     6
        """
        batch = self.execute(drop_alias=drop_alias)
        assert batch.frames is not None, 'relation execute failed'
        return batch.frames

    def execute(self, drop_alias: bool=True) -> Batch:
        """Transform the relation into a result set

        Args:
            drop_alias (bool): whether to drop the table name in the output batch. Default: True.

        Returns:
            Batch: result as evadb Batch

        Example:

            Runs a SQL query and get a Batch
            >>> batch = cursor.query("SELECT * FROM MyTable;").execute()
        """
        result = execute_statement(self._evadb, self._query_node.copy())
        if drop_alias:
            result.drop_column_alias()
        assert result is not None
        return result

    def filter(self, expr: str) -> 'EvaDBQuery':
        """
        Filters rows using the given condition. Multiple filters can be chained using `AND`

        Parameters:
            expr (str): The filter expression.

        Returns:
            EvaDBQuery : Filtered EvaDBQuery.
        Examples:
            >>> relation = cursor.table("sample_table")
            >>> relation.filter("col1 > 10")

            Filter by sql string

            >>> relation.filter("col1 > 10 AND col1 < 20")

        """
        parsed_expr = sql_predicate_to_expresssion_tree(expr)
        self._query_node = handle_select_clause(self._query_node, self._alias, 'where_clause', parsed_expr)
        try_binding(self._evadb.catalog, self._query_node)
        return self

    def limit(self, num: int) -> 'EvaDBQuery':
        """Limits the result count to the number specified.

        Args:
            num (int): Number of records to return. Will return num records or all records if the Relation contains fewer records.

        Returns:
            EvaDBQuery: Relation with subset of records

        Examples:
            >>> relation = cursor.table("sample_table")
            >>> relation.limit(10)

        """
        limit_expr = create_limit_expression(num)
        self._query_node = handle_select_clause(self._query_node, self._alias, 'limit_count', limit_expr)
        try_binding(self._evadb.catalog, self._query_node)
        return self

    def order(self, order_expr: str) -> 'EvaDBQuery':
        """Reorder the relation based on the order_expr

        Args:
            order_expr (str): sql expression to order the relation

        Returns:
            EvaDBQuery: A EvaDBQuery ordered based on the order_expr.

        Examples:
            >>> relation = cursor.table("PDFs")
            >>> relation.order("Similarity(SentenceTransformerFeatureExtractor('When was the NATO created?'), SentenceTransformerFeatureExtractor(data) ) DESC")

        """
        parsed_expr = parse_sql_orderby_expr(order_expr)
        self._query_node = handle_select_clause(self._query_node, self._alias, 'orderby_list', parsed_expr)
        try_binding(self._evadb.catalog, self._query_node)
        return self

    def select(self, expr: str) -> 'EvaDBQuery':
        """
        Projects a set of expressions and returns a new EvaDBQuery.

        Parameters:
            exprs (Union[str, List[str]]): The expression(s) to be selected. If '*' is provided, it expands to all columns in the current EvaDBQuery.

        Returns:
            EvaDBQuery: A EvaDBQuery with subset (or all) of columns.

        Examples:
            >>> relation = cursor.table("sample_table")

            Select all columns in the EvaDBQuery.

            >>> relation.select("*")

            Select all subset of columns in the EvaDBQuery.

            >>> relation.select("col1")
            >>> relation.select("col1, col2")
        """
        parsed_exprs = sql_string_to_expresssion_list(expr)
        self._query_node = handle_select_clause(self._query_node, self._alias, 'target_list', parsed_exprs)
        try_binding(self._evadb.catalog, self._query_node)
        return self

    def show(self) -> pandas.DataFrame:
        """Execute and fetch all rows as a pandas DataFrame

        Returns:
            pandas.DataFrame:
        """
        batch = self.execute()
        assert batch is not None, 'relation execute failed'
        return batch.frames

    def sql_query(self) -> str:
        """Get the SQL query that is equivalent to the relation

        Returns:
            str: the sql query

        Examples:
            >>> relation = cursor.table("sample_table").project('i')
            >>> relation.sql_query()
        """
        return str(self._query_node)

def filter(self, expr: str) -> 'EvaDBQuery':
    """
        Filters rows using the given condition. Multiple filters can be chained using `AND`

        Parameters:
            expr (str): The filter expression.

        Returns:
            EvaDBQuery : Filtered EvaDBQuery.
        Examples:
            >>> relation = cursor.table("sample_table")
            >>> relation.filter("col1 > 10")

            Filter by sql string

            >>> relation.filter("col1 > 10 AND col1 < 20")

        """
    parsed_expr = sql_predicate_to_expresssion_tree(expr)
    self._query_node = handle_select_clause(self._query_node, self._alias, 'where_clause', parsed_expr)
    try_binding(self._evadb.catalog, self._query_node)
    return self

def limit(self, num: int) -> 'EvaDBQuery':
    """Limits the result count to the number specified.

        Args:
            num (int): Number of records to return. Will return num records or all records if the Relation contains fewer records.

        Returns:
            EvaDBQuery: Relation with subset of records

        Examples:
            >>> relation = cursor.table("sample_table")
            >>> relation.limit(10)

        """
    limit_expr = create_limit_expression(num)
    self._query_node = handle_select_clause(self._query_node, self._alias, 'limit_count', limit_expr)
    try_binding(self._evadb.catalog, self._query_node)
    return self

def order(self, order_expr: str) -> 'EvaDBQuery':
    """Reorder the relation based on the order_expr

        Args:
            order_expr (str): sql expression to order the relation

        Returns:
            EvaDBQuery: A EvaDBQuery ordered based on the order_expr.

        Examples:
            >>> relation = cursor.table("PDFs")
            >>> relation.order("Similarity(SentenceTransformerFeatureExtractor('When was the NATO created?'), SentenceTransformerFeatureExtractor(data) ) DESC")

        """
    parsed_expr = parse_sql_orderby_expr(order_expr)
    self._query_node = handle_select_clause(self._query_node, self._alias, 'orderby_list', parsed_expr)
    try_binding(self._evadb.catalog, self._query_node)
    return self

def select(self, expr: str) -> 'EvaDBQuery':
    """
        Projects a set of expressions and returns a new EvaDBQuery.

        Parameters:
            exprs (Union[str, List[str]]): The expression(s) to be selected. If '*' is provided, it expands to all columns in the current EvaDBQuery.

        Returns:
            EvaDBQuery: A EvaDBQuery with subset (or all) of columns.

        Examples:
            >>> relation = cursor.table("sample_table")

            Select all columns in the EvaDBQuery.

            >>> relation.select("*")

            Select all subset of columns in the EvaDBQuery.

            >>> relation.select("col1")
            >>> relation.select("col1, col2")
        """
    parsed_exprs = sql_string_to_expresssion_list(expr)
    self._query_node = handle_select_clause(self._query_node, self._alias, 'target_list', parsed_exprs)
    try_binding(self._evadb.catalog, self._query_node)
    return self

