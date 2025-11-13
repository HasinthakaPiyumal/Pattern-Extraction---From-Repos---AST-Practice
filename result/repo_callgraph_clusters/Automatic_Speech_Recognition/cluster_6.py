# Cluster 6

def _integer2Chinese(number):
    """
    Converting integer to Chinese expression
    """
    charSectionSet = ['', '万', '亿', '万亿']
    result = ''
    zero = False
    unitPos = 0
    if number == 0:
        return '零'
    while number > 0:
        section = number % 10000
        if zero:
            result = '零' + result
        sec_result = _section2Chinese(section)
        if section != 0:
            sec_result += charSectionSet[unitPos]
        result = sec_result + result
        if section < 1000 and section > 0:
            zero = True
        number = number // 10000
        unitPos += 1
    return result

