# Cluster 0

def get_parser():
    parser = argparse.ArgumentParser(description='ChatSim argrument parser.')
    parser.add_argument('--config_yaml', '-y', type=str, default='config/waymo-1287.yaml', help='path to config file')
    parser.add_argument('--prompt', '-p', type=str, default='add a straight driving car in the scene', help='language prompt to ChatSim.')
    parser.add_argument('--simulation_name', '-s', type=str, default='demo', help='simulation experiment name.')
    args = parser.parse_args()
    return args

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tfrecord_dir', type=str)
    parser.add_argument('--nerf_data_dir', type=str)
    parser.add_argument('-nd', '--no_data', action='store_true')
    parser.add_argument('--frame_nums', type=int, default=60)
    parser.add_argument('--start_frame', type=int, default=0)
    return parser.parse_args()

def setup_args(parser):
    parser.add_argument('--input_img', type=str, required=True, help='Path to a single input img')
    parser.add_argument('--point_coords', type=float, nargs='+', required=True, help='The coordinate of the point prompt, [coord_W coord_H].')
    parser.add_argument('--point_labels', type=int, nargs='+', required=True, help='The labels of the point prompt, 1 or 0.')
    parser.add_argument('--dilate_kernel_size', type=int, default=None, help='Dilate kernel size. Default: None')
    parser.add_argument('--output_dir', type=str, required=True, help='Output path to the directory with results.')
    parser.add_argument('--sam_model_type', type=str, default='vit_h', choices=['vit_h', 'vit_l', 'vit_b'], help="The type of sam model to load. Default: 'vit_h")
    parser.add_argument('--sam_ckpt', type=str, required=True, help='The path to the SAM checkpoint to use for mask generation.')

def setup_args(parser):
    parser.add_argument('--input_img', type=str, required=True, help='Path to a single input img')
    parser.add_argument('--coords_type', type=str, required=True, default='key_in', choices=['click', 'key_in'], help='The way to select coords')
    parser.add_argument('--point_coords', type=float, nargs='+', required=True, help='The coordinate of the point prompt, [coord_W coord_H].')
    parser.add_argument('--point_labels', type=int, nargs='+', required=True, help='The labels of the point prompt, 1 or 0.')
    parser.add_argument('--dilate_kernel_size', type=int, default=None, help='Dilate kernel size. Default: None')
    parser.add_argument('--output_dir', type=str, required=True, help='Output path to the directory with results.')
    parser.add_argument('--sam_model_type', type=str, default='vit_h', choices=['vit_h', 'vit_l', 'vit_b', 'vit_t'], help="The type of sam model to load. Default: 'vit_h")
    parser.add_argument('--sam_ckpt', type=str, required=True, help='The path to the SAM checkpoint to use for mask generation.')
    parser.add_argument('--lama_config', type=str, default='./lama/configs/prediction/default.yaml', help='The path to the config file of lama model. Default: the config of big-lama')
    parser.add_argument('--lama_ckpt', type=str, required=True, help='The path to the lama checkpoint.')

def setup_args(parser):
    parser.add_argument('--input_img', type=str, required=True, help='Path to a single input img')
    parser.add_argument('--coords_type', type=str, required=True, default='key_in', choices=['click', 'key_in'], help='The way to select coords')
    parser.add_argument('--point_coords', type=float, nargs='+', required=True, help='The coordinate of the point prompt, [coord_W coord_H].')
    parser.add_argument('--point_labels', type=int, nargs='+', required=True, help='The labels of the point prompt, 1 or 0.')
    parser.add_argument('--text_prompt', type=str, required=True, help='Text prompt')
    parser.add_argument('--dilate_kernel_size', type=int, default=None, help='Dilate kernel size. Default: None')
    parser.add_argument('--output_dir', type=str, required=True, help='Output path to the directory with results.')
    parser.add_argument('--sam_model_type', type=str, default='vit_h', choices=['vit_h', 'vit_l', 'vit_b', 'vit_t'], help="The type of sam model to load. Default: 'vit_h")
    parser.add_argument('--sam_ckpt', type=str, required=True, help='The path to the SAM checkpoint to use for mask generation.')
    parser.add_argument('--seed', type=int, help='Specify seed for reproducibility.')
    parser.add_argument('--deterministic', action='store_true', help='Use deterministic algorithms for reproducibility.')

