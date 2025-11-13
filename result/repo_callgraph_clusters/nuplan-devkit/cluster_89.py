# Cluster 89

class LogSplitter(AbstractSplitter):
    """
    Splitter that splits database to lists of samples for each of train/val/test sets based on log name.
    """

    def __init__(self, log_splits: Dict[str, List[str]]) -> None:
        """
        Initializes the class.

        :param log_splits: dictionary containing 'train', 'val', 'test' keys mapped to lists of log names
        """
        self.train_logs = set(log_splits['train'])
        self.val_logs = set(log_splits['val'])
        self.test_logs = set(log_splits['test'])

    def get_train_samples(self, scenarios: List[AbstractScenario], worker: WorkerPool) -> List[AbstractScenario]:
        """Inherited, see superclass."""
        return _filter_abstract_scenario_by_log_name(scenarios, self.train_logs, worker)

    def get_val_samples(self, scenarios: List[AbstractScenario], worker: WorkerPool) -> List[AbstractScenario]:
        """Inherited, see superclass."""
        return _filter_abstract_scenario_by_log_name(scenarios, self.val_logs, worker)

    def get_test_samples(self, scenarios: List[AbstractScenario], worker: WorkerPool) -> List[AbstractScenario]:
        """Inherited, see superclass."""
        return _filter_abstract_scenario_by_log_name(scenarios, self.test_logs, worker)

def get_train_samples(self, scenarios: List[AbstractScenario], worker: WorkerPool) -> List[AbstractScenario]:
    """Inherited, see superclass."""
    return _filter_abstract_scenario_by_log_name(scenarios, self.train_logs, worker)

def get_val_samples(self, scenarios: List[AbstractScenario], worker: WorkerPool) -> List[AbstractScenario]:
    """Inherited, see superclass."""
    return _filter_abstract_scenario_by_log_name(scenarios, self.val_logs, worker)

def get_test_samples(self, scenarios: List[AbstractScenario], worker: WorkerPool) -> List[AbstractScenario]:
    """Inherited, see superclass."""
    return _filter_abstract_scenario_by_log_name(scenarios, self.test_logs, worker)

