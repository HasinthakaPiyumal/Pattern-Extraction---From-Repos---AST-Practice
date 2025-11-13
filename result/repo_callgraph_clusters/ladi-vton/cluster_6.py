# Cluster 6

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

def __getitem__(self, idx):
    path = self.paths[idx]
    name = os.path.splitext(os.path.basename(path))[0]
    img = self.transform(PIL.Image.open(path).convert('RGB'))
    return (img, name)

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

def __getitem__(self, idx):
    path = self.paths[idx]
    name = os.path.splitext(os.path.basename(path))[0]
    img = self.transform(PIL.Image.open(path).convert('RGB'))
    return (img, name)

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

class StableDiffusionTryOnePipeline(DiffusionPipeline):
    """
    Pipeline for text and posemap -guided image inpainting using Stable Diffusion.

    This model inherits from [`DiffusionPipeline`]. Check the superclass documentation for the generic methods the
    library implements for all the pipelines (such as downloading or saving, running on a particular device, etc.)

    Args:
        vae ([`AutoencoderKL`]):
            Variational Auto-Encoder (VAE) Model to encode and decode images to and from latent representations.
        text_encoder ([`CLIPTextModel`]):
            Frozen text-encoder. Stable Diffusion uses the text portion of
            [CLIP](https://huggingface.co/docs/transformers/model_doc/clip#transformers.CLIPTextModel), specifically
            the [clip-vit-large-patch14](https://huggingface.co/openai/clip-vit-large-patch14) variant.
        tokenizer (`CLIPTokenizer`):
            Tokenizer of class
            [CLIPTokenizer](https://huggingface.co/docs/transformers/v4.21.0/en/model_doc/clip#transformers.CLIPTokenizer).
        unet ([`UNet2DConditionModel`]): Conditional U-Net architecture to denoise the encoded image latents.
        scheduler ([`SchedulerMixin`]):
            A scheduler to be used in combination with `unet` to denoise the encoded image latents. Can be one of
            [`DDIMScheduler`], [`LMSDiscreteScheduler`], or [`PNDMScheduler`].
        safety_checker ([`StableDiffusionSafetyChecker`]):
            Classification module that estimates whether generated images could be considered offensive or harmful.
            Please, refer to the [model card](https://huggingface.co/runwayml/stable-diffusion-v1-5) for details.
        feature_extractor ([`CLIPFeatureExtractor`]):
            Model that extracts features from generated images to be used as inputs for the `safety_checker`.
    """
    _optional_components = ['safety_checker']

    def __init__(self, vae: AutoencoderKL, text_encoder: CLIPTextModel, tokenizer: CLIPTokenizer, unet: UNet2DConditionModel, scheduler: Union[DDIMScheduler, PNDMScheduler, LMSDiscreteScheduler], safety_checker=None, feature_extractor=None, requires_safety_checker: bool=False, emasc=None, emasc_int_layers=None):
        super().__init__()
        self.emasc = emasc
        self.emasc_int_layers = emasc_int_layers
        if hasattr(scheduler.config, 'steps_offset') and scheduler.config.steps_offset != 1:
            deprecation_message = f'The configuration file of this scheduler: {scheduler} is outdated. `steps_offset` should be set to 1 instead of {scheduler.config.steps_offset}. Please make sure to update the config accordingly as leaving `steps_offset` might led to incorrect results in future versions. If you have downloaded this checkpoint from the Hugging Face Hub, it would be very nice if you could open a Pull request for the `scheduler/scheduler_config.json` file'
            deprecate('steps_offset!=1', '1.0.0', deprecation_message, standard_warn=False)
            new_config = dict(scheduler.config)
            new_config['steps_offset'] = 1
            scheduler._internal_dict = FrozenDict(new_config)
        if hasattr(scheduler.config, 'skip_prk_steps') and scheduler.config.skip_prk_steps is False:
            deprecation_message = f'The configuration file of this scheduler: {scheduler} has not set the configuration `skip_prk_steps`. `skip_prk_steps` should be set to True in the configuration file. Please make sure to update the config accordingly as not setting `skip_prk_steps` in the config might lead to incorrect results in future versions. If you have downloaded this checkpoint from the Hugging Face Hub, it would be very nice if you could open a Pull request for the `scheduler/scheduler_config.json` file'
            deprecate('skip_prk_steps not set', '1.0.0', deprecation_message, standard_warn=False)
            new_config = dict(scheduler.config)
            new_config['skip_prk_steps'] = True
            scheduler._internal_dict = FrozenDict(new_config)
        if safety_checker is not None and feature_extractor is None:
            raise ValueError("Make sure to define a feature extractor when loading {self.__class__} if you want to use the safety checker. If you do not want to use the safety checker, you can pass `'safety_checker=None'` instead.")
        is_unet_version_less_0_9_0 = hasattr(unet.config, '_diffusers_version') and version.parse(version.parse(unet.config._diffusers_version).base_version) < version.parse('0.9.0.dev0')
        is_unet_sample_size_less_64 = hasattr(unet.config, 'sample_size') and unet.config.sample_size < 64
        if is_unet_version_less_0_9_0 and is_unet_sample_size_less_64:
            deprecation_message = "The configuration file of the unet has set the default `sample_size` to smaller than 64 which seems highly unlikely .If you're checkpoint is a fine-tuned version of any of the following: \n- CompVis/stable-diffusion-v1-4 \n- CompVis/stable-diffusion-v1-3 \n- CompVis/stable-diffusion-v1-2 \n- CompVis/stable-diffusion-v1-1 \n- runwayml/stable-diffusion-v1-5 \n- runwayml/stable-diffusion-inpainting \n you should change 'sample_size' to 64 in the configuration file. Please make sure to update the config accordingly as leaving `sample_size=32` in the config might lead to incorrect results in future versions. If you have downloaded this checkpoint from the Hugging Face Hub, it would be very nice if you could open a Pull request for the `unet/config.json` file"
            deprecate('sample_size<64', '1.0.0', deprecation_message, standard_warn=False)
            new_config = dict(unet.config)
            new_config['sample_size'] = 64
            unet._internal_dict = FrozenDict(new_config)
        self.register_modules(vae=vae, text_encoder=text_encoder, tokenizer=tokenizer, unet=unet, scheduler=scheduler, safety_checker=safety_checker, feature_extractor=feature_extractor)
        self.vae_scale_factor = 2 ** (len(self.vae.config.block_out_channels) - 1)
        self.register_to_config(requires_safety_checker=requires_safety_checker)

    def enable_sequential_cpu_offload(self, gpu_id=0):
        """
        Offloads all models to CPU using accelerate, significantly reducing memory usage. When called, unet,
        text_encoder, vae and safety checker have their state dicts saved to CPU and then are moved to a
        `torch.device('meta') and loaded to GPU only when their specific submodule has its `forward` method called.
        """
        if is_accelerate_available():
            from accelerate import cpu_offload
        else:
            raise ImportError('Please install accelerate via `pip install accelerate`')
        device = torch.device(f'cuda:{gpu_id}')
        for cpu_offloaded_model in [self.unet, self.text_encoder, self.vae]:
            if cpu_offloaded_model is not None:
                cpu_offload(cpu_offloaded_model, device)
        if self.safety_checker is not None:
            cpu_offload(self.safety_checker.vision_model, device)

    @property
    def _execution_device(self):
        """
        Returns the device on which the pipeline's models will be executed. After calling
        `pipeline.enable_sequential_cpu_offload()` the execution device can only be inferred from Accelerate's module
        hooks.
        """
        if self.device != torch.device('meta') or not hasattr(self.unet, '_hf_hook'):
            return self.device
        for module in self.unet.modules():
            if hasattr(module, '_hf_hook') and hasattr(module._hf_hook, 'execution_device') and (module._hf_hook.execution_device is not None):
                return torch.device(module._hf_hook.execution_device)
        return self.device

    def _encode_prompt(self, prompt, device, num_images_per_prompt, do_classifier_free_guidance, negative_prompt=None, prompt_embeds: Optional[torch.FloatTensor]=None, negative_prompt_embeds: Optional[torch.FloatTensor]=None):
        """
        Encodes the prompt into text encoder hidden states.
        Args:
             prompt (`str` or `List[str]`, *optional*):
                prompt to be encoded
            device: (`torch.device`):
                torch device
            num_images_per_prompt (`int`):
                number of images that should be generated per prompt
            do_classifier_free_guidance (`bool`):
                whether to use classifier free guidance or not
            negative_prompt (`str` or `List[str]`, *optional*):
                The prompt or prompts not to guide the image generation. If not defined, one has to pass
                `negative_prompt_embeds` instead. Ignored when not using guidance (i.e., ignored if `guidance_scale` is
                less than `1`).
            prompt_embeds (`torch.FloatTensor`, *optional*):
                Pre-generated text embeddings. Can be used to easily tweak text inputs, *e.g.* prompt weighting. If not
                provided, text embeddings will be generated from `prompt` input argument.
            negative_prompt_embeds (`torch.FloatTensor`, *optional*):
                Pre-generated negative text embeddings. Can be used to easily tweak text inputs, *e.g.* prompt
                weighting. If not provided, negative_prompt_embeds will be generated from `negative_prompt` input
                argument.
        """
        if prompt is not None and isinstance(prompt, str):
            batch_size = 1
        elif prompt is not None and isinstance(prompt, list):
            batch_size = len(prompt)
        else:
            batch_size = prompt_embeds.shape[0]
        if prompt_embeds is None:
            text_inputs = self.tokenizer(prompt, padding='max_length', max_length=self.tokenizer.model_max_length, truncation=True, return_tensors='pt')
            text_input_ids = text_inputs.input_ids
            untruncated_ids = self.tokenizer(prompt, padding='longest', return_tensors='pt').input_ids
            if untruncated_ids.shape[-1] >= text_input_ids.shape[-1] and (not torch.equal(text_input_ids, untruncated_ids)):
                removed_text = self.tokenizer.batch_decode(untruncated_ids[:, self.tokenizer.model_max_length - 1:-1])
            if hasattr(self.text_encoder.config, 'use_attention_mask') and self.text_encoder.config.use_attention_mask:
                attention_mask = text_inputs.attention_mask.to(device)
            else:
                attention_mask = None
            prompt_embeds = self.text_encoder(text_input_ids.to(device), attention_mask=attention_mask)
            prompt_embeds = prompt_embeds[0]
        prompt_embeds = prompt_embeds.to(dtype=self.text_encoder.dtype, device=device)
        bs_embed, seq_len, _ = prompt_embeds.shape
        prompt_embeds = prompt_embeds.repeat(1, num_images_per_prompt, 1)
        prompt_embeds = prompt_embeds.view(bs_embed * num_images_per_prompt, seq_len, -1)
        if do_classifier_free_guidance and negative_prompt_embeds is None:
            uncond_tokens: List[str]
            if negative_prompt is None:
                uncond_tokens = [''] * batch_size
            elif type(prompt) is not type(negative_prompt):
                raise TypeError(f'`negative_prompt` should be the same type to `prompt`, but got {type(negative_prompt)} != {type(prompt)}.')
            elif isinstance(negative_prompt, str):
                uncond_tokens = [negative_prompt]
            elif batch_size != len(negative_prompt):
                raise ValueError(f'`negative_prompt`: {negative_prompt} has batch size {len(negative_prompt)}, but `prompt`: {prompt} has batch size {batch_size}. Please make sure that passed `negative_prompt` matches the batch size of `prompt`.')
            else:
                uncond_tokens = negative_prompt
            max_length = prompt_embeds.shape[1]
            uncond_input = self.tokenizer(uncond_tokens, padding='max_length', max_length=max_length, truncation=True, return_tensors='pt')
            if hasattr(self.text_encoder.config, 'use_attention_mask') and self.text_encoder.config.use_attention_mask:
                attention_mask = uncond_input.attention_mask.to(device)
            else:
                attention_mask = None
            negative_prompt_embeds = self.text_encoder(uncond_input.input_ids.to(device), attention_mask=attention_mask)
            negative_prompt_embeds = negative_prompt_embeds[0]
        if do_classifier_free_guidance:
            seq_len = negative_prompt_embeds.shape[1]
            negative_prompt_embeds = negative_prompt_embeds.to(dtype=self.text_encoder.dtype, device=device)
            negative_prompt_embeds = negative_prompt_embeds.repeat(1, num_images_per_prompt, 1)
            negative_prompt_embeds = negative_prompt_embeds.view(batch_size * num_images_per_prompt, seq_len, -1)
            prompt_embeds = torch.cat([negative_prompt_embeds, prompt_embeds])
        return prompt_embeds

    def prepare_extra_step_kwargs(self, generator, eta):
        accepts_eta = 'eta' in set(inspect.signature(self.scheduler.step).parameters.keys())
        extra_step_kwargs = {}
        if accepts_eta:
            extra_step_kwargs['eta'] = eta
        accepts_generator = 'generator' in set(inspect.signature(self.scheduler.step).parameters.keys())
        if accepts_generator:
            extra_step_kwargs['generator'] = generator
        return extra_step_kwargs

    def decode_latents(self, latents, intermediate_features=None):
        latents = 1 / self.vae.config.scaling_factor * latents
        if intermediate_features:
            image = self.vae.decode(latents, intermediate_features=intermediate_features, int_layers=self.emasc_int_layers).sample
        else:
            image = self.vae.decode(latents).sample
        image = (image / 2 + 0.5).clamp(0, 1)
        image = image.cpu().permute(0, 2, 3, 1).float().numpy()
        return image

    def check_inputs(self, prompt, height, width, callback_steps, negative_prompt=None, prompt_embeds=None, negative_prompt_embeds=None):
        if height % 8 != 0 or width % 8 != 0:
            raise ValueError(f'`height` and `width` have to be divisible by 8 but are {height} and {width}.')
        if callback_steps is None or (callback_steps is not None and (not isinstance(callback_steps, int) or callback_steps <= 0)):
            raise ValueError(f'`callback_steps` has to be a positive integer but is {callback_steps} of type {type(callback_steps)}.')
        if prompt is not None and prompt_embeds is not None:
            raise ValueError(f'Cannot forward both `prompt`: {prompt} and `prompt_embeds`: {prompt_embeds}. Please make sure to only forward one of the two.')
        elif prompt is None and prompt_embeds is None:
            raise ValueError('Provide either `prompt` or `prompt_embeds`. Cannot leave both `prompt` and `prompt_embeds` undefined.')
        elif prompt is not None and (not isinstance(prompt, str) and (not isinstance(prompt, list))):
            raise ValueError(f'`prompt` has to be of type `str` or `list` but is {type(prompt)}')
        if negative_prompt is not None and negative_prompt_embeds is not None:
            raise ValueError(f'Cannot forward both `negative_prompt`: {negative_prompt} and `negative_prompt_embeds`: {negative_prompt_embeds}. Please make sure to only forward one of the two.')
        if prompt_embeds is not None and negative_prompt_embeds is not None:
            if prompt_embeds.shape != negative_prompt_embeds.shape:
                raise ValueError(f'`prompt_embeds` and `negative_prompt_embeds` must have the same shape when passed directly, but got: `prompt_embeds` {prompt_embeds.shape} != `negative_prompt_embeds` {negative_prompt_embeds.shape}.')

    def prepare_latents(self, batch_size, num_channels_latents, height, width, dtype, device, generator, latents=None):
        shape = (batch_size, num_channels_latents, height // self.vae_scale_factor, width // self.vae_scale_factor)
        if isinstance(generator, list) and len(generator) != batch_size:
            raise ValueError(f'You have passed a list of generators of length {len(generator)}, but requested an effective batch size of {batch_size}. Make sure the batch size matches the length of the generators.')
        if latents is None:
            latents = randn_tensor(shape, generator=generator, device=device, dtype=dtype)
        else:
            latents = latents.to(device)
        latents = latents * self.scheduler.init_noise_sigma
        return latents

    def prepare_mask_latents(self, mask, masked_image, batch_size, height, width, dtype, device, generator, do_classifier_free_guidance, return_intermediate=False):
        mask = torch.nn.functional.interpolate(mask, size=(height // self.vae_scale_factor, width // self.vae_scale_factor))
        mask = mask.to(device=device, dtype=dtype)
        masked_image = masked_image.to(device=device, dtype=dtype)
        if isinstance(generator, list):
            masked_image_latents = [self.vae.encode(masked_image[i:i + 1])[0].latent_dist.sample(generator=generator[i]) for i in range(batch_size)]
            if return_intermediate:
                masked_image_intermediate_features = [self.vae.encode(masked_image[i:i + 1])[1] for i in range(batch_size)]
                masked_image_intermediate_features = [masked_image_intermediate_features[i] for i in self.emasc_int_layers]
            masked_image_latents = torch.cat(masked_image_latents, dim=0)
        else:
            masked_image_latents, masked_image_intermediate_features = self.vae.encode(masked_image)
            masked_image_latents = masked_image_latents.latent_dist.sample(generator=generator)
            if return_intermediate:
                masked_image_intermediate_features = [masked_image_intermediate_features[i] for i in self.emasc_int_layers]
        masked_image_latents = self.vae.config.scaling_factor * masked_image_latents
        if mask.shape[0] < batch_size:
            if not batch_size % mask.shape[0] == 0:
                raise ValueError(f"The passed mask and the required batch size don't match. Masks are supposed to be duplicated to a total batch size of {batch_size}, but {mask.shape[0]} masks were passed. Make sure the number of masks that you pass is divisible by the total requested batch size.")
            mask = mask.repeat(batch_size // mask.shape[0], 1, 1, 1)
        if masked_image_latents.shape[0] < batch_size:
            if not batch_size % masked_image_latents.shape[0] == 0:
                raise ValueError(f"The passed images and the required batch size don't match. Images are supposed to be duplicated to a total batch size of {batch_size}, but {masked_image_latents.shape[0]} images were passed. Make sure the number of images that you pass is divisible by the total requested batch size.")
            masked_image_latents = masked_image_latents.repeat(batch_size // masked_image_latents.shape[0], 1, 1, 1)
        mask = torch.cat([mask] * 2) if do_classifier_free_guidance else mask
        masked_image_latents = torch.cat([masked_image_latents] * 2) if do_classifier_free_guidance else masked_image_latents
        masked_image_latents = masked_image_latents.to(device=device, dtype=dtype)
        if return_intermediate:
            return (mask, masked_image_latents, masked_image_intermediate_features)
        else:
            return (mask, masked_image_latents)

    @torch.no_grad()
    def __call__(self, image: Union[torch.FloatTensor, PIL.Image.Image], mask_image: Union[torch.FloatTensor, PIL.Image.Image], pose_map: torch.FloatTensor, warped_cloth: torch.FloatTensor, prompt: Union[str, List[str]]=None, height: Optional[int]=None, width: Optional[int]=None, num_inference_steps: int=50, guidance_scale: float=7.5, negative_prompt: Optional[Union[str, List[str]]]=None, num_images_per_prompt: Optional[int]=1, eta: float=0.0, prompt_embeds: Optional[torch.FloatTensor]=None, negative_prompt_embeds: Optional[torch.FloatTensor]=None, generator: Optional[Union[torch.Generator, List[torch.Generator]]]=None, latents: Optional[torch.FloatTensor]=None, output_type: Optional[str]='pil', return_dict: bool=True, callback: Optional[Callable[[int, int, torch.FloatTensor], None]]=None, callback_steps: Optional[int]=1, cloth_cond_rate: float=1.0, no_pose: bool=False, cloth_input_type: str='warped'):
        """
        Function invoked when calling the pipeline for generation.

        Args:
            prompt (`str` or `List[str]`):
                The prompt or prompts to guide the image generation.
            image (`PIL.Image.Image`):
                `Image`, or tensor representing an image batch which will be inpainted, *i.e.* parts of the image will
                be masked out with `mask_image` and repainted according to `prompt`.
            mask_image (`PIL.Image.Image`):
                `Image`, or tensor representing an image batch, to mask `image`. White pixels in the mask will be
                repainted, while black pixels will be preserved. If `mask_image` is a PIL image, it will be converted
                to a single channel (luminance) before use. If it's a tensor, it should contain one color channel (L)
                instead of 3, so the expected shape would be `(B, H, W, 1)`.
            height (`int`, *optional*, defaults to self.unet.config.sample_size * self.vae_scale_factor):
                The height in pixels of the generated image.
            width (`int`, *optional*, defaults to self.unet.config.sample_size * self.vae_scale_factor):
                The width in pixels of the generated image.
            num_inference_steps (`int`, *optional*, defaults to 50):
                The number of denoising steps. More denoising steps usually lead to a higher quality image at the
                expense of slower inference.
            guidance_scale (`float`, *optional*, defaults to 7.5):
                Guidance scale as defined in [Classifier-Free Diffusion Guidance](https://arxiv.org/abs/2207.12598).
                `guidance_scale` is defined as `w` of equation 2. of [Imagen
                Paper](https://arxiv.org/pdf/2205.11487.pdf). Guidance scale is enabled by setting `guidance_scale >
                1`. Higher guidance scale encourages to generate images that are closely linked to the text `prompt`,
                usually at the expense of lower image quality.
            negative_prompt (`str` or `List[str]`, *optional*):
                The prompt or prompts not to guide the image generation. Ignored when not using guidance (i.e., ignored
                if `guidance_scale` is less than `1`).
            num_images_per_prompt (`int`, *optional*, defaults to 1):
                The number of images to generate per prompt.
            eta (`float`, *optional*, defaults to 0.0):
                Corresponds to parameter eta (η) in the DDIM paper: https://arxiv.org/abs/2010.02502. Only applies to
                [`schedulers.DDIMScheduler`], will be ignored for others.
            generator (`torch.Generator`, *optional*):
                One or a list of [torch generator(s)](https://pytorch.org/docs/stable/generated/torch.Generator.html)
                to make generation deterministic.
            latents (`torch.FloatTensor`, *optional*):
                Pre-generated noisy latents, sampled from a Gaussian distribution, to be used as inputs for image
                generation. Can be used to tweak the same generation with different prompts. If not provided, a latents
                tensor will ge generated by sampling using the supplied random `generator`.
            output_type (`str`, *optional*, defaults to `"pil"`):
                The output format of the generate image. Choose between
                [PIL](https://pillow.readthedocs.io/en/stable/): `PIL.Image.Image` or `np.array`.
            return_dict (`bool`, *optional*, defaults to `True`):
                Whether or not to return a [`~pipelines.stable_diffusion.StableDiffusionPipelineOutput`] instead of a
                plain tuple.
            callback (`Callable`, *optional*):
                A function that will be called every `callback_steps` steps during inference. The function will be
                called with the following arguments: `callback(step: int, timestep: int, latents: torch.FloatTensor)`.
            callback_steps (`int`, *optional*, defaults to 1):
                The frequency at which the `callback` function will be called. If not specified, the callback will be
                called at every step.

        Returns:
            [`~pipelines.stable_diffusion.StableDiffusionPipelineOutput`] or `tuple`:
            [`~pipelines.stable_diffusion.StableDiffusionPipelineOutput`] if `return_dict` is True, otherwise a `tuple.
            When returning a tuple, the first element is a list with the generated images, and the second element is a
            list of `bool`s denoting whether the corresponding generated image likely represents "not-safe-for-work"
            (nsfw) content, according to the `safety_checker`.
        """
        height = height or self.unet.config.sample_size * self.vae_scale_factor
        width = width or self.unet.config.sample_size * self.vae_scale_factor
        self.check_inputs(prompt, height, width, callback_steps, negative_prompt, prompt_embeds, negative_prompt_embeds)
        if image is None:
            raise ValueError('`image` input cannot be undefined.')
        if mask_image is None:
            raise ValueError('`mask_image` input cannot be undefined.')
        if prompt is not None and isinstance(prompt, str):
            batch_size = 1
        elif prompt is not None and isinstance(prompt, list):
            batch_size = len(prompt)
        else:
            batch_size = prompt_embeds.shape[0]
        device = self._execution_device
        do_classifier_free_guidance = guidance_scale > 1.0
        prompt_embeds = self._encode_prompt(prompt, device, num_images_per_prompt, do_classifier_free_guidance, negative_prompt, prompt_embeds=prompt_embeds, negative_prompt_embeds=negative_prompt_embeds)
        mask, masked_image = prepare_mask_and_masked_image(image, mask_image)
        pose_map = torch.nn.functional.interpolate(pose_map, size=(pose_map.shape[2] // 8, pose_map.shape[3] // 8), mode='bilinear')
        if no_pose:
            pose_map = torch.zeros_like(pose_map)
        if cloth_input_type == 'warped':
            cloth_latents = self.vae.encode(warped_cloth)[0].latent_dist.sample(generator=generator)
        elif cloth_input_type == 'none':
            cloth_latents = None
        else:
            raise ValueError(f'Invalid cloth_input_type {cloth_input_type}')
        if cloth_latents is not None:
            cloth_latents = self.vae.config.scaling_factor * cloth_latents
        self.scheduler.set_timesteps(num_inference_steps, device=device)
        timesteps = self.scheduler.timesteps
        cloth_conditioning_steps = (1 - cloth_cond_rate) * num_inference_steps
        num_channels_latents = self.vae.config.latent_channels
        latents = self.prepare_latents(batch_size * num_images_per_prompt, num_channels_latents, height, width, prompt_embeds.dtype, device, generator, latents)
        if self.emasc:
            mask, masked_image_latents, intermediate_features = self.prepare_mask_latents(mask, masked_image, batch_size * num_images_per_prompt, height, width, prompt_embeds.dtype, device, generator, do_classifier_free_guidance, return_intermediate=True)
            intermediate_features = self.emasc(intermediate_features)
            intermediate_features = mask_features(intermediate_features, mask_image)
        else:
            mask, masked_image_latents = self.prepare_mask_latents(mask, masked_image, batch_size * num_images_per_prompt, height, width, prompt_embeds.dtype, device, generator, do_classifier_free_guidance, return_intermediate=False)
        pose_map = torch.cat([torch.zeros_like(pose_map), pose_map]) if do_classifier_free_guidance else pose_map
        if cloth_latents is not None:
            cloth_latents = torch.cat([torch.zeros_like(cloth_latents), cloth_latents]) if do_classifier_free_guidance else cloth_latents
        extra_step_kwargs = self.prepare_extra_step_kwargs(generator, eta)
        num_warmup_steps = len(timesteps) - num_inference_steps * self.scheduler.order
        with self.progress_bar(total=num_inference_steps) as progress_bar:
            for i, t in enumerate(timesteps):
                latent_model_input = torch.cat([latents] * 2) if do_classifier_free_guidance else latents
                if i >= num_inference_steps - cloth_conditioning_steps:
                    cloth_latents = torch.zeros_like(cloth_latents)
                latent_model_input = self.scheduler.scale_model_input(latent_model_input, t)
                if cloth_latents is not None:
                    latent_model_input = torch.cat([latent_model_input, mask, masked_image_latents, pose_map.to(mask.dtype), cloth_latents.to(mask.dtype)], dim=1)
                else:
                    latent_model_input = torch.cat([latent_model_input, mask, masked_image_latents, pose_map.to(mask.dtype)], dim=1)
                noise_pred = self.unet(latent_model_input, t, encoder_hidden_states=prompt_embeds).sample
                if do_classifier_free_guidance:
                    noise_pred_uncond, noise_pred_text = noise_pred.chunk(2)
                    noise_pred = noise_pred_uncond + guidance_scale * (noise_pred_text - noise_pred_uncond)
                latents = self.scheduler.step(noise_pred, t, latents, **extra_step_kwargs).prev_sample.to(self.vae.dtype)
                if i == len(timesteps) - 1 or (i + 1 > num_warmup_steps and (i + 1) % self.scheduler.order == 0):
                    progress_bar.update()
                    if callback is not None and i % callback_steps == 0:
                        callback(i, t, latents)
        if self.emasc:
            image = self.decode_latents(latents, intermediate_features)
        else:
            image = self.decode_latents(latents)
        if output_type == 'pil':
            image = self.numpy_to_pil(image)
        if not return_dict:
            return (image, None)
        return StableDiffusionPipelineOutput(images=image, nsfw_content_detected=None)

def decode_latents(self, latents, intermediate_features=None):
    latents = 1 / self.vae.config.scaling_factor * latents
    if intermediate_features:
        image = self.vae.decode(latents, intermediate_features=intermediate_features, int_layers=self.emasc_int_layers).sample
    else:
        image = self.vae.decode(latents).sample
    image = (image / 2 + 0.5).clamp(0, 1)
    image = image.cpu().permute(0, 2, 3, 1).float().numpy()
    return image

class TPSGridGen(nn.Module):

    def __init__(self, target_height, target_width, target_control_points):
        super(TPSGridGen, self).__init__()
        assert target_control_points.ndimension() == 2
        assert target_control_points.size(1) == 2
        N = target_control_points.size(0)
        self.num_points = N
        target_control_points = target_control_points.float()
        forward_kernel = torch.zeros(N + 3, N + 3)
        target_control_partial_repr = compute_partial_repr(target_control_points, target_control_points)
        forward_kernel[:N, :N].copy_(target_control_partial_repr)
        forward_kernel[:N, -3].fill_(1)
        forward_kernel[-3, :N].fill_(1)
        forward_kernel[:N, -2:].copy_(target_control_points)
        forward_kernel[-2:, :N].copy_(target_control_points.transpose(0, 1))
        inverse_kernel = torch.inverse(forward_kernel)
        HW = target_height * target_width
        target_coordinate = list(itertools.product(range(target_height), range(target_width)))
        target_coordinate = torch.Tensor(target_coordinate)
        Y, X = target_coordinate.split(1, dim=1)
        Y = Y * 2 / (target_height - 1) - 1
        X = X * 2 / (target_width - 1) - 1
        target_coordinate = torch.cat([X, Y], dim=1)
        target_coordinate_partial_repr = compute_partial_repr(target_coordinate, target_control_points)
        target_coordinate_repr = torch.cat([target_coordinate_partial_repr, torch.ones(HW, 1), target_coordinate], dim=1)
        self.register_buffer('inverse_kernel', inverse_kernel)
        self.register_buffer('padding_matrix', torch.zeros(3, 2))
        self.register_buffer('target_coordinate_repr', target_coordinate_repr)

    def forward(self, source_control_points):
        assert source_control_points.ndimension() == 3
        assert source_control_points.size(1) == self.num_points
        assert source_control_points.size(2) == 2
        batch_size = source_control_points.size(0)
        Y = torch.cat([source_control_points, Variable(self.padding_matrix.expand(batch_size, 3, 2))], 1)
        mapping_matrix = torch.matmul(Variable(self.inverse_kernel), Y)
        source_coordinate = torch.matmul(Variable(self.target_coordinate_repr), mapping_matrix)
        return source_coordinate

def __init__(self, target_height, target_width, target_control_points):
    super(TPSGridGen, self).__init__()
    assert target_control_points.ndimension() == 2
    assert target_control_points.size(1) == 2
    N = target_control_points.size(0)
    self.num_points = N
    target_control_points = target_control_points.float()
    forward_kernel = torch.zeros(N + 3, N + 3)
    target_control_partial_repr = compute_partial_repr(target_control_points, target_control_points)
    forward_kernel[:N, :N].copy_(target_control_partial_repr)
    forward_kernel[:N, -3].fill_(1)
    forward_kernel[-3, :N].fill_(1)
    forward_kernel[:N, -2:].copy_(target_control_points)
    forward_kernel[-2:, :N].copy_(target_control_points.transpose(0, 1))
    inverse_kernel = torch.inverse(forward_kernel)
    HW = target_height * target_width
    target_coordinate = list(itertools.product(range(target_height), range(target_width)))
    target_coordinate = torch.Tensor(target_coordinate)
    Y, X = target_coordinate.split(1, dim=1)
    Y = Y * 2 / (target_height - 1) - 1
    X = X * 2 / (target_width - 1) - 1
    target_coordinate = torch.cat([X, Y], dim=1)
    target_coordinate_partial_repr = compute_partial_repr(target_coordinate, target_control_points)
    target_coordinate_repr = torch.cat([target_coordinate_partial_repr, torch.ones(HW, 1), target_coordinate], dim=1)
    self.register_buffer('inverse_kernel', inverse_kernel)
    self.register_buffer('padding_matrix', torch.zeros(3, 2))
    self.register_buffer('target_coordinate_repr', target_coordinate_repr)

class BoundedGridLocNet(nn.Module):

    def __init__(self, grid_height, grid_width, target_control_points, n_layers):
        super(BoundedGridLocNet, self).__init__()
        self.regression = FeatureRegression(output_dim=grid_height * grid_width * 2)
        bias = torch.from_numpy(np.arctanh(target_control_points.numpy()))
        bias = bias.view(-1)
        self.regression.linear.bias.data.copy_(bias)
        self.regression.linear.weight.data.zero_()

    def forward(self, x):
        batch_size = x.size(0)
        points = self.regression(x)
        coor = points.view(batch_size, -1, 2)
        row = self.get_row(coor, 5)
        col = self.get_col(coor, 5)
        rg_loss = sum(self.grad_row(coor, 5))
        cg_loss = sum(self.grad_col(coor, 5))
        rg_loss = torch.max(rg_loss, torch.tensor(0.02).cuda())
        cg_loss = torch.max(cg_loss, torch.tensor(0.02).cuda())
        rx, ry, cx, cy = (torch.tensor(0.08).cuda(), torch.tensor(0.08).cuda(), torch.tensor(0.08).cuda(), torch.tensor(0.08).cuda())
        row_x, row_y = (row[:, :, 0], row[:, :, 1])
        col_x, col_y = (col[:, :, 0], col[:, :, 1])
        rx_loss = torch.max(rx, row_x).mean()
        ry_loss = torch.max(ry, row_y).mean()
        cx_loss = torch.max(cx, col_x).mean()
        cy_loss = torch.max(cy, col_y).mean()
        return (coor, rx_loss, ry_loss, cx_loss, cy_loss, rg_loss, cg_loss)

    def get_row(self, coor, num):
        sec_dic = []
        for j in range(num):
            sum = 0
            buffer = 0
            flag = False
            max = -1
            for i in range(num - 1):
                differ = (coor[:, j * num + i + 1, :] - coor[:, j * num + i, :]) ** 2
                if not flag:
                    second_dif = 0
                    flag = True
                else:
                    second_dif = torch.abs(differ - buffer)
                    sec_dic.append(second_dif)
                buffer = differ
                sum += second_dif
        return torch.stack(sec_dic, dim=1)

    def get_col(self, coor, num):
        sec_dic = []
        for i in range(num):
            sum = 0
            buffer = 0
            flag = False
            max = -1
            for j in range(num - 1):
                differ = (coor[:, (j + 1) * num + i, :] - coor[:, j * num + i, :]) ** 2
                if not flag:
                    second_dif = 0
                    flag = True
                else:
                    second_dif = torch.abs(differ - buffer)
                    sec_dic.append(second_dif)
                buffer = differ
                sum += second_dif
        return torch.stack(sec_dic, dim=1)

    def grad_row(self, coor, num):
        sec_term = []
        for j in range(num):
            for i in range(1, num - 1):
                x0, y0 = coor[:, j * num + i - 1, :][0]
                x1, y1 = coor[:, j * num + i + 0, :][0]
                x2, y2 = coor[:, j * num + i + 1, :][0]
                grad = torch.abs((y1 - y0) * (x1 - x2) - (y1 - y2) * (x1 - x0))
                sec_term.append(grad)
        return sec_term

    def grad_col(self, coor, num):
        sec_term = []
        for i in range(num):
            for j in range(1, num - 1):
                x0, y0 = coor[:, (j - 1) * num + i, :][0]
                x1, y1 = coor[:, j * num + i, :][0]
                x2, y2 = coor[:, (j + 1) * num + i, :][0]
                grad = torch.abs((y1 - y0) * (x1 - x2) - (y1 - y2) * (x1 - x0))
                sec_term.append(grad)
        return sec_term

def __init__(self, grid_height, grid_width, target_control_points, n_layers):
    super(BoundedGridLocNet, self).__init__()
    self.regression = FeatureRegression(output_dim=grid_height * grid_width * 2)
    bias = torch.from_numpy(np.arctanh(target_control_points.numpy()))
    bias = bias.view(-1)
    self.regression.linear.bias.data.copy_(bias)
    self.regression.linear.weight.data.zero_()

