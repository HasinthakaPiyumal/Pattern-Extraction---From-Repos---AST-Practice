# Cluster 22

def get_dpeth(G: nx.Graph, source=0):
    dfs_tree = nx.dfs_tree(G, source=source)
    max_depth = max(nx.single_source_shortest_path_length(dfs_tree, source=source).values())
    return max_depth

def generate_random_number(thresh):
    return 1 if random.random() <= thresh else 0

def calculate_hot_score(num_likes: int, num_dislikes: int, created_at: datetime) -> int:
    """
    Compute the hot score for a post.

    Args:
        num_likes (int): Number of likes.
        num_dislikes (int): Number of dislikes.
        created_at (datetime): Creation time of the post.

    Returns:
        int: Hot score of the post.

    Reference:
        https://medium.com/hacking-and-gonzo/how-reddit-ranking-algorithms-work-ef111e33d0d9
    """
    s = num_likes - num_dislikes
    order = log(max(abs(s), 1), 10)
    sign = 1 if s > 0 else -1 if s < 0 else 0
    epoch = datetime(1970, 1, 1)
    td = created_at - epoch
    epoch_seconds_result = td.days * 86400 + td.seconds + float(td.microseconds) / 1000000.0
    seconds = epoch_seconds_result - 1134028003
    return round(sign * order + seconds / 45000, 7)

def rec_sys_personalized(user_table: List[Dict[str, Any]], post_table: List[Dict[str, Any]], trace_table: List[Dict[str, Any]], rec_matrix: List[List], max_rec_post_len: int) -> List[List]:
    """
    Recommend posts based on personalized similarity scores.

    Args:
        user_table (List[Dict[str, Any]]): List of users.
        post_table (List[Dict[str, Any]]): List of posts.
        trace_table (List[Dict[str, Any]]): List of user interactions.
        rec_matrix (List[List]): Existing recommendation matrix.
        max_rec_post_len (int): Maximum number of recommended posts.

    Returns:
        List[List]: Updated recommendation matrix.
    """
    global model
    if model is None or isinstance(model, tuple):
        model = get_recsys_model(recsys_type='twitter')
    post_ids = [post['post_id'] for post in post_table]
    print(f'Running personalized recommendation for {len(user_table)} users...')
    start_time = time.time()
    new_rec_matrix = []
    if len(post_ids) <= max_rec_post_len:
        new_rec_matrix = [post_ids] * len(rec_matrix)
    else:
        user_bios = [user['bio'] if 'bio' in user and user['bio'] is not None else '' for user in user_table]
        post_contents = [post['content'] for post in post_table]
        if model:
            user_embeddings = model.encode(user_bios, convert_to_tensor=True, device=device)
            post_embeddings = model.encode(post_contents, convert_to_tensor=True, device=device)
            dot_product = torch.matmul(user_embeddings, post_embeddings.T)
            user_norms = torch.norm(user_embeddings, dim=1)
            post_norms = torch.norm(post_embeddings, dim=1)
            similarities = dot_product / (user_norms[:, None] * post_norms[None, :])
        else:
            similarities = torch.rand(len(user_table), len(post_table))
        for user_index, user in enumerate(user_table):
            filtered_post_indices = [i for i, post in enumerate(post_table) if post['user_id'] != user['user_id']]
            user_similarities = similarities[user_index, filtered_post_indices]
            filtered_post_ids = [post_table[i]['post_id'] for i in filtered_post_indices]
            _, top_indices = torch.topk(user_similarities, k=min(max_rec_post_len, len(filtered_post_ids)))
            top_post_ids = [filtered_post_ids[i] for i in top_indices.tolist()]
            new_rec_matrix.append(top_post_ids)
    end_time = time.time()
    print(f'Personalized recommendation time: {end_time - start_time:.6f}s')
    return new_rec_matrix

def calculate_like_similarity(liked_vectors, target_vectors):
    liked_norms = np.linalg.norm(liked_vectors, axis=1)
    target_norms = np.linalg.norm(target_vectors, axis=1)
    dot_products = np.dot(target_vectors, liked_vectors.T)
    cosine_similarities = dot_products / np.outer(target_norms, liked_norms)
    average_similarities = np.mean(cosine_similarities, axis=1)
    return average_similarities

