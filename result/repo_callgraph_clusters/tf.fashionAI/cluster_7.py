# Cluster 7

def single_device_model_fn(features, labels, mode, params=None, config=None):
    """`model_fn` on a single device without reduction overhead."""
    return _get_loss_towers(model_fn=model_fn, mode=mode, features=[features], labels=[labels], params=params, loss_reduction=loss_reduction, config=config, devices=devices, local_ps_devices=ps_devices)[0]

def replicated_model_fn(features, labels, mode, params=None, config=None):
    """Replicated version of `model_fn` to be used instead."""
    feature_shards, label_shards = _split_batch(features, labels, len(devices), device=consolidation_device)
    tower_specs = _get_loss_towers(model_fn=model_fn, mode=mode, features=feature_shards, labels=label_shards, params=params, loss_reduction=loss_reduction, config=config, devices=devices, local_ps_devices=ps_devices)
    if mode == model_fn_lib.ModeKeys.TRAIN:
        train_op = _minimize_towers(tower_specs)
        return _train_spec(tower_specs, train_op, aggregation_device=consolidation_device)
    elif mode == model_fn_lib.ModeKeys.EVAL:
        return _eval_spec(tower_specs, aggregation_device=consolidation_device)
    elif mode == model_fn_lib.ModeKeys.PREDICT:
        return _predict_spec(tower_specs, aggregation_device=consolidation_device)

