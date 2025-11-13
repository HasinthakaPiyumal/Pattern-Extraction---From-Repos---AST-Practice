# Cluster 8

class FinalNet(BaseModel):

    def __init__(self, feature_map, model_id='FinalNet', gpu=-1, learning_rate=0.001, embedding_dim=10, block_type='2B', batch_norm=True, use_feature_gating=False, block1_hidden_units=[64, 64, 64], block1_hidden_activations=None, block1_dropout=0, block2_hidden_units=[64, 64, 64], block2_hidden_activations=None, block2_dropout=0, residual_type='concat', embedding_regularizer=None, net_regularizer=None, **kwargs):
        super(FinalNet, self).__init__(feature_map, model_id=model_id, gpu=gpu, embedding_regularizer=embedding_regularizer, net_regularizer=net_regularizer, **kwargs)
        assert block_type in ['1B', '2B'], 'block_type={} not supported.'.format(block_type)
        self.embedding_layer = FeatureEmbedding(feature_map, embedding_dim)
        num_fields = feature_map.num_fields
        self.use_feature_gating = use_feature_gating
        if use_feature_gating:
            self.feature_gating = FeatureGating(num_fields, gate_residual='concat')
            gate_out_dim = embedding_dim * num_fields * 2
        self.block_type = block_type
        self.block1 = FinalBlock(input_dim=gate_out_dim if use_feature_gating else embedding_dim * num_fields, hidden_units=block1_hidden_units, hidden_activations=block1_hidden_activations, dropout_rates=block1_dropout, batch_norm=batch_norm, residual_type=residual_type)
        self.fc1 = nn.Linear(block1_hidden_units[-1], 1)
        if block_type == '2B':
            self.block2 = FinalBlock(input_dim=embedding_dim * num_fields, hidden_units=block2_hidden_units, hidden_activations=block2_hidden_activations, dropout_rates=block2_dropout, batch_norm=batch_norm, residual_type=residual_type)
            self.fc2 = nn.Linear(block2_hidden_units[-1], 1)
        self.compile(kwargs['optimizer'], loss=kwargs['loss'], lr=learning_rate)
        self.reset_parameters()
        self.model_to_device()

    def forward(self, inputs):
        X = self.get_inputs(inputs)
        feature_emb = self.embedding_layer(X)
        y_pred, y1, y2 = (None, None, None)
        if self.block_type == '1B':
            y_pred = self.forward1(feature_emb)
        elif self.block_type == '2B':
            y1 = self.forward1(feature_emb)
            y2 = self.forward2(feature_emb)
            y_pred = 0.5 * (y1 + y2)
        y_pred = self.output_activation(y_pred)
        return_dict = {'y_pred': y_pred, 'y1': y1, 'y2': y2}
        return return_dict

    def forward1(self, X):
        if self.use_feature_gating:
            X = self.feature_gating(X)
        block1_out = self.block1(X.flatten(start_dim=1))
        y_pred = self.fc1(block1_out)
        return y_pred

    def forward2(self, X):
        block2_out = self.block2(X.flatten(start_dim=1))
        y_pred = self.fc2(block2_out)
        return y_pred

    def add_loss(self, return_dict, y_true):
        loss = self.loss_fn(return_dict['y_pred'], y_true, reduction='mean')
        if self.block_type == '2B':
            y1 = self.output_activation(return_dict['y1'])
            y2 = self.output_activation(return_dict['y2'])
            loss1 = self.loss_fn(y1, return_dict['y_pred'].detach(), reduction='mean')
            loss2 = self.loss_fn(y2, return_dict['y_pred'].detach(), reduction='mean')
            loss = loss + loss1 + loss2
        return loss

def forward1(self, X):
    if self.use_feature_gating:
        X = self.feature_gating(X)
    block1_out = self.block1(X.flatten(start_dim=1))
    y_pred = self.fc1(block1_out)
    return y_pred

