# Cluster 66

def evaluate_workflow_sequence(prediction: List[Any], ground_truth: List[Any]) -> float:
    """Evaluate F1 score for sequence workflow."""
    from .measures import f1_score
    return f1_score(prediction=prediction, ground_truth=ground_truth)

class WorfBench(Benchmark):
    """
    WorfBench evaluation class for assessing LLM agents on complex workflow generation tasks.
    Assumed data structure:
    {
        "id": str,
        "task": str,
        "context": list of dicts (e.g., [{"title": str, "content": list of str}]),
        "expected_output": str or dict (sequence or graph),
        "type": str,
        "level": str
    }
    """

    def __init__(self, path: str=None, mode: str='test', **kwargs):
        path = os.path.expanduser(path or '~/.worfbench/data')
        super().__init__(name=type(self).__name__, path=path, mode=mode, **kwargs)

    def _load_data_from_file(self, file_name: str) -> Dict:
        if file_name is None:
            return None
        file_path = os.path.join(self.path, file_name)
        if not os.path.exists(file_path):
            download_worfbench_data(dataset='worfbench', save_folder=self.path)
        if not os.path.exists(file_path):
            logger.error(f'File {file_path} still does not exist after download attempt!')
            return None
        logger.info(f'Loading WorfBench data from {file_path} ...')
        data = load_json(path=file_path, type='json')
        if data is None:
            logger.error(f'Failed to load data from {file_path}')
            return None
        return data

    def _load_data(self) -> None:
        if self.mode in ['train', 'dev']:
            self._train_data = self._load_data_from_file(file_name=WORFBENCH_FILES_MAP['train'])
            if self.mode == 'dev':
                if self._train_data:
                    random.seed(42)
                    keys = list(self._train_data.keys())
                    n_dev = len(self._train_data[keys[0]]) // 10 or 1
                    indices = list(range(len(self._train_data[keys[0]])))
                    random.shuffle(indices)
                    self._train_data = {k: [v[i] for i in indices[:n_dev]] for k, v in self._train_data.items()}
        if self.mode == 'test':
            self._test_data = self._load_data_from_file(file_name=WORFBENCH_FILES_MAP['test'])

    def _get_label(self, example: Dict) -> Any:
        return example.get('expected_output', '')

    def _get_id(self, example: Dict) -> Any:
        return example.get('id', '')

    def evaluate(self, prediction: Any, label: Any) -> Dict:
        if isinstance(prediction, list) and isinstance(label, list):
            f1 = evaluate_workflow_sequence(prediction, label)
        elif isinstance(prediction, dict) and isinstance(label, dict):
            f1 = evaluate_workflow_graph(prediction, label)
        else:
            f1 = f1_score(prediction=str(prediction), ground_truth=str(label))
        em = exact_match_score(prediction=prediction, ground_truth=label)
        acc = acc_score(prediction=prediction, ground_truths=[label])
        return {'em': em, 'f1': f1, 'acc': acc}

    async def async_evaluate(self, graph: Callable, example: Dict) -> float:
        task = example.get('task', '')
        context = '\n'.join((f'{ctx.get('title', '')}: {' '.join(ctx.get('content', []))}' for ctx in example.get('context', []) if isinstance(ctx, dict)))
        inputs = f'Task: {task}\nContext: {context}\nGenerate workflow:\nAnswer:'
        try:
            generated_workflow = await graph(inputs)
        except Exception as e:
            logger.error(f'Error generating workflow: {e}')
            generated_workflow = ''
        label = self._get_label(example)
        metrics = self.evaluate(prediction=generated_workflow, label=label)
        return metrics['f1']

def evaluate(self, prediction: Any, label: Any) -> Dict:
    if isinstance(prediction, list) and isinstance(label, list):
        f1 = evaluate_workflow_sequence(prediction, label)
    elif isinstance(prediction, dict) and isinstance(label, dict):
        f1 = evaluate_workflow_graph(prediction, label)
    else:
        f1 = f1_score(prediction=str(prediction), ground_truth=str(label))
    em = exact_match_score(prediction=prediction, ground_truth=label)
    acc = acc_score(prediction=prediction, ground_truths=[label])
    return {'em': em, 'f1': f1, 'acc': acc}

