# Cluster 5

class SplitSourceDriving(object):

    def __call__(self, video):
        source = np.array(video[:1], dtype='float32')
        video = np.array(video[1:], dtype='float32')
        return {'video': video.transpose((3, 0, 1, 2)), 'source': source.transpose((3, 0, 1, 2))}

def __call__(self, video):
    source = np.array(video[:1], dtype='float32')
    video = np.array(video[1:], dtype='float32')
    return {'video': video.transpose((3, 0, 1, 2)), 'source': source.transpose((3, 0, 1, 2))}

class VideoToTensor(object):
    """Convert video array to Tensor."""

    def __call__(self, driving):
        driving = np.array(driving, dtype='float32')
        return {'video': driving.transpose((3, 0, 1, 2))}

def __call__(self, driving):
    driving = np.array(driving, dtype='float32')
    return {'video': driving.transpose((3, 0, 1, 2))}

def make_symetric_matrix(torch_matrix):
    a = torch_matrix.cpu().numpy()
    c = (a + np.transpose(a, (0, 1, 2, 4, 3))) / 2
    d, u = np.linalg.eig(c)
    d[d <= 0] = 1e-06
    d_matrix = np.zeros_like(a)
    d_matrix[..., 0, 0] = d[..., 0]
    d_matrix[..., 1, 1] = d[..., 1]
    res = np.matmul(np.matmul(u, d_matrix), np.transpose(u, (0, 1, 2, 4, 3)))
    res = torch.from_numpy(res).type(torch_matrix.type())
    return res

class Visualizer:

    def __init__(self, kp_size=2, draw_border=False, colormap='gist_rainbow'):
        self.kp_size = kp_size
        self.draw_border = draw_border
        self.colormap = plt.get_cmap(colormap)

    def draw_video_with_kp(self, video, kp_array):
        video_array = np.copy(video)
        spatial_size = np.array(video_array.shape[2:0:-1])[np.newaxis, np.newaxis]
        kp_array = spatial_size * (kp_array + 1) / 2
        num_kp = kp_array.shape[1]
        for i in range(len(video_array)):
            for kp_ind, kp in enumerate(kp_array[i]):
                rr, cc = circle(kp[1], kp[0], self.kp_size, shape=video_array.shape[1:3])
                video_array[i][rr, cc] = np.array(self.colormap(kp_ind / num_kp))[:3]
        return video_array

    def create_video_column_with_kp(self, video, kp):
        video_array = np.array([self.draw_video_with_kp(v, k) for v, k in zip(video, kp)])
        return self.create_video_column(video_array)

    def create_video_column(self, videos):
        if self.draw_border:
            videos = np.copy(videos)
            videos[:, :, [0, -1]] = (1, 1, 1)
            videos[:, :, :, [0, -1]] = (1, 1, 1)
        return np.concatenate(list(videos), axis=1)

    def create_image_grid(self, *args):
        out = []
        for arg in args:
            if type(arg) == tuple:
                out.append(self.create_video_column_with_kp(arg[0], arg[1]))
            else:
                out.append(self.create_video_column(arg))
        return np.concatenate(out, axis=2)

    def visualize_transfer(self, driving_video, source_image, out):
        out_video_batch = out['video_prediction'].data.cpu().numpy()
        appearance_deformed_batch = out['video_deformed'].data.cpu().numpy()
        motion_video_batch = driving_video.data.cpu().numpy()
        appearance_video_batch = source_image[:, :, 0:1].data.cpu().repeat(1, 1, out_video_batch.shape[2], 1, 1).numpy()
        video_first_frame = driving_video[:, :, 0:1].data.cpu().repeat(1, 1, out_video_batch.shape[2], 1, 1).numpy()
        kp_video = out['kp_driving']['mean'].data.cpu().numpy()
        kp_appearance = out['kp_source']['mean'].data.cpu().repeat(1, out_video_batch.shape[2], 1, 1).numpy()
        kp_norm = out['kp_norm']['mean'].data.cpu().numpy()
        kp_video_first = out['kp_driving']['mean'][:, :1].data.cpu().repeat(1, out_video_batch.shape[2], 1, 1).numpy()
        video_first_frame = np.transpose(video_first_frame, [0, 2, 3, 4, 1])
        out_video_batch = np.transpose(out_video_batch, [0, 2, 3, 4, 1])
        motion_video_batch = np.transpose(motion_video_batch, [0, 2, 3, 4, 1])
        appearance_video_batch = np.transpose(appearance_video_batch, [0, 2, 3, 4, 1])
        appearance_deformed_batch = np.transpose(appearance_deformed_batch, [0, 2, 3, 4, 1])
        image = self.create_image_grid((appearance_video_batch, kp_appearance), (video_first_frame, kp_video_first), (motion_video_batch, kp_video), (out_video_batch, kp_norm), out_video_batch, appearance_deformed_batch)
        image = (255 * image).astype(np.uint8)
        return image

    def visualize_reconstruction(self, inp, out):
        out_video_batch = out['video_prediction'].data.cpu().numpy()
        if 'driving' in inp:
            gt_video_batch = inp['driving'].data.cpu().numpy()
        else:
            gt_video_batch = inp['video'].data.cpu().numpy()
        appearance_deformed_batch = out['video_deformed'].data.cpu().numpy()
        appearance_video_batch = inp['source'].data.cpu().repeat(1, 1, out_video_batch.shape[2], 1, 1).numpy()
        kp_video = out['kp_driving']['mean'].data.cpu().numpy()
        kp_appearance = out['kp_source']['mean'].data.cpu().repeat(1, out_video_batch.shape[2], 1, 1).numpy()
        out_video_batch = np.transpose(out_video_batch, [0, 2, 3, 4, 1])
        gt_video_batch = np.transpose(gt_video_batch, [0, 2, 3, 4, 1])
        appearance_video_batch = np.transpose(appearance_video_batch, [0, 2, 3, 4, 1])
        appearance_deformed_batch = np.transpose(appearance_deformed_batch, [0, 2, 3, 4, 1])
        image = self.create_image_grid((appearance_video_batch, kp_appearance), (gt_video_batch, kp_video), out_video_batch, appearance_deformed_batch, gt_video_batch)
        image = (255 * image).astype(np.uint8)
        return image

