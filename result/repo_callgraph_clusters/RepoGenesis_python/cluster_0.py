# Cluster 0

@pytest.fixture
def api_client(base_url, check_server):

    class APIClient:

        def __init__(self, base_url):
            self.base_url = base_url
            self.session = requests.Session()
            self.session.headers.update({'Content-Type': 'application/json'})

        def get(self, endpoint, params=None):
            url = f'{self.base_url}{endpoint}'
            response = self.session.get(url, params=params)
            return response

        def post(self, endpoint, data=None):
            url = f'{self.base_url}{endpoint}'
            response = self.session.post(url, json=data)
            return response

        def put(self, endpoint, data=None):
            url = f'{self.base_url}{endpoint}'
            response = self.session.put(url, json=data)
            return response

        def delete(self, endpoint):
            url = f'{self.base_url}{endpoint}'
            response = self.session.delete(url)
            return response
    return APIClient(base_url)

# Node: APIClient
