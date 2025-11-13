# Cluster 21

class SkyMlp(nn.Module):

    def __init__(self, sky_model_args):
        super(SkyMlp, self).__init__()
        num_encoding_functions = sky_model_args.num_encoding_functions
        hidden_dim = sky_model_args.hidden_dim
        self.positional_encoding = PositionalEncoding(num_encoding_functions)
        self.fc1 = nn.Linear(3 + 3 * 2 * num_encoding_functions, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, 3)
        self.relu = nn.ReLU()

    def capture(self):
        return self.state_dict()

    def train_params(self):
        return self.parameters()

    def restore(self, model_args):
        self.load_state_dict(model_args)

    def _forward(self, view_dir):
        """
        Input:
            view_dir: torch.Tensor of shape [batch_size, num_samples, 3]
        Returns:
            rgb: torch.Tensor of shape [batch_size, num_samples, 3]
        """
        x = self.positional_encoding(view_dir)
        x = self.fc1(x)
        x = self.relu(x)
        x = self.fc2(x)
        x = self.relu(x)
        x = self.fc3(x)
        return x

    def forward(self, viewpoint_camera):
        c2w = torch.linalg.inv(viewpoint_camera.world_view_transform.transpose(0, 1))
        ray_d_world = get_ray_directions(viewpoint_camera.image_height, viewpoint_camera.image_width, viewpoint_camera.FoVx, viewpoint_camera.FoVy, c2w).cuda()
        ray_d_world_batch = ray_d_world.view(1, -1, 3)
        skymap = self._forward(ray_d_world_batch).view(viewpoint_camera.image_height, viewpoint_camera.image_width, 3).permute(2, 0, 1)
        return skymap

def forward(self, viewpoint_camera):
    c2w = torch.linalg.inv(viewpoint_camera.world_view_transform.transpose(0, 1))
    ray_d_world = get_ray_directions(viewpoint_camera.image_height, viewpoint_camera.image_width, viewpoint_camera.FoVx, viewpoint_camera.FoVy, c2w).cuda()
    ray_d_world_batch = ray_d_world.view(1, -1, 3)
    skymap = self._forward(ray_d_world_batch).view(viewpoint_camera.image_height, viewpoint_camera.image_width, 3).permute(2, 0, 1)
    return skymap

class SkyCube(torch.nn.Module):

    def __init__(self, sky_model_args):
        super().__init__()
        resolution = sky_model_args.resolution
        self.waymo_to_opengl = torch.tensor([[0, -1, 0], [0, 0, 1], [-1, 0, 0]], dtype=torch.float32, device='cuda')
        self.base = torch.nn.Parameter(0.5 * torch.ones(6, resolution, resolution, 3, requires_grad=True))

    def capture(self):
        return self.base

    def train_params(self):
        return [self.base]

    def restore(self, model_args):
        self.base = model_args

    def _forward(self, l):
        import nvdiffrast.torch as dr
        l = (l.reshape(-1, 3) @ self.waymo_to_opengl.T).reshape(*l.shape)
        l = l.contiguous()
        prefix = l.shape[:-1]
        if len(prefix) != 3:
            l = l.reshape(1, 1, -1, l.shape[-1])
        light = dr.texture(self.base[None, ...], l, filter_mode='linear', boundary_mode='cube')
        light = light.view(*prefix, -1)
        return light

    def forward(self, viewpoint_camera):
        c2w = torch.linalg.inv(viewpoint_camera.world_view_transform.transpose(0, 1))
        ray_d_world = get_ray_directions(viewpoint_camera.image_height, viewpoint_camera.image_width, viewpoint_camera.FoVx, viewpoint_camera.FoVy, c2w).cuda()
        skymap = self._forward(ray_d_world)
        skymap = skymap.permute(2, 0, 1)
        return skymap

def forward(self, viewpoint_camera):
    c2w = torch.linalg.inv(viewpoint_camera.world_view_transform.transpose(0, 1))
    ray_d_world = get_ray_directions(viewpoint_camera.image_height, viewpoint_camera.image_width, viewpoint_camera.FoVx, viewpoint_camera.FoVy, c2w).cuda()
    skymap = self._forward(ray_d_world)
    skymap = skymap.permute(2, 0, 1)
    return skymap

