# Cluster 41

class StrategyDatabase:
    """Manages a collection of problem-solving strategies."""

    def __init__(self, db_path: str=STRATEGY_DB_PATH, metrics_path: str=STRATEGY_METRICS_PATH):
        self.db_path = db_path
        self.metrics_path = metrics_path
        self.strategies: List[Strategy] = []
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.vectors = None
        self.metrics = {'total_queries': 0, 'strategy_applications': 0, 'strategies_created': 0, 'strategies_refined': 0, 'successful_resolutions': 0, 'last_strategy_id': 0, 'reasoning_examples_collected': 0, 'strategies_merged': 0}
        self._load()

    def _load(self) -> None:
        """Load strategies and metrics from disk."""
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r') as f:
                    data = json.load(f)
                    self.strategies = [Strategy.from_dict(s) for s in data]
                    for strategy in self.strategies:
                        if strategy.strategy_id.startswith('strategy_'):
                            try:
                                strategy_num = int(strategy.strategy_id.split('_')[1])
                                self.metrics['last_strategy_id'] = max(self.metrics['last_strategy_id'], strategy_num)
                            except ValueError:
                                pass
                logger.info(f'Loaded {len(self.strategies)} strategies from {self.db_path}')
                logger.info(f'Last strategy ID is {self.metrics['last_strategy_id']}')
            except Exception as e:
                logger.error(f'Error loading strategies: {str(e)}')
                self.strategies = []
        if os.path.exists(self.metrics_path):
            try:
                with open(self.metrics_path, 'r') as f:
                    metrics = json.load(f)
                    last_id = self.metrics['last_strategy_id']
                    self.metrics.update(metrics)
                    if 'last_strategy_id' in metrics:
                        self.metrics['last_strategy_id'] = max(last_id, metrics['last_strategy_id'])
                logger.info(f'Loaded metrics from {self.metrics_path}')
                logger.info(f'Last strategy ID is {self.metrics['last_strategy_id']}')
            except Exception as e:
                logger.error(f'Error loading metrics: {str(e)}')

    def _save(self) -> None:
        """Save strategies and metrics to disk."""
        try:
            with open(self.db_path, 'w') as f:
                json.dump([s.to_dict() for s in self.strategies], f, indent=2)
            logger.info(f'Saved {len(self.strategies)} strategies to {self.db_path}')
        except Exception as e:
            logger.error(f'Error saving strategies: {str(e)}')
        try:
            with open(self.metrics_path, 'w') as f:
                json.dump(self.metrics, f, indent=2)
            logger.info(f'Saved metrics to {self.metrics_path}')
        except Exception as e:
            logger.error(f'Error saving metrics: {str(e)}')

    def add_strategy(self, strategy: Strategy) -> None:
        """Add a new strategy to the database."""
        if strategy.strategy_id.startswith('strategy_'):
            try:
                strategy_num = int(strategy.strategy_id.split('_')[1])
                self.metrics['last_strategy_id'] = max(self.metrics['last_strategy_id'], strategy_num)
            except ValueError:
                pass
        exists = any((s.problem_type == strategy.problem_type for s in self.strategies))
        self.strategies.append(strategy)
        self.vectors = None
        self.metrics['strategies_created'] += 1
        self._save()
        if not exists:
            logger.info(f'Added first strategy for problem type: {strategy.problem_type}')
        else:
            logger.info(f'Added additional strategy for problem type: {strategy.problem_type}')

    def get_strategies_for_problem(self, problem_type: str) -> List[Strategy]:
        """Get all strategies for a specific problem type."""
        return [s for s in self.strategies if s.problem_type == problem_type]

    def get_strategy_by_id(self, strategy_id: str) -> Optional[Strategy]:
        """Get a strategy by its ID."""
        for strategy in self.strategies:
            if strategy.strategy_id == strategy_id:
                return strategy
        return None

    def update_strategy_performance(self, strategy_id: str, success: bool) -> None:
        """Update the performance metrics for a strategy."""
        strategy = self.get_strategy_by_id(strategy_id)
        if strategy:
            strategy.record_attempt(success)
            self.metrics['strategy_applications'] += 1
            if success:
                self.metrics['successful_resolutions'] += 1
            self._save()

    def refine_strategy(self, strategy_id: str, refined_text: str) -> None:
        """Refine a strategy based on new insights."""
        strategy = self.get_strategy_by_id(strategy_id)
        if strategy:
            strategy.update_strategy(refined_text)
            self.metrics['strategies_refined'] += 1
            self._save()

    def add_reasoning_example(self, strategy_id: str, reasoning: str) -> None:
        """Add a reasoning example to a strategy."""
        strategy = self.get_strategy_by_id(strategy_id)
        if strategy and reasoning:
            strategy.add_reasoning_example(reasoning)
            self.metrics['reasoning_examples_collected'] += 1
            self._save()

    def add_example_to_strategy(self, strategy_id: str, example: str) -> None:
        """Add an example to a strategy."""
        strategy = self.get_strategy_by_id(strategy_id)
        if strategy and example:
            strategy.add_example(example)
            self._save()

    def get_similar_strategies(self, query: str, n: int=5) -> List[Tuple[Strategy, float]]:
        """Find strategies similar to a query using TF-IDF similarity."""
        if not self.strategies:
            return []
        strategy_texts = [s.strategy_text for s in self.strategies]
        if self.vectors is None or len(self.vectors.shape) == 0 or self.vectors.shape[0] != len(strategy_texts):
            try:
                self.vectors = self.vectorizer.fit_transform(strategy_texts)
            except Exception as e:
                logger.error(f'Error creating strategy vectors: {str(e)}')
                return []
        try:
            query_vector = self.vectorizer.transform([query])
            similarities = cosine_similarity(query_vector, self.vectors).flatten()
            sorted_indices = similarities.argsort()[::-1]
            return [(self.strategies[i], float(similarities[i])) for i in sorted_indices[:n]]
        except Exception as e:
            logger.error(f'Error finding similar strategies: {str(e)}')
            return []

    def find_similar_strategy(self, problem_type: str, query: str, threshold: float=STRATEGY_CREATION_THRESHOLD) -> Optional[Tuple[Strategy, float]]:
        """
        Find a strategy of the same problem type that is similar to the query.
        
        Args:
            problem_type: The problem type to match
            query: The query to find similarity against
            threshold: The similarity threshold to consider a match
            
        Returns:
            Optional[Tuple[Strategy, float]]: The most similar strategy and its similarity score,
                                             or None if no similar strategy is found
        """
        if not self.strategies:
            return None
        type_strategies = [s for s in self.strategies if s.problem_type == problem_type]
        if not type_strategies:
            return None
        try:
            strategy_texts = [s.strategy_text for s in type_strategies]
            vectorizer = TfidfVectorizer(stop_words='english')
            vectors = vectorizer.fit_transform(strategy_texts + [query])
            query_vector = vectors[-1]
            strategy_vectors = vectors[:-1]
            similarities = cosine_similarity(query_vector, strategy_vectors).flatten()
            if len(similarities) > 0:
                max_idx = similarities.argmax()
                max_similarity = similarities[max_idx]
                if max_similarity >= threshold:
                    return (type_strategies[max_idx], float(max_similarity))
        except Exception as e:
            logger.error(f'Error finding similar strategy: {str(e)}')
        return None

    def find_similar_examples(self, problem_type: str, query: str, threshold: float=STRATEGY_CREATION_THRESHOLD) -> Optional[Tuple[Strategy, float]]:
        """
        Find a strategy of the same problem type with examples similar to the query.
        
        Args:
            problem_type: The problem type to match
            query: The query to find similarity against
            threshold: The similarity threshold to consider a match
            
        Returns:
            Optional[Tuple[Strategy, float]]: The strategy with the most similar examples and the similarity score,
                                             or None if no similar strategy is found
        """
        if not self.strategies:
            return None
        type_strategies = [s for s in self.strategies if s.problem_type == problem_type]
        if not type_strategies:
            return None
        max_similarity = 0.0
        most_similar_strategy = None
        try:
            for strategy in type_strategies:
                if not strategy.examples:
                    continue
                vectorizer = TfidfVectorizer(stop_words='english')
                vectors = vectorizer.fit_transform(strategy.examples + [query])
                query_vector = vectors[-1]
                example_vectors = vectors[:-1]
                similarities = cosine_similarity(query_vector, example_vectors).flatten()
                if len(similarities) > 0:
                    strategy_max_similarity = similarities.max()
                    if strategy_max_similarity > max_similarity:
                        max_similarity = strategy_max_similarity
                        most_similar_strategy = strategy
            if most_similar_strategy and max_similarity >= threshold:
                return (most_similar_strategy, float(max_similarity))
        except Exception as e:
            logger.error(f'Error finding similar examples: {str(e)}')
        return None

    def get_next_strategy_id(self) -> str:
        """Generate a unique ID for a new strategy."""
        self.metrics['last_strategy_id'] += 1
        new_id = f'strategy_{self.metrics['last_strategy_id']}'
        logger.info(f'Generated new strategy ID: {new_id}')
        return new_id

    def increment_query_count(self) -> None:
        """Increment the total query count."""
        self.metrics['total_queries'] += 1
        self._save()

    def get_metrics(self) -> Dict[str, Any]:
        """Get the current metrics."""
        return self.metrics.copy()

    def prune_strategies(self, min_success_rate: float=0.3, min_attempts: int=5) -> int:
        """Prune strategies with poor performance."""
        initial_count = len(self.strategies)
        self.strategies = [s for s in self.strategies if s.total_attempts < min_attempts or s.success_rate >= min_success_rate]
        pruned_count = initial_count - len(self.strategies)
        if pruned_count > 0:
            self.vectors = None
            self._save()
        return pruned_count

    def merge_similar_strategies(self, similarity_threshold: float=STRATEGY_MERGING_THRESHOLD) -> int:
        """Merge strategies that are very similar to each other."""
        if len(self.strategies) <= 1:
            return 0
        merged_count = 0
        i = 0
        while i < len(self.strategies):
            j = i + 1
            while j < len(self.strategies):
                if self.strategies[i].problem_type == self.strategies[j].problem_type:
                    text_i = self.strategies[i].strategy_text
                    text_j = self.strategies[j].strategy_text
                    vectorizer = TfidfVectorizer(stop_words='english')
                    vectors = vectorizer.fit_transform([text_i, text_j])
                    similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
                    if similarity >= similarity_threshold:
                        merged_strategy = self._merge_two_strategies(self.strategies[i], self.strategies[j])
                        self.strategies[i] = merged_strategy
                        self.strategies.pop(j)
                        merged_count += 1
                        self.metrics['strategies_merged'] += 1
                        logger.info(f'Merged strategies {self.strategies[i].strategy_id} and {merged_strategy.strategy_id} with similarity {similarity:.2f}')
                    else:
                        j += 1
                else:
                    j += 1
            i += 1
        if merged_count > 0:
            self.vectors = None
            self._save()
        return merged_count

    def _merge_two_strategies(self, strategy1: Strategy, strategy2: Strategy) -> Strategy:
        """Merge two similar strategies into one."""
        if strategy1.success_rate >= strategy2.success_rate:
            base, other = (strategy1, strategy2)
        else:
            base, other = (strategy2, strategy1)
        merged = Strategy(strategy_id=base.strategy_id, problem_type=base.problem_type, strategy_text=base.strategy_text, examples=list(set(base.examples + other.examples)), success_count=base.success_count + other.success_count, total_attempts=base.total_attempts + other.total_attempts, created_at=min(base.created_at, other.created_at) if base.created_at and other.created_at else base.created_at, last_used=max(base.last_used, other.last_used) if base.last_used and other.last_used else base.last_used, last_updated=datetime.now().isoformat(), confidence=(base.confidence + other.confidence) / 2, tags=list(set(base.tags + other.tags)), reasoning_examples=base.reasoning_examples + other.reasoning_examples)
        if len(merged.reasoning_examples) > 5:
            merged.reasoning_examples = merged.reasoning_examples[-5:]
        return merged

    def limit_strategies_per_type(self, max_per_type: int=MAX_STRATEGIES_PER_TYPE) -> int:
        """
        Limit the number of strategies per problem type to the specified maximum in the database.
        This controls storage limit, not the number of strategies used during inference.
        Keeps the best performing strategies based on success rate and recency.
        
        Args:
            max_per_type: Maximum number of strategies to keep per problem type
            
        Returns:
            int: Number of strategies removed
        """
        strategies_by_type = {}
        for strategy in self.strategies:
            if strategy.problem_type not in strategies_by_type:
                strategies_by_type[strategy.problem_type] = []
            strategies_by_type[strategy.problem_type].append(strategy)
        to_remove = []
        for problem_type, strategies in strategies_by_type.items():
            if len(strategies) <= max_per_type:
                continue
            scored_strategies = []
            for strategy in strategies:
                recency_score = 0
                if strategy.last_used:
                    last_used = datetime.fromisoformat(strategy.last_used)
                    days_since = (datetime.now() - last_used).days
                    recency_score = max(0, 1.0 - min(1.0, days_since / 30.0))
                score = 0.7 * strategy.success_rate + 0.3 * recency_score
                scored_strategies.append((strategy, score))
            scored_strategies.sort(key=lambda x: x[1], reverse=True)
            for strategy, _ in scored_strategies[max_per_type:]:
                to_remove.append(strategy)
        initial_count = len(self.strategies)
        self.strategies = [s for s in self.strategies if s not in to_remove]
        removed_count = initial_count - len(self.strategies)
        if removed_count > 0:
            self.vectors = None
            self._save()
            logger.info(f'Removed {removed_count} excess strategies to maintain max {max_per_type} per type in database (storage limit)')
        return removed_count

