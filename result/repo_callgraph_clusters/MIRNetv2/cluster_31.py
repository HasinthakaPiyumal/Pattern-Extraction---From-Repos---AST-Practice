# Cluster 31

def bundle_submissions_raw(submission_folder, session):
    """
    Bundles submission data for raw denoising

    submission_folder Folder where denoised images reside

    Output is written to <submission_folder>/bundled/. Please submit
    the content of this folder.
    """
    out_folder = os.path.join(submission_folder, session)
    try:
        os.mkdir(out_folder)
    except:
        pass
    israw = True
    eval_version = '1.0'
    for i in range(50):
        Idenoised = np.zeros((20,), dtype=np.object)
        for bb in range(20):
            filename = '%04d_%02d.mat' % (i + 1, bb + 1)
            s = sio.loadmat(os.path.join(submission_folder, filename))
            Idenoised_crop = s['Idenoised_crop']
            Idenoised[bb] = Idenoised_crop
        filename = '%04d.mat' % (i + 1)
        sio.savemat(os.path.join(out_folder, filename), {'Idenoised': Idenoised, 'israw': israw, 'eval_version': eval_version})

def bundle_submissions_srgb(submission_folder, session):
    """
    Bundles submission data for sRGB denoising
    
    submission_folder Folder where denoised images reside

    Output is written to <submission_folder>/bundled/. Please submit
    the content of this folder.
    """
    out_folder = os.path.join(submission_folder, session)
    try:
        os.mkdir(out_folder)
    except:
        pass
    israw = False
    eval_version = '1.0'
    for i in range(50):
        Idenoised = np.zeros((20,), dtype=np.object)
        for bb in range(20):
            filename = '%04d_%02d.mat' % (i + 1, bb + 1)
            s = sio.loadmat(os.path.join(submission_folder, filename))
            Idenoised_crop = s['Idenoised_crop']
            Idenoised[bb] = Idenoised_crop
        filename = '%04d.mat' % (i + 1)
        sio.savemat(os.path.join(out_folder, filename), {'Idenoised': Idenoised, 'israw': israw, 'eval_version': eval_version})

def bundle_submissions_srgb_v1(submission_folder, session):
    """
    Bundles submission data for sRGB denoising
    
    submission_folder Folder where denoised images reside

    Output is written to <submission_folder>/bundled/. Please submit
    the content of this folder.
    """
    out_folder = os.path.join(submission_folder, session)
    try:
        os.mkdir(out_folder)
    except:
        pass
    israw = False
    eval_version = '1.0'
    for i in range(50):
        Idenoised = np.zeros((20,), dtype=np.object)
        for bb in range(20):
            filename = '%04d_%d.mat' % (i + 1, bb + 1)
            s = sio.loadmat(os.path.join(submission_folder, filename))
            Idenoised_crop = s['Idenoised_crop']
            Idenoised[bb] = Idenoised_crop
        filename = '%04d.mat' % (i + 1)
        sio.savemat(os.path.join(out_folder, filename), {'Idenoised': Idenoised, 'israw': israw, 'eval_version': eval_version})

def generate_gaussian_kernel(kernel_size=13, sigma=1.6):
    """Generate Gaussian kernel used in `duf_downsample`.

    Args:
        kernel_size (int): Kernel size. Default: 13.
        sigma (float): Sigma of the Gaussian kernel. Default: 1.6.

    Returns:
        np.array: The Gaussian kernel.
    """
    from scipy.ndimage import filters as filters
    kernel = np.zeros((kernel_size, kernel_size))
    kernel[kernel_size // 2, kernel_size // 2] = 1
    return filters.gaussian_filter(kernel, sigma)

