# Cluster 68

class RayDistributed(WorkerPool):
    """
    This worker uses ray to distribute work across all available threads.
    """

    def __init__(self, master_node_ip: Optional[str]=None, threads_per_node: Optional[int]=None, debug_mode: bool=False, log_to_driver: bool=True, output_dir: Optional[Union[str, Path]]=None, logs_subdir: Optional[str]='logs', use_distributed: bool=False):
        """
        Initialize ray worker.
        :param master_node_ip: if available, ray will connect to remote cluster.
        :param threads_per_node: Number of threads to use per node.
        :param debug_mode: If true, the code will be executed serially. This
            is useful for debugging.
        :param log_to_driver: If true, the output from all of the worker
                processes on all nodes will be directed to the driver.
        :param output_dir: Experiment output directory.
        :param logs_subdir: Subdirectory inside experiment dir to store worker logs.
        :param use_distributed: Boolean flag to explicitly enable/disable distributed computation
        """
        self._master_node_ip = master_node_ip
        self._threads_per_node = threads_per_node
        self._local_mode = debug_mode
        self._log_to_driver = log_to_driver
        self._log_dir: Optional[Path] = Path(output_dir) / (logs_subdir or '') if output_dir is not None else None
        self._use_distributed = use_distributed
        super().__init__(self.initialize())

    def initialize(self) -> WorkerResources:
        """
        Initialize ray.
        :return: created WorkerResources.
        """
        if ray.is_initialized():
            logger.warning('Ray is running, we will shut it down before starting again!')
            ray.shutdown()
        return initialize_ray(master_node_ip=self._master_node_ip, threads_per_node=self._threads_per_node, local_mode=self._local_mode, log_to_driver=self._log_to_driver, use_distributed=self._use_distributed)

    def shutdown(self) -> None:
        """
        Shutdown the worker and clear memory.
        """
        ray.shutdown()

    def _map(self, task: Task, *item_lists: Iterable[List[Any]], verbose: bool=False) -> List[Any]:
        """Inherited, see superclass."""
        del verbose
        return ray_map(task, *item_lists, log_dir=self._log_dir)

    def submit(self, task: Task, *args: Any, **kwargs: Any) -> Future[Any]:
        """Inherited, see superclass."""
        remote_fn = ray.remote(task.fn).options(num_gpus=task.num_gpus, num_cpus=task.num_cpus)
        object_ids: ray._raylet.ObjectRef = remote_fn.remote(*args, **kwargs)
        return object_ids.future()

def _map(self, task: Task, *item_lists: Iterable[List[Any]], verbose: bool=False) -> List[Any]:
    """Inherited, see superclass."""
    del verbose
    return ray_map(task, *item_lists, log_dir=self._log_dir)

