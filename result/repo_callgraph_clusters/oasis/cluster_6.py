# Cluster 6

def get_stat_list(prop_g: prop_graph):
    _, node_nums = prop_g.plot_scale_time()
    node_nums += [node_nums[-1]] * (300 - len(node_nums))
    _, depth_list = prop_g.plot_depth_time()
    depth_list += [depth_list[-1]] * (300 - len(depth_list))
    _, max_breadth_list = prop_g.plot_max_breadth_time()
    max_breadth_list += [max_breadth_list[-1]] * (300 - len(max_breadth_list))
    return [node_nums, depth_list, max_breadth_list]

def get_stat_list(prop_g: prop_graph):
    _, node_nums = prop_g.plot_scale_time()
    node_nums += [node_nums[-1]] * (300 - len(node_nums))
    _, depth_list = prop_g.plot_depth_time()
    depth_list += [depth_list[-1]] * (300 - len(depth_list))
    _, max_breadth_list = prop_g.plot_max_breadth_time()
    max_breadth_list += [max_breadth_list[-1]] * (300 - len(max_breadth_list))
    return [node_nums, depth_list, max_breadth_list]

def fine_license_start_line(lines: List[str], start_with: str) -> int:
    for i in range(len(lines)):
        if lines[i].startswith(start_with):
            return i
    return None

def find_license_end_line(lines: List[str], start_with: str) -> int:
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].startswith(start_with):
            return i
    return None

def test_rec_sys_random_all_posts():
    post_table = [{'post_id': '1'}, {'post_id': '2'}]
    rec_matrix = [[], []]
    max_rec_post_len = 2
    expected = [['1', '2'], ['1', '2']]
    result = rec_sys_random(post_table, rec_matrix, max_rec_post_len)
    assert result == expected

def test_rec_sys_reddit_all_posts():
    post_table = [{'post_id': '1'}, {'post_id': '2'}]
    rec_matrix = [[], []]
    max_rec_post_len = 2
    expected = [['1', '2'], ['1', '2']]
    result = rec_sys_reddit(post_table, rec_matrix, max_rec_post_len)
    assert result == expected

def test_rec_sys_personalized_all_posts():
    user_table = [{'user_id': 0, 'bio': 'I like cats'}, {'user_id': 1, 'bio': 'I like dogs'}]
    post_table = [{'post_id': '1', 'user_id': 2, 'content': 'I like dogs'}, {'post_id': '2', 'user_id': 3, 'content': 'I like cats'}]
    trace_table = []
    rec_matrix = [[], []]
    max_rec_post_len = 2
    expected = [['1', '2'], ['1', '2']]
    result = rec_sys_personalized(user_table, post_table, trace_table, rec_matrix, max_rec_post_len)
    assert result == expected

def test_rec_sys_personalized_twhin():
    user_table = [{'user_id': 0, 'bio': 'I like cats', 'num_followers': 3}, {'user_id': 1, 'bio': 'I like dogs', 'num_followers': 5}, {'user_id': 2, 'bio': '', 'num_followers': 5}, {'user_id': 3, 'bio': '', 'num_followers': 5}]
    post_table = [{'post_id': '1', 'user_id': 2, 'content': 'I like dogs', 'created_at': '0'}, {'post_id': '2', 'user_id': 3, 'content': 'I like cats', 'created_at': '0'}]
    trace_table = []
    rec_matrix = [[], [], [], []]
    max_rec_post_len = 2
    latest_post_count = len(post_table)
    expected = [['1', '2'], ['1', '2'], ['1', '2'], ['1', '2']]
    reset_globals()
    result = rec_sys_personalized_twh(user_table, post_table, latest_post_count, trace_table, rec_matrix, max_rec_post_len, current_time=1)
    assert result == expected

def test_rec_sys_random_sample_posts():
    post_table = [{'post_id': '1'}, {'post_id': '2'}, {'post_id': '3'}]
    rec_matrix = [[], []]
    max_rec_post_len = 2
    result = rec_sys_random(post_table, rec_matrix, max_rec_post_len)
    for rec in result:
        assert len(rec) == max_rec_post_len
        for post_id in rec:
            assert post_id in ['1', '2', '3']

