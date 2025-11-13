# Cluster 23

class Workflow:

    def __init__(self, name: str, llm_config: LLMConfig, benchmark: Benchmark):
        self.name = name
        self.llm = create_llm_instance(llm_config)
        self.benchmark = benchmark
        self.custom = operator.Custom(self.llm)
        self.answer_generate = operator.AnswerGenerate(self.llm)

    async def __call__(self, problem: str):
        """
        Implementation of the workflow
        """
        solution = await self.answer_generate(input=problem)
        return solution['answer']

def __init__(self, name: str, llm_config: LLMConfig, benchmark: Benchmark):
    self.name = name
    self.llm = create_llm_instance(llm_config)
    self.benchmark = benchmark
    self.custom = operator.Custom(self.llm)
    self.answer_generate = operator.AnswerGenerate(self.llm)

class Workflow:

    def __init__(self, name: str, llm_config: LLMConfig, benchmark: Benchmark):
        self.name = name
        self.llm = create_llm_instance(llm_config)
        self.benchmark = benchmark
        self.custom = operator.Custom(self.llm)

    async def __call__(self, problem: str):
        """
        Implementation of the workflow
        """
        solution = await self.custom(input=problem, instruction=prompt_custom.SOLVE_MATH_PROBLEM_PROMPT)
        return solution['response']

def __init__(self, name: str, llm_config: LLMConfig, benchmark: Benchmark):
    self.name = name
    self.llm = create_llm_instance(llm_config)
    self.benchmark = benchmark
    self.custom = operator.Custom(self.llm)

class Workflow:

    def __init__(self, name: str, llm_config: LLMConfig, benchmark: Benchmark):
        self.name = name
        self.llm = create_llm_instance(llm_config)
        self.benchmark = benchmark
        self.custom = operator.Custom(self.llm)
        self.custom_code_generate = operator.CustomCodeGenerate(self.llm)

    async def __call__(self, problem: str, entry_point: str):
        """
        Implementation of the workflow
        Custom operator to generate anything you want.
        But when you want to get standard code, you should use custom_code_generate operator.
        """
        solution = await self.custom_code_generate(problem=problem, entry_point=entry_point, instruction=prompt_custom.GENERATE_PYTHON_CODE_PROMPT)
        return solution['response']

def __init__(self, name: str, llm_config: LLMConfig, benchmark: Benchmark):
    self.name = name
    self.llm = create_llm_instance(llm_config)
    self.benchmark = benchmark
    self.custom = operator.Custom(self.llm)
    self.custom_code_generate = operator.CustomCodeGenerate(self.llm)

