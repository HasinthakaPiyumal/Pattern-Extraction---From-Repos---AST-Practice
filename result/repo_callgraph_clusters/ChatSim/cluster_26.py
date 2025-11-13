# Cluster 26

def render_sets(args, iteration: int, skip_train: bool, skip_test: bool):
    with torch.no_grad():
        gaussians = GaussianModel(args)
        scene = Scene(args, gaussians, load_iteration=iteration, shuffle=False)
        bg_color = [1, 1, 1] if args.white_background else [0, 0, 0]
        background = torch.tensor(bg_color, dtype=torch.float32, device='cuda')
        if not skip_test:
            render_set(args, 'test', scene.loaded_iter, scene.getTestCameras(), gaussians, background)
        if not skip_train:
            render_set(args, 'train', scene.loaded_iter, scene.getTrainCameras(), gaussians, background)

def training(args):
    if TENSORBOARD_FOUND:
        tb_writer = SummaryWriter(args.model_path)
    else:
        tb_writer = None
        print('Tensorboard not available: not logging progress')
    first_iter = 0
    gaussians = GaussianModel(args)
    scene = Scene(args, gaussians)
    gaussians.training_setup(args)
    if args.start_checkpoint:
        model_params, first_iter = torch.load(args.start_checkpoint)
        gaussians.restore(model_params, args)
    bg_color = [1, 1, 1] if args.white_background else [0, 0, 0]
    background = torch.tensor(bg_color, dtype=torch.float32, device='cuda')
    iter_start = torch.cuda.Event(enable_timing=True)
    iter_end = torch.cuda.Event(enable_timing=True)
    viewpoint_stack = None
    ema_loss_for_log = 0.0
    progress_bar = tqdm(range(first_iter, args.iterations), desc='Training progress')
    first_iter += 1
    for iteration in range(first_iter, args.iterations + 1):
        if args.gui:
            if network_gui.conn == None:
                network_gui.try_connect()
            while network_gui.conn != None:
                try:
                    net_image_bytes = None
                    custom_cam, do_training, args.convert_SHs_python, args.compute_cov3D_python, keep_alive, scaling_modifer = network_gui.receive()
                    if custom_cam != None:
                        net_image = render(custom_cam, gaussians, args, background, scaling_modifer)['render']
                        net_image_bytes = memoryview((torch.clamp(net_image, min=0, max=1.0) * 255).byte().permute(1, 2, 0).contiguous().cpu().numpy())
                    network_gui.send(net_image_bytes, args.source_path)
                    if do_training and (iteration < int(args.iterations) or not keep_alive):
                        break
                except Exception as e:
                    network_gui.conn = None
        iter_start.record()
        gaussians.update_learning_rate(iteration)
        if iteration % 1000 == 0:
            gaussians.oneupSHdegree()
        if not viewpoint_stack:
            viewpoint_stack = scene.getTrainCameras().copy()
        viewpoint_cam = viewpoint_stack.pop(randint(0, len(viewpoint_stack) - 1))
        bg = torch.rand(3, device='cuda') if args.random_background else background
        render_pkg = render(viewpoint_cam, gaussians, args, bg, exposure_scale=viewpoint_cam.exposure_scale)
        image, viewspace_point_tensor, visibility_filter, radii = (render_pkg['render'], render_pkg['viewspace_points'], render_pkg['visibility_filter'], render_pkg['radii'])
        if args.render_depth:
            depth = render_pkg['depth']
        if args.render_opacity:
            opacity = render_pkg['opacity']
        loss_dict = {}
        gt_image = viewpoint_cam.original_image.cuda()
        loss_l1 = l1_loss(image, gt_image)
        loss_dict['l1_loss'] = loss_l1.item()
        loss_ssim = 1.0 - ssim(image, gt_image)
        loss_dict['ssim_loss'] = loss_ssim.item()
        loss = (1.0 - args.lambda_dssim) * loss_l1 + args.lambda_dssim * loss_ssim
        if args.get('lambda_opacity', 0.0) > 0.0:
            sky_mask = viewpoint_cam.sky_mask.cuda()
            opacity_mask = ~sky_mask
            opacity_mask = opacity_mask.float().unsqueeze(0)
            opacity = opacity.clamp(1e-06, 1.0 - 1e-06)
            loss_opacity = -(opacity_mask * torch.log(opacity) + (1 - opacity_mask) * torch.log(1 - opacity)).mean()
            loss += args.lambda_opacity * loss_opacity
            loss_dict['opacity_loss'] = loss_opacity.item()
        if args.get('lambda_depth', 0.0) > 0.0:
            depth_mask = depth_mask > 0
            loss_depth = (torch.abs(depth - viewpoint_cam.depth.to('cuda')) * depth_mask).mean()
            loss += args.lambda_depth * loss_depth
            loss_dict['depth_loss'] = loss_depth.item()
        loss.backward()
        iter_end.record()
        with torch.no_grad():
            ema_loss_for_log = 0.4 * loss.item() + 0.6 * ema_loss_for_log
            if iteration % 10 == 0:
                postfix_dict = {'EMA Loss': f'{ema_loss_for_log:.{3}f}'}
                for key, value in loss_dict.items():
                    postfix_dict[key] = f'{value:.{3}f}'
                progress_bar.set_postfix(postfix_dict)
                progress_bar.update(10)
            if iteration == args.iterations:
                progress_bar.close()
            training_report(tb_writer, iteration, loss_dict, iter_start.elapsed_time(iter_end), args.testing_iterations, scene, render, (args, background))
            if iteration in args.saving_iterations:
                print('\n[ITER {}] Saving Gaussians'.format(iteration))
                scene.save(iteration)
            if iteration < args.densify_until_iter:
                gaussians.max_radii2D[visibility_filter] = torch.max(gaussians.max_radii2D[visibility_filter], radii[visibility_filter])
                gaussians.add_densification_stats(viewspace_point_tensor, visibility_filter, image.shape[2], image.shape[1])
                if iteration > args.densify_from_iter and iteration % args.densification_interval == 0:
                    size_threshold = 20 if iteration > args.opacity_reset_interval else None
                    gaussians.densify_and_prune(args.densify_grad_threshold, 0.005, scene.cameras_extent, size_threshold)
                if iteration % args.opacity_reset_interval == 0 or (args.white_background and iteration == args.densify_from_iter):
                    gaussians.reset_opacity()
            if iteration < args.iterations:
                gaussians.optimizer.step()
                gaussians.optimizer.zero_grad(set_to_none=True)
            if iteration in args.checkpoint_iterations:
                print('\n[ITER {}] Saving Checkpoint'.format(iteration))
                torch.save((gaussians.capture(), iteration), scene.model_path + '/chkpnt' + str(iteration) + '.pth')

def training_report(tb_writer, iteration, loss_dict, elapsed, testing_iterations, scene: Scene, renderFunc, renderArgs):
    if tb_writer:
        for key, value in loss_dict.items():
            tb_writer.add_scalar(f'train/{key}', value, iteration)
    if iteration in testing_iterations:
        torch.cuda.empty_cache()
        validation_configs = ({'name': 'test', 'cameras': scene.getTestCameras()}, {'name': 'train', 'cameras': scene.getTrainCameras()})
        for config in validation_configs:
            if config['cameras'] and len(config['cameras']) > 0:
                l1_test = 0.0
                psnr_test = 0.0
                for idx, viewpoint in enumerate(config['cameras']):
                    image = torch.clamp(renderFunc(viewpoint, scene.gaussians, *renderArgs, exposure_scale=viewpoint.exposure_scale)['render'], 0.0, 1.0)
                    gt_image = torch.clamp(viewpoint.original_image.to('cuda'), 0.0, 1.0)
                    if tb_writer and idx < 5:
                        tb_writer.add_images(config['name'] + '_view_{}/render'.format(viewpoint.image_name), image[None], global_step=iteration)
                        if iteration == testing_iterations[0]:
                            tb_writer.add_images(config['name'] + '_view_{}/ground_truth'.format(viewpoint.image_name), gt_image[None], global_step=iteration)
                    l1_test += l1_loss(image, gt_image).mean().double()
                    psnr_test += psnr(image, gt_image).mean().double()
                psnr_test /= len(config['cameras'])
                l1_test /= len(config['cameras'])
                print('\n[ITER {}] Evaluating {}: L1 {} PSNR {}'.format(iteration, config['name'], l1_test, psnr_test))
                if tb_writer:
                    tb_writer.add_scalar(config['name'] + '/loss_viewpoint - l1_loss', l1_test, iteration)
                    tb_writer.add_scalar(config['name'] + '/loss_viewpoint - psnr', psnr_test, iteration)
        if tb_writer:
            tb_writer.add_histogram('scene/opacity_histogram', scene.gaussians.get_opacity, iteration)
            tb_writer.add_scalar('total_points', scene.gaussians.get_xyz.shape[0], iteration)
        torch.cuda.empty_cache()

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

