# Cluster 26

@DATASETS.register_module()
class ScanNetPairDataset(Dataset):

    def __init__(self, data_root='data/scannet_pair', overlap_threshold=0.3, twin1_transform=None, twin2_transform=None, loop=1, **kwargs):
        super(ScanNetPairDataset, self).__init__()
        self.data_root = data_root
        self.overlap_threshold = overlap_threshold
        self.twin1_transform = Compose(twin1_transform)
        self.twin2_transform = Compose(twin2_transform)
        self.loop = loop
        self.data_list = self.get_data_list()
        logger = get_root_logger()
        logger.info('Totally {} x {} samples.'.format(len(self.data_list), self.loop))

    def get_data_list(self):
        data_list = []
        overlap_list = glob.glob(os.path.join(self.data_root, '*', 'pcd', 'overlap.txt'))
        for overlap_file in overlap_list:
            with open(overlap_file) as f:
                overlap = f.readlines()
            overlap = [pair.strip().split() for pair in overlap]
            data_list.extend([pair[:2] for pair in overlap if float(pair[2]) > self.overlap_threshold])
        return data_list

    def get_data(self, idx):
        pair = self.data_list[idx % len(self.data_list)]
        twin1_dict = torch.load(self.data_root + pair[0])
        twin2_dict = torch.load(self.data_root + pair[1])
        twin1_dict['origin_coord'] = twin1_dict['coord'].copy()
        twin2_dict['origin_coord'] = twin2_dict['coord'].copy()
        return (twin1_dict, twin2_dict)

    def get_data_name(self, idx):
        return os.path.basename(self.data_list[idx % len(self.data_list)]).split('.')[0]

    def prepare_train_data(self, idx):
        twin1_dict, twin2_dict = self.get_data(idx)
        twin1_dict = self.twin1_transform(twin1_dict)
        twin2_dict = self.twin2_transform(twin2_dict)
        data_dict = dict()
        for key, value in twin1_dict.items():
            data_dict['twin1_' + key] = value
        for key, value in twin2_dict.items():
            data_dict['twin2_' + key] = value
        return data_dict

    def prepare_test_data(self, idx):
        raise NotImplementedError

    def __getitem__(self, idx):
        return self.prepare_train_data(idx)

    def __len__(self):
        return len(self.data_list) * self.loop

def __getitem__(self, idx):
    return self.prepare_train_data(idx)

@DATASETS.register_module()
class SemanticKITTIDataset(Dataset):

    def __init__(self, split='train', data_root='data/semantic_kitti', learning_map=None, transform=None, test_mode=False, test_cfg=None, loop=1):
        super(SemanticKITTIDataset, self).__init__()
        self.data_root = data_root
        self.split = split
        self.learning_map = learning_map
        self.split2seq = dict(train=[0, 1, 2, 3, 4, 5, 6, 7, 9, 10], val=[8], test=[11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21])
        self.transform = Compose(transform)
        self.loop = loop if not test_mode else 1
        self.test_mode = test_mode
        self.test_cfg = test_cfg if test_mode else None
        if test_mode:
            self.test_voxelize = TRANSFORMS.build(self.test_cfg.voxelize)
            self.test_crop = TRANSFORMS.build(self.test_cfg.crop)
            self.post_transform = Compose(self.test_cfg.post_transform)
            self.aug_transform = [Compose(aug) for aug in self.test_cfg.aug_transform]
        if isinstance(self.split, str):
            seq_list = self.split2seq[split]
        elif isinstance(self.split, list):
            seq_list = []
            for split in self.split:
                seq_list += self.split2seq[split]
        else:
            raise NotImplementedError
        self.data_list = []
        for seq in seq_list:
            seq = str(seq).zfill(2)
            seq_folder = os.path.join(self.data_root, 'sequences', seq)
            seq_files = sorted(os.listdir(os.path.join(seq_folder, 'velodyne')))
            self.data_list += [os.path.join(seq_folder, 'velodyne', file) for file in seq_files]
        logger = get_root_logger()
        logger.info('Totally {} x {} samples in {} set.'.format(len(self.data_list), self.loop, split))

    def prepare_train_data(self, idx):
        data_idx = idx % len(self.data_list)
        with open(self.data_list[data_idx], 'rb') as b:
            scan = np.fromfile(b, dtype=np.float32).reshape(-1, 4)
        coord = scan[:, :3]
        strength = scan[:, -1].reshape([-1, 1])
        label_file = self.data_list[data_idx].replace('velodyne', 'labels').replace('.bin', '.label')
        if os.path.exists(label_file):
            with open(label_file, 'rb') as a:
                label = np.fromfile(a, dtype=np.int32).reshape(-1)
        else:
            label = np.zeros(coord.shape[0]).astype(np.int32)
        label = np.vectorize(self.learning_map.__getitem__)(label & 65535).astype(np.int64)
        data_dict = dict(coord=coord, strength=strength, label=label)
        data_dict = self.transform(data_dict)
        return data_dict

    def prepare_test_data(self, idx):
        raise NotImplementedError

    def get_data_name(self, idx):
        return self.data_list[self.data_list[idx % len(self.data_list)]]

    def __getitem__(self, idx):
        if self.test_mode:
            return self.prepare_test_data(idx)
        else:
            return self.prepare_train_data(idx)

    def __len__(self):
        return len(self.data_list) * self.loop

