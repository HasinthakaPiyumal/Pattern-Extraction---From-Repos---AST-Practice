# Cluster 1

def main():
    version = get_version()
    if sys.argv[1] == 'release':
        if not distutils.spawn.find_executable('twine'):
            print('Please install twine:\n\n\tpip install twine\n', file=sys.stderr)
            sys.exit(1)
        commands = ['python tests/docs_tests/man_tests/test_labelme_1.py', 'git tag v{:s}'.format(version), 'git push origin master --tag', 'python setup.py sdist', 'twine upload dist/labelme-{:s}.tar.gz'.format(version)]
        for cmd in commands:
            print('+ {:s}'.format(cmd))
            subprocess.check_call(shlex.split(cmd))
        sys.exit(0)
    setup(name='labelme', version=version, packages=find_packages(exclude=['github2pypi']), description='Image Polygonal Annotation with Python', long_description=get_long_description(), long_description_content_type='text/markdown', author='Kentaro Wada', author_email='www.kentaro.wada@gmail.com', url='https://github.com/wkentaro/labelme', install_requires=get_install_requires(), license='GPLv3', keywords='Image Annotation, Machine Learning', classifiers=['Development Status :: 5 - Production/Stable', 'Intended Audience :: Developers', 'Natural Language :: English', 'Programming Language :: Python', 'Programming Language :: Python :: 2.7', 'Programming Language :: Python :: 3.5', 'Programming Language :: Python :: 3.6', 'Programming Language :: Python :: 3.7', 'Programming Language :: Python :: Implementation :: CPython', 'Programming Language :: Python :: Implementation :: PyPy'], package_data={'labelme': ['icons/*', 'config/*.yaml']}, entry_points={'console_scripts': ['labelme=labelme.__main__:main', 'labelme_draw_json=labelme.cli.draw_json:main', 'labelme_draw_label_png=labelme.cli.draw_label_png:main', 'labelme_json_to_dataset=labelme.cli.json_to_dataset:main', 'labelme_on_docker=labelme.cli.on_docker:main']}, data_files=[('share/man/man1', ['docs/man/labelme.1'])])

def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('label_png', help='label PNG file')
    args = parser.parse_args()
    lbl = np.asarray(PIL.Image.open(args.label_png))
    logger.info('label shape: {}'.format(lbl.shape))
    logger.info('unique label values: {}'.format(np.unique(lbl)))
    lbl_viz = imgviz.label2rgb(lbl)
    plt.imshow(lbl_viz)
    plt.show()

def main():
    logger.warning('This script is aimed to demonstrate how to convert the JSON file to a single image dataset.')
    logger.warning("It won't handle multiple JSON files to generate a real-use dataset.")
    parser = argparse.ArgumentParser()
    parser.add_argument('json_file')
    parser.add_argument('-o', '--out', default=None)
    args = parser.parse_args()
    json_file = args.json_file
    if args.out is None:
        out_dir = osp.basename(json_file).replace('.', '_')
        out_dir = osp.join(osp.dirname(json_file), out_dir)
    else:
        out_dir = args.out
    if not osp.exists(out_dir):
        os.mkdir(out_dir)
    data = json.load(open(json_file))
    imageData = data.get('imageData')
    if not imageData:
        imagePath = os.path.join(os.path.dirname(json_file), data['imagePath'])
        with open(imagePath, 'rb') as f:
            imageData = f.read()
            imageData = base64.b64encode(imageData).decode('utf-8')
    img = utils.img_b64_to_arr(imageData)
    label_name_to_value = {'_background_': 0}
    for shape in sorted(data['shapes'], key=lambda x: x['label']):
        label_name = shape['label']
        if label_name in label_name_to_value:
            label_value = label_name_to_value[label_name]
        else:
            label_value = len(label_name_to_value)
            label_name_to_value[label_name] = label_value
    lbl, _ = utils.shapes_to_label(img.shape, data['shapes'], label_name_to_value)
    label_names = [None] * (max(label_name_to_value.values()) + 1)
    for name, value in label_name_to_value.items():
        label_names[value] = name
    lbl_viz = imgviz.label2rgb(label=lbl, img=imgviz.asgray(img), label_names=label_names, loc='rb')
    PIL.Image.fromarray(img).save(osp.join(out_dir, 'img.png'))
    utils.lblsave(osp.join(out_dir, 'label.png'), lbl)
    PIL.Image.fromarray(lbl_viz).save(osp.join(out_dir, 'label_viz.png'))
    with open(osp.join(out_dir, 'label_names.txt'), 'w') as f:
        for lbl_name in label_names:
            f.write(lbl_name + '\n')
    logger.info('Saved to: {}'.format(out_dir))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('json_file')
    args = parser.parse_args()
    label_file = LabelFile(args.json_file)
    img = utils.img_data_to_arr(label_file.imageData)
    label_name_to_value = {'_background_': 0}
    for shape in sorted(label_file.shapes, key=lambda x: x['label']):
        label_name = shape['label']
        if label_name in label_name_to_value:
            label_value = label_name_to_value[label_name]
        else:
            label_value = len(label_name_to_value)
            label_name_to_value[label_name] = label_value
    lbl, _ = utils.shapes_to_label(img.shape, label_file.shapes, label_name_to_value)
    label_names = [None] * (max(label_name_to_value.values()) + 1)
    for name, value in label_name_to_value.items():
        label_names[value] = name
    lbl_viz = imgviz.label2rgb(label=lbl, img=imgviz.asgray(img), label_names=label_names, font_size=30, loc='rb')
    plt.subplot(121)
    plt.imshow(img)
    plt.subplot(122)
    plt.imshow(lbl_viz)
    plt.show()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('in_file', help='Input file or directory.')
    parser.add_argument('-O', '--output')
    args = parser.parse_args()
    if not distutils.spawn.find_executable('docker'):
        print('Please install docker', file=sys.stderr)
        sys.exit(1)
    try:
        out_file = labelme_on_docker(args.in_file, args.output)
        if out_file:
            print('Saved to: %s' % out_file)
    except RuntimeError as e:
        sys.stderr.write(e.__str__() + '\n')
        sys.exit(1)

