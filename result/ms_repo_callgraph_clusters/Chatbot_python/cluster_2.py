# Cluster 2

# Node: json
# Node: error
def answer_question(question, docs) -> str:
    try:
        context = f"You are an AI assistant with access to a collection of relevant documents. \nUse the following information to provide accurate and helpful responses to user questions:\n<docs>\n{docs}\n</docs>\nBased on the above information, please provide the most suitable and detailed response to the following user's question.\n<question>\n{question}\n</question>\n"
        generate_payload = {'model': 'gemma:2b', 'prompt': context, 'stream': False}
        response = requests.post(f'{LLM_SERVICE_URL}/api/generate', json=generate_payload)
        response.raise_for_status()
        output = response.json()
        return output['response']
    except Exception as e:
        logger.error(f'Error answering question: {question}')
        logger.error(e)
        return 'I am sorry, There was an error processing your request'

# Node: raise_for_status
@app.get('/collectionChat/{conversation_id}')
async def get_conversation(conversation_id: str) -> Conversation:
    """Get the conversation from the Redis store."""
    try:
        logger.info('Retrieving initial id %s', conversation_id)
        existing_conversation_json = r.get(conversation_id)
        if existing_conversation_json:
            existing_conversation = json.loads(existing_conversation_json)
            return existing_conversation
        else:
            return Conversation(conversation=[{'role': 'assistant', 'content': 'hi how can i help you?'}])
    except Exception as e:
        logger.error('Error retrieving conversation %s', e)
        return {'error': e}

# Node: loads
# Node: Conversation
@app.post('/ask/{conversation_id}')
async def post_conversation(request: postConversationModel) -> Message:
    """Send the conversation to the AI model and return the response."""
    conversation_id, question = (request.conversation_id, request.question)
    logger.info('Sending Conversation with ID %s to ', conversation_id)
    try:
        existing_conversation_json = r.get(conversation_id)
        if existing_conversation_json:
            existing_conversation = json.loads(existing_conversation_json)
        else:
            existing_conversation = {'conversation': [{'role': 'system', 'content': 'You are a helpful assistant.'}]}
        existing_conversation['conversation'].append({'role': 'user', 'content': question})
        docs = requests.post(f'{RETRIVAL_SERVICE_URL}/retrieve_document/', json={'query': question, 'collection_id': conversation_id}).json()['documents']
        docs = format_docs(docs=docs)
        response = requests.post(f'{AI_SERVICE_URL}/ask/{conversation_id}', json={'conversation_id': conversation_id, 'question': question, 'docs': docs})
        response.raise_for_status()
        assistant_message = response.json()['answer']
        bot_message = {'role': 'assistant', 'content': assistant_message}
        existing_conversation['conversation'].append(bot_message)
        r.set(conversation_id, json.dumps(existing_conversation))
        return bot_message
    except Exception as e:
        logger.error('Error processing conversation %s', e)
        return {'error': e}

# Node: format_docs
# Node: set
# Node: dumps
@app.get('/collections')
def list_collections():
    """List all collections."""
    try:
        response = requests.get(f'{RETRIVAL_SERVICE_URL}/collections/')
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f'Error listing collections: {e}')
        return {'error': str(e)}