def __getitem__(self, idx):
    if self.test_mode:
        return self.prepare_test_data(idx)
    else:
        return self.prepare_train_data(idx)

@DATASETS.register_module()
class ArkitScenesDataset(Dataset):

    def __init__(self, split='Training', data_root='data/ARKitScenesMesh', transform=None, test_mode=False, test_cfg=None, loop=1):
        super(ArkitScenesDataset, self).__init__()
        self.data_root = data_root
        self.split = split
        self.transform = Compose(transform)
        self.loop = loop if not test_mode else 1
        self.test_mode = test_mode
        self.test_cfg = test_cfg if test_mode else None
        self.class2id = np.array(VALID_CLASS_IDS_200)
        if test_mode:
            self.test_voxelize = TRANSFORMS.build(self.test_cfg.voxelize)
            self.test_crop = TRANSFORMS.build(self.test_cfg.crop)
            self.post_transform = Compose(self.test_cfg.post_transform)
            self.aug_transform = [Compose(aug) for aug in self.test_cfg.aug_transform]
        self.data_list = self.get_data_list()
        logger = get_root_logger()
        logger.info('Totally {} x {} samples in {} set.'.format(len(self.data_list), self.loop, split))

    def get_data_list(self):
        if isinstance(self.split, str):
            data_list = glob.glob(os.path.join(self.data_root, self.split, '*.pth'))
        elif isinstance(self.split, list):
            data_list = []
            for split in self.split:
                data_list += glob.glob(os.path.join(self.data_root, split, '*.pth'))
        else:
            raise NotImplementedError
        return data_list

    def get_data(self, idx):
        data = torch.load(self.data_list[idx % len(self.data_list)])
        coord = data['coord']
        color = data['color']
        normal = data['normal']
        label = np.zeros(coord.shape[0])
        data_dict = dict(coord=coord, normal=normal, color=color, label=label)
        return data_dict

    def get_data_name(self, idx):
        data_idx = self.data_idx[idx % len(self.data_idx)]
        return os.path.basename(self.data_list[data_idx]).split('.')[0]

    def prepare_train_data(self, idx):
        data_dict = self.get_data(idx)
        data_dict = self.transform(data_dict)
        return data_dict

    def prepare_test_data(self, idx):
        data_dict = self.get_data(idx)
        label = data_dict.pop('label')
        data_dict = self.transform(data_dict)
        data_dict_list = []
        for aug in self.aug_transform:
            data_dict_list.append(aug(deepcopy(data_dict)))
        input_dict_list = []
        for data in data_dict_list:
            data_part_list = self.test_voxelize(data)
            for data_part in data_part_list:
                data_part_list = self.test_crop(data_part)
                input_dict_list += data_part_list
        for i in range(len(input_dict_list)):
            input_dict_list[i] = self.post_transform(input_dict_list[i])
        return (input_dict_list, label)

    def __getitem__(self, idx):
        if self.test_mode:
            return self.prepare_test_data(idx)
        else:
            return self.prepare_train_data(idx)

    def __len__(self):
        return len(self.data_list) * self.loop

