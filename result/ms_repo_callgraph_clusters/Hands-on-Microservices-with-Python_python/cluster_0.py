# Cluster 0

class ProductClient:

    @staticmethod
    def get_product(slug):
        response = requests.request(method='GET', url='http://product:5000/api/product/' + slug)
        product = response.json()
        return product

    @staticmethod
    def get_products():
        r = requests.get('http://product:5000/api/products')
        products = r.json()
        return products

@staticmethod
def get_product(slug):
    response = requests.request(method='GET', url='http://product:5000/api/product/' + slug)
    product = response.json()
    return product

# Node: request
# Node: json
class OrderClient:

    @staticmethod
    def get_order():
        headers = {'Authorization': 'Basic ' + session['user_api_key']}
        response = requests.request(method='GET', url='http://order:5000/api/order', headers=headers)
        order = response.json()
        return order

    @staticmethod
    def update_order(items):
        url = 'http://order:5000/api/order/update'
        headers = {'Authorization': 'Basic ' + session['user_api_key']}
        response = requests.request('POST', url=url, data=items, headers=headers)
        if response:
            order = response.json()
            return order

    @staticmethod
    def post_add_to_cart(product_id, qty=1):
        payload = {'product_id': product_id, 'qty': qty}
        url = 'http://order:5000/api/order/add-item'
        headers = {'Authorization': 'Basic ' + session['user_api_key']}
        response = requests.request('POST', url=url, data=payload, headers=headers)
        if response:
            order = response.json()
            return order

    @staticmethod
    def post_checkout():
        url = 'http://order:5000/api/order/checkout'
        headers = {'Authorization': 'Basic ' + session['user_api_key']}
        response = requests.request('POST', url=url, data={}, headers=headers)
        order = response.json()
        return order

    @staticmethod
    def get_order_from_session():
        default_order = {'items': {}, 'total': 0}
        return session.get('order', default_order)

@staticmethod
def get_order():
    headers = {'Authorization': 'Basic ' + session['user_api_key']}
    response = requests.request(method='GET', url='http://order:5000/api/order', headers=headers)
    order = response.json()
    return order

@staticmethod
def update_order(items):
    url = 'http://order:5000/api/order/update'
    headers = {'Authorization': 'Basic ' + session['user_api_key']}
    response = requests.request('POST', url=url, data=items, headers=headers)
    if response:
        order = response.json()
        return order

@staticmethod
def post_add_to_cart(product_id, qty=1):
    payload = {'product_id': product_id, 'qty': qty}
    url = 'http://order:5000/api/order/add-item'
    headers = {'Authorization': 'Basic ' + session['user_api_key']}
    response = requests.request('POST', url=url, data=payload, headers=headers)
    if response:
        order = response.json()
        return order

@staticmethod
def post_checkout():
    url = 'http://order:5000/api/order/checkout'
    headers = {'Authorization': 'Basic ' + session['user_api_key']}
    response = requests.request('POST', url=url, data={}, headers=headers)
    order = response.json()
    return order

class UserClient:

    @staticmethod
    def post_login(form):
        api_key = False
        payload = {'username': form.username.data, 'password': form.password.data}
        url = 'http://user:5000/api/user/login'
        response = requests.request('POST', url=url, data=payload)
        if response:
            d = response.json()
            if d['api_key'] is not None:
                api_key = d['api_key']
        return api_key

    @staticmethod
    def does_exist(username):
        url = 'http://user:5000/api/user/' + username + '/exist'
        response = requests.request('GET', url=url)
        return response.status_code == 200

    @staticmethod
    def post_user_create(form):
        user = False
        payload = {'email': form.email.data, 'password': form.password.data, 'first_name': form.first_name.data, 'last_name': form.last_name.data, 'username': form.username.data}
        url = 'http://user:5000/api/user/create'
        response = requests.request('POST', url=url, data=payload)
        if response:
            user = response.json()
        return user

    @staticmethod
    def get_user():
        headers = {'Authorization': 'Basic ' + session['user_api_key']}
        response = requests.request(method='GET', url='http://user:5000/api/user', headers=headers)
        user = response.json()
        return user

@staticmethod
def post_login(form):
    api_key = False
    payload = {'username': form.username.data, 'password': form.password.data}
    url = 'http://user:5000/api/user/login'
    response = requests.request('POST', url=url, data=payload)
    if response:
        d = response.json()
        if d['api_key'] is not None:
            api_key = d['api_key']
    return api_key

@staticmethod
def does_exist(username):
    url = 'http://user:5000/api/user/' + username + '/exist'
    response = requests.request('GET', url=url)
    return response.status_code == 200

@staticmethod
def post_user_create(form):
    user = False
    payload = {'email': form.email.data, 'password': form.password.data, 'first_name': form.first_name.data, 'last_name': form.last_name.data, 'username': form.username.data}
    url = 'http://user:5000/api/user/create'
    response = requests.request('POST', url=url, data=payload)
    if response:
        user = response.json()
    return user

@staticmethod
def get_user():
    headers = {'Authorization': 'Basic ' + session['user_api_key']}
    response = requests.request(method='GET', url='http://user:5000/api/user', headers=headers)
    user = response.json()
    return user

