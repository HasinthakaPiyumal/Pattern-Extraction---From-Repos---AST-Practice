# Cluster 4

def setup_args() -> argparse.Namespace:
    """Setup command line arguments."""
    parser = argparse.ArgumentParser(description='Benchmark Adaptive Classifier')
    parser.add_argument('--model', type=str, default='distilbert/distilbert-base-cased', help='Base transformer model to use')
    parser.add_argument('--batch-size', type=int, default=32, help='Batch size for processing')
    parser.add_argument('--max-samples', type=int, default=1200, help='Maximum number of samples to use (for testing)')
    parser.add_argument('--output-dir', type=str, default='benchmark_results', help='Directory to save results')
    parser.add_argument('--push-to-hub', action='store_true', help='Push the trained model to HuggingFace Hub')
    parser.add_argument('--hub-repo', type=str, help='HuggingFace Hub repository ID (e.g. "username/model-name") for pushing the model')
    parser.add_argument('--hub-token', type=str, help='HuggingFace Hub token. If not provided, will look for the token in the environment')
    return parser.parse_args()

def push_to_hub(classifier: AdaptiveClassifier, repo_id: str, token: str=None, metrics: Dict[str, Any]=None) -> str:
    """Push the classifier to HuggingFace Hub.
    
    Args:
        classifier: Trained classifier to push
        repo_id: HuggingFace Hub repository ID
        token: HuggingFace Hub token
        metrics: Optional evaluation metrics to add to model card
        
    Returns:
        URL of the model on the Hub
    """
    logger.info(f'Pushing model to HuggingFace Hub: {repo_id}')
    if token:
        HfFolder.save_token(token)
    try:
        url = classifier.push_to_hub(repo_id, commit_message='Upload from benchmark script')
        logger.info(f'Successfully pushed model to Hub: {url}')
        return url
    except Exception as e:
        logger.error(f'Error pushing to Hub: {str(e)}')
        raise

def save_results(classifier: AdaptiveClassifier, results: Dict[str, Any], args: argparse.Namespace):
    """Save evaluation results and optionally push to Hub."""
    os.makedirs(args.output_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'benchmark_results_{timestamp}.json'
    filepath = os.path.join(args.output_dir, filename)
    results['config'] = {'model': args.model, 'batch_size': args.batch_size, 'max_samples': args.max_samples, 'timestamp': timestamp}
    classifier.save(args.output_dir)
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f'Results saved to {filepath}')
    if args.push_to_hub:
        if not args.hub_repo:
            raise ValueError('--hub-repo must be specified when using --push-to-hub')
        hub_url = push_to_hub(classifier, args.hub_repo, args.hub_token, metrics=results['metrics'])
        results['hub_url'] = hub_url
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)
    print('\nEvaluation Results:')
    print('-' * 50)
    print(f'Model: {args.model}')
    print(f'Accuracy: {results['metrics']['accuracy']:.4f}')
    print('\nPer-class metrics:')
    for label in ['HIGH', 'LOW']:
        metrics = results['metrics'][label]
        print(f'\n{label}:')
        print(f'  Precision: {metrics['precision']:.4f}')
        print(f'  Recall: {metrics['recall']:.4f}')
        print(f'  F1-score: {metrics['f1-score']:.4f}')
    print('\nConfusion Matrix:')
    print('            Predicted')
    print('             HIGH  LOW')
    print(f'Actual HIGH  {results['confusion_matrix'][0][0]:4d}  {results['confusion_matrix'][0][1]:4d}')
    print(f'      LOW   {results['confusion_matrix'][1][0]:4d}  {results['confusion_matrix'][1][1]:4d}')
    if args.push_to_hub:
        print(f'\nModel pushed to HuggingFace Hub: {results['hub_url']}')

def get_llm_response(messages: List[Dict], model: str, config: RouterConfig) -> Optional[str]:
    """Get response from the LLM with retry logic."""
    for attempt in range(config.max_retries):
        try:
            response = client.chat.completions.create(model=model, messages=messages, max_tokens=4096)
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f'Error getting LLM response (attempt {attempt + 1}): {e}')
            if attempt < config.max_retries - 1:
                time.sleep(config.retry_delay)
            continue
    return None

def save_results(output_file: str, router: LLMRouter, results: List[Dict]):
    """Save evaluation results to file."""
    with open(output_file, 'w') as f:
        json.dump({'stats': router.get_stats(), 'results': results}, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description='Evaluate LLM router on arena-hard-auto dataset')
    parser.add_argument('--high-model', type=str, default='gpt-4o', help='Model to use for high-complexity queries')
    parser.add_argument('--low-model', type=str, default='gpt-4o-mini', help='Model to use for low-complexity queries')
    parser.add_argument('--without-adaptation', action='store_true', help='Disable adaptive learning during evaluation')
    parser.add_argument('--output', type=str, default='router_eval_results.json', help='Output file for results')
    parser.add_argument('--router-path', type=str, default='./adaptive_router', help='Path to load/save the adaptive router')
    args = parser.parse_args()
    os.makedirs('benchmark_results', exist_ok=True)
    output_file = os.path.join('benchmark_results', args.output)
    config = RouterConfig(high_model=args.high_model, low_model=args.low_model, adaptive_router_path=args.router_path)
    evaluate_dataset(config, enable_adaptation=not args.without_adaptation, output_file=output_file)

def convert_to_serializable(obj):
    """Convert numpy/torch types to JSON serializable types."""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, torch.Tensor):
        return obj.detach().cpu().numpy().tolist()
    elif isinstance(obj, dict):
        return {key: convert_to_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(item) for item in obj]
    else:
        return obj

