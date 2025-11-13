# Cluster 18

class EvaluationTask(Task):

    def __init__(self, description, assistant, iterate, evaluate, groundtruth, expected_assistant, eval_function, expected_plan):
        super().__init__(description=description, assistant=assistant, iterate=iterate, evaluate=evaluate)
        self.groundtruth = groundtruth
        self.expected_assistant = expected_assistant
        self.expected_plan = expected_plan
        self.eval_function = eval_function

def __init__(self, description, assistant, iterate, evaluate, groundtruth, expected_assistant, eval_function, expected_plan):
    super().__init__(description=description, assistant=assistant, iterate=iterate, evaluate=evaluate)
    self.groundtruth = groundtruth
    self.expected_assistant = expected_assistant
    self.expected_plan = expected_plan
    self.eval_function = eval_function