def setup_args(parser):
    parser.add_argument('--input_img', type=str, required=True, help='Path to a single input img')
    parser.add_argument('--text_prompt', type=str, required=True, help='Text prompt')
    parser.add_argument('--input_mask_glob', type=str, required=True, help='Glob to input masks')
    parser.add_argument('--output_dir', type=str, required=True, help='Output path to the directory with results.')
    parser.add_argument('--seed', type=int, help='Specify seed for reproducibility.')
    parser.add_argument('--deterministic', action='store_true', help='Use deterministic algorithms for reproducibility.')

def setup_args(parser):
    parser.add_argument('--dilate_kernel_size', type=int, default=None, help='Dilate kernel size. Default: None')
    parser.add_argument('--lama_config', type=str, default='./lama/configs/prediction/default.yaml', help='The path to the config file of lama model. Default: the config of big-lama')
    parser.add_argument('--lama_ckpt', type=str, required=True, help='The path to the lama checkpoint.')
    parser.add_argument('--tracker_ckpt', type=str, required=True, help='The path to tracker checkpoint.')
    parser.add_argument('--vi_ckpt', type=str, required=True, help='The path to video inpainter checkpoint.')
    parser.add_argument('--mask_idx', type=int, default=2, required=True, help='Which mask in the first frame to determine the inpaint region.')
    parser.add_argument('--fps', type=int, default=25, required=True, help='FPS of the input and output videos.')

def setup_args(parser):
    parser.add_argument('--input_img', type=str, required=True, help='Path to a single input img')
    parser.add_argument('--input_mask_glob', type=str, required=True, help='Glob to input masks')
    parser.add_argument('--output_dir', type=str, required=True, help='Output path to the directory with results.')
    parser.add_argument('--lama_config', type=str, default='./lama/configs/prediction/default.yaml', help='The path to the config file of lama model. Default: the config of big-lama')
    parser.add_argument('--lama_ckpt', type=str, required=True, help='The path to the lama checkpoint.')

def setup_args(parser):
    parser.add_argument('--input_img', type=str, required=True, help='Path to a single input img')
    parser.add_argument('--coords_type', type=str, required=True, default='key_in', choices=['click', 'key_in'], help='The way to select coords')
    parser.add_argument('--point_coords', type=float, nargs='+', required=True, help='The coordinate of the point prompt, [coord_W coord_H].')
    parser.add_argument('--point_labels', type=int, nargs='+', required=True, help='The labels of the point prompt, 1 or 0.')
    parser.add_argument('--text_prompt', type=str, required=True, help='Text prompt')
    parser.add_argument('--dilate_kernel_size', type=int, default=None, help='Dilate kernel size. Default: None')
    parser.add_argument('--output_dir', type=str, required=True, help='Output path to the directory with results.')
    parser.add_argument('--sam_model_type', type=str, default='vit_h', choices=['vit_h', 'vit_l', 'vit_b', 'vit_t'], help="The type of sam model to load. Default: 'vit_h")
    parser.add_argument('--sam_ckpt', type=str, required=True, help='The path to the SAM checkpoint to use for mask generation.')
    parser.add_argument('--seed', type=int, help='Specify seed for reproducibility.')
    parser.add_argument('--deterministic', action='store_true', help='Use deterministic algorithms for reproducibility.')

def setup_args(parser):
    parser.add_argument('-v', '--video_p', type=str, required=True)
    parser.add_argument('-m', '--mask_dir', type=str, required=True)
    parser.add_argument('-o', '--output_dir', type=str, required=True)
    parser.add_argument('-c', '--ckpt_p', type=str, required=True)
    parser.add_argument('--model', type=str, default='sttn')

def setup_args(parser):
    parser.add_argument('--input_video', type=str, required=True, help='Path to a single input video')
    parser.add_argument('--coords_type', type=str, required=True, default='key_in', choices=['click', 'key_in'], help='The way to select coords')
    parser.add_argument('--point_coords', type=float, nargs='+', required=True, help='The coordinate of the point prompt, [coord_W coord_H].')
    parser.add_argument('--point_labels', type=int, nargs='+', required=True, help='The labels of the point prompt, 1 or 0.')
    parser.add_argument('--dilate_kernel_size', type=int, default=None, help='Dilate kernel size. Default: None')
    parser.add_argument('--output_dir', type=str, required=True, help='Output path to the directory with results.')
    parser.add_argument('--sam_model_type', type=str, default='vit_h', choices=['vit_h', 'vit_l', 'vit_b', 'vit_t'], help="The type of sam model to load. Default: 'vit_h")
    parser.add_argument('--sam_ckpt', type=str, required=True, help='The path to the SAM checkpoint to use for mask generation.')
    parser.add_argument('--lama_config', type=str, default='./lama/configs/prediction/default.yaml', help='The path to the config file of lama model. Default: the config of big-lama')
    parser.add_argument('--lama_ckpt', type=str, required=True, help='The path to the lama checkpoint.')
    parser.add_argument('--tracker_ckpt', type=str, required=True, help='The path to tracker checkpoint.')
    parser.add_argument('--vi_ckpt', type=str, required=True, help='The path to video inpainter checkpoint.')
    parser.add_argument('--mask_idx', type=int, default=2, required=True, help='Which mask in the first frame to determine the inpaint region.')
    parser.add_argument('--fps', type=int, default=25, required=True, help='FPS of the input and output videos.')

