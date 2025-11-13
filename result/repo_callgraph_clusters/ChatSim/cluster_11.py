# Cluster 11

def l2_loss(network_output, gt):
    return ((network_output - gt) ** 2).mean()

def _ssim(img1, img2, window, window_size, channel, size_average=True):
    mu1 = F.conv2d(img1, window, padding=window_size // 2, groups=channel)
    mu2 = F.conv2d(img2, window, padding=window_size // 2, groups=channel)
    mu1_sq = mu1.pow(2)
    mu2_sq = mu2.pow(2)
    mu1_mu2 = mu1 * mu2
    sigma1_sq = F.conv2d(img1 * img1, window, padding=window_size // 2, groups=channel) - mu1_sq
    sigma2_sq = F.conv2d(img2 * img2, window, padding=window_size // 2, groups=channel) - mu2_sq
    sigma12 = F.conv2d(img1 * img2, window, padding=window_size // 2, groups=channel) - mu1_mu2
    C1 = 0.01 ** 2
    C2 = 0.03 ** 2
    ssim_map = (2 * mu1_mu2 + C1) * (2 * sigma12 + C2) / ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
    if size_average:
        return ssim_map.mean()
    else:
        return ssim_map.mean(1).mean(1).mean(1)

def psnr(img1, img2):
    mse = ((img1 - img2) ** 2).view(img1.shape[0], -1).mean(1, keepdim=True)
    return 20 * torch.log10(1.0 / torch.sqrt(mse))

def get_center_and_diag(cam_centers):
    cam_centers = np.hstack(cam_centers)
    avg_cam_center = np.mean(cam_centers, axis=1, keepdims=True)
    center = avg_cam_center
    dist = np.linalg.norm(cam_centers - center, axis=0, keepdims=True)
    diagonal = np.max(dist)
    return (center.flatten(), diagonal)

class GaussianModel:

    def setup_functions(self):

        def build_covariance_from_scaling_rotation(scaling, scaling_modifier, rotation):
            L = build_scaling_rotation(scaling_modifier * scaling, rotation)
            actual_covariance = L @ L.transpose(1, 2)
            symm = strip_symmetric(actual_covariance)
            return symm
        self.scaling_activation = torch.exp
        self.scaling_inverse_activation = torch.log
        self.covariance_activation = build_covariance_from_scaling_rotation
        self.opacity_activation = torch.sigmoid
        self.inverse_opacity_activation = inverse_sigmoid
        self.rotation_activation = torch.nn.functional.normalize

    def __init__(self, args):
        self.active_sh_degree = 0
        self.max_sh_degree = args.sh_degree
        self._xyz = torch.empty(0)
        self._features_dc = torch.empty(0)
        self._features_rest = torch.empty(0)
        self._scaling = torch.empty(0)
        self._rotation = torch.empty(0)
        self._opacity = torch.empty(0)
        self.max_radii2D = torch.empty(0)
        self.xyz_gradient_accum = torch.empty(0)
        self.denom = torch.empty(0)
        self.optimizer = None
        self.percent_dense = 0
        self.spatial_lr_scale = 0
        self.setup_functions()
        if args.get('sky_model', None) is not None:
            model_filename = 'scene.sky.' + args.sky_model
            model_lib = importlib.import_module(model_filename)
            model_cls = None
            target_model_name = args.sky_model.replace('_', '')
            for name, cls in model_lib.__dict__.items():
                if name.lower() == target_model_name.lower():
                    model_cls = cls
            self.sky_model = model_cls(args.sky_model_args).cuda()
        else:
            self.sky_model = None

    def capture(self):
        return_list = [self.active_sh_degree, self._xyz, self._features_dc, self._features_rest, self._scaling, self._rotation, self._opacity, self.max_radii2D, self.xyz_gradient_accum, self.denom, self.optimizer.state_dict(), self.spatial_lr_scale]
        if self.sky_model is not None:
            return_list.append(self.sky_model.capture())
        return return_list

    def restore(self, model_args, training_args):
        if self.sky_model is not None:
            self.sky_model.restore(model_args.pop(-1))
        self.active_sh_degree, self._xyz, self._features_dc, self._features_rest, self._scaling, self._rotation, self._opacity, self.max_radii2D, xyz_gradient_accum, denom, opt_dict, self.spatial_lr_scale = model_args
        self.training_setup(training_args)
        self.xyz_gradient_accum = xyz_gradient_accum
        self.denom = denom
        self.optimizer.load_state_dict(opt_dict)

    @property
    def get_scaling(self):
        return self.scaling_activation(self._scaling)

    @property
    def get_rotation(self):
        return self.rotation_activation(self._rotation)

    @property
    def get_xyz(self):
        return self._xyz

    @property
    def get_features(self):
        features_dc = self._features_dc
        features_rest = self._features_rest
        return torch.cat((features_dc, features_rest), dim=1)

    @property
    def get_opacity(self):
        return self.opacity_activation(self._opacity)

    def get_covariance(self, scaling_modifier=1):
        return self.covariance_activation(self.get_scaling, scaling_modifier, self._rotation)

    def oneupSHdegree(self):
        if self.active_sh_degree < self.max_sh_degree:
            self.active_sh_degree += 1

    def create_from_pcd(self, pcd: BasicPointCloud, spatial_lr_scale: float):
        self.spatial_lr_scale = spatial_lr_scale
        fused_point_cloud = torch.tensor(np.asarray(pcd.points)).float().cuda()
        fused_color = RGB2SH(torch.tensor(np.asarray(pcd.colors)).float().cuda())
        features = torch.zeros((fused_color.shape[0], 3, (self.max_sh_degree + 1) ** 2)).float().cuda()
        features[:, :3, 0] = fused_color
        features[:, 3:, 1:] = 0.0
        print('Number of points at initialisation : ', fused_point_cloud.shape[0])
        dist2 = torch.clamp_min(distCUDA2(torch.from_numpy(np.asarray(pcd.points)).float().cuda()), 1e-07)
        scales = torch.log(torch.sqrt(dist2))[..., None].repeat(1, 3)
        rots = torch.zeros((fused_point_cloud.shape[0], 4), device='cuda')
        rots[:, 0] = 1
        opacities = inverse_sigmoid(0.1 * torch.ones((fused_point_cloud.shape[0], 1), dtype=torch.float, device='cuda'))
        self._xyz = nn.Parameter(fused_point_cloud.requires_grad_(True))
        self._features_dc = nn.Parameter(features[:, :, 0:1].transpose(1, 2).contiguous().requires_grad_(True))
        self._features_rest = nn.Parameter(features[:, :, 1:].transpose(1, 2).contiguous().requires_grad_(True))
        self._scaling = nn.Parameter(scales.requires_grad_(True))
        self._rotation = nn.Parameter(rots.requires_grad_(True))
        self._opacity = nn.Parameter(opacities.requires_grad_(True))
        self.max_radii2D = torch.zeros(self.get_xyz.shape[0], device='cuda')

    def training_setup(self, training_args):
        self.percent_dense = training_args.percent_dense
        self.xyz_gradient_accum = torch.zeros((self.get_xyz.shape[0], 1), device='cuda')
        self.denom = torch.zeros((self.get_xyz.shape[0], 1), device='cuda')
        l = [{'params': [self._xyz], 'lr': training_args.position_lr_init * self.spatial_lr_scale, 'name': 'xyz'}, {'params': [self._features_dc], 'lr': training_args.feature_lr, 'name': 'f_dc'}, {'params': [self._features_rest], 'lr': training_args.feature_lr / 20.0, 'name': 'f_rest'}, {'params': [self._opacity], 'lr': training_args.opacity_lr, 'name': 'opacity'}, {'params': [self._scaling], 'lr': training_args.scaling_lr, 'name': 'scaling'}, {'params': [self._rotation], 'lr': training_args.rotation_lr, 'name': 'rotation'}]
        if self.sky_model is not None:
            l += ({'params': self.sky_model.train_params(), 'lr': training_args.sky_model_lr, 'name': 'sky_model'},)
        self.optimizer = torch.optim.Adam(l, lr=0.0, eps=1e-15)
        self.xyz_scheduler_args = get_expon_lr_func(lr_init=training_args.position_lr_init * self.spatial_lr_scale, lr_final=training_args.position_lr_final * self.spatial_lr_scale, lr_delay_mult=training_args.position_lr_delay_mult, max_steps=training_args.position_lr_max_steps)

    def update_learning_rate(self, iteration):
        """ Learning rate scheduling per step """
        for param_group in self.optimizer.param_groups:
            if param_group['name'] == 'xyz':
                lr = self.xyz_scheduler_args(iteration)
                param_group['lr'] = lr
                return lr

    def construct_list_of_attributes(self):
        l = ['x', 'y', 'z', 'nx', 'ny', 'nz']
        for i in range(self._features_dc.shape[1] * self._features_dc.shape[2]):
            l.append('f_dc_{}'.format(i))
        for i in range(self._features_rest.shape[1] * self._features_rest.shape[2]):
            l.append('f_rest_{}'.format(i))
        l.append('opacity')
        for i in range(self._scaling.shape[1]):
            l.append('scale_{}'.format(i))
        for i in range(self._rotation.shape[1]):
            l.append('rot_{}'.format(i))
        return l

    def save_ply(self, path):
        mkdir_p(os.path.dirname(path))
        xyz = self._xyz.detach().cpu().numpy()
        normals = np.zeros_like(xyz)
        f_dc = self._features_dc.detach().transpose(1, 2).flatten(start_dim=1).contiguous().cpu().numpy()
        f_rest = self._features_rest.detach().transpose(1, 2).flatten(start_dim=1).contiguous().cpu().numpy()
        opacities = self._opacity.detach().cpu().numpy()
        scale = self._scaling.detach().cpu().numpy()
        rotation = self._rotation.detach().cpu().numpy()
        dtype_full = [(attribute, 'f4') for attribute in self.construct_list_of_attributes()]
        elements = np.empty(xyz.shape[0], dtype=dtype_full)
        attributes = np.concatenate((xyz, normals, f_dc, f_rest, opacities, scale, rotation), axis=1)
        elements[:] = list(map(tuple, attributes))
        el = PlyElement.describe(elements, 'vertex')
        PlyData([el]).write(path)

    def reset_opacity(self):
        opacities_new = inverse_sigmoid(torch.min(self.get_opacity, torch.ones_like(self.get_opacity) * 0.01))
        optimizable_tensors = self.replace_tensor_to_optimizer(opacities_new, 'opacity')
        self._opacity = optimizable_tensors['opacity']

    def load_ply(self, path):
        plydata = PlyData.read(path)
        xyz = np.stack((np.asarray(plydata.elements[0]['x']), np.asarray(plydata.elements[0]['y']), np.asarray(plydata.elements[0]['z'])), axis=1)
        opacities = np.asarray(plydata.elements[0]['opacity'])[..., np.newaxis]
        features_dc = np.zeros((xyz.shape[0], 3, 1))
        features_dc[:, 0, 0] = np.asarray(plydata.elements[0]['f_dc_0'])
        features_dc[:, 1, 0] = np.asarray(plydata.elements[0]['f_dc_1'])
        features_dc[:, 2, 0] = np.asarray(plydata.elements[0]['f_dc_2'])
        extra_f_names = [p.name for p in plydata.elements[0].properties if p.name.startswith('f_rest_')]
        extra_f_names = sorted(extra_f_names, key=lambda x: int(x.split('_')[-1]))
        assert len(extra_f_names) == 3 * (self.max_sh_degree + 1) ** 2 - 3
        features_extra = np.zeros((xyz.shape[0], len(extra_f_names)))
        for idx, attr_name in enumerate(extra_f_names):
            features_extra[:, idx] = np.asarray(plydata.elements[0][attr_name])
        features_extra = features_extra.reshape((features_extra.shape[0], 3, (self.max_sh_degree + 1) ** 2 - 1))
        scale_names = [p.name for p in plydata.elements[0].properties if p.name.startswith('scale_')]
        scale_names = sorted(scale_names, key=lambda x: int(x.split('_')[-1]))
        scales = np.zeros((xyz.shape[0], len(scale_names)))
        for idx, attr_name in enumerate(scale_names):
            scales[:, idx] = np.asarray(plydata.elements[0][attr_name])
        rot_names = [p.name for p in plydata.elements[0].properties if p.name.startswith('rot')]
        rot_names = sorted(rot_names, key=lambda x: int(x.split('_')[-1]))
        rots = np.zeros((xyz.shape[0], len(rot_names)))
        for idx, attr_name in enumerate(rot_names):
            rots[:, idx] = np.asarray(plydata.elements[0][attr_name])
        self._xyz = nn.Parameter(torch.tensor(xyz, dtype=torch.float, device='cuda').requires_grad_(True))
        self._features_dc = nn.Parameter(torch.tensor(features_dc, dtype=torch.float, device='cuda').transpose(1, 2).contiguous().requires_grad_(True))
        self._features_rest = nn.Parameter(torch.tensor(features_extra, dtype=torch.float, device='cuda').transpose(1, 2).contiguous().requires_grad_(True))
        self._opacity = nn.Parameter(torch.tensor(opacities, dtype=torch.float, device='cuda').requires_grad_(True))
        self._scaling = nn.Parameter(torch.tensor(scales, dtype=torch.float, device='cuda').requires_grad_(True))
        self._rotation = nn.Parameter(torch.tensor(rots, dtype=torch.float, device='cuda').requires_grad_(True))
        self.active_sh_degree = self.max_sh_degree

    def replace_tensor_to_optimizer(self, tensor, name):
        optimizable_tensors = {}
        for group in self.optimizer.param_groups:
            if group['name'] == name:
                stored_state = self.optimizer.state.get(group['params'][0], None)
                stored_state['exp_avg'] = torch.zeros_like(tensor)
                stored_state['exp_avg_sq'] = torch.zeros_like(tensor)
                del self.optimizer.state[group['params'][0]]
                group['params'][0] = nn.Parameter(tensor.requires_grad_(True))
                self.optimizer.state[group['params'][0]] = stored_state
                optimizable_tensors[group['name']] = group['params'][0]
        return optimizable_tensors

    def _prune_optimizer(self, mask):
        optimizable_tensors = {}
        for group in self.optimizer.param_groups:
            if 'sky_model' in group['name']:
                continue
            stored_state = self.optimizer.state.get(group['params'][0], None)
            if stored_state is not None:
                stored_state['exp_avg'] = stored_state['exp_avg'][mask]
                stored_state['exp_avg_sq'] = stored_state['exp_avg_sq'][mask]
                del self.optimizer.state[group['params'][0]]
                group['params'][0] = nn.Parameter(group['params'][0][mask].requires_grad_(True))
                self.optimizer.state[group['params'][0]] = stored_state
                optimizable_tensors[group['name']] = group['params'][0]
            else:
                group['params'][0] = nn.Parameter(group['params'][0][mask].requires_grad_(True))
                optimizable_tensors[group['name']] = group['params'][0]
        return optimizable_tensors

    def prune_points(self, mask):
        valid_points_mask = ~mask
        optimizable_tensors = self._prune_optimizer(valid_points_mask)
        self._xyz = optimizable_tensors['xyz']
        self._features_dc = optimizable_tensors['f_dc']
        self._features_rest = optimizable_tensors['f_rest']
        self._opacity = optimizable_tensors['opacity']
        self._scaling = optimizable_tensors['scaling']
        self._rotation = optimizable_tensors['rotation']
        self.xyz_gradient_accum = self.xyz_gradient_accum[valid_points_mask]
        self.denom = self.denom[valid_points_mask]
        self.max_radii2D = self.max_radii2D[valid_points_mask]

    def cat_tensors_to_optimizer(self, tensors_dict):
        optimizable_tensors = {}
        for group in self.optimizer.param_groups:
            if 'sky_model' in group['name']:
                continue
            assert len(group['params']) == 1
            extension_tensor = tensors_dict[group['name']]
            stored_state = self.optimizer.state.get(group['params'][0], None)
            if stored_state is not None:
                stored_state['exp_avg'] = torch.cat((stored_state['exp_avg'], torch.zeros_like(extension_tensor)), dim=0)
                stored_state['exp_avg_sq'] = torch.cat((stored_state['exp_avg_sq'], torch.zeros_like(extension_tensor)), dim=0)
                del self.optimizer.state[group['params'][0]]
                group['params'][0] = nn.Parameter(torch.cat((group['params'][0], extension_tensor), dim=0).requires_grad_(True))
                self.optimizer.state[group['params'][0]] = stored_state
                optimizable_tensors[group['name']] = group['params'][0]
            else:
                group['params'][0] = nn.Parameter(torch.cat((group['params'][0], extension_tensor), dim=0).requires_grad_(True))
                optimizable_tensors[group['name']] = group['params'][0]
        return optimizable_tensors

    def densification_postfix(self, new_xyz, new_features_dc, new_features_rest, new_opacities, new_scaling, new_rotation):
        d = {'xyz': new_xyz, 'f_dc': new_features_dc, 'f_rest': new_features_rest, 'opacity': new_opacities, 'scaling': new_scaling, 'rotation': new_rotation}
        optimizable_tensors = self.cat_tensors_to_optimizer(d)
        self._xyz = optimizable_tensors['xyz']
        self._features_dc = optimizable_tensors['f_dc']
        self._features_rest = optimizable_tensors['f_rest']
        self._opacity = optimizable_tensors['opacity']
        self._scaling = optimizable_tensors['scaling']
        self._rotation = optimizable_tensors['rotation']
        self.xyz_gradient_accum = torch.zeros((self.get_xyz.shape[0], 1), device='cuda')
        self.denom = torch.zeros((self.get_xyz.shape[0], 1), device='cuda')
        self.max_radii2D = torch.zeros(self.get_xyz.shape[0], device='cuda')

    def densify_and_split(self, grads, grad_threshold, scene_extent, N=2):
        n_init_points = self.get_xyz.shape[0]
        padded_grad = torch.zeros(n_init_points, device='cuda')
        padded_grad[:grads.shape[0]] = grads.squeeze()
        selected_pts_mask = torch.where(padded_grad >= grad_threshold, True, False)
        selected_pts_mask = torch.logical_and(selected_pts_mask, torch.max(self.get_scaling, dim=1).values > self.percent_dense * scene_extent)
        stds = self.get_scaling[selected_pts_mask].repeat(N, 1)
        means = torch.zeros((stds.size(0), 3), device='cuda')
        samples = torch.normal(mean=means, std=stds)
        rots = build_rotation(self._rotation[selected_pts_mask]).repeat(N, 1, 1)
        new_xyz = torch.bmm(rots, samples.unsqueeze(-1)).squeeze(-1) + self.get_xyz[selected_pts_mask].repeat(N, 1)
        new_scaling = self.scaling_inverse_activation(self.get_scaling[selected_pts_mask].repeat(N, 1) / (0.8 * N))
        new_rotation = self._rotation[selected_pts_mask].repeat(N, 1)
        new_features_dc = self._features_dc[selected_pts_mask].repeat(N, 1, 1)
        new_features_rest = self._features_rest[selected_pts_mask].repeat(N, 1, 1)
        new_opacity = self._opacity[selected_pts_mask].repeat(N, 1)
        self.densification_postfix(new_xyz, new_features_dc, new_features_rest, new_opacity, new_scaling, new_rotation)
        prune_filter = torch.cat((selected_pts_mask, torch.zeros(N * selected_pts_mask.sum(), device='cuda', dtype=bool)))
        self.prune_points(prune_filter)

    def densify_and_clone(self, grads, grad_threshold, scene_extent):
        selected_pts_mask = torch.where(torch.norm(grads, dim=-1) >= grad_threshold, True, False)
        selected_pts_mask = torch.logical_and(selected_pts_mask, torch.max(self.get_scaling, dim=1).values <= self.percent_dense * scene_extent)
        new_xyz = self._xyz[selected_pts_mask]
        new_features_dc = self._features_dc[selected_pts_mask]
        new_features_rest = self._features_rest[selected_pts_mask]
        new_opacities = self._opacity[selected_pts_mask]
        new_scaling = self._scaling[selected_pts_mask]
        new_rotation = self._rotation[selected_pts_mask]
        self.densification_postfix(new_xyz, new_features_dc, new_features_rest, new_opacities, new_scaling, new_rotation)

    def densify_and_prune(self, max_grad, min_opacity, extent, max_screen_size):
        grads = self.xyz_gradient_accum / self.denom
        grads[grads.isnan()] = 0.0
        self.densify_and_clone(grads, max_grad, extent)
        self.densify_and_split(grads, max_grad, extent)
        prune_mask = (self.get_opacity < min_opacity).squeeze()
        if max_screen_size:
            big_points_vs = self.max_radii2D > max_screen_size
            big_points_ws = self.get_scaling.max(dim=1).values > 0.1 * extent
            prune_mask = torch.logical_or(torch.logical_or(prune_mask, big_points_vs), big_points_ws)
        self.prune_points(prune_mask)
        torch.cuda.empty_cache()

    def add_densification_stats(self, viewspace_point_tensor, update_filter, width, height):
        grad = viewspace_point_tensor.grad.squeeze(0)
        grad[:, 0] *= width * 0.5
        grad[:, 1] *= height * 0.5
        self.xyz_gradient_accum[update_filter] += torch.norm(grad[update_filter, :2], dim=-1, keepdim=True)
        self.denom[update_filter] += 1

    def get_sky_bg(self, viewpoint_camera):
        return self.sky_model(viewpoint_camera)

def save_ply(self, path):
    mkdir_p(os.path.dirname(path))
    xyz = self._xyz.detach().cpu().numpy()
    normals = np.zeros_like(xyz)
    f_dc = self._features_dc.detach().transpose(1, 2).flatten(start_dim=1).contiguous().cpu().numpy()
    f_rest = self._features_rest.detach().transpose(1, 2).flatten(start_dim=1).contiguous().cpu().numpy()
    opacities = self._opacity.detach().cpu().numpy()
    scale = self._scaling.detach().cpu().numpy()
    rotation = self._rotation.detach().cpu().numpy()
    dtype_full = [(attribute, 'f4') for attribute in self.construct_list_of_attributes()]
    elements = np.empty(xyz.shape[0], dtype=dtype_full)
    attributes = np.concatenate((xyz, normals, f_dc, f_rest, opacities, scale, rotation), axis=1)
    elements[:] = list(map(tuple, attributes))
    el = PlyElement.describe(elements, 'vertex')
    PlyData([el]).write(path)

class ParamGroup:

    def __init__(self, parser: ArgumentParser, name: str, fill_none=False):
        group = parser.add_argument_group(name)
        for key, value in vars(self).items():
            shorthand = False
            if key.startswith('_'):
                shorthand = True
                key = key[1:]
            t = type(value)
            value = value if not fill_none else None
            if shorthand:
                if t == bool:
                    group.add_argument('--' + key, '-' + key[0:1], default=value, action='store_true')
                else:
                    group.add_argument('--' + key, '-' + key[0:1], default=value, type=t)
            elif t == bool:
                group.add_argument('--' + key, default=value, action='store_true')
            else:
                group.add_argument('--' + key, default=value, type=t)

    def extract(self, args):
        group = GroupParams()
        for arg in vars(args).items():
            if arg[0] in vars(self) or '_' + arg[0] in vars(self):
                setattr(group, arg[0], arg[1])
        return group

def __init__(self, parser: ArgumentParser, name: str, fill_none=False):
    group = parser.add_argument_group(name)
    for key, value in vars(self).items():
        shorthand = False
        if key.startswith('_'):
            shorthand = True
            key = key[1:]
        t = type(value)
        value = value if not fill_none else None
        if shorthand:
            if t == bool:
                group.add_argument('--' + key, '-' + key[0:1], default=value, action='store_true')
            else:
                group.add_argument('--' + key, '-' + key[0:1], default=value, type=t)
        elif t == bool:
            group.add_argument('--' + key, default=value, action='store_true')
        else:
            group.add_argument('--' + key, default=value, type=t)

def extract(self, args):
    group = GroupParams()
    for arg in vars(args).items():
        if arg[0] in vars(self) or '_' + arg[0] in vars(self):
            setattr(group, arg[0], arg[1])
    return group

class BaseNetwork(nn.Module):

    def __init__(self):
        super(BaseNetwork, self).__init__()

    def print_network(self):
        if isinstance(self, list):
            self = self[0]
        num_params = 0
        for param in self.parameters():
            num_params += param.numel()
        print('Network [%s] was created. Total number of parameters: %.1f million. To see the architecture, do print(network).' % (type(self).__name__, num_params / 1000000))

    def init_weights(self, init_type='normal', gain=0.02):
        """
        initialize network's weights
        init_type: normal | xavier | kaiming | orthogonal
        https://github.com/junyanz/pytorch-CycleGAN-and-pix2pix/blob/9451e70673400885567d08a9e97ade2524c700d0/models/networks.py#L39
        """

        def init_func(m):
            classname = m.__class__.__name__
            if classname.find('InstanceNorm2d') != -1:
                if hasattr(m, 'weight') and m.weight is not None:
                    nn.init.constant_(m.weight.data, 1.0)
                if hasattr(m, 'bias') and m.bias is not None:
                    nn.init.constant_(m.bias.data, 0.0)
            elif hasattr(m, 'weight') and (classname.find('Conv') != -1 or classname.find('Linear') != -1):
                if init_type == 'normal':
                    nn.init.normal_(m.weight.data, 0.0, gain)
                elif init_type == 'xavier':
                    nn.init.xavier_normal_(m.weight.data, gain=gain)
                elif init_type == 'xavier_uniform':
                    nn.init.xavier_uniform_(m.weight.data, gain=1.0)
                elif init_type == 'kaiming':
                    nn.init.kaiming_normal_(m.weight.data, a=0, mode='fan_in')
                elif init_type == 'orthogonal':
                    nn.init.orthogonal_(m.weight.data, gain=gain)
                elif init_type == 'none':
                    m.reset_parameters()
                else:
                    raise NotImplementedError('initialization method [%s] is not implemented' % init_type)
                if hasattr(m, 'bias') and m.bias is not None:
                    nn.init.constant_(m.bias.data, 0.0)
        self.apply(init_func)
        for m in self.children():
            if hasattr(m, 'init_weights'):
                m.init_weights(init_type, gain)

def print_network(self):
    if isinstance(self, list):
        self = self[0]
    num_params = 0
    for param in self.parameters():
        num_params += param.numel()
    print('Network [%s] was created. Total number of parameters: %.1f million. To see the architecture, do print(network).' % (type(self).__name__, num_params / 1000000))

class BaseNetwork(nn.Module):

    def __init__(self):
        super(BaseNetwork, self).__init__()

    def print_network(self):
        if isinstance(self, list):
            self = self[0]
        num_params = 0
        for param in self.parameters():
            num_params += param.numel()
        print('Network [%s] was created. Total number of parameters: %.1f million. To see the architecture, do print(network).' % (type(self).__name__, num_params / 1000000))

    def init_weights(self, init_type='normal', gain=0.02):
        """
        initialize network's weights
        init_type: normal | xavier | kaiming | orthogonal
        https://github.com/junyanz/pytorch-CycleGAN-and-pix2pix/blob/9451e70673400885567d08a9e97ade2524c700d0/models/networks.py#L39
        """

        def init_func(m):
            classname = m.__class__.__name__
            if classname.find('InstanceNorm2d') != -1:
                if hasattr(m, 'weight') and m.weight is not None:
                    nn.init.constant_(m.weight.data, 1.0)
                if hasattr(m, 'bias') and m.bias is not None:
                    nn.init.constant_(m.bias.data, 0.0)
            elif hasattr(m, 'weight') and (classname.find('Conv') != -1 or classname.find('Linear') != -1):
                if init_type == 'normal':
                    nn.init.normal_(m.weight.data, 0.0, gain)
                elif init_type == 'xavier':
                    nn.init.xavier_normal_(m.weight.data, gain=gain)
                elif init_type == 'xavier_uniform':
                    nn.init.xavier_uniform_(m.weight.data, gain=1.0)
                elif init_type == 'kaiming':
                    nn.init.kaiming_normal_(m.weight.data, a=0, mode='fan_in')
                elif init_type == 'orthogonal':
                    nn.init.orthogonal_(m.weight.data, gain=gain)
                elif init_type == 'none':
                    m.reset_parameters()
                else:
                    raise NotImplementedError('initialization method [%s] is not implemented' % init_type)
                if hasattr(m, 'bias') and m.bias is not None:
                    nn.init.constant_(m.bias.data, 0.0)
        self.apply(init_func)
        for m in self.children():
            if hasattr(m, 'init_weights'):
                m.init_weights(init_type, gain)

def print_network(self):
    if isinstance(self, list):
        self = self[0]
    num_params = 0
    for param in self.parameters():
        num_params += param.numel()
    print('Network [%s] was created. Total number of parameters: %.1f million. To see the architecture, do print(network).' % (type(self).__name__, num_params / 1000000))

class SpectralNorm(object):
    _version = 1

    def __init__(self, name='weight', n_power_iterations=1, dim=0, eps=1e-12):
        self.name = name
        self.dim = dim
        if n_power_iterations <= 0:
            raise ValueError('Expected n_power_iterations to be positive, but got n_power_iterations={}'.format(n_power_iterations))
        self.n_power_iterations = n_power_iterations
        self.eps = eps

    def reshape_weight_to_matrix(self, weight):
        weight_mat = weight
        if self.dim != 0:
            weight_mat = weight_mat.permute(self.dim, *[d for d in range(weight_mat.dim()) if d != self.dim])
        height = weight_mat.size(0)
        return weight_mat.reshape(height, -1)

    def compute_weight(self, module, do_power_iteration):
        weight = getattr(module, self.name + '_orig')
        u = getattr(module, self.name + '_u')
        v = getattr(module, self.name + '_v')
        weight_mat = self.reshape_weight_to_matrix(weight)
        if do_power_iteration:
            with torch.no_grad():
                for _ in range(self.n_power_iterations):
                    v = normalize(torch.mv(weight_mat.t(), u), dim=0, eps=self.eps, out=v)
                    u = normalize(torch.mv(weight_mat, v), dim=0, eps=self.eps, out=u)
                if self.n_power_iterations > 0:
                    u = u.clone()
                    v = v.clone()
        sigma = torch.dot(u, torch.mv(weight_mat, v))
        weight = weight / sigma
        return weight

    def remove(self, module):
        with torch.no_grad():
            weight = self.compute_weight(module, do_power_iteration=False)
        delattr(module, self.name)
        delattr(module, self.name + '_u')
        delattr(module, self.name + '_v')
        delattr(module, self.name + '_orig')
        module.register_parameter(self.name, torch.nn.Parameter(weight.detach()))

    def __call__(self, module, inputs):
        setattr(module, self.name, self.compute_weight(module, do_power_iteration=module.training))

    def _solve_v_and_rescale(self, weight_mat, u, target_sigma):
        v = torch.chain_matmul(weight_mat.t().mm(weight_mat).pinverse(), weight_mat.t(), u.unsqueeze(1)).squeeze(1)
        return v.mul_(target_sigma / torch.dot(u, torch.mv(weight_mat, v)))

    @staticmethod
    def apply(module, name, n_power_iterations, dim, eps):
        for k, hook in module._forward_pre_hooks.items():
            if isinstance(hook, SpectralNorm) and hook.name == name:
                raise RuntimeError('Cannot register two spectral_norm hooks on the same parameter {}'.format(name))
        fn = SpectralNorm(name, n_power_iterations, dim, eps)
        weight = module._parameters[name]
        with torch.no_grad():
            weight_mat = fn.reshape_weight_to_matrix(weight)
            h, w = weight_mat.size()
            u = normalize(weight.new_empty(h).normal_(0, 1), dim=0, eps=fn.eps)
            v = normalize(weight.new_empty(w).normal_(0, 1), dim=0, eps=fn.eps)
        delattr(module, fn.name)
        module.register_parameter(fn.name + '_orig', weight)
        setattr(module, fn.name, weight.data)
        module.register_buffer(fn.name + '_u', u)
        module.register_buffer(fn.name + '_v', v)
        module.register_forward_pre_hook(fn)
        module._register_state_dict_hook(SpectralNormStateDictHook(fn))
        module._register_load_state_dict_pre_hook(SpectralNormLoadStateDictPreHook(fn))
        return fn

def remove(self, module):
    with torch.no_grad():
        weight = self.compute_weight(module, do_power_iteration=False)
    delattr(module, self.name)
    delattr(module, self.name + '_u')
    delattr(module, self.name + '_v')
    delattr(module, self.name + '_orig')
    module.register_parameter(self.name, torch.nn.Parameter(weight.detach()))

def __call__(self, module, inputs):
    setattr(module, self.name, self.compute_weight(module, do_power_iteration=module.training))

@staticmethod
def apply(module, name, n_power_iterations, dim, eps):
    for k, hook in module._forward_pre_hooks.items():
        if isinstance(hook, SpectralNorm) and hook.name == name:
            raise RuntimeError('Cannot register two spectral_norm hooks on the same parameter {}'.format(name))
    fn = SpectralNorm(name, n_power_iterations, dim, eps)
    weight = module._parameters[name]
    with torch.no_grad():
        weight_mat = fn.reshape_weight_to_matrix(weight)
        h, w = weight_mat.size()
        u = normalize(weight.new_empty(h).normal_(0, 1), dim=0, eps=fn.eps)
        v = normalize(weight.new_empty(w).normal_(0, 1), dim=0, eps=fn.eps)
    delattr(module, fn.name)
    module.register_parameter(fn.name + '_orig', weight)
    setattr(module, fn.name, weight.data)
    module.register_buffer(fn.name + '_u', u)
    module.register_buffer(fn.name + '_v', v)
    module.register_forward_pre_hook(fn)
    module._register_state_dict_hook(SpectralNormStateDictHook(fn))
    module._register_load_state_dict_pre_hook(SpectralNormLoadStateDictPreHook(fn))
    return fn

class SpectralNormStateDictHook(object):

    def __init__(self, fn):
        self.fn = fn

    def __call__(self, module, state_dict, prefix, local_metadata):
        if 'spectral_norm' not in local_metadata:
            local_metadata['spectral_norm'] = {}
        key = self.fn.name + '.version'
        if key in local_metadata['spectral_norm']:
            raise RuntimeError("Unexpected key in metadata['spectral_norm']: {}".format(key))
        local_metadata['spectral_norm'][key] = self.fn._version

def __call__(self, module, state_dict, prefix, local_metadata):
    if 'spectral_norm' not in local_metadata:
        local_metadata['spectral_norm'] = {}
    key = self.fn.name + '.version'
    if key in local_metadata['spectral_norm']:
        raise RuntimeError("Unexpected key in metadata['spectral_norm']: {}".format(key))
    local_metadata['spectral_norm'][key] = self.fn._version

def to_numpy(tensor):
    return tensor.cpu().numpy()

def get_amg_kwargs(args):
    amg_kwargs = {'points_per_side': args.points_per_side, 'points_per_batch': args.points_per_batch, 'pred_iou_thresh': args.pred_iou_thresh, 'stability_score_thresh': args.stability_score_thresh, 'stability_score_offset': args.stability_score_offset, 'box_nms_thresh': args.box_nms_thresh, 'crop_n_layers': args.crop_n_layers, 'crop_nms_thresh': args.crop_nms_thresh, 'crop_overlap_ratio': args.crop_overlap_ratio, 'crop_n_points_downscale_factor': args.crop_n_points_downscale_factor, 'min_mask_region_area': args.min_mask_region_area}
    amg_kwargs = {k: v for k, v in amg_kwargs.items() if v is not None}
    return amg_kwargs

class SamPredictor:

    def __init__(self, sam_model: Sam) -> None:
        """
        Uses SAM to calculate the image embedding for an image, and then
        allow repeated, efficient mask prediction given prompts.

        Arguments:
          sam_model (Sam): The model to use for mask prediction.
        """
        super().__init__()
        self.model = sam_model
        self.transform = ResizeLongestSide(sam_model.image_encoder.img_size)
        self.reset_image()

    def set_image(self, image: np.ndarray, image_format: str='RGB') -> None:
        """
        Calculates the image embeddings for the provided image, allowing
        masks to be predicted with the 'predict' method.

        Arguments:
          image (np.ndarray): The image for calculating masks. Expects an
            image in HWC uint8 format, with pixel values in [0, 255].
          image_format (str): The color format of the image, in ['RGB', 'BGR'].
        """
        assert image_format in ['RGB', 'BGR'], f"image_format must be in ['RGB', 'BGR'], is {image_format}."
        if image_format != self.model.image_format:
            image = image[..., ::-1]
        input_image = self.transform.apply_image(image)
        input_image_torch = torch.as_tensor(input_image, device=self.device)
        input_image_torch = input_image_torch.permute(2, 0, 1).contiguous()[None, :, :, :]
        self.set_torch_image(input_image_torch, image.shape[:2])

    @torch.no_grad()
    def set_torch_image(self, transformed_image: torch.Tensor, original_image_size: Tuple[int, ...]) -> None:
        """
        Calculates the image embeddings for the provided image, allowing
        masks to be predicted with the 'predict' method. Expects the input
        image to be already transformed to the format expected by the model.

        Arguments:
          transformed_image (torch.Tensor): The input image, with shape
            1x3xHxW, which has been transformed with ResizeLongestSide.
          original_image_size (tuple(int, int)): The size of the image
            before transformation, in (H, W) format.
        """
        assert len(transformed_image.shape) == 4 and transformed_image.shape[1] == 3 and (max(*transformed_image.shape[2:]) == self.model.image_encoder.img_size), f'set_torch_image input must be BCHW with long side {self.model.image_encoder.img_size}.'
        self.reset_image()
        self.original_size = original_image_size
        self.input_size = tuple(transformed_image.shape[-2:])
        input_image = self.model.preprocess(transformed_image)
        self.features = self.model.image_encoder(input_image)
        self.is_image_set = True

    def predict(self, point_coords: Optional[np.ndarray]=None, point_labels: Optional[np.ndarray]=None, box: Optional[np.ndarray]=None, mask_input: Optional[np.ndarray]=None, multimask_output: bool=True, return_logits: bool=False) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Predict masks for the given input prompts, using the currently set image.

        Arguments:
          point_coords (np.ndarray or None): A Nx2 array of point prompts to the
            model. Each point is in (X,Y) in pixels.
          point_labels (np.ndarray or None): A length N array of labels for the
            point prompts. 1 indicates a foreground point and 0 indicates a
            background point.
          box (np.ndarray or None): A length 4 array given a box prompt to the
            model, in XYXY format.
          mask_input (np.ndarray): A low resolution mask input to the model, typically
            coming from a previous prediction iteration. Has form 1xHxW, where
            for SAM, H=W=256.
          multimask_output (bool): If true, the model will return three masks.
            For ambiguous input prompts (such as a single click), this will often
            produce better masks than a single prediction. If only a single
            mask is needed, the model's predicted quality score can be used
            to select the best mask. For non-ambiguous prompts, such as multiple
            input prompts, multimask_output=False can give better results.
          return_logits (bool): If true, returns un-thresholded masks logits
            instead of a binary mask.

        Returns:
          (np.ndarray): The output masks in CxHxW format, where C is the
            number of masks, and (H, W) is the original image size.
          (np.ndarray): An array of length C containing the model's
            predictions for the quality of each mask.
          (np.ndarray): An array of shape CxHxW, where C is the number
            of masks and H=W=256. These low resolution logits can be passed to
            a subsequent iteration as mask input.
        """
        if not self.is_image_set:
            raise RuntimeError('An image must be set with .set_image(...) before mask prediction.')
        coords_torch, labels_torch, box_torch, mask_input_torch = (None, None, None, None)
        if point_coords is not None:
            assert point_labels is not None, 'point_labels must be supplied if point_coords is supplied.'
            point_coords = self.transform.apply_coords(point_coords, self.original_size)
            coords_torch = torch.as_tensor(point_coords, dtype=torch.float, device=self.device)
            labels_torch = torch.as_tensor(point_labels, dtype=torch.int, device=self.device)
            coords_torch, labels_torch = (coords_torch[None, :, :], labels_torch[None, :])
        if box is not None:
            box = self.transform.apply_boxes(box, self.original_size)
            box_torch = torch.as_tensor(box, dtype=torch.float, device=self.device)
            box_torch = box_torch[None, :]
        if mask_input is not None:
            mask_input_torch = torch.as_tensor(mask_input, dtype=torch.float, device=self.device)
            mask_input_torch = mask_input_torch[None, :, :, :]
        masks, iou_predictions, low_res_masks = self.predict_torch(coords_torch, labels_torch, box_torch, mask_input_torch, multimask_output, return_logits=return_logits)
        masks = masks[0].detach().cpu().numpy()
        iou_predictions = iou_predictions[0].detach().cpu().numpy()
        low_res_masks = low_res_masks[0].detach().cpu().numpy()
        return (masks, iou_predictions, low_res_masks)

    @torch.no_grad()
    def predict_torch(self, point_coords: Optional[torch.Tensor], point_labels: Optional[torch.Tensor], boxes: Optional[torch.Tensor]=None, mask_input: Optional[torch.Tensor]=None, multimask_output: bool=True, return_logits: bool=False) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Predict masks for the given input prompts, using the currently set image.
        Input prompts are batched torch tensors and are expected to already be
        transformed to the input frame using ResizeLongestSide.

        Arguments:
          point_coords (torch.Tensor or None): A BxNx2 array of point prompts to the
            model. Each point is in (X,Y) in pixels.
          point_labels (torch.Tensor or None): A BxN array of labels for the
            point prompts. 1 indicates a foreground point and 0 indicates a
            background point.
          box (np.ndarray or None): A Bx4 array given a box prompt to the
            model, in XYXY format.
          mask_input (np.ndarray): A low resolution mask input to the model, typically
            coming from a previous prediction iteration. Has form Bx1xHxW, where
            for SAM, H=W=256. Masks returned by a previous iteration of the
            predict method do not need further transformation.
          multimask_output (bool): If true, the model will return three masks.
            For ambiguous input prompts (such as a single click), this will often
            produce better masks than a single prediction. If only a single
            mask is needed, the model's predicted quality score can be used
            to select the best mask. For non-ambiguous prompts, such as multiple
            input prompts, multimask_output=False can give better results.
          return_logits (bool): If true, returns un-thresholded masks logits
            instead of a binary mask.

        Returns:
          (torch.Tensor): The output masks in BxCxHxW format, where C is the
            number of masks, and (H, W) is the original image size.
          (torch.Tensor): An array of shape BxC containing the model's
            predictions for the quality of each mask.
          (torch.Tensor): An array of shape BxCxHxW, where C is the number
            of masks and H=W=256. These low res logits can be passed to
            a subsequent iteration as mask input.
        """
        if not self.is_image_set:
            raise RuntimeError('An image must be set with .set_image(...) before mask prediction.')
        if point_coords is not None:
            points = (point_coords, point_labels)
        else:
            points = None
        sparse_embeddings, dense_embeddings = self.model.prompt_encoder(points=points, boxes=boxes, masks=mask_input)
        low_res_masks, iou_predictions = self.model.mask_decoder(image_embeddings=self.features, image_pe=self.model.prompt_encoder.get_dense_pe(), sparse_prompt_embeddings=sparse_embeddings, dense_prompt_embeddings=dense_embeddings, multimask_output=multimask_output)
        masks = self.model.postprocess_masks(low_res_masks, self.input_size, self.original_size)
        if not return_logits:
            masks = masks > self.model.mask_threshold
        return (masks, iou_predictions, low_res_masks)

    def get_image_embedding(self) -> torch.Tensor:
        """
        Returns the image embeddings for the currently set image, with
        shape 1xCxHxW, where C is the embedding dimension and (H,W) are
        the embedding spatial dimension of SAM (typically C=256, H=W=64).
        """
        if not self.is_image_set:
            raise RuntimeError('An image must be set with .set_image(...) to generate an embedding.')
        assert self.features is not None, 'Features must exist if an image has been set.'
        return self.features

    @property
    def device(self) -> torch.device:
        return self.model.device

    def reset_image(self) -> None:
        """Resets the currently set image."""
        self.is_image_set = False
        self.features = None
        self.orig_h = None
        self.orig_w = None
        self.input_h = None
        self.input_w = None

def predict(self, point_coords: Optional[np.ndarray]=None, point_labels: Optional[np.ndarray]=None, box: Optional[np.ndarray]=None, mask_input: Optional[np.ndarray]=None, multimask_output: bool=True, return_logits: bool=False) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """
        Predict masks for the given input prompts, using the currently set image.

        Arguments:
          point_coords (np.ndarray or None): A Nx2 array of point prompts to the
            model. Each point is in (X,Y) in pixels.
          point_labels (np.ndarray or None): A length N array of labels for the
            point prompts. 1 indicates a foreground point and 0 indicates a
            background point.
          box (np.ndarray or None): A length 4 array given a box prompt to the
            model, in XYXY format.
          mask_input (np.ndarray): A low resolution mask input to the model, typically
            coming from a previous prediction iteration. Has form 1xHxW, where
            for SAM, H=W=256.
          multimask_output (bool): If true, the model will return three masks.
            For ambiguous input prompts (such as a single click), this will often
            produce better masks than a single prediction. If only a single
            mask is needed, the model's predicted quality score can be used
            to select the best mask. For non-ambiguous prompts, such as multiple
            input prompts, multimask_output=False can give better results.
          return_logits (bool): If true, returns un-thresholded masks logits
            instead of a binary mask.

        Returns:
          (np.ndarray): The output masks in CxHxW format, where C is the
            number of masks, and (H, W) is the original image size.
          (np.ndarray): An array of length C containing the model's
            predictions for the quality of each mask.
          (np.ndarray): An array of shape CxHxW, where C is the number
            of masks and H=W=256. These low resolution logits can be passed to
            a subsequent iteration as mask input.
        """
    if not self.is_image_set:
        raise RuntimeError('An image must be set with .set_image(...) before mask prediction.')
    coords_torch, labels_torch, box_torch, mask_input_torch = (None, None, None, None)
    if point_coords is not None:
        assert point_labels is not None, 'point_labels must be supplied if point_coords is supplied.'
        point_coords = self.transform.apply_coords(point_coords, self.original_size)
        coords_torch = torch.as_tensor(point_coords, dtype=torch.float, device=self.device)
        labels_torch = torch.as_tensor(point_labels, dtype=torch.int, device=self.device)
        coords_torch, labels_torch = (coords_torch[None, :, :], labels_torch[None, :])
    if box is not None:
        box = self.transform.apply_boxes(box, self.original_size)
        box_torch = torch.as_tensor(box, dtype=torch.float, device=self.device)
        box_torch = box_torch[None, :]
    if mask_input is not None:
        mask_input_torch = torch.as_tensor(mask_input, dtype=torch.float, device=self.device)
        mask_input_torch = mask_input_torch[None, :, :, :]
    masks, iou_predictions, low_res_masks = self.predict_torch(coords_torch, labels_torch, box_torch, mask_input_torch, multimask_output, return_logits=return_logits)
    masks = masks[0].detach().cpu().numpy()
    iou_predictions = iou_predictions[0].detach().cpu().numpy()
    low_res_masks = low_res_masks[0].detach().cpu().numpy()
    return (masks, iou_predictions, low_res_masks)

def get_image_embedding(self) -> torch.Tensor:
    """
        Returns the image embeddings for the currently set image, with
        shape 1xCxHxW, where C is the embedding dimension and (H,W) are
        the embedding spatial dimension of SAM (typically C=256, H=W=64).
        """
    if not self.is_image_set:
        raise RuntimeError('An image must be set with .set_image(...) to generate an embedding.')
    assert self.features is not None, 'Features must exist if an image has been set.'
    return self.features

class LayerNorm2d(nn.Module):

    def __init__(self, num_channels: int, eps: float=1e-06) -> None:
        super().__init__()
        self.weight = nn.Parameter(torch.ones(num_channels))
        self.bias = nn.Parameter(torch.zeros(num_channels))
        self.eps = eps

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        u = x.mean(1, keepdim=True)
        s = (x - u).pow(2).mean(1, keepdim=True)
        x = (x - u) / torch.sqrt(s + self.eps)
        x = self.weight[:, None, None] * x + self.bias[:, None, None]
        return x

def forward(self, x: torch.Tensor) -> torch.Tensor:
    u = x.mean(1, keepdim=True)
    s = (x - u).pow(2).mean(1, keepdim=True)
    x = (x - u) / torch.sqrt(s + self.eps)
    x = self.weight[:, None, None] * x + self.bias[:, None, None]
    return x

class LayerNorm2d(nn.Module):

    def __init__(self, num_channels: int, eps: float=1e-06) -> None:
        super().__init__()
        self.weight = nn.Parameter(torch.ones(num_channels))
        self.bias = nn.Parameter(torch.zeros(num_channels))
        self.eps = eps

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        u = x.mean(1, keepdim=True)
        s = (x - u).pow(2).mean(1, keepdim=True)
        x = (x - u) / torch.sqrt(s + self.eps)
        x = self.weight[:, None, None] * x + self.bias[:, None, None]
        return x

def forward(self, x: torch.Tensor) -> torch.Tensor:
    u = x.mean(1, keepdim=True)
    s = (x - u).pow(2).mean(1, keepdim=True)
    x = (x - u) / torch.sqrt(s + self.eps)
    x = self.weight[:, None, None] * x + self.bias[:, None, None]
    return x

class MaskData:
    """
    A structure for storing masks and their related data in batched format.
    Implements basic filtering and concatenation.
    """

    def __init__(self, **kwargs) -> None:
        for v in kwargs.values():
            assert isinstance(v, (list, np.ndarray, torch.Tensor)), 'MaskData only supports list, numpy arrays, and torch tensors.'
        self._stats = dict(**kwargs)

    def __setitem__(self, key: str, item: Any) -> None:
        assert isinstance(item, (list, np.ndarray, torch.Tensor)), 'MaskData only supports list, numpy arrays, and torch tensors.'
        self._stats[key] = item

    def __delitem__(self, key: str) -> None:
        del self._stats[key]

    def __getitem__(self, key: str) -> Any:
        return self._stats[key]

    def items(self) -> ItemsView[str, Any]:
        return self._stats.items()

    def filter(self, keep: torch.Tensor) -> None:
        for k, v in self._stats.items():
            if v is None:
                self._stats[k] = None
            elif isinstance(v, torch.Tensor):
                self._stats[k] = v[torch.as_tensor(keep, device=v.device)]
            elif isinstance(v, np.ndarray):
                self._stats[k] = v[keep.detach().cpu().numpy()]
            elif isinstance(v, list) and keep.dtype == torch.bool:
                self._stats[k] = [a for i, a in enumerate(v) if keep[i]]
            elif isinstance(v, list):
                self._stats[k] = [v[i] for i in keep]
            else:
                raise TypeError(f'MaskData key {k} has an unsupported type {type(v)}.')

    def cat(self, new_stats: 'MaskData') -> None:
        for k, v in new_stats.items():
            if k not in self._stats or self._stats[k] is None:
                self._stats[k] = deepcopy(v)
            elif isinstance(v, torch.Tensor):
                self._stats[k] = torch.cat([self._stats[k], v], dim=0)
            elif isinstance(v, np.ndarray):
                self._stats[k] = np.concatenate([self._stats[k], v], axis=0)
            elif isinstance(v, list):
                self._stats[k] = self._stats[k] + deepcopy(v)
            else:
                raise TypeError(f'MaskData key {k} has an unsupported type {type(v)}.')

    def to_numpy(self) -> None:
        for k, v in self._stats.items():
            if isinstance(v, torch.Tensor):
                self._stats[k] = v.detach().cpu().numpy()

def __setitem__(self, key: str, item: Any) -> None:
    assert isinstance(item, (list, np.ndarray, torch.Tensor)), 'MaskData only supports list, numpy arrays, and torch tensors.'
    self._stats[key] = item

def items(self) -> ItemsView[str, Any]:
    return self._stats.items()

def filter(self, keep: torch.Tensor) -> None:
    for k, v in self._stats.items():
        if v is None:
            self._stats[k] = None
        elif isinstance(v, torch.Tensor):
            self._stats[k] = v[torch.as_tensor(keep, device=v.device)]
        elif isinstance(v, np.ndarray):
            self._stats[k] = v[keep.detach().cpu().numpy()]
        elif isinstance(v, list) and keep.dtype == torch.bool:
            self._stats[k] = [a for i, a in enumerate(v) if keep[i]]
        elif isinstance(v, list):
            self._stats[k] = [v[i] for i in keep]
        else:
            raise TypeError(f'MaskData key {k} has an unsupported type {type(v)}.')

def cat(self, new_stats: 'MaskData') -> None:
    for k, v in new_stats.items():
        if k not in self._stats or self._stats[k] is None:
            self._stats[k] = deepcopy(v)
        elif isinstance(v, torch.Tensor):
            self._stats[k] = torch.cat([self._stats[k], v], dim=0)
        elif isinstance(v, np.ndarray):
            self._stats[k] = np.concatenate([self._stats[k], v], axis=0)
        elif isinstance(v, list):
            self._stats[k] = self._stats[k] + deepcopy(v)
        else:
            raise TypeError(f'MaskData key {k} has an unsupported type {type(v)}.')

def to_numpy(self) -> None:
    for k, v in self._stats.items():
        if isinstance(v, torch.Tensor):
            self._stats[k] = v.detach().cpu().numpy()

def mask_to_rle_pytorch(tensor: torch.Tensor) -> List[Dict[str, Any]]:
    """
    Encodes masks to an uncompressed RLE, in the format expected by
    pycoco tools.
    """
    b, h, w = tensor.shape
    tensor = tensor.permute(0, 2, 1).flatten(1)
    diff = tensor[:, 1:] ^ tensor[:, :-1]
    change_indices = diff.nonzero()
    out = []
    for i in range(b):
        cur_idxs = change_indices[change_indices[:, 0] == i, 1]
        cur_idxs = torch.cat([torch.tensor([0], dtype=cur_idxs.dtype, device=cur_idxs.device), cur_idxs + 1, torch.tensor([h * w], dtype=cur_idxs.dtype, device=cur_idxs.device)])
        btw_idxs = cur_idxs[1:] - cur_idxs[:-1]
        counts = [] if tensor[i, 0] == 0 else [0]
        counts.extend(btw_idxs.detach().cpu().tolist())
        out.append({'size': [h, w], 'counts': counts})
    return out

def add_prefix_to_keys(dct, prefix):
    return {prefix + k: v for k, v in dct.items()}

def flatten_dict(dct):
    result = {}
    for k, v in dct.items():
        if isinstance(k, tuple):
            k = '_'.join(k)
        if isinstance(v, dict):
            for sub_k, sub_v in flatten_dict(v).items():
                result[f'{k}_{sub_k}'] = sub_v
        else:
            result[k] = v
    return result

def get_shape(t):
    if torch.is_tensor(t):
        return tuple(t.shape)
    elif isinstance(t, dict):
        return {n: get_shape(q) for n, q in t.items()}
    elif isinstance(t, (list, tuple)):
        return [get_shape(q) for q in t]
    elif isinstance(t, numbers.Number):
        return type(t)
    else:
        raise ValueError('unexpected type {}'.format(type(t)))

def masked_l2_loss(pred, target, mask, weight_known, weight_missing):
    per_pixel_l2 = F.mse_loss(pred, target, reduction='none')
    pixel_weights = mask * weight_missing + (1 - mask) * weight_known
    return (pixel_weights * per_pixel_l2).mean()

def feature_matching_loss(fake_features: List[torch.Tensor], target_features: List[torch.Tensor], mask=None):
    if mask is None:
        res = torch.stack([F.mse_loss(fake_feat, target_feat) for fake_feat, target_feat in zip(fake_features, target_features)]).mean()
    else:
        res = 0
        norm = 0
        for fake_feat, target_feat in zip(fake_features, target_features):
            cur_mask = F.interpolate(mask, size=fake_feat.shape[-2:], mode='bilinear', align_corners=False)
            error_weights = 1 - cur_mask
            cur_val = ((fake_feat - target_feat).pow(2) * error_weights).mean()
            res = res + cur_val
            norm += 1
        res = res / norm
    return res

class BaseInpaintingTrainingModule(ptl.LightningModule):

    def __init__(self, config, use_ddp, *args, predict_only=False, visualize_each_iters=100, average_generator=False, generator_avg_beta=0.999, average_generator_start_step=30000, average_generator_period=10, store_discr_outputs_for_vis=False, **kwargs):
        super().__init__(*args, **kwargs)
        LOGGER.info('BaseInpaintingTrainingModule init called')
        self.config = config
        self.generator = make_generator(config, **self.config.generator)
        self.use_ddp = use_ddp
        if not get_has_ddp_rank():
            LOGGER.info(f'Generator\n{self.generator}')
        if not predict_only:
            self.save_hyperparameters(self.config)
            self.discriminator = make_discriminator(**self.config.discriminator)
            self.adversarial_loss = make_discrim_loss(**self.config.losses.adversarial)
            self.visualizer = make_visualizer(**self.config.visualizer)
            self.val_evaluator = make_evaluator(**self.config.evaluator)
            self.test_evaluator = make_evaluator(**self.config.evaluator)
            if not get_has_ddp_rank():
                LOGGER.info(f'Discriminator\n{self.discriminator}')
            extra_val = self.config.data.get('extra_val', ())
            if extra_val:
                self.extra_val_titles = list(extra_val)
                self.extra_evaluators = nn.ModuleDict({k: make_evaluator(**self.config.evaluator) for k in extra_val})
            else:
                self.extra_evaluators = {}
            self.average_generator = average_generator
            self.generator_avg_beta = generator_avg_beta
            self.average_generator_start_step = average_generator_start_step
            self.average_generator_period = average_generator_period
            self.generator_average = None
            self.last_generator_averaging_step = -1
            self.store_discr_outputs_for_vis = store_discr_outputs_for_vis
            if self.config.losses.get('l1', {'weight_known': 0})['weight_known'] > 0:
                self.loss_l1 = nn.L1Loss(reduction='none')
            if self.config.losses.get('mse', {'weight': 0})['weight'] > 0:
                self.loss_mse = nn.MSELoss(reduction='none')
            if self.config.losses.perceptual.weight > 0:
                self.loss_pl = PerceptualLoss()
            if self.config.losses.get('resnet_pl', {'weight': 0})['weight'] > 0:
                self.loss_resnet_pl = ResNetPL(**self.config.losses.resnet_pl)
            else:
                self.loss_resnet_pl = None
        self.visualize_each_iters = visualize_each_iters
        LOGGER.info('BaseInpaintingTrainingModule init done')

    def configure_optimizers(self):
        discriminator_params = list(self.discriminator.parameters())
        return [dict(optimizer=make_optimizer(self.generator.parameters(), **self.config.optimizers.generator)), dict(optimizer=make_optimizer(discriminator_params, **self.config.optimizers.discriminator))]

    def train_dataloader(self):
        kwargs = dict(self.config.data.train)
        if self.use_ddp:
            kwargs['ddp_kwargs'] = dict(num_replicas=self.trainer.num_nodes * self.trainer.num_processes, rank=self.trainer.global_rank, shuffle=True)
        dataloader = make_default_train_dataloader(**self.config.data.train)
        return dataloader

    def val_dataloader(self):
        res = [make_default_val_dataloader(**self.config.data.val)]
        if self.config.data.visual_test is not None:
            res = res + [make_default_val_dataloader(**self.config.data.visual_test)]
        else:
            res = res + res
        extra_val = self.config.data.get('extra_val', ())
        if extra_val:
            res += [make_default_val_dataloader(**extra_val[k]) for k in self.extra_val_titles]
        return res

    def training_step(self, batch, batch_idx, optimizer_idx=None):
        self._is_training_step = True
        return self._do_step(batch, batch_idx, mode='train', optimizer_idx=optimizer_idx)

    def validation_step(self, batch, batch_idx, dataloader_idx):
        extra_val_key = None
        if dataloader_idx == 0:
            mode = 'val'
        elif dataloader_idx == 1:
            mode = 'test'
        else:
            mode = 'extra_val'
            extra_val_key = self.extra_val_titles[dataloader_idx - 2]
        self._is_training_step = False
        return self._do_step(batch, batch_idx, mode=mode, extra_val_key=extra_val_key)

    def training_step_end(self, batch_parts_outputs):
        if self.training and self.average_generator and (self.global_step >= self.average_generator_start_step) and (self.global_step >= self.last_generator_averaging_step + self.average_generator_period):
            if self.generator_average is None:
                self.generator_average = copy.deepcopy(self.generator)
            else:
                update_running_average(self.generator_average, self.generator, decay=self.generator_avg_beta)
            self.last_generator_averaging_step = self.global_step
        full_loss = batch_parts_outputs['loss'].mean() if torch.is_tensor(batch_parts_outputs['loss']) else torch.tensor(batch_parts_outputs['loss']).float().requires_grad_(True)
        log_info = {k: v.mean() for k, v in batch_parts_outputs['log_info'].items()}
        self.log_dict(log_info, on_step=True, on_epoch=False)
        return full_loss

    def validation_epoch_end(self, outputs):
        outputs = [step_out for out_group in outputs for step_out in out_group]
        averaged_logs = average_dicts((step_out['log_info'] for step_out in outputs))
        self.log_dict({k: v.mean() for k, v in averaged_logs.items()})
        pd.set_option('display.max_columns', 500)
        pd.set_option('display.width', 1000)
        val_evaluator_states = [s['val_evaluator_state'] for s in outputs if 'val_evaluator_state' in s]
        val_evaluator_res = self.val_evaluator.evaluation_end(states=val_evaluator_states)
        val_evaluator_res_df = pd.DataFrame(val_evaluator_res).stack(1).unstack(0)
        val_evaluator_res_df.dropna(axis=1, how='all', inplace=True)
        LOGGER.info(f'Validation metrics after epoch #{self.current_epoch}, total {self.global_step} iterations:\n{val_evaluator_res_df}')
        for k, v in flatten_dict(val_evaluator_res).items():
            self.log(f'val_{k}', v)
        test_evaluator_states = [s['test_evaluator_state'] for s in outputs if 'test_evaluator_state' in s]
        test_evaluator_res = self.test_evaluator.evaluation_end(states=test_evaluator_states)
        test_evaluator_res_df = pd.DataFrame(test_evaluator_res).stack(1).unstack(0)
        test_evaluator_res_df.dropna(axis=1, how='all', inplace=True)
        LOGGER.info(f'Test metrics after epoch #{self.current_epoch}, total {self.global_step} iterations:\n{test_evaluator_res_df}')
        for k, v in flatten_dict(test_evaluator_res).items():
            self.log(f'test_{k}', v)
        if self.extra_evaluators:
            for cur_eval_title, cur_evaluator in self.extra_evaluators.items():
                cur_state_key = f'extra_val_{cur_eval_title}_evaluator_state'
                cur_states = [s[cur_state_key] for s in outputs if cur_state_key in s]
                cur_evaluator_res = cur_evaluator.evaluation_end(states=cur_states)
                cur_evaluator_res_df = pd.DataFrame(cur_evaluator_res).stack(1).unstack(0)
                cur_evaluator_res_df.dropna(axis=1, how='all', inplace=True)
                LOGGER.info(f'Extra val {cur_eval_title} metrics after epoch #{self.current_epoch}, total {self.global_step} iterations:\n{cur_evaluator_res_df}')
                for k, v in flatten_dict(cur_evaluator_res).items():
                    self.log(f'extra_val_{cur_eval_title}_{k}', v)

    def _do_step(self, batch, batch_idx, mode='train', optimizer_idx=None, extra_val_key=None):
        if optimizer_idx == 0:
            set_requires_grad(self.generator, True)
            set_requires_grad(self.discriminator, False)
        elif optimizer_idx == 1:
            set_requires_grad(self.generator, False)
            set_requires_grad(self.discriminator, True)
        batch = self(batch)
        total_loss = 0
        metrics = {}
        if optimizer_idx is None or optimizer_idx == 0:
            total_loss, metrics = self.generator_loss(batch)
        elif optimizer_idx is None or optimizer_idx == 1:
            if self.config.losses.adversarial.weight > 0:
                total_loss, metrics = self.discriminator_loss(batch)
        if self.get_ddp_rank() in (None, 0) and (batch_idx % self.visualize_each_iters == 0 or mode == 'test'):
            if self.config.losses.adversarial.weight > 0:
                if self.store_discr_outputs_for_vis:
                    with torch.no_grad():
                        self.store_discr_outputs(batch)
            vis_suffix = f'_{mode}'
            if mode == 'extra_val':
                vis_suffix += f'_{extra_val_key}'
            self.visualizer(self.current_epoch, batch_idx, batch, suffix=vis_suffix)
        metrics_prefix = f'{mode}_'
        if mode == 'extra_val':
            metrics_prefix += f'{extra_val_key}_'
        result = dict(loss=total_loss, log_info=add_prefix_to_keys(metrics, metrics_prefix))
        if mode == 'val':
            result['val_evaluator_state'] = self.val_evaluator.process_batch(batch)
        elif mode == 'test':
            result['test_evaluator_state'] = self.test_evaluator.process_batch(batch)
        elif mode == 'extra_val':
            result[f'extra_val_{extra_val_key}_evaluator_state'] = self.extra_evaluators[extra_val_key].process_batch(batch)
        return result

    def get_current_generator(self, no_average=False):
        if not no_average and (not self.training) and self.average_generator and (self.generator_average is not None):
            return self.generator_average
        return self.generator

    def forward(self, batch: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """Pass data through generator and obtain at leas 'predicted_image' and 'inpainted' keys"""
        raise NotImplementedError()

    def generator_loss(self, batch) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        raise NotImplementedError()

    def discriminator_loss(self, batch) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        raise NotImplementedError()

    def store_discr_outputs(self, batch):
        out_size = batch['image'].shape[2:]
        discr_real_out, _ = self.discriminator(batch['image'])
        discr_fake_out, _ = self.discriminator(batch['predicted_image'])
        batch['discr_output_real'] = F.interpolate(discr_real_out, size=out_size, mode='nearest')
        batch['discr_output_fake'] = F.interpolate(discr_fake_out, size=out_size, mode='nearest')
        batch['discr_output_diff'] = batch['discr_output_real'] - batch['discr_output_fake']

    def get_ddp_rank(self):
        return self.trainer.global_rank if self.trainer.num_nodes * self.trainer.num_processes > 1 else None

def training_step_end(self, batch_parts_outputs):
    if self.training and self.average_generator and (self.global_step >= self.average_generator_start_step) and (self.global_step >= self.last_generator_averaging_step + self.average_generator_period):
        if self.generator_average is None:
            self.generator_average = copy.deepcopy(self.generator)
        else:
            update_running_average(self.generator_average, self.generator, decay=self.generator_avg_beta)
        self.last_generator_averaging_step = self.global_step
    full_loss = batch_parts_outputs['loss'].mean() if torch.is_tensor(batch_parts_outputs['loss']) else torch.tensor(batch_parts_outputs['loss']).float().requires_grad_(True)
    log_info = {k: v.mean() for k, v in batch_parts_outputs['log_info'].items()}
    self.log_dict(log_info, on_step=True, on_epoch=False)
    return full_loss

class ConcatTupleLayer(nn.Module):

    def forward(self, x):
        assert isinstance(x, tuple)
        x_l, x_g = x
        assert torch.is_tensor(x_l) or torch.is_tensor(x_g)
        if not torch.is_tensor(x_g):
            return x_l
        return torch.cat(x, dim=1)

def forward(self, x):
    assert isinstance(x, tuple)
    x_l, x_g = x
    assert torch.is_tensor(x_l) or torch.is_tensor(x_g)
    if not torch.is_tensor(x_g):
        return x_l
    return torch.cat(x, dim=1)

class FFCNLayerDiscriminator(BaseDiscriminator):

    def __init__(self, input_nc, ndf=64, n_layers=3, norm_layer=nn.BatchNorm2d, max_features=512, init_conv_kwargs={}, conv_kwargs={}):
        super().__init__()
        self.n_layers = n_layers

        def _act_ctor(inplace=True):
            return nn.LeakyReLU(negative_slope=0.2, inplace=inplace)
        kw = 3
        padw = int(np.ceil((kw - 1.0) / 2))
        sequence = [[FFC_BN_ACT(input_nc, ndf, kernel_size=kw, padding=padw, norm_layer=norm_layer, activation_layer=_act_ctor, **init_conv_kwargs)]]
        nf = ndf
        for n in range(1, n_layers):
            nf_prev = nf
            nf = min(nf * 2, max_features)
            cur_model = [FFC_BN_ACT(nf_prev, nf, kernel_size=kw, stride=2, padding=padw, norm_layer=norm_layer, activation_layer=_act_ctor, **conv_kwargs)]
            sequence.append(cur_model)
        nf_prev = nf
        nf = min(nf * 2, 512)
        cur_model = [FFC_BN_ACT(nf_prev, nf, kernel_size=kw, stride=1, padding=padw, norm_layer=norm_layer, activation_layer=lambda *args, **kwargs: nn.LeakyReLU(*args, negative_slope=0.2, **kwargs), **conv_kwargs), ConcatTupleLayer()]
        sequence.append(cur_model)
        sequence += [[nn.Conv2d(nf, 1, kernel_size=kw, stride=1, padding=padw)]]
        for n in range(len(sequence)):
            setattr(self, 'model' + str(n), nn.Sequential(*sequence[n]))

    def get_all_activations(self, x):
        res = [x]
        for n in range(self.n_layers + 2):
            model = getattr(self, 'model' + str(n))
            res.append(model(res[-1]))
        return res[1:]

    def forward(self, x):
        act = self.get_all_activations(x)
        feats = []
        for out in act[:-1]:
            if isinstance(out, tuple):
                if torch.is_tensor(out[1]):
                    out = torch.cat(out, dim=1)
                else:
                    out = out[0]
            feats.append(out)
        return (act[-1], feats)

def forward(self, x):
    act = self.get_all_activations(x)
    feats = []
    for out in act[:-1]:
        if isinstance(out, tuple):
            if torch.is_tensor(out[1]):
                out = torch.cat(out, dim=1)
            else:
                out = out[0]
        feats.append(out)
    return (act[-1], feats)

class NLayerDiscriminator(BaseDiscriminator):

    def __init__(self, input_nc, ndf=64, n_layers=3, norm_layer=nn.BatchNorm2d):
        super().__init__()
        self.n_layers = n_layers
        kw = 4
        padw = int(np.ceil((kw - 1.0) / 2))
        sequence = [[nn.Conv2d(input_nc, ndf, kernel_size=kw, stride=2, padding=padw), nn.LeakyReLU(0.2, True)]]
        nf = ndf
        for n in range(1, n_layers):
            nf_prev = nf
            nf = min(nf * 2, 512)
            cur_model = []
            cur_model += [nn.Conv2d(nf_prev, nf, kernel_size=kw, stride=2, padding=padw), norm_layer(nf), nn.LeakyReLU(0.2, True)]
            sequence.append(cur_model)
        nf_prev = nf
        nf = min(nf * 2, 512)
        cur_model = []
        cur_model += [nn.Conv2d(nf_prev, nf, kernel_size=kw, stride=1, padding=padw), norm_layer(nf), nn.LeakyReLU(0.2, True)]
        sequence.append(cur_model)
        sequence += [[nn.Conv2d(nf, 1, kernel_size=kw, stride=1, padding=padw)]]
        for n in range(len(sequence)):
            setattr(self, 'model' + str(n), nn.Sequential(*sequence[n]))

    def get_all_activations(self, x):
        res = [x]
        for n in range(self.n_layers + 2):
            model = getattr(self, 'model' + str(n))
            res.append(model(res[-1]))
        return res[1:]

    def forward(self, x):
        act = self.get_all_activations(x)
        return (act[-1], act[:-1])

def forward(self, x):
    act = self.get_all_activations(x)
    return (act[-1], act[:-1])

class MultidilatedNLayerDiscriminator(BaseDiscriminator):

    def __init__(self, input_nc, ndf=64, n_layers=3, norm_layer=nn.BatchNorm2d, multidilation_kwargs={}):
        super().__init__()
        self.n_layers = n_layers
        kw = 4
        padw = int(np.ceil((kw - 1.0) / 2))
        sequence = [[nn.Conv2d(input_nc, ndf, kernel_size=kw, stride=2, padding=padw), nn.LeakyReLU(0.2, True)]]
        nf = ndf
        for n in range(1, n_layers):
            nf_prev = nf
            nf = min(nf * 2, 512)
            cur_model = []
            cur_model += [MultidilatedConv(nf_prev, nf, kernel_size=kw, stride=2, padding=[2, 3], **multidilation_kwargs), norm_layer(nf), nn.LeakyReLU(0.2, True)]
            sequence.append(cur_model)
        nf_prev = nf
        nf = min(nf * 2, 512)
        cur_model = []
        cur_model += [nn.Conv2d(nf_prev, nf, kernel_size=kw, stride=1, padding=padw), norm_layer(nf), nn.LeakyReLU(0.2, True)]
        sequence.append(cur_model)
        sequence += [[nn.Conv2d(nf, 1, kernel_size=kw, stride=1, padding=padw)]]
        for n in range(len(sequence)):
            setattr(self, 'model' + str(n), nn.Sequential(*sequence[n]))

    def get_all_activations(self, x):
        res = [x]
        for n in range(self.n_layers + 2):
            model = getattr(self, 'model' + str(n))
            res.append(model(res[-1]))
        return res[1:]

    def forward(self, x):
        act = self.get_all_activations(x)
        return (act[-1], act[:-1])

def forward(self, x):
    act = self.get_all_activations(x)
    return (act[-1], act[:-1])

def visualize_mask_and_images_batch(batch: Dict[str, torch.Tensor], keys: List[str], max_items=10, last_without_mask=True, rescale_keys=None) -> np.ndarray:
    batch = {k: tens.detach().cpu().numpy() for k, tens in batch.items() if k in keys or k == 'mask'}
    batch_size = next(iter(batch.values())).shape[0]
    items_to_vis = min(batch_size, max_items)
    result = []
    for i in range(items_to_vis):
        cur_dct = {k: tens[i] for k, tens in batch.items()}
        result.append(visualize_mask_and_images(cur_dct, keys, last_without_mask=last_without_mask, rescale_keys=rescale_keys))
    return np.concatenate(result, axis=0)

def move_to_device(obj, device):
    if isinstance(obj, nn.Module):
        return obj.to(device)
    if torch.is_tensor(obj):
        return obj.to(device)
    if isinstance(obj, (tuple, list)):
        return [move_to_device(el, device) for el in obj]
    if isinstance(obj, dict):
        return {name: move_to_device(val, device) for name, val in obj.items()}
    raise ValueError(f'Unexpected type {type(obj)}')

def refine_predict(batch: dict, inpainter: nn.Module, gpu_ids: str, modulo: int, n_iters: int, lr: float, min_side: int, max_scales: int, px_budget: int):
    """Refines the inpainting of the network

    Parameters
    ----------
    batch : dict
        image-mask batch, currently we assume the batchsize to be 1
    inpainter : nn.Module
        the inpainting neural network
    gpu_ids : str
        the GPU ids of the machine to use. If only single GPU, use: "0,"
    modulo : int
        pad the image to ensure dimension % modulo == 0
    n_iters : int
        number of iterations of refinement for each scale
    lr : float
        learning rate
    min_side : int
        all sides of image on all scales should be >= min_side / sqrt(2)
    max_scales : int
        max number of downscaling scales for the image-mask pyramid
    px_budget : int
        pixels budget. Any image will be resized to satisfy height*width <= px_budget

    Returns
    -------
    torch.Tensor
        inpainted image of size (1,3,H,W)
    """
    assert not inpainter.training
    assert not inpainter.add_noise_kwargs
    assert inpainter.concat_mask
    gpu_ids = [f'cuda:{gpuid}' for gpuid in gpu_ids.replace(' ', '').split(',') if gpuid.isdigit()]
    n_resnet_blocks = 0
    first_resblock_ind = 0
    found_first_resblock = False
    for idl in range(len(inpainter.generator.model)):
        if isinstance(inpainter.generator.model[idl], FFCResnetBlock) or isinstance(inpainter.generator.model[idl], ResnetBlock):
            n_resnet_blocks += 1
            found_first_resblock = True
        elif not found_first_resblock:
            first_resblock_ind += 1
    resblocks_per_gpu = n_resnet_blocks // len(gpu_ids)
    devices = [torch.device(gpu_id) for gpu_id in gpu_ids]
    forward_front = inpainter.generator.model[0:first_resblock_ind]
    forward_front.to(devices[0])
    forward_rears = []
    for idd in range(len(gpu_ids)):
        if idd < len(gpu_ids) - 1:
            forward_rears.append(inpainter.generator.model[first_resblock_ind + resblocks_per_gpu * idd:first_resblock_ind + resblocks_per_gpu * (idd + 1)])
        else:
            forward_rears.append(inpainter.generator.model[first_resblock_ind + resblocks_per_gpu * idd:])
        forward_rears[idd].to(devices[idd])
    ls_images, ls_masks = _get_image_mask_pyramid(batch, min_side, max_scales, px_budget)
    image_inpainted = None
    for ids, (image, mask) in enumerate(zip(ls_images, ls_masks)):
        orig_shape = image.shape[2:]
        image = pad_tensor_to_modulo(image, modulo)
        mask = pad_tensor_to_modulo(mask, modulo)
        mask[mask >= 1e-08] = 1.0
        mask[mask < 1e-08] = 0.0
        image, mask = (move_to_device(image, devices[0]), move_to_device(mask, devices[0]))
        if image_inpainted is not None:
            image_inpainted = move_to_device(image_inpainted, devices[-1])
        image_inpainted = _infer(image, mask, forward_front, forward_rears, image_inpainted, orig_shape, devices, ids, n_iters, lr)
        image_inpainted = image_inpainted[:, :, :orig_shape[0], :orig_shape[1]]
        image = image.detach().cpu()
        mask = mask.detach().cpu()
    return image_inpainted

class InpaintingEvaluator:

    def __init__(self, dataset, scores, area_grouping=True, bins=10, batch_size=32, device='cuda', integral_func=None, integral_title=None, clamp_image_range=None):
        """
        :param dataset: torch.utils.data.Dataset which contains images and masks
        :param scores: dict {score_name: EvaluatorScore object}
        :param area_grouping: in addition to the overall scores, allows to compute score for the groups of samples
            which are defined by share of area occluded by mask
        :param bins: number of groups, partition is generated by np.linspace(0., 1., bins + 1)
        :param batch_size: batch_size for the dataloader
        :param device: device to use
        """
        self.scores = scores
        self.dataset = dataset
        self.area_grouping = area_grouping
        self.bins = bins
        self.device = torch.device(device)
        self.dataloader = DataLoader(self.dataset, shuffle=False, batch_size=batch_size)
        self.integral_func = integral_func
        self.integral_title = integral_title
        self.clamp_image_range = clamp_image_range

    def _get_bin_edges(self):
        bin_edges = np.linspace(0, 1, self.bins + 1)
        num_digits = max(0, math.ceil(math.log10(self.bins)) - 1)
        interval_names = []
        for idx_bin in range(self.bins):
            start_percent, end_percent = (round(100 * bin_edges[idx_bin], num_digits), round(100 * bin_edges[idx_bin + 1], num_digits))
            start_percent = '{:.{n}f}'.format(start_percent, n=num_digits)
            end_percent = '{:.{n}f}'.format(end_percent, n=num_digits)
            interval_names.append('{0}-{1}%'.format(start_percent, end_percent))
        groups = []
        for batch in self.dataloader:
            mask = batch['mask']
            batch_size = mask.shape[0]
            area = mask.to(self.device).reshape(batch_size, -1).mean(dim=-1)
            bin_indices = np.searchsorted(bin_edges, area.detach().cpu().numpy(), side='right') - 1
            bin_indices[bin_indices == self.bins] = self.bins - 1
            groups.append(bin_indices)
        groups = np.hstack(groups)
        return (groups, interval_names)

    def evaluate(self, model=None):
        """
        :param model: callable with signature (image_batch, mask_batch); should return inpainted_batch
        :return: dict with (score_name, group_type) as keys, where group_type can be either 'overall' or
            name of the particular group arranged by area of mask (e.g. '10-20%')
            and score statistics for the group as values.
        """
        results = dict()
        if self.area_grouping:
            groups, interval_names = self._get_bin_edges()
        else:
            groups = None
        for score_name, score in tqdm.auto.tqdm(self.scores.items(), desc='scores'):
            score.to(self.device)
            with torch.no_grad():
                score.reset()
                for batch in tqdm.auto.tqdm(self.dataloader, desc=score_name, leave=False):
                    batch = move_to_device(batch, self.device)
                    image_batch, mask_batch = (batch['image'], batch['mask'])
                    if self.clamp_image_range is not None:
                        image_batch = torch.clamp(image_batch, min=self.clamp_image_range[0], max=self.clamp_image_range[1])
                    if model is None:
                        assert 'inpainted' in batch, 'Model is None, so we expected precomputed inpainting results at key "inpainted"'
                        inpainted_batch = batch['inpainted']
                    else:
                        inpainted_batch = model(image_batch, mask_batch)
                    score(inpainted_batch, image_batch, mask_batch)
                total_results, group_results = score.get_value(groups=groups)
            results[score_name, 'total'] = total_results
            if groups is not None:
                for group_index, group_values in group_results.items():
                    group_name = interval_names[group_index]
                    results[score_name, group_name] = group_values
        if self.integral_func is not None:
            results[self.integral_title, 'total'] = dict(mean=self.integral_func(results))
        return results

def __init__(self, dataset, scores, area_grouping=True, bins=10, batch_size=32, device='cuda', integral_func=None, integral_title=None, clamp_image_range=None):
    """
        :param dataset: torch.utils.data.Dataset which contains images and masks
        :param scores: dict {score_name: EvaluatorScore object}
        :param area_grouping: in addition to the overall scores, allows to compute score for the groups of samples
            which are defined by share of area occluded by mask
        :param bins: number of groups, partition is generated by np.linspace(0., 1., bins + 1)
        :param batch_size: batch_size for the dataloader
        :param device: device to use
        """
    self.scores = scores
    self.dataset = dataset
    self.area_grouping = area_grouping
    self.bins = bins
    self.device = torch.device(device)
    self.dataloader = DataLoader(self.dataset, shuffle=False, batch_size=batch_size)
    self.integral_func = integral_func
    self.integral_title = integral_title
    self.clamp_image_range = clamp_image_range

def _get_bin_edges(self):
    bin_edges = np.linspace(0, 1, self.bins + 1)
    num_digits = max(0, math.ceil(math.log10(self.bins)) - 1)
    interval_names = []
    for idx_bin in range(self.bins):
        start_percent, end_percent = (round(100 * bin_edges[idx_bin], num_digits), round(100 * bin_edges[idx_bin + 1], num_digits))
        start_percent = '{:.{n}f}'.format(start_percent, n=num_digits)
        end_percent = '{:.{n}f}'.format(end_percent, n=num_digits)
        interval_names.append('{0}-{1}%'.format(start_percent, end_percent))
    groups = []
    for batch in self.dataloader:
        mask = batch['mask']
        batch_size = mask.shape[0]
        area = mask.to(self.device).reshape(batch_size, -1).mean(dim=-1)
        bin_indices = np.searchsorted(bin_edges, area.detach().cpu().numpy(), side='right') - 1
        bin_indices[bin_indices == self.bins] = self.bins - 1
        groups.append(bin_indices)
    groups = np.hstack(groups)
    return (groups, interval_names)

class InpaintingEvaluatorOnline(nn.Module):

    def __init__(self, scores, bins=10, image_key='image', inpainted_key='inpainted', integral_func=None, integral_title=None, clamp_image_range=None):
        """
        :param scores: dict {score_name: EvaluatorScore object}
        :param bins: number of groups, partition is generated by np.linspace(0., 1., bins + 1)
        :param device: device to use
        """
        super().__init__()
        LOGGER.info(f'{type(self)} init called')
        self.scores = nn.ModuleDict(scores)
        self.image_key = image_key
        self.inpainted_key = inpainted_key
        self.bins_num = bins
        self.bin_edges = np.linspace(0, 1, self.bins_num + 1)
        num_digits = max(0, math.ceil(math.log10(self.bins_num)) - 1)
        self.interval_names = []
        for idx_bin in range(self.bins_num):
            start_percent, end_percent = (round(100 * self.bin_edges[idx_bin], num_digits), round(100 * self.bin_edges[idx_bin + 1], num_digits))
            start_percent = '{:.{n}f}'.format(start_percent, n=num_digits)
            end_percent = '{:.{n}f}'.format(end_percent, n=num_digits)
            self.interval_names.append('{0}-{1}%'.format(start_percent, end_percent))
        self.groups = []
        self.integral_func = integral_func
        self.integral_title = integral_title
        self.clamp_image_range = clamp_image_range
        LOGGER.info(f'{type(self)} init done')

    def _get_bins(self, mask_batch):
        batch_size = mask_batch.shape[0]
        area = mask_batch.view(batch_size, -1).mean(dim=-1).detach().cpu().numpy()
        bin_indices = np.clip(np.searchsorted(self.bin_edges, area) - 1, 0, self.bins_num - 1)
        return bin_indices

    def forward(self, batch: Dict[str, torch.Tensor]):
        """
        Calculate and accumulate metrics for batch. To finalize evaluation and obtain final metrics, call evaluation_end
        :param batch: batch dict with mandatory fields mask, image, inpainted (can be overriden by self.inpainted_key)
        """
        result = {}
        with torch.no_grad():
            image_batch, mask_batch, inpainted_batch = (batch[self.image_key], batch['mask'], batch[self.inpainted_key])
            if self.clamp_image_range is not None:
                image_batch = torch.clamp(image_batch, min=self.clamp_image_range[0], max=self.clamp_image_range[1])
            self.groups.extend(self._get_bins(mask_batch))
            for score_name, score in self.scores.items():
                result[score_name] = score(inpainted_batch, image_batch, mask_batch)
        return result

    def process_batch(self, batch: Dict[str, torch.Tensor]):
        return self(batch)

    def evaluation_end(self, states=None):
        """:return: dict with (score_name, group_type) as keys, where group_type can be either 'overall' or
            name of the particular group arranged by area of mask (e.g. '10-20%')
            and score statistics for the group as values.
        """
        LOGGER.info(f'{type(self)}: evaluation_end called')
        self.groups = np.array(self.groups)
        results = {}
        for score_name, score in self.scores.items():
            LOGGER.info(f'Getting value of {score_name}')
            cur_states = [s[score_name] for s in states] if states is not None else None
            total_results, group_results = score.get_value(groups=self.groups, states=cur_states)
            LOGGER.info(f'Getting value of {score_name} done')
            results[score_name, 'total'] = total_results
            for group_index, group_values in group_results.items():
                group_name = self.interval_names[group_index]
                results[score_name, group_name] = group_values
        if self.integral_func is not None:
            results[self.integral_title, 'total'] = dict(mean=self.integral_func(results))
        LOGGER.info(f'{type(self)}: reset scores')
        self.groups = []
        for sc in self.scores.values():
            sc.reset()
        LOGGER.info(f'{type(self)}: reset scores done')
        LOGGER.info(f'{type(self)}: evaluation_end done')
        return results

def _get_bins(self, mask_batch):
    batch_size = mask_batch.shape[0]
    area = mask_batch.view(batch_size, -1).mean(dim=-1).detach().cpu().numpy()
    bin_indices = np.clip(np.searchsorted(self.bin_edges, area) - 1, 0, self.bins_num - 1)
    return bin_indices

class PairwiseScore(EvaluatorScore, ABC):

    def __init__(self):
        super().__init__()
        self.individual_values = None

    def get_value(self, groups=None, states=None):
        """
        :param groups:
        :return:
            total_results: dict of kind {'mean': score mean, 'std': score std}
            group_results: None, if groups is None;
                else dict {group_idx: {'mean': score mean among group, 'std': score std among group}}
        """
        individual_values = torch.cat(states, dim=-1).reshape(-1).cpu().numpy() if states is not None else self.individual_values
        total_results = {'mean': individual_values.mean(), 'std': individual_values.std()}
        if groups is None:
            return (total_results, None)
        group_results = dict()
        grouping = get_groupings(groups)
        for label, index in grouping.items():
            group_scores = individual_values[index]
            group_results[label] = {'mean': group_scores.mean(), 'std': group_scores.std()}
        return (total_results, group_results)

    def reset(self):
        self.individual_values = []

def get_value(self, groups=None, states=None):
    """
        :param groups:
        :return:
            total_results: dict of kind {'mean': score mean, 'std': score std}
            group_results: None, if groups is None;
                else dict {group_idx: {'mean': score mean among group, 'std': score std among group}}
        """
    individual_values = torch.cat(states, dim=-1).reshape(-1).cpu().numpy() if states is not None else self.individual_values
    total_results = {'mean': individual_values.mean(), 'std': individual_values.std()}
    if groups is None:
        return (total_results, None)
    group_results = dict()
    grouping = get_groupings(groups)
    for label, index in grouping.items():
        group_scores = individual_values[index]
        group_results[label] = {'mean': group_scores.mean(), 'std': group_scores.std()}
    return (total_results, group_results)

class SSIMScore(PairwiseScore):

    def __init__(self, window_size=11):
        super().__init__()
        self.score = SSIM(window_size=window_size, size_average=False).eval()
        self.reset()

    def forward(self, pred_batch, target_batch, mask=None):
        batch_values = self.score(pred_batch, target_batch)
        self.individual_values = np.hstack([self.individual_values, batch_values.detach().cpu().numpy()])
        return batch_values

def forward(self, pred_batch, target_batch, mask=None):
    batch_values = self.score(pred_batch, target_batch)
    self.individual_values = np.hstack([self.individual_values, batch_values.detach().cpu().numpy()])
    return batch_values

class LPIPSScore(PairwiseScore):

    def __init__(self, model='net-lin', net='vgg', model_path=None, use_gpu=True):
        super().__init__()
        self.score = PerceptualLoss(model=model, net=net, model_path=model_path, use_gpu=use_gpu, spatial=False).eval()
        self.reset()

    def forward(self, pred_batch, target_batch, mask=None):
        batch_values = self.score(pred_batch, target_batch).flatten()
        self.individual_values = np.hstack([self.individual_values, batch_values.detach().cpu().numpy()])
        return batch_values

def forward(self, pred_batch, target_batch, mask=None):
    batch_values = self.score(pred_batch, target_batch).flatten()
    self.individual_values = np.hstack([self.individual_values, batch_values.detach().cpu().numpy()])
    return batch_values

def fid_calculate_activation_statistics(act):
    mu = np.mean(act, axis=0)
    sigma = np.cov(act, rowvar=False)
    return (mu, sigma)

class FIDScore(EvaluatorScore):

    def __init__(self, dims=2048, eps=1e-06):
        LOGGER.info('FIDscore init called')
        super().__init__()
        if getattr(FIDScore, '_MODEL', None) is None:
            block_idx = InceptionV3.BLOCK_INDEX_BY_DIM[dims]
            FIDScore._MODEL = InceptionV3([block_idx]).eval()
        self.model = FIDScore._MODEL
        self.eps = eps
        self.reset()
        LOGGER.info('FIDscore init done')

    def forward(self, pred_batch, target_batch, mask=None):
        activations_pred = self._get_activations(pred_batch)
        activations_target = self._get_activations(target_batch)
        self.activations_pred.append(activations_pred.detach().cpu())
        self.activations_target.append(activations_target.detach().cpu())
        return (activations_pred, activations_target)

    def get_value(self, groups=None, states=None):
        LOGGER.info('FIDscore get_value called')
        activations_pred, activations_target = zip(*states) if states is not None else (self.activations_pred, self.activations_target)
        activations_pred = torch.cat(activations_pred).cpu().numpy()
        activations_target = torch.cat(activations_target).cpu().numpy()
        total_distance = calculate_frechet_distance(activations_pred, activations_target, eps=self.eps)
        total_results = dict(mean=total_distance)
        if groups is None:
            group_results = None
        else:
            group_results = dict()
            grouping = get_groupings(groups)
            for label, index in grouping.items():
                if len(index) > 1:
                    group_distance = calculate_frechet_distance(activations_pred[index], activations_target[index], eps=self.eps)
                    group_results[label] = dict(mean=group_distance)
                else:
                    group_results[label] = dict(mean=float('nan'))
        self.reset()
        LOGGER.info('FIDscore get_value done')
        return (total_results, group_results)

    def reset(self):
        self.activations_pred = []
        self.activations_target = []

    def _get_activations(self, batch):
        activations = self.model(batch)[0]
        if activations.shape[2] != 1 or activations.shape[3] != 1:
            assert False, 'We should not have got here, because Inception always scales inputs to 299x299'
        activations = activations.squeeze(-1).squeeze(-1)
        return activations

def forward(self, pred_batch, target_batch, mask=None):
    activations_pred = self._get_activations(pred_batch)
    activations_target = self._get_activations(target_batch)
    self.activations_pred.append(activations_pred.detach().cpu())
    self.activations_target.append(activations_target.detach().cpu())
    return (activations_pred, activations_target)

def get_value(self, groups=None, states=None):
    LOGGER.info('FIDscore get_value called')
    activations_pred, activations_target = zip(*states) if states is not None else (self.activations_pred, self.activations_target)
    activations_pred = torch.cat(activations_pred).cpu().numpy()
    activations_target = torch.cat(activations_target).cpu().numpy()
    total_distance = calculate_frechet_distance(activations_pred, activations_target, eps=self.eps)
    total_results = dict(mean=total_distance)
    if groups is None:
        group_results = None
    else:
        group_results = dict()
        grouping = get_groupings(groups)
        for label, index in grouping.items():
            if len(index) > 1:
                group_distance = calculate_frechet_distance(activations_pred[index], activations_target[index], eps=self.eps)
                group_results[label] = dict(mean=group_distance)
            else:
                group_results[label] = dict(mean=float('nan'))
    self.reset()
    LOGGER.info('FIDscore get_value done')
    return (total_results, group_results)

class SegmentationAwareScore(EvaluatorScore):

    def __init__(self, weights_path):
        super().__init__()
        self.segm_network = SegmentationModule(weights_path=weights_path, use_default_normalization=True).eval()
        self.target_class_freq_by_image_total = []
        self.target_class_freq_by_image_mask = []
        self.pred_class_freq_by_image_mask = []

    def forward(self, pred_batch, target_batch, mask):
        pred_segm_flat = self.segm_network.predict(pred_batch)[0].view(pred_batch.shape[0], -1).long().detach().cpu().numpy()
        target_segm_flat = self.segm_network.predict(target_batch)[0].view(pred_batch.shape[0], -1).long().detach().cpu().numpy()
        mask_flat = (mask.view(mask.shape[0], -1) > 0.5).detach().cpu().numpy()
        batch_target_class_freq_total = []
        batch_target_class_freq_mask = []
        batch_pred_class_freq_mask = []
        for cur_pred_segm, cur_target_segm, cur_mask in zip(pred_segm_flat, target_segm_flat, mask_flat):
            cur_target_class_freq_total = np.bincount(cur_target_segm, minlength=NUM_CLASS)[None, ...]
            cur_target_class_freq_mask = np.bincount(cur_target_segm[cur_mask], minlength=NUM_CLASS)[None, ...]
            cur_pred_class_freq_mask = np.bincount(cur_pred_segm[cur_mask], minlength=NUM_CLASS)[None, ...]
            self.target_class_freq_by_image_total.append(cur_target_class_freq_total)
            self.target_class_freq_by_image_mask.append(cur_target_class_freq_mask)
            self.pred_class_freq_by_image_mask.append(cur_pred_class_freq_mask)
            batch_target_class_freq_total.append(cur_target_class_freq_total)
            batch_target_class_freq_mask.append(cur_target_class_freq_mask)
            batch_pred_class_freq_mask.append(cur_pred_class_freq_mask)
        batch_target_class_freq_total = np.concatenate(batch_target_class_freq_total, axis=0)
        batch_target_class_freq_mask = np.concatenate(batch_target_class_freq_mask, axis=0)
        batch_pred_class_freq_mask = np.concatenate(batch_pred_class_freq_mask, axis=0)
        return (batch_target_class_freq_total, batch_target_class_freq_mask, batch_pred_class_freq_mask)

    def reset(self):
        super().reset()
        self.target_class_freq_by_image_total = []
        self.target_class_freq_by_image_mask = []
        self.pred_class_freq_by_image_mask = []

def forward(self, pred_batch, target_batch, mask):
    pred_segm_flat = self.segm_network.predict(pred_batch)[0].view(pred_batch.shape[0], -1).long().detach().cpu().numpy()
    target_segm_flat = self.segm_network.predict(target_batch)[0].view(pred_batch.shape[0], -1).long().detach().cpu().numpy()
    mask_flat = (mask.view(mask.shape[0], -1) > 0.5).detach().cpu().numpy()
    batch_target_class_freq_total = []
    batch_target_class_freq_mask = []
    batch_pred_class_freq_mask = []
    for cur_pred_segm, cur_target_segm, cur_mask in zip(pred_segm_flat, target_segm_flat, mask_flat):
        cur_target_class_freq_total = np.bincount(cur_target_segm, minlength=NUM_CLASS)[None, ...]
        cur_target_class_freq_mask = np.bincount(cur_target_segm[cur_mask], minlength=NUM_CLASS)[None, ...]
        cur_pred_class_freq_mask = np.bincount(cur_pred_segm[cur_mask], minlength=NUM_CLASS)[None, ...]
        self.target_class_freq_by_image_total.append(cur_target_class_freq_total)
        self.target_class_freq_by_image_mask.append(cur_target_class_freq_mask)
        self.pred_class_freq_by_image_mask.append(cur_pred_class_freq_mask)
        batch_target_class_freq_total.append(cur_target_class_freq_total)
        batch_target_class_freq_mask.append(cur_target_class_freq_mask)
        batch_pred_class_freq_mask.append(cur_pred_class_freq_mask)
    batch_target_class_freq_total = np.concatenate(batch_target_class_freq_total, axis=0)
    batch_target_class_freq_mask = np.concatenate(batch_target_class_freq_mask, axis=0)
    batch_pred_class_freq_mask = np.concatenate(batch_pred_class_freq_mask, axis=0)
    return (batch_target_class_freq_total, batch_target_class_freq_mask, batch_pred_class_freq_mask)

def get_segmentation_idx2name():
    return {i - 1: name for i, name in segm_options['classes'].set_index('Idx', drop=True)['Name'].to_dict().items()}

class SegmentationAwarePairwiseScore(SegmentationAwareScore):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.individual_values = []
        self.segm_idx2name = get_segmentation_idx2name()

    def forward(self, pred_batch, target_batch, mask):
        cur_class_stats = super().forward(pred_batch, target_batch, mask)
        score_values = self.calc_score(pred_batch, target_batch, mask)
        self.individual_values.append(score_values)
        return cur_class_stats + (score_values,)

    @abstractmethod
    def calc_score(self, pred_batch, target_batch, mask):
        raise NotImplementedError()

    def get_value(self, groups=None, states=None):
        """
        :param groups:
        :return:
            total_results: dict of kind {'mean': score mean, 'std': score std}
            group_results: None, if groups is None;
                else dict {group_idx: {'mean': score mean among group, 'std': score std among group}}
        """
        if states is not None:
            target_class_freq_by_image_total, target_class_freq_by_image_mask, pred_class_freq_by_image_mask, individual_values = states
        else:
            target_class_freq_by_image_total = self.target_class_freq_by_image_total
            target_class_freq_by_image_mask = self.target_class_freq_by_image_mask
            pred_class_freq_by_image_mask = self.pred_class_freq_by_image_mask
            individual_values = self.individual_values
        target_class_freq_by_image_total = np.concatenate(target_class_freq_by_image_total, axis=0)
        target_class_freq_by_image_mask = np.concatenate(target_class_freq_by_image_mask, axis=0)
        pred_class_freq_by_image_mask = np.concatenate(pred_class_freq_by_image_mask, axis=0)
        individual_values = np.concatenate(individual_values, axis=0)
        total_results = {'mean': individual_values.mean(), 'std': individual_values.std(), **distribute_values_to_classes(target_class_freq_by_image_mask, individual_values, self.segm_idx2name)}
        if groups is None:
            return (total_results, None)
        group_results = dict()
        grouping = get_groupings(groups)
        for label, index in grouping.items():
            group_class_freq = target_class_freq_by_image_mask[index]
            group_scores = individual_values[index]
            group_results[label] = {'mean': group_scores.mean(), 'std': group_scores.std(), **distribute_values_to_classes(group_class_freq, group_scores, self.segm_idx2name)}
        return (total_results, group_results)

    def reset(self):
        super().reset()
        self.individual_values = []

def get_value(self, groups=None, states=None):
    """
        :param groups:
        :return:
            total_results: dict of kind {'mean': score mean, 'std': score std}
            group_results: None, if groups is None;
                else dict {group_idx: {'mean': score mean among group, 'std': score std among group}}
        """
    if states is not None:
        target_class_freq_by_image_total, target_class_freq_by_image_mask, pred_class_freq_by_image_mask, individual_values = states
    else:
        target_class_freq_by_image_total = self.target_class_freq_by_image_total
        target_class_freq_by_image_mask = self.target_class_freq_by_image_mask
        pred_class_freq_by_image_mask = self.pred_class_freq_by_image_mask
        individual_values = self.individual_values
    target_class_freq_by_image_total = np.concatenate(target_class_freq_by_image_total, axis=0)
    target_class_freq_by_image_mask = np.concatenate(target_class_freq_by_image_mask, axis=0)
    pred_class_freq_by_image_mask = np.concatenate(pred_class_freq_by_image_mask, axis=0)
    individual_values = np.concatenate(individual_values, axis=0)
    total_results = {'mean': individual_values.mean(), 'std': individual_values.std(), **distribute_values_to_classes(target_class_freq_by_image_mask, individual_values, self.segm_idx2name)}
    if groups is None:
        return (total_results, None)
    group_results = dict()
    grouping = get_groupings(groups)
    for label, index in grouping.items():
        group_class_freq = target_class_freq_by_image_mask[index]
        group_scores = individual_values[index]
        group_results[label] = {'mean': group_scores.mean(), 'std': group_scores.std(), **distribute_values_to_classes(group_class_freq, group_scores, self.segm_idx2name)}
    return (total_results, group_results)

class SegmentationClassStats(SegmentationAwarePairwiseScore):

    def calc_score(self, pred_batch, target_batch, mask):
        return 0

    def get_value(self, groups=None, states=None):
        """
        :param groups:
        :return:
            total_results: dict of kind {'mean': score mean, 'std': score std}
            group_results: None, if groups is None;
                else dict {group_idx: {'mean': score mean among group, 'std': score std among group}}
        """
        if states is not None:
            target_class_freq_by_image_total, target_class_freq_by_image_mask, pred_class_freq_by_image_mask, _ = states
        else:
            target_class_freq_by_image_total = self.target_class_freq_by_image_total
            target_class_freq_by_image_mask = self.target_class_freq_by_image_mask
            pred_class_freq_by_image_mask = self.pred_class_freq_by_image_mask
        target_class_freq_by_image_total = np.concatenate(target_class_freq_by_image_total, axis=0)
        target_class_freq_by_image_mask = np.concatenate(target_class_freq_by_image_mask, axis=0)
        pred_class_freq_by_image_mask = np.concatenate(pred_class_freq_by_image_mask, axis=0)
        target_class_freq_by_image_total_marginal = target_class_freq_by_image_total.sum(0).astype('float32')
        target_class_freq_by_image_total_marginal /= target_class_freq_by_image_total_marginal.sum()
        target_class_freq_by_image_mask_marginal = target_class_freq_by_image_mask.sum(0).astype('float32')
        target_class_freq_by_image_mask_marginal /= target_class_freq_by_image_mask_marginal.sum()
        pred_class_freq_diff = (pred_class_freq_by_image_mask - target_class_freq_by_image_mask).sum(0) / (target_class_freq_by_image_mask.sum(0) + 0.001)
        total_results = dict()
        total_results.update({f'total_freq/{self.segm_idx2name[i]}': v for i, v in enumerate(target_class_freq_by_image_total_marginal) if v > 0})
        total_results.update({f'mask_freq/{self.segm_idx2name[i]}': v for i, v in enumerate(target_class_freq_by_image_mask_marginal) if v > 0})
        total_results.update({f'mask_freq_diff/{self.segm_idx2name[i]}': v for i, v in enumerate(pred_class_freq_diff) if target_class_freq_by_image_total_marginal[i] > 0})
        if groups is None:
            return (total_results, None)
        group_results = dict()
        grouping = get_groupings(groups)
        for label, index in grouping.items():
            group_target_class_freq_by_image_total = target_class_freq_by_image_total[index]
            group_target_class_freq_by_image_mask = target_class_freq_by_image_mask[index]
            group_pred_class_freq_by_image_mask = pred_class_freq_by_image_mask[index]
            group_target_class_freq_by_image_total_marginal = group_target_class_freq_by_image_total.sum(0).astype('float32')
            group_target_class_freq_by_image_total_marginal /= group_target_class_freq_by_image_total_marginal.sum()
            group_target_class_freq_by_image_mask_marginal = group_target_class_freq_by_image_mask.sum(0).astype('float32')
            group_target_class_freq_by_image_mask_marginal /= group_target_class_freq_by_image_mask_marginal.sum()
            group_pred_class_freq_diff = (group_pred_class_freq_by_image_mask - group_target_class_freq_by_image_mask).sum(0) / (group_target_class_freq_by_image_mask.sum(0) + 0.001)
            cur_group_results = dict()
            cur_group_results.update({f'total_freq/{self.segm_idx2name[i]}': v for i, v in enumerate(group_target_class_freq_by_image_total_marginal) if v > 0})
            cur_group_results.update({f'mask_freq/{self.segm_idx2name[i]}': v for i, v in enumerate(group_target_class_freq_by_image_mask_marginal) if v > 0})
            cur_group_results.update({f'mask_freq_diff/{self.segm_idx2name[i]}': v for i, v in enumerate(group_pred_class_freq_diff) if group_target_class_freq_by_image_total_marginal[i] > 0})
            group_results[label] = cur_group_results
        return (total_results, group_results)

def get_value(self, groups=None, states=None):
    """
        :param groups:
        :return:
            total_results: dict of kind {'mean': score mean, 'std': score std}
            group_results: None, if groups is None;
                else dict {group_idx: {'mean': score mean among group, 'std': score std among group}}
        """
    if states is not None:
        target_class_freq_by_image_total, target_class_freq_by_image_mask, pred_class_freq_by_image_mask, _ = states
    else:
        target_class_freq_by_image_total = self.target_class_freq_by_image_total
        target_class_freq_by_image_mask = self.target_class_freq_by_image_mask
        pred_class_freq_by_image_mask = self.pred_class_freq_by_image_mask
    target_class_freq_by_image_total = np.concatenate(target_class_freq_by_image_total, axis=0)
    target_class_freq_by_image_mask = np.concatenate(target_class_freq_by_image_mask, axis=0)
    pred_class_freq_by_image_mask = np.concatenate(pred_class_freq_by_image_mask, axis=0)
    target_class_freq_by_image_total_marginal = target_class_freq_by_image_total.sum(0).astype('float32')
    target_class_freq_by_image_total_marginal /= target_class_freq_by_image_total_marginal.sum()
    target_class_freq_by_image_mask_marginal = target_class_freq_by_image_mask.sum(0).astype('float32')
    target_class_freq_by_image_mask_marginal /= target_class_freq_by_image_mask_marginal.sum()
    pred_class_freq_diff = (pred_class_freq_by_image_mask - target_class_freq_by_image_mask).sum(0) / (target_class_freq_by_image_mask.sum(0) + 0.001)
    total_results = dict()
    total_results.update({f'total_freq/{self.segm_idx2name[i]}': v for i, v in enumerate(target_class_freq_by_image_total_marginal) if v > 0})
    total_results.update({f'mask_freq/{self.segm_idx2name[i]}': v for i, v in enumerate(target_class_freq_by_image_mask_marginal) if v > 0})
    total_results.update({f'mask_freq_diff/{self.segm_idx2name[i]}': v for i, v in enumerate(pred_class_freq_diff) if target_class_freq_by_image_total_marginal[i] > 0})
    if groups is None:
        return (total_results, None)
    group_results = dict()
    grouping = get_groupings(groups)
    for label, index in grouping.items():
        group_target_class_freq_by_image_total = target_class_freq_by_image_total[index]
        group_target_class_freq_by_image_mask = target_class_freq_by_image_mask[index]
        group_pred_class_freq_by_image_mask = pred_class_freq_by_image_mask[index]
        group_target_class_freq_by_image_total_marginal = group_target_class_freq_by_image_total.sum(0).astype('float32')
        group_target_class_freq_by_image_total_marginal /= group_target_class_freq_by_image_total_marginal.sum()
        group_target_class_freq_by_image_mask_marginal = group_target_class_freq_by_image_mask.sum(0).astype('float32')
        group_target_class_freq_by_image_mask_marginal /= group_target_class_freq_by_image_mask_marginal.sum()
        group_pred_class_freq_diff = (group_pred_class_freq_by_image_mask - group_target_class_freq_by_image_mask).sum(0) / (group_target_class_freq_by_image_mask.sum(0) + 0.001)
        cur_group_results = dict()
        cur_group_results.update({f'total_freq/{self.segm_idx2name[i]}': v for i, v in enumerate(group_target_class_freq_by_image_total_marginal) if v > 0})
        cur_group_results.update({f'mask_freq/{self.segm_idx2name[i]}': v for i, v in enumerate(group_target_class_freq_by_image_mask_marginal) if v > 0})
        cur_group_results.update({f'mask_freq_diff/{self.segm_idx2name[i]}': v for i, v in enumerate(group_pred_class_freq_diff) if group_target_class_freq_by_image_total_marginal[i] > 0})
        group_results[label] = cur_group_results
    return (total_results, group_results)

class SegmentationAwareSSIM(SegmentationAwarePairwiseScore):

    def __init__(self, *args, window_size=11, **kwargs):
        super().__init__(*args, **kwargs)
        self.score_impl = SSIM(window_size=window_size, size_average=False).eval()

    def calc_score(self, pred_batch, target_batch, mask):
        return self.score_impl(pred_batch, target_batch).detach().cpu().numpy()

def calc_score(self, pred_batch, target_batch, mask):
    return self.score_impl(pred_batch, target_batch).detach().cpu().numpy()

class SegmentationAwareLPIPS(SegmentationAwarePairwiseScore):

    def __init__(self, *args, model='net-lin', net='vgg', model_path=None, use_gpu=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.score_impl = PerceptualLoss(model=model, net=net, model_path=model_path, use_gpu=use_gpu, spatial=False).eval()

    def calc_score(self, pred_batch, target_batch, mask):
        return self.score_impl(pred_batch, target_batch).flatten().detach().cpu().numpy()

def calc_score(self, pred_batch, target_batch, mask):
    return self.score_impl(pred_batch, target_batch).flatten().detach().cpu().numpy()

class SegmentationAwareFID(SegmentationAwarePairwiseScore):

    def __init__(self, *args, dims=2048, eps=1e-06, n_jobs=-1, **kwargs):
        super().__init__(*args, **kwargs)
        if getattr(FIDScore, '_MODEL', None) is None:
            block_idx = InceptionV3.BLOCK_INDEX_BY_DIM[dims]
            FIDScore._MODEL = InceptionV3([block_idx]).eval()
        self.model = FIDScore._MODEL
        self.eps = eps
        self.n_jobs = n_jobs

    def calc_score(self, pred_batch, target_batch, mask):
        activations_pred = self._get_activations(pred_batch)
        activations_target = self._get_activations(target_batch)
        return (activations_pred, activations_target)

    def get_value(self, groups=None, states=None):
        """
        :param groups:
        :return:
            total_results: dict of kind {'mean': score mean, 'std': score std}
            group_results: None, if groups is None;
                else dict {group_idx: {'mean': score mean among group, 'std': score std among group}}
        """
        if states is not None:
            target_class_freq_by_image_total, target_class_freq_by_image_mask, pred_class_freq_by_image_mask, activation_pairs = states
        else:
            target_class_freq_by_image_total = self.target_class_freq_by_image_total
            target_class_freq_by_image_mask = self.target_class_freq_by_image_mask
            pred_class_freq_by_image_mask = self.pred_class_freq_by_image_mask
            activation_pairs = self.individual_values
        target_class_freq_by_image_total = np.concatenate(target_class_freq_by_image_total, axis=0)
        target_class_freq_by_image_mask = np.concatenate(target_class_freq_by_image_mask, axis=0)
        pred_class_freq_by_image_mask = np.concatenate(pred_class_freq_by_image_mask, axis=0)
        activations_pred, activations_target = zip(*activation_pairs)
        activations_pred = np.concatenate(activations_pred, axis=0)
        activations_target = np.concatenate(activations_target, axis=0)
        total_results = {'mean': calculate_frechet_distance(activations_pred, activations_target, eps=self.eps), 'std': 0, **self.distribute_fid_to_classes(target_class_freq_by_image_mask, activations_pred, activations_target)}
        if groups is None:
            return (total_results, None)
        group_results = dict()
        grouping = get_groupings(groups)
        for label, index in grouping.items():
            if len(index) > 1:
                group_activations_pred = activations_pred[index]
                group_activations_target = activations_target[index]
                group_class_freq = target_class_freq_by_image_mask[index]
                group_results[label] = {'mean': calculate_frechet_distance(group_activations_pred, group_activations_target, eps=self.eps), 'std': 0, **self.distribute_fid_to_classes(group_class_freq, group_activations_pred, group_activations_target)}
            else:
                group_results[label] = dict(mean=float('nan'), std=0)
        return (total_results, group_results)

    def distribute_fid_to_classes(self, class_freq, activations_pred, activations_target):
        real_fid = calculate_frechet_distance(activations_pred, activations_target, eps=self.eps)
        fid_no_images = Parallel(n_jobs=self.n_jobs)((delayed(calculade_fid_no_img)(img_i, activations_pred, activations_target, eps=self.eps) for img_i in range(activations_pred.shape[0])))
        errors = real_fid - fid_no_images
        return distribute_values_to_classes(class_freq, errors, self.segm_idx2name)

    def _get_activations(self, batch):
        activations = self.model(batch)[0]
        if activations.shape[2] != 1 or activations.shape[3] != 1:
            activations = F.adaptive_avg_pool2d(activations, output_size=(1, 1))
        activations = activations.squeeze(-1).squeeze(-1).detach().cpu().numpy()
        return activations

def calc_score(self, pred_batch, target_batch, mask):
    activations_pred = self._get_activations(pred_batch)
    activations_target = self._get_activations(target_batch)
    return (activations_pred, activations_target)

def get_value(self, groups=None, states=None):
    """
        :param groups:
        :return:
            total_results: dict of kind {'mean': score mean, 'std': score std}
            group_results: None, if groups is None;
                else dict {group_idx: {'mean': score mean among group, 'std': score std among group}}
        """
    if states is not None:
        target_class_freq_by_image_total, target_class_freq_by_image_mask, pred_class_freq_by_image_mask, activation_pairs = states
    else:
        target_class_freq_by_image_total = self.target_class_freq_by_image_total
        target_class_freq_by_image_mask = self.target_class_freq_by_image_mask
        pred_class_freq_by_image_mask = self.pred_class_freq_by_image_mask
        activation_pairs = self.individual_values
    target_class_freq_by_image_total = np.concatenate(target_class_freq_by_image_total, axis=0)
    target_class_freq_by_image_mask = np.concatenate(target_class_freq_by_image_mask, axis=0)
    pred_class_freq_by_image_mask = np.concatenate(pred_class_freq_by_image_mask, axis=0)
    activations_pred, activations_target = zip(*activation_pairs)
    activations_pred = np.concatenate(activations_pred, axis=0)
    activations_target = np.concatenate(activations_target, axis=0)
    total_results = {'mean': calculate_frechet_distance(activations_pred, activations_target, eps=self.eps), 'std': 0, **self.distribute_fid_to_classes(target_class_freq_by_image_mask, activations_pred, activations_target)}
    if groups is None:
        return (total_results, None)
    group_results = dict()
    grouping = get_groupings(groups)
    for label, index in grouping.items():
        if len(index) > 1:
            group_activations_pred = activations_pred[index]
            group_activations_target = activations_target[index]
            group_class_freq = target_class_freq_by_image_mask[index]
            group_results[label] = {'mean': calculate_frechet_distance(group_activations_pred, group_activations_target, eps=self.eps), 'std': 0, **self.distribute_fid_to_classes(group_class_freq, group_activations_pred, group_activations_target)}
        else:
            group_results[label] = dict(mean=float('nan'), std=0)
    return (total_results, group_results)

def distribute_fid_to_classes(self, class_freq, activations_pred, activations_target):
    real_fid = calculate_frechet_distance(activations_pred, activations_target, eps=self.eps)
    fid_no_images = Parallel(n_jobs=self.n_jobs)((delayed(calculade_fid_no_img)(img_i, activations_pred, activations_target, eps=self.eps) for img_i in range(activations_pred.shape[0])))
    errors = real_fid - fid_no_images
    return distribute_values_to_classes(class_freq, errors, self.segm_idx2name)

def _get_activations(self, batch):
    activations = self.model(batch)[0]
    if activations.shape[2] != 1 or activations.shape[3] != 1:
        activations = F.adaptive_avg_pool2d(activations, output_size=(1, 1))
    activations = activations.squeeze(-1).squeeze(-1).detach().cpu().numpy()
    return activations

class SSIM(torch.nn.Module):
    """SSIM. Modified from:
    https://github.com/Po-Hsun-Su/pytorch-ssim/blob/master/pytorch_ssim/__init__.py
    """

    def __init__(self, window_size=11, size_average=True):
        super().__init__()
        self.window_size = window_size
        self.size_average = size_average
        self.channel = 1
        self.register_buffer('window', self._create_window(window_size, self.channel))

    def forward(self, img1, img2):
        assert len(img1.shape) == 4
        channel = img1.size()[1]
        if channel == self.channel and self.window.data.type() == img1.data.type():
            window = self.window
        else:
            window = self._create_window(self.window_size, channel)
            window = window.type_as(img1)
            self.window = window
            self.channel = channel
        return self._ssim(img1, img2, window, self.window_size, channel, self.size_average)

    def _gaussian(self, window_size, sigma):
        gauss = torch.Tensor([np.exp(-(x - window_size // 2) ** 2 / float(2 * sigma ** 2)) for x in range(window_size)])
        return gauss / gauss.sum()

    def _create_window(self, window_size, channel):
        _1D_window = self._gaussian(window_size, 1.5).unsqueeze(1)
        _2D_window = _1D_window.mm(_1D_window.t()).float().unsqueeze(0).unsqueeze(0)
        return _2D_window.expand(channel, 1, window_size, window_size).contiguous()

    def _ssim(self, img1, img2, window, window_size, channel, size_average=True):
        mu1 = F.conv2d(img1, window, padding=window_size // 2, groups=channel)
        mu2 = F.conv2d(img2, window, padding=window_size // 2, groups=channel)
        mu1_sq = mu1.pow(2)
        mu2_sq = mu2.pow(2)
        mu1_mu2 = mu1 * mu2
        sigma1_sq = F.conv2d(img1 * img1, window, padding=window_size // 2, groups=channel) - mu1_sq
        sigma2_sq = F.conv2d(img2 * img2, window, padding=window_size // 2, groups=channel) - mu2_sq
        sigma12 = F.conv2d(img1 * img2, window, padding=window_size // 2, groups=channel) - mu1_mu2
        C1 = 0.01 ** 2
        C2 = 0.03 ** 2
        ssim_map = (2 * mu1_mu2 + C1) * (2 * sigma12 + C2) / ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
        if size_average:
            return ssim_map.mean()
        return ssim_map.mean(1).mean(1).mean(1)

    def _load_from_state_dict(self, state_dict, prefix, local_metadata, strict, missing_keys, unexpected_keys, error_msgs):
        return

def _ssim(self, img1, img2, window, window_size, channel, size_average=True):
    mu1 = F.conv2d(img1, window, padding=window_size // 2, groups=channel)
    mu2 = F.conv2d(img2, window, padding=window_size // 2, groups=channel)
    mu1_sq = mu1.pow(2)
    mu2_sq = mu2.pow(2)
    mu1_mu2 = mu1 * mu2
    sigma1_sq = F.conv2d(img1 * img1, window, padding=window_size // 2, groups=channel) - mu1_sq
    sigma2_sq = F.conv2d(img2 * img2, window, padding=window_size // 2, groups=channel) - mu2_sq
    sigma12 = F.conv2d(img1 * img2, window, padding=window_size // 2, groups=channel) - mu1_mu2
    C1 = 0.01 ** 2
    C2 = 0.03 ** 2
    ssim_map = (2 * mu1_mu2 + C1) * (2 * sigma12 + C2) / ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
    if size_average:
        return ssim_map.mean()
    return ssim_map.mean(1).mean(1).mean(1)

def l2(p0, p1, range=255.0):
    return 0.5 * np.mean((p0 / range - p1 / range) ** 2)

def psnr(p0, p1, peak=255.0):
    return 10 * np.log10(peak ** 2 / np.mean((1.0 * p0 - 1.0 * p1) ** 2))

def tensor2np(tensor_obj):
    return tensor_obj[0].cpu().float().numpy().transpose((1, 2, 0))

def tensor2vec(vector_tensor):
    return vector_tensor.data.cpu().numpy()[:, :, 0, 0]

class DistModel(BaseModel):

    def name(self):
        return self.model_name

    def initialize(self, model='net-lin', net='alex', colorspace='Lab', pnet_rand=False, pnet_tune=False, model_path=None, use_gpu=True, printNet=False, spatial=False, is_train=False, lr=0.0001, beta1=0.5, version='0.1'):
        """
        INPUTS
            model - ['net-lin'] for linearly calibrated network
                    ['net'] for off-the-shelf network
                    ['L2'] for L2 distance in Lab colorspace
                    ['SSIM'] for ssim in RGB colorspace
            net - ['squeeze','alex','vgg']
            model_path - if None, will look in weights/[NET_NAME].pth
            colorspace - ['Lab','RGB'] colorspace to use for L2 and SSIM
            use_gpu - bool - whether or not to use a GPU
            printNet - bool - whether or not to print network architecture out
            spatial - bool - whether to output an array containing varying distances across spatial dimensions
            spatial_shape - if given, output spatial shape. if None then spatial shape is determined automatically via spatial_factor (see below).
            spatial_factor - if given, specifies upsampling factor relative to the largest spatial extent of a convolutional layer. if None then resized to size of input images.
            spatial_order - spline order of filter for upsampling in spatial mode, by default 1 (bilinear).
            is_train - bool - [True] for training mode
            lr - float - initial learning rate
            beta1 - float - initial momentum term for adam
            version - 0.1 for latest, 0.0 was original (with a bug)
        """
        BaseModel.initialize(self, use_gpu=use_gpu)
        self.model = model
        self.net = net
        self.is_train = is_train
        self.spatial = spatial
        self.model_name = '%s [%s]' % (model, net)
        if self.model == 'net-lin':
            self.net = PNetLin(pnet_rand=pnet_rand, pnet_tune=pnet_tune, pnet_type=net, use_dropout=True, spatial=spatial, version=version, lpips=True)
            kw = dict(map_location='cpu')
            if model_path is None:
                import inspect
                model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'models', 'lpips_models', f'{net}.pth'))
            if not is_train:
                self.net.load_state_dict(torch.load(model_path, **kw), strict=False)
        elif self.model == 'net':
            self.net = PNetLin(pnet_rand=pnet_rand, pnet_type=net, lpips=False)
        elif self.model in ['L2', 'l2']:
            self.net = L2(use_gpu=use_gpu, colorspace=colorspace)
            self.model_name = 'L2'
        elif self.model in ['DSSIM', 'dssim', 'SSIM', 'ssim']:
            self.net = DSSIM(use_gpu=use_gpu, colorspace=colorspace)
            self.model_name = 'SSIM'
        else:
            raise ValueError('Model [%s] not recognized.' % self.model)
        self.trainable_parameters = list(self.net.parameters())
        if self.is_train:
            self.rankLoss = BCERankingLoss()
            self.trainable_parameters += list(self.rankLoss.net.parameters())
            self.lr = lr
            self.old_lr = lr
            self.optimizer_net = torch.optim.Adam(self.trainable_parameters, lr=lr, betas=(beta1, 0.999))
        else:
            self.net.eval()
        if printNet:
            print('---------- Networks initialized -------------')
            print_network(self.net)
            print('-----------------------------------------------')

    def forward(self, in0, in1, retPerLayer=False):
        """ Function computes the distance between image patches in0 and in1
        INPUTS
            in0, in1 - torch.Tensor object of shape Nx3xXxY - image patch scaled to [-1,1]
        OUTPUT
            computed distances between in0 and in1
        """
        return self.net(in0, in1, retPerLayer=retPerLayer)

    def optimize_parameters(self):
        self.forward_train()
        self.optimizer_net.zero_grad()
        self.backward_train()
        self.optimizer_net.step()
        self.clamp_weights()

    def clamp_weights(self):
        for module in self.net.modules():
            if hasattr(module, 'weight') and module.kernel_size == (1, 1):
                module.weight.data = torch.clamp(module.weight.data, min=0)

    def set_input(self, data):
        self.input_ref = data['ref']
        self.input_p0 = data['p0']
        self.input_p1 = data['p1']
        self.input_judge = data['judge']

    def forward_train(self):
        assert False, "We shoud've not get here when using LPIPS as a metric"
        self.d0 = self(self.var_ref, self.var_p0)
        self.d1 = self(self.var_ref, self.var_p1)
        self.acc_r = self.compute_accuracy(self.d0, self.d1, self.input_judge)
        self.var_judge = Variable(1.0 * self.input_judge).view(self.d0.size())
        self.loss_total = self.rankLoss(self.d0, self.d1, self.var_judge * 2.0 - 1.0)
        return self.loss_total

    def backward_train(self):
        torch.mean(self.loss_total).backward()

    def compute_accuracy(self, d0, d1, judge):
        """ d0, d1 are Variables, judge is a Tensor """
        d1_lt_d0 = (d1 < d0).cpu().data.numpy().flatten()
        judge_per = judge.cpu().numpy().flatten()
        return d1_lt_d0 * judge_per + (1 - d1_lt_d0) * (1 - judge_per)

    def get_current_errors(self):
        retDict = OrderedDict([('loss_total', self.loss_total.data.cpu().numpy()), ('acc_r', self.acc_r)])
        for key in retDict.keys():
            retDict[key] = np.mean(retDict[key])
        return retDict

    def get_current_visuals(self):
        zoom_factor = 256 / self.var_ref.data.size()[2]
        ref_img = tensor2im(self.var_ref.data)
        p0_img = tensor2im(self.var_p0.data)
        p1_img = tensor2im(self.var_p1.data)
        ref_img_vis = zoom(ref_img, [zoom_factor, zoom_factor, 1], order=0)
        p0_img_vis = zoom(p0_img, [zoom_factor, zoom_factor, 1], order=0)
        p1_img_vis = zoom(p1_img, [zoom_factor, zoom_factor, 1], order=0)
        return OrderedDict([('ref', ref_img_vis), ('p0', p0_img_vis), ('p1', p1_img_vis)])

    def save(self, path, label):
        if self.use_gpu:
            self.save_network(self.net.module, path, '', label)
        else:
            self.save_network(self.net, path, '', label)
        self.save_network(self.rankLoss.net, path, 'rank', label)

    def update_learning_rate(self, nepoch_decay):
        lrd = self.lr / nepoch_decay
        lr = self.old_lr - lrd
        for param_group in self.optimizer_net.param_groups:
            param_group['lr'] = lr
        print('update lr [%s] decay: %f -> %f' % (type, self.old_lr, lr))
        self.old_lr = lr

def compute_accuracy(self, d0, d1, judge):
    """ d0, d1 are Variables, judge is a Tensor """
    d1_lt_d0 = (d1 < d0).cpu().data.numpy().flatten()
    judge_per = judge.cpu().numpy().flatten()
    return d1_lt_d0 * judge_per + (1 - d1_lt_d0) * (1 - judge_per)

def get_current_errors(self):
    retDict = OrderedDict([('loss_total', self.loss_total.data.cpu().numpy()), ('acc_r', self.acc_r)])
    for key in retDict.keys():
        retDict[key] = np.mean(retDict[key])
    return retDict

def score_2afc_dataset(data_loader, func, name=''):
    """ Function computes Two Alternative Forced Choice (2AFC) score using
        distance function 'func' in dataset 'data_loader'
    INPUTS
        data_loader - CustomDatasetDataLoader object - contains a TwoAFCDataset inside
        func - callable distance function - calling d=func(in0,in1) should take 2
            pytorch tensors with shape Nx3xXxY, and return numpy array of length N
    OUTPUTS
        [0] - 2AFC score in [0,1], fraction of time func agrees with human evaluators
        [1] - dictionary with following elements
            d0s,d1s - N arrays containing distances between reference patch to perturbed patches
            gts - N array in [0,1], preferred patch selected by human evaluators
                (closer to "0" for left patch p0, "1" for right patch p1,
                "0.6" means 60pct people preferred right patch, 40pct preferred left)
            scores - N array in [0,1], corresponding to what percentage function agreed with humans
    CONSTS
        N - number of test triplets in data_loader
    """
    d0s = []
    d1s = []
    gts = []
    for data in tqdm(data_loader.load_data(), desc=name):
        d0s += func(data['ref'], data['p0']).data.cpu().numpy().flatten().tolist()
        d1s += func(data['ref'], data['p1']).data.cpu().numpy().flatten().tolist()
        gts += data['judge'].cpu().numpy().flatten().tolist()
    d0s = np.array(d0s)
    d1s = np.array(d1s)
    gts = np.array(gts)
    scores = (d0s < d1s) * (1.0 - gts) + (d1s < d0s) * gts + (d1s == d0s) * 0.5
    return (np.mean(scores), dict(d0s=d0s, d1s=d1s, gts=gts, scores=scores))

def score_jnd_dataset(data_loader, func, name=''):
    """ Function computes JND score using distance function 'func' in dataset 'data_loader'
    INPUTS
        data_loader - CustomDatasetDataLoader object - contains a JNDDataset inside
        func - callable distance function - calling d=func(in0,in1) should take 2
            pytorch tensors with shape Nx3xXxY, and return pytorch array of length N
    OUTPUTS
        [0] - JND score in [0,1], mAP score (area under precision-recall curve)
        [1] - dictionary with following elements
            ds - N array containing distances between two patches shown to human evaluator
            sames - N array containing fraction of people who thought the two patches were identical
    CONSTS
        N - number of test triplets in data_loader
    """
    ds = []
    gts = []
    for data in tqdm(data_loader.load_data(), desc=name):
        ds += func(data['p0'], data['p1']).data.cpu().numpy().tolist()
        gts += data['same'].cpu().numpy().flatten().tolist()
    sames = np.array(gts)
    ds = np.array(ds)
    sorted_inds = np.argsort(ds)
    ds_sorted = ds[sorted_inds]
    sames_sorted = sames[sorted_inds]
    TPs = np.cumsum(sames_sorted)
    FPs = np.cumsum(1 - sames_sorted)
    FNs = np.sum(sames_sorted) - TPs
    precs = TPs / (TPs + FPs)
    recs = TPs / (TPs + FNs)
    score = voc_ap(recs, precs)
    return (score, dict(ds=ds, sames=sames))

def spatial_average(in_tens, keepdim=True):
    return in_tens.mean([2, 3], keepdim=keepdim)

def print_network(net):
    num_params = 0
    for param in net.parameters():
        num_params += param.numel()
    print('Network', net)
    print('Total number of parameters: %d' % num_params)

def get_activations(files, model, batch_size=50, dims=2048, cuda=False, verbose=False, keep_size=False):
    """Calculates the activations of the pool_3 layer for all images.

    Params:
    -- files       : List of image files paths
    -- model       : Instance of inception model
    -- batch_size  : Batch size of images for the model to process at once.
                     Make sure that the number of samples is a multiple of
                     the batch size, otherwise some samples are ignored. This
                     behavior is retained to match the original FID score
                     implementation.
    -- dims        : Dimensionality of features returned by Inception
    -- cuda        : If set to True, use GPU
    -- verbose     : If set to True and parameter out_step is given, the number
                     of calculated batches is reported.
    Returns:
    -- A numpy array of dimension (num images, dims) that contains the
       activations of the given tensor when feeding inception with the
       query tensor.
    """
    model.eval()
    if len(files) % batch_size != 0:
        print('Warning: number of images is not a multiple of the batch size. Some samples are going to be ignored.')
    if batch_size > len(files):
        print('Warning: batch size is bigger than the data size. Setting batch size to data size')
        batch_size = len(files)
    n_batches = len(files) // batch_size
    n_used_imgs = n_batches * batch_size
    pred_arr = np.empty((n_used_imgs, dims))
    for i in tqdm(range(n_batches)):
        if verbose:
            print('\rPropagating batch %d/%d' % (i + 1, n_batches), end='', flush=True)
        start = i * batch_size
        end = start + batch_size
        t = transform if not keep_size else ToTensor()
        if isinstance(files[0], pathlib.PosixPath):
            images = [t(Image.open(str(f))) for f in files[start:end]]
        elif isinstance(files[0], Image.Image):
            images = [t(f) for f in files[start:end]]
        else:
            raise ValueError(f'Unknown data type for image: {type(files[0])}')
        batch = torch.stack(images)
        if cuda:
            batch = batch.cuda()
        pred = model(batch)[0]
        if pred.shape[2] != 1 or pred.shape[3] != 1:
            pred = adaptive_avg_pool2d(pred, output_size=(1, 1))
        pred_arr[start:end] = pred.cpu().data.numpy().reshape(batch_size, -1)
    if verbose:
        print(' done')
    return pred_arr

def calculate_activation_statistics(files, model, batch_size=50, dims=2048, cuda=False, verbose=False, keep_size=False):
    """Calculation of the statistics used by the FID.
    Params:
    -- files       : List of image files paths
    -- model       : Instance of inception model
    -- batch_size  : The images numpy array is split into batches with
                     batch size batch_size. A reasonable batch size
                     depends on the hardware.
    -- dims        : Dimensionality of features returned by Inception
    -- cuda        : If set to True, use GPU
    -- verbose     : If set to True and parameter out_step is given, the
                     number of calculated batches is reported.
    Returns:
    -- mu    : The mean over samples of the activations of the pool_3 layer of
               the inception model.
    -- sigma : The covariance matrix of the activations of the pool_3 layer of
               the inception model.
    """
    act = get_activations(files, model, batch_size, dims, cuda, verbose, keep_size=keep_size)
    mu = np.mean(act, axis=0)
    sigma = np.cov(act, rowvar=False)
    return (mu, sigma)

def calculate_fid_given_paths(paths, batch_size, cuda, dims):
    """Calculates the FID of two paths"""
    for p in paths:
        if not os.path.exists(p):
            raise RuntimeError('Invalid path: %s' % p)
    block_idx = InceptionV3.BLOCK_INDEX_BY_DIM[dims]
    model = InceptionV3([block_idx])
    if cuda:
        model.cuda()
    m1, s1 = _compute_statistics_of_path(paths[0], model, batch_size, dims, cuda)
    m2, s2 = _compute_statistics_of_path(paths[1], model, batch_size, dims, cuda)
    fid_value = calculate_frechet_distance(m1, s1, m2, s2)
    return fid_value

def calculate_fid_given_images(images, batch_size, cuda, dims, use_globals=False, keep_size=False):
    if use_globals:
        global FID_MODEL
    for imgs in images:
        if isinstance(imgs, list) and isinstance(imgs[0], (Image.Image, JpegImagePlugin.JpegImageFile)):
            pass
        else:
            raise RuntimeError('Invalid images')
    block_idx = InceptionV3.BLOCK_INDEX_BY_DIM[dims]
    if 'FID_MODEL' not in globals() or not use_globals:
        model = InceptionV3([block_idx])
        if cuda:
            model.cuda()
        if use_globals:
            FID_MODEL = model
    else:
        model = FID_MODEL
    m1, s1 = _compute_statistics_of_images(images[0], model, batch_size, dims, cuda, keep_size=False)
    m2, s2 = _compute_statistics_of_images(images[1], model, batch_size, dims, cuda, keep_size=False)
    fid_value = calculate_frechet_distance(m1, s1, m2, s2)
    return fid_value

class SegmentationMask:

    def __init__(self, confidence_threshold=0.5, rigidness_mode=RigidnessMode.rigid, max_object_area=0.3, min_mask_area=0.02, downsample_levels=6, num_variants_per_mask=4, max_mask_intersection=0.5, max_foreground_coverage=0.5, max_foreground_intersection=0.5, max_hidden_area=0.2, max_scale_change=0.25, horizontal_flip=True, max_vertical_shift=0.1, position_shuffle=True):
        """
        :param confidence_threshold: float; threshold for confidence of the panoptic segmentator to allow for
        the instance.
        :param rigidness_mode: RigidnessMode object
            when soft, checks intersection only with the object from which the mask_object was produced
            when rigid, checks intersection with any foreground class object
        :param max_object_area: float; allowed upper bound for to be considered as mask_object.
        :param min_mask_area: float; lower bound for mask to be considered valid
        :param downsample_levels: int; defines width of the resized segmentation to obtain shifted masks;
        :param num_variants_per_mask: int; maximal number of the masks for the same object;
        :param max_mask_intersection: float; maximum allowed area fraction of intersection for 2 masks
        produced by horizontal shift of the same mask_object; higher value -> more diversity
        :param max_foreground_coverage: float; maximum allowed area fraction of intersection for foreground object to be
        covered by mask; lower value -> less the objects are covered
        :param max_foreground_intersection: float; maximum allowed area of intersection for the mask with foreground
        object; lower value -> mask is more on the background than on the objects
        :param max_hidden_area: upper bound on part of the object hidden by shifting object outside the screen area;
        :param max_scale_change: allowed scale change for the mask_object;
        :param horizontal_flip: if horizontal flips are allowed;
        :param max_vertical_shift: amount of vertical movement allowed;
        :param position_shuffle: shuffle
        """
        assert DETECTRON_INSTALLED, 'Cannot use SegmentationMask without detectron2'
        self.cfg = get_cfg()
        self.cfg.merge_from_file(model_zoo.get_config_file('COCO-PanopticSegmentation/panoptic_fpn_R_101_3x.yaml'))
        self.cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url('COCO-PanopticSegmentation/panoptic_fpn_R_101_3x.yaml')
        self.cfg.MODEL.PANOPTIC_FPN.COMBINE.INSTANCES_CONFIDENCE_THRESH = confidence_threshold
        self.predictor = DefaultPredictor(self.cfg)
        self.rigidness_mode = RigidnessMode(rigidness_mode)
        self.max_object_area = max_object_area
        self.min_mask_area = min_mask_area
        self.downsample_levels = downsample_levels
        self.num_variants_per_mask = num_variants_per_mask
        self.max_mask_intersection = max_mask_intersection
        self.max_foreground_coverage = max_foreground_coverage
        self.max_foreground_intersection = max_foreground_intersection
        self.max_hidden_area = max_hidden_area
        self.position_shuffle = position_shuffle
        self.max_scale_change = max_scale_change
        self.horizontal_flip = horizontal_flip
        self.max_vertical_shift = max_vertical_shift

    def get_segmentation(self, img):
        im = img_as_ubyte(img)
        panoptic_seg, segment_info = self.predictor(im)['panoptic_seg']
        return (panoptic_seg, segment_info)

    @staticmethod
    def _is_power_of_two(n):
        return n != 0 and n & n - 1 == 0

    def identify_candidates(self, panoptic_seg, segments_info):
        potential_mask_ids = []
        for segment in segments_info:
            if not segment['isthing']:
                continue
            mask = (panoptic_seg == segment['id']).int().detach().cpu().numpy()
            area = mask.sum().item() / np.prod(panoptic_seg.shape)
            if area >= self.max_object_area:
                continue
            potential_mask_ids.append(segment['id'])
        return potential_mask_ids

    def downsample_mask(self, mask):
        height, width = mask.shape
        if not (self._is_power_of_two(height) and self._is_power_of_two(width)):
            raise ValueError('Image sides are not power of 2.')
        num_iterations = width.bit_length() - 1 - self.downsample_levels
        if num_iterations < 0:
            raise ValueError(f'Width is lower than 2^{self.downsample_levels}.')
        if height.bit_length() - 1 < num_iterations:
            raise ValueError('Height is too low to perform downsampling')
        downsampled = mask
        for _ in range(num_iterations):
            downsampled = zero_corrected_countless(downsampled)
        return downsampled

    def _augmentation_params(self):
        scaling_factor = np.random.uniform(1 - self.max_scale_change, 1 + self.max_scale_change)
        if self.horizontal_flip:
            horizontal_flip = bool(np.random.choice(2))
        else:
            horizontal_flip = False
        vertical_shift = np.random.uniform(-self.max_vertical_shift, self.max_vertical_shift)
        return {'scaling_factor': scaling_factor, 'horizontal_flip': horizontal_flip, 'vertical_shift': vertical_shift}

    def _get_intersection(self, mask_array, mask_object):
        intersection = mask_array[mask_object.up:mask_object.down, mask_object.left:mask_object.right] & mask_object.mask
        return intersection

    def _check_masks_intersection(self, aug_mask, total_mask_area, prev_masks):
        for existing_mask in prev_masks:
            intersection_area = self._get_intersection(existing_mask, aug_mask).sum()
            intersection_existing = intersection_area / existing_mask.sum()
            intersection_current = 1 - (aug_mask.area() - intersection_area) / total_mask_area
            if intersection_existing > self.max_mask_intersection or intersection_current > self.max_mask_intersection:
                return False
        return True

    def _check_foreground_intersection(self, aug_mask, foreground):
        for existing_mask in foreground:
            intersection_area = self._get_intersection(existing_mask, aug_mask).sum()
            intersection_existing = intersection_area / existing_mask.sum()
            if intersection_existing > self.max_foreground_coverage:
                return False
            intersection_mask = intersection_area / aug_mask.area()
            if intersection_mask > self.max_foreground_intersection:
                return False
        return True

    def _move_mask(self, mask, foreground):
        orig_mask = ObjectMask(mask)
        chosen_masks = []
        chosen_parameters = []
        scaling_factor_lower_bound = 0.0
        for var_idx in range(self.num_variants_per_mask):
            augmentation_params = self._augmentation_params()
            augmentation_params['scaling_factor'] = min([augmentation_params['scaling_factor'], 2 * min(orig_mask.up, orig_mask.height - orig_mask.down) / orig_mask.height + 1.0, 2 * min(orig_mask.left, orig_mask.width - orig_mask.right) / orig_mask.width + 1.0])
            augmentation_params['scaling_factor'] = max([augmentation_params['scaling_factor'], scaling_factor_lower_bound])
            aug_mask = deepcopy(orig_mask)
            aug_mask.rescale(augmentation_params['scaling_factor'], inplace=True)
            if augmentation_params['horizontal_flip']:
                aug_mask.horizontal_flip(inplace=True)
            total_aug_area = aug_mask.area()
            if total_aug_area == 0:
                scaling_factor_lower_bound = 1.0
                continue
            vertical_area = aug_mask.mask.sum(axis=1) / total_aug_area
            max_hidden_up = np.searchsorted(vertical_area.cumsum(), self.max_hidden_area)
            max_hidden_down = np.searchsorted(vertical_area[::-1].cumsum(), self.max_hidden_area)
            augmentation_params['vertical_shift'] = np.clip(augmentation_params['vertical_shift'], -(aug_mask.up + max_hidden_up) / aug_mask.height, (aug_mask.height - aug_mask.down + max_hidden_down) / aug_mask.height)
            vertical_shift = int(round(aug_mask.height * augmentation_params['vertical_shift']))
            aug_mask.shift(vertical=vertical_shift, inplace=True)
            aug_mask.crop_to_canvas(vertical=True, horizontal=False, inplace=True)
            max_hidden_area = self.max_hidden_area - (1 - aug_mask.area() / total_aug_area)
            horizontal_area = aug_mask.mask.sum(axis=0) / total_aug_area
            max_hidden_left = np.searchsorted(horizontal_area.cumsum(), max_hidden_area)
            max_hidden_right = np.searchsorted(horizontal_area[::-1].cumsum(), max_hidden_area)
            allowed_shifts = np.arange(-max_hidden_left, aug_mask.width - (aug_mask.right - aug_mask.left) + max_hidden_right + 1)
            allowed_shifts = -(aug_mask.left - allowed_shifts)
            if self.position_shuffle:
                np.random.shuffle(allowed_shifts)
            mask_is_found = False
            for horizontal_shift in allowed_shifts:
                aug_mask_left = deepcopy(aug_mask)
                aug_mask_left.shift(horizontal=horizontal_shift, inplace=True)
                aug_mask_left.crop_to_canvas(inplace=True)
                prev_masks = [mask] + chosen_masks
                is_mask_suitable = self._check_masks_intersection(aug_mask_left, total_aug_area, prev_masks) & self._check_foreground_intersection(aug_mask_left, foreground)
                if is_mask_suitable:
                    aug_draw = aug_mask_left.restore_full_mask()
                    chosen_masks.append(aug_draw)
                    augmentation_params['horizontal_shift'] = horizontal_shift / aug_mask_left.width
                    chosen_parameters.append(augmentation_params)
                    mask_is_found = True
                    break
            if not mask_is_found:
                break
        return chosen_parameters

    def _prepare_mask(self, mask):
        height, width = mask.shape
        target_width = width if self._is_power_of_two(width) else 1 << width.bit_length()
        target_height = height if self._is_power_of_two(height) else 1 << height.bit_length()
        return resize(mask.astype('float32'), (target_height, target_width), order=0, mode='edge').round().astype('int32')

    def get_masks(self, im, return_panoptic=False):
        panoptic_seg, segments_info = self.get_segmentation(im)
        potential_mask_ids = self.identify_candidates(panoptic_seg, segments_info)
        panoptic_seg_scaled = self._prepare_mask(panoptic_seg.detach().cpu().numpy())
        downsampled = self.downsample_mask(panoptic_seg_scaled)
        scene_objects = []
        for segment in segments_info:
            if not segment['isthing']:
                continue
            mask = downsampled == segment['id']
            if not np.any(mask):
                continue
            scene_objects.append(mask)
        mask_set = []
        for mask_id in potential_mask_ids:
            mask = downsampled == mask_id
            if not np.any(mask):
                continue
            if self.rigidness_mode is RigidnessMode.soft:
                foreground = [mask]
            elif self.rigidness_mode is RigidnessMode.rigid:
                foreground = scene_objects
            else:
                raise ValueError(f'Unexpected rigidness_mode: {rigidness_mode}')
            masks_params = self._move_mask(mask, foreground)
            full_mask = ObjectMask((panoptic_seg == mask_id).detach().cpu().numpy())
            for params in masks_params:
                aug_mask = deepcopy(full_mask)
                aug_mask.rescale(params['scaling_factor'], inplace=True)
                if params['horizontal_flip']:
                    aug_mask.horizontal_flip(inplace=True)
                vertical_shift = int(round(aug_mask.height * params['vertical_shift']))
                horizontal_shift = int(round(aug_mask.width * params['horizontal_shift']))
                aug_mask.shift(vertical=vertical_shift, horizontal=horizontal_shift, inplace=True)
                aug_mask = aug_mask.restore_full_mask().astype('uint8')
                if aug_mask.mean() <= self.min_mask_area:
                    continue
                mask_set.append(aug_mask)
        if return_panoptic:
            return (mask_set, panoptic_seg.detach().cpu().numpy())
        else:
            return mask_set

def identify_candidates(self, panoptic_seg, segments_info):
    potential_mask_ids = []
    for segment in segments_info:
        if not segment['isthing']:
            continue
        mask = (panoptic_seg == segment['id']).int().detach().cpu().numpy()
        area = mask.sum().item() / np.prod(panoptic_seg.shape)
        if area >= self.max_object_area:
            continue
        potential_mask_ids.append(segment['id'])
    return potential_mask_ids

def async_copy_to(obj, dev, main_stream=None):
    if torch.is_tensor(obj):
        v = obj.cuda(dev, non_blocking=True)
        if main_stream is not None:
            v.data.record_stream(main_stream)
        return v
    elif isinstance(obj, collections.Mapping):
        return {k: async_copy_to(o, dev, main_stream) for k, o in obj.items()}
    elif isinstance(obj, collections.Sequence):
        return [async_copy_to(o, dev, main_stream) for o in obj]
    else:
        return obj

def gather_map(outputs):
    out = outputs[0]
    if torch.is_tensor(out):
        if out.dim() == 0:
            outputs = [o.unsqueeze(0) for o in outputs]
        return Gather.apply(target_device, dim, *outputs)
    elif out is None:
        return None
    elif isinstance(out, collections.Mapping):
        return {k: gather_map([o[k] for o in outputs]) for k in out}
    elif isinstance(out, collections.Sequence):
        return type(out)(map(gather_map, zip(*outputs)))

def dict_gather(outputs, target_device, dim=0):
    """
    Gathers variables from different GPUs on a specified device
      (-1 means the CPU), with dictionary support.
    """

    def gather_map(outputs):
        out = outputs[0]
        if torch.is_tensor(out):
            if out.dim() == 0:
                outputs = [o.unsqueeze(0) for o in outputs]
            return Gather.apply(target_device, dim, *outputs)
        elif out is None:
            return None
        elif isinstance(out, collections.Mapping):
            return {k: gather_map([o[k] for o in outputs]) for k in out}
        elif isinstance(out, collections.Sequence):
            return type(out)(map(gather_map, zip(*outputs)))
    return gather_map(outputs)

def patch_replication_callback(data_parallel):
    """
    Monkey-patch an existing `DataParallel` object. Add the replication callback.
    Useful when you have customized `DataParallel` implementation.

    Examples:
        > sync_bn = SynchronizedBatchNorm1d(10, eps=1e-5, affine=False)
        > sync_bn = DataParallel(sync_bn, device_ids=[0, 1])
        > patch_replication_callback(sync_bn)
        # this is equivalent to
        > sync_bn = SynchronizedBatchNorm1d(10, eps=1e-5, affine=False)
        > sync_bn = DataParallelWithCallback(sync_bn, device_ids=[0, 1])
    """
    assert isinstance(data_parallel, DataParallel)
    old_replicate = data_parallel.replicate

    @functools.wraps(old_replicate)
    def new_replicate(module, device_ids):
        modules = old_replicate(module, device_ids)
        execute_replication_callbacks(modules)
        return modules
    data_parallel.replicate = new_replicate

def as_numpy(v):
    if isinstance(v, Variable):
        v = v.data
    return v.cpu().numpy()

def _find_bn(module):
    for m in module.modules():
        if isinstance(m, (nn.BatchNorm1d, nn.BatchNorm2d, SynchronizedBatchNorm1d, SynchronizedBatchNorm2d)):
            return m

def as_variable(obj):
    if isinstance(obj, Variable):
        return obj
    if isinstance(obj, collections.Sequence):
        return [as_variable(v) for v in obj]
    elif isinstance(obj, collections.Mapping):
        return {k: as_variable(v) for k, v in obj.items()}
    else:
        return Variable(obj)

def as_numpy(obj):
    if isinstance(obj, collections.Sequence):
        return [as_numpy(v) for v in obj]
    elif isinstance(obj, collections.Mapping):
        return {k: as_numpy(v) for k, v in obj.items()}
    elif isinstance(obj, Variable):
        return obj.data.cpu().numpy()
    elif torch.is_tensor(obj):
        return obj.cpu().numpy()
    else:
        return np.array(obj)

def mark_volatile(obj):
    if torch.is_tensor(obj):
        obj = Variable(obj)
    if isinstance(obj, Variable):
        obj.no_grad = True
        return obj
    elif isinstance(obj, collections.Mapping):
        return {k: mark_volatile(o) for k, o in obj.items()}
    elif isinstance(obj, collections.Sequence):
        return [mark_volatile(o) for o in obj]
    else:
        return obj

def add_prefix_to_keys(dct, prefix):
    return {prefix + k: v for k, v in dct.items()}

def flatten_dict(dct):
    result = {}
    for k, v in dct.items():
        if isinstance(k, tuple):
            k = '_'.join(k)
        if isinstance(v, dict):
            for sub_k, sub_v in flatten_dict(v).items():
                result[f'{k}_{sub_k}'] = sub_v
        else:
            result[k] = v
    return result

def get_shape(t):
    if torch.is_tensor(t):
        return tuple(t.shape)
    elif isinstance(t, dict):
        return {n: get_shape(q) for n, q in t.items()}
    elif isinstance(t, (list, tuple)):
        return [get_shape(q) for q in t]
    elif isinstance(t, numbers.Number):
        return type(t)
    else:
        raise ValueError('unexpected type {}'.format(type(t)))

def masked_l2_loss(pred, target, mask, weight_known, weight_missing):
    per_pixel_l2 = F.mse_loss(pred, target, reduction='none')
    pixel_weights = mask * weight_missing + (1 - mask) * weight_known
    return (pixel_weights * per_pixel_l2).mean()

def feature_matching_loss(fake_features: List[torch.Tensor], target_features: List[torch.Tensor], mask=None):
    if mask is None:
        res = torch.stack([F.mse_loss(fake_feat, target_feat) for fake_feat, target_feat in zip(fake_features, target_features)]).mean()
    else:
        res = 0
        norm = 0
        for fake_feat, target_feat in zip(fake_features, target_features):
            cur_mask = F.interpolate(mask, size=fake_feat.shape[-2:], mode='bilinear', align_corners=False)
            error_weights = 1 - cur_mask
            cur_val = ((fake_feat - target_feat).pow(2) * error_weights).mean()
            res = res + cur_val
            norm += 1
        res = res / norm
    return res

def make_default_val_dataloader(*args, dataloader_kwargs=None, **kwargs):
    dataset = make_default_val_dataset(*args, **kwargs)
    if dataloader_kwargs is None:
        dataloader_kwargs = {}
    dataloader = DataLoader(dataset, **dataloader_kwargs)
    return dataloader

class BaseInpaintingTrainingModule(ptl.LightningModule):

    def __init__(self, config, use_ddp, *args, predict_only=False, visualize_each_iters=100, average_generator=False, generator_avg_beta=0.999, average_generator_start_step=30000, average_generator_period=10, store_discr_outputs_for_vis=False, **kwargs):
        super().__init__(*args, **kwargs)
        LOGGER.info('BaseInpaintingTrainingModule init called')
        self.config = config
        self.generator = make_generator(config, **self.config.generator)
        self.use_ddp = use_ddp
        if not get_has_ddp_rank():
            LOGGER.info(f'Generator\n{self.generator}')
        if not predict_only:
            self.save_hyperparameters(self.config)
            self.discriminator = make_discriminator(**self.config.discriminator)
            self.adversarial_loss = make_discrim_loss(**self.config.losses.adversarial)
            self.visualizer = make_visualizer(**self.config.visualizer)
            self.val_evaluator = make_evaluator(**self.config.evaluator)
            self.test_evaluator = make_evaluator(**self.config.evaluator)
            if not get_has_ddp_rank():
                LOGGER.info(f'Discriminator\n{self.discriminator}')
            extra_val = self.config.data.get('extra_val', ())
            if extra_val:
                self.extra_val_titles = list(extra_val)
                self.extra_evaluators = nn.ModuleDict({k: make_evaluator(**self.config.evaluator) for k in extra_val})
            else:
                self.extra_evaluators = {}
            self.average_generator = average_generator
            self.generator_avg_beta = generator_avg_beta
            self.average_generator_start_step = average_generator_start_step
            self.average_generator_period = average_generator_period
            self.generator_average = None
            self.last_generator_averaging_step = -1
            self.store_discr_outputs_for_vis = store_discr_outputs_for_vis
            if self.config.losses.get('l1', {'weight_known': 0})['weight_known'] > 0:
                self.loss_l1 = nn.L1Loss(reduction='none')
            if self.config.losses.get('mse', {'weight': 0})['weight'] > 0:
                self.loss_mse = nn.MSELoss(reduction='none')
            if self.config.losses.perceptual.weight > 0:
                self.loss_pl = PerceptualLoss()
            if self.config.losses.get('resnet_pl', {'weight': 0})['weight'] > 0:
                self.loss_resnet_pl = ResNetPL(**self.config.losses.resnet_pl)
            else:
                self.loss_resnet_pl = None
        self.visualize_each_iters = visualize_each_iters
        LOGGER.info('BaseInpaintingTrainingModule init done')

    def configure_optimizers(self):
        discriminator_params = list(self.discriminator.parameters())
        return [dict(optimizer=make_optimizer(self.generator.parameters(), **self.config.optimizers.generator)), dict(optimizer=make_optimizer(discriminator_params, **self.config.optimizers.discriminator))]

    def train_dataloader(self):
        kwargs = dict(self.config.data.train)
        if self.use_ddp:
            kwargs['ddp_kwargs'] = dict(num_replicas=self.trainer.num_nodes * self.trainer.num_processes, rank=self.trainer.global_rank, shuffle=True)
        dataloader = make_default_train_dataloader(**self.config.data.train)
        return dataloader

    def val_dataloader(self):
        res = [make_default_val_dataloader(**self.config.data.val)]
        if self.config.data.visual_test is not None:
            res = res + [make_default_val_dataloader(**self.config.data.visual_test)]
        else:
            res = res + res
        extra_val = self.config.data.get('extra_val', ())
        if extra_val:
            res += [make_default_val_dataloader(**extra_val[k]) for k in self.extra_val_titles]
        return res

    def training_step(self, batch, batch_idx, optimizer_idx=None):
        self._is_training_step = True
        return self._do_step(batch, batch_idx, mode='train', optimizer_idx=optimizer_idx)

    def validation_step(self, batch, batch_idx, dataloader_idx):
        extra_val_key = None
        if dataloader_idx == 0:
            mode = 'val'
        elif dataloader_idx == 1:
            mode = 'test'
        else:
            mode = 'extra_val'
            extra_val_key = self.extra_val_titles[dataloader_idx - 2]
        self._is_training_step = False
        return self._do_step(batch, batch_idx, mode=mode, extra_val_key=extra_val_key)

    def training_step_end(self, batch_parts_outputs):
        if self.training and self.average_generator and (self.global_step >= self.average_generator_start_step) and (self.global_step >= self.last_generator_averaging_step + self.average_generator_period):
            if self.generator_average is None:
                self.generator_average = copy.deepcopy(self.generator)
            else:
                update_running_average(self.generator_average, self.generator, decay=self.generator_avg_beta)
            self.last_generator_averaging_step = self.global_step
        full_loss = batch_parts_outputs['loss'].mean() if torch.is_tensor(batch_parts_outputs['loss']) else torch.tensor(batch_parts_outputs['loss']).float().requires_grad_(True)
        log_info = {k: v.mean() for k, v in batch_parts_outputs['log_info'].items()}
        self.log_dict(log_info, on_step=True, on_epoch=False)
        return full_loss

    def validation_epoch_end(self, outputs):
        outputs = [step_out for out_group in outputs for step_out in out_group]
        averaged_logs = average_dicts((step_out['log_info'] for step_out in outputs))
        self.log_dict({k: v.mean() for k, v in averaged_logs.items()})
        pd.set_option('display.max_columns', 500)
        pd.set_option('display.width', 1000)
        val_evaluator_states = [s['val_evaluator_state'] for s in outputs if 'val_evaluator_state' in s]
        val_evaluator_res = self.val_evaluator.evaluation_end(states=val_evaluator_states)
        val_evaluator_res_df = pd.DataFrame(val_evaluator_res).stack(1).unstack(0)
        val_evaluator_res_df.dropna(axis=1, how='all', inplace=True)
        LOGGER.info(f'Validation metrics after epoch #{self.current_epoch}, total {self.global_step} iterations:\n{val_evaluator_res_df}')
        for k, v in flatten_dict(val_evaluator_res).items():
            self.log(f'val_{k}', v)
        test_evaluator_states = [s['test_evaluator_state'] for s in outputs if 'test_evaluator_state' in s]
        test_evaluator_res = self.test_evaluator.evaluation_end(states=test_evaluator_states)
        test_evaluator_res_df = pd.DataFrame(test_evaluator_res).stack(1).unstack(0)
        test_evaluator_res_df.dropna(axis=1, how='all', inplace=True)
        LOGGER.info(f'Test metrics after epoch #{self.current_epoch}, total {self.global_step} iterations:\n{test_evaluator_res_df}')
        for k, v in flatten_dict(test_evaluator_res).items():
            self.log(f'test_{k}', v)
        if self.extra_evaluators:
            for cur_eval_title, cur_evaluator in self.extra_evaluators.items():
                cur_state_key = f'extra_val_{cur_eval_title}_evaluator_state'
                cur_states = [s[cur_state_key] for s in outputs if cur_state_key in s]
                cur_evaluator_res = cur_evaluator.evaluation_end(states=cur_states)
                cur_evaluator_res_df = pd.DataFrame(cur_evaluator_res).stack(1).unstack(0)
                cur_evaluator_res_df.dropna(axis=1, how='all', inplace=True)
                LOGGER.info(f'Extra val {cur_eval_title} metrics after epoch #{self.current_epoch}, total {self.global_step} iterations:\n{cur_evaluator_res_df}')
                for k, v in flatten_dict(cur_evaluator_res).items():
                    self.log(f'extra_val_{cur_eval_title}_{k}', v)

    def _do_step(self, batch, batch_idx, mode='train', optimizer_idx=None, extra_val_key=None):
        if optimizer_idx == 0:
            set_requires_grad(self.generator, True)
            set_requires_grad(self.discriminator, False)
        elif optimizer_idx == 1:
            set_requires_grad(self.generator, False)
            set_requires_grad(self.discriminator, True)
        batch = self(batch)
        total_loss = 0
        metrics = {}
        if optimizer_idx is None or optimizer_idx == 0:
            total_loss, metrics = self.generator_loss(batch)
        elif optimizer_idx is None or optimizer_idx == 1:
            if self.config.losses.adversarial.weight > 0:
                total_loss, metrics = self.discriminator_loss(batch)
        if self.get_ddp_rank() in (None, 0) and (batch_idx % self.visualize_each_iters == 0 or mode == 'test'):
            if self.config.losses.adversarial.weight > 0:
                if self.store_discr_outputs_for_vis:
                    with torch.no_grad():
                        self.store_discr_outputs(batch)
            vis_suffix = f'_{mode}'
            if mode == 'extra_val':
                vis_suffix += f'_{extra_val_key}'
            self.visualizer(self.current_epoch, batch_idx, batch, suffix=vis_suffix)
        metrics_prefix = f'{mode}_'
        if mode == 'extra_val':
            metrics_prefix += f'{extra_val_key}_'
        result = dict(loss=total_loss, log_info=add_prefix_to_keys(metrics, metrics_prefix))
        if mode == 'val':
            result['val_evaluator_state'] = self.val_evaluator.process_batch(batch)
        elif mode == 'test':
            result['test_evaluator_state'] = self.test_evaluator.process_batch(batch)
        elif mode == 'extra_val':
            result[f'extra_val_{extra_val_key}_evaluator_state'] = self.extra_evaluators[extra_val_key].process_batch(batch)
        return result

    def get_current_generator(self, no_average=False):
        if not no_average and (not self.training) and self.average_generator and (self.generator_average is not None):
            return self.generator_average
        return self.generator

    def forward(self, batch: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """Pass data through generator and obtain at leas 'predicted_image' and 'inpainted' keys"""
        raise NotImplementedError()

    def generator_loss(self, batch) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        raise NotImplementedError()

    def discriminator_loss(self, batch) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        raise NotImplementedError()

    def store_discr_outputs(self, batch):
        out_size = batch['image'].shape[2:]
        discr_real_out, _ = self.discriminator(batch['image'])
        discr_fake_out, _ = self.discriminator(batch['predicted_image'])
        batch['discr_output_real'] = F.interpolate(discr_real_out, size=out_size, mode='nearest')
        batch['discr_output_fake'] = F.interpolate(discr_fake_out, size=out_size, mode='nearest')
        batch['discr_output_diff'] = batch['discr_output_real'] - batch['discr_output_fake']

    def get_ddp_rank(self):
        return self.trainer.global_rank if self.trainer.num_nodes * self.trainer.num_processes > 1 else None

def training_step_end(self, batch_parts_outputs):
    if self.training and self.average_generator and (self.global_step >= self.average_generator_start_step) and (self.global_step >= self.last_generator_averaging_step + self.average_generator_period):
        if self.generator_average is None:
            self.generator_average = copy.deepcopy(self.generator)
        else:
            update_running_average(self.generator_average, self.generator, decay=self.generator_avg_beta)
        self.last_generator_averaging_step = self.global_step
    full_loss = batch_parts_outputs['loss'].mean() if torch.is_tensor(batch_parts_outputs['loss']) else torch.tensor(batch_parts_outputs['loss']).float().requires_grad_(True)
    log_info = {k: v.mean() for k, v in batch_parts_outputs['log_info'].items()}
    self.log_dict(log_info, on_step=True, on_epoch=False)
    return full_loss

class ConcatTupleLayer(nn.Module):

    def forward(self, x):
        assert isinstance(x, tuple)
        x_l, x_g = x
        assert torch.is_tensor(x_l) or torch.is_tensor(x_g)
        if not torch.is_tensor(x_g):
            return x_l
        return torch.cat(x, dim=1)

def forward(self, x):
    assert isinstance(x, tuple)
    x_l, x_g = x
    assert torch.is_tensor(x_l) or torch.is_tensor(x_g)
    if not torch.is_tensor(x_g):
        return x_l
    return torch.cat(x, dim=1)

class FFCNLayerDiscriminator(BaseDiscriminator):

    def __init__(self, input_nc, ndf=64, n_layers=3, norm_layer=nn.BatchNorm2d, max_features=512, init_conv_kwargs={}, conv_kwargs={}):
        super().__init__()
        self.n_layers = n_layers

        def _act_ctor(inplace=True):
            return nn.LeakyReLU(negative_slope=0.2, inplace=inplace)
        kw = 3
        padw = int(np.ceil((kw - 1.0) / 2))
        sequence = [[FFC_BN_ACT(input_nc, ndf, kernel_size=kw, padding=padw, norm_layer=norm_layer, activation_layer=_act_ctor, **init_conv_kwargs)]]
        nf = ndf
        for n in range(1, n_layers):
            nf_prev = nf
            nf = min(nf * 2, max_features)
            cur_model = [FFC_BN_ACT(nf_prev, nf, kernel_size=kw, stride=2, padding=padw, norm_layer=norm_layer, activation_layer=_act_ctor, **conv_kwargs)]
            sequence.append(cur_model)
        nf_prev = nf
        nf = min(nf * 2, 512)
        cur_model = [FFC_BN_ACT(nf_prev, nf, kernel_size=kw, stride=1, padding=padw, norm_layer=norm_layer, activation_layer=lambda *args, **kwargs: nn.LeakyReLU(*args, negative_slope=0.2, **kwargs), **conv_kwargs), ConcatTupleLayer()]
        sequence.append(cur_model)
        sequence += [[nn.Conv2d(nf, 1, kernel_size=kw, stride=1, padding=padw)]]
        for n in range(len(sequence)):
            setattr(self, 'model' + str(n), nn.Sequential(*sequence[n]))

    def get_all_activations(self, x):
        res = [x]
        for n in range(self.n_layers + 2):
            model = getattr(self, 'model' + str(n))
            res.append(model(res[-1]))
        return res[1:]

    def forward(self, x):
        act = self.get_all_activations(x)
        feats = []
        for out in act[:-1]:
            if isinstance(out, tuple):
                if torch.is_tensor(out[1]):
                    out = torch.cat(out, dim=1)
                else:
                    out = out[0]
            feats.append(out)
        return (act[-1], feats)

def forward(self, x):
    act = self.get_all_activations(x)
    feats = []
    for out in act[:-1]:
        if isinstance(out, tuple):
            if torch.is_tensor(out[1]):
                out = torch.cat(out, dim=1)
            else:
                out = out[0]
        feats.append(out)
    return (act[-1], feats)

class NLayerDiscriminator(BaseDiscriminator):

    def __init__(self, input_nc, ndf=64, n_layers=3, norm_layer=nn.BatchNorm2d):
        super().__init__()
        self.n_layers = n_layers
        kw = 4
        padw = int(np.ceil((kw - 1.0) / 2))
        sequence = [[nn.Conv2d(input_nc, ndf, kernel_size=kw, stride=2, padding=padw), nn.LeakyReLU(0.2, True)]]
        nf = ndf
        for n in range(1, n_layers):
            nf_prev = nf
            nf = min(nf * 2, 512)
            cur_model = []
            cur_model += [nn.Conv2d(nf_prev, nf, kernel_size=kw, stride=2, padding=padw), norm_layer(nf), nn.LeakyReLU(0.2, True)]
            sequence.append(cur_model)
        nf_prev = nf
        nf = min(nf * 2, 512)
        cur_model = []
        cur_model += [nn.Conv2d(nf_prev, nf, kernel_size=kw, stride=1, padding=padw), norm_layer(nf), nn.LeakyReLU(0.2, True)]
        sequence.append(cur_model)
        sequence += [[nn.Conv2d(nf, 1, kernel_size=kw, stride=1, padding=padw)]]
        for n in range(len(sequence)):
            setattr(self, 'model' + str(n), nn.Sequential(*sequence[n]))

    def get_all_activations(self, x):
        res = [x]
        for n in range(self.n_layers + 2):
            model = getattr(self, 'model' + str(n))
            res.append(model(res[-1]))
        return res[1:]

    def forward(self, x):
        act = self.get_all_activations(x)
        return (act[-1], act[:-1])

def forward(self, x):
    act = self.get_all_activations(x)
    return (act[-1], act[:-1])

class MultidilatedNLayerDiscriminator(BaseDiscriminator):

    def __init__(self, input_nc, ndf=64, n_layers=3, norm_layer=nn.BatchNorm2d, multidilation_kwargs={}):
        super().__init__()
        self.n_layers = n_layers
        kw = 4
        padw = int(np.ceil((kw - 1.0) / 2))
        sequence = [[nn.Conv2d(input_nc, ndf, kernel_size=kw, stride=2, padding=padw), nn.LeakyReLU(0.2, True)]]
        nf = ndf
        for n in range(1, n_layers):
            nf_prev = nf
            nf = min(nf * 2, 512)
            cur_model = []
            cur_model += [MultidilatedConv(nf_prev, nf, kernel_size=kw, stride=2, padding=[2, 3], **multidilation_kwargs), norm_layer(nf), nn.LeakyReLU(0.2, True)]
            sequence.append(cur_model)
        nf_prev = nf
        nf = min(nf * 2, 512)
        cur_model = []
        cur_model += [nn.Conv2d(nf_prev, nf, kernel_size=kw, stride=1, padding=padw), norm_layer(nf), nn.LeakyReLU(0.2, True)]
        sequence.append(cur_model)
        sequence += [[nn.Conv2d(nf, 1, kernel_size=kw, stride=1, padding=padw)]]
        for n in range(len(sequence)):
            setattr(self, 'model' + str(n), nn.Sequential(*sequence[n]))

    def get_all_activations(self, x):
        res = [x]
        for n in range(self.n_layers + 2):
            model = getattr(self, 'model' + str(n))
            res.append(model(res[-1]))
        return res[1:]

    def forward(self, x):
        act = self.get_all_activations(x)
        return (act[-1], act[:-1])

def forward(self, x):
    act = self.get_all_activations(x)
    return (act[-1], act[:-1])

def visualize_mask_and_images_batch(batch: Dict[str, torch.Tensor], keys: List[str], max_items=10, last_without_mask=True, rescale_keys=None) -> np.ndarray:
    batch = {k: tens.detach().cpu().numpy() for k, tens in batch.items() if k in keys or k == 'mask'}
    batch_size = next(iter(batch.values())).shape[0]
    items_to_vis = min(batch_size, max_items)
    result = []
    for i in range(items_to_vis):
        cur_dct = {k: tens[i] for k, tens in batch.items()}
        result.append(visualize_mask_and_images(cur_dct, keys, last_without_mask=last_without_mask, rescale_keys=rescale_keys))
    return np.concatenate(result, axis=0)

def move_to_device(obj, device):
    if isinstance(obj, nn.Module):
        return obj.to(device)
    if torch.is_tensor(obj):
        return obj.to(device)
    if isinstance(obj, (tuple, list)):
        return [move_to_device(el, device) for el in obj]
    if isinstance(obj, dict):
        return {name: move_to_device(val, device) for name, val in obj.items()}
    raise ValueError(f'Unexpected type {type(obj)}')

def refine_predict(batch: dict, inpainter: nn.Module, gpu_ids: str, modulo: int, n_iters: int, lr: float, min_side: int, max_scales: int, px_budget: int):
    """Refines the inpainting of the network

    Parameters
    ----------
    batch : dict
        image-mask batch, currently we assume the batchsize to be 1
    inpainter : nn.Module
        the inpainting neural network
    gpu_ids : str
        the GPU ids of the machine to use. If only single GPU, use: "0,"
    modulo : int
        pad the image to ensure dimension % modulo == 0
    n_iters : int
        number of iterations of refinement for each scale
    lr : float
        learning rate
    min_side : int
        all sides of image on all scales should be >= min_side / sqrt(2)
    max_scales : int
        max number of downscaling scales for the image-mask pyramid
    px_budget : int
        pixels budget. Any image will be resized to satisfy height*width <= px_budget

    Returns
    -------
    torch.Tensor
        inpainted image of size (1,3,H,W)
    """
    assert not inpainter.training
    assert not inpainter.add_noise_kwargs
    assert inpainter.concat_mask
    gpu_ids = [f'cuda:{gpuid}' for gpuid in gpu_ids.replace(' ', '').split(',') if gpuid.isdigit()]
    n_resnet_blocks = 0
    first_resblock_ind = 0
    found_first_resblock = False
    for idl in range(len(inpainter.generator.model)):
        if isinstance(inpainter.generator.model[idl], FFCResnetBlock) or isinstance(inpainter.generator.model[idl], ResnetBlock):
            n_resnet_blocks += 1
            found_first_resblock = True
        elif not found_first_resblock:
            first_resblock_ind += 1
    resblocks_per_gpu = n_resnet_blocks // len(gpu_ids)
    devices = [torch.device(gpu_id) for gpu_id in gpu_ids]
    forward_front = inpainter.generator.model[0:first_resblock_ind]
    forward_front.to(devices[0])
    forward_rears = []
    for idd in range(len(gpu_ids)):
        if idd < len(gpu_ids) - 1:
            forward_rears.append(inpainter.generator.model[first_resblock_ind + resblocks_per_gpu * idd:first_resblock_ind + resblocks_per_gpu * (idd + 1)])
        else:
            forward_rears.append(inpainter.generator.model[first_resblock_ind + resblocks_per_gpu * idd:])
        forward_rears[idd].to(devices[idd])
    ls_images, ls_masks = _get_image_mask_pyramid(batch, min_side, max_scales, px_budget)
    image_inpainted = None
    for ids, (image, mask) in enumerate(zip(ls_images, ls_masks)):
        orig_shape = image.shape[2:]
        image = pad_tensor_to_modulo(image, modulo)
        mask = pad_tensor_to_modulo(mask, modulo)
        mask[mask >= 1e-08] = 1.0
        mask[mask < 1e-08] = 0.0
        image, mask = (move_to_device(image, devices[0]), move_to_device(mask, devices[0]))
        if image_inpainted is not None:
            image_inpainted = move_to_device(image_inpainted, devices[-1])
        image_inpainted = _infer(image, mask, forward_front, forward_rears, image_inpainted, orig_shape, devices, ids, n_iters, lr)
        image_inpainted = image_inpainted[:, :, :orig_shape[0], :orig_shape[1]]
        image = image.detach().cpu()
        mask = mask.detach().cpu()
    return image_inpainted

class InpaintingEvaluator:

    def __init__(self, dataset, scores, area_grouping=True, bins=10, batch_size=32, device='cuda', integral_func=None, integral_title=None, clamp_image_range=None):
        """
        :param dataset: torch.utils.data.Dataset which contains images and masks
        :param scores: dict {score_name: EvaluatorScore object}
        :param area_grouping: in addition to the overall scores, allows to compute score for the groups of samples
            which are defined by share of area occluded by mask
        :param bins: number of groups, partition is generated by np.linspace(0., 1., bins + 1)
        :param batch_size: batch_size for the dataloader
        :param device: device to use
        """
        self.scores = scores
        self.dataset = dataset
        self.area_grouping = area_grouping
        self.bins = bins
        self.device = torch.device(device)
        self.dataloader = DataLoader(self.dataset, shuffle=False, batch_size=batch_size)
        self.integral_func = integral_func
        self.integral_title = integral_title
        self.clamp_image_range = clamp_image_range

    def _get_bin_edges(self):
        bin_edges = np.linspace(0, 1, self.bins + 1)
        num_digits = max(0, math.ceil(math.log10(self.bins)) - 1)
        interval_names = []
        for idx_bin in range(self.bins):
            start_percent, end_percent = (round(100 * bin_edges[idx_bin], num_digits), round(100 * bin_edges[idx_bin + 1], num_digits))
            start_percent = '{:.{n}f}'.format(start_percent, n=num_digits)
            end_percent = '{:.{n}f}'.format(end_percent, n=num_digits)
            interval_names.append('{0}-{1}%'.format(start_percent, end_percent))
        groups = []
        for batch in self.dataloader:
            mask = batch['mask']
            batch_size = mask.shape[0]
            area = mask.to(self.device).reshape(batch_size, -1).mean(dim=-1)
            bin_indices = np.searchsorted(bin_edges, area.detach().cpu().numpy(), side='right') - 1
            bin_indices[bin_indices == self.bins] = self.bins - 1
            groups.append(bin_indices)
        groups = np.hstack(groups)
        return (groups, interval_names)

    def evaluate(self, model=None):
        """
        :param model: callable with signature (image_batch, mask_batch); should return inpainted_batch
        :return: dict with (score_name, group_type) as keys, where group_type can be either 'overall' or
            name of the particular group arranged by area of mask (e.g. '10-20%')
            and score statistics for the group as values.
        """
        results = dict()
        if self.area_grouping:
            groups, interval_names = self._get_bin_edges()
        else:
            groups = None
        for score_name, score in tqdm.auto.tqdm(self.scores.items(), desc='scores'):
            score.to(self.device)
            with torch.no_grad():
                score.reset()
                for batch in tqdm.auto.tqdm(self.dataloader, desc=score_name, leave=False):
                    batch = move_to_device(batch, self.device)
                    image_batch, mask_batch = (batch['image'], batch['mask'])
                    if self.clamp_image_range is not None:
                        image_batch = torch.clamp(image_batch, min=self.clamp_image_range[0], max=self.clamp_image_range[1])
                    if model is None:
                        assert 'inpainted' in batch, 'Model is None, so we expected precomputed inpainting results at key "inpainted"'
                        inpainted_batch = batch['inpainted']
                    else:
                        inpainted_batch = model(image_batch, mask_batch)
                    score(inpainted_batch, image_batch, mask_batch)
                total_results, group_results = score.get_value(groups=groups)
            results[score_name, 'total'] = total_results
            if groups is not None:
                for group_index, group_values in group_results.items():
                    group_name = interval_names[group_index]
                    results[score_name, group_name] = group_values
        if self.integral_func is not None:
            results[self.integral_title, 'total'] = dict(mean=self.integral_func(results))
        return results

def __init__(self, dataset, scores, area_grouping=True, bins=10, batch_size=32, device='cuda', integral_func=None, integral_title=None, clamp_image_range=None):
    """
        :param dataset: torch.utils.data.Dataset which contains images and masks
        :param scores: dict {score_name: EvaluatorScore object}
        :param area_grouping: in addition to the overall scores, allows to compute score for the groups of samples
            which are defined by share of area occluded by mask
        :param bins: number of groups, partition is generated by np.linspace(0., 1., bins + 1)
        :param batch_size: batch_size for the dataloader
        :param device: device to use
        """
    self.scores = scores
    self.dataset = dataset
    self.area_grouping = area_grouping
    self.bins = bins
    self.device = torch.device(device)
    self.dataloader = DataLoader(self.dataset, shuffle=False, batch_size=batch_size)
    self.integral_func = integral_func
    self.integral_title = integral_title
    self.clamp_image_range = clamp_image_range

def _get_bin_edges(self):
    bin_edges = np.linspace(0, 1, self.bins + 1)
    num_digits = max(0, math.ceil(math.log10(self.bins)) - 1)
    interval_names = []
    for idx_bin in range(self.bins):
        start_percent, end_percent = (round(100 * bin_edges[idx_bin], num_digits), round(100 * bin_edges[idx_bin + 1], num_digits))
        start_percent = '{:.{n}f}'.format(start_percent, n=num_digits)
        end_percent = '{:.{n}f}'.format(end_percent, n=num_digits)
        interval_names.append('{0}-{1}%'.format(start_percent, end_percent))
    groups = []
    for batch in self.dataloader:
        mask = batch['mask']
        batch_size = mask.shape[0]
        area = mask.to(self.device).reshape(batch_size, -1).mean(dim=-1)
        bin_indices = np.searchsorted(bin_edges, area.detach().cpu().numpy(), side='right') - 1
        bin_indices[bin_indices == self.bins] = self.bins - 1
        groups.append(bin_indices)
    groups = np.hstack(groups)
    return (groups, interval_names)

class InpaintingEvaluatorOnline(nn.Module):

    def __init__(self, scores, bins=10, image_key='image', inpainted_key='inpainted', integral_func=None, integral_title=None, clamp_image_range=None):
        """
        :param scores: dict {score_name: EvaluatorScore object}
        :param bins: number of groups, partition is generated by np.linspace(0., 1., bins + 1)
        :param device: device to use
        """
        super().__init__()
        LOGGER.info(f'{type(self)} init called')
        self.scores = nn.ModuleDict(scores)
        self.image_key = image_key
        self.inpainted_key = inpainted_key
        self.bins_num = bins
        self.bin_edges = np.linspace(0, 1, self.bins_num + 1)
        num_digits = max(0, math.ceil(math.log10(self.bins_num)) - 1)
        self.interval_names = []
        for idx_bin in range(self.bins_num):
            start_percent, end_percent = (round(100 * self.bin_edges[idx_bin], num_digits), round(100 * self.bin_edges[idx_bin + 1], num_digits))
            start_percent = '{:.{n}f}'.format(start_percent, n=num_digits)
            end_percent = '{:.{n}f}'.format(end_percent, n=num_digits)
            self.interval_names.append('{0}-{1}%'.format(start_percent, end_percent))
        self.groups = []
        self.integral_func = integral_func
        self.integral_title = integral_title
        self.clamp_image_range = clamp_image_range
        LOGGER.info(f'{type(self)} init done')

    def _get_bins(self, mask_batch):
        batch_size = mask_batch.shape[0]
        area = mask_batch.view(batch_size, -1).mean(dim=-1).detach().cpu().numpy()
        bin_indices = np.clip(np.searchsorted(self.bin_edges, area) - 1, 0, self.bins_num - 1)
        return bin_indices

    def forward(self, batch: Dict[str, torch.Tensor]):
        """
        Calculate and accumulate metrics for batch. To finalize evaluation and obtain final metrics, call evaluation_end
        :param batch: batch dict with mandatory fields mask, image, inpainted (can be overriden by self.inpainted_key)
        """
        result = {}
        with torch.no_grad():
            image_batch, mask_batch, inpainted_batch = (batch[self.image_key], batch['mask'], batch[self.inpainted_key])
            if self.clamp_image_range is not None:
                image_batch = torch.clamp(image_batch, min=self.clamp_image_range[0], max=self.clamp_image_range[1])
            self.groups.extend(self._get_bins(mask_batch))
            for score_name, score in self.scores.items():
                result[score_name] = score(inpainted_batch, image_batch, mask_batch)
        return result

    def process_batch(self, batch: Dict[str, torch.Tensor]):
        return self(batch)

    def evaluation_end(self, states=None):
        """:return: dict with (score_name, group_type) as keys, where group_type can be either 'overall' or
            name of the particular group arranged by area of mask (e.g. '10-20%')
            and score statistics for the group as values.
        """
        LOGGER.info(f'{type(self)}: evaluation_end called')
        self.groups = np.array(self.groups)
        results = {}
        for score_name, score in self.scores.items():
            LOGGER.info(f'Getting value of {score_name}')
            cur_states = [s[score_name] for s in states] if states is not None else None
            total_results, group_results = score.get_value(groups=self.groups, states=cur_states)
            LOGGER.info(f'Getting value of {score_name} done')
            results[score_name, 'total'] = total_results
            for group_index, group_values in group_results.items():
                group_name = self.interval_names[group_index]
                results[score_name, group_name] = group_values
        if self.integral_func is not None:
            results[self.integral_title, 'total'] = dict(mean=self.integral_func(results))
        LOGGER.info(f'{type(self)}: reset scores')
        self.groups = []
        for sc in self.scores.values():
            sc.reset()
        LOGGER.info(f'{type(self)}: reset scores done')
        LOGGER.info(f'{type(self)}: evaluation_end done')
        return results

def _get_bins(self, mask_batch):
    batch_size = mask_batch.shape[0]
    area = mask_batch.view(batch_size, -1).mean(dim=-1).detach().cpu().numpy()
    bin_indices = np.clip(np.searchsorted(self.bin_edges, area) - 1, 0, self.bins_num - 1)
    return bin_indices

class PairwiseScore(EvaluatorScore, ABC):

    def __init__(self):
        super().__init__()
        self.individual_values = None

    def get_value(self, groups=None, states=None):
        """
        :param groups:
        :return:
            total_results: dict of kind {'mean': score mean, 'std': score std}
            group_results: None, if groups is None;
                else dict {group_idx: {'mean': score mean among group, 'std': score std among group}}
        """
        individual_values = torch.cat(states, dim=-1).reshape(-1).cpu().numpy() if states is not None else self.individual_values
        total_results = {'mean': individual_values.mean(), 'std': individual_values.std()}
        if groups is None:
            return (total_results, None)
        group_results = dict()
        grouping = get_groupings(groups)
        for label, index in grouping.items():
            group_scores = individual_values[index]
            group_results[label] = {'mean': group_scores.mean(), 'std': group_scores.std()}
        return (total_results, group_results)

    def reset(self):
        self.individual_values = []

def get_value(self, groups=None, states=None):
    """
        :param groups:
        :return:
            total_results: dict of kind {'mean': score mean, 'std': score std}
            group_results: None, if groups is None;
                else dict {group_idx: {'mean': score mean among group, 'std': score std among group}}
        """
    individual_values = torch.cat(states, dim=-1).reshape(-1).cpu().numpy() if states is not None else self.individual_values
    total_results = {'mean': individual_values.mean(), 'std': individual_values.std()}
    if groups is None:
        return (total_results, None)
    group_results = dict()
    grouping = get_groupings(groups)
    for label, index in grouping.items():
        group_scores = individual_values[index]
        group_results[label] = {'mean': group_scores.mean(), 'std': group_scores.std()}
    return (total_results, group_results)

class SSIMScore(PairwiseScore):

    def __init__(self, window_size=11):
        super().__init__()
        self.score = SSIM(window_size=window_size, size_average=False).eval()
        self.reset()

    def forward(self, pred_batch, target_batch, mask=None):
        batch_values = self.score(pred_batch, target_batch)
        self.individual_values = np.hstack([self.individual_values, batch_values.detach().cpu().numpy()])
        return batch_values

def forward(self, pred_batch, target_batch, mask=None):
    batch_values = self.score(pred_batch, target_batch)
    self.individual_values = np.hstack([self.individual_values, batch_values.detach().cpu().numpy()])
    return batch_values

class LPIPSScore(PairwiseScore):

    def __init__(self, model='net-lin', net='vgg', model_path=None, use_gpu=True):
        super().__init__()
        self.score = PerceptualLoss(model=model, net=net, model_path=model_path, use_gpu=use_gpu, spatial=False).eval()
        self.reset()

    def forward(self, pred_batch, target_batch, mask=None):
        batch_values = self.score(pred_batch, target_batch).flatten()
        self.individual_values = np.hstack([self.individual_values, batch_values.detach().cpu().numpy()])
        return batch_values

def forward(self, pred_batch, target_batch, mask=None):
    batch_values = self.score(pred_batch, target_batch).flatten()
    self.individual_values = np.hstack([self.individual_values, batch_values.detach().cpu().numpy()])
    return batch_values

def fid_calculate_activation_statistics(act):
    mu = np.mean(act, axis=0)
    sigma = np.cov(act, rowvar=False)
    return (mu, sigma)

class FIDScore(EvaluatorScore):

    def __init__(self, dims=2048, eps=1e-06):
        LOGGER.info('FIDscore init called')
        super().__init__()
        if getattr(FIDScore, '_MODEL', None) is None:
            block_idx = InceptionV3.BLOCK_INDEX_BY_DIM[dims]
            FIDScore._MODEL = InceptionV3([block_idx]).eval()
        self.model = FIDScore._MODEL
        self.eps = eps
        self.reset()
        LOGGER.info('FIDscore init done')

    def forward(self, pred_batch, target_batch, mask=None):
        activations_pred = self._get_activations(pred_batch)
        activations_target = self._get_activations(target_batch)
        self.activations_pred.append(activations_pred.detach().cpu())
        self.activations_target.append(activations_target.detach().cpu())
        return (activations_pred, activations_target)

    def get_value(self, groups=None, states=None):
        LOGGER.info('FIDscore get_value called')
        activations_pred, activations_target = zip(*states) if states is not None else (self.activations_pred, self.activations_target)
        activations_pred = torch.cat(activations_pred).cpu().numpy()
        activations_target = torch.cat(activations_target).cpu().numpy()
        total_distance = calculate_frechet_distance(activations_pred, activations_target, eps=self.eps)
        total_results = dict(mean=total_distance)
        if groups is None:
            group_results = None
        else:
            group_results = dict()
            grouping = get_groupings(groups)
            for label, index in grouping.items():
                if len(index) > 1:
                    group_distance = calculate_frechet_distance(activations_pred[index], activations_target[index], eps=self.eps)
                    group_results[label] = dict(mean=group_distance)
                else:
                    group_results[label] = dict(mean=float('nan'))
        self.reset()
        LOGGER.info('FIDscore get_value done')
        return (total_results, group_results)

    def reset(self):
        self.activations_pred = []
        self.activations_target = []

    def _get_activations(self, batch):
        activations = self.model(batch)[0]
        if activations.shape[2] != 1 or activations.shape[3] != 1:
            assert False, 'We should not have got here, because Inception always scales inputs to 299x299'
        activations = activations.squeeze(-1).squeeze(-1)
        return activations

def forward(self, pred_batch, target_batch, mask=None):
    activations_pred = self._get_activations(pred_batch)
    activations_target = self._get_activations(target_batch)
    self.activations_pred.append(activations_pred.detach().cpu())
    self.activations_target.append(activations_target.detach().cpu())
    return (activations_pred, activations_target)

def get_value(self, groups=None, states=None):
    LOGGER.info('FIDscore get_value called')
    activations_pred, activations_target = zip(*states) if states is not None else (self.activations_pred, self.activations_target)
    activations_pred = torch.cat(activations_pred).cpu().numpy()
    activations_target = torch.cat(activations_target).cpu().numpy()
    total_distance = calculate_frechet_distance(activations_pred, activations_target, eps=self.eps)
    total_results = dict(mean=total_distance)
    if groups is None:
        group_results = None
    else:
        group_results = dict()
        grouping = get_groupings(groups)
        for label, index in grouping.items():
            if len(index) > 1:
                group_distance = calculate_frechet_distance(activations_pred[index], activations_target[index], eps=self.eps)
                group_results[label] = dict(mean=group_distance)
            else:
                group_results[label] = dict(mean=float('nan'))
    self.reset()
    LOGGER.info('FIDscore get_value done')
    return (total_results, group_results)

class SegmentationAwareScore(EvaluatorScore):

    def __init__(self, weights_path):
        super().__init__()
        self.segm_network = SegmentationModule(weights_path=weights_path, use_default_normalization=True).eval()
        self.target_class_freq_by_image_total = []
        self.target_class_freq_by_image_mask = []
        self.pred_class_freq_by_image_mask = []

    def forward(self, pred_batch, target_batch, mask):
        pred_segm_flat = self.segm_network.predict(pred_batch)[0].view(pred_batch.shape[0], -1).long().detach().cpu().numpy()
        target_segm_flat = self.segm_network.predict(target_batch)[0].view(pred_batch.shape[0], -1).long().detach().cpu().numpy()
        mask_flat = (mask.view(mask.shape[0], -1) > 0.5).detach().cpu().numpy()
        batch_target_class_freq_total = []
        batch_target_class_freq_mask = []
        batch_pred_class_freq_mask = []
        for cur_pred_segm, cur_target_segm, cur_mask in zip(pred_segm_flat, target_segm_flat, mask_flat):
            cur_target_class_freq_total = np.bincount(cur_target_segm, minlength=NUM_CLASS)[None, ...]
            cur_target_class_freq_mask = np.bincount(cur_target_segm[cur_mask], minlength=NUM_CLASS)[None, ...]
            cur_pred_class_freq_mask = np.bincount(cur_pred_segm[cur_mask], minlength=NUM_CLASS)[None, ...]
            self.target_class_freq_by_image_total.append(cur_target_class_freq_total)
            self.target_class_freq_by_image_mask.append(cur_target_class_freq_mask)
            self.pred_class_freq_by_image_mask.append(cur_pred_class_freq_mask)
            batch_target_class_freq_total.append(cur_target_class_freq_total)
            batch_target_class_freq_mask.append(cur_target_class_freq_mask)
            batch_pred_class_freq_mask.append(cur_pred_class_freq_mask)
        batch_target_class_freq_total = np.concatenate(batch_target_class_freq_total, axis=0)
        batch_target_class_freq_mask = np.concatenate(batch_target_class_freq_mask, axis=0)
        batch_pred_class_freq_mask = np.concatenate(batch_pred_class_freq_mask, axis=0)
        return (batch_target_class_freq_total, batch_target_class_freq_mask, batch_pred_class_freq_mask)

    def reset(self):
        super().reset()
        self.target_class_freq_by_image_total = []
        self.target_class_freq_by_image_mask = []
        self.pred_class_freq_by_image_mask = []

def forward(self, pred_batch, target_batch, mask):
    pred_segm_flat = self.segm_network.predict(pred_batch)[0].view(pred_batch.shape[0], -1).long().detach().cpu().numpy()
    target_segm_flat = self.segm_network.predict(target_batch)[0].view(pred_batch.shape[0], -1).long().detach().cpu().numpy()
    mask_flat = (mask.view(mask.shape[0], -1) > 0.5).detach().cpu().numpy()
    batch_target_class_freq_total = []
    batch_target_class_freq_mask = []
    batch_pred_class_freq_mask = []
    for cur_pred_segm, cur_target_segm, cur_mask in zip(pred_segm_flat, target_segm_flat, mask_flat):
        cur_target_class_freq_total = np.bincount(cur_target_segm, minlength=NUM_CLASS)[None, ...]
        cur_target_class_freq_mask = np.bincount(cur_target_segm[cur_mask], minlength=NUM_CLASS)[None, ...]
        cur_pred_class_freq_mask = np.bincount(cur_pred_segm[cur_mask], minlength=NUM_CLASS)[None, ...]
        self.target_class_freq_by_image_total.append(cur_target_class_freq_total)
        self.target_class_freq_by_image_mask.append(cur_target_class_freq_mask)
        self.pred_class_freq_by_image_mask.append(cur_pred_class_freq_mask)
        batch_target_class_freq_total.append(cur_target_class_freq_total)
        batch_target_class_freq_mask.append(cur_target_class_freq_mask)
        batch_pred_class_freq_mask.append(cur_pred_class_freq_mask)
    batch_target_class_freq_total = np.concatenate(batch_target_class_freq_total, axis=0)
    batch_target_class_freq_mask = np.concatenate(batch_target_class_freq_mask, axis=0)
    batch_pred_class_freq_mask = np.concatenate(batch_pred_class_freq_mask, axis=0)
    return (batch_target_class_freq_total, batch_target_class_freq_mask, batch_pred_class_freq_mask)

def get_segmentation_idx2name():
    return {i - 1: name for i, name in segm_options['classes'].set_index('Idx', drop=True)['Name'].to_dict().items()}

class SegmentationAwarePairwiseScore(SegmentationAwareScore):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.individual_values = []
        self.segm_idx2name = get_segmentation_idx2name()

    def forward(self, pred_batch, target_batch, mask):
        cur_class_stats = super().forward(pred_batch, target_batch, mask)
        score_values = self.calc_score(pred_batch, target_batch, mask)
        self.individual_values.append(score_values)
        return cur_class_stats + (score_values,)

    @abstractmethod
    def calc_score(self, pred_batch, target_batch, mask):
        raise NotImplementedError()

    def get_value(self, groups=None, states=None):
        """
        :param groups:
        :return:
            total_results: dict of kind {'mean': score mean, 'std': score std}
            group_results: None, if groups is None;
                else dict {group_idx: {'mean': score mean among group, 'std': score std among group}}
        """
        if states is not None:
            target_class_freq_by_image_total, target_class_freq_by_image_mask, pred_class_freq_by_image_mask, individual_values = states
        else:
            target_class_freq_by_image_total = self.target_class_freq_by_image_total
            target_class_freq_by_image_mask = self.target_class_freq_by_image_mask
            pred_class_freq_by_image_mask = self.pred_class_freq_by_image_mask
            individual_values = self.individual_values
        target_class_freq_by_image_total = np.concatenate(target_class_freq_by_image_total, axis=0)
        target_class_freq_by_image_mask = np.concatenate(target_class_freq_by_image_mask, axis=0)
        pred_class_freq_by_image_mask = np.concatenate(pred_class_freq_by_image_mask, axis=0)
        individual_values = np.concatenate(individual_values, axis=0)
        total_results = {'mean': individual_values.mean(), 'std': individual_values.std(), **distribute_values_to_classes(target_class_freq_by_image_mask, individual_values, self.segm_idx2name)}
        if groups is None:
            return (total_results, None)
        group_results = dict()
        grouping = get_groupings(groups)
        for label, index in grouping.items():
            group_class_freq = target_class_freq_by_image_mask[index]
            group_scores = individual_values[index]
            group_results[label] = {'mean': group_scores.mean(), 'std': group_scores.std(), **distribute_values_to_classes(group_class_freq, group_scores, self.segm_idx2name)}
        return (total_results, group_results)

    def reset(self):
        super().reset()
        self.individual_values = []

def get_value(self, groups=None, states=None):
    """
        :param groups:
        :return:
            total_results: dict of kind {'mean': score mean, 'std': score std}
            group_results: None, if groups is None;
                else dict {group_idx: {'mean': score mean among group, 'std': score std among group}}
        """
    if states is not None:
        target_class_freq_by_image_total, target_class_freq_by_image_mask, pred_class_freq_by_image_mask, individual_values = states
    else:
        target_class_freq_by_image_total = self.target_class_freq_by_image_total
        target_class_freq_by_image_mask = self.target_class_freq_by_image_mask
        pred_class_freq_by_image_mask = self.pred_class_freq_by_image_mask
        individual_values = self.individual_values
    target_class_freq_by_image_total = np.concatenate(target_class_freq_by_image_total, axis=0)
    target_class_freq_by_image_mask = np.concatenate(target_class_freq_by_image_mask, axis=0)
    pred_class_freq_by_image_mask = np.concatenate(pred_class_freq_by_image_mask, axis=0)
    individual_values = np.concatenate(individual_values, axis=0)
    total_results = {'mean': individual_values.mean(), 'std': individual_values.std(), **distribute_values_to_classes(target_class_freq_by_image_mask, individual_values, self.segm_idx2name)}
    if groups is None:
        return (total_results, None)
    group_results = dict()
    grouping = get_groupings(groups)
    for label, index in grouping.items():
        group_class_freq = target_class_freq_by_image_mask[index]
        group_scores = individual_values[index]
        group_results[label] = {'mean': group_scores.mean(), 'std': group_scores.std(), **distribute_values_to_classes(group_class_freq, group_scores, self.segm_idx2name)}
    return (total_results, group_results)

class SegmentationClassStats(SegmentationAwarePairwiseScore):

    def calc_score(self, pred_batch, target_batch, mask):
        return 0

    def get_value(self, groups=None, states=None):
        """
        :param groups:
        :return:
            total_results: dict of kind {'mean': score mean, 'std': score std}
            group_results: None, if groups is None;
                else dict {group_idx: {'mean': score mean among group, 'std': score std among group}}
        """
        if states is not None:
            target_class_freq_by_image_total, target_class_freq_by_image_mask, pred_class_freq_by_image_mask, _ = states
        else:
            target_class_freq_by_image_total = self.target_class_freq_by_image_total
            target_class_freq_by_image_mask = self.target_class_freq_by_image_mask
            pred_class_freq_by_image_mask = self.pred_class_freq_by_image_mask
        target_class_freq_by_image_total = np.concatenate(target_class_freq_by_image_total, axis=0)
        target_class_freq_by_image_mask = np.concatenate(target_class_freq_by_image_mask, axis=0)
        pred_class_freq_by_image_mask = np.concatenate(pred_class_freq_by_image_mask, axis=0)
        target_class_freq_by_image_total_marginal = target_class_freq_by_image_total.sum(0).astype('float32')
        target_class_freq_by_image_total_marginal /= target_class_freq_by_image_total_marginal.sum()
        target_class_freq_by_image_mask_marginal = target_class_freq_by_image_mask.sum(0).astype('float32')
        target_class_freq_by_image_mask_marginal /= target_class_freq_by_image_mask_marginal.sum()
        pred_class_freq_diff = (pred_class_freq_by_image_mask - target_class_freq_by_image_mask).sum(0) / (target_class_freq_by_image_mask.sum(0) + 0.001)
        total_results = dict()
        total_results.update({f'total_freq/{self.segm_idx2name[i]}': v for i, v in enumerate(target_class_freq_by_image_total_marginal) if v > 0})
        total_results.update({f'mask_freq/{self.segm_idx2name[i]}': v for i, v in enumerate(target_class_freq_by_image_mask_marginal) if v > 0})
        total_results.update({f'mask_freq_diff/{self.segm_idx2name[i]}': v for i, v in enumerate(pred_class_freq_diff) if target_class_freq_by_image_total_marginal[i] > 0})
        if groups is None:
            return (total_results, None)
        group_results = dict()
        grouping = get_groupings(groups)
        for label, index in grouping.items():
            group_target_class_freq_by_image_total = target_class_freq_by_image_total[index]
            group_target_class_freq_by_image_mask = target_class_freq_by_image_mask[index]
            group_pred_class_freq_by_image_mask = pred_class_freq_by_image_mask[index]
            group_target_class_freq_by_image_total_marginal = group_target_class_freq_by_image_total.sum(0).astype('float32')
            group_target_class_freq_by_image_total_marginal /= group_target_class_freq_by_image_total_marginal.sum()
            group_target_class_freq_by_image_mask_marginal = group_target_class_freq_by_image_mask.sum(0).astype('float32')
            group_target_class_freq_by_image_mask_marginal /= group_target_class_freq_by_image_mask_marginal.sum()
            group_pred_class_freq_diff = (group_pred_class_freq_by_image_mask - group_target_class_freq_by_image_mask).sum(0) / (group_target_class_freq_by_image_mask.sum(0) + 0.001)
            cur_group_results = dict()
            cur_group_results.update({f'total_freq/{self.segm_idx2name[i]}': v for i, v in enumerate(group_target_class_freq_by_image_total_marginal) if v > 0})
            cur_group_results.update({f'mask_freq/{self.segm_idx2name[i]}': v for i, v in enumerate(group_target_class_freq_by_image_mask_marginal) if v > 0})
            cur_group_results.update({f'mask_freq_diff/{self.segm_idx2name[i]}': v for i, v in enumerate(group_pred_class_freq_diff) if group_target_class_freq_by_image_total_marginal[i] > 0})
            group_results[label] = cur_group_results
        return (total_results, group_results)

def get_value(self, groups=None, states=None):
    """
        :param groups:
        :return:
            total_results: dict of kind {'mean': score mean, 'std': score std}
            group_results: None, if groups is None;
                else dict {group_idx: {'mean': score mean among group, 'std': score std among group}}
        """
    if states is not None:
        target_class_freq_by_image_total, target_class_freq_by_image_mask, pred_class_freq_by_image_mask, _ = states
    else:
        target_class_freq_by_image_total = self.target_class_freq_by_image_total
        target_class_freq_by_image_mask = self.target_class_freq_by_image_mask
        pred_class_freq_by_image_mask = self.pred_class_freq_by_image_mask
    target_class_freq_by_image_total = np.concatenate(target_class_freq_by_image_total, axis=0)
    target_class_freq_by_image_mask = np.concatenate(target_class_freq_by_image_mask, axis=0)
    pred_class_freq_by_image_mask = np.concatenate(pred_class_freq_by_image_mask, axis=0)
    target_class_freq_by_image_total_marginal = target_class_freq_by_image_total.sum(0).astype('float32')
    target_class_freq_by_image_total_marginal /= target_class_freq_by_image_total_marginal.sum()
    target_class_freq_by_image_mask_marginal = target_class_freq_by_image_mask.sum(0).astype('float32')
    target_class_freq_by_image_mask_marginal /= target_class_freq_by_image_mask_marginal.sum()
    pred_class_freq_diff = (pred_class_freq_by_image_mask - target_class_freq_by_image_mask).sum(0) / (target_class_freq_by_image_mask.sum(0) + 0.001)
    total_results = dict()
    total_results.update({f'total_freq/{self.segm_idx2name[i]}': v for i, v in enumerate(target_class_freq_by_image_total_marginal) if v > 0})
    total_results.update({f'mask_freq/{self.segm_idx2name[i]}': v for i, v in enumerate(target_class_freq_by_image_mask_marginal) if v > 0})
    total_results.update({f'mask_freq_diff/{self.segm_idx2name[i]}': v for i, v in enumerate(pred_class_freq_diff) if target_class_freq_by_image_total_marginal[i] > 0})
    if groups is None:
        return (total_results, None)
    group_results = dict()
    grouping = get_groupings(groups)
    for label, index in grouping.items():
        group_target_class_freq_by_image_total = target_class_freq_by_image_total[index]
        group_target_class_freq_by_image_mask = target_class_freq_by_image_mask[index]
        group_pred_class_freq_by_image_mask = pred_class_freq_by_image_mask[index]
        group_target_class_freq_by_image_total_marginal = group_target_class_freq_by_image_total.sum(0).astype('float32')
        group_target_class_freq_by_image_total_marginal /= group_target_class_freq_by_image_total_marginal.sum()
        group_target_class_freq_by_image_mask_marginal = group_target_class_freq_by_image_mask.sum(0).astype('float32')
        group_target_class_freq_by_image_mask_marginal /= group_target_class_freq_by_image_mask_marginal.sum()
        group_pred_class_freq_diff = (group_pred_class_freq_by_image_mask - group_target_class_freq_by_image_mask).sum(0) / (group_target_class_freq_by_image_mask.sum(0) + 0.001)
        cur_group_results = dict()
        cur_group_results.update({f'total_freq/{self.segm_idx2name[i]}': v for i, v in enumerate(group_target_class_freq_by_image_total_marginal) if v > 0})
        cur_group_results.update({f'mask_freq/{self.segm_idx2name[i]}': v for i, v in enumerate(group_target_class_freq_by_image_mask_marginal) if v > 0})
        cur_group_results.update({f'mask_freq_diff/{self.segm_idx2name[i]}': v for i, v in enumerate(group_pred_class_freq_diff) if group_target_class_freq_by_image_total_marginal[i] > 0})
        group_results[label] = cur_group_results
    return (total_results, group_results)

class SegmentationAwareSSIM(SegmentationAwarePairwiseScore):

    def __init__(self, *args, window_size=11, **kwargs):
        super().__init__(*args, **kwargs)
        self.score_impl = SSIM(window_size=window_size, size_average=False).eval()

    def calc_score(self, pred_batch, target_batch, mask):
        return self.score_impl(pred_batch, target_batch).detach().cpu().numpy()

def calc_score(self, pred_batch, target_batch, mask):
    return self.score_impl(pred_batch, target_batch).detach().cpu().numpy()

class SegmentationAwareLPIPS(SegmentationAwarePairwiseScore):

    def __init__(self, *args, model='net-lin', net='vgg', model_path=None, use_gpu=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.score_impl = PerceptualLoss(model=model, net=net, model_path=model_path, use_gpu=use_gpu, spatial=False).eval()

    def calc_score(self, pred_batch, target_batch, mask):
        return self.score_impl(pred_batch, target_batch).flatten().detach().cpu().numpy()

def calc_score(self, pred_batch, target_batch, mask):
    return self.score_impl(pred_batch, target_batch).flatten().detach().cpu().numpy()

class SegmentationAwareFID(SegmentationAwarePairwiseScore):

    def __init__(self, *args, dims=2048, eps=1e-06, n_jobs=-1, **kwargs):
        super().__init__(*args, **kwargs)
        if getattr(FIDScore, '_MODEL', None) is None:
            block_idx = InceptionV3.BLOCK_INDEX_BY_DIM[dims]
            FIDScore._MODEL = InceptionV3([block_idx]).eval()
        self.model = FIDScore._MODEL
        self.eps = eps
        self.n_jobs = n_jobs

    def calc_score(self, pred_batch, target_batch, mask):
        activations_pred = self._get_activations(pred_batch)
        activations_target = self._get_activations(target_batch)
        return (activations_pred, activations_target)

    def get_value(self, groups=None, states=None):
        """
        :param groups:
        :return:
            total_results: dict of kind {'mean': score mean, 'std': score std}
            group_results: None, if groups is None;
                else dict {group_idx: {'mean': score mean among group, 'std': score std among group}}
        """
        if states is not None:
            target_class_freq_by_image_total, target_class_freq_by_image_mask, pred_class_freq_by_image_mask, activation_pairs = states
        else:
            target_class_freq_by_image_total = self.target_class_freq_by_image_total
            target_class_freq_by_image_mask = self.target_class_freq_by_image_mask
            pred_class_freq_by_image_mask = self.pred_class_freq_by_image_mask
            activation_pairs = self.individual_values
        target_class_freq_by_image_total = np.concatenate(target_class_freq_by_image_total, axis=0)
        target_class_freq_by_image_mask = np.concatenate(target_class_freq_by_image_mask, axis=0)
        pred_class_freq_by_image_mask = np.concatenate(pred_class_freq_by_image_mask, axis=0)
        activations_pred, activations_target = zip(*activation_pairs)
        activations_pred = np.concatenate(activations_pred, axis=0)
        activations_target = np.concatenate(activations_target, axis=0)
        total_results = {'mean': calculate_frechet_distance(activations_pred, activations_target, eps=self.eps), 'std': 0, **self.distribute_fid_to_classes(target_class_freq_by_image_mask, activations_pred, activations_target)}
        if groups is None:
            return (total_results, None)
        group_results = dict()
        grouping = get_groupings(groups)
        for label, index in grouping.items():
            if len(index) > 1:
                group_activations_pred = activations_pred[index]
                group_activations_target = activations_target[index]
                group_class_freq = target_class_freq_by_image_mask[index]
                group_results[label] = {'mean': calculate_frechet_distance(group_activations_pred, group_activations_target, eps=self.eps), 'std': 0, **self.distribute_fid_to_classes(group_class_freq, group_activations_pred, group_activations_target)}
            else:
                group_results[label] = dict(mean=float('nan'), std=0)
        return (total_results, group_results)

    def distribute_fid_to_classes(self, class_freq, activations_pred, activations_target):
        real_fid = calculate_frechet_distance(activations_pred, activations_target, eps=self.eps)
        fid_no_images = Parallel(n_jobs=self.n_jobs)((delayed(calculade_fid_no_img)(img_i, activations_pred, activations_target, eps=self.eps) for img_i in range(activations_pred.shape[0])))
        errors = real_fid - fid_no_images
        return distribute_values_to_classes(class_freq, errors, self.segm_idx2name)

    def _get_activations(self, batch):
        activations = self.model(batch)[0]
        if activations.shape[2] != 1 or activations.shape[3] != 1:
            activations = F.adaptive_avg_pool2d(activations, output_size=(1, 1))
        activations = activations.squeeze(-1).squeeze(-1).detach().cpu().numpy()
        return activations

def calc_score(self, pred_batch, target_batch, mask):
    activations_pred = self._get_activations(pred_batch)
    activations_target = self._get_activations(target_batch)
    return (activations_pred, activations_target)

def get_value(self, groups=None, states=None):
    """
        :param groups:
        :return:
            total_results: dict of kind {'mean': score mean, 'std': score std}
            group_results: None, if groups is None;
                else dict {group_idx: {'mean': score mean among group, 'std': score std among group}}
        """
    if states is not None:
        target_class_freq_by_image_total, target_class_freq_by_image_mask, pred_class_freq_by_image_mask, activation_pairs = states
    else:
        target_class_freq_by_image_total = self.target_class_freq_by_image_total
        target_class_freq_by_image_mask = self.target_class_freq_by_image_mask
        pred_class_freq_by_image_mask = self.pred_class_freq_by_image_mask
        activation_pairs = self.individual_values
    target_class_freq_by_image_total = np.concatenate(target_class_freq_by_image_total, axis=0)
    target_class_freq_by_image_mask = np.concatenate(target_class_freq_by_image_mask, axis=0)
    pred_class_freq_by_image_mask = np.concatenate(pred_class_freq_by_image_mask, axis=0)
    activations_pred, activations_target = zip(*activation_pairs)
    activations_pred = np.concatenate(activations_pred, axis=0)
    activations_target = np.concatenate(activations_target, axis=0)
    total_results = {'mean': calculate_frechet_distance(activations_pred, activations_target, eps=self.eps), 'std': 0, **self.distribute_fid_to_classes(target_class_freq_by_image_mask, activations_pred, activations_target)}
    if groups is None:
        return (total_results, None)
    group_results = dict()
    grouping = get_groupings(groups)
    for label, index in grouping.items():
        if len(index) > 1:
            group_activations_pred = activations_pred[index]
            group_activations_target = activations_target[index]
            group_class_freq = target_class_freq_by_image_mask[index]
            group_results[label] = {'mean': calculate_frechet_distance(group_activations_pred, group_activations_target, eps=self.eps), 'std': 0, **self.distribute_fid_to_classes(group_class_freq, group_activations_pred, group_activations_target)}
        else:
            group_results[label] = dict(mean=float('nan'), std=0)
    return (total_results, group_results)

def distribute_fid_to_classes(self, class_freq, activations_pred, activations_target):
    real_fid = calculate_frechet_distance(activations_pred, activations_target, eps=self.eps)
    fid_no_images = Parallel(n_jobs=self.n_jobs)((delayed(calculade_fid_no_img)(img_i, activations_pred, activations_target, eps=self.eps) for img_i in range(activations_pred.shape[0])))
    errors = real_fid - fid_no_images
    return distribute_values_to_classes(class_freq, errors, self.segm_idx2name)

def _get_activations(self, batch):
    activations = self.model(batch)[0]
    if activations.shape[2] != 1 or activations.shape[3] != 1:
        activations = F.adaptive_avg_pool2d(activations, output_size=(1, 1))
    activations = activations.squeeze(-1).squeeze(-1).detach().cpu().numpy()
    return activations

class SSIM(torch.nn.Module):
    """SSIM. Modified from:
    https://github.com/Po-Hsun-Su/pytorch-ssim/blob/master/pytorch_ssim/__init__.py
    """

    def __init__(self, window_size=11, size_average=True):
        super().__init__()
        self.window_size = window_size
        self.size_average = size_average
        self.channel = 1
        self.register_buffer('window', self._create_window(window_size, self.channel))

    def forward(self, img1, img2):
        assert len(img1.shape) == 4
        channel = img1.size()[1]
        if channel == self.channel and self.window.data.type() == img1.data.type():
            window = self.window
        else:
            window = self._create_window(self.window_size, channel)
            window = window.type_as(img1)
            self.window = window
            self.channel = channel
        return self._ssim(img1, img2, window, self.window_size, channel, self.size_average)

    def _gaussian(self, window_size, sigma):
        gauss = torch.Tensor([np.exp(-(x - window_size // 2) ** 2 / float(2 * sigma ** 2)) for x in range(window_size)])
        return gauss / gauss.sum()

    def _create_window(self, window_size, channel):
        _1D_window = self._gaussian(window_size, 1.5).unsqueeze(1)
        _2D_window = _1D_window.mm(_1D_window.t()).float().unsqueeze(0).unsqueeze(0)
        return _2D_window.expand(channel, 1, window_size, window_size).contiguous()

    def _ssim(self, img1, img2, window, window_size, channel, size_average=True):
        mu1 = F.conv2d(img1, window, padding=window_size // 2, groups=channel)
        mu2 = F.conv2d(img2, window, padding=window_size // 2, groups=channel)
        mu1_sq = mu1.pow(2)
        mu2_sq = mu2.pow(2)
        mu1_mu2 = mu1 * mu2
        sigma1_sq = F.conv2d(img1 * img1, window, padding=window_size // 2, groups=channel) - mu1_sq
        sigma2_sq = F.conv2d(img2 * img2, window, padding=window_size // 2, groups=channel) - mu2_sq
        sigma12 = F.conv2d(img1 * img2, window, padding=window_size // 2, groups=channel) - mu1_mu2
        C1 = 0.01 ** 2
        C2 = 0.03 ** 2
        ssim_map = (2 * mu1_mu2 + C1) * (2 * sigma12 + C2) / ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
        if size_average:
            return ssim_map.mean()
        return ssim_map.mean(1).mean(1).mean(1)

    def _load_from_state_dict(self, state_dict, prefix, local_metadata, strict, missing_keys, unexpected_keys, error_msgs):
        return

def _ssim(self, img1, img2, window, window_size, channel, size_average=True):
    mu1 = F.conv2d(img1, window, padding=window_size // 2, groups=channel)
    mu2 = F.conv2d(img2, window, padding=window_size // 2, groups=channel)
    mu1_sq = mu1.pow(2)
    mu2_sq = mu2.pow(2)
    mu1_mu2 = mu1 * mu2
    sigma1_sq = F.conv2d(img1 * img1, window, padding=window_size // 2, groups=channel) - mu1_sq
    sigma2_sq = F.conv2d(img2 * img2, window, padding=window_size // 2, groups=channel) - mu2_sq
    sigma12 = F.conv2d(img1 * img2, window, padding=window_size // 2, groups=channel) - mu1_mu2
    C1 = 0.01 ** 2
    C2 = 0.03 ** 2
    ssim_map = (2 * mu1_mu2 + C1) * (2 * sigma12 + C2) / ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
    if size_average:
        return ssim_map.mean()
    return ssim_map.mean(1).mean(1).mean(1)

def l2(p0, p1, range=255.0):
    return 0.5 * np.mean((p0 / range - p1 / range) ** 2)

def psnr(p0, p1, peak=255.0):
    return 10 * np.log10(peak ** 2 / np.mean((1.0 * p0 - 1.0 * p1) ** 2))

def tensor2np(tensor_obj):
    return tensor_obj[0].cpu().float().numpy().transpose((1, 2, 0))

def tensor2vec(vector_tensor):
    return vector_tensor.data.cpu().numpy()[:, :, 0, 0]

class DistModel(BaseModel):

    def name(self):
        return self.model_name

    def initialize(self, model='net-lin', net='alex', colorspace='Lab', pnet_rand=False, pnet_tune=False, model_path=None, use_gpu=True, printNet=False, spatial=False, is_train=False, lr=0.0001, beta1=0.5, version='0.1'):
        """
        INPUTS
            model - ['net-lin'] for linearly calibrated network
                    ['net'] for off-the-shelf network
                    ['L2'] for L2 distance in Lab colorspace
                    ['SSIM'] for ssim in RGB colorspace
            net - ['squeeze','alex','vgg']
            model_path - if None, will look in weights/[NET_NAME].pth
            colorspace - ['Lab','RGB'] colorspace to use for L2 and SSIM
            use_gpu - bool - whether or not to use a GPU
            printNet - bool - whether or not to print network architecture out
            spatial - bool - whether to output an array containing varying distances across spatial dimensions
            spatial_shape - if given, output spatial shape. if None then spatial shape is determined automatically via spatial_factor (see below).
            spatial_factor - if given, specifies upsampling factor relative to the largest spatial extent of a convolutional layer. if None then resized to size of input images.
            spatial_order - spline order of filter for upsampling in spatial mode, by default 1 (bilinear).
            is_train - bool - [True] for training mode
            lr - float - initial learning rate
            beta1 - float - initial momentum term for adam
            version - 0.1 for latest, 0.0 was original (with a bug)
        """
        BaseModel.initialize(self, use_gpu=use_gpu)
        self.model = model
        self.net = net
        self.is_train = is_train
        self.spatial = spatial
        self.model_name = '%s [%s]' % (model, net)
        if self.model == 'net-lin':
            self.net = PNetLin(pnet_rand=pnet_rand, pnet_tune=pnet_tune, pnet_type=net, use_dropout=True, spatial=spatial, version=version, lpips=True)
            kw = dict(map_location='cpu')
            if model_path is None:
                import inspect
                model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'models', 'lpips_models', f'{net}.pth'))
            if not is_train:
                self.net.load_state_dict(torch.load(model_path, **kw), strict=False)
        elif self.model == 'net':
            self.net = PNetLin(pnet_rand=pnet_rand, pnet_type=net, lpips=False)
        elif self.model in ['L2', 'l2']:
            self.net = L2(use_gpu=use_gpu, colorspace=colorspace)
            self.model_name = 'L2'
        elif self.model in ['DSSIM', 'dssim', 'SSIM', 'ssim']:
            self.net = DSSIM(use_gpu=use_gpu, colorspace=colorspace)
            self.model_name = 'SSIM'
        else:
            raise ValueError('Model [%s] not recognized.' % self.model)
        self.trainable_parameters = list(self.net.parameters())
        if self.is_train:
            self.rankLoss = BCERankingLoss()
            self.trainable_parameters += list(self.rankLoss.net.parameters())
            self.lr = lr
            self.old_lr = lr
            self.optimizer_net = torch.optim.Adam(self.trainable_parameters, lr=lr, betas=(beta1, 0.999))
        else:
            self.net.eval()
        if printNet:
            print('---------- Networks initialized -------------')
            print_network(self.net)
            print('-----------------------------------------------')

    def forward(self, in0, in1, retPerLayer=False):
        """ Function computes the distance between image patches in0 and in1
        INPUTS
            in0, in1 - torch.Tensor object of shape Nx3xXxY - image patch scaled to [-1,1]
        OUTPUT
            computed distances between in0 and in1
        """
        return self.net(in0, in1, retPerLayer=retPerLayer)

    def optimize_parameters(self):
        self.forward_train()
        self.optimizer_net.zero_grad()
        self.backward_train()
        self.optimizer_net.step()
        self.clamp_weights()

    def clamp_weights(self):
        for module in self.net.modules():
            if hasattr(module, 'weight') and module.kernel_size == (1, 1):
                module.weight.data = torch.clamp(module.weight.data, min=0)

    def set_input(self, data):
        self.input_ref = data['ref']
        self.input_p0 = data['p0']
        self.input_p1 = data['p1']
        self.input_judge = data['judge']

    def forward_train(self):
        assert False, "We shoud've not get here when using LPIPS as a metric"
        self.d0 = self(self.var_ref, self.var_p0)
        self.d1 = self(self.var_ref, self.var_p1)
        self.acc_r = self.compute_accuracy(self.d0, self.d1, self.input_judge)
        self.var_judge = Variable(1.0 * self.input_judge).view(self.d0.size())
        self.loss_total = self.rankLoss(self.d0, self.d1, self.var_judge * 2.0 - 1.0)
        return self.loss_total

    def backward_train(self):
        torch.mean(self.loss_total).backward()

    def compute_accuracy(self, d0, d1, judge):
        """ d0, d1 are Variables, judge is a Tensor """
        d1_lt_d0 = (d1 < d0).cpu().data.numpy().flatten()
        judge_per = judge.cpu().numpy().flatten()
        return d1_lt_d0 * judge_per + (1 - d1_lt_d0) * (1 - judge_per)

    def get_current_errors(self):
        retDict = OrderedDict([('loss_total', self.loss_total.data.cpu().numpy()), ('acc_r', self.acc_r)])
        for key in retDict.keys():
            retDict[key] = np.mean(retDict[key])
        return retDict

    def get_current_visuals(self):
        zoom_factor = 256 / self.var_ref.data.size()[2]
        ref_img = tensor2im(self.var_ref.data)
        p0_img = tensor2im(self.var_p0.data)
        p1_img = tensor2im(self.var_p1.data)
        ref_img_vis = zoom(ref_img, [zoom_factor, zoom_factor, 1], order=0)
        p0_img_vis = zoom(p0_img, [zoom_factor, zoom_factor, 1], order=0)
        p1_img_vis = zoom(p1_img, [zoom_factor, zoom_factor, 1], order=0)
        return OrderedDict([('ref', ref_img_vis), ('p0', p0_img_vis), ('p1', p1_img_vis)])

    def save(self, path, label):
        if self.use_gpu:
            self.save_network(self.net.module, path, '', label)
        else:
            self.save_network(self.net, path, '', label)
        self.save_network(self.rankLoss.net, path, 'rank', label)

    def update_learning_rate(self, nepoch_decay):
        lrd = self.lr / nepoch_decay
        lr = self.old_lr - lrd
        for param_group in self.optimizer_net.param_groups:
            param_group['lr'] = lr
        print('update lr [%s] decay: %f -> %f' % (type, self.old_lr, lr))
        self.old_lr = lr

def compute_accuracy(self, d0, d1, judge):
    """ d0, d1 are Variables, judge is a Tensor """
    d1_lt_d0 = (d1 < d0).cpu().data.numpy().flatten()
    judge_per = judge.cpu().numpy().flatten()
    return d1_lt_d0 * judge_per + (1 - d1_lt_d0) * (1 - judge_per)

def get_current_errors(self):
    retDict = OrderedDict([('loss_total', self.loss_total.data.cpu().numpy()), ('acc_r', self.acc_r)])
    for key in retDict.keys():
        retDict[key] = np.mean(retDict[key])
    return retDict

def score_2afc_dataset(data_loader, func, name=''):
    """ Function computes Two Alternative Forced Choice (2AFC) score using
        distance function 'func' in dataset 'data_loader'
    INPUTS
        data_loader - CustomDatasetDataLoader object - contains a TwoAFCDataset inside
        func - callable distance function - calling d=func(in0,in1) should take 2
            pytorch tensors with shape Nx3xXxY, and return numpy array of length N
    OUTPUTS
        [0] - 2AFC score in [0,1], fraction of time func agrees with human evaluators
        [1] - dictionary with following elements
            d0s,d1s - N arrays containing distances between reference patch to perturbed patches
            gts - N array in [0,1], preferred patch selected by human evaluators
                (closer to "0" for left patch p0, "1" for right patch p1,
                "0.6" means 60pct people preferred right patch, 40pct preferred left)
            scores - N array in [0,1], corresponding to what percentage function agreed with humans
    CONSTS
        N - number of test triplets in data_loader
    """
    d0s = []
    d1s = []
    gts = []
    for data in tqdm(data_loader.load_data(), desc=name):
        d0s += func(data['ref'], data['p0']).data.cpu().numpy().flatten().tolist()
        d1s += func(data['ref'], data['p1']).data.cpu().numpy().flatten().tolist()
        gts += data['judge'].cpu().numpy().flatten().tolist()
    d0s = np.array(d0s)
    d1s = np.array(d1s)
    gts = np.array(gts)
    scores = (d0s < d1s) * (1.0 - gts) + (d1s < d0s) * gts + (d1s == d0s) * 0.5
    return (np.mean(scores), dict(d0s=d0s, d1s=d1s, gts=gts, scores=scores))

def score_jnd_dataset(data_loader, func, name=''):
    """ Function computes JND score using distance function 'func' in dataset 'data_loader'
    INPUTS
        data_loader - CustomDatasetDataLoader object - contains a JNDDataset inside
        func - callable distance function - calling d=func(in0,in1) should take 2
            pytorch tensors with shape Nx3xXxY, and return pytorch array of length N
    OUTPUTS
        [0] - JND score in [0,1], mAP score (area under precision-recall curve)
        [1] - dictionary with following elements
            ds - N array containing distances between two patches shown to human evaluator
            sames - N array containing fraction of people who thought the two patches were identical
    CONSTS
        N - number of test triplets in data_loader
    """
    ds = []
    gts = []
    for data in tqdm(data_loader.load_data(), desc=name):
        ds += func(data['p0'], data['p1']).data.cpu().numpy().tolist()
        gts += data['same'].cpu().numpy().flatten().tolist()
    sames = np.array(gts)
    ds = np.array(ds)
    sorted_inds = np.argsort(ds)
    ds_sorted = ds[sorted_inds]
    sames_sorted = sames[sorted_inds]
    TPs = np.cumsum(sames_sorted)
    FPs = np.cumsum(1 - sames_sorted)
    FNs = np.sum(sames_sorted) - TPs
    precs = TPs / (TPs + FPs)
    recs = TPs / (TPs + FNs)
    score = voc_ap(recs, precs)
    return (score, dict(ds=ds, sames=sames))

def spatial_average(in_tens, keepdim=True):
    return in_tens.mean([2, 3], keepdim=keepdim)

def print_network(net):
    num_params = 0
    for param in net.parameters():
        num_params += param.numel()
    print('Network', net)
    print('Total number of parameters: %d' % num_params)

def get_activations(files, model, batch_size=50, dims=2048, cuda=False, verbose=False, keep_size=False):
    """Calculates the activations of the pool_3 layer for all images.

    Params:
    -- files       : List of image files paths
    -- model       : Instance of inception model
    -- batch_size  : Batch size of images for the model to process at once.
                     Make sure that the number of samples is a multiple of
                     the batch size, otherwise some samples are ignored. This
                     behavior is retained to match the original FID score
                     implementation.
    -- dims        : Dimensionality of features returned by Inception
    -- cuda        : If set to True, use GPU
    -- verbose     : If set to True and parameter out_step is given, the number
                     of calculated batches is reported.
    Returns:
    -- A numpy array of dimension (num images, dims) that contains the
       activations of the given tensor when feeding inception with the
       query tensor.
    """
    model.eval()
    if len(files) % batch_size != 0:
        print('Warning: number of images is not a multiple of the batch size. Some samples are going to be ignored.')
    if batch_size > len(files):
        print('Warning: batch size is bigger than the data size. Setting batch size to data size')
        batch_size = len(files)
    n_batches = len(files) // batch_size
    n_used_imgs = n_batches * batch_size
    pred_arr = np.empty((n_used_imgs, dims))
    for i in tqdm(range(n_batches)):
        if verbose:
            print('\rPropagating batch %d/%d' % (i + 1, n_batches), end='', flush=True)
        start = i * batch_size
        end = start + batch_size
        t = transform if not keep_size else ToTensor()
        if isinstance(files[0], pathlib.PosixPath):
            images = [t(Image.open(str(f))) for f in files[start:end]]
        elif isinstance(files[0], Image.Image):
            images = [t(f) for f in files[start:end]]
        else:
            raise ValueError(f'Unknown data type for image: {type(files[0])}')
        batch = torch.stack(images)
        if cuda:
            batch = batch.cuda()
        pred = model(batch)[0]
        if pred.shape[2] != 1 or pred.shape[3] != 1:
            pred = adaptive_avg_pool2d(pred, output_size=(1, 1))
        pred_arr[start:end] = pred.cpu().data.numpy().reshape(batch_size, -1)
    if verbose:
        print(' done')
    return pred_arr

def calculate_activation_statistics(files, model, batch_size=50, dims=2048, cuda=False, verbose=False, keep_size=False):
    """Calculation of the statistics used by the FID.
    Params:
    -- files       : List of image files paths
    -- model       : Instance of inception model
    -- batch_size  : The images numpy array is split into batches with
                     batch size batch_size. A reasonable batch size
                     depends on the hardware.
    -- dims        : Dimensionality of features returned by Inception
    -- cuda        : If set to True, use GPU
    -- verbose     : If set to True and parameter out_step is given, the
                     number of calculated batches is reported.
    Returns:
    -- mu    : The mean over samples of the activations of the pool_3 layer of
               the inception model.
    -- sigma : The covariance matrix of the activations of the pool_3 layer of
               the inception model.
    """
    act = get_activations(files, model, batch_size, dims, cuda, verbose, keep_size=keep_size)
    mu = np.mean(act, axis=0)
    sigma = np.cov(act, rowvar=False)
    return (mu, sigma)

def calculate_fid_given_paths(paths, batch_size, cuda, dims):
    """Calculates the FID of two paths"""
    for p in paths:
        if not os.path.exists(p):
            raise RuntimeError('Invalid path: %s' % p)
    block_idx = InceptionV3.BLOCK_INDEX_BY_DIM[dims]
    model = InceptionV3([block_idx])
    if cuda:
        model.cuda()
    m1, s1 = _compute_statistics_of_path(paths[0], model, batch_size, dims, cuda)
    m2, s2 = _compute_statistics_of_path(paths[1], model, batch_size, dims, cuda)
    fid_value = calculate_frechet_distance(m1, s1, m2, s2)
    return fid_value

def calculate_fid_given_images(images, batch_size, cuda, dims, use_globals=False, keep_size=False):
    if use_globals:
        global FID_MODEL
    for imgs in images:
        if isinstance(imgs, list) and isinstance(imgs[0], (Image.Image, JpegImagePlugin.JpegImageFile)):
            pass
        else:
            raise RuntimeError('Invalid images')
    block_idx = InceptionV3.BLOCK_INDEX_BY_DIM[dims]
    if 'FID_MODEL' not in globals() or not use_globals:
        model = InceptionV3([block_idx])
        if cuda:
            model.cuda()
        if use_globals:
            FID_MODEL = model
    else:
        model = FID_MODEL
    m1, s1 = _compute_statistics_of_images(images[0], model, batch_size, dims, cuda, keep_size=False)
    m2, s2 = _compute_statistics_of_images(images[1], model, batch_size, dims, cuda, keep_size=False)
    fid_value = calculate_frechet_distance(m1, s1, m2, s2)
    return fid_value

class SegmentationMask:

    def __init__(self, confidence_threshold=0.5, rigidness_mode=RigidnessMode.rigid, max_object_area=0.3, min_mask_area=0.02, downsample_levels=6, num_variants_per_mask=4, max_mask_intersection=0.5, max_foreground_coverage=0.5, max_foreground_intersection=0.5, max_hidden_area=0.2, max_scale_change=0.25, horizontal_flip=True, max_vertical_shift=0.1, position_shuffle=True):
        """
        :param confidence_threshold: float; threshold for confidence of the panoptic segmentator to allow for
        the instance.
        :param rigidness_mode: RigidnessMode object
            when soft, checks intersection only with the object from which the mask_object was produced
            when rigid, checks intersection with any foreground class object
        :param max_object_area: float; allowed upper bound for to be considered as mask_object.
        :param min_mask_area: float; lower bound for mask to be considered valid
        :param downsample_levels: int; defines width of the resized segmentation to obtain shifted masks;
        :param num_variants_per_mask: int; maximal number of the masks for the same object;
        :param max_mask_intersection: float; maximum allowed area fraction of intersection for 2 masks
        produced by horizontal shift of the same mask_object; higher value -> more diversity
        :param max_foreground_coverage: float; maximum allowed area fraction of intersection for foreground object to be
        covered by mask; lower value -> less the objects are covered
        :param max_foreground_intersection: float; maximum allowed area of intersection for the mask with foreground
        object; lower value -> mask is more on the background than on the objects
        :param max_hidden_area: upper bound on part of the object hidden by shifting object outside the screen area;
        :param max_scale_change: allowed scale change for the mask_object;
        :param horizontal_flip: if horizontal flips are allowed;
        :param max_vertical_shift: amount of vertical movement allowed;
        :param position_shuffle: shuffle
        """
        assert DETECTRON_INSTALLED, 'Cannot use SegmentationMask without detectron2'
        self.cfg = get_cfg()
        self.cfg.merge_from_file(model_zoo.get_config_file('COCO-PanopticSegmentation/panoptic_fpn_R_101_3x.yaml'))
        self.cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url('COCO-PanopticSegmentation/panoptic_fpn_R_101_3x.yaml')
        self.cfg.MODEL.PANOPTIC_FPN.COMBINE.INSTANCES_CONFIDENCE_THRESH = confidence_threshold
        self.predictor = DefaultPredictor(self.cfg)
        self.rigidness_mode = RigidnessMode(rigidness_mode)
        self.max_object_area = max_object_area
        self.min_mask_area = min_mask_area
        self.downsample_levels = downsample_levels
        self.num_variants_per_mask = num_variants_per_mask
        self.max_mask_intersection = max_mask_intersection
        self.max_foreground_coverage = max_foreground_coverage
        self.max_foreground_intersection = max_foreground_intersection
        self.max_hidden_area = max_hidden_area
        self.position_shuffle = position_shuffle
        self.max_scale_change = max_scale_change
        self.horizontal_flip = horizontal_flip
        self.max_vertical_shift = max_vertical_shift

    def get_segmentation(self, img):
        im = img_as_ubyte(img)
        panoptic_seg, segment_info = self.predictor(im)['panoptic_seg']
        return (panoptic_seg, segment_info)

    @staticmethod
    def _is_power_of_two(n):
        return n != 0 and n & n - 1 == 0

    def identify_candidates(self, panoptic_seg, segments_info):
        potential_mask_ids = []
        for segment in segments_info:
            if not segment['isthing']:
                continue
            mask = (panoptic_seg == segment['id']).int().detach().cpu().numpy()
            area = mask.sum().item() / np.prod(panoptic_seg.shape)
            if area >= self.max_object_area:
                continue
            potential_mask_ids.append(segment['id'])
        return potential_mask_ids

    def downsample_mask(self, mask):
        height, width = mask.shape
        if not (self._is_power_of_two(height) and self._is_power_of_two(width)):
            raise ValueError('Image sides are not power of 2.')
        num_iterations = width.bit_length() - 1 - self.downsample_levels
        if num_iterations < 0:
            raise ValueError(f'Width is lower than 2^{self.downsample_levels}.')
        if height.bit_length() - 1 < num_iterations:
            raise ValueError('Height is too low to perform downsampling')
        downsampled = mask
        for _ in range(num_iterations):
            downsampled = zero_corrected_countless(downsampled)
        return downsampled

    def _augmentation_params(self):
        scaling_factor = np.random.uniform(1 - self.max_scale_change, 1 + self.max_scale_change)
        if self.horizontal_flip:
            horizontal_flip = bool(np.random.choice(2))
        else:
            horizontal_flip = False
        vertical_shift = np.random.uniform(-self.max_vertical_shift, self.max_vertical_shift)
        return {'scaling_factor': scaling_factor, 'horizontal_flip': horizontal_flip, 'vertical_shift': vertical_shift}

    def _get_intersection(self, mask_array, mask_object):
        intersection = mask_array[mask_object.up:mask_object.down, mask_object.left:mask_object.right] & mask_object.mask
        return intersection

    def _check_masks_intersection(self, aug_mask, total_mask_area, prev_masks):
        for existing_mask in prev_masks:
            intersection_area = self._get_intersection(existing_mask, aug_mask).sum()
            intersection_existing = intersection_area / existing_mask.sum()
            intersection_current = 1 - (aug_mask.area() - intersection_area) / total_mask_area
            if intersection_existing > self.max_mask_intersection or intersection_current > self.max_mask_intersection:
                return False
        return True

    def _check_foreground_intersection(self, aug_mask, foreground):
        for existing_mask in foreground:
            intersection_area = self._get_intersection(existing_mask, aug_mask).sum()
            intersection_existing = intersection_area / existing_mask.sum()
            if intersection_existing > self.max_foreground_coverage:
                return False
            intersection_mask = intersection_area / aug_mask.area()
            if intersection_mask > self.max_foreground_intersection:
                return False
        return True

    def _move_mask(self, mask, foreground):
        orig_mask = ObjectMask(mask)
        chosen_masks = []
        chosen_parameters = []
        scaling_factor_lower_bound = 0.0
        for var_idx in range(self.num_variants_per_mask):
            augmentation_params = self._augmentation_params()
            augmentation_params['scaling_factor'] = min([augmentation_params['scaling_factor'], 2 * min(orig_mask.up, orig_mask.height - orig_mask.down) / orig_mask.height + 1.0, 2 * min(orig_mask.left, orig_mask.width - orig_mask.right) / orig_mask.width + 1.0])
            augmentation_params['scaling_factor'] = max([augmentation_params['scaling_factor'], scaling_factor_lower_bound])
            aug_mask = deepcopy(orig_mask)
            aug_mask.rescale(augmentation_params['scaling_factor'], inplace=True)
            if augmentation_params['horizontal_flip']:
                aug_mask.horizontal_flip(inplace=True)
            total_aug_area = aug_mask.area()
            if total_aug_area == 0:
                scaling_factor_lower_bound = 1.0
                continue
            vertical_area = aug_mask.mask.sum(axis=1) / total_aug_area
            max_hidden_up = np.searchsorted(vertical_area.cumsum(), self.max_hidden_area)
            max_hidden_down = np.searchsorted(vertical_area[::-1].cumsum(), self.max_hidden_area)
            augmentation_params['vertical_shift'] = np.clip(augmentation_params['vertical_shift'], -(aug_mask.up + max_hidden_up) / aug_mask.height, (aug_mask.height - aug_mask.down + max_hidden_down) / aug_mask.height)
            vertical_shift = int(round(aug_mask.height * augmentation_params['vertical_shift']))
            aug_mask.shift(vertical=vertical_shift, inplace=True)
            aug_mask.crop_to_canvas(vertical=True, horizontal=False, inplace=True)
            max_hidden_area = self.max_hidden_area - (1 - aug_mask.area() / total_aug_area)
            horizontal_area = aug_mask.mask.sum(axis=0) / total_aug_area
            max_hidden_left = np.searchsorted(horizontal_area.cumsum(), max_hidden_area)
            max_hidden_right = np.searchsorted(horizontal_area[::-1].cumsum(), max_hidden_area)
            allowed_shifts = np.arange(-max_hidden_left, aug_mask.width - (aug_mask.right - aug_mask.left) + max_hidden_right + 1)
            allowed_shifts = -(aug_mask.left - allowed_shifts)
            if self.position_shuffle:
                np.random.shuffle(allowed_shifts)
            mask_is_found = False
            for horizontal_shift in allowed_shifts:
                aug_mask_left = deepcopy(aug_mask)
                aug_mask_left.shift(horizontal=horizontal_shift, inplace=True)
                aug_mask_left.crop_to_canvas(inplace=True)
                prev_masks = [mask] + chosen_masks
                is_mask_suitable = self._check_masks_intersection(aug_mask_left, total_aug_area, prev_masks) & self._check_foreground_intersection(aug_mask_left, foreground)
                if is_mask_suitable:
                    aug_draw = aug_mask_left.restore_full_mask()
                    chosen_masks.append(aug_draw)
                    augmentation_params['horizontal_shift'] = horizontal_shift / aug_mask_left.width
                    chosen_parameters.append(augmentation_params)
                    mask_is_found = True
                    break
            if not mask_is_found:
                break
        return chosen_parameters

    def _prepare_mask(self, mask):
        height, width = mask.shape
        target_width = width if self._is_power_of_two(width) else 1 << width.bit_length()
        target_height = height if self._is_power_of_two(height) else 1 << height.bit_length()
        return resize(mask.astype('float32'), (target_height, target_width), order=0, mode='edge').round().astype('int32')

    def get_masks(self, im, return_panoptic=False):
        panoptic_seg, segments_info = self.get_segmentation(im)
        potential_mask_ids = self.identify_candidates(panoptic_seg, segments_info)
        panoptic_seg_scaled = self._prepare_mask(panoptic_seg.detach().cpu().numpy())
        downsampled = self.downsample_mask(panoptic_seg_scaled)
        scene_objects = []
        for segment in segments_info:
            if not segment['isthing']:
                continue
            mask = downsampled == segment['id']
            if not np.any(mask):
                continue
            scene_objects.append(mask)
        mask_set = []
        for mask_id in potential_mask_ids:
            mask = downsampled == mask_id
            if not np.any(mask):
                continue
            if self.rigidness_mode is RigidnessMode.soft:
                foreground = [mask]
            elif self.rigidness_mode is RigidnessMode.rigid:
                foreground = scene_objects
            else:
                raise ValueError(f'Unexpected rigidness_mode: {rigidness_mode}')
            masks_params = self._move_mask(mask, foreground)
            full_mask = ObjectMask((panoptic_seg == mask_id).detach().cpu().numpy())
            for params in masks_params:
                aug_mask = deepcopy(full_mask)
                aug_mask.rescale(params['scaling_factor'], inplace=True)
                if params['horizontal_flip']:
                    aug_mask.horizontal_flip(inplace=True)
                vertical_shift = int(round(aug_mask.height * params['vertical_shift']))
                horizontal_shift = int(round(aug_mask.width * params['horizontal_shift']))
                aug_mask.shift(vertical=vertical_shift, horizontal=horizontal_shift, inplace=True)
                aug_mask = aug_mask.restore_full_mask().astype('uint8')
                if aug_mask.mean() <= self.min_mask_area:
                    continue
                mask_set.append(aug_mask)
        if return_panoptic:
            return (mask_set, panoptic_seg.detach().cpu().numpy())
        else:
            return mask_set

def identify_candidates(self, panoptic_seg, segments_info):
    potential_mask_ids = []
    for segment in segments_info:
        if not segment['isthing']:
            continue
        mask = (panoptic_seg == segment['id']).int().detach().cpu().numpy()
        area = mask.sum().item() / np.prod(panoptic_seg.shape)
        if area >= self.max_object_area:
            continue
        potential_mask_ids.append(segment['id'])
    return potential_mask_ids

def async_copy_to(obj, dev, main_stream=None):
    if torch.is_tensor(obj):
        v = obj.cuda(dev, non_blocking=True)
        if main_stream is not None:
            v.data.record_stream(main_stream)
        return v
    elif isinstance(obj, collections.Mapping):
        return {k: async_copy_to(o, dev, main_stream) for k, o in obj.items()}
    elif isinstance(obj, collections.Sequence):
        return [async_copy_to(o, dev, main_stream) for o in obj]
    else:
        return obj

def gather_map(outputs):
    out = outputs[0]
    if torch.is_tensor(out):
        if out.dim() == 0:
            outputs = [o.unsqueeze(0) for o in outputs]
        return Gather.apply(target_device, dim, *outputs)
    elif out is None:
        return None
    elif isinstance(out, collections.Mapping):
        return {k: gather_map([o[k] for o in outputs]) for k in out}
    elif isinstance(out, collections.Sequence):
        return type(out)(map(gather_map, zip(*outputs)))

def dict_gather(outputs, target_device, dim=0):
    """
    Gathers variables from different GPUs on a specified device
      (-1 means the CPU), with dictionary support.
    """

    def gather_map(outputs):
        out = outputs[0]
        if torch.is_tensor(out):
            if out.dim() == 0:
                outputs = [o.unsqueeze(0) for o in outputs]
            return Gather.apply(target_device, dim, *outputs)
        elif out is None:
            return None
        elif isinstance(out, collections.Mapping):
            return {k: gather_map([o[k] for o in outputs]) for k in out}
        elif isinstance(out, collections.Sequence):
            return type(out)(map(gather_map, zip(*outputs)))
    return gather_map(outputs)

def patch_replication_callback(data_parallel):
    """
    Monkey-patch an existing `DataParallel` object. Add the replication callback.
    Useful when you have customized `DataParallel` implementation.

    Examples:
        > sync_bn = SynchronizedBatchNorm1d(10, eps=1e-5, affine=False)
        > sync_bn = DataParallel(sync_bn, device_ids=[0, 1])
        > patch_replication_callback(sync_bn)
        # this is equivalent to
        > sync_bn = SynchronizedBatchNorm1d(10, eps=1e-5, affine=False)
        > sync_bn = DataParallelWithCallback(sync_bn, device_ids=[0, 1])
    """
    assert isinstance(data_parallel, DataParallel)
    old_replicate = data_parallel.replicate

    @functools.wraps(old_replicate)
    def new_replicate(module, device_ids):
        modules = old_replicate(module, device_ids)
        execute_replication_callbacks(modules)
        return modules
    data_parallel.replicate = new_replicate

def as_numpy(v):
    if isinstance(v, Variable):
        v = v.data
    return v.cpu().numpy()

def _find_bn(module):
    for m in module.modules():
        if isinstance(m, (nn.BatchNorm1d, nn.BatchNorm2d, SynchronizedBatchNorm1d, SynchronizedBatchNorm2d)):
            return m

def as_variable(obj):
    if isinstance(obj, Variable):
        return obj
    if isinstance(obj, collections.Sequence):
        return [as_variable(v) for v in obj]
    elif isinstance(obj, collections.Mapping):
        return {k: as_variable(v) for k, v in obj.items()}
    else:
        return Variable(obj)

def as_numpy(obj):
    if isinstance(obj, collections.Sequence):
        return [as_numpy(v) for v in obj]
    elif isinstance(obj, collections.Mapping):
        return {k: as_numpy(v) for k, v in obj.items()}
    elif isinstance(obj, Variable):
        return obj.data.cpu().numpy()
    elif torch.is_tensor(obj):
        return obj.cpu().numpy()
    else:
        return np.array(obj)

def mark_volatile(obj):
    if torch.is_tensor(obj):
        obj = Variable(obj)
    if isinstance(obj, Variable):
        obj.no_grad = True
        return obj
    elif isinstance(obj, collections.Mapping):
        return {k: mark_volatile(o) for k, o in obj.items()}
    elif isinstance(obj, collections.Sequence):
        return [mark_volatile(o) for o in obj]
    else:
        return obj

def giou_loss(boxes1, boxes2):
    """

    :param boxes1: (N, 4) (x1,y1,x2,y2)
    :param boxes2: (N, 4) (x1,y1,x2,y2)
    :return:
    """
    giou, iou = generalized_box_iou(boxes1, boxes2)
    return ((1 - giou).mean(), iou)

def generate_bbox_mask(bbox_mask, bbox):
    b, h, w = bbox_mask.shape
    for i in range(b):
        bbox_i = bbox[i].cpu().tolist()
        bbox_mask[i, int(bbox_i[1]):int(bbox_i[1] + bbox_i[3] - 1), int(bbox_i[0]):int(bbox_i[0] + bbox_i[2] - 1)] = 1
    return bbox_mask

class TensorDict(OrderedDict):
    """Container mainly used for dicts of torch tensors. Extends OrderedDict with pytorch functionality."""

    def concat(self, other):
        """Concatenates two dicts without copying internal data."""
        return TensorDict(self, **other)

    def copy(self):
        return TensorDict(super(TensorDict, self).copy())

    def __deepcopy__(self, memodict={}):
        return TensorDict(copy.deepcopy(list(self), memodict))

    def __getattr__(self, name):
        if not hasattr(torch.Tensor, name):
            raise AttributeError("'TensorDict' object has not attribute '{}'".format(name))

        def apply_attr(*args, **kwargs):
            return TensorDict({n: getattr(e, name)(*args, **kwargs) if hasattr(e, name) else e for n, e in self.items()})
        return apply_attr

    def attribute(self, attr: str, *args):
        return TensorDict({n: getattr(e, attr, *args) for n, e in self.items()})

    def apply(self, fn, *args, **kwargs):
        return TensorDict({n: fn(e, *args, **kwargs) for n, e in self.items()})

    @staticmethod
    def _iterable(a):
        return isinstance(a, (TensorDict, list))

@staticmethod
def _iterable(a):
    return isinstance(a, (TensorDict, list))

class TensorList(list):
    """Container mainly used for lists of torch tensors. Extends lists with pytorch functionality."""

    def __init__(self, list_of_tensors=None):
        if list_of_tensors is None:
            list_of_tensors = list()
        super(TensorList, self).__init__(list_of_tensors)

    def __deepcopy__(self, memodict={}):
        return TensorList(copy.deepcopy(list(self), memodict))

    def __getitem__(self, item):
        if isinstance(item, int):
            return super(TensorList, self).__getitem__(item)
        elif isinstance(item, (tuple, list)):
            return TensorList([super(TensorList, self).__getitem__(i) for i in item])
        else:
            return TensorList(super(TensorList, self).__getitem__(item))

    def __add__(self, other):
        if TensorList._iterable(other):
            return TensorList([e1 + e2 for e1, e2 in zip(self, other)])
        return TensorList([e + other for e in self])

    def __radd__(self, other):
        if TensorList._iterable(other):
            return TensorList([e2 + e1 for e1, e2 in zip(self, other)])
        return TensorList([other + e for e in self])

    def __iadd__(self, other):
        if TensorList._iterable(other):
            for i, e2 in enumerate(other):
                self[i] += e2
        else:
            for i in range(len(self)):
                self[i] += other
        return self

    def __sub__(self, other):
        if TensorList._iterable(other):
            return TensorList([e1 - e2 for e1, e2 in zip(self, other)])
        return TensorList([e - other for e in self])

    def __rsub__(self, other):
        if TensorList._iterable(other):
            return TensorList([e2 - e1 for e1, e2 in zip(self, other)])
        return TensorList([other - e for e in self])

    def __isub__(self, other):
        if TensorList._iterable(other):
            for i, e2 in enumerate(other):
                self[i] -= e2
        else:
            for i in range(len(self)):
                self[i] -= other
        return self

    def __mul__(self, other):
        if TensorList._iterable(other):
            return TensorList([e1 * e2 for e1, e2 in zip(self, other)])
        return TensorList([e * other for e in self])

    def __rmul__(self, other):
        if TensorList._iterable(other):
            return TensorList([e2 * e1 for e1, e2 in zip(self, other)])
        return TensorList([other * e for e in self])

    def __imul__(self, other):
        if TensorList._iterable(other):
            for i, e2 in enumerate(other):
                self[i] *= e2
        else:
            for i in range(len(self)):
                self[i] *= other
        return self

    def __truediv__(self, other):
        if TensorList._iterable(other):
            return TensorList([e1 / e2 for e1, e2 in zip(self, other)])
        return TensorList([e / other for e in self])

    def __rtruediv__(self, other):
        if TensorList._iterable(other):
            return TensorList([e2 / e1 for e1, e2 in zip(self, other)])
        return TensorList([other / e for e in self])

    def __itruediv__(self, other):
        if TensorList._iterable(other):
            for i, e2 in enumerate(other):
                self[i] /= e2
        else:
            for i in range(len(self)):
                self[i] /= other
        return self

    def __matmul__(self, other):
        if TensorList._iterable(other):
            return TensorList([e1 @ e2 for e1, e2 in zip(self, other)])
        return TensorList([e @ other for e in self])

    def __rmatmul__(self, other):
        if TensorList._iterable(other):
            return TensorList([e2 @ e1 for e1, e2 in zip(self, other)])
        return TensorList([other @ e for e in self])

    def __imatmul__(self, other):
        if TensorList._iterable(other):
            for i, e2 in enumerate(other):
                self[i] @= e2
        else:
            for i in range(len(self)):
                self[i] @= other
        return self

    def __mod__(self, other):
        if TensorList._iterable(other):
            return TensorList([e1 % e2 for e1, e2 in zip(self, other)])
        return TensorList([e % other for e in self])

    def __rmod__(self, other):
        if TensorList._iterable(other):
            return TensorList([e2 % e1 for e1, e2 in zip(self, other)])
        return TensorList([other % e for e in self])

    def __pos__(self):
        return TensorList([+e for e in self])

    def __neg__(self):
        return TensorList([-e for e in self])

    def __le__(self, other):
        if TensorList._iterable(other):
            return TensorList([e1 <= e2 for e1, e2 in zip(self, other)])
        return TensorList([e <= other for e in self])

    def __ge__(self, other):
        if TensorList._iterable(other):
            return TensorList([e1 >= e2 for e1, e2 in zip(self, other)])
        return TensorList([e >= other for e in self])

    def concat(self, other):
        return TensorList(super(TensorList, self).__add__(other))

    def copy(self):
        return TensorList(super(TensorList, self).copy())

    def unroll(self):
        if not any((isinstance(t, TensorList) for t in self)):
            return self
        new_list = TensorList()
        for t in self:
            if isinstance(t, TensorList):
                new_list.extend(t.unroll())
            else:
                new_list.append(t)
        return new_list

    def list(self):
        return list(self)

    def attribute(self, attr: str, *args):
        return TensorList([getattr(e, attr, *args) for e in self])

    def apply(self, fn):
        return TensorList([fn(e) for e in self])

    def __getattr__(self, name):
        if not hasattr(torch.Tensor, name):
            raise AttributeError("'TensorList' object has not attribute '{}'".format(name))

        def apply_attr(*args, **kwargs):
            return TensorList([getattr(e, name)(*args, **kwargs) for e in self])
        return apply_attr

    @staticmethod
    def _iterable(a):
        return isinstance(a, (TensorList, list))

@staticmethod
def _iterable(a):
    return isinstance(a, (TensorList, list))

def islist(a):
    return isinstance(a, TensorList)

class CenterNetHeatMap(object):

    @staticmethod
    def generate_score_map(fmap, gt_class, gt_wh, centers_int, min_overlap):
        radius = CenterNetHeatMap.get_gaussian_radius(gt_wh, min_overlap)
        radius = torch.clamp_min(radius, 0)
        radius = radius.type(torch.int).cpu().numpy()
        for i in range(gt_class.shape[0]):
            channel_index = gt_class[i]
            CenterNetHeatMap.draw_gaussian(fmap[channel_index], centers_int[i], radius[i])

    @staticmethod
    def get_gaussian_radius(box_size, min_overlap):
        """
        copyed from CornerNet
        box_size (w, h), it could be a torch.Tensor, numpy.ndarray, list or tuple
        notice: we are using a bug-version, please refer to fix bug version in CornerNet
        """
        box_tensor = box_size
        width, height = (box_tensor[..., 0], box_tensor[..., 1])
        a1 = 1
        b1 = height + width
        c1 = width * height * (1 - min_overlap) / (1 + min_overlap)
        sq1 = torch.sqrt(b1 ** 2 - 4 * a1 * c1)
        r1 = (b1 + sq1) / 2
        a2 = 4
        b2 = 2 * (height + width)
        c2 = (1 - min_overlap) * width * height
        sq2 = torch.sqrt(b2 ** 2 - 4 * a2 * c2)
        r2 = (b2 + sq2) / 2
        a3 = 4 * min_overlap
        b3 = -2 * min_overlap * (height + width)
        c3 = (min_overlap - 1) * width * height
        sq3 = torch.sqrt(b3 ** 2 - 4 * a3 * c3)
        r3 = (b3 + sq3) / 2
        return torch.min(r1, torch.min(r2, r3))

    @staticmethod
    def gaussian2D(radius, sigma=1):
        m, n = radius
        y, x = np.ogrid[-m:m + 1, -n:n + 1]
        gauss = np.exp(-(x * x + y * y) / (2 * sigma * sigma))
        gauss[gauss < np.finfo(gauss.dtype).eps * gauss.max()] = 0
        return gauss

    @staticmethod
    def draw_gaussian(fmap, center, radius, k=1):
        diameter = 2 * radius + 1
        gaussian = CenterNetHeatMap.gaussian2D((radius, radius), sigma=diameter / 6)
        gaussian = torch.Tensor(gaussian)
        x, y = (int(center[0]), int(center[1]))
        height, width = fmap.shape[:2]
        left, right = (min(x, radius), min(width - x, radius + 1))
        top, bottom = (min(y, radius), min(height - y, radius + 1))
        masked_fmap = fmap[y - top:y + bottom, x - left:x + right]
        masked_gaussian = gaussian[radius - top:radius + bottom, radius - left:radius + right]
        if min(masked_gaussian.shape) > 0 and min(masked_fmap.shape) > 0:
            masked_fmap = torch.max(masked_fmap, masked_gaussian * k)
            fmap[y - top:y + bottom, x - left:x + right] = masked_fmap

@staticmethod
def generate_score_map(fmap, gt_class, gt_wh, centers_int, min_overlap):
    radius = CenterNetHeatMap.get_gaussian_radius(gt_wh, min_overlap)
    radius = torch.clamp_min(radius, 0)
    radius = radius.type(torch.int).cpu().numpy()
    for i in range(gt_class.shape[0]):
        channel_index = gt_class[i]
        CenterNetHeatMap.draw_gaussian(fmap[channel_index], centers_int[i], radius[i])

class get_local(object):
    cache = {}
    is_activate = False

    def __init__(self, varname):
        self.varname = varname

    def __call__(self, func):
        if not type(self).is_activate:
            return func
        type(self).cache[func.__qualname__] = []
        c = Bytecode.from_code(func.__code__)
        extra_code = [Instr('STORE_FAST', '_res'), Instr('LOAD_FAST', self.varname), Instr('STORE_FAST', '_value'), Instr('LOAD_FAST', '_res'), Instr('LOAD_FAST', '_value'), Instr('BUILD_TUPLE', 2), Instr('STORE_FAST', '_result_tuple'), Instr('LOAD_FAST', '_result_tuple')]
        c[-1:-1] = extra_code
        func.__code__ = c.to_code()

        def wrapper(*args, **kwargs):
            res, values = func(*args, **kwargs)
            if isinstance(values, torch.Tensor):
                type(self).cache[func.__qualname__].append(values.detach().cpu().numpy())
            elif isinstance(values, list):
                type(self).cache[func.__qualname__].append([value.detach().cpu().numpy() for value in values])
            else:
                raise NotImplementedError
            return res
        return wrapper

    @classmethod
    def clear(cls):
        for key in cls.cache.keys():
            cls.cache[key] = []

    @classmethod
    def activate(cls):
        cls.is_activate = True

def __call__(self, func):
    if not type(self).is_activate:
        return func
    type(self).cache[func.__qualname__] = []
    c = Bytecode.from_code(func.__code__)
    extra_code = [Instr('STORE_FAST', '_res'), Instr('LOAD_FAST', self.varname), Instr('STORE_FAST', '_value'), Instr('LOAD_FAST', '_res'), Instr('LOAD_FAST', '_value'), Instr('BUILD_TUPLE', 2), Instr('STORE_FAST', '_result_tuple'), Instr('LOAD_FAST', '_result_tuple')]
    c[-1:-1] = extra_code
    func.__code__ = c.to_code()

    def wrapper(*args, **kwargs):
        res, values = func(*args, **kwargs)
        if isinstance(values, torch.Tensor):
            type(self).cache[func.__qualname__].append(values.detach().cpu().numpy())
        elif isinstance(values, list):
            type(self).cache[func.__qualname__].append([value.detach().cpu().numpy() for value in values])
        else:
            raise NotImplementedError
        return res
    return wrapper

def wrapper(*args, **kwargs):
    res, values = func(*args, **kwargs)
    if isinstance(values, torch.Tensor):
        type(self).cache[func.__qualname__].append(values.detach().cpu().numpy())
    elif isinstance(values, list):
        type(self).cache[func.__qualname__].append([value.detach().cpu().numpy() for value in values])
    else:
        raise NotImplementedError
    return res

class TrackerParams:
    """Class for tracker parameters."""

    def set_default_values(self, default_vals: dict):
        for name, val in default_vals.items():
            if not hasattr(self, name):
                setattr(self, name, val)

    def get(self, name: str, *default):
        """Get a parameter value with the given name. If it does not exists, it return the default value given as a
        second argument or returns an error if no default value is given."""
        if len(default) > 1:
            raise ValueError('Can only give one default value.')
        if not default:
            return getattr(self, name)
        return getattr(self, name, default[0])

    def has(self, name: str):
        """Check if there exist a parameter with the given name."""
        return hasattr(self, name)

def set_default_values(self, default_vals: dict):
    for name, val in default_vals.items():
        if not hasattr(self, name):
            setattr(self, name, val)

class FeatureParams:
    """Class for feature specific parameters"""

    def __init__(self, *args, **kwargs):
        if len(args) > 0:
            raise ValueError
        for name, val in kwargs.items():
            if isinstance(val, list):
                setattr(self, name, TensorList(val))
            else:
                setattr(self, name, val)

def __init__(self, *args, **kwargs):
    if len(args) > 0:
        raise ValueError
    for name, val in kwargs.items():
        if isinstance(val, list):
            setattr(self, name, TensorList(val))
        else:
            setattr(self, name, val)

class BaseTracker:
    """Base class for all trackers."""

    def __init__(self, params):
        self.params = params
        self.visdom = None

    def predicts_segmentation_mask(self):
        return False

    def initialize(self, image, info: dict) -> dict:
        """Overload this function in your tracker. This should initialize the model."""
        raise NotImplementedError

    def track(self, image, info: dict=None) -> dict:
        """Overload this function in your tracker. This should track in the frame and update the model."""
        raise NotImplementedError

    def visdom_draw_tracking(self, image, box, segmentation=None):
        if isinstance(box, OrderedDict):
            box = [v for k, v in box.items()]
        else:
            box = (box,)
        if segmentation is None:
            self.visdom.register((image, *box), 'Tracking', 1, 'Tracking')
        else:
            self.visdom.register((image, *box, segmentation), 'Tracking', 1, 'Tracking')

    def transform_bbox_to_crop(self, box_in, resize_factor, device, box_extract=None, crop_type='template'):
        if crop_type == 'template':
            crop_sz = torch.Tensor([self.params.template_size, self.params.template_size])
        elif crop_type == 'search':
            crop_sz = torch.Tensor([self.params.search_size, self.params.search_size])
        else:
            raise NotImplementedError
        box_in = torch.tensor(box_in)
        if box_extract is None:
            box_extract = box_in
        else:
            box_extract = torch.tensor(box_extract)
        template_bbox = transform_image_to_crop(box_in, box_extract, resize_factor, crop_sz, normalize=True)
        template_bbox = template_bbox.view(1, 1, 4).to(device)
        return template_bbox

    def _init_visdom(self, visdom_info, debug):
        visdom_info = {} if visdom_info is None else visdom_info
        self.pause_mode = False
        self.step = False
        self.next_seq = False
        if debug > 0 and visdom_info.get('use_visdom', True):
            try:
                self.visdom = Visdom(debug, {'handler': self._visdom_ui_handler, 'win_id': 'Tracking'}, visdom_info=visdom_info)
            except:
                time.sleep(0.5)
                print("!!! WARNING: Visdom could not start, so using matplotlib visualization instead !!!\n!!! Start Visdom in a separate terminal window by typing 'visdom' !!!")

    def _visdom_ui_handler(self, data):
        if data['event_type'] == 'KeyPress':
            if data['key'] == ' ':
                self.pause_mode = not self.pause_mode
            elif data['key'] == 'ArrowRight' and self.pause_mode:
                self.step = True
            elif data['key'] == 'n':
                self.next_seq = True

def visdom_draw_tracking(self, image, box, segmentation=None):
    if isinstance(box, OrderedDict):
        box = [v for k, v in box.items()]
    else:
        box = (box,)
    if segmentation is None:
        self.visdom.register((image, *box), 'Tracking', 1, 'Tracking')
    else:
        self.visdom.register((image, *box, segmentation), 'Tracking', 1, 'Tracking')

class OSTrack(BaseTracker):

    def __init__(self, params, dataset_name):
        super(OSTrack, self).__init__(params)
        network = build_ostrack(params.cfg, training=False)
        network.load_state_dict(torch.load(self.params.checkpoint, map_location='cpu')['net'], strict=True)
        self.cfg = params.cfg
        self.network = network.cuda()
        self.network.eval()
        self.preprocessor = Preprocessor()
        self.state = None
        self.feat_sz = self.cfg.TEST.SEARCH_SIZE // self.cfg.MODEL.BACKBONE.STRIDE
        self.output_window = hann2d(torch.tensor([self.feat_sz, self.feat_sz]).long(), centered=True).cuda()
        self.debug = params.debug
        self.use_visdom = params.debug
        self.frame_id = 0
        if self.debug:
            if not self.use_visdom:
                self.save_dir = 'debug'
                if not os.path.exists(self.save_dir):
                    os.makedirs(self.save_dir)
            else:
                self._init_visdom(None, 1)
        self.save_all_boxes = params.save_all_boxes
        self.z_dict1 = {}

    def initialize(self, image, info: dict):
        z_patch_arr, resize_factor, z_amask_arr = sample_target(image, info['init_bbox'], self.params.template_factor, output_sz=self.params.template_size)
        self.z_patch_arr = z_patch_arr
        template = self.preprocessor.process(z_patch_arr, z_amask_arr)
        with torch.no_grad():
            self.z_dict1 = template
        self.box_mask_z = None
        if self.cfg.MODEL.BACKBONE.CE_LOC:
            template_bbox = self.transform_bbox_to_crop(info['init_bbox'], resize_factor, template.tensors.device).squeeze(1)
            self.box_mask_z = generate_mask_cond(self.cfg, 1, template.tensors.device, template_bbox)
        self.state = info['init_bbox']
        self.frame_id = 0
        if self.save_all_boxes:
            'save all predicted boxes'
            all_boxes_save = info['init_bbox'] * self.cfg.MODEL.NUM_OBJECT_QUERIES
            return {'all_boxes': all_boxes_save}

    def track(self, image, info: dict=None):
        H, W, _ = image.shape
        self.frame_id += 1
        x_patch_arr, resize_factor, x_amask_arr = sample_target(image, self.state, self.params.search_factor, output_sz=self.params.search_size)
        search = self.preprocessor.process(x_patch_arr, x_amask_arr)
        with torch.no_grad():
            x_dict = search
            out_dict = self.network.forward(template=self.z_dict1.tensors, search=x_dict.tensors, ce_template_mask=self.box_mask_z)
        pred_score_map = out_dict['score_map']
        response = self.output_window * pred_score_map
        pred_boxes = self.network.box_head.cal_bbox(response, out_dict['size_map'], out_dict['offset_map'])
        pred_boxes = pred_boxes.view(-1, 4)
        pred_box = (pred_boxes.mean(dim=0) * self.params.search_size / resize_factor).tolist()
        self.state = clip_box(self.map_box_back(pred_box, resize_factor), H, W, margin=10)
        if self.debug:
            if not self.use_visdom:
                x1, y1, w, h = self.state
                image_BGR = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                cv2.rectangle(image_BGR, (int(x1), int(y1)), (int(x1 + w), int(y1 + h)), color=(0, 0, 255), thickness=2)
                save_path = os.path.join(self.save_dir, '%04d.jpg' % self.frame_id)
                cv2.imwrite(save_path, image_BGR)
            else:
                self.visdom.register((image, info['gt_bbox'].tolist(), self.state), 'Tracking', 1, 'Tracking')
                self.visdom.register(torch.from_numpy(x_patch_arr).permute(2, 0, 1), 'image', 1, 'search_region')
                self.visdom.register(torch.from_numpy(self.z_patch_arr).permute(2, 0, 1), 'image', 1, 'template')
                self.visdom.register(pred_score_map.view(self.feat_sz, self.feat_sz), 'heatmap', 1, 'score_map')
                self.visdom.register((pred_score_map * self.output_window).view(self.feat_sz, self.feat_sz), 'heatmap', 1, 'score_map_hann')
                if 'removed_indexes_s' in out_dict and out_dict['removed_indexes_s']:
                    removed_indexes_s = out_dict['removed_indexes_s']
                    removed_indexes_s = [removed_indexes_s_i.cpu().numpy() for removed_indexes_s_i in removed_indexes_s]
                    masked_search = gen_visualization(x_patch_arr, removed_indexes_s)
                    self.visdom.register(torch.from_numpy(masked_search).permute(2, 0, 1), 'image', 1, 'masked_search')
                while self.pause_mode:
                    if self.step:
                        self.step = False
                        break
        if self.save_all_boxes:
            'save all predictions'
            all_boxes = self.map_box_back_batch(pred_boxes * self.params.search_size / resize_factor, resize_factor)
            all_boxes_save = all_boxes.view(-1).tolist()
            return {'target_bbox': self.state, 'all_boxes': all_boxes_save}
        else:
            return {'target_bbox': self.state}

    def map_box_back(self, pred_box: list, resize_factor: float):
        cx_prev, cy_prev = (self.state[0] + 0.5 * self.state[2], self.state[1] + 0.5 * self.state[3])
        cx, cy, w, h = pred_box
        half_side = 0.5 * self.params.search_size / resize_factor
        cx_real = cx + (cx_prev - half_side)
        cy_real = cy + (cy_prev - half_side)
        return [cx_real - 0.5 * w, cy_real - 0.5 * h, w, h]

    def map_box_back_batch(self, pred_box: torch.Tensor, resize_factor: float):
        cx_prev, cy_prev = (self.state[0] + 0.5 * self.state[2], self.state[1] + 0.5 * self.state[3])
        cx, cy, w, h = pred_box.unbind(-1)
        half_side = 0.5 * self.params.search_size / resize_factor
        cx_real = cx + (cx_prev - half_side)
        cy_real = cy + (cy_prev - half_side)
        return torch.stack([cx_real - 0.5 * w, cy_real - 0.5 * h, w, h], dim=-1)

    def add_hook(self):
        conv_features, enc_attn_weights, dec_attn_weights = ([], [], [])
        for i in range(12):
            self.network.backbone.blocks[i].attn.register_forward_hook(lambda self, input, output: enc_attn_weights.append(output[1]))
        self.enc_attn_weights = enc_attn_weights

def track(self, image, info: dict=None):
    H, W, _ = image.shape
    self.frame_id += 1
    x_patch_arr, resize_factor, x_amask_arr = sample_target(image, self.state, self.params.search_factor, output_sz=self.params.search_size)
    search = self.preprocessor.process(x_patch_arr, x_amask_arr)
    with torch.no_grad():
        x_dict = search
        out_dict = self.network.forward(template=self.z_dict1.tensors, search=x_dict.tensors, ce_template_mask=self.box_mask_z)
    pred_score_map = out_dict['score_map']
    response = self.output_window * pred_score_map
    pred_boxes = self.network.box_head.cal_bbox(response, out_dict['size_map'], out_dict['offset_map'])
    pred_boxes = pred_boxes.view(-1, 4)
    pred_box = (pred_boxes.mean(dim=0) * self.params.search_size / resize_factor).tolist()
    self.state = clip_box(self.map_box_back(pred_box, resize_factor), H, W, margin=10)
    if self.debug:
        if not self.use_visdom:
            x1, y1, w, h = self.state
            image_BGR = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            cv2.rectangle(image_BGR, (int(x1), int(y1)), (int(x1 + w), int(y1 + h)), color=(0, 0, 255), thickness=2)
            save_path = os.path.join(self.save_dir, '%04d.jpg' % self.frame_id)
            cv2.imwrite(save_path, image_BGR)
        else:
            self.visdom.register((image, info['gt_bbox'].tolist(), self.state), 'Tracking', 1, 'Tracking')
            self.visdom.register(torch.from_numpy(x_patch_arr).permute(2, 0, 1), 'image', 1, 'search_region')
            self.visdom.register(torch.from_numpy(self.z_patch_arr).permute(2, 0, 1), 'image', 1, 'template')
            self.visdom.register(pred_score_map.view(self.feat_sz, self.feat_sz), 'heatmap', 1, 'score_map')
            self.visdom.register((pred_score_map * self.output_window).view(self.feat_sz, self.feat_sz), 'heatmap', 1, 'score_map_hann')
            if 'removed_indexes_s' in out_dict and out_dict['removed_indexes_s']:
                removed_indexes_s = out_dict['removed_indexes_s']
                removed_indexes_s = [removed_indexes_s_i.cpu().numpy() for removed_indexes_s_i in removed_indexes_s]
                masked_search = gen_visualization(x_patch_arr, removed_indexes_s)
                self.visdom.register(torch.from_numpy(masked_search).permute(2, 0, 1), 'image', 1, 'masked_search')
            while self.pause_mode:
                if self.step:
                    self.step = False
                    break
    if self.save_all_boxes:
        'save all predictions'
        all_boxes = self.map_box_back_batch(pred_boxes * self.params.search_size / resize_factor, resize_factor)
        all_boxes_save = all_boxes.view(-1).tolist()
        return {'target_bbox': self.state, 'all_boxes': all_boxes_save}
    else:
        return {'target_bbox': self.state}

def _edict2dict(dest_dict, src_edict):
    if isinstance(dest_dict, dict) and isinstance(src_edict, dict):
        for k, v in src_edict.items():
            if not isinstance(v, edict):
                dest_dict[k] = v
            else:
                dest_dict[k] = {}
                _edict2dict(dest_dict[k], v)
    else:
        return

def _update_config(base_cfg, exp_cfg):
    if isinstance(base_cfg, dict) and isinstance(exp_cfg, edict):
        for k, v in exp_cfg.items():
            if k in base_cfg:
                if not isinstance(v, dict):
                    base_cfg[k] = v
                else:
                    _update_config(base_cfg[k], v)
            else:
                raise ValueError('{} not exist in config.py'.format(k))
    else:
        return

def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

class DataModuleFromConfig(pl.LightningDataModule):

    def __init__(self, batch_size, train=None, validation=None, test=None, predict=None, wrap=False, num_workers=None, shuffle_test_loader=False, use_worker_init_fn=False, shuffle_val_dataloader=False):
        super().__init__()
        self.batch_size = batch_size
        self.dataset_configs = dict()
        self.num_workers = num_workers if num_workers is not None else batch_size * 2
        self.use_worker_init_fn = use_worker_init_fn
        if train is not None:
            self.dataset_configs['train'] = train
            self.train_dataloader = self._train_dataloader
        if validation is not None:
            self.dataset_configs['validation'] = validation
            self.val_dataloader = partial(self._val_dataloader, shuffle=shuffle_val_dataloader)
        if test is not None:
            self.dataset_configs['test'] = test
            self.test_dataloader = partial(self._test_dataloader, shuffle=shuffle_test_loader)
        if predict is not None:
            self.dataset_configs['predict'] = predict
            self.predict_dataloader = self._predict_dataloader
        self.wrap = wrap

    def prepare_data(self):
        for data_cfg in self.dataset_configs.values():
            instantiate_from_config(data_cfg)

    def setup(self, stage=None):
        self.datasets = dict(((k, instantiate_from_config(self.dataset_configs[k])) for k in self.dataset_configs))
        if self.wrap:
            for k in self.datasets:
                self.datasets[k] = WrappedDataset(self.datasets[k])

    def _train_dataloader(self):
        is_iterable_dataset = isinstance(self.datasets['train'], Txt2ImgIterableBaseDataset)
        if is_iterable_dataset or self.use_worker_init_fn:
            init_fn = worker_init_fn
        else:
            init_fn = None
        return DataLoader(self.datasets['train'], batch_size=self.batch_size, num_workers=self.num_workers, shuffle=False if is_iterable_dataset else True, worker_init_fn=init_fn)

    def _val_dataloader(self, shuffle=False):
        if isinstance(self.datasets['validation'], Txt2ImgIterableBaseDataset) or self.use_worker_init_fn:
            init_fn = worker_init_fn
        else:
            init_fn = None
        return DataLoader(self.datasets['validation'], batch_size=self.batch_size, num_workers=self.num_workers, worker_init_fn=init_fn, shuffle=shuffle)

    def _test_dataloader(self, shuffle=False):
        is_iterable_dataset = isinstance(self.datasets['train'], Txt2ImgIterableBaseDataset)
        if is_iterable_dataset or self.use_worker_init_fn:
            init_fn = worker_init_fn
        else:
            init_fn = None
        shuffle = shuffle and (not is_iterable_dataset)
        return DataLoader(self.datasets['test'], batch_size=self.batch_size, num_workers=self.num_workers, worker_init_fn=init_fn, shuffle=shuffle)

    def _predict_dataloader(self, shuffle=False):
        if isinstance(self.datasets['predict'], Txt2ImgIterableBaseDataset) or self.use_worker_init_fn:
            init_fn = worker_init_fn
        else:
            init_fn = None
        return DataLoader(self.datasets['predict'], batch_size=self.batch_size, num_workers=self.num_workers, worker_init_fn=init_fn)

def _train_dataloader(self):
    is_iterable_dataset = isinstance(self.datasets['train'], Txt2ImgIterableBaseDataset)
    if is_iterable_dataset or self.use_worker_init_fn:
        init_fn = worker_init_fn
    else:
        init_fn = None
    return DataLoader(self.datasets['train'], batch_size=self.batch_size, num_workers=self.num_workers, shuffle=False if is_iterable_dataset else True, worker_init_fn=init_fn)

def _val_dataloader(self, shuffle=False):
    if isinstance(self.datasets['validation'], Txt2ImgIterableBaseDataset) or self.use_worker_init_fn:
        init_fn = worker_init_fn
    else:
        init_fn = None
    return DataLoader(self.datasets['validation'], batch_size=self.batch_size, num_workers=self.num_workers, worker_init_fn=init_fn, shuffle=shuffle)

def _test_dataloader(self, shuffle=False):
    is_iterable_dataset = isinstance(self.datasets['train'], Txt2ImgIterableBaseDataset)
    if is_iterable_dataset or self.use_worker_init_fn:
        init_fn = worker_init_fn
    else:
        init_fn = None
    shuffle = shuffle and (not is_iterable_dataset)
    return DataLoader(self.datasets['test'], batch_size=self.batch_size, num_workers=self.num_workers, worker_init_fn=init_fn, shuffle=shuffle)

def _predict_dataloader(self, shuffle=False):
    if isinstance(self.datasets['predict'], Txt2ImgIterableBaseDataset) or self.use_worker_init_fn:
        init_fn = worker_init_fn
    else:
        init_fn = None
    return DataLoader(self.datasets['predict'], batch_size=self.batch_size, num_workers=self.num_workers, worker_init_fn=init_fn)

class ImageLogger(Callback):

    def __init__(self, batch_frequency, max_images, clamp=True, increase_log_steps=True, rescale=True, disabled=False, log_on_batch_idx=False, log_first_step=False, log_images_kwargs=None):
        super().__init__()
        self.rescale = rescale
        self.batch_freq = batch_frequency
        self.max_images = max_images
        self.logger_log_images = {pl.loggers.TestTubeLogger: self._testtube}
        self.log_steps = [2 ** n for n in range(int(np.log2(self.batch_freq)) + 1)]
        if not increase_log_steps:
            self.log_steps = [self.batch_freq]
        self.clamp = clamp
        self.disabled = disabled
        self.log_on_batch_idx = log_on_batch_idx
        self.log_images_kwargs = log_images_kwargs if log_images_kwargs else {}
        self.log_first_step = log_first_step

    @rank_zero_only
    def _testtube(self, pl_module, images, batch_idx, split):
        for k in images:
            grid = torchvision.utils.make_grid(images[k])
            grid = (grid + 1.0) / 2.0
            tag = f'{split}/{k}'
            pl_module.logger.experiment.add_image(tag, grid, global_step=pl_module.global_step)

    @rank_zero_only
    def log_local(self, save_dir, split, images, global_step, current_epoch, batch_idx):
        root = os.path.join(save_dir, 'images', split)
        for k in images:
            grid = torchvision.utils.make_grid(images[k], nrow=4)
            if self.rescale:
                grid = (grid + 1.0) / 2.0
            grid = grid.transpose(0, 1).transpose(1, 2).squeeze(-1)
            grid = grid.numpy()
            grid = (grid * 255).astype(np.uint8)
            filename = '{}_gs-{:06}_e-{:06}_b-{:06}.png'.format(k, global_step, current_epoch, batch_idx)
            path = os.path.join(root, filename)
            os.makedirs(os.path.split(path)[0], exist_ok=True)
            Image.fromarray(grid).save(path)

    def log_img(self, pl_module, batch, batch_idx, split='train'):
        check_idx = batch_idx if self.log_on_batch_idx else pl_module.global_step
        if self.check_frequency(check_idx) and hasattr(pl_module, 'log_images') and callable(pl_module.log_images) and (self.max_images > 0):
            logger = type(pl_module.logger)
            is_train = pl_module.training
            if is_train:
                pl_module.eval()
            with torch.no_grad():
                images = pl_module.log_images(batch, split=split, **self.log_images_kwargs)
            for k in images:
                N = min(images[k].shape[0], self.max_images)
                images[k] = images[k][:N]
                if isinstance(images[k], torch.Tensor):
                    images[k] = images[k].detach().cpu()
                    if self.clamp:
                        images[k] = torch.clamp(images[k], -1.0, 1.0)
            self.log_local(pl_module.logger.save_dir, split, images, pl_module.global_step, pl_module.current_epoch, batch_idx)
            logger_log_images = self.logger_log_images.get(logger, lambda *args, **kwargs: None)
            logger_log_images(pl_module, images, pl_module.global_step, split)
            if is_train:
                pl_module.train()

    def check_frequency(self, check_idx):
        if (check_idx % self.batch_freq == 0 or check_idx in self.log_steps) and (check_idx > 0 or self.log_first_step):
            try:
                self.log_steps.pop(0)
            except IndexError as e:
                print(e)
                pass
            return True
        return False

    def on_train_batch_end(self, trainer, pl_module, outputs, batch, batch_idx, dataloader_idx):
        if not self.disabled and (pl_module.global_step > 0 or self.log_first_step):
            self.log_img(pl_module, batch, batch_idx, split='train')

    def on_validation_batch_end(self, trainer, pl_module, outputs, batch, batch_idx, dataloader_idx):
        if not self.disabled and pl_module.global_step > 0:
            self.log_img(pl_module, batch, batch_idx, split='val')
        if hasattr(pl_module, 'calibrate_grad_norm'):
            if (pl_module.calibrate_grad_norm and batch_idx % 25 == 0) and batch_idx > 0:
                self.log_gradients(trainer, pl_module, batch_idx=batch_idx)

def log_img(self, pl_module, batch, batch_idx, split='train'):
    check_idx = batch_idx if self.log_on_batch_idx else pl_module.global_step
    if self.check_frequency(check_idx) and hasattr(pl_module, 'log_images') and callable(pl_module.log_images) and (self.max_images > 0):
        logger = type(pl_module.logger)
        is_train = pl_module.training
        if is_train:
            pl_module.eval()
        with torch.no_grad():
            images = pl_module.log_images(batch, split=split, **self.log_images_kwargs)
        for k in images:
            N = min(images[k].shape[0], self.max_images)
            images[k] = images[k][:N]
            if isinstance(images[k], torch.Tensor):
                images[k] = images[k].detach().cpu()
                if self.clamp:
                    images[k] = torch.clamp(images[k], -1.0, 1.0)
        self.log_local(pl_module.logger.save_dir, split, images, pl_module.global_step, pl_module.current_epoch, batch_idx)
        logger_log_images = self.logger_log_images.get(logger, lambda *args, **kwargs: None)
        logger_log_images(pl_module, images, pl_module.global_step, split)
        if is_train:
            pl_module.train()

def custom_to_pil(x):
    x = x.detach().cpu()
    x = torch.clamp(x, -1.0, 1.0)
    x = (x + 1.0) / 2.0
    x = x.permute(1, 2, 0).numpy()
    x = (255 * x).astype(np.uint8)
    x = Image.fromarray(x)
    if not x.mode == 'RGB':
        x = x.convert('RGB')
    return x

def custom_to_np(x):
    sample = x.detach().cpu()
    sample = ((sample + 1) * 127.5).clamp(0, 255).to(torch.uint8)
    sample = sample.permute(0, 2, 3, 1)
    sample = sample.contiguous()
    return sample

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

def ismap(x):
    if not isinstance(x, torch.Tensor):
        return False
    return len(x.shape) == 4 and x.shape[1] > 3

def isimage(x):
    if not isinstance(x, torch.Tensor):
        return False
    return len(x.shape) == 4 and (x.shape[1] == 3 or x.shape[1] == 1)

def count_params(model, verbose=False):
    total_params = sum((p.numel() for p in model.parameters()))
    if verbose:
        print(f'{model.__class__.__name__} has {total_params * 1e-06:.2f} M params.')
    return total_params

def parallel_data_prefetch(func: callable, data, n_proc, target_data_type='ndarray', cpu_intensive=True, use_worker_id=False):
    if isinstance(data, np.ndarray) and target_data_type == 'list':
        raise ValueError('list expected but function got ndarray.')
    elif isinstance(data, abc.Iterable):
        if isinstance(data, dict):
            print(f'WARNING:"data" argument passed to parallel_data_prefetch is a dict: Using only its values and disregarding keys.')
            data = list(data.values())
        if target_data_type == 'ndarray':
            data = np.asarray(data)
        else:
            data = list(data)
    else:
        raise TypeError(f'The data, that shall be processed parallel has to be either an np.ndarray or an Iterable, but is actually {type(data)}.')
    if cpu_intensive:
        Q = mp.Queue(1000)
        proc = mp.Process
    else:
        Q = Queue(1000)
        proc = Thread
    if target_data_type == 'ndarray':
        arguments = [[func, Q, part, i, use_worker_id] for i, part in enumerate(np.array_split(data, n_proc))]
    else:
        step = int(len(data) / n_proc + 1) if len(data) % n_proc != 0 else int(len(data) / n_proc)
        arguments = [[func, Q, part, i, use_worker_id] for i, part in enumerate([data[i:i + step] for i in range(0, len(data), step)])]
    processes = []
    for i in range(n_proc):
        p = proc(target=_do_parallel_data_prefetch, args=arguments[i])
        processes += [p]
    print(f'Start prefetching...')
    import time
    start = time.time()
    gather_res = [[] for _ in range(n_proc)]
    try:
        for p in processes:
            p.start()
        k = 0
        while k < n_proc:
            res = Q.get()
            if res == 'Done':
                k += 1
            else:
                gather_res[res[0]] = res[1]
    except Exception as e:
        print('Exception: ', e)
        for p in processes:
            p.terminate()
        raise e
    finally:
        for p in processes:
            p.join()
        print(f'Prefetching complete. [{time.time() - start} sec.]')
    if target_data_type == 'ndarray':
        if not isinstance(gather_res[0], np.ndarray):
            return np.concatenate([np.asarray(r) for r in gather_res], axis=0)
        return np.concatenate(gather_res, axis=0)
    elif target_data_type == 'list':
        out = []
        for r in gather_res:
            out.extend(r)
        return out
    else:
        return gather_res

def l2(x, y):
    return torch.pow(x - y, 2)

def blur(x, k):
    """
    x: image, NxcxHxW
    k: kernel, Nx1xhxw
    """
    n, c = x.shape[:2]
    p1, p2 = ((k.shape[-2] - 1) // 2, (k.shape[-1] - 1) // 2)
    x = torch.nn.functional.pad(x, pad=(p1, p2, p1, p2), mode='replicate')
    k = k.repeat(1, c, 1, 1)
    k = k.view(-1, 1, k.shape[2], k.shape[3])
    x = x.view(1, -1, x.shape[2], x.shape[3])
    x = torch.nn.functional.conv2d(x, k, bias=None, stride=1, padding=0, groups=n * c)
    x = x.view(n, c, x.shape[2], x.shape[3])
    return x

def mkdirs(paths):
    if isinstance(paths, str):
        mkdir(paths)
    else:
        for path in paths:
            mkdir(path)

def tensor2uint(img):
    img = img.data.squeeze().float().clamp_(0, 1).cpu().numpy()
    if img.ndim == 3:
        img = np.transpose(img, (1, 2, 0))
    return np.uint8((img * 255.0).round())

def tensor2single(img):
    img = img.data.squeeze().float().cpu().numpy()
    if img.ndim == 3:
        img = np.transpose(img, (1, 2, 0))
    return img

def tensor2single3(img):
    img = img.data.squeeze().float().cpu().numpy()
    if img.ndim == 3:
        img = np.transpose(img, (1, 2, 0))
    elif img.ndim == 2:
        img = np.expand_dims(img, axis=2)
    return img

def tensor2img(tensor, out_type=np.uint8, min_max=(0, 1)):
    """
    Converts a torch Tensor into an image Numpy array of BGR channel order
    Input: 4D(B,(3/1),H,W), 3D(C,H,W), or 2D(H,W), any range, RGB channel order
    Output: 3D(H,W,C) or 2D(H,W), [0,255], np.uint8 (default)
    """
    tensor = tensor.squeeze().float().cpu().clamp_(*min_max)
    tensor = (tensor - min_max[0]) / (min_max[1] - min_max[0])
    n_dim = tensor.dim()
    if n_dim == 4:
        n_img = len(tensor)
        img_np = make_grid(tensor, nrow=int(math.sqrt(n_img)), normalize=False).numpy()
        img_np = np.transpose(img_np[[2, 1, 0], :, :], (1, 2, 0))
    elif n_dim == 3:
        img_np = tensor.numpy()
        img_np = np.transpose(img_np[[2, 1, 0], :, :], (1, 2, 0))
    elif n_dim == 2:
        img_np = tensor.numpy()
    else:
        raise TypeError('Only support 4D, 3D and 2D tensor. But received with dimension: {:d}'.format(n_dim))
    if out_type == np.uint8:
        img_np = (img_np * 255.0).round()
    return img_np.astype(out_type)

def calculate_psnr(img1, img2, border=0):
    if not img1.shape == img2.shape:
        raise ValueError('Input images must have the same dimensions.')
    h, w = img1.shape[:2]
    img1 = img1[border:h - border, border:w - border]
    img2 = img2[border:h - border, border:w - border]
    img1 = img1.astype(np.float64)
    img2 = img2.astype(np.float64)
    mse = np.mean((img1 - img2) ** 2)
    if mse == 0:
        return float('inf')
    return 20 * math.log10(255.0 / math.sqrt(mse))

class UNetModel(nn.Module):
    """
    The full UNet model with attention and timestep embedding.
    :param in_channels: channels in the input Tensor.
    :param model_channels: base channel count for the model.
    :param out_channels: channels in the output Tensor.
    :param num_res_blocks: number of residual blocks per downsample.
    :param attention_resolutions: a collection of downsample rates at which
        attention will take place. May be a set, list, or tuple.
        For example, if this contains 4, then at 4x downsampling, attention
        will be used.
    :param dropout: the dropout probability.
    :param channel_mult: channel multiplier for each level of the UNet.
    :param conv_resample: if True, use learned convolutions for upsampling and
        downsampling.
    :param dims: determines if the signal is 1D, 2D, or 3D.
    :param num_classes: if specified (as an int), then this model will be
        class-conditional with `num_classes` classes.
    :param use_checkpoint: use gradient checkpointing to reduce memory usage.
    :param num_heads: the number of attention heads in each attention layer.
    :param num_heads_channels: if specified, ignore num_heads and instead use
                               a fixed channel width per attention head.
    :param num_heads_upsample: works with num_heads to set a different number
                               of heads for upsampling. Deprecated.
    :param use_scale_shift_norm: use a FiLM-like conditioning mechanism.
    :param resblock_updown: use residual blocks for up/downsampling.
    :param use_new_attention_order: use a different attention pattern for potentially
                                    increased efficiency.
    """

    def __init__(self, image_size, in_channels, model_channels, out_channels, num_res_blocks, attention_resolutions, dropout=0, channel_mult=(1, 2, 4, 8), conv_resample=True, dims=2, num_classes=None, use_checkpoint=False, use_fp16=False, num_heads=-1, num_head_channels=-1, num_heads_upsample=-1, use_scale_shift_norm=False, resblock_updown=False, use_new_attention_order=False, use_spatial_transformer=False, transformer_depth=1, context_dim=None, n_embed=None, legacy=True):
        super().__init__()
        if use_spatial_transformer:
            assert context_dim is not None, 'Fool!! You forgot to include the dimension of your cross-attention conditioning...'
        if context_dim is not None:
            assert use_spatial_transformer, 'Fool!! You forgot to use the spatial transformer for your cross-attention conditioning...'
            from omegaconf.listconfig import ListConfig
            if type(context_dim) == ListConfig:
                context_dim = list(context_dim)
        if num_heads_upsample == -1:
            num_heads_upsample = num_heads
        if num_heads == -1:
            assert num_head_channels != -1, 'Either num_heads or num_head_channels has to be set'
        if num_head_channels == -1:
            assert num_heads != -1, 'Either num_heads or num_head_channels has to be set'
        self.image_size = image_size
        self.in_channels = in_channels
        self.model_channels = model_channels
        self.out_channels = out_channels
        self.num_res_blocks = num_res_blocks
        self.attention_resolutions = attention_resolutions
        self.dropout = dropout
        self.channel_mult = channel_mult
        self.conv_resample = conv_resample
        self.num_classes = num_classes
        self.use_checkpoint = use_checkpoint
        self.dtype = th.float16 if use_fp16 else th.float32
        self.num_heads = num_heads
        self.num_head_channels = num_head_channels
        self.num_heads_upsample = num_heads_upsample
        self.predict_codebook_ids = n_embed is not None
        time_embed_dim = model_channels * 4
        self.time_embed = nn.Sequential(linear(model_channels, time_embed_dim), nn.SiLU(), linear(time_embed_dim, time_embed_dim))
        if self.num_classes is not None:
            self.label_emb = nn.Embedding(num_classes, time_embed_dim)
        self.input_blocks = nn.ModuleList([TimestepEmbedSequential(conv_nd(dims, in_channels, model_channels, 3, padding=1))])
        self._feature_size = model_channels
        input_block_chans = [model_channels]
        ch = model_channels
        ds = 1
        for level, mult in enumerate(channel_mult):
            for _ in range(num_res_blocks):
                layers = [ResBlock(ch, time_embed_dim, dropout, out_channels=mult * model_channels, dims=dims, use_checkpoint=use_checkpoint, use_scale_shift_norm=use_scale_shift_norm)]
                ch = mult * model_channels
                if ds in attention_resolutions:
                    if num_head_channels == -1:
                        dim_head = ch // num_heads
                    else:
                        num_heads = ch // num_head_channels
                        dim_head = num_head_channels
                    if legacy:
                        dim_head = ch // num_heads if use_spatial_transformer else num_head_channels
                    layers.append(AttentionBlock(ch, use_checkpoint=use_checkpoint, num_heads=num_heads, num_head_channels=dim_head, use_new_attention_order=use_new_attention_order) if not use_spatial_transformer else SpatialTransformer(ch, num_heads, dim_head, depth=transformer_depth, context_dim=context_dim))
                self.input_blocks.append(TimestepEmbedSequential(*layers))
                self._feature_size += ch
                input_block_chans.append(ch)
            if level != len(channel_mult) - 1:
                out_ch = ch
                self.input_blocks.append(TimestepEmbedSequential(ResBlock(ch, time_embed_dim, dropout, out_channels=out_ch, dims=dims, use_checkpoint=use_checkpoint, use_scale_shift_norm=use_scale_shift_norm, down=True) if resblock_updown else Downsample(ch, conv_resample, dims=dims, out_channels=out_ch)))
                ch = out_ch
                input_block_chans.append(ch)
                ds *= 2
                self._feature_size += ch
        if num_head_channels == -1:
            dim_head = ch // num_heads
        else:
            num_heads = ch // num_head_channels
            dim_head = num_head_channels
        if legacy:
            dim_head = ch // num_heads if use_spatial_transformer else num_head_channels
        self.middle_block = TimestepEmbedSequential(ResBlock(ch, time_embed_dim, dropout, dims=dims, use_checkpoint=use_checkpoint, use_scale_shift_norm=use_scale_shift_norm), AttentionBlock(ch, use_checkpoint=use_checkpoint, num_heads=num_heads, num_head_channels=dim_head, use_new_attention_order=use_new_attention_order) if not use_spatial_transformer else SpatialTransformer(ch, num_heads, dim_head, depth=transformer_depth, context_dim=context_dim), ResBlock(ch, time_embed_dim, dropout, dims=dims, use_checkpoint=use_checkpoint, use_scale_shift_norm=use_scale_shift_norm))
        self._feature_size += ch
        self.output_blocks = nn.ModuleList([])
        for level, mult in list(enumerate(channel_mult))[::-1]:
            for i in range(num_res_blocks + 1):
                ich = input_block_chans.pop()
                layers = [ResBlock(ch + ich, time_embed_dim, dropout, out_channels=model_channels * mult, dims=dims, use_checkpoint=use_checkpoint, use_scale_shift_norm=use_scale_shift_norm)]
                ch = model_channels * mult
                if ds in attention_resolutions:
                    if num_head_channels == -1:
                        dim_head = ch // num_heads
                    else:
                        num_heads = ch // num_head_channels
                        dim_head = num_head_channels
                    if legacy:
                        dim_head = ch // num_heads if use_spatial_transformer else num_head_channels
                    layers.append(AttentionBlock(ch, use_checkpoint=use_checkpoint, num_heads=num_heads_upsample, num_head_channels=dim_head, use_new_attention_order=use_new_attention_order) if not use_spatial_transformer else SpatialTransformer(ch, num_heads, dim_head, depth=transformer_depth, context_dim=context_dim))
                if level and i == num_res_blocks:
                    out_ch = ch
                    layers.append(ResBlock(ch, time_embed_dim, dropout, out_channels=out_ch, dims=dims, use_checkpoint=use_checkpoint, use_scale_shift_norm=use_scale_shift_norm, up=True) if resblock_updown else Upsample(ch, conv_resample, dims=dims, out_channels=out_ch))
                    ds //= 2
                self.output_blocks.append(TimestepEmbedSequential(*layers))
                self._feature_size += ch
        self.out = nn.Sequential(normalization(ch), nn.SiLU(), zero_module(conv_nd(dims, model_channels, out_channels, 3, padding=1)))
        if self.predict_codebook_ids:
            self.id_predictor = nn.Sequential(normalization(ch), conv_nd(dims, model_channels, n_embed, 1))

    def convert_to_fp16(self):
        """
        Convert the torso of the model to float16.
        """
        self.input_blocks.apply(convert_module_to_f16)
        self.middle_block.apply(convert_module_to_f16)
        self.output_blocks.apply(convert_module_to_f16)

    def convert_to_fp32(self):
        """
        Convert the torso of the model to float32.
        """
        self.input_blocks.apply(convert_module_to_f32)
        self.middle_block.apply(convert_module_to_f32)
        self.output_blocks.apply(convert_module_to_f32)

    def forward(self, x, timesteps=None, context=None, y=None, **kwargs):
        """
        Apply the model to an input batch.
        :param x: an [N x C x ...] Tensor of inputs.
        :param timesteps: a 1-D batch of timesteps.
        :param context: conditioning plugged in via crossattn
        :param y: an [N] Tensor of labels, if class-conditional.
        :return: an [N x C x ...] Tensor of outputs.
        """
        assert (y is not None) == (self.num_classes is not None), 'must specify y if and only if the model is class-conditional'
        hs = []
        t_emb = timestep_embedding(timesteps, self.model_channels, repeat_only=False)
        emb = self.time_embed(t_emb)
        if self.num_classes is not None:
            assert y.shape == (x.shape[0],)
            emb = emb + self.label_emb(y)
        h = x.type(self.dtype)
        for module in self.input_blocks:
            h = module(h, emb, context)
            hs.append(h)
        h = self.middle_block(h, emb, context)
        for module in self.output_blocks:
            h = th.cat([h, hs.pop()], dim=1)
            h = module(h, emb, context)
        h = h.type(x.dtype)
        if self.predict_codebook_ids:
            return self.id_predictor(h)
        else:
            return self.out(h)

def forward(self, x, timesteps=None, context=None, y=None, **kwargs):
    """
        Apply the model to an input batch.
        :param x: an [N x C x ...] Tensor of inputs.
        :param timesteps: a 1-D batch of timesteps.
        :param context: conditioning plugged in via crossattn
        :param y: an [N] Tensor of labels, if class-conditional.
        :return: an [N x C x ...] Tensor of outputs.
        """
    assert (y is not None) == (self.num_classes is not None), 'must specify y if and only if the model is class-conditional'
    hs = []
    t_emb = timestep_embedding(timesteps, self.model_channels, repeat_only=False)
    emb = self.time_embed(t_emb)
    if self.num_classes is not None:
        assert y.shape == (x.shape[0],)
        emb = emb + self.label_emb(y)
    h = x.type(self.dtype)
    for module in self.input_blocks:
        h = module(h, emb, context)
        hs.append(h)
    h = self.middle_block(h, emb, context)
    for module in self.output_blocks:
        h = th.cat([h, hs.pop()], dim=1)
        h = module(h, emb, context)
    h = h.type(x.dtype)
    if self.predict_codebook_ids:
        return self.id_predictor(h)
    else:
        return self.out(h)

class EncoderUNetModel(nn.Module):
    """
    The half UNet model with attention and timestep embedding.
    For usage, see UNet.
    """

    def __init__(self, image_size, in_channels, model_channels, out_channels, num_res_blocks, attention_resolutions, dropout=0, channel_mult=(1, 2, 4, 8), conv_resample=True, dims=2, use_checkpoint=False, use_fp16=False, num_heads=1, num_head_channels=-1, num_heads_upsample=-1, use_scale_shift_norm=False, resblock_updown=False, use_new_attention_order=False, pool='adaptive', *args, **kwargs):
        super().__init__()
        if num_heads_upsample == -1:
            num_heads_upsample = num_heads
        self.in_channels = in_channels
        self.model_channels = model_channels
        self.out_channels = out_channels
        self.num_res_blocks = num_res_blocks
        self.attention_resolutions = attention_resolutions
        self.dropout = dropout
        self.channel_mult = channel_mult
        self.conv_resample = conv_resample
        self.use_checkpoint = use_checkpoint
        self.dtype = th.float16 if use_fp16 else th.float32
        self.num_heads = num_heads
        self.num_head_channels = num_head_channels
        self.num_heads_upsample = num_heads_upsample
        time_embed_dim = model_channels * 4
        self.time_embed = nn.Sequential(linear(model_channels, time_embed_dim), nn.SiLU(), linear(time_embed_dim, time_embed_dim))
        self.input_blocks = nn.ModuleList([TimestepEmbedSequential(conv_nd(dims, in_channels, model_channels, 3, padding=1))])
        self._feature_size = model_channels
        input_block_chans = [model_channels]
        ch = model_channels
        ds = 1
        for level, mult in enumerate(channel_mult):
            for _ in range(num_res_blocks):
                layers = [ResBlock(ch, time_embed_dim, dropout, out_channels=mult * model_channels, dims=dims, use_checkpoint=use_checkpoint, use_scale_shift_norm=use_scale_shift_norm)]
                ch = mult * model_channels
                if ds in attention_resolutions:
                    layers.append(AttentionBlock(ch, use_checkpoint=use_checkpoint, num_heads=num_heads, num_head_channels=num_head_channels, use_new_attention_order=use_new_attention_order))
                self.input_blocks.append(TimestepEmbedSequential(*layers))
                self._feature_size += ch
                input_block_chans.append(ch)
            if level != len(channel_mult) - 1:
                out_ch = ch
                self.input_blocks.append(TimestepEmbedSequential(ResBlock(ch, time_embed_dim, dropout, out_channels=out_ch, dims=dims, use_checkpoint=use_checkpoint, use_scale_shift_norm=use_scale_shift_norm, down=True) if resblock_updown else Downsample(ch, conv_resample, dims=dims, out_channels=out_ch)))
                ch = out_ch
                input_block_chans.append(ch)
                ds *= 2
                self._feature_size += ch
        self.middle_block = TimestepEmbedSequential(ResBlock(ch, time_embed_dim, dropout, dims=dims, use_checkpoint=use_checkpoint, use_scale_shift_norm=use_scale_shift_norm), AttentionBlock(ch, use_checkpoint=use_checkpoint, num_heads=num_heads, num_head_channels=num_head_channels, use_new_attention_order=use_new_attention_order), ResBlock(ch, time_embed_dim, dropout, dims=dims, use_checkpoint=use_checkpoint, use_scale_shift_norm=use_scale_shift_norm))
        self._feature_size += ch
        self.pool = pool
        if pool == 'adaptive':
            self.out = nn.Sequential(normalization(ch), nn.SiLU(), nn.AdaptiveAvgPool2d((1, 1)), zero_module(conv_nd(dims, ch, out_channels, 1)), nn.Flatten())
        elif pool == 'attention':
            assert num_head_channels != -1
            self.out = nn.Sequential(normalization(ch), nn.SiLU(), AttentionPool2d(image_size // ds, ch, num_head_channels, out_channels))
        elif pool == 'spatial':
            self.out = nn.Sequential(nn.Linear(self._feature_size, 2048), nn.ReLU(), nn.Linear(2048, self.out_channels))
        elif pool == 'spatial_v2':
            self.out = nn.Sequential(nn.Linear(self._feature_size, 2048), normalization(2048), nn.SiLU(), nn.Linear(2048, self.out_channels))
        else:
            raise NotImplementedError(f'Unexpected {pool} pooling')

    def convert_to_fp16(self):
        """
        Convert the torso of the model to float16.
        """
        self.input_blocks.apply(convert_module_to_f16)
        self.middle_block.apply(convert_module_to_f16)

    def convert_to_fp32(self):
        """
        Convert the torso of the model to float32.
        """
        self.input_blocks.apply(convert_module_to_f32)
        self.middle_block.apply(convert_module_to_f32)

    def forward(self, x, timesteps):
        """
        Apply the model to an input batch.
        :param x: an [N x C x ...] Tensor of inputs.
        :param timesteps: a 1-D batch of timesteps.
        :return: an [N x K] Tensor of outputs.
        """
        emb = self.time_embed(timestep_embedding(timesteps, self.model_channels))
        results = []
        h = x.type(self.dtype)
        for module in self.input_blocks:
            h = module(h, emb)
            if self.pool.startswith('spatial'):
                results.append(h.type(x.dtype).mean(dim=(2, 3)))
        h = self.middle_block(h, emb)
        if self.pool.startswith('spatial'):
            results.append(h.type(x.dtype).mean(dim=(2, 3)))
            h = th.cat(results, axis=-1)
            return self.out(h)
        else:
            h = h.type(x.dtype)
            return self.out(h)

def forward(self, x, timesteps):
    """
        Apply the model to an input batch.
        :param x: an [N x C x ...] Tensor of inputs.
        :param timesteps: a 1-D batch of timesteps.
        :return: an [N x K] Tensor of outputs.
        """
    emb = self.time_embed(timestep_embedding(timesteps, self.model_channels))
    results = []
    h = x.type(self.dtype)
    for module in self.input_blocks:
        h = module(h, emb)
        if self.pool.startswith('spatial'):
            results.append(h.type(x.dtype).mean(dim=(2, 3)))
    h = self.middle_block(h, emb)
    if self.pool.startswith('spatial'):
        results.append(h.type(x.dtype).mean(dim=(2, 3)))
        h = th.cat(results, axis=-1)
        return self.out(h)
    else:
        h = h.type(x.dtype)
        return self.out(h)

def make_beta_schedule(schedule, n_timestep, linear_start=0.0001, linear_end=0.02, cosine_s=0.008):
    if schedule == 'linear':
        betas = torch.linspace(linear_start ** 0.5, linear_end ** 0.5, n_timestep, dtype=torch.float64) ** 2
    elif schedule == 'cosine':
        timesteps = torch.arange(n_timestep + 1, dtype=torch.float64) / n_timestep + cosine_s
        alphas = timesteps / (1 + cosine_s) * np.pi / 2
        alphas = torch.cos(alphas).pow(2)
        alphas = alphas / alphas[0]
        betas = 1 - alphas[1:] / alphas[:-1]
        betas = np.clip(betas, a_min=0, a_max=0.999)
    elif schedule == 'sqrt_linear':
        betas = torch.linspace(linear_start, linear_end, n_timestep, dtype=torch.float64)
    elif schedule == 'sqrt':
        betas = torch.linspace(linear_start, linear_end, n_timestep, dtype=torch.float64) ** 0.5
    else:
        raise ValueError(f"schedule '{schedule}' unknown.")
    return betas.numpy()

class DDIMSampler(object):

    def __init__(self, model, schedule='linear', **kwargs):
        super().__init__()
        self.model = model
        self.ddpm_num_timesteps = model.num_timesteps
        self.schedule = schedule

    def register_buffer(self, name, attr):
        if type(attr) == torch.Tensor:
            if attr.device != torch.device('cuda'):
                attr = attr.to(torch.device('cuda'))
        setattr(self, name, attr)

    def make_schedule(self, ddim_num_steps, ddim_discretize='uniform', ddim_eta=0.0, verbose=True):
        self.ddim_timesteps = make_ddim_timesteps(ddim_discr_method=ddim_discretize, num_ddim_timesteps=ddim_num_steps, num_ddpm_timesteps=self.ddpm_num_timesteps, verbose=verbose)
        alphas_cumprod = self.model.alphas_cumprod
        assert alphas_cumprod.shape[0] == self.ddpm_num_timesteps, 'alphas have to be defined for each timestep'
        to_torch = lambda x: x.clone().detach().to(torch.float32).to(self.model.device)
        self.register_buffer('betas', to_torch(self.model.betas))
        self.register_buffer('alphas_cumprod', to_torch(alphas_cumprod))
        self.register_buffer('alphas_cumprod_prev', to_torch(self.model.alphas_cumprod_prev))
        self.register_buffer('sqrt_alphas_cumprod', to_torch(np.sqrt(alphas_cumprod.cpu())))
        self.register_buffer('sqrt_one_minus_alphas_cumprod', to_torch(np.sqrt(1.0 - alphas_cumprod.cpu())))
        self.register_buffer('log_one_minus_alphas_cumprod', to_torch(np.log(1.0 - alphas_cumprod.cpu())))
        self.register_buffer('sqrt_recip_alphas_cumprod', to_torch(np.sqrt(1.0 / alphas_cumprod.cpu())))
        self.register_buffer('sqrt_recipm1_alphas_cumprod', to_torch(np.sqrt(1.0 / alphas_cumprod.cpu() - 1)))
        ddim_sigmas, ddim_alphas, ddim_alphas_prev = make_ddim_sampling_parameters(alphacums=alphas_cumprod.cpu(), ddim_timesteps=self.ddim_timesteps, eta=ddim_eta, verbose=verbose)
        self.register_buffer('ddim_sigmas', ddim_sigmas)
        self.register_buffer('ddim_alphas', ddim_alphas)
        self.register_buffer('ddim_alphas_prev', ddim_alphas_prev)
        self.register_buffer('ddim_sqrt_one_minus_alphas', np.sqrt(1.0 - ddim_alphas))
        sigmas_for_original_sampling_steps = ddim_eta * torch.sqrt((1 - self.alphas_cumprod_prev) / (1 - self.alphas_cumprod) * (1 - self.alphas_cumprod / self.alphas_cumprod_prev))
        self.register_buffer('ddim_sigmas_for_original_num_steps', sigmas_for_original_sampling_steps)

    @torch.no_grad()
    def sample(self, S, batch_size, shape, conditioning=None, callback=None, normals_sequence=None, img_callback=None, quantize_x0=False, eta=0.0, mask=None, x0=None, temperature=1.0, noise_dropout=0.0, score_corrector=None, corrector_kwargs=None, verbose=True, x_T=None, log_every_t=100, unconditional_guidance_scale=1.0, unconditional_conditioning=None, **kwargs):
        if conditioning is not None:
            if isinstance(conditioning, dict):
                cbs = conditioning[list(conditioning.keys())[0]].shape[0]
                if cbs != batch_size:
                    print(f'Warning: Got {cbs} conditionings but batch-size is {batch_size}')
            elif conditioning.shape[0] != batch_size:
                print(f'Warning: Got {conditioning.shape[0]} conditionings but batch-size is {batch_size}')
        self.make_schedule(ddim_num_steps=S, ddim_eta=eta, verbose=verbose)
        C, H, W = shape
        size = (batch_size, C, H, W)
        print(f'Data shape for DDIM sampling is {size}, eta {eta}')
        samples, intermediates = self.ddim_sampling(conditioning, size, callback=callback, img_callback=img_callback, quantize_denoised=quantize_x0, mask=mask, x0=x0, ddim_use_original_steps=False, noise_dropout=noise_dropout, temperature=temperature, score_corrector=score_corrector, corrector_kwargs=corrector_kwargs, x_T=x_T, log_every_t=log_every_t, unconditional_guidance_scale=unconditional_guidance_scale, unconditional_conditioning=unconditional_conditioning)
        return (samples, intermediates)

    @torch.no_grad()
    def ddim_sampling(self, cond, shape, x_T=None, ddim_use_original_steps=False, callback=None, timesteps=None, quantize_denoised=False, mask=None, x0=None, img_callback=None, log_every_t=100, temperature=1.0, noise_dropout=0.0, score_corrector=None, corrector_kwargs=None, unconditional_guidance_scale=1.0, unconditional_conditioning=None):
        device = self.model.betas.device
        b = shape[0]
        if x_T is None:
            img = torch.randn(shape, device=device)
        else:
            img = x_T
        if timesteps is None:
            timesteps = self.ddpm_num_timesteps if ddim_use_original_steps else self.ddim_timesteps
        elif timesteps is not None and (not ddim_use_original_steps):
            subset_end = int(min(timesteps / self.ddim_timesteps.shape[0], 1) * self.ddim_timesteps.shape[0]) - 1
            timesteps = self.ddim_timesteps[:subset_end]
        intermediates = {'x_inter': [img], 'pred_x0': [img]}
        time_range = reversed(range(0, timesteps)) if ddim_use_original_steps else np.flip(timesteps)
        total_steps = timesteps if ddim_use_original_steps else timesteps.shape[0]
        print(f'Running DDIM Sampling with {total_steps} timesteps')
        iterator = tqdm(time_range, desc='DDIM Sampler', total=total_steps)
        for i, step in enumerate(iterator):
            index = total_steps - i - 1
            ts = torch.full((b,), step, device=device, dtype=torch.long)
            if mask is not None:
                assert x0 is not None
                img_orig = self.model.q_sample(x0, ts)
                img = img_orig * mask + (1.0 - mask) * img
            outs = self.p_sample_ddim(img, cond, ts, index=index, use_original_steps=ddim_use_original_steps, quantize_denoised=quantize_denoised, temperature=temperature, noise_dropout=noise_dropout, score_corrector=score_corrector, corrector_kwargs=corrector_kwargs, unconditional_guidance_scale=unconditional_guidance_scale, unconditional_conditioning=unconditional_conditioning)
            img, pred_x0 = outs
            if callback:
                callback(i)
            if img_callback:
                img_callback(pred_x0, i)
            if index % log_every_t == 0 or index == total_steps - 1:
                intermediates['x_inter'].append(img)
                intermediates['pred_x0'].append(pred_x0)
        return (img, intermediates)

    @torch.no_grad()
    def p_sample_ddim(self, x, c, t, index, repeat_noise=False, use_original_steps=False, quantize_denoised=False, temperature=1.0, noise_dropout=0.0, score_corrector=None, corrector_kwargs=None, unconditional_guidance_scale=1.0, unconditional_conditioning=None):
        b, *_, device = (*x.shape, x.device)
        if unconditional_conditioning is None or unconditional_guidance_scale == 1.0:
            e_t = self.model.apply_model(x, t, c)
        else:
            x_in = torch.cat([x] * 2)
            t_in = torch.cat([t] * 2)
            c_in = torch.cat([unconditional_conditioning, c])
            e_t_uncond, e_t = self.model.apply_model(x_in, t_in, c_in).chunk(2)
            e_t = e_t_uncond + unconditional_guidance_scale * (e_t - e_t_uncond)
        if score_corrector is not None:
            assert self.model.parameterization == 'eps'
            e_t = score_corrector.modify_score(self.model, e_t, x, t, c, **corrector_kwargs)
        alphas = self.model.alphas_cumprod if use_original_steps else self.ddim_alphas
        alphas_prev = self.model.alphas_cumprod_prev if use_original_steps else self.ddim_alphas_prev
        sqrt_one_minus_alphas = self.model.sqrt_one_minus_alphas_cumprod if use_original_steps else self.ddim_sqrt_one_minus_alphas
        sigmas = self.model.ddim_sigmas_for_original_num_steps if use_original_steps else self.ddim_sigmas
        a_t = torch.full((b, 1, 1, 1), alphas[index], device=device)
        a_prev = torch.full((b, 1, 1, 1), alphas_prev[index], device=device)
        sigma_t = torch.full((b, 1, 1, 1), sigmas[index], device=device)
        sqrt_one_minus_at = torch.full((b, 1, 1, 1), sqrt_one_minus_alphas[index], device=device)
        pred_x0 = (x - sqrt_one_minus_at * e_t) / a_t.sqrt()
        if quantize_denoised:
            pred_x0, _, *_ = self.model.first_stage_model.quantize(pred_x0)
        dir_xt = (1.0 - a_prev - sigma_t ** 2).sqrt() * e_t
        noise = sigma_t * noise_like(x.shape, device, repeat_noise) * temperature
        if noise_dropout > 0.0:
            noise = torch.nn.functional.dropout(noise, p=noise_dropout)
        x_prev = a_prev.sqrt() * pred_x0 + dir_xt + noise
        return (x_prev, pred_x0)

def register_buffer(self, name, attr):
    if type(attr) == torch.Tensor:
        if attr.device != torch.device('cuda'):
            attr = attr.to(torch.device('cuda'))
    setattr(self, name, attr)

class DDPM(pl.LightningModule):

    def __init__(self, unet_config, timesteps=1000, beta_schedule='linear', loss_type='l2', ckpt_path=None, ignore_keys=[], load_only_unet=False, monitor='val/loss', use_ema=True, first_stage_key='image', image_size=256, channels=3, log_every_t=100, clip_denoised=True, linear_start=0.0001, linear_end=0.02, cosine_s=0.008, given_betas=None, original_elbo_weight=0.0, v_posterior=0.0, l_simple_weight=1.0, conditioning_key=None, parameterization='eps', scheduler_config=None, use_positional_encodings=False, learn_logvar=False, logvar_init=0.0):
        super().__init__()
        assert parameterization in ['eps', 'x0'], 'currently only supporting "eps" and "x0"'
        self.parameterization = parameterization
        print(f'{self.__class__.__name__}: Running in {self.parameterization}-prediction mode')
        self.cond_stage_model = None
        self.clip_denoised = clip_denoised
        self.log_every_t = log_every_t
        self.first_stage_key = first_stage_key
        self.image_size = image_size
        self.channels = channels
        self.use_positional_encodings = use_positional_encodings
        self.model = DiffusionWrapper(unet_config, conditioning_key)
        count_params(self.model, verbose=True)
        self.use_ema = use_ema
        if self.use_ema:
            self.model_ema = LitEma(self.model)
            print(f'Keeping EMAs of {len(list(self.model_ema.buffers()))}.')
        self.use_scheduler = scheduler_config is not None
        if self.use_scheduler:
            self.scheduler_config = scheduler_config
        self.v_posterior = v_posterior
        self.original_elbo_weight = original_elbo_weight
        self.l_simple_weight = l_simple_weight
        if monitor is not None:
            self.monitor = monitor
        if ckpt_path is not None:
            self.init_from_ckpt(ckpt_path, ignore_keys=ignore_keys, only_model=load_only_unet)
        self.register_schedule(given_betas=given_betas, beta_schedule=beta_schedule, timesteps=timesteps, linear_start=linear_start, linear_end=linear_end, cosine_s=cosine_s)
        self.loss_type = loss_type
        self.learn_logvar = learn_logvar
        self.logvar = torch.full(fill_value=logvar_init, size=(self.num_timesteps,))
        if self.learn_logvar:
            self.logvar = nn.Parameter(self.logvar, requires_grad=True)

    def register_schedule(self, given_betas=None, beta_schedule='linear', timesteps=1000, linear_start=0.0001, linear_end=0.02, cosine_s=0.008):
        if exists(given_betas):
            betas = given_betas
        else:
            betas = make_beta_schedule(beta_schedule, timesteps, linear_start=linear_start, linear_end=linear_end, cosine_s=cosine_s)
        alphas = 1.0 - betas
        alphas_cumprod = np.cumprod(alphas, axis=0)
        alphas_cumprod_prev = np.append(1.0, alphas_cumprod[:-1])
        timesteps, = betas.shape
        self.num_timesteps = int(timesteps)
        self.linear_start = linear_start
        self.linear_end = linear_end
        assert alphas_cumprod.shape[0] == self.num_timesteps, 'alphas have to be defined for each timestep'
        to_torch = partial(torch.tensor, dtype=torch.float32)
        self.register_buffer('betas', to_torch(betas))
        self.register_buffer('alphas_cumprod', to_torch(alphas_cumprod))
        self.register_buffer('alphas_cumprod_prev', to_torch(alphas_cumprod_prev))
        self.register_buffer('sqrt_alphas_cumprod', to_torch(np.sqrt(alphas_cumprod)))
        self.register_buffer('sqrt_one_minus_alphas_cumprod', to_torch(np.sqrt(1.0 - alphas_cumprod)))
        self.register_buffer('log_one_minus_alphas_cumprod', to_torch(np.log(1.0 - alphas_cumprod)))
        self.register_buffer('sqrt_recip_alphas_cumprod', to_torch(np.sqrt(1.0 / alphas_cumprod)))
        self.register_buffer('sqrt_recipm1_alphas_cumprod', to_torch(np.sqrt(1.0 / alphas_cumprod - 1)))
        posterior_variance = (1 - self.v_posterior) * betas * (1.0 - alphas_cumprod_prev) / (1.0 - alphas_cumprod) + self.v_posterior * betas
        self.register_buffer('posterior_variance', to_torch(posterior_variance))
        self.register_buffer('posterior_log_variance_clipped', to_torch(np.log(np.maximum(posterior_variance, 1e-20))))
        self.register_buffer('posterior_mean_coef1', to_torch(betas * np.sqrt(alphas_cumprod_prev) / (1.0 - alphas_cumprod)))
        self.register_buffer('posterior_mean_coef2', to_torch((1.0 - alphas_cumprod_prev) * np.sqrt(alphas) / (1.0 - alphas_cumprod)))
        if self.parameterization == 'eps':
            lvlb_weights = self.betas ** 2 / (2 * self.posterior_variance * to_torch(alphas) * (1 - self.alphas_cumprod))
        elif self.parameterization == 'x0':
            lvlb_weights = 0.5 * np.sqrt(torch.Tensor(alphas_cumprod)) / (2.0 * 1 - torch.Tensor(alphas_cumprod))
        else:
            raise NotImplementedError('mu not supported')
        lvlb_weights[0] = lvlb_weights[1]
        self.register_buffer('lvlb_weights', lvlb_weights, persistent=False)
        assert not torch.isnan(self.lvlb_weights).all()

    @contextmanager
    def ema_scope(self, context=None):
        if self.use_ema:
            self.model_ema.store(self.model.parameters())
            self.model_ema.copy_to(self.model)
            if context is not None:
                print(f'{context}: Switched to EMA weights')
        try:
            yield None
        finally:
            if self.use_ema:
                self.model_ema.restore(self.model.parameters())
                if context is not None:
                    print(f'{context}: Restored training weights')

    def init_from_ckpt(self, path, ignore_keys=list(), only_model=False):
        sd = torch.load(path, map_location='cpu')
        if 'state_dict' in list(sd.keys()):
            sd = sd['state_dict']
        keys = list(sd.keys())
        for k in keys:
            for ik in ignore_keys:
                if k.startswith(ik):
                    print('Deleting key {} from state_dict.'.format(k))
                    del sd[k]
        missing, unexpected = self.load_state_dict(sd, strict=False) if not only_model else self.model.load_state_dict(sd, strict=False)
        print(f'Restored from {path} with {len(missing)} missing and {len(unexpected)} unexpected keys')
        if len(missing) > 0:
            print(f'Missing Keys: {missing}')
        if len(unexpected) > 0:
            print(f'Unexpected Keys: {unexpected}')

    def q_mean_variance(self, x_start, t):
        """
        Get the distribution q(x_t | x_0).
        :param x_start: the [N x C x ...] tensor of noiseless inputs.
        :param t: the number of diffusion steps (minus 1). Here, 0 means one step.
        :return: A tuple (mean, variance, log_variance), all of x_start's shape.
        """
        mean = extract_into_tensor(self.sqrt_alphas_cumprod, t, x_start.shape) * x_start
        variance = extract_into_tensor(1.0 - self.alphas_cumprod, t, x_start.shape)
        log_variance = extract_into_tensor(self.log_one_minus_alphas_cumprod, t, x_start.shape)
        return (mean, variance, log_variance)

    def predict_start_from_noise(self, x_t, t, noise):
        return extract_into_tensor(self.sqrt_recip_alphas_cumprod, t, x_t.shape) * x_t - extract_into_tensor(self.sqrt_recipm1_alphas_cumprod, t, x_t.shape) * noise

    def q_posterior(self, x_start, x_t, t):
        posterior_mean = extract_into_tensor(self.posterior_mean_coef1, t, x_t.shape) * x_start + extract_into_tensor(self.posterior_mean_coef2, t, x_t.shape) * x_t
        posterior_variance = extract_into_tensor(self.posterior_variance, t, x_t.shape)
        posterior_log_variance_clipped = extract_into_tensor(self.posterior_log_variance_clipped, t, x_t.shape)
        return (posterior_mean, posterior_variance, posterior_log_variance_clipped)

    def p_mean_variance(self, x, t, clip_denoised: bool):
        model_out = self.model(x, t)
        if self.parameterization == 'eps':
            x_recon = self.predict_start_from_noise(x, t=t, noise=model_out)
        elif self.parameterization == 'x0':
            x_recon = model_out
        if clip_denoised:
            x_recon.clamp_(-1.0, 1.0)
        model_mean, posterior_variance, posterior_log_variance = self.q_posterior(x_start=x_recon, x_t=x, t=t)
        return (model_mean, posterior_variance, posterior_log_variance)

    @torch.no_grad()
    def p_sample(self, x, t, clip_denoised=True, repeat_noise=False):
        b, *_, device = (*x.shape, x.device)
        model_mean, _, model_log_variance = self.p_mean_variance(x=x, t=t, clip_denoised=clip_denoised)
        noise = noise_like(x.shape, device, repeat_noise)
        nonzero_mask = (1 - (t == 0).float()).reshape(b, *(1,) * (len(x.shape) - 1))
        return model_mean + nonzero_mask * (0.5 * model_log_variance).exp() * noise

    @torch.no_grad()
    def p_sample_loop(self, shape, return_intermediates=False):
        device = self.betas.device
        b = shape[0]
        img = torch.randn(shape, device=device)
        intermediates = [img]
        for i in tqdm(reversed(range(0, self.num_timesteps)), desc='Sampling t', total=self.num_timesteps):
            img = self.p_sample(img, torch.full((b,), i, device=device, dtype=torch.long), clip_denoised=self.clip_denoised)
            if i % self.log_every_t == 0 or i == self.num_timesteps - 1:
                intermediates.append(img)
        if return_intermediates:
            return (img, intermediates)
        return img

    @torch.no_grad()
    def sample(self, batch_size=16, return_intermediates=False):
        image_size = self.image_size
        channels = self.channels
        return self.p_sample_loop((batch_size, channels, image_size, image_size), return_intermediates=return_intermediates)

    def q_sample(self, x_start, t, noise=None):
        noise = default(noise, lambda: torch.randn_like(x_start))
        return extract_into_tensor(self.sqrt_alphas_cumprod, t, x_start.shape) * x_start + extract_into_tensor(self.sqrt_one_minus_alphas_cumprod, t, x_start.shape) * noise

    def get_loss(self, pred, target, mean=True):
        if self.loss_type == 'l1':
            loss = (target - pred).abs()
            if mean:
                loss = loss.mean()
        elif self.loss_type == 'l2':
            if mean:
                loss = torch.nn.functional.mse_loss(target, pred)
            else:
                loss = torch.nn.functional.mse_loss(target, pred, reduction='none')
        else:
            raise NotImplementedError("unknown loss type '{loss_type}'")
        return loss

    def p_losses(self, x_start, t, noise=None):
        noise = default(noise, lambda: torch.randn_like(x_start))
        x_noisy = self.q_sample(x_start=x_start, t=t, noise=noise)
        model_out = self.model(x_noisy, t)
        loss_dict = {}
        if self.parameterization == 'eps':
            target = noise
        elif self.parameterization == 'x0':
            target = x_start
        else:
            raise NotImplementedError(f'Paramterization {self.parameterization} not yet supported')
        loss = self.get_loss(model_out, target, mean=False).mean(dim=[1, 2, 3])
        log_prefix = 'train' if self.training else 'val'
        loss_dict.update({f'{log_prefix}/loss_simple': loss.mean()})
        loss_simple = loss.mean() * self.l_simple_weight
        loss_vlb = (self.lvlb_weights[t] * loss).mean()
        loss_dict.update({f'{log_prefix}/loss_vlb': loss_vlb})
        loss = loss_simple + self.original_elbo_weight * loss_vlb
        loss_dict.update({f'{log_prefix}/loss': loss})
        return (loss, loss_dict)

    def forward(self, x, *args, **kwargs):
        t = torch.randint(0, self.num_timesteps, (x.shape[0],), device=self.device).long()
        return self.p_losses(x, t, *args, **kwargs)

    def get_input(self, batch, k):
        x = batch[k]
        if len(x.shape) == 3:
            x = x[..., None]
        x = rearrange(x, 'b h w c -> b c h w')
        x = x.to(memory_format=torch.contiguous_format).float()
        return x

    def shared_step(self, batch):
        x = self.get_input(batch, self.first_stage_key)
        loss, loss_dict = self(x)
        return (loss, loss_dict)

    def training_step(self, batch, batch_idx):
        loss, loss_dict = self.shared_step(batch)
        self.log_dict(loss_dict, prog_bar=True, logger=True, on_step=True, on_epoch=True)
        self.log('global_step', self.global_step, prog_bar=True, logger=True, on_step=True, on_epoch=False)
        if self.use_scheduler:
            lr = self.optimizers().param_groups[0]['lr']
            self.log('lr_abs', lr, prog_bar=True, logger=True, on_step=True, on_epoch=False)
        return loss

    @torch.no_grad()
    def validation_step(self, batch, batch_idx):
        _, loss_dict_no_ema = self.shared_step(batch)
        with self.ema_scope():
            _, loss_dict_ema = self.shared_step(batch)
            loss_dict_ema = {key + '_ema': loss_dict_ema[key] for key in loss_dict_ema}
        self.log_dict(loss_dict_no_ema, prog_bar=False, logger=True, on_step=False, on_epoch=True)
        self.log_dict(loss_dict_ema, prog_bar=False, logger=True, on_step=False, on_epoch=True)

    def on_train_batch_end(self, *args, **kwargs):
        if self.use_ema:
            self.model_ema(self.model)

    def _get_rows_from_list(self, samples):
        n_imgs_per_row = len(samples)
        denoise_grid = rearrange(samples, 'n b c h w -> b n c h w')
        denoise_grid = rearrange(denoise_grid, 'b n c h w -> (b n) c h w')
        denoise_grid = make_grid(denoise_grid, nrow=n_imgs_per_row)
        return denoise_grid

    @torch.no_grad()
    def log_images(self, batch, N=8, n_row=2, sample=True, return_keys=None, **kwargs):
        log = dict()
        x = self.get_input(batch, self.first_stage_key)
        N = min(x.shape[0], N)
        n_row = min(x.shape[0], n_row)
        x = x.to(self.device)[:N]
        log['inputs'] = x
        diffusion_row = list()
        x_start = x[:n_row]
        for t in range(self.num_timesteps):
            if t % self.log_every_t == 0 or t == self.num_timesteps - 1:
                t = repeat(torch.tensor([t]), '1 -> b', b=n_row)
                t = t.to(self.device).long()
                noise = torch.randn_like(x_start)
                x_noisy = self.q_sample(x_start=x_start, t=t, noise=noise)
                diffusion_row.append(x_noisy)
        log['diffusion_row'] = self._get_rows_from_list(diffusion_row)
        if sample:
            with self.ema_scope('Plotting'):
                samples, denoise_row = self.sample(batch_size=N, return_intermediates=True)
            log['samples'] = samples
            log['denoise_row'] = self._get_rows_from_list(denoise_row)
        if return_keys:
            if np.intersect1d(list(log.keys()), return_keys).shape[0] == 0:
                return log
            else:
                return {key: log[key] for key in return_keys}
        return log

    def configure_optimizers(self):
        lr = self.learning_rate
        params = list(self.model.parameters())
        if self.learn_logvar:
            params = params + [self.logvar]
        opt = torch.optim.AdamW(params, lr=lr)
        return opt

def get_loss(self, pred, target, mean=True):
    if self.loss_type == 'l1':
        loss = (target - pred).abs()
        if mean:
            loss = loss.mean()
    elif self.loss_type == 'l2':
        if mean:
            loss = torch.nn.functional.mse_loss(target, pred)
        else:
            loss = torch.nn.functional.mse_loss(target, pred, reduction='none')
    else:
        raise NotImplementedError("unknown loss type '{loss_type}'")
    return loss

class Layout2ImgDiffusion(LatentDiffusion):

    def __init__(self, cond_stage_key, *args, **kwargs):
        assert cond_stage_key == 'coordinates_bbox', 'Layout2ImgDiffusion only for cond_stage_key="coordinates_bbox"'
        super().__init__(*args, cond_stage_key=cond_stage_key, **kwargs)

    def log_images(self, batch, N=8, *args, **kwargs):
        logs = super().log_images(*args, batch=batch, N=N, **kwargs)
        key = 'train' if self.training else 'validation'
        dset = self.trainer.datamodule.datasets[key]
        mapper = dset.conditional_builders[self.cond_stage_key]
        bbox_imgs = []
        map_fn = lambda catno: dset.get_textual_label(dset.get_category_id(catno))
        for tknzd_bbox in batch[self.cond_stage_key][:N]:
            bboximg = mapper.plot(tknzd_bbox.detach().cpu(), map_fn, (256, 256))
            bbox_imgs.append(bboximg)
        cond_img = torch.stack(bbox_imgs, dim=0)
        logs['bbox_image'] = cond_img
        return logs

def log_images(self, batch, N=8, *args, **kwargs):
    logs = super().log_images(*args, batch=batch, N=N, **kwargs)
    key = 'train' if self.training else 'validation'
    dset = self.trainer.datamodule.datasets[key]
    mapper = dset.conditional_builders[self.cond_stage_key]
    bbox_imgs = []
    map_fn = lambda catno: dset.get_textual_label(dset.get_category_id(catno))
    for tknzd_bbox in batch[self.cond_stage_key][:N]:
        bboximg = mapper.plot(tknzd_bbox.detach().cpu(), map_fn, (256, 256))
        bbox_imgs.append(bboximg)
    cond_img = torch.stack(bbox_imgs, dim=0)
    logs['bbox_image'] = cond_img
    return logs

class PLMSSampler(object):

    def __init__(self, model, schedule='linear', **kwargs):
        super().__init__()
        self.model = model
        self.ddpm_num_timesteps = model.num_timesteps
        self.schedule = schedule

    def register_buffer(self, name, attr):
        if type(attr) == torch.Tensor:
            if attr.device != torch.device('cuda'):
                attr = attr.to(torch.device('cuda'))
        setattr(self, name, attr)

    def make_schedule(self, ddim_num_steps, ddim_discretize='uniform', ddim_eta=0.0, verbose=True):
        if ddim_eta != 0:
            raise ValueError('ddim_eta must be 0 for PLMS')
        self.ddim_timesteps = make_ddim_timesteps(ddim_discr_method=ddim_discretize, num_ddim_timesteps=ddim_num_steps, num_ddpm_timesteps=self.ddpm_num_timesteps, verbose=verbose)
        alphas_cumprod = self.model.alphas_cumprod
        assert alphas_cumprod.shape[0] == self.ddpm_num_timesteps, 'alphas have to be defined for each timestep'
        to_torch = lambda x: x.clone().detach().to(torch.float32).to(self.model.device)
        self.register_buffer('betas', to_torch(self.model.betas))
        self.register_buffer('alphas_cumprod', to_torch(alphas_cumprod))
        self.register_buffer('alphas_cumprod_prev', to_torch(self.model.alphas_cumprod_prev))
        self.register_buffer('sqrt_alphas_cumprod', to_torch(np.sqrt(alphas_cumprod.cpu())))
        self.register_buffer('sqrt_one_minus_alphas_cumprod', to_torch(np.sqrt(1.0 - alphas_cumprod.cpu())))
        self.register_buffer('log_one_minus_alphas_cumprod', to_torch(np.log(1.0 - alphas_cumprod.cpu())))
        self.register_buffer('sqrt_recip_alphas_cumprod', to_torch(np.sqrt(1.0 / alphas_cumprod.cpu())))
        self.register_buffer('sqrt_recipm1_alphas_cumprod', to_torch(np.sqrt(1.0 / alphas_cumprod.cpu() - 1)))
        ddim_sigmas, ddim_alphas, ddim_alphas_prev = make_ddim_sampling_parameters(alphacums=alphas_cumprod.cpu(), ddim_timesteps=self.ddim_timesteps, eta=ddim_eta, verbose=verbose)
        self.register_buffer('ddim_sigmas', ddim_sigmas)
        self.register_buffer('ddim_alphas', ddim_alphas)
        self.register_buffer('ddim_alphas_prev', ddim_alphas_prev)
        self.register_buffer('ddim_sqrt_one_minus_alphas', np.sqrt(1.0 - ddim_alphas))
        sigmas_for_original_sampling_steps = ddim_eta * torch.sqrt((1 - self.alphas_cumprod_prev) / (1 - self.alphas_cumprod) * (1 - self.alphas_cumprod / self.alphas_cumprod_prev))
        self.register_buffer('ddim_sigmas_for_original_num_steps', sigmas_for_original_sampling_steps)

    @torch.no_grad()
    def sample(self, S, batch_size, shape, conditioning=None, callback=None, normals_sequence=None, img_callback=None, quantize_x0=False, eta=0.0, mask=None, x0=None, temperature=1.0, noise_dropout=0.0, score_corrector=None, corrector_kwargs=None, verbose=True, x_T=None, log_every_t=100, unconditional_guidance_scale=1.0, unconditional_conditioning=None, **kwargs):
        if conditioning is not None:
            if isinstance(conditioning, dict):
                cbs = conditioning[list(conditioning.keys())[0]].shape[0]
                if cbs != batch_size:
                    print(f'Warning: Got {cbs} conditionings but batch-size is {batch_size}')
            elif conditioning.shape[0] != batch_size:
                print(f'Warning: Got {conditioning.shape[0]} conditionings but batch-size is {batch_size}')
        self.make_schedule(ddim_num_steps=S, ddim_eta=eta, verbose=verbose)
        C, H, W = shape
        size = (batch_size, C, H, W)
        print(f'Data shape for PLMS sampling is {size}')
        samples, intermediates = self.plms_sampling(conditioning, size, callback=callback, img_callback=img_callback, quantize_denoised=quantize_x0, mask=mask, x0=x0, ddim_use_original_steps=False, noise_dropout=noise_dropout, temperature=temperature, score_corrector=score_corrector, corrector_kwargs=corrector_kwargs, x_T=x_T, log_every_t=log_every_t, unconditional_guidance_scale=unconditional_guidance_scale, unconditional_conditioning=unconditional_conditioning)
        return (samples, intermediates)

    @torch.no_grad()
    def plms_sampling(self, cond, shape, x_T=None, ddim_use_original_steps=False, callback=None, timesteps=None, quantize_denoised=False, mask=None, x0=None, img_callback=None, log_every_t=100, temperature=1.0, noise_dropout=0.0, score_corrector=None, corrector_kwargs=None, unconditional_guidance_scale=1.0, unconditional_conditioning=None):
        device = self.model.betas.device
        b = shape[0]
        if x_T is None:
            img = torch.randn(shape, device=device)
        else:
            img = x_T
        if timesteps is None:
            timesteps = self.ddpm_num_timesteps if ddim_use_original_steps else self.ddim_timesteps
        elif timesteps is not None and (not ddim_use_original_steps):
            subset_end = int(min(timesteps / self.ddim_timesteps.shape[0], 1) * self.ddim_timesteps.shape[0]) - 1
            timesteps = self.ddim_timesteps[:subset_end]
        intermediates = {'x_inter': [img], 'pred_x0': [img]}
        time_range = list(reversed(range(0, timesteps))) if ddim_use_original_steps else np.flip(timesteps)
        total_steps = timesteps if ddim_use_original_steps else timesteps.shape[0]
        print(f'Running PLMS Sampling with {total_steps} timesteps')
        iterator = tqdm(time_range, desc='PLMS Sampler', total=total_steps)
        old_eps = []
        for i, step in enumerate(iterator):
            index = total_steps - i - 1
            ts = torch.full((b,), step, device=device, dtype=torch.long)
            ts_next = torch.full((b,), time_range[min(i + 1, len(time_range) - 1)], device=device, dtype=torch.long)
            if mask is not None:
                assert x0 is not None
                img_orig = self.model.q_sample(x0, ts)
                img = img_orig * mask + (1.0 - mask) * img
            outs = self.p_sample_plms(img, cond, ts, index=index, use_original_steps=ddim_use_original_steps, quantize_denoised=quantize_denoised, temperature=temperature, noise_dropout=noise_dropout, score_corrector=score_corrector, corrector_kwargs=corrector_kwargs, unconditional_guidance_scale=unconditional_guidance_scale, unconditional_conditioning=unconditional_conditioning, old_eps=old_eps, t_next=ts_next)
            img, pred_x0, e_t = outs
            old_eps.append(e_t)
            if len(old_eps) >= 4:
                old_eps.pop(0)
            if callback:
                callback(i)
            if img_callback:
                img_callback(pred_x0, i)
            if index % log_every_t == 0 or index == total_steps - 1:
                intermediates['x_inter'].append(img)
                intermediates['pred_x0'].append(pred_x0)
        return (img, intermediates)

    @torch.no_grad()
    def p_sample_plms(self, x, c, t, index, repeat_noise=False, use_original_steps=False, quantize_denoised=False, temperature=1.0, noise_dropout=0.0, score_corrector=None, corrector_kwargs=None, unconditional_guidance_scale=1.0, unconditional_conditioning=None, old_eps=None, t_next=None):
        b, *_, device = (*x.shape, x.device)

        def get_model_output(x, t):
            if unconditional_conditioning is None or unconditional_guidance_scale == 1.0:
                e_t = self.model.apply_model(x, t, c)
            else:
                x_in = torch.cat([x] * 2)
                t_in = torch.cat([t] * 2)
                c_in = torch.cat([unconditional_conditioning, c])
                e_t_uncond, e_t = self.model.apply_model(x_in, t_in, c_in).chunk(2)
                e_t = e_t_uncond + unconditional_guidance_scale * (e_t - e_t_uncond)
            if score_corrector is not None:
                assert self.model.parameterization == 'eps'
                e_t = score_corrector.modify_score(self.model, e_t, x, t, c, **corrector_kwargs)
            return e_t
        alphas = self.model.alphas_cumprod if use_original_steps else self.ddim_alphas
        alphas_prev = self.model.alphas_cumprod_prev if use_original_steps else self.ddim_alphas_prev
        sqrt_one_minus_alphas = self.model.sqrt_one_minus_alphas_cumprod if use_original_steps else self.ddim_sqrt_one_minus_alphas
        sigmas = self.model.ddim_sigmas_for_original_num_steps if use_original_steps else self.ddim_sigmas

        def get_x_prev_and_pred_x0(e_t, index):
            a_t = torch.full((b, 1, 1, 1), alphas[index], device=device)
            a_prev = torch.full((b, 1, 1, 1), alphas_prev[index], device=device)
            sigma_t = torch.full((b, 1, 1, 1), sigmas[index], device=device)
            sqrt_one_minus_at = torch.full((b, 1, 1, 1), sqrt_one_minus_alphas[index], device=device)
            pred_x0 = (x - sqrt_one_minus_at * e_t) / a_t.sqrt()
            if quantize_denoised:
                pred_x0, _, *_ = self.model.first_stage_model.quantize(pred_x0)
            dir_xt = (1.0 - a_prev - sigma_t ** 2).sqrt() * e_t
            noise = sigma_t * noise_like(x.shape, device, repeat_noise) * temperature
            if noise_dropout > 0.0:
                noise = torch.nn.functional.dropout(noise, p=noise_dropout)
            x_prev = a_prev.sqrt() * pred_x0 + dir_xt + noise
            return (x_prev, pred_x0)
        e_t = get_model_output(x, t)
        if len(old_eps) == 0:
            x_prev, pred_x0 = get_x_prev_and_pred_x0(e_t, index)
            e_t_next = get_model_output(x_prev, t_next)
            e_t_prime = (e_t + e_t_next) / 2
        elif len(old_eps) == 1:
            e_t_prime = (3 * e_t - old_eps[-1]) / 2
        elif len(old_eps) == 2:
            e_t_prime = (23 * e_t - 16 * old_eps[-1] + 5 * old_eps[-2]) / 12
        elif len(old_eps) >= 3:
            e_t_prime = (55 * e_t - 59 * old_eps[-1] + 37 * old_eps[-2] - 9 * old_eps[-3]) / 24
        x_prev, pred_x0 = get_x_prev_and_pred_x0(e_t_prime, index)
        return (x_prev, pred_x0, e_t)

def register_buffer(self, name, attr):
    if type(attr) == torch.Tensor:
        if attr.device != torch.device('cuda'):
            attr = attr.to(torch.device('cuda'))
    setattr(self, name, attr)

class AssetSelectAgent:

    def __init__(self, config):
        self.config = config
        self.asset_bank = {'audi': 'Audi_Q3_2023.blend', 'benz_g': 'Benz_G.blend', 'benz_s': 'Benz_S.blend', 'mini': 'BMW_mini.blend', 'cadillac': 'Cadillac_CT6.blend', 'chevrolet': 'Chevrolet.blend', 'dodge': 'Dodge_SRT_Hellcat.blend', 'ferriari': 'Ferriari_f150.blend', 'lamborghini': 'Lamborghini.blend', 'rover': 'Land_Rover_range_rover.blend', 'tank': 'M1A2_tank.blend', 'police_car': 'Police_car.blend', 'porsche': 'Porsche-911-4s-final.blend', 'tesla_cybertruck': 'Tesla_cybertruck.blend', 'tesla_roadster': 'Tesla_roadster.blend', 'loader_truck': 'obstacles/Loader_truck.blend', 'bulldozer': 'obstacles/Bulldozer.blend', 'cement': 'obstacles/Cement_isolation_pier.blend', 'excavator': 'obstacles/Excavator.blend', 'sign_fence': 'obstacles/Sign_fence.blend', 'cone': 'obstacles/Traffic_cone.blend'}
        self.assets_dir = config['assets_dir']

    def llm_selecting_asset(self, scene, message):
        try:
            q0 = "I will provide you with an operation statement to add and place a vehicle, and I need you to determine the car's color and type. "
            q1 = 'You need to return a JSON dictionary with 2 keys, including '
            q2 = "(1) 'color', representing in RGB with range from 0 to 255. If the color is not mentioned, the value is just 'default'."
            q3 = "(2) 'type', one of [audi, benz_g, benz_s, mini, cadillac, chevrolet, dodge, ferriari, lamborghini, rover, tank, police_car, porsche, tesla_cybertruck, tesla_roadster, cone, loader_truck, bulldozer, cement, excavator, sign_fence, random]. If the type is not mentioned or not in the type list, it defaults to random."
            q4 = "An example: Given operation statement 'add a black Rover at the front', you should return: {'color':[0,0,0], 'type':'Rover'}"
            q5 = 'Note that you should not return any code or explanations, only provide a JSON dictionary.'
            q6 = 'The operation statement is:' + message
            prompt_list = [q0, q1, q2, q3, q4, q5, q6]
            result = openai.ChatCompletion.create(model='gpt-4', messages=[{'role': 'system', 'content': "You are an assistant helping me to determine a car's color and type."}] + [{'role': 'user', 'content': q} for q in prompt_list])
            answer = result['choices'][0]['message']['content']
            print(f'{colored('[Asset Agent LLM] deciding asset type and color', color='magenta', attrs=['bold'])}                     \n{colored('[Raw Response>>>]', attrs=['bold'])} {answer}')
            start = answer.index('{')
            answer = answer[start:]
            end = answer.rfind('}')
            answer = answer[:end + 1]
            color_and_type = eval(answer)
            color_and_type['type'] = color_and_type['type'] if color_and_type['type'] != 'random' else random.choice(list(self.asset_bank.keys()))
            print(f'{colored('[Extracted Response>>>]', attrs=['bold'])} {color_and_type} \n')
        except Exception as e:
            print(e)
            traceback.print_exc()
            return '[Asset Agent LLM] deciding asset type and color fails.'
        return color_and_type

    def llm_revise_added_cars(self, scene, message, added_car_dict):
        """ This function is a little go beyond asset_select_agent's role. It also consider the motion of the car

        It determine how to modify the dictionary about already added cars
        """
        try:
            q0 = 'I will provide you with a dictionary in which each key is a vehicle id, and each value is the status description of the vehicle in the scene.'
            q1 = 'Specifically, description of the vehicle is also a dictionary. It has keys as follows:'
            q2 = "(1) 'x', vehicle's x position in meter. positive x is heading forward (2) 'y', vehicle's y position in meter. positive y is heading left " + "(3) 'color', vehicle's color in RGB. 'color' would be 'default' or a list represent the RGB values. If the color is not mentioned, the value is just 'default'."
            q3 = "(4) 'type', one of [audi, benz_g, benz_s, mini, cadillac, chevrolet, dodge, ferriari, lamborghini, rover, tank, police_car, porsche, tesla_cybertruck, tesla_roadster, cone, loader_truck, bulldozer, cement, excavator, sign_fence]. "
            q4 = "(5) 'action', vehicle's driving action, one of ['random', 'straight', 'turn left', 'turn right', 'change lane left', 'change lane right', 'static', 'back']"
            q5 = "(6) 'speed', vehicle's driving speed, one of ['random', 'fast', 'slow']"
            q6 = "(7) 'direction', one of ['away', 'close']. In ego view, moving forward is 'away' while moving towards is 'close'."
            q7 = 'I will get you a requirement. To follow my requirement, you should first find out which car I am describing, and then modify its status description dictionary according to my requirement.                 For unmentioned properties, keep them unchanged.'
            q8 = f'Now the dictionary is {added_car_dict}, and my requirement is {message}. '
            q9 = "Note that you should return a JSON dictionary, which only containing the specfic car in requirement with its modified status.                 Just return the JSON dictionary, I'm not asking you to write code."
            prompt_list = [q0, q1, q2, q3, q4, q5, q6, q7, q8, q9]
            result = openai.ChatCompletion.create(model='gpt-4', messages=[{'role': 'system', 'content': 'You are an assistant helping me modify and return dictionaries.'}] + [{'role': 'user', 'content': q} for q in prompt_list])
            answer = result['choices'][0]['message']['content']
            print(f'{colored('[Asset Select Agent LLM] revising added cars', color='magenta', attrs=['bold'])}                      \n{colored('[Raw Response>>>]', attrs=['bold'])} {answer}')
            start = answer.index('{')
            answer = answer[start:]
            end = answer.rfind('}')
            answer = answer[:end + 1]
            modified_car_dict = eval(answer)
            print(f'{colored('[Extracted Response>>>]', attrs=['bold'])} {modified_car_dict} (number={len(modified_car_dict)})\n')
        except Exception as e:
            print(e)
            traceback.print_exc()
            return '[Asset Select Agent LLM] revising added cars fails.'
        return modified_car_dict

    def func_retrieve_blender_file(self, scene):
        """Retrieve the path of the asset file given the asset type.
        """
        for car_name, car_info in scene.added_cars_dict.items():
            car_blender_file = self.asset_bank[car_info['type'].casefold()]
            car_info['blender_file'] = os.path.join(self.assets_dir, car_blender_file)

def func_retrieve_blender_file(self, scene):
    """Retrieve the path of the asset file given the asset type.
        """
    for car_name, car_info in scene.added_cars_dict.items():
        car_blender_file = self.asset_bank[car_info['type'].casefold()]
        car_info['blender_file'] = os.path.join(self.assets_dir, car_blender_file)

class ProjectManager:

    def __init__(self, config):
        self.config = config

    def decompose_prompt(self, scene, user_prompt):
        """ decompose the prompt to the corresponding chatsim.agents.
        Input:
            scene : Scene
                scene object.
            user_prompt : str
                language prompt to ChatSim.
        Return:
            tasks : dict
                a dictionary of decomposed tasks.
        """
        q0 = 'I have a requirement of editing operations in an autonomous driving scenario, and I need your help to break it down into one or several supportable actions. The scene is large which means many vehicles can be contained. '
        q1 = 'The supportable five actions include adding vehicles ,                 deleting vehicles ,                 put back deleted vehicles,                 adjusting added vehicles ,                 viewpoint adjustment.'
        q2 = 'Please try to retain all the semantics and adjunct words from the original text. Each adding action should only contain one car. ' + 'Information about adding vehicles (such as their type, positions, driving status, speed, color, etc.) should be directly included within the adding action.'
        q3 = 'Split actions should be stored in a JSON dictonary. The key is action id and the value is specific action. They will be executed sequentially, and the broken operations should be independent with each other and do not rely on the detailed scene information.'
        q4 = "An example: the requirement is 'substitute the red car in the scene', you break it down and return" + "{ 1: 'Delete the red car from the scene', 2: 'Add a new car at the location where the red car was deleted' }."
        q5 = "An example: the requirement is 'delete the farthest car and add a red Audi in the right front', you break it down and return " + "{ 1: 'Delete the farthest car', 2: 'Add a red Audi in the right front' }"
        q6 = "An example: the requirement is 'delete all cars', you break it down and return " + "{ 1: 'Delete all the cars'} "
        q7 = 'I may provide very abstract requirements. For such requirements, you should analyze how to comply with the splitting of actions.'
        q8 = "An example (very abstract): the requirement is 'I want several cars driving slowly in the scene', you analyse and return " + "{ 1: 'Add one car driving slowly', 2 : 'Add one car driving slowly', 3 : 'Add one car driving slowly', 4 : 'Add one car driving slowly', 5 : 'Add one car driving slowly', 6 : 'Add one car driving slowly', 7 : 'Add one car driving slowly'} "
        q9 = 'The scene is large enough to contain more than 20 vehicles. So many vehicles can be added to the scene. Do not return any code or explanation; only a JSON dictionary is required.'
        q10 = 'Attention: the adjustments for one specific added vehicle should be included in one single output action. If there are multiple adjustments for one already added car, these adjustments must be merged in one action.'
        q11 = 'Attention: Do not appear information about the vehicles in the other broken actions.'
        q12 = 'The requirement is:' + user_prompt
        prompt_list = [q0, q1, q2, q3, q4, q5, q6, q7, q8, q9, q10, q11, q12]
        result = openai.ChatCompletion.create(model='gpt-4-turbo-preview', messages=[{'role': 'system', 'content': 'You are an assistant helping me to break down the operations.'}] + [{'role': 'user', 'content': q} for q in prompt_list])
        answer = result['choices'][0]['message']['content']
        print(f'{colored('[User prompt]', color='magenta', attrs=['bold'])} {user_prompt}\n')
        print(f'{colored('[Project Manager] decomposing tasks', color='magenta', attrs=['bold'])}                \n{colored('[Raw Response>>>]', attrs=['bold'])} {answer}')
        try:
            start = answer.index('{')
            answer = answer[start:]
            end = answer.rfind('}')
            answer = answer[:end + 1]
            tasks = eval(answer)
            print(f'{colored('[Extracted Response>>>]', attrs=['bold'])} {answer} \n')
        except Exception as e:
            print(e)
            traceback.print_exc()
            return 'Can not parse the requirement.'
        return tasks

    def dispatch_task(self, scene, task, tech_agents):
        """ dispatch the tasks to the corresponding chatsim.agents.
        Input:
            scene : Scene
                scene object.
            task : str
                a decomposed task, should be assigned to one/more agents
            tech_agents : dict
                a dictionary of technical agents, helping to reason the task
        Return:
            callback_message : str
                if encounter bugs, record them in callback_message to users
        """
        operation_category = {1: 'adding', 2: 'deleting', 3: 'adjusting the viewpoint', 4: 'putting back previously deleted vehicles', 5: 'operating on previously added vehicles'}
        q0 = 'I will provide you with an action, and you will help me determine which operation this action belongs to.'
        q1 = 'Operations include (1) adding (2) deleting, (3) adjusting the viewpoint, (4) putting back previously deleted vehicles, (5) operating on previously added vehicles.'
        q2 = "Return the information in JSON format, with a key named 'operation'."
        q3 = "An Example: Given action 'Remove the red car from the scene', you should return {'operation': 2}"
        q4 = "An Example: Given action 'Add a green Porsche at the location where the red car was removed', you should return {'operation': 1}"
        q5 = "An Example: Given action 'Put back the deleted white car', you should return {'operation': 4}"
        q6 = "An Example: Given action 'Move the car just added to the right by 2m', you should return {'operation': 5}"
        q7 = 'Note that you should not return any code or explanations, only provide a JSON dictionary.'
        q8 = task
        prompt_list = [q0, q1, q2, q3, q4, q5, q6, q7, q8]
        result = openai.ChatCompletion.create(model='gpt-4', messages=[{'role': 'system', 'content': 'You are an assistant helping me to classify operations.'}] + [{'role': 'user', 'content': q} for q in prompt_list])
        answer = result['choices'][0]['message']['content']
        print(f'{colored('[Project Manager] dispatching each task', color='magenta', attrs=['bold'])}                 \n{colored('[Raw Response>>>]', attrs=['bold'])} {answer}')
        start = answer.index('{')
        answer = answer[start:]
        end = answer.rfind('}')
        answer = answer[:end + 1]
        operation = eval(answer)['operation']
        print(f'{colored('[Extracted Response>>>]', attrs=['bold'])} {operation}. ({operation_category[operation]}) \n')
        if operation == 1:
            self.addition_operation(scene, task, tech_agents)
        elif operation == 2:
            self.deletion_operation(scene, task, tech_agents)
        elif operation == 3:
            self.view_adjust_operation(scene, task, tech_agents)
        elif operation == 4:
            self.put_back_deleted_operation(scene, task, tech_agents)
        elif operation == 5:
            self.revise_added_operation(scene, task, tech_agents)
        scene.past_operations.append(task)

    def addition_operation(self, scene, task, tech_agents):
        """ addition operation. 
        Participants: asset_select_agent, motion_agent

        Input:
            scene : Scene
                scene object.
            task : str
                a decomposed task, should be assigned to one/more agents
            tech_agents : dict
                a dictionary of technical agents, helping to reason the task
        Return:
            callback_message : str
                if encounter bugs, record them in callback_message to users
        """
        asset_select_agent = tech_agents['asset_select_agent']
        motion_agent = tech_agents['motion_agent']
        placement_mode = motion_agent.llm_reasoning_dependency(scene, task)
        if placement_mode['dependency'] == 0:
            placement_prior = motion_agent.llm_placement_wo_dependency(scene, task)
        else:
            valid_object_descriptors_for_cars_in_scene = ['x', 'y', 'u', 'v', 'depth', 'rgb']
            scene_object_description = {}
            for car_name, description_dict in scene.original_cars_dict.items():
                filtered_description_dict = {k: v for k, v in description_dict.items() if k in valid_object_descriptors_for_cars_in_scene}
                scene_object_description[car_name] = filtered_description_dict
            valid_object_descriptors_for_added_cars = ['color', 'type']
            for car_name, description_dict in scene.added_cars_dict.items():
                filtered_description_dict = {k: v for k, v in description_dict.items() if k in valid_object_descriptors_for_added_cars}
                filtered_description_dict['x'] = description_dict['placement_result'][0]
                filtered_description_dict['y'] = description_dict['placement_result'][1]
                filtered_description_dict['direction'] = description_dict['direction']
                scene_object_description[car_name] = filtered_description_dict
            placement_prior = motion_agent.llm_placement_w_dependency(scene, task, scene_object_description)
        asset_color_and_type = asset_select_agent.llm_selecting_asset(scene, task)
        motion_prior = motion_agent.llm_motion_planning(scene, task)
        added_car_name = scene.add_car({**asset_color_and_type, **placement_prior, **motion_prior})
        motion_agent.func_placement_and_motion_single_vehicle(scene, added_car_name)

    def deletion_operation(self, scene, task, tech_agents):
        """ deletion operation. 
        Participants: deletion_agent

        Input:
            scene : Scene
                scene object.
            task : str
                a decomposed task, should be assigned to one/more agents
            tech_agents : dict
                a dictionary of technical agents, helping to reason the task
        Return:
            callback_message : str
                if encounter bugs, record them in callback_message to users
        """
        deletion_agent = tech_agents['deletion_agent']
        valid_object_descriptors = ['u', 'v', 'depth', 'rgb']
        scene_object_description = {}
        for car_name, description_dict in scene.original_cars_dict.items():
            filtered_description_dict = {k: v for k, v in description_dict.items() if k in valid_object_descriptors}
            scene_object_description[car_name] = filtered_description_dict
        deletion_car_names = deletion_agent.llm_finding_deletion(scene, task, scene_object_description)
        for car_name in deletion_car_names:
            scene.remove_car(car_name)

    def view_adjust_operation(self, scene, task, tech_agents):
        """ view adjust operation. 
        Participants: view_adjust_agent

        Input:
            scene : Scene
                scene object.
            task : str
                a decomposed task, should be assigned to one/more agents
            tech_agents : dict
                a dictionary of technical agents, helping to reason the task
        Return:
            callback_message : str
                if encounter bugs, record them in callback_message to users
        """
        view_adjust_agent = tech_agents['view_adjust_agent']
        is_ego_motion = view_adjust_agent.llm_reasoning_ego_motion(scene, task)
        if is_ego_motion:
            start_frame_in_nerf, end_frame_in_nerf = view_adjust_agent.llm_view_motion_gen(scene, task)
            view_adjust_agent.func_generate_extrinsic(scene, start_frame_in_nerf, end_frame_in_nerf)
        else:
            delta_extrinsic = view_adjust_agent.llm_view_adjust(scene, task)
            view_adjust_agent.func_update_extrinsic(scene, delta_extrinsic)

    def put_back_deleted_operation(self, scene, task, tech_agents):
        """ put back deleted operation. 
        Participants: deletion_agent

        Input:
            scene : Scene
                scene object.
            task : str
                a decomposed task, should be assigned to one/more agents
            tech_agents : dict
                a dictionary of technical agents, helping to reason the task
        Return:
            callback_message : str
                if encounter bugs, record them in callback_message to users
        """
        deletion_agent = tech_agents['deletion_agent']
        valid_object_descriptors = ['u', 'v', 'depth', 'rgb']
        scene_object_description = {}
        for car_name, description_dict in scene.original_cars_dict.items():
            filtered_description_dict = {k: v for k, v in description_dict.items() if k in valid_object_descriptors}
            scene_object_description[car_name] = filtered_description_dict
        put_back_car_names = deletion_agent.llm_putting_back_deletion(scene, task, scene_object_description)
        for car_name in put_back_car_names:
            scene.removed_cars.remove(car_name)

    def revise_added_operation(self, scene, task, tech_agents):
        """ revised added vehicle 
        Participants: asset_select_agent, motion_agent

        Input:
            scene : Scene
                scene object.
            task : str
                a decomposed task, should be assigned to one/more agents
            tech_agents : dict
                a dictionary of technical agents, helping to reason the task
        Return:
            callback_message : str
                if encounter bugs, record them in callback_message to users
        """
        asset_select_agent = tech_agents['asset_select_agent']
        motion_agent = tech_agents['motion_agent']
        for added_car_name, added_car_info in scene.added_cars_dict.items():
            added_car_info['x'] = added_car_info['motion'][0][0]
            added_car_info['y'] = added_car_info['motion'][0][1]
        added_cars_short_dict = copy.deepcopy(scene.added_cars_dict)
        for added_car_name, added_car_info in added_cars_short_dict.items():
            added_car_info.pop('motion')
            if 'mode' in added_car_info:
                added_car_info.pop('mode')
                added_car_info.pop('distance_constraint')
                added_car_info.pop('distance_min_max')
                added_car_info.pop('need_placement_and_motion')
        modified_car_dict = asset_select_agent.llm_revise_added_cars(scene, task, added_cars_short_dict)
        for modified_car_name, modified_car_info in modified_car_dict.items():
            scene.added_cars_dict[modified_car_name]['color'] = modified_car_info['color']
            scene.added_cars_dict[modified_car_name]['type'] = modified_car_info['type']
            scene.added_cars_dict[modified_car_name]['need_placement_and_motion'] = False
            check_attributes = ['action', 'speed', 'direction', 'x', 'y']
            for attri in check_attributes:
                if scene.added_cars_dict[modified_car_name][attri] != modified_car_info[attri]:
                    scene.added_cars_dict[modified_car_name]['need_placement_and_motion'] = True
                    scene.added_cars_dict[modified_car_name][attri] = modified_car_info[attri]
            motion_agent.func_placement_and_motion_single_vehicle(scene, modified_car_name)

def deletion_operation(self, scene, task, tech_agents):
    """ deletion operation. 
        Participants: deletion_agent

        Input:
            scene : Scene
                scene object.
            task : str
                a decomposed task, should be assigned to one/more agents
            tech_agents : dict
                a dictionary of technical agents, helping to reason the task
        Return:
            callback_message : str
                if encounter bugs, record them in callback_message to users
        """
    deletion_agent = tech_agents['deletion_agent']
    valid_object_descriptors = ['u', 'v', 'depth', 'rgb']
    scene_object_description = {}
    for car_name, description_dict in scene.original_cars_dict.items():
        filtered_description_dict = {k: v for k, v in description_dict.items() if k in valid_object_descriptors}
        scene_object_description[car_name] = filtered_description_dict
    deletion_car_names = deletion_agent.llm_finding_deletion(scene, task, scene_object_description)
    for car_name in deletion_car_names:
        scene.remove_car(car_name)

class materialed_meshes:
    """
    If the obj have mulitple meshes and materials, it will build a scene.
    And seperate meshes by material.

    Dump all meshes and concatenate them is a good way to accelerate ray-mesh intersection.
    But we need to record each vertex belongs which material. 
    """

    def __init__(self, obj_path):
        scene = trimesh.load(obj_path, force='scene')
        self.scene_dump = scene.dump()
        self.mesh_all = scene.dump(concatenate=True)
        self.vertex_cnt = [mesh.vertices.shape[0] for mesh in self.scene_dump]
        self.face_cnt = [mesh.faces.shape[0] for mesh in self.scene_dump]
        self.vertex_accu = list(itertools.accumulate(self.vertex_cnt))
        self.face_accu = list(itertools.accumulate(self.face_cnt))

    def find_material_and_idx(self, accu_list, idx):
        material_idx = np.searchsorted(accu_list, idx, side='right')
        local_idx = idx - accu_list[material_idx]
        return (material_idx, local_idx)

    def get_material_from_face_idx_of_all(self, face_idx_in_all):
        """
            face_idx_in_all:
                face idx in self.mesh_all.faces
        """
        material_idx, local_idx = self.find_material_and_idx(self.face_accu, face_idx_in_all)
        mesh = self.scene_dump[material_idx]
        face_local = mesh.faces[local_idx]
        uv_local = mesh.visual.uv[face_local]
        material = mesh.visual.material
        material.kwargs['name'] = mesh.metadata['name']
        return (material, face_local, uv_local)

    def get_all_meshes(self):
        return self.mesh_all

def find_material_and_idx(self, accu_list, idx):
    material_idx = np.searchsorted(accu_list, idx, side='right')
    local_idx = idx - accu_list[material_idx]
    return (material_idx, local_idx)

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

def IBL(self, light_dir):
    """
        transform light_dir in world coord to envmap coor. hand-crafted
        """
    light_dir_np = light_dir.cpu().numpy()
    light_dir_envmap = [-light_dir_np[1], light_dir_np[2], -light_dir_np[0]]
    uu, vv = self.env.world2pixel(light_dir_envmap[0], light_dir_envmap[1], light_dir_envmap[2])
    light_intensity = torch.tensor(self.env.data[vv, uu], device='cuda', dtype=torch.float32)
    return light_intensity

class UE4BRDF:

    def __init__(self, base_color, metallic, roughness, specular):
        self.base_color = torch.tensor(base_color, dtype=torch.float64).cuda()
        self.base_color = srgb_inv_gamma_correction_torch(self.base_color)
        self.metallic = torch.tensor(metallic, dtype=torch.float64).cuda()
        self.roughness = torch.tensor(roughness, dtype=torch.float64).cuda().clamp(min=0.0001)
        self.specular = torch.tensor(specular, dtype=torch.float64).cuda()
        self.c_diffuse = (1 - self.metallic) * self.base_color
        self.c_specular = (1 - self.metallic) * self.specular + self.metallic * self.base_color

    def lambertian_diffuse(self):
        return self.c_diffuse / np.pi

    def fresnel_schlick(self, h_dot_v):
        return self.c_specular + (1 - self.c_specular) * torch.pow(1 - h_dot_v, 5).repeat_interleave(3, dim=-1)

    def smith_g1(self, n_dot_v):
        k = pow(self.roughness + 1, 2) / 8
        return n_dot_v / (n_dot_v * (1 - k) + k)

    def geometry(self, n_dot_v, n_dot_l):
        return self.smith_g1(n_dot_v) * self.smith_g1(n_dot_l)

    def normal_distribution(self, n, h):
        roughness = pow(self.roughness, 2)
        n_cross_h = torch.cross(n, h, dim=1)
        n_dot_h = torch.einsum('ij,ij->i', n, h).unsqueeze(-1)
        a = n_dot_h * roughness
        k = roughness / (torch.einsum('ij,ij->i', n_cross_h, n_cross_h).unsqueeze(-1) + a * a)
        d = k * k * (1 / np.pi)
        return d

    def evaluate(self, normal, light_dir, view_dir):
        n_dot_l = torch.clamp(torch.dot(normal, light_dir), min=1e-05)
        n_dot_v = torch.clamp(torch.dot(normal, view_dir), min=1e-05)
        half_dir = (light_dir + view_dir) / torch.norm(light_dir + view_dir)
        h_dot_v = torch.clamp(torch.dot(half_dir, view_dir), min=1e-05)
        n_dot_h = torch.clamp(torch.dot(normal, half_dir), min=1e-05)
        diffuse_term = self.lambertian_diffuse()
        specular_term = self.fresnel_schlick(h_dot_v) * self.geometry(n_dot_l, n_dot_v) * self.normal_distribution(normal, half_dir) / (4 * n_dot_l * n_dot_v)
        return diffuse_term + specular_term

    def evaluate_parallel(self, normal, light_dir, view_dir):
        """
        Args:
            normal: [num_samples, 3]
            light_dir: [num_samples, 3]
            view_dir: [num_samples]
        """
        normal = normal.double()
        light_dir = light_dir.double()
        view_dir = view_dir.double()
        num_samples = normal.shape[0]
        n_dot_l = torch.clamp(torch.einsum('ij,ij->i', normal, light_dir).unsqueeze(-1), min=1e-05)
        n_dot_v = torch.clamp(torch.einsum('ij,ij->i', normal, view_dir).unsqueeze(-1), min=1e-05)
        half_dir = (light_dir + view_dir) / torch.norm(light_dir + view_dir, p=2, dim=1, keepdim=True)
        h_dot_v = torch.clamp(torch.einsum('ij,ij->i', half_dir, view_dir).unsqueeze(-1), min=1e-05)
        diffuse_term = self.lambertian_diffuse().expand(num_samples, 3)
        specular_term = self.fresnel_schlick(h_dot_v) * self.geometry(n_dot_l, n_dot_v) * self.normal_distribution(normal, half_dir) / (4 * n_dot_l * n_dot_v)
        brdf = diffuse_term + specular_term
        return brdf.float()

def fresnel_schlick(self, h_dot_v):
    return self.c_specular + (1 - self.c_specular) * torch.pow(1 - h_dot_v, 5).repeat_interleave(3, dim=-1)

def smith_g1(self, n_dot_v):
    k = pow(self.roughness + 1, 2) / 8
    return n_dot_v / (n_dot_v * (1 - k) + k)

def rename_material_dict(old_dict):
    new_dict = OrderedDict()
    new_dict['ks'] = old_dict['ks']
    if 'kd' in old_dict:
        new_dict['kd'] = old_dict['kd']
    for key in ['pm', 'pr']:
        if isinstance(old_dict[key], list):
            new_dict[key] = eval(old_dict[key][0])
        else:
            new_dict[key] = eval(old_dict[key])
    return new_dict

class LogEncodedL2Loss(nn.Module):

    def __init__(self, args):
        super(LogEncodedL2Loss, self).__init__()
        self.weight = args['weight']

    def forward(self, pred, target, mask=None):
        loss_map = torch.pow(torch.log(pred + 1 + eps) - torch.log(target + 1 + eps), 2)
        if mask is not None:
            loss = (loss_map * mask).sum() / mask.sum()
        else:
            loss = loss_map.mean()
        return loss * self.weight

def forward(self, pred, target, mask=None):
    loss_map = torch.pow(torch.log(pred + 1 + eps) - torch.log(target + 1 + eps), 2)
    if mask is not None:
        loss = (loss_map * mask).sum() / mask.sum()
    else:
        loss = loss_map.mean()
    return loss * self.weight

class L2Loss(nn.Module):

    def __init__(self, args):
        super(L2Loss, self).__init__()
        self.weight = args['weight']

    def forward(self, pred, target, mask=None):
        loss_map = torch.pow(pred - target, 2)
        if mask is not None:
            loss = (loss_map * mask).sum() / mask.sum()
        else:
            loss = loss_map.mean()
        return loss * self.weight

def forward(self, pred, target, mask=None):
    loss_map = torch.pow(pred - target, 2)
    if mask is not None:
        loss = (loss_map * mask).sum() / mask.sum()
    else:
        loss = loss_map.mean()
    return loss * self.weight

def render_scene(output_dir, intrinsic, model_obj_names, render_downsample, depth_and_occlusion):
    set_render_params(intrinsic['H'], intrinsic['W'], render_downsample)
    node_tree = set_composite_node(output_dir, render_downsample, depth_and_occlusion)
    objects_corners = dict()
    for model_obj_name in model_obj_names:
        model = bpy.data.objects[model_obj_name]
        model.hide_render = False
        position = model.location
        model.rotation_mode = 'QUATERNION'
        rotation_quat = model.rotation_quaternion
        obj2world = pyquaternion.Quaternion(rotation_quat).transformation_matrix
        obj2world[:3, 3] = position
        dimension = model.dimensions
        corner_in_obj = create_bbx([dimension[0] / 2, dimension[1] / 2, dimension[2] / 2])
        corner_in_obj[:, -1] += dimension[2] / 2
        corner_in_obj_homo = np.hstack([corner_in_obj, np.ones((corner_in_obj.shape[0], 1))])
        corner_in_world_homo = (obj2world @ corner_in_obj_homo.T).T
        corner_in_world = corner_in_world_homo[:, :3]
        objects_corners[model_obj_name] = {'world_8_corners': corner_in_world.tolist()}
    save_yaml(objects_corners, os.path.join(output_dir, 'label.yaml'))
    bpy.ops.render.render()

def chat(system, user_assistant):
    assert isinstance(system, str), '`system` should be a string'
    assert isinstance(user_assistant, list), '`user_assistant` should be a list'
    system_msg = [{'role': 'system', 'content': system}]
    user_assistant_msgs = [{'role': 'assistant', 'content': user_assistant[i]} if i % 2 else {'role': 'user', 'content': user_assistant[i]} for i in range(len(user_assistant))]
    msgs = system_msg + user_assistant_msgs
    response = openai.ChatCompletion.create(model='gpt-4', messages=msgs)
    return response['choices'][0]['message']['content']

