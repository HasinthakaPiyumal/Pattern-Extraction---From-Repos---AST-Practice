# Cluster 11

def bart_predict(input):
    input_ids = bart_tokenizer(input)['input_ids']
    input_ids = torch.tensor(input_ids).unsqueeze(0)
    output = bart_model.generate(input_ids, max_length=512, num_return_sequences=5, num_beams=5)
    return bart_tokenizer.batch_decode(output.tolist(), skip_special_tokens=True)[0]

def bart_predict(input, model, skip_special_tokens=True, **kwargs):
    input_ids = bart_tokenizer(input)['input_ids']
    input_ids = torch.tensor(input_ids).unsqueeze(0)
    output = model.generate(input_ids, max_length=512, **kwargs)
    return bart_tokenizer.batch_decode(output.tolist(), skip_special_tokens=skip_special_tokens)

class RCDQN(nn.Module):

    def __init__(self, vocab_size, embedding_dim, hidden_dim, arch, grad, embs=None, gru_embed='embedding', get_image=0, bert_path=''):
        super().__init__()
        self.word_dim = embedding_dim
        self.word_emb = nn.Embedding(vocab_size, embedding_dim)
        if embs is not None:
            print('Loading embeddings of shape {}'.format(embs.shape))
            self.word_emb.weight.data.copy_(torch.from_numpy(embs))
        self.hidden_dim = hidden_dim
        self.keep_prob = 1.0
        self.rnn = EncoderRNN(self.word_dim, self.hidden_dim, 1, concat=True, bidir=True, layernorm='None', return_last=False)
        self.att_1 = BiAttention(self.hidden_dim * 2, 1 - self.keep_prob)
        self.att_2 = BiAttention(self.hidden_dim * 2, 1 - self.keep_prob)
        self.att_3 = BiAttention(embedding_dim, 1 - self.keep_prob)
        self.linear_1 = nn.Sequential(nn.Linear(self.hidden_dim * 8, self.hidden_dim), nn.LeakyReLU())
        self.rnn_2 = EncoderRNN(self.hidden_dim, self.hidden_dim, 1, concat=True, bidir=True, layernorm='layer', return_last=False)
        self.linear_2 = nn.Sequential(nn.Linear(self.hidden_dim * 12, self.hidden_dim * 2), nn.LeakyReLU())
        self.linear_3 = nn.Sequential(nn.Linear(self.hidden_dim * 2, self.hidden_dim), nn.LeakyReLU(), nn.Linear(self.hidden_dim, 1))
        self.get_image = get_image
        if self.get_image:
            self.linear_image = nn.Linear(512, self.hidden_dim)

    def prepare(self, ids):
        """
        Prepare the input for the encoder. Pass it through pad, embedding, and rnn.
        """
        lens = [len(_) for _ in ids]
        ids = [torch.tensor(_) for _ in ids]
        ids = nn.utils.rnn.pad_sequence(ids, batch_first=True).cuda()
        mask = (ids > 0).float()
        embed = self.word_emb(ids)
        output = self.rnn(embed, lens)
        return (ids, lens, mask, embed, output)

    def forward(self, state_batch, act_batch, value=False, q=False, act=False):
        if self.arch == 'bert':
            return self.bert_forward(state_batch, act_batch, value, q, act)
        obs_ids, obs_lens, obs_mask, obs_embed, obs_output = self.prepare([state.obs for state in state_batch])
        goal_ids, goal_lens, goal_mask, goal_embed, goal_output = self.prepare([state.goal for state in state_batch])
        state_output = self.att_1(obs_output, goal_output, goal_mask)
        state_output = self.linear_1(state_output)
        if self.get_image:
            images = [state.image_feat for state in state_batch]
            images = [torch.zeros(512) if _ is None else _ for _ in images]
            images = torch.stack([_ for _ in images]).cuda()
            images = self.linear_image(images)
            state_output = torch.cat([images.unsqueeze(1), state_output], dim=1)
            obs_lens = [_ + 1 for _ in obs_lens]
            obs_mask = torch.cat([obs_mask[:, :1], obs_mask], dim=1)
        state_output = self.rnn_2(state_output, obs_lens)
        if value:
            values = get_aggregated(state_output, obs_lens, 'mean')
            values = self.linear_3(values).squeeze(1)
        act_sizes = [len(_) for _ in act_batch]
        act_batch = list(itertools.chain.from_iterable(act_batch))
        act_ids, act_lens, act_mask, act_embed, act_output = self.prepare(act_batch)
        state_output, state_mask, state_lens = duplicate(state_output, obs_mask, obs_lens, act_sizes)
        goal_embed, goal_mask, goal_lens = duplicate(goal_embed, goal_mask, goal_lens, act_sizes)
        state_act_output = self.att_2(act_output, state_output, state_mask)
        goal_act_output = self.att_3(act_embed, goal_embed, goal_mask)
        output = torch.cat([state_act_output, goal_act_output], dim=-1)
        output = get_aggregated(output, act_lens, 'mean')
        output = self.linear_2(output)
        act_values = self.linear_3(output).squeeze(1)
        if not q:
            act_values = torch.cat([F.log_softmax(_, dim=0) for _ in act_values.split(act_sizes)], dim=0)
        if value:
            return (act_values, act_sizes, values)
        else:
            return (act_values, act_sizes)

