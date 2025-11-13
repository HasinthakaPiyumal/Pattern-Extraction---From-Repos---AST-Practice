# Cluster 3

def crawl_url(url):
    data = {'urls': [url], 'include_raw_html': True, 'word_count_threshold': 10, 'extraction_strategy': 'NoExtractionStrategy', 'chunking_strategy': 'RegexChunking'}
    response = requests.post('https://crawl4ai.com/crawl', json=data)
    response_data = response.json()
    response_data = response_data['results'][0]
    return response_data['markdown']

def crawl_url(url):
    data = {'urls': [url], 'include_raw_html': True, 'word_count_threshold': 10, 'extraction_strategy': 'NoExtractionStrategy', 'chunking_strategy': 'RegexChunking'}
    response = requests.post('https://crawl4ai.com/crawl', json=data)
    response_data = response.json()
    response_data = response_data['results'][0]
    return response_data['markdown']

