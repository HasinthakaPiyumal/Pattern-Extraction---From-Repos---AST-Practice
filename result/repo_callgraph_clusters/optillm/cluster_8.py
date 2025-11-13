# Cluster 8

def get_expected_answer(problem_id: int) -> Optional[str]:
    """Get the expected answer for a problem"""
    problem = get_problem_by_id(problem_id)
    return problem['expected_answer'] if problem else None

def get_answer_type(problem_id: int) -> Optional[str]:
    """Get the answer type for a problem"""
    problem = get_problem_by_id(problem_id)
    return problem['answer_type'] if problem else None

