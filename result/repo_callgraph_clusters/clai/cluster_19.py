# Cluster 19

def transform(corpus) -> (TfidfVectorizer, list):
    vectorizer = TfidfVectorizer(input='content', lowercase=True, analyzer='word', stop_words='english', ngram_range=(1, 2))
    vectors = vectorizer.fit_transform(corpus)
    vectorizer.stop_words_ = None
    return (vectorizer, vectors)

