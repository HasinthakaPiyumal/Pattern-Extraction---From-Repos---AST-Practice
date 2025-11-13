# Cluster 8

def save_image_with_heatmap(image, height, width, heatmap_size, targets, pred_heatmap, indR, indG, indB):
    if not hasattr(save_image_with_heatmap, 'counter'):
        save_image_with_heatmap.counter = 0
    save_image_with_heatmap.counter += 1
    img_to_save = np.array(image.tolist()) + 128
    img_to_save = img_to_save.astype(np.uint8)
    heatmap0 = np.sum(targets[indR, ...], axis=0).astype(np.uint8)
    heatmap1 = np.sum(targets[indG, ...], axis=0).astype(np.uint8)
    heatmap2 = np.sum(targets[indB, ...], axis=0).astype(np.uint8) if len(indB) > 0 else np.zeros((heatmap_size, heatmap_size), dtype=np.float32)
    img_to_save = imresize(img_to_save, (height, width), interp='lanczos')
    heatmap0 = imresize(heatmap0, (height, width), interp='lanczos')
    heatmap1 = imresize(heatmap1, (height, width), interp='lanczos')
    heatmap2 = imresize(heatmap2, (height, width), interp='lanczos')
    img_to_save = img_to_save / 2
    img_to_save[:, :, 0] = np.clip(img_to_save[:, :, 0] + heatmap0 + heatmap2, 0, 255)
    img_to_save[:, :, 1] = np.clip(img_to_save[:, :, 1] + heatmap1 + heatmap2, 0, 255)
    file_name = 'targets_{}.jpg'.format(save_image_with_heatmap.counter)
    imsave(os.path.join(config.DEBUG_DIR, file_name), img_to_save.astype(np.uint8))
    pred_heatmap = np.array(pred_heatmap.tolist())
    for ind in range(pred_heatmap.shape[0]):
        img = pred_heatmap[ind]
        img = img - img.min()
        img *= 255.0 / img.max()
        file_name = 'heatmap_{}_{}.jpg'.format(save_image_with_heatmap.counter, ind)
        imsave(os.path.join(config.DEBUG_DIR, file_name), img.astype(np.uint8))
    return save_image_with_heatmap.counter

def save_image_with_heatmap(image, height, width, heatmap_size, targets, pred_heatmap, indR, indG, indB):
    if not hasattr(save_image_with_heatmap, 'counter'):
        save_image_with_heatmap.counter = 0
    save_image_with_heatmap.counter += 1
    img_to_save = np.array(image.tolist()) + 128
    img_to_save = img_to_save.astype(np.uint8)
    heatmap0 = np.sum(targets[indR, ...], axis=0).astype(np.uint8)
    heatmap1 = np.sum(targets[indG, ...], axis=0).astype(np.uint8)
    heatmap2 = np.sum(targets[indB, ...], axis=0).astype(np.uint8) if len(indB) > 0 else np.zeros((heatmap_size, heatmap_size), dtype=np.float32)
    img_to_save = imresize(img_to_save, (height, width), interp='lanczos')
    heatmap0 = imresize(heatmap0, (height, width), interp='lanczos')
    heatmap1 = imresize(heatmap1, (height, width), interp='lanczos')
    heatmap2 = imresize(heatmap2, (height, width), interp='lanczos')
    img_to_save = img_to_save / 2
    img_to_save[:, :, 0] = np.clip(img_to_save[:, :, 0] + heatmap0 + heatmap2, 0, 255)
    img_to_save[:, :, 1] = np.clip(img_to_save[:, :, 1] + heatmap1 + heatmap2, 0, 255)
    file_name = 'targets_{}.jpg'.format(save_image_with_heatmap.counter)
    imsave(os.path.join(config.DEBUG_DIR, file_name), img_to_save.astype(np.uint8))
    pred_heatmap = np.array(pred_heatmap.tolist())
    for ind in range(pred_heatmap.shape[0]):
        img = pred_heatmap[ind]
        img = img - img.min()
        img *= 255.0 / img.max()
        file_name = 'heatmap_{}_{}.jpg'.format(save_image_with_heatmap.counter, ind)
        imsave(os.path.join(config.DEBUG_DIR, file_name), img.astype(np.uint8))
    return save_image_with_heatmap.counter

def save_image_with_heatmap(image, height, width, heatmap_size, heatmap, predictions, indR, indG, indB):
    if not hasattr(save_image_with_heatmap, 'counter'):
        save_image_with_heatmap.counter = 0
    save_image_with_heatmap.counter += 1
    img_to_save = np.array(image.tolist()) + 120
    img_to_save = img_to_save.astype(np.uint8)
    heatmap0 = np.sum(heatmap[indR, ...], axis=0).astype(np.uint8)
    heatmap1 = np.sum(heatmap[indG, ...], axis=0).astype(np.uint8)
    heatmap2 = np.sum(heatmap[indB, ...], axis=0).astype(np.uint8) if len(indB) > 0 else np.zeros((heatmap_size, heatmap_size), dtype=np.float32)
    img_to_save = imresize(img_to_save, (height, width), interp='lanczos')
    heatmap0 = imresize(heatmap0, (height, width), interp='lanczos')
    heatmap1 = imresize(heatmap1, (height, width), interp='lanczos')
    heatmap2 = imresize(heatmap2, (height, width), interp='lanczos')
    img_to_save = img_to_save / 2
    img_to_save[:, :, 0] = np.clip(img_to_save[:, :, 0] + heatmap0 + heatmap2, 0, 255)
    img_to_save[:, :, 1] = np.clip(img_to_save[:, :, 1] + heatmap1 + heatmap2, 0, 255)
    file_name = 'with_heatmap_{}.jpg'.format(save_image_with_heatmap.counter)
    imsave(os.path.join(config.EVAL_DEBUG_DIR, file_name), img_to_save.astype(np.uint8))
    predictions = np.array(predictions.tolist())
    for ind in range(predictions.shape[0]):
        img = predictions[ind]
        img = img - img.min()
        img *= 255.0 / img.max()
        file_name = 'heatmap_{}_{}.jpg'.format(save_image_with_heatmap.counter, ind)
        imsave(os.path.join(config.EVAL_DEBUG_DIR, file_name), img.astype(np.uint8))
    return save_image_with_heatmap.counter

