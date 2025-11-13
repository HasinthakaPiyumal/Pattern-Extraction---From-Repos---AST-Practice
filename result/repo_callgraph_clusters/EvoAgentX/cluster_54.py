# Cluster 54

class SEWOptimizer(Optimizer):
    graph: Union[SequentialWorkFlowGraph, ActionGraph] = Field(description='The workflow to optimize.')
    repr_scheme: str = Field(default='python', description='The scheme to represent the workflow.')
    optimize_mode: Literal['all', 'structure', 'prompt'] = Field(default='all', description='The mode to optimize the workflow.')
    order: Literal['zero-order', 'first-order'] = Field(default='zero-order', description='Whether to use zero-order (using hyper-mutation prompt) or first-order (using mutation prompt) optimization.')

    def init_module(self, **kwargs):
        self._snapshot: List[dict] = []
        self._prompt_breeder = SimplePromptBreeder(llm=self.llm)
        self._convergence_check_counter = 0
        self._best_score = float('-inf')
        if isinstance(self.graph, ActionGraph):
            if self.optimize_mode != 'prompt':
                raise ValueError(f'{type(self).__name__} only support prompt optimization when `graph` is an `ActionGraph`. The `optimize_mode` should be set to `prompt`, but got {self.optimize_mode}.')

    def optimize(self, dataset: Benchmark, **kwargs):
        if isinstance(self.graph, SequentialWorkFlowGraph):
            logger.info(f'Optimizing the {type(self.graph).__name__} workflow with {self.repr_scheme} representation.')
        elif isinstance(self.graph, ActionGraph):
            logger.info(f'Optimizing the {type(self.graph).__name__} graph ...')
        graph: Union[SequentialWorkFlowGraph, ActionGraph] = self.graph
        logger.info('Run initial evaluation on the original workflow ...')
        with suppress_logger_info():
            metrics = self.evaluate(dataset, eval_mode='dev', graph=graph)
        logger.info(f'Initial metrics: {metrics}')
        self.log_snapshot(graph=graph, metrics=metrics)
        for i in range(self.max_steps):
            try:
                graph = self.step()
                if (i + 1) % self.eval_every_n_steps == 0:
                    logger.info(f'Evaluate the workflow at step {i + 1} ...')
                    with suppress_logger_info():
                        metrics = self.evaluate(dataset, eval_mode='dev')
                    logger.info(f'Step {i + 1} metrics: {metrics}')
                    self.log_snapshot(graph=graph, metrics=metrics)
            except Exception as e:
                logger.warning(f'Error in step {i}: {e}. Skip this step.')
                continue
            if self.convergence_check():
                logger.info(f'Convergence check passed at step {i + 1}. Stop the optimization.')
                break
        if i == self.max_steps - 1:
            logger.info(f'Reach the maximum number of steps {self.max_steps}. Stop the optimization.')
        logger.info('Restore the best graph from the snapshot ...')
        self.restore_best_graph()

    def step(self, **kwargs) -> Union[SequentialWorkFlowGraph, ActionGraph]:
        """
        Take a step of optimization and return the optimized graph.
        """
        graph = self._select_graph_with_highest_score(return_metrics=False)
        if isinstance(graph, SequentialWorkFlowGraph):
            new_graph = self._workflow_graph_step(graph)
        elif isinstance(graph, ActionGraph):
            new_graph = self._action_graph_step(graph)
        else:
            raise ValueError(f'Invalid graph type: {type(graph)}. The graph should be an instance of `WorkFlowGraph` or `ActionGraph`.')
        return new_graph

    def evaluate(self, dataset: Benchmark, eval_mode: str='test', graph: Optional[Union[SequentialWorkFlowGraph, ActionGraph]]=None, indices: Optional[List[int]]=None, sample_k: Optional[int]=None, **kwargs) -> dict:
        """
        Evaluate the workflow. If `graph` is provided, use the provided graph for evaluation. Otherwise, use the graph in the optimizer. 
        
        Args:
            dataset (Benchmark): The dataset to evaluate the workflow on.
            eval_mode (str): The evaluation mode. Choices: ["test", "dev", "train"].
            graph (Union[WorkFlowGraph, ActionGraph], optional): The graph to evaluate. If not provided, use the graph in the optimizer.
            indices (List[int], optional): The indices of the data to evaluate the workflow on.
            sample_k (int, optional): The number of data to evaluate the workflow on. If provided, a random sample of size `sample_k` will be used.
        
        Returns:
            dict: The metrics of the workflow evaluation.
        """
        graph = graph if graph is not None else self.graph
        metrics_list = []
        for i in range(self.eval_rounds):
            eval_info = [f'[{type(graph).__name__}]', f'Evaluation round {i + 1}/{self.eval_rounds}', f'Mode: {eval_mode}']
            if indices is not None:
                eval_info.append(f'Indices: {len(indices)} samples')
            if sample_k is not None:
                eval_info.append(f'Sample size: {sample_k}')
            logger.info(' | '.join(eval_info))
            metrics = self.evaluator.evaluate(graph=graph, benchmark=dataset, eval_mode=eval_mode, indices=indices, sample_k=sample_k, **kwargs)
            metrics_list.append(metrics)
        avg_metrics = self.evaluator._calculate_average_score(metrics_list)
        return avg_metrics

    def log_snapshot(self, graph: Union[SequentialWorkFlowGraph, ActionGraph], metrics: dict):
        if isinstance(graph, SequentialWorkFlowGraph):
            graph_info = graph.get_graph_info()
        elif isinstance(graph, ActionGraph):
            graph_info = graph
        else:
            raise ValueError(f'Invalid graph type: {type(graph)}. The graph should be an instance of `SequentialWorkFlowGraph` or `ActionGraph`.')
        self._snapshot.append({'index': len(self._snapshot), 'graph': deepcopy(graph_info), 'metrics': metrics})

    def _select_graph_with_highest_score(self, return_metrics: bool=False) -> Union[SequentialWorkFlowGraph, ActionGraph]:
        if len(self._snapshot) == 0:
            return self.graph
        snapshot_scores = [np.mean(list(snapshot['metrics'].values())) for snapshot in self._snapshot]
        best_index = np.argmax(snapshot_scores)
        if isinstance(self.graph, SequentialWorkFlowGraph):
            graph = SequentialWorkFlowGraph.from_dict(self._snapshot[best_index]['graph'])
        elif isinstance(self.graph, ActionGraph):
            graph = self._snapshot[best_index]['graph']
        else:
            raise ValueError(f'Invalid graph type: {type(self.graph)}. The graph should be an instance of `SequentialWorkFlowGraph` or `ActionGraph`.')
        if return_metrics:
            return (graph, self._snapshot[best_index]['metrics'])
        return graph

    def restore_best_graph(self):
        best_graph, best_metrics = self._select_graph_with_highest_score(return_metrics=True)
        logger.info(f'Restore the best graph from snapshot with metrics {best_metrics} ...')
        self.graph = best_graph

    def _wfg_structure_optimization_step(self, graph: SequentialWorkFlowGraph) -> SequentialWorkFlowGraph:
        """
        optinize the structure of the workflow graph and return the optimized graph.
        Args:
            graph (SequentialWorkFlowGraph): The workflow graph to optimize.
        
        Returns:
            SequentialWorkFlowGraph: The optimized workflow graph.  
        """
        graph_scheme = SEWWorkFlowScheme(graph=graph)
        graph_repr = graph_scheme.convert_to_scheme(scheme=self.repr_scheme)
        if self.repr_scheme == 'python':
            output_format = "\n\nALWAYS wrap the refined workflow in ```python\n``` format and DON'T include any other text within the code block!"
        elif self.repr_scheme == 'yaml':
            output_format = "\n\nALWAYS wrap the refined workflow in ```yaml\n``` format and DON'T include any other text within the code block!"
        elif self.repr_scheme == 'code':
            output_format = "\n\nALWAYS wrap the refined workflow in ```code\n``` format and DON'T include any other text within the code block!"
        elif self.repr_scheme == 'core':
            output_format = "\n\nALWAYS wrap the refined workflow in ```core\n``` format and DON'T include any other text within the code block!"
        elif self.repr_scheme == 'bpmn':
            output_format = "\n\nALWAYS wrap the refined workflow in ```bpmn\n``` format and DON'T include any other text within the code block!"
        else:
            raise ValueError(f'Invalid representation scheme: {self.repr_scheme}. The scheme should be one of {VALID_SCHEMES}.')
        prompt = 'Task Description: ' + graph.goal + '\n\nWorkflow Steps: ' + graph_repr + output_format
        new_graph_repr = self._prompt_breeder.generate_prompt(task_description=graph.goal, prompt=prompt, order=self.order)
        new_graph = graph_scheme.parse_from_scheme(scheme=self.repr_scheme, repr=new_graph_repr)
        return new_graph

    def _wfg_prompt_optimization_step(self, graph: SequentialWorkFlowGraph) -> SequentialWorkFlowGraph:
        task_description = graph.goal
        graph_scheme = SEWWorkFlowScheme(graph=graph)
        graph_repr = graph_scheme.convert_to_scheme(scheme=self.repr_scheme)
        graph_info = graph.get_graph_info()
        for i, task in enumerate(graph_info['tasks']):
            original_prompt = task['prompt']
            optimization_prompt = 'Task Description: ' + task_description + '\n\nWorkflow Steps:\n' + graph_repr + f'\n\nINSTRUCTION for the {i + 1}-th task:\n"""\n' + original_prompt + '\n"""'
            optimization_prompt += f'\n\nGiven the above information, please refine the instruction for the {i + 1}-th task.\n'
            optimization_prompt += 'Note that you should always use bracket (e.g. `{input_name}`) to wrap the inputs of the tasks in your refined instruction.\\n'
            optimization_prompt += "Only output the refined instruction and DON'T include any other text!"
            new_prompt = self._prompt_breeder.generate_prompt(task_description=task_description, prompt=optimization_prompt, order=self.order)
            graph_info['tasks'][i]['prompt'] = new_prompt
        new_graph = SequentialWorkFlowGraph.from_dict(graph_info)
        return new_graph

    def _workflow_graph_step(self, graph: SequentialWorkFlowGraph) -> SequentialWorkFlowGraph:
        if self.optimize_mode == 'structure' or self.optimize_mode == 'all':
            graph = self._wfg_structure_optimization_step(graph)
        if self.optimize_mode == 'prompt' or self.optimize_mode == 'all':
            graph = self._wfg_prompt_optimization_step(graph)
        return graph

    def _action_graph_prompt_optimization_step(self, graph: ActionGraph) -> ActionGraph:
        task_description = graph.description
        graph_info = graph.get_graph_info()
        graph_steps = inspect.getsource(getattr(graph, 'execute'))
        for operator_name, operator_info in graph_info['operators'].items():
            original_prompt = operator_info['prompt']
            optimization_prompt = 'Task Description: ' + task_description + '\n\nWorkflow Steps:\n' + graph_steps + f'\n\nINSTRUCTION for the `{operator_name}` operator:\n"""\n' + original_prompt + '\n"""'
            optimization_prompt += '\n\nThe interface of the operator is as follows:\n' + operator_info['interface']
            optimization_prompt += f'\n\nGiven the above information, please refine the instruction for the `{operator_name}` operator.\n'
            optimization_prompt += 'Note that you should always use bracket (e.g. `{input_name}`) to wrap the inputs of the operator in your refined instruction, '
            optimization_prompt += "and the input names should be EXACTLY the same as those defined in the interface. DON'T use bracket to wrap output names."
            optimization_prompt += "\nOnly output the refined instruction and DON'T include any other text!"
            new_prompt = self._prompt_breeder.generate_prompt(task_description=task_description, prompt=optimization_prompt, order=self.order)
            new_prompt = new_prompt.replace('"', '').strip()
            graph_info['operators'][operator_name]['prompt'] = new_prompt
        new_graph = ActionGraph.from_dict(graph_info)
        return new_graph

    def _action_graph_step(self, graph: ActionGraph) -> ActionGraph:
        if self.optimize_mode == 'prompt':
            graph = self._action_graph_prompt_optimization_step(graph)
        else:
            raise ValueError(f'{type(self).__name__} only support prompt optimization when `self.graph` is an `ActionGraph` instance. The `optimize_mode` should be set to `prompt`, but got {self.optimize_mode}.')
        return graph

    def convergence_check(self, **kwargs) -> bool:
        if not self._snapshot:
            logger.warning('No snapshots available for convergence check')
            return False
        scores = [np.mean(list(snapshot['metrics'].values())) for snapshot in self._snapshot]
        current_score = scores[-1]
        if current_score > self._best_score:
            self._best_score = current_score
            self._convergence_check_counter = 0
        else:
            self._convergence_check_counter += 1
        if self._convergence_check_counter >= self.convergence_threshold:
            logger.info(f'Early stopping triggered: No improvement for {self.convergence_threshold} iterations')
            return True
        return False

    def save(self, path: str, ignore: List[str]=[]):
        """
        Save the (optimized) workflow graph to a file. 

        Args:
            path (str): The path to save the workflow graph.
            ignore (List[str]): The keys to ignore when saving the workflow graph.
        """
        self.graph.save_module(path, ignore=ignore)

def _workflow_graph_step(self, graph: SequentialWorkFlowGraph) -> SequentialWorkFlowGraph:
    if self.optimize_mode == 'structure' or self.optimize_mode == 'all':
        graph = self._wfg_structure_optimization_step(graph)
    if self.optimize_mode == 'prompt' or self.optimize_mode == 'all':
        graph = self._wfg_prompt_optimization_step(graph)
    return graph

