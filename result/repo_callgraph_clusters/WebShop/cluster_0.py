# Cluster 0

def configure_logger(log_dir, wandb):
    logger.configure(log_dir, format_strs=['log'])
    global tb
    type_strs = ['json', 'stdout']
    if wandb:
        type_strs += ['wandb']
    tb = logger.Logger(log_dir, [logger.make_output_format(type_str, log_dir) for type_str in type_strs])
    global log
    log = logger.log

def get_dataset(split, mem=False):
    states, actions, idxs, sizes, images = get_data(split, mem)
    state_encodings = tokenizer(states, padding='max_length', max_length=512, truncation=True, return_tensors='pt')
    action_encodings = tokenizer(actions, padding='max_length', max_length=128, truncation=True, return_tensors='pt')
    dataset = {'state_input_ids': state_encodings['input_ids'], 'state_attention_mask': state_encodings['attention_mask'], 'action_input_ids': action_encodings['input_ids'].split(sizes), 'action_attention_mask': action_encodings['attention_mask'].split(sizes), 'sizes': sizes, 'images': torch.tensor(images), 'labels': idxs}
    return Dataset.from_dict(dataset)

def get_dataset(name, flip=False, variant=None, size=None):
    fname = name + '-flip' if flip else name
    fpath = os.path.join(os.path.dirname(__file__), fname)
    d = {}
    splits = ['train', 'validation', 'test']
    if name == 'web_search':
        splits = ['train', 'validation', 'test', 'all']
    for split in splits:
        input, output = get_data(split) if name != 'nl2bash' else get_data(split, variant=variant)
        l = len(input) if size is None else int(len(input) * size)
        print('{} size: {}'.format(split, l))
        if flip:
            input, output = (output, input)
        input, output = (input[:l], output[:l])
        d[split] = process_dataset(input, output)
    d = DatasetDict(d)
    return d

def process_dataset(input, output, max_len=256):
    input_encodings = tokenizer(input, padding='max_length', max_length=max_len, truncation=True, return_tensors='pt')
    output_encodings = tokenizer(output, padding='max_length', max_length=max_len, truncation=True, return_tensors='pt')
    labels = output_encodings['input_ids']
    decoder_input_ids = shift_tokens_right(labels, PAD_TOKEN_ID, EOS_TOKEN_ID)
    labels[labels[:, :] == PAD_TOKEN_ID] = -100
    dataset = Dataset.from_dict({'input_ids': input_encodings['input_ids'], 'attention_mask': input_encodings['attention_mask'], 'decoder_input_ids': decoder_input_ids, 'labels': labels})
    dataset.set_format(type='torch', columns=['input_ids', 'labels', 'decoder_input_ids', 'attention_mask'])
    return dataset

def configure(dir=None, format_strs=None):
    if dir is None:
        dir = os.getenv('OPENAI_LOGDIR')
    if dir is None:
        dir = osp.join(tempfile.gettempdir(), datetime.datetime.now().strftime('openai-%Y-%m-%d-%H-%M-%S-%f'))
    assert isinstance(dir, str)
    os.makedirs(dir, exist_ok=True)
    log_suffix = ''
    rank = 0
    for varname in ['PMI_RANK', 'OMPI_COMM_WORLD_RANK']:
        if varname in os.environ:
            rank = int(os.environ[varname])
    if rank > 0:
        log_suffix = '-rank%03i' % rank
    if format_strs is None:
        if rank == 0:
            format_strs = os.getenv('OPENAI_LOG_FORMAT', 'stdout,log,csv').split(',')
        else:
            format_strs = os.getenv('OPENAI_LOG_FORMAT_MPI', 'log').split(',')
    format_strs = filter(None, format_strs)
    output_formats = [make_output_format(f, dir, log_suffix) for f in format_strs]
    Logger.CURRENT = Logger(dir=dir, output_formats=output_formats)
    log('Logging to %s' % dir)

def _configure_default_logger():
    format_strs = None
    if 'OPENAI_LOG_FORMAT' not in os.environ:
        format_strs = ['stdout']
    configure(format_strs=format_strs)
    Logger.DEFAULT = Logger.CURRENT

class scoped_configure(object):

    def __init__(self, dir=None, format_strs=None):
        self.dir = dir
        self.format_strs = format_strs
        self.prevlogger = None

    def __enter__(self):
        self.prevlogger = Logger.CURRENT
        configure(dir=self.dir, format_strs=self.format_strs)

    def __exit__(self, *args):
        Logger.CURRENT.close()
        Logger.CURRENT = self.prevlogger

def __enter__(self):
    self.prevlogger = Logger.CURRENT
    configure(dir=self.dir, format_strs=self.format_strs)

