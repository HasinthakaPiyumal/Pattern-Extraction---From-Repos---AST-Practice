# Cluster 7

def plot_trend(db_folders: List, db_types: List):
    stats = get_all_xdb_data(db_folders)
    stats_name = ['scale', 'depth', 'max breadth']
    fig, axes = plt.subplots(1, 3, figsize=(21, 7))
    for stat_index, stat_name in enumerate(stats_name):
        ax = axes[stat_index]
        colors = ['blue', 'red', 'orange', 'magenta', 'green', 'purple', 'orange']
        for db_index, db_type in enumerate(db_types):
            mean_values = np.mean(stats[db_index][stat_index], axis=0)
            std_dev = np.std(stats[db_index][stat_index], axis=0)
            confidence_interval = 1.96 * (std_dev / np.sqrt(stats[db_index][stat_index].shape[0]))
            ax.plot(mean_values, label=db_type, color=colors[db_index])
            ax.fill_between(range(stats[db_index][stat_index].shape[1]), mean_values - confidence_interval, mean_values + confidence_interval, color=colors[db_index], alpha=0.2, label=f'{db_type} 95% Confidence Interval')
        ax.set_xlabel('Time/minute', fontsize=22)
        ax.set_ylabel(stat_name, fontsize=22)
        ax.set_title(f'Trend of {stat_name} Over Time', fontsize=22)
        ax.tick_params(axis='x', labelsize=20)
        ax.tick_params(axis='y', labelsize=20)
        ax.grid(True)
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, loc='lower center', fontsize=20, ncol=2)
    plt.tight_layout(rect=[0, 0.15, 1, 1])
    file_name = ''
    for type in db_types:
        file_name += f'{type}--'
    file_name += 'all_stats.png'
    save_dir = Path(f'visualization/twitter_simulation/align_with_real_world/results/{file_name}')
    save_dir.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_dir)
    plt.show()

def get_subgraph_by_time(G: nx.Graph, time_threshold=10):
    filtered_nodes = []
    for node, attr in G.nodes(data=True):
        try:
            if attr['timestamp'] <= time_threshold:
                filtered_nodes.append(node)
        except Exception:
            pass
    subG = G.subgraph(filtered_nodes)
    return subG

def plot_graph_like_tree(G, root):
    pos = hierarchy_pos(G, root)
    plt.figure(figsize=(12, 8))
    nx.draw(G, pos, with_labels=True, node_size=3000, node_color='lightblue', font_size=10, font_weight='bold', arrows=True)
    plt.title('Retweet Tree')
    plt.show()

def plot_rmse(db_folders: List, db_types: List):
    stats = get_all_xdb_data(db_folders)
    stats_names = ['scale', 'depth', 'max breadth']
    fig, axes = plt.subplots(1, 3, figsize=(28, 7))
    markers = ['o', '^', 's', 'D', 'v', '*']
    for stat_index, stat_name in enumerate(stats_names):
        ax = axes[stat_index]
        colors = ['blue', 'red', 'orange', 'magenta', 'green', 'purple', 'orange']
        for type_index, db_type in enumerate(db_types):
            topic_rmse_losses = []
            topic_rmse_losses_per_min = []
            for topic_idx in range(len(stats[0][stat_index])):
                simu_arr = np.array(stats[type_index][stat_index][topic_idx])
                real_arr = np.array(stats[-1][stat_index][topic_idx])
                rmse_loss_per_min = np.abs(simu_arr - real_arr) / real_arr.max()
                rmse_loss = np.sqrt(np.mean((simu_arr - real_arr) ** 2)) / real_arr.max()
                topic_rmse_losses.append(rmse_loss)
                topic_rmse_losses_per_min.append(rmse_loss_per_min)
            topic_rmse_losses_per_min = np.array(topic_rmse_losses_per_min)
            rmse_losses = np.mean(np.array(topic_rmse_losses))
            print(f'{db_type}_{stat_name} rmse loss: {rmse_losses}')
            rmse_losses_per_min = np.mean(topic_rmse_losses_per_min, axis=0)
            ax.plot(rmse_losses_per_min, label=f'{db_type}', color=colors[type_index], marker=markers[type_index], markevery=3)
        ax.set_xlabel('Time/minute', fontsize=22)
        if stat_index == 0:
            ax.set_ylabel('Loss', fontsize=22)
        ax.grid(True)
        ax.set_title(f'Trend of {stat_name} Normalized RMSE Over Time', fontsize=22)
        ax.tick_params(axis='x', labelsize=20)
        ax.tick_params(axis='y', labelsize=20)
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, loc='lower center', bbox_to_anchor=(0.5, 0), fontsize=22, ncol=3)
    plt.tight_layout(rect=[0, 0.13, 1, 1])
    file_name = ''
    for type in db_types:
        if 'w/o' in type:
            type = type.replace('w/o', 'without')
        file_name += f'{type}--'
    file_name += 'all_stats.png'
    save_dir = Path(f'visualization/twitter_simulation/align_with_real_world/results/rmse/{file_name}')
    save_dir.parent.mkdir(parents=True, exist_ok=True)
    plt.xticks(fontsize=20)
    plt.yticks(fontsize=20)
    plt.savefig(save_dir)
    plt.show()