def prepare(self, ids):
    """
        Prepare the input for the encoder. Pass it through pad, embedding, and rnn.
        """
    lens = [len(_) for _ in ids]
    ids = [torch.tensor(_) for _ in ids]
    ids = nn.utils.rnn.pad_sequence(ids, batch_first=True).cuda()
    mask = (ids > 0).float()
    embed = self.word_emb(ids)
    output = self.rnn(embed, lens)
    return (ids, lens, mask, embed, output)

def forward(self, state_batch, act_batch, value=False, q=False, act=False):
    if self.arch == 'bert':
        return self.bert_forward(state_batch, act_batch, value, q, act)
    obs_ids, obs_lens, obs_mask, obs_embed, obs_output = self.prepare([state.obs for state in state_batch])
    goal_ids, goal_lens, goal_mask, goal_embed, goal_output = self.prepare([state.goal for state in state_batch])
    state_output = self.att_1(obs_output, goal_output, goal_mask)
    state_output = self.linear_1(state_output)
    if self.get_image:
        images = [state.image_feat for state in state_batch]
        images = [torch.zeros(512) if _ is None else _ for _ in images]
        images = torch.stack([_ for _ in images]).cuda()
        images = self.linear_image(images)
        state_output = torch.cat([images.unsqueeze(1), state_output], dim=1)
        obs_lens = [_ + 1 for _ in obs_lens]
        obs_mask = torch.cat([obs_mask[:, :1], obs_mask], dim=1)
    state_output = self.rnn_2(state_output, obs_lens)
    if value:
        values = get_aggregated(state_output, obs_lens, 'mean')
        values = self.linear_3(values).squeeze(1)
    act_sizes = [len(_) for _ in act_batch]
    act_batch = list(itertools.chain.from_iterable(act_batch))
    act_ids, act_lens, act_mask, act_embed, act_output = self.prepare(act_batch)
    state_output, state_mask, state_lens = duplicate(state_output, obs_mask, obs_lens, act_sizes)
    goal_embed, goal_mask, goal_lens = duplicate(goal_embed, goal_mask, goal_lens, act_sizes)
    state_act_output = self.att_2(act_output, state_output, state_mask)
    goal_act_output = self.att_3(act_embed, goal_embed, goal_mask)
    output = torch.cat([state_act_output, goal_act_output], dim=-1)
    output = get_aggregated(output, act_lens, 'mean')
    output = self.linear_2(output)
    act_values = self.linear_3(output).squeeze(1)
    if not q:
        act_values = torch.cat([F.log_softmax(_, dim=0) for _ in act_values.split(act_sizes)], dim=0)
    if value:
        return (act_values, act_sizes, values)
    else:
        return (act_values, act_sizes)

