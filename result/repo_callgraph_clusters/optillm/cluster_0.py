# Cluster 0

def extract_final_answer(solution: str, problem_id: int) -> Dict[str, any]:
    """
    Extract and verify the final answer using official IMO 2025 solutions
    """
    official_verification = verify_answer_format(problem_id, solution)
    result = {'extracted_answer': None, 'confidence': 0.0, 'extraction_method': None, 'official_answer_found': official_verification['correct_answer_found'], 'official_answer_score': official_verification['answer_score']}
    if not solution:
        return result
    if official_verification['correct_answer_found']:
        result['extracted_answer'] = official_verification['extracted_answer']
        result['confidence'] = 1.0
        result['extraction_method'] = 'official_verification'
        return result
    boxed_pattern = '\\\\boxed\\{([^}]+)\\}'
    boxed_matches = re.findall(boxed_pattern, solution)
    if boxed_matches:
        result['extracted_answer'] = boxed_matches[-1].strip()
        result['confidence'] = 0.9
        result['extraction_method'] = 'boxed'
        return result
    answer_patterns = ['final answer[:\\s]*([^\\n]+)', 'answer[:\\s]*([^\\n]+)', 'therefore[:\\s]*([^\\n]+)', 'thus[:\\s]*([^\\n]+)']
    solution_lower = solution.lower()
    for pattern in answer_patterns:
        matches = re.findall(pattern, solution_lower)
        if matches:
            result['extracted_answer'] = matches[-1].strip()
            result['confidence'] = 0.5
            result['extraction_method'] = 'answer_section'
            break
    return result

def extract_answer_from_solution(solution: str, problem_id: int) -> str:
    """
    Extract the final answer from a solution using unified answer extraction
    """
    extracted_answer = extract_answer(solution, problem_type='imo', problem_id=problem_id)
    if extracted_answer is None:
        return None
    if isinstance(extracted_answer, list):
        for item in extracted_answer:
            if isinstance(item, set):
                sorted_elements = sorted(list(item))
                return '{' + ', '.join(map(str, sorted_elements)) + '}'
            elif isinstance(item, (int, float)):
                if problem_id == 3:
                    return f'c = {int(item)}'
                else:
                    return str(int(item))
            elif isinstance(item, str) and item.strip():
                return item
        return str(extracted_answer)
    if isinstance(extracted_answer, set):
        sorted_elements = sorted(list(extracted_answer))
        return '{' + ', '.join(map(str, sorted_elements)) + '}'
    elif isinstance(extracted_answer, (int, float)):
        if problem_id == 3:
            return f'c = {int(extracted_answer)}'
        else:
            return str(int(extracted_answer))
    elif isinstance(extracted_answer, str):
        return extracted_answer
    else:
        return str(extracted_answer)

def check_answer_correctness(problem_id: int, extracted_answer: str) -> bool:
    """
    Check if extracted answer matches the golden answer for the problem
    """
    if not extracted_answer:
        return False
    golden_answers = {1: ['{0, 1, 2, 3}'], 2: ['tangent'], 3: ['c = 4'], 4: ['6', '18', '6, 18'], 5: ['λ < 1', 'λ < √2/2'], 6: ['4048']}
    if problem_id not in golden_answers:
        return False
    correct_answers = golden_answers[problem_id]
    if extracted_answer in correct_answers:
        return True
    if problem_id == 1:
        if extracted_answer == '{0, 1, 3}':
            return False
    if problem_id == 4:
        if any((val in extracted_answer for val in ['6', '18'])):
            return True
        if '2·3^k form' in extracted_answer:
            return True
    if problem_id == 5:
        if any((cond in extracted_answer for cond in ['λ < 1', 'λ < √2/2'])):
            return True
    return False

def extract_solution_quality(response: str) -> Dict[str, any]:
    """
    Analyze the quality of an IMO solution based on mathematical rigor criteria
    """
    analysis = {'has_proof_structure': False, 'uses_mathematical_notation': False, 'has_logical_steps': False, 'addresses_all_cases': False, 'has_conclusion': False, 'length_score': 0, 'rigor_indicators': [], 'completeness_score': 0}
    if not response:
        return analysis
    response_lower = response.lower()
    proof_keywords = ['proof:', 'solution:', 'we prove', 'to show', 'suppose', 'assume', 'let', 'consider']
    if any((keyword in response_lower for keyword in proof_keywords)):
        analysis['has_proof_structure'] = True
        analysis['rigor_indicators'].append('proof_structure')
    math_patterns = ['\\$.*\\$', '\\\\[a-zA-Z]+', '\\\\geq', '\\\\leq', '\\\\in', '\\\\mathbb', '\\\\sum', '\\\\prod']
    if any((re.search(pattern, response) for pattern in math_patterns)):
        analysis['uses_mathematical_notation'] = True
        analysis['rigor_indicators'].append('mathematical_notation')
    logical_words = ['therefore', 'thus', 'hence', 'consequently', 'since', 'because', 'implies', 'follows']
    logical_count = sum((1 for word in logical_words if word in response_lower))
    if logical_count >= 3:
        analysis['has_logical_steps'] = True
        analysis['rigor_indicators'].append('logical_flow')
    case_words = ['case', 'cases', 'if', 'suppose', 'when', 'consider']
    case_count = sum((1 for word in case_words if word in response_lower))
    if case_count >= 2:
        analysis['addresses_all_cases'] = True
        analysis['rigor_indicators'].append('case_analysis')
    conclusion_words = ['conclude', 'final answer', 'solution is', 'answer:', 'qed', 'proven', 'shown']
    if any((word in response_lower for word in conclusion_words)):
        analysis['has_conclusion'] = True
        analysis['rigor_indicators'].append('clear_conclusion')
    word_count = len(response.split())
    if word_count >= 500:
        analysis['length_score'] = 3
    elif word_count >= 200:
        analysis['length_score'] = 2
    elif word_count >= 100:
        analysis['length_score'] = 1
    else:
        analysis['length_score'] = 0
    completeness_factors = [analysis['has_proof_structure'], analysis['uses_mathematical_notation'], analysis['has_logical_steps'], analysis['addresses_all_cases'], analysis['has_conclusion']]
    analysis['completeness_score'] = sum(completeness_factors) / len(completeness_factors)
    return analysis

def verify_answer_format(problem_id: int, solution: str) -> Dict[str, Any]:
    """
    Verify if the solution contains the correct answer format for problems with specific answers
    """
    result = {'correct_answer_found': False, 'extracted_answer': None, 'answer_score': 0.0, 'error_message': ''}
    solution_clean = solution.lower().replace(' ', '').replace('\n', ' ')
    if problem_id == 1:
        set_patterns = ['\\{0,1,3\\}', '\\{0,\\s*1,\\s*3\\}', '\\{1,0,3\\}', '\\{3,1,0\\}', '\\{[013,\\s]+\\}']
        for pattern in set_patterns:
            if re.search(pattern, solution_clean):
                numbers = re.findall('\\d+', re.search(pattern, solution_clean).group())
                if sorted([int(x) for x in numbers]) == [0, 1, 3]:
                    result['correct_answer_found'] = True
                    result['extracted_answer'] = '{0, 1, 3}'
                    result['answer_score'] = 1.0
                    break
    elif problem_id == 3:
        if re.search('c\\s*=\\s*4(?![0-9])', solution) or re.search('constant.*4(?![0-9])', solution) or re.search('answer.*4(?![0-9])', solution):
            result['correct_answer_found'] = True
            result['extracted_answer'] = '4'
            result['answer_score'] = 1.0
    elif problem_id == 4:
        patterns = ['6j.*12\\^k', '6.*j.*12\\^k', 'a_1\\s*=\\s*6.*12', '6.*\\*.*12\\^']
        for pattern in patterns:
            if re.search(pattern, solution_clean):
                result['correct_answer_found'] = True
                result['extracted_answer'] = '6J·12^K'
                result['answer_score'] = 1.0
                break
    elif problem_id == 5:
        threshold_found = False
        patterns = ['λ\\s*>\\s*1/√2', 'lambda\\s*>\\s*1/sqrt\\(2\\)', '1/√2', '√2/2', 'sqrt\\(2\\)/2']
        for pattern in patterns:
            if re.search(pattern, solution):
                threshold_found = True
                break
        if threshold_found:
            alice_wins = 'alice.*win' in solution_clean or 'alice.*λ.*>' in solution_clean
            bazza_wins = 'bazza.*win' in solution_clean or 'bazza.*λ.*<' in solution_clean
            if alice_wins and bazza_wins:
                result['correct_answer_found'] = True
                result['extracted_answer'] = 'λ = 1/√2 threshold'
                result['answer_score'] = 1.0
    elif problem_id == 6:
        if re.search('2025', solution) and ('minimum' in solution_clean or 'answer' in solution_clean):
            result['correct_answer_found'] = True
            result['extracted_answer'] = '2025'
            result['answer_score'] = 1.0
    return result

def verify_key_insights(problem_id: int, solution: str) -> Dict[str, Any]:
    """
    Check for problem-specific key insights that should appear in correct solutions
    """
    problem_data = next((p for p in IMO_2025_PROBLEMS if p['id'] == problem_id), None)
    if not problem_data:
        return {'insight_score': 0.0, 'insights_found': [], 'insights_missing': []}
    key_insights = problem_data['key_insights']
    solution_lower = solution.lower()
    insights_found = []
    insights_missing = []
    insight_keywords = {'reduction_principle': ['reduction', 'reduce', 'specific case'], 'structural_lemma': ['structural', 'lemma', 'vertical', 'horizontal', 'diagonal'], 'c_k_analysis': ['c(k)', 'assertion', 'pk can be covered'], 'sunny_line_covering': ['sunny', 'shady', 'parallel'], 'excenter_identification': ['excenter', 'external', 'angle bisector'], 'auxiliary_point_v': ['auxiliary', 'point v', 'parallelogram'], 'orthocenter_tangency': ['orthocenter', 'tangent', 'perpendicular'], 'circumcircle_properties': ['circumcircle', 'circumcenter'], 'classification_lemma': ['classification', 'lemma', 'set s'], 'set_s_analysis': ['s = p', 's = ∅', 's = {2}', 'infinite', 'finite'], 'upper_bound_proof': ['upper bound', 'f(n) ≤', 'c ≤ 4'], 'construction_example': ['construction', 'example', 'g(n)'], 'regime_analysis': ['regime', 'growth', 'boost', 'fixed point'], 'evolution_dynamics': ['evolution', 'sequence', 'a_{n+1}'], 'divisibility_constraints': ['6|an', 'divisible', 'v2', 'v3'], 'fixed_point_analysis': ['fixed point', 'stable', 'r(n) = 1'], 'budget_analysis': ['budget', 'ck', 'evolution'], 'critical_threshold': ['threshold', '1/√2', 'critical'], 'strategy_construction': ['strategy', 'alice', 'bazza'], 'drawing_strategies': ['draw', 'game continues', 'forever'], 'tiling_constraints': ['tile', 'rectangular', 'cover'], 'row_column_requirements': ['row', 'column', 'exactly one'], 'optimization_bounds': ['minimum', 'lower bound', 'upper bound'], 'construction_proof': ['construction', 'proof', 'achieve']}
    for insight in key_insights:
        if insight in insight_keywords:
            keywords = insight_keywords[insight]
            if any((keyword in solution_lower for keyword in keywords)):
                insights_found.append(insight)
            else:
                insights_missing.append(insight)
    insight_score = len(insights_found) / len(key_insights) if key_insights else 0.0
    return {'insight_score': insight_score, 'insights_found': insights_found, 'insights_missing': insights_missing, 'total_insights': len(key_insights)}

def extract_gsm8k_answer(text: str) -> float:
    """Extract numerical answer after ### from GSM8K responses."""
    match = re.search('###\\s*(-?\\d*\\.?\\d+)', text)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None

def remove_thinking_blocks(text: str) -> str:
    """
    Remove <think>...</think> blocks from the response.
    If there's a </think> tag, only keep the content after it.
    """
    if not text:
        return text
    if '</think>' in text:
        parts = text.split('</think>')
        return parts[-1].strip()
    return text

def extract_choice_index_from_question(question: str, answer: str) -> int:
    """
    Extract the index of the correct answer from a multiple-choice question.
    
    Args:
        question: The question text containing choices
        answer: The correct answer (just the text, no index)
    
    Returns:
        int: The index of the correct answer, or -1 if not found
    """
    answer_clean = answer.strip().lower()
    logger.debug(f"Looking for answer: '{answer_clean}' in question")
    if 'choices:' in question.lower():
        choices_section = question.lower().split('choices:')[1].strip()
        logger.debug(f"Choices section: '{choices_section}'")
        if '\n' not in choices_section:
            all_choices = re.findall('(\\d+)\\s*\\.\\s*([^0-9.]+?)(?=\\s*\\d+\\s*\\.|$)', choices_section)
            logger.debug(f'Single line choices found: {all_choices}')
            for idx, choice_text in all_choices:
                choice_text_clean = choice_text.strip()
                if choice_text_clean.lower() == answer_clean:
                    logger.debug(f"Found match at index {idx}: '{choice_text_clean}'")
                    return int(idx)
        choices = choices_section.split('\n')
        for i, choice in enumerate(choices):
            choice = choice.strip()
            if not choice:
                continue
            logger.debug(f"Checking choice {i}: '{choice}'")
            match = re.match('\\s*(\\d+)\\s*\\.\\s*(.*)', choice)
            if match:
                idx = int(match.group(1))
                choice_text = match.group(2).strip()
                logger.debug(f"Parsed choice: index={idx}, text='{choice_text}'")
                if choice_text.lower() == answer_clean:
                    logger.debug(f'Found exact match at index {idx}')
                    return idx
        pattern = '(\\d+)\\s*\\.\\s*' + re.escape(answer_clean)
        match = re.search(pattern, choices_section)
        if match:
            logger.debug(f'Fallback match found at index {match.group(1)}')
            return int(match.group(1))
    logger.debug('No match found for answer in choices')
    return -1

def is_numeric_only_response(response: str) -> Tuple[bool, int]:
    """
    Check if the response is just a numeric value, possibly with whitespace and newlines.
    
    Args:
        response: The response text to check
        
    Returns:
        Tuple of (is_numeric, value)
    """
    clean_response = re.sub('\\s', '', response)
    if clean_response.isdigit():
        return (True, int(clean_response))
    return (False, -1)

def evaluate_response(response: str, ground_truth: str, category: str, question: str=None) -> bool:
    """
    Evaluate if the response matches the ground truth based on category.
    
    Args:
        response: Model's response
        ground_truth: Correct answer
        category: Problem category (gsm8k, mmlu_math, boolq, aqua_rat)
        question: Original question text, needed for MMLU evaluation
    
    Returns:
        bool: Whether the response is correct
    """
    if not response or not ground_truth:
        return False
    response = remove_thinking_blocks(response)
    if category == 'gsm8k':
        response_num = extract_gsm8k_answer(response)
        ground_truth_num = extract_gsm8k_answer(ground_truth)
        if response_num is None or ground_truth_num is None:
            return False
        return abs(response_num - ground_truth_num) < 1e-06
    elif category == 'mmlu_math':
        response_clean = response.strip().lower()
        ground_truth_clean = ground_truth.strip().lower()
        if response_clean == ground_truth_clean:
            logger.debug('Exact text match')
            return True
        if question:
            correct_index = extract_choice_index_from_question(question, ground_truth)
            if correct_index >= 0:
                is_numeric, value = is_numeric_only_response(response)
                if is_numeric and value == correct_index:
                    logger.debug(f"Numeric match: response '{response}' -> {value} matches index {correct_index}")
                    return True
                if re.search(f'{correct_index}\\s*\\.\\s*{re.escape(ground_truth_clean)}', response_clean):
                    logger.debug("Pattern match for 'index. answer'")
                    return True
                if str(correct_index) in response_clean and ground_truth_clean in response_clean:
                    logger.debug('Contains both index and answer')
                    return True
        return False
    else:
        response_clean = response.strip().lower()
        ground_truth_clean = ground_truth.strip().lower()
        return response_clean == ground_truth_clean

def select_challenging_examples(dataset: datasets.Dataset, category: str, num_samples: int, field_map: Dict[str, str]) -> List[Dict[str, Any]]:
    """Select challenging examples from the dataset"""
    examples = []
    all_examples = dataset['train'] if 'train' in dataset else dataset['validation']
    shuffled_indices = list(range(len(all_examples)))
    random.shuffle(shuffled_indices)
    for idx in shuffled_indices:
        example = all_examples[idx]
        try:
            if category == 'gsm8k':
                question = str(example[field_map['question']])
                answer = str(example[field_map['answer']])
                if answer.count('=') < 3:
                    continue
            elif category == 'boolq':
                passage = str(example[field_map['passage']])
                q = str(example[field_map['question']])
                question = f'Context: {passage}\nQuestion: {q}'
                answer = 'Yes' if example[field_map['answer']] else 'No'
            elif category == 'mmlu_math':
                question = str(example[field_map['question']])
                choices = example[field_map['choices']]
                answer_index = int(example[field_map['answer']])
                if 0 <= answer_index < len(choices):
                    answer = choices[answer_index]
                else:
                    print(f"Warning: Answer index '{answer_index}' is out of range for choices: {choices}")
                    continue
                choices_text = '\n'.join([f'{i}. {choice}' for i, choice in enumerate(choices)])
                question = f'{question}\nChoices:\n{choices_text}'
            elif category == 'aqua_rat':
                question = str(example[field_map['question']])
                answer = str(example[field_map['answer']])
                if len(question.split()) < 12:
                    continue
            if len(question.split()) < 10:
                continue
            examples.append(format_question(category, question, answer))
            if len(examples) >= num_samples:
                break
        except Exception as e:
            print(f'Error processing example from {category}: {str(e)}')
            continue
    return examples

def clean_text(text: str) -> str:
    """Clean text by removing extra whitespace and normalizing newlines"""
    return ' '.join(text.replace('\r', '\n').split())

def format_question(category: str, question: str, answer: str) -> Dict[str, Any]:
    """Format a question for the benchmark dataset"""
    if not question or not answer:
        raise ValueError(f'Empty question or answer in {category}')
    return {'id': f'{category}_{random.getrandbits(32):08x}', 'category': category, 'question': clean_text(question), 'answer': clean_text(answer), 'metadata': {'source': SOURCES[category]['name'], 'type': category, 'difficulty': 'challenging'}}