class prop_graph:

    def __init__(self, source_post_content, db_path='', viz=False):
        self.source_post_content = source_post_content
        self.db_path = db_path
        self.viz = viz
        self.post_exist = False

    def build_graph(self):
        conn = sqlite3.connect(self.db_path)
        query = 'SELECT * FROM post'
        df = pd.read_sql(query, conn)
        conn.close()
        all_reposts_and_time = []
        for i in range(len(df)):
            content = df.loc[i]['content']
            if self.post_exist is False and self.source_post_content[0:10] in content:
                self.post_exist = True
                self.root_id = df.loc[i]['user_id']
            if 'repost from' in content and self.source_post_content[0:10] in content:
                repost_history = content.split('. original_post: ')[:-1]
                repost_time = df.loc[i]['created_at']
                all_reposts_and_time.append((repost_history, repost_time))
        data = all_reposts_and_time
        start_time = 0
        self.G = nx.DiGraph()
        first_flag = 1
        for reposts, timestamp in data:
            time_diff = timestamp - start_time
            for repost in reposts:
                repost_info = repost.split(' repost from ')
                user = repost_info[0]
                original_user = repost_info[1]
                if first_flag:
                    self.root_id = original_user
                    first_flag = 0
                    if original_user not in self.G:
                        self.G.add_node(original_user, timestamp=0)
                if user not in self.G:
                    self.G.add_node(user, timestamp=time_diff)
                self.G.add_edge(original_user, user)
        self.start_timestamp = 0
        timestamps = nx.get_node_attributes(self.G, 'timestamp')
        try:
            self.end_timestamp = max(timestamps.values()) + 3
        except Exception as e:
            print(self.source_post_content)
            print(f'ERROR: {e}, may be caused by empty repost path')
            print(f'the simulation db is empty: {not self.post_exist}')
            print('Length of repost path:', len(all_reposts_and_time))
        self.total_depth = get_dpeth(self.G, source=self.root_id)
        self.total_scale = self.G.number_of_nodes()
        self.total_max_breadth = 0
        last_breadth_list = [1]
        for depth in range(self.total_depth):
            breadth = len(list(nx.bfs_tree(self.G, source=self.root_id, depth_limit=depth + 1).nodes())) - sum(last_breadth_list)
            last_breadth_list.append(breadth)
            if breadth > self.total_max_breadth:
                self.total_max_breadth = breadth
        undirect_G = self.G.to_undirected()
        self.total_structural_virality = nx.average_shortest_path_length(undirect_G)

    def viz_graph(self, time_threshold=10000):
        subG = get_subgraph_by_time(self.G, time_threshold)
        plot_graph_like_tree(subG, self.root_id)

    def plot_depth_time(self, separate_ratio: float=1):
        """
        Entire propagation process
        Detailed depiction of the data for the process before separate_ratio
        Rough depiction of the data afterwards
        Default to 1
        Use this parameter when the propagation time is very long, can be set
        to 0.01
        """
        depth_list = []
        self.d_t_list = list(range(int(self.start_timestamp), int(self.end_timestamp), 1))
        depth = 0
        for t in self.d_t_list:
            if depth < self.total_depth:
                try:
                    sub_g = get_subgraph_by_time(self.G, time_threshold=t)
                    depth = get_dpeth(sub_g, source=self.root_id)
                except Exception:
                    import pdb
                    pdb.set_trace()
            depth_list.append(depth)
        self.depth_list = depth_list
        if self.viz:
            _, ax = plt.subplots()
            ax.plot(self.d_t_list, self.depth_list)
            plt.title('Propagation depth-time')
            plt.xlabel('Time/minute')
            plt.ylabel('Depth')
            plt.show()
        else:
            return (self.d_t_list, self.depth_list)

    def plot_scale_time(self, separate_ratio: float=1.0):
        """
        Detailed depiction of the data between the start and separate_ratio*T
        of the entire propagation process
        Rough depiction of the data afterwards
        Default to 1
        Use this parameter when the propagation time is very long, can be set
        to 0.1
        """
        self.node_nums = []
        separate_point = int(int(self.start_timestamp) + separate_ratio * (int(self.end_timestamp) - int(self.start_timestamp)))
        self.s_t_list = list(range(int(self.start_timestamp), separate_point, 1))
        for t in self.s_t_list:
            try:
                sub_g = get_subgraph_by_time(self.G, time_threshold=t)
                node_num = sub_g.number_of_nodes()
            except Exception:
                import pdb
                pdb.set_trace()
            self.node_nums.append(node_num)
        if self.viz:
            _, ax = plt.subplots()
            ax.plot(self.s_t_list, self.node_nums)
            plt.title('Propagation scale-time')
            plt.xlabel('Time/minute')
            plt.ylabel('Scale')
            plt.show()
        else:
            return (self.s_t_list, self.node_nums)

    def plot_max_breadth_time(self, interval=1):
        self.max_breadth_list = []
        self.b_t_list = list(range(int(self.start_timestamp), int(self.end_timestamp), interval))
        for t in self.b_t_list:
            try:
                sub_g = get_subgraph_by_time(self.G, time_threshold=t)
            except Exception:
                import pdb
                pdb.set_trace()
            max_depth = self.depth_list[t - self.b_t_list[0]]
            max_breadth = 0
            last_breadth_list = [1]
            for depth in range(max_depth):
                breadth = len(list(nx.bfs_tree(sub_g, source=self.root_id, depth_limit=depth + 1).nodes())) - sum(last_breadth_list)
                last_breadth_list.append(breadth)
                if breadth > max_breadth:
                    max_breadth = breadth
            self.max_breadth_list.append(max_breadth)
        if self.viz:
            _, ax = plt.subplots()
            ax.plot(self.b_t_list, self.max_breadth_list)
            plt.title('Propagation max breadth-time')
            plt.xlabel('Time/minute')
            plt.ylabel('Max breadth')
            plt.show()
        else:
            return (self.b_t_list, self.max_breadth_list)

    def plot_structural_virality_time(self, interval=1):
        self.sv_list = []
        self.sv_t_list = list(range(int(self.start_timestamp), int(self.end_timestamp), interval))
        for t in self.sv_t_list:
            try:
                sub_g = get_subgraph_by_time(self.G, time_threshold=t)
            except Exception:
                import pdb
                pdb.set_trace()
            sub_g = sub_g.to_undirected()
            sv = nx.average_shortest_path_length(sub_g)
            self.sv_list.append(sv)
        if self.viz:
            _, ax = plt.subplots()
            ax.plot(self.sv_t_list, self.sv_list)
            plt.title('Propagation structural virality-time')
            plt.xlabel('Time/minute')
            plt.ylabel('Structural virality')
            plt.show()
        else:
            return (self.sv_t_list, self.sv_list)

