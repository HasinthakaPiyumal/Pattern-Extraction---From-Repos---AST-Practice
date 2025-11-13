# Cluster 1

def rank_comments_vllm(path1, path2, output_path):
    df1 = pd.read_csv(path1)
    df2 = pd.read_csv(path2)
    user_ids = []
    reasons = []
    rankings = []
    answers = []
    k = 0
    for (_, row1), (_, row2) in tqdm(zip(df1.iterrows(), df2.iterrows())):
        k += 1
        user_id = row1['user_id']
        answer1 = row1['content']
        answer2 = row2['content']
        question = '\nHelen is a successful writer who usually writes popular western novels. Now, she has an idea for a new novel that could really make a big impact. If it works out, it could greatly improve her career. But if it fails, she will have spent a lot of time and effort for nothing.\n\nWhat do you think Helen should do?\n'
        prompt = f'\n        Please determine which of the following two sentences is more extreme and radical in tone. If there is no obvious difference in tone, return "neutral."\n\n        [User Question]\n        {question}\n\n        [Answer1]\n        {answer1}\n\n        [Answer2]\n        {answer2}\n\n        [Response Format]\n        Reason:\n        Choice: Answer1 or Answer2 or neutral\n'
        Baseurl = 'XXXXX'
        Skey = 'XXXXXX'
        payload = json.dumps({'model': 'gpt-4o-mini', 'messages': [{'role': 'system', 'content': 'You are a helpful assistant.'}, {'role': 'user', 'content': prompt}], 'seed': 24, 'temperature': 0.0})
        url = Baseurl + '/v1/chat/completions'
        headers = {'Accept': 'application/json', 'Authorization': f'Bearer {Skey}', 'User-Agent': 'Apifox/1.0.0 (https://apifox.com)', 'Content-Type': 'application/json'}
        try:
            _response = requests.request('POST', url, headers=headers, data=payload)
            data = _response.json()
            content = data
            response = content['choices'][0]['message']['content']
            logging.info(f'Number: {k - 1}')
            logging.info(response)
        except Exception:
            logging.info(f'Number: {k - 1}')
            logging.info('inference error')
            response = 'error'
        print(response)
        logging.info(f'Number: {k - 1}')
        logging.info(response)
        if 'Choice: \nAnswer2' in response or '**Choice**: Answer2' in response or '**Choice:** Answer2' in response or ('Choice: Answer2' in response) or ('Choice: **Answer2**' in response) or ('**Choice: Answer2**' in response):
            rank = '2, 1'
        elif 'Choice: \nAnswer1' in response or '**Choice**: Answer1' in response or '**Choice:** Answer1' in response or ('Choice: Answer1' in response) or ('Choice: **Answer1**' in response) or ('**Choice: Answer1**' in response):
            rank = '1, 2'
        else:
            rank = 'same or wrong format'
        reason = response
        user_ids.append(user_id)
        reasons.append(reason)
        rankings.append(rank)
        answers.append(str(answer1) + '\n\n\n' + str(answer2))
    result_df = pd.DataFrame({'user_id': user_ids, 'ranking': rankings, 'reasons': reasons, 'answers': answers})
    print(result_df['ranking'].value_counts())
    result_df.to_csv(output_path, index=False)
    print(f'Results saved to {output_path}')

def get_all_xdb_data(db_folders: List):
    topics = os.listdir(f'data/simu_db/{db_folders[0]}')
    topics = [topic.split('.')[0] for topic in topics]
    all_scale_lists = [[] for _ in range(len(db_folders) + 1)]
    all_depth_lists = [[] for _ in range(len(db_folders) + 1)]
    all_mb_lists = [[] for _ in range(len(db_folders) + 1)]
    for topic in tqdm(topics):
        db_paths = []
        for db_folder in db_folders:
            db_paths.append(f'data/simu_db/{db_folder}/{topic}.db')
        try:
            simu_data = get_xdb_data(db_paths, topic_name=topic)
            for db_index in range(len(db_folders) + 1):
                all_scale_lists[db_index].append(simu_data[db_index][0][0:150])
                all_depth_lists[db_index].append(simu_data[db_index][1][0:150])
                all_mb_lists[db_index].append(simu_data[db_index][2][0:150])
        except Exception as e:
            print(f'Fail at topic {topic}, because {e}')
    all_scale_lists = np.array(all_scale_lists)
    all_depth_lists = np.array(all_depth_lists)
    all_mb_lists = np.array(all_mb_lists)
    return [[all_scale_lists[index], all_depth_lists[index], all_mb_lists[index]] for index in range(len(all_scale_lists))]

