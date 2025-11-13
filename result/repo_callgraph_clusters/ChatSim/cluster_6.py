# Cluster 6

def invert_transformation(rot, t):
    t = np.matmul(-rot.T, t)
    inv_translation = np.concatenate([rot.T, t[:, None]], axis=1)
    return np.concatenate([inv_translation, np.array([[0.0, 0.0, 0.0, 1.0]])])

def invert_transformation(rot, t):
    t = np.matmul(-rot.T, t)
    inv_translation = np.concatenate([rot.T, t[:, None]], axis=1)
    return np.concatenate([inv_translation, np.array([[0.0, 0.0, 0.0, 1.0]])])

def save_poses(basedir, poses, pts3d, perm):
    pts_arr = []
    vis_arr = []
    for k in pts3d:
        pts_arr.append(pts3d[k].xyz)
        cams = [0] * poses.shape[-1]
        for ind in pts3d[k].image_ids:
            if len(cams) < ind - 1:
                print('ERROR: the correct camera poses for current points cannot be accessed')
                return
            cams[ind - 1] = 1
        vis_arr.append(cams)
    pts_arr = np.array(pts_arr)
    vis_arr = np.array(vis_arr)
    print('Points', pts_arr.shape, 'Visibility', vis_arr.shape)
    pcd = trimesh.PointCloud(pts_arr)
    pcd.export(os.path.join(basedir, 'sparse_cloud.ply'))
    os.makedirs(os.path.join(basedir, 'view_cloud'), exist_ok=True)
    for i in perm:
        vis = vis_arr[:, i]
        pts = pts_arr[vis == 1]
        pcd = trimesh.PointCloud(pts)
        pcd.export(os.path.join(basedir, 'view_cloud', '{}.ply'.format(i)))
    zvals = np.sum(-(pts_arr[:, np.newaxis, :].transpose([2, 0, 1]) - poses[:3, 3:4, :]) * poses[:3, 2:3, :], 0)
    valid_z = zvals[vis_arr == 1]
    print('Depth stats', valid_z.min(), valid_z.max(), valid_z.mean())
    save_arr = []
    out_vis_arr = np.zeros([vis_arr.shape[0], vis_arr.shape[1]], dtype=np.uint8)
    for j, i in enumerate(perm):
        vis = vis_arr[:, i]
        out_vis_arr[:, j] = vis.astype(np.uint8)
        zs = zvals[:, i]
        zs = zs[vis == 1]
        close_depth, inf_depth = (np.percentile(zs, 0.1), np.percentile(zs, 99.9))
        save_arr.append(np.concatenate([poses[..., i].ravel(), np.array([close_depth, inf_depth])], 0))
    save_arr = np.array(save_arr)
    cover_ratio = out_vis_arr.astype(np.float32).sum(-1)
    cover_ratio = np.clip(cover_ratio / 10, 0.0, 1.0)
    pcd_color = np.stack([cover_ratio, 1 - cover_ratio, cover_ratio], -1)
    pcd = trimesh.PointCloud(pts_arr, pcd_color)
    pcd.export(os.path.join(basedir, 'sparse_cloud_cover_vis.ply'))
    np.save(os.path.join(basedir, 'poses_bounds.npy'), save_arr)
    np.save(os.path.join(basedir, 'visibility.npy'), out_vis_arr)

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

def build_covariance_from_scaling_rotation(scaling, scaling_modifier, rotation):
    L = build_scaling_rotation(scaling_modifier * scaling, rotation)
    actual_covariance = L @ L.transpose(1, 2)
    symm = strip_symmetric(actual_covariance)
    return symm

def build_lama_model(config_p: str, ckpt_p: str, device='cuda'):
    predict_config = OmegaConf.load(config_p)
    predict_config.model.path = ckpt_p
    device = torch.device(device)
    train_config_path = os.path.join(predict_config.model.path, 'config.yaml')
    with open(train_config_path, 'r') as f:
        train_config = OmegaConf.create(yaml.safe_load(f))
    train_config.training_model.predict_only = True
    train_config.visualizer.kind = 'noop'
    checkpoint_path = os.path.join(predict_config.model.path, 'models', predict_config.model.checkpoint)
    model = load_checkpoint(train_config, checkpoint_path, strict=False)
    model.to(device)
    model.freeze()
    return model

def get_ref_index(length, sample_length):
    if random.uniform(0, 1) > 0.5:
        ref_index = random.sample(range(length), sample_length)
        ref_index.sort()
    else:
        pivot = random.randint(0, length - sample_length)
        ref_index = [pivot + i for i in range(sample_length)]
    return ref_index

class GroupRandomHorizontalFlip(object):
    """Randomly horizontally flips the given PIL.Image with a probability of 0.5
    """

    def __init__(self, is_flow=False):
        self.is_flow = is_flow

    def __call__(self, img_group, is_flow=False):
        v = random.random()
        if v < 0.5:
            ret = [img.transpose(Image.FLIP_LEFT_RIGHT) for img in img_group]
            if self.is_flow:
                for i in range(0, len(ret), 2):
                    ret[i] = ImageOps.invert(ret[i])
            return ret
        else:
            return img_group

def __call__(self, img_group, is_flow=False):
    v = random.random()
    if v < 0.5:
        ret = [img.transpose(Image.FLIP_LEFT_RIGHT) for img in img_group]
        if self.is_flow:
            for i in range(0, len(ret), 2):
                ret[i] = ImageOps.invert(ret[i])
        return ret
    else:
        return img_group