def __getitem__(self, idx):
    if self.test_mode:
        return self.prepare_test_data(idx)
    else:
        return self.prepare_train_data(idx)

@DATASETS.register_module()
class DefaultDataset(Dataset):

    def __init__(self, split='train', data_root='data/dataset', transform=None, test_mode=False, test_cfg=None, loop=1):
        super(DefaultDataset, self).__init__()
        self.data_root = data_root
        self.split = split
        self.transform = Compose(transform)
        self.loop = loop if not test_mode else 1
        self.test_mode = test_mode
        self.test_cfg = test_cfg if test_mode else None
        if test_mode:
            self.test_voxelize = TRANSFORMS.build(self.test_cfg.voxelize)
            self.test_crop = TRANSFORMS.build(self.test_cfg.crop)
            self.post_transform = Compose(self.test_cfg.post_transform)
            self.aug_transform = [Compose(aug) for aug in self.test_cfg.aug_transform]
        self.data_list = self.get_data_list()
        logger = get_root_logger()
        logger.info('Totally {} x {} samples in {} set.'.format(len(self.data_list), self.loop, split))

    def get_data_list(self):
        if isinstance(self.split, str):
            data_list = glob.glob(os.path.join(self.data_root, self.split, '*.pth'))
        elif isinstance(self.split, list):
            data_list = []
            for split in self.split:
                data_list += glob.glob(os.path.join(self.data_root, split, '*.pth'))
        else:
            raise NotImplementedError
        return data_list

    def get_data(self, idx):
        data = torch.load(self.data_list[idx % len(self.data_list)])
        coord = data['coord']
        color = data['color']
        normal = data['normal']
        if 'semantic_gt' in data.keys():
            label = data['semantic_gt'].reshape([-1])
        else:
            label = np.zeros(coord.shape[0])
        data_dict = dict(coord=coord, norm=normal, color=color, label=label)
        return data_dict

    def get_data_name(self, idx):
        data_idx = idx % len(self.data_list)
        return os.path.basename(self.data_list[data_idx]).split('.')[0]

    def prepare_train_data(self, idx):
        data_dict = self.get_data(idx)
        data_dict = self.transform(data_dict)
        return data_dict

    def prepare_test_data(self, idx):
        data_dict = self.get_data(idx)
        label = data_dict.pop('label')
        data_dict = self.transform(data_dict)
        data_dict_list = []
        for aug in self.aug_transform:
            data_dict_list.append(aug(deepcopy(data_dict)))
        input_dict_list = []
        for data in data_dict_list:
            data_part_list = self.test_voxelize(data)
            for data_part in data_part_list:
                if self.test_crop:
                    data_part = self.test_crop(data_part)
                else:
                    data_part = [data_part]
                input_dict_list += data_part
        for i in range(len(input_dict_list)):
            input_dict_list[i] = self.post_transform(input_dict_list[i])
        return (input_dict_list, label)

    def __getitem__(self, idx):
        if self.test_mode:
            return self.prepare_test_data(idx)
        else:
            return self.prepare_train_data(idx)

    def __len__(self):
        return len(self.data_list) * self.loop

def __getitem__(self, idx):
    if self.test_mode:
        return self.prepare_test_data(idx)
    else:
        return self.prepare_train_data(idx)

