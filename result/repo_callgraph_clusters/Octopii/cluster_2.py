# Cluster 2

def search_pii(file_path):
    contains_faces = 0
    if file_utils.is_image(file_path):
        image = cv2.imread(file_path)
        contains_faces = image_utils.scan_image_for_people(image)
        original, intelligible = image_utils.scan_image_for_text(image)
        text = original
    elif file_utils.is_pdf(file_path):
        pdf_pages = convert_from_path(file_path, 400)
        for page in pdf_pages:
            contains_faces = image_utils.scan_image_for_people(page)
            original, intelligible = image_utils.scan_image_for_text(page)
            text = original
    else:
        text = textract.process(file_path).decode()
        intelligible = text_utils.string_tokenizer(text)
    addresses = text_utils.regional_pii(text)
    emails = text_utils.email_pii(text, rules)
    phone_numbers = text_utils.phone_pii(text, rules)
    keywords_scores = text_utils.keywords_classify_pii(rules, intelligible)
    score = max(keywords_scores.values())
    pii_class = list(keywords_scores.keys())[list(keywords_scores.values()).index(score)]
    country_of_origin = rules[pii_class]['region']
    identifiers = text_utils.id_card_numbers_pii(text, rules)
    if score < 5:
        pii_class = None
    if len(identifiers) != 0:
        identifiers = identifiers[0]['result']
    if temp_dir in file_path:
        file_path = file_path.replace(temp_dir, '')
        file_path = urllib.parse.unquote(file_path)
    result = {'file_path': file_path, 'pii_class': pii_class, 'score': score, 'country_of_origin': country_of_origin, 'faces': contains_faces, 'identifiers': identifiers, 'emails': emails, 'phone_numbers': phone_numbers, 'addresses': addresses}
    return result

def is_pdf(file_path):
    try:
        convert_from_path(file_path, 100)
        return True
    except:
        return False

