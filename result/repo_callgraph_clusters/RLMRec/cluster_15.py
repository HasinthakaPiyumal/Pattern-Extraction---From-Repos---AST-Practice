# Cluster 15

def get_gpt_response_w_system(prompt):
    global system_prompt
    completion = openai.ChatCompletion.create(model='gpt-3.5-turbo', messages=[{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': prompt}])
    response = completion.choices[0].message.content
    return response

def get_gpt_emb(prompt):
    embedding = openai.Embedding.create(input=prompt, model='text-embedding-ada-002')['data'][0]['embedding']
    return np.array(embedding)

def get_gpt_response_w_system(prompt):
    global system_prompt
    completion = openai.ChatCompletion.create(model='gpt-3.5-turbo', messages=[{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': prompt}])
    response = completion.choices[0].message.content
    return response

