# Cluster 2

class NEG_loss(nn.Module):

    def __init__(self, num_classes, embed_size):
        """
        :param num_classes: An int. The number of possible classes.
        :param embed_size: An int. Embedding size
        """
        super(NEG_loss, self).__init__()
        self.num_classes = num_classes
        self.embed_size = embed_size
        self.out_embed = nn.Embedding(self.num_classes, self.embed_size)
        self.out_embed.weight = Parameter(t.FloatTensor(self.num_classes, self.embed_size).uniform_(-1, 1))
        self.in_embed = nn.Embedding(self.num_classes, self.embed_size)
        self.in_embed.weight = Parameter(t.FloatTensor(self.num_classes, self.embed_size).uniform_(-1, 1))

    def forward(self, input_labes, out_labels, num_sampled):
        """
        :param input_labes: Tensor with shape of [batch_size] of Long type
        :param out_labels: Tensor with shape of [batch_size] of Long type
        :param num_sampled: An int. The number of sampled from noise examples

        :return: Loss estimation with shape of [batch_size]
            loss defined in Mikolov et al. Distributed Representations of Words and Phrases and their Compositionality
            papers.nips.cc/paper/5021-distributed-representations-of-words-and-phrases-and-their-compositionality.pdf
        """
        assert parameters_allocation_check(self), '\n            Invalid CUDA options. out_embed and in_embed parameters both should be stored in the same memory\n            got out_embed.is_cuda = {}, in_embed.is_cuda = {}\n            '.format(self.out_embed.weight.is_cuda, self.in_embed.weight.is_cuda)
        use_cuda = self.out_embed.weight.is_cuda
        [batch_size] = input_labes.size()
        input = self.in_embed(input_labes)
        output = self.out_embed(out_labels)
        noise = Variable(t.Tensor(batch_size, num_sampled).uniform_(0, self.num_classes - 1).long())
        if use_cuda:
            noise = noise.cuda()
        noise = self.out_embed(noise).neg()
        log_target = (input * output).sum(1).squeeze().sigmoid().log()
        ' ∑[batch_size, num_sampled, embed_size] * [batch_size, embed_size, 1] ->\n            ∑[batch_size, num_sampled] -> [batch_size] '
        sum_log_sampled = t.bmm(noise, input.unsqueeze(2)).sigmoid().log().sum(1).squeeze()
        loss = log_target + sum_log_sampled
        return -loss

    def input_embeddings(self):
        return self.in_embed.weight.data.cpu().numpy()

def input_embeddings(self):
    return self.in_embed.weight.data.cpu().numpy()

def handle_inputs(inputs, use_cuda):
    import torch as t
    from torch.autograd import Variable
    result = [Variable(t.from_numpy(var)) for var in inputs]
    result = [var.cuda() if use_cuda else var for var in result]
    return result

