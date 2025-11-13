# Cluster 4

class ChatSim:

    def __init__(self, config):
        self.config = config
        self.scene = Scene(config['scene'])
        agents_config = config['agents']
        self.project_manager = ProjectManager(agents_config['project_manager'])
        self.asset_select_agent = AssetSelectAgent(agents_config['asset_select_agent'])
        self.deletion_agent = DeletionAgent(agents_config['deletion_agent'])
        self.foreground_rendering_agent = ForegroundRenderingAgent(agents_config['foreground_rendering_agent'])
        self.motion_agent = MotionAgent(agents_config['motion_agent'])
        self.view_adjust_agent = ViewAdjustAgent(agents_config['view_adjust_agent'])
        if agents_config['background_rendering_agent'].get('scene_representation', 'nerf') == 'nerf':
            self.background_rendering_agent = BackgroundRenderingAgent(agents_config['background_rendering_agent'])
        else:
            self.background_rendering_agent = BackgroundRendering3DGSAgent(agents_config['background_rendering_agent'])
        self.tech_agents = {'asset_select_agent': self.asset_select_agent, 'background_rendering_agent': self.background_rendering_agent, 'deletion_agent': self.deletion_agent, 'foreground_rendering_agent': self.foreground_rendering_agent, 'motion_agent': self.motion_agent, 'view_adjust_agent': self.view_adjust_agent}
        self.current_prompt = 'An empty prompt'

    def setup_init_frame(self):
        """Setup initial frame for ChatSim's reasoning and rendering.
        """
        if not os.path.exists(self.scene.init_img_path):
            print(f'{colored('[Note]', color='red', attrs=['bold'])} ', f'{colored('can not find init image, rendering it for the first time')}\n')
            self.background_rendering_agent.func_render_background(self.scene)
            imageio.imwrite(self.scene.init_img_path, self.scene.current_images[0])
        else:
            self.scene.current_images = [imageio.imread(self.scene.init_img_path)] * self.scene.frames

    def execute_llms(self, prompt):
        """Entry of ChatSim's reasoning.
        We perform multi-LLM reasoning for the user's prompt

        Input:
            prompt : str
                language prompt to ChatSim.
        """
        self.scene.setup_cars()
        self.current_prompt = prompt
        tasks = self.project_manager.decompose_prompt(self.scene, prompt)
        for task in tasks.values():
            print(f'{colored('[Performing Single Prompt]', on_color='on_blue', attrs=['bold'])} {colored(task, attrs=['bold'])}\n')
            self.project_manager.dispatch_task(self.scene, task, self.tech_agents)
        print(colored('scene.added_cars_dict', color='red', attrs=['bold']), end=' ')
        pprint.pprint(self.scene.added_cars_dict.keys())
        print(colored('scene.removed_cars', color='red', attrs=['bold']), end=' ')
        pprint.pprint(self.scene.removed_cars)

    def execute_funcs(self):
        """Entry of ChatSim's rendering functions
        We perform agent's functions following the self.scene's configuration.
        self.scene's configuration are updated in self.execute_llms()
        """
        self.background_rendering_agent.func_render_background(self.scene)
        self.deletion_agent.func_inpaint_scene(self.scene)
        self.asset_select_agent.func_retrieve_blender_file(self.scene)
        self.foreground_rendering_agent.func_blender_add_cars(self.scene)
        generate_video(self.scene, self.current_prompt)

def execute_llms(self, prompt):
    """Entry of ChatSim's reasoning.
        We perform multi-LLM reasoning for the user's prompt

        Input:
            prompt : str
                language prompt to ChatSim.
        """
    self.scene.setup_cars()
    self.current_prompt = prompt
    tasks = self.project_manager.decompose_prompt(self.scene, prompt)
    for task in tasks.values():
        print(f'{colored('[Performing Single Prompt]', on_color='on_blue', attrs=['bold'])} {colored(task, attrs=['bold'])}\n')
        self.project_manager.dispatch_task(self.scene, task, self.tech_agents)
    print(colored('scene.added_cars_dict', color='red', attrs=['bold']), end=' ')
    pprint.pprint(self.scene.added_cars_dict.keys())
    print(colored('scene.removed_cars', color='red', attrs=['bold']), end=' ')
    pprint.pprint(self.scene.removed_cars)

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

def build_sam_vit_t(checkpoint=None):
    prompt_embed_dim = 256
    image_size = 1024
    vit_patch_size = 16
    image_embedding_size = image_size // vit_patch_size
    mobile_sam = Sam(image_encoder=TinyViT(img_size=1024, in_chans=3, num_classes=1000, embed_dims=[64, 128, 160, 320], depths=[2, 2, 6, 2], num_heads=[2, 4, 5, 10], window_sizes=[7, 7, 14, 7], mlp_ratio=4.0, drop_rate=0.0, drop_path_rate=0.0, use_checkpoint=False, mbconv_expand_ratio=4.0, local_conv_size=3, layer_lr_decay=0.8), prompt_encoder=PromptEncoder(embed_dim=prompt_embed_dim, image_embedding_size=(image_embedding_size, image_embedding_size), input_image_size=(image_size, image_size), mask_in_chans=16), mask_decoder=MaskDecoder(num_multimask_outputs=3, transformer=TwoWayTransformer(depth=2, embedding_dim=prompt_embed_dim, mlp_dim=2048, num_heads=8), transformer_dim=prompt_embed_dim, iou_head_depth=3, iou_head_hidden_dim=256), pixel_mean=[123.675, 116.28, 103.53], pixel_std=[58.395, 57.12, 57.375])
    mobile_sam.eval()
    if checkpoint is not None:
        with open(checkpoint, 'rb') as f:
            state_dict = torch.load(f)
        mobile_sam.load_state_dict(state_dict)
    return mobile_sam

def _build_sam(encoder_embed_dim, encoder_depth, encoder_num_heads, encoder_global_attn_indexes, checkpoint=None):
    prompt_embed_dim = 256
    image_size = 1024
    vit_patch_size = 16
    image_embedding_size = image_size // vit_patch_size
    sam = Sam(image_encoder=ImageEncoderViT(depth=encoder_depth, embed_dim=encoder_embed_dim, img_size=image_size, mlp_ratio=4, norm_layer=partial(torch.nn.LayerNorm, eps=1e-06), num_heads=encoder_num_heads, patch_size=vit_patch_size, qkv_bias=True, use_rel_pos=True, global_attn_indexes=encoder_global_attn_indexes, window_size=14, out_chans=prompt_embed_dim), prompt_encoder=PromptEncoder(embed_dim=prompt_embed_dim, image_embedding_size=(image_embedding_size, image_embedding_size), input_image_size=(image_size, image_size), mask_in_chans=16), mask_decoder=MaskDecoder(num_multimask_outputs=3, transformer=TwoWayTransformer(depth=2, embedding_dim=prompt_embed_dim, mlp_dim=2048, num_heads=8), transformer_dim=prompt_embed_dim, iou_head_depth=3, iou_head_hidden_dim=256), pixel_mean=[123.675, 116.28, 103.53], pixel_std=[58.395, 57.12, 57.375])
    sam.eval()
    if checkpoint is not None:
        with open(checkpoint, 'rb') as f:
            state_dict = torch.load(f)
        sam.load_state_dict(state_dict)
    return sam

