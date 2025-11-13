# Cluster 28

class AdvancedSelfConsistency:

    def __init__(self, client, model: str, num_samples: int=5, similarity_threshold: float=0.8, request_id: str=None):
        self.client = client
        self.model = model
        self.num_samples = num_samples
        self.similarity_threshold = similarity_threshold
        self.self_consistency_completion_tokens = 0
        self.request_id = request_id

    def generate_responses(self, system_prompt: str, user_prompt: str) -> List[str]:
        responses = []
        for _ in range(self.num_samples):
            provider_request = {'model': self.model, 'messages': [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_prompt}], 'temperature': 1, 'max_tokens': 4096}
            response = self.client.chat.completions.create(**provider_request)
            if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and self.request_id:
                response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
                optillm.conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
            self.self_consistency_completion_tokens += response.usage.completion_tokens
            responses.append(response.choices[0].message.content)
        return responses

    def calculate_similarity(self, a: str, b: str) -> float:
        return SequenceMatcher(None, a, b).ratio()

    def cluster_similar_responses(self, responses: List[str]) -> List[List[str]]:
        clusters = []
        for response in responses:
            added_to_cluster = False
            for cluster in clusters:
                if self.calculate_similarity(response, cluster[0]) >= self.similarity_threshold:
                    cluster.append(response)
                    added_to_cluster = True
                    break
            if not added_to_cluster:
                clusters.append([response])
        return clusters

    def aggregate_results(self, responses: List[str]) -> Dict[str, any]:
        final_answers = responses
        clusters = self.cluster_similar_responses(final_answers)
        cluster_info = []
        for cluster in clusters:
            cluster_info.append({'answer': cluster[0], 'frequency': len(cluster), 'variants': cluster})
        cluster_info.sort(key=lambda x: x['frequency'], reverse=True)
        return {'clusters': cluster_info, 'total_responses': len(responses), 'num_unique_clusters': len(clusters)}

    def evaluate(self, system_prompt: str, user_prompt: str) -> Dict[str, any]:
        responses = self.generate_responses(system_prompt, user_prompt)
        aggregated_result = self.aggregate_results(responses)
        return {'individual_responses': responses, 'aggregated_result': aggregated_result}

def evaluate(self, system_prompt: str, user_prompt: str) -> Dict[str, any]:
    responses = self.generate_responses(system_prompt, user_prompt)
    aggregated_result = self.aggregate_results(responses)
    return {'individual_responses': responses, 'aggregated_result': aggregated_result}