def build_ostrack_model(tracker_param):
    tracker = Tracker('ostrack', tracker_param, 'inpaint-videos')
    return tracker

def setup_args(parser):
    parser.add_argument('--lama_config', type=str, default='./lama/configs/prediction/default.yaml', help='The path to the config file of lama model. Default: the config of big-lama')
    parser.add_argument('--lama_ckpt', type=str, default='pretrained_models/big-lama', help='The path to the lama checkpoint.')
    parser.add_argument('--sam_ckpt', type=str, default='./pretrained_models/sam_vit_h_4b8939.pth', help='The path to the SAM checkpoint to use for mask generation.')

def setup_args(parser):
    parser.add_argument('--input_img', type=str, required=True, help='Path to a single input img')
    parser.add_argument('--input_mask_glob', type=str, required=True, help='Glob to input masks')
    parser.add_argument('--output_dir', type=str, required=True, help='Output path to the directory with results.')

def trackerlist(name: str, parameter_name: str, dataset_name: str, run_ids=None, display_name: str=None, result_only=False):
    """Generate list of trackers.
    args:
        name: Name of tracking method.
        parameter_name: Name of parameter file.
        run_ids: A single or list of run_ids.
        display_name: Name to be displayed in the result plots.
    """
    if run_ids is None or isinstance(run_ids, int):
        run_ids = [run_ids]
    return [Tracker(name, parameter_name, dataset_name, run_id, display_name, result_only) for run_id in run_ids]

def run_tracker(tracker_name, tracker_param, run_id=None, dataset_name='otb', sequence=None, debug=0, threads=0, num_gpus=8):
    """Run tracker on sequence or dataset.
    args:
        tracker_name: Name of tracking method.
        tracker_param: Name of parameter file.
        run_id: The run id.
        dataset_name: Name of dataset (otb, nfs, uav, tpl, vot, tn, gott, gotv, lasot).
        sequence: Sequence number or name.
        debug: Debug level.
        threads: Number of threads.
    """
    dataset = get_dataset(*dataset_name)
    if sequence is not None:
        dataset = [dataset[sequence]]
    trackers = [Tracker(tracker_name, tracker_param, dataset_name, run_id)]
    run_dataset(dataset, trackers, debug, threads, num_gpus=num_gpus)

def main():
    parser = argparse.ArgumentParser(description='Run tracker on sequence or dataset.')
    parser.add_argument('tracker_name', type=str, help='Name of tracking method.')
    parser.add_argument('tracker_param', type=str, help='Name of config file.')
    parser.add_argument('--runid', type=int, default=None, help='The run id.')
    parser.add_argument('--dataset_name', type=str, default='otb', help='Name of dataset (otb, nfs, uav, tpl, vot, tn, gott, gotv, lasot).')
    parser.add_argument('--sequence', type=str, default=None, help='Sequence number or name.')
    parser.add_argument('--debug', type=int, default=0, help='Debug level.')
    parser.add_argument('--threads', type=int, default=0, help='Number of threads.')
    parser.add_argument('--num_gpus', type=int, default=8)
    args = parser.parse_args()
    try:
        seq_name = int(args.sequence)
    except:
        seq_name = args.sequence
    args.dataset_name = ['trackingnet', 'got10k_test', 'lasot']
    run_tracker(args.tracker_name, args.tracker_param, args.runid, args.dataset_name, seq_name, args.debug, args.threads, num_gpus=args.num_gpus)

def run_video(tracker_name, tracker_param, videofile, optional_box=None, debug=None, save_results=False):
    """Run the tracker on your webcam.
    args:
        tracker_name: Name of tracking method.
        tracker_param: Name of parameter file.
        debug: Debug level.
    """
    tracker = Tracker(tracker_name, tracker_param, 'video')
    tracker.run_video(videofilepath=videofile, optional_box=optional_box, debug=debug, save_results=save_results)

