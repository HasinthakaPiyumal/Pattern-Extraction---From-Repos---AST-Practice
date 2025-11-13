# Cluster 52

@app.route('/')
def index():
    return render_template('index.html', name=name, movies=movies)

