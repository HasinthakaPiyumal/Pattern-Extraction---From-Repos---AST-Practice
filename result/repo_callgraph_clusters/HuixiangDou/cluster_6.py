# Cluster 6

def setup(app):
    app.connect('builder-inited', builder_inited_handler)

def setup(app):
    app.connect('builder-inited', builder_inited_handler)

def init_milvus(col_name: str, max_length_bytes: int):
    conn = connections.connect('default', host='localhost', port='19530')
    fields = [FieldSchema(name='pk', dtype=DataType.VARCHAR, is_primary=True, auto_id=True, max_length=100), FieldSchema(name='text', dtype=DataType.VARCHAR, max_length=max_length_bytes), FieldSchema(name='sparse_vector', dtype=DataType.SPARSE_FLOAT_VECTOR), FieldSchema(name='dense_vector', dtype=DataType.FLOAT_VECTOR, dim=dense_dim)]
    schema = CollectionSchema(fields, '')
    col = Collection(col_name, schema, consistency_level='Strong')
    sparse_index = {'index_type': 'SPARSE_INVERTED_INDEX', 'metric_type': 'IP'}
    col.create_index('sparse_vector', sparse_index)
    dense_index = {'index_type': 'FLAT', 'metric_type': 'IP'}
    col.create_index('dense_vector', dense_index)
    col.load()
    return col