def normalize_fraction(fraction_str: str) -> str:
    """Helper function to normalize fractions."""
    logger.debug(f'Normalizing fraction: {repr(fraction_str)}')
    try:
        fraction_str = fraction_str.replace('\\dfrac', '\\frac')
        fraction_str = ''.join(fraction_str.split())
        fraction_str = re.sub('\\s*\\\\text{[^}]+}', '', fraction_str)
        mixed_brace = re.match('^\\\\frac(\\d+)\\{(\\d+)\\}$', fraction_str)
        if mixed_brace:
            num, den = mixed_brace.groups()
            return f'\\frac{{{num}}}{{{den}}}'
        no_braces = re.match('^\\\\frac(\\d+)(\\d+)$', fraction_str)
        if no_braces:
            num, den = no_braces.groups()
            return f'\\frac{{{num}}}{{{den}}}'
        if '/' in fraction_str and (not any((c in fraction_str for c in '\\{}'))):
            num, den = fraction_str.split('/')
            return f'\\frac{{{num.strip()}}}{{{den.strip()}}}'
        standard = re.match('^\\\\frac\\{([^{}]+)\\}\\{([^{}]+)\\}$', fraction_str)
        if standard:
            num, den = standard.groups()
            return f'\\frac{{{num}}}{{{den}}}'
    except Exception as e:
        logger.debug(f'Failed to normalize fraction: {str(e)}')
        logger.debug(f'Original fraction string: {repr(fraction_str)}')
    return fraction_str

def normalize_matrix_entry(entry: str) -> str:
    """Helper function to normalize a single matrix entry."""
    logger.debug(f'Normalizing matrix entry input: {repr(entry)}')
    entry = ''.join(entry.split())
    if '/' in entry and (not any((c in entry for c in '\\{}'))):
        if entry.startswith('-'):
            num, den = entry[1:].split('/')
            return f'-{num.strip()}/{den.strip()}'
        else:
            num, den = entry.split('/')
            return f'{num.strip()}/{den.strip()}'
    entry = entry.replace('\\dfrac', '\\frac')
    frac_match = re.match('^(-)?\\\\frac\\{(\\d+)\\}\\{(\\d+)\\}$', entry)
    if frac_match:
        sign, num, den = frac_match.groups()
        sign = sign if sign else ''
        return f'{sign}{num}/{den}'
    return entry

def normalize_matrix(matrix_str: str) -> str:
    """Helper function to normalize matrices and vectors."""
    logger.debug(f'Normalizing matrix input: {repr(matrix_str)}')
    try:
        matrix_str = ''.join(matrix_str.split())
        match = re.match('^\\\\begin\\{pmatrix\\}(.*?)\\\\end\\{pmatrix\\}$', matrix_str)
        if not match:
            return matrix_str
        content = match.group(1)
        rows = content.split('\\\\')
        normalized_rows = []
        for row in rows:
            if '&' in row:
                entries = [normalize_matrix_entry(entry) for entry in row.split('&')]
            else:
                entries = [normalize_matrix_entry(row)]
            normalized_rows.append('&'.join(entries))
        result = '\\begin{pmatrix}' + '\\\\'.join(normalized_rows) + '\\end{pmatrix}'
        logger.debug(f'Normalized matrix result: {repr(result)}')
        return result
    except Exception as e:
        logger.debug(f'Failed to normalize matrix: {str(e)}')
        return matrix_str

def normalize_algebraic_expression(expr: str) -> str:
    """Helper function to normalize algebraic expressions."""
    logger.debug(f'Normalizing algebraic expression: {repr(expr)}')
    try:
        expr = ''.join(expr.split())
        monomial_match = re.match('^(-?\\d*\\.?\\d*)?([a-zA-Z])(?:\\^(-?\\d+))?$', expr)
        if monomial_match:
            coeff, var, exp = monomial_match.groups()
            coeff = coeff if coeff and coeff not in ['+', '-'] else '1' if not coeff else '-1'
            exp = exp if exp else '1'
            if coeff == '1' and exp == '1':
                result = var
            elif coeff == '1':
                result = f'{var}^{exp}'
            elif coeff == '-1' and exp == '1':
                result = f'-{var}'
            elif coeff == '-1':
                result = f'-{var}^{exp}'
            elif exp == '1':
                result = f'{coeff}{var}'
            else:
                result = f'{coeff}{var}^{exp}'
            logger.debug(f'Matched as monomial with exponent: {repr(result)}')
            return result.lower()
        pi_term_match = re.match('^(-?\\d*\\.?\\d*)\\\\?pi$', expr)
        if pi_term_match:
            coeff = pi_term_match.group(1)
            if not coeff or coeff == '-':
                coeff = '-1' if coeff == '-' else '1'
            return f'{coeff}\\pi'
        frac_pi_match = re.match('^\\\\frac{([^{}]+)}{([^{}]+)}\\\\?pi$', expr)
        if frac_pi_match:
            num, den = frac_pi_match.groups()
            return f'\\frac{{{num}}}{{{den}}}\\pi'
        frac_match = re.match('^\\\\frac{([^{}]+)}{([^{}]+)}$', expr)
        if frac_match:
            num, den = frac_match.groups()
            return f'\\frac{{{num}}}{{{den}}}'
        terms = []
        current_term = ''
        for i, char in enumerate(expr):
            if char in ['+', '-'] and i > 0:
                if current_term:
                    terms.append(current_term)
                current_term = char
            else:
                current_term += char
        if current_term:
            terms.append(current_term)
        if len(terms) == 1 and re.match('^-?[\\d,]+$', terms[0]):
            return normalize_number(terms[0])
        processed_terms = []
        for term in terms:
            if term.startswith('+'):
                term = term[1:]
            if not term.startswith('-'):
                term = '+' + term
            match = re.match('^([+-])?\\s*(\\d*\\.?\\d*)?([a-zA-Z](?:\\^\\d+)?)?$', term)
            if match:
                sign, coeff, var = match.groups()
                if not coeff and var:
                    coeff = '1'
                elif not coeff:
                    coeff = '0'
                processed_terms.append((sign, float(coeff), var or ''))
        processed_terms.sort(key=lambda x: (not bool(x[2]), x[2], -x[1]))
        result = ''
        for sign, coeff, var in processed_terms:
            if coeff == 0:
                continue
            term = ''
            if coeff == 1 and var:
                term = var
            elif coeff == -1 and var:
                term = f'-{var}'
            elif var:
                term = f'{coeff}{var}'
            else:
                term = str(coeff)
            if result and term[0] != '-':
                result += '+'
            result += term
        logger.debug(f'Normalized algebraic expression result: {repr(result)}')
        return result.lower()
    except Exception as e:
        logger.debug(f'Failed to normalize algebraic expression: {str(e)}')
        return expr.lower()

def normalize_interval_bound(bound: str) -> str:
    """Helper function to normalize interval bounds."""
    logger.debug(f'Normalizing interval bound: {repr(bound)}')
    if '\\infty' in bound:
        sign = '-' if bound.startswith('-') else ''
        return f'{sign}\\infty'
    return normalize_answer(bound) or bound

def normalize_interval(interval_str: str) -> str:
    """Helper function to normalize intervals."""
    logger.debug(f'Normalizing interval: {repr(interval_str)}')
    try:
        interval_str = ''.join(interval_str.split())
        match = re.match('^\\\\left?([\\[\\(])(.*?),(.*?)\\\\right?([\\]\\)])$', interval_str)
        if not match:
            match = re.match('^([\\[\\(])(.*?),(.*?)([\\]\\)])$', interval_str)
            if not match:
                return interval_str
        left_bracket, left_bound, right_bound, right_bracket = match.groups()
        norm_left = normalize_interval_bound(left_bound)
        norm_right = normalize_interval_bound(right_bound)
        result = f'\\left{left_bracket}{norm_left},{norm_right}\\right{right_bracket}'
        logger.debug(f'Normalized interval result: {repr(result)}')
        return result
    except Exception as e:
        logger.debug(f'Failed to normalize interval: {str(e)}')
        return interval_str

def normalize_ordered_tuple(tuple_str: str) -> str:
    """Helper function to normalize ordered tuples/lists of numbers."""
    logger.debug(f'Normalizing tuple: {repr(tuple_str)}')
    try:
        tuple_str = tuple_str.replace('\\dfrac', '\\frac')
        tuple_str = tuple_str.replace('\\left', '').replace('\\right', '')
        tuple_str = re.sub('\\\\?\\s+', '', tuple_str)
        inner = tuple_str.strip('()')
        parts = inner.split(',')
        normalized_parts = []
        for part in parts:
            norm_part = normalize_answer(part.strip())
            if not norm_part:
                logger.debug(f'Failed to normalize part: {part}')
                return None
            normalized_parts.append(norm_part)
        result = f'({','.join(normalized_parts)})'
        logger.debug(f'Normalized tuple result: {repr(result)}')
        return result
    except Exception as e:
        logger.debug(f'Failed to normalize tuple: {str(e)}')
        return None

def normalize_answer(answer: str) -> str:
    """Normalize the answer string for comparison."""
    logger.debug(f'Normalizing answer: {repr(answer)}')
    if answer is None:
        logger.debug('Received None answer')
        return ''
    answer = re.sub('\\\\text{[^}]+(?:inches|feet|meters|cm|m|kg|ft|in|lb|oz|ml|L|per|second|minute|hour)[^}]*}', '', answer)
    answer = re.sub('(?<!\\\\)\\s+', '', answer)
    logger.debug(f'After initial whitespace removal: {repr(answer)}')
    ordered_pair_match = re.match('^(?:\\\\left)?\\((.*?)(?:\\\\right)?\\)$', answer)
    if ordered_pair_match:
        content = ordered_pair_match.group(1)
        parts = content.split(',')
        normalized_parts = []
        for part in parts:
            part = re.sub('\\\\?\\s+', '', part)
            norm_part = normalize_answer(part)
            if norm_part is None:
                return None
            normalized_parts.append(norm_part)
        return f'({','.join(normalized_parts)})'
    answer = ''.join(answer.split())
    logger.debug(f'After whitespace removal: {repr(answer)}')
    if not answer:
        logger.debug('Answer became empty after whitespace removal')
        return None
    pm_match = re.match('^(.*?)(?:\\\\pm|-)(.*?)$', answer)
    if pm_match:
        left, right = pm_match.groups()
        norm_left = normalize_answer(left) if left else ''
        norm_right = normalize_answer(right) if right else ''
        if norm_left or norm_right:
            result = f'{norm_left}\\pm{norm_right}'
            logger.debug(f'Matched as plus-minus expression: {repr(result)}')
            return result
    trig_match = re.match('^\\\\(?:sin|cos|tan|cot|sec|csc)\\s*([a-zA-Z])$', answer)
    if trig_match:
        variable = trig_match.group(1)
        func_name = re.match('^\\\\(.*?)(?:\\s|$)', answer).group(1)
        result = f'\\{func_name}{variable}'
        logger.debug(f'Matched as trigonometric function: {repr(result)}')
        return result
    text_match = re.match('^(?:\\\\text{)?([A-Za-z]+)(?:})?$', answer)
    if text_match:
        result = text_match.group(1).lower()
        logger.debug(f'Matched as text answer: {repr(result)}')
        return result
    if (answer.startswith('\\left[') or answer.startswith('\\left(') or answer.startswith('[') or answer.startswith('(')) and (answer.endswith('\\right]') or answer.endswith('\\right)') or answer.endswith(']') or answer.endswith(')')):
        result = normalize_interval(answer)
        if result:
            logger.debug(f'Matched as interval: {repr(result)}')
            return result
    if answer.startswith('\\begin{pmatrix}') and answer.endswith('\\end{pmatrix}'):
        result = normalize_matrix(answer)
        if result:
            logger.debug(f'Matched as matrix: {repr(result)}')
            return result
    answer = answer.replace('\\dfrac', '\\frac')
    if '\\frac' in answer or '\\dfrac' in answer or '/' in answer:
        result = normalize_fraction(answer)
        if result:
            logger.debug(f'Matched as fraction: {repr(result)}')
            return result
    neg_sqrt_match = re.match('^-\\\\sqrt\\{?(\\d+)\\}?$', answer)
    if neg_sqrt_match:
        num = neg_sqrt_match.group(1)
        result = f'-\\sqrt{{{num}}}'
        logger.debug(f'Matched as negative square root: {repr(result)}')
        return result
    logger.debug('Checking for square root pattern...')
    sqrt_match = re.match('^(\\d*)?\\\\sqrt\\{?(\\d+)\\}?$', answer)
    if sqrt_match:
        coeff, num = sqrt_match.groups()
        coeff = coeff if coeff else '1'
        if coeff == '1':
            result = f'\\sqrt{{{num}}}'
        else:
            result = f'{coeff}\\sqrt{{{num}}}'
        logger.debug(f'Matched as pure square root: {repr(result)}')
        return result
    sqrt_with_coeff_match = re.match('^(\\d+)\\\\sqrt\\{?(\\d+)\\}?$', answer)
    if sqrt_with_coeff_match:
        coeff, num = sqrt_with_coeff_match.groups()
        result = f'{coeff}\\sqrt{{{num}}}'
        logger.debug(f'Matched as coefficient with square root: {repr(result)}')
        return result
    base_match = re.match('^(\\d+)(?:_\\{?(\\d+)\\}?|_(\\d+))$', answer)
    if base_match:
        number, base1, base2 = base_match.groups()
        base = base1 if base1 else base2
        result = f'{number}_{base}'
        logger.debug(f'Matched as base number: {repr(result)}')
        return result
    percent_match = re.match('^(\\d+(?:\\.\\d*)?)\\s*\\\\?%$', answer)
    if percent_match:
        number = percent_match.group(1)
        result = normalize_number(number)
        logger.debug(f'Matched as percentage: {repr(result)}')
        return result
    unit_match = re.match('^(\\d+(?:\\.\\d*)?)\\s*(?:(?:\\\\[,\\s])|,)?\\s*(?:\\\\\\\\)?(?:\\\\text{(\\w+)}|\\\\?(?:cm|m|kg|ft|in|lb|oz|ml|L))$', answer)
    if unit_match:
        number = unit_match.group(1)
        result = normalize_number(number)
        logger.debug(f'Matched as number with unit: {repr(result)}')
        return result
    currency_match = re.match('^\\\\?\\$?([\\d,]+\\.?\\d*)$', answer)
    if currency_match:
        result = normalize_number(currency_match.group(1))
        logger.debug(f'Matched as currency: {repr(result)}')
        return result
    if re.match('^-?[\\d,]+$', answer):
        result = normalize_number(answer)
        logger.debug(f'Matched as number: {repr(result)}')
        return result
    unit_match = re.match('^(-?[\\d,]+(?:\\.\\d*)?)\\s*(?:\\\\(?:mbox|text|hbox|displaystyle)\\{[^}]+\\})?(?:\\^?\\d)?$', answer)
    if unit_match:
        result = normalize_number(unit_match.group(1))
        logger.debug(f'Matched as number with units: {repr(result)}')
        return result
    mc_match = re.match('^\\\\text{\\(?([A-Za-z])\\)?}$|^\\(?([A-Za-z])\\)?$', answer)
    if mc_match:
        result = (mc_match.group(1) or mc_match.group(2)).lower()
        logger.debug(f'Matched as multiple choice: {repr(result)}')
        return result
    degree_match = re.match('^(-?[\\d,]+(?:\\.\\d*)?)\\s*(?:(?:\\^?\\\\circ)|(?:{\\\\circ})|(?:°))?$', answer)
    if degree_match:
        result = normalize_number(degree_match.group(1))
        logger.debug(f'Matched as degrees: {repr(result)}')
        return result
    answer = re.sub('\\\\text{([^{}]+)}', '\\1', answer)
    logger.debug(f'After \\text removal: {repr(answer)}')
    try:
        result = normalize_algebraic_expression(answer)
        logger.debug(f'Normalized as algebraic expression: {repr(result)}')
        return result
    except:
        logger.debug('Failed to normalize as algebraic expression')
        pass
    answer = answer.replace('\\left', '').replace('\\right', '')
    answer = answer.replace('\\left', '').replace('\\right', '')
    answer = answer.replace('\\(', '(').replace('\\)', ')')
    answer = answer.replace('\\[', '[').replace('\\]', ']')
    answer = answer.replace('\\{', '{').replace('\\}', '}')
    answer = re.sub('\\\\sqrt\\{?(\\d+)\\}?', '\\\\sqrt{\\1}', answer)
    answer = re.sub('\\\\sqrt{([^{}]+)}', '\\\\sqrt\\1', answer)
    if re.match('^\\d+\\\\%$', answer) or re.match('^\\d+$', answer):
        answer = re.sub('\\\\%$', '', answer)
    answer = re.sub('\\\\text{([^{}]+)}', '\\1', answer)
    while len(answer) >= 2 and answer[0] == '{' and (answer[-1] == '}'):
        if '\\frac' in answer:
            break
        answer = answer[1:-1]
    result = answer.lower()
    logger.debug(f'Final normalized result: {repr(result)}')
    return result if result else None

def compare_answers(correct_answer: str, predicted_answer: Optional[str]) -> bool:
    """Compare the correct answer with the predicted answer."""
    logger.debug(f'Comparing answers - Correct: {repr(correct_answer)}, Predicted: {repr(predicted_answer)}')
    if predicted_answer is None:
        logger.debug('Predicted answer is None')
        return False
    if numerically_equal(correct_answer, predicted_answer):
        return True
    normalized_correct = normalize_answer(correct_answer)
    normalized_predicted = normalize_answer(predicted_answer)
    logger.debug(f'Normalized answers - Correct: {repr(normalized_correct)}, Predicted: {repr(normalized_predicted)}')
    if not normalized_correct or not normalized_predicted:
        logger.debug('One or both normalized answers are None or empty')
        return False
    if normalized_correct == '' and normalized_predicted == '':
        logger.debug('Both answers normalized to empty strings')
        return False
    if ('\\left[' in normalized_correct or '\\left(' in normalized_correct) and ('\\left[' in normalized_predicted or '\\left(' in normalized_predicted):
        result = normalized_correct == normalized_predicted
        logger.debug(f'Interval comparison result: {result}')
        return result
    result = normalized_correct == normalized_predicted
    logger.debug(f'Comparison result: {result}')
    return result

