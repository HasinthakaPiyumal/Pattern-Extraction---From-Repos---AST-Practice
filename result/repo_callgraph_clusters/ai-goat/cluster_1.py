# Cluster 1

def handle_args(inputs):
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--install', help='Install', action='store_true')
    parser.add_argument('-r', '--run', help='Start CTFd or a Challenge.', choices=['ctfd', '1', '2', '3'])
    args = parser.parse_args(inputs)
    return args

