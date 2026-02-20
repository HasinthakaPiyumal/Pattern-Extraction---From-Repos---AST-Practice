# Cluster 16

def validate_uuid(uuid_string: str) -> bool:
    """Validate if string is a valid UUID."""
    try:
        uuid.UUID(uuid_string)
        return True
    except ValueError:
        return False

# Node: UUID
