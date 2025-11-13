# Cluster 74

def parse_drop_table(table_name: str, if_exists: bool):
    return parse_drop(ObjectType.TABLE, table_name, if_exists)

def parse_drop_function(function_name: str, if_exists: bool):
    return parse_drop(ObjectType.FUNCTION, function_name, if_exists)

def parse_drop_index(index_name: str, if_exists: bool):
    return parse_drop(ObjectType.INDEX, index_name, if_exists)

def parse_drop_database(database_name: str, if_exists: bool):
    return parse_drop(ObjectType.DATABASE, database_name, if_exists)