class BIGBenchHard(Benchmark):
    """
    Benchmark class for BIGBenchHard dataset evaluation.
    
    BIGBenchHard is a subset of 23 challenging tasks from the BIG-bench evaluation suite.
    Each task example has the following structure:
    {
        "input": str,    # The input question/problem
        "target": str    # The expected answer/output
    }
    
    The benchmark supports automatic data splitting for training/validation purposes
    and evaluates predictions using exact match scoring.
    """

    def __init__(self, task: str, path: str=None, mode: str='all', dev_sample_num: int=0, seed: int=10, **kwargs):
        """
        Initialize BIGBenchHard benchmark.
        
        Args:
            task: The specific BIGBenchHard task name
            path: Path to store the dataset. Defaults to ~/.evoagentx/data/bigbenchhard/{task}
            mode: Data loading mode. Defaults to "all"
            dev_sample_num: Number of samples to use for dev set. If 0, all data goes to test set
            seed: Random seed for reproducibility. Defaults to 10
            **kwargs: Additional parameters for customization
            
        Raises:
            ValueError: If task is not a valid BIGBenchHard task name
        """
        if task not in ALL_TASKS:
            raise ValueError(f"Unknown task '{task}'. Available tasks: {list(ALL_TASKS.keys())}")
        self.task = task
        self.file_name = ALL_TASKS[task]
        self.dev_sample_num = dev_sample_num
        self.seed = seed
        path = os.path.expanduser(path or f'~/.evoagentx/data/bigbenchhard/{task}')
        super().__init__(name=f'BIGBenchHard-{self.task}', path=path, mode=mode, **kwargs)

    def _load_data_from_file(self, file_name: str) -> Optional[List[dict]]:
        """
        Load data from a specific file.
        
        Args:
            file_name: Name of the file to load
            
        Returns:
            List of loaded examples or None if file doesn't exist
        """
        if file_name is None:
            return None
        file_path = os.path.join(self.path, file_name)
        if not os.path.exists(file_path):
            download_raw_bigbenchhard_data(task_name=self.task, save_folder=self.path)
        logger.info(f'Loading BIGBenchHard data from {file_path}...')
        data = load_json(path=file_path, type='json')
        return data.get('examples', [])

    def _load_data(self):
        """
        Load and split data according to mode and dev_sample_num settings.
        
        Data splitting logic:
        - If dev_sample_num > 0: randomly samples examples for dev set, rest go to test set
        - If dev_sample_num = 0: all data goes to test set for evaluation
        - No training data provided (BIGBenchHard is designed for few-shot evaluation)
        """
        task_data = self._load_data_from_file(file_name=self.file_name)
        if task_data is None:
            logger.warning(f'No data loaded for task {self.task}')
            self._train_data = []
            self._dev_data = []
            self._test_data = []
            return
        self._train_data = []
        if self.dev_sample_num > 0 and len(task_data) > self.dev_sample_num:
            logger.info(f'Sampling {self.dev_sample_num} examples for dev set, rest for test set.')
            if self.seed is not None:
                set_seed(self.seed)
            dev_subset = random.sample(task_data, self.dev_sample_num)
            self._dev_data = dev_subset
            self._test_data = [item for item in task_data if item not in dev_subset]
        elif self.dev_sample_num > 0:
            logger.warning(f'dev_sample_num ({self.dev_sample_num}) >= total data size ({len(task_data)}). Using all data for dev set, none for test set.')
            self._dev_data = task_data
            self._test_data = []
        else:
            logger.info('dev_sample_num is 0, using all data for test set.')
            self._dev_data = []
            self._test_data = task_data

    def get_input_keys(self) -> List[str]:
        """
        Return the input keys expected by the benchmark.
        
        Returns:
            List containing "input" as the key for the problem text
        """
        return ['input']

    def _get_label(self, example: Any) -> Any:
        """
        Extract the ground truth label from an example.
        
        Args:
            example: The benchmark example
            
        Returns:
            The target answer/label
        """
        return example['target']

    def _get_id(self, example: Any) -> Any:
        """
        Extract the unique identifier from an example.
        
        BIGBenchHard examples don't have explicit IDs, so we use input text as identifier.
        
        Args:
            example: The benchmark example
            
        Returns:
            The input text as a unique identifier
        """
        return example.get('input', None)

    def evaluate(self, prediction: Any, label: Any) -> dict:
        """
        Score a prediction against the ground truth label.
        
        Uses exact match scoring with task-specific handling for certain tasks.
        
        Args:
            prediction: The predicted answer
            label: The ground truth answer
            
        Returns:
            Dictionary containing the exact match score
        """
        if self.task == 'dyck_languages':
            em = prediction.replace(' ', '') == label.replace(' ', '')
            return {'em': em}
        else:
            em = exact_match_score(prediction=prediction, ground_truth=label)
            return {'em': em}

