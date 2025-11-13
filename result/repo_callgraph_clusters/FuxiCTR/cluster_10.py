# Cluster 10

class TransActTransformer(nn.Module):

    def __init__(self, transformer_in_dim, dim_feedforward=64, num_heads=1, dropout=0, transformer_layers=1, use_time_window_mask=False, time_window_ms=86400000, first_k_cols=1, concat_max_pool=True):
        super(TransActTransformer, self).__init__()
        self.use_time_window_mask = use_time_window_mask
        self.time_window_ms = time_window_ms
        self.concat_max_pool = concat_max_pool
        self.first_k_cols = first_k_cols
        encoder_layer = nn.TransformerEncoderLayer(d_model=transformer_in_dim, nhead=num_heads, dim_feedforward=dim_feedforward, dropout=dropout, batch_first=True)
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=transformer_layers)
        if self.concat_max_pool:
            self.out_linear = nn.Linear(transformer_in_dim, transformer_in_dim)

    def forward(self, target_emb, sequence_emb, time_interval_seq=None, mask=None):
        seq_len = sequence_emb.size(1)
        concat_seq_emb = torch.cat([sequence_emb, target_emb.unsqueeze(1).expand(-1, seq_len, -1)], dim=-1)
        key_padding_mask = self.adjust_mask(mask)
        if self.use_time_window_mask and self.training:
            rand_time_window_ms = random.randint(0, self.time_window_ms)
            time_window_mask = time_interval_seq < rand_time_window_ms
            key_padding_mask = torch.bitwise_or(key_padding_mask, time_window_mask)
        tfmr_out = self.transformer_encoder(src=concat_seq_emb, src_key_padding_mask=key_padding_mask)
        tfmr_out = tfmr_out.masked_fill(key_padding_mask.unsqueeze(-1).repeat(1, 1, tfmr_out.shape[-1]), 0.0)
        output_concat = []
        output_concat.append(tfmr_out[:, -self.first_k_cols:].flatten(start_dim=1))
        if self.concat_max_pool:
            tfmr_out = tfmr_out.masked_fill(key_padding_mask.unsqueeze(-1).repeat(1, 1, tfmr_out.shape[-1]), -1000000000.0)
            pooled_out = self.out_linear(tfmr_out.max(dim=1).values)
            output_concat.append(pooled_out)
        return torch.cat(output_concat, dim=-1)

    def adjust_mask(self, mask):
        fully_masked = mask.all(dim=-1)
        mask[fully_masked, -1] = 0
        return mask

def adjust_mask(self, mask):
    fully_masked = mask.all(dim=-1)
    mask[fully_masked, -1] = 0
    return mask

class TransActTransformer(nn.Module):

    def __init__(self, transformer_in_dim, dim_feedforward=64, num_heads=1, dropout=0, transformer_layers=1, use_time_window_mask=False, time_window_ms=86400000, first_k_cols=1, concat_max_pool=True):
        super(TransActTransformer, self).__init__()
        self.use_time_window_mask = use_time_window_mask
        self.time_window_ms = time_window_ms
        self.concat_max_pool = concat_max_pool
        self.first_k_cols = first_k_cols
        encoder_layer = nn.TransformerEncoderLayer(d_model=transformer_in_dim, nhead=num_heads, dim_feedforward=dim_feedforward, dropout=dropout, batch_first=True)
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=transformer_layers)
        if self.concat_max_pool:
            self.out_linear = nn.Linear(transformer_in_dim, transformer_in_dim)

    def forward(self, target_emb, sequence_emb, time_interval_seq=None, mask=None):
        seq_len = sequence_emb.size(1)
        concat_seq_emb = torch.cat([sequence_emb, target_emb.unsqueeze(1).expand(-1, seq_len, -1)], dim=-1)
        key_padding_mask = self.adjust_mask(mask)
        if self.use_time_window_mask and self.training:
            rand_time_window_ms = random.randint(0, self.time_window_ms)
            time_window_mask = time_interval_seq < rand_time_window_ms
            key_padding_mask = torch.bitwise_or(key_padding_mask, time_window_mask)
        tfmr_out = self.transformer_encoder(src=concat_seq_emb, src_key_padding_mask=key_padding_mask)
        tfmr_out = tfmr_out.masked_fill(key_padding_mask.unsqueeze(-1).repeat(1, 1, tfmr_out.shape[-1]), 0.0)
        output_concat = []
        output_concat.append(tfmr_out[:, -self.first_k_cols:].flatten(start_dim=1))
        if self.concat_max_pool:
            tfmr_out = tfmr_out.masked_fill(key_padding_mask.unsqueeze(-1).repeat(1, 1, tfmr_out.shape[-1]), -1000000000.0)
            pooled_out = self.out_linear(tfmr_out.max(dim=1).values)
            output_concat.append(pooled_out)
        return torch.cat(output_concat, dim=-1)

    def adjust_mask(self, mask):
        fully_masked = mask.all(dim=-1)
        mask[fully_masked, -1] = 0
        return mask

def adjust_mask(self, mask):
    fully_masked = mask.all(dim=-1)
    mask[fully_masked, -1] = 0
    return mask