def add_strategy(self, strategy: Strategy) -> None:
    """Add a new strategy to the database."""
    if strategy.strategy_id.startswith('strategy_'):
        try:
            strategy_num = int(strategy.strategy_id.split('_')[1])
            self.metrics['last_strategy_id'] = max(self.metrics['last_strategy_id'], strategy_num)
        except ValueError:
            pass
    exists = any((s.problem_type == strategy.problem_type for s in self.strategies))
    self.strategies.append(strategy)
    self.vectors = None
    self.metrics['strategies_created'] += 1
    self._save()
    if not exists:
        logger.info(f'Added first strategy for problem type: {strategy.problem_type}')
    else:
        logger.info(f'Added additional strategy for problem type: {strategy.problem_type}')

def update_strategy_performance(self, strategy_id: str, success: bool) -> None:
    """Update the performance metrics for a strategy."""
    strategy = self.get_strategy_by_id(strategy_id)
    if strategy:
        strategy.record_attempt(success)
        self.metrics['strategy_applications'] += 1
        if success:
            self.metrics['successful_resolutions'] += 1
        self._save()

def refine_strategy(self, strategy_id: str, refined_text: str) -> None:
    """Refine a strategy based on new insights."""
    strategy = self.get_strategy_by_id(strategy_id)
    if strategy:
        strategy.update_strategy(refined_text)
        self.metrics['strategies_refined'] += 1
        self._save()

