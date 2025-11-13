# Cluster 15

def perform_rtc_evaluation(query: str, model: str, config: RouterConfig) -> Tuple[bool, float, Dict]:
    """Perform Round-Trip Correctness evaluation."""
    response_1 = get_llm_response([{'role': 'user', 'content': query}], model, config)
    if not response_1:
        return (False, 0.0, {'error': 'Failed to get initial response'})
    inverse_prompt = f'Given this query and response pair, generate a new query that would lead to a similar response. Focus on the key aspects that would generate equivalent content:\n\nOriginal Query: {query}\nResponse: {response_1}\n\nGenerate a new query that would elicit a similar response:'
    alternate_query = get_llm_response([{'role': 'user', 'content': inverse_prompt}], model, config)
    if not alternate_query:
        return (False, 0.0, {'error': 'Failed to generate alternate query'})
    response_2 = get_llm_response([{'role': 'user', 'content': alternate_query}], model, config)
    if not response_2:
        return (False, 0.0, {'error': 'Failed to get second response'})
    similarity_score = compute_similarity(response_1, response_2)
    evaluation_details = {'original_query': query, 'response_1': response_1, 'alternate_query': alternate_query, 'response_2': response_2, 'similarity_score': similarity_score}
    return (similarity_score >= config.similarity_threshold, similarity_score, evaluation_details)

