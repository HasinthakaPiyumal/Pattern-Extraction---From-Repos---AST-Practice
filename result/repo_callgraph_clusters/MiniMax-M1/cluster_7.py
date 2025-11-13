# Cluster 7

class GLU(nn.Module):

    def __init__(self, d1, d2, bias=False):
        super().__init__()
        self.l1 = nn.Linear(d1, d2, bias=bias)
        self.l2 = nn.Linear(d1, d2, bias=bias)
        self.l3 = nn.Linear(d2, d1, bias=bias)

    def forward(self, x):
        o1 = self.l1(x)
        o2 = self.l2(x)
        output = o1 * o2
        output = self.l3(output)
        return output

def __init__(self, d1, d2, bias=False):
    super().__init__()
    self.l1 = nn.Linear(d1, d2, bias=bias)
    self.l2 = nn.Linear(d1, d2, bias=bias)
    self.l3 = nn.Linear(d2, d1, bias=bias)

class MiniMaxM1LightningAttention(nn.Module):

    def __init__(self, config: MiniMaxM1Config, layer_idx: Optional[int]=None):
        super().__init__()
        bias = False
        self.hidden_size = config.hidden_size
        self.num_heads = config.num_attention_heads
        self.head_dim = getattr(config, 'head_dim', self.hidden_size // self.num_heads)
        self.out_proj = nn.Linear(self.head_dim * self.num_heads, self.hidden_size, bias=bias)
        self.act = get_activation_fn(config.hidden_act)
        self.norm = MiniMaxM1RMSNorm(self.head_dim * self.num_heads)
        self.qkv_proj = nn.Linear(self.hidden_size, 3 * self.head_dim * self.num_heads, bias=bias)
        self.output_gate = nn.Linear(self.hidden_size, self.head_dim * self.num_heads, bias=bias)
        self.offset = 0
        self.layer_idx = layer_idx

    def forward(self, hidden_states, attn_mask: Optional[torch.Tensor]=None, output_attentions: bool=False, past_key_value: Optional[Tuple[torch.Tensor]]=None, use_cache: bool=False, slope_rate: Optional[torch.Tensor]=None, **kwargs):
        if not self.training and (not do_eval):
            return self.inference(hidden_states, attn_mask, output_attentions, past_key_value, use_cache, slope_rate)

    def inference(self, x, attn_mask: Optional[torch.Tensor]=None, output_attentions: bool=False, past_key_value: Optional[Tuple[torch.Tensor]]=None, use_cache: bool=False, slope_rate: Optional[torch.Tensor]=None):
        b, n, d = x.shape
        qkv = self.act(self.qkv_proj(x))
        new_shape = qkv.size()[:-1] + (self.num_heads, -1)
        qkv = qkv.view(*new_shape)
        q, k, v = torch.split(qkv, [self.head_dim] * 3, dim=3)
        q = q.transpose(1, 2)
        k = k.transpose(1, 2)
        v = v.transpose(1, 2)
        if past_key_value is None:
            self.offset = q.shape[-2]
        else:
            self.offset += 1
        ratio = torch.exp(-slope_rate)
        if past_key_value is None:
            slope_rate = slope_rate.to(torch.float32)
            if attn_mask is not None:
                v = v.masked_fill((1 - attn_mask).unsqueeze(1).unsqueeze(-1).to(torch.bool), 0)
            NUM_BLOCK = (n + BLOCK - 1) // BLOCK
            b, h, n, d = q.shape
            e = v.shape[-1]
            array = torch.arange(BLOCK).to(q) + 1
            q_decay = torch.exp(-slope_rate * array.reshape(-1, 1))
            k_decay = torch.exp(-slope_rate * (BLOCK - array.reshape(-1, 1)))
            index = array[:, None] - array[None, :]
            s_index = slope_rate * index[None, None]
            s_index = torch.where(index >= 0, -s_index, float('-inf'))
            diag_decay = torch.exp(s_index)
            kv = torch.zeros(b, h, d, e).to(torch.float32).to(q.device)
            output = torch.empty((b, h, n, e), dtype=q.dtype, device=q.device)
            for i in range(NUM_BLOCK):
                si = i * BLOCK
                ei = min(si + BLOCK, n)
                m = ei - si
                qi = q[:, :, si:ei].contiguous()
                ki = k[:, :, si:ei].contiguous()
                vi = v[:, :, si:ei].contiguous()
                qkv_none_diag = torch.matmul(qi * q_decay[:, :m], kv).to(torch.float32)
                qk = torch.matmul(qi, ki.transpose(-1, -2)).to(torch.float32) * diag_decay[:, :, :m, :m]
                qkv_diag = torch.matmul(qk, vi.to(torch.float32))
                block_decay = torch.exp(-slope_rate * m)
                output[:, :, si:ei] = qkv_none_diag + qkv_diag
                kv = block_decay * kv + torch.matmul((ki * k_decay[:, -m:]).transpose(-1, -2).to(vi.dtype), vi)
        else:
            kv = past_key_value
            output = []
            for i in range(n):
                kv = ratio * kv + torch.einsum('... n d, ... n e -> ... d e', k[:, :, i:i + 1], v[:, :, i:i + 1])
                qkv = torch.einsum('... n e, ... e d -> ... n d', q[:, :, i:i + 1], kv.to(q.dtype))
                output.append(qkv)
            output = torch.concat(output, dim=-2)
        output = rearrange(output, 'b h n d -> b n (h d)')
        output = self.norm(output)
        output = F.sigmoid(self.output_gate(x)) * output
        output = self.out_proj(output)
        attn_weights = None
        return (output, attn_weights, kv)

def __init__(self, config: MiniMaxM1Config, layer_idx: Optional[int]=None):
    super().__init__()
    bias = False
    self.hidden_size = config.hidden_size
    self.num_heads = config.num_attention_heads
    self.head_dim = getattr(config, 'head_dim', self.hidden_size // self.num_heads)
    self.out_proj = nn.Linear(self.head_dim * self.num_heads, self.hidden_size, bias=bias)
    self.act = get_activation_fn(config.hidden_act)
    self.norm = MiniMaxM1RMSNorm(self.head_dim * self.num_heads)
    self.qkv_proj = nn.Linear(self.hidden_size, 3 * self.head_dim * self.num_heads, bias=bias)
    self.output_gate = nn.Linear(self.hidden_size, self.head_dim * self.num_heads, bias=bias)
    self.offset = 0
    self.layer_idx = layer_idx

class MiniMaxM1RMSNorm(nn.Module):

    def __init__(self, hidden_size, eps=1e-06):
        """
        MiniMaxM1RMSNorm is equivalent to T5LayerNorm
        """
        super().__init__()
        self.weight = nn.Parameter(torch.ones(hidden_size))
        self.variance_epsilon = eps

    def forward(self, hidden_states):
        input_dtype = hidden_states.dtype
        hidden_states = hidden_states.to(torch.float32)
        variance = hidden_states.pow(2).mean(-1, keepdim=True)
        hidden_states = hidden_states * torch.rsqrt(variance + self.variance_epsilon)
        return self.weight * hidden_states.to(input_dtype)

def __init__(self, hidden_size, eps=1e-06):
    """
        MiniMaxM1RMSNorm is equivalent to T5LayerNorm
        """
    super().__init__()
    self.weight = nn.Parameter(torch.ones(hidden_size))
    self.variance_epsilon = eps

class MiniMaxM1Attention(nn.Module):
    """
    Multi-headed attention from 'Attention Is All You Need' paper. Modified to use sliding window attention: Longformer
    and "Generating Long Sequences with Sparse Transformers".
    """

    def __init__(self, config: MiniMaxM1Config, layer_idx: Optional[int]=None):
        super().__init__()
        self.config = config
        self.layer_idx = layer_idx
        if layer_idx is None:
            logger.warning_once(f'Instantiating {self.__class__.__name__} without passing a `layer_idx` is not recommended and will lead to errors during the forward call if caching is used. Please make sure to provide a `layer_idx` when creating this class.')
        self.hidden_size = config.hidden_size
        self.num_heads = config.num_attention_heads
        self.head_dim = getattr(config, 'head_dim', self.hidden_size // self.num_heads)
        self.num_key_value_heads = config.num_key_value_heads
        self.num_key_value_groups = self.num_heads // self.num_key_value_heads
        self.max_position_embeddings = config.max_position_embeddings
        self.rope_theta = config.rope_theta
        self.is_causal = True
        self.attention_dropout = config.attention_dropout
        self.q_proj = nn.Linear(self.hidden_size, self.num_heads * self.head_dim, bias=False)
        self.k_proj = nn.Linear(self.hidden_size, self.num_key_value_heads * self.head_dim, bias=False)
        self.v_proj = nn.Linear(self.hidden_size, self.num_key_value_heads * self.head_dim, bias=False)
        self.o_proj = nn.Linear(self.num_heads * self.head_dim, self.hidden_size, bias=False)
        self.rotary_dim = getattr(config, 'rotary_dim', self.head_dim)
        self.rotary_emb = MiniMaxM1RotaryEmbedding(self.rotary_dim, max_position_embeddings=self.max_position_embeddings, base=self.rope_theta)

    def _shape(self, tensor: torch.Tensor, seq_len: int, bsz: int):
        return tensor.view(bsz, seq_len, self.num_heads, self.head_dim).transpose(1, 2).contiguous()

    def forward(self, hidden_states: torch.Tensor, attention_mask: Optional[torch.Tensor]=None, position_ids: Optional[torch.LongTensor]=None, past_key_value: Optional[Cache]=None, output_attentions: bool=False, use_cache: bool=False, **kwargs) -> Tuple[torch.Tensor, Optional[torch.Tensor], Optional[Tuple[torch.Tensor]]]:
        if 'padding_mask' in kwargs:
            warnings.warn('Passing `padding_mask` is deprecated and will be removed in v4.37. Please make sure use `attention_mask` instead.`')
        bsz, q_len, _ = hidden_states.size()
        query_states = self.q_proj(hidden_states)
        key_states = self.k_proj(hidden_states)
        value_states = self.v_proj(hidden_states)
        query_states = query_states.view(bsz, q_len, self.num_heads, self.head_dim).transpose(1, 2)
        key_states = key_states.view(bsz, q_len, self.num_key_value_heads, self.head_dim).transpose(1, 2)
        value_states = value_states.view(bsz, q_len, self.num_key_value_heads, self.head_dim).transpose(1, 2)
        kv_seq_len = key_states.shape[-2]
        if past_key_value is not None:
            if self.layer_idx is None:
                raise ValueError(f'The cache structure has changed since version v4.36. If you are using {self.__class__.__name__} for auto-regressive decoding with k/v caching, please make sure to initialize the attention class with a layer index.')
            kv_seq_len += past_key_value.get_usable_length(kv_seq_len, self.layer_idx)
        cos, sin = self.rotary_emb(value_states, seq_len=kv_seq_len)
        query_states, key_states = apply_rotary_pos_emb(query_states, key_states, cos, sin, position_ids)
        if past_key_value is not None:
            cache_kwargs = {'sin': sin, 'cos': cos}
            key_states, value_states = past_key_value.update(key_states, value_states, self.layer_idx, cache_kwargs)
        key_states = repeat_kv(key_states, self.num_key_value_groups)
        value_states = repeat_kv(value_states, self.num_key_value_groups)
        attn_weights = torch.matmul(query_states, key_states.transpose(2, 3)) / math.sqrt(self.head_dim)
        if attn_weights.size() != (bsz, self.num_heads, q_len, kv_seq_len):
            raise ValueError(f'Attention weights should be of size {(bsz, self.num_heads, q_len, kv_seq_len)}, but is {attn_weights.size()}')
        if attention_mask is not None:
            if attention_mask.size() != (bsz, 1, q_len, kv_seq_len):
                raise ValueError(f'Attention mask should be of size {(bsz, 1, q_len, kv_seq_len)}, but is {attention_mask.size()}')
            attn_weights = attn_weights + attention_mask
        attn_weights = nn.functional.softmax(attn_weights, dim=-1, dtype=torch.float32).to(query_states.dtype)
        attn_weights = nn.functional.dropout(attn_weights, p=self.attention_dropout, training=self.training)
        attn_output = torch.matmul(attn_weights, value_states)
        if attn_output.size() != (bsz, self.num_heads, q_len, self.head_dim):
            raise ValueError(f'`attn_output` should be of size {(bsz, self.num_heads, q_len, self.head_dim)}, but is {attn_output.size()}')
        attn_output = attn_output.transpose(1, 2).contiguous()
        attn_output = attn_output.reshape(bsz, q_len, self.hidden_size)
        attn_output = self.o_proj(attn_output)
        if not output_attentions:
            attn_weights = None
        return (attn_output, attn_weights, past_key_value)

def __init__(self, config: MiniMaxM1Config, layer_idx: Optional[int]=None):
    super().__init__()
    self.config = config
    self.layer_idx = layer_idx
    if layer_idx is None:
        logger.warning_once(f'Instantiating {self.__class__.__name__} without passing a `layer_idx` is not recommended and will lead to errors during the forward call if caching is used. Please make sure to provide a `layer_idx` when creating this class.')
    self.hidden_size = config.hidden_size
    self.num_heads = config.num_attention_heads
    self.head_dim = getattr(config, 'head_dim', self.hidden_size // self.num_heads)
    self.num_key_value_heads = config.num_key_value_heads
    self.num_key_value_groups = self.num_heads // self.num_key_value_heads
    self.max_position_embeddings = config.max_position_embeddings
    self.rope_theta = config.rope_theta
    self.is_causal = True
    self.attention_dropout = config.attention_dropout
    self.q_proj = nn.Linear(self.hidden_size, self.num_heads * self.head_dim, bias=False)
    self.k_proj = nn.Linear(self.hidden_size, self.num_key_value_heads * self.head_dim, bias=False)
    self.v_proj = nn.Linear(self.hidden_size, self.num_key_value_heads * self.head_dim, bias=False)
    self.o_proj = nn.Linear(self.num_heads * self.head_dim, self.hidden_size, bias=False)
    self.rotary_dim = getattr(config, 'rotary_dim', self.head_dim)
    self.rotary_emb = MiniMaxM1RotaryEmbedding(self.rotary_dim, max_position_embeddings=self.max_position_embeddings, base=self.rope_theta)

class MiniMaxM1FlashAttention2(MiniMaxM1Attention):
    """
    MiniMaxM1 flash attention module. This module inherits from `MiniMaxM1Attention` as the weights of the module stays
    untouched. The only required change would be on the forward pass where it needs to correctly call the public API of
    flash attention and deal with padding tokens in case the input contains any of them.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._flash_attn_uses_top_left_mask = not is_flash_attn_greater_or_equal_2_10()

    def forward(self, hidden_states: torch.Tensor, attention_mask: Optional[torch.Tensor]=None, position_ids: Optional[torch.LongTensor]=None, past_key_value: Optional[Union[Cache, Tuple[torch.Tensor]]]=None, output_attentions: bool=False, use_cache: bool=False, **kwargs):
        if 'padding_mask' in kwargs:
            warnings.warn('Passing `padding_mask` is deprecated and will be removed in v4.37. Please make sure use `attention_mask` instead.`')
            attention_mask = kwargs.pop('padding_mask')
        bsz, q_len, _ = hidden_states.size()
        query_states = self.q_proj(hidden_states)
        key_states = self.k_proj(hidden_states)
        value_states = self.v_proj(hidden_states)
        query_states = query_states.view(bsz, q_len, self.num_heads, self.head_dim).transpose(1, 2)
        key_states = key_states.view(bsz, q_len, self.num_key_value_heads, self.head_dim).transpose(1, 2)
        value_states = value_states.view(bsz, q_len, self.num_key_value_heads, self.head_dim).transpose(1, 2)
        kv_seq_len = key_states.shape[-2]
        if past_key_value is not None:
            kv_seq_len += past_key_value[0].shape[-3]
        rotary_seq_len = max(kv_seq_len, position_ids[:, -1].max().item()) + 1
        cos, sin = self.rotary_emb(value_states, seq_len=rotary_seq_len)
        query_states, key_states = apply_rotary_pos_emb(query_states, key_states, cos, sin, position_ids)
        use_sliding_windows = _flash_supports_window_size and getattr(self.config, 'sliding_window', None) is not None and (kv_seq_len > self.config.sliding_window)
        if not _flash_supports_window_size:
            logger.warning_once('The current flash attention version does not support sliding window attention, for a more memory efficient implementation make sure to upgrade flash-attn library.')
        dropout_rate = 0.0 if not self.training else self.attention_dropout
        input_dtype = query_states.dtype
        if input_dtype == torch.float32:
            if torch.is_autocast_enabled():
                target_dtype = torch.get_autocast_gpu_dtype()
            elif hasattr(self.config, '_pre_quantization_dtype'):
                target_dtype = self.config._pre_quantization_dtype
            else:
                target_dtype = self.q_proj.weight.dtype
            logger.warning_once(f'The input hidden states seems to be silently casted in float32, this might be related to the fact you have upcasted embedding or layer norm layers in float32. We will cast back the input in {target_dtype}.')
            query_states = query_states.to(target_dtype)
            key_states = key_states.to(target_dtype)
            value_states = value_states.to(target_dtype)
        query_states = query_states.transpose(1, 2)
        key_states = key_states.transpose(1, 2)
        value_states = value_states.transpose(1, 2)
        if past_key_value is not None:
            key_states = torch.cat([past_key_value[0], key_states], dim=-3)
            value_states = torch.cat([past_key_value[1], value_states], dim=-3)
        past_key_value = (key_states, value_states) if use_cache else None
        attn_output = self._flash_attention_forward(query_states, key_states, value_states, attention_mask, q_len, dropout=dropout_rate, use_sliding_windows=use_sliding_windows)
        attn_output = attn_output.reshape(bsz, q_len, -1).contiguous()
        attn_output = self.o_proj(attn_output)
        if not output_attentions:
            attn_weights = None
        return (attn_output, attn_weights, past_key_value)

    def _flash_attention_forward(self, query_states, key_states, value_states, attention_mask, query_length, dropout=0.0, softmax_scale=None, use_sliding_windows=False):
        """
        Calls the forward method of Flash Attention - if the input hidden states contain at least one padding token
        first unpad the input, then computes the attention scores and pad the final attention scores.

        Args:
            query_states (`torch.Tensor`):
                Input query states to be passed to Flash Attention API
            key_states (`torch.Tensor`):
                Input key states to be passed to Flash Attention API
            value_states (`torch.Tensor`):
                Input value states to be passed to Flash Attention API
            attention_mask (`torch.Tensor`):
                The padding mask - corresponds to a tensor of size `(batch_size, seq_len)` where 0 stands for the
                position of padding tokens and 1 for the position of non-padding tokens.
            dropout (`float`):
                Attention dropout
            softmax_scale (`float`, *optional*):
                The scaling of QK^T before applying softmax. Default to 1 / sqrt(head_dim)
            use_sliding_windows (`bool`, *optional*):
                Whether to activate sliding window attention.
        """
        if not self._flash_attn_uses_top_left_mask:
            causal = self.is_causal
        else:
            causal = self.is_causal and query_length != 1
        if attention_mask is not None:
            batch_size = query_states.shape[0]
            query_states, key_states, value_states, indices_q, cu_seq_lens, max_seq_lens = self._upad_input(query_states, key_states, value_states, attention_mask, query_length)
            cu_seqlens_q, cu_seqlens_k = cu_seq_lens
            max_seqlen_in_batch_q, max_seqlen_in_batch_k = max_seq_lens
            if not use_sliding_windows:
                attn_output_unpad = flash_attn_varlen_func(query_states, key_states, value_states, cu_seqlens_q=cu_seqlens_q, cu_seqlens_k=cu_seqlens_k, max_seqlen_q=max_seqlen_in_batch_q, max_seqlen_k=max_seqlen_in_batch_k, dropout_p=dropout, softmax_scale=softmax_scale, causal=causal)
            else:
                attn_output_unpad = flash_attn_varlen_func(query_states, key_states, value_states, cu_seqlens_q=cu_seqlens_q, cu_seqlens_k=cu_seqlens_k, max_seqlen_q=max_seqlen_in_batch_q, max_seqlen_k=max_seqlen_in_batch_k, dropout_p=dropout, softmax_scale=softmax_scale, causal=causal, window_size=(self.config.sliding_window, self.config.sliding_window))
            attn_output = pad_input(attn_output_unpad, indices_q, batch_size, query_length)
        elif not use_sliding_windows:
            attn_output = flash_attn_func(query_states, key_states, value_states, dropout, softmax_scale=softmax_scale, causal=causal)
        else:
            attn_output = flash_attn_func(query_states, key_states, value_states, dropout, softmax_scale=softmax_scale, causal=causal, window_size=(self.config.sliding_window, self.config.sliding_window))
        return attn_output

    def _upad_input(self, query_layer, key_layer, value_layer, attention_mask, query_length):
        batch_size, kv_seq_len, num_heads, head_dim = key_layer.shape
        if kv_seq_len != attention_mask.shape[-1]:
            attention_mask_num_tokens = attention_mask.shape[-1]
            attention_mask = attention_mask[:, attention_mask_num_tokens - kv_seq_len:]
        indices_k, cu_seqlens_k, max_seqlen_in_batch_k = _get_unpad_data(attention_mask)
        key_layer = index_first_axis(key_layer.reshape(batch_size * kv_seq_len, num_heads, head_dim), indices_k)
        value_layer = index_first_axis(value_layer.reshape(batch_size * kv_seq_len, num_heads, head_dim), indices_k)
        if query_length == kv_seq_len:
            query_layer = index_first_axis(query_layer.reshape(batch_size * kv_seq_len, num_heads, head_dim), indices_k)
            cu_seqlens_q = cu_seqlens_k
            max_seqlen_in_batch_q = max_seqlen_in_batch_k
            indices_q = indices_k
        elif query_length == 1:
            max_seqlen_in_batch_q = 1
            cu_seqlens_q = torch.arange(batch_size + 1, dtype=torch.int32, device=query_layer.device)
            indices_q = cu_seqlens_q[:-1]
            query_layer = query_layer.squeeze(1)
        else:
            attention_mask = attention_mask[:, -query_length:]
            query_layer, indices_q, cu_seqlens_q, max_seqlen_in_batch_q = unpad_input(query_layer, attention_mask)
        return (query_layer, key_layer, value_layer, indices_q, (cu_seqlens_q, cu_seqlens_k), (max_seqlen_in_batch_q, max_seqlen_in_batch_k))

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self._flash_attn_uses_top_left_mask = not is_flash_attn_greater_or_equal_2_10()

class MiniMaxM1MLP(nn.Module):

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.hidden_size = config.hidden_size
        self.intermediate_size = config.intermediate_size
        self.gate_proj = nn.Linear(self.hidden_size, self.intermediate_size, bias=False)
        self.up_proj = nn.Linear(self.hidden_size, self.intermediate_size, bias=False)
        self.down_proj = nn.Linear(self.intermediate_size, self.hidden_size, bias=False)
        self.act_fn = ACT2FN[config.hidden_act]

    def forward(self, x):
        down_proj = self.down_proj(self.act_fn(self.gate_proj(x)) * self.up_proj(x))
        return down_proj

def __init__(self, config):
    super().__init__()
    self.config = config
    self.hidden_size = config.hidden_size
    self.intermediate_size = config.intermediate_size
    self.gate_proj = nn.Linear(self.hidden_size, self.intermediate_size, bias=False)
    self.up_proj = nn.Linear(self.hidden_size, self.intermediate_size, bias=False)
    self.down_proj = nn.Linear(self.intermediate_size, self.hidden_size, bias=False)
    self.act_fn = ACT2FN[config.hidden_act]

class MiniMaxM1BlockSparseTop2MLP(nn.Module):

    def __init__(self, config: MiniMaxM1Config):
        super().__init__()
        self.ffn_dim = config.intermediate_size
        self.hidden_dim = config.hidden_size
        self.w1 = nn.Linear(self.hidden_dim, self.ffn_dim, bias=False)
        self.w2 = nn.Linear(self.ffn_dim, self.hidden_dim, bias=False)
        self.w3 = nn.Linear(self.hidden_dim, self.ffn_dim, bias=False)
        self.act_fn = ACT2FN[config.hidden_act]

    def forward(self, hidden_states):
        current_hidden_states = self.act_fn(self.w1(hidden_states)) * self.w3(hidden_states)
        current_hidden_states = self.w2(current_hidden_states)
        return current_hidden_states

def __init__(self, config: MiniMaxM1Config):
    super().__init__()
    self.ffn_dim = config.intermediate_size
    self.hidden_dim = config.hidden_size
    self.w1 = nn.Linear(self.hidden_dim, self.ffn_dim, bias=False)
    self.w2 = nn.Linear(self.ffn_dim, self.hidden_dim, bias=False)
    self.w3 = nn.Linear(self.hidden_dim, self.ffn_dim, bias=False)
    self.act_fn = ACT2FN[config.hidden_act]

class MiniMaxM1BLockSparseTop2MLP(MiniMaxM1BlockSparseTop2MLP):

    def __init__(self, *args, **kwargs):
        logger.warning_once('MiniMaxM1BLockSparseTop2MLP is deprecated by MiniMaxM1BlockSparseTop2MLP and will be removed in v4.40.')
        super().__init__(*args, **kwargs)

def __init__(self, *args, **kwargs):
    logger.warning_once('MiniMaxM1BLockSparseTop2MLP is deprecated by MiniMaxM1BlockSparseTop2MLP and will be removed in v4.40.')
    super().__init__(*args, **kwargs)

class MiniMaxM1SparseMoeBlock(nn.Module):
    """
    This implementation is
    strictly equivalent to standard MoE with full capacity (no
    dropped tokens). It's faster since it formulates MoE operations
    in terms of block-sparse operations to accomodate imbalanced
    assignments of tokens to experts, whereas standard MoE either
    (1) drop tokens at the cost of reduced performance or (2) set
    capacity factor to number of experts and thus waste computation
    and memory on padding.
    """

    def __init__(self, config):
        super().__init__()
        self.hidden_dim = config.hidden_size
        self.ffn_dim = config.intermediate_size
        self.num_experts = config.num_local_experts
        self.top_k = config.num_experts_per_tok
        self.gate = nn.Linear(self.hidden_dim, self.num_experts, bias=False)
        self.experts = nn.ModuleList([MiniMaxM1BlockSparseTop2MLP(config) for _ in range(self.num_experts)])
        self.jitter_noise = config.router_jitter_noise

    def forward(self, hidden_states: torch.Tensor) -> torch.Tensor:
        """ """
        batch_size, sequence_length, hidden_dim = hidden_states.shape
        if self.training and self.jitter_noise > 0:
            hidden_states *= torch.empty_like(hidden_states).uniform_(1.0 - self.jitter_noise, 1.0 + self.jitter_noise)
        hidden_states = hidden_states.view(-1, hidden_dim)
        router_logits = self.gate(hidden_states)
        routing_weights = F.softmax(router_logits, dim=1, dtype=torch.float)
        routing_weights, selected_experts = torch.topk(routing_weights, self.top_k, dim=-1)
        routing_weights /= routing_weights.sum(dim=-1, keepdim=True)
        routing_weights = routing_weights.to(hidden_states.dtype)
        final_hidden_states = torch.zeros((batch_size * sequence_length, hidden_dim), dtype=hidden_states.dtype, device=hidden_states.device)
        expert_mask = torch.nn.functional.one_hot(selected_experts, num_classes=self.num_experts).permute(2, 1, 0)
        for expert_idx in range(self.num_experts):
            expert_layer = self.experts[expert_idx]
            idx, top_x = torch.where(expert_mask[expert_idx])
            current_state = hidden_states[None, top_x].reshape(-1, hidden_dim)
            current_hidden_states = expert_layer(current_state) * routing_weights[top_x, idx, None]
            final_hidden_states.index_add_(0, top_x, current_hidden_states.to(hidden_states.dtype))
        final_hidden_states = final_hidden_states.reshape(batch_size, sequence_length, hidden_dim)
        return (final_hidden_states, router_logits)

def __init__(self, config):
    super().__init__()
    self.hidden_dim = config.hidden_size
    self.ffn_dim = config.intermediate_size
    self.num_experts = config.num_local_experts
    self.top_k = config.num_experts_per_tok
    self.gate = nn.Linear(self.hidden_dim, self.num_experts, bias=False)
    self.experts = nn.ModuleList([MiniMaxM1BlockSparseTop2MLP(config) for _ in range(self.num_experts)])
    self.jitter_noise = config.router_jitter_noise

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

@add_start_docstrings('The bare MiniMaxM1 Model outputting raw hidden-states without any specific head on top.', MIXTRAL_START_DOCSTRING)
class MiniMaxM1Model(MiniMaxM1PreTrainedModel):
    """
    Transformer decoder consisting of *config.num_hidden_layers* layers. Each layer is a [`MiniMaxM1DecoderLayer`]

    Args:
        config: MiniMaxM1Config
    """

    def __init__(self, config: MiniMaxM1Config):
        super().__init__(config)
        self.padding_idx = config.pad_token_id
        self.vocab_size = config.vocab_size
        self.embed_tokens = nn.Embedding(config.vocab_size, config.hidden_size, self.padding_idx)
        self.attn_type_list = config.attn_type_list
        config_copy = copy.deepcopy(config)
        self.layers = nn.ModuleList([])
        for i in range(config.num_hidden_layers):
            _config = copy.deepcopy(config)
            if self.attn_type_list[i] == 0:
                _config._attn_implementation = 'linear_attention'
                _config.attention_type = 0
            else:
                _config._attn_implementation = config_copy._attn_implementation
                _config.attention_type = 1
            self.layers.append(MiniMaxM1DecoderLayer(_config, i))
        self._attn_implementation = config_copy._attn_implementation
        self.norm = MiniMaxM1RMSNorm(config.hidden_size, eps=config.rms_norm_eps)
        self.gradient_checkpointing = False
        self.slopes = self._build_slope_tensor(config.num_attention_heads)
        self._linear_attn_mask = torch.empty(0)
        self.post_init()

    def get_input_embeddings(self):
        return self.embed_tokens

    def set_input_embeddings(self, value):
        self.embed_tokens = value

    @staticmethod
    def _build_slope_tensor(n_attention_heads: int):

        def get_slopes(n):

            def get_slopes_power_of_2(n):
                start = 2 ** (-2 ** (-(math.log2(n) - 3)))
                ratio = start
                return [start * ratio ** i for i in range(n)]
            if math.log2(n).is_integer():
                return get_slopes_power_of_2(n)
            else:
                closest_power_of_2 = 2 ** math.floor(math.log2(n))
                return get_slopes_power_of_2(closest_power_of_2) + get_slopes(2 * closest_power_of_2)[0::2][:n - closest_power_of_2]
        slopes = torch.tensor(get_slopes(n_attention_heads), dtype=torch.float32).reshape(n_attention_heads, 1, 1)
        return slopes

    @add_start_docstrings_to_model_forward(MIXTRAL_INPUTS_DOCSTRING)
    def forward(self, input_ids: torch.LongTensor=None, attention_mask: Optional[torch.Tensor]=None, position_ids: Optional[torch.LongTensor]=None, past_key_values: Optional[List[torch.FloatTensor]]=None, inputs_embeds: Optional[torch.FloatTensor]=None, use_cache: Optional[bool]=None, output_attentions: Optional[bool]=None, output_hidden_states: Optional[bool]=None, output_router_logits: Optional[bool]=None, return_dict: Optional[bool]=None) -> Union[Tuple, MoeModelOutputWithPast]:
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_router_logits = output_router_logits if output_router_logits is not None else self.config.output_router_logits
        output_hidden_states = output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        use_cache = use_cache if use_cache is not None else self.config.use_cache
        return_dict = return_dict if return_dict is not None else self.config.use_return_dict
        if input_ids is not None and inputs_embeds is not None:
            raise ValueError('You cannot specify both decoder_input_ids and decoder_inputs_embeds at the same time')
        elif input_ids is not None:
            batch_size, seq_length = input_ids.shape
            default_device = input_ids.device
        elif inputs_embeds is not None:
            batch_size, seq_length, _ = inputs_embeds.shape
            default_device = inputs_embeds.device
        else:
            raise ValueError('You have to specify either decoder_input_ids or decoder_inputs_embeds')
        past_key_values_length = 0
        if self.gradient_checkpointing and self.training:
            if use_cache:
                logger.warning_once('`use_cache=True` is incompatible with gradient checkpointing. Setting `use_cache=False`...')
                use_cache = False
        seq_length_with_past = seq_length
        if past_key_values is not None:
            for idx in range(len(past_key_values)):
                if self.attn_type_list[idx] == 1:
                    past_key_values_length = past_key_values[idx][0].shape[-3]
                    seq_length_with_past = seq_length_with_past + past_key_values_length
                    break
        if position_ids is None:
            device = input_ids.device if input_ids is not None else inputs_embeds.device
            position_ids = torch.arange(past_key_values_length, seq_length + past_key_values_length, dtype=torch.long, device=device)
            position_ids = position_ids.unsqueeze(0).view(-1, seq_length)
        else:
            position_ids = position_ids.view(-1, seq_length).long()
        if inputs_embeds is None:
            inputs_embeds = self.embed_tokens(input_ids)
        if attention_mask is not None and self._attn_implementation == 'flash_attention_2' and use_cache:
            is_padding_right = attention_mask[:, -1].sum().item() != batch_size
            if is_padding_right:
                raise ValueError("You are attempting to perform batched generation with padding_side='right' this may lead to unexpected behaviour for Flash Attention version of MiniMaxM1. Make sure to  call `tokenizer.padding_side  = 'left'` before tokenizing the input. ")
        slope_rates = [self.slopes.to(default_device) for _ in range(len(self.layers))]
        hidden_states = inputs_embeds
        all_hidden_states = () if output_hidden_states else None
        all_self_attns = () if output_attentions else None
        all_router_logits = () if output_router_logits else None
        next_decoder_cache = () if use_cache else None
        for idx, decoder_layer in enumerate(self.layers):
            if output_hidden_states:
                all_hidden_states += (hidden_states,)
            past_key_value = past_key_values[idx] if past_key_values is not None else None
            attn_mask = attention_mask
            slope_rate = slope_rates[idx]
            slope_rate = slope_rate * (1 - idx / (len(self.layers) - 1) + 1e-05)
            if self.gradient_checkpointing and self.training:
                layer_outputs = self._gradient_checkpointing_func(decoder_layer.__call__, hidden_states, attention_mask, position_ids, past_key_values, output_attentions, output_router_logits, use_cache)
            else:
                layer_outputs = decoder_layer(hidden_states, attention_mask=attn_mask, position_ids=position_ids, past_key_value=past_key_value, output_attentions=output_attentions, output_router_logits=output_router_logits, use_cache=use_cache, slope_rate=slope_rate)
            hidden_states = layer_outputs[0]
            if use_cache:
                next_decoder_cache += (layer_outputs[2 if output_attentions else 1],)
            if output_attentions:
                all_self_attns += (layer_outputs[1],)
            if output_router_logits:
                all_router_logits += (layer_outputs[-1],)
        hidden_states = self.norm(hidden_states)
        if output_hidden_states:
            all_hidden_states += (hidden_states,)
        next_cache = next_decoder_cache if use_cache else None
        if not return_dict:
            return tuple((v for v in [hidden_states, next_cache, all_hidden_states, all_self_attns, all_router_logits] if v is not None))
        return MoeModelOutputWithPast(last_hidden_state=hidden_states, past_key_values=next_cache, hidden_states=all_hidden_states, attentions=all_self_attns, router_logits=all_router_logits)

def __init__(self, config: MiniMaxM1Config):
    super().__init__(config)
    self.padding_idx = config.pad_token_id
    self.vocab_size = config.vocab_size
    self.embed_tokens = nn.Embedding(config.vocab_size, config.hidden_size, self.padding_idx)
    self.attn_type_list = config.attn_type_list
    config_copy = copy.deepcopy(config)
    self.layers = nn.ModuleList([])
    for i in range(config.num_hidden_layers):
        _config = copy.deepcopy(config)
        if self.attn_type_list[i] == 0:
            _config._attn_implementation = 'linear_attention'
            _config.attention_type = 0
        else:
            _config._attn_implementation = config_copy._attn_implementation
            _config.attention_type = 1
        self.layers.append(MiniMaxM1DecoderLayer(_config, i))
    self._attn_implementation = config_copy._attn_implementation
    self.norm = MiniMaxM1RMSNorm(config.hidden_size, eps=config.rms_norm_eps)
    self.gradient_checkpointing = False
    self.slopes = self._build_slope_tensor(config.num_attention_heads)
    self._linear_attn_mask = torch.empty(0)
    self.post_init()

class MiniMaxM1ForCausalLM(MiniMaxM1PreTrainedModel):
    _tied_weights_keys = ['lm_head.weight']

    def __init__(self, config):
        super().__init__(config)
        self.model = MiniMaxM1Model(config)
        self.vocab_size = config.vocab_size
        self.lm_head = nn.Linear(config.hidden_size, config.vocab_size, bias=False)
        self.router_aux_loss_coef = config.router_aux_loss_coef
        self.num_experts = config.num_local_experts
        self.num_experts_per_tok = config.num_experts_per_tok
        self.post_init()

    def get_input_embeddings(self):
        return self.model.embed_tokens

    def set_input_embeddings(self, value):
        self.model.embed_tokens = value

    def get_output_embeddings(self):
        return self.lm_head

    def set_output_embeddings(self, new_embeddings):
        self.lm_head = new_embeddings

    def set_decoder(self, decoder):
        self.model = decoder

    def get_decoder(self):
        return self.model

    @add_start_docstrings_to_model_forward(MIXTRAL_INPUTS_DOCSTRING)
    @replace_return_docstrings(output_type=MoeCausalLMOutputWithPast, config_class=_CONFIG_FOR_DOC)
    def forward(self, input_ids: torch.LongTensor=None, attention_mask: Optional[torch.Tensor]=None, position_ids: Optional[torch.LongTensor]=None, past_key_values: Optional[List[torch.FloatTensor]]=None, inputs_embeds: Optional[torch.FloatTensor]=None, labels: Optional[torch.LongTensor]=None, use_cache: Optional[bool]=None, output_attentions: Optional[bool]=None, output_hidden_states: Optional[bool]=None, output_router_logits: Optional[bool]=None, return_dict: Optional[bool]=None) -> Union[Tuple, MoeCausalLMOutputWithPast]:
        """
        Args:
            labels (`torch.LongTensor` of shape `(batch_size, sequence_length)`, *optional*):
                Labels for computing the masked language modeling loss. Indices should either be in `[0, ...,
                config.vocab_size]` or -100 (see `input_ids` docstring). Tokens with indices set to `-100` are ignored
                (masked), the loss is only computed for the tokens with labels in `[0, ..., config.vocab_size]`.

        Returns:

        Example:

        ```python
        >>> from transformers import AutoTokenizer, MiniMaxM1ForCausalLM

        >>> model = MiniMaxM1ForCausalLM.from_pretrained(PATH_TO_WEIGHTS)
        >>> tokenizer = AutoTokenizer.from_pretrained(PATH_TO_WEIGHTS)

        >>> prompt = "Hey, are you conscious? Can you talk to me?"
        >>> inputs = tokenizer(prompt, return_tensors="pt")

        >>> # Generate
        >>> generate_ids = model.generate(inputs.input_ids, max_length=30)
        >>> tokenizer.batch_decode(generate_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]
        "Hey, are you conscious? Can you talk to me?\\nI'm not conscious, but I can talk to you."
        ```"""
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_router_logits = output_router_logits if output_router_logits is not None else self.config.output_router_logits
        output_hidden_states = output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        return_dict = return_dict if return_dict is not None else self.config.use_return_dict
        outputs = self.model(input_ids=input_ids, attention_mask=attention_mask, position_ids=position_ids, past_key_values=past_key_values, inputs_embeds=inputs_embeds, use_cache=use_cache, output_attentions=output_attentions, output_hidden_states=output_hidden_states, output_router_logits=output_router_logits, return_dict=return_dict)
        hidden_states = outputs[0]
        logits = self.lm_head(hidden_states)
        logits = logits.float()
        loss = None
        if labels is not None:
            shift_logits = logits[..., :-1, :].contiguous()
            shift_labels = labels[..., 1:].contiguous()
            loss_fct = CrossEntropyLoss()
            shift_logits = shift_logits.view(-1, self.config.vocab_size)
            shift_labels = shift_labels.view(-1)
            shift_labels = shift_labels.to(shift_logits.device)
            loss = loss_fct(shift_logits, shift_labels)
        aux_loss = None
        if output_router_logits:
            aux_loss = load_balancing_loss_func(outputs.router_logits if return_dict else outputs[-1], self.num_experts, self.num_experts_per_tok, attention_mask)
            if labels is not None:
                loss += self.router_aux_loss_coef * aux_loss.to(loss.device)
        if not return_dict:
            output = (logits,) + outputs[1:]
            if output_router_logits:
                output = (aux_loss,) + output
            return (loss,) + output if loss is not None else output
        torch.cuda.empty_cache()
        return MoeCausalLMOutputWithPast(loss=loss, aux_loss=aux_loss, logits=logits, past_key_values=outputs.past_key_values, hidden_states=outputs.hidden_states, attentions=outputs.attentions, router_logits=outputs.router_logits)

    def prepare_inputs_for_generation(self, input_ids, past_key_values=None, attention_mask=None, inputs_embeds=None, **kwargs):
        if past_key_values:
            input_ids = input_ids[:, -1:]
        if inputs_embeds is not None and past_key_values is None:
            model_inputs = {'inputs_embeds': inputs_embeds}
        else:
            model_inputs = {'input_ids': input_ids}
        model_inputs.update({'past_key_values': past_key_values, 'use_cache': kwargs.get('use_cache'), 'attention_mask': attention_mask})
        return model_inputs

    @staticmethod
    def _reorder_cache(past_key_values, beam_idx):
        reordered_past = ()
        for layer_past in past_key_values:
            reordered_past += (tuple((past_state.index_select(0, beam_idx.to(past_state.device)) for past_state in layer_past)),)
        return reordered_past

def __init__(self, config):
    super().__init__(config)
    self.model = MiniMaxM1Model(config)
    self.vocab_size = config.vocab_size
    self.lm_head = nn.Linear(config.hidden_size, config.vocab_size, bias=False)
    self.router_aux_loss_coef = config.router_aux_loss_coef
    self.num_experts = config.num_local_experts
    self.num_experts_per_tok = config.num_experts_per_tok
    self.post_init()

@add_start_docstrings('\n    The MiniMaxM1 Model transformer with a sequence classification head on top (linear layer).\n\n    [`MiniMaxM1ForSequenceClassification`] uses the last token in order to do the classification, as other causal models\n    (e.g. GPT-2) do.\n\n    Since it does classification on the last token, it requires to know the position of the last token. If a\n    `pad_token_id` is defined in the configuration, it finds the last token that is not a padding token in each row. If\n    no `pad_token_id` is defined, it simply takes the last value in each row of the batch. Since it cannot guess the\n    padding tokens when `inputs_embeds` are passed instead of `input_ids`, it does the same (take the last value in\n    each row of the batch).\n    ', MIXTRAL_START_DOCSTRING)
class MiniMaxM1ForSequenceClassification(MiniMaxM1PreTrainedModel):

    def __init__(self, config):
        super().__init__(config)
        self.num_labels = config.num_labels
        self.model = MiniMaxM1Model(config)
        self.score = nn.Linear(config.hidden_size, self.num_labels, bias=False)
        self.post_init()

    def get_input_embeddings(self):
        return self.model.embed_tokens

    def set_input_embeddings(self, value):
        self.model.embed_tokens = value

    @add_start_docstrings_to_model_forward(MIXTRAL_INPUTS_DOCSTRING)
    def forward(self, input_ids: torch.LongTensor=None, attention_mask: Optional[torch.Tensor]=None, position_ids: Optional[torch.LongTensor]=None, past_key_values: Optional[Union[Cache, List[torch.FloatTensor]]]=None, inputs_embeds: Optional[torch.FloatTensor]=None, labels: Optional[torch.LongTensor]=None, use_cache: Optional[bool]=None, output_attentions: Optional[bool]=None, output_hidden_states: Optional[bool]=None, return_dict: Optional[bool]=None) -> Union[Tuple, SequenceClassifierOutputWithPast]:
        """
        labels (`torch.LongTensor` of shape `(batch_size,)`, *optional*):
            Labels for computing the sequence classification/regression loss. Indices should be in `[0, ...,
            config.num_labels - 1]`. If `config.num_labels == 1` a regression loss is computed (Mean-Square loss), If
            `config.num_labels > 1` a classification loss is computed (Cross-Entropy).
        """
        return_dict = return_dict if return_dict is not None else self.config.use_return_dict
        transformer_outputs = self.model(input_ids, attention_mask=attention_mask, position_ids=position_ids, past_key_values=past_key_values, inputs_embeds=inputs_embeds, use_cache=use_cache, output_attentions=output_attentions, output_hidden_states=output_hidden_states, return_dict=return_dict)
        hidden_states = transformer_outputs[0]
        logits = self.score(hidden_states)
        if input_ids is not None:
            batch_size = input_ids.shape[0]
        else:
            batch_size = inputs_embeds.shape[0]
        if self.config.pad_token_id is None and batch_size != 1:
            raise ValueError('Cannot handle batch sizes > 1 if no padding token is defined.')
        if self.config.pad_token_id is None:
            sequence_lengths = -1
        elif input_ids is not None:
            sequence_lengths = torch.eq(input_ids, self.config.pad_token_id).int().argmax(-1) - 1
            sequence_lengths = sequence_lengths % input_ids.shape[-1]
            sequence_lengths = sequence_lengths.to(logits.device)
        else:
            sequence_lengths = -1
        pooled_logits = logits[torch.arange(batch_size, device=logits.device), sequence_lengths]
        loss = None
        if labels is not None:
            labels = labels.to(logits.device)
            if self.config.problem_type is None:
                if self.num_labels == 1:
                    self.config.problem_type = 'regression'
                elif self.num_labels > 1 and (labels.dtype == torch.long or labels.dtype == torch.int):
                    self.config.problem_type = 'single_label_classification'
                else:
                    self.config.problem_type = 'multi_label_classification'
            if self.config.problem_type == 'regression':
                loss_fct = MSELoss()
                if self.num_labels == 1:
                    loss = loss_fct(pooled_logits.squeeze(), labels.squeeze())
                else:
                    loss = loss_fct(pooled_logits, labels)
            elif self.config.problem_type == 'single_label_classification':
                loss_fct = CrossEntropyLoss()
                loss = loss_fct(pooled_logits.view(-1, self.num_labels), labels.view(-1))
            elif self.config.problem_type == 'multi_label_classification':
                loss_fct = BCEWithLogitsLoss()
                loss = loss_fct(pooled_logits, labels)
        if not return_dict:
            output = (pooled_logits,) + transformer_outputs[1:]
            return (loss,) + output if loss is not None else output
        return SequenceClassifierOutputWithPast(loss=loss, logits=pooled_logits, past_key_values=transformer_outputs.past_key_values, hidden_states=transformer_outputs.hidden_states, attentions=transformer_outputs.attentions)

def __init__(self, config):
    super().__init__(config)
    self.num_labels = config.num_labels
    self.model = MiniMaxM1Model(config)
    self.score = nn.Linear(config.hidden_size, self.num_labels, bias=False)
    self.post_init()

class MiniMaxM1Config(PretrainedConfig):
    """
    This is the configuration class to store the configuration of a [`MiniMaxM1Model`]. It is used to instantiate an
    MiniMaxM1 model according to the specified arguments, defining the model architecture. Instantiating a configuration
    with the defaults will yield a similar configuration to that of the MiniMaxM1.

    Configuration objects inherit from [`PretrainedConfig`] and can be used to control the model outputs. Read the
    documentation from [`PretrainedConfig`] for more information.


    Args:
        vocab_size (`int`, *optional*, defaults to 32000):
            Vocabulary size of the MiniMaxM1 model. Defines the number of different tokens that can be represented by the
            `inputs_ids` passed when calling [`MiniMaxM1Model`]
        hidden_size (`int`, *optional*, defaults to 4096):
            Dimension of the hidden representations.
        intermediate_size (`int`, *optional*, defaults to 14336):
            Dimension of the MLP representations.
        num_hidden_layers (`int`, *optional*, defaults to 32):
            Number of hidden layers in the Transformer encoder.
        num_attention_heads (`int`, *optional*, defaults to 32):
            Number of attention heads for each attention layer in the Transformer encoder.
        num_key_value_heads (`int`, *optional*, defaults to 8):
            This is the number of key_value heads that should be used to implement Grouped Query Attention. If
            `num_key_value_heads=num_attention_heads`, the model will use Multi Head Attention (MHA), if
            `num_key_value_heads=1 the model will use Multi Query Attention (MQA) otherwise GQA is used. When
            converting a multi-head checkpoint to a GQA checkpoint, each group key and value head should be constructed
            by meanpooling all the original heads within that group. For more details checkout [this
            paper](https://arxiv.org/pdf/2305.13245.pdf). If it is not specified, will default to `8`.
        hidden_act (`str` or `function`, *optional*, defaults to `"silu"`):
            The non-linear activation function (function or string) in the decoder.
        max_position_embeddings (`int`, *optional*, defaults to `4096*32`):
            The maximum sequence length that this model might ever be used with. MiniMaxM1's sliding window attention
            allows sequence of up to 4096*32 tokens.
        initializer_range (`float`, *optional*, defaults to 0.02):
            The standard deviation of the truncated_normal_initializer for initializing all weight matrices.
        rms_norm_eps (`float`, *optional*, defaults to 1e-05):
            The epsilon used by the rms normalization layers.
        use_cache (`bool`, *optional*, defaults to `True`):
            Whether or not the model should return the last key/values attentions (not used by all models). Only
            relevant if `config.is_decoder=True`.
        pad_token_id (`int`, *optional*):
            The id of the padding token.
        bos_token_id (`int`, *optional*, defaults to 1):
            The id of the "beginning-of-sequence" token.
        eos_token_id (`int`, *optional*, defaults to 2):
            The id of the "end-of-sequence" token.
        tie_word_embeddings (`bool`, *optional*, defaults to `False`):
            Whether the model's input and output word embeddings should be tied.
        rope_theta (`float`, *optional*, defaults to 1000000.0):
            The base period of the RoPE embeddings.
        sliding_window (`int`, *optional*):
            Sliding window attention window size. If not specified, will default to `4096`.
        attention_dropout (`float`, *optional*, defaults to 0.0):
            The dropout ratio for the attention probabilities.
        num_experts_per_tok (`int`, *optional*, defaults to 2):
            The number of experts to route per-token, can be also interpreted as the `top-k` routing
            parameter
        num_local_experts (`int`, *optional*, defaults to 8):
            Number of experts per Sparse MLP layer.
        output_router_logits (`bool`, *optional*, defaults to `False`):
            Whether or not the router logits should be returned by the model. Enabeling this will also
            allow the model to output the auxiliary loss. See [here]() for more details
        router_aux_loss_coef (`float`, *optional*, defaults to 0.001):
            The aux loss factor for the total loss.
        router_jitter_noise (`float`, *optional*, defaults to 0.0):
            Amount of noise to add to the router.

    ```python
    >>> from transformers import MiniMaxM1Model, MiniMaxM1Config

    >>> # Initializing a MiniMaxM1 style configuration
    >>> configuration = MiniMaxM1Config()

    >>> # Initializing a model from the MiniMaxM1 style configuration
    >>> model = MiniMaxM1Model(configuration)

    >>> # Accessing the model configuration
    >>> configuration = model.config
    ```"""
    model_type = 'MiniMaxM1'
    keys_to_ignore_at_inference = ['past_key_values']

    def __init__(self, vocab_size=32000, hidden_size=4096, intermediate_size=14336, num_hidden_layers=32, num_attention_heads=32, num_key_value_heads=8, hidden_act='silu', max_position_embeddings=4096 * 32, initializer_range=0.02, rms_norm_eps=1e-05, use_cache=True, pad_token_id=None, bos_token_id=None, eos_token_id=None, tie_word_embeddings=False, rope_theta=1000000.0, sliding_window=None, attention_dropout=0.0, num_experts_per_tok=2, num_local_experts=8, output_router_logits=False, router_aux_loss_coef=0.001, router_jitter_noise=0.0, **kwargs):
        self.vocab_size = vocab_size
        self.max_position_embeddings = max_position_embeddings
        self.hidden_size = hidden_size
        self.intermediate_size = intermediate_size
        self.num_hidden_layers = num_hidden_layers
        self.num_attention_heads = num_attention_heads
        self.sliding_window = sliding_window
        if num_key_value_heads is None:
            num_key_value_heads = num_attention_heads
        self.num_key_value_heads = num_key_value_heads
        self.hidden_act = hidden_act
        self.initializer_range = initializer_range
        self.rms_norm_eps = rms_norm_eps
        self.use_cache = use_cache
        self.rope_theta = rope_theta
        self.attention_dropout = attention_dropout
        self.num_experts_per_tok = num_experts_per_tok
        self.num_local_experts = num_local_experts
        self.output_router_logits = output_router_logits
        self.router_aux_loss_coef = router_aux_loss_coef
        self.router_jitter_noise = router_jitter_noise
        super().__init__(pad_token_id=pad_token_id, bos_token_id=bos_token_id, eos_token_id=eos_token_id, tie_word_embeddings=tie_word_embeddings, **kwargs)

def __init__(self, vocab_size=32000, hidden_size=4096, intermediate_size=14336, num_hidden_layers=32, num_attention_heads=32, num_key_value_heads=8, hidden_act='silu', max_position_embeddings=4096 * 32, initializer_range=0.02, rms_norm_eps=1e-05, use_cache=True, pad_token_id=None, bos_token_id=None, eos_token_id=None, tie_word_embeddings=False, rope_theta=1000000.0, sliding_window=None, attention_dropout=0.0, num_experts_per_tok=2, num_local_experts=8, output_router_logits=False, router_aux_loss_coef=0.001, router_jitter_noise=0.0, **kwargs):
    self.vocab_size = vocab_size
    self.max_position_embeddings = max_position_embeddings
    self.hidden_size = hidden_size
    self.intermediate_size = intermediate_size
    self.num_hidden_layers = num_hidden_layers
    self.num_attention_heads = num_attention_heads
    self.sliding_window = sliding_window
    if num_key_value_heads is None:
        num_key_value_heads = num_attention_heads
    self.num_key_value_heads = num_key_value_heads
    self.hidden_act = hidden_act
    self.initializer_range = initializer_range
    self.rms_norm_eps = rms_norm_eps
    self.use_cache = use_cache
    self.rope_theta = rope_theta
    self.attention_dropout = attention_dropout
    self.num_experts_per_tok = num_experts_per_tok
    self.num_local_experts = num_local_experts
    self.output_router_logits = output_router_logits
    self.router_aux_loss_coef = router_aux_loss_coef
    self.router_jitter_noise = router_jitter_noise
    super().__init__(pad_token_id=pad_token_id, bos_token_id=bos_token_id, eos_token_id=eos_token_id, tie_word_embeddings=tie_word_embeddings, **kwargs)

