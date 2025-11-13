# Cluster 16

def conversation_was_successful(messages) -> bool:
    conversation = f'CONVERSATION: {json.dumps(messages)}'
    result: BoolEvalResult = evaluate_with_llm_bool(CONVERSATIONAL_EVAL_SYSTEM_PROMPT, conversation)
    return result.value

def get_weather(location, time='now'):
    """Get the current weather in a given location. Location MUST be a city."""
    return json.dumps({'location': location, 'temperature': '65', 'time': time})