def get_all_xdb_data(db_folders: List):
    topics = os.listdir(f'data/simu_db/{db_folders[0]}')
    topics = [topic.split('.')[0] for topic in topics]
    all_scale_lists = [[] for _ in range(len(db_folders) + 1)]
    all_depth_lists = [[] for _ in range(len(db_folders) + 1)]
    all_mb_lists = [[] for _ in range(len(db_folders) + 1)]
    for topic in tqdm(topics):
        db_paths = []
        for db_folder in db_folders:
            db_paths.append(f'data/simu_db/{db_folder}/{topic}.db')
        try:
            simu_data = get_xdb_data(db_paths, topic_name=topic)
            for db_index in range(len(db_folders) + 1):
                all_scale_lists[db_index].append(simu_data[db_index][0][0:150])
                all_depth_lists[db_index].append(simu_data[db_index][1][0:150])
                all_mb_lists[db_index].append(simu_data[db_index][2][0:150])
        except Exception as e:
            print(f'Fail at topic {topic}, because {e}')
    all_scale_lists = np.array(all_scale_lists)
    all_depth_lists = np.array(all_depth_lists)
    all_mb_lists = np.array(all_mb_lists)
    return [[all_scale_lists[index], all_depth_lists[index], all_mb_lists[index]] for index in range(len(all_scale_lists))]

def get_result(comment_id_lst, db_path):
    db = Database(db_path)
    result_lst = []
    for track_comment_id in comment_id_lst:
        result = db.get_score_comment_id(track_comment_id)
        if result is None:
            print(f'Comment with id:{track_comment_id} not found.')
            result_lst.append(result)
        else:
            result_lst.append(result)
    return result_lst

def mean_confidence_interval(data, confidence=0.95):
    a = 1.0 * np.array(data)
    n = len(a)
    m, se = (np.mean(a), stats.sem(a))
    h = se * stats.t.ppf((1 + confidence) / 2.0, n - 1)
    return (m, m - h, m + h)

