# Cluster 54

def bind_table_info(catalog: CatalogManager, table_info: TableInfo):
    """
    Uses catalog to bind the table information .

    Arguments:
         catalog (CatalogManager): catalog manager to use
         table_info (TableInfo): table information obtained from SQL query

    Returns:
        TableCatalogEntry  -  corresponding table catalog entry for the input table info
    """
    if table_info.database_name is not None:
        bind_native_table_info(catalog, table_info)
    else:
        bind_evadb_table_info(catalog, table_info)

