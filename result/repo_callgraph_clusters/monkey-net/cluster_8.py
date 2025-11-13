# Cluster 8

class KPDataset(Dataset):
    """Dataset of detected keypoints"""

    def __init__(self, keypoints_array, num_frames):
        self.keypoints_array = keypoints_array
        self.transform = SelectRandomFrames(consequent=True, number_of_frames=num_frames)

    def __len__(self):
        return len(self.keypoints_array)

    def __getitem__(self, idx):
        keypoints = self.keypoints_array[idx]
        selected = self.transform(keypoints)
        selected = {k: np.concatenate([v[k][0] for v in selected], axis=0) for k in selected[0].keys()}
        return selected

def __len__(self):
    return len(self.keypoints_array)

class SelectRandomFrames(object):

    def __init__(self, consequent=False, number_of_frames=2):
        self.consequent = consequent
        self.number_of_frames = number_of_frames

    def __call__(self, clip):
        """
        Args:
        img (PIL.Image or numpy.ndarray): List of images for selection
        in format (h, w, c) in numpy.ndarray
        Returns:
        PIL.Image or numpy.ndarray: List of number_of_frames images
        """
        frame_count = len(clip)
        num_frames_to_select = self.number_of_frames
        if self.consequent:
            first_frame = np.random.choice(max(1, frame_count - num_frames_to_select + 1), size=1)[0]
            selected = clip[first_frame:first_frame + num_frames_to_select]
        else:
            selected_index = np.sort(np.random.choice(range(frame_count), replace=True, size=num_frames_to_select))
            selected = clip[selected_index]
        return selected

def __call__(self, clip):
    """
        Args:
        img (PIL.Image or numpy.ndarray): List of images for selection
        in format (h, w, c) in numpy.ndarray
        Returns:
        PIL.Image or numpy.ndarray: List of number_of_frames images
        """
    frame_count = len(clip)
    num_frames_to_select = self.number_of_frames
    if self.consequent:
        first_frame = np.random.choice(max(1, frame_count - num_frames_to_select + 1), size=1)[0]
        selected = clip[first_frame:first_frame + num_frames_to_select]
    else:
        selected_index = np.sort(np.random.choice(range(frame_count), replace=True, size=num_frames_to_select))
        selected = clip[selected_index]
    return selected

def read_video(name, image_shape):
    if name.lower().endswith('.png') or name.lower().endswith('.jpg'):
        image = io.imread(name)
        if len(image.shape) == 2 or image.shape[2] == 1:
            image = gray2rgb(image)
        if image.shape[2] == 4:
            image = image[..., :3]
        image = img_as_float32(image)
        video_array = np.moveaxis(image, 1, 0)
        video_array = video_array.reshape((-1,) + image_shape)
        video_array = np.moveaxis(video_array, 1, 2)
    elif name.lower().endswith('.gif') or name.lower().endswith('.mp4') or name.lower().endswith('.mov'):
        video = np.array(mimread(name))
        if len(video.shape) == 3:
            video = np.array([gray2rgb(frame) for frame in video])
        if video.shape[-1] == 4:
            video = video[..., :3]
        video_array = img_as_float32(video)
    else:
        raise Exception('Unknown file extensions  %s' % name)
    return video_array

class FramesDataset(Dataset):
    """Dataset of videos, videos can be represented as an image of concatenated frames, or in '.mp4','.gif' format"""

    def __init__(self, root_dir, augmentation_params, image_shape=(64, 64, 3), is_train=True, random_seed=0, pairs_list=None, transform=None):
        self.root_dir = root_dir
        self.images = os.listdir(root_dir)
        self.image_shape = tuple(image_shape)
        self.pairs_list = pairs_list
        if os.path.exists(os.path.join(root_dir, 'train')):
            assert os.path.exists(os.path.join(root_dir, 'test'))
            print('Use predefined train-test split.')
            train_images = os.listdir(os.path.join(root_dir, 'train'))
            test_images = os.listdir(os.path.join(root_dir, 'test'))
            self.root_dir = os.path.join(self.root_dir, 'train' if is_train else 'test')
        else:
            print('Use random train-test split.')
            train_images, test_images = train_test_split(self.images, random_state=random_seed, test_size=0.2)
        if is_train:
            self.images = train_images
        else:
            self.images = test_images
        if transform is None:
            if is_train:
                self.transform = AllAugmentationTransform(**augmentation_params)
            else:
                self.transform = VideoToTensor()
        else:
            self.transform = transform

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        img_name = os.path.join(self.root_dir, self.images[idx])
        video_array = read_video(img_name, image_shape=self.image_shape)
        out = self.transform(video_array)
        out['name'] = os.path.basename(img_name)
        return out

