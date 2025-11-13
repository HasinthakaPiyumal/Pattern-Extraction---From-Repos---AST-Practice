# Cluster 15

def vis_parser():
    parser = argparse.ArgumentParser(description='data visualization')
    parser.add_argument('--color_mode', type=str, default='intensity', help='lidar color rendering mode, e.g. intensity,z-value or constant.')
    opt = parser.parse_args()
    return opt

def test_parser():
    parser = argparse.ArgumentParser(description='synthetic data generation')
    parser.add_argument('--model_dir', type=str, required=True, help='Continued training path')
    parser.add_argument('--fusion_method', type=str, default='late', help='late, early or intermediate')
    opt = parser.parse_args()
    return opt

def train_parser():
    parser = argparse.ArgumentParser(description='synthetic data generation')
    parser.add_argument('--hypes_yaml', type=str, required=True, help='data generation yaml file needed ')
    parser.add_argument('--model_dir', default='', help='Continued training path')
    parser.add_argument('--half', action='store_true', help='whether train with half precision')
    opt = parser.parse_args()
    return opt

def test_parser():
    parser = argparse.ArgumentParser(description='synthetic data generation')
    parser.add_argument('--model_dir', type=str, required=True, help='Continued training path')
    parser.add_argument('--fusion_method', required=True, type=str, default='late', help='late, early or intermediate')
    parser.add_argument('--show_vis', action='store_true', help='whether to show image visualization result')
    parser.add_argument('--show_sequence', action='store_true', help='whether to show video visualization result.it can note be set true with show_vis together ')
    parser.add_argument('--save_vis', action='store_true', help='whether to save visualization result')
    parser.add_argument('--save_npy', action='store_true', help='whether to save prediction and gt resultin npy file')
    opt = parser.parse_args()
    return opt

