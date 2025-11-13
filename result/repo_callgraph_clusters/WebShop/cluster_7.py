# Cluster 7

def get_attribute_reward(purchased_product, goal):
    """Determines whether purchased products shares same attributes as goal"""
    purchased_attrs = purchased_product['Attributes']
    goal_attrs = goal['attributes']
    num_attr_matches = 0
    for g_attr in goal_attrs:
        matched = False
        for p_attr in purchased_attrs:
            score = fuzz.token_set_ratio(p_attr, g_attr)
            if score > 85:
                num_attr_matches += 1
                matched = True
                break
        if not matched and (g_attr in purchased_product['Title'].lower() or g_attr in ' '.join(purchased_product['BulletPoints']).lower() or g_attr in purchased_product['Description'].lower()):
            num_attr_matches += 1
            matched = True
    r_attr = num_attr_matches / len(goal_attrs)
    return (r_attr, num_attr_matches)

def get_option_reward(purchased_options, goal_options):
    """Calculate reward for purchased product's options w.r.t. goal options"""
    purchased_options = [normalize_color(o) for o in purchased_options]
    goal_options = [normalize_color(o) for o in goal_options]
    num_option_matches = 0
    for g_option in goal_options:
        for p_option in purchased_options:
            score = fuzz.token_set_ratio(p_option, g_option)
            if score > 85:
                num_option_matches += 1
                break
    r_option = num_option_matches / len(goal_options) if len(goal_options) > 0 else None
    return (r_option, num_option_matches)

class EncoderRNN(nn.Module):

    def __init__(self, input_size, num_units, nlayers, concat, bidir, layernorm, return_last):
        super().__init__()
        self.layernorm = layernorm == 'layer'
        if layernorm:
            self.norm = nn.LayerNorm(input_size)
        self.rnns = []
        for i in range(nlayers):
            if i == 0:
                input_size_ = input_size
                output_size_ = num_units
            else:
                input_size_ = num_units if not bidir else num_units * 2
                output_size_ = num_units
            self.rnns.append(nn.GRU(input_size_, output_size_, 1, bidirectional=bidir, batch_first=True))
        self.rnns = nn.ModuleList(self.rnns)
        self.init_hidden = nn.ParameterList([nn.Parameter(torch.zeros(size=(2 if bidir else 1, 1, num_units)), requires_grad=True) for _ in range(nlayers)])
        self.concat = concat
        self.nlayers = nlayers
        self.return_last = return_last
        self.reset_parameters()

    def reset_parameters(self):
        with torch.no_grad():
            for rnn_layer in self.rnns:
                for name, p in rnn_layer.named_parameters():
                    if 'weight_ih' in name:
                        torch.nn.init.xavier_uniform_(p.data)
                    elif 'weight_hh' in name:
                        torch.nn.init.orthogonal_(p.data)
                    elif 'bias' in name:
                        p.data.fill_(0.0)
                    else:
                        p.data.normal_(std=0.1)

    def get_init(self, bsz, i):
        return self.init_hidden[i].expand(-1, bsz, -1).contiguous()

    def forward(self, inputs, input_lengths=None):
        bsz, slen = (inputs.size(0), inputs.size(1))
        if self.layernorm:
            inputs = self.norm(inputs)
        output = inputs
        outputs = []
        lens = 0
        if input_lengths is not None:
            lens = input_lengths
        for i in range(self.nlayers):
            hidden = self.get_init(bsz, i)
            if input_lengths is not None:
                output = rnn.pack_padded_sequence(output, lens, batch_first=True, enforce_sorted=False)
            output, hidden = self.rnns[i](output, hidden)
            if input_lengths is not None:
                output, _ = rnn.pad_packed_sequence(output, batch_first=True)
                if output.size(1) < slen:
                    padding = torch.zeros(size=(1, 1, 1), dtype=output.type(), device=output.device())
                    output = torch.cat([output, padding.expand(output.size(0), slen - output.size(1), output.size(2))], dim=1)
            if self.return_last:
                outputs.append(hidden.permute(1, 0, 2).contiguous().view(bsz, -1))
            else:
                outputs.append(output)
        if self.concat:
            return torch.cat(outputs, dim=2)
        return outputs[-1]

def get_init(self, bsz, i):
    return self.init_hidden[i].expand(-1, bsz, -1).contiguous()

def forward(self, inputs, input_lengths=None):
    bsz, slen = (inputs.size(0), inputs.size(1))
    if self.layernorm:
        inputs = self.norm(inputs)
    output = inputs
    outputs = []
    lens = 0
    if input_lengths is not None:
        lens = input_lengths
    for i in range(self.nlayers):
        hidden = self.get_init(bsz, i)
        if input_lengths is not None:
            output = rnn.pack_padded_sequence(output, lens, batch_first=True, enforce_sorted=False)
        output, hidden = self.rnns[i](output, hidden)
        if input_lengths is not None:
            output, _ = rnn.pad_packed_sequence(output, batch_first=True)
            if output.size(1) < slen:
                padding = torch.zeros(size=(1, 1, 1), dtype=output.type(), device=output.device())
                output = torch.cat([output, padding.expand(output.size(0), slen - output.size(1), output.size(2))], dim=1)
        if self.return_last:
            outputs.append(hidden.permute(1, 0, 2).contiguous().view(bsz, -1))
        else:
            outputs.append(output)
    if self.concat:
        return torch.cat(outputs, dim=2)
    return outputs[-1]