def save_image_with_heatmap(image, height, width, heatmap_size, targets, pred_heatmap, indR, indG, indB):
    if not hasattr(save_image_with_heatmap, 'counter'):
        save_image_with_heatmap.counter = 0
    save_image_with_heatmap.counter += 1
    img_to_save = np.array(image.tolist()) + 128
    img_to_save = img_to_save.astype(np.uint8)
    heatmap0 = np.sum(targets[indR, ...], axis=0).astype(np.uint8)
    heatmap1 = np.sum(targets[indG, ...], axis=0).astype(np.uint8)
    heatmap2 = np.sum(targets[indB, ...], axis=0).astype(np.uint8) if len(indB) > 0 else np.zeros((heatmap_size, heatmap_size), dtype=np.float32)
    img_to_save = imresize(img_to_save, (height, width), interp='lanczos')
    heatmap0 = imresize(heatmap0, (height, width), interp='lanczos')
    heatmap1 = imresize(heatmap1, (height, width), interp='lanczos')
    heatmap2 = imresize(heatmap2, (height, width), interp='lanczos')
    img_to_save = img_to_save / 2
    img_to_save[:, :, 0] = np.clip(img_to_save[:, :, 0] + heatmap0 + heatmap2, 0, 255)
    img_to_save[:, :, 1] = np.clip(img_to_save[:, :, 1] + heatmap1 + heatmap2, 0, 255)
    file_name = 'targets_{}.jpg'.format(save_image_with_heatmap.counter)
    imsave(os.path.join(config.DEBUG_DIR, file_name), img_to_save.astype(np.uint8))
    pred_heatmap = np.array(pred_heatmap.tolist())
    for ind in range(pred_heatmap.shape[0]):
        img = pred_heatmap[ind]
        img = img - img.min()
        img *= 255.0 / img.max()
        file_name = 'heatmap_{}_{}.jpg'.format(save_image_with_heatmap.counter, ind)
        imsave(os.path.join(config.DEBUG_DIR, file_name), img.astype(np.uint8))
    return save_image_with_heatmap.counter

def save_image_with_heatmap(image, height, width, heatmap_size, targets, pred_heatmap, indR, indG, indB):
    if not hasattr(save_image_with_heatmap, 'counter'):
        save_image_with_heatmap.counter = 0
    save_image_with_heatmap.counter += 1
    img_to_save = np.array(image.tolist()) + 128
    img_to_save = img_to_save.astype(np.uint8)
    heatmap0 = np.sum(targets[indR, ...], axis=0).astype(np.uint8)
    heatmap1 = np.sum(targets[indG, ...], axis=0).astype(np.uint8)
    heatmap2 = np.sum(targets[indB, ...], axis=0).astype(np.uint8) if len(indB) > 0 else np.zeros((heatmap_size, heatmap_size), dtype=np.float32)
    img_to_save = imresize(img_to_save, (height, width), interp='lanczos')
    heatmap0 = imresize(heatmap0, (height, width), interp='lanczos')
    heatmap1 = imresize(heatmap1, (height, width), interp='lanczos')
    heatmap2 = imresize(heatmap2, (height, width), interp='lanczos')
    img_to_save = img_to_save / 2
    img_to_save[:, :, 0] = np.clip(img_to_save[:, :, 0] + heatmap0 + heatmap2, 0, 255)
    img_to_save[:, :, 1] = np.clip(img_to_save[:, :, 1] + heatmap1 + heatmap2, 0, 255)
    file_name = 'targets_{}.jpg'.format(save_image_with_heatmap.counter)
    imsave(os.path.join(config.DEBUG_DIR, file_name), img_to_save.astype(np.uint8))
    pred_heatmap = np.array(pred_heatmap.tolist())
    for ind in range(pred_heatmap.shape[0]):
        img = pred_heatmap[ind]
        img = img - img.min()
        img *= 255.0 / img.max()
        file_name = 'heatmap_{}_{}.jpg'.format(save_image_with_heatmap.counter, ind)
        imsave(os.path.join(config.DEBUG_DIR, file_name), img.astype(np.uint8))
    return save_image_with_heatmap.counter