def add_reasoning_example(self, strategy_id: str, reasoning: str) -> None:
    """Add a reasoning example to a strategy."""
    strategy = self.get_strategy_by_id(strategy_id)
    if strategy and reasoning:
        strategy.add_reasoning_example(reasoning)
        self.metrics['reasoning_examples_collected'] += 1
        self._save()

def add_example_to_strategy(self, strategy_id: str, example: str) -> None:
    """Add an example to a strategy."""
    strategy = self.get_strategy_by_id(strategy_id)
    if strategy and example:
        strategy.add_example(example)
        self._save()

def increment_query_count(self) -> None:
    """Increment the total query count."""
    self.metrics['total_queries'] += 1
    self._save()

def prune_strategies(self, min_success_rate: float=0.3, min_attempts: int=5) -> int:
    """Prune strategies with poor performance."""
    initial_count = len(self.strategies)
    self.strategies = [s for s in self.strategies if s.total_attempts < min_attempts or s.success_rate >= min_success_rate]
    pruned_count = initial_count - len(self.strategies)
    if pruned_count > 0:
        self.vectors = None
        self._save()
    return pruned_count

def run_spl(system_prompt: str, initial_query: str, client, model: str, request_config: dict=None) -> Tuple[str, int]:
    """
    Main plugin function that implements system prompt learning.
    
    By default, the plugin runs in inference-only mode, which uses existing strategies without modifying them.
    Setting request_config['spl_learning'] = True enables learning mode to create and refine strategies.
    
    Args:
        system_prompt: The system prompt
        initial_query: The user's query
        client: The LLM client
        model: The model identifier
        request_config: Optional request configuration
                       Can include {'spl_learning': True} to enable learning mode
    
    Returns:
        Tuple[str, int]: The LLM response and token count
    """
    start_time = time.time()
    logger.info(f'Starting SPL plugin execution for query: {initial_query[:100]}...')
    learning_mode = False
    if request_config and 'spl_learning' in request_config:
        learning_mode = request_config['spl_learning']
        logger.info(f'Running in learning mode: {learning_mode}')
    db = StrategyDatabase()
    logger.info(f'Current strategy count: {len(db.strategies)}')
    logger.info(f'Last strategy ID: {db.metrics.get('last_strategy_id', 0)}')
    if learning_mode:
        db.increment_query_count()
        db._save()
    problem_type = classify_problem(initial_query, client, model)
    logger.info(f'Classified problem as: {problem_type}')
    existing_strategies = db.get_strategies_for_problem(problem_type)
    logger.info(f'Found {len(existing_strategies)} existing strategies for {problem_type}')
    similar_strategy = None
    if learning_mode:
        should_create, similar_strategy = should_create_new_strategy(problem_type, initial_query, existing_strategies, db)
        if should_create:
            logger.info(f'Creating new strategy for {problem_type}')
            new_strategy = generate_strategy(initial_query, problem_type, client, model, db)
            db.add_strategy(new_strategy)
            logger.info(f'Added new strategy with ID: {new_strategy.strategy_id}')
        elif similar_strategy:
            logger.info(f'Updating existing strategy {similar_strategy.strategy_id} with new example')
            db.add_example_to_strategy(similar_strategy.strategy_id, initial_query)
    if learning_mode and db.metrics['total_queries'] % MAINTENANCE_INTERVAL == 0:
        merged_count = db.merge_similar_strategies(similarity_threshold=STRATEGY_MERGING_THRESHOLD)
        logger.info(f'Merged {merged_count} similar strategies')
        limited_count = db.limit_strategies_per_type(max_per_type=MAX_STRATEGIES_PER_TYPE)
        pruned_count = db.prune_strategies()
        logger.info(f'Pruned {pruned_count} low-performing strategies')
    existing_strategies = db.get_strategies_for_problem(problem_type)
    selected_strategies = select_relevant_strategies(initial_query, problem_type, db, learning_mode, MAX_STRATEGIES_FOR_INFERENCE)
    for i, strategy in enumerate(selected_strategies, 1):
        logger.info(f'Selected strategy {i}/{MAX_STRATEGIES_FOR_INFERENCE} for inference: {strategy.strategy_id} (success rate: {strategy.success_rate:.2f})')
    if not selected_strategies:
        if not existing_strategies:
            logger.info(f"No strategies exist for problem type '{problem_type}'. Enable learning mode with 'spl_learning=True' to create strategies.")
        else:
            logger.info(f"Strategies exist for problem type '{problem_type}' but none meet the minimum success rate threshold of {MIN_SUCCESS_RATE_FOR_INFERENCE:.2f}.")
            logger.info(f"Enable learning mode with 'spl_learning=True' to improve strategies.")
        logger.info('Running without strategy augmentation - using base system prompt only.')
        augmented_prompt = system_prompt
    else:
        augmented_prompt = augment_system_prompt(system_prompt, selected_strategies)
        logger.info(f'Augmented system prompt with {len(selected_strategies)} strategies (inference limit: {MAX_STRATEGIES_FOR_INFERENCE})')
    try:
        request_params = {}
        if request_config:
            request_params = {k: v for k, v in request_config.items() if k != 'spl_learning'}
        if 'max_tokens' not in request_params:
            request_params['max_tokens'] = DEFAULT_MAX_TOKENS
        elif request_params['max_tokens'] < DEFAULT_MAX_TOKENS:
            request_params['max_tokens'] = DEFAULT_MAX_TOKENS
        response = client.chat.completions.create(model=model, messages=[{'role': 'system', 'content': augmented_prompt}, {'role': 'user', 'content': initial_query}], **request_params)
        completion_tokens = response.usage.completion_tokens
        response_text = response.choices[0].message.content
        final_response, thinking = extract_thinking(response_text)
        logger.debug(f"Main response - raw: '{response_text}'")
        if thinking:
            logger.debug(f"Main response - thinking extracted: '{thinking}'")
            logger.debug(f"Main response - final answer after removing thinking: '{final_response}'")
        if learning_mode:
            if selected_strategies:
                strategy_effectiveness = evaluate_strategy_effectiveness(final_response, thinking, selected_strategies, client, model)
                for strategy_id, effective in strategy_effectiveness.items():
                    if strategy_id != 'fallback_temporary':
                        db.update_strategy_performance(strategy_id, effective)
                        logger.info(f'Strategy {strategy_id} effectiveness: {effective}')
                        if effective and thinking and (strategy_id != 'fallback_temporary'):
                            db.add_reasoning_example(strategy_id, thinking)
                            logger.info(f'Added reasoning example to strategy {strategy_id}')
                for strategy in selected_strategies:
                    if strategy.strategy_id != 'fallback_temporary' and strategy.total_attempts % 10 == 0 and (strategy.total_attempts > 0):
                        logger.info(f'Refining strategy {strategy.strategy_id} after {strategy.total_attempts} attempts')
                        refined_strategy = refine_strategy(strategy, initial_query, final_response, thinking, client, model)
                        db.refine_strategy(strategy.strategy_id, refined_strategy.strategy_text)
            else:
                logger.info('No strategies to evaluate or refine - consider adding strategies for this problem type')
        else:
            logger.info('Strategy evaluation and refinement skipped (not in learning mode)')
        execution_time = time.time() - start_time
        logger.info(f'SPL plugin execution completed in {execution_time:.2f} seconds')
        logger.info(f'Final strategy count: {len(db.strategies)}')
        logger.info(f'Final last strategy ID: {db.metrics.get('last_strategy_id', 0)}')
        return (response_text, completion_tokens)
    except Exception as e:
        logger.error(f'Error in SPL plugin: {str(e)}')
        try:
            response = client.chat.completions.create(model=model, messages=[{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': initial_query}], max_tokens=DEFAULT_MAX_TOKENS)
            return (response.choices[0].message.content, response.usage.completion_tokens)
        except Exception as inner_e:
            logger.error(f'Error in fallback completion: {str(inner_e)}')
            return (f'Error processing request: {str(e)}', 0)