def labelme_shapes_to_label(img_shape, shapes):
    logger.warn('labelme_shapes_to_label is deprecated, so please use shapes_to_label.')
    label_name_to_value = {'_background_': 0}
    for shape in shapes:
        label_name = shape['label']
        if label_name in label_name_to_value:
            label_value = label_name_to_value[label_name]
        else:
            label_value = len(label_name_to_value)
            label_name_to_value[label_name] = label_value
    lbl, _ = shapes_to_label(img_shape, shapes, label_name_to_value)
    return (lbl, label_name_to_value)

def img_b64_to_arr(img_b64):
    img_data = base64.b64decode(img_b64)
    img_arr = img_data_to_arr(img_data)
    return img_arr

def parse_args():
    parser = argparse.ArgumentParser(description='MMDet benchmark a model of FPS')
    parser.add_argument('config', help='test config file path')
    parser.add_argument('checkpoint_root', help='Checkpoint file root path')
    parser.add_argument('--round-num', type=int, default=1, help='round a number to a given precision in decimal digits')
    parser.add_argument('--repeat-num', type=int, default=1, help='number of repeat times of measurement for averaging the results')
    parser.add_argument('--out', type=str, help='output path of gathered fps to be stored')
    parser.add_argument('--max-iter', type=int, default=2000, help='num of max iter')
    parser.add_argument('--log-interval', type=int, default=50, help='interval of logging')
    parser.add_argument('--fuse-conv-bn', action='store_true', help='Whether to fuse conv and bn, this will slightly increasethe inference speed')
    parser.add_argument('--cfg-options', nargs='+', action=DictAction, help='override some settings in the used config, the key-value pair in xxx=yyy format will be merged into config file. If the value to be overwritten is a list, it should be like key="[a,b]" or key=a,b It also allows nested list/tuple values, e.g. key="[(a,b),(c,d)]" Note that the quotation marks are necessary and that no white space is allowed.')
    parser.add_argument('--launcher', choices=['none', 'pytorch', 'slurm', 'mpi'], default='none', help='job launcher')
    parser.add_argument('--local_rank', type=int, default=0)
    args = parser.parse_args()
    if 'LOCAL_RANK' not in os.environ:
        os.environ['LOCAL_RANK'] = str(args.local_rank)
    return args

def parse_args():
    parser = argparse.ArgumentParser(description='Goes through all the inline-links in markdown files and reports the breakages')
    parser.add_argument('--num-threads', type=int, default=100, help='Number of processes to confirm the link')
    parser.add_argument('--https-proxy', type=str, help='https proxy')
    parser.add_argument('--out', type=str, default='link_reports.txt', help='output path of reports')
    args = parser.parse_args()
    return args

def parse_args():
    parser = argparse.ArgumentParser(description='Filter configs to train')
    parser.add_argument('--basic-arch', action='store_true', help='to train models in basic arch')
    parser.add_argument('--datasets', action='store_true', help='to train models in dataset')
    parser.add_argument('--data-pipeline', action='store_true', help='to train models related to data pipeline, e.g. augmentations')
    parser.add_argument('--nn-module', action='store_true', help='to train models related to neural network modules')
    parser.add_argument('--model-options', nargs='+', help='custom options to special model benchmark')
    parser.add_argument('--out', type=str, default='batch_train_list.txt', help='output path of gathered metrics to be stored')
    args = parser.parse_args()
    return args

def parse_args():
    parser = argparse.ArgumentParser(description='Convert benchmark model json to script')
    parser.add_argument('txt_path', type=str, help='txt path output by benchmark_filter')
    parser.add_argument('--partition', type=str, default='openmmlab', help='slurm partition name')
    parser.add_argument('--max-keep-ckpts', type=int, default=1, help='The maximum checkpoints to keep')
    parser.add_argument('--run', action='store_true', help='run script directly')
    parser.add_argument('--out', type=str, help='path to save model benchmark script')
    args = parser.parse_args()
    return args

def parse_args():
    parser = ArgumentParser()
    parser.add_argument('config', help='test config file path')
    parser.add_argument('checkpoint_root', help='Checkpoint file root path')
    parser.add_argument('--img', default='demo/demo.jpg', help='Image file')
    parser.add_argument('--aug', action='store_true', help='aug test')
    parser.add_argument('--model-name', help='model name to inference')
    parser.add_argument('--show', action='store_true', help='show results')
    parser.add_argument('--wait-time', type=float, default=1, help='the interval of show (s), 0 is block')
    parser.add_argument('--device', default='cuda:0', help='Device used for inference')
    parser.add_argument('--score-thr', type=float, default=0.3, help='bbox score threshold')
    args = parser.parse_args()
    return args

def parse_args():
    parser = argparse.ArgumentParser(description='Convert benchmark model list to script')
    parser.add_argument('config', help='test config file path')
    parser.add_argument('--port', type=int, default=29666, help='dist port')
    parser.add_argument('--work-dir', default='tools/batch_test', help='the dir to save metric')
    parser.add_argument('--run', action='store_true', help='run script directly')
    parser.add_argument('--out', type=str, help='path to save model benchmark script')
    args = parser.parse_args()
    return args

def parse_args():
    parser = argparse.ArgumentParser(description='Gather benchmarked models metric')
    parser.add_argument('config', help='test config file path')
    parser.add_argument('root', type=str, help='root path of benchmarked models to be gathered')
    parser.add_argument('--out', type=str, help='output path of gathered metrics to be stored')
    parser.add_argument('--not-show', action='store_true', help='not show metrics')
    parser.add_argument('--show-all', action='store_true', help='show all model metrics')
    args = parser.parse_args()
    return args

def parse_args():
    parser = argparse.ArgumentParser(description='Gather benchmarked models metric')
    parser.add_argument('root', type=str, help='root path of benchmarked models to be gathered')
    parser.add_argument('txt_path', type=str, help='txt path output by benchmark_filter')
    parser.add_argument('--out', type=str, help='output path of gathered metrics to be stored')
    parser.add_argument('--not-show', action='store_true', help='not show metrics')
    parser.add_argument('--excel', type=str, help='input path of excel to be recorded')
    parser.add_argument('--ncol', type=int, help='Number of column to be modified or appended')
    args = parser.parse_args()
    return args

