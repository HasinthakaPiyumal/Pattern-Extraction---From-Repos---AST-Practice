# Cluster 2

def mkstemp(suffix, dir=None):
    fd, path = tempfile.mkstemp(suffix=f'{suffix}', dir=dir)
    os.close(fd)
    return Path(path)

def show_img_with_mask(img, mask):
    if np.max(mask) == 1:
        mask = np.uint8(mask * 255)
    dpi = plt.rcParams['figure.dpi']
    height, width = img.shape[:2]
    plt.figure(figsize=(width / dpi / 0.77, height / dpi / 0.77))
    plt.imshow(img)
    plt.axis('off')
    show_mask(plt.gca(), mask, random_color=False)
    tmp_p = mkstemp('.png')
    plt.savefig(tmp_p, bbox_inches='tight', pad_inches=0)
    plt.close()
    return iio.imread(tmp_p)

def show_img_with_point(img, point_coords, point_labels):
    dpi = plt.rcParams['figure.dpi']
    height, width = img.shape[:2]
    plt.figure(figsize=(width / dpi / 0.77, height / dpi / 0.77))
    plt.imshow(img)
    plt.axis('off')
    show_points(plt.gca(), point_coords, point_labels, size=(width * 0.04) ** 2)
    tmp_p = mkstemp('.png')
    plt.savefig(tmp_p, bbox_inches='tight', pad_inches=0)
    plt.close()
    return iio.imread(tmp_p)

def show_img_with_box(img, box):
    dpi = plt.rcParams['figure.dpi']
    height, width = img.shape[:2]
    fig, ax = plt.subplots(1, figsize=(width / dpi / 0.77, height / dpi / 0.77))
    ax.imshow(img)
    ax.axis('off')
    x1, y1, w, h = box
    rect = patches.Rectangle((x1, y1), w, h, linewidth=2, edgecolor='r', facecolor='none')
    ax.add_patch(rect)
    tmp_p = mkstemp('.png')
    fig.savefig(tmp_p, bbox_inches='tight', pad_inches=0)
    plt.close()
    return iio.imread(tmp_p)

def mkstemp(suffix, dir=None):
    fd, path = tempfile.mkstemp(suffix=f'{suffix}', dir=dir)
    os.close(fd)
    return Path(path)

def show_img_with_mask(img, mask):
    if np.max(mask) == 1:
        mask = np.uint8(mask * 255)
    dpi = plt.rcParams['figure.dpi']
    height, width = img.shape[:2]
    plt.figure(figsize=(width / dpi / 0.77, height / dpi / 0.77))
    plt.imshow(img)
    plt.axis('off')
    show_mask(plt.gca(), mask, random_color=False)
    tmp_p = mkstemp('.png')
    plt.savefig(tmp_p, bbox_inches='tight', pad_inches=0)
    plt.close()
    return iio.imread(tmp_p)

def show_img_with_point(img, point_coords, point_labels):
    dpi = plt.rcParams['figure.dpi']
    height, width = img.shape[:2]
    plt.figure(figsize=(width / dpi / 0.77, height / dpi / 0.77))
    plt.imshow(img)
    plt.axis('off')
    show_points(plt.gca(), point_coords, point_labels, size=(width * 0.04) ** 2)
    tmp_p = mkstemp('.png')
    plt.savefig(tmp_p, bbox_inches='tight', pad_inches=0)
    plt.close()
    return iio.imread(tmp_p)

def show_img_with_box(img, box):
    dpi = plt.rcParams['figure.dpi']
    height, width = img.shape[:2]
    fig, ax = plt.subplots(1, figsize=(width / dpi / 0.77, height / dpi / 0.77))
    ax.imshow(img)
    ax.axis('off')
    x1, y1, w, h = box
    rect = patches.Rectangle((x1, y1), w, h, linewidth=2, edgecolor='r', facecolor='none')
    ax.add_patch(rect)
    tmp_p = mkstemp('.png')
    fig.savefig(tmp_p, bbox_inches='tight', pad_inches=0)
    plt.close()
    return iio.imread(tmp_p)

