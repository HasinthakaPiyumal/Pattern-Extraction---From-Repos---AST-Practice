# Cluster 58

def make_constant_area_crop_batch(batch, **kwargs):
    crop_y, crop_x, crop_height, crop_width = make_constant_area_crop_params(img_height=batch['image'].shape[2], img_width=batch['image'].shape[3], **kwargs)
    batch['image'] = batch['image'][:, :, crop_y:crop_y + crop_height, crop_x:crop_x + crop_width]
    batch['mask'] = batch['mask'][:, :, crop_y:crop_y + crop_height, crop_x:crop_x + crop_width]
    return batch

def make_constant_area_crop_batch(batch, **kwargs):
    crop_y, crop_x, crop_height, crop_width = make_constant_area_crop_params(img_height=batch['image'].shape[2], img_width=batch['image'].shape[3], **kwargs)
    batch['image'] = batch['image'][:, :, crop_y:crop_y + crop_height, crop_x:crop_x + crop_width]
    batch['mask'] = batch['mask'][:, :, crop_y:crop_y + crop_height, crop_x:crop_x + crop_width]
    return batch