class FakeFakesGenerator:

    def __init__(self, aug_proba=0.5, img_aug_degree=30, img_aug_translate=0.2):
        self.grad_aug = RandomAffine(degrees=360, translate=0.2, padding_mode=SamplePadding.REFLECTION, keepdim=False, p=1)
        self.img_aug = RandomAffine(degrees=img_aug_degree, translate=img_aug_translate, padding_mode=SamplePadding.REFLECTION, keepdim=True, p=1)
        self.aug_proba = aug_proba

    def __call__(self, input_images, masks):
        blend_masks = self._fill_masks_with_gradient(masks)
        blend_target = self._make_blend_target(input_images)
        result = input_images * (1 - blend_masks) + blend_target * blend_masks
        return (result, blend_masks)

    def _make_blend_target(self, input_images):
        batch_size = input_images.shape[0]
        permuted = input_images[torch.randperm(batch_size)]
        augmented = self.img_aug(input_images)
        is_aug = (torch.rand(batch_size, device=input_images.device)[:, None, None, None] < self.aug_proba).float()
        result = augmented * is_aug + permuted * (1 - is_aug)
        return result

    def _fill_masks_with_gradient(self, masks):
        batch_size, _, height, width = masks.shape
        grad = torch.linspace(0, 1, steps=width * 2, device=masks.device, dtype=masks.dtype).view(1, 1, 1, -1).expand(batch_size, 1, height * 2, width * 2)
        grad = self.grad_aug(grad)
        grad = CenterCrop((height, width))(grad)
        grad *= masks
        grad_for_min = grad + (1 - masks) * 10
        grad -= grad_for_min.view(batch_size, -1).min(-1).values[:, None, None, None]
        grad /= grad.view(batch_size, -1).max(-1).values[:, None, None, None] + 1e-06
        grad.clamp_(min=0, max=1)
        return grad

def _make_blend_target(self, input_images):
    batch_size = input_images.shape[0]
    permuted = input_images[torch.randperm(batch_size)]
    augmented = self.img_aug(input_images)
    is_aug = (torch.rand(batch_size, device=input_images.device)[:, None, None, None] < self.aug_proba).float()
    result = augmented * is_aug + permuted * (1 - is_aug)
    return result

class SyncTestCase(TorchTestCase):

    def _syncParameters(self, bn1, bn2):
        bn1.reset_parameters()
        bn2.reset_parameters()
        if bn1.affine and bn2.affine:
            bn2.weight.data.copy_(bn1.weight.data)
            bn2.bias.data.copy_(bn1.bias.data)

    def _checkBatchNormResult(self, bn1, bn2, input, is_train, cuda=False):
        """Check the forward and backward for the customized batch normalization."""
        bn1.train(mode=is_train)
        bn2.train(mode=is_train)
        if cuda:
            input = input.cuda()
        self._syncParameters(_find_bn(bn1), _find_bn(bn2))
        input1 = Variable(input, requires_grad=True)
        output1 = bn1(input1)
        output1.sum().backward()
        input2 = Variable(input, requires_grad=True)
        output2 = bn2(input2)
        output2.sum().backward()
        self.assertTensorClose(input1.data, input2.data)
        self.assertTensorClose(output1.data, output2.data)
        self.assertTensorClose(input1.grad, input2.grad)
        self.assertTensorClose(_find_bn(bn1).running_mean, _find_bn(bn2).running_mean)
        self.assertTensorClose(_find_bn(bn1).running_var, _find_bn(bn2).running_var)

    def testSyncBatchNormNormalTrain(self):
        bn = nn.BatchNorm1d(10)
        sync_bn = SynchronizedBatchNorm1d(10)
        self._checkBatchNormResult(bn, sync_bn, torch.rand(16, 10), True)

    def testSyncBatchNormNormalEval(self):
        bn = nn.BatchNorm1d(10)
        sync_bn = SynchronizedBatchNorm1d(10)
        self._checkBatchNormResult(bn, sync_bn, torch.rand(16, 10), False)

    def testSyncBatchNormSyncTrain(self):
        bn = nn.BatchNorm1d(10, eps=1e-05, affine=False)
        sync_bn = SynchronizedBatchNorm1d(10, eps=1e-05, affine=False)
        sync_bn = DataParallelWithCallback(sync_bn, device_ids=[0, 1])
        bn.cuda()
        sync_bn.cuda()
        self._checkBatchNormResult(bn, sync_bn, torch.rand(16, 10), True, cuda=True)

    def testSyncBatchNormSyncEval(self):
        bn = nn.BatchNorm1d(10, eps=1e-05, affine=False)
        sync_bn = SynchronizedBatchNorm1d(10, eps=1e-05, affine=False)
        sync_bn = DataParallelWithCallback(sync_bn, device_ids=[0, 1])
        bn.cuda()
        sync_bn.cuda()
        self._checkBatchNormResult(bn, sync_bn, torch.rand(16, 10), False, cuda=True)

    def testSyncBatchNorm2DSyncTrain(self):
        bn = nn.BatchNorm2d(10)
        sync_bn = SynchronizedBatchNorm2d(10)
        sync_bn = DataParallelWithCallback(sync_bn, device_ids=[0, 1])
        bn.cuda()
        sync_bn.cuda()
        self._checkBatchNormResult(bn, sync_bn, torch.rand(16, 10, 16, 16), True, cuda=True)

def testSyncBatchNormNormalTrain(self):
    bn = nn.BatchNorm1d(10)
    sync_bn = SynchronizedBatchNorm1d(10)
    self._checkBatchNormResult(bn, sync_bn, torch.rand(16, 10), True)

def testSyncBatchNormNormalEval(self):
    bn = nn.BatchNorm1d(10)
    sync_bn = SynchronizedBatchNorm1d(10)
    self._checkBatchNormResult(bn, sync_bn, torch.rand(16, 10), False)