def __len__(self):
    return len(self.images)

class PairedDataset(Dataset):
    """
    Dataset of pairs for transfer.
    """

    def __init__(self, initial_dataset, number_of_pairs, seed=0):
        self.initial_dataset = initial_dataset
        pairs_list = self.initial_dataset.pairs_list
        np.random.seed(seed)
        if pairs_list is None:
            max_idx = min(number_of_pairs, len(initial_dataset))
            nx, ny = (max_idx, max_idx)
            xy = np.mgrid[:nx, :ny].reshape(2, -1).T
            number_of_pairs = min(xy.shape[0], number_of_pairs)
            self.pairs = xy.take(np.random.choice(xy.shape[0], number_of_pairs, replace=False), axis=0)
        else:
            images = self.initial_dataset.images
            name_to_index = {name: index for index, name in enumerate(images)}
            pairs = pd.read_csv(pairs_list)
            pairs = pairs[np.logical_and(pairs['source'].isin(images), pairs['driving'].isin(images))]
            number_of_pairs = min(pairs.shape[0], number_of_pairs)
            self.pairs = []
            self.start_frames = []
            for ind in range(number_of_pairs):
                self.pairs.append((name_to_index[pairs['driving'].iloc[ind]], name_to_index[pairs['source'].iloc[ind]]))

    def __len__(self):
        return len(self.pairs)

    def __getitem__(self, idx):
        pair = self.pairs[idx]
        first = self.initial_dataset[pair[0]]
        second = self.initial_dataset[pair[1]]
        first = {'driving_' + key: value for key, value in first.items()}
        second = {'source_' + key: value for key, value in second.items()}
        return {**first, **second}

def __init__(self, initial_dataset, number_of_pairs, seed=0):
    self.initial_dataset = initial_dataset
    pairs_list = self.initial_dataset.pairs_list
    np.random.seed(seed)
    if pairs_list is None:
        max_idx = min(number_of_pairs, len(initial_dataset))
        nx, ny = (max_idx, max_idx)
        xy = np.mgrid[:nx, :ny].reshape(2, -1).T
        number_of_pairs = min(xy.shape[0], number_of_pairs)
        self.pairs = xy.take(np.random.choice(xy.shape[0], number_of_pairs, replace=False), axis=0)
    else:
        images = self.initial_dataset.images
        name_to_index = {name: index for index, name in enumerate(images)}
        pairs = pd.read_csv(pairs_list)
        pairs = pairs[np.logical_and(pairs['source'].isin(images), pairs['driving'].isin(images))]
        number_of_pairs = min(pairs.shape[0], number_of_pairs)
        self.pairs = []
        self.start_frames = []
        for ind in range(number_of_pairs):
            self.pairs.append((name_to_index[pairs['driving'].iloc[ind]], name_to_index[pairs['source'].iloc[ind]]))

def __len__(self):
    return len(self.pairs)

