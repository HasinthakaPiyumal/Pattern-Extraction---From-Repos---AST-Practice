# Cluster 0

def split_kp(kp_joined, detach=False):
    if detach:
        kp_video = {k: v[:, 1:].detach() for k, v in kp_joined.items()}
        kp_appearance = {k: v[:, :1].detach() for k, v in kp_joined.items()}
    else:
        kp_video = {k: v[:, 1:] for k, v in kp_joined.items()}
        kp_appearance = {k: v[:, :1] for k, v in kp_joined.items()}
    return {'kp_driving': kp_video, 'kp_source': kp_appearance}

def train(config, generator, discriminator, kp_detector, checkpoint, log_dir, dataset, device_ids):
    train_params = config['train_params']
    optimizer_generator = torch.optim.Adam(generator.parameters(), lr=train_params['lr'], betas=(0.5, 0.999))
    optimizer_discriminator = torch.optim.Adam(discriminator.parameters(), lr=train_params['lr'], betas=(0.5, 0.999))
    optimizer_kp_detector = torch.optim.Adam(kp_detector.parameters(), lr=train_params['lr'], betas=(0.5, 0.999))
    if checkpoint is not None:
        start_epoch, it = Logger.load_cpk(checkpoint, generator, discriminator, kp_detector, optimizer_generator, optimizer_discriminator, optimizer_kp_detector)
    else:
        start_epoch = 0
        it = 0
    scheduler_generator = MultiStepLR(optimizer_generator, train_params['epoch_milestones'], gamma=0.1, last_epoch=start_epoch - 1)
    scheduler_discriminator = MultiStepLR(optimizer_discriminator, train_params['epoch_milestones'], gamma=0.1, last_epoch=start_epoch - 1)
    scheduler_kp_detector = MultiStepLR(optimizer_kp_detector, train_params['epoch_milestones'], gamma=0.1, last_epoch=start_epoch - 1)
    dataloader = DataLoader(dataset, batch_size=train_params['batch_size'], shuffle=True, num_workers=4, drop_last=True)
    generator_full = GeneratorFullModel(kp_detector, generator, discriminator, train_params)
    discriminator_full = DiscriminatorFullModel(kp_detector, generator, discriminator, train_params)
    generator_full_par = DataParallelWithCallback(generator_full, device_ids=device_ids)
    discriminator_full_par = DataParallelWithCallback(discriminator_full, device_ids=device_ids)
    with Logger(log_dir=log_dir, visualizer_params=config['visualizer_params'], **train_params['log_params']) as logger:
        for epoch in trange(start_epoch, train_params['num_epochs']):
            for x in dataloader:
                out = generator_full_par(x)
                loss_values = out[:-2]
                generated = out[-2]
                kp_joined = out[-1]
                loss_values = [val.mean() for val in loss_values]
                loss = sum(loss_values)
                loss.backward(retain_graph=not train_params['detach_kp_discriminator'])
                optimizer_generator.step()
                optimizer_generator.zero_grad()
                optimizer_discriminator.zero_grad()
                if train_params['detach_kp_discriminator']:
                    optimizer_kp_detector.step()
                    optimizer_kp_detector.zero_grad()
                generator_loss_values = [val.detach().cpu().numpy() for val in loss_values]
                loss_values = discriminator_full_par(x, kp_joined, generated)
                loss_values = [val.mean() for val in loss_values]
                loss = sum(loss_values)
                loss.backward()
                optimizer_discriminator.step()
                optimizer_discriminator.zero_grad()
                if not train_params['detach_kp_discriminator']:
                    optimizer_kp_detector.step()
                    optimizer_kp_detector.zero_grad()
                discriminator_loss_values = [val.detach().cpu().numpy() for val in loss_values]
                logger.log_iter(it, names=generator_loss_names(train_params['loss_weights']) + discriminator_loss_names(), values=generator_loss_values + discriminator_loss_values, inp=x, out=generated)
                it += 1
            scheduler_generator.step()
            scheduler_discriminator.step()
            scheduler_kp_detector.step()
            logger.log_epoch(epoch, {'generator': generator, 'discriminator': discriminator, 'kp_detector': kp_detector, 'optimizer_generator': optimizer_generator, 'optimizer_discriminator': optimizer_discriminator, 'optimizer_kp_detector': optimizer_kp_detector})

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