def evaluate(self, prediction: Any, label: Any) -> dict:
    """
        Score a prediction against the ground truth label.
        
        Uses exact match scoring with task-specific handling for certain tasks.
        
        Args:
            prediction: The predicted answer
            label: The ground truth answer
            
        Returns:
            Dictionary containing the exact match score
        """
    if self.task == 'dyck_languages':
        em = prediction.replace(' ', '') == label.replace(' ', '')
        return {'em': em}
    else:
        em = exact_match_score(prediction=prediction, ground_truth=label)
        return {'em': em}

class RealMMRAG(Benchmark):
    """REAL-MM-RAG FinReport benchmark for multimodal retrieval evaluation.
    
    This benchmark contains financial report pages with associated queries,
    designed to test multimodal retrieval capabilities on real-world documents.
    """

    def __init__(self, path: str=None, mode: str='test', **kwargs):
        path = os.path.expanduser(path or '~/.evoagentx/data/real_mm_rag')
        self.dataset_file = Path(path) / 'real_mm_rag_finreport.json'
        self.images_dir = Path(path) / 'images'
        super().__init__(name=type(self).__name__, path=path, mode=mode, **kwargs)

    def _load_data(self):
        """Load the dataset from JSON file."""
        if not self.dataset_file.exists():
            download_real_mm_rag_data(save_dir=self.path)
        try:
            with open(self.dataset_file, 'r') as f:
                self._test_data = json.load(f)
            logger.info(f'Loaded {len(self._test_data)} samples from REAL-MM-RAG dataset')
        except Exception as e:
            logger.error(f'Failed to load dataset: {str(e)}')
            raise

    def _get_label(self, example: Any) -> Any:
        return example['answer']

    def _get_id(self, example: Any) -> Any:
        return example['id']

    def evaluate(self, prediction: Any, label: Any) -> dict:
        em = exact_match_score(prediction=prediction, ground_truth=label)
        f1 = f1_score(prediction=prediction, ground_truth=label)
        acc = acc_score(prediction=prediction, ground_truths=[label])
        return {'f1': f1, 'em': em, 'acc': acc}

    @property
    def data(self) -> List[Dict[str, Any]]:
        """Get the raw dataset."""
        return self._test_data

    def get_sample(self, index: int) -> Dict[str, Any]:
        """Get a single sample by index.
        
        Args:
            index: Sample index
            
        Returns:
            Dict containing query, image_filename, answer, and rephrases
        """
        if index >= len(self._test_data):
            raise IndexError(f'Index {index} out of range for dataset size {len(self._test_data)}')
        sample = self._test_data[index]
        sample['image_path'] = str(self.images_dir / sample['image_filename'])
        return sample

    def get_samples(self, start: int=0, end: Optional[int]=None) -> List[Dict[str, Any]]:
        """Get a range of samples.
        
        Args:
            start: Start index (inclusive)
            end: End index (exclusive). If None, goes to end of dataset
            
        Returns:
            List of samples
        """
        end = end or len(self._test_data)
        samples = []
        for i in range(start, min(end, len(self._test_data))):
            samples.append(self.get_sample(i))
        return samples

    def get_random_samples(self, n: int, seed: int=42) -> List[Dict[str, Any]]:
        """Get n random samples from the dataset.
        
        Args:
            n: Number of samples to return
            seed: Random seed for reproducibility
            
        Returns:
            List of random samples
        """
        import random
        random.seed(seed)
        indices = random.sample(range(len(self._test_data)), min(n, len(self._test_data)))
        return [self.get_sample(i) for i in indices]

    def get_query_variations(self, sample: Dict[str, Any]) -> List[str]:
        """Get all query variations for a sample.
        
        Args:
            sample: A sample from the dataset
            
        Returns:
            List of query variations (original + 3 rephrase levels)
        """
        queries = [sample['query']]
        for level in ['rephrase_level_1', 'rephrase_level_2', 'rephrase_level_3']:
            if level in sample and sample[level]:
                queries.append(sample[level])
        return queries

    def get_stats(self) -> Dict[str, Any]:
        """Get dataset statistics.
        
        Returns:
            Dictionary with dataset statistics
        """
        total_samples = len(self._test_data)
        has_rephrase_1 = sum((1 for s in self._test_data if s.get('rephrase_level_1')))
        has_rephrase_2 = sum((1 for s in self._test_data if s.get('rephrase_level_2')))
        has_rephrase_3 = sum((1 for s in self._test_data if s.get('rephrase_level_3')))
        unique_images = set((s['image_filename'] for s in self._test_data))
        return {'total_samples': total_samples, 'unique_images': len(unique_images), 'samples_with_rephrase_1': has_rephrase_1, 'samples_with_rephrase_2': has_rephrase_2, 'samples_with_rephrase_3': has_rephrase_3, 'avg_queries_per_image': total_samples / len(unique_images)}

