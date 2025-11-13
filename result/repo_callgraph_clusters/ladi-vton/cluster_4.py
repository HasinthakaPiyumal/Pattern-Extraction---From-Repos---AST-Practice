# Cluster 4

def make_custom_stats(dresscode_dataroot: str, vitonhd_dataroot: str):
    if dresscode_dataroot is not None:
        dresscode_filesplit = os.path.join(dresscode_dataroot, f'test_pairs_paired.txt')
        with open(dresscode_filesplit, 'r') as f:
            lines = f.read().splitlines()
        for category in ['lower_body', 'upper_body', 'dresses']:
            if not fid.test_stats_exists(f'dresscode_{category}', mode='clean'):
                paths = [os.path.join(dresscode_dataroot, category, 'images', line.strip().split()[0]) for line in lines if os.path.exists(os.path.join(dresscode_dataroot, category, 'images', line.strip().split()[0]))]
                tmp_folder = f'/tmp/dresscode/{category}'
                os.makedirs(tmp_folder, exist_ok=True)
                for path in tqdm(paths):
                    shutil.copy(path, tmp_folder)
                fid.make_custom_stats(f'dresscode_{category}', tmp_folder, mode='clean', verbose=True)
        if not fid.test_stats_exists(f'dresscode_all', mode='clean'):
            paths = [os.path.join(dresscode_dataroot, category, 'images', line.strip().split()[0]) for line in lines for category in ['lower_body', 'upper_body', 'dresses'] if os.path.exists(os.path.join(dresscode_dataroot, category, 'images', line.strip().split()[0]))]
            tmp_folder = f'/tmp/dresscode/all'
            os.makedirs(tmp_folder, exist_ok=True)
            for path in tqdm(paths):
                shutil.copy(path, tmp_folder)
            fid.make_custom_stats(f'dresscode_all', tmp_folder, mode='clean', verbose=True)
    if vitonhd_dataroot is not None:
        if not fid.test_stats_exists(f'vitonhd_all', mode='clean'):
            fid.make_custom_stats(f'vitonhd_all', os.path.join(vitonhd_dataroot, 'test', 'image'), mode='clean', verbose=True)
        if not fid.test_stats_exists(f'vitonhd_upper_body', mode='clean'):
            fid.make_custom_stats(f'vitonhd_upper_body', os.path.join(vitonhd_dataroot, 'test', 'image'), mode='clean', verbose=True)

class GTTestDataset(torch.utils.data.Dataset):

    def __init__(self, dataroot: str, dataset: str, category: str, transform: transforms.Compose):
        """
        Dataset for the ground truth test images
        """
        assert dataset in ['dresscode', 'vitonhd'], 'Unsupported dataset'
        assert category in ['all', 'dresses', 'lower_body', 'upper_body'], 'Unsupported category'
        self.dataset = dataset
        self.category = category
        self.transform = transform
        self.dataroot = dataroot
        if dataset == 'dresscode':
            filepath = os.path.join(dataroot, f'test_pairs_paired.txt')
            with open(filepath, 'r') as f:
                lines = f.read().splitlines()
            if category in ['lower_body', 'upper_body', 'dresses']:
                self.paths = sorted([os.path.join(dataroot, category, 'images', line.strip().split()[0]) for line in lines if os.path.exists(os.path.join(dataroot, category, 'images', line.strip().split()[0]))])
            else:
                self.paths = sorted([os.path.join(dataroot, category, 'images', line.strip().split()[0]) for line in lines for category in ['lower_body', 'upper_body', 'dresses'] if os.path.exists(os.path.join(dataroot, category, 'images', line.strip().split()[0]))])
        else:
            filepath = os.path.join(dataroot, f'test_pairs.txt')
            with open(filepath, 'r') as f:
                lines = f.read().splitlines()
            self.paths = sorted([os.path.join(dataroot, 'test', 'image', line.strip().split()[0]) for line in lines])

    def __len__(self):
        return len(self.paths)

    def __getitem__(self, idx):
        path = self.paths[idx]
        name = os.path.splitext(os.path.basename(path))[0]
        img = self.transform(PIL.Image.open(path).convert('RGB'))
        return (img, name)

def __init__(self, dataroot: str, dataset: str, category: str, transform: transforms.Compose):
    """
        Dataset for the ground truth test images
        """
    assert dataset in ['dresscode', 'vitonhd'], 'Unsupported dataset'
    assert category in ['all', 'dresses', 'lower_body', 'upper_body'], 'Unsupported category'
    self.dataset = dataset
    self.category = category
    self.transform = transform
    self.dataroot = dataroot
    if dataset == 'dresscode':
        filepath = os.path.join(dataroot, f'test_pairs_paired.txt')
        with open(filepath, 'r') as f:
            lines = f.read().splitlines()
        if category in ['lower_body', 'upper_body', 'dresses']:
            self.paths = sorted([os.path.join(dataroot, category, 'images', line.strip().split()[0]) for line in lines if os.path.exists(os.path.join(dataroot, category, 'images', line.strip().split()[0]))])
        else:
            self.paths = sorted([os.path.join(dataroot, category, 'images', line.strip().split()[0]) for line in lines for category in ['lower_body', 'upper_body', 'dresses'] if os.path.exists(os.path.join(dataroot, category, 'images', line.strip().split()[0]))])
    else:
        filepath = os.path.join(dataroot, f'test_pairs.txt')
        with open(filepath, 'r') as f:
            lines = f.read().splitlines()
        self.paths = sorted([os.path.join(dataroot, 'test', 'image', line.strip().split()[0]) for line in lines])

class GenTestDataset(torch.utils.data.Dataset):

    def __init__(self, gen_folder: str, category: str, transform: transforms.Compose):
        """
        Dataset for the ground truth test images
        """
        assert category in ['all', 'dresses', 'lower_body', 'upper_body'], 'Unsupported category'
        self.category = category
        self.transform = transform
        self.gen_folder = gen_folder
        if category in ['lower_body', 'upper_body', 'dresses']:
            self.paths = sorted([os.path.join(gen_folder, category, name) for name in os.listdir(os.path.join(gen_folder, category))])
        elif category == 'all':
            existing_categories = []
            for category in ['lower_body', 'upper_body', 'dresses']:
                if os.path.exists(os.path.join(gen_folder, category)):
                    existing_categories.append(category)
            self.paths = sorted([os.path.join(gen_folder, category, name) for category in existing_categories for name in os.listdir(os.path.join(gen_folder, category)) if os.path.exists(os.path.join(gen_folder, category, name))])
        else:
            raise ValueError('Unsupported category')

    def __len__(self):
        return len(self.paths)

    def __getitem__(self, idx):
        path = self.paths[idx]
        name = os.path.splitext(os.path.basename(path))[0]
        img = self.transform(PIL.Image.open(path).convert('RGB'))
        return (img, name)