def __getitem__(self, idx):
    keypoints = self.keypoints_array[idx]
    selected = self.transform(keypoints)
    selected = {k: np.concatenate([v[k][0] for v in selected], axis=0) for k in selected[0].keys()}
    return selected

def prediction(config, generator, kp_detector, checkpoint, log_dir):
    dataset = FramesDataset(is_train=True, transform=VideoToTensor(), **config['dataset_params'])
    log_dir = os.path.join(log_dir, 'prediction')
    png_dir = os.path.join(log_dir, 'png')
    if checkpoint is not None:
        Logger.load_cpk(checkpoint, generator=generator, kp_detector=kp_detector)
    else:
        raise AttributeError("Checkpoint should be specified for mode='prediction'.")
    dataloader = DataLoader(dataset, batch_size=1, shuffle=False, num_workers=1)
    generator = DataParallelWithCallback(generator)
    kp_detector = DataParallelWithCallback(kp_detector)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    if not os.path.exists(png_dir):
        os.makedirs(png_dir)
    print('Extracting keypoints...')
    kp_detector.eval()
    generator.eval()
    keypoints_array = []
    prediction_params = config['prediction_params']
    for it, x in tqdm(enumerate(dataloader)):
        if prediction_params['train_size'] is not None:
            if it > prediction_params['train_size']:
                break
        with torch.no_grad():
            keypoints = []
            for i in range(x['video'].shape[2]):
                kp = kp_detector(x['video'][:, :, i:i + 1])
                kp = {k: v.data.cpu().numpy() for k, v in kp.items()}
                keypoints.append(kp)
            keypoints_array.append(keypoints)
    predictor = PredictionModule(num_kp=config['model_params']['common_params']['num_kp'], kp_variance=config['model_params']['common_params']['kp_variance'], **prediction_params['rnn_params']).cuda()
    num_epochs = prediction_params['num_epochs']
    lr = prediction_params['lr']
    bs = prediction_params['batch_size']
    num_frames = prediction_params['num_frames']
    init_frames = prediction_params['init_frames']
    optimizer = torch.optim.Adam(predictor.parameters(), lr=lr)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, verbose=True, patience=50)
    kp_dataset = KPDataset(keypoints_array, num_frames=num_frames)
    kp_dataloader = DataLoader(kp_dataset, batch_size=bs)
    print('Training prediction...')
    for _ in trange(num_epochs):
        loss_list = []
        for x in kp_dataloader:
            x = {k: v.cuda() for k, v in x.items()}
            gt = {k: v.clone() for k, v in x.items()}
            for k in x:
                x[k][:, init_frames:] = 0
            prediction = predictor(x)
            loss = sum([torch.abs(gt[k][:, init_frames:] - prediction[k][:, init_frames:]).mean() for k in x])
            loss.backward()
            optimizer.step()
            optimizer.zero_grad()
            loss_list.append(loss.detach().data.cpu().numpy())
        loss = np.mean(loss_list)
        scheduler.step(loss)
    dataset = FramesDataset(is_train=False, transform=VideoToTensor(), **config['dataset_params'])
    dataloader = DataLoader(dataset, batch_size=1, shuffle=False, num_workers=1)
    print('Make predictions...')
    for it, x in tqdm(enumerate(dataloader)):
        with torch.no_grad():
            x['video'] = x['video'][:, :, :num_frames]
            kp_init = kp_detector(x['video'])
            for k in kp_init:
                kp_init[k][:, init_frames:] = 0
            kp_source = kp_detector(x['video'][:, :, :1])
            kp_video = predictor(kp_init)
            for k in kp_video:
                kp_video[k][:, :init_frames] = kp_init[k][:, :init_frames]
            if 'var' in kp_video and prediction_params['predict_variance']:
                kp_video['var'] = kp_init['var'][:, init_frames - 1:init_frames].repeat(1, kp_video['var'].shape[1], 1, 1, 1)
            out = generate(generator, appearance_image=x['video'][:, :, :1], kp_appearance=kp_source, kp_video=kp_video)
            x['source'] = x['video'][:, :, :1]
            out_video_batch = out['video_prediction'].data.cpu().numpy()
            out_video_batch = np.concatenate(np.transpose(out_video_batch, [0, 2, 3, 4, 1])[0], axis=1)
            imageio.imsave(os.path.join(png_dir, x['name'][0] + '.png'), (255 * out_video_batch).astype(np.uint8))
            image = Visualizer(**config['visualizer_params']).visualize_reconstruction(x, out)
            image_name = x['name'][0] + prediction_params['format']
            imageio.mimsave(os.path.join(log_dir, image_name), image)
            del x, kp_video, kp_source, out

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

