# Cluster 2

def env_monitor():
    while True:
        cur_time = time.time()
        pop_keys = []
        for k, v in envs.items():
            if cur_time - v['update_time'] >= ENV_TIMEOUT_SECOND:
                pop_keys.append(k)
        for k in pop_keys:
            envs.pop(k)
        time.sleep(1)

def env_monitor():
    while True:
        cur_time = time.time()
        pop_keys = []
        for k, v in envs.items():
            if cur_time - v['update_time'] >= ENV_TIMEOUT_SECOND:
                pop_keys.append(k)
        for k in pop_keys:
            envs.pop(k)
        time.sleep(1)