def train_classifier(model_name: str, train_texts: List[str], train_labels: List[str], config: Dict[str, Any]=None) -> AdaptiveClassifier:
    """Train an adaptive classifier on the training data.
    
    Args:
        model_name: Name of the transformer model to use
        train_texts: Training texts
        train_labels: Training labels
        config: Optional configuration for the classifier
        
    Returns:
        Trained AdaptiveClassifier instance
    """
    logger.info(f'Training classifier with model: {model_name}')
    logger.info(f'Strategic mode: {(config.get('enable_strategic_mode', False) if config else False)}')
    classifier = AdaptiveClassifier(model_name, config=config)
    if config and config.get('enable_strategic_mode'):
        logger.info(f'Strategic mode enabled: {classifier.strategic_mode}')
        logger.info(f'Strategic cost function: {classifier.strategic_cost_function is not None}')
        logger.info(f'Strategic optimizer: {classifier.strategic_optimizer is not None}')
        if not classifier.strategic_mode:
            error_msg = f'CRITICAL ERROR: Strategic mode failed to initialize!\nConfig cost_coefficients: {config.get('cost_coefficients')}\nConfig cost_function_type: {config.get('cost_function_type')}\nStrategic mode is required for this evaluation. Please fix the strategic classifier implementation.'
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    batch_size = 50
    for i in range(0, len(train_texts), batch_size):
        batch_texts = train_texts[i:i + batch_size]
        batch_labels = train_labels[i:i + batch_size]
        classifier.add_examples(batch_texts, batch_labels)
        if (i // batch_size + 1) % 10 == 0:
            logger.info(f'Processed {i + len(batch_texts)} / {len(train_texts)} training examples')
    logger.info('Training completed')
    return classifier

def evaluate_strategic_robustness(strategic_classifier: AdaptiveClassifier, test_texts: List[str], test_labels: List[str]) -> Dict[str, Any]:
    """Evaluate strategic robustness at different gaming levels.
    
    Args:
        strategic_classifier: Classifier with strategic capabilities
        test_texts: Test texts  
        test_labels: Test labels
        
    Returns:
        Dictionary of robustness metrics
    """
    if not strategic_classifier.strategic_mode:
        logger.error('Strategic mode not enabled - cannot evaluate robustness')
        raise RuntimeError('Strategic mode not enabled - cannot evaluate robustness')
    logger.info('Evaluating strategic robustness...')
    gaming_levels = [0.0, 0.25, 0.5, 0.75, 1.0]
    robustness_results = {}
    for level in gaming_levels:
        logger.info(f'Testing gaming level: {level}')
        if level == 0.0:
            results = evaluate_classifier(strategic_classifier, test_texts, test_labels, mode='regular')
        elif level == 1.0:
            results = evaluate_classifier(strategic_classifier, test_texts, test_labels, mode='strategic')
        else:
            results = evaluate_classifier(strategic_classifier, test_texts, test_labels, mode='dual')
        robustness_results[f'gaming_level_{level}'] = {'accuracy': results['accuracy'], 'f1_score': results['f1_score'], 'avg_confidence': results['avg_confidence']}
    baseline_accuracy = robustness_results['gaming_level_0.0']['accuracy']
    strategic_accuracy = robustness_results['gaming_level_1.0']['accuracy']
    robustness_score = baseline_accuracy - strategic_accuracy
    relative_robustness = strategic_accuracy / baseline_accuracy if baseline_accuracy > 0 else 0.0
    robustness_results['summary'] = {'baseline_accuracy': baseline_accuracy, 'strategic_accuracy': strategic_accuracy, 'robustness_score': robustness_score, 'relative_robustness': relative_robustness}
    logger.info(f'Robustness Score: {robustness_score:.4f}')
    logger.info(f'Relative Robustness: {relative_robustness:.4f}')
    return robustness_results

def main():
    parser = argparse.ArgumentParser(description='Evaluate Strategic Classifier on AI-Secure/adv_glue dataset')
    parser.add_argument('--model', type=str, default='answerdotai/ModernBERT-base', help="HuggingFace model name to use (default: answerdotai/ModernBERT-base). The script automatically adapts to any model's embedding dimension.")
    parser.add_argument('--cost-strategy', type=str, default='balanced', choices=['balanced', 'sparse_low', 'uniform_low', 'minimal', 'sparse_high'], help="Strategic cost function strategy. Options: 'balanced' (50%% manipulable dims, cost 0.3), 'sparse_low' (20%% manipulable dims, cost 0.4), 'uniform_low' (all dims, cost 0.15), 'minimal' (all dims, cost 0.05 - for debugging), 'sparse_high' (legacy - adjusted to be less restrictive)")
    parser.add_argument('--output', type=str, default='strategic_classifier_evaluation_results.json', help='Output file for results (default: strategic_classifier_evaluation_results.json)')
    parser.add_argument('--test-size', type=float, default=0.3, help='Fraction of data to use for testing (default: 0.3)')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducibility (default: 42)')
    args = parser.parse_args()
    set_seed(args.seed)
    logger.info('Starting Strategic Classifier Evaluation')
    logger.info(f'Model: {args.model}')
    logger.info(f'Cost strategy: {args.cost_strategy}')
    logger.info(f'Output file: {args.output}')
    logger.info(f'Test size: {args.test_size}')
    logger.info(f'Random seed: {args.seed}')
    start_time = time.time()
    try:
        texts, labels = load_adv_glue_dataset()
        train_texts, test_texts, train_labels, test_labels = split_dataset(texts, labels, test_size=args.test_size, random_state=args.seed)
        logger.info('=' * 60)
        logger.info('TRAINING REGULAR CLASSIFIER')
        logger.info('=' * 60)
        regular_classifier = train_classifier(args.model, train_texts, train_labels, config=None)
        logger.info('=' * 60)
        logger.info('TRAINING STRATEGIC CLASSIFIER')
        logger.info('=' * 60)
        strategic_config = create_strategic_config(args.model, args.cost_strategy)
        strategic_classifier = train_classifier(args.model, train_texts, train_labels, config=strategic_config)
        if not strategic_classifier.strategic_mode:
            raise RuntimeError('Strategic mode failed to initialize. Cannot proceed with strategic evaluation.')
        logger.info('=' * 60)
        logger.info('EVALUATION PHASE')
        logger.info('=' * 60)
        regular_results = evaluate_classifier(regular_classifier, test_texts, test_labels, mode='regular')
        strategic_dual_results = evaluate_classifier(strategic_classifier, test_texts, test_labels, mode='dual')
        strategic_only_results = evaluate_classifier(strategic_classifier, test_texts, test_labels, mode='strategic')
        robust_results = evaluate_classifier(strategic_classifier, test_texts, test_labels, mode='robust')
        comparison_results = evaluate_comparison_on_manipulated_data(regular_classifier, strategic_classifier, test_texts, test_labels)
        robustness_results = evaluate_strategic_robustness(strategic_classifier, test_texts, test_labels)
        end_time = time.time()
        total_time = end_time - start_time
        final_results = {'metadata': {'model_name': args.model, 'dataset': 'AI-Secure/adv_glue (adv_sst2)', 'evaluation_date': datetime.now().isoformat(), 'total_examples': len(texts), 'train_examples': len(train_texts), 'test_examples': len(test_texts), 'test_size': args.test_size, 'random_seed': args.seed, 'total_evaluation_time': total_time}, 'dataset_info': {'train_label_distribution': dict(zip(*np.unique(train_labels, return_counts=True))), 'test_label_distribution': dict(zip(*np.unique(test_labels, return_counts=True)))}, 'regular_classifier': regular_results, 'strategic_classifier': {'dual_mode': strategic_dual_results, 'strategic_only_mode': strategic_only_results, 'robust_mode': robust_results}, 'strategic_robustness': robustness_results, 'fair_comparison_on_manipulated_data': comparison_results, 'comparison': {'accuracy_improvement': strategic_dual_results['accuracy'] - regular_results['accuracy'], 'f1_improvement': strategic_dual_results['f1_score'] - regular_results['f1_score'], 'relative_accuracy_improvement': (strategic_dual_results['accuracy'] - regular_results['accuracy']) / regular_results['accuracy'] if regular_results['accuracy'] > 0 else 0.0}, 'config': {'strategic_config': strategic_config, 'cost_strategy': args.cost_strategy}}
        output_path = Path(args.output)
        serializable_results = convert_to_serializable(final_results)
        with open(output_path, 'w') as f:
            json.dump(serializable_results, f, indent=2, sort_keys=True)
        logger.info('=' * 60)
        logger.info('EVALUATION SUMMARY')
        logger.info('=' * 60)
        logger.info(f'Regular Classifier Accuracy: {regular_results['accuracy']:.4f}')
        logger.info(f'Strategic Classifier (Dual) Accuracy: {strategic_dual_results['accuracy']:.4f}')
        logger.info(f'Strategic Classifier (Strategic-only) Accuracy: {strategic_only_results['accuracy']:.4f}')
        logger.info(f'Strategic Classifier (Robust) Accuracy: {robust_results['accuracy']:.4f}')
        logger.info('')
        logger.info(f'Accuracy Improvement: {final_results['comparison']['accuracy_improvement']:.4f}')
        logger.info(f'F1-score Improvement: {final_results['comparison']['f1_improvement']:.4f}')
        logger.info(f'Relative Accuracy Improvement: {final_results['comparison']['relative_accuracy_improvement']:.4f}')
        if robustness_results and 'summary' in robustness_results:
            logger.info('')
            logger.info(f'Strategic Robustness Score: {robustness_results['summary']['robustness_score']:.4f}')
            logger.info(f'Relative Robustness: {robustness_results['summary']['relative_robustness']:.4f}')
        if comparison_results and 'comparison' in comparison_results:
            logger.info('')
            logger.info('COMPARISON ON MANIPULATED DATA:')
            logger.info(f'Regular Classifier on Manipulated Data: {comparison_results['regular_on_manipulated']['accuracy']:.4f}')
            logger.info(f'Strategic Classifier on Manipulated Data: {comparison_results['strategic_on_manipulated']['accuracy']:.4f}')
            logger.info(f'Accuracy Improvement: {comparison_results['comparison']['accuracy_improvement']:.4f}')
            logger.info(f'F1-score Improvement: {comparison_results['comparison']['f1_improvement']:.4f}')
        logger.info('')
        logger.info(f'Total Evaluation Time: {total_time:.2f} seconds')
        logger.info(f'Results saved to: {output_path}')
        logger.info('=' * 60)
        logger.info('EVALUATION COMPLETED SUCCESSFULLY')
        logger.info('=' * 60)
    except Exception as e:
        logger.error(f'Evaluation failed: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)

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

def _save_results(self, save_path: str):
    """Save classifier and statistics."""
    self.classifier.save(save_path)
    stats_path = Path(save_path) / 'optimization_stats.json'
    with open(stats_path, 'w') as f:
        json.dump(self.stats, f, indent=2)
    logger.info(f'\nResults saved to {save_path}')

def main():
    parser = argparse.ArgumentParser(description='Train an adaptive classifier for LLM temperature optimization')
    parser.add_argument('--model', type=str, required=True, help='Name of the model to optimize')
    parser.add_argument('--max-examples', type=int, default=500, help='Maximum number of examples to process')
    parser.add_argument('--save-path', type=str, default='./config_optimizer', help='Path to save the classifier')
    parser.add_argument('--push-to-hub', type=str, help='Name to use when pushing to HuggingFace')
    parser.add_argument('--batch-size', type=int, default=5, help='Batch size for processing examples')
    parser.add_argument('--similarity-threshold', type=float, default=0.5, help='Minimum similarity score threshold')
    args = parser.parse_args()
    os.makedirs(args.save_path, exist_ok=True)
    logger.info('Starting optimization with configuration:')
    logger.info(f'Model: {args.model}')
    logger.info(f'Max examples: {args.max_examples}')
    logger.info(f'Batch size: {args.batch_size}')
    logger.info(f'Similarity threshold: {args.similarity_threshold}')
    logger.info(f'Save path: {args.save_path}')
    logger.info(f'Push to hub: {args.push_to_hub}')
    training_config = TrainingConfig(model=args.model, max_examples=args.max_examples, batch_size=args.batch_size, similarity_threshold=args.similarity_threshold)
    optimizer = ConfigOptimizer(training_config)
    optimizer.optimize_and_train(args.save_path, args.push_to_hub)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Train and evaluate a hallucination detector using adaptive-classifier')
    parser.add_argument('--train-percentage', type=float, default=20.0, help='Percentage of dataset to use for training (default: 20%%)')
    parser.add_argument('--train-count', type=int, default=None, help='Fixed number of examples to use for training (overrides --train-percentage if specified)')
    parser.add_argument('--use-all-data', action='store_true', help='Use all available data for training and testing (overrides other training parameters)')
    parser.add_argument('--model-name', type=str, default='distilbert-base-uncased', help='Hugging Face model name to use as the base model')
    parser.add_argument('--save-dir', type=str, default='./hallucination-detector', help='Directory to save the trained model')
    parser.add_argument('--push-to-hub', type=str, help='Name to use when pushing to HuggingFace Hub under adaptive-classifier/')
    parser.add_argument('--batch-size', type=int, default=16, help='Batch size for training')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducibility')
    parser.add_argument('--min-examples', type=int, default=0, help='Minimum number of examples required per task (default: 0, use all available data)')
    parser.add_argument('--verbose', action='store_true', help='Enable more detailed logging')
    parser.add_argument('--log-level', type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], default='INFO', help='Set the logging level')
    return parser.parse_args()

def train_and_evaluate(args):
    """Train and evaluate the hallucination detector."""
    logger.info(f'Loading dataset with training parameters:')
    if args.use_all_data:
        logger.info('  - Using all data for both training and testing')
    elif args.train_count is not None:
        logger.info(f'  - Using fixed count of {args.train_count} examples for training')
    else:
        logger.info(f'  - Using {args.train_percentage}% of data for training')
    splits = load_and_split_dataset(args)
    if not splits:
        logger.error('No data found in dataset. Please check the dataset structure.')
        return {}
    logger.info(f'Initializing adaptive classifier with {args.model_name}')
    config = {'max_length': 2048, 'batch_size': 4, 'max_examples_per_class': 100, 'prototype_update_frequency': 10, 'similarity_threshold': 0.6, 'learning_rate': 2e-05, 'epochs': 5, 'early_stopping_patience': 2, 'prototype_weight': 0.7, 'neural_weight': 0.3}
    classifier = AdaptiveClassifier(args.model_name, config=config)
    save_dir = Path(args.save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    task_stats = {}
    for task_type in splits.keys():
        logger.info(f'Processing task: {task_type}')
        train_texts, train_labels = prepare_examples(splits[task_type]['train'], task_type)
        test_texts, test_labels = prepare_examples(splits[task_type]['test'], task_type)
        if len(train_texts) == 0 or len(test_texts) == 0:
            logger.warning(f'No data for task {task_type}. Skipping.')
            continue
        elif len(train_texts) < args.min_examples or len(test_texts) < args.min_examples:
            logger.warning(f'Not enough data for task {task_type}. Minimum required: {args.min_examples}. Found: {len(train_texts)} train, {len(test_texts)} test. Skipping.')
            continue
        train_positive = sum((1 for label in train_labels if label == 'HALLUCINATED'))
        train_negative = len(train_labels) - train_positive
        test_positive = sum((1 for label in test_labels if label == 'HALLUCINATED'))
        test_negative = len(test_labels) - test_positive
        logger.info(f'Train distribution for {task_type}: {train_positive} HALLUCINATED, {train_negative} NOT_HALLUCINATED')
        logger.info(f'Test distribution for {task_type}: {test_positive} HALLUCINATED, {test_negative} NOT_HALLUCINATED')
        logger.info(f'Training on {len(train_texts)} examples for task {task_type}')
        batch_size = args.batch_size
        for i in range(0, len(train_texts), batch_size):
            end_idx = min(i + batch_size, len(train_texts))
            batch_texts = train_texts[i:end_idx]
            batch_labels = train_labels[i:end_idx]
            classifier.add_examples(batch_texts, batch_labels)
            if i // batch_size % 10 == 0 and i > 0:
                logger.info(f'Added {i + len(batch_texts)} examples so far...')
        logger.info(f'Evaluating on {len(test_texts)} examples for task {task_type}')
        metrics = evaluate_classifier(classifier, test_texts, test_labels)
        true_positives = sum((1 for true, pred in zip(metrics['true_labels'], metrics['predictions']) if true == 'HALLUCINATED' and pred == 'HALLUCINATED'))
        false_positives = sum((1 for true, pred in zip(metrics['true_labels'], metrics['predictions']) if true == 'NOT_HALLUCINATED' and pred == 'HALLUCINATED'))
        true_negatives = sum((1 for true, pred in zip(metrics['true_labels'], metrics['predictions']) if true == 'NOT_HALLUCINATED' and pred == 'NOT_HALLUCINATED'))
        false_negatives = sum((1 for true, pred in zip(metrics['true_labels'], metrics['predictions']) if true == 'HALLUCINATED' and pred == 'NOT_HALLUCINATED'))
        confusion_matrix = {'true_positives': true_positives, 'false_positives': false_positives, 'true_negatives': true_negatives, 'false_negatives': false_negatives}
        task_stats[task_type] = {'precision': metrics['precision'], 'recall': metrics['recall'], 'f1': metrics['f1'], 'throughput': metrics['throughput'], 'num_train_examples': len(train_texts), 'num_test_examples': len(test_texts), 'confusion_matrix': confusion_matrix}
        logger.info(f'Task: {task_type} - Precision: {metrics['precision']:.2f}%, Recall: {metrics['recall']:.2f}%, F1: {metrics['f1']:.2f}%')
        logger.info(f'Throughput: {metrics['throughput']:.2f} examples/second')
        logger.info(f'Confusion Matrix: TP={true_positives}, FP={false_positives}, TN={true_negatives}, FN={false_negatives}')
        if 'predictions' in metrics:
            del metrics['predictions']
        if 'true_labels' in metrics:
            del metrics['true_labels']
    if not task_stats:
        logger.warning('No task statistics available. Skipping overall metrics calculation.')
        return {'metadata': {'train_percentage': args.train_percentage, 'model_name': args.model_name, 'batch_size': args.batch_size, 'seed': args.seed, 'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'), 'error': 'No data processed successfully'}}
    total_test = sum((stats['num_test_examples'] for stats in task_stats.values()))
    if total_test > 0:
        overall_precision = sum((stats['precision'] * stats['num_test_examples'] / total_test for stats in task_stats.values()))
        overall_recall = sum((stats['recall'] * stats['num_test_examples'] / total_test for stats in task_stats.values()))
        overall_f1 = sum((stats['f1'] * stats['num_test_examples'] / total_test for stats in task_stats.values()))
        overall_throughput = sum((stats['throughput'] * stats['num_test_examples'] / total_test for stats in task_stats.values()))
        overall_tp = sum((stats['confusion_matrix']['true_positives'] for stats in task_stats.values()))
        overall_fp = sum((stats['confusion_matrix']['false_positives'] for stats in task_stats.values()))
        overall_tn = sum((stats['confusion_matrix']['true_negatives'] for stats in task_stats.values()))
        overall_fn = sum((stats['confusion_matrix']['false_negatives'] for stats in task_stats.values()))
        task_stats['overall'] = {'precision': overall_precision, 'recall': overall_recall, 'f1': overall_f1, 'throughput': overall_throughput, 'confusion_matrix': {'true_positives': overall_tp, 'false_positives': overall_fp, 'true_negatives': overall_tn, 'false_negatives': overall_fn}}
        logger.info(f'Overall - Precision: {overall_precision:.2f}%, Recall: {overall_recall:.2f}%, F1: {overall_f1:.2f}%')
        logger.info(f'Overall Throughput: {overall_throughput:.2f} examples/second')
        logger.info(f'Overall Confusion Matrix: TP={overall_tp}, FP={overall_fp}, TN={overall_tn}, FN={overall_fn}')
    task_stats['metadata'] = {'train_percentage': args.train_percentage, 'model_name': args.model_name, 'batch_size': args.batch_size, 'seed': args.seed, 'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')}
    logger.info(f'Saving model to {save_dir}')
    classifier.save(save_dir)
    metrics_file = save_dir / 'metrics.json'
    with open(metrics_file, 'w') as f:
        json.dump(task_stats, f, indent=2)
    logger.info(f'Metrics saved to {metrics_file}')
    if args.push_to_hub:
        repo_id = f'adaptive-classifier/{args.push_to_hub}'
        logger.info(f'Pushing model to HuggingFace Hub: {repo_id}')
        try:
            classifier.push_to_hub(repo_id)
            logger.info(f'Successfully pushed to {repo_id}')
        except Exception as e:
            logger.error(f'Error pushing to HuggingFace Hub: {e}')
            logger.info('Trying alternative push method...')
            try:
                from huggingface_hub import upload_folder
                upload_folder(folder_path=str(save_dir), repo_id=repo_id, repo_type='model')
                logger.info(f'Successfully pushed to {repo_id} using upload_folder')
            except Exception as e:
                logger.error(f'Error using alternative push method: {e}')
    return task_stats