@DATASETS.register_module()
class S3DISDataset(Dataset):

    def __init__(self, split=('Area_1', 'Area_2', 'Area_3', 'Area_4', 'Area_6'), data_root='data/s3dis', transform=None, test_mode=False, test_cfg=None, loop=1):
        super(S3DISDataset, self).__init__()
        self.data_root = data_root
        self.split = split
        self.transform = Compose(transform)
        self.loop = loop if not test_mode else 1
        self.test_mode = test_mode
        self.test_cfg = test_cfg if test_mode else None
        if test_mode:
            self.test_voxelize = TRANSFORMS.build(self.test_cfg.voxelize)
            self.test_crop = TRANSFORMS.build(self.test_cfg.crop) if self.test_cfg.crop else None
            self.post_transform = Compose(self.test_cfg.post_transform)
            self.aug_transform = [Compose(aug) for aug in self.test_cfg.aug_transform]
        self.data_list = self.get_data_list()
        logger = get_root_logger()
        logger.info('Totally {} x {} samples in {} set.'.format(len(self.data_list), self.loop, split))

    def get_data_list(self):
        if isinstance(self.split, str):
            data_list = glob.glob(os.path.join(self.data_root, self.split, '*.pth'))
        elif isinstance(self.split, Sequence):
            data_list = []
            for split in self.split:
                data_list += glob.glob(os.path.join(self.data_root, split, '*.pth'))
        else:
            raise NotImplementedError
        return data_list

    def get_data(self, idx):
        data = torch.load(self.data_list[idx % len(self.data_list)])
        coord = data['coord']
        color = data['color']
        if 'semantic_gt' in data.keys():
            label = data['semantic_gt'].reshape([-1])
        else:
            label = np.zeros(coord.shape[0])
        data_dict = dict(coord=coord, color=color, label=label)
        return data_dict

    def get_data_name(self, idx):
        return os.path.basename(self.data_list[idx % len(self.data_list)]).split('.')[0]

    def prepare_train_data(self, idx):
        data_dict = self.get_data(idx)
        data_dict = self.transform(data_dict)
        return data_dict

    def prepare_test_data(self, idx):
        data_dict = self.get_data(idx)
        label = data_dict.pop('label')
        data_dict = self.transform(data_dict)
        data_dict_list = []
        for aug in self.aug_transform:
            data_dict_list.append(aug(deepcopy(data_dict)))
        input_dict_list = []
        for data in data_dict_list:
            data_part_list = self.test_voxelize(data)
            for data_part in data_part_list:
                if self.test_crop:
                    data_part = self.test_crop(data_part)
                else:
                    data_part = [data_part]
                input_dict_list += data_part
        for i in range(len(input_dict_list)):
            input_dict_list[i] = self.post_transform(input_dict_list[i])
        return (input_dict_list, label)

    def __getitem__(self, idx):
        if self.test_mode:
            return self.prepare_test_data(idx)
        else:
            return self.prepare_train_data(idx)

    def __len__(self):
        return len(self.data_list) * self.loop

def __getitem__(self, idx):
    if self.test_mode:
        return self.prepare_test_data(idx)
    else:
        return self.prepare_train_data(idx)

@DATASETS.register_module()
class ModelNetDataset(Dataset):

    def __init__(self, split='train', data_root='data/modelnet40_normal_resampled', class_names=None, transform=None, cache_data=False, test_mode=False, test_cfg=None, loop=1):
        super(ModelNetDataset, self).__init__()
        self.data_root = data_root
        self.class_names = dict(zip(class_names, range(len(class_names))))
        self.split = split
        self.cache_data = cache_data
        self.transform = Compose(transform)
        self.loop = loop if not test_mode else 1
        self.test_mode = test_mode
        self.test_cfg = test_cfg if test_mode else None
        self.cache = {}
        if test_mode:
            pass
        self.data_list = [line.rstrip() for line in open(os.path.join(self.data_root, 'modelnet40_{}.txt'.format(self.split)))]
        logger = get_root_logger()
        logger.info('Totally {} x {} samples in {} set.'.format(len(self.data_idx), self.loop, split))

    def prepare_train_data(self, idx):
        data_idx = idx % len(self.data_list)
        if self.cache_data:
            coord, norm, label = self.cache[data_idx]
        else:
            data_shape = '_'.join(self.data_list[data_idx].split('_')[0:-1])
            data_path = os.path.join(self.data_root, data_shape, self.data_list[data_idx] + '.txt')
            data = np.loadtxt(data_path, delimiter=',').astype(np.float32)
            coord, norm = (data[:, 0:3], data[:, 3:6])
            label = np.array([self.class_names[data_shape]])
            if self.cache_data:
                self.cache[data_idx] = (coord, norm, label)
        data_dict = dict(coord=coord, norm=norm, label=label)
        data_dict = self.transform(data_dict)
        return data_dict

    def prepare_test_data(self, idx):
        assert idx < len(self.data_idx)
        data_idx = idx
        data_shape = '_'.join(self.data_list[data_idx].split('_')[0:-1])
        data_path = os.path.join(self.data_root, data_shape, self.data_list[data_idx] + '.txt')
        data = np.loadtxt(data_path, delimiter=',').astype(np.float32)
        coord, norm = (data[:, 0:3], data[:, 3:6])
        label = np.array([self.class_names[data_shape]])
        data_dict = dict(coord=coord, norm=norm, label=label)
        data_dict = self.transform(data_dict)
        return data_dict

    def get_data_name(self, idx):
        data_idx = idx % len(self.data_list)
        return self.data_list[data_idx]

    def __getitem__(self, idx):
        if self.test_mode:
            return self.prepare_test_data(idx)
        else:
            return self.prepare_train_data(idx)

    def __len__(self):
        return len(self.data_idx) * self.loop

