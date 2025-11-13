# Cluster 48

def is_postgres_uri(db_uri):
    """
    Determines if the db_uri is that of postgres.

    Args:
        db_uri (str) : db_uri to parse
    """
    parsed_uri = urlparse(db_uri)
    return parsed_uri.scheme == 'postgres' or parsed_uri.scheme == 'postgresql'

