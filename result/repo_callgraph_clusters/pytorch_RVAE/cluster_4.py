# Cluster 4

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

def _add_to_parameters(self, parameters, name):
    for i, parameter in enumerate(parameters):
        self.register_parameter(name='{}-{}'.format(name, i), param=parameter)

class Highway(nn.Module):

    def __init__(self, size, num_layers, f):
        super(Highway, self).__init__()
        self.num_layers = num_layers
        self.nonlinear = [nn.Linear(size, size) for _ in range(num_layers)]
        for i, module in enumerate(self.nonlinear):
            self._add_to_parameters(module.parameters(), 'nonlinear_module_{}'.format(i))
        self.linear = [nn.Linear(size, size) for _ in range(num_layers)]
        for i, module in enumerate(self.linear):
            self._add_to_parameters(module.parameters(), 'linear_module_{}'.format(i))
        self.gate = [nn.Linear(size, size) for _ in range(num_layers)]
        for i, module in enumerate(self.gate):
            self._add_to_parameters(module.parameters(), 'gate_module_{}'.format(i))
        self.f = f

    def forward(self, x):
        """
        :param x: tensor with shape of [batch_size, size]

        :return: tensor with shape of [batch_size, size]

        applies σ(x) ⨀ (f(G(x))) + (1 - σ(x)) ⨀ (Q(x)) transformation | G and Q is affine transformation,
            f is non-linear transformation, σ(x) is affine transformation with sigmoid non-linearition
            and ⨀ is element-wise multiplication
        """
        for layer in range(self.num_layers):
            gate = F.sigmoid(self.gate[layer](x))
            nonlinear = self.f(self.nonlinear[layer](x))
            linear = self.linear[layer](x)
            x = gate * nonlinear + (1 - gate) * linear
        return x

    def _add_to_parameters(self, parameters, name):
        for i, parameter in enumerate(parameters):
            self.register_parameter(name='{}-{}'.format(name, i), param=parameter)

def __init__(self, size, num_layers, f):
    super(Highway, self).__init__()
    self.num_layers = num_layers
    self.nonlinear = [nn.Linear(size, size) for _ in range(num_layers)]
    for i, module in enumerate(self.nonlinear):
        self._add_to_parameters(module.parameters(), 'nonlinear_module_{}'.format(i))
    self.linear = [nn.Linear(size, size) for _ in range(num_layers)]
    for i, module in enumerate(self.linear):
        self._add_to_parameters(module.parameters(), 'linear_module_{}'.format(i))
    self.gate = [nn.Linear(size, size) for _ in range(num_layers)]
    for i, module in enumerate(self.gate):
        self._add_to_parameters(module.parameters(), 'gate_module_{}'.format(i))
    self.f = f

def _add_to_parameters(self, parameters, name):
    for i, parameter in enumerate(parameters):
        self.register_parameter(name='{}-{}'.format(name, i), param=parameter)