def get_random_shape(edge_num=9, ratio=0.7, width=432, height=240):
    """
      There is the initial point and 3 points per cubic bezier curve. 
      Thus, the curve will only pass though n points, which will be the sharp edges.
      The other 2 modify the shape of the bezier curve.
      edge_num, Number of possibly sharp edges
      points_num, number of points in the Path
      ratio, (0, 1) magnitude of the perturbation from the unit circle, 
    """
    points_num = edge_num * 3 + 1
    angles = np.linspace(0, 2 * np.pi, points_num)
    codes = np.full(points_num, Path.CURVE4)
    codes[0] = Path.MOVETO
    verts = np.stack((np.cos(angles), np.sin(angles))).T * (2 * ratio * np.random.random(points_num) + 1 - ratio)[:, None]
    verts[-1, :] = verts[0, :]
    path = Path(verts, codes)
    fig = plt.figure()
    ax = fig.add_subplot(111)
    patch = patches.PathPatch(path, facecolor='black', lw=2)
    ax.add_patch(patch)
    ax.set_xlim(np.min(verts) * 1.1, np.max(verts) * 1.1)
    ax.set_ylim(np.min(verts) * 1.1, np.max(verts) * 1.1)
    ax.axis('off')
    fig.canvas.draw()
    data = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
    data = data.reshape(fig.canvas.get_width_height()[::-1] + (3,))
    plt.close(fig)
    data = cv2.resize(data, (width, height))[:, :, 0]
    data = (1 - np.array(data > 0).astype(np.uint8)) * 255
    corrdinates = np.where(data > 0)
    xmin, xmax, ymin, ymax = (np.min(corrdinates[0]), np.max(corrdinates[0]), np.min(corrdinates[1]), np.max(corrdinates[1]))
    region = Image.fromarray(data).crop((ymin, xmin, ymax, xmax))
    return region

def mkstemp(suffix, dir=None):
    fd, path = tempfile.mkstemp(suffix=f'{suffix}', dir=dir)
    os.close(fd)
    return Path(path)

def get_masked_img(img, w, h, features, orig_h, orig_w, input_h, input_w, dilate_kernel_size):
    point_coords = [w, h]
    point_labels = [1]
    model['sam'].is_image_set = True
    model['sam'].features = features
    model['sam'].orig_h = orig_h
    model['sam'].orig_w = orig_w
    model['sam'].input_h = input_h
    model['sam'].input_w = input_w
    print(point_coords)
    masks, _, _ = model['sam'].predict(point_coords=np.array([point_coords]), point_labels=np.array(point_labels), multimask_output=True)
    masks = masks.astype(np.uint8) * 255
    if dilate_kernel_size is not None:
        masks = [dilate_mask(mask, dilate_kernel_size) for mask in masks]
    else:
        masks = [mask for mask in masks]
    figs = []
    for idx, mask in enumerate(masks):
        tmp_p = mkstemp('.png')
        dpi = plt.rcParams['figure.dpi']
        height, width = img.shape[:2]
        fig = plt.figure(figsize=(width / dpi / 0.77, height / dpi / 0.77))
        plt.imshow(img)
        plt.axis('off')
        show_points(plt.gca(), [point_coords], point_labels, size=(width * 0.04) ** 2)
        show_mask(plt.gca(), mask, random_color=False)
        plt.tight_layout()
        plt.savefig(tmp_p, bbox_inches='tight', pad_inches=0)
        figs.append(fig)
        plt.close()
    return (*figs, *masks)

def get_select_coords(img, evt: gr.SelectData):
    dpi = plt.rcParams['figure.dpi']
    height, width = img.shape[:2]
    fig = plt.figure(figsize=(width / dpi / 0.77, height / dpi / 0.77))
    plt.imshow(img)
    plt.axis('off')
    plt.tight_layout()
    show_points(plt.gca(), [[evt.index[0], evt.index[1]]], [1], size=(width * 0.04) ** 2)
    return (evt.index[0], evt.index[1], fig)

def mouse_callback(event, x, y, flags, param):
    nonlocal last_point, keep_looping, img
    if event == cv2.EVENT_LBUTTONDOWN:
        if last_point:
            cv2.circle(img, tuple(last_point), 5, (0, 0, 0), -1)
        last_point = [x, y]
        cv2.circle(img, tuple(last_point), 5, (0, 0, 255), -1)
        cv2.imshow('image', img)
    elif event == cv2.EVENT_RBUTTONDOWN:
        keep_looping = False