def save_image_with_heatmap(image, height, width, heatmap_size, targets, pred_heatmap, indR, indG, indB):
    if not hasattr(save_image_with_heatmap, 'counter'):
        save_image_with_heatmap.counter = 0
    save_image_with_heatmap.counter += 1
    img_to_save = np.array(image.tolist()) + 120
    img_to_save = img_to_save.astype(np.uint8)
    heatmap0 = np.sum(targets[indR, ...], axis=0).astype(np.uint8)
    heatmap1 = np.sum(targets[indG, ...], axis=0).astype(np.uint8)
    heatmap2 = np.sum(targets[indB, ...], axis=0).astype(np.uint8) if len(indB) > 0 else np.zeros((heatmap_size, heatmap_size), dtype=np.float32)
    img_to_save = imresize(img_to_save, (height, width), interp='lanczos')
    heatmap0 = imresize(heatmap0, (height, width), interp='lanczos')
    heatmap1 = imresize(heatmap1, (height, width), interp='lanczos')
    heatmap2 = imresize(heatmap2, (height, width), interp='lanczos')
    img_to_save = img_to_save / 2
    img_to_save[:, :, 0] = np.clip(img_to_save[:, :, 0] + heatmap0 + heatmap2, 0, 255)
    img_to_save[:, :, 1] = np.clip(img_to_save[:, :, 1] + heatmap1 + heatmap2, 0, 255)
    file_name = 'targets_{}.jpg'.format(save_image_with_heatmap.counter)
    imsave(os.path.join(config.DEBUG_DIR, file_name), img_to_save.astype(np.uint8))
    pred_heatmap = np.array(pred_heatmap.tolist())
    for ind in range(pred_heatmap.shape[0]):
        img = pred_heatmap[ind]
        img = img - img.min()
        img *= 255.0 / img.max()
        file_name = 'heatmap_{}_{}.jpg'.format(save_image_with_heatmap.counter, ind)
        imsave(os.path.join(config.DEBUG_DIR, file_name), img.astype(np.uint8))
    return save_image_with_heatmap.counter

def save_image_with_heatmap(image, height, width, heatmap_size, targets, pred_heatmap, indR, indG, indB):
    if not hasattr(save_image_with_heatmap, 'counter'):
        save_image_with_heatmap.counter = 0
    save_image_with_heatmap.counter += 1
    img_to_save = np.array(image.tolist()) + 128
    img_to_save = img_to_save.astype(np.uint8)
    heatmap0 = np.sum(targets[indR, ...], axis=0).astype(np.uint8)
    heatmap1 = np.sum(targets[indG, ...], axis=0).astype(np.uint8)
    heatmap2 = np.sum(targets[indB, ...], axis=0).astype(np.uint8) if len(indB) > 0 else np.zeros((heatmap_size, heatmap_size), dtype=np.float32)
    img_to_save = imresize(img_to_save, (height, width), interp='lanczos')
    heatmap0 = imresize(heatmap0, (height, width), interp='lanczos')
    heatmap1 = imresize(heatmap1, (height, width), interp='lanczos')
    heatmap2 = imresize(heatmap2, (height, width), interp='lanczos')
    img_to_save = img_to_save / 2
    img_to_save[:, :, 0] = np.clip(img_to_save[:, :, 0] + heatmap0 + heatmap2, 0, 255)
    img_to_save[:, :, 1] = np.clip(img_to_save[:, :, 1] + heatmap1 + heatmap2, 0, 255)
    file_name = 'targets_{}.jpg'.format(save_image_with_heatmap.counter)
    imsave(os.path.join(config.DEBUG_DIR, file_name), img_to_save.astype(np.uint8))
    pred_heatmap = np.array(pred_heatmap.tolist())
    for ind in range(pred_heatmap.shape[0]):
        img = pred_heatmap[ind]
        img = img - img.min()
        img *= 255.0 / img.max()
        file_name = 'heatmap_{}_{}.jpg'.format(save_image_with_heatmap.counter, ind)
        imsave(os.path.join(config.DEBUG_DIR, file_name), img.astype(np.uint8))
    return save_image_with_heatmap.counter

def save_image_with_heatmap(image, height, width, heatmap_size, heatmap, predictions, indR, indG, indB):
    if not hasattr(save_image_with_heatmap, 'counter'):
        save_image_with_heatmap.counter = 0
    save_image_with_heatmap.counter += 1
    img_to_save = np.array(image.tolist()) + 120
    img_to_save = img_to_save.astype(np.uint8)
    heatmap0 = np.sum(heatmap[indR, ...], axis=0).astype(np.uint8)
    heatmap1 = np.sum(heatmap[indG, ...], axis=0).astype(np.uint8)
    heatmap2 = np.sum(heatmap[indB, ...], axis=0).astype(np.uint8) if len(indB) > 0 else np.zeros((heatmap_size, heatmap_size), dtype=np.float32)
    img_to_save = imresize(img_to_save, (height, width), interp='lanczos')
    heatmap0 = imresize(heatmap0, (height, width), interp='lanczos')
    heatmap1 = imresize(heatmap1, (height, width), interp='lanczos')
    heatmap2 = imresize(heatmap2, (height, width), interp='lanczos')
    img_to_save = img_to_save / 2
    img_to_save[:, :, 0] = np.clip(img_to_save[:, :, 0] + heatmap0 + heatmap2, 0, 255)
    img_to_save[:, :, 1] = np.clip(img_to_save[:, :, 1] + heatmap1 + heatmap2, 0, 255)
    file_name = 'with_heatmap_{}.jpg'.format(save_image_with_heatmap.counter)
    imsave(os.path.join(config.EVAL_DEBUG_DIR, file_name), img_to_save.astype(np.uint8))
    predictions = np.array(predictions.tolist())
    for ind in range(predictions.shape[0]):
        img = predictions[ind]
        img = img - img.min()
        img *= 255.0 / img.max()
        file_name = 'heatmap_{}_{}.jpg'.format(save_image_with_heatmap.counter, ind)
        imsave(os.path.join(config.EVAL_DEBUG_DIR, file_name), img.astype(np.uint8))
    return save_image_with_heatmap.counter

