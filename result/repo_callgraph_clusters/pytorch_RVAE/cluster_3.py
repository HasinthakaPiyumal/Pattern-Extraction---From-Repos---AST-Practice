# Cluster 3

class Embedding(nn.Module):

    def __init__(self, params, path='../../../'):
        super(Embedding, self).__init__()
        self.params = params
        word_embed = np.load(path + 'data/word_embeddings.npy')
        self.word_embed = nn.Embedding(self.params.word_vocab_size, self.params.word_embed_size)
        self.char_embed = nn.Embedding(self.params.char_vocab_size, self.params.char_embed_size)
        self.word_embed.weight = Parameter(t.from_numpy(word_embed).float(), requires_grad=False)
        self.char_embed.weight = Parameter(t.Tensor(self.params.char_vocab_size, self.params.char_embed_size).uniform_(-1, 1))
        self.TDNN = TDNN(self.params)

    def forward(self, word_input, character_input):
        """
        :param word_input: [batch_size, seq_len] tensor of Long type
        :param character_input: [batch_size, seq_len, max_word_len] tensor of Long type
        :return: input embedding with shape of [batch_size, seq_len, word_embed_size + sum_depth]
        """
        assert word_input.size()[:2] == character_input.size()[:2], 'Word input and character input must have the same sizes, but {} and {} found'.format(word_input.size(), character_input.size())
        [batch_size, seq_len] = word_input.size()
        word_input = self.word_embed(word_input)
        character_input = character_input.view(-1, self.params.max_word_len)
        character_input = self.char_embed(character_input)
        character_input = character_input.view(batch_size, seq_len, self.params.max_word_len, self.params.char_embed_size)
        character_input = self.TDNN(character_input)
        result = t.cat([word_input, character_input], 2)
        return result

def forward(self, word_input, character_input):
    """
        :param word_input: [batch_size, seq_len] tensor of Long type
        :param character_input: [batch_size, seq_len, max_word_len] tensor of Long type
        :return: input embedding with shape of [batch_size, seq_len, word_embed_size + sum_depth]
        """
    assert word_input.size()[:2] == character_input.size()[:2], 'Word input and character input must have the same sizes, but {} and {} found'.format(word_input.size(), character_input.size())
    [batch_size, seq_len] = word_input.size()
    word_input = self.word_embed(word_input)
    character_input = character_input.view(-1, self.params.max_word_len)
    character_input = self.char_embed(character_input)
    character_input = character_input.view(batch_size, seq_len, self.params.max_word_len, self.params.char_embed_size)
    character_input = self.TDNN(character_input)
    result = t.cat([word_input, character_input], 2)
    return result

class TDNN(nn.Module):

    def __init__(self, params):
        super(TDNN, self).__init__()
        self.params = params
        self.kernels = [Parameter(t.Tensor(out_dim, self.params.char_embed_size, kW).uniform_(-1, 1)) for kW, out_dim in params.kernels]
        self._add_to_parameters(self.kernels, 'TDNN_kernel')

    def forward(self, x):
        """
        :param x: tensor with shape [batch_size, max_seq_len, max_word_len, char_embed_size]

        :return: tensor with shape [batch_size, max_seq_len, depth_sum]

        applies multikenrel 1d-conv layer along every word in input with max-over-time pooling
            to emit fixed-size output
        """
        input_size = x.size()
        input_size_len = len(input_size)
        assert input_size_len == 4, 'Wrong input rang, must be equal to 4, but {} found'.format(input_size_len)
        [batch_size, seq_len, _, embed_size] = input_size
        assert embed_size == self.params.char_embed_size, 'Wrong embedding size, must be equal to {}, but {} found'.format(self.params.char_embed_size, embed_size)
        x = x.view(-1, self.params.max_word_len, self.params.char_embed_size).transpose(1, 2).contiguous()
        xs = [F.tanh(F.conv1d(x, kernel)) for kernel in self.kernels]
        xs = [x.max(2)[0].squeeze(2) for x in xs]
        x = t.cat(xs, 1)
        x = x.view(batch_size, seq_len, -1)
        return x

    def _add_to_parameters(self, parameters, name):
        for i, parameter in enumerate(parameters):
            self.register_parameter(name='{}-{}'.format(name, i), param=parameter)

def forward(self, x):
    """
        :param x: tensor with shape [batch_size, max_seq_len, max_word_len, char_embed_size]

        :return: tensor with shape [batch_size, max_seq_len, depth_sum]

        applies multikenrel 1d-conv layer along every word in input with max-over-time pooling
            to emit fixed-size output
        """
    input_size = x.size()
    input_size_len = len(input_size)
    assert input_size_len == 4, 'Wrong input rang, must be equal to 4, but {} found'.format(input_size_len)
    [batch_size, seq_len, _, embed_size] = input_size
    assert embed_size == self.params.char_embed_size, 'Wrong embedding size, must be equal to {}, but {} found'.format(self.params.char_embed_size, embed_size)
    x = x.view(-1, self.params.max_word_len, self.params.char_embed_size).transpose(1, 2).contiguous()
    xs = [F.tanh(F.conv1d(x, kernel)) for kernel in self.kernels]
    xs = [x.max(2)[0].squeeze(2) for x in xs]
    x = t.cat(xs, 1)
    x = x.view(batch_size, seq_len, -1)
    return x

def kld_coef(i):
    import math
    return (math.tanh((i - 3500) / 1000) + 1) / 2

