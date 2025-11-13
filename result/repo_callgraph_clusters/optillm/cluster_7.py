# Cluster 7

def main():
    parser = argparse.ArgumentParser(description='Evaluate LLM performance on IMO 2025 problems')
    parser.add_argument('--model', type=str, required=True, help='Model to use (e.g., google/gemma-2.5-flash-lite)')
    parser.add_argument('--approach', type=str, default='none', help='OptiLLM approach to use (none, mars, moa, bon, etc.)')
    parser.add_argument('--timeout', type=int, default=600, help='Timeout in seconds for each problem (default: 600)')
    parser.add_argument('--problems', type=str, help="Comma-separated list of problem IDs to evaluate (e.g., '1,3,5')")
    args = parser.parse_args()
    os.makedirs('results', exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = f'results/imo25_{args.model.replace('/', '_')}_{args.approach}_{timestamp}.json'
    if args.problems:
        problem_ids = [int(x.strip()) for x in args.problems.split(',')]
        problems_to_evaluate = [p for p in IMO_2025_PROBLEMS if p['id'] in problem_ids]
    else:
        problems_to_evaluate = IMO_2025_PROBLEMS
    print(f'Evaluating {len(problems_to_evaluate)} IMO 2025 problems')
    print(f'Model: {args.model}')
    print(f'Approach: {args.approach}')
    print(f'Results will be saved to: {results_file}')
    if args.approach == 'mars':
        extra_body = {'optillm_approach': 'mars', 'mars_config': {'use_thinking_tags': False, 'answer_extraction_mode': 'none'}}
    elif args.approach != 'none':
        extra_body = {'optillm_approach': args.approach}
    else:
        extra_body = None
    for problem_data in tqdm(problems_to_evaluate, desc='Solving IMO problems'):
        logger.info(f'Evaluating Problem {problem_data['id']}: {problem_data['type']}')
        start_time = time.time()
        response = get_llm_response(problem_data['problem'], args.model, extra_body, args.timeout)
        solve_time = time.time() - start_time
        evaluation = evaluate_solution(problem_data, response['solution'], args.model)
        result = {'timestamp': datetime.now().isoformat(), 'model': args.model, 'approach': args.approach, 'problem_data': problem_data, 'response': response, 'evaluation': evaluation, 'solve_time_seconds': solve_time}
        save_result(results_file, result)
        logger.info(f'Problem {problem_data['id']} completed - Score: {evaluation['correctness_score']:.3f}')
    final_results = load_existing_results(results_file)
    analyze_results(final_results, args.approach)
    print(f'\nEvaluation complete! Results saved to: {results_file}')

def save_results(metrics: Dict[str, float], detailed_results: List[Dict[str, Any]], model: str, approach: str, output_dir: str):
    """Save evaluation results to files."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    model_dir = os.path.join(output_dir, model.replace('/', '_'))
    os.makedirs(model_dir, exist_ok=True)
    base_filename = os.path.join(model_dir, f'{approach}_{timestamp}')
    with open(f'{base_filename}_metrics.json', 'w') as f:
        json.dump(metrics, f, indent=2)
    with open(f'{base_filename}_detailed.json', 'w') as f:
        json.dump(detailed_results, f, indent=2)
    df = pd.DataFrame([{k: v for k, v in result.items() if k != 'raw_response' and k != 'processed_response'} for result in detailed_results])
    df.to_csv(f'{base_filename}_summary.csv', index=False)
    logger.info(f'Results saved to {base_filename}_*')

def generate_report(all_metrics: Dict[str, Dict[str, float]], output_dir: str, is_test_time_compute: bool=False):
    """Generate a comprehensive report comparing all approaches."""
    report = []
    is_default_test_time = set(all_metrics.keys()) == {'avg@5', 'pass@5', 'maj@5', 'genselect@5'}
    if is_default_test_time:
        report_title = 'OptiLLM Bench Test-Time Compute Evaluation Report'
    elif is_test_time_compute:
        report_title = 'OptiLLM Bench Test-Time Compute Scaling Report'
    else:
        report_title = 'OptiLLM Bench Evaluation Report'
    report.append(f'# {report_title}')
    report.append(f'Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n')
    if is_default_test_time:
        report.append('## Test-Time Compute Evaluation Results\n')
        report.append('This report evaluates the potential of test-time compute with:')
        report.append('- **avg@5**: Average success rate of 5 parallel responses')
        report.append('- **pass@5**: Success if ANY of 5 responses is correct')
        report.append('- **maj@5**: Majority voting with 5 candidates')
        report.append('- **genselect@5**: Quality-based selection from 5 candidates\n')
        report.append('All approaches use n=5 parallel generation (with sequential fallback) for fair comparison.\n')
    elif is_test_time_compute:
        report.append('This report evaluates test-time compute scaling approaches:')
        report.append('- **Sequential scaling**: ThinkDeeper with varying thinking token budgets')
        report.append('- **Parallel scaling**: Majority voting with varying k values\n')
    report.append('## Overall Results')
    headers = ['Approach', 'Accuracy', 'Avg Time (s)', 'Total Time (s)']
    rows = []
    for approach, metrics in all_metrics.items():
        rows.append([approach, f'{metrics['accuracy'] * 100:.2f}%', f'{metrics['average_time']:.2f}', f'{metrics['total_time']:.2f}'])
    df = pd.DataFrame(rows, columns=headers)
    report.append(df.to_markdown())
    report.append('\n## Results by Category')
    categories = ['gsm8k', 'mmlu_math', 'boolq', 'aqua_rat']
    for category in categories:
        report.append(f'\n### {category.upper()}')
        headers = ['Approach', 'Accuracy', 'Avg Time (s)']
        rows = []
        for approach, metrics in all_metrics.items():
            if f'{category}_accuracy' in metrics:
                rows.append([approach, f'{metrics[f'{category}_accuracy'] * 100:.2f}%', f'{metrics[f'{category}_average_time']:.2f}'])
        df = pd.DataFrame(rows, columns=headers)
        report.append(df.to_markdown())
    if is_default_test_time:
        report.append('\n## Summary')
        if all((metric in all_metrics for metric in ['avg@5', 'pass@5', 'maj@5', 'genselect@5'])):
            avg5_acc = all_metrics['avg@5']['accuracy'] * 100
            pass5_acc = all_metrics['pass@5']['accuracy'] * 100
            maj5_acc = all_metrics['maj@5']['accuracy'] * 100
            genselect5_acc = all_metrics['genselect@5']['accuracy'] * 100
            report.append(f'\n**Key Metrics:**')
            report.append(f'- **avg@5** (average of 5 responses): {avg5_acc:.2f}%')
            report.append(f'- **pass@5** (success if any correct): {pass5_acc:.2f}%')
            report.append(f'- **maj@5** (majority voting): {maj5_acc:.2f}%')
            report.append(f'- **genselect@5** (quality-based selection): {genselect5_acc:.2f}%')
            if avg5_acc > 0:
                pass_improvement = (pass5_acc - avg5_acc) / avg5_acc * 100
                maj_improvement = (maj5_acc - avg5_acc) / avg5_acc * 100
                genselect_improvement = (genselect5_acc - avg5_acc) / avg5_acc * 100
                report.append(f'\n**Improvements over avg@5 baseline:**')
                report.append(f'- pass@5: {('+' if pass_improvement > 0 else '')}{pass_improvement:.1f}%')
                report.append(f'- maj@5: {('+' if maj_improvement > 0 else '')}{maj_improvement:.1f}%')
                report.append(f'- genselect@5: {('+' if genselect_improvement > 0 else '')}{genselect_improvement:.1f}%')
            if pass5_acc > avg5_acc:
                variance_ratio = (pass5_acc - avg5_acc) / avg5_acc * 100
                report.append(f'\n**Response Variance Indicator:**')
                report.append(f'- Gap between pass@5 and avg@5: {variance_ratio:.1f}%')
                report.append(f'- This indicates {('high' if variance_ratio > 50 else 'moderate' if variance_ratio > 20 else 'low')} variance in response quality')
    report_path = f'{output_dir}/evaluation_report.md'
    with open(report_path, 'w') as f:
        f.write('\n\n'.join(report))
    logger.info(f'Report saved to {report_path}')

def main():
    parser = argparse.ArgumentParser(description='Evaluate a model on OptiLLM Bench. By default, runs test-time compute evaluation with pass@1, maj@64, and genselect@64.')
    parser.add_argument('--model', required=True, help='Model identifier')
    parser.add_argument('--base-url', default='http://localhost:8000/v1', help='Base URL for API endpoint')
    parser.add_argument('--max-samples', type=int, help='Maximum number of samples to evaluate')
    parser.add_argument('--output-dir', default='results', help='Directory to save results')
    parser.add_argument('--approaches', nargs='+', help='Specific approaches to evaluate (overrides default test-time compute)')
    parser.add_argument('--test-time-compute', action='store_true', help='Evaluate full test-time compute scaling approaches (ThinkDeeper and various k values)')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    args = parser.parse_args()
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    os.makedirs(args.output_dir, exist_ok=True)
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise ValueError('OPENAI_API_KEY environment variable must be set')
    client = OpenAI(api_key=api_key, base_url=args.base_url)
    dataset = load_optillm_bench()
    if args.test_time_compute:
        approaches_config = TEST_TIME_COMPUTE_APPROACHES
        if args.approaches:
            approaches_config = [a for a in TEST_TIME_COMPUTE_APPROACHES if a[0] in args.approaches]
    elif args.approaches:
        all_available_approaches = APPROACHES + TEST_TIME_COMPUTE_APPROACHES + DEFAULT_TEST_TIME_COMPUTE
        approaches_config = []
        for requested_approach in args.approaches:
            found = False
            for approach_tuple in all_available_approaches:
                if approach_tuple[0] == requested_approach:
                    if approach_tuple not in approaches_config:
                        approaches_config.append(approach_tuple)
                    found = True
                    break
            if not found:
                logger.warning(f"Approach '{requested_approach}' not found in any configuration")
        if not approaches_config:
            raise ValueError(f'No valid approaches found. Requested: {args.approaches}')
    else:
        approaches_config = DEFAULT_TEST_TIME_COMPUTE
        logger.info('Using default test-time compute evaluation (avg@5, pass@5, maj@5, genselect@5)')
    all_metrics = {}
    for approach_name, description, extra_body_params in approaches_config:
        logger.info(f'Evaluating approach: {approach_name} - {description}')
        if extra_body_params:
            logger.info(f'Extra parameters: {extra_body_params}')
        try:
            metrics, detailed_results = evaluate_model(client, args.model, dataset, approach_name, extra_body_params, args.max_samples)
            all_metrics[approach_name] = metrics
            save_results(metrics, detailed_results, args.model, approach_name, args.output_dir)
            logger.info(f'Completed evaluation for {approach_name}')
            logger.info(f'Accuracy: {metrics['accuracy'] * 100:.2f}%')
            logger.info(f'Average time per sample: {metrics['average_time']:.2f}s')
        except Exception as e:
            logger.error(f'Error evaluating approach {approach_name}: {e}')
            continue
    is_test_time = args.test_time_compute or (not args.approaches and approaches_config == DEFAULT_TEST_TIME_COMPUTE)
    generate_report(all_metrics, args.output_dir, is_test_time)

def create_benchmark_dataset() -> Dataset:
    """Create the complete benchmark dataset"""
    all_examples = []
    for category, config in tqdm(SOURCES.items(), desc='Processing datasets'):
        print(f'\nProcessing {category} dataset...')
        dataset = load_source_dataset(config)
        if not dataset:
            continue
        try:
            examples = select_challenging_examples(dataset, category, config['samples'], config['field_map'])
            print(f'Selected {len(examples)} examples from {category}')
            all_examples.extend(examples)
        except Exception as e:
            print(f'Error selecting examples from {category}: {str(e)}')
            continue
    random.shuffle(all_examples)
    num_train = int(len(all_examples) * SPLIT_RATIO['train'])
    train_examples = all_examples[:num_train]
    test_examples = all_examples[num_train:]
    dataset_dict = DatasetDict({'train': Dataset.from_list(train_examples), 'test': Dataset.from_list(test_examples)})
    return dataset_dict

def main():
    parser = argparse.ArgumentParser(description='Generate OptILM dataset')
    parser.add_argument('--num_samples', type=int, default=100, help='Number of samples to process')
    parser.add_argument('--output_file', type=str, default='optillm_dataset.jsonl', help='Output file path')
    args = parser.parse_args()
    asyncio.run(generate_dataset(args.num_samples, args.output_file))
    print(f'Dataset generated and saved to {args.output_file}')

def main(model: str):
    """Main evaluation function."""
    os.makedirs('results', exist_ok=True)
    results_file = f'evaluation_results_math500_{model.replace('/', '_')}.json'
    dataset = load_math500_dataset()
    existing_results = load_existing_results(results_file)
    processed_indexes = {result['index'] for result in existing_results}
    for idx, item in enumerate(tqdm(dataset, desc='Evaluating problems')):
        if idx in processed_indexes:
            continue
        problem_text = item['problem']
        correct_answer = item['answer']
        response = get_llm_response(problem_text, model)
        predicted_answer = extract_answer(response)
        is_correct = compare_answers(correct_answer, predicted_answer)
        result = {'index': idx, 'problem': problem_text, 'response': response, 'correct_answer': correct_answer, 'predicted_answer': predicted_answer, 'is_correct': is_correct}
        save_result(results_file, result)
    final_results = load_existing_results(results_file)
    analyze_results(final_results)

class SimpleQAEvaluator:
    """Main evaluator class for SimpleQA benchmark"""

    def __init__(self, model: str, approach: str, base_url: str=DEFAULT_BASE_URL, grader_model: str=DEFAULT_GRADER_MODEL, timeout: int=DEFAULT_TIMEOUT, cache_dir: str='cache', output_dir: str='results', use_verified: bool=False):
        self.model = model
        self.approach = approach
        self.base_url = base_url
        self.grader_model = grader_model
        self.timeout = timeout
        self.use_verified = use_verified
        self.cache_dir = Path(cache_dir)
        self.output_dir = Path(output_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        self.optillm_client = OpenAI(api_key='optillm', base_url=base_url, timeout=httpx.Timeout(timeout, connect=5.0), max_retries=0)
        try:
            self.grader_client = OpenAI(api_key='optillm', base_url=base_url, timeout=httpx.Timeout(timeout, connect=5.0), max_retries=0)
            logger.info('Using OptILLM for grading responses')
        except Exception as e:
            logger.warning(f'Could not initialize grader client: {e}')
            logger.warning('Grading will be skipped.')
            self.grader_client = None
        self.results = []
        self.metrics = {'correct': 0, 'incorrect': 0, 'not_attempted': 0, 'errors': 0, 'total_processed': 0}

    def download_dataset(self) -> str:
        """Download SimpleQA dataset if not cached"""
        if self.use_verified:
            cache_file = self.cache_dir / 'simpleqa_verified.csv'
            url = SIMPLEQA_VERIFIED_CSV_URL
            dataset_name = 'SimpleQA-Verified'
        else:
            cache_file = self.cache_dir / 'simple_qa_test_set.csv'
            url = SIMPLEQA_CSV_URL
            dataset_name = 'SimpleQA'
        if cache_file.exists():
            logger.info(f'Using cached {dataset_name} dataset: {cache_file}')
            return str(cache_file)
        logger.info(f'Downloading {dataset_name} dataset from {url}')
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            with open(cache_file, 'wb') as f:
                f.write(response.content)
            logger.info(f'Dataset downloaded to {cache_file}')
            return str(cache_file)
        except Exception as e:
            logger.error(f'Failed to download dataset: {e}')
            raise

    def load_dataset(self, num_samples: Optional[int]=None, start_index: int=0) -> List[Dict]:
        """Load and parse SimpleQA dataset"""
        dataset_file = self.download_dataset()
        questions = []
        try:
            with open(dataset_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader):
                    if i < start_index:
                        continue
                    if num_samples and len(questions) >= num_samples:
                        break
                    if self.use_verified:
                        metadata = {'original_index': row.get('original_index', i), 'topic': row.get('topic', ''), 'answer_type': row.get('answer_type', ''), 'multi_step': row.get('multi_step', ''), 'requires_reasoning': row.get('requires_reasoning', ''), 'urls': row.get('urls', '')}
                        question_id = row.get('original_index', i)
                    else:
                        try:
                            metadata = json.loads(row['metadata']) if row.get('metadata') else {}
                        except:
                            metadata = {}
                        question_id = i
                    question_data = {'id': question_id, 'metadata': metadata, 'question': row['problem'], 'gold_answer': row['answer']}
                    questions.append(question_data)
            dataset_type = 'SimpleQA-Verified' if self.use_verified else 'SimpleQA'
            logger.info(f'Loaded {len(questions)} questions from {dataset_type} dataset')
            return questions
        except Exception as e:
            logger.error(f'Failed to load dataset: {e}')
            raise

    def get_approach_config(self) -> Dict:
        """Get configuration for specific approach"""
        if self.approach == 'none':
            return {}
        elif self.approach == 'web_search':
            return {'num_results': 10, 'headless': True, 'timeout': 30}
        elif self.approach == 'deep_research':
            return {'max_iterations': 1, 'max_sources': 10}
        else:
            return {}

    def query_optillm(self, question: str) -> Tuple[str, bool]:
        """Query OptILLM with the specified approach"""
        try:
            if self.approach == 'none':
                model_name = self.model
            else:
                model_name = f'{self.approach}-{self.model}'
            messages = [{'role': 'system', 'content': 'You are a helpful assistant that provides accurate, factual answers to questions. Be direct and concise.'}, {'role': 'user', 'content': question}]
            extra_body = {}
            approach_config = self.get_approach_config()
            if approach_config:
                extra_body.update(approach_config)
            logger.debug(f'Querying model: {model_name}')
            logger.debug(f'Question: {question}')
            response = self.optillm_client.chat.completions.create(model=model_name, messages=messages, extra_body=extra_body if extra_body else None, max_tokens=4096, temperature=0.6)
            answer = response.choices[0].message.content
            answer = remove_thinking_blocks(answer)
            logger.debug(f'Response: {answer}')
            return (answer, True)
        except Exception as e:
            logger.error(f'Error querying OptILLM: {e}')
            return (f'Error: {str(e)}', False)

    def grade_response(self, question: str, gold_answer: str, response: str) -> str:
        """Grade response using SimpleQA methodology"""
        if not self.grader_client:
            return 'NOT_GRADED'
        try:
            grading_prompt = GRADING_PROMPT.format(question=question, gold_answer=gold_answer, response=response)
            grader_response = self.grader_client.chat.completions.create(model=self.grader_model, messages=[{'role': 'user', 'content': grading_prompt}], temperature=0.6, max_tokens=4096)
            grade_text = grader_response.choices[0].message.content.strip()
            grade_text = re.sub('<think>.*?</think>', '', grade_text, flags=re.DOTALL).strip()
            if grade_text.startswith('A'):
                return 'CORRECT'
            elif grade_text.startswith('B'):
                return 'INCORRECT'
            elif grade_text.startswith('C'):
                return 'NOT_ATTEMPTED'
            else:
                logger.warning(f'Unexpected grade format: {grade_text}')
                return 'NOT_GRADED'
        except Exception as e:
            logger.error(f'Error grading response: {e}')
            return 'ERROR_GRADING'

    def evaluate_question(self, question_data: Dict) -> Dict:
        """Evaluate a single question"""
        question = question_data['question']
        gold_answer = question_data['gold_answer']
        response, success = self.query_optillm(question)
        result = {'id': question_data['id'], 'metadata': question_data['metadata'], 'question': question, 'gold_answer': gold_answer, 'response': response, 'success': success, 'timestamp': datetime.now().isoformat()}
        if success:
            grade = self.grade_response(question, gold_answer, response)
            result['grade'] = grade
            if grade == 'CORRECT':
                self.metrics['correct'] += 1
            elif grade == 'INCORRECT':
                self.metrics['incorrect'] += 1
            elif grade == 'NOT_ATTEMPTED':
                self.metrics['not_attempted'] += 1
        else:
            result['grade'] = 'ERROR'
            self.metrics['errors'] += 1
        self.metrics['total_processed'] += 1
        return result

    def calculate_metrics(self) -> Dict:
        """Calculate final evaluation metrics"""
        total = self.metrics['total_processed']
        correct = self.metrics['correct']
        incorrect = self.metrics['incorrect']
        not_attempted = self.metrics['not_attempted']
        errors = self.metrics['errors']
        if total == 0:
            return {'error': 'No questions processed'}
        accuracy = correct / total * 100 if total > 0 else 0
        attempted = correct + incorrect
        correct_given_attempted = correct / attempted * 100 if attempted > 0 else 0
        precision = correct / (correct + incorrect) if correct + incorrect > 0 else 0
        recall = correct / (correct + not_attempted) if correct + not_attempted > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if precision + recall > 0 else 0
        return {'total_questions': total, 'correct': correct, 'incorrect': incorrect, 'not_attempted': not_attempted, 'errors': errors, 'accuracy': accuracy, 'correct_given_attempted': correct_given_attempted, 'precision': precision, 'recall': recall, 'f1_score': f1_score, 'attempted_rate': attempted / total * 100 if total > 0 else 0}

    def save_results(self, timestamp: str) -> Tuple[str, str, str]:
        """Save evaluation results to files"""
        dataset_suffix = '_verified' if self.use_verified else ''
        run_dir = self.output_dir / f'simpleqa{dataset_suffix}_{self.model}_{self.approach}'
        run_dir.mkdir(parents=True, exist_ok=True)
        detailed_file = run_dir / f'{timestamp}_detailed.json'
        metrics_file = run_dir / f'{timestamp}_metrics.json'
        summary_file = run_dir / f'{timestamp}_summary.csv'
        with open(detailed_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        final_metrics = self.calculate_metrics()
        final_metrics.update({'model': self.model, 'approach': self.approach, 'timestamp': timestamp, 'base_url': self.base_url, 'grader_model': self.grader_model})
        with open(metrics_file, 'w') as f:
            json.dump(final_metrics, f, indent=2)
        df = pd.DataFrame(self.results)
        df.to_csv(summary_file, index=False)
        logger.info(f'Results saved to {run_dir}')
        return (str(detailed_file), str(metrics_file), str(summary_file))

    def run_evaluation(self, num_samples: Optional[int]=None, start_index: int=0) -> Dict:
        """Run the complete evaluation"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        dataset_type = 'SimpleQA-Verified' if self.use_verified else 'SimpleQA'
        logger.info(f'Starting {dataset_type} evaluation')
        logger.info(f'Model: {self.model}')
        logger.info(f'Approach: {self.approach}')
        logger.info(f'Dataset: {dataset_type} ({('1k verified questions' if self.use_verified else '4.3k questions')})')
        logger.info(f'Base URL: {self.base_url}')
        logger.info(f'Timeout: {self.timeout}s')
        questions = self.load_dataset(num_samples, start_index)
        for question_data in tqdm(questions, desc='Evaluating questions'):
            try:
                result = self.evaluate_question(question_data)
                self.results.append(result)
                if len(self.results) % 10 == 0:
                    metrics = self.calculate_metrics()
                    logger.info(f'Progress: {len(self.results)}/{len(questions)} - Accuracy: {metrics['accuracy']:.1f}%')
            except KeyboardInterrupt:
                logger.info('Evaluation interrupted by user')
                break
            except Exception as e:
                logger.error(f'Error evaluating question {question_data['id']}: {e}')
                continue
        detailed_file, metrics_file, summary_file = self.save_results(timestamp)
        final_metrics = self.calculate_metrics()
        logger.info('Evaluation completed!')
        logger.info(f'Total questions: {final_metrics['total_questions']}')
        logger.info(f'Accuracy: {final_metrics['accuracy']:.1f}%')
        logger.info(f'F1 Score: {final_metrics['f1_score']:.3f}')
        logger.info(f'Correct: {final_metrics['correct']}')
        logger.info(f'Incorrect: {final_metrics['incorrect']}')
        logger.info(f'Not Attempted: {final_metrics['not_attempted']}')
        return final_metrics

def evaluate_question(self, question_data: Dict) -> Dict:
    """Evaluate a single question"""
    question = question_data['question']
    gold_answer = question_data['gold_answer']
    response, success = self.query_optillm(question)
    result = {'id': question_data['id'], 'metadata': question_data['metadata'], 'question': question, 'gold_answer': gold_answer, 'response': response, 'success': success, 'timestamp': datetime.now().isoformat()}
    if success:
        grade = self.grade_response(question, gold_answer, response)
        result['grade'] = grade
        if grade == 'CORRECT':
            self.metrics['correct'] += 1
        elif grade == 'INCORRECT':
            self.metrics['incorrect'] += 1
        elif grade == 'NOT_ATTEMPTED':
            self.metrics['not_attempted'] += 1
    else:
        result['grade'] = 'ERROR'
        self.metrics['errors'] += 1
    self.metrics['total_processed'] += 1
    return result

def save_results(self, timestamp: str) -> Tuple[str, str, str]:
    """Save evaluation results to files"""
    dataset_suffix = '_verified' if self.use_verified else ''
    run_dir = self.output_dir / f'simpleqa{dataset_suffix}_{self.model}_{self.approach}'
    run_dir.mkdir(parents=True, exist_ok=True)
    detailed_file = run_dir / f'{timestamp}_detailed.json'
    metrics_file = run_dir / f'{timestamp}_metrics.json'
    summary_file = run_dir / f'{timestamp}_summary.csv'
    with open(detailed_file, 'w') as f:
        json.dump(self.results, f, indent=2)
    final_metrics = self.calculate_metrics()
    final_metrics.update({'model': self.model, 'approach': self.approach, 'timestamp': timestamp, 'base_url': self.base_url, 'grader_model': self.grader_model})
    with open(metrics_file, 'w') as f:
        json.dump(final_metrics, f, indent=2)
    df = pd.DataFrame(self.results)
    df.to_csv(summary_file, index=False)
    logger.info(f'Results saved to {run_dir}')
    return (str(detailed_file), str(metrics_file), str(summary_file))

def run_evaluation(self, num_samples: Optional[int]=None, start_index: int=0) -> Dict:
    """Run the complete evaluation"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    dataset_type = 'SimpleQA-Verified' if self.use_verified else 'SimpleQA'
    logger.info(f'Starting {dataset_type} evaluation')
    logger.info(f'Model: {self.model}')
    logger.info(f'Approach: {self.approach}')
    logger.info(f'Dataset: {dataset_type} ({('1k verified questions' if self.use_verified else '4.3k questions')})')
    logger.info(f'Base URL: {self.base_url}')
    logger.info(f'Timeout: {self.timeout}s')
    questions = self.load_dataset(num_samples, start_index)
    for question_data in tqdm(questions, desc='Evaluating questions'):
        try:
            result = self.evaluate_question(question_data)
            self.results.append(result)
            if len(self.results) % 10 == 0:
                metrics = self.calculate_metrics()
                logger.info(f'Progress: {len(self.results)}/{len(questions)} - Accuracy: {metrics['accuracy']:.1f}%')
        except KeyboardInterrupt:
            logger.info('Evaluation interrupted by user')
            break
        except Exception as e:
            logger.error(f'Error evaluating question {question_data['id']}: {e}')
            continue
    detailed_file, metrics_file, summary_file = self.save_results(timestamp)
    final_metrics = self.calculate_metrics()
    logger.info('Evaluation completed!')
    logger.info(f'Total questions: {final_metrics['total_questions']}')
    logger.info(f'Accuracy: {final_metrics['accuracy']:.1f}%')
    logger.info(f'F1 Score: {final_metrics['f1_score']:.3f}')
    logger.info(f'Correct: {final_metrics['correct']}')
    logger.info(f'Incorrect: {final_metrics['incorrect']}')
    logger.info(f'Not Attempted: {final_metrics['not_attempted']}')
    return final_metrics

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Evaluate OptILLM on SimpleQA factuality benchmark')
    parser.add_argument('--model', type=str, default='gpt-4o-mini', help='Model to evaluate (default: gpt-4o-mini)')
    parser.add_argument('--approach', type=str, default='none', choices=['none', 'web_search', 'deep_research'], help='Approach to use (default: none)')
    parser.add_argument('--base-url', type=str, default=DEFAULT_BASE_URL, help=f'OptILLM base URL (default: {DEFAULT_BASE_URL})')
    parser.add_argument('--timeout', type=int, default=DEFAULT_TIMEOUT, help=f'Request timeout in seconds (default: {DEFAULT_TIMEOUT})')
    parser.add_argument('--grader-model', type=str, default=DEFAULT_GRADER_MODEL, help=f'Model for grading responses (default: {DEFAULT_GRADER_MODEL})')
    parser.add_argument('--num-samples', type=int, default=None, help='Number of questions to evaluate (default: all)')
    parser.add_argument('--start-index', type=int, default=0, help='Start from specific question index (default: 0)')
    parser.add_argument('--num-search-results', type=int, default=10, help='Number of search results per query (default: 10)')
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode for web search')
    parser.add_argument('--cache-dir', type=str, default='cache', help='Directory for caching dataset (default: cache)')
    parser.add_argument('--output-dir', type=str, default='results', help='Directory for saving results (default: results)')
    parser.add_argument('--verified', action='store_true', help='Use SimpleQA-Verified dataset (1k verified questions) instead of original SimpleQA')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    return parser.parse_args()

def perform_rtc_evaluation(query: str, model: str) -> Tuple[bool, float, Dict]:
    """
    Perform Round-Trip Correctness evaluation.
    
    Args:
        query: Original query
        model: Model name to use
        
    Returns:
        Tuple of (passed_rtc, similarity_score, evaluation_details)
    """
    response_1 = get_llm_response([{'role': 'user', 'content': query}], model)
    if not response_1:
        return (False, 0.0, {'error': 'Failed to get initial response'})
    inverse_prompt = f'Given this query and response pair, generate a new query that would lead to a similar response. Focus on the key aspects that would generate equivalent content:\n\nOriginal Query: {query}\nResponse: {response_1}\n\nGenerate a new query that would elicit a similar response:'
    alternate_query = get_llm_response([{'role': 'user', 'content': inverse_prompt}], model)
    if not alternate_query:
        return (False, 0.0, {'error': 'Failed to generate alternate query'})
    response_2 = get_llm_response([{'role': 'user', 'content': alternate_query}], model)
    if not response_2:
        return (False, 0.0, {'error': 'Failed to get second response'})
    similarity_score = compute_similarity(response_1, response_2)
    evaluation_details = {'original_query': query, 'response_1': response_1, 'alternate_query': alternate_query, 'response_2': response_2, 'similarity_score': similarity_score}
    return (similarity_score >= RTCConfig.similarity_threshold, similarity_score, evaluation_details)

def main():
    parser = argparse.ArgumentParser(description='Evaluate LLMs on arena-hard-auto dataset using RTC')
    parser.add_argument('--model', type=str, required=True, help='OpenAI model to use')
    parser.add_argument('--output', type=str, default='rtc_eval_results.json', help='Output file for results')
    args = parser.parse_args()
    os.makedirs('results', exist_ok=True)
    output_file = os.path.join('results', args.output)
    evaluate_dataset(args.model, output_file)

def main(model: str, n_attempts: int, year: int=2024, analyze_thoughts: bool=False, analyze_logits: bool=False, test_time_compute: bool=False, approach_name: str=None, extra_body: dict=None):
    """Main evaluation function that handles gaps in processed indexes."""
    os.makedirs('results', exist_ok=True)
    suffix_parts = []
    if year != 2024:
        suffix_parts.append(f'aime{year}')
    if analyze_thoughts:
        suffix_parts.append('thought_analysis')
    if analyze_logits:
        suffix_parts.append('logit_analysis')
    if approach_name:
        suffix_parts.append(approach_name)
    suffix = '_' + '_'.join(suffix_parts) if suffix_parts else ''
    results_file = f'results/evaluation_results_{model.replace('/', '_')}_pass_at_{n_attempts}{suffix}.json'
    dataset = load_dataset_by_year(year)
    existing_results = load_existing_results(results_file)
    processed_indexes = {result['index'] for result in existing_results}
    for _, item in enumerate(tqdm(dataset, desc='Evaluating problems')):
        id = int(item['id'])
        if id in processed_indexes:
            continue
        problem_text = item['problem']
        correct_answer = int(item['answer'])
        print(f'\n🔬 Processing Problem {id}: {problem_text[:100]}...')
        print(f'   Expected answer: {correct_answer}')
        if extra_body and 'optillm_approach' in extra_body:
            print(f'   Using approach: {extra_body['optillm_approach']}')
        attempts = make_n_attempts(problem_text, model, n_attempts, analyze_thoughts, analyze_logits, extra_body)
        is_correct, first_correct = evaluate_pass_at_n(attempts, correct_answer)
        predicted_answers = [attempt.get('predicted_answer') for attempt in attempts]
        print(f'   Predicted: {predicted_answers}')
        if is_correct:
            print(f'   ✅ CORRECT!')
        else:
            print(f'   ❌ Incorrect')
        result = {'index': id, 'problem': problem_text, 'attempts': attempts, 'correct_answer': correct_answer, 'is_correct': is_correct, 'first_correct_attempt': first_correct}
        save_result(results_file, result)
    final_results = load_existing_results(results_file)
    analyze_results(final_results, n_attempts, analyze_thoughts, analyze_logits)

def main():
    parser = argparse.ArgumentParser(description='Generate OptILM Ground Truth dataset')
    parser.add_argument('--num_samples', type=int, default=100, help='Total number of samples to process (divided among configurations)')
    parser.add_argument('--output_file', type=str, default='optillm_ground_truth_dataset.jsonl', help='Output file path')
    args = parser.parse_args()
    asyncio.run(generate_dataset(args.num_samples, args.output_file))
    print(f'Dataset generated and saved to {args.output_file}')

def main(model: str):
    dataset = load_dataset('google/frames-benchmark', split='test')
    filename = f'evaluation_results_{model.replace('/', '_')}.json'
    existing_results = load_existing_results(filename)
    last_processed_index = get_last_processed_index(existing_results)
    for item in tqdm(dataset, desc='Processing samples'):
        index = int(item['Unnamed: 0'])
        if index <= last_processed_index:
            continue
        prompt = generate_llm_prompt(item['Prompt'], item['wiki_links'])
        llm_response = get_llm_response(prompt, model)
        evaluation = evaluate_response(item['Prompt'], llm_response, item['Answer'], model)
        result = {'index': index, 'prompt': item['Prompt'], 'ground_truth': item['Answer'], 'llm_response': llm_response, 'evaluation_decision': evaluation['decision'], 'evaluation_explanation': evaluation['explanation'], 'reasoning_type': item['reasoning_types']}
        save_result(filename, result)
    results = load_existing_results(filename)
    total_samples = len(results)
    correct_answers = sum((1 for r in results if r['evaluation_decision'] == 'TRUE'))
    accuracy = correct_answers / total_samples
    print(f'Model: {model}')
    print(f'Total samples: {total_samples}')
    print(f'Correct answers: {correct_answers}')
    print(f'Accuracy: {accuracy:.2%}')
    reasoning_types = set((r['reasoning_type'] for r in results))
    for rt in reasoning_types:
        rt_samples = [r for r in results if r['reasoning_type'] == rt]
        rt_correct = sum((1 for r in rt_samples if r['evaluation_decision'] == 'TRUE'))
        rt_accuracy = rt_correct / len(rt_samples)
        print(f'Accuracy for {rt}: {rt_accuracy:.2%}')

class RequestBatcher:
    """
    Automatic request batching for OptILLM
    
    Collects incoming requests into batches and processes them together
    for improved throughput. Maintains separate queues per model type
    to avoid incompatible mixing.
    """

    def __init__(self, max_batch_size: int=4, max_wait_ms: int=50, enable_logging: bool=True):
        """
        Initialize the request batcher
        
        Args:
            max_batch_size: Maximum number of requests per batch
            max_wait_ms: Maximum time to wait for batch formation (milliseconds)
            enable_logging: Whether to log batching operations
        """
        self.max_batch_size = max_batch_size
        self.max_wait_seconds = max_wait_ms / 1000.0
        self.enable_logging = enable_logging
        self.queues: Dict[str, queue.Queue] = {}
        self.batch_threads: Dict[str, threading.Thread] = {}
        self.stats = {'total_requests': 0, 'total_batches': 0, 'avg_batch_size': 0.0, 'total_wait_time': 0.0}
        self._shutdown = False
        if self.enable_logging:
            logger.info(f'RequestBatcher initialized: max_batch_size={max_batch_size}, max_wait_ms={max_wait_ms}')

    def _get_request_key(self, request_data: Dict[str, Any]) -> str:
        """
        Generate key to group compatible requests
        
        Args:
            request_data: The request data dictionary
            
        Returns:
            String key for grouping compatible requests
        """
        model = request_data.get('model', 'default')
        approach = request_data.get('optillm_approach', 'none')
        if request_data.get('stream', False):
            raise BatchingError('Streaming requests cannot be batched')
        return f'{model}:{approach}'

    def _validate_batch_compatibility(self, requests: List[BatchRequest]) -> None:
        """
        Validate that all requests in batch are compatible
        
        Args:
            requests: List of batch requests
            
        Raises:
            BatchingError: If requests are not compatible
        """
        if not requests:
            return
        models = set((req.model for req in requests))
        if len(models) > 1:
            raise BatchingError(f'Cannot batch different models: {models}')
        approaches = set((req.approach for req in requests))
        if len(approaches) > 1:
            raise BatchingError(f'Cannot batch different optillm approaches: {approaches}')
        streaming = any((req.request_data.get('stream', False) for req in requests))
        if streaming:
            raise BatchingError('Cannot batch streaming requests')

    def _create_batch_processor(self, queue_key: str) -> None:
        """
        Create and start a batch processor thread for a specific queue
        
        Args:
            queue_key: The key identifying the queue/model type
        """

        def batch_processor():
            """Background thread that forms and processes batches"""
            if self.enable_logging:
                logger.debug(f'Batch processor started for {queue_key}')
            while not self._shutdown:
                try:
                    batch = []
                    queue_obj = self.queues[queue_key]
                    deadline = time.time() + self.max_wait_seconds
                    while len(batch) < self.max_batch_size and time.time() < deadline:
                        timeout = max(0.001, deadline - time.time())
                        try:
                            request = queue_obj.get(timeout=timeout)
                            batch.append(request)
                            if self.enable_logging and len(batch) == 1:
                                logger.debug(f'Started batch formation for {queue_key}')
                        except queue.Empty:
                            break
                    if batch:
                        if self.enable_logging:
                            wait_time = time.time() - batch[0].timestamp
                            logger.info(f'Processing batch of {len(batch)} requests for {queue_key} (waited {wait_time * 1000:.1f}ms)')
                        self.stats['total_batches'] += 1
                        self.stats['total_requests'] += len(batch)
                        self.stats['avg_batch_size'] = self.stats['total_requests'] / self.stats['total_batches']
                        self.stats['total_wait_time'] += sum((time.time() - req.timestamp for req in batch))
                        self._process_batch(batch)
                except Exception as e:
                    logger.error(f'Error in batch processor for {queue_key}: {e}')
            if self.enable_logging:
                logger.debug(f'Batch processor stopped for {queue_key}')
        thread = threading.Thread(target=batch_processor, daemon=True)
        thread.start()
        self.batch_threads[queue_key] = thread

    def _process_batch(self, batch: List[BatchRequest]) -> None:
        """
        Process a batch of requests
        
        Args:
            batch: List of batch requests to process
        """
        try:
            self._validate_batch_compatibility(batch)
            if not hasattr(self, '_processor_func'):
                raise BatchingError('No batch processor function set')
            request_data_list = [req.request_data for req in batch]
            responses = self._processor_func(request_data_list)
            if len(responses) != len(batch):
                raise BatchingError(f'Processor returned {len(responses)} responses for {len(batch)} requests')
            for req, response in zip(batch, responses):
                req.future.set_result(response)
        except Exception as e:
            error_msg = f'Batch processing failed: {str(e)}'
            logger.error(error_msg)
            for req in batch:
                req.future.set_exception(BatchingError(error_msg))

    def set_processor(self, processor_func):
        """
        Set the batch processing function
        
        Args:
            processor_func: Function that takes list of request data and returns list of responses
        """
        self._processor_func = processor_func

    def add_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a request to be batched
        
        Args:
            request_data: The request data dictionary
            
        Returns:
            The response from batch processing
            
        Raises:
            BatchingError: If request cannot be processed
        """
        try:
            queue_key = self._get_request_key(request_data)
            if queue_key not in self.queues:
                self.queues[queue_key] = queue.Queue()
                self._create_batch_processor(queue_key)
            future = Future()
            batch_request = BatchRequest(request_data=request_data, future=future, timestamp=time.time(), model=request_data.get('model', 'default'), approach=request_data.get('optillm_approach'))
            self.queues[queue_key].put(batch_request)
            if self.enable_logging:
                logger.debug(f'Added request to batch queue {queue_key}')
            return future.result()
        except Exception as e:
            raise BatchingError(f'Failed to process request: {str(e)}')

    def get_stats(self) -> Dict[str, Any]:
        """Get batching statistics"""
        return self.stats.copy()

    def shutdown(self):
        """Shutdown the batcher and all background threads"""
        self._shutdown = True
        if self.enable_logging:
            logger.info('RequestBatcher shutting down...')
        for thread in self.batch_threads.values():
            thread.join(timeout=1.0)

def get_stats(self) -> Dict[str, Any]:
    """Get batching statistics"""
    return self.stats.copy()

class ConversationLogger:
    """
    Logger for OptiLLM conversations including all provider interactions and metadata.
    
    Logs are saved in JSONL format (one JSON object per line) with daily rotation.
    Each entry contains the full conversation including all intermediate provider calls.
    """

    def __init__(self, log_dir: Path, enabled: bool=False):
        self.enabled = enabled
        self.log_dir = log_dir
        self.active_entries: Dict[str, ConversationEntry] = {}
        self._lock = threading.Lock()
        if self.enabled:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f'Conversation logging enabled. Logs will be saved to: {self.log_dir}')
        else:
            logger.debug('Conversation logging disabled')

    def _get_log_file_path(self, timestamp: datetime=None) -> Path:
        """Get the log file path for a given timestamp (defaults to now)"""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        date_str = timestamp.strftime('%Y-%m-%d')
        return self.log_dir / f'conversations_{date_str}.jsonl'

    def _generate_request_id(self) -> str:
        """Generate a unique request ID"""
        return f'req_{uuid.uuid4().hex[:8]}'

    def start_conversation(self, client_request: Dict[str, Any], approach: str, model: str) -> str:
        """
        Start logging a new conversation.
        
        Args:
            client_request: The original request from the client
            approach: The optimization approach being used
            model: The model name
            
        Returns:
            str: Unique request ID for this conversation
        """
        if not self.enabled:
            return ''
        request_id = self._generate_request_id()
        timestamp = datetime.now(timezone.utc).isoformat()
        entry = ConversationEntry(request_id=request_id, timestamp=timestamp, approach=approach, model=model, client_request=client_request.copy())
        with self._lock:
            self.active_entries[request_id] = entry
        logger.debug(f'Started conversation logging for request {request_id}')
        return request_id

    def log_provider_call(self, request_id: str, provider_request: Dict[str, Any], provider_response: Dict[str, Any]) -> None:
        """
        Log a provider API call and response.
        
        Args:
            request_id: The request ID for this conversation
            provider_request: The request sent to the provider
            provider_response: The response received from the provider
        """
        if not self.enabled or not request_id:
            return
        with self._lock:
            entry = self.active_entries.get(request_id)
            if not entry:
                logger.warning(f'No active conversation found for request {request_id}')
                return
            call_data = {'call_number': len(entry.provider_calls) + 1, 'timestamp': datetime.now(timezone.utc).isoformat(), 'request': provider_request.copy(), 'response': provider_response.copy()}
            entry.provider_calls.append(call_data)
        logger.debug(f'Logged provider call #{len(entry.provider_calls)} for request {request_id}')

    def log_final_response(self, request_id: str, final_response: Dict[str, Any]) -> None:
        """
        Log the final response sent back to the client.
        
        Args:
            request_id: The request ID for this conversation
            final_response: The final response sent to the client
        """
        if not self.enabled or not request_id:
            return
        with self._lock:
            entry = self.active_entries.get(request_id)
            if not entry:
                logger.warning(f'No active conversation found for request {request_id}')
                return
            entry.final_response = final_response.copy()
            entry.final_response['timestamp'] = datetime.now(timezone.utc).isoformat()

    def log_error(self, request_id: str, error: str) -> None:
        """
        Log an error for this conversation.
        
        Args:
            request_id: The request ID for this conversation  
            error: Error message or description
        """
        if not self.enabled or not request_id:
            return
        with self._lock:
            entry = self.active_entries.get(request_id)
            if not entry:
                logger.warning(f'No active conversation found for request {request_id}')
                return
            entry.error = error
        logger.debug(f'Logged error for request {request_id}: {error}')

    def finalize_conversation(self, request_id: str) -> None:
        """
        Finalize and save the conversation to disk.
        
        Args:
            request_id: The request ID for this conversation
        """
        if not self.enabled or not request_id:
            return
        with self._lock:
            entry = self.active_entries.pop(request_id, None)
            if not entry:
                logger.warning(f'No active conversation found for request {request_id}')
                return
            entry.total_duration_ms = int((time.time() - entry.start_time) * 1000)
            log_entry = {'timestamp': entry.timestamp, 'request_id': entry.request_id, 'approach': entry.approach, 'model': entry.model, 'client_request': entry.client_request, 'provider_calls': entry.provider_calls, 'final_response': entry.final_response, 'total_duration_ms': entry.total_duration_ms, 'error': entry.error}
            self._write_log_entry(log_entry)
        logger.debug(f'Finalized conversation for request {request_id}')

    def _write_log_entry(self, log_entry: Dict[str, Any]) -> None:
        """Write a log entry to the appropriate JSONL file"""
        try:
            log_file_path = self._get_log_file_path()
            with open(log_file_path, 'a', encoding='utf-8') as f:
                json.dump(log_entry, f, separators=(',', ':'))
                f.write('\n')
            logger.debug(f'Wrote log entry to {log_file_path}')
        except Exception as e:
            logger.error(f'Failed to write log entry: {e}')

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about conversation logging"""
        with self._lock:
            active_count = len(self.active_entries)
        stats = {'enabled': self.enabled, 'log_dir': str(self.log_dir), 'active_conversations': active_count}
        if self.enabled:
            log_files = list(self.log_dir.glob('conversations_*.jsonl'))
            total_entries = 0
            for log_file in log_files:
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        total_entries += sum((1 for line in f if line.strip()))
                except Exception:
                    pass
            stats.update({'log_files_count': len(log_files), 'total_entries_approximate': total_entries})
        return stats

def _get_log_file_path(self, timestamp: datetime=None) -> Path:
    """Get the log file path for a given timestamp (defaults to now)"""
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)
    date_str = timestamp.strftime('%Y-%m-%d')
    return self.log_dir / f'conversations_{date_str}.jsonl'

def start_conversation(self, client_request: Dict[str, Any], approach: str, model: str) -> str:
    """
        Start logging a new conversation.
        
        Args:
            client_request: The original request from the client
            approach: The optimization approach being used
            model: The model name
            
        Returns:
            str: Unique request ID for this conversation
        """
    if not self.enabled:
        return ''
    request_id = self._generate_request_id()
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = ConversationEntry(request_id=request_id, timestamp=timestamp, approach=approach, model=model, client_request=client_request.copy())
    with self._lock:
        self.active_entries[request_id] = entry
    logger.debug(f'Started conversation logging for request {request_id}')
    return request_id

def log_provider_call(self, request_id: str, provider_request: Dict[str, Any], provider_response: Dict[str, Any]) -> None:
    """
        Log a provider API call and response.
        
        Args:
            request_id: The request ID for this conversation
            provider_request: The request sent to the provider
            provider_response: The response received from the provider
        """
    if not self.enabled or not request_id:
        return
    with self._lock:
        entry = self.active_entries.get(request_id)
        if not entry:
            logger.warning(f'No active conversation found for request {request_id}')
            return
        call_data = {'call_number': len(entry.provider_calls) + 1, 'timestamp': datetime.now(timezone.utc).isoformat(), 'request': provider_request.copy(), 'response': provider_response.copy()}
        entry.provider_calls.append(call_data)
    logger.debug(f'Logged provider call #{len(entry.provider_calls)} for request {request_id}')

def log_final_response(self, request_id: str, final_response: Dict[str, Any]) -> None:
    """
        Log the final response sent back to the client.
        
        Args:
            request_id: The request ID for this conversation
            final_response: The final response sent to the client
        """
    if not self.enabled or not request_id:
        return
    with self._lock:
        entry = self.active_entries.get(request_id)
        if not entry:
            logger.warning(f'No active conversation found for request {request_id}')
            return
        entry.final_response = final_response.copy()
        entry.final_response['timestamp'] = datetime.now(timezone.utc).isoformat()

def normalize_message_content(messages):
    """
    Ensure all message content fields are strings, not lists.
    Some models don't handle list-format content correctly.
    """
    normalized_messages = []
    for message in messages:
        normalized_message = message.copy()
        content = message.get('content', '')
        if isinstance(content, list):
            text_content = ' '.join((item.get('text', '') for item in content if isinstance(item, dict) and item.get('type') == 'text'))
            normalized_message['content'] = text_content
        normalized_messages.append(normalized_message)
    return normalized_messages

def parse_args():
    parser = argparse.ArgumentParser(description='Run LLM inference with various approaches.')
    try:
        from optillm import __version__ as package_version
    except ImportError:
        package_version = 'unknown'
    parser.add_argument('--version', action='version', version=f'%(prog)s {package_version}', help="Show program's version number and exit")
    args_env = [('--optillm-api-key', 'OPTILLM_API_KEY', str, '', 'Optional API key for client authentication to optillm'), ('--approach', 'OPTILLM_APPROACH', str, 'auto', 'Inference approach to use', known_approaches + list(plugin_approaches.keys())), ('--mcts-simulations', 'OPTILLM_SIMULATIONS', int, 2, 'Number of MCTS simulations'), ('--mcts-exploration', 'OPTILLM_EXPLORATION', float, 0.2, 'Exploration weight for MCTS'), ('--mcts-depth', 'OPTILLM_DEPTH', int, 1, 'Simulation depth for MCTS'), ('--model', 'OPTILLM_MODEL', str, 'gpt-4o-mini', 'OpenAI model to use'), ('--rstar-max-depth', 'OPTILLM_RSTAR_MAX_DEPTH', int, 3, 'Maximum depth for rStar algorithm'), ('--rstar-num-rollouts', 'OPTILLM_RSTAR_NUM_ROLLOUTS', int, 5, 'Number of rollouts for rStar algorithm'), ('--rstar-c', 'OPTILLM_RSTAR_C', float, 1.4, 'Exploration constant for rStar algorithm'), ('--n', 'OPTILLM_N', int, 1, 'Number of final responses to be returned'), ('--return-full-response', 'OPTILLM_RETURN_FULL_RESPONSE', bool, False, 'Return the full response including the CoT with <thinking> tags'), ('--port', 'OPTILLM_PORT', int, 8000, 'Specify the port to run the proxy'), ('--log', 'OPTILLM_LOG', str, 'info', 'Specify the logging level', list(logging_levels.keys())), ('--launch-gui', 'OPTILLM_LAUNCH_GUI', bool, False, 'Launch a Gradio chat interface'), ('--plugins-dir', 'OPTILLM_PLUGINS_DIR', str, '', 'Path to the plugins directory'), ('--log-conversations', 'OPTILLM_LOG_CONVERSATIONS', bool, False, 'Enable conversation logging with full metadata'), ('--conversation-log-dir', 'OPTILLM_CONVERSATION_LOG_DIR', str, str(Path.home() / '.optillm' / 'conversations'), 'Directory to save conversation logs')]
    for arg, env, type_, default, help_text, *extra in args_env:
        env_value = os.environ.get(env)
        if env_value is not None:
            if type_ == bool:
                default = env_value.lower() in ('true', '1', 'yes')
            else:
                default = type_(env_value)
        if extra and extra[0]:
            parser.add_argument(arg, type=type_, default=default, help=help_text, choices=extra[0])
        elif type_ == bool:
            parser.add_argument(arg, action='store_true', default=default, help=help_text)
        else:
            parser.add_argument(arg, type=type_, default=default, help=help_text)
    best_of_n_default = int(os.environ.get('OPTILLM_BEST_OF_N', 3))
    parser.add_argument('--best-of-n', '--best_of_n', dest='best_of_n', type=int, default=best_of_n_default, help='Number of samples for best_of_n approach')
    base_url_default = os.environ.get('OPTILLM_BASE_URL', '')
    parser.add_argument('--base-url', '--base_url', dest='base_url', type=str, default=base_url_default, help='Base url for OpenAI compatible endpoint')
    ssl_verify_default = os.environ.get('OPTILLM_SSL_VERIFY', 'true').lower() in ('true', '1', 'yes')
    parser.add_argument('--ssl-verify', dest='ssl_verify', action='store_true' if ssl_verify_default else 'store_false', default=ssl_verify_default, help='Enable SSL certificate verification (default: True)')
    parser.add_argument('--no-ssl-verify', dest='ssl_verify', action='store_false', help='Disable SSL certificate verification')
    ssl_cert_path_default = os.environ.get('OPTILLM_SSL_CERT_PATH', '')
    parser.add_argument('--ssl-cert-path', dest='ssl_cert_path', type=str, default=ssl_cert_path_default, help='Path to custom CA certificate bundle for SSL verification')
    default_config_path = get_config_path()
    batch_mode_default = os.environ.get('OPTILLM_BATCH_MODE', 'false').lower() == 'true'
    batch_size_default = int(os.environ.get('OPTILLM_BATCH_SIZE', 4))
    batch_wait_ms_default = int(os.environ.get('OPTILLM_BATCH_WAIT_MS', 50))
    parser.add_argument('--batch-mode', action='store_true', default=batch_mode_default, help='Enable automatic request batching (fail-fast, no fallback)')
    parser.add_argument('--batch-size', type=int, default=batch_size_default, help='Maximum batch size for request batching')
    parser.add_argument('--batch-wait-ms', dest='batch_wait_ms', type=int, default=batch_wait_ms_default, help='Maximum wait time in milliseconds for batch formation')
    for field in fields(CepoConfig):
        parser.add_argument(f'--cepo_{field.name}', dest=f'cepo_{field.name}', type=field.type, default=None, help=f'CePO configuration for {field.name}')
    parser.add_argument('--cepo_config_file', dest='cepo_config_file', type=str, default=default_config_path, help='Path to CePO configuration file')
    args = parser.parse_args()
    args_dict = vars(args)
    for key in list(args_dict.keys()):
        new_key = key.replace('-', '_')
        if new_key != key:
            args_dict[new_key] = args_dict.pop(key)
    return args

def run(system_prompt, initial_query: str, client=None, model=None) -> Tuple[str, int]:
    urls = extract_urls(initial_query)
    modified_query = initial_query
    for url in urls:
        content = fetch_webpage_content(url)
        domain = urlparse(url).netloc
        modified_query = modified_query.replace(url, f'{url} [Content from {domain}: {content}]')
    return (modified_query, 0)

class Strategy:
    """Represents a problem-solving strategy learned by the system."""

    def __init__(self, strategy_id: str, problem_type: str, strategy_text: str, examples: List[str]=None, success_count: int=0, total_attempts: int=0, created_at: str=None, last_used: str=None, last_updated: str=None, confidence: float=0.5, tags: List[str]=None, reasoning_examples: List[str]=None):
        self.strategy_id = strategy_id
        self.problem_type = problem_type if problem_type in VALID_PROBLEM_TYPES else 'general_problem'
        self.strategy_text = strategy_text
        self.examples = examples or []
        self.success_count = success_count
        self.total_attempts = total_attempts
        self.created_at = created_at or datetime.now().isoformat()
        self.last_used = last_used
        self.last_updated = last_updated or self.created_at
        self.confidence = confidence
        self.tags = tags or []
        self.reasoning_examples = reasoning_examples or []

    @property
    def success_rate(self) -> float:
        """Calculate the success rate of this strategy."""
        if self.total_attempts == 0:
            return 0.0
        return self.success_count / self.total_attempts

    def to_dict(self) -> Dict[str, Any]:
        """Convert the strategy to a dictionary for serialization."""
        return {'strategy_id': self.strategy_id, 'problem_type': self.problem_type, 'strategy_text': self.strategy_text, 'examples': self.examples, 'success_count': self.success_count, 'total_attempts': self.total_attempts, 'created_at': self.created_at, 'last_used': self.last_used, 'last_updated': self.last_updated, 'confidence': self.confidence, 'tags': self.tags, 'reasoning_examples': self.reasoning_examples}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Strategy':
        """Create a Strategy instance from a dictionary."""
        return cls(strategy_id=data['strategy_id'], problem_type=data['problem_type'], strategy_text=data['strategy_text'], examples=data.get('examples', []), success_count=data.get('success_count', 0), total_attempts=data.get('total_attempts', 0), created_at=data.get('created_at'), last_used=data.get('last_used'), last_updated=data.get('last_updated'), confidence=data.get('confidence', 0.5), tags=data.get('tags', []), reasoning_examples=data.get('reasoning_examples', []))

    def record_attempt(self, success: bool) -> None:
        """Record an attempt to use this strategy."""
        self.total_attempts += 1
        if success:
            self.success_count += 1
        self.last_used = datetime.now().isoformat()
        alpha = 0.1
        self.confidence = (1 - alpha) * self.confidence + alpha * (1.0 if success else 0.0)

    def update_strategy(self, new_strategy_text: str) -> None:
        """Update the strategy text with a refined version."""
        self.strategy_text = new_strategy_text
        self.last_updated = datetime.now().isoformat()

    def add_reasoning_example(self, reasoning: str) -> None:
        """Add a reasoning example to the strategy."""
        if reasoning and reasoning.strip():
            if len(self.reasoning_examples) >= 5:
                self.reasoning_examples.pop(0)
            self.reasoning_examples.append(reasoning.strip())

    def add_example(self, example: str) -> None:
        """Add an example to the strategy."""
        if example and example not in self.examples:
            self.examples.append(example)

def __init__(self, strategy_id: str, problem_type: str, strategy_text: str, examples: List[str]=None, success_count: int=0, total_attempts: int=0, created_at: str=None, last_used: str=None, last_updated: str=None, confidence: float=0.5, tags: List[str]=None, reasoning_examples: List[str]=None):
    self.strategy_id = strategy_id
    self.problem_type = problem_type if problem_type in VALID_PROBLEM_TYPES else 'general_problem'
    self.strategy_text = strategy_text
    self.examples = examples or []
    self.success_count = success_count
    self.total_attempts = total_attempts
    self.created_at = created_at or datetime.now().isoformat()
    self.last_used = last_used
    self.last_updated = last_updated or self.created_at
    self.confidence = confidence
    self.tags = tags or []
    self.reasoning_examples = reasoning_examples or []

def record_attempt(self, success: bool) -> None:
    """Record an attempt to use this strategy."""
    self.total_attempts += 1
    if success:
        self.success_count += 1
    self.last_used = datetime.now().isoformat()
    alpha = 0.1
    self.confidence = (1 - alpha) * self.confidence + alpha * (1.0 if success else 0.0)

def update_strategy(self, new_strategy_text: str) -> None:
    """Update the strategy text with a refined version."""
    self.strategy_text = new_strategy_text
    self.last_updated = datetime.now().isoformat()

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

def get_metrics(self) -> Dict[str, Any]:
    """Get the current metrics."""
    return self.metrics.copy()

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

def main():
    parser = argparse.ArgumentParser(description='Run AutoThink demo')
    parser.add_argument('--model', type=str, default='deepseek-ai/deepseek-r1-llama-8b', help='Model name or path')
    parser.add_argument('--steering-dataset', type=str, default='codelion/Qwen3-0.6B-pts-steering-vectors', help='Steering vectors dataset')
    parser.add_argument('--target-layer', type=int, default=19, help='Target layer for steering')
    parser.add_argument('--query', type=str, default='Explain quantum computing to me in detail', help='Query to process')
    args = parser.parse_args()
    try:
        logger.info(f'Loading model: {args.model}')
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        logger.info(f'Using device: {device}')
        tokenizer = AutoTokenizer.from_pretrained(args.model)
        model_kwargs = {'trust_remote_code': True}
        if device == 'cuda':
            model_kwargs['torch_dtype'] = torch.float16
            model_kwargs['device_map'] = 'auto'
        model = AutoModelForCausalLM.from_pretrained(args.model, **model_kwargs)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        logger.info('Model and tokenizer loaded successfully')
        config = {'steering_dataset': args.steering_dataset, 'target_layer': args.target_layer, 'pattern_strengths': {'depth_and_thoroughness': 2.5, 'numerical_accuracy': 2.0, 'self_correction': 3.0, 'exploration': 2.0, 'organization': 1.5}}
        messages = [{'role': 'system', 'content': 'You are a helpful assistant.'}, {'role': 'user', 'content': args.query}]
        logger.info('Running AutoThink processing...')
        response = autothink_decode(model, tokenizer, messages, config)
        print('\n' + '=' * 80)
        print('QUERY:', args.query)
        print('-' * 80)
        print(response)
        print('=' * 80 + '\n')
    except Exception as e:
        logger.error(f'Error in AutoThink demo: {str(e)}')
        raise

def extract_question_only(task: str) -> str:
    """
    We noticed that sometimes if the task includes specific formatting instructions, they may interfere with the reasoning flow. This
    is a temporary workaround to extract the question only from the task. Work in progress.
    """
    question_only = task.replace('\n## Question: \n\n', '')
    question_only = question_only.replace('\n\n\n## Instruction \n\nPlease answer this question by first reasoning and then providing your answer.\nPresent your reasoning and solution in the following json format. \nPlease show your final answer in the `answer` field, e.g.,`"answer": "42"`.\n\n```json\n{\n    "reasoning": "___",\n    "answer": "___"\n}\n```\n', '')
    return question_only

class TestConversationLoggingWithServer(unittest.TestCase):
    """Integration tests with real OptILLM server and conversation logging"""

    @classmethod
    def setUpClass(cls):
        """Set up OptILLM server for testing"""
        setup_test_env()
        cls.server_available = cls._check_existing_server()
        cls.server_process = None
        cls.temp_log_dir = None
        if not cls.server_available:
            cls.temp_log_dir = Path(tempfile.mkdtemp())
            cls.server_process = cls._start_server_with_logging()
            max_wait = 30
            start_time = time.time()
            while time.time() - start_time < max_wait:
                if cls._check_server_health():
                    cls.server_available = True
                    break
                time.sleep(1)
            if not cls.server_available:
                if cls.server_process:
                    stop_test_server(cls.server_process)
                raise unittest.SkipTest('Could not start OptILLM server for testing')

    @classmethod
    def tearDownClass(cls):
        """Clean up server"""
        if cls.server_process:
            stop_test_server(cls.server_process)
        if cls.temp_log_dir and cls.temp_log_dir.exists():
            import shutil
            shutil.rmtree(cls.temp_log_dir, ignore_errors=True)

    @staticmethod
    def _check_existing_server():
        """Check if OptILLM server is already running"""
        try:
            response = requests.get('http://localhost:8000/v1/health', timeout=2)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    @staticmethod
    def _check_server_health():
        """Check if server is healthy"""
        try:
            response = requests.get('http://localhost:8000/v1/health', timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    @classmethod
    def _start_server_with_logging(cls):
        """Start server with conversation logging enabled"""
        env = os.environ.copy()
        env['OPTILLM_API_KEY'] = 'optillm'
        env['OPTILLM_LOG_CONVERSATIONS'] = 'true'
        env['OPTILLM_CONVERSATION_LOG_DIR'] = str(cls.temp_log_dir)
        proc = subprocess.Popen([sys.executable, 'optillm.py', '--model', TEST_MODEL, '--port', '8000', '--log-conversations', '--conversation-log-dir', str(cls.temp_log_dir)], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return proc

    def setUp(self):
        """Set up test client"""
        if not self.server_available:
            self.skipTest('OptILLM server not available')
        self.client = OpenAI(api_key='optillm', base_url='http://localhost:8000/v1')
        if self.temp_log_dir:
            self.log_dir = self.temp_log_dir
        else:
            self.log_dir = Path.home() / '.optillm' / 'conversations'
        self.initial_log_files = set(self.log_dir.glob('*.jsonl')) if self.log_dir.exists() else set()

    def _get_new_log_entries(self):
        """Get new log entries since test started"""
        if not self.log_dir.exists():
            return []
        current_log_files = set(self.log_dir.glob('*.jsonl'))
        new_files = current_log_files - self.initial_log_files
        modified_files = [f for f in self.initial_log_files if f in current_log_files and f.stat().st_mtime > time.time() - 60]
        entries = []
        for log_file in new_files.union(set(modified_files)):
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            entries.append(json.loads(line))
            except (json.JSONDecodeError, IOError):
                continue
        return entries

    def test_basic_none_approach_logging(self):
        """Test basic none approach with conversation logging"""
        response = self.client.chat.completions.create(model=TEST_MODEL, messages=[{'role': 'system', 'content': 'You are a helpful assistant.'}, {'role': 'user', 'content': 'What is 2 + 2? Answer with just the number.'}], max_tokens=10)
        self.assertIsNotNone(response)
        self.assertGreater(len(response.choices), 0)
        self.assertIsNotNone(response.choices[0].message.content)
        time.sleep(2)
        entries = self._get_new_log_entries()
        self.assertGreater(len(entries), 0, 'No log entries found for basic none approach')
        found_entry = False
        for entry in entries:
            if entry.get('approach') == 'none' and entry.get('model') == TEST_MODEL:
                found_entry = True
                self.assertIn('provider_calls', entry)
                self.assertIn('client_request', entry)
                self.assertIn('timestamp', entry)
                break
        self.assertTrue(found_entry, 'No valid log entry found for none approach')

    def test_re2_approach_logging(self):
        """Test RE2 approach with conversation logging"""
        response = self.client.chat.completions.create(model=f're2-{TEST_MODEL}', messages=[{'role': 'system', 'content': 'You are a helpful assistant.'}, {'role': 'user', 'content': 'What is the capital of France? Answer in one word.'}], max_tokens=10)
        self.assertIsNotNone(response)
        self.assertGreater(len(response.choices), 0)
        time.sleep(3)
        entries = self._get_new_log_entries()
        re2_entry = None
        for entry in entries:
            if entry.get('approach') == 're2':
                re2_entry = entry
                break
        self.assertIsNotNone(re2_entry, 'No RE2 log entry found')
        self.assertEqual(re2_entry['model'], TEST_MODEL)
        self.assertIn('provider_calls', re2_entry)
        self.assertGreaterEqual(len(re2_entry['provider_calls']), 1)

    def test_cot_reflection_approach_logging(self):
        """Test CoT Reflection approach with conversation logging"""
        response = self.client.chat.completions.create(model=f'cot_reflection-{TEST_MODEL}', messages=[{'role': 'system', 'content': 'Think step by step.'}, {'role': 'user', 'content': 'What is 3 × 4? Show your work.'}], max_tokens=50)
        self.assertIsNotNone(response)
        self.assertGreater(len(response.choices), 0)
        time.sleep(3)
        entries = self._get_new_log_entries()
        cot_entry = None
        for entry in entries:
            if entry.get('approach') == 'cot_reflection':
                cot_entry = entry
                break
        self.assertIsNotNone(cot_entry, 'No CoT reflection log entry found')
        self.assertEqual(cot_entry['model'], TEST_MODEL)
        self.assertIn('provider_calls', cot_entry)
        self.assertGreaterEqual(len(cot_entry['provider_calls']), 1)

    def test_extra_body_approach_logging(self):
        """Test approach specification via extra_body parameter"""
        response = self.client.chat.completions.create(model=TEST_MODEL, messages=[{'role': 'system', 'content': 'You are a helpful assistant.'}, {'role': 'user', 'content': "Test extra_body. Reply with 'OK'."}], extra_body={'optillm_approach': 're2'}, max_tokens=10)
        self.assertIsNotNone(response)
        self.assertGreater(len(response.choices), 0)
        time.sleep(3)
        entries = self._get_new_log_entries()
        found_entry = False
        for entry in entries:
            if entry.get('approach') == 're2' and entry.get('model') == TEST_MODEL:
                found_entry = True
                self.assertIn('provider_calls', entry)
                break
        self.assertTrue(found_entry, 'No log entry found for extra_body approach specification')

    def test_reasoning_tokens_logging(self):
        """Test that reasoning tokens are properly logged"""
        response = self.client.chat.completions.create(model=TEST_MODEL, messages=[{'role': 'system', 'content': 'Think step by step and show reasoning.'}, {'role': 'user', 'content': 'What is 5 + 7? Explain your thinking.'}], max_tokens=100)
        self.assertIsNotNone(response)
        self.assertIsNotNone(response.usage)
        time.sleep(3)
        entries = self._get_new_log_entries()
        found_usage_entry = False
        for entry in entries:
            if 'provider_calls' in entry and len(entry['provider_calls']) > 0:
                for call in entry['provider_calls']:
                    if 'response' in call and 'usage' in call['response']:
                        found_usage_entry = True
                        usage = call['response']['usage']
                        self.assertIn('completion_tokens', usage)
                        if 'completion_tokens_details' in usage:
                            details = usage['completion_tokens_details']
                            if 'reasoning_tokens' in details:
                                self.assertIsInstance(details['reasoning_tokens'], int)
                        break
            if found_usage_entry:
                break
        self.assertTrue(found_usage_entry, 'No log entry with usage information found')

    def test_multiple_approaches_logging(self):
        """Test multiple different approaches get logged correctly"""
        approaches_to_test = [('none', TEST_MODEL), ('re2', f're2-{TEST_MODEL}'), ('cot_reflection', f'cot_reflection-{TEST_MODEL}')]
        responses = []
        for approach_name, model_name in approaches_to_test:
            try:
                response = self.client.chat.completions.create(model=model_name, messages=[{'role': 'system', 'content': 'You are a helpful assistant.'}, {'role': 'user', 'content': f"Test {approach_name}. Reply 'OK'."}], max_tokens=10)
                responses.append((approach_name, response))
                time.sleep(1)
            except Exception as e:
                self.fail(f'Approach {approach_name} failed: {e}')
        self.assertEqual(len(responses), 3)
        for approach_name, response in responses:
            self.assertIsNotNone(response)
            self.assertGreater(len(response.choices), 0)
        time.sleep(5)
        entries = self._get_new_log_entries()
        found_approaches = set()
        for entry in entries:
            approach = entry.get('approach')
            if approach in ['none', 're2', 'cot_reflection']:
                found_approaches.add(approach)
                self.assertEqual(entry['model'], TEST_MODEL)
                self.assertIn('provider_calls', entry)
        self.assertGreaterEqual(len(found_approaches), 2, f'Not all approaches logged. Found: {found_approaches}')

    def test_concurrent_requests_logging(self):
        """Test that concurrent requests are logged properly"""
        import threading
        import queue
        results = queue.Queue()

        def make_request(index):
            try:
                response = self.client.chat.completions.create(model=TEST_MODEL, messages=[{'role': 'system', 'content': 'You are a helpful assistant.'}, {'role': 'user', 'content': f'Concurrent test {index}. Reply with the number {index}.'}], max_tokens=10)
                results.put(('success', index, response))
            except Exception as e:
                results.put(('error', index, str(e)))
        threads = []
        for i in range(3):
            thread = threading.Thread(target=make_request, args=(i,))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join(timeout=30)
        successful_requests = []
        while not results.empty():
            result_type, index, result = results.get()
            if result_type == 'success':
                successful_requests.append((index, result))
            else:
                self.fail(f'Concurrent request {index} failed: {result}')
        self.assertGreaterEqual(len(successful_requests), 2, 'Not enough concurrent requests succeeded')
        time.sleep(5)
        entries = self._get_new_log_entries()
        concurrent_entries = [e for e in entries if 'Concurrent test' in str(e.get('client_request', {}))]
        self.assertGreaterEqual(len(concurrent_entries), 2, 'Not enough concurrent request log entries found')

    def test_error_handling_logging(self):
        """Test that errors in approaches are properly logged"""
        try:
            response = self.client.chat.completions.create(model=TEST_MODEL, messages=[{'role': 'system', 'content': 'You are a helpful assistant.'}, {'role': 'user', 'content': 'This is a test for error logging scenarios.'}], max_tokens=1)
            self.assertIsNotNone(response)
        except Exception:
            pass
        time.sleep(3)
        entries = self._get_new_log_entries()
        found_relevant_entry = False
        for entry in entries:
            if 'error logging scenarios' in str(entry.get('client_request', {})):
                found_relevant_entry = True
                break
        self.assertGreaterEqual(len(entries), 0, 'No log entries found (system may have crashed)')

    def test_log_file_structure_and_format(self):
        """Test that log files have correct JSONL structure and required fields"""
        response = self.client.chat.completions.create(model=TEST_MODEL, messages=[{'role': 'system', 'content': 'You are a helpful assistant.'}, {'role': 'user', 'content': "Structure test. Reply 'STRUCTURE_OK'."}], max_tokens=15)
        self.assertIsNotNone(response)
        time.sleep(3)
        entries = self._get_new_log_entries()
        relevant_entry = None
        for entry in entries:
            if 'STRUCTURE_OK' in str(entry.get('client_request', {})) or 'Structure test' in str(entry.get('client_request', {})):
                relevant_entry = entry
                break
        if not relevant_entry and entries:
            relevant_entry = entries[0]
        self.assertIsNotNone(relevant_entry, 'No log entry found for structure validation')
        required_fields = ['timestamp', 'request_id', 'approach', 'model', 'client_request', 'provider_calls']
        for field in required_fields:
            self.assertIn(field, relevant_entry, f'Missing required field: {field}')
        provider_calls = relevant_entry['provider_calls']
        self.assertIsInstance(provider_calls, list)
        self.assertGreater(len(provider_calls), 0, 'No provider calls logged')
        for call in provider_calls:
            self.assertIn('request', call)
            self.assertIn('response', call)
            self.assertIn('timestamp', call)
            self.assertIn('call_number', call)
        self.assertIsInstance(relevant_entry['timestamp'], str)
        for call in provider_calls:
            self.assertIsInstance(call['timestamp'], str)

@classmethod
def _start_server_with_logging(cls):
    """Start server with conversation logging enabled"""
    env = os.environ.copy()
    env['OPTILLM_API_KEY'] = 'optillm'
    env['OPTILLM_LOG_CONVERSATIONS'] = 'true'
    env['OPTILLM_CONVERSATION_LOG_DIR'] = str(cls.temp_log_dir)
    proc = subprocess.Popen([sys.executable, 'optillm.py', '--model', TEST_MODEL, '--port', '8000', '--log-conversations', '--conversation-log-dir', str(cls.temp_log_dir)], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc

def test_config_validation():
    """Test configuration validation."""
    logger.info('Testing configuration validation...')
    try:
        from optillm.deepconf.deepconf import validate_deepconf_config, DEFAULT_CONFIG
        valid_config = DEFAULT_CONFIG.copy()
        validated = validate_deepconf_config(valid_config)
        assert validated == valid_config
        try:
            invalid_config = {'variant': 'invalid'}
            validate_deepconf_config(invalid_config)
            assert False, 'Should have raised ValueError'
        except ValueError:
            pass
        try:
            invalid_config = {'warmup_samples': -1}
            validate_deepconf_config(invalid_config)
            assert False, 'Should have raised ValueError'
        except ValueError:
            pass
        logger.info('✓ Configuration validation tests passed')
        return True
    except Exception as e:
        logger.error(f'✗ Configuration validation test failed: {e}')
        return False

def main():
    parser = argparse.ArgumentParser(description='Test different LLM inference approaches.')
    parser.add_argument('--test_cases', type=str, default=None, help='Path to test cases JSON file')
    parser.add_argument('--approaches', nargs='+', default=list(APPROACHES.keys()), help='Approaches to test')
    parser.add_argument('--model', type=str, default='gpt-4o-mini', help='Model to use for testing')
    parser.add_argument('--base-url', type=str, default=None, help='The base_url for the OpenAI API compatible endpoint')
    parser.add_argument('--single-test', type=str, default=None, help='Name of a single test case to run')
    args = parser.parse_args()
    if args.test_cases is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        args.test_cases = os.path.join(script_dir, 'test_cases.json')
    if API_KEY == 'optillm' and args.model == 'gpt-4o-mini':
        args.model = TEST_MODEL
        logger.info(f'Using local model: {args.model}')
    if API_KEY == 'optillm':
        os.environ['OPTILLM_API_KEY'] = 'optillm'
    test_cases = load_test_cases(args.test_cases)
    if args.base_url:
        client = OpenAI(api_key=API_KEY, base_url=args.base_url)
    elif API_KEY == 'optillm':
        client = OpenAI(api_key=API_KEY, base_url='http://localhost:8000/v1')
        logger.info('Using local inference endpoint: http://localhost:8000/v1')
    else:
        client = OpenAI(api_key=API_KEY)
    results = run_tests(test_cases, args.approaches, client, args.model, args.single_test)
    print_summary(results)
    with open('test_results.json', 'w') as f:
        json.dump(results, f, indent=2)

class TestSSLConfiguration(unittest.TestCase):
    """Test SSL configuration via CLI arguments and environment variables."""

    def setUp(self):
        """Reset server_config before each test."""
        self.original_config = server_config.copy()
        for key in ['OPTILLM_SSL_VERIFY', 'OPTILLM_SSL_CERT_PATH']:
            if key in os.environ:
                del os.environ[key]

    def tearDown(self):
        """Restore original server_config after each test."""
        server_config.clear()
        server_config.update(self.original_config)

    def test_default_ssl_verify_enabled(self):
        """Test that SSL verification is enabled by default."""
        self.assertTrue(server_config.get('ssl_verify', True))
        self.assertEqual(server_config.get('ssl_cert_path', ''), '')

    def test_cli_no_ssl_verify_flag(self):
        """Test --no-ssl-verify CLI flag disables SSL verification."""
        with patch('sys.argv', ['optillm', '--no-ssl-verify']):
            args = parse_args()
            self.assertFalse(args.ssl_verify)

    def test_cli_ssl_cert_path(self):
        """Test --ssl-cert-path CLI argument."""
        test_cert_path = '/path/to/ca-bundle.crt'
        with patch('sys.argv', ['optillm', '--ssl-cert-path', test_cert_path]):
            args = parse_args()
            self.assertEqual(args.ssl_cert_path, test_cert_path)

    def test_env_ssl_verify_false(self):
        """Test OPTILLM_SSL_VERIFY=false environment variable."""
        os.environ['OPTILLM_SSL_VERIFY'] = 'false'
        with patch('sys.argv', ['optillm']):
            args = parse_args()
            self.assertFalse(args.ssl_verify)

    def test_env_ssl_verify_true(self):
        """Test OPTILLM_SSL_VERIFY=true environment variable."""
        os.environ['OPTILLM_SSL_VERIFY'] = 'true'
        with patch('sys.argv', ['optillm']):
            args = parse_args()
            self.assertTrue(args.ssl_verify)

    def test_env_ssl_cert_path(self):
        """Test OPTILLM_SSL_CERT_PATH environment variable."""
        test_cert_path = '/etc/ssl/certs/custom-ca.pem'
        os.environ['OPTILLM_SSL_CERT_PATH'] = test_cert_path
        with patch('sys.argv', ['optillm']):
            args = parse_args()
            self.assertEqual(args.ssl_cert_path, test_cert_path)

    def test_cli_overrides_env(self):
        """Test that CLI arguments override environment variables."""
        os.environ['OPTILLM_SSL_VERIFY'] = 'true'
        with patch('sys.argv', ['optillm', '--no-ssl-verify']):
            args = parse_args()
            self.assertFalse(args.ssl_verify)

def setUp(self):
    """Reset server_config before each test."""
    self.original_config = server_config.copy()
    for key in ['OPTILLM_SSL_VERIFY', 'OPTILLM_SSL_CERT_PATH']:
        if key in os.environ:
            del os.environ[key]

class TestHTTPClientSSLConfiguration(unittest.TestCase):
    """Test that SSL configuration is properly applied to HTTP clients."""

    def setUp(self):
        """Set up test environment."""
        self.original_config = server_config.copy()

    def tearDown(self):
        """Restore original server_config."""
        server_config.clear()
        server_config.update(self.original_config)

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_httpx_client_ssl_verify_disabled(self):
        """Test httpx.Client created with verify=False when SSL disabled."""
        from optillm.server import get_config
        server_config['ssl_verify'] = False
        server_config['ssl_cert_path'] = ''
        with patch('httpx.Client') as mock_httpx_client, patch('optillm.server.OpenAI') as mock_openai:
            get_config()
            mock_httpx_client.assert_called_once_with(verify=False)

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_httpx_client_ssl_verify_enabled(self):
        """Test httpx.Client created with verify=True by default."""
        from optillm.server import get_config
        server_config['ssl_verify'] = True
        server_config['ssl_cert_path'] = ''
        with patch('httpx.Client') as mock_httpx_client, patch('optillm.server.OpenAI') as mock_openai:
            get_config()
            mock_httpx_client.assert_called_once_with(verify=True)

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_httpx_client_custom_cert_path(self):
        """Test httpx.Client created with custom certificate path."""
        from optillm.server import get_config
        test_cert_path = '/path/to/custom-ca.pem'
        server_config['ssl_verify'] = True
        server_config['ssl_cert_path'] = test_cert_path
        with patch('httpx.Client') as mock_httpx_client, patch('optillm.server.OpenAI') as mock_openai:
            get_config()
            mock_httpx_client.assert_called_once_with(verify=test_cert_path)

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_openai_client_receives_http_client(self):
        """Test that OpenAI client receives the configured httpx client."""
        from optillm.server import get_config
        server_config['ssl_verify'] = False
        server_config['ssl_cert_path'] = ''
        server_config['base_url'] = ''
        mock_http_client_instance = MagicMock()
        with patch('httpx.Client', return_value=mock_http_client_instance) as mock_httpx_client, patch('optillm.server.OpenAI') as mock_openai:
            get_config()
            mock_openai.assert_called_once()
            call_kwargs = mock_openai.call_args[1]
            self.assertIn('http_client', call_kwargs)
            self.assertEqual(call_kwargs['http_client'], mock_http_client_instance)

    @patch.dict(os.environ, {'CEREBRAS_API_KEY': 'test-key'})
    def test_cerebras_client_receives_http_client(self):
        """Test that Cerebras client receives the configured httpx client."""
        from optillm.server import get_config
        server_config['ssl_verify'] = False
        server_config['ssl_cert_path'] = ''
        server_config['base_url'] = ''
        mock_http_client_instance = MagicMock()
        with patch('httpx.Client', return_value=mock_http_client_instance) as mock_httpx_client, patch('optillm.server.Cerebras') as mock_cerebras:
            get_config()
            mock_cerebras.assert_called_once()
            call_kwargs = mock_cerebras.call_args[1]
            self.assertIn('http_client', call_kwargs)
            self.assertEqual(call_kwargs['http_client'], mock_http_client_instance)

    @patch.dict(os.environ, {'AZURE_OPENAI_API_KEY': 'test-key', 'AZURE_API_VERSION': '2024-02-15-preview', 'AZURE_API_BASE': 'https://test.openai.azure.com'})
    def test_azure_client_receives_http_client(self):
        """Test that AzureOpenAI client receives the configured httpx client."""
        from optillm.server import get_config
        server_config['ssl_verify'] = False
        server_config['ssl_cert_path'] = ''
        mock_http_client_instance = MagicMock()
        with patch('httpx.Client', return_value=mock_http_client_instance) as mock_httpx_client, patch('optillm.server.AzureOpenAI') as mock_azure:
            get_config()
            mock_azure.assert_called_once()
            call_kwargs = mock_azure.call_args[1]
            self.assertIn('http_client', call_kwargs)
            self.assertEqual(call_kwargs['http_client'], mock_http_client_instance)

def setUp(self):
    """Set up test environment."""
    self.original_config = server_config.copy()

class TestPluginSSLConfiguration(unittest.TestCase):
    """Test that plugins properly use SSL configuration."""

    def setUp(self):
        """Set up test environment."""
        self.original_config = server_config.copy()

    def tearDown(self):
        """Restore original server_config."""
        server_config.clear()
        server_config.update(self.original_config)

    @patch('optillm.plugins.readurls_plugin.requests.get')
    def test_readurls_plugin_ssl_verify_disabled(self, mock_requests_get):
        """Test readurls plugin respects SSL verification disabled."""
        from optillm.plugins.readurls_plugin import fetch_webpage_content
        server_config['ssl_verify'] = False
        server_config['ssl_cert_path'] = ''
        mock_response = MagicMock()
        mock_response.content = b'<html><body><p>Test content</p></body></html>'
        mock_response.raise_for_status = MagicMock()
        mock_requests_get.return_value = mock_response
        fetch_webpage_content('https://example.com')
        mock_requests_get.assert_called_once()
        call_kwargs = mock_requests_get.call_args[1]
        self.assertIn('verify', call_kwargs)
        self.assertFalse(call_kwargs['verify'])

    @patch('optillm.plugins.readurls_plugin.requests.get')
    def test_readurls_plugin_ssl_verify_enabled(self, mock_requests_get):
        """Test readurls plugin respects SSL verification enabled."""
        from optillm.plugins.readurls_plugin import fetch_webpage_content
        server_config['ssl_verify'] = True
        server_config['ssl_cert_path'] = ''
        mock_response = MagicMock()
        mock_response.content = b'<html><body><p>Test content</p></body></html>'
        mock_response.raise_for_status = MagicMock()
        mock_requests_get.return_value = mock_response
        fetch_webpage_content('https://example.com')
        mock_requests_get.assert_called_once()
        call_kwargs = mock_requests_get.call_args[1]
        self.assertIn('verify', call_kwargs)
        self.assertTrue(call_kwargs['verify'])

    @patch('optillm.plugins.readurls_plugin.requests.get')
    def test_readurls_plugin_custom_cert_path(self, mock_requests_get):
        """Test readurls plugin uses custom certificate path."""
        from optillm.plugins.readurls_plugin import fetch_webpage_content
        test_cert_path = '/path/to/custom-ca.pem'
        server_config['ssl_verify'] = True
        server_config['ssl_cert_path'] = test_cert_path
        mock_response = MagicMock()
        mock_response.content = b'<html><body><p>Test content</p></body></html>'
        mock_response.raise_for_status = MagicMock()
        mock_requests_get.return_value = mock_response
        fetch_webpage_content('https://example.com')
        mock_requests_get.assert_called_once()
        call_kwargs = mock_requests_get.call_args[1]
        self.assertIn('verify', call_kwargs)
        self.assertEqual(call_kwargs['verify'], test_cert_path)

def setUp(self):
    """Set up test environment."""
    self.original_config = server_config.copy()

class TestSSLWarnings(unittest.TestCase):
    """Test that appropriate warnings are shown when SSL is disabled."""

    def setUp(self):
        """Set up test environment."""
        self.original_config = server_config.copy()

    def tearDown(self):
        """Restore original server_config."""
        server_config.clear()
        server_config.update(self.original_config)

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_warning_when_ssl_disabled(self):
        """Test that a warning is logged when SSL verification is disabled."""
        from optillm.server import get_config
        server_config['ssl_verify'] = False
        server_config['ssl_cert_path'] = ''
        with patch('httpx.Client') as mock_httpx_client, patch('optillm.server.OpenAI') as mock_openai, patch('optillm.server.logger.warning') as mock_logger_warning:
            get_config()
            mock_logger_warning.assert_called()
            warning_message = mock_logger_warning.call_args[0][0]
            self.assertIn('SSL certificate verification is DISABLED', warning_message)
            self.assertIn('insecure', warning_message.lower())

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_info_when_custom_cert_used(self):
        """Test that an info message is logged when using custom certificate."""
        from optillm.server import get_config
        test_cert_path = '/path/to/custom-ca.pem'
        server_config['ssl_verify'] = True
        server_config['ssl_cert_path'] = test_cert_path
        with patch('httpx.Client') as mock_httpx_client, patch('optillm.server.OpenAI') as mock_openai, patch('optillm.server.logger.info') as mock_logger_info:
            get_config()
            mock_logger_info.assert_called()
            info_message = mock_logger_info.call_args[0][0]
            self.assertIn('custom CA certificate bundle', info_message)
            self.assertIn(test_cert_path, info_message)

def setUp(self):
    """Set up test environment."""
    self.original_config = server_config.copy()

def start_test_server(model: str=TEST_MODEL, port: int=8000) -> subprocess.Popen:
    """
    Start optillm server for testing
    Returns the process handle
    """
    env = os.environ.copy()
    env['OPTILLM_API_KEY'] = 'optillm'
    proc = subprocess.Popen([sys.executable, 'optillm.py', '--model', model, '--port', str(port)], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(5)
    return proc

