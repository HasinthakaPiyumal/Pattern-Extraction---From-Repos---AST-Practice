# Cluster 43

def build_optimizer(model, cfg):
    optimizer_cfg = copy.deepcopy(cfg)
    constructor_type = optimizer_cfg.pop('constructor', 'DefaultOptimizerConstructor')
    paramwise_cfg = optimizer_cfg.pop('paramwise_cfg', None)
    optim_constructor = build_optimizer_constructor(dict(type=constructor_type, optimizer_cfg=optimizer_cfg, paramwise_cfg=paramwise_cfg))
    optimizer = optim_constructor(model)
    return optimizer

def test_learning_rate_decay_optimizer_constructor():
    backbone = ToyConvNeXt()
    model = PseudoDataParallel(ToyDetector(backbone))
    optimizer_cfg = dict(type='AdamW', lr=base_lr, betas=(0.9, 0.999), weight_decay=0.05)
    stagewise_paramwise_cfg = dict(decay_rate=decay_rate, decay_type='stage_wise', num_layers=6)
    optim_constructor = LearningRateDecayOptimizerConstructor(optimizer_cfg, stagewise_paramwise_cfg)
    optimizer = optim_constructor(model)
    check_optimizer_lr_wd(optimizer, expected_stage_wise_lr_wd_convnext)
    layerwise_paramwise_cfg = dict(decay_rate=decay_rate, decay_type='layer_wise', num_layers=6)
    optim_constructor = LearningRateDecayOptimizerConstructor(optimizer_cfg, layerwise_paramwise_cfg)
    optimizer = optim_constructor(model)
    check_optimizer_lr_wd(optimizer, expected_layer_wise_lr_wd_convnext)