def build_graph(self):
    conn = sqlite3.connect(self.db_path)
    query = 'SELECT * FROM post'
    df = pd.read_sql(query, conn)
    conn.close()
    all_reposts_and_time = []
    for i in range(len(df)):
        content = df.loc[i]['content']
        if self.post_exist is False and self.source_post_content[0:10] in content:
            self.post_exist = True
            self.root_id = df.loc[i]['user_id']
        if 'repost from' in content and self.source_post_content[0:10] in content:
            repost_history = content.split('. original_post: ')[:-1]
            repost_time = df.loc[i]['created_at']
            all_reposts_and_time.append((repost_history, repost_time))
    data = all_reposts_and_time
    start_time = 0
    self.G = nx.DiGraph()
    first_flag = 1
    for reposts, timestamp in data:
        time_diff = timestamp - start_time
        for repost in reposts:
            repost_info = repost.split(' repost from ')
            user = repost_info[0]
            original_user = repost_info[1]
            if first_flag:
                self.root_id = original_user
                first_flag = 0
                if original_user not in self.G:
                    self.G.add_node(original_user, timestamp=0)
            if user not in self.G:
                self.G.add_node(user, timestamp=time_diff)
            self.G.add_edge(original_user, user)
    self.start_timestamp = 0
    timestamps = nx.get_node_attributes(self.G, 'timestamp')
    try:
        self.end_timestamp = max(timestamps.values()) + 3
    except Exception as e:
        print(self.source_post_content)
        print(f'ERROR: {e}, may be caused by empty repost path')
        print(f'the simulation db is empty: {not self.post_exist}')
        print('Length of repost path:', len(all_reposts_and_time))
    self.total_depth = get_dpeth(self.G, source=self.root_id)
    self.total_scale = self.G.number_of_nodes()
    self.total_max_breadth = 0
    last_breadth_list = [1]
    for depth in range(self.total_depth):
        breadth = len(list(nx.bfs_tree(self.G, source=self.root_id, depth_limit=depth + 1).nodes())) - sum(last_breadth_list)
        last_breadth_list.append(breadth)
        if breadth > self.total_max_breadth:
            self.total_max_breadth = breadth
    undirect_G = self.G.to_undirected()
    self.total_structural_virality = nx.average_shortest_path_length(undirect_G)

