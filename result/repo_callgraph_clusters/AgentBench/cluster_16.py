# Cluster 16

class TaskHandler:

    def match(self, task_name) -> bool:
        raise NotImplementedError()

    def get_main_metric(self, overall_result):
        raise NotImplementedError()

    def get_order_priority(self):
        return 100000

    @staticmethod
    def get_handler(task_name) -> 'TaskHandler':
        handlers = [DCG(), HH(), OS(), DB(), KG(), LTP(), WB(), WS()]
        for handler in handlers:
            if handler.match(task_name):
                return handler
        raise ValueError(f'Unknown task: {task_name}')

def match(self, task_name) -> bool:
    raise NotImplementedError()

def get_main_metric(self, overall_result):
    raise NotImplementedError()

class RuleBase:

    def check(self, obj) -> bool:
        raise NotImplementedError()

def check(self, obj) -> bool:
    raise NotImplementedError()

class AgentClient:

    def __init__(self, *args, **kwargs):
        pass

    def inference(self, history: List[dict]) -> str:
        raise NotImplementedError()

def inference(self, history: List[dict]) -> str:
    raise NotImplementedError()