def __init__(self, gen_folder: str, category: str, transform: transforms.Compose):
    """
        Dataset for the ground truth test images
        """
    assert category in ['all', 'dresses', 'lower_body', 'upper_body'], 'Unsupported category'
    self.category = category
    self.transform = transform
    self.gen_folder = gen_folder
    if category in ['lower_body', 'upper_body', 'dresses']:
        self.paths = sorted([os.path.join(gen_folder, category, name) for name in os.listdir(os.path.join(gen_folder, category))])
    elif category == 'all':
        existing_categories = []
        for category in ['lower_body', 'upper_body', 'dresses']:
            if os.path.exists(os.path.join(gen_folder, category)):
                existing_categories.append(category)
        self.paths = sorted([os.path.join(gen_folder, category, name) for category in existing_categories for name in os.listdir(os.path.join(gen_folder, category)) if os.path.exists(os.path.join(gen_folder, category, name))])
    else:
        raise ValueError('Unsupported category')

def compute_metrics(gen_folder: str, test_order: str, dataset: str, category: str, metrics2compute: List[str], dresscode_dataroot: str, vitonhd_dataroot: str, generated_size: Tuple[int, int]=(512, 384), batch_size: int=32, workers: int=8) -> Dict[str, float]:
    """
    Computes the metrics for the generated images in gen_folder
    """
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    assert test_order in ['paired', 'unpaired']
    assert dataset in ['dresscode', 'vitonhd'], 'Unsupported dataset'
    assert category in ['all', 'dresses', 'lower_body', 'upper_body'], 'Unsupported category'
    if dataset == 'dresscode':
        gt_folder = dresscode_dataroot
    elif dataset == 'vitonhd':
        gt_folder = vitonhd_dataroot
    else:
        raise ValueError('Unsupported dataset')
    for m in metrics2compute:
        assert m in ['all', 'ssim_score', 'lpips_score', 'fid_score', 'kid_score', 'is_score'], 'Unsupported metric'
    if metrics2compute == ['all']:
        metrics2compute = ['ssim_score', 'lpips_score', 'fid_score', 'kid_score', 'is_score']
    if category == 'all':
        if 'fid_score' in metrics2compute or 'all' in metrics2compute:
            if not fid.test_stats_exists(f'{dataset}_all', mode='clean'):
                make_custom_stats(dresscode_dataroot, vitonhd_dataroot)
            fid_score = fid.compute_fid(gen_folder, dataset_name=f'{dataset}_all', mode='clean', dataset_split='custom', verbose=True, use_dataparallel=False)
        if 'kid_score' in metrics2compute or 'all' in metrics2compute:
            if not fid.test_stats_exists(f'{dataset}_all', mode='clean'):
                make_custom_stats(dresscode_dataroot, vitonhd_dataroot)
            kid_score = fid.compute_kid(gen_folder, dataset_name=f'{dataset}_all', mode='clean', dataset_split='custom', verbose=True, use_dataparallel=False)
    else:
        if 'fid_score' in metrics2compute or 'all' in metrics2compute:
            if not fid.test_stats_exists(f'{dataset}_{category}', mode='clean'):
                make_custom_stats(dresscode_dataroot, vitonhd_dataroot)
            fid_score = fid.compute_fid(os.path.join(gen_folder, category), dataset_name=f'{dataset}_{category}', mode='clean', verbose=True, dataset_split='custom', use_dataparallel=False)
        if 'kid_score' in metrics2compute or 'all' in metrics2compute:
            if not fid.test_stats_exists(f'{dataset}_{category}', mode='clean'):
                make_custom_stats(dresscode_dataroot, vitonhd_dataroot)
            kid_score = fid.compute_kid(os.path.join(gen_folder, category), dataset_name=f'{dataset}_{category}', mode='clean', verbose=True, dataset_split='custom', use_dataparallel=False)
    trans = transforms.Compose([transforms.Resize(generated_size), transforms.ToTensor()])
    gen_dataset = GenTestDataset(gen_folder, category, transform=trans)
    gt_dataset = GTTestDataset(gt_folder, dataset, category, trans)
    gen_loader = DataLoader(gen_dataset, batch_size=batch_size, shuffle=False, num_workers=workers)
    gt_loader = DataLoader(gt_dataset, batch_size=batch_size, shuffle=False, num_workers=workers)
    if 'is_score' in metrics2compute or 'all' in metrics2compute:
        model_is = InceptionScore(normalize=True).to(device)
    if 'ssim_score' in metrics2compute or 'all' in metrics2compute:
        ssim = StructuralSimilarityIndexMeasure(data_range=1.0).to(device)
    if 'lpips_score' in metrics2compute or 'all' in metrics2compute:
        lpips = LearnedPerceptualImagePatchSimilarity(net='alex', normalize=True).to(device)
    for idx, (gen_batch, gt_batch) in tqdm(enumerate(zip(gen_loader, gt_loader)), total=len(gt_loader)):
        gen_images, gen_names = gen_batch
        gt_images, gt_names = gt_batch
        assert gen_names == gt_names
        gen_images = gen_images.to(device)
        gt_images = gt_images.to(device)
        if 'is_score' in metrics2compute or 'all' in metrics2compute:
            model_is.update(gen_images)
        if 'ssim_score' in metrics2compute or 'all' in metrics2compute:
            ssim.update(gen_images, gt_images)
        if 'lpips_score' in metrics2compute or 'all' in metrics2compute:
            lpips.update(gen_images, gt_images)
    if 'is_score' in metrics2compute or 'all' in metrics2compute:
        is_score, is_std = model_is.compute()
    if 'ssim_score' in metrics2compute or 'all' in metrics2compute:
        ssim_score = ssim.compute()
    if 'lpips_score' in metrics2compute or 'all' in metrics2compute:
        lpips_score = lpips.compute()
    results = {}
    for m in metrics2compute:
        if torch.is_tensor(locals()[m]):
            results[m] = locals()[m].item()
        else:
            results[m] = locals()[m]
    return results