def __getitem__(self, idx):
    img_name = os.path.join(self.root_dir, self.images[idx])
    video_array = read_video(img_name, image_shape=self.image_shape)
    out = self.transform(video_array)
    out['name'] = os.path.basename(img_name)
    return out

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

def __getitem__(self, idx):
    pair = self.pairs[idx]
    first = self.initial_dataset[pair[0]]
    second = self.initial_dataset[pair[1]]
    first = {'driving_' + key: value for key, value in first.items()}
    second = {'source_' + key: value for key, value in second.items()}
    return {**first, **second}

def transfer_one(generator, kp_detector, source_image, driving_video, transfer_params):
    cat_dict = lambda l, dim: {k: torch.cat([v[k] for v in l], dim=dim) for k in l[0]}
    d = driving_video.shape[2]
    kp_driving = cat_dict([kp_detector(driving_video[:, :, i:i + 1]) for i in range(d)], dim=1)
    kp_source = kp_detector(source_image)
    kp_driving_norm = normalize_kp(kp_driving, kp_source, **transfer_params['normalization_params'])
    kp_video_list = [{k: v[:, i:i + 1] for k, v in kp_driving_norm.items()} for i in range(d)]
    out = cat_dict([generator(source_image=source_image, kp_driving=kp, kp_source=kp_source) for kp in kp_video_list], dim=2)
    out['kp_driving'] = kp_driving
    out['kp_source'] = kp_source
    out['kp_norm'] = kp_driving_norm
    return out

def transfer(config, generator, kp_detector, checkpoint, log_dir, dataset):
    log_dir = os.path.join(log_dir, 'transfer')
    png_dir = os.path.join(log_dir, 'png')
    transfer_params = config['transfer_params']
    dataset = PairedDataset(initial_dataset=dataset, number_of_pairs=transfer_params['num_pairs'])
    dataloader = DataLoader(dataset, batch_size=1, shuffle=False, num_workers=1)
    if checkpoint is not None:
        Logger.load_cpk(checkpoint, generator=generator, kp_detector=kp_detector)
    else:
        raise AttributeError("Checkpoint should be specified for mode='transfer'.")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    if not os.path.exists(png_dir):
        os.makedirs(png_dir)
    generator = DataParallelWithCallback(generator)
    kp_detector = DataParallelWithCallback(kp_detector)
    generator.eval()
    kp_detector.eval()
    for it, x in tqdm(enumerate(dataloader)):
        with torch.no_grad():
            x = {key: value if not hasattr(value, 'cuda') else value.cuda() for key, value in x.items()}
            driving_video = x['driving_video']
            source_image = x['source_video'][:, :, :1, :, :]
            out = transfer_one(generator, kp_detector, source_image, driving_video, transfer_params)
            img_name = '-'.join([x['driving_name'][0], x['source_name'][0]])
            out_video_batch = out['video_prediction'].data.cpu().numpy()
            out_video_batch = np.concatenate(np.transpose(out_video_batch, [0, 2, 3, 4, 1])[0], axis=1)
            imageio.imsave(os.path.join(png_dir, img_name + '.png'), (255 * out_video_batch).astype(np.uint8))
            image = Visualizer(**config['visualizer_params']).visualize_transfer(driving_video=driving_video, source_image=source_image, out=out)
            imageio.mimsave(os.path.join(log_dir, img_name + transfer_params['format']), image)

