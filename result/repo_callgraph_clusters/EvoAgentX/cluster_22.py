# Cluster 22

def mock_openai_completions_create(self, stream: bool=False, **kwargs):
    if stream:

        class Iterator(object):

            def __iter__(self):
                yield default_resp_chunk
        return Iterator()
    else:
        return default_resp

