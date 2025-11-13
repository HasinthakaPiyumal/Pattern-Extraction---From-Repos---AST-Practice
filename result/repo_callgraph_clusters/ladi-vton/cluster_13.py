# Cluster 13

class VGGLoss(nn.Module):
    """
    VGG loss module.
    """

    def __init__(self, gpu=None):
        super(VGGLoss, self).__init__()
        self.vgg = VGG19().eval()
        if gpu:
            self.vgg = self.vgg.cuda(gpu)
        self.criterion = nn.L1Loss()
        self.weights = [1.0 / 32, 1.0 / 16, 1.0 / 8, 1.0 / 4, 1.0]
        self.register_buffer('mean', torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1))
        self.register_buffer('std', torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1))
        self.resize = Resize(256, antialias=True)

    def forward(self, x, y):
        x = self.resize(x)
        y = self.resize(y)
        x = (x + 1) / 2
        y = (y + 1) / 2
        x = (x - self.mean) / self.std
        y = (y - self.mean) / self.std
        x_vgg, y_vgg = (self.vgg(x), self.vgg(y))
        loss = 0
        for i in range(len(x_vgg)):
            loss += self.weights[i] * self.criterion(x_vgg[i], y_vgg[i].detach())
        return loss

def forward(self, x, y):
    x = self.resize(x)
    y = self.resize(y)
    x = (x + 1) / 2
    y = (y + 1) / 2
    x = (x - self.mean) / self.std
    y = (y - self.mean) / self.std
    x_vgg, y_vgg = (self.vgg(x), self.vgg(y))
    loss = 0
    for i in range(len(x_vgg)):
        loss += self.weights[i] * self.criterion(x_vgg[i], y_vgg[i].detach())
    return loss

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

def __len__(self):
    return len(self.paths)

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

def __len__(self):
    return len(self.paths)

def encode_text_word_embedding(text_encoder: CLIPTextModel, input_ids: torch.tensor, word_embeddings: torch.tensor, num_vstar: int=1) -> BaseModelOutputWithPooling:
    """
    Encode text by replacing the '$' with the PTEs extracted with the inversion adapter.
    Heavily based on hugginface implementation of CLIP.
    """
    existing_indexes = (input_ids == 259).nonzero(as_tuple=True)[0]
    existing_indexes = existing_indexes.unique()
    if len(existing_indexes) > 0:
        _, counts = torch.unique((input_ids == 259).nonzero(as_tuple=True)[0], return_counts=True)
        cum_sum = torch.cat((torch.zeros(1, device=input_ids.device).int(), torch.cumsum(counts, dim=0)[:-1]))
        first_vstar_indexes = (input_ids == 259).nonzero()[cum_sum][:, 1]
        rep_idx = torch.cat([(first_vstar_indexes + n).unsqueeze(0) for n in range(num_vstar)])
        word_embeddings = word_embeddings.to(input_ids.device)
    input_shape = input_ids.size()
    input_ids = input_ids.view(-1, input_shape[-1])
    seq_length = input_ids.shape[-1]
    position_ids = text_encoder.text_model.embeddings.position_ids[:, :seq_length]
    input_embeds = text_encoder.text_model.embeddings.token_embedding(input_ids)
    if len(existing_indexes) > 0:
        assert word_embeddings.shape[0] == input_embeds.shape[0]
        if len(word_embeddings.shape) == 2:
            word_embeddings = word_embeddings.unsqueeze(1)
        input_embeds[torch.arange(input_embeds.shape[0]).repeat_interleave(num_vstar).reshape(input_embeds.shape[0], num_vstar)[existing_indexes.cpu()], rep_idx.T] = word_embeddings.to(input_embeds.dtype)[existing_indexes]
    position_embeddings = text_encoder.text_model.embeddings.position_embedding(position_ids)
    hidden_states = input_embeds + position_embeddings
    bsz, seq_len = input_shape
    causal_attention_mask = text_encoder.text_model._build_causal_attention_mask(bsz, seq_len, hidden_states.dtype).to(hidden_states.device)
    encoder_outputs = text_encoder.text_model.encoder(inputs_embeds=hidden_states, attention_mask=None, causal_attention_mask=causal_attention_mask, output_attentions=None, output_hidden_states=None, return_dict=None)
    last_hidden_state = encoder_outputs[0]
    last_hidden_state = text_encoder.text_model.final_layer_norm(last_hidden_state)
    pooled_output = last_hidden_state[torch.arange(last_hidden_state.shape[0], device=last_hidden_state.device), input_ids.to(dtype=torch.int, device=last_hidden_state.device).argmax(dim=-1)]
    return BaseModelOutputWithPooling(last_hidden_state=last_hidden_state, pooler_output=pooled_output, hidden_states=encoder_outputs.hidden_states, attentions=encoder_outputs.attentions)

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

