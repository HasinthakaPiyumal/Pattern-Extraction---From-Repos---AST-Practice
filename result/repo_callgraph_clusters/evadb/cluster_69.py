# Cluster 69

class SchemaUtils(object):

    @staticmethod
    def xform_to_sqlalchemy_column(df_column: ColumnCatalogEntry) -> Column:
        column_type = df_column.type
        sqlalchemy_column = None
        if column_type == ColumnType.INTEGER:
            sqlalchemy_column = Column(Integer)
        elif column_type == ColumnType.FLOAT:
            sqlalchemy_column = Column(Float)
        elif column_type == ColumnType.TEXT:
            sqlalchemy_column = Column(TEXT)
        elif column_type == ColumnType.NDARRAY:
            sqlalchemy_column = Column(LargeBinary)
        else:
            msg = 'Invalid column type: ' + str(column_type)
            logger.error(msg)
            raise NotImplementedError
        return sqlalchemy_column

    @staticmethod
    def xform_to_sqlalchemy_schema(column_list: List[ColumnCatalogEntry]) -> Dict[str, Column]:
        """Converts the list of DataFrameColumns to SQLAlchemyColumns

        Args:
            column_list (List[ColumnCatalog]): columns to be converted

        Returns:
            Dict[str, Column]: mapping from column_name to sqlalchemy column object
        """
        return {column.name: SchemaUtils.xform_to_sqlalchemy_column(column) for column in column_list}

@staticmethod
def xform_to_sqlalchemy_schema(column_list: List[ColumnCatalogEntry]) -> Dict[str, Column]:
    """Converts the list of DataFrameColumns to SQLAlchemyColumns

        Args:
            column_list (List[ColumnCatalog]): columns to be converted

        Returns:
            Dict[str, Column]: mapping from column_name to sqlalchemy column object
        """
    return {column.name: SchemaUtils.xform_to_sqlalchemy_column(column) for column in column_list}