def rec_sys_personalized_twh(user_table: List[Dict[str, Any]], post_table: List[Dict[str, Any]], latest_post_count: int, trace_table: List[Dict[str, Any]], rec_matrix: List[List], max_rec_post_len: int, current_time: int, recall_only: bool=False, enable_like_score: bool=False, use_openai_embedding: bool=False) -> List[List]:
    global twhin_model, twhin_tokenizer
    if twhin_model is None or twhin_tokenizer is None:
        twhin_tokenizer, twhin_model = get_recsys_model(recsys_type='twhin-bert')
    global date_score, t_items, u_items, user_previous_post
    global user_previous_post_all, user_profiles
    if not u_items or len(u_items) != len(user_table):
        u_items = {user['user_id']: user['num_followers'] for user in user_table}
    if not user_previous_post_all or len(user_previous_post_all) != len(user_table):
        user_previous_post_all = {index: [] for index in range(len(user_table))}
        user_previous_post = {index: '' for index in range(len(user_table))}
    if not user_profiles or len(user_profiles) != len(user_table):
        for user in user_table:
            if user['bio'] is None:
                user_profiles.append('This user does not have profile')
            else:
                user_profiles.append(user['bio'])
    if len(t_items) < len(post_table):
        for post in post_table[-latest_post_count:]:
            t_items[post['post_id']] = post['content']
            user_previous_post_all[post['user_id']].append(post['content'])
            user_previous_post[post['user_id']] = post['content']
            date_score.append(np.log((271.8 - (current_time - int(post['created_at']))) / 100))
    date_score_np = np.array(date_score)
    if enable_like_score:
        like_post_ids_all = []
        for user in user_table:
            user_id = user['agent_id']
            like_post_ids = get_like_post_id(user_id, ActionType.LIKE_POST.value, trace_table)
            like_post_ids_all.append(like_post_ids)
    scores = date_score_np
    new_rec_matrix = []
    if len(post_table) <= max_rec_post_len:
        tids = [t['post_id'] for t in post_table]
        new_rec_matrix = [tids] * len(rec_matrix)
    else:
        for post_user_index in user_previous_post:
            try:
                update_profile = f' # Recent post:{user_previous_post[post_user_index]}'
                if user_previous_post[post_user_index] != '':
                    if '# Recent post:' not in user_profiles[post_user_index]:
                        user_profiles[post_user_index] += update_profile
                    elif update_profile not in user_profiles[post_user_index]:
                        user_profiles[post_user_index] = user_profiles[post_user_index].split('# Recent post:')[0] + update_profile
            except Exception:
                print('update previous post failed')
        filtered_posts_tuple = coarse_filtering(list(t_items.values()), 4000)
        corpus = user_profiles + filtered_posts_tuple[0]
        tweet_vector_start_t = time.time()
        if use_openai_embedding:
            all_post_vector_list = generate_post_vector_openai(corpus, batch_size=1000)
        else:
            all_post_vector_list = generate_post_vector(twhin_model, twhin_tokenizer, corpus, batch_size=1000)
        tweet_vector_end_t = time.time()
        rec_log.info(f'twhin model cost time: {tweet_vector_end_t - tweet_vector_start_t}')
        user_vector = all_post_vector_list[:len(user_profiles)]
        posts_vector = all_post_vector_list[len(user_profiles):]
        if enable_like_score:
            like_posts_vectors = []
            for user_idx, like_post_ids in enumerate(like_post_ids_all):
                if len(like_post_ids) != 1:
                    for like_post_id in like_post_ids:
                        try:
                            like_posts_vectors.append(posts_vector[like_post_id - 1])
                        except Exception:
                            like_posts_vectors.append(user_vector[user_idx])
                else:
                    like_posts_vectors += [user_vector[user_idx] for _ in range(5)]
            try:
                like_posts_vectors = torch.stack(like_posts_vectors).view(len(user_table), 5, posts_vector.shape[1])
            except Exception:
                import pdb
                pdb.set_trace()
        get_similar_start_t = time.time()
        cosine_similarities = cosine_similarity(user_vector, posts_vector)
        get_similar_end_t = time.time()
        rec_log.info(f'get cosine_similarity time: {get_similar_end_t - get_similar_start_t}')
        if enable_like_score:
            for user_index, profile in enumerate(user_profiles):
                user_like_posts_vector = like_posts_vectors[user_index]
                like_scores = calculate_like_similarity(user_like_posts_vector, posts_vector)
                try:
                    scores = scores + like_scores
                except Exception:
                    import pdb
                    pdb.set_trace()
        filter_posts_index = filtered_posts_tuple[1]
        cosine_similarities = cosine_similarities * scores[filter_posts_index]
        cosine_similarities = torch.tensor(cosine_similarities)
        value, indices = torch.topk(cosine_similarities, max_rec_post_len, dim=1, largest=True, sorted=True)
        filter_posts_index = torch.tensor(filter_posts_index)
        indices = filter_posts_index[indices]
        matrix_list = indices.cpu().numpy()
        post_list = list(t_items.keys())
        for rec_ids in matrix_list:
            rec_ids = [post_list[i] for i in rec_ids]
            new_rec_matrix.append(rec_ids)
    return new_rec_matrix

