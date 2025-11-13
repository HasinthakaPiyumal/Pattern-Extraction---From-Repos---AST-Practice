# Cluster 7

def list_directory_files(url):
    urls_list = []
    url = url.replace(' ', '%20')
    request = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    response = urlopen(request).read()
    soup = BeautifulSoup(response, 'html.parser')
    a_tags = soup.find_all('a')
    for a_tag in a_tags:
        file_name = ''
        try:
            file_name = re.compile('(?<=<a href=")(.+)(?=">)').findall(str(a_tag))[0]
            if '?C=' in file_name or len(file_name) <= 3:
                raise TypeError
        except TypeError:
            file_name = a_tag.extract().get_text()
        url_new = url + file_name
        url_new = url_new.replace(' ', '%20')
        urls_list.append(url_new)
    return urls_list

def read_pdf(pdf):
    pdf_contents = ''
    for page in pdf:
        pdf_contents += str(pytesseract.image_to_string(page, config='--psm 12'))
    return pdf_contents

