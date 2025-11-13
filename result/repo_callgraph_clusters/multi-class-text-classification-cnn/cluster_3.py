# Cluster 3

def clean_str(s):
    """Clean sentence"""
    s = re.sub("[^A-Za-z0-9(),!?\\'\\`]", ' ', s)
    s = re.sub("\\'s", " 's", s)
    s = re.sub("\\'ve", " 've", s)
    s = re.sub("n\\'t", " n't", s)
    s = re.sub("\\'re", " 're", s)
    s = re.sub("\\'d", " 'd", s)
    s = re.sub("\\'ll", " 'll", s)
    s = re.sub(',', ' , ', s)
    s = re.sub('!', ' ! ', s)
    s = re.sub('\\(', ' \\( ', s)
    s = re.sub('\\)', ' \\) ', s)
    s = re.sub('\\?', ' \\? ', s)
    s = re.sub('\\s{2,}', ' ', s)
    s = re.sub('\\S*(x{2,}|X{2,})\\S*', 'xxx', s)
    s = re.sub('[^\\x00-\\x7F]+', '', s)
    return s.strip().lower()

