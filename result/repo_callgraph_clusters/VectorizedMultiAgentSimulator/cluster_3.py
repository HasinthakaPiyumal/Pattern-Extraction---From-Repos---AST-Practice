# Cluster 3

def rst_jinja_render(app, _, source):
    rst_context = {'vmas': vmas}
    source[0] = app.builder.templates.render_string(source[0], rst_context)

