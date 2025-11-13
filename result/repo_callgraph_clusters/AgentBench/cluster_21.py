# Cluster 21

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, default='configs/agents/api_agents.yaml')
    parser.add_argument('--agent', type=str, default='gpt-3.5-turbo-0613')
    return parser.parse_args()