def testSyncBatchNormSyncTrain(self):
    bn = nn.BatchNorm1d(10, eps=1e-05, affine=False)
    sync_bn = SynchronizedBatchNorm1d(10, eps=1e-05, affine=False)
    sync_bn = DataParallelWithCallback(sync_bn, device_ids=[0, 1])
    bn.cuda()
    sync_bn.cuda()
    self._checkBatchNormResult(bn, sync_bn, torch.rand(16, 10), True, cuda=True)

def testSyncBatchNormSyncEval(self):
    bn = nn.BatchNorm1d(10, eps=1e-05, affine=False)
    sync_bn = SynchronizedBatchNorm1d(10, eps=1e-05, affine=False)
    sync_bn = DataParallelWithCallback(sync_bn, device_ids=[0, 1])
    bn.cuda()
    sync_bn.cuda()
    self._checkBatchNormResult(bn, sync_bn, torch.rand(16, 10), False, cuda=True)

def testSyncBatchNorm2DSyncTrain(self):
    bn = nn.BatchNorm2d(10)
    sync_bn = SynchronizedBatchNorm2d(10)
    sync_bn = DataParallelWithCallback(sync_bn, device_ids=[0, 1])
    bn.cuda()
    sync_bn.cuda()
    self._checkBatchNormResult(bn, sync_bn, torch.rand(16, 10, 16, 16), True, cuda=True)

class FakeFakesGenerator:

    def __init__(self, aug_proba=0.5, img_aug_degree=30, img_aug_translate=0.2):
        self.grad_aug = RandomAffine(degrees=360, translate=0.2, padding_mode=SamplePadding.REFLECTION, keepdim=False, p=1)
        self.img_aug = RandomAffine(degrees=img_aug_degree, translate=img_aug_translate, padding_mode=SamplePadding.REFLECTION, keepdim=True, p=1)
        self.aug_proba = aug_proba

    def __call__(self, input_images, masks):
        blend_masks = self._fill_masks_with_gradient(masks)
        blend_target = self._make_blend_target(input_images)
        result = input_images * (1 - blend_masks) + blend_target * blend_masks
        return (result, blend_masks)

    def _make_blend_target(self, input_images):
        batch_size = input_images.shape[0]
        permuted = input_images[torch.randperm(batch_size)]
        augmented = self.img_aug(input_images)
        is_aug = (torch.rand(batch_size, device=input_images.device)[:, None, None, None] < self.aug_proba).float()
        result = augmented * is_aug + permuted * (1 - is_aug)
        return result

    def _fill_masks_with_gradient(self, masks):
        batch_size, _, height, width = masks.shape
        grad = torch.linspace(0, 1, steps=width * 2, device=masks.device, dtype=masks.dtype).view(1, 1, 1, -1).expand(batch_size, 1, height * 2, width * 2)
        grad = self.grad_aug(grad)
        grad = CenterCrop((height, width))(grad)
        grad *= masks
        grad_for_min = grad + (1 - masks) * 10
        grad -= grad_for_min.view(batch_size, -1).min(-1).values[:, None, None, None]
        grad /= grad.view(batch_size, -1).max(-1).values[:, None, None, None] + 1e-06
        grad.clamp_(min=0, max=1)
        return grad

def _make_blend_target(self, input_images):
    batch_size = input_images.shape[0]
    permuted = input_images[torch.randperm(batch_size)]
    augmented = self.img_aug(input_images)
    is_aug = (torch.rand(batch_size, device=input_images.device)[:, None, None, None] < self.aug_proba).float()
    result = augmented * is_aug + permuted * (1 - is_aug)
    return result

class SyncTestCase(TorchTestCase):

    def _syncParameters(self, bn1, bn2):
        bn1.reset_parameters()
        bn2.reset_parameters()
        if bn1.affine and bn2.affine:
            bn2.weight.data.copy_(bn1.weight.data)
            bn2.bias.data.copy_(bn1.bias.data)

    def _checkBatchNormResult(self, bn1, bn2, input, is_train, cuda=False):
        """Check the forward and backward for the customized batch normalization."""
        bn1.train(mode=is_train)
        bn2.train(mode=is_train)
        if cuda:
            input = input.cuda()
        self._syncParameters(_find_bn(bn1), _find_bn(bn2))
        input1 = Variable(input, requires_grad=True)
        output1 = bn1(input1)
        output1.sum().backward()
        input2 = Variable(input, requires_grad=True)
        output2 = bn2(input2)
        output2.sum().backward()
        self.assertTensorClose(input1.data, input2.data)
        self.assertTensorClose(output1.data, output2.data)
        self.assertTensorClose(input1.grad, input2.grad)
        self.assertTensorClose(_find_bn(bn1).running_mean, _find_bn(bn2).running_mean)
        self.assertTensorClose(_find_bn(bn1).running_var, _find_bn(bn2).running_var)

    def testSyncBatchNormNormalTrain(self):
        bn = nn.BatchNorm1d(10)
        sync_bn = SynchronizedBatchNorm1d(10)
        self._checkBatchNormResult(bn, sync_bn, torch.rand(16, 10), True)

    def testSyncBatchNormNormalEval(self):
        bn = nn.BatchNorm1d(10)
        sync_bn = SynchronizedBatchNorm1d(10)
        self._checkBatchNormResult(bn, sync_bn, torch.rand(16, 10), False)

    def testSyncBatchNormSyncTrain(self):
        bn = nn.BatchNorm1d(10, eps=1e-05, affine=False)
        sync_bn = SynchronizedBatchNorm1d(10, eps=1e-05, affine=False)
        sync_bn = DataParallelWithCallback(sync_bn, device_ids=[0, 1])
        bn.cuda()
        sync_bn.cuda()
        self._checkBatchNormResult(bn, sync_bn, torch.rand(16, 10), True, cuda=True)

    def testSyncBatchNormSyncEval(self):
        bn = nn.BatchNorm1d(10, eps=1e-05, affine=False)
        sync_bn = SynchronizedBatchNorm1d(10, eps=1e-05, affine=False)
        sync_bn = DataParallelWithCallback(sync_bn, device_ids=[0, 1])
        bn.cuda()
        sync_bn.cuda()
        self._checkBatchNormResult(bn, sync_bn, torch.rand(16, 10), False, cuda=True)

    def testSyncBatchNorm2DSyncTrain(self):
        bn = nn.BatchNorm2d(10)
        sync_bn = SynchronizedBatchNorm2d(10)
        sync_bn = DataParallelWithCallback(sync_bn, device_ids=[0, 1])
        bn.cuda()
        sync_bn.cuda()
        self._checkBatchNormResult(bn, sync_bn, torch.rand(16, 10, 16, 16), True, cuda=True)

