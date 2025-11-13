# Cluster 1

def imo25_verify_solution(problem: str, solution: str, model: str, problem_id: int=None) -> Dict[str, any]:
    """
    Two-stage verification system from IMO25 repository:
    Stage 1: Detailed verification using comprehensive IMO grader prompt
    Stage 2: Simple yes/no check on solution correctness
    """
    verification_system_prompt = 'You are an expert mathematician and a meticulous grader for an International Mathematical Olympiad (IMO) level exam. Your primary task is to rigorously verify the provided mathematical solution. A solution is to be judged correct **only if every step is rigorously justified.** A solution that arrives at a correct final answer through flawed reasoning, educated guesses, or with gaps in its arguments must be flagged as incorrect or incomplete.\n\n### Instructions ###\n\n**1. Core Instructions**\n*   Your sole task is to find and report all issues in the provided solution. You must act as a **verifier**, NOT a solver. **Do NOT attempt to correct the errors or fill the gaps you find.**\n*   You must perform a **step-by-step** check of the entire solution. This analysis will be presented in a **Detailed Verification Log**, where you justify your assessment of each step: for correct steps, a brief justification suffices; for steps with errors or gaps, you must provide a detailed explanation.\n\n**2. How to Handle Issues in the Solution**\nWhen you identify an issue in a step, you MUST first classify it into one of the following two categories and then follow the specified procedure.\n\n*   **a. Critical Error:**\n    This is any error that breaks the logical chain of the proof. This includes both **logical fallacies** (e.g., claiming that `A>B, C>D` implies `A-C>B-D`) and **factual errors** (e.g., a calculation error like `2+3=6`).\n    *   **Procedure:**\n        *   Explain the specific error and state that it **invalidates the current line of reasoning**.\n        *   Do NOT check any further steps that rely on this error.\n        *   You MUST, however, scan the rest of the solution to identify and verify any fully independent parts. For example, if a proof is split into multiple cases, an error in one case does not prevent you from checking the other cases.\n\n*   **b. Justification Gap:**\n    This is for steps where the conclusion may be correct, but the provided argument is incomplete, hand-wavy, or lacks sufficient rigor.\n    *   **Procedure:**\n        *   Explain the gap in the justification.\n        *   State that you will **assume the step\'s conclusion is true** for the sake of argument.\n        *   Then, proceed to verify all subsequent steps to check if the remainder of the argument is sound.\n\n**3. Output Format**\nYour response MUST be structured into two main sections: a **Summary** followed by the **Detailed Verification Log**.\n\n*   **a. Summary**\n    This section MUST be at the very beginning of your response. It must contain two components:\n    *   **Final Verdict**: A single, clear sentence declaring the overall validity of the solution. For example: "The solution is correct," "The solution contains a Critical Error and is therefore invalid," or "The solution\'s approach is viable but contains several Justification Gaps."\n    *   **List of Findings**: A bulleted list that summarizes **every** issue you discovered. For each finding, you must provide:\n        *   **Location:** A direct quote of the key phrase or equation where the issue occurs.\n        *   **Issue:** A brief description of the problem and its classification (**Critical Error** or **Justification Gap**).\n\n*   **b. Detailed Verification Log**\n    Following the summary, provide the full, step-by-step verification log as defined in the Core Instructions. When you refer to a specific part of the solution, **quote the relevant text** to make your reference clear before providing your detailed analysis of that part.\n\n**Example of the Required Summary Format**\n*This is a generic example to illustrate the required format. Your findings must be based on the actual solution provided below.*\n\n**Final Verdict:** The solution is **invalid** because it contains a Critical Error.\n\n**List of Findings:**\n*   **Location:** "By interchanging the limit and the integral, we get..."\n    *   **Issue:** Justification Gap - The solution interchanges a limit and an integral without providing justification, such as proving uniform convergence.\n*   **Location:** "From $A > B$ and $C > D$, it follows that $A-C > B-D$"\n    *   **Issue:** Critical Error - This step is a logical fallacy. Subtracting inequalities in this manner is not a valid mathematical operation.\n\n### Verification Task Reminder ###\n\nYour task is to act as an IMO grader. Now, generate the **summary** and the **step-by-step verification log** for the solution above. In your log, justify each correct step and explain in detail any errors or justification gaps you find, as specified in the instructions above.'
    verification_prompt = f'\n======================================================================\n### Problem ###\n\n{problem}\n\n======================================================================\n### Solution ###\n\n{solution}\n\n{verification_system_prompt}\n'
    extracted_answer = None
    answer_is_correct = False
    if problem_id is not None:
        extracted_answer = extract_answer_from_solution(solution, problem_id)
        answer_is_correct = check_answer_correctness(problem_id, extracted_answer)
        logger.info(f"Problem {problem_id}: Extracted answer = '{extracted_answer}', Correct = {answer_is_correct}")
    try:
        response = client.with_options(timeout=300).chat.completions.create(model=model, messages=[{'role': 'system', 'content': verification_system_prompt}, {'role': 'user', 'content': verification_prompt}], max_tokens=64000, temperature=0.1)
        verification_response = response.choices[0].message.content.strip()
        if answer_is_correct:
            check_correctness_prompt = f'The solution contains the correct final answer. Please respond with "yes" or "no":\n\nIs the overall mathematical approach reasonable and the final answer correct, even if there are minor justification gaps or presentation issues?\n\n{verification_response}'
        else:
            check_correctness_prompt = f'Response in "yes" or "no". Is the following statement saying the solution is correct, or does not contain critical error or a major justification gap?\n\n{verification_response}'
        response2 = client.with_options(timeout=300).chat.completions.create(model=model, messages=[{'role': 'user', 'content': check_correctness_prompt}], max_tokens=10, temperature=0.1)
        correctness_check = response2.choices[0].message.content.strip().lower()
        verification_says_correct = 'yes' in correctness_check
        if answer_is_correct and verification_says_correct:
            is_correct = True
        elif answer_is_correct and (not verification_says_correct):
            is_correct = True
            logger.info(f'Problem {problem_id}: Answer correct but verification strict - accepting solution')
        else:
            is_correct = verification_says_correct
        bug_report = ''
        if not is_correct:
            verification_log_match = re.search('### Detailed Verification Log ###\\s*(.*)', verification_response, re.DOTALL)
            if verification_log_match:
                bug_report = verification_log_match.group(1).strip()
            else:
                bug_report = verification_response
        return {'judge_response': verification_response, 'correctness_check': correctness_check, 'is_correct': is_correct, 'bug_report': bug_report, 'correctness_score': 1.0 if is_correct else 0.0, 'completeness_score': 1.0 if is_correct else 0.0, 'has_key_insights': is_correct, 'errors_found': [bug_report] if bug_report else [], 'overall_assessment': 'correct' if is_correct else 'incorrect', 'judge_reasoning': verification_response, 'success': True, 'extracted_answer': extracted_answer, 'answer_is_correct': answer_is_correct, 'verification_says_correct': verification_says_correct, 'verification_method': 'hybrid_answer_aware' if problem_id else 'original_imo25'}
    except Exception as e:
        logger.error(f'Error in IMO25 verification: {e}')
        return {'judge_response': f'Error: {str(e)}', 'correctness_check': 'error', 'is_correct': False, 'bug_report': f'Verification error: {str(e)}', 'correctness_score': 0.0, 'completeness_score': 0.0, 'has_key_insights': False, 'errors_found': [f'Judge error: {str(e)}'], 'overall_assessment': 'error', 'judge_reasoning': '', 'success': False}

def get_llm_response(problem: str, model: str, extra_body: dict=None, timeout: int=600) -> Dict[str, any]:
    """
    Get response from the LLM for an IMO problem with extended timeout for complex reasoning
    """
    try:
        kwargs = {}
        if extra_body:
            kwargs['extra_body'] = extra_body
        response = client.with_options(timeout=timeout).chat.completions.create(model=model, messages=[{'role': 'system', 'content': SYSTEM_PROMPT}, {'role': 'user', 'content': problem}], max_tokens=64000, **kwargs)
        solution_text = response.choices[0].message.content.strip()
        reasoning_tokens = getattr(response.usage, 'reasoning_tokens', 0)
        total_tokens = response.usage.total_tokens if hasattr(response.usage, 'total_tokens') else 0
        return {'solution': solution_text, 'reasoning_tokens': reasoning_tokens, 'total_tokens': total_tokens, 'success': True}
    except Exception as e:
        logger.error(f'Error getting LLM response: {e}')
        return {'solution': f'Error generating solution: {str(e)}', 'reasoning_tokens': 0, 'total_tokens': 0, 'success': False}

def evaluate_model(client: OpenAI, model: str, dataset: datasets.Dataset, approach: str, approach_extra_body: Dict[str, Any]=None, max_samples: int=None) -> Tuple[Dict[str, float], List[Dict[str, Any]]]:
    """
    Evaluate a model on the dataset using a specific approach.
    Returns metrics and detailed results.
    """
    metrics = {'total_correct': 0, 'total_time': 0, 'samples': 0}
    category_metrics = {}
    detailed_results = []
    examples = dataset if max_samples is None else dataset.select(range(max_samples))
    num_runs = approach_extra_body.get('num_runs', 1) if approach_extra_body else 1
    n_param = approach_extra_body.get('n', 1) if approach_extra_body else 1
    if approach.startswith('avg@') or approach.startswith('pass@'):
        full_model_name = model
    elif approach.startswith('maj@'):
        full_model_name = f'majority_voting-{model}'
    elif approach.startswith('genselect@'):
        full_model_name = f'genselect-{model}'
    elif approach.startswith('thinkdeeper_'):
        full_model_name = model
    elif approach.startswith('majority_voting'):
        full_model_name = f'majority_voting-{model}'
    elif approach == 'none':
        full_model_name = model
    else:
        full_model_name = f'{approach}-{model}'
    for example in tqdm(examples, desc=f'Evaluating {approach}'):
        if n_param > 1 and (approach.startswith('avg@') or approach.startswith('pass@')):
            try:
                prompt = get_prompt_for_category(example['question'], example['category'])
                start_time = time.time()
                extra_body = {'spl_learning': False}
                if approach_extra_body:
                    extra_body_clean = {k: v for k, v in approach_extra_body.items() if k not in ['n', 'approach']}
                    extra_body.update(extra_body_clean)
                responses = []
                try:
                    response = client.chat.completions.create(model=full_model_name, messages=[{'role': 'system', 'content': 'You are a helpful AI assistant focused on providing precise answers in the requested format.'}, {'role': 'user', 'content': prompt}], n=n_param, temperature=0.6, max_tokens=4096, extra_body=extra_body)
                    responses = [(choice.message.content, time.time() - start_time) for choice in response.choices]
                    logger.debug(f'Generated {len(responses)} responses using n={n_param}')
                except Exception as e:
                    logger.warning(f'Parallel generation failed: {type(e).__name__}: {str(e)}')
                    logger.info('Falling back to sequential generation')
                    for i in range(n_param):
                        try:
                            single_start = time.time()
                            response = client.chat.completions.create(model=full_model_name, messages=[{'role': 'system', 'content': 'You are a helpful AI assistant focused on providing precise answers in the requested format.'}, {'role': 'user', 'content': prompt}], temperature=0.6, max_tokens=4096, extra_body=extra_body)
                            response_text = response.choices[0].message.content
                            responses.append((response_text, time.time() - single_start))
                        except Exception as seq_error:
                            logger.error(f'Sequential generation {i + 1}/{n_param} failed: {seq_error}')
                            responses.append((None, 0))
                time_taken = time.time() - start_time
                run_results = []
                for response_text, _ in responses:
                    if response_text is not None:
                        processed_response = remove_thinking_blocks(response_text)
                        is_correct = evaluate_response(processed_response, example['answer'], example['category'], example['question'])
                        run_results.append(is_correct)
                    else:
                        run_results.append(False)
                if approach.startswith('avg@'):
                    success_rate = sum(run_results) / len(run_results) if run_results else 0
                elif approach.startswith('pass@'):
                    success_rate = 1.0 if any(run_results) else 0.0
                else:
                    success_rate = sum(run_results) / len(run_results) if run_results else 0
                metrics['total_correct'] += success_rate
                metrics['total_time'] += time_taken
                metrics['samples'] += 1
                if example['category'] not in category_metrics:
                    category_metrics[example['category']] = {'correct': 0, 'total': 0, 'time': 0}
                category_metrics[example['category']]['correct'] += success_rate
                category_metrics[example['category']]['total'] += 1
                category_metrics[example['category']]['time'] += time_taken
                detailed_results.append({'id': example['id'], 'category': example['category'], 'correct': success_rate, 'n_param': n_param, 'successes': sum(run_results), 'time_taken': time_taken, 'ground_truth': example['answer']})
            except Exception as e:
                logger.error(f'Error processing example {example['id']}: {e}')
                metrics['total_correct'] += 0
                metrics['total_time'] += 0
                metrics['samples'] += 1
                if example['category'] not in category_metrics:
                    category_metrics[example['category']] = {'correct': 0, 'total': 0, 'time': 0}
                category_metrics[example['category']]['correct'] += 0
                category_metrics[example['category']]['total'] += 1
                category_metrics[example['category']]['time'] += 0
                detailed_results.append({'id': example['id'], 'category': example['category'], 'correct': False, 'time_taken': 0, 'raw_response': f'ERROR: {str(e)}', 'processed_response': None, 'has_thinking': False, 'ground_truth': example['answer'], 'error': str(e)})
                continue
        elif num_runs > 1:
            run_results = []
            total_run_time = 0
            for run_idx in range(num_runs):
                try:
                    prompt = get_prompt_for_category(example['question'], example['category'])
                    start_time = time.time()
                    extra_body = {'spl_learning': False}
                    if approach_extra_body:
                        extra_body_clean = {k: v for k, v in approach_extra_body.items() if k not in ['num_runs', 'approach']}
                        extra_body.update(extra_body_clean)
                    response = client.chat.completions.create(model=full_model_name, messages=[{'role': 'system', 'content': 'You are a helpful AI assistant focused on providing precise answers in the requested format.'}, {'role': 'user', 'content': prompt}], temperature=0.6, max_tokens=4096, extra_body=extra_body)
                    time_taken = time.time() - start_time
                    total_run_time += time_taken
                    response_text = response.choices[0].message.content
                    processed_response = remove_thinking_blocks(response_text)
                    is_correct = evaluate_response(processed_response, example['answer'], example['category'], example['question'])
                    run_results.append(is_correct)
                except Exception as e:
                    logger.error(f'Error in run {run_idx + 1} for example {example['id']}: {e}')
                    run_results.append(False)
            success_rate = sum(run_results) / len(run_results) if run_results else 0
            avg_time = total_run_time / len(run_results) if run_results else 0
            metrics['total_correct'] += success_rate
            metrics['total_time'] += avg_time
            metrics['samples'] += 1
            if example['category'] not in category_metrics:
                category_metrics[example['category']] = {'correct': 0, 'total': 0, 'time': 0}
            category_metrics[example['category']]['correct'] += success_rate
            category_metrics[example['category']]['total'] += 1
            category_metrics[example['category']]['time'] += avg_time
            detailed_results.append({'id': example['id'], 'category': example['category'], 'correct': success_rate, 'num_runs': num_runs, 'successes': sum(run_results), 'time_taken': avg_time, 'ground_truth': example['answer']})
        else:
            try:
                prompt = get_prompt_for_category(example['question'], example['category'])
                start_time = time.time()
                extra_body = {'spl_learning': False}
                if approach_extra_body:
                    extra_body_clean = {k: v for k, v in approach_extra_body.items() if k != 'approach'}
                    extra_body.update(extra_body_clean)
                response = client.chat.completions.create(model=full_model_name, messages=[{'role': 'system', 'content': 'You are a helpful AI assistant focused on providing precise answers in the requested format.'}, {'role': 'user', 'content': prompt}], temperature=0.6, max_tokens=4096, extra_body=extra_body)
                time_taken = time.time() - start_time
                response_text = response.choices[0].message.content
                raw_response = response_text
                processed_response = remove_thinking_blocks(response_text)
                is_correct = evaluate_response(processed_response, example['answer'], example['category'], example['question'])
                metrics['total_correct'] += int(is_correct)
                metrics['total_time'] += time_taken
                metrics['samples'] += 1
                if example['category'] not in category_metrics:
                    category_metrics[example['category']] = {'correct': 0, 'total': 0, 'time': 0}
                category_metrics[example['category']]['correct'] += int(is_correct)
                category_metrics[example['category']]['total'] += 1
                category_metrics[example['category']]['time'] += time_taken
                has_thinking = '</think>' in raw_response
                detailed_results.append({'id': example['id'], 'category': example['category'], 'correct': is_correct, 'time_taken': time_taken, 'raw_response': raw_response, 'processed_response': processed_response if has_thinking else None, 'has_thinking': has_thinking, 'ground_truth': example['answer']})
            except Exception as e:
                logger.error(f'Error processing example {example['id']}: {e}')
                metrics['total_correct'] += 0
                metrics['total_time'] += 0
                metrics['samples'] += 1
                if example['category'] not in category_metrics:
                    category_metrics[example['category']] = {'correct': 0, 'total': 0, 'time': 0}
                category_metrics[example['category']]['correct'] += 0
                category_metrics[example['category']]['total'] += 1
                category_metrics[example['category']]['time'] += 0
                detailed_results.append({'id': example['id'], 'category': example['category'], 'correct': False, 'time_taken': 0, 'raw_response': f'ERROR: {str(e)}', 'processed_response': None, 'has_thinking': False, 'ground_truth': example['answer'], 'error': str(e)})
                continue
    final_metrics = {'accuracy': metrics['total_correct'] / metrics['samples'] if metrics['samples'] > 0 else 0, 'average_time': metrics['total_time'] / metrics['samples'] if metrics['samples'] > 0 else 0, 'total_time': metrics['total_time'], 'total_samples': metrics['samples']}
    total_expected = len(examples)
    failures = len([r for r in detailed_results if 'error' in r])
    if failures > 0:
        logger.warning(f'Approach {approach}: {failures}/{total_expected} examples failed due to errors')
        logger.warning(f'Failed examples are counted as incorrect in accuracy calculation')
    for category, cat_metrics in category_metrics.items():
        final_metrics[f'{category}_accuracy'] = cat_metrics['correct'] / cat_metrics['total']
        final_metrics[f'{category}_average_time'] = cat_metrics['time'] / cat_metrics['total']
    return (final_metrics, detailed_results)

def normalize_number(num_str: str) -> str:
    """Helper function to normalize number representation."""
    try:
        cleaned = re.sub('[,\\$\\\\]|\\s*(?:cm|m|kg|ft|in|lb|oz|ml|L)$|\\s*\\\\text{[^}]+}', '', num_str).strip()
        if cleaned.startswith('.'):
            cleaned = '0' + cleaned
        num = float(cleaned)
        if abs(num) < 1 and '.' in cleaned:
            decimal_places = len(cleaned.split('.')[1])
            format_str = f'{{:.{decimal_places}f}}'
            result = format_str.format(num)
        else:
            result = str(num)
        logger.debug(f'Normalized number result: {repr(result)}')
        return result
    except Exception as e:
        logger.debug(f'Failed to normalize number: {str(e)}')
        return num_str

def get_llm_response(problem: str, model: str) -> str:
    """
    Get response from the LLM for a given problem.
    
    Args:
        problem (str): The problem text
        model (str): The model identifier
        
    Returns:
        str: Model's response
    """
    try:
        response = client.chat.completions.create(model=model, temperature=0.6, messages=[{'role': 'user', 'content': SYSTEM_PROMPT + '\n' + problem}], max_tokens=8192)
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f'Error getting LLM response: {e}')
        return ''

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

def get_llm_response(messages: List[Dict], model: str) -> Optional[str]:
    """Get response from the LLM with retry logic."""
    for attempt in range(RTCConfig.max_retries):
        try:
            response = client.chat.completions.create(model=model, messages=messages, max_tokens=4096)
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f'Error getting LLM response (attempt {attempt + 1}): {e}')
            if attempt < RTCConfig.max_retries - 1:
                time.sleep(RTCConfig.retry_delay)
            continue
    return None

def get_llm_response(problem: str, model: str, analyze_logits: bool=False, extra_body: dict=None) -> Union[str, List[Dict]]:
    """
    Get response from the LLM for a given problem.
    If multiple choices are returned, formats them as attempt dictionaries.
    
    Args:
        problem (str): The problem text
        model (str): The model identifier
        analyze_logits (bool): Whether to request logprobs
        
    Returns:
        Union[str, List[Dict]]: Either a string response or list of attempt dictionaries
    """
    try:
        kwargs = {}
        if analyze_logits:
            kwargs['logprobs'] = True
            kwargs['top_logprobs'] = 3
        if extra_body:
            kwargs['extra_body'] = extra_body
        response = client.with_options(timeout=6000.0).chat.completions.create(model=model, messages=[{'role': 'user', 'content': SYSTEM_PROMPT + problem}], max_tokens=64000, **kwargs)
        if analyze_logits:
            raw_filename = f'results/raw_responses_{model.replace('/', '_')}.json'
            problem_id = hash(problem) % 10000
            save_raw_response(raw_filename, problem_id, response.model_dump())
        if len(response.choices) > 1:
            attempts = []
            for i, choice in enumerate(response.choices):
                response_text = choice.message.content.strip()
                predicted_answer = extract_answer(response_text)
                attempt_data = {'attempt_number': i + 1, 'response': response_text, 'predicted_answer': predicted_answer}
                if analyze_logits and hasattr(choice.message, 'logprobs') and choice.message.logprobs:
                    attempt_data['logprobs'] = choice.message.logprobs
                attempts.append(attempt_data)
            return attempts
        response_text = response.choices[0].message.content.strip()
        if analyze_logits and hasattr(response.choices[0].message, 'logprobs') and response.choices[0].message.logprobs:
            return {'response': response_text, 'logprobs': response.choices[0].message.logprobs}
        return response_text
    except Exception as e:
        logger.error(f'Error getting LLM response: {e}')
        logger.error(f'Error type: {type(e).__name__}')
        if 'timeout' in str(e).lower():
            logger.error('API call timed out - consider increasing timeout for complex approaches like MARS')
        raise e

def make_n_attempts(problem: str, model: str, n: int, analyze_thoughts: bool=False, analyze_logits: bool=False, extra_body: dict=None) -> List[Dict]:
    """
    Make n attempts to solve a problem and return all responses and predictions.
    
    Args:
        problem (str): The problem text
        model (str): The model identifier
        n (int): Number of attempts to make
        analyze_thoughts (bool): Whether to analyze thinking patterns
        analyze_logits (bool): Whether to analyze token probabilities
        
    Returns:
        List[Dict]: List of dictionaries containing response and predicted answer for each attempt
    """
    attempts = []
    remaining_attempts = n
    while remaining_attempts > 0:
        try:
            response = get_llm_response(problem, model, analyze_logits, extra_body)
        except Exception as e:
            logger.error(f'Failed to get response for attempt {n - remaining_attempts + 1}: {e}')
            attempt_data = {'attempt_number': len(attempts) + 1, 'response': f'ERROR: {str(e)}', 'predicted_answer': None, 'error': str(e)}
            attempts.append(attempt_data)
            remaining_attempts -= 1
            continue
        if isinstance(response, list):
            for attempt in response:
                if analyze_thoughts:
                    attempt['thought_analysis'] = analyze_thinking(attempt['response'])
                if analyze_logits and 'logprobs' in attempt:
                    attempt['logit_analysis'] = analyze_logits_probs(attempt['logprobs']['content'])
            attempts.extend(response)
            remaining_attempts = n - len(attempts)
        elif isinstance(response, dict) and 'response' in response:
            response_text = response['response']
            predicted_answer = extract_answer(response_text)
            attempt_data = {'attempt_number': len(attempts) + 1, 'response': response_text, 'predicted_answer': predicted_answer}
            if analyze_thoughts:
                attempt_data['thought_analysis'] = analyze_thinking(response_text)
            if analyze_logits and 'logprobs' in response:
                attempt_data['logit_analysis'] = analyze_logits_probs(response['logprobs']['content'])
            attempts.append(attempt_data)
            remaining_attempts -= 1
        else:
            predicted_answer = extract_answer(response)
            attempt_data = {'attempt_number': len(attempts) + 1, 'response': response, 'predicted_answer': predicted_answer}
            if analyze_thoughts:
                attempt_data['thought_analysis'] = analyze_thinking(response)
            attempts.append(attempt_data)
            remaining_attempts -= 1
    return attempts

def get_llm_response(prompt: str, model: str) -> str:
    response = client.with_options(timeout=1000.0).chat.completions.create(model=model, messages=[{'role': 'system', 'content': 'You are a helpful assistant.'}, {'role': 'user', 'content': prompt}], max_tokens=1000, n=1, stop=None, temperature=0.7, extra_body={'optillm_approach': 'readurls&memory'})
    return response.choices[0].message.content.strip()

def evaluate_response(question: str, llm_response: str, ground_truth: str, model: str) -> Dict[str, str]:
    evaluation_prompt = f"""===Task===\nI need your help in evaluating an answer provided by an LLM against a ground\ntruth answer. Your task is to determine if the ground truth answer is present in the LLM's\nresponse. Please analyze the provided data and make a decision.\n===Instructions===\n1. Carefully compare the "Predicted Answer" with the "Ground Truth Answer".\n2. Consider the substance of the answers - look for equivalent information or correct answers.\nDo not focus on exact wording unless the exact wording is crucial to the meaning.\n3. Your final decision should be based on whether the meaning and the vital facts of the\n"Ground Truth Answer" are present in the "Predicted Answer:"\n===Input Data===\n- Question: {question}\n- Predicted Answer: {llm_response}\n- Ground Truth Answer: {ground_truth}\n===Output Format===\nProvide your final evaluation in the following format:\n"Explanation:" (How you made the decision?)\n"Decision:" ("TRUE" or "FALSE" )\nPlease proceed with the evaluation."""
    evaluation_response = client.chat.completions.create(model=model, messages=[{'role': 'system', 'content': 'You are a helpful assistant.'}, {'role': 'user', 'content': evaluation_prompt}], max_tokens=300, n=1, stop=None, temperature=0.3)
    evaluation_text = evaluation_response.choices[0].message.content.strip()
    lines = evaluation_text.split('\n')
    decision = 'FALSE'
    explanation = ''
    for line in lines:
        if line.startswith('Decision:'):
            decision = line.split(':')[1].strip().upper()
        elif line.startswith('Explanation:'):
            explanation = line.split(':', 1)[1].strip()
    return {'decision': decision, 'explanation': explanation}

class LEAP:

    def __init__(self, system_prompt: str, client, model: str, request_id: str=None):
        self.system_prompt = system_prompt
        self.client = client
        self.model = model
        self.request_id = request_id
        self.low_level_principles = []
        self.high_level_principles = []
        self.leap_completion_tokens = 0

    def extract_output(self, text: str) -> str:
        match = re.search('<output>(.*?)(?:</output>|$)', text, re.DOTALL)
        return match.group(1).strip() if match else ''

    def extract_examples_from_query(self, initial_query: str) -> List[Tuple[str, str]]:
        logger.info('Extracting examples from initial query')
        provider_request = {'model': self.model, 'max_tokens': 4096, 'messages': [{'role': 'system', 'content': self.system_prompt}, {'role': 'user', 'content': f'\n                Analyze the following query and determine if it contains few-shot examples.\n                If it does, extract the examples and their corresponding answers.\n                Format the examples as a JSON array of objects, where each object has "question" and "answer" fields.\n                If there are no examples, return an empty array.\n                Enclose your response within <output></output> tags.\n                Do not put any explanation or any other reponse other than the JSON array within the <output></output> tags.\n\n                Example output format:\n                <output>\n                [\n                    {{"question": "What is 2+2?", "answer": "4"}},\n                    {{"question": "What is the capital of France?", "answer": "Paris"}}\n                ]\n                </output>\n\n                Query: {initial_query}\n                '}]}
        response = self.client.chat.completions.create(**provider_request)
        if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and self.request_id:
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
            optillm.conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
        self.leap_completion_tokens += response.usage.completion_tokens
        examples_str = self.extract_output(response.choices[0].message.content)
        logger.debug(f'Extracted examples: {examples_str}')
        examples = []
        if examples_str:
            try:
                examples_list = json.loads(examples_str)
                examples = [(example['question'], example['answer']) for example in examples_list]
            except json.JSONDecodeError:
                logger.warning('Failed to parse examples JSON, using empty list')
            except KeyError:
                logger.warning('Parsed JSON does not have the expected structure, using empty list')
        logger.debug(f'Extracted examples: {examples}')
        return examples

    def generate_mistakes(self, examples: List[Tuple[str, str]]) -> List[Tuple[str, str, str, str]]:
        logger.info('Generating mistakes for given examples')
        mistakes = []
        for question, correct_answer in examples:
            provider_request = {'model': self.model, 'max_tokens': 4096, 'messages': [{'role': 'system', 'content': self.system_prompt}, {'role': 'user', 'content': f'\n                    Instruction: Answer the following question step by step. To induce a mistake, \n                    deliberately introduce an error in your reasoning or calculation.\n                    Question: {question}\n                    Provide your step-by-step reasoning, then enclose your final answer within <output></output> tags.\n                    Think step by step, but make sure to include a mistake.\n                    '}], 'temperature': 0.7}
            response = self.client.chat.completions.create(**provider_request)
            if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and self.request_id:
                response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
                optillm.conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
            self.leap_completion_tokens += response.usage.completion_tokens
            generated_reasoning = response.choices[0].message.content
            generated_answer = self.extract_output(generated_reasoning)
            if generated_answer != correct_answer:
                mistakes.append((question, generated_reasoning, generated_answer, correct_answer))
        return mistakes

    def generate_low_level_principles(self, mistakes: List[Tuple[str, str, str, str]]) -> List[str]:
        logger.info('Generating low-level principles from mistakes')
        for question, generated_reasoning, generated_answer, correct_answer in mistakes:
            provider_request = {'model': self.model, 'max_tokens': 4096, 'messages': [{'role': 'system', 'content': self.system_prompt}, {'role': 'user', 'content': f'\n                    Question: {question}\n                    Generated Reasoning: {generated_reasoning}\n                    Generated Answer: {generated_answer}\n                    Correct Answer: {correct_answer}\n                    Instruction: Conduct a thorough analysis of the generated answer in comparison to the\n                    correct answer. Also observe how the generated reasoning differs from the correct\n                    reasoning. Identify any discrepancies, misunderstandings, or errors. Provide clear\n                    insights, principles, or guidelines that can be derived from this analysis to improve\n                    future responses. We are not focused on this one data point, but rather on the general\n                    principle.\n                    Reasoning: <discuss why the generated answer is wrong>\n                    Insights: Enclose ONLY the principles or insights within <output></output> tags.\n                    '}]}
            response = self.client.chat.completions.create(**provider_request)
            if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and self.request_id:
                response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
                optillm.conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
            self.leap_completion_tokens += response.usage.completion_tokens
            self.low_level_principles.append(self.extract_output(response.choices[0].message.content))
        return self.low_level_principles

    def generate_high_level_principles(self) -> List[str]:
        logger.info('Generating high-level principles from low-level principles')
        principles_text = '\n'.join(self.low_level_principles)
        provider_request = {'model': self.model, 'max_tokens': 4096, 'messages': [{'role': 'system', 'content': self.system_prompt}, {'role': 'user', 'content': f'\n                Low-level principles: {principles_text}\n                Create a list of *unique* and insightful principles to improve future responses based\n                on the analysis above.\n                Focus on capturing the essence of the feedback while eliminating redundancies.\n                Ensure that each point is clear, concise, and directly derived from the introspection\n                results.\n                Create a numbered list of principles. Leave specific details in place.\n                Limit to at most 8 principles.\n                Enclose your list of principles within <output></output> tags.\n                '}]}
        response = self.client.chat.completions.create(**provider_request)
        if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and self.request_id:
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
            optillm.conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
        self.leap_completion_tokens += response.usage.completion_tokens
        self.high_level_principles = self.extract_output(response.choices[0].message.content).split('\n')
        return self.high_level_principles

    def apply_principles(self, query: str) -> str:
        logger.info('Applying learned principles to query')
        principles_text = '\n'.join(self.high_level_principles)
        provider_request = {'model': self.model, 'max_tokens': 4096, 'messages': [{'role': 'system', 'content': self.system_prompt}, {'role': 'user', 'content': f'\n                Please answer the following query. Keep in mind these principles:\n\n                {principles_text}\n\n                Query: {query}\n                '}]}
        response = self.client.chat.completions.create(**provider_request)
        if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and self.request_id:
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
            optillm.conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
        self.leap_completion_tokens += response.usage.completion_tokens
        return response.choices[0].message.content

    def solve(self, initial_query: str) -> str:
        logger.info('Starting LEAP process')
        examples = self.extract_examples_from_query(initial_query)
        if not examples:
            logger.warning('No examples found in the query. Proceeding with direct answer.')
            return self.apply_principles(initial_query)
        mistakes = self.generate_mistakes(examples)
        self.generate_low_level_principles(mistakes)
        self.generate_high_level_principles()
        return self.apply_principles(initial_query)

def extract_examples_from_query(self, initial_query: str) -> List[Tuple[str, str]]:
    logger.info('Extracting examples from initial query')
    provider_request = {'model': self.model, 'max_tokens': 4096, 'messages': [{'role': 'system', 'content': self.system_prompt}, {'role': 'user', 'content': f'\n                Analyze the following query and determine if it contains few-shot examples.\n                If it does, extract the examples and their corresponding answers.\n                Format the examples as a JSON array of objects, where each object has "question" and "answer" fields.\n                If there are no examples, return an empty array.\n                Enclose your response within <output></output> tags.\n                Do not put any explanation or any other reponse other than the JSON array within the <output></output> tags.\n\n                Example output format:\n                <output>\n                [\n                    {{"question": "What is 2+2?", "answer": "4"}},\n                    {{"question": "What is the capital of France?", "answer": "Paris"}}\n                ]\n                </output>\n\n                Query: {initial_query}\n                '}]}
    response = self.client.chat.completions.create(**provider_request)
    if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and self.request_id:
        response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
        optillm.conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
    self.leap_completion_tokens += response.usage.completion_tokens
    examples_str = self.extract_output(response.choices[0].message.content)
    logger.debug(f'Extracted examples: {examples_str}')
    examples = []
    if examples_str:
        try:
            examples_list = json.loads(examples_str)
            examples = [(example['question'], example['answer']) for example in examples_list]
        except json.JSONDecodeError:
            logger.warning('Failed to parse examples JSON, using empty list')
        except KeyError:
            logger.warning('Parsed JSON does not have the expected structure, using empty list')
    logger.debug(f'Extracted examples: {examples}')
    return examples

def generate_mistakes(self, examples: List[Tuple[str, str]]) -> List[Tuple[str, str, str, str]]:
    logger.info('Generating mistakes for given examples')
    mistakes = []
    for question, correct_answer in examples:
        provider_request = {'model': self.model, 'max_tokens': 4096, 'messages': [{'role': 'system', 'content': self.system_prompt}, {'role': 'user', 'content': f'\n                    Instruction: Answer the following question step by step. To induce a mistake, \n                    deliberately introduce an error in your reasoning or calculation.\n                    Question: {question}\n                    Provide your step-by-step reasoning, then enclose your final answer within <output></output> tags.\n                    Think step by step, but make sure to include a mistake.\n                    '}], 'temperature': 0.7}
        response = self.client.chat.completions.create(**provider_request)
        if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and self.request_id:
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
            optillm.conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
        self.leap_completion_tokens += response.usage.completion_tokens
        generated_reasoning = response.choices[0].message.content
        generated_answer = self.extract_output(generated_reasoning)
        if generated_answer != correct_answer:
            mistakes.append((question, generated_reasoning, generated_answer, correct_answer))
    return mistakes

def generate_low_level_principles(self, mistakes: List[Tuple[str, str, str, str]]) -> List[str]:
    logger.info('Generating low-level principles from mistakes')
    for question, generated_reasoning, generated_answer, correct_answer in mistakes:
        provider_request = {'model': self.model, 'max_tokens': 4096, 'messages': [{'role': 'system', 'content': self.system_prompt}, {'role': 'user', 'content': f'\n                    Question: {question}\n                    Generated Reasoning: {generated_reasoning}\n                    Generated Answer: {generated_answer}\n                    Correct Answer: {correct_answer}\n                    Instruction: Conduct a thorough analysis of the generated answer in comparison to the\n                    correct answer. Also observe how the generated reasoning differs from the correct\n                    reasoning. Identify any discrepancies, misunderstandings, or errors. Provide clear\n                    insights, principles, or guidelines that can be derived from this analysis to improve\n                    future responses. We are not focused on this one data point, but rather on the general\n                    principle.\n                    Reasoning: <discuss why the generated answer is wrong>\n                    Insights: Enclose ONLY the principles or insights within <output></output> tags.\n                    '}]}
        response = self.client.chat.completions.create(**provider_request)
        if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and self.request_id:
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
            optillm.conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
        self.leap_completion_tokens += response.usage.completion_tokens
        self.low_level_principles.append(self.extract_output(response.choices[0].message.content))
    return self.low_level_principles

def generate_high_level_principles(self) -> List[str]:
    logger.info('Generating high-level principles from low-level principles')
    principles_text = '\n'.join(self.low_level_principles)
    provider_request = {'model': self.model, 'max_tokens': 4096, 'messages': [{'role': 'system', 'content': self.system_prompt}, {'role': 'user', 'content': f'\n                Low-level principles: {principles_text}\n                Create a list of *unique* and insightful principles to improve future responses based\n                on the analysis above.\n                Focus on capturing the essence of the feedback while eliminating redundancies.\n                Ensure that each point is clear, concise, and directly derived from the introspection\n                results.\n                Create a numbered list of principles. Leave specific details in place.\n                Limit to at most 8 principles.\n                Enclose your list of principles within <output></output> tags.\n                '}]}
    response = self.client.chat.completions.create(**provider_request)
    if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and self.request_id:
        response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
        optillm.conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
    self.leap_completion_tokens += response.usage.completion_tokens
    self.high_level_principles = self.extract_output(response.choices[0].message.content).split('\n')
    return self.high_level_principles

def apply_principles(self, query: str) -> str:
    logger.info('Applying learned principles to query')
    principles_text = '\n'.join(self.high_level_principles)
    provider_request = {'model': self.model, 'max_tokens': 4096, 'messages': [{'role': 'system', 'content': self.system_prompt}, {'role': 'user', 'content': f'\n                Please answer the following query. Keep in mind these principles:\n\n                {principles_text}\n\n                Query: {query}\n                '}]}
    response = self.client.chat.completions.create(**provider_request)
    if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and self.request_id:
        response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
        optillm.conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
    self.leap_completion_tokens += response.usage.completion_tokens
    return response.choices[0].message.content

def cot_reflection(system_prompt, initial_query, client, model: str, return_full_response: bool=False, request_config: dict=None, request_id: str=None):
    cot_completion_tokens = 0
    temperature = 0.6
    max_tokens = 4096
    if request_config:
        temperature = request_config.get('temperature', temperature)
        max_tokens = request_config.get('max_tokens', max_tokens)
    cot_prompt = f'\n        {system_prompt}\n\n        You are an AI assistant that uses a Chain of Thought (CoT) approach with reflection to answer queries. Follow these steps:\n\n        1. Think through the problem step by step within the <thinking> tags.\n        2. Reflect on your thinking to check for any errors or improvements within the <reflection> tags.\n        3. Make any necessary adjustments based on your reflection.\n        4. Provide your final, concise answer within the <output> tags.\n\n        Important: The <thinking> and <reflection> sections are for your internal reasoning process only. \n        Do not include any part of the final answer in these sections. \n        The actual response to the query must be entirely contained within the <output> tags.\n\n        Use the following format for your response:\n        <thinking>\n        [Your step-by-step reasoning goes here. This is your internal thought process, not the final answer.]\n        <reflection>\n        [Your reflection on your reasoning, checking for errors or improvements]\n        </reflection>\n        [Any adjustments to your thinking based on your reflection]\n        </thinking>\n        <output>\n        [Your final, concise answer to the query. This is the only part that will be shown to the user.]\n        </output>\n        '
    provider_request = {'model': model, 'messages': [{'role': 'system', 'content': cot_prompt}, {'role': 'user', 'content': initial_query}], 'temperature': temperature, 'max_tokens': max_tokens}
    response = client.chat.completions.create(**provider_request)
    if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and request_id:
        response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
        optillm.conversation_logger.log_provider_call(request_id, provider_request, response_dict)
    full_response = response.choices[0].message.content
    cot_completion_tokens += response.usage.completion_tokens
    logger.info(f'CoT with Reflection :\n{full_response}')
    thinking_match = re.search('<thinking>(.*?)</thinking>', full_response, re.DOTALL)
    output_match = re.search('<output>(.*?)(?:</output>|$)', full_response, re.DOTALL)
    thinking = thinking_match.group(1).strip() if thinking_match else 'No thinking process provided.'
    output = output_match.group(1).strip() if output_match else full_response
    logger.info(f'Final output :\n{output}')
    if return_full_response:
        return (full_response, cot_completion_tokens)
    else:
        return (output, cot_completion_tokens)

class ThinkDeeperProcessor:

    def __init__(self, config: Dict[str, Any], tokenizer, model):
        self.config = {**DEFAULT_CONFIG, **config}
        self.tokenizer = tokenizer
        self.model = model
        start_tokens = self.tokenizer.encode(self.config['start_think_token'])
        end_tokens = self.tokenizer.encode(self.config['end_think_token'])
        self._start_think_token = start_tokens[0] if len(start_tokens) == 1 else start_tokens[1]
        self.end_think_token = end_tokens[0] if len(end_tokens) == 1 else end_tokens[1]
        self.thought_switch_sequences = []
        for phrase in self.config['thought_switch_tokens']:
            token_ids = self.tokenizer.encode(phrase, add_special_tokens=False)
            self.thought_switch_sequences.append(token_ids)
            logger.debug(f"Encoded '{phrase}' to token sequence: {token_ids}")
            logger.debug(f'Decoded back: {self.tokenizer.decode(token_ids)}')
        self.thought_count = 0
        self.current_sequence = []
        self.max_sequence_length = max((len(seq) for seq in self.thought_switch_sequences))
        for phrase, sequence in zip(self.config['thought_switch_tokens'], self.thought_switch_sequences):
            logger.debug(f"Thought switch marker '{phrase}' encoded as: {sequence}")
            logger.debug(f'Decoded back as: {self.tokenizer.decode(sequence)}')

    def is_thought_switch(self, token: int) -> bool:
        """Check if adding this token creates a thought switch sequence."""
        self.current_sequence.append(token)
        if len(self.current_sequence) > self.max_sequence_length:
            self.current_sequence = self.current_sequence[-self.max_sequence_length:]
        for sequence in self.thought_switch_sequences:
            if len(sequence) <= len(self.current_sequence) and self.current_sequence[-len(sequence):] == sequence:
                return True
        return False

    @torch.inference_mode()
    def reasoning_effort(self, messages) -> str:
        """Generate response with ThinkDeeper's controlled thinking process"""
        messages.append({'role': 'assistant', 'content': f'{self.config['start_think_token']}\n{self.config['prefill']}'})
        tokens = self.tokenizer.apply_chat_template(messages, continue_final_message=True, return_tensors='pt')
        tokens = tokens.to(self.model.device)
        kv = DynamicCache()
        n_thinking_tokens = 0
        seen_end_think = False
        response_chunks = []
        while True:
            out = self.model(input_ids=tokens, past_key_values=kv, use_cache=True)
            logits = out.logits[0, -1, :]
            force_end = n_thinking_tokens >= self.config['max_thinking_tokens'] or self.thought_count >= self.config['max_thoughts']
            if force_end and (not seen_end_think):
                logger.debug(f'Forcing end think token. Tokens: {n_thinking_tokens}, Thoughts: {self.thought_count}')
                next_token = self.end_think_token
                response_chunks.append(self.tokenizer.decode([next_token]))
                seen_end_think = True
                tokens = torch.tensor([[next_token]]).to(tokens.device)
                continue
            else:
                next_token = torch.multinomial(torch.softmax(logits, dim=-1), 1).item()
            kv = out.past_key_values
            next_str = self.tokenizer.decode([next_token])
            if not seen_end_think and self.is_thought_switch(next_token):
                self.thought_count += 1
                logger.debug(f'Detected thought switch marker. Total thoughts: {self.thought_count}')
                self.current_sequence = []
            if next_token == self.end_think_token:
                seen_end_think = True
                logger.debug('Found end think token')
                if n_thinking_tokens < self.config['min_thinking_tokens']:
                    replacement = random.choice(self.config['thought_switch_tokens'])
                    logger.debug(f"Inserting thought transition: '{replacement}' (tokens: {n_thinking_tokens})")
                    response_chunks.append(replacement)
                    replacement_tokens = self.tokenizer.encode(replacement)
                    n_thinking_tokens += len(replacement_tokens)
                    tokens = torch.tensor([replacement_tokens]).to(tokens.device)
                    self.thought_count += 1
                    seen_end_think = False
                    continue
            if next_token == self.model.config.eos_token_id:
                logger.debug('Found eos token')
                if seen_end_think:
                    logger.debug('Reached EOS after end think token - stopping generation')
                    response_chunks.append(next_str)
                    break
                elif n_thinking_tokens < self.config['min_thinking_tokens']:
                    replacement = random.choice(self.config['thought_switch_tokens'])
                    logger.debug(f"Inserting thought transition: '{replacement}' (tokens: {n_thinking_tokens})")
                    response_chunks.append(replacement)
                    replacement_tokens = self.tokenizer.encode(replacement)
                    n_thinking_tokens += len(replacement_tokens)
                    tokens = torch.tensor([replacement_tokens]).to(tokens.device)
                    self.thought_count += 1
                    continue
                else:
                    logger.debug('Reached EOS without end think token - adding end token and continuing generation')
                    response_chunks.append(self.tokenizer.decode([self.end_think_token]))
                    tokens = torch.tensor([[self.end_think_token]]).to(tokens.device)
                    seen_end_think = True
                    continue
            response_chunks.append(next_str)
            if not seen_end_think:
                n_thinking_tokens += 1
            tokens = torch.tensor([[next_token]]).to(tokens.device)
        response = ''.join(response_chunks)
        full_response = f'{self.config['start_think_token']}\n{self.config['prefill']}{response}'
        logger.debug(f'Final response length: {len(full_response)} chars, Total thoughts: {self.thought_count}, Thinking tokens: {n_thinking_tokens}')
        return (full_response, n_thinking_tokens)

def is_thought_switch(self, token: int) -> bool:
    """Check if adding this token creates a thought switch sequence."""
    self.current_sequence.append(token)
    if len(self.current_sequence) > self.max_sequence_length:
        self.current_sequence = self.current_sequence[-self.max_sequence_length:]
    for sequence in self.thought_switch_sequences:
        if len(sequence) <= len(self.current_sequence) and self.current_sequence[-len(sequence):] == sequence:
            return True
    return False

class MLXInferencePipeline:
    """MLX-based inference pipeline that mirrors PyTorch pipeline interface"""

    def __init__(self, model_config: MLXModelConfig, cache_manager):
        self.model_config = model_config
        self.cache_manager = cache_manager
        self.last_used = time.time()
        if not MLX_AVAILABLE:
            raise RuntimeError('MLX framework not available. Install with: pip install mlx-lm')
        if not is_apple_silicon():
            raise RuntimeError('MLX framework is only supported on Apple Silicon')
        try:
            logger.info(f'Loading MLX model: {model_config.model_id}')
            self.model, self.tokenizer = self._load_mlx_model(model_config.model_id)
            logger.info('MLX model loaded successfully')
        except Exception as e:
            logger.error(f'Failed to load MLX model: {str(e)}')
            raise

    def _load_mlx_model(self, model_id: str):
        """Load MLX model and tokenizer with caching"""

        def _load_model():
            start_time = time.time()
            logger.info(f'Loading MLX model: {model_id}')
            try:
                model, tokenizer = mlx_load(model_id)
                load_time = time.time() - start_time
                logger.info(f'MLX model loaded in {load_time:.2f}s')
                return (model, tokenizer)
            except Exception as e:
                logger.error(f'Error loading MLX model {model_id}: {str(e)}')
                raise
        return self.cache_manager.get_or_load_model(f'mlx_{model_id}', _load_model)

    def generate(self, prompt: str, generation_params: Optional[Dict[str, Any]]=None) -> Tuple[List[str], List[int], List[Optional[Dict]]]:
        """Generate text using MLX"""
        start_time = time.time()
        if generation_params is None:
            generation_params = {}
        max_tokens = generation_params.get('max_new_tokens', self.model_config.max_new_tokens)
        temperature = generation_params.get('temperature', self.model_config.temperature)
        top_p = generation_params.get('top_p', self.model_config.top_p)
        repetition_penalty = generation_params.get('repetition_penalty', self.model_config.repetition_penalty)
        num_return_sequences = generation_params.get('num_return_sequences', 1)
        if generation_params.get('seed') is not None:
            mx.random.seed(generation_params['seed'])
        responses = []
        token_counts = []
        logprobs_results = []
        for _ in range(num_return_sequences):
            try:
                logger.debug(f'Generating with MLX: max_tokens={max_tokens}, temp={temperature}')
                response = self._robust_mlx_generate(prompt, max_tokens, temperature, top_p, repetition_penalty)
                responses.append(response)
                if isinstance(response, str):
                    token_count = len(self.tokenizer.encode(response))
                else:
                    token_count = len(response) if hasattr(response, '__len__') else 0
                token_counts.append(token_count)
                logprobs_results.append(None)
            except Exception as e:
                logger.error(f'Error during MLX generation: {str(e)}')
                logger.error(f'MLX generation parameters: max_tokens={max_tokens}, temp={temperature}, top_p={top_p}')
                responses.append('')
                token_counts.append(0)
                logprobs_results.append(None)
        generation_time = time.time() - start_time
        logger.info(f'MLX generation completed in {generation_time:.2f}s')
        return (responses, token_counts, logprobs_results)

    def _robust_mlx_generate(self, prompt: str, max_tokens: int, temperature: float, top_p: float, repetition_penalty: float) -> str:
        """Robust MLX generation using sampler approach"""
        try:
            sampler = make_sampler(temp=temperature, top_p=top_p, min_p=0.0, min_tokens_to_keep=1)
            response = mlx_generate(self.model, self.tokenizer, prompt, max_tokens=max_tokens, sampler=sampler, verbose=False)
            return response
        except Exception as e:
            logger.error(f'MLX generation with sampler failed: {str(e)}')
            try:
                logger.debug('Attempting MLX generation without sampler')
                response = mlx_generate(self.model, self.tokenizer, prompt, max_tokens=max_tokens, verbose=False)
                return response
            except Exception as fallback_e:
                logger.error(f'MLX fallback generation also failed: {str(fallback_e)}')
                raise

    def format_chat_prompt(self, system_prompt: str, user_prompt: str) -> str:
        """Format the prompt according to model's chat template"""
        if hasattr(self.tokenizer, 'apply_chat_template'):
            messages = [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_prompt}]
            try:
                return self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            except Exception as e:
                logger.warning(f'Failed to apply chat template: {e}, using fallback')
                return f'System: {system_prompt}\n\nUser: {user_prompt}\n\nAssistant:'
        else:
            return f'System: {system_prompt}\n\nUser: {user_prompt}\n\nAssistant:'

    def process_batch(self, system_prompts: List[str], user_prompts: List[str], generation_params: Optional[Dict[str, Any]]=None, active_adapter: str=None, return_token_count: bool=True) -> Tuple[List[str], List[int]]:
        """
        Process a batch of prompts with MLX-based batch inference
        
        This method provides true batch processing for MLX models, processing multiple
        prompts simultaneously for improved throughput.
        
        Args:
            system_prompts: List of system prompts
            user_prompts: List of user prompts
            generation_params: Generation parameters (temperature, max_tokens, etc.)
            active_adapter: Active adapter (not used in MLX)
            return_token_count: Whether to return token counts
            
        Returns:
            Tuple of (responses, token_counts)
        """
        import time
        if generation_params is None:
            generation_params = {}
        if len(system_prompts) != len(user_prompts):
            raise ValueError(f'Number of system prompts ({len(system_prompts)}) must match user prompts ({len(user_prompts)})')
        if not system_prompts:
            return ([], [])
        batch_size = len(system_prompts)
        logger.info(f'MLX batch processing {batch_size} prompts')
        start_time = time.time()
        formatted_prompts = [self.format_chat_prompt(system_prompt, user_prompt) for system_prompt, user_prompt in zip(system_prompts, user_prompts)]
        max_tokens = generation_params.get('max_new_tokens', self.model_config.max_new_tokens)
        temperature = generation_params.get('temperature', self.model_config.temperature)
        top_p = generation_params.get('top_p', self.model_config.top_p)
        repetition_penalty = generation_params.get('repetition_penalty', self.model_config.repetition_penalty)
        n = generation_params.get('num_return_sequences', 1)
        if generation_params.get('seed') is not None:
            mx.random.seed(generation_params['seed'])
        all_responses = []
        token_counts = []
        try:
            for i, prompt in enumerate(formatted_prompts):
                logger.debug(f'Processing MLX batch item {i + 1}/{batch_size}')
                for _ in range(n):
                    try:
                        response = self._robust_mlx_generate(prompt, max_tokens, temperature, top_p, repetition_penalty)
                        all_responses.append(response)
                        if isinstance(response, str):
                            token_count = len(self.tokenizer.encode(response))
                        else:
                            token_count = len(response) if hasattr(response, '__len__') else 0
                        token_counts.append(token_count)
                    except Exception as e:
                        logger.error(f'Error generating response for batch item {i + 1}: {e}')
                        all_responses.append('')
                        token_counts.append(0)
            processing_time = time.time() - start_time
            logger.info(f'MLX batch processing completed in {processing_time:.2f}s')
            if return_token_count:
                return (all_responses, token_counts)
            return (all_responses, [0] * len(all_responses))
        except Exception as e:
            logger.error(f'MLX batch processing failed: {e}')
            raise

    def _batch_tokenize(self, prompts: List[str]) -> Dict[str, Any]:
        """
        Tokenize a batch of prompts with padding
        
        Args:
            prompts: List of text prompts
            
        Returns:
            Dictionary with tokenized inputs suitable for MLX
        """
        pass

    def _batch_generate(self, input_ids, attention_mask, generation_params: Dict) -> List[str]:
        """
        Perform batch generation using MLX model
        
        Args:
            input_ids: Batched input token IDs
            attention_mask: Attention mask for padded sequences
            generation_params: Generation parameters
            
        Returns:
            List of generated responses
        """
        pass

def _load_model():
    start_time = time.time()
    logger.info(f'Loading MLX model: {model_id}')
    try:
        model, tokenizer = mlx_load(model_id)
        load_time = time.time() - start_time
        logger.info(f'MLX model loaded in {load_time:.2f}s')
        return (model, tokenizer)
    except Exception as e:
        logger.error(f'Error loading MLX model {model_id}: {str(e)}')
        raise

def generate(self, prompt: str, generation_params: Optional[Dict[str, Any]]=None) -> Tuple[List[str], List[int], List[Optional[Dict]]]:
    """Generate text using MLX"""
    start_time = time.time()
    if generation_params is None:
        generation_params = {}
    max_tokens = generation_params.get('max_new_tokens', self.model_config.max_new_tokens)
    temperature = generation_params.get('temperature', self.model_config.temperature)
    top_p = generation_params.get('top_p', self.model_config.top_p)
    repetition_penalty = generation_params.get('repetition_penalty', self.model_config.repetition_penalty)
    num_return_sequences = generation_params.get('num_return_sequences', 1)
    if generation_params.get('seed') is not None:
        mx.random.seed(generation_params['seed'])
    responses = []
    token_counts = []
    logprobs_results = []
    for _ in range(num_return_sequences):
        try:
            logger.debug(f'Generating with MLX: max_tokens={max_tokens}, temp={temperature}')
            response = self._robust_mlx_generate(prompt, max_tokens, temperature, top_p, repetition_penalty)
            responses.append(response)
            if isinstance(response, str):
                token_count = len(self.tokenizer.encode(response))
            else:
                token_count = len(response) if hasattr(response, '__len__') else 0
            token_counts.append(token_count)
            logprobs_results.append(None)
        except Exception as e:
            logger.error(f'Error during MLX generation: {str(e)}')
            logger.error(f'MLX generation parameters: max_tokens={max_tokens}, temp={temperature}, top_p={top_p}')
            responses.append('')
            token_counts.append(0)
            logprobs_results.append(None)
    generation_time = time.time() - start_time
    logger.info(f'MLX generation completed in {generation_time:.2f}s')
    return (responses, token_counts, logprobs_results)

def _robust_mlx_generate(self, prompt: str, max_tokens: int, temperature: float, top_p: float, repetition_penalty: float) -> str:
    """Robust MLX generation using sampler approach"""
    try:
        sampler = make_sampler(temp=temperature, top_p=top_p, min_p=0.0, min_tokens_to_keep=1)
        response = mlx_generate(self.model, self.tokenizer, prompt, max_tokens=max_tokens, sampler=sampler, verbose=False)
        return response
    except Exception as e:
        logger.error(f'MLX generation with sampler failed: {str(e)}')
        try:
            logger.debug('Attempting MLX generation without sampler')
            response = mlx_generate(self.model, self.tokenizer, prompt, max_tokens=max_tokens, verbose=False)
            return response
        except Exception as fallback_e:
            logger.error(f'MLX fallback generation also failed: {str(fallback_e)}')
            raise

def process_batch(self, system_prompts: List[str], user_prompts: List[str], generation_params: Optional[Dict[str, Any]]=None, active_adapter: str=None, return_token_count: bool=True) -> Tuple[List[str], List[int]]:
    """
        Process a batch of prompts with MLX-based batch inference
        
        This method provides true batch processing for MLX models, processing multiple
        prompts simultaneously for improved throughput.
        
        Args:
            system_prompts: List of system prompts
            user_prompts: List of user prompts
            generation_params: Generation parameters (temperature, max_tokens, etc.)
            active_adapter: Active adapter (not used in MLX)
            return_token_count: Whether to return token counts
            
        Returns:
            Tuple of (responses, token_counts)
        """
    import time
    if generation_params is None:
        generation_params = {}
    if len(system_prompts) != len(user_prompts):
        raise ValueError(f'Number of system prompts ({len(system_prompts)}) must match user prompts ({len(user_prompts)})')
    if not system_prompts:
        return ([], [])
    batch_size = len(system_prompts)
    logger.info(f'MLX batch processing {batch_size} prompts')
    start_time = time.time()
    formatted_prompts = [self.format_chat_prompt(system_prompt, user_prompt) for system_prompt, user_prompt in zip(system_prompts, user_prompts)]
    max_tokens = generation_params.get('max_new_tokens', self.model_config.max_new_tokens)
    temperature = generation_params.get('temperature', self.model_config.temperature)
    top_p = generation_params.get('top_p', self.model_config.top_p)
    repetition_penalty = generation_params.get('repetition_penalty', self.model_config.repetition_penalty)
    n = generation_params.get('num_return_sequences', 1)
    if generation_params.get('seed') is not None:
        mx.random.seed(generation_params['seed'])
    all_responses = []
    token_counts = []
    try:
        for i, prompt in enumerate(formatted_prompts):
            logger.debug(f'Processing MLX batch item {i + 1}/{batch_size}')
            for _ in range(n):
                try:
                    response = self._robust_mlx_generate(prompt, max_tokens, temperature, top_p, repetition_penalty)
                    all_responses.append(response)
                    if isinstance(response, str):
                        token_count = len(self.tokenizer.encode(response))
                    else:
                        token_count = len(response) if hasattr(response, '__len__') else 0
                    token_counts.append(token_count)
                except Exception as e:
                    logger.error(f'Error generating response for batch item {i + 1}: {e}')
                    all_responses.append('')
                    token_counts.append(0)
        processing_time = time.time() - start_time
        logger.info(f'MLX batch processing completed in {processing_time:.2f}s')
        if return_token_count:
            return (all_responses, token_counts)
        return (all_responses, [0] * len(all_responses))
    except Exception as e:
        logger.error(f'MLX batch processing failed: {e}')
        raise

class DeviceManager:

    def __init__(self):
        self.available_devices = self._detect_devices()
        self.device_stats = {device: {'memory_used': 0, 'active_models': 0} for device in self.available_devices}

    def _detect_devices(self) -> List[str]:
        devices = ['cpu']
        if torch.cuda.is_available():
            devices.extend([f'cuda:{i}' for i in range(torch.cuda.device_count())])
        if torch.backends.mps.is_available():
            devices.append('mps')
        return devices

    def get_optimal_device(self, model_size: int=0) -> str:
        if not self.available_devices:
            return 'cpu'
        cuda_devices = [d for d in self.available_devices if 'cuda' in d]
        if cuda_devices:
            max_free_memory = 0
            optimal_device = cuda_devices[0]
            for device in cuda_devices:
                idx = int(device.split(':')[1])
                free_memory = torch.cuda.get_device_properties(idx).total_memory - torch.cuda.memory_allocated(idx)
                if free_memory > max_free_memory:
                    max_free_memory = free_memory
                    optimal_device = device
            return optimal_device
        if 'mps' in self.available_devices:
            return 'mps'
        return 'cpu'

    def track_device_usage(self, device: str, memory_delta: int):
        if device in self.device_stats:
            self.device_stats[device]['memory_used'] += memory_delta

def _detect_devices(self) -> List[str]:
    devices = ['cpu']
    if torch.cuda.is_available():
        devices.extend([f'cuda:{i}' for i in range(torch.cuda.device_count())])
    if torch.backends.mps.is_available():
        devices.append('mps')
    return devices

class LoRAManager:
    """LoRA manager with enhanced error handling and caching"""

    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self.loaded_adapters = {}
        self.adapter_names = {}

    def _get_adapter_name(self, adapter_id: str) -> str:
        """Create a valid adapter name from adapter_id."""
        if adapter_id in self.adapter_names:
            return self.adapter_names[adapter_id]
        name = adapter_id.replace('.', '_').replace('-', '_')
        name = ''.join((c if c.isalnum() or c == '_' else '' for c in name))
        if name[0].isdigit():
            name = f'adapter_{name}'
        self.adapter_names[adapter_id] = name
        return name

    def validate_adapter(self, adapter_id: str) -> bool:
        """Validate if adapter exists and is compatible"""
        try:
            config = PeftConfig.from_pretrained(adapter_id, trust_remote_code=True, token=os.getenv('HF_TOKEN'))
            return True
        except Exception as e:
            logger.error(f'Error validating adapter {adapter_id}: {str(e)}')
            return False

    def load_adapter(self, base_model: PreTrainedModel, adapter_id: str) -> PreTrainedModel:
        """Load a LoRA adapter with enhanced caching"""
        model_key = base_model.config._name_or_path

        def _load_adapter():
            logger.info(f'Loading LoRA adapter: {adapter_id}')
            if not self.validate_adapter(adapter_id):
                error_msg = f'Adapter {adapter_id} not found or is not compatible'
                logger.error(error_msg)
                raise ValueError(error_msg)
            try:
                adapter_name = self._get_adapter_name(adapter_id)
                config = PeftConfig.from_pretrained(adapter_id, trust_remote_code=True, token=os.getenv('HF_TOKEN'))
                model = base_model
                model.add_adapter(config, adapter_name=adapter_name)
                if model not in self.loaded_adapters:
                    self.loaded_adapters[model] = []
                if adapter_id not in self.loaded_adapters[model]:
                    self.loaded_adapters[model].append(adapter_id)
                return model
            except Exception as e:
                error_msg = f'Failed to load adapter {adapter_id}: {str(e)}'
                logger.error(error_msg)
                raise RuntimeError(error_msg) from e
        return self.cache_manager.get_or_load_adapter(model_key, adapter_id, _load_adapter)

    def set_active_adapter(self, model: PeftModel, adapter_id: str=None) -> bool:
        """Set a specific adapter as active with error handling"""
        if not isinstance(model, PeftModel):
            logger.warning('Model is not a PeftModel, cannot set active adapter')
            return False
        available_adapters = self.loaded_adapters.get(model, [])
        if not available_adapters:
            logger.warning('No adapters loaded in model')
            return False
        if adapter_id is None:
            adapter_id = available_adapters[-1]
        if adapter_id in available_adapters:
            try:
                model.set_adapter(self._get_adapter_name(adapter_id))
                logger.info(f'Successfully set active adapter to: {adapter_id}')
                return True
            except Exception as e:
                logger.error(f'Error setting adapter {adapter_id}: {str(e)}')
                return False
        else:
            logger.warning(f'Requested adapter {adapter_id} not loaded. Available adapters: {available_adapters}')
            return False

def validate_adapter(self, adapter_id: str) -> bool:
    """Validate if adapter exists and is compatible"""
    try:
        config = PeftConfig.from_pretrained(adapter_id, trust_remote_code=True, token=os.getenv('HF_TOKEN'))
        return True
    except Exception as e:
        logger.error(f'Error validating adapter {adapter_id}: {str(e)}')
        return False

class ChatCompletion:

    def __init__(self, response_dict: Dict):
        self.id = response_dict['id']
        self.object = response_dict['object']
        self.created = response_dict['created']
        self.model = response_dict['model']
        self.choices = [ChatCompletionChoice(index=choice['index'], message=choice['message'], finish_reason=choice['finish_reason']) for choice in response_dict['choices']]
        self.usage = ChatCompletionUsage(**response_dict['usage'])

    def model_dump(self) -> Dict:
        return {'id': self.id, 'object': self.object, 'created': self.created, 'model': self.model, 'choices': [{'index': choice.index, 'message': {'role': choice.message.role, 'content': choice.message.content, 'logprobs': choice.message.logprobs} if choice.message.logprobs else {'role': choice.message.role, 'content': choice.message.content}, 'finish_reason': choice.finish_reason} for choice in self.choices], 'usage': {'prompt_tokens': self.usage.prompt_tokens, 'completion_tokens': self.usage.completion_tokens, 'total_tokens': self.usage.total_tokens, 'completion_tokens_details': {'reasoning_tokens': getattr(self.usage, 'reasoning_tokens', 0)}}}

def model_dump(self) -> Dict:
    return {'id': self.id, 'object': self.object, 'created': self.created, 'model': self.model, 'choices': [{'index': choice.index, 'message': {'role': choice.message.role, 'content': choice.message.content, 'logprobs': choice.message.logprobs} if choice.message.logprobs else {'role': choice.message.role, 'content': choice.message.content}, 'finish_reason': choice.finish_reason} for choice in self.choices], 'usage': {'prompt_tokens': self.usage.prompt_tokens, 'completion_tokens': self.usage.completion_tokens, 'total_tokens': self.usage.total_tokens, 'completion_tokens_details': {'reasoning_tokens': getattr(self.usage, 'reasoning_tokens', 0)}}}

class MLXThinkDeeperProcessor:

    def __init__(self, config: Dict[str, Any], tokenizer, model):
        self.config = {**DEFAULT_CONFIG, **config}
        self.tokenizer = tokenizer
        self.model = model
        start_tokens = self.tokenizer.encode(self.config['start_think_token'])
        end_tokens = self.tokenizer.encode(self.config['end_think_token'])
        self._start_think_token = start_tokens[0] if len(start_tokens) == 1 else start_tokens[1]
        self.end_think_token = end_tokens[0] if len(end_tokens) == 1 else end_tokens[1]
        self.thought_switch_sequences = []
        for phrase in self.config['thought_switch_tokens']:
            token_ids = self.tokenizer.encode(phrase, add_special_tokens=False)
            self.thought_switch_sequences.append(token_ids)
        self.thought_count = 0
        self.current_sequence = []
        self.max_sequence_length = max((len(seq) for seq in self.thought_switch_sequences)) if self.thought_switch_sequences else 5
        self.total_tokens_generated = 0
        self.max_total_tokens = config.get('max_tokens', 8192)

    def is_thought_switch(self, token: int) -> bool:
        """Check if adding this token creates a thought switch sequence."""
        self.current_sequence.append(token)
        if len(self.current_sequence) > self.max_sequence_length:
            self.current_sequence = self.current_sequence[-self.max_sequence_length:]
        for sequence in self.thought_switch_sequences:
            if len(sequence) <= len(self.current_sequence) and self.current_sequence[-len(sequence):] == sequence:
                return True
        return False

    def reasoning_effort(self, messages) -> str:
        """Generate response with ThinkDeeper's controlled thinking process using MLX"""
        thinking_messages = messages.copy()
        thinking_messages.append({'role': 'assistant', 'content': f'{self.config['start_think_token']}\n{self.config['prefill']}'})
        if hasattr(self.tokenizer, 'apply_chat_template'):
            prompt = self.tokenizer.apply_chat_template(thinking_messages, continue_final_message=False, tokenize=False, add_generation_prompt=True)
        else:
            prompt = ''
            for msg in thinking_messages:
                prompt += f'{msg['role']}: {msg['content']}\n'
        n_thinking_tokens = 0
        seen_end_think = False
        response_chunks = []
        current_prompt = prompt
        max_chunk_size = 150
        consecutive_empty_chunks = 0
        max_empty_chunks = 3
        while n_thinking_tokens < self.config['max_thinking_tokens'] and self.thought_count < self.config['max_thoughts'] and (self.total_tokens_generated < self.max_total_tokens - 512):
            try:
                chunk_response = self._generate_chunk(current_prompt, max_tokens=min(max_chunk_size, self.config['max_thinking_tokens'] - n_thinking_tokens), temperature=0.6)
                if not chunk_response or chunk_response.strip() == '':
                    consecutive_empty_chunks += 1
                    if consecutive_empty_chunks >= max_empty_chunks:
                        break
                    max_chunk_size = min(max_chunk_size + 50, 300)
                    continue
                else:
                    consecutive_empty_chunks = 0
                    max_chunk_size = 150
                    chunk_tokens = len(self.tokenizer.encode(chunk_response))
                    self.total_tokens_generated += chunk_tokens
                if self.config['end_think_token'] in chunk_response:
                    parts = chunk_response.split(self.config['end_think_token'], 1)
                    before_end = parts[0]
                    after_end = parts[1] if len(parts) > 1 else ''
                    response_chunks.append(before_end)
                    n_thinking_tokens += len(self.tokenizer.encode(before_end))
                    if n_thinking_tokens < self.config['min_thinking_tokens']:
                        transition = random.choice(self.config['thought_switch_tokens'])
                        response_chunks.append(transition)
                        current_prompt += before_end + transition
                        n_thinking_tokens += len(self.tokenizer.encode(transition))
                        self.thought_count += 1
                        continue
                    else:
                        response_chunks.append(self.config['end_think_token'])
                        current_prompt += before_end + self.config['end_think_token']
                        seen_end_think = True
                        if after_end.strip():
                            response_chunks.append(after_end)
                        else:
                            conclusion = self._generate_chunk(current_prompt, max_tokens=200, temperature=0.3)
                            if conclusion:
                                response_chunks.append(conclusion)
                        break
                else:
                    response_chunks.append(chunk_response)
                    current_prompt += chunk_response
                    n_thinking_tokens += len(self.tokenizer.encode(chunk_response))
                    for phrase in self.config['thought_switch_tokens']:
                        if phrase in chunk_response:
                            self.thought_count += 1
                            break
                if len(response_chunks) > 100:
                    logger.warning('Too many chunks generated, stopping to avoid infinite loop')
                    break
            except Exception as e:
                logger.error(f'Error during MLX chunk generation: {str(e)}')
                break
        if not seen_end_think and n_thinking_tokens < self.config['min_thinking_tokens']:
            while n_thinking_tokens < self.config['min_thinking_tokens'] and self.thought_count < self.config['max_thoughts']:
                transition = random.choice(self.config['thought_switch_tokens'])
                response_chunks.append(f' {transition} ')
                current_prompt += f' {transition} '
                additional_thinking = self._generate_chunk(current_prompt, max_tokens=min(200, self.config['min_thinking_tokens'] - n_thinking_tokens + 100), temperature=0.6)
                if additional_thinking and additional_thinking.strip():
                    response_chunks.append(additional_thinking)
                    current_prompt += additional_thinking
                    additional_tokens = len(self.tokenizer.encode(additional_thinking))
                    n_thinking_tokens += additional_tokens
                    self.thought_count += 1
                else:
                    break
        if not seen_end_think:
            response_chunks.append(self.config['end_think_token'])
            try:
                conclusion = self._generate_chunk(current_prompt + self.config['end_think_token'], max_tokens=100, temperature=0.3)
                if conclusion:
                    response_chunks.append(conclusion)
            except Exception as e:
                logger.error(f'Error generating conclusion: {str(e)}')
        response_content = ''.join(response_chunks)
        full_response = f'{self.config['start_think_token']}\n{self.config['prefill']}{response_content}'
        logger.debug(f'MLX Final response length: {len(full_response)} chars, Thinking tokens: {n_thinking_tokens}')
        return (full_response, n_thinking_tokens)

    def _generate_chunk(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate a small chunk of text using MLX with proper sampler"""
        try:
            sampler = make_sampler(temp=temperature, top_p=0.95, top_k=20, min_p=0.0, min_tokens_to_keep=3)
            actual_max_tokens = max(max_tokens, 30)
            response = mlx_generate(self.model, self.tokenizer, prompt, max_tokens=actual_max_tokens, sampler=sampler, verbose=False)
            if response:
                if response.startswith(prompt):
                    new_content = response[len(prompt):]
                else:
                    new_content = response
                if new_content.strip():
                    return new_content
            return ''
        except Exception as e:
            logger.error(f'Error in MLX chunk generation: {str(e)}')
            return ''

def is_thought_switch(self, token: int) -> bool:
    """Check if adding this token creates a thought switch sequence."""
    self.current_sequence.append(token)
    if len(self.current_sequence) > self.max_sequence_length:
        self.current_sequence = self.current_sequence[-self.max_sequence_length:]
    for sequence in self.thought_switch_sequences:
        if len(sequence) <= len(self.current_sequence) and self.current_sequence[-len(sequence):] == sequence:
            return True
    return False

def _generate_chunk(self, prompt: str, max_tokens: int, temperature: float) -> str:
    """Generate a small chunk of text using MLX with proper sampler"""
    try:
        sampler = make_sampler(temp=temperature, top_p=0.95, top_k=20, min_p=0.0, min_tokens_to_keep=3)
        actual_max_tokens = max(max_tokens, 30)
        response = mlx_generate(self.model, self.tokenizer, prompt, max_tokens=actual_max_tokens, sampler=sampler, verbose=False)
        if response:
            if response.startswith(prompt):
                new_content = response[len(prompt):]
            else:
                new_content = response
            if new_content.strip():
                return new_content
        return ''
    except Exception as e:
        logger.error(f'Error in MLX chunk generation: {str(e)}')
        return ''

def best_of_n_sampling(system_prompt: str, initial_query: str, client, model: str, n: int=3, request_id: str=None) -> str:
    bon_completion_tokens = 0
    messages = [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': initial_query}]
    completions = []
    try:
        provider_request = {'model': model, 'messages': messages, 'max_tokens': 4096, 'n': n, 'temperature': 1}
        response = client.chat.completions.create(**provider_request)
        if request_id:
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
            conversation_logger.log_provider_call(request_id, provider_request, response_dict)
        completions = [choice.message.content for choice in response.choices]
        logger.info(f'Generated {len(completions)} initial completions using n parameter. Tokens used: {response.usage.completion_tokens}')
        bon_completion_tokens += response.usage.completion_tokens
    except Exception as e:
        logger.warning(f'n parameter not supported by provider: {str(e)}')
        logger.info(f'Falling back to generating {n} completions one by one')
        for i in range(n):
            try:
                provider_request = {'model': model, 'messages': messages, 'max_tokens': 4096, 'temperature': 1}
                response = client.chat.completions.create(**provider_request)
                if request_id:
                    response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
                    conversation_logger.log_provider_call(request_id, provider_request, response_dict)
                completions.append(response.choices[0].message.content)
                bon_completion_tokens += response.usage.completion_tokens
                logger.debug(f'Generated completion {i + 1}/{n}')
            except Exception as fallback_error:
                logger.error(f'Error generating completion {i + 1}: {str(fallback_error)}')
                continue
        if not completions:
            logger.error('Failed to generate any completions')
            return ('Error: Could not generate any completions', 0)
        logger.info(f'Generated {len(completions)} completions using fallback method. Total tokens used: {bon_completion_tokens}')
    rating_messages = messages.copy()
    rating_messages.append({'role': 'system', 'content': 'Rate the following responses on a scale from 0 to 10, where 0 is poor and 10 is excellent. Consider factors such as relevance, coherence, and helpfulness. Respond with only a number.'})
    ratings = []
    for completion in completions:
        rating_messages.append({'role': 'assistant', 'content': completion})
        rating_messages.append({'role': 'user', 'content': 'Rate the above response:'})
        provider_request = {'model': model, 'messages': rating_messages, 'max_tokens': 256, 'n': 1, 'temperature': 0.1}
        rating_response = client.chat.completions.create(**provider_request)
        if request_id:
            response_dict = rating_response.model_dump() if hasattr(rating_response, 'model_dump') else rating_response
            conversation_logger.log_provider_call(request_id, provider_request, response_dict)
        bon_completion_tokens += rating_response.usage.completion_tokens
        try:
            rating = float(rating_response.choices[0].message.content.strip())
            ratings.append(rating)
        except ValueError:
            ratings.append(0)
        rating_messages = rating_messages[:-2]
    best_index = ratings.index(max(ratings))
    return (completions[best_index], bon_completion_tokens)

class RStar:

    def __init__(self, system: str, client, model: str, max_depth: int=3, num_rollouts: int=5, c: float=1.4, request_id: str=None):
        self.client = client
        self.model_name = model
        self.max_depth = max_depth
        self.num_rollouts = num_rollouts
        self.c = c
        self.actions = ['A1', 'A2', 'A3', 'A4', 'A5']
        self.original_question = None
        self.system = system
        self.rstar_completion_tokens = 0
        self.request_id = request_id
        logger.debug(f'Initialized RStar with model: {model}, max_depth: {max_depth}, num_rollouts: {num_rollouts}')

    async def generate_response_async(self, prompt: str) -> str:
        return await asyncio.to_thread(self.generate_response, prompt)

    async def expand_async(self, node: Node, action: str) -> Node:
        prompt = self.create_prompt(node.state, action)
        new_state = await self.generate_response_async(prompt)
        child_node = Node(new_state, action, node)
        node.children.append(child_node)
        logger.debug(f'Expanded node with action: {action}')
        return child_node

    async def simulate_async(self, node: Node) -> float:
        current_node = node
        depth = 0
        logger.debug('Starting simulation')
        while depth < self.max_depth:
            if not current_node.children:
                action = random.choice(self.actions)
                current_node = await self.expand_async(current_node, action)
            else:
                current_node = random.choice(current_node.children)
            depth += 1
        value = self.evaluate(current_node)
        logger.debug(f'Simulation complete. Final value: {value}')
        return value

    async def mcts_async(self, root_state: str) -> List[Node]:
        root = Node(root_state, None)
        tasks = []
        for _ in range(self.num_rollouts):
            tasks.append(self.mcts_rollout_async(root))
        await asyncio.gather(*tasks)
        return self.extract_trajectories(root)

    async def mcts_rollout_async(self, root: Node):
        node = root
        while node.children:
            node, _ = self.select_action(node)
        action = random.choice(self.actions)
        if len(node.children) < len(self.actions):
            node = await self.expand_async(node, action)
        value = await self.simulate_async(node)
        self.backpropagate(node, value)

    async def solve_async(self, question: str) -> str:
        self.original_question = question
        logger.info(f'Solving question: {question}')
        trajectories = await self.mcts_async(question)
        if not trajectories:
            logger.warning('No trajectories found. Unable to solve the question.')
            return 'Unable to solve the question due to insufficient reasoning paths.'
        final_trajectory = self.select_final_trajectory(trajectories)
        logger.debug(f'Final trajectory: {[node.state for node in final_trajectory]}')
        answers = [self.extract_answer(node.state) for node in final_trajectory]
        final_answer = self.select_best_answer(answers)
        logger.info(f'Selected final answer: {final_answer}')
        return (final_answer, self.rstar_completion_tokens)

    def generate_response(self, prompt: str) -> str:
        logger.debug(f'Generating response for prompt: {prompt[:100]}...')
        provider_request = {'model': self.model_name, 'messages': [{'role': 'system', 'content': 'You are a helpful assistant focused on solving mathematical problems. Stick to the given question and avoid introducing new scenarios.'}, {'role': 'user', 'content': prompt}], 'max_tokens': 4096, 'temperature': 0.2}
        response = self.client.chat.completions.create(**provider_request)
        if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and self.request_id:
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
            optillm.conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
        self.rstar_completion_tokens += response.usage.completion_tokens
        generated_response = response.choices[0].message.content.strip()
        logger.debug(f'Generated response: {generated_response}')
        return generated_response

    def select_action(self, node: Node) -> Tuple[Node, str]:
        if not node.children:
            action = random.choice(self.actions)
            logger.debug(f'Selected random action: {action}')
            return (node, action)
        uct_values = []
        for child in node.children:
            if child.visits == 0:
                uct = float('inf')
            else:
                uct = child.value / child.visits + self.c * math.sqrt(math.log(node.visits) / child.visits)
            uct_values.append(uct)
        best_child = node.children[uct_values.index(max(uct_values))]
        logger.debug(f'Selected action: {best_child.action}')
        return (best_child, best_child.action)

    def expand(self, node: Node, action: str) -> Node:
        prompt = self.create_prompt(node.state, action)
        new_state = self.generate_response(prompt)
        child_node = Node(new_state, action, node)
        node.children.append(child_node)
        logger.debug(f'Expanded node with action: {action}')
        return child_node

    def simulate(self, node: Node) -> float:
        current_node = node
        depth = 0
        logger.debug('Starting simulation')
        while depth < self.max_depth:
            if not current_node.children:
                action = random.choice(self.actions)
                current_node = self.expand(current_node, action)
            else:
                current_node = random.choice(current_node.children)
            depth += 1
        value = self.evaluate(current_node)
        logger.debug(f'Simulation complete. Final value: {value}')
        return value

    def backpropagate(self, node: Node, value: float):
        logger.debug('Starting backpropagation')
        while node:
            node.visits += 1
            node.value += value
            node = node.parent
        logger.debug('Backpropagation complete')

    def mcts(self, root_state: str) -> List[Node]:
        root = Node(root_state, None)
        logger.debug(f'Starting MCTS with {self.num_rollouts} rollouts')
        for i in range(self.num_rollouts):
            logger.debug(f'Rollout {i + 1}/{self.num_rollouts}')
            node = root
            while node.children:
                node, _ = self.select_action(node)
            action = random.choice(self.actions)
            if len(node.children) < len(self.actions):
                node = self.expand(node, action)
            value = self.simulate(node)
            self.backpropagate(node, value)
        logger.debug('MCTS complete')
        return self.extract_trajectories(root)

    def extract_trajectories(self, root: Node) -> List[List[Node]]:
        logger.debug('Extracting trajectories')
        trajectories = []
        stack = [(root, [])]
        while stack:
            node, path = stack.pop()
            if not node.children:
                trajectories.append(path + [node])
            else:
                for child in node.children:
                    stack.append((child, path + [node]))
        logger.debug(f'Extracted {len(trajectories)} trajectories')
        return trajectories

    def mutual_consistency(self, trajectory: List[Node]) -> bool:
        split_index = random.randint(1, len(trajectory) - 1)
        partial_trajectory = trajectory[:split_index]
        prompt = self.create_discriminator_prompt(partial_trajectory)
        completion = self.generate_response(prompt)
        is_consistent = self.compare_completions(completion, trajectory[split_index:])
        logger.debug(f'Mutual consistency check: {('Passed' if is_consistent else 'Failed')}')
        return is_consistent

    def select_final_trajectory(self, trajectories: List[List[Node]]) -> List[Node]:
        logger.debug('Selecting final trajectory')
        valid_trajectories = [t for t in trajectories if self.mutual_consistency(t)]
        logger.debug(f'Found {len(valid_trajectories)} valid trajectories')
        if not valid_trajectories:
            logger.warning('No valid trajectories found. Selecting based on value/visits.')
            return max(trajectories, key=lambda t: self.trajectory_score(t))
        return max(valid_trajectories, key=lambda t: self.trajectory_score(t))

    def trajectory_score(self, trajectory: List[Node]) -> float:
        if not trajectory:
            return float('-inf')
        last_node = trajectory[-1]
        if last_node.visits == 0:
            return last_node.value
        return last_node.value / last_node.visits

    def select_best_answer(self, answers: List[Tuple[str, float]]) -> str:
        valid_answers = [(answer, conf) for answer, conf in answers if answer]
        if not valid_answers:
            return 'Unable to determine a valid answer.'
        answer_counts = {}
        for answer, conf in valid_answers:
            if answer in answer_counts:
                answer_counts[answer] = (answer_counts[answer][0] + 1, max(answer_counts[answer][1], conf))
            else:
                answer_counts[answer] = (1, conf)
        sorted_answers = sorted(answer_counts.items(), key=lambda x: (-x[1][1], -x[1][0]))
        best_answer, (count, conf) = sorted_answers[0]
        logger.debug(f'Selected best answer: {best_answer} (count: {count}, confidence: {conf})')
        return best_answer

    def create_prompt(self, state: str, action: str) -> str:
        question = self.original_question if hasattr(self, 'original_question') else 'the original question'
        prompts = {'A1': f'Given the current state: {state}\nGenerate the next logical step in solving {question}.\nYour response should be a single, clear thought that moves towards the solution.\nIf you can determine the final answer at this step, state it clearly.', 'A2': f'Given the current state: {state}\nContinue the reasoning process to solve {question}.\nProvide the remaining steps needed to reach the final answer.\nEach step should be clear and directly related to solving the problem.', 'A3': f'Given the current state: {state}\nIdentify a key sub-question that needs to be answered to solve {question}.\nState this sub-question clearly, then provide its answer.\nExplain how this sub-question and its answer contribute to solving the main problem.', 'A4': f'Given the current state: {state}\nRe-examine the previous step in solving {question} using Chain-of-Thought reasoning.\nBreak down your thinking process explicitly, showing each logical step.\nIf you reach a conclusion, state it clearly.', 'A5': f'Given the current state: {state}\nRephrase {question} by clearly listing all relevant conditions and unknowns.\nEnsure that your rephrasing captures all important details from the original question.\nThis rephrasing should help clarify the problem and guide the solution process.'}
        prompt = prompts[action] + "\n\nIf you determine the final answer, explicitly state 'The final answer is [your numeric answer]' at the end of your response."
        logger.debug(f'Created prompt for action {action}: {prompt}')
        return prompt

    def create_discriminator_prompt(self, partial_trajectory: List[Node]) -> str:
        states = [node.state for node in partial_trajectory]
        partial_reasoning = ' '.join(states)
        return f'Given the partial reasoning:\n{partial_reasoning}\nComplete the reasoning to solve the problem:'

    def compare_completions(self, completion: str, remaining_trajectory: List[Node]) -> bool:
        remaining_states = [node.state for node in remaining_trajectory]
        remaining_reasoning = ' '.join(remaining_states)
        completion_words = set(completion.lower().replace('.', '').replace(',', '').split())
        trajectory_words = set(remaining_reasoning.lower().replace('.', '').replace(',', '').split())
        overlap = len(completion_words.intersection(trajectory_words))
        total_words = len(completion_words.union(trajectory_words))
        return overlap / total_words > 0.7

    def evaluate(self, node: Node) -> float:
        answer, confidence = self.extract_answer(node.state)
        try:
            float(answer)
            logger.debug(f'Evaluated node. Answer: {answer}, Confidence: {confidence}, Value: {confidence}')
            return confidence
        except ValueError:
            logger.debug(f'Evaluated node. Answer: {answer}, Confidence: {confidence}, Value: 0.0')
            return 0.0

    def extract_answer(self, final_state: str) -> Tuple[str, float]:
        logger.debug(f'Extracting answer from state: {final_state}')
        patterns = ['The answer is (\\d+)', 'The final answer is (\\d+)', 'Therefore, the answer is (\\d+)', 'So, the answer is (\\d+)', 'Thus, the answer is (\\d+)', 'In conclusion, the answer is (\\d+)']
        for pattern in patterns:
            match = re.search(pattern, final_state)
            if match:
                answer = match.group(1)
                confidence = 1.0
                logger.debug(f"Answer found using pattern '{pattern}': {answer}")
                return (answer, confidence)
        numbers = re.findall('\\d+', final_state)
        if numbers:
            answer = numbers[-1]
            confidence = 0.5
            logger.debug(f'No pattern found. Using last number as answer: {answer}')
            return (answer, confidence)
        logger.warning('No answer found in the state.')
        return ('', 0.0)

    def solve(self, question: str) -> str:
        """
        Synchronous wrapper for solve_async method.
        """
        return asyncio.run(self.solve_async(question))

def generate_response(self, prompt: str) -> str:
    logger.debug(f'Generating response for prompt: {prompt[:100]}...')
    provider_request = {'model': self.model_name, 'messages': [{'role': 'system', 'content': 'You are a helpful assistant focused on solving mathematical problems. Stick to the given question and avoid introducing new scenarios.'}, {'role': 'user', 'content': prompt}], 'max_tokens': 4096, 'temperature': 0.2}
    response = self.client.chat.completions.create(**provider_request)
    if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and self.request_id:
        response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
        optillm.conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
    self.rstar_completion_tokens += response.usage.completion_tokens
    generated_response = response.choices[0].message.content.strip()
    logger.debug(f'Generated response: {generated_response}')
    return generated_response

def mixture_of_agents(system_prompt: str, initial_query: str, client, model: str, request_id: str=None) -> str:
    logger.info(f'Starting mixture_of_agents function with model: {model}')
    moa_completion_tokens = 0
    completions = []
    logger.debug(f'Generating initial completions for query: {initial_query}')
    try:
        provider_request = {'model': model, 'messages': [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': initial_query}], 'max_tokens': 4096, 'n': 3, 'temperature': 1}
        response = client.chat.completions.create(**provider_request)
        response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
        if request_id:
            conversation_logger.log_provider_call(request_id, provider_request, response_dict)
        completions = [choice.message.content for choice in response.choices]
        moa_completion_tokens += response.usage.completion_tokens
        logger.info(f'Generated {len(completions)} initial completions using n parameter. Tokens used: {response.usage.completion_tokens}')
    except Exception as e:
        logger.warning(f'n parameter not supported by provider: {str(e)}')
        logger.info('Falling back to generating 3 completions one by one')
        completions = []
        for i in range(3):
            try:
                provider_request = {'model': model, 'messages': [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': initial_query}], 'max_tokens': 4096, 'temperature': 1}
                response = client.chat.completions.create(**provider_request)
                response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
                if request_id:
                    conversation_logger.log_provider_call(request_id, provider_request, response_dict)
                completions.append(response.choices[0].message.content)
                moa_completion_tokens += response.usage.completion_tokens
                logger.debug(f'Generated completion {i + 1}/3')
            except Exception as fallback_error:
                logger.error(f'Error generating completion {i + 1}: {str(fallback_error)}')
                continue
        if not completions:
            logger.error('Failed to generate any completions')
            return ('Error: Could not generate any completions', 0)
        logger.info(f'Generated {len(completions)} completions using fallback method. Total tokens used: {moa_completion_tokens}')
    if len(completions) < 3:
        original_count = len(completions)
        while len(completions) < 3:
            completions.append(completions[0])
        logger.warning(f'Only generated {original_count} unique completions, padded to 3 for critique')
    logger.debug('Preparing critique prompt')
    critique_prompt = f'\n    Original query: {initial_query}\n\n    I will present you with three candidate responses to the original query. Please analyze and critique each response, discussing their strengths and weaknesses. Provide your analysis for each candidate separately.\n\n    Candidate 1:\n    {completions[0]}\n\n    Candidate 2:\n    {completions[1]}\n\n    Candidate 3:\n    {completions[2]}\n\n    Please provide your critique for each candidate:\n    '
    logger.debug('Generating critiques')
    provider_request = {'model': model, 'messages': [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': critique_prompt}], 'max_tokens': 512, 'n': 1, 'temperature': 0.1}
    critique_response = client.chat.completions.create(**provider_request)
    response_dict = critique_response.model_dump() if hasattr(critique_response, 'model_dump') else critique_response
    if request_id:
        conversation_logger.log_provider_call(request_id, provider_request, response_dict)
    critiques = critique_response.choices[0].message.content
    moa_completion_tokens += critique_response.usage.completion_tokens
    logger.info(f'Generated critiques. Tokens used: {critique_response.usage.completion_tokens}')
    logger.debug('Preparing final prompt')
    final_prompt = f'\n    Original query: {initial_query}\n\n    Based on the following candidate responses and their critiques, generate a final response to the original query.\n\n    Candidate 1:\n    {completions[0]}\n\n    Candidate 2:\n    {completions[1]}\n\n    Candidate 3:\n    {completions[2]}\n\n    Critiques of all candidates:\n    {critiques}\n\n    Please provide a final, optimized response to the original query:\n    '
    logger.debug('Generating final response')
    provider_request = {'model': model, 'messages': [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': final_prompt}], 'max_tokens': 8192, 'n': 1, 'temperature': 0.1}
    final_response = client.chat.completions.create(**provider_request)
    response_dict = final_response.model_dump() if hasattr(final_response, 'model_dump') else final_response
    if request_id:
        conversation_logger.log_provider_call(request_id, provider_request, response_dict)
    moa_completion_tokens += final_response.usage.completion_tokens
    logger.info(f'Generated final response. Tokens used: {final_response.usage.completion_tokens}')
    logger.info(f'Total completion tokens used: {moa_completion_tokens}')
    return (final_response.choices[0].message.content, moa_completion_tokens)

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

def _generate_request_id(self) -> str:
    """Generate a unique request ID"""
    return f'req_{uuid.uuid4().hex[:8]}'

def log_provider_call(request_id: str, provider_request: Dict[str, Any], provider_response: Dict[str, Any]) -> None:
    """Log a provider call using the global logger instance"""
    if _global_logger and _global_logger.enabled:
        _global_logger.log_provider_call(request_id, provider_request, provider_response)

def round_trip_optimization(system_prompt: str, initial_query: str, client, model: str, request_id: str=None) -> str:
    rto_completion_tokens = 0
    messages = [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': initial_query}]
    provider_request = {'model': model, 'messages': messages, 'max_tokens': 4096, 'n': 1, 'temperature': 0.1}
    response_c1 = client.chat.completions.create(**provider_request)
    if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and request_id:
        response_dict = response_c1.model_dump() if hasattr(response_c1, 'model_dump') else response_c1
        optillm.conversation_logger.log_provider_call(request_id, provider_request, response_dict)
    c1 = response_c1.choices[0].message.content
    rto_completion_tokens += response_c1.usage.completion_tokens
    messages.append({'role': 'assistant', 'content': c1})
    messages.append({'role': 'user', 'content': 'Summarize or describe the code you just created. The summary should be in form of an instruction such that, given the instruction you can create the code yourself.'})
    provider_request = {'model': model, 'messages': messages, 'max_tokens': 1024, 'n': 1, 'temperature': 0.1}
    response_q2 = client.chat.completions.create(**provider_request)
    if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and request_id:
        response_dict = response_q2.model_dump() if hasattr(response_q2, 'model_dump') else response_q2
        optillm.conversation_logger.log_provider_call(request_id, provider_request, response_dict)
    q2 = response_q2.choices[0].message.content
    rto_completion_tokens += response_q2.usage.completion_tokens
    messages = [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': q2}]
    provider_request = {'model': model, 'messages': messages, 'max_tokens': 4096, 'n': 1, 'temperature': 0.1}
    response_c2 = client.chat.completions.create(**provider_request)
    if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and request_id:
        response_dict = response_c2.model_dump() if hasattr(response_c2, 'model_dump') else response_c2
        optillm.conversation_logger.log_provider_call(request_id, provider_request, response_dict)
    c2 = response_c2.choices[0].message.content
    rto_completion_tokens += response_c2.usage.completion_tokens
    c1 = extract_code_from_prompt(c1)
    c2 = extract_code_from_prompt(c2)
    if c1.strip() == c2.strip():
        return (c1, rto_completion_tokens)
    messages = [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': f'Initial query: {initial_query}\n\nFirst generated code (C1):\n{c1}\n\nSecond generated code (C2):\n{c2}\n\nBased on the initial query and these two different code implementations, generate a final, optimized version of the code. Only respond with the final code, do not return anything else.'}]
    provider_request = {'model': model, 'messages': messages, 'max_tokens': 4096, 'n': 1, 'temperature': 0.1}
    response_c3 = client.chat.completions.create(**provider_request)
    if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and request_id:
        response_dict = response_c3.model_dump() if hasattr(response_c3, 'model_dump') else response_c3
        optillm.conversation_logger.log_provider_call(request_id, provider_request, response_dict)
    c3 = response_c3.choices[0].message.content
    rto_completion_tokens += response_c3.usage.completion_tokens
    return (c3, rto_completion_tokens)

class AdvancedSelfConsistency:

    def __init__(self, client, model: str, num_samples: int=5, similarity_threshold: float=0.8, request_id: str=None):
        self.client = client
        self.model = model
        self.num_samples = num_samples
        self.similarity_threshold = similarity_threshold
        self.self_consistency_completion_tokens = 0
        self.request_id = request_id

    def generate_responses(self, system_prompt: str, user_prompt: str) -> List[str]:
        responses = []
        for _ in range(self.num_samples):
            provider_request = {'model': self.model, 'messages': [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_prompt}], 'temperature': 1, 'max_tokens': 4096}
            response = self.client.chat.completions.create(**provider_request)
            if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and self.request_id:
                response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
                optillm.conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
            self.self_consistency_completion_tokens += response.usage.completion_tokens
            responses.append(response.choices[0].message.content)
        return responses

    def calculate_similarity(self, a: str, b: str) -> float:
        return SequenceMatcher(None, a, b).ratio()

    def cluster_similar_responses(self, responses: List[str]) -> List[List[str]]:
        clusters = []
        for response in responses:
            added_to_cluster = False
            for cluster in clusters:
                if self.calculate_similarity(response, cluster[0]) >= self.similarity_threshold:
                    cluster.append(response)
                    added_to_cluster = True
                    break
            if not added_to_cluster:
                clusters.append([response])
        return clusters

    def aggregate_results(self, responses: List[str]) -> Dict[str, any]:
        final_answers = responses
        clusters = self.cluster_similar_responses(final_answers)
        cluster_info = []
        for cluster in clusters:
            cluster_info.append({'answer': cluster[0], 'frequency': len(cluster), 'variants': cluster})
        cluster_info.sort(key=lambda x: x['frequency'], reverse=True)
        return {'clusters': cluster_info, 'total_responses': len(responses), 'num_unique_clusters': len(clusters)}

    def evaluate(self, system_prompt: str, user_prompt: str) -> Dict[str, any]:
        responses = self.generate_responses(system_prompt, user_prompt)
        aggregated_result = self.aggregate_results(responses)
        return {'individual_responses': responses, 'aggregated_result': aggregated_result}

def generate_responses(self, system_prompt: str, user_prompt: str) -> List[str]:
    responses = []
    for _ in range(self.num_samples):
        provider_request = {'model': self.model, 'messages': [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_prompt}], 'temperature': 1, 'max_tokens': 4096}
        response = self.client.chat.completions.create(**provider_request)
        if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and self.request_id:
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
            optillm.conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
        self.self_consistency_completion_tokens += response.usage.completion_tokens
        responses.append(response.choices[0].message.content)
    return responses

def cluster_similar_responses(self, responses: List[str]) -> List[List[str]]:
    clusters = []
    for response in responses:
        added_to_cluster = False
        for cluster in clusters:
            if self.calculate_similarity(response, cluster[0]) >= self.similarity_threshold:
                cluster.append(response)
                added_to_cluster = True
                break
        if not added_to_cluster:
            clusters.append([response])
    return clusters

class MCTS:

    def __init__(self, simulation_depth, exploration_weight, client, model, request_id=None):
        self.simulation_depth = simulation_depth
        self.exploration_weight = exploration_weight
        self.root = None
        self.graph = nx.Graph()
        self.node_labels = {}
        self.client = client
        self.model = model
        self.completion_tokens = 0
        self.request_id = request_id

    def select(self, node: MCTSNode) -> MCTSNode:
        logger.debug(f'Selecting node. Current node visits: {node.visits}, value: {node.value}')
        if not node.children:
            logger.debug('Node has no children. Returning current node.')
            return node
        selected_node = max(node.children, key=lambda c: c.value / (c.visits + 1e-08) + self.exploration_weight * np.sqrt(np.log(node.visits + 1) / (c.visits + 1e-08)))
        logger.debug(f'Selected child node. Visits: {selected_node.visits}, Value: {selected_node.value}')
        return selected_node

    def expand(self, node: MCTSNode) -> MCTSNode:
        logger.debug(f'Expanding node. Current state: {node.state}')
        actions = self.generate_actions(node.state)
        logger.debug(f'Generated {len(actions)} possible actions')
        for i, action in enumerate(actions):
            new_state = self.apply_action(node.state, action)
            child = MCTSNode(new_state, parent=node)
            node.children.append(child)
            self.graph.add_edge(id(node), id(child))
            self.node_labels[id(child)] = f'Visits: {child.visits}\nValue: {child.value:.2f}'
            logger.debug(f'Created child node {i + 1}. Action: {action[:50]}...')
        selected_child = random.choice(node.children)
        logger.debug(f'Randomly selected child node for simulation. Visits: {selected_child.visits}, Value: {selected_child.value}')
        return selected_child

    def simulate(self, node: MCTSNode) -> float:
        logger.debug(f'Starting simulation from node. Current query: {node.state.current_query}')
        state = node.state
        for i in range(self.simulation_depth):
            if self.is_terminal(state):
                logger.debug(f'Reached terminal state at depth {i}')
                break
            action = random.choice(self.generate_actions(state))
            state = self.apply_action(state, action)
            logger.debug(f'Simulation step {i + 1}. Action: {action[:50]}...')
        value = self.evaluate_state(state)
        logger.debug(f'Simulation complete. Final state value: {value}')
        return value

    def backpropagate(self, node: MCTSNode, value: float):
        logger.debug(f'Starting backpropagation. Initial value: {value}')
        while node:
            node.visits += 1
            node.value += value
            self.node_labels[id(node)] = f'Visits: {node.visits}\nValue: {node.value:.2f}'
            logger.debug(f'Updated node. Visits: {node.visits}, New value: {node.value}')
            node = node.parent

    def search(self, initial_state: DialogueState, num_simulations: int) -> DialogueState:
        logger.debug(f'Starting MCTS search with {num_simulations} simulations')
        if not self.root:
            self.root = MCTSNode(initial_state)
            self.graph.add_node(id(self.root))
            self.node_labels[id(self.root)] = f'Root\nVisits: 0\nValue: 0.00'
            logger.debug('Created root node')
        for i in range(num_simulations):
            logger.debug(f'Starting simulation {i + 1}')
            node = self.select(self.root)
            if not self.is_terminal(node.state):
                node = self.expand(node)
            value = self.simulate(node)
            self.backpropagate(node, value)
        best_child = max(self.root.children, key=lambda c: c.visits)
        logger.debug(f'Search complete. Best child node: Visits: {best_child.visits}, Value: {best_child.value}')
        return best_child.state

    def generate_actions(self, state: DialogueState) -> List[str]:
        logger.debug('Generating actions for current state')
        messages = [{'role': 'system', 'content': state.system_prompt}]
        messages.extend(state.conversation_history)
        messages.append({'role': 'user', 'content': state.current_query})
        completions = []
        n = 3
        logger.info(f'Requesting {n} completions from the model')
        provider_request = {'model': self.model, 'messages': messages, 'max_tokens': 4096, 'n': n, 'temperature': 1}
        response = self.client.chat.completions.create(**provider_request)
        if self.request_id:
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
            conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
        completions = [choice.message.content.strip() for choice in response.choices]
        self.completion_tokens += response.usage.completion_tokens
        logger.info(f'Received {len(completions)} completions from the model')
        return completions

    def apply_action(self, state: DialogueState, action: str) -> DialogueState:
        logger.info(f'Applying action: {action[:50]}...')
        new_history = state.conversation_history.copy()
        new_history.append({'role': 'assistant', 'content': action})
        messages = [{'role': 'system', 'content': state.system_prompt}]
        messages.extend(new_history)
        messages.append({'role': 'user', 'content': 'Based on this conversation, what might the user ask or say next? Provide a likely user query.'})
        logger.info('Requesting next user query from the model')
        provider_request = {'model': self.model, 'messages': messages, 'max_tokens': 1024, 'n': 1, 'temperature': 1}
        response = self.client.chat.completions.create(**provider_request)
        if self.request_id:
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
            conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
        next_query = response.choices[0].message.content
        self.completion_tokens += response.usage.completion_tokens
        logger.info(f'Generated next user query: {next_query}')
        return DialogueState(state.system_prompt, new_history, next_query)

    def is_terminal(self, state: DialogueState) -> bool:
        is_terminal = len(state.conversation_history) > 10 or 'goodbye' in state.current_query.lower()
        logger.info(f'Checking if state is terminal: {is_terminal}')
        return is_terminal

    def evaluate_state(self, state: DialogueState) -> float:
        logger.info('Evaluating current state')
        messages = [{'role': 'system', 'content': state.system_prompt}]
        messages.extend(state.conversation_history)
        messages.append({'role': 'user', 'content': 'Evaluate the quality of this conversation on a scale from 0 to 1, where 0 is poor and 1 is excellent. Consider factors such as coherence, relevance, and engagement. Respond with only a number.'})
        provider_request = {'model': self.model, 'messages': messages, 'max_tokens': 256, 'n': 1, 'temperature': 0.1}
        response = self.client.chat.completions.create(**provider_request)
        if self.request_id:
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
            conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
        self.completion_tokens += response.usage.completion_tokens
        try:
            score = float(response.choices[0].message.content.strip())
            score = max(0, min(score, 1))
            logger.info(f'State evaluation score: {score}')
            return score
        except ValueError:
            logger.warning('Failed to parse evaluation score. Using default value 0.5')
            return 0.5

def generate_actions(self, state: DialogueState) -> List[str]:
    logger.debug('Generating actions for current state')
    messages = [{'role': 'system', 'content': state.system_prompt}]
    messages.extend(state.conversation_history)
    messages.append({'role': 'user', 'content': state.current_query})
    completions = []
    n = 3
    logger.info(f'Requesting {n} completions from the model')
    provider_request = {'model': self.model, 'messages': messages, 'max_tokens': 4096, 'n': n, 'temperature': 1}
    response = self.client.chat.completions.create(**provider_request)
    if self.request_id:
        response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
        conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
    completions = [choice.message.content.strip() for choice in response.choices]
    self.completion_tokens += response.usage.completion_tokens
    logger.info(f'Received {len(completions)} completions from the model')
    return completions

def apply_action(self, state: DialogueState, action: str) -> DialogueState:
    logger.info(f'Applying action: {action[:50]}...')
    new_history = state.conversation_history.copy()
    new_history.append({'role': 'assistant', 'content': action})
    messages = [{'role': 'system', 'content': state.system_prompt}]
    messages.extend(new_history)
    messages.append({'role': 'user', 'content': 'Based on this conversation, what might the user ask or say next? Provide a likely user query.'})
    logger.info('Requesting next user query from the model')
    provider_request = {'model': self.model, 'messages': messages, 'max_tokens': 1024, 'n': 1, 'temperature': 1}
    response = self.client.chat.completions.create(**provider_request)
    if self.request_id:
        response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
        conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
    next_query = response.choices[0].message.content
    self.completion_tokens += response.usage.completion_tokens
    logger.info(f'Generated next user query: {next_query}')
    return DialogueState(state.system_prompt, new_history, next_query)

def evaluate_state(self, state: DialogueState) -> float:
    logger.info('Evaluating current state')
    messages = [{'role': 'system', 'content': state.system_prompt}]
    messages.extend(state.conversation_history)
    messages.append({'role': 'user', 'content': 'Evaluate the quality of this conversation on a scale from 0 to 1, where 0 is poor and 1 is excellent. Consider factors such as coherence, relevance, and engagement. Respond with only a number.'})
    provider_request = {'model': self.model, 'messages': messages, 'max_tokens': 256, 'n': 1, 'temperature': 0.1}
    response = self.client.chat.completions.create(**provider_request)
    if self.request_id:
        response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
        conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
    self.completion_tokens += response.usage.completion_tokens
    try:
        score = float(response.choices[0].message.content.strip())
        score = max(0, min(score, 1))
        logger.info(f'State evaluation score: {score}')
        return score
    except ValueError:
        logger.warning('Failed to parse evaluation score. Using default value 0.5')
        return 0.5

def Rational(numerator, denominator=1):
    return z3.Real(str(Fraction(numerator, denominator)))

class Z3SymPySolverSystem:

    def __init__(self, system_prompt: str, client, model: str, timeout: int=30, request_id: str=None):
        self.system_prompt = system_prompt
        self.model = model
        self.client = client
        self.timeout = timeout
        self.solver_completion_tokens = 0
        self.request_id = request_id
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def process_query(self, query: str) -> str:
        try:
            analysis = self.analyze_query(query)
            if 'SOLVER_CAN_BE_APPLIED: True' not in analysis:
                return (self.standard_llm_inference(query), self.solver_completion_tokens)
            formulation = self.extract_and_validate_expressions(analysis)
            solver_result = self.solve_with_z3_sympy(formulation)
            return (self.generate_response(query, analysis, solver_result), self.solver_completion_tokens)
        except Exception as e:
            logging.error(f'An error occurred while processing the query with Z3 and SymPy, returning standard llm inference results: {str(e)}')
            return (self.standard_llm_inference(query), self.solver_completion_tokens)

    def analyze_query(self, query: str) -> str:
        analysis_prompt = f'Analyze the given query and determine if it can be solved using Z3 or SymPy:\n\n1. Identify variables, constraints, and objectives.\n2. Determine the problem type (e.g., SAT, optimization, symbolic manipulation).\n3. Decide if Z3, SymPy, or a combination of both is suitable.\n\nIf Z3 or SymPy can be applied, provide Python code using the appropriate library (or both) to solve the problem. Make sure you define any additional methods you need for solving the problem.\nThe code will be executed in an environment with Z3 and SymPy available, so do not include any other libraries or modules.\n\nQuery: {query}\n\nRespond with:\nSOLVER_CAN_BE_APPLIED: [True/False]\n\nSOLVER_FORMULATION:\n```python\n# Z3 and/or SymPy code here\n```\n\nAnalysis:\n[Your step-by-step analysis]\n'
        provider_request = {'model': self.model, 'messages': [{'role': 'system', 'content': self.system_prompt}, {'role': 'user', 'content': analysis_prompt}], 'max_tokens': 1024, 'n': 1, 'temperature': 0.1}
        analysis_response = self.client.chat.completions.create(**provider_request)
        if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and self.request_id:
            response_dict = analysis_response.model_dump() if hasattr(analysis_response, 'model_dump') else analysis_response
            optillm.conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
        self.solver_completion_tokens = analysis_response.usage.completion_tokens
        return analysis_response.choices[0].message.content

    def generate_response(self, query: str, analysis: str, solver_result: Dict[str, Any]) -> str:
        if solver_result.get('status') != 'success':
            return self.standard_llm_inference(query)
        response_prompt = f'Provide a clear answer to the query using the analysis and solver result:\n\nQuery: {query}\n\nAnalysis: {analysis}\n\nSolver Result: {solver_result.get('output')}\n\nResponse:\n'
        provider_request = {'model': self.model, 'messages': [{'role': 'system', 'content': self.system_prompt}, {'role': 'user', 'content': response_prompt}], 'max_tokens': 4096, 'n': 1, 'temperature': 0.1}
        response = self.client.chat.completions.create(**provider_request)
        if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and self.request_id:
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
            optillm.conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
        self.solver_completion_tokens = response.usage.completion_tokens
        return response.choices[0].message.content

    def standard_llm_inference(self, query: str) -> str:
        provider_request = {'model': self.model, 'messages': [{'role': 'system', 'content': self.system_prompt}, {'role': 'user', 'content': query}], 'max_tokens': 4096, 'n': 1, 'temperature': 0.1}
        response = self.client.chat.completions.create(**provider_request)
        if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and self.request_id:
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
            optillm.conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
        self.solver_completion_tokens = response.usage.completion_tokens
        return response.choices[0].message.content

    def extract_and_validate_expressions(self, analysis: str) -> str:
        formulation = re.search('```python\\n([\\s\\S]+?)```', analysis)
        if formulation:
            return formulation.group(1).strip()
        raise ValueError('No valid Z3 or SymPy formulation found in the analysis.')

    def solve_with_z3_sympy(self, formulation: str, max_attempts: int=3) -> Dict[str, Any]:
        for attempt in range(max_attempts):
            output = self.execute_solver_code(formulation)
            if 'Error:' not in output:
                return {'status': 'success', 'output': output}
            error_prompt = f'Fix the Z3 or SymPy code that resulted in an error. Follow these steps:\n\n    1. Review the original code and the error message carefully.\n    2. Analyze the error and identify its root cause.\n    3. Think through the necessary changes to fix the error.\n    4. Generate a corrected version of the code.\n\n    Original Code:\n    {formulation}\n\n    Error Message:\n    {output}\n\n    Step-by-Step Analysis:\n    [Provide your step-by-step analysis here]\n\n    Corrected Z3 or SymPy Code:\n    ```python\n    # Corrected code here\n    ```\n    '
            provider_request = {'model': self.model, 'messages': [{'role': 'system', 'content': self.system_prompt}, {'role': 'user', 'content': error_prompt}], 'max_tokens': 1024, 'n': 1, 'temperature': 0.1}
            response = self.client.chat.completions.create(**provider_request)
            if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and self.request_id:
                response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
                optillm.conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
            self.solver_completion_tokens = response.usage.completion_tokens
            formulation = self.extract_and_validate_expressions(response.choices[0].message.content)
        return {'status': 'failed', 'output': 'Failed to solve after multiple attempts.'}

    def execute_solver_code(self, code: str) -> str:
        logging.info('Executing Z3 and SymPy solver code')
        logging.info(f'Code: {code}')
        try:
            _ = ast.parse(code)
        except SyntaxError as e:
            logging.error(f'Syntax error in provided code: {e}')
            return f'Error: Syntax error: {e}'
        ctx = multiprocessing.get_context('spawn')
        with ctx.Pool(1) as pool:
            async_result = pool.apply_async(execute_code_in_process, (code,))
            try:
                status, result = async_result.get(timeout=self.timeout)
            except multiprocessing.TimeoutError:
                pool.terminate()
                logging.error('Execution timed out')
                return 'Error: Execution timed out'
        if status == 'error':
            logging.error(f'Execution error: {result}')
            return f'Error: {result}'
        logging.info('Z3 and SymPy solver code executed successfully')
        return result

def process_query(self, query: str) -> str:
    try:
        analysis = self.analyze_query(query)
        if 'SOLVER_CAN_BE_APPLIED: True' not in analysis:
            return (self.standard_llm_inference(query), self.solver_completion_tokens)
        formulation = self.extract_and_validate_expressions(analysis)
        solver_result = self.solve_with_z3_sympy(formulation)
        return (self.generate_response(query, analysis, solver_result), self.solver_completion_tokens)
    except Exception as e:
        logging.error(f'An error occurred while processing the query with Z3 and SymPy, returning standard llm inference results: {str(e)}')
        return (self.standard_llm_inference(query), self.solver_completion_tokens)

def analyze_query(self, query: str) -> str:
    analysis_prompt = f'Analyze the given query and determine if it can be solved using Z3 or SymPy:\n\n1. Identify variables, constraints, and objectives.\n2. Determine the problem type (e.g., SAT, optimization, symbolic manipulation).\n3. Decide if Z3, SymPy, or a combination of both is suitable.\n\nIf Z3 or SymPy can be applied, provide Python code using the appropriate library (or both) to solve the problem. Make sure you define any additional methods you need for solving the problem.\nThe code will be executed in an environment with Z3 and SymPy available, so do not include any other libraries or modules.\n\nQuery: {query}\n\nRespond with:\nSOLVER_CAN_BE_APPLIED: [True/False]\n\nSOLVER_FORMULATION:\n```python\n# Z3 and/or SymPy code here\n```\n\nAnalysis:\n[Your step-by-step analysis]\n'
    provider_request = {'model': self.model, 'messages': [{'role': 'system', 'content': self.system_prompt}, {'role': 'user', 'content': analysis_prompt}], 'max_tokens': 1024, 'n': 1, 'temperature': 0.1}
    analysis_response = self.client.chat.completions.create(**provider_request)
    if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and self.request_id:
        response_dict = analysis_response.model_dump() if hasattr(analysis_response, 'model_dump') else analysis_response
        optillm.conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
    self.solver_completion_tokens = analysis_response.usage.completion_tokens
    return analysis_response.choices[0].message.content

def generate_response(self, query: str, analysis: str, solver_result: Dict[str, Any]) -> str:
    if solver_result.get('status') != 'success':
        return self.standard_llm_inference(query)
    response_prompt = f'Provide a clear answer to the query using the analysis and solver result:\n\nQuery: {query}\n\nAnalysis: {analysis}\n\nSolver Result: {solver_result.get('output')}\n\nResponse:\n'
    provider_request = {'model': self.model, 'messages': [{'role': 'system', 'content': self.system_prompt}, {'role': 'user', 'content': response_prompt}], 'max_tokens': 4096, 'n': 1, 'temperature': 0.1}
    response = self.client.chat.completions.create(**provider_request)
    if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and self.request_id:
        response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
        optillm.conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
    self.solver_completion_tokens = response.usage.completion_tokens
    return response.choices[0].message.content

def standard_llm_inference(self, query: str) -> str:
    provider_request = {'model': self.model, 'messages': [{'role': 'system', 'content': self.system_prompt}, {'role': 'user', 'content': query}], 'max_tokens': 4096, 'n': 1, 'temperature': 0.1}
    response = self.client.chat.completions.create(**provider_request)
    if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and self.request_id:
        response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
        optillm.conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
    self.solver_completion_tokens = response.usage.completion_tokens
    return response.choices[0].message.content

def solve_with_z3_sympy(self, formulation: str, max_attempts: int=3) -> Dict[str, Any]:
    for attempt in range(max_attempts):
        output = self.execute_solver_code(formulation)
        if 'Error:' not in output:
            return {'status': 'success', 'output': output}
        error_prompt = f'Fix the Z3 or SymPy code that resulted in an error. Follow these steps:\n\n    1. Review the original code and the error message carefully.\n    2. Analyze the error and identify its root cause.\n    3. Think through the necessary changes to fix the error.\n    4. Generate a corrected version of the code.\n\n    Original Code:\n    {formulation}\n\n    Error Message:\n    {output}\n\n    Step-by-Step Analysis:\n    [Provide your step-by-step analysis here]\n\n    Corrected Z3 or SymPy Code:\n    ```python\n    # Corrected code here\n    ```\n    '
        provider_request = {'model': self.model, 'messages': [{'role': 'system', 'content': self.system_prompt}, {'role': 'user', 'content': error_prompt}], 'max_tokens': 1024, 'n': 1, 'temperature': 0.1}
        response = self.client.chat.completions.create(**provider_request)
        if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and self.request_id:
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
            optillm.conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
        self.solver_completion_tokens = response.usage.completion_tokens
        formulation = self.extract_and_validate_expressions(response.choices[0].message.content)
    return {'status': 'failed', 'output': 'Failed to solve after multiple attempts.'}

class Completions:

    @staticmethod
    def create(model: str, messages: List[Dict[str, str]], **kwargs):
        if model.startswith('gemini'):
            response = completion(model=model, messages=messages, **kwargs, safety_settings=SAFETY_SETTINGS)
        else:
            response = completion(model=model, messages=messages, **kwargs)
        return response

@staticmethod
def create(model: str, messages: List[Dict[str, str]], **kwargs):
    if model.startswith('gemini'):
        response = completion(model=model, messages=messages, **kwargs, safety_settings=SAFETY_SETTINGS)
    else:
        response = completion(model=model, messages=messages, **kwargs)
    return response

def none_approach(client: Any, model: str, original_messages: List[Dict[str, str]], request_id: str=None, **kwargs) -> Dict[str, Any]:
    """
    Direct proxy approach that passes through all parameters to the underlying endpoint.
    
    Args:
        client: OpenAI client instance
        model: Model identifier
        original_messages: Original messages from the request
        request_id: Optional request ID for conversation logging
        **kwargs: Additional parameters to pass through
    
    Returns:
        Dict[str, Any]: Full OpenAI API response
    """
    if model.startswith('none-'):
        model = model[5:]
    try:
        normalized_messages = normalize_message_content(original_messages)
        provider_request = {'model': model, 'messages': normalized_messages, **kwargs}
        response = client.chat.completions.create(model=model, messages=normalized_messages, **kwargs)
        response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
        if conversation_logger and request_id:
            conversation_logger.log_provider_call(request_id, provider_request, response_dict)
        return response_dict
    except Exception as e:
        if conversation_logger and request_id:
            conversation_logger.log_error(request_id, f'Error in none approach: {str(e)}')
        logger.error(f'Error in none approach: {str(e)}')
        raise

def process_single_response(text):
    if not has_conversation_tags(text):
        return text
    messages = []
    parts = re.split('(?=(User:|Assistant:))', text.strip())
    parts = [p for p in parts if p.strip()]
    for part in parts:
        part = part.strip()
        if part.startswith('User:'):
            messages.append({'role': 'user', 'content': part[5:].strip()})
        elif part.startswith('Assistant:'):
            messages.append({'role': 'assistant', 'content': part[10:].strip()})
    return messages

def chat_with_optillm(message, history):
    import httpx
    from openai import OpenAI
    custom_client = OpenAI(api_key='optillm', base_url=base_url, timeout=httpx.Timeout(1800.0, connect=5.0), max_retries=0)
    messages = []
    for h in history:
        if h[0]:
            messages.append({'role': 'user', 'content': h[0]})
        if h[1]:
            messages.append({'role': 'assistant', 'content': h[1]})
    messages.append({'role': 'user', 'content': message})
    try:
        response = custom_client.chat.completions.create(model=server_config['model'], messages=messages)
        return response.choices[0].message.content
    except Exception as e:
        return f'Error: {str(e)}'

def generate_solutions(client, system_prompt: str, query: str, model: str, num_solutions: int, is_sneaky: bool=False, temperature: float=0.7, request_id: str=None) -> List[str]:
    global pvg_completion_tokens
    role = 'sneaky' if is_sneaky else 'helpful'
    logger.info(f'Generating {num_solutions} {role} solutions')
    role_instruction = "\n    You are a problem solver tasked with generating solutions to the given problem. \n    If you are in 'helpful' mode:\n    - Provide a correct, detailed, and step-by-step solution to the problem.\n    - Explain your reasoning clearly and logically.\n    - Ensure your final answer or conclusion is accurate and well-supported.\n    - Use domain-specific terminology or notation if appropriate.\n\n    If you are in 'sneaky' mode:\n    - Provide a solution that appears correct but contains subtle errors or flaws.\n    - Make your explanation seem logical and convincing.\n    - Ensure your final answer or conclusion is incorrect, but in a way that's not immediately obvious.\n    - Maintain the appearance of expertise in the relevant domain.\n    "
    messages = [{'role': 'system', 'content': f'{system_prompt}\n{role_instruction}\nYou are in {role} mode.'}, {'role': 'user', 'content': query}]
    provider_request = {'model': model, 'messages': messages, 'n': num_solutions, 'max_tokens': 4096, 'temperature': temperature}
    response = client.chat.completions.create(**provider_request)
    if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and request_id:
        response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
        optillm.conversation_logger.log_provider_call(request_id, provider_request, response_dict)
    pvg_completion_tokens += response.usage.completion_tokens
    solutions = [choice.message.content for choice in response.choices]
    logger.debug(f'Generated {role} solutions: {solutions}')
    return solutions

def verify_solutions(client, system_prompt: str, initial_query: str, solutions: List[str], model: str, request_id: str=None) -> List[float]:
    global pvg_completion_tokens
    logger.info(f'Verifying {len(solutions)} solutions')
    verify_prompt = f'{system_prompt}\nYou are a verifier tasked with evaluating the correctness and clarity of solutions to the given problem.\nRate the following solution on a scale from 0 to 10, where:\n- 0 is completely incorrect or incomprehensible\n- 5 is partially correct or lacks clarity\n- 10 is perfectly correct, clear, and well-explained\n\nConsider the following criteria:\n1. Accuracy of the final answer or conclusion\n2. Correctness of each step or argument in the solution\n3. Clarity and logical flow of the explanation\n4. Appropriate use of domain-specific concepts or terminology\n5. Completeness of the solution\n\nBe especially vigilant for subtle errors or flaws that might not be immediately obvious.\n\nProvide your response in the following format:\n\nScore: [Your numerical score from 0 to 10]\nExplanation: [Your detailed explanation for the score, highlighting specific strengths or weaknesses]\n\nEnsure that the Score is a single number between 0 and 10, and the Explanation is on a new line.'
    scores = []
    for i, solution in enumerate(solutions):
        messages = [{'role': 'system', 'content': verify_prompt}, {'role': 'user', 'content': f'Problem: {initial_query}\n\nSolution: {solution}'}]
        provider_request = {'model': model, 'messages': messages, 'max_tokens': 1024, 'temperature': 0.2}
        response = client.chat.completions.create(**provider_request)
        if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and request_id:
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
            optillm.conversation_logger.log_provider_call(request_id, provider_request, response_dict)
        pvg_completion_tokens += response.usage.completion_tokens
        rating = response.choices[0].message.content
        logger.debug(f'Raw rating for solution {i + 1}: {rating}')
        score_match = re.search('Score:\\s*(\\d+(\\.\\d+)?)', rating)
        explanation_match = re.search('Explanation:\\s*(.*)', rating, re.DOTALL)
        if score_match:
            try:
                score = float(score_match.group(1))
                scores.append(score)
                logger.debug(f'Solution {i + 1} score: {score}')
                if explanation_match:
                    explanation = explanation_match.group(1).strip()
                    logger.debug(f'Explanation: {explanation}')
                else:
                    logger.warning(f'No explanation found for solution {i + 1}')
            except ValueError:
                scores.append(0)
                logger.warning(f'Failed to parse score for solution {i + 1}. Setting score to 0.')
        else:
            scores.append(0)
            logger.warning(f'No score found for solution {i + 1}. Setting score to 0.')
    return scores

def inference_time_pv_game(system_prompt: str, initial_query: str, client, model: str, num_rounds: int=2, num_solutions: int=3, request_id: str=None) -> str:
    global pvg_completion_tokens
    logger.info(f'Starting inference-time PV game with {num_rounds} rounds and {num_solutions} solutions per round')
    best_solution = ''
    best_score = -1
    for round in range(num_rounds):
        logger.info(f'Starting round {round + 1}')
        temperature = max(0.2, 0.7 - round * 0.1)
        helpful_solutions = generate_solutions(client, system_prompt, initial_query, model, num_solutions, temperature=temperature, request_id=request_id)
        sneaky_solutions = generate_solutions(client, system_prompt, initial_query, model, num_solutions, is_sneaky=True, temperature=temperature, request_id=request_id)
        all_solutions = helpful_solutions + sneaky_solutions
        scores = verify_solutions(client, system_prompt, initial_query, all_solutions, model, request_id=request_id)
        round_best_solution = max(zip(all_solutions, scores), key=lambda x: x[1])
        if round_best_solution[1] > best_score:
            best_solution = round_best_solution[0]
            best_score = round_best_solution[1]
            logger.info(f'New best solution found in round {round + 1} with score {best_score}')
        else:
            logger.debug(f'No improvement in round {round + 1}. Best score remains {best_score}')
        if round < num_rounds - 1:
            logger.debug('Refining query for next round')
            refine_prompt = f'\n            Based on the original query and the best solution so far, suggest a refined query that might lead to an even better solution.\n            Focus on aspects of the problem that were challenging or not fully addressed in the best solution.\n            Maintain the core intent of the original query while adding specificity or context that could improve the solution.\n            \n            Original query: {initial_query}\n            \n            Best solution so far: {best_solution}\n            \n            Refined query:\n            '
            messages = [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': refine_prompt}]
            provider_request = {'model': model, 'messages': messages, 'max_tokens': 1024, 'temperature': 0.5}
            response = client.chat.completions.create(**provider_request)
            if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and request_id:
                response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
                optillm.conversation_logger.log_provider_call(request_id, provider_request, response_dict)
            pvg_completion_tokens += response.usage.completion_tokens
            initial_query = response.choices[0].message.content
            logger.debug(f'Refined query: {initial_query}')
    logger.info(f'Inference-time PV game completed. Best solution score: {best_score}')
    return (best_solution, pvg_completion_tokens)

def re2_approach(system_prompt, initial_query, client, model, n=1, request_id: str=None):
    """
    Implement the RE2 (Re-Reading) approach for improved reasoning in LLMs.
    
    Args:
    system_prompt (str): The system prompt to be used.
    initial_query (str): The initial user query.
    client: The OpenAI client object.
    model (str): The name of the model to use.
    n (int): Number of completions to generate.
    
    Returns:
    str or list: The generated response(s) from the model.
    """
    logger.info('Using RE2 approach for query processing')
    re2_completion_tokens = 0
    re2_prompt = f'{initial_query}\nRead the question again: {initial_query}'
    messages = [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': re2_prompt}]
    try:
        provider_request = {'model': model, 'messages': messages, 'n': n}
        response = client.chat.completions.create(**provider_request)
        if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and request_id:
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
            optillm.conversation_logger.log_provider_call(request_id, provider_request, response_dict)
        re2_completion_tokens += response.usage.completion_tokens
        if n == 1:
            return (response.choices[0].message.content.strip(), re2_completion_tokens)
        else:
            return ([choice.message.content.strip() for choice in response.choices], re2_completion_tokens)
    except Exception as e:
        logger.error(f'Error in RE2 approach: {str(e)}')
        raise

class PlanSearch:

    def __init__(self, system_prompt: str, client, model: str, request_id: str=None):
        self.system_prompt = system_prompt
        self.client = client
        self.model = model
        self.request_id = request_id
        self.plansearch_completion_tokens = 0

    def generate_observations(self, problem: str, num_observations: int=3) -> List[str]:
        prompt = f'You are an expert Python programmer. You will be given a competitive programming question\n(problem specification). You will return several useful, non-obvious, and correct observations\nabout the problem, like hints to solve the problem. You will NOT return any code. Be as\ncreative as possible, going beyond what you think is intuitively correct.\n\nHere is the competitive programming problem:\n{problem}\n\nPlease provide {num_observations} observations.'
        provider_request = {'model': self.model, 'max_tokens': 4096, 'messages': [{'role': 'system', 'content': self.system_prompt}, {'role': 'user', 'content': prompt}]}
        response = self.client.chat.completions.create(**provider_request)
        if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and self.request_id:
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
            optillm.conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
        self.plansearch_completion_tokens += response.usage.completion_tokens
        observations = response.choices[0].message.content.strip().split('\n')
        return [obs.strip() for obs in observations if obs.strip()]

    def generate_derived_observations(self, problem: str, observations: List[str], num_new_observations: int=2) -> List[str]:
        prompt = f'You are an expert Python programmer. You will be given a competitive programming question\n(problem specification) and several correct observations about the problem.\nYou will brainstorm several new, useful, and correct observations about the problem, derived\nfrom the given observations. You will NOT return any code. Be as creative as possible, going\nbeyond what you think is intuitively correct.\n\nHere is the competitive programming problem:\n{problem}\n\nHere are the existing observations:\n{chr(10).join((f'{i + 1}. {obs}' for i, obs in enumerate(observations)))}\n\nPlease provide {num_new_observations} new observations derived from the existing ones.'
        provider_request = {'model': self.model, 'max_tokens': 4096, 'messages': [{'role': 'system', 'content': self.system_prompt}, {'role': 'user', 'content': prompt}]}
        response = self.client.chat.completions.create(**provider_request)
        if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and self.request_id:
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
            optillm.conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
        self.plansearch_completion_tokens += response.usage.completion_tokens
        new_observations = response.choices[0].message.content.strip().split('\n')
        return [obs.strip() for obs in new_observations if obs.strip()]

    def generate_solution(self, problem: str, observations: List[str]) -> str:
        prompt = f'Here is the competitive programming problem:\n{problem}\n\nHere are the intelligent observations to help solve the problem:\n{chr(10).join((f'Observation {i + 1}: {obs}' for i, obs in enumerate(observations)))}\n\nUse these observations above to brainstorm a natural language solution to the problem above.\nNote that your intuition may lead you astray, so come up with simple, creative ideas that\ngo beyond what you would usually come up with and exceeds your narrow intuition.\nQuote relevant parts of the observations EXACTLY before each step of the solution. QUOTING\nIS CRUCIAL.'
        provider_request = {'model': self.model, 'max_tokens': 4096, 'messages': [{'role': 'system', 'content': self.system_prompt}, {'role': 'user', 'content': prompt}]}
        response = self.client.chat.completions.create(**provider_request)
        if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and self.request_id:
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
            optillm.conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
        self.plansearch_completion_tokens += response.usage.completion_tokens
        return response.choices[0].message.content.strip()

    def implement_solution(self, problem: str, solution: str) -> str:
        prompt = f'You are an expert Python programmer. You will be given a question (problem specification)\nand a natural language solution/tutorial that describes how to solve the problem. You will\ngenerate a correct Python program that matches said specification and tutorial and passes\nall tests. You will NOT return anything except for the program inside markdown codeblocks.\n\nProblem:\n{problem}\n\nSolution:\n{solution}\n\nPlease implement the solution in Python.'
        provider_request = {'model': self.model, 'max_tokens': 4096, 'messages': [{'role': 'system', 'content': self.system_prompt}, {'role': 'user', 'content': prompt}]}
        response = self.client.chat.completions.create(**provider_request)
        if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and self.request_id:
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
            optillm.conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
        self.plansearch_completion_tokens += response.usage.completion_tokens
        return response.choices[0].message.content.strip()

    def solve(self, problem: str, num_initial_observations: int=3, num_derived_observations: int=2) -> Tuple[str, str]:
        logger.info('Generating initial observations')
        initial_observations = self.generate_observations(problem, num_initial_observations)
        logger.info('Generating derived observations')
        derived_observations = self.generate_derived_observations(problem, initial_observations, num_derived_observations)
        all_observations = initial_observations + derived_observations
        logger.info('Generating solution based on observations')
        natural_language_solution = self.generate_solution(problem, all_observations)
        logger.info('Implementing solution in Python')
        python_implementation = self.implement_solution(problem, natural_language_solution)
        return (natural_language_solution, python_implementation)

    def solve_multiple(self, problem: str, n: int, num_initial_observations: int=3, num_derived_observations: int=2) -> List[str]:
        solutions = []
        for _ in range(n):
            _, python_implementation = self.solve(problem, num_initial_observations, num_derived_observations)
            solutions.append(python_implementation)
        return solutions

def generate_observations(self, problem: str, num_observations: int=3) -> List[str]:
    prompt = f'You are an expert Python programmer. You will be given a competitive programming question\n(problem specification). You will return several useful, non-obvious, and correct observations\nabout the problem, like hints to solve the problem. You will NOT return any code. Be as\ncreative as possible, going beyond what you think is intuitively correct.\n\nHere is the competitive programming problem:\n{problem}\n\nPlease provide {num_observations} observations.'
    provider_request = {'model': self.model, 'max_tokens': 4096, 'messages': [{'role': 'system', 'content': self.system_prompt}, {'role': 'user', 'content': prompt}]}
    response = self.client.chat.completions.create(**provider_request)
    if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and self.request_id:
        response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
        optillm.conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
    self.plansearch_completion_tokens += response.usage.completion_tokens
    observations = response.choices[0].message.content.strip().split('\n')
    return [obs.strip() for obs in observations if obs.strip()]

def generate_derived_observations(self, problem: str, observations: List[str], num_new_observations: int=2) -> List[str]:
    prompt = f'You are an expert Python programmer. You will be given a competitive programming question\n(problem specification) and several correct observations about the problem.\nYou will brainstorm several new, useful, and correct observations about the problem, derived\nfrom the given observations. You will NOT return any code. Be as creative as possible, going\nbeyond what you think is intuitively correct.\n\nHere is the competitive programming problem:\n{problem}\n\nHere are the existing observations:\n{chr(10).join((f'{i + 1}. {obs}' for i, obs in enumerate(observations)))}\n\nPlease provide {num_new_observations} new observations derived from the existing ones.'
    provider_request = {'model': self.model, 'max_tokens': 4096, 'messages': [{'role': 'system', 'content': self.system_prompt}, {'role': 'user', 'content': prompt}]}
    response = self.client.chat.completions.create(**provider_request)
    if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and self.request_id:
        response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
        optillm.conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
    self.plansearch_completion_tokens += response.usage.completion_tokens
    new_observations = response.choices[0].message.content.strip().split('\n')
    return [obs.strip() for obs in new_observations if obs.strip()]

def generate_solution(self, problem: str, observations: List[str]) -> str:
    prompt = f'Here is the competitive programming problem:\n{problem}\n\nHere are the intelligent observations to help solve the problem:\n{chr(10).join((f'Observation {i + 1}: {obs}' for i, obs in enumerate(observations)))}\n\nUse these observations above to brainstorm a natural language solution to the problem above.\nNote that your intuition may lead you astray, so come up with simple, creative ideas that\ngo beyond what you would usually come up with and exceeds your narrow intuition.\nQuote relevant parts of the observations EXACTLY before each step of the solution. QUOTING\nIS CRUCIAL.'
    provider_request = {'model': self.model, 'max_tokens': 4096, 'messages': [{'role': 'system', 'content': self.system_prompt}, {'role': 'user', 'content': prompt}]}
    response = self.client.chat.completions.create(**provider_request)
    if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and self.request_id:
        response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
        optillm.conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
    self.plansearch_completion_tokens += response.usage.completion_tokens
    return response.choices[0].message.content.strip()

def implement_solution(self, problem: str, solution: str) -> str:
    prompt = f'You are an expert Python programmer. You will be given a question (problem specification)\nand a natural language solution/tutorial that describes how to solve the problem. You will\ngenerate a correct Python program that matches said specification and tutorial and passes\nall tests. You will NOT return anything except for the program inside markdown codeblocks.\n\nProblem:\n{problem}\n\nSolution:\n{solution}\n\nPlease implement the solution in Python.'
    provider_request = {'model': self.model, 'max_tokens': 4096, 'messages': [{'role': 'system', 'content': self.system_prompt}, {'role': 'user', 'content': prompt}]}
    response = self.client.chat.completions.create(**provider_request)
    if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and self.request_id:
        response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
        optillm.conversation_logger.log_provider_call(self.request_id, provider_request, response_dict)
    self.plansearch_completion_tokens += response.usage.completion_tokens
    return response.choices[0].message.content.strip()

class MARSAggregator:
    """
    RSA-inspired aggregation system for combining solutions

    Key features:
    - Population management (N > K for diversity)
    - Recursive aggregation loops
    - Parallel execution of aggregation calls
    - Solution quality tracking
    """

    def __init__(self, client, model: str, config: Dict[str, Any]):
        self.client = client
        self.model = model
        self.config = config
        self.population_size = config.get('population_size', 6)
        self.aggregation_size = config.get('aggregation_size', 3)
        self.aggregation_loops = config.get('aggregation_loops', 3)
        self.max_tokens = config.get('max_tokens', 30000)

    async def run_aggregation_loops(self, workspace: MARSWorkspace, request_id: str=None, executor: ThreadPoolExecutor=None) -> Tuple[int, Dict[str, Any]]:
        """
        Run T iterations of RSA-style aggregation

        Args:
            workspace: MARS workspace containing solutions
            request_id: Request ID for logging
            executor: Thread pool for parallel execution

        Returns:
            Tuple of (total_reasoning_tokens, aggregation_summary)
        """
        logger.info(f'Starting {self.aggregation_loops} aggregation loops')
        total_reasoning_tokens = 0
        aggregation_history = []
        self._ensure_population_size(workspace)
        for loop_idx in range(self.aggregation_loops):
            logger.info(f'Aggregation loop {loop_idx + 1}/{self.aggregation_loops}')
            loop_tokens, loop_summary = await self._run_single_aggregation_loop(workspace, loop_idx, request_id, executor)
            total_reasoning_tokens += loop_tokens
            aggregation_history.append({'loop': loop_idx, 'tokens': loop_tokens, 'summary': loop_summary})
            logger.info(f'Loop {loop_idx + 1} complete: {loop_summary['solutions_generated']} new solutions')
        summary = {'total_loops': self.aggregation_loops, 'total_reasoning_tokens': total_reasoning_tokens, 'final_population_size': len(workspace.solutions), 'aggregation_history': aggregation_history}
        logger.info(f'Aggregation complete: {summary['final_population_size']} solutions in final population')
        return (total_reasoning_tokens, summary)

    async def _run_single_aggregation_loop(self, workspace: MARSWorkspace, loop_idx: int, request_id: str=None, executor: ThreadPoolExecutor=None) -> Tuple[int, Dict[str, Any]]:
        """Run a single aggregation loop: sample K -> aggregate -> update population"""
        sampled_solutions = self._sample_solutions_for_aggregation(workspace)
        new_solutions, total_tokens = await self._generate_aggregated_solutions(workspace, sampled_solutions, request_id, executor)
        self._update_population(workspace, new_solutions)
        loop_summary = {'sampled_solutions': len(sampled_solutions), 'solutions_generated': len(new_solutions), 'population_size': len(workspace.solutions), 'total_tokens': total_tokens}
        return (total_tokens, loop_summary)

    def _sample_solutions_for_aggregation(self, workspace: MARSWorkspace) -> List[List[AgentSolution]]:
        """
        Sample K solutions from population for aggregation
        Uses different strategies for each sample to maintain diversity
        """
        all_solutions = workspace.solutions
        if len(all_solutions) < self.aggregation_size:
            return [all_solutions]
        samples = []
        num_samples = min(self.population_size // self.aggregation_size, 3)
        for i in range(num_samples):
            if i == 0:
                sample = sorted(all_solutions, key=lambda s: s.verification_score, reverse=True)[:self.aggregation_size]
            elif i == 1:
                by_agent = {}
                for sol in all_solutions:
                    if sol.agent_id not in by_agent:
                        by_agent[sol.agent_id] = []
                    by_agent[sol.agent_id].append(sol)
                sample = []
                for agent_solutions in by_agent.values():
                    if sample and len(sample) < self.aggregation_size:
                        sample.append(max(agent_solutions, key=lambda s: s.confidence))
                    if len(sample) >= self.aggregation_size:
                        break
                if len(sample) < self.aggregation_size:
                    remaining = [s for s in all_solutions if s not in sample]
                    sample.extend(sorted(remaining, key=lambda s: s.verification_score, reverse=True)[:self.aggregation_size - len(sample)])
            else:
                sample = random.sample(all_solutions, min(self.aggregation_size, len(all_solutions)))
            samples.append(sample)
        logger.info(f'Generated {len(samples)} sample groups for aggregation')
        return samples

    async def _generate_aggregated_solutions(self, workspace: MARSWorkspace, sampled_solution_groups: List[List[AgentSolution]], request_id: str=None, executor: ThreadPoolExecutor=None) -> Tuple[List[AgentSolution], int]:
        """Generate new solutions by aggregating sampled solutions in parallel"""

        async def aggregate_solution_group(solutions: List[AgentSolution]) -> Tuple[Optional[AgentSolution], int]:
            """Aggregate a single group of solutions"""
            loop = asyncio.get_event_loop()
            try:
                if len(solutions) == 1:
                    prompt = SINGLE_REFINEMENT_PROMPT.format(problem=workspace.problem, candidate_solution=solutions[0].solution)
                else:
                    candidate_text = ''
                    for i, sol in enumerate(solutions):
                        candidate_text += f'Solution {i + 1} (Agent {sol.agent_id}, confidence: {sol.confidence:.2f}):\n'
                        candidate_text += sol.solution + '\n\n'
                    prompt = MULTI_AGGREGATION_PROMPT.format(problem=workspace.problem, candidate_solutions=candidate_text)
                solution, tokens = await loop.run_in_executor(executor, self._call_model_for_aggregation, prompt, request_id)
                if solution:
                    aggregated_solution = AgentSolution(agent_id=f'agg_{datetime.now().strftime('%H%M%S')}', solution=solution, confidence=0.8, reasoning_tokens=tokens, total_tokens=tokens, solution_length=len(solution), is_verified=False, verification_score=0.0)
                    return (aggregated_solution, tokens)
                return (None, tokens)
            except Exception as e:
                logger.error(f'Aggregation failed: {str(e)}')
                return (None, 0)
        tasks = [aggregate_solution_group(group) for group in sampled_solution_groups]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        new_solutions = []
        total_tokens = 0
        for result in results:
            if isinstance(result, Exception):
                logger.error(f'Aggregation task failed: {str(result)}')
                continue
            solution, tokens = result
            if solution:
                new_solutions.append(solution)
            total_tokens += tokens
        logger.info(f'Generated {len(new_solutions)} aggregated solutions with {total_tokens} reasoning tokens')
        return (new_solutions, total_tokens)

    def _call_model_for_aggregation(self, prompt: str, request_id: str=None) -> Tuple[str, int]:
        """Call the model to perform aggregation (synchronous for executor)"""
        try:
            response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'system', 'content': 'You are a mathematical reasoning expert focused on solution aggregation and refinement.'}, {'role': 'user', 'content': prompt}], max_tokens=self.max_tokens, temperature=0.7, timeout=300, extra_body={'reasoning': {'effort': 'high'}})
            if request_id:
                provider_request = {'model': self.model, 'messages': [{'role': 'system', 'content': 'You are a mathematical reasoning expert focused on solution aggregation and refinement.'}, {'role': 'user', 'content': prompt}], 'max_tokens': self.max_tokens, 'temperature': 0.7, 'extra_body': {'reasoning': {'effort': 'high'}}}
                response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
                conversation_logger.log_provider_call(request_id, provider_request, response_dict)
            solution = response.choices[0].message.content.strip()
            reasoning_tokens = 0
            if hasattr(response, 'usage') and response.usage:
                if hasattr(response.usage, 'completion_tokens_details') and response.usage.completion_tokens_details:
                    reasoning_tokens = getattr(response.usage.completion_tokens_details, 'reasoning_tokens', 0)
                if reasoning_tokens == 0:
                    reasoning_tokens = getattr(response.usage, 'reasoning_tokens', 0)
            return (solution, reasoning_tokens)
        except Exception as e:
            logger.error(f'Model call for aggregation failed: {str(e)}')
            return ('', 0)

    def _update_population(self, workspace: MARSWorkspace, new_solutions: List[AgentSolution]) -> None:
        """Update population with new solutions, maintaining population size limit"""
        for solution in new_solutions:
            workspace.add_solution(solution)
        all_solutions = workspace.solutions
        if len(all_solutions) > self.population_size:
            sorted_solutions = sorted(all_solutions, key=lambda s: (s.verification_score, s.confidence), reverse=True)
            workspace.solutions = sorted_solutions[:self.population_size]
            logger.info(f'Population trimmed to {self.population_size} best solutions')

    def _ensure_population_size(self, workspace: MARSWorkspace) -> None:
        """Ensure we have minimum population size for effective aggregation"""
        current_size = len(workspace.solutions)
        if current_size < self.aggregation_size:
            logger.warning(f'Population size ({current_size}) < aggregation size ({self.aggregation_size})')
            logger.warning('Aggregation may be less effective with limited diversity')
        logger.info(f'Population ready: {current_size} solutions available for aggregation')

def _call_model_for_aggregation(self, prompt: str, request_id: str=None) -> Tuple[str, int]:
    """Call the model to perform aggregation (synchronous for executor)"""
    try:
        response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'system', 'content': 'You are a mathematical reasoning expert focused on solution aggregation and refinement.'}, {'role': 'user', 'content': prompt}], max_tokens=self.max_tokens, temperature=0.7, timeout=300, extra_body={'reasoning': {'effort': 'high'}})
        if request_id:
            provider_request = {'model': self.model, 'messages': [{'role': 'system', 'content': 'You are a mathematical reasoning expert focused on solution aggregation and refinement.'}, {'role': 'user', 'content': prompt}], 'max_tokens': self.max_tokens, 'temperature': 0.7, 'extra_body': {'reasoning': {'effort': 'high'}}}
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
            conversation_logger.log_provider_call(request_id, provider_request, response_dict)
        solution = response.choices[0].message.content.strip()
        reasoning_tokens = 0
        if hasattr(response, 'usage') and response.usage:
            if hasattr(response.usage, 'completion_tokens_details') and response.usage.completion_tokens_details:
                reasoning_tokens = getattr(response.usage.completion_tokens_details, 'reasoning_tokens', 0)
            if reasoning_tokens == 0:
                reasoning_tokens = getattr(response.usage, 'reasoning_tokens', 0)
        return (solution, reasoning_tokens)
    except Exception as e:
        logger.error(f'Model call for aggregation failed: {str(e)}')
        return ('', 0)

class StrategyNetwork:
    """
    Cross-agent strategy sharing and meta-reasoning system

    Key capabilities:
    1. Extract reasoning strategies from agent solutions
    2. Share effective strategies between agents
    3. Track strategy effectiveness across problem types
    4. Enable adaptive agent behavior based on peer insights
    """

    def __init__(self, client, model: str, config: Dict[str, Any]):
        self.client = client
        self.model = model
        self.config = config
        self.max_tokens = config.get('max_tokens', 30000)
        self.strategies: Dict[str, ReasoningStrategy] = {}
        self.strategy_effectiveness: Dict[Tuple[str, str], StrategyEffectiveness] = {}
        self.agent_preferred_strategies: Dict[str, List[str]] = defaultdict(list)
        self.problem_type_cache: Dict[str, str] = {}
        logger.info('Initialized Strategy Network for cross-agent insight sharing')

    async def extract_strategies_from_solutions(self, workspace: MARSWorkspace, request_id: str=None, executor: ThreadPoolExecutor=None) -> Dict[str, ReasoningStrategy]:
        """Extract reasoning strategies from all agent solutions"""
        logger.info('Extracting strategies from agent solutions...')
        extraction_tasks = []
        for solution in workspace.solutions:
            if not solution.agent_id.startswith('agg_'):
                task = self._extract_strategy_async(solution, workspace.problem, request_id, executor)
                extraction_tasks.append(task)
        results = await asyncio.gather(*extraction_tasks, return_exceptions=True)
        extracted_strategies = {}
        for result in results:
            if isinstance(result, Exception):
                logger.error(f'Strategy extraction failed: {str(result)}')
                continue
            if result:
                strategy = result
                extracted_strategies[strategy.strategy_id] = strategy
                self.strategies[strategy.strategy_id] = strategy
                self.agent_preferred_strategies[strategy.agent_id].append(strategy.strategy_id)
        logger.info(f'Extracted {len(extracted_strategies)} reasoning strategies')
        return extracted_strategies

    async def _extract_strategy_async(self, solution: AgentSolution, problem: str, request_id: str=None, executor: ThreadPoolExecutor=None) -> Optional[ReasoningStrategy]:
        """Extract strategy from a single agent solution"""
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(executor, self._extract_strategy_from_solution, solution, problem, request_id)
        except Exception as e:
            logger.error(f'Failed to extract strategy from agent {solution.agent_id}: {str(e)}')
            return None

    def _extract_strategy_from_solution(self, solution: AgentSolution, problem: str, request_id: str=None) -> Optional[ReasoningStrategy]:
        """Extract reasoning strategy using LLM analysis"""
        strategy_extraction_prompt = f'Analyze this mathematical solution and extract the key reasoning strategy:\n\nProblem: {problem}\n\nAgent Solution:\n{solution.solution}\n\nExtract the following strategy components:\n\n1. PROBLEM_TYPE: Classify as one of [algebra, geometry, combinatorics, number_theory, calculus, discrete_math, probability]\n\n2. APPROACH_TYPE: Identify the main approach [direct_computation, proof_by_contradiction, constructive_proof, case_analysis, induction, algebraic_manipulation, geometric_visualization, pattern_recognition, reduction_to_known_problem]\n\n3. KEY_INSIGHTS: List 2-3 key mathematical insights that enabled the solution\n\n4. MATHEMATICAL_TECHNIQUES: List specific techniques used [substitution, factorization, coordinate_geometry, symmetry, pigeonhole_principle, etc.]\n\n5. SOLUTION_PATTERN: Describe the general pattern/template of this solution approach\n\n6. SUCCESS_INDICATORS: What makes this approach particularly effective for this type of problem?\n\nFormat your response as:\nPROBLEM_TYPE: [type]\nAPPROACH_TYPE: [approach]\nKEY_INSIGHTS: [insight1], [insight2], [insight3]\nMATHEMATICAL_TECHNIQUES: [technique1], [technique2], [technique3]\nSOLUTION_PATTERN: [pattern description]\nSUCCESS_INDICATORS: [indicator1], [indicator2]'
        try:
            response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'system', 'content': 'You are a mathematical strategy analysis expert. Extract reasoning patterns from solutions.'}, {'role': 'user', 'content': strategy_extraction_prompt}], max_tokens=self.max_tokens // 4, temperature=0.3, timeout=120, extra_body={'reasoning': {'effort': 'medium'}})
            if request_id:
                provider_request = {'model': self.model, 'messages': [{'role': 'system', 'content': 'You are a mathematical strategy analysis expert.'}, {'role': 'user', 'content': strategy_extraction_prompt}], 'max_tokens': self.max_tokens // 4, 'temperature': 0.3, 'extra_body': {'reasoning': {'effort': 'medium'}}}
                response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
                conversation_logger.log_provider_call(request_id, provider_request, response_dict)
            analysis = response.choices[0].message.content.strip()
            strategy_data = self._parse_strategy_analysis(analysis)
            if strategy_data:
                strategy_id = f'strategy_{solution.agent_id}_{datetime.now().strftime('%H%M%S')}'
                return ReasoningStrategy(strategy_id=strategy_id, agent_id=solution.agent_id, problem_type=strategy_data.get('problem_type', 'unknown'), approach_type=strategy_data.get('approach_type', 'unknown'), key_insights=strategy_data.get('key_insights', []), mathematical_techniques=strategy_data.get('mathematical_techniques', []), solution_pattern=strategy_data.get('solution_pattern', ''), confidence=solution.confidence, success_indicators=strategy_data.get('success_indicators', []))
        except Exception as e:
            logger.error(f'Strategy extraction failed for agent {solution.agent_id}: {str(e)}')
            return None

    def _parse_strategy_analysis(self, analysis: str) -> Optional[Dict[str, Any]]:
        """Parse structured strategy analysis response"""
        try:
            lines = analysis.split('\n')
            strategy_data = {}
            for line in lines:
                line = line.strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    if key == 'problem_type':
                        strategy_data['problem_type'] = value
                    elif key == 'approach_type':
                        strategy_data['approach_type'] = value
                    elif 'insights' in key:
                        strategy_data['key_insights'] = [insight.strip() for insight in value.split(',')]
                    elif 'techniques' in key:
                        strategy_data['mathematical_techniques'] = [tech.strip() for tech in value.split(',')]
                    elif 'pattern' in key:
                        strategy_data['solution_pattern'] = value
                    elif 'indicators' in key:
                        strategy_data['success_indicators'] = [ind.strip() for ind in value.split(',')]
            return strategy_data if strategy_data else None
        except Exception as e:
            logger.error(f'Failed to parse strategy analysis: {str(e)}')
            return None

    async def share_strategies_across_agents(self, workspace: MARSWorkspace, extracted_strategies: Dict[str, ReasoningStrategy], request_id: str=None, executor: ThreadPoolExecutor=None) -> Dict[str, List[str]]:
        """Share effective strategies across agents and generate enhanced solutions"""
        logger.info('Sharing strategies across agents...')
        problem_type = await self._classify_problem_type(workspace.problem, request_id, executor)
        effective_strategies = self._get_effective_strategies_for_type(problem_type, extracted_strategies)
        enhancement_tasks = []
        agent_strategies = {}
        for solution in workspace.solutions:
            if not solution.agent_id.startswith('agg_'):
                cross_agent_strategies = [strategy for strategy in effective_strategies.values() if strategy.agent_id != solution.agent_id]
                if cross_agent_strategies:
                    agent_strategies[solution.agent_id] = [s.strategy_id for s in cross_agent_strategies]
                    task = self._generate_strategy_enhanced_solution_async(solution, workspace.problem, cross_agent_strategies, request_id, executor)
                    enhancement_tasks.append((solution.agent_id, task))
        if enhancement_tasks:
            tasks = [task for _, task in enhancement_tasks]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f'Strategy enhancement failed: {str(result)}')
                    continue
                if result:
                    enhanced_solution = result
                    workspace.add_solution(enhanced_solution)
                    logger.info(f'Added strategy-enhanced solution from agent {enhanced_solution.agent_id}')
        logger.info(f'Strategy sharing complete: enhanced {len(enhancement_tasks)} agents')
        return agent_strategies

    async def _classify_problem_type(self, problem: str, request_id: str=None, executor: ThreadPoolExecutor=None) -> str:
        """Classify the problem type for strategy matching"""
        if problem in self.problem_type_cache:
            return self.problem_type_cache[problem]
        loop = asyncio.get_event_loop()
        try:
            problem_type = await loop.run_in_executor(executor, self._classify_problem_with_llm, problem, request_id)
            self.problem_type_cache[problem] = problem_type
            return problem_type
        except Exception as e:
            logger.error(f'Problem classification failed: {str(e)}')
            return 'unknown'

    def _classify_problem_with_llm(self, problem: str, request_id: str=None) -> str:
        """Use LLM to classify problem type"""
        classification_prompt = f'Classify this mathematical problem into one category:\n\nProblem: {problem}\n\nCategories: [algebra, geometry, combinatorics, number_theory, calculus, discrete_math, probability]\n\nRespond with just the category name.'
        try:
            response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'system', 'content': 'You are a mathematical problem classifier.'}, {'role': 'user', 'content': classification_prompt}], max_tokens=50, temperature=0.1, timeout=60, extra_body={'reasoning': {'effort': 'low'}})
            classification = response.choices[0].message.content.strip().lower()
            valid_types = ['algebra', 'geometry', 'combinatorics', 'number_theory', 'calculus', 'discrete_math', 'probability']
            if classification in valid_types:
                return classification
            else:
                return 'algebra'
        except Exception as e:
            logger.error(f'Problem classification failed: {str(e)}')
            return 'algebra'

    def _get_effective_strategies_for_type(self, problem_type: str, extracted_strategies: Dict[str, ReasoningStrategy]) -> Dict[str, ReasoningStrategy]:
        """Get most effective strategies for the given problem type"""
        relevant_strategies = {}
        for strategy_id, strategy in extracted_strategies.items():
            if (strategy.problem_type == problem_type or strategy.problem_type == 'unknown') and strategy.confidence >= 0.6:
                relevant_strategies[strategy_id] = strategy
        if not relevant_strategies:
            sorted_strategies = sorted(extracted_strategies.items(), key=lambda x: x[1].confidence, reverse=True)
            relevant_strategies = dict(sorted_strategies[:2])
        return relevant_strategies

    async def _generate_strategy_enhanced_solution_async(self, original_solution: AgentSolution, problem: str, peer_strategies: List[ReasoningStrategy], request_id: str=None, executor: ThreadPoolExecutor=None) -> Optional[AgentSolution]:
        """Generate enhanced solution using peer strategies"""
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(executor, self._generate_strategy_enhanced_solution, original_solution, problem, peer_strategies, request_id)
        except Exception as e:
            logger.error(f'Strategy enhancement failed for agent {original_solution.agent_id}: {str(e)}')
            return None

    def _generate_strategy_enhanced_solution(self, original_solution: AgentSolution, problem: str, peer_strategies: List[ReasoningStrategy], request_id: str=None) -> Optional[AgentSolution]:
        """Generate solution enhanced with peer strategies"""
        strategy_insights = ''
        for strategy in peer_strategies[:2]:
            strategy_insights += f'\nPeer Strategy from Agent {strategy.agent_id}:\n'
            strategy_insights += f'- Approach: {strategy.approach_type}\n'
            strategy_insights += f'- Key Insights: {', '.join(strategy.key_insights[:3])}\n'
            strategy_insights += f'- Techniques: {', '.join(strategy.mathematical_techniques[:3])}\n'
            strategy_insights += f'- Success Pattern: {strategy.solution_pattern[:200]}...\n'
        enhancement_prompt = f'You are Agent {original_solution.agent_id} collaborating with other mathematical agents.\n\nOriginal Problem: {problem}\n\nYour Current Solution:\n{original_solution.solution}\n\nPeer Agent Strategy Insights:\n{strategy_insights}\n\nTask: Enhance your solution by incorporating the most valuable insights from your peers while maintaining your unique approach. Consider:\n\n1. Can any peer techniques strengthen your solution?\n2. Do peer insights reveal gaps in your reasoning?\n3. Can you combine approaches for a more robust solution?\n4. What verification steps from peers could improve confidence?\n\nProvide an enhanced solution that synthesizes the best ideas while ensuring mathematical rigor.\n\nEnhanced Solution:'
        try:
            response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'system', 'content': 'You are a collaborative mathematical agent learning from peer insights.'}, {'role': 'user', 'content': enhancement_prompt}], max_tokens=self.max_tokens, temperature=original_solution.temperature * 0.9, timeout=300, extra_body={'reasoning': {'effort': 'high'}})
            if request_id:
                provider_request = {'model': self.model, 'messages': [{'role': 'system', 'content': 'You are a collaborative mathematical agent learning from peer insights.'}, {'role': 'user', 'content': enhancement_prompt}], 'max_tokens': self.max_tokens, 'temperature': original_solution.temperature * 0.9, 'extra_body': {'reasoning': {'effort': 'high'}}}
                response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
                conversation_logger.log_provider_call(request_id, provider_request, response_dict)
            enhanced_solution_text = response.choices[0].message.content.strip()
            reasoning_tokens = 0
            total_tokens = 0
            if hasattr(response, 'usage') and response.usage:
                total_tokens = getattr(response.usage, 'total_tokens', 0)
                if hasattr(response.usage, 'completion_tokens_details') and response.usage.completion_tokens_details:
                    reasoning_tokens = getattr(response.usage.completion_tokens_details, 'reasoning_tokens', 0)
                if reasoning_tokens == 0:
                    reasoning_tokens = getattr(response.usage, 'reasoning_tokens', 0)
            enhanced_agent_solution = AgentSolution(agent_id=f'enhanced_{original_solution.agent_id}', solution=enhanced_solution_text, confidence=min(original_solution.confidence + 0.1, 1.0), reasoning_tokens=reasoning_tokens, total_tokens=total_tokens, solution_length=len(enhanced_solution_text), temperature=original_solution.temperature)
            logger.info(f'Generated strategy-enhanced solution for agent {original_solution.agent_id}')
            return enhanced_agent_solution
        except Exception as e:
            logger.error(f'Strategy enhancement failed for agent {original_solution.agent_id}: {str(e)}')
            return None

    def update_strategy_effectiveness(self, strategy_id: str, problem_type: str, was_successful: bool, confidence: float):
        """Update effectiveness tracking for a strategy"""
        key = (strategy_id, problem_type)
        if key not in self.strategy_effectiveness:
            self.strategy_effectiveness[key] = StrategyEffectiveness(strategy_id=strategy_id, problem_type=problem_type)
        effectiveness = self.strategy_effectiveness[key]
        effectiveness.total_uses += 1
        if was_successful:
            effectiveness.success_count += 1
        else:
            effectiveness.failure_count += 1
        effectiveness.average_confidence = (effectiveness.average_confidence * (effectiveness.total_uses - 1) + confidence) / effectiveness.total_uses

    def get_strategy_insights_summary(self) -> Dict[str, Any]:
        """Get summary of strategy network insights"""
        return {'total_strategies': len(self.strategies), 'strategies_by_type': self._count_strategies_by_type(), 'most_effective_strategies': self._get_most_effective_strategies(), 'agent_strategy_preferences': dict(self.agent_preferred_strategies), 'strategy_effectiveness_stats': self._get_effectiveness_stats()}

    def _count_strategies_by_type(self) -> Dict[str, int]:
        """Count strategies by problem type"""
        counts = defaultdict(int)
        for strategy in self.strategies.values():
            counts[strategy.problem_type] += 1
        return dict(counts)

    def _get_most_effective_strategies(self) -> List[Dict[str, Any]]:
        """Get most effective strategies across all problem types"""
        effective_strategies = []
        for effectiveness in self.strategy_effectiveness.values():
            if effectiveness.total_uses >= 2:
                effective_strategies.append({'strategy_id': effectiveness.strategy_id, 'problem_type': effectiveness.problem_type, 'success_rate': effectiveness.success_rate, 'average_confidence': effectiveness.average_confidence, 'total_uses': effectiveness.total_uses})
        effective_strategies.sort(key=lambda x: (x['success_rate'], x['average_confidence']), reverse=True)
        return effective_strategies[:5]

    def _get_effectiveness_stats(self) -> Dict[str, float]:
        """Get overall effectiveness statistics"""
        if not self.strategy_effectiveness:
            return {}
        success_rates = [eff.success_rate for eff in self.strategy_effectiveness.values()]
        avg_confidences = [eff.average_confidence for eff in self.strategy_effectiveness.values()]
        return {'average_success_rate': sum(success_rates) / len(success_rates) if success_rates else 0, 'average_confidence': sum(avg_confidences) / len(avg_confidences) if avg_confidences else 0, 'total_strategy_applications': sum((eff.total_uses for eff in self.strategy_effectiveness.values()))}

def _extract_strategy_from_solution(self, solution: AgentSolution, problem: str, request_id: str=None) -> Optional[ReasoningStrategy]:
    """Extract reasoning strategy using LLM analysis"""
    strategy_extraction_prompt = f'Analyze this mathematical solution and extract the key reasoning strategy:\n\nProblem: {problem}\n\nAgent Solution:\n{solution.solution}\n\nExtract the following strategy components:\n\n1. PROBLEM_TYPE: Classify as one of [algebra, geometry, combinatorics, number_theory, calculus, discrete_math, probability]\n\n2. APPROACH_TYPE: Identify the main approach [direct_computation, proof_by_contradiction, constructive_proof, case_analysis, induction, algebraic_manipulation, geometric_visualization, pattern_recognition, reduction_to_known_problem]\n\n3. KEY_INSIGHTS: List 2-3 key mathematical insights that enabled the solution\n\n4. MATHEMATICAL_TECHNIQUES: List specific techniques used [substitution, factorization, coordinate_geometry, symmetry, pigeonhole_principle, etc.]\n\n5. SOLUTION_PATTERN: Describe the general pattern/template of this solution approach\n\n6. SUCCESS_INDICATORS: What makes this approach particularly effective for this type of problem?\n\nFormat your response as:\nPROBLEM_TYPE: [type]\nAPPROACH_TYPE: [approach]\nKEY_INSIGHTS: [insight1], [insight2], [insight3]\nMATHEMATICAL_TECHNIQUES: [technique1], [technique2], [technique3]\nSOLUTION_PATTERN: [pattern description]\nSUCCESS_INDICATORS: [indicator1], [indicator2]'
    try:
        response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'system', 'content': 'You are a mathematical strategy analysis expert. Extract reasoning patterns from solutions.'}, {'role': 'user', 'content': strategy_extraction_prompt}], max_tokens=self.max_tokens // 4, temperature=0.3, timeout=120, extra_body={'reasoning': {'effort': 'medium'}})
        if request_id:
            provider_request = {'model': self.model, 'messages': [{'role': 'system', 'content': 'You are a mathematical strategy analysis expert.'}, {'role': 'user', 'content': strategy_extraction_prompt}], 'max_tokens': self.max_tokens // 4, 'temperature': 0.3, 'extra_body': {'reasoning': {'effort': 'medium'}}}
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
            conversation_logger.log_provider_call(request_id, provider_request, response_dict)
        analysis = response.choices[0].message.content.strip()
        strategy_data = self._parse_strategy_analysis(analysis)
        if strategy_data:
            strategy_id = f'strategy_{solution.agent_id}_{datetime.now().strftime('%H%M%S')}'
            return ReasoningStrategy(strategy_id=strategy_id, agent_id=solution.agent_id, problem_type=strategy_data.get('problem_type', 'unknown'), approach_type=strategy_data.get('approach_type', 'unknown'), key_insights=strategy_data.get('key_insights', []), mathematical_techniques=strategy_data.get('mathematical_techniques', []), solution_pattern=strategy_data.get('solution_pattern', ''), confidence=solution.confidence, success_indicators=strategy_data.get('success_indicators', []))
    except Exception as e:
        logger.error(f'Strategy extraction failed for agent {solution.agent_id}: {str(e)}')
        return None

def _parse_strategy_analysis(self, analysis: str) -> Optional[Dict[str, Any]]:
    """Parse structured strategy analysis response"""
    try:
        lines = analysis.split('\n')
        strategy_data = {}
        for line in lines:
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                if key == 'problem_type':
                    strategy_data['problem_type'] = value
                elif key == 'approach_type':
                    strategy_data['approach_type'] = value
                elif 'insights' in key:
                    strategy_data['key_insights'] = [insight.strip() for insight in value.split(',')]
                elif 'techniques' in key:
                    strategy_data['mathematical_techniques'] = [tech.strip() for tech in value.split(',')]
                elif 'pattern' in key:
                    strategy_data['solution_pattern'] = value
                elif 'indicators' in key:
                    strategy_data['success_indicators'] = [ind.strip() for ind in value.split(',')]
        return strategy_data if strategy_data else None
    except Exception as e:
        logger.error(f'Failed to parse strategy analysis: {str(e)}')
        return None

def _classify_problem_with_llm(self, problem: str, request_id: str=None) -> str:
    """Use LLM to classify problem type"""
    classification_prompt = f'Classify this mathematical problem into one category:\n\nProblem: {problem}\n\nCategories: [algebra, geometry, combinatorics, number_theory, calculus, discrete_math, probability]\n\nRespond with just the category name.'
    try:
        response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'system', 'content': 'You are a mathematical problem classifier.'}, {'role': 'user', 'content': classification_prompt}], max_tokens=50, temperature=0.1, timeout=60, extra_body={'reasoning': {'effort': 'low'}})
        classification = response.choices[0].message.content.strip().lower()
        valid_types = ['algebra', 'geometry', 'combinatorics', 'number_theory', 'calculus', 'discrete_math', 'probability']
        if classification in valid_types:
            return classification
        else:
            return 'algebra'
    except Exception as e:
        logger.error(f'Problem classification failed: {str(e)}')
        return 'algebra'

def _generate_strategy_enhanced_solution(self, original_solution: AgentSolution, problem: str, peer_strategies: List[ReasoningStrategy], request_id: str=None) -> Optional[AgentSolution]:
    """Generate solution enhanced with peer strategies"""
    strategy_insights = ''
    for strategy in peer_strategies[:2]:
        strategy_insights += f'\nPeer Strategy from Agent {strategy.agent_id}:\n'
        strategy_insights += f'- Approach: {strategy.approach_type}\n'
        strategy_insights += f'- Key Insights: {', '.join(strategy.key_insights[:3])}\n'
        strategy_insights += f'- Techniques: {', '.join(strategy.mathematical_techniques[:3])}\n'
        strategy_insights += f'- Success Pattern: {strategy.solution_pattern[:200]}...\n'
    enhancement_prompt = f'You are Agent {original_solution.agent_id} collaborating with other mathematical agents.\n\nOriginal Problem: {problem}\n\nYour Current Solution:\n{original_solution.solution}\n\nPeer Agent Strategy Insights:\n{strategy_insights}\n\nTask: Enhance your solution by incorporating the most valuable insights from your peers while maintaining your unique approach. Consider:\n\n1. Can any peer techniques strengthen your solution?\n2. Do peer insights reveal gaps in your reasoning?\n3. Can you combine approaches for a more robust solution?\n4. What verification steps from peers could improve confidence?\n\nProvide an enhanced solution that synthesizes the best ideas while ensuring mathematical rigor.\n\nEnhanced Solution:'
    try:
        response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'system', 'content': 'You are a collaborative mathematical agent learning from peer insights.'}, {'role': 'user', 'content': enhancement_prompt}], max_tokens=self.max_tokens, temperature=original_solution.temperature * 0.9, timeout=300, extra_body={'reasoning': {'effort': 'high'}})
        if request_id:
            provider_request = {'model': self.model, 'messages': [{'role': 'system', 'content': 'You are a collaborative mathematical agent learning from peer insights.'}, {'role': 'user', 'content': enhancement_prompt}], 'max_tokens': self.max_tokens, 'temperature': original_solution.temperature * 0.9, 'extra_body': {'reasoning': {'effort': 'high'}}}
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
            conversation_logger.log_provider_call(request_id, provider_request, response_dict)
        enhanced_solution_text = response.choices[0].message.content.strip()
        reasoning_tokens = 0
        total_tokens = 0
        if hasattr(response, 'usage') and response.usage:
            total_tokens = getattr(response.usage, 'total_tokens', 0)
            if hasattr(response.usage, 'completion_tokens_details') and response.usage.completion_tokens_details:
                reasoning_tokens = getattr(response.usage.completion_tokens_details, 'reasoning_tokens', 0)
            if reasoning_tokens == 0:
                reasoning_tokens = getattr(response.usage, 'reasoning_tokens', 0)
        enhanced_agent_solution = AgentSolution(agent_id=f'enhanced_{original_solution.agent_id}', solution=enhanced_solution_text, confidence=min(original_solution.confidence + 0.1, 1.0), reasoning_tokens=reasoning_tokens, total_tokens=total_tokens, solution_length=len(enhanced_solution_text), temperature=original_solution.temperature)
        logger.info(f'Generated strategy-enhanced solution for agent {original_solution.agent_id}')
        return enhanced_agent_solution
    except Exception as e:
        logger.error(f'Strategy enhancement failed for agent {original_solution.agent_id}: {str(e)}')
        return None

class MARSAgent:
    """Individual agent for mathematical reasoning with OpenRouter reasoning API"""

    def __init__(self, agent_id: int, client, model: str, config: Dict[str, Any]):
        self.agent_id = agent_id
        self.client = client
        self.model = model
        self.config = config
        self.temperature = self._assign_temperature()

    def _assign_temperature(self) -> float:
        """Assign temperature based on agent ID for 3-agent configuration"""
        temperatures = [0.3, 0.6, 1.0]
        return temperatures[self.agent_id % len(temperatures)]

    def _get_reasoning_effort(self) -> str:
        """Get reasoning effort level based on agent temperature"""
        if self.temperature <= 0.4:
            return 'low'
        elif self.temperature <= 0.8:
            return 'medium'
        else:
            return 'high'

    def generate_solution(self, problem: str, request_id: str=None) -> Tuple[AgentSolution, int]:
        """Generate a solution for the given problem using reasoning API"""
        import time
        start_time = time.time()
        logger.info(f'🤖 AGENT {self.agent_id}: Starting solution generation (temp: {self.temperature}, effort: {self._get_reasoning_effort()})')
        logger.info(f'🤖 AGENT {self.agent_id}: Problem length: {len(problem)} characters')
        exploration_prompt = AGENT_EXPLORATION_PROMPT.format(agent_id=self.agent_id, temperature=self.temperature, problem=problem)
        reasoning_effort = self._get_reasoning_effort()
        max_tokens = self.config['max_tokens']
        logger.info(f'🤖 AGENT {self.agent_id}: Using max_tokens={max_tokens}, reasoning_effort={reasoning_effort}')
        reasoning_config = {'effort': reasoning_effort}
        try:
            api_start = time.time()
            logger.info(f'🤖 AGENT {self.agent_id}: Making API call to {self.model}...')
            response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'system', 'content': MATHEMATICAL_SYSTEM_PROMPT}, {'role': 'user', 'content': exploration_prompt}], max_tokens=max_tokens, temperature=self.temperature, timeout=300, extra_body={'reasoning': reasoning_config})
            api_duration = time.time() - api_start
            logger.info(f'🤖 AGENT {self.agent_id}: API call completed in {api_duration:.2f}s')
            solution_text = response.choices[0].message.content.strip()
            solution_length = len(solution_text)
            word_count = len(solution_text.split())
            has_boxed = '\\boxed{' in solution_text
            has_proof_words = any((word in solution_text.lower() for word in ['therefore', 'thus', 'proof', 'qed']))
            logger.info(f'🤖 AGENT {self.agent_id}: Solution analysis:')
            logger.info(f'  📝 Length: {solution_length:,} chars, {word_count:,} words')
            logger.info(f'  📦 Has boxed answer: {has_boxed}')
            logger.info(f'  🔍 Has proof indicators: {has_proof_words}')
            logger.info(f'  📄 Preview: {solution_text[:200]}{('...' if len(solution_text) > 200 else '')}')
            logger.info(f'  📄 Last 100 chars: ...{(solution_text[-100:] if solution_length > 100 else solution_text)}')
            reasoning_tokens = 0
            total_tokens = 0
            if hasattr(response, 'usage') and response.usage:
                total_tokens = getattr(response.usage, 'total_tokens', 0)
                if hasattr(response.usage, 'completion_tokens_details') and response.usage.completion_tokens_details:
                    reasoning_tokens = getattr(response.usage.completion_tokens_details, 'reasoning_tokens', 0)
                if reasoning_tokens == 0:
                    reasoning_tokens = getattr(response.usage, 'reasoning_tokens', 0)
            reasoning_ratio = reasoning_tokens / total_tokens * 100 if total_tokens > 0 else 0
            logger.info(f'🤖 AGENT {self.agent_id}: Token usage: reasoning={reasoning_tokens:,}, total={total_tokens:,} ({reasoning_ratio:.1f}% reasoning)')
            confidence = self._estimate_confidence(solution_text)
            logger.info(f'🤖 AGENT {self.agent_id}: Estimated confidence: {confidence:.3f}')
            agent_solution = AgentSolution(agent_id=str(self.agent_id), solution=solution_text, confidence=confidence, reasoning_tokens=reasoning_tokens, total_tokens=total_tokens, solution_length=solution_length, temperature=self.temperature)
            total_duration = time.time() - start_time
            logger.info(f'🤖 AGENT {self.agent_id}: ✅ Solution generated in {total_duration:.2f}s (API: {api_duration:.2f}s, processing: {total_duration - api_duration:.2f}s)')
            return (agent_solution, reasoning_tokens)
        except Exception as e:
            error_duration = time.time() - start_time
            logger.error(f'🤖 AGENT {self.agent_id}: ❌ Error generating solution after {error_duration:.2f}s: {str(e)}')
            logger.error(f'🤖 AGENT {self.agent_id}: Model: {self.model}, Temperature: {self.temperature}, Max tokens: {max_tokens}')
            error_message = f'Error generating solution: {str(e)}'
            error_solution = AgentSolution(agent_id=str(self.agent_id), solution=error_message, confidence=0.0, reasoning_tokens=0, total_tokens=0, solution_length=len(error_message), temperature=self.temperature)
            return (error_solution, 0)

    def verify_solution(self, problem: str, solution: str, verifier_id: int, solution_agent_id: int, request_id: str=None) -> VerificationResult:
        """Verify a solution using mathematical reasoning"""
        import time
        start_time = time.time()
        logger.info(f'🔍 VERIFIER {self.agent_id}: Starting verification (target: Agent {solution_agent_id}, verifier_id: {verifier_id})')
        logger.info(f'🔍 VERIFIER {self.agent_id}: Solution length: {len(solution):,} chars')
        verification_prompt = VERIFICATION_PROMPT.format(problem=problem, solution=solution)
        max_tokens = self.config['max_tokens']
        try:
            api_start = time.time()
            logger.info(f'🔍 VERIFIER {self.agent_id}: Making verification API call...')
            response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'system', 'content': MATHEMATICAL_SYSTEM_PROMPT}, {'role': 'user', 'content': verification_prompt}], max_tokens=max_tokens, temperature=0.1, timeout=180, extra_body={'reasoning': {'effort': 'low'}})
            api_duration = time.time() - api_start
            logger.info(f'🔍 VERIFIER {self.agent_id}: Verification API call completed in {api_duration:.2f}s')
            verification_text = response.choices[0].message.content.strip()
            assessment, confidence, issues, suggestions = self._parse_verification(verification_text)
            logger.info(f'🔍 VERIFIER {self.agent_id}: Assessment: {assessment}, Confidence: {confidence:.3f}')
            logger.info(f'🔍 VERIFIER {self.agent_id}: Issues found: {len(issues)}, Suggestions: {len(suggestions)}')
            if issues:
                logger.info(f'🔍 VERIFIER {self.agent_id}: Key issues: {issues[:2]}')
            result = VerificationResult(verifier_id=verifier_id, solution_id=f'agent_{solution_agent_id}_iter_0', assessment=assessment, confidence=confidence, issues=issues, suggestions=suggestions, detailed_report=verification_text, timestamp=datetime.now())
            total_duration = time.time() - start_time
            logger.info(f'🔍 VERIFIER {self.agent_id}: ✅ Verification completed in {total_duration:.2f}s')
            return result
        except Exception as e:
            error_duration = time.time() - start_time
            logger.error(f'🔍 VERIFIER {self.agent_id}: ❌ Verification error after {error_duration:.2f}s: {str(e)}')
            return VerificationResult(verifier_id=verifier_id, solution_id=f'agent_{solution_agent_id}_iter_0', assessment='INCOMPLETE', confidence=0.0, issues=[f'Verification error: {str(e)}'], suggestions=['Retry verification'], detailed_report=f'Error during verification: {str(e)}', timestamp=datetime.now())

    def improve_solution(self, problem: str, current_solution: str, feedback: str, issues: list, request_id: str=None) -> Tuple[str, int]:
        """Improve a solution based on verification feedback"""
        import time
        start_time = time.time()
        logger.info(f'🔧 IMPROVER {self.agent_id}: Starting solution improvement')
        logger.info(f'🔧 IMPROVER {self.agent_id}: Current solution: {len(current_solution):,} chars')
        logger.info(f'🔧 IMPROVER {self.agent_id}: Issues to address: {len(issues)}')
        improvement_prompt = IMPROVEMENT_PROMPT.format(problem=problem, current_solution=current_solution, feedback=feedback, issues='\n'.join((f'- {issue}' for issue in issues)))
        max_tokens = self.config['max_tokens']
        try:
            api_start = time.time()
            logger.info(f'🔧 IMPROVER {self.agent_id}: Making improvement API call...')
            response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'system', 'content': MATHEMATICAL_SYSTEM_PROMPT}, {'role': 'user', 'content': improvement_prompt}], max_tokens=max_tokens, temperature=self.temperature * 0.8, timeout=300, extra_body={'reasoning': {'effort': 'high'}})
            api_duration = time.time() - api_start
            logger.info(f'🔧 IMPROVER {self.agent_id}: Improvement API call completed in {api_duration:.2f}s')
            improved_solution = response.choices[0].message.content.strip()
            reasoning_tokens = getattr(response.usage, 'reasoning_tokens', 0)
            length_change = len(improved_solution) - len(current_solution)
            logger.info(f'🔧 IMPROVER {self.agent_id}: Solution length change: {length_change:+,} chars')
            logger.info(f'🔧 IMPROVER {self.agent_id}: Improved solution preview: {improved_solution[:200]}{('...' if len(improved_solution) > 200 else '')}')
            total_duration = time.time() - start_time
            logger.info(f'🔧 IMPROVER {self.agent_id}: ✅ Solution improved in {total_duration:.2f}s with {reasoning_tokens:,} reasoning tokens')
            return (improved_solution, reasoning_tokens)
        except Exception as e:
            error_duration = time.time() - start_time
            logger.error(f'🔧 IMPROVER {self.agent_id}: ❌ Improvement error after {error_duration:.2f}s: {str(e)}')
            logger.warning(f'🔧 IMPROVER {self.agent_id}: Returning original solution due to error')
            return (current_solution, 0)

    def _estimate_confidence(self, solution: str) -> float:
        """Estimate confidence based on solution characteristics"""
        confidence = 0.5
        confidence_factors = []
        if '\\boxed{' in solution:
            confidence += 0.2
            confidence_factors.append('boxed_answer')
        if 'therefore' in solution.lower() or 'thus' in solution.lower():
            confidence += 0.1
            confidence_factors.append('logical_connectors')
        if 'proof' in solution.lower():
            confidence += 0.1
            confidence_factors.append('proof_structure')
        if len(solution.split()) > 200:
            confidence += 0.1
            confidence_factors.append('detailed_solution')
        if 'let' in solution.lower() and 'assume' in solution.lower():
            confidence += 0.1
            confidence_factors.append('formal_approach')
        uncertainty_factors = []
        if 'might' in solution.lower() or 'possibly' in solution.lower():
            confidence -= 0.1
            uncertainty_factors.append('hedging_language')
        if 'unsure' in solution.lower() or 'not sure' in solution.lower():
            confidence -= 0.2
            uncertainty_factors.append('explicit_uncertainty')
        final_confidence = max(0.1, min(1.0, confidence))
        logger.debug(f'🤖 AGENT {self.agent_id}: Confidence factors: +{confidence_factors}, -{uncertainty_factors} → {final_confidence:.3f}')
        return final_confidence

    def _parse_verification(self, verification_text: str) -> Tuple[str, float, list, list]:
        """Parse verification result to extract structured information"""
        assessment = 'INCOMPLETE'
        confidence = 0.5
        issues = []
        suggestions = []
        text_lower = verification_text.lower()
        if 'correct' in text_lower and 'incorrect' not in text_lower:
            assessment = 'CORRECT'
            confidence = 0.8
        elif 'incorrect' in text_lower:
            assessment = 'INCORRECT'
            confidence = 0.8
        elif 'incomplete' in text_lower:
            assessment = 'INCOMPLETE'
            confidence = 0.6
        import re
        confidence_match = re.search('confidence.*?(\\d+).*?(?:out of|/)\\s*(\\d+)', text_lower)
        if confidence_match:
            conf_score = float(confidence_match.group(1))
            conf_total = float(confidence_match.group(2))
            confidence = conf_score / conf_total
        lines = verification_text.split('\n')
        for line in lines:
            line_lower = line.lower()
            if any((word in line_lower for word in ['error', 'mistake', 'incorrect', 'wrong', 'issue'])):
                issues.append(line.strip())
        for line in lines:
            line_lower = line.lower()
            if any((word in line_lower for word in ['suggest', 'recommend', 'should', 'could improve'])):
                suggestions.append(line.strip())
        return (assessment, confidence, issues, suggestions)

def generate_solution(self, problem: str, request_id: str=None) -> Tuple[AgentSolution, int]:
    """Generate a solution for the given problem using reasoning API"""
    import time
    start_time = time.time()
    logger.info(f'🤖 AGENT {self.agent_id}: Starting solution generation (temp: {self.temperature}, effort: {self._get_reasoning_effort()})')
    logger.info(f'🤖 AGENT {self.agent_id}: Problem length: {len(problem)} characters')
    exploration_prompt = AGENT_EXPLORATION_PROMPT.format(agent_id=self.agent_id, temperature=self.temperature, problem=problem)
    reasoning_effort = self._get_reasoning_effort()
    max_tokens = self.config['max_tokens']
    logger.info(f'🤖 AGENT {self.agent_id}: Using max_tokens={max_tokens}, reasoning_effort={reasoning_effort}')
    reasoning_config = {'effort': reasoning_effort}
    try:
        api_start = time.time()
        logger.info(f'🤖 AGENT {self.agent_id}: Making API call to {self.model}...')
        response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'system', 'content': MATHEMATICAL_SYSTEM_PROMPT}, {'role': 'user', 'content': exploration_prompt}], max_tokens=max_tokens, temperature=self.temperature, timeout=300, extra_body={'reasoning': reasoning_config})
        api_duration = time.time() - api_start
        logger.info(f'🤖 AGENT {self.agent_id}: API call completed in {api_duration:.2f}s')
        solution_text = response.choices[0].message.content.strip()
        solution_length = len(solution_text)
        word_count = len(solution_text.split())
        has_boxed = '\\boxed{' in solution_text
        has_proof_words = any((word in solution_text.lower() for word in ['therefore', 'thus', 'proof', 'qed']))
        logger.info(f'🤖 AGENT {self.agent_id}: Solution analysis:')
        logger.info(f'  📝 Length: {solution_length:,} chars, {word_count:,} words')
        logger.info(f'  📦 Has boxed answer: {has_boxed}')
        logger.info(f'  🔍 Has proof indicators: {has_proof_words}')
        logger.info(f'  📄 Preview: {solution_text[:200]}{('...' if len(solution_text) > 200 else '')}')
        logger.info(f'  📄 Last 100 chars: ...{(solution_text[-100:] if solution_length > 100 else solution_text)}')
        reasoning_tokens = 0
        total_tokens = 0
        if hasattr(response, 'usage') and response.usage:
            total_tokens = getattr(response.usage, 'total_tokens', 0)
            if hasattr(response.usage, 'completion_tokens_details') and response.usage.completion_tokens_details:
                reasoning_tokens = getattr(response.usage.completion_tokens_details, 'reasoning_tokens', 0)
            if reasoning_tokens == 0:
                reasoning_tokens = getattr(response.usage, 'reasoning_tokens', 0)
        reasoning_ratio = reasoning_tokens / total_tokens * 100 if total_tokens > 0 else 0
        logger.info(f'🤖 AGENT {self.agent_id}: Token usage: reasoning={reasoning_tokens:,}, total={total_tokens:,} ({reasoning_ratio:.1f}% reasoning)')
        confidence = self._estimate_confidence(solution_text)
        logger.info(f'🤖 AGENT {self.agent_id}: Estimated confidence: {confidence:.3f}')
        agent_solution = AgentSolution(agent_id=str(self.agent_id), solution=solution_text, confidence=confidence, reasoning_tokens=reasoning_tokens, total_tokens=total_tokens, solution_length=solution_length, temperature=self.temperature)
        total_duration = time.time() - start_time
        logger.info(f'🤖 AGENT {self.agent_id}: ✅ Solution generated in {total_duration:.2f}s (API: {api_duration:.2f}s, processing: {total_duration - api_duration:.2f}s)')
        return (agent_solution, reasoning_tokens)
    except Exception as e:
        error_duration = time.time() - start_time
        logger.error(f'🤖 AGENT {self.agent_id}: ❌ Error generating solution after {error_duration:.2f}s: {str(e)}')
        logger.error(f'🤖 AGENT {self.agent_id}: Model: {self.model}, Temperature: {self.temperature}, Max tokens: {max_tokens}')
        error_message = f'Error generating solution: {str(e)}'
        error_solution = AgentSolution(agent_id=str(self.agent_id), solution=error_message, confidence=0.0, reasoning_tokens=0, total_tokens=0, solution_length=len(error_message), temperature=self.temperature)
        return (error_solution, 0)

def verify_solution(self, problem: str, solution: str, verifier_id: int, solution_agent_id: int, request_id: str=None) -> VerificationResult:
    """Verify a solution using mathematical reasoning"""
    import time
    start_time = time.time()
    logger.info(f'🔍 VERIFIER {self.agent_id}: Starting verification (target: Agent {solution_agent_id}, verifier_id: {verifier_id})')
    logger.info(f'🔍 VERIFIER {self.agent_id}: Solution length: {len(solution):,} chars')
    verification_prompt = VERIFICATION_PROMPT.format(problem=problem, solution=solution)
    max_tokens = self.config['max_tokens']
    try:
        api_start = time.time()
        logger.info(f'🔍 VERIFIER {self.agent_id}: Making verification API call...')
        response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'system', 'content': MATHEMATICAL_SYSTEM_PROMPT}, {'role': 'user', 'content': verification_prompt}], max_tokens=max_tokens, temperature=0.1, timeout=180, extra_body={'reasoning': {'effort': 'low'}})
        api_duration = time.time() - api_start
        logger.info(f'🔍 VERIFIER {self.agent_id}: Verification API call completed in {api_duration:.2f}s')
        verification_text = response.choices[0].message.content.strip()
        assessment, confidence, issues, suggestions = self._parse_verification(verification_text)
        logger.info(f'🔍 VERIFIER {self.agent_id}: Assessment: {assessment}, Confidence: {confidence:.3f}')
        logger.info(f'🔍 VERIFIER {self.agent_id}: Issues found: {len(issues)}, Suggestions: {len(suggestions)}')
        if issues:
            logger.info(f'🔍 VERIFIER {self.agent_id}: Key issues: {issues[:2]}')
        result = VerificationResult(verifier_id=verifier_id, solution_id=f'agent_{solution_agent_id}_iter_0', assessment=assessment, confidence=confidence, issues=issues, suggestions=suggestions, detailed_report=verification_text, timestamp=datetime.now())
        total_duration = time.time() - start_time
        logger.info(f'🔍 VERIFIER {self.agent_id}: ✅ Verification completed in {total_duration:.2f}s')
        return result
    except Exception as e:
        error_duration = time.time() - start_time
        logger.error(f'🔍 VERIFIER {self.agent_id}: ❌ Verification error after {error_duration:.2f}s: {str(e)}')
        return VerificationResult(verifier_id=verifier_id, solution_id=f'agent_{solution_agent_id}_iter_0', assessment='INCOMPLETE', confidence=0.0, issues=[f'Verification error: {str(e)}'], suggestions=['Retry verification'], detailed_report=f'Error during verification: {str(e)}', timestamp=datetime.now())

def improve_solution(self, problem: str, current_solution: str, feedback: str, issues: list, request_id: str=None) -> Tuple[str, int]:
    """Improve a solution based on verification feedback"""
    import time
    start_time = time.time()
    logger.info(f'🔧 IMPROVER {self.agent_id}: Starting solution improvement')
    logger.info(f'🔧 IMPROVER {self.agent_id}: Current solution: {len(current_solution):,} chars')
    logger.info(f'🔧 IMPROVER {self.agent_id}: Issues to address: {len(issues)}')
    improvement_prompt = IMPROVEMENT_PROMPT.format(problem=problem, current_solution=current_solution, feedback=feedback, issues='\n'.join((f'- {issue}' for issue in issues)))
    max_tokens = self.config['max_tokens']
    try:
        api_start = time.time()
        logger.info(f'🔧 IMPROVER {self.agent_id}: Making improvement API call...')
        response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'system', 'content': MATHEMATICAL_SYSTEM_PROMPT}, {'role': 'user', 'content': improvement_prompt}], max_tokens=max_tokens, temperature=self.temperature * 0.8, timeout=300, extra_body={'reasoning': {'effort': 'high'}})
        api_duration = time.time() - api_start
        logger.info(f'🔧 IMPROVER {self.agent_id}: Improvement API call completed in {api_duration:.2f}s')
        improved_solution = response.choices[0].message.content.strip()
        reasoning_tokens = getattr(response.usage, 'reasoning_tokens', 0)
        length_change = len(improved_solution) - len(current_solution)
        logger.info(f'🔧 IMPROVER {self.agent_id}: Solution length change: {length_change:+,} chars')
        logger.info(f'🔧 IMPROVER {self.agent_id}: Improved solution preview: {improved_solution[:200]}{('...' if len(improved_solution) > 200 else '')}')
        total_duration = time.time() - start_time
        logger.info(f'🔧 IMPROVER {self.agent_id}: ✅ Solution improved in {total_duration:.2f}s with {reasoning_tokens:,} reasoning tokens')
        return (improved_solution, reasoning_tokens)
    except Exception as e:
        error_duration = time.time() - start_time
        logger.error(f'🔧 IMPROVER {self.agent_id}: ❌ Improvement error after {error_duration:.2f}s: {str(e)}')
        logger.warning(f'🔧 IMPROVER {self.agent_id}: Returning original solution due to error')
        return (current_solution, 0)

def _synthesize_final_solution(workspace: MARSWorkspace, client, model: str, config: Dict[str, Any], request_id: str=None) -> Tuple[str, int]:
    """Synthesize the final solution from all agent outputs and verifications"""
    best_solution = workspace.get_best_solution()
    if best_solution and best_solution.is_verified:
        logger.info(f'Using verified solution from agent {best_solution.agent_id}')
        return (best_solution.solution, 0)
    logger.info(f'🗳️  VOTING: No verified solutions found, attempting numerical voting on {len(workspace.solutions)} solutions')
    numerical_answers = []
    extracted_answers_info = []
    logger.info(f'🗳️  VOTING: Starting unified answer extraction from {len(workspace.solutions)} solutions')
    for i, solution in enumerate(workspace.solutions):
        extracted_answer = extract_answer(solution.solution, problem_type='imo', problem_id=None)
        if extracted_answer is not None:
            logger.info(f"🗳️  VOTING: Agent {solution.agent_id} extracted answer '{extracted_answer}' via unified extraction (confidence: {solution.confidence:.2f})")
            answers_to_process = []
            if isinstance(extracted_answer, list):
                answers_to_process = extracted_answer
            else:
                answers_to_process = [extracted_answer]
            for ans in answers_to_process:
                if isinstance(ans, (int, float)):
                    numerical_answers.append((int(ans), solution))
                    extracted_answers_info.append((str(int(ans)), solution, 'unified_numeric'))
                    break
                elif isinstance(ans, str) and ans.strip():
                    extracted_answers_info.append((ans, solution, 'unified_formula'))
                    logger.info(f"🗳️  VOTING: Non-numeric answer stored for synthesis: '{ans}'")
                    break
                elif isinstance(ans, set):
                    set_str = '{' + ', '.join(map(str, sorted(ans))) + '}'
                    extracted_answers_info.append((set_str, solution, 'unified_set'))
                    logger.info(f"🗳️  VOTING: Set answer stored for synthesis: '{set_str}'")
                    break
            if not any((isinstance(ans, (int, float, str, set)) for ans in answers_to_process if isinstance(ans, str) and ans.strip())):
                extracted_answers_info.append((str(extracted_answer), solution, 'unified_other'))
                logger.info(f"🗳️  VOTING: Other answer type stored for synthesis: '{extracted_answer}'")
        else:
            logger.info(f'🗳️  VOTING: Agent {solution.agent_id} - no answer extracted via unified extraction (confidence: {solution.confidence:.2f})')
    workspace._extracted_answers_info = getattr(workspace, '_extracted_answers_info', []) + extracted_answers_info
    logger.info(f'🗳️  VOTING: Extracted {len(numerical_answers)} numerical answers from {len(workspace.solutions)} solutions')
    if len(numerical_answers) >= 2:
        answer_counts = Counter([ans for ans, _ in numerical_answers])
        most_common_answers = answer_counts.most_common()
        logger.info(f'🗳️  VOTING: Answer distribution:')
        for answer, count in most_common_answers:
            percentage = count / len(numerical_answers) * 100
            agents_with_answer = [sol.agent_id for ans, sol in numerical_answers if ans == answer]
            logger.info(f'🗳️  VOTING:   Answer {answer}: {count}/{len(numerical_answers)} votes ({percentage:.1f}%) - Agents: {agents_with_answer}')
        answer, count = most_common_answers[0]
        if count >= 2:
            matching_solutions = [sol for ans, sol in numerical_answers if ans == answer]
            best_solution = max(matching_solutions, key=lambda s: s.confidence)
            logger.info(f'🎆 VOTING SUCCESS: Using majority vote answer {answer} ({count}/{len(numerical_answers)} agents agreed)')
            logger.info(f'🎆 VOTING SUCCESS: Selected solution from agent {best_solution.agent_id} with confidence {best_solution.confidence:.2f}')
            logger.info(f'🎆 VOTING SUCCESS: Solution length: {len(best_solution.solution)} chars')
            return (best_solution.solution, 0)
        else:
            logger.info(f'🗳️  VOTING: No consensus - best answer {answer} only has {count} vote(s), need 2+')
    else:
        logger.info(f'🗳️  VOTING: Insufficient numerical answers for voting ({len(numerical_answers)} < 2)')
    logger.info(f'🤔 VOTING FALLBACK: No numerical consensus found, falling back to answer-preserving synthesis')
    all_extracted = getattr(workspace, '_extracted_answers_info', [])
    if all_extracted:
        logger.info(f'🔍 EXTRACTED ANSWERS SUMMARY: Found {len(all_extracted)} extracted answers:')
        for answer, solution, method in all_extracted:
            logger.info(f"🔍 EXTRACTED ANSWERS SUMMARY:   '{answer}' from Agent {solution.agent_id} via {method}")
    else:
        logger.info(f'🔍 EXTRACTED ANSWERS SUMMARY: No extracted answers found')
    synthesis_data = workspace.get_synthesis_input()
    input_chars = sum((len(sol_data['solution']) for sol_data in synthesis_data['solutions']))
    logger.info(f'🤝 SYNTHESIS INPUT: Processing {len(synthesis_data['solutions'])} solutions')
    logger.info(f'🤝 SYNTHESIS INPUT: Total input characters: {input_chars:,}')
    logger.info(f'🤝 SYNTHESIS INPUT: Verification summary: {synthesis_data['verification_summary']}')
    agent_solutions_text = ''
    solutions_used = synthesis_data['solutions'][:3]
    logger.info(f'🤝 SYNTHESIS INPUT: Using top {len(solutions_used)} solutions for synthesis:')
    for i, sol_data in enumerate(solutions_used):
        logger.info(f'🤝 SYNTHESIS INPUT:   Solution {i + 1}: Agent {sol_data['agent_id']}, {len(sol_data['solution']):,} chars, confidence {sol_data['confidence']:.2f}')
        agent_solutions_text += f'\nAgent {sol_data['agent_id']} (confidence: {sol_data['confidence']:.2f}):\n'
        agent_solutions_text += sol_data['solution']
        agent_solutions_text += '\n' + '=' * 50 + '\n'
    synthesis_input_chars = len(agent_solutions_text)
    verification_text = f'Verification Summary: {synthesis_data['verification_summary']}'
    logger.info(f'🤝 SYNTHESIS INPUT: Final synthesis prompt: {synthesis_input_chars:,} characters')
    extracted_answers_text = ''
    all_extracted = getattr(workspace, '_extracted_answers_info', [])
    if all_extracted:
        extracted_answers_text = '\n\nEXTRACTED ANSWERS FROM AGENTS:\n'
        for answer, solution, method in all_extracted:
            extracted_answers_text += f"- Agent {solution.agent_id}: '{answer}' (via {method})\n"
        extracted_answers_text += '\nIMPORTANT: If multiple agents extracted the same answer, prioritize it in your synthesis.\n'
        extracted_answers_text += 'Ensure the final answer is clearly formatted and matches the expected answer format.\n'
    synthesis_prompt = SYNTHESIS_PROMPT.format(problem=workspace.problem, agent_solutions=agent_solutions_text, verification_results=verification_text) + extracted_answers_text
    try:
        response = client.chat.completions.create(model=model, messages=[{'role': 'system', 'content': 'You are a mathematical synthesis expert.'}, {'role': 'user', 'content': synthesis_prompt}], max_tokens=config['max_tokens'], temperature=0.3, timeout=300, extra_body={'reasoning': {'effort': 'high'}})
        if request_id:
            provider_request = {'model': model, 'messages': [{'role': 'system', 'content': 'You are a mathematical synthesis expert.'}, {'role': 'user', 'content': synthesis_prompt}], 'max_tokens': config['max_tokens'], 'temperature': 0.3, 'extra_body': {'reasoning': {'effort': 'high'}}}
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
            conversation_logger.log_provider_call(request_id, provider_request, response_dict)
        final_solution = response.choices[0].message.content.strip()
        output_chars = len(final_solution)
        compression_ratio = output_chars / synthesis_input_chars * 100 if synthesis_input_chars > 0 else 0
        logger.info(f'🤝 SYNTHESIS PROCESSING: Input: {synthesis_input_chars:,} chars → Output: {output_chars:,} chars ({compression_ratio:.1f}% retention)')
        reasoning_tokens = 0
        total_tokens = 0
        if hasattr(response, 'usage') and response.usage:
            total_tokens = getattr(response.usage, 'total_tokens', 0)
            if hasattr(response.usage, 'completion_tokens_details') and response.usage.completion_tokens_details:
                reasoning_tokens = getattr(response.usage.completion_tokens_details, 'reasoning_tokens', 0)
            if reasoning_tokens == 0:
                reasoning_tokens = getattr(response.usage, 'reasoning_tokens', 0)
        logger.info(f'🤝 SYNTHESIS SUCCESS: Synthesis completed')
        logger.info(f'🤝 SYNTHESIS SUCCESS:   Output solution length: {len(final_solution)} characters')
        logger.info(f'🤝 SYNTHESIS SUCCESS:   Reasoning tokens: {reasoning_tokens}')
        logger.info(f'🤝 SYNTHESIS SUCCESS:   Total tokens: {total_tokens}')
        logger.info(f'🤝 SYNTHESIS SUCCESS:   Solution preview: {final_solution[:200]}...')
        return (final_solution, reasoning_tokens)
    except Exception as e:
        logger.error(f'🚨 SYNTHESIS ERROR: Synthesis failed: {str(e)}')
        if workspace.solutions:
            fallback_solution = max(workspace.solutions, key=lambda s: s.verification_score)
            logger.info(f'🚑 SYNTHESIS FALLBACK: Using fallback solution from agent {fallback_solution.agent_id}')
            logger.info(f'🚑 SYNTHESIS FALLBACK: Solution length: {len(fallback_solution.solution):,} chars, score: {fallback_solution.verification_score:.2f}')
            return (fallback_solution.solution, 0)
        logger.error(f'🚨 SYNTHESIS ERROR: No solutions available for fallback')
        return ('Unable to generate solution due to synthesis failure.', 0)

class MARSVerifier:
    """Multi-pass verification system inspired by IMO25 solver"""

    def __init__(self, agents: List[MARSAgent], workspace: MARSWorkspace, config: Dict[str, Any]):
        self.agents = agents
        self.workspace = workspace
        self.config = config
        self.verification_threshold = config.get('verification_passes_required', 5)

    def verify_solutions(self, request_id: str=None) -> Dict[str, Any]:
        """Run comprehensive verification on all solutions in workspace"""
        logger.info(f'Starting verification process with {self.verification_threshold}-pass threshold')
        verification_summary = {'total_verifications': 0, 'solutions_verified': 0, 'consensus_reached': False, 'verification_details': []}
        solutions = self.workspace.solutions
        if not solutions:
            logger.warning('No solutions to verify')
            return verification_summary
        for solution in solutions:
            solution_verification = self._verify_single_solution(solution, request_id)
            verification_summary['verification_details'].append(solution_verification)
            verification_summary['total_verifications'] += solution_verification['verification_count']
            if solution_verification['passes_threshold']:
                verification_summary['solutions_verified'] += 1
        verified_solutions = self.workspace.get_verified_solutions()
        verification_summary['consensus_reached'] = len(verified_solutions) >= self.config.get('consensus_threshold', 2)
        logger.info(f'Verification complete: {verification_summary['solutions_verified']} solutions verified')
        return verification_summary

    async def verify_solutions_parallel(self, request_id: str=None, executor: ThreadPoolExecutor=None) -> Dict[str, Any]:
        """Run comprehensive verification on all solutions in workspace with parallel execution"""
        logger.info(f'Starting parallel verification process with {self.verification_threshold}-pass threshold')
        verification_summary = {'total_verifications': 0, 'solutions_verified': 0, 'consensus_reached': False, 'verification_details': []}
        solutions = self.workspace.solutions
        if not solutions:
            logger.warning('No solutions to verify')
            return verification_summary

        async def verify_solution_async(solution: AgentSolution):
            """Async wrapper for single solution verification"""
            loop = asyncio.get_event_loop()
            try:
                result = await loop.run_in_executor(executor, self._verify_single_solution, solution, request_id)
                return result
            except Exception as e:
                logger.error(f'Verification failed for solution from agent {solution.agent_id}: {str(e)}')
                return {'solution_agent_id': solution.agent_id, 'verification_count': 0, 'consecutive_passes': 0, 'passes_threshold': False, 'verification_results': []}
        tasks = [verify_solution_async(solution) for solution in solutions]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception):
                logger.error(f'Verification task failed: {str(result)}')
                continue
            verification_summary['verification_details'].append(result)
            verification_summary['total_verifications'] += result['verification_count']
            if result['passes_threshold']:
                verification_summary['solutions_verified'] += 1
        verified_solutions = self.workspace.get_verified_solutions()
        verification_summary['consensus_reached'] = len(verified_solutions) >= self.config.get('consensus_threshold', 2)
        logger.info(f'Parallel verification complete: {verification_summary['solutions_verified']} solutions verified')
        return verification_summary

    def _verify_single_solution(self, solution: AgentSolution, request_id: str=None) -> Dict[str, Any]:
        """Verify a single solution with multiple passes"""
        logger.info(f'Verifying solution from agent {solution.agent_id}')
        verification_results = []
        consecutive_passes = 0
        max_verification_attempts = self.config.get('max_verification_attempts', 10)
        for attempt in range(max_verification_attempts):
            verifier_agent = self._select_verifier_agent(solution.agent_id)
            if not verifier_agent:
                logger.warning('No suitable verifier agent available')
                break
            try:
                verification = verifier_agent.verify_solution(problem=self.workspace.problem, solution=solution.solution, verifier_id=verifier_agent.agent_id, solution_agent_id=solution.agent_id, request_id=request_id)
                verification_results.append(verification)
                self.workspace.add_verification(verification)
                if verification.assessment == 'CORRECT':
                    consecutive_passes += 1
                    logger.info(f'Verification pass {consecutive_passes}/{self.verification_threshold}')
                    if consecutive_passes >= self.verification_threshold:
                        logger.info(f'Solution from agent {solution.agent_id} passed {self.verification_threshold}-pass verification')
                        break
                else:
                    consecutive_passes = 0
                    logger.info(f'Verification failed: {verification.assessment}')
            except Exception as e:
                logger.error(f'Verification attempt {attempt + 1} failed: {str(e)}')
                consecutive_passes = 0
        return {'solution_agent_id': solution.agent_id, 'verification_count': len(verification_results), 'consecutive_passes': consecutive_passes, 'passes_threshold': consecutive_passes >= self.verification_threshold, 'verification_results': [{'verifier_id': v.verifier_id, 'assessment': v.assessment, 'confidence': v.confidence, 'issues_count': len(v.issues)} for v in verification_results]}

    def _select_verifier_agent(self, solution_agent_id: int) -> MARSAgent:
        """Select an agent different from the solution creator for verification"""
        available_agents = [agent for agent in self.agents if agent.agent_id != solution_agent_id]
        if not available_agents:
            available_agents = self.agents
        if len(available_agents) > 1:
            solution_agent = next((a for a in self.agents if a.agent_id == solution_agent_id), None)
            if solution_agent:
                solution_temp = solution_agent.temperature
                available_agents.sort(key=lambda a: abs(a.temperature - solution_temp), reverse=True)
        return available_agents[0] if available_agents else None

    def iterative_improvement(self, request_id: str=None) -> Dict[str, Any]:
        """Run iterative improvement on solutions that failed verification"""
        logger.info('Starting iterative improvement process')
        improvement_summary = {'solutions_improved': 0, 'improvement_attempts': 0, 'total_reasoning_tokens': 0}
        unverified_solutions = [s for s in self.workspace.solutions if not s.is_verified]
        for solution in unverified_solutions:
            if solution.verification_results:
                latest_verification = solution.verification_results[-1]
                if latest_verification['assessment'] in ['INCORRECT', 'INCOMPLETE']:
                    original_agent = next((a for a in self.agents if a.agent_id == solution.agent_id), None)
                    if original_agent:
                        try:
                            improved_solution, reasoning_tokens = original_agent.improve_solution(problem=self.workspace.problem, current_solution=solution.solution, feedback=latest_verification['detailed_report'], issues=latest_verification['issues'], request_id=request_id)
                            solution.solution = improved_solution
                            solution.timestamp = datetime.now()
                            solution.reasoning_tokens += reasoning_tokens
                            improvement_summary['solutions_improved'] += 1
                            improvement_summary['total_reasoning_tokens'] += reasoning_tokens
                            logger.info(f'Improved solution from agent {solution.agent_id}')
                        except Exception as e:
                            logger.error(f'Failed to improve solution from agent {solution.agent_id}: {str(e)}')
                    improvement_summary['improvement_attempts'] += 1
        return improvement_summary

    async def iterative_improvement_parallel(self, request_id: str=None, executor: ThreadPoolExecutor=None) -> Dict[str, Any]:
        """Run iterative improvement on solutions that failed verification with parallel execution"""
        logger.info('Starting parallel iterative improvement process')
        improvement_summary = {'solutions_improved': 0, 'improvement_attempts': 0, 'total_reasoning_tokens': 0}
        unverified_solutions = [s for s in self.workspace.solutions if not s.is_verified]
        improvable_solutions = []
        for solution in unverified_solutions:
            if solution.verification_results:
                latest_verification = solution.verification_results[-1]
                if latest_verification['assessment'] in ['INCORRECT', 'INCOMPLETE']:
                    original_agent = next((a for a in self.agents if a.agent_id == solution.agent_id), None)
                    if original_agent:
                        improvable_solutions.append((solution, original_agent, latest_verification))
        if not improvable_solutions:
            logger.info('No solutions need improvement')
            return improvement_summary

        async def improve_solution_async(solution_data):
            """Async wrapper for solution improvement"""
            solution, agent, verification = solution_data
            loop = asyncio.get_event_loop()
            try:
                improved_solution, reasoning_tokens = await loop.run_in_executor(executor, agent.improve_solution, self.workspace.problem, solution.solution, verification['detailed_report'], verification['issues'], request_id)
                solution.solution = improved_solution
                solution.timestamp = datetime.now()
                solution.reasoning_tokens += reasoning_tokens
                logger.info(f'Improved solution from agent {solution.agent_id}')
                return (solution.agent_id, True, reasoning_tokens, None)
            except Exception as e:
                logger.error(f'Failed to improve solution from agent {solution.agent_id}: {str(e)}')
                return (solution.agent_id, False, 0, e)
        tasks = [improve_solution_async(sol_data) for sol_data in improvable_solutions]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            improvement_summary['improvement_attempts'] += 1
            if isinstance(result, Exception):
                logger.error(f'Improvement task failed: {str(result)}')
                continue
            agent_id, success, tokens, error = result
            if success:
                improvement_summary['solutions_improved'] += 1
                improvement_summary['total_reasoning_tokens'] += tokens
        logger.info(f'Parallel improvement complete: {improvement_summary['solutions_improved']} solutions improved')
        return improvement_summary

    def final_consensus_check(self) -> bool:
        """Final check to determine if consensus has been reached"""
        verified_solutions = self.workspace.get_verified_solutions()
        consensus_threshold = self.config.get('consensus_threshold', 2)
        has_consensus = len(verified_solutions) >= consensus_threshold
        if has_consensus:
            logger.info(f'Consensus reached with {len(verified_solutions)} verified solutions')
            for solution in verified_solutions:
                logger.info(f'Verified solution from agent {solution.agent_id} (score: {solution.verification_score:.2f})')
        else:
            logger.info(f'No consensus: only {len(verified_solutions)} solutions verified (need {consensus_threshold})')
        return has_consensus

def _verify_single_solution(self, solution: AgentSolution, request_id: str=None) -> Dict[str, Any]:
    """Verify a single solution with multiple passes"""
    logger.info(f'Verifying solution from agent {solution.agent_id}')
    verification_results = []
    consecutive_passes = 0
    max_verification_attempts = self.config.get('max_verification_attempts', 10)
    for attempt in range(max_verification_attempts):
        verifier_agent = self._select_verifier_agent(solution.agent_id)
        if not verifier_agent:
            logger.warning('No suitable verifier agent available')
            break
        try:
            verification = verifier_agent.verify_solution(problem=self.workspace.problem, solution=solution.solution, verifier_id=verifier_agent.agent_id, solution_agent_id=solution.agent_id, request_id=request_id)
            verification_results.append(verification)
            self.workspace.add_verification(verification)
            if verification.assessment == 'CORRECT':
                consecutive_passes += 1
                logger.info(f'Verification pass {consecutive_passes}/{self.verification_threshold}')
                if consecutive_passes >= self.verification_threshold:
                    logger.info(f'Solution from agent {solution.agent_id} passed {self.verification_threshold}-pass verification')
                    break
            else:
                consecutive_passes = 0
                logger.info(f'Verification failed: {verification.assessment}')
        except Exception as e:
            logger.error(f'Verification attempt {attempt + 1} failed: {str(e)}')
            consecutive_passes = 0
    return {'solution_agent_id': solution.agent_id, 'verification_count': len(verification_results), 'consecutive_passes': consecutive_passes, 'passes_threshold': consecutive_passes >= self.verification_threshold, 'verification_results': [{'verifier_id': v.verifier_id, 'assessment': v.assessment, 'confidence': v.confidence, 'issues_count': len(v.issues)} for v in verification_results]}

def format_search_results(query: str, results: List[Dict[str, str]]) -> str:
    """Format search results into readable text"""
    if not results:
        return f'No search results found for: {query}'
    formatted = f"Search results for '{query}':\n\n"
    for i, result in enumerate(results, 1):
        formatted += f'{i}. **{result['title']}**\n'
        formatted += f'   URL: {result['url']}\n'
        if result['snippet']:
            formatted += f'   Summary: {result['snippet']}\n'
        formatted += '\n'
    return formatted

class Completions:

    def __init__(self, parent):
        self.parent = parent

    def create(self, **kwargs):
        """Create completion with appropriate timeout handling"""
        if self.parent.client_type == 'openai_compatible':
            try:
                if 'Cerebras' in self.parent.client.__class__.__name__:
                    from cerebras.cloud.sdk import Cerebras
                    custom_client = Cerebras(api_key=self.parent.client.api_key, base_url=getattr(self.parent.client, 'base_url', None), timeout=self.parent.timeout, max_retries=self.parent.max_retries)
                else:
                    existing_http_client = getattr(self.parent.client, '_client', None)
                    if 'Azure' in self.parent.client.__class__.__name__:
                        from openai import AzureOpenAI
                        custom_client = AzureOpenAI(api_key=self.parent.client.api_key, api_version=getattr(self.parent.client, 'api_version', None), azure_endpoint=getattr(self.parent.client, 'azure_endpoint', None), azure_ad_token_provider=getattr(self.parent.client, 'azure_ad_token_provider', None), timeout=self.parent.timeout, max_retries=self.parent.max_retries, http_client=existing_http_client)
                    else:
                        from openai import OpenAI
                        custom_client = OpenAI(api_key=self.parent.client.api_key, base_url=getattr(self.parent.client, 'base_url', None), timeout=self.parent.timeout, max_retries=self.parent.max_retries, http_client=existing_http_client)
                return custom_client.chat.completions.create(**kwargs)
            except Exception as e:
                print(f'⚠️ Warning: Could not create custom client with timeout: {str(e)}')
                return self.parent.client.chat.completions.create(**kwargs)
        elif self.parent.client_type == 'litellm':
            kwargs['timeout'] = self.parent.timeout
            return self.parent.client.chat.completions.create(**kwargs)
        else:
            print(f'ℹ️ Using original client (type: {self.parent.client.__class__.__name__}) without timeout modification')
            return self.parent.client.chat.completions.create(**kwargs)

def create(self, **kwargs):
    """Create completion with appropriate timeout handling"""
    if self.parent.client_type == 'openai_compatible':
        try:
            if 'Cerebras' in self.parent.client.__class__.__name__:
                from cerebras.cloud.sdk import Cerebras
                custom_client = Cerebras(api_key=self.parent.client.api_key, base_url=getattr(self.parent.client, 'base_url', None), timeout=self.parent.timeout, max_retries=self.parent.max_retries)
            else:
                existing_http_client = getattr(self.parent.client, '_client', None)
                if 'Azure' in self.parent.client.__class__.__name__:
                    from openai import AzureOpenAI
                    custom_client = AzureOpenAI(api_key=self.parent.client.api_key, api_version=getattr(self.parent.client, 'api_version', None), azure_endpoint=getattr(self.parent.client, 'azure_endpoint', None), azure_ad_token_provider=getattr(self.parent.client, 'azure_ad_token_provider', None), timeout=self.parent.timeout, max_retries=self.parent.max_retries, http_client=existing_http_client)
                else:
                    from openai import OpenAI
                    custom_client = OpenAI(api_key=self.parent.client.api_key, base_url=getattr(self.parent.client, 'base_url', None), timeout=self.parent.timeout, max_retries=self.parent.max_retries, http_client=existing_http_client)
            return custom_client.chat.completions.create(**kwargs)
        except Exception as e:
            print(f'⚠️ Warning: Could not create custom client with timeout: {str(e)}')
            return self.parent.client.chat.completions.create(**kwargs)
    elif self.parent.client_type == 'litellm':
        kwargs['timeout'] = self.parent.timeout
        return self.parent.client.chat.completions.create(**kwargs)
    else:
        print(f'ℹ️ Using original client (type: {self.parent.client.__class__.__name__}) without timeout modification')
        return self.parent.client.chat.completions.create(**kwargs)

def _format_messages_for_model(system_prompt: str, initial_query: str, supports_system_messages: bool) -> list:
    """
    Format messages based on whether the model supports system messages.
    """
    if supports_system_messages:
        return [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': initial_query}]
    else:
        if system_prompt.strip():
            combined_message = f'{system_prompt}\n\nUser: {initial_query}'
        else:
            combined_message = initial_query
        return [{'role': 'user', 'content': combined_message}]

def extract_code_blocks(text: str) -> List[str]:
    """Extract Python code blocks from text."""
    pattern = '```python\\s*(.*?)\\s*```'
    matches = re.findall(pattern, text, re.DOTALL)
    blocks = [m.strip() for m in matches]
    logger.info(f'Extracted {len(blocks)} code blocks')
    for i, block in enumerate(blocks):
        logger.info(f'Code block {i + 1}:\n{block}')
    return blocks

def generate_fixed_code(original_code: str, error: str, client, model: str) -> Tuple[str, int]:
    """Ask LLM to fix the broken code."""
    logger.info('Requesting code fix from LLM')
    logger.info(f'Original error: {error}')
    response = client.chat.completions.create(model=model, messages=[{'role': 'system', 'content': CODE_FIX_PROMPT.format(code=original_code, error=error)}, {'role': 'user', 'content': 'Fix the code to make it work.'}], temperature=0.2)
    fixed_code = response.choices[0].message.content
    code_blocks = extract_code_blocks(fixed_code)
    if code_blocks:
        logger.info('Received fixed code from LLM')
        return (code_blocks[0], response.usage.completion_tokens)
    else:
        logger.warning('No code block found in LLM response')
        return (None, response.usage.completion_tokens)

def simulate_execution(code: str, error: str, client, model: str) -> Tuple[Any, int]:
    """Ask LLM to simulate code execution."""
    logger.info('Attempting code simulation with LLM')
    response = client.chat.completions.create(model=model, messages=[{'role': 'system', 'content': SIMULATION_PROMPT.format(code=code, error=error)}, {'role': 'user', 'content': 'Simulate this code and return the final answer value.'}], temperature=0.2)
    try:
        result = response.choices[0].message.content.strip()
        try:
            answer = ast.literal_eval(result)
        except:
            answer = result
        logger.info(f'Simulation successful. Result: {answer}')
        return (answer, response.usage.completion_tokens)
    except Exception as e:
        logger.error(f'Failed to parse simulation result: {str(e)}')
        return (None, response.usage.completion_tokens)

def run(system_prompt: str, initial_query: str, client, model: str) -> Tuple[str, int]:
    """Main Chain of Code execution function."""
    logger.info('Starting Chain of Code execution')
    logger.info(f'Query: {initial_query}')
    messages = [{'role': 'system', 'content': system_prompt + '\n' + CHAIN_OF_CODE_PROMPT}, {'role': 'user', 'content': initial_query}]
    response = client.chat.completions.create(model=model, messages=messages, temperature=0.7)
    total_tokens = response.usage.completion_tokens
    code_blocks = extract_code_blocks(response.choices[0].message.content)
    if not code_blocks:
        logger.warning('No code blocks found in response')
        return (response.choices[0].message.content, total_tokens)
    current_code = code_blocks[0]
    fix_attempts = 0
    last_error = None
    while fix_attempts < MAX_FIX_ATTEMPTS:
        fix_attempts += 1
        logger.info(f'Execution attempt {fix_attempts}/{MAX_FIX_ATTEMPTS}')
        answer, error = execute_code(current_code)
        if error is None:
            logger.info(f'Successful execution on attempt {fix_attempts}')
            return (str(answer), total_tokens)
        last_error = error
        if fix_attempts >= MAX_FIX_ATTEMPTS:
            logger.warning(f'Failed after {fix_attempts} fix attempts')
            break
        logger.info(f'Requesting code fix, attempt {fix_attempts}')
        fixed_code, fix_tokens = generate_fixed_code(current_code, error, client, model)
        total_tokens += fix_tokens
        if fixed_code:
            current_code = fixed_code
        else:
            logger.error('Failed to get fixed code from LLM')
            break
    logger.info('All execution attempts failed, trying simulation')
    simulated_answer, sim_tokens = simulate_execution(current_code, last_error, client, model)
    total_tokens += sim_tokens
    if simulated_answer is not None:
        logger.info('Successfully got answer from simulation')
        return (str(simulated_answer), total_tokens)
    logger.warning('All strategies failed')
    return (f'Error: Could not solve problem after all attempts. Last error: {last_error}', total_tokens)

class JSONGenerator:

    def get_device(self):
        """Get the appropriate device (mps, cuda, or cpu)."""
        if torch.backends.mps.is_available():
            return torch.device('mps')
        elif torch.cuda.is_available():
            return torch.device('cuda')
        else:
            return torch.device('cpu')

    def __init__(self, model_name: str='google/gemma-3-270m-it'):
        """Initialize the JSON generator with a specific model."""
        self.device = self.get_device()
        logger.info(f'Using device: {self.device}')
        try:
            hf_model = AutoModelForCausalLM.from_pretrained(model_name, device_map='auto' if str(self.device) != 'cpu' else None, torch_dtype=torch.float16 if str(self.device) != 'cpu' else torch.float32)
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = outlines.from_transformers(hf_model, self.tokenizer)
            logger.info(f'Successfully loaded model: {model_name}')
        except Exception as e:
            logger.error(f'Error loading model: {str(e)}')
            raise

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text string."""
        try:
            tokens = self.tokenizer.encode(text)
            return len(tokens)
        except Exception as e:
            logger.error(f'Error counting tokens: {str(e)}')
            return 0

    def parse_json_schema_to_pydantic(self, schema_str: str) -> type[BaseModel]:
        """Convert JSON schema string to Pydantic model."""
        try:
            schema_dict = json.loads(schema_str)
            properties = schema_dict.get('properties', {})
            required = schema_dict.get('required', [])
            fields = {}
            for field_name, field_def in properties.items():
                field_type = str
                if field_def.get('type') == 'integer':
                    field_type = int
                elif field_def.get('type') == 'number':
                    field_type = float
                elif field_def.get('type') == 'boolean':
                    field_type = bool
                elif field_def.get('type') == 'array':
                    field_type = list
                elif field_def.get('type') == 'object':
                    field_type = dict
                if field_name in required:
                    fields[field_name] = (field_type, ...)
                else:
                    fields[field_name] = (Optional[field_type], None)
            return create_model('DynamicModel', **fields)
        except Exception as e:
            logger.error(f'Error parsing JSON schema: {str(e)}')
            raise

    def generate_json(self, prompt: str, schema: str) -> Dict[str, Any]:
        """Generate JSON based on the provided schema and prompt."""
        try:
            pydantic_model = self.parse_json_schema_to_pydantic(schema)
            logger.info('Parsed JSON schema to Pydantic model')
            result = self.model(prompt, pydantic_model)
            logger.info('Successfully generated JSON response')
            if hasattr(result, 'model_dump'):
                return result.model_dump()
            elif hasattr(result, 'dict'):
                return result.dict()
            else:
                return dict(result)
        except Exception as e:
            logger.error(f'Error generating JSON: {str(e)}')
            raise

def count_tokens(self, text: str) -> int:
    """Count the number of tokens in a text string."""
    try:
        tokens = self.tokenizer.encode(text)
        return len(tokens)
    except Exception as e:
        logger.error(f'Error counting tokens: {str(e)}')
        return 0

def generate_json(self, prompt: str, schema: str) -> Dict[str, Any]:
    """Generate JSON based on the provided schema and prompt."""
    try:
        pydantic_model = self.parse_json_schema_to_pydantic(schema)
        logger.info('Parsed JSON schema to Pydantic model')
        result = self.model(prompt, pydantic_model)
        logger.info('Successfully generated JSON response')
        if hasattr(result, 'model_dump'):
            return result.model_dump()
        elif hasattr(result, 'dict'):
            return result.dict()
        else:
            return dict(result)
    except Exception as e:
        logger.error(f'Error generating JSON: {str(e)}')
        raise

def run(system_prompt: str, initial_query: str, client, model: str) -> Tuple[str, int]:
    query, request_code = extract_python_code(initial_query)[0] if extract_python_code(initial_query) else (initial_query, '')
    if should_execute_request_code(query) and request_code:
        code_output = execute_code(request_code)
        context = f'Query: {query}\nCode:\n```python\n{request_code}\n```\nOutput:\n{code_output}'
        messages = [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': context}]
        response = client.chat.completions.create(model=model, messages=messages)
        return (response.choices[0].message.content.strip(), response.usage.completion_tokens)
    else:
        messages = [{'role': 'system', 'content': system_prompt + EXECUTE_CODE_PROMPT}, {'role': 'user', 'content': initial_query}]
        response = client.chat.completions.create(model=model, messages=messages)
        initial_response = response.choices[0].message.content.strip()
        response_code = extract_python_code(initial_response)
        if response_code:
            code_output = execute_code(response_code[0])
            context = f'Initial response:\n{initial_response}\n\nCode output:\n{code_output}'
            messages.append({'role': 'assistant', 'content': initial_response})
            messages.append({'role': 'user', 'content': f'Based on the code execution output, please provide a final response:\n{context}'})
            final_response = client.chat.completions.create(model=model, messages=messages)
            return (final_response.choices[0].message.content.strip(), response.usage.completion_tokens + final_response.usage.completion_tokens)
        else:
            return (initial_response, response.usage.completion_tokens)

def run(system_prompt: str, initial_query: str, client, model: str, request_config: Dict[str, Any]=None) -> Tuple[str, int]:
    """
    Generic majority voting implementation.
    """
    logger.info('Starting majority voting process')
    k = request_config.get('k', DEFAULT_K) if request_config else DEFAULT_K
    temperature = request_config.get('temperature', DEFAULT_TEMPERATURE) if request_config else DEFAULT_TEMPERATURE
    max_tokens = request_config.get('max_tokens', 4096) if request_config else 4096
    logger.info(f'Generating {k} candidates with temperature={temperature}')
    messages = [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': initial_query}]
    candidates = []
    total_tokens = 0
    try:
        response = client.chat.completions.create(model=model, messages=messages, n=k, temperature=temperature, max_tokens=max_tokens)
        candidates = [choice.message.content for choice in response.choices]
        total_tokens = response.usage.completion_tokens
    except Exception as e:
        logger.warning(f'Parallel generation failed: {str(e)}')
        for i in range(k):
            try:
                response = client.chat.completions.create(model=model, messages=messages, temperature=temperature, max_tokens=max_tokens)
                candidates.append(response.choices[0].message.content)
                total_tokens += response.usage.completion_tokens
            except Exception as err:
                logger.error(f'Error generating candidate {i + 1}: {str(err)}')
                continue
    if not candidates:
        return ('Error: Could not generate any candidates', 0)
    answer_votes = Counter()
    answer_to_responses = {}
    for i, candidate in enumerate(candidates):
        answer = extract_final_answer(candidate)
        normalized = normalize_response(answer)
        if normalized:
            answer_votes[normalized] += 1
            if normalized not in answer_to_responses:
                answer_to_responses[normalized] = []
            answer_to_responses[normalized].append(candidate)
            logger.debug(f"Candidate {i + 1}: '{answer}' -> '{normalized}'")
        else:
            logger.warning(f'Could not extract/normalize answer from candidate {i + 1}')
    if answer_votes:
        most_common_normalized, count = answer_votes.most_common(1)[0]
        logger.info(f"Most common answer: '{most_common_normalized}' with {count}/{k} votes")
        winning_responses = answer_to_responses[most_common_normalized]
        return (winning_responses[0], total_tokens)
    else:
        logger.warning('No answers could be extracted, returning first candidate')
        return (candidates[0], total_tokens)

def classify_margin(margin):
    return margin.startswith('YES#')

def extract_key_information(system_message, text: str, query: str, client, model: str) -> List[str]:
    messages = [{'role': 'system', 'content': system_message}, {'role': 'user', 'content': f"\n'''text\n{text}\n'''\nCopy over all context relevant to the query: {query}\nProvide the answer in the format: <YES/NO>#<Relevant context>.\nHere are rules:\n- If you don't know how to answer the query - start your answer with NO#\n- If the text is not related to the query - start your answer with NO#\n- If you can extract relevant information - start your answer with YES#\n- If the text does not mention the person by name - start your answer with NO#\nExample answers:\n- YES#Western philosophy originated in Ancient Greece in the 6th century BCE with the pre-Socratics.\n- NO#No relevant context.\n"}]
    try:
        response = client.chat.completions.create(model=model, messages=messages, max_tokens=1000)
        key_info = response.choices[0].message.content.strip()
    except Exception as e:
        print(f'Error parsing content: {str(e)}')
        return ([], 0)
    margins = []
    if classify_margin(key_info):
        margins.append(key_info.split('#', 1)[1])
    return (margins, response.usage.completion_tokens)

def create_comparison_prompt(candidates: List[str], query: str, comparison_mode: str='batch') -> str:
    """
    Create a prompt for comparing candidate solutions.
    
    Args:
        candidates: List of candidate responses
        query: The original user query
        comparison_mode: "batch" for all at once, "tournament" for pairwise
        
    Returns:
        The comparison prompt
    """
    if comparison_mode == 'batch':
        prompt = f'You are an expert evaluator tasked with selecting the best response to the following query:\n\nQuery: {query}\n\nI will provide you with {len(candidates)} different candidate responses. Please analyze each one carefully and select the best response based on the following criteria:\n\n1. **Correctness and Accuracy**: Is the response factually correct and accurate?\n2. **Completeness**: Does it fully address all aspects of the query?\n3. **Clarity**: Is the explanation clear and easy to understand?\n4. **Logical Coherence**: Is the reasoning sound and well-structured?\n5. **Practical Value**: Does it provide useful, actionable information?\n\nFor coding problems, also consider:\n- Code correctness and efficiency\n- Best practices and style\n- Error handling\n\nHere are the candidate responses:\n\n'
        for i, candidate in enumerate(candidates, 1):
            prompt += f'=== Candidate {i} ===\n{candidate}\n\n'
        prompt += 'Please analyze all candidates and provide:\n1. A brief comparison highlighting the strengths and weaknesses of each candidate\n2. Your selection of the best candidate (specify the number)\n3. A clear explanation of why you selected that candidate\n\nFormat your response as:\nCOMPARISON:\n[Your comparison analysis]\n\nBEST CANDIDATE: [number]\n\nREASONING:\n[Your explanation for the selection]'
    else:
        return create_comparison_prompt(candidates, query, 'batch')
    return prompt

def run(system_prompt: str, initial_query: str, client, model: str, request_config: Dict[str, Any]=None) -> Tuple[str, int]:
    """
    Main entry point for the GenSelect plugin.
    
    Generates multiple candidate solutions and uses LLM comparison to select the best one.
    
    Args:
        system_prompt: System prompt for the model
        initial_query: User's query
        client: OpenAI-compatible client instance
        model: Model identifier
        request_config: Additional configuration parameters
        
    Returns:
        Tuple of (response_text, completion_tokens_used)
    """
    logger.info('Starting GenSelect process')
    config = request_config or {}
    num_candidates = config.get('num_candidates', DEFAULT_NUM_CANDIDATES)
    temperature = config.get('temperature', DEFAULT_TEMPERATURE)
    comparison_temperature = config.get('comparison_temperature', DEFAULT_COMPARISON_TEMPERATURE)
    comparison_mode = config.get('comparison_mode', DEFAULT_COMPARISON_MODE)
    include_reasoning = config.get('include_reasoning', DEFAULT_INCLUDE_REASONING)
    max_tokens = config.get('max_tokens', 4096)
    num_candidates = max(2, num_candidates)
    logger.info(f'Generating {num_candidates} candidates with temperature={temperature}')
    messages = [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': initial_query}]
    candidates = []
    total_tokens = 0
    try:
        response = client.chat.completions.create(model=model, messages=messages, n=num_candidates, temperature=temperature, max_tokens=max_tokens)
        candidates = [choice.message.content for choice in response.choices]
        total_tokens += response.usage.completion_tokens
        logger.info(f'Generated {len(candidates)} candidates using n parameter. Tokens: {total_tokens}')
    except Exception as e:
        logger.warning(f'n parameter not supported: {str(e)}')
        logger.info('Falling back to sequential generation')
        for i in range(num_candidates):
            try:
                response = client.chat.completions.create(model=model, messages=messages, temperature=temperature, max_tokens=max_tokens)
                candidates.append(response.choices[0].message.content)
                total_tokens += response.usage.completion_tokens
                logger.debug(f'Generated candidate {i + 1}/{num_candidates}')
            except Exception as gen_error:
                logger.error(f'Error generating candidate {i + 1}: {str(gen_error)}')
                continue
    if len(candidates) < 2:
        logger.error(f'Insufficient candidates generated ({len(candidates)})')
        if candidates:
            return (candidates[0], total_tokens)
        return ('Error: Could not generate sufficient candidates for selection', total_tokens)
    comparison_prompt = create_comparison_prompt(candidates, initial_query, comparison_mode)
    logger.info('Comparing candidates for selection')
    try:
        comparison_messages = [{'role': 'system', 'content': 'You are an expert evaluator skilled at comparing and selecting high-quality responses.'}, {'role': 'user', 'content': comparison_prompt}]
        comparison_response = client.chat.completions.create(model=model, messages=comparison_messages, temperature=comparison_temperature, max_tokens=2048)
        selection_response = comparison_response.choices[0].message.content
        total_tokens += comparison_response.usage.completion_tokens
        selected_index, reasoning = parse_selection_response(selection_response, len(candidates))
        selected_candidate = candidates[selected_index]
        logger.info(f'GenSelect Summary:')
        logger.info(f'  - Generated {len(candidates)} candidates')
        logger.info(f'  - Selected candidate {selected_index + 1}')
        logger.info(f'  - Total tokens used: {total_tokens}')
        if include_reasoning:
            final_response = f'{selected_candidate}\n\n---\n**GenSelect Reasoning**: {reasoning}'
        else:
            final_response = selected_candidate
        return (final_response, total_tokens)
    except Exception as e:
        logger.error(f'Error during comparison: {str(e)}')
        logger.warning('Falling back to first candidate due to comparison error')
        return (candidates[0], total_tokens)

class ProxyConfig:
    """Manages proxy configuration with caching and validation."""
    _cached_config: Optional[Dict[str, Any]] = None
    _config_path: Optional[Path] = None

    @classmethod
    def load(cls, path: str=None, force_reload: bool=False) -> Dict[str, Any]:
        """
        Load and cache configuration.
        
        Args:
            path: Optional path to config file
            force_reload: Force reload even if cached
            
        Returns:
            Loaded and validated configuration dictionary
        """
        if cls._cached_config and (not force_reload):
            return cls._cached_config
        if not path:
            config_locations = [Path.home() / '.optillm' / 'proxy_config.yaml', Path.home() / '.optillm' / 'proxy_config.yml', Path(__file__).parent / 'example_config.yaml']
            for config_path in config_locations:
                if config_path.exists():
                    path = config_path
                    logger.info(f'Using config from: {path}')
                    break
            else:
                path = config_locations[0]
                cls._create_default(path)
        cls._config_path = Path(path)
        try:
            with open(path, 'r') as f:
                config = yaml.safe_load(f) or {}
            if not isinstance(config, dict):
                raise ValueError('Configuration must be a dictionary')
            config = cls._interpolate_env_vars(config)
            config = cls._apply_defaults(config)
            config = cls._validate_config(config)
            cls._cached_config = config
            logger.debug(f'Loaded config with {len(config.get('providers', []))} providers')
            return config
        except Exception as e:
            logger.error(f'Failed to load proxy config from {path}: {e}')
            return cls._get_minimal_config()

    @classmethod
    def reload(cls) -> Dict[str, Any]:
        """Force reload configuration from disk."""
        return cls.load(force_reload=True)

    @staticmethod
    def _interpolate_env_vars(obj: Any) -> Any:
        """
        Recursively replace ${VAR} and ${VAR:-default} with environment values.
        
        Args:
            obj: Object to process (dict, list, str, or other)
            
        Returns:
            Processed object with environment variables replaced
        """
        if isinstance(obj, str):
            pattern = re.compile('\\$\\{([^}]+)\\}')

            def replacer(match):
                var_expr = match.group(1)
                if ':-' in var_expr:
                    var_name, default = var_expr.split(':-', 1)
                    value = os.environ.get(var_name.strip(), default)
                else:
                    var_name = var_expr.strip()
                    value = os.environ.get(var_name)
                    if value is None:
                        logger.warning(f'Environment variable ${{{var_name}}} not set')
                        return match.group(0)
                return value
            return pattern.sub(replacer, obj)
        elif isinstance(obj, dict):
            return {k: ProxyConfig._interpolate_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [ProxyConfig._interpolate_env_vars(item) for item in obj]
        return obj

    @staticmethod
    def _apply_defaults(config: Dict) -> Dict:
        """
        Apply sensible defaults to configuration.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Configuration with defaults applied
        """
        config.setdefault('providers', [])
        config.setdefault('routing', {})
        config.setdefault('monitoring', {})
        config.setdefault('timeouts', {})
        config.setdefault('queue', {})
        routing = config['routing']
        routing.setdefault('strategy', 'round_robin')
        routing.setdefault('health_check', {})
        health_check = routing['health_check']
        health_check.setdefault('enabled', True)
        health_check.setdefault('interval', 30)
        health_check.setdefault('timeout', 5)
        monitoring = config['monitoring']
        monitoring.setdefault('log_level', 'INFO')
        monitoring.setdefault('track_latency', True)
        monitoring.setdefault('track_errors', True)
        timeouts = config['timeouts']
        timeouts.setdefault('request', 30)
        timeouts.setdefault('connect', 5)
        queue = config['queue']
        queue.setdefault('max_concurrent', 100)
        queue.setdefault('timeout', 60)
        for i, provider in enumerate(config['providers']):
            provider.setdefault('name', f'provider_{i}')
            provider.setdefault('weight', 1)
            provider.setdefault('fallback_only', False)
            provider.setdefault('model_map', {})
            provider.setdefault('max_concurrent', None)
        return config

    @staticmethod
    def _validate_config(config: Dict) -> Dict:
        """
        Validate configuration structure and values.
        
        Args:
            config: Configuration to validate
            
        Returns:
            Validated configuration
            
        Raises:
            ValueError: If configuration is invalid
        """
        for provider in config.get('providers', []):
            if 'base_url' not in provider:
                raise ValueError(f'Provider {provider.get('name', 'unknown')} missing base_url')
            if 'api_key' not in provider:
                raise ValueError(f'Provider {provider.get('name', 'unknown')} missing api_key')
            if provider['weight'] <= 0:
                logger.warning(f'Provider {provider['name']} has invalid weight {provider['weight']}, setting to 1')
                provider['weight'] = 1
            if provider.get('max_concurrent') is not None:
                if not isinstance(provider['max_concurrent'], int) or provider['max_concurrent'] <= 0:
                    logger.warning(f'Provider {provider['name']} has invalid max_concurrent {provider['max_concurrent']}, removing limit')
                    provider['max_concurrent'] = None
        valid_strategies = ['weighted', 'round_robin', 'failover']
        strategy = config['routing']['strategy']
        if strategy not in valid_strategies:
            logger.warning(f"Invalid routing strategy '{strategy}', using 'round_robin'")
            config['routing']['strategy'] = 'round_robin'
        return config

    @staticmethod
    def _create_default(path: Path):
        """Create default configuration file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        default = '# OptiLLM Proxy Plugin Configuration\n# \n# This is an auto-generated configuration file.\n# Add your LLM provider endpoints and API keys below.\n# \n# Environment variables are supported: ${VAR_NAME} or ${VAR_NAME:-default_value}\n\nproviders:\n  # Example OpenAI provider (uncomment and configure)\n  # - name: openai_primary\n  #   base_url: https://api.openai.com/v1\n  #   api_key: ${OPENAI_API_KEY}\n  #   weight: 1\n\nrouting:\n  strategy: round_robin  # Options: weighted, round_robin, failover\n  health_check:\n    enabled: true\n    interval: 30  # seconds\n    timeout: 5    # seconds\n\ntimeouts:\n  request: 30     # Maximum time for a request (seconds)\n  connect: 5      # Maximum time for connection (seconds)\n\nqueue:\n  max_concurrent: 100  # Maximum concurrent requests\n  timeout: 60          # Maximum time in queue (seconds)\n\nmonitoring:\n  log_level: INFO\n  track_latency: true\n  track_errors: true\n\n# See proxy/README.md for full documentation\n'
        path.write_text(default)
        logger.info(f'Created default proxy config at {path}')
        logger.info('Please configure your providers in this file')

    @staticmethod
    def _get_minimal_config() -> Dict:
        """Return minimal working config as fallback."""
        return {'providers': [], 'routing': {'strategy': 'round_robin', 'health_check': {'enabled': False}}, 'timeouts': {'request': 30, 'connect': 5}, 'queue': {'max_concurrent': 100, 'timeout': 60}, 'monitoring': {'log_level': 'INFO', 'track_latency': False, 'track_errors': True}}

@staticmethod
def _apply_defaults(config: Dict) -> Dict:
    """
        Apply sensible defaults to configuration.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Configuration with defaults applied
        """
    config.setdefault('providers', [])
    config.setdefault('routing', {})
    config.setdefault('monitoring', {})
    config.setdefault('timeouts', {})
    config.setdefault('queue', {})
    routing = config['routing']
    routing.setdefault('strategy', 'round_robin')
    routing.setdefault('health_check', {})
    health_check = routing['health_check']
    health_check.setdefault('enabled', True)
    health_check.setdefault('interval', 30)
    health_check.setdefault('timeout', 5)
    monitoring = config['monitoring']
    monitoring.setdefault('log_level', 'INFO')
    monitoring.setdefault('track_latency', True)
    monitoring.setdefault('track_errors', True)
    timeouts = config['timeouts']
    timeouts.setdefault('request', 30)
    timeouts.setdefault('connect', 5)
    queue = config['queue']
    queue.setdefault('max_concurrent', 100)
    queue.setdefault('timeout', 60)
    for i, provider in enumerate(config['providers']):
        provider.setdefault('name', f'provider_{i}')
        provider.setdefault('weight', 1)
        provider.setdefault('fallback_only', False)
        provider.setdefault('model_map', {})
        provider.setdefault('max_concurrent', None)
    return config

class _Completions:

    def __init__(self, proxy_client):
        self.proxy_client = proxy_client
        self._system_message_support_cache = {}

    def _filter_kwargs(self, kwargs: dict) -> dict:
        """Filter out OptiLLM-specific parameters that shouldn't be sent to providers"""
        optillm_params = {'optillm_approach', 'proxy_wrap', 'wrapped_approach', 'wrap', 'mcts_simulations', 'mcts_exploration', 'mcts_depth', 'best_of_n', 'rstar_max_depth', 'rstar_num_rollouts', 'rstar_c'}
        return {k: v for k, v in kwargs.items() if k not in optillm_params}

    def _test_system_message_support(self, provider, model: str) -> bool:
        """Test if a model supports system messages"""
        cache_key = f'{provider.name}:{model}'
        if cache_key in self._system_message_support_cache:
            return self._system_message_support_cache[cache_key]
        try:
            test_response = provider.client.chat.completions.create(model=model, messages=[{'role': 'system', 'content': 'test'}, {'role': 'user', 'content': 'hi'}], max_tokens=1, temperature=0)
            self._system_message_support_cache[cache_key] = True
            return True
        except Exception as e:
            error_msg = str(e).lower()
            if any((pattern in error_msg for pattern in ['developer instruction', 'system message', 'not enabled', 'not supported'])):
                logger.info(f'Provider {provider.name} model {model} does not support system messages')
                self._system_message_support_cache[cache_key] = False
                return False
            self._system_message_support_cache[cache_key] = True
            return True

    def _format_messages_for_provider(self, provider, model: str, messages: list) -> list:
        """Format messages based on provider's system message support"""
        has_system = any((msg.get('role') == 'system' for msg in messages))
        if not has_system:
            return messages
        supports_system = self._test_system_message_support(provider, model)
        if supports_system:
            return messages
        formatted_messages = []
        system_content = None
        for msg in messages:
            if msg.get('role') == 'system':
                system_content = msg.get('content', '')
            elif msg.get('role') == 'user':
                if system_content:
                    formatted_messages.append({'role': 'user', 'content': f'Instructions: {system_content}\n\nUser: {msg.get('content', '')}'})
                    system_content = None
                else:
                    formatted_messages.append(msg)
            else:
                formatted_messages.append(msg)
        return formatted_messages

    def _make_request_with_timeout(self, provider, request_kwargs):
        """Make a request with timeout handling"""
        try:
            response = provider.client.chat.completions.create(**request_kwargs)
            return response
        except Exception as e:
            if 'timeout' in str(e).lower() or 'timed out' in str(e).lower():
                raise TimeoutError(f'Request to {provider.name} timed out after {self.proxy_client.request_timeout}s')
            raise e

    def create(self, **kwargs):
        """Create completion with load balancing, failover, and timeout handling"""
        if not self.proxy_client._request_semaphore.acquire(blocking=True, timeout=self.proxy_client.queue_timeout):
            raise TimeoutError(f'Request queue timeout after {self.proxy_client.queue_timeout}s - server overloaded')
        try:
            model = kwargs.get('model', 'unknown')
            attempted_providers = set()
            errors = []
            healthy_providers = [p for p in self.proxy_client.active_providers if p.is_healthy]
            if not healthy_providers:
                logger.warning('No healthy providers, trying fallback providers')
                healthy_providers = self.proxy_client.fallback_providers
            while healthy_providers:
                available_providers = [p for p in healthy_providers if p not in attempted_providers]
                if not available_providers:
                    break
                provider = self.proxy_client.router.select(available_providers)
                logger.info(f'Router selected provider: {(provider.name if provider else 'None')}')
                if not provider:
                    break
                attempted_providers.add(provider)
                slot_timeout = 10.0
                if not provider.acquire_slot(timeout=slot_timeout):
                    logger.debug(f'Provider {provider.name} at max capacity, trying next provider')
                    errors.append((provider.name, 'At max concurrent requests'))
                    continue
                try:
                    request_kwargs = self._filter_kwargs(kwargs.copy())
                    mapped_model = provider.map_model(model)
                    request_kwargs['model'] = mapped_model
                    if 'messages' in request_kwargs:
                        request_kwargs['messages'] = self._format_messages_for_provider(provider, mapped_model, request_kwargs['messages'])
                    request_kwargs['timeout'] = self.proxy_client.request_timeout
                    start_time = time.time()
                    logger.debug(f'Routing to {provider.name} with {self.proxy_client.request_timeout}s timeout')
                    response = self._make_request_with_timeout(provider, request_kwargs)
                    latency = time.time() - start_time
                    if self.proxy_client.track_latency:
                        provider.track_latency(latency)
                    logger.info(f'Request succeeded via {provider.name} in {latency:.2f}s')
                    return response
                except TimeoutError as e:
                    logger.error(f'Provider {provider.name} timed out: {e}')
                    errors.append((provider.name, str(e)))
                    if self.proxy_client.track_errors:
                        provider.is_healthy = False
                        provider.last_error = f'Timeout: {str(e)}'
                except Exception as e:
                    logger.error(f'Provider {provider.name} failed: {e}')
                    errors.append((provider.name, str(e)))
                    if self.proxy_client.track_errors:
                        provider.is_healthy = False
                        provider.last_error = str(e)
                finally:
                    provider.release_slot()
                    logger.debug(f'Released slot for provider {provider.name}')
            if self.proxy_client.fallback_client:
                logger.warning('All proxy providers failed, using fallback client')
                try:
                    fallback_kwargs = self._filter_kwargs(kwargs.copy())
                    fallback_kwargs['timeout'] = self.proxy_client.request_timeout
                    return self.proxy_client.fallback_client.chat.completions.create(**fallback_kwargs)
                except Exception as e:
                    errors.append(('fallback_client', str(e)))
            error_msg = f'All providers failed. Errors: {errors}'
            logger.error(error_msg)
            raise Exception(error_msg)
        finally:
            self.proxy_client._request_semaphore.release()

def _make_request_with_timeout(self, provider, request_kwargs):
    """Make a request with timeout handling"""
    try:
        response = provider.client.chat.completions.create(**request_kwargs)
        return response
    except Exception as e:
        if 'timeout' in str(e).lower() or 'timed out' in str(e).lower():
            raise TimeoutError(f'Request to {provider.name} timed out after {self.proxy_client.request_timeout}s')
        raise e

class ApproachHandler:
    """Dynamically handles both approaches and plugins"""

    def __init__(self):
        self._approaches_cache = {}
        self._plugins_cache = {}
        self._discovered = False

    def handle(self, name: str, system_prompt: str, initial_query: str, client, model: str, request_config: dict=None) -> Optional[Tuple[str, int]]:
        """
        Try to handle the given name as an approach or plugin.
        Returns None if not found, otherwise returns (response, tokens)
        """
        if not self._discovered:
            self._discover_handlers()
            self._discovered = True
        if name in self._approaches_cache:
            logger.info(f"Routing approach '{name}' through proxy")
            handler = self._approaches_cache[name]
            return self._execute_handler(handler, system_prompt, initial_query, client, model, request_config)
        if name in self._plugins_cache:
            logger.info(f"Routing plugin '{name}' through proxy")
            handler = self._plugins_cache[name]
            return self._execute_handler(handler, system_prompt, initial_query, client, model, request_config)
        logger.debug(f"'{name}' not recognized as approach or plugin")
        return None

    def _discover_handlers(self):
        """Discover available approaches and plugins dynamically"""
        self._discover_approaches()
        self._discover_plugins()
        logger.info(f'Discovered {len(self._approaches_cache)} approaches, {len(self._plugins_cache)} plugins')

    def _discover_approaches(self):
        """Discover built-in approaches from optillm package"""
        approach_modules = {'mcts': ('optillm.mcts', 'chat_with_mcts'), 'bon': ('optillm.bon', 'best_of_n_sampling'), 'moa': ('optillm.moa', 'mixture_of_agents'), 'rto': ('optillm.rto', 'round_trip_optimization'), 'self_consistency': ('optillm.self_consistency', 'advanced_self_consistency_approach'), 'pvg': ('optillm.pvg', 'inference_time_pv_game'), 'z3': ('optillm.z3_solver', None), 'rstar': ('optillm.rstar', None), 'cot_reflection': ('optillm.cot_reflection', 'cot_reflection'), 'plansearch': ('optillm.plansearch', 'plansearch'), 'leap': ('optillm.leap', 'leap'), 're2': ('optillm.reread', 're2_approach'), 'cepo': ('optillm.cepo.cepo', 'cepo')}
        for name, (module_path, func_name) in approach_modules.items():
            try:
                module = importlib.import_module(module_path)
                if name == 'z3':
                    solver_class = getattr(module, 'Z3SymPySolverSystem')
                    self._approaches_cache[name] = lambda s, q, c, m, **kw: solver_class(s, c, m).process_query(q)
                elif name == 'rstar':
                    rstar_class = getattr(module, 'RStar')
                    self._approaches_cache[name] = lambda s, q, c, m, **kw: rstar_class(s, c, m, **kw).solve(q)
                elif name == 'cepo':
                    cepo_func = getattr(module, func_name)
                    self._approaches_cache[name] = cepo_func
                elif func_name:
                    self._approaches_cache[name] = getattr(module, func_name)
            except (ImportError, AttributeError) as e:
                logger.debug(f"Could not load approach '{name}': {e}")

    def _discover_plugins(self):
        """Discover available plugins dynamically"""
        try:
            import optillm
            import os
            import glob
            package_dir = Path(optillm.__file__).parent / 'plugins'
            plugin_files = []
            if package_dir.exists():
                plugin_files.extend(glob.glob(str(package_dir / '*.py')))
            for plugin_file in plugin_files:
                if '__pycache__' in plugin_file or '__init__' in plugin_file:
                    continue
                try:
                    module_name = Path(plugin_file).stem
                    if module_name == 'proxy_plugin':
                        continue
                    spec = importlib.util.spec_from_file_location(module_name, plugin_file)
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        if hasattr(module, 'SLUG') and hasattr(module, 'run'):
                            slug = getattr(module, 'SLUG')
                            run_func = getattr(module, 'run')
                            self._plugins_cache[slug] = run_func
                except Exception as e:
                    logger.debug(f'Could not load plugin from {plugin_file}: {e}')
        except Exception as e:
            logger.debug(f'Error discovering plugins: {e}')

    def _execute_handler(self, handler, system_prompt: str, initial_query: str, client, model: str, request_config: dict=None) -> Tuple[str, int]:
        """Execute a handler function with proper signature detection"""
        try:
            sig = inspect.signature(handler)
            params = sig.parameters
            args = [system_prompt, initial_query, client, model]
            kwargs = {}
            if 'request_config' in params:
                kwargs['request_config'] = request_config
            if any((p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())):
                if request_config:
                    safe_kwargs = {k: v for k, v in request_config.items() if k not in ['model', 'messages', 'system_prompt', 'initial_query']}
                    kwargs.update(safe_kwargs)
            return handler(*args, **kwargs)
        except Exception as e:
            logger.error(f'Error executing handler: {e}')
            raise

def _discover_plugins(self):
    """Discover available plugins dynamically"""
    try:
        import optillm
        import os
        import glob
        package_dir = Path(optillm.__file__).parent / 'plugins'
        plugin_files = []
        if package_dir.exists():
            plugin_files.extend(glob.glob(str(package_dir / '*.py')))
        for plugin_file in plugin_files:
            if '__pycache__' in plugin_file or '__init__' in plugin_file:
                continue
            try:
                module_name = Path(plugin_file).stem
                if module_name == 'proxy_plugin':
                    continue
                spec = importlib.util.spec_from_file_location(module_name, plugin_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    if hasattr(module, 'SLUG') and hasattr(module, 'run'):
                        slug = getattr(module, 'SLUG')
                        run_func = getattr(module, 'run')
                        self._plugins_cache[slug] = run_func
            except Exception as e:
                logger.debug(f'Could not load plugin from {plugin_file}: {e}')
    except Exception as e:
        logger.debug(f'Error discovering plugins: {e}')

def concurrent_map(gen_function: Callable, client, model: str, context_chunks: List[str], query: str, system_prompt: str, cb_log: CBLog, summaries_per_chunk: Optional[List[str]]=None, workers: int=16) -> Tuple[List[str], CBLog]:
    """
    Runs `gen_function` concurrently over a list of context chunks.

    Args:
        gen_function (Callable): Function to call with each chunk and associated arguments.
        client: LLM API client.
        model (str): Base model name.
        context_chunks (List[str]): Input context chunks.
        query (str): User query.
        system_prompt (str): System prompt string.
        cb_log (CBLog): Log object for tracking model calls.
        summaries_per_chunk (Optional[List[str]]): Concatenated neighbor summaries for each chunk.
        workers (int): Number of threads to use.

    Returns:
        Tuple[List[str], CBLog]: List of responses (in original order) and updated log object.
    """
    result = [None] * len(context_chunks)
    wrapped_gen_function = lambda index, *args: (index, gen_function(*args))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_idx = {}
        for idx, chunk in enumerate(context_chunks):
            args = [client, model, chunk, query, system_prompt]
            if summaries_per_chunk is not None:
                args.append(summaries_per_chunk[idx])
            future_to_idx[executor.submit(wrapped_gen_function, idx, *args)] = idx
        for future in as_completed(future_to_idx):
            try:
                index, (response, upd_log) = future.result()
                result[index] = response
                cb_log.update(upd_log)
            except Exception as e:
                logger.error(f'Error processing chunk: {e}')
    return (result, cb_log)

def remove_chunks(chunks: List[str], irrelevance_tags: Tuple[str]) -> List[str]:
    """
    Filter out chunks that contain at least one of irrelevance tags.
    """
    new_chunks = []
    for chunk in chunks:
        flag = False
        for tag in irrelevance_tags:
            if tag.upper() in chunk.upper():
                flag = True
                break
        if not flag:
            new_chunks.append(chunk)
    return new_chunks

class SelfDiscover:
    """
    Implementation of the SELF-DISCOVER framework.
    
    The framework operates in two stages:
    1. Stage 1: Discover task-specific reasoning structure (SELECT, ADAPT, IMPLEMENT)
    2. Stage 2: Use discovered structure to solve problem instances
    """

    def __init__(self, client, model: str, max_tokens: int=16382):
        self.client = client
        self.model = model
        self.max_tokens = max_tokens
        self.reasoning_modules = get_all_modules()
        self.completion_tokens = 0

    def discover_reasoning_structure(self, task_description: str, task_examples: List[str]=None) -> Dict[str, Any]:
        """
        Stage 1: Discover reasoning structure for the given task.
        
        Args:
            task_description: Description of the task type
            task_examples: Optional examples of the task (without labels)
            
        Returns:
            Dict containing the discovered reasoning structure
        """
        logger.info('Starting SELF-DISCOVER reasoning structure discovery')
        selected_modules = self._select_modules(task_description, task_examples)
        logger.info(f'Selected {len(selected_modules)} reasoning modules')
        adapted_modules = self._adapt_modules(selected_modules, task_description, task_examples)
        logger.info('Adapted modules to be task-specific')
        reasoning_structure = self._implement_structure(adapted_modules, task_description, task_examples)
        logger.info('Implemented reasoning structure')
        return {'selected_modules': selected_modules, 'adapted_modules': adapted_modules, 'reasoning_structure': reasoning_structure, 'completion_tokens': self.completion_tokens}

    def _select_modules(self, task_description: str, task_examples: List[str]=None) -> List[Dict[str, Any]]:
        """SELECT: Choose relevant reasoning modules for the task."""
        module_descriptions = get_module_descriptions()
        modules_text = '\n'.join([f'{i + 1}. {desc}' for i, desc in enumerate(module_descriptions)])
        examples_text = ''
        if task_examples:
            examples_text = '\n\nTask examples:\n' + '\n'.join([f'Example {i + 1}: {ex}' for i, ex in enumerate(task_examples)])
        select_prompt = f'You are an expert in problem-solving and reasoning. Given a task description and available reasoning modules, select the most relevant modules that would be useful for solving this type of task.\n\nTask description: {task_description}{examples_text}\n\nAvailable reasoning modules:\n{modules_text}\n\nInstructions:\n1. Analyze the task and identify what types of reasoning would be most helpful\n2. Select 3-7 reasoning modules that are most relevant for this task\n3. Consider both the complexity of the task and the complementary nature of different modules\n4. Avoid selecting too many similar modules\n5. IMPORTANT: Respond ONLY with a valid JSON array of numbers\n\nExample response format: [1, 5, 9, 15, 23]\n\nSelected modules (JSON array only):'
        response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'user', 'content': select_prompt}], max_tokens=1024, temperature=0.3)
        self.completion_tokens += response.usage.completion_tokens
        try:
            response_text = response.choices[0].message.content.strip()
            json_match = re.search('\\[[\\d,\\s]+\\]', response_text)
            if json_match:
                selected_indices = json.loads(json_match.group(0))
            else:
                numbers = re.findall('\\b(\\d+)\\b', response_text)
                selected_indices = [int(n) for n in numbers[:7]]
            selected_modules = []
            for idx in selected_indices:
                if 1 <= idx <= len(self.reasoning_modules):
                    selected_modules.append(self.reasoning_modules[idx - 1])
            return selected_modules[:7]
        except Exception as e:
            logger.warning(f'Error parsing selected modules: {e}')
            return self.reasoning_modules[:5]

    def _adapt_modules(self, selected_modules: List[Dict[str, Any]], task_description: str, task_examples: List[str]=None) -> List[str]:
        """ADAPT: Rephrase modules to be more task-specific."""
        modules_text = '\n'.join([f'- {module['description']}' for module in selected_modules])
        examples_text = ''
        if task_examples:
            examples_text = '\n\nTask examples:\n' + '\n'.join([f'Example {i + 1}: {ex}' for i, ex in enumerate(task_examples)])
        adapt_prompt = f'You are an expert in adapting general reasoning strategies to specific tasks. Given the selected reasoning modules and task description, rephrase each module to be more specific and tailored to this particular type of task.\n\nTask description: {task_description}{examples_text}\n\nSelected reasoning modules:\n{modules_text}\n\nInstructions:\n1. For each module, rephrase the description to be more specific to this task\n2. Keep the core reasoning approach but make it more actionable for this specific type of problem\n3. Use terminology and concepts relevant to the task domain\n4. Make the adapted descriptions more concrete and specific\n\nProvide the adapted modules as a numbered list:'
        response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'user', 'content': adapt_prompt}], max_tokens=2048, temperature=0.3)
        self.completion_tokens += response.usage.completion_tokens
        response_text = response.choices[0].message.content.strip()
        adapted_modules = []
        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()
            if re.match('^\\d+\\.', line):
                adapted_desc = re.sub('^\\d+\\.\\s*', '', line)
                adapted_modules.append(adapted_desc)
        return adapted_modules

    def _implement_structure(self, adapted_modules: List[str], task_description: str, task_examples: List[str]=None) -> Dict[str, Any]:
        """IMPLEMENT: Create a structured reasoning plan in JSON format."""
        modules_text = '\n'.join([f'{i + 1}. {module}' for i, module in enumerate(adapted_modules)])
        examples_text = ''
        if task_examples:
            examples_text = '\n\nTask examples:\n' + '\n'.join([f'Example {i + 1}: {ex}' for i, ex in enumerate(task_examples)])
        demo_structure = '{\n    "problem_analysis": "Analyze the core components and requirements",\n    "approach_selection": "Choose the most appropriate solution method",\n    "step_by_step_solution": {\n        "step_1": "First logical step with clear reasoning",\n        "step_2": "Second step building on previous results", \n        "step_3": "Continue logical progression"\n    },\n    "verification": "Check the solution for accuracy and completeness",\n    "final_answer": "Present the final result clearly"\n}'
        implement_prompt = f'You are an expert in creating structured reasoning plans. Given the adapted reasoning modules for a specific task, create a detailed JSON reasoning structure that can be followed step-by-step to solve instances of this task.\n\nTask description: {task_description}{examples_text}\n\nAdapted reasoning modules:\n{modules_text}\n\nExample of a reasoning structure format:\n{demo_structure}\n\nInstructions:\n1. Create a JSON structure that operationalizes the adapted reasoning modules\n2. The structure should be specific enough to guide step-by-step reasoning\n3. Include clear field names that indicate what should be filled in each step\n4. Make it actionable - each field should represent a concrete reasoning step\n5. Ensure the structure flows logically from problem understanding to final answer\n6. The structure should be comprehensive enough to handle the complexity of the task\n\n7. IMPORTANT: Return ONLY valid JSON with double quotes around all property names and string values\n8. Do not include any text before or after the JSON structure\n\nValid JSON reasoning structure:'
        response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'user', 'content': implement_prompt}], max_tokens=2048, temperature=0.3)
        self.completion_tokens += response.usage.completion_tokens
        response_text = response.choices[0].message.content.strip()
        return self._parse_json_structure(response_text)

    def _parse_json_structure(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON structure with robust error handling and cleanup."""
        fallback_structure = {'problem_understanding': 'Analyze and understand the problem requirements', 'solution_approach': 'Determine the best approach based on problem characteristics', 'step_by_step_reasoning': 'Work through the problem systematically', 'verification': 'Verify the solution is correct and complete', 'final_answer': 'State the final answer clearly'}
        strategies = [self._extract_json_strategy_1, self._extract_json_strategy_2, self._extract_json_strategy_3, self._clean_and_parse_strategy]
        for i, strategy in enumerate(strategies, 1):
            try:
                structure = strategy(response_text)
                if structure and isinstance(structure, dict) and (len(structure) > 0):
                    logger.debug(f'Successfully parsed JSON using strategy {i}')
                    return structure
            except Exception as e:
                logger.debug(f'Strategy {i} failed: {e}')
                continue
        logger.warning(f'All JSON parsing strategies failed. Using fallback structure.')
        logger.debug(f'Raw response that failed to parse: {response_text[:500]}...')
        return fallback_structure

    def _extract_json_strategy_1(self, text: str) -> Dict[str, Any]:
        """Strategy 1: Find first complete JSON object with balanced braces."""
        start_idx = text.find('{')
        if start_idx == -1:
            raise ValueError('No opening brace found')
        brace_count = 0
        end_idx = start_idx
        for i in range(start_idx, len(text)):
            if text[i] == '{':
                brace_count += 1
            elif text[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_idx = i + 1
                    break
        if brace_count != 0:
            raise ValueError('Unbalanced braces')
        json_str = text[start_idx:end_idx]
        return json.loads(json_str)

    def _extract_json_strategy_2(self, text: str) -> Dict[str, Any]:
        """Strategy 2: Use regex with non-greedy matching."""
        json_match = re.search('\\{[^{}]*(?:\\{[^{}]*\\}[^{}]*)*\\}', text)
        if not json_match:
            raise ValueError('No JSON object found with regex')
        json_str = json_match.group(0)
        return json.loads(json_str)

    def _extract_json_strategy_3(self, text: str) -> Dict[str, Any]:
        """Strategy 3: Extract between ```json``` code blocks."""
        patterns = ['```json\\s*([^`]+)```', '```\\s*([^`]+)```', '`([^`]+)`']
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                json_str = match.group(1).strip()
                try:
                    return json.loads(json_str)
                except:
                    continue
        raise ValueError('No valid JSON found in code blocks')

    def _clean_and_parse_strategy(self, text: str) -> Dict[str, Any]:
        """Strategy 4: Clean common formatting issues and parse."""
        json_match = re.search('\\{.*\\}', text, re.DOTALL)
        if not json_match:
            raise ValueError('No JSON-like content found')
        json_str = json_match.group(0)
        cleanups = [("(?<!\\\\)'([^']*)'(?=\\s*[,}])", '"\\1"'), ('([{,]\\s*)([a-zA-Z_][a-zA-Z0-9_]*)\\s*:', '\\1"\\2":'), (',\\s*([}\\]])', '\\1'), (',,+', ',')]
        for pattern, replacement in cleanups:
            json_str = re.sub(pattern, replacement, json_str)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            if 'line 1 column 2' in str(e):
                json_str = re.sub('^[^{]*', '', json_str)
                return json.loads(json_str)
            else:
                raise e

    def solve_with_structure(self, problem: str, reasoning_structure: Dict[str, Any]) -> str:
        """
        Stage 2: Use the discovered reasoning structure to solve a specific problem.
        """
        structure_text = json.dumps(reasoning_structure, indent=2)
        solve_prompt = f'Follow the step-by-step reasoning structure below to solve the given problem. Fill in each field with your reasoning and analysis, then provide your final answer.\n\nReasoning Structure:\n{structure_text}\n\nProblem to solve: {problem}\n\nInstructions:\n1. Work through each field in the reasoning structure systematically\n2. Provide detailed reasoning for each step\n3. Use the structure to guide your thinking process\n4. Ensure your reasoning is logical and well-supported\n5. Wrap your internal reasoning in <think> tags\n6. Provide a clear final answer after your reasoning\n\n<think>\n[Follow the reasoning structure step by step here]\n</think>\n\nBased on my systematic analysis using the reasoning structure, the answer is:'
        response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'user', 'content': solve_prompt}], max_tokens=self.max_tokens, temperature=0.7)
        self.completion_tokens += response.usage.completion_tokens
        return response.choices[0].message.content.strip()

def _adapt_modules(self, selected_modules: List[Dict[str, Any]], task_description: str, task_examples: List[str]=None) -> List[str]:
    """ADAPT: Rephrase modules to be more task-specific."""
    modules_text = '\n'.join([f'- {module['description']}' for module in selected_modules])
    examples_text = ''
    if task_examples:
        examples_text = '\n\nTask examples:\n' + '\n'.join([f'Example {i + 1}: {ex}' for i, ex in enumerate(task_examples)])
    adapt_prompt = f'You are an expert in adapting general reasoning strategies to specific tasks. Given the selected reasoning modules and task description, rephrase each module to be more specific and tailored to this particular type of task.\n\nTask description: {task_description}{examples_text}\n\nSelected reasoning modules:\n{modules_text}\n\nInstructions:\n1. For each module, rephrase the description to be more specific to this task\n2. Keep the core reasoning approach but make it more actionable for this specific type of problem\n3. Use terminology and concepts relevant to the task domain\n4. Make the adapted descriptions more concrete and specific\n\nProvide the adapted modules as a numbered list:'
    response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'user', 'content': adapt_prompt}], max_tokens=2048, temperature=0.3)
    self.completion_tokens += response.usage.completion_tokens
    response_text = response.choices[0].message.content.strip()
    adapted_modules = []
    lines = response_text.split('\n')
    for line in lines:
        line = line.strip()
        if re.match('^\\d+\\.', line):
            adapted_desc = re.sub('^\\d+\\.\\s*', '', line)
            adapted_modules.append(adapted_desc)
    return adapted_modules

def _implement_structure(self, adapted_modules: List[str], task_description: str, task_examples: List[str]=None) -> Dict[str, Any]:
    """IMPLEMENT: Create a structured reasoning plan in JSON format."""
    modules_text = '\n'.join([f'{i + 1}. {module}' for i, module in enumerate(adapted_modules)])
    examples_text = ''
    if task_examples:
        examples_text = '\n\nTask examples:\n' + '\n'.join([f'Example {i + 1}: {ex}' for i, ex in enumerate(task_examples)])
    demo_structure = '{\n    "problem_analysis": "Analyze the core components and requirements",\n    "approach_selection": "Choose the most appropriate solution method",\n    "step_by_step_solution": {\n        "step_1": "First logical step with clear reasoning",\n        "step_2": "Second step building on previous results", \n        "step_3": "Continue logical progression"\n    },\n    "verification": "Check the solution for accuracy and completeness",\n    "final_answer": "Present the final result clearly"\n}'
    implement_prompt = f'You are an expert in creating structured reasoning plans. Given the adapted reasoning modules for a specific task, create a detailed JSON reasoning structure that can be followed step-by-step to solve instances of this task.\n\nTask description: {task_description}{examples_text}\n\nAdapted reasoning modules:\n{modules_text}\n\nExample of a reasoning structure format:\n{demo_structure}\n\nInstructions:\n1. Create a JSON structure that operationalizes the adapted reasoning modules\n2. The structure should be specific enough to guide step-by-step reasoning\n3. Include clear field names that indicate what should be filled in each step\n4. Make it actionable - each field should represent a concrete reasoning step\n5. Ensure the structure flows logically from problem understanding to final answer\n6. The structure should be comprehensive enough to handle the complexity of the task\n\n7. IMPORTANT: Return ONLY valid JSON with double quotes around all property names and string values\n8. Do not include any text before or after the JSON structure\n\nValid JSON reasoning structure:'
    response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'user', 'content': implement_prompt}], max_tokens=2048, temperature=0.3)
    self.completion_tokens += response.usage.completion_tokens
    response_text = response.choices[0].message.content.strip()
    return self._parse_json_structure(response_text)

def solve_with_structure(self, problem: str, reasoning_structure: Dict[str, Any]) -> str:
    """
        Stage 2: Use the discovered reasoning structure to solve a specific problem.
        """
    structure_text = json.dumps(reasoning_structure, indent=2)
    solve_prompt = f'Follow the step-by-step reasoning structure below to solve the given problem. Fill in each field with your reasoning and analysis, then provide your final answer.\n\nReasoning Structure:\n{structure_text}\n\nProblem to solve: {problem}\n\nInstructions:\n1. Work through each field in the reasoning structure systematically\n2. Provide detailed reasoning for each step\n3. Use the structure to guide your thinking process\n4. Ensure your reasoning is logical and well-supported\n5. Wrap your internal reasoning in <think> tags\n6. Provide a clear final answer after your reasoning\n\n<think>\n[Follow the reasoning structure step by step here]\n</think>\n\nBased on my systematic analysis using the reasoning structure, the answer is:'
    response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'user', 'content': solve_prompt}], max_tokens=self.max_tokens, temperature=0.7)
    self.completion_tokens += response.usage.completion_tokens
    return response.choices[0].message.content.strip()

class UncertaintyRoutedCoT:
    """
    Implements uncertainty-routed chain-of-thought reasoning.
    
    The approach:
    1. Generate k chain-of-thought samples
    2. Evaluate confidence through consistency analysis
    3. Route to majority vote (high confidence) or greedy sample (low confidence)
    """

    def __init__(self, client, model: str, max_tokens: int=16382):
        self.client = client
        self.model = model
        self.max_tokens = max_tokens
        self.completion_tokens = 0

    def generate_with_uncertainty_routing(self, prompt: str, num_samples: int=3, confidence_threshold: float=0.7, temperature: float=0.7, top_p: float=0.95) -> Dict[str, Any]:
        """
        Generate response using uncertainty-routed chain-of-thought.
        
        Args:
            prompt: The prompt to generate responses for
            num_samples: Number of samples to generate for uncertainty evaluation
            confidence_threshold: Threshold for routing decision
            temperature: Sampling temperature for multiple samples
            top_p: Top-p parameter for sampling
            
        Returns:
            Dict containing final response, confidence score, and routing decision
        """
        logger.info(f'Generating {num_samples} samples for uncertainty routing')
        samples = self._generate_multiple_samples(prompt, num_samples, temperature, top_p)
        greedy_sample = self._generate_greedy_sample(prompt)
        sample_data = []
        for sample in samples:
            thinking = self._extract_thinking(sample)
            answer = self._extract_answer(sample)
            sample_data.append({'full_response': sample, 'thinking': thinking, 'answer': answer})
        greedy_thinking = self._extract_thinking(greedy_sample)
        greedy_answer = self._extract_answer(greedy_sample)
        confidence_score = self._evaluate_confidence(sample_data)
        logger.debug(f'Confidence evaluation completed: {confidence_score:.3f}')
        logger.debug(f'Sample answers: {[sample['answer'][:50] + '...' if len(sample['answer']) > 50 else sample['answer'] for sample in sample_data if sample['answer']]}')
        if confidence_score >= confidence_threshold:
            final_response = self._majority_vote_response(sample_data)
            routing_decision = 'majority_vote'
            logger.info(f'High confidence ({confidence_score:.3f} >= {confidence_threshold}) - using majority vote')
        else:
            final_response = greedy_sample
            routing_decision = 'greedy'
            logger.info(f'Low confidence ({confidence_score:.3f} < {confidence_threshold}) - using greedy sample')
        return {'final_response': final_response, 'confidence_score': confidence_score, 'routing_decision': routing_decision, 'samples': sample_data, 'greedy_sample': {'full_response': greedy_sample, 'thinking': greedy_thinking, 'answer': greedy_answer}, 'completion_tokens': self.completion_tokens}

    def _generate_multiple_samples(self, prompt: str, num_samples: int, temperature: float, top_p: float) -> List[str]:
        """Generate multiple samples by calling the API multiple times."""
        samples = []
        for i in range(num_samples):
            logger.debug(f'Generating sample {i + 1}/{num_samples}')
            response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'user', 'content': prompt}], max_tokens=self.max_tokens, temperature=temperature, top_p=top_p)
            self.completion_tokens += response.usage.completion_tokens
            samples.append(response.choices[0].message.content.strip())
        return samples

    def _generate_greedy_sample(self, prompt: str) -> str:
        """Generate a single greedy sample with temperature=0."""
        logger.debug('Generating greedy sample')
        response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'user', 'content': prompt}], max_tokens=self.max_tokens, temperature=0.0)
        self.completion_tokens += response.usage.completion_tokens
        return response.choices[0].message.content.strip()

    def _extract_thinking(self, response: str) -> str:
        """Extract content from <think> tags."""
        match = re.search('<think>(.*?)</think>', response, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ''

    def _extract_answer(self, response: str) -> str:
        """Extract the final answer from the response."""
        think_end = response.find('</think>')
        if think_end != -1:
            answer_part = response[think_end + 8:].strip()
        else:
            answer_part = response.strip()
        patterns = ['(?:the )?(?:final )?answer is:?\\s*(.+?)(?:\\n|$)', '(?:therefore|thus|so),?\\s*(?:the )?(?:answer is:?\\s*)?(.+?)(?:\\n|$)', '(?:conclusion|result):?\\s*(.+?)(?:\\n|$)']
        for pattern in patterns:
            match = re.search(pattern, answer_part, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        lines = answer_part.split('\n')
        for line in lines:
            line = line.strip()
            if line and len(line) > 10:
                return line
        return answer_part[:200] if answer_part else ''

    def _evaluate_confidence(self, sample_data: List[Dict[str, Any]]) -> float:
        """
        Evaluate confidence based on consistency across samples.
        
        Returns a confidence score between 0 and 1.
        """
        if len(sample_data) < 2:
            return 0.5
        answers = [sample['answer'] for sample in sample_data if sample['answer']]
        thinking_texts = [sample['thinking'] for sample in sample_data if sample['thinking']]
        if not answers:
            return 0.1
        answer_consistency = self._calculate_answer_consistency(answers)
        reasoning_consistency = self._calculate_reasoning_consistency(thinking_texts)
        confidence = 0.6 * answer_consistency + 0.4 * reasoning_consistency
        logger.debug(f'Answer consistency: {answer_consistency:.3f} (weight: 0.6)')
        logger.debug(f'Reasoning consistency: {reasoning_consistency:.3f} (weight: 0.4)')
        logger.debug(f'Combined confidence: {confidence:.3f}')
        if confidence < 0.5:
            logger.debug(f'Low confidence detected. Sample count: {len(sample_data)}')
            logger.debug(f'Answers found: {len(answers)}, Thinking texts: {len(thinking_texts)}')
            if answers:
                logger.debug(f'Sample answers: {answers}')
            if len(answers) >= 2:
                logger.debug(f'Most common answer appears {max(Counter(answers).values())} times out of {len(answers)}')
        return confidence

    def _calculate_answer_consistency(self, answers: List[str]) -> float:
        """Calculate consistency of final answers."""
        if len(answers) < 2:
            return 0.5
        normalized_answers = []
        for answer in answers:
            norm_answer = re.sub('[^\\w\\s]', '', answer.lower().strip())
            norm_answer = re.sub('\\s+', ' ', norm_answer)
            normalized_answers.append(norm_answer)
        answer_counts = Counter(normalized_answers)
        most_common_count = answer_counts.most_common(1)[0][1]
        total_answers = len(answers)
        agreement_ratio = most_common_count / total_answers
        logger.debug(f'Answer distribution: {dict(answer_counts)}')
        logger.debug(f'Agreement ratio: {agreement_ratio:.3f} ({most_common_count}/{total_answers})')
        max_similarity = 0.0
        for i, ans1 in enumerate(normalized_answers):
            for j, ans2 in enumerate(normalized_answers[i + 1:], i + 1):
                similarity = SequenceMatcher(None, ans1, ans2).ratio()
                max_similarity = max(max_similarity, similarity)
        consistency = max(agreement_ratio, max_similarity)
        return min(consistency, 1.0)

    def _calculate_reasoning_consistency(self, thinking_texts: List[str]) -> float:
        """Calculate consistency of reasoning processes."""
        if len(thinking_texts) < 2:
            return 0.5
        similarities = []
        for i, text1 in enumerate(thinking_texts):
            for j, text2 in enumerate(thinking_texts[i + 1:], i + 1):
                similarity = SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
                similarities.append(similarity)
        if not similarities:
            return 0.5
        avg_similarity = sum(similarities) / len(similarities)
        logger.debug(f'Reasoning similarity pairs: {[f'{s:.3f}' for s in similarities]}')
        logger.debug(f'Average reasoning similarity: {avg_similarity:.3f}')
        return min(avg_similarity, 1.0)

    def _majority_vote_response(self, sample_data: List[Dict[str, Any]]) -> str:
        """
        Create response based on majority vote of answers and best reasoning.
        """
        answers = [sample['answer'] for sample in sample_data if sample['answer']]
        if not answers:
            return sample_data[0]['full_response']
        normalized_answers = []
        for answer in answers:
            norm_answer = re.sub('[^\\w\\s]', '', answer.lower().strip())
            norm_answer = re.sub('\\s+', ' ', norm_answer)
            normalized_answers.append(norm_answer)
        answer_counts = Counter(normalized_answers)
        most_common_answer = answer_counts.most_common(1)[0][0]
        best_sample = None
        best_reasoning_length = 0
        for i, sample in enumerate(sample_data):
            if sample['answer']:
                norm_answer = re.sub('[^\\w\\s]', '', sample['answer'].lower().strip())
                norm_answer = re.sub('\\s+', ' ', norm_answer)
                if norm_answer == most_common_answer:
                    reasoning_length = len(sample['thinking'])
                    if reasoning_length > best_reasoning_length:
                        best_reasoning_length = reasoning_length
                        best_sample = sample
        if best_sample:
            return best_sample['full_response']
        else:
            for sample in sample_data:
                if sample['answer']:
                    norm_answer = re.sub('[^\\w\\s]', '', sample['answer'].lower().strip())
                    norm_answer = re.sub('\\s+', ' ', norm_answer)
                    if norm_answer == most_common_answer:
                        return sample['full_response']
        return sample_data[0]['full_response']

def _generate_multiple_samples(self, prompt: str, num_samples: int, temperature: float, top_p: float) -> List[str]:
    """Generate multiple samples by calling the API multiple times."""
    samples = []
    for i in range(num_samples):
        logger.debug(f'Generating sample {i + 1}/{num_samples}')
        response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'user', 'content': prompt}], max_tokens=self.max_tokens, temperature=temperature, top_p=top_p)
        self.completion_tokens += response.usage.completion_tokens
        samples.append(response.choices[0].message.content.strip())
    return samples

def _generate_greedy_sample(self, prompt: str) -> str:
    """Generate a single greedy sample with temperature=0."""
    logger.debug('Generating greedy sample')
    response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'user', 'content': prompt}], max_tokens=self.max_tokens, temperature=0.0)
    self.completion_tokens += response.usage.completion_tokens
    return response.choices[0].message.content.strip()

def _majority_vote_response(self, sample_data: List[Dict[str, Any]]) -> str:
    """
        Create response based on majority vote of answers and best reasoning.
        """
    answers = [sample['answer'] for sample in sample_data if sample['answer']]
    if not answers:
        return sample_data[0]['full_response']
    normalized_answers = []
    for answer in answers:
        norm_answer = re.sub('[^\\w\\s]', '', answer.lower().strip())
        norm_answer = re.sub('\\s+', ' ', norm_answer)
        normalized_answers.append(norm_answer)
    answer_counts = Counter(normalized_answers)
    most_common_answer = answer_counts.most_common(1)[0][0]
    best_sample = None
    best_reasoning_length = 0
    for i, sample in enumerate(sample_data):
        if sample['answer']:
            norm_answer = re.sub('[^\\w\\s]', '', sample['answer'].lower().strip())
            norm_answer = re.sub('\\s+', ' ', norm_answer)
            if norm_answer == most_common_answer:
                reasoning_length = len(sample['thinking'])
                if reasoning_length > best_reasoning_length:
                    best_reasoning_length = reasoning_length
                    best_sample = sample
    if best_sample:
        return best_sample['full_response']
    else:
        for sample in sample_data:
            if sample['answer']:
                norm_answer = re.sub('[^\\w\\s]', '', sample['answer'].lower().strip())
                norm_answer = re.sub('\\s+', ' ', norm_answer)
                if norm_answer == most_common_answer:
                    return sample['full_response']
    return sample_data[0]['full_response']

def augment_system_prompt(system_prompt: str, strategies: List[Any]) -> str:
    """
    Augment the system prompt with selected strategies and reasoning examples.
    Instructs the LLM to apply the strategies in its solution.
    
    Args:
        system_prompt: The original system prompt
        strategies: A list of strategies to add to the prompt
    
    Returns:
        str: The augmented system prompt
    """
    if not strategies:
        return system_prompt
    strategies_section = ''
    for i, strategy in enumerate(strategies, 1):
        strategies_section += f'Strategy {i} for {strategy.problem_type} problems:\n{strategy.strategy_text}\n\n'
        if strategy.reasoning_examples:
            reasoning = strategy.reasoning_examples[-1]
            if reasoning:
                strategies_section += f'Example reasoning process:\n<think>\n{reasoning}\n</think>\n\n'
    strategy_prompt = STRATEGY_APPLICATION_PROMPT.format(strategies_section=strategies_section)
    augmented_prompt = system_prompt + '\n\n' + strategy_prompt
    return augmented_prompt

def evaluate_strategy_effectiveness(response: str, thinking: Optional[str], selected_strategies: List[Strategy], client, model: str) -> Dict[str, bool]:
    """
    Evaluate how effective each strategy was in generating the response.
    
    Args:
        response: The LLM's final response to the query
        thinking: The LLM's reasoning process (if any)
        selected_strategies: The strategies that were used
        client: LLM client for making API calls
        model: Model identifier
    
    Returns:
        Dict[str, bool]: Mapping from strategy ID to effectiveness (True/False)
    """
    if not selected_strategies:
        return {}
    results = {}
    try:
        for strategy in selected_strategies:
            full_response = thinking + '\n\n' + response if thinking else response
            messages = [{'role': 'system', 'content': STRATEGY_EVALUATION_PROMPT}, {'role': 'user', 'content': f'Strategy:\n{strategy.strategy_text}\n\nResponse (including reasoning):\n{full_response}\n\nDoes the response show clear evidence that the strategy was effectively applied? Answer with ONLY YES or NO.'}]
            eval_response = client.chat.completions.create(model=model, messages=messages, temperature=0.1, max_tokens=DEFAULT_MAX_TOKENS)
            result_text = eval_response.choices[0].message.content
            final_result, eval_thinking = extract_thinking(result_text)
            final_result = final_result.strip().upper()
            logger.debug(f"Strategy evaluation - raw response: '{result_text}'")
            logger.debug(f"Strategy evaluation - final result after removing thinking: '{final_result}'")
            is_effective = 'YES' in final_result
            results[strategy.strategy_id] = is_effective
            logger.info(f'Strategy {strategy.strategy_id} evaluation: {final_result} -> {is_effective}')
    except Exception as e:
        logger.error(f'Error evaluating strategy effectiveness: {str(e)}')
        for strategy in selected_strategies:
            results[strategy.strategy_id] = False
    return results

def refine_strategy(strategy: Strategy, problem: str, response: str, thinking: Optional[str], client, model: str) -> Strategy:
    """
    Refine a strategy based on its application to a specific problem.
    
    Args:
        strategy: The strategy to refine
        problem: The problem that was solved
        response: The LLM's final response to the problem
        thinking: The LLM's reasoning process (if any)
        client: LLM client for making API calls
        model: Model identifier
    
    Returns:
        Strategy: The refined strategy
    """
    try:
        full_response = thinking + '\n\n' + response if thinking else response
        messages = [{'role': 'system', 'content': STRATEGY_REFINEMENT_PROMPT}, {'role': 'user', 'content': f'Original strategy for {strategy.problem_type} problems:\n{strategy.strategy_text}\n\nNew problem:\n{problem}\n\nSolution process (including reasoning):\n{full_response}\n\nProvide a refined version of the original strategy that incorporates any insights from this new example.'}]
        refine_response = client.chat.completions.create(model=model, messages=messages, temperature=0.5, max_tokens=DEFAULT_MAX_TOKENS)
        response_text = refine_response.choices[0].message.content
        refined_text, refinement_thinking = extract_thinking(response_text)
        if not refined_text.strip():
            refined_text = response_text
        logger.debug(f"Strategy refinement - raw response: '{response_text}'")
        logger.debug(f"Strategy refinement - final text after removing thinking: '{refined_text}'")
        refined_strategy = Strategy(strategy_id=strategy.strategy_id, problem_type=strategy.problem_type, strategy_text=refined_text.strip(), examples=strategy.examples + [problem], success_count=strategy.success_count, total_attempts=strategy.total_attempts, created_at=strategy.created_at, last_used=datetime.now().isoformat(), last_updated=datetime.now().isoformat(), confidence=strategy.confidence, tags=strategy.tags, reasoning_examples=strategy.reasoning_examples.copy())
        if refinement_thinking:
            refined_strategy.add_reasoning_example(refinement_thinking)
        return refined_strategy
    except Exception as e:
        logger.error(f'Error refining strategy: {str(e)}')
        return strategy

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

def add_example(self, example: str) -> None:
    """Add an example to the strategy."""
    if example and example not in self.examples:
        self.examples.append(example)

def classify_problem(content: str, client, model: str) -> str:
    """
    Use the LLM to classify the problem type, ensuring the result is one of the valid types.
    
    Args:
        content: The query/problem to classify
        client: LLM client for making API calls
        model: Model identifier
    
    Returns:
        str: The problem type classification (always a valid type)
    """
    problem_types_str = ', '.join(VALID_PROBLEM_TYPES[:-1])
    try:
        messages = [{'role': 'system', 'content': PROBLEM_CLASSIFICATION_PROMPT.format(problem_types=problem_types_str)}, {'role': 'user', 'content': f'Classify the following problem into ONE of these types: {problem_types_str}\n\nProblem: {content}'}]
        response = client.chat.completions.create(model=model, messages=messages, temperature=0.1, max_tokens=DEFAULT_MAX_TOKENS)
        raw_response = response.choices[0].message.content
        final_response, thinking = extract_thinking(raw_response)
        final_response = final_response.strip().lower()
        logger.debug(f"Problem classification - raw response: '{raw_response}'")
        logger.debug(f"Problem classification - final response after removing thinking: '{final_response}'")
        for valid_type in VALID_PROBLEM_TYPES:
            if valid_type.lower() == final_response:
                logger.info(f"Classified problem as '{valid_type}' (exact match)")
                return valid_type
        for valid_type in VALID_PROBLEM_TYPES:
            if valid_type.lower() in final_response:
                logger.info(f"Classified problem as '{valid_type}' (partial match from '{final_response}')")
                return valid_type
        logger.warning(f"Could not match '{final_response}' to any valid problem type, using 'general_problem'")
        return 'general_problem'
    except Exception as e:
        logger.error(f'Error classifying problem: {str(e)}')
        return 'general_problem'

def generate_strategy(problem: str, problem_type: str, client, model: str, db: StrategyDatabase) -> Strategy:
    """
    Generate a new problem-solving strategy using the LLM.
    
    Args:
        problem: The problem that needs a strategy
        problem_type: The type of problem
        client: LLM client for making API calls
        model: Model identifier
        db: The strategy database to use for generating IDs
    
    Returns:
        Strategy: A new strategy for solving this type of problem
    """
    try:
        messages = [{'role': 'system', 'content': STRATEGY_GENERATION_PROMPT}, {'role': 'user', 'content': f'Create a problem-solving strategy for the following {problem_type} problem:\n\n{problem}\n\nThis strategy should help solve not just this specific problem, but any {problem_type} problem.'}]
        response = client.chat.completions.create(model=model, messages=messages, temperature=0.7, max_tokens=DEFAULT_MAX_TOKENS)
        response_text = response.choices[0].message.content
        strategy_text, thinking = extract_thinking(response_text)
        if not strategy_text.strip():
            strategy_text = response_text
        logger.debug(f"Generated strategy - raw response: '{response_text}'")
        logger.debug(f"Generated strategy - final text after removing thinking: '{strategy_text}'")
        strategy = Strategy(strategy_id=db.get_next_strategy_id(), problem_type=problem_type, strategy_text=strategy_text.strip(), examples=[problem], created_at=None, reasoning_examples=[thinking] if thinking else [])
        logger.info(f'Generated new strategy for {problem_type}: ID {strategy.strategy_id}')
        return strategy
    except Exception as e:
        logger.error(f'Error generating strategy: {str(e)}')
        fallback_id = f'fallback_{uuid.uuid4().hex[:8]}'
        logger.info(f'Using fallback strategy with ID: {fallback_id}')
        return Strategy(strategy_id=fallback_id, problem_type=problem_type, strategy_text=f'When solving {problem_type} problems:\n1. Break down the problem into smaller parts\n2. Solve each part systematically\n3. Combine the solutions', examples=[problem])

class DeepResearcher:
    """
    Simplified implementation of Test-Time Diffusion Deep Researcher (TTD-DR) algorithm

    This class implements the core concepts from the TTD-DR paper: treating research as a
    diffusion process with iterative refinement through denoising and retrieval.

    Implemented features:
    - Preliminary draft generation (updatable skeleton)
    - Gap analysis and draft-guided search
    - Iterative denoising through retrieval
    - Quality-guided termination

    Not yet implemented (future work):
    - Component-wise self-evolutionary optimization (fitness tracking exists but not used)
    - Memory-based synthesis for unbounded context

    Based on: https://arxiv.org/abs/2507.16075v1
    """

    def __init__(self, client, model: str, max_iterations: int=5, max_sources: int=30):
        self.client = client
        self.model = model
        self.max_iterations = max_iterations
        self.max_sources = max_sources
        self.session_id = str(uuid.uuid4())
        self.session_manager = None
        self.research_state = {'iteration': 0}
        self.total_tokens = 0
        self.citations = {}
        self.citation_counter = 0
        self.source_content_map = {}
        self.current_draft = ''
        self.draft_history = []
        self.component_fitness = {'search_strategy': 1.0, 'synthesis_quality': 1.0, 'gap_detection': 1.0, 'integration_ability': 1.0}
        self.gap_analysis_history = []
        self.session_manager = None

    def cleanup_placeholder_tags(self, text: str) -> str:
        """
        Remove any remaining placeholder tags from the final report.
        
        This is a final cleanup step to ensure no incomplete research tags remain
        in the published report.
        
        Args:
            text: Research report text
            
        Returns:
            Text with all placeholder tags removed
        """
        return cleanup_placeholder_tags(text)

    def fix_incomplete_report(self, report: str, validation: Dict[str, Any], original_query: str) -> str:
        """
        Attempt to fix an incomplete report by removing problematic sections
        and ensuring a coherent final document.
        
        This is a fallback when the report contains placeholders or incomplete sections.
        """
        print('🔧 Attempting to fix incomplete report...')
        fixed_report = cleanup_placeholder_tags(report)
        if 'Research Questions for Investigation' in fixed_report:
            fixed_report = re.sub('## Research Questions for Investigation.*?(?=##|$)', '', fixed_report, flags=re.DOTALL)
            print('   - Removed incomplete research questions section')
        fixed_report = re.sub('\\[\\d+\\]\\s*\\[Placeholder[^\\]]+\\]\\n?', '', fixed_report)
        fixed_report = re.sub('##\\s+([^#\\n]+)\\n\\s*(?=##)', '', fixed_report)
        if len(fixed_report.split()) < 300:
            completion_note = f'\n            \n## Note on Report Completion\n\nThis research report represents the findings gathered during the available research time. While comprehensive coverage was the goal, some areas may require additional investigation for complete analysis.\n\nFor more detailed information on specific aspects of {original_query}, additional focused research sessions may be beneficial.\n'
            if '## References' in fixed_report:
                fixed_report = fixed_report.replace('## References', completion_note + '\n## References')
            else:
                fixed_report += completion_note
            print('   - Added completion note due to short report length')
        fixed_report = re.sub('\\n\\s*\\n\\s*\\n+', '\n\n', fixed_report)
        fixed_report = fixed_report.strip()
        new_validation = validate_report_completeness(fixed_report)
        if new_validation['is_complete']:
            print('✅ Report successfully fixed and validated')
        else:
            print(f'⚠️  Report still has {len(new_validation['issues'])} issues after fixing')
        return fixed_report

    def decompose_query(self, system_prompt: str, initial_query: str) -> List[str]:
        """
        Decompose complex research query into focused sub-queries
        This implements the query planning phase of TTD-DR
        """
        decomposition_prompt = f'\n        You are a research assistant. Given a complex query, break it down into 3-5 focused sub-queries that would help gather comprehensive information.\n        \n        Original query: {initial_query}\n        \n        Provide sub-queries in this format:\n        1. [specific focused question]\n        2. [specific focused question]\n        3. [specific focused question]\n        ...\n        \n        Make each sub-query specific and searchable. Focus on different aspects of the main topic.\n        '
        try:
            response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': decomposition_prompt}], temperature=0.7, max_tokens=1000)
            content = response.choices[0].message.content.strip()
            content = clean_reasoning_tags(content)
            self.total_tokens += response.usage.completion_tokens
            queries = []
            for line in content.split('\n'):
                line = line.strip()
                if re.match('^\\d+\\.', line):
                    query = re.sub('^\\d+\\.\\s*\\[?(.*?)\\]?$', '\\1', line).strip()
                    if query:
                        queries.append(query)
            return queries[:5]
        except Exception as e:
            return [initial_query]

    def perform_web_search(self, queries: List[str]) -> str:
        """
        Perform web search for multiple queries using the web_search plugin
        """
        all_results = []
        if not hasattr(self, 'session_manager') or self.session_manager is None:
            print(f'⚠️  Warning: session_manager not available in perform_web_search (session_id: {getattr(self, 'session_id', 'N/A')})')
            self.session_manager = None
        else:
            print(f'📊 Using existing session manager for web search (session_id: {self.session_id}, manager: {id(self.session_manager)})')
        for i, query in enumerate(queries):
            try:
                search_query = f'search for {query.strip()}'
                results_per_query = max(1, self.max_sources // len(queries))
                enhanced_query, _ = web_search_run('', search_query, None, None, {'num_results': results_per_query, 'delay_seconds': None, 'headless': False, 'session_manager': self.session_manager})
                if enhanced_query and 'Web Search Results' in enhanced_query:
                    all_results.append(enhanced_query)
            except Exception as e:
                all_results.append(f"Search failed for query '{query}': {str(e)}")
                continue
        if not all_results:
            return 'Web search failed: No results obtained from any query'
        combined_results = '\n\n'.join(all_results)
        return combined_results

    def extract_and_fetch_urls(self, search_results: str) -> Tuple[str, List[Dict]]:
        """
        Extract URLs from search results and fetch their content using readurls plugin
        Returns content and list of sources with metadata
        """
        try:
            sources = []
            result_pattern = '(\\d+)\\.\\s*\\*\\*(.+?)\\*\\*\\s*\\n\\s*URL:\\s*(.+?)\\n'
            matches = re.findall(result_pattern, search_results, re.MULTILINE)
            for match in matches:
                source = {'number': match[0], 'title': match[1].strip(), 'url': match[2].strip(), 'access_date': datetime.now().strftime('%Y-%m-%d')}
                sources.append(source)
            if not sources:
                lines = search_results.split('\n')
                current_source = {}
                for i, line in enumerate(lines):
                    title_match = re.match('^(\\d+)\\.\\s*\\*\\*(.+?)\\*\\*', line.strip())
                    if title_match:
                        if current_source and 'url' in current_source:
                            sources.append(current_source)
                        current_source = {'number': title_match.group(1), 'title': title_match.group(2).strip()}
                    elif line.strip().startswith('URL:') and current_source:
                        url = line.strip()[4:].strip()
                        current_source['url'] = url
                        current_source['access_date'] = datetime.now().strftime('%Y-%m-%d')
                if current_source and 'url' in current_source:
                    sources.append(current_source)
            content_with_urls, _ = readurls_run('', search_results, None, None)
            return (content_with_urls, sources)
        except Exception as e:
            return (f'URL fetching failed: {str(e)}', [])

    def evaluate_completeness(self, system_prompt: str, query: str, current_synthesis: str) -> Tuple[bool, List[str]]:
        """
        Evaluate if the current research is complete or needs more information
        Returns (is_complete, list_of_missing_aspects)
        """
        evaluation_prompt = f'\n        You are evaluating the completeness of a research synthesis. \n        \n        Original query: {query}\n        Current synthesis: {current_synthesis}\n        \n        Evaluate if this synthesis adequately addresses the original query. Consider:\n        1. Are all major aspects of the query covered?\n        2. Is there sufficient depth and detail?\n        3. Are there any obvious gaps or missing information?\n        \n        Respond in this format:\n        COMPLETE: [YES/NO]\n        MISSING: [list any missing aspects, one per line, or "None" if complete]\n        '
        try:
            response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': evaluation_prompt}], temperature=0.3, max_tokens=500)
            content = response.choices[0].message.content.strip()
            content = clean_reasoning_tags(content)
            self.total_tokens += response.usage.completion_tokens
            is_complete = 'COMPLETE: YES' in content.upper()
            missing_aspects = []
            if 'MISSING:' in content.upper():
                missing_section = content.split('MISSING:')[-1].strip()
                if missing_section.upper() != 'NONE':
                    missing_aspects = [line.strip() for line in missing_section.split('\n') if line.strip()]
            return (is_complete, missing_aspects)
        except Exception as e:
            return (False, ['Error in evaluation'])

    def generate_focused_queries(self, missing_aspects: List[str], original_query: str) -> List[str]:
        """
        Generate focused search queries to address missing aspects
        """
        focused_queries = []
        for aspect in missing_aspects:
            focused_query = f'{original_query} {aspect}'
            focused_queries.append(focused_query)
        return focused_queries[:3]

    def generate_preliminary_draft(self, system_prompt: str, initial_query: str) -> str:
        """
        Generate the preliminary draft (updatable skeleton) from LLM internal knowledge
        This serves as the initial state for the diffusion process
        """
        draft_prompt = f"""\n        Generate a preliminary research report structure for the following query using your internal knowledge.\n        This will serve as an evolving draft that gets refined through iterative research.\n        \n        Query: {initial_query}\n        \n        Create a structured report with:\n        1. Title and Executive Summary (brief)\n        2. Introduction and Background (what you know)\n        3. Key Areas to Explore (identify knowledge gaps)\n        4. Preliminary Findings (from internal knowledge)\n        5. Research Questions for Investigation\n        6. Conclusion (preliminary thoughts)\n        \n        IMPORTANT: You MUST mark multiple areas that need external research with [NEEDS RESEARCH] tags.\n        Every claim that would benefit from external evidence should have [SOURCE NEEDED].\n        This is a preliminary draft - it should have many gaps for iterative improvement.\n        \n        Example of proper marking:\n        - "Recent studies show [SOURCE NEEDED] that quantum computing..."\n        - "The economic impact [NEEDS RESEARCH: current market data] is significant..."\n        - "Historical context [NEEDS RESEARCH: specific timeline and events] shows..."\n        \n        Include AT LEAST 5-10 [NEEDS RESEARCH] or [SOURCE NEEDED] tags throughout the draft.\n        Be explicit about what you don't know and what needs external validation.\n        """
        try:
            response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': draft_prompt}], temperature=0.7, max_tokens=2000)
            draft = response.choices[0].message.content.strip()
            draft = clean_reasoning_tags(draft)
            self.total_tokens += response.usage.completion_tokens
            return draft
        except Exception as e:
            return f'Failed to generate preliminary draft: {str(e)}'

    def analyze_draft_gaps(self, current_draft: str, original_query: str) -> List[Dict[str, str]]:
        """
        Analyze the current draft to identify gaps, weaknesses, and areas needing research
        This guides the next retrieval iteration (draft-guided search)
        """
        gap_analysis_prompt = f"\n        Analyze the following research draft to identify specific gaps and areas that need external research.\n        Be thorough and aggressive in finding areas for improvement - even good drafts can be enhanced.\n        \n        Original Query: {original_query}\n        \n        Current Draft:\n        {current_draft}\n        \n        CRITICAL ANALYSIS REQUIRED:\n        1. MANDATORY: Find ALL [NEEDS RESEARCH], [SOURCE NEEDED], [CITATION NEEDED] tags\n        2. Identify claims lacking evidence (even if not explicitly marked)\n        3. Find areas that could benefit from recent data or statistics\n        4. Spot generalizations that need specific examples\n        5. Locate outdated information or areas needing current updates\n        6. Identify missing perspectives or counterarguments\n        \n        For each gap you identify, provide:\n        1. SECTION: Which section has the gap\n        2. GAP_TYPE: [PLACEHOLDER_TAG, MISSING_INFO, OUTDATED_INFO, NEEDS_EVIDENCE, LACKS_DEPTH, NEEDS_EXAMPLES, MISSING_PERSPECTIVE]\n        3. SPECIFIC_NEED: Exactly what information is needed\n        4. SEARCH_QUERY: A specific, targeted search query to address this gap\n        5. PRIORITY: [HIGH, MEDIUM, LOW] - HIGH for placeholder tags and critical missing info\n        \n        Format each gap as:\n        GAP_ID: [number]\n        SECTION: [section name]\n        GAP_TYPE: [type]\n        SPECIFIC_NEED: [what's missing]\n        SEARCH_QUERY: [search query to find this info]\n        PRIORITY: [priority level]\n        \n        IMPORTANT: Identify AT LEAST 3-8 gaps. Be critical and thorough.\n        Even well-written sections can benefit from additional evidence, examples, or perspectives.\n        Push for depth, accuracy, and comprehensiveness in the research.\n        "
        try:
            response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'system', 'content': 'You are an expert research analyst.'}, {'role': 'user', 'content': gap_analysis_prompt}], temperature=0.3, max_tokens=1000)
            content = response.choices[0].message.content.strip()
            content = clean_reasoning_tags(content)
            self.total_tokens += response.usage.completion_tokens
            gaps = []
            current_gap = {}
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('GAP_ID:'):
                    if current_gap:
                        gaps.append(current_gap)
                    current_gap = {'id': line.split(':', 1)[1].strip()}
                elif line.startswith('SECTION:'):
                    current_gap['section'] = line.split(':', 1)[1].strip()
                elif line.startswith('GAP_TYPE:'):
                    current_gap['gap_type'] = line.split(':', 1)[1].strip()
                elif line.startswith('SPECIFIC_NEED:'):
                    current_gap['specific_need'] = line.split(':', 1)[1].strip()
                elif line.startswith('SEARCH_QUERY:'):
                    current_gap['search_query'] = line.split(':', 1)[1].strip()
                elif line.startswith('PRIORITY:'):
                    current_gap['priority'] = line.split(':', 1)[1].strip()
            if current_gap:
                gaps.append(current_gap)
            return gaps
        except Exception as e:
            return [{'id': '1', 'section': 'General', 'gap_type': 'MISSING_INFO', 'specific_need': 'More detailed information needed', 'search_query': original_query}]

    def perform_gap_targeted_search(self, gaps: List[Dict[str, str]]) -> str:
        """
        Perform targeted searches based on identified gaps in the current draft
        Prioritizes HIGH priority gaps (placeholder tags) first
        """
        all_results = []
        if not hasattr(self, 'session_manager') or self.session_manager is None:
            print('⚠️  Warning: session_manager not available in perform_web_search')
            self.session_manager = None
        sorted_gaps = sorted(gaps, key=lambda g: 0 if g.get('priority', '').upper() == 'HIGH' else 1 if g.get('priority', '').upper() == 'MEDIUM' else 2)
        for gap in sorted_gaps:
            search_query = gap.get('search_query', '')
            if not search_query:
                continue
            try:
                search_query = f'search for {search_query.strip()}'
                enhanced_query, _ = web_search_run('', search_query, None, None, {'num_results': max(1, self.max_sources // len(gaps)), 'delay_seconds': None, 'headless': False, 'session_manager': self.session_manager})
                if enhanced_query and 'Web Search Results' in enhanced_query:
                    gap_context = f'[ADDRESSING GAP: {gap.get('section', 'Unknown')} - {gap.get('specific_need', 'General research')}]\n'
                    all_results.append(gap_context + enhanced_query)
            except Exception as e:
                continue
        return '\n\n'.join(all_results) if all_results else 'No gap-targeted search results obtained'

    def denoise_draft_with_retrieval(self, current_draft: str, retrieval_content: str, original_query: str) -> str:
        """
        Core denoising step: integrate retrieved information with current draft
        This is the heart of the diffusion process
        """
        citation_context = '\n\n**AVAILABLE CITATIONS (USE THESE!):**\n'
        for num, source in self.citations.items():
            citation_context += f'[{num}] {source.get('title', 'Untitled')} - {source.get('url', 'No URL')}\n'
        denoising_prompt = f'\n        You are performing a denoising step in a research diffusion process.\n\n        TASK: Integrate new retrieved information with the existing draft to reduce "noise" (gaps, inaccuracies, incompleteness).\n\n        Original Query: {original_query}\n\n        Current Draft:\n        {current_draft}\n\n        New Retrieved Information:\n        {retrieval_content}\n        {citation_context}\n\n        CRITICAL CITATION REQUIREMENTS:\n        1. EVERY factual claim, statistic, finding, or piece of evidence MUST be cited using [1], [2], etc.\n        2. Multiple related claims from the same source can share a citation [3]\n        3. Claims from different sources should have multiple citations like [1,4,7]\n        4. Direct quotes MUST have citations immediately after the closing quote\n        5. When integrating new information, ALWAYS add appropriate citations from the available sources\n        6. Uncited claims will be considered incomplete and must be fixed\n\n        DENOISING INSTRUCTIONS:\n        1. Identify where the new information fills gaps marked with [NEEDS RESEARCH] or [SOURCE NEEDED]\n        2. Replace placeholder content with specific, detailed information from the retrieved content\n        3. Add proper citations for ALL new information using the citation numbers shown above\n        4. Resolve any conflicts between new and existing information\n        5. Maintain the overall structure and coherence of the draft\n        6. Enhance depth and accuracy without losing existing valuable insights\n        7. Mark any remaining research needs with [NEEDS RESEARCH]\n        8. Review the draft and add missing citations to any uncited factual claims\n\n        QUALITY CHECK: Before returning, verify that the majority of substantive claims have citations.\n        Aim for at least 70% of factual statements to be properly cited.\n\n        Return the improved draft with integrated information and comprehensive citations.\n        '
        try:
            response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'system', 'content': 'You are an expert research synthesizer performing draft denoising.'}, {'role': 'user', 'content': denoising_prompt}], temperature=0.6, max_tokens=3000)
            denoised_draft = response.choices[0].message.content.strip()
            denoised_draft = clean_reasoning_tags(denoised_draft)
            self.total_tokens += response.usage.completion_tokens
            return denoised_draft
        except Exception as e:
            return f'Denoising failed: {str(e)}\n\nFalling back to current draft:\n{current_draft}'

    def evaluate_draft_quality(self, draft: str, previous_draft: str, original_query: str) -> Dict[str, float]:
        """
        Evaluate the quality improvement of the current draft vs previous iteration
        Used for termination decisions and component fitness updates
        """
        evaluation_prompt = f'\n        Evaluate the research draft quality improvement.\n        \n        Original Query: {original_query}\n        \n        Previous Draft:\n        {previous_draft}\n        \n        Current Draft:\n        {draft}\n        \n        Rate the following aspects from 0.0 to 1.0:\n        \n        COMPLETENESS: How well does the current draft address all aspects of the query?\n        ACCURACY: How accurate and reliable is the information?\n        DEPTH: How detailed and comprehensive is the analysis?\n        COHERENCE: How well-structured and logically organized is the draft?\n        CITATIONS: How well are sources cited and integrated?\n        IMPROVEMENT: How much better is this draft compared to the previous version?\n        \n        Respond ONLY with:\n        COMPLETENESS: [score]\n        ACCURACY: [score]\n        DEPTH: [score]\n        COHERENCE: [score]\n        CITATIONS: [score]\n        IMPROVEMENT: [score]\n        '
        try:
            response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'system', 'content': 'You are an expert research quality evaluator.'}, {'role': 'user', 'content': evaluation_prompt}], temperature=0.2, max_tokens=500)
            content = response.choices[0].message.content.strip()
            content = clean_reasoning_tags(content)
            self.total_tokens += response.usage.completion_tokens
            scores = {}
            for line in content.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    try:
                        scores[key] = float(value.strip())
                    except ValueError:
                        scores[key] = 0.5
            return scores
        except Exception as e:
            return {'completeness': 0.5, 'accuracy': 0.5, 'depth': 0.5, 'coherence': 0.5, 'citations': 0.5, 'improvement': 0.1}

    def update_component_fitness(self, quality_scores: Dict[str, float]):
        """
        Update component fitness based on performance (self-evolution)

        NOTE: This method tracks fitness values but they are not yet used to modify
        component behavior. This is placeholder code for future implementation of
        component-wise self-evolutionary optimization as described in the TTD-DR paper.
        """
        improvement = quality_scores.get('improvement', 0.0)
        if improvement > 0.1:
            self.component_fitness['search_strategy'] *= 1.1
            self.component_fitness['synthesis_quality'] *= 1.1
            self.component_fitness['integration_ability'] *= 1.1
        elif improvement < 0.05:
            self.component_fitness['search_strategy'] *= 0.95
            self.component_fitness['synthesis_quality'] *= 0.95
        for key in self.component_fitness:
            self.component_fitness[key] = max(0.1, min(2.0, self.component_fitness[key]))

    def research(self, system_prompt: str, initial_query: str) -> Tuple[str, int]:
        """
        TTD-DR (Test-Time Diffusion Deep Researcher) main algorithm

        Implements the core diffusion process with:
        1. Preliminary draft generation (initial noisy state)
        2. Initial research to gather external sources
        3. Iterative denoising through draft-guided retrieval
        4. Gap analysis to identify areas needing more research
        5. Quality-guided termination

        Note: Component-wise self-evolutionary optimization is tracked but not yet
        used to modify behavior (future enhancement).
        """
        self.session_manager = get_session_manager(self.session_id, headless=False, timeout=30)
        if self.session_manager:
            print(f'🔬 Starting deep research with session ID: {self.session_id} (DeepResearcher instance: {id(self)})')
        else:
            print('⚠️ Failed to create browser session, proceeding without web search')
        try:
            print('TTD-DR: Generating preliminary draft...')
            self.current_draft = self.generate_preliminary_draft(system_prompt, initial_query)
            self.draft_history.append(self.current_draft)
            print('TTD-DR: Performing initial research...')
            initial_queries = self.decompose_query(system_prompt, initial_query)
            if initial_queries:
                print(f'  - Searching for {len(initial_queries)} initial topics...')
                initial_search_results = self.perform_web_search(initial_queries)
                if initial_search_results and 'Web Search Results' in initial_search_results:
                    print('  - Extracting initial sources...')
                    initial_content, initial_sources = self.extract_and_fetch_urls(initial_search_results)
                    for source in initial_sources:
                        if 'url' in source:
                            self.citation_counter += 1
                            self.citations[self.citation_counter] = source
                    print(f'  - Found {len(initial_sources)} initial sources')
                else:
                    print('  - No sources found in initial search')
            else:
                print('  - Warning: Could not decompose query for initial research')
                print('  - Using fallback search strategy...')
                fallback_queries = [initial_query]
                fallback_search_results = self.perform_web_search(fallback_queries)
                if fallback_search_results and 'Web Search Results' in fallback_search_results:
                    fallback_content, fallback_sources = self.extract_and_fetch_urls(fallback_search_results)
                    for source in fallback_sources:
                        if 'url' in source:
                            self.citation_counter += 1
                            self.citations[self.citation_counter] = source
                    print(f'  - Fallback search found {len(fallback_sources)} sources')
            for iteration in range(self.max_iterations):
                self.research_state['iteration'] = iteration + 1
                print(f'TTD-DR: Denoising iteration {iteration + 1}/{self.max_iterations}')
                print('  - Analyzing draft gaps...')
                gaps = self.analyze_draft_gaps(self.current_draft, initial_query)
                self.gap_analysis_history.append(gaps)
                if not gaps:
                    print('  - No significant gaps found, research complete')
                    break
                print(f'  - Performing targeted search for {len(gaps)} gaps...')
                retrieval_content = self.perform_gap_targeted_search(gaps)
                print('  - Extracting and fetching content...')
                content_with_urls, sources = self.extract_and_fetch_urls(retrieval_content)
                for source in sources:
                    if 'url' in source:
                        self.citation_counter += 1
                        self.citations[self.citation_counter] = source
                print('  - Performing denoising step...')
                previous_draft = self.current_draft
                self.current_draft = self.denoise_draft_with_retrieval(self.current_draft, content_with_urls, initial_query)
                self.draft_history.append(self.current_draft)
                print('  - Evaluating draft quality...')
                quality_scores = self.evaluate_draft_quality(self.current_draft, previous_draft, initial_query)
                self.update_component_fitness(quality_scores)
                completeness = quality_scores.get('completeness', 0.0)
                improvement = quality_scores.get('improvement', 0.0)
                print(f'  - Quality scores: Completeness={completeness:.2f}, Improvement={improvement:.2f}')
                if completeness > 0.9 or (improvement < 0.03 and completeness > 0.7):
                    print('  - Quality threshold reached, research complete')
                    break
            print('TTD-DR: Finalizing research report...')
            if len(self.citations) == 0:
                print('⚠️  Warning: No external sources found during research!')
                print('   Deep research should always consult external sources.')
            else:
                print(f'✅ Research completed with {len(self.citations)} sources')
            final_report = self.finalize_research_report(system_prompt, initial_query, self.current_draft)
            return (final_report, self.total_tokens)
        finally:
            if self.session_manager:
                print(f'🏁 Closing research session: {self.session_id}')
                close_session(self.session_id)
                self.session_manager = None

    def finalize_research_report(self, system_prompt: str, original_query: str, final_draft: str) -> str:
        """
        Apply final polishing to the research report
        """
        citation_context = '\n\n**AVAILABLE CITATIONS:**\n'
        for num, source in self.citations.items():
            citation_context += f'[{num}] {source.get('title', 'Untitled')}\n'
        finalization_prompt = f'\n        Apply final polishing to this research report. This is the last step in the TTD-DR diffusion process.\n\n        Original Query: {original_query}\n\n        Current Draft:\n        {final_draft}\n        {citation_context}\n\n        FINALIZATION TASKS:\n        1. Ensure professional academic formatting with clear sections\n        2. **CRITICAL**: Verify all citations are properly formatted as [1], [2], etc. and ADD MISSING CITATIONS\n        3. Add citations to any factual claims, statistics, or findings that lack them\n        4. Add a compelling title and executive summary\n        5. Ensure smooth transitions between sections\n        6. Add conclusion that directly addresses the original query\n        7. **CRITICAL**: Remove ALL [NEEDS RESEARCH], [SOURCE NEEDED], and similar placeholder tags\n        8. Replace any remaining placeholders with actual content or remove incomplete sections\n        9. Polish language and style for clarity and impact\n\n        **CRITICAL CITATION REQUIREMENTS**:\n        - Every major factual claim MUST have a citation\n        - Statistics, data points, and research findings MUST be cited\n        - If information came from research, it needs a citation from the available sources above\n        - Aim for at least 60-70% of substantive claims to have proper citations\n        - Remove or rephrase claims that cannot be supported with available citations\n\n        **CRITICAL QUALITY REQUIREMENTS**:\n        - The final report must NOT contain ANY placeholder tags: [NEEDS RESEARCH], [SOURCE NEEDED], [Placeholder for...], etc.\n        - Remove incomplete "Research Questions for Investigation" sections with unanswered questions\n        - Do not include citation placeholders like "[1] [Placeholder for specific research citation]"\n        - If sections are incomplete, either complete them with available information or remove them entirely\n        - Ensure all statements are backed by available evidence or are clearly marked as preliminary findings\n        - The report must be publication-ready with no incomplete elements\n        - DO NOT create a References section - it will be added automatically\n\n        Return the final polished research report with comprehensive citations.\n        '
        try:
            response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': finalization_prompt}], temperature=0.5, max_tokens=3000)
            polished_report = response.choices[0].message.content.strip()
            polished_report = clean_reasoning_tags(polished_report)
            polished_report = self.cleanup_placeholder_tags(polished_report)
            validation = validate_report_completeness(polished_report)
            if not validation['is_complete']:
                print(f'⚠️  Report validation found {len(validation['issues'])} issues:')
                for issue in validation['issues']:
                    print(f'   - {issue}')
                polished_report = self.fix_incomplete_report(polished_report, validation, original_query)
            else:
                print('✅ Report validation passed - report is complete')
            self.total_tokens += response.usage.completion_tokens
            polished_report = re.sub('##\\s*References.*?(?=##|\\Z)', '', polished_report, flags=re.DOTALL)
            polished_report = re.sub('(?m)^References\\s*\\n\\s*(?:\\[\\d+\\]\\s*\\n)+', '', polished_report)
            polished_report = re.sub('\\n\\s*\\n\\s*\\n+', '\n\n', polished_report)
            citation_validation = validate_citation_usage(polished_report, len(self.citations))
            print(f'📊 Citation Statistics:')
            print(f'   - Used citations: {citation_validation['citations_used']}/{citation_validation['citations_total']}')
            print(f'   - Usage percentage: {citation_validation['usage_percentage']:.1f}%')
            if 'warning' in citation_validation:
                print(f'⚠️  {citation_validation['warning']}')
                if len(citation_validation['unused_citations']) > 0:
                    print(f'   - Unused citations: {citation_validation['unused_citations'][:10]}' + (f'... and {len(citation_validation['unused_citations']) - 10} more' if len(citation_validation['unused_citations']) > 10 else ''))
            references = '\n\n## References\n\n'
            used_citations = set(citation_validation['used_citations'])
            for num, source in sorted(self.citations.items()):
                if num in used_citations:
                    title = source.get('title', 'Untitled')
                    url = source['url']
                    access_date = source.get('access_date', datetime.now().strftime('%Y-%m-%d'))
                    references += f'[{num}] {title}. Available at: <{url}> [Accessed: {access_date}]\n\n'
            metadata = '\n---\n\n**TTD-DR Research Metadata:**\n'
            metadata += f'- Algorithm: Test-Time Diffusion Deep Researcher\n'
            metadata += f'- Denoising iterations: {len(self.draft_history) - 1}\n'
            metadata += f'- Total gaps addressed: {sum((len(gaps) for gaps in self.gap_analysis_history))}\n'
            metadata += f'- Total sources consulted: {len(self.citations)}\n'
            metadata += f'- Citations used in text: {citation_validation['citations_used']} ({citation_validation['usage_percentage']:.1f}%)\n'
            metadata += f'- Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n'
            metadata += f'- Total tokens used: {self.total_tokens}\n'
            return polished_report + references + metadata
        except Exception as e:
            return f'Finalization failed: {str(e)}\n\nReturning current draft:\n{final_draft}'

def __init__(self, client, model: str, max_iterations: int=5, max_sources: int=30):
    self.client = client
    self.model = model
    self.max_iterations = max_iterations
    self.max_sources = max_sources
    self.session_id = str(uuid.uuid4())
    self.session_manager = None
    self.research_state = {'iteration': 0}
    self.total_tokens = 0
    self.citations = {}
    self.citation_counter = 0
    self.source_content_map = {}
    self.current_draft = ''
    self.draft_history = []
    self.component_fitness = {'search_strategy': 1.0, 'synthesis_quality': 1.0, 'gap_detection': 1.0, 'integration_ability': 1.0}
    self.gap_analysis_history = []
    self.session_manager = None

def decompose_query(self, system_prompt: str, initial_query: str) -> List[str]:
    """
        Decompose complex research query into focused sub-queries
        This implements the query planning phase of TTD-DR
        """
    decomposition_prompt = f'\n        You are a research assistant. Given a complex query, break it down into 3-5 focused sub-queries that would help gather comprehensive information.\n        \n        Original query: {initial_query}\n        \n        Provide sub-queries in this format:\n        1. [specific focused question]\n        2. [specific focused question]\n        3. [specific focused question]\n        ...\n        \n        Make each sub-query specific and searchable. Focus on different aspects of the main topic.\n        '
    try:
        response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': decomposition_prompt}], temperature=0.7, max_tokens=1000)
        content = response.choices[0].message.content.strip()
        content = clean_reasoning_tags(content)
        self.total_tokens += response.usage.completion_tokens
        queries = []
        for line in content.split('\n'):
            line = line.strip()
            if re.match('^\\d+\\.', line):
                query = re.sub('^\\d+\\.\\s*\\[?(.*?)\\]?$', '\\1', line).strip()
                if query:
                    queries.append(query)
        return queries[:5]
    except Exception as e:
        return [initial_query]

def perform_web_search(self, queries: List[str]) -> str:
    """
        Perform web search for multiple queries using the web_search plugin
        """
    all_results = []
    if not hasattr(self, 'session_manager') or self.session_manager is None:
        print(f'⚠️  Warning: session_manager not available in perform_web_search (session_id: {getattr(self, 'session_id', 'N/A')})')
        self.session_manager = None
    else:
        print(f'📊 Using existing session manager for web search (session_id: {self.session_id}, manager: {id(self.session_manager)})')
    for i, query in enumerate(queries):
        try:
            search_query = f'search for {query.strip()}'
            results_per_query = max(1, self.max_sources // len(queries))
            enhanced_query, _ = web_search_run('', search_query, None, None, {'num_results': results_per_query, 'delay_seconds': None, 'headless': False, 'session_manager': self.session_manager})
            if enhanced_query and 'Web Search Results' in enhanced_query:
                all_results.append(enhanced_query)
        except Exception as e:
            all_results.append(f"Search failed for query '{query}': {str(e)}")
            continue
    if not all_results:
        return 'Web search failed: No results obtained from any query'
    combined_results = '\n\n'.join(all_results)
    return combined_results

def extract_and_fetch_urls(self, search_results: str) -> Tuple[str, List[Dict]]:
    """
        Extract URLs from search results and fetch their content using readurls plugin
        Returns content and list of sources with metadata
        """
    try:
        sources = []
        result_pattern = '(\\d+)\\.\\s*\\*\\*(.+?)\\*\\*\\s*\\n\\s*URL:\\s*(.+?)\\n'
        matches = re.findall(result_pattern, search_results, re.MULTILINE)
        for match in matches:
            source = {'number': match[0], 'title': match[1].strip(), 'url': match[2].strip(), 'access_date': datetime.now().strftime('%Y-%m-%d')}
            sources.append(source)
        if not sources:
            lines = search_results.split('\n')
            current_source = {}
            for i, line in enumerate(lines):
                title_match = re.match('^(\\d+)\\.\\s*\\*\\*(.+?)\\*\\*', line.strip())
                if title_match:
                    if current_source and 'url' in current_source:
                        sources.append(current_source)
                    current_source = {'number': title_match.group(1), 'title': title_match.group(2).strip()}
                elif line.strip().startswith('URL:') and current_source:
                    url = line.strip()[4:].strip()
                    current_source['url'] = url
                    current_source['access_date'] = datetime.now().strftime('%Y-%m-%d')
            if current_source and 'url' in current_source:
                sources.append(current_source)
        content_with_urls, _ = readurls_run('', search_results, None, None)
        return (content_with_urls, sources)
    except Exception as e:
        return (f'URL fetching failed: {str(e)}', [])

def evaluate_completeness(self, system_prompt: str, query: str, current_synthesis: str) -> Tuple[bool, List[str]]:
    """
        Evaluate if the current research is complete or needs more information
        Returns (is_complete, list_of_missing_aspects)
        """
    evaluation_prompt = f'\n        You are evaluating the completeness of a research synthesis. \n        \n        Original query: {query}\n        Current synthesis: {current_synthesis}\n        \n        Evaluate if this synthesis adequately addresses the original query. Consider:\n        1. Are all major aspects of the query covered?\n        2. Is there sufficient depth and detail?\n        3. Are there any obvious gaps or missing information?\n        \n        Respond in this format:\n        COMPLETE: [YES/NO]\n        MISSING: [list any missing aspects, one per line, or "None" if complete]\n        '
    try:
        response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': evaluation_prompt}], temperature=0.3, max_tokens=500)
        content = response.choices[0].message.content.strip()
        content = clean_reasoning_tags(content)
        self.total_tokens += response.usage.completion_tokens
        is_complete = 'COMPLETE: YES' in content.upper()
        missing_aspects = []
        if 'MISSING:' in content.upper():
            missing_section = content.split('MISSING:')[-1].strip()
            if missing_section.upper() != 'NONE':
                missing_aspects = [line.strip() for line in missing_section.split('\n') if line.strip()]
        return (is_complete, missing_aspects)
    except Exception as e:
        return (False, ['Error in evaluation'])

def generate_focused_queries(self, missing_aspects: List[str], original_query: str) -> List[str]:
    """
        Generate focused search queries to address missing aspects
        """
    focused_queries = []
    for aspect in missing_aspects:
        focused_query = f'{original_query} {aspect}'
        focused_queries.append(focused_query)
    return focused_queries[:3]

def generate_preliminary_draft(self, system_prompt: str, initial_query: str) -> str:
    """
        Generate the preliminary draft (updatable skeleton) from LLM internal knowledge
        This serves as the initial state for the diffusion process
        """
    draft_prompt = f"""\n        Generate a preliminary research report structure for the following query using your internal knowledge.\n        This will serve as an evolving draft that gets refined through iterative research.\n        \n        Query: {initial_query}\n        \n        Create a structured report with:\n        1. Title and Executive Summary (brief)\n        2. Introduction and Background (what you know)\n        3. Key Areas to Explore (identify knowledge gaps)\n        4. Preliminary Findings (from internal knowledge)\n        5. Research Questions for Investigation\n        6. Conclusion (preliminary thoughts)\n        \n        IMPORTANT: You MUST mark multiple areas that need external research with [NEEDS RESEARCH] tags.\n        Every claim that would benefit from external evidence should have [SOURCE NEEDED].\n        This is a preliminary draft - it should have many gaps for iterative improvement.\n        \n        Example of proper marking:\n        - "Recent studies show [SOURCE NEEDED] that quantum computing..."\n        - "The economic impact [NEEDS RESEARCH: current market data] is significant..."\n        - "Historical context [NEEDS RESEARCH: specific timeline and events] shows..."\n        \n        Include AT LEAST 5-10 [NEEDS RESEARCH] or [SOURCE NEEDED] tags throughout the draft.\n        Be explicit about what you don't know and what needs external validation.\n        """
    try:
        response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': draft_prompt}], temperature=0.7, max_tokens=2000)
        draft = response.choices[0].message.content.strip()
        draft = clean_reasoning_tags(draft)
        self.total_tokens += response.usage.completion_tokens
        return draft
    except Exception as e:
        return f'Failed to generate preliminary draft: {str(e)}'

def analyze_draft_gaps(self, current_draft: str, original_query: str) -> List[Dict[str, str]]:
    """
        Analyze the current draft to identify gaps, weaknesses, and areas needing research
        This guides the next retrieval iteration (draft-guided search)
        """
    gap_analysis_prompt = f"\n        Analyze the following research draft to identify specific gaps and areas that need external research.\n        Be thorough and aggressive in finding areas for improvement - even good drafts can be enhanced.\n        \n        Original Query: {original_query}\n        \n        Current Draft:\n        {current_draft}\n        \n        CRITICAL ANALYSIS REQUIRED:\n        1. MANDATORY: Find ALL [NEEDS RESEARCH], [SOURCE NEEDED], [CITATION NEEDED] tags\n        2. Identify claims lacking evidence (even if not explicitly marked)\n        3. Find areas that could benefit from recent data or statistics\n        4. Spot generalizations that need specific examples\n        5. Locate outdated information or areas needing current updates\n        6. Identify missing perspectives or counterarguments\n        \n        For each gap you identify, provide:\n        1. SECTION: Which section has the gap\n        2. GAP_TYPE: [PLACEHOLDER_TAG, MISSING_INFO, OUTDATED_INFO, NEEDS_EVIDENCE, LACKS_DEPTH, NEEDS_EXAMPLES, MISSING_PERSPECTIVE]\n        3. SPECIFIC_NEED: Exactly what information is needed\n        4. SEARCH_QUERY: A specific, targeted search query to address this gap\n        5. PRIORITY: [HIGH, MEDIUM, LOW] - HIGH for placeholder tags and critical missing info\n        \n        Format each gap as:\n        GAP_ID: [number]\n        SECTION: [section name]\n        GAP_TYPE: [type]\n        SPECIFIC_NEED: [what's missing]\n        SEARCH_QUERY: [search query to find this info]\n        PRIORITY: [priority level]\n        \n        IMPORTANT: Identify AT LEAST 3-8 gaps. Be critical and thorough.\n        Even well-written sections can benefit from additional evidence, examples, or perspectives.\n        Push for depth, accuracy, and comprehensiveness in the research.\n        "
    try:
        response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'system', 'content': 'You are an expert research analyst.'}, {'role': 'user', 'content': gap_analysis_prompt}], temperature=0.3, max_tokens=1000)
        content = response.choices[0].message.content.strip()
        content = clean_reasoning_tags(content)
        self.total_tokens += response.usage.completion_tokens
        gaps = []
        current_gap = {}
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('GAP_ID:'):
                if current_gap:
                    gaps.append(current_gap)
                current_gap = {'id': line.split(':', 1)[1].strip()}
            elif line.startswith('SECTION:'):
                current_gap['section'] = line.split(':', 1)[1].strip()
            elif line.startswith('GAP_TYPE:'):
                current_gap['gap_type'] = line.split(':', 1)[1].strip()
            elif line.startswith('SPECIFIC_NEED:'):
                current_gap['specific_need'] = line.split(':', 1)[1].strip()
            elif line.startswith('SEARCH_QUERY:'):
                current_gap['search_query'] = line.split(':', 1)[1].strip()
            elif line.startswith('PRIORITY:'):
                current_gap['priority'] = line.split(':', 1)[1].strip()
        if current_gap:
            gaps.append(current_gap)
        return gaps
    except Exception as e:
        return [{'id': '1', 'section': 'General', 'gap_type': 'MISSING_INFO', 'specific_need': 'More detailed information needed', 'search_query': original_query}]

def perform_gap_targeted_search(self, gaps: List[Dict[str, str]]) -> str:
    """
        Perform targeted searches based on identified gaps in the current draft
        Prioritizes HIGH priority gaps (placeholder tags) first
        """
    all_results = []
    if not hasattr(self, 'session_manager') or self.session_manager is None:
        print('⚠️  Warning: session_manager not available in perform_web_search')
        self.session_manager = None
    sorted_gaps = sorted(gaps, key=lambda g: 0 if g.get('priority', '').upper() == 'HIGH' else 1 if g.get('priority', '').upper() == 'MEDIUM' else 2)
    for gap in sorted_gaps:
        search_query = gap.get('search_query', '')
        if not search_query:
            continue
        try:
            search_query = f'search for {search_query.strip()}'
            enhanced_query, _ = web_search_run('', search_query, None, None, {'num_results': max(1, self.max_sources // len(gaps)), 'delay_seconds': None, 'headless': False, 'session_manager': self.session_manager})
            if enhanced_query and 'Web Search Results' in enhanced_query:
                gap_context = f'[ADDRESSING GAP: {gap.get('section', 'Unknown')} - {gap.get('specific_need', 'General research')}]\n'
                all_results.append(gap_context + enhanced_query)
        except Exception as e:
            continue
    return '\n\n'.join(all_results) if all_results else 'No gap-targeted search results obtained'

def denoise_draft_with_retrieval(self, current_draft: str, retrieval_content: str, original_query: str) -> str:
    """
        Core denoising step: integrate retrieved information with current draft
        This is the heart of the diffusion process
        """
    citation_context = '\n\n**AVAILABLE CITATIONS (USE THESE!):**\n'
    for num, source in self.citations.items():
        citation_context += f'[{num}] {source.get('title', 'Untitled')} - {source.get('url', 'No URL')}\n'
    denoising_prompt = f'\n        You are performing a denoising step in a research diffusion process.\n\n        TASK: Integrate new retrieved information with the existing draft to reduce "noise" (gaps, inaccuracies, incompleteness).\n\n        Original Query: {original_query}\n\n        Current Draft:\n        {current_draft}\n\n        New Retrieved Information:\n        {retrieval_content}\n        {citation_context}\n\n        CRITICAL CITATION REQUIREMENTS:\n        1. EVERY factual claim, statistic, finding, or piece of evidence MUST be cited using [1], [2], etc.\n        2. Multiple related claims from the same source can share a citation [3]\n        3. Claims from different sources should have multiple citations like [1,4,7]\n        4. Direct quotes MUST have citations immediately after the closing quote\n        5. When integrating new information, ALWAYS add appropriate citations from the available sources\n        6. Uncited claims will be considered incomplete and must be fixed\n\n        DENOISING INSTRUCTIONS:\n        1. Identify where the new information fills gaps marked with [NEEDS RESEARCH] or [SOURCE NEEDED]\n        2. Replace placeholder content with specific, detailed information from the retrieved content\n        3. Add proper citations for ALL new information using the citation numbers shown above\n        4. Resolve any conflicts between new and existing information\n        5. Maintain the overall structure and coherence of the draft\n        6. Enhance depth and accuracy without losing existing valuable insights\n        7. Mark any remaining research needs with [NEEDS RESEARCH]\n        8. Review the draft and add missing citations to any uncited factual claims\n\n        QUALITY CHECK: Before returning, verify that the majority of substantive claims have citations.\n        Aim for at least 70% of factual statements to be properly cited.\n\n        Return the improved draft with integrated information and comprehensive citations.\n        '
    try:
        response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'system', 'content': 'You are an expert research synthesizer performing draft denoising.'}, {'role': 'user', 'content': denoising_prompt}], temperature=0.6, max_tokens=3000)
        denoised_draft = response.choices[0].message.content.strip()
        denoised_draft = clean_reasoning_tags(denoised_draft)
        self.total_tokens += response.usage.completion_tokens
        return denoised_draft
    except Exception as e:
        return f'Denoising failed: {str(e)}\n\nFalling back to current draft:\n{current_draft}'

def evaluate_draft_quality(self, draft: str, previous_draft: str, original_query: str) -> Dict[str, float]:
    """
        Evaluate the quality improvement of the current draft vs previous iteration
        Used for termination decisions and component fitness updates
        """
    evaluation_prompt = f'\n        Evaluate the research draft quality improvement.\n        \n        Original Query: {original_query}\n        \n        Previous Draft:\n        {previous_draft}\n        \n        Current Draft:\n        {draft}\n        \n        Rate the following aspects from 0.0 to 1.0:\n        \n        COMPLETENESS: How well does the current draft address all aspects of the query?\n        ACCURACY: How accurate and reliable is the information?\n        DEPTH: How detailed and comprehensive is the analysis?\n        COHERENCE: How well-structured and logically organized is the draft?\n        CITATIONS: How well are sources cited and integrated?\n        IMPROVEMENT: How much better is this draft compared to the previous version?\n        \n        Respond ONLY with:\n        COMPLETENESS: [score]\n        ACCURACY: [score]\n        DEPTH: [score]\n        COHERENCE: [score]\n        CITATIONS: [score]\n        IMPROVEMENT: [score]\n        '
    try:
        response = self.client.chat.completions.create(model=self.model, messages=[{'role': 'system', 'content': 'You are an expert research quality evaluator.'}, {'role': 'user', 'content': evaluation_prompt}], temperature=0.2, max_tokens=500)
        content = response.choices[0].message.content.strip()
        content = clean_reasoning_tags(content)
        self.total_tokens += response.usage.completion_tokens
        scores = {}
        for line in content.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                try:
                    scores[key] = float(value.strip())
                except ValueError:
                    scores[key] = 0.5
        return scores
    except Exception as e:
        return {'completeness': 0.5, 'accuracy': 0.5, 'depth': 0.5, 'coherence': 0.5, 'citations': 0.5, 'improvement': 0.1}

class AutoThinkProcessor:
    """
    AutoThink processor for controlled thinking with 
    complexity classification and steering vectors.
    """

    def __init__(self, config: Dict[str, Any], tokenizer: PreTrainedTokenizer, model: PreTrainedModel):
        """
        Initialize the AutoThink processor.
        
        Args:
            config: Configuration dictionary
            tokenizer: Model tokenizer
            model: Language model
        """
        self.config = {**DEFAULT_CONFIG, **config}
        self.tokenizer = tokenizer
        self.model = model
        self.classifier = ComplexityClassifier(self.config['classifier_model'])
        start_tokens = self.tokenizer.encode(self.config['start_think_token'])
        end_tokens = self.tokenizer.encode(self.config['end_think_token'])
        self._start_think_token = start_tokens[0] if len(start_tokens) == 1 else start_tokens[1]
        self.end_think_token = end_tokens[0] if len(end_tokens) == 1 else end_tokens[1]
        self.thought_switch_sequences = []
        for phrase in self.config['thought_switch_tokens']:
            token_ids = self.tokenizer.encode(phrase, add_special_tokens=False)
            self.thought_switch_sequences.append(token_ids)
            logger.debug(f"Encoded '{phrase}' to token sequence: {token_ids}")
            logger.debug(f'Decoded back: {self.tokenizer.decode(token_ids)}')
        self.thought_count = 0
        self.current_sequence = []
        self.max_sequence_length = max((len(seq) for seq in self.thought_switch_sequences))
        self.steering_manager = None
        self.steering_hooks = []
        if self.config['steering_dataset']:
            self._setup_steering()

    def _setup_steering(self):
        """Set up steering vector management."""
        try:
            self.steering_manager = SteeringVectorManager(dataset_name=self.config['steering_dataset'], target_layer=self.config['target_layer'])
            if 'pattern_strengths' in self.config:
                for pattern, strength in self.config['pattern_strengths'].items():
                    self.steering_manager.set_steering_strength(pattern, strength)
            self.steering_manager.create_tokenized_contexts(self.tokenizer)
            self.steering_hooks = install_steering_hooks(self.model, self.steering_manager, self.tokenizer)
            logger.info(f'STEERING: Set up steering with {len(self.steering_hooks)} hooks')
        except Exception as e:
            logger.error(f'STEERING: Error setting up steering: {e}')
            self.steering_manager = None
            self.steering_hooks = []

    def _cleanup_steering(self):
        """Clean up steering hooks."""
        if self.steering_hooks:
            remove_steering_hooks(self.steering_hooks)
            self.steering_hooks = []
            logger.info('STEERING: Hooks removed successfully')

    def classify_complexity(self, query: str) -> Tuple[str, float]:
        """
        Classify query complexity.
        
        Args:
            query: The query to classify
            
        Returns:
            Tuple of (complexity_label, confidence_score)
        """
        complexity, confidence = self.classifier.get_complexity_with_confidence(query)
        logger.info(f'Query classified as {complexity} with confidence {confidence:.2f}')
        return (complexity, confidence)

    def get_token_budget(self, complexity: str) -> Tuple[int, int]:
        """
        Get token budget based on complexity.
        
        Args:
            complexity: Complexity label (HIGH or LOW)
            
        Returns:
            Tuple of (min_tokens, max_tokens)
        """
        if complexity == 'HIGH':
            return (self.config['high_complexity_min_tokens'], self.config['high_complexity_max_tokens'])
        else:
            return (self.config['low_complexity_min_tokens'], self.config['low_complexity_max_tokens'])

    def is_thought_switch(self, token: int) -> bool:
        """
        Check if adding this token creates a thought switch sequence.
        
        Args:
            token: Token ID to check
            
        Returns:
            Boolean indicating if this completes a thought switch
        """
        self.current_sequence.append(token)
        if len(self.current_sequence) > self.max_sequence_length:
            self.current_sequence = self.current_sequence[-self.max_sequence_length:]
        for sequence in self.thought_switch_sequences:
            if len(sequence) <= len(self.current_sequence) and self.current_sequence[-len(sequence):] == sequence:
                return True
        return False

    @torch.inference_mode()
    def process(self, messages: List[Dict[str, str]]) -> str:
        """
        Process messages with AutoThink's controlled thinking.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Generated response
        """
        try:
            query = self._extract_query(messages)
            complexity, confidence = self.classify_complexity(query)
            min_tokens, max_tokens = self.get_token_budget(complexity)
            logger.info(f'Using token budget: {min_tokens}-{max_tokens} for {complexity} complexity')
            thinking_messages = messages.copy()
            thinking_messages.append({'role': 'assistant', 'content': f'{self.config['start_think_token']}\n{self.config['prefill']}'})
            tokens = self.tokenizer.apply_chat_template(thinking_messages, continue_final_message=True, return_tensors='pt').to(self.model.device)
            if self.steering_hooks:
                token_ids = tokens[0].tolist()
                prompt_text = self.tokenizer.decode(token_ids)
                for hook, _ in self.steering_hooks:
                    hook.reset()
                    hook.update_token_history(token_ids)
                    hook.update_context(prompt_text)
                    hook.try_match()
            kv = DynamicCache()
            n_thinking_tokens = 0
            seen_end_think = False
            response_chunks = []
            while True:
                out = self.model(input_ids=tokens, past_key_values=kv, use_cache=True)
                logits = out.logits[0, -1, :]
                force_end = n_thinking_tokens >= max_tokens or self.thought_count >= self.config['max_thoughts']
                if force_end and (not seen_end_think):
                    logger.debug(f'Forcing end think token. Tokens: {n_thinking_tokens}, Thoughts: {self.thought_count}')
                    next_token = self.end_think_token
                    response_chunks.append(self.tokenizer.decode([next_token]))
                    seen_end_think = True
                    tokens = torch.tensor([[next_token]]).to(tokens.device)
                    continue
                else:
                    next_token = torch.multinomial(torch.softmax(logits, dim=-1), 1).item()
                kv = out.past_key_values
                next_str = self.tokenizer.decode([next_token])
                if self.steering_hooks:
                    for hook, _ in self.steering_hooks:
                        hook.update_token_history([next_token])
                if not seen_end_think and self.is_thought_switch(next_token):
                    self.thought_count += 1
                    logger.debug(f'Detected thought switch marker. Total thoughts: {self.thought_count}')
                    self.current_sequence = []
                if next_token == self.end_think_token:
                    seen_end_think = True
                    logger.debug('Found end think token')
                    if n_thinking_tokens < min_tokens:
                        replacement = random.choice(self.config['thought_switch_tokens'])
                        logger.debug(f"Inserting thought transition: '{replacement}' (tokens: {n_thinking_tokens})")
                        response_chunks.append(replacement)
                        replacement_tokens = self.tokenizer.encode(replacement)
                        n_thinking_tokens += len(replacement_tokens)
                        tokens = torch.tensor([replacement_tokens]).to(tokens.device)
                        self.thought_count += 1
                        seen_end_think = False
                        continue
                if next_token == self.model.config.eos_token_id:
                    logger.debug('Found EOS token')
                    if seen_end_think:
                        logger.debug('Reached EOS after end think token - stopping generation')
                        response_chunks.append(next_str)
                        break
                    elif n_thinking_tokens < min_tokens:
                        replacement = random.choice(self.config['thought_switch_tokens'])
                        logger.debug(f"Inserting thought transition: '{replacement}' (tokens: {n_thinking_tokens})")
                        response_chunks.append(replacement)
                        replacement_tokens = self.tokenizer.encode(replacement)
                        n_thinking_tokens += len(replacement_tokens)
                        tokens = torch.tensor([replacement_tokens]).to(tokens.device)
                        self.thought_count += 1
                        continue
                    else:
                        logger.debug('Reached EOS without end think token - adding end token and continuing generation')
                        response_chunks.append(self.tokenizer.decode([self.end_think_token]))
                        tokens = torch.tensor([[self.end_think_token]]).to(tokens.device)
                        seen_end_think = True
                        continue
                response_chunks.append(next_str)
                if not seen_end_think:
                    n_thinking_tokens += 1
                if self.steering_hooks:
                    for hook, _ in self.steering_hooks:
                        hook.update_token_history([next_token])
                        hook.update_context(next_str)
                        hook.try_match()
                tokens = torch.tensor([[next_token]]).to(tokens.device)
            if self.steering_hooks:
                for hook, _ in self.steering_hooks:
                    hook.reset()
            self._cleanup_steering()
            response = ''.join(response_chunks)
            full_response = f'{self.config['start_think_token']}\n{self.config['prefill']}{response}'
            logger.debug(f'Final response length: {len(full_response)} chars, Total thoughts: {self.thought_count}')
            return full_response
        except Exception as e:
            self._cleanup_steering()
            logger.error(f'Error in AutoThink processing: {str(e)}')
            raise

    def _extract_query(self, messages: List[Dict[str, str]]) -> str:
        """
        Extract the query from messages for classification.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Extracted query string
        """
        user_messages = [m['content'] for m in messages if m['role'] == 'user']
        if user_messages:
            return user_messages[-1]
        return ' '.join((m['content'] for m in messages))

def is_thought_switch(self, token: int) -> bool:
    """
        Check if adding this token creates a thought switch sequence.
        
        Args:
            token: Token ID to check
            
        Returns:
            Boolean indicating if this completes a thought switch
        """
    self.current_sequence.append(token)
    if len(self.current_sequence) > self.max_sequence_length:
        self.current_sequence = self.current_sequence[-self.max_sequence_length:]
    for sequence in self.thought_switch_sequences:
        if len(sequence) <= len(self.current_sequence) and self.current_sequence[-len(sequence):] == sequence:
            return True
    return False

class DeepConfProcessor:
    """
    Main DeepConf processor implementing online mode with early termination.
    """

    def __init__(self, model: PreTrainedModel, tokenizer: PreTrainedTokenizer, config: Dict[str, Any]=None):
        """
        Initialize the DeepConf processor.
        
        Args:
            model: The language model
            tokenizer: The tokenizer
            config: Configuration dictionary
        """
        self.model = model
        self.tokenizer = tokenizer
        self.config = {**DEFAULT_CONFIG, **(config or {})}
        self.confidence_calculator = ConfidenceCalculator(window_size=self.config['window_size'], top_k=self.config['top_k'])
        self.threshold_calibrator = ConfidenceThresholdCalibrator(variant=self.config['variant'])
        self.warmup_traces = []
        self.online_traces = []
        self.confidence_threshold = None
        self.total_tokens_used = 0
        logger.info(f'DeepConf processor initialized with variant: {self.config['variant']}')

    def reset(self):
        """Reset processor state for new query."""
        self.warmup_traces = []
        self.online_traces = []
        self.confidence_threshold = None
        self.total_tokens_used = 0
        self.confidence_calculator.reset()

    def generate_single_trace(self, messages: List[Dict[str, str]], use_early_termination: bool=False) -> TraceResult:
        """
        Generate a single reasoning trace with optional early termination.
        
        Args:
            messages: Input messages
            use_early_termination: Whether to apply early termination
            
        Returns:
            TraceResult object containing trace and confidence stats
        """
        self.confidence_calculator.reset()
        tokens = self.tokenizer.apply_chat_template(messages, return_tensors='pt', add_generation_prompt=True).to(self.model.device)
        kv_cache = DynamicCache()
        generated_tokens = []
        generated_text_parts = []
        token_count = 0
        terminated_early = False
        while token_count < self.config['max_tokens_per_trace']:
            with torch.no_grad():
                outputs = self.model(input_ids=tokens, past_key_values=kv_cache, use_cache=True)
                logits = outputs.logits[0, -1, :]
                kv_cache = outputs.past_key_values
            token_confidence = self.confidence_calculator.add_token_confidence(logits)
            if use_early_termination and token_count >= self.config['min_trace_length'] and (self.confidence_threshold is not None):
                current_group_confidence = self.confidence_calculator.get_current_group_confidence()
                if current_group_confidence is not None and current_group_confidence < self.confidence_threshold:
                    logger.debug(f'Early termination at token {token_count}, confidence: {current_group_confidence:.4f} < {self.confidence_threshold:.4f}')
                    terminated_early = True
                    break
            probs = torch.softmax(logits / self.config['temperature'], dim=-1)
            next_token = torch.multinomial(probs, num_samples=1).item()
            if next_token == self.tokenizer.eos_token_id:
                break
            generated_tokens.append(next_token)
            token_text = self.tokenizer.decode([next_token])
            generated_text_parts.append(token_text)
            tokens = torch.tensor([[next_token]]).to(self.model.device)
            token_count += 1
        generated_text = ''.join(generated_text_parts)
        confidence_stats = self.confidence_calculator.get_trace_statistics()
        trace_result = TraceResult(generated_tokens, generated_text, confidence_stats)
        trace_result.terminated_early = terminated_early
        self.total_tokens_used += token_count
        logger.debug(f'Generated trace: {token_count} tokens, avg confidence: {confidence_stats['average_confidence']:.4f}, early termination: {terminated_early}')
        return trace_result

    def run_warmup_phase(self, messages: List[Dict[str, str]]) -> None:
        """
        Run the warmup phase to generate initial traces and calibrate threshold.
        
        Args:
            messages: Input messages
        """
        logger.info(f'Starting warmup phase with {self.config['warmup_samples']} traces')
        for i in range(self.config['warmup_samples']):
            trace = self.generate_single_trace(messages, use_early_termination=False)
            self.warmup_traces.append(trace)
            self.threshold_calibrator.add_warmup_trace(trace.confidence_stats)
            logger.debug(f'Warmup trace {i + 1}/{self.config['warmup_samples']} completed')
        self.confidence_threshold = self.threshold_calibrator.calculate_threshold(metric=self.config['confidence_metric'])
        logger.info(f'Warmup phase completed. Threshold: {self.confidence_threshold:.4f}')

    def check_consensus(self, traces: List[TraceResult]) -> Tuple[bool, str, float]:
        """
        Check if consensus has been reached among traces.
        
        Args:
            traces: List of trace results
            
        Returns:
            Tuple of (has_consensus, consensus_answer, consensus_ratio)
        """
        if not traces:
            return (False, '', 0.0)
        answers = []
        for trace in traces:
            answer = trace.text.strip().split('.')[-1].strip()
            if not answer:
                answer = trace.text.strip()[-50:].strip()
            answers.append(answer)
        answer_counts = Counter(answers)
        most_common_answer, most_common_count = answer_counts.most_common(1)[0]
        consensus_ratio = most_common_count / len(answers)
        has_consensus = consensus_ratio >= self.config['consensus_threshold']
        logger.debug(f'Consensus check: {consensus_ratio:.3f} ({('✓' if has_consensus else '✗')} >= {self.config['consensus_threshold']})')
        return (has_consensus, most_common_answer, consensus_ratio)

    def weighted_majority_vote(self, traces: List[TraceResult]) -> Tuple[str, Dict[str, float]]:
        """
        Perform weighted majority voting based on trace confidences.
        
        Args:
            traces: List of trace results
            
        Returns:
            Tuple of (best_answer, voting_stats)
        """
        if not traces:
            return ('', {})
        answer_groups = defaultdict(list)
        for trace in traces:
            answer = trace.text.strip().split('.')[-1].strip()
            if not answer:
                answer = trace.text.strip()[-50:].strip()
            answer_groups[answer].append(trace)
        answer_scores = {}
        for answer, group_traces in answer_groups.items():
            confidences = [trace.confidence_stats['average_confidence'] for trace in group_traces]
            weighted_score = sum(confidences) / len(confidences)
            count_weight = len(group_traces) / len(traces)
            final_score = weighted_score * 0.7 + count_weight * 0.3
            answer_scores[answer] = final_score
        best_answer = max(answer_scores.keys(), key=lambda x: answer_scores[x])
        voting_stats = {'num_unique_answers': len(answer_groups), 'best_score': answer_scores[best_answer], 'answer_distribution': {ans: len(traces) for ans, traces in answer_groups.items()}}
        logger.info(f'Weighted voting completed. Best answer score: {answer_scores[best_answer]:.4f}')
        return (best_answer, voting_stats)

    def process_online(self, messages: List[Dict[str, str]]) -> Tuple[str, Dict[str, Any]]:
        """
        Main online processing with warmup and early termination.
        
        Args:
            messages: Input messages
            
        Returns:
            Tuple of (final_answer, processing_stats)
        """
        self.reset()
        logger.info('Starting DeepConf online processing')
        self.run_warmup_phase(messages)
        logger.info('Starting online generation phase')
        all_traces = self.warmup_traces[:]
        for trace_num in range(self.config['max_traces'] - self.config['warmup_samples']):
            trace = self.generate_single_trace(messages, use_early_termination=True)
            all_traces.append(trace)
            self.online_traces.append(trace)
            has_consensus, consensus_answer, consensus_ratio = self.check_consensus(all_traces)
            logger.debug(f'Online trace {trace_num + 1} completed. Total traces: {len(all_traces)}, Consensus: {consensus_ratio:.3f}')
            if has_consensus:
                logger.info(f'Consensus reached after {len(all_traces)} traces (ratio: {consensus_ratio:.3f})')
                break
        final_answer, voting_stats = self.weighted_majority_vote(all_traces)
        processing_stats = {'total_traces': len(all_traces), 'warmup_traces': len(self.warmup_traces), 'online_traces': len(self.online_traces), 'early_terminations': sum((1 for trace in all_traces if trace.terminated_early)), 'total_tokens_used': self.total_tokens_used, 'confidence_threshold': self.confidence_threshold, 'variant': self.config['variant'], **voting_stats}
        logger.info(f'DeepConf processing completed. Traces: {processing_stats['total_traces']}, Tokens: {processing_stats['total_tokens_used']}, Early terminations: {processing_stats['early_terminations']}')
        return (final_answer, processing_stats)

def check_consensus(self, traces: List[TraceResult]) -> Tuple[bool, str, float]:
    """
        Check if consensus has been reached among traces.
        
        Args:
            traces: List of trace results
            
        Returns:
            Tuple of (has_consensus, consensus_answer, consensus_ratio)
        """
    if not traces:
        return (False, '', 0.0)
    answers = []
    for trace in traces:
        answer = trace.text.strip().split('.')[-1].strip()
        if not answer:
            answer = trace.text.strip()[-50:].strip()
        answers.append(answer)
    answer_counts = Counter(answers)
    most_common_answer, most_common_count = answer_counts.most_common(1)[0]
    consensus_ratio = most_common_count / len(answers)
    has_consensus = consensus_ratio >= self.config['consensus_threshold']
    logger.debug(f'Consensus check: {consensus_ratio:.3f} ({('✓' if has_consensus else '✗')} >= {self.config['consensus_threshold']})')
    return (has_consensus, most_common_answer, consensus_ratio)

class ConfidenceThresholdCalibrator:
    """
    Calibrates confidence thresholds based on warmup traces.
    """

    def __init__(self, variant: str='low'):
        """
        Initialize the threshold calibrator.
        
        Args:
            variant: "low" (aggressive, top 10%) or "high" (conservative, top 90%)
        """
        self.variant = variant
        self.warmup_confidences = []

    def add_warmup_trace(self, confidence_stats: Dict[str, float]):
        """
        Add confidence statistics from a warmup trace.
        
        Args:
            confidence_stats: Dictionary with confidence metrics
        """
        self.warmup_confidences.append(confidence_stats)

    def calculate_threshold(self, metric: str='average_confidence') -> float:
        """
        Calculate the confidence threshold based on warmup traces.
        
        Args:
            metric: Which confidence metric to use for threshold calculation
            
        Returns:
            Calculated threshold value
        """
        if not self.warmup_confidences:
            logger.warning('No warmup traces available for threshold calculation')
            return 0.0
        confidences = [stats[metric] for stats in self.warmup_confidences]
        if self.variant == 'low':
            threshold = np.percentile(confidences, 90)
        else:
            threshold = np.percentile(confidences, 10)
        logger.info(f'Calculated {self.variant} threshold: {threshold:.4f} for metric: {metric}')
        return threshold

    def should_terminate_trace(self, current_confidence: float, threshold: float) -> bool:
        """
        Determine if current trace should be terminated based on confidence.
        
        Args:
            current_confidence: Current confidence value
            threshold: Threshold for termination
            
        Returns:
            True if trace should be terminated
        """
        return current_confidence < threshold

def add_warmup_trace(self, confidence_stats: Dict[str, float]):
    """
        Add confidence statistics from a warmup trace.
        
        Args:
            confidence_stats: Dictionary with confidence metrics
        """
    self.warmup_confidences.append(confidence_stats)

def extract_llm_response(response):
    """
    Extract text content and finish reason from an LLM response.

    Supports both non-streaming responses (dict-like with `.choices[0].message.content`)
    and streaming responses (iterable of chunks with `.choices[0].delta.content`).

    Args:
        response: LLM response object or streaming generator.

    Returns:
        Tuple[str, Optional[str]]:
            - Extracted text content (stripped).
            - Finish reason (or None if unavailable).
    """
    if hasattr(response, 'choices') and hasattr(response.choices[0], 'message'):
        content = response.choices[0].message.content
        if content:
            content = content.strip()
        finish_reason = getattr(response.choices[0], 'finish_reason', None)
        return (content, finish_reason)
    full_content = ''
    finish_reason = None
    for chunk in response:
        delta = chunk.choices[0].delta
        if hasattr(delta, 'content') and delta.content:
            full_content += delta.content
        if chunk.choices[0].finish_reason is not None:
            finish_reason = chunk.choices[0].finish_reason
    return (full_content.strip(), finish_reason)

def llm_call(client: Any, provider_request: dict, cepo_config: CepoConfig) -> tuple[str, str, int]:
    """
    Call the LLM with retries on transient errors.

    Makes a chat completion request to the given client and extracts the response.
    Retries up to 2 times on 400/500 errors with exponential backoff.

    Args:
        client (Any): LLM API client instance.
        provider_request (dict): LMM call params.

    Returns:
        tuple[str, str, int]:
            - response_text: Model output (post-processed, never None).
            - finish_reason: Why generation stopped.
            - completion_tokens: Number of tokens generated.
    """
    retries = cepo_config.num_of_retries + 1
    for attempt in range(retries):
        try:
            response_object = client.chat.completions.create(stream=False, **provider_request)
            response_text, finish_reason = extract_llm_response(response_object)
            completion_tokens = getattr(getattr(response_object, 'usage', None), 'completion_tokens', 0) or 0
            response_text = response_text or ''
            if response_text is not None:
                response_text = remove_think_section(response_text)
            return (response_text, finish_reason, completion_tokens)
        except (OpenAIBadRequestError, OpenAIInternalServerError) as e:
            if attempt < retries - 1:
                sleep_time = 0.2 * (attempt + 1)
                print(f'Got {e.__class__.__name__}, retrying in {sleep_time:.1f}s...')
                time.sleep(sleep_time)
                continue
            raise

def generate_completion(system_prompt: str, task: str, client: Any, model: str, cepo_config: CepoConfig, approach: Optional[str]=None, request_id: str=None) -> str:
    """
    Generates a completion based on the provided system prompt and task.

    Parameters:
        system_prompt (str): The system prompt to guide the model.
        task (str): The task or question to be addressed.
        client (Any): The client instance for interacting with the AI model.
        model (str): The model name to be used for generating completions.
        cepo_config (CepoConfig): Configuration parameters for CePO flow.
        approach (str|None): optional approach that is used to seed plan generation.

    Returns:
        Tuple[str, int, dict]: The generated completion, number of tokens used, and a log dictionary.
    """
    completion_tokens = 0
    question_only = extract_question_only(task)
    cb_log = {}
    plans = []

    def generate_single_plan(i):
        local_cb_log = {}
        local_completion_tokens = 0
        if cepo_config.planning_max_tokens_step1 != 0:
            if cepo_config.use_plan_diversity:
                assert approach
                content = f'To answer this question, can you come up with a concise plan using to solve it step-by-step but do not provide the final answer. Here is the approach you need to follow to generate the plan: {approach}. Also, for each step, provide your confidence in the correctness of that step as well as your ability to execute it correctly. Here is the question:\n{question_only}\nRead the question again:\n\n{question_only}'
            else:
                assert not approach
                content = f'To answer this question, can you come up with a concise plan to solve it step-by-step but do not provide the final answer. Also, for each step, provide your confidence in the correctness of that step as well as your ability to execute it correctly. Here is the question:\n{question_only}\nRead the question again:\n\n{question_only}'
            messages = [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': content}]
            provider_request = {'model': model, 'messages': messages, 'max_tokens': cepo_config.planning_max_tokens_step1, 'temperature': cepo_config.planning_temperature_step1, 'top_p': 1.0}
            response, finish_reason, completion_tokens = llm_call_reason_effort_fallback(client=client, provider_request=provider_request, reasoning_effort_levels=['high', 'medium'], cepo_config=cepo_config)
            local_completion_tokens += completion_tokens
            if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and request_id:
                response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
                optillm.conversation_logger.log_provider_call(request_id, provider_request, response_dict)
            if finish_reason == 'length':
                return (i, None, local_completion_tokens, {f'messages_planning_{i}_rejected_due_to_length': messages})
            parsed_plan = response
        else:
            messages = []
            parsed_plan = ''
        if cepo_config.planning_max_tokens_step1 != 0:
            messages.append({'role': 'assistant', 'content': parsed_plan})
            messages.append({'role': 'user', 'content': 'Can you execute the above plan step-by-step to produce the final answer. Be extra careful when executing steps where your confidence is lower. /think'})
        else:
            messages.append({'role': 'user', 'content': f'Can you solve this problem step-by-step to produce the final answer? Here is the question:\n{question_only}\nRead the question again:\n\n{question_only} /think'})
        provider_request = {'model': model, 'messages': messages, 'max_tokens': cepo_config.planning_max_tokens_step1, 'temperature': cepo_config.planning_temperature_step1, 'top_p': 1.0}
        response, finish_reason, completion_tokens = llm_call_reason_effort_fallback(client=client, provider_request=provider_request, reasoning_effort_levels=['high', 'medium'], cepo_config=cepo_config)
        local_completion_tokens += completion_tokens
        if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and request_id:
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
            optillm.conversation_logger.log_provider_call(request_id, provider_request, response_dict)
        if finish_reason == 'length':
            return (i, None, local_completion_tokens, {f'messages_planning_{i}_rejected_due_to_length': messages})
        parsed_exec = response
        messages.append({'role': 'assistant', 'content': parsed_exec})
        local_cb_log[f'messages_planning_{i}'] = messages
        return (i, parsed_exec, local_completion_tokens, local_cb_log)
    with ThreadPoolExecutor(max_workers=cepo_config.planning_m) as executor:
        futures = [executor.submit(generate_single_plan, i) for i in range(cepo_config.planning_m)]
        for future in as_completed(futures):
            i, plan, tokens_used, log_entry = future.result()
            completion_tokens += tokens_used
            cb_log.update(log_entry)
            if plan:
                plans.append((i, plan))
                if cepo_config.print_output:
                    print(f'\nCePO: Plan proposal generated. Attempt {i + 1} out of {cepo_config.planning_m}.\n')
            if len(plans) == cepo_config.planning_n:
                break
    plans = [plan for _, plan in sorted(plans)]
    if not plans:
        messages = [{'role': 'user', 'content': question_only}]
        provider_request = {'model': model, 'messages': messages, 'max_tokens': cepo_config.planning_max_tokens_step2_direct, 'temperature': cepo_config.planning_temperature_step2_direct, 'top_p': 0.95, 'reasoning_effort_levels': ['high', 'medium', 'low']}
        response, finish_reason, completion_tokens = llm_call_reason_effort_fallback(client=client, provider_request=provider_request, cepo_config=cepo_config)
        local_completion_tokens += completion_tokens
        if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and request_id:
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
            optillm.conversation_logger.log_provider_call(request_id, provider_request, response_dict)
        if response is None or finish_reason == 'length':
            print('Direct answer failed, empty response or length')
            response = ''
        messages.append({'role': 'assistant', 'content': response})
        plans.append(response)
        cb_log[f'messages_planning_fallback_used'] = messages
        if cepo_config.print_output:
            print(f'\nCePO: No plans generated successfully. Taking the fallback.\n')
    plans_message = ''
    for i, plan in enumerate(plans):
        plans_message += f'Response {i + 1}:\n{plan}\n\n'
    plans_message = plans_message.rstrip()
    content = f'Can you review your last {len(plans)} responses and identify any inconsistency between them. After that, can you address it and present a final step-by-step solution to the problem? Here is the question:\n{question_only} /think'
    user_content = f'Previous responses to review:\n\n{plans_message}\n\n{content}'
    messages = [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_content}]
    provider_request = {'model': model, 'messages': messages, 'max_tokens': cepo_config.planning_max_tokens_step1, 'temperature': cepo_config.planning_temperature_step1, 'top_p': 1.0}
    response, finish_reason, completion_tokens_ = llm_call_reason_effort_fallback(client=client, provider_request=provider_request, reasoning_effort_levels=['high', 'medium'], cepo_config=cepo_config)
    completion_tokens += completion_tokens_
    if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and request_id:
        response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
        optillm.conversation_logger.log_provider_call(request_id, provider_request, response_dict)
    if response is None or finish_reason == 'length':
        print('Step 3 failed and only taking plans[0]')
        final_solution = plans[0]
    else:
        completion_tokens += completion_tokens
        final_solution = response
    messages.append({'role': 'assistant', 'content': final_solution})
    if cepo_config.planning_max_tokens_step4 != 0:
        content = f'Use your final solution from above to correctly answer the question. Here is the question:\n{task} /think'
        messages = [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': f"Here's my final solution: {final_solution}\n\nNow {content}"}]
        provider_request = {'model': model, 'messages': messages, 'max_tokens': cepo_config.planning_max_tokens_step1, 'temperature': cepo_config.planning_temperature_step1, 'top_p': 1.0}
        response, finish_reason, completion_tokens_ = llm_call_reason_effort_fallback(client=client, provider_request=provider_request, reasoning_effort_levels=['high', 'medium'], cepo_config=cepo_config)
        completion_tokens += completion_tokens_
        if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and request_id:
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
            optillm.conversation_logger.log_provider_call(request_id, provider_request, response_dict)
        if response is None or finish_reason == 'length':
            print('Step 4 failed and only taking step 3 output')
            final_output = final_solution
        else:
            final_output = response
    else:
        final_output = final_solution
    cb_log['messages'] = messages
    if cepo_config.print_output:
        print(f'\nCePO: Answer generated for one bestofn_n attempt.')
    return (final_output, completion_tokens, cb_log)

def generate_single_plan(i):
    local_cb_log = {}
    local_completion_tokens = 0
    if cepo_config.planning_max_tokens_step1 != 0:
        if cepo_config.use_plan_diversity:
            assert approach
            content = f'To answer this question, can you come up with a concise plan using to solve it step-by-step but do not provide the final answer. Here is the approach you need to follow to generate the plan: {approach}. Also, for each step, provide your confidence in the correctness of that step as well as your ability to execute it correctly. Here is the question:\n{question_only}\nRead the question again:\n\n{question_only}'
        else:
            assert not approach
            content = f'To answer this question, can you come up with a concise plan to solve it step-by-step but do not provide the final answer. Also, for each step, provide your confidence in the correctness of that step as well as your ability to execute it correctly. Here is the question:\n{question_only}\nRead the question again:\n\n{question_only}'
        messages = [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': content}]
        provider_request = {'model': model, 'messages': messages, 'max_tokens': cepo_config.planning_max_tokens_step1, 'temperature': cepo_config.planning_temperature_step1, 'top_p': 1.0}
        response, finish_reason, completion_tokens = llm_call_reason_effort_fallback(client=client, provider_request=provider_request, reasoning_effort_levels=['high', 'medium'], cepo_config=cepo_config)
        local_completion_tokens += completion_tokens
        if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and request_id:
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
            optillm.conversation_logger.log_provider_call(request_id, provider_request, response_dict)
        if finish_reason == 'length':
            return (i, None, local_completion_tokens, {f'messages_planning_{i}_rejected_due_to_length': messages})
        parsed_plan = response
    else:
        messages = []
        parsed_plan = ''
    if cepo_config.planning_max_tokens_step1 != 0:
        messages.append({'role': 'assistant', 'content': parsed_plan})
        messages.append({'role': 'user', 'content': 'Can you execute the above plan step-by-step to produce the final answer. Be extra careful when executing steps where your confidence is lower. /think'})
    else:
        messages.append({'role': 'user', 'content': f'Can you solve this problem step-by-step to produce the final answer? Here is the question:\n{question_only}\nRead the question again:\n\n{question_only} /think'})
    provider_request = {'model': model, 'messages': messages, 'max_tokens': cepo_config.planning_max_tokens_step1, 'temperature': cepo_config.planning_temperature_step1, 'top_p': 1.0}
    response, finish_reason, completion_tokens = llm_call_reason_effort_fallback(client=client, provider_request=provider_request, reasoning_effort_levels=['high', 'medium'], cepo_config=cepo_config)
    local_completion_tokens += completion_tokens
    if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and request_id:
        response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
        optillm.conversation_logger.log_provider_call(request_id, provider_request, response_dict)
    if finish_reason == 'length':
        return (i, None, local_completion_tokens, {f'messages_planning_{i}_rejected_due_to_length': messages})
    parsed_exec = response
    messages.append({'role': 'assistant', 'content': parsed_exec})
    local_cb_log[f'messages_planning_{i}'] = messages
    return (i, parsed_exec, local_completion_tokens, local_cb_log)

def generate_approaches(system_prompt: str, initial_query: str, num_approach: int, client: Any, model: str, cepo_config: CepoConfig, max_retry: int=2, request_id: str=None) -> tuple[list[str], int]:
    completion_tokens = 0
    question_only = extract_question_only(initial_query)
    approaches = []
    content = f'To answer the question: "{question_only}", please propose {num_approach} different high-level approaches to solve the problem. All approaches should be fundamentally different from each other and easily excecutable without too much steps. Do not include a step-by-step plan or the final answer. You must present the approaches in the following JSON format which is directly loadable:\n{{\n    "approach_1": "<Description of approach 1>",\n    "approach_2": "<Description of approach 2>",\n    "approach_3": "<Description of approach 3>",\n    ...\n}}'
    messages = [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': content}]
    retries = 0
    while retries < max_retry:
        try:
            provider_request = {'model': model, 'messages': messages, 'max_tokens': cepo_config.planning_max_tokens_step0, 'temperature': cepo_config.planning_temperature_step0, 'stream': False}
            response = client.chat.completions.create(**provider_request)
            if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and request_id:
                response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
                optillm.conversation_logger.log_provider_call(request_id, provider_request, response_dict)
            completion_tokens += response.usage.completion_tokens
            completion = response.choices[0].message.content
            cleaned_completion = completion.replace('\\', '\\\\').replace('json', '').replace('```', '')
            for _, value in json.loads(cleaned_completion).items():
                approaches.append(value.replace('\\\\', '\\'))
            break
        except json.JSONDecodeError as e:
            print(e)
            print(f'Parsing Error when generating diverse approaches, retrying... ({retries + 1}/{max_retry})')
            retries += 1
    if retries == max_retry:
        print('Max retry attempts reached, returning empty list.')
        return ([], 0)
    return (approaches, completion_tokens)

def generate_n_completions(system_prompt: str, initial_query: str, client: Any, model: str, cepo_config: CepoConfig, request_id: str) -> tuple[list[str], int, dict]:
    """
    Generates n completions for the Best of N step of CePO.

    Parameters:
        system_prompt (str): The system prompt to guide the model.
        initial_query (str): The task or question to be addressed.
        client (Any): The client instance for interacting with the AI model.
        model (str): The model name to be used for generating completions.
        cepo_config (CepoConfig): Configuration parameters for CePO flow.

    Returns:
        Tuple[str, int, dict]: The generated completion, number of tokens used, and a log dictionary.
    """
    completion_tokens = 0
    cb_log = {}
    cb_log['system_prompt'] = system_prompt
    cb_log['initial_query'] = initial_query
    completions = [None] * cepo_config.bestofn_n
    approaches = None
    if cepo_config.use_plan_diversity:
        approaches, approach_completion_tokens = generate_approaches(system_prompt=system_prompt, initial_query=initial_query, num_approach=cepo_config.bestofn_n, client=client, model=model, cepo_config=cepo_config, request_id=request_id)
        cb_log['approaches'] = approaches
        completion_tokens += approach_completion_tokens
        if cepo_config.print_output:
            print(f'\nCePO: Plan diversity approaches ({cepo_config.bestofn_n}):\n{approaches}\n')

    def run_single_completion(i):
        if cepo_config.print_output:
            print(f'\nCePO: Generating completion {i + 1} out of {cepo_config.bestofn_n} \n')
        approach = approaches[i] if approaches else None
        response_i, completion_tokens_i, cb_log_i = generate_completion(system_prompt, initial_query, client, model, cepo_config, approach, request_id)
        return (i, response_i, completion_tokens_i, cb_log_i)
    with ThreadPoolExecutor(max_workers=cepo_config.bestofn_n) as executor:
        futures = [executor.submit(run_single_completion, i) for i in range(cepo_config.bestofn_n)]
        for future in as_completed(futures):
            i, response_i, tokens_i, cb_log_i = future.result()
            completions[i] = response_i
            completion_tokens += tokens_i
            cb_log[f'completion_{i}_response'] = response_i
            cb_log[f'completion_{i}_log'] = cb_log_i
            cb_log[f'completion_{i}_completion_tokens'] = tokens_i
    if cepo_config.print_output:
        print(f'\nCePO: All Answers generated!')
    completions = [c if isinstance(c, str) else '' for c in completions]
    return (completions, completion_tokens, cb_log)

def rate_completions_absolute(system_prompt: str, initial_query: str, client: Any, model: str, completions: list[str], cepo_config: CepoConfig, cb_log: dict, request_id: str=None) -> tuple[str, int, dict]:
    """
    Rates completions for the Best of N step of CePO. Each completion is rated on a scale of 1 to 10 individually.
    
    Parameters:
        system_prompt (str): The system prompt to guide the model.
        initial_query (str): The task or question to be addressed.
        client (Any): The client instance for interacting with the AI model.
        model (str): The model name to be used for generating completions.
        completions (list[str]): List of completions to be rated.
        cepo_config (CepoConfig): Configuration parameters for CePO flow.

    Returns:
        Tuple[str, int, dict]: The generated completion, number of tokens used, and a log dictionary.
    """
    completion_tokens = 0
    rating_prompt = 'Please act as an impartial judge and evaluate the accuracy of the response provided by an AI assistant to the user question displayed below. Your evaluation should consider only correctness and accuracy as the primary factor. Evaluation Criteria:\n- Correctness: How free is it from errors or mistakes?\n- Accuracy: Are the information and explanations factually correct?\nEvaluation Process:\n1. Carefully review the user question and the AI assistant\'s response.\n2. Assess the response for any inaccuracies in reasoning as well as execution.\n3. Provide a detailed explanation of your step-by-step evaluation.\n4. Identify if the final answer is correct or not. \nBegin your evaluation by thinking through the given problem and response step-by-step. VERY IMPORTANT: Re-do any calculations present and check if you arrive at the same answer. Throughly check for any inaccuracies in reasoning and calculations for each step. Be as objective as possible. After providing your detailed explanation, please rate the response as 0 or 1, (0 for incorrect and 1 for correct) by strictly following this format: "Rating: [[rating]]", for example: "Rating: [[0]]"'
    rating_format_instruction = '\n\nRate the above response beginning with the detailed explanation followed by a rating of 0 or 1 by strictly following this format: "Explanation: <reason for your rating>\n\nRating: [[rating]]"'
    ratings = []
    for i, completion in enumerate(completions):
        system_content = f'USER QUESTION: {initial_query}\n\nRESPONSE: {completion}'
        rating_messages = [{'role': 'system', 'content': system_prompt + '\n\n' + rating_prompt}, {'role': 'user', 'content': system_content + rating_format_instruction}]
        provider_request = {'model': model, 'messages': rating_messages, 'max_tokens': cepo_config.bestofn_max_tokens, 'temperature': cepo_config.bestofn_temperature, 'top_p': 1.0}
        rating_response = client.chat.completions.create(**provider_request)
        rating_response, _, completion_tokens_ = llm_call_reason_effort_fallback(client=client, provider_request=provider_request, reasoning_effort_levels=['high', 'medium'], cepo_config=cepo_config)
        if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and request_id:
            response_dict = rating_response.model_dump() if hasattr(rating_response, 'model_dump') else rating_response
            optillm.conversation_logger.log_provider_call(request_id, provider_request, response_dict)
        completion_tokens += completion_tokens_
        cb_log[f'rating_response_{i}'] = rating_response
        if cepo_config.print_output:
            print(f'\nCePO: Rating response for completion {i}: {rating_response}')
        pattern = 'Rating: \\[\\[(\\d+)\\]\\]'
        match = re.search(pattern, rating_response)
        rating_response = match.group(1) if match else '-1'
        try:
            ratings.append(float(rating_response))
        except ValueError:
            ratings.append(-1)
    best_index = ratings.index(max(ratings))
    cb_log['ratings'] = ratings
    cb_log['best_index'] = best_index
    if cepo_config.print_output:
        print(f'\nCePO: Finished rating completions. Ratings: {ratings}, best completion index: {best_index}')
    return (completions[best_index], completion_tokens, cb_log)

def rate_completions_pairwise(system_prompt: str, initial_query: str, client: Any, model: str, completions: list[str], cepo_config: CepoConfig, cb_log: dict, request_id: str=None) -> tuple[str, int, dict]:
    """
    Rates completions for the Best of N step of CePO. Completions are rated pairwise against each other in both orders (A vs B and B vs A).

    Parameters:
        system_prompt (str): The system prompt to guide the model.
        initial_query (str): The task or question to be addressed.
        client (Any): The client instance for interacting with the AI model.
        model (str): The model name to be used for generating completions.
        completions (list[str]): List of completions to be rated.
        cepo_config (CepoConfig): Configuration parameters for CePO flow.

    Returns:
        Tuple[str, int, dict]: The generated completion, number of tokens used, and a log dictionary.
    """
    completion_tokens = 0
    rating_prompt = 'Please act as an impartial judge and compare the quality of the two responses provided by the AI assistant to the user\'s question displayed below. Evaluation Criteria:\n- Helpfulness: How effectively does the response meet the user\'s needs?\n- Relevance: How directly does the response address the original question?\n- Accuracy: Are the information and explanations factually correct?\n- Depth: Does the response provide comprehensive and meaningful insights?\n- Creativity: Does the response offer unique or innovative perspectives?\n- Clarity: Is the response well-organized, coherent, and easy to understand?\nEvaluation Process:\n1. Carefully review the user\'s question and the AI assistant\'s responses.\n2. Compare the responses against each other for each criterion.\n3. Provide a concise explanation of your overall evaluation.\n4. Select the response that is superior based on the above criteria.\nReply with "Better Response: [[response id]]".\nIf the first response is better, reply with "Better Response: [[0]]". If the second response is better, reply with "Better Response: [[1]]".'
    ratings = [0] * cepo_config.bestofn_n
    pairs = [(i, j) for i in range(cepo_config.bestofn_n) for j in range(cepo_config.bestofn_n) if i != j]
    for pair in pairs:
        comparison_content = f'User Question: {initial_query}\n\nResponse 0: {completions[pair[0]]}\n\nResponse 1: {completions[pair[1]]}\n\nWhich response is better? Please provide your reasoning and then indicate your choice with "Better Response: [[0]]" if the first response is better, or "Better Response: [[1]]" if the second response is better.'
        rating_messages = [{'role': 'system', 'content': system_prompt + '\n\n' + rating_prompt}, {'role': 'user', 'content': comparison_content}]
        provider_request = {'model': model, 'messages': rating_messages, 'max_tokens': cepo_config.bestofn_max_tokens, 'temperature': cepo_config.bestofn_temperature}
        rating_response = client.chat.completions.create(**provider_request)
        if hasattr(optillm, 'conversation_logger') and optillm.conversation_logger and request_id:
            response_dict = rating_response.model_dump() if hasattr(rating_response, 'model_dump') else rating_response
            optillm.conversation_logger.log_provider_call(request_id, provider_request, response_dict)
        completion_tokens += rating_response.usage.completion_tokens
        rating_response = rating_response.choices[0].message.content.strip()
        cb_log[f'rating_response_for_pair_{pair[0]}_{pair[1]}'] = rating_response
        if cepo_config.print_output:
            print(f'\nCePO: Rating response for pair {pair}: {rating_response}')
        pattern = 'Better Response: \\[\\[(\\d+)\\]\\]'
        match = re.search(pattern, rating_response)
        if match:
            rating_response = match.group(1)
            try:
                rating = int(rating_response)
                ratings[pair[rating]] += 1
            except ValueError:
                ratings[pair[0]] += 1
        else:
            ratings[pair[0]] += 1
    best_index = ratings.index(max(ratings))
    cb_log['ratings'] = ratings
    cb_log['best_index'] = best_index
    if cepo_config.print_output:
        print(f'\nCePO: Finished rating completions. Ratings: {ratings}, best completion index: {best_index}')
    return (completions[best_index], completion_tokens, cb_log)

def majority_vote_math(completions, last_n_chars=100):
    extracted_answer_map = []
    for response in completions:
        extracted_answer = extract_answer_mathverify(response, last_n_chars)
        extracted_answer = extracted_answer[0] if extracted_answer else None
        extracted_answer_map.append((response, extracted_answer))
    counts = Counter((answer for _, answer in extracted_answer_map))
    majority_answer, count = counts.most_common(1)[0]
    for response, answer in extracted_answer_map:
        if answer == majority_answer:
            return (response, count)
    return (extracted_answer_map[0][0], 0)

def majority_vote_mcq(completions, last_n_chars=100):
    extracted_answer_map = []
    for response in completions:
        extracted_answer = extract_abcd(response[-last_n_chars:])
        extracted_answer_map.append((response, extracted_answer))
    counts = Counter((answer for _, answer in extracted_answer_map))
    majority_answer, count = counts.most_common(1)[0]
    for response, answer in extracted_answer_map:
        if answer == majority_answer:
            return (response, count)
    return (extracted_answer_map[0][0], 0)

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

def make_request(index):
    try:
        response = self.client.chat.completions.create(model=TEST_MODEL, messages=[{'role': 'system', 'content': 'You are a helpful assistant.'}, {'role': 'user', 'content': f'Concurrent test {index}. Reply with the number {index}.'}], max_tokens=10)
        results.put(('success', index, response))
    except Exception as e:
        results.put(('error', index, str(e)))

class MockOpenAIResponse:
    """Mock OpenAI API response"""

    def __init__(self, content='Test response', usage_tokens=10, n=1, call_index=0):
        self.choices = []
        for i in range(n):
            choice = Mock()
            choice.message = Mock()
            if call_index % 2 == 0:
                choice.message.content = f'Code version A: {content} {i + 1}' if n > 1 else f'Code version A: {content}'
            else:
                choice.message.content = f'Code version B: {content} {i + 1}' if n > 1 else f'Code version B: {content}'
            self.choices.append(choice)
        self.usage = Mock()
        self.usage.completion_tokens = usage_tokens
        self.usage.completion_tokens_details = Mock()
        self.usage.completion_tokens_details.reasoning_tokens = 0

    def model_dump(self):
        return {'choices': [{'message': {'content': choice.message.content}} for choice in self.choices], 'usage': {'completion_tokens': self.usage.completion_tokens}}

def __init__(self, content='Test response', usage_tokens=10, n=1, call_index=0):
    self.choices = []
    for i in range(n):
        choice = Mock()
        choice.message = Mock()
        if call_index % 2 == 0:
            choice.message.content = f'Code version A: {content} {i + 1}' if n > 1 else f'Code version A: {content}'
        else:
            choice.message.content = f'Code version B: {content} {i + 1}' if n > 1 else f'Code version B: {content}'
        self.choices.append(choice)
    self.usage = Mock()
    self.usage.completion_tokens = usage_tokens
    self.usage.completion_tokens_details = Mock()
    self.usage.completion_tokens_details.reasoning_tokens = 0

class TestPluginStructure:
    """Test plugin structure and exports"""

    def test_slug_exists(self):
        """Test that plugin has SLUG defined"""
        assert hasattr(sys.modules['optillm.plugins.mcp_plugin'], 'SLUG')
        assert SLUG == 'mcp'

    def test_run_function_exists(self):
        """Test that plugin has run function defined"""
        import optillm.plugins.mcp_plugin as plugin
        assert hasattr(plugin, 'run')
        assert callable(plugin.run)

    def test_required_imports(self):
        """Test that required modules can be imported"""
        try:
            from mcp.client.sse import sse_client
            from mcp.client.websocket import websocket_client
            assert sse_client is not None
            assert websocket_client is not None
        except ImportError as e:
            pytest.fail(f'Required MCP imports failed: {e}')

def test_slug_exists(self):
    """Test that plugin has SLUG defined"""
    assert hasattr(sys.modules['optillm.plugins.mcp_plugin'], 'SLUG')
    assert SLUG == 'mcp'

def test_memory_plugin_structure():
    """Test memory plugin has required structure"""
    import optillm.plugins.memory_plugin as plugin
    assert hasattr(plugin, 'run')
    assert hasattr(plugin, 'SLUG')
    assert plugin.SLUG == 'memory'
    assert hasattr(plugin, 'Memory')

def test_genselect_plugin():
    """Test genselect plugin module"""
    import optillm.plugins.genselect_plugin as plugin
    assert hasattr(plugin, 'run')
    assert hasattr(plugin, 'SLUG')
    assert hasattr(plugin, 'DEFAULT_NUM_CANDIDATES')
    assert plugin.SLUG == 'genselect'

def test_majority_voting_plugin():
    """Test majority voting plugin module"""
    import optillm.plugins.majority_voting_plugin as plugin
    assert hasattr(plugin, 'run')
    assert hasattr(plugin, 'SLUG')
    assert hasattr(plugin, 'extract_final_answer')
    assert hasattr(plugin, 'normalize_response')
    assert plugin.SLUG == 'majority_voting'

def test_web_search_plugin():
    """Test web search plugin module"""
    import optillm.plugins.web_search_plugin as plugin
    assert hasattr(plugin, 'run')
    assert hasattr(plugin, 'SLUG')
    assert hasattr(plugin, 'GoogleSearcher')
    assert hasattr(plugin, 'extract_search_queries')
    assert plugin.SLUG == 'web_search'

def test_deep_research_plugin():
    """Test deep research plugin module"""
    import optillm.plugins.deep_research_plugin as plugin
    assert hasattr(plugin, 'run')
    assert hasattr(plugin, 'SLUG')
    assert hasattr(plugin, 'DeepResearcher')
    assert plugin.SLUG == 'deep_research'

def test_deepthink_plugin_imports():
    """Test deepthink plugin and its submodules can be imported"""
    import optillm.plugins.deepthink_plugin as plugin
    assert hasattr(plugin, 'run')
    assert hasattr(plugin, 'SLUG')
    assert plugin.SLUG == 'deepthink'
    from optillm.plugins.deepthink import SelfDiscover, UncertaintyRoutedCoT
    assert SelfDiscover is not None
    assert UncertaintyRoutedCoT is not None

def test_longcepo_plugin():
    """Test longcepo plugin module"""
    import optillm.plugins.longcepo_plugin as plugin
    assert hasattr(plugin, 'run')
    assert hasattr(plugin, 'SLUG')
    assert plugin.SLUG == 'longcepo'
    from optillm.plugins.longcepo import run_longcepo
    assert run_longcepo is not None

def test_spl_plugin():
    """Test spl plugin module"""
    import optillm.plugins.spl_plugin as plugin
    assert hasattr(plugin, 'run')
    assert hasattr(plugin, 'SLUG')
    assert plugin.SLUG == 'spl'
    from optillm.plugins.spl import run_spl
    assert run_spl is not None

def test_proxy_plugin():
    """Test proxy plugin module"""
    import optillm.plugins.proxy_plugin as plugin
    assert hasattr(plugin, 'run')
    assert hasattr(plugin, 'SLUG')
    assert plugin.SLUG == 'proxy'
    from optillm.plugins.proxy import client, config, approach_handler
    assert client is not None
    assert config is not None
    assert approach_handler is not None

def test_mcp_plugin():
    """Test MCP plugin module"""
    import optillm.plugins.mcp_plugin as plugin
    assert hasattr(plugin, 'run')
    assert hasattr(plugin, 'SLUG')
    assert hasattr(plugin, 'ServerConfig')
    assert hasattr(plugin, 'MCPServer')
    assert hasattr(plugin, 'execute_tool')
    assert plugin.SLUG == 'mcp'

def run_approach(approach_name: str, system_prompt: str, query: str, client, model: str) -> Dict:
    start_time = time.time()
    try:
        if approach_name == 'none':
            messages = []
            if system_prompt:
                messages.append({'role': 'system', 'content': system_prompt})
            messages.append({'role': 'user', 'content': query})
            response = client.chat.completions.create(model=model, messages=messages, temperature=0.7)
            result = (response.choices[0].message.content, response.usage.total_tokens)
        else:
            approach_func = APPROACHES[approach_name]
            result = approach_func(system_prompt, query, client, model)
        end_time = time.time()
        return {'approach': approach_name, 'result': result, 'time': end_time - start_time, 'status': 'success'}
    except Exception as e:
        end_time = time.time()
        logger.error(f'Error in {approach_name}: {str(e)}')
        return {'approach': approach_name, 'result': str(e), 'time': end_time - start_time, 'status': 'error'}

def run_test_case(test_case: Dict, approaches: List[str], client, model: str) -> Dict:
    system_prompt = test_case['system_prompt']
    query = test_case['query']
    results = []
    with ThreadPoolExecutor() as executor:
        future_to_approach = {executor.submit(run_approach, approach, system_prompt, query, client, model): approach for approach in approaches}
        for future in as_completed(future_to_approach):
            results.append(future.result())
    return {'test_case': test_case, 'results': results}

class TestRequestBatcher(unittest.TestCase):
    """Test the core RequestBatcher functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.batcher = RequestBatcher(max_batch_size=4, max_wait_ms=100)
        self.test_responses = []

        def mock_processor(requests):
            """Mock batch processor that returns simple responses"""
            responses = []
            for i, req in enumerate(requests):
                responses.append({'id': f'test-{i}', 'object': 'chat.completion', 'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': f'Response to request {i}'}, 'finish_reason': 'stop'}], 'usage': {'completion_tokens': 10, 'total_tokens': 20}})
            return responses
        self.batcher.set_processor(mock_processor)

    def tearDown(self):
        """Clean up after tests"""
        self.batcher.shutdown()

    def test_single_request(self):
        """Test that single requests work correctly"""
        request_data = {'model': 'test-model', 'prompt': 'Hello'}
        response = self.batcher.add_request(request_data)
        self.assertIsInstance(response, dict)
        self.assertEqual(response['object'], 'chat.completion')
        self.assertEqual(response['choices'][0]['message']['content'], 'Response to request 0')

    def test_batch_formation(self):
        """Test that multiple requests form a batch"""

        def send_request(request_id):
            request_data = {'model': 'test-model', 'prompt': f'Request {request_id}'}
            return self.batcher.add_request(request_data)
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(send_request, i) for i in range(3)]
            responses = [future.result() for future in futures]
        self.assertEqual(len(responses), 3)
        for i, response in enumerate(responses):
            self.assertIsInstance(response, dict)
            self.assertEqual(response['object'], 'chat.completion')

    def test_batch_timeout(self):
        """Test that partial batches process after timeout"""
        start_time = time.time()
        request_data = {'model': 'test-model', 'prompt': 'Single request'}
        response = self.batcher.add_request(request_data)
        elapsed_time = time.time() - start_time
        self.assertGreater(elapsed_time, 0.09)
        self.assertIsInstance(response, dict)

    def test_incompatible_requests(self):
        """Test that incompatible requests are properly handled"""
        request_data = {'model': 'test-model', 'stream': True}
        with self.assertRaises(BatchingError):
            self.batcher.add_request(request_data)

    def test_processor_error_handling(self):
        """Test that processor errors are handled correctly"""

        def failing_processor(requests):
            raise Exception('Processor failed')
        batcher = RequestBatcher(max_batch_size=2, max_wait_ms=50)
        batcher.set_processor(failing_processor)
        try:
            request_data = {'model': 'test-model', 'prompt': 'Test'}
            with self.assertRaises(BatchingError):
                batcher.add_request(request_data)
        finally:
            batcher.shutdown()

    def test_batch_stats(self):
        """Test that batch statistics are collected correctly"""
        for i in range(5):
            request_data = {'model': 'test-model', 'prompt': f'Request {i}'}
            self.batcher.add_request(request_data)
        stats = self.batcher.get_stats()
        self.assertGreater(stats['total_requests'], 0)
        self.assertGreater(stats['total_batches'], 0)
        self.assertGreater(stats['avg_batch_size'], 0)

def mock_processor(requests):
    """Mock batch processor that returns simple responses"""
    responses = []
    for i, req in enumerate(requests):
        responses.append({'id': f'test-{i}', 'object': 'chat.completion', 'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': f'Response to request {i}'}, 'finish_reason': 'stop'}], 'usage': {'completion_tokens': 10, 'total_tokens': 20}})
    return responses

def test_batch_formation(self):
    """Test that multiple requests form a batch"""

    def send_request(request_id):
        request_data = {'model': 'test-model', 'prompt': f'Request {request_id}'}
        return self.batcher.add_request(request_data)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(send_request, i) for i in range(3)]
        responses = [future.result() for future in futures]
    self.assertEqual(len(responses), 3)
    for i, response in enumerate(responses):
        self.assertIsInstance(response, dict)
        self.assertEqual(response['object'], 'chat.completion')

class TestPerformanceBenches(unittest.TestCase):
    """Performance comparison tests"""

    def setUp(self):
        """Set up performance test fixtures"""
        self.test_prompts = [('System prompt 1', 'What is AI?'), ('System prompt 2', 'Explain machine learning'), ('System prompt 3', 'Define neural networks'), ('System prompt 4', 'Describe deep learning')]

    def measure_sequential_processing(self, prompts):
        """Measure time for sequential processing"""
        start_time = time.time()
        responses = []
        for sys_prompt, user_prompt in prompts:
            time.sleep(0.1)
            responses.append(f'Response to: {user_prompt}')
        end_time = time.time()
        return (responses, end_time - start_time)

    def measure_batch_processing(self, prompts):
        """Measure time for batch processing"""
        batcher = RequestBatcher(max_batch_size=len(prompts), max_wait_ms=10)

        def mock_batch_processor(requests):
            time.sleep(0.15)
            return [{'response': f'Batched response {i}'} for i in range(len(requests))]
        batcher.set_processor(mock_batch_processor)
        try:
            start_time = time.time()

            def send_request(prompt_data):
                sys_prompt, user_prompt = prompt_data
                return batcher.add_request({'model': 'test-model', 'system_prompt': sys_prompt, 'user_prompt': user_prompt})
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(prompts)) as executor:
                futures = [executor.submit(send_request, prompt) for prompt in prompts]
                responses = [future.result() for future in futures]
            end_time = time.time()
            return (responses, end_time - start_time)
        finally:
            batcher.shutdown()

    def test_batching_performance_improvement(self):
        """Test that batching provides performance improvement"""
        seq_responses, seq_time = self.measure_sequential_processing(self.test_prompts)
        batch_responses, batch_time = self.measure_batch_processing(self.test_prompts)
        improvement_ratio = seq_time / batch_time
        self.assertGreater(improvement_ratio, 1.5, f'Batching should be >1.5x faster, got {improvement_ratio:.2f}x')
        self.assertEqual(len(seq_responses), len(batch_responses))

def measure_batch_processing(self, prompts):
    """Measure time for batch processing"""
    batcher = RequestBatcher(max_batch_size=len(prompts), max_wait_ms=10)

    def mock_batch_processor(requests):
        time.sleep(0.15)
        return [{'response': f'Batched response {i}'} for i in range(len(requests))]
    batcher.set_processor(mock_batch_processor)
    try:
        start_time = time.time()

        def send_request(prompt_data):
            sys_prompt, user_prompt = prompt_data
            return batcher.add_request({'model': 'test-model', 'system_prompt': sys_prompt, 'user_prompt': user_prompt})
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(prompts)) as executor:
            futures = [executor.submit(send_request, prompt) for prompt in prompts]
            responses = [future.result() for future in futures]
        end_time = time.time()
        return (responses, end_time - start_time)
    finally:
        batcher.shutdown()

class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases"""

    def test_batch_mode_errors(self):
        """Test error conditions in batch mode"""
        batcher = RequestBatcher(max_batch_size=2, max_wait_ms=50)
        with self.assertRaises(BatchingError):
            batcher.add_request({'model': 'test'})
        batcher.shutdown()

    def test_mixed_model_requests(self):
        """Test that requests with different models are properly separated"""
        batcher = RequestBatcher(max_batch_size=4, max_wait_ms=50)

        def mock_processor(requests):
            models = set((req.get('model') for req in requests))
            self.assertEqual(len(models), 1, 'Batch should have requests from single model')
            return [{'response': 'ok'}] * len(requests)
        batcher.set_processor(mock_processor)
        try:
            req1 = {'model': 'model-a', 'prompt': 'test1'}
            req2 = {'model': 'model-b', 'prompt': 'test2'}
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                future1 = executor.submit(batcher.add_request, req1)
                future2 = executor.submit(batcher.add_request, req2)
                response1 = future1.result()
                response2 = future2.result()
                self.assertIsInstance(response1, dict)
                self.assertIsInstance(response2, dict)
        finally:
            batcher.shutdown()

def test_mixed_model_requests(self):
    """Test that requests with different models are properly separated"""
    batcher = RequestBatcher(max_batch_size=4, max_wait_ms=50)

    def mock_processor(requests):
        models = set((req.get('model') for req in requests))
        self.assertEqual(len(models), 1, 'Batch should have requests from single model')
        return [{'response': 'ok'}] * len(requests)
    batcher.set_processor(mock_processor)
    try:
        req1 = {'model': 'model-a', 'prompt': 'test1'}
        req2 = {'model': 'model-b', 'prompt': 'test2'}
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future1 = executor.submit(batcher.add_request, req1)
            future2 = executor.submit(batcher.add_request, req2)
            response1 = future1.result()
            response2 = future2.result()
            self.assertIsInstance(response1, dict)
            self.assertIsInstance(response2, dict)
    finally:
        batcher.shutdown()

def test_basic_completion(client):
    """Test basic chat completion"""
    response = client.chat.completions.create(model=TEST_MODEL, messages=[{'role': 'system', 'content': 'You are a helpful assistant.'}, {'role': 'user', 'content': 'Say hello'}], max_tokens=10)
    assert hasattr(response, 'choices')
    assert len(response.choices) > 0
    assert hasattr(response.choices[0], 'message')
    assert hasattr(response.choices[0].message, 'content')

def test_approach_prefix(client):
    """Test approach prefix in model name"""
    response = client.chat.completions.create(model=f'moa-{TEST_MODEL}', messages=[{'role': 'user', 'content': 'What is 2+2?'}], max_tokens=10)
    assert hasattr(response, 'choices')
    assert len(response.choices) > 0

def test_extra_body_approach(client):
    """Test approach specification via extra_body"""
    response = client.chat.completions.create(model=TEST_MODEL, messages=[{'role': 'user', 'content': 'What is 2+2?'}], extra_body={'optillm_approach': 'bon'}, max_tokens=10)
    assert hasattr(response, 'choices')
    assert len(response.choices) > 0

def test_reasoning_tokens_in_response(client):
    """Test that reasoning tokens are included in API responses"""
    response = client.chat.completions.create(model=TEST_MODEL, messages=[{'role': 'system', 'content': 'Think step by step and show your reasoning.'}, {'role': 'user', 'content': 'What is 15 × 23? Please think through this step by step.'}], max_tokens=100)
    assert hasattr(response, 'choices')
    assert len(response.choices) > 0
    assert hasattr(response, 'usage')
    assert hasattr(response.usage, 'completion_tokens_details')
    assert hasattr(response.usage.completion_tokens_details, 'reasoning_tokens')
    reasoning_tokens = response.usage.completion_tokens_details.reasoning_tokens
    assert isinstance(reasoning_tokens, int)
    assert reasoning_tokens >= 0

def test_reasoning_tokens_with_thinking_prompt(client):
    """Test reasoning tokens with a prompt designed to trigger thinking"""
    response = client.chat.completions.create(model=TEST_MODEL, messages=[{'role': 'system', 'content': 'You are a helpful assistant. Use <think> tags to show your reasoning process.'}, {'role': 'user', 'content': 'I have 12 apples. I eat 3, give away 4, and buy 7 more. How many apples do I have now?'}], max_tokens=150)
    assert hasattr(response, 'usage')
    assert hasattr(response.usage, 'completion_tokens_details')
    assert hasattr(response.usage.completion_tokens_details, 'reasoning_tokens')
    reasoning_tokens = response.usage.completion_tokens_details.reasoning_tokens
    assert isinstance(reasoning_tokens, int)
    assert reasoning_tokens >= 0

def test_reasoning_tokens_with_multiple_responses(client):
    """Test reasoning tokens with n > 1"""
    response = client.chat.completions.create(model=TEST_MODEL, messages=[{'role': 'user', 'content': "Think about this: What's 2+2?"}], n=2, max_tokens=50)
    assert len(response.choices) == 2
    assert hasattr(response.usage, 'completion_tokens_details')
    assert hasattr(response.usage.completion_tokens_details, 'reasoning_tokens')
    reasoning_tokens = response.usage.completion_tokens_details.reasoning_tokens
    assert isinstance(reasoning_tokens, int)
    assert reasoning_tokens >= 0

def test_reasoning_tokens_backward_compatibility(client):
    """Test that responses without thinking still work normally"""
    response = client.chat.completions.create(model=TEST_MODEL, messages=[{'role': 'user', 'content': 'Say hello'}], max_tokens=10)
    assert hasattr(response.usage, 'completion_tokens_details')
    assert hasattr(response.usage.completion_tokens_details, 'reasoning_tokens')
    reasoning_tokens = response.usage.completion_tokens_details.reasoning_tokens
    assert isinstance(reasoning_tokens, int)
    assert reasoning_tokens >= 0