def main(args):
    config = load_yaml(args.config)
    latents_dir = os.path.join(args.outpath, 'latents')
    os.makedirs(latents_dir, exist_ok=True)
    global_worst_dir = os.path.join(args.outpath, 'global_worst')
    os.makedirs(global_worst_dir, exist_ok=True)
    global_best_dir = os.path.join(args.outpath, 'global_best')
    os.makedirs(global_best_dir, exist_ok=True)
    worst_best_by_best_worst_score_diff_max_dir = os.path.join(args.outpath, 'worst_best_by_real', 'best_worst_score_diff_max')
    os.makedirs(worst_best_by_best_worst_score_diff_max_dir, exist_ok=True)
    worst_best_by_best_worst_score_diff_min_dir = os.path.join(args.outpath, 'worst_best_by_real', 'best_worst_score_diff_min')
    os.makedirs(worst_best_by_best_worst_score_diff_min_dir, exist_ok=True)
    worst_best_by_real_best_score_diff_max_dir = os.path.join(args.outpath, 'worst_best_by_real', 'real_best_score_diff_max')
    os.makedirs(worst_best_by_real_best_score_diff_max_dir, exist_ok=True)
    worst_best_by_real_best_score_diff_min_dir = os.path.join(args.outpath, 'worst_best_by_real', 'real_best_score_diff_min')
    os.makedirs(worst_best_by_real_best_score_diff_min_dir, exist_ok=True)
    worst_best_by_real_worst_score_diff_max_dir = os.path.join(args.outpath, 'worst_best_by_real', 'real_worst_score_diff_max')
    os.makedirs(worst_best_by_real_worst_score_diff_max_dir, exist_ok=True)
    worst_best_by_real_worst_score_diff_min_dir = os.path.join(args.outpath, 'worst_best_by_real', 'real_worst_score_diff_min')
    os.makedirs(worst_best_by_real_worst_score_diff_min_dir, exist_ok=True)
    if not args.only_report:
        block_idx = InceptionV3.BLOCK_INDEX_BY_DIM[2048]
        inception_model = InceptionV3([block_idx]).eval().cuda()
        dataset = PrecomputedInpaintingResultsDataset(args.datadir, args.predictdir, **config.dataset_kwargs)
        real2vector_cache = {}
        real_features = []
        fake_features = []
        orig_fnames = []
        mask_fnames = []
        mask2real_fname = {}
        mask2fake_fname = {}
        for batch_i, batch in enumerate(dataset):
            orig_img_fname = dataset.img_filenames[batch_i]
            mask_fname = dataset.mask_filenames[batch_i]
            fake_fname = dataset.pred_filenames[batch_i]
            mask2real_fname[mask_fname] = orig_img_fname
            mask2fake_fname[mask_fname] = fake_fname
            cur_real_vector = real2vector_cache.get(orig_img_fname, None)
            if cur_real_vector is None:
                with torch.no_grad():
                    in_img = torch.from_numpy(batch['image'][None, ...]).cuda()
                    cur_real_vector = inception_model(in_img)[0].squeeze(-1).squeeze(-1).cpu().numpy()
                real2vector_cache[orig_img_fname] = cur_real_vector
            pred_img = torch.from_numpy(batch['inpainted'][None, ...]).cuda()
            cur_fake_vector = inception_model(pred_img)[0].squeeze(-1).squeeze(-1).cpu().numpy()
            real_features.append(cur_real_vector)
            fake_features.append(cur_fake_vector)
            orig_fnames.append(orig_img_fname)
            mask_fnames.append(mask_fname)
        ids_features = np.concatenate(real_features + fake_features, axis=0)
        ids_labels = np.array([1] * len(real_features) + [0] * len(fake_features))
        with open(os.path.join(latents_dir, 'featues.pkl'), 'wb') as f:
            pickle.dump(ids_features, f, protocol=3)
        with open(os.path.join(latents_dir, 'labels.pkl'), 'wb') as f:
            pickle.dump(ids_labels, f, protocol=3)
        with open(os.path.join(latents_dir, 'orig_fnames.pkl'), 'wb') as f:
            pickle.dump(orig_fnames, f, protocol=3)
        with open(os.path.join(latents_dir, 'mask_fnames.pkl'), 'wb') as f:
            pickle.dump(mask_fnames, f, protocol=3)
        with open(os.path.join(latents_dir, 'mask2real_fname.pkl'), 'wb') as f:
            pickle.dump(mask2real_fname, f, protocol=3)
        with open(os.path.join(latents_dir, 'mask2fake_fname.pkl'), 'wb') as f:
            pickle.dump(mask2fake_fname, f, protocol=3)
        svm = sklearn.svm.LinearSVC(dual=False)
        svm.fit(ids_features, ids_labels)
        pred_scores = svm.decision_function(ids_features)
        real_scores = pred_scores[:len(real_features)]
        fake_scores = pred_scores[len(real_features):]
        with open(os.path.join(latents_dir, 'pred_scores.pkl'), 'wb') as f:
            pickle.dump(pred_scores, f, protocol=3)
        with open(os.path.join(latents_dir, 'real_scores.pkl'), 'wb') as f:
            pickle.dump(real_scores, f, protocol=3)
        with open(os.path.join(latents_dir, 'fake_scores.pkl'), 'wb') as f:
            pickle.dump(fake_scores, f, protocol=3)
    else:
        with open(os.path.join(latents_dir, 'orig_fnames.pkl'), 'rb') as f:
            orig_fnames = pickle.load(f)
        with open(os.path.join(latents_dir, 'mask_fnames.pkl'), 'rb') as f:
            mask_fnames = pickle.load(f)
        with open(os.path.join(latents_dir, 'mask2real_fname.pkl'), 'rb') as f:
            mask2real_fname = pickle.load(f)
        with open(os.path.join(latents_dir, 'mask2fake_fname.pkl'), 'rb') as f:
            mask2fake_fname = pickle.load(f)
        with open(os.path.join(latents_dir, 'real_scores.pkl'), 'rb') as f:
            real_scores = pickle.load(f)
        with open(os.path.join(latents_dir, 'fake_scores.pkl'), 'rb') as f:
            fake_scores = pickle.load(f)
    real_info = pd.DataFrame(data=[dict(real_fname=fname, real_score=score) for fname, score in zip(orig_fnames, real_scores)])
    real_info.set_index('real_fname', drop=True, inplace=True)
    fake_info = pd.DataFrame(data=[dict(mask_fname=fname, fake_fname=mask2fake_fname[fname], real_fname=mask2real_fname[fname], fake_score=score) for fname, score in zip(mask_fnames, fake_scores)])
    fake_info = fake_info.join(real_info, on='real_fname', how='left')
    fake_info.drop_duplicates(['fake_fname', 'real_fname'], inplace=True)
    fake_stats_by_real = fake_info.groupby('real_fname')['fake_score'].describe()[['mean', 'std']].rename({'mean': 'mean_fake_by_real', 'std': 'std_fake_by_real'}, axis=1)
    fake_info = fake_info.join(fake_stats_by_real, on='real_fname', rsuffix='stat_by_real')
    fake_info.drop_duplicates(['fake_fname', 'real_fname'], inplace=True)
    fake_info.to_csv(os.path.join(latents_dir, 'join_scores_table.csv'), sep='\t', index=False)
    fake_scores_table = fake_info.set_index('mask_fname')['fake_score'].to_frame()
    real_scores_table = fake_info.set_index('real_fname')['real_score'].drop_duplicates().to_frame()
    fig, (ax1, ax2) = plt.subplots(1, 2)
    ax1.hist(fake_scores)
    ax2.hist(real_scores)
    fig.tight_layout()
    fig.savefig(os.path.join(args.outpath, 'global_scores_hist.png'))
    plt.close(fig)
    global_worst_masks = fake_info.sort_values('fake_score', ascending=True)['mask_fname'].iloc[:config.take_global_top].to_list()
    global_best_masks = fake_info.sort_values('fake_score', ascending=False)['mask_fname'].iloc[:config.take_global_top].to_list()
    save_global_samples(global_worst_masks, mask2real_fname, mask2fake_fname, global_worst_dir, real_scores_table, fake_scores_table)
    save_global_samples(global_best_masks, mask2real_fname, mask2fake_fname, global_best_dir, real_scores_table, fake_scores_table)
    worst_samples_by_real = fake_info.groupby('real_fname').apply(lambda d: d.set_index('mask_fname')['fake_score'].idxmin()).to_frame().rename({0: 'worst'}, axis=1)
    best_samples_by_real = fake_info.groupby('real_fname').apply(lambda d: d.set_index('mask_fname')['fake_score'].idxmax()).to_frame().rename({0: 'best'}, axis=1)
    worst_best_by_real = pd.concat([worst_samples_by_real, best_samples_by_real], axis=1)
    worst_best_by_real = worst_best_by_real.join(fake_scores_table.rename({'fake_score': 'worst_score'}, axis=1), on='worst')
    worst_best_by_real = worst_best_by_real.join(fake_scores_table.rename({'fake_score': 'best_score'}, axis=1), on='best')
    worst_best_by_real = worst_best_by_real.join(real_scores_table)
    worst_best_by_real['best_worst_score_diff'] = worst_best_by_real['best_score'] - worst_best_by_real['worst_score']
    worst_best_by_real['real_best_score_diff'] = worst_best_by_real['real_score'] - worst_best_by_real['best_score']
    worst_best_by_real['real_worst_score_diff'] = worst_best_by_real['real_score'] - worst_best_by_real['worst_score']
    worst_best_by_best_worst_score_diff_min = worst_best_by_real.sort_values('best_worst_score_diff', ascending=True).iloc[:config.take_worst_best_top]
    worst_best_by_best_worst_score_diff_max = worst_best_by_real.sort_values('best_worst_score_diff', ascending=False).iloc[:config.take_worst_best_top]
    save_samples_by_real(worst_best_by_best_worst_score_diff_min, mask2fake_fname, fake_info, worst_best_by_best_worst_score_diff_min_dir)
    save_samples_by_real(worst_best_by_best_worst_score_diff_max, mask2fake_fname, fake_info, worst_best_by_best_worst_score_diff_max_dir)
    worst_best_by_real_best_score_diff_min = worst_best_by_real.sort_values('real_best_score_diff', ascending=True).iloc[:config.take_worst_best_top]
    worst_best_by_real_best_score_diff_max = worst_best_by_real.sort_values('real_best_score_diff', ascending=False).iloc[:config.take_worst_best_top]
    save_samples_by_real(worst_best_by_real_best_score_diff_min, mask2fake_fname, fake_info, worst_best_by_real_best_score_diff_min_dir)
    save_samples_by_real(worst_best_by_real_best_score_diff_max, mask2fake_fname, fake_info, worst_best_by_real_best_score_diff_max_dir)
    worst_best_by_real_worst_score_diff_min = worst_best_by_real.sort_values('real_worst_score_diff', ascending=True).iloc[:config.take_worst_best_top]
    worst_best_by_real_worst_score_diff_max = worst_best_by_real.sort_values('real_worst_score_diff', ascending=False).iloc[:config.take_worst_best_top]
    save_samples_by_real(worst_best_by_real_worst_score_diff_min, mask2fake_fname, fake_info, worst_best_by_real_worst_score_diff_min_dir)
    save_samples_by_real(worst_best_by_real_worst_score_diff_max, mask2fake_fname, fake_info, worst_best_by_real_worst_score_diff_max_dir)
    overlapping_mask_fname_pairs = []
    overlapping_mask_fname_score_diffs = []
    for cur_real_fname in orig_fnames:
        cur_fakes_info = fake_info[fake_info['real_fname'] == cur_real_fname]
        cur_mask_fnames = sorted(cur_fakes_info['mask_fname'].unique())
        cur_mask_pairs_and_scores = Parallel(args.n_jobs)((delayed(extract_overlapping_masks)(cur_mask_fnames, i, fake_scores_table) for i in range(len(cur_mask_fnames) - 1)))
        for cur_pairs, cur_scores in cur_mask_pairs_and_scores:
            overlapping_mask_fname_pairs.extend(cur_pairs)
            overlapping_mask_fname_score_diffs.extend(cur_scores)
    overlapping_mask_fname_pairs = np.asarray(overlapping_mask_fname_pairs)
    overlapping_mask_fname_score_diffs = np.asarray(overlapping_mask_fname_score_diffs)
    overlapping_sort_idx = np.argsort(overlapping_mask_fname_score_diffs)
    overlapping_mask_fname_pairs = overlapping_mask_fname_pairs[overlapping_sort_idx]
    overlapping_mask_fname_score_diffs = overlapping_mask_fname_score_diffs[overlapping_sort_idx]