def parse_args():
    parser = argparse.ArgumentParser(description='Gather benchmarked models')
    parser.add_argument('root', type=str, help='root path of benchmarked models to be gathered')
    parser.add_argument('out', type=str, help='output path of gathered models to be stored')
    parser.add_argument('--best', action='store_true', help='whether to gather the best model.')
    args = parser.parse_args()
    return args

def parse_args():
    parser = argparse.ArgumentParser(description='Train a detector')
    parser.add_argument('config', help='train config file path')
    parser.add_argument('--work-dir', help='the dir to save logs and models')
    parser.add_argument('--resume-from', help='the checkpoint file to resume from')
    parser.add_argument('--auto-resume', action='store_true', help='resume from the latest checkpoint automatically')
    parser.add_argument('--no-validate', action='store_true', help='whether not to evaluate the checkpoint during training')
    group_gpus = parser.add_mutually_exclusive_group()
    group_gpus.add_argument('--gpus', type=int, help='(Deprecated, please use --gpu-id) number of gpus to use (only applicable to non-distributed training)')
    group_gpus.add_argument('--gpu-ids', type=int, nargs='+', help='(Deprecated, please use --gpu-id) ids of gpus to use (only applicable to non-distributed training)')
    group_gpus.add_argument('--gpu-id', type=int, default=0, help='id of gpu to use (only applicable to non-distributed training)')
    parser.add_argument('--seed', type=int, default=None, help='random seed')
    parser.add_argument('--diff-seed', action='store_true', help='Whether or not set different seeds for different ranks')
    parser.add_argument('--deterministic', action='store_true', help='whether to set deterministic options for CUDNN backend.')
    parser.add_argument('--options', nargs='+', action=DictAction, help='override some settings in the used config, the key-value pair in xxx=yyy format will be merged into config file (deprecate), change to --cfg-options instead.')
    parser.add_argument('--cfg-options', nargs='+', action=DictAction, help='override some settings in the used config, the key-value pair in xxx=yyy format will be merged into config file. If the value to be overwritten is a list, it should be like key="[a,b]" or key=a,b It also allows nested list/tuple values, e.g. key="[(a,b),(c,d)]" Note that the quotation marks are necessary and that no white space is allowed.')
    parser.add_argument('--launcher', choices=['none', 'pytorch', 'slurm', 'mpi'], default='none', help='job launcher')
    parser.add_argument('--local_rank', type=int, default=0)
    parser.add_argument('--auto-scale-lr', action='store_true', help='enable automatically scaling LR.')
    args = parser.parse_args()
    if 'LOCAL_RANK' not in os.environ:
        os.environ['LOCAL_RANK'] = str(args.local_rank)
    if args.options and args.cfg_options:
        raise ValueError('--options and --cfg-options cannot be both specified, --options is deprecated in favor of --cfg-options')
    if args.options:
        warnings.warn('--options is deprecated in favor of --cfg-options')
        args.cfg_options = args.options
    return args

def parse_args():
    parser = argparse.ArgumentParser(description='MMDet test (and eval) a model')
    parser.add_argument('config', help='test config file path')
    parser.add_argument('checkpoint', help='checkpoint file')
    parser.add_argument('--work-dir', help='the directory to save the file containing evaluation metrics')
    parser.add_argument('--out', help='output result file in pickle format')
    parser.add_argument('--fuse-conv-bn', action='store_true', help='Whether to fuse conv and bn, this will slightly increasethe inference speed')
    parser.add_argument('--gpu-ids', type=int, nargs='+', help='(Deprecated, please use --gpu-id) ids of gpus to use (only applicable to non-distributed training)')
    parser.add_argument('--gpu-id', type=int, default=0, help='id of gpu to use (only applicable to non-distributed testing)')
    parser.add_argument('--format-only', action='store_true', help='Format the output results without perform evaluation. It isuseful when you want to format the result to a specific format and submit it to the test server')
    parser.add_argument('--eval', type=str, nargs='+', help='evaluation metrics, which depends on the dataset, e.g., "bbox", "segm", "proposal" for COCO, and "mAP", "recall" for PASCAL VOC')
    parser.add_argument('--show', action='store_true', help='show results')
    parser.add_argument('--show-dir', help='directory where painted images will be saved')
    parser.add_argument('--show-score-thr', type=float, default=0.3, help='score threshold (default: 0.3)')
    parser.add_argument('--gpu-collect', action='store_true', help='whether to use gpu to collect results.')
    parser.add_argument('--tmpdir', help='tmp directory used for collecting results from multiple workers, available when gpu-collect is not specified')
    parser.add_argument('--cfg-options', nargs='+', action=DictAction, help='override some settings in the used config, the key-value pair in xxx=yyy format will be merged into config file. If the value to be overwritten is a list, it should be like key="[a,b]" or key=a,b It also allows nested list/tuple values, e.g. key="[(a,b),(c,d)]" Note that the quotation marks are necessary and that no white space is allowed.')
    parser.add_argument('--options', nargs='+', action=DictAction, help='custom options for evaluation, the key-value pair in xxx=yyy format will be kwargs for dataset.evaluate() function (deprecate), change to --eval-options instead.')
    parser.add_argument('--eval-options', nargs='+', action=DictAction, help='custom options for evaluation, the key-value pair in xxx=yyy format will be kwargs for dataset.evaluate() function')
    parser.add_argument('--launcher', choices=['none', 'pytorch', 'slurm', 'mpi'], default='none', help='job launcher')
    parser.add_argument('--local_rank', type=int, default=0)
    args = parser.parse_args()
    if 'LOCAL_RANK' not in os.environ:
        os.environ['LOCAL_RANK'] = str(args.local_rank)
    if args.options and args.eval_options:
        raise ValueError('--options and --eval-options cannot be both specified, --options is deprecated in favor of --eval-options')
    if args.options:
        warnings.warn('--options is deprecated in favor of --eval-options')
        args.eval_options = args.options
    return args