def save_image_with_heatmap(image, height, width, heatmap_size, targets, pred_heatmap, indR, indG, indB):
    if not hasattr(save_image_with_heatmap, 'counter'):
        save_image_with_heatmap.counter = 0
    save_image_with_heatmap.counter += 1
    img_to_save = np.array(image.tolist()) + 128
    img_to_save = img_to_save.astype(np.uint8)
    heatmap0 = np.sum(targets[indR, ...], axis=0).astype(np.uint8)
    heatmap1 = np.sum(targets[indG, ...], axis=0).astype(np.uint8)
    heatmap2 = np.sum(targets[indB, ...], axis=0).astype(np.uint8) if len(indB) > 0 else np.zeros((heatmap_size, heatmap_size), dtype=np.float32)
    img_to_save = imresize(img_to_save, (height, width), interp='lanczos')
    heatmap0 = imresize(heatmap0, (height, width), interp='lanczos')
    heatmap1 = imresize(heatmap1, (height, width), interp='lanczos')
    heatmap2 = imresize(heatmap2, (height, width), interp='lanczos')
    img_to_save = img_to_save / 2
    img_to_save[:, :, 0] = np.clip(img_to_save[:, :, 0] + heatmap0 + heatmap2, 0, 255)
    img_to_save[:, :, 1] = np.clip(img_to_save[:, :, 1] + heatmap1 + heatmap2, 0, 255)
    file_name = 'targets_{}.jpg'.format(save_image_with_heatmap.counter)
    imsave(os.path.join(config.DEBUG_DIR, file_name), img_to_save.astype(np.uint8))
    pred_heatmap = np.array(pred_heatmap.tolist())
    for ind in range(pred_heatmap.shape[0]):
        img = pred_heatmap[ind]
        img = img - img.min()
        img *= 255.0 / img.max()
        file_name = 'heatmap_{}_{}.jpg'.format(save_image_with_heatmap.counter, ind)
        imsave(os.path.join(config.DEBUG_DIR, file_name), img.astype(np.uint8))
    return save_image_with_heatmap.counter

def validate_batch_size_for_multi_gpu(batch_size):
    """For multi-gpu, batch-size must be a multiple of the number of
    available GPUs.

    Note that this should eventually be handled by replicate_model_fn
    directly. Multi-GPU support is currently experimental, however,
    so doing the work here until that feature is in place.
    """
    if not FLAGS.multi_gpu:
        return 0
    from tensorflow.python.client import device_lib
    local_device_protos = device_lib.list_local_devices()
    num_gpus = sum([1 for d in local_device_protos if d.device_type == 'GPU'])
    if not num_gpus:
        raise ValueError('Multi-GPU mode was specified, but no GPUs were found. To use CPU, run without --multi_gpu=False.')
    remainder = batch_size % num_gpus
    if remainder:
        err = 'When running with multiple GPUs, batch size must be a multiple of the number of available GPUs. Found {} GPUs with a batch size of {}; try --batch_size={} instead.'.format(num_gpus, batch_size, batch_size - remainder)
        raise ValueError(err)
    return num_gpus

def save_image_with_heatmap(image, height, width, heatmap_size, targets, pred_heatmap, indR, indG, indB):
    if not hasattr(save_image_with_heatmap, 'counter'):
        save_image_with_heatmap.counter = 0
    save_image_with_heatmap.counter += 1
    img_to_save = np.array(image.tolist()) + 128
    img_to_save = img_to_save.astype(np.uint8)
    heatmap0 = np.sum(targets[indR, ...], axis=0).astype(np.uint8)
    heatmap1 = np.sum(targets[indG, ...], axis=0).astype(np.uint8)
    heatmap2 = np.sum(targets[indB, ...], axis=0).astype(np.uint8) if len(indB) > 0 else np.zeros((heatmap_size, heatmap_size), dtype=np.float32)
    img_to_save = imresize(img_to_save, (height, width), interp='lanczos')
    heatmap0 = imresize(heatmap0, (height, width), interp='lanczos')
    heatmap1 = imresize(heatmap1, (height, width), interp='lanczos')
    heatmap2 = imresize(heatmap2, (height, width), interp='lanczos')
    img_to_save = img_to_save / 2
    img_to_save[:, :, 0] = np.clip(img_to_save[:, :, 0] + heatmap0 + heatmap2, 0, 255)
    img_to_save[:, :, 1] = np.clip(img_to_save[:, :, 1] + heatmap1 + heatmap2, 0, 255)
    file_name = 'targets_{}.jpg'.format(save_image_with_heatmap.counter)
    imsave(os.path.join(config.DEBUG_DIR, file_name), img_to_save.astype(np.uint8))
    pred_heatmap = np.array(pred_heatmap.tolist())
    for ind in range(pred_heatmap.shape[0]):
        img = pred_heatmap[ind]
        img = img - img.min()
        img *= 255.0 / img.max()
        file_name = 'heatmap_{}_{}.jpg'.format(save_image_with_heatmap.counter, ind)
        imsave(os.path.join(config.DEBUG_DIR, file_name), img.astype(np.uint8))
    return save_image_with_heatmap.counter

