# Cluster 1

def load_batched_data(mfccPath, labelPath, batchSize, mode, level):
    """returns 3-element tuple: batched data (list), maxTimeLength (int), and
       total number of samples (int)"""
    return data_lists_to_batches([np.load(os.path.join(mfccPath, fn)) for fn in os.listdir(mfccPath)], [np.load(os.path.join(labelPath, fn)) for fn in os.listdir(labelPath)], batchSize, level) + (len(os.listdir(mfccPath)),)

def check_path_exists(path):
    """ check a path exists or not
    """
    if isinstance(path, list):
        for p in path:
            if not os.path.exists(p):
                os.makedirs(p)
    elif not os.path.exists(path):
        os.makedirs(path)

def get_data(datadir, level, train_dataset, dev_dataset, test_dataset, mode):
    if mode == 'train':
        train_feature_dirs = [os.path.join(os.path.join(datadir, level, train_dataset), i, 'feature') for i in os.listdir(os.path.join(datadir, level, train_dataset))]
        train_label_dirs = [os.path.join(os.path.join(datadir, level, train_dataset), i, 'label') for i in os.listdir(os.path.join(datadir, level, train_dataset))]
        return (train_feature_dirs, train_label_dirs)
    if mode == 'dev':
        dev_feature_dirs = [os.path.join(os.path.join(datadir, level, dev_dataset), i, 'feature') for i in os.listdir(os.path.join(datadir, level, dev_dataset))]
        dev_label_dirs = [os.path.join(os.path.join(datadir, level, dev_dataset), i, 'label') for i in os.listdir(os.path.join(datadir, level, dev_dataset))]
        return (dev_feature_dirs, dev_label_dirs)
    if mode == 'test':
        test_feature_dirs = [os.path.join(os.path.join(datadir, level, test_dataset), i, 'feature') for i in os.listdir(os.path.join(datadir, level, test_dataset))]
        test_label_dirs = [os.path.join(os.path.join(datadir, level, test_dataset), i, 'label') for i in os.listdir(os.path.join(datadir, level, test_dataset))]
        return (test_feature_dirs, test_label_dirs)

def get_data(datadir, level, train_dataset, dev_dataset, test_dataset, mode):
    if mode == 'train':
        train_feature_dirs = [os.path.join(os.path.join(datadir, level, train_dataset), i, 'feature') for i in os.listdir(os.path.join(datadir, level, train_dataset))]
        train_label_dirs = [os.path.join(os.path.join(datadir, level, train_dataset), i, 'label') for i in os.listdir(os.path.join(datadir, level, train_dataset))]
        return (train_feature_dirs, train_label_dirs)
    if mode == 'dev':
        dev_feature_dirs = [os.path.join(os.path.join(datadir, level, dev_dataset), i, 'feature') for i in os.listdir(os.path.join(datadir, level, dev_dataset))]
        dev_label_dirs = [os.path.join(os.path.join(datadir, level, dev_dataset), i, 'label') for i in os.listdir(os.path.join(datadir, level, dev_dataset))]
        return (dev_feature_dirs, dev_label_dirs)
    if mode == 'test':
        test_feature_dirs = [os.path.join(os.path.join(datadir, level, test_dataset), i, 'feature') for i in os.listdir(os.path.join(datadir, level, test_dataset))]
        test_label_dirs = [os.path.join(os.path.join(datadir, level, test_dataset), i, 'label') for i in os.listdir(os.path.join(datadir, level, test_dataset))]
        return (test_feature_dirs, test_label_dirs)