def parse_args():
    parser = argparse.ArgumentParser(description='MMDet test (and eval) an ONNX model using ONNXRuntime')
    parser.add_argument('config', help='test config file path')
    parser.add_argument('model', help='Input model file')
    parser.add_argument('--out', help='output result file in pickle format')
    parser.add_argument('--format-only', action='store_true', help='Format the output results without perform evaluation. It isuseful when you want to format the result to a specific format and submit it to the test server')
    parser.add_argument('--backend', required=True, choices=['onnxruntime', 'tensorrt'], help='Backend for input model to run. ')
    parser.add_argument('--eval', type=str, nargs='+', help='evaluation metrics, which depends on the dataset, e.g., "bbox", "segm", "proposal" for COCO, and "mAP", "recall" for PASCAL VOC')
    parser.add_argument('--show', action='store_true', help='show results')
    parser.add_argument('--show-dir', help='directory where painted images will be saved')
    parser.add_argument('--show-score-thr', type=float, default=0.3, help='score threshold (default: 0.3)')
    parser.add_argument('--cfg-options', nargs='+', action=DictAction, help='override some settings in the used config, the key-value pair in xxx=yyy format will be merged into config file. If the value to be overwritten is a list, it should be like key="[a,b]" or key=a,b It also allows nested list/tuple values, e.g. key="[(a,b),(c,d)]" Note that the quotation marks are necessary and that no white space is allowed.')
    parser.add_argument('--eval-options', nargs='+', action=DictAction, help='custom options for evaluation, the key-value pair in xxx=yyy format will be kwargs for dataset.evaluate() function')
    args = parser.parse_args()
    return args

def parse_args():
    parser = argparse.ArgumentParser(description='Convert MMDetection models to ONNX')
    parser.add_argument('config', help='test config file path')
    parser.add_argument('checkpoint', help='checkpoint file')
    parser.add_argument('--input-img', type=str, help='Images for input')
    parser.add_argument('--show', action='store_true', help='Show onnx graph and detection outputs')
    parser.add_argument('--output-file', type=str, default='tmp.onnx')
    parser.add_argument('--opset-version', type=int, default=11)
    parser.add_argument('--test-img', type=str, default=None, help='Images for test')
    parser.add_argument('--dataset', type=str, default='coco', help='Dataset name. This argument is deprecated and will be removed         in future releases.')
    parser.add_argument('--verify', action='store_true', help='verify the onnx model output against pytorch output')
    parser.add_argument('--simplify', action='store_true', help='Whether to simplify onnx model.')
    parser.add_argument('--shape', type=int, nargs='+', default=[800, 1216], help='input image size')
    parser.add_argument('--mean', type=float, nargs='+', default=[123.675, 116.28, 103.53], help='mean value used for preprocess input data.This argument         is deprecated and will be removed in future releases.')
    parser.add_argument('--std', type=float, nargs='+', default=[58.395, 57.12, 57.375], help='variance value used for preprocess input data. This argument is deprecated and will be removed in future releases.')
    parser.add_argument('--cfg-options', nargs='+', action=DictAction, help='Override some settings in the used config, the key-value pair in xxx=yyy format will be merged into config file. If the value to be overwritten is a list, it should be like key="[a,b]" or key=a,b It also allows nested list/tuple values, e.g. key="[(a,b),(c,d)]" Note that the quotation marks are necessary and that no white space is allowed.')
    parser.add_argument('--dynamic-export', action='store_true', help='Whether to export onnx with dynamic axis.')
    parser.add_argument('--skip-postprocess', action='store_true', help='Whether to export model without post process. Experimental option. We do not guarantee the correctness of the exported model.')
    args = parser.parse_args()
    return args

def parse_args():
    parser = ArgumentParser(description='Convert MMDetection models to TorchServe `.mar` format.')
    parser.add_argument('config', type=str, help='config file path')
    parser.add_argument('checkpoint', type=str, help='checkpoint file path')
    parser.add_argument('--output-folder', type=str, required=True, help='Folder where `{model_name}.mar` will be created.')
    parser.add_argument('--model-name', type=str, default=None, help='If not None, used for naming the `{model_name}.mar`file that will be created under `output_folder`.If None, `{Path(checkpoint_file).stem}` will be used.')
    parser.add_argument('--model-version', type=str, default='1.0', help='Number used for versioning.')
    parser.add_argument('-f', '--force', action='store_true', help='overwrite the existing `{model_name}.mar`')
    args = parser.parse_args()
    return args

def parse_args():
    parser = ArgumentParser()
    parser.add_argument('img', help='Image file')
    parser.add_argument('config', help='Config file')
    parser.add_argument('checkpoint', help='Checkpoint file')
    parser.add_argument('model_name', help='The model name in the server')
    parser.add_argument('--inference-addr', default='127.0.0.1:8080', help='Address and port of the inference server')
    parser.add_argument('--device', default='cuda:0', help='Device used for inference')
    parser.add_argument('--score-thr', type=float, default=0.5, help='bbox score threshold')
    args = parser.parse_args()
    return args