def testSyncBatchNormNormalTrain(self):
    bn = nn.BatchNorm1d(10)
    sync_bn = SynchronizedBatchNorm1d(10)
    self._checkBatchNormResult(bn, sync_bn, torch.rand(16, 10), True)

def testSyncBatchNormNormalEval(self):
    bn = nn.BatchNorm1d(10)
    sync_bn = SynchronizedBatchNorm1d(10)
    self._checkBatchNormResult(bn, sync_bn, torch.rand(16, 10), False)

def testSyncBatchNormSyncTrain(self):
    bn = nn.BatchNorm1d(10, eps=1e-05, affine=False)
    sync_bn = SynchronizedBatchNorm1d(10, eps=1e-05, affine=False)
    sync_bn = DataParallelWithCallback(sync_bn, device_ids=[0, 1])
    bn.cuda()
    sync_bn.cuda()
    self._checkBatchNormResult(bn, sync_bn, torch.rand(16, 10), True, cuda=True)

def testSyncBatchNormSyncEval(self):
    bn = nn.BatchNorm1d(10, eps=1e-05, affine=False)
    sync_bn = SynchronizedBatchNorm1d(10, eps=1e-05, affine=False)
    sync_bn = DataParallelWithCallback(sync_bn, device_ids=[0, 1])
    bn.cuda()
    sync_bn.cuda()
    self._checkBatchNormResult(bn, sync_bn, torch.rand(16, 10), False, cuda=True)

def testSyncBatchNorm2DSyncTrain(self):
    bn = nn.BatchNorm2d(10)
    sync_bn = SynchronizedBatchNorm2d(10)
    sync_bn = DataParallelWithCallback(sync_bn, device_ids=[0, 1])
    bn.cuda()
    sync_bn.cuda()
    self._checkBatchNormResult(bn, sync_bn, torch.rand(16, 10, 16, 16), True, cuda=True)

