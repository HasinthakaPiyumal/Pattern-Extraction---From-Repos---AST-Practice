# Cluster 6

def generate_attrs(corpus_by_cat, k, save_name):
    attrs = dict()
    for n in range(1, 3):
        ngram_range = (n, n)
        top_attrs_by_cat = generate_ngram_attrs(corpus_by_cat, ngram_range, k, attrs)
        if save_name is not None:
            save_path = Path(ATTR_DIR) / f'{save_name}_{n}-gram.yaml'
            with open(save_path, 'w') as f:
                yaml.dump(top_attrs_by_cat, f, default_flow_style=False)
            print(f'Saved: {save_path}')
    save_path = Path(ATTR_DIR) / f'{save_name}_attrs_unfiltered.json'
    with open(save_path, 'w') as f:
        json.dump(attrs, f)
    print(f'Saved: {save_path}')

def logkv(key, val):
    """
    Log a value of some diagnostic
    Call this once for each diagnostic quantity, each iteration
    If called many times, last value will be used.
    """
    Logger.CURRENT.logkv(key, val)

def logkvs(d):
    """
    Log a dictionary of key-value pairs
    """
    for k, v in d.items():
        logkv(k, v)

def dumpkvs():
    """
    Write all of the diagnostics from the current iteration

    level: int. (see logger.py docs) If the global logger level is higher than
                the level argument here, don't print to stdout.
    """
    Logger.CURRENT.dumpkvs()

def set_level(level):
    """
    Set logging threshold on current logger.
    """
    Logger.CURRENT.set_level(level)

def _demo():
    info('hi')
    debug("shouldn't appear")
    set_level(DEBUG)
    debug('should appear')
    dir = '/tmp/testlogging'
    if os.path.exists(dir):
        shutil.rmtree(dir)
    configure(dir=dir)
    logkv('a', 3)
    logkv('b', 2.5)
    dumpkvs()
    logkv('b', -2.5)
    logkv('a', 5.5)
    dumpkvs()
    info('^^^ should see a = 5.5')
    logkv_mean('b', -22.5)
    logkv_mean('b', -44.4)
    logkv('a', 5.5)
    dumpkvs()
    info('^^^ should see b = 33.3')
    logkv('b', -2.5)
    dumpkvs()
    logkv('a', 'longasslongasslongasslongasslongasslongassvalue')
    dumpkvs()

def test_setup_logger():
    LOG_DIR = 'user_session_logs_test/'
    user_log_dir = Path(LOG_DIR)
    user_log_dir.mkdir(parents=True, exist_ok=True)
    session_id = 'ABC'
    logger = setup_logger(session_id, user_log_dir)
    log_file = Path(LOG_DIR + '/' + session_id + '.jsonl')
    assert Path(log_file).is_file()
    assert logger.level == logging.INFO
    content = 'Hello there'
    logger.info(content)
    assert log_file.read_text().strip('\n') == content
    shutil.rmtree(LOG_DIR)

