# Cluster 62

class ResnetBlock(nn.Module):

    def __init__(self, dim, padding_type, norm_layer, activation=nn.ReLU(True), use_dropout=False, conv_kind='default', dilation=1, in_dim=None, groups=1, second_dilation=None):
        super(ResnetBlock, self).__init__()
        self.in_dim = in_dim
        self.dim = dim
        if second_dilation is None:
            second_dilation = dilation
        self.conv_block = self.build_conv_block(dim, padding_type, norm_layer, activation, use_dropout, conv_kind=conv_kind, dilation=dilation, in_dim=in_dim, groups=groups, second_dilation=second_dilation)
        if self.in_dim is not None:
            self.input_conv = nn.Conv2d(in_dim, dim, 1)
        self.out_channnels = dim

    def build_conv_block(self, dim, padding_type, norm_layer, activation, use_dropout, conv_kind='default', dilation=1, in_dim=None, groups=1, second_dilation=1):
        conv_layer = get_conv_block_ctor(conv_kind)
        conv_block = []
        p = 0
        if padding_type == 'reflect':
            conv_block += [nn.ReflectionPad2d(dilation)]
        elif padding_type == 'replicate':
            conv_block += [nn.ReplicationPad2d(dilation)]
        elif padding_type == 'zero':
            p = dilation
        else:
            raise NotImplementedError('padding [%s] is not implemented' % padding_type)
        if in_dim is None:
            in_dim = dim
        conv_block += [conv_layer(in_dim, dim, kernel_size=3, padding=p, dilation=dilation), norm_layer(dim), activation]
        if use_dropout:
            conv_block += [nn.Dropout(0.5)]
        p = 0
        if padding_type == 'reflect':
            conv_block += [nn.ReflectionPad2d(second_dilation)]
        elif padding_type == 'replicate':
            conv_block += [nn.ReplicationPad2d(second_dilation)]
        elif padding_type == 'zero':
            p = second_dilation
        else:
            raise NotImplementedError('padding [%s] is not implemented' % padding_type)
        conv_block += [conv_layer(dim, dim, kernel_size=3, padding=p, dilation=second_dilation, groups=groups), norm_layer(dim)]
        return nn.Sequential(*conv_block)

    def forward(self, x):
        x_before = x
        if self.in_dim is not None:
            x = self.input_conv(x)
        out = x + self.conv_block(x_before)
        return out

def forward(self, x):
    x_before = x
    if self.in_dim is not None:
        x = self.input_conv(x)
    out = x + self.conv_block(x_before)
    return out

class ResnetBlock5x5(nn.Module):

    def __init__(self, dim, padding_type, norm_layer, activation=nn.ReLU(True), use_dropout=False, conv_kind='default', dilation=1, in_dim=None, groups=1, second_dilation=None):
        super(ResnetBlock5x5, self).__init__()
        self.in_dim = in_dim
        self.dim = dim
        if second_dilation is None:
            second_dilation = dilation
        self.conv_block = self.build_conv_block(dim, padding_type, norm_layer, activation, use_dropout, conv_kind=conv_kind, dilation=dilation, in_dim=in_dim, groups=groups, second_dilation=second_dilation)
        if self.in_dim is not None:
            self.input_conv = nn.Conv2d(in_dim, dim, 1)
        self.out_channnels = dim

    def build_conv_block(self, dim, padding_type, norm_layer, activation, use_dropout, conv_kind='default', dilation=1, in_dim=None, groups=1, second_dilation=1):
        conv_layer = get_conv_block_ctor(conv_kind)
        conv_block = []
        p = 0
        if padding_type == 'reflect':
            conv_block += [nn.ReflectionPad2d(dilation * 2)]
        elif padding_type == 'replicate':
            conv_block += [nn.ReplicationPad2d(dilation * 2)]
        elif padding_type == 'zero':
            p = dilation * 2
        else:
            raise NotImplementedError('padding [%s] is not implemented' % padding_type)
        if in_dim is None:
            in_dim = dim
        conv_block += [conv_layer(in_dim, dim, kernel_size=5, padding=p, dilation=dilation), norm_layer(dim), activation]
        if use_dropout:
            conv_block += [nn.Dropout(0.5)]
        p = 0
        if padding_type == 'reflect':
            conv_block += [nn.ReflectionPad2d(second_dilation * 2)]
        elif padding_type == 'replicate':
            conv_block += [nn.ReplicationPad2d(second_dilation * 2)]
        elif padding_type == 'zero':
            p = second_dilation * 2
        else:
            raise NotImplementedError('padding [%s] is not implemented' % padding_type)
        conv_block += [conv_layer(dim, dim, kernel_size=5, padding=p, dilation=second_dilation, groups=groups), norm_layer(dim)]
        return nn.Sequential(*conv_block)

    def forward(self, x):
        x_before = x
        if self.in_dim is not None:
            x = self.input_conv(x)
        out = x + self.conv_block(x_before)
        return out

