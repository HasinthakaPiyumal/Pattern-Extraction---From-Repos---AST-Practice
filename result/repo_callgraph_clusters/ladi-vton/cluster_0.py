# Cluster 0

def inversion_adapter(dataset: Literal['dresscode', 'vitonhd']):
    config = AutoConfig.from_pretrained('laion/CLIP-ViT-H-14-laion2B-s32B-b79K')
    text_encoder_config = UNet2DConditionModel.load_config('stabilityai/stable-diffusion-2-inpainting', subfolder='text_encoder')
    inversion_adapter = InversionAdapter(input_dim=config.vision_config.hidden_size, hidden_dim=config.vision_config.hidden_size * 4, output_dim=text_encoder_config['hidden_size'] * 16, num_encoder_layers=1, config=config.vision_config)
    checkpoint_url = f'https://github.com/miccunifi/ladi-vton/releases/download/weights/inversion_adapter_{dataset}.pth'
    inversion_adapter.load_state_dict(torch.hub.load_state_dict_from_url(checkpoint_url, map_location='cpu'))
    return inversion_adapter

def extended_unet(dataset: Literal['dresscode', 'vitonhd']):
    config = UNet2DConditionModel.load_config('stabilityai/stable-diffusion-2-inpainting', subfolder='unet')
    config['in_channels'] = 31
    unet = UNet2DConditionModel.from_config(config)
    checkpoint_url = f'https://github.com/miccunifi/ladi-vton/releases/download/weights/unet_{dataset}.pth'
    unet.load_state_dict(torch.hub.load_state_dict_from_url(checkpoint_url, map_location='cpu'))
    return unet

def emasc(dataset: Literal['dresscode', 'vitonhd']):
    in_feature_channels = [128, 128, 128, 256, 512]
    out_feature_channels = [128, 256, 512, 512, 512]
    emasc = EMASC(in_feature_channels, out_feature_channels, kernel_size=3, padding=1, stride=1, type='nonlinear')
    checkpoint_url = f'https://github.com/miccunifi/ladi-vton/releases/download/weights/emasc_{dataset}.pth'
    emasc.load_state_dict(torch.hub.load_state_dict_from_url(checkpoint_url, map_location='cpu'))
    return emasc

def warping_module(dataset: Literal['dresscode', 'vitonhd']):
    tps = ConvNet_TPS(256, 192, 21, 3)
    refinement = UNetVanilla(n_channels=24, n_classes=3, bilinear=True)
    checkpoint_url = f'https://github.com/miccunifi/ladi-vton/releases/download/weights/warping_{dataset}.pth'
    tps.load_state_dict(torch.hub.load_state_dict_from_url(checkpoint_url, map_location='cpu')['tps'])
    refinement.load_state_dict(torch.hub.load_state_dict_from_url(checkpoint_url, map_location='cpu')['refinement'])
    return (tps, refinement)

