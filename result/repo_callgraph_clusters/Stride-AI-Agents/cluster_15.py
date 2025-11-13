# Cluster 15

def evaluate_with_llm_bool(instruction, data) -> BoolEvalResult:
    eval_result, _ = __client.chat.completions.create_with_completion(model='gpt-4o', messages=[{'role': 'system', 'content': instruction}, {'role': 'user', 'content': data}], response_model=BoolEvalResult)
    return eval_result

