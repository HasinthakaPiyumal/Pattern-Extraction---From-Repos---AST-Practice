# Cluster 4

class MiniMaxM1DecoderLayer(nn.Module):

    def __init__(self, config: MiniMaxM1Config, layer_idx: int):
        super().__init__()
        self.config = config
        self.hidden_size = config.hidden_size
        self.self_attn = self.build_attn(config, layer_idx)
        self.layer_idx = layer_idx
        self.block_sparse_moe = MiniMaxM1SparseMoeBlock(config)
        self.input_layernorm = MiniMaxM1RMSNorm(config.hidden_size, eps=config.rms_norm_eps)
        self.post_attention_layernorm = MiniMaxM1RMSNorm(config.hidden_size, eps=config.rms_norm_eps)
        self.postnorm = getattr(config, 'postnorm', False)
        self.layernorm_attention_alpha = getattr(config, 'layernorm_linear_attention_alpha', 1) if config.attention_type == 0 else getattr(config, 'layernorm_full_attention_alpha', 1)
        self.layernorm_attention_beta = getattr(config, 'layernorm_linear_attention_beta', 1) if config.attention_type == 0 else getattr(config, 'layernorm_full_attention_beta', 1)
        self.layernorm_mlp_alpha = getattr(config, 'layernorm_mlp_alpha', 1)
        self.layernorm_mlp_beta = getattr(config, 'layernorm_mlp_beta', 1)
        shared_intermediate = getattr(config, 'shared_intermediate_size', 0)
        self.shared_moe = False
        if shared_intermediate > 0:
            self.shared_moe = True
            self.shared_mlp = MiniMaxM1MLP(config)
            self.coefficient = torch.nn.Linear(self.hidden_size, 1, bias=False)

    def build_attn(self, config, layer_idx):
        if config.attention_type == 0:
            Attention_module = MiniMaxM1LightningAttention
        else:
            Attention_module = MiniMaxM1FlashAttention2
        return Attention_module(config, layer_idx)

    def forward(self, hidden_states: torch.Tensor, attention_mask: Optional[torch.Tensor]=None, position_ids: Optional[torch.LongTensor]=None, past_key_value: Optional[Tuple[torch.Tensor]]=None, output_attentions: Optional[bool]=False, output_router_logits: Optional[bool]=False, use_cache: Optional[bool]=False, slope_rate: Optional[float]=None, **kwargs) -> Tuple[torch.FloatTensor, Optional[Tuple[torch.FloatTensor, torch.FloatTensor]]]:
        if 'padding_mask' in kwargs:
            warnings.warn('Passing `padding_mask` is deprecated and will be removed in v4.37. Please make sure use `attention_mask` instead.`')
        '\n        Args:\n            hidden_states (`torch.FloatTensor`): input to the layer of shape `(batch, seq_len, embed_dim)`\n            attention_mask (`torch.FloatTensor`, *optional*): attention mask of size\n                `(batch, sequence_length)` where padding elements are indicated by 0.\n            past_key_value (`Tuple(torch.FloatTensor)`, *optional*): cached past key and value projection states\n            output_attentions (`bool`, *optional*):\n                Whether or not to return the attentions tensors of all attention layers. See `attentions` under\n                returned tensors for more detail.\n            output_router_logits (`bool`, *optional*):\n                Whether or not to return the logits of all the routers. They are useful for computing the router loss, and\n                should not be returned during inference.\n            use_cache (`bool`, *optional*):\n                If set to `True`, `past_key_values` key value states are returned and can be used to speed up decoding\n                (see `past_key_values`).\n        '
        residual = hidden_states
        hidden_states = self.input_layernorm(hidden_states)
        if self.postnorm:
            residual = hidden_states
        hidden_states, self_attn_weights, present_key_value = self.self_attn(hidden_states=hidden_states, position_ids=position_ids, attn_mask=attention_mask, past_key_value=past_key_value, output_attentions=output_attentions, use_cache=use_cache, slope_rate=slope_rate)
        hidden_states = residual * self.layernorm_attention_alpha + hidden_states * self.layernorm_attention_beta
        residual = hidden_states
        hidden_states = self.post_attention_layernorm(hidden_states)
        if self.postnorm:
            residual = hidden_states
        moe_hidden_states, router_logits = self.block_sparse_moe(hidden_states)
        if self.shared_moe:
            output_mlp = self.shared_mlp(hidden_states)
            weight_fp32 = self.coefficient.weight.float()
            coef = hidden_states.to(torch.float32) @ weight_fp32.T
            coef = torch.nn.functional.sigmoid(coef).to(hidden_states.dtype)
            hidden_states = moe_hidden_states * (1 - coef) + output_mlp * coef
        else:
            hidden_states = moe_hidden_states
        hidden_states = residual * self.layernorm_mlp_alpha + hidden_states * self.layernorm_mlp_beta
        outputs = (hidden_states,)
        if output_attentions:
            outputs += (self_attn_weights,)
        if use_cache:
            outputs += (present_key_value,)
        if output_router_logits:
            outputs += (router_logits,)
        return outputs

def build_attn(self, config, layer_idx):
    if config.attention_type == 0:
        Attention_module = MiniMaxM1LightningAttention
    else:
        Attention_module = MiniMaxM1FlashAttention2
    return Attention_module(config, layer_idx)

