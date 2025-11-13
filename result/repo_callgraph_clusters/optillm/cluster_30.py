# Cluster 30

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

def __init__(self, system_prompt: str, client, model: str, timeout: int=30, request_id: str=None):
    self.system_prompt = system_prompt
    self.model = model
    self.client = client
    self.timeout = timeout
    self.solver_completion_tokens = 0
    self.request_id = request_id
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