def save_image_with_heatmap(image, height, width, heatmap_size, heatmap, predictions, indR, indG, indB):
    if not hasattr(save_image_with_heatmap, 'counter'):
        save_image_with_heatmap.counter = 0
    save_image_with_heatmap.counter += 1
    img_to_save = np.array(image.tolist()) + 120
    img_to_save = img_to_save.astype(np.uint8)
    heatmap0 = np.sum(heatmap[indR, ...], axis=0).astype(np.uint8)
    heatmap1 = np.sum(heatmap[indG, ...], axis=0).astype(np.uint8)
    heatmap2 = np.sum(heatmap[indB, ...], axis=0).astype(np.uint8) if len(indB) > 0 else np.zeros((heatmap_size, heatmap_size), dtype=np.float32)
    img_to_save = imresize(img_to_save, (height, width), interp='lanczos')
    heatmap0 = imresize(heatmap0, (height, width), interp='lanczos')
    heatmap1 = imresize(heatmap1, (height, width), interp='lanczos')
    heatmap2 = imresize(heatmap2, (height, width), interp='lanczos')
    img_to_save = img_to_save / 2
    img_to_save[:, :, 0] = np.clip(img_to_save[:, :, 0] + heatmap0 + heatmap2, 0, 255)
    img_to_save[:, :, 1] = np.clip(img_to_save[:, :, 1] + heatmap1 + heatmap2, 0, 255)
    file_name = 'with_heatmap_{}.jpg'.format(save_image_with_heatmap.counter)
    imsave(os.path.join(config.EVAL_DEBUG_DIR, file_name), img_to_save.astype(np.uint8))
    predictions = np.array(predictions.tolist())
    for ind in range(predictions.shape[0]):
        img = predictions[ind]
        img = img - img.min()
        img *= 255.0 / img.max()
        file_name = 'heatmap_{}_{}.jpg'.format(save_image_with_heatmap.counter, ind)
        imsave(os.path.join(config.EVAL_DEBUG_DIR, file_name), img.astype(np.uint8))
    return save_image_with_heatmap.counter

def validate_batch_size_for_multi_gpu(batch_size):
    """For multi-gpu, batch-size must be a multiple of the number of
    available GPUs.

    Note that this should eventually be handled by replicate_model_fn
    directly. Multi-GPU support is currently experimental, however,
    so doing the work here until that feature is in place.
    """
    if not FLAGS.multi_gpu:
        return 0
    from tensorflow.python.client import device_lib
    local_device_protos = device_lib.list_local_devices()
    num_gpus = sum([1 for d in local_device_protos if d.device_type == 'GPU'])
    if not num_gpus:
        raise ValueError('Multi-GPU mode was specified, but no GPUs were found. To use CPU, run without --multi_gpu=False.')
    remainder = batch_size % num_gpus
    if remainder:
        err = 'When running with multiple GPUs, batch size must be a multiple of the number of available GPUs. Found {} GPUs with a batch size of {}; try --batch_size={} instead.'.format(num_gpus, batch_size, batch_size - remainder)
        raise ValueError(err)
    return num_gpus

def save_image_with_heatmap(image, height, width, heatmap_size, targets, pred_heatmap, indR, indG, indB):
    if not hasattr(save_image_with_heatmap, 'counter'):
        save_image_with_heatmap.counter = 0
    save_image_with_heatmap.counter += 1
    img_to_save = np.array(image.tolist()) + 128
    img_to_save = img_to_save.astype(np.uint8)
    heatmap0 = np.sum(targets[indR, ...], axis=0).astype(np.uint8)
    heatmap1 = np.sum(targets[indG, ...], axis=0).astype(np.uint8)
    heatmap2 = np.sum(targets[indB, ...], axis=0).astype(np.uint8) if len(indB) > 0 else np.zeros((heatmap_size, heatmap_size), dtype=np.float32)
    img_to_save = imresize(img_to_save, (height, width), interp='lanczos')
    heatmap0 = imresize(heatmap0, (height, width), interp='lanczos')
    heatmap1 = imresize(heatmap1, (height, width), interp='lanczos')
    heatmap2 = imresize(heatmap2, (height, width), interp='lanczos')
    img_to_save = img_to_save / 2
    img_to_save[:, :, 0] = np.clip(img_to_save[:, :, 0] + heatmap0 + heatmap2, 0, 255)
    img_to_save[:, :, 1] = np.clip(img_to_save[:, :, 1] + heatmap1 + heatmap2, 0, 255)
    file_name = 'targets_{}.jpg'.format(save_image_with_heatmap.counter)
    imsave(os.path.join(config.DEBUG_DIR, file_name), img_to_save.astype(np.uint8))
    pred_heatmap = np.array(pred_heatmap.tolist())
    for ind in range(pred_heatmap.shape[0]):
        img = pred_heatmap[ind]
        img = img - img.min()
        img *= 255.0 / img.max()
        file_name = 'heatmap_{}_{}.jpg'.format(save_image_with_heatmap.counter, ind)
        imsave(os.path.join(config.DEBUG_DIR, file_name), img.astype(np.uint8))
    return save_image_with_heatmap.counter

