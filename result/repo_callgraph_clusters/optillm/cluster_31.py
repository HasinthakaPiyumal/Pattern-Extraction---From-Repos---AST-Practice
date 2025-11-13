# Cluster 31

def plansearch(system_prompt: str, initial_query: str, client, model: str, n: int=1, request_id: str=None) -> List[str]:
    planner = PlanSearch(system_prompt, client, model, request_id)
    return (planner.solve_multiple(initial_query, n), planner.plansearch_completion_tokens)