def training_setup(self, training_args):
    self.percent_dense = training_args.percent_dense
    self.xyz_gradient_accum = torch.zeros((self.get_xyz.shape[0], 1), device='cuda')
    self.denom = torch.zeros((self.get_xyz.shape[0], 1), device='cuda')
    l = [{'params': [self._xyz], 'lr': training_args.position_lr_init * self.spatial_lr_scale, 'name': 'xyz'}, {'params': [self._features_dc], 'lr': training_args.feature_lr, 'name': 'f_dc'}, {'params': [self._features_rest], 'lr': training_args.feature_lr / 20.0, 'name': 'f_rest'}, {'params': [self._opacity], 'lr': training_args.opacity_lr, 'name': 'opacity'}, {'params': [self._scaling], 'lr': training_args.scaling_lr, 'name': 'scaling'}, {'params': [self._rotation], 'lr': training_args.rotation_lr, 'name': 'rotation'}]
    if self.sky_model is not None:
        l += ({'params': self.sky_model.train_params(), 'lr': training_args.sky_model_lr, 'name': 'sky_model'},)
    self.optimizer = torch.optim.Adam(l, lr=0.0, eps=1e-15)
    self.xyz_scheduler_args = get_expon_lr_func(lr_init=training_args.position_lr_init * self.spatial_lr_scale, lr_final=training_args.position_lr_final * self.spatial_lr_scale, lr_delay_mult=training_args.position_lr_delay_mult, max_steps=training_args.position_lr_max_steps)