def generate_colors(nlabels, type='bright', first_color_black=False, last_color_black=True, verbose=False):
    """
    Creates a random colormap to be used together with matplotlib. Useful for segmentation tasks
    :param nlabels: Number of labels (size of colormap)
    :param type: 'bright' for strong colors, 'soft' for pastel colors
    :param first_color_black: Option to use first color as black, True or False
    :param last_color_black: Option to use last color as black, True or False
    :param verbose: Prints the number of labels and shows the colormap. True or False
    :return: colormap for matplotlib
    """
    if type not in ('bright', 'soft'):
        print('Please choose "bright" or "soft" for type')
        return
    if verbose:
        print('Number of labels: ' + str(nlabels))
    if type == 'bright':
        randHSVcolors = [(np.random.uniform(low=0.0, high=1), np.random.uniform(low=0.2, high=1), np.random.uniform(low=0.9, high=1)) for i in range(nlabels)]
        randRGBcolors = []
        for HSVcolor in randHSVcolors:
            randRGBcolors.append(colorsys.hsv_to_rgb(HSVcolor[0], HSVcolor[1], HSVcolor[2]))
        if first_color_black:
            randRGBcolors[0] = [0, 0, 0]
        if last_color_black:
            randRGBcolors[-1] = [0, 0, 0]
        random_colormap = LinearSegmentedColormap.from_list('new_map', randRGBcolors, N=nlabels)
    if type == 'soft':
        low = 0.6
        high = 0.95
        randRGBcolors = [(np.random.uniform(low=low, high=high), np.random.uniform(low=low, high=high), np.random.uniform(low=low, high=high)) for i in range(nlabels)]
        if first_color_black:
            randRGBcolors[0] = [0, 0, 0]
        if last_color_black:
            randRGBcolors[-1] = [0, 0, 0]
        random_colormap = LinearSegmentedColormap.from_list('new_map', randRGBcolors, N=nlabels)
    if verbose:
        from matplotlib import colors, colorbar
        from matplotlib import pyplot as plt
        fig, ax = plt.subplots(1, 1, figsize=(15, 0.5))
        bounds = np.linspace(0, nlabels, nlabels + 1)
        norm = colors.BoundaryNorm(bounds, nlabels)
        cb = colorbar.ColorbarBase(ax, cmap=random_colormap, norm=norm, spacing='proportional', ticks=None, boundaries=bounds, format='%1i', orientation=u'horizontal')
    return (randRGBcolors, random_colormap)