def test_rec_sys_reddit_sample_posts():
    post_table = [{'post_id': '1', 'num_likes': 100000, 'num_dislikes': 25, 'created_at': '2024-06-25 12:00:00.222000'}, {'post_id': '2', 'num_likes': 90, 'num_dislikes': 30, 'created_at': '2024-06-26 12:00:00.321009'}, {'post_id': '3', 'num_likes': 75, 'num_dislikes': 50, 'created_at': '2024-06-27 12:00:00.123009'}, {'post_id': '4', 'num_likes': 70, 'num_dislikes': 50, 'created_at': '2024-06-27 13:00:00.321009'}]
    rec_matrix = [[], []]
    max_rec_post_len = 3
    result = rec_sys_reddit(post_table, rec_matrix, max_rec_post_len)
    for rec in result:
        assert len(rec) == max_rec_post_len
        for post_id in rec:
            assert post_id in ['3', '4', '1']

def test_rec_sys_personalized_sample_posts():
    user_table = [{'user_id': 0, 'bio': 'I like cats'}, {'user_id': 1, 'bio': 'I like dogs'}]
    post_table = [{'post_id': '1', 'user_id': 2, 'content': 'I like dogs'}, {'post_id': '2', 'user_id': 3, 'content': 'I like cats'}, {'post_id': '3', 'user_id': 4, 'content': 'I like birds'}]
    trace_table = []
    rec_matrix = [[], []]
    max_rec_post_len = 2
    result = rec_sys_personalized(user_table, post_table, trace_table, rec_matrix, max_rec_post_len)
    for rec in result:
        assert len(rec) == max_rec_post_len
        for post_id in rec:
            assert post_id in ['1', '2', '3']
    for i in range(len(result)):
        if i == 0:
            assert result[i] == ['2', '1']
        if i == 1:
            assert result[i] == ['1', '2']

def test_rec_sys_personalized_twhin_sample_posts():
    user_table = [{'user_id': 0, 'bio': 'I like cats', 'num_followers': 3}, {'user_id': 1, 'bio': 'I like dogs', 'num_followers': 3}, {'user_id': 2, 'bio': '', 'num_followers': 3}, {'user_id': 3, 'bio': '', 'num_followers': 3}, {'user_id': 4, 'bio': '', 'num_followers': 3}]
    post_table = [{'post_id': '1', 'user_id': 2, 'content': 'I like dogs', 'created_at': '0'}, {'post_id': '2', 'user_id': 3, 'content': 'I like cats', 'created_at': '0'}, {'post_id': '3', 'user_id': 4, 'content': 'I like birds', 'created_at': '0'}]
    trace_table = []
    rec_matrix = [[], [], [], [], []]
    max_rec_post_len = 2
    latest_post_count = len(post_table)
    reset_globals()
    result = rec_sys_personalized_twh(user_table, post_table, latest_post_count, trace_table, rec_matrix, max_rec_post_len, current_time=1)
    for rec in result:
        assert len(rec) == max_rec_post_len
        for post_id in rec:
            assert post_id in ['1', '2', '3']
    for i in range(len(result)):
        if i == 0:
            assert result[i] == ['2', '1']
        if i == 1:
            assert result[i] == ['1', '2']

def gen_topics():
    elements = list(range(8))
    combinations = list(itertools.combinations(elements, 2))
    expanded_combinations = []
    while len(expanded_combinations) < total:
        expanded_combinations.extend(combinations)
    expanded_combinations = expanded_combinations[:total]
    random.shuffle(expanded_combinations)
    return expanded_combinations

