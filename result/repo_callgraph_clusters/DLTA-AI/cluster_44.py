# Cluster 44

def build_backbone(cfg):
    """Build backbone."""
    return BACKBONES.build(cfg)

def build_neck(cfg):
    """Build neck."""
    return NECKS.build(cfg)

def build_roi_extractor(cfg):
    """Build roi extractor."""
    return ROI_EXTRACTORS.build(cfg)

def build_shared_head(cfg):
    """Build shared head."""
    return SHARED_HEADS.build(cfg)

def build_head(cfg):
    """Build head."""
    return HEADS.build(cfg)

def build_loss(cfg):
    """Build loss."""
    return LOSSES.build(cfg)