def main():
    args = parse_args()
    log_level = getattr(logging, args.log_level)
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    set_seeds(args.seed)
    try:
        stats = train_and_evaluate(args)
        if not stats or not any((key not in ['metadata'] for key in stats.keys())):
            logger.warning('No statistics available. Cannot generate report.')
            return
        print('\nResults Summary:')
        print('=' * 80)
        print(f'{'Task':<15} {'Precision':<12} {'Recall':<12} {'F1':<12} {'Throughput':<12}')
        print('-' * 80)
        for task_type, metrics in stats.items():
            if task_type not in ['overall', 'metadata']:
                print(f'{task_type:<15} {metrics['precision']:<12.2f} {metrics['recall']:<12.2f} {metrics['f1']:<12.2f} {metrics['throughput']:<12.2f}')
        print('-' * 80)
        if 'overall' in stats:
            print(f'{'overall':<15} {stats['overall']['precision']:<12.2f} {stats['overall']['recall']:<12.2f} {stats['overall']['f1']:<12.2f} {stats['overall']['throughput']:<12.2f}')
        print('=' * 80)
        print_comparison_table(stats, args)
    except Exception as e:
        logger.error(f'Error during execution: {e}')
        raise

class AdaptiveClassifier(ModelHubMixin):
    """A flexible classifier that can adapt to new classes and examples."""

    def __init__(self, model_name: str, device: Optional[str]=None, config: Optional[Dict[str, Any]]=None, seed: int=42, use_onnx: Optional[Union[bool, str]]='auto', trust_remote_code: bool=False):
        """Initialize the adaptive classifier.

        Args:
            model_name: Name of the HuggingFace transformer model
            device: Device to run the model on (default: auto-detect)
            config: Optional configuration dictionary
            seed: Random seed for initialization
            use_onnx: Whether to use ONNX Runtime ("auto", True, False).
                     "auto" uses ONNX on CPU, PyTorch on GPU.
            trust_remote_code: Whether to trust remote code when loading models (default: False)
        """
        torch.manual_seed(seed)
        self.config = ModelConfig(config)
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.use_onnx = self._should_use_onnx(use_onnx)
        if self.use_onnx:
            try:
                from optimum.onnxruntime import ORTModelForFeatureExtraction
                logger.info(f'Initializing ONNX model for {model_name}')
                self.model = ORTModelForFeatureExtraction.from_pretrained(model_name, export=True, trust_remote_code=trust_remote_code)
                logger.info('Successfully loaded ONNX model')
            except ImportError:
                logger.warning('optimum[onnxruntime] not installed. Falling back to PyTorch. Install with: pip install optimum[onnxruntime]')
                self.use_onnx = False
                self.model = AutoModel.from_pretrained(model_name, trust_remote_code=trust_remote_code).to(self.device)
            except Exception as e:
                logger.warning(f'Failed to load ONNX model: {e}. Falling back to PyTorch.')
                self.use_onnx = False
                self.model = AutoModel.from_pretrained(model_name, trust_remote_code=trust_remote_code).to(self.device)
        else:
            self.model = AutoModel.from_pretrained(model_name, trust_remote_code=trust_remote_code).to(self.device)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=trust_remote_code)
        self.embedding_dim = self.model.config.hidden_size
        self.memory = PrototypeMemory(self.embedding_dim, config=self.config)
        self.adaptive_head = None
        self.label_to_id = {}
        self.id_to_label = {}
        self.train_steps = 0
        self.training_history = {}
        self.strategic_cost_function = None
        self.strategic_optimizer = None
        self.strategic_evaluator = None
        if self.config.enable_strategic_mode:
            self._initialize_strategic_components()

    def _should_use_onnx(self, use_onnx: Union[bool, str]) -> bool:
        """Determine if ONNX should be used based on configuration and device.

        Args:
            use_onnx: User preference ("auto", True, False)

        Returns:
            True if ONNX should be used, False otherwise
        """
        if use_onnx == 'auto':
            return self.device == 'cpu'
        elif isinstance(use_onnx, bool):
            return use_onnx
        else:
            logger.warning(f'Invalid use_onnx value: {use_onnx}. Using auto-detection.')
            return self.device == 'cpu'

    def add_examples(self, texts: List[str], labels: List[str]):
        """Add new examples with special handling for new classes."""
        if not texts or not labels:
            raise ValueError('Empty input lists')
        if len(texts) != len(labels):
            raise ValueError('Mismatched text and label lists')
        has_existing_classes = len(self.label_to_id) > 0
        new_classes = set(labels) - set(self.label_to_id.keys())
        is_adding_new_classes = len(new_classes) > 0
        for label in sorted(new_classes):
            idx = len(self.label_to_id)
            self.label_to_id[label] = idx
            self.id_to_label[idx] = label
        embeddings = self._get_embeddings(texts)
        for text, embedding, label in zip(texts, embeddings, labels):
            example = Example(text, label, embedding)
            self.memory.add_example(example, label)
            if label not in self.training_history:
                self.training_history[label] = 0
            self.training_history[label] += 1
        is_incremental_learning = is_adding_new_classes and has_existing_classes
        if is_incremental_learning:
            old_head = copy.deepcopy(self.adaptive_head) if self.adaptive_head is not None else None
            num_classes = len(self.label_to_id)
            self.adaptive_head.update_num_classes(num_classes)
            self.adaptive_head = self.adaptive_head.to(self.device)
            self._train_new_classes(old_head, new_classes)
        else:
            if self.adaptive_head is None:
                self._initialize_adaptive_head()
            elif is_adding_new_classes:
                num_classes = len(self.label_to_id)
                self.adaptive_head.update_num_classes(num_classes)
                self.adaptive_head = self.adaptive_head.to(self.device)
            self._train_adaptive_head()
            if self.strategic_mode and self.train_steps % self.config.strategic_training_frequency == 0:
                self._perform_strategic_training()
        self.memory._rebuild_index()

    def _train_new_classes(self, old_head: Optional[nn.Module], new_classes: Set[str]):
        """Train the model with focus on new classes while preserving old class knowledge."""
        if not self.memory.examples:
            return
        all_embeddings = []
        all_labels = []
        examples_per_class = {}
        for label in self.memory.examples:
            examples_per_class[label] = len(self.memory.examples[label])
        min_examples = min(examples_per_class.values())
        max_examples = max(examples_per_class.values())
        num_classes = len(examples_per_class)
        target_samples_per_class = max(5, min(10, min_examples * 2))
        if num_classes > 20:
            for label, examples in self.memory.examples.items():
                if label in new_classes:
                    num_samples = min(len(examples), target_samples_per_class * 2)
                else:
                    num_samples = min(len(examples), target_samples_per_class)
                if num_samples <= len(examples):
                    indices = np.random.choice(len(examples), size=num_samples, replace=False)
                else:
                    indices = np.random.choice(len(examples), size=num_samples, replace=True)
                for idx in indices:
                    example = examples[idx]
                    all_embeddings.append(example.embedding)
                    all_labels.append(self.label_to_id[label])
        else:
            sampling_weights = {}
            for label, count in examples_per_class.items():
                if label in new_classes:
                    sampling_weights[label] = 2.0
                else:
                    sampling_weights[label] = min_examples / count
            for label, examples in self.memory.examples.items():
                weight = sampling_weights[label]
                num_samples = max(min_examples, int(len(examples) * weight))
                indices = np.random.choice(len(examples), size=num_samples, replace=num_samples > len(examples))
                for idx in indices:
                    example = examples[idx]
                    all_embeddings.append(example.embedding)
                    all_labels.append(self.label_to_id[label])
        all_embeddings = torch.stack(all_embeddings)
        all_labels = torch.tensor(all_labels)
        dataset = torch.utils.data.TensorDataset(all_embeddings, all_labels)
        ewc = None
        if old_head is not None:
            old_embeddings = []
            old_labels = []
            old_label_to_id = {label: idx for idx, label in enumerate(self.id_to_label.values()) if label not in new_classes}
            for label, examples in self.memory.examples.items():
                if label not in new_classes:
                    for example in examples[:5]:
                        old_embeddings.append(example.embedding)
                        old_labels.append(old_label_to_id[label])
            if old_embeddings:
                old_embeddings = torch.stack(old_embeddings)
                old_labels = torch.tensor(old_labels, dtype=torch.long)
                old_dataset = torch.utils.data.TensorDataset(old_embeddings, old_labels)
                ewc = EWC(old_head, old_dataset, device=self.device, ewc_lambda=5.0)
        self.adaptive_head.train()
        criterion = nn.CrossEntropyLoss()
        optimizer = torch.optim.AdamW(self.adaptive_head.parameters(), lr=0.001, weight_decay=0.01)
        loader = torch.utils.data.DataLoader(dataset, batch_size=32, shuffle=True, generator=torch.Generator().manual_seed(42))
        best_loss = float('inf')
        patience = 3
        patience_counter = 0
        for epoch in range(15):
            total_loss = 0
            for batch_embeddings, batch_labels in loader:
                batch_embeddings = batch_embeddings.to(self.device)
                batch_labels = batch_labels.to(self.device)
                optimizer.zero_grad()
                outputs = self.adaptive_head(batch_embeddings)
                task_loss = criterion(outputs, batch_labels)
                if ewc is not None:
                    ewc_loss = ewc.ewc_loss(batch_size=len(batch_embeddings))
                    loss = task_loss + ewc_loss
                else:
                    loss = task_loss
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.adaptive_head.parameters(), max_norm=1.0)
                optimizer.step()
                total_loss += loss.item()
            avg_loss = total_loss / len(loader)
            if avg_loss < best_loss:
                best_loss = avg_loss
                patience_counter = 0
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    logger.debug(f'Early stopping at epoch {epoch + 1}')
                    break
        self.train_steps += 1

    def _perform_strategic_training(self):
        """Perform strategic training on current examples."""
        if not self.strategic_mode or not self.memory.examples:
            return
        all_embeddings = []
        all_labels = []
        for label in self.memory.examples:
            for example in self.memory.examples[label]:
                all_embeddings.append(example.embedding)
                all_labels.append(self.label_to_id[label])
        if all_embeddings:
            all_embeddings = torch.stack(all_embeddings)
            all_labels = torch.tensor(all_labels, dtype=torch.long, device=self.device)
            self._strategic_training_step(all_embeddings, all_labels)
            logger.debug('Performed strategic training step')

    def predict(self, text: str, k: int=5) -> List[Tuple[str, float]]:
        """Predict with dual prediction system - blends strategic and regular predictions.
        
        If no cost function is provided, uses existing prediction logic (zero changes).
        If cost function is provided, blends strategic and regular predictions.
        
        Args:
            text: Input text to classify
            k: Number of top predictions to return
            
        Returns:
            List of (label, confidence) tuples
        """
        if not text:
            raise ValueError('Empty input text')
        if not self.strategic_mode:
            return self._predict_regular(text, k)
        return self._predict_dual(text, k)

    def _predict_regular(self, text: str, k: int=5) -> List[Tuple[str, float]]:
        """Regular prediction logic (original implementation)."""
        with torch.no_grad():
            embedding = self._get_embeddings([text])[0]
            max_classes = len(self.id_to_label) if self.id_to_label else k
            proto_preds = self.memory.get_nearest_prototypes(embedding, k=max_classes)
            if self.adaptive_head is not None:
                self.adaptive_head.eval()
                input_embedding = embedding.unsqueeze(0).to(self.device)
                logits = self.adaptive_head(input_embedding)
                logits = logits.squeeze(0)
                probs = F.softmax(logits, dim=0)
                values, indices = torch.topk(probs, len(self.id_to_label))
                head_preds = [(self.id_to_label[idx.item()], val.item()) for val, idx in zip(values, indices)]
            else:
                head_preds = []
        combined_scores = {}
        for label, score in proto_preds:
            trained_examples = self.training_history.get(label, 0)
            if trained_examples < 10:
                weight = 0.3
            else:
                weight = 0.7
            combined_scores[label] = score * weight
        for label, score in head_preds:
            trained_examples = self.training_history.get(label, 0)
            if trained_examples < 10:
                weight = 0.7
            else:
                weight = 0.3
            combined_scores[label] = combined_scores.get(label, 0) + score * weight
        predictions = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
        total = sum((score for _, score in predictions))
        if total > 0:
            predictions = [(label, score / total) for label, score in predictions]
        return predictions[:k]

    def _predict_dual(self, text: str, k: int=5) -> List[Tuple[str, float]]:
        """Dual prediction system that blends strategic and regular predictions."""
        regular_preds = self._predict_regular(text, k)
        strategic_preds = self.predict_strategic(text, k)
        blended_scores = {}
        regular_weight = self.config.strategic_blend_regular_weight
        strategic_weight = self.config.strategic_blend_strategic_weight
        for label, score in regular_preds:
            blended_scores[label] = score * regular_weight
        for label, score in strategic_preds:
            blended_scores[label] = blended_scores.get(label, 0) + score * strategic_weight
        blended_predictions = sorted(blended_scores.items(), key=lambda x: x[1], reverse=True)
        total = sum((score for _, score in blended_predictions))
        if total > 0:
            blended_predictions = [(label, score / total) for label, score in blended_predictions]
        logger.debug(f'Dual prediction - Regular: {regular_preds[:3]}, Strategic: {strategic_preds[:3]}, Blended: {blended_predictions[:3]}')
        return blended_predictions[:k]

    def _save_pretrained(self, save_directory: Union[str, Path], config: Optional[Dict[str, Any]]=None, include_onnx: bool=True, quantize_onnx: bool=True, **kwargs) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Save the model to a directory.

        Args:
            save_directory: Directory to save the model to
            config: Optional additional configuration
            include_onnx: Whether to include ONNX export (default: True)
            quantize_onnx: Whether to quantize ONNX model (requires include_onnx=True)
            **kwargs: Additional arguments passed to save_pretrained

        Returns:
            Tuple of (dict of filenames, dict of objects to save)
        """
        save_directory = Path(save_directory)
        os.makedirs(save_directory, exist_ok=True)
        config_dict = {'model_name': self.model.config._name_or_path, 'embedding_dim': self.embedding_dim, 'label_to_id': self.label_to_id, 'id_to_label': {str(k): v for k, v in self.id_to_label.items()}, 'train_steps': self.train_steps, 'training_history': self.training_history, 'config': self.config.to_dict(), 'library_name': 'adaptive-classifier'}
        saved_examples = {}
        for label, examples in self.memory.examples.items():
            saved_examples[label] = [ex.to_dict() for ex in self.select_representative_examples(examples, k=self.config.num_representative_examples)]
        tensor_dict = {}
        for label, proto in self.memory.prototypes.items():
            tensor_dict[f'prototype_{label}'] = proto
        if self.adaptive_head is not None:
            for name, param in self.adaptive_head.state_dict().items():
                tensor_dict[f'adaptive_head_{name}'] = param
        config_file = save_directory / 'config.json'
        examples_file = save_directory / 'examples.json'
        tensors_file = save_directory / 'model.safetensors'
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2, sort_keys=True)
        with open(examples_file, 'w', encoding='utf-8') as f:
            json.dump(saved_examples, f, indent=2, sort_keys=True)
        save_file(tensor_dict, tensors_file)
        model_card_path = save_directory / 'README.md'
        if not model_card_path.exists():
            model_card_content = self._generate_model_card()
            with open(model_card_path, 'w', encoding='utf-8') as f:
                f.write(model_card_content)
        if include_onnx:
            try:
                onnx_dir = save_directory / 'onnx'
                self.export_onnx(onnx_dir, quantize=quantize_onnx)
                logger.info(f'ONNX model exported to {onnx_dir}')
            except ImportError:
                logger.warning('Skipping ONNX export: optimum[onnxruntime] not installed. Install with: pip install optimum[onnxruntime]')
            except Exception as e:
                logger.warning(f'Skipping ONNX export due to error: {e}')
        saved_files = {'config': config_file.name, 'examples': examples_file.name, 'model': tensors_file.name, 'model_card': model_card_path.name}
        if include_onnx and (save_directory / 'onnx').exists():
            saved_files['onnx'] = 'onnx/'
        return (saved_files, {})

    @classmethod
    def _from_pretrained(cls, model_id: str, revision: Optional[str]=None, cache_dir: Optional[str]=None, force_download: bool=False, proxies: Optional[Dict]=None, resume_download: bool=False, local_files_only: bool=False, token: Optional[Union[str, bool]]=None, use_onnx: Optional[Union[bool, str]]='auto', prefer_quantized: bool=True, trust_remote_code: bool=False, **kwargs) -> 'AdaptiveClassifier':
        """Load a model from the HuggingFace Hub or local directory.

        Args:
            model_id: HuggingFace Hub model ID or path to local directory
            revision: Revision of the model on the Hub
            cache_dir: Cache directory for downloaded models
            force_download: Force download of models
            proxies: Proxies to use for downloading
            resume_download: Resume downloading if interrupted
            local_files_only: Use local files only, don't download
            token: Authentication token for Hub
            use_onnx: Whether to use ONNX Runtime ("auto", True, False)
            prefer_quantized: Use quantized ONNX model if available (default: True)
                             Set to False to use unquantized model for maximum accuracy
            trust_remote_code: Whether to trust remote code when loading models (default: False)
            **kwargs: Additional arguments passed to from_pretrained

        Returns:
            Loaded AdaptiveClassifier instance

        Examples:
            >>> # Load with quantized ONNX (default - faster, smaller)
            >>> classifier = AdaptiveClassifier.load("adaptive-classifier/llm-router")
            >>>
            >>> # Load with unquantized ONNX (maximum accuracy)
            >>> classifier = AdaptiveClassifier.load("adaptive-classifier/llm-router", prefer_quantized=False)
            >>>
            >>> # Force PyTorch (no ONNX)
            >>> classifier = AdaptiveClassifier.load("adaptive-classifier/llm-router", use_onnx=False)
            >>>
            >>> # Load model requiring custom code
            >>> classifier = AdaptiveClassifier.load("model-with-custom-code", trust_remote_code=True)
        """
        model_path = Path(model_id)
        try:
            if model_path.is_dir() and (model_path / 'config.json').exists():
                pass
            else:
                config_file = hf_hub_download(repo_id=model_id, filename='config.json', revision=revision, cache_dir=cache_dir, force_download=force_download, proxies=proxies, resume_download=resume_download, token=token, local_files_only=local_files_only)
                model_path = Path(os.path.dirname(config_file))
                hf_hub_download(repo_id=model_id, filename='examples.json', revision=revision, cache_dir=cache_dir, force_download=force_download, proxies=proxies, resume_download=resume_download, token=token, local_files_only=local_files_only)
                hf_hub_download(repo_id=model_id, filename='model.safetensors', revision=revision, cache_dir=cache_dir, force_download=force_download, proxies=proxies, resume_download=resume_download, token=token, local_files_only=local_files_only)
                try:
                    hf_hub_download(repo_id=model_id, filename='onnx/model_quantized.onnx', revision=revision, cache_dir=cache_dir, force_download=force_download, proxies=proxies, resume_download=resume_download, token=token, local_files_only=local_files_only)
                    for onnx_file in ['config.json', 'ort_config.json', 'tokenizer.json', 'tokenizer_config.json', 'special_tokens_map.json', 'vocab.txt']:
                        try:
                            hf_hub_download(repo_id=model_id, filename=f'onnx/{onnx_file}', revision=revision, cache_dir=cache_dir, force_download=force_download, proxies=proxies, resume_download=resume_download, token=token, local_files_only=local_files_only)
                        except:
                            pass
                    logger.info('Downloaded ONNX model files from Hub')
                except Exception as e:
                    logger.debug(f'ONNX model not available on Hub: {e}')
        except Exception as e:
            raise ValueError(f'Error loading model from {model_id}: {e}')
        with open(model_path / 'config.json', 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
        with open(model_path / 'examples.json', 'r', encoding='utf-8') as f:
            saved_examples = json.load(f)
        onnx_path = model_path / 'onnx'
        has_onnx = onnx_path.exists() and ((onnx_path / 'model_quantized.onnx').exists() or (onnx_path / 'model.onnx').exists())
        final_use_onnx = use_onnx
        if use_onnx == 'auto':
            device = kwargs.get('device', None) or ('cuda' if torch.cuda.is_available() else 'cpu')
            final_use_onnx = has_onnx and device == 'cpu'
        elif use_onnx is True and (not has_onnx):
            logger.warning('ONNX model requested but not found in save directory. Loading PyTorch model instead.')
            final_use_onnx = False
        device = kwargs.get('device', None)
        if final_use_onnx and has_onnx:
            from optimum.onnxruntime import ORTModelForFeatureExtraction
            logger.info(f'Loading ONNX model from {onnx_path}')
            classifier = cls.__new__(cls)
            torch.manual_seed(42)
            classifier.config = ModelConfig(config_dict.get('config', None))
            classifier.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
            classifier.use_onnx = True
            has_quantized = (onnx_path / 'model_quantized.onnx').exists()
            has_unquantized = (onnx_path / 'model.onnx').exists()
            if prefer_quantized and has_quantized:
                onnx_file = 'model_quantized.onnx'
                logger.info('Loading quantized ONNX model for optimal performance')
            elif has_unquantized:
                onnx_file = 'model.onnx'
                logger.info('Loading unquantized ONNX model')
            elif has_quantized:
                onnx_file = 'model_quantized.onnx'
                logger.info('Loading quantized ONNX model (only version available)')
            else:
                raise ValueError(f'No ONNX model files found in {onnx_path}')
            classifier.model = ORTModelForFeatureExtraction.from_pretrained(onnx_path, file_name=onnx_file, trust_remote_code=trust_remote_code)
            classifier.tokenizer = AutoTokenizer.from_pretrained(config_dict['model_name'], trust_remote_code=trust_remote_code)
            classifier.embedding_dim = classifier.model.config.hidden_size
            classifier.memory = PrototypeMemory(classifier.embedding_dim, config=classifier.config)
            classifier.adaptive_head = None
            classifier.label_to_id = {}
            classifier.id_to_label = {}
            classifier.train_steps = 0
            classifier.training_history = {}
            classifier.strategic_cost_function = None
            classifier.strategic_optimizer = None
            classifier.strategic_evaluator = None
            if not hasattr(classifier, 'default_threshold'):
                classifier.default_threshold = 0.5
            if not hasattr(classifier, 'min_predictions'):
                classifier.min_predictions = 1
            if not hasattr(classifier, 'max_predictions'):
                classifier.max_predictions = None
            if not hasattr(classifier, 'label_thresholds'):
                classifier.label_thresholds = {}
            if classifier.config.enable_strategic_mode:
                classifier._initialize_strategic_components()
        else:
            classifier = cls(config_dict['model_name'], device=device, config=config_dict.get('config', None), use_onnx=final_use_onnx if isinstance(final_use_onnx, bool) else False, trust_remote_code=trust_remote_code)
        classifier.label_to_id = config_dict['label_to_id']
        classifier.id_to_label = {int(k): v for k, v in config_dict['id_to_label'].items()}
        classifier.train_steps = config_dict['train_steps']
        classifier.training_history = config_dict.get('training_history', {})
        tensors = load_file(model_path / 'model.safetensors')
        for label, examples_data in saved_examples.items():
            classifier.memory.examples[label] = [Example.from_dict(ex_data) for ex_data in examples_data]
        for label in classifier.label_to_id.keys():
            prototype_key = f'prototype_{label}'
            if prototype_key in tensors:
                prototype = tensors[prototype_key]
                classifier.memory.prototypes[label] = prototype
        classifier.memory._restore_from_save()
        adaptive_head_params = {k.replace('adaptive_head_', ''): v for k, v in tensors.items() if k.startswith('adaptive_head_')}
        if adaptive_head_params:
            classifier._initialize_adaptive_head()
            classifier.adaptive_head.load_state_dict(adaptive_head_params)
        if not classifier.training_history:
            for label, examples in saved_examples.items():
                classifier.training_history[label] = len(examples) * 20
        return classifier

    def _generate_model_card(self) -> str:
        """Generate a model card for the classifier.
        
        Returns:
            Model card content as string
        """
        stats = self.get_memory_stats()
        model_card = f'---\nlanguage: multilingual\ntags:\n- adaptive-classifier\n- text-classification\n- continuous-learning\nlicense: apache-2.0\n---\n\n# Adaptive Classifier\n\nThis model is an instance of an [adaptive-classifier](https://github.com/codelion/adaptive-classifier) that allows for continuous learning and dynamic class addition.\n\n## Installation\n\n**IMPORTANT:** To use this model, you must first install the `adaptive-classifier` library. You do **NOT** need `trust_remote_code=True`.\n\n```bash\npip install adaptive-classifier\n```\n\n## Model Details\n\n- Base Model: {self.model.config._name_or_path}\n- Number of Classes: {stats['num_classes']}\n- Total Examples: {stats['total_examples']}\n- Embedding Dimension: {self.embedding_dim}\n\n## Class Distribution\n\n```\n{self._format_class_distribution(stats)}\n```\n\n## Usage\n\nAfter installing the `adaptive-classifier` library, you can load and use this model:\n\n```python\nfrom adaptive_classifier import AdaptiveClassifier\n\n# Load the model (no trust_remote_code needed!)\nclassifier = AdaptiveClassifier.from_pretrained("adaptive-classifier/model-name")\n\n# Make predictions\ntext = "Your text here"\npredictions = classifier.predict(text)\nprint(predictions)  # List of (label, confidence) tuples\n\n# Add new examples for continuous learning\ntexts = ["Example 1", "Example 2"]\nlabels = ["class1", "class2"]\nclassifier.add_examples(texts, labels)\n```\n\n**Note:** This model uses the `adaptive-classifier` library distributed via PyPI. You do **NOT** need to set `trust_remote_code=True` - just install the library first.\n\n## Training Details\n\n- Training Steps: {self.train_steps}\n- Examples per Class: See distribution above\n- Prototype Memory: Active\n- Neural Adaptation: {('Active' if self.adaptive_head is not None else 'Inactive')}\n\n## Limitations\n\nThis model:\n- Requires at least {self.config.min_examples_per_class} examples per class\n- Has a maximum of {self.config.max_examples_per_class} examples per class\n- Updates prototypes every {self.config.prototype_update_frequency} examples\n\n## Citation\n\n```bibtex\n@software{{adaptive_classifier,\n  title = {{Adaptive Classifier: Dynamic Text Classification with Continuous Learning}},\n  author = {{Sharma, Asankhaya}},\n  year = {{2025}},\n  publisher = {{GitHub}},\n  url = {{https://github.com/codelion/adaptive-classifier}}\n}}\n```\n'
        return model_card

    def _format_class_distribution(self, stats: Dict[str, Any]) -> str:
        """Format class distribution for model card.
        
        Args:
            stats: Statistics from get_memory_stats()
            
        Returns:
            Formatted string of class distribution
        """
        if 'examples_per_class' not in stats:
            return 'No examples stored'
        lines = []
        total = sum(stats['examples_per_class'].values())
        for label, count in sorted(stats['examples_per_class'].items()):
            percentage = count / total * 100 if total > 0 else 0
            lines.append(f'{label}: {count} examples ({percentage:.1f}%)')
        return '\n'.join(lines)

    def export_onnx(self, save_directory: Union[str, Path], quantize: bool=False, quantization_config: Optional[str]='arm64') -> Path:
        """Export the transformer model to ONNX format.

        Args:
            save_directory: Directory to save ONNX model
            quantize: Whether to apply INT8 quantization
            quantization_config: Quantization configuration ("arm64", "avx512", "avx2")

        Returns:
            Path to the saved ONNX model directory

        Raises:
            ImportError: If optimum[onnxruntime] is not installed
            ValueError: If model is already in ONNX format
        """
        try:
            from optimum.onnxruntime import ORTModelForFeatureExtraction, ORTQuantizer
            from optimum.onnxruntime.configuration import AutoQuantizationConfig
        except ImportError:
            raise ImportError('optimum[onnxruntime] is required for ONNX export. Install with: pip install optimum[onnxruntime]')
        save_directory = Path(save_directory)
        save_directory.mkdir(parents=True, exist_ok=True)
        if self.use_onnx:
            logger.warning('Model is already in ONNX format. Saving current model.')
            self.model.save_pretrained(save_directory)
            return save_directory
        model_name = self.model.config._name_or_path
        logger.info(f'Exporting {model_name} to ONNX format...')
        ort_model = ORTModelForFeatureExtraction.from_pretrained(model_name, export=True)
        ort_model.save_pretrained(save_directory)
        logger.info(f'Saved unquantized ONNX model to {save_directory}')
        if quantize:
            logger.info(f'Applying {quantization_config} INT8 quantization...')
            if quantization_config == 'arm64':
                qconfig = AutoQuantizationConfig.arm64(is_static=False, per_channel=False)
            elif quantization_config == 'avx512':
                qconfig = AutoQuantizationConfig.avx512(is_static=False, per_channel=False)
            elif quantization_config == 'avx2':
                qconfig = AutoQuantizationConfig.avx2(is_static=False, per_channel=False)
            else:
                logger.warning(f'Unknown quantization config: {quantization_config}. Using arm64.')
                qconfig = AutoQuantizationConfig.arm64(is_static=False, per_channel=False)
            quantizer = ORTQuantizer.from_pretrained(ort_model)
            quantizer.quantize(save_dir=save_directory, quantization_config=qconfig)
            logger.info(f'Saved quantized ONNX model to {save_directory}')
        logger.info(f'ONNX model exported to {save_directory}')
        return save_directory

    def push_to_hub(self, repo_id: str, include_onnx: bool=True, quantize_onnx: bool=True, token: Optional[str]=None, commit_message: Optional[str]=None, private: bool=False, **kwargs):
        """Push model to HuggingFace Hub with ONNX export by default.

        Args:
            repo_id: Repository ID on HuggingFace Hub (e.g., "username/model-name")
            include_onnx: Whether to include ONNX version of the model (default: True)
            quantize_onnx: Whether to quantize the ONNX model (requires include_onnx=True)
            token: HuggingFace Hub authentication token (or set HF_TOKEN env var)
            commit_message: Commit message for the push
            private: Whether to create a private repository
            **kwargs: Additional arguments passed to HfApi.upload_folder

        Examples:
            >>> classifier.push_to_hub("my-org/my-classifier")  # ONNX included by default
            >>> classifier.push_to_hub("my-org/my-classifier", quantize_onnx=True)
            >>> classifier.push_to_hub("my-org/my-classifier", include_onnx=False)  # Opt-out
        """
        import tempfile
        import os
        from huggingface_hub import HfApi
        token = token or os.environ.get('HF_TOKEN')
        if not token:
            logger.warning('No HuggingFace token provided. Set HF_TOKEN environment variable or pass token parameter. You may need to login with `huggingface-cli login`')
        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = Path(tmpdir)
            self._save_pretrained(save_path, include_onnx=include_onnx, quantize_onnx=quantize_onnx)
            api = HfApi()
            try:
                api.create_repo(repo_id=repo_id, token=token, private=private, exist_ok=True)
            except Exception as e:
                logger.warning(f'Could not create repo (may already exist): {e}')
            commit_info = api.upload_folder(folder_path=str(save_path), repo_id=repo_id, token=token, commit_message=commit_message or 'Upload model with adaptive-classifier', **kwargs)
            logger.info(f'Successfully pushed model to https://huggingface.co/{repo_id}')
            return f'https://huggingface.co/{repo_id}'

    def save(self, save_dir: str, include_onnx: bool=True, quantize_onnx: bool=True):
        """Legacy save method for backwards compatibility.

        Args:
            save_dir: Directory to save to
            include_onnx: Whether to include ONNX export (default: True)
            quantize_onnx: Whether to quantize ONNX model
        """
        return self._save_pretrained(save_dir, include_onnx=include_onnx, quantize_onnx=quantize_onnx)

    @classmethod
    def load(cls, save_dir: str, device: Optional[str]=None, use_onnx: Optional[Union[bool, str]]='auto', prefer_quantized: bool=True, trust_remote_code: bool=False) -> 'AdaptiveClassifier':
        """Legacy load method for backwards compatibility.

        Args:
            save_dir: Directory to load from
            device: Device to load model on
            use_onnx: Whether to use ONNX Runtime ("auto", True, False)
            prefer_quantized: Use quantized ONNX model if available (default: True)
            trust_remote_code: Whether to trust remote code when loading models (default: False)
        """
        kwargs = {}
        if device is not None:
            kwargs['device'] = device
        return cls._from_pretrained(save_dir, use_onnx=use_onnx, prefer_quantized=prefer_quantized, trust_remote_code=trust_remote_code, **kwargs)

    def to(self, device: str) -> 'AdaptiveClassifier':
        """Move the model to specified device.
        
        Args:
            device: Device to move to ("cuda" or "cpu")
            
        Returns:
            Self for chaining
        """
        self.device = device
        self.model = self.model.to(device)
        if self.adaptive_head is not None:
            self.adaptive_head = self.adaptive_head.to(device)
        return self

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics.
        
        Returns:
            Dictionary of memory statistics
        """
        return self.memory.get_stats()

    def _initialize_adaptive_head(self):
        """Initialize or reinitialize the adaptive head with improved configuration."""
        num_classes = len(self.label_to_id)
        hidden_dims = [self.embedding_dim, self.embedding_dim // 2]
        self.adaptive_head = AdaptiveHead(self.embedding_dim, num_classes, hidden_dims=hidden_dims).to(self.device)

    def _get_embeddings(self, texts: List[str]) -> List[torch.Tensor]:
        """Get embeddings for input texts."""
        was_training = False
        if not self.use_onnx and hasattr(self.model, 'training'):
            was_training = self.model.training
            self.model.eval()
        with torch.no_grad():
            inputs = self.tokenizer(texts, max_length=self.config.max_length, truncation=True, padding=True, return_tensors='pt')
            if not self.use_onnx:
                inputs = inputs.to(self.device)
            outputs = self.model(**inputs)
            embeddings = outputs.last_hidden_state[:, 0, :]
            embeddings = F.normalize(embeddings, p=2, dim=1)
        if was_training and hasattr(self.model, 'train'):
            self.model.train()
        return [emb.cpu() for emb in embeddings]

    def get_example_statistics(self) -> Dict[str, Any]:
        """Get statistics about stored examples and model state."""
        stats = {'total_examples': sum((len(exs) for exs in self.memory.examples.values())), 'examples_per_class': {label: len(exs) for label, exs in self.memory.examples.items()}, 'num_classes': len(self.label_to_id), 'train_steps': self.train_steps, 'memory_usage': {'prototypes': sum((p.nelement() * p.element_size() for p in self.memory.prototypes.values())), 'examples': sum((sum((ex.embedding.nelement() * ex.embedding.element_size() for ex in exs)) for exs in self.memory.examples.values()))}}
        if self.adaptive_head is not None:
            stats['model_params'] = sum((p.nelement() for p in self.adaptive_head.parameters()))
        return stats

    def predict_batch(self, texts: List[str], k: int=5, batch_size: int=32) -> List[List[Tuple[str, float]]]:
        """Predict labels for a batch of texts with improved batching."""
        if not texts:
            raise ValueError('Empty input batch')
        all_predictions = []
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_embeddings = self._get_embeddings(batch_texts)
            batch_predictions = []
            for embedding in batch_embeddings:
                proto_preds = self.memory.get_nearest_prototypes(embedding, k=k)
                if self.adaptive_head is not None:
                    self.adaptive_head.eval()
                    with torch.no_grad():
                        input_embedding = embedding.unsqueeze(0).to(self.device)
                        logits = self.adaptive_head(input_embedding)
                        logits = logits.squeeze(0)
                        probs = F.softmax(logits, dim=0)
                        values, indices = torch.topk(probs, min(k, len(self.id_to_label)))
                        head_preds = [(self.id_to_label[idx.item()], val.item()) for val, idx in zip(values, indices)]
                else:
                    head_preds = []
                combined_scores = {}
                proto_weight = 0.7
                head_weight = 0.3
                for label, score in proto_preds:
                    combined_scores[label] = score * proto_weight
                for label, score in head_preds:
                    combined_scores[label] = combined_scores.get(label, 0) + score * head_weight
                predictions = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
                total = sum((score for _, score in predictions))
                if total > 0:
                    predictions = [(label, score / total) for label, score in predictions]
                batch_predictions.append(predictions[:k])
            all_predictions.extend(batch_predictions)
        return all_predictions

    def clear_memory(self, labels: Optional[List[str]]=None):
        """Clear memory for specified labels or all if none specified."""
        if labels is None:
            self.memory.clear()
        else:
            for label in labels:
                if label in self.memory.examples:
                    del self.memory.examples[label]
                if label in self.memory.prototypes:
                    del self.memory.prototypes[label]
            self.memory._rebuild_index()

    def merge_classifiers(self, other: 'AdaptiveClassifier') -> 'AdaptiveClassifier':
        """Merge another classifier into this one."""
        if self.embedding_dim != other.embedding_dim:
            raise ValueError('Classifiers have different embedding dimensions')
        next_idx = max(self.id_to_label.keys()) + 1
        for label in other.label_to_id:
            if label not in self.label_to_id:
                self.label_to_id[label] = next_idx
                self.id_to_label[next_idx] = label
                next_idx += 1
        for label, examples in other.memory.examples.items():
            for example in examples:
                self.memory.add_example(example, label)
        if self.adaptive_head is not None:
            self._initialize_adaptive_head()
            self._train_adaptive_head()
        return self

    def _train_adaptive_head(self, epochs: int=10):
        """Train the adaptive head with improved stability."""
        if not self.memory.examples:
            return
        all_embeddings = []
        all_labels = []
        for label in sorted(self.memory.examples.keys()):
            examples = sorted(self.memory.examples[label], key=lambda x: x.text)
            for example in examples:
                all_embeddings.append(example.embedding)
                all_labels.append(self.label_to_id[example.label])
        all_embeddings = torch.stack(all_embeddings)
        all_labels = torch.tensor(all_labels, dtype=torch.long, device=self.device)
        all_embeddings = F.normalize(all_embeddings, p=2, dim=1)
        dataset = torch.utils.data.TensorDataset(all_embeddings, all_labels)
        loader = torch.utils.data.DataLoader(dataset, batch_size=min(32, len(all_embeddings)), shuffle=True, generator=torch.Generator().manual_seed(42))
        self.adaptive_head.train()
        criterion = nn.CrossEntropyLoss()
        optimizer = torch.optim.AdamW(self.adaptive_head.parameters(), lr=0.001, weight_decay=0.01, betas=(0.9, 0.999))
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=2)
        best_loss = float('inf')
        patience_counter = 0
        patience = 3
        for epoch in range(epochs):
            total_loss = 0
            for batch_embeddings, batch_labels in loader:
                batch_embeddings = batch_embeddings.to(self.device)
                batch_labels = batch_labels.to(self.device)
                optimizer.zero_grad()
                outputs = self.adaptive_head(batch_embeddings)
                if epoch == 0 and total_loss == 0:
                    logger.debug(f'outputs shape: {outputs.shape}')
                    logger.debug(f'batch_labels shape: {batch_labels.shape}')
                    logger.debug(f'batch_labels content: {batch_labels}')
                loss = criterion(outputs, batch_labels)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.adaptive_head.parameters(), max_norm=1.0)
                optimizer.step()
                total_loss += loss.item()
            avg_loss = total_loss / len(loader)
            scheduler.step(avg_loss)
            if avg_loss < best_loss:
                best_loss = avg_loss
                patience_counter = 0
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    logger.debug(f'Early stopping at epoch {epoch + 1}')
                    break
        self.train_steps += 1

    def _update_adaptive_head(self):
        """Update adaptive head for new classes."""
        num_classes = len(self.label_to_id)
        if self.adaptive_head is None:
            self._initialize_adaptive_head()
        elif num_classes > self.adaptive_head.model[-1].out_features:
            self.adaptive_head.update_num_classes(num_classes)

    def select_representative_examples(self, examples: List[Example], k: int=5) -> List[Example]:
        """Select k most representative examples using k-means clustering.
        
        Args:
            examples: List of examples to select from
            k: Number of examples to select
            
        Returns:
            List of selected examples
        """
        if len(examples) <= k:
            return examples
        embeddings = torch.stack([ex.embedding for ex in examples])
        embeddings = F.normalize(embeddings, p=2, dim=1)
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(embeddings.numpy())
        selected_indices = []
        centroids = torch.tensor(kmeans.cluster_centers_)
        for centroid in centroids:
            distances = torch.norm(embeddings - centroid, dim=1)
            closest_idx = torch.argmin(distances).item()
            selected_indices.append(closest_idx)
        return [examples[idx] for idx in selected_indices]

    def _initialize_strategic_components(self):
        """Initialize strategic classification components."""
        try:
            if self.config.cost_coefficients:
                self.strategic_cost_function = CostFunctionFactory.create_cost_function(cost_type=self.config.cost_function_type, cost_coefficients=self.config.cost_coefficients)
                self.strategic_optimizer = StrategicOptimizer(self.strategic_cost_function)
                self.strategic_evaluator = StrategicEvaluator(self.strategic_cost_function)
                logger.info(f'Initialized strategic mode with {self.config.cost_function_type} cost function')
            else:
                logger.warning('Strategic mode enabled but no cost coefficients provided')
        except Exception as e:
            logger.error(f'Failed to initialize strategic components: {e}')
            self.config.enable_strategic_mode = False

    @property
    def strategic_mode(self) -> bool:
        """Check if strategic mode is enabled and properly initialized."""
        return self.config.enable_strategic_mode and self.strategic_cost_function is not None

    def _strategic_training_step(self, all_embeddings: torch.Tensor, all_labels: torch.Tensor):
        """Perform strategic training step."""
        if not self.strategic_mode or self.adaptive_head is None:
            return
        self.adaptive_head.train()
        optimizer = torch.optim.AdamW(self.adaptive_head.parameters(), lr=self.config.learning_rate * 0.5, weight_decay=0.01)
        dataset = torch.utils.data.TensorDataset(all_embeddings, all_labels)
        loader = torch.utils.data.DataLoader(dataset, batch_size=min(16, len(all_embeddings)), shuffle=True, generator=torch.Generator().manual_seed(42))
        for epoch in range(5):
            for batch_embeddings, batch_labels in loader:
                batch_embeddings = batch_embeddings.to(self.device)
                batch_labels = batch_labels.to(self.device)
                optimizer.zero_grad()
                strategic_loss = self.strategic_optimizer.strategic_loss(self.adaptive_head, batch_embeddings, batch_labels, self.config.strategic_lambda)
                strategic_loss.backward()
                torch.nn.utils.clip_grad_norm_(self.adaptive_head.parameters(), max_norm=1.0)
                optimizer.step()
        logger.debug('Completed strategic training step')

    def predict_strategic(self, text: str, k: int=5) -> List[Tuple[str, float]]:
        """Predict assuming the input might be strategically modified.
        
        This method simulates how a strategic agent might modify the input
        to get a better classification outcome, then predicts on that modified input.
        
        Args:
            text: Input text to classify
            k: Number of top predictions to return
            
        Returns:
            List of (label, confidence) tuples for strategic predictions
        """
        if not self.strategic_mode:
            return self._predict_regular(text, k)
        try:
            embedding = self._get_embeddings([text])[0]

            def classifier_func(x):
                with torch.no_grad():
                    if self.adaptive_head is not None:
                        self.adaptive_head.eval()
                        if x.dim() == 1:
                            x = x.unsqueeze(0)
                        logits = self.adaptive_head(x.to(self.device))
                        return F.softmax(logits, dim=-1)
                    else:
                        num_classes = len(self.label_to_id) if self.label_to_id else 1
                        return torch.ones(1, num_classes) / num_classes
            strategic_embedding = self.strategic_cost_function.compute_best_response(embedding, classifier_func)
            return self._predict_from_embedding(strategic_embedding, k, strategic=True)
        except Exception as e:
            logger.warning(f'Strategic prediction failed: {e}. Falling back to regular prediction.')
            return self._predict_regular(text, k)

    def predict_robust(self, text: str, k: int=5) -> List[Tuple[str, float]]:
        """Predict assuming input has already been strategically modified.
        
        This method assumes the input text has already been strategically manipulated
        and applies robust prediction techniques that are less susceptible to such manipulation.
        
        Args:
            text: Input text (potentially strategically modified)
            k: Number of top predictions to return
            
        Returns:
            List of (label, confidence) tuples for robust predictions
        """
        if not self.strategic_mode:
            return self._predict_regular(text, k)
        try:
            embedding = self._get_embeddings([text])[0]
            return self._predict_from_embedding(embedding, k, robust=True)
        except Exception as e:
            logger.warning(f'Robust prediction failed: {e}. Falling back to regular prediction.')
            return self._predict_regular(text, k)

    def _predict_from_embedding(self, embedding: torch.Tensor, k: int=5, robust: bool=False, strategic: bool=False) -> List[Tuple[str, float]]:
        """Helper method to predict from embedding with strategic considerations.
        
        Args:
            embedding: Input embedding tensor
            k: Number of top predictions to return
            robust: If True, applies robust prediction weights
            strategic: If True, indicates this is for strategic prediction
            
        Returns:
            List of (label, confidence) tuples
        """
        with torch.no_grad():
            proto_preds = self.memory.get_nearest_prototypes(embedding, k=k)
            if self.adaptive_head is not None:
                self.adaptive_head.eval()
                input_embedding = embedding.unsqueeze(0).to(self.device)
                logits = self.adaptive_head(input_embedding)
                logits = logits.squeeze(0)
                probs = F.softmax(logits, dim=0)
                values, indices = torch.topk(probs, min(k, len(self.id_to_label)))
                head_preds = [(self.id_to_label[idx.item()], val.item()) for val, idx in zip(values, indices)]
            else:
                head_preds = []
        combined_scores = {}
        if self.strategic_mode and robust:
            proto_weight = self.config.strategic_robust_proto_weight
            head_weight = self.config.strategic_robust_head_weight
        elif self.strategic_mode and strategic:
            proto_weight = self.config.strategic_prediction_proto_weight
            head_weight = self.config.strategic_prediction_head_weight
        else:
            proto_weight = self.config.prototype_weight
            head_weight = self.config.neural_weight
        for label, score in proto_preds:
            combined_scores[label] = score * proto_weight
        for label, score in head_preds:
            combined_scores[label] = combined_scores.get(label, 0) + score * head_weight
        predictions = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
        total = sum((score for _, score in predictions))
        if total > 0:
            predictions = [(label, score / total) for label, score in predictions]
        return predictions[:k]

    def evaluate_strategic_robustness(self, test_texts: List[str], test_labels: List[str], gaming_levels: List[float]=[0.0, 0.5, 1.0]) -> Dict[str, float]:
        """Evaluate strategic robustness of the classifier."""
        if not self.strategic_mode:
            raise ValueError('Strategic mode not enabled')
        test_embeddings = torch.stack(self._get_embeddings(test_texts))
        test_label_indices = torch.tensor([self.label_to_id[label] for label in test_labels])
        return self.strategic_evaluator.evaluate_robustness(self.adaptive_head, test_embeddings, test_label_indices, gaming_levels)