def wav2feature(rootdir, save_directory, mode, feature_len, level, keywords, win_len, win_step, seq2seq, save):
    feat_dir = os.path.join(save_directory, level, keywords, mode)
    label_dir = os.path.join(save_directory, level, keywords, 'label')
    if not os.path.exists(label_dir):
        os.makedirs(label_dir)
    if not os.path.exists(feat_dir):
        os.makedirs(feat_dir)
    count = 0
    for subdir, dirs, files in os.walk(rootdir):
        for file in files:
            fullFilename = os.path.join(subdir, file)
            filenameNoSuffix = os.path.splitext(fullFilename)[0]
            if file.endswith('.WAV'):
                rate, sig = (16000, np.fromfile(fullFilename, dtype=np.int16)[512:])
                feat = calcfeat_delta_delta(sig, rate, win_length=win_len, win_step=win_step, mode=mode, feature_len=feature_len)
                feat = preprocessing.scale(feat)
                feat = np.transpose(feat)
                print(feat.shape)
                if level == 'phn':
                    labelFilename = filenameNoSuffix + '.PHN'
                    phenome = []
                    with open(labelFilename, 'r') as f:
                        if seq2seq is True:
                            phenome.append(len(phn))
                        for line in f.read().splitlines():
                            s = line.split(' ')[2]
                            p_index = phn.index(s)
                            phenome.append(p_index)
                        if seq2seq is True:
                            phenome.append(len(phn) + 1)
                        print(phenome)
                    phenome = np.array(phenome)
                elif level == 'cha':
                    labelFilename = filenameNoSuffix + '.WRD'
                    phenome = []
                    sentence = ''
                    with open(labelFilename, 'r') as f:
                        for line in f.read().splitlines():
                            s = line.split(' ')[2]
                            sentence += s + ' '
                            if seq2seq is True:
                                phenome.append(28)
                            for c in s:
                                if c == "'":
                                    phenome.append(27)
                                else:
                                    phenome.append(ord(c) - 96)
                            phenome.append(0)
                        phenome = phenome[:-1]
                        if seq2seq is True:
                            phenome.append(29)
                    print(phenome)
                    print(sentence)
                count += 1
                print('file index:', count)
                if save:
                    speaker, sentence_name = filenameNoSuffix.split('/')[-2:]
                    feature_filename = '{}/{}-{}.npy'.format(feat_dir, speaker, sentence_name)
                    np.save(feature_filename, feat)
                    label_filename = '{}/{}-{}.npy'.format(label_dir, speaker, sentence_name)
                    print(label_filename)
                    np.save(label_filename, phenome)

def wav2feature(root_directory, save_directory, name, win_len, win_step, mode, feature_len, seq2seq, save):
    """
  To run for WSJ corpus, you should download sph2pipe_v2.5 first!
  """
    count = 0
    dirid = 0
    level = 'cha' if seq2seq is False else 'seq2seq'
    for subdir, dirs, files in os.walk(root_directory):
        for f in files:
            fullFilename = os.path.join(subdir, f)
            filenameNoSuffix = os.path.splitext(fullFilename)[0]
            if f.endswith('.wv1') or f.endswith('.wav'):
                rate = None
                sig = None
                try:
                    rate, sig = wav.read(fullFilename)
                except ValueError as e:
                    sph2pipe = os.path.join(sph2pipe_dir, 'sph2pipe')
                    wav_name = fullFilename.replace('wv1', 'wav')
                    check_call(['./sph2pipe', '-f', 'rif', fullFilename, wav_name])
                    os.remove(fullFilename)
                    print(wav_name)
                    rate, sig = wav.read(wav_name)
                    os.remove(fullFilename)
                feat = calcfeat_delta_delta(sig, rate, win_length=win_len, win_step=win_step, feature_len=feature_len, mode=mode)
                feat = preprocessing.scale(feat)
                feat = np.transpose(feat)
                print(feat.shape)
                labelFilename = filenameNoSuffix + '.label'
                with open(labelFilename, 'r') as f:
                    characters = f.readline().strip().lower()
                targets = []
                if seq2seq is True:
                    targets.append(28)
                for c in characters:
                    if c == ' ':
                        targets.append(0)
                    elif c == "'":
                        targets.append(27)
                    else:
                        targets.append(ord(c) - 96)
                if seq2seq is True:
                    targets.append(29)
                targets = np.array(targets)
                print(targets)
                if save:
                    count += 1
                    if count % 1000 == 0:
                        dirid += 1
                    print('file index:', count)
                    print('dir index:', dirid)
                    label_dir = os.path.join(save_directory, level, name, str(dirid), 'label')
                    feat_dir = os.path.join(save_directory, level, name, str(dirid), mode)
                    if not os.path.isdir(label_dir):
                        os.makedirs(label_dir)
                    if not os.path.isdir(feat_dir):
                        os.makedirs(feat_dir)
                    featureFilename = os.path.join(feat_dir, filenameNoSuffix.split('/')[-1] + '.npy')
                    np.save(featureFilename, feat)
                    t_f = os.path.join(label_dir, filenameNoSuffix.split('/')[-1] + '.npy')
                    print(t_f)
                    np.save(t_f, targets)

