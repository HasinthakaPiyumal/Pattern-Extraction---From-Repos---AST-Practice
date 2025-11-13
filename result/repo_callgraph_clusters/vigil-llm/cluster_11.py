# Cluster 11

class Registration:

    @staticmethod
    def scanner(name: str, requires_config=False, requires_vectordb=False, **additional_metadata):

        def decorator(scanner_class: Type[BaseScanner]):
            ScannerRegistry.register_scanner(name, scanner_class, requires_config, requires_vectordb, **additional_metadata)
            return scanner_class
        return decorator

def decorator(scanner_class: Type[BaseScanner]):
    ScannerRegistry.register_scanner(name, scanner_class, requires_config, requires_vectordb, **additional_metadata)
    return scanner_class