def normalize_similarity_adjustments(post_scores, base_similarity, like_similarity, dislike_similarity):
    """
    Normalize the adjustments to keep them in scale with overall similarities.

    Args:
        post_scores (list): List of post scores.
        base_similarity (float): Base similarity score.
        like_similarity (float): Similarity score for liked posts.
        dislike_similarity (float): Similarity score for disliked posts.

    Returns:
        float: Adjusted similarity score.
    """
    if len(post_scores) == 0:
        return base_similarity
    max_score = max(post_scores, key=lambda x: x[1])[1]
    min_score = min(post_scores, key=lambda x: x[1])[1]
    score_range = max_score - min_score
    adjustment = (like_similarity - dislike_similarity) * (score_range / 2)
    return base_similarity + adjustment

def rec_sys_personalized_with_trace(user_table: List[Dict[str, Any]], post_table: List[Dict[str, Any]], trace_table: List[Dict[str, Any]], rec_matrix: List[List], max_rec_post_len: int, swap_rate: float=0.1) -> List[List]:
    """
    This version:
    1. If the number of posts is less than or equal to the maximum
        recommended length, each user gets all post IDs

    2. Otherwise:
        - For each user, get a like-trace pool and dislike-trace pool from the
            trace table
        - For each user, calculate the similarity between the user's bio and
            the post text
        - Use the trace table to adjust the similarity score
        - Swap 10% of the recommended posts with the random posts

    Personalized recommendation system that uses user interaction traces.

    Args:
        user_table (List[Dict[str, Any]]): List of users.
        post_table (List[Dict[str, Any]]): List of posts.
        trace_table (List[Dict[str, Any]]): List of user interactions.
        rec_matrix (List[List]): Existing recommendation matrix.
        max_rec_post_len (int): Maximum number of recommended posts.
        swap_rate (float): Percentage of posts to swap for diversity.

    Returns:
        List[List]: Updated recommendation matrix.
    """
    start_time = time.time()
    new_rec_matrix = []
    post_ids = [post['post_id'] for post in post_table]
    if len(post_ids) <= max_rec_post_len:
        new_rec_matrix = [post_ids] * (len(rec_matrix) - 1)
    else:
        for idx in range(1, len(rec_matrix)):
            user_id = user_table[idx - 1]['user_id']
            user_bio = user_table[idx - 1]['bio']
            available_post_contents = [(post['post_id'], post['content']) for post in post_table if post['user_id'] != user_id]
            like_trace_contents = get_trace_contents(user_id, ActionType.LIKE_POST.value, post_table, trace_table)
            dislike_trace_contents = get_trace_contents(user_id, ActionType.UNLIKE_POST.value, post_table, trace_table)
            post_scores = []
            for post_id, post_content in available_post_contents:
                if model is not None:
                    user_embedding = model.encode(user_bio)
                    post_embedding = model.encode(post_content)
                    base_similarity = np.dot(user_embedding, post_embedding) / (np.linalg.norm(user_embedding) * np.linalg.norm(post_embedding))
                    post_scores.append((post_id, base_similarity))
                else:
                    post_scores.append((post_id, random.random()))
            new_post_scores = []
            for _post_id, _base_similarity in post_scores:
                _post_content = post_table[post_ids.index(_post_id)]['content']
                like_similarity = sum((np.dot(model.encode(_post_content), model.encode(like)) / (np.linalg.norm(model.encode(_post_content)) * np.linalg.norm(model.encode(like))) for like in like_trace_contents)) / len(like_trace_contents) if like_trace_contents else 0
                dislike_similarity = sum((np.dot(model.encode(_post_content), model.encode(dislike)) / (np.linalg.norm(model.encode(_post_content)) * np.linalg.norm(model.encode(dislike))) for dislike in dislike_trace_contents)) / len(dislike_trace_contents) if dislike_trace_contents else 0
                adjusted_similarity = normalize_similarity_adjustments(post_scores, _base_similarity, like_similarity, dislike_similarity)
                new_post_scores.append((_post_id, adjusted_similarity))
            new_post_scores.sort(key=lambda x: x[1], reverse=True)
            rec_post_ids = [post_id for post_id, _ in new_post_scores[:max_rec_post_len]]
            if swap_rate > 0:
                swap_free_ids = [post_id for post_id in post_ids if post_id not in rec_post_ids and post_id not in [trace['post_id'] for trace in trace_table if trace['user_id']]]
                rec_post_ids = swap_random_posts(rec_post_ids, swap_free_ids, swap_rate)
            new_rec_matrix.append(rec_post_ids)
    end_time = time.time()
    print(f'Personalized recommendation time: {end_time - start_time:.6f}s')
    return new_rec_matrix

