# Cluster 36

@dataclass
class EvaDBDatabase:
    db_uri: str
    catalog_uri: str
    catalog_func: Callable

    def catalog(self) -> 'CatalogManager':
        """
        Note: Generating an object on demand plays a crucial role in ensuring that different threads do not share the same catalog object, as it can result in serialization issues and incorrect behavior with SQLAlchemy. Refer to get_catalog_instance()
        """
        return self.catalog_func(self.catalog_uri)

def catalog(self) -> 'CatalogManager':
    """
        Note: Generating an object on demand plays a crucial role in ensuring that different threads do not share the same catalog object, as it can result in serialization issues and incorrect behavior with SQLAlchemy. Refer to get_catalog_instance()
        """
    return self.catalog_func(self.catalog_uri)

