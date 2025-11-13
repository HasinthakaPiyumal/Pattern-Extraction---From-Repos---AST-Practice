# Cluster 5

def compute_similarity(text1: str, text2: str) -> float:
    """Compute cosine similarity between two texts using TF-IDF."""
    try:
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return float(similarity)
    except Exception as e:
        logger.error(f'Error computing similarity: {e}')
        return 0.0

class ResponseEvaluator:
    """Evaluates response quality using multiple metrics."""

    def __init__(self):
        """Initialize evaluator with models and vectorizers."""
        self.tfidf = TfidfVectorizer(stop_words='english')
        try:
            self.semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            logger.warning(f'Could not load semantic model: {e}')
            self.semantic_model = None

    def evaluate_responses(self, response_1: str, response_2: str) -> Tuple[float, Dict[str, float]]:
        """Evaluate responses using multiple metrics."""
        scores = {}
        len_ratio = min(len(response_1), len(response_2)) / max(len(response_1), len(response_2))
        scores['length_ratio'] = len_ratio
        try:
            tfidf_matrix = self.tfidf.fit_transform([response_1, response_2])
            scores['lexical_similarity'] = float(cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0])
        except Exception:
            scores['lexical_similarity'] = 0.0
        if self.semantic_model:
            try:
                embeddings = self.semantic_model.encode([response_1, response_2])
                scores['semantic_similarity'] = float(cosine_similarity([embeddings[0]], [embeddings[1]])[0][0])
            except Exception:
                scores['semantic_similarity'] = 0.0
        scores['edit_similarity'] = textdistance.levenshtein.normalized_similarity(response_1, response_2)
        weights = {'semantic_similarity': 0.4, 'lexical_similarity': 0.3, 'edit_similarity': 0.2, 'length_ratio': 0.1}
        total_score = sum((scores.get(k, 0) * v for k, v in weights.items()))
        return (total_score, scores)

def __init__(self):
    """Initialize evaluator with models and vectorizers."""
    self.tfidf = TfidfVectorizer(stop_words='english')
    try:
        self.semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
    except Exception as e:
        logger.warning(f'Could not load semantic model: {e}')
        self.semantic_model = None

def evaluate_responses(self, response_1: str, response_2: str) -> Tuple[float, Dict[str, float]]:
    """Evaluate responses using multiple metrics."""
    scores = {}
    len_ratio = min(len(response_1), len(response_2)) / max(len(response_1), len(response_2))
    scores['length_ratio'] = len_ratio
    try:
        tfidf_matrix = self.tfidf.fit_transform([response_1, response_2])
        scores['lexical_similarity'] = float(cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0])
    except Exception:
        scores['lexical_similarity'] = 0.0
    if self.semantic_model:
        try:
            embeddings = self.semantic_model.encode([response_1, response_2])
            scores['semantic_similarity'] = float(cosine_similarity([embeddings[0]], [embeddings[1]])[0][0])
        except Exception:
            scores['semantic_similarity'] = 0.0
    scores['edit_similarity'] = textdistance.levenshtein.normalized_similarity(response_1, response_2)
    weights = {'semantic_similarity': 0.4, 'lexical_similarity': 0.3, 'edit_similarity': 0.2, 'length_ratio': 0.1}
    total_score = sum((scores.get(k, 0) * v for k, v in weights.items()))
    return (total_score, scores)