def reconstruction(config, generator, kp_detector, checkpoint, log_dir, dataset):
    png_dir = os.path.join(log_dir, 'reconstruction/png')
    log_dir = os.path.join(log_dir, 'reconstruction')
    if checkpoint is not None:
        Logger.load_cpk(checkpoint, generator=generator, kp_detector=kp_detector)
    else:
        raise AttributeError("Checkpoint should be specified for mode='test'.")
    dataloader = DataLoader(dataset, batch_size=1, shuffle=False, num_workers=1)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    if not os.path.exists(png_dir):
        os.makedirs(png_dir)
    loss_list = []
    generator = DataParallelWithCallback(generator)
    kp_detector = DataParallelWithCallback(kp_detector)
    generator.eval()
    kp_detector.eval()
    cat_dict = lambda l, dim: {k: torch.cat([v[k] for v in l], dim=dim) for k in l[0]}
    for it, x in tqdm(enumerate(dataloader)):
        if config['reconstruction_params']['num_videos'] is not None:
            if it > config['reconstruction_params']['num_videos']:
                break
        with torch.no_grad():
            kp_appearance = kp_detector(x['video'][:, :, :1])
            d = x['video'].shape[2]
            kp_video = cat_dict([kp_detector(x['video'][:, :, i:i + 1]) for i in range(d)], dim=1)
            out = generate(generator, appearance_image=x['video'][:, :, :1], kp_appearance=kp_appearance, kp_video=kp_video)
            x['source'] = x['video'][:, :, :1]
            out_video_batch = out['video_prediction'].data.cpu().numpy()
            out_video_batch = np.concatenate(np.transpose(out_video_batch, [0, 2, 3, 4, 1])[0], axis=1)
            imageio.imsave(os.path.join(png_dir, x['name'][0] + '.png'), (255 * out_video_batch).astype(np.uint8))
            image = Visualizer(**config['visualizer_params']).visualize_reconstruction(x, out)
            image_name = x['name'][0] + config['reconstruction_params']['format']
            imageio.mimsave(os.path.join(log_dir, image_name), image)
            loss = reconstruction_loss(out['video_prediction'].cpu(), x['video'].cpu(), 1)
            loss_list.append(loss.data.cpu().numpy())
            del x, kp_video, kp_appearance, out, loss
    print('Reconstruction loss: %s' % np.mean(loss_list))

