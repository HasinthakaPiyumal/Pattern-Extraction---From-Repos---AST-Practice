# Cluster 4

def find_word_in_string(w, s):
    return re.compile('\\b({0})\\b'.format(w), flags=re.IGNORECASE).search(s)