def _compute_statistics_of_path(path, model, batch_size, dims, cuda):
    if path.endswith('.npz'):
        f = np.load(path)
        m, s = (f['mu'][:], f['sigma'][:])
        f.close()
    else:
        path = pathlib.Path(path)
        files = list(path.glob('*.jpg')) + list(path.glob('*.png'))
        m, s = calculate_activation_statistics(files, model, batch_size, dims, cuda)
    return (m, s)

def _compute_statistics_of_images(images, model, batch_size, dims, cuda, keep_size=False):
    if isinstance(images, list):
        m, s = calculate_activation_statistics(images, model, batch_size, dims, cuda, keep_size=keep_size)
        return (m, s)
    else:
        raise ValueError

def generate_colors(nlabels, type='bright', first_color_black=False, last_color_black=True, verbose=False):
    """
    Creates a random colormap to be used together with matplotlib. Useful for segmentation tasks
    :param nlabels: Number of labels (size of colormap)
    :param type: 'bright' for strong colors, 'soft' for pastel colors
    :param first_color_black: Option to use first color as black, True or False
    :param last_color_black: Option to use last color as black, True or False
    :param verbose: Prints the number of labels and shows the colormap. True or False
    :return: colormap for matplotlib
    """
    if type not in ('bright', 'soft'):
        print('Please choose "bright" or "soft" for type')
        return
    if verbose:
        print('Number of labels: ' + str(nlabels))
    if type == 'bright':
        randHSVcolors = [(np.random.uniform(low=0.0, high=1), np.random.uniform(low=0.2, high=1), np.random.uniform(low=0.9, high=1)) for i in range(nlabels)]
        randRGBcolors = []
        for HSVcolor in randHSVcolors:
            randRGBcolors.append(colorsys.hsv_to_rgb(HSVcolor[0], HSVcolor[1], HSVcolor[2]))
        if first_color_black:
            randRGBcolors[0] = [0, 0, 0]
        if last_color_black:
            randRGBcolors[-1] = [0, 0, 0]
        random_colormap = LinearSegmentedColormap.from_list('new_map', randRGBcolors, N=nlabels)
    if type == 'soft':
        low = 0.6
        high = 0.95
        randRGBcolors = [(np.random.uniform(low=low, high=high), np.random.uniform(low=low, high=high), np.random.uniform(low=low, high=high)) for i in range(nlabels)]
        if first_color_black:
            randRGBcolors[0] = [0, 0, 0]
        if last_color_black:
            randRGBcolors[-1] = [0, 0, 0]
        random_colormap = LinearSegmentedColormap.from_list('new_map', randRGBcolors, N=nlabels)
    if verbose:
        from matplotlib import colors, colorbar
        from matplotlib import pyplot as plt
        fig, ax = plt.subplots(1, 1, figsize=(15, 0.5))
        bounds = np.linspace(0, nlabels, nlabels + 1)
        norm = colors.BoundaryNorm(bounds, nlabels)
        cb = colorbar.ColorbarBase(ax, cmap=random_colormap, norm=norm, spacing='proportional', ticks=None, boundaries=bounds, format='%1i', orientation=u'horizontal')
    return (randRGBcolors, random_colormap)

