# Cluster 1

@frontend_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('frontend.home'))
    form = forms.LoginForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            api_key = UserClient.post_login(form)
            if api_key:
                session['user_api_key'] = api_key
                user = UserClient.get_user()
                session['user'] = user['result']
                order = OrderClient.get_order()
                if order.get('result', False):
                    session['order'] = order['result']
                flash('Welcome back, ' + user['result']['username'], 'success')
                return redirect(url_for('frontend.home'))
            else:
                flash('Cannot login', 'error')
        else:
            flash('Errors found', 'error')
    return render_template('login/index.html', form=form)

# Node: LoginForm
# Node: post_login
# Node: get_user
# Node: get_order
# Node: flash
@frontend_blueprint.route('/checkout', methods=['GET'])
def summary():
    if 'user' not in session:
        flash('Please login', 'error')
        return redirect(url_for('frontend.login'))
    if 'order' not in session:
        flash('No order found', 'error')
        return redirect(url_for('frontend.home'))
    order = OrderClient.get_order()
    if len(order['result']['items']) == 0:
        flash('No order found', 'error')
        return redirect(url_for('frontend.home'))
    OrderClient.post_checkout()
    return redirect(url_for('frontend.thank_you'))

# Node: len
# Node: post_checkout
