# Cluster 35

class ColumnTransformInfo:

    def __init__(self, column_name: str, column_type: ColumnTransformType | str, transform: TransformerEncoderInstanceType, output_info: List[SpanInfo], output_dimensions: int):
        self.column_name: str = column_name
        self.column_type: ColumnTransformType = ColumnTransformType(column_type)
        self.transform: TransformerEncoderInstanceType = transform
        self.output_info: List[SpanInfo] = output_info
        self.output_dimensions: int = output_dimensions

def __init__(self, column_name: str, column_type: ColumnTransformType | str, transform: TransformerEncoderInstanceType, output_info: List[SpanInfo], output_dimensions: int):
    self.column_name: str = column_name
    self.column_type: ColumnTransformType = ColumnTransformType(column_type)
    self.transform: TransformerEncoderInstanceType = transform
    self.output_info: List[SpanInfo] = output_info
    self.output_dimensions: int = output_dimensions

