# Cluster 4

def list_local_files(local_path):
    files_list = []
    for root, subdirectories, files in os.walk(local_path):
        for file in files:
            relative_path = os.path.join(root, file)
            files_list.append(relative_path)
    return files_list

def regional_pii(text):
    import nltk
    from nltk import word_tokenize, pos_tag, ne_chunk
    from nltk.corpus import stopwords
    resources = ['punkt', 'maxent_ne_chunker', 'stopwords', 'words', 'averaged_perceptron_tagger']
    try:
        nltk_resources = ['tokenizers/punkt', 'chunkers/maxent_ne_chunker', 'corpora/words.zip']
        for resource in nltk_resources:
            if not nltk.data.find(resource):
                raise LookupError()
    except LookupError:
        for resource in resources:
            nltk.download(resource)
    stop_words = set(stopwords.words('english'))
    words = word_tokenize(text)
    tagged_words = pos_tag(words)
    named_entities = ne_chunk(tagged_words)
    locations = []
    for entity in named_entities:
        if isinstance(entity, nltk.tree.Tree):
            if entity.label() in ['GPE', 'GSP', 'LOCATION', 'FACILITY']:
                location_name = ' '.join([word for word, tag in entity.leaves() if word.lower() not in stop_words and len(word) > 2])
                locations.append(location_name)
    return list(set(locations))

