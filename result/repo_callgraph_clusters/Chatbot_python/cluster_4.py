# Cluster 4

def list_collections() -> List[Collection]:
    try:
        response = requests.get(f'{CHATBOT_URL}/collections')
        if response.status_code == 200:
            collections = [Collection(name=collection['name'], id=collection['id']) for collection in response.json()]
        else:
            collections = []
        return collections
    except Exception as e:
        st.error(f'Error listing collections: {e}')
        return []

# Node: get
# Node: Collection
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
@app.get('/')
def read_root():
    return {'message': 'Welcome to the chatbot service', 'description': 'This service is responsible for managing chatbot conversations'}

@app.post('/upload')
def uploadFiles(files: List[UploadFile]=File(...)) -> UploadResponse:
    """Upload files to the service."""
    try:
        collections = []
        for file in files:
            if not file.filename.endswith('.txt'):
                return {'error': 'Only .txt files are allowed', collections: []}
            logger.info('Uploading file %s', file.filename)
            with file.file as file_content:
                collection_id = file.filename if file.filename else str(uuid4())
                payload = {'collection_id': collection_id, 'document_text': file_content.read().decode('utf-8')}
                response = requests.post(f'{RETRIVAL_SERVICE_URL}/save_document/', json=payload)
                response.raise_for_status()
                collections.append(response.json().get('collection_id'))
        return UploadResponse(collections=collections)
    except Exception as e:
        logger.error(f'Error uploading files: {e}')
        return {'error': str(e), 'collections': []}

# Node: File
# Node: endswith
# Node: str
# Node: read
# Node: UploadResponse
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

@app.get('/')
def read_root():
    return {'message': 'Welcome to the document management service', 'description': 'This service is responsible for managing documents'}