class Visualizer:

    def __init__(self, kp_size=2, draw_border=False, colormap='gist_rainbow'):
        self.kp_size = kp_size
        self.draw_border = draw_border
        self.colormap = plt.get_cmap(colormap)

    def draw_video_with_kp(self, video, kp_array):
        video_array = np.copy(video)
        spatial_size = np.array(video_array.shape[2:0:-1])[np.newaxis, np.newaxis]
        kp_array = spatial_size * (kp_array + 1) / 2
        num_kp = kp_array.shape[1]
        for i in range(len(video_array)):
            for kp_ind, kp in enumerate(kp_array[i]):
                rr, cc = circle(kp[1], kp[0], self.kp_size, shape=video_array.shape[1:3])
                video_array[i][rr, cc] = np.array(self.colormap(kp_ind / num_kp))[:3]
        return video_array

    def create_video_column_with_kp(self, video, kp):
        video_array = np.array([self.draw_video_with_kp(v, k) for v, k in zip(video, kp)])
        return self.create_video_column(video_array)

    def create_video_column(self, videos):
        if self.draw_border:
            videos = np.copy(videos)
            videos[:, :, [0, -1]] = (1, 1, 1)
            videos[:, :, :, [0, -1]] = (1, 1, 1)
        return np.concatenate(list(videos), axis=1)

    def create_image_grid(self, *args):
        out = []
        for arg in args:
            if type(arg) == tuple:
                out.append(self.create_video_column_with_kp(arg[0], arg[1]))
            else:
                out.append(self.create_video_column(arg))
        return np.concatenate(out, axis=2)

    def visualize_transfer(self, driving_video, source_image, out):
        out_video_batch = out['video_prediction'].data.cpu().numpy()
        appearance_deformed_batch = out['video_deformed'].data.cpu().numpy()
        motion_video_batch = driving_video.data.cpu().numpy()
        appearance_video_batch = source_image[:, :, 0:1].data.cpu().repeat(1, 1, out_video_batch.shape[2], 1, 1).numpy()
        video_first_frame = driving_video[:, :, 0:1].data.cpu().repeat(1, 1, out_video_batch.shape[2], 1, 1).numpy()
        kp_video = out['kp_driving']['mean'].data.cpu().numpy()
        kp_appearance = out['kp_source']['mean'].data.cpu().repeat(1, out_video_batch.shape[2], 1, 1).numpy()
        kp_norm = out['kp_norm']['mean'].data.cpu().numpy()
        kp_video_first = out['kp_driving']['mean'][:, :1].data.cpu().repeat(1, out_video_batch.shape[2], 1, 1).numpy()
        video_first_frame = np.transpose(video_first_frame, [0, 2, 3, 4, 1])
        out_video_batch = np.transpose(out_video_batch, [0, 2, 3, 4, 1])
        motion_video_batch = np.transpose(motion_video_batch, [0, 2, 3, 4, 1])
        appearance_video_batch = np.transpose(appearance_video_batch, [0, 2, 3, 4, 1])
        appearance_deformed_batch = np.transpose(appearance_deformed_batch, [0, 2, 3, 4, 1])
        image = self.create_image_grid((appearance_video_batch, kp_appearance), (video_first_frame, kp_video_first), (motion_video_batch, kp_video), (out_video_batch, kp_norm), out_video_batch, appearance_deformed_batch)
        image = (255 * image).astype(np.uint8)
        return image

    def visualize_reconstruction(self, inp, out):
        out_video_batch = out['video_prediction'].data.cpu().numpy()
        if 'driving' in inp:
            gt_video_batch = inp['driving'].data.cpu().numpy()
        else:
            gt_video_batch = inp['video'].data.cpu().numpy()
        appearance_deformed_batch = out['video_deformed'].data.cpu().numpy()
        appearance_video_batch = inp['source'].data.cpu().repeat(1, 1, out_video_batch.shape[2], 1, 1).numpy()
        kp_video = out['kp_driving']['mean'].data.cpu().numpy()
        kp_appearance = out['kp_source']['mean'].data.cpu().repeat(1, out_video_batch.shape[2], 1, 1).numpy()
        out_video_batch = np.transpose(out_video_batch, [0, 2, 3, 4, 1])
        gt_video_batch = np.transpose(gt_video_batch, [0, 2, 3, 4, 1])
        appearance_video_batch = np.transpose(appearance_video_batch, [0, 2, 3, 4, 1])
        appearance_deformed_batch = np.transpose(appearance_deformed_batch, [0, 2, 3, 4, 1])
        image = self.create_image_grid((appearance_video_batch, kp_appearance), (gt_video_batch, kp_video), out_video_batch, appearance_deformed_batch, gt_video_batch)
        image = (255 * image).astype(np.uint8)
        return image

