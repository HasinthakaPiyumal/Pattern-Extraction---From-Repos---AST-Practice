# Cluster 2

def llama_api(prompt):
    payload = json.dumps({'input': {'prompt': prompt, 'max_new_tokens': 4500, 'temperature': 0.9, 'top_k': 50, 'top_p': 0.7, 'repetition_penalty': 1.2, 'batch_size': 8, 'stop': ['</s>']}})
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {RUNPOD_API_KEY}'}
    response = requests.request('POST', url, headers=headers, data=payload)
    response_t = json.loads(response.text)
    return response_t['output']

def save_chat(chat_history: list[Any, Any]) -> None:
    f = open('chat_history.json', 'w+')
    f.write(json.dumps(chat_history))
    f.close

