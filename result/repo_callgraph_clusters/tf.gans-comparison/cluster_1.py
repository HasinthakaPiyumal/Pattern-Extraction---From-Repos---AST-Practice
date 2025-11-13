# Cluster 1

def center_crop(im, output_size):
    output_height, output_width = output_size
    h, w = im.shape[:2]
    if h < output_height and w < output_width:
        raise ValueError('image is small')
    offset_h = int((h - output_height) / 2)
    offset_w = int((w - output_width) / 2)
    return im[offset_h:offset_h + output_height, offset_w:offset_w + output_width, :]

def plot(samples, shape=(4, 4), figratio=0.75):
    """only for square-size samples
    wh = sqrt(samples.size)
    figratio: small-size = 0.75 (default) / big-size = 1.0
    """
    if len(samples) != shape[0] * shape[1]:
        print('Error: # of samples = {} but shape is {}'.format(len(samples), shape))
        return
    h_figsize = shape[0] * figratio
    w_figsize = shape[1] * figratio
    fig = plt.figure(figsize=(w_figsize, h_figsize))
    gs = gridspec.GridSpec(shape[0], shape[1])
    gs.update(wspace=0.05, hspace=0.05)
    for i, sample in enumerate(samples):
        ax = plt.subplot(gs[i])
        plt.axis('off')
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        ax.set_aspect('equal')
        plt.imshow(sample)
    return fig

def merge(images, size):
    """merge images - burrowed from @carpedm20.

    checklist before/after imsave:
    * are images post-processed? for example - denormalization
    * is np.squeeze required? maybe for grayscale...
    """
    h, w = (images.shape[1], images.shape[2])
    if images.shape[3] in (3, 4):
        c = images.shape[3]
        img = np.zeros((h * size[0], w * size[1], c))
        for idx, image in enumerate(images):
            i = idx % size[1]
            j = idx // size[1]
            img[j * h:j * h + h, i * w:i * w + w, :] = image
        return img
    elif images.shape[3] == 1:
        img = np.zeros((h * size[0], w * size[1]))
        for idx, image in enumerate(images):
            i = idx % size[1]
            j = idx // size[1]
            img[j * h:j * h + h, i * w:i * w + w] = image[:, :, 0]
        return img
    else:
        raise ValueError('in merge(images,size) images parameter must have dimensions: HxW or HxWx3 or HxWx4')

def get_dataset(dataset_name):
    celebA_64 = './data/celebA_tfrecords/*.tfrecord'
    celebA_128 = './data/celebA_128_tfrecords/*.tfrecord'
    lsun_bedroom_128 = './data/lsun/bedroom_128_tfrecords/*.tfrecord'
    if dataset_name == 'celeba':
        path = celebA_128
        n_examples = 202599
    elif dataset_name == 'lsun':
        path = lsun_bedroom_128
        n_examples = 3033042
    else:
        raise ValueError('{} is does not supported. dataset must be celeba or lsun.'.format(dataset_name))
    return (path, n_examples)