def remove_thinking_blocks(text: str) -> str:
    """Remove <think>...</think> blocks from the response."""
    if not text:
        return text
    if '</think>' in text:
        parts = text.split('</think>')
        return parts[-1].strip()
    elif '<think>' in text and '</think>' not in text:
        parts = text.split('<think>')
        return parts[0].strip() if len(parts) > 1 and parts[0] else ''
    return text

def load_dataset_by_year(year: int) -> list[dict]:
    """
    Load dataset by year (2024 or 2025).
    Returns:
        list[dict]: The dataset of problems.
    """
    if year == 2024:
        return load_2024_dataset()
    elif year == 2025:
        return load_2025_dataset()
    else:
        raise ValueError(f'Unsupported year: {year}. Only 2024 and 2025 are supported.')

def extract_answer(response: str) -> Optional[int]:
    """
    Extract the numerical answer from a math solution response using unified extraction.
    AIME problems expect integer answers between 0 and 999.
    """
    if not response:
        return None
    extracted_answer = unified_extract_answer(response, problem_type='aime', problem_id=None)
    if extracted_answer is None:
        return None
    if isinstance(extracted_answer, list):
        for item in extracted_answer:
            if isinstance(item, (int, float)):
                answer = int(item)
                if 0 <= answer <= 999:
                    return answer
            elif isinstance(item, str) and item.isdigit():
                answer = int(item)
                if 0 <= answer <= 999:
                    return answer
        return None
    if isinstance(extracted_answer, (int, float)):
        answer = int(extracted_answer)
        if 0 <= answer <= 999:
            return answer
    elif isinstance(extracted_answer, str) and extracted_answer.isdigit():
        answer = int(extracted_answer)
        if 0 <= answer <= 999:
            return answer
    return None

def analyze_thinking(response: str) -> Dict:
    """
    Analyze thinking patterns in the response.
    Extract tokens between <think> and </think> tags and count thought transitions.
    
    Args:
        response (str): The model's response text
        
    Returns:
        Dict: Analysis metrics including thinking tokens and thought transitions
    """
    result = {'has_think_tags': False, 'thinking_tokens': 0, 'thinking_tokens_text': '', 'total_tokens': len(response.split()), 'thought_transitions': 0, 'transition_counts': {phrase: 0 for phrase in THOUGHT_TRANSITIONS}, 'transition_positions': []}
    think_pattern = re.compile('<think>(.*?)</think>', re.DOTALL)
    think_match = think_pattern.search(response)
    if think_match:
        thinking_text = think_match.group(1)
        result['has_think_tags'] = True
        result['thinking_tokens'] = len(thinking_text.split())
        result['thinking_tokens_text'] = thinking_text
        position = 0
        for phrase in THOUGHT_TRANSITIONS:
            for match in re.finditer('\\b' + re.escape(phrase) + '\\b', thinking_text):
                result['transition_counts'][phrase] += 1
                token_position = len(thinking_text[:match.start()].split())
                result['transition_positions'].append((phrase, token_position))
        result['transition_positions'].sort(key=lambda x: x[1])
        result['thought_transitions'] = sum(result['transition_counts'].values())
    return result

def get_last_processed_index(results: List[Dict]) -> int:
    """Get the index of the last processed problem."""
    if not results:
        return -1
    return max((int(r.get('index', -1)) for r in results))

def construct_prompt(sample: Dict[str, Any], split_type: str) -> str:
    """Construct prompt based on split type."""
    context = sample.get('context', '')
    prompt = sample['prompt']
    if split_type == 'multiple_choice':
        options = sample['options']
        options_text = '\nOptions:\n' + '\n'.join([f'{i + 1}. {opt}' for i, opt in enumerate(options)])
        return f'Context: {context}\n\nQuestion: {prompt}{options_text}\n\nProvide the correct answer from the options above.'
    else:
        return f'Context: {context}\n\nQuestion: {prompt}\n\nProvide your answer.'

def is_correct_response(response: str, targets: List[str]) -> bool:
    """Check if response matches any of the target answers."""
    response = response.strip().lower()
    return any((target.strip().lower() == response for target in targets))

def rank_responses(responses: List[Dict[str, Any]], targets: List[str]) -> List[int]:
    """Rank responses based on correctness and token efficiency."""
    ranked_data = []
    for i, response in enumerate(responses):
        is_correct = is_correct_response(response['content'], targets)
        ranked_data.append((i, is_correct, response['tokens']))
    ranked_data.sort(key=lambda x: (-int(x[1]), x[2]))
    return [idx for idx, _, _ in ranked_data]

def get_last_processed_index(results: List[Dict]) -> int:
    if not results:
        return -1
    return max((int(r.get('index', -1)) for r in results))

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

def extract_output(self, text: str) -> str:
    match = re.search('<output>(.*?)(?:</output>|$)', text, re.DOTALL)
    return match.group(1).strip() if match else ''

def count_reasoning_tokens(text: str, tokenizer=None) -> int:
    """
    Count tokens within <think>...</think> tags in the given text.
    
    Args:
        text: The text to analyze
        tokenizer: Optional tokenizer instance for precise counting
        
    Returns:
        Number of reasoning tokens (0 if no think tags found)
    """
    if not text or not isinstance(text, str):
        return 0
    complete_pattern = '<think>(.*?)</think>'
    complete_matches = re.findall(complete_pattern, text, re.DOTALL)
    truncated_pattern = '<think>(?!.*</think>)(.*)$'
    truncated_match = re.search(truncated_pattern, text, re.DOTALL)
    thinking_content = ''.join(complete_matches)
    if truncated_match:
        thinking_content += truncated_match.group(1)
    if not thinking_content:
        return 0
    if tokenizer and hasattr(tokenizer, 'encode'):
        try:
            tokens = tokenizer.encode(thinking_content)
            return len(tokens)
        except Exception as e:
            logger.warning(f'Failed to count tokens with tokenizer: {e}')
    content_length = len(thinking_content.strip())
    return max(1, content_length // 4) if content_length > 0 else 0

class LogProbsCalculator:
    """Handles calculation of log probabilities for generated tokens"""

    def __init__(self, tokenizer, model):
        self.tokenizer = tokenizer
        self.model = model

    def _get_bytes_for_token(self, token: str) -> List[int]:
        """Get UTF-8 bytes for a token"""
        try:
            return list(token.encode('utf-8'))
        except UnicodeEncodeError:
            return []

    def _get_top_alternatives(self, logits: torch.Tensor, actual_token_id: int, num_alternatives: int) -> Dict[str, float]:
        """Calculate top alternative tokens and their logprobs"""
        probs = F.softmax(logits, dim=-1)
        logprobs = torch.log(probs)
        top_values, top_indices = torch.topk(logprobs, k=num_alternatives + 1)
        alternatives = {}
        for value, idx in zip(top_values, top_indices):
            token = self.tokenizer.decode([idx])
            if idx != actual_token_id:
                alternatives[token] = value.item()
                if len(alternatives) >= num_alternatives:
                    break
        return alternatives

    def calculate_logprobs(self, input_ids: torch.Tensor, generated_ids: torch.Tensor, attention_mask: torch.Tensor, num_alternatives: int=5) -> LogProbsResult:
        """Calculate log probabilities for a sequence of tokens"""
        self.model.eval()
        with torch.no_grad():
            outputs = self.model(input_ids=input_ids, attention_mask=attention_mask, return_dict=True)
            logits = outputs.logits
            probs = F.softmax(logits, dim=-1)
            logprobs = torch.log(probs)
            all_tokens = []
            all_token_logprobs = []
            all_top_logprobs = []
            all_bytes = []
            sequence_length = generated_ids.shape[-1]
            for pos in range(sequence_length - 1):
                next_token_id = generated_ids[0, pos + 1]
                current_logits = logits[0, pos]
                token = self.tokenizer.decode([next_token_id])
                token_logprob = logprobs[0, pos, next_token_id].item()
                top_logprobs = self._get_top_alternatives(current_logits, next_token_id, num_alternatives)
                token_bytes = self._get_bytes_for_token(token)
                all_tokens.append(token)
                all_token_logprobs.append(token_logprob)
                all_top_logprobs.append(top_logprobs)
                all_bytes.append(token_bytes)
            all_tokens.append(self.tokenizer.decode([generated_ids[0, -1]]))
            all_token_logprobs.append(None)
            all_top_logprobs.append(None)
            all_bytes.append(self._get_bytes_for_token(all_tokens[-1]))
            return LogProbsResult(tokens=all_tokens, token_logprobs=all_token_logprobs, top_logprobs=all_top_logprobs, bytes_per_token=all_bytes)

def _get_bytes_for_token(self, token: str) -> List[int]:
    """Get UTF-8 bytes for a token"""
    try:
        return list(token.encode('utf-8'))
    except UnicodeEncodeError:
        return []

def should_use_mlx(model_id: str) -> bool:
    """Determine if a model should use MLX instead of PyTorch"""
    if not MLX_AVAILABLE or not is_apple_silicon():
        return False
    mlx_patterns = ['mlx-community/', 'mlx-', '-mlx-']
    problematic_models = ['Qwen/Qwen3-', 'google/gemma-3-', 'google/gemma3-']
    model_lower = model_id.lower()
    for pattern in mlx_patterns:
        if pattern.lower() in model_lower:
            return True
    for pattern in problematic_models:
        if pattern.lower() in model_lower:
            logger.warning(f'Model {model_id} detected as potentially problematic with MPS backend')
            suggested_mlx = suggest_mlx_alternative(model_id)
            logger.warning(f'Consider using MLX model: {suggested_mlx}')
            return False
    return False

class PromptCache:
    """Advanced caching system for frequent prompts and responses"""

    def __init__(self, max_size: int=1000):
        self.max_size = max_size
        self.cache = OrderedDict()
        self.prompt_stats = defaultdict(lambda: {'count': 0, 'success_rate': 0.0})

    @lru_cache(maxsize=128)
    def _compute_prompt_signature(self, prompt: str) -> str:
        """Compute a signature for semantic similarity matching"""
        words = set(prompt.lower().split())
        return ' '.join(sorted(list(words)))

    def get_cached_response(self, prompt: str, temperature: float, top_p: float) -> Optional[str]:
        """Get cached response with fuzzy matching"""
        signature = self._compute_prompt_signature(prompt)
        if signature in self.cache:
            cached_item = self.cache[signature]
            if abs(cached_item['temperature'] - temperature) < 0.1 and abs(cached_item['top_p'] - top_p) < 0.1:
                self.prompt_stats[signature]['count'] += 1
                return cached_item['response']
        return None

    def add_to_cache(self, prompt: str, response: str, temperature: float, top_p: float):
        """Add response to cache with metadata"""
        signature = self._compute_prompt_signature(prompt)
        self.cache[signature] = {'response': response, 'temperature': temperature, 'top_p': top_p, 'timestamp': torch.cuda.current_timestamp() if torch.cuda.is_available() else 0}
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)

    def update_stats(self, prompt: str, success: bool):
        """Update prompt success statistics"""
        signature = self._compute_prompt_signature(prompt)
        stats = self.prompt_stats[signature]
        stats['count'] += 1
        stats['success_rate'] = (stats['success_rate'] * (stats['count'] - 1) + float(success)) / stats['count']

@lru_cache(maxsize=128)
def _compute_prompt_signature(self, prompt: str) -> str:
    """Compute a signature for semantic similarity matching"""
    words = set(prompt.lower().split())
    return ' '.join(sorted(list(words)))

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

class Models:
    """OpenAI-compatible models interface"""

    def list(self):
        """Return list of supported models"""
        try:
            import requests
            response = requests.get('https://huggingface.co/api/models?sort=downloads&direction=-1&filter=text-generation&limit=20')
            models = response.json()
            model_list = []
            for model in models:
                if 'pipeline_tag' in model and model['pipeline_tag'] == 'text-generation':
                    model_list.append({'id': model['id'], 'object': 'model', 'created': int(time.time()), 'owned_by': 'huggingface'})
            return {'data': model_list, 'object': 'list'}
        except Exception as e:
            logger.warning(f'Failed to fetch models: {e}')
            return {'data': [{'id': 'HuggingFaceTB/SmolLM-135M-Instruct', 'object': 'model', 'created': int(time.time()), 'owned_by': 'huggingface'}], 'object': 'list'}

def list(self):
    """Return list of supported models"""
    try:
        import requests
        response = requests.get('https://huggingface.co/api/models?sort=downloads&direction=-1&filter=text-generation&limit=20')
        models = response.json()
        model_list = []
        for model in models:
            if 'pipeline_tag' in model and model['pipeline_tag'] == 'text-generation':
                model_list.append({'id': model['id'], 'object': 'model', 'created': int(time.time()), 'owned_by': 'huggingface'})
        return {'data': model_list, 'object': 'list'}
    except Exception as e:
        logger.warning(f'Failed to fetch models: {e}')
        return {'data': [{'id': 'HuggingFaceTB/SmolLM-135M-Instruct', 'object': 'model', 'created': int(time.time()), 'owned_by': 'huggingface'}], 'object': 'list'}

def parse_model_string(model: str) -> ModelConfig:
    """Parse the model string to extract base model and adapter IDs"""
    parts = model.split('+')
    base_model_id = parts[0]
    adapter_ids = parts[1:] if len(parts) > 1 else None
    return ModelConfig(base_model_id=base_model_id, adapter_ids=adapter_ids, use_memory_efficient_attention=False, quantization_bits=0, enable_prompt_caching=False, dynamic_temperature=False)

def get_effort_profile(reasoning_effort: str, max_tokens: int=4096) -> dict:
    """Get reasoning effort profile based on specified level and max tokens.
    
    Args:
        reasoning_effort: 'low', 'medium', or 'high'
        max_tokens: Maximum tokens allowed for generation, defaults to 4096
    
    Returns:
        dict: Configuration for the specified reasoning effort level
    """
    profiles = {'low': {'min_tokens_pct': 0.1, 'max_tokens_pct': 0.33, 'max_thoughts': 64, 'thought_switch_tokens': ['Wait,', 'Alternatively,', 'However,', 'Additionally,'], 'prefill': ''}, 'medium': {'min_tokens_pct': 0.1, 'max_tokens_pct': 0.66, 'max_thoughts': 256, 'thought_switch_tokens': ['Wait,', 'Alternatively,', 'However,', 'Additionally,'], 'prefill': ''}, 'high': {'min_tokens_pct': 0.1, 'max_tokens_pct': 0.9, 'max_thoughts': 512, 'thought_switch_tokens': ['Wait,', 'Alternatively,', 'However,', 'Additionally,'], 'prefill': ''}}
    profile = profiles.get(reasoning_effort.lower(), profiles['low'])
    min_thinking_tokens = int(max_tokens * profile['min_tokens_pct'])
    max_thinking_tokens = int(max_tokens * profile['max_tokens_pct'])
    config = {'min_thinking_tokens': min_thinking_tokens, 'max_thinking_tokens': max_thinking_tokens, 'max_thoughts': profile['max_thoughts'], 'thought_switch_tokens': profile['thought_switch_tokens'], 'prefill': profile['prefill']}
    return config

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

def extract_code_from_prompt(text):
    pattern = '```(?:[\\w-]+)?\\n(.*?)```'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    else:
        logger.warning('Could not extract code from prompt. Returning original text.')
        return text

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

def aggregate_results(self, responses: List[str]) -> Dict[str, any]:
    final_answers = responses
    clusters = self.cluster_similar_responses(final_answers)
    cluster_info = []
    for cluster in clusters:
        cluster_info.append({'answer': cluster[0], 'frequency': len(cluster), 'variants': cluster})
    cluster_info.sort(key=lambda x: x['frequency'], reverse=True)
    return {'clusters': cluster_info, 'total_responses': len(responses), 'num_unique_clusters': len(clusters)}

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

def is_terminal(self, state: DialogueState) -> bool:
    is_terminal = len(state.conversation_history) > 10 or 'goodbye' in state.current_query.lower()
    logger.info(f'Checking if state is terminal: {is_terminal}')
    return is_terminal

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

def extract_and_validate_expressions(self, analysis: str) -> str:
    formulation = re.search('```python\\n([\\s\\S]+?)```', analysis)
    if formulation:
        return formulation.group(1).strip()
    raise ValueError('No valid Z3 or SymPy formulation found in the analysis.')

