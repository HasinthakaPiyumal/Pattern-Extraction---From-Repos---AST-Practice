# Cluster 29

def check_url(match_tuple: MatchTuple, http_session: requests.Session) -> Tuple[bool, str]:
    """Check if a URL is reachable."""
    try:
        result = http_session.head(match_tuple.link, timeout=5, allow_redirects=True)
        return (result.ok or result.status_code in OK_STATUS_CODES, f'status code = {result.status_code}')
    except (requests.ConnectionError, requests.Timeout):
        return (False, 'connection error')