class Searcher(object):

    def __init__(self, database, retriever_version='ViT-L/14'):
        assert database in DATABASES
        self.database_name = database
        self.searcher_savedir = f'data/rdm/searchers/{self.database_name}'
        self.database_path = f'data/rdm/retrieval_databases/{self.database_name}'
        self.retriever = self.load_retriever(version=retriever_version)
        self.database = {'embedding': [], 'img_id': [], 'patch_coords': []}
        self.load_database()
        self.load_searcher()

    def train_searcher(self, k, metric='dot_product', searcher_savedir=None):
        print('Start training searcher')
        searcher = scann.scann_ops_pybind.builder(self.database['embedding'] / np.linalg.norm(self.database['embedding'], axis=1)[:, np.newaxis], k, metric)
        self.searcher = searcher.score_brute_force().build()
        print('Finish training searcher')
        if searcher_savedir is not None:
            print(f'Save trained searcher under "{searcher_savedir}"')
            os.makedirs(searcher_savedir, exist_ok=True)
            self.searcher.serialize(searcher_savedir)

    def load_single_file(self, saved_embeddings):
        compressed = np.load(saved_embeddings)
        self.database = {key: compressed[key] for key in compressed.files}
        print('Finished loading of clip embeddings.')

    def load_multi_files(self, data_archive):
        out_data = {key: [] for key in self.database}
        for d in tqdm(data_archive, desc=f'Loading datapool from {len(data_archive)} individual files.'):
            for key in d.files:
                out_data[key].append(d[key])
        return out_data

    def load_database(self):
        print(f'Load saved patch embedding from "{self.database_path}"')
        file_content = glob.glob(os.path.join(self.database_path, '*.npz'))
        if len(file_content) == 1:
            self.load_single_file(file_content[0])
        elif len(file_content) > 1:
            data = [np.load(f) for f in file_content]
            prefetched_data = parallel_data_prefetch(self.load_multi_files, data, n_proc=min(len(data), cpu_count()), target_data_type='dict')
            self.database = {key: np.concatenate([od[key] for od in prefetched_data], axis=1)[0] for key in self.database}
        else:
            raise ValueError(f'No npz-files in specified path "{self.database_path}" is this directory existing?')
        print(f'Finished loading of retrieval database of length {self.database['embedding'].shape[0]}.')

    def load_retriever(self, version='ViT-L/14'):
        model = FrozenClipImageEmbedder(model=version)
        if torch.cuda.is_available():
            model.cuda()
        model.eval()
        return model

    def load_searcher(self):
        print(f'load searcher for database {self.database_name} from {self.searcher_savedir}')
        self.searcher = scann.scann_ops_pybind.load_searcher(self.searcher_savedir)
        print('Finished loading searcher.')

    def search(self, x, k):
        if self.searcher is None and self.database['embedding'].shape[0] < 20000.0:
            self.train_searcher(k)
        assert self.searcher is not None, 'Cannot search with uninitialized searcher'
        if isinstance(x, torch.Tensor):
            x = x.detach().cpu().numpy()
        if len(x.shape) == 3:
            x = x[:, 0]
        query_embeddings = x / np.linalg.norm(x, axis=1)[:, np.newaxis]
        start = time.time()
        nns, distances = self.searcher.search_batched(query_embeddings, final_num_neighbors=k)
        end = time.time()
        out_embeddings = self.database['embedding'][nns]
        out_img_ids = self.database['img_id'][nns]
        out_pc = self.database['patch_coords'][nns]
        out = {'nn_embeddings': out_embeddings / np.linalg.norm(out_embeddings, axis=-1)[..., np.newaxis], 'img_ids': out_img_ids, 'patch_coords': out_pc, 'queries': x, 'exec_time': end - start, 'nns': nns, 'q_embeddings': query_embeddings}
        return out

    def __call__(self, x, n):
        return self.search(x, n)

def load_retriever(self, version='ViT-L/14'):
    model = FrozenClipImageEmbedder(model=version)
    if torch.cuda.is_available():
        model.cuda()
    model.eval()
    return model

def uniform_on_device(r1, r2, shape, device):
    return (r1 - r2) * torch.rand(*shape, device=device) + r2

