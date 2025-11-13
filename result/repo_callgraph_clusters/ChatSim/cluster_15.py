# Cluster 15

def convert_to_ndc(origins: Tensor, directions: Tensor, pixtocam: Tensor, near: float=1.0) -> Tuple[Tensor, Tensor]:
    """Converts a set of rays to normalized device coordinates (NDC).

    Args:
      origins: ndarray(float32), [..., 3], world space ray origins.
      directions: ndarray(float32), [..., 3], world space ray directions.
      pixtocam: ndarray(float32), [3, 3], inverse intrinsic matrix.
      near: float, near plane along the negative z axis.
      xnp: either numpy or jax.numpy.

    Returns:
      origins_ndc: ndarray(float32), [..., 3].
      directions_ndc: ndarray(float32), [..., 3].

    This function assumes input rays should be mapped into the NDC space for a
    perspective projection pinhole camera, with identity extrinsic matrix (pose)
    and intrinsic parameters defined by inputs focal, width, and height.

    The near value specifies the near plane of the frustum, and the far plane is
    assumed to be infinity.

    The ray bundle for the identity pose camera will be remapped to parallel rays
    within the (-1, -1, -1) to (1, 1, 1) cube. Any other ray in the original
    world space can be remapped as long as it has dz < 0 (ray direction has a
    negative z-coord); this allows us to share a common NDC space for "forward
    facing" scenes.

    Note that
        projection(origins + t * directions)
    will NOT be equal to
        origins_ndc + t * directions_ndc
    and that the directions_ndc are not unit length. Rather, directions_ndc is
    defined such that the valid near and far planes in NDC will be 0 and 1.

    See Appendix C in https://arxiv.org/abs/2003.08934 for additional details.
    """
    t = -(near + origins[..., 2]) / directions[..., 2]
    origins = origins + t[..., None] * directions
    dx, dy, dz = torch.moveaxis(directions, -1, 0)
    ox, oy, oz = torch.moveaxis(origins, -1, 0)
    xmult = 1.0 / pixtocam[0, 2]
    ymult = 1.0 / pixtocam[1, 2]
    origins_ndc = torch.stack([xmult * ox / oz, ymult * oy / oz, -torch.ones_like(oz)], dim=-1)
    infinity_ndc = torch.stack([xmult * dx / dz, ymult * dy / dz, torch.ones_like(oz)], dim=-1)
    directions_ndc = infinity_ndc - origins_ndc
    return (origins_ndc, directions_ndc)

def pix_to_dir(x, y):
    return torch.stack([x + 0.5, y + 0.5, torch.ones_like(x)], dim=-1)

def pixels_to_rays(pix_x_int: Tensor, pix_y_int: Tensor, pixtocams: Tensor, camtoworlds: Tensor, distortion_params: Optional[Mapping[str, float]]=None, pixtocam_ndc: Optional[Tensor]=None, camtype: ProjectionType=ProjectionType.PERSPECTIVE) -> Tuple[Tensor, Tensor, Tensor, Tensor, Tensor]:
    """Calculates rays given pixel coordinates, intrinisics, and extrinsics.

    Given 2D pixel coordinates pix_x_int, pix_y_int for cameras with
    inverse intrinsics pixtocams and extrinsics camtoworlds (and optional
    distortion coefficients distortion_params and NDC space projection matrix
    pixtocam_ndc), computes the corresponding 3D camera rays.

    Vectorized over the leading dimensions of the first four arguments.

    Args:
      pix_x_int: int array, shape SH, x coordinates of image pixels.
      pix_y_int: int array, shape SH, y coordinates of image pixels.
      pixtocams: float array, broadcastable to SH + [3, 3], inverse intrinsics.
      camtoworlds: float array, broadcastable to SH + [3, 4], camera extrinsics.
      distortion_params: dict of floats, optional camera distortion parameters.
      pixtocam_ndc: float array, [3, 3], optional inverse intrinsics for NDC.
      camtype: camera_utils.ProjectionType, fisheye or perspective camera.
      xnp: either numpy or jax.numpy.

    Returns:
      origins: float array, shape SH + [3], ray origin points.
      directions: float array, shape SH + [3], ray direction vectors.
      viewdirs: float array, shape SH + [3], normalized ray direction vectors.
      radii: float array, shape SH + [1], ray differential radii.
      imageplane: float array, shape SH + [2], xy coordinates on the image plane.
        If the image plane is at world space distance 1 from the pinhole, then
        imageplane will be the xy coordinates of a pixel in that space (so the
        camera ray direction at the origin would be (x, y, -1) in OpenGL coords).
    """

    def pix_to_dir(x, y):
        return torch.stack([x + 0.5, y + 0.5, torch.ones_like(x)], dim=-1)
    pixel_dirs_stacked = torch.stack([pix_to_dir(pix_x_int, pix_y_int), pix_to_dir(pix_x_int + 1, pix_y_int), pix_to_dir(pix_x_int, pix_y_int + 1)], dim=0)
    mat_vec_mul = lambda A, b: torch.matmul(A, b[..., None])[..., 0]
    camera_dirs_stacked = mat_vec_mul(pixtocams, pixel_dirs_stacked)
    if distortion_params is not None:
        x, y = _radial_and_tangential_undistort(camera_dirs_stacked[..., 0], camera_dirs_stacked[..., 1], **distortion_params)
        camera_dirs_stacked = torch.stack([x, y, torch.ones_like(x)], -1)
    if camtype == ProjectionType.FISHEYE:
        theta = torch.sqrt(torch.sum(torch.square(camera_dirs_stacked[..., :2]), dim=-1))
        theta = theta.clip(None, np.pi)
        sin_theta_over_theta = torch.sin(theta) / theta
        camera_dirs_stacked = torch.stack([camera_dirs_stacked[..., 0] * sin_theta_over_theta, camera_dirs_stacked[..., 1] * sin_theta_over_theta, torch.cos(theta)], dim=-1)
    camera_dirs_stacked = torch.matmul(camera_dirs_stacked, torch.diag(torch.tensor([1.0, -1.0, -1.0], dtype=torch.float32, device=camera_dirs_stacked.device)))
    imageplane = camera_dirs_stacked[0, ..., :2]
    directions_stacked = mat_vec_mul(camtoworlds[..., :3, :3], camera_dirs_stacked)
    directions, dx, dy = directions_stacked
    origins = torch.broadcast_to(camtoworlds[..., :3, -1], directions.shape)
    viewdirs = directions / torch.linalg.norm(directions, ord=2, dim=-1, keepdim=True)
    if pixtocam_ndc is None:
        dx_norm = torch.linalg.norm(dx - directions, ord=2, dim=-1)
        dy_norm = torch.linalg.norm(dy - directions, ord=2, dim=-1)
    else:
        origins_dx, _ = convert_to_ndc(origins, dx, pixtocam_ndc)
        origins_dy, _ = convert_to_ndc(origins, dy, pixtocam_ndc)
        origins, directions = convert_to_ndc(origins, directions, pixtocam_ndc)
        dx_norm = torch.linalg.norm(origins_dx - origins, ord=2, dim=-1)
        dy_norm = torch.linalg.norm(origins_dy - origins, ord=2, dim=-1)
    radii = (0.5 * (dx_norm + dy_norm))[..., None] * 2 / np.sqrt(12.0)
    return (origins, directions, viewdirs, radii, imageplane)

def simple_radial_distortion(camera, x):
    return x * (1.0 + camera.k1 * np.square(x).sum(axis=-1, keepdims=True))

def radial_distortion(camera, x):
    r_sq = np.square(x).sum(axis=-1, keepdims=True)
    return x * (1.0 + r_sq * (camera.k1 + camera.k2 * r_sq))

def opencv_distortion(camera, x):
    x_sq = np.square(x)
    xy = np.prod(x, axis=-1, keepdims=True)
    r_sq = x_sq.sum(axis=-1, keepdims=True)
    return x * (1.0 + r_sq * (camera.k1 + camera.k2 * r_sq)) + np.concatenate((2.0 * camera.p1 * xy + camera.p2 * (r_sq + 2.0 * x_sq), camera.p1 * (r_sq + 2.0 * y_sq) + 2.0 * camera.p2 * xy), axis=-1)

class Quaternion:

    @staticmethod
    def FromR(R):
        trace = np.trace(R)
        if trace > 0:
            qw = 0.5 * np.sqrt(1.0 + trace)
            qx = (R[2, 1] - R[1, 2]) * 0.25 / qw
            qy = (R[0, 2] - R[2, 0]) * 0.25 / qw
            qz = (R[1, 0] - R[0, 1]) * 0.25 / qw
        elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
            s = 2.0 * np.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2])
            qw = (R[2, 1] - R[1, 2]) / s
            qx = 0.25 * s
            qy = (R[0, 1] + R[1, 0]) / s
            qz = (R[0, 2] + R[2, 0]) / s
        elif R[1, 1] > R[2, 2]:
            s = 2.0 * np.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2])
            qw = (R[0, 2] - R[2, 0]) / s
            qx = (R[0, 1] + R[1, 0]) / s
            qy = 0.25 * s
            qz = (R[1, 2] + R[2, 1]) / s
        else:
            s = 2.0 * np.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1])
            qw = (R[1, 0] - R[0, 1]) / s
            qx = (R[0, 2] + R[2, 0]) / s
            qy = (R[1, 2] + R[2, 1]) / s
            qz = 0.25 * s
        return Quaternion(np.array((qw, qx, qy, qz)))

    @staticmethod
    def FromAxisAngle(axis, angle=None):
        if angle is None:
            angle = np.linalg.norm(axis)
            if np.abs(angle) > np.finfo('float').eps:
                axis = axis / angle
        qw = np.cos(0.5 * angle)
        axis = axis * np.sin(0.5 * angle)
        return Quaternion(np.array((qw, axis[0], axis[1], axis[2])))

    def __init__(self, q=np.array((1.0, 0.0, 0.0, 0.0))):
        if isinstance(q, Quaternion):
            self.q = q.q.copy()
        else:
            q = np.asarray(q)
            if q.size == 4:
                self.q = q.copy()
            elif q.size == 3:
                self.q = np.empty(4)
                self.q[0], self.q[1:] = (0.0, q.ravel())
            else:
                raise Exception('Input quaternion should be a 3- or 4-vector')

    def __add__(self, other):
        return Quaternion(self.q + other.q)

    def __iadd__(self, other):
        self.q += other.q
        return self

    def __invert__(self):
        return Quaternion(np.array((self.q[0], -self.q[1], -self.q[2], -self.q[3])))

    def __mul__(self, other):
        if isinstance(other, Quaternion):
            return Quaternion(np.array((self.q[0] * other.q[0] - self.q[1] * other.q[1] - self.q[2] * other.q[2] - self.q[3] * other.q[3], self.q[0] * other.q[1] + self.q[1] * other.q[0] + self.q[2] * other.q[3] - self.q[3] * other.q[2], self.q[0] * other.q[2] - self.q[1] * other.q[3] + self.q[2] * other.q[0] + self.q[3] * other.q[1], self.q[0] * other.q[3] + self.q[1] * other.q[2] - self.q[2] * other.q[1] + self.q[3] * other.q[0])))
        else:
            return Quaternion(other * self.q)

    def __rmul__(self, other):
        return self * other

    def __imul__(self, other):
        self.q[:] = (self * other).q
        return self

    def __irmul__(self, other):
        self.q[:] = (self * other).q
        return self

    def __neg__(self):
        return Quaternion(-self.q)

    def __sub__(self, other):
        return Quaternion(self.q - other.q)

    def __isub__(self, other):
        self.q -= other.q
        return self

    def __str__(self):
        return str(self.q)

    def copy(self):
        return Quaternion(self)

    def dot(self, other):
        return self.q.dot(other.q)

    def inverse(self):
        return Quaternion((~self).q / self.q.dot(self.q))

    def norm(self):
        return np.linalg.norm(self.q)

    def normalize(self):
        self.q /= np.linalg.norm(self.q)
        return self

    def rotate_points(self, x):
        x = np.atleast_2d(x)
        return x.dot(self.ToR().T)

    def ToR(self):
        return np.eye(3) + 2 * np.array(((-self.q[2] * self.q[2] - self.q[3] * self.q[3], self.q[1] * self.q[2] - self.q[3] * self.q[0], self.q[1] * self.q[3] + self.q[2] * self.q[0]), (self.q[1] * self.q[2] + self.q[3] * self.q[0], -self.q[1] * self.q[1] - self.q[3] * self.q[3], self.q[2] * self.q[3] - self.q[1] * self.q[0]), (self.q[1] * self.q[3] - self.q[2] * self.q[0], self.q[2] * self.q[3] + self.q[1] * self.q[0], -self.q[1] * self.q[1] - self.q[2] * self.q[2])))

    def ToAxisAngle(self):
        sin_sq_theta = self.q[1:].dot(self.q[1:])
        if np.abs(sin_sq_theta) > np.finfo('float').eps:
            sin_theta = np.sqrt(sin_sq_theta)
            cos_theta = self.q[0]
            angle = 2.0 * (np.arctan2(-sin_theta, -cos_theta) if cos_theta < 0.0 else np.arctan2(sin_theta, cos_theta))
            return self.q[1:] * (angle / sin_theta)
        return np.zeros(3)

    def ToEulerAngles(self):
        qsq = self.q ** 2
        k = 2.0 * (self.q[0] * self.q[3] + self.q[1] * self.q[2]) / qsq.sum()
        if 1.0 - k < np.finfo('float').eps:
            return (2.0 * np.arctan2(self.q[1], self.q[0]), 0.5 * np.pi, 0.0)
        if 1.0 + k < np.finfo('float').eps:
            return (-2.0 * np.arctan2(self.q[1], self.q[0]), -0.5 * np.pi, 0.0)
        yaw = np.arctan2(2.0 * (self.q[0] * self.q[2] - self.q[1] * self.q[3]), qsq[0] + qsq[1] - qsq[2] - qsq[3])
        pitch = np.arcsin(k)
        roll = np.arctan2(2.0 * (self.q[0] * self.q[1] - self.q[2] * self.q[3]), qsq[0] - qsq[1] + qsq[2] - qsq[3])
        return (yaw, pitch, roll)

def ToEulerAngles(self):
    qsq = self.q ** 2
    k = 2.0 * (self.q[0] * self.q[3] + self.q[1] * self.q[2]) / qsq.sum()
    if 1.0 - k < np.finfo('float').eps:
        return (2.0 * np.arctan2(self.q[1], self.q[0]), 0.5 * np.pi, 0.0)
    if 1.0 + k < np.finfo('float').eps:
        return (-2.0 * np.arctan2(self.q[1], self.q[0]), -0.5 * np.pi, 0.0)
    yaw = np.arctan2(2.0 * (self.q[0] * self.q[2] - self.q[1] * self.q[3]), qsq[0] + qsq[1] - qsq[2] - qsq[3])
    pitch = np.arcsin(k)
    roll = np.arctan2(2.0 * (self.q[0] * self.q[1] - self.q[2] * self.q[3]), qsq[0] - qsq[1] + qsq[2] - qsq[3])
    return (yaw, pitch, roll)

def inter_two_poses(pose_a, pose_b, alpha):
    ret = np.zeros([3, 4], dtype=np.float64)
    rot_a = R.from_matrix(pose_a[:3, :3])
    rot_b = R.from_matrix(pose_b[:3, :3])
    key_rots = R.from_matrix(np.stack([pose_a[:3, :3], pose_b[:3, :3]], 0))
    key_times = [0, 1]
    slerp = Slerp(key_times, key_rots)
    rot = slerp(1.0 - alpha)
    ret[:3, :3] = rot.as_matrix()
    ret[:3, 3] = (pose_a * alpha + pose_b * (1.0 - alpha))[:3, 3]
    return ret

def convert_to_ndc(origins: Tensor, directions: Tensor, pixtocam: Tensor, near: float=1.0) -> Tuple[Tensor, Tensor]:
    """Converts a set of rays to normalized device coordinates (NDC).

    Args:
      origins: ndarray(float32), [..., 3], world space ray origins.
      directions: ndarray(float32), [..., 3], world space ray directions.
      pixtocam: ndarray(float32), [3, 3], inverse intrinsic matrix.
      near: float, near plane along the negative z axis.
      xnp: either numpy or jax.numpy.

    Returns:
      origins_ndc: ndarray(float32), [..., 3].
      directions_ndc: ndarray(float32), [..., 3].

    This function assumes input rays should be mapped into the NDC space for a
    perspective projection pinhole camera, with identity extrinsic matrix (pose)
    and intrinsic parameters defined by inputs focal, width, and height.

    The near value specifies the near plane of the frustum, and the far plane is
    assumed to be infinity.

    The ray bundle for the identity pose camera will be remapped to parallel rays
    within the (-1, -1, -1) to (1, 1, 1) cube. Any other ray in the original
    world space can be remapped as long as it has dz < 0 (ray direction has a
    negative z-coord); this allows us to share a common NDC space for "forward
    facing" scenes.

    Note that
        projection(origins + t * directions)
    will NOT be equal to
        origins_ndc + t * directions_ndc
    and that the directions_ndc are not unit length. Rather, directions_ndc is
    defined such that the valid near and far planes in NDC will be 0 and 1.

    See Appendix C in https://arxiv.org/abs/2003.08934 for additional details.
    """
    t = -(near + origins[..., 2]) / directions[..., 2]
    origins = origins + t[..., None] * directions
    dx, dy, dz = torch.moveaxis(directions, -1, 0)
    ox, oy, oz = torch.moveaxis(origins, -1, 0)
    xmult = 1.0 / pixtocam[0, 2]
    ymult = 1.0 / pixtocam[1, 2]
    origins_ndc = torch.stack([xmult * ox / oz, ymult * oy / oz, -torch.ones_like(oz)], dim=-1)
    infinity_ndc = torch.stack([xmult * dx / dz, ymult * dy / dz, torch.ones_like(oz)], dim=-1)
    directions_ndc = infinity_ndc - origins_ndc
    return (origins_ndc, directions_ndc)

def pix_to_dir(x, y):
    return torch.stack([x + 0.5, y + 0.5, torch.ones_like(x)], dim=-1)

def pixels_to_rays(pix_x_int: Tensor, pix_y_int: Tensor, pixtocams: Tensor, camtoworlds: Tensor, distortion_params: Optional[Mapping[str, float]]=None, pixtocam_ndc: Optional[Tensor]=None, camtype: ProjectionType=ProjectionType.PERSPECTIVE) -> Tuple[Tensor, Tensor, Tensor, Tensor, Tensor]:
    """Calculates rays given pixel coordinates, intrinisics, and extrinsics.

    Given 2D pixel coordinates pix_x_int, pix_y_int for cameras with
    inverse intrinsics pixtocams and extrinsics camtoworlds (and optional
    distortion coefficients distortion_params and NDC space projection matrix
    pixtocam_ndc), computes the corresponding 3D camera rays.

    Vectorized over the leading dimensions of the first four arguments.

    Args:
      pix_x_int: int array, shape SH, x coordinates of image pixels.
      pix_y_int: int array, shape SH, y coordinates of image pixels.
      pixtocams: float array, broadcastable to SH + [3, 3], inverse intrinsics.
      camtoworlds: float array, broadcastable to SH + [3, 4], camera extrinsics.
      distortion_params: dict of floats, optional camera distortion parameters.
      pixtocam_ndc: float array, [3, 3], optional inverse intrinsics for NDC.
      camtype: camera_utils.ProjectionType, fisheye or perspective camera.
      xnp: either numpy or jax.numpy.

    Returns:
      origins: float array, shape SH + [3], ray origin points.
      directions: float array, shape SH + [3], ray direction vectors.
      viewdirs: float array, shape SH + [3], normalized ray direction vectors.
      radii: float array, shape SH + [1], ray differential radii.
      imageplane: float array, shape SH + [2], xy coordinates on the image plane.
        If the image plane is at world space distance 1 from the pinhole, then
        imageplane will be the xy coordinates of a pixel in that space (so the
        camera ray direction at the origin would be (x, y, -1) in OpenGL coords).
    """

    def pix_to_dir(x, y):
        return torch.stack([x + 0.5, y + 0.5, torch.ones_like(x)], dim=-1)
    pixel_dirs_stacked = torch.stack([pix_to_dir(pix_x_int, pix_y_int), pix_to_dir(pix_x_int + 1, pix_y_int), pix_to_dir(pix_x_int, pix_y_int + 1)], dim=0)
    mat_vec_mul = lambda A, b: torch.matmul(A, b[..., None])[..., 0]
    camera_dirs_stacked = mat_vec_mul(pixtocams, pixel_dirs_stacked)
    if distortion_params is not None:
        x, y = _radial_and_tangential_undistort(camera_dirs_stacked[..., 0], camera_dirs_stacked[..., 1], **distortion_params)
        camera_dirs_stacked = torch.stack([x, y, torch.ones_like(x)], -1)
    if camtype == ProjectionType.FISHEYE:
        theta = torch.sqrt(torch.sum(torch.square(camera_dirs_stacked[..., :2]), dim=-1))
        theta = theta.clip(None, np.pi)
        sin_theta_over_theta = torch.sin(theta) / theta
        camera_dirs_stacked = torch.stack([camera_dirs_stacked[..., 0] * sin_theta_over_theta, camera_dirs_stacked[..., 1] * sin_theta_over_theta, torch.cos(theta)], dim=-1)
    camera_dirs_stacked = torch.matmul(camera_dirs_stacked, torch.diag(torch.tensor([1.0, -1.0, -1.0], dtype=torch.float32, device=camera_dirs_stacked.device)))
    imageplane = camera_dirs_stacked[0, ..., :2]
    directions_stacked = mat_vec_mul(camtoworlds[..., :3, :3], camera_dirs_stacked)
    directions, dx, dy = directions_stacked
    origins = torch.broadcast_to(camtoworlds[..., :3, -1], directions.shape)
    viewdirs = directions / torch.linalg.norm(directions, ord=2, dim=-1, keepdim=True)
    if pixtocam_ndc is None:
        dx_norm = torch.linalg.norm(dx - directions, ord=2, dim=-1)
        dy_norm = torch.linalg.norm(dy - directions, ord=2, dim=-1)
    else:
        origins_dx, _ = convert_to_ndc(origins, dx, pixtocam_ndc)
        origins_dy, _ = convert_to_ndc(origins, dy, pixtocam_ndc)
        origins, directions = convert_to_ndc(origins, directions, pixtocam_ndc)
        dx_norm = torch.linalg.norm(origins_dx - origins, ord=2, dim=-1)
        dy_norm = torch.linalg.norm(origins_dy - origins, ord=2, dim=-1)
    radii = (0.5 * (dx_norm + dy_norm))[..., None] * 2 / np.sqrt(12.0)
    return (origins, directions, viewdirs, radii, imageplane)

def rgb_ssim(img0, img1, max_val, filter_size=11, filter_sigma=1.5, k1=0.01, k2=0.03, return_map=False):
    assert len(img0.shape) == 3
    assert img0.shape[-1] == 3
    assert img0.shape == img1.shape
    hw = filter_size // 2
    shift = (2 * hw - filter_size + 1) / 2
    f_i = ((np.arange(filter_size) - hw + shift) / filter_sigma) ** 2
    filt = np.exp(-0.5 * f_i)
    filt /= np.sum(filt)

    def convolve2d(z, f):
        return scipy.signal.convolve2d(z, f, mode='valid')
    filt_fn = lambda z: np.stack([convolve2d(convolve2d(z[..., i], filt[:, None]), filt[None, :]) for i in range(z.shape[-1])], -1)
    mu0 = filt_fn(img0)
    mu1 = filt_fn(img1)
    mu00 = mu0 * mu0
    mu11 = mu1 * mu1
    mu01 = mu0 * mu1
    sigma00 = filt_fn(img0 ** 2) - mu00
    sigma11 = filt_fn(img1 ** 2) - mu11
    sigma01 = filt_fn(img0 * img1) - mu01
    sigma00 = np.maximum(0.0, sigma00)
    sigma11 = np.maximum(0.0, sigma11)
    sigma01 = np.sign(sigma01) * np.minimum(np.sqrt(sigma00 * sigma11), np.abs(sigma01))
    c1 = (k1 * max_val) ** 2
    c2 = (k2 * max_val) ** 2
    numer = (2 * mu01 + c1) * (2 * sigma01 + c2)
    denom = (mu00 + mu11 + c1) * (sigma00 + sigma11 + c2)
    ssim_map = numer / denom
    ssim = np.mean(ssim_map)
    return ssim_map if return_map else ssim

def convolve2d(z, f):
    return scipy.signal.convolve2d(z, f, mode='valid')

def rgb_ssim(img0, img1, max_val, filter_size=11, filter_sigma=1.5, k1=0.01, k2=0.03, return_map=False):
    assert len(img0.shape) == 3
    assert img0.shape[-1] == 3
    assert img0.shape == img1.shape
    hw = filter_size // 2
    shift = (2 * hw - filter_size + 1) / 2
    f_i = ((np.arange(filter_size) - hw + shift) / filter_sigma) ** 2
    filt = np.exp(-0.5 * f_i)
    filt /= np.sum(filt)

    def convolve2d(z, f):
        return scipy.signal.convolve2d(z, f, mode='valid')
    filt_fn = lambda z: np.stack([convolve2d(convolve2d(z[..., i], filt[:, None]), filt[None, :]) for i in range(z.shape[-1])], -1)
    mu0 = filt_fn(img0)
    mu1 = filt_fn(img1)
    mu00 = mu0 * mu0
    mu11 = mu1 * mu1
    mu01 = mu0 * mu1
    sigma00 = filt_fn(img0 ** 2) - mu00
    sigma11 = filt_fn(img1 ** 2) - mu11
    sigma01 = filt_fn(img0 * img1) - mu01
    sigma00 = np.maximum(0.0, sigma00)
    sigma11 = np.maximum(0.0, sigma11)
    sigma01 = np.sign(sigma01) * np.minimum(np.sqrt(sigma00 * sigma11), np.abs(sigma01))
    c1 = (k1 * max_val) ** 2
    c2 = (k2 * max_val) ** 2
    numer = (2 * mu01 + c1) * (2 * sigma01 + c2)
    denom = (mu00 + mu11 + c1) * (sigma00 + sigma11 + c2)
    ssim_map = numer / denom
    ssim = np.mean(ssim_map)
    return ssim_map if return_map else ssim

def convolve2d(z, f):
    return scipy.signal.convolve2d(z, f, mode='valid')

def simple_radial_distortion(camera, x):
    return x * (1.0 + camera.k1 * np.square(x).sum(axis=-1, keepdims=True))

def radial_distortion(camera, x):
    r_sq = np.square(x).sum(axis=-1, keepdims=True)
    return x * (1.0 + r_sq * (camera.k1 + camera.k2 * r_sq))

def opencv_distortion(camera, x):
    x_sq = np.square(x)
    xy = np.prod(x, axis=-1, keepdims=True)
    r_sq = x_sq.sum(axis=-1, keepdims=True)
    return x * (1.0 + r_sq * (camera.k1 + camera.k2 * r_sq)) + np.concatenate((2.0 * camera.p1 * xy + camera.p2 * (r_sq + 2.0 * x_sq), camera.p1 * (r_sq + 2.0 * y_sq) + 2.0 * camera.p2 * xy), axis=-1)

class Quaternion:

    @staticmethod
    def FromR(R):
        trace = np.trace(R)
        if trace > 0:
            qw = 0.5 * np.sqrt(1.0 + trace)
            qx = (R[2, 1] - R[1, 2]) * 0.25 / qw
            qy = (R[0, 2] - R[2, 0]) * 0.25 / qw
            qz = (R[1, 0] - R[0, 1]) * 0.25 / qw
        elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
            s = 2.0 * np.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2])
            qw = (R[2, 1] - R[1, 2]) / s
            qx = 0.25 * s
            qy = (R[0, 1] + R[1, 0]) / s
            qz = (R[0, 2] + R[2, 0]) / s
        elif R[1, 1] > R[2, 2]:
            s = 2.0 * np.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2])
            qw = (R[0, 2] - R[2, 0]) / s
            qx = (R[0, 1] + R[1, 0]) / s
            qy = 0.25 * s
            qz = (R[1, 2] + R[2, 1]) / s
        else:
            s = 2.0 * np.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1])
            qw = (R[1, 0] - R[0, 1]) / s
            qx = (R[0, 2] + R[2, 0]) / s
            qy = (R[1, 2] + R[2, 1]) / s
            qz = 0.25 * s
        return Quaternion(np.array((qw, qx, qy, qz)))

    @staticmethod
    def FromAxisAngle(axis, angle=None):
        if angle is None:
            angle = np.linalg.norm(axis)
            if np.abs(angle) > np.finfo('float').eps:
                axis = axis / angle
        qw = np.cos(0.5 * angle)
        axis = axis * np.sin(0.5 * angle)
        return Quaternion(np.array((qw, axis[0], axis[1], axis[2])))

    def __init__(self, q=np.array((1.0, 0.0, 0.0, 0.0))):
        if isinstance(q, Quaternion):
            self.q = q.q.copy()
        else:
            q = np.asarray(q)
            if q.size == 4:
                self.q = q.copy()
            elif q.size == 3:
                self.q = np.empty(4)
                self.q[0], self.q[1:] = (0.0, q.ravel())
            else:
                raise Exception('Input quaternion should be a 3- or 4-vector')

    def __add__(self, other):
        return Quaternion(self.q + other.q)

    def __iadd__(self, other):
        self.q += other.q
        return self

    def __invert__(self):
        return Quaternion(np.array((self.q[0], -self.q[1], -self.q[2], -self.q[3])))

    def __mul__(self, other):
        if isinstance(other, Quaternion):
            return Quaternion(np.array((self.q[0] * other.q[0] - self.q[1] * other.q[1] - self.q[2] * other.q[2] - self.q[3] * other.q[3], self.q[0] * other.q[1] + self.q[1] * other.q[0] + self.q[2] * other.q[3] - self.q[3] * other.q[2], self.q[0] * other.q[2] - self.q[1] * other.q[3] + self.q[2] * other.q[0] + self.q[3] * other.q[1], self.q[0] * other.q[3] + self.q[1] * other.q[2] - self.q[2] * other.q[1] + self.q[3] * other.q[0])))
        else:
            return Quaternion(other * self.q)

    def __rmul__(self, other):
        return self * other

    def __imul__(self, other):
        self.q[:] = (self * other).q
        return self

    def __irmul__(self, other):
        self.q[:] = (self * other).q
        return self

    def __neg__(self):
        return Quaternion(-self.q)

    def __sub__(self, other):
        return Quaternion(self.q - other.q)

    def __isub__(self, other):
        self.q -= other.q
        return self

    def __str__(self):
        return str(self.q)

    def copy(self):
        return Quaternion(self)

    def dot(self, other):
        return self.q.dot(other.q)

    def inverse(self):
        return Quaternion((~self).q / self.q.dot(self.q))

    def norm(self):
        return np.linalg.norm(self.q)

    def normalize(self):
        self.q /= np.linalg.norm(self.q)
        return self

    def rotate_points(self, x):
        x = np.atleast_2d(x)
        return x.dot(self.ToR().T)

    def ToR(self):
        return np.eye(3) + 2 * np.array(((-self.q[2] * self.q[2] - self.q[3] * self.q[3], self.q[1] * self.q[2] - self.q[3] * self.q[0], self.q[1] * self.q[3] + self.q[2] * self.q[0]), (self.q[1] * self.q[2] + self.q[3] * self.q[0], -self.q[1] * self.q[1] - self.q[3] * self.q[3], self.q[2] * self.q[3] - self.q[1] * self.q[0]), (self.q[1] * self.q[3] - self.q[2] * self.q[0], self.q[2] * self.q[3] + self.q[1] * self.q[0], -self.q[1] * self.q[1] - self.q[2] * self.q[2])))

    def ToAxisAngle(self):
        sin_sq_theta = self.q[1:].dot(self.q[1:])
        if np.abs(sin_sq_theta) > np.finfo('float').eps:
            sin_theta = np.sqrt(sin_sq_theta)
            cos_theta = self.q[0]
            angle = 2.0 * (np.arctan2(-sin_theta, -cos_theta) if cos_theta < 0.0 else np.arctan2(sin_theta, cos_theta))
            return self.q[1:] * (angle / sin_theta)
        return np.zeros(3)

    def ToEulerAngles(self):
        qsq = self.q ** 2
        k = 2.0 * (self.q[0] * self.q[3] + self.q[1] * self.q[2]) / qsq.sum()
        if 1.0 - k < np.finfo('float').eps:
            return (2.0 * np.arctan2(self.q[1], self.q[0]), 0.5 * np.pi, 0.0)
        if 1.0 + k < np.finfo('float').eps:
            return (-2.0 * np.arctan2(self.q[1], self.q[0]), -0.5 * np.pi, 0.0)
        yaw = np.arctan2(2.0 * (self.q[0] * self.q[2] - self.q[1] * self.q[3]), qsq[0] + qsq[1] - qsq[2] - qsq[3])
        pitch = np.arcsin(k)
        roll = np.arctan2(2.0 * (self.q[0] * self.q[1] - self.q[2] * self.q[3]), qsq[0] - qsq[1] + qsq[2] - qsq[3])
        return (yaw, pitch, roll)