def _save_pretrained(self, save_directory: Union[str, Path], config: Optional[Dict[str, Any]]=None, include_onnx: bool=True, quantize_onnx: bool=True, **kwargs) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Save the model to a directory.

        Args:
            save_directory: Directory to save the model to
            config: Optional additional configuration
            include_onnx: Whether to include ONNX export (default: True)
            quantize_onnx: Whether to quantize ONNX model (requires include_onnx=True)
            **kwargs: Additional arguments passed to save_pretrained

        Returns:
            Tuple of (dict of filenames, dict of objects to save)
        """
    save_directory = Path(save_directory)
    os.makedirs(save_directory, exist_ok=True)
    config_dict = {'model_name': self.model.config._name_or_path, 'embedding_dim': self.embedding_dim, 'label_to_id': self.label_to_id, 'id_to_label': {str(k): v for k, v in self.id_to_label.items()}, 'train_steps': self.train_steps, 'training_history': self.training_history, 'config': self.config.to_dict(), 'library_name': 'adaptive-classifier'}
    saved_examples = {}
    for label, examples in self.memory.examples.items():
        saved_examples[label] = [ex.to_dict() for ex in self.select_representative_examples(examples, k=self.config.num_representative_examples)]
    tensor_dict = {}
    for label, proto in self.memory.prototypes.items():
        tensor_dict[f'prototype_{label}'] = proto
    if self.adaptive_head is not None:
        for name, param in self.adaptive_head.state_dict().items():
            tensor_dict[f'adaptive_head_{name}'] = param
    config_file = save_directory / 'config.json'
    examples_file = save_directory / 'examples.json'
    tensors_file = save_directory / 'model.safetensors'
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config_dict, f, indent=2, sort_keys=True)
    with open(examples_file, 'w', encoding='utf-8') as f:
        json.dump(saved_examples, f, indent=2, sort_keys=True)
    save_file(tensor_dict, tensors_file)
    model_card_path = save_directory / 'README.md'
    if not model_card_path.exists():
        model_card_content = self._generate_model_card()
        with open(model_card_path, 'w', encoding='utf-8') as f:
            f.write(model_card_content)
    if include_onnx:
        try:
            onnx_dir = save_directory / 'onnx'
            self.export_onnx(onnx_dir, quantize=quantize_onnx)
            logger.info(f'ONNX model exported to {onnx_dir}')
        except ImportError:
            logger.warning('Skipping ONNX export: optimum[onnxruntime] not installed. Install with: pip install optimum[onnxruntime]')
        except Exception as e:
            logger.warning(f'Skipping ONNX export due to error: {e}')
    saved_files = {'config': config_file.name, 'examples': examples_file.name, 'model': tensors_file.name, 'model_card': model_card_path.name}
    if include_onnx and (save_directory / 'onnx').exists():
        saved_files['onnx'] = 'onnx/'
    return (saved_files, {})

def main():
    """Main function to run all demonstrations."""
    print('Multi-Label Adaptive Classifier Example')
    print("Fixing the 'No labels met the threshold criteria' issue\n")
    try:
        classifier = demonstrate_basic_usage()
        demonstrate_predictions(classifier)
        demonstrate_threshold_adjustment(classifier)
        loaded_classifier = demonstrate_saving_loading(classifier)
        demonstrate_incremental_learning(loaded_classifier)
        print('\n' + '=' * 60)
        print('EXAMPLE COMPLETED SUCCESSFULLY')
        print('=' * 60)
        final_stats = loaded_classifier.get_label_statistics()
        print(f'\nFinal Model Statistics:')
        print(f'- Labels: {final_stats['num_classes']}')
        print(f'- Examples: {final_stats['total_examples']}')
        print(f'- Default threshold: {final_stats['default_threshold']}')
        print(f'- Adaptive threshold: {final_stats['adaptive_threshold']:.3f}')
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