def evaluate(self, prediction: Any, label: Any) -> dict:
    em = exact_match_score(prediction=prediction, ground_truth=label)
    f1 = f1_score(prediction=prediction, ground_truth=label)
    acc = acc_score(prediction=prediction, ground_truths=[label])
    return {'f1': f1, 'em': em, 'acc': acc}

class HotPotQA(Benchmark):
    """Benchmark class for evaluating multi-hop question answering on HotPotQA dataset.
    
    Each HotPotQA example has the following structure:
    {
        "_id": str, 
        "question": str, 
        "answer": str, 
        "context": [["context_title", ["context_sentence", "another_sentence"]]],
        "supporting_facts": [["supporting_title", supporting_sentence_index]],
        "type": str,
        "level": str
    }
    
    The benchmark evaluates answers using exact match, F1 score, and accuracy metrics.
    """

    def __init__(self, path: str=None, mode: str='all', **kwargs):
        path = os.path.expanduser(path or '~/.evoagentx/data/hotpotqa')
        super().__init__(name=type(self).__name__, path=path, mode=mode, **kwargs)

    def _load_data_from_file(self, file_name: str):
        if file_name is None:
            return None
        file_path = os.path.join(self.path, file_name)
        if not os.path.exists(file_path):
            download_raw_hotpotqa_data(name=file_name, save_folder=self.path)
        logger.info(f'loading HotPotQA data from {file_path} ...')
        return load_json(path=file_path, type='json')

    def _load_data(self):
        if self.mode == 'train' or self.mode == 'all':
            self._train_data = self._load_data_from_file(file_name=HOTPOTQA_FILES_MAP['train'])
        if self.mode == 'dev' or self.mode == 'all':
            self._dev_data = self._load_data_from_file(file_name=HOTPOTQA_FILES_MAP['dev'])
        if self.mode == 'test' or self.mode == 'all':
            self._test_data = self._load_data_from_file(file_name=HOTPOTQA_FILES_MAP['test'])

    def _get_label(self, example: Any) -> Any:
        return example['answer']

    def _get_id(self, example: Any) -> Any:
        return example['_id']

    def evaluate(self, prediction: Any, label: Any) -> dict:
        em = exact_match_score(prediction=prediction, ground_truth=label)
        f1 = f1_score(prediction=prediction, ground_truth=label)
        acc = acc_score(prediction=prediction, ground_truths=[label])
        return {'f1': f1, 'em': em, 'acc': acc}

def evaluate(self, prediction: Any, label: Any) -> dict:
    em = exact_match_score(prediction=prediction, ground_truth=label)
    f1 = f1_score(prediction=prediction, ground_truth=label)
    acc = acc_score(prediction=prediction, ground_truths=[label])
    return {'f1': f1, 'em': em, 'acc': acc}

