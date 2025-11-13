# Cluster 17

def parse_args():
    parser = ArgumentParser(description='Interactive rendering')
    parser.add_argument('--scenario', type=str, default='waterfall', help='Scenario to load. Can be the name of a file in `vmas.scenarios` folder or a :class:`~vmas.simulator.scenario.BaseScenario` class')
    parser.add_argument('--control_two_agents', action=BooleanOptionalAction, default=True, help='Whether to control two agents or just one')
    parser.add_argument('--display_info', action=BooleanOptionalAction, default=True, help='Whether to display on the screen the following info from the first controlled agent: name, reward, total reward, done, and observation')
    parser.add_argument('--save_render', action='store_true', help='Whether to save a video of the render up to the first reset')
    return parser.parse_args()