def ToEulerAngles(self):
    qsq = self.q ** 2
    k = 2.0 * (self.q[0] * self.q[3] + self.q[1] * self.q[2]) / qsq.sum()
    if 1.0 - k < np.finfo('float').eps:
        return (2.0 * np.arctan2(self.q[1], self.q[0]), 0.5 * np.pi, 0.0)
    if 1.0 + k < np.finfo('float').eps:
        return (-2.0 * np.arctan2(self.q[1], self.q[0]), -0.5 * np.pi, 0.0)
    yaw = np.arctan2(2.0 * (self.q[0] * self.q[2] - self.q[1] * self.q[3]), qsq[0] + qsq[1] - qsq[2] - qsq[3])
    pitch = np.arcsin(k)
    roll = np.arctan2(2.0 * (self.q[0] * self.q[1] - self.q[2] * self.q[3]), qsq[0] - qsq[1] + qsq[2] - qsq[3])
    return (yaw, pitch, roll)

def build_rotation(r):
    norm = torch.sqrt(r[:, 0] * r[:, 0] + r[:, 1] * r[:, 1] + r[:, 2] * r[:, 2] + r[:, 3] * r[:, 3])
    q = r / norm[:, None]
    R = torch.zeros((q.size(0), 3, 3), device='cuda')
    r = q[:, 0]
    x = q[:, 1]
    y = q[:, 2]
    z = q[:, 3]
    R[:, 0, 0] = 1 - 2 * (y * y + z * z)
    R[:, 0, 1] = 2 * (x * y - r * z)
    R[:, 0, 2] = 2 * (x * z + r * y)
    R[:, 1, 0] = 2 * (x * y + r * z)
    R[:, 1, 1] = 1 - 2 * (x * x + z * z)
    R[:, 1, 2] = 2 * (y * z - r * x)
    R[:, 2, 0] = 2 * (x * z - r * y)
    R[:, 2, 1] = 2 * (y * z + r * x)
    R[:, 2, 2] = 1 - 2 * (x * x + y * y)
    return R

def getProjectionMatrix(znear, zfar, fovX, fovY):
    tanHalfFovY = math.tan(fovY / 2)
    tanHalfFovX = math.tan(fovX / 2)
    top = tanHalfFovY * znear
    bottom = -top
    right = tanHalfFovX * znear
    left = -right
    P = torch.zeros(4, 4)
    z_sign = 1.0
    P[0, 0] = 2.0 * znear / (right - left)
    P[1, 1] = 2.0 * znear / (top - bottom)
    P[0, 2] = (right + left) / (right - left)
    P[1, 2] = (top + bottom) / (top - bottom)
    P[3, 2] = z_sign
    P[2, 2] = z_sign * zfar / (zfar - znear)
    P[2, 3] = -(zfar * znear) / (zfar - znear)
    return P

def fov2focal(fov, pixels):
    return pixels / (2 * math.tan(fov / 2))

