# Cluster 43

class ExchangeExecutor(AbstractExecutor):

    def __init__(self, db: EvaDBDatabase, node: ExchangePlan):
        self.inner_plan = node.inner_plan
        self.parallelism = node.parallelism
        self.ray_pull_env_conf_dict = node.ray_pull_env_conf_dict
        self.ray_parallel_env_conf_dict = node.ray_parallel_env_conf_dict
        super().__init__(db, node)

    def build_inner_executor(self, inner_executor):
        self.inner_executor = inner_executor
        self.inner_executor.children = [QueueReaderExecutor()]

    def exec(self) -> Iterator[Batch]:
        from ray.util.queue import Queue
        input_queue = Queue(maxsize=100)
        output_queue = Queue(maxsize=100)
        assert len(self.children) == 1, 'Exchange currently only supports parallelization of node with only one child'
        ray_pull_task = ray_pull().remote(self.ray_pull_env_conf_dict, self.children[0], input_queue)
        ray_parallel_task_list = []
        for i in range(self.parallelism):
            ray_parallel_task_list.append(ray_parallel().remote(self.ray_parallel_env_conf_dict[i], self.inner_executor, input_queue, output_queue))
        ray_wait_and_alert().remote([ray_pull_task], input_queue)
        ray_wait_and_alert().remote(ray_parallel_task_list, output_queue)
        while True:
            res = output_queue.get(block=True)
            if res is StageCompleteSignal:
                break
            elif isinstance(res, ExecutorError):
                raise res
            else:
                yield res

def build_inner_executor(self, inner_executor):
    self.inner_executor = inner_executor
    self.inner_executor.children = [QueueReaderExecutor()]