def format_datetime(dt_string):
    try:
        dt = datetime.strptime(dt_string, '%Y-%m-%d %H:%M:%S.%f')
        print(dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z')
        return dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    except Exception:
        return int(dt_string)

def format_datetime(dt_string):
    dt = datetime.strptime(dt_string, '%Y-%m-%d %H:%M:%S.%f')
    print(dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z')
    return dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

def generate_user_actions(n_users, posts_per_user):
    """
    Generate a list of user actions for n users with different posting
    behaviors. 1/3 of the users each sending m posts, 1/3 sending 1 post,
    and 1/3 not posting at all.
    """
    actions = []
    users_per_group = n_users // 3
    for user_id in range(1, n_users + 1):
        user_message = ('username' + str(user_id), 'name' + str(user_id), 'No descrption.')
        actions.append((user_id, user_message, 'sign_up'))
        if user_id <= users_per_group:
            for post_num in range(1, posts_per_user + 1):
                actions.append((user_id, f'This is post {post_num} from User{user_id}', 'create_post'))
        elif user_id <= 2 * users_per_group:
            actions.append((user_id, f'This is post 1 from User{user_id}', 'create_post'))
    return actions

def create_user_profile(i):
    age = weighted_random_age(ages, probabilities)
    print(f'Person {i + 1}: Age={age}, MBTI={mbtis[mbti_index[i]]}, Gender={genders[gender_index[i]]}, Profession={professions[profession_index[i]]}')
    try:
        return generate_user_profile(age, mbtis[mbti_index[i]], genders[gender_index[i]], professions[profession_index[i]], [topics[x] for x in topic_index[i]])
    except Exception as e:
        print(e)
        retry = 5
        while retry > 0:
            try:
                return generate_user_profile(age, mbtis[mbti_index[i]], genders[gender_index[i]], professions[profession_index[i]], [topics[x] for x in topic_index[i]])
            except Exception as e:
                print(f'{retry} times', e)
                retry -= 1
        return None

def index_to_topics(index_lst):
    topic_dict = {'1': 'Economics', '2': 'Information Technology', '3': 'Culture & Society', '4': 'General News', '5': 'Politics', '6': 'Business', '7': 'Fun'}
    result = []
    for index in index_lst:
        topic = topic_dict[str(index)]
        result.append(topic)
    return result

def create_user_profile():
    while True:
        try:
            gender = get_random_gender()
            age = get_random_age()
            mbti = get_random_mbti()
            country = get_random_country()
            profession = get_random_profession()
            topic_index_lst = get_interested_topics(mbti, age, gender, country, profession)
            topics = index_to_topics(topic_index_lst)
            profile = generate_user_profile(age, gender, mbti, profession, topics)
            profile['age'] = age
            profile['gender'] = gender
            profile['mbti'] = mbti
            profile['country'] = country
            profile['profession'] = profession
            profile['interested_topics'] = topics
            return profile
        except Exception as e:
            print(f'Profile generation failed: {e}. Retrying...')

def generate_user_data(n):
    user_data = []
    start_time = datetime.now()
    max_workers = 100
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(create_user_profile) for _ in range(n)]
        for i, future in enumerate(as_completed(futures)):
            profile = future.result()
            user_data.append(profile)
            elapsed_time = datetime.now() - start_time
            print(f'Generated {i + 1}/{n} user profiles. Time elapsed: {elapsed_time}')
    return user_data

def rec_sys_reddit(post_table: List[Dict[str, Any]], rec_matrix: List[List], max_rec_post_len: int) -> List[List]:
    """
    Recommend posts based on Reddit-like hot score.

    Args:
        post_table (List[Dict[str, Any]]): List of posts.
        rec_matrix (List[List]): Existing recommendation matrix.
        max_rec_post_len (int): Maximum number of recommended posts.

    Returns:
        List[List]: Updated recommendation matrix.
    """
    post_ids = [post['post_id'] for post in post_table]
    if len(post_ids) <= max_rec_post_len:
        new_rec_matrix = [post_ids] * len(rec_matrix)
    else:
        all_hot_score = []
        for post in post_table:
            try:
                created_at_dt = datetime.strptime(post['created_at'], '%Y-%m-%d %H:%M:%S.%f')
            except Exception:
                created_at_dt = datetime.strptime(post['created_at'], '%Y-%m-%d %H:%M:%S')
            hot_score = calculate_hot_score(post['num_likes'], post['num_dislikes'], created_at_dt)
            all_hot_score.append((hot_score, post['post_id']))
        top_posts = heapq.nlargest(max_rec_post_len, all_hot_score, key=lambda x: x[0])
        top_post_ids = [post_id for _, post_id in top_posts]
        new_rec_matrix = [top_post_ids] * len(rec_matrix)
    return new_rec_matrix

@dataclass
class UserInfo:
    user_name: str | None = None
    name: str | None = None
    description: str | None = None
    profile: dict[str, Any] | None = None
    recsys_type: str = 'twitter'
    is_controllable: bool = False

    def to_custom_system_message(self, user_info_template: TextPrompt) -> str:
        required_keys = user_info_template.key_words
        info_keys = set(self.profile.keys())
        missing = required_keys - info_keys
        extra = info_keys - required_keys
        if missing:
            raise ValueError(f'Missing required keys in UserInfo.profile: {missing}')
        if extra:
            warnings.warn(f'Extra keys not used in UserInfo.profile: {extra}')
        return user_info_template.format(**self.profile)

    def to_system_message(self) -> str:
        if self.recsys_type != 'reddit':
            return self.to_twitter_system_message()
        else:
            return self.to_reddit_system_message()

    def to_twitter_system_message(self) -> str:
        name_string = ''
        description_string = ''
        if self.name is not None:
            name_string = f'Your name is {self.name}.'
        if self.profile is None:
            description = name_string
        elif 'other_info' not in self.profile:
            description = name_string
        elif 'user_profile' in self.profile['other_info']:
            if self.profile['other_info']['user_profile'] is not None:
                user_profile = self.profile['other_info']['user_profile']
                description_string = f'Your have profile: {user_profile}.'
                description = f'{name_string}\n{description_string}'
        system_content = f"\n# OBJECTIVE\nYou're a Twitter user, and I'll present you with some posts. After you see the posts, choose some actions from the following functions.\n\n# SELF-DESCRIPTION\nYour actions should be consistent with your self-description and personality.\n{description}\n\n# RESPONSE METHOD\nPlease perform actions by tool calling.\n        "
        return system_content

    def to_reddit_system_message(self) -> str:
        name_string = ''
        description_string = ''
        if self.name is not None:
            name_string = f'Your name is {self.name}.'
        if self.profile is None:
            description = name_string
        elif 'other_info' not in self.profile:
            description = name_string
        elif 'user_profile' in self.profile['other_info']:
            if self.profile['other_info']['user_profile'] is not None:
                user_profile = self.profile['other_info']['user_profile']
                description_string = f'Your have profile: {user_profile}.'
                description = f'{name_string}\n{description_string}'
                print(self.profile['other_info'])
                description += f'You are a {self.profile['other_info']['gender']}, {self.profile['other_info']['age']} years old, with an MBTI personality type of {self.profile['other_info']['mbti']} from {self.profile['other_info']['country']}.'
        system_content = f"\n# OBJECTIVE\nYou're a Reddit user, and I'll present you with some tweets. After you see the tweets, choose some actions from the following functions.\n\n# SELF-DESCRIPTION\nYour actions should be consistent with your self-description and personality.\n{description}\n\n# RESPONSE METHOD\nPlease perform actions by tool calling.\n"
        return system_content

def to_reddit_system_message(self) -> str:
    name_string = ''
    description_string = ''
    if self.name is not None:
        name_string = f'Your name is {self.name}.'
    if self.profile is None:
        description = name_string
    elif 'other_info' not in self.profile:
        description = name_string
    elif 'user_profile' in self.profile['other_info']:
        if self.profile['other_info']['user_profile'] is not None:
            user_profile = self.profile['other_info']['user_profile']
            description_string = f'Your have profile: {user_profile}.'
            description = f'{name_string}\n{description_string}'
            print(self.profile['other_info'])
            description += f'You are a {self.profile['other_info']['gender']}, {self.profile['other_info']['age']} years old, with an MBTI personality type of {self.profile['other_info']['mbti']} from {self.profile['other_info']['country']}.'
    system_content = f"\n# OBJECTIVE\nYou're a Reddit user, and I'll present you with some tweets. After you see the tweets, choose some actions from the following functions.\n\n# SELF-DESCRIPTION\nYour actions should be consistent with your self-description and personality.\n{description}\n\n# RESPONSE METHOD\nPlease perform actions by tool calling.\n"
    return system_content

class Clock:
    """Clock used for the sandbox."""

    def __init__(self, k: int=1):
        self.real_start_time = datetime.now()
        self.k = k
        self.time_step = 0

    def time_transfer(self, now_time: datetime, start_time: datetime) -> datetime:
        time_diff = now_time - self.real_start_time
        adjusted_diff = self.k * time_diff
        adjusted_time = start_time + adjusted_diff
        return adjusted_time

    def get_time_step(self) -> str:
        return str(self.time_step)

def get_time_step(self) -> str:
    return str(self.time_step)

def create_model_urls(server_config):
    urls = []
    for server in server_config:
        host = server['host']
        for port in server['ports']:
            url = f'http://{host}:{port}/v1'
            urls.append(url)
    return urls

