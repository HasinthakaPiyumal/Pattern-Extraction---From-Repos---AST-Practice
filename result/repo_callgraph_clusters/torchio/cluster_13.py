# Cluster 13

def rotate(image: np.ndarray, *, radiological: bool=True, n: int=-1) -> np.ndarray:
    image = np.rot90(image, n, axes=(0, 1))
    if radiological:
        image = np.fliplr(image)
    return image

