# Cluster 0

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
@app.get('/')
async def root():
    """Root endpoint for the AI service."""
    return {'message': 'Welcome to the AI service!'}

@app.get('/')
def read_root():
    return {'message': 'Welcome to the chatbot service', 'description': 'This service is responsible for managing chatbot conversations'}

@app.get('/')
def read_root():
    return {'message': 'Welcome to the document management service', 'description': 'This service is responsible for managing documents'}

@app.get('/collections')
def get_collections() -> List[Collection]:
    try:
        logger.info('Retrieving collections')
        db = SessionLocal()
        collections = db.query(langchain_pg_collection).all()
        return [Collection(id=str(collection.uuid), name=collection.name) for collection in collections]
    except Exception as e:
        logger.error('Error retrieving collections')
        logger.debug(f'connection string: {CONNECTION_STRING}')
        logger.error(e)
        return {'error': str(e)}
    finally:
        db.close()

# Node: SessionLocal
# Node: all
# Node: query
# Node: close