class BiAttention(nn.Module):

    def __init__(self, input_size, dropout):
        super().__init__()
        self.dropout = nn.Dropout(dropout)
        self.input_linear = nn.Linear(input_size, 1, bias=False)
        self.memory_linear = nn.Linear(input_size, 1, bias=False)
        self.dot_scale = nn.Parameter(torch.zeros(size=(input_size,)).uniform_(1.0 / input_size ** 0.5), requires_grad=True)
        self.init_parameters()

    def init_parameters(self):
        return

    def forward(self, context, memory, mask):
        bsz, input_len = (context.size(0), context.size(1))
        memory_len = memory.size(1)
        context = self.dropout(context)
        memory = self.dropout(memory)
        input_dot = self.input_linear(context)
        memory_dot = self.memory_linear(memory).view(bsz, 1, memory_len)
        cross_dot = torch.bmm(context * self.dot_scale, memory.permute(0, 2, 1).contiguous())
        att = input_dot + memory_dot + cross_dot
        att = att - 1e+30 * (1 - mask[:, None])
        weight_one = F.softmax(att, dim=-1)
        output_one = torch.bmm(weight_one, memory)
        weight_two = F.softmax(att.max(dim=-1)[0], dim=-1).view(bsz, 1, input_len)
        output_two = torch.bmm(weight_two, context)
        return torch.cat([context, output_one, context * output_one, output_two * output_one], dim=-1)

def forward(self, context, memory, mask):
    bsz, input_len = (context.size(0), context.size(1))
    memory_len = memory.size(1)
    context = self.dropout(context)
    memory = self.dropout(memory)
    input_dot = self.input_linear(context)
    memory_dot = self.memory_linear(memory).view(bsz, 1, memory_len)
    cross_dot = torch.bmm(context * self.dot_scale, memory.permute(0, 2, 1).contiguous())
    att = input_dot + memory_dot + cross_dot
    att = att - 1e+30 * (1 - mask[:, None])
    weight_one = F.softmax(att, dim=-1)
    output_one = torch.bmm(weight_one, memory)
    weight_two = F.softmax(att.max(dim=-1)[0], dim=-1).view(bsz, 1, input_len)
    output_two = torch.bmm(weight_two, context)
    return torch.cat([context, output_one, context * output_one, output_two * output_one], dim=-1)

def test_generate_mturk_code():
    suite = [('', 'DA39A3EE5E'), ('ABC', '3C01BDBB26'), ('123', '40BD001563'), ('1A1', '10E7DB0A44'), ('$%^ABC', '5D5607D24E')]
    for session_id, expected in suite:
        output = generate_mturk_code(session_id)
        assert type(expected) is str
        assert output == expected

def test_normalize_color():
    suite = [('', ''), ('black forest', 'black'), ('violet lavender', 'lavender'), ('steelivy fuchsia', 'fuchsia'), ('123alabaster', 'alabaster'), ('webshop', 'webshop')]
    for color_string, expected in suite:
        output = normalize_color(color_string)
        assert type(output) is str
        assert output == expected

def test_normalize_color_size():
    product_prices = {(1, 'black forest', '3 meter'): 10.29, (2, 'violet lavender', 'xx-large'): 23.42, (3, 'steelivy fuchsia', 'random value'): 193.87, (4, '123alabaster', '40cm plus'): 67.23, (5, 'webshop', '142'): 1.02, (6, 'webshopsteel', '2 petite'): 57.99, (7, 'leather black', '91ft walnut feet'): 6.2}
    color_mapping_expected = {'N.A.': 'not_matched', 'black forest': 'black', 'violet lavender': 'lavender', 'steelivy fuchsia': 'fuchsia', '123alabaster': 'alabaster', 'webshop': 'not_matched', 'webshopsteel': 'steel', 'leather black': 'black'}
    size_mapping_expected = {'N.A.': 'not_matched', '3 meter': '(.*)meter', 'xx-large': 'xx-large', 'random value': 'not_matched', '40cm plus': '(.*)plus', '142': 'numeric_size', '2 petite': '(.*)petite', '91ft walnut feet': '(.*)ft'}
    color_mapping, size_mapping = normalize_color_size(product_prices)
    assert type(color_mapping) == dict
    assert type(size_mapping) == dict
    assert color_mapping == color_mapping_expected
    assert size_mapping == size_mapping_expected

