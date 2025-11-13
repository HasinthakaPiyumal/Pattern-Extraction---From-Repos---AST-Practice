# Cluster 2

def setup(app):
    warnings.filterwarnings(action='ignore', category=UserWarning, message='.*Container node skipped.*')
    app.add_js_file('js/top-navigation.js', defer='defer')
    app.add_js_file('https://cdn.jsdelivr.net/npm/@docsearch/js@3.3.3/dist/umd/index.js', defer='defer')
    app.add_js_file('js/algolia.js', defer='defer')