def duplicate(output, mask, lens, act_sizes):
    """
    Duplicate the output based on the action sizes.
    """
    output = torch.cat([output[i:i + 1].repeat(j, 1, 1) for i, j in enumerate(act_sizes)], dim=0)
    mask = torch.cat([mask[i:i + 1].repeat(j, 1) for i, j in enumerate(act_sizes)], dim=0)
    lens = list(itertools.chain.from_iterable([lens[i:i + 1] * j for i, j in enumerate(act_sizes)]))
    return (output, mask, lens)

def get_aggregated(output, lens, method):
    """
    Get the aggregated hidden state of the encoder.
    B x D
    """
    if method == 'mean':
        return torch.stack([output[i, :j, :].mean(0) for i, j in enumerate(lens)], dim=0)
    elif method == 'last':
        return torch.stack([output[i, j - 1, :] for i, j in enumerate(lens)], dim=0)
    elif method == 'first':
        return output[:, 0, :]

class BertModelForWebshop(PreTrainedModel):
    config_class = BertConfigForWebshop

    def __init__(self, config):
        super().__init__(config)
        bert_config = BertConfig.from_pretrained('bert-base-uncased')
        if config.pretrained_bert:
            self.bert = BertModel.from_pretrained('bert-base-uncased')
        else:
            self.bert = BertModel(config)
        self.bert.resize_token_embeddings(30526)
        self.attn = BiAttention(768, 0.0)
        self.linear_1 = nn.Linear(768 * 4, 768)
        self.relu = nn.ReLU()
        self.linear_2 = nn.Linear(768, 1)
        if config.image:
            self.image_linear = nn.Linear(512, 768)
        else:
            self.image_linear = None
        self.linear_3 = nn.Sequential(nn.Linear(768, 128), nn.LeakyReLU(), nn.Linear(128, 1))

    def forward(self, state_input_ids, state_attention_mask, action_input_ids, action_attention_mask, sizes, images=None, labels=None):
        sizes = sizes.tolist()
        state_rep = self.bert(state_input_ids, attention_mask=state_attention_mask)[0]
        if images is not None and self.image_linear is not None:
            images = self.image_linear(images)
            state_rep = torch.cat([images.unsqueeze(1), state_rep], dim=1)
            state_attention_mask = torch.cat([state_attention_mask[:, :1], state_attention_mask], dim=1)
        action_rep = self.bert(action_input_ids, attention_mask=action_attention_mask)[0]
        state_rep = torch.cat([state_rep[i:i + 1].repeat(j, 1, 1) for i, j in enumerate(sizes)], dim=0)
        state_attention_mask = torch.cat([state_attention_mask[i:i + 1].repeat(j, 1) for i, j in enumerate(sizes)], dim=0)
        act_lens = action_attention_mask.sum(1).tolist()
        state_action_rep = self.attn(action_rep, state_rep, state_attention_mask)
        state_action_rep = self.relu(self.linear_1(state_action_rep))
        act_values = get_aggregated(state_action_rep, act_lens, 'mean')
        act_values = self.linear_2(act_values).squeeze(1)
        logits = [F.log_softmax(_, dim=0) for _ in act_values.split(sizes)]
        loss = None
        if labels is not None:
            loss = -sum([logit[label] for logit, label in zip(logits, labels)]) / len(logits)
        return SequenceClassifierOutput(loss=loss, logits=logits)

    def rl_forward(self, state_batch, act_batch, value=False, q=False, act=False):
        act_values = []
        act_sizes = []
        values = []
        for state, valid_acts in zip(state_batch, act_batch):
            with torch.set_grad_enabled(not act):
                state_ids = torch.tensor([state.obs]).cuda()
                state_mask = (state_ids > 0).int()
                act_lens = [len(_) for _ in valid_acts]
                act_ids = [torch.tensor(_) for _ in valid_acts]
                act_ids = nn.utils.rnn.pad_sequence(act_ids, batch_first=True).cuda()
                act_mask = (act_ids > 0).int()
                act_size = torch.tensor([len(valid_acts)]).cuda()
                if self.image_linear is not None:
                    images = [state.image_feat]
                    images = [torch.zeros(512) if _ is None else _ for _ in images]
                    images = torch.stack(images).cuda()
                else:
                    images = None
                logits = self.forward(state_ids, state_mask, act_ids, act_mask, act_size, images=images).logits[0]
                act_values.append(logits)
                act_sizes.append(len(valid_acts))
            if value:
                v = self.bert(state_ids, state_mask)[0]
                values.append(self.linear_3(v[0][0]))
        act_values = torch.cat(act_values, dim=0)
        act_values = torch.cat([F.log_softmax(_, dim=0) for _ in act_values.split(act_sizes)], dim=0)
        if value:
            values = torch.cat(values, dim=0)
            return (act_values, act_sizes, values)
        else:
            return (act_values, act_sizes)