class TowerOptimizer(optimizer_lib.Optimizer):
    """Gathers gradients from all towers and reduces them in the last one."""
    COLLECTION_FOR_GRAPH_STATES = 'replicate_model_fn_graph_states'

    def __init__(self, optimizer_or_optimizer_fn):
        """Wrap an existing optimizer for gathering gradients across towers.

    Each invocation of model_fn has to call the same optimizers in the same
    order.

    Multiple optimizers that use the same or different losses are supported.

    If TowerOptimizer is used but `replicate_model_fn` isn't, then no
    aggregation will happen.  All calls will simply be forwarded to the
    underlying optimizer. The behavior is similar if there is only one tower.

    If TowerOptimizer is used together with SyncReplicasOptimizer that wraps
    the user's optimizer, then it's the SyncReplicasOptimizer that needs to be
    wrapped with TowerOptimizer.

    Args:
      optimizer_or_optimizer_fn: an instance of optimizer to wrap.  That
        instance is going to be used for optimizer-specific logic.  This can
        also be a no-argument function that returns such an optimizer instance.
    """
        self._optimizer_or_optimizer_fn = optimizer_or_optimizer_fn

    @staticmethod
    def has_been_used():
        return TowerOptimizer._graph_state().has_tower_optimizer_been_used

    def get_slot(self, *args, **kwargs):
        return self._get_optimizer().get_slot(*args, **kwargs)

    def get_slot_names(self, *args, **kwargs):
        return self._get_optimizer().get_slot_names(*args, **kwargs)

    def get_name(self, *args, **kwargs):
        return self._get_optimizer().get_name(*args, **kwargs)

    def variables(self, *args, **kwargs):
        return self._get_optimizer().variables(*args, **kwargs)

    def compute_gradients(self, loss, *args, **kwargs):
        """Compute gradients, but first, if needed, scale the loss."""
        loss = _scale_loss(loss, self._graph_state().loss_reduction, self._graph_state().number_of_towers)
        return self._get_optimizer().compute_gradients(loss, *args, **kwargs)

    def apply_gradients(self, grads_and_vars, global_step=None, **kwargs):
        """Collect gradients updates to apply them with the last tower."""
        if self._graph_state().number_of_towers == 1:
            return self._get_optimizer().apply_gradients(grads_and_vars, global_step, **kwargs)
        self._graph_state().collect_gradients(grads_and_vars)
        if not self._graph_state().is_the_last_tower:
            with ops_lib.control_dependencies(_extract_tensors(grads_and_vars)):
                return self._construct_no_op_train_op()
        else:
            var_scope, name_scope = self._graph_state().scopes_of_the_first_tower
            with variable_scope.variable_scope(var_scope):
                with ops_lib.name_scope(name_scope):
                    return self._apply_gathered_gradients(global_step, **kwargs)

    def _apply_gathered_gradients(self, global_step, **kwargs):
        graph_state = self._graph_state()
        optimizer = self._get_optimizer()
        grad_lists = {}
        for grad, var in graph_state.get_latest_gradients_from_all_towers():
            if grad is not None:
                grad_lists.setdefault(var, []).append(grad)
        aggregated_grads = []
        with ops_lib.name_scope('gradient_aggregating'):
            for var, grads in six.iteritems(grad_lists):
                grad = _compute_sum_on_device(grads, var.device)
                aggregated_grads.append((grad, var))
        return optimizer.apply_gradients(aggregated_grads, global_step=global_step, **kwargs)

    def _get_optimizer(self):
        if callable(self._optimizer_or_optimizer_fn):
            self._optimizer_or_optimizer_fn = self._optimizer_or_optimizer_fn()
        self._graph_state().has_tower_optimizer_been_used = True
        return self._optimizer_or_optimizer_fn

    def _construct_no_op_train_op(self):
        return control_flow_ops.no_op(name='train_op_placeholder')

    @staticmethod
    def _graph_state():
        graph_states = ops_lib.get_default_graph().get_collection_ref(TowerOptimizer.COLLECTION_FOR_GRAPH_STATES)
        if not graph_states:
            graph_states.append(TowerOptimizer._PerGraphState())
        return graph_states[-1]

    @staticmethod
    def _did_towers_have_same_optimizer_calls():
        graph_state = TowerOptimizer._graph_state()
        return graph_state.did_towers_have_same_optimizer_calls()

    @staticmethod
    def _clear_graph_state():
        ops_lib.get_default_graph().clear_collection(TowerOptimizer.COLLECTION_FOR_GRAPH_STATES)

    class _PerGraphState(object):
        """Gradient reduction related state of a Tensorflow graph."""

        def __init__(self):
            self._collected_grads_and_vars = defaultdict(list)
            self._current_tower_index = 0
            self._number_of_towers = 1
            self._loss_reduction = None
            self._variable_scope = None
            self._name_scope = None
            self._has_tower_optimizer_been_used = False

        def collect_gradients(self, grads_and_vars):
            self._collected_grads_and_vars[self._current_tower_index].append(grads_and_vars)

        def get_latest_gradients_from_all_towers(self):
            """Get gradients across towers for the last called optimizer."""
            grads_and_vars = []
            index_of_last_gradients = len(self._collected_grads_and_vars[self._current_tower_index]) - 1
            for tower_id in range(self._current_tower_index + 1):
                grads_and_vars.extend(self._collected_grads_and_vars[tower_id][index_of_last_gradients])
            return grads_and_vars

        def set_reduction_across_towers(self, loss_reduction, number_of_towers):
            self._loss_reduction = loss_reduction
            self._number_of_towers = number_of_towers

        @contextmanager
        def tower(self, tower_id, var_scope, name_scope):
            if tower_id == 0:
                self._variable_scope = var_scope
                self._name_scope = name_scope
            self._current_tower_index = tower_id
            yield

        @property
        def scopes_of_the_first_tower(self):
            return (self._variable_scope, self._name_scope)

        @property
        def is_the_last_tower(self):
            return self._current_tower_index == self._number_of_towers - 1

        @property
        def number_of_towers(self):
            return self._number_of_towers

        @property
        def loss_reduction(self):
            return self._loss_reduction

        @property
        def has_tower_optimizer_been_used(self):
            return self._has_tower_optimizer_been_used

        @has_tower_optimizer_been_used.setter
        def has_tower_optimizer_been_used(self, value):
            self._has_tower_optimizer_been_used = value

        def did_towers_have_same_optimizer_calls(self):
            total_number_of_grads = sum([len(grads) for _, grads in six.iteritems(self._collected_grads_and_vars)])
            return total_number_of_grads % self._number_of_towers == 0

