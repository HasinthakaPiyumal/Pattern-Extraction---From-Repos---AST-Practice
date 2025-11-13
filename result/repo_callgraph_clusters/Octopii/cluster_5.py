# Cluster 5

def email_pii(text, rules):
    email_rules = rules['Email']['regex']
    email_addresses = re.findall(email_rules, text)
    email_addresses = list(set(filter(None, email_addresses)))
    return email_addresses

def phone_pii(text, rules):
    phone_rules = rules['Phone Number']['regex']
    phone_numbers = re.findall(phone_rules, text)
    phone_numbers = list(itertools.chain(*phone_numbers))
    phone_numbers = list(set(filter(None, phone_numbers)))
    return phone_numbers

def id_card_numbers_pii(text, rules):
    results = []
    regional_regexes = {}
    for key in rules.keys():
        region = rules[key]['region']
        if region is not None:
            regional_regexes[key] = rules[key]
    for key in regional_regexes.keys():
        region = rules[key]['region']
        rule = rules[key]['regex']
        try:
            match = re.findall(rule, text)
        except:
            match = []
        if len(match) > 0:
            result = {'identifier_class': key, 'result': list(set(match))}
            results.append(result)
    return results

