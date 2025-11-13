# Cluster 20

def validate_patches(patches: List[Dict[str, Any]]) -> List[PatchOperation]:
    validated = ConfigPatchSet(patches=patches)
    return validated.patches

