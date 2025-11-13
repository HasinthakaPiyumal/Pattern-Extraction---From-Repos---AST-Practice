# Cluster 6

def _get_unpad_data(attention_mask):
    seqlens_in_batch = attention_mask.sum(dim=-1, dtype=torch.int32)
    indices = torch.nonzero(attention_mask.flatten(), as_tuple=False).flatten()
    max_seqlen_in_batch = seqlens_in_batch.max().item()
    cu_seqlens = F.pad(torch.cumsum(seqlens_in_batch, dim=0, dtype=torch.int32), (1, 0))
    return (indices, cu_seqlens, max_seqlen_in_batch)

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

@staticmethod
def _reorder_cache(past_key_values, beam_idx):
    reordered_past = ()
    for layer_past in past_key_values:
        reordered_past += (tuple((past_state.index_select(0, beam_idx.to(past_state.device)) for past_state in layer_past)),)
    return reordered_past