def main():
    parser = argparse.ArgumentParser(description='Run the tracker on your webcam.')
    parser.add_argument('tracker_name', type=str, help='Name of tracking method.')
    parser.add_argument('tracker_param', type=str, help='Name of parameter file.')
    parser.add_argument('videofile', type=str, help='path to a video file.')
    parser.add_argument('--optional_box', type=float, default=None, nargs='+', help='optional_box with format x y w h.')
    parser.add_argument('--debug', type=int, default=0, help='Debug level.')
    parser.add_argument('--save_results', dest='save_results', action='store_true', help='Save bounding boxes')
    parser.set_defaults(save_results=False)
    args = parser.parse_args()
    run_video(args.tracker_name, args.tracker_param, args.videofile, args.optional_box, args.debug, args.save_results)

def parse_args():
    """
    args for training.
    """
    parser = argparse.ArgumentParser(description='Parse args for training')
    parser.add_argument('--script', type=str, default='ostrack', choices=['ostrack'], help='training script name')
    parser.add_argument('--config', type=str, default='vitb_256_mae_ce_32x4_ep300', help='yaml configure file name')
    args = parser.parse_args()
    return args

def run_tracker(tracker_name, tracker_param, run_id=None, dataset_name='otb', sequence=None, debug=0, threads=0, num_gpus=8):
    """Run tracker on sequence or dataset.
    args:
        tracker_name: Name of tracking method.
        tracker_param: Name of parameter file.
        run_id: The run id.
        dataset_name: Name of dataset (otb, nfs, uav, tpl, vot, tn, gott, gotv, lasot).
        sequence: Sequence number or name.
        debug: Debug level.
        threads: Number of threads.
    """
    dataset = get_dataset(dataset_name)
    if sequence is not None:
        dataset = [dataset[sequence]]
    trackers = [Tracker(tracker_name, tracker_param, dataset_name, run_id)]
    run_dataset(dataset, trackers, debug, threads, num_gpus=num_gpus)

def main():
    parser = argparse.ArgumentParser(description='Run tracker on sequence or dataset.')
    parser.add_argument('tracker_name', type=str, help='Name of tracking method.')
    parser.add_argument('tracker_param', type=str, help='Name of config file.')
    parser.add_argument('--runid', type=int, default=None, help='The run id.')
    parser.add_argument('--dataset_name', type=str, default='otb', help='Name of dataset (otb, nfs, uav, tpl, vot, tn, gott, gotv, lasot).')
    parser.add_argument('--sequence', type=str, default=None, help='Sequence number or name.')
    parser.add_argument('--debug', type=int, default=0, help='Debug level.')
    parser.add_argument('--threads', type=int, default=0, help='Number of threads.')
    parser.add_argument('--num_gpus', type=int, default=8)
    args = parser.parse_args()
    try:
        seq_name = int(args.sequence)
    except:
        seq_name = args.sequence
    run_tracker(args.tracker_name, args.tracker_param, args.runid, args.dataset_name, seq_name, args.debug, args.threads, num_gpus=args.num_gpus)

def run_video(tracker_param, videofile, optional_box=None, debug=None, save_results=False):
    """Run the tracker on your webcam.
    args:
        tracker_param: Name of parameter file.
        debug: Debug level.
    """
    tracker = Tracker('ostrack', tracker_param, 'video')
    tracker.run_video(videofilepath=videofile, optional_box=optional_box, debug=debug, save_results=save_results)

