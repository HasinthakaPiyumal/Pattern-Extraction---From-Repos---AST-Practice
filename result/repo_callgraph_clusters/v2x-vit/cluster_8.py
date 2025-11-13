# Cluster 8

class V2XFusionBlock(nn.Module):

    def __init__(self, num_blocks, cav_att_config, pwindow_config):
        super().__init__()
        self.layers = nn.ModuleList([])
        self.num_blocks = num_blocks
        for _ in range(num_blocks):
            att = HGTCavAttention(cav_att_config['dim'], heads=cav_att_config['heads'], dim_head=cav_att_config['dim_head'], dropout=cav_att_config['dropout']) if cav_att_config['use_hetero'] else CavAttention(cav_att_config['dim'], heads=cav_att_config['heads'], dim_head=cav_att_config['dim_head'], dropout=cav_att_config['dropout'])
            self.layers.append(nn.ModuleList([PreNorm(cav_att_config['dim'], att), PreNorm(cav_att_config['dim'], PyramidWindowAttention(pwindow_config['dim'], heads=pwindow_config['heads'], dim_heads=pwindow_config['dim_head'], drop_out=pwindow_config['dropout'], window_size=pwindow_config['window_size'], relative_pos_embedding=pwindow_config['relative_pos_embedding'], fuse_method=pwindow_config['fusion_method']))]))

    def forward(self, x, mask, prior_encoding):
        for cav_attn, pwindow_attn in self.layers:
            x = cav_attn(x, mask=mask, prior_encoding=prior_encoding) + x
            x = pwindow_attn(x) + x
        return x

def forward(self, x, mask, prior_encoding):
    for cav_attn, pwindow_attn in self.layers:
        x = cav_attn(x, mask=mask, prior_encoding=prior_encoding) + x
        x = pwindow_attn(x) + x
    return x

