# Cluster 27

def SSIM(img1, img2):
    return metrics.structural_similarity(img1, img2, data_range=1, channel_axis=-1)

