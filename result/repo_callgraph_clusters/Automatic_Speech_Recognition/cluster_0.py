# Cluster 0

@wraps(func)
def wrapper(*args, **kwargs):
    print(func.__name__ + '...')
    start = time.time()
    result = func(*args, **kwargs)
    end = time.time()
    print(str(func.__name__ + ' in ' + str(end - start) + ' s'))
    return result

@describe
def logging(model, logfile, errorRate, epoch=0, delta_time=0, mode='train'):
    """ log the cost and error rate and time while training or testing
    """
    if mode != 'train' and mode != 'test' and (mode != 'config') and (mode != 'dev'):
        raise TypeError('mode should be train or test or config.')
    logfile = logfile
    if mode == 'config':
        with open(logfile, 'a') as myfile:
            myfile.write(str(model.config) + '\n')
    elif mode == 'train':
        with open(logfile, 'a') as myfile:
            myfile.write(str(time.strftime('%X %x %Z')) + '\n')
            myfile.write('Epoch:' + str(epoch + 1) + ' ' + 'train error rate:' + str(errorRate) + '\n')
            myfile.write('Epoch:' + str(epoch + 1) + ' ' + 'train time:' + str(delta_time) + ' s\n')
    elif mode == 'test':
        logfile = logfile + '_TEST'
        with open(logfile, 'a') as myfile:
            myfile.write(str(model.config) + '\n')
            myfile.write(str(time.strftime('%X %x %Z')) + '\n')
            myfile.write('test error rate:' + str(errorRate) + '\n')
    elif mode == 'dev':
        logfile = logfile + '_DEV'
        with open(logfile, 'a') as myfile:
            myfile.write(str(model.config) + '\n')
            myfile.write(str(time.strftime('%X %x %Z')) + '\n')
            myfile.write('development error rate:' + str(errorRate) + '\n')

def get_num_classes(level):
    if level == 'phn':
        num_classes = 62
    elif level == 'cha':
        num_classes = 29
    elif level == 'seq2seq':
        num_classes = 30
    else:
        raise ValueError('level must be phn, cha or seq2seq, but the given level is %s' % str(level))
    return num_classes