def renameCD(src_dir, mode):
    logfile = mode + '.links.log'
    cd_dir = os.path.join(src_dir, mode)
    count = 0
    for subdir in os.listdir(cd_dir):
        if subdir.startswith('CD') or subdir.startswith('cd'):
            newName = lookup(subdir, os.path.join(src_dir, logfile))
            cd_path = os.path.join(src_dir, mode, subdir)
            new_cd_path = os.path.join(src_dir, mode, newName)
            os.rename(cd_path, new_cd_path)
            count += 1
            print('new file ', count, ': ', new_cd_path)

def extract(rootdir):
    for subdir, dirs, files in os.walk(rootdir):
        for f in files:
            if f.endswith('.zip'):
                fullFilename = os.path.join(rootdir, f)
                subprocess.call(['atool', '-x', fullFilename])
                print(f)

def preprocess(root_directory):
    """
    Function to walk through the directory and convert flac to wav files
    """
    try:
        check_call(['flac'])
    except OSError:
        raise OSError('Flac not installed. Install using apt-get install flac')
    for subdir, dirs, files in os.walk(root_directory):
        for f in files:
            filename = os.path.join(subdir, f)
            if f.endswith('.flac'):
                try:
                    check_call(['flac', '-d', filename])
                    os.remove(filename)
                except CalledProcessError as e:
                    print('Failed to convert file {}'.format(filename))
            elif f.endswith('.TXT'):
                os.remove(filename)
            elif f.endswith('.txt'):
                with open(filename, 'r') as fp:
                    lines = fp.readlines()
                    for line in lines:
                        sub_n = line.split(' ')[0] + '.label'
                        subfile = os.path.join(subdir, sub_n)
                        sub_c = ' '.join(line.split(' ')[1:])
                        sub_c = sub_c.lower()
                        with open(subfile, 'w') as sp:
                            sp.write(sub_c)
            elif f.endswith('.wav'):
                if not os.path.isfile(os.path.splitext(filename)[0] + '.label'):
                    raise ValueError('.label file not found for {}'.format(filename))
            else:
                pass

def wav2feature(root_directory, save_directory, name, win_len, win_step, mode, feature_len, seq2seq, save):
    count = 0
    dirid = 0
    level = 'cha' if seq2seq is False else 'seq2seq'
    data_dir = os.path.join(root_directory, name)
    preprocess(data_dir)
    for subdir, dirs, files in os.walk(data_dir):
        for f in files:
            fullFilename = os.path.join(subdir, f)
            filenameNoSuffix = os.path.splitext(fullFilename)[0]
            if f.endswith('.wav'):
                rate = None
                sig = None
                try:
                    rate, sig = wav.read(fullFilename)
                except ValueError as e:
                    if e.message == "File format 'NIST'... not understood.":
                        sf = Sndfile(fullFilename, 'r')
                    nframes = sf.nframes
                    sig = sf.read_frames(nframes)
                    rate = sf.samplerate
                feat = calcfeat_delta_delta(sig, rate, win_length=win_len, win_step=win_step, mode=mode, feature_len=feature_len)
                feat = preprocessing.scale(feat)
                feat = np.transpose(feat)
                print(feat.shape)
                labelFilename = filenameNoSuffix + '.label'
                with open(labelFilename, 'r') as f:
                    characters = f.readline().strip().lower()
                targets = []
                if seq2seq is True:
                    targets.append(28)
                for c in characters:
                    if c == ' ':
                        targets.append(0)
                    elif c == "'":
                        targets.append(27)
                    else:
                        targets.append(ord(c) - 96)
                if seq2seq is True:
                    targets.append(29)
                print(targets)
                if save:
                    count += 1
                    if count % 4000 == 0:
                        dirid += 1
                    print('file index:', count)
                    print('dir index:', dirid)
                    label_dir = os.path.join(save_directory, level, name, str(dirid), 'label')
                    feat_dir = os.path.join(save_directory, level, name, str(dirid), 'feature')
                    if not os.path.isdir(label_dir):
                        os.makedirs(label_dir)
                    if not os.path.isdir(feat_dir):
                        os.makedirs(feat_dir)
                    featureFilename = os.path.join(feat_dir, filenameNoSuffix.split('/')[-1] + '.npy')
                    np.save(featureFilename, feat)
                    t_f = os.path.join(label_dir, filenameNoSuffix.split('/')[-1] + '.npy')
                    print(t_f)
                    np.save(t_f, targets)

