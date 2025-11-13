# Cluster 8

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

def delete_index(self, index_name):
    pinecone.delete_index(index_name)

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

def delete_index(self):
    self.pinecone_manager.delete_index(self.index_name)

