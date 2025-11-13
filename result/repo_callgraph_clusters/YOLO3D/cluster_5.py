# Cluster 5

def main(opt):
    train(**vars(opt))

def main(opt):
    train(**vars(opt))

def exif_size(img):
    s = img.size
    try:
        rotation = dict(img._getexif().items())[orientation]
        if rotation == 6:
            s = (s[1], s[0])
        elif rotation == 8:
            s = (s[1], s[0])
    except:
        pass
    return s

def create_dataloader(path, imgsz, batch_size, stride, single_cls=False, hyp=None, augment=False, cache=False, pad=0.0, rect=False, rank=-1, workers=8, image_weights=False, quad=False, prefix='', shuffle=False):
    if rect and shuffle:
        LOGGER.warning('WARNING: --rect is incompatible with DataLoader shuffle, setting shuffle=False')
        shuffle = False
    with torch_distributed_zero_first(rank):
        dataset = LoadImagesAndLabels(path, imgsz, batch_size, augment=augment, hyp=hyp, rect=rect, cache_images=cache, single_cls=single_cls, stride=int(stride), pad=pad, image_weights=image_weights, prefix=prefix)
    batch_size = min(batch_size, len(dataset))
    nw = min([os.cpu_count() // WORLD_SIZE, batch_size if batch_size > 1 else 0, workers])
    sampler = None if rank == -1 else distributed.DistributedSampler(dataset, shuffle=shuffle)
    loader = DataLoader if image_weights else InfiniteDataLoader
    return (loader(dataset, batch_size=batch_size, shuffle=shuffle and sampler is None, num_workers=nw, sampler=sampler, pin_memory=True, collate_fn=LoadImagesAndLabels.collate_fn4 if quad else LoadImagesAndLabels.collate_fn), dataset)

def create_folder(path='./new'):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)

def check_train_batch_size(model, imgsz=640):
    with amp.autocast():
        return autobatch(deepcopy(model).train(), imgsz)

def notebook_init(verbose=True):
    print('Checking setup...')
    import os
    import shutil
    from utils.general import check_requirements, emojis, is_colab
    from utils.torch_utils import select_device
    check_requirements(('psutil', 'IPython'))
    import psutil
    from IPython import display
    if is_colab():
        shutil.rmtree('/content/sample_data', ignore_errors=True)
    if verbose:
        gib = 1 / 1024 ** 3
        ram = psutil.virtual_memory().total
        total, used, free = shutil.disk_usage('/')
        display.clear_output()
        s = f'({os.cpu_count()} CPUs, {ram * gib:.1f} GB RAM, {(total - free) * gib:.1f}/{total * gib:.1f} GB disk)'
    else:
        s = ''
    select_device(newline=False)
    print(emojis(f'Setup complete ✅ {s}'))
    return display

class Loggers:

    def __init__(self, save_dir=None, weights=None, opt=None, hyp=None, logger=None, include=LOGGERS):
        self.save_dir = save_dir
        self.weights = weights
        self.opt = opt
        self.hyp = hyp
        self.logger = logger
        self.include = include
        self.keys = ['train/box_loss', 'train/obj_loss', 'train/cls_loss', 'metrics/precision', 'metrics/recall', 'metrics/mAP_0.5', 'metrics/mAP_0.5:0.95', 'val/box_loss', 'val/obj_loss', 'val/cls_loss', 'x/lr0', 'x/lr1', 'x/lr2']
        self.best_keys = ['best/epoch', 'best/precision', 'best/recall', 'best/mAP_0.5', 'best/mAP_0.5:0.95']
        for k in LOGGERS:
            setattr(self, k, None)
        self.csv = True
        if not wandb:
            prefix = colorstr('Weights & Biases: ')
            s = f"{prefix}run 'pip install wandb' to automatically track and visualize YOLOv5 🚀 runs (RECOMMENDED)"
            print(emojis(s))
        s = self.save_dir
        if 'tb' in self.include and (not self.opt.evolve):
            prefix = colorstr('TensorBoard: ')
            self.logger.info(f"{prefix}Start with 'tensorboard --logdir {s.parent}', view at http://localhost:6006/")
            self.tb = SummaryWriter(str(s))
        if wandb and 'wandb' in self.include:
            wandb_artifact_resume = isinstance(self.opt.resume, str) and self.opt.resume.startswith('wandb-artifact://')
            run_id = torch.load(self.weights).get('wandb_id') if self.opt.resume and (not wandb_artifact_resume) else None
            self.opt.hyp = self.hyp
            self.wandb = WandbLogger(self.opt, run_id)
        else:
            self.wandb = None

    def on_pretrain_routine_end(self):
        paths = self.save_dir.glob('*labels*.jpg')
        if self.wandb:
            self.wandb.log({'Labels': [wandb.Image(str(x), caption=x.name) for x in paths]})

    def on_train_batch_end(self, ni, model, imgs, targets, paths, plots, sync_bn):
        if plots:
            if ni == 0:
                if not sync_bn:
                    with warnings.catch_warnings():
                        warnings.simplefilter('ignore')
                        self.tb.add_graph(torch.jit.trace(de_parallel(model), imgs[0:1], strict=False), [])
            if ni < 3:
                f = self.save_dir / f'train_batch{ni}.jpg'
                Thread(target=plot_images, args=(imgs, targets, paths, f), daemon=True).start()
            if self.wandb and ni == 10:
                files = sorted(self.save_dir.glob('train*.jpg'))
                self.wandb.log({'Mosaics': [wandb.Image(str(f), caption=f.name) for f in files if f.exists()]})

    def on_train_epoch_end(self, epoch):
        if self.wandb:
            self.wandb.current_epoch = epoch + 1

    def on_val_image_end(self, pred, predn, path, names, im):
        if self.wandb:
            self.wandb.val_one_image(pred, predn, path, names, im)

    def on_val_end(self):
        if self.wandb:
            files = sorted(self.save_dir.glob('val*.jpg'))
            self.wandb.log({'Validation': [wandb.Image(str(f), caption=f.name) for f in files]})

    def on_fit_epoch_end(self, vals, epoch, best_fitness, fi):
        x = {k: v for k, v in zip(self.keys, vals)}
        if self.csv:
            file = self.save_dir / 'results.csv'
            n = len(x) + 1
            s = '' if file.exists() else ('%20s,' * n % tuple(['epoch'] + self.keys)).rstrip(',') + '\n'
            with open(file, 'a') as f:
                f.write(s + ('%20.5g,' * n % tuple([epoch] + vals)).rstrip(',') + '\n')
        if self.tb:
            for k, v in x.items():
                self.tb.add_scalar(k, v, epoch)
        if self.wandb:
            if best_fitness == fi:
                best_results = [epoch] + vals[3:7]
                for i, name in enumerate(self.best_keys):
                    self.wandb.wandb_run.summary[name] = best_results[i]
            self.wandb.log(x)
            self.wandb.end_epoch(best_result=best_fitness == fi)

    def on_model_save(self, last, epoch, final_epoch, best_fitness, fi):
        if self.wandb:
            if ((epoch + 1) % self.opt.save_period == 0 and (not final_epoch)) and self.opt.save_period != -1:
                self.wandb.log_model(last.parent, self.opt, epoch, fi, best_model=best_fitness == fi)

    def on_train_end(self, last, best, plots, epoch, results):
        if plots:
            plot_results(file=self.save_dir / 'results.csv')
        files = ['results.png', 'confusion_matrix.png', *(f'{x}_curve.png' for x in ('F1', 'PR', 'P', 'R'))]
        files = [self.save_dir / f for f in files if (self.save_dir / f).exists()]
        if self.tb:
            import cv2
            for f in files:
                self.tb.add_image(f.stem, cv2.imread(str(f))[..., ::-1], epoch, dataformats='HWC')
        if self.wandb:
            self.wandb.log({k: v for k, v in zip(self.keys[3:10], results)})
            self.wandb.log({'Results': [wandb.Image(str(f), caption=f.name) for f in files]})
            if not self.opt.evolve:
                wandb.log_artifact(str(best if best.exists() else last), type='model', name='run_' + self.wandb.wandb_run.id + '_model', aliases=['latest', 'best', 'stripped'])
                self.wandb.finish_run()
            else:
                self.wandb.finish_run()
                self.wandb = WandbLogger(self.opt)

    def on_params_update(self, params):
        if self.wandb:
            self.wandb.wandb_run.config.update(params, allow_val_change=True)

def on_params_update(self, params):
    if self.wandb:
        self.wandb.wandb_run.config.update(params, allow_val_change=True)

class WandbLogger:
    """Log training runs, datasets, models, and predictions to Weights & Biases.

    This logger sends information to W&B at wandb.ai. By default, this information
    includes hyperparameters, system configuration and metrics, model metrics,
    and basic data metrics and analyses.

    By providing additional command line arguments to train.py, datasets,
    models and predictions can also be logged.

    For more on how this logger is used, see the Weights & Biases documentation:
    https://docs.wandb.com/guides/integrations/yolov5
    """

    def __init__(self, opt, run_id=None, job_type='Training'):
        """
        - Initialize WandbLogger instance
        - Upload dataset if opt.upload_dataset is True
        - Setup trainig processes if job_type is 'Training'

        arguments:
        opt (namespace) -- Commandline arguments for this run
        run_id (str) -- Run ID of W&B run to be resumed
        job_type (str) -- To set the job_type for this run

       """
        self.job_type = job_type
        self.wandb, self.wandb_run = (wandb, None if not wandb else wandb.run)
        self.val_artifact, self.train_artifact = (None, None)
        self.train_artifact_path, self.val_artifact_path = (None, None)
        self.result_artifact = None
        self.val_table, self.result_table = (None, None)
        self.bbox_media_panel_images = []
        self.val_table_path_map = None
        self.max_imgs_to_log = 16
        self.wandb_artifact_data_dict = None
        self.data_dict = None
        if isinstance(opt.resume, str):
            if opt.resume.startswith(WANDB_ARTIFACT_PREFIX):
                entity, project, run_id, model_artifact_name = get_run_info(opt.resume)
                model_artifact_name = WANDB_ARTIFACT_PREFIX + model_artifact_name
                assert wandb, 'install wandb to resume wandb runs'
                self.wandb_run = wandb.init(id=run_id, project=project, entity=entity, resume='allow', allow_val_change=True)
                opt.resume = model_artifact_name
        elif self.wandb:
            self.wandb_run = wandb.init(config=opt, resume='allow', project='YOLOv5' if opt.project == 'runs/train' else Path(opt.project).stem, entity=opt.entity, name=opt.name if opt.name != 'exp' else None, job_type=job_type, id=run_id, allow_val_change=True) if not wandb.run else wandb.run
        if self.wandb_run:
            if self.job_type == 'Training':
                if opt.upload_dataset:
                    if not opt.resume:
                        self.wandb_artifact_data_dict = self.check_and_upload_dataset(opt)
                if opt.resume:
                    if isinstance(opt.resume, str) and opt.resume.startswith(WANDB_ARTIFACT_PREFIX):
                        self.data_dict = dict(self.wandb_run.config.data_dict)
                    else:
                        self.data_dict = check_wandb_dataset(opt.data)
                else:
                    self.data_dict = check_wandb_dataset(opt.data)
                    self.wandb_artifact_data_dict = self.wandb_artifact_data_dict or self.data_dict
                    self.wandb_run.config.update({'data_dict': self.wandb_artifact_data_dict}, allow_val_change=True)
                self.setup_training(opt)
            if self.job_type == 'Dataset Creation':
                self.wandb_run.config.update({'upload_dataset': True})
                self.data_dict = self.check_and_upload_dataset(opt)

    def check_and_upload_dataset(self, opt):
        """
        Check if the dataset format is compatible and upload it as W&B artifact

        arguments:
        opt (namespace)-- Commandline arguments for current run

        returns:
        Updated dataset info dictionary where local dataset paths are replaced by WAND_ARFACT_PREFIX links.
        """
        assert wandb, 'Install wandb to upload dataset'
        config_path = self.log_dataset_artifact(opt.data, opt.single_cls, 'YOLOv5' if opt.project == 'runs/train' else Path(opt.project).stem)
        with open(config_path, errors='ignore') as f:
            wandb_data_dict = yaml.safe_load(f)
        return wandb_data_dict

    def setup_training(self, opt):
        """
        Setup the necessary processes for training YOLO models:
          - Attempt to download model checkpoint and dataset artifacts if opt.resume stats with WANDB_ARTIFACT_PREFIX
          - Update data_dict, to contain info of previous run if resumed and the paths of dataset artifact if downloaded
          - Setup log_dict, initialize bbox_interval

        arguments:
        opt (namespace) -- commandline arguments for this run

        """
        self.log_dict, self.current_epoch = ({}, 0)
        self.bbox_interval = opt.bbox_interval
        if isinstance(opt.resume, str):
            modeldir, _ = self.download_model_artifact(opt)
            if modeldir:
                self.weights = Path(modeldir) / 'last.pt'
                config = self.wandb_run.config
                opt.weights, opt.save_period, opt.batch_size, opt.bbox_interval, opt.epochs, opt.hyp = (str(self.weights), config.save_period, config.batch_size, config.bbox_interval, config.epochs, config.hyp)
        data_dict = self.data_dict
        if self.val_artifact is None:
            self.train_artifact_path, self.train_artifact = self.download_dataset_artifact(data_dict.get('train'), opt.artifact_alias)
            self.val_artifact_path, self.val_artifact = self.download_dataset_artifact(data_dict.get('val'), opt.artifact_alias)
        if self.train_artifact_path is not None:
            train_path = Path(self.train_artifact_path) / 'data/images/'
            data_dict['train'] = str(train_path)
        if self.val_artifact_path is not None:
            val_path = Path(self.val_artifact_path) / 'data/images/'
            data_dict['val'] = str(val_path)
        if self.val_artifact is not None:
            self.result_artifact = wandb.Artifact('run_' + wandb.run.id + '_progress', 'evaluation')
            columns = ['epoch', 'id', 'ground truth', 'prediction']
            columns.extend(self.data_dict['names'])
            self.result_table = wandb.Table(columns)
            self.val_table = self.val_artifact.get('val')
            if self.val_table_path_map is None:
                self.map_val_table_path()
        if opt.bbox_interval == -1:
            self.bbox_interval = opt.bbox_interval = opt.epochs // 10 if opt.epochs > 10 else 1
        train_from_artifact = self.train_artifact_path is not None and self.val_artifact_path is not None
        if train_from_artifact:
            self.data_dict = data_dict

    def download_dataset_artifact(self, path, alias):
        """
        download the model checkpoint artifact if the path starts with WANDB_ARTIFACT_PREFIX

        arguments:
        path -- path of the dataset to be used for training
        alias (str)-- alias of the artifact to be download/used for training

        returns:
        (str, wandb.Artifact) -- path of the downladed dataset and it's corresponding artifact object if dataset
        is found otherwise returns (None, None)
        """
        if isinstance(path, str) and path.startswith(WANDB_ARTIFACT_PREFIX):
            artifact_path = Path(remove_prefix(path, WANDB_ARTIFACT_PREFIX) + ':' + alias)
            dataset_artifact = wandb.use_artifact(artifact_path.as_posix().replace('\\', '/'))
            assert dataset_artifact is not None, "'Error: W&B dataset artifact doesn't exist'"
            datadir = dataset_artifact.download()
            return (datadir, dataset_artifact)
        return (None, None)

    def download_model_artifact(self, opt):
        """
        download the model checkpoint artifact if the resume path starts with WANDB_ARTIFACT_PREFIX

        arguments:
        opt (namespace) -- Commandline arguments for this run
        """
        if opt.resume.startswith(WANDB_ARTIFACT_PREFIX):
            model_artifact = wandb.use_artifact(remove_prefix(opt.resume, WANDB_ARTIFACT_PREFIX) + ':latest')
            assert model_artifact is not None, "Error: W&B model artifact doesn't exist"
            modeldir = model_artifact.download()
            epochs_trained = model_artifact.metadata.get('epochs_trained')
            total_epochs = model_artifact.metadata.get('total_epochs')
            is_finished = total_epochs is None
            assert not is_finished, 'training is finished, can only resume incomplete runs.'
            return (modeldir, model_artifact)
        return (None, None)

    def log_model(self, path, opt, epoch, fitness_score, best_model=False):
        """
        Log the model checkpoint as W&B artifact

        arguments:
        path (Path)   -- Path of directory containing the checkpoints
        opt (namespace) -- Command line arguments for this run
        epoch (int)  -- Current epoch number
        fitness_score (float) -- fitness score for current epoch
        best_model (boolean) -- Boolean representing if the current checkpoint is the best yet.
        """
        model_artifact = wandb.Artifact('run_' + wandb.run.id + '_model', type='model', metadata={'original_url': str(path), 'epochs_trained': epoch + 1, 'save period': opt.save_period, 'project': opt.project, 'total_epochs': opt.epochs, 'fitness_score': fitness_score})
        model_artifact.add_file(str(path / 'last.pt'), name='last.pt')
        wandb.log_artifact(model_artifact, aliases=['latest', 'last', 'epoch ' + str(self.current_epoch), 'best' if best_model else ''])
        LOGGER.info(f'Saving model artifact on epoch {epoch + 1}')

    def log_dataset_artifact(self, data_file, single_cls, project, overwrite_config=False):
        """
        Log the dataset as W&B artifact and return the new data file with W&B links

        arguments:
        data_file (str) -- the .yaml file with information about the dataset like - path, classes etc.
        single_class (boolean)  -- train multi-class data as single-class
        project (str) -- project name. Used to construct the artifact path
        overwrite_config (boolean) -- overwrites the data.yaml file if set to true otherwise creates a new
        file with _wandb postfix. Eg -> data_wandb.yaml

        returns:
        the new .yaml file with artifact links. it can be used to start training directly from artifacts
        """
        upload_dataset = self.wandb_run.config.upload_dataset
        log_val_only = isinstance(upload_dataset, str) and upload_dataset == 'val'
        self.data_dict = check_dataset(data_file)
        data = dict(self.data_dict)
        nc, names = (1, ['item']) if single_cls else (int(data['nc']), data['names'])
        names = {k: v for k, v in enumerate(names)}
        if not log_val_only:
            self.train_artifact = self.create_dataset_table(LoadImagesAndLabels(data['train'], rect=True, batch_size=1), names, name='train') if data.get('train') else None
            if data.get('train'):
                data['train'] = WANDB_ARTIFACT_PREFIX + str(Path(project) / 'train')
        self.val_artifact = self.create_dataset_table(LoadImagesAndLabels(data['val'], rect=True, batch_size=1), names, name='val') if data.get('val') else None
        if data.get('val'):
            data['val'] = WANDB_ARTIFACT_PREFIX + str(Path(project) / 'val')
        path = Path(data_file)
        if not log_val_only:
            path = (path.stem if overwrite_config else path.stem + '_wandb') + '.yaml'
            path = Path('data') / path
            data.pop('download', None)
            data.pop('path', None)
            with open(path, 'w') as f:
                yaml.safe_dump(data, f)
                LOGGER.info(f'Created dataset config file {path}')
        if self.job_type == 'Training':
            if not log_val_only:
                self.wandb_run.log_artifact(self.train_artifact)
            self.wandb_run.use_artifact(self.val_artifact)
            self.val_artifact.wait()
            self.val_table = self.val_artifact.get('val')
            self.map_val_table_path()
        else:
            self.wandb_run.log_artifact(self.train_artifact)
            self.wandb_run.log_artifact(self.val_artifact)
        return path

    def map_val_table_path(self):
        """
        Map the validation dataset Table like name of file -> it's id in the W&B Table.
        Useful for - referencing artifacts for evaluation.
        """
        self.val_table_path_map = {}
        LOGGER.info('Mapping dataset')
        for i, data in enumerate(tqdm(self.val_table.data)):
            self.val_table_path_map[data[3]] = data[0]

    def create_dataset_table(self, dataset: LoadImagesAndLabels, class_to_id: Dict[int, str], name: str='dataset'):
        """
        Create and return W&B artifact containing W&B Table of the dataset.

        arguments:
        dataset -- instance of LoadImagesAndLabels class used to iterate over the data to build Table
        class_to_id -- hash map that maps class ids to labels
        name -- name of the artifact

        returns:
        dataset artifact to be logged or used
        """
        artifact = wandb.Artifact(name=name, type='dataset')
        img_files = tqdm([dataset.path]) if isinstance(dataset.path, str) and Path(dataset.path).is_dir() else None
        img_files = tqdm(dataset.img_files) if not img_files else img_files
        for img_file in img_files:
            if Path(img_file).is_dir():
                artifact.add_dir(img_file, name='data/images')
                labels_path = 'labels'.join(dataset.path.rsplit('images', 1))
                artifact.add_dir(labels_path, name='data/labels')
            else:
                artifact.add_file(img_file, name='data/images/' + Path(img_file).name)
                label_file = Path(img2label_paths([img_file])[0])
                artifact.add_file(str(label_file), name='data/labels/' + label_file.name) if label_file.exists() else None
        table = wandb.Table(columns=['id', 'train_image', 'Classes', 'name'])
        class_set = wandb.Classes([{'id': id, 'name': name} for id, name in class_to_id.items()])
        for si, (img, labels, paths, shapes) in enumerate(tqdm(dataset)):
            box_data, img_classes = ([], {})
            for cls, *xywh in labels[:, 1:].tolist():
                cls = int(cls)
                box_data.append({'position': {'middle': [xywh[0], xywh[1]], 'width': xywh[2], 'height': xywh[3]}, 'class_id': cls, 'box_caption': '%s' % class_to_id[cls]})
                img_classes[cls] = class_to_id[cls]
            boxes = {'ground_truth': {'box_data': box_data, 'class_labels': class_to_id}}
            table.add_data(si, wandb.Image(paths, classes=class_set, boxes=boxes), list(img_classes.values()), Path(paths).name)
        artifact.add(table, name)
        return artifact

    def log_training_progress(self, predn, path, names):
        """
        Build evaluation Table. Uses reference from validation dataset table.

        arguments:
        predn (list): list of predictions in the native space in the format - [xmin, ymin, xmax, ymax, confidence, class]
        path (str): local path of the current evaluation image
        names (dict(int, str)): hash map that maps class ids to labels
        """
        class_set = wandb.Classes([{'id': id, 'name': name} for id, name in names.items()])
        box_data = []
        avg_conf_per_class = [0] * len(self.data_dict['names'])
        pred_class_count = {}
        for *xyxy, conf, cls in predn.tolist():
            if conf >= 0.25:
                cls = int(cls)
                box_data.append({'position': {'minX': xyxy[0], 'minY': xyxy[1], 'maxX': xyxy[2], 'maxY': xyxy[3]}, 'class_id': cls, 'box_caption': f'{names[cls]} {conf:.3f}', 'scores': {'class_score': conf}, 'domain': 'pixel'})
                avg_conf_per_class[cls] += conf
                if cls in pred_class_count:
                    pred_class_count[cls] += 1
                else:
                    pred_class_count[cls] = 1
        for pred_class in pred_class_count.keys():
            avg_conf_per_class[pred_class] = avg_conf_per_class[pred_class] / pred_class_count[pred_class]
        boxes = {'predictions': {'box_data': box_data, 'class_labels': names}}
        id = self.val_table_path_map[Path(path).name]
        self.result_table.add_data(self.current_epoch, id, self.val_table.data[id][1], wandb.Image(self.val_table.data[id][1], boxes=boxes, classes=class_set), *avg_conf_per_class)

    def val_one_image(self, pred, predn, path, names, im):
        """
        Log validation data for one image. updates the result Table if validation dataset is uploaded and log bbox media panel

        arguments:
        pred (list): list of scaled predictions in the format - [xmin, ymin, xmax, ymax, confidence, class]
        predn (list): list of predictions in the native space - [xmin, ymin, xmax, ymax, confidence, class]
        path (str): local path of the current evaluation image
        """
        if self.val_table and self.result_table:
            self.log_training_progress(predn, path, names)
        if len(self.bbox_media_panel_images) < self.max_imgs_to_log and self.current_epoch > 0:
            if self.current_epoch % self.bbox_interval == 0:
                box_data = [{'position': {'minX': xyxy[0], 'minY': xyxy[1], 'maxX': xyxy[2], 'maxY': xyxy[3]}, 'class_id': int(cls), 'box_caption': f'{names[cls]} {conf:.3f}', 'scores': {'class_score': conf}, 'domain': 'pixel'} for *xyxy, conf, cls in pred.tolist()]
                boxes = {'predictions': {'box_data': box_data, 'class_labels': names}}
                self.bbox_media_panel_images.append(wandb.Image(im, boxes=boxes, caption=path.name))

    def log(self, log_dict):
        """
        save the metrics to the logging dictionary

        arguments:
        log_dict (Dict) -- metrics/media to be logged in current step
        """
        if self.wandb_run:
            for key, value in log_dict.items():
                self.log_dict[key] = value

    def end_epoch(self, best_result=False):
        """
        commit the log_dict, model artifacts and Tables to W&B and flush the log_dict.

        arguments:
        best_result (boolean): Boolean representing if the result of this evaluation is best or not
        """
        if self.wandb_run:
            with all_logging_disabled():
                if self.bbox_media_panel_images:
                    self.log_dict['BoundingBoxDebugger'] = self.bbox_media_panel_images
                try:
                    wandb.log(self.log_dict)
                except BaseException as e:
                    LOGGER.info(f'An error occurred in wandb logger. The training will proceed without interruption. More info\n{e}')
                    self.wandb_run.finish()
                    self.wandb_run = None
                self.log_dict = {}
                self.bbox_media_panel_images = []
            if self.result_artifact:
                self.result_artifact.add(self.result_table, 'result')
                wandb.log_artifact(self.result_artifact, aliases=['latest', 'last', 'epoch ' + str(self.current_epoch), 'best' if best_result else ''])
                wandb.log({'evaluation': self.result_table})
                columns = ['epoch', 'id', 'ground truth', 'prediction']
                columns.extend(self.data_dict['names'])
                self.result_table = wandb.Table(columns)
                self.result_artifact = wandb.Artifact('run_' + wandb.run.id + '_progress', 'evaluation')

    def finish_run(self):
        """
        Log metrics if any and finish the current W&B run
        """
        if self.wandb_run:
            if self.log_dict:
                with all_logging_disabled():
                    wandb.log(self.log_dict)
            wandb.run.finish()

def __init__(self, opt, run_id=None, job_type='Training'):
    """
        - Initialize WandbLogger instance
        - Upload dataset if opt.upload_dataset is True
        - Setup trainig processes if job_type is 'Training'

        arguments:
        opt (namespace) -- Commandline arguments for this run
        run_id (str) -- Run ID of W&B run to be resumed
        job_type (str) -- To set the job_type for this run

       """
    self.job_type = job_type
    self.wandb, self.wandb_run = (wandb, None if not wandb else wandb.run)
    self.val_artifact, self.train_artifact = (None, None)
    self.train_artifact_path, self.val_artifact_path = (None, None)
    self.result_artifact = None
    self.val_table, self.result_table = (None, None)
    self.bbox_media_panel_images = []
    self.val_table_path_map = None
    self.max_imgs_to_log = 16
    self.wandb_artifact_data_dict = None
    self.data_dict = None
    if isinstance(opt.resume, str):
        if opt.resume.startswith(WANDB_ARTIFACT_PREFIX):
            entity, project, run_id, model_artifact_name = get_run_info(opt.resume)
            model_artifact_name = WANDB_ARTIFACT_PREFIX + model_artifact_name
            assert wandb, 'install wandb to resume wandb runs'
            self.wandb_run = wandb.init(id=run_id, project=project, entity=entity, resume='allow', allow_val_change=True)
            opt.resume = model_artifact_name
    elif self.wandb:
        self.wandb_run = wandb.init(config=opt, resume='allow', project='YOLOv5' if opt.project == 'runs/train' else Path(opt.project).stem, entity=opt.entity, name=opt.name if opt.name != 'exp' else None, job_type=job_type, id=run_id, allow_val_change=True) if not wandb.run else wandb.run
    if self.wandb_run:
        if self.job_type == 'Training':
            if opt.upload_dataset:
                if not opt.resume:
                    self.wandb_artifact_data_dict = self.check_and_upload_dataset(opt)
            if opt.resume:
                if isinstance(opt.resume, str) and opt.resume.startswith(WANDB_ARTIFACT_PREFIX):
                    self.data_dict = dict(self.wandb_run.config.data_dict)
                else:
                    self.data_dict = check_wandb_dataset(opt.data)
            else:
                self.data_dict = check_wandb_dataset(opt.data)
                self.wandb_artifact_data_dict = self.wandb_artifact_data_dict or self.data_dict
                self.wandb_run.config.update({'data_dict': self.wandb_artifact_data_dict}, allow_val_change=True)
            self.setup_training(opt)
        if self.job_type == 'Dataset Creation':
            self.wandb_run.config.update({'upload_dataset': True})
            self.data_dict = self.check_and_upload_dataset(opt)

def sweep():
    wandb.init()
    hyp_dict = vars(wandb.config).get('_items')
    opt = parse_opt(known=True)
    opt.batch_size = hyp_dict.get('batch_size')
    opt.save_dir = str(increment_path(Path(opt.project) / opt.name, exist_ok=opt.exist_ok or opt.evolve))
    opt.epochs = hyp_dict.get('epochs')
    opt.nosave = True
    opt.data = hyp_dict.get('data')
    opt.weights = str(opt.weights)
    opt.cfg = str(opt.cfg)
    opt.data = str(opt.data)
    opt.hyp = str(opt.hyp)
    opt.project = str(opt.project)
    device = select_device(opt.device, batch_size=opt.batch_size)
    train(hyp_dict, opt, device, callbacks=Callbacks())

def main(opt):
    run(**vars(opt))

class Detections:

    def __init__(self, imgs, pred, files, times=(0, 0, 0, 0), names=None, shape=None):
        super().__init__()
        d = pred[0].device
        gn = [torch.tensor([*(im.shape[i] for i in [1, 0, 1, 0]), 1, 1], device=d) for im in imgs]
        self.imgs = imgs
        self.pred = pred
        self.names = names
        self.files = files
        self.times = times
        self.xyxy = pred
        self.xywh = [xyxy2xywh(x) for x in pred]
        self.xyxyn = [x / g for x, g in zip(self.xyxy, gn)]
        self.xywhn = [x / g for x, g in zip(self.xywh, gn)]
        self.n = len(self.pred)
        self.t = tuple(((times[i + 1] - times[i]) * 1000 / self.n for i in range(3)))
        self.s = shape

    def display(self, pprint=False, show=False, save=False, crop=False, render=False, save_dir=Path('')):
        crops = []
        for i, (im, pred) in enumerate(zip(self.imgs, self.pred)):
            s = f'image {i + 1}/{len(self.pred)}: {im.shape[0]}x{im.shape[1]} '
            if pred.shape[0]:
                for c in pred[:, -1].unique():
                    n = (pred[:, -1] == c).sum()
                    s += f'{n} {self.names[int(c)]}{'s' * (n > 1)}, '
                if show or save or render or crop:
                    annotator = Annotator(im, example=str(self.names))
                    for *box, conf, cls in reversed(pred):
                        label = f'{self.names[int(cls)]} {conf:.2f}'
                        if crop:
                            file = save_dir / 'crops' / self.names[int(cls)] / self.files[i] if save else None
                            crops.append({'box': box, 'conf': conf, 'cls': cls, 'label': label, 'im': save_one_box(box, im, file=file, save=save)})
                        else:
                            annotator.box_label(box, label, color=colors(cls))
                    im = annotator.im
            else:
                s += '(no detections)'
            im = Image.fromarray(im.astype(np.uint8)) if isinstance(im, np.ndarray) else im
            if pprint:
                LOGGER.info(s.rstrip(', '))
            if show:
                im.show(self.files[i])
            if save:
                f = self.files[i]
                im.save(save_dir / f)
                if i == self.n - 1:
                    LOGGER.info(f'Saved {self.n} image{'s' * (self.n > 1)} to {colorstr('bold', save_dir)}')
            if render:
                self.imgs[i] = np.asarray(im)
        if crop:
            if save:
                LOGGER.info(f'Saved results to {save_dir}\n')
            return crops

    def print(self):
        self.display(pprint=True)
        LOGGER.info(f'Speed: %.1fms pre-process, %.1fms inference, %.1fms NMS per image at shape {tuple(self.s)}' % self.t)

    def show(self):
        self.display(show=True)

    def save(self, save_dir='runs/detect/exp'):
        save_dir = increment_path(save_dir, exist_ok=save_dir != 'runs/detect/exp', mkdir=True)
        self.display(save=True, save_dir=save_dir)

    def crop(self, save=True, save_dir='runs/detect/exp'):
        save_dir = increment_path(save_dir, exist_ok=save_dir != 'runs/detect/exp', mkdir=True) if save else None
        return self.display(crop=True, save=save, save_dir=save_dir)

    def render(self):
        self.display(render=True)
        return self.imgs

    def pandas(self):
        new = copy(self)
        ca = ('xmin', 'ymin', 'xmax', 'ymax', 'confidence', 'class', 'name')
        cb = ('xcenter', 'ycenter', 'width', 'height', 'confidence', 'class', 'name')
        for k, c in zip(['xyxy', 'xyxyn', 'xywh', 'xywhn'], [ca, ca, cb, cb]):
            a = [[x[:5] + [int(x[5]), self.names[int(x[5])]] for x in x.tolist()] for x in getattr(self, k)]
            setattr(new, k, [pd.DataFrame(x, columns=c) for x in a])
        return new

    def tolist(self):
        r = range(self.n)
        x = [Detections([self.imgs[i]], [self.pred[i]], [self.files[i]], self.times, self.names, self.s) for i in r]
        return x

    def __len__(self):
        return self.n

def print(self):
    self.display(pprint=True)
    LOGGER.info(f'Speed: %.1fms pre-process, %.1fms inference, %.1fms NMS per image at shape {tuple(self.s)}' % self.t)

def show(self):
    self.display(show=True)

def save(self, save_dir='runs/detect/exp'):
    save_dir = increment_path(save_dir, exist_ok=save_dir != 'runs/detect/exp', mkdir=True)
    self.display(save=True, save_dir=save_dir)

def crop(self, save=True, save_dir='runs/detect/exp'):
    save_dir = increment_path(save_dir, exist_ok=save_dir != 'runs/detect/exp', mkdir=True) if save else None
    return self.display(crop=True, save=save, save_dir=save_dir)

def render(self):
    self.display(render=True)
    return self.imgs