class DressCodeDataset(data.Dataset):

    def __init__(self, dataroot_path: str, phase: Literal['train', 'test'], radius=5, caption_filename: str='dresscode.json', order: Literal['paired', 'unpaired']='paired', outputlist: Tuple[str]=('c_name', 'im_name', 'cloth', 'image', 'im_cloth', 'shape', 'pose_map', 'parse_array', 'im_mask', 'inpaint_mask', 'parse_mask_total', 'captions', 'category', 'warped_cloth', 'clip_cloth_features'), category: Tuple[str]=('dresses', 'upper_body', 'lower_body'), size: Tuple[int, int]=(512, 384)):
        super().__init__()
        self.dataroot = dataroot_path
        self.phase = phase
        self.category = category
        self.outputlist = outputlist
        self.height = size[0]
        self.width = size[1]
        self.radius = radius
        self.transform = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))])
        self.transform2D = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.5,), (0.5,))])
        self.order = order
        im_names = []
        c_names = []
        dataroot_names = []
        possible_outputs = ['c_name', 'im_name', 'cloth', 'image', 'im_cloth', 'shape', 'im_head', 'im_pose', 'pose_map', 'parse_array', 'dense_labels', 'dense_uv', 'skeleton', 'im_mask', 'inpaint_mask', 'parse_mask_total', 'captions', 'category', 'hands', 'parse_head_2', 'warped_cloth', 'clip_cloth_features']
        assert all((x in possible_outputs for x in outputlist))
        if 'captions' in self.outputlist:
            try:
                with open(PROJECT_ROOT / 'data' / 'noun_chunks' / caption_filename, 'r') as f:
                    self.captions_dict = json.load(f)
            except FileNotFoundError as e:
                print(f'File {caption_filename} not found. NO captions will be loaded.')
        for c in category:
            assert c in ['dresses', 'upper_body', 'lower_body']
            dataroot = os.path.join(self.dataroot, c)
            if phase == 'train':
                filename = os.path.join(dataroot, f'{phase}_pairs.txt')
            else:
                filename = os.path.join(dataroot, f'{phase}_pairs_{order}.txt')
            with open(filename, 'r') as f:
                for line in f.readlines():
                    im_name, c_name = line.strip().split()
                    im_names.append(im_name)
                    c_names.append(c_name)
                    dataroot_names.append(dataroot)
        self.im_names = im_names
        self.c_names = c_names
        self.dataroot_names = dataroot_names
        if 'clip_cloth_features' in self.outputlist:
            self.clip_cloth_features = torch.load(os.path.join(PROJECT_ROOT / 'data', 'clip_cloth_embeddings', 'dresscode', f'{phase}_last_hidden_state_features.pt'), map_location='cpu').detach().requires_grad_(False)
            with open(os.path.join(PROJECT_ROOT / 'data', 'clip_cloth_embeddings', 'dresscode', f'{phase}_features_names.pkl'), 'rb') as f:
                self.clip_cloth_features_names = pickle.load(f)

    def __getitem__(self, index):
        c_name = self.c_names[index]
        im_name = self.im_names[index]
        dataroot = self.dataroot_names[index]
        category = dataroot.split('/')[-1]
        if 'captions' in self.outputlist:
            captions = self.captions_dict[c_name.split('_')[0]]
            if self.phase == 'train':
                random.shuffle(captions)
            captions = ', '.join(captions)
        if 'clip_cloth_features' in self.outputlist:
            clip_cloth_features = self.clip_cloth_features[self.clip_cloth_features_names.index(c_name)].float()
        if 'cloth' in self.outputlist:
            cloth = Image.open(os.path.join(dataroot, 'images', c_name))
            mask = Image.open(os.path.join(dataroot, 'masks', c_name.replace('.jpg', '.png')))
            cloth = Image.composite(ImageOps.invert(mask.convert('L')), cloth, ImageOps.invert(mask.convert('L')))
            cloth = cloth.resize((self.width, self.height))
            cloth = self.transform(cloth)
        if 'image' in self.outputlist or 'im_head' in self.outputlist or 'im_cloth' in self.outputlist:
            image = Image.open(os.path.join(dataroot, 'images', im_name))
            image = image.resize((self.width, self.height))
            image = self.transform(image)
        if 'warped_cloth' in self.outputlist:
            if self.order == 'unpaired':
                warped_cloth = Image.open(os.path.join(PROJECT_ROOT, 'data', 'warped_cloths_unpaired', 'dresscode', category, im_name.replace('.jpg', '') + '_' + c_name))
                warped_cloth = warped_cloth.resize((self.width, self.height))
                warped_cloth = self.transform(warped_cloth)
            elif self.order == 'paired':
                warped_cloth = Image.open(os.path.join(PROJECT_ROOT, 'data', 'warped_cloths', 'dresscode', category, im_name.replace('.jpg', '') + '_' + c_name))
                warped_cloth = warped_cloth.resize((self.width, self.height))
                warped_cloth = self.transform(warped_cloth)
            else:
                raise ValueError(f"Order {self.order} not implemented. Please choose between 'paired' and 'unpaired'.")
        if 'skeleton' in self.outputlist:
            skeleton = Image.open(os.path.join(dataroot, 'skeletons', im_name.replace('_0', '_5')))
            skeleton = skeleton.resize((self.width, self.height))
            skeleton = self.transform(skeleton)
        if 'im_pose' in self.outputlist or 'parser_mask' in self.outputlist or 'im_mask' in self.outputlist or ('parse_mask_total' in self.outputlist) or ('parse_array' in self.outputlist) or ('pose_map' in self.outputlist) or ('parse_array' in self.outputlist) or ('shape' in self.outputlist) or ('im_head' in self.outputlist):
            parse_name = im_name.replace('_0.jpg', '_4.png')
            im_parse = Image.open(os.path.join(dataroot, 'label_maps', parse_name))
            im_parse = im_parse.resize((self.width, self.height), Image.NEAREST)
            parse_array = np.array(im_parse)
            parse_shape = (parse_array > 0).astype(np.float32)
            parse_head = (parse_array == 1).astype(np.float32) + (parse_array == 2).astype(np.float32) + (parse_array == 3).astype(np.float32) + (parse_array == 11).astype(np.float32)
            parser_mask_fixed = (parse_array == label_map['hair']).astype(np.float32) + (parse_array == label_map['left_shoe']).astype(np.float32) + (parse_array == label_map['right_shoe']).astype(np.float32) + (parse_array == label_map['hat']).astype(np.float32) + (parse_array == label_map['sunglasses']).astype(np.float32) + (parse_array == label_map['scarf']).astype(np.float32) + (parse_array == label_map['bag']).astype(np.float32)
            parser_mask_changeable = (parse_array == label_map['background']).astype(np.float32)
            arms = (parse_array == 14).astype(np.float32) + (parse_array == 15).astype(np.float32)
            if dataroot.split('/')[-1] == 'dresses':
                label_cat = 7
                parse_cloth = (parse_array == 7).astype(np.float32)
                parse_mask = (parse_array == 7).astype(np.float32) + (parse_array == 12).astype(np.float32) + (parse_array == 13).astype(np.float32)
                parser_mask_changeable += np.logical_and(parse_array, np.logical_not(parser_mask_fixed))
            elif dataroot.split('/')[-1] == 'upper_body':
                label_cat = 4
                parse_cloth = (parse_array == 4).astype(np.float32)
                parse_mask = (parse_array == 4).astype(np.float32)
                parser_mask_fixed += (parse_array == label_map['skirt']).astype(np.float32) + (parse_array == label_map['pants']).astype(np.float32)
                parser_mask_changeable += np.logical_and(parse_array, np.logical_not(parser_mask_fixed))
            elif dataroot.split('/')[-1] == 'lower_body':
                label_cat = 6
                parse_cloth = (parse_array == 6).astype(np.float32)
                parse_mask = (parse_array == 6).astype(np.float32) + (parse_array == 12).astype(np.float32) + (parse_array == 13).astype(np.float32)
                parser_mask_fixed += (parse_array == label_map['upper_clothes']).astype(np.float32) + (parse_array == 14).astype(np.float32) + (parse_array == 15).astype(np.float32)
                parser_mask_changeable += np.logical_and(parse_array, np.logical_not(parser_mask_fixed))
            else:
                raise NotImplementedError
            parse_head = torch.from_numpy(parse_head)
            parse_cloth = torch.from_numpy(parse_cloth)
            parse_mask = torch.from_numpy(parse_mask)
            parser_mask_fixed = torch.from_numpy(parser_mask_fixed)
            parser_mask_changeable = torch.from_numpy(parser_mask_changeable)
            parse_without_cloth = np.logical_and(parse_shape, np.logical_not(parse_mask))
            parse_mask = parse_mask.cpu().numpy()
            if 'im_head' in self.outputlist:
                im_head = image * parse_head - (1 - parse_head)
            if 'im_cloth' in self.outputlist:
                im_cloth = image * parse_cloth + (1 - parse_cloth)
            parse_shape = Image.fromarray((parse_shape * 255).astype(np.uint8))
            parse_shape = parse_shape.resize((self.width // 16, self.height // 16), Image.BILINEAR)
            parse_shape = parse_shape.resize((self.width, self.height), Image.BILINEAR)
            shape = self.transform2D(parse_shape)
            pose_name = im_name.replace('_0.jpg', '_2.json')
            with open(os.path.join(dataroot, 'keypoints', pose_name), 'r') as f:
                pose_label = json.load(f)
                pose_data = pose_label['keypoints']
                pose_data = np.array(pose_data)
                pose_data = pose_data.reshape((-1, 4))
            point_num = pose_data.shape[0]
            pose_map = torch.zeros(point_num, self.height, self.width)
            r = self.radius * (self.height / 512.0)
            im_pose = Image.new('L', (self.width, self.height))
            pose_draw = ImageDraw.Draw(im_pose)
            neck = Image.new('L', (self.width, self.height))
            neck_draw = ImageDraw.Draw(neck)
            for i in range(point_num):
                one_map = Image.new('L', (self.width, self.height))
                draw = ImageDraw.Draw(one_map)
                point_x = np.multiply(pose_data[i, 0], self.width / 384.0)
                point_y = np.multiply(pose_data[i, 1], self.height / 512.0)
                if point_x > 1 and point_y > 1:
                    draw.rectangle((point_x - r, point_y - r, point_x + r, point_y + r), 'white', 'white')
                    pose_draw.rectangle((point_x - r, point_y - r, point_x + r, point_y + r), 'white', 'white')
                    if i == 2 or i == 5:
                        neck_draw.ellipse((point_x - r * 4, point_y - r * 4, point_x + r * 4, point_y + r * 4), 'white', 'white')
                one_map = self.transform2D(one_map)
                pose_map[i] = one_map[0]
            d = []
            for pose_d in pose_data:
                ux = pose_d[0] / 384.0
                uy = pose_d[1] / 512.0
                px = ux * self.width
                py = uy * self.height
                d.append(kpoint_to_heatmap(np.array([px, py]), (self.height, self.width), 9))
            pose_map = torch.stack(d)
            im_pose = self.transform2D(im_pose)
            im_arms = Image.new('L', (self.width, self.height))
            arms_draw = ImageDraw.Draw(im_arms)
            if dataroot.split('/')[-1] == 'dresses' or dataroot.split('/')[-1] == 'upper_body' or dataroot.split('/')[-1] == 'lower_body':
                with open(os.path.join(dataroot, 'keypoints', pose_name), 'r') as f:
                    data = json.load(f)
                    shoulder_right = np.multiply(tuple(data['keypoints'][2][:2]), self.height / 512.0)
                    shoulder_left = np.multiply(tuple(data['keypoints'][5][:2]), self.height / 512.0)
                    elbow_right = np.multiply(tuple(data['keypoints'][3][:2]), self.height / 512.0)
                    elbow_left = np.multiply(tuple(data['keypoints'][6][:2]), self.height / 512.0)
                    wrist_right = np.multiply(tuple(data['keypoints'][4][:2]), self.height / 512.0)
                    wrist_left = np.multiply(tuple(data['keypoints'][7][:2]), self.height / 512.0)
                    if wrist_right[0] <= 1.0 and wrist_right[1] <= 1.0:
                        if elbow_right[0] <= 1.0 and elbow_right[1] <= 1.0:
                            arms_draw.line(np.concatenate((wrist_left, elbow_left, shoulder_left, shoulder_right)).astype(np.uint16).tolist(), 'white', 45, 'curve')
                        else:
                            arms_draw.line(np.concatenate((wrist_left, elbow_left, shoulder_left, shoulder_right, elbow_right)).astype(np.uint16).tolist(), 'white', 45, 'curve')
                    elif wrist_left[0] <= 1.0 and wrist_left[1] <= 1.0:
                        if elbow_left[0] <= 1.0 and elbow_left[1] <= 1.0:
                            arms_draw.line(np.concatenate((shoulder_left, shoulder_right, elbow_right, wrist_right)).astype(np.uint16).tolist(), 'white', 45, 'curve')
                        else:
                            arms_draw.line(np.concatenate((elbow_left, shoulder_left, shoulder_right, elbow_right, wrist_right)).astype(np.uint16).tolist(), 'white', 45, 'curve')
                    else:
                        arms_draw.line(np.concatenate((wrist_left, elbow_left, shoulder_left, shoulder_right, elbow_right, wrist_right)).astype(np.uint16).tolist(), 'white', 45, 'curve')
                hands = np.logical_and(np.logical_not(im_arms), arms)
                if dataroot.split('/')[-1] == 'dresses' or dataroot.split('/')[-1] == 'upper_body':
                    parse_mask += im_arms
                    parser_mask_fixed += hands
            parse_head_2 = torch.clone(parse_head)
            if dataroot.split('/')[-1] == 'dresses' or dataroot.split('/')[-1] == 'upper_body':
                with open(os.path.join(dataroot, 'keypoints', pose_name), 'r') as f:
                    data = json.load(f)
                    points = []
                    points.append(np.multiply(tuple(data['keypoints'][2][:2]), self.height / 512.0))
                    points.append(np.multiply(tuple(data['keypoints'][5][:2]), self.height / 512.0))
                    x_coords, y_coords = zip(*points)
                    A = np.vstack([x_coords, np.ones(len(x_coords))]).T
                    m, c = lstsq(A, y_coords, rcond=None)[0]
                    for i in range(parse_array.shape[1]):
                        y = i * m + c
                        parse_head_2[int(y - 20 * (self.height / 512.0)):, i] = 0
            parser_mask_fixed = np.logical_or(parser_mask_fixed, np.array(parse_head_2, dtype=np.uint16))
            parse_mask += np.logical_or(parse_mask, np.logical_and(np.array(parse_head, dtype=np.uint16), np.logical_not(np.array(parse_head_2, dtype=np.uint16))))
            parse_mask = cv2.dilate(parse_mask, np.ones((5, 5), np.uint16), iterations=5)
            parse_mask = np.logical_and(parser_mask_changeable, np.logical_not(parse_mask))
            parse_mask_total = np.logical_or(parse_mask, parser_mask_fixed)
            im_mask = image * parse_mask_total
            inpaint_mask = 1 - parse_mask_total
            inpaint_mask = inpaint_mask.unsqueeze(0)
            parse_mask_total = parse_mask_total.numpy()
            parse_mask_total = parse_array * parse_mask_total
            parse_mask_total = torch.from_numpy(parse_mask_total)
        if 'dense_uv' in self.outputlist:
            dense_uv = np.load(os.path.join(dataroot, 'dense', im_name.replace('_0.jpg', '_5_uv.npz')))
            dense_uv = dense_uv['uv']
            dense_uv = torch.from_numpy(dense_uv)
            dense_uv = transforms.functional.resize(dense_uv, (self.height, self.width), antialias=True)
        if 'dense_labels' in self.outputlist:
            labels = Image.open(os.path.join(dataroot, 'dense', im_name.replace('_0.jpg', '_5.png')))
            labels = labels.resize((self.width, self.height), Image.NEAREST)
            labels = np.array(labels)
        result = {}
        for k in self.outputlist:
            result[k] = vars()[k]
        return result

    def __len__(self):
        return len(self.c_names)

def __init__(self, dataroot_path: str, phase: Literal['train', 'test'], radius=5, caption_filename: str='dresscode.json', order: Literal['paired', 'unpaired']='paired', outputlist: Tuple[str]=('c_name', 'im_name', 'cloth', 'image', 'im_cloth', 'shape', 'pose_map', 'parse_array', 'im_mask', 'inpaint_mask', 'parse_mask_total', 'captions', 'category', 'warped_cloth', 'clip_cloth_features'), category: Tuple[str]=('dresses', 'upper_body', 'lower_body'), size: Tuple[int, int]=(512, 384)):
    super().__init__()
    self.dataroot = dataroot_path
    self.phase = phase
    self.category = category
    self.outputlist = outputlist
    self.height = size[0]
    self.width = size[1]
    self.radius = radius
    self.transform = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))])
    self.transform2D = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.5,), (0.5,))])
    self.order = order
    im_names = []
    c_names = []
    dataroot_names = []
    possible_outputs = ['c_name', 'im_name', 'cloth', 'image', 'im_cloth', 'shape', 'im_head', 'im_pose', 'pose_map', 'parse_array', 'dense_labels', 'dense_uv', 'skeleton', 'im_mask', 'inpaint_mask', 'parse_mask_total', 'captions', 'category', 'hands', 'parse_head_2', 'warped_cloth', 'clip_cloth_features']
    assert all((x in possible_outputs for x in outputlist))
    if 'captions' in self.outputlist:
        try:
            with open(PROJECT_ROOT / 'data' / 'noun_chunks' / caption_filename, 'r') as f:
                self.captions_dict = json.load(f)
        except FileNotFoundError as e:
            print(f'File {caption_filename} not found. NO captions will be loaded.')
    for c in category:
        assert c in ['dresses', 'upper_body', 'lower_body']
        dataroot = os.path.join(self.dataroot, c)
        if phase == 'train':
            filename = os.path.join(dataroot, f'{phase}_pairs.txt')
        else:
            filename = os.path.join(dataroot, f'{phase}_pairs_{order}.txt')
        with open(filename, 'r') as f:
            for line in f.readlines():
                im_name, c_name = line.strip().split()
                im_names.append(im_name)
                c_names.append(c_name)
                dataroot_names.append(dataroot)
    self.im_names = im_names
    self.c_names = c_names
    self.dataroot_names = dataroot_names
    if 'clip_cloth_features' in self.outputlist:
        self.clip_cloth_features = torch.load(os.path.join(PROJECT_ROOT / 'data', 'clip_cloth_embeddings', 'dresscode', f'{phase}_last_hidden_state_features.pt'), map_location='cpu').detach().requires_grad_(False)
        with open(os.path.join(PROJECT_ROOT / 'data', 'clip_cloth_embeddings', 'dresscode', f'{phase}_features_names.pkl'), 'rb') as f:
            self.clip_cloth_features_names = pickle.load(f)

