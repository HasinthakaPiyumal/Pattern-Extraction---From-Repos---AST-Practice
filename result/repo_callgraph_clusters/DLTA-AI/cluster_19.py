# Cluster 19

def count_objects(json_paths, annotation_path):
    import matplotlib.pyplot as plt
    import json
    labels = []
    counts = []
    for i in range(len(json_paths)):
        with open(json_paths[i]) as f:
            labels.append(json_paths[i].split('time_')[-1].split('.')[0].replace('_', ':')[-5:])
            data = json.load(f)
            inner_count = 0
            for j in range(len(data['shapes'])):
                inner_count += 1
            counts.append(inner_count)
        plt.figure(figsize=(20, 12))
        plt.plot(counts)
        plt.title('Number of Objects Over Time')
        plt.tight_layout(pad=3)
        plt.grid()
        plt.xticks(range(len(labels)), labels, rotation=90)
        plt.yticks(range(max(counts) + 1))
        plt.xlabel('Time')
        plt.ylabel('Number of Objects')
        plt.savefig(annotation_path)
        plt.close()
    return annotation_path

def set_random_seed(seed, deterministic=False):
    """Set random seed.

    Args:
        seed (int): Seed to be used.
        deterministic (bool): Whether to set the deterministic option for
            CUDNN backend, i.e., set `torch.backends.cudnn.deterministic`
            to True and `torch.backends.cudnn.benchmark` to False.
            Default: False.
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    if deterministic:
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

def imshow_det_bboxes(img, bboxes=None, labels=None, segms=None, class_names=None, score_thr=0, bbox_color='green', text_color='green', mask_color=None, thickness=2, font_size=8, win_name='', show=True, wait_time=0, out_file=None):
    """Draw bboxes and class labels (with scores) on an image.

    Args:
        img (str | ndarray): The image to be displayed.
        bboxes (ndarray): Bounding boxes (with scores), shaped (n, 4) or
            (n, 5).
        labels (ndarray): Labels of bboxes.
        segms (ndarray | None): Masks, shaped (n,h,w) or None.
        class_names (list[str]): Names of each classes.
        score_thr (float): Minimum score of bboxes to be shown. Default: 0.
        bbox_color (list[tuple] | tuple | str | None): Colors of bbox lines.
           If a single color is given, it will be applied to all classes.
           The tuple of color should be in RGB order. Default: 'green'.
        text_color (list[tuple] | tuple | str | None): Colors of texts.
           If a single color is given, it will be applied to all classes.
           The tuple of color should be in RGB order. Default: 'green'.
        mask_color (list[tuple] | tuple | str | None, optional): Colors of
           masks. If a single color is given, it will be applied to all
           classes. The tuple of color should be in RGB order.
           Default: None.
        thickness (int): Thickness of lines. Default: 2.
        font_size (int): Font size of texts. Default: 13.
        show (bool): Whether to show the image. Default: True.
        win_name (str): The window name. Default: ''.
        wait_time (float): Value of waitKey param. Default: 0.
        out_file (str, optional): The filename to write the image.
            Default: None.

    Returns:
        ndarray: The image with bboxes drawn on it.
    """
    assert bboxes is None or bboxes.ndim == 2, f' bboxes ndim should be 2, but its ndim is {bboxes.ndim}.'
    assert labels.ndim == 1, f' labels ndim should be 1, but its ndim is {labels.ndim}.'
    assert bboxes is None or bboxes.shape[1] == 4 or bboxes.shape[1] == 5, f' bboxes.shape[1] should be 4 or 5, but its {bboxes.shape[1]}.'
    assert bboxes is None or bboxes.shape[0] <= labels.shape[0], 'labels.shape[0] should not be less than bboxes.shape[0].'
    assert segms is None or segms.shape[0] == labels.shape[0], 'segms.shape[0] and labels.shape[0] should have the same length.'
    assert segms is not None or bboxes is not None, 'segms and bboxes should not be None at the same time.'
    img = mmcv.imread(img).astype(np.uint8)
    if score_thr > 0:
        assert bboxes is not None and bboxes.shape[1] == 5
        scores = bboxes[:, -1]
        inds = scores > score_thr
        bboxes = bboxes[inds, :]
        labels = labels[inds]
        if segms is not None:
            segms = segms[inds, ...]
    img = mmcv.bgr2rgb(img)
    width, height = (img.shape[1], img.shape[0])
    img = np.ascontiguousarray(img)
    fig = plt.figure(win_name, frameon=False)
    plt.title(win_name)
    canvas = fig.canvas
    dpi = fig.get_dpi()
    fig.set_size_inches((width + EPS) / dpi, (height + EPS) / dpi)
    plt.subplots_adjust(left=0, right=1, bottom=0, top=1)
    ax = plt.gca()
    ax.axis('off')
    max_label = int(max(labels) if len(labels) > 0 else 0)
    text_palette = palette_val(get_palette(text_color, max_label + 1))
    text_colors = [text_palette[label] for label in labels]
    num_bboxes = 0
    if bboxes is not None:
        num_bboxes = bboxes.shape[0]
        bbox_palette = palette_val(get_palette(bbox_color, max_label + 1))
        colors = [bbox_palette[label] for label in labels[:num_bboxes]]
        draw_bboxes(ax, bboxes, colors, alpha=0.8, thickness=thickness)
        horizontal_alignment = 'left'
        positions = bboxes[:, :2].astype(np.int32) + thickness
        areas = (bboxes[:, 3] - bboxes[:, 1]) * (bboxes[:, 2] - bboxes[:, 0])
        scales = _get_adaptive_scales(areas)
        scores = bboxes[:, 4] if bboxes.shape[1] == 5 else None
        draw_labels(ax, labels[:num_bboxes], positions, scores=scores, class_names=class_names, color=text_colors, font_size=font_size, scales=scales, horizontal_alignment=horizontal_alignment)
    if segms is not None:
        mask_palette = get_palette(mask_color, max_label + 1)
        colors = [mask_palette[label] for label in labels]
        colors = np.array(colors, dtype=np.uint8)
        draw_masks(ax, img, segms, colors, with_edge=True)
        if num_bboxes < segms.shape[0]:
            segms = segms[num_bboxes:]
            horizontal_alignment = 'center'
            areas = []
            positions = []
            for mask in segms:
                _, _, stats, centroids = cv2.connectedComponentsWithStats(mask.astype(np.uint8), connectivity=8)
                largest_id = np.argmax(stats[1:, -1]) + 1
                positions.append(centroids[largest_id])
                areas.append(stats[largest_id, -1])
            areas = np.stack(areas, axis=0)
            scales = _get_adaptive_scales(areas)
            draw_labels(ax, labels[num_bboxes:], positions, class_names=class_names, color=text_colors, font_size=font_size, scales=scales, horizontal_alignment=horizontal_alignment)
    plt.imshow(img)
    stream, _ = canvas.print_to_buffer()
    buffer = np.frombuffer(stream, dtype='uint8')
    if sys.platform == 'darwin':
        width, height = canvas.get_width_height(physical=True)
    img_rgba = buffer.reshape(height, width, 4)
    rgb, alpha = np.split(img_rgba, [3], axis=2)
    img = rgb.astype('uint8')
    img = mmcv.rgb2bgr(img)
    if show:
        if wait_time == 0:
            plt.show()
        else:
            plt.show(block=False)
            plt.pause(wait_time)
    if out_file is not None:
        mmcv.imwrite(img, out_file)
    plt.close()
    return img

@HOOKS.register_module()
class MMDetWandbHook(WandbLoggerHook):
    """Enhanced Wandb logger hook for MMDetection.

    Comparing with the :cls:`mmcv.runner.WandbLoggerHook`, this hook can not
    only automatically log all the metrics but also log the following extra
    information - saves model checkpoints as W&B Artifact, and
    logs model prediction as interactive W&B Tables.

    - Metrics: The MMDetWandbHook will automatically log training
        and validation metrics along with system metrics (CPU/GPU).

    - Checkpointing: If `log_checkpoint` is True, the checkpoint saved at
        every checkpoint interval will be saved as W&B Artifacts.
        This depends on the : class:`mmcv.runner.CheckpointHook` whose priority
        is higher than this hook. Please refer to
        https://docs.wandb.ai/guides/artifacts/model-versioning
        to learn more about model versioning with W&B Artifacts.

    - Checkpoint Metadata: If evaluation results are available for a given
        checkpoint artifact, it will have a metadata associated with it.
        The metadata contains the evaluation metrics computed on validation
        data with that checkpoint along with the current epoch. It depends
        on `EvalHook` whose priority is more than MMDetWandbHook.

    - Evaluation: At every evaluation interval, the `MMDetWandbHook` logs the
        model prediction as interactive W&B Tables. The number of samples
        logged is given by `num_eval_images`. Currently, the `MMDetWandbHook`
        logs the predicted bounding boxes along with the ground truth at every
        evaluation interval. This depends on the `EvalHook` whose priority is
        more than `MMDetWandbHook`. Also note that the data is just logged once
        and subsequent evaluation tables uses reference to the logged data
        to save memory usage. Please refer to
        https://docs.wandb.ai/guides/data-vis to learn more about W&B Tables.

    For more details check out W&B's MMDetection docs:
    https://docs.wandb.ai/guides/integrations/mmdetection

    ```
    Example:
        log_config = dict(
            ...
            hooks=[
                ...,
                dict(type='MMDetWandbHook',
                     init_kwargs={
                         'entity': "YOUR_ENTITY",
                         'project': "YOUR_PROJECT_NAME"
                     },
                     interval=50,
                     log_checkpoint=True,
                     log_checkpoint_metadata=True,
                     num_eval_images=100,
                     bbox_score_thr=0.3)
            ])
    ```

    Args:
        init_kwargs (dict): A dict passed to wandb.init to initialize
            a W&B run. Please refer to https://docs.wandb.ai/ref/python/init
            for possible key-value pairs.
        interval (int): Logging interval (every k iterations). Defaults to 50.
        log_checkpoint (bool): Save the checkpoint at every checkpoint interval
            as W&B Artifacts. Use this for model versioning where each version
            is a checkpoint. Defaults to False.
        log_checkpoint_metadata (bool): Log the evaluation metrics computed
            on the validation data with the checkpoint, along with current
            epoch as a metadata to that checkpoint.
            Defaults to True.
        num_eval_images (int): The number of validation images to be logged.
            If zero, the evaluation won't be logged. Defaults to 100.
        bbox_score_thr (float): Threshold for bounding box scores.
            Defaults to 0.3.
    """

    def __init__(self, init_kwargs=None, interval=50, log_checkpoint=False, log_checkpoint_metadata=False, num_eval_images=100, bbox_score_thr=0.3, **kwargs):
        super(MMDetWandbHook, self).__init__(init_kwargs, interval, **kwargs)
        self.log_checkpoint = log_checkpoint
        self.log_checkpoint_metadata = log_checkpoint and log_checkpoint_metadata
        self.num_eval_images = num_eval_images
        self.bbox_score_thr = bbox_score_thr
        self.log_evaluation = num_eval_images > 0
        self.ckpt_hook: CheckpointHook = None
        self.eval_hook: EvalHook = None

    def import_wandb(self):
        try:
            import wandb
            from wandb import init
            if digit_version(wandb.__version__) < digit_version('0.12.10'):
                warnings.warn(f'The current wandb {wandb.__version__} is lower than v0.12.10 will cause ResourceWarning when calling wandb.log, Please run "pip install --upgrade wandb"')
        except ImportError:
            raise ImportError('Please run "pip install "wandb>=0.12.10"" to install wandb')
        self.wandb = wandb

    @master_only
    def before_run(self, runner):
        super(MMDetWandbHook, self).before_run(runner)
        if runner.meta is not None and runner.meta.get('exp_name', None) is not None:
            src_cfg_path = osp.join(runner.work_dir, runner.meta.get('exp_name', None))
            if osp.exists(src_cfg_path):
                self.wandb.save(src_cfg_path, base_path=runner.work_dir)
                self._update_wandb_config(runner)
        else:
            runner.logger.warning('No meta information found in the runner. ')
        for hook in runner.hooks:
            if isinstance(hook, CheckpointHook):
                self.ckpt_hook = hook
            if isinstance(hook, (EvalHook, DistEvalHook)):
                self.eval_hook = hook
        if self.log_checkpoint:
            if self.ckpt_hook is None:
                self.log_checkpoint = False
                self.log_checkpoint_metadata = False
                runner.logger.warning('To log checkpoint in MMDetWandbHook, `CheckpointHook` isrequired, please check hooks in the runner.')
            else:
                self.ckpt_interval = self.ckpt_hook.interval
        if self.log_evaluation or self.log_checkpoint_metadata:
            if self.eval_hook is None:
                self.log_evaluation = False
                self.log_checkpoint_metadata = False
                runner.logger.warning('To log evaluation or checkpoint metadata in MMDetWandbHook, `EvalHook` or `DistEvalHook` in mmdet is required, please check whether the validation is enabled.')
            else:
                self.eval_interval = self.eval_hook.interval
                self.val_dataset = self.eval_hook.dataloader.dataset
                if self.num_eval_images > len(self.val_dataset):
                    self.num_eval_images = len(self.val_dataset)
                    runner.logger.warning(f'The num_eval_images ({self.num_eval_images}) is greater than the total number of validation samples ({len(self.val_dataset)}). The complete validation dataset will be logged.')
        if self.log_checkpoint_metadata:
            assert self.ckpt_interval % self.eval_interval == 0, f'To log checkpoint metadata in MMDetWandbHook, the interval of checkpoint saving ({self.ckpt_interval}) should be divisible by the interval of evaluation ({self.eval_interval}).'
        if self.log_evaluation:
            self._init_data_table()
            self._add_ground_truth(runner)
            self._log_data_table()

    @master_only
    def after_train_epoch(self, runner):
        super(MMDetWandbHook, self).after_train_epoch(runner)
        if not self.by_epoch:
            return
        if self.log_checkpoint and self.every_n_epochs(runner, self.ckpt_interval) or (self.ckpt_hook.save_last and self.is_last_epoch(runner)):
            if self.log_checkpoint_metadata and self.eval_hook:
                metadata = {'epoch': runner.epoch + 1, **self._get_eval_results()}
            else:
                metadata = None
            aliases = [f'epoch_{runner.epoch + 1}', 'latest']
            model_path = osp.join(self.ckpt_hook.out_dir, f'epoch_{runner.epoch + 1}.pth')
            self._log_ckpt_as_artifact(model_path, aliases, metadata)
        if self.log_evaluation and self.eval_hook._should_evaluate(runner):
            results = self.eval_hook.latest_results
            self._init_pred_table()
            self._log_predictions(results)
            self._log_eval_table(runner.epoch + 1)

    @master_only
    def after_train_iter(self, runner):
        if self.get_mode(runner) == 'train':
            return super(MMDetWandbHook, self).after_train_iter(runner)
        else:
            super(MMDetWandbHook, self).after_train_iter(runner)
        if self.by_epoch:
            return
        if self.log_checkpoint and self.every_n_iters(runner, self.ckpt_interval) or (self.ckpt_hook.save_last and self.is_last_iter(runner)):
            if self.log_checkpoint_metadata and self.eval_hook:
                metadata = {'iter': runner.iter + 1, **self._get_eval_results()}
            else:
                metadata = None
            aliases = [f'iter_{runner.iter + 1}', 'latest']
            model_path = osp.join(self.ckpt_hook.out_dir, f'iter_{runner.iter + 1}.pth')
            self._log_ckpt_as_artifact(model_path, aliases, metadata)
        if self.log_evaluation and self.eval_hook._should_evaluate(runner):
            results = self.eval_hook.latest_results
            self._init_pred_table()
            self._log_predictions(results)
            self._log_eval_table(runner.iter + 1)

    @master_only
    def after_run(self, runner):
        self.wandb.finish()

    def _update_wandb_config(self, runner):
        """Update wandb config."""
        sys.path.append(runner.work_dir)
        config_filename = runner.meta['exp_name'][:-3]
        configs = importlib.import_module(config_filename)
        config_keys = [key for key in dir(configs) if not key.startswith('__')]
        config_dict = {key: getattr(configs, key) for key in config_keys}
        self.wandb.config.update(config_dict)

    def _log_ckpt_as_artifact(self, model_path, aliases, metadata=None):
        """Log model checkpoint as  W&B Artifact.

        Args:
            model_path (str): Path of the checkpoint to log.
            aliases (list): List of the aliases associated with this artifact.
            metadata (dict, optional): Metadata associated with this artifact.
        """
        model_artifact = self.wandb.Artifact(f'run_{self.wandb.run.id}_model', type='model', metadata=metadata)
        model_artifact.add_file(model_path)
        self.wandb.log_artifact(model_artifact, aliases=aliases)

    def _get_eval_results(self):
        """Get model evaluation results."""
        results = self.eval_hook.latest_results
        eval_results = self.val_dataset.evaluate(results, logger='silent', **self.eval_hook.eval_kwargs)
        return eval_results

    def _init_data_table(self):
        """Initialize the W&B Tables for validation data."""
        columns = ['image_name', 'image']
        self.data_table = self.wandb.Table(columns=columns)

    def _init_pred_table(self):
        """Initialize the W&B Tables for model evaluation."""
        columns = ['image_name', 'ground_truth', 'prediction']
        self.eval_table = self.wandb.Table(columns=columns)

    def _add_ground_truth(self, runner):
        from mmdet.datasets.pipelines import LoadImageFromFile
        img_loader = None
        for t in self.val_dataset.pipeline.transforms:
            if isinstance(t, LoadImageFromFile):
                img_loader = t
        if img_loader is None:
            self.log_evaluation = False
            runner.logger.warning('LoadImageFromFile is required to add images to W&B Tables.')
            return
        self.eval_image_indexs = np.arange(len(self.val_dataset))
        np.random.seed(42)
        np.random.shuffle(self.eval_image_indexs)
        self.eval_image_indexs = self.eval_image_indexs[:self.num_eval_images]
        CLASSES = self.val_dataset.CLASSES
        self.class_id_to_label = {id + 1: name for id, name in enumerate(CLASSES)}
        self.class_set = self.wandb.Classes([{'id': id, 'name': name} for id, name in self.class_id_to_label.items()])
        img_prefix = self.val_dataset.img_prefix
        for idx in self.eval_image_indexs:
            img_info = self.val_dataset.data_infos[idx]
            image_name = img_info.get('filename', f'img_{idx}')
            img_height, img_width = (img_info['height'], img_info['width'])
            img_meta = img_loader(dict(img_info=img_info, img_prefix=img_prefix))
            image = mmcv.bgr2rgb(img_meta['img'])
            data_ann = self.val_dataset.get_ann_info(idx)
            bboxes = data_ann['bboxes']
            labels = data_ann['labels']
            masks = data_ann.get('masks', None)
            assert len(bboxes) == len(labels)
            wandb_boxes = self._get_wandb_bboxes(bboxes, labels)
            if masks is not None:
                wandb_masks = self._get_wandb_masks(masks, labels, is_poly_mask=True, height=img_height, width=img_width)
            else:
                wandb_masks = None
            self.data_table.add_data(image_name, self.wandb.Image(image, boxes=wandb_boxes, masks=wandb_masks, classes=self.class_set))

    def _log_predictions(self, results):
        table_idxs = self.data_table_ref.get_index()
        assert len(table_idxs) == len(self.eval_image_indexs)
        for ndx, eval_image_index in enumerate(self.eval_image_indexs):
            result = results[eval_image_index]
            if isinstance(result, tuple):
                bbox_result, segm_result = result
                if isinstance(segm_result, tuple):
                    segm_result = segm_result[0]
            else:
                bbox_result, segm_result = (result, None)
            assert len(bbox_result) == len(self.class_id_to_label)
            bboxes = np.vstack(bbox_result)
            labels = [np.full(bbox.shape[0], i, dtype=np.int32) for i, bbox in enumerate(bbox_result)]
            labels = np.concatenate(labels)
            segms = None
            if segm_result is not None and len(labels) > 0:
                segms = mmcv.concat_list(segm_result)
                segms = mask_util.decode(segms)
                segms = segms.transpose(2, 0, 1)
                assert len(segms) == len(labels)
            if self.bbox_score_thr > 0:
                assert bboxes is not None and bboxes.shape[1] == 5
                scores = bboxes[:, -1]
                inds = scores > self.bbox_score_thr
                bboxes = bboxes[inds, :]
                labels = labels[inds]
                if segms is not None:
                    segms = segms[inds, ...]
            wandb_boxes = self._get_wandb_bboxes(bboxes, labels, log_gt=False)
            if segms is not None:
                wandb_masks = self._get_wandb_masks(segms, labels)
            else:
                wandb_masks = None
            self.eval_table.add_data(self.data_table_ref.data[ndx][0], self.data_table_ref.data[ndx][1], self.wandb.Image(self.data_table_ref.data[ndx][1], boxes=wandb_boxes, masks=wandb_masks, classes=self.class_set))

    def _get_wandb_bboxes(self, bboxes, labels, log_gt=True):
        """Get list of structured dict for logging bounding boxes to W&B.

        Args:
            bboxes (list): List of bounding box coordinates in
                        (minX, minY, maxX, maxY) format.
            labels (int): List of label ids.
            log_gt (bool): Whether to log ground truth or prediction boxes.

        Returns:
            Dictionary of bounding boxes to be logged.
        """
        wandb_boxes = {}
        box_data = []
        for bbox, label in zip(bboxes, labels):
            if not isinstance(label, int):
                label = int(label)
            label = label + 1
            if len(bbox) == 5:
                confidence = float(bbox[4])
                class_name = self.class_id_to_label[label]
                box_caption = f'{class_name} {confidence:.2f}'
            else:
                box_caption = str(self.class_id_to_label[label])
            position = dict(minX=int(bbox[0]), minY=int(bbox[1]), maxX=int(bbox[2]), maxY=int(bbox[3]))
            box_data.append({'position': position, 'class_id': label, 'box_caption': box_caption, 'domain': 'pixel'})
        wandb_bbox_dict = {'box_data': box_data, 'class_labels': self.class_id_to_label}
        if log_gt:
            wandb_boxes['ground_truth'] = wandb_bbox_dict
        else:
            wandb_boxes['predictions'] = wandb_bbox_dict
        return wandb_boxes

    def _get_wandb_masks(self, masks, labels, is_poly_mask=False, height=None, width=None):
        """Get list of structured dict for logging masks to W&B.

        Args:
            masks (list): List of masks.
            labels (int): List of label ids.
            is_poly_mask (bool): Whether the mask is polygonal or not.
                This is true for CocoDataset.
            height (int): Height of the image.
            width (int): Width of the image.

        Returns:
            Dictionary of masks to be logged.
        """
        mask_label_dict = dict()
        for mask, label in zip(masks, labels):
            label = label + 1
            if is_poly_mask:
                if height is not None and width is not None:
                    mask = polygon_to_bitmap(mask, height, width)
            if label not in mask_label_dict.keys():
                mask_label_dict[label] = mask
            else:
                mask_label_dict[label] = np.logical_or(mask_label_dict[label], mask)
        wandb_masks = dict()
        for key, value in mask_label_dict.items():
            value = value.astype(np.uint8)
            value[value > 0] = key
            class_name = self.class_id_to_label[key]
            wandb_masks[class_name] = {'mask_data': value, 'class_labels': self.class_id_to_label}
        return wandb_masks

    def _log_data_table(self):
        """Log the W&B Tables for validation data as artifact and calls
        `use_artifact` on it so that the evaluation table can use the reference
        of already uploaded images.

        This allows the data to be uploaded just once.
        """
        data_artifact = self.wandb.Artifact('val', type='dataset')
        data_artifact.add(self.data_table, 'val_data')
        if not self.wandb.run.offline:
            self.wandb.run.use_artifact(data_artifact)
            data_artifact.wait()
            self.data_table_ref = data_artifact.get('val_data')
        else:
            self.data_table_ref = self.data_table

    def _log_eval_table(self, idx):
        """Log the W&B Tables for model evaluation.

        The table will be logged multiple times creating new version. Use this
        to compare models at different intervals interactively.
        """
        pred_artifact = self.wandb.Artifact(f'run_{self.wandb.run.id}_pred', type='evaluation')
        pred_artifact.add(self.eval_table, 'eval_data')
        if self.by_epoch:
            aliases = ['latest', f'epoch_{idx}']
        else:
            aliases = ['latest', f'iter_{idx}']
        self.wandb.run.log_artifact(pred_artifact, aliases=aliases)

def _add_ground_truth(self, runner):
    from mmdet.datasets.pipelines import LoadImageFromFile
    img_loader = None
    for t in self.val_dataset.pipeline.transforms:
        if isinstance(t, LoadImageFromFile):
            img_loader = t
    if img_loader is None:
        self.log_evaluation = False
        runner.logger.warning('LoadImageFromFile is required to add images to W&B Tables.')
        return
    self.eval_image_indexs = np.arange(len(self.val_dataset))
    np.random.seed(42)
    np.random.shuffle(self.eval_image_indexs)
    self.eval_image_indexs = self.eval_image_indexs[:self.num_eval_images]
    CLASSES = self.val_dataset.CLASSES
    self.class_id_to_label = {id + 1: name for id, name in enumerate(CLASSES)}
    self.class_set = self.wandb.Classes([{'id': id, 'name': name} for id, name in self.class_id_to_label.items()])
    img_prefix = self.val_dataset.img_prefix
    for idx in self.eval_image_indexs:
        img_info = self.val_dataset.data_infos[idx]
        image_name = img_info.get('filename', f'img_{idx}')
        img_height, img_width = (img_info['height'], img_info['width'])
        img_meta = img_loader(dict(img_info=img_info, img_prefix=img_prefix))
        image = mmcv.bgr2rgb(img_meta['img'])
        data_ann = self.val_dataset.get_ann_info(idx)
        bboxes = data_ann['bboxes']
        labels = data_ann['labels']
        masks = data_ann.get('masks', None)
        assert len(bboxes) == len(labels)
        wandb_boxes = self._get_wandb_bboxes(bboxes, labels)
        if masks is not None:
            wandb_masks = self._get_wandb_masks(masks, labels, is_poly_mask=True, height=img_height, width=img_width)
        else:
            wandb_masks = None
        self.data_table.add_data(image_name, self.wandb.Image(image, boxes=wandb_boxes, masks=wandb_masks, classes=self.class_set))

def _log_predictions(self, results):
    table_idxs = self.data_table_ref.get_index()
    assert len(table_idxs) == len(self.eval_image_indexs)
    for ndx, eval_image_index in enumerate(self.eval_image_indexs):
        result = results[eval_image_index]
        if isinstance(result, tuple):
            bbox_result, segm_result = result
            if isinstance(segm_result, tuple):
                segm_result = segm_result[0]
        else:
            bbox_result, segm_result = (result, None)
        assert len(bbox_result) == len(self.class_id_to_label)
        bboxes = np.vstack(bbox_result)
        labels = [np.full(bbox.shape[0], i, dtype=np.int32) for i, bbox in enumerate(bbox_result)]
        labels = np.concatenate(labels)
        segms = None
        if segm_result is not None and len(labels) > 0:
            segms = mmcv.concat_list(segm_result)
            segms = mask_util.decode(segms)
            segms = segms.transpose(2, 0, 1)
            assert len(segms) == len(labels)
        if self.bbox_score_thr > 0:
            assert bboxes is not None and bboxes.shape[1] == 5
            scores = bboxes[:, -1]
            inds = scores > self.bbox_score_thr
            bboxes = bboxes[inds, :]
            labels = labels[inds]
            if segms is not None:
                segms = segms[inds, ...]
        wandb_boxes = self._get_wandb_bboxes(bboxes, labels, log_gt=False)
        if segms is not None:
            wandb_masks = self._get_wandb_masks(segms, labels)
        else:
            wandb_masks = None
        self.eval_table.add_data(self.data_table_ref.data[ndx][0], self.data_table_ref.data[ndx][1], self.wandb.Image(self.data_table_ref.data[ndx][1], boxes=wandb_boxes, masks=wandb_masks, classes=self.class_set))

def plot_num_recall(recalls, proposal_nums):
    """Plot Proposal_num-Recalls curve.

    Args:
        recalls(ndarray or list): shape (k,)
        proposal_nums(ndarray or list): same shape as `recalls`
    """
    if isinstance(proposal_nums, np.ndarray):
        _proposal_nums = proposal_nums.tolist()
    else:
        _proposal_nums = proposal_nums
    if isinstance(recalls, np.ndarray):
        _recalls = recalls.tolist()
    else:
        _recalls = recalls
    import matplotlib.pyplot as plt
    f = plt.figure()
    plt.plot([0] + _proposal_nums, [0] + _recalls)
    plt.xlabel('Proposal num')
    plt.ylabel('Recall')
    plt.axis([0, proposal_nums.max(), 0, 1])
    f.show()

def plot_iou_recall(recalls, iou_thrs):
    """Plot IoU-Recalls curve.

    Args:
        recalls(ndarray or list): shape (k,)
        iou_thrs(ndarray or list): same shape as `recalls`
    """
    if isinstance(iou_thrs, np.ndarray):
        _iou_thrs = iou_thrs.tolist()
    else:
        _iou_thrs = iou_thrs
    if isinstance(recalls, np.ndarray):
        _recalls = recalls.tolist()
    else:
        _recalls = recalls
    import matplotlib.pyplot as plt
    f = plt.figure()
    plt.plot(_iou_thrs + [1.0], _recalls + [0.0])
    plt.xlabel('IoU')
    plt.ylabel('Recall')
    plt.axis([iou_thrs.min(), 1, 0, 1])
    f.show()

def plot_curve(log_dicts, args):
    if args.backend is not None:
        plt.switch_backend(args.backend)
    sns.set_style(args.style)
    legend = args.legend
    if legend is None:
        legend = []
        for json_log in args.json_logs:
            for metric in args.keys:
                legend.append(f'{json_log}_{metric}')
    assert len(legend) == len(args.json_logs) * len(args.keys)
    metrics = args.keys
    num_metrics = len(metrics)
    for i, log_dict in enumerate(log_dicts):
        epochs = list(log_dict.keys())
        for j, metric in enumerate(metrics):
            print(f'plot curve of {args.json_logs[i]}, metric is {metric}')
            if metric not in log_dict[epochs[int(args.eval_interval) - 1]]:
                if 'mAP' in metric:
                    raise KeyError(f'{args.json_logs[i]} does not contain metric {metric}. Please check if "--no-validate" is specified when you trained the model.')
                raise KeyError(f'{args.json_logs[i]} does not contain metric {metric}. Please reduce the log interval in the config so that interval is less than iterations of one epoch.')
            if 'mAP' in metric:
                xs = []
                ys = []
                for epoch in epochs:
                    ys += log_dict[epoch][metric]
                    if 'val' in log_dict[epoch]['mode']:
                        xs.append(epoch)
                plt.xlabel('epoch')
                plt.plot(xs, ys, label=legend[i * num_metrics + j], marker='o')
            else:
                xs = []
                ys = []
                num_iters_per_epoch = log_dict[epochs[0]]['iter'][-2]
                for epoch in epochs:
                    iters = log_dict[epoch]['iter']
                    if log_dict[epoch]['mode'][-1] == 'val':
                        iters = iters[:-1]
                    xs.append(np.array(iters) + (epoch - 1) * num_iters_per_epoch)
                    ys.append(np.array(log_dict[epoch][metric][:len(iters)]))
                xs = np.concatenate(xs)
                ys = np.concatenate(ys)
                plt.xlabel('iter')
                plt.plot(xs, ys, label=legend[i * num_metrics + j], linewidth=0.5)
            plt.legend()
        if args.title is not None:
            plt.title(args.title)
    if args.out is None:
        plt.show()
    else:
        print(f'save curve to: {args.out}')
        plt.savefig(args.out)
        plt.cla()

def makeplot(rs, ps, outDir, class_name, iou_type):
    cs = np.vstack([np.ones((2, 3)), np.array([0.31, 0.51, 0.74]), np.array([0.75, 0.31, 0.3]), np.array([0.36, 0.9, 0.38]), np.array([0.5, 0.39, 0.64]), np.array([1, 0.6, 0])])
    areaNames = ['allarea', 'small', 'medium', 'large']
    types = ['C75', 'C50', 'Loc', 'Sim', 'Oth', 'BG', 'FN']
    for i in range(len(areaNames)):
        area_ps = ps[..., i, 0]
        figure_title = iou_type + '-' + class_name + '-' + areaNames[i]
        aps = [ps_.mean() for ps_ in area_ps]
        ps_curve = [ps_.mean(axis=1) if ps_.ndim > 1 else ps_ for ps_ in area_ps]
        ps_curve.insert(0, np.zeros(ps_curve[0].shape))
        fig = plt.figure()
        ax = plt.subplot(111)
        for k in range(len(types)):
            ax.plot(rs, ps_curve[k + 1], color=[0, 0, 0], linewidth=0.5)
            ax.fill_between(rs, ps_curve[k], ps_curve[k + 1], color=cs[k], label=str(f'[{aps[k]:.3f}]' + types[k]))
        plt.xlabel('recall')
        plt.ylabel('precision')
        plt.xlim(0, 1.0)
        plt.ylim(0, 1.0)
        plt.title(figure_title)
        plt.legend()
        fig.savefig(outDir + f'/{figure_title}.png')
        plt.close(fig)

def makebarplot(rs, ps, outDir, class_name, iou_type):
    areaNames = ['allarea', 'small', 'medium', 'large']
    types = ['C75', 'C50', 'Loc', 'Sim', 'Oth', 'BG', 'FN']
    fig, ax = plt.subplots()
    x = np.arange(len(areaNames))
    width = 0.6
    rects_list = []
    figure_title = iou_type + '-' + class_name + '-' + 'ap bar plot'
    for i in range(len(types) - 1):
        type_ps = ps[i, ..., 0]
        aps = [ps_.mean() for ps_ in type_ps.T]
        rects_list.append(ax.bar(x - width / 2 + (i + 1) * width / len(types), aps, width / len(types), label=types[i]))
    ax.set_ylabel('Mean Average Precision (mAP)')
    ax.set_title(figure_title)
    ax.set_xticks(x)
    ax.set_xticklabels(areaNames)
    ax.legend()
    for rects in rects_list:
        autolabel(ax, rects)
    fig.savefig(outDir + f'/{figure_title}.png')
    plt.close(fig)

def make_gt_area_group_numbers_plot(cocoEval, outDir, verbose=True):
    areaRngLbl2Number = get_gt_area_group_numbers(cocoEval)
    areaRngLbl = areaRngLbl2Number.keys()
    if verbose:
        print('number of annotations per area group:', areaRngLbl2Number)
    fig, ax = plt.subplots()
    x = np.arange(len(areaRngLbl))
    width = 0.6
    figure_title = 'number of annotations per area group'
    rects = ax.bar(x, areaRngLbl2Number.values(), width)
    ax.set_ylabel('Number of annotations')
    ax.set_title(figure_title)
    ax.set_xticks(x)
    ax.set_xticklabels(areaRngLbl)
    autolabel(ax, rects)
    fig.tight_layout()
    fig.savefig(outDir + f'/{figure_title}.png')
    plt.close(fig)

def make_gt_area_histogram_plot(cocoEval, outDir):
    n_bins = 100
    areas = [ann['area'] for ann in cocoEval.cocoGt.anns.values()]
    figure_title = 'gt annotation areas histogram plot'
    fig, ax = plt.subplots()
    ax.hist(np.sqrt(areas), bins=n_bins)
    ax.set_xlabel('Squareroot Area')
    ax.set_ylabel('Number of annotations')
    ax.set_title(figure_title)
    fig.tight_layout()
    fig.savefig(outDir + f'/{figure_title}.png')
    plt.close(fig)

def plot_confusion_matrix(confusion_matrix, labels, save_dir=None, show=True, title='Normalized Confusion Matrix', color_theme='plasma'):
    """Draw confusion matrix with matplotlib.

    Args:
        confusion_matrix (ndarray): The confusion matrix.
        labels (list[str]): List of class names.
        save_dir (str|optional): If set, save the confusion matrix plot to the
            given path. Default: None.
        show (bool): Whether to show the plot. Default: True.
        title (str): Title of the plot. Default: `Normalized Confusion Matrix`.
        color_theme (str): Theme of the matrix color map. Default: `plasma`.
    """
    per_label_sums = confusion_matrix.sum(axis=1)[:, np.newaxis]
    confusion_matrix = confusion_matrix.astype(np.float32) / per_label_sums * 100
    num_classes = len(labels)
    fig, ax = plt.subplots(figsize=(0.5 * num_classes, 0.5 * num_classes * 0.8), dpi=180)
    cmap = plt.get_cmap(color_theme)
    im = ax.imshow(confusion_matrix, cmap=cmap)
    plt.colorbar(mappable=im, ax=ax)
    title_font = {'weight': 'bold', 'size': 12}
    ax.set_title(title, fontdict=title_font)
    label_font = {'size': 10}
    plt.ylabel('Ground Truth Label', fontdict=label_font)
    plt.xlabel('Prediction Label', fontdict=label_font)
    xmajor_locator = MultipleLocator(1)
    xminor_locator = MultipleLocator(0.5)
    ax.xaxis.set_major_locator(xmajor_locator)
    ax.xaxis.set_minor_locator(xminor_locator)
    ymajor_locator = MultipleLocator(1)
    yminor_locator = MultipleLocator(0.5)
    ax.yaxis.set_major_locator(ymajor_locator)
    ax.yaxis.set_minor_locator(yminor_locator)
    ax.grid(True, which='minor', linestyle='-')
    ax.set_xticks(np.arange(num_classes))
    ax.set_yticks(np.arange(num_classes))
    ax.set_xticklabels(labels)
    ax.set_yticklabels(labels)
    ax.tick_params(axis='x', bottom=False, top=True, labelbottom=False, labeltop=True)
    plt.setp(ax.get_xticklabels(), rotation=45, ha='left', rotation_mode='anchor')
    for i in range(num_classes):
        for j in range(num_classes):
            ax.text(j, i, '{}%'.format(int(confusion_matrix[i, j]) if not np.isnan(confusion_matrix[i, j]) else -1), ha='center', va='center', color='w', size=7)
    ax.set_ylim(len(confusion_matrix) - 0.5, -0.5)
    fig.tight_layout()
    if save_dir is not None:
        plt.savefig(os.path.join(save_dir, 'confusion_matrix.png'), format='png')
    if show:
        plt.show()

def test_palette():
    assert vis.palette_val([(1, 2, 3)])[0] == (1 / 255, 2 / 255, 3 / 255)
    palette = [(1, 0, 0), (0, 1, 0), (0, 0, 1)]
    palette_ = vis.get_palette(palette, 3)
    for color, color_ in zip(palette, palette_):
        assert color == color_
    palette = vis.get_palette((1, 2, 3), 3)
    assert len(palette) == 3
    for color in palette:
        assert color == (1, 2, 3)
    palette = vis.get_palette('red', 3)
    assert len(palette) == 3
    for color in palette:
        assert color == (255, 0, 0)
    palette = vis.get_palette('coco', len(CocoDataset.CLASSES))
    assert len(palette) == len(CocoDataset.CLASSES)
    assert palette[0] == (220, 20, 60)
    palette = vis.get_palette('coco', len(CocoPanopticDataset.CLASSES))
    assert len(palette) == len(CocoPanopticDataset.CLASSES)
    assert palette[-1] == (250, 141, 255)
    palette = vis.get_palette('voc', len(VOCDataset.CLASSES))
    assert len(palette) == len(VOCDataset.CLASSES)
    assert palette[0] == (106, 0, 228)
    palette = vis.get_palette('citys', len(CityscapesDataset.CLASSES))
    assert len(palette) == len(CityscapesDataset.CLASSES)
    assert palette[0] == (220, 20, 60)
    palette1 = vis.get_palette('random', 3)
    palette2 = vis.get_palette(None, 3)
    for color1, color2 in zip(palette1, palette2):
        assert isinstance(color1, tuple)
        assert isinstance(color2, tuple)
        assert color1 == color2

def ious(atlbrs, btlbrs):
    """
    Compute cost based on IoU
    :type atlbrs: list[tlbr] | np.ndarray
    :type atlbrs: list[tlbr] | np.ndarray

    :rtype ious np.ndarray
    """
    ious = np.zeros((len(atlbrs), len(btlbrs)), dtype=np.float32)
    if ious.size == 0:
        return ious
    ious = bbox_ious(np.ascontiguousarray(atlbrs, dtype=np.float32), np.ascontiguousarray(btlbrs, dtype=np.float32))
    return ious

def ious(atlbrs, btlbrs):
    """
    Compute cost based on IoU
    :type atlbrs: list[tlbr] | np.ndarray
    :type atlbrs: list[tlbr] | np.ndarray

    :rtype ious np.ndarray
    """
    ious = np.zeros((len(atlbrs), len(btlbrs)), dtype=np.float32)
    if ious.size == 0:
        return ious
    ious = bbox_ious(np.ascontiguousarray(atlbrs, dtype=np.float32), np.ascontiguousarray(btlbrs, dtype=np.float32))
    return ious

