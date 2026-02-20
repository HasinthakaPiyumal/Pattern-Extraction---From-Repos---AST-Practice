# Cluster 0

@frontend_blueprint.route('/', methods=['GET'])
def home():
    if current_user.is_authenticated:
        session['order'] = OrderClient.get_order_from_session()
    try:
        products = ProductClient.get_products()
    except requests.exceptions.ConnectionError:
        products = {'results': []}
    return render_template('home/index.html', products=products)

# Node: get_order_from_session
# Node: get_products
# Node: render_template
