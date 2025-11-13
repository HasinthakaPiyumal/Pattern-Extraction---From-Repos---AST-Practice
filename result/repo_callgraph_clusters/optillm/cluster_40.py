# Cluster 40

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

def __init__(self, client, model: str, max_tokens: int=16382):
    self.client = client
    self.model = model
    self.max_tokens = max_tokens
    self.reasoning_modules = get_all_modules()
    self.completion_tokens = 0

