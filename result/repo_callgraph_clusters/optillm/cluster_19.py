# Cluster 19

def rate_completions_majority(completions: list[str], last_n_chars: int=150) -> tuple[str, int, dict]:
    mcq_majority, count = majority_vote_mcq(completions, last_n_chars)
    if mcq_majority is None:
        return majority_vote_math(completions, last_n_chars)
    return (mcq_majority, count)

