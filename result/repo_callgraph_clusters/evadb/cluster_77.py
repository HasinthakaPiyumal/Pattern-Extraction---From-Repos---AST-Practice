# Cluster 77

class CreateTable:

    def create_table(self, tree):
        table_info = None
        if_not_exists = False
        create_definitions = []
        query = None
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data == 'if_not_exists':
                    if_not_exists = True
                elif child.data == 'table_name':
                    table_info = self.visit(child)
                elif child.data == 'create_definitions':
                    create_definitions = self.visit(child)
                elif child.data == 'simple_select':
                    query = self.visit(child)
        create_stmt = CreateTableStatement(table_info, if_not_exists, create_definitions, query=query)
        return create_stmt

    def create_definitions(self, tree):
        column_definitions = []
        for child in tree.children:
            if isinstance(child, Tree):
                create_definition = None
                if child.data == 'column_declaration':
                    create_definition = self.visit(child)
                column_definitions.append(create_definition)
        return column_definitions

    def column_declaration(self, tree):
        column_name = None
        data_type = None
        array_type = None
        dimensions = None
        column_constraint_information = None
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data == 'uid':
                    column_name = self.visit(child)
                elif child.data == 'column_definition':
                    data_type, array_type, dimensions, column_constraint_information = self.visit(child)
        if column_name is not None:
            return ColumnDefinition(column_name, data_type, array_type, dimensions, column_constraint_information)

    def column_definition(self, tree):
        data_type = None
        array_type = None
        dimensions = None
        column_constraint_information = ColConstraintInfo()
        not_null_set = False
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data.endswith('data_type'):
                    data_type, array_type, dimensions = self.visit(child)
                elif child.data.endswith('column_constraint'):
                    return_type = self.visit(child)
                    if return_type == ColumnConstraintEnum.UNIQUE:
                        column_constraint_information.unique = True
                        column_constraint_information.nullable = False
                        not_null_set = True
                    elif return_type == ColumnConstraintEnum.NOTNULL:
                        column_constraint_information.nullable = False
                        not_null_set = True
        if not not_null_set:
            column_constraint_information.nullable = True
        return (data_type, array_type, dimensions, column_constraint_information)

    def unique_key_column_constraint(self, tree):
        return ColumnConstraintEnum.UNIQUE

    def null_column_constraint(self, tree):
        return ColumnConstraintEnum.NOTNULL

    def simple_data_type(self, tree):
        data_type = None
        array_type = None
        dimensions = []
        token = tree.children[0]
        if str.upper(token) == 'BOOLEAN':
            data_type = ColumnType.BOOLEAN
        return (data_type, array_type, dimensions)

    def integer_data_type(self, tree):
        data_type = None
        array_type = None
        dimensions = []
        token = tree.children[0]
        if str.upper(token) == 'INTEGER':
            data_type = ColumnType.INTEGER
        return (data_type, array_type, dimensions)

    def dimension_data_type(self, tree):
        data_type = None
        array_type = None
        dimensions = []
        token = tree.children[0]
        if str.upper(token) == 'FLOAT':
            data_type = ColumnType.FLOAT
        elif str.upper(token) == 'TEXT':
            data_type = ColumnType.TEXT
        if len(tree.children) > 1:
            dimensions = self.visit(tree.children[1])
        return (data_type, array_type, dimensions)

    def array_data_type(self, tree):
        data_type = ColumnType.NDARRAY
        array_type = NdArrayType.ANYTYPE
        dimensions = None
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data == 'array_type':
                    array_type = self.visit(child)
                elif child.data == 'length_dimension_list':
                    dimensions = self.visit(child)
        return (data_type, array_type, dimensions)

    def any_data_type(self, tree):
        return (ColumnType.ANY, None, [])

    def array_type(self, tree):
        array_type = None
        token = tree.children[0]
        if str.upper(token) == 'INT8':
            array_type = NdArrayType.INT8
        elif str.upper(token) == 'UINT8':
            array_type = NdArrayType.UINT8
        elif str.upper(token) == 'INT16':
            array_type = NdArrayType.INT16
        elif str.upper(token) == 'INT32':
            array_type = NdArrayType.INT32
        elif str.upper(token) == 'INT64':
            array_type = NdArrayType.INT64
        elif str.upper(token) == 'UNICODE':
            array_type = NdArrayType.UNICODE
        elif str.upper(token) == 'BOOLEAN':
            array_type = NdArrayType.BOOL
        elif str.upper(token) == 'FLOAT32':
            array_type = NdArrayType.FLOAT32
        elif str.upper(token) == 'FLOAT64':
            array_type = NdArrayType.FLOAT64
        elif str.upper(token) == 'DECIMAL':
            array_type = NdArrayType.DECIMAL
        elif str.upper(token) == 'STR':
            array_type = NdArrayType.STR
        elif str.upper(token) == 'DATETIME':
            array_type = NdArrayType.DATETIME
        elif str.upper(token) == 'ANYTYPE':
            array_type = NdArrayType.ANYTYPE
        return array_type

    def dimension_helper(self, tree):
        dimensions = []
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data == 'decimal_literal':
                    decimal = self.visit(child)
                    dimensions.append(decimal)
        return tuple(dimensions)

    def length_one_dimension(self, tree):
        dimensions = self.dimension_helper(tree)
        return dimensions

    def length_two_dimension(self, tree):
        dimensions = self.dimension_helper(tree)
        return dimensions

    def length_dimension_list(self, tree):
        dimensions = self.dimension_helper(tree)
        return dimensions

def length_one_dimension(self, tree):
    dimensions = self.dimension_helper(tree)
    return dimensions

def length_two_dimension(self, tree):
    dimensions = self.dimension_helper(tree)
    return dimensions

def length_dimension_list(self, tree):
    dimensions = self.dimension_helper(tree)
    return dimensions

