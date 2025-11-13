# Cluster 1

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

def get_global_rank():
    """Find OMPI world rank without calling mpi functions
    :rtype: int
    """
    if os.environ.get('PMI_RANK') is not None:
        return int(os.environ.get('PMI_RANK') or 0)
    elif os.environ.get('OMPI_COMM_WORLD_RANK') is not None:
        return int(os.environ.get('OMPI_COMM_WORLD_RANK') or 0)
    else:
        return 0

def get_local_rank():
    """Find OMPI local rank without calling mpi functions
    :rtype: int
    """
    if os.environ.get('MPI_LOCALRANKID') is not None:
        return int(os.environ.get('MPI_LOCALRANKID') or 0)
    elif os.environ.get('OMPI_COMM_WORLD_LOCAL_RANK') is not None:
        return int(os.environ.get('OMPI_COMM_WORLD_LOCAL_RANK') or 0)
    else:
        return 0

def get_master_ip():
    if os.environ.get('AZ_BATCH_MASTER_NODE') is not None:
        return os.environ.get('AZ_BATCH_MASTER_NODE').split(':')[0]
    elif os.environ.get('AZ_BATCHAI_MPI_MASTER_NODE') is not None:
        return os.environ.get('AZ_BATCHAI_MPI_MASTER_NODE')
    else:
        return '127.0.0.1'

def sum_dict_with_prefix(target, cur_dict, prefix, default=0):
    for k, v in cur_dict.items():
        target_key = prefix + k
        target[target_key] = target.get(target_key, default) + v

def handle_deterministic_config(config):
    seed = dict(config).get('seed', None)
    if seed is None:
        return False
    seed_everything(seed)
    return True

def get_has_ddp_rank():
    master_port = os.environ.get('MASTER_PORT', None)
    node_rank = os.environ.get('NODE_RANK', None)
    local_rank = os.environ.get('LOCAL_RANK', None)
    world_size = os.environ.get('WORLD_SIZE', None)
    has_rank = master_port is not None or node_rank is not None or local_rank is not None or (world_size is not None)
    return has_rank

@functools.wraps(main_func)
def new_main(*args, **kwargs):
    parent_cwd = os.environ.get('TRAINING_PARENT_WORK_DIR', None)
    has_parent = parent_cwd is not None
    has_rank = get_has_ddp_rank()
    assert has_parent == has_rank, f'Inconsistent state: has_parent={has_parent}, has_rank={has_rank}'
    if has_parent:
        sys.argv.extend([f'hydra.run.dir={parent_cwd}'])
    main_func(*args, **kwargs)

def handle_ddp_parent_process():
    parent_cwd = os.environ.get('TRAINING_PARENT_WORK_DIR', None)
    has_parent = parent_cwd is not None
    has_rank = get_has_ddp_rank()
    assert has_parent == has_rank, f'Inconsistent state: has_parent={has_parent}, has_rank={has_rank}'
    if parent_cwd is None:
        os.environ['TRAINING_PARENT_WORK_DIR'] = os.getcwd()
    return has_parent

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

def store_discr_outputs(self, batch):
    out_size = batch['image'].shape[2:]
    discr_real_out, _ = self.discriminator(batch['image'])
    discr_fake_out, _ = self.discriminator(batch['predicted_image'])
    batch['discr_output_real'] = F.interpolate(discr_real_out, size=out_size, mode='nearest')
    batch['discr_output_fake'] = F.interpolate(discr_fake_out, size=out_size, mode='nearest')
    batch['discr_output_diff'] = batch['discr_output_real'] - batch['discr_output_fake']