def parse_args():
    parser = argparse.ArgumentParser(description='Convert MMDetection models from ONNX to TensorRT')
    parser.add_argument('config', help='test config file path')
    parser.add_argument('model', help='Filename of input ONNX model')
    parser.add_argument('--trt-file', type=str, default='tmp.trt', help='Filename of output TensorRT engine')
    parser.add_argument('--input-img', type=str, default='', help='Image for test')
    parser.add_argument('--show', action='store_true', help='Whether to show output results')
    parser.add_argument('--dataset', type=str, default='coco', help='Dataset name. This argument is deprecated and will be         removed in future releases.')
    parser.add_argument('--verify', action='store_true', help='Verify the outputs of ONNXRuntime and TensorRT')
    parser.add_argument('--verbose', action='store_true', help='Whether to verbose logging messages while creating                 TensorRT engine. Defaults to False.')
    parser.add_argument('--to-rgb', action='store_false', help='Feed model with RGB or BGR image. Default is RGB. This         argument is deprecated and will be removed in future releases.')
    parser.add_argument('--shape', type=int, nargs='+', default=[400, 600], help='Input size of the model')
    parser.add_argument('--mean', type=float, nargs='+', default=[123.675, 116.28, 103.53], help='Mean value used for preprocess input data. This argument         is deprecated and will be removed in future releases.')
    parser.add_argument('--std', type=float, nargs='+', default=[58.395, 57.12, 57.375], help='Variance value used for preprocess input data.         This argument is deprecated and will be removed in future releases.')
    parser.add_argument('--min-shape', type=int, nargs='+', default=None, help='Minimum input size of the model in TensorRT')
    parser.add_argument('--max-shape', type=int, nargs='+', default=None, help='Maximum input size of the model in TensorRT')
    parser.add_argument('--workspace-size', type=int, default=1, help='Max workspace size in GiB')
    args = parser.parse_args()
    return args

def parse_args():
    parser = argparse.ArgumentParser(description='Convert Cityscapes annotations to COCO format')
    parser.add_argument('cityscapes_path', help='cityscapes data path')
    parser.add_argument('--img-dir', default='leftImg8bit', type=str)
    parser.add_argument('--gt-dir', default='gtFine', type=str)
    parser.add_argument('-o', '--out-dir', help='output path')
    parser.add_argument('--nproc', default=1, type=int, help='number of process')
    args = parser.parse_args()
    return args

def parse_args():
    parser = argparse.ArgumentParser(description='Convert images to coco format without annotations')
    parser.add_argument('img_path', help='The root path of images')
    parser.add_argument('classes', type=str, help='The text file name of storage class list')
    parser.add_argument('out', type=str, help='The output annotation json file name, The save dir is in the same directory as img_path')
    parser.add_argument('-e', '--exclude-extensions', type=str, nargs='+', help='The suffix of images to be excluded, such as "png" and "bmp"')
    args = parser.parse_args()
    return args

def parse_args():
    parser = argparse.ArgumentParser(description='Convert PASCAL VOC annotations to mmdetection format')
    parser.add_argument('devkit_path', help='pascal voc devkit path')
    parser.add_argument('-o', '--out-dir', help='output path')
    parser.add_argument('--out-format', default='pkl', choices=('pkl', 'coco'), help='output format, "coco" indicates coco annotation format')
    args = parser.parse_args()
    return args

def main():
    parser = argparse.ArgumentParser(description='Convert model keys')
    parser.add_argument('src', help='src detectron model path')
    parser.add_argument('dst', help='save path')
    parser.add_argument('depth', type=int, help='ResNet model depth')
    args = parser.parse_args()
    convert(args.src, args.dst, args.depth)

def main():
    parser = argparse.ArgumentParser(description='Upgrade model version')
    parser.add_argument('in_file', help='input checkpoint file')
    parser.add_argument('out_file', help='output checkpoint file')
    parser.add_argument('--num-classes', type=int, default=81, help='number of classes of the original model')
    args = parser.parse_args()
    convert(args.in_file, args.out_file, args.num_classes)

def parse_args():
    parser = argparse.ArgumentParser(description='Process a checkpoint to be published')
    parser.add_argument('in_file', help='input checkpoint filename')
    parser.add_argument('out_file', help='output checkpoint filename')
    args = parser.parse_args()
    return args

def main():
    args = parse_args()
    process_checkpoint(args.in_file, args.out_file)

def main():
    parser = argparse.ArgumentParser(description='Upgrade SSD version')
    parser.add_argument('in_file', help='input checkpoint file')
    parser.add_argument('out_file', help='output checkpoint file')
    args = parser.parse_args()
    convert(args.in_file, args.out_file)

def main():
    parser = argparse.ArgumentParser(description='Convert model keys')
    parser.add_argument('src', help='src detectron model path')
    parser.add_argument('dst', help='save path')
    parser.add_argument('--selfsup', type=str, choices=['moco', 'swav'], help='save path')
    args = parser.parse_args()
    if args.selfsup == 'moco':
        moco_convert(args.src, args.dst)
    elif args.selfsup == 'swav':
        print('SWAV does not need to convert the keys')

def main():
    parser = argparse.ArgumentParser(description='Convert model keys')
    parser.add_argument('src', help='src detectron model path')
    parser.add_argument('dst', help='save path')
    args = parser.parse_args()
    convert(args.src, args.dst)

def parse_args():
    parser = argparse.ArgumentParser(description='Generate COCO test image information for COCO panoptic segmentation.')
    parser.add_argument('data_root', help='Path to COCO annotation directory.')
    args = parser.parse_args()
    return args

def parse_args():
    parser = argparse.ArgumentParser(description='Browse a dataset')
    parser.add_argument('config', help='train config file path')
    parser.add_argument('--skip-type', type=str, nargs='+', default=['DefaultFormatBundle', 'Normalize', 'Collect'], help='skip some useless pipeline')
    parser.add_argument('--output-dir', default=None, type=str, help='If there is no display interface, you can save it')
    parser.add_argument('--not-show', default=False, action='store_true')
    parser.add_argument('--show-interval', type=float, default=2, help='the interval of show (s)')
    parser.add_argument('--cfg-options', nargs='+', action=DictAction, help='override some settings in the used config, the key-value pair in xxx=yyy format will be merged into config file. If the value to be overwritten is a list, it should be like key="[a,b]" or key=a,b It also allows nested list/tuple values, e.g. key="[(a,b),(c,d)]" Note that the quotation marks are necessary and that no white space is allowed.')
    args = parser.parse_args()
    return args

def parse_args():
    parser = argparse.ArgumentParser(description='Collect image metas')
    parser.add_argument('config', help='Config file path')
    parser.add_argument('--out', default='validation-image-metas.pkl', help='The output image metas file name. The save dir is in the same directory as `dataset.ann_file` path')
    parser.add_argument('--nproc', default=4, type=int, help='Processes used for get image metas')
    args = parser.parse_args()
    return args

