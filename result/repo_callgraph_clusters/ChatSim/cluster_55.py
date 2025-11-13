# Cluster 55

class BCELoss(BaseAdversarialLoss):

    def __init__(self, weight):
        self.weight = weight
        self.bce_loss = nn.BCEWithLogitsLoss()

    def generator_loss(self, discr_fake_pred: torch.Tensor) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        real_mask_gt = torch.zeros(discr_fake_pred.shape).to(discr_fake_pred.device)
        fake_loss = self.bce_loss(discr_fake_pred, real_mask_gt) * self.weight
        return (fake_loss, dict())

    def pre_discriminator_step(self, real_batch: torch.Tensor, fake_batch: torch.Tensor, generator: nn.Module, discriminator: nn.Module):
        real_batch.requires_grad = True

    def discriminator_loss(self, mask: torch.Tensor, discr_real_pred: torch.Tensor, discr_fake_pred: torch.Tensor) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        real_mask_gt = torch.zeros(discr_real_pred.shape).to(discr_real_pred.device)
        sum_discr_loss = (self.bce_loss(discr_real_pred, real_mask_gt) + self.bce_loss(discr_fake_pred, mask)) / 2
        metrics = dict(discr_real_out=discr_real_pred.mean(), discr_fake_out=discr_fake_pred.mean(), discr_real_gp=0)
        return (sum_discr_loss, metrics)

def __init__(self, weight):
    self.weight = weight
    self.bce_loss = nn.BCEWithLogitsLoss()

class BCELoss(BaseAdversarialLoss):

    def __init__(self, weight):
        self.weight = weight
        self.bce_loss = nn.BCEWithLogitsLoss()

    def generator_loss(self, discr_fake_pred: torch.Tensor) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        real_mask_gt = torch.zeros(discr_fake_pred.shape).to(discr_fake_pred.device)
        fake_loss = self.bce_loss(discr_fake_pred, real_mask_gt) * self.weight
        return (fake_loss, dict())

    def pre_discriminator_step(self, real_batch: torch.Tensor, fake_batch: torch.Tensor, generator: nn.Module, discriminator: nn.Module):
        real_batch.requires_grad = True

    def discriminator_loss(self, mask: torch.Tensor, discr_real_pred: torch.Tensor, discr_fake_pred: torch.Tensor) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        real_mask_gt = torch.zeros(discr_real_pred.shape).to(discr_real_pred.device)
        sum_discr_loss = (self.bce_loss(discr_real_pred, real_mask_gt) + self.bce_loss(discr_fake_pred, mask)) / 2
        metrics = dict(discr_real_out=discr_real_pred.mean(), discr_fake_out=discr_fake_pred.mean(), discr_real_gp=0)
        return (sum_discr_loss, metrics)

def __init__(self, weight):
    self.weight = weight
    self.bce_loss = nn.BCEWithLogitsLoss()

