# Cluster 1

def clearscr() -> None:
    try:
        osp = platform.system()
        match osp:
            case 'Darwin':
                os.system('clear')
            case 'Linux':
                os.system('clear')
            case 'Windows':
                os.system('cls')
    except Exception:
        pass