class Decoder(nn.Module):

    def __init__(self, params):
        super(Decoder, self).__init__()
        self.params = params
        self.rnn = nn.LSTM(input_size=self.params.latent_variable_size + self.params.word_embed_size, hidden_size=self.params.decoder_rnn_size, num_layers=self.params.decoder_num_layers, batch_first=True)
        self.fc = nn.Linear(self.params.decoder_rnn_size, self.params.word_vocab_size)

    def forward(self, decoder_input, z, drop_prob, initial_state=None):
        """
        :param decoder_input: tensor with shape of [batch_size, seq_len, embed_size]
        :param z: sequence context with shape of [batch_size, latent_variable_size]
        :param drop_prob: probability of an element of decoder input to be zeroed in sense of dropout
        :param initial_state: initial state of decoder rnn

        :return: unnormalized logits of sentense words distribution probabilities
                    with shape of [batch_size, seq_len, word_vocab_size]
                 final rnn state with shape of [num_layers, batch_size, decoder_rnn_size]
        """
        assert parameters_allocation_check(self), 'Invalid CUDA options. Parameters should be allocated in the same memory'
        [batch_size, seq_len, _] = decoder_input.size()
        '\n            decoder rnn is conditioned on context via additional bias = W_cond * z to every input token\n        '
        decoder_input = F.dropout(decoder_input, drop_prob)
        z = t.cat([z] * seq_len, 1).view(batch_size, seq_len, self.params.latent_variable_size)
        decoder_input = t.cat([decoder_input, z], 2)
        rnn_out, final_state = self.rnn(decoder_input, initial_state)
        rnn_out = rnn_out.contiguous().view(-1, self.params.decoder_rnn_size)
        result = self.fc(rnn_out)
        result = result.view(batch_size, seq_len, self.params.word_vocab_size)
        return (result, final_state)

def forward(self, decoder_input, z, drop_prob, initial_state=None):
    """
        :param decoder_input: tensor with shape of [batch_size, seq_len, embed_size]
        :param z: sequence context with shape of [batch_size, latent_variable_size]
        :param drop_prob: probability of an element of decoder input to be zeroed in sense of dropout
        :param initial_state: initial state of decoder rnn

        :return: unnormalized logits of sentense words distribution probabilities
                    with shape of [batch_size, seq_len, word_vocab_size]
                 final rnn state with shape of [num_layers, batch_size, decoder_rnn_size]
        """
    assert parameters_allocation_check(self), 'Invalid CUDA options. Parameters should be allocated in the same memory'
    [batch_size, seq_len, _] = decoder_input.size()
    '\n            decoder rnn is conditioned on context via additional bias = W_cond * z to every input token\n        '
    decoder_input = F.dropout(decoder_input, drop_prob)
    z = t.cat([z] * seq_len, 1).view(batch_size, seq_len, self.params.latent_variable_size)
    decoder_input = t.cat([decoder_input, z], 2)
    rnn_out, final_state = self.rnn(decoder_input, initial_state)
    rnn_out = rnn_out.contiguous().view(-1, self.params.decoder_rnn_size)
    result = self.fc(rnn_out)
    result = result.view(batch_size, seq_len, self.params.word_vocab_size)
    return (result, final_state)

class Encoder(nn.Module):

    def __init__(self, params):
        super(Encoder, self).__init__()
        self.params = params
        self.hw1 = Highway(self.params.sum_depth + self.params.word_embed_size, 2, F.relu)
        self.rnn = nn.LSTM(input_size=self.params.word_embed_size + self.params.sum_depth, hidden_size=self.params.encoder_rnn_size, num_layers=self.params.encoder_num_layers, batch_first=True, bidirectional=True)

    def forward(self, input):
        """
        :param input: [batch_size, seq_len, embed_size] tensor
        :return: context of input sentenses with shape of [batch_size, latent_variable_size]
        """
        [batch_size, seq_len, embed_size] = input.size()
        input = input.view(-1, embed_size)
        input = self.hw1(input)
        input = input.view(batch_size, seq_len, embed_size)
        assert parameters_allocation_check(self), 'Invalid CUDA options. Parameters should be allocated in the same memory'
        ' Unfold rnn with zero initial state and get its final state from the last layer\n        '
        _, (_, final_state) = self.rnn(input)
        final_state = final_state.view(self.params.encoder_num_layers, 2, batch_size, self.params.encoder_rnn_size)
        final_state = final_state[-1]
        h_1, h_2 = (final_state[0], final_state[1])
        final_state = t.cat([h_1, h_2], 1)
        return final_state

def forward(self, input):
    """
        :param input: [batch_size, seq_len, embed_size] tensor
        :return: context of input sentenses with shape of [batch_size, latent_variable_size]
        """
    [batch_size, seq_len, embed_size] = input.size()
    input = input.view(-1, embed_size)
    input = self.hw1(input)
    input = input.view(batch_size, seq_len, embed_size)
    assert parameters_allocation_check(self), 'Invalid CUDA options. Parameters should be allocated in the same memory'
    ' Unfold rnn with zero initial state and get its final state from the last layer\n        '
    _, (_, final_state) = self.rnn(input)
    final_state = final_state.view(self.params.encoder_num_layers, 2, batch_size, self.params.encoder_rnn_size)
    final_state = final_state[-1]
    h_1, h_2 = (final_state[0], final_state[1])
    final_state = t.cat([h_1, h_2], 1)
    return final_state