class CorpusGardener(object):
    """
    Preprocessing multiple language corpuses, and gathering
    them into batches
    """

    def __init__(self, remove_duplicate_space=True):
        self.remove_dubplicate_space = remove_duplicate_space
        self.save_dir = '/home/pony/github/data/spellingChecker/raw'

    def process_poetry(self, data_dir='/media/pony/DLdigest/data/languageModel/chinese-poetry/json'):
        """
        Process Tang and Song poems dataset
        """
        save_dir = os.path.join(self.save_dir, 'poem')
        check_path_exists(save_dir)
        count = 0
        for entry in os.scandir(data_dir):
            if entry.name.startswith('poet'):
                with open(entry.path, 'r') as json_file:
                    poems = json.load(json_file)
                    for p in poems:
                        paras = HanziConv.toSimplified(''.join(p['paragraphs']).replace('\n', ''))
                        paras = filter_punctuation(paras)
                        for para in paras.split(' '):
                            if len(para.strip()) > 1:
                                pys = ' '.join(np.array(pinyin(para)).flatten())
                                with open(os.path.join(save_dir, str(count // 400000 + 1) + '.txt'), 'a') as f:
                                    f.write(para + ',' + pys + '\n')
                                count += 1

    def process_dureader(self, data_dir='/media/pony/DLdigest/data/languageModel/dureader-raw/'):
        """
        Processing Baidu released QA Reader Dataset
        """
        save_dir = os.path.join(self.save_dir, 'dureader')
        check_path_exists(save_dir)
        count = 0
        for entry in os.scandir(data_dir):
            if entry.name.endswith('json'):
                print(entry.path)
                with open(entry.path, 'r') as f:
                    for line in f:
                        contents = json.loads(line)
                        con = []
                        try:
                            answers = ''.join(contents['answers'])
                            con.append(answers)
                            questions = contents['question']
                            con.append(questions)
                            for doc in contents['documents']:
                                paragraphs = ''.join(doc['paragraphs'])
                                title = doc['title']
                                con.append(paragraphs)
                                con.append(title)
                            con = HanziConv.toSimplified(''.join(con).replace('\n', ''))
                            cons = filter_punctuation(con)
                            for c in cons.split(' '):
                                if len(c.strip()) > 1:
                                    pys = ' '.join(np.array(pinyin(c)).flatten())
                                    count += 1
                                    with open(os.path.join(save_dir, str(count // 400000 + 1) + '.txt'), 'a') as f:
                                        f.write(c + ',' + pys + '\n')
                        except KeyError:
                            continue

    def process_audioLabels(self, data_dir='/media/pony/DLdigest/data/ASR_zh/'):
        """
        Processing label files in collected Chinese audio dataset
        """
        save_dir = os.path.join(self.save_dir, 'audioLabels')
        check_path_exists(save_dir)
        count = 0
        for subdir, dirs, files in os.walk(data_dir):
            print(subdir)
            for f in files:
                if f.endswith('label'):
                    fullFilename = os.path.join(subdir, f)
                    with open(fullFilename, 'r') as f:
                        line = f.read()
                        con = HanziConv.toSimplified(line)
                        con = filter_punctuation(con)
                        for c in con.split(' '):
                            if len(c.strip()) > 1:
                                pys = ' '.join(np.array(pinyin(c)).flatten())
                                count += 1
                                with open(os.path.join(save_dir, str(count // 400000 + 1) + '.txt'), 'a') as f:
                                    f.write(c + ',' + pys + '\n')

def process_poetry(self, data_dir='/media/pony/DLdigest/data/languageModel/chinese-poetry/json'):
    """
        Process Tang and Song poems dataset
        """
    save_dir = os.path.join(self.save_dir, 'poem')
    check_path_exists(save_dir)
    count = 0
    for entry in os.scandir(data_dir):
        if entry.name.startswith('poet'):
            with open(entry.path, 'r') as json_file:
                poems = json.load(json_file)
                for p in poems:
                    paras = HanziConv.toSimplified(''.join(p['paragraphs']).replace('\n', ''))
                    paras = filter_punctuation(paras)
                    for para in paras.split(' '):
                        if len(para.strip()) > 1:
                            pys = ' '.join(np.array(pinyin(para)).flatten())
                            with open(os.path.join(save_dir, str(count // 400000 + 1) + '.txt'), 'a') as f:
                                f.write(para + ',' + pys + '\n')
                            count += 1

def process_dureader(self, data_dir='/media/pony/DLdigest/data/languageModel/dureader-raw/'):
    """
        Processing Baidu released QA Reader Dataset
        """
    save_dir = os.path.join(self.save_dir, 'dureader')
    check_path_exists(save_dir)
    count = 0
    for entry in os.scandir(data_dir):
        if entry.name.endswith('json'):
            print(entry.path)
            with open(entry.path, 'r') as f:
                for line in f:
                    contents = json.loads(line)
                    con = []
                    try:
                        answers = ''.join(contents['answers'])
                        con.append(answers)
                        questions = contents['question']
                        con.append(questions)
                        for doc in contents['documents']:
                            paragraphs = ''.join(doc['paragraphs'])
                            title = doc['title']
                            con.append(paragraphs)
                            con.append(title)
                        con = HanziConv.toSimplified(''.join(con).replace('\n', ''))
                        cons = filter_punctuation(con)
                        for c in cons.split(' '):
                            if len(c.strip()) > 1:
                                pys = ' '.join(np.array(pinyin(c)).flatten())
                                count += 1
                                with open(os.path.join(save_dir, str(count // 400000 + 1) + '.txt'), 'a') as f:
                                    f.write(c + ',' + pys + '\n')
                    except KeyError:
                        continue

def process_audioLabels(self, data_dir='/media/pony/DLdigest/data/ASR_zh/'):
    """
        Processing label files in collected Chinese audio dataset
        """
    save_dir = os.path.join(self.save_dir, 'audioLabels')
    check_path_exists(save_dir)
    count = 0
    for subdir, dirs, files in os.walk(data_dir):
        print(subdir)
        for f in files:
            if f.endswith('label'):
                fullFilename = os.path.join(subdir, f)
                with open(fullFilename, 'r') as f:
                    line = f.read()
                    con = HanziConv.toSimplified(line)
                    con = filter_punctuation(con)
                    for c in con.split(' '):
                        if len(c.strip()) > 1:
                            pys = ' '.join(np.array(pinyin(c)).flatten())
                            count += 1
                            with open(os.path.join(save_dir, str(count // 400000 + 1) + '.txt'), 'a') as f:
                                f.write(c + ',' + pys + '\n')

def _c2n(c_str):
    """
    将汉字转化成数字
    """
    if c_str == '':
        return u'0'
    src = u'点零一二三四五六七八九'
    dst = u'.0123456789'
    for i, c in enumerate(src):
        c_str = c_str.replace(c, dst[i])
    return c_str

class DigitPrecessor(object):

    def __init__(self, mode):
        assert mode == 'digit2char' or mode == 'char2digit', 'Wrong mode: %s' % str(mode)
        self.mode = mode

    def processString(self, string):
        if self.mode == 'digit2char':
            return convertDigit2Character(string)
        else:
            return convertCharacter2Digit(string)

    def processFile(self, fileName):
        result = []
        assert os.path.isfile(fileName), 'Wrong file path: %s' % str(fileName)
        with codecs.open(fileName, 'r', 'utf-8') as f:
            content = f.readlines()
        if self.mode == 'digit2char':
            for string in content:
                result.append(convertDigit2Character(string))
        else:
            for string in content:
                result.append(convertCharacter2Digit(string))
        return result

def __init__(self, mode):
    assert mode == 'digit2char' or mode == 'char2digit', 'Wrong mode: %s' % str(mode)
    self.mode = mode