def viz_graph(self, time_threshold=10000):
    subG = get_subgraph_by_time(self.G, time_threshold)
    plot_graph_like_tree(subG, self.root_id)

def plot_depth_time(self, separate_ratio: float=1):
    """
        Entire propagation process
        Detailed depiction of the data for the process before separate_ratio
        Rough depiction of the data afterwards
        Default to 1
        Use this parameter when the propagation time is very long, can be set
        to 0.01
        """
    depth_list = []
    self.d_t_list = list(range(int(self.start_timestamp), int(self.end_timestamp), 1))
    depth = 0
    for t in self.d_t_list:
        if depth < self.total_depth:
            try:
                sub_g = get_subgraph_by_time(self.G, time_threshold=t)
                depth = get_dpeth(sub_g, source=self.root_id)
            except Exception:
                import pdb
                pdb.set_trace()
        depth_list.append(depth)
    self.depth_list = depth_list
    if self.viz:
        _, ax = plt.subplots()
        ax.plot(self.d_t_list, self.depth_list)
        plt.title('Propagation depth-time')
        plt.xlabel('Time/minute')
        plt.ylabel('Depth')
        plt.show()
    else:
        return (self.d_t_list, self.depth_list)

def plot_scale_time(self, separate_ratio: float=1.0):
    """
        Detailed depiction of the data between the start and separate_ratio*T
        of the entire propagation process
        Rough depiction of the data afterwards
        Default to 1
        Use this parameter when the propagation time is very long, can be set
        to 0.1
        """
    self.node_nums = []
    separate_point = int(int(self.start_timestamp) + separate_ratio * (int(self.end_timestamp) - int(self.start_timestamp)))
    self.s_t_list = list(range(int(self.start_timestamp), separate_point, 1))
    for t in self.s_t_list:
        try:
            sub_g = get_subgraph_by_time(self.G, time_threshold=t)
            node_num = sub_g.number_of_nodes()
        except Exception:
            import pdb
            pdb.set_trace()
        self.node_nums.append(node_num)
    if self.viz:
        _, ax = plt.subplots()
        ax.plot(self.s_t_list, self.node_nums)
        plt.title('Propagation scale-time')
        plt.xlabel('Time/minute')
        plt.ylabel('Scale')
        plt.show()
    else:
        return (self.s_t_list, self.node_nums)