def forward(self, state_input_ids, state_attention_mask, action_input_ids, action_attention_mask, sizes, images=None, labels=None):
    sizes = sizes.tolist()
    state_rep = self.bert(state_input_ids, attention_mask=state_attention_mask)[0]
    if images is not None and self.image_linear is not None:
        images = self.image_linear(images)
        state_rep = torch.cat([images.unsqueeze(1), state_rep], dim=1)
        state_attention_mask = torch.cat([state_attention_mask[:, :1], state_attention_mask], dim=1)
    action_rep = self.bert(action_input_ids, attention_mask=action_attention_mask)[0]
    state_rep = torch.cat([state_rep[i:i + 1].repeat(j, 1, 1) for i, j in enumerate(sizes)], dim=0)
    state_attention_mask = torch.cat([state_attention_mask[i:i + 1].repeat(j, 1) for i, j in enumerate(sizes)], dim=0)
    act_lens = action_attention_mask.sum(1).tolist()
    state_action_rep = self.attn(action_rep, state_rep, state_attention_mask)
    state_action_rep = self.relu(self.linear_1(state_action_rep))
    act_values = get_aggregated(state_action_rep, act_lens, 'mean')
    act_values = self.linear_2(act_values).squeeze(1)
    logits = [F.log_softmax(_, dim=0) for _ in act_values.split(sizes)]
    loss = None
    if labels is not None:
        loss = -sum([logit[label] for logit, label in zip(logits, labels)]) / len(logits)
    return SequenceClassifierOutput(loss=loss, logits=logits)

def rl_forward(self, state_batch, act_batch, value=False, q=False, act=False):
    act_values = []
    act_sizes = []
    values = []
    for state, valid_acts in zip(state_batch, act_batch):
        with torch.set_grad_enabled(not act):
            state_ids = torch.tensor([state.obs]).cuda()
            state_mask = (state_ids > 0).int()
            act_lens = [len(_) for _ in valid_acts]
            act_ids = [torch.tensor(_) for _ in valid_acts]
            act_ids = nn.utils.rnn.pad_sequence(act_ids, batch_first=True).cuda()
            act_mask = (act_ids > 0).int()
            act_size = torch.tensor([len(valid_acts)]).cuda()
            if self.image_linear is not None:
                images = [state.image_feat]
                images = [torch.zeros(512) if _ is None else _ for _ in images]
                images = torch.stack(images).cuda()
            else:
                images = None
            logits = self.forward(state_ids, state_mask, act_ids, act_mask, act_size, images=images).logits[0]
            act_values.append(logits)
            act_sizes.append(len(valid_acts))
        if value:
            v = self.bert(state_ids, state_mask)[0]
            values.append(self.linear_3(v[0][0]))
    act_values = torch.cat(act_values, dim=0)
    act_values = torch.cat([F.log_softmax(_, dim=0) for _ in act_values.split(act_sizes)], dim=0)
    if value:
        values = torch.cat(values, dim=0)
        return (act_values, act_sizes, values)
    else:
        return (act_values, act_sizes)

