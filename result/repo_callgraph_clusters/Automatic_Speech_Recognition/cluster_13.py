# Cluster 13

def lookup(cd_id, logfile):
    with open(logfile, 'r') as f:
        content = f.readlines()
    for line in content:
        if int(line.split(' ')[-1][2:]) == int(cd_id[2:]):
            if '.' in line.split(' ')[-3]:
                newName = line.split(' ')[-3]
                return newName
        else:
            continue

def split_data_by_s5(src_dir, des_dir, keywords=['train_si284', 'test_eval92', 'test_dev93']):
    count = 0
    for key in keywords:
        wav_file_list = os.path.join(src_dir, key + '.flist')
        label_file_list = os.path.join(src_dir, key + '.txt')
        new_path = check_path_exists(os.path.join(des_dir, key))
        with open(wav_file_list, 'r') as wfl:
            wfl_contents = wfl.readlines()
            for line in wfl_contents:
                line = line.strip()
                if os.path.isfile(line):
                    shutil.copyfile(line, os.path.join(des_dir, key, line.split('/')[-1]))
                    print(line)
                else:
                    tmp = '/'.join(line.split('/')[:-1] + [line.split('/')[-1].upper()])
                    shutil.copyfile(tmp, os.path.join(des_dir, key, line.split('/')[-1].replace('WV1', 'wv1')))
                    print(tmp)
        with open(label_file_list, 'r') as lfl:
            lfl_contents = lfl.readlines()
            for line in lfl_contents:
                label = ' '.join(line.strip().split(' ')[1:])
                with open(os.path.join(des_dir, key, line.strip().split(' ')[0] + '.label'), 'w') as lf:
                    lf.writelines(label)
                print(key, label)

def _get_gewei(c_str):
    """
    分割出个位数字
    """
    if u'百零' in c_str:
        return _c2n(c_str.split(u'百零')[1])
    elif u'十' in c_str:
        return _c2n(c_str.split(u'十')[1])
    elif u'千零' in c_str:
        return _c2n(c_str.split(u'千零')[1])
    else:
        return '0'

def _get_shiwei(c_str):
    """
    分割出十位数字
    """
    if u'百零' in c_str:
        return u'0'
    elif u'百' in c_str:
        return _c2n(c_str.split(u'百')[1].split(u'十')[0])
    elif u'千零' in c_str and u'十' in c_str:
        return _c2n(c_str.split(u'千零')[1].split(u'十')[0])
    elif u'十' in c_str:
        if c_str.split(u'十')[0] == '':
            return u'1'
        return _c2n(c_str.split(u'十')[0])
    else:
        return u'0'

def _get_baiwei(c_str):
    """
    分割出百位数字
    """
    if u'千零' in c_str:
        return u'0'
    elif u'千' in c_str:
        return _c2n(c_str.split(u'千')[1].split(u'百')[0])
    elif u'百' in c_str:
        return _c2n(c_str.split(u'百')[0])
    else:
        return ''

def _get_qianwei(c_str):
    """
    分割出千位数字
    """
    if u'万零' in c_str:
        return u'0'
    elif u'万' in c_str:
        return _c2n(c_str.split(u'万')[1].split(u'千')[0])
    elif u'千' in c_str:
        return _c2n(c_str.split(u'千')[0])
    else:
        return ''

def _convert_section(c_str):
    if _check_whether_special(c_str):
        return _c2n(c_str)
    else:
        return _get_complex(c_str)

def _convert_all(c_str):
    if _check_whether_special(c_str):
        return _c2n(c_str)
    result = ''
    flag = 0
    float_part = ''
    if u'点' in c_str:
        flag1 = 1
        i = c_str.split(u'点')[1]
        c_str = c_str.split(u'点')[0]
        float_part = '.' + _convert_section(i)
    if u'亿' in c_str:
        flag = 8
        i = c_str.split(u'亿')[0]
        c_str = c_str.split(u'亿')[1]
        result += _convert_section(i)
        if c_str == '':
            result += '00000000'
            return result
    if u'万' in c_str:
        flag = 4
        i = c_str.split(u'万')[0]
        c_str = c_str.split(u'万')[1]
        result += _convert_section(i)
        if c_str == '':
            result += '0000'
            return result
    right = _get_complex(c_str)
    return result + '0' * (flag - len(_get_complex(c_str))) + right + float_part

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