class Renderer:

    def __init__(self, obj_path):
        self.scene = materialed_meshes(obj_path)
        self.num_samples = 5000

    def read_int(self):
        self.H = 1280 // 3
        self.W = 1920 // 3
        self.focal = 2083 // 3
        self.buffer = torch.zeros(self.H * self.W, 3).to('cuda')

    def read_ext(self):
        self.c2w = np.array([[0.0123957, -0.00906409, -0.99988209, 2.35675933], [-0.99987913, 0.00927219, -0.01247972, -0.01891149], [0.00938421, 0.99991593, -0.00894806, 2.11490003]]).astype(np.float32)

    def read_env(self, envpath):
        """ envmap: viewing -Z
            Y
            | 
            |
            .------ X
           /       
          Z
        """
        self.env = EnvironmentMap(envpath, 'latlong')
        data = np.ones((2048, 4096, 3))
        self.env = EnvironmentMap(data, 'latlong')

    def IBL(self, light_dir):
        """
        Args:
            light_dir: [num_sample, 3], torch.tensor

        Returns:
            light_intensity:  [num_sample, 3], torch.tensor
        """

        def world2latlong(x, y, z):
            """Get the (u, v) coordinates of the point defined by (x, y, z) for
            a latitude-longitude map."""
            u = 1 + 1 / np.pi * torch.arctan2(x, -z)
            v = 1 / np.pi * torch.arccos(y)
            u = u / 2
            return (u, v)
        light_dir_envmap = [-light_dir[:, 1], light_dir[:, 2], -light_dir[:, 0]]
        uu, vv = world2latlong(light_dir_envmap[0], light_dir_envmap[1], light_dir_envmap[2])
        uu = np.floor(uu.cpu().numpy() * self.env.data.shape[1] % self.env.data.shape[1]).astype(int)
        vv = np.floor(vv.cpu().numpy() * self.env.data.shape[0] % self.env.data.shape[0]).astype(int)
        light_intensity = self.env.data[vv, uu]
        light_intensity = torch.from_numpy(light_intensity).to(light_dir)
        return light_intensity

    def render_hdri(self):
        self.buffer = self.IBL(torch.from_numpy(self.ray_d))

    def render(self):
        timer = Timer()
        directions = get_ray_directions(self.H, self.W, self.focal)
        self.ray_o, self.ray_d = get_rays(directions, self.c2w)
        timer.print('generating rays')
        self.render_hdri()
        timer.print('HDRI background rendering')
        mesh_all = self.scene.get_all_meshes()
        intersections, index_ray, index_tri = mesh_all.ray.intersects_location(ray_origins=self.ray_o, ray_directions=self.ray_d, multiple_hits=False)
        intersection_normals = mesh_all.face_normals[index_tri].astype(np.float32)
        timer.print('ray-mesh intersection')
        num_hit = intersections.shape[0]
        print(f'number of intersection: {num_hit}')
        for i in range(num_hit):
            intersection_p = intersections[i]
            normal = intersection_normals[i]
            idx_in_ray = index_ray[i]
            idx_in_faces = index_tri[i]
            wo = -self.ray_d[idx_in_ray]
            material, face_local, uv_local = self.scene.get_material_from_face_idx_of_all(idx_in_faces)
            if 'kd' not in material.kwargs:
                material_image = material.image
                u, v = uv_local[0]
                u = u - floor(u)
                v = v - floor(v)
                width, height = material_image.size
                pixel_x = int(u * (width - 1))
                pixel_y = int(v * (height - 1))
                kd = material_image.getpixel((pixel_x, pixel_y))
                if isinstance(kd, int):
                    kd = [kd, kd, kd]
                material.kwargs['kd'] = [kd[0] / 255, kd[1] / 255, kd[2] / 255]
            material_dict = rename_material_dict(material.kwargs)
            bdrf = UE4BRDF(base_color=material_dict['kd'], metallic=material_dict['pm'], roughness=material_dict['pr'], specular=material_dict['ks'])
            if material_dict['pr'] == 0:
                wi = 2 * np.dot(wo, normal) * normal - wo
                wi = torch.from_numpy(wi).cuda().reshape(1, 3)
                colors = self.IBL(wi)
            else:
                color = torch.zeros(3).cuda()
                normal = torch.from_numpy(normal).cuda()
                normal = normal / normal.norm()
                normal = normal.expand(self.num_samples, 3)
                view_dir = torch.from_numpy(wo).cuda()
                view_dir = view_dir.expand(self.num_samples, 3)
                light_dir = random_samples_on_hemisphere(normal, self.num_samples)
                brdfs = bdrf.evaluate_parallel(normal, light_dir, view_dir)
                light_intensity = self.IBL(light_dir)
                n_dot_l = torch.einsum('ij,ij->i', normal, light_dir).unsqueeze(-1).expand(-1, 3)
                colors = light_intensity * brdfs * n_dot_l / (0.5 / np.pi)
            self.buffer[idx_in_ray] = colors.mean(0)
        timer.print('Rendering foreground')
        self.renderd_image = self.buffer.reshape(self.H, self.W, 3)
        self.renderd_image = srgb_gamma_correction_torch(self.renderd_image)
        output = (self.renderd_image * 255).cpu().numpy().astype(np.uint8)
        imageio.imsave('/home/yfl/workspace/LDR_to_HDR/logs/rendered_result_pos2_whitehdr_kloppenheim_05_1k.png', output)

def render_hdri(self):
    self.buffer = self.IBL(torch.from_numpy(self.ray_d))

def render(self):
    timer = Timer()
    directions = get_ray_directions(self.H, self.W, self.focal)
    self.ray_o, self.ray_d = get_rays(directions, self.c2w)
    timer.print('generating rays')
    self.render_hdri()
    timer.print('HDRI background rendering')
    mesh_all = self.scene.get_all_meshes()
    intersections, index_ray, index_tri = mesh_all.ray.intersects_location(ray_origins=self.ray_o, ray_directions=self.ray_d, multiple_hits=False)
    intersection_normals = mesh_all.face_normals[index_tri].astype(np.float32)
    timer.print('ray-mesh intersection')
    num_hit = intersections.shape[0]
    print(f'number of intersection: {num_hit}')
    for i in range(num_hit):
        intersection_p = intersections[i]
        normal = intersection_normals[i]
        idx_in_ray = index_ray[i]
        idx_in_faces = index_tri[i]
        wo = -self.ray_d[idx_in_ray]
        material, face_local, uv_local = self.scene.get_material_from_face_idx_of_all(idx_in_faces)
        if 'kd' not in material.kwargs:
            material_image = material.image
            u, v = uv_local[0]
            u = u - floor(u)
            v = v - floor(v)
            width, height = material_image.size
            pixel_x = int(u * (width - 1))
            pixel_y = int(v * (height - 1))
            kd = material_image.getpixel((pixel_x, pixel_y))
            if isinstance(kd, int):
                kd = [kd, kd, kd]
            material.kwargs['kd'] = [kd[0] / 255, kd[1] / 255, kd[2] / 255]
        material_dict = rename_material_dict(material.kwargs)
        bdrf = UE4BRDF(base_color=material_dict['kd'], metallic=material_dict['pm'], roughness=material_dict['pr'], specular=material_dict['ks'])
        if material_dict['pr'] == 0:
            wi = 2 * np.dot(wo, normal) * normal - wo
            wi = torch.from_numpy(wi).cuda().reshape(1, 3)
            colors = self.IBL(wi)
        else:
            color = torch.zeros(3).cuda()
            normal = torch.from_numpy(normal).cuda()
            normal = normal / normal.norm()
            normal = normal.expand(self.num_samples, 3)
            view_dir = torch.from_numpy(wo).cuda()
            view_dir = view_dir.expand(self.num_samples, 3)
            light_dir = random_samples_on_hemisphere(normal, self.num_samples)
            brdfs = bdrf.evaluate_parallel(normal, light_dir, view_dir)
            light_intensity = self.IBL(light_dir)
            n_dot_l = torch.einsum('ij,ij->i', normal, light_dir).unsqueeze(-1).expand(-1, 3)
            colors = light_intensity * brdfs * n_dot_l / (0.5 / np.pi)
        self.buffer[idx_in_ray] = colors.mean(0)
    timer.print('Rendering foreground')
    self.renderd_image = self.buffer.reshape(self.H, self.W, 3)
    self.renderd_image = srgb_gamma_correction_torch(self.renderd_image)
    output = (self.renderd_image * 255).cpu().numpy().astype(np.uint8)
    imageio.imsave('/home/yfl/workspace/LDR_to_HDR/logs/rendered_result_pos2_whitehdr_kloppenheim_05_1k.png', output)