def __getitem__(self, idx):
    if self.test_mode:
        return self.prepare_test_data(idx)
    else:
        return self.prepare_train_data(idx)

@DATASETS.register_module()
class ShapeNetPartDataset(Dataset):

    def __init__(self, split='train', data_root='data/shapenetcore_partanno_segmentation_benchmark_v0_normal', transform=None, test_mode=False, test_cfg=None, loop=1):
        super(ShapeNetPartDataset, self).__init__()
        self.data_root = data_root
        self.split = split
        self.transform = Compose(transform)
        self.loop = loop if not test_mode else 1
        self.test_mode = test_mode
        self.test_cfg = test_cfg if test_mode else None
        self.cache = {}
        self.categories = []
        self.category2part = {'Airplane': [0, 1, 2, 3], 'Bag': [4, 5], 'Cap': [6, 7], 'Car': [8, 9, 10, 11], 'Chair': [12, 13, 14, 15], 'Earphone': [16, 17, 18], 'Guitar': [19, 20, 21], 'Knife': [22, 23], 'Lamp': [24, 25, 26, 27], 'Laptop': [28, 29], 'Motorbike': [30, 31, 32, 33, 34, 35], 'Mug': [36, 37], 'Pistol': [38, 39, 40], 'Rocket': [41, 42, 43], 'Skateboard': [44, 45, 46], 'Table': [47, 48, 49]}
        self.token2category = {}
        with open(os.path.join(self.data_root, 'synsetoffset2category.txt'), 'r') as f:
            for line in f:
                ls = line.strip().split()
                self.token2category[ls[1]] = len(self.categories)
                self.categories.append(ls[0])
        if test_mode:
            self.post_transform = Compose(self.test_cfg.post_transform)
            self.aug_transform = [Compose(aug) for aug in self.test_cfg.aug_transform]
        if isinstance(self.split, str):
            self.data_list = self.load_data_list(self.split)
        elif isinstance(self.split, list):
            self.data_list = []
            for s in self.split:
                self.data_list += self.load_data_list(s)
        else:
            raise NotImplementedError
        logger = get_root_logger()
        logger.info('Totally {} x {} samples in {} set.'.format(len(self.data_idx), self.loop, split))

    def load_data_list(self, split):
        split_file = os.path.join(self.data_root, 'train_test_split', 'shuffled_{}_file_list.json'.format(split))
        if not os.path.isfile(split_file):
            raise RuntimeError('Split file do not exist: ' + split_file + '\n')
        with open(split_file, 'r') as f:
            data_list = [os.path.join(self.data_root, data[11:] + '.txt') for data in json.load(f)]
        return data_list

    def prepare_train_data(self, idx):
        data_idx = idx % len(self.data_list)
        if data_idx in self.cache:
            coord, norm, label, cls_token = self.cache[data_idx]
        else:
            data = np.loadtxt(self.data_list[data_idx]).astype(np.float32)
            cls_token = self.token2category[os.path.basename(os.path.dirname(self.data_list[data_idx]))]
            coord, norm, label = (data[:, :3], data[:, 3:6], data[:, 6].astype(np.int32))
            self.cache[data_idx] = (coord, norm, label, cls_token)
        data_dict = dict(coord=coord, norm=norm, label=label, cls_token=cls_token)
        data_dict = self.transform(data_dict)
        return data_dict

    def prepare_test_data(self, idx):
        data_idx = self.data_idx[idx % len(self.data_idx)]
        data = np.loadtxt(self.data_list[data_idx]).astype(np.float32)
        cls_token = self.token2category[os.path.basename(os.path.dirname(self.data_list[data_idx]))]
        coord, norm, label = (data[:, :3], data[:, 3:6], data[:, 6].astype(np.int32))
        data_dict = dict(coord=coord, norm=norm, cls_token=cls_token)
        data_dict = self.transform(data_dict)
        data_dict_list = []
        for aug in self.aug_transform:
            data_dict_list.append(self.post_transform(aug(deepcopy(data_dict))))
        return (data_dict_list, label)

    def get_data_name(self, idx):
        data_idx = self.data_idx[idx % len(self.data_idx)]
        return os.path.basename(self.data_list[data_idx]).split('.')[0]

    def __getitem__(self, idx):
        if self.test_mode:
            return self.prepare_test_data(idx)
        else:
            return self.prepare_train_data(idx)

    def __len__(self):
        return len(self.data_idx) * self.loop

