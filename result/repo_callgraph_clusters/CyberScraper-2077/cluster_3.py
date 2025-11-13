# Cluster 3

def get_redirect_uri():
    return st.get_option('server.baseUrlPath') or 'http://localhost:8501'

