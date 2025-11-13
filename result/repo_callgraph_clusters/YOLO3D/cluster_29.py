# Cluster 29

class Model(pl.LightningModule):

    def __init__(self, model_select='resnet18', bins=2, w=0.4, lr=0.0001, alpha=0.6):
        super(Model, self).__init__()
        self.save_hyperparameters()
        self.bins = bins
        self.w = w
        self.learning_rate = lr
        self.alpha = alpha
        self.conf_loss_func = nn.CrossEntropyLoss()
        self.dim_loss_func = nn.MSELoss()
        self.orient_loss_func = OrientationLoss
        self.model = model_factory(model_select)[0]
        self.in_features = model_factory(model_select)[1]
        self.orientation = nn.Sequential(nn.Linear(self.in_features, 256), nn.ReLU(True), nn.Dropout(), nn.Linear(256, 256), nn.ReLU(True), nn.Dropout(), nn.Linear(256, bins * 2))
        self.confidence = nn.Sequential(nn.Linear(self.in_features, 256), nn.ReLU(True), nn.Dropout(), nn.Linear(256, 256), nn.ReLU(True), nn.Dropout(), nn.Linear(256, bins))
        self.dimension = nn.Sequential(nn.Linear(self.in_features, 512), nn.ReLU(True), nn.Dropout(), nn.Linear(512, 512), nn.ReLU(True), nn.Dropout(), nn.Linear(512, 3))

    def forward(self, x):
        x = self.model(x)
        x = x.view(-1, self.in_features)
        orientation = self.orientation(x)
        orientation = orientation.view(-1, self.bins, 2)
        orientation = F.normalize(orientation, dim=2)
        confidence = self.confidence(x)
        dimension = self.dimension(x)
        return (orientation, confidence, dimension)

    def training_step(self, batch, batch_idx):
        x, labels = batch
        x = x.float()
        truth_orient = labels['Orientation'].float()
        truth_conf = labels['Confidence'].float()
        truth_dim = labels['Dimensions'].float()
        [orient, conf, dim] = self(x)
        orient_loss = self.orient_loss_func(orient, truth_orient, truth_conf)
        dim_loss = self.dim_loss_func(dim, truth_dim)
        truth_conf = torch.max(truth_conf, dim=1)[1]
        conf_loss = self.conf_loss_func(conf, truth_conf)
        loss_theta = conf_loss + self.w * orient_loss
        loss = self.alpha * dim_loss + loss_theta
        self.log('train_loss', loss)
        return {'loss': loss}

    def validation_step(self, batch, batch_idx):
        """
        In validation_step we use batch and batch_idx from validation data
        """
        results = self.training_step(batch, batch_idx)
        return results

    def validation_epoch_end(self, val_step_outputs):
        avg_val_loss = torch.tensor([x['loss'] for x in val_step_outputs]).mean()
        self.log('val_loss', avg_val_loss)
        return {'val_loss': avg_val_loss}

    def configure_optimizers(self):
        optimizer = torch.optim.SGD(self.parameters(), lr=self.learning_rate, momentum=0.9)
        return optimizer

def validation_step(self, batch, batch_idx):
    """
        In validation_step we use batch and batch_idx from validation data
        """
    results = self.training_step(batch, batch_idx)
    return results

