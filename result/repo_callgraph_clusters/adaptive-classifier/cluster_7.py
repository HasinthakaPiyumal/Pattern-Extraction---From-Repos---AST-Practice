# Cluster 7

class ConfigOptimizer:
    """Optimizer class to find best temperature configurations for queries."""

    def __init__(self, training_config: TrainingConfig):
        """Initialize the optimizer."""
        self.training_config = training_config
        self.classifier = AdaptiveClassifier('distilbert-base-uncased')
        self.evaluator = ResponseEvaluator()
        self.stats = {'total_queries': 0, 'successful_optimizations': 0, 'failed_optimizations': 0, 'avg_similarity_score': 0.0, 'class_distribution': {class_name: 0 for class_name in TemperatureConfig.class_ranges.keys()}, 'detailed_scores': []}

    def find_best_temperature_class(self, query: str) -> Tuple[Optional[str], float, Dict[str, float]]:
        """Find best temperature class for a query."""
        best_score = -1
        best_class = None
        best_metrics = {}
        configs_tested = 0
        for class_name in TemperatureConfig.class_ranges.keys():
            class_temps = TemperatureConfig.get_temperatures_for_class(class_name)
            for temp in class_temps:
                configs_tested += 1
                score, metrics = self._evaluate_temperature(query, temp)
                logger.debug(f'Temperature {temp:.1f} achieved score {score:.3f}')
                if score > best_score:
                    best_score = score
                    best_class = class_name
                    best_metrics = metrics
                if best_score >= 0.8:
                    break
            if best_score >= 0.8:
                break
        logger.info(f'Tested {configs_tested} configurations for query')
        return (best_class, best_score, best_metrics)

    def _evaluate_temperature(self, query: str, temperature: float) -> Tuple[float, Dict[str, float]]:
        """Evaluate a temperature setting using RTC."""
        config = {'temperature': temperature, 'top_p': 1.0}
        response_1 = self._get_llm_response(query, config)
        if not response_1:
            return (0.0, {})
        inverse_prompt = f'Given this query and response pair, generate a new query that would lead to a similar response:\n\nOriginal Query: {query}\nResponse: {response_1}\n\nGenerate a new query that would elicit a similar response:'
        alternate_query = self._get_llm_response(inverse_prompt, config)
        if not alternate_query:
            return (0.0, {})
        response_2 = self._get_llm_response(alternate_query, config)
        if not response_2:
            return (0.0, {})
        similarity_score, metrics = self.evaluator.evaluate_responses(response_1, response_2)
        metrics['temperature'] = temperature
        return (similarity_score, metrics)

    def _get_llm_response(self, prompt: str, config: Dict[str, float]) -> Optional[str]:
        """Get response from the LLM with improved error handling."""
        messages = [{'role': 'user', 'content': prompt}]
        for attempt in range(self.training_config.max_retries):
            try:
                response = client.chat.completions.create(model=self.training_config.model, messages=messages, max_tokens=4096, **config)
                if not response or not hasattr(response, 'choices') or (not response.choices):
                    logger.warning(f'Invalid response structure (attempt {attempt + 1})')
                    continue
                content = response.choices[0].message.content
                if not content or not isinstance(content, str):
                    logger.warning(f'Invalid content (attempt {attempt + 1})')
                    continue
                return content.strip()
            except Exception as e:
                logger.error(f'Error getting LLM response (attempt {attempt + 1}): {e}')
            if attempt < self.training_config.max_retries - 1:
                sleep_time = self.training_config.retry_delay * 2 ** attempt
                time.sleep(sleep_time)
        return None

    def optimize_and_train(self, save_path: str, push_to_hub: str):
        """Run optimization and training process."""
        try:
            dataset = load_dataset('lmarena-ai/arena-hard-auto-v0.1')
            logger.info('Successfully loaded dataset')
        except Exception as e:
            logger.error(f'Error loading dataset: {e}')
            return
        logger.info(f'Starting optimization for model: {self.training_config.model}')
        successful_examples = []
        for i in tqdm(range(0, min(len(dataset['train']), self.training_config.max_examples), self.training_config.batch_size)):
            batch = dataset['train'][i:i + self.training_config.batch_size]
            for item in batch:
                query = item['text'] if isinstance(item, dict) else str(item)
                self.stats['total_queries'] += 1
                best_class, score, metrics = self.find_best_temperature_class(query)
                if best_class and score >= self.training_config.similarity_threshold:
                    successful_examples.append((query, best_class))
                    self.stats['successful_optimizations'] += 1
                    self.stats['avg_similarity_score'] = (self.stats['avg_similarity_score'] * (len(successful_examples) - 1) + score) / len(successful_examples)
                    self.stats['class_distribution'][best_class] += 1
                    self.stats['detailed_scores'].append({'query': query, 'class': best_class, 'score': score, 'metrics': metrics})
                else:
                    self.stats['failed_optimizations'] += 1
                if self.stats['total_queries'] % 50 == 0:
                    self._print_intermediate_stats()
            if successful_examples:
                queries, labels = zip(*successful_examples)
                self.classifier.add_examples(list(queries), list(labels))
                successful_examples = []
        self._save_results(save_path)
        if push_to_hub:
            repo_id = f'adaptive-classifier/{push_to_hub}'
            logger.info(f'\nPushing to HuggingFace Hub: {repo_id}')
            try:
                self.classifier.push_to_hub(repo_id)
                logger.info('Successfully pushed to HuggingFace Hub')
            except Exception as e:
                logger.error(f'Error pushing to HuggingFace Hub: {e}')
        self._print_final_stats()

    def _print_intermediate_stats(self):
        """Print intermediate statistics."""
        logger.info('\nIntermediate Statistics:')
        logger.info(f'Processed queries: {self.stats['total_queries']}')
        logger.info(f'Successful optimizations: {self.stats['successful_optimizations']}')
        success_rate = self.stats['successful_optimizations'] / self.stats['total_queries'] * 100
        logger.info(f'Current success rate: {success_rate:.2f}%')
        logger.info(f'Average similarity score: {self.stats['avg_similarity_score']:.3f}')
        logger.info('\nClass distribution:')
        for class_name, count in self.stats['class_distribution'].items():
            if count > 0:
                percentage = count / self.stats['successful_optimizations'] * 100
                logger.info(f'{class_name}: {count} ({percentage:.1f}%)')

    def _print_final_stats(self):
        """Print final detailed statistics."""
        logger.info('\nFinal Statistics:')
        logger.info(f'Total queries processed: {self.stats['total_queries']}')
        logger.info(f'Successful optimizations: {self.stats['successful_optimizations']}')
        logger.info(f'Failed optimizations: {self.stats['failed_optimizations']}')
        if self.stats['successful_optimizations'] > 0:
            success_rate = self.stats['successful_optimizations'] / self.stats['total_queries'] * 100
            logger.info(f'Success rate: {success_rate:.2f}%')
            logger.info(f'Average similarity score: {self.stats['avg_similarity_score']:.3f}')
            logger.info('\nTemperature Class Distribution:')
            for class_name, count in sorted(self.stats['class_distribution'].items(), key=lambda x: x[1], reverse=True):
                if count > 0:
                    percentage = count / self.stats['successful_optimizations'] * 100
                    logger.info(f'{class_name}: {count} ({percentage:.1f}%)')
            logger.info('\nAverage Scores by Class:')
            class_scores = {}
            for result in self.stats['detailed_scores']:
                class_name = result['class']
                if class_name not in class_scores:
                    class_scores[class_name] = []
                class_scores[class_name].append(result['score'])
            for class_name, scores in class_scores.items():
                avg_score = sum(scores) / len(scores)
                logger.info(f'{class_name}: {avg_score:.3f}')

    def _save_results(self, save_path: str):
        """Save classifier and statistics."""
        self.classifier.save(save_path)
        stats_path = Path(save_path) / 'optimization_stats.json'
        with open(stats_path, 'w') as f:
            json.dump(self.stats, f, indent=2)
        logger.info(f'\nResults saved to {save_path}')

def _evaluate_temperature(self, query: str, temperature: float) -> Tuple[float, Dict[str, float]]:
    """Evaluate a temperature setting using RTC."""
    config = {'temperature': temperature, 'top_p': 1.0}
    response_1 = self._get_llm_response(query, config)
    if not response_1:
        return (0.0, {})
    inverse_prompt = f'Given this query and response pair, generate a new query that would lead to a similar response:\n\nOriginal Query: {query}\nResponse: {response_1}\n\nGenerate a new query that would elicit a similar response:'
    alternate_query = self._get_llm_response(inverse_prompt, config)
    if not alternate_query:
        return (0.0, {})
    response_2 = self._get_llm_response(alternate_query, config)
    if not response_2:
        return (0.0, {})
    similarity_score, metrics = self.evaluator.evaluate_responses(response_1, response_2)
    metrics['temperature'] = temperature
    return (similarity_score, metrics)