def _construct_no_op_train_op(self):
    return control_flow_ops.no_op(name='train_op_placeholder')

class _PerGraphState(object):
    """Gradient reduction related state of a Tensorflow graph."""

    def __init__(self):
        self._collected_grads_and_vars = defaultdict(list)
        self._current_tower_index = 0
        self._number_of_towers = 1
        self._loss_reduction = None
        self._variable_scope = None
        self._name_scope = None
        self._has_tower_optimizer_been_used = False

    def collect_gradients(self, grads_and_vars):
        self._collected_grads_and_vars[self._current_tower_index].append(grads_and_vars)

    def get_latest_gradients_from_all_towers(self):
        """Get gradients across towers for the last called optimizer."""
        grads_and_vars = []
        index_of_last_gradients = len(self._collected_grads_and_vars[self._current_tower_index]) - 1
        for tower_id in range(self._current_tower_index + 1):
            grads_and_vars.extend(self._collected_grads_and_vars[tower_id][index_of_last_gradients])
        return grads_and_vars

    def set_reduction_across_towers(self, loss_reduction, number_of_towers):
        self._loss_reduction = loss_reduction
        self._number_of_towers = number_of_towers

    @contextmanager
    def tower(self, tower_id, var_scope, name_scope):
        if tower_id == 0:
            self._variable_scope = var_scope
            self._name_scope = name_scope
        self._current_tower_index = tower_id
        yield

    @property
    def scopes_of_the_first_tower(self):
        return (self._variable_scope, self._name_scope)

    @property
    def is_the_last_tower(self):
        return self._current_tower_index == self._number_of_towers - 1

    @property
    def number_of_towers(self):
        return self._number_of_towers

    @property
    def loss_reduction(self):
        return self._loss_reduction

    @property
    def has_tower_optimizer_been_used(self):
        return self._has_tower_optimizer_been_used

    @has_tower_optimizer_been_used.setter
    def has_tower_optimizer_been_used(self, value):
        self._has_tower_optimizer_been_used = value

    def did_towers_have_same_optimizer_calls(self):
        total_number_of_grads = sum([len(grads) for _, grads in six.iteritems(self._collected_grads_and_vars)])
        return total_number_of_grads % self._number_of_towers == 0

def did_towers_have_same_optimizer_calls(self):
    total_number_of_grads = sum([len(grads) for _, grads in six.iteritems(self._collected_grads_and_vars)])
    return total_number_of_grads % self._number_of_towers == 0

def _get_local_devices(device_type):
    local_device_protos = device_lib.list_local_devices()
    return [device.name for device in local_device_protos if device.device_type == device_type]

def _reduce_metric_variables(number_of_towers):
    """Aggregate local variables used in metrics into the first tower."""
    if number_of_towers == 1:
        return control_flow_ops.no_op(name='no_eval_metric_reduction')
    metric_variables = ops_lib.get_collection(ops_lib.GraphKeys.METRIC_VARIABLES)
    variables_per_tower = len(metric_variables) // number_of_towers
    if len(metric_variables) % number_of_towers != 0:
        raise ValueError('Different `EstimatorSpec.eval_metric_ops` across `model_fn()` calls. Expected {} local variables, but got {} instead.'.format(variables_per_tower * number_of_towers, len(metric_variables)))
    ops = []
    for i in range(0, variables_per_tower):
        next_replica_id = i + variables_per_tower
        replicas = [metric_variables[replica_id] for replica_id in range(next_replica_id, len(metric_variables), variables_per_tower)]
        reduce_op = state_ops.assign_add(metric_variables[i], math_ops.add_n(replicas))
        with ops_lib.control_dependencies([reduce_op]):
            for replica in replicas:
                zeros_for_replica = array_ops.zeros(array_ops.shape(replica), dtype=replica.dtype)
                zero_out_replica_op = state_ops.assign(replica, zeros_for_replica)
                ops.append(zero_out_replica_op)
    return control_flow_ops.group(*ops)

def metric_variable(shape, dtype, validate_shape=True, name=None):
    """Create variable in `GraphKeys.(LOCAL|METRIC_VARIABLES`) collections."""
    return variable_scope.variable(lambda: array_ops.zeros(shape, dtype), trainable=False, collections=[ops.GraphKeys.LOCAL_VARIABLES], validate_shape=validate_shape, name=name)

