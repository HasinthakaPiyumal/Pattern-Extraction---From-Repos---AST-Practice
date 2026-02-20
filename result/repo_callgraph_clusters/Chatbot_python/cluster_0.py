# Cluster 0

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
