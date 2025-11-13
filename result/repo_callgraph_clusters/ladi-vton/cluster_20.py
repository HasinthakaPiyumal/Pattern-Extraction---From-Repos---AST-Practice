# Cluster 20

class Encoder(nn.Module):

    def __init__(self, in_channels=3, out_channels=3, down_block_types=('DownEncoderBlock2D',), block_out_channels=(64,), layers_per_block=2, norm_num_groups=32, act_fn='silu', double_z=True):
        super().__init__()
        self.layers_per_block = layers_per_block
        self.conv_in = torch.nn.Conv2d(in_channels, block_out_channels[0], kernel_size=3, stride=1, padding=1)
        self.mid_block = None
        self.down_blocks = nn.ModuleList([])
        output_channel = block_out_channels[0]
        for i, down_block_type in enumerate(down_block_types):
            input_channel = output_channel
            output_channel = block_out_channels[i]
            is_final_block = i == len(block_out_channels) - 1
            down_block = get_down_block(down_block_type, num_layers=self.layers_per_block, in_channels=input_channel, out_channels=output_channel, add_downsample=not is_final_block, resnet_eps=1e-06, downsample_padding=0, resnet_act_fn=act_fn, resnet_groups=norm_num_groups, attn_num_head_channels=None, temb_channels=None)
            self.down_blocks.append(down_block)
        self.mid_block = UNetMidBlock2D(in_channels=block_out_channels[-1], resnet_eps=1e-06, resnet_act_fn=act_fn, output_scale_factor=1, resnet_time_scale_shift='default', attn_num_head_channels=None, resnet_groups=norm_num_groups, temb_channels=None)
        self.conv_norm_out = nn.GroupNorm(num_channels=block_out_channels[-1], num_groups=norm_num_groups, eps=1e-06)
        self.conv_act = nn.SiLU()
        conv_out_channels = 2 * out_channels if double_z else out_channels
        self.conv_out = nn.Conv2d(block_out_channels[-1], conv_out_channels, 3, padding=1)

    def forward(self, x):
        intermediate_features = []
        intermediate_features.append(x)
        sample = x
        sample = self.conv_in(sample)
        intermediate_features.append(sample)
        for down_block in self.down_blocks:
            intermediate_features.append(sample)
            sample = down_block(sample)
        sample = self.mid_block(sample)
        sample = self.conv_norm_out(sample)
        sample = self.conv_act(sample)
        sample = self.conv_out(sample)
        return (sample, intermediate_features)

def forward(self, x):
    intermediate_features = []
    intermediate_features.append(x)
    sample = x
    sample = self.conv_in(sample)
    intermediate_features.append(sample)
    for down_block in self.down_blocks:
        intermediate_features.append(sample)
        sample = down_block(sample)
    sample = self.mid_block(sample)
    sample = self.conv_norm_out(sample)
    sample = self.conv_act(sample)
    sample = self.conv_out(sample)
    return (sample, intermediate_features)

class Decoder(nn.Module):

    def __init__(self, in_channels=3, out_channels=3, up_block_types=('UpDecoderBlock2D',), block_out_channels=(64,), layers_per_block=2, norm_num_groups=32, act_fn='silu'):
        super().__init__()
        self.layers_per_block = layers_per_block
        self.conv_in = nn.Conv2d(in_channels, block_out_channels[-1], kernel_size=3, stride=1, padding=1)
        self.mid_block = None
        self.up_blocks = nn.ModuleList([])
        self.mid_block = UNetMidBlock2D(in_channels=block_out_channels[-1], resnet_eps=1e-06, resnet_act_fn=act_fn, output_scale_factor=1, resnet_time_scale_shift='default', attn_num_head_channels=None, resnet_groups=norm_num_groups, temb_channels=None)
        reversed_block_out_channels = list(reversed(block_out_channels))
        output_channel = reversed_block_out_channels[0]
        for i, up_block_type in enumerate(up_block_types):
            prev_output_channel = output_channel
            output_channel = reversed_block_out_channels[i]
            is_final_block = i == len(block_out_channels) - 1
            up_block = get_up_block(up_block_type, num_layers=self.layers_per_block + 1, in_channels=prev_output_channel, out_channels=output_channel, prev_output_channel=None, add_upsample=not is_final_block, resnet_eps=1e-06, resnet_act_fn=act_fn, resnet_groups=norm_num_groups, attn_num_head_channels=None, temb_channels=None)
            self.up_blocks.append(up_block)
            prev_output_channel = output_channel
        self.conv_norm_out = nn.GroupNorm(num_channels=block_out_channels[0], num_groups=norm_num_groups, eps=1e-06)
        self.conv_act = nn.SiLU()
        self.conv_out = nn.Conv2d(block_out_channels[0], out_channels, 3, padding=1)

    def forward(self, z, intermediate_features=None, int_layers=None):
        sample = z
        sample = self.conv_in(sample)
        sample = self.mid_block(sample)
        if intermediate_features:
            intermediate_features.reverse()
            for up_block, int_feat in zip(self.up_blocks, intermediate_features):
                sample += int_feat
                sample = up_block(sample)
        else:
            for up_block in self.up_blocks:
                sample = up_block(sample)
        sample = self.conv_norm_out(sample)
        sample = self.conv_act(sample)
        if int_layers and 1 in int_layers:
            sample += intermediate_features[len(int_layers) - 1 - int_layers.index(1)]
        sample = self.conv_out(sample)
        if int_layers and 0 in int_layers:
            sample += intermediate_features[len(int_layers) - 1 - int_layers.index(0)]
        return sample

def forward(self, z, intermediate_features=None, int_layers=None):
    sample = z
    sample = self.conv_in(sample)
    sample = self.mid_block(sample)
    if intermediate_features:
        intermediate_features.reverse()
        for up_block, int_feat in zip(self.up_blocks, intermediate_features):
            sample += int_feat
            sample = up_block(sample)
    else:
        for up_block in self.up_blocks:
            sample = up_block(sample)
    sample = self.conv_norm_out(sample)
    sample = self.conv_act(sample)
    if int_layers and 1 in int_layers:
        sample += intermediate_features[len(int_layers) - 1 - int_layers.index(1)]
    sample = self.conv_out(sample)
    if int_layers and 0 in int_layers:
        sample += intermediate_features[len(int_layers) - 1 - int_layers.index(0)]
    return sample