def __len__(self):
    return len(self.c_names)

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

def __len__(self):
    return len(self.c_names)

class Up(nn.Module):
    """Upscaling then double conv"""

    def __init__(self, in_channels, out_channels, bilinear=True):
        super().__init__()
        if bilinear:
            self.up = nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True)
            self.conv = DoubleConv(in_channels, out_channels, in_channels // 2)
        else:
            self.up = nn.ConvTranspose2d(in_channels, in_channels // 2, kernel_size=2, stride=2)
            self.conv = DoubleConv(in_channels, out_channels)

    def forward(self, x1, x2):
        x1 = self.up(x1)
        diffY = x2.size()[2] - x1.size()[2]
        diffX = x2.size()[3] - x1.size()[3]
        x1 = F.pad(x1, [diffX // 2, diffX - diffX // 2, diffY // 2, diffY - diffY // 2])
        x = torch.cat([x2, x1], dim=1)
        return self.conv(x)

def forward(self, x1, x2):
    x1 = self.up(x1)
    diffY = x2.size()[2] - x1.size()[2]
    diffX = x2.size()[3] - x1.size()[3]
    x1 = F.pad(x1, [diffX // 2, diffX - diffX // 2, diffY // 2, diffY - diffY // 2])
    x = torch.cat([x2, x1], dim=1)
    return self.conv(x)

class OutConv(nn.Module):

    def __init__(self, in_channels, out_channels):
        super(OutConv, self).__init__()
        self.conv = nn.Conv2d(in_channels, out_channels, kernel_size=1)

    def forward(self, x):
        return self.conv(x)

def forward(self, x):
    return self.conv(x)

class VectorQuantizer(nn.Module):
    """
    Improved version over VectorQuantizer, can be used as a drop-in replacement. Mostly avoids costly matrix
    multiplications and allows for post-hoc remapping of indices.
    """

    def __init__(self, n_e, vq_embed_dim, beta, remap=None, unknown_index='random', sane_index_shape=False, legacy=True):
        super().__init__()
        self.n_e = n_e
        self.vq_embed_dim = vq_embed_dim
        self.beta = beta
        self.legacy = legacy
        self.embedding = nn.Embedding(self.n_e, self.vq_embed_dim)
        self.embedding.weight.data.uniform_(-1.0 / self.n_e, 1.0 / self.n_e)
        self.remap = remap
        if self.remap is not None:
            self.register_buffer('used', torch.tensor(np.load(self.remap)))
            self.re_embed = self.used.shape[0]
            self.unknown_index = unknown_index
            if self.unknown_index == 'extra':
                self.unknown_index = self.re_embed
                self.re_embed = self.re_embed + 1
            print(f'Remapping {self.n_e} indices to {self.re_embed} indices. Using {self.unknown_index} for unknown indices.')
        else:
            self.re_embed = n_e
        self.sane_index_shape = sane_index_shape

    def remap_to_used(self, inds):
        ishape = inds.shape
        assert len(ishape) > 1
        inds = inds.reshape(ishape[0], -1)
        used = self.used.to(inds)
        match = (inds[:, :, None] == used[None, None, ...]).long()
        new = match.argmax(-1)
        unknown = match.sum(2) < 1
        if self.unknown_index == 'random':
            new[unknown] = torch.randint(0, self.re_embed, size=new[unknown].shape).to(device=new.device)
        else:
            new[unknown] = self.unknown_index
        return new.reshape(ishape)

    def unmap_to_all(self, inds):
        ishape = inds.shape
        assert len(ishape) > 1
        inds = inds.reshape(ishape[0], -1)
        used = self.used.to(inds)
        if self.re_embed > self.used.shape[0]:
            inds[inds >= self.used.shape[0]] = 0
        back = torch.gather(used[None, :][inds.shape[0] * [0], :], 1, inds)
        return back.reshape(ishape)

    def forward(self, z):
        z = z.permute(0, 2, 3, 1).contiguous()
        z_flattened = z.view(-1, self.vq_embed_dim)
        min_encoding_indices = torch.argmin(torch.cdist(z_flattened, self.embedding.weight), dim=1)
        z_q = self.embedding(min_encoding_indices).view(z.shape)
        perplexity = None
        min_encodings = None
        if not self.legacy:
            loss = self.beta * torch.mean((z_q.detach() - z) ** 2) + torch.mean((z_q - z.detach()) ** 2)
        else:
            loss = torch.mean((z_q.detach() - z) ** 2) + self.beta * torch.mean((z_q - z.detach()) ** 2)
        z_q = z + (z_q - z).detach()
        z_q = z_q.permute(0, 3, 1, 2).contiguous()
        if self.remap is not None:
            min_encoding_indices = min_encoding_indices.reshape(z.shape[0], -1)
            min_encoding_indices = self.remap_to_used(min_encoding_indices)
            min_encoding_indices = min_encoding_indices.reshape(-1, 1)
        if self.sane_index_shape:
            min_encoding_indices = min_encoding_indices.reshape(z_q.shape[0], z_q.shape[2], z_q.shape[3])
        return (z_q, loss, (perplexity, min_encodings, min_encoding_indices))

    def get_codebook_entry(self, indices, shape):
        if self.remap is not None:
            indices = indices.reshape(shape[0], -1)
            indices = self.unmap_to_all(indices)
            indices = indices.reshape(-1)
        z_q = self.embedding(indices)
        if shape is not None:
            z_q = z_q.view(shape)
            z_q = z_q.permute(0, 3, 1, 2).contiguous()
        return z_q

def remap_to_used(self, inds):
    ishape = inds.shape
    assert len(ishape) > 1
    inds = inds.reshape(ishape[0], -1)
    used = self.used.to(inds)
    match = (inds[:, :, None] == used[None, None, ...]).long()
    new = match.argmax(-1)
    unknown = match.sum(2) < 1
    if self.unknown_index == 'random':
        new[unknown] = torch.randint(0, self.re_embed, size=new[unknown].shape).to(device=new.device)
    else:
        new[unknown] = self.unknown_index
    return new.reshape(ishape)

def unmap_to_all(self, inds):
    ishape = inds.shape
    assert len(ishape) > 1
    inds = inds.reshape(ishape[0], -1)
    used = self.used.to(inds)
    if self.re_embed > self.used.shape[0]:
        inds[inds >= self.used.shape[0]] = 0
    back = torch.gather(used[None, :][inds.shape[0] * [0], :], 1, inds)
    return back.reshape(ishape)

def forward(self, z):
    z = z.permute(0, 2, 3, 1).contiguous()
    z_flattened = z.view(-1, self.vq_embed_dim)
    min_encoding_indices = torch.argmin(torch.cdist(z_flattened, self.embedding.weight), dim=1)
    z_q = self.embedding(min_encoding_indices).view(z.shape)
    perplexity = None
    min_encodings = None
    if not self.legacy:
        loss = self.beta * torch.mean((z_q.detach() - z) ** 2) + torch.mean((z_q - z.detach()) ** 2)
    else:
        loss = torch.mean((z_q.detach() - z) ** 2) + self.beta * torch.mean((z_q - z.detach()) ** 2)
    z_q = z + (z_q - z).detach()
    z_q = z_q.permute(0, 3, 1, 2).contiguous()
    if self.remap is not None:
        min_encoding_indices = min_encoding_indices.reshape(z.shape[0], -1)
        min_encoding_indices = self.remap_to_used(min_encoding_indices)
        min_encoding_indices = min_encoding_indices.reshape(-1, 1)
    if self.sane_index_shape:
        min_encoding_indices = min_encoding_indices.reshape(z_q.shape[0], z_q.shape[2], z_q.shape[3])
    return (z_q, loss, (perplexity, min_encodings, min_encoding_indices))

def get_codebook_entry(self, indices, shape):
    if self.remap is not None:
        indices = indices.reshape(shape[0], -1)
        indices = self.unmap_to_all(indices)
        indices = indices.reshape(-1)
    z_q = self.embedding(indices)
    if shape is not None:
        z_q = z_q.view(shape)
        z_q = z_q.permute(0, 3, 1, 2).contiguous()
    return z_q

class FeatureCorrelation(nn.Module):

    def __init__(self):
        super(FeatureCorrelation, self).__init__()

    def forward(self, feature_A, feature_B):
        b, c, h, w = feature_A.size()
        feature_A = feature_A.transpose(2, 3).contiguous().view(b, c, h * w)
        feature_B = feature_B.view(b, c, h * w).transpose(1, 2)
        feature_mul = torch.bmm(feature_B, feature_A)
        correlation_tensor = feature_mul.view(b, h, w, h * w).transpose(2, 3).transpose(1, 2)
        return correlation_tensor

    def get_output_size(self, in_shape):
        out_shape = None
        with torch.no_grad():
            out_shape = self.forward(torch.randn(in_shape), torch.randn(in_shape))
        return out_shape.shape

def forward(self, feature_A, feature_B):
    b, c, h, w = feature_A.size()
    feature_A = feature_A.transpose(2, 3).contiguous().view(b, c, h * w)
    feature_B = feature_B.view(b, c, h * w).transpose(1, 2)
    feature_mul = torch.bmm(feature_B, feature_A)
    correlation_tensor = feature_mul.view(b, h, w, h * w).transpose(2, 3).transpose(1, 2)
    return correlation_tensor

class FeatureRegression(nn.Module):

    def __init__(self, input_nc=192, output_dim=6, use_cuda=True, in_shape=None):
        super(FeatureRegression, self).__init__()
        self.conv = nn.Sequential(nn.Conv2d(input_nc, 512, kernel_size=4, stride=2, padding=1), nn.BatchNorm2d(512), nn.ReLU(inplace=True), nn.Conv2d(512, 256, kernel_size=4, stride=2, padding=1), nn.BatchNorm2d(256), nn.ReLU(inplace=True), nn.Conv2d(256, 128, kernel_size=3, padding=1), nn.BatchNorm2d(128), nn.ReLU(inplace=True), nn.Conv2d(128, 64, kernel_size=3, padding=1), nn.BatchNorm2d(64), nn.ReLU(inplace=True))
        if in_shape is not None:
            with torch.no_grad():
                out = self.conv(torch.randn(in_shape))
            _, out_c, out_w, out_h = out.shape
        else:
            out_c, out_w, out_h = (64, 3, 4)
        self.linear = nn.Linear(out_c * out_h * out_w, output_dim)
        self.tanh = nn.Tanh()

    def forward(self, x):
        x = self.conv(x)
        x = x.reshape(x.size(0), -1)
        x = self.linear(x)
        x = self.tanh(x)
        return x

def forward(self, x):
    x = self.conv(x)
    x = x.reshape(x.size(0), -1)
    x = self.linear(x)
    x = self.tanh(x)
    return x

def compute_partial_repr(input_points, control_points):
    N = input_points.size(0)
    M = control_points.size(0)
    pairwise_diff = input_points.view(N, 1, 2) - control_points.view(1, M, 2)
    pairwise_diff_square = pairwise_diff * pairwise_diff
    pairwise_dist = pairwise_diff_square[:, :, 0] + pairwise_diff_square[:, :, 1]
    repr_matrix = 0.5 * pairwise_dist * torch.log(pairwise_dist)
    mask = repr_matrix != repr_matrix
    repr_matrix.masked_fill_(mask, 0)
    return repr_matrix

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

def forward(self, source_control_points):
    assert source_control_points.ndimension() == 3
    assert source_control_points.size(1) == self.num_points
    assert source_control_points.size(2) == 2
    batch_size = source_control_points.size(0)
    Y = torch.cat([source_control_points, Variable(self.padding_matrix.expand(batch_size, 3, 2))], 1)
    mapping_matrix = torch.matmul(Variable(self.inverse_kernel), Y)
    source_coordinate = torch.matmul(Variable(self.target_coordinate_repr), mapping_matrix)
    return source_coordinate

class ConvNet_TPS(nn.Module):
    """ Geometric Matching Module
    """

    def __init__(self, height, width, input_nc=6, n_layer=4):
        super(ConvNet_TPS, self).__init__()
        range = 0.9
        r1 = range
        r2 = range
        grid_size_h = 5
        grid_size_w = 5
        self.height = height
        self.width = width
        assert r1 < 1 and r2 < 1
        target_control_points = torch.Tensor(list(itertools.product(np.arange(-r1, r1 + 1e-05, 2.0 * r1 / (grid_size_h - 1)), np.arange(-r2, r2 + 1e-05, 2.0 * r2 / (grid_size_w - 1)))))
        Y, X = target_control_points.split(1, dim=1)
        target_control_points = torch.cat([X, Y], dim=1)
        self.extractionA = FeatureExtraction(3, ngf=64, n_layers=n_layer, norm_layer=nn.BatchNorm2d)
        self.extractionB = FeatureExtraction(input_nc, ngf=64, n_layers=n_layer, norm_layer=nn.BatchNorm2d)
        self.in_shape = self.extractionA.get_output_size((4, 3, height, width))
        self.l2norm = FeatureL2Norm()
        self.correlation = FeatureCorrelation()
        self.in_shape = self.correlation.get_output_size(self.in_shape)
        self.loc_net = BoundedGridLocNet(grid_size_h, grid_size_w, target_control_points, n_layers=5)
        self.gridGen = TPSGridGen(height, width, target_control_points)

    def forward(self, inputA, inputB):
        batch_size = inputA.size(0)
        featureA = self.extractionA(inputA)
        featureB = self.extractionB(inputB)
        featureA = self.l2norm(featureA)
        featureB = self.l2norm(featureB)
        correlation = self.correlation(featureA, featureB)
        source_control_points, rx, ry, cx, cy, rg, cg = self.loc_net(correlation)
        source_control_points = source_control_points
        source_coordinate = self.gridGen(source_control_points)
        grid = source_coordinate.view(batch_size, self.height, self.width, 2)
        return (grid, source_control_points, rx, ry, cx, cy, rg, cg)

def forward(self, inputA, inputB):
    batch_size = inputA.size(0)
    featureA = self.extractionA(inputA)
    featureB = self.extractionB(inputB)
    featureA = self.l2norm(featureA)
    featureB = self.l2norm(featureB)
    correlation = self.correlation(featureA, featureB)
    source_control_points, rx, ry, cx, cy, rg, cg = self.loc_net(correlation)
    source_control_points = source_control_points
    source_coordinate = self.gridGen(source_control_points)
    grid = source_coordinate.view(batch_size, self.height, self.width, 2)
    return (grid, source_control_points, rx, ry, cx, cy, rg, cg)

class EMASC(nn.Module):
    """
    EMASC: Enhanced Mask-Aware Skip Connections
    """

    def __init__(self, in_channels: List[int], out_channels: List[int], kernel_size: int=3, padding: int=1, stride: int=1, type: str='nonlinear'):
        super().__init__()
        if type == 'linear':
            self.conv = nn.ModuleList()
            for in_ch, out_ch in zip(in_channels, out_channels):
                self.conv.append(nn.Conv2d(in_ch, out_ch, kernel_size=3, bias=True, padding=padding, stride=stride))
            self.apply(self._init_weights)
        elif type == 'nonlinear':
            self.conv = nn.ModuleList()
            for in_ch, out_ch in zip(in_channels, out_channels):
                adapter = nn.Sequential(nn.Conv2d(in_ch, in_ch, kernel_size=kernel_size, bias=True, padding=padding, stride=stride), nn.SiLU(inplace=True), nn.Conv2d(in_ch, out_ch, kernel_size=kernel_size, bias=True, padding=padding, stride=stride))
                self.conv.append(adapter)
        else:
            raise NotImplementedError(f'EMASC type {type} is not implemented.')

    def forward(self, x: list):
        for i in range(len(x)):
            x[i] = self.conv[i](x[i])
        return x

    def _init_weights(self, w):
        if isinstance(w, nn.Conv2d):
            w.weight.data.fill_(0.0)
            w.bias.data.fill_(0.0)

def forward(self, x: list):
    for i in range(len(x)):
        x[i] = self.conv[i](x[i])
    return x

