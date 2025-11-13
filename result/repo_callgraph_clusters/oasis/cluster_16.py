# Cluster 16

def load_list(path):
    with open(path, 'rb') as file:
        loaded_list = pickle.load(file)
    return loaded_list

def load_list(path):
    with open(path, 'rb') as file:
        loaded_list = pickle.load(file)
    return loaded_list

def main(exp_info_file_path, db_path, exp_name, folder_path):
    with open(exp_info_file_path, 'r') as file:
        exp_info = json.load(file)
    up_result = get_result(exp_info['up_comment_id'], db_path)
    down_result = get_result(exp_info['down_comment_id'], db_path)
    control_result = get_result(exp_info['control_comment_id'], db_path)
    print('up_result:', up_result, 'down_result:', down_result, 'control_result', control_result)
    visualization(up_result, down_result, control_result, exp_name, folder_path)

def update_license_in_file(file_path: str, license_template_path: str, start_line_start_with: str, end_line_start_with: str) -> bool:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    with open(license_template_path, 'r', encoding='utf-8') as f:
        new_license = f.read().strip()
    maybe_existing_licenses = re.findall('^#.*?(?=\\n)', content, re.MULTILINE | re.DOTALL)
    start_index = fine_license_start_line(maybe_existing_licenses, start_line_start_with)
    end_index = find_license_end_line(maybe_existing_licenses, end_line_start_with)
    if start_index is not None and end_index is not None:
        maybe_existing_licenses = maybe_existing_licenses[start_index:end_index + 1]
    else:
        maybe_existing_licenses = None
    if maybe_existing_licenses:
        maybe_old_licenses = '\n'.join(maybe_existing_licenses)
        if maybe_old_licenses.strip() != new_license.strip():
            replaced_content = content.replace(maybe_old_licenses, new_license)
            with open(file_path, 'w') as f:
                f.write(replaced_content)
            print(f'Replaced license in {file_path}')
            return True
        else:
            return False
    else:
        with open(file_path, 'w') as f:
            f.write(new_license + '\n' + content)
        print(f'Added license to {file_path}')
        return True

def get_random_gender():
    return random.choices(genders, gender_ratio)[0]

def get_random_age():
    group = random.choices(age_groups, age_ratio)[0]
    if group == 'underage':
        return random.randint(10, 17)
    elif group == '18-29':
        return random.randint(18, 29)
    elif group == '30-49':
        return random.randint(30, 49)
    elif group == '50-64':
        return random.randint(50, 64)
    else:
        return random.randint(65, 100)

def get_random_mbti():
    return random.choices(mbti_types, p_mbti)[0]

def get_random_country():
    country = random.choices(countries, country_ratio)[0]
    if country == 'Other':
        response = client.chat.completions.create(model='gpt-3.5-turbo', messages=[{'role': 'system', 'content': 'Select a real country name randomly:'}])
        return response.choices[0].message.content.strip()
    return country

def get_random_profession():
    return random.choices(professions, p_professions)[0]

def get_interested_topics(mbti, age, gender, country, profession):
    prompt = f"Based on the provided personality traits, age, gender and profession, please select 2-3 topics of interest from the given list.\n    Input:\n        Personality Traits: {mbti}\n        Age: {age}\n        Gender: {gender}\n        Country: {country}\n        Profession: {profession}\n    Available Topics:\n        1. Economics: The study and management of production, distribution, and consumption of goods and services. Economics focuses on how individuals, businesses, governments, and nations make choices about allocating resources to satisfy their wants and needs, and tries to determine how these groups should organize and coordinate efforts to achieve maximum output.\n        2. IT (Information Technology): The use of computers, networking, and other physical devices, infrastructure, and processes to create, process, store, secure, and exchange all forms of electronic data. IT is commonly used within the context of business operations as opposed to personal or entertainment technologies.\n        3. Culture & Society: The way of life for an entire society, including codes of manners, dress, language, religion, rituals, norms of behavior, and systems of belief. This topic explores how cultural expressions and societal structures influence human behavior, relationships, and social norms.\n        4. General News: A broad category that includes current events, happenings, and trends across a wide range of areas such as politics, business, science, technology, and entertainment. General news provides a comprehensive overview of the latest developments affecting the world at large.\n        5. Politics: The activities associated with the governance of a country or other area, especially the debate or conflict among individuals or parties having or hoping to achieve power. Politics is often a battle over control of resources, policy decisions, and the direction of societal norms.\n        6. Business: The practice of making one's living through commerce, trade, or services. This topic encompasses the entrepreneurial, managerial, and administrative processes involved in starting, managing, and growing a business entity.\n        7. Fun: Activities or ideas that are light-hearted or amusing. This topic covers a wide range of entertainment choices and leisure activities that bring joy, laughter, and enjoyment to individuals and groups.\n    Output:\n    [list of topic numbers]\n    Ensure your output could be parsed to **list**, don't output anything else."
    response = client.chat.completions.create(model='gpt-3.5-turbo', messages=[{'role': 'system', 'content': prompt}])
    topics = response.choices[0].message.content.strip()
    return json.loads(topics)

def generate_user_profile(age, gender, mbti, profession, topics):
    prompt = f'Please generate a social media user profile based on the provided personal information, including a real name, username, user bio, and a new user persona. The focus should be on creating a fictional background story and detailed interests based on their hobbies and profession.\n    Input:\n        age: {age}\n        gender: {gender}\n        mbti: {mbti}\n        profession: {profession}\n        interested topics: {topics}\n    Output:\n    {{\n        "realname": "str",\n        "username": "str",\n        "bio": "str",\n        "persona": "str"\n    }}\n    Ensure the output can be directly parsed to **JSON**, do not output anything else.'
    response = client.chat.completions.create(model='gpt-3.5-turbo', messages=[{'role': 'system', 'content': prompt}])
    profile = response.choices[0].message.content.strip()
    return json.loads(profile)

def save_user_data(user_data, filename):
    with open(filename, 'w') as f:
        json.dump(user_data, f, ensure_ascii=False, indent=2)