def forward(self, x):
    x_before = x
    if self.in_dim is not None:
        x = self.input_conv(x)
    out = x + self.conv_block(x_before)
    return out

class MultidilatedResnetBlock(nn.Module):

    def __init__(self, dim, padding_type, conv_layer, norm_layer, activation=nn.ReLU(True), use_dropout=False):
        super().__init__()
        self.conv_block = self.build_conv_block(dim, padding_type, conv_layer, norm_layer, activation, use_dropout)

    def build_conv_block(self, dim, padding_type, conv_layer, norm_layer, activation, use_dropout, dilation=1):
        conv_block = []
        conv_block += [conv_layer(dim, dim, kernel_size=3, padding_mode=padding_type), norm_layer(dim), activation]
        if use_dropout:
            conv_block += [nn.Dropout(0.5)]
        conv_block += [conv_layer(dim, dim, kernel_size=3, padding_mode=padding_type), norm_layer(dim)]
        return nn.Sequential(*conv_block)

    def forward(self, x):
        out = x + self.conv_block(x)
        return out

def forward(self, x):
    out = x + self.conv_block(x)
    return out

class ResnetBlock(nn.Module):

    def __init__(self, dim, padding_type, norm_layer, activation=nn.ReLU(True), use_dropout=False, conv_kind='default', dilation=1, in_dim=None, groups=1, second_dilation=None):
        super(ResnetBlock, self).__init__()
        self.in_dim = in_dim
        self.dim = dim
        if second_dilation is None:
            second_dilation = dilation
        self.conv_block = self.build_conv_block(dim, padding_type, norm_layer, activation, use_dropout, conv_kind=conv_kind, dilation=dilation, in_dim=in_dim, groups=groups, second_dilation=second_dilation)
        if self.in_dim is not None:
            self.input_conv = nn.Conv2d(in_dim, dim, 1)
        self.out_channnels = dim

    def build_conv_block(self, dim, padding_type, norm_layer, activation, use_dropout, conv_kind='default', dilation=1, in_dim=None, groups=1, second_dilation=1):
        conv_layer = get_conv_block_ctor(conv_kind)
        conv_block = []
        p = 0
        if padding_type == 'reflect':
            conv_block += [nn.ReflectionPad2d(dilation)]
        elif padding_type == 'replicate':
            conv_block += [nn.ReplicationPad2d(dilation)]
        elif padding_type == 'zero':
            p = dilation
        else:
            raise NotImplementedError('padding [%s] is not implemented' % padding_type)
        if in_dim is None:
            in_dim = dim
        conv_block += [conv_layer(in_dim, dim, kernel_size=3, padding=p, dilation=dilation), norm_layer(dim), activation]
        if use_dropout:
            conv_block += [nn.Dropout(0.5)]
        p = 0
        if padding_type == 'reflect':
            conv_block += [nn.ReflectionPad2d(second_dilation)]
        elif padding_type == 'replicate':
            conv_block += [nn.ReplicationPad2d(second_dilation)]
        elif padding_type == 'zero':
            p = second_dilation
        else:
            raise NotImplementedError('padding [%s] is not implemented' % padding_type)
        conv_block += [conv_layer(dim, dim, kernel_size=3, padding=p, dilation=second_dilation, groups=groups), norm_layer(dim)]
        return nn.Sequential(*conv_block)

    def forward(self, x):
        x_before = x
        if self.in_dim is not None:
            x = self.input_conv(x)
        out = x + self.conv_block(x_before)
        return out