class Attention(nn.Module):
    """
    An attention layer that allows for downscaling the size of the embedding
    after projection to queries, keys, and values.
    """

    def __init__(self, embedding_dim: int, num_heads: int, downsample_rate: int=1) -> None:
        super().__init__()
        self.embedding_dim = embedding_dim
        self.internal_dim = embedding_dim // downsample_rate
        self.num_heads = num_heads
        assert self.internal_dim % num_heads == 0, 'num_heads must divide embedding_dim.'
        self.q_proj = nn.Linear(embedding_dim, self.internal_dim)
        self.k_proj = nn.Linear(embedding_dim, self.internal_dim)
        self.v_proj = nn.Linear(embedding_dim, self.internal_dim)
        self.out_proj = nn.Linear(self.internal_dim, embedding_dim)

    def _separate_heads(self, x: Tensor, num_heads: int) -> Tensor:
        b, n, c = x.shape
        x = x.reshape(b, n, num_heads, c // num_heads)
        return x.transpose(1, 2)

    def _recombine_heads(self, x: Tensor) -> Tensor:
        b, n_heads, n_tokens, c_per_head = x.shape
        x = x.transpose(1, 2)
        return x.reshape(b, n_tokens, n_heads * c_per_head)

    def forward(self, q: Tensor, k: Tensor, v: Tensor) -> Tensor:
        q = self.q_proj(q)
        k = self.k_proj(k)
        v = self.v_proj(v)
        q = self._separate_heads(q, self.num_heads)
        k = self._separate_heads(k, self.num_heads)
        v = self._separate_heads(v, self.num_heads)
        _, _, _, c_per_head = q.shape
        attn = q @ k.permute(0, 1, 3, 2)
        attn = attn / math.sqrt(c_per_head)
        attn = torch.softmax(attn, dim=-1)
        out = attn @ v
        out = self._recombine_heads(out)
        out = self.out_proj(out)
        return out

def forward(self, q: Tensor, k: Tensor, v: Tensor) -> Tensor:
    q = self.q_proj(q)
    k = self.k_proj(k)
    v = self.v_proj(v)
    q = self._separate_heads(q, self.num_heads)
    k = self._separate_heads(k, self.num_heads)
    v = self._separate_heads(v, self.num_heads)
    _, _, _, c_per_head = q.shape
    attn = q @ k.permute(0, 1, 3, 2)
    attn = attn / math.sqrt(c_per_head)
    attn = torch.softmax(attn, dim=-1)
    out = attn @ v
    out = self._recombine_heads(out)
    out = self.out_proj(out)
    return out

@register_tiny_vit_model
def tiny_vit_5m_224(pretrained=False, num_classes=1000, drop_path_rate=0.0):
    return TinyViT(num_classes=num_classes, embed_dims=[64, 128, 160, 320], depths=[2, 2, 6, 2], num_heads=[2, 4, 5, 10], window_sizes=[7, 7, 14, 7], drop_path_rate=drop_path_rate)

@register_tiny_vit_model
def tiny_vit_11m_224(pretrained=False, num_classes=1000, drop_path_rate=0.1):
    return TinyViT(num_classes=num_classes, embed_dims=[64, 128, 256, 448], depths=[2, 2, 6, 2], num_heads=[2, 4, 8, 14], window_sizes=[7, 7, 14, 7], drop_path_rate=drop_path_rate)

@register_tiny_vit_model
def tiny_vit_21m_224(pretrained=False, num_classes=1000, drop_path_rate=0.2):
    return TinyViT(num_classes=num_classes, embed_dims=[96, 192, 384, 576], depths=[2, 2, 6, 2], num_heads=[3, 6, 12, 18], window_sizes=[7, 7, 14, 7], drop_path_rate=drop_path_rate)

@register_tiny_vit_model
def tiny_vit_21m_384(pretrained=False, num_classes=1000, drop_path_rate=0.1):
    return TinyViT(img_size=384, num_classes=num_classes, embed_dims=[96, 192, 384, 576], depths=[2, 2, 6, 2], num_heads=[3, 6, 12, 18], window_sizes=[12, 12, 24, 12], drop_path_rate=drop_path_rate)

@register_tiny_vit_model
def tiny_vit_21m_512(pretrained=False, num_classes=1000, drop_path_rate=0.1):
    return TinyViT(img_size=512, num_classes=num_classes, embed_dims=[96, 192, 384, 576], depths=[2, 2, 6, 2], num_heads=[3, 6, 12, 18], window_sizes=[16, 16, 32, 16], drop_path_rate=drop_path_rate)

class JITWrapper(nn.Module):

    def __init__(self, model):
        super().__init__()
        self.model = model

    def forward(self, image, mask):
        batch = {'image': image, 'mask': mask}
        out = self.model(batch)
        return out['inpainted']

def forward(self, image, mask):
    batch = {'image': image, 'mask': mask}
    out = self.model(batch)
    return out['inpainted']

class ResNetHead(nn.Module):

    def __init__(self, input_nc, ngf=64, n_downsampling=3, n_blocks=9, norm_layer=nn.BatchNorm2d, padding_type='reflect', conv_kind='default', activation=nn.ReLU(True)):
        assert n_blocks >= 0
        super(ResNetHead, self).__init__()
        conv_layer = get_conv_block_ctor(conv_kind)
        model = [nn.ReflectionPad2d(3), conv_layer(input_nc, ngf, kernel_size=7, padding=0), norm_layer(ngf), activation]
        for i in range(n_downsampling):
            mult = 2 ** i
            model += [conv_layer(ngf * mult, ngf * mult * 2, kernel_size=3, stride=2, padding=1), norm_layer(ngf * mult * 2), activation]
        mult = 2 ** n_downsampling
        for i in range(n_blocks):
            model += [ResnetBlock(ngf * mult, padding_type=padding_type, activation=activation, norm_layer=norm_layer, conv_kind=conv_kind)]
        self.model = nn.Sequential(*model)

    def forward(self, input):
        return self.model(input)

def forward(self, input):
    return self.model(input)

class ResNetTail(nn.Module):

    def __init__(self, output_nc, ngf=64, n_downsampling=3, n_blocks=9, norm_layer=nn.BatchNorm2d, padding_type='reflect', conv_kind='default', activation=nn.ReLU(True), up_norm_layer=nn.BatchNorm2d, up_activation=nn.ReLU(True), add_out_act=False, out_extra_layers_n=0, add_in_proj=None):
        assert n_blocks >= 0
        super(ResNetTail, self).__init__()
        mult = 2 ** n_downsampling
        model = []
        if add_in_proj is not None:
            model.append(nn.Conv2d(add_in_proj, ngf * mult, kernel_size=1))
        for i in range(n_blocks):
            model += [ResnetBlock(ngf * mult, padding_type=padding_type, activation=activation, norm_layer=norm_layer, conv_kind=conv_kind)]
        for i in range(n_downsampling):
            mult = 2 ** (n_downsampling - i)
            model += [nn.ConvTranspose2d(ngf * mult, int(ngf * mult / 2), kernel_size=3, stride=2, padding=1, output_padding=1), up_norm_layer(int(ngf * mult / 2)), up_activation]
        self.model = nn.Sequential(*model)
        out_layers = []
        for _ in range(out_extra_layers_n):
            out_layers += [nn.Conv2d(ngf, ngf, kernel_size=1, padding=0), up_norm_layer(ngf), up_activation]
        out_layers += [nn.ReflectionPad2d(3), nn.Conv2d(ngf, output_nc, kernel_size=7, padding=0)]
        if add_out_act:
            out_layers.append(get_activation('tanh' if add_out_act is True else add_out_act))
        self.out_proj = nn.Sequential(*out_layers)

    def forward(self, input, return_last_act=False):
        features = self.model(input)
        out = self.out_proj(features)
        if return_last_act:
            return (out, features)
        else:
            return out

def forward(self, input, return_last_act=False):
    features = self.model(input)
    out = self.out_proj(features)
    if return_last_act:
        return (out, features)
    else:
        return out

class FFCResNetGenerator(nn.Module):

    def __init__(self, input_nc, output_nc, ngf=64, n_downsampling=3, n_blocks=9, norm_layer=nn.BatchNorm2d, padding_type='reflect', activation_layer=nn.ReLU, up_norm_layer=nn.BatchNorm2d, up_activation=nn.ReLU(True), init_conv_kwargs={}, downsample_conv_kwargs={}, resnet_conv_kwargs={}, spatial_transform_layers=None, spatial_transform_kwargs={}, add_out_act=True, max_features=1024, out_ffc=False, out_ffc_kwargs={}):
        assert n_blocks >= 0
        super().__init__()
        model = [nn.ReflectionPad2d(3), FFC_BN_ACT(input_nc, ngf, kernel_size=7, padding=0, norm_layer=norm_layer, activation_layer=activation_layer, **init_conv_kwargs)]
        for i in range(n_downsampling):
            mult = 2 ** i
            if i == n_downsampling - 1:
                cur_conv_kwargs = dict(downsample_conv_kwargs)
                cur_conv_kwargs['ratio_gout'] = resnet_conv_kwargs.get('ratio_gin', 0)
            else:
                cur_conv_kwargs = downsample_conv_kwargs
            model += [FFC_BN_ACT(min(max_features, ngf * mult), min(max_features, ngf * mult * 2), kernel_size=3, stride=2, padding=1, norm_layer=norm_layer, activation_layer=activation_layer, **cur_conv_kwargs)]
        mult = 2 ** n_downsampling
        feats_num_bottleneck = min(max_features, ngf * mult)
        for i in range(n_blocks):
            cur_resblock = FFCResnetBlock(feats_num_bottleneck, padding_type=padding_type, activation_layer=activation_layer, norm_layer=norm_layer, **resnet_conv_kwargs)
            if spatial_transform_layers is not None and i in spatial_transform_layers:
                cur_resblock = LearnableSpatialTransformWrapper(cur_resblock, **spatial_transform_kwargs)
            model += [cur_resblock]
        model += [ConcatTupleLayer()]
        for i in range(n_downsampling):
            mult = 2 ** (n_downsampling - i)
            model += [nn.ConvTranspose2d(min(max_features, ngf * mult), min(max_features, int(ngf * mult / 2)), kernel_size=3, stride=2, padding=1, output_padding=1), up_norm_layer(min(max_features, int(ngf * mult / 2))), up_activation]
        if out_ffc:
            model += [FFCResnetBlock(ngf, padding_type=padding_type, activation_layer=activation_layer, norm_layer=norm_layer, inline=True, **out_ffc_kwargs)]
        model += [nn.ReflectionPad2d(3), nn.Conv2d(ngf, output_nc, kernel_size=7, padding=0)]
        if add_out_act:
            model.append(get_activation('tanh' if add_out_act is True else add_out_act))
        self.model = nn.Sequential(*model)

    def forward(self, input):
        return self.model(input)

def forward(self, input):
    return self.model(input)

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

def get_all_activations(self, x):
    res = [x]
    for n in range(self.n_layers + 2):
        model = getattr(self, 'model' + str(n))
        res.append(model(res[-1]))
    return res[1:]

class MultiDilatedGlobalGenerator(nn.Module):

    def __init__(self, input_nc, output_nc, ngf=64, n_downsampling=3, n_blocks=3, norm_layer=nn.BatchNorm2d, padding_type='reflect', conv_kind='default', deconv_kind='convtranspose', activation=nn.ReLU(True), up_norm_layer=nn.BatchNorm2d, affine=None, up_activation=nn.ReLU(True), add_out_act=True, max_features=1024, multidilation_kwargs={}, ffc_positions=None, ffc_kwargs={}):
        assert n_blocks >= 0
        super().__init__()
        conv_layer = get_conv_block_ctor(conv_kind)
        resnet_conv_layer = functools.partial(get_conv_block_ctor('multidilated'), **multidilation_kwargs)
        norm_layer = get_norm_layer(norm_layer)
        if affine is not None:
            norm_layer = partial(norm_layer, affine=affine)
        up_norm_layer = get_norm_layer(up_norm_layer)
        if affine is not None:
            up_norm_layer = partial(up_norm_layer, affine=affine)
        model = [nn.ReflectionPad2d(3), conv_layer(input_nc, ngf, kernel_size=7, padding=0), norm_layer(ngf), activation]
        identity = Identity()
        for i in range(n_downsampling):
            mult = 2 ** i
            model += [conv_layer(min(max_features, ngf * mult), min(max_features, ngf * mult * 2), kernel_size=3, stride=2, padding=1), norm_layer(min(max_features, ngf * mult * 2)), activation]
        mult = 2 ** n_downsampling
        feats_num_bottleneck = min(max_features, ngf * mult)
        for i in range(n_blocks):
            if ffc_positions is not None and i in ffc_positions:
                model += [FFCResnetBlock(feats_num_bottleneck, padding_type, norm_layer, activation_layer=nn.ReLU, inline=True, **ffc_kwargs)]
            model += [MultidilatedResnetBlock(feats_num_bottleneck, padding_type=padding_type, conv_layer=resnet_conv_layer, activation=activation, norm_layer=norm_layer)]
        for i in range(n_downsampling):
            mult = 2 ** (n_downsampling - i)
            model += deconv_factory(deconv_kind, ngf, mult, up_norm_layer, up_activation, max_features)
        model += [nn.ReflectionPad2d(3), nn.Conv2d(ngf, output_nc, kernel_size=7, padding=0)]
        if add_out_act:
            model.append(get_activation('tanh' if add_out_act is True else add_out_act))
        self.model = nn.Sequential(*model)

    def forward(self, input):
        return self.model(input)

def forward(self, input):
    return self.model(input)

class ConfigGlobalGenerator(nn.Module):

    def __init__(self, input_nc, output_nc, ngf=64, n_downsampling=3, n_blocks=3, norm_layer=nn.BatchNorm2d, padding_type='reflect', conv_kind='default', deconv_kind='convtranspose', activation=nn.ReLU(True), up_norm_layer=nn.BatchNorm2d, affine=None, up_activation=nn.ReLU(True), add_out_act=True, max_features=1024, manual_block_spec=[], resnet_block_kind='multidilatedresnetblock', resnet_conv_kind='multidilated', resnet_dilation=1, multidilation_kwargs={}):
        assert n_blocks >= 0
        super().__init__()
        conv_layer = get_conv_block_ctor(conv_kind)
        resnet_conv_layer = functools.partial(get_conv_block_ctor(resnet_conv_kind), **multidilation_kwargs)
        norm_layer = get_norm_layer(norm_layer)
        if affine is not None:
            norm_layer = partial(norm_layer, affine=affine)
        up_norm_layer = get_norm_layer(up_norm_layer)
        if affine is not None:
            up_norm_layer = partial(up_norm_layer, affine=affine)
        model = [nn.ReflectionPad2d(3), conv_layer(input_nc, ngf, kernel_size=7, padding=0), norm_layer(ngf), activation]
        identity = Identity()
        for i in range(n_downsampling):
            mult = 2 ** i
            model += [conv_layer(min(max_features, ngf * mult), min(max_features, ngf * mult * 2), kernel_size=3, stride=2, padding=1), norm_layer(min(max_features, ngf * mult * 2)), activation]
        mult = 2 ** n_downsampling
        feats_num_bottleneck = min(max_features, ngf * mult)
        if len(manual_block_spec) == 0:
            manual_block_spec = [DotDict(lambda: None, {'n_blocks': n_blocks, 'use_default': True})]
        for block_spec in manual_block_spec:

            def make_and_add_blocks(model, block_spec):
                block_spec = DotDict(lambda: None, block_spec)
                if not block_spec.use_default:
                    resnet_conv_layer = functools.partial(get_conv_block_ctor(block_spec.resnet_conv_kind), **block_spec.multidilation_kwargs)
                    resnet_conv_kind = block_spec.resnet_conv_kind
                    resnet_block_kind = block_spec.resnet_block_kind
                    if block_spec.resnet_dilation is not None:
                        resnet_dilation = block_spec.resnet_dilation
                for i in range(block_spec.n_blocks):
                    if resnet_block_kind == 'multidilatedresnetblock':
                        model += [MultidilatedResnetBlock(feats_num_bottleneck, padding_type=padding_type, conv_layer=resnet_conv_layer, activation=activation, norm_layer=norm_layer)]
                    if resnet_block_kind == 'resnetblock':
                        model += [ResnetBlock(ngf * mult, padding_type=padding_type, activation=activation, norm_layer=norm_layer, conv_kind=resnet_conv_kind)]
                    if resnet_block_kind == 'resnetblock5x5':
                        model += [ResnetBlock5x5(ngf * mult, padding_type=padding_type, activation=activation, norm_layer=norm_layer, conv_kind=resnet_conv_kind)]
                    if resnet_block_kind == 'resnetblockdwdil':
                        model += [ResnetBlock(ngf * mult, padding_type=padding_type, activation=activation, norm_layer=norm_layer, conv_kind=resnet_conv_kind, dilation=resnet_dilation, second_dilation=resnet_dilation)]
            make_and_add_blocks(model, block_spec)
        for i in range(n_downsampling):
            mult = 2 ** (n_downsampling - i)
            model += deconv_factory(deconv_kind, ngf, mult, up_norm_layer, up_activation, max_features)
        model += [nn.ReflectionPad2d(3), nn.Conv2d(ngf, output_nc, kernel_size=7, padding=0)]
        if add_out_act:
            model.append(get_activation('tanh' if add_out_act is True else add_out_act))
        self.model = nn.Sequential(*model)

    def forward(self, input):
        return self.model(input)

def forward(self, input):
    return self.model(input)

class GlobalGenerator(nn.Module):

    def __init__(self, input_nc, output_nc, ngf=64, n_downsampling=3, n_blocks=9, norm_layer=nn.BatchNorm2d, padding_type='reflect', conv_kind='default', activation=nn.ReLU(True), up_norm_layer=nn.BatchNorm2d, affine=None, up_activation=nn.ReLU(True), dilated_blocks_n=0, dilated_blocks_n_start=0, dilated_blocks_n_middle=0, add_out_act=True, max_features=1024, is_resblock_depthwise=False, ffc_positions=None, ffc_kwargs={}, dilation=1, second_dilation=None, dilation_block_kind='simple', multidilation_kwargs={}):
        assert n_blocks >= 0
        super().__init__()
        conv_layer = get_conv_block_ctor(conv_kind)
        norm_layer = get_norm_layer(norm_layer)
        if affine is not None:
            norm_layer = partial(norm_layer, affine=affine)
        up_norm_layer = get_norm_layer(up_norm_layer)
        if affine is not None:
            up_norm_layer = partial(up_norm_layer, affine=affine)
        if ffc_positions is not None:
            ffc_positions = collections.Counter(ffc_positions)
        model = [nn.ReflectionPad2d(3), conv_layer(input_nc, ngf, kernel_size=7, padding=0), norm_layer(ngf), activation]
        identity = Identity()
        for i in range(n_downsampling):
            mult = 2 ** i
            model += [conv_layer(min(max_features, ngf * mult), min(max_features, ngf * mult * 2), kernel_size=3, stride=2, padding=1), norm_layer(min(max_features, ngf * mult * 2)), activation]
        mult = 2 ** n_downsampling
        feats_num_bottleneck = min(max_features, ngf * mult)
        dilated_block_kwargs = dict(dim=feats_num_bottleneck, padding_type=padding_type, activation=activation, norm_layer=norm_layer)
        if dilation_block_kind == 'simple':
            dilated_block_kwargs['conv_kind'] = conv_kind
        elif dilation_block_kind == 'multi':
            dilated_block_kwargs['conv_layer'] = functools.partial(get_conv_block_ctor('multidilated'), **multidilation_kwargs)
        if dilated_blocks_n_start is not None and dilated_blocks_n_start > 0:
            model += make_dil_blocks(dilated_blocks_n_start, dilation_block_kind, dilated_block_kwargs)
        for i in range(n_blocks):
            if i == n_blocks // 2 and dilated_blocks_n_middle is not None and (dilated_blocks_n_middle > 0):
                model += make_dil_blocks(dilated_blocks_n_middle, dilation_block_kind, dilated_block_kwargs)
            if ffc_positions is not None and i in ffc_positions:
                for _ in range(ffc_positions[i]):
                    model += [FFCResnetBlock(feats_num_bottleneck, padding_type, norm_layer, activation_layer=nn.ReLU, inline=True, **ffc_kwargs)]
            if is_resblock_depthwise:
                resblock_groups = feats_num_bottleneck
            else:
                resblock_groups = 1
            model += [ResnetBlock(feats_num_bottleneck, padding_type=padding_type, activation=activation, norm_layer=norm_layer, conv_kind=conv_kind, groups=resblock_groups, dilation=dilation, second_dilation=second_dilation)]
        if dilated_blocks_n is not None and dilated_blocks_n > 0:
            model += make_dil_blocks(dilated_blocks_n, dilation_block_kind, dilated_block_kwargs)
        for i in range(n_downsampling):
            mult = 2 ** (n_downsampling - i)
            model += [nn.ConvTranspose2d(min(max_features, ngf * mult), min(max_features, int(ngf * mult / 2)), kernel_size=3, stride=2, padding=1, output_padding=1), up_norm_layer(min(max_features, int(ngf * mult / 2))), up_activation]
        model += [nn.ReflectionPad2d(3), nn.Conv2d(ngf, output_nc, kernel_size=7, padding=0)]
        if add_out_act:
            model.append(get_activation('tanh' if add_out_act is True else add_out_act))
        self.model = nn.Sequential(*model)

    def forward(self, input):
        return self.model(input)

def forward(self, input):
    return self.model(input)

class GlobalGeneratorFromSuperChannels(nn.Module):

    def __init__(self, input_nc, output_nc, n_downsampling, n_blocks, super_channels, norm_layer='bn', padding_type='reflect', add_out_act=True):
        super().__init__()
        self.n_downsampling = n_downsampling
        norm_layer = get_norm_layer(norm_layer)
        if type(norm_layer) == functools.partial:
            use_bias = norm_layer.func == nn.InstanceNorm2d
        else:
            use_bias = norm_layer == nn.InstanceNorm2d
        channels = self.convert_super_channels(super_channels)
        self.channels = channels
        model = [nn.ReflectionPad2d(3), nn.Conv2d(input_nc, channels[0], kernel_size=7, padding=0, bias=use_bias), norm_layer(channels[0]), nn.ReLU(True)]
        for i in range(n_downsampling):
            mult = 2 ** i
            model += [nn.Conv2d(channels[0 + i], channels[1 + i], kernel_size=3, stride=2, padding=1, bias=use_bias), norm_layer(channels[1 + i]), nn.ReLU(True)]
        mult = 2 ** n_downsampling
        n_blocks1 = n_blocks // 3
        n_blocks2 = n_blocks1
        n_blocks3 = n_blocks - n_blocks1 - n_blocks2
        for i in range(n_blocks1):
            c = n_downsampling
            dim = channels[c]
            model += [ResnetBlock(dim, padding_type=padding_type, norm_layer=norm_layer)]
        for i in range(n_blocks2):
            c = n_downsampling + 1
            dim = channels[c]
            kwargs = {}
            if i == 0:
                kwargs = {'in_dim': channels[c - 1]}
            model += [ResnetBlock(dim, padding_type=padding_type, norm_layer=norm_layer, **kwargs)]
        for i in range(n_blocks3):
            c = n_downsampling + 2
            dim = channels[c]
            kwargs = {}
            if i == 0:
                kwargs = {'in_dim': channels[c - 1]}
            model += [ResnetBlock(dim, padding_type=padding_type, norm_layer=norm_layer, **kwargs)]
        for i in range(n_downsampling):
            mult = 2 ** (n_downsampling - i)
            model += [nn.ConvTranspose2d(channels[n_downsampling + 3 + i], channels[n_downsampling + 3 + i + 1], kernel_size=3, stride=2, padding=1, output_padding=1, bias=use_bias), norm_layer(channels[n_downsampling + 3 + i + 1]), nn.ReLU(True)]
        model += [nn.ReflectionPad2d(3)]
        model += [nn.Conv2d(channels[2 * n_downsampling + 3], output_nc, kernel_size=7, padding=0)]
        if add_out_act:
            model.append(get_activation('tanh' if add_out_act is True else add_out_act))
        self.model = nn.Sequential(*model)

    def convert_super_channels(self, super_channels):
        n_downsampling = self.n_downsampling
        result = []
        cnt = 0
        if n_downsampling == 2:
            N1 = 10
        elif n_downsampling == 3:
            N1 = 13
        else:
            raise NotImplementedError
        for i in range(0, N1):
            if i in [1, 4, 7, 10]:
                channel = super_channels[cnt] * 2 ** cnt
                config = {'channel': channel}
                result.append(channel)
                logging.info(f'Downsample channels {result[-1]}')
                cnt += 1
        for i in range(3):
            for counter, j in enumerate(range(N1 + i * 3, N1 + 3 + i * 3)):
                if len(super_channels) == 6:
                    channel = super_channels[3] * 4
                else:
                    channel = super_channels[i + 3] * 4
                config = {'channel': channel}
                if counter == 0:
                    result.append(channel)
                    logging.info(f'Bottleneck channels {result[-1]}')
        cnt = 2
        for i in range(N1 + 9, N1 + 21):
            if i in [22, 25, 28]:
                cnt -= 1
                if len(super_channels) == 6:
                    channel = super_channels[5 - cnt] * 2 ** cnt
                else:
                    channel = super_channels[7 - cnt] * 2 ** cnt
                result.append(int(channel))
                logging.info(f'Upsample channels {result[-1]}')
        return result

    def forward(self, input):
        return self.model(input)

def forward(self, input):
    return self.model(input)

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

def get_all_activations(self, x):
    res = [x]
    for n in range(self.n_layers + 2):
        model = getattr(self, 'model' + str(n))
        res.append(model(res[-1]))
    return res[1:]

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

def get_all_activations(self, x):
    res = [x]
    for n in range(self.n_layers + 2):
        model = getattr(self, 'model' + str(n))
        res.append(model(res[-1]))
    return res[1:]

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

def reset(self):
    super().reset()
    self.target_class_freq_by_image_total = []
    self.target_class_freq_by_image_mask = []
    self.pred_class_freq_by_image_mask = []

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

def reset(self):
    super().reset()
    self.individual_values = []

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

def __init__(self, *args, dims=2048, eps=1e-06, n_jobs=-1, **kwargs):
    super().__init__(*args, **kwargs)
    if getattr(FIDScore, '_MODEL', None) is None:
        block_idx = InceptionV3.BLOCK_INDEX_BY_DIM[dims]
        FIDScore._MODEL = InceptionV3([block_idx]).eval()
    self.model = FIDScore._MODEL
    self.eps = eps
    self.n_jobs = n_jobs

class PerceptualLoss(torch.nn.Module):

    def __init__(self, model='net-lin', net='alex', colorspace='rgb', model_path=None, spatial=False, use_gpu=True):
        super(PerceptualLoss, self).__init__()
        self.use_gpu = use_gpu
        self.spatial = spatial
        self.model = DistModel()
        self.model.initialize(model=model, net=net, use_gpu=use_gpu, colorspace=colorspace, model_path=model_path, spatial=self.spatial)

    def forward(self, pred, target, normalize=True):
        """
        Pred and target are Variables.
        If normalize is True, assumes the images are between [0,1] and then scales them between [-1,+1]
        If normalize is False, assumes the images are already between [-1,+1]
        Inputs pred and target are Nx3xHxW
        Output pytorch Variable N long
        """
        if normalize:
            target = 2 * target - 1
            pred = 2 * pred - 1
        return self.model(target, pred)

def forward(self, pred, target, normalize=True):
    """
        Pred and target are Variables.
        If normalize is True, assumes the images are between [0,1] and then scales them between [-1,+1]
        If normalize is False, assumes the images are already between [-1,+1]
        Inputs pred and target are Nx3xHxW
        Output pytorch Variable N long
        """
    if normalize:
        target = 2 * target - 1
        pred = 2 * pred - 1
    return self.model(target, pred)

class Dist2LogitLayer(nn.Module):
    """ takes 2 distances, puts through fc layers, spits out value between [0,1] (if use_sigmoid is True) """

    def __init__(self, chn_mid=32, use_sigmoid=True):
        super(Dist2LogitLayer, self).__init__()
        layers = [nn.Conv2d(5, chn_mid, 1, stride=1, padding=0, bias=True)]
        layers += [nn.LeakyReLU(0.2, True)]
        layers += [nn.Conv2d(chn_mid, chn_mid, 1, stride=1, padding=0, bias=True)]
        layers += [nn.LeakyReLU(0.2, True)]
        layers += [nn.Conv2d(chn_mid, 1, 1, stride=1, padding=0, bias=True)]
        if use_sigmoid:
            layers += [nn.Sigmoid()]
        self.model = nn.Sequential(*layers)

    def forward(self, d0, d1, eps=0.1):
        return self.model(torch.cat((d0, d1, d0 - d1, d0 / (d1 + eps), d1 / (d0 + eps)), dim=1))

def forward(self, d0, d1, eps=0.1):
    return self.model(torch.cat((d0, d1, d0 - d1, d0 / (d1 + eps), d1 / (d0 + eps)), dim=1))

def benchmark():

    def countless3d_generalized(img):
        return countless_generalized(img, (2, 8, 1))

    def countless3d_dynamic_generalized(img):
        return dynamic_countless_generalized(img, (8, 8, 1))
    methods = [countless3d_generalized]
    data = np.zeros(shape=(16 ** 2, 16 ** 2, 16 ** 2), dtype=np.uint8) + 1
    N = 5
    print('Algorithm\tMPx\tMB/sec\tSec\tN=%d' % N)
    for fn in methods:
        start = time.time()
        for _ in range(N):
            result = fn(data)
        end = time.time()
        total_time = end - start
        mpx = N * float(data.shape[0] * data.shape[1] * data.shape[2]) / total_time / 1024.0 / 1024.0
        mbytes = mpx * np.dtype(data.dtype).itemsize
        print('%s\t%.3f\t%.3f\t%.2f' % (fn.__name__, mpx, mbytes, total_time))

class ResNetHead(nn.Module):

    def __init__(self, input_nc, ngf=64, n_downsampling=3, n_blocks=9, norm_layer=nn.BatchNorm2d, padding_type='reflect', conv_kind='default', activation=nn.ReLU(True)):
        assert n_blocks >= 0
        super(ResNetHead, self).__init__()
        conv_layer = get_conv_block_ctor(conv_kind)
        model = [nn.ReflectionPad2d(3), conv_layer(input_nc, ngf, kernel_size=7, padding=0), norm_layer(ngf), activation]
        for i in range(n_downsampling):
            mult = 2 ** i
            model += [conv_layer(ngf * mult, ngf * mult * 2, kernel_size=3, stride=2, padding=1), norm_layer(ngf * mult * 2), activation]
        mult = 2 ** n_downsampling
        for i in range(n_blocks):
            model += [ResnetBlock(ngf * mult, padding_type=padding_type, activation=activation, norm_layer=norm_layer, conv_kind=conv_kind)]
        self.model = nn.Sequential(*model)

    def forward(self, input):
        return self.model(input)

def forward(self, input):
    return self.model(input)

class ResNetTail(nn.Module):

    def __init__(self, output_nc, ngf=64, n_downsampling=3, n_blocks=9, norm_layer=nn.BatchNorm2d, padding_type='reflect', conv_kind='default', activation=nn.ReLU(True), up_norm_layer=nn.BatchNorm2d, up_activation=nn.ReLU(True), add_out_act=False, out_extra_layers_n=0, add_in_proj=None):
        assert n_blocks >= 0
        super(ResNetTail, self).__init__()
        mult = 2 ** n_downsampling
        model = []
        if add_in_proj is not None:
            model.append(nn.Conv2d(add_in_proj, ngf * mult, kernel_size=1))
        for i in range(n_blocks):
            model += [ResnetBlock(ngf * mult, padding_type=padding_type, activation=activation, norm_layer=norm_layer, conv_kind=conv_kind)]
        for i in range(n_downsampling):
            mult = 2 ** (n_downsampling - i)
            model += [nn.ConvTranspose2d(ngf * mult, int(ngf * mult / 2), kernel_size=3, stride=2, padding=1, output_padding=1), up_norm_layer(int(ngf * mult / 2)), up_activation]
        self.model = nn.Sequential(*model)
        out_layers = []
        for _ in range(out_extra_layers_n):
            out_layers += [nn.Conv2d(ngf, ngf, kernel_size=1, padding=0), up_norm_layer(ngf), up_activation]
        out_layers += [nn.ReflectionPad2d(3), nn.Conv2d(ngf, output_nc, kernel_size=7, padding=0)]
        if add_out_act:
            out_layers.append(get_activation('tanh' if add_out_act is True else add_out_act))
        self.out_proj = nn.Sequential(*out_layers)

    def forward(self, input, return_last_act=False):
        features = self.model(input)
        out = self.out_proj(features)
        if return_last_act:
            return (out, features)
        else:
            return out

def forward(self, input, return_last_act=False):
    features = self.model(input)
    out = self.out_proj(features)
    if return_last_act:
        return (out, features)
    else:
        return out

class FFCResNetGenerator(nn.Module):

    def __init__(self, input_nc, output_nc, ngf=64, n_downsampling=3, n_blocks=9, norm_layer=nn.BatchNorm2d, padding_type='reflect', activation_layer=nn.ReLU, up_norm_layer=nn.BatchNorm2d, up_activation=nn.ReLU(True), init_conv_kwargs={}, downsample_conv_kwargs={}, resnet_conv_kwargs={}, spatial_transform_layers=None, spatial_transform_kwargs={}, add_out_act=True, max_features=1024, out_ffc=False, out_ffc_kwargs={}):
        assert n_blocks >= 0
        super().__init__()
        model = [nn.ReflectionPad2d(3), FFC_BN_ACT(input_nc, ngf, kernel_size=7, padding=0, norm_layer=norm_layer, activation_layer=activation_layer, **init_conv_kwargs)]
        for i in range(n_downsampling):
            mult = 2 ** i
            if i == n_downsampling - 1:
                cur_conv_kwargs = dict(downsample_conv_kwargs)
                cur_conv_kwargs['ratio_gout'] = resnet_conv_kwargs.get('ratio_gin', 0)
            else:
                cur_conv_kwargs = downsample_conv_kwargs
            model += [FFC_BN_ACT(min(max_features, ngf * mult), min(max_features, ngf * mult * 2), kernel_size=3, stride=2, padding=1, norm_layer=norm_layer, activation_layer=activation_layer, **cur_conv_kwargs)]
        mult = 2 ** n_downsampling
        feats_num_bottleneck = min(max_features, ngf * mult)
        for i in range(n_blocks):
            cur_resblock = FFCResnetBlock(feats_num_bottleneck, padding_type=padding_type, activation_layer=activation_layer, norm_layer=norm_layer, **resnet_conv_kwargs)
            if spatial_transform_layers is not None and i in spatial_transform_layers:
                cur_resblock = LearnableSpatialTransformWrapper(cur_resblock, **spatial_transform_kwargs)
            model += [cur_resblock]
        model += [ConcatTupleLayer()]
        for i in range(n_downsampling):
            mult = 2 ** (n_downsampling - i)
            model += [nn.ConvTranspose2d(min(max_features, ngf * mult), min(max_features, int(ngf * mult / 2)), kernel_size=3, stride=2, padding=1, output_padding=1), up_norm_layer(min(max_features, int(ngf * mult / 2))), up_activation]
        if out_ffc:
            model += [FFCResnetBlock(ngf, padding_type=padding_type, activation_layer=activation_layer, norm_layer=norm_layer, inline=True, **out_ffc_kwargs)]
        model += [nn.ReflectionPad2d(3), nn.Conv2d(ngf, output_nc, kernel_size=7, padding=0)]
        if add_out_act:
            model.append(get_activation('tanh' if add_out_act is True else add_out_act))
        self.model = nn.Sequential(*model)

    def forward(self, input):
        return self.model(input)

def forward(self, input):
    return self.model(input)

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

def get_all_activations(self, x):
    res = [x]
    for n in range(self.n_layers + 2):
        model = getattr(self, 'model' + str(n))
        res.append(model(res[-1]))
    return res[1:]

class MultiDilatedGlobalGenerator(nn.Module):

    def __init__(self, input_nc, output_nc, ngf=64, n_downsampling=3, n_blocks=3, norm_layer=nn.BatchNorm2d, padding_type='reflect', conv_kind='default', deconv_kind='convtranspose', activation=nn.ReLU(True), up_norm_layer=nn.BatchNorm2d, affine=None, up_activation=nn.ReLU(True), add_out_act=True, max_features=1024, multidilation_kwargs={}, ffc_positions=None, ffc_kwargs={}):
        assert n_blocks >= 0
        super().__init__()
        conv_layer = get_conv_block_ctor(conv_kind)
        resnet_conv_layer = functools.partial(get_conv_block_ctor('multidilated'), **multidilation_kwargs)
        norm_layer = get_norm_layer(norm_layer)
        if affine is not None:
            norm_layer = partial(norm_layer, affine=affine)
        up_norm_layer = get_norm_layer(up_norm_layer)
        if affine is not None:
            up_norm_layer = partial(up_norm_layer, affine=affine)
        model = [nn.ReflectionPad2d(3), conv_layer(input_nc, ngf, kernel_size=7, padding=0), norm_layer(ngf), activation]
        identity = Identity()
        for i in range(n_downsampling):
            mult = 2 ** i
            model += [conv_layer(min(max_features, ngf * mult), min(max_features, ngf * mult * 2), kernel_size=3, stride=2, padding=1), norm_layer(min(max_features, ngf * mult * 2)), activation]
        mult = 2 ** n_downsampling
        feats_num_bottleneck = min(max_features, ngf * mult)
        for i in range(n_blocks):
            if ffc_positions is not None and i in ffc_positions:
                model += [FFCResnetBlock(feats_num_bottleneck, padding_type, norm_layer, activation_layer=nn.ReLU, inline=True, **ffc_kwargs)]
            model += [MultidilatedResnetBlock(feats_num_bottleneck, padding_type=padding_type, conv_layer=resnet_conv_layer, activation=activation, norm_layer=norm_layer)]
        for i in range(n_downsampling):
            mult = 2 ** (n_downsampling - i)
            model += deconv_factory(deconv_kind, ngf, mult, up_norm_layer, up_activation, max_features)
        model += [nn.ReflectionPad2d(3), nn.Conv2d(ngf, output_nc, kernel_size=7, padding=0)]
        if add_out_act:
            model.append(get_activation('tanh' if add_out_act is True else add_out_act))
        self.model = nn.Sequential(*model)

    def forward(self, input):
        return self.model(input)

def forward(self, input):
    return self.model(input)

class ConfigGlobalGenerator(nn.Module):

    def __init__(self, input_nc, output_nc, ngf=64, n_downsampling=3, n_blocks=3, norm_layer=nn.BatchNorm2d, padding_type='reflect', conv_kind='default', deconv_kind='convtranspose', activation=nn.ReLU(True), up_norm_layer=nn.BatchNorm2d, affine=None, up_activation=nn.ReLU(True), add_out_act=True, max_features=1024, manual_block_spec=[], resnet_block_kind='multidilatedresnetblock', resnet_conv_kind='multidilated', resnet_dilation=1, multidilation_kwargs={}):
        assert n_blocks >= 0
        super().__init__()
        conv_layer = get_conv_block_ctor(conv_kind)
        resnet_conv_layer = functools.partial(get_conv_block_ctor(resnet_conv_kind), **multidilation_kwargs)
        norm_layer = get_norm_layer(norm_layer)
        if affine is not None:
            norm_layer = partial(norm_layer, affine=affine)
        up_norm_layer = get_norm_layer(up_norm_layer)
        if affine is not None:
            up_norm_layer = partial(up_norm_layer, affine=affine)
        model = [nn.ReflectionPad2d(3), conv_layer(input_nc, ngf, kernel_size=7, padding=0), norm_layer(ngf), activation]
        identity = Identity()
        for i in range(n_downsampling):
            mult = 2 ** i
            model += [conv_layer(min(max_features, ngf * mult), min(max_features, ngf * mult * 2), kernel_size=3, stride=2, padding=1), norm_layer(min(max_features, ngf * mult * 2)), activation]
        mult = 2 ** n_downsampling
        feats_num_bottleneck = min(max_features, ngf * mult)
        if len(manual_block_spec) == 0:
            manual_block_spec = [DotDict(lambda: None, {'n_blocks': n_blocks, 'use_default': True})]
        for block_spec in manual_block_spec:

            def make_and_add_blocks(model, block_spec):
                block_spec = DotDict(lambda: None, block_spec)
                if not block_spec.use_default:
                    resnet_conv_layer = functools.partial(get_conv_block_ctor(block_spec.resnet_conv_kind), **block_spec.multidilation_kwargs)
                    resnet_conv_kind = block_spec.resnet_conv_kind
                    resnet_block_kind = block_spec.resnet_block_kind
                    if block_spec.resnet_dilation is not None:
                        resnet_dilation = block_spec.resnet_dilation
                for i in range(block_spec.n_blocks):
                    if resnet_block_kind == 'multidilatedresnetblock':
                        model += [MultidilatedResnetBlock(feats_num_bottleneck, padding_type=padding_type, conv_layer=resnet_conv_layer, activation=activation, norm_layer=norm_layer)]
                    if resnet_block_kind == 'resnetblock':
                        model += [ResnetBlock(ngf * mult, padding_type=padding_type, activation=activation, norm_layer=norm_layer, conv_kind=resnet_conv_kind)]
                    if resnet_block_kind == 'resnetblock5x5':
                        model += [ResnetBlock5x5(ngf * mult, padding_type=padding_type, activation=activation, norm_layer=norm_layer, conv_kind=resnet_conv_kind)]
                    if resnet_block_kind == 'resnetblockdwdil':
                        model += [ResnetBlock(ngf * mult, padding_type=padding_type, activation=activation, norm_layer=norm_layer, conv_kind=resnet_conv_kind, dilation=resnet_dilation, second_dilation=resnet_dilation)]
            make_and_add_blocks(model, block_spec)
        for i in range(n_downsampling):
            mult = 2 ** (n_downsampling - i)
            model += deconv_factory(deconv_kind, ngf, mult, up_norm_layer, up_activation, max_features)
        model += [nn.ReflectionPad2d(3), nn.Conv2d(ngf, output_nc, kernel_size=7, padding=0)]
        if add_out_act:
            model.append(get_activation('tanh' if add_out_act is True else add_out_act))
        self.model = nn.Sequential(*model)

    def forward(self, input):
        return self.model(input)

def forward(self, input):
    return self.model(input)

class GlobalGenerator(nn.Module):

    def __init__(self, input_nc, output_nc, ngf=64, n_downsampling=3, n_blocks=9, norm_layer=nn.BatchNorm2d, padding_type='reflect', conv_kind='default', activation=nn.ReLU(True), up_norm_layer=nn.BatchNorm2d, affine=None, up_activation=nn.ReLU(True), dilated_blocks_n=0, dilated_blocks_n_start=0, dilated_blocks_n_middle=0, add_out_act=True, max_features=1024, is_resblock_depthwise=False, ffc_positions=None, ffc_kwargs={}, dilation=1, second_dilation=None, dilation_block_kind='simple', multidilation_kwargs={}):
        assert n_blocks >= 0
        super().__init__()
        conv_layer = get_conv_block_ctor(conv_kind)
        norm_layer = get_norm_layer(norm_layer)
        if affine is not None:
            norm_layer = partial(norm_layer, affine=affine)
        up_norm_layer = get_norm_layer(up_norm_layer)
        if affine is not None:
            up_norm_layer = partial(up_norm_layer, affine=affine)
        if ffc_positions is not None:
            ffc_positions = collections.Counter(ffc_positions)
        model = [nn.ReflectionPad2d(3), conv_layer(input_nc, ngf, kernel_size=7, padding=0), norm_layer(ngf), activation]
        identity = Identity()
        for i in range(n_downsampling):
            mult = 2 ** i
            model += [conv_layer(min(max_features, ngf * mult), min(max_features, ngf * mult * 2), kernel_size=3, stride=2, padding=1), norm_layer(min(max_features, ngf * mult * 2)), activation]
        mult = 2 ** n_downsampling
        feats_num_bottleneck = min(max_features, ngf * mult)
        dilated_block_kwargs = dict(dim=feats_num_bottleneck, padding_type=padding_type, activation=activation, norm_layer=norm_layer)
        if dilation_block_kind == 'simple':
            dilated_block_kwargs['conv_kind'] = conv_kind
        elif dilation_block_kind == 'multi':
            dilated_block_kwargs['conv_layer'] = functools.partial(get_conv_block_ctor('multidilated'), **multidilation_kwargs)
        if dilated_blocks_n_start is not None and dilated_blocks_n_start > 0:
            model += make_dil_blocks(dilated_blocks_n_start, dilation_block_kind, dilated_block_kwargs)
        for i in range(n_blocks):
            if i == n_blocks // 2 and dilated_blocks_n_middle is not None and (dilated_blocks_n_middle > 0):
                model += make_dil_blocks(dilated_blocks_n_middle, dilation_block_kind, dilated_block_kwargs)
            if ffc_positions is not None and i in ffc_positions:
                for _ in range(ffc_positions[i]):
                    model += [FFCResnetBlock(feats_num_bottleneck, padding_type, norm_layer, activation_layer=nn.ReLU, inline=True, **ffc_kwargs)]
            if is_resblock_depthwise:
                resblock_groups = feats_num_bottleneck
            else:
                resblock_groups = 1
            model += [ResnetBlock(feats_num_bottleneck, padding_type=padding_type, activation=activation, norm_layer=norm_layer, conv_kind=conv_kind, groups=resblock_groups, dilation=dilation, second_dilation=second_dilation)]
        if dilated_blocks_n is not None and dilated_blocks_n > 0:
            model += make_dil_blocks(dilated_blocks_n, dilation_block_kind, dilated_block_kwargs)
        for i in range(n_downsampling):
            mult = 2 ** (n_downsampling - i)
            model += [nn.ConvTranspose2d(min(max_features, ngf * mult), min(max_features, int(ngf * mult / 2)), kernel_size=3, stride=2, padding=1, output_padding=1), up_norm_layer(min(max_features, int(ngf * mult / 2))), up_activation]
        model += [nn.ReflectionPad2d(3), nn.Conv2d(ngf, output_nc, kernel_size=7, padding=0)]
        if add_out_act:
            model.append(get_activation('tanh' if add_out_act is True else add_out_act))
        self.model = nn.Sequential(*model)

    def forward(self, input):
        return self.model(input)

def forward(self, input):
    return self.model(input)

class GlobalGeneratorFromSuperChannels(nn.Module):

    def __init__(self, input_nc, output_nc, n_downsampling, n_blocks, super_channels, norm_layer='bn', padding_type='reflect', add_out_act=True):
        super().__init__()
        self.n_downsampling = n_downsampling
        norm_layer = get_norm_layer(norm_layer)
        if type(norm_layer) == functools.partial:
            use_bias = norm_layer.func == nn.InstanceNorm2d
        else:
            use_bias = norm_layer == nn.InstanceNorm2d
        channels = self.convert_super_channels(super_channels)
        self.channels = channels
        model = [nn.ReflectionPad2d(3), nn.Conv2d(input_nc, channels[0], kernel_size=7, padding=0, bias=use_bias), norm_layer(channels[0]), nn.ReLU(True)]
        for i in range(n_downsampling):
            mult = 2 ** i
            model += [nn.Conv2d(channels[0 + i], channels[1 + i], kernel_size=3, stride=2, padding=1, bias=use_bias), norm_layer(channels[1 + i]), nn.ReLU(True)]
        mult = 2 ** n_downsampling
        n_blocks1 = n_blocks // 3
        n_blocks2 = n_blocks1
        n_blocks3 = n_blocks - n_blocks1 - n_blocks2
        for i in range(n_blocks1):
            c = n_downsampling
            dim = channels[c]
            model += [ResnetBlock(dim, padding_type=padding_type, norm_layer=norm_layer)]
        for i in range(n_blocks2):
            c = n_downsampling + 1
            dim = channels[c]
            kwargs = {}
            if i == 0:
                kwargs = {'in_dim': channels[c - 1]}
            model += [ResnetBlock(dim, padding_type=padding_type, norm_layer=norm_layer, **kwargs)]
        for i in range(n_blocks3):
            c = n_downsampling + 2
            dim = channels[c]
            kwargs = {}
            if i == 0:
                kwargs = {'in_dim': channels[c - 1]}
            model += [ResnetBlock(dim, padding_type=padding_type, norm_layer=norm_layer, **kwargs)]
        for i in range(n_downsampling):
            mult = 2 ** (n_downsampling - i)
            model += [nn.ConvTranspose2d(channels[n_downsampling + 3 + i], channels[n_downsampling + 3 + i + 1], kernel_size=3, stride=2, padding=1, output_padding=1, bias=use_bias), norm_layer(channels[n_downsampling + 3 + i + 1]), nn.ReLU(True)]
        model += [nn.ReflectionPad2d(3)]
        model += [nn.Conv2d(channels[2 * n_downsampling + 3], output_nc, kernel_size=7, padding=0)]
        if add_out_act:
            model.append(get_activation('tanh' if add_out_act is True else add_out_act))
        self.model = nn.Sequential(*model)

    def convert_super_channels(self, super_channels):
        n_downsampling = self.n_downsampling
        result = []
        cnt = 0
        if n_downsampling == 2:
            N1 = 10
        elif n_downsampling == 3:
            N1 = 13
        else:
            raise NotImplementedError
        for i in range(0, N1):
            if i in [1, 4, 7, 10]:
                channel = super_channels[cnt] * 2 ** cnt
                config = {'channel': channel}
                result.append(channel)
                logging.info(f'Downsample channels {result[-1]}')
                cnt += 1
        for i in range(3):
            for counter, j in enumerate(range(N1 + i * 3, N1 + 3 + i * 3)):
                if len(super_channels) == 6:
                    channel = super_channels[3] * 4
                else:
                    channel = super_channels[i + 3] * 4
                config = {'channel': channel}
                if counter == 0:
                    result.append(channel)
                    logging.info(f'Bottleneck channels {result[-1]}')
        cnt = 2
        for i in range(N1 + 9, N1 + 21):
            if i in [22, 25, 28]:
                cnt -= 1
                if len(super_channels) == 6:
                    channel = super_channels[5 - cnt] * 2 ** cnt
                else:
                    channel = super_channels[7 - cnt] * 2 ** cnt
                result.append(int(channel))
                logging.info(f'Upsample channels {result[-1]}')
        return result

    def forward(self, input):
        return self.model(input)

def forward(self, input):
    return self.model(input)

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

def get_all_activations(self, x):
    res = [x]
    for n in range(self.n_layers + 2):
        model = getattr(self, 'model' + str(n))
        res.append(model(res[-1]))
    return res[1:]

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

def get_all_activations(self, x):
    res = [x]
    for n in range(self.n_layers + 2):
        model = getattr(self, 'model' + str(n))
        res.append(model(res[-1]))
    return res[1:]

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

def reset(self):
    super().reset()
    self.target_class_freq_by_image_total = []
    self.target_class_freq_by_image_mask = []
    self.pred_class_freq_by_image_mask = []

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

def reset(self):
    super().reset()
    self.individual_values = []

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

def __init__(self, *args, dims=2048, eps=1e-06, n_jobs=-1, **kwargs):
    super().__init__(*args, **kwargs)
    if getattr(FIDScore, '_MODEL', None) is None:
        block_idx = InceptionV3.BLOCK_INDEX_BY_DIM[dims]
        FIDScore._MODEL = InceptionV3([block_idx]).eval()
    self.model = FIDScore._MODEL
    self.eps = eps
    self.n_jobs = n_jobs

class PerceptualLoss(torch.nn.Module):

    def __init__(self, model='net-lin', net='alex', colorspace='rgb', model_path=None, spatial=False, use_gpu=True):
        super(PerceptualLoss, self).__init__()
        self.use_gpu = use_gpu
        self.spatial = spatial
        self.model = DistModel()
        self.model.initialize(model=model, net=net, use_gpu=use_gpu, colorspace=colorspace, model_path=model_path, spatial=self.spatial)

    def forward(self, pred, target, normalize=True):
        """
        Pred and target are Variables.
        If normalize is True, assumes the images are between [0,1] and then scales them between [-1,+1]
        If normalize is False, assumes the images are already between [-1,+1]
        Inputs pred and target are Nx3xHxW
        Output pytorch Variable N long
        """
        if normalize:
            target = 2 * target - 1
            pred = 2 * pred - 1
        return self.model(target, pred)

def forward(self, pred, target, normalize=True):
    """
        Pred and target are Variables.
        If normalize is True, assumes the images are between [0,1] and then scales them between [-1,+1]
        If normalize is False, assumes the images are already between [-1,+1]
        Inputs pred and target are Nx3xHxW
        Output pytorch Variable N long
        """
    if normalize:
        target = 2 * target - 1
        pred = 2 * pred - 1
    return self.model(target, pred)

class Dist2LogitLayer(nn.Module):
    """ takes 2 distances, puts through fc layers, spits out value between [0,1] (if use_sigmoid is True) """

    def __init__(self, chn_mid=32, use_sigmoid=True):
        super(Dist2LogitLayer, self).__init__()
        layers = [nn.Conv2d(5, chn_mid, 1, stride=1, padding=0, bias=True)]
        layers += [nn.LeakyReLU(0.2, True)]
        layers += [nn.Conv2d(chn_mid, chn_mid, 1, stride=1, padding=0, bias=True)]
        layers += [nn.LeakyReLU(0.2, True)]
        layers += [nn.Conv2d(chn_mid, 1, 1, stride=1, padding=0, bias=True)]
        if use_sigmoid:
            layers += [nn.Sigmoid()]
        self.model = nn.Sequential(*layers)

    def forward(self, d0, d1, eps=0.1):
        return self.model(torch.cat((d0, d1, d0 - d1, d0 / (d1 + eps), d1 / (d0 + eps)), dim=1))

def forward(self, d0, d1, eps=0.1):
    return self.model(torch.cat((d0, d1, d0 - d1, d0 / (d1 + eps), d1 / (d0 + eps)), dim=1))

def benchmark():

    def countless3d_generalized(img):
        return countless_generalized(img, (2, 8, 1))

    def countless3d_dynamic_generalized(img):
        return dynamic_countless_generalized(img, (8, 8, 1))
    methods = [countless3d_generalized]
    data = np.zeros(shape=(16 ** 2, 16 ** 2, 16 ** 2), dtype=np.uint8) + 1
    N = 5
    print('Algorithm\tMPx\tMB/sec\tSec\tN=%d' % N)
    for fn in methods:
        start = time.time()
        for _ in range(N):
            result = fn(data)
        end = time.time()
        total_time = end - start
        mpx = N * float(data.shape[0] * data.shape[1] * data.shape[2]) / total_time / 1024.0 / 1024.0
        mbytes = mpx * np.dtype(data.dtype).itemsize
        print('%s\t%.3f\t%.3f\t%.2f' % (fn.__name__, mpx, mbytes, total_time))

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

def concat(self, other):
    """Concatenates two dicts without copying internal data."""
    return TensorDict(self, **other)

def copy(self):
    return TensorDict(super(TensorDict, self).copy())

def __deepcopy__(self, memodict={}):
    return TensorDict(copy.deepcopy(list(self), memodict))

def apply_attr(*args, **kwargs):
    return TensorDict({n: getattr(e, name)(*args, **kwargs) if hasattr(e, name) else e for n, e in self.items()})

def attribute(self, attr: str, *args):
    return TensorDict({n: getattr(e, attr, *args) for n, e in self.items()})

def apply(self, fn, *args, **kwargs):
    return TensorDict({n: fn(e, *args, **kwargs) for n, e in self.items()})

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

def attribute(self, attr: str, *args):
    return TensorList([getattr(e, attr, *args) for e in self])

def apply(self, fn):
    return TensorList([fn(e) for e in self])

def apply_attr(*args, **kwargs):
    return TensorList([getattr(e, name)(*args, **kwargs) for e in self])

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

def get(self, name: str, *default):
    """Get a parameter value with the given name. If it does not exists, it return the default value given as a
        second argument or returns an error if no default value is given."""
    if len(default) > 1:
        raise ValueError('Can only give one default value.')
    if not default:
        return getattr(self, name)
    return getattr(self, name, default[0])

class Sequence:
    """Class for the sequence in an evaluation."""

    def __init__(self, name, frames, dataset, ground_truth_rect, ground_truth_seg=None, init_data=None, object_class=None, target_visible=None, object_ids=None, multiobj_mode=False):
        self.name = name
        self.frames = frames
        self.dataset = dataset
        self.ground_truth_rect = ground_truth_rect
        self.ground_truth_seg = ground_truth_seg
        self.object_class = object_class
        self.target_visible = target_visible
        self.object_ids = object_ids
        self.multiobj_mode = multiobj_mode
        self.init_data = self._construct_init_data(init_data)
        self._ensure_start_frame()

    def _ensure_start_frame(self):
        start_frame = min(list(self.init_data.keys()))
        if start_frame > 0:
            self.frames = self.frames[start_frame:]
            if self.ground_truth_rect is not None:
                if isinstance(self.ground_truth_rect, (dict, OrderedDict)):
                    for obj_id, gt in self.ground_truth_rect.items():
                        self.ground_truth_rect[obj_id] = gt[start_frame:, :]
                else:
                    self.ground_truth_rect = self.ground_truth_rect[start_frame:, :]
            if self.ground_truth_seg is not None:
                self.ground_truth_seg = self.ground_truth_seg[start_frame:]
                assert len(self.frames) == len(self.ground_truth_seg)
            if self.target_visible is not None:
                self.target_visible = self.target_visible[start_frame:]
            self.init_data = {frame - start_frame: val for frame, val in self.init_data.items()}

    def _construct_init_data(self, init_data):
        if init_data is not None:
            if not self.multiobj_mode:
                assert self.object_ids is None or len(self.object_ids) == 1
                for frame, init_val in init_data.items():
                    if 'bbox' in init_val and isinstance(init_val['bbox'], (dict, OrderedDict)):
                        init_val['bbox'] = init_val['bbox'][self.object_ids[0]]
            for frame, init_val in init_data.items():
                if 'bbox' in init_val:
                    if isinstance(init_val['bbox'], (dict, OrderedDict)):
                        init_val['bbox'] = OrderedDict({obj_id: list(init) for obj_id, init in init_val['bbox'].items()})
                    else:
                        init_val['bbox'] = list(init_val['bbox'])
        else:
            init_data = {0: dict()}
            if self.object_ids is not None:
                init_data[0]['object_ids'] = self.object_ids
            if self.ground_truth_rect is not None:
                if self.multiobj_mode:
                    assert isinstance(self.ground_truth_rect, (dict, OrderedDict))
                    init_data[0]['bbox'] = OrderedDict({obj_id: list(gt[0, :]) for obj_id, gt in self.ground_truth_rect.items()})
                else:
                    assert self.object_ids is None or len(self.object_ids) == 1
                    if isinstance(self.ground_truth_rect, (dict, OrderedDict)):
                        init_data[0]['bbox'] = list(self.ground_truth_rect[self.object_ids[0]][0, :])
                    else:
                        init_data[0]['bbox'] = list(self.ground_truth_rect[0, :])
            if self.ground_truth_seg is not None:
                init_data[0]['mask'] = self.ground_truth_seg[0]
        return init_data

    def init_info(self):
        info = self.frame_info(frame_num=0)
        return info

    def frame_info(self, frame_num):
        info = self.object_init_data(frame_num=frame_num)
        return info

    def init_bbox(self, frame_num=0):
        return self.object_init_data(frame_num=frame_num).get('init_bbox')

    def init_mask(self, frame_num=0):
        return self.object_init_data(frame_num=frame_num).get('init_mask')

    def get_info(self, keys, frame_num=None):
        info = dict()
        for k in keys:
            val = self.get(k, frame_num=frame_num)
            if val is not None:
                info[k] = val
        return info

    def object_init_data(self, frame_num=None) -> dict:
        if frame_num is None:
            frame_num = 0
        if frame_num not in self.init_data:
            return dict()
        init_data = dict()
        for key, val in self.init_data[frame_num].items():
            if val is None:
                continue
            init_data['init_' + key] = val
        if 'init_mask' in init_data and init_data['init_mask'] is not None:
            anno = imread_indexed(init_data['init_mask'])
            if not self.multiobj_mode and self.object_ids is not None:
                assert len(self.object_ids) == 1
                anno = (anno == int(self.object_ids[0])).astype(np.uint8)
            init_data['init_mask'] = anno
        if self.object_ids is not None:
            init_data['object_ids'] = self.object_ids
            init_data['sequence_object_ids'] = self.object_ids
        return init_data

    def target_class(self, frame_num=None):
        return self.object_class

    def get(self, name, frame_num=None):
        return getattr(self, name)(frame_num)

    def __repr__(self):
        return '{self.__class__.__name__} {self.name}, length={len} frames'.format(self=self, len=len(self.frames))

def get(self, name, frame_num=None):
    return getattr(self, name)(frame_num)

class Tracker:
    """Wraps the tracker for evaluation and running purposes.
    args:
        name: Name of tracking method.
        parameter_name: Name of parameter file.
        run_id: The run id.
        display_name: Name to be displayed in the result plots.
    """

    def __init__(self, name: str, parameter_name: str, dataset_name: str, run_id: int=None, display_name: str=None, result_only=False):
        assert run_id is None or isinstance(run_id, int)
        self.name = name
        self.parameter_name = parameter_name
        self.dataset_name = dataset_name
        self.run_id = run_id
        self.display_name = display_name
        tracker_module_abspath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tracker', '%s.py' % self.name))
        if os.path.isfile(tracker_module_abspath):
            tracker_module = importlib.import_module('lib.test.tracker.{}'.format(self.name))
            self.tracker_class = tracker_module.get_tracker_class()
        else:
            self.tracker_class = None

    def create_tracker(self, params):
        tracker = self.tracker_class(params, self.dataset_name)
        return tracker

    def run_sequence(self, seq, debug=None):
        """Run tracker on sequence.
        args:
            seq: Sequence to run the tracker on.
            visualization: Set visualization flag (None means default value specified in the parameters).
            debug: Set debug level (None means default value specified in the parameters).
            multiobj_mode: Which mode to use for multiple objects.
        """
        params = self.get_parameters()
        debug_ = debug
        if debug is None:
            debug_ = getattr(params, 'debug', 0)
        params.debug = debug_
        init_info = seq.init_info()
        tracker = self.create_tracker(params)
        output = self._track_sequence(tracker, seq, init_info)
        return output

    def _track_sequence(self, tracker, seq, init_info):
        output = {'target_bbox': [], 'time': []}
        if tracker.params.save_all_boxes:
            output['all_boxes'] = []
            output['all_scores'] = []

        def _store_outputs(tracker_out: dict, defaults=None):
            defaults = {} if defaults is None else defaults
            for key in output.keys():
                val = tracker_out.get(key, defaults.get(key, None))
                if key in tracker_out or val is not None:
                    output[key].append(val)
        image = self._read_image(seq.frames[0])
        start_time = time.time()
        out = tracker.initialize(image, init_info)
        if out is None:
            out = {}
        prev_output = OrderedDict(out)
        init_default = {'target_bbox': init_info.get('init_bbox'), 'time': time.time() - start_time}
        if tracker.params.save_all_boxes:
            init_default['all_boxes'] = out['all_boxes']
            init_default['all_scores'] = out['all_scores']
        _store_outputs(out, init_default)
        for frame_num, frame_path in enumerate(seq.frames[1:], start=1):
            image = self._read_image(frame_path)
            start_time = time.time()
            info = seq.frame_info(frame_num)
            info['previous_output'] = prev_output
            if len(seq.ground_truth_rect) > 1:
                info['gt_bbox'] = seq.ground_truth_rect[frame_num]
            out = tracker.track(image, info)
            prev_output = OrderedDict(out)
            _store_outputs(out, {'time': time.time() - start_time})
        for key in ['target_bbox', 'all_boxes', 'all_scores']:
            if key in output and len(output[key]) <= 1:
                output.pop(key)
        return output

    def run_video(self, videofilepath, optional_box=None, debug=None, visdom_info=None, save_results=False):
        """Run the tracker with the vieofile.
        args:
            debug: Debug level.
        """
        params = self.get_parameters()
        debug_ = debug
        if debug is None:
            debug_ = getattr(params, 'debug', 0)
        params.debug = debug_
        params.tracker_name = self.name
        params.param_name = self.parameter_name
        multiobj_mode = getattr(params, 'multiobj_mode', getattr(self.tracker_class, 'multiobj_mode', 'default'))
        if multiobj_mode == 'default':
            tracker = self.create_tracker(params)
        elif multiobj_mode == 'parallel':
            tracker = MultiObjectWrapper(self.tracker_class, params, self.visdom, fast_load=True)
        else:
            raise ValueError('Unknown multi object mode {}'.format(multiobj_mode))
        assert os.path.isfile(videofilepath), 'Invalid param {}'.format(videofilepath)
        ', videofilepath must be a valid videofile'
        output_boxes = []
        cap = cv.VideoCapture(videofilepath)
        display_name = 'Display: ' + tracker.params.tracker_name
        cv.namedWindow(display_name, cv.WINDOW_NORMAL | cv.WINDOW_KEEPRATIO)
        cv.resizeWindow(display_name, 960, 720)
        success, frame = cap.read()
        cv.imshow(display_name, frame)

        def _build_init_info(box):
            return {'init_bbox': box}
        if success is not True:
            print('Read frame from {} failed.'.format(videofilepath))
            exit(-1)
        if optional_box is not None:
            assert isinstance(optional_box, (list, tuple))
            assert len(optional_box) == 4, "valid box's foramt is [x,y,w,h]"
            tracker.initialize(frame, _build_init_info(optional_box))
            output_boxes.append(optional_box)
        else:
            while True:
                frame_disp = frame.copy()
                cv.putText(frame_disp, 'Select target ROI and press ENTER', (20, 30), cv.FONT_HERSHEY_COMPLEX_SMALL, 1.5, (0, 0, 0), 1)
                x, y, w, h = cv.selectROI(display_name, frame_disp, fromCenter=False)
                init_state = [x, y, w, h]
                tracker.initialize(frame, _build_init_info(init_state))
                output_boxes.append(init_state)
                break
        while True:
            ret, frame = cap.read()
            if frame is None:
                break
            frame_disp = frame.copy()
            out = tracker.track(frame)
            state = [int(s) for s in out['target_bbox']]
            output_boxes.append(state)
            cv.rectangle(frame_disp, (state[0], state[1]), (state[2] + state[0], state[3] + state[1]), (0, 255, 0), 5)
            font_color = (0, 0, 0)
            cv.putText(frame_disp, 'Tracking!', (20, 30), cv.FONT_HERSHEY_COMPLEX_SMALL, 1, font_color, 1)
            cv.putText(frame_disp, 'Press r to reset', (20, 55), cv.FONT_HERSHEY_COMPLEX_SMALL, 1, font_color, 1)
            cv.putText(frame_disp, 'Press q to quit', (20, 80), cv.FONT_HERSHEY_COMPLEX_SMALL, 1, font_color, 1)
            cv.imshow(display_name, frame_disp)
            key = cv.waitKey(1)
            if key == ord('q'):
                break
            elif key == ord('r'):
                ret, frame = cap.read()
                frame_disp = frame.copy()
                cv.putText(frame_disp, 'Select target ROI and press ENTER', (20, 30), cv.FONT_HERSHEY_COMPLEX_SMALL, 1.5, (0, 0, 0), 1)
                cv.imshow(display_name, frame_disp)
                x, y, w, h = cv.selectROI(display_name, frame_disp, fromCenter=False)
                init_state = [x, y, w, h]
                tracker.initialize(frame, _build_init_info(init_state))
                output_boxes.append(init_state)
        cap.release()
        cv.destroyAllWindows()
        if save_results:
            if not os.path.exists(self.results_dir):
                os.makedirs(self.results_dir)
            video_name = Path(videofilepath).stem
            base_results_path = os.path.join(self.results_dir, 'video_{}'.format(video_name))
            tracked_bb = np.array(output_boxes).astype(int)
            bbox_file = '{}.txt'.format(base_results_path)
            np.savetxt(bbox_file, tracked_bb, delimiter='\t', fmt='%d')

    def get_parameters(self):
        """Get parameters."""
        param_module = importlib.import_module('lib.test.parameter.{}'.format(self.name))
        params = param_module.parameters(self.parameter_name)
        return params

    def _read_image(self, image_file: str):
        if isinstance(image_file, str):
            im = cv.imread(image_file)
            return cv.cvtColor(im, cv.COLOR_BGR2RGB)
        elif isinstance(image_file, list) and len(image_file) == 2:
            return decode_img(image_file[0], image_file[1])
        else:
            raise ValueError('type of image_file should be str or list')

def run_sequence(self, seq, debug=None):
    """Run tracker on sequence.
        args:
            seq: Sequence to run the tracker on.
            visualization: Set visualization flag (None means default value specified in the parameters).
            debug: Set debug level (None means default value specified in the parameters).
            multiobj_mode: Which mode to use for multiple objects.
        """
    params = self.get_parameters()
    debug_ = debug
    if debug is None:
        debug_ = getattr(params, 'debug', 0)
    params.debug = debug_
    init_info = seq.init_info()
    tracker = self.create_tracker(params)
    output = self._track_sequence(tracker, seq, init_info)
    return output

def build_box_head(cfg, hidden_dim):
    stride = cfg.MODEL.BACKBONE.STRIDE
    if cfg.MODEL.HEAD.TYPE == 'MLP':
        mlp_head = MLP(hidden_dim, hidden_dim, 4, 3)
        return mlp_head
    elif 'CORNER' in cfg.MODEL.HEAD.TYPE:
        feat_sz = int(cfg.DATA.SEARCH.SIZE / stride)
        channel = getattr(cfg.MODEL, 'NUM_CHANNELS', 256)
        print('head channel: %d' % channel)
        if cfg.MODEL.HEAD.TYPE == 'CORNER':
            corner_head = Corner_Predictor(inplanes=cfg.MODEL.HIDDEN_DIM, channel=channel, feat_sz=feat_sz, stride=stride)
        else:
            raise ValueError()
        return corner_head
    elif cfg.MODEL.HEAD.TYPE == 'CENTER':
        in_channel = hidden_dim
        out_channel = cfg.MODEL.HEAD.NUM_CHANNELS
        feat_sz = int(cfg.DATA.SEARCH.SIZE / stride)
        center_head = CenterPredictor(inplanes=in_channel, channel=out_channel, feat_sz=feat_sz, stride=stride)
        return center_head
    else:
        raise ValueError('HEAD TYPE %s is not supported.' % cfg.MODEL.HEAD_TYPE)

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

def setup(self, stage=None):
    self.datasets = dict(((k, instantiate_from_config(self.dataset_configs[k])) for k in self.dataset_configs))
    if self.wrap:
        for k in self.datasets:
            self.datasets[k] = WrappedDataset(self.datasets[k])

def load_model_from_config(config, sd):
    model = instantiate_from_config(config)
    model.load_state_dict(sd, strict=False)
    model.cuda()
    model.eval()
    return model

class Scale(nn.Module):

    def __init__(self, value, fn):
        super().__init__()
        self.value = value
        self.fn = fn

    def forward(self, x, **kwargs):
        x, *rest = self.fn(x, **kwargs)
        return (x * self.value, *rest)

def forward(self, x, **kwargs):
    x, *rest = self.fn(x, **kwargs)
    return (x * self.value, *rest)

class Rezero(nn.Module):

    def __init__(self, fn):
        super().__init__()
        self.fn = fn
        self.g = nn.Parameter(torch.zeros(1))

    def forward(self, x, **kwargs):
        x, *rest = self.fn(x, **kwargs)
        return (x * self.g, *rest)

def forward(self, x, **kwargs):
    x, *rest = self.fn(x, **kwargs)
    return (x * self.g, *rest)

class FirstStagePostProcessor(nn.Module):

    def __init__(self, ch_mult: list, in_channels, pretrained_model: nn.Module=None, reshape=False, n_channels=None, dropout=0.0, pretrained_config=None):
        super().__init__()
        if pretrained_config is None:
            assert pretrained_model is not None, 'Either "pretrained_model" or "pretrained_config" must not be None'
            self.pretrained_model = pretrained_model
        else:
            assert pretrained_config is not None, 'Either "pretrained_model" or "pretrained_config" must not be None'
            self.instantiate_pretrained(pretrained_config)
        self.do_reshape = reshape
        if n_channels is None:
            n_channels = self.pretrained_model.encoder.ch
        self.proj_norm = Normalize(in_channels, num_groups=in_channels // 2)
        self.proj = nn.Conv2d(in_channels, n_channels, kernel_size=3, stride=1, padding=1)
        blocks = []
        downs = []
        ch_in = n_channels
        for m in ch_mult:
            blocks.append(ResnetBlock(in_channels=ch_in, out_channels=m * n_channels, dropout=dropout))
            ch_in = m * n_channels
            downs.append(Downsample(ch_in, with_conv=False))
        self.model = nn.ModuleList(blocks)
        self.downsampler = nn.ModuleList(downs)

    def instantiate_pretrained(self, config):
        model = instantiate_from_config(config)
        self.pretrained_model = model.eval()
        for param in self.pretrained_model.parameters():
            param.requires_grad = False

    @torch.no_grad()
    def encode_with_pretrained(self, x):
        c = self.pretrained_model.encode(x)
        if isinstance(c, DiagonalGaussianDistribution):
            c = c.mode()
        return c

    def forward(self, x):
        z_fs = self.encode_with_pretrained(x)
        z = self.proj_norm(z_fs)
        z = self.proj(z)
        z = nonlinearity(z)
        for submodel, downmodel in zip(self.model, self.downsampler):
            z = submodel(z, temb=None)
            z = downmodel(z)
        if self.do_reshape:
            z = rearrange(z, 'b c h w -> b (h w) c')
        return z

def instantiate_pretrained(self, config):
    model = instantiate_from_config(config)
    self.pretrained_model = model.eval()
    for param in self.pretrained_model.parameters():
        param.requires_grad = False

class CheckpointFunction(torch.autograd.Function):

    @staticmethod
    def forward(ctx, run_function, length, *args):
        ctx.run_function = run_function
        ctx.input_tensors = list(args[:length])
        ctx.input_params = list(args[length:])
        with torch.no_grad():
            output_tensors = ctx.run_function(*ctx.input_tensors)
        return output_tensors

    @staticmethod
    def backward(ctx, *output_grads):
        ctx.input_tensors = [x.detach().requires_grad_(True) for x in ctx.input_tensors]
        with torch.enable_grad():
            shallow_copies = [x.view_as(x) for x in ctx.input_tensors]
            output_tensors = ctx.run_function(*shallow_copies)
        input_grads = torch.autograd.grad(output_tensors, ctx.input_tensors + ctx.input_params, output_grads, allow_unused=True)
        del ctx.input_tensors
        del ctx.input_params
        del output_tensors
        return (None, None) + input_grads

@staticmethod
def forward(ctx, run_function, length, *args):
    ctx.run_function = run_function
    ctx.input_tensors = list(args[:length])
    ctx.input_params = list(args[length:])
    with torch.no_grad():
        output_tensors = ctx.run_function(*ctx.input_tensors)
    return output_tensors

@staticmethod
def backward(ctx, *output_grads):
    ctx.input_tensors = [x.detach().requires_grad_(True) for x in ctx.input_tensors]
    with torch.enable_grad():
        shallow_copies = [x.view_as(x) for x in ctx.input_tensors]
        output_tensors = ctx.run_function(*shallow_copies)
    input_grads = torch.autograd.grad(output_tensors, ctx.input_tensors + ctx.input_params, output_grads, allow_unused=True)
    del ctx.input_tensors
    del ctx.input_params
    del output_tensors
    return (None, None) + input_grads

class FrozenCLIPTextEmbedder(nn.Module):
    """
    Uses the CLIP transformer encoder for text.
    """

    def __init__(self, version='ViT-L/14', device='cuda', max_length=77, n_repeat=1, normalize=True):
        super().__init__()
        self.model, _ = clip.load(version, jit=False, device='cpu')
        self.device = device
        self.max_length = max_length
        self.n_repeat = n_repeat
        self.normalize = normalize

    def freeze(self):
        self.model = self.model.eval()
        for param in self.parameters():
            param.requires_grad = False

    def forward(self, text):
        tokens = clip.tokenize(text).to(self.device)
        z = self.model.encode_text(tokens)
        if self.normalize:
            z = z / torch.linalg.norm(z, dim=1, keepdim=True)
        return z

    def encode(self, text):
        z = self(text)
        if z.ndim == 2:
            z = z[:, None, :]
        z = repeat(z, 'b 1 d -> b k d', k=self.n_repeat)
        return z

def freeze(self):
    self.model = self.model.eval()
    for param in self.parameters():
        param.requires_grad = False

class VQModel(pl.LightningModule):

    def __init__(self, ddconfig, lossconfig, n_embed, embed_dim, ckpt_path=None, ignore_keys=[], image_key='image', colorize_nlabels=None, monitor=None, batch_resize_range=None, scheduler_config=None, lr_g_factor=1.0, remap=None, sane_index_shape=False, use_ema=False):
        super().__init__()
        self.embed_dim = embed_dim
        self.n_embed = n_embed
        self.image_key = image_key
        self.encoder = Encoder(**ddconfig)
        self.decoder = Decoder(**ddconfig)
        self.loss = instantiate_from_config(lossconfig)
        self.quantize = VectorQuantizer(n_embed, embed_dim, beta=0.25, remap=remap, sane_index_shape=sane_index_shape)
        self.quant_conv = torch.nn.Conv2d(ddconfig['z_channels'], embed_dim, 1)
        self.post_quant_conv = torch.nn.Conv2d(embed_dim, ddconfig['z_channels'], 1)
        if colorize_nlabels is not None:
            assert type(colorize_nlabels) == int
            self.register_buffer('colorize', torch.randn(3, colorize_nlabels, 1, 1))
        if monitor is not None:
            self.monitor = monitor
        self.batch_resize_range = batch_resize_range
        if self.batch_resize_range is not None:
            print(f'{self.__class__.__name__}: Using per-batch resizing in range {batch_resize_range}.')
        self.use_ema = use_ema
        if self.use_ema:
            self.model_ema = LitEma(self)
            print(f'Keeping EMAs of {len(list(self.model_ema.buffers()))}.')
        if ckpt_path is not None:
            self.init_from_ckpt(ckpt_path, ignore_keys=ignore_keys)
        self.scheduler_config = scheduler_config
        self.lr_g_factor = lr_g_factor

    @contextmanager
    def ema_scope(self, context=None):
        if self.use_ema:
            self.model_ema.store(self.parameters())
            self.model_ema.copy_to(self)
            if context is not None:
                print(f'{context}: Switched to EMA weights')
        try:
            yield None
        finally:
            if self.use_ema:
                self.model_ema.restore(self.parameters())
                if context is not None:
                    print(f'{context}: Restored training weights')

    def init_from_ckpt(self, path, ignore_keys=list()):
        sd = torch.load(path, map_location='cpu')['state_dict']
        keys = list(sd.keys())
        for k in keys:
            for ik in ignore_keys:
                if k.startswith(ik):
                    print('Deleting key {} from state_dict.'.format(k))
                    del sd[k]
        missing, unexpected = self.load_state_dict(sd, strict=False)
        print(f'Restored from {path} with {len(missing)} missing and {len(unexpected)} unexpected keys')
        if len(missing) > 0:
            print(f'Missing Keys: {missing}')
            print(f'Unexpected Keys: {unexpected}')

    def on_train_batch_end(self, *args, **kwargs):
        if self.use_ema:
            self.model_ema(self)

    def encode(self, x):
        h = self.encoder(x)
        h = self.quant_conv(h)
        quant, emb_loss, info = self.quantize(h)
        return (quant, emb_loss, info)

    def encode_to_prequant(self, x):
        h = self.encoder(x)
        h = self.quant_conv(h)
        return h

    def decode(self, quant):
        quant = self.post_quant_conv(quant)
        dec = self.decoder(quant)
        return dec

    def decode_code(self, code_b):
        quant_b = self.quantize.embed_code(code_b)
        dec = self.decode(quant_b)
        return dec

    def forward(self, input, return_pred_indices=False):
        quant, diff, (_, _, ind) = self.encode(input)
        dec = self.decode(quant)
        if return_pred_indices:
            return (dec, diff, ind)
        return (dec, diff)

    def get_input(self, batch, k):
        x = batch[k]
        if len(x.shape) == 3:
            x = x[..., None]
        x = x.permute(0, 3, 1, 2).to(memory_format=torch.contiguous_format).float()
        if self.batch_resize_range is not None:
            lower_size = self.batch_resize_range[0]
            upper_size = self.batch_resize_range[1]
            if self.global_step <= 4:
                new_resize = upper_size
            else:
                new_resize = np.random.choice(np.arange(lower_size, upper_size + 16, 16))
            if new_resize != x.shape[2]:
                x = F.interpolate(x, size=new_resize, mode='bicubic')
            x = x.detach()
        return x

    def training_step(self, batch, batch_idx, optimizer_idx):
        x = self.get_input(batch, self.image_key)
        xrec, qloss, ind = self(x, return_pred_indices=True)
        if optimizer_idx == 0:
            aeloss, log_dict_ae = self.loss(qloss, x, xrec, optimizer_idx, self.global_step, last_layer=self.get_last_layer(), split='train', predicted_indices=ind)
            self.log_dict(log_dict_ae, prog_bar=False, logger=True, on_step=True, on_epoch=True)
            return aeloss
        if optimizer_idx == 1:
            discloss, log_dict_disc = self.loss(qloss, x, xrec, optimizer_idx, self.global_step, last_layer=self.get_last_layer(), split='train')
            self.log_dict(log_dict_disc, prog_bar=False, logger=True, on_step=True, on_epoch=True)
            return discloss

    def validation_step(self, batch, batch_idx):
        log_dict = self._validation_step(batch, batch_idx)
        with self.ema_scope():
            log_dict_ema = self._validation_step(batch, batch_idx, suffix='_ema')
        return log_dict

    def _validation_step(self, batch, batch_idx, suffix=''):
        x = self.get_input(batch, self.image_key)
        xrec, qloss, ind = self(x, return_pred_indices=True)
        aeloss, log_dict_ae = self.loss(qloss, x, xrec, 0, self.global_step, last_layer=self.get_last_layer(), split='val' + suffix, predicted_indices=ind)
        discloss, log_dict_disc = self.loss(qloss, x, xrec, 1, self.global_step, last_layer=self.get_last_layer(), split='val' + suffix, predicted_indices=ind)
        rec_loss = log_dict_ae[f'val{suffix}/rec_loss']
        self.log(f'val{suffix}/rec_loss', rec_loss, prog_bar=True, logger=True, on_step=False, on_epoch=True, sync_dist=True)
        self.log(f'val{suffix}/aeloss', aeloss, prog_bar=True, logger=True, on_step=False, on_epoch=True, sync_dist=True)
        if version.parse(pl.__version__) >= version.parse('1.4.0'):
            del log_dict_ae[f'val{suffix}/rec_loss']
        self.log_dict(log_dict_ae)
        self.log_dict(log_dict_disc)
        return self.log_dict

    def configure_optimizers(self):
        lr_d = self.learning_rate
        lr_g = self.lr_g_factor * self.learning_rate
        print('lr_d', lr_d)
        print('lr_g', lr_g)
        opt_ae = torch.optim.Adam(list(self.encoder.parameters()) + list(self.decoder.parameters()) + list(self.quantize.parameters()) + list(self.quant_conv.parameters()) + list(self.post_quant_conv.parameters()), lr=lr_g, betas=(0.5, 0.9))
        opt_disc = torch.optim.Adam(self.loss.discriminator.parameters(), lr=lr_d, betas=(0.5, 0.9))
        if self.scheduler_config is not None:
            scheduler = instantiate_from_config(self.scheduler_config)
            print('Setting up LambdaLR scheduler...')
            scheduler = [{'scheduler': LambdaLR(opt_ae, lr_lambda=scheduler.schedule), 'interval': 'step', 'frequency': 1}, {'scheduler': LambdaLR(opt_disc, lr_lambda=scheduler.schedule), 'interval': 'step', 'frequency': 1}]
            return ([opt_ae, opt_disc], scheduler)
        return ([opt_ae, opt_disc], [])

    def get_last_layer(self):
        return self.decoder.conv_out.weight

    def log_images(self, batch, only_inputs=False, plot_ema=False, **kwargs):
        log = dict()
        x = self.get_input(batch, self.image_key)
        x = x.to(self.device)
        if only_inputs:
            log['inputs'] = x
            return log
        xrec, _ = self(x)
        if x.shape[1] > 3:
            assert xrec.shape[1] > 3
            x = self.to_rgb(x)
            xrec = self.to_rgb(xrec)
        log['inputs'] = x
        log['reconstructions'] = xrec
        if plot_ema:
            with self.ema_scope():
                xrec_ema, _ = self(x)
                if x.shape[1] > 3:
                    xrec_ema = self.to_rgb(xrec_ema)
                log['reconstructions_ema'] = xrec_ema
        return log

    def to_rgb(self, x):
        assert self.image_key == 'segmentation'
        if not hasattr(self, 'colorize'):
            self.register_buffer('colorize', torch.randn(3, x.shape[1], 1, 1).to(x))
        x = F.conv2d(x, weight=self.colorize)
        x = 2.0 * (x - x.min()) / (x.max() - x.min()) - 1.0
        return x

def configure_optimizers(self):
    lr_d = self.learning_rate
    lr_g = self.lr_g_factor * self.learning_rate
    print('lr_d', lr_d)
    print('lr_g', lr_g)
    opt_ae = torch.optim.Adam(list(self.encoder.parameters()) + list(self.decoder.parameters()) + list(self.quantize.parameters()) + list(self.quant_conv.parameters()) + list(self.post_quant_conv.parameters()), lr=lr_g, betas=(0.5, 0.9))
    opt_disc = torch.optim.Adam(self.loss.discriminator.parameters(), lr=lr_d, betas=(0.5, 0.9))
    if self.scheduler_config is not None:
        scheduler = instantiate_from_config(self.scheduler_config)
        print('Setting up LambdaLR scheduler...')
        scheduler = [{'scheduler': LambdaLR(opt_ae, lr_lambda=scheduler.schedule), 'interval': 'step', 'frequency': 1}, {'scheduler': LambdaLR(opt_disc, lr_lambda=scheduler.schedule), 'interval': 'step', 'frequency': 1}]
        return ([opt_ae, opt_disc], scheduler)
    return ([opt_ae, opt_disc], [])

class NoisyLatentImageClassifier(pl.LightningModule):

    def __init__(self, diffusion_path, num_classes, ckpt_path=None, pool='attention', label_key=None, diffusion_ckpt_path=None, scheduler_config=None, weight_decay=0.01, log_steps=10, monitor='val/loss', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.num_classes = num_classes
        diffusion_config = natsorted(glob(os.path.join(diffusion_path, 'configs', '*-project.yaml')))[-1]
        self.diffusion_config = OmegaConf.load(diffusion_config).model
        self.diffusion_config.params.ckpt_path = diffusion_ckpt_path
        self.load_diffusion()
        self.monitor = monitor
        self.numd = self.diffusion_model.first_stage_model.encoder.num_resolutions - 1
        self.log_time_interval = self.diffusion_model.num_timesteps // log_steps
        self.log_steps = log_steps
        self.label_key = label_key if not hasattr(self.diffusion_model, 'cond_stage_key') else self.diffusion_model.cond_stage_key
        assert self.label_key is not None, 'label_key neither in diffusion model nor in model.params'
        if self.label_key not in __models__:
            raise NotImplementedError()
        self.load_classifier(ckpt_path, pool)
        self.scheduler_config = scheduler_config
        self.use_scheduler = self.scheduler_config is not None
        self.weight_decay = weight_decay

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

    def load_diffusion(self):
        model = instantiate_from_config(self.diffusion_config)
        self.diffusion_model = model.eval()
        self.diffusion_model.train = disabled_train
        for param in self.diffusion_model.parameters():
            param.requires_grad = False

    def load_classifier(self, ckpt_path, pool):
        model_config = deepcopy(self.diffusion_config.params.unet_config.params)
        model_config.in_channels = self.diffusion_config.params.unet_config.params.out_channels
        model_config.out_channels = self.num_classes
        if self.label_key == 'class_label':
            model_config.pool = pool
        self.model = __models__[self.label_key](**model_config)
        if ckpt_path is not None:
            print('#####################################################################')
            print(f'load from ckpt "{ckpt_path}"')
            print('#####################################################################')
            self.init_from_ckpt(ckpt_path)

    @torch.no_grad()
    def get_x_noisy(self, x, t, noise=None):
        noise = default(noise, lambda: torch.randn_like(x))
        continuous_sqrt_alpha_cumprod = None
        if self.diffusion_model.use_continuous_noise:
            continuous_sqrt_alpha_cumprod = self.diffusion_model.sample_continuous_noise_level(x.shape[0], t + 1)
        return self.diffusion_model.q_sample(x_start=x, t=t, noise=noise, continuous_sqrt_alpha_cumprod=continuous_sqrt_alpha_cumprod)

    def forward(self, x_noisy, t, *args, **kwargs):
        return self.model(x_noisy, t)

    @torch.no_grad()
    def get_input(self, batch, k):
        x = batch[k]
        if len(x.shape) == 3:
            x = x[..., None]
        x = rearrange(x, 'b h w c -> b c h w')
        x = x.to(memory_format=torch.contiguous_format).float()
        return x

    @torch.no_grad()
    def get_conditioning(self, batch, k=None):
        if k is None:
            k = self.label_key
        assert k is not None, 'Needs to provide label key'
        targets = batch[k].to(self.device)
        if self.label_key == 'segmentation':
            targets = rearrange(targets, 'b h w c -> b c h w')
            for down in range(self.numd):
                h, w = targets.shape[-2:]
                targets = F.interpolate(targets, size=(h // 2, w // 2), mode='nearest')
        return targets

    def compute_top_k(self, logits, labels, k, reduction='mean'):
        _, top_ks = torch.topk(logits, k, dim=1)
        if reduction == 'mean':
            return (top_ks == labels[:, None]).float().sum(dim=-1).mean().item()
        elif reduction == 'none':
            return (top_ks == labels[:, None]).float().sum(dim=-1)

    def on_train_epoch_start(self):
        self.diffusion_model.model.to('cpu')

    @torch.no_grad()
    def write_logs(self, loss, logits, targets):
        log_prefix = 'train' if self.training else 'val'
        log = {}
        log[f'{log_prefix}/loss'] = loss.mean()
        log[f'{log_prefix}/acc@1'] = self.compute_top_k(logits, targets, k=1, reduction='mean')
        log[f'{log_prefix}/acc@5'] = self.compute_top_k(logits, targets, k=5, reduction='mean')
        self.log_dict(log, prog_bar=False, logger=True, on_step=self.training, on_epoch=True)
        self.log('loss', log[f'{log_prefix}/loss'], prog_bar=True, logger=False)
        self.log('global_step', self.global_step, logger=False, on_epoch=False, prog_bar=True)
        lr = self.optimizers().param_groups[0]['lr']
        self.log('lr_abs', lr, on_step=True, logger=True, on_epoch=False, prog_bar=True)

    def shared_step(self, batch, t=None):
        x, *_ = self.diffusion_model.get_input(batch, k=self.diffusion_model.first_stage_key)
        targets = self.get_conditioning(batch)
        if targets.dim() == 4:
            targets = targets.argmax(dim=1)
        if t is None:
            t = torch.randint(0, self.diffusion_model.num_timesteps, (x.shape[0],), device=self.device).long()
        else:
            t = torch.full(size=(x.shape[0],), fill_value=t, device=self.device).long()
        x_noisy = self.get_x_noisy(x, t)
        logits = self(x_noisy, t)
        loss = F.cross_entropy(logits, targets, reduction='none')
        self.write_logs(loss.detach(), logits.detach(), targets.detach())
        loss = loss.mean()
        return (loss, logits, x_noisy, targets)

    def training_step(self, batch, batch_idx):
        loss, *_ = self.shared_step(batch)
        return loss

    def reset_noise_accs(self):
        self.noisy_acc = {t: {'acc@1': [], 'acc@5': []} for t in range(0, self.diffusion_model.num_timesteps, self.diffusion_model.log_every_t)}

    def on_validation_start(self):
        self.reset_noise_accs()

    @torch.no_grad()
    def validation_step(self, batch, batch_idx):
        loss, *_ = self.shared_step(batch)
        for t in self.noisy_acc:
            _, logits, _, targets = self.shared_step(batch, t)
            self.noisy_acc[t]['acc@1'].append(self.compute_top_k(logits, targets, k=1, reduction='mean'))
            self.noisy_acc[t]['acc@5'].append(self.compute_top_k(logits, targets, k=5, reduction='mean'))
        return loss

    def configure_optimizers(self):
        optimizer = AdamW(self.model.parameters(), lr=self.learning_rate, weight_decay=self.weight_decay)
        if self.use_scheduler:
            scheduler = instantiate_from_config(self.scheduler_config)
            print('Setting up LambdaLR scheduler...')
            scheduler = [{'scheduler': LambdaLR(optimizer, lr_lambda=scheduler.schedule), 'interval': 'step', 'frequency': 1}]
            return ([optimizer], scheduler)
        return optimizer

    @torch.no_grad()
    def log_images(self, batch, N=8, *args, **kwargs):
        log = dict()
        x = self.get_input(batch, self.diffusion_model.first_stage_key)
        log['inputs'] = x
        y = self.get_conditioning(batch)
        if self.label_key == 'class_label':
            y = log_txt_as_img((x.shape[2], x.shape[3]), batch['human_label'])
            log['labels'] = y
        if ismap(y):
            log['labels'] = self.diffusion_model.to_rgb(y)
            for step in range(self.log_steps):
                current_time = step * self.log_time_interval
                _, logits, x_noisy, _ = self.shared_step(batch, t=current_time)
                log[f'inputs@t{current_time}'] = x_noisy
                pred = F.one_hot(logits.argmax(dim=1), num_classes=self.num_classes)
                pred = rearrange(pred, 'b h w c -> b c h w')
                log[f'pred@t{current_time}'] = self.diffusion_model.to_rgb(pred)
        for key in log:
            log[key] = log[key][:N]
        return log

def load_diffusion(self):
    model = instantiate_from_config(self.diffusion_config)
    self.diffusion_model = model.eval()
    self.diffusion_model.train = disabled_train
    for param in self.diffusion_model.parameters():
        param.requires_grad = False

def forward(self, x_noisy, t, *args, **kwargs):
    return self.model(x_noisy, t)

def configure_optimizers(self):
    optimizer = AdamW(self.model.parameters(), lr=self.learning_rate, weight_decay=self.weight_decay)
    if self.use_scheduler:
        scheduler = instantiate_from_config(self.scheduler_config)
        print('Setting up LambdaLR scheduler...')
        scheduler = [{'scheduler': LambdaLR(optimizer, lr_lambda=scheduler.schedule), 'interval': 'step', 'frequency': 1}]
        return ([optimizer], scheduler)
    return optimizer

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

def configure_optimizers(self):
    lr = self.learning_rate
    params = list(self.model.parameters())
    if self.learn_logvar:
        params = params + [self.logvar]
    opt = torch.optim.AdamW(params, lr=lr)
    return opt

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

class DeletionAgent:

    def __init__(self, config):
        self.config = config
        self.inpaint_dir = config['inpaint_dir']
        self.video_inpaint_dir = config['video_inpaint_dir']

    def llm_finding_deletion(self, scene, message, scene_object_description):
        try:
            q0 = 'I will provide you with an operation statement and a dictionary containing information about cars in a scene. ' + ' You need to determine which car or cars should be deleted from the dictionary. '
            q1 = 'The dictionary is ' + str(scene_object_description)
            q2 = 'The keys of the dictionary are the car IDs, and the value is also a dictionary containing car detail, ' + 'including its image coordinate (u,v) in an image frame, depth, color in RGB.'
            q2 = "My statement may include information about the car's color or position. You should find out from my statement which cars should be deleted and return their car IDs"
            q3 = 'Note: (1) The definitions of u and v conform to the image coordinate system, u=0, v=0 represents the upper left corner. ' + "And the larger the 'u', the more to the right; And the larger the 'v', the more to the down. " + "(2) You can judge the distance by the 'depth'. The greater the depth, the farther the distance, the smaller the depth, the closer the distance." + '(3) The description of the color may not be absolutely accurate, choose the car with the closest color.'
            q4 = "You should return a JSON dictionary, with a key: 'removed_cars'." + " 'removed_cars' contains IDs of all the cars that meet the requirements. "
            q5 = 'Note that there is no need to return any code or explanations; only provide a JSON dictionary.'
            q6 = "If the dictionary is empty, 'removed_cars' should be an empty list "
            q7 = 'The requirement is :' + message
            prompt_list = [q0, q1, q2, q3, q4, q5, q6, q7]
            result = openai.ChatCompletion.create(model='gpt-4', messages=[{'role': 'system', 'content': 'You are an assistant helping me to assess and maintain information in a dictionary.'}] + [{'role': 'user', 'content': q} for q in prompt_list])
            answer = result['choices'][0]['message']['content']
            print(f'{colored('[Deletion Agent LLM] finding the car to delete', color='magenta', attrs=['bold'])}                     \n{colored('[Raw Response>>>]', attrs=['bold'])} {answer}')
            start = answer.index('{')
            answer = answer[start:]
            end = answer.rfind('}')
            answer = answer[:end + 1]
            deletion_car_ids = eval(answer)['removed_cars']
            print(f'{colored('[Extracted Response>>>]', attrs=['bold'])} {deletion_car_ids} \n')
        except Exception as e:
            print(e)
            traceback.print_exc()
            print('[Deletion Agent LLM] finding the car to delete fails')
            return []
        return deletion_car_ids

    def llm_putting_back_deletion(self, scene, message, scene_object_description):
        try:
            deleted_object_dict = {k: v for k, v in scene_object_description.items() if k in scene.removed_cars}
            q0 = 'I will provide you with a dictionary in which each key is a vehicle id, and each value is the description of the vehicle in the image.'
            q1 = "Specifically, description of the vehicle is also a dictionary. It has keys: (1) vehicle's u in image coordinate (2) vehicle's v in image coordinate (3) vehicle color in RGB. (4) vehicle's depth from viewpoint"
            q2 = 'The definitions of u and v conform to the image coordinate system, u=0, v=0 represents the upper left corner. ' + "The larger the 'u', the more to the right; And the larger the 'v', the more to the down. "
            q3 = 'I will get you a requirement, and I want you can follow this requirement and take out all the relavant vehicle ids from the dictionary.'
            q4 = f'Now the dictionary is {deleted_object_dict}, and my requirement is {message}. My requirement may contain extraneous verb descriptions or the wrong singular and plural expression, please ignore.'
            q5 = "Note that you should return a JSON dictionary, the key is 'selected_vehicle', the value includes the vehicle ids. DO NOT return anything else. I'm not asking you to write code."
            prompt_list = [q0, q1, q2, q3, q4, q5]
            result = openai.ChatCompletion.create(model='gpt-4', messages=[{'role': 'system', 'content': 'You are an assistant helping me maintain and return dictionaries.'}] + [{'role': 'user', 'content': q} for q in prompt_list])
            answer = result['choices'][0]['message']['content']
            print(f'{colored('[Deletion Agent LLM] finding the car to be put back', color='magenta', attrs=['bold'])}                      \n{colored('[Raw Response>>>]', attrs=['bold'])} {answer}')
            start = answer.index('{')
            answer = answer[start:]
            end = answer.rfind('}')
            answer = answer[:end + 1]
            put_back_car_ids = eval(answer)['selected_vehicle']
            print(f'{colored('[Extracted Response>>>]', attrs=['bold'])} {put_back_car_ids} \n')
        except Exception as e:
            print(e)
            traceback.print_exc()
            print('[Deletion Agent LLM] finding the car to be put back fails')
        return put_back_car_ids

    def func_inpaint_scene(self, scene):
        """
        Call inpainting, store results in scene.current_inpainted_images

        if no scene.removed_cars
            just return

        """
        if len(scene.removed_cars) == 0:
            print(f'{colored('[Inpaint]', 'green', attrs=['bold'])} No inpainting.')
            scene.current_inpainted_images = scene.current_images
            return
        current_dir = os.getcwd()
        inpaint_input_path = os.path.join(current_dir, scene.cache_dir, 'inpaint_input')
        inpaint_output_path = os.path.join(current_dir, scene.cache_dir, 'inpaint_output')
        check_and_mkdirs(inpaint_input_path)
        check_and_mkdirs(inpaint_output_path)
        if scene.is_ego_motion is False:
            print(f'{colored('[Inpaint]', 'green', attrs=['bold'])} is_ego_motion is False, inpainting one frame.')
            all_mask = self.func_get_mask(scene)
            img = scene.current_images[0]
            masked_img = copy.deepcopy(img)
            if scene.is_wide_angle:
                masked_img = cv2.resize(masked_img, (1152, 256))
            else:
                masked_img = cv2.resize(masked_img, (512, 384))
            imageio.imwrite(os.path.join(inpaint_input_path, 'img.png'), masked_img.astype(np.uint8))
            imageio.imwrite(os.path.join(inpaint_input_path, 'img_mask.png'), all_mask.astype(np.uint8))
            current_dir = os.getcwd()
            os.chdir(self.inpaint_dir)
            os.system(f'python scripts/inpaint.py --indir {inpaint_input_path} --outdir {inpaint_output_path}')
            os.chdir(current_dir)
            new_img = imageio.imread(os.path.join(inpaint_output_path, 'img.png'))
            new_img = cv2.resize(new_img, (scene.width, scene.height))
            all_mask_in_ori_resolution = cv2.resize(all_mask, (scene.width, scene.height)).reshape(scene.height, scene.width, 1).repeat(3, axis=2)
            new_img = np.where(all_mask_in_ori_resolution == 0, scene.current_images[0], new_img)
            scene.current_inpainted_images = [new_img] * scene.frames
        else:
            print(f'{colored('[Inpaint]', 'green', attrs=['bold'])} is_ego_motion is True, inpainting multiple frame (as video).')
            mask_list = []
            for i in range(scene.frames):
                current_frame_mask = np.zeros((scene.height, scene.width))
                for car_id in scene.bbox_data.keys():
                    if scene.bbox_car_id_to_name[car_id] in scene.removed_cars:
                        corners = generate_vertices(scene.bbox_data[car_id])
                        mask, mask_corners = get_outlines(corners, transform_nerf2opencv_convention(scene.current_extrinsics[i]), scene.intrinsics, scene.height, scene.width)
                        current_frame_mask[mask == 1] = 1
                mask_list.append(current_frame_mask)
            np.save(f'{self.video_inpaint_dir}/chatsim/masks.npy', mask_list)
            np.save(f'{self.video_inpaint_dir}/chatsim/current_images.npy', scene.current_images)
            current_dir = os.getcwd()
            os.chdir(self.video_inpaint_dir)
            os.system(f'python remove_anything_video_npy.py                         --dilate_kernel_size 15                         --lama_config lama/configs/prediction/default.yaml                         --lama_ckpt ./pretrained_models/big-lama                         --tracker_ckpt vitb_384_mae_ce_32x4_ep300                         --vi_ckpt ./pretrained_models/sttn.pth                         --mask_idx 2                         --fps 25')
            os.chdir(current_dir)
            print(f'{colored('[Inpaint]', 'green', attrs=['bold'])} Video Inpainting Done!')
            inpainted_images = np.load(f'{self.video_inpaint_dir}/chatsim/inpainted_imgs.npy', allow_pickle=True)
            scene.current_inpainted_images = [np.array(image) for image in inpainted_images]

    def func_get_mask(self, scene):
        masks = []
        extrinsic_for_project = transform_nerf2opencv_convention(scene.current_extrinsics[0])
        for car_name in scene.removed_cars:
            car_id = scene.name_to_bbox_car_id[car_name]
            corners = generate_vertices(scene.bbox_data[car_id])
            mask, _ = get_outlines(corners, extrinsic_for_project, scene.intrinsics, scene.height, scene.width)
            mask *= 255
            masks.append(mask)
        mask = np.max(np.stack(masks), axis=0)
        if scene.is_wide_angle:
            mask = cv2.resize(mask, (1152, 256))
        else:
            mask = cv2.resize(mask, (512, 384))
        return mask

def llm_finding_deletion(self, scene, message, scene_object_description):
    try:
        q0 = 'I will provide you with an operation statement and a dictionary containing information about cars in a scene. ' + ' You need to determine which car or cars should be deleted from the dictionary. '
        q1 = 'The dictionary is ' + str(scene_object_description)
        q2 = 'The keys of the dictionary are the car IDs, and the value is also a dictionary containing car detail, ' + 'including its image coordinate (u,v) in an image frame, depth, color in RGB.'
        q2 = "My statement may include information about the car's color or position. You should find out from my statement which cars should be deleted and return their car IDs"
        q3 = 'Note: (1) The definitions of u and v conform to the image coordinate system, u=0, v=0 represents the upper left corner. ' + "And the larger the 'u', the more to the right; And the larger the 'v', the more to the down. " + "(2) You can judge the distance by the 'depth'. The greater the depth, the farther the distance, the smaller the depth, the closer the distance." + '(3) The description of the color may not be absolutely accurate, choose the car with the closest color.'
        q4 = "You should return a JSON dictionary, with a key: 'removed_cars'." + " 'removed_cars' contains IDs of all the cars that meet the requirements. "
        q5 = 'Note that there is no need to return any code or explanations; only provide a JSON dictionary.'
        q6 = "If the dictionary is empty, 'removed_cars' should be an empty list "
        q7 = 'The requirement is :' + message
        prompt_list = [q0, q1, q2, q3, q4, q5, q6, q7]
        result = openai.ChatCompletion.create(model='gpt-4', messages=[{'role': 'system', 'content': 'You are an assistant helping me to assess and maintain information in a dictionary.'}] + [{'role': 'user', 'content': q} for q in prompt_list])
        answer = result['choices'][0]['message']['content']
        print(f'{colored('[Deletion Agent LLM] finding the car to delete', color='magenta', attrs=['bold'])}                     \n{colored('[Raw Response>>>]', attrs=['bold'])} {answer}')
        start = answer.index('{')
        answer = answer[start:]
        end = answer.rfind('}')
        answer = answer[:end + 1]
        deletion_car_ids = eval(answer)['removed_cars']
        print(f'{colored('[Extracted Response>>>]', attrs=['bold'])} {deletion_car_ids} \n')
    except Exception as e:
        print(e)
        traceback.print_exc()
        print('[Deletion Agent LLM] finding the car to delete fails')
        return []
    return deletion_car_ids

def llm_putting_back_deletion(self, scene, message, scene_object_description):
    try:
        deleted_object_dict = {k: v for k, v in scene_object_description.items() if k in scene.removed_cars}
        q0 = 'I will provide you with a dictionary in which each key is a vehicle id, and each value is the description of the vehicle in the image.'
        q1 = "Specifically, description of the vehicle is also a dictionary. It has keys: (1) vehicle's u in image coordinate (2) vehicle's v in image coordinate (3) vehicle color in RGB. (4) vehicle's depth from viewpoint"
        q2 = 'The definitions of u and v conform to the image coordinate system, u=0, v=0 represents the upper left corner. ' + "The larger the 'u', the more to the right; And the larger the 'v', the more to the down. "
        q3 = 'I will get you a requirement, and I want you can follow this requirement and take out all the relavant vehicle ids from the dictionary.'
        q4 = f'Now the dictionary is {deleted_object_dict}, and my requirement is {message}. My requirement may contain extraneous verb descriptions or the wrong singular and plural expression, please ignore.'
        q5 = "Note that you should return a JSON dictionary, the key is 'selected_vehicle', the value includes the vehicle ids. DO NOT return anything else. I'm not asking you to write code."
        prompt_list = [q0, q1, q2, q3, q4, q5]
        result = openai.ChatCompletion.create(model='gpt-4', messages=[{'role': 'system', 'content': 'You are an assistant helping me maintain and return dictionaries.'}] + [{'role': 'user', 'content': q} for q in prompt_list])
        answer = result['choices'][0]['message']['content']
        print(f'{colored('[Deletion Agent LLM] finding the car to be put back', color='magenta', attrs=['bold'])}                      \n{colored('[Raw Response>>>]', attrs=['bold'])} {answer}')
        start = answer.index('{')
        answer = answer[start:]
        end = answer.rfind('}')
        answer = answer[:end + 1]
        put_back_car_ids = eval(answer)['selected_vehicle']
        print(f'{colored('[Extracted Response>>>]', attrs=['bold'])} {put_back_car_ids} \n')
    except Exception as e:
        print(e)
        traceback.print_exc()
        print('[Deletion Agent LLM] finding the car to be put back fails')
    return put_back_car_ids

class MotionAgent:

    def __init__(self, config):
        self.config = config
        self.motion_tracking = config.get('motion_tracking', False)

    def llm_reasoning_dependency(self, scene, message):
        """ LLM reasoning of Motion Agent, determine if the vehicle placement is depend on scene elements.
        Input:
            scene : Scene
                scene object.
            message : str
                language prompt to ChatSim.
        """
        try:
            q0 = 'I will provide an operation statement to add a vehicle, and you need to determine whether the position of the added car has any spatial dependency with other cars in my statement'
            q1 = "Only return a JSON format dictionary as your response, which contains a key 'dependency'. If the added car's position depends on other objects, set it to 1; otherwise, set it to 0."
            q2 = "An Example: Given statement 'add an Audi in the back which drives ahead', you should return {'dependency': 0}. This is because I only mention the added Audi."
            q3 = "An Example: Given statement 'add a Porsche at 2m to the right of the red Audi.', you should return {'dependency': 1}. This is because Porsche's position depends on Audi."
            q4 = "An Example: Given statement 'add a car in front of me.', you should return {'dependency': 0}. This is because 'me' is not other car in the scene."
            q5 = 'The statement is:' + message
            prompt_list = [q0, q1, q2, q3, q4, q5]
            result = openai.ChatCompletion.create(model='gpt-4', messages=[{'role': 'system', 'content': 'You are an assistant helping me to extract information from the operations.'}] + [{'role': 'user', 'content': q} for q in prompt_list])
            answer = result['choices'][0]['message']['content']
            print(f'{colored('[Motion Agent LLM] analyzing insertion scene dependency ', color='magenta', attrs=['bold'])}                     \n{colored('[Raw Response>>>]', attrs=['bold'])} {answer}')
            start = answer.index('{')
            answer = answer[start:]
            end = answer.rfind('}')
            answer = answer[:end + 1]
            placement_mode = eval(answer)
            print(f'{colored('[Extracted Response>>>]', attrs=['bold'])} {placement_mode} \n')
        except Exception as e:
            print(e)
            traceback.print_exc()
            return '[Motion Agent LLM] reasoning object dependency fails.'
        return placement_mode

    def llm_placement_wo_dependency(self, scene, message):
        try:
            q0 = 'I will provide you with an operation statement to add and place a vehicle, and I need you to extract 3 specific placement information from the statement, including: '
            q1 = " (1) 'mode', one of ['front', 'left front', 'left', 'right front', 'right', 'random'], representing approximate initial positions of the vehicle. If not specified, it defaults to 'random'."
            q2 = " (2) 'distance_constraint' indicates whether there's a constraint on the distance of the added vehicle. 0 means no constraint, 1 means there is a constraint." + " If there's no relevant information mentioned, it defaults to 0."
            q3 = " (3) 'distance_min_max' represents the range of constraints when 'distance_constraint' applicable. It should be a tuple in the format (min, max), for example, (9, 11) means the minimum distance is 9, and the maximum is 11." + " When there's 'distance_constraint' is 0, the default value is (4, 45). If distance is specified as a specific value 'x', 'distance_min_max' is (x, x+5)"
            q4 = "Just return the json dict with keys:'mode', 'distance_constraint', 'distance_min_max'. Do not return any code or discription."
            q5 = "An Example: Given operation statement: 'Add an Audi 7-10 meters ahead', you should return " + "{'mode':'front', 'distance_constraint': 1, 'distance_min_max':(7,10)}"
            q6 = "An Example: Given operation statement: 'Add an Porsche in the right front.', you should return " + "{'mode':'right front', 'distance_constraint': 0, 'distance_min_max':(4, 45)}"
            q7 = 'Note that you should not return any code or explanations, only provide a JSON dictionary.'
            q8 = 'The operation statement:' + message
            prompt_list = [q0, q1, q2, q3, q4, q5, q6, q7, q8]
            result = openai.ChatCompletion.create(model='gpt-4', messages=[{'role': 'system', 'content': 'You are an assistant helping me to determine how to place a car.'}] + [{'role': 'user', 'content': q} for q in prompt_list])
            answer = result['choices'][0]['message']['content']
            print(f'{colored('[Motion Agent LLM] deciding scene-independent object placement', color='magenta', attrs=['bold'])}                     \n{colored('[Raw Response>>>]', attrs=['bold'])} {answer}')
            start = answer.index('{')
            answer = answer[start:]
            end = answer.rfind('}')
            answer = answer[:end + 1]
            placement_prior = eval(answer)
            print(f'{colored('[Extracted Response>>>]', attrs=['bold'])} {placement_prior} \n')
        except Exception as e:
            print(e)
            traceback.print_exc()
            return '[Motion Agent LLM] deciding placement fails.'
        return placement_prior

    def llm_placement_w_dependency(self, scene, message, scene_object_description):
        try:
            q0 = 'I will provide you with an operation statement to add and place a vehicle, as well as information of other cars in the scene.'
            q1 = 'I need you to determine a specific position (x, y) for placement of the added car in my statement. '
            q2 = 'Information of other cars in the scene is a two-level dictionary, with the first level representing the different car id in the scene, ' + 'and the second level containing various information about that car, including the (x, y) of its world 3D coordinate, ' + 'its image coordinate (u, v) in an image frame, depth, and rgb color representation.'
            q3 = 'The dictionary is' + str(scene_object_description)
            q4 = 'I will also further inform you about the operations that have been previously performed on this scene. ' + 'You can use these past operations, along with the dictionary I provide, to generate the final position.'
            q5 = 'The previously performed operation is : ' + str(scene.past_operations)
            q6 = "If the car with key 'direction', and direction is close, 'behind' means keep the same 'y' and increase 'x' 10 meters. If direction is away, 'behind' means keep the same 'y' and decrease 'x' 10 meters." + "If the car with key 'direction', and direction is close, 'front' means keep the same 'y' and decrease 'x' 10 meters. If direction is away, 'front' means keep the same 'y' and increase 'x' 10 meters."
            q7 = "'left' means keep the same 'x' and increase 'y' 5m, 'right' means keep the same 'x' and decrease 'y' 5m."
            q8 = "You should return a placemenet positon in JSON dictionary with 2 keys: 'x', 'y'. Do not provide any code or explanations, only return the final JSON dictionary."
            q9 = 'The requirement is:' + message
            prompt_list = [q0, q1, q2, q3, q4, q5, q6, q7, q8, q9]
            result = openai.ChatCompletion.create(model='gpt-4', messages=[{'role': 'system', 'content': 'You are an assistant helping me to determine how to place a car.'}] + [{'role': 'user', 'content': q} for q in prompt_list])
            answer = result['choices'][0]['message']['content']
            print(f'{colored('[Motion Agent LLM] deciding scene-dependent object placement', color='magenta', attrs=['bold'])}                     \n{colored('[Raw Response>>>]', attrs=['bold'])} {answer}')
            start = answer.index('{')
            answer = answer[start:]
            end = answer.rfind('}')
            answer = answer[:end + 1]
            placement_prior = eval(answer)
            print(f'{colored('[Extracted Response>>>]', attrs=['bold'])} {placement_prior} \n')
        except Exception as e:
            print(e)
            traceback.print_exc()
            return '[Motion Agent LLM] deciding placement fails.'
        return placement_prior

    def llm_motion_planning(self, scene, message):
        try:
            q0 = 'I will provide you with an operation statement to add and place a vehicle, and I need you to determine the its motion situation from my statement, including: '
            q1 = "(1) 'action', one of ['static', 'random', 'straight', 'turn left', 'turn right']. If action not mentioned in the statement, it defaults to 'straight'." + "For example, the statement is 'add a black car in front of me', then the action is 'straight'."
            q2 = "(2) 'speed', the approximate speed of the vehicle, one of ['random', 'fast', 'slow']. If speed is not mentioned in the statement, it defaults to 'slow'."
            q3 = "(3) 'direction', one of ['away', 'close', 'random']. 'away' represents the direction away from oneself, and 'close' represents the direction toward oneself." + "For example, moving forward is 'away' from oneself, while moving towards oneself is 'close'. If direction is not mentioned in the statement, just return 'random'."
            q4 = "(4) 'wrong_way', if the vehicle drives in the wrong way, one of ['true'. 'false']. If the information is not mentioned in the statement, it defaults to 'false'."
            q4 = "An Example: Given the statement 'add a Tesla that is racing straight ahead in the right front of the scene', you should return {'action': 'straight', 'speed': 'fast', 'direction': 'away', 'wrong_way': 'false'}"
            q5 = "An Example: Given the statement 'add a yellow Audi in front of the scene', you should return {'action': 'static', 'speed': 'random', 'direction': 'away', 'wrong_way': 'false'}"
            q6 = "An Example: Given the statement 'add a Tesla coming from the front and driving in the wrong way', you should return {'action': 'straight', 'speed': 'random', 'direction': 'close', 'wrong_way': 'true'}"
            q7 = 'Note that there is no need to return any code or explanations; only provide a JSON dictionary. Do not include any additional statements.'
            q8 = 'The operation statement is:' + message
            prompt_list = [q0, q1, q2, q3, q4, q5, q6, q7, q8]
            result = openai.ChatCompletion.create(model='gpt-4', messages=[{'role': 'system', 'content': 'You are an assistant helping me to assess the motion situation for adding vehicles.'}] + [{'role': 'user', 'content': q} for q in prompt_list])
            answer = result['choices'][0]['message']['content']
            print(f'{colored('[Motion Agent LLM] finding motion prior', color='magenta', attrs=['bold'])}                     \n{colored('[Raw Response>>>]', attrs=['bold'])} {answer}')
            start = answer.index('{')
            answer = answer[start:]
            end = answer.rfind('}')
            answer = answer[:end + 1]
            motion_prior = eval(answer)
            if not motion_prior.get('wrong_way'):
                motion_prior['wrong_way'] = False
            print(f'{colored('[Extracted Response>>>]', attrs=['bold'])} {motion_prior} \n')
        except Exception as e:
            print(e)
            traceback.print_exc()
            return '[Motion Agent LLM] finding motion prior fails.'
        return motion_prior

    def func_placement_and_motion_single_vehicle(self, scene, added_car_name):
        added_car_id = added_car_name.lstrip('added_car_')
        transformed_map_data_ = transform_node_to_lane(scene.map_data)
        all_current_vertices_coord = scene.all_current_vertices_coord
        for added_traj in scene.all_trajectories:
            all_current_vertices_coord = np.vstack([all_current_vertices_coord, added_traj[0:1, 0:2]])
        one_added_car = scene.added_cars_dict[added_car_name]
        if one_added_car['need_placement_and_motion'] is True:
            scene.added_cars_dict[added_car_name]['need_placement_and_motion'] = False
            one_added_car = scene.added_cars_dict[added_car_name]
            transformed_map_data = deepcopy(transformed_map_data_)
            if one_added_car['wrong_way'] is True:
                transformed_map_data['centerline'][:, -1] = (transformed_map_data['centerline'][:, -1] + 1) % 2
                transformed_map_data['centerline'] = np.concatenate((transformed_map_data['centerline'][:, 2:4], transformed_map_data['centerline'][:, 0:2], transformed_map_data['centerline'][:, 4:]), axis=1)
                transformed_map_data['centerline'] = np.flip(transformed_map_data['centerline'], axis=0)
            if one_added_car.get('x') is None:
                placement_result = vehicle_placement(transformed_map_data, all_current_vertices_coord, one_added_car['direction'] if one_added_car['direction'] != 'random' else random.choice(['away', 'close']), one_added_car['mode'], one_added_car['distance_constraint'], one_added_car['distance_min_max'], 'default')
            else:
                placement_result = vehicle_placement_specific(transformed_map_data, all_current_vertices_coord, np.array([one_added_car['x'], one_added_car['y']]))
            if placement_result[0] is None:
                del scene.added_cars_dict[added_car_name]
                return
            one_added_car['placement_result'] = placement_result
            try:
                motion_result = vehicle_motion(transformed_map_data, scene.all_current_vertices[:, ::2, :2] if scene.all_current_vertices.shape[0] != 0 else scene.all_current_vertices, placement_result=one_added_car['placement_result'], high_level_action_direction=one_added_car['action'], high_level_action_speed=one_added_car['speed'], dt=1 / scene.fps, total_len=scene.frames)
            except ValueError as e:
                print(f'{colored('[Motion Agent] Error: Potentially no feasible destination can be found.', color='red', attrs=['bold'])} {e}')
                raise ValueError('No feasible destination can be found.')
            if motion_result[0] is None:
                del scene.added_cars_dict[added_car_name]
                return
            one_added_car['motion'] = motion_result
            scene.added_cars_dict[added_car_name] = one_added_car
            all_trajectories = []
            for one_car_name in scene.added_cars_dict.keys():
                all_trajectories.append(scene.added_cars_dict[one_car_name]['motion'][:, :2])
            all_trajectories_after_check_collision = check_collision_and_revise_dynamic(all_trajectories)
            all_trajectories_after_check_collision = all_trajectories
            scene.all_trajectories = all_trajectories_after_check_collision
            for idx, one_car_name in enumerate(scene.added_cars_dict.keys()):
                motion_result = all_trajectories_after_check_collision[idx]
                placement_result = scene.added_cars_dict[one_car_name]['placement_result']
                direction = np.zeros((motion_result.shape[0], 1))
                angle = np.arctan2(placement_result[-1] - placement_result[-3], placement_result[-2] - placement_result[-4])
                for i in range(motion_result.shape[0] - 1):
                    if motion_result[i, 0] == motion_result[i + 1, 0] and motion_result[i, 1] == motion_result[i + 1, 1]:
                        direction[i, 0] = angle
                    else:
                        direction[i, 0] = np.arctan2(motion_result[i + 1, 1] - motion_result[i, 1], motion_result[i + 1, 0] - motion_result[i, 0])
                direction[-1, 0] = direction[-2, 0]
                motion_result = np.concatenate((motion_result, direction), axis=1)
                if self.motion_tracking:
                    try:
                        from simulator import TrajectoryTracker
                    except ModuleNotFoundError:
                        error_msg1 = f'{colored('[ERROR]', color='red', attrs=['bold'])} Trajectory Tracking Module is not installed.\n'
                        error_msg2 = "\nYou can 1) Install Installation README's Step 5: Setup Trajectory Tracking Module"
                        error_msg3 = "\n     Or 2) set ['motion_agent']['motion_tracking'] to False in config.\n"
                        raise ModuleNotFoundError(error_msg1 + error_msg2 + error_msg3)
                    reference_line = interpolate_uniformly(motion_result, int(scene.frames * scene.fps / 10))
                    reference_line = [(reference_line[i, 0], reference_line[i, 1]) for i in range(reference_line.shape[0])]
                    init_state = (motion_result[0, 0], motion_result[0, 1], motion_result[0, 2], np.linalg.norm(np.array(reference_line[1]) - np.array(reference_line[0])) * 10)
                    pretrained_checkpoint_dir = './chatsim/foreground/drl-based-trajectory-tracking/submodules/drltt-assets/checkpoints/track/checkpoint'
                    trajectory_tracker = TrajectoryTracker(checkpoint_dir=pretrained_checkpoint_dir)
                    states, actions = trajectory_tracker.track_reference_line(reference_line=reference_line, init_state=init_state)
                    motion_result = np.stack(states)[:, :-1]
                    motion_result = interpolate_uniformly(motion_result, scene.frames)
                scene.added_cars_dict[one_car_name]['motion'] = motion_result

def llm_reasoning_dependency(self, scene, message):
    """ LLM reasoning of Motion Agent, determine if the vehicle placement is depend on scene elements.
        Input:
            scene : Scene
                scene object.
            message : str
                language prompt to ChatSim.
        """
    try:
        q0 = 'I will provide an operation statement to add a vehicle, and you need to determine whether the position of the added car has any spatial dependency with other cars in my statement'
        q1 = "Only return a JSON format dictionary as your response, which contains a key 'dependency'. If the added car's position depends on other objects, set it to 1; otherwise, set it to 0."
        q2 = "An Example: Given statement 'add an Audi in the back which drives ahead', you should return {'dependency': 0}. This is because I only mention the added Audi."
        q3 = "An Example: Given statement 'add a Porsche at 2m to the right of the red Audi.', you should return {'dependency': 1}. This is because Porsche's position depends on Audi."
        q4 = "An Example: Given statement 'add a car in front of me.', you should return {'dependency': 0}. This is because 'me' is not other car in the scene."
        q5 = 'The statement is:' + message
        prompt_list = [q0, q1, q2, q3, q4, q5]
        result = openai.ChatCompletion.create(model='gpt-4', messages=[{'role': 'system', 'content': 'You are an assistant helping me to extract information from the operations.'}] + [{'role': 'user', 'content': q} for q in prompt_list])
        answer = result['choices'][0]['message']['content']
        print(f'{colored('[Motion Agent LLM] analyzing insertion scene dependency ', color='magenta', attrs=['bold'])}                     \n{colored('[Raw Response>>>]', attrs=['bold'])} {answer}')
        start = answer.index('{')
        answer = answer[start:]
        end = answer.rfind('}')
        answer = answer[:end + 1]
        placement_mode = eval(answer)
        print(f'{colored('[Extracted Response>>>]', attrs=['bold'])} {placement_mode} \n')
    except Exception as e:
        print(e)
        traceback.print_exc()
        return '[Motion Agent LLM] reasoning object dependency fails.'
    return placement_mode

def llm_placement_wo_dependency(self, scene, message):
    try:
        q0 = 'I will provide you with an operation statement to add and place a vehicle, and I need you to extract 3 specific placement information from the statement, including: '
        q1 = " (1) 'mode', one of ['front', 'left front', 'left', 'right front', 'right', 'random'], representing approximate initial positions of the vehicle. If not specified, it defaults to 'random'."
        q2 = " (2) 'distance_constraint' indicates whether there's a constraint on the distance of the added vehicle. 0 means no constraint, 1 means there is a constraint." + " If there's no relevant information mentioned, it defaults to 0."
        q3 = " (3) 'distance_min_max' represents the range of constraints when 'distance_constraint' applicable. It should be a tuple in the format (min, max), for example, (9, 11) means the minimum distance is 9, and the maximum is 11." + " When there's 'distance_constraint' is 0, the default value is (4, 45). If distance is specified as a specific value 'x', 'distance_min_max' is (x, x+5)"
        q4 = "Just return the json dict with keys:'mode', 'distance_constraint', 'distance_min_max'. Do not return any code or discription."
        q5 = "An Example: Given operation statement: 'Add an Audi 7-10 meters ahead', you should return " + "{'mode':'front', 'distance_constraint': 1, 'distance_min_max':(7,10)}"
        q6 = "An Example: Given operation statement: 'Add an Porsche in the right front.', you should return " + "{'mode':'right front', 'distance_constraint': 0, 'distance_min_max':(4, 45)}"
        q7 = 'Note that you should not return any code or explanations, only provide a JSON dictionary.'
        q8 = 'The operation statement:' + message
        prompt_list = [q0, q1, q2, q3, q4, q5, q6, q7, q8]
        result = openai.ChatCompletion.create(model='gpt-4', messages=[{'role': 'system', 'content': 'You are an assistant helping me to determine how to place a car.'}] + [{'role': 'user', 'content': q} for q in prompt_list])
        answer = result['choices'][0]['message']['content']
        print(f'{colored('[Motion Agent LLM] deciding scene-independent object placement', color='magenta', attrs=['bold'])}                     \n{colored('[Raw Response>>>]', attrs=['bold'])} {answer}')
        start = answer.index('{')
        answer = answer[start:]
        end = answer.rfind('}')
        answer = answer[:end + 1]
        placement_prior = eval(answer)
        print(f'{colored('[Extracted Response>>>]', attrs=['bold'])} {placement_prior} \n')
    except Exception as e:
        print(e)
        traceback.print_exc()
        return '[Motion Agent LLM] deciding placement fails.'
    return placement_prior

def llm_placement_w_dependency(self, scene, message, scene_object_description):
    try:
        q0 = 'I will provide you with an operation statement to add and place a vehicle, as well as information of other cars in the scene.'
        q1 = 'I need you to determine a specific position (x, y) for placement of the added car in my statement. '
        q2 = 'Information of other cars in the scene is a two-level dictionary, with the first level representing the different car id in the scene, ' + 'and the second level containing various information about that car, including the (x, y) of its world 3D coordinate, ' + 'its image coordinate (u, v) in an image frame, depth, and rgb color representation.'
        q3 = 'The dictionary is' + str(scene_object_description)
        q4 = 'I will also further inform you about the operations that have been previously performed on this scene. ' + 'You can use these past operations, along with the dictionary I provide, to generate the final position.'
        q5 = 'The previously performed operation is : ' + str(scene.past_operations)
        q6 = "If the car with key 'direction', and direction is close, 'behind' means keep the same 'y' and increase 'x' 10 meters. If direction is away, 'behind' means keep the same 'y' and decrease 'x' 10 meters." + "If the car with key 'direction', and direction is close, 'front' means keep the same 'y' and decrease 'x' 10 meters. If direction is away, 'front' means keep the same 'y' and increase 'x' 10 meters."
        q7 = "'left' means keep the same 'x' and increase 'y' 5m, 'right' means keep the same 'x' and decrease 'y' 5m."
        q8 = "You should return a placemenet positon in JSON dictionary with 2 keys: 'x', 'y'. Do not provide any code or explanations, only return the final JSON dictionary."
        q9 = 'The requirement is:' + message
        prompt_list = [q0, q1, q2, q3, q4, q5, q6, q7, q8, q9]
        result = openai.ChatCompletion.create(model='gpt-4', messages=[{'role': 'system', 'content': 'You are an assistant helping me to determine how to place a car.'}] + [{'role': 'user', 'content': q} for q in prompt_list])
        answer = result['choices'][0]['message']['content']
        print(f'{colored('[Motion Agent LLM] deciding scene-dependent object placement', color='magenta', attrs=['bold'])}                     \n{colored('[Raw Response>>>]', attrs=['bold'])} {answer}')
        start = answer.index('{')
        answer = answer[start:]
        end = answer.rfind('}')
        answer = answer[:end + 1]
        placement_prior = eval(answer)
        print(f'{colored('[Extracted Response>>>]', attrs=['bold'])} {placement_prior} \n')
    except Exception as e:
        print(e)
        traceback.print_exc()
        return '[Motion Agent LLM] deciding placement fails.'
    return placement_prior

def llm_motion_planning(self, scene, message):
    try:
        q0 = 'I will provide you with an operation statement to add and place a vehicle, and I need you to determine the its motion situation from my statement, including: '
        q1 = "(1) 'action', one of ['static', 'random', 'straight', 'turn left', 'turn right']. If action not mentioned in the statement, it defaults to 'straight'." + "For example, the statement is 'add a black car in front of me', then the action is 'straight'."
        q2 = "(2) 'speed', the approximate speed of the vehicle, one of ['random', 'fast', 'slow']. If speed is not mentioned in the statement, it defaults to 'slow'."
        q3 = "(3) 'direction', one of ['away', 'close', 'random']. 'away' represents the direction away from oneself, and 'close' represents the direction toward oneself." + "For example, moving forward is 'away' from oneself, while moving towards oneself is 'close'. If direction is not mentioned in the statement, just return 'random'."
        q4 = "(4) 'wrong_way', if the vehicle drives in the wrong way, one of ['true'. 'false']. If the information is not mentioned in the statement, it defaults to 'false'."
        q4 = "An Example: Given the statement 'add a Tesla that is racing straight ahead in the right front of the scene', you should return {'action': 'straight', 'speed': 'fast', 'direction': 'away', 'wrong_way': 'false'}"
        q5 = "An Example: Given the statement 'add a yellow Audi in front of the scene', you should return {'action': 'static', 'speed': 'random', 'direction': 'away', 'wrong_way': 'false'}"
        q6 = "An Example: Given the statement 'add a Tesla coming from the front and driving in the wrong way', you should return {'action': 'straight', 'speed': 'random', 'direction': 'close', 'wrong_way': 'true'}"
        q7 = 'Note that there is no need to return any code or explanations; only provide a JSON dictionary. Do not include any additional statements.'
        q8 = 'The operation statement is:' + message
        prompt_list = [q0, q1, q2, q3, q4, q5, q6, q7, q8]
        result = openai.ChatCompletion.create(model='gpt-4', messages=[{'role': 'system', 'content': 'You are an assistant helping me to assess the motion situation for adding vehicles.'}] + [{'role': 'user', 'content': q} for q in prompt_list])
        answer = result['choices'][0]['message']['content']
        print(f'{colored('[Motion Agent LLM] finding motion prior', color='magenta', attrs=['bold'])}                     \n{colored('[Raw Response>>>]', attrs=['bold'])} {answer}')
        start = answer.index('{')
        answer = answer[start:]
        end = answer.rfind('}')
        answer = answer[:end + 1]
        motion_prior = eval(answer)
        if not motion_prior.get('wrong_way'):
            motion_prior['wrong_way'] = False
        print(f'{colored('[Extracted Response>>>]', attrs=['bold'])} {motion_prior} \n')
    except Exception as e:
        print(e)
        traceback.print_exc()
        return '[Motion Agent LLM] finding motion prior fails.'
    return motion_prior

class ViewAdjustAgent:

    def __init__(self, config):
        self.config = config

    def llm_reasoning_ego_motion(self, scene, message):
        try:
            q0 = 'I will give you a description about view adjustment, I need you to help me judge if the description is related to static view adjust or ego is dynamic(with motion).'
            q1 = "Given my description, return a dictionary in JSON format, with key 'if_view_motion'"
            q2 = "If the description is just a view adjust operation, the 'if_view_motion' should be 0. If the description is related to view motion, the 'if_view_motion' should be 1."
            q3 = "I will give you some examples. <user>: Rotate the viewpoint 30 degrees to the left, you should return {'if_view_motion':0}. " + "<user>: viewpoint moves ahead slowly, you should return {'if_view_motion':1}. "
            result = openai.ChatCompletion.create(model='gpt-4', messages=[{'role': 'system', 'content': 'You are an assistant helping me to provide information and ultimately return a JSON dictionary.'}, {'role': 'user', 'content': q0}, {'role': 'user', 'content': q1}, {'role': 'user', 'content': q2}, {'role': 'user', 'content': q3}, {'role': 'user', 'content': message}])
            answer = result['choices'][0]['message']['content']
            print(f'{colored('[View Adjust Agent LLM] reasoning the view motion', color='magenta', attrs=['bold'])}                      \n{colored('[Raw Response>>>]', attrs=['bold'])} {answer}')
            start = answer.index('{')
            answer = answer[start:]
            end = answer.rfind('}')
            answer = answer[:end + 1]
            if_view_motion = eval(answer)
            print(f'{colored('[Extracted Response>>>]', attrs=['bold'])} {if_view_motion} \n')
        except Exception as e:
            print(e)
            traceback.print_exc()
            return '[View Adjust Agent LLM] fails, can not recongnize instruction'
        if if_view_motion['if_view_motion'] == 0:
            return False
        else:
            return True

    def llm_view_motion_gen(self, scene, message):
        try:
            q0 = 'I will give you a description about ego motion, you should tell me the speed of ego.'
            q1 = "Given my description, return a dictionary in JSON format, with key 'speed'."
            q2 = "If the ego motion is fast, 'speed' should be 'fast'; if the ego motion is slow, 'speed' should be 'slow'; if the description doesnot mention speed, 'speed' is default as 'fast'."
            q3 = "I will give you some examples. <user>: ego vehicle moves forward, you should return {'speed':'fast'}. " + "<user>: ego vehicle drives ahead slowly, you should return {'speed':'slow'}. "
            result = openai.ChatCompletion.create(model='gpt-4', messages=[{'role': 'system', 'content': 'You are an assistant helping me to provide information and ultimately return a JSON dictionary.'}, {'role': 'user', 'content': q0}, {'role': 'user', 'content': q1}, {'role': 'user', 'content': q2}, {'role': 'user', 'content': q3}, {'role': 'user', 'content': message}])
            answer = result['choices'][0]['message']['content']
            print(f'{colored('[View Adjust Agent LLM] generating the ego motion', color='magenta', attrs=['bold'])}                      \n{colored('[Raw Response>>>]', attrs=['bold'])} {answer}')
            start = answer.index('{')
            answer = answer[start:]
            end = answer.rfind('}')
            answer = answer[:end + 1]
            ego_motion_speed = eval(answer)
            print(f'{colored('[Extracted Response>>>]', attrs=['bold'])} {ego_motion_speed} \n')
        except Exception as e:
            print(e)
            traceback.print_exc()
            return '[View Adjust Agent LLM] fails, can not recongnize instruction'
        if ego_motion_speed['speed'] == 'fast':
            return (0, scene.nerf_motion_extrinsics.shape[0])
        else:
            return (0, scene.nerf_motion_extrinsics.shape[0] // 3)

    def llm_view_adjust(self, scene, message):
        try:
            q0 = "I will give you a transformation operation for my viewpoint, which may include translation in 'x', 'y', 'z' or a rotation 'theta' around z-axis. "
            q1 = "For translation, positive 'x' represents forward, positve 'y' represents left, and 'z' represents up. It follows a left-hand coordinate system." + "For rotation, postive 'theta' is counterclockwise. So from own perspective, my viewpoint turns to the left. 'theta' is in degree."
            q2 = "Given my operation, return a dictionary in JSON format, with keys 'x', 'y', 'z', 'theta'."
            q3 = 'I will give you some examples: <user>: Rotate the viewpoint 30 degrees to the left ' + "<assistant>: {\n  'x': 0,\n  'y': 0,\n  'z': 0,\n  'theta': 30,\n } \n" + '<user>: move the viewpoint forward by 1 ' + "<assistant>: {\n  'x': 1,\n  'y': 0,\n  'z': 0,\n  'theta': 0,\n }  \n" + '<user>: move the viewpoint to the right by 1' + "<assistant>: {\n  'x': 0,\n  'y': -1,\n  'z': 0,\n  'theta': 0,\n} "
            result = openai.ChatCompletion.create(model='gpt-4', messages=[{'role': 'system', 'content': 'You are an assistant helping me to provide information and ultimately return a JSON dictionary.'}, {'role': 'user', 'content': q0}, {'role': 'user', 'content': q1}, {'role': 'user', 'content': q2}, {'role': 'user', 'content': q3}, {'role': 'user', 'content': message}])
            answer = result['choices'][0]['message']['content']
            print(f'{colored('[View Adjust Agent LLM] analyzing view change', color='magenta', attrs=['bold'])}                      \n{colored('[Raw Response>>>]', attrs=['bold'])} {answer}')
            start = answer.index('{')
            answer = answer[start:]
            end = answer.rfind('}')
            answer = answer[:end + 1]
            delta_extrinsic = eval(answer)
            print(f'{colored('[Extracted Response>>>]', attrs=['bold'])} {delta_extrinsic} \n')
        except Exception as e:
            print(e)
            traceback.print_exc()
            return '[View Adjust Agent LLM] fails, can not recongnize instruction'
        return delta_extrinsic

    def func_update_extrinsic(self, scene, delta_extrinsic):
        scene.current_extrinsics[:, 0, 3] += delta_extrinsic['x']
        scene.current_extrinsics[:, 1, 3] += delta_extrinsic['y']
        scene.current_extrinsics[:, 2, 3] += delta_extrinsic['z']
        theta = delta_extrinsic['theta']
        theta = theta / 180 * np.pi
        T_theta = np.array([[np.cos(theta), -np.sin(theta), 0], [np.sin(theta), np.cos(theta), 0], [0, 0, 1]])
        scene.current_extrinsics = np.matmul(T_theta, scene.current_extrinsics)

    def func_generate_extrinsic(self, scene, start_frame_idx, end_frame_idx):
        scene.current_extrinsics = inter_poses(scene.nerf_motion_extrinsics[start_frame_idx:end_frame_idx:3], scene.frames)

def llm_reasoning_ego_motion(self, scene, message):
    try:
        q0 = 'I will give you a description about view adjustment, I need you to help me judge if the description is related to static view adjust or ego is dynamic(with motion).'
        q1 = "Given my description, return a dictionary in JSON format, with key 'if_view_motion'"
        q2 = "If the description is just a view adjust operation, the 'if_view_motion' should be 0. If the description is related to view motion, the 'if_view_motion' should be 1."
        q3 = "I will give you some examples. <user>: Rotate the viewpoint 30 degrees to the left, you should return {'if_view_motion':0}. " + "<user>: viewpoint moves ahead slowly, you should return {'if_view_motion':1}. "
        result = openai.ChatCompletion.create(model='gpt-4', messages=[{'role': 'system', 'content': 'You are an assistant helping me to provide information and ultimately return a JSON dictionary.'}, {'role': 'user', 'content': q0}, {'role': 'user', 'content': q1}, {'role': 'user', 'content': q2}, {'role': 'user', 'content': q3}, {'role': 'user', 'content': message}])
        answer = result['choices'][0]['message']['content']
        print(f'{colored('[View Adjust Agent LLM] reasoning the view motion', color='magenta', attrs=['bold'])}                      \n{colored('[Raw Response>>>]', attrs=['bold'])} {answer}')
        start = answer.index('{')
        answer = answer[start:]
        end = answer.rfind('}')
        answer = answer[:end + 1]
        if_view_motion = eval(answer)
        print(f'{colored('[Extracted Response>>>]', attrs=['bold'])} {if_view_motion} \n')
    except Exception as e:
        print(e)
        traceback.print_exc()
        return '[View Adjust Agent LLM] fails, can not recongnize instruction'
    if if_view_motion['if_view_motion'] == 0:
        return False
    else:
        return True

def llm_view_motion_gen(self, scene, message):
    try:
        q0 = 'I will give you a description about ego motion, you should tell me the speed of ego.'
        q1 = "Given my description, return a dictionary in JSON format, with key 'speed'."
        q2 = "If the ego motion is fast, 'speed' should be 'fast'; if the ego motion is slow, 'speed' should be 'slow'; if the description doesnot mention speed, 'speed' is default as 'fast'."
        q3 = "I will give you some examples. <user>: ego vehicle moves forward, you should return {'speed':'fast'}. " + "<user>: ego vehicle drives ahead slowly, you should return {'speed':'slow'}. "
        result = openai.ChatCompletion.create(model='gpt-4', messages=[{'role': 'system', 'content': 'You are an assistant helping me to provide information and ultimately return a JSON dictionary.'}, {'role': 'user', 'content': q0}, {'role': 'user', 'content': q1}, {'role': 'user', 'content': q2}, {'role': 'user', 'content': q3}, {'role': 'user', 'content': message}])
        answer = result['choices'][0]['message']['content']
        print(f'{colored('[View Adjust Agent LLM] generating the ego motion', color='magenta', attrs=['bold'])}                      \n{colored('[Raw Response>>>]', attrs=['bold'])} {answer}')
        start = answer.index('{')
        answer = answer[start:]
        end = answer.rfind('}')
        answer = answer[:end + 1]
        ego_motion_speed = eval(answer)
        print(f'{colored('[Extracted Response>>>]', attrs=['bold'])} {ego_motion_speed} \n')
    except Exception as e:
        print(e)
        traceback.print_exc()
        return '[View Adjust Agent LLM] fails, can not recongnize instruction'
    if ego_motion_speed['speed'] == 'fast':
        return (0, scene.nerf_motion_extrinsics.shape[0])
    else:
        return (0, scene.nerf_motion_extrinsics.shape[0] // 3)

def llm_view_adjust(self, scene, message):
    try:
        q0 = "I will give you a transformation operation for my viewpoint, which may include translation in 'x', 'y', 'z' or a rotation 'theta' around z-axis. "
        q1 = "For translation, positive 'x' represents forward, positve 'y' represents left, and 'z' represents up. It follows a left-hand coordinate system." + "For rotation, postive 'theta' is counterclockwise. So from own perspective, my viewpoint turns to the left. 'theta' is in degree."
        q2 = "Given my operation, return a dictionary in JSON format, with keys 'x', 'y', 'z', 'theta'."
        q3 = 'I will give you some examples: <user>: Rotate the viewpoint 30 degrees to the left ' + "<assistant>: {\n  'x': 0,\n  'y': 0,\n  'z': 0,\n  'theta': 30,\n } \n" + '<user>: move the viewpoint forward by 1 ' + "<assistant>: {\n  'x': 1,\n  'y': 0,\n  'z': 0,\n  'theta': 0,\n }  \n" + '<user>: move the viewpoint to the right by 1' + "<assistant>: {\n  'x': 0,\n  'y': -1,\n  'z': 0,\n  'theta': 0,\n} "
        result = openai.ChatCompletion.create(model='gpt-4', messages=[{'role': 'system', 'content': 'You are an assistant helping me to provide information and ultimately return a JSON dictionary.'}, {'role': 'user', 'content': q0}, {'role': 'user', 'content': q1}, {'role': 'user', 'content': q2}, {'role': 'user', 'content': q3}, {'role': 'user', 'content': message}])
        answer = result['choices'][0]['message']['content']
        print(f'{colored('[View Adjust Agent LLM] analyzing view change', color='magenta', attrs=['bold'])}                      \n{colored('[Raw Response>>>]', attrs=['bold'])} {answer}')
        start = answer.index('{')
        answer = answer[start:]
        end = answer.rfind('}')
        answer = answer[:end + 1]
        delta_extrinsic = eval(answer)
        print(f'{colored('[Extracted Response>>>]', attrs=['bold'])} {delta_extrinsic} \n')
    except Exception as e:
        print(e)
        traceback.print_exc()
        return '[View Adjust Agent LLM] fails, can not recongnize instruction'
    return delta_extrinsic

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

def build_dataset(hypes, split):
    dataset_args = hypes['dataset']
    dataset_cls = eval(dataset_args['name'])
    return dataset_cls(dataset_args, split)

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

def on_train_epoch_start(self):
    print(f'Module fixed in training: {self.fix_modules}.')
    for module in self.fix_modules:
        for p in eval(f'self.{module}').parameters():
            p.requires_grad_(False)
        eval(f'self.{module}').eval()

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

def on_train_epoch_start(self):
    print(f'Module fixed in training: {self.fix_modules}.')
    for module in self.fix_modules:
        for p in eval(f'self.{module}').parameters():
            p.requires_grad_(False)
        eval(f'self.{module}').eval()

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

def on_train_epoch_start(self):
    print(f'Module fixed in training: {self.fix_modules}.')
    for module in self.fix_modules:
        for p in eval(f'self.{module}').parameters():
            p.requires_grad_(False)
        eval(f'self.{module}').eval()

def build_module(args):
    module_type = args['type']
    module_args = args['args']
    module_cls = eval(module_type)
    return module_cls(module_args)

class EncoderNet(nn.Module):

    def __init__(self, args):
        super().__init__()
        self.args = args
        layer_num = len(args['layer_channels'])
        layer_channels = args['layer_channels']
        kernel_size = args['kernel_size']
        strides = args['strides']
        block_nums = args['block_nums']
        use_bn = args['use_bn']
        act = args['act']
        inplanes = args['in_ch']
        module_list = []
        for i in range(layer_num):
            module_list.append(build_layer(inplanes, layer_channels[i], kernel_size, strides[i], block_nums[i], act, use_bn))
            inplanes = layer_channels[i]
        self.model = nn.Sequential(*module_list)

    def forward(self, x):
        return self.model(x)

def forward(self, x):
    return self.model(x)

class DecoderNet(nn.Module):

    def __init__(self, args):
        super().__init__()
        self.args = args
        layer_num = len(args['layer_channels'])
        layer_channels = args['layer_channels']
        kernel_size = args['kernel_size']
        upstrides = args['upstrides']
        block_nums = args['block_nums']
        use_bn = args['use_bn']
        act = args['act']
        inplanes = args['in_ch']
        module_list = []
        for i in range(layer_num):
            module_list.append(build_up_layer(inplanes, layer_channels[i], kernel_size, upstrides[i], block_nums[i], act, use_bn))
            inplanes = layer_channels[i]
        self.model = nn.Sequential(*module_list)

    def forward(self, x):
        return self.model(x)

def forward(self, x):
    return self.model(x)

class MLP(nn.Module):

    def __init__(self, args):
        super().__init__()
        self.args = args
        layer_num = len(args['layer_channels'])
        layer_channels = args['layer_channels']
        act = args['act']
        if act == 'relu':
            self.act = nn.ReLU(inplace=True)
        elif act == 'selu':
            self.act = nn.SELU(inplace=True)
        elif act == 'elu':
            self.act = nn.ELU(inplace=True)
        elif act == 'none':
            self.act = nn.Identity()
        inplanes = args['in_ch']
        module_list = []
        for i in range(layer_num):
            module_list.append(nn.Linear(inplanes, layer_channels[i]))
            module_list.append(self.act)
            inplanes = layer_channels[i]
        self.model = nn.Sequential(*module_list)

    def forward(self, x):
        return self.model(x)

def forward(self, x):
    return self.model(x)

