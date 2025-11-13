# Cluster 4

def setup(app):

    def rst_jinja_render(app, _, source):
        rst_context = {'vmas': vmas}
        source[0] = app.builder.templates.render_string(source[0], rst_context)
    app.connect('source-read', rst_jinja_render)
    app.add_js_file('js/version_alert.js')