def forward(self, x):
    x_before = x
    if self.in_dim is not None:
        x = self.input_conv(x)
    out = x + self.conv_block(x_before)
    return out

class ResnetBlock5x5(nn.Module):

    def __init__(self, dim, padding_type, norm_layer, activation=nn.ReLU(True), use_dropout=False, conv_kind='default', dilation=1, in_dim=None, groups=1, second_dilation=None):
        super(ResnetBlock5x5, self).__init__()
        self.in_dim = in_dim
        self.dim = dim
        if second_dilation is None:
            second_dilation = dilation
        self.conv_block = self.build_conv_block(dim, padding_type, norm_layer, activation, use_dropout, conv_kind=conv_kind, dilation=dilation, in_dim=in_dim, groups=groups, second_dilation=second_dilation)
        if self.in_dim is not None:
            self.input_conv = nn.Conv2d(in_dim, dim, 1)
        self.out_channnels = dim

    def build_conv_block(self, dim, padding_type, norm_layer, activation, use_dropout, conv_kind='default', dilation=1, in_dim=None, groups=1, second_dilation=1):
        conv_layer = get_conv_block_ctor(conv_kind)
        conv_block = []
        p = 0
        if padding_type == 'reflect':
            conv_block += [nn.ReflectionPad2d(dilation * 2)]
        elif padding_type == 'replicate':
            conv_block += [nn.ReplicationPad2d(dilation * 2)]
        elif padding_type == 'zero':
            p = dilation * 2
        else:
            raise NotImplementedError('padding [%s] is not implemented' % padding_type)
        if in_dim is None:
            in_dim = dim
        conv_block += [conv_layer(in_dim, dim, kernel_size=5, padding=p, dilation=dilation), norm_layer(dim), activation]
        if use_dropout:
            conv_block += [nn.Dropout(0.5)]
        p = 0
        if padding_type == 'reflect':
            conv_block += [nn.ReflectionPad2d(second_dilation * 2)]
        elif padding_type == 'replicate':
            conv_block += [nn.ReplicationPad2d(second_dilation * 2)]
        elif padding_type == 'zero':
            p = second_dilation * 2
        else:
            raise NotImplementedError('padding [%s] is not implemented' % padding_type)
        conv_block += [conv_layer(dim, dim, kernel_size=5, padding=p, dilation=second_dilation, groups=groups), norm_layer(dim)]
        return nn.Sequential(*conv_block)

    def forward(self, x):
        x_before = x
        if self.in_dim is not None:
            x = self.input_conv(x)
        out = x + self.conv_block(x_before)
        return out

def forward(self, x):
    x_before = x
    if self.in_dim is not None:
        x = self.input_conv(x)
    out = x + self.conv_block(x_before)
    return out

class MultidilatedResnetBlock(nn.Module):

    def __init__(self, dim, padding_type, conv_layer, norm_layer, activation=nn.ReLU(True), use_dropout=False):
        super().__init__()
        self.conv_block = self.build_conv_block(dim, padding_type, conv_layer, norm_layer, activation, use_dropout)

    def build_conv_block(self, dim, padding_type, conv_layer, norm_layer, activation, use_dropout, dilation=1):
        conv_block = []
        conv_block += [conv_layer(dim, dim, kernel_size=3, padding_mode=padding_type), norm_layer(dim), activation]
        if use_dropout:
            conv_block += [nn.Dropout(0.5)]
        conv_block += [conv_layer(dim, dim, kernel_size=3, padding_mode=padding_type), norm_layer(dim)]
        return nn.Sequential(*conv_block)

    def forward(self, x):
        out = x + self.conv_block(x)
        return out

def forward(self, x):
    out = x + self.conv_block(x)
    return out

