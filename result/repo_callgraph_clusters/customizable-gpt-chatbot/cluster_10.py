# Cluster 10

class URLHandler:
    """
    This class is used to handle the URLs
    """

    @staticmethod
    def is_valid_url(url):
        parsed_url = urlsplit(url)
        return bool(parsed_url.scheme) and bool(parsed_url.netloc)

    @staticmethod
    def extract_links(url):
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        links = []
        for link in soup.find_all('a'):
            href = link.get('href')
            if href:
                absolute_url = urljoin(url, href)
                if URLHandler.is_valid_url(absolute_url):
                    links.append(absolute_url)
        return links

    @staticmethod
    def extract_links_from_websites(websites):
        all_links = []
        for website in websites:
            links = URLHandler.extract_links(website)
            all_links.extend(links)
        return all_links

@staticmethod
def extract_links_from_websites(websites):
    all_links = []
    for website in websites:
        links = URLHandler.extract_links(website)
        all_links.extend(links)
    return all_links

