# Cluster 44

class VectorIndexScanExecutor(AbstractExecutor):

    def __init__(self, db: EvaDBDatabase, node: VectorIndexScanPlan):
        super().__init__(db, node)
        self.index_name = node.index.name
        self.vector_store_type = node.index.type
        self.feat_column = node.index.feat_column
        self.limit_count = node.limit_count
        self.search_query_expr = node.search_query_expr

    def exec(self, *args, **kwargs) -> Iterator[Batch]:
        if self.vector_store_type == VectorStoreType.PGVECTOR:
            return self._native_vector_index_scan()
        else:
            return self._evadb_vector_index_scan(*args, **kwargs)

    def _get_search_query_results(self):
        dummy_batch = Batch(frames=pd.DataFrame({'0': [0]}))
        search_batch = self.search_query_expr.evaluate(dummy_batch)
        feature_col_name = self.search_query_expr.output_objs[0].name
        search_batch.drop_column_alias()
        search_feat = search_batch.column_as_numpy_array(feature_col_name)[0]
        search_feat = search_feat.reshape(1, -1)
        return search_feat

    def _native_vector_index_scan(self):
        search_feat = self._get_search_query_results()
        search_feat = search_feat.reshape(-1).tolist()
        tb_catalog_entry = list(self.node.find_all(StoragePlan))[0].table
        db_catalog_entry = self.db.catalog().get_database_catalog_entry(tb_catalog_entry.database_name)
        with get_database_handler(db_catalog_entry.engine, **db_catalog_entry.params) as handler:
            resp = handler.execute_native_query(f"SELECT * FROM {tb_catalog_entry.name}\n                                                ORDER BY {self.feat_column.name} <-> '{search_feat}'\n                                                LIMIT {self.limit_count}")
            if resp.error is not None:
                raise ExecutorError(f'Native index can encounters {resp.error}')
            res = Batch(frames=resp.data)
            res.modify_column_alias(tb_catalog_entry.name)
            yield res

    def _evadb_vector_index_scan(self, *args, **kwargs):
        index_catalog_entry = self.catalog().get_index_catalog_entry_by_name(self.index_name)
        self.index_path = index_catalog_entry.save_file_path
        self.index = VectorStoreFactory.init_vector_store(self.vector_store_type, self.index_name, **handle_vector_store_params(self.vector_store_type, self.index_path, self.db.catalog))
        search_feat = self._get_search_query_results()
        index_result = self.index.query(VectorIndexQuery(search_feat, self.limit_count.value))
        row_num_np = index_result.ids
        row_num_col_name = None
        num_required_results = self.limit_count.value
        if len(index_result.ids) < self.limit_count.value:
            num_required_results = len(index_result.ids)
            logger.warning(f'The index {self.index_name} returned only {num_required_results} results, which is fewer than the required {self.limit_count.value}.')
        final_df = pd.DataFrame()
        res_data_list = []
        row_num_df = pd.DataFrame({'row_num_np': row_num_np})
        for batch in self.children[0].exec(**kwargs):
            if not row_num_col_name:
                column_list = batch.columns
                row_num_alias = get_row_num_column_alias(column_list)
                row_num_col_name = '{}.{}'.format(row_num_alias, ROW_NUM_COLUMN)
            if not batch.frames[row_num_col_name].isin(row_num_df['row_num_np']).any():
                continue
            for index, row in batch.frames.iterrows():
                row_dict = row.to_dict()
                res_data_list.append(row_dict)
        result_df = pd.DataFrame(res_data_list)
        final_df = pd.merge(row_num_df, result_df, left_on='row_num_np', right_on=row_num_col_name, how='inner')
        if 'row_num_np' in final_df:
            del final_df['row_num_np']
        yield Batch(final_df)

def exec(self, *args, **kwargs) -> Iterator[Batch]:
    if self.vector_store_type == VectorStoreType.PGVECTOR:
        return self._native_vector_index_scan()
    else:
        return self._evadb_vector_index_scan(*args, **kwargs)