def visualize_transfer(self, driving_video, source_image, out):
    out_video_batch = out['video_prediction'].data.cpu().numpy()
    appearance_deformed_batch = out['video_deformed'].data.cpu().numpy()
    motion_video_batch = driving_video.data.cpu().numpy()
    appearance_video_batch = source_image[:, :, 0:1].data.cpu().repeat(1, 1, out_video_batch.shape[2], 1, 1).numpy()
    video_first_frame = driving_video[:, :, 0:1].data.cpu().repeat(1, 1, out_video_batch.shape[2], 1, 1).numpy()
    kp_video = out['kp_driving']['mean'].data.cpu().numpy()
    kp_appearance = out['kp_source']['mean'].data.cpu().repeat(1, out_video_batch.shape[2], 1, 1).numpy()
    kp_norm = out['kp_norm']['mean'].data.cpu().numpy()
    kp_video_first = out['kp_driving']['mean'][:, :1].data.cpu().repeat(1, out_video_batch.shape[2], 1, 1).numpy()
    video_first_frame = np.transpose(video_first_frame, [0, 2, 3, 4, 1])
    out_video_batch = np.transpose(out_video_batch, [0, 2, 3, 4, 1])
    motion_video_batch = np.transpose(motion_video_batch, [0, 2, 3, 4, 1])
    appearance_video_batch = np.transpose(appearance_video_batch, [0, 2, 3, 4, 1])
    appearance_deformed_batch = np.transpose(appearance_deformed_batch, [0, 2, 3, 4, 1])
    image = self.create_image_grid((appearance_video_batch, kp_appearance), (video_first_frame, kp_video_first), (motion_video_batch, kp_video), (out_video_batch, kp_norm), out_video_batch, appearance_deformed_batch)
    image = (255 * image).astype(np.uint8)
    return image

def visualize_reconstruction(self, inp, out):
    out_video_batch = out['video_prediction'].data.cpu().numpy()
    if 'driving' in inp:
        gt_video_batch = inp['driving'].data.cpu().numpy()
    else:
        gt_video_batch = inp['video'].data.cpu().numpy()
    appearance_deformed_batch = out['video_deformed'].data.cpu().numpy()
    appearance_video_batch = inp['source'].data.cpu().repeat(1, 1, out_video_batch.shape[2], 1, 1).numpy()
    kp_video = out['kp_driving']['mean'].data.cpu().numpy()
    kp_appearance = out['kp_source']['mean'].data.cpu().repeat(1, out_video_batch.shape[2], 1, 1).numpy()
    out_video_batch = np.transpose(out_video_batch, [0, 2, 3, 4, 1])
    gt_video_batch = np.transpose(gt_video_batch, [0, 2, 3, 4, 1])
    appearance_video_batch = np.transpose(appearance_video_batch, [0, 2, 3, 4, 1])
    appearance_deformed_batch = np.transpose(appearance_deformed_batch, [0, 2, 3, 4, 1])
    image = self.create_image_grid((appearance_video_batch, kp_appearance), (gt_video_batch, kp_video), out_video_batch, appearance_deformed_batch, gt_video_batch)
    image = (255 * image).astype(np.uint8)
    return image

def as_numpy(v):
    if isinstance(v, Variable):
        v = v.data
    return v.cpu().numpy()

def compute_image_gradient(image, padding=0):
    bs, c, h, w = image.shape
    sobel_x = torch.from_numpy(np.array([[1, 0, -1], [2, 0, -2], [1, 0, -1]])).type(image.type())
    filter = sobel_x.unsqueeze(0).repeat(c, 1, 1, 1)
    grad_x = F.conv2d(image, filter, groups=c, padding=padding)
    grad_x = grad_x
    sobel_y = torch.from_numpy(np.array([[1, 2, 1], [0, 0, 0], [-1, -2, -1]])).type(image.type())
    filter = sobel_y.unsqueeze(0).repeat(c, 1, 1, 1)
    grad_y = F.conv2d(image, filter, groups=c, padding=padding)
    grad_y = grad_y
    return torch.cat([grad_x, grad_y], dim=1)

def color_as_num(val):
    val = val.astype(np.uint64)
    return val[..., 0] + 256 * val[..., 1] + 256 * 256 * val[..., 2]