def create_random_shape_with_random_motion(video_length, imageHeight=240, imageWidth=432):
    height = random.randint(imageHeight // 3, imageHeight - 1)
    width = random.randint(imageWidth // 3, imageWidth - 1)
    edge_num = random.randint(6, 8)
    ratio = random.randint(6, 8) / 10
    region = get_random_shape(edge_num=edge_num, ratio=ratio, height=height, width=width)
    region_width, region_height = region.size
    x, y = (random.randint(0, imageHeight - region_height), random.randint(0, imageWidth - region_width))
    velocity = get_random_velocity(max_speed=3)
    m = Image.fromarray(np.zeros((imageHeight, imageWidth)).astype(np.uint8))
    m.paste(region, (y, x, y + region.size[0], x + region.size[1]))
    masks = [m.convert('L')]
    if random.uniform(0, 1) > 0.5:
        return masks * video_length
    for _ in range(video_length - 1):
        x, y, velocity = random_move_control_points(x, y, imageHeight, imageWidth, velocity, region.size, maxLineAcceleration=(3, 0.5), maxInitSpeed=3)
        m = Image.fromarray(np.zeros((imageHeight, imageWidth)).astype(np.uint8))
        m.paste(region, (y, x, y + region.size[0], x + region.size[1]))
        masks.append(m.convert('L'))
    return masks

def random_accelerate(velocity, maxAcceleration, dist='uniform'):
    speed, angle = velocity
    d_speed, d_angle = maxAcceleration
    if dist == 'uniform':
        speed += np.random.uniform(-d_speed, d_speed)
        angle += np.random.uniform(-d_angle, d_angle)
    elif dist == 'guassian':
        speed += np.random.normal(0, d_speed / 2)
        angle += np.random.normal(0, d_angle / 2)
    else:
        raise NotImplementedError(f'Distribution type {dist} is not supported.')
    return (speed, angle)

def get_random_velocity(max_speed=3, dist='uniform'):
    if dist == 'uniform':
        speed = np.random.uniform(max_speed)
    elif dist == 'guassian':
        speed = np.abs(np.random.normal(0, max_speed / 2))
    else:
        raise NotImplementedError(f'Distribution type {dist} is not supported.')
    angle = np.random.uniform(0, 2 * np.pi)
    return (speed, angle)

def build_point_grid(n_per_side: int) -> np.ndarray:
    """Generates a 2D grid of points evenly spaced in [0,1]x[0,1]."""
    offset = 1 / (2 * n_per_side)
    points_one_side = np.linspace(offset, 1 - offset, n_per_side)
    points_x = np.tile(points_one_side[None, :], (n_per_side, 1))
    points_y = np.tile(points_one_side[:, None], (1, n_per_side))
    points = np.stack([points_x, points_y], axis=-1).reshape(-1, 2)
    return points

def dilate_mask(mask, dilate_factor=15):
    mask = mask.astype(np.uint8)
    mask = cv2.dilate(mask, np.ones((dilate_factor, dilate_factor), np.uint8), iterations=1)
    return mask

def erode_mask(mask, dilate_factor=15):
    mask = mask.astype(np.uint8)
    mask = cv2.erode(mask, np.ones((dilate_factor, dilate_factor), np.uint8), iterations=1)
    return mask

def show_mask(ax, mask: np.ndarray, random_color=False):
    mask = mask.astype(np.uint8)
    if np.max(mask) == 255:
        mask = mask / 255
    if random_color:
        color = np.concatenate([np.random.random(3), np.array([0.6])], axis=0)
    else:
        color = np.array([30 / 255, 144 / 255, 255 / 255, 0.6])
    h, w = mask.shape[-2:]
    mask_img = mask.reshape(h, w, 1) * color.reshape(1, 1, -1)
    ax.imshow(mask_img)

def resize_and_pad(image: np.ndarray, mask: np.ndarray, target_size: int=512) -> Tuple[np.ndarray, np.ndarray]:
    """
    Resizes an image and its corresponding mask to have the longer side equal to `target_size` and pads them to make them
    both have the same size. The resulting image and mask have dimensions (target_size, target_size).

    Args:
        image: A numpy array representing the image to resize and pad.
        mask: A numpy array representing the mask to resize and pad.
        target_size: An integer specifying the desired size of the longer side after resizing.

    Returns:
        A tuple containing two numpy arrays - the resized and padded image and the resized and padded mask.
    """
    height, width, _ = image.shape
    max_dim = max(height, width)
    scale = target_size / max_dim
    new_height = int(height * scale)
    new_width = int(width * scale)
    image_resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
    mask_resized = cv2.resize(mask, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
    pad_height = target_size - new_height
    pad_width = target_size - new_width
    top_pad = pad_height // 2
    bottom_pad = pad_height - top_pad
    left_pad = pad_width // 2
    right_pad = pad_width - left_pad
    image_padded = np.pad(image_resized, ((top_pad, bottom_pad), (left_pad, right_pad), (0, 0)), mode='constant')
    mask_padded = np.pad(mask_resized, ((top_pad, bottom_pad), (left_pad, right_pad)), mode='constant')
    return (image_padded, mask_padded, (top_pad, bottom_pad, left_pad, right_pad))

def recover_size(image_padded: np.ndarray, mask_padded: np.ndarray, orig_size: Tuple[int, int], padding_factors: Tuple[int, int, int, int]) -> Tuple[np.ndarray, np.ndarray]:
    """
    Resizes a padded and resized image and mask to the original size.

    Args:
        image_padded: A numpy array representing the padded and resized image.
        mask_padded: A numpy array representing the padded and resized mask.
        orig_size: A tuple containing two integers - the original height and width of the image before resizing and padding.

    Returns:
        A tuple containing two numpy arrays - the recovered image and the recovered mask with dimensions `orig_size`.
    """
    h, w, c = image_padded.shape
    top_pad, bottom_pad, left_pad, right_pad = padding_factors
    image = image_padded[top_pad:h - bottom_pad, left_pad:w - right_pad, :]
    mask = mask_padded[top_pad:h - bottom_pad, left_pad:w - right_pad]
    image_resized = cv2.resize(image, orig_size[::-1], interpolation=cv2.INTER_LINEAR)
    mask_resized = cv2.resize(mask, orig_size[::-1], interpolation=cv2.INTER_LINEAR)
    return (image_resized, mask_resized)

def save_mask_for_sidebyside(item, out_file):
    mask = item['mask']
    if mask.ndim == 3:
        mask = mask[0]
    mask = np.clip(mask * 255, 0, 255).astype('uint8')
    io.imsave(out_file, mask)

def save_img_for_sidebyside(item, out_file):
    img = np.transpose(item['image'], (1, 2, 0))
    img = np.clip(img * 255, 0, 255).astype('uint8')
    io.imsave(out_file, img)

def save_masked_img_for_sidebyside(item, out_file):
    mask = item['mask']
    img = item['image']
    img = (1 - mask) * img + mask
    img = np.transpose(img, (1, 2, 0))
    img = np.clip(img * 255, 0, 255).astype('uint8')
    io.imsave(out_file, img)

def draw_score(img, score):
    img = np.transpose(img, (1, 2, 0))
    cv2.putText(img, f'{score:.2f}', (40, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 1, 0), thickness=3)
    img = np.transpose(img, (2, 0, 1))
    return img

def save_global_samples(global_mask_fnames, mask2real_fname, mask2fake_fname, out_dir, real_scores_by_fname, fake_scores_by_fname):
    for cur_mask_fname in global_mask_fnames:
        cur_real_fname = mask2real_fname[cur_mask_fname]
        orig_img = load_image(cur_real_fname, mode='RGB')
        fake_img = load_image(mask2fake_fname[cur_mask_fname], mode='RGB')[:, :orig_img.shape[1], :orig_img.shape[2]]
        mask = load_image(cur_mask_fname, mode='L')[None, ...]
        draw_score(orig_img, real_scores_by_fname.loc[cur_real_fname, 'real_score'])
        draw_score(fake_img, fake_scores_by_fname.loc[cur_mask_fname, 'fake_score'])
        cur_grid = visualize_mask_and_images(dict(image=orig_img, mask=mask, fake=fake_img), keys=['image', 'fake'], last_without_mask=True)
        cur_grid = np.clip(cur_grid * 255, 0, 255).astype('uint8')
        cur_grid = cv2.cvtColor(cur_grid, cv2.COLOR_RGB2BGR)
        cv2.imwrite(os.path.join(out_dir, os.path.splitext(os.path.basename(cur_mask_fname))[0] + '.jpg'), cur_grid)

def save_samples_by_real(worst_best_by_real, mask2fake_fname, fake_info, out_dir):
    for real_fname in worst_best_by_real.index:
        worst_mask_path = worst_best_by_real.loc[real_fname, 'worst']
        best_mask_path = worst_best_by_real.loc[real_fname, 'best']
        orig_img = load_image(real_fname, mode='RGB')
        worst_mask_img = load_image(worst_mask_path, mode='L')[None, ...]
        worst_fake_img = load_image(mask2fake_fname[worst_mask_path], mode='RGB')[:, :orig_img.shape[1], :orig_img.shape[2]]
        best_mask_img = load_image(best_mask_path, mode='L')[None, ...]
        best_fake_img = load_image(mask2fake_fname[best_mask_path], mode='RGB')[:, :orig_img.shape[1], :orig_img.shape[2]]
        draw_score(orig_img, worst_best_by_real.loc[real_fname, 'real_score'])
        draw_score(worst_fake_img, worst_best_by_real.loc[real_fname, 'worst_score'])
        draw_score(best_fake_img, worst_best_by_real.loc[real_fname, 'best_score'])
        cur_grid = visualize_mask_and_images(dict(image=orig_img, mask=np.zeros_like(worst_mask_img), worst_mask=worst_mask_img, worst_img=worst_fake_img, best_mask=best_mask_img, best_img=best_fake_img), keys=['image', 'worst_mask', 'worst_img', 'best_mask', 'best_img'], rescale_keys=['worst_mask', 'best_mask'], last_without_mask=True)
        cur_grid = np.clip(cur_grid * 255, 0, 255).astype('uint8')
        cur_grid = cv2.cvtColor(cur_grid, cv2.COLOR_RGB2BGR)
        cv2.imwrite(os.path.join(out_dir, os.path.splitext(os.path.basename(real_fname))[0] + '.jpg'), cur_grid)
        fig, (ax1, ax2) = plt.subplots(1, 2)
        cur_stat = fake_info[fake_info['real_fname'] == real_fname]
        cur_stat['fake_score'].hist(ax=ax1)
        cur_stat['real_score'].hist(ax=ax2)
        fig.tight_layout()
        fig.savefig(os.path.join(out_dir, os.path.splitext(os.path.basename(real_fname))[0] + '_scores.png'))
        plt.close(fig)

def main(args):
    config = load_yaml(args.config)
    datasets = [PrecomputedInpaintingResultsDataset(args.datadir, cur_predictdir, **config.dataset_kwargs) for cur_predictdir in args.predictdirs]
    assert len({len(ds) for ds in datasets}) == 1
    len_first = len(datasets[0])
    indices = list(range(len_first))
    if len_first > args.max_n:
        indices = sorted(random.sample(indices, args.max_n))
    os.makedirs(args.outpath, exist_ok=True)
    filename2i = {}
    keys = ['image'] + [i for i in range(len(datasets))]
    for img_i in indices:
        try:
            mask_fname = os.path.basename(datasets[0].mask_filenames[img_i])
            if mask_fname in filename2i:
                filename2i[mask_fname] += 1
                idx = filename2i[mask_fname]
                mask_fname_only, ext = os.path.split(mask_fname)
                mask_fname = f'{mask_fname_only}_{idx}{ext}'
            else:
                filename2i[mask_fname] = 1
            cur_vis_dict = datasets[0][img_i]
            for ds_i, ds in enumerate(datasets):
                cur_vis_dict[ds_i] = ds[img_i]['inpainted']
            vis_img = visualize_mask_and_images(cur_vis_dict, keys, last_without_mask=False, mask_only_first=True, black_mask=args.black)
            vis_img = np.clip(vis_img * 255, 0, 255).astype('uint8')
            out_fname = os.path.join(args.outpath, mask_fname)
            vis_img = cv2.cvtColor(vis_img, cv2.COLOR_RGB2BGR)
            cv2.imwrite(out_fname, vis_img)
        except Exception as ex:
            print(f'Could not process {img_i} due to {ex}')

def process_images(src_images, indir, outdir, config):
    if config.generator_kind == 'segmentation':
        mask_generator = SegmentationMask(**config.mask_generator_kwargs)
    elif config.generator_kind == 'random':
        mask_generator_kwargs = OmegaConf.to_container(config.mask_generator_kwargs, resolve=True)
        variants_n = mask_generator_kwargs.pop('variants_n', 2)
        mask_generator = MakeManyMasksWrapper(MixedMaskGenerator(**mask_generator_kwargs), variants_n=variants_n)
    else:
        raise ValueError(f'Unexpected generator kind: {config.generator_kind}')
    max_tamper_area = config.get('max_tamper_area', 1)
    for infile in src_images:
        try:
            file_relpath = infile[len(indir):]
            img_outpath = os.path.join(outdir, file_relpath)
            os.makedirs(os.path.dirname(img_outpath), exist_ok=True)
            image = Image.open(infile).convert('RGB')
            if min(image.size) < config.cropping.out_min_size:
                handle_small_mode = SmallMode(config.cropping.handle_small_mode)
                if handle_small_mode == SmallMode.DROP:
                    continue
                elif handle_small_mode == SmallMode.UPSCALE:
                    factor = config.cropping.out_min_size / min(image.size)
                    out_size = (np.array(image.size) * factor).round().astype('uint32')
                    image = image.resize(out_size, resample=Image.BICUBIC)
            else:
                factor = config.cropping.out_min_size / min(image.size)
                out_size = (np.array(image.size) * factor).round().astype('uint32')
                image = image.resize(out_size, resample=Image.BICUBIC)
            src_masks = mask_generator.get_masks(image)
            filtered_image_mask_pairs = []
            for cur_mask in src_masks:
                if config.cropping.out_square_crop:
                    crop_left, crop_top, crop_right, crop_bottom = propose_random_square_crop(cur_mask, min_overlap=config.cropping.crop_min_overlap)
                    cur_mask = cur_mask[crop_top:crop_bottom, crop_left:crop_right]
                    cur_image = image.copy().crop((crop_left, crop_top, crop_right, crop_bottom))
                else:
                    cur_image = image
                if len(np.unique(cur_mask)) == 0 or cur_mask.mean() > max_tamper_area:
                    continue
                filtered_image_mask_pairs.append((cur_image, cur_mask))
            mask_indices = np.random.choice(len(filtered_image_mask_pairs), size=min(len(filtered_image_mask_pairs), config.max_masks_per_image), replace=False)
            mask_basename = os.path.join(outdir, os.path.splitext(file_relpath)[0])
            for i, idx in enumerate(mask_indices):
                cur_image, cur_mask = filtered_image_mask_pairs[idx]
                cur_basename = mask_basename + f'_crop{i:03d}'
                Image.fromarray(np.clip(cur_mask * 255, 0, 255).astype('uint8'), mode='L').save(cur_basename + f'_mask{i:03d}.png')
                cur_image.save(cur_basename + '.png')
        except KeyboardInterrupt:
            return
        except Exception as ex:
            print(f'Could not make masks for {infile} due to {ex}:\n{traceback.format_exc()}')

@hydra.main(config_path='../configs/prediction', config_name='default_inner_features.yaml')
def main(predict_config: OmegaConf):
    try:
        register_debug_signal_handlers()
        device = torch.device(predict_config.device)
        train_config_path = os.path.join(predict_config.model.path, 'config.yaml')
        with open(train_config_path, 'r') as f:
            train_config = OmegaConf.create(yaml.safe_load(f))
        checkpoint_path = os.path.join(predict_config.model.path, 'models', predict_config.model.checkpoint)
        model = load_checkpoint(train_config, checkpoint_path, strict=False)
        model.freeze()
        model.to(device)
        assert isinstance(model, DefaultInpaintingTrainingModule), 'Only DefaultInpaintingTrainingModule is supported'
        assert isinstance(getattr(model.generator, 'model', None), torch.nn.Sequential)
        if not predict_config.indir.endswith('/'):
            predict_config.indir += '/'
        dataset = make_default_val_dataset(predict_config.indir, **predict_config.dataset)
        max_level = max(predict_config.levels)
        with torch.no_grad():
            for img_i in tqdm.trange(len(dataset)):
                mask_fname = dataset.mask_filenames[img_i]
                cur_out_fname = os.path.join(predict_config.outdir, os.path.splitext(mask_fname[len(predict_config.indir):])[0])
                os.makedirs(os.path.dirname(cur_out_fname), exist_ok=True)
                batch = move_to_device(default_collate([dataset[img_i]]), device)
                img = batch['image']
                mask = batch['mask']
                mask[:] = 0
                mask_h, mask_w = mask.shape[-2:]
                mask[:, :, mask_h // 2 - predict_config.hole_radius:mask_h // 2 + predict_config.hole_radius, mask_w // 2 - predict_config.hole_radius:mask_w // 2 + predict_config.hole_radius] = 1
                masked_img = torch.cat([img * (1 - mask), mask], dim=1)
                feats = masked_img
                for level_i, level in enumerate(model.generator.model):
                    feats = level(feats)
                    if level_i in predict_config.levels:
                        cur_feats = torch.cat([f for f in feats if torch.is_tensor(f)], dim=1) if isinstance(feats, tuple) else feats
                        if predict_config.slice_channels:
                            cur_feats = cur_feats[:, slice(*predict_config.slice_channels)]
                        cur_feat = cur_feats.pow(2).mean(1).pow(0.5).clone()
                        cur_feat -= cur_feat.min()
                        cur_feat /= cur_feat.std()
                        cur_feat = cur_feat.clamp(0, 1) / 1
                        cur_feat = cur_feat.cpu().numpy()[0]
                        cur_feat *= 255
                        cur_feat = np.clip(cur_feat, 0, 255).astype('uint8')
                        cv2.imwrite(cur_out_fname + f'_lev{level_i:02d}_norm.png', cur_feat)
                    elif level_i >= max_level:
                        break
    except KeyboardInterrupt:
        LOGGER.warning('Interrupted by user')
    except Exception as ex:
        LOGGER.critical(f'Prediction failed due to {ex}:\n{traceback.format_exc()}')
        sys.exit(1)

def main(args):
    try:
        if not args.indir.endswith('/'):
            args.indir += '/'
        for in_img in glob.glob(os.path.join(args.indir, '**', '*' + args.img_suffix), recursive=True):
            if 'mask' in os.path.basename(in_img):
                continue
            out_img_path = os.path.join(args.outdir, os.path.splitext(in_img[len(args.indir):])[0] + '.png')
            out_mask_path = f'{os.path.splitext(out_img_path)[0]}_mask.png'
            os.makedirs(os.path.dirname(out_img_path), exist_ok=True)
            img = load_image(in_img)
            height, width = img.shape[1:]
            pad_h, pad_w = (int(height * args.coef / 2), int(width * args.coef / 2))
            mask = np.zeros((height, width), dtype='uint8')
            if args.expand:
                img = np.pad(img, ((0, 0), (pad_h, pad_h), (pad_w, pad_w)))
                mask = np.pad(mask, ((pad_h, pad_h), (pad_w, pad_w)), mode='constant', constant_values=255)
            else:
                mask[:pad_h] = 255
                mask[-pad_h:] = 255
                mask[:, :pad_w] = 255
                mask[:, -pad_w:] = 255
            img = np.clip(np.transpose(img, (1, 2, 0)) * 255, 0, 255).astype('uint8')
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            cv2.imwrite(out_img_path, img)
            cv2.imwrite(out_mask_path, mask)
    except KeyboardInterrupt:
        LOGGER.warning('Interrupted by user')
    except Exception as ex:
        LOGGER.critical(f'Prediction failed due to {ex}:\n{traceback.format_exc()}')
        sys.exit(1)

@hydra.main(config_path='../configs/prediction', config_name='default.yaml')
def main(predict_config: OmegaConf):
    try:
        register_debug_signal_handlers()
        device = torch.device(predict_config.device)
        train_config_path = os.path.join(predict_config.model.path, 'config.yaml')
        with open(train_config_path, 'r') as f:
            train_config = OmegaConf.create(yaml.safe_load(f))
        train_config.training_model.predict_only = True
        train_config.visualizer.kind = 'noop'
        out_ext = predict_config.get('out_ext', '.png')
        checkpoint_path = os.path.join(predict_config.model.path, 'models', predict_config.model.checkpoint)
        model = load_checkpoint(train_config, checkpoint_path, strict=False, map_location='cpu')
        model.freeze()
        if not predict_config.get('refine', False):
            model.to(device)
        if not predict_config.indir.endswith('/'):
            predict_config.indir += '/'
        dataset = make_default_val_dataset(predict_config.indir, **predict_config.dataset)
        for img_i in tqdm.trange(len(dataset)):
            mask_fname = dataset.mask_filenames[img_i]
            cur_out_fname = os.path.join(predict_config.outdir, os.path.splitext(mask_fname[len(predict_config.indir):])[0] + out_ext)
            os.makedirs(os.path.dirname(cur_out_fname), exist_ok=True)
            batch = default_collate([dataset[img_i]])
            if predict_config.get('refine', False):
                assert 'unpad_to_size' in batch, 'Unpadded size is required for the refinement'
                cur_res = refine_predict(batch, model, **predict_config.refiner)
                cur_res = cur_res[0].permute(1, 2, 0).detach().cpu().numpy()
            else:
                with torch.no_grad():
                    batch = move_to_device(batch, device)
                    batch['mask'] = (batch['mask'] > 0) * 1
                    batch = model(batch)
                    cur_res = batch[predict_config.out_key][0].permute(1, 2, 0).detach().cpu().numpy()
                    unpad_to_size = batch.get('unpad_to_size', None)
                    if unpad_to_size is not None:
                        orig_height, orig_width = unpad_to_size
                        cur_res = cur_res[:orig_height, :orig_width]
            cur_res = np.clip(cur_res * 255, 0, 255).astype('uint8')
            cur_res = cv2.cvtColor(cur_res, cv2.COLOR_RGB2BGR)
            cv2.imwrite(cur_out_fname, cur_res)
    except KeyboardInterrupt:
        LOGGER.warning('Interrupted by user')
    except Exception as ex:
        LOGGER.critical(f'Prediction failed due to {ex}:\n{traceback.format_exc()}')
        sys.exit(1)

def main(args):
    config = load_yaml(args.config)
    if not args.predictdir.endswith('/'):
        args.predictdir += '/'
    dataset = PrecomputedInpaintingResultsDataset(args.datadir, args.predictdir, **config.dataset_kwargs)
    os.makedirs(os.path.dirname(args.outpath), exist_ok=True)
    for img_i in tqdm.trange(len(dataset)):
        pred_fname = dataset.pred_filenames[img_i]
        cur_out_fname = os.path.join(args.outpath, pred_fname[len(args.predictdir):])
        os.makedirs(os.path.dirname(cur_out_fname), exist_ok=True)
        sample = dataset[img_i]
        img = sample['image']
        mask = sample['mask']
        inpainted = sample['inpainted']
        inpainted_blurred = cv2.GaussianBlur(np.transpose(inpainted, (1, 2, 0)), ksize=(args.k, args.k), sigmaX=args.s, sigmaY=args.s, borderType=cv2.BORDER_REFLECT)
        cur_res = (1 - mask) * np.transpose(img, (1, 2, 0)) + mask * inpainted_blurred
        cur_res = np.clip(cur_res * 255, 0, 255).astype('uint8')
        cur_res = cv2.cvtColor(cur_res, cv2.COLOR_RGB2BGR)
        cv2.imwrite(cur_out_fname, cur_res)

def process_images(src_images, indir, outdir, config):
    if config.generator_kind == 'segmentation':
        mask_generator = SegmentationMask(**config.mask_generator_kwargs)
    elif config.generator_kind == 'random':
        variants_n = config.mask_generator_kwargs.pop('variants_n', 2)
        mask_generator = MakeManyMasksWrapper(MixedMaskGenerator(**config.mask_generator_kwargs), variants_n=variants_n)
    else:
        raise ValueError(f'Unexpected generator kind: {config.generator_kind}')
    max_tamper_area = config.get('max_tamper_area', 1)
    for infile in src_images:
        try:
            file_relpath = infile[len(indir):]
            img_outpath = os.path.join(outdir, file_relpath)
            os.makedirs(os.path.dirname(img_outpath), exist_ok=True)
            image = Image.open(infile).convert('RGB')
            if min(image.size) < config.cropping.out_min_size:
                handle_small_mode = SmallMode(config.cropping.handle_small_mode)
                if handle_small_mode == SmallMode.DROP:
                    continue
                elif handle_small_mode == SmallMode.UPSCALE:
                    factor = config.cropping.out_min_size / min(image.size)
                    out_size = (np.array(image.size) * factor).round().astype('uint32')
                    image = image.resize(out_size, resample=Image.BICUBIC)
            else:
                factor = config.cropping.out_min_size / min(image.size)
                out_size = (np.array(image.size) * factor).round().astype('uint32')
                image = image.resize(out_size, resample=Image.BICUBIC)
            src_masks = mask_generator.get_masks(image)
            filtered_image_mask_pairs = []
            for cur_mask in src_masks:
                if config.cropping.out_square_crop:
                    crop_left, crop_top, crop_right, crop_bottom = propose_random_square_crop(cur_mask, min_overlap=config.cropping.crop_min_overlap)
                    cur_mask = cur_mask[crop_top:crop_bottom, crop_left:crop_right]
                    cur_image = image.copy().crop((crop_left, crop_top, crop_right, crop_bottom))
                else:
                    cur_image = image
                if len(np.unique(cur_mask)) == 0 or cur_mask.mean() > max_tamper_area:
                    continue
                filtered_image_mask_pairs.append((cur_image, cur_mask))
            mask_indices = np.random.choice(len(filtered_image_mask_pairs), size=min(len(filtered_image_mask_pairs), config.max_masks_per_image), replace=False)
            mask_basename = os.path.join(outdir, os.path.splitext(file_relpath)[0])
            for i, idx in enumerate(mask_indices):
                cur_image, cur_mask = filtered_image_mask_pairs[idx]
                cur_basename = mask_basename + f'_crop{i:03d}'
                Image.fromarray(np.clip(cur_mask * 255, 0, 255).astype('uint8'), mode='L').save(cur_basename + f'_mask{i:03d}.png')
                cur_image.save(cur_basename + '.png')
        except KeyboardInterrupt:
            return
        except Exception as ex:
            print(f'Could not make masks for {infile} due to {ex}:\n{traceback.format_exc()}')

def print_traceback_handler(sig, frame):
    LOGGER.warning(f'Received signal {sig}')
    bt = ''.join(traceback.format_stack())
    LOGGER.warning(f'Requested stack trace:\n{bt}')

def register_debug_signal_handlers(sig=signal.SIGUSR1, handler=print_traceback_handler):
    LOGGER.warning(f'Setting signal {sig} handler {handler}')
    signal.signal(sig, handler)

def visualize_mask_and_images(images_dict: Dict[str, np.ndarray], keys: List[str], last_without_mask=True, rescale_keys=None, mask_only_first=None, black_mask=False) -> np.ndarray:
    mask = images_dict['mask'] > 0.5
    result = []
    for i, k in enumerate(keys):
        img = images_dict[k]
        img = np.transpose(img, (1, 2, 0))
        if rescale_keys is not None and k in rescale_keys:
            img = img - img.min()
            img /= img.max() + 1e-05
        if len(img.shape) == 2:
            img = np.expand_dims(img, 2)
        if img.shape[2] == 1:
            img = np.repeat(img, 3, axis=2)
        elif img.shape[2] > 3:
            img_classes = img.argmax(2)
            img = color.label2rgb(img_classes, colors=COLORS)
        if mask_only_first:
            need_mark_boundaries = i == 0
        else:
            need_mark_boundaries = i < len(keys) - 1 or not last_without_mask
        if need_mark_boundaries:
            if black_mask:
                img = img * (1 - mask[0][..., None])
            img = mark_boundaries(img, mask[0], color=(1.0, 0.0, 0.0), outline_color=(1.0, 1.0, 1.0), mode='thick')
        result.append(img)
    return np.concatenate(result, axis=1)

class DirectoryVisualizer(BaseVisualizer):
    DEFAULT_KEY_ORDER = 'image predicted_image inpainted'.split(' ')

    def __init__(self, outdir, key_order=DEFAULT_KEY_ORDER, max_items_in_batch=10, last_without_mask=True, rescale_keys=None):
        self.outdir = outdir
        os.makedirs(self.outdir, exist_ok=True)
        self.key_order = key_order
        self.max_items_in_batch = max_items_in_batch
        self.last_without_mask = last_without_mask
        self.rescale_keys = rescale_keys

    def __call__(self, epoch_i, batch_i, batch, suffix='', rank=None):
        check_and_warn_input_range(batch['image'], 0, 1, 'DirectoryVisualizer target image')
        vis_img = visualize_mask_and_images_batch(batch, self.key_order, max_items=self.max_items_in_batch, last_without_mask=self.last_without_mask, rescale_keys=self.rescale_keys)
        vis_img = np.clip(vis_img * 255, 0, 255).astype('uint8')
        curoutdir = os.path.join(self.outdir, f'epoch{epoch_i:04d}{suffix}')
        os.makedirs(curoutdir, exist_ok=True)
        rank_suffix = f'_r{rank}' if rank is not None else ''
        out_fname = os.path.join(curoutdir, f'batch{batch_i:07d}{rank_suffix}.jpg')
        vis_img = cv2.cvtColor(vis_img, cv2.COLOR_RGB2BGR)
        cv2.imwrite(out_fname, vis_img)

def __call__(self, epoch_i, batch_i, batch, suffix='', rank=None):
    check_and_warn_input_range(batch['image'], 0, 1, 'DirectoryVisualizer target image')
    vis_img = visualize_mask_and_images_batch(batch, self.key_order, max_items=self.max_items_in_batch, last_without_mask=self.last_without_mask, rescale_keys=self.rescale_keys)
    vis_img = np.clip(vis_img * 255, 0, 255).astype('uint8')
    curoutdir = os.path.join(self.outdir, f'epoch{epoch_i:04d}{suffix}')
    os.makedirs(curoutdir, exist_ok=True)
    rank_suffix = f'_r{rank}' if rank is not None else ''
    out_fname = os.path.join(curoutdir, f'batch{batch_i:07d}{rank_suffix}.jpg')
    vis_img = cv2.cvtColor(vis_img, cv2.COLOR_RGB2BGR)
    cv2.imwrite(out_fname, vis_img)

def load_image(fname, mode='RGB', return_orig=False):
    img = np.array(Image.open(fname).convert(mode))
    if img.ndim == 3:
        img = np.transpose(img, (2, 0, 1))
    out_img = img.astype('float32') / 255
    if return_orig:
        return (out_img, img)
    else:
        return out_img

def scale_image(img, factor, interpolation=cv2.INTER_AREA):
    if img.shape[0] == 1:
        img = img[0]
    else:
        img = np.transpose(img, (1, 2, 0))
    img = cv2.resize(img, dsize=None, fx=factor, fy=factor, interpolation=interpolation)
    if img.ndim == 2:
        img = img[None, ...]
    else:
        img = np.transpose(img, (2, 0, 1))
    return img

def save_item_for_vis(item, out_file):
    mask = item['mask'] > 0.5
    if mask.ndim == 3:
        mask = mask[0]
    img = mark_boundaries(np.transpose(item['image'], (1, 2, 0)), mask, color=(1.0, 0.0, 0.0), outline_color=(1.0, 1.0, 1.0), mode='thick')
    if 'inpainted' in item:
        inp_img = mark_boundaries(np.transpose(item['inpainted'], (1, 2, 0)), mask, color=(1.0, 0.0, 0.0), mode='outer')
        img = np.concatenate((img, inp_img), axis=1)
    img = np.clip(img * 255, 0, 255).astype('uint8')
    io.imsave(out_file, img)

def save_mask_for_sidebyside(item, out_file):
    mask = item['mask']
    if mask.ndim == 3:
        mask = mask[0]
    mask = np.clip(mask * 255, 0, 255).astype('uint8')
    io.imsave(out_file, mask)

def save_img_for_sidebyside(item, out_file):
    img = np.transpose(item['image'], (1, 2, 0))
    img = np.clip(img * 255, 0, 255).astype('uint8')
    io.imsave(out_file, img)

def calculade_fid_no_img(img_i, activations_pred, activations_target, eps=1e-06):
    activations_pred = activations_pred.copy()
    activations_pred[img_i] = activations_target[img_i]
    return calculate_frechet_distance(activations_pred, activations_target, eps=eps)

def tensor2im(image_tensor, imtype=np.uint8, cent=1.0, factor=255.0 / 2.0):
    image_numpy = image_tensor[0].cpu().float().numpy()
    image_numpy = (np.transpose(image_numpy, (1, 2, 0)) + cent) * factor
    return image_numpy.astype(imtype)

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

def _prepare_mask(self, mask):
    height, width = mask.shape
    target_width = width if self._is_power_of_two(width) else 1 << width.bit_length()
    target_height = height if self._is_power_of_two(height) else 1 << height.bit_length()
    return resize(mask.astype('float32'), (target_height, target_width), order=0, mode='edge').round().astype('int32')

def upgrade_type(arr):
    dtype = arr.dtype
    if dtype == np.uint8:
        return (arr.astype(np.uint16), True)
    elif dtype == np.uint16:
        return (arr.astype(np.uint32), True)
    elif dtype == np.uint32:
        return (arr.astype(np.uint64), True)
    return (arr, False)

def downgrade_type(arr):
    dtype = arr.dtype
    if dtype == np.uint64:
        return arr.astype(np.uint32)
    elif dtype == np.uint32:
        return arr.astype(np.uint16)
    elif dtype == np.uint16:
        return arr.astype(np.uint8)
    return arr

def color_encode(labelmap, colors, mode='RGB'):
    labelmap = labelmap.astype('int')
    labelmap_rgb = np.zeros((labelmap.shape[0], labelmap.shape[1], 3), dtype=np.uint8)
    for label in np.unique(labelmap):
        if label < 0:
            continue
        labelmap_rgb += (labelmap == label)[:, :, np.newaxis] * np.tile(colors[label], (labelmap.shape[0], labelmap.shape[1], 1))
    if mode == 'BGR':
        return labelmap_rgb[:, :, ::-1]
    else:
        return labelmap_rgb

def print_traceback_handler(sig, frame):
    LOGGER.warning(f'Received signal {sig}')
    bt = ''.join(traceback.format_stack())
    LOGGER.warning(f'Requested stack trace:\n{bt}')

def register_debug_signal_handlers(sig=signal.SIGUSR1, handler=print_traceback_handler):
    LOGGER.warning(f'Setting signal {sig} handler {handler}')
    signal.signal(sig, handler)

def make_random_irregular_mask(shape, max_angle=4, max_len=60, max_width=20, min_times=0, max_times=10, draw_method=DrawMethod.LINE):
    draw_method = DrawMethod(draw_method)
    height, width = shape
    mask = np.zeros((height, width), np.float32)
    times = np.random.randint(min_times, max_times + 1)
    for i in range(times):
        start_x = np.random.randint(width)
        start_y = np.random.randint(height)
        for j in range(1 + np.random.randint(5)):
            angle = 0.01 + np.random.randint(max_angle)
            if i % 2 == 0:
                angle = 2 * 3.1415926 - angle
            length = 10 + np.random.randint(max_len)
            brush_w = 5 + np.random.randint(max_width)
            end_x = np.clip((start_x + length * np.sin(angle)).astype(np.int32), 0, width)
            end_y = np.clip((start_y + length * np.cos(angle)).astype(np.int32), 0, height)
            if draw_method == DrawMethod.LINE:
                cv2.line(mask, (start_x, start_y), (end_x, end_y), 1.0, brush_w)
            elif draw_method == DrawMethod.CIRCLE:
                cv2.circle(mask, (start_x, start_y), radius=brush_w, color=1.0, thickness=-1)
            elif draw_method == DrawMethod.SQUARE:
                radius = brush_w // 2
                mask[start_y - radius:start_y + radius, start_x - radius:start_x + radius] = 1
            start_x, start_y = (end_x, end_y)
    return mask[None, ...]

class RandomSegmentationMaskGenerator:

    def __init__(self, **kwargs):
        self.impl = None
        self.kwargs = kwargs

    def __call__(self, img, iter_i=None, raw_image=None):
        if self.impl is None:
            self.impl = SegmentationMask(**self.kwargs)
        masks = self.impl.get_masks(np.transpose(img, (1, 2, 0)))
        masks = [m for m in masks if len(np.unique(m)) > 1]
        return np.random.choice(masks)

def __call__(self, img, iter_i=None, raw_image=None):
    if self.impl is None:
        self.impl = SegmentationMask(**self.kwargs)
    masks = self.impl.get_masks(np.transpose(img, (1, 2, 0)))
    masks = [m for m in masks if len(np.unique(m)) > 1]
    return np.random.choice(masks)

class DumbAreaMaskGenerator:
    min_ratio = 0.1
    max_ratio = 0.35
    default_ratio = 0.225

    def __init__(self, is_training):
        self.is_training = is_training

    def _random_vector(self, dimension):
        if self.is_training:
            lower_limit = math.sqrt(self.min_ratio)
            upper_limit = math.sqrt(self.max_ratio)
            mask_side = round((random.random() * (upper_limit - lower_limit) + lower_limit) * dimension)
            u = random.randint(0, dimension - mask_side - 1)
            v = u + mask_side
        else:
            margin = math.sqrt(self.default_ratio) / 2 * dimension
            u = round(dimension / 2 - margin)
            v = round(dimension / 2 + margin)
        return (u, v)

    def __call__(self, img, iter_i=None, raw_image=None):
        c, height, width = img.shape
        mask = np.zeros((height, width), np.float32)
        x1, x2 = self._random_vector(width)
        y1, y2 = self._random_vector(height)
        mask[x1:x2, y1:y2] = 1
        return mask[None, ...]

def _random_vector(self, dimension):
    if self.is_training:
        lower_limit = math.sqrt(self.min_ratio)
        upper_limit = math.sqrt(self.max_ratio)
        mask_side = round((random.random() * (upper_limit - lower_limit) + lower_limit) * dimension)
        u = random.randint(0, dimension - mask_side - 1)
        v = u + mask_side
    else:
        margin = math.sqrt(self.default_ratio) / 2 * dimension
        u = round(dimension / 2 - margin)
        v = round(dimension / 2 + margin)
    return (u, v)

class OutpaintingMaskGenerator:

    def __init__(self, min_padding_percent: float=0.04, max_padding_percent: int=0.25, left_padding_prob: float=0.5, top_padding_prob: float=0.5, right_padding_prob: float=0.5, bottom_padding_prob: float=0.5, is_fixed_randomness: bool=False):
        """
        is_fixed_randomness - get identical paddings for the same image if args are the same
        """
        self.min_padding_percent = min_padding_percent
        self.max_padding_percent = max_padding_percent
        self.probs = [left_padding_prob, top_padding_prob, right_padding_prob, bottom_padding_prob]
        self.is_fixed_randomness = is_fixed_randomness
        assert self.min_padding_percent <= self.max_padding_percent
        assert self.max_padding_percent > 0
        assert len([x for x in [self.min_padding_percent, self.max_padding_percent] if x >= 0 and x <= 1]) == 2, f'Padding percentage should be in [0,1]'
        assert sum(self.probs) > 0, f'At least one of the padding probs should be greater than 0 - {self.probs}'
        assert len([x for x in self.probs if x >= 0 and x <= 1]) == 4, f'At least one of padding probs is not in [0,1] - {self.probs}'
        if len([x for x in self.probs if x > 0]) == 1:
            LOGGER.warning(f'Only one padding prob is greater than zero - {self.probs}. That means that the outpainting masks will be always on the same side')

    def apply_padding(self, mask, coord):
        mask[int(coord[0][0] * self.img_h):int(coord[1][0] * self.img_h), int(coord[0][1] * self.img_w):int(coord[1][1] * self.img_w)] = 1
        return mask

    def get_padding(self, size):
        n1 = int(self.min_padding_percent * size)
        n2 = int(self.max_padding_percent * size)
        return self.rnd.randint(n1, n2) / size

    @staticmethod
    def _img2rs(img):
        arr = np.ascontiguousarray(img.astype(np.uint8))
        str_hash = hashlib.sha1(arr).hexdigest()
        res = hash(str_hash) % 2 ** 32
        return res

    def __call__(self, img, iter_i=None, raw_image=None):
        c, self.img_h, self.img_w = img.shape
        mask = np.zeros((self.img_h, self.img_w), np.float32)
        at_least_one_mask_applied = False
        if self.is_fixed_randomness:
            assert raw_image is not None, f'Cant calculate hash on raw_image=None'
            rs = self._img2rs(raw_image)
            self.rnd = np.random.RandomState(rs)
        else:
            self.rnd = np.random
        coords = [[(0, 0), (1, self.get_padding(size=self.img_h))], [(0, 0), (self.get_padding(size=self.img_w), 1)], [(0, 1 - self.get_padding(size=self.img_h)), (1, 1)], [(1 - self.get_padding(size=self.img_w), 0), (1, 1)]]
        for pp, coord in zip(self.probs, coords):
            if self.rnd.random() < pp:
                at_least_one_mask_applied = True
                mask = self.apply_padding(mask=mask, coord=coord)
        if not at_least_one_mask_applied:
            idx = self.rnd.choice(range(len(coords)), p=np.array(self.probs) / sum(self.probs))
            mask = self.apply_padding(mask=mask, coord=coords[idx])
        return mask[None, ...]

def __init__(self, min_padding_percent: float=0.04, max_padding_percent: int=0.25, left_padding_prob: float=0.5, top_padding_prob: float=0.5, right_padding_prob: float=0.5, bottom_padding_prob: float=0.5, is_fixed_randomness: bool=False):
    """
        is_fixed_randomness - get identical paddings for the same image if args are the same
        """
    self.min_padding_percent = min_padding_percent
    self.max_padding_percent = max_padding_percent
    self.probs = [left_padding_prob, top_padding_prob, right_padding_prob, bottom_padding_prob]
    self.is_fixed_randomness = is_fixed_randomness
    assert self.min_padding_percent <= self.max_padding_percent
    assert self.max_padding_percent > 0
    assert len([x for x in [self.min_padding_percent, self.max_padding_percent] if x >= 0 and x <= 1]) == 2, f'Padding percentage should be in [0,1]'
    assert sum(self.probs) > 0, f'At least one of the padding probs should be greater than 0 - {self.probs}'
    assert len([x for x in self.probs if x >= 0 and x <= 1]) == 4, f'At least one of padding probs is not in [0,1] - {self.probs}'
    if len([x for x in self.probs if x > 0]) == 1:
        LOGGER.warning(f'Only one padding prob is greater than zero - {self.probs}. That means that the outpainting masks will be always on the same side')

@staticmethod
def _img2rs(img):
    arr = np.ascontiguousarray(img.astype(np.uint8))
    str_hash = hashlib.sha1(arr).hexdigest()
    res = hash(str_hash) % 2 ** 32
    return res

def __call__(self, img, iter_i=None, raw_image=None):
    c, self.img_h, self.img_w = img.shape
    mask = np.zeros((self.img_h, self.img_w), np.float32)
    at_least_one_mask_applied = False
    if self.is_fixed_randomness:
        assert raw_image is not None, f'Cant calculate hash on raw_image=None'
        rs = self._img2rs(raw_image)
        self.rnd = np.random.RandomState(rs)
    else:
        self.rnd = np.random
    coords = [[(0, 0), (1, self.get_padding(size=self.img_h))], [(0, 0), (self.get_padding(size=self.img_w), 1)], [(0, 1 - self.get_padding(size=self.img_h)), (1, 1)], [(1 - self.get_padding(size=self.img_w), 0), (1, 1)]]
    for pp, coord in zip(self.probs, coords):
        if self.rnd.random() < pp:
            at_least_one_mask_applied = True
            mask = self.apply_padding(mask=mask, coord=coord)
    if not at_least_one_mask_applied:
        idx = self.rnd.choice(range(len(coords)), p=np.array(self.probs) / sum(self.probs))
        mask = self.apply_padding(mask=mask, coord=coords[idx])
    return mask[None, ...]

class MixedMaskGenerator:

    def __init__(self, irregular_proba=1 / 3, irregular_kwargs=None, box_proba=1 / 3, box_kwargs=None, segm_proba=1 / 3, segm_kwargs=None, squares_proba=0, squares_kwargs=None, superres_proba=0, superres_kwargs=None, outpainting_proba=0, outpainting_kwargs=None, invert_proba=0):
        self.probas = []
        self.gens = []
        if irregular_proba > 0:
            self.probas.append(irregular_proba)
            if irregular_kwargs is None:
                irregular_kwargs = {}
            else:
                irregular_kwargs = dict(irregular_kwargs)
            irregular_kwargs['draw_method'] = DrawMethod.LINE
            self.gens.append(RandomIrregularMaskGenerator(**irregular_kwargs))
        if box_proba > 0:
            self.probas.append(box_proba)
            if box_kwargs is None:
                box_kwargs = {}
            self.gens.append(RandomRectangleMaskGenerator(**box_kwargs))
        if segm_proba > 0:
            self.probas.append(segm_proba)
            if segm_kwargs is None:
                segm_kwargs = {}
            self.gens.append(RandomSegmentationMaskGenerator(**segm_kwargs))
        if squares_proba > 0:
            self.probas.append(squares_proba)
            if squares_kwargs is None:
                squares_kwargs = {}
            else:
                squares_kwargs = dict(squares_kwargs)
            squares_kwargs['draw_method'] = DrawMethod.SQUARE
            self.gens.append(RandomIrregularMaskGenerator(**squares_kwargs))
        if superres_proba > 0:
            self.probas.append(superres_proba)
            if superres_kwargs is None:
                superres_kwargs = {}
            self.gens.append(RandomSuperresMaskGenerator(**superres_kwargs))
        if outpainting_proba > 0:
            self.probas.append(outpainting_proba)
            if outpainting_kwargs is None:
                outpainting_kwargs = {}
            self.gens.append(OutpaintingMaskGenerator(**outpainting_kwargs))
        self.probas = np.array(self.probas, dtype='float32')
        self.probas /= self.probas.sum()
        self.invert_proba = invert_proba

    def __call__(self, img, iter_i=None, raw_image=None):
        kind = np.random.choice(len(self.probas), p=self.probas)
        gen = self.gens[kind]
        result = gen(img, iter_i=iter_i, raw_image=raw_image)
        if self.invert_proba > 0 and random.random() < self.invert_proba:
            result = 1 - result
        return result

def __call__(self, img, iter_i=None, raw_image=None):
    kind = np.random.choice(len(self.probas), p=self.probas)
    gen = self.gens[kind]
    result = gen(img, iter_i=iter_i, raw_image=raw_image)
    if self.invert_proba > 0 and random.random() < self.invert_proba:
        result = 1 - result
    return result

class InpaintingTrainDataset(Dataset):

    def __init__(self, indir, mask_generator, transform):
        self.in_files = list(glob.glob(os.path.join(indir, '**', '*.jpg'), recursive=True))
        self.mask_generator = mask_generator
        self.transform = transform
        self.iter_i = 0

    def __len__(self):
        return len(self.in_files)

    def __getitem__(self, item):
        path = self.in_files[item]
        img = cv2.imread(path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = self.transform(image=img)['image']
        img = np.transpose(img, (2, 0, 1))
        mask = self.mask_generator(img, iter_i=self.iter_i)
        self.iter_i += 1
        return dict(image=img, mask=mask)

def __getitem__(self, item):
    path = self.in_files[item]
    img = cv2.imread(path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = self.transform(image=img)['image']
    img = np.transpose(img, (2, 0, 1))
    mask = self.mask_generator(img, iter_i=self.iter_i)
    self.iter_i += 1
    return dict(image=img, mask=mask)

class InpaintingTrainWebDataset(IterableDataset):

    def __init__(self, indir, mask_generator, transform, shuffle_buffer=200):
        self.impl = webdataset.Dataset(indir).shuffle(shuffle_buffer).decode('rgb').to_tuple('jpg')
        self.mask_generator = mask_generator
        self.transform = transform

    def __iter__(self):
        for iter_i, (img,) in enumerate(self.impl):
            img = np.clip(img * 255, 0, 255).astype('uint8')
            img = self.transform(image=img)['image']
            img = np.transpose(img, (2, 0, 1))
            mask = self.mask_generator(img, iter_i=iter_i)
            yield dict(image=img, mask=mask)

def __iter__(self):
    for iter_i, (img,) in enumerate(self.impl):
        img = np.clip(img * 255, 0, 255).astype('uint8')
        img = self.transform(image=img)['image']
        img = np.transpose(img, (2, 0, 1))
        mask = self.mask_generator(img, iter_i=iter_i)
        yield dict(image=img, mask=mask)

class ImgSegmentationDataset(Dataset):

    def __init__(self, indir, mask_generator, transform, out_size, segm_indir, semantic_seg_n_classes):
        self.indir = indir
        self.segm_indir = segm_indir
        self.mask_generator = mask_generator
        self.transform = transform
        self.out_size = out_size
        self.semantic_seg_n_classes = semantic_seg_n_classes
        self.in_files = list(glob.glob(os.path.join(indir, '**', '*.jpg'), recursive=True))

    def __len__(self):
        return len(self.in_files)

    def __getitem__(self, item):
        path = self.in_files[item]
        img = cv2.imread(path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, (self.out_size, self.out_size))
        img = self.transform(image=img)['image']
        img = np.transpose(img, (2, 0, 1))
        mask = self.mask_generator(img)
        segm, segm_classes = self.load_semantic_segm(path)
        result = dict(image=img, mask=mask, segm=segm, segm_classes=segm_classes)
        return result

    def load_semantic_segm(self, img_path):
        segm_path = img_path.replace(self.indir, self.segm_indir).replace('.jpg', '.png')
        mask = cv2.imread(segm_path, cv2.IMREAD_GRAYSCALE)
        mask = cv2.resize(mask, (self.out_size, self.out_size))
        tensor = torch.from_numpy(np.clip(mask.astype(int) - 1, 0, None))
        ohe = F.one_hot(tensor.long(), num_classes=self.semantic_seg_n_classes)
        return (ohe.permute(2, 0, 1).float(), tensor.unsqueeze(0))

def __getitem__(self, item):
    path = self.in_files[item]
    img = cv2.imread(path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (self.out_size, self.out_size))
    img = self.transform(image=img)['image']
    img = np.transpose(img, (2, 0, 1))
    mask = self.mask_generator(img)
    segm, segm_classes = self.load_semantic_segm(path)
    result = dict(image=img, mask=mask, segm=segm, segm_classes=segm_classes)
    return result

def make_constant_area_crop_params(img_height, img_width, min_size=128, max_size=512, area=256 * 256, round_to_mod=16):
    min_size = min(img_height, img_width, min_size)
    max_size = min(img_height, img_width, max_size)
    if random.random() < 0.5:
        out_height = min(max_size, ceil_modulo(random.randint(min_size, max_size), round_to_mod))
        out_width = min(max_size, ceil_modulo(area // out_height, round_to_mod))
    else:
        out_width = min(max_size, ceil_modulo(random.randint(min_size, max_size), round_to_mod))
        out_height = min(max_size, ceil_modulo(area // out_width, round_to_mod))
    start_y = random.randint(0, img_height - out_height)
    start_x = random.randint(0, img_width - out_width)
    return (start_y, start_x, out_height, out_width)

def visualize_mask_and_images(images_dict: Dict[str, np.ndarray], keys: List[str], last_without_mask=True, rescale_keys=None, mask_only_first=None, black_mask=False) -> np.ndarray:
    mask = images_dict['mask'] > 0.5
    result = []
    for i, k in enumerate(keys):
        img = images_dict[k]
        img = np.transpose(img, (1, 2, 0))
        if rescale_keys is not None and k in rescale_keys:
            img = img - img.min()
            img /= img.max() + 1e-05
        if len(img.shape) == 2:
            img = np.expand_dims(img, 2)
        if img.shape[2] == 1:
            img = np.repeat(img, 3, axis=2)
        elif img.shape[2] > 3:
            img_classes = img.argmax(2)
            img = color.label2rgb(img_classes, colors=COLORS)
        if mask_only_first:
            need_mark_boundaries = i == 0
        else:
            need_mark_boundaries = i < len(keys) - 1 or not last_without_mask
        if need_mark_boundaries:
            if black_mask:
                img = img * (1 - mask[0][..., None])
            img = mark_boundaries(img, mask[0], color=(1.0, 0.0, 0.0), outline_color=(1.0, 1.0, 1.0), mode='thick')
        result.append(img)
    return np.concatenate(result, axis=1)

class DirectoryVisualizer(BaseVisualizer):
    DEFAULT_KEY_ORDER = 'image predicted_image inpainted'.split(' ')

    def __init__(self, outdir, key_order=DEFAULT_KEY_ORDER, max_items_in_batch=10, last_without_mask=True, rescale_keys=None):
        self.outdir = outdir
        os.makedirs(self.outdir, exist_ok=True)
        self.key_order = key_order
        self.max_items_in_batch = max_items_in_batch
        self.last_without_mask = last_without_mask
        self.rescale_keys = rescale_keys

    def __call__(self, epoch_i, batch_i, batch, suffix='', rank=None):
        check_and_warn_input_range(batch['image'], 0, 1, 'DirectoryVisualizer target image')
        vis_img = visualize_mask_and_images_batch(batch, self.key_order, max_items=self.max_items_in_batch, last_without_mask=self.last_without_mask, rescale_keys=self.rescale_keys)
        vis_img = np.clip(vis_img * 255, 0, 255).astype('uint8')
        curoutdir = os.path.join(self.outdir, f'epoch{epoch_i:04d}{suffix}')
        os.makedirs(curoutdir, exist_ok=True)
        rank_suffix = f'_r{rank}' if rank is not None else ''
        out_fname = os.path.join(curoutdir, f'batch{batch_i:07d}{rank_suffix}.jpg')
        vis_img = cv2.cvtColor(vis_img, cv2.COLOR_RGB2BGR)
        cv2.imwrite(out_fname, vis_img)

def __call__(self, epoch_i, batch_i, batch, suffix='', rank=None):
    check_and_warn_input_range(batch['image'], 0, 1, 'DirectoryVisualizer target image')
    vis_img = visualize_mask_and_images_batch(batch, self.key_order, max_items=self.max_items_in_batch, last_without_mask=self.last_without_mask, rescale_keys=self.rescale_keys)
    vis_img = np.clip(vis_img * 255, 0, 255).astype('uint8')
    curoutdir = os.path.join(self.outdir, f'epoch{epoch_i:04d}{suffix}')
    os.makedirs(curoutdir, exist_ok=True)
    rank_suffix = f'_r{rank}' if rank is not None else ''
    out_fname = os.path.join(curoutdir, f'batch{batch_i:07d}{rank_suffix}.jpg')
    vis_img = cv2.cvtColor(vis_img, cv2.COLOR_RGB2BGR)
    cv2.imwrite(out_fname, vis_img)

def load_image(fname, mode='RGB', return_orig=False):
    img = np.array(Image.open(fname).convert(mode))
    if img.ndim == 3:
        img = np.transpose(img, (2, 0, 1))
    out_img = img.astype('float32') / 255
    if return_orig:
        return (out_img, img)
    else:
        return out_img

def scale_image(img, factor, interpolation=cv2.INTER_AREA):
    if img.shape[0] == 1:
        img = img[0]
    else:
        img = np.transpose(img, (1, 2, 0))
    img = cv2.resize(img, dsize=None, fx=factor, fy=factor, interpolation=interpolation)
    if img.ndim == 2:
        img = img[None, ...]
    else:
        img = np.transpose(img, (2, 0, 1))
    return img

def save_item_for_vis(item, out_file):
    mask = item['mask'] > 0.5
    if mask.ndim == 3:
        mask = mask[0]
    img = mark_boundaries(np.transpose(item['image'], (1, 2, 0)), mask, color=(1.0, 0.0, 0.0), outline_color=(1.0, 1.0, 1.0), mode='thick')
    if 'inpainted' in item:
        inp_img = mark_boundaries(np.transpose(item['inpainted'], (1, 2, 0)), mask, color=(1.0, 0.0, 0.0), mode='outer')
        img = np.concatenate((img, inp_img), axis=1)
    img = np.clip(img * 255, 0, 255).astype('uint8')
    io.imsave(out_file, img)

def save_mask_for_sidebyside(item, out_file):
    mask = item['mask']
    if mask.ndim == 3:
        mask = mask[0]
    mask = np.clip(mask * 255, 0, 255).astype('uint8')
    io.imsave(out_file, mask)

def save_img_for_sidebyside(item, out_file):
    img = np.transpose(item['image'], (1, 2, 0))
    img = np.clip(img * 255, 0, 255).astype('uint8')
    io.imsave(out_file, img)

def calculade_fid_no_img(img_i, activations_pred, activations_target, eps=1e-06):
    activations_pred = activations_pred.copy()
    activations_pred[img_i] = activations_target[img_i]
    return calculate_frechet_distance(activations_pred, activations_target, eps=eps)

def tensor2im(image_tensor, imtype=np.uint8, cent=1.0, factor=255.0 / 2.0):
    image_numpy = image_tensor[0].cpu().float().numpy()
    image_numpy = (np.transpose(image_numpy, (1, 2, 0)) + cent) * factor
    return image_numpy.astype(imtype)

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

def _prepare_mask(self, mask):
    height, width = mask.shape
    target_width = width if self._is_power_of_two(width) else 1 << width.bit_length()
    target_height = height if self._is_power_of_two(height) else 1 << height.bit_length()
    return resize(mask.astype('float32'), (target_height, target_width), order=0, mode='edge').round().astype('int32')

def upgrade_type(arr):
    dtype = arr.dtype
    if dtype == np.uint8:
        return (arr.astype(np.uint16), True)
    elif dtype == np.uint16:
        return (arr.astype(np.uint32), True)
    elif dtype == np.uint32:
        return (arr.astype(np.uint64), True)
    return (arr, False)

def downgrade_type(arr):
    dtype = arr.dtype
    if dtype == np.uint64:
        return arr.astype(np.uint32)
    elif dtype == np.uint32:
        return arr.astype(np.uint16)
    elif dtype == np.uint16:
        return arr.astype(np.uint8)
    return arr

def color_encode(labelmap, colors, mode='RGB'):
    labelmap = labelmap.astype('int')
    labelmap_rgb = np.zeros((labelmap.shape[0], labelmap.shape[1], 3), dtype=np.uint8)
    for label in np.unique(labelmap):
        if label < 0:
            continue
        labelmap_rgb += (labelmap == label)[:, :, np.newaxis] * np.tile(colors[label], (labelmap.shape[0], labelmap.shape[1], 1))
    if mode == 'BGR':
        return labelmap_rgb[:, :, ::-1]
    else:
        return labelmap_rgb

def sample_target(im, target_bb, search_area_factor, output_sz=None, mask=None):
    """ Extracts a square crop centered at target_bb box, of area search_area_factor^2 times target_bb area

    args:
        im - cv image
        target_bb - target box [x, y, w, h]
        search_area_factor - Ratio of crop size to target size
        output_sz - (float) Size to which the extracted crop is resized (always square). If None, no resizing is done.

    returns:
        cv image - extracted crop
        float - the factor by which the crop has been resized to make the crop size equal output_size
    """
    if not isinstance(target_bb, list):
        x, y, w, h = target_bb.tolist()
    else:
        x, y, w, h = target_bb
    crop_sz = math.ceil(math.sqrt(w * h) * search_area_factor)
    if crop_sz < 1:
        raise Exception('Too small bounding box.')
    x1 = round(x + 0.5 * w - crop_sz * 0.5)
    x2 = x1 + crop_sz
    y1 = round(y + 0.5 * h - crop_sz * 0.5)
    y2 = y1 + crop_sz
    x1_pad = max(0, -x1)
    x2_pad = max(x2 - im.shape[1] + 1, 0)
    y1_pad = max(0, -y1)
    y2_pad = max(y2 - im.shape[0] + 1, 0)
    im_crop = im[y1 + y1_pad:y2 - y2_pad, x1 + x1_pad:x2 - x2_pad, :]
    if mask is not None:
        mask_crop = mask[y1 + y1_pad:y2 - y2_pad, x1 + x1_pad:x2 - x2_pad]
    im_crop_padded = cv.copyMakeBorder(im_crop, y1_pad, y2_pad, x1_pad, x2_pad, cv.BORDER_CONSTANT)
    H, W, _ = im_crop_padded.shape
    att_mask = np.ones((H, W))
    end_x, end_y = (-x2_pad, -y2_pad)
    if y2_pad == 0:
        end_y = None
    if x2_pad == 0:
        end_x = None
    att_mask[y1_pad:end_y, x1_pad:end_x] = 0
    if mask is not None:
        mask_crop_padded = F.pad(mask_crop, pad=(x1_pad, x2_pad, y1_pad, y2_pad), mode='constant', value=0)
    if output_sz is not None:
        resize_factor = output_sz / crop_sz
        im_crop_padded = cv.resize(im_crop_padded, (output_sz, output_sz))
        att_mask = cv.resize(att_mask, (output_sz, output_sz)).astype(np.bool_)
        if mask is None:
            return (im_crop_padded, resize_factor, att_mask)
        mask_crop_padded = F.interpolate(mask_crop_padded[None, None], (output_sz, output_sz), mode='bilinear', align_corners=False)[0, 0]
        return (im_crop_padded, resize_factor, att_mask, mask_crop_padded)
    else:
        if mask is None:
            return (im_crop_padded, att_mask.astype(np.bool_), 1.0)
        return (im_crop_padded, 1.0, att_mask.astype(np.bool_), mask_crop_padded)

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

def copy(self):
    return TensorList(super(TensorList, self).copy())

def Choice(*args):
    """Can be used to sample random parameter values."""
    return random.choice(args)

def gen_masked_tokens(tokens, indices, alpha=0.2):
    indices = indices[0].astype(int)
    tokens = tokens.copy()
    tokens[indices] = alpha * tokens[indices] + (1 - alpha) * 255
    return tokens

class PreprocessorX_onnx(object):

    def __init__(self):
        self.mean = np.array([0.485, 0.456, 0.406]).reshape((1, 3, 1, 1))
        self.std = np.array([0.229, 0.224, 0.225]).reshape((1, 3, 1, 1))

    def process(self, img_arr: np.ndarray, amask_arr: np.ndarray):
        """img_arr: (H,W,3), amask_arr: (H,W)"""
        img_arr_4d = img_arr[np.newaxis, :, :, :].transpose(0, 3, 1, 2)
        img_arr_4d = (img_arr_4d / 255.0 - self.mean) / self.std
        amask_arr_3d = amask_arr[np.newaxis, :, :]
        return (img_arr_4d.astype(np.float32), amask_arr_3d.astype(np.bool))

def process(self, img_arr: np.ndarray, amask_arr: np.ndarray):
    """img_arr: (H,W,3), amask_arr: (H,W)"""
    img_arr_4d = img_arr[np.newaxis, :, :, :].transpose(0, 3, 1, 2)
    img_arr_4d = (img_arr_4d / 255.0 - self.mean) / self.std
    amask_arr_3d = amask_arr[np.newaxis, :, :]
    return (img_arr_4d.astype(np.float32), amask_arr_3d.astype(np.bool))

@torch.no_grad()
def convsample_ddim(model, cond, steps, shape, eta=1.0, callback=None, normals_sequence=None, mask=None, x0=None, quantize_x0=False, img_callback=None, temperature=1.0, noise_dropout=0.0, score_corrector=None, corrector_kwargs=None, x_T=None, log_every_t=None):
    ddim = DDIMSampler(model)
    bs = shape[0]
    shape = shape[1:]
    print(f'Sampling with eta = {eta}; steps: {steps}')
    samples, intermediates = ddim.sample(steps, batch_size=bs, shape=shape, conditioning=cond, callback=callback, normals_sequence=normals_sequence, quantize_x0=quantize_x0, eta=eta, mask=mask, x0=x0, temperature=temperature, verbose=False, score_corrector=score_corrector, corrector_kwargs=corrector_kwargs, x_T=x_T)
    return (samples, intermediates)

def make_batch(image, mask, device):
    image = np.array(Image.open(image).convert('RGB'))
    image = image.astype(np.float32) / 255.0
    image = image[None].transpose(0, 3, 1, 2)
    image = torch.from_numpy(image)
    mask = np.array(Image.open(mask).convert('L'))
    mask = mask.astype(np.float32) / 255.0
    mask = mask[None, None]
    mask[mask < 0.5] = 0
    mask[mask >= 0.5] = 1
    mask = torch.from_numpy(mask)
    masked_image = (1 - mask) * image
    batch = {'image': image, 'mask': mask, 'masked_image': masked_image}
    for k in batch:
        batch[k] = batch[k].to(device=device)
        batch[k] = batch[k] * 2.0 - 1.0
    return batch

@torch.no_grad()
def convsample_ddim(model, steps, shape, eta=1.0):
    ddim = DDIMSampler(model)
    bs = shape[0]
    shape = shape[1:]
    samples, intermediates = ddim.sample(steps, batch_size=bs, shape=shape, eta=eta, verbose=False)
    return (samples, intermediates)

def modcrop_np(img, sf):
    """
    Args:
        img: numpy image, WxH or WxHxC
        sf: scale factor
    Return:
        cropped image
    """
    w, h = img.shape[:2]
    im = np.copy(img)
    return im[:w - w % sf, :h - h % sf, ...]

def shift_pixel(x, sf, upper_left=True):
    """shift pixel for super-resolution with different scale factors
    Args:
        x: WxHxC or WxH
        sf: scale factor
        upper_left: shift direction
    """
    h, w = x.shape[:2]
    shift = (sf - 1) * 0.5
    xv, yv = (np.arange(0, w, 1.0), np.arange(0, h, 1.0))
    if upper_left:
        x1 = xv + shift
        y1 = yv + shift
    else:
        x1 = xv - shift
        y1 = yv - shift
    x1 = np.clip(x1, 0, w - 1)
    y1 = np.clip(y1, 0, h - 1)
    if x.ndim == 2:
        x = interp2d(xv, yv, x)(x1, y1)
    if x.ndim == 3:
        for i in range(x.shape[-1]):
            x[:, :, i] = interp2d(xv, yv, x[:, :, i])(x1, y1)
    return x

def bicubic_degradation(x, sf=3):
    """
    Args:
        x: HxWxC image, [0, 1]
        sf: down-scale factor
    Return:
        bicubicly downsampled LR image
    """
    x = util.imresize_np(x, scale=1 / sf)
    return x

def srmd_degradation(x, k, sf=3):
    """ blur + bicubic downsampling
    Args:
        x: HxWxC image, [0, 1]
        k: hxw, double
        sf: down-scale factor
    Return:
        downsampled LR image
    Reference:
        @inproceedings{zhang2018learning,
          title={Learning a single convolutional super-resolution network for multiple degradations},
          author={Zhang, Kai and Zuo, Wangmeng and Zhang, Lei},
          booktitle={IEEE Conference on Computer Vision and Pattern Recognition},
          pages={3262--3271},
          year={2018}
        }
    """
    x = ndimage.filters.convolve(x, np.expand_dims(k, axis=2), mode='wrap')
    x = bicubic_degradation(x, sf=sf)
    return x

def dpsr_degradation(x, k, sf=3):
    """ bicubic downsampling + blur
    Args:
        x: HxWxC image, [0, 1]
        k: hxw, double
        sf: down-scale factor
    Return:
        downsampled LR image
    Reference:
        @inproceedings{zhang2019deep,
          title={Deep Plug-and-Play Super-Resolution for Arbitrary Blur Kernels},
          author={Zhang, Kai and Zuo, Wangmeng and Zhang, Lei},
          booktitle={IEEE Conference on Computer Vision and Pattern Recognition},
          pages={1671--1681},
          year={2019}
        }
    """
    x = bicubic_degradation(x, sf=sf)
    x = ndimage.filters.convolve(x, np.expand_dims(k, axis=2), mode='wrap')
    return x

def classical_degradation(x, k, sf=3):
    """ blur + downsampling
    Args:
        x: HxWxC image, [0, 1]/[0, 255]
        k: hxw, double
        sf: down-scale factor
    Return:
        downsampled LR image
    """
    x = ndimage.filters.convolve(x, np.expand_dims(k, axis=2), mode='wrap')
    st = 0
    return x[st::sf, st::sf, ...]

def add_sharpening(img, weight=0.5, radius=50, threshold=10):
    """USM sharpening. borrowed from real-ESRGAN
    Input image: I; Blurry image: B.
    1. K = I + weight * (I - B)
    2. Mask = 1 if abs(I - B) > threshold, else: 0
    3. Blur mask:
    4. Out = Mask * K + (1 - Mask) * I
    Args:
        img (Numpy array): Input image, HWC, BGR; float32, [0, 1].
        weight (float): Sharp weight. Default: 1.
        radius (float): Kernel size of Gaussian blur. Default: 50.
        threshold (int):
    """
    if radius % 2 == 0:
        radius += 1
    blur = cv2.GaussianBlur(img, (radius, radius), 0)
    residual = img - blur
    mask = np.abs(residual) * 255 > threshold
    mask = mask.astype('float32')
    soft_mask = cv2.GaussianBlur(mask, (radius, radius), 0)
    K = img + weight * residual
    K = np.clip(K, 0, 1)
    return soft_mask * K + (1 - soft_mask) * img

def add_blur(img, sf=4):
    wd2 = 4.0 + sf
    wd = 2.0 + 0.2 * sf
    wd2 = wd2 / 4
    wd = wd / 4
    if random.random() < 0.5:
        l1 = wd2 * random.random()
        l2 = wd2 * random.random()
        k = anisotropic_Gaussian(ksize=random.randint(2, 11) + 3, theta=random.random() * np.pi, l1=l1, l2=l2)
    else:
        k = fspecial('gaussian', random.randint(2, 4) + 3, wd * random.random())
    img = ndimage.filters.convolve(img, np.expand_dims(k, axis=2), mode='mirror')
    return img

def add_resize(img, sf=4):
    rnum = np.random.rand()
    if rnum > 0.8:
        sf1 = random.uniform(1, 2)
    elif rnum < 0.7:
        sf1 = random.uniform(0.5 / sf, 1)
    else:
        sf1 = 1.0
    img = cv2.resize(img, (int(sf1 * img.shape[1]), int(sf1 * img.shape[0])), interpolation=random.choice([1, 2, 3]))
    img = np.clip(img, 0.0, 1.0)
    return img

def add_Gaussian_noise(img, noise_level1=2, noise_level2=25):
    noise_level = random.randint(noise_level1, noise_level2)
    rnum = np.random.rand()
    if rnum > 0.6:
        img = img + np.random.normal(0, noise_level / 255.0, img.shape).astype(np.float32)
    elif rnum < 0.4:
        img = img + np.random.normal(0, noise_level / 255.0, (*img.shape[:2], 1)).astype(np.float32)
    else:
        L = noise_level2 / 255.0
        D = np.diag(np.random.rand(3))
        U = orth(np.random.rand(3, 3))
        conv = np.dot(np.dot(np.transpose(U), D), U)
        img = img + np.random.multivariate_normal([0, 0, 0], np.abs(L ** 2 * conv), img.shape[:2]).astype(np.float32)
    img = np.clip(img, 0.0, 1.0)
    return img

def add_speckle_noise(img, noise_level1=2, noise_level2=25):
    noise_level = random.randint(noise_level1, noise_level2)
    img = np.clip(img, 0.0, 1.0)
    rnum = random.random()
    if rnum > 0.6:
        img += img * np.random.normal(0, noise_level / 255.0, img.shape).astype(np.float32)
    elif rnum < 0.4:
        img += img * np.random.normal(0, noise_level / 255.0, (*img.shape[:2], 1)).astype(np.float32)
    else:
        L = noise_level2 / 255.0
        D = np.diag(np.random.rand(3))
        U = orth(np.random.rand(3, 3))
        conv = np.dot(np.dot(np.transpose(U), D), U)
        img += img * np.random.multivariate_normal([0, 0, 0], np.abs(L ** 2 * conv), img.shape[:2]).astype(np.float32)
    img = np.clip(img, 0.0, 1.0)
    return img

def add_Poisson_noise(img):
    img = np.clip((img * 255.0).round(), 0, 255) / 255.0
    vals = 10 ** (2 * random.random() + 2.0)
    if random.random() < 0.5:
        img = np.random.poisson(img * vals).astype(np.float32) / vals
    else:
        img_gray = np.dot(img[..., :3], [0.299, 0.587, 0.114])
        img_gray = np.clip((img_gray * 255.0).round(), 0, 255) / 255.0
        noise_gray = np.random.poisson(img_gray * vals).astype(np.float32) / vals - img_gray
        img += noise_gray[:, :, np.newaxis]
    img = np.clip(img, 0.0, 1.0)
    return img

def add_JPEG_noise(img):
    quality_factor = random.randint(80, 95)
    img = cv2.cvtColor(util.single2uint(img), cv2.COLOR_RGB2BGR)
    result, encimg = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), quality_factor])
    img = cv2.imdecode(encimg, 1)
    img = cv2.cvtColor(util.uint2single(img), cv2.COLOR_BGR2RGB)
    return img

def degradation_bsrgan(img, sf=4, lq_patchsize=72, isp_model=None):
    """
    This is the degradation model of BSRGAN from the paper
    "Designing a Practical Degradation Model for Deep Blind Image Super-Resolution"
    ----------
    img: HXWXC, [0, 1], its size should be large than (lq_patchsizexsf)x(lq_patchsizexsf)
    sf: scale factor
    isp_model: camera ISP model
    Returns
    -------
    img: low-quality patch, size: lq_patchsizeXlq_patchsizeXC, range: [0, 1]
    hq: corresponding high-quality patch, size: (lq_patchsizexsf)X(lq_patchsizexsf)XC, range: [0, 1]
    """
    isp_prob, jpeg_prob, scale2_prob = (0.25, 0.9, 0.25)
    sf_ori = sf
    h1, w1 = img.shape[:2]
    img = img.copy()[:w1 - w1 % sf, :h1 - h1 % sf, ...]
    h, w = img.shape[:2]
    if h < lq_patchsize * sf or w < lq_patchsize * sf:
        raise ValueError(f'img size ({h1}X{w1}) is too small!')
    hq = img.copy()
    if sf == 4 and random.random() < scale2_prob:
        if np.random.rand() < 0.5:
            img = cv2.resize(img, (int(1 / 2 * img.shape[1]), int(1 / 2 * img.shape[0])), interpolation=random.choice([1, 2, 3]))
        else:
            img = util.imresize_np(img, 1 / 2, True)
        img = np.clip(img, 0.0, 1.0)
        sf = 2
    shuffle_order = random.sample(range(7), 7)
    idx1, idx2 = (shuffle_order.index(2), shuffle_order.index(3))
    if idx1 > idx2:
        shuffle_order[idx1], shuffle_order[idx2] = (shuffle_order[idx2], shuffle_order[idx1])
    for i in shuffle_order:
        if i == 0:
            img = add_blur(img, sf=sf)
        elif i == 1:
            img = add_blur(img, sf=sf)
        elif i == 2:
            a, b = (img.shape[1], img.shape[0])
            if random.random() < 0.75:
                sf1 = random.uniform(1, 2 * sf)
                img = cv2.resize(img, (int(1 / sf1 * img.shape[1]), int(1 / sf1 * img.shape[0])), interpolation=random.choice([1, 2, 3]))
            else:
                k = fspecial('gaussian', 25, random.uniform(0.1, 0.6 * sf))
                k_shifted = shift_pixel(k, sf)
                k_shifted = k_shifted / k_shifted.sum()
                img = ndimage.filters.convolve(img, np.expand_dims(k_shifted, axis=2), mode='mirror')
                img = img[0::sf, 0::sf, ...]
            img = np.clip(img, 0.0, 1.0)
        elif i == 3:
            img = cv2.resize(img, (int(1 / sf * a), int(1 / sf * b)), interpolation=random.choice([1, 2, 3]))
            img = np.clip(img, 0.0, 1.0)
        elif i == 4:
            img = add_Gaussian_noise(img, noise_level1=2, noise_level2=8)
        elif i == 5:
            if random.random() < jpeg_prob:
                img = add_JPEG_noise(img)
        elif i == 6:
            if random.random() < isp_prob and isp_model is not None:
                with torch.no_grad():
                    img, hq = isp_model.forward(img.copy(), hq)
    img = add_JPEG_noise(img)
    img, hq = random_crop(img, hq, sf_ori, lq_patchsize)
    return (img, hq)

def degradation_bsrgan_variant(image, sf=4, isp_model=None):
    """
    This is the degradation model of BSRGAN from the paper
    "Designing a Practical Degradation Model for Deep Blind Image Super-Resolution"
    ----------
    sf: scale factor
    isp_model: camera ISP model
    Returns
    -------
    img: low-quality patch, size: lq_patchsizeXlq_patchsizeXC, range: [0, 1]
    hq: corresponding high-quality patch, size: (lq_patchsizexsf)X(lq_patchsizexsf)XC, range: [0, 1]
    """
    image = util.uint2single(image)
    isp_prob, jpeg_prob, scale2_prob = (0.25, 0.9, 0.25)
    sf_ori = sf
    h1, w1 = image.shape[:2]
    image = image.copy()[:w1 - w1 % sf, :h1 - h1 % sf, ...]
    h, w = image.shape[:2]
    hq = image.copy()
    if sf == 4 and random.random() < scale2_prob:
        if np.random.rand() < 0.5:
            image = cv2.resize(image, (int(1 / 2 * image.shape[1]), int(1 / 2 * image.shape[0])), interpolation=random.choice([1, 2, 3]))
        else:
            image = util.imresize_np(image, 1 / 2, True)
        image = np.clip(image, 0.0, 1.0)
        sf = 2
    shuffle_order = random.sample(range(7), 7)
    idx1, idx2 = (shuffle_order.index(2), shuffle_order.index(3))
    if idx1 > idx2:
        shuffle_order[idx1], shuffle_order[idx2] = (shuffle_order[idx2], shuffle_order[idx1])
    for i in shuffle_order:
        if i == 0:
            image = add_blur(image, sf=sf)
        if i == 0:
            pass
        elif i == 2:
            a, b = (image.shape[1], image.shape[0])
            if random.random() < 0.8:
                sf1 = random.uniform(1, 2 * sf)
                image = cv2.resize(image, (int(1 / sf1 * image.shape[1]), int(1 / sf1 * image.shape[0])), interpolation=random.choice([1, 2, 3]))
            else:
                k = fspecial('gaussian', 25, random.uniform(0.1, 0.6 * sf))
                k_shifted = shift_pixel(k, sf)
                k_shifted = k_shifted / k_shifted.sum()
                image = ndimage.filters.convolve(image, np.expand_dims(k_shifted, axis=2), mode='mirror')
                image = image[0::sf, 0::sf, ...]
            image = np.clip(image, 0.0, 1.0)
        elif i == 3:
            image = cv2.resize(image, (int(1 / sf * a), int(1 / sf * b)), interpolation=random.choice([1, 2, 3]))
            image = np.clip(image, 0.0, 1.0)
        elif i == 4:
            image = add_Gaussian_noise(image, noise_level1=1, noise_level2=2)
        elif i == 5:
            if random.random() < jpeg_prob:
                image = add_JPEG_noise(image)
    image = add_JPEG_noise(image)
    image = util.single2uint(image)
    example = {'image': image}
    return example

def imread_uint(path, n_channels=3):
    if n_channels == 1:
        img = cv2.imread(path, 0)
        img = np.expand_dims(img, axis=2)
    elif n_channels == 3:
        img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        if img.ndim == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        else:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return img

def read_img(path):
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    img = img.astype(np.float32) / 255.0
    if img.ndim == 2:
        img = np.expand_dims(img, axis=2)
    if img.shape[2] > 3:
        img = img[:, :, :3]
    return img

def single2uint(img):
    return np.uint8((img.clip(0, 1) * 255.0).round())

def single2uint16(img):
    return np.uint16((img.clip(0, 1) * 65535.0).round())

def augment_img_np3(img, mode=0):
    if mode == 0:
        return img
    elif mode == 1:
        return img.transpose(1, 0, 2)
    elif mode == 2:
        return img[::-1, :, :]
    elif mode == 3:
        img = img[::-1, :, :]
        img = img.transpose(1, 0, 2)
        return img
    elif mode == 4:
        return img[:, ::-1, :]
    elif mode == 5:
        img = img[:, ::-1, :]
        img = img.transpose(1, 0, 2)
        return img
    elif mode == 6:
        img = img[:, ::-1, :]
        img = img[::-1, :, :]
        return img
    elif mode == 7:
        img = img[:, ::-1, :]
        img = img[::-1, :, :]
        img = img.transpose(1, 0, 2)
        return img

def augment_imgs(img_list, hflip=True, rot=True):
    hflip = hflip and random.random() < 0.5
    vflip = rot and random.random() < 0.5
    rot90 = rot and random.random() < 0.5

    def _augment(img):
        if hflip:
            img = img[:, ::-1, :]
        if vflip:
            img = img[::-1, :, :]
        if rot90:
            img = img.transpose(1, 0, 2)
        return img
    return [_augment(img) for img in img_list]

def _augment(img):
    if hflip:
        img = img[:, ::-1, :]
    if vflip:
        img = img[::-1, :, :]
    if rot90:
        img = img.transpose(1, 0, 2)
    return img

def modcrop(img_in, scale):
    img = np.copy(img_in)
    if img.ndim == 2:
        H, W = img.shape
        H_r, W_r = (H % scale, W % scale)
        img = img[:H - H_r, :W - W_r]
    elif img.ndim == 3:
        H, W, C = img.shape
        H_r, W_r = (H % scale, W % scale)
        img = img[:H - H_r, :W - W_r, :]
    else:
        raise ValueError('Wrong img ndim: [{:d}].'.format(img.ndim))
    return img

def shave(img_in, border=0):
    img = np.copy(img_in)
    h, w = img.shape[:2]
    img = img[border:h - border, border:w - border]
    return img

def rgb2ycbcr(img, only_y=True):
    """same as matlab rgb2ycbcr
    only_y: only return Y channel
    Input:
        uint8, [0, 255]
        float, [0, 1]
    """
    in_img_type = img.dtype
    img.astype(np.float32)
    if in_img_type != np.uint8:
        img *= 255.0
    if only_y:
        rlt = np.dot(img, [65.481, 128.553, 24.966]) / 255.0 + 16.0
    else:
        rlt = np.matmul(img, [[65.481, -37.797, 112.0], [128.553, -74.203, -93.786], [24.966, 112.0, -18.214]]) / 255.0 + [16, 128, 128]
    if in_img_type == np.uint8:
        rlt = rlt.round()
    else:
        rlt /= 255.0
    return rlt.astype(in_img_type)

def ycbcr2rgb(img):
    """same as matlab ycbcr2rgb
    Input:
        uint8, [0, 255]
        float, [0, 1]
    """
    in_img_type = img.dtype
    img.astype(np.float32)
    if in_img_type != np.uint8:
        img *= 255.0
    rlt = np.matmul(img, [[0.00456621, 0.00456621, 0.00456621], [0, -0.00153632, 0.00791071], [0.00625893, -0.00318811, 0]]) * 255.0 + [-222.921, 135.576, -276.836]
    if in_img_type == np.uint8:
        rlt = rlt.round()
    else:
        rlt /= 255.0
    return rlt.astype(in_img_type)

def bgr2ycbcr(img, only_y=True):
    """bgr version of rgb2ycbcr
    only_y: only return Y channel
    Input:
        uint8, [0, 255]
        float, [0, 1]
    """
    in_img_type = img.dtype
    img.astype(np.float32)
    if in_img_type != np.uint8:
        img *= 255.0
    if only_y:
        rlt = np.dot(img, [24.966, 128.553, 65.481]) / 255.0 + 16.0
    else:
        rlt = np.matmul(img, [[24.966, 112.0, -18.214], [128.553, -74.203, -93.786], [65.481, -37.797, 112.0]]) / 255.0 + [16, 128, 128]
    if in_img_type == np.uint8:
        rlt = rlt.round()
    else:
        rlt /= 255.0
    return rlt.astype(in_img_type)

def channel_convert(in_c, tar_type, img_list):
    if in_c == 3 and tar_type == 'gray':
        gray_list = [cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) for img in img_list]
        return [np.expand_dims(img, axis=2) for img in gray_list]
    elif in_c == 3 and tar_type == 'y':
        y_list = [bgr2ycbcr(img, only_y=True) for img in img_list]
        return [np.expand_dims(img, axis=2) for img in y_list]
    elif in_c == 1 and tar_type == 'RGB':
        return [cv2.cvtColor(img, cv2.COLOR_GRAY2BGR) for img in img_list]
    else:
        return img_list

def ssim(img1, img2):
    C1 = (0.01 * 255) ** 2
    C2 = (0.03 * 255) ** 2
    img1 = img1.astype(np.float64)
    img2 = img2.astype(np.float64)
    kernel = cv2.getGaussianKernel(11, 1.5)
    window = np.outer(kernel, kernel.transpose())
    mu1 = cv2.filter2D(img1, -1, window)[5:-5, 5:-5]
    mu2 = cv2.filter2D(img2, -1, window)[5:-5, 5:-5]
    mu1_sq = mu1 ** 2
    mu2_sq = mu2 ** 2
    mu1_mu2 = mu1 * mu2
    sigma1_sq = cv2.filter2D(img1 ** 2, -1, window)[5:-5, 5:-5] - mu1_sq
    sigma2_sq = cv2.filter2D(img2 ** 2, -1, window)[5:-5, 5:-5] - mu2_sq
    sigma12 = cv2.filter2D(img1 * img2, -1, window)[5:-5, 5:-5] - mu1_mu2
    ssim_map = (2 * mu1_mu2 + C1) * (2 * sigma12 + C2) / ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
    return ssim_map.mean()

def modcrop_np(img, sf):
    """
    Args:
        img: numpy image, WxH or WxHxC
        sf: scale factor
    Return:
        cropped image
    """
    w, h = img.shape[:2]
    im = np.copy(img)
    return im[:w - w % sf, :h - h % sf, ...]

def shift_pixel(x, sf, upper_left=True):
    """shift pixel for super-resolution with different scale factors
    Args:
        x: WxHxC or WxH
        sf: scale factor
        upper_left: shift direction
    """
    h, w = x.shape[:2]
    shift = (sf - 1) * 0.5
    xv, yv = (np.arange(0, w, 1.0), np.arange(0, h, 1.0))
    if upper_left:
        x1 = xv + shift
        y1 = yv + shift
    else:
        x1 = xv - shift
        y1 = yv - shift
    x1 = np.clip(x1, 0, w - 1)
    y1 = np.clip(y1, 0, h - 1)
    if x.ndim == 2:
        x = interp2d(xv, yv, x)(x1, y1)
    if x.ndim == 3:
        for i in range(x.shape[-1]):
            x[:, :, i] = interp2d(xv, yv, x[:, :, i])(x1, y1)
    return x

def bicubic_degradation(x, sf=3):
    """
    Args:
        x: HxWxC image, [0, 1]
        sf: down-scale factor
    Return:
        bicubicly downsampled LR image
    """
    x = util.imresize_np(x, scale=1 / sf)
    return x

def srmd_degradation(x, k, sf=3):
    """ blur + bicubic downsampling
    Args:
        x: HxWxC image, [0, 1]
        k: hxw, double
        sf: down-scale factor
    Return:
        downsampled LR image
    Reference:
        @inproceedings{zhang2018learning,
          title={Learning a single convolutional super-resolution network for multiple degradations},
          author={Zhang, Kai and Zuo, Wangmeng and Zhang, Lei},
          booktitle={IEEE Conference on Computer Vision and Pattern Recognition},
          pages={3262--3271},
          year={2018}
        }
    """
    x = ndimage.filters.convolve(x, np.expand_dims(k, axis=2), mode='wrap')
    x = bicubic_degradation(x, sf=sf)
    return x

def dpsr_degradation(x, k, sf=3):
    """ bicubic downsampling + blur
    Args:
        x: HxWxC image, [0, 1]
        k: hxw, double
        sf: down-scale factor
    Return:
        downsampled LR image
    Reference:
        @inproceedings{zhang2019deep,
          title={Deep Plug-and-Play Super-Resolution for Arbitrary Blur Kernels},
          author={Zhang, Kai and Zuo, Wangmeng and Zhang, Lei},
          booktitle={IEEE Conference on Computer Vision and Pattern Recognition},
          pages={1671--1681},
          year={2019}
        }
    """
    x = bicubic_degradation(x, sf=sf)
    x = ndimage.filters.convolve(x, np.expand_dims(k, axis=2), mode='wrap')
    return x

def classical_degradation(x, k, sf=3):
    """ blur + downsampling
    Args:
        x: HxWxC image, [0, 1]/[0, 255]
        k: hxw, double
        sf: down-scale factor
    Return:
        downsampled LR image
    """
    x = ndimage.filters.convolve(x, np.expand_dims(k, axis=2), mode='wrap')
    st = 0
    return x[st::sf, st::sf, ...]

def add_sharpening(img, weight=0.5, radius=50, threshold=10):
    """USM sharpening. borrowed from real-ESRGAN
    Input image: I; Blurry image: B.
    1. K = I + weight * (I - B)
    2. Mask = 1 if abs(I - B) > threshold, else: 0
    3. Blur mask:
    4. Out = Mask * K + (1 - Mask) * I
    Args:
        img (Numpy array): Input image, HWC, BGR; float32, [0, 1].
        weight (float): Sharp weight. Default: 1.
        radius (float): Kernel size of Gaussian blur. Default: 50.
        threshold (int):
    """
    if radius % 2 == 0:
        radius += 1
    blur = cv2.GaussianBlur(img, (radius, radius), 0)
    residual = img - blur
    mask = np.abs(residual) * 255 > threshold
    mask = mask.astype('float32')
    soft_mask = cv2.GaussianBlur(mask, (radius, radius), 0)
    K = img + weight * residual
    K = np.clip(K, 0, 1)
    return soft_mask * K + (1 - soft_mask) * img

def add_blur(img, sf=4):
    wd2 = 4.0 + sf
    wd = 2.0 + 0.2 * sf
    if random.random() < 0.5:
        l1 = wd2 * random.random()
        l2 = wd2 * random.random()
        k = anisotropic_Gaussian(ksize=2 * random.randint(2, 11) + 3, theta=random.random() * np.pi, l1=l1, l2=l2)
    else:
        k = fspecial('gaussian', 2 * random.randint(2, 11) + 3, wd * random.random())
    img = ndimage.filters.convolve(img, np.expand_dims(k, axis=2), mode='mirror')
    return img

def add_resize(img, sf=4):
    rnum = np.random.rand()
    if rnum > 0.8:
        sf1 = random.uniform(1, 2)
    elif rnum < 0.7:
        sf1 = random.uniform(0.5 / sf, 1)
    else:
        sf1 = 1.0
    img = cv2.resize(img, (int(sf1 * img.shape[1]), int(sf1 * img.shape[0])), interpolation=random.choice([1, 2, 3]))
    img = np.clip(img, 0.0, 1.0)
    return img

def add_Gaussian_noise(img, noise_level1=2, noise_level2=25):
    noise_level = random.randint(noise_level1, noise_level2)
    rnum = np.random.rand()
    if rnum > 0.6:
        img = img + np.random.normal(0, noise_level / 255.0, img.shape).astype(np.float32)
    elif rnum < 0.4:
        img = img + np.random.normal(0, noise_level / 255.0, (*img.shape[:2], 1)).astype(np.float32)
    else:
        L = noise_level2 / 255.0
        D = np.diag(np.random.rand(3))
        U = orth(np.random.rand(3, 3))
        conv = np.dot(np.dot(np.transpose(U), D), U)
        img = img + np.random.multivariate_normal([0, 0, 0], np.abs(L ** 2 * conv), img.shape[:2]).astype(np.float32)
    img = np.clip(img, 0.0, 1.0)
    return img

def add_speckle_noise(img, noise_level1=2, noise_level2=25):
    noise_level = random.randint(noise_level1, noise_level2)
    img = np.clip(img, 0.0, 1.0)
    rnum = random.random()
    if rnum > 0.6:
        img += img * np.random.normal(0, noise_level / 255.0, img.shape).astype(np.float32)
    elif rnum < 0.4:
        img += img * np.random.normal(0, noise_level / 255.0, (*img.shape[:2], 1)).astype(np.float32)
    else:
        L = noise_level2 / 255.0
        D = np.diag(np.random.rand(3))
        U = orth(np.random.rand(3, 3))
        conv = np.dot(np.dot(np.transpose(U), D), U)
        img += img * np.random.multivariate_normal([0, 0, 0], np.abs(L ** 2 * conv), img.shape[:2]).astype(np.float32)
    img = np.clip(img, 0.0, 1.0)
    return img

def add_Poisson_noise(img):
    img = np.clip((img * 255.0).round(), 0, 255) / 255.0
    vals = 10 ** (2 * random.random() + 2.0)
    if random.random() < 0.5:
        img = np.random.poisson(img * vals).astype(np.float32) / vals
    else:
        img_gray = np.dot(img[..., :3], [0.299, 0.587, 0.114])
        img_gray = np.clip((img_gray * 255.0).round(), 0, 255) / 255.0
        noise_gray = np.random.poisson(img_gray * vals).astype(np.float32) / vals - img_gray
        img += noise_gray[:, :, np.newaxis]
    img = np.clip(img, 0.0, 1.0)
    return img

def add_JPEG_noise(img):
    quality_factor = random.randint(30, 95)
    img = cv2.cvtColor(util.single2uint(img), cv2.COLOR_RGB2BGR)
    result, encimg = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), quality_factor])
    img = cv2.imdecode(encimg, 1)
    img = cv2.cvtColor(util.uint2single(img), cv2.COLOR_BGR2RGB)
    return img

def degradation_bsrgan(img, sf=4, lq_patchsize=72, isp_model=None):
    """
    This is the degradation model of BSRGAN from the paper
    "Designing a Practical Degradation Model for Deep Blind Image Super-Resolution"
    ----------
    img: HXWXC, [0, 1], its size should be large than (lq_patchsizexsf)x(lq_patchsizexsf)
    sf: scale factor
    isp_model: camera ISP model
    Returns
    -------
    img: low-quality patch, size: lq_patchsizeXlq_patchsizeXC, range: [0, 1]
    hq: corresponding high-quality patch, size: (lq_patchsizexsf)X(lq_patchsizexsf)XC, range: [0, 1]
    """
    isp_prob, jpeg_prob, scale2_prob = (0.25, 0.9, 0.25)
    sf_ori = sf
    h1, w1 = img.shape[:2]
    img = img.copy()[:w1 - w1 % sf, :h1 - h1 % sf, ...]
    h, w = img.shape[:2]
    if h < lq_patchsize * sf or w < lq_patchsize * sf:
        raise ValueError(f'img size ({h1}X{w1}) is too small!')
    hq = img.copy()
    if sf == 4 and random.random() < scale2_prob:
        if np.random.rand() < 0.5:
            img = cv2.resize(img, (int(1 / 2 * img.shape[1]), int(1 / 2 * img.shape[0])), interpolation=random.choice([1, 2, 3]))
        else:
            img = util.imresize_np(img, 1 / 2, True)
        img = np.clip(img, 0.0, 1.0)
        sf = 2
    shuffle_order = random.sample(range(7), 7)
    idx1, idx2 = (shuffle_order.index(2), shuffle_order.index(3))
    if idx1 > idx2:
        shuffle_order[idx1], shuffle_order[idx2] = (shuffle_order[idx2], shuffle_order[idx1])
    for i in shuffle_order:
        if i == 0:
            img = add_blur(img, sf=sf)
        elif i == 1:
            img = add_blur(img, sf=sf)
        elif i == 2:
            a, b = (img.shape[1], img.shape[0])
            if random.random() < 0.75:
                sf1 = random.uniform(1, 2 * sf)
                img = cv2.resize(img, (int(1 / sf1 * img.shape[1]), int(1 / sf1 * img.shape[0])), interpolation=random.choice([1, 2, 3]))
            else:
                k = fspecial('gaussian', 25, random.uniform(0.1, 0.6 * sf))
                k_shifted = shift_pixel(k, sf)
                k_shifted = k_shifted / k_shifted.sum()
                img = ndimage.filters.convolve(img, np.expand_dims(k_shifted, axis=2), mode='mirror')
                img = img[0::sf, 0::sf, ...]
            img = np.clip(img, 0.0, 1.0)
        elif i == 3:
            img = cv2.resize(img, (int(1 / sf * a), int(1 / sf * b)), interpolation=random.choice([1, 2, 3]))
            img = np.clip(img, 0.0, 1.0)
        elif i == 4:
            img = add_Gaussian_noise(img, noise_level1=2, noise_level2=25)
        elif i == 5:
            if random.random() < jpeg_prob:
                img = add_JPEG_noise(img)
        elif i == 6:
            if random.random() < isp_prob and isp_model is not None:
                with torch.no_grad():
                    img, hq = isp_model.forward(img.copy(), hq)
    img = add_JPEG_noise(img)
    img, hq = random_crop(img, hq, sf_ori, lq_patchsize)
    return (img, hq)

def degradation_bsrgan_variant(image, sf=4, isp_model=None):
    """
    This is the degradation model of BSRGAN from the paper
    "Designing a Practical Degradation Model for Deep Blind Image Super-Resolution"
    ----------
    sf: scale factor
    isp_model: camera ISP model
    Returns
    -------
    img: low-quality patch, size: lq_patchsizeXlq_patchsizeXC, range: [0, 1]
    hq: corresponding high-quality patch, size: (lq_patchsizexsf)X(lq_patchsizexsf)XC, range: [0, 1]
    """
    image = util.uint2single(image)
    isp_prob, jpeg_prob, scale2_prob = (0.25, 0.9, 0.25)
    sf_ori = sf
    h1, w1 = image.shape[:2]
    image = image.copy()[:w1 - w1 % sf, :h1 - h1 % sf, ...]
    h, w = image.shape[:2]
    hq = image.copy()
    if sf == 4 and random.random() < scale2_prob:
        if np.random.rand() < 0.5:
            image = cv2.resize(image, (int(1 / 2 * image.shape[1]), int(1 / 2 * image.shape[0])), interpolation=random.choice([1, 2, 3]))
        else:
            image = util.imresize_np(image, 1 / 2, True)
        image = np.clip(image, 0.0, 1.0)
        sf = 2
    shuffle_order = random.sample(range(7), 7)
    idx1, idx2 = (shuffle_order.index(2), shuffle_order.index(3))
    if idx1 > idx2:
        shuffle_order[idx1], shuffle_order[idx2] = (shuffle_order[idx2], shuffle_order[idx1])
    for i in shuffle_order:
        if i == 0:
            image = add_blur(image, sf=sf)
        elif i == 1:
            image = add_blur(image, sf=sf)
        elif i == 2:
            a, b = (image.shape[1], image.shape[0])
            if random.random() < 0.75:
                sf1 = random.uniform(1, 2 * sf)
                image = cv2.resize(image, (int(1 / sf1 * image.shape[1]), int(1 / sf1 * image.shape[0])), interpolation=random.choice([1, 2, 3]))
            else:
                k = fspecial('gaussian', 25, random.uniform(0.1, 0.6 * sf))
                k_shifted = shift_pixel(k, sf)
                k_shifted = k_shifted / k_shifted.sum()
                image = ndimage.filters.convolve(image, np.expand_dims(k_shifted, axis=2), mode='mirror')
                image = image[0::sf, 0::sf, ...]
            image = np.clip(image, 0.0, 1.0)
        elif i == 3:
            image = cv2.resize(image, (int(1 / sf * a), int(1 / sf * b)), interpolation=random.choice([1, 2, 3]))
            image = np.clip(image, 0.0, 1.0)
        elif i == 4:
            image = add_Gaussian_noise(image, noise_level1=2, noise_level2=25)
        elif i == 5:
            if random.random() < jpeg_prob:
                image = add_JPEG_noise(image)
    image = add_JPEG_noise(image)
    image = util.single2uint(image)
    example = {'image': image}
    return example

def degradation_bsrgan_plus(img, sf=4, shuffle_prob=0.5, use_sharp=True, lq_patchsize=64, isp_model=None):
    """
    This is an extended degradation model by combining
    the degradation models of BSRGAN and Real-ESRGAN
    ----------
    img: HXWXC, [0, 1], its size should be large than (lq_patchsizexsf)x(lq_patchsizexsf)
    sf: scale factor
    use_shuffle: the degradation shuffle
    use_sharp: sharpening the img
    Returns
    -------
    img: low-quality patch, size: lq_patchsizeXlq_patchsizeXC, range: [0, 1]
    hq: corresponding high-quality patch, size: (lq_patchsizexsf)X(lq_patchsizexsf)XC, range: [0, 1]
    """
    h1, w1 = img.shape[:2]
    img = img.copy()[:w1 - w1 % sf, :h1 - h1 % sf, ...]
    h, w = img.shape[:2]
    if h < lq_patchsize * sf or w < lq_patchsize * sf:
        raise ValueError(f'img size ({h1}X{w1}) is too small!')
    if use_sharp:
        img = add_sharpening(img)
    hq = img.copy()
    if random.random() < shuffle_prob:
        shuffle_order = random.sample(range(13), 13)
    else:
        shuffle_order = list(range(13))
        shuffle_order[2:6] = random.sample(shuffle_order[2:6], len(range(2, 6)))
        shuffle_order[9:13] = random.sample(shuffle_order[9:13], len(range(9, 13)))
    poisson_prob, speckle_prob, isp_prob = (0.1, 0.1, 0.1)
    for i in shuffle_order:
        if i == 0:
            img = add_blur(img, sf=sf)
        elif i == 1:
            img = add_resize(img, sf=sf)
        elif i == 2:
            img = add_Gaussian_noise(img, noise_level1=2, noise_level2=25)
        elif i == 3:
            if random.random() < poisson_prob:
                img = add_Poisson_noise(img)
        elif i == 4:
            if random.random() < speckle_prob:
                img = add_speckle_noise(img)
        elif i == 5:
            if random.random() < isp_prob and isp_model is not None:
                with torch.no_grad():
                    img, hq = isp_model.forward(img.copy(), hq)
        elif i == 6:
            img = add_JPEG_noise(img)
        elif i == 7:
            img = add_blur(img, sf=sf)
        elif i == 8:
            img = add_resize(img, sf=sf)
        elif i == 9:
            img = add_Gaussian_noise(img, noise_level1=2, noise_level2=25)
        elif i == 10:
            if random.random() < poisson_prob:
                img = add_Poisson_noise(img)
        elif i == 11:
            if random.random() < speckle_prob:
                img = add_speckle_noise(img)
        elif i == 12:
            if random.random() < isp_prob and isp_model is not None:
                with torch.no_grad():
                    img, hq = isp_model.forward(img.copy(), hq)
        else:
            print('check the shuffle!')
    img = cv2.resize(img, (int(1 / sf * hq.shape[1]), int(1 / sf * hq.shape[0])), interpolation=random.choice([1, 2, 3]))
    img = add_JPEG_noise(img)
    img, hq = random_crop(img, hq, sf, lq_patchsize)
    return (img, hq)

class FrozenClipImageEmbedder(nn.Module):
    """
        Uses the CLIP image encoder.
        """

    def __init__(self, model, jit=False, device='cuda' if torch.cuda.is_available() else 'cpu', antialias=False):
        super().__init__()
        self.model, _ = clip.load(name=model, device=device, jit=jit)
        self.antialias = antialias
        self.register_buffer('mean', torch.Tensor([0.48145466, 0.4578275, 0.40821073]), persistent=False)
        self.register_buffer('std', torch.Tensor([0.26862954, 0.26130258, 0.27577711]), persistent=False)

    def preprocess(self, x):
        x = kornia.geometry.resize(x, (224, 224), interpolation='bicubic', align_corners=True, antialias=self.antialias)
        x = (x + 1.0) / 2.0
        x = kornia.enhance.normalize(x, self.mean, self.std)
        return x

    def forward(self, x):
        return self.model.encode_image(self.preprocess(x))

def preprocess(self, x):
    x = kornia.geometry.resize(x, (224, 224), interpolation='bicubic', align_corners=True, antialias=self.antialias)
    x = (x + 1.0) / 2.0
    x = kornia.enhance.normalize(x, self.mean, self.std)
    return x

class LatentDiffusion(DDPM):
    """main class"""

    def __init__(self, first_stage_config, cond_stage_config, num_timesteps_cond=None, cond_stage_key='image', cond_stage_trainable=False, concat_mode=True, cond_stage_forward=None, conditioning_key=None, scale_factor=1.0, scale_by_std=False, *args, **kwargs):
        self.num_timesteps_cond = default(num_timesteps_cond, 1)
        self.scale_by_std = scale_by_std
        assert self.num_timesteps_cond <= kwargs['timesteps']
        if conditioning_key is None:
            conditioning_key = 'concat' if concat_mode else 'crossattn'
        if cond_stage_config == '__is_unconditional__':
            conditioning_key = None
        ckpt_path = kwargs.pop('ckpt_path', None)
        ignore_keys = kwargs.pop('ignore_keys', [])
        super().__init__(*args, conditioning_key=conditioning_key, **kwargs)
        self.concat_mode = concat_mode
        self.cond_stage_trainable = cond_stage_trainable
        self.cond_stage_key = cond_stage_key
        try:
            self.num_downs = len(first_stage_config.params.ddconfig.ch_mult) - 1
        except:
            self.num_downs = 0
        if not scale_by_std:
            self.scale_factor = scale_factor
        else:
            self.register_buffer('scale_factor', torch.tensor(scale_factor))
        self.instantiate_first_stage(first_stage_config)
        self.instantiate_cond_stage(cond_stage_config)
        self.cond_stage_forward = cond_stage_forward
        self.clip_denoised = False
        self.bbox_tokenizer = None
        self.restarted_from_ckpt = False
        if ckpt_path is not None:
            self.init_from_ckpt(ckpt_path, ignore_keys)
            self.restarted_from_ckpt = True

    def make_cond_schedule(self):
        self.cond_ids = torch.full(size=(self.num_timesteps,), fill_value=self.num_timesteps - 1, dtype=torch.long)
        ids = torch.round(torch.linspace(0, self.num_timesteps - 1, self.num_timesteps_cond)).long()
        self.cond_ids[:self.num_timesteps_cond] = ids

    @rank_zero_only
    @torch.no_grad()
    def on_train_batch_start(self, batch, batch_idx, dataloader_idx):
        if self.scale_by_std and self.current_epoch == 0 and (self.global_step == 0) and (batch_idx == 0) and (not self.restarted_from_ckpt):
            assert self.scale_factor == 1.0, 'rather not use custom rescaling and std-rescaling simultaneously'
            print('### USING STD-RESCALING ###')
            x = super().get_input(batch, self.first_stage_key)
            x = x.to(self.device)
            encoder_posterior = self.encode_first_stage(x)
            z = self.get_first_stage_encoding(encoder_posterior).detach()
            del self.scale_factor
            self.register_buffer('scale_factor', 1.0 / z.flatten().std())
            print(f'setting self.scale_factor to {self.scale_factor}')
            print('### USING STD-RESCALING ###')

    def register_schedule(self, given_betas=None, beta_schedule='linear', timesteps=1000, linear_start=0.0001, linear_end=0.02, cosine_s=0.008):
        super().register_schedule(given_betas, beta_schedule, timesteps, linear_start, linear_end, cosine_s)
        self.shorten_cond_schedule = self.num_timesteps_cond > 1
        if self.shorten_cond_schedule:
            self.make_cond_schedule()

    def instantiate_first_stage(self, config):
        model = instantiate_from_config(config)
        self.first_stage_model = model.eval()
        self.first_stage_model.train = disabled_train
        for param in self.first_stage_model.parameters():
            param.requires_grad = False

    def instantiate_cond_stage(self, config):
        if not self.cond_stage_trainable:
            if config == '__is_first_stage__':
                print('Using first stage also as cond stage.')
                self.cond_stage_model = self.first_stage_model
            elif config == '__is_unconditional__':
                print(f'Training {self.__class__.__name__} as an unconditional model.')
                self.cond_stage_model = None
            else:
                model = instantiate_from_config(config)
                self.cond_stage_model = model.eval()
                self.cond_stage_model.train = disabled_train
                for param in self.cond_stage_model.parameters():
                    param.requires_grad = False
        else:
            assert config != '__is_first_stage__'
            assert config != '__is_unconditional__'
            model = instantiate_from_config(config)
            self.cond_stage_model = model

    def _get_denoise_row_from_list(self, samples, desc='', force_no_decoder_quantization=False):
        denoise_row = []
        for zd in tqdm(samples, desc=desc):
            denoise_row.append(self.decode_first_stage(zd.to(self.device), force_not_quantize=force_no_decoder_quantization))
        n_imgs_per_row = len(denoise_row)
        denoise_row = torch.stack(denoise_row)
        denoise_grid = rearrange(denoise_row, 'n b c h w -> b n c h w')
        denoise_grid = rearrange(denoise_grid, 'b n c h w -> (b n) c h w')
        denoise_grid = make_grid(denoise_grid, nrow=n_imgs_per_row)
        return denoise_grid

    def get_first_stage_encoding(self, encoder_posterior):
        if isinstance(encoder_posterior, DiagonalGaussianDistribution):
            z = encoder_posterior.sample()
        elif isinstance(encoder_posterior, torch.Tensor):
            z = encoder_posterior
        else:
            raise NotImplementedError(f"encoder_posterior of type '{type(encoder_posterior)}' not yet implemented")
        return self.scale_factor * z

    def get_learned_conditioning(self, c):
        if self.cond_stage_forward is None:
            if hasattr(self.cond_stage_model, 'encode') and callable(self.cond_stage_model.encode):
                c = self.cond_stage_model.encode(c)
                if isinstance(c, DiagonalGaussianDistribution):
                    c = c.mode()
            else:
                c = self.cond_stage_model(c)
        else:
            assert hasattr(self.cond_stage_model, self.cond_stage_forward)
            c = getattr(self.cond_stage_model, self.cond_stage_forward)(c)
        return c

    def meshgrid(self, h, w):
        y = torch.arange(0, h).view(h, 1, 1).repeat(1, w, 1)
        x = torch.arange(0, w).view(1, w, 1).repeat(h, 1, 1)
        arr = torch.cat([y, x], dim=-1)
        return arr

    def delta_border(self, h, w):
        """
        :param h: height
        :param w: width
        :return: normalized distance to image border,
         wtith min distance = 0 at border and max dist = 0.5 at image center
        """
        lower_right_corner = torch.tensor([h - 1, w - 1]).view(1, 1, 2)
        arr = self.meshgrid(h, w) / lower_right_corner
        dist_left_up = torch.min(arr, dim=-1, keepdims=True)[0]
        dist_right_down = torch.min(1 - arr, dim=-1, keepdims=True)[0]
        edge_dist = torch.min(torch.cat([dist_left_up, dist_right_down], dim=-1), dim=-1)[0]
        return edge_dist

    def get_weighting(self, h, w, Ly, Lx, device):
        weighting = self.delta_border(h, w)
        weighting = torch.clip(weighting, self.split_input_params['clip_min_weight'], self.split_input_params['clip_max_weight'])
        weighting = weighting.view(1, h * w, 1).repeat(1, 1, Ly * Lx).to(device)
        if self.split_input_params['tie_braker']:
            L_weighting = self.delta_border(Ly, Lx)
            L_weighting = torch.clip(L_weighting, self.split_input_params['clip_min_tie_weight'], self.split_input_params['clip_max_tie_weight'])
            L_weighting = L_weighting.view(1, 1, Ly * Lx).to(device)
            weighting = weighting * L_weighting
        return weighting

    def get_fold_unfold(self, x, kernel_size, stride, uf=1, df=1):
        """
        :param x: img of size (bs, c, h, w)
        :return: n img crops of size (n, bs, c, kernel_size[0], kernel_size[1])
        """
        bs, nc, h, w = x.shape
        Ly = (h - kernel_size[0]) // stride[0] + 1
        Lx = (w - kernel_size[1]) // stride[1] + 1
        if uf == 1 and df == 1:
            fold_params = dict(kernel_size=kernel_size, dilation=1, padding=0, stride=stride)
            unfold = torch.nn.Unfold(**fold_params)
            fold = torch.nn.Fold(output_size=x.shape[2:], **fold_params)
            weighting = self.get_weighting(kernel_size[0], kernel_size[1], Ly, Lx, x.device).to(x.dtype)
            normalization = fold(weighting).view(1, 1, h, w)
            weighting = weighting.view((1, 1, kernel_size[0], kernel_size[1], Ly * Lx))
        elif uf > 1 and df == 1:
            fold_params = dict(kernel_size=kernel_size, dilation=1, padding=0, stride=stride)
            unfold = torch.nn.Unfold(**fold_params)
            fold_params2 = dict(kernel_size=(kernel_size[0] * uf, kernel_size[0] * uf), dilation=1, padding=0, stride=(stride[0] * uf, stride[1] * uf))
            fold = torch.nn.Fold(output_size=(x.shape[2] * uf, x.shape[3] * uf), **fold_params2)
            weighting = self.get_weighting(kernel_size[0] * uf, kernel_size[1] * uf, Ly, Lx, x.device).to(x.dtype)
            normalization = fold(weighting).view(1, 1, h * uf, w * uf)
            weighting = weighting.view((1, 1, kernel_size[0] * uf, kernel_size[1] * uf, Ly * Lx))
        elif df > 1 and uf == 1:
            fold_params = dict(kernel_size=kernel_size, dilation=1, padding=0, stride=stride)
            unfold = torch.nn.Unfold(**fold_params)
            fold_params2 = dict(kernel_size=(kernel_size[0] // df, kernel_size[0] // df), dilation=1, padding=0, stride=(stride[0] // df, stride[1] // df))
            fold = torch.nn.Fold(output_size=(x.shape[2] // df, x.shape[3] // df), **fold_params2)
            weighting = self.get_weighting(kernel_size[0] // df, kernel_size[1] // df, Ly, Lx, x.device).to(x.dtype)
            normalization = fold(weighting).view(1, 1, h // df, w // df)
            weighting = weighting.view((1, 1, kernel_size[0] // df, kernel_size[1] // df, Ly * Lx))
        else:
            raise NotImplementedError
        return (fold, unfold, normalization, weighting)

    @torch.no_grad()
    def get_input(self, batch, k, return_first_stage_outputs=False, force_c_encode=False, cond_key=None, return_original_cond=False, bs=None):
        x = super().get_input(batch, k)
        if bs is not None:
            x = x[:bs]
        x = x.to(self.device)
        encoder_posterior = self.encode_first_stage(x)
        z = self.get_first_stage_encoding(encoder_posterior).detach()
        if self.model.conditioning_key is not None:
            if cond_key is None:
                cond_key = self.cond_stage_key
            if cond_key != self.first_stage_key:
                if cond_key in ['caption', 'coordinates_bbox']:
                    xc = batch[cond_key]
                elif cond_key == 'class_label':
                    xc = batch
                else:
                    xc = super().get_input(batch, cond_key).to(self.device)
            else:
                xc = x
            if not self.cond_stage_trainable or force_c_encode:
                if isinstance(xc, dict) or isinstance(xc, list):
                    c = self.get_learned_conditioning(xc)
                else:
                    c = self.get_learned_conditioning(xc.to(self.device))
            else:
                c = xc
            if bs is not None:
                c = c[:bs]
            if self.use_positional_encodings:
                pos_x, pos_y = self.compute_latent_shifts(batch)
                ckey = __conditioning_keys__[self.model.conditioning_key]
                c = {ckey: c, 'pos_x': pos_x, 'pos_y': pos_y}
        else:
            c = None
            xc = None
            if self.use_positional_encodings:
                pos_x, pos_y = self.compute_latent_shifts(batch)
                c = {'pos_x': pos_x, 'pos_y': pos_y}
        out = [z, c]
        if return_first_stage_outputs:
            xrec = self.decode_first_stage(z)
            out.extend([x, xrec])
        if return_original_cond:
            out.append(xc)
        return out

    @torch.no_grad()
    def decode_first_stage(self, z, predict_cids=False, force_not_quantize=False):
        if predict_cids:
            if z.dim() == 4:
                z = torch.argmax(z.exp(), dim=1).long()
            z = self.first_stage_model.quantize.get_codebook_entry(z, shape=None)
            z = rearrange(z, 'b h w c -> b c h w').contiguous()
        z = 1.0 / self.scale_factor * z
        if hasattr(self, 'split_input_params'):
            if self.split_input_params['patch_distributed_vq']:
                ks = self.split_input_params['ks']
                stride = self.split_input_params['stride']
                uf = self.split_input_params['vqf']
                bs, nc, h, w = z.shape
                if ks[0] > h or ks[1] > w:
                    ks = (min(ks[0], h), min(ks[1], w))
                    print('reducing Kernel')
                if stride[0] > h or stride[1] > w:
                    stride = (min(stride[0], h), min(stride[1], w))
                    print('reducing stride')
                fold, unfold, normalization, weighting = self.get_fold_unfold(z, ks, stride, uf=uf)
                z = unfold(z)
                z = z.view((z.shape[0], -1, ks[0], ks[1], z.shape[-1]))
                if isinstance(self.first_stage_model, VQModelInterface):
                    output_list = [self.first_stage_model.decode(z[:, :, :, :, i], force_not_quantize=predict_cids or force_not_quantize) for i in range(z.shape[-1])]
                else:
                    output_list = [self.first_stage_model.decode(z[:, :, :, :, i]) for i in range(z.shape[-1])]
                o = torch.stack(output_list, axis=-1)
                o = o * weighting
                o = o.view((o.shape[0], -1, o.shape[-1]))
                decoded = fold(o)
                decoded = decoded / normalization
                return decoded
            elif isinstance(self.first_stage_model, VQModelInterface):
                return self.first_stage_model.decode(z, force_not_quantize=predict_cids or force_not_quantize)
            else:
                return self.first_stage_model.decode(z)
        elif isinstance(self.first_stage_model, VQModelInterface):
            return self.first_stage_model.decode(z, force_not_quantize=predict_cids or force_not_quantize)
        else:
            return self.first_stage_model.decode(z)

    def differentiable_decode_first_stage(self, z, predict_cids=False, force_not_quantize=False):
        if predict_cids:
            if z.dim() == 4:
                z = torch.argmax(z.exp(), dim=1).long()
            z = self.first_stage_model.quantize.get_codebook_entry(z, shape=None)
            z = rearrange(z, 'b h w c -> b c h w').contiguous()
        z = 1.0 / self.scale_factor * z
        if hasattr(self, 'split_input_params'):
            if self.split_input_params['patch_distributed_vq']:
                ks = self.split_input_params['ks']
                stride = self.split_input_params['stride']
                uf = self.split_input_params['vqf']
                bs, nc, h, w = z.shape
                if ks[0] > h or ks[1] > w:
                    ks = (min(ks[0], h), min(ks[1], w))
                    print('reducing Kernel')
                if stride[0] > h or stride[1] > w:
                    stride = (min(stride[0], h), min(stride[1], w))
                    print('reducing stride')
                fold, unfold, normalization, weighting = self.get_fold_unfold(z, ks, stride, uf=uf)
                z = unfold(z)
                z = z.view((z.shape[0], -1, ks[0], ks[1], z.shape[-1]))
                if isinstance(self.first_stage_model, VQModelInterface):
                    output_list = [self.first_stage_model.decode(z[:, :, :, :, i], force_not_quantize=predict_cids or force_not_quantize) for i in range(z.shape[-1])]
                else:
                    output_list = [self.first_stage_model.decode(z[:, :, :, :, i]) for i in range(z.shape[-1])]
                o = torch.stack(output_list, axis=-1)
                o = o * weighting
                o = o.view((o.shape[0], -1, o.shape[-1]))
                decoded = fold(o)
                decoded = decoded / normalization
                return decoded
            elif isinstance(self.first_stage_model, VQModelInterface):
                return self.first_stage_model.decode(z, force_not_quantize=predict_cids or force_not_quantize)
            else:
                return self.first_stage_model.decode(z)
        elif isinstance(self.first_stage_model, VQModelInterface):
            return self.first_stage_model.decode(z, force_not_quantize=predict_cids or force_not_quantize)
        else:
            return self.first_stage_model.decode(z)

    @torch.no_grad()
    def encode_first_stage(self, x):
        if hasattr(self, 'split_input_params'):
            if self.split_input_params['patch_distributed_vq']:
                ks = self.split_input_params['ks']
                stride = self.split_input_params['stride']
                df = self.split_input_params['vqf']
                self.split_input_params['original_image_size'] = x.shape[-2:]
                bs, nc, h, w = x.shape
                if ks[0] > h or ks[1] > w:
                    ks = (min(ks[0], h), min(ks[1], w))
                    print('reducing Kernel')
                if stride[0] > h or stride[1] > w:
                    stride = (min(stride[0], h), min(stride[1], w))
                    print('reducing stride')
                fold, unfold, normalization, weighting = self.get_fold_unfold(x, ks, stride, df=df)
                z = unfold(x)
                z = z.view((z.shape[0], -1, ks[0], ks[1], z.shape[-1]))
                output_list = [self.first_stage_model.encode(z[:, :, :, :, i]) for i in range(z.shape[-1])]
                o = torch.stack(output_list, axis=-1)
                o = o * weighting
                o = o.view((o.shape[0], -1, o.shape[-1]))
                decoded = fold(o)
                decoded = decoded / normalization
                return decoded
            else:
                return self.first_stage_model.encode(x)
        else:
            return self.first_stage_model.encode(x)

    def shared_step(self, batch, **kwargs):
        x, c = self.get_input(batch, self.first_stage_key)
        loss = self(x, c)
        return loss

    def forward(self, x, c, *args, **kwargs):
        t = torch.randint(0, self.num_timesteps, (x.shape[0],), device=self.device).long()
        if self.model.conditioning_key is not None:
            assert c is not None
            if self.cond_stage_trainable:
                c = self.get_learned_conditioning(c)
            if self.shorten_cond_schedule:
                tc = self.cond_ids[t].to(self.device)
                c = self.q_sample(x_start=c, t=tc, noise=torch.randn_like(c.float()))
        return self.p_losses(x, c, t, *args, **kwargs)

    def _rescale_annotations(self, bboxes, crop_coordinates):

        def rescale_bbox(bbox):
            x0 = clamp((bbox[0] - crop_coordinates[0]) / crop_coordinates[2])
            y0 = clamp((bbox[1] - crop_coordinates[1]) / crop_coordinates[3])
            w = min(bbox[2] / crop_coordinates[2], 1 - x0)
            h = min(bbox[3] / crop_coordinates[3], 1 - y0)
            return (x0, y0, w, h)
        return [rescale_bbox(b) for b in bboxes]

    def apply_model(self, x_noisy, t, cond, return_ids=False):
        if isinstance(cond, dict):
            pass
        else:
            if not isinstance(cond, list):
                cond = [cond]
            key = 'c_concat' if self.model.conditioning_key == 'concat' else 'c_crossattn'
            cond = {key: cond}
        if hasattr(self, 'split_input_params'):
            assert len(cond) == 1
            assert not return_ids
            ks = self.split_input_params['ks']
            stride = self.split_input_params['stride']
            h, w = x_noisy.shape[-2:]
            fold, unfold, normalization, weighting = self.get_fold_unfold(x_noisy, ks, stride)
            z = unfold(x_noisy)
            z = z.view((z.shape[0], -1, ks[0], ks[1], z.shape[-1]))
            z_list = [z[:, :, :, :, i] for i in range(z.shape[-1])]
            if self.cond_stage_key in ['image', 'LR_image', 'segmentation', 'bbox_img'] and self.model.conditioning_key:
                c_key = next(iter(cond.keys()))
                c = next(iter(cond.values()))
                assert len(c) == 1
                c = c[0]
                c = unfold(c)
                c = c.view((c.shape[0], -1, ks[0], ks[1], c.shape[-1]))
                cond_list = [{c_key: [c[:, :, :, :, i]]} for i in range(c.shape[-1])]
            elif self.cond_stage_key == 'coordinates_bbox':
                assert 'original_image_size' in self.split_input_params, 'BoudingBoxRescaling is missing original_image_size'
                n_patches_per_row = int((w - ks[0]) / stride[0] + 1)
                full_img_h, full_img_w = self.split_input_params['original_image_size']
                num_downs = self.first_stage_model.encoder.num_resolutions - 1
                rescale_latent = 2 ** num_downs
                tl_patch_coordinates = [(rescale_latent * stride[0] * (patch_nr % n_patches_per_row) / full_img_w, rescale_latent * stride[1] * (patch_nr // n_patches_per_row) / full_img_h) for patch_nr in range(z.shape[-1])]
                patch_limits = [(x_tl, y_tl, rescale_latent * ks[0] / full_img_w, rescale_latent * ks[1] / full_img_h) for x_tl, y_tl in tl_patch_coordinates]
                patch_limits_tknzd = [torch.LongTensor(self.bbox_tokenizer._crop_encoder(bbox))[None].to(self.device) for bbox in patch_limits]
                print(patch_limits_tknzd[0].shape)
                assert isinstance(cond, dict), 'cond must be dict to be fed into model'
                cut_cond = cond['c_crossattn'][0][..., :-2].to(self.device)
                print(cut_cond.shape)
                adapted_cond = torch.stack([torch.cat([cut_cond, p], dim=1) for p in patch_limits_tknzd])
                adapted_cond = rearrange(adapted_cond, 'l b n -> (l b) n')
                print(adapted_cond.shape)
                adapted_cond = self.get_learned_conditioning(adapted_cond)
                print(adapted_cond.shape)
                adapted_cond = rearrange(adapted_cond, '(l b) n d -> l b n d', l=z.shape[-1])
                print(adapted_cond.shape)
                cond_list = [{'c_crossattn': [e]} for e in adapted_cond]
            else:
                cond_list = [cond for i in range(z.shape[-1])]
            output_list = [self.model(z_list[i], t, **cond_list[i]) for i in range(z.shape[-1])]
            assert not isinstance(output_list[0], tuple)
            o = torch.stack(output_list, axis=-1)
            o = o * weighting
            o = o.view((o.shape[0], -1, o.shape[-1]))
            x_recon = fold(o) / normalization
        else:
            x_recon = self.model(x_noisy, t, **cond)
        if isinstance(x_recon, tuple) and (not return_ids):
            return x_recon[0]
        else:
            return x_recon

    def _predict_eps_from_xstart(self, x_t, t, pred_xstart):
        return (extract_into_tensor(self.sqrt_recip_alphas_cumprod, t, x_t.shape) * x_t - pred_xstart) / extract_into_tensor(self.sqrt_recipm1_alphas_cumprod, t, x_t.shape)

    def _prior_bpd(self, x_start):
        """
        Get the prior KL term for the variational lower-bound, measured in
        bits-per-dim.
        This term can't be optimized, as it only depends on the encoder.
        :param x_start: the [N x C x ...] tensor of inputs.
        :return: a batch of [N] KL values (in bits), one per batch element.
        """
        batch_size = x_start.shape[0]
        t = torch.tensor([self.num_timesteps - 1] * batch_size, device=x_start.device)
        qt_mean, _, qt_log_variance = self.q_mean_variance(x_start, t)
        kl_prior = normal_kl(mean1=qt_mean, logvar1=qt_log_variance, mean2=0.0, logvar2=0.0)
        return mean_flat(kl_prior) / np.log(2.0)

    def p_losses(self, x_start, cond, t, noise=None):
        noise = default(noise, lambda: torch.randn_like(x_start))
        x_noisy = self.q_sample(x_start=x_start, t=t, noise=noise)
        model_output = self.apply_model(x_noisy, t, cond)
        loss_dict = {}
        prefix = 'train' if self.training else 'val'
        if self.parameterization == 'x0':
            target = x_start
        elif self.parameterization == 'eps':
            target = noise
        else:
            raise NotImplementedError()
        loss_simple = self.get_loss(model_output, target, mean=False).mean([1, 2, 3])
        loss_dict.update({f'{prefix}/loss_simple': loss_simple.mean()})
        logvar_t = self.logvar[t].to(self.device)
        loss = loss_simple / torch.exp(logvar_t) + logvar_t
        if self.learn_logvar:
            loss_dict.update({f'{prefix}/loss_gamma': loss.mean()})
            loss_dict.update({'logvar': self.logvar.data.mean()})
        loss = self.l_simple_weight * loss.mean()
        loss_vlb = self.get_loss(model_output, target, mean=False).mean(dim=(1, 2, 3))
        loss_vlb = (self.lvlb_weights[t] * loss_vlb).mean()
        loss_dict.update({f'{prefix}/loss_vlb': loss_vlb})
        loss += self.original_elbo_weight * loss_vlb
        loss_dict.update({f'{prefix}/loss': loss})
        return (loss, loss_dict)

    def p_mean_variance(self, x, c, t, clip_denoised: bool, return_codebook_ids=False, quantize_denoised=False, return_x0=False, score_corrector=None, corrector_kwargs=None):
        t_in = t
        model_out = self.apply_model(x, t_in, c, return_ids=return_codebook_ids)
        if score_corrector is not None:
            assert self.parameterization == 'eps'
            model_out = score_corrector.modify_score(self, model_out, x, t, c, **corrector_kwargs)
        if return_codebook_ids:
            model_out, logits = model_out
        if self.parameterization == 'eps':
            x_recon = self.predict_start_from_noise(x, t=t, noise=model_out)
        elif self.parameterization == 'x0':
            x_recon = model_out
        else:
            raise NotImplementedError()
        if clip_denoised:
            x_recon.clamp_(-1.0, 1.0)
        if quantize_denoised:
            x_recon, _, [_, _, indices] = self.first_stage_model.quantize(x_recon)
        model_mean, posterior_variance, posterior_log_variance = self.q_posterior(x_start=x_recon, x_t=x, t=t)
        if return_codebook_ids:
            return (model_mean, posterior_variance, posterior_log_variance, logits)
        elif return_x0:
            return (model_mean, posterior_variance, posterior_log_variance, x_recon)
        else:
            return (model_mean, posterior_variance, posterior_log_variance)

    @torch.no_grad()
    def p_sample(self, x, c, t, clip_denoised=False, repeat_noise=False, return_codebook_ids=False, quantize_denoised=False, return_x0=False, temperature=1.0, noise_dropout=0.0, score_corrector=None, corrector_kwargs=None):
        b, *_, device = (*x.shape, x.device)
        outputs = self.p_mean_variance(x=x, c=c, t=t, clip_denoised=clip_denoised, return_codebook_ids=return_codebook_ids, quantize_denoised=quantize_denoised, return_x0=return_x0, score_corrector=score_corrector, corrector_kwargs=corrector_kwargs)
        if return_codebook_ids:
            raise DeprecationWarning('Support dropped.')
            model_mean, _, model_log_variance, logits = outputs
        elif return_x0:
            model_mean, _, model_log_variance, x0 = outputs
        else:
            model_mean, _, model_log_variance = outputs
        noise = noise_like(x.shape, device, repeat_noise) * temperature
        if noise_dropout > 0.0:
            noise = torch.nn.functional.dropout(noise, p=noise_dropout)
        nonzero_mask = (1 - (t == 0).float()).reshape(b, *(1,) * (len(x.shape) - 1))
        if return_codebook_ids:
            return (model_mean + nonzero_mask * (0.5 * model_log_variance).exp() * noise, logits.argmax(dim=1))
        if return_x0:
            return (model_mean + nonzero_mask * (0.5 * model_log_variance).exp() * noise, x0)
        else:
            return model_mean + nonzero_mask * (0.5 * model_log_variance).exp() * noise

    @torch.no_grad()
    def progressive_denoising(self, cond, shape, verbose=True, callback=None, quantize_denoised=False, img_callback=None, mask=None, x0=None, temperature=1.0, noise_dropout=0.0, score_corrector=None, corrector_kwargs=None, batch_size=None, x_T=None, start_T=None, log_every_t=None):
        if not log_every_t:
            log_every_t = self.log_every_t
        timesteps = self.num_timesteps
        if batch_size is not None:
            b = batch_size if batch_size is not None else shape[0]
            shape = [batch_size] + list(shape)
        else:
            b = batch_size = shape[0]
        if x_T is None:
            img = torch.randn(shape, device=self.device)
        else:
            img = x_T
        intermediates = []
        if cond is not None:
            if isinstance(cond, dict):
                cond = {key: cond[key][:batch_size] if not isinstance(cond[key], list) else list(map(lambda x: x[:batch_size], cond[key])) for key in cond}
            else:
                cond = [c[:batch_size] for c in cond] if isinstance(cond, list) else cond[:batch_size]
        if start_T is not None:
            timesteps = min(timesteps, start_T)
        iterator = tqdm(reversed(range(0, timesteps)), desc='Progressive Generation', total=timesteps) if verbose else reversed(range(0, timesteps))
        if type(temperature) == float:
            temperature = [temperature] * timesteps
        for i in iterator:
            ts = torch.full((b,), i, device=self.device, dtype=torch.long)
            if self.shorten_cond_schedule:
                assert self.model.conditioning_key != 'hybrid'
                tc = self.cond_ids[ts].to(cond.device)
                cond = self.q_sample(x_start=cond, t=tc, noise=torch.randn_like(cond))
            img, x0_partial = self.p_sample(img, cond, ts, clip_denoised=self.clip_denoised, quantize_denoised=quantize_denoised, return_x0=True, temperature=temperature[i], noise_dropout=noise_dropout, score_corrector=score_corrector, corrector_kwargs=corrector_kwargs)
            if mask is not None:
                assert x0 is not None
                img_orig = self.q_sample(x0, ts)
                img = img_orig * mask + (1.0 - mask) * img
            if i % log_every_t == 0 or i == timesteps - 1:
                intermediates.append(x0_partial)
            if callback:
                callback(i)
            if img_callback:
                img_callback(img, i)
        return (img, intermediates)

    @torch.no_grad()
    def p_sample_loop(self, cond, shape, return_intermediates=False, x_T=None, verbose=True, callback=None, timesteps=None, quantize_denoised=False, mask=None, x0=None, img_callback=None, start_T=None, log_every_t=None):
        if not log_every_t:
            log_every_t = self.log_every_t
        device = self.betas.device
        b = shape[0]
        if x_T is None:
            img = torch.randn(shape, device=device)
        else:
            img = x_T
        intermediates = [img]
        if timesteps is None:
            timesteps = self.num_timesteps
        if start_T is not None:
            timesteps = min(timesteps, start_T)
        iterator = tqdm(reversed(range(0, timesteps)), desc='Sampling t', total=timesteps) if verbose else reversed(range(0, timesteps))
        if mask is not None:
            assert x0 is not None
            assert x0.shape[2:3] == mask.shape[2:3]
        for i in iterator:
            ts = torch.full((b,), i, device=device, dtype=torch.long)
            if self.shorten_cond_schedule:
                assert self.model.conditioning_key != 'hybrid'
                tc = self.cond_ids[ts].to(cond.device)
                cond = self.q_sample(x_start=cond, t=tc, noise=torch.randn_like(cond))
            img = self.p_sample(img, cond, ts, clip_denoised=self.clip_denoised, quantize_denoised=quantize_denoised)
            if mask is not None:
                img_orig = self.q_sample(x0, ts)
                img = img_orig * mask + (1.0 - mask) * img
            if i % log_every_t == 0 or i == timesteps - 1:
                intermediates.append(img)
            if callback:
                callback(i)
            if img_callback:
                img_callback(img, i)
        if return_intermediates:
            return (img, intermediates)
        return img

    @torch.no_grad()
    def sample(self, cond, batch_size=16, return_intermediates=False, x_T=None, verbose=True, timesteps=None, quantize_denoised=False, mask=None, x0=None, shape=None, **kwargs):
        if shape is None:
            shape = (batch_size, self.channels, self.image_size, self.image_size)
        if cond is not None:
            if isinstance(cond, dict):
                cond = {key: cond[key][:batch_size] if not isinstance(cond[key], list) else list(map(lambda x: x[:batch_size], cond[key])) for key in cond}
            else:
                cond = [c[:batch_size] for c in cond] if isinstance(cond, list) else cond[:batch_size]
        return self.p_sample_loop(cond, shape, return_intermediates=return_intermediates, x_T=x_T, verbose=verbose, timesteps=timesteps, quantize_denoised=quantize_denoised, mask=mask, x0=x0)

    @torch.no_grad()
    def sample_log(self, cond, batch_size, ddim, ddim_steps, **kwargs):
        if ddim:
            ddim_sampler = DDIMSampler(self)
            shape = (self.channels, self.image_size, self.image_size)
            samples, intermediates = ddim_sampler.sample(ddim_steps, batch_size, shape, cond, verbose=False, **kwargs)
        else:
            samples, intermediates = self.sample(cond=cond, batch_size=batch_size, return_intermediates=True, **kwargs)
        return (samples, intermediates)

    @torch.no_grad()
    def log_images(self, batch, N=8, n_row=4, sample=True, ddim_steps=200, ddim_eta=1.0, return_keys=None, quantize_denoised=True, inpaint=True, plot_denoise_rows=False, plot_progressive_rows=True, plot_diffusion_rows=True, **kwargs):
        use_ddim = ddim_steps is not None
        log = dict()
        z, c, x, xrec, xc = self.get_input(batch, self.first_stage_key, return_first_stage_outputs=True, force_c_encode=True, return_original_cond=True, bs=N)
        N = min(x.shape[0], N)
        n_row = min(x.shape[0], n_row)
        log['inputs'] = x
        log['reconstruction'] = xrec
        if self.model.conditioning_key is not None:
            if hasattr(self.cond_stage_model, 'decode'):
                xc = self.cond_stage_model.decode(c)
                log['conditioning'] = xc
            elif self.cond_stage_key in ['caption']:
                xc = log_txt_as_img((x.shape[2], x.shape[3]), batch['caption'])
                log['conditioning'] = xc
            elif self.cond_stage_key == 'class_label':
                xc = log_txt_as_img((x.shape[2], x.shape[3]), batch['human_label'])
                log['conditioning'] = xc
            elif isimage(xc):
                log['conditioning'] = xc
            if ismap(xc):
                log['original_conditioning'] = self.to_rgb(xc)
        if plot_diffusion_rows:
            diffusion_row = list()
            z_start = z[:n_row]
            for t in range(self.num_timesteps):
                if t % self.log_every_t == 0 or t == self.num_timesteps - 1:
                    t = repeat(torch.tensor([t]), '1 -> b', b=n_row)
                    t = t.to(self.device).long()
                    noise = torch.randn_like(z_start)
                    z_noisy = self.q_sample(x_start=z_start, t=t, noise=noise)
                    diffusion_row.append(self.decode_first_stage(z_noisy))
            diffusion_row = torch.stack(diffusion_row)
            diffusion_grid = rearrange(diffusion_row, 'n b c h w -> b n c h w')
            diffusion_grid = rearrange(diffusion_grid, 'b n c h w -> (b n) c h w')
            diffusion_grid = make_grid(diffusion_grid, nrow=diffusion_row.shape[0])
            log['diffusion_row'] = diffusion_grid
        if sample:
            with self.ema_scope('Plotting'):
                samples, z_denoise_row = self.sample_log(cond=c, batch_size=N, ddim=use_ddim, ddim_steps=ddim_steps, eta=ddim_eta)
            x_samples = self.decode_first_stage(samples)
            log['samples'] = x_samples
            if plot_denoise_rows:
                denoise_grid = self._get_denoise_row_from_list(z_denoise_row)
                log['denoise_row'] = denoise_grid
            if quantize_denoised and (not isinstance(self.first_stage_model, AutoencoderKL)) and (not isinstance(self.first_stage_model, IdentityFirstStage)):
                with self.ema_scope('Plotting Quantized Denoised'):
                    samples, z_denoise_row = self.sample_log(cond=c, batch_size=N, ddim=use_ddim, ddim_steps=ddim_steps, eta=ddim_eta, quantize_denoised=True)
                x_samples = self.decode_first_stage(samples.to(self.device))
                log['samples_x0_quantized'] = x_samples
            if inpaint:
                b, h, w = (z.shape[0], z.shape[2], z.shape[3])
                mask = torch.ones(N, h, w).to(self.device)
                mask[:, h // 4:3 * h // 4, w // 4:3 * w // 4] = 0.0
                mask = mask[:, None, ...]
                with self.ema_scope('Plotting Inpaint'):
                    samples, _ = self.sample_log(cond=c, batch_size=N, ddim=use_ddim, eta=ddim_eta, ddim_steps=ddim_steps, x0=z[:N], mask=mask)
                x_samples = self.decode_first_stage(samples.to(self.device))
                log['samples_inpainting'] = x_samples
                log['mask'] = mask
                with self.ema_scope('Plotting Outpaint'):
                    samples, _ = self.sample_log(cond=c, batch_size=N, ddim=use_ddim, eta=ddim_eta, ddim_steps=ddim_steps, x0=z[:N], mask=mask)
                x_samples = self.decode_first_stage(samples.to(self.device))
                log['samples_outpainting'] = x_samples
        if plot_progressive_rows:
            with self.ema_scope('Plotting Progressives'):
                img, progressives = self.progressive_denoising(c, shape=(self.channels, self.image_size, self.image_size), batch_size=N)
            prog_row = self._get_denoise_row_from_list(progressives, desc='Progressive Generation')
            log['progressive_row'] = prog_row
        if return_keys:
            if np.intersect1d(list(log.keys()), return_keys).shape[0] == 0:
                return log
            else:
                return {key: log[key] for key in return_keys}
        return log

    def configure_optimizers(self):
        lr = self.learning_rate
        params = list(self.model.parameters())
        if self.cond_stage_trainable:
            print(f'{self.__class__.__name__}: Also optimizing conditioner params!')
            params = params + list(self.cond_stage_model.parameters())
        if self.learn_logvar:
            print('Diffusion model optimizing logvar')
            params.append(self.logvar)
        opt = torch.optim.AdamW(params, lr=lr)
        if self.use_scheduler:
            assert 'target' in self.scheduler_config
            scheduler = instantiate_from_config(self.scheduler_config)
            print('Setting up LambdaLR scheduler...')
            scheduler = [{'scheduler': LambdaLR(opt, lr_lambda=scheduler.schedule), 'interval': 'step', 'frequency': 1}]
            return ([opt], scheduler)
        return opt

    @torch.no_grad()
    def to_rgb(self, x):
        x = x.float()
        if not hasattr(self, 'colorize'):
            self.colorize = torch.randn(3, x.shape[1], 1, 1).to(x)
        x = nn.functional.conv2d(x, weight=self.colorize)
        x = 2.0 * (x - x.min()) / (x.max() - x.min()) - 1.0
        return x

def get_first_stage_encoding(self, encoder_posterior):
    if isinstance(encoder_posterior, DiagonalGaussianDistribution):
        z = encoder_posterior.sample()
    elif isinstance(encoder_posterior, torch.Tensor):
        z = encoder_posterior
    else:
        raise NotImplementedError(f"encoder_posterior of type '{type(encoder_posterior)}' not yet implemented")
    return self.scale_factor * z

@torch.no_grad()
def sample_log(self, cond, batch_size, ddim, ddim_steps, **kwargs):
    if ddim:
        ddim_sampler = DDIMSampler(self)
        shape = (self.channels, self.image_size, self.image_size)
        samples, intermediates = ddim_sampler.sample(ddim_steps, batch_size, shape, cond, verbose=False, **kwargs)
    else:
        samples, intermediates = self.sample(cond=cond, batch_size=batch_size, return_intermediates=True, **kwargs)
    return (samples, intermediates)

def get_outlines(corners, extrinsic, intrinsic, height, width):

    def generate_convex_hull(points):
        hull = ConvexHull(points)
        return points[hull.vertices]

    def polygon_to_mask(polygon, height, width):
        img = Image.new('L', (width, height), 0)
        ImageDraw.Draw(img).polygon([tuple(p) for p in polygon], outline=1, fill=1)
        mask = np.array(img)
        return mask
    all_one = np.ones((corners.shape[0], 1))
    points = np.concatenate((corners, all_one), axis=1).T
    cam_points = (np.linalg.inv(extrinsic) @ points)[:3]
    cam_points = cam_points / cam_points[2:]
    points = (intrinsic @ cam_points).T[:, :2]
    points[:, 0] = np.clip(points[:, 0], 0, width)
    points[:, 1] = np.clip(points[:, 1], 0, height)
    mask = np.zeros((height, width))
    points = points.astype(int)
    y_min = max(points[:, 1].min() - 50, 0)
    y_max = min(points[:, 1].max() + 50, height)
    x_min = max(points[:, 0].min() - 50, 0)
    x_max = min(points[:, 0].max() + 50, width)
    mask[y_min:y_max, x_min:x_max] = 1
    return (mask, [y_min, y_max, x_min, x_max])

def get_attributes_for_one_car(car, extrinsic, intrinsic):
    x = car['cx']
    y = car['cy']
    z = car['cz']
    one_point = np.array([[x, y, z]])
    all_one = np.ones((one_point.shape[0], 1))
    points = np.concatenate((one_point, all_one), axis=1).T
    cam_points = (np.linalg.inv(extrinsic) @ points)[:3]
    cam_points_without_norm = copy.copy(cam_points)
    cam_points = cam_points / cam_points[2:]
    points = (intrinsic @ cam_points).T[:, :2]
    return {'u': points[0, 0], 'v': points[0, 1], 'depth': cam_points_without_norm[-1, 0]}

def blending_hdr_sky(nerf_env_panorama, sky_dome_panorama, nerf_last_trans, sky_mask):
    """
    blending hdr sky dome with nerf panorama
    Args:
        nerf_env_panorama : np.ndarray
            shape [H1, W1, 3], In Linear space

        sky_dome_panorama : np.ndarray
            shape [H2, W2, 3], In Linear space

        nerf_last_trans : np.ndarray
            shape [H1, W1, 1], range (0-1)
        
    """
    H, W, _ = sky_dome_panorama.shape
    sky_mask = cv2.resize(sky_mask, (W, H))[:, :, :1]
    nerf_env_panorama = cv2.resize(nerf_env_panorama, (W, H))
    nerf_last_trans = cv2.resize(nerf_last_trans, (W, H))[:, :, np.newaxis]
    nerf_last_trans[sky_mask > 255 * 0.5] = 1
    final_hdr_sky = nerf_env_panorama + sky_dome_panorama * nerf_last_trans
    return final_hdr_sky

def get_color(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
    maxsum = -100
    color = None
    color_dict = getColorList()
    max_num = 0
    for d in color_dict:
        mask = cv2.inRange(hsv, color_dict[d][0], color_dict[d][1])
        binary = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)[1]
        binary = cv2.dilate(binary, None, iterations=2)
        img, cnts = cv2.findContours(binary.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        mask_num = binary[binary == 255].shape[0]
        if mask_num > max_num:
            max_num = mask_num
            color = d
    return color

class HoliCitySDRDataset(Dataset):

    def __init__(self, args, split='train'):
        self.multicrop_dir = args['multicrop_dir']
        self.skymask_dir = args['skymask_dir']
        self.skyldr_dir = args['skyldr_dir']
        self.skyhdr_dir = args['skyhdr_dir']
        selected_sample_json = args['selected_sample_json']
        view_args = args['view_setting']
        self.crop_H = view_args['camera_H'] // view_args['downsample_for_crop']
        self.crop_W = view_args['camera_W'] // view_args['downsample_for_crop']
        self.camera_vfov = np.degrees(np.arctan2(view_args['camera_H'] / 2, view_args['focal'])) * 2
        self.aspect_ratio = view_args['camera_W'] / view_args['camera_H']
        self.view_num = view_args['view_num']
        self.view_dis_deg = view_args['view_dis']
        self.sky_pano_H = args['sky_pano_H']
        self.sky_pano_W = args['sky_pano_W']
        with open(selected_sample_json, 'r') as f:
            self.select_sample = json.load(f)
        random.seed(303)
        random.shuffle(self.select_sample)
        all_sample_num = len(self.select_sample)
        train_ratio = 0.8
        self.train_file_list = self.select_sample[:int(all_sample_num * train_ratio)]
        self.val_file_list = self.select_sample[int(all_sample_num * train_ratio):]
        self.is_train = split == 'train'
        if self.is_train:
            self.file_list = self.train_file_list
        else:
            self.file_list = self.val_file_list
        self.aug_rotation = True if self.is_train else False

    def __len__(self):
        return len(self.file_list)

    def __getitem__(self, idx):
        sky_ldr_path = os.path.join(self.skyldr_dir, self.file_list[idx])
        sky_mask_path = os.path.join(self.skymask_dir, self.file_list[idx])
        sky_hdr_path = os.path.join(self.skyhdr_dir, self.file_list[idx].replace('.jpg', '.npz'))
        ldr_skypano = imread(sky_ldr_path) / 255
        sky_mask = imread(sky_mask_path).astype(np.float32) / 255
        sky_hdr_dict = np.load(sky_hdr_path)
        peak_vector = sky_hdr_dict['peak_vector']
        latent_vector = sky_hdr_dict['latent_vector']
        hdr_skypano = sky_hdr_dict['hdr_skypano']
        ldr_envmap = EnvironmentMap(ldr_skypano, 'skylatlong')
        hdr_envmap = EnvironmentMap(hdr_skypano, 'skylatlong')
        mask_envmap = EnvironmentMap(sky_mask, 'skylatlong')
        if self.aug_rotation:
            azimuth_deg = choice(range(0, 360, 45))
            azimuth_rad = np.radians(azimuth_deg)
            rotation_mat = rotation_matrix(azimuth=azimuth_rad, elevation=0)
            inv_rotation_mat = rotation_matrix(azimuth=-azimuth_rad, elevation=0)
        else:
            azimuth_deg = 0
        img_crops_tensor_list = []
        for i in range(self.view_num):
            azimuth_deg_i = (azimuth_deg + self.view_dis_deg[i]) % 360
            azimuth_deg_i = int(azimuth_deg_i)
            img_crop_path = os.path.join(self.multicrop_dir, str(azimuth_deg_i), self.file_list[idx])
            img_crop = imread(img_crop_path) / 255
            img_crops_tensor_list.append(totensor(img_crop))
        if self.aug_rotation:
            hdr_envmap.rotate(dcm=inv_rotation_mat)
            mask_envmap.rotate(dcm=inv_rotation_mat)
            ldr_envmap.rotate(dcm=inv_rotation_mat)
            peak_vector[:3] = (rotation_mat @ peak_vector[:3].reshape(3, 1)).flatten()
        img_crops_tensor = torch.stack(img_crops_tensor_list)
        peak_vector_tensor = totensor(peak_vector)
        latent_vector_tensor = totensor(latent_vector)
        mask_envmap_tensor = totensor(mask_envmap.data)
        hdr_envmap_tensor = totensor(hdr_envmap.data)
        ldr_envmap_tensor = totensor(ldr_envmap.data)
        return (img_crops_tensor, peak_vector_tensor, latent_vector_tensor, mask_envmap_tensor, hdr_envmap_tensor, ldr_envmap_tensor)

def __getitem__(self, idx):
    sky_ldr_path = os.path.join(self.skyldr_dir, self.file_list[idx])
    sky_mask_path = os.path.join(self.skymask_dir, self.file_list[idx])
    sky_hdr_path = os.path.join(self.skyhdr_dir, self.file_list[idx].replace('.jpg', '.npz'))
    ldr_skypano = imread(sky_ldr_path) / 255
    sky_mask = imread(sky_mask_path).astype(np.float32) / 255
    sky_hdr_dict = np.load(sky_hdr_path)
    peak_vector = sky_hdr_dict['peak_vector']
    latent_vector = sky_hdr_dict['latent_vector']
    hdr_skypano = sky_hdr_dict['hdr_skypano']
    ldr_envmap = EnvironmentMap(ldr_skypano, 'skylatlong')
    hdr_envmap = EnvironmentMap(hdr_skypano, 'skylatlong')
    mask_envmap = EnvironmentMap(sky_mask, 'skylatlong')
    if self.aug_rotation:
        azimuth_deg = choice(range(0, 360, 45))
        azimuth_rad = np.radians(azimuth_deg)
        rotation_mat = rotation_matrix(azimuth=azimuth_rad, elevation=0)
        inv_rotation_mat = rotation_matrix(azimuth=-azimuth_rad, elevation=0)
    else:
        azimuth_deg = 0
    img_crops_tensor_list = []
    for i in range(self.view_num):
        azimuth_deg_i = (azimuth_deg + self.view_dis_deg[i]) % 360
        azimuth_deg_i = int(azimuth_deg_i)
        img_crop_path = os.path.join(self.multicrop_dir, str(azimuth_deg_i), self.file_list[idx])
        img_crop = imread(img_crop_path) / 255
        img_crops_tensor_list.append(totensor(img_crop))
    if self.aug_rotation:
        hdr_envmap.rotate(dcm=inv_rotation_mat)
        mask_envmap.rotate(dcm=inv_rotation_mat)
        ldr_envmap.rotate(dcm=inv_rotation_mat)
        peak_vector[:3] = (rotation_mat @ peak_vector[:3].reshape(3, 1)).flatten()
    img_crops_tensor = torch.stack(img_crops_tensor_list)
    peak_vector_tensor = totensor(peak_vector)
    latent_vector_tensor = totensor(latent_vector)
    mask_envmap_tensor = totensor(mask_envmap.data)
    hdr_envmap_tensor = totensor(hdr_envmap.data)
    ldr_envmap_tensor = totensor(ldr_envmap.data)
    return (img_crops_tensor, peak_vector_tensor, latent_vector_tensor, mask_envmap_tensor, hdr_envmap_tensor, ldr_envmap_tensor)

class HDRSkyDataset(Dataset):

    def __init__(self, args, split='train'):
        root_dir = args['root_dir']
        downsample = args['downsample']
        self.sky_H = args['image_H'] // downsample // 2
        self.sky_W = args['image_W'] // downsample
        self.root_dir = os.path.join(root_dir, split)
        self.downsample = downsample
        self.file_list = sorted(os.listdir(self.root_dir))
        self.is_train = split == 'train'
        self.env_template = EnvironmentMap(self.sky_H, 'skylatlong')
        self.center_align = args.get('center_align', False)
        self.normalize = args.get('normalize', None)
        self.aug_exposure_range = args.get('aug_exposure_range', [-2.5, 0.5])
        self.aug_temperature_range = args.get('aug_temperature_range', [1, 1])

    def __len__(self):
        return len(self.file_list)

    def __getitem__(self, idx):
        file_path = os.path.join(self.root_dir, self.file_list[idx])
        hdr_pano = imread(file_path)
        hdr_skypano = hdr_pano[:hdr_pano.shape[0] // 2, :, :]
        hdr_skypano = cv2.resize(hdr_skypano, (self.sky_W, self.sky_H))[:, :, :3]
        if self.is_train:
            hdr_skypano = adjust_exposure(hdr_skypano, self.aug_exposure_range)
            hdr_skypano = adjust_flip(hdr_skypano)
            if not self.center_align:
                hdr_skypano = adjust_rotation(hdr_skypano)
            hdr_skypano = adjust_color_temperature(hdr_skypano, self.aug_temperature_range)
        illumination = 0.2126 * hdr_skypano[..., 0] + 0.7152 * hdr_skypano[..., 1] + 0.0722 * hdr_skypano[..., 2]
        max_index = np.argmax(illumination, axis=None)
        max_index_2d = np.unravel_index(max_index, illumination.shape)
        peak_int_v, peak_int_u = max_index_2d
        if self.center_align:
            azimuth = (self.sky_W // 2 - peak_int_u) % self.sky_W / self.sky_W * 2 * np.pi
            hdr_skypano = adjust_rotation(hdr_skypano, azimuth)
            peak_int_u = self.sky_W // 2
        peak_int = hdr_skypano[peak_int_v, peak_int_u]
        peak_dir_w_flag = self.env_template.pixel2world(peak_int_u, peak_int_v)
        peak_dir = np.array([peak_dir_w_flag[0], peak_dir_w_flag[1], peak_dir_w_flag[2]])
        ldr_skypano = srgb_gamma_correction(hdr_skypano)
        if self.normalize:
            peak_int_R = np.percentile(hdr_skypano[..., 0], self.normalize * 100)
            peak_int_G = np.percentile(hdr_skypano[..., 1], self.normalize * 100)
            peak_int_B = np.percentile(hdr_skypano[..., 2], self.normalize * 100)
            peak_int = np.array([peak_int_R, peak_int_G, peak_int_B])
            hdr_skypano = hdr_skypano / peak_int
            hdr_skypano = hdr_skypano.clip(0, 1)
        peak_vector = np.concatenate([peak_dir, peak_int], axis=-1)
        peak_vector_tensor = torch.from_numpy(peak_vector.astype(np.float32))
        hdr_skypano_tensor = torch.from_numpy(hdr_skypano.astype(np.float32)).permute(2, 0, 1)
        ldr_skypano_tensor = torch.from_numpy(ldr_skypano.astype(np.float32)).permute(2, 0, 1)
        return (ldr_skypano_tensor, hdr_skypano_tensor, peak_vector_tensor)

def __getitem__(self, idx):
    file_path = os.path.join(self.root_dir, self.file_list[idx])
    hdr_pano = imread(file_path)
    hdr_skypano = hdr_pano[:hdr_pano.shape[0] // 2, :, :]
    hdr_skypano = cv2.resize(hdr_skypano, (self.sky_W, self.sky_H))[:, :, :3]
    if self.is_train:
        hdr_skypano = adjust_exposure(hdr_skypano, self.aug_exposure_range)
        hdr_skypano = adjust_flip(hdr_skypano)
        if not self.center_align:
            hdr_skypano = adjust_rotation(hdr_skypano)
        hdr_skypano = adjust_color_temperature(hdr_skypano, self.aug_temperature_range)
    illumination = 0.2126 * hdr_skypano[..., 0] + 0.7152 * hdr_skypano[..., 1] + 0.0722 * hdr_skypano[..., 2]
    max_index = np.argmax(illumination, axis=None)
    max_index_2d = np.unravel_index(max_index, illumination.shape)
    peak_int_v, peak_int_u = max_index_2d
    if self.center_align:
        azimuth = (self.sky_W // 2 - peak_int_u) % self.sky_W / self.sky_W * 2 * np.pi
        hdr_skypano = adjust_rotation(hdr_skypano, azimuth)
        peak_int_u = self.sky_W // 2
    peak_int = hdr_skypano[peak_int_v, peak_int_u]
    peak_dir_w_flag = self.env_template.pixel2world(peak_int_u, peak_int_v)
    peak_dir = np.array([peak_dir_w_flag[0], peak_dir_w_flag[1], peak_dir_w_flag[2]])
    ldr_skypano = srgb_gamma_correction(hdr_skypano)
    if self.normalize:
        peak_int_R = np.percentile(hdr_skypano[..., 0], self.normalize * 100)
        peak_int_G = np.percentile(hdr_skypano[..., 1], self.normalize * 100)
        peak_int_B = np.percentile(hdr_skypano[..., 2], self.normalize * 100)
        peak_int = np.array([peak_int_R, peak_int_G, peak_int_B])
        hdr_skypano = hdr_skypano / peak_int
        hdr_skypano = hdr_skypano.clip(0, 1)
    peak_vector = np.concatenate([peak_dir, peak_int], axis=-1)
    peak_vector_tensor = torch.from_numpy(peak_vector.astype(np.float32))
    hdr_skypano_tensor = torch.from_numpy(hdr_skypano.astype(np.float32)).permute(2, 0, 1)
    ldr_skypano_tensor = torch.from_numpy(ldr_skypano.astype(np.float32)).permute(2, 0, 1)
    return (ldr_skypano_tensor, hdr_skypano_tensor, peak_vector_tensor)

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

def adjust_flip(image, probability=0.5):
    if np.random.random() < probability:
        return np.fliplr(image)
    else:
        return image

def adjust_rotation(image, azimuth=None):
    if azimuth is None:
        azimuth = np.random.rand() * 2 * np.pi
    envmap = EnvironmentMap(image, 'skylatlong')
    envmap.rotate(dcm=rotation_matrix(azimuth=azimuth, elevation=0))
    return envmap.data

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

def test_crop():
    e = EnvironmentMap('dataset/holicity_pano/2008-07/8heFyix0weuW7Kzd6A_BLg.jpg', 'latlong')
    outpath = 'crop.png'
    rotation_mat = rotation_matrix(azimuth=np.pi / 6, elevation=0)
    crop = (e.project(vfov=60, ar=16 / 9, resolution=(640, 360), rotation_matrix=rotation_mat) * 255).astype(np.uint8)
    imageio.imsave(outpath, crop)

def test_resolution():
    pano_image = imageio.imread('dataset/holicity_pano/2008-07/8heFyix0weuW7Kzd6A_BLg.jpg')
    H = pano_image.shape[0]
    for level in range(8):
        time_begin = time.time()
        pano_image_downsample = cv2.resize(pano_image, (H // 2 ** level * 2, H // 2 ** level))
        e = EnvironmentMap(pano_image_downsample, 'latlong')
        for j in range(3):
            outpath = f'crop_down{level}x_{j}.png'
            rotation_mat = rotation_matrix(azimuth=2 * np.pi / 10, elevation=0)
            e.rotate(rotation_mat)
            crop = e.project(vfov=60, ar=16 / 9, resolution=(640, 360), rotation_matrix=rotation_mat).astype(np.uint8)
            imageio.imsave(outpath, crop)
        print(f'Level {level} using time: {time.time() - time_begin}')

def crop_pano_single(ns, record_date):
    print(f'In this process, we handle {record_date}')
    source_date_dir = os.path.join(ns['source_dir'], record_date)
    pano_filenames = os.listdir(source_date_dir)
    for azimuth_deg in range(0, 360, ns['degree_interval']):
        check_and_mkdirs(os.path.join(ns['target_dir'], str(azimuth_deg), record_date))
    for pano_filename in ns['selected_sample_dict'][record_date]:
        azimuth_deg = range(0, 360, ns['degree_interval'])[-1]
        pass_flag = os.path.exists(os.path.join(ns['target_dir'], str(azimuth_deg), record_date, pano_filename))
        if pass_flag:
            continue
        image = cv2.imread(os.path.join(source_date_dir, pano_filename))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB) / 255
        pano_envmap = EnvironmentMap(image, 'latlong')
        for azimuth_deg in range(0, 360, ns['degree_interval']):
            if os.path.exists(os.path.join(ns['target_dir'], str(azimuth_deg), record_date, pano_filename)):
                continue
            azimuth_rad = np.radians(azimuth_deg)
            rotation_mat_i = rotation_matrix(azimuth=azimuth_rad, elevation=0)
            img_crop = pano_envmap.project(vfov=ns['camera_vfov'], ar=ns['aspect_ratio'], resolution=(ns['crop_W'], ns['crop_H']), rotation_matrix=rotation_mat_i)
            img_crop = (img_crop * 255).astype(np.uint8)
            imageio.imsave(os.path.join(ns['target_dir'], str(azimuth_deg), record_date, pano_filename), img_crop)
            print(f'save to {os.path.join(ns['target_dir'], str(azimuth_deg), record_date, pano_filename)}')

def test_interpolate():
    e = EnvironmentMap('/home/yfl/workspace/dataset_ln/holicity_pano(full_resolution)/2008-07/8heFyix0weuW7Kzd6A_BLg.jpg', 'latlong')
    outpath = '/home/yfl/workspace/LDR_to_HDR/crop_scipy.png'
    rotation_mat = rotation_matrix(azimuth=np.pi / 6, elevation=0)
    crop = (e.project(vfov=60, ar=16 / 9, resolution=(640, 360), rotation_matrix=rotation_mat) * 255).astype(np.uint8)
    imageio.imsave(outpath, crop)

def motion_blur(image, degree=12, angle=45):
    """
    degree : intensity of blur
    angle : direction of blur. 
        angle = 0 is +u, angle = 90 is -v
    """
    image = np.array(image)
    angle -= 135
    M = cv2.getRotationMatrix2D((degree / 2, degree / 2), angle, 1)
    motion_blur_kernel = np.diag(np.ones(degree))
    motion_blur_kernel = cv2.warpAffine(motion_blur_kernel, M, (degree, degree))
    motion_blur_kernel = motion_blur_kernel / degree
    blurred = cv2.filter2D(image, -1, motion_blur_kernel)
    cv2.normalize(blurred, blurred, 0, 255, cv2.NORM_MINMAX)
    blurred = np.array(blurred, dtype=np.uint8)
    return blurred

def compose(rendered_output_dir, background_RGB, background_depth, render_downsample, motion_blur_degree, depth_and_occlusion):
    """
    Args:
        rendered_output_dir: str
            the folder that saves RGB/depth/mask for vehicle w/wo plane
        background_RGB: np.ndarray
            background image
        background_depth: np.ndarray
            background depth image
    """
    if depth_and_occlusion == False:
        RGB_over_background = read_from_render(rendered_output_dir, 'RGB', 'vehicle_and_shadow_over_background')
        H, W = RGB_over_background.shape[:2]
        RGB_over_background = cv2.resize(RGB_over_background, (render_downsample * W, render_downsample * H))
        RGB_over_background = RGB_over_background[:, :, :3]
        RGB_over_background = motion_blur(RGB_over_background, degree=motion_blur_degree, angle=45)
        imageio.imsave(os.path.join(rendered_output_dir, 'RGB_composite.png'), RGB_over_background)
        return
    depth_vp = read_from_render(rendered_output_dir, 'depth', 'vehicle_and_plane')
    depth_vp = expand_depth(depth_vp).astype(np.float32)
    RGB_over_background = read_from_render(rendered_output_dir, 'RGB', 'vehicle_and_shadow_over_background')
    mask_vs = read_from_render(rendered_output_dir, 'mask', 'vehicle_and_shadow')
    H, W = depth_vp.shape[:2]
    depth_vp = cv2.resize(depth_vp, (render_downsample * W, render_downsample * H))
    RGB_over_background = cv2.resize(RGB_over_background, (render_downsample * W, render_downsample * H))
    RGB_over_background = RGB_over_background[:, :, :3]
    RGB_over_background = motion_blur(RGB_over_background, degree=motion_blur_degree, angle=45)
    mask_vs = cv2.resize(mask_vs, (render_downsample * W, render_downsample * H))
    depth_vp = depth_vp[:, :, 0:1]
    mask_vs = mask_vs[:, :, 0:1]
    noise_thres = 0.02
    depth_vs = np.where(mask_vs > noise_thres, depth_vp, np.inf)
    RGB_composite = np.where(depth_vs <= background_depth[..., np.newaxis], RGB_over_background, background_RGB).astype(np.uint8)
    imageio.imsave(os.path.join(rendered_output_dir, 'RGB_composite.png'), RGB_composite)
    imageio.imsave(os.path.join(rendered_output_dir, 'RGB_over_background.png'), RGB_over_background)

