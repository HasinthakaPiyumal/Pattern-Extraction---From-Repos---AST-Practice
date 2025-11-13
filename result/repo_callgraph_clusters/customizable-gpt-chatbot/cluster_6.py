# Cluster 6

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

def __init__(self, api_key, environment):
    pinecone.init(api_key=api_key, environment=environment)