def draw_video_with_kp(self, video, kp_array):
    video_array = np.copy(video)
    spatial_size = np.array(video_array.shape[2:0:-1])[np.newaxis, np.newaxis]
    kp_array = spatial_size * (kp_array + 1) / 2
    num_kp = kp_array.shape[1]
    for i in range(len(video_array)):
        for kp_ind, kp in enumerate(kp_array[i]):
            rr, cc = circle(kp[1], kp[0], self.kp_size, shape=video_array.shape[1:3])
            video_array[i][rr, cc] = np.array(self.colormap(kp_ind / num_kp))[:3]
    return video_array

def create_video_column(self, videos):
    if self.draw_border:
        videos = np.copy(videos)
        videos[:, :, [0, -1]] = (1, 1, 1)
        videos[:, :, :, [0, -1]] = (1, 1, 1)
    return np.concatenate(list(videos), axis=1)

class SyncMaster(object):
    """An abstract `SyncMaster` object.

    - During the replication, as the data parallel will trigger an callback of each module, all slave devices should
    call `register(id)` and obtain an `SlavePipe` to communicate with the master.
    - During the forward pass, master device invokes `run_master`, all messages from slave devices will be collected,
    and passed to a registered callback.
    - After receiving the messages, the master device should gather the information and determine to message passed
    back to each slave devices.
    """

    def __init__(self, master_callback):
        """

        Args:
            master_callback: a callback to be invoked after having collected messages from slave devices.
        """
        self._master_callback = master_callback
        self._queue = queue.Queue()
        self._registry = collections.OrderedDict()
        self._activated = False

    def __getstate__(self):
        return {'master_callback': self._master_callback}

    def __setstate__(self, state):
        self.__init__(state['master_callback'])

    def register_slave(self, identifier):
        """
        Register an slave device.

        Args:
            identifier: an identifier, usually is the device id.

        Returns: a `SlavePipe` object which can be used to communicate with the master device.

        """
        if self._activated:
            assert self._queue.empty(), 'Queue is not clean before next initialization.'
            self._activated = False
            self._registry.clear()
        future = FutureResult()
        self._registry[identifier] = _MasterRegistry(future)
        return SlavePipe(identifier, self._queue, future)

    def run_master(self, master_msg):
        """
        Main entry for the master device in each forward pass.
        The messages were first collected from each devices (including the master device), and then
        an callback will be invoked to compute the message to be sent back to each devices
        (including the master device).

        Args:
            master_msg: the message that the master want to send to itself. This will be placed as the first
            message when calling `master_callback`. For detailed usage, see `_SynchronizedBatchNorm` for an example.

        Returns: the message to be sent back to the master device.

        """
        self._activated = True
        intermediates = [(0, master_msg)]
        for i in range(self.nr_slaves):
            intermediates.append(self._queue.get())
        results = self._master_callback(intermediates)
        assert results[0][0] == 0, 'The first result should belongs to the master.'
        for i, res in results:
            if i == 0:
                continue
            self._registry[i].result.put(res)
        for i in range(self.nr_slaves):
            assert self._queue.get() is True
        return results[0][1]

    @property
    def nr_slaves(self):
        return len(self._registry)

@property
def nr_slaves(self):
    return len(self._registry)

def get_files_by_file_size(filepaths, dir, reverse=False):
    """ Return list of file paths  sorted by file size """
    for i in range(len(filepaths)):
        filepaths[i] = (filepaths[i], os.path.getsize(os.path.join(dir, filepaths[i])))
    filepaths.sort(key=lambda filename: filename[1], reverse=reverse)
    for i in range(len(filepaths)):
        filepaths[i] = filepaths[i][0]
    return filepaths

def onmouse(event, x, y, flags, param):
    global drawing, mask
    thickness = thickness_area if value == FILL_AREA else thickness_color
    if event == cv.EVENT_LBUTTONDOWN:
        drawing = True
        cv.circle(mask, (x, y), thickness, True, -1)
    elif event == cv.EVENT_MOUSEMOVE:
        if drawing == True:
            cv.circle(mask, (x, y), thickness, True, -1)
    elif event == cv.EVENT_LBUTTONUP:
        if drawing == True:
            drawing = False
            cv.circle(mask, (x, y), thickness, True, -1)

