# Cluster 33

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

