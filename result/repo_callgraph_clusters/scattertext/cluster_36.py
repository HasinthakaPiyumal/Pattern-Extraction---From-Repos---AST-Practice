# Cluster 36

def japanese_nlp(doc, entity_type=None, tag_type=None):
    tokenizer = _get_japanese_tokenizer()
    return _asian_tokenization(doc, entity_type, tag_type, tokenizer)

def chinese_nlp(doc, entity_type=None, tag_type=None):
    tokenizer = _get_chinese_tokenizer()
    return _asian_tokenization(doc, entity_type, tag_type, tokenizer)

