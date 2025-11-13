# Cluster 1

def tokenize_prompt(prompt: str):
    tokenized_prompt = processor([prompt])
    return replicate(tokenized_prompt)

