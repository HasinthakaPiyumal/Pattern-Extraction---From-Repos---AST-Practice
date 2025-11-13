# Cluster 0

def check_port_open(host, port):
    while True:
        url = f'http://{host}:{port}/health'
        try:
            response = requests.get(url)
            if response.status_code == 200:
                break
            else:
                time.sleep(0.3)
        except Exception:
            time.sleep(0.3)

def get_xdb_data(db_paths, topic_name):
    source_tweet_content = all_topic_df[all_topic_df['topic_name'] == topic_name]['source_tweet'].item()
    stats = []
    real_stat_list = []
    for index, stat in enumerate(['scale', 'depth', 'max_breadth']):
        real_data_root = Path(f'data/twitter_dataset/real_world_prop_data/real_data_{stat}')
        real_data_root.mkdir(parents=True, exist_ok=True)
        pkl_path = os.path.join(real_data_root, f'{topic_name}.pkl')
        Y_real = load_list(pkl_path)
        Y_real += [Y_real[-1]] * (300 - len(Y_real))
        real_stat_list.append(Y_real)
    for db_path in db_paths:
        pg = prop_graph(source_tweet_content, db_path, viz=False)
        try:
            pg.build_graph()
            stats.append(get_stat_list(pg))
        except Exception as e:
            zero_stats = [[0] * 300] * 3
            stats.append(zero_stats)
            print(e)
    stats.append(real_stat_list)
    return stats

def get_xdb_data(db_paths, topic_name):
    source_tweet_content = all_topic_df[all_topic_df['topic_name'] == topic_name]['source_tweet'].item()
    stats = []
    for db_path in db_paths:
        pg = prop_graph(source_tweet_content, db_path, viz=False)
        try:
            pg.build_graph()
            stats.append(get_stat_list(pg))
        except Exception:
            zero_stats = [[0] * 300] * 3
            stats.append(zero_stats)
    real_stat_list = []
    for index, stat in enumerate(['scale', 'depth', 'max_breadth']):
        real_data_root = Path(f'data/twitter_dataset/real_world_prop_data/real_data_{stat}')
        real_data_root.mkdir(parents=True, exist_ok=True)
        pkl_path = os.path.join(real_data_root, f'{topic_name}.pkl')
        Y_real = load_list(pkl_path)
        Y_real += [Y_real[-1]] * (300 - len(Y_real))
        real_stat_list.append(Y_real)
    stats.append(real_stat_list)
    return stats

def update_license_in_directory(directory_path: str, license_template_path: str, start_line_start_with: str, end_line_start_with: str) -> None:
    if not os.path.isdir(directory_path):
        raise NotADirectoryError(f'{directory_path} is not a directory')
    if not os.path.isfile(license_template_path):
        raise FileNotFoundError(f'{license_template_path} not found')
    file_count = 0
    for py_files in Path(directory_path).rglob('*.py'):
        if py_files.name.startswith('.'):
            continue
        if any((part.startswith('.') for part in py_files.parts)):
            continue
        if update_license_in_file(py_files, license_template_path, start_line_start_with, end_line_start_with):
            file_count += 1
    print(f'License updated in {file_count} files')

def get_db_path() -> str:
    env_db_path = os.environ.get('OASIS_DB_PATH')
    if env_db_path:
        return env_db_path
    curr_file_path = osp.abspath(__file__)
    parent_dir = osp.dirname(osp.dirname(curr_file_path))
    db_dir = osp.join(parent_dir, DB_DIR)
    os.makedirs(db_dir, exist_ok=True)
    db_path = osp.join(db_dir, DB_NAME)
    return db_path

def get_schema_dir_path() -> str:
    curr_file_path = osp.abspath(__file__)
    parent_dir = osp.dirname(osp.dirname(curr_file_path))
    schema_dir = osp.join(parent_dir, SCHEMA_DIR)
    return schema_dir

