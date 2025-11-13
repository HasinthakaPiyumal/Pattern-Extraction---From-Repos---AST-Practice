# Cluster 89

def download_models(mode):
    if mode == 'superresolution':
        url_conf = 'https://heibox.uni-heidelberg.de/f/31a76b13ea27482981b4/?dl=1'
        url_ckpt = 'https://heibox.uni-heidelberg.de/f/578df07c8fc04ffbadf3/?dl=1'
        path_conf = 'logs/diffusion/superresolution_bsr/configs/project.yaml'
        path_ckpt = 'logs/diffusion/superresolution_bsr/checkpoints/last.ckpt'
        download_url(url_conf, path_conf)
        download_url(url_ckpt, path_ckpt)
        path_conf = path_conf + '/?dl=1'
        path_ckpt = path_ckpt + '/?dl=1'
        return (path_conf, path_ckpt)
    else:
        raise NotImplementedError