def _compute_statistics_of_path(path, model, batch_size, dims, cuda):
    if path.endswith('.npz'):
        f = np.load(path)
        m, s = (f['mu'][:], f['sigma'][:])
        f.close()
    else:
        path = pathlib.Path(path)
        files = list(path.glob('*.jpg')) + list(path.glob('*.png'))
        m, s = calculate_activation_statistics(files, model, batch_size, dims, cuda)
    return (m, s)

def _compute_statistics_of_images(images, model, batch_size, dims, cuda, keep_size=False):
    if isinstance(images, list):
        m, s = calculate_activation_statistics(images, model, batch_size, dims, cuda, keep_size=keep_size)
        return (m, s)
    else:
        raise ValueError

def imshow(x, title=None, cbar=False, figsize=None):
    plt.figure(figsize=figsize)
    plt.imshow(np.squeeze(x), interpolation='nearest', cmap='gray')
    if title:
        plt.title(title)
    if cbar:
        plt.colorbar()
    plt.show()

def surf(Z, cmap='rainbow', figsize=None):
    plt.figure(figsize=figsize)
    ax3 = plt.axes(projection='3d')
    w, h = Z.shape[:2]
    xx = np.arange(0, w, 1)
    yy = np.arange(0, h, 1)
    X, Y = np.meshgrid(xx, yy)
    ax3.plot_surface(X, Y, Z, cmap=cmap)
    plt.show()

