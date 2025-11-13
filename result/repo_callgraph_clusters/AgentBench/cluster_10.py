# Cluster 10

class SingleAlfredTWEnv(AlfredTWEnv):

    def __init__(self, config, game_files, train_eval='eval_out_of_distribution'):
        self.config = config
        self.train_eval = train_eval
        self.goal_desc_human_anns_prob = self.config['env']['goal_desc_human_anns_prob']
        self.get_game_logic()
        self.random_seed = 42
        self.game_files = [game_files]
        self.num_games = 1

def __init__(self, config, game_files, train_eval='eval_out_of_distribution'):
    self.config = config
    self.train_eval = train_eval
    self.goal_desc_human_anns_prob = self.config['env']['goal_desc_human_anns_prob']
    self.get_game_logic()
    self.random_seed = 42
    self.game_files = [game_files]
    self.num_games = 1

