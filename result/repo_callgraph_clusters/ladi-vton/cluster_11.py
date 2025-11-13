# Cluster 11

class FeatureExtraction(nn.Module):

    def __init__(self, input_nc, ngf=64, n_layers=3, norm_layer=nn.BatchNorm2d, use_dropout=False):
        super(FeatureExtraction, self).__init__()
        downconv = nn.Conv2d(input_nc, ngf, kernel_size=4, stride=2, padding=1)
        model = [downconv, nn.ReLU(True), norm_layer(ngf)]
        for i in range(n_layers):
            in_ngf = 2 ** i * ngf if 2 ** i * ngf < 512 else 512
            out_ngf = 2 ** (i + 1) * ngf if 2 ** i * ngf < 512 else 512
            downconv = nn.Conv2d(in_ngf, out_ngf, kernel_size=4, stride=2, padding=1)
            model += [downconv, nn.ReLU(True)]
            model += [norm_layer(out_ngf)]
        model += [nn.Conv2d(512, 512, kernel_size=3, stride=1, padding=1), nn.ReLU(True)]
        model += [norm_layer(512)]
        model += [nn.Conv2d(512, 512, kernel_size=3, stride=1, padding=1), nn.ReLU(True)]
        self.model = nn.Sequential(*model)
        init_weights(self.model, init_type='normal')

    def get_output_size(self, in_shape):
        out_shape = None
        with torch.no_grad():
            out_shape = self.model(torch.randn(in_shape))
        return out_shape.shape

    def forward(self, x):
        return self.model(x)

def get_output_size(self, in_shape):
    out_shape = None
    with torch.no_grad():
        out_shape = self.model(torch.randn(in_shape))
    return out_shape.shape

def forward(self, x):
    return self.model(x)

class FeatureCorrelation(nn.Module):

    def __init__(self):
        super(FeatureCorrelation, self).__init__()

    def forward(self, feature_A, feature_B):
        b, c, h, w = feature_A.size()
        feature_A = feature_A.transpose(2, 3).contiguous().view(b, c, h * w)
        feature_B = feature_B.view(b, c, h * w).transpose(1, 2)
        feature_mul = torch.bmm(feature_B, feature_A)
        correlation_tensor = feature_mul.view(b, h, w, h * w).transpose(2, 3).transpose(1, 2)
        return correlation_tensor

    def get_output_size(self, in_shape):
        out_shape = None
        with torch.no_grad():
            out_shape = self.forward(torch.randn(in_shape), torch.randn(in_shape))
        return out_shape.shape

def get_output_size(self, in_shape):
    out_shape = None
    with torch.no_grad():
        out_shape = self.forward(torch.randn(in_shape), torch.randn(in_shape))
    return out_shape.shape

