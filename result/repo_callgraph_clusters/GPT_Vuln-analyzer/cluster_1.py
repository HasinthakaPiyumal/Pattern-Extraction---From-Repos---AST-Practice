# Cluster 1

def get_api_keys():
    return {'geoip_api_key': os.getenv('GEOIP_API_KEY'), 'openai_api_key': os.getenv('OPENAI_API_KEY'), 'bard_api_key': os.getenv('BARD_API_KEY'), 'runpod_api_key': os.getenv('RUNPOD_API_KEY'), 'runpod_endpoint_id': os.getenv('RUNPOD_ENDPOINT_ID')}