def save_image_with_heatmap(image, heatmap, indR, indG, indB, shape, heatmap_size):
    if not hasattr(save_image_with_heatmap, 'counter'):
        save_image_with_heatmap.counter = 0
    save_image_with_heatmap.counter += 1
    img_to_save = np.array(image.tolist())
    img_to_save = img_to_save.astype(np.uint8)
    file_name = 'raw_{}.jpg'.format(save_image_with_heatmap.counter)
    imsave(os.path.join(config.DEBUG_DIR, file_name), img_to_save)
    heatmap_all = (np.sum(heatmap, axis=0) * 255.0).astype(np.uint8)
    file_name = 'heatmap_{}.jpg'.format(save_image_with_heatmap.counter)
    imsave(os.path.join(config.DEBUG_DIR, file_name), heatmap_all)
    heatmap0 = (np.sum(heatmap[indR, ...], axis=0) * 255.0).astype(np.uint8)
    heatmap1 = (np.sum(heatmap[indG, ...], axis=0) * 255.0).astype(np.uint8)
    heatmap2 = (np.sum(heatmap[indB, ...], axis=0) * 255.0).astype(np.uint8) if len(indB) > 0 else np.zeros((heatmap_size, heatmap_size), dtype=np.float32)
    heatmap0 = imresize(heatmap0, shape, interp='lanczos')
    heatmap1 = imresize(heatmap1, shape, interp='lanczos')
    heatmap2 = imresize(heatmap2, shape, interp='lanczos')
    img_to_save = img_to_save / 2.0
    img_to_save[:, :, 0] = np.clip(img_to_save[:, :, 0] + heatmap0 + heatmap2, 0, 255)
    img_to_save[:, :, 1] = np.clip(img_to_save[:, :, 1] + heatmap1 + heatmap2, 0, 255)
    file_name = 'with_heatmap_{}.jpg'.format(save_image_with_heatmap.counter)
    imsave(os.path.join(config.DEBUG_DIR, file_name), img_to_save.astype(np.uint8))
    return save_image_with_heatmap.counter

def _save_image(image):
    if not hasattr(save_image_with_heatmap, 'counter'):
        save_image_with_heatmap.counter = 0
    save_image_with_heatmap.counter += 1
    img_to_save = np.array(image.tolist())
    img_to_save = img_to_save.astype(np.uint8)
    file_name = 'raw_{}.jpg'.format(save_image_with_heatmap.counter)
    imsave(os.path.join(config.DEBUG_DIR, file_name), img_to_save)
    return save_image_with_heatmap.counter

def np_draw_labelmap(pt, heatmap_sigma, heatmap_size, type='Gaussian'):
    img = np.zeros((heatmap_size, heatmap_size), dtype=np.float32)
    if pt[0] < 1 or pt[1] < 1:
        return (img, 0)
    ul = [int(pt[0] - 3 * heatmap_sigma), int(pt[1] - 3 * heatmap_sigma)]
    br = [int(pt[0] + 3 * heatmap_sigma + 1), int(pt[1] + 3 * heatmap_sigma + 1)]
    if ul[0] >= img.shape[1] or ul[1] >= img.shape[0] or br[0] < 0 or (br[1] < 0):
        return (img, 0)
    size = 6 * heatmap_sigma + 1
    x = np.arange(0, size, 1, float)
    y = x[:, np.newaxis]
    x0 = y0 = size // 2
    if type == 'Gaussian':
        g = np.exp(-((x - x0) ** 2 + (y - y0) ** 2) / (2 * heatmap_sigma ** 2))
    elif type == 'Cauchy':
        g = heatmap_sigma / ((x - x0) ** 2 + (y - y0) ** 2 + heatmap_sigma ** 2) ** 1.5
    g_x = (max(0, -ul[0]), min(br[0], img.shape[1]) - ul[0])
    g_y = (max(0, -ul[1]), min(br[1], img.shape[0]) - ul[1])
    img_x = (max(0, ul[0]), min(br[0], img.shape[1]))
    img_y = (max(0, ul[1]), min(br[1], img.shape[0]))
    img[img_y[0]:img_y[1], img_x[0]:img_x[1]] = g[g_y[0]:g_y[1], g_x[0]:g_x[1]]
    return (img, 1)

def preprocess_image(image, classid, shape, output_height, output_width, key_x, key_y, key_v, norm_table, is_training=False, data_format='NCHW', category='*', bbox_border=25.0, heatmap_sigma=1.0, heatmap_size=64, return_keypoints=False, resize_side_min=_RESIZE_SIDE_MIN, resize_side_max=_RESIZE_SIDE_MAX):
    """Preprocesses the given image.

  Args:
    image: A `Tensor` representing an image of arbitrary size.
    output_height: The height of the image after preprocessing.
    output_width: The width of the image after preprocessing.
    is_training: `True` if we're preprocessing the image for training and
      `False` otherwise.
    resize_side_min: The lower bound for the smallest side of the image for
      aspect-preserving resizing. If `is_training` is `False`, then this value
      is used for rescaling.
    resize_side_max: The upper bound for the smallest side of the image for
      aspect-preserving resizing. If `is_training` is `False`, this value is
      ignored. Otherwise, the resize side is sampled from
        [resize_size_min, resize_size_max].

  Returns:
    A preprocessed image.
  """
    if is_training:
        return preprocess_for_train(image, classid, shape, output_height, output_width, key_x, key_y, key_v, norm_table, data_format, category, bbox_border, heatmap_sigma, heatmap_size, return_keypoints, resize_side_min, resize_side_max)
    else:
        return preprocess_for_eval(image, classid, shape, output_height, output_width, key_x, key_y, key_v, norm_table, data_format, category, bbox_border, heatmap_sigma, heatmap_size, min(output_height, output_width))

