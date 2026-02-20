# Cluster 5

# Node: info
# Node: uuid4
# Node: decode
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