class NQ(Benchmark):
    """Benchmark class for evaluating question answering on Natural Questions dataset.
    
    Natural Questions (NQ) is a dataset for open-domain question answering,
    containing real questions from Google Search and answers from Wikipedia.
    This class handles loading the dataset, evaluating answers, and computing
    metrics like exact match and F1 score.
    
    Each NQ example has the following structure:
    {
        "id": str, 
        "question": str, 
        "answers": List[str]
    }
    
    The benchmark evaluates answers using exact match, F1 score, and accuracy metrics.
    """

    def __init__(self, path: str=None, mode: str='all', **kwargs):
        path = os.path.expanduser(path or '~/.evoagentx/data/nq')
        super().__init__(name=type(self).__name__, path=path, mode=mode, **kwargs)

    def _load_data_from_file(self, file_name: str):
        if file_name is None:
            return None
        file_path = os.path.join(self.path, file_name)
        if not os.path.exists(file_path):
            download_raw_nq_data(name=file_name, save_folder=self.path)
        logger.info(f'loading NQ data from {file_path} ...')
        return load_tsv_data(file_path=file_path)

    def _load_data(self):
        if self.mode == 'train' or self.mode == 'all':
            self._train_data = self._load_data_from_file(file_name=NQ_FILES_MAP['train'])
        if self.mode == 'dev' or self.mode == 'all':
            self._dev_data = self._load_data_from_file(file_name=NQ_FILES_MAP['dev'])
        if self.mode == 'test' or self.mode == 'all':
            self._test_data = self._load_data_from_file(file_name=NQ_FILES_MAP['test'])

    def _get_label(self, example: Any) -> Any:
        return example['answers']

    def _get_id(self, example: Any) -> Any:
        return example['id']

    def evaluate(self, prediction: Any, label: Any) -> dict:
        em = ems(prediction=prediction, ground_truths=label)
        f1 = max((f1_score(prediction=prediction, ground_truth=one_answer) for one_answer in label))
        acc = acc_score(prediction=prediction, ground_truths=label)
        return {'f1': f1, 'em': em, 'acc': acc}

def evaluate(self, prediction: Any, label: Any) -> dict:
    em = ems(prediction=prediction, ground_truths=label)
    f1 = max((f1_score(prediction=prediction, ground_truth=one_answer) for one_answer in label))
    acc = acc_score(prediction=prediction, ground_truths=label)
    return {'f1': f1, 'em': em, 'acc': acc}

def ems(prediction: str, ground_truths: List[str]) -> float:
    assert isinstance(ground_truths, list), f'ground_truths must be a list, but got {type(ground_truths)}'
    return max([exact_match_score(prediction, gt) for gt in ground_truths])

class MessageBenchmark(Benchmark):
    """
    Adapt dataset in messages format, automatically extract last user/assistant round.
    """

    def __init__(self, path: str, mode: str='train'):
        super().__init__(name='MessageBenchmark', path=path, mode=mode)

    def _load_data(self):
        import json
        file_path = os.path.join(self.path, 'worfbench_train.json')
        with open(file_path, 'r', encoding='utf-8') as f:
            self._train_data = json.load(f)

    def _get_label(self, example):
        return [m['content'] for m in example['messages'] if m['role'] == 'assistant'][-1]

    def _get_id(self, example):
        user_msg = [m['content'] for m in example['messages'] if m['role'] == 'user'][-1]
        return example.get('source', '') + '_' + user_msg[:20]

    def evaluate(self, prediction, label):
        from evoagentx.benchmark.measures import exact_match_score, f1_score, acc_score
        em = exact_match_score(prediction, label)
        f1 = f1_score(prediction, label)
        acc = acc_score(prediction, [label])
        return {'em': em, 'f1': f1, 'acc': acc}

def evaluate(self, prediction, label):
    from evoagentx.benchmark.measures import exact_match_score, f1_score, acc_score
    em = exact_match_score(prediction, label)
    f1 = f1_score(prediction, label)
    acc = acc_score(prediction, [label])
    return {'em': em, 'f1': f1, 'acc': acc}

def f1_chain(prediction: str, label: str) -> float:
    from evoagentx.benchmark.measures import f1_score
    return f1_score(prediction, label)

