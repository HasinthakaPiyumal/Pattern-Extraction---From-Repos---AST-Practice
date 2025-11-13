# Cluster 11

def get_all_game_files(config, split='eval_out_of_distribution'):
    env = AlfredTWEnv(config, train_eval=split)
    game_files = env.game_files
    del env
    return game_files

