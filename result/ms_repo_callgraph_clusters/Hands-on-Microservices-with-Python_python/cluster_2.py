# Cluster 2

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
# Node: route
# Node: redirect
# Node: url_for
@frontend_blueprint.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect(url_for('frontend.home'))

# Node: clear
@frontend_blueprint.route('/product/<slug>', methods=['GET', 'POST'])
def product(slug):
    response = ProductClient.get_product(slug)
    item = response['result']
    form = forms.ItemForm(product_id=item['id'])
    if request.method == 'POST':
        if 'user' not in session:
            flash('Please login', 'error')
            return redirect(url_for('frontend.login'))
        order = OrderClient.post_add_to_cart(product_id=item['id'], qty=1)
        session['order'] = order['result']
        flash('Order has been updated', 'success')
    return render_template('product/index.html', product=item, form=form)

# Node: get_product
# Node: ItemForm
# Node: post_add_to_cart
@frontend_blueprint.route('/order/thank-you', methods=['GET'])
def thank_you():
    if 'user' not in session:
        flash('Please login', 'error')
        return redirect(url_for('frontend.login'))
    if 'order' not in session:
        flash('No order found', 'error')
        return redirect(url_for('frontend.home'))
    session.pop('order', None)
    flash('Thank you for your order', 'success')
    return render_template('order/thankyou.html')

# Node: pop
