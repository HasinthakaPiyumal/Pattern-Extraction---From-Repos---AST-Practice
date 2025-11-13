# Cluster 48

def build_sam_vit_h(checkpoint=None):
    return _build_sam(encoder_embed_dim=1280, encoder_depth=32, encoder_num_heads=16, encoder_global_attn_indexes=[7, 15, 23, 31], checkpoint=checkpoint)

def build_sam_vit_l(checkpoint=None):
    return _build_sam(encoder_embed_dim=1024, encoder_depth=24, encoder_num_heads=16, encoder_global_attn_indexes=[5, 11, 17, 23], checkpoint=checkpoint)

def build_sam_vit_b(checkpoint=None):
    return _build_sam(encoder_embed_dim=768, encoder_depth=12, encoder_num_heads=12, encoder_global_attn_indexes=[2, 5, 8, 11], checkpoint=checkpoint)