class BatchLoader:

    def __init__(self, path='../../'):
        """
            :properties

                data_files - array containing paths to data sources

                idx_files - array of paths to vocabulury files

                tensor_files - matrix with shape of [2, target_num] containing paths to files
                    with data represented as tensors
                    where first index in shape corresponds to types of representation of data,
                    i.e. word representation and character-aware representation

                blind_symbol - special symbol to fill spaces in every word in character-aware representation
                    to make all words be the same lenght
                pad_token - the same special symbol as blind_symbol, but in case of lines of words
                go_token - start of sequence symbol
                end_token - end of sequence symbol

                chars_vocab_size - number of unique characters
                idx_to_char - array of shape [chars_vocab_size] containing ordered list of inique characters
                char_to_idx - dictionary of shape [chars_vocab_size]
                    such that idx_to_char[char_to_idx[some_char]] = some_char
                    where some_char is such that idx_to_char contains it

                words_vocab_size, idx_to_word, word_to_idx - same as for characters

                max_word_len - maximum word length
                max_seq_len - maximum sequence length
                num_lines - num of lines in data with shape [target_num]

                word_tensor -  tensor of shape [target_num, num_lines, line_lenght] c
                    ontains word's indexes instead of words itself

                character_tensor - tensor of shape [target_num, num_lines, line_lenght, max_word_len].
                    Rows contain character indexes for every word in data

            :methods

                build_character_vocab(self, data) -> chars_vocab_size, idx_to_char, char_to_idx
                    chars_vocab_size - size of unique characters in corpus
                    idx_to_char - array of shape [chars_vocab_size] containing ordered list of inique characters
                    char_to_idx - dictionary of shape [chars_vocab_size]
                        such that idx_to_char[char_to_idx[some_char]] = some_char
                        where some_char is such that idx_to_char contains it

                build_word_vocab(self, sentences) -> words_vocab_size, idx_to_word, word_to_idx
                    same as for characters

                preprocess(self, data_files, idx_files, tensor_files) -> Void
                    preprocessed and initialized properties and then save them

                load_preprocessed(self, data_files, idx_files, tensor_files) -> Void
                    load and and initialized properties

                next_batch(self, batch_size, target_str) -> encoder_word_input, encoder_character_input, input_seq_len,
                        decoder_input, decoder_output
                    randomly sampled batch_size num of sequences for target from target_str.
                    fills sequences with pad tokens to made them the same lenght.
                    encoder_word_input and encoder_character_input have reversed order of the words
                        in case of performance
        """
        self.data_files = [path + 'data/train.txt', path + 'data/test.txt']
        self.idx_files = [path + 'data/words_vocab.pkl', path + 'data/characters_vocab.pkl']
        self.tensor_files = [[path + 'data/train_word_tensor.npy', path + 'data/valid_word_tensor.npy'], [path + 'data/train_character_tensor.npy', path + 'data/valid_character_tensor.npy']]
        self.blind_symbol = ''
        self.pad_token = '_'
        self.go_token = '>'
        self.end_token = '|'
        idx_exists = fold(f_and, [os.path.exists(file) for file in self.idx_files], True)
        tensors_exists = fold(f_and, [os.path.exists(file) for target in self.tensor_files for file in target], True)
        if idx_exists and tensors_exists:
            self.load_preprocessed(self.data_files, self.idx_files, self.tensor_files)
            print('preprocessed data was found and loaded')
        else:
            self.preprocess(self.data_files, self.idx_files, self.tensor_files)
            print('data have preprocessed')
        self.word_embedding_index = 0

    def clean_whole_data(self, string):
        string = re.sub('^[\\d\\:]+ ', '', string, 0, re.M)
        string = re.sub('\n\\s{11}', ' ', string, 0, re.M)
        string = re.sub('\n{2}', '\n', string, 0, re.M)
        return string.lower()

    def clean_str(self, string):
        """
            Tokenization/string cleaning for all datasets except for SST.
            Original taken from https://github.com/yoonkim/CNN_sentence/blob/master/process_data
        """
        string = re.sub("[^가-힣A-Za-z0-9(),!?:;.\\'\\`]", ' ', string)
        string = re.sub("\\'s", " 's", string)
        string = re.sub("\\'ve", " 've", string)
        string = re.sub("n\\'t", " n't", string)
        string = re.sub("\\'re", " 're", string)
        string = re.sub("\\'d", " 'd", string)
        string = re.sub("\\'ll", " 'll", string)
        string = re.sub('\\.', ' . ', string)
        string = re.sub(',', ' , ', string)
        string = re.sub(':', ' : ', string)
        string = re.sub(';', ' ; ', string)
        string = re.sub('!', ' ! ', string)
        string = re.sub('\\(', ' ( ', string)
        string = re.sub('\\)', ' ) ', string)
        string = re.sub('\\?', ' ? ', string)
        string = re.sub('\\s{2,}', ' ', string)
        return string.strip()

    def build_character_vocab(self, data):
        chars = list(set(data)) + [self.blind_symbol, self.pad_token, self.go_token, self.end_token]
        chars_vocab_size = len(chars)
        idx_to_char = chars
        char_to_idx = {x: i for i, x in enumerate(idx_to_char)}
        return (chars_vocab_size, idx_to_char, char_to_idx)

    def build_word_vocab(self, sentences):
        word_counts = collections.Counter(sentences)
        idx_to_word = [x[0] for x in word_counts.most_common()]
        idx_to_word = list(sorted(idx_to_word)) + [self.pad_token, self.go_token, self.end_token]
        words_vocab_size = len(idx_to_word)
        word_to_idx = {x: i for i, x in enumerate(idx_to_word)}
        return (words_vocab_size, idx_to_word, word_to_idx)

    def preprocess(self, data_files, idx_files, tensor_files):
        data = [open(file, 'r').read() for file in data_files]
        merged_data = data[0] + '\n' + data[1]
        self.chars_vocab_size, self.idx_to_char, self.char_to_idx = self.build_character_vocab(merged_data)
        with open(idx_files[1], 'wb') as f:
            cPickle.dump(self.idx_to_char, f)
        data_words = [[line.split() for line in target.split('\n')] for target in data]
        merged_data_words = merged_data.split()
        self.words_vocab_size, self.idx_to_word, self.word_to_idx = self.build_word_vocab(merged_data_words)
        self.max_word_len = np.amax([len(word) for word in self.idx_to_word])
        self.max_seq_len = np.amax([len(line) for target in data_words for line in target])
        self.num_lines = [len(target) for target in data_words]
        with open(idx_files[0], 'wb') as f:
            cPickle.dump(self.idx_to_word, f)
        self.word_tensor = np.array([[list(map(self.word_to_idx.get, line)) for line in target] for target in data_words])
        print(self.word_tensor.shape)
        for i, path in enumerate(tensor_files[0]):
            np.save(path, self.word_tensor[i])
        self.character_tensor = np.array([[list(map(self.encode_characters, line)) for line in target] for target in data_words])
        for i, path in enumerate(tensor_files[1]):
            np.save(path, self.character_tensor[i])
        self.just_words = [word for line in self.word_tensor[0] for word in line]

    def load_preprocessed(self, data_files, idx_files, tensor_files):
        data = [open(file, 'r').read() for file in data_files]
        data_words = [[line.split() for line in target.split('\n')] for target in data]
        self.max_seq_len = np.amax([len(line) for target in data_words for line in target])
        self.num_lines = [len(target) for target in data_words]
        [self.idx_to_word, self.idx_to_char] = [cPickle.load(open(file, 'rb')) for file in idx_files]
        [self.words_vocab_size, self.chars_vocab_size] = [len(idx) for idx in [self.idx_to_word, self.idx_to_char]]
        [self.word_to_idx, self.char_to_idx] = [dict(zip(idx, range(len(idx)))) for idx in [self.idx_to_word, self.idx_to_char]]
        self.max_word_len = np.amax([len(word) for word in self.idx_to_word])
        [self.word_tensor, self.character_tensor] = [np.array([np.load(target) for target in input_type]) for input_type in tensor_files]
        self.just_words = [word for line in self.word_tensor[0] for word in line]

    def next_batch(self, batch_size, target_str):
        target = 0 if target_str == 'train' else 1
        indexes = np.array(np.random.randint(self.num_lines[target], size=batch_size))
        encoder_word_input = [self.word_tensor[target][index] for index in indexes]
        encoder_character_input = [self.character_tensor[target][index] for index in indexes]
        input_seq_len = [len(line) for line in encoder_word_input]
        max_input_seq_len = np.amax(input_seq_len)
        encoded_words = [[idx for idx in line] for line in encoder_word_input]
        decoder_word_input = [[self.word_to_idx[self.go_token]] + line for line in encoder_word_input]
        decoder_character_input = [[self.encode_characters(self.go_token)] + line for line in encoder_character_input]
        decoder_output = [line + [self.word_to_idx[self.end_token]] for line in encoded_words]
        for i, line in enumerate(decoder_word_input):
            line_len = input_seq_len[i]
            to_add = max_input_seq_len - line_len
            decoder_word_input[i] = line + [self.word_to_idx[self.pad_token]] * to_add
        for i, line in enumerate(decoder_character_input):
            line_len = input_seq_len[i]
            to_add = max_input_seq_len - line_len
            decoder_character_input[i] = line + [self.encode_characters(self.pad_token)] * to_add
        for i, line in enumerate(decoder_output):
            line_len = input_seq_len[i]
            to_add = max_input_seq_len - line_len
            decoder_output[i] = line + [self.word_to_idx[self.pad_token]] * to_add
        for i, line in enumerate(encoder_word_input):
            line_len = input_seq_len[i]
            to_add = max_input_seq_len - line_len
            encoder_word_input[i] = [self.word_to_idx[self.pad_token]] * to_add + line[::-1]
        for i, line in enumerate(encoder_character_input):
            line_len = input_seq_len[i]
            to_add = max_input_seq_len - line_len
            encoder_character_input[i] = [self.encode_characters(self.pad_token)] * to_add + line[::-1]
        return (np.array(encoder_word_input), np.array(encoder_character_input), np.array(decoder_word_input), np.array(decoder_character_input), np.array(decoder_output))

    def next_embedding_seq(self, seq_len):
        """
        :return:
            tuple of input and output for word embedding learning,
            where input = [b, b, c, c, d, d, e, e]
            and output  = [a, c, b, d, d, e, d, g]
            for line [a, b, c, d, e, g] at index i
        """
        words_len = len(self.just_words)
        seq = [self.just_words[i % words_len] for i in np.arange(self.word_embedding_index, self.word_embedding_index + seq_len)]
        result = []
        for i in range(seq_len - 2):
            result.append([seq[i + 1], seq[i]])
            result.append([seq[i + 1], seq[i + 2]])
        self.word_embedding_index = (self.word_embedding_index + seq_len) % words_len - 2
        result = np.array(result)
        return (result[:, 0], result[:, 1])

    def go_input(self, batch_size):
        go_word_input = [[self.word_to_idx[self.go_token]] for _ in range(batch_size)]
        go_character_input = [[self.encode_characters(self.go_token)] for _ in range(batch_size)]
        return (np.array(go_word_input), np.array(go_character_input))

    def encode_word(self, idx):
        result = np.zeros(self.words_vocab_size)
        result[idx] = 1
        return result

    def decode_word(self, word_idx):
        word = self.idx_to_word[word_idx]
        return word

    def sample_word_from_distribution(self, distribution):
        ix = np.random.choice(range(self.words_vocab_size), p=distribution.ravel())
        x = np.zeros((self.words_vocab_size, 1))
        x[ix] = 1
        return self.idx_to_word[np.argmax(x)]

    def encode_characters(self, characters):
        word_len = len(characters)
        to_add = self.max_word_len - word_len
        characters_idx = [self.char_to_idx[i] for i in characters] + to_add * [self.char_to_idx['']]
        return characters_idx

    def decode_characters(self, characters_idx):
        characters = [self.idx_to_char[i] for i in characters_idx]
        return ''.join(characters)

def build_character_vocab(self, data):
    chars = list(set(data)) + [self.blind_symbol, self.pad_token, self.go_token, self.end_token]
    chars_vocab_size = len(chars)
    idx_to_char = chars
    char_to_idx = {x: i for i, x in enumerate(idx_to_char)}
    return (chars_vocab_size, idx_to_char, char_to_idx)

def build_word_vocab(self, sentences):
    word_counts = collections.Counter(sentences)
    idx_to_word = [x[0] for x in word_counts.most_common()]
    idx_to_word = list(sorted(idx_to_word)) + [self.pad_token, self.go_token, self.end_token]
    words_vocab_size = len(idx_to_word)
    word_to_idx = {x: i for i, x in enumerate(idx_to_word)}
    return (words_vocab_size, idx_to_word, word_to_idx)

def parameters_allocation_check(module):
    parameters = list(module.parameters())
    return fold(f_and, parameters, True) or not fold(f_or, parameters, False)

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

def learnable_parameters(self):
    return [p for p in self.parameters() if p.requires_grad]