class VitonHDDataset(data.Dataset):

    def __init__(self, dataroot_path: str, phase: Literal['train', 'test'], radius=5, caption_filename: str='vitonhd.json', order: Literal['paired', 'unpaired']='paired', outputlist: Tuple[str]=('c_name', 'im_name', 'cloth', 'image', 'im_cloth', 'shape', 'pose_map', 'parse_array', 'im_mask', 'inpaint_mask', 'parse_mask_total', 'captions', 'category', 'warped_cloth', 'clip_cloth_features'), size: Tuple[int, int]=(512, 384)):
        super(VitonHDDataset, self).__init__()
        self.dataroot = dataroot_path
        self.phase = phase
        self.category = 'upper_body'
        self.outputlist = outputlist
        self.height = size[0]
        self.width = size[1]
        self.radius = radius
        self.transform = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))])
        self.transform2D = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.5,), (0.5,))])
        self.order = order
        im_names = []
        c_names = []
        dataroot_names = []
        possible_outputs = ['c_name', 'im_name', 'cloth', 'image', 'im_cloth', 'shape', 'im_head', 'im_pose', 'pose_map', 'parse_array', 'dense_labels', 'dense_uv', 'skeleton', 'im_mask', 'inpaint_mask', 'parse_mask_total', 'captions', 'category', 'warped_cloth', 'clip_cloth_features']
        assert all((x in possible_outputs for x in outputlist))
        if 'captions' in self.outputlist:
            try:
                with open(PROJECT_ROOT / 'data' / 'noun_chunks' / caption_filename, 'r') as f:
                    self.captions_dict = json.load(f)
            except FileNotFoundError as e:
                print(f'File {caption_filename} not found. NO captions will be loaded.')
        dataroot = self.dataroot
        if phase == 'train':
            filename = os.path.join(dataroot, f'{phase}_pairs.txt')
        else:
            filename = os.path.join(dataroot, f'{phase}_pairs.txt')
        with open(filename, 'r') as f:
            for line in f.readlines():
                if phase == 'train':
                    im_name, _ = line.strip().split()
                    c_name = im_name
                elif order == 'paired':
                    im_name, _ = line.strip().split()
                    c_name = im_name
                else:
                    im_name, c_name = line.strip().split()
                im_names.append(im_name)
                c_names.append(c_name)
                dataroot_names.append(dataroot)
        self.im_names = im_names
        self.c_names = c_names
        self.dataroot_names = dataroot_names
        if 'clip_cloth_features' in self.outputlist:
            self.clip_cloth_features = torch.load(os.path.join(PROJECT_ROOT / 'data', 'clip_cloth_embeddings', 'vitonhd', f'{phase}_last_hidden_state_features.pt'), map_location='cpu').detach().requires_grad_(False)
            with open(os.path.join(PROJECT_ROOT / 'data', 'clip_cloth_embeddings', 'vitonhd', f'{phase}_features_names.pkl'), 'rb') as f:
                self.clip_cloth_features_names = pickle.load(f)

    def __getitem__(self, index):
        c_name = self.c_names[index]
        im_name = self.im_names[index]
        dataroot = self.dataroot_names[index]
        category = 'upper_body'
        if 'captions' in self.outputlist:
            captions = self.captions_dict[c_name.split('_')[0]]
            if self.phase == 'train':
                random.shuffle(captions)
            captions = ', '.join(captions)
        if 'clip_cloth_features' in self.outputlist:
            clip_cloth_features = self.clip_cloth_features[self.clip_cloth_features_names.index(c_name)].float()
        if 'cloth' in self.outputlist:
            cloth = Image.open(os.path.join(dataroot, self.phase, 'cloth', c_name))
            cloth = cloth.resize((self.width, self.height))
            cloth = self.transform(cloth)
        if 'image' in self.outputlist or 'im_head' in self.outputlist or 'im_cloth' in self.outputlist:
            image = Image.open(os.path.join(dataroot, self.phase, 'image', im_name))
            image = image.resize((self.width, self.height))
            image = self.transform(image)
        if 'warped_cloth' in self.outputlist:
            if self.order == 'unpaired':
                warped_cloth = Image.open(os.path.join(PROJECT_ROOT, 'data', 'warped_cloths_unpaired', 'vitonhd', category, im_name.replace('.jpg', '') + '_' + c_name))
                warped_cloth = warped_cloth.resize((self.width, self.height))
                warped_cloth = self.transform(warped_cloth)
            elif self.order == 'paired':
                warped_cloth = Image.open(os.path.join(PROJECT_ROOT, 'data', 'warped_cloths', 'vitonhd', category, im_name.replace('.jpg', '') + '_' + c_name))
                warped_cloth = warped_cloth.resize((self.width, self.height))
                warped_cloth = self.transform(warped_cloth)
            else:
                raise ValueError(f'Order should be either paired or unpaired')
        labels = {0: ['background', [0, 10]], 1: ['hair', [1, 2]], 2: ['face', [4, 13]], 3: ['upper', [5, 6, 7]], 4: ['bottom', [9, 12]], 5: ['left_arm', [14]], 6: ['right_arm', [15]], 7: ['left_leg', [16]], 8: ['right_leg', [17]], 9: ['left_shoe', [18]], 10: ['right_shoe', [19]], 11: ['socks', [8]], 12: ['noise', [3, 11]]}
        if 'skeleton' in self.outputlist:
            skeleton = Image.open(os.path.join(dataroot, self.phase, 'openpose_img', im_name.replace('.jpg', '_rendered.png')))
            skeleton = skeleton.resize((self.width, self.height))
            skeleton = self.transform(skeleton)
        if 'im_pose' in self.outputlist or 'parser_mask' in self.outputlist or 'im_mask' in self.outputlist or ('parse_mask_total' in self.outputlist) or ('parse_array' in self.outputlist) or ('pose_map' in self.outputlist) or ('parse_array' in self.outputlist) or ('shape' in self.outputlist) or ('im_head' in self.outputlist):
            parse_name = im_name.replace('.jpg', '.png')
            im_parse = Image.open(os.path.join(dataroot, self.phase, 'image-parse-v3', parse_name))
            im_parse = im_parse.resize((self.width, self.height), Image.NEAREST)
            im_parse_final = transforms.ToTensor()(im_parse) * 255
            parse_array = np.array(im_parse)
            parse_shape = (parse_array > 0).astype(np.float32)
            parse_head = (parse_array == 1).astype(np.float32) + (parse_array == 2).astype(np.float32) + (parse_array == 4).astype(np.float32) + (parse_array == 13).astype(np.float32)
            parser_mask_fixed = (parse_array == 1).astype(np.float32) + (parse_array == 2).astype(np.float32) + (parse_array == 18).astype(np.float32) + (parse_array == 19).astype(np.float32)
            parser_mask_changeable = (parse_array == 0).astype(np.float32)
            arms = (parse_array == 14).astype(np.float32) + (parse_array == 15).astype(np.float32)
            parse_cloth = (parse_array == 5).astype(np.float32) + (parse_array == 6).astype(np.float32) + (parse_array == 7).astype(np.float32)
            parse_mask = (parse_array == 5).astype(np.float32) + (parse_array == 6).astype(np.float32) + (parse_array == 7).astype(np.float32)
            parser_mask_fixed = parser_mask_fixed + (parse_array == 9).astype(np.float32) + (parse_array == 12).astype(np.float32)
            parser_mask_changeable += np.logical_and(parse_array, np.logical_not(parser_mask_fixed))
            parse_head = torch.from_numpy(parse_head)
            parse_cloth = torch.from_numpy(parse_cloth)
            parse_mask = torch.from_numpy(parse_mask)
            parser_mask_fixed = torch.from_numpy(parser_mask_fixed)
            parser_mask_changeable = torch.from_numpy(parser_mask_changeable)
            parse_without_cloth = np.logical_and(parse_shape, np.logical_not(parse_mask))
            parse_mask = parse_mask.cpu().numpy()
            if 'im_head' in self.outputlist:
                im_head = image * parse_head - (1 - parse_head)
            if 'im_cloth' in self.outputlist:
                im_cloth = image * parse_cloth + (1 - parse_cloth)
            parse_shape = Image.fromarray((parse_shape * 255).astype(np.uint8))
            parse_shape = parse_shape.resize((self.width // 16, self.height // 16), Image.BILINEAR)
            parse_shape = parse_shape.resize((self.width, self.height), Image.BILINEAR)
            shape = self.transform2D(parse_shape)
            pose_name = im_name.replace('.jpg', '_keypoints.json')
            with open(os.path.join(dataroot, self.phase, 'openpose_json', pose_name), 'r') as f:
                pose_label = json.load(f)
                pose_data = pose_label['people'][0]['pose_keypoints_2d']
                pose_data = np.array(pose_data)
                pose_data = pose_data.reshape((-1, 3))[:, :2]
                pose_data[:, 0] = pose_data[:, 0] * (self.width / 768)
                pose_data[:, 1] = pose_data[:, 1] * (self.height / 1024)
            pose_mapping = get_coco_body25_mapping()
            point_num = len(pose_mapping)
            pose_map = torch.zeros(point_num, self.height, self.width)
            r = self.radius * (self.height / 512.0)
            im_pose = Image.new('L', (self.width, self.height))
            pose_draw = ImageDraw.Draw(im_pose)
            neck = Image.new('L', (self.width, self.height))
            neck_draw = ImageDraw.Draw(neck)
            for i in range(point_num):
                one_map = Image.new('L', (self.width, self.height))
                draw = ImageDraw.Draw(one_map)
                point_x = np.multiply(pose_data[pose_mapping[i], 0], 1)
                point_y = np.multiply(pose_data[pose_mapping[i], 1], 1)
                if point_x > 1 and point_y > 1:
                    draw.rectangle((point_x - r, point_y - r, point_x + r, point_y + r), 'white', 'white')
                    pose_draw.rectangle((point_x - r, point_y - r, point_x + r, point_y + r), 'white', 'white')
                    if i == 2 or i == 5:
                        neck_draw.ellipse((point_x - r * 4, point_y - r * 4, point_x + r * 4, point_y + r * 4), 'white', 'white')
                one_map = self.transform2D(one_map)
                pose_map[i] = one_map[0]
            d = []
            for idx in range(point_num):
                ux = pose_data[pose_mapping[idx], 0]
                uy = pose_data[pose_mapping[idx], 1]
                px = ux
                py = uy
                d.append(kpoint_to_heatmap(np.array([px, py]), (self.height, self.width), 9))
            pose_map = torch.stack(d)
            im_pose = self.transform2D(im_pose)
            im_arms = Image.new('L', (self.width, self.height))
            arms_draw = ImageDraw.Draw(im_arms)
            with open(os.path.join(dataroot, self.phase, 'openpose_json', pose_name), 'r') as f:
                data = json.load(f)
                data = data['people'][0]['pose_keypoints_2d']
                data = np.array(data)
                data = data.reshape((-1, 3))[:, :2]
                data[:, 0] = data[:, 0] * (self.width / 768)
                data[:, 1] = data[:, 1] * (self.height / 1024)
                shoulder_right = tuple(data[pose_mapping[2]])
                shoulder_left = tuple(data[pose_mapping[5]])
                elbow_right = tuple(data[pose_mapping[3]])
                elbow_left = tuple(data[pose_mapping[6]])
                wrist_right = tuple(data[pose_mapping[4]])
                wrist_left = tuple(data[pose_mapping[7]])
                ARM_LINE_WIDTH = int(90 / 512 * self.height)
                if wrist_right[0] <= 1.0 and wrist_right[1] <= 1.0:
                    if elbow_right[0] <= 1.0 and elbow_right[1] <= 1.0:
                        arms_draw.line(np.concatenate((wrist_left, elbow_left, shoulder_left, shoulder_right)).astype(np.uint16).tolist(), 'white', ARM_LINE_WIDTH, 'curve')
                    else:
                        arms_draw.line(np.concatenate((wrist_left, elbow_left, shoulder_left, shoulder_right, elbow_right)).astype(np.uint16).tolist(), 'white', ARM_LINE_WIDTH, 'curve')
                elif wrist_left[0] <= 1.0 and wrist_left[1] <= 1.0:
                    if elbow_left[0] <= 1.0 and elbow_left[1] <= 1.0:
                        arms_draw.line(np.concatenate((shoulder_left, shoulder_right, elbow_right, wrist_right)).astype(np.uint16).tolist(), 'white', ARM_LINE_WIDTH, 'curve')
                    else:
                        arms_draw.line(np.concatenate((elbow_left, shoulder_left, shoulder_right, elbow_right, wrist_right)).astype(np.uint16).tolist(), 'white', ARM_LINE_WIDTH, 'curve')
                else:
                    arms_draw.line(np.concatenate((wrist_left, elbow_left, shoulder_left, shoulder_right, elbow_right, wrist_right)).astype(np.uint16).tolist(), 'white', ARM_LINE_WIDTH, 'curve')
                hands = np.logical_and(np.logical_not(im_arms), arms)
                parse_mask += im_arms
                parser_mask_fixed += hands
            parse_head_2 = torch.clone(parse_head)
            parser_mask_fixed = np.logical_or(parser_mask_fixed, np.array(parse_head_2, dtype=np.uint16))
            parse_mask += np.logical_or(parse_mask, np.logical_and(np.array(parse_head, dtype=np.uint16), np.logical_not(np.array(parse_head_2, dtype=np.uint16))))
            parse_mask = cv2.dilate(parse_mask, np.ones((5, 5), np.uint16), iterations=5)
            parse_mask = np.logical_and(parser_mask_changeable, np.logical_not(parse_mask))
            parse_mask_total = np.logical_or(parse_mask, parser_mask_fixed)
            im_mask = image * parse_mask_total
            inpaint_mask = 1 - parse_mask_total
            inpaint_mask = inpaint_mask.unsqueeze(0)
            parse_mask_total = parse_mask_total.numpy()
            parse_mask_total = parse_array * parse_mask_total
            parse_mask_total = torch.from_numpy(parse_mask_total)
        if 'dense_uv' in self.outputlist:
            uv = np.load(os.path.join(dataroot, 'dense', im_name.replace('_0.jpg', '_5_uv.npz')))
            uv = uv['uv']
            uv = torch.from_numpy(uv)
            uv = transforms.functional.resize(uv, (self.height, self.width))
        if 'dense_labels' in self.outputlist:
            labels = Image.open(os.path.join(dataroot, 'dense', im_name.replace('_0.jpg', '_5.png')))
            labels = labels.resize((self.width, self.height), Image.NEAREST)
            labels = np.array(labels)
        result = {}
        for k in self.outputlist:
            result[k] = vars()[k]
        return result

    def __len__(self):
        return len(self.c_names)

def __init__(self, dataroot_path: str, phase: Literal['train', 'test'], radius=5, caption_filename: str='vitonhd.json', order: Literal['paired', 'unpaired']='paired', outputlist: Tuple[str]=('c_name', 'im_name', 'cloth', 'image', 'im_cloth', 'shape', 'pose_map', 'parse_array', 'im_mask', 'inpaint_mask', 'parse_mask_total', 'captions', 'category', 'warped_cloth', 'clip_cloth_features'), size: Tuple[int, int]=(512, 384)):
    super(VitonHDDataset, self).__init__()
    self.dataroot = dataroot_path
    self.phase = phase
    self.category = 'upper_body'
    self.outputlist = outputlist
    self.height = size[0]
    self.width = size[1]
    self.radius = radius
    self.transform = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))])
    self.transform2D = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.5,), (0.5,))])
    self.order = order
    im_names = []
    c_names = []
    dataroot_names = []
    possible_outputs = ['c_name', 'im_name', 'cloth', 'image', 'im_cloth', 'shape', 'im_head', 'im_pose', 'pose_map', 'parse_array', 'dense_labels', 'dense_uv', 'skeleton', 'im_mask', 'inpaint_mask', 'parse_mask_total', 'captions', 'category', 'warped_cloth', 'clip_cloth_features']
    assert all((x in possible_outputs for x in outputlist))
    if 'captions' in self.outputlist:
        try:
            with open(PROJECT_ROOT / 'data' / 'noun_chunks' / caption_filename, 'r') as f:
                self.captions_dict = json.load(f)
        except FileNotFoundError as e:
            print(f'File {caption_filename} not found. NO captions will be loaded.')
    dataroot = self.dataroot
    if phase == 'train':
        filename = os.path.join(dataroot, f'{phase}_pairs.txt')
    else:
        filename = os.path.join(dataroot, f'{phase}_pairs.txt')
    with open(filename, 'r') as f:
        for line in f.readlines():
            if phase == 'train':
                im_name, _ = line.strip().split()
                c_name = im_name
            elif order == 'paired':
                im_name, _ = line.strip().split()
                c_name = im_name
            else:
                im_name, c_name = line.strip().split()
            im_names.append(im_name)
            c_names.append(c_name)
            dataroot_names.append(dataroot)
    self.im_names = im_names
    self.c_names = c_names
    self.dataroot_names = dataroot_names
    if 'clip_cloth_features' in self.outputlist:
        self.clip_cloth_features = torch.load(os.path.join(PROJECT_ROOT / 'data', 'clip_cloth_embeddings', 'vitonhd', f'{phase}_last_hidden_state_features.pt'), map_location='cpu').detach().requires_grad_(False)
        with open(os.path.join(PROJECT_ROOT / 'data', 'clip_cloth_embeddings', 'vitonhd', f'{phase}_features_names.pkl'), 'rb') as f:
            self.clip_cloth_features_names = pickle.load(f)

def init_weights(net, init_type='normal'):
    print('initialization method [%s]' % init_type)
    if init_type == 'normal':
        net.apply(weights_init_normal)
    else:
        raise NotImplementedError('initialization method [%s] is not implemented' % init_type)