def plot_max_breadth_time(self, interval=1):
    self.max_breadth_list = []
    self.b_t_list = list(range(int(self.start_timestamp), int(self.end_timestamp), interval))
    for t in self.b_t_list:
        try:
            sub_g = get_subgraph_by_time(self.G, time_threshold=t)
        except Exception:
            import pdb
            pdb.set_trace()
        max_depth = self.depth_list[t - self.b_t_list[0]]
        max_breadth = 0
        last_breadth_list = [1]
        for depth in range(max_depth):
            breadth = len(list(nx.bfs_tree(sub_g, source=self.root_id, depth_limit=depth + 1).nodes())) - sum(last_breadth_list)
            last_breadth_list.append(breadth)
            if breadth > max_breadth:
                max_breadth = breadth
        self.max_breadth_list.append(max_breadth)
    if self.viz:
        _, ax = plt.subplots()
        ax.plot(self.b_t_list, self.max_breadth_list)
        plt.title('Propagation max breadth-time')
        plt.xlabel('Time/minute')
        plt.ylabel('Max breadth')
        plt.show()
    else:
        return (self.b_t_list, self.max_breadth_list)

def plot_structural_virality_time(self, interval=1):
    self.sv_list = []
    self.sv_t_list = list(range(int(self.start_timestamp), int(self.end_timestamp), interval))
    for t in self.sv_t_list:
        try:
            sub_g = get_subgraph_by_time(self.G, time_threshold=t)
        except Exception:
            import pdb
            pdb.set_trace()
        sub_g = sub_g.to_undirected()
        sv = nx.average_shortest_path_length(sub_g)
        self.sv_list.append(sv)
    if self.viz:
        _, ax = plt.subplots()
        ax.plot(self.sv_t_list, self.sv_list)
        plt.title('Propagation structural virality-time')
        plt.xlabel('Time/minute')
        plt.ylabel('Structural virality')
        plt.show()
    else:
        return (self.sv_t_list, self.sv_list)

def visualization(up_result, down_result, control_result, exp_name, folder_path):
    up_mean, up_ci_low, up_ci_high = mean_confidence_interval(up_result)
    down_mean, down_ci_low, down_ci_high = mean_confidence_interval(down_result)
    control_mean, control_ci_low, control_ci_high = mean_confidence_interval(control_result)
    labels = ['Down', 'Control', 'Up']
    means = [down_mean, control_mean, up_mean]
    conf_intervals = [(down_ci_low, down_ci_high), (control_ci_low, control_ci_high), (up_ci_low, up_ci_high)]
    x_pos = range(len(labels))
    fig, ax = plt.subplots()
    ax.bar(labels, means, color='skyblue', yerr=np.transpose([[mean - ci_low, ci_high - mean] for mean, (ci_low, ci_high) in zip(means, conf_intervals)]), capsize=10)
    for i, mean in enumerate(means):
        ax.plot(x_pos[i], mean, 'ro')
    ax.set_ylabel('Scores')
    ax.set_title('Mean Scores with 95% Confidence Intervals')
    plt.savefig(f'{folder_path}/score_{exp_name}.png')
    plt.show()

def format_docs(docs):
    formatted_docs = ''
    for i, doc in enumerate(docs, start=1):
        formatted_docs += f'Example {i}:\n{doc.page_content}\n\n'
    return formatted_docs.strip().replace('character', 'persona')

def weighted_random_age(ages, probabilities):
    ranges = []
    for age_range in ages:
        if '+' in age_range:
            start = int(age_range[:-1])
            end = start + 20
        else:
            start, end = map(int, age_range.split('-'))
        ranges.append((start, end))
    total_weight = sum(probabilities)
    rnd = random.uniform(0, total_weight)
    cumulative_weight = 0
    for i, weight in enumerate(probabilities):
        cumulative_weight += weight
        if rnd < cumulative_weight:
            start, end = ranges[i]
            return random.randint(start, end)
    return None

def get_recommendations(user_index, cosine_similarities, items, score, top_n=100):
    similarities = np.array(cosine_similarities[user_index])
    similarities = similarities * score
    top_item_indices = similarities.argsort()[::-1][:top_n]
    recommended_items = [(list(items.keys())[i], similarities[i]) for i in top_item_indices]
    return recommended_items

def insert_matrix_into_rec_table(cursor: sqlite3.Cursor, matrix: List[List[int]]) -> None:
    for user_id, post_ids in enumerate(matrix, start=1):
        for post_id in post_ids:
            cursor.execute('INSERT INTO rec (user_id, post_id) VALUES (?, ?)', (user_id, post_id))