def visualize_poses(poses, camera_coord_axis_order='DRB', size=0.1):
    """
    Args:
        poses : numpy.ndarray
            shape [B, 3/4, 4]

        size : float
            size of axis

        camera_coord_axis_order : str
            https://zhuanlan.zhihu.com/p/593204605
            how camera coordinate's xyz related to the camera view
            For example, 'DRB' means x->down, y->right, z->back. 
            ======================
            OpenCV/Colmap: RDF
            LLFF: DRB
            OpenGL/NeRF: RUB
            Blender: RUB
            Mitsuba/Pytorch3D: LUF

    """
    try:
        camera_front = camera_view_dir(camera_coord_axis_order.index('F'), 1)
    except:
        camera_front = camera_view_dir(camera_coord_axis_order.index('B'), -1)
    try:
        camera_right = camera_view_dir(camera_coord_axis_order.index('R'), 1)
    except:
        camera_right = camera_view_dir(camera_coord_axis_order.index('L'), -1)
    try:
        camera_up = camera_view_dir(camera_coord_axis_order.index('U'), 1)
    except:
        camera_up = camera_view_dir(camera_coord_axis_order.index('D'), -1)
    axes = trimesh.creation.axis(axis_length=4)
    box = trimesh.primitives.Box(extents=(2, 2, 2)).as_outline()
    box.colors = np.array([[128, 128, 128]] * len(box.entities))
    objects = [axes, box]
    if poses.shape[1] == 3:
        pad_values = np.array([0, 0, 0, 1.0])
        poses = np.pad(poses, ((0, 0), (0, 1), (0, 0)), mode='constant', constant_values=0)
        poses[:, -1, :] = pad_values
    for pose in poses:
        axes = trimesh.creation.axis(transform=pose, axis_length=size)
        objects.append(axes)
        pos = pose[:3, 3]
        up_left = pos + camera_front.pn * size * pose[:3, camera_front.axis] + camera_up.pn * size * pose[:3, camera_up.axis] - camera_right.pn * size * pose[:3, camera_right.axis]
        up_right = pos + camera_front.pn * size * pose[:3, camera_front.axis] + camera_up.pn * size * pose[:3, camera_up.axis] + camera_right.pn * size * pose[:3, camera_right.axis]
        down_left = pos + camera_front.pn * size * pose[:3, camera_front.axis] - camera_up.pn * size * pose[:3, camera_up.axis] - camera_right.pn * size * pose[:3, camera_right.axis]
        down_right = pos + camera_front.pn * size * pose[:3, camera_front.axis] - camera_up.pn * size * pose[:3, camera_up.axis] + camera_right.pn * size * pose[:3, camera_right.axis]
        dir = (up_left + up_right + down_left + down_right) / 4 - pos
        dir = dir / (np.linalg.norm(dir) + 1e-08)
        o = pos + dir * 2
        up_middle = (up_left + up_right) / 2
        segs = np.array([[pos, up_left], [pos, up_right], [pos, down_left], [pos, down_right], [up_left, up_right], [up_right, down_right], [down_right, down_left], [down_left, up_left], [pos, o], [pos, up_middle]])
        segs = trimesh.load_path(segs)
        objects.append(segs)
    trimesh.Scene(objects).show()

def plot_feature(feature, channel, save_path, flag='', vmin=None, vmax=None, colorbar=True):
    """
    Args:
        feature : torch.tensor or np.ndarry
            suppose in shape [N, C, H, W]

        channel : int or list of int
            channel for ploting

        save_path : str
            save path for visualizing results.
    """
    if isinstance(feature, torch.Tensor):
        feature = feature.detach().cpu().numpy()
    if isinstance(channel, int):
        channel = [channel]
    if not os.path.exists(save_path):
        os.mkdir(save_path)
    N, C, H, W = feature.shape
    for c in channel:
        for n in range(N):
            plt.imshow(feature[n, c], vmin=vmin, vmax=vmax)
            file_path = os.path.join(save_path, f'{flag}_agent_{n}_channel_{c}.png')
            if colorbar:
                plt.colorbar()
            plt.savefig(file_path, dpi=400)
            plt.close()
            print(f'Saving to {file_path}')

