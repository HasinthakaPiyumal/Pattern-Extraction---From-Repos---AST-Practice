# Cluster 53

class Workflow:

    def __init__(self):
        self.system_prompt = 'You are a helpful assistant.'
        self.few_shot = 'Q: 1+1=?\nA: 2'
        self.sampler = Sampler()

    def execute(self):
        pass

    def run(self):
        prompt = f'{self.system_prompt}\n{self.few_shot}\nUser: Hi'
        return {'prompt': prompt, 'score': random.uniform(0, 1)}

def __init__(self):
    self.system_prompt = 'You are a helpful assistant.'
    self.few_shot = 'Q: 1+1=?\nA: 2'
    self.sampler = Sampler()