def __getitem__(self, idx):
    if self.test_mode:
        return self.prepare_test_data(idx)
    else:
        return self.prepare_train_data(idx)

@DATASETS.register_module()
class ScanNetDataset(Dataset):
    class2id = np.array(VALID_CLASS_IDS_20)

    def __init__(self, split='train', data_root='data/scannet', transform=None, test_mode=False, test_cfg=None, loop=1):
        super(ScanNetDataset, self).__init__()
        self.data_root = data_root
        self.split = split
        self.transform = Compose(transform)
        self.loop = loop if not test_mode else 1
        self.test_mode = test_mode
        self.test_cfg = test_cfg if test_mode else None
        if test_mode:
            self.test_voxelize = TRANSFORMS.build(self.test_cfg.voxelize)
            self.test_crop = TRANSFORMS.build(self.test_cfg.crop) if self.test_cfg.crop else None
            self.post_transform = Compose(self.test_cfg.post_transform)
            self.aug_transform = [Compose(aug) for aug in self.test_cfg.aug_transform]
        self.data_list = self.get_data_list()
        logger = get_root_logger()
        logger.info('Totally {} x {} samples in {} set.'.format(len(self.data_list), self.loop, split))

    def get_data_list(self):
        if isinstance(self.split, str):
            data_list = glob.glob(os.path.join(self.data_root, self.split, '*.pth'))
        elif isinstance(self.split, list):
            data_list = []
            for split in self.split:
                data_list += glob.glob(os.path.join(self.data_root, split, '*.pth'))
        else:
            raise NotImplementedError
        return data_list

    def get_data(self, idx):
        data = torch.load(self.data_list[idx % len(self.data_list)])
        coord = data['coord']
        color = data['color']
        normal = data['normal']
        if 'semantic_gt20' in data.keys():
            label = data['semantic_gt20'].reshape([-1])
        else:
            label = np.ones(coord.shape[0]) * 255
        data_dict = dict(coord=coord, normal=normal, color=color, label=label)
        return data_dict

    def get_data_name(self, idx):
        return os.path.basename(self.data_list[idx % len(self.data_list)]).split('.')[0]

    def prepare_train_data(self, idx):
        data_dict = self.get_data(idx)
        data_dict = self.transform(data_dict)
        return data_dict

    def prepare_test_data(self, idx):
        data_dict = self.get_data(idx)
        label = data_dict.pop('label')
        data_dict = self.transform(data_dict)
        data_dict_list = []
        for aug in self.aug_transform:
            data_dict_list.append(aug(deepcopy(data_dict)))
        input_dict_list = []
        for data in data_dict_list:
            data_part_list = self.test_voxelize(data)
            for data_part in data_part_list:
                if self.test_crop:
                    data_part = self.test_crop(data_part)
                else:
                    data_part = [data_part]
                input_dict_list += data_part
        for i in range(len(input_dict_list)):
            input_dict_list[i] = self.post_transform(input_dict_list[i])
        return (input_dict_list, label)

    def __getitem__(self, idx):
        if self.test_mode:
            return self.prepare_test_data(idx)
        else:
            return self.prepare_train_data(idx)

    def __len__(self):
        return len(self.data_list) * self.loop

def __getitem__(self, idx):
    if self.test_mode:
        return self.prepare_test_data(idx)
    else:
        return self.prepare_train_data(idx)