class Trainer:

    def __init__(self, config, debug=False):
        self.config = config
        self.epoch = 0
        self.iteration = 0
        if debug:
            self.config['trainer']['save_freq'] = 5
            self.config['trainer']['valid_freq'] = 5
            self.config['trainer']['iterations'] = 5
        self.train_dataset = Dataset(config['data_loader'], split='train', debug=debug)
        self.train_sampler = None
        self.train_args = config['trainer']
        if config['distributed']:
            self.train_sampler = DistributedSampler(self.train_dataset, num_replicas=config['world_size'], rank=config['global_rank'])
        self.train_loader = DataLoader(self.train_dataset, batch_size=self.train_args['batch_size'] // config['world_size'], shuffle=self.train_sampler is None, num_workers=self.train_args['num_workers'], sampler=self.train_sampler)
        self.adversarial_loss = AdversarialLoss(type=self.config['losses']['GAN_LOSS'])
        self.adversarial_loss = self.adversarial_loss.to(self.config['device'])
        self.l1_loss = nn.L1Loss()
        net = importlib.import_module('model.' + config['model'])
        self.netG = net.InpaintGenerator()
        self.netG = self.netG.to(self.config['device'])
        self.netD = net.Discriminator(in_channels=3, use_sigmoid=config['losses']['GAN_LOSS'] != 'hinge')
        self.netD = self.netD.to(self.config['device'])
        self.optimG = torch.optim.Adam(self.netG.parameters(), lr=config['trainer']['lr'], betas=(self.config['trainer']['beta1'], self.config['trainer']['beta2']))
        self.optimD = torch.optim.Adam(self.netD.parameters(), lr=config['trainer']['lr'], betas=(self.config['trainer']['beta1'], self.config['trainer']['beta2']))
        self.load()
        if config['distributed']:
            self.netG = DDP(self.netG, device_ids=[self.config['local_rank']], output_device=self.config['local_rank'], broadcast_buffers=True, find_unused_parameters=False)
            self.netD = DDP(self.netD, device_ids=[self.config['local_rank']], output_device=self.config['local_rank'], broadcast_buffers=True, find_unused_parameters=False)
        self.dis_writer = None
        self.gen_writer = None
        self.summary = {}
        if self.config['global_rank'] == 0 or not config['distributed']:
            self.dis_writer = SummaryWriter(os.path.join(config['save_dir'], 'dis'))
            self.gen_writer = SummaryWriter(os.path.join(config['save_dir'], 'gen'))

    def get_lr(self):
        return self.optimG.param_groups[0]['lr']

    def adjust_learning_rate(self):
        decay = 0.1 ** (min(self.iteration, self.config['trainer']['niter_steady']) // self.config['trainer']['niter'])
        new_lr = self.config['trainer']['lr'] * decay
        if new_lr != self.get_lr():
            for param_group in self.optimG.param_groups:
                param_group['lr'] = new_lr
            for param_group in self.optimD.param_groups:
                param_group['lr'] = new_lr

    def add_summary(self, writer, name, val):
        if name not in self.summary:
            self.summary[name] = 0
        self.summary[name] += val
        if writer is not None and self.iteration % 100 == 0:
            writer.add_scalar(name, self.summary[name] / 100, self.iteration)
            self.summary[name] = 0

    def load(self):
        model_path = self.config['save_dir']
        if os.path.isfile(os.path.join(model_path, 'latest.ckpt')):
            latest_epoch = open(os.path.join(model_path, 'latest.ckpt'), 'r').read().splitlines()[-1]
        else:
            ckpts = [os.path.basename(i).split('.pth')[0] for i in glob.glob(os.path.join(model_path, '*.pth'))]
            ckpts.sort()
            latest_epoch = ckpts[-1] if len(ckpts) > 0 else None
        if latest_epoch is not None:
            gen_path = os.path.join(model_path, 'gen_{}.pth'.format(str(latest_epoch).zfill(5)))
            dis_path = os.path.join(model_path, 'dis_{}.pth'.format(str(latest_epoch).zfill(5)))
            opt_path = os.path.join(model_path, 'opt_{}.pth'.format(str(latest_epoch).zfill(5)))
            if self.config['global_rank'] == 0:
                print('Loading model from {}...'.format(gen_path))
            data = torch.load(gen_path, map_location=self.config['device'])
            self.netG.load_state_dict(data['netG'])
            data = torch.load(dis_path, map_location=self.config['device'])
            self.netD.load_state_dict(data['netD'])
            data = torch.load(opt_path, map_location=self.config['device'])
            self.optimG.load_state_dict(data['optimG'])
            self.optimD.load_state_dict(data['optimD'])
            self.epoch = data['epoch']
            self.iteration = data['iteration']
        elif self.config['global_rank'] == 0:
            print('Warnning: There is no trained model found. An initialized model will be used.')

    def save(self, it):
        if self.config['global_rank'] == 0:
            gen_path = os.path.join(self.config['save_dir'], 'gen_{}.pth'.format(str(it).zfill(5)))
            dis_path = os.path.join(self.config['save_dir'], 'dis_{}.pth'.format(str(it).zfill(5)))
            opt_path = os.path.join(self.config['save_dir'], 'opt_{}.pth'.format(str(it).zfill(5)))
            print('\nsaving model to {} ...'.format(gen_path))
            if isinstance(self.netG, torch.nn.DataParallel) or isinstance(self.netG, DDP):
                netG = self.netG.module
                netD = self.netD.module
            else:
                netG = self.netG
                netD = self.netD
            torch.save({'netG': netG.state_dict()}, gen_path)
            torch.save({'netD': netD.state_dict()}, dis_path)
            torch.save({'epoch': self.epoch, 'iteration': self.iteration, 'optimG': self.optimG.state_dict(), 'optimD': self.optimD.state_dict()}, opt_path)
            os.system('echo {} > {}'.format(str(it).zfill(5), os.path.join(self.config['save_dir'], 'latest.ckpt')))

    def train(self):
        pbar = range(int(self.train_args['iterations']))
        if self.config['global_rank'] == 0:
            pbar = tqdm(pbar, initial=self.iteration, dynamic_ncols=True, smoothing=0.01)
        while True:
            self.epoch += 1
            if self.config['distributed']:
                self.train_sampler.set_epoch(self.epoch)
            self._train_epoch(pbar)
            if self.iteration > self.train_args['iterations']:
                break
        print('\nEnd training....')

    def _train_epoch(self, pbar):
        device = self.config['device']
        for frames, masks in self.train_loader:
            self.adjust_learning_rate()
            self.iteration += 1
            frames, masks = (frames.to(device), masks.to(device))
            b, t, c, h, w = frames.size()
            masked_frame = frames * (1 - masks).float()
            pred_img = self.netG(masked_frame, masks)
            frames = frames.view(b * t, c, h, w)
            masks = masks.view(b * t, 1, h, w)
            comp_img = frames * (1.0 - masks) + masks * pred_img
            gen_loss = 0
            dis_loss = 0
            real_vid_feat = self.netD(frames)
            fake_vid_feat = self.netD(comp_img.detach())
            dis_real_loss = self.adversarial_loss(real_vid_feat, True, True)
            dis_fake_loss = self.adversarial_loss(fake_vid_feat, False, True)
            dis_loss += (dis_real_loss + dis_fake_loss) / 2
            self.add_summary(self.dis_writer, 'loss/dis_vid_fake', dis_fake_loss.item())
            self.add_summary(self.dis_writer, 'loss/dis_vid_real', dis_real_loss.item())
            self.optimD.zero_grad()
            dis_loss.backward()
            self.optimD.step()
            gen_vid_feat = self.netD(comp_img)
            gan_loss = self.adversarial_loss(gen_vid_feat, True, False)
            gan_loss = gan_loss * self.config['losses']['adversarial_weight']
            gen_loss += gan_loss
            self.add_summary(self.gen_writer, 'loss/gan_loss', gan_loss.item())
            hole_loss = self.l1_loss(pred_img * masks, frames * masks)
            hole_loss = hole_loss / torch.mean(masks) * self.config['losses']['hole_weight']
            gen_loss += hole_loss
            self.add_summary(self.gen_writer, 'loss/hole_loss', hole_loss.item())
            valid_loss = self.l1_loss(pred_img * (1 - masks), frames * (1 - masks))
            valid_loss = valid_loss / torch.mean(1 - masks) * self.config['losses']['valid_weight']
            gen_loss += valid_loss
            self.add_summary(self.gen_writer, 'loss/valid_loss', valid_loss.item())
            self.optimG.zero_grad()
            gen_loss.backward()
            self.optimG.step()
            if self.config['global_rank'] == 0:
                pbar.update(1)
                pbar.set_description(f'd: {dis_loss.item():.3f}; g: {gan_loss.item():.3f};hole: {hole_loss.item():.3f}; valid: {valid_loss.item():.3f}')
            if self.iteration % self.train_args['save_freq'] == 0:
                self.save(int(self.iteration // self.train_args['save_freq']))
            if self.iteration > self.train_args['iterations']:
                break

def add_summary(self, writer, name, val):
    if name not in self.summary:
        self.summary[name] = 0
    self.summary[name] += val
    if writer is not None and self.iteration % 100 == 0:
        writer.add_scalar(name, self.summary[name] / 100, self.iteration)
        self.summary[name] = 0

def _train_epoch(self, pbar):
    device = self.config['device']
    for frames, masks in self.train_loader:
        self.adjust_learning_rate()
        self.iteration += 1
        frames, masks = (frames.to(device), masks.to(device))
        b, t, c, h, w = frames.size()
        masked_frame = frames * (1 - masks).float()
        pred_img = self.netG(masked_frame, masks)
        frames = frames.view(b * t, c, h, w)
        masks = masks.view(b * t, 1, h, w)
        comp_img = frames * (1.0 - masks) + masks * pred_img
        gen_loss = 0
        dis_loss = 0
        real_vid_feat = self.netD(frames)
        fake_vid_feat = self.netD(comp_img.detach())
        dis_real_loss = self.adversarial_loss(real_vid_feat, True, True)
        dis_fake_loss = self.adversarial_loss(fake_vid_feat, False, True)
        dis_loss += (dis_real_loss + dis_fake_loss) / 2
        self.add_summary(self.dis_writer, 'loss/dis_vid_fake', dis_fake_loss.item())
        self.add_summary(self.dis_writer, 'loss/dis_vid_real', dis_real_loss.item())
        self.optimD.zero_grad()
        dis_loss.backward()
        self.optimD.step()
        gen_vid_feat = self.netD(comp_img)
        gan_loss = self.adversarial_loss(gen_vid_feat, True, False)
        gan_loss = gan_loss * self.config['losses']['adversarial_weight']
        gen_loss += gan_loss
        self.add_summary(self.gen_writer, 'loss/gan_loss', gan_loss.item())
        hole_loss = self.l1_loss(pred_img * masks, frames * masks)
        hole_loss = hole_loss / torch.mean(masks) * self.config['losses']['hole_weight']
        gen_loss += hole_loss
        self.add_summary(self.gen_writer, 'loss/hole_loss', hole_loss.item())
        valid_loss = self.l1_loss(pred_img * (1 - masks), frames * (1 - masks))
        valid_loss = valid_loss / torch.mean(1 - masks) * self.config['losses']['valid_weight']
        gen_loss += valid_loss
        self.add_summary(self.gen_writer, 'loss/valid_loss', valid_loss.item())
        self.optimG.zero_grad()
        gen_loss.backward()
        self.optimG.step()
        if self.config['global_rank'] == 0:
            pbar.update(1)
            pbar.set_description(f'd: {dis_loss.item():.3f}; g: {gan_loss.item():.3f};hole: {hole_loss.item():.3f}; valid: {valid_loss.item():.3f}')
        if self.iteration % self.train_args['save_freq'] == 0:
            self.save(int(self.iteration // self.train_args['save_freq']))
        if self.iteration > self.train_args['iterations']:
            break

def masked_l1_loss(pred, target, mask, weight_known, weight_missing):
    per_pixel_l1 = F.l1_loss(pred, target, reduction='none')
    pixel_weights = mask * weight_missing + (1 - mask) * weight_known
    return (pixel_weights * per_pixel_l1).mean()

class SimpleMultiStepGenerator(nn.Module):

    def __init__(self, steps: List[nn.Module]):
        super().__init__()
        self.steps = nn.ModuleList(steps)

    def forward(self, x):
        cur_in = x
        outs = []
        for step in self.steps:
            cur_out = step(cur_in)
            outs.append(cur_out)
            cur_in = torch.cat((cur_in, cur_out), dim=1)
        return torch.cat(outs[::-1], dim=1)

def forward(self, x):
    cur_in = x
    outs = []
    for step in self.steps:
        cur_out = step(cur_in)
        outs.append(cur_out)
        cur_in = torch.cat((cur_in, cur_out), dim=1)
    return torch.cat(outs[::-1], dim=1)

def _infer(image: torch.Tensor, mask: torch.Tensor, forward_front: nn.Module, forward_rears: nn.Module, ref_lower_res: torch.Tensor, orig_shape: tuple, devices: list, scale_ind: int, n_iters: int=15, lr: float=0.002):
    """Performs inference with refinement at a given scale.

    Parameters
    ----------
    image : torch.Tensor
        input image to be inpainted, of size (1,3,H,W)
    mask : torch.Tensor
        input inpainting mask, of size (1,1,H,W) 
    forward_front : nn.Module
        the front part of the inpainting network
    forward_rears : nn.Module
        the rear part of the inpainting network
    ref_lower_res : torch.Tensor
        the inpainting at previous scale, used as reference image
    orig_shape : tuple
        shape of the original input image before padding
    devices : list
        list of available devices
    scale_ind : int
        the scale index
    n_iters : int, optional
        number of iterations of refinement, by default 15
    lr : float, optional
        learning rate, by default 0.002

    Returns
    -------
    torch.Tensor
        inpainted image
    """
    masked_image = image * (1 - mask)
    masked_image = torch.cat([masked_image, mask], dim=1)
    mask = mask.repeat(1, 3, 1, 1)
    if ref_lower_res is not None:
        ref_lower_res = ref_lower_res.detach()
    with torch.no_grad():
        z1, z2 = forward_front(masked_image)
    mask = mask.to(devices[-1])
    ekernel = torch.from_numpy(cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)).astype(bool)).float()
    ekernel = ekernel.to(devices[-1])
    image = image.to(devices[-1])
    z1, z2 = (z1.detach().to(devices[0]), z2.detach().to(devices[0]))
    z1.requires_grad, z2.requires_grad = (True, True)
    optimizer = Adam([z1, z2], lr=lr)
    pbar = tqdm(range(n_iters), leave=False)
    for idi in pbar:
        optimizer.zero_grad()
        input_feat = (z1, z2)
        for idd, forward_rear in enumerate(forward_rears):
            output_feat = forward_rear(input_feat)
            if idd < len(devices) - 1:
                midz1, midz2 = output_feat
                midz1, midz2 = (midz1.to(devices[idd + 1]), midz2.to(devices[idd + 1]))
                input_feat = (midz1, midz2)
            else:
                pred = output_feat
        if ref_lower_res is None:
            break
        losses = {}
        pred_downscaled = _pyrdown(pred[:, :, :orig_shape[0], :orig_shape[1]])
        mask_downscaled = _pyrdown_mask(mask[:, :1, :orig_shape[0], :orig_shape[1]], blur_mask=False, round_up=False)
        mask_downscaled = _erode_mask(mask_downscaled, ekernel=ekernel)
        mask_downscaled = mask_downscaled.repeat(1, 3, 1, 1)
        losses['ms_l1'] = _l1_loss(pred, pred_downscaled, ref_lower_res, mask, mask_downscaled, image, on_pred=True)
        loss = sum(losses.values())
        pbar.set_description('Refining scale {} using scale {} ...current loss: {:.4f}'.format(scale_ind + 1, scale_ind, loss.item()))
        if idi < n_iters - 1:
            loss.backward()
            optimizer.step()
            del pred_downscaled
            del loss
            del pred
    inpainted = mask * pred + (1 - mask) * image
    inpainted = inpainted.detach().cpu()
    return inpainted

def _get_image_mask_pyramid(batch: dict, min_side: int, max_scales: int, px_budget: int):
    """Build the image mask pyramid

    Parameters
    ----------
    batch : dict
        batch containing image, mask, etc
    min_side : int
        minimum side length to limit the number of scales of the pyramid 
    max_scales : int
        maximum number of scales allowed
    px_budget : int
        the product H*W cannot exceed this budget, because of resource constraints

    Returns
    -------
    tuple
        image-mask pyramid in the form of list of images and list of masks
    """
    assert batch['image'].shape[0] == 1, 'refiner works on only batches of size 1!'
    h, w = batch['unpad_to_size']
    h, w = (h[0].item(), w[0].item())
    image = batch['image'][..., :h, :w]
    mask = batch['mask'][..., :h, :w]
    if h * w > px_budget:
        ratio = np.sqrt(px_budget / float(h * w))
        h_orig, w_orig = (h, w)
        h, w = (int(h * ratio), int(w * ratio))
        print(f'Original image too large for refinement! Resizing {(h_orig, w_orig)} to {(h, w)}...')
        image = resize(image, (h, w), interpolation='bilinear', align_corners=False)
        mask = resize(mask, (h, w), interpolation='bilinear', align_corners=False)
        mask[mask > 1e-08] = 1
    breadth = min(h, w)
    n_scales = min(1 + int(round(max(0, np.log2(breadth / min_side)))), max_scales)
    ls_images = []
    ls_masks = []
    ls_images.append(image)
    ls_masks.append(mask)
    for _ in range(n_scales - 1):
        image_p = _pyrdown(ls_images[-1])
        mask_p = _pyrdown_mask(ls_masks[-1])
        ls_images.append(image_p)
        ls_masks.append(mask_p)
    return (ls_images[::-1], ls_masks[::-1])

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

def optimize_parameters(self):
    self.forward_train()
    self.optimizer_net.zero_grad()
    self.backward_train()
    self.optimizer_net.step()
    self.clamp_weights()

def masked_l1_loss(pred, target, mask, weight_known, weight_missing):
    per_pixel_l1 = F.l1_loss(pred, target, reduction='none')
    pixel_weights = mask * weight_missing + (1 - mask) * weight_known
    return (pixel_weights * per_pixel_l1).mean()

class SimpleMultiStepGenerator(nn.Module):

    def __init__(self, steps: List[nn.Module]):
        super().__init__()
        self.steps = nn.ModuleList(steps)

    def forward(self, x):
        cur_in = x
        outs = []
        for step in self.steps:
            cur_out = step(cur_in)
            outs.append(cur_out)
            cur_in = torch.cat((cur_in, cur_out), dim=1)
        return torch.cat(outs[::-1], dim=1)

def forward(self, x):
    cur_in = x
    outs = []
    for step in self.steps:
        cur_out = step(cur_in)
        outs.append(cur_out)
        cur_in = torch.cat((cur_in, cur_out), dim=1)
    return torch.cat(outs[::-1], dim=1)

def _infer(image: torch.Tensor, mask: torch.Tensor, forward_front: nn.Module, forward_rears: nn.Module, ref_lower_res: torch.Tensor, orig_shape: tuple, devices: list, scale_ind: int, n_iters: int=15, lr: float=0.002):
    """Performs inference with refinement at a given scale.

    Parameters
    ----------
    image : torch.Tensor
        input image to be inpainted, of size (1,3,H,W)
    mask : torch.Tensor
        input inpainting mask, of size (1,1,H,W) 
    forward_front : nn.Module
        the front part of the inpainting network
    forward_rears : nn.Module
        the rear part of the inpainting network
    ref_lower_res : torch.Tensor
        the inpainting at previous scale, used as reference image
    orig_shape : tuple
        shape of the original input image before padding
    devices : list
        list of available devices
    scale_ind : int
        the scale index
    n_iters : int, optional
        number of iterations of refinement, by default 15
    lr : float, optional
        learning rate, by default 0.002

    Returns
    -------
    torch.Tensor
        inpainted image
    """
    masked_image = image * (1 - mask)
    masked_image = torch.cat([masked_image, mask], dim=1)
    mask = mask.repeat(1, 3, 1, 1)
    if ref_lower_res is not None:
        ref_lower_res = ref_lower_res.detach()
    with torch.no_grad():
        z1, z2 = forward_front(masked_image)
    mask = mask.to(devices[-1])
    ekernel = torch.from_numpy(cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)).astype(bool)).float()
    ekernel = ekernel.to(devices[-1])
    image = image.to(devices[-1])
    z1, z2 = (z1.detach().to(devices[0]), z2.detach().to(devices[0]))
    z1.requires_grad, z2.requires_grad = (True, True)
    optimizer = Adam([z1, z2], lr=lr)
    pbar = tqdm(range(n_iters), leave=False)
    for idi in pbar:
        optimizer.zero_grad()
        input_feat = (z1, z2)
        for idd, forward_rear in enumerate(forward_rears):
            output_feat = forward_rear(input_feat)
            if idd < len(devices) - 1:
                midz1, midz2 = output_feat
                midz1, midz2 = (midz1.to(devices[idd + 1]), midz2.to(devices[idd + 1]))
                input_feat = (midz1, midz2)
            else:
                pred = output_feat
        if ref_lower_res is None:
            break
        losses = {}
        pred_downscaled = _pyrdown(pred[:, :, :orig_shape[0], :orig_shape[1]])
        mask_downscaled = _pyrdown_mask(mask[:, :1, :orig_shape[0], :orig_shape[1]], blur_mask=False, round_up=False)
        mask_downscaled = _erode_mask(mask_downscaled, ekernel=ekernel)
        mask_downscaled = mask_downscaled.repeat(1, 3, 1, 1)
        losses['ms_l1'] = _l1_loss(pred, pred_downscaled, ref_lower_res, mask, mask_downscaled, image, on_pred=True)
        loss = sum(losses.values())
        pbar.set_description('Refining scale {} using scale {} ...current loss: {:.4f}'.format(scale_ind + 1, scale_ind, loss.item()))
        if idi < n_iters - 1:
            loss.backward()
            optimizer.step()
            del pred_downscaled
            del loss
            del pred
    inpainted = mask * pred + (1 - mask) * image
    inpainted = inpainted.detach().cpu()
    return inpainted

def _get_image_mask_pyramid(batch: dict, min_side: int, max_scales: int, px_budget: int):
    """Build the image mask pyramid

    Parameters
    ----------
    batch : dict
        batch containing image, mask, etc
    min_side : int
        minimum side length to limit the number of scales of the pyramid 
    max_scales : int
        maximum number of scales allowed
    px_budget : int
        the product H*W cannot exceed this budget, because of resource constraints

    Returns
    -------
    tuple
        image-mask pyramid in the form of list of images and list of masks
    """
    assert batch['image'].shape[0] == 1, 'refiner works on only batches of size 1!'
    h, w = batch['unpad_to_size']
    h, w = (h[0].item(), w[0].item())
    image = batch['image'][..., :h, :w]
    mask = batch['mask'][..., :h, :w]
    if h * w > px_budget:
        ratio = np.sqrt(px_budget / float(h * w))
        h_orig, w_orig = (h, w)
        h, w = (int(h * ratio), int(w * ratio))
        print(f'Original image too large for refinement! Resizing {(h_orig, w_orig)} to {(h, w)}...')
        image = resize(image, (h, w), interpolation='bilinear', align_corners=False)
        mask = resize(mask, (h, w), interpolation='bilinear', align_corners=False)
        mask[mask > 1e-08] = 1
    breadth = min(h, w)
    n_scales = min(1 + int(round(max(0, np.log2(breadth / min_side)))), max_scales)
    ls_images = []
    ls_masks = []
    ls_images.append(image)
    ls_masks.append(mask)
    for _ in range(n_scales - 1):
        image_p = _pyrdown(ls_images[-1])
        mask_p = _pyrdown_mask(ls_masks[-1])
        ls_images.append(image_p)
        ls_masks.append(mask_p)
    return (ls_images[::-1], ls_masks[::-1])

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

def optimize_parameters(self):
    self.forward_train()
    self.optimizer_net.zero_grad()
    self.backward_train()
    self.optimizer_net.step()
    self.clamp_weights()

def calculate_ssim(img1, img2, border=0):
    """calculate SSIM
    the same outputs as MATLAB's
    img1, img2: [0, 255]
    """
    if not img1.shape == img2.shape:
        raise ValueError('Input images must have the same dimensions.')
    h, w = img1.shape[:2]
    img1 = img1[border:h - border, border:w - border]
    img2 = img2[border:h - border, border:w - border]
    if img1.ndim == 2:
        return ssim(img1, img2)
    elif img1.ndim == 3:
        if img1.shape[2] == 3:
            ssims = []
            for i in range(3):
                ssims.append(ssim(img1[:, :, i], img2[:, :, i]))
            return np.array(ssims).mean()
        elif img1.shape[2] == 1:
            return ssim(np.squeeze(img1), np.squeeze(img2))
    else:
        raise ValueError('Wrong input image dimensions.')

class AutoencoderKL(pl.LightningModule):

    def __init__(self, ddconfig, lossconfig, embed_dim, ckpt_path=None, ignore_keys=[], image_key='image', colorize_nlabels=None, monitor=None):
        super().__init__()
        self.image_key = image_key
        self.encoder = Encoder(**ddconfig)
        self.decoder = Decoder(**ddconfig)
        self.loss = instantiate_from_config(lossconfig)
        assert ddconfig['double_z']
        self.quant_conv = torch.nn.Conv2d(2 * ddconfig['z_channels'], 2 * embed_dim, 1)
        self.post_quant_conv = torch.nn.Conv2d(embed_dim, ddconfig['z_channels'], 1)
        self.embed_dim = embed_dim
        if colorize_nlabels is not None:
            assert type(colorize_nlabels) == int
            self.register_buffer('colorize', torch.randn(3, colorize_nlabels, 1, 1))
        if monitor is not None:
            self.monitor = monitor
        if ckpt_path is not None:
            self.init_from_ckpt(ckpt_path, ignore_keys=ignore_keys)

    def init_from_ckpt(self, path, ignore_keys=list()):
        sd = torch.load(path, map_location='cpu')['state_dict']
        keys = list(sd.keys())
        for k in keys:
            for ik in ignore_keys:
                if k.startswith(ik):
                    print('Deleting key {} from state_dict.'.format(k))
                    del sd[k]
        self.load_state_dict(sd, strict=False)
        print(f'Restored from {path}')

    def encode(self, x):
        h = self.encoder(x)
        moments = self.quant_conv(h)
        posterior = DiagonalGaussianDistribution(moments)
        return posterior

    def decode(self, z):
        z = self.post_quant_conv(z)
        dec = self.decoder(z)
        return dec

    def forward(self, input, sample_posterior=True):
        posterior = self.encode(input)
        if sample_posterior:
            z = posterior.sample()
        else:
            z = posterior.mode()
        dec = self.decode(z)
        return (dec, posterior)

    def get_input(self, batch, k):
        x = batch[k]
        if len(x.shape) == 3:
            x = x[..., None]
        x = x.permute(0, 3, 1, 2).to(memory_format=torch.contiguous_format).float()
        return x

    def training_step(self, batch, batch_idx, optimizer_idx):
        inputs = self.get_input(batch, self.image_key)
        reconstructions, posterior = self(inputs)
        if optimizer_idx == 0:
            aeloss, log_dict_ae = self.loss(inputs, reconstructions, posterior, optimizer_idx, self.global_step, last_layer=self.get_last_layer(), split='train')
            self.log('aeloss', aeloss, prog_bar=True, logger=True, on_step=True, on_epoch=True)
            self.log_dict(log_dict_ae, prog_bar=False, logger=True, on_step=True, on_epoch=False)
            return aeloss
        if optimizer_idx == 1:
            discloss, log_dict_disc = self.loss(inputs, reconstructions, posterior, optimizer_idx, self.global_step, last_layer=self.get_last_layer(), split='train')
            self.log('discloss', discloss, prog_bar=True, logger=True, on_step=True, on_epoch=True)
            self.log_dict(log_dict_disc, prog_bar=False, logger=True, on_step=True, on_epoch=False)
            return discloss

    def validation_step(self, batch, batch_idx):
        inputs = self.get_input(batch, self.image_key)
        reconstructions, posterior = self(inputs)
        aeloss, log_dict_ae = self.loss(inputs, reconstructions, posterior, 0, self.global_step, last_layer=self.get_last_layer(), split='val')
        discloss, log_dict_disc = self.loss(inputs, reconstructions, posterior, 1, self.global_step, last_layer=self.get_last_layer(), split='val')
        self.log('val/rec_loss', log_dict_ae['val/rec_loss'])
        self.log_dict(log_dict_ae)
        self.log_dict(log_dict_disc)
        return self.log_dict

    def configure_optimizers(self):
        lr = self.learning_rate
        opt_ae = torch.optim.Adam(list(self.encoder.parameters()) + list(self.decoder.parameters()) + list(self.quant_conv.parameters()) + list(self.post_quant_conv.parameters()), lr=lr, betas=(0.5, 0.9))
        opt_disc = torch.optim.Adam(self.loss.discriminator.parameters(), lr=lr, betas=(0.5, 0.9))
        return ([opt_ae, opt_disc], [])

    def get_last_layer(self):
        return self.decoder.conv_out.weight

    @torch.no_grad()
    def log_images(self, batch, only_inputs=False, **kwargs):
        log = dict()
        x = self.get_input(batch, self.image_key)
        x = x.to(self.device)
        if not only_inputs:
            xrec, posterior = self(x)
            if x.shape[1] > 3:
                assert xrec.shape[1] > 3
                x = self.to_rgb(x)
                xrec = self.to_rgb(xrec)
            log['samples'] = self.decode(torch.randn_like(posterior.sample()))
            log['reconstructions'] = xrec
        log['inputs'] = x
        return log

    def to_rgb(self, x):
        assert self.image_key == 'segmentation'
        if not hasattr(self, 'colorize'):
            self.register_buffer('colorize', torch.randn(3, x.shape[1], 1, 1).to(x))
        x = F.conv2d(x, weight=self.colorize)
        x = 2.0 * (x - x.min()) / (x.max() - x.min()) - 1.0
        return x

def configure_optimizers(self):
    lr = self.learning_rate
    opt_ae = torch.optim.Adam(list(self.encoder.parameters()) + list(self.decoder.parameters()) + list(self.quant_conv.parameters()) + list(self.post_quant_conv.parameters()), lr=lr, betas=(0.5, 0.9))
    opt_disc = torch.optim.Adam(self.loss.discriminator.parameters(), lr=lr, betas=(0.5, 0.9))
    return ([opt_ae, opt_disc], [])

def main():
    renderer = Renderer('/home/yfl/Desktop/3d_assets/chevrolet_suv2/chevrolet.obj')
    renderer.read_env('/home/yfl/workspace/dataset_ln/HDR_ours/train/kloppenheim_05_1k.exr')
    renderer.read_ext()
    renderer.read_int()
    renderer.render()

def parallel_rendering(scene, inter_dict, ids):
    sub_render = subRender(scene, inter_dict)
    return sub_render.render(ids)

def main():
    renderer = Renderer('/home/yfl/Desktop/3d_assets/chevrolet_suv/chevrolet-suv-rigged_waymo_sunny1.obj')
    renderer.read_env('/home/yfl/workspace/dataset_ln/HDR_ours/train/abandoned_parking_1k.exr')
    renderer.read_ext()
    renderer.read_int()
    renderer.render()

class SkyModel(pl.LightningModule):

    def __init__(self, hypes):
        super().__init__()
        self.hypes = hypes
        downsample = hypes['dataset']['downsample']
        self.sky_H = hypes['dataset']['image_H'] // downsample // 2
        self.sky_W = hypes['dataset']['image_W'] // downsample
        self.teacher_prob = hypes['model']['teacher_prob']
        self.env_template = EnvironmentMap(self.sky_H, 'skylatlong')
        world_coord = self.env_template.worldCoordinates()
        self.pos_encoding = torch.from_numpy(np.stack([world_coord[0], world_coord[1], world_coord[2]], axis=-1))
        self.pos_encoding = self.pos_encoding.to('cuda')
        self.input_inv_gamma = hypes['model']['input_inv_gamma']
        self.input_add_pe = hypes['model']['input_add_pe']
        self.encoder_outdim = hypes['model']['ldr_encoder']['args']['layer_channels'][-1]
        self.feat_down = reduce(lambda x, y: x * y, hypes['model']['ldr_encoder']['args']['strides'])
        self.save_hyperparameters()
        self.ldr_encoder = build_module(hypes['model']['ldr_encoder'])
        self.shared_mlp = build_module(hypes['model']['shared_mlp'])
        self.latent_mlp = build_module(hypes['model']['latent_mlp'])
        self.latent_mlp_recon = build_module(hypes['model']['latent_mlp_recon'])
        self.peak_dir_mlp = build_module(hypes['model']['peak_dir_mlp'])
        self.peak_int_mlp = build_module(hypes['model']['peak_int_mlp'])
        self.ldr_decoder = nn.Sequential(build_module(hypes['model']['ldr_decoder']), nn.Sigmoid())
        self.hdr_decoder = build_module(hypes['model']['hdr_decoder'])
        self.ldr_recon_loss = build_loss(hypes['loss']['ldr_recon_loss'])
        self.hdr_recon_loss = build_loss(hypes['loss']['hdr_recon_loss'])
        self.peak_int_loss = build_loss(hypes['loss']['peak_int_loss'])
        self.peak_dir_loss = build_loss(hypes['loss']['peak_dir_loss'])
        self.fix_modules = hypes['model'].get('fix_modules', [])
        self.on_train_epoch_start()

    def encode_forward(self, x):
        """
        Encode LDR panorama to sky vector: 
            1) peak dir 
            2) peak int 
            3) latent vector
            where 1) and 2) can cat together
        
        deep vector -> shared vector -->    latent vector      --> recon deep vector 
                                     |
                                     .->  peak int/dir vector

        Should we add explicit inv gamma to the input?
        """
        if self.input_inv_gamma:
            x = srgb_inv_gamma_correction_torch(x)
        if self.input_add_pe:
            x = x + self.pos_encoding.permute(2, 0, 1)
        deep_feature = self.ldr_encoder(x)
        deep_vector = deep_feature.permute(0, 2, 3, 1).flatten(1)
        shared_vector = self.shared_mlp(deep_vector)
        peak_dir_vector = self.peak_dir_mlp(shared_vector)
        peak_int_vector = self.peak_int_mlp(shared_vector)
        latent_vector = self.latent_mlp(shared_vector)
        peak_dir_vector = peak_dir_vector / peak_dir_vector.norm(dim=1, keepdim=True)
        peak_vector = torch.cat([peak_dir_vector, peak_int_vector], dim=-1)
        return (peak_vector, latent_vector)

    def decode_forward(self, latent_vector, peak_vector, peak_vector_gt):
        use_gt_peak = False
        if self.training and np.random.rand() < self.teacher_prob:
            use_gt_peak = True
            peak_vector = peak_vector_gt
        B = peak_vector.shape[0]
        peak_dir_encoding, peak_int_encoding = self.build_peak_map(peak_vector)
        decoder_input = torch.cat([peak_dir_encoding, peak_int_encoding, self.pos_encoding.expand(B, -1, -1, -1)], dim=-1)
        decoder_input = decoder_input.permute(0, 3, 1, 2)
        recon_deep_vector = self.latent_mlp_recon(latent_vector)
        recon_deep_feature = recon_deep_vector.view(B, self.sky_H // self.feat_down, self.sky_W // self.feat_down, self.encoder_outdim).permute(0, 3, 1, 2)
        ldr_skypano_recon = self.ldr_decoder(recon_deep_feature)
        hdr_skypano_recon = self.hdr_decoder(decoder_input, recon_deep_feature)
        return (hdr_skypano_recon, ldr_skypano_recon, use_gt_peak)

    def build_peak_map(self, peak_vector):
        """
        Args:
            peak_vector: [B, 6]
                3 for peak dir, 3 for peak intensity

        Returns:
            peak encoding map: [B, 4, H, W]
                1 for peak dir using spherical gaussian lobe, 3 for peak intensity
        """
        dir_vector = peak_vector[..., :3]
        int_vector = peak_vector[..., 3:]
        dir_vector_expand = dir_vector.unsqueeze(1).unsqueeze(1).expand(-1, self.sky_H, self.sky_W, -1)
        peak_dir_encoding = torch.exp(100 * (torch.einsum('nhwc,nhwc->nhw', dir_vector_expand, self.pos_encoding.expand(dir_vector_expand.shape)) - 1)).unsqueeze(-1)
        sun_mask = torch.gt(peak_dir_encoding, 0.9).expand(-1, -1, -1, 3)
        int_vector_expand = int_vector.unsqueeze(1).unsqueeze(1).expand(-1, self.sky_H, self.sky_W, -1)
        peak_int_encoding = torch.where(sun_mask, int_vector_expand, 0)
        return (peak_dir_encoding, peak_int_encoding)

    def on_train_epoch_start(self):
        print(f'Module fixed in training: {self.fix_modules}.')
        for module in self.fix_modules:
            for p in eval(f'self.{module}').parameters():
                p.requires_grad_(False)
            eval(f'self.{module}').eval()

    def training_step(self, batch, batch_idx):
        ldr_skypano, hdr_skypano_gt, peak_vector_gt = batch
        peak_vector_pred, latent_vector = self.encode_forward(ldr_skypano)
        hdr_skypano_pred, ldr_skypano_recon, _ = self.decode_forward(latent_vector, peak_vector_pred, peak_vector_gt)
        ldr_recon_loss = self.ldr_recon_loss(ldr_skypano_recon, ldr_skypano)
        hdr_recon_loss = self.hdr_recon_loss(hdr_skypano_pred, hdr_skypano_gt)
        peak_dir_loss = self.peak_dir_loss(peak_vector_pred[..., :3], peak_vector_gt[..., :3])
        peak_int_loss = self.peak_int_loss(peak_vector_pred[..., 3:], peak_vector_gt[..., 3:])
        loss = hdr_recon_loss + peak_dir_loss + peak_int_loss + ldr_recon_loss
        self.log('train_loss', loss)
        self.log('hdr_recon_loss', hdr_recon_loss)
        self.log('ldr_recon_loss', ldr_recon_loss)
        self.log('peak_dir_loss', peak_dir_loss)
        self.log('peak_int_loss', peak_int_loss)
        log_info = f'|| loss: {loss:.3f} || hdr_recon_loss: {hdr_recon_loss:.3f}  || ldr_recon_loss: {ldr_recon_loss:.3f} || peak_dir_loss: {peak_dir_loss:.3f} ' + f'|| peak_int_loss: {peak_int_loss:.3f}'
        print(log_info)
        return loss

    def validation_step(self, batch, batch_idx):
        ldr_skypano, hdr_skypano_gt, peak_vector_gt = batch
        peak_vector_pred, latent_vector = self.encode_forward(ldr_skypano)
        hdr_skypano_pred, ldr_skypano_recon, _ = self.decode_forward(latent_vector, peak_vector_pred, peak_vector_pred)
        ldr_recon_loss = self.ldr_recon_loss(ldr_skypano_recon, ldr_skypano)
        hdr_recon_loss = self.hdr_recon_loss(hdr_skypano_pred, hdr_skypano_gt)
        loss = hdr_recon_loss
        self.log('val_loss', loss)
        return loss

    def test_step(self, batch, batch_idx):
        return self.validation_step(batch, batch_idx)

    def predict_step(self, batch, batch_idx):
        ldr_skypano, hdr_skypano_gt, peak_vector_gt = batch
        peak_vector_pred, latent_vector = self.encode_forward(ldr_skypano)
        hdr_skypano_pred, ldr_skypano_recon, _ = self.decode_forward(latent_vector, peak_vector_pred, peak_vector_pred)
        print(f'{batch_idx:0>3} \n                  HDRI Peak Intensity:\t\t {hdr_skypano_pred[0].flatten(1, 2).max(dim=-1)[0]} \n                  Peak Intensity Vector:\t {peak_vector_pred[0][3:]} \n                  Ground Truth Peak Intensity:\t {peak_vector_gt[0][3:]}')
        return_dict = {'ldr_skypano_input': ldr_skypano.permute(0, 2, 3, 1), 'ldr_skypano_pred': ldr_skypano_recon.permute(0, 2, 3, 1), 'hdr_skypano_gt': hdr_skypano_gt.permute(0, 2, 3, 1), 'hdr_skypano_pred': hdr_skypano_pred.permute(0, 2, 3, 1), 'batch_idx': batch_idx}
        return return_dict

    def configure_optimizers(self):
        optimizer = torch.optim.Adam(self.parameters(), lr=self.hypes['lr_schedule']['init_lr'])
        lr_scheduler = StepLR(optimizer=optimizer, step_size=self.hypes['lr_schedule']['decay_per_epoch'], gamma=self.hypes['lr_schedule']['decay_rate'])
        return ([optimizer], [lr_scheduler])

def configure_optimizers(self):
    optimizer = torch.optim.Adam(self.parameters(), lr=self.hypes['lr_schedule']['init_lr'])
    lr_scheduler = StepLR(optimizer=optimizer, step_size=self.hypes['lr_schedule']['decay_per_epoch'], gamma=self.hypes['lr_schedule']['decay_rate'])
    return ([optimizer], [lr_scheduler])

class SkyModelEnhanced(pl.LightningModule):

    def __init__(self, hypes):
        super().__init__()
        self.hypes = hypes
        downsample = hypes['dataset']['downsample']
        self.sky_H = hypes['dataset']['image_H'] // downsample // 2
        self.sky_W = hypes['dataset']['image_W'] // downsample
        self.teacher_prob = hypes['model']['teacher_prob']
        self.env_template = EnvironmentMap(self.sky_H, 'skylatlong')
        world_coord = self.env_template.worldCoordinates()
        self.pos_encoding = torch.from_numpy(np.stack([world_coord[0], world_coord[1], world_coord[2]], axis=-1))
        self.pos_encoding = self.pos_encoding.to('cuda')
        self.input_inv_gamma = hypes['model']['input_inv_gamma']
        self.input_add_pe = hypes['model']['input_add_pe']
        self.encoder_outdim = hypes['model']['ldr_encoder']['args']['layer_channels'][-1]
        self.feat_down = reduce(lambda x, y: x * y, hypes['model']['ldr_encoder']['args']['strides'])
        self.sum_lobe_thres = hypes['model'].get('sum_lobe_thres', 0.9)
        self.save_hyperparameters()
        self.ldr_encoder = build_module(hypes['model']['ldr_encoder'])
        self.shared_mlp = build_module(hypes['model']['shared_mlp'])
        self.latent_mlp = build_module(hypes['model']['latent_mlp'])
        self.latent_mlp_recon = build_module(hypes['model']['latent_mlp_recon'])
        self.peak_dir_mlp = build_module(hypes['model']['peak_dir_mlp'])
        self.peak_int_mlp = build_module(hypes['model']['peak_int_mlp'])
        self.ldr_decoder = nn.Sequential(build_module(hypes['model']['ldr_decoder']), nn.Sigmoid())
        self.hdr_decoder = build_module(hypes['model']['hdr_decoder'])
        self.ldr_recon_loss = build_loss(hypes['loss']['ldr_recon_loss'])
        self.hdr_recon_loss = build_loss(hypes['loss']['hdr_recon_loss'])
        self.peak_int_loss = build_loss(hypes['loss']['peak_int_loss'])
        self.peak_dir_loss = build_loss(hypes['loss']['peak_dir_loss'])
        self.fix_modules = hypes['model'].get('fix_modules', [])
        self.on_train_epoch_start()

    def encode_forward(self, x):
        """
        Encode LDR panorama to sky vector: 
            1) peak dir 
            2) peak int 
            3) latent vector
            where 1) and 2) can cat together
        
        deep vector -> shared vector -->    latent vector      --> recon deep vector 
                                     |
                                     .->  peak int/dir vector

        Should we add explicit inv gamma to the input?
        """
        if self.input_inv_gamma:
            x = srgb_inv_gamma_correction_torch(x)
        if self.input_add_pe:
            x = x + self.pos_encoding.permute(2, 0, 1)
        deep_feature = self.ldr_encoder(x)
        deep_vector = deep_feature.permute(0, 2, 3, 1).flatten(1)
        shared_vector = self.shared_mlp(deep_vector)
        peak_dir_vector = self.peak_dir_mlp(shared_vector)
        peak_int_vector = self.peak_int_mlp(shared_vector)
        latent_vector = self.latent_mlp(shared_vector)
        peak_dir_vector = peak_dir_vector / peak_dir_vector.norm(dim=1, keepdim=True)
        peak_vector = torch.cat([peak_dir_vector, peak_int_vector], dim=-1)
        return (peak_vector, latent_vector)

    def decode_forward(self, latent_vector, peak_vector, peak_vector_gt):
        use_gt_peak = False
        if self.training and np.random.rand() < self.teacher_prob:
            use_gt_peak = True
            peak_vector = peak_vector_gt
        B = peak_vector.shape[0]
        peak_dir_encoding, peak_int_encoding, sum_mask = self.build_peak_map(peak_vector)
        decoder_input = torch.cat([peak_dir_encoding, peak_int_encoding, self.pos_encoding.expand(B, -1, -1, -1)], dim=-1)
        decoder_input = decoder_input.permute(0, 3, 1, 2)
        recon_deep_vector = self.latent_mlp_recon(latent_vector)
        recon_deep_feature = recon_deep_vector.view(B, self.sky_H // self.feat_down, self.sky_W // self.feat_down, self.encoder_outdim).permute(0, 3, 1, 2)
        ldr_skypano_recon = self.ldr_decoder(recon_deep_feature)
        hdr_skypano_recon = self.hdr_decoder(decoder_input, recon_deep_feature)
        sum_mask = sum_mask.permute(0, 3, 1, 2)
        sun_peak_map = peak_dir_encoding.permute(0, 3, 1, 2) * peak_int_encoding.permute(0, 3, 1, 2)
        hdr_skypano_recon = torch.where(sum_mask, sun_peak_map, hdr_skypano_recon)
        return (hdr_skypano_recon, ldr_skypano_recon, use_gt_peak)

    def build_peak_map(self, peak_vector):
        """
        Args:
            peak_vector : [B, 6]
                3 for peak dir, 3 for peak intensity

        Returns:
            peak encoding map : [B, H, W, 4]
                1 for peak dir using spherical gaussian lobe, 3 for peak intensity

            sum_mask :[B, H, W, 3]
        """
        dir_vector = peak_vector[..., :3]
        int_vector = peak_vector[..., 3:]
        dir_vector_expand = dir_vector.unsqueeze(1).unsqueeze(1).expand(-1, self.sky_H, self.sky_W, -1)
        peak_dir_cosine = torch.einsum('nhwc,nhwc->nhw', dir_vector_expand, self.pos_encoding.expand(dir_vector_expand.shape)).unsqueeze(-1)
        peak_dir_encoding = torch.exp(100 * (peak_dir_cosine - 1))
        sun_mask = torch.gt(peak_dir_encoding, self.sum_lobe_thres).expand(-1, -1, -1, 3)
        int_vector_expand = int_vector.unsqueeze(1).unsqueeze(1).expand(-1, self.sky_H, self.sky_W, -1)
        peak_int_encoding = torch.where(sun_mask, int_vector_expand, 0)
        return (peak_dir_encoding, peak_int_encoding, sun_mask)

    def on_train_epoch_start(self):
        print(f'Module fixed in training: {self.fix_modules}.')
        for module in self.fix_modules:
            for p in eval(f'self.{module}').parameters():
                p.requires_grad_(False)
            eval(f'self.{module}').eval()

    def training_step(self, batch, batch_idx):
        ldr_skypano, hdr_skypano_gt, peak_vector_gt = batch
        peak_vector_pred, latent_vector = self.encode_forward(ldr_skypano)
        hdr_skypano_pred, ldr_skypano_recon, _ = self.decode_forward(latent_vector, peak_vector_pred, peak_vector_gt)
        ldr_recon_loss = self.ldr_recon_loss(ldr_skypano_recon, ldr_skypano)
        hdr_recon_loss = self.hdr_recon_loss(hdr_skypano_pred, hdr_skypano_gt)
        peak_dir_loss = self.peak_dir_loss(peak_vector_pred[..., :3], peak_vector_gt[..., :3])
        peak_int_loss = self.peak_int_loss(peak_vector_pred[..., 3:], peak_vector_gt[..., 3:])
        loss = hdr_recon_loss + peak_dir_loss + peak_int_loss + ldr_recon_loss
        self.log('train_loss', loss)
        self.log('hdr_recon_loss', hdr_recon_loss)
        self.log('ldr_recon_loss', ldr_recon_loss)
        self.log('peak_dir_loss', peak_dir_loss)
        self.log('peak_int_loss', peak_int_loss)
        log_info = f'|| loss: {loss:.3f} || hdr_recon_loss: {hdr_recon_loss:.3f}  || ldr_recon_loss: {ldr_recon_loss:.3f} || peak_dir_loss: {peak_dir_loss:.3f} ' + f'|| peak_int_loss: {peak_int_loss:.3f}'
        print(log_info)
        return loss

    def validation_step(self, batch, batch_idx):
        ldr_skypano, hdr_skypano_gt, peak_vector_gt = batch
        peak_vector_pred, latent_vector = self.encode_forward(ldr_skypano)
        hdr_skypano_pred, ldr_skypano_recon, _ = self.decode_forward(latent_vector, peak_vector_pred, peak_vector_pred)
        ldr_recon_loss = self.ldr_recon_loss(ldr_skypano_recon, ldr_skypano)
        hdr_recon_loss = self.hdr_recon_loss(hdr_skypano_pred, hdr_skypano_gt)
        peak_dir_loss = self.peak_dir_loss(peak_vector_pred[..., :3], peak_vector_gt[..., :3])
        peak_int_loss = self.peak_int_loss(peak_vector_pred[..., 3:], peak_vector_gt[..., 3:])
        loss = hdr_recon_loss + peak_dir_loss + peak_int_loss + ldr_recon_loss
        self.log('val_loss', loss)
        return loss

    def test_step(self, batch, batch_idx):
        return self.validation_step(batch, batch_idx)

    def predict_step(self, batch, batch_idx):
        ldr_skypano, hdr_skypano_gt, peak_vector_gt = batch
        peak_vector_pred, latent_vector = self.encode_forward(ldr_skypano)
        hdr_skypano_pred, ldr_skypano_recon, _ = self.decode_forward(latent_vector, peak_vector_pred, peak_vector_pred)
        print(f'{batch_idx:0>3} \n                  HDRI Peak Intensity:\t\t {hdr_skypano_pred[0].flatten(1, 2).max(dim=-1)[0]} \n                  Peak Intensity Vector:\t {peak_vector_pred[0][3:]} \n                  Ground Truth Peak Intensity:\t {peak_vector_gt[0][3:]}')
        return_dict = {'ldr_skypano_input': ldr_skypano.permute(0, 2, 3, 1), 'ldr_skypano_pred': ldr_skypano_recon.permute(0, 2, 3, 1), 'hdr_skypano_gt': hdr_skypano_gt.permute(0, 2, 3, 1), 'hdr_skypano_pred': hdr_skypano_pred.permute(0, 2, 3, 1), 'batch_idx': batch_idx}
        return return_dict

    def configure_optimizers(self):
        optimizer = torch.optim.Adam(self.parameters(), lr=self.hypes['lr_schedule']['init_lr'])
        lr_scheduler = StepLR(optimizer=optimizer, step_size=self.hypes['lr_schedule']['decay_per_epoch'], gamma=self.hypes['lr_schedule']['decay_rate'])
        return ([optimizer], [lr_scheduler])

def configure_optimizers(self):
    optimizer = torch.optim.Adam(self.parameters(), lr=self.hypes['lr_schedule']['init_lr'])
    lr_scheduler = StepLR(optimizer=optimizer, step_size=self.hypes['lr_schedule']['decay_per_epoch'], gamma=self.hypes['lr_schedule']['decay_rate'])
    return ([optimizer], [lr_scheduler])

class SkyPred(pl.LightningModule):

    def __init__(self, hypes):
        super().__init__()
        self.hypes = hypes
        self.save_hyperparameters()
        self.latent_predictor = build_latent_predictor(hypes['model']['latent_predictor'])
        sky_model_core_method = hypes['model']['sky_model']['core_method']
        sky_model_core_method_ckpt_path = hypes['model']['sky_model']['ckpt_path']
        if sky_model_core_method == 'sky_model_enhanced':
            self.sky_model = SkyModelEnhanced.load_from_checkpoint(sky_model_core_method_ckpt_path)
        elif sky_model_core_method == 'sky_model':
            self.sky_model = SkyModel.load_from_checkpoint(sky_model_core_method_ckpt_path)
        self.ldr_recon_loss = build_loss(hypes['loss']['ldr_recon_loss'])
        self.hdr_recon_loss = build_loss(hypes['loss']['hdr_recon_loss'])
        self.peak_int_loss = build_loss(hypes['loss']['peak_int_loss'])
        self.peak_dir_loss = build_loss(hypes['loss']['peak_dir_loss'])
        self.latent_loss = build_loss(hypes['loss']['latent_loss'])
        self.fix_modules = hypes['model'].get('fix_modules', [])
        self.on_train_epoch_start()

    def decode_forward(self, latent_vector, peak_vector):
        return self.sky_model.decode_forward(latent_vector, peak_vector, peak_vector)

    def on_train_epoch_start(self):
        print(f'Module fixed in training: {self.fix_modules}.')
        for module in self.fix_modules:
            for p in eval(f'self.{module}').parameters():
                p.requires_grad_(False)
            eval(f'self.{module}').eval()

    def training_step(self, batch, batch_idx):
        img_crops_tensor, peak_vector_gt, latent_vector_gt, mask_envmap_tensor, hdr_envmap_tensor, ldr_envmap_tensor = batch
        peak_vector_pred, latent_vector_pred = self.latent_predictor(img_crops_tensor)
        hdr_skypano_pred, ldr_skypano_pred, _ = self.decode_forward(latent_vector_pred, peak_vector_pred)
        hdr_recon_loss = self.hdr_recon_loss(hdr_skypano_pred, hdr_envmap_tensor, mask_envmap_tensor)
        ldr_recon_loss = self.ldr_recon_loss(srgb_gamma_correction_torch(hdr_skypano_pred), ldr_envmap_tensor, mask_envmap_tensor)
        latent_loss = self.latent_loss(latent_vector_pred, latent_vector_gt)
        peak_dir_loss = self.peak_dir_loss(peak_vector_pred[..., :3], peak_vector_gt[..., :3])
        peak_int_loss = self.peak_int_loss(peak_vector_pred[..., 3:], peak_vector_gt[..., 3:])
        loss = hdr_recon_loss + ldr_recon_loss + latent_loss + peak_dir_loss + peak_int_loss
        self.log('train_loss', loss)
        self.log('hdr_recon_loss', hdr_recon_loss)
        self.log('ldr_recon_loss', ldr_recon_loss)
        self.log('latent_loss', latent_loss)
        self.log('peak_dir_loss', peak_dir_loss)
        self.log('peak_int_loss', peak_int_loss)
        print(f'|| loss: {loss:.3f} || hdr_recon_loss: {hdr_recon_loss:.3f} || ldr_recon_loss: {ldr_recon_loss:.3f} ' + f'|| latent_loss: {latent_loss:.3f} || peak_dir_loss: {peak_dir_loss:.3f} || peak_int_loss: {peak_int_loss:.3f}')
        return loss

    def validation_step(self, batch, batch_idx):
        img_crops_tensor, peak_vector_gt, latent_vector_gt, mask_envmap_tensor, hdr_envmap_tensor, ldr_envmap_tensor = batch
        mask_envmap_tensor = torch.gt(mask_envmap_tensor, 0.8)
        peak_vector_pred, latent_vector_pred = self.latent_predictor(img_crops_tensor)
        hdr_skypano_pred, ldr_skypano_pred, _ = self.decode_forward(latent_vector_pred, peak_vector_pred)
        hdr_recon_loss = self.hdr_recon_loss(hdr_skypano_pred, hdr_envmap_tensor, mask_envmap_tensor)
        ldr_recon_loss = self.ldr_recon_loss(srgb_gamma_correction_torch(hdr_skypano_pred), ldr_envmap_tensor, mask_envmap_tensor)
        latent_loss = self.latent_loss(latent_vector_pred, latent_vector_gt)
        peak_dir_loss = self.peak_dir_loss(peak_vector_pred[..., :3], peak_vector_gt[..., :3])
        peak_int_loss = self.peak_int_loss(peak_vector_pred[..., 3:], peak_vector_gt[..., 3:])
        loss = hdr_recon_loss + ldr_recon_loss
        self.log('val_loss', loss)
        return loss

    def test_step(self, batch, batch_idx):
        return self.validation_step(batch, batch_idx)

    def predict_step(self, batch, batch_idx):
        img_crops_tensor, peak_vector_gt, latent_vector_gt, mask_envmap_tensor, hdr_envmap_tensor, ldr_envmap_tensor = batch
        mask_envmap_tensor = torch.gt(mask_envmap_tensor, 0.8)
        peak_vector_pred, latent_vector_pred = self.latent_predictor(img_crops_tensor)
        hdr_skypano_pred, ldr_skypano_pred, _ = self.decode_forward(latent_vector_pred, peak_vector_pred)
        return_dict = {'hdr_skypano_pred': hdr_skypano_pred.permute(0, 2, 3, 1), 'ldr_skypano_pred': srgb_gamma_correction_torch(hdr_skypano_pred).permute(0, 2, 3, 1), 'hdr_skypano_gt': hdr_envmap_tensor.permute(0, 2, 3, 1), 'ldr_skypano_input': ldr_envmap_tensor.permute(0, 2, 3, 1), 'mask_env': mask_envmap_tensor.permute(0, 2, 3, 1), 'image_crops': img_crops_tensor.permute(0, 1, 3, 4, 2), 'batch_idx': batch_idx}
        return return_dict

    def configure_optimizers(self):
        optimizer = torch.optim.Adam(self.parameters(), lr=self.hypes['lr_schedule']['init_lr'])
        lr_scheduler = StepLR(optimizer=optimizer, step_size=self.hypes['lr_schedule']['decay_per_epoch'], gamma=self.hypes['lr_schedule']['decay_rate'])
        return ([optimizer], [lr_scheduler])

def configure_optimizers(self):
    optimizer = torch.optim.Adam(self.parameters(), lr=self.hypes['lr_schedule']['init_lr'])
    lr_scheduler = StepLR(optimizer=optimizer, step_size=self.hypes['lr_schedule']['decay_per_epoch'], gamma=self.hypes['lr_schedule']['decay_rate'])
    return ([optimizer], [lr_scheduler])

