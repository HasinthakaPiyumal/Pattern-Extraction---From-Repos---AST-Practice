# Cluster 5

# Node: validate_on_submit
@frontend_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    form = forms.RegisterForm(request.form)
    if request.method == 'POST':
        if form.validate_on_submit():
            username = form.username.data
            user = UserClient.does_exist(username)
            if user:
                flash('Please try another username', 'error')
                return render_template('register/index.html', form=form)
            else:
                user = UserClient.post_user_create(form)
                if user:
                    flash('Thanks for registering, please login', 'success')
                    return redirect(url_for('frontend.login'))
        else:
            flash('Errors found', 'error')
    return render_template('register/index.html', form=form)

# Node: RegisterForm
# Node: does_exist
# Node: post_user_create