def visualize_poses(poses, camera_coord_axis_order='DRB', size=0.1):
    """
    Args:
        poses : numpy.ndarray
            shape [B, 3/4, 4]

        size : float
            size of axis

        camera_coord_axis_order : str
            https://zhuanlan.zhihu.com/p/593204605
            how camera coordinate's xyz related to the camera view
            For example, 'DRB' means x->down, y->right, z->back. 
            ======================
            OpenCV/Colmap: RDF
            LLFF: DRB
            OpenGL/NeRF: RUB
            Blender: RUB
            Mitsuba/Pytorch3D: LUF

    """
    try:
        camera_front = camera_view_dir(camera_coord_axis_order.index('F'), 1)
    except:
        camera_front = camera_view_dir(camera_coord_axis_order.index('B'), -1)
    try:
        camera_right = camera_view_dir(camera_coord_axis_order.index('R'), 1)
    except:
        camera_right = camera_view_dir(camera_coord_axis_order.index('L'), -1)
    try:
        camera_up = camera_view_dir(camera_coord_axis_order.index('U'), 1)
    except:
        camera_up = camera_view_dir(camera_coord_axis_order.index('D'), -1)
    axes = trimesh.creation.axis(axis_length=4)
    box = trimesh.primitives.Box(extents=(2, 2, 2)).as_outline()
    box.colors = np.array([[128, 128, 128]] * len(box.entities))
    objects = [axes, box]
    if poses.shape[1] == 3:
        pad_values = np.array([0, 0, 0, 1.0])
        poses = np.pad(poses, ((0, 0), (0, 1), (0, 0)), mode='constant', constant_values=0)
        poses[:, -1, :] = pad_values
    for pose in poses:
        axes = trimesh.creation.axis(transform=pose, axis_length=size)
        objects.append(axes)
        pos = pose[:3, 3]
        up_left = pos + camera_front.pn * size * pose[:3, camera_front.axis] + camera_up.pn * size * pose[:3, camera_up.axis] - camera_right.pn * size * pose[:3, camera_right.axis]
        up_right = pos + camera_front.pn * size * pose[:3, camera_front.axis] + camera_up.pn * size * pose[:3, camera_up.axis] + camera_right.pn * size * pose[:3, camera_right.axis]
        down_left = pos + camera_front.pn * size * pose[:3, camera_front.axis] - camera_up.pn * size * pose[:3, camera_up.axis] - camera_right.pn * size * pose[:3, camera_right.axis]
        down_right = pos + camera_front.pn * size * pose[:3, camera_front.axis] - camera_up.pn * size * pose[:3, camera_up.axis] + camera_right.pn * size * pose[:3, camera_right.axis]
        dir = (up_left + up_right + down_left + down_right) / 4 - pos
        dir = dir / (np.linalg.norm(dir) + 1e-08)
        o = pos + dir * 2
        up_middle = (up_left + up_right) / 2
        segs = np.array([[pos, up_left], [pos, up_right], [pos, down_left], [pos, down_right], [up_left, up_right], [up_right, down_right], [down_right, down_left], [down_left, up_left], [pos, o], [pos, up_middle]])
        segs = trimesh.load_path(segs)
        objects.append(segs)
    trimesh.Scene(objects).show()

def visualize(input, file_name, input_map=None, multi_traj=False, obj=None):
    plt.cla()
    plt.figure(figsize=(10, 6))
    plt.xlabel('X (Front of the car) [meters]')
    plt.ylabel('Y (Right of the car) [meters]')
    if multi_traj:
        cmap = plt.get_cmap('viridis')
        colors = [cmap(i / len(input)) for i in range(len(input))]
        for i in range(len(input)):
            if input[i][0] is not None:
                x_vals, y_vals = (input[i][:, 0], input[i][:, 1])
                plt.plot(x_vals, y_vals, 'b-', color=colors[i], label=f'Trajectory{i}', lw=5)
    else:
        x_vals, y_vals = zip(*input)
        plt.cla()
        plt.figure(figsize=(10, 6))
        plt.plot(x_vals, y_vals, 'b-', label='Trajectory', lw=5)
        plt.xlabel('X (Front of the car) [meters]')
        plt.ylabel('Y (Right of the car) [meters]')
    if input_map is not None:
        centerline = input_map['centerline']
        boundary = input_map['boundary']
        for i in range(len(centerline)):
            lane_vec = centerline[i]
            plt.plot([lane_vec[0], lane_vec[2]], [lane_vec[1], lane_vec[3]], color='green', linewidth=1)
            plt.scatter([lane_vec[0], lane_vec[2]], [lane_vec[1], lane_vec[3]], color='black', s=1)
        for i in range(len(boundary)):
            lane_vec = boundary[i]
            plt.plot([lane_vec[0], lane_vec[2]], [lane_vec[1], lane_vec[3]], color='red', linewidth=1)
            plt.scatter([lane_vec[0], lane_vec[2]], [lane_vec[1], lane_vec[3]], color='black', s=1)
    if obj is not None:
        for i in range(len(obj)):
            plt.fill(obj[i, :, 0], obj[i, :, 1], 'r', fill=True)
    plt.grid(True)
    plt.legend()
    plt.savefig(file_name)
    plt.show()
    return