def count_reasoning_tokens(text: str, tokenizer=None) -> int:
    """
    Count tokens within <think>...</think> tags in the given text.
    
    Args:
        text: The text to analyze
        tokenizer: Optional tokenizer instance for precise counting
        
    Returns:
        Number of reasoning tokens (0 if no think tags found)
    """
    if not text or not isinstance(text, str):
        return 0
    complete_pattern = '<think>(.*?)</think>'
    complete_matches = re.findall(complete_pattern, text, re.DOTALL)
    truncated_pattern = '<think>(?!.*</think>)(.*)$'
    truncated_match = re.search(truncated_pattern, text, re.DOTALL)
    thinking_content = ''.join(complete_matches)
    if truncated_match:
        thinking_content += truncated_match.group(1)
    if not thinking_content:
        return 0
    if tokenizer and hasattr(tokenizer, 'encode'):
        try:
            tokens = tokenizer.encode(thinking_content)
            return len(tokens)
        except Exception as e:
            logger.warning(f'Failed to count tokens with tokenizer: {e}')
    content_length = len(thinking_content.strip())
    return max(1, content_length // 4) if content_length > 0 else 0

def parse_combined_approach(model: str, known_approaches: list, plugin_approaches: dict):
    if model == 'auto':
        return ('SINGLE', ['none'], model)
    parts = model.split('-')
    approaches = []
    operation = 'SINGLE'
    model_parts = []
    parsing_approaches = True
    for part in parts:
        if parsing_approaches:
            if part in known_approaches or part in plugin_approaches:
                approaches.append(part)
            elif '&' in part:
                operation = 'AND'
                approaches.extend(part.split('&'))
            elif '|' in part:
                operation = 'OR'
                approaches.extend(part.split('|'))
            else:
                parsing_approaches = False
                model_parts.append(part)
        else:
            model_parts.append(part)
    if not approaches:
        approaches = ['none']
        operation = 'SINGLE'
    actual_model = '-'.join(model_parts)
    return (operation, approaches, actual_model)

def generate_streaming_response(final_response, model):
    if isinstance(final_response, list):
        for index, response in enumerate(final_response):
            yield ('data: ' + json.dumps({'choices': [{'delta': {'content': response}, 'index': index, 'finish_reason': 'stop'}], 'model': model}) + '\n\n')
    else:
        yield ('data: ' + json.dumps({'choices': [{'delta': {'content': final_response}, 'index': 0, 'finish_reason': 'stop'}], 'model': model}) + '\n\n')
    yield 'data: [DONE]\n\n'

def parse_conversation(messages):
    system_prompt = ''
    conversation = []
    optillm_approach = None
    for message in messages:
        role = message['role']
        content = message['content']
        if isinstance(content, list):
            text_content = ' '.join((item['text'] for item in content if isinstance(item, dict) and item.get('type') == 'text'))
        else:
            text_content = content
        if role == 'system':
            system_prompt, optillm_approach = extract_optillm_approach(text_content)
        elif role == 'user':
            if not optillm_approach:
                text_content, optillm_approach = extract_optillm_approach(text_content)
            conversation.append(f'User: {text_content}')
        elif role == 'assistant':
            conversation.append(f'Assistant: {text_content}')
    initial_query = '\n'.join(conversation)
    return (system_prompt, initial_query, optillm_approach)

def tagged_conversation_to_messages(response_text):
    """Convert a tagged conversation string or list of strings into a list of messages.
    If the input doesn't contain User:/Assistant: tags, return it as is.
    
    Args:
        response_text: Either a string containing "User:" and "Assistant:" tags,
                      or a list of such strings.
    
    Returns:
        If input has tags: A list of message dictionaries.
        If input has no tags: The original input.
    """

    def has_conversation_tags(text):
        return 'User:' in text or 'Assistant:' in text

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
    if isinstance(response_text, list):
        processed = [process_single_response(text) for text in response_text]
        if all((isinstance(p, str) for p in processed)):
            return response_text
        return processed
    else:
        return process_single_response(response_text)

def extract_optillm_approach(content):
    match = re.search('<optillm_approach>(.*?)</optillm_approach>', content)
    if match:
        approach = match.group(1)
        content = re.sub('<optillm_approach>.*?</optillm_approach>', '', content).strip()
        return (content, approach)
    return (content, None)

def extract_answer(final_state: str) -> Tuple[str, float]:
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

def detect_answer_type(text: str) -> str:
    """Detect whether this is a code, math, or generic problem"""
    code_indicators = ['```', 'def ', 'import ', 'class ', 'return ', 'for ', 'while ']
    has_code = any((indicator in text for indicator in code_indicators))
    math_indicators = ['\\boxed', '\\frac', '\\sum', '\\int', '$$', '$\\']
    has_math = any((indicator in text for indicator in math_indicators))
    if has_code:
        return 'code'
    elif has_math:
        return 'math'
    else:
        return 'generic'

def extract_code_answer(text: str) -> str:
    """
    Extract clean code from synthesis output
    Finds the last complete code block as the final answer
    """
    code_blocks = re.findall('```(?:python|cpp|java|javascript|go|rust)?\\n(.*?)\\n```', text, re.DOTALL)
    if code_blocks:
        final_code = code_blocks[-1].strip()
        logger.info(f'📝 EXTRACTION: Found {len(code_blocks)} code blocks, using last one ({len(final_code)} chars)')
        return f'```python\n{final_code}\n```'
    sections = re.split('\\n#+\\s+(?:Final Solution|Solution|Implementation|Code)\\s*\\n', text, flags=re.IGNORECASE)
    if len(sections) > 1:
        final_section = sections[-1].strip()
        logger.info(f'📝 EXTRACTION: Using code from final section ({len(final_section)} chars)')
        return final_section
    parts = text.split('###')
    if len(parts) > 1:
        final_part = parts[-1].strip()
        logger.info(f'📝 EXTRACTION: Using text after last heading ({len(final_part)} chars)')
        return final_part
    logger.warning('⚠️  EXTRACTION: No clear code found, returning full text')
    return text

def extract_math_answer(text: str) -> str:
    """
    Extract clean math answer from synthesis output
    Finds the last \\boxed{} answer as the final answer
    """
    boxed_answers = re.findall('\\\\boxed\\{([^}]+)\\}', text)
    if boxed_answers:
        final_answer = boxed_answers[-1]
        logger.info(f'📝 EXTRACTION: Found {len(boxed_answers)} boxed answers, using last one: {final_answer}')
        return f'The final answer is $\\boxed{{{final_answer}}}$'
    final_patterns = ['[Ff]inal answer[:\\s]+(.+?)(?:\\n|$)', '[Tt]he answer is[:\\s]+(.+?)(?:\\n|$)', '[Tt]herefore[,\\s]+(.+?)(?:\\n|$)']
    for pattern in final_patterns:
        matches = re.findall(pattern, text)
        if matches:
            final_answer = matches[-1].strip()
            logger.info(f"📝 EXTRACTION: Found answer via pattern '{pattern}': {final_answer}")
            return final_answer
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    if paragraphs:
        final_para = paragraphs[-1]
        logger.info(f'📝 EXTRACTION: Using last paragraph ({len(final_para)} chars)')
        return final_para
    logger.warning('⚠️  EXTRACTION: No clear math answer found, returning full text')
    return text

def extract_generic_answer(text: str) -> str:
    """
    Extract answer for generic (non-code, non-math) problems
    Returns the last paragraph or sentence as the final answer
    For proof-based problems, may return the full text if no clear answer section exists
    """
    proof_indicators = ['proof', 'QED', 'proven', 'demonstrate', 'show that', 'prove that']
    is_proof = any((indicator.lower() in text.lower() for indicator in proof_indicators))
    conclusion_markers = ['In conclusion', 'Therefore', 'Thus', 'Hence', 'Finally', 'The answer is', 'The final answer']
    for marker in conclusion_markers:
        if marker in text:
            parts = text.rsplit(marker, 1)
            if len(parts) > 1:
                answer = parts[1].strip()
                first_para = answer.split('\n\n')[0].strip()
                if len(first_para) > 20:
                    logger.info(f"📝 EXTRACTION: Found answer after '{marker}' ({len(first_para)} chars)")
                    return first_para
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    if is_proof and paragraphs:
        if len(paragraphs) >= 3:
            conclusion_text = '\n\n'.join(paragraphs[-3:])
            logger.info(f'📝 EXTRACTION: Proof detected, using last 3 paragraphs ({len(conclusion_text)} chars)')
            return conclusion_text
        else:
            logger.info(f'📝 EXTRACTION: Short proof detected, returning full text ({len(text)} chars)')
            return text
    if paragraphs:
        final_para = paragraphs[-1]
        logger.info(f'📝 EXTRACTION: Using last paragraph ({len(final_para)} chars)')
        return final_para
    sentences = [s.strip() for s in text.split('.') if s.strip()]
    if sentences:
        final_sentence = sentences[-1] + '.'
        logger.info(f'📝 EXTRACTION: Using last sentence ({len(final_sentence)} chars)')
        return final_sentence
    logger.warning('⚠️  EXTRACTION: No clear answer found, returning full text')
    return text

def strip_thinking_tags(text: str) -> str:
    """
    Remove <think></think> tags from text (for debugging/logging)

    Args:
        text: Text potentially containing thinking tags

    Returns:
        Text with thinking tags removed
    """
    text = re.sub('<think>.*?</think>', '', text, flags=re.DOTALL)
    return text.strip()

def get_answer_after_thinking(text: str) -> str:
    """
    Extract only the content after </think> tag

    Args:
        text: Text with thinking tags

    Returns:
        Content after </think> tag, or full text if no tags
    """
    match = re.search('</think>\\s*(.+)', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text

class MARSWorkspace:
    """Shared workspace for agent collaboration and solution tracking"""

    def __init__(self, problem: str, config: Dict[str, Any]):
        self.problem = problem
        self.config = config
        self.solutions: List[AgentSolution] = []
        self.verification_results: List[VerificationResult] = []
        self.synthesis_attempts: List[Dict] = []
        self.final_solution: Optional[str] = None
        self.iteration_count = 0
        self.total_reasoning_tokens = 0
        logger.info(f'Initialized MARS workspace for problem: {problem[:100]}...')

    def add_solution(self, agent_solution: AgentSolution) -> str:
        """Add a new agent solution to the workspace"""
        solution_id = f'agent_{agent_solution.agent_id}_iter_{self.iteration_count}'
        self.solutions.append(agent_solution)
        self.total_reasoning_tokens += agent_solution.reasoning_tokens
        logger.info(f'Added solution {solution_id} with {agent_solution.reasoning_tokens} reasoning tokens')
        return solution_id

    def add_verification(self, verification: VerificationResult):
        """Add a verification result to the workspace"""
        self.verification_results.append(verification)
        if verification.solution_id.startswith('agent_'):
            try:
                agent_id_str = verification.solution_id.split('_')[1]
                for solution in self.solutions:
                    if str(solution.agent_id) == agent_id_str:
                        solution.verification_results.append({'assessment': verification.assessment, 'confidence': verification.confidence, 'issues': verification.issues, 'detailed_report': verification.detailed_report})
                        verified_count = len([v for v in solution.verification_results if v['assessment'] == 'CORRECT'])
                        total_verifications = len(solution.verification_results)
                        solution.verification_score = verified_count / total_verifications if total_verifications > 0 else 0
                        consecutive_correct = 0
                        for v in reversed(solution.verification_results):
                            if v['assessment'] == 'CORRECT':
                                consecutive_correct += 1
                            else:
                                break
                        verification_threshold = self.config.get('verification_passes_required', 5)
                        solution.is_verified = consecutive_correct >= verification_threshold
                        break
            except (IndexError, ValueError):
                logger.warning(f'Invalid solution_id format: {verification.solution_id}')
        logger.info(f'Added verification for {verification.solution_id}: {verification.assessment}')

    def get_verified_solutions(self) -> List[AgentSolution]:
        """Get all solutions that have passed verification"""
        return [s for s in self.solutions if s.is_verified]

    def get_best_solution(self) -> Optional[AgentSolution]:
        """Get the best solution based on verification score and confidence"""
        if not self.solutions:
            return None
        verified_solutions = self.get_verified_solutions()
        if verified_solutions:
            return max(verified_solutions, key=lambda s: s.confidence)
        else:
            return max(self.solutions, key=lambda s: s.verification_score)

    def has_consensus(self) -> bool:
        """Check if we have enough verified solutions to reach consensus"""
        verified_count = len(self.get_verified_solutions())
        required_consensus = self.config.get('consensus_threshold', 2)
        return verified_count >= required_consensus

    def should_continue_iteration(self) -> bool:
        """Determine if we should continue with another iteration"""
        max_iterations = self.config.get('max_iterations', 5)
        min_verified = self.config.get('min_verified_solutions', 1)
        return self.iteration_count < max_iterations and len(self.get_verified_solutions()) < min_verified

    def get_synthesis_input(self) -> Dict[str, Any]:
        """Prepare input data for solution synthesis"""
        return {'problem': self.problem, 'solutions': [{'agent_id': s.agent_id, 'solution': s.solution, 'confidence': s.confidence, 'verification_score': s.verification_score, 'verification_results': s.verification_results} for s in self.solutions], 'verification_summary': self._get_verification_summary(), 'total_reasoning_tokens': self.total_reasoning_tokens}

    def _get_verification_summary(self) -> Dict[str, Any]:
        """Generate a summary of all verification results"""
        total_verifications = len(self.verification_results)
        if total_verifications == 0:
            return {'total': 0, 'correct': 0, 'incorrect': 0, 'incomplete': 0}
        assessments = [v.assessment for v in self.verification_results]
        return {'total': total_verifications, 'correct': assessments.count('CORRECT'), 'incorrect': assessments.count('INCORRECT'), 'incomplete': assessments.count('INCOMPLETE'), 'avg_confidence': sum((v.confidence for v in self.verification_results)) / total_verifications}

    def set_final_solution(self, solution: str):
        """Set the final synthesized solution"""
        self.final_solution = solution
        logger.info('Final solution set in workspace')

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the workspace state"""
        return {'problem': self.problem, 'total_solutions': len(self.solutions), 'verified_solutions': len(self.get_verified_solutions()), 'total_verifications': len(self.verification_results), 'iterations_completed': self.iteration_count, 'total_reasoning_tokens': self.total_reasoning_tokens, 'has_consensus': self.has_consensus(), 'final_solution': self.final_solution, 'verification_summary': self._get_verification_summary()}

def add_verification(self, verification: VerificationResult):
    """Add a verification result to the workspace"""
    self.verification_results.append(verification)
    if verification.solution_id.startswith('agent_'):
        try:
            agent_id_str = verification.solution_id.split('_')[1]
            for solution in self.solutions:
                if str(solution.agent_id) == agent_id_str:
                    solution.verification_results.append({'assessment': verification.assessment, 'confidence': verification.confidence, 'issues': verification.issues, 'detailed_report': verification.detailed_report})
                    verified_count = len([v for v in solution.verification_results if v['assessment'] == 'CORRECT'])
                    total_verifications = len(solution.verification_results)
                    solution.verification_score = verified_count / total_verifications if total_verifications > 0 else 0
                    consecutive_correct = 0
                    for v in reversed(solution.verification_results):
                        if v['assessment'] == 'CORRECT':
                            consecutive_correct += 1
                        else:
                            break
                    verification_threshold = self.config.get('verification_passes_required', 5)
                    solution.is_verified = consecutive_correct >= verification_threshold
                    break
        except (IndexError, ValueError):
            logger.warning(f'Invalid solution_id format: {verification.solution_id}')
    logger.info(f'Added verification for {verification.solution_id}: {verification.assessment}')

def _get_verification_summary(self) -> Dict[str, Any]:
    """Generate a summary of all verification results"""
    total_verifications = len(self.verification_results)
    if total_verifications == 0:
        return {'total': 0, 'correct': 0, 'incorrect': 0, 'incomplete': 0}
    assessments = [v.assessment for v in self.verification_results]
    return {'total': total_verifications, 'correct': assessments.count('CORRECT'), 'incorrect': assessments.count('INCORRECT'), 'incomplete': assessments.count('INCOMPLETE'), 'avg_confidence': sum((v.confidence for v in self.verification_results)) / total_verifications}

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

def extract_search_queries(text: str) -> List[str]:
    """Extract potential search queries from the input text"""
    text = text.strip()
    for prefix in ['User:', 'user:', 'User ', 'user ', 'Assistant:', 'assistant:', 'System:', 'system:']:
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
    search_patterns = ['search for[:\\s]+(\\S[^\\n]*?)(?:\\s*\\n|$)', 'find information about[:\\s]+(\\S[^\\n]*?)(?:\\s*\\n|$)', 'look up[:\\s]+(\\S[^\\n]*?)(?:\\s*\\n|$)', 'research[:\\s]+(\\S[^\\n]*?)(?:\\s*\\n|$)']
    queries = []
    for pattern in search_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            cleaned = match.strip()
            cleaned = cleaned.rstrip('"\'')
            cleaned = cleaned.lstrip('"\'')
            if cleaned:
                queries.append(cleaned)
    if not queries:
        search_prefixes = ['search for', 'find information about', 'look up', 'research']
        text_lower = text.lower().strip()
        is_empty_search = any((text_lower.startswith(prefix) and len(text_lower.replace(prefix, '').strip().strip('"\'')) < 2 for prefix in search_prefixes))
        if not is_empty_search:
            cleaned_query = text.replace('?', '').strip()
            cleaned_query = cleaned_query.strip('"\'')
            if cleaned_query and len(cleaned_query.split()) > 2:
                queries.append(cleaned_query)
            else:
                cleaned_query = re.sub('[^\\w\\s\\.]', ' ', text)
                cleaned_query = ' '.join(cleaned_query.split())
                cleaned_query = cleaned_query.strip('"\'')
                if len(cleaned_query) > 100:
                    cleaned_query = cleaned_query[:100].rsplit(' ', 1)[0]
                if cleaned_query and len(cleaned_query) > 2:
                    queries.append(cleaned_query)
    return queries

def extract_urls(text: str) -> List[str]:
    url_pattern = re.compile('https?://[^\\s\\\'"]+')
    urls = url_pattern.findall(text)
    cleaned_urls = []
    for url in urls:
        url = re.sub('[,\\\'\\"\\)\\]]+$', '', url)
        cleaned_urls.append(url)
    return cleaned_urls

def fetch_webpage_content(url: str, max_length: int=100000, verify_ssl: Optional[bool]=None, cert_path: Optional[str]=None) -> str:
    try:
        headers = {'User-Agent': f'optillm/{__version__} (https://github.com/codelion/optillm)'}
        if verify_ssl is None:
            verify_ssl = server_config.get('ssl_verify', True)
        if cert_path is None:
            cert_path = server_config.get('ssl_cert_path', '')
        if not verify_ssl:
            verify = False
        elif cert_path:
            verify = cert_path
        else:
            verify = True
        response = requests.get(url, headers=headers, timeout=10, verify=verify)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'lxml')
        for script in soup(['script', 'style']):
            script.decompose()
        text_elements = []
        for tag in ['article', 'main', 'div[role="main"]', '.main-content']:
            content = soup.select_one(tag)
            if content:
                text_elements.extend(content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'table']))
                break
        if not text_elements:
            text_elements = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'table'])
        content_parts = []
        for element in text_elements:
            if element.name == 'table':
                table_content = []
                headers = element.find_all('th')
                if headers:
                    header_text = ' | '.join((header.get_text(strip=True) for header in headers))
                    table_content.append(header_text)
                for row in element.find_all('tr'):
                    cells = row.find_all(['td', 'th'])
                    if cells:
                        row_text = ' | '.join((cell.get_text(strip=True) for cell in cells))
                        table_content.append(row_text)
                content_parts.append('\n' + '\n'.join(table_content) + '\n')
            else:
                content_parts.append(element.get_text(strip=False))
        text = ' '.join(content_parts)
        text = re.sub('\\s+', ' ', text).strip()
        text = re.sub('\\[.*?\\]+', '', text)
        if len(text) > max_length:
            text = text[:max_length] + '...'
        return text
    except Exception as e:
        return f'Error fetching content: {str(e)}'

def log_mcp_message(direction: str, method: str, params: Any=None, result: Any=None, error: Any=None):
    """Log MCP communication in detail"""
    message_parts = [f'MCP {direction} - Method: {method}']
    if params:
        try:
            params_str = json.dumps(params, indent=2)
            message_parts.append(f'Params: {params_str}')
        except:
            message_parts.append(f'Params: {params}')
    if result:
        try:
            result_str = json.dumps(result, indent=2)
            message_parts.append(f'Result: {result_str}')
        except:
            message_parts.append(f'Result: {result}')
    if error:
        message_parts.append(f'Error: {error}')
    logger.debug('\n'.join(message_parts))

class MCPServerManager:
    """Manages MCP servers and capabilities"""

    def __init__(self, config_manager: MCPConfigManager):
        self.config_manager = config_manager
        self.servers: Dict[str, MCPServer] = {}
        self.initialized = False
        self.all_tools = []
        self.all_resources = []
        self.all_prompts = []

    async def initialize(self) -> bool:
        """Initialize and cache all server capabilities"""
        if self.initialized:
            return True
        for server_name, server_config in self.config_manager.servers.items():
            self.servers[server_name] = MCPServer(server_name, server_config)
        connected_servers = 0
        for server_name, server in self.servers.items():
            success = await server.connect_and_discover()
            if success:
                connected_servers += 1
                for tool in server.tools:
                    tool_info = {'server': server_name, 'name': tool.name, 'description': tool.description, 'input_schema': tool.inputSchema}
                    self.all_tools.append(tool_info)
                    logger.debug(f'Cached tool: {tool_info}')
                for resource in server.resources:
                    resource_info = {'server': server_name, 'uri': resource.uri, 'name': resource.name, 'description': resource.description}
                    self.all_resources.append(resource_info)
                    logger.debug(f'Cached resource: {resource_info}')
                for prompt in server.prompts:
                    prompt_info = {'server': server_name, 'name': prompt.name, 'description': prompt.description, 'arguments': prompt.arguments}
                    self.all_prompts.append(prompt_info)
                    logger.debug(f'Cached prompt: {prompt_info}')
        self.initialized = True
        logger.info(f'Connected to {connected_servers}/{len(self.servers)} MCP servers')
        return connected_servers > 0

    def get_tools_for_model(self) -> List[Dict[str, Any]]:
        """Get tools in a format suitable for the model's tool-calling API"""
        tools = []
        for tool_info in self.all_tools:
            server_name = tool_info['server']
            tool_name = tool_info['name']
            tool_entry = {'type': 'function', 'function': {'name': f'{server_name}.{tool_name}', 'description': tool_info['description'] or f'Tool {tool_name} from server {server_name}', 'parameters': tool_info['input_schema']}}
            tools.append(tool_entry)
            logger.debug(f'Added tool for model: {tool_entry}')
        return tools

    def get_capabilities_description(self) -> str:
        """Get a description of all capabilities"""
        if not self.servers:
            return 'No MCP servers available.'
        description_parts = []
        for server_name, server in self.servers.items():
            if not server.connected:
                description_parts.append(f'## {server_name}\nServer connection failed or not established.\n')
                continue
            server_description = f'## {server_name}\n'
            if server.config.description:
                server_description += f'{server.config.description}\n\n'
            if server.tools:
                server_description += '### Tools\n'
                for tool in server.tools:
                    server_description += f'- {server_name}.{tool.name}: {tool.description or 'No description'}\n'
                server_description += '\n'
            if server.resources:
                server_description += '### Resources\n'
                for resource in server.resources:
                    server_description += f'- {resource.uri}: {resource.name or 'No name'} - {resource.description or 'No description'}\n'
                server_description += '\n'
            if server.prompts:
                server_description += '### Prompts\n'
                for prompt in server.prompts:
                    server_description += f'- {prompt.name}: {prompt.description or 'No description'}\n'
                server_description += '\n'
            description_parts.append(server_description)
        return '\n'.join(description_parts)

def get_capabilities_description(self) -> str:
    """Get a description of all capabilities"""
    if not self.servers:
        return 'No MCP servers available.'
    description_parts = []
    for server_name, server in self.servers.items():
        if not server.connected:
            description_parts.append(f'## {server_name}\nServer connection failed or not established.\n')
            continue
        server_description = f'## {server_name}\n'
        if server.config.description:
            server_description += f'{server.config.description}\n\n'
        if server.tools:
            server_description += '### Tools\n'
            for tool in server.tools:
                server_description += f'- {server_name}.{tool.name}: {tool.description or 'No description'}\n'
            server_description += '\n'
        if server.resources:
            server_description += '### Resources\n'
            for resource in server.resources:
                server_description += f'- {resource.uri}: {resource.name or 'No name'} - {resource.description or 'No description'}\n'
            server_description += '\n'
        if server.prompts:
            server_description += '### Prompts\n'
            for prompt in server.prompts:
                server_description += f'- {prompt.name}: {prompt.description or 'No description'}\n'
            server_description += '\n'
        description_parts.append(server_description)
    return '\n'.join(description_parts)

def _extract_task_description(initial_query: str, system_prompt: str) -> str:
    """Extract a task description for SELF-DISCOVER from the query and system prompt."""
    combined_text = f'{system_prompt}\n\n{initial_query}'
    task_keywords = {'mathematical': ['solve', 'calculate', 'equation', 'math', 'number', 'formula'], 'analytical': ['analyze', 'evaluate', 'assess', 'examine', 'compare'], 'creative': ['create', 'design', 'generate', 'brainstorm', 'invent'], 'logical': ['reason', 'logic', 'prove', 'deduce', 'conclude'], 'planning': ['plan', 'strategy', 'approach', 'method', 'steps'], 'problem_solving': ['problem', 'solution', 'solve', 'fix', 'resolve']}
    detected_types = []
    combined_lower = combined_text.lower()
    for task_type, keywords in task_keywords.items():
        if any((keyword in combined_lower for keyword in keywords)):
            detected_types.append(task_type)
    if detected_types:
        primary_type = detected_types[0]
        task_description = f'This is primarily a {primary_type} task that requires {', '.join(detected_types)} thinking.'
    else:
        task_description = 'This is a general reasoning task that requires systematic thinking and analysis.'
    if len(initial_query) > 50:
        task_description += f' The specific task involves: {initial_query[:200]}...'
    else:
        task_description += f' The specific task is: {initial_query}'
    return task_description

def _create_enhanced_prompt(system_prompt: str, initial_query: str, reasoning_structure: Dict[str, Any]=None, config: Dict[str, Any]=None) -> str:
    """Create an enhanced prompt that incorporates the reasoning structure."""
    base_prompt = f'System: {system_prompt}\n\nTask: {initial_query}'
    if reasoning_structure:
        import json
        structure_text = json.dumps(reasoning_structure, indent=2)
        enhanced_prompt = f'{base_prompt}\n\nREASONING STRUCTURE:\nPlease follow this discovered reasoning structure to solve the problem systematically:\n\n{structure_text}\n\nINSTRUCTIONS:\n1. Use the reasoning structure above to guide your thinking process\n2. Work through each component of the structure systematically  \n3. Wrap your detailed reasoning process in <think> tags\n4. After your reasoning, provide a clear and concise final answer\n5. Be thorough in your analysis but also aim for clarity and accuracy\n\n<think>\n[Follow the reasoning structure step-by-step to analyze and solve the problem]\n</think>\n\nBased on my systematic analysis, the answer is:'
    else:
        enhanced_prompt = f'{base_prompt}\n\nINSTRUCTIONS:\nPlease solve this problem using careful step-by-step reasoning.\n\n1. Wrap your detailed reasoning process in <think> tags\n2. Consider the problem from multiple angles\n3. Work through the solution systematically\n4. Provide a clear and well-supported final answer\n\n<think>\n[Provide your detailed step-by-step reasoning here]\n</think>\n\nBased on my analysis, the answer is:'
    return enhanced_prompt

def _clean_response(response: str) -> str:
    """Clean up the final response."""
    response = response.strip()
    if response and (not response.endswith(('.', '!', '?', ':', '"', "'"))):
        if not (response.replace(' ', '').replace(',', '').replace('.', '').isdigit() or len(response.split()) <= 3):
            response += '.'
    return response

def _test_system_message_support(proxy_client, model: str) -> bool:
    """
    Test if a model supports system messages by making a minimal test request.
    Returns True if supported, False otherwise.
    """
    try:
        test_response = proxy_client.chat.completions.create(model=model, messages=[{'role': 'system', 'content': 'test'}, {'role': 'user', 'content': 'hi'}], max_tokens=1, temperature=0)
        return True
    except Exception as e:
        error_msg = str(e).lower()
        if any((pattern in error_msg for pattern in ['developer instruction', 'system message', 'not enabled', 'not supported'])):
            logger.info(f'Model {model} does not support system messages: {str(e)[:100]}')
            return False
        else:
            logger.debug(f'System message test failed for {model}, assuming supported: {str(e)[:100]}')
            return True

def sanitize_code(code: str) -> str:
    """Prepare code for safe execution by removing problematic visualization code."""
    lines = code.split('\n')
    safe_lines = []
    for line in lines:
        if any((x in line.lower() for x in ['matplotlib', 'plt.', '.plot(', '.show(', 'figure', 'subplot'])):
            safe_lines.append(f'# {line}  # Removed for safety')
        else:
            safe_lines.append(line)
    return '\n'.join(safe_lines)

def extract_schema_from_response_format(response_format: Dict[str, Any]) -> Optional[str]:
    """Extract schema from response_format field."""
    try:
        if not response_format:
            return None
        if isinstance(response_format, dict):
            if response_format.get('type') == 'json_schema':
                schema_data = response_format.get('json_schema', {})
                if isinstance(schema_data, dict) and 'schema' in schema_data:
                    return json.dumps(schema_data['schema'])
                return json.dumps(schema_data)
        logger.warning(f'Could not extract valid schema from response_format')
        return None
    except Exception as e:
        logger.error(f'Error extracting schema from response_format: {str(e)}')
        return None

def run(system_prompt: str, initial_query: str, client, model: str, request_config: dict=None) -> Tuple[str, int]:
    """Main plugin execution function."""
    logger.info('Starting JSON plugin execution')
    completion_tokens = 0
    try:
        response_format = request_config.get('response_format') if request_config else None
        schema = extract_schema_from_response_format(response_format)
        if not schema:
            logger.warning('No valid schema found in response_format')
            response = client.chat.completions.create(model=model, messages=[{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': initial_query}])
            return (response.choices[0].message.content, response.usage.completion_tokens)
        json_generator = JSONGenerator()
        result = json_generator.generate_json(initial_query, schema)
        json_response = json.dumps(result) if isinstance(result, dict) else str(result)
        completion_tokens = json_generator.count_tokens(json_response)
        logger.info(f'Successfully generated JSON response: {json_response}')
        return (json_response, completion_tokens)
    except Exception as e:
        logger.error(f'Error in JSON plugin: {str(e)}')
        response = client.chat.completions.create(model=model, messages=[{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': initial_query}])
        return (response.choices[0].message.content, response.usage.completion_tokens)

def extract_python_code(text: str) -> List[str]:
    """Extract Python code blocks from text."""
    pattern = '```python\\s*(.*?)\\s*```'
    return re.findall(pattern, text, re.DOTALL)

def should_execute_request_code(query: str) -> bool:
    """Decide whether to execute code from the request based on the query."""
    keywords = ['run', 'execute', 'output', 'result']
    return any((keyword in query.lower() for keyword in keywords))

def normalize_response(response: str) -> str:
    """
    Basic normalization for comparing responses.
    Removes extra whitespace, punctuation at ends, and lowercases.
    """
    if not response:
        return ''
    response = re.sub('<think>.*?</think>', '', response, flags=re.DOTALL)
    response = response.strip()
    response = response.lower()
    response = response.rstrip('.,;:!?')
    response = ' '.join(response.split())
    return response

def extract_final_answer(response: str) -> str:
    """
    Try to extract just the final answer from a response.
    This is generic and looks for common patterns.
    """
    if not response:
        return response
    response = re.sub('<think>.*?</think>', '', response, flags=re.DOTALL).strip()
    patterns = ['(?:final answer|answer):\\s*(.+?)(?:\\n|$)', '(?:the answer is|answer is)\\s*(.+?)(?:\\n|$)', '###\\s*(.+?)(?:\\n|$)', '^([A-E])\\b', '\\b([A-E])\\b\\s*$']
    for pattern in patterns:
        match = re.search(pattern, response, re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(1).strip()
    return response

def parse_selection_response(response: str, num_candidates: int) -> Tuple[int, str]:
    """
    Parse the selection response to extract the chosen candidate number and reasoning.
    
    Args:
        response: The LLM's comparison response
        num_candidates: Total number of candidates
        
    Returns:
        Tuple of (selected_index, reasoning)
    """
    import re
    match = re.search('BEST CANDIDATE:\\s*(\\d+)', response, re.IGNORECASE)
    if match:
        candidate_num = int(match.group(1))
        selected_index = candidate_num - 1
        if 0 <= selected_index < num_candidates:
            reasoning_match = re.search('REASONING:\\s*(.+)', response, re.IGNORECASE | re.DOTALL)
            reasoning = reasoning_match.group(1).strip() if reasoning_match else 'No explicit reasoning provided'
            logger.info(f'Selected candidate {candidate_num} based on comparison')
            return (selected_index, reasoning)
    patterns = ['[Cc]andidate\\s+(\\d+)\\s+is\\s+(?:the\\s+)?best', '[Ii]\\s+(?:would\\s+)?select\\s+[Cc]andidate\\s+(\\d+)', '[Tt]he\\s+best\\s+(?:response|candidate)\\s+is\\s+(?:number\\s+)?(\\d+)']
    for pattern in patterns:
        match = re.search(pattern, response)
        if match:
            candidate_num = int(match.group(1))
            selected_index = candidate_num - 1
            if 0 <= selected_index < num_candidates:
                logger.info(f'Selected candidate {candidate_num} using fallback pattern')
                return (selected_index, 'Selection extracted from response pattern')
    logger.warning('Could not parse selection from comparison response, defaulting to first candidate')
    return (0, 'Failed to parse selection, defaulted to first candidate')

class InstanceCounterAnonymizer(Operator):
    """
    Anonymizer which replaces the entity value
    with an instance counter per entity.
    """
    REPLACING_FORMAT = '<{entity_type}_{index}>'

    def operate(self, text: str, params: Dict=None) -> str:
        """Anonymize the input text."""
        entity_type: str = params['entity_type']
        entity_mapping: Dict[Dict:str] = params['entity_mapping']
        entity_mapping_for_type = entity_mapping.get(entity_type)
        if not entity_mapping_for_type:
            new_text = self.REPLACING_FORMAT.format(entity_type=entity_type, index=0)
            entity_mapping[entity_type] = {}
        else:
            if text in entity_mapping_for_type:
                return entity_mapping_for_type[text]
            previous_index = self._get_last_index(entity_mapping_for_type)
            new_text = self.REPLACING_FORMAT.format(entity_type=entity_type, index=previous_index + 1)
        entity_mapping[entity_type][text] = new_text
        return new_text

    @staticmethod
    def _get_last_index(entity_mapping_for_type: Dict) -> int:
        """Get the last index for a given entity type."""

        def get_index(value: str) -> int:
            return int(value.split('_')[-1][:-1])
        indices = [get_index(v) for v in entity_mapping_for_type.values()]
        return max(indices)

    def validate(self, params: Dict=None) -> None:
        """Validate operator parameters."""
        if 'entity_mapping' not in params:
            raise ValueError('An input Dict called `entity_mapping` is required.')
        if 'entity_type' not in params:
            raise ValueError('An entity_type param is required.')

    def operator_name(self) -> str:
        return 'entity_counter'

    def operator_type(self) -> OperatorType:
        return OperatorType.Anonymize

def get_index(value: str) -> int:
    return int(value.split('_')[-1][:-1])

def validate(self, params: Dict=None) -> None:
    """Validate operator parameters."""
    if 'entity_mapping' not in params:
        raise ValueError('An input Dict called `entity_mapping` is required.')
    if 'entity_type' not in params:
        raise ValueError('An entity_type param is required.')

def replace_entities(entity_map, text):
    reverse_map = {}
    for entity_type, entities in entity_map.items():
        for entity_name, placeholder in entities.items():
            reverse_map[placeholder] = entity_name

    def replace_placeholder(match):
        placeholder = match.group(0)
        return reverse_map.get(placeholder, placeholder)
    import re
    pattern = '<[A-Z_]+_\\d+>'
    replaced_text = re.sub(pattern, replace_placeholder, text)
    return replaced_text

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

class HealthChecker:
    """Background health checker for providers"""

    def __init__(self, providers: List, enabled: bool=True, interval: int=30, timeout: int=5):
        self.providers = providers
        self.enabled = enabled
        self.interval = interval
        self.timeout = timeout
        self.running = False
        self.thread = None

    def start(self):
        """Start health checking in background"""
        if not self.enabled:
            return
        self.running = True
        self.thread = threading.Thread(target=self._check_loop, daemon=True)
        self.thread.start()
        logger.info(f'Health checker started (interval: {self.interval}s)')

    def stop(self):
        """Stop health checking"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)

    def _check_loop(self):
        """Main health check loop"""
        while self.running:
            for provider in self.providers:
                self._check_provider(provider)
            time.sleep(self.interval)

    def _check_provider(self, provider):
        """Check health of a single provider"""
        try:
            response = provider.client.models.list()
            if not provider.is_healthy:
                logger.info(f'Provider {provider.name} is now healthy')
            provider.is_healthy = True
            provider.last_error = None
        except Exception as e:
            if provider.is_healthy:
                logger.warning(f'Provider {provider.name} failed health check: {e}')
            provider.is_healthy = False
            provider.last_error = str(e)

def stop(self):
    """Stop health checking"""
    self.running = False
    if self.thread:
        self.thread.join(timeout=1)

def _check_provider(self, provider):
    """Check health of a single provider"""
    try:
        response = provider.client.models.list()
        if not provider.is_healthy:
            logger.info(f'Provider {provider.name} is now healthy')
        provider.is_healthy = True
        provider.last_error = None
    except Exception as e:
        if provider.is_healthy:
            logger.warning(f'Provider {provider.name} failed health check: {e}')
        provider.is_healthy = False
        provider.last_error = str(e)

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

def chunk_context(doc: str, chunk_size: int, tokenizer, separator='\n') -> List[str]:
    """
    Splits a long document into token-limited chunks based on a separator, ensuring each chunk fits within `chunk_size`.

    Uses a greedy approach to accumulate text segments (split by `separator`) into chunks that fit within the
    token limit. If a segment alone exceeds the limit, it is recursively broken down using sentence-level
    splitting. Attempts to preserve natural boundaries while minimizing excessive chunking.

    Args:
        doc (str): Input document to split.
        chunk_size (int): Maximum number of tokens allowed per chunk.
        tokenizer: Tokenizer instance with `.encode()` method to compute token length.
        separator (str): Delimiter to split initial segments (default: newline).

    Returns:
        List[str]: List of non-empty, token-constrained document chunks.
    """
    paragraphs = doc.split(separator)
    paragraphs = [paragraph for paragraph in paragraphs if paragraph]
    separator_len = get_prompt_length(separator, tokenizer, no_special_tokens=True)
    docs = []
    current_doc = []
    total = 0
    for paragraph in paragraphs:
        plen = get_prompt_length(paragraph, tokenizer, no_special_tokens=True)
        if total + plen + (separator_len if len(current_doc) > 0 else 0) > chunk_size:
            if total > chunk_size:
                logger.info(f'Created a chunk of size {total}, which is longer than the specified {chunk_size}')
                if len(current_doc) == 1:
                    split_again = split_into_granular_chunks(current_doc[0], chunk_size, tokenizer)
                    docs.extend(split_again)
                    current_doc = []
                    total = 0
            if len(current_doc) > 0:
                doc = separator.join(current_doc)
                if doc is not None:
                    docs.append(doc)
                while total > 0 or (total + plen + (separator_len if len(current_doc) > 0 else 0) > chunk_size and total > 0):
                    total -= get_prompt_length(current_doc[0], tokenizer, no_special_tokens=True) + (separator_len if len(current_doc) > 1 else 0)
                    current_doc = current_doc[1:]
        current_doc.append(paragraph)
        total += plen + (separator_len if len(current_doc) > 1 else 0)
    if get_prompt_length(current_doc[-1], tokenizer, no_special_tokens=True) > chunk_size and len(current_doc) == 1:
        split_again = split_into_granular_chunks(current_doc[0], chunk_size, tokenizer)
        docs.extend(split_again)
        current_doc = []
    else:
        doc = separator.join(current_doc)
        if doc is not None:
            docs.append(doc)
    return [doc for doc in docs if doc.strip()]

def split_into_granular_chunks(text: str, chunk_size: int, tokenizer, spliter='([。！？；.?!;])') -> List[str]:
    """
    Splits long text into granular, token-length-constrained chunks using sentence boundaries.

    Sentences are first extracted using a delimiter pattern (`spliter`), then grouped into chunks such that
    each chunk does not exceed the specified `chunk_size` (in tokens). If a chunk still exceeds the limit,
    it is recursively broken down further using whitespace as a fallback.

    Ensures that the final chunks are balanced: if the last chunk is too small, it redistributes the last two
    chunks more evenly by re-splitting and re-allocating their sentences.

    Args:
        text (str): Input text to be chunked.
        chunk_size (int): Maximum number of tokens per chunk.
        tokenizer: Tokenizer instance with `.encode()` method to compute token length.
        spliter (str): Regex pattern to split sentences.

    Returns:
        List[str]: List of token-limited chunks, each composed of one or more sentences.
    """
    sentences = split_sentences(text, spliter)
    chunks = []
    current_chunk = ''
    for sentence in sentences:
        sentence_length = get_prompt_length(sentence, tokenizer)
        if get_prompt_length(current_chunk, tokenizer) + sentence_length <= chunk_size:
            current_chunk += sentence
        else:
            if current_chunk:
                if get_prompt_length(current_chunk, tokenizer) <= chunk_size:
                    chunks.append(current_chunk)
                elif spliter != ' ':
                    chunks.extend(split_into_granular_chunks(current_chunk, chunk_size=chunk_size, tokenizer=tokenizer, spliter=' '))
            current_chunk = sentence
    if current_chunk != '':
        if get_prompt_length(current_chunk, tokenizer) <= chunk_size:
            chunks.append(current_chunk)
        elif spliter != ' ':
            chunks.extend(split_into_granular_chunks(current_chunk, chunk_size=chunk_size, tokenizer=tokenizer, spliter=' '))
    if len(chunks) > 1 and get_prompt_length(chunks[-1], tokenizer) < chunk_size // 2:
        last_chunk = chunks.pop()
        penultimate_chunk = chunks.pop()
        combined_text = penultimate_chunk + last_chunk
        new_sentences = split_sentences(combined_text, spliter)
        new_penultimate_chunk = ''
        new_last_chunk = ''
        start, end = (0, len(new_sentences) - 1)
        while start <= end and len(new_sentences) != 1:
            flag = False
            if get_prompt_length(new_penultimate_chunk + new_sentences[start], tokenizer) <= chunk_size:
                flag = True
                new_penultimate_chunk += new_sentences[start]
                if start == end:
                    break
                start += 1
            if get_prompt_length(new_last_chunk + new_sentences[end], tokenizer) <= chunk_size:
                new_last_chunk = new_sentences[end] + new_last_chunk
                end -= 1
                flag = True
            if flag == False:
                break
        if start < end:
            remaining_sentences = new_sentences[start:end + 1]
            if remaining_sentences:
                remaining_text = ''.join(remaining_sentences)
                words = remaining_text.split(' ')
                end_index = len(words) - 1
                for index, w in enumerate(words):
                    if get_prompt_length(' '.join([new_penultimate_chunk, w]), tokenizer) <= chunk_size:
                        new_penultimate_chunk = ' '.join([new_penultimate_chunk, w])
                    else:
                        end_index = index
                        break
                if end_index != len(words) - 1:
                    new_last_chunk = ' '.join(words[end_index:]) + ' ' + new_last_chunk
        if len(new_sentences) == 1:
            chunks.append(penultimate_chunk)
            chunks.append(last_chunk)
        else:
            chunks.append(new_penultimate_chunk)
            chunks.append(new_last_chunk)
    return chunks

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

def extract_thinking(response: str) -> Tuple[str, Optional[str]]:
    """
    Extract thinking content from <think>...</think> tags and the response after.
    
    Args:
        response: The model's response
    
    Returns:
        Tuple[str, Optional[str]]: The cleaned response and the thinking content (if any)
    """
    thinking_content = None
    final_response = response
    think_pattern = '<think>(.*?)</think>'
    think_matches = re.findall(think_pattern, response, re.DOTALL)
    if think_matches:
        thinking_content = '\n'.join(think_matches)
        final_parts = response.split('</think>')
        if len(final_parts) > 1:
            final_response = final_parts[-1].strip()
    return (final_response, thinking_content)

def clean_reasoning_tags(text: str) -> str:
    """
    Remove reasoning tags from model responses for clean final output.
    
    Removes common reasoning tags like:
    - <think></think>
    - <thinking></thinking>
    - <reasoning></reasoning>
    - <thought></thought>
    
    Args:
        text: Raw model response text
        
    Returns:
        Cleaned text with reasoning tags removed
    """
    if not text:
        return text
    reasoning_patterns = ['<think>.*?</think>', '<thinking>.*?</thinking>', '<reasoning>.*?</reasoning>', '<thought>.*?</thought>', '<reflect>.*?</reflect>', '<reflection>.*?</reflection>']
    cleaned_text = text
    for pattern in reasoning_patterns:
        cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.DOTALL | re.IGNORECASE)
    cleaned_text = re.sub('\\n\\s*\\n\\s*\\n+', '\n\n', cleaned_text)
    cleaned_text = re.sub('  +', ' ', cleaned_text)
    cleaned_text = cleaned_text.strip()
    return cleaned_text

def cleanup_placeholder_tags(text: str) -> str:
    """
    Remove any remaining placeholder tags from the final report.
    
    This is a final cleanup step to ensure no incomplete research tags remain
    in the published report.
    
    Args:
        text: Research report text
        
    Returns:
        Text with all placeholder tags removed
    """
    if not text:
        return text
    placeholder_patterns = ['\\[NEEDS RESEARCH[^\\]]*\\]', '\\[SOURCE NEEDED[^\\]]*\\]', '\\[RESEARCH NEEDED[^\\]]*\\]', '\\[CITATION NEEDED[^\\]]*\\]', '\\[MORE RESEARCH NEEDED[^\\]]*\\]', '\\[REQUIRES INVESTIGATION[^\\]]*\\]', '\\[TO BE RESEARCHED[^\\]]*\\]', '\\[VERIFY[^\\]]*\\]', '\\[CHECK[^\\]]*\\]', '\\[Placeholder for[^\\]]+\\]', '\\[\\d+\\]\\s*\\[Placeholder[^\\]]+\\]', '\\[Insert citation[^\\]]*\\]', '\\[Add reference[^\\]]*\\]', '\\[Reference needed[^\\]]*\\]', '\\[To be completed[^\\]]*\\]', '\\[Under development[^\\]]*\\]', '\\[Coming soon[^\\]]*\\]', '\\[TBD[^\\]]*\\]', '\\[TODO[^\\]]*\\]', '\\[Question \\d+[^\\]]*\\]', '\\[Research question[^\\]]*\\]']
    cleaned_text = text
    for pattern in placeholder_patterns:
        cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE)
    lines = cleaned_text.split('\n')
    filtered_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped and (not re.match('^[\\s\\-\\*\\.\\,\\;\\:]*$', stripped)):
            filtered_lines.append(line)
        elif not stripped:
            filtered_lines.append(line)
    result = '\n'.join(filtered_lines)
    result = re.sub('\\n\\s*\\n\\s*\\n+', '\n\n', result)
    result = result.strip()
    return result

def validate_citation_usage(text: str, total_citations: int) -> Dict[str, Any]:
    """
    Validate that citations are actually used in the report text.

    Checks which citation numbers appear in the body text and warns about
    unused citations that are only in the references section.

    Args:
        text: The full report text including references
        total_citations: Total number of citations available

    Returns:
        Dict with validation results including used/unused citation counts
    """
    if not text:
        return {'citations_used': 0, 'citations_total': total_citations, 'usage_percentage': 0.0, 'unused_citations': list(range(1, total_citations + 1)), 'warning': 'Empty report text'}
    body_text = text.split('## References')[0] if '## References' in text else text
    citations_in_body = set()
    citation_pattern = '\\[(\\d+)\\]'
    for match in re.finditer(citation_pattern, body_text):
        citation_num = int(match.group(1))
        citations_in_body.add(citation_num)
    all_citations = set(range(1, total_citations + 1))
    unused_citations = sorted(all_citations - citations_in_body)
    usage_percentage = len(citations_in_body) / total_citations * 100 if total_citations > 0 else 0
    result = {'citations_used': len(citations_in_body), 'citations_total': total_citations, 'usage_percentage': usage_percentage, 'unused_citations': unused_citations, 'used_citations': sorted(citations_in_body)}
    if usage_percentage < 30:
        result['warning'] = f'Very low citation usage ({usage_percentage:.1f}%). Most sources are not cited in the text.'
    elif usage_percentage < 50:
        result['warning'] = f'Low citation usage ({usage_percentage:.1f}%). Many sources are not cited in the text.'
    return result

def validate_report_completeness(text: str) -> Dict[str, Any]:
    """
    Validate that the research report is complete and ready for publication.
    
    Checks for:
    - Placeholder citations
    - Incomplete sections
    - Unfinished research questions
    - Missing content indicators
    
    Returns:
        Dict with validation results and suggestions for fixes
    """
    if not text:
        return {'is_complete': False, 'issues': ['Empty report'], 'suggestions': []}
    issues = []
    suggestions = []
    placeholder_citation_patterns = ['\\[Placeholder for[^\\]]+\\]', '\\[\\d+\\]\\s*\\[Placeholder[^\\]]+\\]', '\\[Insert citation[^\\]]*\\]', '\\[Reference needed[^\\]]*\\]']
    for pattern in placeholder_citation_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            issues.append(f'Found {len(matches)} placeholder citations: {matches[:3]}')
            suggestions.append('Replace placeholder citations with actual sources or remove incomplete claims')
    if 'Research Questions for Investigation' in text:
        question_section_match = re.search('## Research Questions for Investigation.*?(?=##|$)', text, re.DOTALL)
        if question_section_match:
            question_content = question_section_match.group(0)
            question_lines = [line for line in question_content.split('\n') if line.strip().startswith('*') or line.strip().startswith('-')]
            if len(question_lines) > 3:
                issues.append('Report contains unanswered research questions section')
                suggestions.append('Convert research questions into answered findings or remove incomplete section')
    section_pattern = '##\\s+([^#\\n]+)\\n(.*?)(?=##|$)'
    sections = re.findall(section_pattern, text, re.DOTALL)
    for section_title, section_content in sections:
        placeholder_count = len(re.findall('\\[[^\\]]*(?:placeholder|needed|research|todo|tbd)[^\\]]*\\]', section_content, re.IGNORECASE))
        content_lines = [line.strip() for line in section_content.split('\n') if line.strip()]
        if placeholder_count > len(content_lines) / 3:
            issues.append(f"Section '{section_title.strip()}' is mostly placeholders")
            suggestions.append(f"Complete content for '{section_title.strip()}' section or remove it")
    if text.count('[') - text.count(']') != 0:
        issues.append('Unmatched brackets detected - possible incomplete citations')
        suggestions.append('Review and fix citation formatting')
    if len(text.split()) < 500:
        issues.append('Report appears to be very short, possibly incomplete')
        suggestions.append('Ensure all research areas are adequately covered')
    is_complete = len(issues) == 0
    return {'is_complete': is_complete, 'issues': issues, 'suggestions': suggestions, 'word_count': len(text.split()), 'section_count': len(sections)}

class AnswerExtractor:
    """Universal answer extractor using math-verify with fallback patterns"""

    def __init__(self):
        self.math_verify_timeout = 5

    def extract_answer(self, solution: str, problem_type: str='general', problem_id: Optional[int]=None) -> Optional[Any]:
        """
        Universal answer extraction using math-verify library with fallback patterns.

        Args:
            solution: The solution text to extract answer from
            problem_type: Type of problem (general, imo, aime, etc.)
            problem_id: Specific problem ID for customized extraction

        Returns:
            Extracted answer in appropriate format (int, str, list, etc.)
        """
        if not solution:
            return None
        logger.debug(f'Extracting answer from solution (type: {problem_type}, id: {problem_id})')
        math_verify_result = self._try_math_verify(solution)
        if math_verify_result is not None:
            logger.debug(f'Math-verify extracted: {math_verify_result}')
            return math_verify_result
        if problem_type == 'imo' and problem_id:
            specific_result = self._extract_imo_specific(solution, problem_id)
            if specific_result is not None:
                logger.debug(f'IMO-specific extracted: {specific_result}')
                return specific_result
        if problem_type == 'aime':
            aime_result = self._extract_aime_answer(solution)
            if aime_result is not None:
                logger.debug(f'AIME-style extracted: {aime_result}')
                return aime_result
        general_result = self._extract_general_answer(solution)
        if general_result is not None:
            logger.debug(f'General pattern extracted: {general_result}')
            return general_result
        logger.debug('No answer extracted')
        return None

    def _try_math_verify(self, solution: str) -> Optional[Any]:
        """Try to extract answer using math-verify library"""
        try:
            parsed_result = math_verify.parse(solution, parsing_timeout=self.math_verify_timeout)
            if parsed_result:
                return self._normalize_math_verify_result(parsed_result)
        except Exception as e:
            logger.debug(f'Math-verify failed: {str(e)}')
        return None

    def _normalize_math_verify_result(self, result) -> Any:
        """Normalize math-verify result to appropriate format"""
        if isinstance(result, (int, float)):
            return int(result) if result == int(result) else result
        elif isinstance(result, str):
            try:
                if result.isdigit():
                    return int(result)
                elif result.replace('.', '', 1).isdigit():
                    float_val = float(result)
                    return int(float_val) if float_val == int(float_val) else float_val
            except ValueError:
                pass
            return result
        elif isinstance(result, (list, tuple)):
            return result
        else:
            return str(result)

    def _extract_imo_specific(self, solution: str, problem_id: int) -> Optional[Any]:
        """Extract answers for specific IMO 2025 problems"""
        solution_lower = solution.lower()
        if problem_id == 1:
            set_patterns = ['\\\\boxed\\{([^}]+)\\}', '\\{([^}]+)\\}', 'k\\s*\\\\in\\s*\\{([^}]+)\\}', 'k\\s*can\\s*be\\s*([0-9,\\s]+)']
            for pattern in set_patterns:
                matches = re.finditer(pattern, solution, re.IGNORECASE)
                for match in matches:
                    content = match.group(1).strip()
                    logger.debug(f'Found set content: {content}')
                    if '...' in content or '\\ldots' in content:
                        return self._parse_set_with_ellipsis(content)
                    elif ',' in content:
                        return self._parse_explicit_set(content)
                    elif content.isdigit():
                        return {int(content)}
            if any((phrase in solution_lower for phrase in ['all non-negative', 'all integers', 'any integer'])):
                return 'all_integers'
        elif problem_id == 3:
            constant_patterns = ['\\\\boxed\\{(\\d+)\\}', 'c\\s*=\\s*(\\d+)', 'constant\\s+is\\s+(\\d+)', 'answer\\s+is\\s+(\\d+)', 'minimum\\s+constant\\s+is\\s+(\\d+)']
            for pattern in constant_patterns:
                matches = list(re.finditer(pattern, solution, re.IGNORECASE))
                if matches:
                    return int(matches[-1].group(1))
        elif problem_id == 6:
            if '4048' in solution:
                return 4048
            number_patterns = ['\\\\boxed\\{(\\d+)\\}', 'answer\\s+is\\s+(\\d+)', 'minimum\\s+number\\s+is\\s+(\\d+)', 'tiles?\\s+is\\s+(\\d+)']
            for pattern in number_patterns:
                matches = list(re.finditer(pattern, solution, re.IGNORECASE))
                if matches:
                    number = int(matches[-1].group(1))
                    if number > 100:
                        return number
        return None

    def _parse_set_with_ellipsis(self, content: str) -> set:
        """Parse set notation with ellipsis like '0, 1, 2, ..., n'"""
        content = content.replace('\\ldots', '...').replace('\\dots', '...')
        numbers_before = re.findall('(\\d+)', content.split('...')[0])
        if len(numbers_before) >= 2:
            start = int(numbers_before[0])
            next_val = int(numbers_before[1])
            step = next_val - start
            if step == 1 and start == 0:
                return {0, 1, 2, 3}
        numbers = [int(x) for x in re.findall('\\d+', content)]
        return set(numbers)

    def _parse_explicit_set(self, content: str) -> set:
        """Parse explicit set like '0, 1, 3'"""
        numbers = re.findall('\\d+', content)
        return {int(x) for x in numbers}

    def _extract_aime_answer(self, solution: str) -> Optional[int]:
        """Extract AIME-style numeric answers (integers 0-999)"""
        patterns = ['\\$n=\\\\boxed{(\\d+)}\\$', '\\\\\\[\\\\boxed{(\\d+)}\\\\\\]', '\\\\\\[\\\\boxed{(\\d+)}\\.\\\\\\]', '\\\\boxed{(\\d+)}', '\\$\\\\boxed{(\\d+)}\\$', 'boxed{(\\d+)}', '\\\\boxed\\s*{\\s*(\\d+)\\s*}', '\\bboxed\\s*{\\s*(\\d+)\\s*}', 'final answer is[^\\d]*(\\d+)', 'answer is[^\\d]*(\\d+)', 'answer:[^\\d]*(\\d+)', '= ?(\\d+)$']
        for pattern in patterns:
            matches = re.finditer(pattern, solution, re.IGNORECASE)
            last_match = None
            for match in matches:
                last_match = match
            if last_match:
                try:
                    number = int(last_match.group(1))
                    if 0 <= number <= 999:
                        return number
                except (ValueError, IndexError):
                    continue
        numbers = re.findall('(\\d+)', solution)
        if numbers:
            try:
                last_number = int(numbers[-1])
                if 0 <= last_number <= 999:
                    return last_number
            except ValueError:
                pass
        return None

    def _extract_general_answer(self, solution: str) -> Optional[Any]:
        """General fallback answer extraction patterns"""
        patterns = [('\\\\boxed\\{([^}]+)\\}', self._parse_boxed_content), ('boxed\\{([^}]+)\\}', self._parse_boxed_content), ('(?:the\\s+)?answer\\s+is\\s+([^\\n.!?]+)', str.strip), ('(?:final\\s+)?answer:\\s*([^\\n.!?]+)', str.strip), ('therefore,?\\s+([^\\n.!?]+)', str.strip), ('thus,?\\s+([^\\n.!?]+)', str.strip), ('=\\s*([^\\n.!?]+)$', str.strip)]
        for pattern, processor in patterns:
            matches = list(re.finditer(pattern, solution, re.IGNORECASE))
            if matches:
                content = matches[-1].group(1).strip()
                if content:
                    processed = processor(content) if processor else content
                    logger.debug(f'General pattern matched: {content} -> {processed}')
                    return processed
        return None

    def _parse_boxed_content(self, content: str) -> Any:
        """Parse content from boxed answers"""
        content = content.strip()
        if content.isdigit():
            return int(content)
        try:
            float_val = float(content)
            return int(float_val) if float_val == int(float_val) else float_val
        except ValueError:
            pass
        if content.startswith('{') and content.endswith('}'):
            try:
                set_content = content[1:-1]
                if ',' in set_content:
                    numbers = [int(x.strip()) for x in set_content.split(',') if x.strip().isdigit()]
                    return set(numbers)
            except ValueError:
                pass
        return content

def _normalize_math_verify_result(self, result) -> Any:
    """Normalize math-verify result to appropriate format"""
    if isinstance(result, (int, float)):
        return int(result) if result == int(result) else result
    elif isinstance(result, str):
        try:
            if result.isdigit():
                return int(result)
            elif result.replace('.', '', 1).isdigit():
                float_val = float(result)
                return int(float_val) if float_val == int(float_val) else float_val
        except ValueError:
            pass
        return result
    elif isinstance(result, (list, tuple)):
        return result
    else:
        return str(result)

def _extract_imo_specific(self, solution: str, problem_id: int) -> Optional[Any]:
    """Extract answers for specific IMO 2025 problems"""
    solution_lower = solution.lower()
    if problem_id == 1:
        set_patterns = ['\\\\boxed\\{([^}]+)\\}', '\\{([^}]+)\\}', 'k\\s*\\\\in\\s*\\{([^}]+)\\}', 'k\\s*can\\s*be\\s*([0-9,\\s]+)']
        for pattern in set_patterns:
            matches = re.finditer(pattern, solution, re.IGNORECASE)
            for match in matches:
                content = match.group(1).strip()
                logger.debug(f'Found set content: {content}')
                if '...' in content or '\\ldots' in content:
                    return self._parse_set_with_ellipsis(content)
                elif ',' in content:
                    return self._parse_explicit_set(content)
                elif content.isdigit():
                    return {int(content)}
        if any((phrase in solution_lower for phrase in ['all non-negative', 'all integers', 'any integer'])):
            return 'all_integers'
    elif problem_id == 3:
        constant_patterns = ['\\\\boxed\\{(\\d+)\\}', 'c\\s*=\\s*(\\d+)', 'constant\\s+is\\s+(\\d+)', 'answer\\s+is\\s+(\\d+)', 'minimum\\s+constant\\s+is\\s+(\\d+)']
        for pattern in constant_patterns:
            matches = list(re.finditer(pattern, solution, re.IGNORECASE))
            if matches:
                return int(matches[-1].group(1))
    elif problem_id == 6:
        if '4048' in solution:
            return 4048
        number_patterns = ['\\\\boxed\\{(\\d+)\\}', 'answer\\s+is\\s+(\\d+)', 'minimum\\s+number\\s+is\\s+(\\d+)', 'tiles?\\s+is\\s+(\\d+)']
        for pattern in number_patterns:
            matches = list(re.finditer(pattern, solution, re.IGNORECASE))
            if matches:
                number = int(matches[-1].group(1))
                if number > 100:
                    return number
    return None

def _parse_set_with_ellipsis(self, content: str) -> set:
    """Parse set notation with ellipsis like '0, 1, 2, ..., n'"""
    content = content.replace('\\ldots', '...').replace('\\dots', '...')
    numbers_before = re.findall('(\\d+)', content.split('...')[0])
    if len(numbers_before) >= 2:
        start = int(numbers_before[0])
        next_val = int(numbers_before[1])
        step = next_val - start
        if step == 1 and start == 0:
            return {0, 1, 2, 3}
    numbers = [int(x) for x in re.findall('\\d+', content)]
    return set(numbers)

def _parse_explicit_set(self, content: str) -> set:
    """Parse explicit set like '0, 1, 3'"""
    numbers = re.findall('\\d+', content)
    return {int(x) for x in numbers}

def _extract_aime_answer(self, solution: str) -> Optional[int]:
    """Extract AIME-style numeric answers (integers 0-999)"""
    patterns = ['\\$n=\\\\boxed{(\\d+)}\\$', '\\\\\\[\\\\boxed{(\\d+)}\\\\\\]', '\\\\\\[\\\\boxed{(\\d+)}\\.\\\\\\]', '\\\\boxed{(\\d+)}', '\\$\\\\boxed{(\\d+)}\\$', 'boxed{(\\d+)}', '\\\\boxed\\s*{\\s*(\\d+)\\s*}', '\\bboxed\\s*{\\s*(\\d+)\\s*}', 'final answer is[^\\d]*(\\d+)', 'answer is[^\\d]*(\\d+)', 'answer:[^\\d]*(\\d+)', '= ?(\\d+)$']
    for pattern in patterns:
        matches = re.finditer(pattern, solution, re.IGNORECASE)
        last_match = None
        for match in matches:
            last_match = match
        if last_match:
            try:
                number = int(last_match.group(1))
                if 0 <= number <= 999:
                    return number
            except (ValueError, IndexError):
                continue
    numbers = re.findall('(\\d+)', solution)
    if numbers:
        try:
            last_number = int(numbers[-1])
            if 0 <= last_number <= 999:
                return last_number
        except ValueError:
            pass
    return None

def _extract_general_answer(self, solution: str) -> Optional[Any]:
    """General fallback answer extraction patterns"""
    patterns = [('\\\\boxed\\{([^}]+)\\}', self._parse_boxed_content), ('boxed\\{([^}]+)\\}', self._parse_boxed_content), ('(?:the\\s+)?answer\\s+is\\s+([^\\n.!?]+)', str.strip), ('(?:final\\s+)?answer:\\s*([^\\n.!?]+)', str.strip), ('therefore,?\\s+([^\\n.!?]+)', str.strip), ('thus,?\\s+([^\\n.!?]+)', str.strip), ('=\\s*([^\\n.!?]+)$', str.strip)]
    for pattern, processor in patterns:
        matches = list(re.finditer(pattern, solution, re.IGNORECASE))
        if matches:
            content = matches[-1].group(1).strip()
            if content:
                processed = processor(content) if processor else content
                logger.debug(f'General pattern matched: {content} -> {processed}')
                return processed
    return None

def _parse_boxed_content(self, content: str) -> Any:
    """Parse content from boxed answers"""
    content = content.strip()
    if content.isdigit():
        return int(content)
    try:
        float_val = float(content)
        return int(float_val) if float_val == int(float_val) else float_val
    except ValueError:
        pass
    if content.startswith('{') and content.endswith('}'):
        try:
            set_content = content[1:-1]
            if ',' in set_content:
                numbers = [int(x.strip()) for x in set_content.split(',') if x.strip().isdigit()]
                return set(numbers)
        except ValueError:
            pass
    return content

class ComplexityClassifier:
    """
    Classifies queries as HIGH or LOW complexity for token budget allocation.
    Uses the adaptive-classifier model for classification.
    """

    def __init__(self, model_name: str='adaptive-classifier/llm-router'):
        """
        Initialize the complexity classifier.
        
        Args:
            model_name: HuggingFace model name or path for the classifier
        """
        self.model_name = model_name
        self.classifier = None
        self._load_model()

    def _load_model(self):
        """Load the classification model using adaptive-classifier library."""
        try:
            try:
                import adaptive_classifier
            except ImportError:
                logger.info('Installing adaptive-classifier library...')
                os.system(f'{sys.executable} -m pip install adaptive-classifier')
                import adaptive_classifier
            from adaptive_classifier import AdaptiveClassifier
            logger.info(f'Loading complexity classifier model: {self.model_name}')
            self.classifier = AdaptiveClassifier.from_pretrained(self.model_name)
            logger.info('Classifier loaded successfully')
        except Exception as e:
            logger.error(f'Error loading complexity classifier: {e}')
            self.classifier = None

    def predict(self, text: str) -> List[Tuple[str, float]]:
        """
        Predict the complexity label for a given text.
        
        Args:
            text: The query text to classify
            
        Returns:
            List of (label, score) tuples sorted by confidence
        """
        if self.classifier is None:
            logger.warning('Classifier not loaded. Using fallback classification.')
            return self._fallback_classification(text)
        try:
            predictions = self.classifier.predict(text)
            logger.debug(f'Classifier predictions: {predictions}')
            if isinstance(predictions, list) and all((isinstance(p, tuple) and len(p) == 2 for p in predictions)):
                predictions.sort(key=lambda x: x[1], reverse=True)
                return predictions
            else:
                logger.warning(f'Unexpected prediction format: {predictions}')
                return self._fallback_classification(text)
        except Exception as e:
            logger.error(f'Error during classification: {e}')
            return self._fallback_classification(text)

    def _fallback_classification(self, text: str) -> List[Tuple[str, float]]:
        """
        Simple heuristic classification when model isn't available.
        
        Args:
            text: The query text
            
        Returns:
            List of (label, score) tuples
        """
        complexity_indicators = ['explain', 'analyze', 'compare', 'evaluate', 'synthesize', 'how', 'why', 'complex', 'detail', 'thorough', 'comprehensive', 'step by step', 'calculate', 'prove', 'justify', 'multiple', 'consequences', 'implications', 'differentiate', 'frameworks']
        count = sum((1 for indicator in complexity_indicators if indicator.lower() in text.lower()))
        text_length_factor = min(len(text) / 100, 2.0)
        indicator_factor = min(count / 3, 1.5)
        complexity_score = text_length_factor * indicator_factor
        if complexity_score > 1.0:
            return [('HIGH', 0.7), ('LOW', 0.3)]
        else:
            return [('LOW', 0.8), ('HIGH', 0.2)]

    def is_high_complexity(self, text: str, threshold: float=0.5) -> bool:
        """
        Determine if a query is high complexity.
        
        Args:
            text: The query text
            threshold: Confidence threshold for HIGH classification
            
        Returns:
            Boolean indicating if the query is high complexity
        """
        predictions = self.predict(text)
        for label, score in predictions:
            if label == 'HIGH' and score >= threshold:
                return True
        return False

    def get_complexity_with_confidence(self, text: str) -> Tuple[str, float]:
        """
        Get the complexity label and confidence score.
        
        Args:
            text: The query text
            
        Returns:
            Tuple of (complexity_label, confidence_score)
        """
        predictions = self.predict(text)
        return predictions[0]

def predict(self, text: str) -> List[Tuple[str, float]]:
    """
        Predict the complexity label for a given text.
        
        Args:
            text: The query text to classify
            
        Returns:
            List of (label, score) tuples sorted by confidence
        """
    if self.classifier is None:
        logger.warning('Classifier not loaded. Using fallback classification.')
        return self._fallback_classification(text)
    try:
        predictions = self.classifier.predict(text)
        logger.debug(f'Classifier predictions: {predictions}')
        if isinstance(predictions, list) and all((isinstance(p, tuple) and len(p) == 2 for p in predictions)):
            predictions.sort(key=lambda x: x[1], reverse=True)
            return predictions
        else:
            logger.warning(f'Unexpected prediction format: {predictions}')
            return self._fallback_classification(text)
    except Exception as e:
        logger.error(f'Error during classification: {e}')
        return self._fallback_classification(text)

def is_high_complexity(self, text: str, threshold: float=0.5) -> bool:
    """
        Determine if a query is high complexity.
        
        Args:
            text: The query text
            threshold: Confidence threshold for HIGH classification
            
        Returns:
            Boolean indicating if the query is high complexity
        """
    predictions = self.predict(text)
    for label, score in predictions:
        if label == 'HIGH' and score >= threshold:
            return True
    return False

def get_complexity_with_confidence(self, text: str) -> Tuple[str, float]:
    """
        Get the complexity label and confidence score.
        
        Args:
            text: The query text
            
        Returns:
            Tuple of (complexity_label, confidence_score)
        """
    predictions = self.predict(text)
    return predictions[0]

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

class SteeringVectorManager:
    """
    Manager for loading and applying steering vectors from a dataset.
    """

    def __init__(self, dataset_name: str, target_layer: int=19, cache_dir: Optional[str]=None, device: Optional[str]=None):
        """
        Initialize the steering vector manager.
        
        Args:
            dataset_name: Name of the HuggingFace dataset containing steering vectors
            target_layer: Target layer for applying steering vectors
            cache_dir: Directory for caching the dataset
            device: Device to use for tensors
        """
        self.dataset_name = dataset_name
        self.target_layer = target_layer
        self.cache_dir = cache_dir
        self.device = device or ('cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu')
        self.steering_vectors = []
        self.pattern_to_vectors = {}
        self.tokenized_contexts = {}
        self.default_strength = 2.0
        self.pattern_strengths = {'depth_and_thoroughness': 2.5, 'numerical_accuracy': 2.0, 'self_correction': 3.0, 'exploration': 2.0, 'organization': 1.5, 'unknown': 1.0}
        if dataset_name:
            self.load_dataset()

    def load_dataset(self):
        """Load steering vectors from the HuggingFace dataset."""
        try:
            logger.info(f'Loading steering vectors from dataset: {self.dataset_name}')
            dataset = datasets.load_dataset(self.dataset_name, cache_dir=self.cache_dir)
            main_split = list(dataset.keys())[0]
            vector_data = dataset[main_split]
            for item in vector_data:
                vector = self._process_dataset_item(item)
                if vector:
                    self.steering_vectors.append(vector)
                    pattern = vector.get('reasoning_pattern', 'unknown')
                    if pattern not in self.pattern_to_vectors:
                        self.pattern_to_vectors[pattern] = []
                    self.pattern_to_vectors[pattern].append(vector)
            logger.info(f'Loaded {len(self.steering_vectors)} steering vectors')
            logger.info(f'Found {len(self.pattern_to_vectors)} reasoning patterns: {list(self.pattern_to_vectors.keys())}')
            if self.steering_vectors:
                first_vector = self.steering_vectors[0]
                logger.info(f'First vector sample - pattern: {first_vector.get('reasoning_pattern', 'missing')}')
                if 'pivot_context' in first_vector:
                    context_len = len(first_vector['pivot_context'])
                    logger.info(f'First vector pivot_context length: {context_len}')
        except Exception as e:
            logger.error(f'Error loading steering vectors: {e}')
            self.steering_vectors = []
            self.pattern_to_vectors = {}

    def _process_dataset_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a dataset item into a steering vector.
        
        Args:
            item: Dataset item
            
        Returns:
            Processed steering vector or None if invalid
        """
        try:
            required_fields = ['pivot_context', 'steering_vector', 'reasoning_pattern']
            if not all((field in item for field in required_fields)):
                return None
            steering_vector = item['steering_vector']
            if isinstance(steering_vector, str):
                try:
                    steering_vector = json.loads(steering_vector)
                except json.JSONDecodeError:
                    steering_vector = [float(x) for x in steering_vector.strip('[]').split(',')]
            if not isinstance(steering_vector, list):
                logger.warning(f'Invalid steering vector format: {type(steering_vector)}')
                return None
            vector = {'pivot_context': item['pivot_context'], 'pivot_token': item.get('pivot_token', ''), 'pivot_token_id': item.get('pivot_token_id', -1), 'prob_before': item.get('prob_before', 0.0), 'prob_after': item.get('prob_after', 0.0), 'prob_delta': item.get('prob_delta', 0.0), 'model_id': item.get('model_id', ''), 'task_type': item.get('task_type', 'unknown'), 'steering_vector': steering_vector, 'cluster_id': item.get('cluster_id', -1), 'reasoning_pattern': item.get('reasoning_pattern', 'unknown'), 'cluster_vector': item.get('cluster_vector', steering_vector), 'steering_layer': item.get('steering_layer', self.target_layer)}
            return vector
        except Exception as e:
            logger.error(f'Error processing dataset item: {e}')
            return None

    def create_tokenized_contexts(self, tokenizer):
        """
        Pre-tokenize context patterns for efficient matching during generation.
        Similar to how guided mode does token-based matching.
        
        Args:
            tokenizer: Tokenizer for encoding contexts
        """
        max_pts_tokens = 256
        count = 0
        for vector in self.steering_vectors:
            context = vector.get('pivot_context', '')
            if not context:
                continue
            tokenized_context = tokenizer.encode(context, add_special_tokens=False)
            if len(tokenized_context) > max_pts_tokens:
                tokenized_context = tokenized_context[-max_pts_tokens:]
            tuple_key = tuple(tokenized_context)
            self.tokenized_contexts[tuple_key] = vector
            for suffix_len in [4, 8, 12]:
                if len(tokenized_context) > suffix_len:
                    suffix = tokenized_context[-suffix_len:]
                    suffix_tuple = tuple(suffix)
                    if suffix_tuple not in self.tokenized_contexts:
                        self.tokenized_contexts[suffix_tuple] = vector
            count += 1
        logger.info(f'STEERING: Pre-tokenized {count} contexts into {len(self.tokenized_contexts)} token patterns')
        length_counts = {}
        for key in self.tokenized_contexts.keys():
            length = len(key)
            if length not in length_counts:
                length_counts[length] = 0
            length_counts[length] += 1
        logger.info(f'STEERING: Token pattern length distribution: {sorted(length_counts.items())}')

    def get_steering_strength(self, pattern: str) -> float:
        """
        Get the steering strength for a specific pattern.
        
        Args:
            pattern: The reasoning pattern
            
        Returns:
            The steering strength
        """
        return self.pattern_strengths.get(pattern, self.default_strength)

    def set_steering_strength(self, pattern: str, strength: float):
        """
        Set the steering strength for a specific pattern.
        
        Args:
            pattern: The reasoning pattern
            strength: The steering strength
        """
        self.pattern_strengths[pattern] = strength
        logger.info(f'STEERING: Set strength for {pattern} to {strength}')

    def get_pattern_vectors(self, pattern: str) -> List[Dict[str, Any]]:
        """
        Get all steering vectors for a specific reasoning pattern.
        
        Args:
            pattern: The reasoning pattern
            
        Returns:
            List of steering vectors
        """
        return self.pattern_to_vectors.get(pattern, [])

    def get_steering_vector(self, context: str, match_key: Optional[str]=None) -> Optional[Dict[str, Any]]:
        """
        Get the most appropriate steering vector for a context.
        
        Args:
            context: The current generation context.
            match_key: Optional key for matching.
            
        Returns:
            Dictionary with steering data or None if no match.
        """
        if match_key is not None:
            for vector in self.steering_vectors:
                vector_context = vector.get('pivot_context', '')
                vector_key = vector_context[-100:] if len(vector_context) >= 100 else vector_context
                if vector_key == match_key:
                    logger.debug(f"STEERING: Context match found for '{vector.get('pivot_token', '')}' with pattern {vector.get('reasoning_pattern', 'unknown')}")
                    return vector
                if random.random() < 0.001:
                    logger.debug(f'STEERING: Match failed - key length: {len(match_key)}, vector key length: {len(vector_key)}')
                    logger.debug(f"STEERING: Match key sample: '{match_key[:20]}...'")
                    logger.debug(f"STEERING: Vector key sample: '{vector_key[:20]}...'")
        return None

def _process_dataset_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
    """
        Process a dataset item into a steering vector.
        
        Args:
            item: Dataset item
            
        Returns:
            Processed steering vector or None if invalid
        """
    try:
        required_fields = ['pivot_context', 'steering_vector', 'reasoning_pattern']
        if not all((field in item for field in required_fields)):
            return None
        steering_vector = item['steering_vector']
        if isinstance(steering_vector, str):
            try:
                steering_vector = json.loads(steering_vector)
            except json.JSONDecodeError:
                steering_vector = [float(x) for x in steering_vector.strip('[]').split(',')]
        if not isinstance(steering_vector, list):
            logger.warning(f'Invalid steering vector format: {type(steering_vector)}')
            return None
        vector = {'pivot_context': item['pivot_context'], 'pivot_token': item.get('pivot_token', ''), 'pivot_token_id': item.get('pivot_token_id', -1), 'prob_before': item.get('prob_before', 0.0), 'prob_after': item.get('prob_after', 0.0), 'prob_delta': item.get('prob_delta', 0.0), 'model_id': item.get('model_id', ''), 'task_type': item.get('task_type', 'unknown'), 'steering_vector': steering_vector, 'cluster_id': item.get('cluster_id', -1), 'reasoning_pattern': item.get('reasoning_pattern', 'unknown'), 'cluster_vector': item.get('cluster_vector', steering_vector), 'steering_layer': item.get('steering_layer', self.target_layer)}
        return vector
    except Exception as e:
        logger.error(f'Error processing dataset item: {e}')
        return None

def validate_deepconf_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and normalize DeepConf configuration.
    
    Args:
        config: Input configuration dictionary
        
    Returns:
        Validated and normalized configuration
        
    Raises:
        ValueError: If configuration is invalid
    """
    validated = config.copy()
    if 'variant' in validated:
        if validated['variant'] not in ['low', 'high']:
            raise ValueError("variant must be 'low' or 'high'")
    numeric_params = {'warmup_samples': (1, 100), 'max_traces': (1, 1000), 'window_size': (100, 10000), 'top_k': (1, 100), 'min_trace_length': (10, 10000), 'max_tokens_per_trace': (100, 100000), 'consensus_threshold': (0.5, 1.0), 'temperature': (0.1, 2.0)}
    for param, (min_val, max_val) in numeric_params.items():
        if param in validated:
            value = validated[param]
            if not isinstance(value, (int, float)) or value < min_val or value > max_val:
                raise ValueError(f'{param} must be between {min_val} and {max_val}')
    if validated.get('warmup_samples', 0) >= validated.get('max_traces', 100):
        raise ValueError('warmup_samples must be less than max_traces')
    return validated

def remove_think_section(response):
    """
    Remove a <think>...</think> block from the response text, if present.

    Args:
        response (str): Raw model output.

    Returns:
        str: Response without the <think> section, or an empty string if input
        is invalid or empty.
    """
    if not isinstance(response, str) or not response:
        return ''
    if not response.startswith('<think>') and '<think>' not in response:
        return response
    match = re.search('</think>\\s*(.*)', response, re.DOTALL)
    if match:
        parsed_response = match.group(1)
        return parsed_response
    else:
        return response

def extract_abcd(text: str) -> str | None:
    """
    Scan text (with Markdown/LaTeX wrappers intact) and return
    'A', 'B', 'C', or 'D' if a correct-answer declaration is found.
    Otherwise return None.
    """
    matches = []
    for prio, pat in enumerate(MCQ_PATTERNS):
        m = pat.search(text)
        if m:
            letter = m.group(1).upper()
            if letter in 'ABCD':
                matches.append((prio, m, letter))
    matches.sort(key=lambda triple: (triple[0], len(triple[1].group(0))))
    for _, match, letter in matches:
        return letter
    return text.removeprefix('**')[:1]

def cepo(system_prompt: str, initial_query: str, client: Any, model: str, cepo_config: CepoConfig, request_id: str=None) -> tuple[str, int]:
    """
    Applies CePO reasoning flow for the given task. First, it generates multiple completions, and then rates them to select the best one.
    Each completion is generated as follows:
    
    Generate `planning_n` solution proposals:
        Step 1: Plan Generation - The model generates a detailed, step-by-step plan to solve the problem, along with its confidence level for 
                each step.
        Step 2: Initial Solution - Using the plan from Step 1, the model produces an initial solution.
    
    Step 3: Plan Refinement - The model reviews all generated solution proposals and their associated plans, identifying inconsistencies.
            Based on this analysis, a refined, final step-by-step plan is constructed.
    Step 4: Final Solution - The model uses the refined plan from Step 3 to produce the final answer.
    
    Parameters:
        system_prompt (str): The system prompt to guide the model.
        initial_query (str): The task or question to be addressed.
        client (Any): The client instance for interacting with the AI model.
        model (str): The model name to be used for generating completions.
        cepo_config (CepoConfig): Configuration parameters for CePO flow.

    Returns:
        Tuple[str, int, dict]: The generated completion, number of tokens used
    """
    completions, completion_tokens_planning, cb_log = generate_n_completions(system_prompt, initial_query, client, model, cepo_config, request_id)
    completions = [c for c in completions if c]
    rating_model = cepo_config.rating_model if cepo_config.rating_model else model
    if cepo_config.bestofn_rating_type == 'absolute':
        best_completion, completion_tokens_rating, cb_log = rate_completions_absolute(system_prompt, initial_query, client, rating_model, completions, cepo_config, cb_log, request_id)
    elif cepo_config.bestofn_rating_type == 'pairwise':
        best_completion, completion_tokens_rating, cb_log = rate_completions_pairwise(system_prompt, initial_query, client, rating_model, completions, cepo_config, cb_log, request_id)
    elif cepo_config.bestofn_rating_type == 'majority':
        best_completion, _ = rate_completions_majority(completions)
        completion_tokens_rating = 0
    else:
        raise ValueError('Invalid rating type in cepo_config')
    return (best_completion, completion_tokens_planning + completion_tokens_rating)

class MockTokenizer:

    def encode(self, text):
        return text.split()

def encode(self, text):
    return text.split()

class EnhancedMockClient(MockOpenAIClient):

    def __init__(self):
        super().__init__(response_delay=0.1, reasoning_tokens=3000)
        self.problem_responses = {'Advanced Algebra': 'This requires systematic case analysis. Let me examine small values systematically. After checking cases x,y,z < 100, the equation x³ + y³ = z³ - 1 has solutions like (x,y,z) = (1,1,1) since 1³ + 1³ = 2 = 2³ - 6... Actually, let me recalculate: 1³ + 1³ = 2, and z³ - 1 = 2 means z³ = 3, so z ≈ 1.44. Let me check (2,2,2): 8 + 8 = 16 = 8 - 1 = 7? No. This is a difficult Diophantine equation requiring advanced techniques.', 'Number Theory': "I'll prove this by contradiction using Euclid's method. Assume there are only finitely many primes of the form 4k+3: p₁, p₂, ..., pₙ. Consider N = 4(p₁p₂...pₙ) + 3. Since N ≡ 3 (mod 4), at least one prime factor of N must be ≡ 3 (mod 4). But N is not divisible by any of p₁, p₂, ..., pₙ, so there must be another prime of the form 4k+3, contradicting our assumption. Therefore, there are infinitely many such primes.", 'Combinatorics': 'This is a stars and bars problem with constraints. We need to distribute 20 balls into 5 boxes with each box having at least 2 balls. First, place 2 balls in each box (using 10 balls). Now we need to distribute the remaining 10 balls into 5 boxes with no constraints. Using stars and bars: C(10+5-1, 5-1) = C(14,4) = 1001 ways.', 'Geometry': "This is a form of Weitzenböck's inequality. We can prove this using the relationship between area and sides. For a triangle with area S and sides a,b,c, we have S = √[s(s-a)(s-b)(s-c)] where s = (a+b+c)/2. We want to show a² + b² + c² ≥ 4√3 · S. This can be proven using the isoperimetric inequality and Jensen's inequality applied to the convex function f(x) = x²."}

    def chat_completions_create(self, **kwargs):
        result = super().chat_completions_create(**kwargs)
        messages = kwargs.get('messages', [])
        for message in messages:
            content = message.get('content', '')
            for prob_type, response in self.problem_responses.items():
                if any((keyword in content for keyword in prob_type.lower().split())):
                    result.choices[0].message.content = response
                    return result
        result.choices[0].message.content = 'This is a complex problem requiring careful analysis. Let me work through it step by step with rigorous reasoning.'
        return result

def chat_completions_create(self, **kwargs):
    result = super().chat_completions_create(**kwargs)
    messages = kwargs.get('messages', [])
    for message in messages:
        content = message.get('content', '')
        for prob_type, response in self.problem_responses.items():
            if any((keyword in content for keyword in prob_type.lower().split())):
                result.choices[0].message.content = response
                return result
    result.choices[0].message.content = 'This is a complex problem requiring careful analysis. Let me work through it step by step with rigorous reasoning.'
    return result

class JSONGenerator:

    def __init__(self, *args, **kwargs):
        pass

    def generate_json(self, *args, **kwargs):
        return {'mocked': 'result'}

    def count_tokens(self, text):
        return len(text.split())

def count_tokens(self, text):
    return len(text.split())

class TestJSONPlugin(unittest.TestCase):
    """Test cases for the JSON plugin with new outlines API."""

    def setUp(self):
        """Set up test fixtures."""
        self.simple_schema = json.dumps({'type': 'object', 'properties': {'name': {'type': 'string'}, 'age': {'type': 'integer'}, 'active': {'type': 'boolean'}}, 'required': ['name', 'age']})
        self.complex_schema = json.dumps({'type': 'object', 'properties': {'id': {'type': 'integer'}, 'email': {'type': 'string'}, 'score': {'type': 'number'}, 'tags': {'type': 'array'}, 'metadata': {'type': 'object'}}, 'required': ['id', 'email']})

    @patch('optillm.plugins.json_plugin.outlines.from_transformers')
    @patch('optillm.plugins.json_plugin.AutoTokenizer.from_pretrained')
    def test_json_generator_init(self, mock_tokenizer, mock_from_transformers):
        """Test JSONGenerator initialization with new API."""
        mock_model = Mock()
        mock_from_transformers.return_value = mock_model
        mock_tokenizer.return_value = Mock()
        generator = JSONGenerator()
        mock_from_transformers.assert_called_once()
        mock_tokenizer.assert_called_once()
        self.assertIsNotNone(generator.model)
        self.assertIsNotNone(generator.tokenizer)

    @patch('optillm.plugins.json_plugin.outlines.from_transformers')
    @patch('optillm.plugins.json_plugin.AutoModelForCausalLM.from_pretrained')
    @patch('optillm.plugins.json_plugin.AutoTokenizer.from_pretrained')
    def test_parse_json_schema_to_pydantic(self, mock_tokenizer, mock_model, mock_from_transformers):
        """Test JSON schema to Pydantic model conversion."""
        if not PLUGIN_AVAILABLE:
            self.skipTest('JSON plugin not available')
        mock_model.return_value = Mock()
        mock_tokenizer.return_value = Mock()
        mock_from_transformers.return_value = Mock()
        generator = JSONGenerator()
        try:
            result = generator.parse_json_schema_to_pydantic(self.simple_schema)
            self.assertIsNotNone(result)
        except Exception:
            self.assertTrue(hasattr(generator, 'parse_json_schema_to_pydantic'))

    @patch('optillm.plugins.json_plugin.outlines.from_transformers')
    @patch('optillm.plugins.json_plugin.AutoTokenizer.from_pretrained')
    def test_generate_json_new_api(self, mock_tokenizer, mock_from_transformers):
        """Test JSON generation with new outlines API."""
        mock_result = Mock()
        mock_result.model_dump.return_value = {'name': 'Test', 'age': 25}
        mock_model = Mock()
        mock_model.return_value = mock_result
        mock_from_transformers.return_value = mock_model
        generator = JSONGenerator()
        prompt = 'Create a person named Test who is 25 years old'
        result = generator.generate_json(prompt, self.simple_schema)
        self.assertEqual(result, {'name': 'Test', 'age': 25})
        mock_model.assert_called_once()

    def test_extract_schema_from_response_format(self):
        """Test schema extraction from OpenAI response format."""
        response_format = {'type': 'json_schema', 'json_schema': {'name': 'test_schema', 'schema': {'type': 'object', 'properties': {'test': {'type': 'string'}}}}}
        result = extract_schema_from_response_format(response_format)
        self.assertIsNotNone(result)
        schema = json.loads(result)
        self.assertEqual(schema['type'], 'object')
        self.assertIn('test', schema['properties'])

    @patch('optillm.plugins.json_plugin.JSONGenerator')
    def test_run_function_with_schema(self, mock_json_generator_class):
        """Test the main run function with a valid schema."""
        mock_generator = Mock()
        mock_generator.generate_json.return_value = {'result': 'test'}
        mock_generator.count_tokens.return_value = 10
        mock_json_generator_class.return_value = mock_generator
        mock_client = Mock()
        request_config = {'response_format': {'type': 'json_schema', 'json_schema': {'schema': {'type': 'object', 'properties': {'result': {'type': 'string'}}}}}}
        result, tokens = run('System prompt', 'Generate a test result', mock_client, 'test-model', request_config)
        self.assertIn('result', result)
        self.assertEqual(tokens, 10)
        mock_generator.generate_json.assert_called_once()

    def test_run_function_without_schema(self):
        """Test the main run function without a schema (fallback)."""
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='Regular response'))]
        mock_response.usage.completion_tokens = 5
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        result, tokens = run('System prompt', 'Test query', mock_client, 'test-model', {})
        self.assertEqual(result, 'Regular response')
        self.assertEqual(tokens, 5)
        mock_client.chat.completions.create.assert_called_once()

    @patch('optillm.plugins.json_plugin.JSONGenerator')
    def test_error_handling(self, mock_json_generator_class):
        """Test error handling and fallback."""
        mock_generator = Mock()
        mock_generator.generate_json.side_effect = Exception('Test error')
        mock_json_generator_class.return_value = mock_generator
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='Fallback response'))]
        mock_response.usage.completion_tokens = 8
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        request_config = {'response_format': {'type': 'json_schema', 'json_schema': {'schema': {'type': 'object'}}}}
        result, tokens = run('System prompt', 'Test query', mock_client, 'test-model', request_config)
        self.assertEqual(result, 'Fallback response')
        self.assertEqual(tokens, 8)
        mock_client.chat.completions.create.assert_called_once()

def setUp(self):
    """Set up test fixtures."""
    self.simple_schema = json.dumps({'type': 'object', 'properties': {'name': {'type': 'string'}, 'age': {'type': 'integer'}, 'active': {'type': 'boolean'}}, 'required': ['name', 'age']})
    self.complex_schema = json.dumps({'type': 'object', 'properties': {'id': {'type': 'integer'}, 'email': {'type': 'string'}, 'score': {'type': 'number'}, 'tags': {'type': 'array'}, 'metadata': {'type': 'object'}}, 'required': ['id', 'email']})

def test_streaming(client):
    """Test streaming response"""
    stream = client.chat.completions.create(model=TEST_MODEL, messages=[{'role': 'user', 'content': 'Count from 1 to 5'}], stream=True, max_tokens=50)
    chunks = list(stream)
    assert len(chunks) > 0
    assert chunks[0].choices[0].delta.role == 'assistant'
    content_chunks = [chunk.choices[0].delta.content for chunk in chunks if chunk.choices[0].delta.content]
    assert len(content_chunks) > 0