def gaussian(window_size, sigma):
    gauss = torch.Tensor([exp(-(x - window_size // 2) ** 2 / float(2 * sigma ** 2)) for x in range(window_size)])
    return gauss / gauss.sum()

def ssim(img1, img2, window_size=11, size_average=True):
    channel = img1.size(-3)
    window = create_window(window_size, channel)
    if img1.is_cuda:
        window = window.cuda(img1.get_device())
    window = window.type_as(img1)
    return _ssim(img1, img2, window, window_size, channel, size_average)

class GaussianModel:

    def setup_functions(self):

        def build_covariance_from_scaling_rotation(scaling, scaling_modifier, rotation):
            L = build_scaling_rotation(scaling_modifier * scaling, rotation)
            actual_covariance = L @ L.transpose(1, 2)
            symm = strip_symmetric(actual_covariance)
            return symm
        self.scaling_activation = torch.exp
        self.scaling_inverse_activation = torch.log
        self.covariance_activation = build_covariance_from_scaling_rotation
        self.opacity_activation = torch.sigmoid
        self.inverse_opacity_activation = inverse_sigmoid
        self.rotation_activation = torch.nn.functional.normalize

    def __init__(self, args):
        self.active_sh_degree = 0
        self.max_sh_degree = args.sh_degree
        self._xyz = torch.empty(0)
        self._features_dc = torch.empty(0)
        self._features_rest = torch.empty(0)
        self._scaling = torch.empty(0)
        self._rotation = torch.empty(0)
        self._opacity = torch.empty(0)
        self.max_radii2D = torch.empty(0)
        self.xyz_gradient_accum = torch.empty(0)
        self.denom = torch.empty(0)
        self.optimizer = None
        self.percent_dense = 0
        self.spatial_lr_scale = 0
        self.setup_functions()
        if args.get('sky_model', None) is not None:
            model_filename = 'scene.sky.' + args.sky_model
            model_lib = importlib.import_module(model_filename)
            model_cls = None
            target_model_name = args.sky_model.replace('_', '')
            for name, cls in model_lib.__dict__.items():
                if name.lower() == target_model_name.lower():
                    model_cls = cls
            self.sky_model = model_cls(args.sky_model_args).cuda()
        else:
            self.sky_model = None

    def capture(self):
        return_list = [self.active_sh_degree, self._xyz, self._features_dc, self._features_rest, self._scaling, self._rotation, self._opacity, self.max_radii2D, self.xyz_gradient_accum, self.denom, self.optimizer.state_dict(), self.spatial_lr_scale]
        if self.sky_model is not None:
            return_list.append(self.sky_model.capture())
        return return_list

    def restore(self, model_args, training_args):
        if self.sky_model is not None:
            self.sky_model.restore(model_args.pop(-1))
        self.active_sh_degree, self._xyz, self._features_dc, self._features_rest, self._scaling, self._rotation, self._opacity, self.max_radii2D, xyz_gradient_accum, denom, opt_dict, self.spatial_lr_scale = model_args
        self.training_setup(training_args)
        self.xyz_gradient_accum = xyz_gradient_accum
        self.denom = denom
        self.optimizer.load_state_dict(opt_dict)

    @property
    def get_scaling(self):
        return self.scaling_activation(self._scaling)

    @property
    def get_rotation(self):
        return self.rotation_activation(self._rotation)

    @property
    def get_xyz(self):
        return self._xyz

    @property
    def get_features(self):
        features_dc = self._features_dc
        features_rest = self._features_rest
        return torch.cat((features_dc, features_rest), dim=1)

    @property
    def get_opacity(self):
        return self.opacity_activation(self._opacity)

    def get_covariance(self, scaling_modifier=1):
        return self.covariance_activation(self.get_scaling, scaling_modifier, self._rotation)

    def oneupSHdegree(self):
        if self.active_sh_degree < self.max_sh_degree:
            self.active_sh_degree += 1

    def create_from_pcd(self, pcd: BasicPointCloud, spatial_lr_scale: float):
        self.spatial_lr_scale = spatial_lr_scale
        fused_point_cloud = torch.tensor(np.asarray(pcd.points)).float().cuda()
        fused_color = RGB2SH(torch.tensor(np.asarray(pcd.colors)).float().cuda())
        features = torch.zeros((fused_color.shape[0], 3, (self.max_sh_degree + 1) ** 2)).float().cuda()
        features[:, :3, 0] = fused_color
        features[:, 3:, 1:] = 0.0
        print('Number of points at initialisation : ', fused_point_cloud.shape[0])
        dist2 = torch.clamp_min(distCUDA2(torch.from_numpy(np.asarray(pcd.points)).float().cuda()), 1e-07)
        scales = torch.log(torch.sqrt(dist2))[..., None].repeat(1, 3)
        rots = torch.zeros((fused_point_cloud.shape[0], 4), device='cuda')
        rots[:, 0] = 1
        opacities = inverse_sigmoid(0.1 * torch.ones((fused_point_cloud.shape[0], 1), dtype=torch.float, device='cuda'))
        self._xyz = nn.Parameter(fused_point_cloud.requires_grad_(True))
        self._features_dc = nn.Parameter(features[:, :, 0:1].transpose(1, 2).contiguous().requires_grad_(True))
        self._features_rest = nn.Parameter(features[:, :, 1:].transpose(1, 2).contiguous().requires_grad_(True))
        self._scaling = nn.Parameter(scales.requires_grad_(True))
        self._rotation = nn.Parameter(rots.requires_grad_(True))
        self._opacity = nn.Parameter(opacities.requires_grad_(True))
        self.max_radii2D = torch.zeros(self.get_xyz.shape[0], device='cuda')

    def training_setup(self, training_args):
        self.percent_dense = training_args.percent_dense
        self.xyz_gradient_accum = torch.zeros((self.get_xyz.shape[0], 1), device='cuda')
        self.denom = torch.zeros((self.get_xyz.shape[0], 1), device='cuda')
        l = [{'params': [self._xyz], 'lr': training_args.position_lr_init * self.spatial_lr_scale, 'name': 'xyz'}, {'params': [self._features_dc], 'lr': training_args.feature_lr, 'name': 'f_dc'}, {'params': [self._features_rest], 'lr': training_args.feature_lr / 20.0, 'name': 'f_rest'}, {'params': [self._opacity], 'lr': training_args.opacity_lr, 'name': 'opacity'}, {'params': [self._scaling], 'lr': training_args.scaling_lr, 'name': 'scaling'}, {'params': [self._rotation], 'lr': training_args.rotation_lr, 'name': 'rotation'}]
        if self.sky_model is not None:
            l += ({'params': self.sky_model.train_params(), 'lr': training_args.sky_model_lr, 'name': 'sky_model'},)
        self.optimizer = torch.optim.Adam(l, lr=0.0, eps=1e-15)
        self.xyz_scheduler_args = get_expon_lr_func(lr_init=training_args.position_lr_init * self.spatial_lr_scale, lr_final=training_args.position_lr_final * self.spatial_lr_scale, lr_delay_mult=training_args.position_lr_delay_mult, max_steps=training_args.position_lr_max_steps)

    def update_learning_rate(self, iteration):
        """ Learning rate scheduling per step """
        for param_group in self.optimizer.param_groups:
            if param_group['name'] == 'xyz':
                lr = self.xyz_scheduler_args(iteration)
                param_group['lr'] = lr
                return lr

    def construct_list_of_attributes(self):
        l = ['x', 'y', 'z', 'nx', 'ny', 'nz']
        for i in range(self._features_dc.shape[1] * self._features_dc.shape[2]):
            l.append('f_dc_{}'.format(i))
        for i in range(self._features_rest.shape[1] * self._features_rest.shape[2]):
            l.append('f_rest_{}'.format(i))
        l.append('opacity')
        for i in range(self._scaling.shape[1]):
            l.append('scale_{}'.format(i))
        for i in range(self._rotation.shape[1]):
            l.append('rot_{}'.format(i))
        return l

    def save_ply(self, path):
        mkdir_p(os.path.dirname(path))
        xyz = self._xyz.detach().cpu().numpy()
        normals = np.zeros_like(xyz)
        f_dc = self._features_dc.detach().transpose(1, 2).flatten(start_dim=1).contiguous().cpu().numpy()
        f_rest = self._features_rest.detach().transpose(1, 2).flatten(start_dim=1).contiguous().cpu().numpy()
        opacities = self._opacity.detach().cpu().numpy()
        scale = self._scaling.detach().cpu().numpy()
        rotation = self._rotation.detach().cpu().numpy()
        dtype_full = [(attribute, 'f4') for attribute in self.construct_list_of_attributes()]
        elements = np.empty(xyz.shape[0], dtype=dtype_full)
        attributes = np.concatenate((xyz, normals, f_dc, f_rest, opacities, scale, rotation), axis=1)
        elements[:] = list(map(tuple, attributes))
        el = PlyElement.describe(elements, 'vertex')
        PlyData([el]).write(path)

    def reset_opacity(self):
        opacities_new = inverse_sigmoid(torch.min(self.get_opacity, torch.ones_like(self.get_opacity) * 0.01))
        optimizable_tensors = self.replace_tensor_to_optimizer(opacities_new, 'opacity')
        self._opacity = optimizable_tensors['opacity']

    def load_ply(self, path):
        plydata = PlyData.read(path)
        xyz = np.stack((np.asarray(plydata.elements[0]['x']), np.asarray(plydata.elements[0]['y']), np.asarray(plydata.elements[0]['z'])), axis=1)
        opacities = np.asarray(plydata.elements[0]['opacity'])[..., np.newaxis]
        features_dc = np.zeros((xyz.shape[0], 3, 1))
        features_dc[:, 0, 0] = np.asarray(plydata.elements[0]['f_dc_0'])
        features_dc[:, 1, 0] = np.asarray(plydata.elements[0]['f_dc_1'])
        features_dc[:, 2, 0] = np.asarray(plydata.elements[0]['f_dc_2'])
        extra_f_names = [p.name for p in plydata.elements[0].properties if p.name.startswith('f_rest_')]
        extra_f_names = sorted(extra_f_names, key=lambda x: int(x.split('_')[-1]))
        assert len(extra_f_names) == 3 * (self.max_sh_degree + 1) ** 2 - 3
        features_extra = np.zeros((xyz.shape[0], len(extra_f_names)))
        for idx, attr_name in enumerate(extra_f_names):
            features_extra[:, idx] = np.asarray(plydata.elements[0][attr_name])
        features_extra = features_extra.reshape((features_extra.shape[0], 3, (self.max_sh_degree + 1) ** 2 - 1))
        scale_names = [p.name for p in plydata.elements[0].properties if p.name.startswith('scale_')]
        scale_names = sorted(scale_names, key=lambda x: int(x.split('_')[-1]))
        scales = np.zeros((xyz.shape[0], len(scale_names)))
        for idx, attr_name in enumerate(scale_names):
            scales[:, idx] = np.asarray(plydata.elements[0][attr_name])
        rot_names = [p.name for p in plydata.elements[0].properties if p.name.startswith('rot')]
        rot_names = sorted(rot_names, key=lambda x: int(x.split('_')[-1]))
        rots = np.zeros((xyz.shape[0], len(rot_names)))
        for idx, attr_name in enumerate(rot_names):
            rots[:, idx] = np.asarray(plydata.elements[0][attr_name])
        self._xyz = nn.Parameter(torch.tensor(xyz, dtype=torch.float, device='cuda').requires_grad_(True))
        self._features_dc = nn.Parameter(torch.tensor(features_dc, dtype=torch.float, device='cuda').transpose(1, 2).contiguous().requires_grad_(True))
        self._features_rest = nn.Parameter(torch.tensor(features_extra, dtype=torch.float, device='cuda').transpose(1, 2).contiguous().requires_grad_(True))
        self._opacity = nn.Parameter(torch.tensor(opacities, dtype=torch.float, device='cuda').requires_grad_(True))
        self._scaling = nn.Parameter(torch.tensor(scales, dtype=torch.float, device='cuda').requires_grad_(True))
        self._rotation = nn.Parameter(torch.tensor(rots, dtype=torch.float, device='cuda').requires_grad_(True))
        self.active_sh_degree = self.max_sh_degree

    def replace_tensor_to_optimizer(self, tensor, name):
        optimizable_tensors = {}
        for group in self.optimizer.param_groups:
            if group['name'] == name:
                stored_state = self.optimizer.state.get(group['params'][0], None)
                stored_state['exp_avg'] = torch.zeros_like(tensor)
                stored_state['exp_avg_sq'] = torch.zeros_like(tensor)
                del self.optimizer.state[group['params'][0]]
                group['params'][0] = nn.Parameter(tensor.requires_grad_(True))
                self.optimizer.state[group['params'][0]] = stored_state
                optimizable_tensors[group['name']] = group['params'][0]
        return optimizable_tensors

    def _prune_optimizer(self, mask):
        optimizable_tensors = {}
        for group in self.optimizer.param_groups:
            if 'sky_model' in group['name']:
                continue
            stored_state = self.optimizer.state.get(group['params'][0], None)
            if stored_state is not None:
                stored_state['exp_avg'] = stored_state['exp_avg'][mask]
                stored_state['exp_avg_sq'] = stored_state['exp_avg_sq'][mask]
                del self.optimizer.state[group['params'][0]]
                group['params'][0] = nn.Parameter(group['params'][0][mask].requires_grad_(True))
                self.optimizer.state[group['params'][0]] = stored_state
                optimizable_tensors[group['name']] = group['params'][0]
            else:
                group['params'][0] = nn.Parameter(group['params'][0][mask].requires_grad_(True))
                optimizable_tensors[group['name']] = group['params'][0]
        return optimizable_tensors

    def prune_points(self, mask):
        valid_points_mask = ~mask
        optimizable_tensors = self._prune_optimizer(valid_points_mask)
        self._xyz = optimizable_tensors['xyz']
        self._features_dc = optimizable_tensors['f_dc']
        self._features_rest = optimizable_tensors['f_rest']
        self._opacity = optimizable_tensors['opacity']
        self._scaling = optimizable_tensors['scaling']
        self._rotation = optimizable_tensors['rotation']
        self.xyz_gradient_accum = self.xyz_gradient_accum[valid_points_mask]
        self.denom = self.denom[valid_points_mask]
        self.max_radii2D = self.max_radii2D[valid_points_mask]

    def cat_tensors_to_optimizer(self, tensors_dict):
        optimizable_tensors = {}
        for group in self.optimizer.param_groups:
            if 'sky_model' in group['name']:
                continue
            assert len(group['params']) == 1
            extension_tensor = tensors_dict[group['name']]
            stored_state = self.optimizer.state.get(group['params'][0], None)
            if stored_state is not None:
                stored_state['exp_avg'] = torch.cat((stored_state['exp_avg'], torch.zeros_like(extension_tensor)), dim=0)
                stored_state['exp_avg_sq'] = torch.cat((stored_state['exp_avg_sq'], torch.zeros_like(extension_tensor)), dim=0)
                del self.optimizer.state[group['params'][0]]
                group['params'][0] = nn.Parameter(torch.cat((group['params'][0], extension_tensor), dim=0).requires_grad_(True))
                self.optimizer.state[group['params'][0]] = stored_state
                optimizable_tensors[group['name']] = group['params'][0]
            else:
                group['params'][0] = nn.Parameter(torch.cat((group['params'][0], extension_tensor), dim=0).requires_grad_(True))
                optimizable_tensors[group['name']] = group['params'][0]
        return optimizable_tensors

    def densification_postfix(self, new_xyz, new_features_dc, new_features_rest, new_opacities, new_scaling, new_rotation):
        d = {'xyz': new_xyz, 'f_dc': new_features_dc, 'f_rest': new_features_rest, 'opacity': new_opacities, 'scaling': new_scaling, 'rotation': new_rotation}
        optimizable_tensors = self.cat_tensors_to_optimizer(d)
        self._xyz = optimizable_tensors['xyz']
        self._features_dc = optimizable_tensors['f_dc']
        self._features_rest = optimizable_tensors['f_rest']
        self._opacity = optimizable_tensors['opacity']
        self._scaling = optimizable_tensors['scaling']
        self._rotation = optimizable_tensors['rotation']
        self.xyz_gradient_accum = torch.zeros((self.get_xyz.shape[0], 1), device='cuda')
        self.denom = torch.zeros((self.get_xyz.shape[0], 1), device='cuda')
        self.max_radii2D = torch.zeros(self.get_xyz.shape[0], device='cuda')

    def densify_and_split(self, grads, grad_threshold, scene_extent, N=2):
        n_init_points = self.get_xyz.shape[0]
        padded_grad = torch.zeros(n_init_points, device='cuda')
        padded_grad[:grads.shape[0]] = grads.squeeze()
        selected_pts_mask = torch.where(padded_grad >= grad_threshold, True, False)
        selected_pts_mask = torch.logical_and(selected_pts_mask, torch.max(self.get_scaling, dim=1).values > self.percent_dense * scene_extent)
        stds = self.get_scaling[selected_pts_mask].repeat(N, 1)
        means = torch.zeros((stds.size(0), 3), device='cuda')
        samples = torch.normal(mean=means, std=stds)
        rots = build_rotation(self._rotation[selected_pts_mask]).repeat(N, 1, 1)
        new_xyz = torch.bmm(rots, samples.unsqueeze(-1)).squeeze(-1) + self.get_xyz[selected_pts_mask].repeat(N, 1)
        new_scaling = self.scaling_inverse_activation(self.get_scaling[selected_pts_mask].repeat(N, 1) / (0.8 * N))
        new_rotation = self._rotation[selected_pts_mask].repeat(N, 1)
        new_features_dc = self._features_dc[selected_pts_mask].repeat(N, 1, 1)
        new_features_rest = self._features_rest[selected_pts_mask].repeat(N, 1, 1)
        new_opacity = self._opacity[selected_pts_mask].repeat(N, 1)
        self.densification_postfix(new_xyz, new_features_dc, new_features_rest, new_opacity, new_scaling, new_rotation)
        prune_filter = torch.cat((selected_pts_mask, torch.zeros(N * selected_pts_mask.sum(), device='cuda', dtype=bool)))
        self.prune_points(prune_filter)

    def densify_and_clone(self, grads, grad_threshold, scene_extent):
        selected_pts_mask = torch.where(torch.norm(grads, dim=-1) >= grad_threshold, True, False)
        selected_pts_mask = torch.logical_and(selected_pts_mask, torch.max(self.get_scaling, dim=1).values <= self.percent_dense * scene_extent)
        new_xyz = self._xyz[selected_pts_mask]
        new_features_dc = self._features_dc[selected_pts_mask]
        new_features_rest = self._features_rest[selected_pts_mask]
        new_opacities = self._opacity[selected_pts_mask]
        new_scaling = self._scaling[selected_pts_mask]
        new_rotation = self._rotation[selected_pts_mask]
        self.densification_postfix(new_xyz, new_features_dc, new_features_rest, new_opacities, new_scaling, new_rotation)

    def densify_and_prune(self, max_grad, min_opacity, extent, max_screen_size):
        grads = self.xyz_gradient_accum / self.denom
        grads[grads.isnan()] = 0.0
        self.densify_and_clone(grads, max_grad, extent)
        self.densify_and_split(grads, max_grad, extent)
        prune_mask = (self.get_opacity < min_opacity).squeeze()
        if max_screen_size:
            big_points_vs = self.max_radii2D > max_screen_size
            big_points_ws = self.get_scaling.max(dim=1).values > 0.1 * extent
            prune_mask = torch.logical_or(torch.logical_or(prune_mask, big_points_vs), big_points_ws)
        self.prune_points(prune_mask)
        torch.cuda.empty_cache()

    def add_densification_stats(self, viewspace_point_tensor, update_filter, width, height):
        grad = viewspace_point_tensor.grad.squeeze(0)
        grad[:, 0] *= width * 0.5
        grad[:, 1] *= height * 0.5
        self.xyz_gradient_accum[update_filter] += torch.norm(grad[update_filter, :2], dim=-1, keepdim=True)
        self.denom[update_filter] += 1

    def get_sky_bg(self, viewpoint_camera):
        return self.sky_model(viewpoint_camera)

def reset_opacity(self):
    opacities_new = inverse_sigmoid(torch.min(self.get_opacity, torch.ones_like(self.get_opacity) * 0.01))
    optimizable_tensors = self.replace_tensor_to_optimizer(opacities_new, 'opacity')
    self._opacity = optimizable_tensors['opacity']

def get_ray_directions(H, W, FoVx, FoVy, c2w):
    """
    Get ray directions for all pixels in the camera coordinate system. Suppose opencv convention

    Args:
        H (int): Height of the image.
        W (int): Width of the image.
        FoVx (float): FoV in the x direction. radians
        FoVy (float): FoV in the y direction. radians
        c2w (torch.Tensor): Camera-to-world transformation matrix of shape (4, 4).

    Returns:
        ray_directions (torch.Tensor): Ray directions in the world coordinate system of shape (H, W, 3).
    """
    c2w = c2w.cuda()
    i, j = torch.meshgrid(torch.arange(W, dtype=torch.float32), torch.arange(H, dtype=torch.float32), indexing='xy')
    directions = torch.stack([(i - W * 0.5) / (W * 0.5) * math.tan(FoVx * 0.5), (j - H * 0.5) / (H * 0.5) * math.tan(FoVy * 0.5), torch.ones_like(i)], dim=-1).cuda()
    directions = directions.unsqueeze(-1)
    ray_directions = torch.einsum('ij,hwjk->hwik', c2w[:3, :3], directions).squeeze(-1)
    ray_directions = ray_directions / torch.norm(ray_directions, dim=-1, keepdim=True)
    return ray_directions

def normalize_activation(x, eps=1e-10):
    norm_factor = torch.sqrt(torch.sum(x ** 2, dim=1, keepdim=True))
    return x / (norm_factor + eps)

class Attention(nn.Module):
    """
    Compute 'Scaled Dot Product Attention
    """

    def forward(self, query, key, value, m):
        scores = torch.matmul(query, key.transpose(-2, -1)) / math.sqrt(query.size(-1))
        scores.masked_fill(m, -1000000000.0)
        p_attn = F.softmax(scores, dim=-1)
        p_val = torch.matmul(p_attn, value)
        return (p_val, p_attn)

def forward(self, query, key, value, m):
    scores = torch.matmul(query, key.transpose(-2, -1)) / math.sqrt(query.size(-1))
    scores.masked_fill(m, -1000000000.0)
    p_attn = F.softmax(scores, dim=-1)
    p_val = torch.matmul(p_attn, value)
    return (p_val, p_attn)

class Attention(nn.Module):
    """
    Compute 'Scaled Dot Product Attention
    """

    def forward(self, query, key, value, m):
        scores = torch.matmul(query, key.transpose(-2, -1)) / math.sqrt(query.size(-1))
        scores.masked_fill(m, -1000000000.0)
        p_attn = F.softmax(scores, dim=-1)
        p_val = torch.matmul(p_attn, value)
        return (p_val, p_attn)

def forward(self, query, key, value, m):
    scores = torch.matmul(query, key.transpose(-2, -1)) / math.sqrt(query.size(-1))
    scores.masked_fill(m, -1000000000.0)
    p_attn = F.softmax(scores, dim=-1)
    p_val = torch.matmul(p_attn, value)
    return (p_val, p_attn)

def spectral_norm(module, name='weight', n_power_iterations=1, eps=1e-12, dim=None):
    """Applies spectral normalization to a parameter in the given module.

    .. math::
        \\mathbf{W}_{SN} = \\dfrac{\\mathbf{W}}{\\sigma(\\mathbf{W})},
        \\sigma(\\mathbf{W}) = \\max_{\\mathbf{h}: \\mathbf{h} \\ne 0} \\dfrac{\\|\\mathbf{W} \\mathbf{h}\\|_2}{\\|\\mathbf{h}\\|_2}

    Spectral normalization stabilizes the training of discriminators (critics)
    in Generative Adversarial Networks (GANs) by rescaling the weight tensor
    with spectral norm :math:`\\sigma` of the weight matrix calculated using
    power iteration method. If the dimension of the weight tensor is greater
    than 2, it is reshaped to 2D in power iteration method to get spectral
    norm. This is implemented via a hook that calculates spectral norm and
    rescales weight before every :meth:`~Module.forward` call.

    See `Spectral Normalization for Generative Adversarial Networks`_ .

    .. _`Spectral Normalization for Generative Adversarial Networks`: https://arxiv.org/abs/1802.05957

    Args:
        module (nn.Module): containing module
        name (str, optional): name of weight parameter
        n_power_iterations (int, optional): number of power iterations to
            calculate spectral norm
        eps (float, optional): epsilon for numerical stability in
            calculating norms
        dim (int, optional): dimension corresponding to number of outputs,
            the default is ``0``, except for modules that are instances of
            ConvTranspose{1,2,3}d, when it is ``1``

    Returns:
        The original module with the spectral norm hook

    Example::

        >>> m = spectral_norm(nn.Linear(20, 40))
        >>> m
        Linear(in_features=20, out_features=40, bias=True)
        >>> m.weight_u.size()
        torch.Size([40])

    """
    if dim is None:
        if isinstance(module, (torch.nn.ConvTranspose1d, torch.nn.ConvTranspose2d, torch.nn.ConvTranspose3d)):
            dim = 1
        else:
            dim = 0
    SpectralNorm.apply(module, name, n_power_iterations, dim, eps)
    return module

class TinyViT(nn.Module):

    def __init__(self, img_size=224, in_chans=3, num_classes=1000, embed_dims=[96, 192, 384, 768], depths=[2, 2, 6, 2], num_heads=[3, 6, 12, 24], window_sizes=[7, 7, 14, 7], mlp_ratio=4.0, drop_rate=0.0, drop_path_rate=0.1, use_checkpoint=False, mbconv_expand_ratio=4.0, local_conv_size=3, layer_lr_decay=1.0):
        super().__init__()
        self.img_size = img_size
        self.num_classes = num_classes
        self.depths = depths
        self.num_layers = len(depths)
        self.mlp_ratio = mlp_ratio
        activation = nn.GELU
        self.patch_embed = PatchEmbed(in_chans=in_chans, embed_dim=embed_dims[0], resolution=img_size, activation=activation)
        patches_resolution = self.patch_embed.patches_resolution
        self.patches_resolution = patches_resolution
        dpr = [x.item() for x in torch.linspace(0, drop_path_rate, sum(depths))]
        self.layers = nn.ModuleList()
        for i_layer in range(self.num_layers):
            kwargs = dict(dim=embed_dims[i_layer], input_resolution=(patches_resolution[0] // 2 ** (i_layer - 1 if i_layer == 3 else i_layer), patches_resolution[1] // 2 ** (i_layer - 1 if i_layer == 3 else i_layer)), depth=depths[i_layer], drop_path=dpr[sum(depths[:i_layer]):sum(depths[:i_layer + 1])], downsample=PatchMerging if i_layer < self.num_layers - 1 else None, use_checkpoint=use_checkpoint, out_dim=embed_dims[min(i_layer + 1, len(embed_dims) - 1)], activation=activation)
            if i_layer == 0:
                layer = ConvLayer(conv_expand_ratio=mbconv_expand_ratio, **kwargs)
            else:
                layer = BasicLayer(num_heads=num_heads[i_layer], window_size=window_sizes[i_layer], mlp_ratio=self.mlp_ratio, drop=drop_rate, local_conv_size=local_conv_size, **kwargs)
            self.layers.append(layer)
        self.norm_head = nn.LayerNorm(embed_dims[-1])
        self.head = nn.Linear(embed_dims[-1], num_classes) if num_classes > 0 else torch.nn.Identity()
        self.apply(self._init_weights)
        self.set_layer_lr_decay(layer_lr_decay)
        self.neck = nn.Sequential(nn.Conv2d(embed_dims[-1], 256, kernel_size=1, bias=False), LayerNorm2d(256), nn.Conv2d(256, 256, kernel_size=3, padding=1, bias=False), LayerNorm2d(256))

    def set_layer_lr_decay(self, layer_lr_decay):
        decay_rate = layer_lr_decay
        depth = sum(self.depths)
        lr_scales = [decay_rate ** (depth - i - 1) for i in range(depth)]

        def _set_lr_scale(m, scale):
            for p in m.parameters():
                p.lr_scale = scale
        self.patch_embed.apply(lambda x: _set_lr_scale(x, lr_scales[0]))
        i = 0
        for layer in self.layers:
            for block in layer.blocks:
                block.apply(lambda x: _set_lr_scale(x, lr_scales[i]))
                i += 1
            if layer.downsample is not None:
                layer.downsample.apply(lambda x: _set_lr_scale(x, lr_scales[i - 1]))
        assert i == depth
        for m in [self.norm_head, self.head]:
            m.apply(lambda x: _set_lr_scale(x, lr_scales[-1]))
        for k, p in self.named_parameters():
            p.param_name = k

        def _check_lr_scale(m):
            for p in m.parameters():
                assert hasattr(p, 'lr_scale'), p.param_name
        self.apply(_check_lr_scale)

    def _init_weights(self, m):
        if isinstance(m, nn.Linear):
            trunc_normal_(m.weight, std=0.02)
            if isinstance(m, nn.Linear) and m.bias is not None:
                nn.init.constant_(m.bias, 0)
        elif isinstance(m, nn.LayerNorm):
            nn.init.constant_(m.bias, 0)
            nn.init.constant_(m.weight, 1.0)

    @torch.jit.ignore
    def no_weight_decay_keywords(self):
        return {'attention_biases'}

    def forward_features(self, x):
        x = self.patch_embed(x)
        x = self.layers[0](x)
        start_i = 1
        for i in range(start_i, len(self.layers)):
            layer = self.layers[i]
            x = layer(x)
        B, _, C = x.size()
        x = x.view(B, 64, 64, C)
        x = x.permute(0, 3, 1, 2)
        x = self.neck(x)
        return x

    def forward(self, x):
        x = self.forward_features(x)
        return x

def set_layer_lr_decay(self, layer_lr_decay):
    decay_rate = layer_lr_decay
    depth = sum(self.depths)
    lr_scales = [decay_rate ** (depth - i - 1) for i in range(depth)]

    def _set_lr_scale(m, scale):
        for p in m.parameters():
            p.lr_scale = scale
    self.patch_embed.apply(lambda x: _set_lr_scale(x, lr_scales[0]))
    i = 0
    for layer in self.layers:
        for block in layer.blocks:
            block.apply(lambda x: _set_lr_scale(x, lr_scales[i]))
            i += 1
        if layer.downsample is not None:
            layer.downsample.apply(lambda x: _set_lr_scale(x, lr_scales[i - 1]))
    assert i == depth
    for m in [self.norm_head, self.head]:
        m.apply(lambda x: _set_lr_scale(x, lr_scales[-1]))
    for k, p in self.named_parameters():
        p.param_name = k

    def _check_lr_scale(m):
        for p in m.parameters():
            assert hasattr(p, 'lr_scale'), p.param_name
    self.apply(_check_lr_scale)

def area_from_rle(rle: Dict[str, Any]) -> int:
    return sum(rle['counts'][1::2])

def calculate_stability_score(masks: torch.Tensor, mask_threshold: float, threshold_offset: float) -> torch.Tensor:
    """
    Computes the stability score for a batch of masks. The stability
    score is the IoU between the binary masks obtained by thresholding
    the predicted mask logits at high and low values.
    """
    intersections = (masks > mask_threshold + threshold_offset).sum(-1, dtype=torch.int16).sum(-1, dtype=torch.int32)
    unions = (masks > mask_threshold - threshold_offset).sum(-1, dtype=torch.int16).sum(-1, dtype=torch.int32)
    return intersections / unions

class Model:

    def __call__(self, img_batch, mask_batch):
        mean = (img_batch * mask_batch[:, None, :, :]).sum(dim=(2, 3)) / mask_batch.sum(dim=(1, 2))[:, None]
        inpainted = mean[:, :, None, None] * (1 - mask_batch[:, None, :, :]) + img_batch * mask_batch[:, None, :, :]
        return inpainted

def __call__(self, img_batch, mask_batch):
    mean = (img_batch * mask_batch[:, None, :, :]).sum(dim=(2, 3)) / mask_batch.sum(dim=(1, 2))[:, None]
    inpainted = mean[:, :, None, None] * (1 - mask_batch[:, None, :, :]) + img_batch * mask_batch[:, None, :, :]
    return inpainted

class PerceptualLoss(nn.Module):

    def __init__(self, normalize_inputs=True):
        super(PerceptualLoss, self).__init__()
        self.normalize_inputs = normalize_inputs
        self.mean_ = IMAGENET_MEAN
        self.std_ = IMAGENET_STD
        vgg = torchvision.models.vgg19(pretrained=True).features
        vgg_avg_pooling = []
        for weights in vgg.parameters():
            weights.requires_grad = False
        for module in vgg.modules():
            if module.__class__.__name__ == 'Sequential':
                continue
            elif module.__class__.__name__ == 'MaxPool2d':
                vgg_avg_pooling.append(nn.AvgPool2d(kernel_size=2, stride=2, padding=0))
            else:
                vgg_avg_pooling.append(module)
        self.vgg = nn.Sequential(*vgg_avg_pooling)

    def do_normalize_inputs(self, x):
        return (x - self.mean_.to(x.device)) / self.std_.to(x.device)

    def partial_losses(self, input, target, mask=None):
        check_and_warn_input_range(target, 0, 1, 'PerceptualLoss target in partial_losses')
        losses = []
        if self.normalize_inputs:
            features_input = self.do_normalize_inputs(input)
            features_target = self.do_normalize_inputs(target)
        else:
            features_input = input
            features_target = target
        for layer in self.vgg[:30]:
            features_input = layer(features_input)
            features_target = layer(features_target)
            if layer.__class__.__name__ == 'ReLU':
                loss = F.mse_loss(features_input, features_target, reduction='none')
                if mask is not None:
                    cur_mask = F.interpolate(mask, size=features_input.shape[-2:], mode='bilinear', align_corners=False)
                    loss = loss * (1 - cur_mask)
                loss = loss.mean(dim=tuple(range(1, len(loss.shape))))
                losses.append(loss)
        return losses

    def forward(self, input, target, mask=None):
        losses = self.partial_losses(input, target, mask=mask)
        return torch.stack(losses).sum(dim=0)

    def get_global_features(self, input):
        check_and_warn_input_range(input, 0, 1, 'PerceptualLoss input in get_global_features')
        if self.normalize_inputs:
            features_input = self.do_normalize_inputs(input)
        else:
            features_input = input
        features_input = self.vgg(features_input)
        return features_input

def forward(self, input, target, mask=None):
    losses = self.partial_losses(input, target, mask=mask)
    return torch.stack(losses).sum(dim=0)

def distribute_values_to_classes(target_class_freq_by_image_mask, values, idx2name):
    assert target_class_freq_by_image_mask.ndim == 2 and target_class_freq_by_image_mask.shape[0] == values.shape[0]
    total_class_freq = target_class_freq_by_image_mask.sum(0)
    distr_values = (target_class_freq_by_image_mask * values[..., None]).sum(0)
    result = distr_values / (total_class_freq + 0.001)
    return {idx2name[i]: val for i, val in enumerate(result) if total_class_freq[i] > 0}

class SSIM(torch.nn.Module):
    """SSIM. Modified from:
    https://github.com/Po-Hsun-Su/pytorch-ssim/blob/master/pytorch_ssim/__init__.py
    """

    def __init__(self, window_size=11, size_average=True):
        super().__init__()
        self.window_size = window_size
        self.size_average = size_average
        self.channel = 1
        self.register_buffer('window', self._create_window(window_size, self.channel))

    def forward(self, img1, img2):
        assert len(img1.shape) == 4
        channel = img1.size()[1]
        if channel == self.channel and self.window.data.type() == img1.data.type():
            window = self.window
        else:
            window = self._create_window(self.window_size, channel)
            window = window.type_as(img1)
            self.window = window
            self.channel = channel
        return self._ssim(img1, img2, window, self.window_size, channel, self.size_average)

    def _gaussian(self, window_size, sigma):
        gauss = torch.Tensor([np.exp(-(x - window_size // 2) ** 2 / float(2 * sigma ** 2)) for x in range(window_size)])
        return gauss / gauss.sum()

    def _create_window(self, window_size, channel):
        _1D_window = self._gaussian(window_size, 1.5).unsqueeze(1)
        _2D_window = _1D_window.mm(_1D_window.t()).float().unsqueeze(0).unsqueeze(0)
        return _2D_window.expand(channel, 1, window_size, window_size).contiguous()

    def _ssim(self, img1, img2, window, window_size, channel, size_average=True):
        mu1 = F.conv2d(img1, window, padding=window_size // 2, groups=channel)
        mu2 = F.conv2d(img2, window, padding=window_size // 2, groups=channel)
        mu1_sq = mu1.pow(2)
        mu2_sq = mu2.pow(2)
        mu1_mu2 = mu1 * mu2
        sigma1_sq = F.conv2d(img1 * img1, window, padding=window_size // 2, groups=channel) - mu1_sq
        sigma2_sq = F.conv2d(img2 * img2, window, padding=window_size // 2, groups=channel) - mu2_sq
        sigma12 = F.conv2d(img1 * img2, window, padding=window_size // 2, groups=channel) - mu1_mu2
        C1 = 0.01 ** 2
        C2 = 0.03 ** 2
        ssim_map = (2 * mu1_mu2 + C1) * (2 * sigma12 + C2) / ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
        if size_average:
            return ssim_map.mean()
        return ssim_map.mean(1).mean(1).mean(1)

    def _load_from_state_dict(self, state_dict, prefix, local_metadata, strict, missing_keys, unexpected_keys, error_msgs):
        return

def forward(self, img1, img2):
    assert len(img1.shape) == 4
    channel = img1.size()[1]
    if channel == self.channel and self.window.data.type() == img1.data.type():
        window = self.window
    else:
        window = self._create_window(self.window_size, channel)
        window = window.type_as(img1)
        self.window = window
        self.channel = channel
    return self._ssim(img1, img2, window, self.window_size, channel, self.size_average)

def _gaussian(self, window_size, sigma):
    gauss = torch.Tensor([np.exp(-(x - window_size // 2) ** 2 / float(2 * sigma ** 2)) for x in range(window_size)])
    return gauss / gauss.sum()

def normalize_tensor(in_feat, eps=1e-10):
    norm_factor = torch.sqrt(torch.sum(in_feat ** 2, dim=1, keepdim=True))
    return in_feat / (norm_factor + eps)

def rgb2lab(input):
    from skimage import color
    return color.rgb2lab(input / 255.0)

def np2tensor(np_obj):
    return torch.Tensor(np_obj[:, :, :, np.newaxis].transpose((3, 2, 0, 1)))

def tensor2tensorlab(image_tensor, to_norm=True, mc_only=False):
    from skimage import color
    img = tensor2im(image_tensor)
    img_lab = color.rgb2lab(img)
    if mc_only:
        img_lab[:, :, 0] = img_lab[:, :, 0] - 50
    if to_norm and (not mc_only):
        img_lab[:, :, 0] = img_lab[:, :, 0] - 50
        img_lab = img_lab / 100.0
    return np2tensor(img_lab)

def tensorlab2tensor(lab_tensor, return_inbnd=False):
    from skimage import color
    import warnings
    warnings.filterwarnings('ignore')
    lab = tensor2np(lab_tensor) * 100.0
    lab[:, :, 0] = lab[:, :, 0] + 50
    rgb_back = 255.0 * np.clip(color.lab2rgb(lab.astype('float')), 0, 1)
    if return_inbnd:
        lab_back = color.rgb2lab(rgb_back.astype('uint8'))
        mask = 1.0 * np.isclose(lab_back, lab, atol=2.0)
        mask = np2tensor(np.prod(mask, axis=2)[:, :, np.newaxis])
        return (im2tensor(rgb_back), mask)
    else:
        return im2tensor(rgb_back)

def im2tensor(image, imtype=np.uint8, cent=1.0, factor=255.0 / 2.0):
    return torch.Tensor((image / factor - cent)[:, :, :, np.newaxis].transpose((3, 2, 0, 1)))

class DistModel(BaseModel):

    def name(self):
        return self.model_name

    def initialize(self, model='net-lin', net='alex', colorspace='Lab', pnet_rand=False, pnet_tune=False, model_path=None, use_gpu=True, printNet=False, spatial=False, is_train=False, lr=0.0001, beta1=0.5, version='0.1'):
        """
        INPUTS
            model - ['net-lin'] for linearly calibrated network
                    ['net'] for off-the-shelf network
                    ['L2'] for L2 distance in Lab colorspace
                    ['SSIM'] for ssim in RGB colorspace
            net - ['squeeze','alex','vgg']
            model_path - if None, will look in weights/[NET_NAME].pth
            colorspace - ['Lab','RGB'] colorspace to use for L2 and SSIM
            use_gpu - bool - whether or not to use a GPU
            printNet - bool - whether or not to print network architecture out
            spatial - bool - whether to output an array containing varying distances across spatial dimensions
            spatial_shape - if given, output spatial shape. if None then spatial shape is determined automatically via spatial_factor (see below).
            spatial_factor - if given, specifies upsampling factor relative to the largest spatial extent of a convolutional layer. if None then resized to size of input images.
            spatial_order - spline order of filter for upsampling in spatial mode, by default 1 (bilinear).
            is_train - bool - [True] for training mode
            lr - float - initial learning rate
            beta1 - float - initial momentum term for adam
            version - 0.1 for latest, 0.0 was original (with a bug)
        """
        BaseModel.initialize(self, use_gpu=use_gpu)
        self.model = model
        self.net = net
        self.is_train = is_train
        self.spatial = spatial
        self.model_name = '%s [%s]' % (model, net)
        if self.model == 'net-lin':
            self.net = PNetLin(pnet_rand=pnet_rand, pnet_tune=pnet_tune, pnet_type=net, use_dropout=True, spatial=spatial, version=version, lpips=True)
            kw = dict(map_location='cpu')
            if model_path is None:
                import inspect
                model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'models', 'lpips_models', f'{net}.pth'))
            if not is_train:
                self.net.load_state_dict(torch.load(model_path, **kw), strict=False)
        elif self.model == 'net':
            self.net = PNetLin(pnet_rand=pnet_rand, pnet_type=net, lpips=False)
        elif self.model in ['L2', 'l2']:
            self.net = L2(use_gpu=use_gpu, colorspace=colorspace)
            self.model_name = 'L2'
        elif self.model in ['DSSIM', 'dssim', 'SSIM', 'ssim']:
            self.net = DSSIM(use_gpu=use_gpu, colorspace=colorspace)
            self.model_name = 'SSIM'
        else:
            raise ValueError('Model [%s] not recognized.' % self.model)
        self.trainable_parameters = list(self.net.parameters())
        if self.is_train:
            self.rankLoss = BCERankingLoss()
            self.trainable_parameters += list(self.rankLoss.net.parameters())
            self.lr = lr
            self.old_lr = lr
            self.optimizer_net = torch.optim.Adam(self.trainable_parameters, lr=lr, betas=(beta1, 0.999))
        else:
            self.net.eval()
        if printNet:
            print('---------- Networks initialized -------------')
            print_network(self.net)
            print('-----------------------------------------------')

    def forward(self, in0, in1, retPerLayer=False):
        """ Function computes the distance between image patches in0 and in1
        INPUTS
            in0, in1 - torch.Tensor object of shape Nx3xXxY - image patch scaled to [-1,1]
        OUTPUT
            computed distances between in0 and in1
        """
        return self.net(in0, in1, retPerLayer=retPerLayer)

    def optimize_parameters(self):
        self.forward_train()
        self.optimizer_net.zero_grad()
        self.backward_train()
        self.optimizer_net.step()
        self.clamp_weights()

    def clamp_weights(self):
        for module in self.net.modules():
            if hasattr(module, 'weight') and module.kernel_size == (1, 1):
                module.weight.data = torch.clamp(module.weight.data, min=0)

    def set_input(self, data):
        self.input_ref = data['ref']
        self.input_p0 = data['p0']
        self.input_p1 = data['p1']
        self.input_judge = data['judge']

    def forward_train(self):
        assert False, "We shoud've not get here when using LPIPS as a metric"
        self.d0 = self(self.var_ref, self.var_p0)
        self.d1 = self(self.var_ref, self.var_p1)
        self.acc_r = self.compute_accuracy(self.d0, self.d1, self.input_judge)
        self.var_judge = Variable(1.0 * self.input_judge).view(self.d0.size())
        self.loss_total = self.rankLoss(self.d0, self.d1, self.var_judge * 2.0 - 1.0)
        return self.loss_total

    def backward_train(self):
        torch.mean(self.loss_total).backward()

    def compute_accuracy(self, d0, d1, judge):
        """ d0, d1 are Variables, judge is a Tensor """
        d1_lt_d0 = (d1 < d0).cpu().data.numpy().flatten()
        judge_per = judge.cpu().numpy().flatten()
        return d1_lt_d0 * judge_per + (1 - d1_lt_d0) * (1 - judge_per)

    def get_current_errors(self):
        retDict = OrderedDict([('loss_total', self.loss_total.data.cpu().numpy()), ('acc_r', self.acc_r)])
        for key in retDict.keys():
            retDict[key] = np.mean(retDict[key])
        return retDict

    def get_current_visuals(self):
        zoom_factor = 256 / self.var_ref.data.size()[2]
        ref_img = tensor2im(self.var_ref.data)
        p0_img = tensor2im(self.var_p0.data)
        p1_img = tensor2im(self.var_p1.data)
        ref_img_vis = zoom(ref_img, [zoom_factor, zoom_factor, 1], order=0)
        p0_img_vis = zoom(p0_img, [zoom_factor, zoom_factor, 1], order=0)
        p1_img_vis = zoom(p1_img, [zoom_factor, zoom_factor, 1], order=0)
        return OrderedDict([('ref', ref_img_vis), ('p0', p0_img_vis), ('p1', p1_img_vis)])

    def save(self, path, label):
        if self.use_gpu:
            self.save_network(self.net.module, path, '', label)
        else:
            self.save_network(self.net, path, '', label)
        self.save_network(self.rankLoss.net, path, 'rank', label)

    def update_learning_rate(self, nepoch_decay):
        lrd = self.lr / nepoch_decay
        lr = self.old_lr - lrd
        for param_group in self.optimizer_net.param_groups:
            param_group['lr'] = lr
        print('update lr [%s] decay: %f -> %f' % (type, self.old_lr, lr))
        self.old_lr = lr

def forward_train(self):
    assert False, "We shoud've not get here when using LPIPS as a metric"
    self.d0 = self(self.var_ref, self.var_p0)
    self.d1 = self(self.var_ref, self.var_p1)
    self.acc_r = self.compute_accuracy(self.d0, self.d1, self.input_judge)
    self.var_judge = Variable(1.0 * self.input_judge).view(self.d0.size())
    self.loss_total = self.rankLoss(self.d0, self.d1, self.var_judge * 2.0 - 1.0)
    return self.loss_total

def backward_train(self):
    torch.mean(self.loss_total).backward()

def get_current_visuals(self):
    zoom_factor = 256 / self.var_ref.data.size()[2]
    ref_img = tensor2im(self.var_ref.data)
    p0_img = tensor2im(self.var_p0.data)
    p1_img = tensor2im(self.var_p1.data)
    ref_img_vis = zoom(ref_img, [zoom_factor, zoom_factor, 1], order=0)
    p0_img_vis = zoom(p0_img, [zoom_factor, zoom_factor, 1], order=0)
    p1_img_vis = zoom(p1_img, [zoom_factor, zoom_factor, 1], order=0)
    return OrderedDict([('ref', ref_img_vis), ('p0', p0_img_vis), ('p1', p1_img_vis)])

class L2(FakeNet):

    def forward(self, in0, in1, retPerLayer=None):
        assert in0.size()[0] == 1
        if self.colorspace == 'RGB':
            N, C, X, Y = in0.size()
            value = torch.mean(torch.mean(torch.mean((in0 - in1) ** 2, dim=1).view(N, 1, X, Y), dim=2).view(N, 1, 1, Y), dim=3).view(N)
            return value
        elif self.colorspace == 'Lab':
            value = l2(tensor2np(tensor2tensorlab(in0.data, to_norm=False)), tensor2np(tensor2tensorlab(in1.data, to_norm=False)), range=100.0).astype('float')
            ret_var = Variable(torch.Tensor((value,)))
            return ret_var

def forward(self, in0, in1, retPerLayer=None):
    assert in0.size()[0] == 1
    if self.colorspace == 'RGB':
        N, C, X, Y = in0.size()
        value = torch.mean(torch.mean(torch.mean((in0 - in1) ** 2, dim=1).view(N, 1, X, Y), dim=2).view(N, 1, 1, Y), dim=3).view(N)
        return value
    elif self.colorspace == 'Lab':
        value = l2(tensor2np(tensor2tensorlab(in0.data, to_norm=False)), tensor2np(tensor2tensorlab(in1.data, to_norm=False)), range=100.0).astype('float')
        ret_var = Variable(torch.Tensor((value,)))
        return ret_var

class DSSIM(FakeNet):

    def forward(self, in0, in1, retPerLayer=None):
        assert in0.size()[0] == 1
        if self.colorspace == 'RGB':
            value = dssim(1.0 * tensor2im(in0.data), 1.0 * tensor2im(in1.data), range=255.0).astype('float')
        elif self.colorspace == 'Lab':
            value = dssim(tensor2np(tensor2tensorlab(in0.data, to_norm=False)), tensor2np(tensor2tensorlab(in1.data, to_norm=False)), range=100.0).astype('float')
        ret_var = Variable(torch.Tensor((value,)))
        return ret_var

def forward(self, in0, in1, retPerLayer=None):
    assert in0.size()[0] == 1
    if self.colorspace == 'RGB':
        value = dssim(1.0 * tensor2im(in0.data), 1.0 * tensor2im(in1.data), range=255.0).astype('float')
    elif self.colorspace == 'Lab':
        value = dssim(tensor2np(tensor2tensorlab(in0.data, to_norm=False)), tensor2np(tensor2tensorlab(in1.data, to_norm=False)), range=100.0).astype('float')
    ret_var = Variable(torch.Tensor((value,)))
    return ret_var

class ObjectMask:

    def __init__(self, mask):
        self.height, self.width = mask.shape
        (self.up, self.down), (self.left, self.right) = self._get_limits(mask)
        self.mask = mask[self.up:self.down, self.left:self.right].copy()

    @staticmethod
    def _get_limits(mask):

        def indicator_limits(indicator):
            lower = indicator.argmax()
            upper = len(indicator) - indicator[::-1].argmax()
            return (lower, upper)
        vertical_indicator = mask.any(axis=1)
        vertical_limits = indicator_limits(vertical_indicator)
        horizontal_indicator = mask.any(axis=0)
        horizontal_limits = indicator_limits(horizontal_indicator)
        return (vertical_limits, horizontal_limits)

    def _clean(self):
        self.up, self.down, self.left, self.right = (0, 0, 0, 0)
        self.mask = np.empty((0, 0))

    def horizontal_flip(self, inplace=False):
        if not inplace:
            flipped = deepcopy(self)
            return flipped.horizontal_flip(inplace=True)
        self.mask = self.mask[:, ::-1]
        return self

    def vertical_flip(self, inplace=False):
        if not inplace:
            flipped = deepcopy(self)
            return flipped.vertical_flip(inplace=True)
        self.mask = self.mask[::-1, :]
        return self

    def image_center(self):
        y_center = self.up + (self.down - self.up) / 2
        x_center = self.left + (self.right - self.left) / 2
        return (y_center, x_center)

    def rescale(self, scaling_factor, inplace=False):
        if not inplace:
            scaled = deepcopy(self)
            return scaled.rescale(scaling_factor, inplace=True)
        scaled_mask = rescale(self.mask.astype(float), scaling_factor, order=0) > 0.5
        (up, down), (left, right) = self._get_limits(scaled_mask)
        self.mask = scaled_mask[up:down, left:right]
        y_center, x_center = self.image_center()
        mask_height, mask_width = self.mask.shape
        self.up = int(round(y_center - mask_height / 2))
        self.down = self.up + mask_height
        self.left = int(round(x_center - mask_width / 2))
        self.right = self.left + mask_width
        return self

    def crop_to_canvas(self, vertical=True, horizontal=True, inplace=False):
        if not inplace:
            cropped = deepcopy(self)
            cropped.crop_to_canvas(vertical=vertical, horizontal=horizontal, inplace=True)
            return cropped
        if vertical:
            if self.up >= self.height or self.down <= 0:
                self._clean()
            else:
                cut_up, cut_down = (max(-self.up, 0), max(self.down - self.height, 0))
                if cut_up != 0:
                    self.mask = self.mask[cut_up:]
                    self.up = 0
                if cut_down != 0:
                    self.mask = self.mask[:-cut_down]
                    self.down = self.height
        if horizontal:
            if self.left >= self.width or self.right <= 0:
                self._clean()
            else:
                cut_left, cut_right = (max(-self.left, 0), max(self.right - self.width, 0))
                if cut_left != 0:
                    self.mask = self.mask[:, cut_left:]
                    self.left = 0
                if cut_right != 0:
                    self.mask = self.mask[:, :-cut_right]
                    self.right = self.width
        return self

    def restore_full_mask(self, allow_crop=False):
        cropped = self.crop_to_canvas(inplace=allow_crop)
        mask = np.zeros((cropped.height, cropped.width), dtype=bool)
        mask[cropped.up:cropped.down, cropped.left:cropped.right] = cropped.mask
        return mask

    def shift(self, vertical=0, horizontal=0, inplace=False):
        if not inplace:
            shifted = deepcopy(self)
            return shifted.shift(vertical=vertical, horizontal=horizontal, inplace=True)
        self.up += vertical
        self.down += vertical
        self.left += horizontal
        self.right += horizontal
        return self

    def area(self):
        return self.mask.sum()

def area(self):
    return self.mask.sum()

class SegmentationMask:

    def __init__(self, confidence_threshold=0.5, rigidness_mode=RigidnessMode.rigid, max_object_area=0.3, min_mask_area=0.02, downsample_levels=6, num_variants_per_mask=4, max_mask_intersection=0.5, max_foreground_coverage=0.5, max_foreground_intersection=0.5, max_hidden_area=0.2, max_scale_change=0.25, horizontal_flip=True, max_vertical_shift=0.1, position_shuffle=True):
        """
        :param confidence_threshold: float; threshold for confidence of the panoptic segmentator to allow for
        the instance.
        :param rigidness_mode: RigidnessMode object
            when soft, checks intersection only with the object from which the mask_object was produced
            when rigid, checks intersection with any foreground class object
        :param max_object_area: float; allowed upper bound for to be considered as mask_object.
        :param min_mask_area: float; lower bound for mask to be considered valid
        :param downsample_levels: int; defines width of the resized segmentation to obtain shifted masks;
        :param num_variants_per_mask: int; maximal number of the masks for the same object;
        :param max_mask_intersection: float; maximum allowed area fraction of intersection for 2 masks
        produced by horizontal shift of the same mask_object; higher value -> more diversity
        :param max_foreground_coverage: float; maximum allowed area fraction of intersection for foreground object to be
        covered by mask; lower value -> less the objects are covered
        :param max_foreground_intersection: float; maximum allowed area of intersection for the mask with foreground
        object; lower value -> mask is more on the background than on the objects
        :param max_hidden_area: upper bound on part of the object hidden by shifting object outside the screen area;
        :param max_scale_change: allowed scale change for the mask_object;
        :param horizontal_flip: if horizontal flips are allowed;
        :param max_vertical_shift: amount of vertical movement allowed;
        :param position_shuffle: shuffle
        """
        assert DETECTRON_INSTALLED, 'Cannot use SegmentationMask without detectron2'
        self.cfg = get_cfg()
        self.cfg.merge_from_file(model_zoo.get_config_file('COCO-PanopticSegmentation/panoptic_fpn_R_101_3x.yaml'))
        self.cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url('COCO-PanopticSegmentation/panoptic_fpn_R_101_3x.yaml')
        self.cfg.MODEL.PANOPTIC_FPN.COMBINE.INSTANCES_CONFIDENCE_THRESH = confidence_threshold
        self.predictor = DefaultPredictor(self.cfg)
        self.rigidness_mode = RigidnessMode(rigidness_mode)
        self.max_object_area = max_object_area
        self.min_mask_area = min_mask_area
        self.downsample_levels = downsample_levels
        self.num_variants_per_mask = num_variants_per_mask
        self.max_mask_intersection = max_mask_intersection
        self.max_foreground_coverage = max_foreground_coverage
        self.max_foreground_intersection = max_foreground_intersection
        self.max_hidden_area = max_hidden_area
        self.position_shuffle = position_shuffle
        self.max_scale_change = max_scale_change
        self.horizontal_flip = horizontal_flip
        self.max_vertical_shift = max_vertical_shift

    def get_segmentation(self, img):
        im = img_as_ubyte(img)
        panoptic_seg, segment_info = self.predictor(im)['panoptic_seg']
        return (panoptic_seg, segment_info)

    @staticmethod
    def _is_power_of_two(n):
        return n != 0 and n & n - 1 == 0

    def identify_candidates(self, panoptic_seg, segments_info):
        potential_mask_ids = []
        for segment in segments_info:
            if not segment['isthing']:
                continue
            mask = (panoptic_seg == segment['id']).int().detach().cpu().numpy()
            area = mask.sum().item() / np.prod(panoptic_seg.shape)
            if area >= self.max_object_area:
                continue
            potential_mask_ids.append(segment['id'])
        return potential_mask_ids

    def downsample_mask(self, mask):
        height, width = mask.shape
        if not (self._is_power_of_two(height) and self._is_power_of_two(width)):
            raise ValueError('Image sides are not power of 2.')
        num_iterations = width.bit_length() - 1 - self.downsample_levels
        if num_iterations < 0:
            raise ValueError(f'Width is lower than 2^{self.downsample_levels}.')
        if height.bit_length() - 1 < num_iterations:
            raise ValueError('Height is too low to perform downsampling')
        downsampled = mask
        for _ in range(num_iterations):
            downsampled = zero_corrected_countless(downsampled)
        return downsampled

    def _augmentation_params(self):
        scaling_factor = np.random.uniform(1 - self.max_scale_change, 1 + self.max_scale_change)
        if self.horizontal_flip:
            horizontal_flip = bool(np.random.choice(2))
        else:
            horizontal_flip = False
        vertical_shift = np.random.uniform(-self.max_vertical_shift, self.max_vertical_shift)
        return {'scaling_factor': scaling_factor, 'horizontal_flip': horizontal_flip, 'vertical_shift': vertical_shift}

    def _get_intersection(self, mask_array, mask_object):
        intersection = mask_array[mask_object.up:mask_object.down, mask_object.left:mask_object.right] & mask_object.mask
        return intersection

    def _check_masks_intersection(self, aug_mask, total_mask_area, prev_masks):
        for existing_mask in prev_masks:
            intersection_area = self._get_intersection(existing_mask, aug_mask).sum()
            intersection_existing = intersection_area / existing_mask.sum()
            intersection_current = 1 - (aug_mask.area() - intersection_area) / total_mask_area
            if intersection_existing > self.max_mask_intersection or intersection_current > self.max_mask_intersection:
                return False
        return True

    def _check_foreground_intersection(self, aug_mask, foreground):
        for existing_mask in foreground:
            intersection_area = self._get_intersection(existing_mask, aug_mask).sum()
            intersection_existing = intersection_area / existing_mask.sum()
            if intersection_existing > self.max_foreground_coverage:
                return False
            intersection_mask = intersection_area / aug_mask.area()
            if intersection_mask > self.max_foreground_intersection:
                return False
        return True

    def _move_mask(self, mask, foreground):
        orig_mask = ObjectMask(mask)
        chosen_masks = []
        chosen_parameters = []
        scaling_factor_lower_bound = 0.0
        for var_idx in range(self.num_variants_per_mask):
            augmentation_params = self._augmentation_params()
            augmentation_params['scaling_factor'] = min([augmentation_params['scaling_factor'], 2 * min(orig_mask.up, orig_mask.height - orig_mask.down) / orig_mask.height + 1.0, 2 * min(orig_mask.left, orig_mask.width - orig_mask.right) / orig_mask.width + 1.0])
            augmentation_params['scaling_factor'] = max([augmentation_params['scaling_factor'], scaling_factor_lower_bound])
            aug_mask = deepcopy(orig_mask)
            aug_mask.rescale(augmentation_params['scaling_factor'], inplace=True)
            if augmentation_params['horizontal_flip']:
                aug_mask.horizontal_flip(inplace=True)
            total_aug_area = aug_mask.area()
            if total_aug_area == 0:
                scaling_factor_lower_bound = 1.0
                continue
            vertical_area = aug_mask.mask.sum(axis=1) / total_aug_area
            max_hidden_up = np.searchsorted(vertical_area.cumsum(), self.max_hidden_area)
            max_hidden_down = np.searchsorted(vertical_area[::-1].cumsum(), self.max_hidden_area)
            augmentation_params['vertical_shift'] = np.clip(augmentation_params['vertical_shift'], -(aug_mask.up + max_hidden_up) / aug_mask.height, (aug_mask.height - aug_mask.down + max_hidden_down) / aug_mask.height)
            vertical_shift = int(round(aug_mask.height * augmentation_params['vertical_shift']))
            aug_mask.shift(vertical=vertical_shift, inplace=True)
            aug_mask.crop_to_canvas(vertical=True, horizontal=False, inplace=True)
            max_hidden_area = self.max_hidden_area - (1 - aug_mask.area() / total_aug_area)
            horizontal_area = aug_mask.mask.sum(axis=0) / total_aug_area
            max_hidden_left = np.searchsorted(horizontal_area.cumsum(), max_hidden_area)
            max_hidden_right = np.searchsorted(horizontal_area[::-1].cumsum(), max_hidden_area)
            allowed_shifts = np.arange(-max_hidden_left, aug_mask.width - (aug_mask.right - aug_mask.left) + max_hidden_right + 1)
            allowed_shifts = -(aug_mask.left - allowed_shifts)
            if self.position_shuffle:
                np.random.shuffle(allowed_shifts)
            mask_is_found = False
            for horizontal_shift in allowed_shifts:
                aug_mask_left = deepcopy(aug_mask)
                aug_mask_left.shift(horizontal=horizontal_shift, inplace=True)
                aug_mask_left.crop_to_canvas(inplace=True)
                prev_masks = [mask] + chosen_masks
                is_mask_suitable = self._check_masks_intersection(aug_mask_left, total_aug_area, prev_masks) & self._check_foreground_intersection(aug_mask_left, foreground)
                if is_mask_suitable:
                    aug_draw = aug_mask_left.restore_full_mask()
                    chosen_masks.append(aug_draw)
                    augmentation_params['horizontal_shift'] = horizontal_shift / aug_mask_left.width
                    chosen_parameters.append(augmentation_params)
                    mask_is_found = True
                    break
            if not mask_is_found:
                break
        return chosen_parameters

    def _prepare_mask(self, mask):
        height, width = mask.shape
        target_width = width if self._is_power_of_two(width) else 1 << width.bit_length()
        target_height = height if self._is_power_of_two(height) else 1 << height.bit_length()
        return resize(mask.astype('float32'), (target_height, target_width), order=0, mode='edge').round().astype('int32')

    def get_masks(self, im, return_panoptic=False):
        panoptic_seg, segments_info = self.get_segmentation(im)
        potential_mask_ids = self.identify_candidates(panoptic_seg, segments_info)
        panoptic_seg_scaled = self._prepare_mask(panoptic_seg.detach().cpu().numpy())
        downsampled = self.downsample_mask(panoptic_seg_scaled)
        scene_objects = []
        for segment in segments_info:
            if not segment['isthing']:
                continue
            mask = downsampled == segment['id']
            if not np.any(mask):
                continue
            scene_objects.append(mask)
        mask_set = []
        for mask_id in potential_mask_ids:
            mask = downsampled == mask_id
            if not np.any(mask):
                continue
            if self.rigidness_mode is RigidnessMode.soft:
                foreground = [mask]
            elif self.rigidness_mode is RigidnessMode.rigid:
                foreground = scene_objects
            else:
                raise ValueError(f'Unexpected rigidness_mode: {rigidness_mode}')
            masks_params = self._move_mask(mask, foreground)
            full_mask = ObjectMask((panoptic_seg == mask_id).detach().cpu().numpy())
            for params in masks_params:
                aug_mask = deepcopy(full_mask)
                aug_mask.rescale(params['scaling_factor'], inplace=True)
                if params['horizontal_flip']:
                    aug_mask.horizontal_flip(inplace=True)
                vertical_shift = int(round(aug_mask.height * params['vertical_shift']))
                horizontal_shift = int(round(aug_mask.width * params['horizontal_shift']))
                aug_mask.shift(vertical=vertical_shift, horizontal=horizontal_shift, inplace=True)
                aug_mask = aug_mask.restore_full_mask().astype('uint8')
                if aug_mask.mean() <= self.min_mask_area:
                    continue
                mask_set.append(aug_mask)
        if return_panoptic:
            return (mask_set, panoptic_seg.detach().cpu().numpy())
        else:
            return mask_set

def _check_masks_intersection(self, aug_mask, total_mask_area, prev_masks):
    for existing_mask in prev_masks:
        intersection_area = self._get_intersection(existing_mask, aug_mask).sum()
        intersection_existing = intersection_area / existing_mask.sum()
        intersection_current = 1 - (aug_mask.area() - intersection_area) / total_mask_area
        if intersection_existing > self.max_mask_intersection or intersection_current > self.max_mask_intersection:
            return False
    return True

def _check_foreground_intersection(self, aug_mask, foreground):
    for existing_mask in foreground:
        intersection_area = self._get_intersection(existing_mask, aug_mask).sum()
        intersection_existing = intersection_area / existing_mask.sum()
        if intersection_existing > self.max_foreground_coverage:
            return False
        intersection_mask = intersection_area / aug_mask.area()
        if intersection_mask > self.max_foreground_intersection:
            return False
    return True

def ndzoom(array):
    if len(array.shape) == 3:
        ratio = (1 / 2.0, 1 / 2.0, 1.0)
    else:
        ratio = (1 / 2.0, 1 / 2.0)
    return ndimage.interpolation.zoom(array, ratio, order=1)

def _sum_ft(tensor):
    """sum over the first and last dimention"""
    return tensor.sum(dim=0).sum(dim=-1)

class _SynchronizedBatchNorm(_BatchNorm):

    def __init__(self, num_features, eps=1e-05, momentum=0.001, affine=True):
        super(_SynchronizedBatchNorm, self).__init__(num_features, eps=eps, momentum=momentum, affine=affine)
        self._sync_master = SyncMaster(self._data_parallel_master)
        self._is_parallel = False
        self._parallel_id = None
        self._slave_pipe = None
        self._moving_average_fraction = 1.0 - momentum
        self.register_buffer('_tmp_running_mean', torch.zeros(self.num_features))
        self.register_buffer('_tmp_running_var', torch.ones(self.num_features))
        self.register_buffer('_running_iter', torch.ones(1))
        self._tmp_running_mean = self.running_mean.clone() * self._running_iter
        self._tmp_running_var = self.running_var.clone() * self._running_iter

    def forward(self, input):
        if not (self._is_parallel and self.training):
            return F.batch_norm(input, self.running_mean, self.running_var, self.weight, self.bias, self.training, self.momentum, self.eps)
        input_shape = input.size()
        input = input.view(input.size(0), self.num_features, -1)
        sum_size = input.size(0) * input.size(2)
        input_sum = _sum_ft(input)
        input_ssum = _sum_ft(input ** 2)
        if self._parallel_id == 0:
            mean, inv_std = self._sync_master.run_master(_ChildMessage(input_sum, input_ssum, sum_size))
        else:
            mean, inv_std = self._slave_pipe.run_slave(_ChildMessage(input_sum, input_ssum, sum_size))
        if self.affine:
            output = (input - _unsqueeze_ft(mean)) * _unsqueeze_ft(inv_std * self.weight) + _unsqueeze_ft(self.bias)
        else:
            output = (input - _unsqueeze_ft(mean)) * _unsqueeze_ft(inv_std)
        return output.view(input_shape)

    def __data_parallel_replicate__(self, ctx, copy_id):
        self._is_parallel = True
        self._parallel_id = copy_id
        if self._parallel_id == 0:
            ctx.sync_master = self._sync_master
        else:
            self._slave_pipe = ctx.sync_master.register_slave(copy_id)

    def _data_parallel_master(self, intermediates):
        """Reduce the sum and square-sum, compute the statistics, and broadcast it."""
        intermediates = sorted(intermediates, key=lambda i: i[1].sum.get_device())
        to_reduce = [i[1][:2] for i in intermediates]
        to_reduce = [j for i in to_reduce for j in i]
        target_gpus = [i[1].sum.get_device() for i in intermediates]
        sum_size = sum([i[1].sum_size for i in intermediates])
        sum_, ssum = ReduceAddCoalesced.apply(target_gpus[0], 2, *to_reduce)
        mean, inv_std = self._compute_mean_std(sum_, ssum, sum_size)
        broadcasted = Broadcast.apply(target_gpus, mean, inv_std)
        outputs = []
        for i, rec in enumerate(intermediates):
            outputs.append((rec[0], _MasterMessage(*broadcasted[i * 2:i * 2 + 2])))
        return outputs

    def _add_weighted(self, dest, delta, alpha=1, beta=1, bias=0):
        """return *dest* by `dest := dest*alpha + delta*beta + bias`"""
        return dest * alpha + delta * beta + bias

    def _compute_mean_std(self, sum_, ssum, size):
        """Compute the mean and standard-deviation with sum and square-sum. This method
        also maintains the moving average on the master device."""
        assert size > 1, 'BatchNorm computes unbiased standard-deviation, which requires size > 1.'
        mean = sum_ / size
        sumvar = ssum - sum_ * mean
        unbias_var = sumvar / (size - 1)
        bias_var = sumvar / size
        self._tmp_running_mean = self._add_weighted(self._tmp_running_mean, mean.data, alpha=self._moving_average_fraction)
        self._tmp_running_var = self._add_weighted(self._tmp_running_var, unbias_var.data, alpha=self._moving_average_fraction)
        self._running_iter = self._add_weighted(self._running_iter, 1, alpha=self._moving_average_fraction)
        self.running_mean = self._tmp_running_mean / self._running_iter
        self.running_var = self._tmp_running_var / self._running_iter
        return (mean, bias_var.clamp(self.eps) ** (-0.5))

def forward(self, input):
    if not (self._is_parallel and self.training):
        return F.batch_norm(input, self.running_mean, self.running_var, self.weight, self.bias, self.training, self.momentum, self.eps)
    input_shape = input.size()
    input = input.view(input.size(0), self.num_features, -1)
    sum_size = input.size(0) * input.size(2)
    input_sum = _sum_ft(input)
    input_ssum = _sum_ft(input ** 2)
    if self._parallel_id == 0:
        mean, inv_std = self._sync_master.run_master(_ChildMessage(input_sum, input_ssum, sum_size))
    else:
        mean, inv_std = self._slave_pipe.run_slave(_ChildMessage(input_sum, input_ssum, sum_size))
    if self.affine:
        output = (input - _unsqueeze_ft(mean)) * _unsqueeze_ft(inv_std * self.weight) + _unsqueeze_ft(self.bias)
    else:
        output = (input - _unsqueeze_ft(mean)) * _unsqueeze_ft(inv_std)
    return output.view(input_shape)

def _data_parallel_master(self, intermediates):
    """Reduce the sum and square-sum, compute the statistics, and broadcast it."""
    intermediates = sorted(intermediates, key=lambda i: i[1].sum.get_device())
    to_reduce = [i[1][:2] for i in intermediates]
    to_reduce = [j for i in to_reduce for j in i]
    target_gpus = [i[1].sum.get_device() for i in intermediates]
    sum_size = sum([i[1].sum_size for i in intermediates])
    sum_, ssum = ReduceAddCoalesced.apply(target_gpus[0], 2, *to_reduce)
    mean, inv_std = self._compute_mean_std(sum_, ssum, sum_size)
    broadcasted = Broadcast.apply(target_gpus, mean, inv_std)
    outputs = []
    for i, rec in enumerate(intermediates):
        outputs.append((rec[0], _MasterMessage(*broadcasted[i * 2:i * 2 + 2])))
    return outputs

def handy_var(a, unbias=True):
    n = a.size(0)
    asum = a.sum(dim=0)
    as_sum = (a ** 2).sum(dim=0)
    sumvar = as_sum - asum * asum / n
    if unbias:
        return sumvar / (n - 1)
    else:
        return sumvar / n

class SyncTestCase(TorchTestCase):

    def _syncParameters(self, bn1, bn2):
        bn1.reset_parameters()
        bn2.reset_parameters()
        if bn1.affine and bn2.affine:
            bn2.weight.data.copy_(bn1.weight.data)
            bn2.bias.data.copy_(bn1.bias.data)

    def _checkBatchNormResult(self, bn1, bn2, input, is_train, cuda=False):
        """Check the forward and backward for the customized batch normalization."""
        bn1.train(mode=is_train)
        bn2.train(mode=is_train)
        if cuda:
            input = input.cuda()
        self._syncParameters(_find_bn(bn1), _find_bn(bn2))
        input1 = Variable(input, requires_grad=True)
        output1 = bn1(input1)
        output1.sum().backward()
        input2 = Variable(input, requires_grad=True)
        output2 = bn2(input2)
        output2.sum().backward()
        self.assertTensorClose(input1.data, input2.data)
        self.assertTensorClose(output1.data, output2.data)
        self.assertTensorClose(input1.grad, input2.grad)
        self.assertTensorClose(_find_bn(bn1).running_mean, _find_bn(bn2).running_mean)
        self.assertTensorClose(_find_bn(bn1).running_var, _find_bn(bn2).running_var)

    def testSyncBatchNormNormalTrain(self):
        bn = nn.BatchNorm1d(10)
        sync_bn = SynchronizedBatchNorm1d(10)
        self._checkBatchNormResult(bn, sync_bn, torch.rand(16, 10), True)

    def testSyncBatchNormNormalEval(self):
        bn = nn.BatchNorm1d(10)
        sync_bn = SynchronizedBatchNorm1d(10)
        self._checkBatchNormResult(bn, sync_bn, torch.rand(16, 10), False)

    def testSyncBatchNormSyncTrain(self):
        bn = nn.BatchNorm1d(10, eps=1e-05, affine=False)
        sync_bn = SynchronizedBatchNorm1d(10, eps=1e-05, affine=False)
        sync_bn = DataParallelWithCallback(sync_bn, device_ids=[0, 1])
        bn.cuda()
        sync_bn.cuda()
        self._checkBatchNormResult(bn, sync_bn, torch.rand(16, 10), True, cuda=True)

    def testSyncBatchNormSyncEval(self):
        bn = nn.BatchNorm1d(10, eps=1e-05, affine=False)
        sync_bn = SynchronizedBatchNorm1d(10, eps=1e-05, affine=False)
        sync_bn = DataParallelWithCallback(sync_bn, device_ids=[0, 1])
        bn.cuda()
        sync_bn.cuda()
        self._checkBatchNormResult(bn, sync_bn, torch.rand(16, 10), False, cuda=True)

    def testSyncBatchNorm2DSyncTrain(self):
        bn = nn.BatchNorm2d(10)
        sync_bn = SynchronizedBatchNorm2d(10)
        sync_bn = DataParallelWithCallback(sync_bn, device_ids=[0, 1])
        bn.cuda()
        sync_bn.cuda()
        self._checkBatchNormResult(bn, sync_bn, torch.rand(16, 10, 16, 16), True, cuda=True)

def _checkBatchNormResult(self, bn1, bn2, input, is_train, cuda=False):
    """Check the forward and backward for the customized batch normalization."""
    bn1.train(mode=is_train)
    bn2.train(mode=is_train)
    if cuda:
        input = input.cuda()
    self._syncParameters(_find_bn(bn1), _find_bn(bn2))
    input1 = Variable(input, requires_grad=True)
    output1 = bn1(input1)
    output1.sum().backward()
    input2 = Variable(input, requires_grad=True)
    output2 = bn2(input2)
    output2.sum().backward()
    self.assertTensorClose(input1.data, input2.data)
    self.assertTensorClose(output1.data, output2.data)
    self.assertTensorClose(input1.grad, input2.grad)
    self.assertTensorClose(_find_bn(bn1).running_mean, _find_bn(bn2).running_mean)
    self.assertTensorClose(_find_bn(bn1).running_var, _find_bn(bn2).running_var)

def handy_var(a, unbias=True):
    n = a.size(0)
    asum = a.sum(dim=0)
    as_sum = (a ** 2).sum(dim=0)
    sumvar = as_sum - asum * asum / n
    if unbias:
        return sumvar / (n - 1)
    else:
        return sumvar / n

class NumericTestCase(TorchTestCase):

    def testNumericBatchNorm(self):
        a = torch.rand(16, 10)
        bn = nn.BatchNorm2d(10, momentum=1, eps=1e-05, affine=False)
        bn.train()
        a_var1 = Variable(a, requires_grad=True)
        b_var1 = bn(a_var1)
        loss1 = b_var1.sum()
        loss1.backward()
        a_var2 = Variable(a, requires_grad=True)
        a_mean2 = a_var2.mean(dim=0, keepdim=True)
        a_std2 = torch.sqrt(handy_var(a_var2, unbias=False).clamp(min=1e-05))
        b_var2 = (a_var2 - a_mean2) / a_std2
        loss2 = b_var2.sum()
        loss2.backward()
        self.assertTensorClose(bn.running_mean, a.mean(dim=0))
        self.assertTensorClose(bn.running_var, handy_var(a))
        self.assertTensorClose(a_var1.data, a_var2.data)
        self.assertTensorClose(b_var1.data, b_var2.data)
        self.assertTensorClose(a_var1.grad, a_var2.grad)

def testNumericBatchNorm(self):
    a = torch.rand(16, 10)
    bn = nn.BatchNorm2d(10, momentum=1, eps=1e-05, affine=False)
    bn.train()
    a_var1 = Variable(a, requires_grad=True)
    b_var1 = bn(a_var1)
    loss1 = b_var1.sum()
    loss1.backward()
    a_var2 = Variable(a, requires_grad=True)
    a_mean2 = a_var2.mean(dim=0, keepdim=True)
    a_std2 = torch.sqrt(handy_var(a_var2, unbias=False).clamp(min=1e-05))
    b_var2 = (a_var2 - a_mean2) / a_std2
    loss2 = b_var2.sum()
    loss2.backward()
    self.assertTensorClose(bn.running_mean, a.mean(dim=0))
    self.assertTensorClose(bn.running_var, handy_var(a))
    self.assertTensorClose(a_var1.data, a_var2.data)
    self.assertTensorClose(b_var1.data, b_var2.data)
    self.assertTensorClose(a_var1.grad, a_var2.grad)

class PerceptualLoss(nn.Module):

    def __init__(self, normalize_inputs=True):
        super(PerceptualLoss, self).__init__()
        self.normalize_inputs = normalize_inputs
        self.mean_ = IMAGENET_MEAN
        self.std_ = IMAGENET_STD
        vgg = torchvision.models.vgg19(pretrained=True).features
        vgg_avg_pooling = []
        for weights in vgg.parameters():
            weights.requires_grad = False
        for module in vgg.modules():
            if module.__class__.__name__ == 'Sequential':
                continue
            elif module.__class__.__name__ == 'MaxPool2d':
                vgg_avg_pooling.append(nn.AvgPool2d(kernel_size=2, stride=2, padding=0))
            else:
                vgg_avg_pooling.append(module)
        self.vgg = nn.Sequential(*vgg_avg_pooling)

    def do_normalize_inputs(self, x):
        return (x - self.mean_.to(x.device)) / self.std_.to(x.device)

    def partial_losses(self, input, target, mask=None):
        check_and_warn_input_range(target, 0, 1, 'PerceptualLoss target in partial_losses')
        losses = []
        if self.normalize_inputs:
            features_input = self.do_normalize_inputs(input)
            features_target = self.do_normalize_inputs(target)
        else:
            features_input = input
            features_target = target
        for layer in self.vgg[:30]:
            features_input = layer(features_input)
            features_target = layer(features_target)
            if layer.__class__.__name__ == 'ReLU':
                loss = F.mse_loss(features_input, features_target, reduction='none')
                if mask is not None:
                    cur_mask = F.interpolate(mask, size=features_input.shape[-2:], mode='bilinear', align_corners=False)
                    loss = loss * (1 - cur_mask)
                loss = loss.mean(dim=tuple(range(1, len(loss.shape))))
                losses.append(loss)
        return losses

    def forward(self, input, target, mask=None):
        losses = self.partial_losses(input, target, mask=mask)
        return torch.stack(losses).sum(dim=0)

    def get_global_features(self, input):
        check_and_warn_input_range(input, 0, 1, 'PerceptualLoss input in get_global_features')
        if self.normalize_inputs:
            features_input = self.do_normalize_inputs(input)
        else:
            features_input = input
        features_input = self.vgg(features_input)
        return features_input

def forward(self, input, target, mask=None):
    losses = self.partial_losses(input, target, mask=mask)
    return torch.stack(losses).sum(dim=0)

class MixedMaskGenerator:

    def __init__(self, irregular_proba=1 / 3, irregular_kwargs=None, box_proba=1 / 3, box_kwargs=None, segm_proba=1 / 3, segm_kwargs=None, squares_proba=0, squares_kwargs=None, superres_proba=0, superres_kwargs=None, outpainting_proba=0, outpainting_kwargs=None, invert_proba=0):
        self.probas = []
        self.gens = []
        if irregular_proba > 0:
            self.probas.append(irregular_proba)
            if irregular_kwargs is None:
                irregular_kwargs = {}
            else:
                irregular_kwargs = dict(irregular_kwargs)
            irregular_kwargs['draw_method'] = DrawMethod.LINE
            self.gens.append(RandomIrregularMaskGenerator(**irregular_kwargs))
        if box_proba > 0:
            self.probas.append(box_proba)
            if box_kwargs is None:
                box_kwargs = {}
            self.gens.append(RandomRectangleMaskGenerator(**box_kwargs))
        if segm_proba > 0:
            self.probas.append(segm_proba)
            if segm_kwargs is None:
                segm_kwargs = {}
            self.gens.append(RandomSegmentationMaskGenerator(**segm_kwargs))
        if squares_proba > 0:
            self.probas.append(squares_proba)
            if squares_kwargs is None:
                squares_kwargs = {}
            else:
                squares_kwargs = dict(squares_kwargs)
            squares_kwargs['draw_method'] = DrawMethod.SQUARE
            self.gens.append(RandomIrregularMaskGenerator(**squares_kwargs))
        if superres_proba > 0:
            self.probas.append(superres_proba)
            if superres_kwargs is None:
                superres_kwargs = {}
            self.gens.append(RandomSuperresMaskGenerator(**superres_kwargs))
        if outpainting_proba > 0:
            self.probas.append(outpainting_proba)
            if outpainting_kwargs is None:
                outpainting_kwargs = {}
            self.gens.append(OutpaintingMaskGenerator(**outpainting_kwargs))
        self.probas = np.array(self.probas, dtype='float32')
        self.probas /= self.probas.sum()
        self.invert_proba = invert_proba

    def __call__(self, img, iter_i=None, raw_image=None):
        kind = np.random.choice(len(self.probas), p=self.probas)
        gen = self.gens[kind]
        result = gen(img, iter_i=iter_i, raw_image=raw_image)
        if self.invert_proba > 0 and random.random() < self.invert_proba:
            result = 1 - result
        return result

def __init__(self, irregular_proba=1 / 3, irregular_kwargs=None, box_proba=1 / 3, box_kwargs=None, segm_proba=1 / 3, segm_kwargs=None, squares_proba=0, squares_kwargs=None, superres_proba=0, superres_kwargs=None, outpainting_proba=0, outpainting_kwargs=None, invert_proba=0):
    self.probas = []
    self.gens = []
    if irregular_proba > 0:
        self.probas.append(irregular_proba)
        if irregular_kwargs is None:
            irregular_kwargs = {}
        else:
            irregular_kwargs = dict(irregular_kwargs)
        irregular_kwargs['draw_method'] = DrawMethod.LINE
        self.gens.append(RandomIrregularMaskGenerator(**irregular_kwargs))
    if box_proba > 0:
        self.probas.append(box_proba)
        if box_kwargs is None:
            box_kwargs = {}
        self.gens.append(RandomRectangleMaskGenerator(**box_kwargs))
    if segm_proba > 0:
        self.probas.append(segm_proba)
        if segm_kwargs is None:
            segm_kwargs = {}
        self.gens.append(RandomSegmentationMaskGenerator(**segm_kwargs))
    if squares_proba > 0:
        self.probas.append(squares_proba)
        if squares_kwargs is None:
            squares_kwargs = {}
        else:
            squares_kwargs = dict(squares_kwargs)
        squares_kwargs['draw_method'] = DrawMethod.SQUARE
        self.gens.append(RandomIrregularMaskGenerator(**squares_kwargs))
    if superres_proba > 0:
        self.probas.append(superres_proba)
        if superres_kwargs is None:
            superres_kwargs = {}
        self.gens.append(RandomSuperresMaskGenerator(**superres_kwargs))
    if outpainting_proba > 0:
        self.probas.append(outpainting_proba)
        if outpainting_kwargs is None:
            outpainting_kwargs = {}
        self.gens.append(OutpaintingMaskGenerator(**outpainting_kwargs))
    self.probas = np.array(self.probas, dtype='float32')
    self.probas /= self.probas.sum()
    self.invert_proba = invert_proba

def distribute_values_to_classes(target_class_freq_by_image_mask, values, idx2name):
    assert target_class_freq_by_image_mask.ndim == 2 and target_class_freq_by_image_mask.shape[0] == values.shape[0]
    total_class_freq = target_class_freq_by_image_mask.sum(0)
    distr_values = (target_class_freq_by_image_mask * values[..., None]).sum(0)
    result = distr_values / (total_class_freq + 0.001)
    return {idx2name[i]: val for i, val in enumerate(result) if total_class_freq[i] > 0}

class SSIM(torch.nn.Module):
    """SSIM. Modified from:
    https://github.com/Po-Hsun-Su/pytorch-ssim/blob/master/pytorch_ssim/__init__.py
    """

    def __init__(self, window_size=11, size_average=True):
        super().__init__()
        self.window_size = window_size
        self.size_average = size_average
        self.channel = 1
        self.register_buffer('window', self._create_window(window_size, self.channel))

    def forward(self, img1, img2):
        assert len(img1.shape) == 4
        channel = img1.size()[1]
        if channel == self.channel and self.window.data.type() == img1.data.type():
            window = self.window
        else:
            window = self._create_window(self.window_size, channel)
            window = window.type_as(img1)
            self.window = window
            self.channel = channel
        return self._ssim(img1, img2, window, self.window_size, channel, self.size_average)

    def _gaussian(self, window_size, sigma):
        gauss = torch.Tensor([np.exp(-(x - window_size // 2) ** 2 / float(2 * sigma ** 2)) for x in range(window_size)])
        return gauss / gauss.sum()

    def _create_window(self, window_size, channel):
        _1D_window = self._gaussian(window_size, 1.5).unsqueeze(1)
        _2D_window = _1D_window.mm(_1D_window.t()).float().unsqueeze(0).unsqueeze(0)
        return _2D_window.expand(channel, 1, window_size, window_size).contiguous()

    def _ssim(self, img1, img2, window, window_size, channel, size_average=True):
        mu1 = F.conv2d(img1, window, padding=window_size // 2, groups=channel)
        mu2 = F.conv2d(img2, window, padding=window_size // 2, groups=channel)
        mu1_sq = mu1.pow(2)
        mu2_sq = mu2.pow(2)
        mu1_mu2 = mu1 * mu2
        sigma1_sq = F.conv2d(img1 * img1, window, padding=window_size // 2, groups=channel) - mu1_sq
        sigma2_sq = F.conv2d(img2 * img2, window, padding=window_size // 2, groups=channel) - mu2_sq
        sigma12 = F.conv2d(img1 * img2, window, padding=window_size // 2, groups=channel) - mu1_mu2
        C1 = 0.01 ** 2
        C2 = 0.03 ** 2
        ssim_map = (2 * mu1_mu2 + C1) * (2 * sigma12 + C2) / ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
        if size_average:
            return ssim_map.mean()
        return ssim_map.mean(1).mean(1).mean(1)

    def _load_from_state_dict(self, state_dict, prefix, local_metadata, strict, missing_keys, unexpected_keys, error_msgs):
        return

def forward(self, img1, img2):
    assert len(img1.shape) == 4
    channel = img1.size()[1]
    if channel == self.channel and self.window.data.type() == img1.data.type():
        window = self.window
    else:
        window = self._create_window(self.window_size, channel)
        window = window.type_as(img1)
        self.window = window
        self.channel = channel
    return self._ssim(img1, img2, window, self.window_size, channel, self.size_average)

def _gaussian(self, window_size, sigma):
    gauss = torch.Tensor([np.exp(-(x - window_size // 2) ** 2 / float(2 * sigma ** 2)) for x in range(window_size)])
    return gauss / gauss.sum()

def normalize_tensor(in_feat, eps=1e-10):
    norm_factor = torch.sqrt(torch.sum(in_feat ** 2, dim=1, keepdim=True))
    return in_feat / (norm_factor + eps)

def rgb2lab(input):
    from skimage import color
    return color.rgb2lab(input / 255.0)

def np2tensor(np_obj):
    return torch.Tensor(np_obj[:, :, :, np.newaxis].transpose((3, 2, 0, 1)))

def tensor2tensorlab(image_tensor, to_norm=True, mc_only=False):
    from skimage import color
    img = tensor2im(image_tensor)
    img_lab = color.rgb2lab(img)
    if mc_only:
        img_lab[:, :, 0] = img_lab[:, :, 0] - 50
    if to_norm and (not mc_only):
        img_lab[:, :, 0] = img_lab[:, :, 0] - 50
        img_lab = img_lab / 100.0
    return np2tensor(img_lab)

def tensorlab2tensor(lab_tensor, return_inbnd=False):
    from skimage import color
    import warnings
    warnings.filterwarnings('ignore')
    lab = tensor2np(lab_tensor) * 100.0
    lab[:, :, 0] = lab[:, :, 0] + 50
    rgb_back = 255.0 * np.clip(color.lab2rgb(lab.astype('float')), 0, 1)
    if return_inbnd:
        lab_back = color.rgb2lab(rgb_back.astype('uint8'))
        mask = 1.0 * np.isclose(lab_back, lab, atol=2.0)
        mask = np2tensor(np.prod(mask, axis=2)[:, :, np.newaxis])
        return (im2tensor(rgb_back), mask)
    else:
        return im2tensor(rgb_back)

def im2tensor(image, imtype=np.uint8, cent=1.0, factor=255.0 / 2.0):
    return torch.Tensor((image / factor - cent)[:, :, :, np.newaxis].transpose((3, 2, 0, 1)))

class DistModel(BaseModel):

    def name(self):
        return self.model_name

    def initialize(self, model='net-lin', net='alex', colorspace='Lab', pnet_rand=False, pnet_tune=False, model_path=None, use_gpu=True, printNet=False, spatial=False, is_train=False, lr=0.0001, beta1=0.5, version='0.1'):
        """
        INPUTS
            model - ['net-lin'] for linearly calibrated network
                    ['net'] for off-the-shelf network
                    ['L2'] for L2 distance in Lab colorspace
                    ['SSIM'] for ssim in RGB colorspace
            net - ['squeeze','alex','vgg']
            model_path - if None, will look in weights/[NET_NAME].pth
            colorspace - ['Lab','RGB'] colorspace to use for L2 and SSIM
            use_gpu - bool - whether or not to use a GPU
            printNet - bool - whether or not to print network architecture out
            spatial - bool - whether to output an array containing varying distances across spatial dimensions
            spatial_shape - if given, output spatial shape. if None then spatial shape is determined automatically via spatial_factor (see below).
            spatial_factor - if given, specifies upsampling factor relative to the largest spatial extent of a convolutional layer. if None then resized to size of input images.
            spatial_order - spline order of filter for upsampling in spatial mode, by default 1 (bilinear).
            is_train - bool - [True] for training mode
            lr - float - initial learning rate
            beta1 - float - initial momentum term for adam
            version - 0.1 for latest, 0.0 was original (with a bug)
        """
        BaseModel.initialize(self, use_gpu=use_gpu)
        self.model = model
        self.net = net
        self.is_train = is_train
        self.spatial = spatial
        self.model_name = '%s [%s]' % (model, net)
        if self.model == 'net-lin':
            self.net = PNetLin(pnet_rand=pnet_rand, pnet_tune=pnet_tune, pnet_type=net, use_dropout=True, spatial=spatial, version=version, lpips=True)
            kw = dict(map_location='cpu')
            if model_path is None:
                import inspect
                model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'models', 'lpips_models', f'{net}.pth'))
            if not is_train:
                self.net.load_state_dict(torch.load(model_path, **kw), strict=False)
        elif self.model == 'net':
            self.net = PNetLin(pnet_rand=pnet_rand, pnet_type=net, lpips=False)
        elif self.model in ['L2', 'l2']:
            self.net = L2(use_gpu=use_gpu, colorspace=colorspace)
            self.model_name = 'L2'
        elif self.model in ['DSSIM', 'dssim', 'SSIM', 'ssim']:
            self.net = DSSIM(use_gpu=use_gpu, colorspace=colorspace)
            self.model_name = 'SSIM'
        else:
            raise ValueError('Model [%s] not recognized.' % self.model)
        self.trainable_parameters = list(self.net.parameters())
        if self.is_train:
            self.rankLoss = BCERankingLoss()
            self.trainable_parameters += list(self.rankLoss.net.parameters())
            self.lr = lr
            self.old_lr = lr
            self.optimizer_net = torch.optim.Adam(self.trainable_parameters, lr=lr, betas=(beta1, 0.999))
        else:
            self.net.eval()
        if printNet:
            print('---------- Networks initialized -------------')
            print_network(self.net)
            print('-----------------------------------------------')

    def forward(self, in0, in1, retPerLayer=False):
        """ Function computes the distance between image patches in0 and in1
        INPUTS
            in0, in1 - torch.Tensor object of shape Nx3xXxY - image patch scaled to [-1,1]
        OUTPUT
            computed distances between in0 and in1
        """
        return self.net(in0, in1, retPerLayer=retPerLayer)

    def optimize_parameters(self):
        self.forward_train()
        self.optimizer_net.zero_grad()
        self.backward_train()
        self.optimizer_net.step()
        self.clamp_weights()

    def clamp_weights(self):
        for module in self.net.modules():
            if hasattr(module, 'weight') and module.kernel_size == (1, 1):
                module.weight.data = torch.clamp(module.weight.data, min=0)

    def set_input(self, data):
        self.input_ref = data['ref']
        self.input_p0 = data['p0']
        self.input_p1 = data['p1']
        self.input_judge = data['judge']

    def forward_train(self):
        assert False, "We shoud've not get here when using LPIPS as a metric"
        self.d0 = self(self.var_ref, self.var_p0)
        self.d1 = self(self.var_ref, self.var_p1)
        self.acc_r = self.compute_accuracy(self.d0, self.d1, self.input_judge)
        self.var_judge = Variable(1.0 * self.input_judge).view(self.d0.size())
        self.loss_total = self.rankLoss(self.d0, self.d1, self.var_judge * 2.0 - 1.0)
        return self.loss_total

    def backward_train(self):
        torch.mean(self.loss_total).backward()

    def compute_accuracy(self, d0, d1, judge):
        """ d0, d1 are Variables, judge is a Tensor """
        d1_lt_d0 = (d1 < d0).cpu().data.numpy().flatten()
        judge_per = judge.cpu().numpy().flatten()
        return d1_lt_d0 * judge_per + (1 - d1_lt_d0) * (1 - judge_per)

    def get_current_errors(self):
        retDict = OrderedDict([('loss_total', self.loss_total.data.cpu().numpy()), ('acc_r', self.acc_r)])
        for key in retDict.keys():
            retDict[key] = np.mean(retDict[key])
        return retDict

    def get_current_visuals(self):
        zoom_factor = 256 / self.var_ref.data.size()[2]
        ref_img = tensor2im(self.var_ref.data)
        p0_img = tensor2im(self.var_p0.data)
        p1_img = tensor2im(self.var_p1.data)
        ref_img_vis = zoom(ref_img, [zoom_factor, zoom_factor, 1], order=0)
        p0_img_vis = zoom(p0_img, [zoom_factor, zoom_factor, 1], order=0)
        p1_img_vis = zoom(p1_img, [zoom_factor, zoom_factor, 1], order=0)
        return OrderedDict([('ref', ref_img_vis), ('p0', p0_img_vis), ('p1', p1_img_vis)])

    def save(self, path, label):
        if self.use_gpu:
            self.save_network(self.net.module, path, '', label)
        else:
            self.save_network(self.net, path, '', label)
        self.save_network(self.rankLoss.net, path, 'rank', label)

    def update_learning_rate(self, nepoch_decay):
        lrd = self.lr / nepoch_decay
        lr = self.old_lr - lrd
        for param_group in self.optimizer_net.param_groups:
            param_group['lr'] = lr
        print('update lr [%s] decay: %f -> %f' % (type, self.old_lr, lr))
        self.old_lr = lr

def forward_train(self):
    assert False, "We shoud've not get here when using LPIPS as a metric"
    self.d0 = self(self.var_ref, self.var_p0)
    self.d1 = self(self.var_ref, self.var_p1)
    self.acc_r = self.compute_accuracy(self.d0, self.d1, self.input_judge)
    self.var_judge = Variable(1.0 * self.input_judge).view(self.d0.size())
    self.loss_total = self.rankLoss(self.d0, self.d1, self.var_judge * 2.0 - 1.0)
    return self.loss_total

def backward_train(self):
    torch.mean(self.loss_total).backward()

def get_current_visuals(self):
    zoom_factor = 256 / self.var_ref.data.size()[2]
    ref_img = tensor2im(self.var_ref.data)
    p0_img = tensor2im(self.var_p0.data)
    p1_img = tensor2im(self.var_p1.data)
    ref_img_vis = zoom(ref_img, [zoom_factor, zoom_factor, 1], order=0)
    p0_img_vis = zoom(p0_img, [zoom_factor, zoom_factor, 1], order=0)
    p1_img_vis = zoom(p1_img, [zoom_factor, zoom_factor, 1], order=0)
    return OrderedDict([('ref', ref_img_vis), ('p0', p0_img_vis), ('p1', p1_img_vis)])

class L2(FakeNet):

    def forward(self, in0, in1, retPerLayer=None):
        assert in0.size()[0] == 1
        if self.colorspace == 'RGB':
            N, C, X, Y = in0.size()
            value = torch.mean(torch.mean(torch.mean((in0 - in1) ** 2, dim=1).view(N, 1, X, Y), dim=2).view(N, 1, 1, Y), dim=3).view(N)
            return value
        elif self.colorspace == 'Lab':
            value = l2(tensor2np(tensor2tensorlab(in0.data, to_norm=False)), tensor2np(tensor2tensorlab(in1.data, to_norm=False)), range=100.0).astype('float')
            ret_var = Variable(torch.Tensor((value,)))
            return ret_var

def forward(self, in0, in1, retPerLayer=None):
    assert in0.size()[0] == 1
    if self.colorspace == 'RGB':
        N, C, X, Y = in0.size()
        value = torch.mean(torch.mean(torch.mean((in0 - in1) ** 2, dim=1).view(N, 1, X, Y), dim=2).view(N, 1, 1, Y), dim=3).view(N)
        return value
    elif self.colorspace == 'Lab':
        value = l2(tensor2np(tensor2tensorlab(in0.data, to_norm=False)), tensor2np(tensor2tensorlab(in1.data, to_norm=False)), range=100.0).astype('float')
        ret_var = Variable(torch.Tensor((value,)))
        return ret_var

class DSSIM(FakeNet):

    def forward(self, in0, in1, retPerLayer=None):
        assert in0.size()[0] == 1
        if self.colorspace == 'RGB':
            value = dssim(1.0 * tensor2im(in0.data), 1.0 * tensor2im(in1.data), range=255.0).astype('float')
        elif self.colorspace == 'Lab':
            value = dssim(tensor2np(tensor2tensorlab(in0.data, to_norm=False)), tensor2np(tensor2tensorlab(in1.data, to_norm=False)), range=100.0).astype('float')
        ret_var = Variable(torch.Tensor((value,)))
        return ret_var

def forward(self, in0, in1, retPerLayer=None):
    assert in0.size()[0] == 1
    if self.colorspace == 'RGB':
        value = dssim(1.0 * tensor2im(in0.data), 1.0 * tensor2im(in1.data), range=255.0).astype('float')
    elif self.colorspace == 'Lab':
        value = dssim(tensor2np(tensor2tensorlab(in0.data, to_norm=False)), tensor2np(tensor2tensorlab(in1.data, to_norm=False)), range=100.0).astype('float')
    ret_var = Variable(torch.Tensor((value,)))
    return ret_var

class ObjectMask:

    def __init__(self, mask):
        self.height, self.width = mask.shape
        (self.up, self.down), (self.left, self.right) = self._get_limits(mask)
        self.mask = mask[self.up:self.down, self.left:self.right].copy()

    @staticmethod
    def _get_limits(mask):

        def indicator_limits(indicator):
            lower = indicator.argmax()
            upper = len(indicator) - indicator[::-1].argmax()
            return (lower, upper)
        vertical_indicator = mask.any(axis=1)
        vertical_limits = indicator_limits(vertical_indicator)
        horizontal_indicator = mask.any(axis=0)
        horizontal_limits = indicator_limits(horizontal_indicator)
        return (vertical_limits, horizontal_limits)

    def _clean(self):
        self.up, self.down, self.left, self.right = (0, 0, 0, 0)
        self.mask = np.empty((0, 0))

    def horizontal_flip(self, inplace=False):
        if not inplace:
            flipped = deepcopy(self)
            return flipped.horizontal_flip(inplace=True)
        self.mask = self.mask[:, ::-1]
        return self

    def vertical_flip(self, inplace=False):
        if not inplace:
            flipped = deepcopy(self)
            return flipped.vertical_flip(inplace=True)
        self.mask = self.mask[::-1, :]
        return self

    def image_center(self):
        y_center = self.up + (self.down - self.up) / 2
        x_center = self.left + (self.right - self.left) / 2
        return (y_center, x_center)

    def rescale(self, scaling_factor, inplace=False):
        if not inplace:
            scaled = deepcopy(self)
            return scaled.rescale(scaling_factor, inplace=True)
        scaled_mask = rescale(self.mask.astype(float), scaling_factor, order=0) > 0.5
        (up, down), (left, right) = self._get_limits(scaled_mask)
        self.mask = scaled_mask[up:down, left:right]
        y_center, x_center = self.image_center()
        mask_height, mask_width = self.mask.shape
        self.up = int(round(y_center - mask_height / 2))
        self.down = self.up + mask_height
        self.left = int(round(x_center - mask_width / 2))
        self.right = self.left + mask_width
        return self

    def crop_to_canvas(self, vertical=True, horizontal=True, inplace=False):
        if not inplace:
            cropped = deepcopy(self)
            cropped.crop_to_canvas(vertical=vertical, horizontal=horizontal, inplace=True)
            return cropped
        if vertical:
            if self.up >= self.height or self.down <= 0:
                self._clean()
            else:
                cut_up, cut_down = (max(-self.up, 0), max(self.down - self.height, 0))
                if cut_up != 0:
                    self.mask = self.mask[cut_up:]
                    self.up = 0
                if cut_down != 0:
                    self.mask = self.mask[:-cut_down]
                    self.down = self.height
        if horizontal:
            if self.left >= self.width or self.right <= 0:
                self._clean()
            else:
                cut_left, cut_right = (max(-self.left, 0), max(self.right - self.width, 0))
                if cut_left != 0:
                    self.mask = self.mask[:, cut_left:]
                    self.left = 0
                if cut_right != 0:
                    self.mask = self.mask[:, :-cut_right]
                    self.right = self.width
        return self

    def restore_full_mask(self, allow_crop=False):
        cropped = self.crop_to_canvas(inplace=allow_crop)
        mask = np.zeros((cropped.height, cropped.width), dtype=bool)
        mask[cropped.up:cropped.down, cropped.left:cropped.right] = cropped.mask
        return mask

    def shift(self, vertical=0, horizontal=0, inplace=False):
        if not inplace:
            shifted = deepcopy(self)
            return shifted.shift(vertical=vertical, horizontal=horizontal, inplace=True)
        self.up += vertical
        self.down += vertical
        self.left += horizontal
        self.right += horizontal
        return self

    def area(self):
        return self.mask.sum()

def area(self):
    return self.mask.sum()

class SegmentationMask:

    def __init__(self, confidence_threshold=0.5, rigidness_mode=RigidnessMode.rigid, max_object_area=0.3, min_mask_area=0.02, downsample_levels=6, num_variants_per_mask=4, max_mask_intersection=0.5, max_foreground_coverage=0.5, max_foreground_intersection=0.5, max_hidden_area=0.2, max_scale_change=0.25, horizontal_flip=True, max_vertical_shift=0.1, position_shuffle=True):
        """
        :param confidence_threshold: float; threshold for confidence of the panoptic segmentator to allow for
        the instance.
        :param rigidness_mode: RigidnessMode object
            when soft, checks intersection only with the object from which the mask_object was produced
            when rigid, checks intersection with any foreground class object
        :param max_object_area: float; allowed upper bound for to be considered as mask_object.
        :param min_mask_area: float; lower bound for mask to be considered valid
        :param downsample_levels: int; defines width of the resized segmentation to obtain shifted masks;
        :param num_variants_per_mask: int; maximal number of the masks for the same object;
        :param max_mask_intersection: float; maximum allowed area fraction of intersection for 2 masks
        produced by horizontal shift of the same mask_object; higher value -> more diversity
        :param max_foreground_coverage: float; maximum allowed area fraction of intersection for foreground object to be
        covered by mask; lower value -> less the objects are covered
        :param max_foreground_intersection: float; maximum allowed area of intersection for the mask with foreground
        object; lower value -> mask is more on the background than on the objects
        :param max_hidden_area: upper bound on part of the object hidden by shifting object outside the screen area;
        :param max_scale_change: allowed scale change for the mask_object;
        :param horizontal_flip: if horizontal flips are allowed;
        :param max_vertical_shift: amount of vertical movement allowed;
        :param position_shuffle: shuffle
        """
        assert DETECTRON_INSTALLED, 'Cannot use SegmentationMask without detectron2'
        self.cfg = get_cfg()
        self.cfg.merge_from_file(model_zoo.get_config_file('COCO-PanopticSegmentation/panoptic_fpn_R_101_3x.yaml'))
        self.cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url('COCO-PanopticSegmentation/panoptic_fpn_R_101_3x.yaml')
        self.cfg.MODEL.PANOPTIC_FPN.COMBINE.INSTANCES_CONFIDENCE_THRESH = confidence_threshold
        self.predictor = DefaultPredictor(self.cfg)
        self.rigidness_mode = RigidnessMode(rigidness_mode)
        self.max_object_area = max_object_area
        self.min_mask_area = min_mask_area
        self.downsample_levels = downsample_levels
        self.num_variants_per_mask = num_variants_per_mask
        self.max_mask_intersection = max_mask_intersection
        self.max_foreground_coverage = max_foreground_coverage
        self.max_foreground_intersection = max_foreground_intersection
        self.max_hidden_area = max_hidden_area
        self.position_shuffle = position_shuffle
        self.max_scale_change = max_scale_change
        self.horizontal_flip = horizontal_flip
        self.max_vertical_shift = max_vertical_shift

    def get_segmentation(self, img):
        im = img_as_ubyte(img)
        panoptic_seg, segment_info = self.predictor(im)['panoptic_seg']
        return (panoptic_seg, segment_info)

    @staticmethod
    def _is_power_of_two(n):
        return n != 0 and n & n - 1 == 0

    def identify_candidates(self, panoptic_seg, segments_info):
        potential_mask_ids = []
        for segment in segments_info:
            if not segment['isthing']:
                continue
            mask = (panoptic_seg == segment['id']).int().detach().cpu().numpy()
            area = mask.sum().item() / np.prod(panoptic_seg.shape)
            if area >= self.max_object_area:
                continue
            potential_mask_ids.append(segment['id'])
        return potential_mask_ids

    def downsample_mask(self, mask):
        height, width = mask.shape
        if not (self._is_power_of_two(height) and self._is_power_of_two(width)):
            raise ValueError('Image sides are not power of 2.')
        num_iterations = width.bit_length() - 1 - self.downsample_levels
        if num_iterations < 0:
            raise ValueError(f'Width is lower than 2^{self.downsample_levels}.')
        if height.bit_length() - 1 < num_iterations:
            raise ValueError('Height is too low to perform downsampling')
        downsampled = mask
        for _ in range(num_iterations):
            downsampled = zero_corrected_countless(downsampled)
        return downsampled

    def _augmentation_params(self):
        scaling_factor = np.random.uniform(1 - self.max_scale_change, 1 + self.max_scale_change)
        if self.horizontal_flip:
            horizontal_flip = bool(np.random.choice(2))
        else:
            horizontal_flip = False
        vertical_shift = np.random.uniform(-self.max_vertical_shift, self.max_vertical_shift)
        return {'scaling_factor': scaling_factor, 'horizontal_flip': horizontal_flip, 'vertical_shift': vertical_shift}

    def _get_intersection(self, mask_array, mask_object):
        intersection = mask_array[mask_object.up:mask_object.down, mask_object.left:mask_object.right] & mask_object.mask
        return intersection

    def _check_masks_intersection(self, aug_mask, total_mask_area, prev_masks):
        for existing_mask in prev_masks:
            intersection_area = self._get_intersection(existing_mask, aug_mask).sum()
            intersection_existing = intersection_area / existing_mask.sum()
            intersection_current = 1 - (aug_mask.area() - intersection_area) / total_mask_area
            if intersection_existing > self.max_mask_intersection or intersection_current > self.max_mask_intersection:
                return False
        return True

    def _check_foreground_intersection(self, aug_mask, foreground):
        for existing_mask in foreground:
            intersection_area = self._get_intersection(existing_mask, aug_mask).sum()
            intersection_existing = intersection_area / existing_mask.sum()
            if intersection_existing > self.max_foreground_coverage:
                return False
            intersection_mask = intersection_area / aug_mask.area()
            if intersection_mask > self.max_foreground_intersection:
                return False
        return True

    def _move_mask(self, mask, foreground):
        orig_mask = ObjectMask(mask)
        chosen_masks = []
        chosen_parameters = []
        scaling_factor_lower_bound = 0.0
        for var_idx in range(self.num_variants_per_mask):
            augmentation_params = self._augmentation_params()
            augmentation_params['scaling_factor'] = min([augmentation_params['scaling_factor'], 2 * min(orig_mask.up, orig_mask.height - orig_mask.down) / orig_mask.height + 1.0, 2 * min(orig_mask.left, orig_mask.width - orig_mask.right) / orig_mask.width + 1.0])
            augmentation_params['scaling_factor'] = max([augmentation_params['scaling_factor'], scaling_factor_lower_bound])
            aug_mask = deepcopy(orig_mask)
            aug_mask.rescale(augmentation_params['scaling_factor'], inplace=True)
            if augmentation_params['horizontal_flip']:
                aug_mask.horizontal_flip(inplace=True)
            total_aug_area = aug_mask.area()
            if total_aug_area == 0:
                scaling_factor_lower_bound = 1.0
                continue
            vertical_area = aug_mask.mask.sum(axis=1) / total_aug_area
            max_hidden_up = np.searchsorted(vertical_area.cumsum(), self.max_hidden_area)
            max_hidden_down = np.searchsorted(vertical_area[::-1].cumsum(), self.max_hidden_area)
            augmentation_params['vertical_shift'] = np.clip(augmentation_params['vertical_shift'], -(aug_mask.up + max_hidden_up) / aug_mask.height, (aug_mask.height - aug_mask.down + max_hidden_down) / aug_mask.height)
            vertical_shift = int(round(aug_mask.height * augmentation_params['vertical_shift']))
            aug_mask.shift(vertical=vertical_shift, inplace=True)
            aug_mask.crop_to_canvas(vertical=True, horizontal=False, inplace=True)
            max_hidden_area = self.max_hidden_area - (1 - aug_mask.area() / total_aug_area)
            horizontal_area = aug_mask.mask.sum(axis=0) / total_aug_area
            max_hidden_left = np.searchsorted(horizontal_area.cumsum(), max_hidden_area)
            max_hidden_right = np.searchsorted(horizontal_area[::-1].cumsum(), max_hidden_area)
            allowed_shifts = np.arange(-max_hidden_left, aug_mask.width - (aug_mask.right - aug_mask.left) + max_hidden_right + 1)
            allowed_shifts = -(aug_mask.left - allowed_shifts)
            if self.position_shuffle:
                np.random.shuffle(allowed_shifts)
            mask_is_found = False
            for horizontal_shift in allowed_shifts:
                aug_mask_left = deepcopy(aug_mask)
                aug_mask_left.shift(horizontal=horizontal_shift, inplace=True)
                aug_mask_left.crop_to_canvas(inplace=True)
                prev_masks = [mask] + chosen_masks
                is_mask_suitable = self._check_masks_intersection(aug_mask_left, total_aug_area, prev_masks) & self._check_foreground_intersection(aug_mask_left, foreground)
                if is_mask_suitable:
                    aug_draw = aug_mask_left.restore_full_mask()
                    chosen_masks.append(aug_draw)
                    augmentation_params['horizontal_shift'] = horizontal_shift / aug_mask_left.width
                    chosen_parameters.append(augmentation_params)
                    mask_is_found = True
                    break
            if not mask_is_found:
                break
        return chosen_parameters

    def _prepare_mask(self, mask):
        height, width = mask.shape
        target_width = width if self._is_power_of_two(width) else 1 << width.bit_length()
        target_height = height if self._is_power_of_two(height) else 1 << height.bit_length()
        return resize(mask.astype('float32'), (target_height, target_width), order=0, mode='edge').round().astype('int32')

    def get_masks(self, im, return_panoptic=False):
        panoptic_seg, segments_info = self.get_segmentation(im)
        potential_mask_ids = self.identify_candidates(panoptic_seg, segments_info)
        panoptic_seg_scaled = self._prepare_mask(panoptic_seg.detach().cpu().numpy())
        downsampled = self.downsample_mask(panoptic_seg_scaled)
        scene_objects = []
        for segment in segments_info:
            if not segment['isthing']:
                continue
            mask = downsampled == segment['id']
            if not np.any(mask):
                continue
            scene_objects.append(mask)
        mask_set = []
        for mask_id in potential_mask_ids:
            mask = downsampled == mask_id
            if not np.any(mask):
                continue
            if self.rigidness_mode is RigidnessMode.soft:
                foreground = [mask]
            elif self.rigidness_mode is RigidnessMode.rigid:
                foreground = scene_objects
            else:
                raise ValueError(f'Unexpected rigidness_mode: {rigidness_mode}')
            masks_params = self._move_mask(mask, foreground)
            full_mask = ObjectMask((panoptic_seg == mask_id).detach().cpu().numpy())
            for params in masks_params:
                aug_mask = deepcopy(full_mask)
                aug_mask.rescale(params['scaling_factor'], inplace=True)
                if params['horizontal_flip']:
                    aug_mask.horizontal_flip(inplace=True)
                vertical_shift = int(round(aug_mask.height * params['vertical_shift']))
                horizontal_shift = int(round(aug_mask.width * params['horizontal_shift']))
                aug_mask.shift(vertical=vertical_shift, horizontal=horizontal_shift, inplace=True)
                aug_mask = aug_mask.restore_full_mask().astype('uint8')
                if aug_mask.mean() <= self.min_mask_area:
                    continue
                mask_set.append(aug_mask)
        if return_panoptic:
            return (mask_set, panoptic_seg.detach().cpu().numpy())
        else:
            return mask_set

def _check_masks_intersection(self, aug_mask, total_mask_area, prev_masks):
    for existing_mask in prev_masks:
        intersection_area = self._get_intersection(existing_mask, aug_mask).sum()
        intersection_existing = intersection_area / existing_mask.sum()
        intersection_current = 1 - (aug_mask.area() - intersection_area) / total_mask_area
        if intersection_existing > self.max_mask_intersection or intersection_current > self.max_mask_intersection:
            return False
    return True

def _check_foreground_intersection(self, aug_mask, foreground):
    for existing_mask in foreground:
        intersection_area = self._get_intersection(existing_mask, aug_mask).sum()
        intersection_existing = intersection_area / existing_mask.sum()
        if intersection_existing > self.max_foreground_coverage:
            return False
        intersection_mask = intersection_area / aug_mask.area()
        if intersection_mask > self.max_foreground_intersection:
            return False
    return True

def ndzoom(array):
    if len(array.shape) == 3:
        ratio = (1 / 2.0, 1 / 2.0, 1.0)
    else:
        ratio = (1 / 2.0, 1 / 2.0)
    return ndimage.interpolation.zoom(array, ratio, order=1)

def _sum_ft(tensor):
    """sum over the first and last dimention"""
    return tensor.sum(dim=0).sum(dim=-1)

class _SynchronizedBatchNorm(_BatchNorm):

    def __init__(self, num_features, eps=1e-05, momentum=0.001, affine=True):
        super(_SynchronizedBatchNorm, self).__init__(num_features, eps=eps, momentum=momentum, affine=affine)
        self._sync_master = SyncMaster(self._data_parallel_master)
        self._is_parallel = False
        self._parallel_id = None
        self._slave_pipe = None
        self._moving_average_fraction = 1.0 - momentum
        self.register_buffer('_tmp_running_mean', torch.zeros(self.num_features))
        self.register_buffer('_tmp_running_var', torch.ones(self.num_features))
        self.register_buffer('_running_iter', torch.ones(1))
        self._tmp_running_mean = self.running_mean.clone() * self._running_iter
        self._tmp_running_var = self.running_var.clone() * self._running_iter

    def forward(self, input):
        if not (self._is_parallel and self.training):
            return F.batch_norm(input, self.running_mean, self.running_var, self.weight, self.bias, self.training, self.momentum, self.eps)
        input_shape = input.size()
        input = input.view(input.size(0), self.num_features, -1)
        sum_size = input.size(0) * input.size(2)
        input_sum = _sum_ft(input)
        input_ssum = _sum_ft(input ** 2)
        if self._parallel_id == 0:
            mean, inv_std = self._sync_master.run_master(_ChildMessage(input_sum, input_ssum, sum_size))
        else:
            mean, inv_std = self._slave_pipe.run_slave(_ChildMessage(input_sum, input_ssum, sum_size))
        if self.affine:
            output = (input - _unsqueeze_ft(mean)) * _unsqueeze_ft(inv_std * self.weight) + _unsqueeze_ft(self.bias)
        else:
            output = (input - _unsqueeze_ft(mean)) * _unsqueeze_ft(inv_std)
        return output.view(input_shape)

    def __data_parallel_replicate__(self, ctx, copy_id):
        self._is_parallel = True
        self._parallel_id = copy_id
        if self._parallel_id == 0:
            ctx.sync_master = self._sync_master
        else:
            self._slave_pipe = ctx.sync_master.register_slave(copy_id)

    def _data_parallel_master(self, intermediates):
        """Reduce the sum and square-sum, compute the statistics, and broadcast it."""
        intermediates = sorted(intermediates, key=lambda i: i[1].sum.get_device())
        to_reduce = [i[1][:2] for i in intermediates]
        to_reduce = [j for i in to_reduce for j in i]
        target_gpus = [i[1].sum.get_device() for i in intermediates]
        sum_size = sum([i[1].sum_size for i in intermediates])
        sum_, ssum = ReduceAddCoalesced.apply(target_gpus[0], 2, *to_reduce)
        mean, inv_std = self._compute_mean_std(sum_, ssum, sum_size)
        broadcasted = Broadcast.apply(target_gpus, mean, inv_std)
        outputs = []
        for i, rec in enumerate(intermediates):
            outputs.append((rec[0], _MasterMessage(*broadcasted[i * 2:i * 2 + 2])))
        return outputs

    def _add_weighted(self, dest, delta, alpha=1, beta=1, bias=0):
        """return *dest* by `dest := dest*alpha + delta*beta + bias`"""
        return dest * alpha + delta * beta + bias

    def _compute_mean_std(self, sum_, ssum, size):
        """Compute the mean and standard-deviation with sum and square-sum. This method
        also maintains the moving average on the master device."""
        assert size > 1, 'BatchNorm computes unbiased standard-deviation, which requires size > 1.'
        mean = sum_ / size
        sumvar = ssum - sum_ * mean
        unbias_var = sumvar / (size - 1)
        bias_var = sumvar / size
        self._tmp_running_mean = self._add_weighted(self._tmp_running_mean, mean.data, alpha=self._moving_average_fraction)
        self._tmp_running_var = self._add_weighted(self._tmp_running_var, unbias_var.data, alpha=self._moving_average_fraction)
        self._running_iter = self._add_weighted(self._running_iter, 1, alpha=self._moving_average_fraction)
        self.running_mean = self._tmp_running_mean / self._running_iter
        self.running_var = self._tmp_running_var / self._running_iter
        return (mean, bias_var.clamp(self.eps) ** (-0.5))

def forward(self, input):
    if not (self._is_parallel and self.training):
        return F.batch_norm(input, self.running_mean, self.running_var, self.weight, self.bias, self.training, self.momentum, self.eps)
    input_shape = input.size()
    input = input.view(input.size(0), self.num_features, -1)
    sum_size = input.size(0) * input.size(2)
    input_sum = _sum_ft(input)
    input_ssum = _sum_ft(input ** 2)
    if self._parallel_id == 0:
        mean, inv_std = self._sync_master.run_master(_ChildMessage(input_sum, input_ssum, sum_size))
    else:
        mean, inv_std = self._slave_pipe.run_slave(_ChildMessage(input_sum, input_ssum, sum_size))
    if self.affine:
        output = (input - _unsqueeze_ft(mean)) * _unsqueeze_ft(inv_std * self.weight) + _unsqueeze_ft(self.bias)
    else:
        output = (input - _unsqueeze_ft(mean)) * _unsqueeze_ft(inv_std)
    return output.view(input_shape)

def _data_parallel_master(self, intermediates):
    """Reduce the sum and square-sum, compute the statistics, and broadcast it."""
    intermediates = sorted(intermediates, key=lambda i: i[1].sum.get_device())
    to_reduce = [i[1][:2] for i in intermediates]
    to_reduce = [j for i in to_reduce for j in i]
    target_gpus = [i[1].sum.get_device() for i in intermediates]
    sum_size = sum([i[1].sum_size for i in intermediates])
    sum_, ssum = ReduceAddCoalesced.apply(target_gpus[0], 2, *to_reduce)
    mean, inv_std = self._compute_mean_std(sum_, ssum, sum_size)
    broadcasted = Broadcast.apply(target_gpus, mean, inv_std)
    outputs = []
    for i, rec in enumerate(intermediates):
        outputs.append((rec[0], _MasterMessage(*broadcasted[i * 2:i * 2 + 2])))
    return outputs

def handy_var(a, unbias=True):
    n = a.size(0)
    asum = a.sum(dim=0)
    as_sum = (a ** 2).sum(dim=0)
    sumvar = as_sum - asum * asum / n
    if unbias:
        return sumvar / (n - 1)
    else:
        return sumvar / n

class SyncTestCase(TorchTestCase):

    def _syncParameters(self, bn1, bn2):
        bn1.reset_parameters()
        bn2.reset_parameters()
        if bn1.affine and bn2.affine:
            bn2.weight.data.copy_(bn1.weight.data)
            bn2.bias.data.copy_(bn1.bias.data)

    def _checkBatchNormResult(self, bn1, bn2, input, is_train, cuda=False):
        """Check the forward and backward for the customized batch normalization."""
        bn1.train(mode=is_train)
        bn2.train(mode=is_train)
        if cuda:
            input = input.cuda()
        self._syncParameters(_find_bn(bn1), _find_bn(bn2))
        input1 = Variable(input, requires_grad=True)
        output1 = bn1(input1)
        output1.sum().backward()
        input2 = Variable(input, requires_grad=True)
        output2 = bn2(input2)
        output2.sum().backward()
        self.assertTensorClose(input1.data, input2.data)
        self.assertTensorClose(output1.data, output2.data)
        self.assertTensorClose(input1.grad, input2.grad)
        self.assertTensorClose(_find_bn(bn1).running_mean, _find_bn(bn2).running_mean)
        self.assertTensorClose(_find_bn(bn1).running_var, _find_bn(bn2).running_var)

    def testSyncBatchNormNormalTrain(self):
        bn = nn.BatchNorm1d(10)
        sync_bn = SynchronizedBatchNorm1d(10)
        self._checkBatchNormResult(bn, sync_bn, torch.rand(16, 10), True)

    def testSyncBatchNormNormalEval(self):
        bn = nn.BatchNorm1d(10)
        sync_bn = SynchronizedBatchNorm1d(10)
        self._checkBatchNormResult(bn, sync_bn, torch.rand(16, 10), False)

    def testSyncBatchNormSyncTrain(self):
        bn = nn.BatchNorm1d(10, eps=1e-05, affine=False)
        sync_bn = SynchronizedBatchNorm1d(10, eps=1e-05, affine=False)
        sync_bn = DataParallelWithCallback(sync_bn, device_ids=[0, 1])
        bn.cuda()
        sync_bn.cuda()
        self._checkBatchNormResult(bn, sync_bn, torch.rand(16, 10), True, cuda=True)

    def testSyncBatchNormSyncEval(self):
        bn = nn.BatchNorm1d(10, eps=1e-05, affine=False)
        sync_bn = SynchronizedBatchNorm1d(10, eps=1e-05, affine=False)
        sync_bn = DataParallelWithCallback(sync_bn, device_ids=[0, 1])
        bn.cuda()
        sync_bn.cuda()
        self._checkBatchNormResult(bn, sync_bn, torch.rand(16, 10), False, cuda=True)

    def testSyncBatchNorm2DSyncTrain(self):
        bn = nn.BatchNorm2d(10)
        sync_bn = SynchronizedBatchNorm2d(10)
        sync_bn = DataParallelWithCallback(sync_bn, device_ids=[0, 1])
        bn.cuda()
        sync_bn.cuda()
        self._checkBatchNormResult(bn, sync_bn, torch.rand(16, 10, 16, 16), True, cuda=True)

def _checkBatchNormResult(self, bn1, bn2, input, is_train, cuda=False):
    """Check the forward and backward for the customized batch normalization."""
    bn1.train(mode=is_train)
    bn2.train(mode=is_train)
    if cuda:
        input = input.cuda()
    self._syncParameters(_find_bn(bn1), _find_bn(bn2))
    input1 = Variable(input, requires_grad=True)
    output1 = bn1(input1)
    output1.sum().backward()
    input2 = Variable(input, requires_grad=True)
    output2 = bn2(input2)
    output2.sum().backward()
    self.assertTensorClose(input1.data, input2.data)
    self.assertTensorClose(output1.data, output2.data)
    self.assertTensorClose(input1.grad, input2.grad)
    self.assertTensorClose(_find_bn(bn1).running_mean, _find_bn(bn2).running_mean)
    self.assertTensorClose(_find_bn(bn1).running_var, _find_bn(bn2).running_var)

def handy_var(a, unbias=True):
    n = a.size(0)
    asum = a.sum(dim=0)
    as_sum = (a ** 2).sum(dim=0)
    sumvar = as_sum - asum * asum / n
    if unbias:
        return sumvar / (n - 1)
    else:
        return sumvar / n

class NumericTestCase(TorchTestCase):

    def testNumericBatchNorm(self):
        a = torch.rand(16, 10)
        bn = nn.BatchNorm2d(10, momentum=1, eps=1e-05, affine=False)
        bn.train()
        a_var1 = Variable(a, requires_grad=True)
        b_var1 = bn(a_var1)
        loss1 = b_var1.sum()
        loss1.backward()
        a_var2 = Variable(a, requires_grad=True)
        a_mean2 = a_var2.mean(dim=0, keepdim=True)
        a_std2 = torch.sqrt(handy_var(a_var2, unbias=False).clamp(min=1e-05))
        b_var2 = (a_var2 - a_mean2) / a_std2
        loss2 = b_var2.sum()
        loss2.backward()
        self.assertTensorClose(bn.running_mean, a.mean(dim=0))
        self.assertTensorClose(bn.running_var, handy_var(a))
        self.assertTensorClose(a_var1.data, a_var2.data)
        self.assertTensorClose(b_var1.data, b_var2.data)
        self.assertTensorClose(a_var1.grad, a_var2.grad)

def testNumericBatchNorm(self):
    a = torch.rand(16, 10)
    bn = nn.BatchNorm2d(10, momentum=1, eps=1e-05, affine=False)
    bn.train()
    a_var1 = Variable(a, requires_grad=True)
    b_var1 = bn(a_var1)
    loss1 = b_var1.sum()
    loss1.backward()
    a_var2 = Variable(a, requires_grad=True)
    a_mean2 = a_var2.mean(dim=0, keepdim=True)
    a_std2 = torch.sqrt(handy_var(a_var2, unbias=False).clamp(min=1e-05))
    b_var2 = (a_var2 - a_mean2) / a_std2
    loss2 = b_var2.sum()
    loss2.backward()
    self.assertTensorClose(bn.running_mean, a.mean(dim=0))
    self.assertTensorClose(bn.running_var, handy_var(a))
    self.assertTensorClose(a_var1.data, a_var2.data)
    self.assertTensorClose(b_var1.data, b_var2.data)
    self.assertTensorClose(a_var1.grad, a_var2.grad)

def jittered_center_crop(frames, box_extract, box_gt, search_area_factor, output_sz, masks=None):
    """ For each frame in frames, extracts a square crop centered at box_extract, of area search_area_factor^2
    times box_extract area. The extracted crops are then resized to output_sz. Further, the co-ordinates of the box
    box_gt are transformed to the image crop co-ordinates

    args:
        frames - list of frames
        box_extract - list of boxes of same length as frames. The crops are extracted using anno_extract
        box_gt - list of boxes of same length as frames. The co-ordinates of these boxes are transformed from
                    image co-ordinates to the crop co-ordinates
        search_area_factor - The area of the extracted crop is search_area_factor^2 times box_extract area
        output_sz - The size to which the extracted crops are resized

    returns:
        list - list of image crops
        list - box_gt location in the crop co-ordinates
        """
    if masks is None:
        crops_resize_factors = [sample_target(f, a, search_area_factor, output_sz) for f, a in zip(frames, box_extract)]
        frames_crop, resize_factors, att_mask = zip(*crops_resize_factors)
        masks_crop = None
    else:
        crops_resize_factors = [sample_target(f, a, search_area_factor, output_sz, m) for f, a, m in zip(frames, box_extract, masks)]
        frames_crop, resize_factors, att_mask, masks_crop = zip(*crops_resize_factors)
    crop_sz = torch.Tensor([output_sz, output_sz])
    'Note that here we use normalized coord'
    box_crop = [transform_image_to_crop(a_gt, a_ex, rf, crop_sz, normalize=True) for a_gt, a_ex, rf in zip(box_gt, box_extract, resize_factors)]
    return (frames_crop, box_crop, att_mask, masks_crop)

def box_cxcywh_to_xyxy(x):
    x_c, y_c, w, h = x.unbind(-1)
    b = [x_c - 0.5 * w, y_c - 0.5 * h, x_c + 0.5 * w, y_c + 0.5 * h]
    return torch.stack(b, dim=-1)

def box_xywh_to_xyxy(x):
    x1, y1, w, h = x.unbind(-1)
    b = [x1, y1, x1 + w, y1 + h]
    return torch.stack(b, dim=-1)

def box_xyxy_to_xywh(x):
    x1, y1, x2, y2 = x.unbind(-1)
    b = [x1, y1, x2 - x1, y2 - y1]
    return torch.stack(b, dim=-1)

def box_xyxy_to_cxcywh(x):
    x0, y0, x1, y1 = x.unbind(-1)
    b = [(x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0]
    return torch.stack(b, dim=-1)

class CenterNetHeatMap(object):

    @staticmethod
    def generate_score_map(fmap, gt_class, gt_wh, centers_int, min_overlap):
        radius = CenterNetHeatMap.get_gaussian_radius(gt_wh, min_overlap)
        radius = torch.clamp_min(radius, 0)
        radius = radius.type(torch.int).cpu().numpy()
        for i in range(gt_class.shape[0]):
            channel_index = gt_class[i]
            CenterNetHeatMap.draw_gaussian(fmap[channel_index], centers_int[i], radius[i])

    @staticmethod
    def get_gaussian_radius(box_size, min_overlap):
        """
        copyed from CornerNet
        box_size (w, h), it could be a torch.Tensor, numpy.ndarray, list or tuple
        notice: we are using a bug-version, please refer to fix bug version in CornerNet
        """
        box_tensor = box_size
        width, height = (box_tensor[..., 0], box_tensor[..., 1])
        a1 = 1
        b1 = height + width
        c1 = width * height * (1 - min_overlap) / (1 + min_overlap)
        sq1 = torch.sqrt(b1 ** 2 - 4 * a1 * c1)
        r1 = (b1 + sq1) / 2
        a2 = 4
        b2 = 2 * (height + width)
        c2 = (1 - min_overlap) * width * height
        sq2 = torch.sqrt(b2 ** 2 - 4 * a2 * c2)
        r2 = (b2 + sq2) / 2
        a3 = 4 * min_overlap
        b3 = -2 * min_overlap * (height + width)
        c3 = (min_overlap - 1) * width * height
        sq3 = torch.sqrt(b3 ** 2 - 4 * a3 * c3)
        r3 = (b3 + sq3) / 2
        return torch.min(r1, torch.min(r2, r3))

    @staticmethod
    def gaussian2D(radius, sigma=1):
        m, n = radius
        y, x = np.ogrid[-m:m + 1, -n:n + 1]
        gauss = np.exp(-(x * x + y * y) / (2 * sigma * sigma))
        gauss[gauss < np.finfo(gauss.dtype).eps * gauss.max()] = 0
        return gauss

    @staticmethod
    def draw_gaussian(fmap, center, radius, k=1):
        diameter = 2 * radius + 1
        gaussian = CenterNetHeatMap.gaussian2D((radius, radius), sigma=diameter / 6)
        gaussian = torch.Tensor(gaussian)
        x, y = (int(center[0]), int(center[1]))
        height, width = fmap.shape[:2]
        left, right = (min(x, radius), min(width - x, radius + 1))
        top, bottom = (min(y, radius), min(height - y, radius + 1))
        masked_fmap = fmap[y - top:y + bottom, x - left:x + right]
        masked_gaussian = gaussian[radius - top:radius + bottom, radius - left:radius + right]
        if min(masked_gaussian.shape) > 0 and min(masked_fmap.shape) > 0:
            masked_fmap = torch.max(masked_fmap, masked_gaussian * k)
            fmap[y - top:y + bottom, x - left:x + right] = masked_fmap

@staticmethod
def get_gaussian_radius(box_size, min_overlap):
    """
        copyed from CornerNet
        box_size (w, h), it could be a torch.Tensor, numpy.ndarray, list or tuple
        notice: we are using a bug-version, please refer to fix bug version in CornerNet
        """
    box_tensor = box_size
    width, height = (box_tensor[..., 0], box_tensor[..., 1])
    a1 = 1
    b1 = height + width
    c1 = width * height * (1 - min_overlap) / (1 + min_overlap)
    sq1 = torch.sqrt(b1 ** 2 - 4 * a1 * c1)
    r1 = (b1 + sq1) / 2
    a2 = 4
    b2 = 2 * (height + width)
    c2 = (1 - min_overlap) * width * height
    sq2 = torch.sqrt(b2 ** 2 - 4 * a2 * c2)
    r2 = (b2 + sq2) / 2
    a3 = 4 * min_overlap
    b3 = -2 * min_overlap * (height + width)
    c3 = (min_overlap - 1) * width * height
    sq3 = torch.sqrt(b3 ** 2 - 4 * a3 * c3)
    r3 = (b3 + sq3) / 2
    return torch.min(r1, torch.min(r2, r3))

@staticmethod
def draw_gaussian(fmap, center, radius, k=1):
    diameter = 2 * radius + 1
    gaussian = CenterNetHeatMap.gaussian2D((radius, radius), sigma=diameter / 6)
    gaussian = torch.Tensor(gaussian)
    x, y = (int(center[0]), int(center[1]))
    height, width = fmap.shape[:2]
    left, right = (min(x, radius), min(width - x, radius + 1))
    top, bottom = (min(y, radius), min(height - y, radius + 1))
    masked_fmap = fmap[y - top:y + bottom, x - left:x + right]
    masked_gaussian = gaussian[radius - top:radius + bottom, radius - left:radius + right]
    if min(masked_gaussian.shape) > 0 and min(masked_fmap.shape) > 0:
        masked_fmap = torch.max(masked_fmap, masked_gaussian * k)
        fmap[y - top:y + bottom, x - left:x + right] = masked_fmap

def compute_grids(features, strides):
    """
    grids regret to the input image size
    """
    grids = []
    for level, feature in enumerate(features):
        h, w = feature.size()[-2:]
        shifts_x = torch.arange(0, w * strides[level], step=strides[level], dtype=torch.float32, device=feature.device)
        shifts_y = torch.arange(0, h * strides[level], step=strides[level], dtype=torch.float32, device=feature.device)
        shift_y, shift_x = torch.meshgrid(shifts_y, shifts_x)
        shift_x = shift_x.reshape(-1)
        shift_y = shift_y.reshape(-1)
        grids_per_level = torch.stack((shift_x, shift_y), dim=1) + strides[level] // 2
        grids.append(grids_per_level)
    return grids

def add_path(path):
    if path not in sys.path:
        sys.path.insert(0, path)

class BaseTracker:
    """Base class for all trackers."""

    def __init__(self, params):
        self.params = params
        self.visdom = None

    def predicts_segmentation_mask(self):
        return False

    def initialize(self, image, info: dict) -> dict:
        """Overload this function in your tracker. This should initialize the model."""
        raise NotImplementedError

    def track(self, image, info: dict=None) -> dict:
        """Overload this function in your tracker. This should track in the frame and update the model."""
        raise NotImplementedError

    def visdom_draw_tracking(self, image, box, segmentation=None):
        if isinstance(box, OrderedDict):
            box = [v for k, v in box.items()]
        else:
            box = (box,)
        if segmentation is None:
            self.visdom.register((image, *box), 'Tracking', 1, 'Tracking')
        else:
            self.visdom.register((image, *box, segmentation), 'Tracking', 1, 'Tracking')

    def transform_bbox_to_crop(self, box_in, resize_factor, device, box_extract=None, crop_type='template'):
        if crop_type == 'template':
            crop_sz = torch.Tensor([self.params.template_size, self.params.template_size])
        elif crop_type == 'search':
            crop_sz = torch.Tensor([self.params.search_size, self.params.search_size])
        else:
            raise NotImplementedError
        box_in = torch.tensor(box_in)
        if box_extract is None:
            box_extract = box_in
        else:
            box_extract = torch.tensor(box_extract)
        template_bbox = transform_image_to_crop(box_in, box_extract, resize_factor, crop_sz, normalize=True)
        template_bbox = template_bbox.view(1, 1, 4).to(device)
        return template_bbox

    def _init_visdom(self, visdom_info, debug):
        visdom_info = {} if visdom_info is None else visdom_info
        self.pause_mode = False
        self.step = False
        self.next_seq = False
        if debug > 0 and visdom_info.get('use_visdom', True):
            try:
                self.visdom = Visdom(debug, {'handler': self._visdom_ui_handler, 'win_id': 'Tracking'}, visdom_info=visdom_info)
            except:
                time.sleep(0.5)
                print("!!! WARNING: Visdom could not start, so using matplotlib visualization instead !!!\n!!! Start Visdom in a separate terminal window by typing 'visdom' !!!")

    def _visdom_ui_handler(self, data):
        if data['event_type'] == 'KeyPress':
            if data['key'] == ' ':
                self.pause_mode = not self.pause_mode
            elif data['key'] == 'ArrowRight' and self.pause_mode:
                self.step = True
            elif data['key'] == 'n':
                self.next_seq = True

def transform_bbox_to_crop(self, box_in, resize_factor, device, box_extract=None, crop_type='template'):
    if crop_type == 'template':
        crop_sz = torch.Tensor([self.params.template_size, self.params.template_size])
    elif crop_type == 'search':
        crop_sz = torch.Tensor([self.params.search_size, self.params.search_size])
    else:
        raise NotImplementedError
    box_in = torch.tensor(box_in)
    if box_extract is None:
        box_extract = box_in
    else:
        box_extract = torch.tensor(box_extract)
    template_bbox = transform_image_to_crop(box_in, box_extract, resize_factor, crop_sz, normalize=True)
    template_bbox = template_bbox.view(1, 1, 4).to(device)
    return template_bbox

class OSTrack(BaseTracker):

    def __init__(self, params, dataset_name):
        super(OSTrack, self).__init__(params)
        network = build_ostrack(params.cfg, training=False)
        network.load_state_dict(torch.load(self.params.checkpoint, map_location='cpu')['net'], strict=True)
        self.cfg = params.cfg
        self.network = network.cuda()
        self.network.eval()
        self.preprocessor = Preprocessor()
        self.state = None
        self.feat_sz = self.cfg.TEST.SEARCH_SIZE // self.cfg.MODEL.BACKBONE.STRIDE
        self.output_window = hann2d(torch.tensor([self.feat_sz, self.feat_sz]).long(), centered=True).cuda()
        self.debug = params.debug
        self.use_visdom = params.debug
        self.frame_id = 0
        if self.debug:
            if not self.use_visdom:
                self.save_dir = 'debug'
                if not os.path.exists(self.save_dir):
                    os.makedirs(self.save_dir)
            else:
                self._init_visdom(None, 1)
        self.save_all_boxes = params.save_all_boxes
        self.z_dict1 = {}

    def initialize(self, image, info: dict):
        z_patch_arr, resize_factor, z_amask_arr = sample_target(image, info['init_bbox'], self.params.template_factor, output_sz=self.params.template_size)
        self.z_patch_arr = z_patch_arr
        template = self.preprocessor.process(z_patch_arr, z_amask_arr)
        with torch.no_grad():
            self.z_dict1 = template
        self.box_mask_z = None
        if self.cfg.MODEL.BACKBONE.CE_LOC:
            template_bbox = self.transform_bbox_to_crop(info['init_bbox'], resize_factor, template.tensors.device).squeeze(1)
            self.box_mask_z = generate_mask_cond(self.cfg, 1, template.tensors.device, template_bbox)
        self.state = info['init_bbox']
        self.frame_id = 0
        if self.save_all_boxes:
            'save all predicted boxes'
            all_boxes_save = info['init_bbox'] * self.cfg.MODEL.NUM_OBJECT_QUERIES
            return {'all_boxes': all_boxes_save}

    def track(self, image, info: dict=None):
        H, W, _ = image.shape
        self.frame_id += 1
        x_patch_arr, resize_factor, x_amask_arr = sample_target(image, self.state, self.params.search_factor, output_sz=self.params.search_size)
        search = self.preprocessor.process(x_patch_arr, x_amask_arr)
        with torch.no_grad():
            x_dict = search
            out_dict = self.network.forward(template=self.z_dict1.tensors, search=x_dict.tensors, ce_template_mask=self.box_mask_z)
        pred_score_map = out_dict['score_map']
        response = self.output_window * pred_score_map
        pred_boxes = self.network.box_head.cal_bbox(response, out_dict['size_map'], out_dict['offset_map'])
        pred_boxes = pred_boxes.view(-1, 4)
        pred_box = (pred_boxes.mean(dim=0) * self.params.search_size / resize_factor).tolist()
        self.state = clip_box(self.map_box_back(pred_box, resize_factor), H, W, margin=10)
        if self.debug:
            if not self.use_visdom:
                x1, y1, w, h = self.state
                image_BGR = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                cv2.rectangle(image_BGR, (int(x1), int(y1)), (int(x1 + w), int(y1 + h)), color=(0, 0, 255), thickness=2)
                save_path = os.path.join(self.save_dir, '%04d.jpg' % self.frame_id)
                cv2.imwrite(save_path, image_BGR)
            else:
                self.visdom.register((image, info['gt_bbox'].tolist(), self.state), 'Tracking', 1, 'Tracking')
                self.visdom.register(torch.from_numpy(x_patch_arr).permute(2, 0, 1), 'image', 1, 'search_region')
                self.visdom.register(torch.from_numpy(self.z_patch_arr).permute(2, 0, 1), 'image', 1, 'template')
                self.visdom.register(pred_score_map.view(self.feat_sz, self.feat_sz), 'heatmap', 1, 'score_map')
                self.visdom.register((pred_score_map * self.output_window).view(self.feat_sz, self.feat_sz), 'heatmap', 1, 'score_map_hann')
                if 'removed_indexes_s' in out_dict and out_dict['removed_indexes_s']:
                    removed_indexes_s = out_dict['removed_indexes_s']
                    removed_indexes_s = [removed_indexes_s_i.cpu().numpy() for removed_indexes_s_i in removed_indexes_s]
                    masked_search = gen_visualization(x_patch_arr, removed_indexes_s)
                    self.visdom.register(torch.from_numpy(masked_search).permute(2, 0, 1), 'image', 1, 'masked_search')
                while self.pause_mode:
                    if self.step:
                        self.step = False
                        break
        if self.save_all_boxes:
            'save all predictions'
            all_boxes = self.map_box_back_batch(pred_boxes * self.params.search_size / resize_factor, resize_factor)
            all_boxes_save = all_boxes.view(-1).tolist()
            return {'target_bbox': self.state, 'all_boxes': all_boxes_save}
        else:
            return {'target_bbox': self.state}

    def map_box_back(self, pred_box: list, resize_factor: float):
        cx_prev, cy_prev = (self.state[0] + 0.5 * self.state[2], self.state[1] + 0.5 * self.state[3])
        cx, cy, w, h = pred_box
        half_side = 0.5 * self.params.search_size / resize_factor
        cx_real = cx + (cx_prev - half_side)
        cy_real = cy + (cy_prev - half_side)
        return [cx_real - 0.5 * w, cy_real - 0.5 * h, w, h]

    def map_box_back_batch(self, pred_box: torch.Tensor, resize_factor: float):
        cx_prev, cy_prev = (self.state[0] + 0.5 * self.state[2], self.state[1] + 0.5 * self.state[3])
        cx, cy, w, h = pred_box.unbind(-1)
        half_side = 0.5 * self.params.search_size / resize_factor
        cx_real = cx + (cx_prev - half_side)
        cy_real = cy + (cy_prev - half_side)
        return torch.stack([cx_real - 0.5 * w, cy_real - 0.5 * h, w, h], dim=-1)

    def add_hook(self):
        conv_features, enc_attn_weights, dec_attn_weights = ([], [], [])
        for i in range(12):
            self.network.backbone.blocks[i].attn.register_forward_hook(lambda self, input, output: enc_attn_weights.append(output[1]))
        self.enc_attn_weights = enc_attn_weights

def initialize(self, image, info: dict):
    z_patch_arr, resize_factor, z_amask_arr = sample_target(image, info['init_bbox'], self.params.template_factor, output_sz=self.params.template_size)
    self.z_patch_arr = z_patch_arr
    template = self.preprocessor.process(z_patch_arr, z_amask_arr)
    with torch.no_grad():
        self.z_dict1 = template
    self.box_mask_z = None
    if self.cfg.MODEL.BACKBONE.CE_LOC:
        template_bbox = self.transform_bbox_to_crop(info['init_bbox'], resize_factor, template.tensors.device).squeeze(1)
        self.box_mask_z = generate_mask_cond(self.cfg, 1, template.tensors.device, template_bbox)
    self.state = info['init_bbox']
    self.frame_id = 0
    if self.save_all_boxes:
        'save all predicted boxes'
        all_boxes_save = info['init_bbox'] * self.cfg.MODEL.NUM_OBJECT_QUERIES
        return {'all_boxes': all_boxes_save}

def map_box_back_batch(self, pred_box: torch.Tensor, resize_factor: float):
    cx_prev, cy_prev = (self.state[0] + 0.5 * self.state[2], self.state[1] + 0.5 * self.state[3])
    cx, cy, w, h = pred_box.unbind(-1)
    half_side = 0.5 * self.params.search_size / resize_factor
    cx_real = cx + (cx_prev - half_side)
    cy_real = cy + (cy_prev - half_side)
    return torch.stack([cx_real - 0.5 * w, cy_real - 0.5 * h, w, h], dim=-1)

class VisionTransformer(BaseBackbone):
    """ Vision Transformer
    A PyTorch impl of : `An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale`
        - https://arxiv.org/abs/2010.11929
    Includes distillation token & head support for `DeiT: Data-efficient Image Transformers`
        - https://arxiv.org/abs/2012.12877
    """

    def __init__(self, img_size=224, patch_size=16, in_chans=3, num_classes=1000, embed_dim=768, depth=12, num_heads=12, mlp_ratio=4.0, qkv_bias=True, representation_size=None, distilled=False, drop_rate=0.0, attn_drop_rate=0.0, drop_path_rate=0.0, embed_layer=PatchEmbed, norm_layer=None, act_layer=None, weight_init=''):
        """
        Args:
            img_size (int, tuple): input image size
            patch_size (int, tuple): patch size
            in_chans (int): number of input channels
            num_classes (int): number of classes for classification head
            embed_dim (int): embedding dimension
            depth (int): depth of transformer
            num_heads (int): number of attention heads
            mlp_ratio (int): ratio of mlp hidden dim to embedding dim
            qkv_bias (bool): enable bias for qkv if True
            representation_size (Optional[int]): enable and set representation layer (pre-logits) to this value if set
            distilled (bool): model includes a distillation token and head as in DeiT models
            drop_rate (float): dropout rate
            attn_drop_rate (float): attention dropout rate
            drop_path_rate (float): stochastic depth rate
            embed_layer (nn.Module): patch embedding layer
            norm_layer: (nn.Module): normalization layer
            weight_init: (str): weight init scheme
        """
        super().__init__()
        self.num_classes = num_classes
        self.num_features = self.embed_dim = embed_dim
        self.num_tokens = 2 if distilled else 1
        norm_layer = norm_layer or partial(nn.LayerNorm, eps=1e-06)
        act_layer = act_layer or nn.GELU
        self.patch_embed = embed_layer(img_size=img_size, patch_size=patch_size, in_chans=in_chans, embed_dim=embed_dim)
        num_patches = self.patch_embed.num_patches
        self.cls_token = nn.Parameter(torch.zeros(1, 1, embed_dim))
        self.dist_token = nn.Parameter(torch.zeros(1, 1, embed_dim)) if distilled else None
        self.pos_embed = nn.Parameter(torch.zeros(1, num_patches + self.num_tokens, embed_dim))
        self.pos_drop = nn.Dropout(p=drop_rate)
        dpr = [x.item() for x in torch.linspace(0, drop_path_rate, depth)]
        self.blocks = nn.Sequential(*[Block(dim=embed_dim, num_heads=num_heads, mlp_ratio=mlp_ratio, qkv_bias=qkv_bias, drop=drop_rate, attn_drop=attn_drop_rate, drop_path=dpr[i], norm_layer=norm_layer, act_layer=act_layer) for i in range(depth)])
        self.norm = norm_layer(embed_dim)
        self.init_weights(weight_init)

    def init_weights(self, mode=''):
        assert mode in ('jax', 'jax_nlhb', 'nlhb', '')
        head_bias = -math.log(self.num_classes) if 'nlhb' in mode else 0.0
        trunc_normal_(self.pos_embed, std=0.02)
        if self.dist_token is not None:
            trunc_normal_(self.dist_token, std=0.02)
        if mode.startswith('jax'):
            named_apply(partial(_init_vit_weights, head_bias=head_bias, jax_impl=True), self)
        else:
            trunc_normal_(self.cls_token, std=0.02)
            self.apply(_init_vit_weights)

    def _init_weights(self, m):
        _init_vit_weights(m)

    @torch.jit.ignore()
    def load_pretrained(self, checkpoint_path, prefix=''):
        _load_weights(self, checkpoint_path, prefix)

    @torch.jit.ignore
    def no_weight_decay(self):
        return {'pos_embed', 'cls_token', 'dist_token'}

    def get_classifier(self):
        if self.dist_token is None:
            return self.head
        else:
            return (self.head, self.head_dist)

    def reset_classifier(self, num_classes, global_pool=''):
        self.num_classes = num_classes
        self.head = nn.Linear(self.embed_dim, num_classes) if num_classes > 0 else nn.Identity()
        if self.num_tokens == 2:
            self.head_dist = nn.Linear(self.embed_dim, self.num_classes) if num_classes > 0 else nn.Identity()

def init_weights(self, mode=''):
    assert mode in ('jax', 'jax_nlhb', 'nlhb', '')
    head_bias = -math.log(self.num_classes) if 'nlhb' in mode else 0.0
    trunc_normal_(self.pos_embed, std=0.02)
    if self.dist_token is not None:
        trunc_normal_(self.dist_token, std=0.02)
    if mode.startswith('jax'):
        named_apply(partial(_init_vit_weights, head_bias=head_bias, jax_impl=True), self)
    else:
        trunc_normal_(self.cls_token, std=0.02)
        self.apply(_init_vit_weights)

def resize_pos_embed(posemb, posemb_new, num_tokens=1, gs_new=()):
    print('Resized position embedding: %s to %s', posemb.shape, posemb_new.shape)
    ntok_new = posemb_new.shape[1]
    if num_tokens:
        posemb_tok, posemb_grid = (posemb[:, :num_tokens], posemb[0, num_tokens:])
        ntok_new -= num_tokens
    else:
        posemb_tok, posemb_grid = (posemb[:, :0], posemb[0])
    gs_old = int(math.sqrt(len(posemb_grid)))
    if not len(gs_new):
        gs_new = [int(math.sqrt(ntok_new))] * 2
    assert len(gs_new) >= 2
    print('Position embedding grid-size from %s to %s', [gs_old, gs_old], gs_new)
    posemb_grid = posemb_grid.reshape(1, gs_old, gs_old, -1).permute(0, 3, 1, 2)
    posemb_grid = F.interpolate(posemb_grid, size=gs_new, mode='bilinear')
    posemb_grid = posemb_grid.permute(0, 2, 3, 1).reshape(1, gs_new[0] * gs_new[1], -1)
    posemb = torch.cat([posemb_tok, posemb_grid], dim=1)
    return posemb

class Corner_Predictor(nn.Module):
    """ Corner Predictor module"""

    def __init__(self, inplanes=64, channel=256, feat_sz=20, stride=16, freeze_bn=False):
        super(Corner_Predictor, self).__init__()
        self.feat_sz = feat_sz
        self.stride = stride
        self.img_sz = self.feat_sz * self.stride
        'top-left corner'
        self.conv1_tl = conv(inplanes, channel, freeze_bn=freeze_bn)
        self.conv2_tl = conv(channel, channel // 2, freeze_bn=freeze_bn)
        self.conv3_tl = conv(channel // 2, channel // 4, freeze_bn=freeze_bn)
        self.conv4_tl = conv(channel // 4, channel // 8, freeze_bn=freeze_bn)
        self.conv5_tl = nn.Conv2d(channel // 8, 1, kernel_size=1)
        'bottom-right corner'
        self.conv1_br = conv(inplanes, channel, freeze_bn=freeze_bn)
        self.conv2_br = conv(channel, channel // 2, freeze_bn=freeze_bn)
        self.conv3_br = conv(channel // 2, channel // 4, freeze_bn=freeze_bn)
        self.conv4_br = conv(channel // 4, channel // 8, freeze_bn=freeze_bn)
        self.conv5_br = nn.Conv2d(channel // 8, 1, kernel_size=1)
        'about coordinates and indexs'
        with torch.no_grad():
            self.indice = torch.arange(0, self.feat_sz).view(-1, 1) * self.stride
            self.coord_x = self.indice.repeat((self.feat_sz, 1)).view((self.feat_sz * self.feat_sz,)).float().cuda()
            self.coord_y = self.indice.repeat((1, self.feat_sz)).view((self.feat_sz * self.feat_sz,)).float().cuda()

    def forward(self, x, return_dist=False, softmax=True):
        """ Forward pass with input x. """
        score_map_tl, score_map_br = self.get_score_map(x)
        if return_dist:
            coorx_tl, coory_tl, prob_vec_tl = self.soft_argmax(score_map_tl, return_dist=True, softmax=softmax)
            coorx_br, coory_br, prob_vec_br = self.soft_argmax(score_map_br, return_dist=True, softmax=softmax)
            return (torch.stack((coorx_tl, coory_tl, coorx_br, coory_br), dim=1) / self.img_sz, prob_vec_tl, prob_vec_br)
        else:
            coorx_tl, coory_tl = self.soft_argmax(score_map_tl)
            coorx_br, coory_br = self.soft_argmax(score_map_br)
            return torch.stack((coorx_tl, coory_tl, coorx_br, coory_br), dim=1) / self.img_sz

    def get_score_map(self, x):
        x_tl1 = self.conv1_tl(x)
        x_tl2 = self.conv2_tl(x_tl1)
        x_tl3 = self.conv3_tl(x_tl2)
        x_tl4 = self.conv4_tl(x_tl3)
        score_map_tl = self.conv5_tl(x_tl4)
        x_br1 = self.conv1_br(x)
        x_br2 = self.conv2_br(x_br1)
        x_br3 = self.conv3_br(x_br2)
        x_br4 = self.conv4_br(x_br3)
        score_map_br = self.conv5_br(x_br4)
        return (score_map_tl, score_map_br)

    def soft_argmax(self, score_map, return_dist=False, softmax=True):
        """ get soft-argmax coordinate for a given heatmap """
        score_vec = score_map.view((-1, self.feat_sz * self.feat_sz))
        prob_vec = nn.functional.softmax(score_vec, dim=1)
        exp_x = torch.sum(self.coord_x * prob_vec, dim=1)
        exp_y = torch.sum(self.coord_y * prob_vec, dim=1)
        if return_dist:
            if softmax:
                return (exp_x, exp_y, prob_vec)
            else:
                return (exp_x, exp_y, score_vec)
        else:
            return (exp_x, exp_y)

def forward(self, x, return_dist=False, softmax=True):
    """ Forward pass with input x. """
    score_map_tl, score_map_br = self.get_score_map(x)
    if return_dist:
        coorx_tl, coory_tl, prob_vec_tl = self.soft_argmax(score_map_tl, return_dist=True, softmax=softmax)
        coorx_br, coory_br, prob_vec_br = self.soft_argmax(score_map_br, return_dist=True, softmax=softmax)
        return (torch.stack((coorx_tl, coory_tl, coorx_br, coory_br), dim=1) / self.img_sz, prob_vec_tl, prob_vec_br)
    else:
        coorx_tl, coory_tl = self.soft_argmax(score_map_tl)
        coorx_br, coory_br = self.soft_argmax(score_map_br)
        return torch.stack((coorx_tl, coory_tl, coorx_br, coory_br), dim=1) / self.img_sz

class CenterPredictor(nn.Module):

    def __init__(self, inplanes=64, channel=256, feat_sz=20, stride=16, freeze_bn=False):
        super(CenterPredictor, self).__init__()
        self.feat_sz = feat_sz
        self.stride = stride
        self.img_sz = self.feat_sz * self.stride
        self.conv1_ctr = conv(inplanes, channel, freeze_bn=freeze_bn)
        self.conv2_ctr = conv(channel, channel // 2, freeze_bn=freeze_bn)
        self.conv3_ctr = conv(channel // 2, channel // 4, freeze_bn=freeze_bn)
        self.conv4_ctr = conv(channel // 4, channel // 8, freeze_bn=freeze_bn)
        self.conv5_ctr = nn.Conv2d(channel // 8, 1, kernel_size=1)
        self.conv1_offset = conv(inplanes, channel, freeze_bn=freeze_bn)
        self.conv2_offset = conv(channel, channel // 2, freeze_bn=freeze_bn)
        self.conv3_offset = conv(channel // 2, channel // 4, freeze_bn=freeze_bn)
        self.conv4_offset = conv(channel // 4, channel // 8, freeze_bn=freeze_bn)
        self.conv5_offset = nn.Conv2d(channel // 8, 2, kernel_size=1)
        self.conv1_size = conv(inplanes, channel, freeze_bn=freeze_bn)
        self.conv2_size = conv(channel, channel // 2, freeze_bn=freeze_bn)
        self.conv3_size = conv(channel // 2, channel // 4, freeze_bn=freeze_bn)
        self.conv4_size = conv(channel // 4, channel // 8, freeze_bn=freeze_bn)
        self.conv5_size = nn.Conv2d(channel // 8, 2, kernel_size=1)
        for p in self.parameters():
            if p.dim() > 1:
                nn.init.xavier_uniform_(p)

    def forward(self, x, gt_score_map=None):
        """ Forward pass with input x. """
        score_map_ctr, size_map, offset_map = self.get_score_map(x)
        if gt_score_map is None:
            bbox = self.cal_bbox(score_map_ctr, size_map, offset_map)
        else:
            bbox = self.cal_bbox(gt_score_map.unsqueeze(1), size_map, offset_map)
        return (score_map_ctr, bbox, size_map, offset_map)

    def cal_bbox(self, score_map_ctr, size_map, offset_map, return_score=False):
        max_score, idx = torch.max(score_map_ctr.flatten(1), dim=1, keepdim=True)
        idx_y = idx // self.feat_sz
        idx_x = idx % self.feat_sz
        idx = idx.unsqueeze(1).expand(idx.shape[0], 2, 1)
        size = size_map.flatten(2).gather(dim=2, index=idx)
        offset = offset_map.flatten(2).gather(dim=2, index=idx).squeeze(-1)
        bbox = torch.cat([(idx_x.to(torch.float) + offset[:, :1]) / self.feat_sz, (idx_y.to(torch.float) + offset[:, 1:]) / self.feat_sz, size.squeeze(-1)], dim=1)
        if return_score:
            return (bbox, max_score)
        return bbox

    def get_pred(self, score_map_ctr, size_map, offset_map):
        max_score, idx = torch.max(score_map_ctr.flatten(1), dim=1, keepdim=True)
        idx_y = idx // self.feat_sz
        idx_x = idx % self.feat_sz
        idx = idx.unsqueeze(1).expand(idx.shape[0], 2, 1)
        size = size_map.flatten(2).gather(dim=2, index=idx)
        offset = offset_map.flatten(2).gather(dim=2, index=idx).squeeze(-1)
        return (size * self.feat_sz, offset)

    def get_score_map(self, x):

        def _sigmoid(x):
            y = torch.clamp(x.sigmoid_(), min=0.0001, max=1 - 0.0001)
            return y
        x_ctr1 = self.conv1_ctr(x)
        x_ctr2 = self.conv2_ctr(x_ctr1)
        x_ctr3 = self.conv3_ctr(x_ctr2)
        x_ctr4 = self.conv4_ctr(x_ctr3)
        score_map_ctr = self.conv5_ctr(x_ctr4)
        x_offset1 = self.conv1_offset(x)
        x_offset2 = self.conv2_offset(x_offset1)
        x_offset3 = self.conv3_offset(x_offset2)
        x_offset4 = self.conv4_offset(x_offset3)
        score_map_offset = self.conv5_offset(x_offset4)
        x_size1 = self.conv1_size(x)
        x_size2 = self.conv2_size(x_size1)
        x_size3 = self.conv3_size(x_size2)
        x_size4 = self.conv4_size(x_size3)
        score_map_size = self.conv5_size(x_size4)
        return (_sigmoid(score_map_ctr), _sigmoid(score_map_size), score_map_offset)

def forward(self, x, gt_score_map=None):
    """ Forward pass with input x. """
    score_map_ctr, size_map, offset_map = self.get_score_map(x)
    if gt_score_map is None:
        bbox = self.cal_bbox(score_map_ctr, size_map, offset_map)
    else:
        bbox = self.cal_bbox(gt_score_map.unsqueeze(1), size_map, offset_map)
    return (score_map_ctr, bbox, size_map, offset_map)

def add_path(path):
    if path not in sys.path:
        sys.path.insert(0, path)

class LambdaWarmUpCosineScheduler2:
    """
    supports repeated iterations, configurable via lists
    note: use with a base_lr of 1.0.
    """

    def __init__(self, warm_up_steps, f_min, f_max, f_start, cycle_lengths, verbosity_interval=0):
        assert len(warm_up_steps) == len(f_min) == len(f_max) == len(f_start) == len(cycle_lengths)
        self.lr_warm_up_steps = warm_up_steps
        self.f_start = f_start
        self.f_min = f_min
        self.f_max = f_max
        self.cycle_lengths = cycle_lengths
        self.cum_cycles = np.cumsum([0] + list(self.cycle_lengths))
        self.last_f = 0.0
        self.verbosity_interval = verbosity_interval

    def find_in_interval(self, n):
        interval = 0
        for cl in self.cum_cycles[1:]:
            if n <= cl:
                return interval
            interval += 1

    def schedule(self, n, **kwargs):
        cycle = self.find_in_interval(n)
        n = n - self.cum_cycles[cycle]
        if self.verbosity_interval > 0:
            if n % self.verbosity_interval == 0:
                print(f'current step: {n}, recent lr-multiplier: {self.last_f}, current cycle {cycle}')
        if n < self.lr_warm_up_steps[cycle]:
            f = (self.f_max[cycle] - self.f_start[cycle]) / self.lr_warm_up_steps[cycle] * n + self.f_start[cycle]
            self.last_f = f
            return f
        else:
            t = (n - self.lr_warm_up_steps[cycle]) / (self.cycle_lengths[cycle] - self.lr_warm_up_steps[cycle])
            t = min(t, 1.0)
            f = self.f_min[cycle] + 0.5 * (self.f_max[cycle] - self.f_min[cycle]) * (1 + np.cos(t * np.pi))
            self.last_f = f
            return f

    def __call__(self, n, **kwargs):
        return self.schedule(n, **kwargs)

def __init__(self, warm_up_steps, f_min, f_max, f_start, cycle_lengths, verbosity_interval=0):
    assert len(warm_up_steps) == len(f_min) == len(f_max) == len(f_start) == len(cycle_lengths)
    self.lr_warm_up_steps = warm_up_steps
    self.f_start = f_start
    self.f_min = f_min
    self.f_max = f_max
    self.cycle_lengths = cycle_lengths
    self.cum_cycles = np.cumsum([0] + list(self.cycle_lengths))
    self.last_f = 0.0
    self.verbosity_interval = verbosity_interval

def init_(tensor):
    dim = tensor.shape[-1]
    std = 1 / math.sqrt(dim)
    tensor.uniform_(-std, std)
    return tensor

class DiagonalGaussianDistribution(object):

    def __init__(self, parameters, deterministic=False):
        self.parameters = parameters
        self.mean, self.logvar = torch.chunk(parameters, 2, dim=1)
        self.logvar = torch.clamp(self.logvar, -30.0, 20.0)
        self.deterministic = deterministic
        self.std = torch.exp(0.5 * self.logvar)
        self.var = torch.exp(self.logvar)
        if self.deterministic:
            self.var = self.std = torch.zeros_like(self.mean).to(device=self.parameters.device)

    def sample(self):
        x = self.mean + self.std * torch.randn(self.mean.shape).to(device=self.parameters.device)
        return x

    def kl(self, other=None):
        if self.deterministic:
            return torch.Tensor([0.0])
        elif other is None:
            return 0.5 * torch.sum(torch.pow(self.mean, 2) + self.var - 1.0 - self.logvar, dim=[1, 2, 3])
        else:
            return 0.5 * torch.sum(torch.pow(self.mean - other.mean, 2) / other.var + self.var / other.var - 1.0 - self.logvar + other.logvar, dim=[1, 2, 3])

    def nll(self, sample, dims=[1, 2, 3]):
        if self.deterministic:
            return torch.Tensor([0.0])
        logtwopi = np.log(2.0 * np.pi)
        return 0.5 * torch.sum(logtwopi + self.logvar + torch.pow(sample - self.mean, 2) / self.var, dim=dims)

    def mode(self):
        return self.mean

def kl(self, other=None):
    if self.deterministic:
        return torch.Tensor([0.0])
    elif other is None:
        return 0.5 * torch.sum(torch.pow(self.mean, 2) + self.var - 1.0 - self.logvar, dim=[1, 2, 3])
    else:
        return 0.5 * torch.sum(torch.pow(self.mean - other.mean, 2) / other.var + self.var / other.var - 1.0 - self.logvar + other.logvar, dim=[1, 2, 3])

def nll(self, sample, dims=[1, 2, 3]):
    if self.deterministic:
        return torch.Tensor([0.0])
    logtwopi = np.log(2.0 * np.pi)
    return 0.5 * torch.sum(logtwopi + self.logvar + torch.pow(sample - self.mean, 2) / self.var, dim=dims)

def hinge_d_loss_with_exemplar_weights(logits_real, logits_fake, weights):
    assert weights.shape[0] == logits_real.shape[0] == logits_fake.shape[0]
    loss_real = torch.mean(F.relu(1.0 - logits_real), dim=[1, 2, 3])
    loss_fake = torch.mean(F.relu(1.0 + logits_fake), dim=[1, 2, 3])
    loss_real = (weights * loss_real).sum() / weights.sum()
    loss_fake = (weights * loss_fake).sum() / weights.sum()
    d_loss = 0.5 * (loss_real + loss_fake)
    return d_loss

def gm_blur_kernel(mean, cov, size=15):
    center = size / 2.0 + 0.5
    k = np.zeros([size, size])
    for y in range(size):
        for x in range(size):
            cy = y - center + 1
            cx = x - center + 1
            k[y, x] = ss.multivariate_normal.pdf([cx, cy], mean=mean, cov=cov)
    k = k / np.sum(k)
    return k

def cubic(x):
    absx = torch.abs(x)
    absx2 = absx ** 2
    absx3 = absx ** 3
    return (1.5 * absx3 - 2.5 * absx2 + 1) * (absx <= 1).type_as(absx) + (-0.5 * absx3 + 2.5 * absx2 - 4 * absx + 2) * ((absx > 1) * (absx <= 2)).type_as(absx)

def gm_blur_kernel(mean, cov, size=15):
    center = size / 2.0 + 0.5
    k = np.zeros([size, size])
    for y in range(size):
        for x in range(size):
            cy = y - center + 1
            cx = x - center + 1
            k[y, x] = ss.multivariate_normal.pdf([cx, cy], mean=mean, cov=cov)
    k = k / np.sum(k)
    return k

def count_flops_attn(model, _x, y):
    """
    A counter for the `thop` package to count the operations in an
    attention operation.
    Meant to be used like:
        macs, params = thop.profile(
            model,
            inputs=(inputs, timestamps),
            custom_ops={QKVAttention: QKVAttention.count_flops},
        )
    """
    b, c, *spatial = y[0].shape
    num_spatial = int(np.prod(spatial))
    matmul_ops = 2 * b * num_spatial ** 2 * c
    model.total_ops += th.DoubleTensor([matmul_ops])

class UNetModel(nn.Module):
    """
    The full UNet model with attention and timestep embedding.
    :param in_channels: channels in the input Tensor.
    :param model_channels: base channel count for the model.
    :param out_channels: channels in the output Tensor.
    :param num_res_blocks: number of residual blocks per downsample.
    :param attention_resolutions: a collection of downsample rates at which
        attention will take place. May be a set, list, or tuple.
        For example, if this contains 4, then at 4x downsampling, attention
        will be used.
    :param dropout: the dropout probability.
    :param channel_mult: channel multiplier for each level of the UNet.
    :param conv_resample: if True, use learned convolutions for upsampling and
        downsampling.
    :param dims: determines if the signal is 1D, 2D, or 3D.
    :param num_classes: if specified (as an int), then this model will be
        class-conditional with `num_classes` classes.
    :param use_checkpoint: use gradient checkpointing to reduce memory usage.
    :param num_heads: the number of attention heads in each attention layer.
    :param num_heads_channels: if specified, ignore num_heads and instead use
                               a fixed channel width per attention head.
    :param num_heads_upsample: works with num_heads to set a different number
                               of heads for upsampling. Deprecated.
    :param use_scale_shift_norm: use a FiLM-like conditioning mechanism.
    :param resblock_updown: use residual blocks for up/downsampling.
    :param use_new_attention_order: use a different attention pattern for potentially
                                    increased efficiency.
    """

    def __init__(self, image_size, in_channels, model_channels, out_channels, num_res_blocks, attention_resolutions, dropout=0, channel_mult=(1, 2, 4, 8), conv_resample=True, dims=2, num_classes=None, use_checkpoint=False, use_fp16=False, num_heads=-1, num_head_channels=-1, num_heads_upsample=-1, use_scale_shift_norm=False, resblock_updown=False, use_new_attention_order=False, use_spatial_transformer=False, transformer_depth=1, context_dim=None, n_embed=None, legacy=True):
        super().__init__()
        if use_spatial_transformer:
            assert context_dim is not None, 'Fool!! You forgot to include the dimension of your cross-attention conditioning...'
        if context_dim is not None:
            assert use_spatial_transformer, 'Fool!! You forgot to use the spatial transformer for your cross-attention conditioning...'
            from omegaconf.listconfig import ListConfig
            if type(context_dim) == ListConfig:
                context_dim = list(context_dim)
        if num_heads_upsample == -1:
            num_heads_upsample = num_heads
        if num_heads == -1:
            assert num_head_channels != -1, 'Either num_heads or num_head_channels has to be set'
        if num_head_channels == -1:
            assert num_heads != -1, 'Either num_heads or num_head_channels has to be set'
        self.image_size = image_size
        self.in_channels = in_channels
        self.model_channels = model_channels
        self.out_channels = out_channels
        self.num_res_blocks = num_res_blocks
        self.attention_resolutions = attention_resolutions
        self.dropout = dropout
        self.channel_mult = channel_mult
        self.conv_resample = conv_resample
        self.num_classes = num_classes
        self.use_checkpoint = use_checkpoint
        self.dtype = th.float16 if use_fp16 else th.float32
        self.num_heads = num_heads
        self.num_head_channels = num_head_channels
        self.num_heads_upsample = num_heads_upsample
        self.predict_codebook_ids = n_embed is not None
        time_embed_dim = model_channels * 4
        self.time_embed = nn.Sequential(linear(model_channels, time_embed_dim), nn.SiLU(), linear(time_embed_dim, time_embed_dim))
        if self.num_classes is not None:
            self.label_emb = nn.Embedding(num_classes, time_embed_dim)
        self.input_blocks = nn.ModuleList([TimestepEmbedSequential(conv_nd(dims, in_channels, model_channels, 3, padding=1))])
        self._feature_size = model_channels
        input_block_chans = [model_channels]
        ch = model_channels
        ds = 1
        for level, mult in enumerate(channel_mult):
            for _ in range(num_res_blocks):
                layers = [ResBlock(ch, time_embed_dim, dropout, out_channels=mult * model_channels, dims=dims, use_checkpoint=use_checkpoint, use_scale_shift_norm=use_scale_shift_norm)]
                ch = mult * model_channels
                if ds in attention_resolutions:
                    if num_head_channels == -1:
                        dim_head = ch // num_heads
                    else:
                        num_heads = ch // num_head_channels
                        dim_head = num_head_channels
                    if legacy:
                        dim_head = ch // num_heads if use_spatial_transformer else num_head_channels
                    layers.append(AttentionBlock(ch, use_checkpoint=use_checkpoint, num_heads=num_heads, num_head_channels=dim_head, use_new_attention_order=use_new_attention_order) if not use_spatial_transformer else SpatialTransformer(ch, num_heads, dim_head, depth=transformer_depth, context_dim=context_dim))
                self.input_blocks.append(TimestepEmbedSequential(*layers))
                self._feature_size += ch
                input_block_chans.append(ch)
            if level != len(channel_mult) - 1:
                out_ch = ch
                self.input_blocks.append(TimestepEmbedSequential(ResBlock(ch, time_embed_dim, dropout, out_channels=out_ch, dims=dims, use_checkpoint=use_checkpoint, use_scale_shift_norm=use_scale_shift_norm, down=True) if resblock_updown else Downsample(ch, conv_resample, dims=dims, out_channels=out_ch)))
                ch = out_ch
                input_block_chans.append(ch)
                ds *= 2
                self._feature_size += ch
        if num_head_channels == -1:
            dim_head = ch // num_heads
        else:
            num_heads = ch // num_head_channels
            dim_head = num_head_channels
        if legacy:
            dim_head = ch // num_heads if use_spatial_transformer else num_head_channels
        self.middle_block = TimestepEmbedSequential(ResBlock(ch, time_embed_dim, dropout, dims=dims, use_checkpoint=use_checkpoint, use_scale_shift_norm=use_scale_shift_norm), AttentionBlock(ch, use_checkpoint=use_checkpoint, num_heads=num_heads, num_head_channels=dim_head, use_new_attention_order=use_new_attention_order) if not use_spatial_transformer else SpatialTransformer(ch, num_heads, dim_head, depth=transformer_depth, context_dim=context_dim), ResBlock(ch, time_embed_dim, dropout, dims=dims, use_checkpoint=use_checkpoint, use_scale_shift_norm=use_scale_shift_norm))
        self._feature_size += ch
        self.output_blocks = nn.ModuleList([])
        for level, mult in list(enumerate(channel_mult))[::-1]:
            for i in range(num_res_blocks + 1):
                ich = input_block_chans.pop()
                layers = [ResBlock(ch + ich, time_embed_dim, dropout, out_channels=model_channels * mult, dims=dims, use_checkpoint=use_checkpoint, use_scale_shift_norm=use_scale_shift_norm)]
                ch = model_channels * mult
                if ds in attention_resolutions:
                    if num_head_channels == -1:
                        dim_head = ch // num_heads
                    else:
                        num_heads = ch // num_head_channels
                        dim_head = num_head_channels
                    if legacy:
                        dim_head = ch // num_heads if use_spatial_transformer else num_head_channels
                    layers.append(AttentionBlock(ch, use_checkpoint=use_checkpoint, num_heads=num_heads_upsample, num_head_channels=dim_head, use_new_attention_order=use_new_attention_order) if not use_spatial_transformer else SpatialTransformer(ch, num_heads, dim_head, depth=transformer_depth, context_dim=context_dim))
                if level and i == num_res_blocks:
                    out_ch = ch
                    layers.append(ResBlock(ch, time_embed_dim, dropout, out_channels=out_ch, dims=dims, use_checkpoint=use_checkpoint, use_scale_shift_norm=use_scale_shift_norm, up=True) if resblock_updown else Upsample(ch, conv_resample, dims=dims, out_channels=out_ch))
                    ds //= 2
                self.output_blocks.append(TimestepEmbedSequential(*layers))
                self._feature_size += ch
        self.out = nn.Sequential(normalization(ch), nn.SiLU(), zero_module(conv_nd(dims, model_channels, out_channels, 3, padding=1)))
        if self.predict_codebook_ids:
            self.id_predictor = nn.Sequential(normalization(ch), conv_nd(dims, model_channels, n_embed, 1))

    def convert_to_fp16(self):
        """
        Convert the torso of the model to float16.
        """
        self.input_blocks.apply(convert_module_to_f16)
        self.middle_block.apply(convert_module_to_f16)
        self.output_blocks.apply(convert_module_to_f16)

    def convert_to_fp32(self):
        """
        Convert the torso of the model to float32.
        """
        self.input_blocks.apply(convert_module_to_f32)
        self.middle_block.apply(convert_module_to_f32)
        self.output_blocks.apply(convert_module_to_f32)

    def forward(self, x, timesteps=None, context=None, y=None, **kwargs):
        """
        Apply the model to an input batch.
        :param x: an [N x C x ...] Tensor of inputs.
        :param timesteps: a 1-D batch of timesteps.
        :param context: conditioning plugged in via crossattn
        :param y: an [N] Tensor of labels, if class-conditional.
        :return: an [N x C x ...] Tensor of outputs.
        """
        assert (y is not None) == (self.num_classes is not None), 'must specify y if and only if the model is class-conditional'
        hs = []
        t_emb = timestep_embedding(timesteps, self.model_channels, repeat_only=False)
        emb = self.time_embed(t_emb)
        if self.num_classes is not None:
            assert y.shape == (x.shape[0],)
            emb = emb + self.label_emb(y)
        h = x.type(self.dtype)
        for module in self.input_blocks:
            h = module(h, emb, context)
            hs.append(h)
        h = self.middle_block(h, emb, context)
        for module in self.output_blocks:
            h = th.cat([h, hs.pop()], dim=1)
            h = module(h, emb, context)
        h = h.type(x.dtype)
        if self.predict_codebook_ids:
            return self.id_predictor(h)
        else:
            return self.out(h)

def convert_to_fp16(self):
    """
        Convert the torso of the model to float16.
        """
    self.input_blocks.apply(convert_module_to_f16)
    self.middle_block.apply(convert_module_to_f16)
    self.output_blocks.apply(convert_module_to_f16)

def convert_to_fp32(self):
    """
        Convert the torso of the model to float32.
        """
    self.input_blocks.apply(convert_module_to_f32)
    self.middle_block.apply(convert_module_to_f32)
    self.output_blocks.apply(convert_module_to_f32)

class EncoderUNetModel(nn.Module):
    """
    The half UNet model with attention and timestep embedding.
    For usage, see UNet.
    """

    def __init__(self, image_size, in_channels, model_channels, out_channels, num_res_blocks, attention_resolutions, dropout=0, channel_mult=(1, 2, 4, 8), conv_resample=True, dims=2, use_checkpoint=False, use_fp16=False, num_heads=1, num_head_channels=-1, num_heads_upsample=-1, use_scale_shift_norm=False, resblock_updown=False, use_new_attention_order=False, pool='adaptive', *args, **kwargs):
        super().__init__()
        if num_heads_upsample == -1:
            num_heads_upsample = num_heads
        self.in_channels = in_channels
        self.model_channels = model_channels
        self.out_channels = out_channels
        self.num_res_blocks = num_res_blocks
        self.attention_resolutions = attention_resolutions
        self.dropout = dropout
        self.channel_mult = channel_mult
        self.conv_resample = conv_resample
        self.use_checkpoint = use_checkpoint
        self.dtype = th.float16 if use_fp16 else th.float32
        self.num_heads = num_heads
        self.num_head_channels = num_head_channels
        self.num_heads_upsample = num_heads_upsample
        time_embed_dim = model_channels * 4
        self.time_embed = nn.Sequential(linear(model_channels, time_embed_dim), nn.SiLU(), linear(time_embed_dim, time_embed_dim))
        self.input_blocks = nn.ModuleList([TimestepEmbedSequential(conv_nd(dims, in_channels, model_channels, 3, padding=1))])
        self._feature_size = model_channels
        input_block_chans = [model_channels]
        ch = model_channels
        ds = 1
        for level, mult in enumerate(channel_mult):
            for _ in range(num_res_blocks):
                layers = [ResBlock(ch, time_embed_dim, dropout, out_channels=mult * model_channels, dims=dims, use_checkpoint=use_checkpoint, use_scale_shift_norm=use_scale_shift_norm)]
                ch = mult * model_channels
                if ds in attention_resolutions:
                    layers.append(AttentionBlock(ch, use_checkpoint=use_checkpoint, num_heads=num_heads, num_head_channels=num_head_channels, use_new_attention_order=use_new_attention_order))
                self.input_blocks.append(TimestepEmbedSequential(*layers))
                self._feature_size += ch
                input_block_chans.append(ch)
            if level != len(channel_mult) - 1:
                out_ch = ch
                self.input_blocks.append(TimestepEmbedSequential(ResBlock(ch, time_embed_dim, dropout, out_channels=out_ch, dims=dims, use_checkpoint=use_checkpoint, use_scale_shift_norm=use_scale_shift_norm, down=True) if resblock_updown else Downsample(ch, conv_resample, dims=dims, out_channels=out_ch)))
                ch = out_ch
                input_block_chans.append(ch)
                ds *= 2
                self._feature_size += ch
        self.middle_block = TimestepEmbedSequential(ResBlock(ch, time_embed_dim, dropout, dims=dims, use_checkpoint=use_checkpoint, use_scale_shift_norm=use_scale_shift_norm), AttentionBlock(ch, use_checkpoint=use_checkpoint, num_heads=num_heads, num_head_channels=num_head_channels, use_new_attention_order=use_new_attention_order), ResBlock(ch, time_embed_dim, dropout, dims=dims, use_checkpoint=use_checkpoint, use_scale_shift_norm=use_scale_shift_norm))
        self._feature_size += ch
        self.pool = pool
        if pool == 'adaptive':
            self.out = nn.Sequential(normalization(ch), nn.SiLU(), nn.AdaptiveAvgPool2d((1, 1)), zero_module(conv_nd(dims, ch, out_channels, 1)), nn.Flatten())
        elif pool == 'attention':
            assert num_head_channels != -1
            self.out = nn.Sequential(normalization(ch), nn.SiLU(), AttentionPool2d(image_size // ds, ch, num_head_channels, out_channels))
        elif pool == 'spatial':
            self.out = nn.Sequential(nn.Linear(self._feature_size, 2048), nn.ReLU(), nn.Linear(2048, self.out_channels))
        elif pool == 'spatial_v2':
            self.out = nn.Sequential(nn.Linear(self._feature_size, 2048), normalization(2048), nn.SiLU(), nn.Linear(2048, self.out_channels))
        else:
            raise NotImplementedError(f'Unexpected {pool} pooling')

    def convert_to_fp16(self):
        """
        Convert the torso of the model to float16.
        """
        self.input_blocks.apply(convert_module_to_f16)
        self.middle_block.apply(convert_module_to_f16)

    def convert_to_fp32(self):
        """
        Convert the torso of the model to float32.
        """
        self.input_blocks.apply(convert_module_to_f32)
        self.middle_block.apply(convert_module_to_f32)

    def forward(self, x, timesteps):
        """
        Apply the model to an input batch.
        :param x: an [N x C x ...] Tensor of inputs.
        :param timesteps: a 1-D batch of timesteps.
        :return: an [N x K] Tensor of outputs.
        """
        emb = self.time_embed(timestep_embedding(timesteps, self.model_channels))
        results = []
        h = x.type(self.dtype)
        for module in self.input_blocks:
            h = module(h, emb)
            if self.pool.startswith('spatial'):
                results.append(h.type(x.dtype).mean(dim=(2, 3)))
        h = self.middle_block(h, emb)
        if self.pool.startswith('spatial'):
            results.append(h.type(x.dtype).mean(dim=(2, 3)))
            h = th.cat(results, axis=-1)
            return self.out(h)
        else:
            h = h.type(x.dtype)
            return self.out(h)

def convert_to_fp16(self):
    """
        Convert the torso of the model to float16.
        """
    self.input_blocks.apply(convert_module_to_f16)
    self.middle_block.apply(convert_module_to_f16)

def convert_to_fp32(self):
    """
        Convert the torso of the model to float32.
        """
    self.input_blocks.apply(convert_module_to_f32)
    self.middle_block.apply(convert_module_to_f32)

def make_ddim_sampling_parameters(alphacums, ddim_timesteps, eta, verbose=True):
    alphas = alphacums[ddim_timesteps]
    alphas_prev = np.asarray([alphacums[0]] + alphacums[ddim_timesteps[:-1]].tolist())
    sigmas = eta * np.sqrt((1 - alphas_prev) / (1 - alphas) * (1 - alphas / alphas_prev))
    if verbose:
        print(f'Selected alphas for ddim sampler: a_t: {alphas}; a_(t-1): {alphas_prev}')
        print(f'For the chosen value of eta, which is {eta}, this results in the following sigma_t schedule for ddim sampler {sigmas}')
    return (sigmas, alphas, alphas_prev)

def checkpoint(func, inputs, params, flag):
    """
    Evaluate a function without caching intermediate activations, allowing for
    reduced memory at the expense of extra compute in the backward pass.
    :param func: the function to evaluate.
    :param inputs: the argument sequence to pass to `func`.
    :param params: a sequence of parameters `func` depends on but does not
                   explicitly take as arguments.
    :param flag: if False, disable gradient checkpointing.
    """
    if flag:
        args = tuple(inputs) + tuple(params)
        return CheckpointFunction.apply(func, len(inputs), *args)
    else:
        return func(*inputs)

class DDPM(pl.LightningModule):

    def __init__(self, unet_config, timesteps=1000, beta_schedule='linear', loss_type='l2', ckpt_path=None, ignore_keys=[], load_only_unet=False, monitor='val/loss', use_ema=True, first_stage_key='image', image_size=256, channels=3, log_every_t=100, clip_denoised=True, linear_start=0.0001, linear_end=0.02, cosine_s=0.008, given_betas=None, original_elbo_weight=0.0, v_posterior=0.0, l_simple_weight=1.0, conditioning_key=None, parameterization='eps', scheduler_config=None, use_positional_encodings=False, learn_logvar=False, logvar_init=0.0):
        super().__init__()
        assert parameterization in ['eps', 'x0'], 'currently only supporting "eps" and "x0"'
        self.parameterization = parameterization
        print(f'{self.__class__.__name__}: Running in {self.parameterization}-prediction mode')
        self.cond_stage_model = None
        self.clip_denoised = clip_denoised
        self.log_every_t = log_every_t
        self.first_stage_key = first_stage_key
        self.image_size = image_size
        self.channels = channels
        self.use_positional_encodings = use_positional_encodings
        self.model = DiffusionWrapper(unet_config, conditioning_key)
        count_params(self.model, verbose=True)
        self.use_ema = use_ema
        if self.use_ema:
            self.model_ema = LitEma(self.model)
            print(f'Keeping EMAs of {len(list(self.model_ema.buffers()))}.')
        self.use_scheduler = scheduler_config is not None
        if self.use_scheduler:
            self.scheduler_config = scheduler_config
        self.v_posterior = v_posterior
        self.original_elbo_weight = original_elbo_weight
        self.l_simple_weight = l_simple_weight
        if monitor is not None:
            self.monitor = monitor
        if ckpt_path is not None:
            self.init_from_ckpt(ckpt_path, ignore_keys=ignore_keys, only_model=load_only_unet)
        self.register_schedule(given_betas=given_betas, beta_schedule=beta_schedule, timesteps=timesteps, linear_start=linear_start, linear_end=linear_end, cosine_s=cosine_s)
        self.loss_type = loss_type
        self.learn_logvar = learn_logvar
        self.logvar = torch.full(fill_value=logvar_init, size=(self.num_timesteps,))
        if self.learn_logvar:
            self.logvar = nn.Parameter(self.logvar, requires_grad=True)

    def register_schedule(self, given_betas=None, beta_schedule='linear', timesteps=1000, linear_start=0.0001, linear_end=0.02, cosine_s=0.008):
        if exists(given_betas):
            betas = given_betas
        else:
            betas = make_beta_schedule(beta_schedule, timesteps, linear_start=linear_start, linear_end=linear_end, cosine_s=cosine_s)
        alphas = 1.0 - betas
        alphas_cumprod = np.cumprod(alphas, axis=0)
        alphas_cumprod_prev = np.append(1.0, alphas_cumprod[:-1])
        timesteps, = betas.shape
        self.num_timesteps = int(timesteps)
        self.linear_start = linear_start
        self.linear_end = linear_end
        assert alphas_cumprod.shape[0] == self.num_timesteps, 'alphas have to be defined for each timestep'
        to_torch = partial(torch.tensor, dtype=torch.float32)
        self.register_buffer('betas', to_torch(betas))
        self.register_buffer('alphas_cumprod', to_torch(alphas_cumprod))
        self.register_buffer('alphas_cumprod_prev', to_torch(alphas_cumprod_prev))
        self.register_buffer('sqrt_alphas_cumprod', to_torch(np.sqrt(alphas_cumprod)))
        self.register_buffer('sqrt_one_minus_alphas_cumprod', to_torch(np.sqrt(1.0 - alphas_cumprod)))
        self.register_buffer('log_one_minus_alphas_cumprod', to_torch(np.log(1.0 - alphas_cumprod)))
        self.register_buffer('sqrt_recip_alphas_cumprod', to_torch(np.sqrt(1.0 / alphas_cumprod)))
        self.register_buffer('sqrt_recipm1_alphas_cumprod', to_torch(np.sqrt(1.0 / alphas_cumprod - 1)))
        posterior_variance = (1 - self.v_posterior) * betas * (1.0 - alphas_cumprod_prev) / (1.0 - alphas_cumprod) + self.v_posterior * betas
        self.register_buffer('posterior_variance', to_torch(posterior_variance))
        self.register_buffer('posterior_log_variance_clipped', to_torch(np.log(np.maximum(posterior_variance, 1e-20))))
        self.register_buffer('posterior_mean_coef1', to_torch(betas * np.sqrt(alphas_cumprod_prev) / (1.0 - alphas_cumprod)))
        self.register_buffer('posterior_mean_coef2', to_torch((1.0 - alphas_cumprod_prev) * np.sqrt(alphas) / (1.0 - alphas_cumprod)))
        if self.parameterization == 'eps':
            lvlb_weights = self.betas ** 2 / (2 * self.posterior_variance * to_torch(alphas) * (1 - self.alphas_cumprod))
        elif self.parameterization == 'x0':
            lvlb_weights = 0.5 * np.sqrt(torch.Tensor(alphas_cumprod)) / (2.0 * 1 - torch.Tensor(alphas_cumprod))
        else:
            raise NotImplementedError('mu not supported')
        lvlb_weights[0] = lvlb_weights[1]
        self.register_buffer('lvlb_weights', lvlb_weights, persistent=False)
        assert not torch.isnan(self.lvlb_weights).all()

    @contextmanager
    def ema_scope(self, context=None):
        if self.use_ema:
            self.model_ema.store(self.model.parameters())
            self.model_ema.copy_to(self.model)
            if context is not None:
                print(f'{context}: Switched to EMA weights')
        try:
            yield None
        finally:
            if self.use_ema:
                self.model_ema.restore(self.model.parameters())
                if context is not None:
                    print(f'{context}: Restored training weights')

    def init_from_ckpt(self, path, ignore_keys=list(), only_model=False):
        sd = torch.load(path, map_location='cpu')
        if 'state_dict' in list(sd.keys()):
            sd = sd['state_dict']
        keys = list(sd.keys())
        for k in keys:
            for ik in ignore_keys:
                if k.startswith(ik):
                    print('Deleting key {} from state_dict.'.format(k))
                    del sd[k]
        missing, unexpected = self.load_state_dict(sd, strict=False) if not only_model else self.model.load_state_dict(sd, strict=False)
        print(f'Restored from {path} with {len(missing)} missing and {len(unexpected)} unexpected keys')
        if len(missing) > 0:
            print(f'Missing Keys: {missing}')
        if len(unexpected) > 0:
            print(f'Unexpected Keys: {unexpected}')

    def q_mean_variance(self, x_start, t):
        """
        Get the distribution q(x_t | x_0).
        :param x_start: the [N x C x ...] tensor of noiseless inputs.
        :param t: the number of diffusion steps (minus 1). Here, 0 means one step.
        :return: A tuple (mean, variance, log_variance), all of x_start's shape.
        """
        mean = extract_into_tensor(self.sqrt_alphas_cumprod, t, x_start.shape) * x_start
        variance = extract_into_tensor(1.0 - self.alphas_cumprod, t, x_start.shape)
        log_variance = extract_into_tensor(self.log_one_minus_alphas_cumprod, t, x_start.shape)
        return (mean, variance, log_variance)

    def predict_start_from_noise(self, x_t, t, noise):
        return extract_into_tensor(self.sqrt_recip_alphas_cumprod, t, x_t.shape) * x_t - extract_into_tensor(self.sqrt_recipm1_alphas_cumprod, t, x_t.shape) * noise

    def q_posterior(self, x_start, x_t, t):
        posterior_mean = extract_into_tensor(self.posterior_mean_coef1, t, x_t.shape) * x_start + extract_into_tensor(self.posterior_mean_coef2, t, x_t.shape) * x_t
        posterior_variance = extract_into_tensor(self.posterior_variance, t, x_t.shape)
        posterior_log_variance_clipped = extract_into_tensor(self.posterior_log_variance_clipped, t, x_t.shape)
        return (posterior_mean, posterior_variance, posterior_log_variance_clipped)

    def p_mean_variance(self, x, t, clip_denoised: bool):
        model_out = self.model(x, t)
        if self.parameterization == 'eps':
            x_recon = self.predict_start_from_noise(x, t=t, noise=model_out)
        elif self.parameterization == 'x0':
            x_recon = model_out
        if clip_denoised:
            x_recon.clamp_(-1.0, 1.0)
        model_mean, posterior_variance, posterior_log_variance = self.q_posterior(x_start=x_recon, x_t=x, t=t)
        return (model_mean, posterior_variance, posterior_log_variance)

    @torch.no_grad()
    def p_sample(self, x, t, clip_denoised=True, repeat_noise=False):
        b, *_, device = (*x.shape, x.device)
        model_mean, _, model_log_variance = self.p_mean_variance(x=x, t=t, clip_denoised=clip_denoised)
        noise = noise_like(x.shape, device, repeat_noise)
        nonzero_mask = (1 - (t == 0).float()).reshape(b, *(1,) * (len(x.shape) - 1))
        return model_mean + nonzero_mask * (0.5 * model_log_variance).exp() * noise

    @torch.no_grad()
    def p_sample_loop(self, shape, return_intermediates=False):
        device = self.betas.device
        b = shape[0]
        img = torch.randn(shape, device=device)
        intermediates = [img]
        for i in tqdm(reversed(range(0, self.num_timesteps)), desc='Sampling t', total=self.num_timesteps):
            img = self.p_sample(img, torch.full((b,), i, device=device, dtype=torch.long), clip_denoised=self.clip_denoised)
            if i % self.log_every_t == 0 or i == self.num_timesteps - 1:
                intermediates.append(img)
        if return_intermediates:
            return (img, intermediates)
        return img

    @torch.no_grad()
    def sample(self, batch_size=16, return_intermediates=False):
        image_size = self.image_size
        channels = self.channels
        return self.p_sample_loop((batch_size, channels, image_size, image_size), return_intermediates=return_intermediates)

    def q_sample(self, x_start, t, noise=None):
        noise = default(noise, lambda: torch.randn_like(x_start))
        return extract_into_tensor(self.sqrt_alphas_cumprod, t, x_start.shape) * x_start + extract_into_tensor(self.sqrt_one_minus_alphas_cumprod, t, x_start.shape) * noise

    def get_loss(self, pred, target, mean=True):
        if self.loss_type == 'l1':
            loss = (target - pred).abs()
            if mean:
                loss = loss.mean()
        elif self.loss_type == 'l2':
            if mean:
                loss = torch.nn.functional.mse_loss(target, pred)
            else:
                loss = torch.nn.functional.mse_loss(target, pred, reduction='none')
        else:
            raise NotImplementedError("unknown loss type '{loss_type}'")
        return loss

    def p_losses(self, x_start, t, noise=None):
        noise = default(noise, lambda: torch.randn_like(x_start))
        x_noisy = self.q_sample(x_start=x_start, t=t, noise=noise)
        model_out = self.model(x_noisy, t)
        loss_dict = {}
        if self.parameterization == 'eps':
            target = noise
        elif self.parameterization == 'x0':
            target = x_start
        else:
            raise NotImplementedError(f'Paramterization {self.parameterization} not yet supported')
        loss = self.get_loss(model_out, target, mean=False).mean(dim=[1, 2, 3])
        log_prefix = 'train' if self.training else 'val'
        loss_dict.update({f'{log_prefix}/loss_simple': loss.mean()})
        loss_simple = loss.mean() * self.l_simple_weight
        loss_vlb = (self.lvlb_weights[t] * loss).mean()
        loss_dict.update({f'{log_prefix}/loss_vlb': loss_vlb})
        loss = loss_simple + self.original_elbo_weight * loss_vlb
        loss_dict.update({f'{log_prefix}/loss': loss})
        return (loss, loss_dict)

    def forward(self, x, *args, **kwargs):
        t = torch.randint(0, self.num_timesteps, (x.shape[0],), device=self.device).long()
        return self.p_losses(x, t, *args, **kwargs)

    def get_input(self, batch, k):
        x = batch[k]
        if len(x.shape) == 3:
            x = x[..., None]
        x = rearrange(x, 'b h w c -> b c h w')
        x = x.to(memory_format=torch.contiguous_format).float()
        return x

    def shared_step(self, batch):
        x = self.get_input(batch, self.first_stage_key)
        loss, loss_dict = self(x)
        return (loss, loss_dict)

    def training_step(self, batch, batch_idx):
        loss, loss_dict = self.shared_step(batch)
        self.log_dict(loss_dict, prog_bar=True, logger=True, on_step=True, on_epoch=True)
        self.log('global_step', self.global_step, prog_bar=True, logger=True, on_step=True, on_epoch=False)
        if self.use_scheduler:
            lr = self.optimizers().param_groups[0]['lr']
            self.log('lr_abs', lr, prog_bar=True, logger=True, on_step=True, on_epoch=False)
        return loss

    @torch.no_grad()
    def validation_step(self, batch, batch_idx):
        _, loss_dict_no_ema = self.shared_step(batch)
        with self.ema_scope():
            _, loss_dict_ema = self.shared_step(batch)
            loss_dict_ema = {key + '_ema': loss_dict_ema[key] for key in loss_dict_ema}
        self.log_dict(loss_dict_no_ema, prog_bar=False, logger=True, on_step=False, on_epoch=True)
        self.log_dict(loss_dict_ema, prog_bar=False, logger=True, on_step=False, on_epoch=True)

    def on_train_batch_end(self, *args, **kwargs):
        if self.use_ema:
            self.model_ema(self.model)

    def _get_rows_from_list(self, samples):
        n_imgs_per_row = len(samples)
        denoise_grid = rearrange(samples, 'n b c h w -> b n c h w')
        denoise_grid = rearrange(denoise_grid, 'b n c h w -> (b n) c h w')
        denoise_grid = make_grid(denoise_grid, nrow=n_imgs_per_row)
        return denoise_grid

    @torch.no_grad()
    def log_images(self, batch, N=8, n_row=2, sample=True, return_keys=None, **kwargs):
        log = dict()
        x = self.get_input(batch, self.first_stage_key)
        N = min(x.shape[0], N)
        n_row = min(x.shape[0], n_row)
        x = x.to(self.device)[:N]
        log['inputs'] = x
        diffusion_row = list()
        x_start = x[:n_row]
        for t in range(self.num_timesteps):
            if t % self.log_every_t == 0 or t == self.num_timesteps - 1:
                t = repeat(torch.tensor([t]), '1 -> b', b=n_row)
                t = t.to(self.device).long()
                noise = torch.randn_like(x_start)
                x_noisy = self.q_sample(x_start=x_start, t=t, noise=noise)
                diffusion_row.append(x_noisy)
        log['diffusion_row'] = self._get_rows_from_list(diffusion_row)
        if sample:
            with self.ema_scope('Plotting'):
                samples, denoise_row = self.sample(batch_size=N, return_intermediates=True)
            log['samples'] = samples
            log['denoise_row'] = self._get_rows_from_list(denoise_row)
        if return_keys:
            if np.intersect1d(list(log.keys()), return_keys).shape[0] == 0:
                return log
            else:
                return {key: log[key] for key in return_keys}
        return log

    def configure_optimizers(self):
        lr = self.learning_rate
        params = list(self.model.parameters())
        if self.learn_logvar:
            params = params + [self.logvar]
        opt = torch.optim.AdamW(params, lr=lr)
        return opt

def register_schedule(self, given_betas=None, beta_schedule='linear', timesteps=1000, linear_start=0.0001, linear_end=0.02, cosine_s=0.008):
    if exists(given_betas):
        betas = given_betas
    else:
        betas = make_beta_schedule(beta_schedule, timesteps, linear_start=linear_start, linear_end=linear_end, cosine_s=cosine_s)
    alphas = 1.0 - betas
    alphas_cumprod = np.cumprod(alphas, axis=0)
    alphas_cumprod_prev = np.append(1.0, alphas_cumprod[:-1])
    timesteps, = betas.shape
    self.num_timesteps = int(timesteps)
    self.linear_start = linear_start
    self.linear_end = linear_end
    assert alphas_cumprod.shape[0] == self.num_timesteps, 'alphas have to be defined for each timestep'
    to_torch = partial(torch.tensor, dtype=torch.float32)
    self.register_buffer('betas', to_torch(betas))
    self.register_buffer('alphas_cumprod', to_torch(alphas_cumprod))
    self.register_buffer('alphas_cumprod_prev', to_torch(alphas_cumprod_prev))
    self.register_buffer('sqrt_alphas_cumprod', to_torch(np.sqrt(alphas_cumprod)))
    self.register_buffer('sqrt_one_minus_alphas_cumprod', to_torch(np.sqrt(1.0 - alphas_cumprod)))
    self.register_buffer('log_one_minus_alphas_cumprod', to_torch(np.log(1.0 - alphas_cumprod)))
    self.register_buffer('sqrt_recip_alphas_cumprod', to_torch(np.sqrt(1.0 / alphas_cumprod)))
    self.register_buffer('sqrt_recipm1_alphas_cumprod', to_torch(np.sqrt(1.0 / alphas_cumprod - 1)))
    posterior_variance = (1 - self.v_posterior) * betas * (1.0 - alphas_cumprod_prev) / (1.0 - alphas_cumprod) + self.v_posterior * betas
    self.register_buffer('posterior_variance', to_torch(posterior_variance))
    self.register_buffer('posterior_log_variance_clipped', to_torch(np.log(np.maximum(posterior_variance, 1e-20))))
    self.register_buffer('posterior_mean_coef1', to_torch(betas * np.sqrt(alphas_cumprod_prev) / (1.0 - alphas_cumprod)))
    self.register_buffer('posterior_mean_coef2', to_torch((1.0 - alphas_cumprod_prev) * np.sqrt(alphas) / (1.0 - alphas_cumprod)))
    if self.parameterization == 'eps':
        lvlb_weights = self.betas ** 2 / (2 * self.posterior_variance * to_torch(alphas) * (1 - self.alphas_cumprod))
    elif self.parameterization == 'x0':
        lvlb_weights = 0.5 * np.sqrt(torch.Tensor(alphas_cumprod)) / (2.0 * 1 - torch.Tensor(alphas_cumprod))
    else:
        raise NotImplementedError('mu not supported')
    lvlb_weights[0] = lvlb_weights[1]
    self.register_buffer('lvlb_weights', lvlb_weights, persistent=False)
    assert not torch.isnan(self.lvlb_weights).all()

def scale_dense_depth_map(dense_depth_map, sparse_depth_map, depth_map_mask):
    """
    Scale the dense depth map to match the scale of the sparse depth map.

    :param dense_depth_map: [H, W] dense depth map
    :param sparse_depth_map: [H, W] sparse depth map
    :param depth_map_mask: [H, W] mask indicating valid values in the sparse depth map
    :return: Scaled dense depth map
    """
    dense_depth_map = torch.tensor(dense_depth_map, dtype=torch.float32)
    sparse_depth_map = torch.tensor(sparse_depth_map, dtype=torch.float32)
    depth_map_mask = torch.tensor(depth_map_mask, dtype=torch.float32)
    valid_dense_depths = torch.masked_select(dense_depth_map, depth_map_mask.bool())
    valid_sparse_depths = torch.masked_select(sparse_depth_map, depth_map_mask.bool())
    alpha_numerator = torch.sum(valid_dense_depths * valid_sparse_depths)
    alpha_denominator = torch.sum(valid_dense_depths ** 2)
    alpha = alpha_numerator / alpha_denominator
    print('scaling factor: ', alpha)
    scaled_dense_depth_map = alpha * dense_depth_map
    return scaled_dense_depth_map

def interpolate_uniformly(track, num_points):
    """
    Interpolates a given track to a specified number of points, distributing them uniformly.

    :param track: A numpy array of shape (n, d) where n is the number of points and d is the dimension.
    :param num_points: The number of points in the output interpolated track.
    :return: A numpy array of shape (num_points, d) representing the uniformly interpolated track.
    """
    distances = np.cumsum(np.sqrt(np.sum(np.diff(track, axis=0) ** 2, axis=1)))
    distances = np.insert(distances, 0, 0)
    max_distance = distances[-1]
    uniform_distances = np.linspace(0, max_distance, num_points)
    uniform_track = np.array([np.interp(uniform_distances, distances, track[:, dim]) for dim in range(track.shape[1])])
    return uniform_track.T

def get_ray_directions(H, W, focal, use_np=True):
    """
    Get ray directions for all pixels in camera coordinate.
    Reference: https://www.scratchapixel.com/lessons/3d-basic-rendering/
               ray-tracing-generating-camera-rays/standard-coordinate-systems

    Inputs:
        H, W, focal: image height, width and focal length

    Outputs:
        directions: (H, W, 3), the direction of the rays in camera coordinate
    """
    grid = create_meshgrid(H, W, normalized_coordinates=False)[0]
    i, j = grid.unbind(-1)
    directions = torch.stack([(i - W / 2) / focal, -(j - H / 2) / focal, -torch.ones_like(i)], -1).to(torch.float32)
    if use_np:
        directions = directions.numpy()
    return directions

class L1AngularLoss(nn.Module):

    def __init__(self, args):
        super(L1AngularLoss, self).__init__()
        self.weight = args['weight']

    def forward(self, pred, target):
        """
            pred/target: [B, 3]
        """
        cosine_similarity = (pred * target).sum(dim=1).clamp(-1 + eps, 1 - eps)
        angle_diff = torch.acos(cosine_similarity)
        loss = torch.abs(angle_diff).mean()
        return loss * self.weight

def forward(self, pred, target):
    """
            pred/target: [B, 3]
        """
    cosine_similarity = (pred * target).sum(dim=1).clamp(-1 + eps, 1 - eps)
    angle_diff = torch.acos(cosine_similarity)
    loss = torch.abs(angle_diff).mean()
    return loss * self.weight

def interpolate_uniformly(track, num_points):
    """
        Interpolates a given track to a specified number of points, distributing them uniformly.

        :param track: A numpy array of shape (n, d) where n is the number of points and d is the dimension.
        :param num_points: The number of points in the output interpolated track.
        :return: A numpy array of shape (num_points, d) representing the uniformly interpolated track.
        """
    distances = np.cumsum(np.sqrt(np.sum(np.diff(track, axis=0) ** 2, axis=1)))
    distances = np.insert(distances, 0, 0)
    max_distance = distances[-1]
    uniform_distances = np.linspace(0, max_distance, num_points)
    uniform_track = np.array([np.interp(uniform_distances, distances, track[:, dim]) for dim in range(track.shape[1])])
    return uniform_track.T

def hermite_spline_once(P0, P1, T0, T1, num_points=100):
    spline_points = hermite_spline(P0, P1, T0, T1, num_points)
    return spline_points

def hermite_spline_twice(P0, P1, PM, T0, T1, TM, num_points=100):
    spline_points_1 = hermite_spline(P0, PM, T0, TM, num_points)
    spline_points_2 = hermite_spline(PM, P1, TM, T1, num_points)
    spline_points = np.vstack((spline_points_1, spline_points_2))
    return spline_points

def hermite_spline_third(P0, P1, PM, PMM1, PMM2, T0, T1, TM, TMM1, TMM2, num_points=100, time=1, input_map=None, post_transform=(False, None), obj=None):
    spline_points_1 = hermite_spline(P0, PMM1, T0, TMM1, num_points)
    spline_points_2 = hermite_spline(PMM1, PM, TMM1, TM, num_points)
    spline_points_3 = hermite_spline(PM, PMM2, TM, TMM2, num_points)
    spline_points_4 = hermite_spline(PMM2, P1, TMM2, T1, num_points)
    spline_points = np.vstack((spline_points_1, spline_points_2, spline_points_3, spline_points_4))
    return spline_points

def accerlate(trajectory, speed_increase=1.1):
    speeds = np.diff(trajectory, axis=0)
    speeds *= speed_increase
    new_trajectory = np.cumsum(np.vstack([trajectory[0], speeds]), axis=0)
    return new_trajectory

def deaccerlate(trajectory, speed_decrease=1.1):
    speeds = np.diff(trajectory, axis=0)
    speeds *= speed_decrease
    new_trajectory = np.cumsum(np.vstack([trajectory[0], speeds]), axis=0)
    return new_trajectory

def conflict_check(centerline, index, current_vertices):
    thres = 4
    for i in range(current_vertices.shape[0]):
        point1 = (centerline[index][0:2] + centerline[index][2:4]) / 2
        point2 = current_vertices[i][:2]
        if np.sqrt(np.sum((np.array(point2) - np.array(point1)) ** 2)) < thres:
            return False
    return True