class Logger:

    def __init__(self, log_dir, log_file_name='log.txt', log_freq_iter=100, cpk_freq_epoch=100, zfill_num=8, visualizer_params=None):
        self.loss_list = []
        self.cpk_dir = log_dir
        self.visualizations_dir = os.path.join(log_dir, 'train-vis')
        if not os.path.exists(self.visualizations_dir):
            os.makedirs(self.visualizations_dir)
        self.log_file = open(os.path.join(log_dir, log_file_name), 'a')
        self.log_freq = log_freq_iter
        self.cpk_freq = cpk_freq_epoch
        self.zfill_num = zfill_num
        self.visualizer = Visualizer(**visualizer_params)
        self.epoch = 0
        self.it = 0

    def log_scores(self, loss_names):
        loss_mean = np.array(self.loss_list).mean(axis=0)
        loss_string = '; '.join(['%s - %.5f' % (name, value) for name, value in zip(loss_names, loss_mean)])
        loss_string = str(self.it).zfill(self.zfill_num) + ') ' + loss_string
        print(loss_string, file=self.log_file)
        self.loss_list = []
        self.log_file.flush()

    def visualize_rec(self, inp, out):
        image = self.visualizer.visualize_reconstruction(inp, out)
        imageio.mimsave(os.path.join(self.visualizations_dir, '%s-rec.gif' % str(self.it).zfill(self.zfill_num)), image)

    def save_cpk(self):
        cpk = {k: v.state_dict() for k, v in self.models.items()}
        cpk['epoch'] = self.epoch
        cpk['it'] = self.it
        torch.save(cpk, os.path.join(self.cpk_dir, '%s-checkpoint.pth.tar' % str(self.epoch).zfill(self.zfill_num)))

    @staticmethod
    def load_cpk(checkpoint_path, generator=None, discriminator=None, kp_detector=None, optimizer_generator=None, optimizer_discriminator=None, optimizer_kp_detector=None):
        checkpoint = torch.load(checkpoint_path)
        if generator is not None:
            generator.load_state_dict(checkpoint['generator'])
        if kp_detector is not None:
            kp_detector.load_state_dict(checkpoint['kp_detector'])
        if discriminator is not None:
            discriminator.load_state_dict(checkpoint['discriminator'])
        if optimizer_generator is not None:
            optimizer_generator.load_state_dict(checkpoint['optimizer_generator'])
        if optimizer_discriminator is not None:
            optimizer_discriminator.load_state_dict(checkpoint['optimizer_discriminator'])
        if optimizer_kp_detector is not None:
            optimizer_kp_detector.load_state_dict(checkpoint['optimizer_kp_detector'])
        return (checkpoint['epoch'], checkpoint['it'])

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if 'models' in self.__dict__:
            self.save_cpk()
        self.log_file.close()

    def log_iter(self, it, names, values, inp, out):
        self.it = it
        self.names = names
        self.loss_list.append(values)
        if it % self.log_freq == 0:
            self.log_scores(self.names)
            self.visualize_rec(inp, out)

    def log_epoch(self, epoch, models):
        self.epoch = epoch
        self.models = models
        if epoch % self.cpk_freq == 0:
            self.save_cpk()

def __init__(self, log_dir, log_file_name='log.txt', log_freq_iter=100, cpk_freq_epoch=100, zfill_num=8, visualizer_params=None):
    self.loss_list = []
    self.cpk_dir = log_dir
    self.visualizations_dir = os.path.join(log_dir, 'train-vis')
    if not os.path.exists(self.visualizations_dir):
        os.makedirs(self.visualizations_dir)
    self.log_file = open(os.path.join(log_dir, log_file_name), 'a')
    self.log_freq = log_freq_iter
    self.cpk_freq = cpk_freq_epoch
    self.zfill_num = zfill_num
    self.visualizer = Visualizer(**visualizer_params)
    self.epoch = 0
    self.it = 0

def log_scores(self, loss_names):
    loss_mean = np.array(self.loss_list).mean(axis=0)
    loss_string = '; '.join(['%s - %.5f' % (name, value) for name, value in zip(loss_names, loss_mean)])
    loss_string = str(self.it).zfill(self.zfill_num) + ') ' + loss_string
    print(loss_string, file=self.log_file)
    self.loss_list = []
    self.log_file.flush()

def visualize_rec(self, inp, out):
    image = self.visualizer.visualize_reconstruction(inp, out)
    imageio.mimsave(os.path.join(self.visualizations_dir, '%s-rec.gif' % str(self.it).zfill(self.zfill_num)), image)

def save_cpk(self):
    cpk = {k: v.state_dict() for k, v in self.models.items()}
    cpk['epoch'] = self.epoch
    cpk['it'] = self.it
    torch.save(cpk, os.path.join(self.cpk_dir, '%s-checkpoint.pth.tar' % str(self.epoch).zfill(self.zfill_num)))

def mv_all_images(images, in_folder, out_folder):
    for img in images:
        move(os.path.join(in_folder, img), os.path.join(out_folder, img))