def get_parser(**parser_kwargs):

    def str2bool(v):
        if isinstance(v, bool):
            return v
        if v.lower() in ('yes', 'true', 't', 'y', '1'):
            return True
        elif v.lower() in ('no', 'false', 'f', 'n', '0'):
            return False
        else:
            raise argparse.ArgumentTypeError('Boolean value expected.')
    parser = argparse.ArgumentParser(**parser_kwargs)
    parser.add_argument('-n', '--name', type=str, const=True, default='', nargs='?', help='postfix for logdir')
    parser.add_argument('-r', '--resume', type=str, const=True, default='', nargs='?', help='resume from logdir or checkpoint in logdir')
    parser.add_argument('-b', '--base', nargs='*', metavar='base_config.yaml', help='paths to base configs. Loaded from left-to-right. Parameters can be overwritten or added with command-line options of the form `--key value`.', default=list())
    parser.add_argument('-t', '--train', type=str2bool, const=True, default=False, nargs='?', help='train')
    parser.add_argument('--no-test', type=str2bool, const=True, default=False, nargs='?', help='disable test')
    parser.add_argument('-p', '--project', help='name of new or path to existing project')
    parser.add_argument('-d', '--debug', type=str2bool, nargs='?', const=True, default=False, help='enable post-mortem debugging')
    parser.add_argument('-s', '--seed', type=int, default=23, help='seed for seed_everything')
    parser.add_argument('-f', '--postfix', type=str, default='', help='post-postfix for default name')
    parser.add_argument('-l', '--logdir', type=str, default='logs', help='directory for logging dat shit')
    parser.add_argument('--scale_lr', type=str2bool, nargs='?', const=True, default=True, help='scale base-lr by ngpu * batch_size * n_accumulate')
    return parser

def nondefault_trainer_args(opt):
    parser = argparse.ArgumentParser()
    parser = Trainer.add_argparse_args(parser)
    args = parser.parse_args([])
    return sorted((k for k in vars(args) if getattr(opt, k) != getattr(args, k)))

def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--resume', type=str, nargs='?', help='load from logdir or checkpoint in logdir')
    parser.add_argument('-n', '--n_samples', type=int, nargs='?', help='number of samples to draw', default=50000)
    parser.add_argument('-e', '--eta', type=float, nargs='?', help='eta for ddim sampling (0.0 yields deterministic sampling)', default=1.0)
    parser.add_argument('-v', '--vanilla_sample', default=False, action='store_true', help='vanilla sampling (default option is DDIM sampling)?')
    parser.add_argument('-l', '--logdir', type=str, nargs='?', help='extra logdir', default='none')
    parser.add_argument('-c', '--custom_steps', type=int, nargs='?', help='number of steps for ddim and fastdpm sampling', default=50)
    parser.add_argument('--batch_size', type=int, nargs='?', help='the bs', default=10)
    return parser

def get_parser():
    parser = argparse.ArgumentParser(description='Example argparse program')
    parser.add_argument('--config', '-y', type=str, help='path to config file')
    parser.add_argument('--ckpt_path', '-c', type=str, default=None, help='path to ckpt file for restore training')
    parser.add_argument('--load_weight_only', action='store_true', help='only load weight from ckpt for model')
    args = parser.parse_args()
    return args

def get_parser():
    parser = argparse.ArgumentParser(description='Example argparse program')
    parser.add_argument('--config', '-y', type=str, help='path to config file')
    parser.add_argument('--ckpt_path', '-c', type=str, default=None, help='path to ckpt file for restore training')
    parser.add_argument('--waymo_scenes_dir', '-w', type=str, default='/home/yfl/workspace/f2-nerf/data/waymo_multi_view', help='path to image directory')
    parser.add_argument('--output_dir', '-o', type=str, help='path to store hdr panorama')
    args = parser.parse_args()
    return args

def get_parser():
    parser = argparse.ArgumentParser(description='Example argparse program')
    parser.add_argument('--config', '-y', type=str, help='path to config file')
    parser.add_argument('--ckpt_path', '-c', type=str, default=None, help='path to ckpt file for restore training')
    parser.add_argument('--image_dir', '-i', type=str, help='path to image directory')
    parser.add_argument('--output_dir', '-o', type=str, help='path to store hdr panorama')
    args = parser.parse_args()
    return args

def get_parser():
    parser = argparse.ArgumentParser(description='Example argparse program')
    parser.add_argument('--config', '-y', type=str, help='path to config file')
    parser.add_argument('--ckpt_path', '-c', type=str, default=None, help='path to ckpt file for restore training')
    args = parser.parse_args()
    return args

def get_parser():
    parser = argparse.ArgumentParser(description='Example argparse program')
    parser.add_argument('--config', '-y', type=str, help='path to config file')
    parser.add_argument('--ckpt_path', '-c', type=str, help='checkpoint path', required=True)
    parser.add_argument('--target_dir', type=str, help='output directory for estimated hdri', required=True)
    parser.add_argument('--holicity_sky_data', type=str, help='directory of resized sky holicity dataset', default='dataset/holicity_pano_sky_resized_64')
    parser.add_argument('--selected_sample_json', type=str, help='path to selected sample json file', default='dataset/holicity_meta_info/selected_sample.json')
    args = parser.parse_args()
    return args

