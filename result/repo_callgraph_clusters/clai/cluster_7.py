# Cluster 7

def is_root_user():
    return os.geteuid() == 0

def is_root_user(args):
    return os.geteuid() == 0 or args.demo_mode