def parse_args():
    parser = argparse.ArgumentParser(description='Print the whole config')
    parser.add_argument('config', help='config file path')
    parser.add_argument('--options', nargs='+', action=DictAction, help='override some settings in the used config, the key-value pair in xxx=yyy format will be merged into config file (deprecate), change to --cfg-options instead.')
    parser.add_argument('--cfg-options', nargs='+', action=DictAction, help='override some settings in the used config, the key-value pair in xxx=yyy format will be merged into config file. If the value to be overwritten is a list, it should be like key="[a,b]" or key=a,b It also allows nested list/tuple values, e.g. key="[(a,b),(c,d)]" Note that the quotation marks are necessary and that no white space is allowed.')
    args = parser.parse_args()
    if args.options and args.cfg_options:
        raise ValueError('--options and --cfg-options cannot be both specified, --options is deprecated in favor of --cfg-options')
    if args.options:
        warnings.warn('--options is deprecated in favor of --cfg-options')
        args.cfg_options = args.options
    return args

def parse_args():
    parser = argparse.ArgumentParser(description='Download datasets for training')
    parser.add_argument('--dataset-name', type=str, help='dataset name', default='coco2017')
    parser.add_argument('--save-dir', type=str, help='the dir to save dataset', default='data/coco')
    parser.add_argument('--unzip', action='store_true', help='whether unzip dataset or not, zipped files will be saved')
    parser.add_argument('--delete', action='store_true', help='delete the download zipped files')
    parser.add_argument('--threads', type=int, help='number of threading', default=4)
    args = parser.parse_args()
    return args

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-root', type=str, help='The data root of coco dataset.', default='./data/coco/')
    parser.add_argument('--out-dir', type=str, help='The output directory of coco semi-supervised annotations.', default='./data/coco_semi_annos/')
    parser.add_argument('--labeled-percent', type=float, nargs='+', help='The percentage of labeled data in the training set.', default=[1, 2, 5, 10])
    parser.add_argument('--fold', type=int, help='K-fold cross validation for semi-supervised object detection.', default=5)
    args = parser.parse_args()
    return args

def parse_args():
    parser = argparse.ArgumentParser(description='Train a detector')
    parser.add_argument('config', help='train config file path')
    parser.add_argument('--shape', type=int, nargs='+', default=[1280, 800], help='input image size')
    parser.add_argument('--cfg-options', nargs='+', action=DictAction, help='override some settings in the used config, the key-value pair in xxx=yyy format will be merged into config file. If the value to be overwritten is a list, it should be like key="[a,b]" or key=a,b It also allows nested list/tuple values, e.g. key="[(a,b),(c,d)]" Note that the quotation marks are necessary and that no white space is allowed.')
    parser.add_argument('--size-divisor', type=int, default=32, help='Pad the input image, the minimum size that is divisible by size_divisor, -1 means do not pad the image.')
    args = parser.parse_args()
    return args

def parse_args():
    parser = argparse.ArgumentParser(description='Evaluate metric of the results saved in pkl format')
    parser.add_argument('config', help='Config of the model')
    parser.add_argument('pkl_results', help='Results in pickle format')
    parser.add_argument('--format-only', action='store_true', help='Format the output results without perform evaluation. It isuseful when you want to format the result to a specific format and submit it to the test server')
    parser.add_argument('--eval', type=str, nargs='+', help='Evaluation metrics, which depends on the dataset, e.g., "bbox", "segm", "proposal" for COCO, and "mAP", "recall" for PASCAL VOC')
    parser.add_argument('--cfg-options', nargs='+', action=DictAction, help='override some settings in the used config, the key-value pair in xxx=yyy format will be merged into config file. If the value to be overwritten is a list, it should be like key="[a,b]" or key=a,b It also allows nested list/tuple values, e.g. key="[(a,b),(c,d)]" Note that the quotation marks are necessary and that no white space is allowed.')
    parser.add_argument('--eval-options', nargs='+', action=DictAction, help='custom options for evaluation, the key-value pair in xxx=yyy format will be kwargs for dataset.evaluate() function')
    args = parser.parse_args()
    return args

def add_plot_parser(subparsers):
    parser_plt = subparsers.add_parser('plot_curve', help='parser for plotting curves')
    parser_plt.add_argument('json_logs', type=str, nargs='+', help='path of train log in json format')
    parser_plt.add_argument('--keys', type=str, nargs='+', default=['bbox_mAP'], help='the metric that you want to plot')
    parser_plt.add_argument('--start-epoch', type=str, default='1', help='the epoch that you want to start')
    parser_plt.add_argument('--eval-interval', type=str, default='1', help='the eval interval when training')
    parser_plt.add_argument('--title', type=str, help='title of figure')
    parser_plt.add_argument('--legend', type=str, nargs='+', default=None, help='legend of each plot')
    parser_plt.add_argument('--backend', type=str, default=None, help='backend of plt')
    parser_plt.add_argument('--style', type=str, default='dark', help='style of plt')
    parser_plt.add_argument('--out', type=str, default=None)

def add_time_parser(subparsers):
    parser_time = subparsers.add_parser('cal_train_time', help='parser for computing the average time per training iteration')
    parser_time.add_argument('json_logs', type=str, nargs='+', help='path of train log in json format')
    parser_time.add_argument('--include-outliers', action='store_true', help='include the first value of every epoch when computing the average time')

def parse_args():
    parser = argparse.ArgumentParser(description='Analyze Json Log')
    subparsers = parser.add_subparsers(dest='task', help='task parser')
    add_plot_parser(subparsers)
    add_time_parser(subparsers)
    args = parser.parse_args()
    return args

def main():
    args = parse_args()
    json_logs = args.json_logs
    for json_log in json_logs:
        assert json_log.endswith('.json')
    log_dicts = load_json_logs(json_logs)
    eval(args.task)(log_dicts, args)

