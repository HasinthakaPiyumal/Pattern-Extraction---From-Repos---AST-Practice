# Cluster 36

def render(mode):
    return env._render(mode, close=False)

def close():
    env._render('human', close=True)

