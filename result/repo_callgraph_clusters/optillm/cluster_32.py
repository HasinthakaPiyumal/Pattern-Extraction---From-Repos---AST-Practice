# Cluster 32

def extract_clean_answer(text: str, mode: str='auto') -> str:
    """
    Extract clean final answer from MARS synthesis text

    Args:
        text: Full synthesis output with reasoning
        mode: 'auto', 'code', 'math', or 'none'

    Returns:
        Clean final answer without intermediate reasoning
    """
    if mode == 'none':
        return text
    if mode == 'auto':
        mode = detect_answer_type(text)
    if mode == 'code':
        return extract_code_answer(text)
    elif mode == 'math':
        return extract_math_answer(text)
    else:
        return extract_generic_answer(text)