def adjust_exposure(image, range=(-2.5, 0.5)):
    exposure = np.random.rand() * (range[1] - range[0]) + range[0]
    return image * 2 ** exposure

def adjust_color_temperature(img, temp_range):
    """
    调整图像的色温
    :param img: np.ndarray, 图像数据
    :param temperature: float, 色温调整的比例，大于1表示变暖，小于1表示变冷
    :return: np.ndarray, 色温调整后的图像
    """
    temperature = np.random.rand() * (temp_range[1] - temp_range[0]) + temp_range[0]
    img[:, :, 2] = img[:, :, 2] * temperature
    img[:, :, 0] = img[:, :, 0] / temperature
    return img

class subRender:

    def __init__(self, scene, inter_dict):
        self.scene = scene
        self.inter_dict = inter_dict
        self.num_samples = 5000

    def render(self, ids):
        color_list = []
        for i in ids:
            normal = self.inter_dict['intersection_normals'][i]
            idx_in_ray = self.inter_dict['index_ray'][i]
            idx_in_faces = self.inter_dict['index_tri'][i]
            wi = -self.inter_dict['ray_d'][idx_in_ray]
            material, face_local, uv_local = self.scene.get_material_from_face_idx_of_all(idx_in_faces)
            if 'kd' not in material.kwargs:
                material_image = material.image
                u, v = uv_local[0]
                u = u - floor(u)
                v = v - floor(v)
                width, height = material_image.size
                pixel_x = int(u * (width - 1))
                pixel_y = int(v * (height - 1))
                kd = material_image.getpixel((pixel_x, pixel_y))
                if isinstance(kd, int):
                    kd = [kd, kd, kd]
                material.kwargs['kd'] = [kd[0] / 255, kd[1] / 255, kd[2] / 255]
            material_dict = rename_material_dict(material.kwargs)
            bdrf = UE4BRDF(base_color=material_dict['kd'], metallic=material_dict['pm'], roughness=material_dict['pr'], specular=material_dict['ks'])
            normal = torch.from_numpy(normal).cuda()
            normal = normal / normal.norm()
            light_dir = torch.from_numpy(wi).cuda()
            light_dir = light_dir / light_dir.norm()
            normal = normal.expand(self.num_samples, 3)
            light_dir = light_dir.expand(self.num_samples, 3)
            view_dir = random_samples_on_hemisphere(normal, self.num_samples)
            color = bdrf.evaluate_parallel(normal, light_dir, view_dir).mean(dim=0)
            color_list.append(color)
        return torch.stack(color_list)

def render(self, ids):
    color_list = []
    for i in ids:
        normal = self.inter_dict['intersection_normals'][i]
        idx_in_ray = self.inter_dict['index_ray'][i]
        idx_in_faces = self.inter_dict['index_tri'][i]
        wi = -self.inter_dict['ray_d'][idx_in_ray]
        material, face_local, uv_local = self.scene.get_material_from_face_idx_of_all(idx_in_faces)
        if 'kd' not in material.kwargs:
            material_image = material.image
            u, v = uv_local[0]
            u = u - floor(u)
            v = v - floor(v)
            width, height = material_image.size
            pixel_x = int(u * (width - 1))
            pixel_y = int(v * (height - 1))
            kd = material_image.getpixel((pixel_x, pixel_y))
            if isinstance(kd, int):
                kd = [kd, kd, kd]
            material.kwargs['kd'] = [kd[0] / 255, kd[1] / 255, kd[2] / 255]
        material_dict = rename_material_dict(material.kwargs)
        bdrf = UE4BRDF(base_color=material_dict['kd'], metallic=material_dict['pm'], roughness=material_dict['pr'], specular=material_dict['ks'])
        normal = torch.from_numpy(normal).cuda()
        normal = normal / normal.norm()
        light_dir = torch.from_numpy(wi).cuda()
        light_dir = light_dir / light_dir.norm()
        normal = normal.expand(self.num_samples, 3)
        light_dir = light_dir.expand(self.num_samples, 3)
        view_dir = random_samples_on_hemisphere(normal, self.num_samples)
        color = bdrf.evaluate_parallel(normal, light_dir, view_dir).mean(dim=0)
        color_list.append(color)
    return torch.stack(color_list)