def rec_sys_random(post_table: List[Dict[str, Any]], rec_matrix: List[List], max_rec_post_len: int) -> List[List]:
    """
    Randomly recommend posts to users.

    Args:
        user_table (List[Dict[str, Any]]): List of users.
        post_table (List[Dict[str, Any]]): List of posts.
        trace_table (List[Dict[str, Any]]): List of user interactions.
        rec_matrix (List[List]): Existing recommendation matrix.
        max_rec_post_len (int): Maximum number of recommended posts.

    Returns:
        List[List]: Updated recommendation matrix.
    """
    post_ids = [post['post_id'] for post in post_table]
    new_rec_matrix = []
    if len(post_ids) <= max_rec_post_len:
        new_rec_matrix = [post_ids] * len(rec_matrix)
    else:
        for _ in range(len(rec_matrix)):
            new_rec_matrix.append(random.sample(post_ids, max_rec_post_len))
    return new_rec_matrix

def get_like_post_id(user_id, action, trace_table):
    """
    Get the post IDs that a user has liked or unliked.

    Args:
        user_id (str): ID of the user.
        action (str): Type of action (like or unlike).
        post_table (list): List of posts.
        trace_table (list): List of user interactions.

    Returns:
        list: List of post IDs.
    """
    trace_post_ids = [literal_eval(trace['info'])['post_id'] for trace in trace_table if trace['user_id'] == user_id and trace['action'] == action]
    'Only take the last 5 liked posts, if not enough, pad with the most\n    recently liked post. Only take IDs, not content, because calculating\n    embeddings for all posts again is very time-consuming, especially when the\n    number of agents is large'
    if len(trace_post_ids) < 5 and len(trace_post_ids) > 0:
        trace_post_ids += [trace_post_ids[-1]] * (5 - len(trace_post_ids))
    elif len(trace_post_ids) > 5:
        trace_post_ids = trace_post_ids[-5:]
    else:
        trace_post_ids = [0]
    return trace_post_ids

def coarse_filtering(input_list, scale):
    """
    Coarse filtering posts and return selected elements with their indices.
    """
    if len(input_list) <= scale:
        sampled_indices = range(len(input_list))
        return (input_list, sampled_indices)
    else:
        sampled_indices = random.sample(range(len(input_list)), scale)
        sampled_elements = [input_list[idx] for idx in sampled_indices]
        return (sampled_elements, sampled_indices)

def swap_random_posts(rec_post_ids, post_ids, swap_percent=0.1):
    """
    Swap a percentage of recommended posts with random posts.

    Args:
        rec_post_ids (list): List of recommended post IDs.
        post_ids (list): List of all post IDs.
        swap_percent (float): Percentage of posts to swap.

    Returns:
        list: Updated list of recommended post IDs.
    """
    num_to_swap = int(len(rec_post_ids) * swap_percent)
    posts_to_swap = random.sample(post_ids, num_to_swap)
    indices_to_replace = random.sample(range(len(rec_post_ids)), num_to_swap)
    for idx, new_post in zip(indices_to_replace, posts_to_swap):
        rec_post_ids[idx] = new_post
    return rec_post_ids

def generate_post_vector(model: AutoModel, tokenizer: AutoTokenizer, texts, batch_size):
    all_outputs = []
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i + batch_size]
        batch_outputs = process_batch(model, tokenizer, batch_texts)
        all_outputs.append(batch_outputs)
    all_outputs_tensor = torch.cat(all_outputs, dim=0)
    return all_outputs_tensor.cpu()

def generate_post_vector_openai(texts: List[str], batch_size: int=100):
    """
    Generate embeddings using OpenAI API

    Args:
        texts: List of texts to process
        batch_size: Size of each batch
    """
    openai_embedding = OpenAIEmbedding(model_type=EmbeddingModelType.TEXT_EMBEDDING_3_SMALL)
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i + batch_size]
        cleaned_texts = [text.strip() if text and isinstance(text, str) else 'empty' for text in batch_texts]
        batch_embeddings = openai_embedding.embed_list(objs=cleaned_texts)
        batch_tensor = torch.tensor(batch_embeddings)
        all_embeddings.append(batch_tensor)
    return torch.cat(all_embeddings, dim=0)

