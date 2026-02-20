# Cluster 5

# Node: info
# Node: str
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
# Node: uuid4
# Node: decode
# Node: read
# Node: UploadResponse
@app.post('/save_document')
def save_document(request: UpdateCollectionRequest):
    """Update a document in the database."""
    collection_id = request.collection_id or str(uuid4())
    documents = text_to_documents(request.document_text, {'file': collection_id})
    try:
        logger.info('Updating collection %s', collection_id)
        store = PGVector(embeddings=embeddings, collection_name=collection_id, connection=CONNECTION_STRING, use_jsonb=True)
        retriever = store.as_retriever()
        documents_id = retriever.add_documents(documents)
        return UpdateCollectionResponse(document_ids=documents_id, collection_id=collection_id)
    except Exception as e:
        logger.error(f'Error updating collection: {collection_id}')
        logger.debug(f'connection string: {CONNECTION_STRING}')
        logger.error(e)
        return {'error': str(e)}

# Node: text_to_documents
# Node: PGVector
# Node: as_retriever
# Node: add_documents
# Node: UpdateCollectionResponse
# Node: debug
@app.post('/retrieve_document')
def retrieve_document(request: RetriveDocumentRequest) -> RetriveDocumentResponse:
    """Retrieve a document from the database."""
    try:
        logger.info('Retrieving document %s', request.collection_id)
        store = PGVector(embeddings=embeddings, collection_name=request.collection_id, connection=CONNECTION_STRING, use_jsonb=True)
        retriever = store.as_retriever()
        return RetriveDocumentResponse(documents=retriever.invoke(input=request.query))
    except Exception as e:
        logger.error(f'Error retrieving document: {request.collection_id}')
        logger.debug(f'connection string: {CONNECTION_STRING}')
        logger.error(e)
        return {'error': str(e)}

# Node: RetriveDocumentResponse
# Node: invoke
def parseUploadFile(file_content: bytes) -> List[Document]:
    """Parse the content of an uploaded file into a list of Document objects."""
    logger.info('Parsing uploaded file')
    text = file_content.decode('utf-8')
    return text_to_documents(text, {})

@app.post('/upload_document')
async def upload_document(file: UploadFile=File(...)):
    """Upload a text file and save its content as documents in the database."""
    try:
        content = await file.read()
        documents = parseUploadFile(content)
        collection_id = file.filename or str(uuid4())
        logger.info('Uploading document %s', collection_id)
        store = PGVector(embeddings=embeddings, collection_name=collection_id, connection=CONNECTION_STRING, use_jsonb=True)
        retriever = store.as_retriever()
        documents_id = retriever.add_documents(documents)
        return UpdateCollectionResponse(document_ids=documents_id, collection_id=collection_id)
    except Exception as e:
        logger.error('Error uploading document')
        logger.debug(f'connection string: {CONNECTION_STRING}')
        logger.error(e)
        return {'error': str(e)}

# Node: parseUploadFile