def nist2wav(src_dir):
    count = 0
    for subdir, dirs, files in os.walk(src_dir):
        for f in files:
            fullFilename = os.path.join(subdir, f)
            if f.endswith('.wv1') or f.endswith('.wv2'):
                count += 1
                os.system('./sph2pipe_v2.5/sph2pipe ' + fullFilename + ' -f rif ' + fullFilename + '.wav')
                print(fullFilename)

def save_obj(name, obj):
    with open(name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

class NGram:

    def __init__(self, rootdir):
        self.rootdir = rootdir

    def get_corpus(self):
        corpus = []
        word_count = {}
        biword_count = {}
        bigram = {}
        bigram['SOS'] = {}
        trigram = {}
        for subdir, dirs, files in os.walk(self.rootdir):
            for f in files:
                fullFilename = os.path.join(subdir, f)
                filenameNoSuffix = os.path.splitext(fullFilename)[0]
            if f.endswith('.label'):
                with open(fullFilename, 'r') as f:
                    line = f.readline()
                    corpus.append(line)
                    line = line.strip().split(' ')
                    len_sent = range(len(line))
                    for idx in len_sent:
                        word = line[idx]
                        word_count = inc_dict(word_count, word)
                        if not bigram.has_key(word):
                            bigram[word] = {}
                        if idx == 0:
                            bigram['SOS'] = inc_dict(bigram['SOS'], word)
                        elif idx != len(line) - 1:
                            bigram[word] = inc_dict(bigram[word], line[idx + 1])
                        else:
                            bigram[word] = inc_dict(bigram[word], 'EOS')
                        if idx == 0:
                            tri_key = 'SOS ' + word
                        else:
                            tri_key = line[idx - 1] + ' ' + word
                        if not trigram.has_key(tri_key):
                            trigram[tri_key] = {}
                        if idx == len(line) - 1:
                            trigram[tri_key] = inc_dict(trigram[tri_key], 'EOS')
                        else:
                            trigram[tri_key] = inc_dict(trigram[tri_key], line[idx + 1])
        return (corpus, word_count, bigram, trigram)

def get_corpus(self):
    corpus = []
    word_count = {}
    biword_count = {}
    bigram = {}
    bigram['SOS'] = {}
    trigram = {}
    for subdir, dirs, files in os.walk(self.rootdir):
        for f in files:
            fullFilename = os.path.join(subdir, f)
            filenameNoSuffix = os.path.splitext(fullFilename)[0]
        if f.endswith('.label'):
            with open(fullFilename, 'r') as f:
                line = f.readline()
                corpus.append(line)
                line = line.strip().split(' ')
                len_sent = range(len(line))
                for idx in len_sent:
                    word = line[idx]
                    word_count = inc_dict(word_count, word)
                    if not bigram.has_key(word):
                        bigram[word] = {}
                    if idx == 0:
                        bigram['SOS'] = inc_dict(bigram['SOS'], word)
                    elif idx != len(line) - 1:
                        bigram[word] = inc_dict(bigram[word], line[idx + 1])
                    else:
                        bigram[word] = inc_dict(bigram[word], 'EOS')
                    if idx == 0:
                        tri_key = 'SOS ' + word
                    else:
                        tri_key = line[idx - 1] + ' ' + word
                    if not trigram.has_key(tri_key):
                        trigram[tri_key] = {}
                    if idx == len(line) - 1:
                        trigram[tri_key] = inc_dict(trigram[tri_key], 'EOS')
                    else:
                        trigram[tri_key] = inc_dict(trigram[tri_key], line[idx + 1])
    return (corpus, word_count, bigram, trigram)

def inc_dict(dic, key):
    if not dic.has_key(key):
        dic[key] = 0
        dic[key] += 1
    return dic

