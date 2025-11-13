# Cluster 71

@dataclass(unsafe_hash=True)
class FunctionCatalogEntry:
    """Dataclass representing an entry in the `FunctionCatalog`.
    This is done to ensure we don't expose the sqlalchemy dependencies beyond catalog service. Further, sqlalchemy does not allow sharing of objects across threads.
    """
    name: str
    impl_file_path: str
    type: str
    checksum: str
    row_id: int = None
    args: List[FunctionIOCatalogEntry] = field(compare=False, default_factory=list)
    outputs: List[FunctionIOCatalogEntry] = field(compare=False, default_factory=list)
    metadata: List[FunctionMetadataCatalogEntry] = field(compare=False, default_factory=list)
    dep_caches: List[FunctionIOCatalogEntry] = field(compare=False, default_factory=list)

    def display_format(self):

        def _to_str(col):
            col_display = col.display_format()
            return f'{col_display['name']} {col_display['data_type']}'
        return {'name': self.name, 'inputs': [_to_str(col) for col in self.args], 'outputs': [_to_str(col) for col in self.outputs], 'type': self.type, 'impl': self.impl_file_path, 'metadata': self.metadata}

def display_format(self):

    def _to_str(col):
        col_display = col.display_format()
        return f'{col_display['name']} {col_display['data_type']}'
    return {'name': self.name, 'inputs': [_to_str(col) for col in self.args], 'outputs': [_to_str(col) for col in self.outputs], 'type': self.type, 'impl': self.impl_file_path, 'metadata': self.metadata}

