# Cluster 100

class HybridConditioner(nn.Module):

    def __init__(self, c_concat_config, c_crossattn_config):
        super().__init__()
        self.concat_conditioner = instantiate_from_config(c_concat_config)
        self.crossattn_conditioner = instantiate_from_config(c_crossattn_config)

    def forward(self, c_concat, c_crossattn):
        c_concat = self.concat_conditioner(c_concat)
        c_crossattn = self.crossattn_conditioner(c_crossattn)
        return {'c_concat': [c_concat], 'c_crossattn': [c_crossattn]}

def forward(self, c_concat, c_crossattn):
    c_concat = self.concat_conditioner(c_concat)
    c_crossattn = self.crossattn_conditioner(c_crossattn)
    return {'c_concat': [c_concat], 'c_crossattn': [c_crossattn]}

