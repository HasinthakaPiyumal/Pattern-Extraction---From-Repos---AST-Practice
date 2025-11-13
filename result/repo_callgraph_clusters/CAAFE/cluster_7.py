# Cluster 7

def format_for_display(code):
    code = code.replace('```python', '').replace('```', '').replace('<end>', '')
    return code

def generate_code(messages):
    if model == 'skip':
        return ''
    client = openai.OpenAI()
    completion = client.chat.completions.create(model=model, messages=messages, stop=['```end'], temperature=0.5, max_completion_tokens=500)
    completion = response.model_dump()
    code = completion['choices'][0]['message']['content']
    code = code.replace('```python', '').replace('```', '').replace('<end>', '')
    return code

