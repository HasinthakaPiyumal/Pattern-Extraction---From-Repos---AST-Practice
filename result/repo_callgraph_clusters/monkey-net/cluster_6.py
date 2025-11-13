# Cluster 6

class KPDataset(Dataset):
    """Dataset of detected keypoints"""

    def __init__(self, keypoints_array, num_frames):
        self.keypoints_array = keypoints_array
        self.transform = SelectRandomFrames(consequent=True, number_of_frames=num_frames)

    def __len__(self):
        return len(self.keypoints_array)

    def __getitem__(self, idx):
        keypoints = self.keypoints_array[idx]
        selected = self.transform(keypoints)
        selected = {k: np.concatenate([v[k][0] for v in selected], axis=0) for k in selected[0].keys()}
        return selected

def __init__(self, keypoints_array, num_frames):
    self.keypoints_array = keypoints_array
    self.transform = SelectRandomFrames(consequent=True, number_of_frames=num_frames)

class AllAugmentationTransform:

    def __init__(self, resize_param=None, rotation_param=None, flip_param=None, crop_param=None, jitter_param=None):
        self.transforms = []
        self.select = SelectRandomFrames()
        self.transforms.append(self.select)
        if flip_param is not None:
            self.transforms.append(RandomFlip(**flip_param))
        if rotation_param is not None:
            self.transforms.append(RandomRotation(**rotation_param))
        if resize_param is not None:
            self.transforms.append(RandomResize(**resize_param))
        if crop_param is not None:
            self.transforms.append(RandomCrop(**crop_param))
        if jitter_param is not None:
            self.transforms.append(ColorJitter(**jitter_param))
        self.transforms.append(SplitSourceDriving())

    def __call__(self, clip):
        for t in self.transforms:
            clip = t(clip)
        return clip

def __init__(self, resize_param=None, rotation_param=None, flip_param=None, crop_param=None, jitter_param=None):
    self.transforms = []
    self.select = SelectRandomFrames()
    self.transforms.append(self.select)
    if flip_param is not None:
        self.transforms.append(RandomFlip(**flip_param))
    if rotation_param is not None:
        self.transforms.append(RandomRotation(**rotation_param))
    if resize_param is not None:
        self.transforms.append(RandomResize(**resize_param))
    if crop_param is not None:
        self.transforms.append(RandomCrop(**crop_param))
    if jitter_param is not None:
        self.transforms.append(ColorJitter(**jitter_param))
    self.transforms.append(SplitSourceDriving())

