# Cluster 51

def test_postprocess_group_chat_results():
    """Test postprocessing of group chat results."""
    messages = [{'name': 'Agent1', 'content': 'Hello', 'role': 'user'}, {'name': 'Agent2', 'content': 'Hi there', 'role': 'user'}]
    result = postprocess_group_chat_results(messages)
    assert '<SENDER>: Agent1 </SENDER>' in result[0]['content']
    assert '<SENDER>: Agent2 </SENDER>' in result[1]['content']
    assert result[0]['role'] == 'assistant'
    assert result[1]['role'] == 'assistant'

def test_postprocess_group_chat_results_empty_content():
    """Test postprocessing with empty content."""
    messages = [{'name': 'Agent1', 'content': '', 'role': 'user'}, {'name': 'Agent2', 'content': None, 'role': 'user'}]
    result = postprocess_group_chat_results(messages)
    assert result[0]['content'] == ''
    assert result[1]['content'] is None
    assert result[0]['role'] == 'assistant'
    assert result[1]['role'] == 'assistant'

