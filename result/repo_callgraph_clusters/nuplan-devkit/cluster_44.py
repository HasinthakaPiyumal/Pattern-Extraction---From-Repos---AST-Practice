# Cluster 44

class UUID(TypeDecorator):
    """
    Use BLOB(16) for sqlite.(bigint for mysql and uuid for postgresql)
    """
    impl = BLOB
    cache_ok = True

    def load_dialect_impl(self, dialect: Dialect) -> TypeEngine:
        """Inherited, see superclass."""
        return dialect.type_descriptor(BLOB(16))

    def process_bind_param(self, value: Optional[str], dialect: Dialect) -> Optional[bytes]:
        """Inherited, see superclass."""
        if not value:
            return None
        return uuid.UUID(value).bytes

    def process_result_value(self, value: Optional[bytes], dialect: Dialect) -> Optional[str]:
        """Inherited, see superclass."""
        if not value:
            return None
        return value.hex()

def process_bind_param(self, value: Optional[str], dialect: Dialect) -> Optional[bytes]:
    """Inherited, see superclass."""
    if not value:
        return None
    return uuid.UUID(value).bytes

