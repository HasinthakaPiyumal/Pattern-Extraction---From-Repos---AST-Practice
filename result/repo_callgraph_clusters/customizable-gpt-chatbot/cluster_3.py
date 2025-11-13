# Cluster 3

class PineconeManager:
    """
    This class is used to manage the Pinecone Indexes
    """

    def __init__(self, api_key, environment):
        pinecone.init(api_key=api_key, environment=environment)

    def list_of_indexes(self):
        try:
            pinecone_index_list = pinecone.list_indexes()
            print('List of Pinecone Indexes: ')
            print(pinecone_index_list)
            print('____________________________________________________')
            return pinecone_index_list
        except Exception as e:
            print('Error in listing the Pinecone Indexes: ', e)
            print('____________________________________________________')
            raise Exception('Error in listing the Pinecone Indexes: ', e)

    def create_index(self, index_name, dimension, metric):
        pinecone.create_index(name=index_name, dimension=dimension, metric=metric)

    def delete_index(self, index_name):
        pinecone.delete_index(index_name)

def create_index(self, index_name, dimension, metric):
    pinecone.create_index(name=index_name, dimension=dimension, metric=metric)

class PineconeIndexManager:
    """
    This class is used to manage the Pinecone Indexes
    """

    def __init__(self, pinecone_manager, index_name):
        self.pinecone_manager = pinecone_manager
        self.index_name = index_name

    def index_exists(self):
        active_indexes = self.pinecone_manager.list_of_indexes()
        return self.index_name in active_indexes

    def create_index(self, dimension, metric):
        self.pinecone_manager.create_index(self.index_name, dimension, metric)

    def delete_index(self):
        self.pinecone_manager.delete_index(self.index_name)

def create_index(self, dimension, metric):
    self.pinecone_manager.create_index(self.index_name, dimension, metric)

def build_or_update_pinecone_index(file_path, index_name, name_space):
    """
    This function is used to build or update the Pinecone Index
    """
    pinecone_index_manager = PineconeIndexManager(PineconeManager(PINECONE_API_KEY, PINECONE_ENVIRONMENT), index_name)
    loader = DocumentLoaderFactory.get_loader(file_path)
    pages = loader.load_and_split()
    if pinecone_index_manager.index_exists():
        print('Updating the model')
        pinecone_index = Pinecone.from_documents(pages, embeddings, index_name=pinecone_index_manager.index_name, namespace=PINECONE_NAMESPACE_NAME)
    else:
        print('Training the model')
        pinecone_index_manager.create_index(dimension=1536, metric='cosine')
        pinecone_index = Pinecone.from_documents(documents=pages, embedding=embeddings, index_name=pinecone_index_manager.index_name, namespace=PINECONE_NAMESPACE_NAME)
    return pinecone_index

def build_or_update_faiss_index(file_path, index_name):
    faiss_obj_path = os.path.join(MODELS_DIR, f'{index_name}.pickle')
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    loader = get_loader(file_path)
    pages = loader.load_and_split()
    if os.path.exists(faiss_obj_path):
        faiss_index = FAISS.load(faiss_obj_path)
        new_embeddings = FAISS.from_documents(pages, embeddings, index_name=index_name)
        faiss_index.add_vectors(new_embeddings)
    else:
        faiss_index = FAISS.from_documents(pages, embeddings, index_name=index_name)
    faiss_index.save(faiss_obj_path)
    return faiss_index

def get_pinecone_index(index_name, name_space):
    pinecone_manager = PineconeManager(PINECONE_API_KEY, PINECONE_ENVIRONMENT)
    pinecone_index_manager = PineconeIndexManager(pinecone_manager, index_name)
    try:
        pinecone_index = Pinecone.from_existing_index(index_name=pinecone_index_manager.index_name, embedding=embeddings, namespace=settings.PINECONE_NAMESPACE_NAME)
        return pinecone_index
    except Exception as e:
        logger.error(f'Failed to load Pinecone index: {e}')
        return None