class RVAE(nn.Module):

    def __init__(self, params):
        super(RVAE, self).__init__()
        self.params = params
        self.embedding = Embedding(self.params, '')
        self.encoder = Encoder(self.params)
        self.context_to_mu = nn.Linear(self.params.encoder_rnn_size * 2, self.params.latent_variable_size)
        self.context_to_logvar = nn.Linear(self.params.encoder_rnn_size * 2, self.params.latent_variable_size)
        self.decoder = Decoder(self.params)

    def forward(self, drop_prob, encoder_word_input=None, encoder_character_input=None, decoder_word_input=None, decoder_character_input=None, z=None, initial_state=None):
        """
        :param encoder_word_input: An tensor with shape of [batch_size, seq_len] of Long type
        :param encoder_character_input: An tensor with shape of [batch_size, seq_len, max_word_len] of Long type
        :param decoder_word_input: An tensor with shape of [batch_size, max_seq_len + 1] of Long type
        :param initial_state: initial state of decoder rnn in order to perform sampling

        :param drop_prob: probability of an element of decoder input to be zeroed in sense of dropout

        :param z: context if sampling is performing

        :return: unnormalized logits of sentence words distribution probabilities
                    with shape of [batch_size, seq_len, word_vocab_size]
                 final rnn state with shape of [num_layers, batch_size, decoder_rnn_size]
        """
        assert parameters_allocation_check(self), 'Invalid CUDA options. Parameters should be allocated in the same memory'
        use_cuda = self.embedding.word_embed.weight.is_cuda
        assert z is None and fold(lambda acc, parameter: acc and parameter is not None, [encoder_word_input, encoder_character_input, decoder_word_input], True) or (z is not None and decoder_word_input is not None), 'Invalid input. If z is None then encoder and decoder inputs should be passed as arguments'
        if z is None:
            ' Get context from encoder and sample z ~ N(mu, std)\n            '
            [batch_size, _] = encoder_word_input.size()
            encoder_input = self.embedding(encoder_word_input, encoder_character_input)
            context = self.encoder(encoder_input)
            mu = self.context_to_mu(context)
            logvar = self.context_to_logvar(context)
            std = t.exp(0.5 * logvar)
            z = Variable(t.randn([batch_size, self.params.latent_variable_size]))
            if use_cuda:
                z = z.cuda()
            z = z * std + mu
            kld = (-0.5 * t.sum(logvar - t.pow(mu, 2) - t.exp(logvar) + 1, 1)).mean().squeeze()
        else:
            kld = None
        decoder_input = self.embedding.word_embed(decoder_word_input)
        out, final_state = self.decoder(decoder_input, z, drop_prob, initial_state)
        return (out, final_state, kld)

    def learnable_parameters(self):
        return [p for p in self.parameters() if p.requires_grad]

    def trainer(self, optimizer, batch_loader):

        def train(i, batch_size, use_cuda, dropout):
            input = batch_loader.next_batch(batch_size, 'train')
            input = [Variable(t.from_numpy(var)) for var in input]
            input = [var.long() for var in input]
            input = [var.cuda() if use_cuda else var for var in input]
            [encoder_word_input, encoder_character_input, decoder_word_input, decoder_character_input, target] = input
            logits, _, kld = self(dropout, encoder_word_input, encoder_character_input, decoder_word_input, decoder_character_input, z=None)
            logits = logits.view(-1, self.params.word_vocab_size)
            target = target.view(-1)
            cross_entropy = F.cross_entropy(logits, target)
            loss = 79 * cross_entropy + kld_coef(i) * kld
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            return (cross_entropy, kld, kld_coef(i))
        return train

    def validater(self, batch_loader):

        def validate(batch_size, use_cuda):
            input = batch_loader.next_batch(batch_size, 'valid')
            input = [Variable(t.from_numpy(var)) for var in input]
            input = [var.long() for var in input]
            input = [var.cuda() if use_cuda else var for var in input]
            [encoder_word_input, encoder_character_input, decoder_word_input, decoder_character_input, target] = input
            logits, _, kld = self(0.0, encoder_word_input, encoder_character_input, decoder_word_input, decoder_character_input, z=None)
            logits = logits.view(-1, self.params.word_vocab_size)
            target = target.view(-1)
            cross_entropy = F.cross_entropy(logits, target)
            return (cross_entropy, kld)
        return validate

    def sample(self, batch_loader, seq_len, seed, use_cuda):
        seed = Variable(t.from_numpy(seed).float())
        if use_cuda:
            seed = seed.cuda()
        decoder_word_input_np, decoder_character_input_np = batch_loader.go_input(1)
        decoder_word_input = Variable(t.from_numpy(decoder_word_input_np).long())
        decoder_character_input = Variable(t.from_numpy(decoder_character_input_np).long())
        if use_cuda:
            decoder_word_input, decoder_character_input = (decoder_word_input.cuda(), decoder_character_input.cuda())
        result = ''
        initial_state = None
        for i in range(seq_len):
            logits, initial_state, _ = self(0.0, None, None, decoder_word_input, decoder_character_input, seed, initial_state)
            logits = logits.view(-1, self.params.word_vocab_size)
            prediction = F.softmax(logits)
            word = batch_loader.sample_word_from_distribution(prediction.data.cpu().numpy()[-1])
            if word == batch_loader.end_token:
                break
            result += ' ' + word
            decoder_word_input_np = np.array([[batch_loader.word_to_idx[word]]])
            decoder_character_input_np = np.array([[batch_loader.encode_characters(word)]])
            decoder_word_input = Variable(t.from_numpy(decoder_word_input_np).long())
            decoder_character_input = Variable(t.from_numpy(decoder_character_input_np).long())
            if use_cuda:
                decoder_word_input, decoder_character_input = (decoder_word_input.cuda(), decoder_character_input.cuda())
        return result