def main():
    parser = ArgumentParser(description='Corruption Result Analysis')
    parser.add_argument('filename', help='result file path')
    parser.add_argument('--dataset', type=str, choices=['coco', 'voc', 'cityscapes'], default='coco', help='dataset type')
    parser.add_argument('--task', type=str, nargs='+', choices=['bbox', 'segm'], default=['bbox'], help='task to report')
    parser.add_argument('--metric', nargs='+', choices=[None, 'AP', 'AP50', 'AP75', 'APs', 'APm', 'APl', 'AR1', 'AR10', 'AR100', 'ARs', 'ARm', 'ARl'], default=None, help='metric to report')
    parser.add_argument('--prints', type=str, nargs='+', choices=['P', 'mPC', 'rPC'], default='mPC', help='corruption benchmark metric to print')
    parser.add_argument('--aggregate', type=str, choices=['all', 'benchmark'], default='benchmark', help='aggregate all results or only those         for benchmark corruptions')
    args = parser.parse_args()
    for task in args.task:
        get_results(args.filename, dataset=args.dataset, task=task, metric=args.metric, prints=args.prints, aggregate=args.aggregate)

def main():
    parser = ArgumentParser(description='COCO Error Analysis Tool')
    parser.add_argument('result', help='result file (json format) path')
    parser.add_argument('out_dir', help='dir to save analyze result images')
    parser.add_argument('--ann', default='data/coco/annotations/instances_val2017.json', help='annotation file path')
    parser.add_argument('--types', type=str, nargs='+', default=['bbox'], help='result types')
    parser.add_argument('--extraplots', action='store_true', help='export extra bar/stat plots')
    parser.add_argument('--areas', type=int, nargs='+', default=[1024, 9216, 10000000000], help='area regions')
    args = parser.parse_args()
    analyze_results(args.result, args.ann, args.types, out_dir=args.out_dir, extraplots=args.extraplots, areas=args.areas)

def parse_args():
    parser = argparse.ArgumentParser(description='Generate confusion matrix from detection results')
    parser.add_argument('config', help='test config file path')
    parser.add_argument('prediction_path', help='prediction path where test .pkl result')
    parser.add_argument('save_dir', help='directory where confusion matrix will be saved')
    parser.add_argument('--show', action='store_true', help='show confusion matrix')
    parser.add_argument('--color-theme', default='plasma', help='theme of the matrix color map')
    parser.add_argument('--score-thr', type=float, default=0.3, help='score threshold to filter detection bboxes')
    parser.add_argument('--tp-iou-thr', type=float, default=0.5, help='IoU threshold to be considered as matched')
    parser.add_argument('--nms-iou-thr', type=float, default=None, help='nms IoU threshold, only applied when users want to change thenms IoU threshold.')
    parser.add_argument('--cfg-options', nargs='+', action=DictAction, help='override some settings in the used config, the key-value pair in xxx=yyy format will be merged into config file. If the value to be overwritten is a list, it should be like key="[a,b]" or key=a,b It also allows nested list/tuple values, e.g. key="[(a,b),(c,d)]" Note that the quotation marks are necessary and that no white space is allowed.')
    args = parser.parse_args()
    return args

def parse_args():
    parser = argparse.ArgumentParser(description='MMDet test detector')
    parser.add_argument('config', help='test config file path')
    parser.add_argument('checkpoint', help='checkpoint file')
    parser.add_argument('--out', help='output result file')
    parser.add_argument('--corruptions', type=str, nargs='+', default='benchmark', choices=['all', 'benchmark', 'noise', 'blur', 'weather', 'digital', 'holdout', 'None', 'gaussian_noise', 'shot_noise', 'impulse_noise', 'defocus_blur', 'glass_blur', 'motion_blur', 'zoom_blur', 'snow', 'frost', 'fog', 'brightness', 'contrast', 'elastic_transform', 'pixelate', 'jpeg_compression', 'speckle_noise', 'gaussian_blur', 'spatter', 'saturate'], help='corruptions')
    parser.add_argument('--severities', type=int, nargs='+', default=[0, 1, 2, 3, 4, 5], help='corruption severity levels')
    parser.add_argument('--eval', type=str, nargs='+', choices=['proposal', 'proposal_fast', 'bbox', 'segm', 'keypoints'], help='eval types')
    parser.add_argument('--iou-thr', type=float, default=0.5, help='IoU threshold for pascal voc evaluation')
    parser.add_argument('--summaries', type=bool, default=False, help='Print summaries for every corruption and severity')
    parser.add_argument('--workers', type=int, default=32, help='workers per gpu')
    parser.add_argument('--show', action='store_true', help='show results')
    parser.add_argument('--show-dir', help='directory where painted images will be saved')
    parser.add_argument('--show-score-thr', type=float, default=0.3, help='score threshold (default: 0.3)')
    parser.add_argument('--tmpdir', help='tmp dir for writing some results')
    parser.add_argument('--seed', type=int, default=None, help='random seed')
    parser.add_argument('--launcher', choices=['none', 'pytorch', 'slurm', 'mpi'], default='none', help='job launcher')
    parser.add_argument('--local_rank', type=int, default=0)
    parser.add_argument('--final-prints', type=str, nargs='+', choices=['P', 'mPC', 'rPC'], default='mPC', help='corruption benchmark metric to print at the end')
    parser.add_argument('--final-prints-aggregate', type=str, choices=['all', 'benchmark'], default='benchmark', help='aggregate all results or only those for benchmark corruptions')
    parser.add_argument('--cfg-options', nargs='+', action=DictAction, help='override some settings in the used config, the key-value pair in xxx=yyy format will be merged into config file. If the value to be overwritten is a list, it should be like key="[a,b]" or key=a,b It also allows nested list/tuple values, e.g. key="[(a,b),(c,d)]" Note that the quotation marks are necessary and that no white space is allowed.')
    args = parser.parse_args()
    if 'LOCAL_RANK' not in os.environ:
        os.environ['LOCAL_RANK'] = str(args.local_rank)
    return args

