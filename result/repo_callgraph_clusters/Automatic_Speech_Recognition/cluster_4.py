# Cluster 4

def _prepString(string):
    """
    Preprocessing the sentence and splitting the decimal, integer or special
    """
    decimal_set = re.findall('\\d+\\.\\d+', string)
    sub_str = re.sub('\\d+\\.\\d+', '_', string)
    newStr = _replaceDecimal(decimal_set, sub_str)
    integer_set = re.findall('\\d+年', newStr)
    sub_str = re.sub('\\d+年', '_', newStr)
    newStr = _replaceSpecial(integer_set, sub_str)
    integer_set = re.findall('\\d+', newStr)
    sub_str = re.sub('\\d+', '_', newStr)
    newStr = _replaceInteger(integer_set, sub_str)
    print('原句子:', string)
    print('新句子:', newStr)
    print('\n')
    return newStr

def convertCharacter2Digit(string):
    chinese_numbers = re.findall(u'[点零一二三四五六七八九十百千万亿]{1,}', string, re.S)
    sub_str = re.sub(u'[点零一二三四五六七八九十百千万亿]{1,}', '_', string)
    for chinese_number in chinese_numbers:
        digit = _convert_all(chinese_number)
        sub_str = sub_str.replace('_', digit, 1)
    print('原句子:', string)
    print('新句子:', sub_str)
    print('\n')
    return sub_str