def process(video, filename, outdir, skipdir):
    global mask, value, drawing
    video2 = video.copy()
    current_it = 0
    cv.namedWindow('input')
    cv.setMouseCallback('input', onmouse)
    cv.moveWindow('input', video.shape[2] + 10, 90)
    video_as_num = color_as_num(video)
    original_fillmask = video_as_num != 256 ** 3 - 1
    paused = False
    while 1:
        current_frame = current_it // 25
        cv.imshow('input', video[current_frame % video.shape[0]])
        k = cv.waitKey(1)
        if not paused:
            current_it += 1
        if k == 27:
            break
        elif k == ord('0'):
            print(' Mark region to fill with left mouse button \n')
            value = FILL_AREA
            mask = np.zeros(video.shape[1:3], dtype=np.uint8)
        elif k == ord('1'):
            print('Mark colors to fill with left mouse button \n')
            value = FILL_COLOR
            mask = np.zeros(video.shape[1:3], dtype=np.uint8)
        elif k == ord('2'):
            print('Mark area to fill (in  all frames) with left mouse button \n')
            value = FILL_ALL_COLOR
            mask = np.zeros(video.shape[1:3], dtype=np.uint8)
        elif k == ord('3'):
            print('Mark connected area to fill with left mouse button \n')
            value = FILL_CONNECTED
            mask = np.zeros(video.shape[1:3], dtype=np.uint8)
        elif k == ord('f'):
            color = np.random.randint(255, size=3)
            video_as_num = color_as_num(video)
            fillmask = video_as_num != 256 ** 3 - 1
            for i in range(len(video)):
                video[i, scipy.ndimage.morphology.binary_fill_holes(fillmask[i])] = color
            video[original_fillmask] = (0, 0, 0)
        elif k == ord('d'):
            video_as_num = color_as_num(video)
            fillmask = video_as_num != 256 ** 3 - 1
            for i in range(len(video)):
                video[i, binary_dilation(fillmask[i])] = (0, 0, 0)
        elif k == ord('e'):
            video_as_num = color_as_num(video)
            fillmask = video_as_num != 256 ** 3 - 1
            for i in range(len(video)):
                video[i, np.logical_not(binary_erosion(fillmask[i]))] = (255, 255, 255)
        elif k == ord('i'):
            video = 255 - video
        elif k == ord('p'):
            video = np.array([img_as_ubyte(np.concatenate([median(frame[..., i], disk(1))[..., np.newaxis] for i in range(3)], axis=-1)) for frame in video])
        elif k == ord('l'):
            paused = not paused
        elif k == ord('n'):
            mimsave(os.path.join(outdir, filename), video[..., ::-1])
            break
        elif k == ord('s'):
            mimsave(os.path.join(skipdir, filename), video2[..., ::-1])
            break
        elif k == ord('r'):
            print('resetting \n')
            drawing = False
            video = video2.copy()
            mask = np.zeros(video.shape[1:3], dtype=np.uint8)
        if mask.sum() == 0:
            continue
        if value == FILL_AREA:
            video[:, mask.astype(bool)] = (255, 255, 255)
            mask = np.zeros(video.shape[1:3], dtype=np.uint8)
        elif value == FILL_COLOR:
            colors = video[current_frame % video.shape[0]][mask.astype(bool)]
            colors = color_as_num(val=colors).reshape((-1,))
            colors = np.unique(colors)
            video_as_num = color_as_num(video)
            for color in colors:
                video[video_as_num == color] = (255, 255, 255)
            mask = np.zeros(video.shape[1:3], dtype=np.uint8)
        elif value == FILL_ALL_COLOR:
            colors = video[:, mask.astype(bool)]
            colors = color_as_num(val=colors).reshape((-1,))
            colors = np.unique(colors)
            video_as_num = color_as_num(video)
            for color in colors:
                video[video_as_num == color] = (255, 255, 255)
            mask = np.zeros(video.shape[1:3], dtype=np.uint8)
        elif value == FILL_CONNECTED:
            color = np.random.randint(255, size=3)
            video_as_num = color_as_num(video)
            fillmask = video_as_num != 256 ** 3 - 1
            for i in range(len(video)):
                labels = label(fillmask[i])
                index = labels[mask]
                video[i, labels == np.unique(index)] = color
            video[original_fillmask] = (0, 0, 0)
            mask = np.zeros(video.shape[1:3], dtype=np.uint8)
    cv.destroyAllWindows()