def main():
    args = parse_args()
    print(args.exp_name)
    if args.dataset == 'vitonhd' and args.vitonhd_dataroot is None:
        raise ValueError('VitonHD dataroot must be provided')
    if args.dataset == 'dresscode' and args.dresscode_dataroot is None:
        raise ValueError('DressCode dataroot must be provided')
    if args.wandb_log:
        wandb.init(project=args.wandb_project, entity=args.wandb_entity, name=args.exp_name, config=vars(args))
    dataset_output_list = ['c_name', 'im_name', 'cloth', 'image', 'im_cloth', 'im_mask', 'pose_map', 'category']
    if args.dense:
        dataset_output_list.append('dense_uv')
    if args.dataset == 'vitonhd':
        dataset_train = VitonHDDataset(phase='train', outputlist=dataset_output_list, dataroot_path=args.vitonhd_dataroot, size=(args.height, args.width))
    elif args.dataset == 'dresscode':
        dataset_train = DressCodeDataset(dataroot_path=args.dresscode_dataroot, phase='train', outputlist=dataset_output_list, size=(args.height, args.width))
    else:
        raise NotImplementedError('Dataset should be either vitonhd or dresscode')
    dataloader_train = DataLoader(batch_size=args.batch_size, dataset=dataset_train, shuffle=True, num_workers=args.workers)
    if args.dataset == 'vitonhd':
        dataset_test_paired = VitonHDDataset(phase='test', dataroot_path=args.vitonhd_dataroot, outputlist=dataset_output_list, size=(args.height, args.width))
        dataset_test_unpaired = VitonHDDataset(phase='test', order='unpaired', dataroot_path=args.vitonhd_dataroot, outputlist=dataset_output_list, size=(args.height, args.width))
    elif args.dataset == 'dresscode':
        dataset_test_paired = DressCodeDataset(dataroot_path=args.dresscode_dataroot, phase='test', outputlist=dataset_output_list, size=(args.height, args.width))
        dataset_test_unpaired = DressCodeDataset(phase='test', order='unpaired', dataroot_path=args.dresscode_dataroot, outputlist=dataset_output_list, size=(args.height, args.width))
    else:
        raise NotImplementedError('Dataset should be either vitonhd or dresscode')
    dataloader_test_paired = DataLoader(batch_size=args.batch_size, dataset=dataset_test_paired, shuffle=True, num_workers=args.workers, drop_last=True)
    dataloader_test_unpaired = DataLoader(batch_size=args.batch_size, dataset=dataset_test_unpaired, shuffle=True, num_workers=args.workers, drop_last=True)
    input_nc = 5 if args.dense else 21
    n_layer = 3
    tps = ConvNet_TPS(256, 192, input_nc, n_layer).to(device)
    refinement = UNetVanilla(n_channels=8 if args.dense else 24, n_classes=3, bilinear=True).to(device)
    optimizer_tps = torch.optim.Adam(tps.parameters(), lr=args.lr, betas=(0.5, 0.99))
    optimizer_ref = torch.optim.Adam(list(refinement.parameters()), lr=args.lr, betas=(0.5, 0.99))
    scaler = torch.cuda.amp.GradScaler()
    criterion_l1 = nn.L1Loss()
    if args.vgg_weight > 0:
        criterion_vgg = VGGLoss().to(device)
    else:
        criterion_vgg = None
    start_epoch = 0
    if os.path.exists(os.path.join(args.checkpoints_dir, args.exp_name, f'checkpoint_last.pth')):
        print('Loading full checkpoint')
        state_dict = torch.load(os.path.join(args.checkpoints_dir, args.exp_name, f'checkpoint_last.pth'))
        tps.load_state_dict(state_dict['tps'])
        refinement.load_state_dict(state_dict['refinement'])
        optimizer_tps.load_state_dict(state_dict['optimizer_tps'])
        optimizer_ref.load_state_dict(state_dict['optimizer_ref'])
        start_epoch = state_dict['epoch']
        if args.only_extraction:
            print('Extracting warped cloth images...')
            extraction_dataset_paired = torch.utils.data.ConcatDataset([dataset_test_paired, dataset_train])
            extraction_dataloader_paired = DataLoader(batch_size=args.batch_size, dataset=extraction_dataset_paired, shuffle=False, num_workers=args.workers, drop_last=False)
            if args.save_path:
                warped_cloth_root = args.save_path
            else:
                warped_cloth_root = PROJECT_ROOT / 'data'
            save_name_paired = warped_cloth_root / 'warped_cloths' / args.dataset
            extract_images(extraction_dataloader_paired, tps, refinement, save_name_paired, args.height, args.width)
            extraction_dataset = dataset_test_unpaired
            extraction_dataloader_paired = DataLoader(batch_size=args.batch_size, dataset=extraction_dataset, shuffle=False, num_workers=args.workers)
            save_name_unpaired = warped_cloth_root / 'warped_cloths_unpaired' / args.dataset
            extract_images(extraction_dataloader_paired, tps, refinement, save_name_unpaired, args.height, args.width)
            exit()
    if args.only_extraction and (not os.path.exists(os.path.join(args.checkpoints_dir, args.exp_name, f'checkpoint_last.pth'))):
        print('No checkpoint found, before extracting warped cloth images, please train the model first.')
        exit()
    dataset_train.height = 256
    dataset_train.width = 192
    for e in range(start_epoch, args.epochs_tps):
        print(f'Epoch {e}/{args.epochs_tps}')
        print('train')
        train_loss, train_l1_loss, train_const_loss, visual = training_loop_tps(dataloader_train, tps, optimizer_tps, criterion_l1, scaler, args.const_weight)
        print('paired test')
        running_loss, vgg_running_loss, visual = compute_metric(dataloader_test_paired, tps, criterion_l1, criterion_vgg, refinement=None, height=args.height, width=args.width)
        imgs = torchvision.utils.make_grid(torch.cat(visual[0]), nrow=len(visual[0][0]), padding=2, normalize=True, range=None, scale_each=False, pad_value=0)
        print('unpaired test')
        running_loss_unpaired, vgg_running_loss_unpaired, visual = compute_metric(dataloader_test_unpaired, tps, criterion_l1, criterion_vgg, refinement=None, height=args.height, width=args.width)
        imgs_unpaired = torchvision.utils.make_grid(torch.cat(visual[0]), nrow=len(visual[0][0]), padding=2, normalize=True, range=None, scale_each=False, pad_value=0)
        if args.wandb_log:
            wandb.log({'train/loss': train_loss, 'train/l1_loss': train_l1_loss, 'train/const_loss': train_const_loss, 'train/vgg_loss': 0, 'eval/eval_loss_paired': running_loss, 'eval/eval_vgg_loss_paired': vgg_running_loss, 'eval/eval_loss_unpaired': running_loss_unpaired, 'eval/eval_vgg_loss_unpaired': vgg_running_loss_unpaired, 'images_paired': wandb.Image(imgs), 'images_unpaired': wandb.Image(imgs_unpaired)})
        os.makedirs(os.path.join(args.checkpoints_dir, args.exp_name), exist_ok=True)
        torch.save({'epoch': e + 1, 'tps': tps.state_dict(), 'refinement': refinement.state_dict(), 'optimizer_tps': optimizer_tps.state_dict(), 'optimizer_ref': optimizer_ref.state_dict()}, os.path.join(args.checkpoints_dir, args.exp_name, f'checkpoint_last.pth'))
    scaler = torch.cuda.amp.GradScaler()
    dataset_train.height = args.height
    dataset_train.width = args.width
    for e in range(max(start_epoch, args.epochs_tps), max(start_epoch, args.epochs_tps) + args.epochs_refinement):
        print(f'Epoch {e}/{max(start_epoch, args.epochs_tps) + args.epochs_refinement}')
        train_loss, train_l1_loss, train_vgg_loss, visual = training_loop_refinement(dataloader_train, tps, refinement, optimizer_ref, criterion_l1, criterion_vgg, args.l1_weight, args.vgg_weight, scaler, args.height, args.width)
        running_loss, vgg_running_loss, visual = compute_metric(dataloader_test_paired, tps, criterion_l1, criterion_vgg, refinement=refinement, height=args.height, width=args.width)
        imgs = torchvision.utils.make_grid(torch.cat(visual[0]), nrow=len(visual[0][0]), padding=2, normalize=True, range=None, scale_each=False, pad_value=0)
        running_loss_unpaired, vgg_running_loss_unpaired, visual = compute_metric(dataloader_test_unpaired, tps, criterion_l1, criterion_vgg, refinement=refinement, height=args.height, width=args.width)
        imgs_unpaired = torchvision.utils.make_grid(torch.cat(visual[0]), nrow=len(visual[0][0]), padding=2, normalize=True, range=None, scale_each=False, pad_value=0)
        if args.wandb_log:
            wandb.log({'train/loss': train_loss, 'train/l1_loss': train_l1_loss, 'train/const_loss': 0, 'train/vgg_loss': train_vgg_loss, 'eval/eval_loss_paired': running_loss, 'eval/eval_vgg_loss_paired': vgg_running_loss, 'eval/eval_loss_unpaired': running_loss_unpaired, 'eval/eval_vgg_loss_unpaired': vgg_running_loss_unpaired, 'images_paired': wandb.Image(imgs), 'images_unpaired': wandb.Image(imgs_unpaired)})
        os.makedirs(os.path.join(args.checkpoints_dir, args.exp_name), exist_ok=True)
        torch.save({'epoch': e + 1, 'tps': tps.state_dict(), 'refinement': refinement.state_dict(), 'optimizer_tps': optimizer_tps.state_dict(), 'optimizer_ref': optimizer_ref.state_dict()}, os.path.join(args.checkpoints_dir, args.exp_name, f'checkpoint_last.pth'))
    print('Extracting warped cloth images...')
    extraction_dataset_paired = torch.utils.data.ConcatDataset([dataset_test_paired, dataset_train])
    extraction_dataloader_paired = DataLoader(batch_size=args.batch_size, dataset=extraction_dataset_paired, shuffle=False, num_workers=args.workers, drop_last=False)
    if args.save_path:
        warped_cloth_root = args.save_path
    else:
        warped_cloth_root = PROJECT_ROOT / 'data'
    save_name_paired = warped_cloth_root / 'warped_cloths' / args.dataset
    extract_images(extraction_dataloader_paired, tps, refinement, save_name_paired, args.height, args.width)
    extraction_dataset = dataset_test_unpaired
    extraction_dataloader_paired = DataLoader(batch_size=args.batch_size, dataset=extraction_dataset, shuffle=False, num_workers=args.workers)
    save_name_unpaired = warped_cloth_root / 'warped_cloths_unpaired' / args.dataset
    extract_images(extraction_dataloader_paired, tps, refinement, save_name_unpaired, args.height, args.width)