def train(i, batch_size, use_cuda, dropout):
    input = batch_loader.next_batch(batch_size, 'train')
    input = [Variable(t.from_numpy(var)) for var in input]
    input = [var.long() for var in input]
    input = [var.cuda() if use_cuda else var for var in input]
    [encoder_word_input, encoder_character_input, decoder_word_input, decoder_character_input, target] = input
    logits, _, kld = self(dropout, encoder_word_input, encoder_character_input, decoder_word_input, decoder_character_input, z=None)
    logits = logits.view(-1, self.params.word_vocab_size)
    target = target.view(-1)
    cross_entropy = F.cross_entropy(logits, target)
    loss = 79 * cross_entropy + kld_coef(i) * kld
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    return (cross_entropy, kld, kld_coef(i))

def validate(batch_size, use_cuda):
    input = batch_loader.next_batch(batch_size, 'valid')
    input = [Variable(t.from_numpy(var)) for var in input]
    input = [var.long() for var in input]
    input = [var.cuda() if use_cuda else var for var in input]
    [encoder_word_input, encoder_character_input, decoder_word_input, decoder_character_input, target] = input
    logits, _, kld = self(0.0, encoder_word_input, encoder_character_input, decoder_word_input, decoder_character_input, z=None)
    logits = logits.view(-1, self.params.word_vocab_size)
    target = target.view(-1)
    cross_entropy = F.cross_entropy(logits, target)
    return (cross_entropy, kld)

def sample(self, batch_loader, seq_len, seed, use_cuda):
    seed = Variable(t.from_numpy(seed).float())
    if use_cuda:
        seed = seed.cuda()
    decoder_word_input_np, decoder_character_input_np = batch_loader.go_input(1)
    decoder_word_input = Variable(t.from_numpy(decoder_word_input_np).long())
    decoder_character_input = Variable(t.from_numpy(decoder_character_input_np).long())
    if use_cuda:
        decoder_word_input, decoder_character_input = (decoder_word_input.cuda(), decoder_character_input.cuda())
    result = ''
    initial_state = None
    for i in range(seq_len):
        logits, initial_state, _ = self(0.0, None, None, decoder_word_input, decoder_character_input, seed, initial_state)
        logits = logits.view(-1, self.params.word_vocab_size)
        prediction = F.softmax(logits)
        word = batch_loader.sample_word_from_distribution(prediction.data.cpu().numpy()[-1])
        if word == batch_loader.end_token:
            break
        result += ' ' + word
        decoder_word_input_np = np.array([[batch_loader.word_to_idx[word]]])
        decoder_character_input_np = np.array([[batch_loader.encode_characters(word)]])
        decoder_word_input = Variable(t.from_numpy(decoder_word_input_np).long())
        decoder_character_input = Variable(t.from_numpy(decoder_character_input_np).long())
        if use_cuda:
            decoder_word_input, decoder_character_input = (decoder_word_input.cuda(), decoder_character_input.cuda())
    return result