class Renderer:

    def __init__(self, obj_path):
        self.scene = materialed_meshes(obj_path)
        self.num_samples = 5000
        self.num_processes = 2

    def read_int(self):
        self.H = 1280
        self.W = 1920
        self.focal = 2083
        self.buffer = torch.zeros(self.H * self.W, 3).to('cuda')

    def read_ext(self):
        self.c2w = np.array([[0.0123957, -0.00906409, -0.99988209, 2.35675933], [-0.99987913, 0.00927219, -0.01247972, -0.01891149], [0.00938421, 0.99991593, -0.00894806, 2.11490003]]).astype(np.float32)

    def read_env(self, envpath):
        """ envmap: viewing -Z
            Y
            | 
            |
            .------ X
           /       
          Z
        """
        self.env = EnvironmentMap(envpath, 'latlong')

    def IBL(self, light_dir):
        """
        transform light_dir in world coord to envmap coor. hand-crafted
        """
        light_dir_np = light_dir.cpu().numpy()
        light_dir_envmap = [-light_dir_np[1], light_dir_np[2], -light_dir_np[0]]
        uu, vv = self.env.world2pixel(light_dir_envmap[0], light_dir_envmap[1], light_dir_envmap[2])
        light_intensity = torch.tensor(self.env.data[vv, uu], device='cuda', dtype=torch.float32)
        return light_intensity

    def render(self):
        multiprocessing.set_start_method('spawn')
        timer = Timer()
        directions = get_ray_directions(self.H, self.W, self.focal)
        self.ray_o, self.ray_d = get_rays(directions, self.c2w)
        timer.print('generating rays')
        mesh_all = self.scene.get_all_meshes()
        intersections, index_ray, index_tri = mesh_all.ray.intersects_location(ray_origins=self.ray_o, ray_directions=self.ray_d, multiple_hits=False)
        intersection_normals = mesh_all.face_normals[index_tri].astype(np.float32)
        timer.print('ray-mesh intersection')
        num_hit = intersections.shape[0]
        print(f'number of intersection: {num_hit}')
        self.inter_dict = OrderedDict()
        self.inter_dict['index_ray'] = index_ray
        self.inter_dict['index_tri'] = index_tri
        self.inter_dict['intersection_normals'] = intersection_normals
        self.inter_dict['ray_d'] = self.ray_d
        pool = multiprocessing.Pool(processes=self.num_processes)
        tasks = np.array_split(np.arange(num_hit), self.num_processes)
        results = pool.starmap(parallel_rendering, [(deepcopy(self.scene), deepcopy(self.inter_dict), ids) for ids in tasks])
        pool.close()
        pool.join()
        colors = torch.cat(results, dim=0)
        self.buffer[index_ray] = colors
        timer.print('Rendering foreground')
        self.renderd_image = self.buffer.reshape(self.H, self.W, 3)
        self.renderd_image = srgb_gamma_correction_torch(self.renderd_image)
        output = (self.renderd_image * 255).cpu().numpy().astype(np.uint8)
        imageio.imsave('/home/yfl/workspace/LDR_to_HDR/logs/rendered_result.png', output)

def render(self):
    multiprocessing.set_start_method('spawn')
    timer = Timer()
    directions = get_ray_directions(self.H, self.W, self.focal)
    self.ray_o, self.ray_d = get_rays(directions, self.c2w)
    timer.print('generating rays')
    mesh_all = self.scene.get_all_meshes()
    intersections, index_ray, index_tri = mesh_all.ray.intersects_location(ray_origins=self.ray_o, ray_directions=self.ray_d, multiple_hits=False)
    intersection_normals = mesh_all.face_normals[index_tri].astype(np.float32)
    timer.print('ray-mesh intersection')
    num_hit = intersections.shape[0]
    print(f'number of intersection: {num_hit}')
    self.inter_dict = OrderedDict()
    self.inter_dict['index_ray'] = index_ray
    self.inter_dict['index_tri'] = index_tri
    self.inter_dict['intersection_normals'] = intersection_normals
    self.inter_dict['ray_d'] = self.ray_d
    pool = multiprocessing.Pool(processes=self.num_processes)
    tasks = np.array_split(np.arange(num_hit), self.num_processes)
    results = pool.starmap(parallel_rendering, [(deepcopy(self.scene), deepcopy(self.inter_dict), ids) for ids in tasks])
    pool.close()
    pool.join()
    colors = torch.cat(results, dim=0)
    self.buffer[index_ray] = colors
    timer.print('Rendering foreground')
    self.renderd_image = self.buffer.reshape(self.H, self.W, 3)
    self.renderd_image = srgb_gamma_correction_torch(self.renderd_image)
    output = (self.renderd_image * 255).cpu().numpy().astype(np.uint8)
    imageio.imsave('/home/yfl/workspace/LDR_to_HDR/logs/rendered_result.png', output)