def parse_args():
    parser = argparse.ArgumentParser(description='MMDet eval image prediction result for each')
    parser.add_argument('config', help='test config file path')
    parser.add_argument('prediction_path', help='prediction path where test pkl result')
    parser.add_argument('show_dir', help='directory where painted images will be saved')
    parser.add_argument('--show', action='store_true', help='show results')
    parser.add_argument('--wait-time', type=float, default=0, help='the interval of show (s), 0 is block')
    parser.add_argument('--topk', default=20, type=int, help='saved Number of the highest topk and lowest topk after index sorting')
    parser.add_argument('--show-score-thr', type=float, default=0, help='score threshold (default: 0.)')
    parser.add_argument('--overlay-gt-pred', action='store_true', help='whether to plot gts and predictions on the same image.If False, predictions and gts will be plotted on two sameimage which will be concatenated in vertical direction.The image above is drawn with gt, and the image below isdrawn with the prediction result.')
    parser.add_argument('--cfg-options', nargs='+', action=DictAction, help='override some settings in the used config, the key-value pair in xxx=yyy format will be merged into config file. If the value to be overwritten is a list, it should be like key="[a,b]" or key=a,b It also allows nested list/tuple values, e.g. key="[(a,b),(c,d)]" Note that the quotation marks are necessary and that no white space is allowed.')
    args = parser.parse_args()
    return args

def parse_args():
    parser = argparse.ArgumentParser(description='MMDet benchmark a model')
    parser.add_argument('config', help='test config file path')
    parser.add_argument('checkpoint', help='checkpoint file')
    parser.add_argument('--repeat-num', type=int, default=1, help='number of repeat times of measurement for averaging the results')
    parser.add_argument('--max-iter', type=int, default=2000, help='num of max iter')
    parser.add_argument('--log-interval', type=int, default=50, help='interval of logging')
    parser.add_argument('--fuse-conv-bn', action='store_true', help='Whether to fuse conv and bn, this will slightly increasethe inference speed')
    parser.add_argument('--cfg-options', nargs='+', action=DictAction, help='override some settings in the used config, the key-value pair in xxx=yyy format will be merged into config file. If the value to be overwritten is a list, it should be like key="[a,b]" or key=a,b It also allows nested list/tuple values, e.g. key="[(a,b),(c,d)]" Note that the quotation marks are necessary and that no white space is allowed.')
    parser.add_argument('--launcher', choices=['none', 'pytorch', 'slurm', 'mpi'], default='none', help='job launcher')
    parser.add_argument('--local_rank', type=int, default=0)
    args = parser.parse_args()
    if 'LOCAL_RANK' not in os.environ:
        os.environ['LOCAL_RANK'] = str(args.local_rank)
    return args

def parse_args():
    parser = argparse.ArgumentParser(description='Optimize anchor parameters.')
    parser.add_argument('config', help='Train config file path.')
    parser.add_argument('--device', default='cuda:0', help='Device used for calculating.')
    parser.add_argument('--input-shape', type=int, nargs='+', default=[608, 608], help='input image size')
    parser.add_argument('--algorithm', default='differential_evolution', help='Algorithm used for anchor optimizing.Support k-means and differential_evolution for YOLO.')
    parser.add_argument('--iters', default=1000, type=int, help='Maximum iterations for optimizer.')
    parser.add_argument('--output-dir', default=None, type=str, help='Path to save anchor optimize result.')
    args = parser.parse_args()
    return args

def make_parser():
    parser = argparse.ArgumentParser('OC-SORT parameters')
    parser.add_argument('-b', '--batch-size', type=int, default=1, help='batch size')
    parser.add_argument('-d', '--devices', default=None, type=int, help='device for training')
    parser.add_argument('--local_rank', default=0, type=int, help='local rank for dist training')
    parser.add_argument('--num_machines', default=1, type=int, help='num of node for training')
    parser.add_argument('--machine_rank', default=0, type=int, help='node rank for multi-node training')
    parser.add_argument('-f', '--exp_file', default=None, type=str, help='pls input your expriment description file')
    parser.add_argument('--test', dest='test', default=False, action='store_true', help='Evaluating on test-dev set.')
    parser.add_argument('opts', help='Modify config options using the command-line', default=None, nargs=argparse.REMAINDER)
    parser.add_argument('-c', '--ckpt', default=None, type=str, help='ckpt for eval')
    parser.add_argument('--conf', default=0.1, type=float, help='test conf')
    parser.add_argument('--nms', default=0.7, type=float, help='test nms threshold')
    parser.add_argument('--tsize', default=[800, 1440], nargs='+', type=int, help='test img size')
    parser.add_argument('--seed', default=None, type=int, help='eval seed')
    parser.add_argument('--track_thresh', type=float, default=0.6, help='detection confidence threshold')
    parser.add_argument('--iou_thresh', type=float, default=0.3, help='the iou threshold in Sort for matching')
    parser.add_argument('--min_hits', type=int, default=3, help='min hits to create track in SORT')
    parser.add_argument('--inertia', type=float, default=0.2, help='the weight of VDC term in cost matrix')
    parser.add_argument('--deltat', type=int, default=3, help='time step difference to estimate direction')
    parser.add_argument('--track_buffer', type=int, default=30, help='the frames for keep lost tracks')
    parser.add_argument('--match_thresh', type=float, default=0.9, help='matching threshold for tracking')
    parser.add_argument('--gt-type', type=str, default='_val_half', help='suffix to find the gt annotation')
    parser.add_argument('--public', action='store_true', help='use public detection')
    parser.add_argument('--asso', default='iou', help='similarity function: iou/giou/diou/ciou/ctdis')
    parser.add_argument('--raw_results_path', type=str, default='exps/permatrack_kitti_test/', help='path to the raw tracking results from other tracks')
    parser.add_argument('--out_path', type=str, help='path to save output results')
    parser.add_argument('--hp', action='store_true', help='use head padding to add the missing objects during             initializing the tracks (offline).')
    parser.add_argument('--demo_type', default='image', help='demo type, eg. image, video and webcam')
    parser.add_argument('--path', default='./videos/demo.mp4', help='path to images or video')
    parser.add_argument('--camid', type=int, default=0, help='webcam demo camera id')
    parser.add_argument('--save_result', action='store_true', help='whether to save the inference result of image/video')
    parser.add_argument('--device', default='gpu', type=str, help='device to run our model, can either be cpu or gpu')
    return parser