class DefaultInpaintingTrainingModule(BaseInpaintingTrainingModule):

    def __init__(self, *args, concat_mask=True, rescale_scheduler_kwargs=None, image_to_discriminator='predicted_image', add_noise_kwargs=None, noise_fill_hole=False, const_area_crop_kwargs=None, distance_weighter_kwargs=None, distance_weighted_mask_for_discr=False, fake_fakes_proba=0, fake_fakes_generator_kwargs=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.concat_mask = concat_mask
        self.rescale_size_getter = get_ramp(**rescale_scheduler_kwargs) if rescale_scheduler_kwargs is not None else None
        self.image_to_discriminator = image_to_discriminator
        self.add_noise_kwargs = add_noise_kwargs
        self.noise_fill_hole = noise_fill_hole
        self.const_area_crop_kwargs = const_area_crop_kwargs
        self.refine_mask_for_losses = make_mask_distance_weighter(**distance_weighter_kwargs) if distance_weighter_kwargs is not None else None
        self.distance_weighted_mask_for_discr = distance_weighted_mask_for_discr
        self.fake_fakes_proba = fake_fakes_proba
        if self.fake_fakes_proba > 0.001:
            self.fake_fakes_gen = FakeFakesGenerator(**fake_fakes_generator_kwargs or {})

    def forward(self, batch):
        if self.training and self.rescale_size_getter is not None:
            cur_size = self.rescale_size_getter(self.global_step)
            batch['image'] = F.interpolate(batch['image'], size=cur_size, mode='bilinear', align_corners=False)
            batch['mask'] = F.interpolate(batch['mask'], size=cur_size, mode='nearest')
        if self.training and self.const_area_crop_kwargs is not None:
            batch = make_constant_area_crop_batch(batch, **self.const_area_crop_kwargs)
        img = batch['image']
        mask = batch['mask']
        masked_img = img * (1 - mask)
        if self.add_noise_kwargs is not None:
            noise = make_multiscale_noise(masked_img, **self.add_noise_kwargs)
            if self.noise_fill_hole:
                masked_img = masked_img + mask * noise[:, :masked_img.shape[1]]
            masked_img = torch.cat([masked_img, noise], dim=1)
        if self.concat_mask:
            masked_img = torch.cat([masked_img, mask], dim=1)
        batch['predicted_image'] = self.generator(masked_img)
        batch['inpainted'] = mask * batch['predicted_image'] + (1 - mask) * batch['image']
        if self.fake_fakes_proba > 0.001:
            if self.training and torch.rand(1).item() < self.fake_fakes_proba:
                batch['fake_fakes'], batch['fake_fakes_masks'] = self.fake_fakes_gen(img, mask)
                batch['use_fake_fakes'] = True
            else:
                batch['fake_fakes'] = torch.zeros_like(img)
                batch['fake_fakes_masks'] = torch.zeros_like(mask)
                batch['use_fake_fakes'] = False
        batch['mask_for_losses'] = self.refine_mask_for_losses(img, batch['predicted_image'], mask) if self.refine_mask_for_losses is not None and self.training else mask
        return batch

    def generator_loss(self, batch):
        img = batch['image']
        predicted_img = batch[self.image_to_discriminator]
        original_mask = batch['mask']
        supervised_mask = batch['mask_for_losses']
        l1_value = masked_l1_loss(predicted_img, img, supervised_mask, self.config.losses.l1.weight_known, self.config.losses.l1.weight_missing)
        total_loss = l1_value
        metrics = dict(gen_l1=l1_value)
        if self.config.losses.perceptual.weight > 0:
            pl_value = self.loss_pl(predicted_img, img, mask=supervised_mask).sum() * self.config.losses.perceptual.weight
            total_loss = total_loss + pl_value
            metrics['gen_pl'] = pl_value
        mask_for_discr = supervised_mask if self.distance_weighted_mask_for_discr else original_mask
        self.adversarial_loss.pre_generator_step(real_batch=img, fake_batch=predicted_img, generator=self.generator, discriminator=self.discriminator)
        discr_real_pred, discr_real_features = self.discriminator(img)
        discr_fake_pred, discr_fake_features = self.discriminator(predicted_img)
        adv_gen_loss, adv_metrics = self.adversarial_loss.generator_loss(real_batch=img, fake_batch=predicted_img, discr_real_pred=discr_real_pred, discr_fake_pred=discr_fake_pred, mask=mask_for_discr)
        total_loss = total_loss + adv_gen_loss
        metrics['gen_adv'] = adv_gen_loss
        metrics.update(add_prefix_to_keys(adv_metrics, 'adv_'))
        if self.config.losses.feature_matching.weight > 0:
            need_mask_in_fm = OmegaConf.to_container(self.config.losses.feature_matching).get('pass_mask', False)
            mask_for_fm = supervised_mask if need_mask_in_fm else None
            fm_value = feature_matching_loss(discr_fake_features, discr_real_features, mask=mask_for_fm) * self.config.losses.feature_matching.weight
            total_loss = total_loss + fm_value
            metrics['gen_fm'] = fm_value
        if self.loss_resnet_pl is not None:
            resnet_pl_value = self.loss_resnet_pl(predicted_img, img)
            total_loss = total_loss + resnet_pl_value
            metrics['gen_resnet_pl'] = resnet_pl_value
        return (total_loss, metrics)

    def discriminator_loss(self, batch):
        total_loss = 0
        metrics = {}
        predicted_img = batch[self.image_to_discriminator].detach()
        self.adversarial_loss.pre_discriminator_step(real_batch=batch['image'], fake_batch=predicted_img, generator=self.generator, discriminator=self.discriminator)
        discr_real_pred, discr_real_features = self.discriminator(batch['image'])
        discr_fake_pred, discr_fake_features = self.discriminator(predicted_img)
        adv_discr_loss, adv_metrics = self.adversarial_loss.discriminator_loss(real_batch=batch['image'], fake_batch=predicted_img, discr_real_pred=discr_real_pred, discr_fake_pred=discr_fake_pred, mask=batch['mask'])
        total_loss = total_loss + adv_discr_loss
        metrics['discr_adv'] = adv_discr_loss
        metrics.update(add_prefix_to_keys(adv_metrics, 'adv_'))
        if batch.get('use_fake_fakes', False):
            fake_fakes = batch['fake_fakes']
            self.adversarial_loss.pre_discriminator_step(real_batch=batch['image'], fake_batch=fake_fakes, generator=self.generator, discriminator=self.discriminator)
            discr_fake_fakes_pred, _ = self.discriminator(fake_fakes)
            fake_fakes_adv_discr_loss, fake_fakes_adv_metrics = self.adversarial_loss.discriminator_loss(real_batch=batch['image'], fake_batch=fake_fakes, discr_real_pred=discr_real_pred, discr_fake_pred=discr_fake_fakes_pred, mask=batch['mask'])
            total_loss = total_loss + fake_fakes_adv_discr_loss
            metrics['discr_adv_fake_fakes'] = fake_fakes_adv_discr_loss
            metrics.update(add_prefix_to_keys(fake_fakes_adv_metrics, 'adv_'))
        return (total_loss, metrics)

def generator_loss(self, batch):
    img = batch['image']
    predicted_img = batch[self.image_to_discriminator]
    original_mask = batch['mask']
    supervised_mask = batch['mask_for_losses']
    l1_value = masked_l1_loss(predicted_img, img, supervised_mask, self.config.losses.l1.weight_known, self.config.losses.l1.weight_missing)
    total_loss = l1_value
    metrics = dict(gen_l1=l1_value)
    if self.config.losses.perceptual.weight > 0:
        pl_value = self.loss_pl(predicted_img, img, mask=supervised_mask).sum() * self.config.losses.perceptual.weight
        total_loss = total_loss + pl_value
        metrics['gen_pl'] = pl_value
    mask_for_discr = supervised_mask if self.distance_weighted_mask_for_discr else original_mask
    self.adversarial_loss.pre_generator_step(real_batch=img, fake_batch=predicted_img, generator=self.generator, discriminator=self.discriminator)
    discr_real_pred, discr_real_features = self.discriminator(img)
    discr_fake_pred, discr_fake_features = self.discriminator(predicted_img)
    adv_gen_loss, adv_metrics = self.adversarial_loss.generator_loss(real_batch=img, fake_batch=predicted_img, discr_real_pred=discr_real_pred, discr_fake_pred=discr_fake_pred, mask=mask_for_discr)
    total_loss = total_loss + adv_gen_loss
    metrics['gen_adv'] = adv_gen_loss
    metrics.update(add_prefix_to_keys(adv_metrics, 'adv_'))
    if self.config.losses.feature_matching.weight > 0:
        need_mask_in_fm = OmegaConf.to_container(self.config.losses.feature_matching).get('pass_mask', False)
        mask_for_fm = supervised_mask if need_mask_in_fm else None
        fm_value = feature_matching_loss(discr_fake_features, discr_real_features, mask=mask_for_fm) * self.config.losses.feature_matching.weight
        total_loss = total_loss + fm_value
        metrics['gen_fm'] = fm_value
    if self.loss_resnet_pl is not None:
        resnet_pl_value = self.loss_resnet_pl(predicted_img, img)
        total_loss = total_loss + resnet_pl_value
        metrics['gen_resnet_pl'] = resnet_pl_value
    return (total_loss, metrics)

def discriminator_loss(self, batch):
    total_loss = 0
    metrics = {}
    predicted_img = batch[self.image_to_discriminator].detach()
    self.adversarial_loss.pre_discriminator_step(real_batch=batch['image'], fake_batch=predicted_img, generator=self.generator, discriminator=self.discriminator)
    discr_real_pred, discr_real_features = self.discriminator(batch['image'])
    discr_fake_pred, discr_fake_features = self.discriminator(predicted_img)
    adv_discr_loss, adv_metrics = self.adversarial_loss.discriminator_loss(real_batch=batch['image'], fake_batch=predicted_img, discr_real_pred=discr_real_pred, discr_fake_pred=discr_fake_pred, mask=batch['mask'])
    total_loss = total_loss + adv_discr_loss
    metrics['discr_adv'] = adv_discr_loss
    metrics.update(add_prefix_to_keys(adv_metrics, 'adv_'))
    if batch.get('use_fake_fakes', False):
        fake_fakes = batch['fake_fakes']
        self.adversarial_loss.pre_discriminator_step(real_batch=batch['image'], fake_batch=fake_fakes, generator=self.generator, discriminator=self.discriminator)
        discr_fake_fakes_pred, _ = self.discriminator(fake_fakes)
        fake_fakes_adv_discr_loss, fake_fakes_adv_metrics = self.adversarial_loss.discriminator_loss(real_batch=batch['image'], fake_batch=fake_fakes, discr_real_pred=discr_real_pred, discr_fake_pred=discr_fake_fakes_pred, mask=batch['mask'])
        total_loss = total_loss + fake_fakes_adv_discr_loss
        metrics['discr_adv_fake_fakes'] = fake_fakes_adv_discr_loss
        metrics.update(add_prefix_to_keys(fake_fakes_adv_metrics, 'adv_'))
    return (total_loss, metrics)

def make_training_model(config):
    kind = config.training_model.kind
    kwargs = dict(config.training_model)
    kwargs.pop('kind')
    kwargs['use_ddp'] = config.trainer.kwargs.get('accelerator', None) == 'ddp'
    logging.info(f'Make training model {kind}')
    cls = get_training_model_class(kind)
    return cls(config, **kwargs)

class DataParallelWithCallback(DataParallel):
    """
    Data Parallel with a replication callback.

    An replication callback `__data_parallel_replicate__` of each module will be invoked after being created by
    original `replicate` function.
    The callback will be invoked with arguments `__data_parallel_replicate__(ctx, copy_id)`

    Examples:
        > sync_bn = SynchronizedBatchNorm1d(10, eps=1e-5, affine=False)
        > sync_bn = DataParallelWithCallback(sync_bn, device_ids=[0, 1])
        # sync_bn.__data_parallel_replicate__ will be invoked.
    """

    def replicate(self, module, device_ids):
        modules = super(DataParallelWithCallback, self).replicate(module, device_ids)
        execute_replication_callbacks(modules)
        return modules

def replicate(self, module, device_ids):
    modules = super(DataParallelWithCallback, self).replicate(module, device_ids)
    execute_replication_callbacks(modules)
    return modules

@functools.wraps(old_replicate)
def new_replicate(module, device_ids):
    modules = old_replicate(module, device_ids)
    execute_replication_callbacks(modules)
    return modules

class SlavePipe(_SlavePipeBase):
    """Pipe for master-slave communication."""

    def run_slave(self, msg):
        self.queue.put((self.identifier, msg))
        ret = self.result.get()
        self.queue.put(True)
        return ret

def run_slave(self, msg):
    self.queue.put((self.identifier, msg))
    ret = self.result.get()
    self.queue.put(True)
    return ret

class SyncMaster(object):
    """An abstract `SyncMaster` object.

    - During the replication, as the data parallel will trigger an callback of each module, all slave devices should
    call `register(id)` and obtain an `SlavePipe` to communicate with the master.
    - During the forward pass, master device invokes `run_master`, all messages from slave devices will be collected,
    and passed to a registered callback.
    - After receiving the messages, the master device should gather the information and determine to message passed
    back to each slave devices.
    """

    def __init__(self, master_callback):
        """

        Args:
            master_callback: a callback to be invoked after having collected messages from slave devices.
        """
        self._master_callback = master_callback
        self._queue = queue.Queue()
        self._registry = collections.OrderedDict()
        self._activated = False

    def register_slave(self, identifier):
        """
        Register an slave device.

        Args:
            identifier: an identifier, usually is the device id.

        Returns: a `SlavePipe` object which can be used to communicate with the master device.

        """
        if self._activated:
            assert self._queue.empty(), 'Queue is not clean before next initialization.'
            self._activated = False
            self._registry.clear()
        future = FutureResult()
        self._registry[identifier] = _MasterRegistry(future)
        return SlavePipe(identifier, self._queue, future)

    def run_master(self, master_msg):
        """
        Main entry for the master device in each forward pass.
        The messages were first collected from each devices (including the master device), and then
        an callback will be invoked to compute the message to be sent back to each devices
        (including the master device).

        Args:
            master_msg: the message that the master want to send to itself. This will be placed as the first
            message when calling `master_callback`. For detailed usage, see `_SynchronizedBatchNorm` for an example.

        Returns: the message to be sent back to the master device.

        """
        self._activated = True
        intermediates = [(0, master_msg)]
        for i in range(self.nr_slaves):
            intermediates.append(self._queue.get())
        results = self._master_callback(intermediates)
        assert results[0][0] == 0, 'The first result should belongs to the master.'
        for i, res in results:
            if i == 0:
                continue
            self._registry[i].result.put(res)
        for i in range(self.nr_slaves):
            assert self._queue.get() is True
        return results[0][1]

    @property
    def nr_slaves(self):
        return len(self._registry)

def run_master(self, master_msg):
    """
        Main entry for the master device in each forward pass.
        The messages were first collected from each devices (including the master device), and then
        an callback will be invoked to compute the message to be sent back to each devices
        (including the master device).

        Args:
            master_msg: the message that the master want to send to itself. This will be placed as the first
            message when calling `master_callback`. For detailed usage, see `_SynchronizedBatchNorm` for an example.

        Returns: the message to be sent back to the master device.

        """
    self._activated = True
    intermediates = [(0, master_msg)]
    for i in range(self.nr_slaves):
        intermediates.append(self._queue.get())
    results = self._master_callback(intermediates)
    assert results[0][0] == 0, 'The first result should belongs to the master.'
    for i, res in results:
        if i == 0:
            continue
        self._registry[i].result.put(res)
    for i in range(self.nr_slaves):
        assert self._queue.get() is True
    return results[0][1]

def sum_dict_with_prefix(target, cur_dict, prefix, default=0):
    for k, v in cur_dict.items():
        target_key = prefix + k
        target[target_key] = target.get(target_key, default) + v

def handle_deterministic_config(config):
    seed = dict(config).get('seed', None)
    if seed is None:
        return False
    seed_everything(seed)
    return True

def get_has_ddp_rank():
    master_port = os.environ.get('MASTER_PORT', None)
    node_rank = os.environ.get('NODE_RANK', None)
    local_rank = os.environ.get('LOCAL_RANK', None)
    world_size = os.environ.get('WORLD_SIZE', None)
    has_rank = master_port is not None or node_rank is not None or local_rank is not None or (world_size is not None)
    return has_rank

@functools.wraps(main_func)
def new_main(*args, **kwargs):
    parent_cwd = os.environ.get('TRAINING_PARENT_WORK_DIR', None)
    has_parent = parent_cwd is not None
    has_rank = get_has_ddp_rank()
    assert has_parent == has_rank, f'Inconsistent state: has_parent={has_parent}, has_rank={has_rank}'
    if has_parent:
        sys.argv.extend([f'hydra.run.dir={parent_cwd}'])
    main_func(*args, **kwargs)

def handle_ddp_parent_process():
    parent_cwd = os.environ.get('TRAINING_PARENT_WORK_DIR', None)
    has_parent = parent_cwd is not None
    has_rank = get_has_ddp_rank()
    assert has_parent == has_rank, f'Inconsistent state: has_parent={has_parent}, has_rank={has_rank}'
    if parent_cwd is None:
        os.environ['TRAINING_PARENT_WORK_DIR'] = os.getcwd()
    return has_parent

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

def store_discr_outputs(self, batch):
    out_size = batch['image'].shape[2:]
    discr_real_out, _ = self.discriminator(batch['image'])
    discr_fake_out, _ = self.discriminator(batch['predicted_image'])
    batch['discr_output_real'] = F.interpolate(discr_real_out, size=out_size, mode='nearest')
    batch['discr_output_fake'] = F.interpolate(discr_fake_out, size=out_size, mode='nearest')
    batch['discr_output_diff'] = batch['discr_output_real'] - batch['discr_output_fake']

class DefaultInpaintingTrainingModule(BaseInpaintingTrainingModule):

    def __init__(self, *args, concat_mask=True, rescale_scheduler_kwargs=None, image_to_discriminator='predicted_image', add_noise_kwargs=None, noise_fill_hole=False, const_area_crop_kwargs=None, distance_weighter_kwargs=None, distance_weighted_mask_for_discr=False, fake_fakes_proba=0, fake_fakes_generator_kwargs=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.concat_mask = concat_mask
        self.rescale_size_getter = get_ramp(**rescale_scheduler_kwargs) if rescale_scheduler_kwargs is not None else None
        self.image_to_discriminator = image_to_discriminator
        self.add_noise_kwargs = add_noise_kwargs
        self.noise_fill_hole = noise_fill_hole
        self.const_area_crop_kwargs = const_area_crop_kwargs
        self.refine_mask_for_losses = make_mask_distance_weighter(**distance_weighter_kwargs) if distance_weighter_kwargs is not None else None
        self.distance_weighted_mask_for_discr = distance_weighted_mask_for_discr
        self.fake_fakes_proba = fake_fakes_proba
        if self.fake_fakes_proba > 0.001:
            self.fake_fakes_gen = FakeFakesGenerator(**fake_fakes_generator_kwargs or {})

    def forward(self, batch):
        if self.training and self.rescale_size_getter is not None:
            cur_size = self.rescale_size_getter(self.global_step)
            batch['image'] = F.interpolate(batch['image'], size=cur_size, mode='bilinear', align_corners=False)
            batch['mask'] = F.interpolate(batch['mask'], size=cur_size, mode='nearest')
        if self.training and self.const_area_crop_kwargs is not None:
            batch = make_constant_area_crop_batch(batch, **self.const_area_crop_kwargs)
        img = batch['image']
        mask = batch['mask']
        masked_img = img * (1 - mask)
        if self.add_noise_kwargs is not None:
            noise = make_multiscale_noise(masked_img, **self.add_noise_kwargs)
            if self.noise_fill_hole:
                masked_img = masked_img + mask * noise[:, :masked_img.shape[1]]
            masked_img = torch.cat([masked_img, noise], dim=1)
        if self.concat_mask:
            masked_img = torch.cat([masked_img, mask], dim=1)
        batch['predicted_image'] = self.generator(masked_img)
        batch['inpainted'] = mask * batch['predicted_image'] + (1 - mask) * batch['image']
        if self.fake_fakes_proba > 0.001:
            if self.training and torch.rand(1).item() < self.fake_fakes_proba:
                batch['fake_fakes'], batch['fake_fakes_masks'] = self.fake_fakes_gen(img, mask)
                batch['use_fake_fakes'] = True
            else:
                batch['fake_fakes'] = torch.zeros_like(img)
                batch['fake_fakes_masks'] = torch.zeros_like(mask)
                batch['use_fake_fakes'] = False
        batch['mask_for_losses'] = self.refine_mask_for_losses(img, batch['predicted_image'], mask) if self.refine_mask_for_losses is not None and self.training else mask
        return batch

    def generator_loss(self, batch):
        img = batch['image']
        predicted_img = batch[self.image_to_discriminator]
        original_mask = batch['mask']
        supervised_mask = batch['mask_for_losses']
        l1_value = masked_l1_loss(predicted_img, img, supervised_mask, self.config.losses.l1.weight_known, self.config.losses.l1.weight_missing)
        total_loss = l1_value
        metrics = dict(gen_l1=l1_value)
        if self.config.losses.perceptual.weight > 0:
            pl_value = self.loss_pl(predicted_img, img, mask=supervised_mask).sum() * self.config.losses.perceptual.weight
            total_loss = total_loss + pl_value
            metrics['gen_pl'] = pl_value
        mask_for_discr = supervised_mask if self.distance_weighted_mask_for_discr else original_mask
        self.adversarial_loss.pre_generator_step(real_batch=img, fake_batch=predicted_img, generator=self.generator, discriminator=self.discriminator)
        discr_real_pred, discr_real_features = self.discriminator(img)
        discr_fake_pred, discr_fake_features = self.discriminator(predicted_img)
        adv_gen_loss, adv_metrics = self.adversarial_loss.generator_loss(real_batch=img, fake_batch=predicted_img, discr_real_pred=discr_real_pred, discr_fake_pred=discr_fake_pred, mask=mask_for_discr)
        total_loss = total_loss + adv_gen_loss
        metrics['gen_adv'] = adv_gen_loss
        metrics.update(add_prefix_to_keys(adv_metrics, 'adv_'))
        if self.config.losses.feature_matching.weight > 0:
            need_mask_in_fm = OmegaConf.to_container(self.config.losses.feature_matching).get('pass_mask', False)
            mask_for_fm = supervised_mask if need_mask_in_fm else None
            fm_value = feature_matching_loss(discr_fake_features, discr_real_features, mask=mask_for_fm) * self.config.losses.feature_matching.weight
            total_loss = total_loss + fm_value
            metrics['gen_fm'] = fm_value
        if self.loss_resnet_pl is not None:
            resnet_pl_value = self.loss_resnet_pl(predicted_img, img)
            total_loss = total_loss + resnet_pl_value
            metrics['gen_resnet_pl'] = resnet_pl_value
        return (total_loss, metrics)

    def discriminator_loss(self, batch):
        total_loss = 0
        metrics = {}
        predicted_img = batch[self.image_to_discriminator].detach()
        self.adversarial_loss.pre_discriminator_step(real_batch=batch['image'], fake_batch=predicted_img, generator=self.generator, discriminator=self.discriminator)
        discr_real_pred, discr_real_features = self.discriminator(batch['image'])
        discr_fake_pred, discr_fake_features = self.discriminator(predicted_img)
        adv_discr_loss, adv_metrics = self.adversarial_loss.discriminator_loss(real_batch=batch['image'], fake_batch=predicted_img, discr_real_pred=discr_real_pred, discr_fake_pred=discr_fake_pred, mask=batch['mask'])
        total_loss = total_loss + adv_discr_loss
        metrics['discr_adv'] = adv_discr_loss
        metrics.update(add_prefix_to_keys(adv_metrics, 'adv_'))
        if batch.get('use_fake_fakes', False):
            fake_fakes = batch['fake_fakes']
            self.adversarial_loss.pre_discriminator_step(real_batch=batch['image'], fake_batch=fake_fakes, generator=self.generator, discriminator=self.discriminator)
            discr_fake_fakes_pred, _ = self.discriminator(fake_fakes)
            fake_fakes_adv_discr_loss, fake_fakes_adv_metrics = self.adversarial_loss.discriminator_loss(real_batch=batch['image'], fake_batch=fake_fakes, discr_real_pred=discr_real_pred, discr_fake_pred=discr_fake_fakes_pred, mask=batch['mask'])
            total_loss = total_loss + fake_fakes_adv_discr_loss
            metrics['discr_adv_fake_fakes'] = fake_fakes_adv_discr_loss
            metrics.update(add_prefix_to_keys(fake_fakes_adv_metrics, 'adv_'))
        return (total_loss, metrics)

def generator_loss(self, batch):
    img = batch['image']
    predicted_img = batch[self.image_to_discriminator]
    original_mask = batch['mask']
    supervised_mask = batch['mask_for_losses']
    l1_value = masked_l1_loss(predicted_img, img, supervised_mask, self.config.losses.l1.weight_known, self.config.losses.l1.weight_missing)
    total_loss = l1_value
    metrics = dict(gen_l1=l1_value)
    if self.config.losses.perceptual.weight > 0:
        pl_value = self.loss_pl(predicted_img, img, mask=supervised_mask).sum() * self.config.losses.perceptual.weight
        total_loss = total_loss + pl_value
        metrics['gen_pl'] = pl_value
    mask_for_discr = supervised_mask if self.distance_weighted_mask_for_discr else original_mask
    self.adversarial_loss.pre_generator_step(real_batch=img, fake_batch=predicted_img, generator=self.generator, discriminator=self.discriminator)
    discr_real_pred, discr_real_features = self.discriminator(img)
    discr_fake_pred, discr_fake_features = self.discriminator(predicted_img)
    adv_gen_loss, adv_metrics = self.adversarial_loss.generator_loss(real_batch=img, fake_batch=predicted_img, discr_real_pred=discr_real_pred, discr_fake_pred=discr_fake_pred, mask=mask_for_discr)
    total_loss = total_loss + adv_gen_loss
    metrics['gen_adv'] = adv_gen_loss
    metrics.update(add_prefix_to_keys(adv_metrics, 'adv_'))
    if self.config.losses.feature_matching.weight > 0:
        need_mask_in_fm = OmegaConf.to_container(self.config.losses.feature_matching).get('pass_mask', False)
        mask_for_fm = supervised_mask if need_mask_in_fm else None
        fm_value = feature_matching_loss(discr_fake_features, discr_real_features, mask=mask_for_fm) * self.config.losses.feature_matching.weight
        total_loss = total_loss + fm_value
        metrics['gen_fm'] = fm_value
    if self.loss_resnet_pl is not None:
        resnet_pl_value = self.loss_resnet_pl(predicted_img, img)
        total_loss = total_loss + resnet_pl_value
        metrics['gen_resnet_pl'] = resnet_pl_value
    return (total_loss, metrics)

def discriminator_loss(self, batch):
    total_loss = 0
    metrics = {}
    predicted_img = batch[self.image_to_discriminator].detach()
    self.adversarial_loss.pre_discriminator_step(real_batch=batch['image'], fake_batch=predicted_img, generator=self.generator, discriminator=self.discriminator)
    discr_real_pred, discr_real_features = self.discriminator(batch['image'])
    discr_fake_pred, discr_fake_features = self.discriminator(predicted_img)
    adv_discr_loss, adv_metrics = self.adversarial_loss.discriminator_loss(real_batch=batch['image'], fake_batch=predicted_img, discr_real_pred=discr_real_pred, discr_fake_pred=discr_fake_pred, mask=batch['mask'])
    total_loss = total_loss + adv_discr_loss
    metrics['discr_adv'] = adv_discr_loss
    metrics.update(add_prefix_to_keys(adv_metrics, 'adv_'))
    if batch.get('use_fake_fakes', False):
        fake_fakes = batch['fake_fakes']
        self.adversarial_loss.pre_discriminator_step(real_batch=batch['image'], fake_batch=fake_fakes, generator=self.generator, discriminator=self.discriminator)
        discr_fake_fakes_pred, _ = self.discriminator(fake_fakes)
        fake_fakes_adv_discr_loss, fake_fakes_adv_metrics = self.adversarial_loss.discriminator_loss(real_batch=batch['image'], fake_batch=fake_fakes, discr_real_pred=discr_real_pred, discr_fake_pred=discr_fake_fakes_pred, mask=batch['mask'])
        total_loss = total_loss + fake_fakes_adv_discr_loss
        metrics['discr_adv_fake_fakes'] = fake_fakes_adv_discr_loss
        metrics.update(add_prefix_to_keys(fake_fakes_adv_metrics, 'adv_'))
    return (total_loss, metrics)

def make_training_model(config):
    kind = config.training_model.kind
    kwargs = dict(config.training_model)
    kwargs.pop('kind')
    kwargs['use_ddp'] = config.trainer.kwargs.get('accelerator', None) == 'ddp'
    logging.info(f'Make training model {kind}')
    cls = get_training_model_class(kind)
    return cls(config, **kwargs)

class DataParallelWithCallback(DataParallel):
    """
    Data Parallel with a replication callback.

    An replication callback `__data_parallel_replicate__` of each module will be invoked after being created by
    original `replicate` function.
    The callback will be invoked with arguments `__data_parallel_replicate__(ctx, copy_id)`

    Examples:
        > sync_bn = SynchronizedBatchNorm1d(10, eps=1e-5, affine=False)
        > sync_bn = DataParallelWithCallback(sync_bn, device_ids=[0, 1])
        # sync_bn.__data_parallel_replicate__ will be invoked.
    """

    def replicate(self, module, device_ids):
        modules = super(DataParallelWithCallback, self).replicate(module, device_ids)
        execute_replication_callbacks(modules)
        return modules

def replicate(self, module, device_ids):
    modules = super(DataParallelWithCallback, self).replicate(module, device_ids)
    execute_replication_callbacks(modules)
    return modules

@functools.wraps(old_replicate)
def new_replicate(module, device_ids):
    modules = old_replicate(module, device_ids)
    execute_replication_callbacks(modules)
    return modules

class SlavePipe(_SlavePipeBase):
    """Pipe for master-slave communication."""

    def run_slave(self, msg):
        self.queue.put((self.identifier, msg))
        ret = self.result.get()
        self.queue.put(True)
        return ret

def run_slave(self, msg):
    self.queue.put((self.identifier, msg))
    ret = self.result.get()
    self.queue.put(True)
    return ret

class SyncMaster(object):
    """An abstract `SyncMaster` object.

    - During the replication, as the data parallel will trigger an callback of each module, all slave devices should
    call `register(id)` and obtain an `SlavePipe` to communicate with the master.
    - During the forward pass, master device invokes `run_master`, all messages from slave devices will be collected,
    and passed to a registered callback.
    - After receiving the messages, the master device should gather the information and determine to message passed
    back to each slave devices.
    """

    def __init__(self, master_callback):
        """

        Args:
            master_callback: a callback to be invoked after having collected messages from slave devices.
        """
        self._master_callback = master_callback
        self._queue = queue.Queue()
        self._registry = collections.OrderedDict()
        self._activated = False

    def register_slave(self, identifier):
        """
        Register an slave device.

        Args:
            identifier: an identifier, usually is the device id.

        Returns: a `SlavePipe` object which can be used to communicate with the master device.

        """
        if self._activated:
            assert self._queue.empty(), 'Queue is not clean before next initialization.'
            self._activated = False
            self._registry.clear()
        future = FutureResult()
        self._registry[identifier] = _MasterRegistry(future)
        return SlavePipe(identifier, self._queue, future)

    def run_master(self, master_msg):
        """
        Main entry for the master device in each forward pass.
        The messages were first collected from each devices (including the master device), and then
        an callback will be invoked to compute the message to be sent back to each devices
        (including the master device).

        Args:
            master_msg: the message that the master want to send to itself. This will be placed as the first
            message when calling `master_callback`. For detailed usage, see `_SynchronizedBatchNorm` for an example.

        Returns: the message to be sent back to the master device.

        """
        self._activated = True
        intermediates = [(0, master_msg)]
        for i in range(self.nr_slaves):
            intermediates.append(self._queue.get())
        results = self._master_callback(intermediates)
        assert results[0][0] == 0, 'The first result should belongs to the master.'
        for i, res in results:
            if i == 0:
                continue
            self._registry[i].result.put(res)
        for i in range(self.nr_slaves):
            assert self._queue.get() is True
        return results[0][1]

    @property
    def nr_slaves(self):
        return len(self._registry)

def run_master(self, master_msg):
    """
        Main entry for the master device in each forward pass.
        The messages were first collected from each devices (including the master device), and then
        an callback will be invoked to compute the message to be sent back to each devices
        (including the master device).

        Args:
            master_msg: the message that the master want to send to itself. This will be placed as the first
            message when calling `master_callback`. For detailed usage, see `_SynchronizedBatchNorm` for an example.

        Returns: the message to be sent back to the master device.

        """
    self._activated = True
    intermediates = [(0, master_msg)]
    for i in range(self.nr_slaves):
        intermediates.append(self._queue.get())
    results = self._master_callback(intermediates)
    assert results[0][0] == 0, 'The first result should belongs to the master.'
    for i, res in results:
        if i == 0:
            continue
        self._registry[i].result.put(res)
    for i in range(self.nr_slaves):
        assert self._queue.get() is True
    return results[0][1]

class MetricLogger(object):

    def __init__(self, delimiter='\t'):
        self.meters = defaultdict(SmoothedValue)
        self.delimiter = delimiter

    def update(self, **kwargs):
        for k, v in kwargs.items():
            if isinstance(v, torch.Tensor):
                v = v.item()
            assert isinstance(v, (float, int))
            self.meters[k].update(v)

    def __getattr__(self, attr):
        if attr in self.meters:
            return self.meters[attr]
        if attr in self.__dict__:
            return self.__dict__[attr]
        raise AttributeError("'{}' object has no attribute '{}'".format(type(self).__name__, attr))

    def __str__(self):
        loss_str = []
        for name, meter in self.meters.items():
            loss_str.append('{}: {}'.format(name, str(meter)))
        return self.delimiter.join(loss_str)

    def synchronize_between_processes(self):
        for meter in self.meters.values():
            meter.synchronize_between_processes()

    def add_meter(self, name, meter):
        self.meters[name] = meter

    def log_every(self, iterable, print_freq, header=None):
        i = 0
        if not header:
            header = ''
        start_time = time.time()
        end = time.time()
        iter_time = SmoothedValue(fmt='{avg:.4f}')
        data_time = SmoothedValue(fmt='{avg:.4f}')
        space_fmt = ':' + str(len(str(len(iterable)))) + 'd'
        if torch.cuda.is_available():
            log_msg = self.delimiter.join([header, '[{0' + space_fmt + '}/{1}]', 'eta: {eta}', '{meters}', 'time: {time}', 'data: {data}', 'max mem: {memory:.0f}'])
        else:
            log_msg = self.delimiter.join([header, '[{0' + space_fmt + '}/{1}]', 'eta: {eta}', '{meters}', 'time: {time}', 'data: {data}'])
        MB = 1024.0 * 1024.0
        for obj in iterable:
            data_time.update(time.time() - end)
            yield obj
            iter_time.update(time.time() - end)
            if i % print_freq == 0 or i == len(iterable) - 1:
                eta_seconds = iter_time.global_avg * (len(iterable) - i)
                eta_string = str(datetime.timedelta(seconds=int(eta_seconds)))
                if torch.cuda.is_available():
                    print(log_msg.format(i, len(iterable), eta=eta_string, meters=str(self), time=str(iter_time), data=str(data_time), memory=torch.cuda.max_memory_allocated() / MB))
                else:
                    print(log_msg.format(i, len(iterable), eta=eta_string, meters=str(self), time=str(iter_time), data=str(data_time)))
            i += 1
            end = time.time()
        total_time = time.time() - start_time
        total_time_str = str(datetime.timedelta(seconds=int(total_time)))
        print('{} Total time: {} ({:.4f} s / it)'.format(header, total_time_str, total_time / len(iterable)))

def update(self, **kwargs):
    for k, v in kwargs.items():
        if isinstance(v, torch.Tensor):
            v = v.item()
        assert isinstance(v, (float, int))
        self.meters[k].update(v)

def print(*args, **kwargs):
    force = kwargs.pop('force', False)
    if is_master or force:
        builtin_print(*args, **kwargs)

def merge_template_search(inp_list, return_search=False, return_template=False):
    """NOTICE: search region related features must be in the last place"""
    seq_dict = {'feat': torch.cat([x['feat'] for x in inp_list], dim=0), 'mask': torch.cat([x['mask'] for x in inp_list], dim=1), 'pos': torch.cat([x['pos'] for x in inp_list], dim=0)}
    if return_search:
        x = inp_list[-1]
        seq_dict.update({'feat_x': x['feat'], 'mask_x': x['mask'], 'pos_x': x['pos']})
    if return_template:
        z = inp_list[0]
        seq_dict.update({'feat_z': z['feat'], 'mask_z': z['mask'], 'pos_z': z['pos']})
    return seq_dict

def get_lmdb_handle(name):
    global LMDB_HANDLES, LMDB_FILELISTS
    item = LMDB_HANDLES.get(name, None)
    if item is None:
        env = lmdb.open(name, readonly=True, lock=False, readahead=False, meminit=False)
        LMDB_ENVS[name] = env
        item = env.begin(write=False)
        LMDB_HANDLES[name] = item
    return item

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

def _store_outputs(tracker_out: dict, defaults=None):
    defaults = {} if defaults is None else defaults
    for key in output.keys():
        val = tracker_out.get(key, defaults.get(key, None))
        if key in tracker_out or val is not None:
            output[key].append(val)

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

class OSTrack(nn.Module):
    """ This is the base class for OSTrack """

    def __init__(self, transformer, box_head, aux_loss=False, head_type='CORNER'):
        """ Initializes the model.
        Parameters:
            transformer: torch module of the transformer architecture.
            aux_loss: True if auxiliary decoding losses (loss at each decoder layer) are to be used.
        """
        super().__init__()
        self.backbone = transformer
        self.box_head = box_head
        self.aux_loss = aux_loss
        self.head_type = head_type
        if head_type == 'CORNER' or head_type == 'CENTER':
            self.feat_sz_s = int(box_head.feat_sz)
            self.feat_len_s = int(box_head.feat_sz ** 2)
        if self.aux_loss:
            self.box_head = _get_clones(self.box_head, 6)

    def forward(self, template: torch.Tensor, search: torch.Tensor, ce_template_mask=None, ce_keep_rate=None, return_last_attn=False):
        x, aux_dict = self.backbone(z=template, x=search, ce_template_mask=ce_template_mask, ce_keep_rate=ce_keep_rate, return_last_attn=return_last_attn)
        feat_last = x
        if isinstance(x, list):
            feat_last = x[-1]
        out = self.forward_head(feat_last, None)
        out.update(aux_dict)
        out['backbone_feat'] = x
        return out

    def forward_head(self, cat_feature, gt_score_map=None):
        """
        cat_feature: output embeddings of the backbone, it can be (HW1+HW2, B, C) or (HW2, B, C)
        """
        enc_opt = cat_feature[:, -self.feat_len_s:]
        opt = enc_opt.unsqueeze(-1).permute((0, 3, 2, 1)).contiguous()
        bs, Nq, C, HW = opt.size()
        opt_feat = opt.view(-1, C, self.feat_sz_s, self.feat_sz_s)
        if self.head_type == 'CORNER':
            pred_box, score_map = self.box_head(opt_feat, True)
            outputs_coord = box_xyxy_to_cxcywh(pred_box)
            outputs_coord_new = outputs_coord.view(bs, Nq, 4)
            out = {'pred_boxes': outputs_coord_new, 'score_map': score_map}
            return out
        elif self.head_type == 'CENTER':
            score_map_ctr, bbox, size_map, offset_map = self.box_head(opt_feat, gt_score_map)
            outputs_coord = bbox
            outputs_coord_new = outputs_coord.view(bs, Nq, 4)
            out = {'pred_boxes': outputs_coord_new, 'score_map': score_map_ctr, 'size_map': size_map, 'offset_map': offset_map}
            return out
        else:
            raise NotImplementedError

def forward(self, template: torch.Tensor, search: torch.Tensor, ce_template_mask=None, ce_keep_rate=None, return_last_attn=False):
    x, aux_dict = self.backbone(z=template, x=search, ce_template_mask=ce_template_mask, ce_keep_rate=ce_keep_rate, return_last_attn=return_last_attn)
    feat_last = x
    if isinstance(x, list):
        feat_last = x[-1]
    out = self.forward_head(feat_last, None)
    out.update(aux_dict)
    out['backbone_feat'] = x
    return out

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

def check_frequency(self, check_idx):
    if (check_idx % self.batch_freq == 0 or check_idx in self.log_steps) and (check_idx > 0 or self.log_first_step):
        try:
            self.log_steps.pop(0)
        except IndexError as e:
            print(e)
            pass
        return True
    return False

def log_txt_as_img(wh, xc, size=10):
    b = len(xc)
    txts = list()
    for bi in range(b):
        txt = Image.new('RGB', wh, color='white')
        draw = ImageDraw.Draw(txt)
        font = ImageFont.truetype('data/DejaVuSans.ttf', size=size)
        nc = int(40 * (wh[0] / 256))
        lines = '\n'.join((xc[bi][start:start + nc] for start in range(0, len(xc[bi]), nc)))
        try:
            draw.text((0, 0), lines, fill='black', font=font)
        except UnicodeEncodeError:
            print('Cant encode string for logging. Skipping.')
        txt = np.array(txt).transpose(2, 0, 1) / 127.5 - 1.0
        txts.append(txt)
    txts = np.stack(txts)
    txts = torch.tensor(txts)
    return txts

def instantiate_from_config(config):
    if not 'target' in config:
        if config == '__is_first_stage__':
            return None
        elif config == '__is_unconditional__':
            return None
        raise KeyError('Expected key `target` to instantiate.')
    return get_obj_from_str(config['target'])(**config.get('params', dict()))

def _do_parallel_data_prefetch(func, Q, data, idx, idx_to_fn=False):
    if idx_to_fn:
        res = func(data, worker_id=idx)
    else:
        res = func(data)
    Q.put([idx, res])
    Q.put('Done')

def pick_and_pop(keys, d):
    values = list(map(lambda key: d.pop(key), keys))
    return dict(zip(keys, values))

class Struct:

    def __init__(self, **entries):
        self.__dict__.update(entries)

def __init__(self, **entries):
    self.__dict__.update(entries)

def polygon_to_mask(polygon, height, width):
    img = Image.new('L', (width, height), 0)
    ImageDraw.Draw(img).polygon([tuple(p) for p in polygon], outline=1, fill=1)
    mask = np.array(img)
    return mask

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

def __init__(self, config):
    self.config = config
    self.motion_tracking = config.get('motion_tracking', False)

def render(render_opt):
    render_downsample = render_opt.get('render_downsample', 1)
    motion_blur_degree = render_opt.get('motion_blur_degree', 4)
    hdri_file = render_opt['hdri_file']
    intrinsic = render_opt['intrinsic']
    cam2world = render_opt['cam2world']
    background_RGB = render_opt['background_RGB']
    background_depth = render_opt['background_depth']
    set_camera_params(intrinsic, cam2world)
    model_obj_names = []
    car_list = render_opt['cars']
    for car_obj in car_list:
        add_model_params(car_obj)
        model_obj_names.append(car_obj['new_obj_name'])
    add_plane(227)
    set_hdri(hdri_file, None)
    check_mkdir(render_opt['output_dir'])
    render_output_dir = os.path.join(render_opt['output_dir'], render_opt['render_name'])
    check_mkdir(render_output_dir)
    render_output_backup_dir = os.path.join(render_output_dir, 'backup')
    check_mkdir(render_output_backup_dir)
    imageio.imsave(os.path.join(render_output_backup_dir, 'RGB.png'), background_RGB)
    if render_opt['backup_hdri'] == True:
        shutil.copy(hdri_file, os.path.join(render_output_backup_dir, 'hdri.exr'))
    depth_and_occlusion = render_opt['depth_and_occlusion']
    render_scene(render_output_dir, intrinsic, model_obj_names, render_downsample, depth_and_occlusion)
    compose(render_output_dir, background_RGB, background_depth, render_downsample, motion_blur_degree, depth_and_occlusion)

def set_composite_node(output_dir, render_downsample, depth_and_occlusion):
    """
        setup composite node.
    """
    scene = bpy.context.scene
    scene.use_nodes = True
    node_tree = scene.node_tree
    tree_nodes = node_tree.nodes
    tree_nodes.clear()
    render_node = tree_nodes.new('CompositorNodeRLayers')
    render_node.name = 'Render_node'
    render_node.location = (-300, 0)
    transform_node_for_image = tree_nodes.new(type='CompositorNodeTransform')
    transform_node_for_image.location = (300, 400)
    transform_node_for_image.filter_type = 'BILINEAR'
    transform_node_for_image.inputs['Scale'].default_value = 1 / render_downsample
    image_node = tree_nodes.new('CompositorNodeImage')
    image_node.name = 'Image_node'
    image_node.location = (0, 400)
    image_path = os.path.join(output_dir, 'backup', 'RGB.png')
    image_node.image = bpy.data.images.load(image_path)
    image_node.image.colorspace_settings.name = 'Filmic sRGB'
    RGB_output_node = tree_nodes.new('CompositorNodeOutputFile')
    RGB_output_node.name = 'RGB_output_node'
    RGB_output_node.location = (1500, 200)
    RGB_output_node.format.file_format = 'PNG'
    RGB_output_node.format.color_mode = 'RGBA'
    RGB_folder = os.path.join(output_dir, 'RGB')
    RGB_output_node.base_path = RGB_folder
    RGB_output_node.file_slots[0].path = 'vehicle_and_shadow_over_background'
    check_mkdir(RGB_folder)
    if depth_and_occlusion == True:
        depth_output_node = tree_nodes.new('CompositorNodeOutputFile')
        depth_output_node.name = 'Depth_output_node'
        depth_output_node.location = (1500, 0)
        depth_output_node.format.file_format = 'OPEN_EXR'
        depth_output_node.format.color_mode = 'RGBA'
        depth_folder = os.path.join(output_dir, 'depth')
        depth_output_node.base_path = depth_folder
        depth_output_node.file_slots[0].path = 'vehicle_and_plane'
        check_mkdir(depth_folder)
    if depth_and_occlusion == True:
        mask_output_node = tree_nodes.new('CompositorNodeOutputFile')
        mask_output_node.name = 'Mask_output_node'
        mask_output_node.location = (1500, -300)
        mask_output_node.format.file_format = 'OPEN_EXR'
        mask_output_node.format.color_mode = 'RGBA'
        mask_folder = os.path.join(output_dir, 'mask')
        mask_output_node.base_path = mask_folder
        mask_output_node.file_slots[0].path = 'vehicle_and_shadow'
        check_mkdir(mask_folder)
    multiply_node = tree_nodes.new('CompositorNodeMixRGB')
    multiply_node.name = 'Multiply_node'
    multiply_node.blend_type = 'MULTIPLY'
    multiply_node.location = (600, 100)
    alpha_over_node = tree_nodes.new('CompositorNodeAlphaOver')
    alpha_over_node.name = 'Alpha_over_node'
    alpha_over_node.location = (900, 100)
    invert_node = tree_nodes.new('CompositorNodeInvert')
    invert_node.name = 'Invert_node'
    invert_node.location = (300, -300)
    set_alpha_node_1 = tree_nodes.new('CompositorNodeSetAlpha')
    set_alpha_node_1.name = 'Set_alpha_node_1'
    set_alpha_node_1.location = (600, -300)
    set_alpha_node_1.inputs[0].default_value = (1, 1, 1, 1)
    set_alpha_node_2 = tree_nodes.new('CompositorNodeSetAlpha')
    set_alpha_node_2.name = 'Set_alpha_node_2'
    set_alpha_node_2.location = (600, -500)
    set_alpha_node_2.inputs[0].default_value = (1, 1, 1, 1)
    add_node = tree_nodes.new('CompositorNodeMixRGB')
    add_node.name = 'Add_node'
    add_node.blend_type = 'ADD'
    add_node.location = (900, -300)
    add_node.use_clamp = True
    separate_rgba_node = tree_nodes.new(type='CompositorNodeSepRGBA')
    separate_rgba_node.name = 'Seperate_RGBA'
    separate_rgba_node.location = (1200, -300)
    node_tree.links.clear()
    links = node_tree.links
    if depth_and_occlusion == True:
        links.new(render_node.outputs['Depth'], depth_output_node.inputs[0])
    links.new(render_node.outputs['Image'], alpha_over_node.inputs[2])
    links.new(render_node.outputs['Shadow Catcher'], multiply_node.inputs[1])
    links.new(image_node.outputs['Image'], transform_node_for_image.inputs['Image'])
    links.new(transform_node_for_image.outputs['Image'], multiply_node.inputs[2])
    links.new(multiply_node.outputs['Image'], alpha_over_node.inputs[1])
    links.new(alpha_over_node.outputs['Image'], RGB_output_node.inputs[0])
    if depth_and_occlusion == True:
        links.new(render_node.outputs['Alpha'], set_alpha_node_2.inputs['Alpha'])
        links.new(render_node.outputs['Shadow Catcher'], invert_node.inputs['Color'])
        links.new(invert_node.outputs['Color'], set_alpha_node_1.inputs['Alpha'])
        links.new(set_alpha_node_1.outputs['Image'], add_node.inputs[1])
        links.new(set_alpha_node_2.outputs['Image'], add_node.inputs[2])
        links.new(add_node.outputs['Image'], separate_rgba_node.inputs['Image'])
        links.new(separate_rgba_node.outputs['R'], mask_output_node.inputs['Image'])
    return node_tree

def add_model_params(model_setting):
    """
    model_setting includes:
        - blender_file: path to object model file
        - insert_pos: list of len 3
        - insert_rot: list of len 3 
        - model_obj_name: object name within blender_file
        - new_obj_name: object name in this scene
        - target_color: optional .
    """
    blender_file = model_setting['blender_file']
    model_obj_name = model_setting['model_obj_name']
    new_obj_name = model_setting['new_obj_name']
    target_color = model_setting.get('target_color', None)
    with bpy.data.libraries.load(blender_file, link=False) as (data_from, data_to):
        data_to.objects = data_from.objects
    for obj in data_to.objects:
        if obj.name == model_obj_name:
            bpy.context.collection.objects.link(obj)
    if model_obj_name in bpy.data.objects:
        imported_object = bpy.data.objects[model_obj_name]
        imported_object.name = new_obj_name
        print(f'rename {model_obj_name} to {new_obj_name}')
    for slot in imported_object.material_slots:
        material = slot.material
        if material:
            material.name = new_obj_name + '_' + material.name
    if target_color is not None:
        target_color['material_key'] = new_obj_name + '_' + target_color['material_key']
    set_model_params(model_setting['insert_pos'], model_setting['insert_rot'], rot_mode='XYZ', model_obj_name=new_obj_name, target_color=target_color)

def add_plane(size):
    bpy.ops.mesh.primitive_plane_add(size=1)
    if hasattr(bpy.context, 'object'):
        plane = bpy.context.object
    else:
        plane = bpy.data.objects['Plane']
    plane.scale = (size, size, 1)
    plane.name = 'plane'
    plane.is_shadow_catcher = True
    material = bpy.data.materials.new(name='new_plane_material')
    plane.data.materials.append(material)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    BSDF_node = nodes.get('Principled BSDF')
    if BSDF_node:
        BSDF_node.inputs[0].default_value = (0.004, 0.005, 0.006, 1)
        BSDF_node.inputs[9].default_value = 1
        BSDF_node.inputs[21].default_value = 1

