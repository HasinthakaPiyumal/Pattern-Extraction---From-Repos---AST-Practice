# Cluster 72

class DictGatherDataParallel(nn.DataParallel):

    def gather(self, outputs, output_device):
        return dict_gather(outputs, output_device, dim=self.dim)

def gather(self, outputs, output_device):
    return dict_gather(outputs, output_device, dim=self.dim)

class DictGatherDataParallel(nn.DataParallel):

    def gather(self, outputs, output_device):
        return dict_gather(outputs, output_device, dim=self.dim)

def gather(self, outputs, output_device):
    return dict_gather(outputs, output_device, dim=self.dim)

