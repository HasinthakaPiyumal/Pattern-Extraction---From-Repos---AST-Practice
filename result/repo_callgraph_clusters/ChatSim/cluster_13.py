# Cluster 13

def _radial_and_tangential_undistort(xd: Tensor, yd: Tensor, k1: float=0, k2: float=0, k3: float=0, k4: float=0, p1: float=0, p2: float=0, eps: float=1e-09, max_iterations=10) -> Tuple[Tensor, Tensor]:
    """Computes undistorted (x, y) from (xd, yd)."""
    x = xd.clone()
    y = yd.clone()
    for _ in range(max_iterations):
        fx, fy, fx_x, fx_y, fy_x, fy_y = _compute_residual_and_jacobian(x=x, y=y, xd=xd, yd=yd, k1=k1, k2=k2, k3=k3, k4=k4, p1=p1, p2=p2)
        denominator = fy_x * fx_y - fx_x * fy_y
        x_numerator = fx * fy_y - fy * fx_y
        y_numerator = fy * fx_x - fx * fy_x
        step_x = torch.where(torch.abs(denominator) > eps, x_numerator / denominator, torch.zeros_like(denominator))
        step_y = torch.where(torch.abs(denominator) > eps, y_numerator / denominator, torch.zeros_like(denominator))
        x = x + step_x
        y = y + step_y
    return (x, y)

class Camera:

    @staticmethod
    def GetNumParams(type_):
        if type_ == 0 or type_ == 'SIMPLE_PINHOLE':
            return 3
        if type_ == 1 or type_ == 'PINHOLE':
            return 4
        if type_ == 2 or type_ == 'SIMPLE_RADIAL':
            return 4
        if type_ == 3 or type_ == 'RADIAL':
            return 5
        if type_ == 4 or type_ == 'OPENCV':
            return 8
        raise Exception('Camera type not supported')

    @staticmethod
    def GetNameFromType(type_):
        if type_ == 0:
            return 'SIMPLE_PINHOLE'
        if type_ == 1:
            return 'PINHOLE'
        if type_ == 2:
            return 'SIMPLE_RADIAL'
        if type_ == 3:
            return 'RADIAL'
        if type_ == 4:
            return 'OPENCV'
        raise Exception('Camera type not supported')

    def __init__(self, type_, width_, height_, params):
        self.width = width_
        self.height = height_
        if type_ == 0 or type_ == 'SIMPLE_PINHOLE':
            self.fx, self.cx, self.cy = params
            self.fy = self.fx
            self.distortion_func = None
            self.camera_type = 0
        elif type_ == 1 or type_ == 'PINHOLE':
            self.fx, self.fy, self.cx, self.cy = params
            self.distortion_func = None
            self.camera_type = 1
        elif type_ == 2 or type_ == 'SIMPLE_RADIAL':
            self.fx, self.cx, self.cy, self.k1 = params
            self.fy = self.fx
            self.distortion_func = simple_radial_distortion
            self.camera_type = 2
        elif type_ == 3 or type_ == 'RADIAL':
            self.fx, self.cx, self.cy, self.k1, self.k2 = params
            self.fy = self.fx
            self.distortion_func = radial_distortion
            self.camera_type = 3
        elif type_ == 4 or type_ == 'OPENCV':
            self.fx, self.fy, self.cx, self.cy = params[:4]
            self.k1, self.k2, self.p1, self.p2 = params[4:]
            self.distortion_func = opencv_distortion
            self.camera_type = 4
        else:
            raise Exception('Camera type not supported')

    def __str__(self):
        s = self.GetNameFromType(self.camera_type) + ' {} {} {}'.format(self.width, self.height, self.fx)
        if self.camera_type in (1, 4):
            s += ' {}'.format(self.fy)
        s += ' {} {}'.format(self.cx, self.cy)
        if self.camera_type == 2:
            s += ' {}'.format(self.k1)
        elif self.camera_type == 3:
            s += ' {} {}'.format(self.k1, self.k2)
        elif self.camera_type == 4:
            s += ' {} {} {} {}'.format(self.k1, self.k2, self.p1, self.p2)
        return s

    def get_params(self):
        if self.camera_type == 0:
            return np.array((self.fx, self.cx, self.cy))
        if self.camera_type == 1:
            return np.array((self.fx, self.fy, self.cx, self.cy))
        if self.camera_type == 2:
            return np.array((self.fx, self.cx, self.cy, self.k1))
        if self.camera_type == 3:
            return np.array((self.fx, self.cx, self.cy, self.k1, self.k2))
        if self.camera_type == 4:
            return np.array((self.fx, self.fy, self.cx, self.cy, self.k1, self.k2, self.p1, self.p2))

    def get_camera_matrix(self):
        return np.array(((self.fx, 0, self.cx), (0, self.fy, self.cy), (0, 0, 1)))

    def get_inverse_camera_matrix(self):
        return np.array(((1.0 / self.fx, 0, -self.cx / self.fx), (0, 1.0 / self.fy, -self.cy / self.fy), (0, 0, 1)))

    @property
    def K(self):
        return self.get_camera_matrix()

    @property
    def K_inv(self):
        return self.get_inverse_camera_matrix()

    def get_inv_camera_matrix(self):
        inv_fx, inv_fy = (1.0 / self.fx, 1.0 / self.fy)
        return np.array(((inv_fx, 0, -inv_fx * self.cx), (0, inv_fy, -inv_fy * self.cy), (0, 0, 1)))

    def get_image_grid(self):
        xmin = (0.5 - self.cx) / self.fx
        xmax = (self.width - 0.5 - self.cx) / self.fx
        ymin = (0.5 - self.cy) / self.fy
        ymax = (self.height - 0.5 - self.cy) / self.fy
        return np.meshgrid(np.linspace(xmin, xmax, self.width), np.linspace(ymin, ymax, self.height))

    def distort_points(self, x, normalized=True, denormalize=True):
        x = np.atleast_2d(x)
        if not normalized:
            x -= np.array([[self.cx, self.cy]])
            x /= np.array([[self.fx, self.fy]])
        if self.distortion_func is not None:
            x = self.distortion_func(self, x)
        if denormalize:
            x *= np.array([[self.fx, self.fy]])
            x += np.array([[self.cx, self.cy]])
        return x

    def undistort_points(self, x, normalized=False, denormalize=True):
        x = np.atleast_2d(x)
        if not normalized:
            x = x - np.array([self.cx, self.cy])
            x /= np.array([self.fx, self.fy])
        if self.distortion_func is not None:

            def objective(xu):
                return (x - self.distortion_func(self, xu.reshape(*x.shape))).ravel()
            xu = root(objective, x).x.reshape(*x.shape)
        else:
            xu = x
        if denormalize:
            xu *= np.array([[self.fx, self.fy]])
            xu += np.array([[self.cx, self.cy]])
        return xu

def get_image_grid(self):
    xmin = (0.5 - self.cx) / self.fx
    xmax = (self.width - 0.5 - self.cx) / self.fx
    ymin = (0.5 - self.cy) / self.fy
    ymax = (self.height - 0.5 - self.cy) / self.fy
    return np.meshgrid(np.linspace(xmin, xmax, self.width), np.linspace(ymin, ymax, self.height))

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

def norm(self):
    return np.linalg.norm(self.q)

def normalize(self):
    self.q /= np.linalg.norm(self.q)
    return self

class DualQuaternion:

    @staticmethod
    def FromQT(q, t):
        return DualQuaternion(qe=0.5 * np.asarray(t)) * DualQuaternion(q)

    def __init__(self, q0=np.array((1.0, 0.0, 0.0, 0.0)), qe=np.zeros(4)):
        self.q0, self.qe = (Quaternion(q0), Quaternion(qe))

    def __add__(self, other):
        return DualQuaternion(self.q0 + other.q0, self.qe + other.qe)

    def __iadd__(self, other):
        self.q0 += other.q0
        self.qe += other.qe
        return self

    def __invert__(self):
        return DualQuaternion(~self.q0, ~self.qe)

    def __mul__(self, other):
        if isinstance(other, DualQuaternion):
            return DualQuaternion(self.q0 * other.q0, self.q0 * other.qe + self.qe * other.q0)
        elif isinstance(other, complex):
            return DualQuaternion(self.q0 * other.real, self.q0 * other.imag + self.qe * other.real)
        else:
            return DualQuaternion(other * self.q0, other * self.qe)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __imul__(self, other):
        tmp = self * other
        self.q0, self.qe = (tmp.q0, tmp.qe)
        return self

    def __neg__(self):
        return DualQuaternion(-self.q0, -self.qe)

    def __sub__(self, other):
        return DualQuaternion(self.q0 - other.q0, self.qe - other.qe)

    def __isub__(self, other):
        self.q0 -= other.q0
        self.qe -= other.qe
        return self

    def inverse(self):
        normsq = complex(q0.dot(q0), 2.0 * self.q0.q.dot(self.qe.q))
        inv_len_real = 1.0 / normsq.real
        return ~self * complex(inv_len_real, -normsq.imag * inv_len_real * inv_len_real)

    def norm(self):
        q0_norm = self.q0.norm()
        return complex(q0_norm, self.q0.dot(self.qe) / q0_norm)

    def normalize(self):
        norm = self.norm()
        inv_len_real = 1.0 / norm.real
        self *= complex(inv_len_real, -norm.imag * inv_len_real * inv_len_real)
        return self

    def getT(self):
        return 2 * (self.qe * ~self.q0).q[1:]

    def ToQT(self):
        return (self.q0, self.getT())

def inverse(self):
    normsq = complex(q0.dot(q0), 2.0 * self.q0.q.dot(self.qe.q))
    inv_len_real = 1.0 / normsq.real
    return ~self * complex(inv_len_real, -normsq.imag * inv_len_real * inv_len_real)

def norm(self):
    q0_norm = self.q0.norm()
    return complex(q0_norm, self.q0.dot(self.qe) / q0_norm)

def normalize(self):
    norm = self.norm()
    inv_len_real = 1.0 / norm.real
    self *= complex(inv_len_real, -norm.imag * inv_len_real * inv_len_real)
    return self

def inter_poses(key_poses, n_out_poses, sigma=1.0):
    n_key_poses = len(key_poses)
    out_poses = []
    for i in range(n_out_poses):
        w = np.linspace(0, n_key_poses - 1, n_key_poses)
        w = np.exp(-(np.abs(i / n_out_poses * n_key_poses - w) / sigma) ** 2)
        w = w + 1e-06
        w /= np.sum(w)
        cur_pose = key_poses[0]
        cur_w = w[0]
        for j in range(0, n_key_poses - 1):
            cur_pose = inter_two_poses(cur_pose, key_poses[j + 1], cur_w / (cur_w + w[j + 1]))
            cur_w += w[j + 1]
        out_poses.append(cur_pose)
    return np.stack(out_poses)

def _radial_and_tangential_undistort(xd: Tensor, yd: Tensor, k1: float=0, k2: float=0, k3: float=0, k4: float=0, p1: float=0, p2: float=0, eps: float=1e-09, max_iterations=10) -> Tuple[Tensor, Tensor]:
    """Computes undistorted (x, y) from (xd, yd)."""
    x = xd.clone()
    y = yd.clone()
    for _ in range(max_iterations):
        fx, fy, fx_x, fx_y, fy_x, fy_y = _compute_residual_and_jacobian(x=x, y=y, xd=xd, yd=yd, k1=k1, k2=k2, k3=k3, k4=k4, p1=p1, p2=p2)
        denominator = fy_x * fx_y - fx_x * fy_y
        x_numerator = fx * fy_y - fy * fx_y
        y_numerator = fy * fx_x - fx * fy_x
        step_x = torch.where(torch.abs(denominator) > eps, x_numerator / denominator, torch.zeros_like(denominator))
        step_y = torch.where(torch.abs(denominator) > eps, y_numerator / denominator, torch.zeros_like(denominator))
        x = x + step_x
        y = y + step_y
    return (x, y)

def to_torch_image(img):
    return (torch.from_numpy(img).to(torch.float32) / 255.0).to(torch.device('cuda')).permute(2, 0, 1)[None]

def to_torch_image(img):
    return (torch.from_numpy(img).to(torch.float32) / 255.0 * 2.0 - 1.0).to(torch.device('cuda')).permute(2, 0, 1)[None]

class Camera:

    @staticmethod
    def GetNumParams(type_):
        if type_ == 0 or type_ == 'SIMPLE_PINHOLE':
            return 3
        if type_ == 1 or type_ == 'PINHOLE':
            return 4
        if type_ == 2 or type_ == 'SIMPLE_RADIAL':
            return 4
        if type_ == 3 or type_ == 'RADIAL':
            return 5
        if type_ == 4 or type_ == 'OPENCV':
            return 8
        raise Exception('Camera type not supported')

    @staticmethod
    def GetNameFromType(type_):
        if type_ == 0:
            return 'SIMPLE_PINHOLE'
        if type_ == 1:
            return 'PINHOLE'
        if type_ == 2:
            return 'SIMPLE_RADIAL'
        if type_ == 3:
            return 'RADIAL'
        if type_ == 4:
            return 'OPENCV'
        raise Exception('Camera type not supported')

    def __init__(self, type_, width_, height_, params):
        self.width = width_
        self.height = height_
        if type_ == 0 or type_ == 'SIMPLE_PINHOLE':
            self.fx, self.cx, self.cy = params
            self.fy = self.fx
            self.distortion_func = None
            self.camera_type = 0
        elif type_ == 1 or type_ == 'PINHOLE':
            self.fx, self.fy, self.cx, self.cy = params
            self.distortion_func = None
            self.camera_type = 1
        elif type_ == 2 or type_ == 'SIMPLE_RADIAL':
            self.fx, self.cx, self.cy, self.k1 = params
            self.fy = self.fx
            self.distortion_func = simple_radial_distortion
            self.camera_type = 2
        elif type_ == 3 or type_ == 'RADIAL':
            self.fx, self.cx, self.cy, self.k1, self.k2 = params
            self.fy = self.fx
            self.distortion_func = radial_distortion
            self.camera_type = 3
        elif type_ == 4 or type_ == 'OPENCV':
            self.fx, self.fy, self.cx, self.cy = params[:4]
            self.k1, self.k2, self.p1, self.p2 = params[4:]
            self.distortion_func = opencv_distortion
            self.camera_type = 4
        else:
            raise Exception('Camera type not supported')

    def __str__(self):
        s = self.GetNameFromType(self.camera_type) + ' {} {} {}'.format(self.width, self.height, self.fx)
        if self.camera_type in (1, 4):
            s += ' {}'.format(self.fy)
        s += ' {} {}'.format(self.cx, self.cy)
        if self.camera_type == 2:
            s += ' {}'.format(self.k1)
        elif self.camera_type == 3:
            s += ' {} {}'.format(self.k1, self.k2)
        elif self.camera_type == 4:
            s += ' {} {} {} {}'.format(self.k1, self.k2, self.p1, self.p2)
        return s

    def get_params(self):
        if self.camera_type == 0:
            return np.array((self.fx, self.cx, self.cy))
        if self.camera_type == 1:
            return np.array((self.fx, self.fy, self.cx, self.cy))
        if self.camera_type == 2:
            return np.array((self.fx, self.cx, self.cy, self.k1))
        if self.camera_type == 3:
            return np.array((self.fx, self.cx, self.cy, self.k1, self.k2))
        if self.camera_type == 4:
            return np.array((self.fx, self.fy, self.cx, self.cy, self.k1, self.k2, self.p1, self.p2))

    def get_camera_matrix(self):
        return np.array(((self.fx, 0, self.cx), (0, self.fy, self.cy), (0, 0, 1)))

    def get_inverse_camera_matrix(self):
        return np.array(((1.0 / self.fx, 0, -self.cx / self.fx), (0, 1.0 / self.fy, -self.cy / self.fy), (0, 0, 1)))

    @property
    def K(self):
        return self.get_camera_matrix()

    @property
    def K_inv(self):
        return self.get_inverse_camera_matrix()

    def get_inv_camera_matrix(self):
        inv_fx, inv_fy = (1.0 / self.fx, 1.0 / self.fy)
        return np.array(((inv_fx, 0, -inv_fx * self.cx), (0, inv_fy, -inv_fy * self.cy), (0, 0, 1)))

    def get_image_grid(self):
        xmin = (0.5 - self.cx) / self.fx
        xmax = (self.width - 0.5 - self.cx) / self.fx
        ymin = (0.5 - self.cy) / self.fy
        ymax = (self.height - 0.5 - self.cy) / self.fy
        return np.meshgrid(np.linspace(xmin, xmax, self.width), np.linspace(ymin, ymax, self.height))

    def distort_points(self, x, normalized=True, denormalize=True):
        x = np.atleast_2d(x)
        if not normalized:
            x -= np.array([[self.cx, self.cy]])
            x /= np.array([[self.fx, self.fy]])
        if self.distortion_func is not None:
            x = self.distortion_func(self, x)
        if denormalize:
            x *= np.array([[self.fx, self.fy]])
            x += np.array([[self.cx, self.cy]])
        return x

    def undistort_points(self, x, normalized=False, denormalize=True):
        x = np.atleast_2d(x)
        if not normalized:
            x = x - np.array([self.cx, self.cy])
            x /= np.array([self.fx, self.fy])
        if self.distortion_func is not None:

            def objective(xu):
                return (x - self.distortion_func(self, xu.reshape(*x.shape))).ravel()
            xu = root(objective, x).x.reshape(*x.shape)
        else:
            xu = x
        if denormalize:
            xu *= np.array([[self.fx, self.fy]])
            xu += np.array([[self.cx, self.cy]])
        return xu

def get_image_grid(self):
    xmin = (0.5 - self.cx) / self.fx
    xmax = (self.width - 0.5 - self.cx) / self.fx
    ymin = (0.5 - self.cy) / self.fy
    ymax = (self.height - 0.5 - self.cy) / self.fy
    return np.meshgrid(np.linspace(xmin, xmax, self.width), np.linspace(ymin, ymax, self.height))

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

def norm(self):
    return np.linalg.norm(self.q)

def normalize(self):
    self.q /= np.linalg.norm(self.q)
    return self

class DualQuaternion:

    @staticmethod
    def FromQT(q, t):
        return DualQuaternion(qe=0.5 * np.asarray(t)) * DualQuaternion(q)

    def __init__(self, q0=np.array((1.0, 0.0, 0.0, 0.0)), qe=np.zeros(4)):
        self.q0, self.qe = (Quaternion(q0), Quaternion(qe))

    def __add__(self, other):
        return DualQuaternion(self.q0 + other.q0, self.qe + other.qe)

    def __iadd__(self, other):
        self.q0 += other.q0
        self.qe += other.qe
        return self

    def __invert__(self):
        return DualQuaternion(~self.q0, ~self.qe)

    def __mul__(self, other):
        if isinstance(other, DualQuaternion):
            return DualQuaternion(self.q0 * other.q0, self.q0 * other.qe + self.qe * other.q0)
        elif isinstance(other, complex):
            return DualQuaternion(self.q0 * other.real, self.q0 * other.imag + self.qe * other.real)
        else:
            return DualQuaternion(other * self.q0, other * self.qe)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __imul__(self, other):
        tmp = self * other
        self.q0, self.qe = (tmp.q0, tmp.qe)
        return self

    def __neg__(self):
        return DualQuaternion(-self.q0, -self.qe)

    def __sub__(self, other):
        return DualQuaternion(self.q0 - other.q0, self.qe - other.qe)

    def __isub__(self, other):
        self.q0 -= other.q0
        self.qe -= other.qe
        return self

    def inverse(self):
        normsq = complex(q0.dot(q0), 2.0 * self.q0.q.dot(self.qe.q))
        inv_len_real = 1.0 / normsq.real
        return ~self * complex(inv_len_real, -normsq.imag * inv_len_real * inv_len_real)

    def norm(self):
        q0_norm = self.q0.norm()
        return complex(q0_norm, self.q0.dot(self.qe) / q0_norm)

    def normalize(self):
        norm = self.norm()
        inv_len_real = 1.0 / norm.real
        self *= complex(inv_len_real, -norm.imag * inv_len_real * inv_len_real)
        return self

    def getT(self):
        return 2 * (self.qe * ~self.q0).q[1:]

    def ToQT(self):
        return (self.q0, self.getT())

def inverse(self):
    normsq = complex(q0.dot(q0), 2.0 * self.q0.q.dot(self.qe.q))
    inv_len_real = 1.0 / normsq.real
    return ~self * complex(inv_len_real, -normsq.imag * inv_len_real * inv_len_real)

def norm(self):
    q0_norm = self.q0.norm()
    return complex(q0_norm, self.q0.dot(self.qe) / q0_norm)

def normalize(self):
    norm = self.norm()
    inv_len_real = 1.0 / norm.real
    self *= complex(inv_len_real, -norm.imag * inv_len_real * inv_len_real)
    return self

def gsplat_render(viewpoint_camera, pc: GaussianModel, args: omegaconf.dictconfig.DictConfig, bg_color: torch.Tensor, scaling_modifier=1.0, override_color=None, exposure_scale=None):
    """
    Render the scene. 
    
    Background tensor (bg_color) must be on GPU!
    """
    if viewpoint_camera.K is not None:
        focal_length_x, focal_length_y, cx, cy = viewpoint_camera.K
        K = torch.tensor([[focal_length_x, 0, cx], [0, focal_length_y, cy], [0, 0, 1.0]]).to(pc.get_xyz)
    else:
        tanfovx = math.tan(viewpoint_camera.FoVx * 0.5)
        tanfovy = math.tan(viewpoint_camera.FoVy * 0.5)
        focal_length_x = viewpoint_camera.image_width / (2 * tanfovx)
        focal_length_y = viewpoint_camera.image_height / (2 * tanfovy)
        K = torch.tensor([[focal_length_x, 0, viewpoint_camera.image_width / 2.0], [0, focal_length_y, viewpoint_camera.image_height / 2.0], [0, 0, 1]]).to(pc.get_xyz)
    means3D = pc.get_xyz
    opacity = pc.get_opacity
    scales = pc.get_scaling * scaling_modifier
    rotations = pc.get_rotation
    if override_color is not None:
        colors = override_color
        sh_degree = None
    else:
        colors = pc.get_features
        sh_degree = pc.active_sh_degree
    viewmat = viewpoint_camera.world_view_transform.transpose(0, 1)
    render_colors, render_alphas, info = rasterization(means=means3D, quats=rotations, scales=scales, opacities=opacity.squeeze(-1), colors=colors, viewmats=viewmat[None], Ks=K[None], backgrounds=None, width=int(viewpoint_camera.image_width), height=int(viewpoint_camera.image_height), packed=False, sh_degree=sh_degree, render_mode='RGB+ED')
    rendered_image = render_colors[0].permute(2, 0, 1)[:3]
    rendered_depth = render_colors[0].permute(2, 0, 1)[3:]
    rendered_alphas = render_alphas[0].permute(2, 0, 1)
    if exposure_scale is not None:
        rendered_image *= exposure_scale
        rendered_image = OETF(rendered_image)
    radii = info['radii'].squeeze(0)
    try:
        info['means2d'].retain_grad()
    except:
        pass
    return_pkg = {'render_3dgs': rendered_image, 'viewspace_points': info['means2d'], 'visibility_filter': radii > 0, 'radii': radii}
    if args.render_depth:
        return_pkg['depth'] = rendered_depth
    if args.render_opacity:
        return_pkg['opacity'] = rendered_alphas
    if args.render_sky:
        sky_bg = pc.get_sky_bg(viewpoint_camera)
        return_pkg['sky_bg'] = sky_bg
        if args.blend_sky:
            assert args.render_opacity
            rendered_image = rendered_image + (1 - rendered_alphas) * sky_bg
    return_pkg['render'] = rendered_image
    return return_pkg

def PILtoTorch(pil_image, resolution):
    resized_image_PIL = pil_image.resize(resolution)
    resized_image = torch.from_numpy(np.array(resized_image_PIL)) / 255.0
    if len(resized_image.shape) == 3:
        return resized_image.permute(2, 0, 1)
    else:
        return resized_image.unsqueeze(dim=-1).permute(2, 0, 1)

def helper(step):
    if step < 0 or (lr_init == 0.0 and lr_final == 0.0):
        return 0.0
    if lr_delay_steps > 0:
        delay_rate = lr_delay_mult + (1 - lr_delay_mult) * np.sin(0.5 * np.pi * np.clip(step / lr_delay_steps, 0, 1))
    else:
        delay_rate = 1.0
    t = np.clip(step / max_steps, 0, 1)
    log_lerp = np.exp(np.log(lr_init) * (1 - t) + np.log(lr_final) * t)
    return delay_rate * log_lerp

def geom_transform_points(points, transf_matrix):
    P, _ = points.shape
    ones = torch.ones(P, 1, dtype=points.dtype, device=points.device)
    points_hom = torch.cat([points, ones], dim=1)
    points_out = torch.matmul(points_hom, transf_matrix.unsqueeze(0))
    denom = points_out[..., 3:] + 1e-07
    return (points_out[..., :3] / denom).squeeze(dim=0)

def OETF(x):
    a = 0.055
    return torch.where(x <= 0.0031308, 12.92 * x, (1 + a) * torch.pow(x, 1 / 2.4) - a)

def create_window(window_size, channel):
    _1D_window = gaussian(window_size, 1.5).unsqueeze(1)
    _2D_window = _1D_window.mm(_1D_window.t()).float().unsqueeze(0).unsqueeze(0)
    window = Variable(_2D_window.expand(channel, 1, window_size, window_size).contiguous())
    return window

def mse(img1, img2):
    return ((img1 - img2) ** 2).view(img1.shape[0], -1).mean(1, keepdim=True)

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

@property
def get_features(self):
    features_dc = self._features_dc
    features_rest = self._features_rest
    return torch.cat((features_dc, features_rest), dim=1)

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

def convert_cubemap(img, view_name):
    """
    Args:
        img : np.ndarray
            [res, res, 3]
        view_name : str
            one of ['front', 'back', 'left', 'right', 'top', 'bottom']

    if view name is in ['front', 'back', 'left', 'right'], horizontal flip the image!
    if view name is in ['top', 'bottom'], vertical flip the image!
    """
    if view_name in ['front', 'back', 'left', 'right']:
        img = np.flip(img, axis=1)
    elif view_name in ['top', 'bottom']:
        img = np.flip(img, axis=0)
    return img

def convert_cubemap_torch(img, view_name):
    """
    Args:
        img : torch.Tensor
            [res, res, 3]
        view_name : str
            one of ['front', 'back', 'left', 'right', 'top', 'bottom']

    if view name is in ['front', 'back', 'left', 'right'], horizontal flip the image!
    if view name is in ['top', 'bottom'], vertical flip the image!
    """
    if view_name in ['front', 'back', 'left', 'right']:
        img = torch.flip(img, [1])
    elif view_name in ['top', 'bottom']:
        img = torch.flip(img, [0])
    return img

class SkyCube(torch.nn.Module):

    def __init__(self, sky_model_args):
        super().__init__()
        resolution = sky_model_args.resolution
        self.waymo_to_opengl = torch.tensor([[0, -1, 0], [0, 0, 1], [-1, 0, 0]], dtype=torch.float32, device='cuda')
        self.base = torch.nn.Parameter(0.5 * torch.ones(6, resolution, resolution, 3, requires_grad=True))

    def capture(self):
        return self.base

    def train_params(self):
        return [self.base]

    def restore(self, model_args):
        self.base = model_args

    def _forward(self, l):
        import nvdiffrast.torch as dr
        l = (l.reshape(-1, 3) @ self.waymo_to_opengl.T).reshape(*l.shape)
        l = l.contiguous()
        prefix = l.shape[:-1]
        if len(prefix) != 3:
            l = l.reshape(1, 1, -1, l.shape[-1])
        light = dr.texture(self.base[None, ...], l, filter_mode='linear', boundary_mode='cube')
        light = light.view(*prefix, -1)
        return light

    def forward(self, viewpoint_camera):
        c2w = torch.linalg.inv(viewpoint_camera.world_view_transform.transpose(0, 1))
        ray_d_world = get_ray_directions(viewpoint_camera.image_height, viewpoint_camera.image_width, viewpoint_camera.FoVx, viewpoint_camera.FoVy, c2w).cuda()
        skymap = self._forward(ray_d_world)
        skymap = skymap.permute(2, 0, 1)
        return skymap

def _forward(self, l):
    import nvdiffrast.torch as dr
    l = (l.reshape(-1, 3) @ self.waymo_to_opengl.T).reshape(*l.shape)
    l = l.contiguous()
    prefix = l.shape[:-1]
    if len(prefix) != 3:
        l = l.reshape(1, 1, -1, l.shape[-1])
    light = dr.texture(self.base[None, ...], l, filter_mode='linear', boundary_mode='cube')
    light = light.view(*prefix, -1)
    return light

class RemoveAnythingVideo(nn.Module):

    def __init__(self, args, tracker_target='ostrack', segmentor_target='sam', inpainter_target='sttn'):
        super().__init__()
        tracker_build_args = {'tracker_param': args.tracker_ckpt}
        inpainter_build_args = {'lama': {'lama_config': args.lama_config, 'lama_ckpt': args.lama_ckpt}, 'sttn': {'model_type': 'sttn', 'ckpt_p': args.vi_ckpt}}
        self.tracker = self.build_tracker(tracker_target, **tracker_build_args)
        self.inpainter = self.build_inpainter(inpainter_target, **inpainter_build_args[inpainter_target])
        self.tracker_target = tracker_target
        self.inpainter_target = inpainter_target

    def build_tracker(self, target, **kwargs):
        assert target == 'ostrack', 'Only support sam now.'
        return build_ostrack_model(**kwargs)

    def build_segmentor(self, target='sam', **kwargs):
        assert target == 'sam', 'Only support sam now.'
        return build_sam_model(**kwargs)

    def build_inpainter(self, target='sttn', **kwargs):
        if target == 'lama':
            return build_lama_model(**kwargs)
        elif target == 'sttn':
            return build_sttn_model(**kwargs)
        else:
            raise NotImplementedError('Only support lama and sttn')

    def forward_tracker(self, frames_ps, init_box):
        init_box = np.array(init_box).astype(np.float32).reshape(-1, 4)
        seq = Sequence('tmp', frames_ps, 'inpaint-anything', init_box)
        all_box_xywh = get_box_using_ostrack(self.tracker, seq)
        return all_box_xywh

    def forward_segmentor(self, img, point_coords=None, point_labels=None, box=None, mask_input=None, multimask_output=True, return_logits=False):
        self.segmentor.set_image(img)
        masks, scores, logits = self.segmentor.predict(point_coords=point_coords, point_labels=point_labels, box=box, mask_input=mask_input, multimask_output=multimask_output, return_logits=return_logits)
        self.segmentor.reset_image()
        return (masks, scores)

    def forward_inpainter(self, frames, masks):
        print(self.inpainter_target)
        if self.inpainter_target == 'lama':
            for idx in range(len(frames)):
                frames[idx] = inpaint_img_with_builded_lama(self.inpainter, frames[idx], masks[idx], device=self.device)
        elif self.inpainter_target == 'sttn':
            frames = [Image.fromarray(frame) for frame in frames]
            masks = [Image.fromarray(np.uint8(mask * 255)) for mask in masks]
            frames = inpaint_video_with_builded_sttn(self.inpainter, frames, masks, device=self.device)
        else:
            raise NotImplementedError
        return frames

    @property
    def device(self):
        return 'cuda' if torch.cuda.is_available() else 'cpu'

    def mask_selection(self, masks, scores, ref_mask=None, interactive=False):
        if interactive:
            raise NotImplementedError
        else:
            if ref_mask is not None:
                mse = np.mean((masks.astype(np.int32) - ref_mask.astype(np.int32)) ** 2, axis=(-2, -1))
                idx = mse.argmin()
            else:
                idx = scores.argmax()
            return masks[idx]

    @staticmethod
    def get_box_from_mask(mask):
        x, y, w, h = cv2.boundingRect(mask)
        return np.array([x, y, w, h])

    def forward(self, frame_ps: List[str], key_frame_idx: int, key_frame_point_coords: np.ndarray, key_frame_point_labels: np.ndarray, key_frame_mask_idx: int=None, dilate_kernel_size: int=15):
        """
        Mask is 0-1 ndarray in default
        Frame is 0-255 ndarray in default
        """
        assert key_frame_idx == 0, 'Only support key frame at the beginning.'
        key_frame_p = frame_ps[key_frame_idx]
        key_frame = iio.imread(key_frame_p)
        key_masks, key_scores = self.forward_segmentor(key_frame, key_frame_point_coords, key_frame_point_labels)
        if key_frame_mask_idx is not None:
            key_mask = key_masks[key_frame_mask_idx]
        else:
            key_mask = self.mask_selection(key_masks, key_scores)
        if dilate_kernel_size is not None:
            key_mask = dilate_mask(key_mask, dilate_kernel_size)
        key_box = self.get_box_from_mask(key_mask)
        print('Tracking ...')
        all_box = self.forward_tracker(frame_ps, key_box)
        print('Segmenting ...')
        all_mask = [key_mask]
        all_frame = [key_frame]
        ref_mask = key_mask
        for frame_p, box in zip(frame_ps[1:], all_box[1:]):
            frame = iio.imread(frame_p)
            x, y, w, h = box
            sam_box = np.array([x, y, x + w, y + h])
            masks, scores = self.forward_segmentor(frame, box=sam_box)
            mask = self.mask_selection(masks, scores, ref_mask)
            if dilate_kernel_size is not None:
                mask = dilate_mask(mask, dilate_kernel_size)
            ref_mask = mask
            all_mask.append(mask)
            all_frame.append(frame)
        print('Inpainting ...')
        all_frame = self.forward_inpainter(all_frame, all_mask)
        return (all_frame, all_mask, all_box)

@staticmethod
def get_box_from_mask(mask):
    x, y, w, h = cv2.boundingRect(mask)
    return np.array([x, y, w, h])

@torch.no_grad()
def inpaint_img_with_lama(img: np.ndarray, mask: np.ndarray, config_p: str, ckpt_p: str, mod=8, device='cuda'):
    assert len(mask.shape) == 2
    if np.max(mask) == 1:
        mask = mask * 255
    img = torch.from_numpy(img).float().div(255.0)
    mask = torch.from_numpy(mask).float()
    predict_config = OmegaConf.load(config_p)
    predict_config.model.path = ckpt_p
    device = torch.device(device)
    train_config_path = os.path.join(predict_config.model.path, 'config.yaml')
    with open(train_config_path, 'r') as f:
        train_config = OmegaConf.create(yaml.safe_load(f))
    train_config.training_model.predict_only = True
    train_config.visualizer.kind = 'noop'
    checkpoint_path = os.path.join(predict_config.model.path, 'models', predict_config.model.checkpoint)
    model = load_checkpoint(train_config, checkpoint_path, strict=False, map_location='cpu')
    model.freeze()
    if not predict_config.get('refine', False):
        model.to(device)
    batch = {}
    batch['image'] = img.permute(2, 0, 1).unsqueeze(0)
    batch['mask'] = mask[None, None]
    unpad_to_size = [batch['image'].shape[2], batch['image'].shape[3]]
    batch['image'] = pad_tensor_to_modulo(batch['image'], mod)
    batch['mask'] = pad_tensor_to_modulo(batch['mask'], mod)
    batch = move_to_device(batch, device)
    batch['mask'] = (batch['mask'] > 0) * 1
    batch = model(batch)
    cur_res = batch[predict_config.out_key][0].permute(1, 2, 0)
    cur_res = cur_res.detach().cpu().numpy()
    if unpad_to_size is not None:
        orig_height, orig_width = unpad_to_size
        cur_res = cur_res[:orig_height, :orig_width]
    cur_res = np.clip(cur_res * 255, 0, 255).astype('uint8')
    return cur_res

@torch.no_grad()
def inpaint_img_with_builded_lama(model, img: np.ndarray, mask: np.ndarray, config_p=None, mod=8, device='cuda'):
    assert len(mask.shape) == 2
    if np.max(mask) == 1:
        mask = mask * 255
    img = torch.from_numpy(img).float().div(255.0)
    mask = torch.from_numpy(mask).float()
    batch = {}
    batch['image'] = img.permute(2, 0, 1).unsqueeze(0)
    batch['mask'] = mask[None, None]
    unpad_to_size = [batch['image'].shape[2], batch['image'].shape[3]]
    batch['image'] = pad_tensor_to_modulo(batch['image'], mod)
    batch['mask'] = pad_tensor_to_modulo(batch['mask'], mod)
    batch = move_to_device(batch, device)
    batch['mask'] = (batch['mask'] > 0) * 1
    batch = model(batch)
    cur_res = batch['inpainted'][0].permute(1, 2, 0)
    cur_res = cur_res.detach().cpu().numpy()
    if unpad_to_size is not None:
        orig_height, orig_width = unpad_to_size
        cur_res = cur_res[:orig_height, :orig_width]
    cur_res = np.clip(cur_res * 255, 0, 255).astype('uint8')
    return cur_res

class RemoveAnythingVideo(nn.Module):

    def __init__(self, args, tracker_target='ostrack', segmentor_target='sam', inpainter_target='sttn'):
        super().__init__()
        tracker_build_args = {'tracker_param': args.tracker_ckpt}
        segmentor_build_args = {'model_type': args.sam_model_type, 'ckpt_p': args.sam_ckpt}
        inpainter_build_args = {'lama': {'lama_config': args.lama_config, 'lama_ckpt': args.lama_ckpt}, 'sttn': {'model_type': 'sttn', 'ckpt_p': args.vi_ckpt}}
        self.tracker = self.build_tracker(tracker_target, **tracker_build_args)
        self.segmentor = self.build_segmentor(segmentor_target, **segmentor_build_args)
        self.inpainter = self.build_inpainter(inpainter_target, **inpainter_build_args[inpainter_target])
        self.tracker_target = tracker_target
        self.segmentor_target = segmentor_target
        self.inpainter_target = inpainter_target

    def build_tracker(self, target, **kwargs):
        assert target == 'ostrack', 'Only support sam now.'
        return build_ostrack_model(**kwargs)

    def build_segmentor(self, target='sam', **kwargs):
        assert target == 'sam', 'Only support sam now.'
        return build_sam_model(**kwargs)

    def build_inpainter(self, target='sttn', **kwargs):
        if target == 'lama':
            return build_lama_model(**kwargs)
        elif target == 'sttn':
            return build_sttn_model(**kwargs)
        else:
            raise NotImplementedError('Only support lama and sttn')

    def forward_tracker(self, frames_ps, init_box):
        init_box = np.array(init_box).astype(np.float32).reshape(-1, 4)
        seq = Sequence('tmp', frames_ps, 'inpaint-anything', init_box)
        all_box_xywh = get_box_using_ostrack(self.tracker, seq)
        return all_box_xywh

    def forward_segmentor(self, img, point_coords=None, point_labels=None, box=None, mask_input=None, multimask_output=True, return_logits=False):
        self.segmentor.set_image(img)
        masks, scores, logits = self.segmentor.predict(point_coords=point_coords, point_labels=point_labels, box=box, mask_input=mask_input, multimask_output=multimask_output, return_logits=return_logits)
        self.segmentor.reset_image()
        return (masks, scores)

    def forward_inpainter(self, frames, masks):
        print(self.inpainter_target)
        if self.inpainter_target == 'lama':
            for idx in range(len(frames)):
                frames[idx] = inpaint_img_with_builded_lama(self.inpainter, frames[idx], masks[idx], device=self.device)
        elif self.inpainter_target == 'sttn':
            frames = [Image.fromarray(frame) for frame in frames]
            masks = [Image.fromarray(np.uint8(mask * 255)) for mask in masks]
            frames = inpaint_video_with_builded_sttn(self.inpainter, frames, masks, device=self.device)
        else:
            raise NotImplementedError
        return frames

    @property
    def device(self):
        return 'cuda' if torch.cuda.is_available() else 'cpu'

    def mask_selection(self, masks, scores, ref_mask=None, interactive=False):
        if interactive:
            raise NotImplementedError
        else:
            if ref_mask is not None:
                mse = np.mean((masks.astype(np.int32) - ref_mask.astype(np.int32)) ** 2, axis=(-2, -1))
                idx = mse.argmin()
            else:
                idx = scores.argmax()
            return masks[idx]

    @staticmethod
    def get_box_from_mask(mask):
        x, y, w, h = cv2.boundingRect(mask)
        return np.array([x, y, w, h])

    def forward(self, frame_ps: List[str], key_frame_idx: int, key_frame_point_coords: np.ndarray, key_frame_point_labels: np.ndarray, key_frame_mask_idx: int=None, dilate_kernel_size: int=15):
        """
        Mask is 0-1 ndarray in default
        Frame is 0-255 ndarray in default
        """
        assert key_frame_idx == 0, 'Only support key frame at the beginning.'
        key_frame_p = frame_ps[key_frame_idx]
        key_frame = iio.imread(key_frame_p)
        key_masks, key_scores = self.forward_segmentor(key_frame, key_frame_point_coords, key_frame_point_labels)
        if key_frame_mask_idx is not None:
            key_mask = key_masks[key_frame_mask_idx]
        else:
            key_mask = self.mask_selection(key_masks, key_scores)
        if dilate_kernel_size is not None:
            key_mask = dilate_mask(key_mask, dilate_kernel_size)
        key_box = self.get_box_from_mask(key_mask)
        print('Tracking ...')
        all_box = self.forward_tracker(frame_ps, key_box)
        print('Segmenting ...')
        all_mask = [key_mask]
        all_frame = [key_frame]
        ref_mask = key_mask
        for frame_p, box in zip(frame_ps[1:], all_box[1:]):
            frame = iio.imread(frame_p)
            x, y, w, h = box
            sam_box = np.array([x, y, x + w, y + h])
            masks, scores = self.forward_segmentor(frame, box=sam_box)
            mask = self.mask_selection(masks, scores, ref_mask)
            if dilate_kernel_size is not None:
                mask = dilate_mask(mask, dilate_kernel_size)
            ref_mask = mask
            all_mask.append(mask)
            all_frame.append(frame)
        print('Inpainting ...')
        all_frame = self.forward_inpainter(all_frame, all_mask)
        return (all_frame, all_mask, all_box)

@staticmethod
def get_box_from_mask(mask):
    x, y, w, h = cv2.boundingRect(mask)
    return np.array([x, y, w, h])

class deconv(nn.Module):

    def __init__(self, input_channel, output_channel, kernel_size=3, padding=0):
        super().__init__()
        self.conv = nn.Conv2d(input_channel, output_channel, kernel_size=kernel_size, stride=1, padding=padding)

    def forward(self, x):
        x = F.interpolate(x, scale_factor=2, mode='bilinear', align_corners=True)
        return self.conv(x)

def forward(self, x):
    x = F.interpolate(x, scale_factor=2, mode='bilinear', align_corners=True)
    return self.conv(x)

class MultiHeadedAttention(nn.Module):
    """
    Take in model size and number of heads.
    """

    def __init__(self, patchsize, d_model):
        super().__init__()
        self.patchsize = patchsize
        self.query_embedding = nn.Conv2d(d_model, d_model, kernel_size=1, padding=0)
        self.value_embedding = nn.Conv2d(d_model, d_model, kernel_size=1, padding=0)
        self.key_embedding = nn.Conv2d(d_model, d_model, kernel_size=1, padding=0)
        self.output_linear = nn.Sequential(nn.Conv2d(d_model, d_model, kernel_size=3, padding=1), nn.LeakyReLU(0.2, inplace=True))
        self.attention = Attention()

    def forward(self, x, m, b, c):
        bt, _, h, w = x.size()
        t = bt // b
        d_k = c // len(self.patchsize)
        output = []
        _query = self.query_embedding(x)
        _key = self.key_embedding(x)
        _value = self.value_embedding(x)
        for (width, height), query, key, value in zip(self.patchsize, torch.chunk(_query, len(self.patchsize), dim=1), torch.chunk(_key, len(self.patchsize), dim=1), torch.chunk(_value, len(self.patchsize), dim=1)):
            out_w, out_h = (w // width, h // height)
            mm = m.view(b, t, 1, out_h, height, out_w, width)
            mm = mm.permute(0, 1, 3, 5, 2, 4, 6).contiguous().view(b, t * out_h * out_w, height * width)
            mm = (mm.mean(-1) > 0.5).unsqueeze(1).repeat(1, t * out_h * out_w, 1)
            query = query.view(b, t, d_k, out_h, height, out_w, width)
            query = query.permute(0, 1, 3, 5, 2, 4, 6).contiguous().view(b, t * out_h * out_w, d_k * height * width)
            key = key.view(b, t, d_k, out_h, height, out_w, width)
            key = key.permute(0, 1, 3, 5, 2, 4, 6).contiguous().view(b, t * out_h * out_w, d_k * height * width)
            value = value.view(b, t, d_k, out_h, height, out_w, width)
            value = value.permute(0, 1, 3, 5, 2, 4, 6).contiguous().view(b, t * out_h * out_w, d_k * height * width)
            '\n            # 2) Apply attention on all the projected vectors in batch.\n            tmp1 = []\n            for q,k,v in zip(torch.chunk(query, b, dim=0), torch.chunk(key, b, dim=0), torch.chunk(value, b, dim=0)):\n                y, _ = self.attention(q.unsqueeze(0), k.unsqueeze(0), v.unsqueeze(0))\n                tmp1.append(y)\n            y = torch.cat(tmp1,1)\n            '
            y, _ = self.attention(query, key, value, mm)
            y = y.view(b, t, out_h, out_w, d_k, height, width)
            y = y.permute(0, 1, 4, 2, 5, 3, 6).contiguous().view(bt, d_k, h, w)
            output.append(y)
        output = torch.cat(output, 1)
        x = self.output_linear(output)
        return x

def forward(self, x, m, b, c):
    bt, _, h, w = x.size()
    t = bt // b
    d_k = c // len(self.patchsize)
    output = []
    _query = self.query_embedding(x)
    _key = self.key_embedding(x)
    _value = self.value_embedding(x)
    for (width, height), query, key, value in zip(self.patchsize, torch.chunk(_query, len(self.patchsize), dim=1), torch.chunk(_key, len(self.patchsize), dim=1), torch.chunk(_value, len(self.patchsize), dim=1)):
        out_w, out_h = (w // width, h // height)
        mm = m.view(b, t, 1, out_h, height, out_w, width)
        mm = mm.permute(0, 1, 3, 5, 2, 4, 6).contiguous().view(b, t * out_h * out_w, height * width)
        mm = (mm.mean(-1) > 0.5).unsqueeze(1).repeat(1, t * out_h * out_w, 1)
        query = query.view(b, t, d_k, out_h, height, out_w, width)
        query = query.permute(0, 1, 3, 5, 2, 4, 6).contiguous().view(b, t * out_h * out_w, d_k * height * width)
        key = key.view(b, t, d_k, out_h, height, out_w, width)
        key = key.permute(0, 1, 3, 5, 2, 4, 6).contiguous().view(b, t * out_h * out_w, d_k * height * width)
        value = value.view(b, t, d_k, out_h, height, out_w, width)
        value = value.permute(0, 1, 3, 5, 2, 4, 6).contiguous().view(b, t * out_h * out_w, d_k * height * width)
        '\n            # 2) Apply attention on all the projected vectors in batch.\n            tmp1 = []\n            for q,k,v in zip(torch.chunk(query, b, dim=0), torch.chunk(key, b, dim=0), torch.chunk(value, b, dim=0)):\n                y, _ = self.attention(q.unsqueeze(0), k.unsqueeze(0), v.unsqueeze(0))\n                tmp1.append(y)\n            y = torch.cat(tmp1,1)\n            '
        y, _ = self.attention(query, key, value, mm)
        y = y.view(b, t, out_h, out_w, d_k, height, width)
        y = y.permute(0, 1, 4, 2, 5, 3, 6).contiguous().view(bt, d_k, h, w)
        output.append(y)
    output = torch.cat(output, 1)
    x = self.output_linear(output)
    return x

class FeedForward(nn.Module):

    def __init__(self, d_model):
        super(FeedForward, self).__init__()
        self.conv = nn.Sequential(nn.Conv2d(d_model, d_model, kernel_size=3, padding=2, dilation=2), nn.LeakyReLU(0.2, inplace=True), nn.Conv2d(d_model, d_model, kernel_size=3, padding=1), nn.LeakyReLU(0.2, inplace=True))

    def forward(self, x):
        x = self.conv(x)
        return x

def forward(self, x):
    x = self.conv(x)
    return x

class TransformerBlock(nn.Module):
    """
    Transformer = MultiHead_Attention + Feed_Forward with sublayer connection
    """

    def __init__(self, patchsize, hidden=128):
        super().__init__()
        self.attention = MultiHeadedAttention(patchsize, d_model=hidden)
        self.feed_forward = FeedForward(hidden)

    def forward(self, x):
        x, m, b, c = (x['x'], x['m'], x['b'], x['c'])
        x = x + self.attention(x, m, b, c)
        x = x + self.feed_forward(x)
        return {'x': x, 'm': m, 'b': b, 'c': c}

def forward(self, x):
    x, m, b, c = (x['x'], x['m'], x['b'], x['c'])
    x = x + self.attention(x, m, b, c)
    x = x + self.feed_forward(x)
    return {'x': x, 'm': m, 'b': b, 'c': c}

class deconv(nn.Module):

    def __init__(self, input_channel, output_channel, kernel_size=3, padding=0):
        super().__init__()
        self.conv = nn.Conv2d(input_channel, output_channel, kernel_size=kernel_size, stride=1, padding=padding)

    def forward(self, x):
        x = F.interpolate(x, scale_factor=2, mode='bilinear', align_corners=True)
        return self.conv(x)

def forward(self, x):
    x = F.interpolate(x, scale_factor=2, mode='bilinear', align_corners=True)
    return self.conv(x)

class MultiHeadedAttention(nn.Module):
    """
    Take in model size and number of heads.
    """

    def __init__(self, patchsize, d_model):
        super().__init__()
        self.patchsize = patchsize
        self.query_embedding = nn.Conv2d(d_model, d_model, kernel_size=1, padding=0)
        self.value_embedding = nn.Conv2d(d_model, d_model, kernel_size=1, padding=0)
        self.key_embedding = nn.Conv2d(d_model, d_model, kernel_size=1, padding=0)
        self.output_linear = nn.Sequential(nn.Conv2d(d_model, d_model, kernel_size=3, padding=1), nn.LeakyReLU(0.2, inplace=True))
        self.attention = Attention()

    def forward(self, x, m, b, c):
        bt, _, h, w = x.size()
        t = bt // b
        d_k = c // len(self.patchsize)
        output = []
        _query = self.query_embedding(x)
        _key = self.key_embedding(x)
        _value = self.value_embedding(x)
        for (width, height), query, key, value in zip(self.patchsize, torch.chunk(_query, len(self.patchsize), dim=1), torch.chunk(_key, len(self.patchsize), dim=1), torch.chunk(_value, len(self.patchsize), dim=1)):
            out_w, out_h = (w // width, h // height)
            mm = m.view(b, t, 1, out_h, height, out_w, width)
            mm = mm.permute(0, 1, 3, 5, 2, 4, 6).contiguous().view(b, t * out_h * out_w, height * width)
            mm = (mm.mean(-1) > 0.5).unsqueeze(1).repeat(1, t * out_h * out_w, 1)
            query = query.view(b, t, d_k, out_h, height, out_w, width)
            query = query.permute(0, 1, 3, 5, 2, 4, 6).contiguous().view(b, t * out_h * out_w, d_k * height * width)
            key = key.view(b, t, d_k, out_h, height, out_w, width)
            key = key.permute(0, 1, 3, 5, 2, 4, 6).contiguous().view(b, t * out_h * out_w, d_k * height * width)
            value = value.view(b, t, d_k, out_h, height, out_w, width)
            value = value.permute(0, 1, 3, 5, 2, 4, 6).contiguous().view(b, t * out_h * out_w, d_k * height * width)
            '\n            # 2) Apply attention on all the projected vectors in batch.\n            tmp1 = []\n            for q,k,v in zip(torch.chunk(query, b, dim=0), torch.chunk(key, b, dim=0), torch.chunk(value, b, dim=0)):\n                y, _ = self.attention(q.unsqueeze(0), k.unsqueeze(0), v.unsqueeze(0))\n                tmp1.append(y)\n            y = torch.cat(tmp1,1)\n            '
            y, attn = self.attention(query, key, value, mm)
            if width == 18:
                select_attn = attn.view(t, out_h * out_w, t, out_h, out_w)[0]
                select_mm = mm[0].view(t * out_h * out_w, t, out_h, out_w)[0]
            y = y.view(b, t, out_h, out_w, d_k, height, width)
            y = y.permute(0, 1, 4, 2, 5, 3, 6).contiguous().view(bt, d_k, h, w)
            output.append(y)
        output = torch.cat(output, 1)
        x = self.output_linear(output)
        return (x, select_attn, select_mm)

def forward(self, x, m, b, c):
    bt, _, h, w = x.size()
    t = bt // b
    d_k = c // len(self.patchsize)
    output = []
    _query = self.query_embedding(x)
    _key = self.key_embedding(x)
    _value = self.value_embedding(x)
    for (width, height), query, key, value in zip(self.patchsize, torch.chunk(_query, len(self.patchsize), dim=1), torch.chunk(_key, len(self.patchsize), dim=1), torch.chunk(_value, len(self.patchsize), dim=1)):
        out_w, out_h = (w // width, h // height)
        mm = m.view(b, t, 1, out_h, height, out_w, width)
        mm = mm.permute(0, 1, 3, 5, 2, 4, 6).contiguous().view(b, t * out_h * out_w, height * width)
        mm = (mm.mean(-1) > 0.5).unsqueeze(1).repeat(1, t * out_h * out_w, 1)
        query = query.view(b, t, d_k, out_h, height, out_w, width)
        query = query.permute(0, 1, 3, 5, 2, 4, 6).contiguous().view(b, t * out_h * out_w, d_k * height * width)
        key = key.view(b, t, d_k, out_h, height, out_w, width)
        key = key.permute(0, 1, 3, 5, 2, 4, 6).contiguous().view(b, t * out_h * out_w, d_k * height * width)
        value = value.view(b, t, d_k, out_h, height, out_w, width)
        value = value.permute(0, 1, 3, 5, 2, 4, 6).contiguous().view(b, t * out_h * out_w, d_k * height * width)
        '\n            # 2) Apply attention on all the projected vectors in batch.\n            tmp1 = []\n            for q,k,v in zip(torch.chunk(query, b, dim=0), torch.chunk(key, b, dim=0), torch.chunk(value, b, dim=0)):\n                y, _ = self.attention(q.unsqueeze(0), k.unsqueeze(0), v.unsqueeze(0))\n                tmp1.append(y)\n            y = torch.cat(tmp1,1)\n            '
        y, attn = self.attention(query, key, value, mm)
        if width == 18:
            select_attn = attn.view(t, out_h * out_w, t, out_h, out_w)[0]
            select_mm = mm[0].view(t * out_h * out_w, t, out_h, out_w)[0]
        y = y.view(b, t, out_h, out_w, d_k, height, width)
        y = y.permute(0, 1, 4, 2, 5, 3, 6).contiguous().view(bt, d_k, h, w)
        output.append(y)
    output = torch.cat(output, 1)
    x = self.output_linear(output)
    return (x, select_attn, select_mm)

class FeedForward(nn.Module):

    def __init__(self, d_model):
        super(FeedForward, self).__init__()
        self.conv = nn.Sequential(nn.Conv2d(d_model, d_model, kernel_size=3, padding=2, dilation=2), nn.LeakyReLU(0.2, inplace=True), nn.Conv2d(d_model, d_model, kernel_size=3, padding=1), nn.LeakyReLU(0.2, inplace=True))

    def forward(self, x):
        x = self.conv(x)
        return x

def forward(self, x):
    x = self.conv(x)
    return x

class TransformerBlock(nn.Module):
    """
    Transformer = MultiHead_Attention + Feed_Forward with sublayer connection
    """

    def __init__(self, patchsize, hidden=128):
        super().__init__()
        self.attention = MultiHeadedAttention(patchsize, d_model=hidden)
        self.feed_forward = FeedForward(hidden)

    def forward(self, x):
        x, m, b, c = (x['x'], x['m'], x['b'], x['c'])
        val, attn, mm = self.attention(x, m, b, c)
        x = x + val
        x = x + self.feed_forward(x)
        return {'x': x, 'm': m, 'b': b, 'c': c, 'attn': attn, 'smm': mm}

def forward(self, x):
    x, m, b, c = (x['x'], x['m'], x['b'], x['c'])
    val, attn, mm = self.attention(x, m, b, c)
    x = x + val
    x = x + self.feed_forward(x)
    return {'x': x, 'm': m, 'b': b, 'c': c, 'attn': attn, 'smm': mm}

class ToTorchFormatTensor(object):
    """ Converts a PIL.Image (RGB) or numpy.ndarray (H x W x C) in the range [0, 255]
    to a torch.FloatTensor of shape (C x H x W) in the range [0.0, 1.0] """

    def __init__(self, div=True):
        self.div = div

    def __call__(self, pic):
        if isinstance(pic, np.ndarray):
            img = torch.from_numpy(pic).permute(2, 3, 0, 1).contiguous()
        else:
            img = torch.ByteTensor(torch.ByteStorage.from_buffer(pic.tobytes()))
            img = img.view(pic.size[1], pic.size[0], len(pic.mode))
            img = img.transpose(0, 1).transpose(0, 2).contiguous()
        img = img.float().div(255) if self.div else img.float()
        return img

def __call__(self, pic):
    if isinstance(pic, np.ndarray):
        img = torch.from_numpy(pic).permute(2, 3, 0, 1).contiguous()
    else:
        img = torch.ByteTensor(torch.ByteStorage.from_buffer(pic.tobytes()))
        img = img.view(pic.size[1], pic.size[0], len(pic.mode))
        img = img.transpose(0, 1).transpose(0, 2).contiguous()
    img = img.float().div(255) if self.div else img.float()
    return img

class AdversarialLoss(nn.Module):
    """
    Adversarial loss
    https://arxiv.org/abs/1711.10337
    """

    def __init__(self, type='nsgan', target_real_label=1.0, target_fake_label=0.0):
        """
        type = nsgan | lsgan | hinge
        """
        super(AdversarialLoss, self).__init__()
        self.type = type
        self.register_buffer('real_label', torch.tensor(target_real_label))
        self.register_buffer('fake_label', torch.tensor(target_fake_label))
        if type == 'nsgan':
            self.criterion = nn.BCELoss()
        elif type == 'lsgan':
            self.criterion = nn.MSELoss()
        elif type == 'hinge':
            self.criterion = nn.ReLU()

    def __call__(self, outputs, is_real, is_disc=None):
        if self.type == 'hinge':
            if is_disc:
                if is_real:
                    outputs = -outputs
                return self.criterion(1 + outputs).mean()
            else:
                return (-outputs).mean()
        else:
            labels = (self.real_label if is_real else self.fake_label).expand_as(outputs)
            loss = self.criterion(outputs, labels)
            return loss

def __call__(self, outputs, is_real, is_disc=None):
    if self.type == 'hinge':
        if is_disc:
            if is_real:
                outputs = -outputs
            return self.criterion(1 + outputs).mean()
        else:
            return (-outputs).mean()
    else:
        labels = (self.real_label if is_real else self.fake_label).expand_as(outputs)
        loss = self.criterion(outputs, labels)
        return loss

class SpectralNorm(object):
    _version = 1

    def __init__(self, name='weight', n_power_iterations=1, dim=0, eps=1e-12):
        self.name = name
        self.dim = dim
        if n_power_iterations <= 0:
            raise ValueError('Expected n_power_iterations to be positive, but got n_power_iterations={}'.format(n_power_iterations))
        self.n_power_iterations = n_power_iterations
        self.eps = eps

    def reshape_weight_to_matrix(self, weight):
        weight_mat = weight
        if self.dim != 0:
            weight_mat = weight_mat.permute(self.dim, *[d for d in range(weight_mat.dim()) if d != self.dim])
        height = weight_mat.size(0)
        return weight_mat.reshape(height, -1)

    def compute_weight(self, module, do_power_iteration):
        weight = getattr(module, self.name + '_orig')
        u = getattr(module, self.name + '_u')
        v = getattr(module, self.name + '_v')
        weight_mat = self.reshape_weight_to_matrix(weight)
        if do_power_iteration:
            with torch.no_grad():
                for _ in range(self.n_power_iterations):
                    v = normalize(torch.mv(weight_mat.t(), u), dim=0, eps=self.eps, out=v)
                    u = normalize(torch.mv(weight_mat, v), dim=0, eps=self.eps, out=u)
                if self.n_power_iterations > 0:
                    u = u.clone()
                    v = v.clone()
        sigma = torch.dot(u, torch.mv(weight_mat, v))
        weight = weight / sigma
        return weight

    def remove(self, module):
        with torch.no_grad():
            weight = self.compute_weight(module, do_power_iteration=False)
        delattr(module, self.name)
        delattr(module, self.name + '_u')
        delattr(module, self.name + '_v')
        delattr(module, self.name + '_orig')
        module.register_parameter(self.name, torch.nn.Parameter(weight.detach()))

    def __call__(self, module, inputs):
        setattr(module, self.name, self.compute_weight(module, do_power_iteration=module.training))

    def _solve_v_and_rescale(self, weight_mat, u, target_sigma):
        v = torch.chain_matmul(weight_mat.t().mm(weight_mat).pinverse(), weight_mat.t(), u.unsqueeze(1)).squeeze(1)
        return v.mul_(target_sigma / torch.dot(u, torch.mv(weight_mat, v)))

    @staticmethod
    def apply(module, name, n_power_iterations, dim, eps):
        for k, hook in module._forward_pre_hooks.items():
            if isinstance(hook, SpectralNorm) and hook.name == name:
                raise RuntimeError('Cannot register two spectral_norm hooks on the same parameter {}'.format(name))
        fn = SpectralNorm(name, n_power_iterations, dim, eps)
        weight = module._parameters[name]
        with torch.no_grad():
            weight_mat = fn.reshape_weight_to_matrix(weight)
            h, w = weight_mat.size()
            u = normalize(weight.new_empty(h).normal_(0, 1), dim=0, eps=fn.eps)
            v = normalize(weight.new_empty(w).normal_(0, 1), dim=0, eps=fn.eps)
        delattr(module, fn.name)
        module.register_parameter(fn.name + '_orig', weight)
        setattr(module, fn.name, weight.data)
        module.register_buffer(fn.name + '_u', u)
        module.register_buffer(fn.name + '_v', v)
        module.register_forward_pre_hook(fn)
        module._register_state_dict_hook(SpectralNormStateDictHook(fn))
        module._register_load_state_dict_pre_hook(SpectralNormLoadStateDictPreHook(fn))
        return fn

def _solve_v_and_rescale(self, weight_mat, u, target_sigma):
    v = torch.chain_matmul(weight_mat.t().mm(weight_mat).pinverse(), weight_mat.t(), u.unsqueeze(1)).squeeze(1)
    return v.mul_(target_sigma / torch.dot(u, torch.mv(weight_mat, v)))

class SamPredictor:

    def __init__(self, sam_model: Sam) -> None:
        """
        Uses SAM to calculate the image embedding for an image, and then
        allow repeated, efficient mask prediction given prompts.

        Arguments:
          sam_model (Sam): The model to use for mask prediction.
        """
        super().__init__()
        self.model = sam_model
        self.transform = ResizeLongestSide(sam_model.image_encoder.img_size)
        self.reset_image()

    def set_image(self, image: np.ndarray, image_format: str='RGB') -> None:
        """
        Calculates the image embeddings for the provided image, allowing
        masks to be predicted with the 'predict' method.

        Arguments:
          image (np.ndarray): The image for calculating masks. Expects an
            image in HWC uint8 format, with pixel values in [0, 255].
          image_format (str): The color format of the image, in ['RGB', 'BGR'].
        """
        assert image_format in ['RGB', 'BGR'], f"image_format must be in ['RGB', 'BGR'], is {image_format}."
        if image_format != self.model.image_format:
            image = image[..., ::-1]
        input_image = self.transform.apply_image(image)
        input_image_torch = torch.as_tensor(input_image, device=self.device)
        input_image_torch = input_image_torch.permute(2, 0, 1).contiguous()[None, :, :, :]
        self.set_torch_image(input_image_torch, image.shape[:2])

    @torch.no_grad()
    def set_torch_image(self, transformed_image: torch.Tensor, original_image_size: Tuple[int, ...]) -> None:
        """
        Calculates the image embeddings for the provided image, allowing
        masks to be predicted with the 'predict' method. Expects the input
        image to be already transformed to the format expected by the model.

        Arguments:
          transformed_image (torch.Tensor): The input image, with shape
            1x3xHxW, which has been transformed with ResizeLongestSide.
          original_image_size (tuple(int, int)): The size of the image
            before transformation, in (H, W) format.
        """
        assert len(transformed_image.shape) == 4 and transformed_image.shape[1] == 3 and (max(*transformed_image.shape[2:]) == self.model.image_encoder.img_size), f'set_torch_image input must be BCHW with long side {self.model.image_encoder.img_size}.'
        self.reset_image()
        self.original_size = original_image_size
        self.input_size = tuple(transformed_image.shape[-2:])
        input_image = self.model.preprocess(transformed_image)
        self.features = self.model.image_encoder(input_image)
        self.is_image_set = True

    def predict(self, point_coords: Optional[np.ndarray]=None, point_labels: Optional[np.ndarray]=None, box: Optional[np.ndarray]=None, mask_input: Optional[np.ndarray]=None, multimask_output: bool=True, return_logits: bool=False) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Predict masks for the given input prompts, using the currently set image.

        Arguments:
          point_coords (np.ndarray or None): A Nx2 array of point prompts to the
            model. Each point is in (X,Y) in pixels.
          point_labels (np.ndarray or None): A length N array of labels for the
            point prompts. 1 indicates a foreground point and 0 indicates a
            background point.
          box (np.ndarray or None): A length 4 array given a box prompt to the
            model, in XYXY format.
          mask_input (np.ndarray): A low resolution mask input to the model, typically
            coming from a previous prediction iteration. Has form 1xHxW, where
            for SAM, H=W=256.
          multimask_output (bool): If true, the model will return three masks.
            For ambiguous input prompts (such as a single click), this will often
            produce better masks than a single prediction. If only a single
            mask is needed, the model's predicted quality score can be used
            to select the best mask. For non-ambiguous prompts, such as multiple
            input prompts, multimask_output=False can give better results.
          return_logits (bool): If true, returns un-thresholded masks logits
            instead of a binary mask.

        Returns:
          (np.ndarray): The output masks in CxHxW format, where C is the
            number of masks, and (H, W) is the original image size.
          (np.ndarray): An array of length C containing the model's
            predictions for the quality of each mask.
          (np.ndarray): An array of shape CxHxW, where C is the number
            of masks and H=W=256. These low resolution logits can be passed to
            a subsequent iteration as mask input.
        """
        if not self.is_image_set:
            raise RuntimeError('An image must be set with .set_image(...) before mask prediction.')
        coords_torch, labels_torch, box_torch, mask_input_torch = (None, None, None, None)
        if point_coords is not None:
            assert point_labels is not None, 'point_labels must be supplied if point_coords is supplied.'
            point_coords = self.transform.apply_coords(point_coords, self.original_size)
            coords_torch = torch.as_tensor(point_coords, dtype=torch.float, device=self.device)
            labels_torch = torch.as_tensor(point_labels, dtype=torch.int, device=self.device)
            coords_torch, labels_torch = (coords_torch[None, :, :], labels_torch[None, :])
        if box is not None:
            box = self.transform.apply_boxes(box, self.original_size)
            box_torch = torch.as_tensor(box, dtype=torch.float, device=self.device)
            box_torch = box_torch[None, :]
        if mask_input is not None:
            mask_input_torch = torch.as_tensor(mask_input, dtype=torch.float, device=self.device)
            mask_input_torch = mask_input_torch[None, :, :, :]
        masks, iou_predictions, low_res_masks = self.predict_torch(coords_torch, labels_torch, box_torch, mask_input_torch, multimask_output, return_logits=return_logits)
        masks = masks[0].detach().cpu().numpy()
        iou_predictions = iou_predictions[0].detach().cpu().numpy()
        low_res_masks = low_res_masks[0].detach().cpu().numpy()
        return (masks, iou_predictions, low_res_masks)

    @torch.no_grad()
    def predict_torch(self, point_coords: Optional[torch.Tensor], point_labels: Optional[torch.Tensor], boxes: Optional[torch.Tensor]=None, mask_input: Optional[torch.Tensor]=None, multimask_output: bool=True, return_logits: bool=False) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Predict masks for the given input prompts, using the currently set image.
        Input prompts are batched torch tensors and are expected to already be
        transformed to the input frame using ResizeLongestSide.

        Arguments:
          point_coords (torch.Tensor or None): A BxNx2 array of point prompts to the
            model. Each point is in (X,Y) in pixels.
          point_labels (torch.Tensor or None): A BxN array of labels for the
            point prompts. 1 indicates a foreground point and 0 indicates a
            background point.
          box (np.ndarray or None): A Bx4 array given a box prompt to the
            model, in XYXY format.
          mask_input (np.ndarray): A low resolution mask input to the model, typically
            coming from a previous prediction iteration. Has form Bx1xHxW, where
            for SAM, H=W=256. Masks returned by a previous iteration of the
            predict method do not need further transformation.
          multimask_output (bool): If true, the model will return three masks.
            For ambiguous input prompts (such as a single click), this will often
            produce better masks than a single prediction. If only a single
            mask is needed, the model's predicted quality score can be used
            to select the best mask. For non-ambiguous prompts, such as multiple
            input prompts, multimask_output=False can give better results.
          return_logits (bool): If true, returns un-thresholded masks logits
            instead of a binary mask.

        Returns:
          (torch.Tensor): The output masks in BxCxHxW format, where C is the
            number of masks, and (H, W) is the original image size.
          (torch.Tensor): An array of shape BxC containing the model's
            predictions for the quality of each mask.
          (torch.Tensor): An array of shape BxCxHxW, where C is the number
            of masks and H=W=256. These low res logits can be passed to
            a subsequent iteration as mask input.
        """
        if not self.is_image_set:
            raise RuntimeError('An image must be set with .set_image(...) before mask prediction.')
        if point_coords is not None:
            points = (point_coords, point_labels)
        else:
            points = None
        sparse_embeddings, dense_embeddings = self.model.prompt_encoder(points=points, boxes=boxes, masks=mask_input)
        low_res_masks, iou_predictions = self.model.mask_decoder(image_embeddings=self.features, image_pe=self.model.prompt_encoder.get_dense_pe(), sparse_prompt_embeddings=sparse_embeddings, dense_prompt_embeddings=dense_embeddings, multimask_output=multimask_output)
        masks = self.model.postprocess_masks(low_res_masks, self.input_size, self.original_size)
        if not return_logits:
            masks = masks > self.model.mask_threshold
        return (masks, iou_predictions, low_res_masks)

    def get_image_embedding(self) -> torch.Tensor:
        """
        Returns the image embeddings for the currently set image, with
        shape 1xCxHxW, where C is the embedding dimension and (H,W) are
        the embedding spatial dimension of SAM (typically C=256, H=W=64).
        """
        if not self.is_image_set:
            raise RuntimeError('An image must be set with .set_image(...) to generate an embedding.')
        assert self.features is not None, 'Features must exist if an image has been set.'
        return self.features

    @property
    def device(self) -> torch.device:
        return self.model.device

    def reset_image(self) -> None:
        """Resets the currently set image."""
        self.is_image_set = False
        self.features = None
        self.orig_h = None
        self.orig_w = None
        self.input_h = None
        self.input_w = None

def set_image(self, image: np.ndarray, image_format: str='RGB') -> None:
    """
        Calculates the image embeddings for the provided image, allowing
        masks to be predicted with the 'predict' method.

        Arguments:
          image (np.ndarray): The image for calculating masks. Expects an
            image in HWC uint8 format, with pixel values in [0, 255].
          image_format (str): The color format of the image, in ['RGB', 'BGR'].
        """
    assert image_format in ['RGB', 'BGR'], f"image_format must be in ['RGB', 'BGR'], is {image_format}."
    if image_format != self.model.image_format:
        image = image[..., ::-1]
    input_image = self.transform.apply_image(image)
    input_image_torch = torch.as_tensor(input_image, device=self.device)
    input_image_torch = input_image_torch.permute(2, 0, 1).contiguous()[None, :, :, :]
    self.set_torch_image(input_image_torch, image.shape[:2])

class ImageEncoderViT(nn.Module):

    def __init__(self, img_size: int=1024, patch_size: int=16, in_chans: int=3, embed_dim: int=768, depth: int=12, num_heads: int=12, mlp_ratio: float=4.0, out_chans: int=256, qkv_bias: bool=True, norm_layer: Type[nn.Module]=nn.LayerNorm, act_layer: Type[nn.Module]=nn.GELU, use_abs_pos: bool=True, use_rel_pos: bool=False, rel_pos_zero_init: bool=True, window_size: int=0, global_attn_indexes: Tuple[int, ...]=()) -> None:
        """
        Args:
            img_size (int): Input image size.
            patch_size (int): Patch size.
            in_chans (int): Number of input image channels.
            embed_dim (int): Patch embedding dimension.
            depth (int): Depth of ViT.
            num_heads (int): Number of attention heads in each ViT block.
            mlp_ratio (float): Ratio of mlp hidden dim to embedding dim.
            qkv_bias (bool): If True, add a learnable bias to query, key, value.
            norm_layer (nn.Module): Normalization layer.
            act_layer (nn.Module): Activation layer.
            use_abs_pos (bool): If True, use absolute positional embeddings.
            use_rel_pos (bool): If True, add relative positional embeddings to the attention map.
            rel_pos_zero_init (bool): If True, zero initialize relative positional parameters.
            window_size (int): Window size for window attention blocks.
            global_attn_indexes (list): Indexes for blocks using global attention.
        """
        super().__init__()
        self.img_size = img_size
        self.patch_embed = PatchEmbed(kernel_size=(patch_size, patch_size), stride=(patch_size, patch_size), in_chans=in_chans, embed_dim=embed_dim)
        self.pos_embed: Optional[nn.Parameter] = None
        if use_abs_pos:
            self.pos_embed = nn.Parameter(torch.zeros(1, img_size // patch_size, img_size // patch_size, embed_dim))
        self.blocks = nn.ModuleList()
        for i in range(depth):
            block = Block(dim=embed_dim, num_heads=num_heads, mlp_ratio=mlp_ratio, qkv_bias=qkv_bias, norm_layer=norm_layer, act_layer=act_layer, use_rel_pos=use_rel_pos, rel_pos_zero_init=rel_pos_zero_init, window_size=window_size if i not in global_attn_indexes else 0, input_size=(img_size // patch_size, img_size // patch_size))
            self.blocks.append(block)
        self.neck = nn.Sequential(nn.Conv2d(embed_dim, out_chans, kernel_size=1, bias=False), LayerNorm2d(out_chans), nn.Conv2d(out_chans, out_chans, kernel_size=3, padding=1, bias=False), LayerNorm2d(out_chans))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.patch_embed(x)
        if self.pos_embed is not None:
            x = x + self.pos_embed
        for blk in self.blocks:
            x = blk(x)
        x = self.neck(x.permute(0, 3, 1, 2))
        return x

def forward(self, x: torch.Tensor) -> torch.Tensor:
    x = self.patch_embed(x)
    if self.pos_embed is not None:
        x = x + self.pos_embed
    for blk in self.blocks:
        x = blk(x)
    x = self.neck(x.permute(0, 3, 1, 2))
    return x

class Attention(nn.Module):
    """Multi-head Attention block with relative position embeddings."""

    def __init__(self, dim: int, num_heads: int=8, qkv_bias: bool=True, use_rel_pos: bool=False, rel_pos_zero_init: bool=True, input_size: Optional[Tuple[int, int]]=None) -> None:
        """
        Args:
            dim (int): Number of input channels.
            num_heads (int): Number of attention heads.
            qkv_bias (bool:  If True, add a learnable bias to query, key, value.
            rel_pos (bool): If True, add relative positional embeddings to the attention map.
            rel_pos_zero_init (bool): If True, zero initialize relative positional parameters.
            input_size (int or None): Input resolution for calculating the relative positional
                parameter size.
        """
        super().__init__()
        self.num_heads = num_heads
        head_dim = dim // num_heads
        self.scale = head_dim ** (-0.5)
        self.qkv = nn.Linear(dim, dim * 3, bias=qkv_bias)
        self.proj = nn.Linear(dim, dim)
        self.use_rel_pos = use_rel_pos
        if self.use_rel_pos:
            assert input_size is not None, 'Input size must be provided if using relative positional encoding.'
            self.rel_pos_h = nn.Parameter(torch.zeros(2 * input_size[0] - 1, head_dim))
            self.rel_pos_w = nn.Parameter(torch.zeros(2 * input_size[1] - 1, head_dim))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        B, H, W, _ = x.shape
        qkv = self.qkv(x).reshape(B, H * W, 3, self.num_heads, -1).permute(2, 0, 3, 1, 4)
        q, k, v = qkv.reshape(3, B * self.num_heads, H * W, -1).unbind(0)
        attn = q * self.scale @ k.transpose(-2, -1)
        if self.use_rel_pos:
            attn = add_decomposed_rel_pos(attn, q, self.rel_pos_h, self.rel_pos_w, (H, W), (H, W))
        attn = attn.softmax(dim=-1)
        x = (attn @ v).view(B, self.num_heads, H, W, -1).permute(0, 2, 3, 1, 4).reshape(B, H, W, -1)
        x = self.proj(x)
        return x

def forward(self, x: torch.Tensor) -> torch.Tensor:
    B, H, W, _ = x.shape
    qkv = self.qkv(x).reshape(B, H * W, 3, self.num_heads, -1).permute(2, 0, 3, 1, 4)
    q, k, v = qkv.reshape(3, B * self.num_heads, H * W, -1).unbind(0)
    attn = q * self.scale @ k.transpose(-2, -1)
    if self.use_rel_pos:
        attn = add_decomposed_rel_pos(attn, q, self.rel_pos_h, self.rel_pos_w, (H, W), (H, W))
    attn = attn.softmax(dim=-1)
    x = (attn @ v).view(B, self.num_heads, H, W, -1).permute(0, 2, 3, 1, 4).reshape(B, H, W, -1)
    x = self.proj(x)
    return x

def window_partition(x: torch.Tensor, window_size: int) -> Tuple[torch.Tensor, Tuple[int, int]]:
    """
    Partition into non-overlapping windows with padding if needed.
    Args:
        x (tensor): input tokens with [B, H, W, C].
        window_size (int): window size.

    Returns:
        windows: windows after partition with [B * num_windows, window_size, window_size, C].
        (Hp, Wp): padded height and width before partition
    """
    B, H, W, C = x.shape
    pad_h = (window_size - H % window_size) % window_size
    pad_w = (window_size - W % window_size) % window_size
    if pad_h > 0 or pad_w > 0:
        x = F.pad(x, (0, 0, 0, pad_w, 0, pad_h))
    Hp, Wp = (H + pad_h, W + pad_w)
    x = x.view(B, Hp // window_size, window_size, Wp // window_size, window_size, C)
    windows = x.permute(0, 1, 3, 2, 4, 5).contiguous().view(-1, window_size, window_size, C)
    return (windows, (Hp, Wp))

def window_unpartition(windows: torch.Tensor, window_size: int, pad_hw: Tuple[int, int], hw: Tuple[int, int]) -> torch.Tensor:
    """
    Window unpartition into original sequences and removing padding.
    Args:
        x (tensor): input tokens with [B * num_windows, window_size, window_size, C].
        window_size (int): window size.
        pad_hw (Tuple): padded height and width (Hp, Wp).
        hw (Tuple): original height and width (H, W) before padding.

    Returns:
        x: unpartitioned sequences with [B, H, W, C].
    """
    Hp, Wp = pad_hw
    H, W = hw
    B = windows.shape[0] // (Hp * Wp // window_size // window_size)
    x = windows.view(B, Hp // window_size, Wp // window_size, window_size, window_size, -1)
    x = x.permute(0, 1, 3, 2, 4, 5).contiguous().view(B, Hp, Wp, -1)
    if Hp > H or Wp > W:
        x = x[:, :H, :W, :].contiguous()
    return x

def get_rel_pos(q_size: int, k_size: int, rel_pos: torch.Tensor) -> torch.Tensor:
    """
    Get relative positional embeddings according to the relative positions of
        query and key sizes.
    Args:
        q_size (int): size of query q.
        k_size (int): size of key k.
        rel_pos (Tensor): relative position embeddings (L, C).

    Returns:
        Extracted positional embeddings according to relative positions.
    """
    max_rel_dist = int(2 * max(q_size, k_size) - 1)
    if rel_pos.shape[0] != max_rel_dist:
        rel_pos_resized = F.interpolate(rel_pos.reshape(1, rel_pos.shape[0], -1).permute(0, 2, 1), size=max_rel_dist, mode='linear')
        rel_pos_resized = rel_pos_resized.reshape(-1, max_rel_dist).permute(1, 0)
    else:
        rel_pos_resized = rel_pos
    q_coords = torch.arange(q_size)[:, None] * max(k_size / q_size, 1.0)
    k_coords = torch.arange(k_size)[None, :] * max(q_size / k_size, 1.0)
    relative_coords = q_coords - k_coords + (k_size - 1) * max(q_size / k_size, 1.0)
    return rel_pos_resized[relative_coords.long()]

def add_decomposed_rel_pos(attn: torch.Tensor, q: torch.Tensor, rel_pos_h: torch.Tensor, rel_pos_w: torch.Tensor, q_size: Tuple[int, int], k_size: Tuple[int, int]) -> torch.Tensor:
    """
    Calculate decomposed Relative Positional Embeddings from :paper:`mvitv2`.
    https://github.com/facebookresearch/mvit/blob/19786631e330df9f3622e5402b4a419a263a2c80/mvit/models/attention.py   # noqa B950
    Args:
        attn (Tensor): attention map.
        q (Tensor): query q in the attention layer with shape (B, q_h * q_w, C).
        rel_pos_h (Tensor): relative position embeddings (Lh, C) for height axis.
        rel_pos_w (Tensor): relative position embeddings (Lw, C) for width axis.
        q_size (Tuple): spatial sequence size of query q with (q_h, q_w).
        k_size (Tuple): spatial sequence size of key k with (k_h, k_w).

    Returns:
        attn (Tensor): attention map with added relative positional embeddings.
    """
    q_h, q_w = q_size
    k_h, k_w = k_size
    Rh = get_rel_pos(q_h, k_h, rel_pos_h)
    Rw = get_rel_pos(q_w, k_w, rel_pos_w)
    B, _, dim = q.shape
    r_q = q.reshape(B, q_h, q_w, dim)
    rel_h = torch.einsum('bhwc,hkc->bhwk', r_q, Rh)
    rel_w = torch.einsum('bhwc,wkc->bhwk', r_q, Rw)
    attn = (attn.view(B, q_h, q_w, k_h, k_w) + rel_h[:, :, :, :, None] + rel_w[:, :, :, None, :]).view(B, q_h * q_w, k_h * k_w)
    return attn

class PatchEmbed(nn.Module):
    """
    Image to Patch Embedding.
    """

    def __init__(self, kernel_size: Tuple[int, int]=(16, 16), stride: Tuple[int, int]=(16, 16), padding: Tuple[int, int]=(0, 0), in_chans: int=3, embed_dim: int=768) -> None:
        """
        Args:
            kernel_size (Tuple): kernel size of the projection layer.
            stride (Tuple): stride of the projection layer.
            padding (Tuple): padding size of the projection layer.
            in_chans (int): Number of input image channels.
            embed_dim (int):  embed_dim (int): Patch embedding dimension.
        """
        super().__init__()
        self.proj = nn.Conv2d(in_chans, embed_dim, kernel_size=kernel_size, stride=stride, padding=padding)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.proj(x)
        x = x.permute(0, 2, 3, 1)
        return x

def forward(self, x: torch.Tensor) -> torch.Tensor:
    x = self.proj(x)
    x = x.permute(0, 2, 3, 1)
    return x

class Sam(nn.Module):
    mask_threshold: float = 0.0
    image_format: str = 'RGB'

    def __init__(self, image_encoder: Union[ImageEncoderViT, TinyViT], prompt_encoder: PromptEncoder, mask_decoder: MaskDecoder, pixel_mean: List[float]=[123.675, 116.28, 103.53], pixel_std: List[float]=[58.395, 57.12, 57.375]) -> None:
        """
        SAM predicts object masks from an image and input prompts.

        Arguments:
          image_encoder (ImageEncoderViT): The backbone used to encode the
            image into image embeddings that allow for efficient mask prediction.
          prompt_encoder (PromptEncoder): Encodes various types of input prompts.
          mask_decoder (MaskDecoder): Predicts masks from the image embeddings
            and encoded prompts.
          pixel_mean (list(float)): Mean values for normalizing pixels in the input image.
          pixel_std (list(float)): Std values for normalizing pixels in the input image.
        """
        super().__init__()
        self.image_encoder = image_encoder
        self.prompt_encoder = prompt_encoder
        self.mask_decoder = mask_decoder
        self.register_buffer('pixel_mean', torch.Tensor(pixel_mean).view(-1, 1, 1), False)
        self.register_buffer('pixel_std', torch.Tensor(pixel_std).view(-1, 1, 1), False)

    @property
    def device(self) -> Any:
        return self.pixel_mean.device

    @torch.no_grad()
    def forward(self, batched_input: List[Dict[str, Any]], multimask_output: bool) -> List[Dict[str, torch.Tensor]]:
        """
        Predicts masks end-to-end from provided images and prompts.
        If prompts are not known in advance, using SamPredictor is
        recommended over calling the model directly.

        Arguments:
          batched_input (list(dict)): A list over input images, each a
            dictionary with the following keys. A prompt key can be
            excluded if it is not present.
              'image': The image as a torch tensor in 3xHxW format,
                already transformed for input to the model.
              'original_size': (tuple(int, int)) The original size of
                the image before transformation, as (H, W).
              'point_coords': (torch.Tensor) Batched point prompts for
                this image, with shape BxNx2. Already transformed to the
                input frame of the model.
              'point_labels': (torch.Tensor) Batched labels for point prompts,
                with shape BxN.
              'boxes': (torch.Tensor) Batched box inputs, with shape Bx4.
                Already transformed to the input frame of the model.
              'mask_inputs': (torch.Tensor) Batched mask inputs to the model,
                in the form Bx1xHxW.
          multimask_output (bool): Whether the model should predict multiple
            disambiguating masks, or return a single mask.

        Returns:
          (list(dict)): A list over input images, where each element is
            as dictionary with the following keys.
              'masks': (torch.Tensor) Batched binary mask predictions,
                with shape BxCxHxW, where B is the number of input promts,
                C is determiend by multimask_output, and (H, W) is the
                original size of the image.
              'iou_predictions': (torch.Tensor) The model's predictions
                of mask quality, in shape BxC.
              'low_res_logits': (torch.Tensor) Low resolution logits with
                shape BxCxHxW, where H=W=256. Can be passed as mask input
                to subsequent iterations of prediction.
        """
        input_images = torch.stack([self.preprocess(x['image']) for x in batched_input], dim=0)
        image_embeddings = self.image_encoder(input_images)
        outputs = []
        for image_record, curr_embedding in zip(batched_input, image_embeddings):
            if 'point_coords' in image_record:
                points = (image_record['point_coords'], image_record['point_labels'])
            else:
                points = None
            sparse_embeddings, dense_embeddings = self.prompt_encoder(points=points, boxes=image_record.get('boxes', None), masks=image_record.get('mask_inputs', None))
            low_res_masks, iou_predictions = self.mask_decoder(image_embeddings=curr_embedding.unsqueeze(0), image_pe=self.prompt_encoder.get_dense_pe(), sparse_prompt_embeddings=sparse_embeddings, dense_prompt_embeddings=dense_embeddings, multimask_output=multimask_output)
            masks = self.postprocess_masks(low_res_masks, input_size=image_record['image'].shape[-2:], original_size=image_record['original_size'])
            masks = masks > self.mask_threshold
            outputs.append({'masks': masks, 'iou_predictions': iou_predictions, 'low_res_logits': low_res_masks})
        return outputs

    def postprocess_masks(self, masks: torch.Tensor, input_size: Tuple[int, ...], original_size: Tuple[int, ...]) -> torch.Tensor:
        """
        Remove padding and upscale masks to the original image size.

        Arguments:
          masks (torch.Tensor): Batched masks from the mask_decoder,
            in BxCxHxW format.
          input_size (tuple(int, int)): The size of the image input to the
            model, in (H, W) format. Used to remove padding.
          original_size (tuple(int, int)): The original size of the image
            before resizing for input to the model, in (H, W) format.

        Returns:
          (torch.Tensor): Batched masks in BxCxHxW format, where (H, W)
            is given by original_size.
        """
        masks = F.interpolate(masks, (self.image_encoder.img_size, self.image_encoder.img_size), mode='bilinear', align_corners=False)
        masks = masks[..., :input_size[0], :input_size[1]]
        masks = F.interpolate(masks, original_size, mode='bilinear', align_corners=False)
        return masks

    def preprocess(self, x: torch.Tensor) -> torch.Tensor:
        """Normalize pixel values and pad to a square input."""
        x = (x - self.pixel_mean) / self.pixel_std
        h, w = x.shape[-2:]
        padh = self.image_encoder.img_size - h
        padw = self.image_encoder.img_size - w
        x = F.pad(x, (0, padw, 0, padh))
        return x

def postprocess_masks(self, masks: torch.Tensor, input_size: Tuple[int, ...], original_size: Tuple[int, ...]) -> torch.Tensor:
    """
        Remove padding and upscale masks to the original image size.

        Arguments:
          masks (torch.Tensor): Batched masks from the mask_decoder,
            in BxCxHxW format.
          input_size (tuple(int, int)): The size of the image input to the
            model, in (H, W) format. Used to remove padding.
          original_size (tuple(int, int)): The original size of the image
            before resizing for input to the model, in (H, W) format.

        Returns:
          (torch.Tensor): Batched masks in BxCxHxW format, where (H, W)
            is given by original_size.
        """
    masks = F.interpolate(masks, (self.image_encoder.img_size, self.image_encoder.img_size), mode='bilinear', align_corners=False)
    masks = masks[..., :input_size[0], :input_size[1]]
    masks = F.interpolate(masks, original_size, mode='bilinear', align_corners=False)
    return masks

def preprocess(self, x: torch.Tensor) -> torch.Tensor:
    """Normalize pixel values and pad to a square input."""
    x = (x - self.pixel_mean) / self.pixel_std
    h, w = x.shape[-2:]
    padh = self.image_encoder.img_size - h
    padw = self.image_encoder.img_size - w
    x = F.pad(x, (0, padw, 0, padh))
    return x

class MaskDecoder(nn.Module):

    def __init__(self, *, transformer_dim: int, transformer: nn.Module, num_multimask_outputs: int=3, activation: Type[nn.Module]=nn.GELU, iou_head_depth: int=3, iou_head_hidden_dim: int=256) -> None:
        """
        Predicts masks given an image and prompt embeddings, using a
        tranformer architecture.

        Arguments:
          transformer_dim (int): the channel dimension of the transformer
          transformer (nn.Module): the transformer used to predict masks
          num_multimask_outputs (int): the number of masks to predict
            when disambiguating masks
          activation (nn.Module): the type of activation to use when
            upscaling masks
          iou_head_depth (int): the depth of the MLP used to predict
            mask quality
          iou_head_hidden_dim (int): the hidden dimension of the MLP
            used to predict mask quality
        """
        super().__init__()
        self.transformer_dim = transformer_dim
        self.transformer = transformer
        self.num_multimask_outputs = num_multimask_outputs
        self.iou_token = nn.Embedding(1, transformer_dim)
        self.num_mask_tokens = num_multimask_outputs + 1
        self.mask_tokens = nn.Embedding(self.num_mask_tokens, transformer_dim)
        self.output_upscaling = nn.Sequential(nn.ConvTranspose2d(transformer_dim, transformer_dim // 4, kernel_size=2, stride=2), LayerNorm2d(transformer_dim // 4), activation(), nn.ConvTranspose2d(transformer_dim // 4, transformer_dim // 8, kernel_size=2, stride=2), activation())
        self.output_hypernetworks_mlps = nn.ModuleList([MLP(transformer_dim, transformer_dim, transformer_dim // 8, 3) for i in range(self.num_mask_tokens)])
        self.iou_prediction_head = MLP(transformer_dim, iou_head_hidden_dim, self.num_mask_tokens, iou_head_depth)

    def forward(self, image_embeddings: torch.Tensor, image_pe: torch.Tensor, sparse_prompt_embeddings: torch.Tensor, dense_prompt_embeddings: torch.Tensor, multimask_output: bool) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Predict masks given image and prompt embeddings.

        Arguments:
          image_embeddings (torch.Tensor): the embeddings from the image encoder
          image_pe (torch.Tensor): positional encoding with the shape of image_embeddings
          sparse_prompt_embeddings (torch.Tensor): the embeddings of the points and boxes
          dense_prompt_embeddings (torch.Tensor): the embeddings of the mask inputs
          multimask_output (bool): Whether to return multiple masks or a single
            mask.

        Returns:
          torch.Tensor: batched predicted masks
          torch.Tensor: batched predictions of mask quality
        """
        masks, iou_pred = self.predict_masks(image_embeddings=image_embeddings, image_pe=image_pe, sparse_prompt_embeddings=sparse_prompt_embeddings, dense_prompt_embeddings=dense_prompt_embeddings)
        if multimask_output:
            mask_slice = slice(1, None)
        else:
            mask_slice = slice(0, 1)
        masks = masks[:, mask_slice, :, :]
        iou_pred = iou_pred[:, mask_slice]
        return (masks, iou_pred)

    def predict_masks(self, image_embeddings: torch.Tensor, image_pe: torch.Tensor, sparse_prompt_embeddings: torch.Tensor, dense_prompt_embeddings: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Predicts masks. See 'forward' for more details."""
        output_tokens = torch.cat([self.iou_token.weight, self.mask_tokens.weight], dim=0)
        output_tokens = output_tokens.unsqueeze(0).expand(sparse_prompt_embeddings.size(0), -1, -1)
        tokens = torch.cat((output_tokens, sparse_prompt_embeddings), dim=1)
        src = torch.repeat_interleave(image_embeddings, tokens.shape[0], dim=0)
        src = src + dense_prompt_embeddings
        pos_src = torch.repeat_interleave(image_pe, tokens.shape[0], dim=0)
        b, c, h, w = src.shape
        hs, src = self.transformer(src, pos_src, tokens)
        iou_token_out = hs[:, 0, :]
        mask_tokens_out = hs[:, 1:1 + self.num_mask_tokens, :]
        src = src.transpose(1, 2).view(b, c, h, w)
        upscaled_embedding = self.output_upscaling(src)
        hyper_in_list: List[torch.Tensor] = []
        for i in range(self.num_mask_tokens):
            hyper_in_list.append(self.output_hypernetworks_mlps[i](mask_tokens_out[:, i, :]))
        hyper_in = torch.stack(hyper_in_list, dim=1)
        b, c, h, w = upscaled_embedding.shape
        masks = (hyper_in @ upscaled_embedding.view(b, c, h * w)).view(b, -1, h, w)
        iou_pred = self.iou_prediction_head(iou_token_out)
        return (masks, iou_pred)

def predict_masks(self, image_embeddings: torch.Tensor, image_pe: torch.Tensor, sparse_prompt_embeddings: torch.Tensor, dense_prompt_embeddings: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
    """Predicts masks. See 'forward' for more details."""
    output_tokens = torch.cat([self.iou_token.weight, self.mask_tokens.weight], dim=0)
    output_tokens = output_tokens.unsqueeze(0).expand(sparse_prompt_embeddings.size(0), -1, -1)
    tokens = torch.cat((output_tokens, sparse_prompt_embeddings), dim=1)
    src = torch.repeat_interleave(image_embeddings, tokens.shape[0], dim=0)
    src = src + dense_prompt_embeddings
    pos_src = torch.repeat_interleave(image_pe, tokens.shape[0], dim=0)
    b, c, h, w = src.shape
    hs, src = self.transformer(src, pos_src, tokens)
    iou_token_out = hs[:, 0, :]
    mask_tokens_out = hs[:, 1:1 + self.num_mask_tokens, :]
    src = src.transpose(1, 2).view(b, c, h, w)
    upscaled_embedding = self.output_upscaling(src)
    hyper_in_list: List[torch.Tensor] = []
    for i in range(self.num_mask_tokens):
        hyper_in_list.append(self.output_hypernetworks_mlps[i](mask_tokens_out[:, i, :]))
    hyper_in = torch.stack(hyper_in_list, dim=1)
    b, c, h, w = upscaled_embedding.shape
    masks = (hyper_in @ upscaled_embedding.view(b, c, h * w)).view(b, -1, h, w)
    iou_pred = self.iou_prediction_head(iou_token_out)
    return (masks, iou_pred)

class PromptEncoder(nn.Module):

    def __init__(self, embed_dim: int, image_embedding_size: Tuple[int, int], input_image_size: Tuple[int, int], mask_in_chans: int, activation: Type[nn.Module]=nn.GELU) -> None:
        """
        Encodes prompts for input to SAM's mask decoder.

        Arguments:
          embed_dim (int): The prompts' embedding dimension
          image_embedding_size (tuple(int, int)): The spatial size of the
            image embedding, as (H, W).
          input_image_size (int): The padded size of the image as input
            to the image encoder, as (H, W).
          mask_in_chans (int): The number of hidden channels used for
            encoding input masks.
          activation (nn.Module): The activation to use when encoding
            input masks.
        """
        super().__init__()
        self.embed_dim = embed_dim
        self.input_image_size = input_image_size
        self.image_embedding_size = image_embedding_size
        self.pe_layer = PositionEmbeddingRandom(embed_dim // 2)
        self.num_point_embeddings: int = 4
        point_embeddings = [nn.Embedding(1, embed_dim) for i in range(self.num_point_embeddings)]
        self.point_embeddings = nn.ModuleList(point_embeddings)
        self.not_a_point_embed = nn.Embedding(1, embed_dim)
        self.mask_input_size = (4 * image_embedding_size[0], 4 * image_embedding_size[1])
        self.mask_downscaling = nn.Sequential(nn.Conv2d(1, mask_in_chans // 4, kernel_size=2, stride=2), LayerNorm2d(mask_in_chans // 4), activation(), nn.Conv2d(mask_in_chans // 4, mask_in_chans, kernel_size=2, stride=2), LayerNorm2d(mask_in_chans), activation(), nn.Conv2d(mask_in_chans, embed_dim, kernel_size=1))
        self.no_mask_embed = nn.Embedding(1, embed_dim)

    def get_dense_pe(self) -> torch.Tensor:
        """
        Returns the positional encoding used to encode point prompts,
        applied to a dense set of points the shape of the image encoding.

        Returns:
          torch.Tensor: Positional encoding with shape
            1x(embed_dim)x(embedding_h)x(embedding_w)
        """
        return self.pe_layer(self.image_embedding_size).unsqueeze(0)

    def _embed_points(self, points: torch.Tensor, labels: torch.Tensor, pad: bool) -> torch.Tensor:
        """Embeds point prompts."""
        points = points + 0.5
        if pad:
            padding_point = torch.zeros((points.shape[0], 1, 2), device=points.device)
            padding_label = -torch.ones((labels.shape[0], 1), device=labels.device)
            points = torch.cat([points, padding_point], dim=1)
            labels = torch.cat([labels, padding_label], dim=1)
        point_embedding = self.pe_layer.forward_with_coords(points, self.input_image_size)
        point_embedding[labels == -1] = 0.0
        point_embedding[labels == -1] += self.not_a_point_embed.weight
        point_embedding[labels == 0] += self.point_embeddings[0].weight
        point_embedding[labels == 1] += self.point_embeddings[1].weight
        return point_embedding

    def _embed_boxes(self, boxes: torch.Tensor) -> torch.Tensor:
        """Embeds box prompts."""
        boxes = boxes + 0.5
        coords = boxes.reshape(-1, 2, 2)
        corner_embedding = self.pe_layer.forward_with_coords(coords, self.input_image_size)
        corner_embedding[:, 0, :] += self.point_embeddings[2].weight
        corner_embedding[:, 1, :] += self.point_embeddings[3].weight
        return corner_embedding

    def _embed_masks(self, masks: torch.Tensor) -> torch.Tensor:
        """Embeds mask inputs."""
        mask_embedding = self.mask_downscaling(masks)
        return mask_embedding

    def _get_batch_size(self, points: Optional[Tuple[torch.Tensor, torch.Tensor]], boxes: Optional[torch.Tensor], masks: Optional[torch.Tensor]) -> int:
        """
        Gets the batch size of the output given the batch size of the input prompts.
        """
        if points is not None:
            return points[0].shape[0]
        elif boxes is not None:
            return boxes.shape[0]
        elif masks is not None:
            return masks.shape[0]
        else:
            return 1

    def _get_device(self) -> torch.device:
        return self.point_embeddings[0].weight.device

    def forward(self, points: Optional[Tuple[torch.Tensor, torch.Tensor]], boxes: Optional[torch.Tensor], masks: Optional[torch.Tensor]) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Embeds different types of prompts, returning both sparse and dense
        embeddings.

        Arguments:
          points (tuple(torch.Tensor, torch.Tensor) or none): point coordinates
            and labels to embed.
          boxes (torch.Tensor or none): boxes to embed
          masks (torch.Tensor or none): masks to embed

        Returns:
          torch.Tensor: sparse embeddings for the points and boxes, with shape
            BxNx(embed_dim), where N is determined by the number of input points
            and boxes.
          torch.Tensor: dense embeddings for the masks, in the shape
            Bx(embed_dim)x(embed_H)x(embed_W)
        """
        bs = self._get_batch_size(points, boxes, masks)
        sparse_embeddings = torch.empty((bs, 0, self.embed_dim), device=self._get_device())
        if points is not None:
            coords, labels = points
            point_embeddings = self._embed_points(coords, labels, pad=boxes is None)
            sparse_embeddings = torch.cat([sparse_embeddings, point_embeddings], dim=1)
        if boxes is not None:
            box_embeddings = self._embed_boxes(boxes)
            sparse_embeddings = torch.cat([sparse_embeddings, box_embeddings], dim=1)
        if masks is not None:
            dense_embeddings = self._embed_masks(masks)
        else:
            dense_embeddings = self.no_mask_embed.weight.reshape(1, -1, 1, 1).expand(bs, -1, self.image_embedding_size[0], self.image_embedding_size[1])
        return (sparse_embeddings, dense_embeddings)

def get_dense_pe(self) -> torch.Tensor:
    """
        Returns the positional encoding used to encode point prompts,
        applied to a dense set of points the shape of the image encoding.

        Returns:
          torch.Tensor: Positional encoding with shape
            1x(embed_dim)x(embedding_h)x(embedding_w)
        """
    return self.pe_layer(self.image_embedding_size).unsqueeze(0)

class ConvLayer(nn.Module):

    def __init__(self, dim, input_resolution, depth, activation, drop_path=0.0, downsample=None, use_checkpoint=False, out_dim=None, conv_expand_ratio=4.0):
        super().__init__()
        self.dim = dim
        self.input_resolution = input_resolution
        self.depth = depth
        self.use_checkpoint = use_checkpoint
        self.blocks = nn.ModuleList([MBConv(dim, dim, conv_expand_ratio, activation, drop_path[i] if isinstance(drop_path, list) else drop_path) for i in range(depth)])
        if downsample is not None:
            self.downsample = downsample(input_resolution, dim=dim, out_dim=out_dim, activation=activation)
        else:
            self.downsample = None

    def forward(self, x):
        for blk in self.blocks:
            if self.use_checkpoint:
                x = checkpoint.checkpoint(blk, x)
            else:
                x = blk(x)
        if self.downsample is not None:
            x = self.downsample(x)
        return x

def forward(self, x):
    for blk in self.blocks:
        if self.use_checkpoint:
            x = checkpoint.checkpoint(blk, x)
        else:
            x = blk(x)
    if self.downsample is not None:
        x = self.downsample(x)
    return x

class Attention(torch.nn.Module):

    def __init__(self, dim, key_dim, num_heads=8, attn_ratio=4, resolution=(14, 14)):
        super().__init__()
        assert isinstance(resolution, tuple) and len(resolution) == 2
        self.num_heads = num_heads
        self.scale = key_dim ** (-0.5)
        self.key_dim = key_dim
        self.nh_kd = nh_kd = key_dim * num_heads
        self.d = int(attn_ratio * key_dim)
        self.dh = int(attn_ratio * key_dim) * num_heads
        self.attn_ratio = attn_ratio
        h = self.dh + nh_kd * 2
        self.norm = nn.LayerNorm(dim)
        self.qkv = nn.Linear(dim, h)
        self.proj = nn.Linear(self.dh, dim)
        points = list(itertools.product(range(resolution[0]), range(resolution[1])))
        N = len(points)
        attention_offsets = {}
        idxs = []
        for p1 in points:
            for p2 in points:
                offset = (abs(p1[0] - p2[0]), abs(p1[1] - p2[1]))
                if offset not in attention_offsets:
                    attention_offsets[offset] = len(attention_offsets)
                idxs.append(attention_offsets[offset])
        self.attention_biases = torch.nn.Parameter(torch.zeros(num_heads, len(attention_offsets)))
        self.register_buffer('attention_bias_idxs', torch.LongTensor(idxs).view(N, N), persistent=False)

    @torch.no_grad()
    def train(self, mode=True):
        super().train(mode)
        if mode and hasattr(self, 'ab'):
            del self.ab
        else:
            self.register_buffer('ab', self.attention_biases[:, self.attention_bias_idxs], persistent=False)

    def forward(self, x):
        B, N, _ = x.shape
        x = self.norm(x)
        qkv = self.qkv(x)
        q, k, v = qkv.view(B, N, self.num_heads, -1).split([self.key_dim, self.key_dim, self.d], dim=3)
        q = q.permute(0, 2, 1, 3)
        k = k.permute(0, 2, 1, 3)
        v = v.permute(0, 2, 1, 3)
        attn = q @ k.transpose(-2, -1) * self.scale + (self.attention_biases[:, self.attention_bias_idxs] if self.training else self.ab)
        attn = attn.softmax(dim=-1)
        x = (attn @ v).transpose(1, 2).reshape(B, N, self.dh)
        x = self.proj(x)
        return x

def forward(self, x):
    B, N, _ = x.shape
    x = self.norm(x)
    qkv = self.qkv(x)
    q, k, v = qkv.view(B, N, self.num_heads, -1).split([self.key_dim, self.key_dim, self.d], dim=3)
    q = q.permute(0, 2, 1, 3)
    k = k.permute(0, 2, 1, 3)
    v = v.permute(0, 2, 1, 3)
    attn = q @ k.transpose(-2, -1) * self.scale + (self.attention_biases[:, self.attention_bias_idxs] if self.training else self.ab)
    attn = attn.softmax(dim=-1)
    x = (attn @ v).transpose(1, 2).reshape(B, N, self.dh)
    x = self.proj(x)
    return x

class TinyViTBlock(nn.Module):
    """ TinyViT Block.

    Args:
        dim (int): Number of input channels.
        input_resolution (tuple[int, int]): Input resulotion.
        num_heads (int): Number of attention heads.
        window_size (int): Window size.
        mlp_ratio (float): Ratio of mlp hidden dim to embedding dim.
        drop (float, optional): Dropout rate. Default: 0.0
        drop_path (float, optional): Stochastic depth rate. Default: 0.0
        local_conv_size (int): the kernel size of the convolution between
                               Attention and MLP. Default: 3
        activation: the activation function. Default: nn.GELU
    """

    def __init__(self, dim, input_resolution, num_heads, window_size=7, mlp_ratio=4.0, drop=0.0, drop_path=0.0, local_conv_size=3, activation=nn.GELU):
        super().__init__()
        self.dim = dim
        self.input_resolution = input_resolution
        self.num_heads = num_heads
        assert window_size > 0, 'window_size must be greater than 0'
        self.window_size = window_size
        self.mlp_ratio = mlp_ratio
        self.drop_path = DropPath(drop_path) if drop_path > 0.0 else nn.Identity()
        assert dim % num_heads == 0, 'dim must be divisible by num_heads'
        head_dim = dim // num_heads
        window_resolution = (window_size, window_size)
        self.attn = Attention(dim, head_dim, num_heads, attn_ratio=1, resolution=window_resolution)
        mlp_hidden_dim = int(dim * mlp_ratio)
        mlp_activation = activation
        self.mlp = Mlp(in_features=dim, hidden_features=mlp_hidden_dim, act_layer=mlp_activation, drop=drop)
        pad = local_conv_size // 2
        self.local_conv = Conv2d_BN(dim, dim, ks=local_conv_size, stride=1, pad=pad, groups=dim)

    def forward(self, x):
        H, W = self.input_resolution
        B, L, C = x.shape
        assert L == H * W, 'input feature has wrong size'
        res_x = x
        if H == self.window_size and W == self.window_size:
            x = self.attn(x)
        else:
            x = x.view(B, H, W, C)
            pad_b = (self.window_size - H % self.window_size) % self.window_size
            pad_r = (self.window_size - W % self.window_size) % self.window_size
            padding = pad_b > 0 or pad_r > 0
            if padding:
                x = F.pad(x, (0, 0, 0, pad_r, 0, pad_b))
            pH, pW = (H + pad_b, W + pad_r)
            nH = pH // self.window_size
            nW = pW // self.window_size
            x = x.view(B, nH, self.window_size, nW, self.window_size, C).transpose(2, 3).reshape(B * nH * nW, self.window_size * self.window_size, C)
            x = self.attn(x)
            x = x.view(B, nH, nW, self.window_size, self.window_size, C).transpose(2, 3).reshape(B, pH, pW, C)
            if padding:
                x = x[:, :H, :W].contiguous()
            x = x.view(B, L, C)
        x = res_x + self.drop_path(x)
        x = x.transpose(1, 2).reshape(B, C, H, W)
        x = self.local_conv(x)
        x = x.view(B, C, L).transpose(1, 2)
        x = x + self.drop_path(self.mlp(x))
        return x

    def extra_repr(self) -> str:
        return f'dim={self.dim}, input_resolution={self.input_resolution}, num_heads={self.num_heads}, window_size={self.window_size}, mlp_ratio={self.mlp_ratio}'

def forward(self, x):
    H, W = self.input_resolution
    B, L, C = x.shape
    assert L == H * W, 'input feature has wrong size'
    res_x = x
    if H == self.window_size and W == self.window_size:
        x = self.attn(x)
    else:
        x = x.view(B, H, W, C)
        pad_b = (self.window_size - H % self.window_size) % self.window_size
        pad_r = (self.window_size - W % self.window_size) % self.window_size
        padding = pad_b > 0 or pad_r > 0
        if padding:
            x = F.pad(x, (0, 0, 0, pad_r, 0, pad_b))
        pH, pW = (H + pad_b, W + pad_r)
        nH = pH // self.window_size
        nW = pW // self.window_size
        x = x.view(B, nH, self.window_size, nW, self.window_size, C).transpose(2, 3).reshape(B * nH * nW, self.window_size * self.window_size, C)
        x = self.attn(x)
        x = x.view(B, nH, nW, self.window_size, self.window_size, C).transpose(2, 3).reshape(B, pH, pW, C)
        if padding:
            x = x[:, :H, :W].contiguous()
        x = x.view(B, L, C)
    x = res_x + self.drop_path(x)
    x = x.transpose(1, 2).reshape(B, C, H, W)
    x = self.local_conv(x)
    x = x.view(B, C, L).transpose(1, 2)
    x = x + self.drop_path(self.mlp(x))
    return x

class BasicLayer(nn.Module):
    """ A basic TinyViT layer for one stage.

    Args:
        dim (int): Number of input channels.
        input_resolution (tuple[int]): Input resolution.
        depth (int): Number of blocks.
        num_heads (int): Number of attention heads.
        window_size (int): Local window size.
        mlp_ratio (float): Ratio of mlp hidden dim to embedding dim.
        drop (float, optional): Dropout rate. Default: 0.0
        drop_path (float | tuple[float], optional): Stochastic depth rate. Default: 0.0
        downsample (nn.Module | None, optional): Downsample layer at the end of the layer. Default: None
        use_checkpoint (bool): Whether to use checkpointing to save memory. Default: False.
        local_conv_size: the kernel size of the depthwise convolution between attention and MLP. Default: 3
        activation: the activation function. Default: nn.GELU
        out_dim: the output dimension of the layer. Default: dim
    """

    def __init__(self, dim, input_resolution, depth, num_heads, window_size, mlp_ratio=4.0, drop=0.0, drop_path=0.0, downsample=None, use_checkpoint=False, local_conv_size=3, activation=nn.GELU, out_dim=None):
        super().__init__()
        self.dim = dim
        self.input_resolution = input_resolution
        self.depth = depth
        self.use_checkpoint = use_checkpoint
        self.blocks = nn.ModuleList([TinyViTBlock(dim=dim, input_resolution=input_resolution, num_heads=num_heads, window_size=window_size, mlp_ratio=mlp_ratio, drop=drop, drop_path=drop_path[i] if isinstance(drop_path, list) else drop_path, local_conv_size=local_conv_size, activation=activation) for i in range(depth)])
        if downsample is not None:
            self.downsample = downsample(input_resolution, dim=dim, out_dim=out_dim, activation=activation)
        else:
            self.downsample = None

    def forward(self, x):
        for blk in self.blocks:
            if self.use_checkpoint:
                x = checkpoint.checkpoint(blk, x)
            else:
                x = blk(x)
        if self.downsample is not None:
            x = self.downsample(x)
        return x

    def extra_repr(self) -> str:
        return f'dim={self.dim}, input_resolution={self.input_resolution}, depth={self.depth}'

def forward(self, x):
    for blk in self.blocks:
        if self.use_checkpoint:
            x = checkpoint.checkpoint(blk, x)
        else:
            x = blk(x)
    if self.downsample is not None:
        x = self.downsample(x)
    return x

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

class SamOnnxModel(nn.Module):
    """
    This model should not be called directly, but is used in ONNX export.
    It combines the prompt encoder, mask decoder, and mask postprocessing of Sam,
    with some functions modified to enable model tracing. Also supports extra
    options controlling what information. See the ONNX export script for details.
    """

    def __init__(self, model: Sam, return_single_mask: bool, use_stability_score: bool=False, return_extra_metrics: bool=False) -> None:
        super().__init__()
        self.mask_decoder = model.mask_decoder
        self.model = model
        self.img_size = model.image_encoder.img_size
        self.return_single_mask = return_single_mask
        self.use_stability_score = use_stability_score
        self.stability_score_offset = 1.0
        self.return_extra_metrics = return_extra_metrics

    @staticmethod
    def resize_longest_image_size(input_image_size: torch.Tensor, longest_side: int) -> torch.Tensor:
        input_image_size = input_image_size.to(torch.float32)
        scale = longest_side / torch.max(input_image_size)
        transformed_size = scale * input_image_size
        transformed_size = torch.floor(transformed_size + 0.5).to(torch.int64)
        return transformed_size

    def _embed_points(self, point_coords: torch.Tensor, point_labels: torch.Tensor) -> torch.Tensor:
        point_coords = point_coords + 0.5
        point_coords = point_coords / self.img_size
        point_embedding = self.model.prompt_encoder.pe_layer._pe_encoding(point_coords)
        point_labels = point_labels.unsqueeze(-1).expand_as(point_embedding)
        point_embedding = point_embedding * (point_labels != -1)
        point_embedding = point_embedding + self.model.prompt_encoder.not_a_point_embed.weight * (point_labels == -1)
        for i in range(self.model.prompt_encoder.num_point_embeddings):
            point_embedding = point_embedding + self.model.prompt_encoder.point_embeddings[i].weight * (point_labels == i)
        return point_embedding

    def _embed_masks(self, input_mask: torch.Tensor, has_mask_input: torch.Tensor) -> torch.Tensor:
        mask_embedding = has_mask_input * self.model.prompt_encoder.mask_downscaling(input_mask)
        mask_embedding = mask_embedding + (1 - has_mask_input) * self.model.prompt_encoder.no_mask_embed.weight.reshape(1, -1, 1, 1)
        return mask_embedding

    def mask_postprocessing(self, masks: torch.Tensor, orig_im_size: torch.Tensor) -> torch.Tensor:
        masks = F.interpolate(masks, size=(self.img_size, self.img_size), mode='bilinear', align_corners=False)
        prepadded_size = self.resize_longest_image_size(orig_im_size, self.img_size).to(torch.int64)
        masks = masks[..., :prepadded_size[0], :prepadded_size[1]]
        orig_im_size = orig_im_size.to(torch.int64)
        h, w = (orig_im_size[0], orig_im_size[1])
        masks = F.interpolate(masks, size=(h, w), mode='bilinear', align_corners=False)
        return masks

    def select_masks(self, masks: torch.Tensor, iou_preds: torch.Tensor, num_points: int) -> Tuple[torch.Tensor, torch.Tensor]:
        score_reweight = torch.tensor([[1000] + [0] * (self.model.mask_decoder.num_mask_tokens - 1)]).to(iou_preds.device)
        score = iou_preds + (num_points - 2.5) * score_reweight
        best_idx = torch.argmax(score, dim=1)
        masks = masks[torch.arange(masks.shape[0]), best_idx, :, :].unsqueeze(1)
        iou_preds = iou_preds[torch.arange(masks.shape[0]), best_idx].unsqueeze(1)
        return (masks, iou_preds)

    @torch.no_grad()
    def forward(self, image_embeddings: torch.Tensor, point_coords: torch.Tensor, point_labels: torch.Tensor, mask_input: torch.Tensor, has_mask_input: torch.Tensor, orig_im_size: torch.Tensor):
        sparse_embedding = self._embed_points(point_coords, point_labels)
        dense_embedding = self._embed_masks(mask_input, has_mask_input)
        masks, scores = self.model.mask_decoder.predict_masks(image_embeddings=image_embeddings, image_pe=self.model.prompt_encoder.get_dense_pe(), sparse_prompt_embeddings=sparse_embedding, dense_prompt_embeddings=dense_embedding)
        if self.use_stability_score:
            scores = calculate_stability_score(masks, self.model.mask_threshold, self.stability_score_offset)
        if self.return_single_mask:
            masks, scores = self.select_masks(masks, scores, point_coords.shape[1])
        upscaled_masks = self.mask_postprocessing(masks, orig_im_size)
        if self.return_extra_metrics:
            stability_scores = calculate_stability_score(upscaled_masks, self.model.mask_threshold, self.stability_score_offset)
            areas = (upscaled_masks > self.model.mask_threshold).sum(-1).sum(-1)
            return (upscaled_masks, scores, stability_scores, areas, masks)
        return (upscaled_masks, scores, masks)

@staticmethod
def resize_longest_image_size(input_image_size: torch.Tensor, longest_side: int) -> torch.Tensor:
    input_image_size = input_image_size.to(torch.float32)
    scale = longest_side / torch.max(input_image_size)
    transformed_size = scale * input_image_size
    transformed_size = torch.floor(transformed_size + 0.5).to(torch.int64)
    return transformed_size

def _embed_points(self, point_coords: torch.Tensor, point_labels: torch.Tensor) -> torch.Tensor:
    point_coords = point_coords + 0.5
    point_coords = point_coords / self.img_size
    point_embedding = self.model.prompt_encoder.pe_layer._pe_encoding(point_coords)
    point_labels = point_labels.unsqueeze(-1).expand_as(point_embedding)
    point_embedding = point_embedding * (point_labels != -1)
    point_embedding = point_embedding + self.model.prompt_encoder.not_a_point_embed.weight * (point_labels == -1)
    for i in range(self.model.prompt_encoder.num_point_embeddings):
        point_embedding = point_embedding + self.model.prompt_encoder.point_embeddings[i].weight * (point_labels == i)
    return point_embedding

def mask_postprocessing(self, masks: torch.Tensor, orig_im_size: torch.Tensor) -> torch.Tensor:
    masks = F.interpolate(masks, size=(self.img_size, self.img_size), mode='bilinear', align_corners=False)
    prepadded_size = self.resize_longest_image_size(orig_im_size, self.img_size).to(torch.int64)
    masks = masks[..., :prepadded_size[0], :prepadded_size[1]]
    orig_im_size = orig_im_size.to(torch.int64)
    h, w = (orig_im_size[0], orig_im_size[1])
    masks = F.interpolate(masks, size=(h, w), mode='bilinear', align_corners=False)
    return masks

class ResizeLongestSide:
    """
    Resizes images to longest side 'target_length', as well as provides
    methods for resizing coordinates and boxes. Provides methods for
    transforming both numpy array and batched torch tensors.
    """

    def __init__(self, target_length: int) -> None:
        self.target_length = target_length

    def apply_image(self, image: np.ndarray) -> np.ndarray:
        """
        Expects a numpy array with shape HxWxC in uint8 format.
        """
        target_size = self.get_preprocess_shape(image.shape[0], image.shape[1], self.target_length)
        return np.array(resize(to_pil_image(image), target_size))

    def apply_coords(self, coords: np.ndarray, original_size: Tuple[int, ...]) -> np.ndarray:
        """
        Expects a numpy array of length 2 in the final dimension. Requires the
        original image size in (H, W) format.
        """
        old_h, old_w = original_size
        new_h, new_w = self.get_preprocess_shape(original_size[0], original_size[1], self.target_length)
        coords = deepcopy(coords).astype(float)
        coords[..., 0] = coords[..., 0] * (new_w / old_w)
        coords[..., 1] = coords[..., 1] * (new_h / old_h)
        return coords

    def apply_boxes(self, boxes: np.ndarray, original_size: Tuple[int, ...]) -> np.ndarray:
        """
        Expects a numpy array shape Bx4. Requires the original image size
        in (H, W) format.
        """
        boxes = self.apply_coords(boxes.reshape(-1, 2, 2), original_size)
        return boxes.reshape(-1, 4)

    def apply_image_torch(self, image: torch.Tensor) -> torch.Tensor:
        """
        Expects batched images with shape BxCxHxW and float format. This
        transformation may not exactly match apply_image. apply_image is
        the transformation expected by the model.
        """
        target_size = self.get_preprocess_shape(image.shape[0], image.shape[1], self.target_length)
        return F.interpolate(image, target_size, mode='bilinear', align_corners=False, antialias=True)

    def apply_coords_torch(self, coords: torch.Tensor, original_size: Tuple[int, ...]) -> torch.Tensor:
        """
        Expects a torch tensor with length 2 in the last dimension. Requires the
        original image size in (H, W) format.
        """
        old_h, old_w = original_size
        new_h, new_w = self.get_preprocess_shape(original_size[0], original_size[1], self.target_length)
        coords = deepcopy(coords).to(torch.float)
        coords[..., 0] = coords[..., 0] * (new_w / old_w)
        coords[..., 1] = coords[..., 1] * (new_h / old_h)
        return coords

    def apply_boxes_torch(self, boxes: torch.Tensor, original_size: Tuple[int, ...]) -> torch.Tensor:
        """
        Expects a torch tensor with shape Bx4. Requires the original image
        size in (H, W) format.
        """
        boxes = self.apply_coords_torch(boxes.reshape(-1, 2, 2), original_size)
        return boxes.reshape(-1, 4)

    @staticmethod
    def get_preprocess_shape(oldh: int, oldw: int, long_side_length: int) -> Tuple[int, int]:
        """
        Compute the output size given input size and target long side length.
        """
        scale = long_side_length * 1.0 / max(oldh, oldw)
        newh, neww = (oldh * scale, oldw * scale)
        neww = int(neww + 0.5)
        newh = int(newh + 0.5)
        return (newh, neww)

@staticmethod
def get_preprocess_shape(oldh: int, oldw: int, long_side_length: int) -> Tuple[int, int]:
    """
        Compute the output size given input size and target long side length.
        """
    scale = long_side_length * 1.0 / max(oldh, oldw)
    newh, neww = (oldh * scale, oldw * scale)
    neww = int(neww + 0.5)
    newh = int(newh + 0.5)
    return (newh, neww)

def uncrop_boxes_xyxy(boxes: torch.Tensor, crop_box: List[int]) -> torch.Tensor:
    x0, y0, _, _ = crop_box
    offset = torch.tensor([[x0, y0, x0, y0]], device=boxes.device)
    if len(boxes.shape) == 3:
        offset = offset.unsqueeze(1)
    return boxes + offset

def uncrop_points(points: torch.Tensor, crop_box: List[int]) -> torch.Tensor:
    x0, y0, _, _ = crop_box
    offset = torch.tensor([[x0, y0]], device=points.device)
    if len(points.shape) == 3:
        offset = offset.unsqueeze(1)
    return points + offset

def uncrop_masks(masks: torch.Tensor, crop_box: List[int], orig_h: int, orig_w: int) -> torch.Tensor:
    x0, y0, x1, y1 = crop_box
    if x0 == 0 and y0 == 0 and (x1 == orig_w) and (y1 == orig_h):
        return masks
    pad_x, pad_y = (orig_w - (x1 - x0), orig_h - (y1 - y0))
    pad = (x0, pad_x - x0, y0, pad_y - y0)
    return torch.nn.functional.pad(masks, pad, value=0)

def batched_mask_to_box(masks: torch.Tensor) -> torch.Tensor:
    """
    Calculates boxes in XYXY format around masks. Return [0,0,0,0] for
    an empty mask. For input shape C1xC2x...xHxW, the output shape is C1xC2x...x4.
    """
    if torch.numel(masks) == 0:
        return torch.zeros(*masks.shape[:-2], 4, device=masks.device)
    shape = masks.shape
    h, w = shape[-2:]
    if len(shape) > 2:
        masks = masks.flatten(0, -3)
    else:
        masks = masks.unsqueeze(0)
    in_height, _ = torch.max(masks, dim=-1)
    in_height_coords = in_height * torch.arange(h, device=in_height.device)[None, :]
    bottom_edges, _ = torch.max(in_height_coords, dim=-1)
    in_height_coords = in_height_coords + h * ~in_height
    top_edges, _ = torch.min(in_height_coords, dim=-1)
    in_width, _ = torch.max(masks, dim=-2)
    in_width_coords = in_width * torch.arange(w, device=in_width.device)[None, :]
    right_edges, _ = torch.max(in_width_coords, dim=-1)
    in_width_coords = in_width_coords + w * ~in_width
    left_edges, _ = torch.min(in_width_coords, dim=-1)
    empty_filter = (right_edges < left_edges) | (bottom_edges < top_edges)
    out = torch.stack([left_edges, top_edges, right_edges, bottom_edges], dim=-1)
    out = out * (~empty_filter).unsqueeze(-1)
    if len(shape) > 2:
        out = out.reshape(*shape[:-2], 4)
    else:
        out = out[0]
    return out

def paste_object(source, source_mask, target, target_coords, resize_scale=1):
    assert target_coords[0] < target.shape[1] and target_coords[1] < target.shape[0]
    x, y, w, h = cv2.boundingRect(source_mask)
    assert h < source.shape[0] and w < source.shape[1]
    obj = source[y:y + h, x:x + w]
    obj_msk = source_mask[y:y + h, x:x + w]
    if resize_scale != 1:
        obj = cv2.resize(obj, (0, 0), fx=resize_scale, fy=resize_scale)
        obj_msk = cv2.resize(obj_msk, (0, 0), fx=resize_scale, fy=resize_scale)
        _, _, w, h = cv2.boundingRect(obj_msk)
    xt = max(0, target_coords[0] - w // 2)
    yt = max(0, target_coords[1] - h // 2)
    if target_coords[0] - w // 2 < 0:
        obj = obj[:, w // 2 - target_coords[0]:]
        obj_msk = obj_msk[:, w // 2 - target_coords[0]:]
    if target_coords[0] + w // 2 > target.shape[1]:
        obj = obj[:, :target.shape[1] - target_coords[0] + w // 2]
        obj_msk = obj_msk[:, :target.shape[1] - target_coords[0] + w // 2]
    if target_coords[1] - h // 2 < 0:
        obj = obj[h // 2 - target_coords[1]:, :]
        obj_msk = obj_msk[h // 2 - target_coords[1]:, :]
    if target_coords[1] + h // 2 > target.shape[0]:
        obj = obj[:target.shape[0] - target_coords[1] + h // 2, :]
        obj_msk = obj_msk[:target.shape[0] - target_coords[1] + h // 2, :]
    _, _, w, h = cv2.boundingRect(obj_msk)
    target[yt:yt + h, xt:xt + w][obj_msk == 255] = obj[obj_msk == 255]
    target_mask = np.zeros_like(target)
    target_mask = cv2.cvtColor(target_mask, cv2.COLOR_BGR2GRAY)
    target_mask[yt:yt + h, xt:xt + w][obj_msk == 255] = 255
    return (target, target_mask)

def crop_for_filling_pre(image: np.array, mask: np.array, crop_size: int=512):
    height, width = image.shape[:2]
    aspect_ratio = float(width) / float(height)
    if min(height, width) < crop_size:
        if height < width:
            new_height = crop_size
            new_width = int(new_height * aspect_ratio)
        else:
            new_width = crop_size
            new_height = int(new_width / aspect_ratio)
        image = cv2.resize(image, (new_width, new_height))
        mask = cv2.resize(mask, (new_width, new_height))
    x, y, w, h = cv2.boundingRect(mask)
    height, width = image.shape[:2]
    if w > crop_size or h > crop_size:
        if height < width:
            padding = width - height
            image = np.pad(image, ((padding // 2, padding - padding // 2), (0, 0), (0, 0)), 'constant')
            mask = np.pad(mask, ((padding // 2, padding - padding // 2), (0, 0)), 'constant')
        else:
            padding = height - width
            image = np.pad(image, ((0, 0), (padding // 2, padding - padding // 2), (0, 0)), 'constant')
            mask = np.pad(mask, ((0, 0), (padding // 2, padding - padding // 2)), 'constant')
        resize_factor = crop_size / max(w, h)
        image = cv2.resize(image, (0, 0), fx=resize_factor, fy=resize_factor)
        mask = cv2.resize(mask, (0, 0), fx=resize_factor, fy=resize_factor)
        x, y, w, h = cv2.boundingRect(mask)
    crop_x = min(max(x + w // 2 - crop_size // 2, 0), width - crop_size)
    crop_y = min(max(y + h // 2 - crop_size // 2, 0), height - crop_size)
    cropped_image = image[crop_y:crop_y + crop_size, crop_x:crop_x + crop_size]
    cropped_mask = mask[crop_y:crop_y + crop_size, crop_x:crop_x + crop_size]
    return (cropped_image, cropped_mask)

def crop_for_filling_post(image: np.array, mask: np.array, filled_image: np.array, crop_size: int=512):
    image_copy = image.copy()
    mask_copy = mask.copy()
    height, width = image.shape[:2]
    height_ori, width_ori = (height, width)
    aspect_ratio = float(width) / float(height)
    if min(height, width) < crop_size:
        if height < width:
            new_height = crop_size
            new_width = int(new_height * aspect_ratio)
        else:
            new_width = crop_size
            new_height = int(new_width / aspect_ratio)
        image = cv2.resize(image, (new_width, new_height))
        mask = cv2.resize(mask, (new_width, new_height))
    x, y, w, h = cv2.boundingRect(mask)
    height, width = image.shape[:2]
    if w > crop_size or h > crop_size:
        flag_padding = True
        if height < width:
            padding = width - height
            image = np.pad(image, ((padding // 2, padding - padding // 2), (0, 0), (0, 0)), 'constant')
            mask = np.pad(mask, ((padding // 2, padding - padding // 2), (0, 0)), 'constant')
            padding_side = 'h'
        else:
            padding = height - width
            image = np.pad(image, ((0, 0), (padding // 2, padding - padding // 2), (0, 0)), 'constant')
            mask = np.pad(mask, ((0, 0), (padding // 2, padding - padding // 2)), 'constant')
            padding_side = 'w'
        resize_factor = crop_size / max(w, h)
        image = cv2.resize(image, (0, 0), fx=resize_factor, fy=resize_factor)
        mask = cv2.resize(mask, (0, 0), fx=resize_factor, fy=resize_factor)
        x, y, w, h = cv2.boundingRect(mask)
    else:
        flag_padding = False
    crop_x = min(max(x + w // 2 - crop_size // 2, 0), width - crop_size)
    crop_y = min(max(y + h // 2 - crop_size // 2, 0), height - crop_size)
    image[crop_y:crop_y + crop_size, crop_x:crop_x + crop_size] = filled_image
    if flag_padding:
        image = cv2.resize(image, (0, 0), fx=1 / resize_factor, fy=1 / resize_factor)
        if padding_side == 'h':
            image = image[padding // 2:padding // 2 + height_ori, :]
        else:
            image = image[:, padding // 2:padding // 2 + width_ori]
    image = cv2.resize(image, (width_ori, height_ori))
    image_copy[mask_copy == 255] = image[mask_copy == 255]
    return image_copy

def ssim_fid100_f1(metrics, fid_scale=100):
    ssim = metrics.loc['total', 'ssim']['mean']
    fid = metrics.loc['total', 'fid']['mean']
    fid_rel = max(0, fid_scale - fid) / fid_scale
    f1 = 2 * ssim * fid_rel / (ssim + fid_rel + 0.001)
    return f1

def check_and_warn_input_range(tensor, min_value, max_value, name):
    actual_min = tensor.min()
    actual_max = tensor.max()
    if actual_min < min_value or actual_max > max_value:
        warnings.warn(f'{name} must be in {min_value}..{max_value} range, but it ranges {actual_min}..{actual_max}')

class BaseAdversarialLoss:

    def pre_generator_step(self, real_batch: torch.Tensor, fake_batch: torch.Tensor, generator: nn.Module, discriminator: nn.Module):
        """
        Prepare for generator step
        :param real_batch: Tensor, a batch of real samples
        :param fake_batch: Tensor, a batch of samples produced by generator
        :param generator:
        :param discriminator:
        :return: None
        """

    def pre_discriminator_step(self, real_batch: torch.Tensor, fake_batch: torch.Tensor, generator: nn.Module, discriminator: nn.Module):
        """
        Prepare for discriminator step
        :param real_batch: Tensor, a batch of real samples
        :param fake_batch: Tensor, a batch of samples produced by generator
        :param generator:
        :param discriminator:
        :return: None
        """

    def generator_loss(self, real_batch: torch.Tensor, fake_batch: torch.Tensor, discr_real_pred: torch.Tensor, discr_fake_pred: torch.Tensor, mask: Optional[torch.Tensor]=None) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        """
        Calculate generator loss
        :param real_batch: Tensor, a batch of real samples
        :param fake_batch: Tensor, a batch of samples produced by generator
        :param discr_real_pred: Tensor, discriminator output for real_batch
        :param discr_fake_pred: Tensor, discriminator output for fake_batch
        :param mask: Tensor, actual mask, which was at input of generator when making fake_batch
        :return: total generator loss along with some values that might be interesting to log
        """
        raise NotImplemented()

    def discriminator_loss(self, real_batch: torch.Tensor, fake_batch: torch.Tensor, discr_real_pred: torch.Tensor, discr_fake_pred: torch.Tensor, mask: Optional[torch.Tensor]=None) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        """
        Calculate discriminator loss and call .backward() on it
        :param real_batch: Tensor, a batch of real samples
        :param fake_batch: Tensor, a batch of samples produced by generator
        :param discr_real_pred: Tensor, discriminator output for real_batch
        :param discr_fake_pred: Tensor, discriminator output for fake_batch
        :param mask: Tensor, actual mask, which was at input of generator when making fake_batch
        :return: total discriminator loss along with some values that might be interesting to log
        """
        raise NotImplemented()

    def interpolate_mask(self, mask, shape):
        assert mask is not None
        assert self.allow_scale_mask or shape == mask.shape[-2:]
        if shape != mask.shape[-2:] and self.allow_scale_mask:
            if self.mask_scale_mode == 'maxpool':
                mask = F.adaptive_max_pool2d(mask, shape)
            else:
                mask = F.interpolate(mask, size=shape, mode=self.mask_scale_mode)
        return mask

def interpolate_mask(self, mask, shape):
    assert mask is not None
    assert self.allow_scale_mask or shape == mask.shape[-2:]
    if shape != mask.shape[-2:] and self.allow_scale_mask:
        if self.mask_scale_mode == 'maxpool':
            mask = F.adaptive_max_pool2d(mask, shape)
        else:
            mask = F.interpolate(mask, size=shape, mode=self.mask_scale_mode)
    return mask

def make_r1_gp(discr_real_pred, real_batch):
    if torch.is_grad_enabled():
        grad_real = torch.autograd.grad(outputs=discr_real_pred.sum(), inputs=real_batch, create_graph=True)[0]
        grad_penalty = (grad_real.view(grad_real.shape[0], -1).norm(2, dim=1) ** 2).mean()
    else:
        grad_penalty = 0
    real_batch.requires_grad = False
    return grad_penalty

class CrossEntropy2d(nn.Module):

    def __init__(self, reduction='mean', ignore_label=255, weights=None, *args, **kwargs):
        """
        weight (Tensor, optional): a manual rescaling weight given to each class.
            If given, has to be a Tensor of size "nclasses"
        """
        super(CrossEntropy2d, self).__init__()
        self.reduction = reduction
        self.ignore_label = ignore_label
        self.weights = weights
        if self.weights is not None:
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            self.weights = torch.FloatTensor(constant_weights[weights]).to(device)

    def forward(self, predict, target):
        """
            Args:
                predict:(n, c, h, w)
                target:(n, 1, h, w)
        """
        target = target.long()
        assert not target.requires_grad
        assert predict.dim() == 4, '{0}'.format(predict.size())
        assert target.dim() == 4, '{0}'.format(target.size())
        assert predict.size(0) == target.size(0), '{0} vs {1} '.format(predict.size(0), target.size(0))
        assert target.size(1) == 1, '{0}'.format(target.size(1))
        assert predict.size(2) == target.size(2), '{0} vs {1} '.format(predict.size(2), target.size(2))
        assert predict.size(3) == target.size(3), '{0} vs {1} '.format(predict.size(3), target.size(3))
        target = target.squeeze(1)
        n, c, h, w = predict.size()
        target_mask = (target >= 0) * (target != self.ignore_label)
        target = target[target_mask]
        predict = predict.transpose(1, 2).transpose(2, 3).contiguous()
        predict = predict[target_mask.view(n, h, w, 1).repeat(1, 1, 1, c)].view(-1, c)
        loss = F.cross_entropy(predict, target, weight=self.weights, reduction=self.reduction)
        return loss

def forward(self, predict, target):
    """
            Args:
                predict:(n, c, h, w)
                target:(n, 1, h, w)
        """
    target = target.long()
    assert not target.requires_grad
    assert predict.dim() == 4, '{0}'.format(predict.size())
    assert target.dim() == 4, '{0}'.format(target.size())
    assert predict.size(0) == target.size(0), '{0} vs {1} '.format(predict.size(0), target.size(0))
    assert target.size(1) == 1, '{0}'.format(target.size(1))
    assert predict.size(2) == target.size(2), '{0} vs {1} '.format(predict.size(2), target.size(2))
    assert predict.size(3) == target.size(3), '{0} vs {1} '.format(predict.size(3), target.size(3))
    target = target.squeeze(1)
    n, c, h, w = predict.size()
    target_mask = (target >= 0) * (target != self.ignore_label)
    target = target[target_mask]
    predict = predict.transpose(1, 2).transpose(2, 3).contiguous()
    predict = predict[target_mask.view(n, h, w, 1).repeat(1, 1, 1, c)].view(-1, c)
    loss = F.cross_entropy(predict, target, weight=self.weights, reduction=self.reduction)
    return loss

def get_gauss_kernel(kernel_size, width_factor=1):
    coords = torch.stack(torch.meshgrid(torch.arange(kernel_size), torch.arange(kernel_size)), dim=0).float()
    diff = torch.exp(-((coords - kernel_size // 2) ** 2).sum(0) / kernel_size / width_factor)
    diff /= diff.sum()
    return diff

def make_multiscale_noise(base_tensor, scales=6, scale_mode='bilinear'):
    batch_size, _, height, width = base_tensor.shape
    cur_height, cur_width = (height, width)
    result = []
    align_corners = False if scale_mode in ('bilinear', 'bicubic') else None
    for _ in range(scales):
        cur_sample = torch.randn(batch_size, 1, cur_height, cur_width, device=base_tensor.device)
        cur_sample_scaled = F.interpolate(cur_sample, size=(height, width), mode=scale_mode, align_corners=align_corners)
        result.append(cur_sample_scaled)
        cur_height //= 2
        cur_width //= 2
    return torch.cat(result, dim=1)

class DefaultInpaintingTrainingModule(BaseInpaintingTrainingModule):

    def __init__(self, *args, concat_mask=True, rescale_scheduler_kwargs=None, image_to_discriminator='predicted_image', add_noise_kwargs=None, noise_fill_hole=False, const_area_crop_kwargs=None, distance_weighter_kwargs=None, distance_weighted_mask_for_discr=False, fake_fakes_proba=0, fake_fakes_generator_kwargs=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.concat_mask = concat_mask
        self.rescale_size_getter = get_ramp(**rescale_scheduler_kwargs) if rescale_scheduler_kwargs is not None else None
        self.image_to_discriminator = image_to_discriminator
        self.add_noise_kwargs = add_noise_kwargs
        self.noise_fill_hole = noise_fill_hole
        self.const_area_crop_kwargs = const_area_crop_kwargs
        self.refine_mask_for_losses = make_mask_distance_weighter(**distance_weighter_kwargs) if distance_weighter_kwargs is not None else None
        self.distance_weighted_mask_for_discr = distance_weighted_mask_for_discr
        self.fake_fakes_proba = fake_fakes_proba
        if self.fake_fakes_proba > 0.001:
            self.fake_fakes_gen = FakeFakesGenerator(**fake_fakes_generator_kwargs or {})

    def forward(self, batch):
        if self.training and self.rescale_size_getter is not None:
            cur_size = self.rescale_size_getter(self.global_step)
            batch['image'] = F.interpolate(batch['image'], size=cur_size, mode='bilinear', align_corners=False)
            batch['mask'] = F.interpolate(batch['mask'], size=cur_size, mode='nearest')
        if self.training and self.const_area_crop_kwargs is not None:
            batch = make_constant_area_crop_batch(batch, **self.const_area_crop_kwargs)
        img = batch['image']
        mask = batch['mask']
        masked_img = img * (1 - mask)
        if self.add_noise_kwargs is not None:
            noise = make_multiscale_noise(masked_img, **self.add_noise_kwargs)
            if self.noise_fill_hole:
                masked_img = masked_img + mask * noise[:, :masked_img.shape[1]]
            masked_img = torch.cat([masked_img, noise], dim=1)
        if self.concat_mask:
            masked_img = torch.cat([masked_img, mask], dim=1)
        batch['predicted_image'] = self.generator(masked_img)
        batch['inpainted'] = mask * batch['predicted_image'] + (1 - mask) * batch['image']
        if self.fake_fakes_proba > 0.001:
            if self.training and torch.rand(1).item() < self.fake_fakes_proba:
                batch['fake_fakes'], batch['fake_fakes_masks'] = self.fake_fakes_gen(img, mask)
                batch['use_fake_fakes'] = True
            else:
                batch['fake_fakes'] = torch.zeros_like(img)
                batch['fake_fakes_masks'] = torch.zeros_like(mask)
                batch['use_fake_fakes'] = False
        batch['mask_for_losses'] = self.refine_mask_for_losses(img, batch['predicted_image'], mask) if self.refine_mask_for_losses is not None and self.training else mask
        return batch

    def generator_loss(self, batch):
        img = batch['image']
        predicted_img = batch[self.image_to_discriminator]
        original_mask = batch['mask']
        supervised_mask = batch['mask_for_losses']
        l1_value = masked_l1_loss(predicted_img, img, supervised_mask, self.config.losses.l1.weight_known, self.config.losses.l1.weight_missing)
        total_loss = l1_value
        metrics = dict(gen_l1=l1_value)
        if self.config.losses.perceptual.weight > 0:
            pl_value = self.loss_pl(predicted_img, img, mask=supervised_mask).sum() * self.config.losses.perceptual.weight
            total_loss = total_loss + pl_value
            metrics['gen_pl'] = pl_value
        mask_for_discr = supervised_mask if self.distance_weighted_mask_for_discr else original_mask
        self.adversarial_loss.pre_generator_step(real_batch=img, fake_batch=predicted_img, generator=self.generator, discriminator=self.discriminator)
        discr_real_pred, discr_real_features = self.discriminator(img)
        discr_fake_pred, discr_fake_features = self.discriminator(predicted_img)
        adv_gen_loss, adv_metrics = self.adversarial_loss.generator_loss(real_batch=img, fake_batch=predicted_img, discr_real_pred=discr_real_pred, discr_fake_pred=discr_fake_pred, mask=mask_for_discr)
        total_loss = total_loss + adv_gen_loss
        metrics['gen_adv'] = adv_gen_loss
        metrics.update(add_prefix_to_keys(adv_metrics, 'adv_'))
        if self.config.losses.feature_matching.weight > 0:
            need_mask_in_fm = OmegaConf.to_container(self.config.losses.feature_matching).get('pass_mask', False)
            mask_for_fm = supervised_mask if need_mask_in_fm else None
            fm_value = feature_matching_loss(discr_fake_features, discr_real_features, mask=mask_for_fm) * self.config.losses.feature_matching.weight
            total_loss = total_loss + fm_value
            metrics['gen_fm'] = fm_value
        if self.loss_resnet_pl is not None:
            resnet_pl_value = self.loss_resnet_pl(predicted_img, img)
            total_loss = total_loss + resnet_pl_value
            metrics['gen_resnet_pl'] = resnet_pl_value
        return (total_loss, metrics)

    def discriminator_loss(self, batch):
        total_loss = 0
        metrics = {}
        predicted_img = batch[self.image_to_discriminator].detach()
        self.adversarial_loss.pre_discriminator_step(real_batch=batch['image'], fake_batch=predicted_img, generator=self.generator, discriminator=self.discriminator)
        discr_real_pred, discr_real_features = self.discriminator(batch['image'])
        discr_fake_pred, discr_fake_features = self.discriminator(predicted_img)
        adv_discr_loss, adv_metrics = self.adversarial_loss.discriminator_loss(real_batch=batch['image'], fake_batch=predicted_img, discr_real_pred=discr_real_pred, discr_fake_pred=discr_fake_pred, mask=batch['mask'])
        total_loss = total_loss + adv_discr_loss
        metrics['discr_adv'] = adv_discr_loss
        metrics.update(add_prefix_to_keys(adv_metrics, 'adv_'))
        if batch.get('use_fake_fakes', False):
            fake_fakes = batch['fake_fakes']
            self.adversarial_loss.pre_discriminator_step(real_batch=batch['image'], fake_batch=fake_fakes, generator=self.generator, discriminator=self.discriminator)
            discr_fake_fakes_pred, _ = self.discriminator(fake_fakes)
            fake_fakes_adv_discr_loss, fake_fakes_adv_metrics = self.adversarial_loss.discriminator_loss(real_batch=batch['image'], fake_batch=fake_fakes, discr_real_pred=discr_real_pred, discr_fake_pred=discr_fake_fakes_pred, mask=batch['mask'])
            total_loss = total_loss + fake_fakes_adv_discr_loss
            metrics['discr_adv_fake_fakes'] = fake_fakes_adv_discr_loss
            metrics.update(add_prefix_to_keys(fake_fakes_adv_metrics, 'adv_'))
        return (total_loss, metrics)

def forward(self, batch):
    if self.training and self.rescale_size_getter is not None:
        cur_size = self.rescale_size_getter(self.global_step)
        batch['image'] = F.interpolate(batch['image'], size=cur_size, mode='bilinear', align_corners=False)
        batch['mask'] = F.interpolate(batch['mask'], size=cur_size, mode='nearest')
    if self.training and self.const_area_crop_kwargs is not None:
        batch = make_constant_area_crop_batch(batch, **self.const_area_crop_kwargs)
    img = batch['image']
    mask = batch['mask']
    masked_img = img * (1 - mask)
    if self.add_noise_kwargs is not None:
        noise = make_multiscale_noise(masked_img, **self.add_noise_kwargs)
        if self.noise_fill_hole:
            masked_img = masked_img + mask * noise[:, :masked_img.shape[1]]
        masked_img = torch.cat([masked_img, noise], dim=1)
    if self.concat_mask:
        masked_img = torch.cat([masked_img, mask], dim=1)
    batch['predicted_image'] = self.generator(masked_img)
    batch['inpainted'] = mask * batch['predicted_image'] + (1 - mask) * batch['image']
    if self.fake_fakes_proba > 0.001:
        if self.training and torch.rand(1).item() < self.fake_fakes_proba:
            batch['fake_fakes'], batch['fake_fakes_masks'] = self.fake_fakes_gen(img, mask)
            batch['use_fake_fakes'] = True
        else:
            batch['fake_fakes'] = torch.zeros_like(img)
            batch['fake_fakes_masks'] = torch.zeros_like(mask)
            batch['use_fake_fakes'] = False
    batch['mask_for_losses'] = self.refine_mask_for_losses(img, batch['predicted_image'], mask) if self.refine_mask_for_losses is not None and self.training else mask
    return batch

class FourierUnit(nn.Module):

    def __init__(self, in_channels, out_channels, groups=1, spatial_scale_factor=None, spatial_scale_mode='bilinear', spectral_pos_encoding=False, use_se=False, se_kwargs=None, ffc3d=False, fft_norm='ortho'):
        super(FourierUnit, self).__init__()
        self.groups = groups
        self.conv_layer = torch.nn.Conv2d(in_channels=in_channels * 2 + (2 if spectral_pos_encoding else 0), out_channels=out_channels * 2, kernel_size=1, stride=1, padding=0, groups=self.groups, bias=False)
        self.bn = torch.nn.BatchNorm2d(out_channels * 2)
        self.relu = torch.nn.ReLU(inplace=True)
        self.use_se = use_se
        if use_se:
            if se_kwargs is None:
                se_kwargs = {}
            self.se = SELayer(self.conv_layer.in_channels, **se_kwargs)
        self.spatial_scale_factor = spatial_scale_factor
        self.spatial_scale_mode = spatial_scale_mode
        self.spectral_pos_encoding = spectral_pos_encoding
        self.ffc3d = ffc3d
        self.fft_norm = fft_norm

    def forward(self, x):
        batch = x.shape[0]
        if self.spatial_scale_factor is not None:
            orig_size = x.shape[-2:]
            x = F.interpolate(x, scale_factor=self.spatial_scale_factor, mode=self.spatial_scale_mode, align_corners=False)
        r_size = x.size()
        fft_dim = (-3, -2, -1) if self.ffc3d else (-2, -1)
        ffted = torch.fft.rfftn(x, dim=fft_dim, norm=self.fft_norm)
        ffted = torch.stack((ffted.real, ffted.imag), dim=-1)
        ffted = ffted.permute(0, 1, 4, 2, 3).contiguous()
        ffted = ffted.view((batch, -1) + ffted.size()[3:])
        if self.spectral_pos_encoding:
            height, width = ffted.shape[-2:]
            coords_vert = torch.linspace(0, 1, height)[None, None, :, None].expand(batch, 1, height, width).to(ffted)
            coords_hor = torch.linspace(0, 1, width)[None, None, None, :].expand(batch, 1, height, width).to(ffted)
            ffted = torch.cat((coords_vert, coords_hor, ffted), dim=1)
        if self.use_se:
            ffted = self.se(ffted)
        ffted = self.conv_layer(ffted)
        ffted = self.relu(self.bn(ffted))
        ffted = ffted.view((batch, -1, 2) + ffted.size()[2:]).permute(0, 1, 3, 4, 2).contiguous()
        ffted = torch.complex(ffted[..., 0], ffted[..., 1])
        ifft_shape_slice = x.shape[-3:] if self.ffc3d else x.shape[-2:]
        output = torch.fft.irfftn(ffted, s=ifft_shape_slice, dim=fft_dim, norm=self.fft_norm)
        if self.spatial_scale_factor is not None:
            output = F.interpolate(output, size=orig_size, mode=self.spatial_scale_mode, align_corners=False)
        return output

def forward(self, x):
    batch = x.shape[0]
    if self.spatial_scale_factor is not None:
        orig_size = x.shape[-2:]
        x = F.interpolate(x, scale_factor=self.spatial_scale_factor, mode=self.spatial_scale_mode, align_corners=False)
    r_size = x.size()
    fft_dim = (-3, -2, -1) if self.ffc3d else (-2, -1)
    ffted = torch.fft.rfftn(x, dim=fft_dim, norm=self.fft_norm)
    ffted = torch.stack((ffted.real, ffted.imag), dim=-1)
    ffted = ffted.permute(0, 1, 4, 2, 3).contiguous()
    ffted = ffted.view((batch, -1) + ffted.size()[3:])
    if self.spectral_pos_encoding:
        height, width = ffted.shape[-2:]
        coords_vert = torch.linspace(0, 1, height)[None, None, :, None].expand(batch, 1, height, width).to(ffted)
        coords_hor = torch.linspace(0, 1, width)[None, None, None, :].expand(batch, 1, height, width).to(ffted)
        ffted = torch.cat((coords_vert, coords_hor, ffted), dim=1)
    if self.use_se:
        ffted = self.se(ffted)
    ffted = self.conv_layer(ffted)
    ffted = self.relu(self.bn(ffted))
    ffted = ffted.view((batch, -1, 2) + ffted.size()[2:]).permute(0, 1, 3, 4, 2).contiguous()
    ffted = torch.complex(ffted[..., 0], ffted[..., 1])
    ifft_shape_slice = x.shape[-3:] if self.ffc3d else x.shape[-2:]
    output = torch.fft.irfftn(ffted, s=ifft_shape_slice, dim=fft_dim, norm=self.fft_norm)
    if self.spatial_scale_factor is not None:
        output = F.interpolate(output, size=orig_size, mode=self.spatial_scale_mode, align_corners=False)
    return output

class SELayer(nn.Module):

    def __init__(self, channel, reduction=16):
        super(SELayer, self).__init__()
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Sequential(nn.Linear(channel, channel // reduction, bias=False), nn.ReLU(inplace=True), nn.Linear(channel // reduction, channel, bias=False), nn.Sigmoid())

    def forward(self, x):
        b, c, _, _ = x.size()
        y = self.avg_pool(x).view(b, c)
        y = self.fc(y).view(b, c, 1, 1)
        res = x * y.expand_as(x)
        return res

def forward(self, x):
    b, c, _, _ = x.size()
    y = self.avg_pool(x).view(b, c)
    y = self.fc(y).view(b, c, 1, 1)
    res = x * y.expand_as(x)
    return res

class FakeFakesGenerator:

    def __init__(self, aug_proba=0.5, img_aug_degree=30, img_aug_translate=0.2):
        self.grad_aug = RandomAffine(degrees=360, translate=0.2, padding_mode=SamplePadding.REFLECTION, keepdim=False, p=1)
        self.img_aug = RandomAffine(degrees=img_aug_degree, translate=img_aug_translate, padding_mode=SamplePadding.REFLECTION, keepdim=True, p=1)
        self.aug_proba = aug_proba

    def __call__(self, input_images, masks):
        blend_masks = self._fill_masks_with_gradient(masks)
        blend_target = self._make_blend_target(input_images)
        result = input_images * (1 - blend_masks) + blend_target * blend_masks
        return (result, blend_masks)

    def _make_blend_target(self, input_images):
        batch_size = input_images.shape[0]
        permuted = input_images[torch.randperm(batch_size)]
        augmented = self.img_aug(input_images)
        is_aug = (torch.rand(batch_size, device=input_images.device)[:, None, None, None] < self.aug_proba).float()
        result = augmented * is_aug + permuted * (1 - is_aug)
        return result

    def _fill_masks_with_gradient(self, masks):
        batch_size, _, height, width = masks.shape
        grad = torch.linspace(0, 1, steps=width * 2, device=masks.device, dtype=masks.dtype).view(1, 1, 1, -1).expand(batch_size, 1, height * 2, width * 2)
        grad = self.grad_aug(grad)
        grad = CenterCrop((height, width))(grad)
        grad *= masks
        grad_for_min = grad + (1 - masks) * 10
        grad -= grad_for_min.view(batch_size, -1).min(-1).values[:, None, None, None]
        grad /= grad.view(batch_size, -1).max(-1).values[:, None, None, None] + 1e-06
        grad.clamp_(min=0, max=1)
        return grad

def _fill_masks_with_gradient(self, masks):
    batch_size, _, height, width = masks.shape
    grad = torch.linspace(0, 1, steps=width * 2, device=masks.device, dtype=masks.dtype).view(1, 1, 1, -1).expand(batch_size, 1, height * 2, width * 2)
    grad = self.grad_aug(grad)
    grad = CenterCrop((height, width))(grad)
    grad *= masks
    grad_for_min = grad + (1 - masks) * 10
    grad -= grad_for_min.view(batch_size, -1).min(-1).values[:, None, None, None]
    grad /= grad.view(batch_size, -1).max(-1).values[:, None, None, None] + 1e-06
    grad.clamp_(min=0, max=1)
    return grad

def pad_img_to_modulo(img, mod):
    channels, height, width = img.shape
    out_height = ceil_modulo(height, mod)
    out_width = ceil_modulo(width, mod)
    return np.pad(img, ((0, 0), (0, out_height - height), (0, out_width - width)), mode='symmetric')

def pad_tensor_to_modulo(img, mod):
    batch_size, channels, height, width = img.shape
    out_height = ceil_modulo(height, mod)
    out_width = ceil_modulo(width, mod)
    return F.pad(img, pad=(0, out_width - width, 0, out_height - height), mode='reflect')

def _pyrdown(im: torch.Tensor, downsize: tuple=None):
    """downscale the image"""
    if downsize is None:
        downsize = (im.shape[2] // 2, im.shape[3] // 2)
    assert im.shape[1] == 3, 'Expected shape for the input to be (n,3,height,width)'
    im = gaussian_blur2d(im, kernel_size=(5, 5), sigma=(1.0, 1.0))
    im = F.interpolate(im, size=downsize, mode='bilinear', align_corners=False)
    return im

def _pyrdown_mask(mask: torch.Tensor, downsize: tuple=None, eps: float=1e-08, blur_mask: bool=True, round_up: bool=True):
    """downscale the mask tensor

    Parameters
    ----------
    mask : torch.Tensor
        mask of size (B, 1, H, W)
    downsize : tuple, optional
        size to downscale to. If None, image is downscaled to half, by default None
    eps : float, optional
        threshold value for binarizing the mask, by default 1e-8
    blur_mask : bool, optional
        if True, apply gaussian filter before downscaling, by default True
    round_up : bool, optional
        if True, values above eps are marked 1, else, values below 1-eps are marked 0, by default True

    Returns
    -------
    torch.Tensor
        downscaled mask
    """
    if downsize is None:
        downsize = (mask.shape[2] // 2, mask.shape[3] // 2)
    assert mask.shape[1] == 1, 'Expected shape for the input to be (n,1,height,width)'
    if blur_mask == True:
        mask = gaussian_blur2d(mask, kernel_size=(5, 5), sigma=(1.0, 1.0))
        mask = F.interpolate(mask, size=downsize, mode='bilinear', align_corners=False)
    else:
        mask = F.interpolate(mask, size=downsize, mode='bilinear', align_corners=False)
    if round_up:
        mask[mask >= eps] = 1
        mask[mask < eps] = 0
    else:
        mask[mask >= 1.0 - eps] = 1
        mask[mask < 1.0 - eps] = 0
    return mask

def ssim_fid100_f1(metrics, fid_scale=100):
    ssim = metrics['ssim', 'total']['mean']
    fid = metrics['fid', 'total']['mean']
    fid_rel = max(0, fid_scale - fid) / fid_scale
    f1 = 2 * ssim * fid_rel / (ssim + fid_rel + 0.001)
    return f1

def lpips_fid100_f1(metrics, fid_scale=100):
    neg_lpips = 1 - metrics['lpips', 'total']['mean']
    fid = metrics['fid', 'total']['mean']
    fid_rel = max(0, fid_scale - fid) / fid_scale
    f1 = 2 * neg_lpips * fid_rel / (neg_lpips + fid_rel + 0.001)
    return f1

class InpaintingEvaluatorOnline(nn.Module):

    def __init__(self, scores, bins=10, image_key='image', inpainted_key='inpainted', integral_func=None, integral_title=None, clamp_image_range=None):
        """
        :param scores: dict {score_name: EvaluatorScore object}
        :param bins: number of groups, partition is generated by np.linspace(0., 1., bins + 1)
        :param device: device to use
        """
        super().__init__()
        LOGGER.info(f'{type(self)} init called')
        self.scores = nn.ModuleDict(scores)
        self.image_key = image_key
        self.inpainted_key = inpainted_key
        self.bins_num = bins
        self.bin_edges = np.linspace(0, 1, self.bins_num + 1)
        num_digits = max(0, math.ceil(math.log10(self.bins_num)) - 1)
        self.interval_names = []
        for idx_bin in range(self.bins_num):
            start_percent, end_percent = (round(100 * self.bin_edges[idx_bin], num_digits), round(100 * self.bin_edges[idx_bin + 1], num_digits))
            start_percent = '{:.{n}f}'.format(start_percent, n=num_digits)
            end_percent = '{:.{n}f}'.format(end_percent, n=num_digits)
            self.interval_names.append('{0}-{1}%'.format(start_percent, end_percent))
        self.groups = []
        self.integral_func = integral_func
        self.integral_title = integral_title
        self.clamp_image_range = clamp_image_range
        LOGGER.info(f'{type(self)} init done')

    def _get_bins(self, mask_batch):
        batch_size = mask_batch.shape[0]
        area = mask_batch.view(batch_size, -1).mean(dim=-1).detach().cpu().numpy()
        bin_indices = np.clip(np.searchsorted(self.bin_edges, area) - 1, 0, self.bins_num - 1)
        return bin_indices

    def forward(self, batch: Dict[str, torch.Tensor]):
        """
        Calculate and accumulate metrics for batch. To finalize evaluation and obtain final metrics, call evaluation_end
        :param batch: batch dict with mandatory fields mask, image, inpainted (can be overriden by self.inpainted_key)
        """
        result = {}
        with torch.no_grad():
            image_batch, mask_batch, inpainted_batch = (batch[self.image_key], batch['mask'], batch[self.inpainted_key])
            if self.clamp_image_range is not None:
                image_batch = torch.clamp(image_batch, min=self.clamp_image_range[0], max=self.clamp_image_range[1])
            self.groups.extend(self._get_bins(mask_batch))
            for score_name, score in self.scores.items():
                result[score_name] = score(inpainted_batch, image_batch, mask_batch)
        return result

    def process_batch(self, batch: Dict[str, torch.Tensor]):
        return self(batch)

    def evaluation_end(self, states=None):
        """:return: dict with (score_name, group_type) as keys, where group_type can be either 'overall' or
            name of the particular group arranged by area of mask (e.g. '10-20%')
            and score statistics for the group as values.
        """
        LOGGER.info(f'{type(self)}: evaluation_end called')
        self.groups = np.array(self.groups)
        results = {}
        for score_name, score in self.scores.items():
            LOGGER.info(f'Getting value of {score_name}')
            cur_states = [s[score_name] for s in states] if states is not None else None
            total_results, group_results = score.get_value(groups=self.groups, states=cur_states)
            LOGGER.info(f'Getting value of {score_name} done')
            results[score_name, 'total'] = total_results
            for group_index, group_values in group_results.items():
                group_name = self.interval_names[group_index]
                results[score_name, group_name] = group_values
        if self.integral_func is not None:
            results[self.integral_title, 'total'] = dict(mean=self.integral_func(results))
        LOGGER.info(f'{type(self)}: reset scores')
        self.groups = []
        for sc in self.scores.values():
            sc.reset()
        LOGGER.info(f'{type(self)}: reset scores done')
        LOGGER.info(f'{type(self)}: evaluation_end done')
        return results

def forward(self, batch: Dict[str, torch.Tensor]):
    """
        Calculate and accumulate metrics for batch. To finalize evaluation and obtain final metrics, call evaluation_end
        :param batch: batch dict with mandatory fields mask, image, inpainted (can be overriden by self.inpainted_key)
        """
    result = {}
    with torch.no_grad():
        image_batch, mask_batch, inpainted_batch = (batch[self.image_key], batch['mask'], batch[self.inpainted_key])
        if self.clamp_image_range is not None:
            image_batch = torch.clamp(image_batch, min=self.clamp_image_range[0], max=self.clamp_image_range[1])
        self.groups.extend(self._get_bins(mask_batch))
        for score_name, score in self.scores.items():
            result[score_name] = score(inpainted_batch, image_batch, mask_batch)
    return result

class FIDScore(EvaluatorScore):

    def __init__(self, dims=2048, eps=1e-06):
        LOGGER.info('FIDscore init called')
        super().__init__()
        if getattr(FIDScore, '_MODEL', None) is None:
            block_idx = InceptionV3.BLOCK_INDEX_BY_DIM[dims]
            FIDScore._MODEL = InceptionV3([block_idx]).eval()
        self.model = FIDScore._MODEL
        self.eps = eps
        self.reset()
        LOGGER.info('FIDscore init done')

    def forward(self, pred_batch, target_batch, mask=None):
        activations_pred = self._get_activations(pred_batch)
        activations_target = self._get_activations(target_batch)
        self.activations_pred.append(activations_pred.detach().cpu())
        self.activations_target.append(activations_target.detach().cpu())
        return (activations_pred, activations_target)

    def get_value(self, groups=None, states=None):
        LOGGER.info('FIDscore get_value called')
        activations_pred, activations_target = zip(*states) if states is not None else (self.activations_pred, self.activations_target)
        activations_pred = torch.cat(activations_pred).cpu().numpy()
        activations_target = torch.cat(activations_target).cpu().numpy()
        total_distance = calculate_frechet_distance(activations_pred, activations_target, eps=self.eps)
        total_results = dict(mean=total_distance)
        if groups is None:
            group_results = None
        else:
            group_results = dict()
            grouping = get_groupings(groups)
            for label, index in grouping.items():
                if len(index) > 1:
                    group_distance = calculate_frechet_distance(activations_pred[index], activations_target[index], eps=self.eps)
                    group_results[label] = dict(mean=group_distance)
                else:
                    group_results[label] = dict(mean=float('nan'))
        self.reset()
        LOGGER.info('FIDscore get_value done')
        return (total_results, group_results)

    def reset(self):
        self.activations_pred = []
        self.activations_target = []

    def _get_activations(self, batch):
        activations = self.model(batch)[0]
        if activations.shape[2] != 1 or activations.shape[3] != 1:
            assert False, 'We should not have got here, because Inception always scales inputs to 299x299'
        activations = activations.squeeze(-1).squeeze(-1)
        return activations

def _get_activations(self, batch):
    activations = self.model(batch)[0]
    if activations.shape[2] != 1 or activations.shape[3] != 1:
        assert False, 'We should not have got here, because Inception always scales inputs to 299x299'
    activations = activations.squeeze(-1).squeeze(-1)
    return activations

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

def _create_window(self, window_size, channel):
    _1D_window = self._gaussian(window_size, 1.5).unsqueeze(1)
    _2D_window = _1D_window.mm(_1D_window.t()).float().unsqueeze(0).unsqueeze(0)
    return _2D_window.expand(channel, 1, window_size, window_size).contiguous()

def voc_ap(rec, prec, use_07_metric=False):
    """ ap = voc_ap(rec, prec, [use_07_metric])
    Compute VOC AP given precision and recall.
    If use_07_metric is true, uses the
    VOC 07 11 point method (default:False).
    """
    if use_07_metric:
        ap = 0.0
        for t in np.arange(0.0, 1.1, 0.1):
            if np.sum(rec >= t) == 0:
                p = 0
            else:
                p = np.max(prec[rec >= t])
            ap = ap + p / 11.0
    else:
        mrec = np.concatenate(([0.0], rec, [1.0]))
        mpre = np.concatenate(([0.0], prec, [0.0]))
        for i in range(mpre.size - 1, 0, -1):
            mpre[i - 1] = np.maximum(mpre[i - 1], mpre[i])
        i = np.where(mrec[1:] != mrec[:-1])[0]
        ap = np.sum((mrec[i + 1] - mrec[i]) * mpre[i + 1])
    return ap

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

def clamp_weights(self):
    for module in self.net.modules():
        if hasattr(module, 'weight') and module.kernel_size == (1, 1):
            module.weight.data = torch.clamp(module.weight.data, min=0)

class InceptionV3(nn.Module):
    """Pretrained InceptionV3 network returning feature maps"""
    DEFAULT_BLOCK_INDEX = 3
    BLOCK_INDEX_BY_DIM = {64: 0, 192: 1, 768: 2, 2048: 3}

    def __init__(self, output_blocks=[DEFAULT_BLOCK_INDEX], resize_input=True, normalize_input=True, requires_grad=False, use_fid_inception=True):
        """Build pretrained InceptionV3

        Parameters
        ----------
        output_blocks : list of int
            Indices of blocks to return features of. Possible values are:
                - 0: corresponds to output of first max pooling
                - 1: corresponds to output of second max pooling
                - 2: corresponds to output which is fed to aux classifier
                - 3: corresponds to output of final average pooling
        resize_input : bool
            If true, bilinearly resizes input to width and height 299 before
            feeding input to model. As the network without fully connected
            layers is fully convolutional, it should be able to handle inputs
            of arbitrary size, so resizing might not be strictly needed
        normalize_input : bool
            If true, scales the input from range (0, 1) to the range the
            pretrained Inception network expects, namely (-1, 1)
        requires_grad : bool
            If true, parameters of the model require gradients. Possibly useful
            for finetuning the network
        use_fid_inception : bool
            If true, uses the pretrained Inception model used in Tensorflow's
            FID implementation. If false, uses the pretrained Inception model
            available in torchvision. The FID Inception model has different
            weights and a slightly different structure from torchvision's
            Inception model. If you want to compute FID scores, you are
            strongly advised to set this parameter to true to get comparable
            results.
        """
        super(InceptionV3, self).__init__()
        self.resize_input = resize_input
        self.normalize_input = normalize_input
        self.output_blocks = sorted(output_blocks)
        self.last_needed_block = max(output_blocks)
        assert self.last_needed_block <= 3, 'Last possible output block index is 3'
        self.blocks = nn.ModuleList()
        if use_fid_inception:
            inception = fid_inception_v3()
        else:
            inception = models.inception_v3(pretrained=True)
        block0 = [inception.Conv2d_1a_3x3, inception.Conv2d_2a_3x3, inception.Conv2d_2b_3x3, nn.MaxPool2d(kernel_size=3, stride=2)]
        self.blocks.append(nn.Sequential(*block0))
        if self.last_needed_block >= 1:
            block1 = [inception.Conv2d_3b_1x1, inception.Conv2d_4a_3x3, nn.MaxPool2d(kernel_size=3, stride=2)]
            self.blocks.append(nn.Sequential(*block1))
        if self.last_needed_block >= 2:
            block2 = [inception.Mixed_5b, inception.Mixed_5c, inception.Mixed_5d, inception.Mixed_6a, inception.Mixed_6b, inception.Mixed_6c, inception.Mixed_6d, inception.Mixed_6e]
            self.blocks.append(nn.Sequential(*block2))
        if self.last_needed_block >= 3:
            block3 = [inception.Mixed_7a, inception.Mixed_7b, inception.Mixed_7c, nn.AdaptiveAvgPool2d(output_size=(1, 1))]
            self.blocks.append(nn.Sequential(*block3))
        for param in self.parameters():
            param.requires_grad = requires_grad

    def forward(self, inp):
        """Get Inception feature maps

        Parameters
        ----------
        inp : torch.autograd.Variable
            Input tensor of shape Bx3xHxW. Values are expected to be in
            range (0, 1)

        Returns
        -------
        List of torch.autograd.Variable, corresponding to the selected output
        block, sorted ascending by index
        """
        outp = []
        x = inp
        if self.resize_input:
            x = F.interpolate(x, size=(299, 299), mode='bilinear', align_corners=False)
        if self.normalize_input:
            x = 2 * x - 1
        for idx, block in enumerate(self.blocks):
            x = block(x)
            if idx in self.output_blocks:
                outp.append(x)
            if idx == self.last_needed_block:
                break
        return outp

def forward(self, inp):
    """Get Inception feature maps

        Parameters
        ----------
        inp : torch.autograd.Variable
            Input tensor of shape Bx3xHxW. Values are expected to be in
            range (0, 1)

        Returns
        -------
        List of torch.autograd.Variable, corresponding to the selected output
        block, sorted ascending by index
        """
    outp = []
    x = inp
    if self.resize_input:
        x = F.interpolate(x, size=(299, 299), mode='bilinear', align_corners=False)
    if self.normalize_input:
        x = 2 * x - 1
    for idx, block in enumerate(self.blocks):
        x = block(x)
        if idx in self.output_blocks:
            outp.append(x)
        if idx == self.last_needed_block:
            break
    return outp

def propose_random_square_crop(mask, min_overlap=0.5):
    height, width = mask.shape
    mask_ys, mask_xs = np.where(mask > 0.5)
    if height < width:
        crop_size = height
        obj_left, obj_right = (mask_xs.min(), mask_xs.max())
        obj_width = obj_right - obj_left
        left_border = max(0, min(width - crop_size - 1, obj_left + obj_width * min_overlap - crop_size))
        right_border = max(left_border + 1, min(width - crop_size, obj_left + obj_width * min_overlap))
        start_x = np.random.randint(left_border, right_border)
        return (start_x, 0, start_x + crop_size, height)
    else:
        crop_size = width
        obj_top, obj_bottom = (mask_ys.min(), mask_ys.max())
        obj_height = obj_bottom - obj_top
        top_border = max(0, min(height - crop_size - 1, obj_top + obj_height * min_overlap - crop_size))
        bottom_border = max(top_border + 1, min(height - crop_size, obj_top + obj_height * min_overlap))
        start_y = np.random.randint(top_border, bottom_border)
        return (0, start_y, width, start_y + crop_size)

class InvertedResidual(nn.Module):

    def __init__(self, inp, oup, stride, expand_ratio):
        super(InvertedResidual, self).__init__()
        self.stride = stride
        assert stride in [1, 2]
        hidden_dim = round(inp * expand_ratio)
        self.use_res_connect = self.stride == 1 and inp == oup
        if expand_ratio == 1:
            self.conv = nn.Sequential(nn.Conv2d(hidden_dim, hidden_dim, 3, stride, 1, groups=hidden_dim, bias=False), BatchNorm2d(hidden_dim), nn.ReLU6(inplace=True), nn.Conv2d(hidden_dim, oup, 1, 1, 0, bias=False), BatchNorm2d(oup))
        else:
            self.conv = nn.Sequential(nn.Conv2d(inp, hidden_dim, 1, 1, 0, bias=False), BatchNorm2d(hidden_dim), nn.ReLU6(inplace=True), nn.Conv2d(hidden_dim, hidden_dim, 3, stride, 1, groups=hidden_dim, bias=False), BatchNorm2d(hidden_dim), nn.ReLU6(inplace=True), nn.Conv2d(hidden_dim, oup, 1, 1, 0, bias=False), BatchNorm2d(oup))

    def forward(self, x):
        if self.use_res_connect:
            return x + self.conv(x)
        else:
            return self.conv(x)

def forward(self, x):
    if self.use_res_connect:
        return x + self.conv(x)
    else:
        return self.conv(x)

class SegmentationModule(nn.Module):

    def __init__(self, weights_path, num_classes=150, arch_encoder='resnet50dilated', drop_last_conv=False, net_enc=None, net_dec=None, encode=None, use_default_normalization=False, return_feature_maps=False, return_feature_maps_level=3, return_feature_maps_only=True, **kwargs):
        super().__init__()
        self.weights_path = weights_path
        self.drop_last_conv = drop_last_conv
        self.arch_encoder = arch_encoder
        if self.arch_encoder == 'resnet50dilated':
            self.arch_decoder = 'ppm_deepsup'
            self.fc_dim = 2048
        elif self.arch_encoder == 'mobilenetv2dilated':
            self.arch_decoder = 'c1_deepsup'
            self.fc_dim = 320
        else:
            raise NotImplementedError(f'No such arch_encoder={self.arch_encoder}')
        model_builder_kwargs = dict(arch_encoder=self.arch_encoder, arch_decoder=self.arch_decoder, fc_dim=self.fc_dim, drop_last_conv=drop_last_conv, weights_path=self.weights_path)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.encoder = ModelBuilder.get_encoder(**model_builder_kwargs) if net_enc is None else net_enc
        self.decoder = ModelBuilder.get_decoder(**model_builder_kwargs) if net_dec is None else net_dec
        self.use_default_normalization = use_default_normalization
        self.default_normalization = NormalizeTensor(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        self.encode = encode
        self.return_feature_maps = return_feature_maps
        assert 0 <= return_feature_maps_level <= 3
        self.return_feature_maps_level = return_feature_maps_level

    def normalize_input(self, tensor):
        if tensor.min() < 0 or tensor.max() > 1:
            raise ValueError('Tensor should be 0..1 before using normalize_input')
        return self.default_normalization(tensor)

    @property
    def feature_maps_channels(self):
        return 256 * 2 ** self.return_feature_maps_level

    def forward(self, img_data, segSize=None):
        if segSize is None:
            raise NotImplementedError('Please pass segSize param. By default: (300, 300)')
        fmaps = self.encoder(img_data, return_feature_maps=True)
        pred = self.decoder(fmaps, segSize=segSize)
        if self.return_feature_maps:
            return (pred, fmaps)
        return pred

    def multi_mask_from_multiclass(self, pred, classes):

        def isin(ar1, ar2):
            return (ar1[..., None] == ar2).any(-1).float()
        return isin(pred, torch.LongTensor(classes).to(self.device))

    @staticmethod
    def multi_mask_from_multiclass_probs(scores, classes):
        res = None
        for c in classes:
            if res is None:
                res = scores[:, c]
            else:
                res += scores[:, c]
        return res

    def predict(self, tensor, imgSizes=(-1,), segSize=None):
        """Entry-point for segmentation. Use this methods instead of forward
        Arguments:
            tensor {torch.Tensor} -- BCHW
        Keyword Arguments:
            imgSizes {tuple or list} -- imgSizes for segmentation input.
                default: (300, 450)
                original implementation: (300, 375, 450, 525, 600)

        """
        if segSize is None:
            segSize = tensor.shape[-2:]
        segSize = (tensor.shape[2], tensor.shape[3])
        with torch.no_grad():
            if self.use_default_normalization:
                tensor = self.normalize_input(tensor)
            scores = torch.zeros(1, NUM_CLASS, segSize[0], segSize[1]).to(self.device)
            features = torch.zeros(1, self.feature_maps_channels, segSize[0], segSize[1]).to(self.device)
            result = []
            for img_size in imgSizes:
                if img_size != -1:
                    img_data = F.interpolate(tensor.clone(), size=img_size)
                else:
                    img_data = tensor.clone()
                if self.return_feature_maps:
                    pred_current, fmaps = self.forward(img_data, segSize=segSize)
                else:
                    pred_current = self.forward(img_data, segSize=segSize)
                result.append(pred_current)
                scores = scores + pred_current / len(imgSizes)
                if self.return_feature_maps:
                    features = features + F.interpolate(fmaps[self.return_feature_maps_level], size=segSize) / len(imgSizes)
            _, pred = torch.max(scores, dim=1)
            if self.return_feature_maps:
                return features
            return (pred, result)

    def get_edges(self, t):
        edge = torch.cuda.ByteTensor(t.size()).zero_()
        edge[:, :, :, 1:] = edge[:, :, :, 1:] | (t[:, :, :, 1:] != t[:, :, :, :-1])
        edge[:, :, :, :-1] = edge[:, :, :, :-1] | (t[:, :, :, 1:] != t[:, :, :, :-1])
        edge[:, :, 1:, :] = edge[:, :, 1:, :] | (t[:, :, 1:, :] != t[:, :, :-1, :])
        edge[:, :, :-1, :] = edge[:, :, :-1, :] | (t[:, :, 1:, :] != t[:, :, :-1, :])
        if True:
            return edge.half()
        return edge.float()

def get_edges(self, t):
    edge = torch.cuda.ByteTensor(t.size()).zero_()
    edge[:, :, :, 1:] = edge[:, :, :, 1:] | (t[:, :, :, 1:] != t[:, :, :, :-1])
    edge[:, :, :, :-1] = edge[:, :, :, :-1] | (t[:, :, :, 1:] != t[:, :, :, :-1])
    edge[:, :, 1:, :] = edge[:, :, 1:, :] | (t[:, :, 1:, :] != t[:, :, :-1, :])
    edge[:, :, :-1, :] = edge[:, :, :-1, :] | (t[:, :, 1:, :] != t[:, :, :-1, :])
    if True:
        return edge.half()
    return edge.float()

class PPMDeepsup(nn.Module):

    def __init__(self, num_class=NUM_CLASS, fc_dim=4096, use_softmax=False, pool_scales=(1, 2, 3, 6), drop_last_conv=False):
        super().__init__()
        self.use_softmax = use_softmax
        self.drop_last_conv = drop_last_conv
        self.ppm = []
        for scale in pool_scales:
            self.ppm.append(nn.Sequential(nn.AdaptiveAvgPool2d(scale), nn.Conv2d(fc_dim, 512, kernel_size=1, bias=False), BatchNorm2d(512), nn.ReLU(inplace=True)))
        self.ppm = nn.ModuleList(self.ppm)
        self.cbr_deepsup = conv3x3_bn_relu(fc_dim // 2, fc_dim // 4, 1)
        self.conv_last = nn.Sequential(nn.Conv2d(fc_dim + len(pool_scales) * 512, 512, kernel_size=3, padding=1, bias=False), BatchNorm2d(512), nn.ReLU(inplace=True), nn.Dropout2d(0.1), nn.Conv2d(512, num_class, kernel_size=1))
        self.conv_last_deepsup = nn.Conv2d(fc_dim // 4, num_class, 1, 1, 0)
        self.dropout_deepsup = nn.Dropout2d(0.1)

    def forward(self, conv_out, segSize=None):
        conv5 = conv_out[-1]
        input_size = conv5.size()
        ppm_out = [conv5]
        for pool_scale in self.ppm:
            ppm_out.append(nn.functional.interpolate(pool_scale(conv5), (input_size[2], input_size[3]), mode='bilinear', align_corners=False))
        ppm_out = torch.cat(ppm_out, 1)
        if self.drop_last_conv:
            return ppm_out
        else:
            x = self.conv_last(ppm_out)
            if self.use_softmax:
                x = nn.functional.interpolate(x, size=segSize, mode='bilinear', align_corners=False)
                x = nn.functional.softmax(x, dim=1)
                return x
            conv4 = conv_out[-2]
            _ = self.cbr_deepsup(conv4)
            _ = self.dropout_deepsup(_)
            _ = self.conv_last_deepsup(_)
            x = nn.functional.log_softmax(x, dim=1)
            _ = nn.functional.log_softmax(_, dim=1)
            return (x, _)

def forward(self, conv_out, segSize=None):
    conv5 = conv_out[-1]
    input_size = conv5.size()
    ppm_out = [conv5]
    for pool_scale in self.ppm:
        ppm_out.append(nn.functional.interpolate(pool_scale(conv5), (input_size[2], input_size[3]), mode='bilinear', align_corners=False))
    ppm_out = torch.cat(ppm_out, 1)
    if self.drop_last_conv:
        return ppm_out
    else:
        x = self.conv_last(ppm_out)
        if self.use_softmax:
            x = nn.functional.interpolate(x, size=segSize, mode='bilinear', align_corners=False)
            x = nn.functional.softmax(x, dim=1)
            return x
        conv4 = conv_out[-2]
        _ = self.cbr_deepsup(conv4)
        _ = self.dropout_deepsup(_)
        _ = self.conv_last_deepsup(_)
        x = nn.functional.log_softmax(x, dim=1)
        _ = nn.functional.log_softmax(_, dim=1)
        return (x, _)

class C1DeepSup(nn.Module):

    def __init__(self, num_class=150, fc_dim=2048, use_softmax=False, drop_last_conv=False):
        super(C1DeepSup, self).__init__()
        self.use_softmax = use_softmax
        self.drop_last_conv = drop_last_conv
        self.cbr = conv3x3_bn_relu(fc_dim, fc_dim // 4, 1)
        self.cbr_deepsup = conv3x3_bn_relu(fc_dim // 2, fc_dim // 4, 1)
        self.conv_last = nn.Conv2d(fc_dim // 4, num_class, 1, 1, 0)
        self.conv_last_deepsup = nn.Conv2d(fc_dim // 4, num_class, 1, 1, 0)

    def forward(self, conv_out, segSize=None):
        conv5 = conv_out[-1]
        x = self.cbr(conv5)
        if self.drop_last_conv:
            return x
        else:
            x = self.conv_last(x)
            if self.use_softmax:
                x = nn.functional.interpolate(x, size=segSize, mode='bilinear', align_corners=False)
                x = nn.functional.softmax(x, dim=1)
                return x
            conv4 = conv_out[-2]
            _ = self.cbr_deepsup(conv4)
            _ = self.conv_last_deepsup(_)
            x = nn.functional.log_softmax(x, dim=1)
            _ = nn.functional.log_softmax(_, dim=1)
            return (x, _)

def forward(self, conv_out, segSize=None):
    conv5 = conv_out[-1]
    x = self.cbr(conv5)
    if self.drop_last_conv:
        return x
    else:
        x = self.conv_last(x)
        if self.use_softmax:
            x = nn.functional.interpolate(x, size=segSize, mode='bilinear', align_corners=False)
            x = nn.functional.softmax(x, dim=1)
            return x
        conv4 = conv_out[-2]
        _ = self.cbr_deepsup(conv4)
        _ = self.conv_last_deepsup(_)
        x = nn.functional.log_softmax(x, dim=1)
        _ = nn.functional.log_softmax(_, dim=1)
        return (x, _)

class C1(nn.Module):

    def __init__(self, num_class=150, fc_dim=2048, use_softmax=False):
        super(C1, self).__init__()
        self.use_softmax = use_softmax
        self.cbr = conv3x3_bn_relu(fc_dim, fc_dim // 4, 1)
        self.conv_last = nn.Conv2d(fc_dim // 4, num_class, 1, 1, 0)

    def forward(self, conv_out, segSize=None):
        conv5 = conv_out[-1]
        x = self.cbr(conv5)
        x = self.conv_last(x)
        if self.use_softmax:
            x = nn.functional.interpolate(x, size=segSize, mode='bilinear', align_corners=False)
            x = nn.functional.softmax(x, dim=1)
        else:
            x = nn.functional.log_softmax(x, dim=1)
        return x

def forward(self, conv_out, segSize=None):
    conv5 = conv_out[-1]
    x = self.cbr(conv5)
    x = self.conv_last(x)
    if self.use_softmax:
        x = nn.functional.interpolate(x, size=segSize, mode='bilinear', align_corners=False)
        x = nn.functional.softmax(x, dim=1)
    else:
        x = nn.functional.log_softmax(x, dim=1)
    return x

class PPM(nn.Module):

    def __init__(self, num_class=150, fc_dim=4096, use_softmax=False, pool_scales=(1, 2, 3, 6)):
        super(PPM, self).__init__()
        self.use_softmax = use_softmax
        self.ppm = []
        for scale in pool_scales:
            self.ppm.append(nn.Sequential(nn.AdaptiveAvgPool2d(scale), nn.Conv2d(fc_dim, 512, kernel_size=1, bias=False), BatchNorm2d(512), nn.ReLU(inplace=True)))
        self.ppm = nn.ModuleList(self.ppm)
        self.conv_last = nn.Sequential(nn.Conv2d(fc_dim + len(pool_scales) * 512, 512, kernel_size=3, padding=1, bias=False), BatchNorm2d(512), nn.ReLU(inplace=True), nn.Dropout2d(0.1), nn.Conv2d(512, num_class, kernel_size=1))

    def forward(self, conv_out, segSize=None):
        conv5 = conv_out[-1]
        input_size = conv5.size()
        ppm_out = [conv5]
        for pool_scale in self.ppm:
            ppm_out.append(nn.functional.interpolate(pool_scale(conv5), (input_size[2], input_size[3]), mode='bilinear', align_corners=False))
        ppm_out = torch.cat(ppm_out, 1)
        x = self.conv_last(ppm_out)
        if self.use_softmax:
            x = nn.functional.interpolate(x, size=segSize, mode='bilinear', align_corners=False)
            x = nn.functional.softmax(x, dim=1)
        else:
            x = nn.functional.log_softmax(x, dim=1)
        return x

def forward(self, conv_out, segSize=None):
    conv5 = conv_out[-1]
    input_size = conv5.size()
    ppm_out = [conv5]
    for pool_scale in self.ppm:
        ppm_out.append(nn.functional.interpolate(pool_scale(conv5), (input_size[2], input_size[3]), mode='bilinear', align_corners=False))
    ppm_out = torch.cat(ppm_out, 1)
    x = self.conv_last(ppm_out)
    if self.use_softmax:
        x = nn.functional.interpolate(x, size=segSize, mode='bilinear', align_corners=False)
        x = nn.functional.softmax(x, dim=1)
    else:
        x = nn.functional.log_softmax(x, dim=1)
    return x

def _unsqueeze_ft(tensor):
    """add new dementions at the front and the tail"""
    return tensor.unsqueeze(0).unsqueeze(-1)

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

def check_and_warn_input_range(tensor, min_value, max_value, name):
    actual_min = tensor.min()
    actual_max = tensor.max()
    if actual_min < min_value or actual_max > max_value:
        warnings.warn(f'{name} must be in {min_value}..{max_value} range, but it ranges {actual_min}..{actual_max}')

class BaseAdversarialLoss:

    def pre_generator_step(self, real_batch: torch.Tensor, fake_batch: torch.Tensor, generator: nn.Module, discriminator: nn.Module):
        """
        Prepare for generator step
        :param real_batch: Tensor, a batch of real samples
        :param fake_batch: Tensor, a batch of samples produced by generator
        :param generator:
        :param discriminator:
        :return: None
        """

    def pre_discriminator_step(self, real_batch: torch.Tensor, fake_batch: torch.Tensor, generator: nn.Module, discriminator: nn.Module):
        """
        Prepare for discriminator step
        :param real_batch: Tensor, a batch of real samples
        :param fake_batch: Tensor, a batch of samples produced by generator
        :param generator:
        :param discriminator:
        :return: None
        """

    def generator_loss(self, real_batch: torch.Tensor, fake_batch: torch.Tensor, discr_real_pred: torch.Tensor, discr_fake_pred: torch.Tensor, mask: Optional[torch.Tensor]=None) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        """
        Calculate generator loss
        :param real_batch: Tensor, a batch of real samples
        :param fake_batch: Tensor, a batch of samples produced by generator
        :param discr_real_pred: Tensor, discriminator output for real_batch
        :param discr_fake_pred: Tensor, discriminator output for fake_batch
        :param mask: Tensor, actual mask, which was at input of generator when making fake_batch
        :return: total generator loss along with some values that might be interesting to log
        """
        raise NotImplemented()

    def discriminator_loss(self, real_batch: torch.Tensor, fake_batch: torch.Tensor, discr_real_pred: torch.Tensor, discr_fake_pred: torch.Tensor, mask: Optional[torch.Tensor]=None) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        """
        Calculate discriminator loss and call .backward() on it
        :param real_batch: Tensor, a batch of real samples
        :param fake_batch: Tensor, a batch of samples produced by generator
        :param discr_real_pred: Tensor, discriminator output for real_batch
        :param discr_fake_pred: Tensor, discriminator output for fake_batch
        :param mask: Tensor, actual mask, which was at input of generator when making fake_batch
        :return: total discriminator loss along with some values that might be interesting to log
        """
        raise NotImplemented()

    def interpolate_mask(self, mask, shape):
        assert mask is not None
        assert self.allow_scale_mask or shape == mask.shape[-2:]
        if shape != mask.shape[-2:] and self.allow_scale_mask:
            if self.mask_scale_mode == 'maxpool':
                mask = F.adaptive_max_pool2d(mask, shape)
            else:
                mask = F.interpolate(mask, size=shape, mode=self.mask_scale_mode)
        return mask

def interpolate_mask(self, mask, shape):
    assert mask is not None
    assert self.allow_scale_mask or shape == mask.shape[-2:]
    if shape != mask.shape[-2:] and self.allow_scale_mask:
        if self.mask_scale_mode == 'maxpool':
            mask = F.adaptive_max_pool2d(mask, shape)
        else:
            mask = F.interpolate(mask, size=shape, mode=self.mask_scale_mode)
    return mask

def make_r1_gp(discr_real_pred, real_batch):
    if torch.is_grad_enabled():
        grad_real = torch.autograd.grad(outputs=discr_real_pred.sum(), inputs=real_batch, create_graph=True)[0]
        grad_penalty = (grad_real.view(grad_real.shape[0], -1).norm(2, dim=1) ** 2).mean()
    else:
        grad_penalty = 0
    real_batch.requires_grad = False
    return grad_penalty

class CrossEntropy2d(nn.Module):

    def __init__(self, reduction='mean', ignore_label=255, weights=None, *args, **kwargs):
        """
        weight (Tensor, optional): a manual rescaling weight given to each class.
            If given, has to be a Tensor of size "nclasses"
        """
        super(CrossEntropy2d, self).__init__()
        self.reduction = reduction
        self.ignore_label = ignore_label
        self.weights = weights
        if self.weights is not None:
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            self.weights = torch.FloatTensor(constant_weights[weights]).to(device)

    def forward(self, predict, target):
        """
            Args:
                predict:(n, c, h, w)
                target:(n, 1, h, w)
        """
        target = target.long()
        assert not target.requires_grad
        assert predict.dim() == 4, '{0}'.format(predict.size())
        assert target.dim() == 4, '{0}'.format(target.size())
        assert predict.size(0) == target.size(0), '{0} vs {1} '.format(predict.size(0), target.size(0))
        assert target.size(1) == 1, '{0}'.format(target.size(1))
        assert predict.size(2) == target.size(2), '{0} vs {1} '.format(predict.size(2), target.size(2))
        assert predict.size(3) == target.size(3), '{0} vs {1} '.format(predict.size(3), target.size(3))
        target = target.squeeze(1)
        n, c, h, w = predict.size()
        target_mask = (target >= 0) * (target != self.ignore_label)
        target = target[target_mask]
        predict = predict.transpose(1, 2).transpose(2, 3).contiguous()
        predict = predict[target_mask.view(n, h, w, 1).repeat(1, 1, 1, c)].view(-1, c)
        loss = F.cross_entropy(predict, target, weight=self.weights, reduction=self.reduction)
        return loss

def forward(self, predict, target):
    """
            Args:
                predict:(n, c, h, w)
                target:(n, 1, h, w)
        """
    target = target.long()
    assert not target.requires_grad
    assert predict.dim() == 4, '{0}'.format(predict.size())
    assert target.dim() == 4, '{0}'.format(target.size())
    assert predict.size(0) == target.size(0), '{0} vs {1} '.format(predict.size(0), target.size(0))
    assert target.size(1) == 1, '{0}'.format(target.size(1))
    assert predict.size(2) == target.size(2), '{0} vs {1} '.format(predict.size(2), target.size(2))
    assert predict.size(3) == target.size(3), '{0} vs {1} '.format(predict.size(3), target.size(3))
    target = target.squeeze(1)
    n, c, h, w = predict.size()
    target_mask = (target >= 0) * (target != self.ignore_label)
    target = target[target_mask]
    predict = predict.transpose(1, 2).transpose(2, 3).contiguous()
    predict = predict[target_mask.view(n, h, w, 1).repeat(1, 1, 1, c)].view(-1, c)
    loss = F.cross_entropy(predict, target, weight=self.weights, reduction=self.reduction)
    return loss

def get_gauss_kernel(kernel_size, width_factor=1):
    coords = torch.stack(torch.meshgrid(torch.arange(kernel_size), torch.arange(kernel_size)), dim=0).float()
    diff = torch.exp(-((coords - kernel_size // 2) ** 2).sum(0) / kernel_size / width_factor)
    diff /= diff.sum()
    return diff

class ImgSegmentationDataset(Dataset):

    def __init__(self, indir, mask_generator, transform, out_size, segm_indir, semantic_seg_n_classes):
        self.indir = indir
        self.segm_indir = segm_indir
        self.mask_generator = mask_generator
        self.transform = transform
        self.out_size = out_size
        self.semantic_seg_n_classes = semantic_seg_n_classes
        self.in_files = list(glob.glob(os.path.join(indir, '**', '*.jpg'), recursive=True))

    def __len__(self):
        return len(self.in_files)

    def __getitem__(self, item):
        path = self.in_files[item]
        img = cv2.imread(path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, (self.out_size, self.out_size))
        img = self.transform(image=img)['image']
        img = np.transpose(img, (2, 0, 1))
        mask = self.mask_generator(img)
        segm, segm_classes = self.load_semantic_segm(path)
        result = dict(image=img, mask=mask, segm=segm, segm_classes=segm_classes)
        return result

    def load_semantic_segm(self, img_path):
        segm_path = img_path.replace(self.indir, self.segm_indir).replace('.jpg', '.png')
        mask = cv2.imread(segm_path, cv2.IMREAD_GRAYSCALE)
        mask = cv2.resize(mask, (self.out_size, self.out_size))
        tensor = torch.from_numpy(np.clip(mask.astype(int) - 1, 0, None))
        ohe = F.one_hot(tensor.long(), num_classes=self.semantic_seg_n_classes)
        return (ohe.permute(2, 0, 1).float(), tensor.unsqueeze(0))

def load_semantic_segm(self, img_path):
    segm_path = img_path.replace(self.indir, self.segm_indir).replace('.jpg', '.png')
    mask = cv2.imread(segm_path, cv2.IMREAD_GRAYSCALE)
    mask = cv2.resize(mask, (self.out_size, self.out_size))
    tensor = torch.from_numpy(np.clip(mask.astype(int) - 1, 0, None))
    ohe = F.one_hot(tensor.long(), num_classes=self.semantic_seg_n_classes)
    return (ohe.permute(2, 0, 1).float(), tensor.unsqueeze(0))

def make_multiscale_noise(base_tensor, scales=6, scale_mode='bilinear'):
    batch_size, _, height, width = base_tensor.shape
    cur_height, cur_width = (height, width)
    result = []
    align_corners = False if scale_mode in ('bilinear', 'bicubic') else None
    for _ in range(scales):
        cur_sample = torch.randn(batch_size, 1, cur_height, cur_width, device=base_tensor.device)
        cur_sample_scaled = F.interpolate(cur_sample, size=(height, width), mode=scale_mode, align_corners=align_corners)
        result.append(cur_sample_scaled)
        cur_height //= 2
        cur_width //= 2
    return torch.cat(result, dim=1)

class DefaultInpaintingTrainingModule(BaseInpaintingTrainingModule):

    def __init__(self, *args, concat_mask=True, rescale_scheduler_kwargs=None, image_to_discriminator='predicted_image', add_noise_kwargs=None, noise_fill_hole=False, const_area_crop_kwargs=None, distance_weighter_kwargs=None, distance_weighted_mask_for_discr=False, fake_fakes_proba=0, fake_fakes_generator_kwargs=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.concat_mask = concat_mask
        self.rescale_size_getter = get_ramp(**rescale_scheduler_kwargs) if rescale_scheduler_kwargs is not None else None
        self.image_to_discriminator = image_to_discriminator
        self.add_noise_kwargs = add_noise_kwargs
        self.noise_fill_hole = noise_fill_hole
        self.const_area_crop_kwargs = const_area_crop_kwargs
        self.refine_mask_for_losses = make_mask_distance_weighter(**distance_weighter_kwargs) if distance_weighter_kwargs is not None else None
        self.distance_weighted_mask_for_discr = distance_weighted_mask_for_discr
        self.fake_fakes_proba = fake_fakes_proba
        if self.fake_fakes_proba > 0.001:
            self.fake_fakes_gen = FakeFakesGenerator(**fake_fakes_generator_kwargs or {})

    def forward(self, batch):
        if self.training and self.rescale_size_getter is not None:
            cur_size = self.rescale_size_getter(self.global_step)
            batch['image'] = F.interpolate(batch['image'], size=cur_size, mode='bilinear', align_corners=False)
            batch['mask'] = F.interpolate(batch['mask'], size=cur_size, mode='nearest')
        if self.training and self.const_area_crop_kwargs is not None:
            batch = make_constant_area_crop_batch(batch, **self.const_area_crop_kwargs)
        img = batch['image']
        mask = batch['mask']
        masked_img = img * (1 - mask)
        if self.add_noise_kwargs is not None:
            noise = make_multiscale_noise(masked_img, **self.add_noise_kwargs)
            if self.noise_fill_hole:
                masked_img = masked_img + mask * noise[:, :masked_img.shape[1]]
            masked_img = torch.cat([masked_img, noise], dim=1)
        if self.concat_mask:
            masked_img = torch.cat([masked_img, mask], dim=1)
        batch['predicted_image'] = self.generator(masked_img)
        batch['inpainted'] = mask * batch['predicted_image'] + (1 - mask) * batch['image']
        if self.fake_fakes_proba > 0.001:
            if self.training and torch.rand(1).item() < self.fake_fakes_proba:
                batch['fake_fakes'], batch['fake_fakes_masks'] = self.fake_fakes_gen(img, mask)
                batch['use_fake_fakes'] = True
            else:
                batch['fake_fakes'] = torch.zeros_like(img)
                batch['fake_fakes_masks'] = torch.zeros_like(mask)
                batch['use_fake_fakes'] = False
        batch['mask_for_losses'] = self.refine_mask_for_losses(img, batch['predicted_image'], mask) if self.refine_mask_for_losses is not None and self.training else mask
        return batch

    def generator_loss(self, batch):
        img = batch['image']
        predicted_img = batch[self.image_to_discriminator]
        original_mask = batch['mask']
        supervised_mask = batch['mask_for_losses']
        l1_value = masked_l1_loss(predicted_img, img, supervised_mask, self.config.losses.l1.weight_known, self.config.losses.l1.weight_missing)
        total_loss = l1_value
        metrics = dict(gen_l1=l1_value)
        if self.config.losses.perceptual.weight > 0:
            pl_value = self.loss_pl(predicted_img, img, mask=supervised_mask).sum() * self.config.losses.perceptual.weight
            total_loss = total_loss + pl_value
            metrics['gen_pl'] = pl_value
        mask_for_discr = supervised_mask if self.distance_weighted_mask_for_discr else original_mask
        self.adversarial_loss.pre_generator_step(real_batch=img, fake_batch=predicted_img, generator=self.generator, discriminator=self.discriminator)
        discr_real_pred, discr_real_features = self.discriminator(img)
        discr_fake_pred, discr_fake_features = self.discriminator(predicted_img)
        adv_gen_loss, adv_metrics = self.adversarial_loss.generator_loss(real_batch=img, fake_batch=predicted_img, discr_real_pred=discr_real_pred, discr_fake_pred=discr_fake_pred, mask=mask_for_discr)
        total_loss = total_loss + adv_gen_loss
        metrics['gen_adv'] = adv_gen_loss
        metrics.update(add_prefix_to_keys(adv_metrics, 'adv_'))
        if self.config.losses.feature_matching.weight > 0:
            need_mask_in_fm = OmegaConf.to_container(self.config.losses.feature_matching).get('pass_mask', False)
            mask_for_fm = supervised_mask if need_mask_in_fm else None
            fm_value = feature_matching_loss(discr_fake_features, discr_real_features, mask=mask_for_fm) * self.config.losses.feature_matching.weight
            total_loss = total_loss + fm_value
            metrics['gen_fm'] = fm_value
        if self.loss_resnet_pl is not None:
            resnet_pl_value = self.loss_resnet_pl(predicted_img, img)
            total_loss = total_loss + resnet_pl_value
            metrics['gen_resnet_pl'] = resnet_pl_value
        return (total_loss, metrics)

    def discriminator_loss(self, batch):
        total_loss = 0
        metrics = {}
        predicted_img = batch[self.image_to_discriminator].detach()
        self.adversarial_loss.pre_discriminator_step(real_batch=batch['image'], fake_batch=predicted_img, generator=self.generator, discriminator=self.discriminator)
        discr_real_pred, discr_real_features = self.discriminator(batch['image'])
        discr_fake_pred, discr_fake_features = self.discriminator(predicted_img)
        adv_discr_loss, adv_metrics = self.adversarial_loss.discriminator_loss(real_batch=batch['image'], fake_batch=predicted_img, discr_real_pred=discr_real_pred, discr_fake_pred=discr_fake_pred, mask=batch['mask'])
        total_loss = total_loss + adv_discr_loss
        metrics['discr_adv'] = adv_discr_loss
        metrics.update(add_prefix_to_keys(adv_metrics, 'adv_'))
        if batch.get('use_fake_fakes', False):
            fake_fakes = batch['fake_fakes']
            self.adversarial_loss.pre_discriminator_step(real_batch=batch['image'], fake_batch=fake_fakes, generator=self.generator, discriminator=self.discriminator)
            discr_fake_fakes_pred, _ = self.discriminator(fake_fakes)
            fake_fakes_adv_discr_loss, fake_fakes_adv_metrics = self.adversarial_loss.discriminator_loss(real_batch=batch['image'], fake_batch=fake_fakes, discr_real_pred=discr_real_pred, discr_fake_pred=discr_fake_fakes_pred, mask=batch['mask'])
            total_loss = total_loss + fake_fakes_adv_discr_loss
            metrics['discr_adv_fake_fakes'] = fake_fakes_adv_discr_loss
            metrics.update(add_prefix_to_keys(fake_fakes_adv_metrics, 'adv_'))
        return (total_loss, metrics)

def forward(self, batch):
    if self.training and self.rescale_size_getter is not None:
        cur_size = self.rescale_size_getter(self.global_step)
        batch['image'] = F.interpolate(batch['image'], size=cur_size, mode='bilinear', align_corners=False)
        batch['mask'] = F.interpolate(batch['mask'], size=cur_size, mode='nearest')
    if self.training and self.const_area_crop_kwargs is not None:
        batch = make_constant_area_crop_batch(batch, **self.const_area_crop_kwargs)
    img = batch['image']
    mask = batch['mask']
    masked_img = img * (1 - mask)
    if self.add_noise_kwargs is not None:
        noise = make_multiscale_noise(masked_img, **self.add_noise_kwargs)
        if self.noise_fill_hole:
            masked_img = masked_img + mask * noise[:, :masked_img.shape[1]]
        masked_img = torch.cat([masked_img, noise], dim=1)
    if self.concat_mask:
        masked_img = torch.cat([masked_img, mask], dim=1)
    batch['predicted_image'] = self.generator(masked_img)
    batch['inpainted'] = mask * batch['predicted_image'] + (1 - mask) * batch['image']
    if self.fake_fakes_proba > 0.001:
        if self.training and torch.rand(1).item() < self.fake_fakes_proba:
            batch['fake_fakes'], batch['fake_fakes_masks'] = self.fake_fakes_gen(img, mask)
            batch['use_fake_fakes'] = True
        else:
            batch['fake_fakes'] = torch.zeros_like(img)
            batch['fake_fakes_masks'] = torch.zeros_like(mask)
            batch['use_fake_fakes'] = False
    batch['mask_for_losses'] = self.refine_mask_for_losses(img, batch['predicted_image'], mask) if self.refine_mask_for_losses is not None and self.training else mask
    return batch

class FourierUnit(nn.Module):

    def __init__(self, in_channels, out_channels, groups=1, spatial_scale_factor=None, spatial_scale_mode='bilinear', spectral_pos_encoding=False, use_se=False, se_kwargs=None, ffc3d=False, fft_norm='ortho'):
        super(FourierUnit, self).__init__()
        self.groups = groups
        self.conv_layer = torch.nn.Conv2d(in_channels=in_channels * 2 + (2 if spectral_pos_encoding else 0), out_channels=out_channels * 2, kernel_size=1, stride=1, padding=0, groups=self.groups, bias=False)
        self.bn = torch.nn.BatchNorm2d(out_channels * 2)
        self.relu = torch.nn.ReLU(inplace=True)
        self.use_se = use_se
        if use_se:
            if se_kwargs is None:
                se_kwargs = {}
            self.se = SELayer(self.conv_layer.in_channels, **se_kwargs)
        self.spatial_scale_factor = spatial_scale_factor
        self.spatial_scale_mode = spatial_scale_mode
        self.spectral_pos_encoding = spectral_pos_encoding
        self.ffc3d = ffc3d
        self.fft_norm = fft_norm

    def forward(self, x):
        batch = x.shape[0]
        if self.spatial_scale_factor is not None:
            orig_size = x.shape[-2:]
            x = F.interpolate(x, scale_factor=self.spatial_scale_factor, mode=self.spatial_scale_mode, align_corners=False)
        r_size = x.size()
        fft_dim = (-3, -2, -1) if self.ffc3d else (-2, -1)
        ffted = torch.fft.rfftn(x, dim=fft_dim, norm=self.fft_norm)
        ffted = torch.stack((ffted.real, ffted.imag), dim=-1)
        ffted = ffted.permute(0, 1, 4, 2, 3).contiguous()
        ffted = ffted.view((batch, -1) + ffted.size()[3:])
        if self.spectral_pos_encoding:
            height, width = ffted.shape[-2:]
            coords_vert = torch.linspace(0, 1, height)[None, None, :, None].expand(batch, 1, height, width).to(ffted)
            coords_hor = torch.linspace(0, 1, width)[None, None, None, :].expand(batch, 1, height, width).to(ffted)
            ffted = torch.cat((coords_vert, coords_hor, ffted), dim=1)
        if self.use_se:
            ffted = self.se(ffted)
        ffted = self.conv_layer(ffted)
        ffted = self.relu(self.bn(ffted))
        ffted = ffted.view((batch, -1, 2) + ffted.size()[2:]).permute(0, 1, 3, 4, 2).contiguous()
        ffted = torch.complex(ffted[..., 0], ffted[..., 1])
        ifft_shape_slice = x.shape[-3:] if self.ffc3d else x.shape[-2:]
        output = torch.fft.irfftn(ffted, s=ifft_shape_slice, dim=fft_dim, norm=self.fft_norm)
        if self.spatial_scale_factor is not None:
            output = F.interpolate(output, size=orig_size, mode=self.spatial_scale_mode, align_corners=False)
        return output

def forward(self, x):
    batch = x.shape[0]
    if self.spatial_scale_factor is not None:
        orig_size = x.shape[-2:]
        x = F.interpolate(x, scale_factor=self.spatial_scale_factor, mode=self.spatial_scale_mode, align_corners=False)
    r_size = x.size()
    fft_dim = (-3, -2, -1) if self.ffc3d else (-2, -1)
    ffted = torch.fft.rfftn(x, dim=fft_dim, norm=self.fft_norm)
    ffted = torch.stack((ffted.real, ffted.imag), dim=-1)
    ffted = ffted.permute(0, 1, 4, 2, 3).contiguous()
    ffted = ffted.view((batch, -1) + ffted.size()[3:])
    if self.spectral_pos_encoding:
        height, width = ffted.shape[-2:]
        coords_vert = torch.linspace(0, 1, height)[None, None, :, None].expand(batch, 1, height, width).to(ffted)
        coords_hor = torch.linspace(0, 1, width)[None, None, None, :].expand(batch, 1, height, width).to(ffted)
        ffted = torch.cat((coords_vert, coords_hor, ffted), dim=1)
    if self.use_se:
        ffted = self.se(ffted)
    ffted = self.conv_layer(ffted)
    ffted = self.relu(self.bn(ffted))
    ffted = ffted.view((batch, -1, 2) + ffted.size()[2:]).permute(0, 1, 3, 4, 2).contiguous()
    ffted = torch.complex(ffted[..., 0], ffted[..., 1])
    ifft_shape_slice = x.shape[-3:] if self.ffc3d else x.shape[-2:]
    output = torch.fft.irfftn(ffted, s=ifft_shape_slice, dim=fft_dim, norm=self.fft_norm)
    if self.spatial_scale_factor is not None:
        output = F.interpolate(output, size=orig_size, mode=self.spatial_scale_mode, align_corners=False)
    return output

class SELayer(nn.Module):

    def __init__(self, channel, reduction=16):
        super(SELayer, self).__init__()
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Sequential(nn.Linear(channel, channel // reduction, bias=False), nn.ReLU(inplace=True), nn.Linear(channel // reduction, channel, bias=False), nn.Sigmoid())

    def forward(self, x):
        b, c, _, _ = x.size()
        y = self.avg_pool(x).view(b, c)
        y = self.fc(y).view(b, c, 1, 1)
        res = x * y.expand_as(x)
        return res

def forward(self, x):
    b, c, _, _ = x.size()
    y = self.avg_pool(x).view(b, c)
    y = self.fc(y).view(b, c, 1, 1)
    res = x * y.expand_as(x)
    return res

class FakeFakesGenerator:

    def __init__(self, aug_proba=0.5, img_aug_degree=30, img_aug_translate=0.2):
        self.grad_aug = RandomAffine(degrees=360, translate=0.2, padding_mode=SamplePadding.REFLECTION, keepdim=False, p=1)
        self.img_aug = RandomAffine(degrees=img_aug_degree, translate=img_aug_translate, padding_mode=SamplePadding.REFLECTION, keepdim=True, p=1)
        self.aug_proba = aug_proba

    def __call__(self, input_images, masks):
        blend_masks = self._fill_masks_with_gradient(masks)
        blend_target = self._make_blend_target(input_images)
        result = input_images * (1 - blend_masks) + blend_target * blend_masks
        return (result, blend_masks)

    def _make_blend_target(self, input_images):
        batch_size = input_images.shape[0]
        permuted = input_images[torch.randperm(batch_size)]
        augmented = self.img_aug(input_images)
        is_aug = (torch.rand(batch_size, device=input_images.device)[:, None, None, None] < self.aug_proba).float()
        result = augmented * is_aug + permuted * (1 - is_aug)
        return result

    def _fill_masks_with_gradient(self, masks):
        batch_size, _, height, width = masks.shape
        grad = torch.linspace(0, 1, steps=width * 2, device=masks.device, dtype=masks.dtype).view(1, 1, 1, -1).expand(batch_size, 1, height * 2, width * 2)
        grad = self.grad_aug(grad)
        grad = CenterCrop((height, width))(grad)
        grad *= masks
        grad_for_min = grad + (1 - masks) * 10
        grad -= grad_for_min.view(batch_size, -1).min(-1).values[:, None, None, None]
        grad /= grad.view(batch_size, -1).max(-1).values[:, None, None, None] + 1e-06
        grad.clamp_(min=0, max=1)
        return grad

def _fill_masks_with_gradient(self, masks):
    batch_size, _, height, width = masks.shape
    grad = torch.linspace(0, 1, steps=width * 2, device=masks.device, dtype=masks.dtype).view(1, 1, 1, -1).expand(batch_size, 1, height * 2, width * 2)
    grad = self.grad_aug(grad)
    grad = CenterCrop((height, width))(grad)
    grad *= masks
    grad_for_min = grad + (1 - masks) * 10
    grad -= grad_for_min.view(batch_size, -1).min(-1).values[:, None, None, None]
    grad /= grad.view(batch_size, -1).max(-1).values[:, None, None, None] + 1e-06
    grad.clamp_(min=0, max=1)
    return grad

def pad_img_to_modulo(img, mod):
    channels, height, width = img.shape
    out_height = ceil_modulo(height, mod)
    out_width = ceil_modulo(width, mod)
    return np.pad(img, ((0, 0), (0, out_height - height), (0, out_width - width)), mode='symmetric')

def pad_tensor_to_modulo(img, mod):
    batch_size, channels, height, width = img.shape
    out_height = ceil_modulo(height, mod)
    out_width = ceil_modulo(width, mod)
    return F.pad(img, pad=(0, out_width - width, 0, out_height - height), mode='reflect')

def _pyrdown(im: torch.Tensor, downsize: tuple=None):
    """downscale the image"""
    if downsize is None:
        downsize = (im.shape[2] // 2, im.shape[3] // 2)
    assert im.shape[1] == 3, 'Expected shape for the input to be (n,3,height,width)'
    im = gaussian_blur2d(im, kernel_size=(5, 5), sigma=(1.0, 1.0))
    im = F.interpolate(im, size=downsize, mode='bilinear', align_corners=False)
    return im

def _pyrdown_mask(mask: torch.Tensor, downsize: tuple=None, eps: float=1e-08, blur_mask: bool=True, round_up: bool=True):
    """downscale the mask tensor

    Parameters
    ----------
    mask : torch.Tensor
        mask of size (B, 1, H, W)
    downsize : tuple, optional
        size to downscale to. If None, image is downscaled to half, by default None
    eps : float, optional
        threshold value for binarizing the mask, by default 1e-8
    blur_mask : bool, optional
        if True, apply gaussian filter before downscaling, by default True
    round_up : bool, optional
        if True, values above eps are marked 1, else, values below 1-eps are marked 0, by default True

    Returns
    -------
    torch.Tensor
        downscaled mask
    """
    if downsize is None:
        downsize = (mask.shape[2] // 2, mask.shape[3] // 2)
    assert mask.shape[1] == 1, 'Expected shape for the input to be (n,1,height,width)'
    if blur_mask == True:
        mask = gaussian_blur2d(mask, kernel_size=(5, 5), sigma=(1.0, 1.0))
        mask = F.interpolate(mask, size=downsize, mode='bilinear', align_corners=False)
    else:
        mask = F.interpolate(mask, size=downsize, mode='bilinear', align_corners=False)
    if round_up:
        mask[mask >= eps] = 1
        mask[mask < eps] = 0
    else:
        mask[mask >= 1.0 - eps] = 1
        mask[mask < 1.0 - eps] = 0
    return mask

def ssim_fid100_f1(metrics, fid_scale=100):
    ssim = metrics['ssim', 'total']['mean']
    fid = metrics['fid', 'total']['mean']
    fid_rel = max(0, fid_scale - fid) / fid_scale
    f1 = 2 * ssim * fid_rel / (ssim + fid_rel + 0.001)
    return f1

def lpips_fid100_f1(metrics, fid_scale=100):
    neg_lpips = 1 - metrics['lpips', 'total']['mean']
    fid = metrics['fid', 'total']['mean']
    fid_rel = max(0, fid_scale - fid) / fid_scale
    f1 = 2 * neg_lpips * fid_rel / (neg_lpips + fid_rel + 0.001)
    return f1

class InpaintingEvaluatorOnline(nn.Module):

    def __init__(self, scores, bins=10, image_key='image', inpainted_key='inpainted', integral_func=None, integral_title=None, clamp_image_range=None):
        """
        :param scores: dict {score_name: EvaluatorScore object}
        :param bins: number of groups, partition is generated by np.linspace(0., 1., bins + 1)
        :param device: device to use
        """
        super().__init__()
        LOGGER.info(f'{type(self)} init called')
        self.scores = nn.ModuleDict(scores)
        self.image_key = image_key
        self.inpainted_key = inpainted_key
        self.bins_num = bins
        self.bin_edges = np.linspace(0, 1, self.bins_num + 1)
        num_digits = max(0, math.ceil(math.log10(self.bins_num)) - 1)
        self.interval_names = []
        for idx_bin in range(self.bins_num):
            start_percent, end_percent = (round(100 * self.bin_edges[idx_bin], num_digits), round(100 * self.bin_edges[idx_bin + 1], num_digits))
            start_percent = '{:.{n}f}'.format(start_percent, n=num_digits)
            end_percent = '{:.{n}f}'.format(end_percent, n=num_digits)
            self.interval_names.append('{0}-{1}%'.format(start_percent, end_percent))
        self.groups = []
        self.integral_func = integral_func
        self.integral_title = integral_title
        self.clamp_image_range = clamp_image_range
        LOGGER.info(f'{type(self)} init done')

    def _get_bins(self, mask_batch):
        batch_size = mask_batch.shape[0]
        area = mask_batch.view(batch_size, -1).mean(dim=-1).detach().cpu().numpy()
        bin_indices = np.clip(np.searchsorted(self.bin_edges, area) - 1, 0, self.bins_num - 1)
        return bin_indices

    def forward(self, batch: Dict[str, torch.Tensor]):
        """
        Calculate and accumulate metrics for batch. To finalize evaluation and obtain final metrics, call evaluation_end
        :param batch: batch dict with mandatory fields mask, image, inpainted (can be overriden by self.inpainted_key)
        """
        result = {}
        with torch.no_grad():
            image_batch, mask_batch, inpainted_batch = (batch[self.image_key], batch['mask'], batch[self.inpainted_key])
            if self.clamp_image_range is not None:
                image_batch = torch.clamp(image_batch, min=self.clamp_image_range[0], max=self.clamp_image_range[1])
            self.groups.extend(self._get_bins(mask_batch))
            for score_name, score in self.scores.items():
                result[score_name] = score(inpainted_batch, image_batch, mask_batch)
        return result

    def process_batch(self, batch: Dict[str, torch.Tensor]):
        return self(batch)

    def evaluation_end(self, states=None):
        """:return: dict with (score_name, group_type) as keys, where group_type can be either 'overall' or
            name of the particular group arranged by area of mask (e.g. '10-20%')
            and score statistics for the group as values.
        """
        LOGGER.info(f'{type(self)}: evaluation_end called')
        self.groups = np.array(self.groups)
        results = {}
        for score_name, score in self.scores.items():
            LOGGER.info(f'Getting value of {score_name}')
            cur_states = [s[score_name] for s in states] if states is not None else None
            total_results, group_results = score.get_value(groups=self.groups, states=cur_states)
            LOGGER.info(f'Getting value of {score_name} done')
            results[score_name, 'total'] = total_results
            for group_index, group_values in group_results.items():
                group_name = self.interval_names[group_index]
                results[score_name, group_name] = group_values
        if self.integral_func is not None:
            results[self.integral_title, 'total'] = dict(mean=self.integral_func(results))
        LOGGER.info(f'{type(self)}: reset scores')
        self.groups = []
        for sc in self.scores.values():
            sc.reset()
        LOGGER.info(f'{type(self)}: reset scores done')
        LOGGER.info(f'{type(self)}: evaluation_end done')
        return results

def forward(self, batch: Dict[str, torch.Tensor]):
    """
        Calculate and accumulate metrics for batch. To finalize evaluation and obtain final metrics, call evaluation_end
        :param batch: batch dict with mandatory fields mask, image, inpainted (can be overriden by self.inpainted_key)
        """
    result = {}
    with torch.no_grad():
        image_batch, mask_batch, inpainted_batch = (batch[self.image_key], batch['mask'], batch[self.inpainted_key])
        if self.clamp_image_range is not None:
            image_batch = torch.clamp(image_batch, min=self.clamp_image_range[0], max=self.clamp_image_range[1])
        self.groups.extend(self._get_bins(mask_batch))
        for score_name, score in self.scores.items():
            result[score_name] = score(inpainted_batch, image_batch, mask_batch)
    return result

class FIDScore(EvaluatorScore):

    def __init__(self, dims=2048, eps=1e-06):
        LOGGER.info('FIDscore init called')
        super().__init__()
        if getattr(FIDScore, '_MODEL', None) is None:
            block_idx = InceptionV3.BLOCK_INDEX_BY_DIM[dims]
            FIDScore._MODEL = InceptionV3([block_idx]).eval()
        self.model = FIDScore._MODEL
        self.eps = eps
        self.reset()
        LOGGER.info('FIDscore init done')

    def forward(self, pred_batch, target_batch, mask=None):
        activations_pred = self._get_activations(pred_batch)
        activations_target = self._get_activations(target_batch)
        self.activations_pred.append(activations_pred.detach().cpu())
        self.activations_target.append(activations_target.detach().cpu())
        return (activations_pred, activations_target)

    def get_value(self, groups=None, states=None):
        LOGGER.info('FIDscore get_value called')
        activations_pred, activations_target = zip(*states) if states is not None else (self.activations_pred, self.activations_target)
        activations_pred = torch.cat(activations_pred).cpu().numpy()
        activations_target = torch.cat(activations_target).cpu().numpy()
        total_distance = calculate_frechet_distance(activations_pred, activations_target, eps=self.eps)
        total_results = dict(mean=total_distance)
        if groups is None:
            group_results = None
        else:
            group_results = dict()
            grouping = get_groupings(groups)
            for label, index in grouping.items():
                if len(index) > 1:
                    group_distance = calculate_frechet_distance(activations_pred[index], activations_target[index], eps=self.eps)
                    group_results[label] = dict(mean=group_distance)
                else:
                    group_results[label] = dict(mean=float('nan'))
        self.reset()
        LOGGER.info('FIDscore get_value done')
        return (total_results, group_results)

    def reset(self):
        self.activations_pred = []
        self.activations_target = []

    def _get_activations(self, batch):
        activations = self.model(batch)[0]
        if activations.shape[2] != 1 or activations.shape[3] != 1:
            assert False, 'We should not have got here, because Inception always scales inputs to 299x299'
        activations = activations.squeeze(-1).squeeze(-1)
        return activations

def _get_activations(self, batch):
    activations = self.model(batch)[0]
    if activations.shape[2] != 1 or activations.shape[3] != 1:
        assert False, 'We should not have got here, because Inception always scales inputs to 299x299'
    activations = activations.squeeze(-1).squeeze(-1)
    return activations

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

def _create_window(self, window_size, channel):
    _1D_window = self._gaussian(window_size, 1.5).unsqueeze(1)
    _2D_window = _1D_window.mm(_1D_window.t()).float().unsqueeze(0).unsqueeze(0)
    return _2D_window.expand(channel, 1, window_size, window_size).contiguous()

def voc_ap(rec, prec, use_07_metric=False):
    """ ap = voc_ap(rec, prec, [use_07_metric])
    Compute VOC AP given precision and recall.
    If use_07_metric is true, uses the
    VOC 07 11 point method (default:False).
    """
    if use_07_metric:
        ap = 0.0
        for t in np.arange(0.0, 1.1, 0.1):
            if np.sum(rec >= t) == 0:
                p = 0
            else:
                p = np.max(prec[rec >= t])
            ap = ap + p / 11.0
    else:
        mrec = np.concatenate(([0.0], rec, [1.0]))
        mpre = np.concatenate(([0.0], prec, [0.0]))
        for i in range(mpre.size - 1, 0, -1):
            mpre[i - 1] = np.maximum(mpre[i - 1], mpre[i])
        i = np.where(mrec[1:] != mrec[:-1])[0]
        ap = np.sum((mrec[i + 1] - mrec[i]) * mpre[i + 1])
    return ap

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

def clamp_weights(self):
    for module in self.net.modules():
        if hasattr(module, 'weight') and module.kernel_size == (1, 1):
            module.weight.data = torch.clamp(module.weight.data, min=0)

class InceptionV3(nn.Module):
    """Pretrained InceptionV3 network returning feature maps"""
    DEFAULT_BLOCK_INDEX = 3
    BLOCK_INDEX_BY_DIM = {64: 0, 192: 1, 768: 2, 2048: 3}

    def __init__(self, output_blocks=[DEFAULT_BLOCK_INDEX], resize_input=True, normalize_input=True, requires_grad=False, use_fid_inception=True):
        """Build pretrained InceptionV3

        Parameters
        ----------
        output_blocks : list of int
            Indices of blocks to return features of. Possible values are:
                - 0: corresponds to output of first max pooling
                - 1: corresponds to output of second max pooling
                - 2: corresponds to output which is fed to aux classifier
                - 3: corresponds to output of final average pooling
        resize_input : bool
            If true, bilinearly resizes input to width and height 299 before
            feeding input to model. As the network without fully connected
            layers is fully convolutional, it should be able to handle inputs
            of arbitrary size, so resizing might not be strictly needed
        normalize_input : bool
            If true, scales the input from range (0, 1) to the range the
            pretrained Inception network expects, namely (-1, 1)
        requires_grad : bool
            If true, parameters of the model require gradients. Possibly useful
            for finetuning the network
        use_fid_inception : bool
            If true, uses the pretrained Inception model used in Tensorflow's
            FID implementation. If false, uses the pretrained Inception model
            available in torchvision. The FID Inception model has different
            weights and a slightly different structure from torchvision's
            Inception model. If you want to compute FID scores, you are
            strongly advised to set this parameter to true to get comparable
            results.
        """
        super(InceptionV3, self).__init__()
        self.resize_input = resize_input
        self.normalize_input = normalize_input
        self.output_blocks = sorted(output_blocks)
        self.last_needed_block = max(output_blocks)
        assert self.last_needed_block <= 3, 'Last possible output block index is 3'
        self.blocks = nn.ModuleList()
        if use_fid_inception:
            inception = fid_inception_v3()
        else:
            inception = models.inception_v3(pretrained=True)
        block0 = [inception.Conv2d_1a_3x3, inception.Conv2d_2a_3x3, inception.Conv2d_2b_3x3, nn.MaxPool2d(kernel_size=3, stride=2)]
        self.blocks.append(nn.Sequential(*block0))
        if self.last_needed_block >= 1:
            block1 = [inception.Conv2d_3b_1x1, inception.Conv2d_4a_3x3, nn.MaxPool2d(kernel_size=3, stride=2)]
            self.blocks.append(nn.Sequential(*block1))
        if self.last_needed_block >= 2:
            block2 = [inception.Mixed_5b, inception.Mixed_5c, inception.Mixed_5d, inception.Mixed_6a, inception.Mixed_6b, inception.Mixed_6c, inception.Mixed_6d, inception.Mixed_6e]
            self.blocks.append(nn.Sequential(*block2))
        if self.last_needed_block >= 3:
            block3 = [inception.Mixed_7a, inception.Mixed_7b, inception.Mixed_7c, nn.AdaptiveAvgPool2d(output_size=(1, 1))]
            self.blocks.append(nn.Sequential(*block3))
        for param in self.parameters():
            param.requires_grad = requires_grad

    def forward(self, inp):
        """Get Inception feature maps

        Parameters
        ----------
        inp : torch.autograd.Variable
            Input tensor of shape Bx3xHxW. Values are expected to be in
            range (0, 1)

        Returns
        -------
        List of torch.autograd.Variable, corresponding to the selected output
        block, sorted ascending by index
        """
        outp = []
        x = inp
        if self.resize_input:
            x = F.interpolate(x, size=(299, 299), mode='bilinear', align_corners=False)
        if self.normalize_input:
            x = 2 * x - 1
        for idx, block in enumerate(self.blocks):
            x = block(x)
            if idx in self.output_blocks:
                outp.append(x)
            if idx == self.last_needed_block:
                break
        return outp

def forward(self, inp):
    """Get Inception feature maps

        Parameters
        ----------
        inp : torch.autograd.Variable
            Input tensor of shape Bx3xHxW. Values are expected to be in
            range (0, 1)

        Returns
        -------
        List of torch.autograd.Variable, corresponding to the selected output
        block, sorted ascending by index
        """
    outp = []
    x = inp
    if self.resize_input:
        x = F.interpolate(x, size=(299, 299), mode='bilinear', align_corners=False)
    if self.normalize_input:
        x = 2 * x - 1
    for idx, block in enumerate(self.blocks):
        x = block(x)
        if idx in self.output_blocks:
            outp.append(x)
        if idx == self.last_needed_block:
            break
    return outp

def propose_random_square_crop(mask, min_overlap=0.5):
    height, width = mask.shape
    mask_ys, mask_xs = np.where(mask > 0.5)
    if height < width:
        crop_size = height
        obj_left, obj_right = (mask_xs.min(), mask_xs.max())
        obj_width = obj_right - obj_left
        left_border = max(0, min(width - crop_size - 1, obj_left + obj_width * min_overlap - crop_size))
        right_border = max(left_border + 1, min(width - crop_size, obj_left + obj_width * min_overlap))
        start_x = np.random.randint(left_border, right_border)
        return (start_x, 0, start_x + crop_size, height)
    else:
        crop_size = width
        obj_top, obj_bottom = (mask_ys.min(), mask_ys.max())
        obj_height = obj_bottom - obj_top
        top_border = max(0, min(height - crop_size - 1, obj_top + obj_height * min_overlap - crop_size))
        bottom_border = max(top_border + 1, min(height - crop_size, obj_top + obj_height * min_overlap))
        start_y = np.random.randint(top_border, bottom_border)
        return (0, start_y, width, start_y + crop_size)

class InvertedResidual(nn.Module):

    def __init__(self, inp, oup, stride, expand_ratio):
        super(InvertedResidual, self).__init__()
        self.stride = stride
        assert stride in [1, 2]
        hidden_dim = round(inp * expand_ratio)
        self.use_res_connect = self.stride == 1 and inp == oup
        if expand_ratio == 1:
            self.conv = nn.Sequential(nn.Conv2d(hidden_dim, hidden_dim, 3, stride, 1, groups=hidden_dim, bias=False), BatchNorm2d(hidden_dim), nn.ReLU6(inplace=True), nn.Conv2d(hidden_dim, oup, 1, 1, 0, bias=False), BatchNorm2d(oup))
        else:
            self.conv = nn.Sequential(nn.Conv2d(inp, hidden_dim, 1, 1, 0, bias=False), BatchNorm2d(hidden_dim), nn.ReLU6(inplace=True), nn.Conv2d(hidden_dim, hidden_dim, 3, stride, 1, groups=hidden_dim, bias=False), BatchNorm2d(hidden_dim), nn.ReLU6(inplace=True), nn.Conv2d(hidden_dim, oup, 1, 1, 0, bias=False), BatchNorm2d(oup))

    def forward(self, x):
        if self.use_res_connect:
            return x + self.conv(x)
        else:
            return self.conv(x)

def forward(self, x):
    if self.use_res_connect:
        return x + self.conv(x)
    else:
        return self.conv(x)

class SegmentationModule(nn.Module):

    def __init__(self, weights_path, num_classes=150, arch_encoder='resnet50dilated', drop_last_conv=False, net_enc=None, net_dec=None, encode=None, use_default_normalization=False, return_feature_maps=False, return_feature_maps_level=3, return_feature_maps_only=True, **kwargs):
        super().__init__()
        self.weights_path = weights_path
        self.drop_last_conv = drop_last_conv
        self.arch_encoder = arch_encoder
        if self.arch_encoder == 'resnet50dilated':
            self.arch_decoder = 'ppm_deepsup'
            self.fc_dim = 2048
        elif self.arch_encoder == 'mobilenetv2dilated':
            self.arch_decoder = 'c1_deepsup'
            self.fc_dim = 320
        else:
            raise NotImplementedError(f'No such arch_encoder={self.arch_encoder}')
        model_builder_kwargs = dict(arch_encoder=self.arch_encoder, arch_decoder=self.arch_decoder, fc_dim=self.fc_dim, drop_last_conv=drop_last_conv, weights_path=self.weights_path)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.encoder = ModelBuilder.get_encoder(**model_builder_kwargs) if net_enc is None else net_enc
        self.decoder = ModelBuilder.get_decoder(**model_builder_kwargs) if net_dec is None else net_dec
        self.use_default_normalization = use_default_normalization
        self.default_normalization = NormalizeTensor(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        self.encode = encode
        self.return_feature_maps = return_feature_maps
        assert 0 <= return_feature_maps_level <= 3
        self.return_feature_maps_level = return_feature_maps_level

    def normalize_input(self, tensor):
        if tensor.min() < 0 or tensor.max() > 1:
            raise ValueError('Tensor should be 0..1 before using normalize_input')
        return self.default_normalization(tensor)

    @property
    def feature_maps_channels(self):
        return 256 * 2 ** self.return_feature_maps_level

    def forward(self, img_data, segSize=None):
        if segSize is None:
            raise NotImplementedError('Please pass segSize param. By default: (300, 300)')
        fmaps = self.encoder(img_data, return_feature_maps=True)
        pred = self.decoder(fmaps, segSize=segSize)
        if self.return_feature_maps:
            return (pred, fmaps)
        return pred

    def multi_mask_from_multiclass(self, pred, classes):

        def isin(ar1, ar2):
            return (ar1[..., None] == ar2).any(-1).float()
        return isin(pred, torch.LongTensor(classes).to(self.device))

    @staticmethod
    def multi_mask_from_multiclass_probs(scores, classes):
        res = None
        for c in classes:
            if res is None:
                res = scores[:, c]
            else:
                res += scores[:, c]
        return res

    def predict(self, tensor, imgSizes=(-1,), segSize=None):
        """Entry-point for segmentation. Use this methods instead of forward
        Arguments:
            tensor {torch.Tensor} -- BCHW
        Keyword Arguments:
            imgSizes {tuple or list} -- imgSizes for segmentation input.
                default: (300, 450)
                original implementation: (300, 375, 450, 525, 600)

        """
        if segSize is None:
            segSize = tensor.shape[-2:]
        segSize = (tensor.shape[2], tensor.shape[3])
        with torch.no_grad():
            if self.use_default_normalization:
                tensor = self.normalize_input(tensor)
            scores = torch.zeros(1, NUM_CLASS, segSize[0], segSize[1]).to(self.device)
            features = torch.zeros(1, self.feature_maps_channels, segSize[0], segSize[1]).to(self.device)
            result = []
            for img_size in imgSizes:
                if img_size != -1:
                    img_data = F.interpolate(tensor.clone(), size=img_size)
                else:
                    img_data = tensor.clone()
                if self.return_feature_maps:
                    pred_current, fmaps = self.forward(img_data, segSize=segSize)
                else:
                    pred_current = self.forward(img_data, segSize=segSize)
                result.append(pred_current)
                scores = scores + pred_current / len(imgSizes)
                if self.return_feature_maps:
                    features = features + F.interpolate(fmaps[self.return_feature_maps_level], size=segSize) / len(imgSizes)
            _, pred = torch.max(scores, dim=1)
            if self.return_feature_maps:
                return features
            return (pred, result)

    def get_edges(self, t):
        edge = torch.cuda.ByteTensor(t.size()).zero_()
        edge[:, :, :, 1:] = edge[:, :, :, 1:] | (t[:, :, :, 1:] != t[:, :, :, :-1])
        edge[:, :, :, :-1] = edge[:, :, :, :-1] | (t[:, :, :, 1:] != t[:, :, :, :-1])
        edge[:, :, 1:, :] = edge[:, :, 1:, :] | (t[:, :, 1:, :] != t[:, :, :-1, :])
        edge[:, :, :-1, :] = edge[:, :, :-1, :] | (t[:, :, 1:, :] != t[:, :, :-1, :])
        if True:
            return edge.half()
        return edge.float()

def get_edges(self, t):
    edge = torch.cuda.ByteTensor(t.size()).zero_()
    edge[:, :, :, 1:] = edge[:, :, :, 1:] | (t[:, :, :, 1:] != t[:, :, :, :-1])
    edge[:, :, :, :-1] = edge[:, :, :, :-1] | (t[:, :, :, 1:] != t[:, :, :, :-1])
    edge[:, :, 1:, :] = edge[:, :, 1:, :] | (t[:, :, 1:, :] != t[:, :, :-1, :])
    edge[:, :, :-1, :] = edge[:, :, :-1, :] | (t[:, :, 1:, :] != t[:, :, :-1, :])
    if True:
        return edge.half()
    return edge.float()

class PPMDeepsup(nn.Module):

    def __init__(self, num_class=NUM_CLASS, fc_dim=4096, use_softmax=False, pool_scales=(1, 2, 3, 6), drop_last_conv=False):
        super().__init__()
        self.use_softmax = use_softmax
        self.drop_last_conv = drop_last_conv
        self.ppm = []
        for scale in pool_scales:
            self.ppm.append(nn.Sequential(nn.AdaptiveAvgPool2d(scale), nn.Conv2d(fc_dim, 512, kernel_size=1, bias=False), BatchNorm2d(512), nn.ReLU(inplace=True)))
        self.ppm = nn.ModuleList(self.ppm)
        self.cbr_deepsup = conv3x3_bn_relu(fc_dim // 2, fc_dim // 4, 1)
        self.conv_last = nn.Sequential(nn.Conv2d(fc_dim + len(pool_scales) * 512, 512, kernel_size=3, padding=1, bias=False), BatchNorm2d(512), nn.ReLU(inplace=True), nn.Dropout2d(0.1), nn.Conv2d(512, num_class, kernel_size=1))
        self.conv_last_deepsup = nn.Conv2d(fc_dim // 4, num_class, 1, 1, 0)
        self.dropout_deepsup = nn.Dropout2d(0.1)

    def forward(self, conv_out, segSize=None):
        conv5 = conv_out[-1]
        input_size = conv5.size()
        ppm_out = [conv5]
        for pool_scale in self.ppm:
            ppm_out.append(nn.functional.interpolate(pool_scale(conv5), (input_size[2], input_size[3]), mode='bilinear', align_corners=False))
        ppm_out = torch.cat(ppm_out, 1)
        if self.drop_last_conv:
            return ppm_out
        else:
            x = self.conv_last(ppm_out)
            if self.use_softmax:
                x = nn.functional.interpolate(x, size=segSize, mode='bilinear', align_corners=False)
                x = nn.functional.softmax(x, dim=1)
                return x
            conv4 = conv_out[-2]
            _ = self.cbr_deepsup(conv4)
            _ = self.dropout_deepsup(_)
            _ = self.conv_last_deepsup(_)
            x = nn.functional.log_softmax(x, dim=1)
            _ = nn.functional.log_softmax(_, dim=1)
            return (x, _)

def forward(self, conv_out, segSize=None):
    conv5 = conv_out[-1]
    input_size = conv5.size()
    ppm_out = [conv5]
    for pool_scale in self.ppm:
        ppm_out.append(nn.functional.interpolate(pool_scale(conv5), (input_size[2], input_size[3]), mode='bilinear', align_corners=False))
    ppm_out = torch.cat(ppm_out, 1)
    if self.drop_last_conv:
        return ppm_out
    else:
        x = self.conv_last(ppm_out)
        if self.use_softmax:
            x = nn.functional.interpolate(x, size=segSize, mode='bilinear', align_corners=False)
            x = nn.functional.softmax(x, dim=1)
            return x
        conv4 = conv_out[-2]
        _ = self.cbr_deepsup(conv4)
        _ = self.dropout_deepsup(_)
        _ = self.conv_last_deepsup(_)
        x = nn.functional.log_softmax(x, dim=1)
        _ = nn.functional.log_softmax(_, dim=1)
        return (x, _)

class C1DeepSup(nn.Module):

    def __init__(self, num_class=150, fc_dim=2048, use_softmax=False, drop_last_conv=False):
        super(C1DeepSup, self).__init__()
        self.use_softmax = use_softmax
        self.drop_last_conv = drop_last_conv
        self.cbr = conv3x3_bn_relu(fc_dim, fc_dim // 4, 1)
        self.cbr_deepsup = conv3x3_bn_relu(fc_dim // 2, fc_dim // 4, 1)
        self.conv_last = nn.Conv2d(fc_dim // 4, num_class, 1, 1, 0)
        self.conv_last_deepsup = nn.Conv2d(fc_dim // 4, num_class, 1, 1, 0)

    def forward(self, conv_out, segSize=None):
        conv5 = conv_out[-1]
        x = self.cbr(conv5)
        if self.drop_last_conv:
            return x
        else:
            x = self.conv_last(x)
            if self.use_softmax:
                x = nn.functional.interpolate(x, size=segSize, mode='bilinear', align_corners=False)
                x = nn.functional.softmax(x, dim=1)
                return x
            conv4 = conv_out[-2]
            _ = self.cbr_deepsup(conv4)
            _ = self.conv_last_deepsup(_)
            x = nn.functional.log_softmax(x, dim=1)
            _ = nn.functional.log_softmax(_, dim=1)
            return (x, _)

def forward(self, conv_out, segSize=None):
    conv5 = conv_out[-1]
    x = self.cbr(conv5)
    if self.drop_last_conv:
        return x
    else:
        x = self.conv_last(x)
        if self.use_softmax:
            x = nn.functional.interpolate(x, size=segSize, mode='bilinear', align_corners=False)
            x = nn.functional.softmax(x, dim=1)
            return x
        conv4 = conv_out[-2]
        _ = self.cbr_deepsup(conv4)
        _ = self.conv_last_deepsup(_)
        x = nn.functional.log_softmax(x, dim=1)
        _ = nn.functional.log_softmax(_, dim=1)
        return (x, _)

class C1(nn.Module):

    def __init__(self, num_class=150, fc_dim=2048, use_softmax=False):
        super(C1, self).__init__()
        self.use_softmax = use_softmax
        self.cbr = conv3x3_bn_relu(fc_dim, fc_dim // 4, 1)
        self.conv_last = nn.Conv2d(fc_dim // 4, num_class, 1, 1, 0)

    def forward(self, conv_out, segSize=None):
        conv5 = conv_out[-1]
        x = self.cbr(conv5)
        x = self.conv_last(x)
        if self.use_softmax:
            x = nn.functional.interpolate(x, size=segSize, mode='bilinear', align_corners=False)
            x = nn.functional.softmax(x, dim=1)
        else:
            x = nn.functional.log_softmax(x, dim=1)
        return x

def forward(self, conv_out, segSize=None):
    conv5 = conv_out[-1]
    x = self.cbr(conv5)
    x = self.conv_last(x)
    if self.use_softmax:
        x = nn.functional.interpolate(x, size=segSize, mode='bilinear', align_corners=False)
        x = nn.functional.softmax(x, dim=1)
    else:
        x = nn.functional.log_softmax(x, dim=1)
    return x

class PPM(nn.Module):

    def __init__(self, num_class=150, fc_dim=4096, use_softmax=False, pool_scales=(1, 2, 3, 6)):
        super(PPM, self).__init__()
        self.use_softmax = use_softmax
        self.ppm = []
        for scale in pool_scales:
            self.ppm.append(nn.Sequential(nn.AdaptiveAvgPool2d(scale), nn.Conv2d(fc_dim, 512, kernel_size=1, bias=False), BatchNorm2d(512), nn.ReLU(inplace=True)))
        self.ppm = nn.ModuleList(self.ppm)
        self.conv_last = nn.Sequential(nn.Conv2d(fc_dim + len(pool_scales) * 512, 512, kernel_size=3, padding=1, bias=False), BatchNorm2d(512), nn.ReLU(inplace=True), nn.Dropout2d(0.1), nn.Conv2d(512, num_class, kernel_size=1))

    def forward(self, conv_out, segSize=None):
        conv5 = conv_out[-1]
        input_size = conv5.size()
        ppm_out = [conv5]
        for pool_scale in self.ppm:
            ppm_out.append(nn.functional.interpolate(pool_scale(conv5), (input_size[2], input_size[3]), mode='bilinear', align_corners=False))
        ppm_out = torch.cat(ppm_out, 1)
        x = self.conv_last(ppm_out)
        if self.use_softmax:
            x = nn.functional.interpolate(x, size=segSize, mode='bilinear', align_corners=False)
            x = nn.functional.softmax(x, dim=1)
        else:
            x = nn.functional.log_softmax(x, dim=1)
        return x

def forward(self, conv_out, segSize=None):
    conv5 = conv_out[-1]
    input_size = conv5.size()
    ppm_out = [conv5]
    for pool_scale in self.ppm:
        ppm_out.append(nn.functional.interpolate(pool_scale(conv5), (input_size[2], input_size[3]), mode='bilinear', align_corners=False))
    ppm_out = torch.cat(ppm_out, 1)
    x = self.conv_last(ppm_out)
    if self.use_softmax:
        x = nn.functional.interpolate(x, size=segSize, mode='bilinear', align_corners=False)
        x = nn.functional.softmax(x, dim=1)
    else:
        x = nn.functional.log_softmax(x, dim=1)
    return x

def _unsqueeze_ft(tensor):
    """add new dementions at the front and the tail"""
    return tensor.unsqueeze(0).unsqueeze(-1)

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

def transform_image_to_crop(box_in: torch.Tensor, box_extract: torch.Tensor, resize_factor: float, crop_sz: torch.Tensor, normalize=False) -> torch.Tensor:
    """ Transform the box co-ordinates from the original image co-ordinates to the co-ordinates of the cropped image
    args:
        box_in - the box for which the co-ordinates are to be transformed
        box_extract - the box about which the image crop has been extracted.
        resize_factor - the ratio between the original image scale and the scale of the image crop
        crop_sz - size of the cropped image

    returns:
        torch.Tensor - transformed co-ordinates of box_in
    """
    box_extract_center = box_extract[0:2] + 0.5 * box_extract[2:4]
    box_in_center = box_in[0:2] + 0.5 * box_in[2:4]
    box_out_center = (crop_sz - 1) / 2 + (box_in_center - box_extract_center) * resize_factor
    box_out_wh = box_in[2:4] * resize_factor
    box_out = torch.cat((box_out_center - 0.5 * box_out_wh, box_out_wh))
    if normalize:
        return box_out / crop_sz[0]
    else:
        return box_out

def box_iou(boxes1, boxes2):
    """

    :param boxes1: (N, 4) (x1,y1,x2,y2)
    :param boxes2: (N, 4) (x1,y1,x2,y2)
    :return:
    """
    area1 = box_area(boxes1)
    area2 = box_area(boxes2)
    lt = torch.max(boxes1[:, :2], boxes2[:, :2])
    rb = torch.min(boxes1[:, 2:], boxes2[:, 2:])
    wh = (rb - lt).clamp(min=0)
    inter = wh[:, 0] * wh[:, 1]
    union = area1 + area2 - inter
    iou = inter / union
    return (iou, union)

def generalized_box_iou(boxes1, boxes2):
    """
    Generalized IoU from https://giou.stanford.edu/

    The boxes should be in [x0, y0, x1, y1] format

    boxes1: (N, 4)
    boxes2: (N, 4)
    """
    assert (boxes1[:, 2:] >= boxes1[:, :2]).all()
    assert (boxes2[:, 2:] >= boxes2[:, :2]).all()
    iou, union = box_iou(boxes1, boxes2)
    lt = torch.min(boxes1[:, :2], boxes2[:, :2])
    rb = torch.max(boxes1[:, 2:], boxes2[:, 2:])
    wh = (rb - lt).clamp(min=0)
    area = wh[:, 0] * wh[:, 1]
    return (iou - (area - union) / area, iou)

def clip_box(box: list, H, W, margin=0):
    x1, y1, w, h = box
    x2, y2 = (x1 + w, y1 + h)
    x1 = min(max(0, x1), W - margin)
    x2 = min(max(margin, x2), W)
    y1 = min(max(0, y1), H - margin)
    y2 = min(max(margin, y2), H)
    w = max(margin, x2 - x1)
    h = max(margin, y2 - y1)
    return [x1, y1, w, h]

class FocalLoss(nn.Module, ABC):

    def __init__(self, alpha=2, beta=4):
        super(FocalLoss, self).__init__()
        self.alpha = alpha
        self.beta = beta

    def forward(self, prediction, target):
        positive_index = target.eq(1).float()
        negative_index = target.lt(1).float()
        negative_weights = torch.pow(1 - target, self.beta)
        prediction = torch.clamp(prediction, 1e-12)
        positive_loss = torch.log(prediction) * torch.pow(1 - prediction, self.alpha) * positive_index
        negative_loss = torch.log(1 - prediction) * torch.pow(prediction, self.alpha) * negative_weights * negative_index
        num_positive = positive_index.float().sum()
        positive_loss = positive_loss.sum()
        negative_loss = negative_loss.sum()
        if num_positive == 0:
            loss = -negative_loss
        else:
            loss = -(positive_loss + negative_loss) / num_positive
        return loss

def forward(self, prediction, target):
    positive_index = target.eq(1).float()
    negative_index = target.lt(1).float()
    negative_weights = torch.pow(1 - target, self.beta)
    prediction = torch.clamp(prediction, 1e-12)
    positive_loss = torch.log(prediction) * torch.pow(1 - prediction, self.alpha) * positive_index
    negative_loss = torch.log(1 - prediction) * torch.pow(prediction, self.alpha) * negative_weights * negative_index
    num_positive = positive_index.float().sum()
    positive_loss = positive_loss.sum()
    negative_loss = negative_loss.sum()
    if num_positive == 0:
        loss = -negative_loss
    else:
        loss = -(positive_loss + negative_loss) / num_positive
    return loss

class LBHinge(nn.Module):
    """Loss that uses a 'hinge' on the lower bound.
    This means that for samples with a label value smaller than the threshold, the loss is zero if the prediction is
    also smaller than that threshold.
    args:
        error_matric:  What base loss to use (MSE by default).
        threshold:  Threshold to use for the hinge.
        clip:  Clip the loss if it is above this value.
    """

    def __init__(self, error_metric=nn.MSELoss(), threshold=None, clip=None):
        super().__init__()
        self.error_metric = error_metric
        self.threshold = threshold if threshold is not None else -100
        self.clip = clip

    def forward(self, prediction, label, target_bb=None):
        negative_mask = (label < self.threshold).float()
        positive_mask = 1.0 - negative_mask
        prediction = negative_mask * F.relu(prediction) + positive_mask * prediction
        loss = self.error_metric(prediction, positive_mask * label)
        if self.clip is not None:
            loss = torch.min(loss, torch.tensor([self.clip], device=loss.device))
        return loss

def forward(self, prediction, label, target_bb=None):
    negative_mask = (label < self.threshold).float()
    positive_mask = 1.0 - negative_mask
    prediction = negative_mask * F.relu(prediction) + positive_mask * prediction
    loss = self.error_metric(prediction, positive_mask * label)
    if self.clip is not None:
        loss = torch.min(loss, torch.tensor([self.clip], device=loss.device))
    return loss

def generate_mask_cond(cfg, bs, device, gt_bbox):
    template_size = cfg.DATA.TEMPLATE.SIZE
    stride = cfg.MODEL.BACKBONE.STRIDE
    template_feat_size = template_size // stride
    if cfg.MODEL.BACKBONE.CE_TEMPLATE_RANGE == 'ALL':
        box_mask_z = None
    elif cfg.MODEL.BACKBONE.CE_TEMPLATE_RANGE == 'CTR_POINT':
        if template_feat_size == 8:
            index = slice(3, 4)
        elif template_feat_size == 12:
            index = slice(5, 6)
        elif template_feat_size == 7:
            index = slice(3, 4)
        elif template_feat_size == 14:
            index = slice(6, 7)
        else:
            raise NotImplementedError
        box_mask_z = torch.zeros([bs, template_feat_size, template_feat_size], device=device)
        box_mask_z[:, index, index] = 1
        box_mask_z = box_mask_z.flatten(1).to(torch.bool)
    elif cfg.MODEL.BACKBONE.CE_TEMPLATE_RANGE == 'CTR_REC':
        if template_feat_size == 8:
            index = slice(3, 5)
        elif template_feat_size == 12:
            index = slice(5, 7)
        elif template_feat_size == 7:
            index = slice(3, 4)
        else:
            raise NotImplementedError
        box_mask_z = torch.zeros([bs, template_feat_size, template_feat_size], device=device)
        box_mask_z[:, index, index] = 1
        box_mask_z = box_mask_z.flatten(1).to(torch.bool)
    elif cfg.MODEL.BACKBONE.CE_TEMPLATE_RANGE == 'GT_BOX':
        box_mask_z = torch.zeros([bs, template_size, template_size], device=device)
        box_mask_z = generate_bbox_mask(box_mask_z, gt_bbox * template_size).unsqueeze(1).to(torch.float)
        box_mask_z = F.interpolate(box_mask_z, scale_factor=1.0 / cfg.MODEL.BACKBONE.STRIDE, mode='bilinear', align_corners=False)
        box_mask_z = box_mask_z.flatten(1).to(torch.bool)
    else:
        raise NotImplementedError
    return box_mask_z

class SmoothedValue(object):
    """Track a series of values and provide access to smoothed values over a
    window or the global series average.
    """

    def __init__(self, window_size=20, fmt=None):
        if fmt is None:
            fmt = '{median:.4f} ({global_avg:.4f})'
        self.deque = deque(maxlen=window_size)
        self.total = 0.0
        self.count = 0
        self.fmt = fmt

    def update(self, value, n=1):
        self.deque.append(value)
        self.count += n
        self.total += value * n

    def synchronize_between_processes(self):
        """
        Warning: does not synchronize the deque!
        """
        if not is_dist_avail_and_initialized():
            return
        t = torch.tensor([self.count, self.total], dtype=torch.float64, device='cuda')
        dist.barrier()
        dist.all_reduce(t)
        t = t.tolist()
        self.count = int(t[0])
        self.total = t[1]

    @property
    def median(self):
        d = torch.tensor(list(self.deque))
        return d.median().item()

    @property
    def avg(self):
        d = torch.tensor(list(self.deque), dtype=torch.float32)
        return d.mean().item()

    @property
    def global_avg(self):
        return self.total / self.count

    @property
    def max(self):
        return max(self.deque)

    @property
    def value(self):
        return self.deque[-1]

    def __str__(self):
        return self.fmt.format(median=self.median, avg=self.avg, global_avg=self.global_avg, max=self.max, value=self.value)

@property
def median(self):
    d = torch.tensor(list(self.deque))
    return d.median().item()

@property
def avg(self):
    d = torch.tensor(list(self.deque), dtype=torch.float32)
    return d.mean().item()

@property
def max(self):
    return max(self.deque)

def all_gather(data):
    """
    Run all_gather on arbitrary picklable data (not necessarily tensors)
    Args:
        data: any picklable object
    Returns:
        list[data]: list of data gathered from each rank
    """
    world_size = get_world_size()
    if world_size == 1:
        return [data]
    buffer = pickle.dumps(data)
    storage = torch.ByteStorage.from_buffer(buffer)
    tensor = torch.ByteTensor(storage).to('cuda')
    local_size = torch.tensor([tensor.numel()], device='cuda')
    size_list = [torch.tensor([0], device='cuda') for _ in range(world_size)]
    dist.all_gather(size_list, local_size)
    size_list = [int(size.item()) for size in size_list]
    max_size = max(size_list)
    tensor_list = []
    for _ in size_list:
        tensor_list.append(torch.empty((max_size,), dtype=torch.uint8, device='cuda'))
    if local_size != max_size:
        padding = torch.empty(size=(max_size - local_size,), dtype=torch.uint8, device='cuda')
        tensor = torch.cat((tensor, padding), dim=0)
    dist.all_gather(tensor_list, tensor)
    data_list = []
    for size, tensor in zip(size_list, tensor_list):
        buffer = tensor.cpu().numpy().tobytes()[:size]
        data_list.append(pickle.loads(buffer))
    return data_list

@torch.no_grad()
def accuracy(output, target, topk=(1,)):
    """Computes the precision@k for the specified values of k"""
    if target.numel() == 0:
        return [torch.zeros([], device=output.device)]
    maxk = max(topk)
    batch_size = target.size(0)
    _, pred = output.topk(maxk, 1, True, True)
    pred = pred.t()
    correct = pred.eq(target.view(1, -1).expand_as(pred))
    res = []
    for k in topk:
        correct_k = correct[:k].view(-1).float().sum(0)
        res.append(correct_k.mul_(100.0 / batch_size))
    return res

def interpolate(input, size=None, scale_factor=None, mode='nearest', align_corners=None):
    """
    Equivalent to nn.functional.interpolate, but with support for empty batch sizes.
    This will eventually be supported natively by PyTorch, and this
    class can go away.
    """
    if float(torchvision.__version__[:3]) < 0.7:
        if input.numel() > 0:
            return torch.nn.functional.interpolate(input, size, scale_factor, mode, align_corners)
        output_shape = _output_size(2, input, size, scale_factor)
        output_shape = list(input.shape[:-2]) + list(output_shape)
        return _new_empty_tensor(input, output_shape)
    else:
        return torchvision.ops.misc.interpolate(input, size, scale_factor, mode, align_corners)

def get_qkv(inp_list):
    """The 1st element of the inp_list is about the template,
    the 2nd (the last) element is about the search region"""
    dict_x = inp_list[-1]
    dict_c = {'feat': torch.cat([x['feat'] for x in inp_list], dim=0), 'mask': torch.cat([x['mask'] for x in inp_list], dim=1), 'pos': torch.cat([x['pos'] for x in inp_list], dim=0)}
    q = dict_x['feat'] + dict_x['pos']
    k = dict_c['feat'] + dict_c['pos']
    v = dict_c['feat']
    key_padding_mask = dict_c['mask']
    return (q, k, v, key_padding_mask)

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
def gaussian2D(radius, sigma=1):
    m, n = radius
    y, x = np.ogrid[-m:m + 1, -n:n + 1]
    gauss = np.exp(-(x * x + y * y) / (2 * sigma * sigma))
    gauss[gauss < np.finfo(gauss.dtype).eps * gauss.max()] = 0
    return gauss

def get_pred(score_map_ctr, size_map, offset_map, feat_size):
    max_score, idx = torch.max(score_map_ctr.flatten(1), dim=1, keepdim=True)
    idx = idx.unsqueeze(1).expand(idx.shape[0], 2, 1)
    size = size_map.flatten(2).gather(dim=2, index=idx).squeeze(-1)
    offset = offset_map.flatten(2).gather(dim=2, index=idx).squeeze(-1)
    return (size * feat_size, offset)

def hann1d(sz: int, centered=True) -> torch.Tensor:
    """1D cosine window."""
    if centered:
        return 0.5 * (1 - torch.cos(2 * math.pi / (sz + 1) * torch.arange(1, sz + 1).float()))
    w = 0.5 * (1 + torch.cos(2 * math.pi / (sz + 2) * torch.arange(0, sz // 2 + 1).float()))
    return torch.cat([w, w[1:sz - sz // 2].flip((0,))])

def gauss_fourier(sz: int, sigma: float, half: bool=False) -> torch.Tensor:
    if half:
        k = torch.arange(0, int(sz / 2 + 1))
    else:
        k = torch.arange(-int((sz - 1) / 2), int(sz / 2 + 1))
    return math.sqrt(2 * math.pi) * sigma / sz * torch.exp(-2 * (math.pi * sigma * k.float() / sz) ** 2)

def gauss_spatial(sz, sigma, center=0, end_pad=0):
    k = torch.arange(-(sz - 1) / 2, (sz + 1) / 2 + end_pad)
    return torch.exp(-1.0 / (2 * sigma ** 2) * (k - center) ** 2)

def max2d(a: torch.Tensor) -> (torch.Tensor, torch.Tensor):
    """Computes maximum and argmax in the last two dimensions."""
    max_val_row, argmax_row = torch.max(a, dim=-2)
    max_val, argmax_col = torch.max(max_val_row, dim=-1)
    argmax_row = argmax_row.view(argmax_col.numel(), -1)[torch.arange(argmax_col.numel()), argmax_col.view(-1)]
    argmax_row = argmax_row.reshape(argmax_col.shape)
    argmax = torch.cat((argmax_row.unsqueeze(-1), argmax_col.unsqueeze(-1)), -1)
    return (max_val, argmax)

class Preprocessor(object):

    def __init__(self):
        self.mean = torch.tensor([0.485, 0.456, 0.406]).view((1, 3, 1, 1)).cuda()
        self.std = torch.tensor([0.229, 0.224, 0.225]).view((1, 3, 1, 1)).cuda()

    def process(self, img_arr: np.ndarray, amask_arr: np.ndarray):
        img_tensor = torch.tensor(img_arr).cuda().float().permute((2, 0, 1)).unsqueeze(dim=0)
        img_tensor_norm = (img_tensor / 255.0 - self.mean) / self.std
        amask_tensor = torch.from_numpy(amask_arr).to(torch.bool).cuda().unsqueeze(dim=0)
        return NestedTensor(img_tensor_norm, amask_tensor)

def __init__(self):
    self.mean = torch.tensor([0.485, 0.456, 0.406]).view((1, 3, 1, 1)).cuda()
    self.std = torch.tensor([0.229, 0.224, 0.225]).view((1, 3, 1, 1)).cuda()

def process(self, img_arr: np.ndarray, amask_arr: np.ndarray):
    img_tensor = torch.tensor(img_arr).cuda().float().permute((2, 0, 1)).unsqueeze(dim=0)
    img_tensor_norm = (img_tensor / 255.0 - self.mean) / self.std
    amask_tensor = torch.from_numpy(amask_arr).to(torch.bool).cuda().unsqueeze(dim=0)
    return NestedTensor(img_tensor_norm, amask_tensor)

class PreprocessorX(object):

    def __init__(self):
        self.mean = torch.tensor([0.485, 0.456, 0.406]).view((1, 3, 1, 1)).cuda()
        self.std = torch.tensor([0.229, 0.224, 0.225]).view((1, 3, 1, 1)).cuda()

    def process(self, img_arr: np.ndarray, amask_arr: np.ndarray):
        img_tensor = torch.tensor(img_arr).cuda().float().permute((2, 0, 1)).unsqueeze(dim=0)
        img_tensor_norm = (img_tensor / 255.0 - self.mean) / self.std
        amask_tensor = torch.from_numpy(amask_arr).to(torch.bool).cuda().unsqueeze(dim=0)
        return (img_tensor_norm, amask_tensor)

def __init__(self):
    self.mean = torch.tensor([0.485, 0.456, 0.406]).view((1, 3, 1, 1)).cuda()
    self.std = torch.tensor([0.229, 0.224, 0.225]).view((1, 3, 1, 1)).cuda()

def process(self, img_arr: np.ndarray, amask_arr: np.ndarray):
    img_tensor = torch.tensor(img_arr).cuda().float().permute((2, 0, 1)).unsqueeze(dim=0)
    img_tensor_norm = (img_tensor / 255.0 - self.mean) / self.std
    amask_tensor = torch.from_numpy(amask_arr).to(torch.bool).cuda().unsqueeze(dim=0)
    return (img_tensor_norm, amask_tensor)

class Attention(nn.Module):

    def __init__(self, dim, num_heads=8, qkv_bias=False, attn_drop=0.0, proj_drop=0.0):
        super().__init__()
        self.num_heads = num_heads
        head_dim = dim // num_heads
        self.scale = head_dim ** (-0.5)
        self.qkv = nn.Linear(dim, dim * 3, bias=qkv_bias)
        self.attn_drop = nn.Dropout(attn_drop)
        self.proj = nn.Linear(dim, dim)
        self.proj_drop = nn.Dropout(proj_drop)

    def forward(self, x, return_attention=False):
        B, N, C = x.shape
        qkv = self.qkv(x).reshape(B, N, 3, self.num_heads, C // self.num_heads).permute(2, 0, 3, 1, 4)
        q, k, v = (qkv[0], qkv[1], qkv[2])
        attn = q @ k.transpose(-2, -1) * self.scale
        attn = attn.softmax(dim=-1)
        attn = self.attn_drop(attn)
        x = (attn @ v).transpose(1, 2).reshape(B, N, C)
        x = self.proj(x)
        x = self.proj_drop(x)
        if return_attention:
            return (x, attn)
        return x

def forward(self, x, return_attention=False):
    B, N, C = x.shape
    qkv = self.qkv(x).reshape(B, N, 3, self.num_heads, C // self.num_heads).permute(2, 0, 3, 1, 4)
    q, k, v = (qkv[0], qkv[1], qkv[2])
    attn = q @ k.transpose(-2, -1) * self.scale
    attn = attn.softmax(dim=-1)
    attn = self.attn_drop(attn)
    x = (attn @ v).transpose(1, 2).reshape(B, N, C)
    x = self.proj(x)
    x = self.proj_drop(x)
    if return_attention:
        return (x, attn)
    return x

def _n2p(w, t=True):
    if w.ndim == 4 and w.shape[0] == w.shape[1] == w.shape[2] == 1:
        w = w.flatten()
    if t:
        if w.ndim == 4:
            w = w.transpose([3, 2, 0, 1])
        elif w.ndim == 3:
            w = w.transpose([2, 0, 1])
        elif w.ndim == 2:
            w = w.transpose([1, 0])
    return torch.from_numpy(w)

class VisionTransformerCE(VisionTransformer):
    """ Vision Transformer with candidate elimination (CE) module

    A PyTorch impl of : `An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale`
        - https://arxiv.org/abs/2010.11929

    Includes distillation token & head support for `DeiT: Data-efficient Image Transformers`
        - https://arxiv.org/abs/2012.12877
    """

    def __init__(self, img_size=224, patch_size=16, in_chans=3, num_classes=1000, embed_dim=768, depth=12, num_heads=12, mlp_ratio=4.0, qkv_bias=True, representation_size=None, distilled=False, drop_rate=0.0, attn_drop_rate=0.0, drop_path_rate=0.0, embed_layer=PatchEmbed, norm_layer=None, act_layer=None, weight_init='', ce_loc=None, ce_keep_ratio=None):
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
        if isinstance(img_size, tuple):
            self.img_size = img_size
        else:
            self.img_size = to_2tuple(img_size)
        self.patch_size = patch_size
        self.in_chans = in_chans
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
        blocks = []
        ce_index = 0
        self.ce_loc = ce_loc
        for i in range(depth):
            ce_keep_ratio_i = 1.0
            if ce_loc is not None and i in ce_loc:
                ce_keep_ratio_i = ce_keep_ratio[ce_index]
                ce_index += 1
            blocks.append(CEBlock(dim=embed_dim, num_heads=num_heads, mlp_ratio=mlp_ratio, qkv_bias=qkv_bias, drop=drop_rate, attn_drop=attn_drop_rate, drop_path=dpr[i], norm_layer=norm_layer, act_layer=act_layer, keep_ratio_search=ce_keep_ratio_i))
        self.blocks = nn.Sequential(*blocks)
        self.norm = norm_layer(embed_dim)
        self.init_weights(weight_init)

    def forward_features(self, z, x, mask_z=None, mask_x=None, ce_template_mask=None, ce_keep_rate=None, return_last_attn=False):
        B, H, W = (x.shape[0], x.shape[2], x.shape[3])
        x = self.patch_embed(x)
        z = self.patch_embed(z)
        if mask_z is not None and mask_x is not None:
            mask_z = F.interpolate(mask_z[None].float(), scale_factor=1.0 / self.patch_size).to(torch.bool)[0]
            mask_z = mask_z.flatten(1).unsqueeze(-1)
            mask_x = F.interpolate(mask_x[None].float(), scale_factor=1.0 / self.patch_size).to(torch.bool)[0]
            mask_x = mask_x.flatten(1).unsqueeze(-1)
            mask_x = combine_tokens(mask_z, mask_x, mode=self.cat_mode)
            mask_x = mask_x.squeeze(-1)
        if self.add_cls_token:
            cls_tokens = self.cls_token.expand(B, -1, -1)
            cls_tokens = cls_tokens + self.cls_pos_embed
        z += self.pos_embed_z
        x += self.pos_embed_x
        if self.add_sep_seg:
            x += self.search_segment_pos_embed
            z += self.template_segment_pos_embed
        x = combine_tokens(z, x, mode=self.cat_mode)
        if self.add_cls_token:
            x = torch.cat([cls_tokens, x], dim=1)
        x = self.pos_drop(x)
        lens_z = self.pos_embed_z.shape[1]
        lens_x = self.pos_embed_x.shape[1]
        global_index_t = torch.linspace(0, lens_z - 1, lens_z).to(x.device)
        global_index_t = global_index_t.repeat(B, 1)
        global_index_s = torch.linspace(0, lens_x - 1, lens_x).to(x.device)
        global_index_s = global_index_s.repeat(B, 1)
        removed_indexes_s = []
        for i, blk in enumerate(self.blocks):
            x, global_index_t, global_index_s, removed_index_s, attn = blk(x, global_index_t, global_index_s, mask_x, ce_template_mask, ce_keep_rate)
            if self.ce_loc is not None and i in self.ce_loc:
                removed_indexes_s.append(removed_index_s)
        x = self.norm(x)
        lens_x_new = global_index_s.shape[1]
        lens_z_new = global_index_t.shape[1]
        z = x[:, :lens_z_new]
        x = x[:, lens_z_new:]
        if removed_indexes_s and removed_indexes_s[0] is not None:
            removed_indexes_cat = torch.cat(removed_indexes_s, dim=1)
            pruned_lens_x = lens_x - lens_x_new
            pad_x = torch.zeros([B, pruned_lens_x, x.shape[2]], device=x.device)
            x = torch.cat([x, pad_x], dim=1)
            index_all = torch.cat([global_index_s, removed_indexes_cat], dim=1)
            C = x.shape[-1]
            x = torch.zeros_like(x).scatter_(dim=1, index=index_all.unsqueeze(-1).expand(B, -1, C).to(torch.int64), src=x)
        x = recover_tokens(x, lens_z_new, lens_x, mode=self.cat_mode)
        x = torch.cat([z, x], dim=1)
        aux_dict = {'attn': attn, 'removed_indexes_s': removed_indexes_s}
        return (x, aux_dict)

    def forward(self, z, x, ce_template_mask=None, ce_keep_rate=None, tnc_keep_rate=None, return_last_attn=False):
        x, aux_dict = self.forward_features(z, x, ce_template_mask=ce_template_mask, ce_keep_rate=ce_keep_rate)
        return (x, aux_dict)

def forward_features(self, z, x, mask_z=None, mask_x=None, ce_template_mask=None, ce_keep_rate=None, return_last_attn=False):
    B, H, W = (x.shape[0], x.shape[2], x.shape[3])
    x = self.patch_embed(x)
    z = self.patch_embed(z)
    if mask_z is not None and mask_x is not None:
        mask_z = F.interpolate(mask_z[None].float(), scale_factor=1.0 / self.patch_size).to(torch.bool)[0]
        mask_z = mask_z.flatten(1).unsqueeze(-1)
        mask_x = F.interpolate(mask_x[None].float(), scale_factor=1.0 / self.patch_size).to(torch.bool)[0]
        mask_x = mask_x.flatten(1).unsqueeze(-1)
        mask_x = combine_tokens(mask_z, mask_x, mode=self.cat_mode)
        mask_x = mask_x.squeeze(-1)
    if self.add_cls_token:
        cls_tokens = self.cls_token.expand(B, -1, -1)
        cls_tokens = cls_tokens + self.cls_pos_embed
    z += self.pos_embed_z
    x += self.pos_embed_x
    if self.add_sep_seg:
        x += self.search_segment_pos_embed
        z += self.template_segment_pos_embed
    x = combine_tokens(z, x, mode=self.cat_mode)
    if self.add_cls_token:
        x = torch.cat([cls_tokens, x], dim=1)
    x = self.pos_drop(x)
    lens_z = self.pos_embed_z.shape[1]
    lens_x = self.pos_embed_x.shape[1]
    global_index_t = torch.linspace(0, lens_z - 1, lens_z).to(x.device)
    global_index_t = global_index_t.repeat(B, 1)
    global_index_s = torch.linspace(0, lens_x - 1, lens_x).to(x.device)
    global_index_s = global_index_s.repeat(B, 1)
    removed_indexes_s = []
    for i, blk in enumerate(self.blocks):
        x, global_index_t, global_index_s, removed_index_s, attn = blk(x, global_index_t, global_index_s, mask_x, ce_template_mask, ce_keep_rate)
        if self.ce_loc is not None and i in self.ce_loc:
            removed_indexes_s.append(removed_index_s)
    x = self.norm(x)
    lens_x_new = global_index_s.shape[1]
    lens_z_new = global_index_t.shape[1]
    z = x[:, :lens_z_new]
    x = x[:, lens_z_new:]
    if removed_indexes_s and removed_indexes_s[0] is not None:
        removed_indexes_cat = torch.cat(removed_indexes_s, dim=1)
        pruned_lens_x = lens_x - lens_x_new
        pad_x = torch.zeros([B, pruned_lens_x, x.shape[2]], device=x.device)
        x = torch.cat([x, pad_x], dim=1)
        index_all = torch.cat([global_index_s, removed_indexes_cat], dim=1)
        C = x.shape[-1]
        x = torch.zeros_like(x).scatter_(dim=1, index=index_all.unsqueeze(-1).expand(B, -1, C).to(torch.int64), src=x)
    x = recover_tokens(x, lens_z_new, lens_x, mode=self.cat_mode)
    x = torch.cat([z, x], dim=1)
    aux_dict = {'attn': attn, 'removed_indexes_s': removed_indexes_s}
    return (x, aux_dict)

def combine_tokens(template_tokens, search_tokens, mode='direct', return_res=False):
    len_t = template_tokens.shape[1]
    len_s = search_tokens.shape[1]
    if mode == 'direct':
        merged_feature = torch.cat((template_tokens, search_tokens), dim=1)
    elif mode == 'template_central':
        central_pivot = len_s // 2
        first_half = search_tokens[:, :central_pivot, :]
        second_half = search_tokens[:, central_pivot:, :]
        merged_feature = torch.cat((first_half, template_tokens, second_half), dim=1)
    elif mode == 'partition':
        feat_size_s = int(math.sqrt(len_s))
        feat_size_t = int(math.sqrt(len_t))
        window_size = math.ceil(feat_size_t / 2.0)
        B, _, C = template_tokens.shape
        H = W = feat_size_t
        template_tokens = template_tokens.view(B, H, W, C)
        pad_l = pad_b = pad_r = 0
        pad_t = (window_size - H % window_size) % window_size
        template_tokens = F.pad(template_tokens, (0, 0, pad_l, pad_r, pad_t, pad_b))
        _, Hp, Wp, _ = template_tokens.shape
        template_tokens = template_tokens.view(B, Hp // window_size, window_size, W, C)
        template_tokens = torch.cat([template_tokens[:, 0, ...], template_tokens[:, 1, ...]], dim=2)
        _, Hc, Wc, _ = template_tokens.shape
        template_tokens = template_tokens.view(B, -1, C)
        merged_feature = torch.cat([template_tokens, search_tokens], dim=1)
        merged_h, merged_w = (feat_size_s + Hc, feat_size_s)
        if return_res:
            return (merged_feature, merged_h, merged_w)
    else:
        raise NotImplementedError
    return merged_feature

def recover_tokens(merged_tokens, len_template_token, len_search_token, mode='direct'):
    if mode == 'direct':
        recovered_tokens = merged_tokens
    elif mode == 'template_central':
        central_pivot = len_search_token // 2
        len_remain = len_search_token - central_pivot
        len_half_and_t = central_pivot + len_template_token
        first_half = merged_tokens[:, :central_pivot, :]
        second_half = merged_tokens[:, -len_remain:, :]
        template_tokens = merged_tokens[:, central_pivot:len_half_and_t, :]
        recovered_tokens = torch.cat((template_tokens, first_half, second_half), dim=1)
    elif mode == 'partition':
        recovered_tokens = merged_tokens
    else:
        raise NotImplementedError
    return recovered_tokens

def window_partition(x, window_size: int):
    """
    Args:
        x: (B, H, W, C)
        window_size (int): window size

    Returns:
        windows: (num_windows*B, window_size, window_size, C)
    """
    B, H, W, C = x.shape
    x = x.view(B, H // window_size, window_size, W // window_size, window_size, C)
    windows = x.permute(0, 1, 3, 2, 4, 5).contiguous().view(-1, window_size, window_size, C)
    return windows

def window_reverse(windows, window_size: int, H: int, W: int):
    """
    Args:
        windows: (num_windows*B, window_size, window_size, C)
        window_size (int): Window size
        H (int): Height of image
        W (int): Width of image

    Returns:
        x: (B, H, W, C)
    """
    B = int(windows.shape[0] / (H * W / window_size / window_size))
    x = windows.view(B, H // window_size, W // window_size, window_size, window_size, -1)
    x = x.permute(0, 1, 3, 2, 4, 5).contiguous().view(B, H, W, -1)
    return x

class BaseBackbone(nn.Module):

    def __init__(self):
        super().__init__()
        self.pos_embed = None
        self.img_size = [224, 224]
        self.patch_size = 16
        self.embed_dim = 384
        self.cat_mode = 'direct'
        self.pos_embed_z = None
        self.pos_embed_x = None
        self.template_segment_pos_embed = None
        self.search_segment_pos_embed = None
        self.return_inter = False
        self.return_stage = [2, 5, 8, 11]
        self.add_cls_token = False
        self.add_sep_seg = False

    def finetune_track(self, cfg, patch_start_index=1):
        search_size = to_2tuple(cfg.DATA.SEARCH.SIZE)
        template_size = to_2tuple(cfg.DATA.TEMPLATE.SIZE)
        new_patch_size = cfg.MODEL.BACKBONE.STRIDE
        self.cat_mode = cfg.MODEL.BACKBONE.CAT_MODE
        self.return_inter = cfg.MODEL.RETURN_INTER
        self.return_stage = cfg.MODEL.RETURN_STAGES
        self.add_sep_seg = cfg.MODEL.BACKBONE.SEP_SEG
        if new_patch_size != self.patch_size:
            print('Inconsistent Patch Size With The Pretrained Weights, Interpolate The Weight!')
            old_patch_embed = {}
            for name, param in self.patch_embed.named_parameters():
                if 'weight' in name:
                    param = nn.functional.interpolate(param, size=(new_patch_size, new_patch_size), mode='bicubic', align_corners=False)
                    param = nn.Parameter(param)
                old_patch_embed[name] = param
            self.patch_embed = PatchEmbed(img_size=self.img_size, patch_size=new_patch_size, in_chans=3, embed_dim=self.embed_dim)
            self.patch_embed.proj.bias = old_patch_embed['proj.bias']
            self.patch_embed.proj.weight = old_patch_embed['proj.weight']
        patch_pos_embed = self.pos_embed[:, patch_start_index:, :]
        patch_pos_embed = patch_pos_embed.transpose(1, 2)
        B, E, Q = patch_pos_embed.shape
        P_H, P_W = (self.img_size[0] // self.patch_size, self.img_size[1] // self.patch_size)
        patch_pos_embed = patch_pos_embed.view(B, E, P_H, P_W)
        H, W = search_size
        new_P_H, new_P_W = (H // new_patch_size, W // new_patch_size)
        search_patch_pos_embed = nn.functional.interpolate(patch_pos_embed, size=(new_P_H, new_P_W), mode='bicubic', align_corners=False)
        search_patch_pos_embed = search_patch_pos_embed.flatten(2).transpose(1, 2)
        H, W = template_size
        new_P_H, new_P_W = (H // new_patch_size, W // new_patch_size)
        template_patch_pos_embed = nn.functional.interpolate(patch_pos_embed, size=(new_P_H, new_P_W), mode='bicubic', align_corners=False)
        template_patch_pos_embed = template_patch_pos_embed.flatten(2).transpose(1, 2)
        self.pos_embed_z = nn.Parameter(template_patch_pos_embed)
        self.pos_embed_x = nn.Parameter(search_patch_pos_embed)
        if self.add_cls_token and patch_start_index > 0:
            cls_pos_embed = self.pos_embed[:, 0:1, :]
            self.cls_pos_embed = nn.Parameter(cls_pos_embed)
        if self.add_sep_seg:
            self.template_segment_pos_embed = nn.Parameter(torch.zeros(1, 1, self.embed_dim))
            self.template_segment_pos_embed = trunc_normal_(self.template_segment_pos_embed, std=0.02)
            self.search_segment_pos_embed = nn.Parameter(torch.zeros(1, 1, self.embed_dim))
            self.search_segment_pos_embed = trunc_normal_(self.search_segment_pos_embed, std=0.02)
        if self.return_inter:
            for i_layer in self.return_stage:
                if i_layer != 11:
                    norm_layer = partial(nn.LayerNorm, eps=1e-06)
                    layer = norm_layer(self.embed_dim)
                    layer_name = f'norm{i_layer}'
                    self.add_module(layer_name, layer)

    def forward_features(self, z, x):
        B, H, W = (x.shape[0], x.shape[2], x.shape[3])
        x = self.patch_embed(x)
        z = self.patch_embed(z)
        if self.add_cls_token:
            cls_tokens = self.cls_token.expand(B, -1, -1)
            cls_tokens = cls_tokens + self.cls_pos_embed
        z += self.pos_embed_z
        x += self.pos_embed_x
        if self.add_sep_seg:
            x += self.search_segment_pos_embed
            z += self.template_segment_pos_embed
        x = combine_tokens(z, x, mode=self.cat_mode)
        if self.add_cls_token:
            x = torch.cat([cls_tokens, x], dim=1)
        x = self.pos_drop(x)
        for i, blk in enumerate(self.blocks):
            x = blk(x)
        lens_z = self.pos_embed_z.shape[1]
        lens_x = self.pos_embed_x.shape[1]
        x = recover_tokens(x, lens_z, lens_x, mode=self.cat_mode)
        aux_dict = {'attn': None}
        return (self.norm(x), aux_dict)

    def forward(self, z, x, **kwargs):
        """
        Joint feature extraction and relation modeling for the basic ViT backbone.
        Args:
            z (torch.Tensor): template feature, [B, C, H_z, W_z]
            x (torch.Tensor): search region feature, [B, C, H_x, W_x]

        Returns:
            x (torch.Tensor): merged template and search region feature, [B, L_z+L_x, C]
            attn : None
        """
        x, aux_dict = self.forward_features(z, x)
        return (x, aux_dict)

def forward_features(self, z, x):
    B, H, W = (x.shape[0], x.shape[2], x.shape[3])
    x = self.patch_embed(x)
    z = self.patch_embed(z)
    if self.add_cls_token:
        cls_tokens = self.cls_token.expand(B, -1, -1)
        cls_tokens = cls_tokens + self.cls_pos_embed
    z += self.pos_embed_z
    x += self.pos_embed_x
    if self.add_sep_seg:
        x += self.search_segment_pos_embed
        z += self.template_segment_pos_embed
    x = combine_tokens(z, x, mode=self.cat_mode)
    if self.add_cls_token:
        x = torch.cat([cls_tokens, x], dim=1)
    x = self.pos_drop(x)
    for i, blk in enumerate(self.blocks):
        x = blk(x)
    lens_z = self.pos_embed_z.shape[1]
    lens_x = self.pos_embed_x.shape[1]
    x = recover_tokens(x, lens_z, lens_x, mode=self.cat_mode)
    aux_dict = {'attn': None}
    return (self.norm(x), aux_dict)

class OSTrack(nn.Module):
    """ This is the base class for OSTrack """

    def __init__(self, transformer, box_head, aux_loss=False, head_type='CORNER'):
        """ Initializes the model.
        Parameters:
            transformer: torch module of the transformer architecture.
            aux_loss: True if auxiliary decoding losses (loss at each decoder layer) are to be used.
        """
        super().__init__()
        self.backbone = transformer
        self.box_head = box_head
        self.aux_loss = aux_loss
        self.head_type = head_type
        if head_type == 'CORNER' or head_type == 'CENTER':
            self.feat_sz_s = int(box_head.feat_sz)
            self.feat_len_s = int(box_head.feat_sz ** 2)
        if self.aux_loss:
            self.box_head = _get_clones(self.box_head, 6)

    def forward(self, template: torch.Tensor, search: torch.Tensor, ce_template_mask=None, ce_keep_rate=None, return_last_attn=False):
        x, aux_dict = self.backbone(z=template, x=search, ce_template_mask=ce_template_mask, ce_keep_rate=ce_keep_rate, return_last_attn=return_last_attn)
        feat_last = x
        if isinstance(x, list):
            feat_last = x[-1]
        out = self.forward_head(feat_last, None)
        out.update(aux_dict)
        out['backbone_feat'] = x
        return out

    def forward_head(self, cat_feature, gt_score_map=None):
        """
        cat_feature: output embeddings of the backbone, it can be (HW1+HW2, B, C) or (HW2, B, C)
        """
        enc_opt = cat_feature[:, -self.feat_len_s:]
        opt = enc_opt.unsqueeze(-1).permute((0, 3, 2, 1)).contiguous()
        bs, Nq, C, HW = opt.size()
        opt_feat = opt.view(-1, C, self.feat_sz_s, self.feat_sz_s)
        if self.head_type == 'CORNER':
            pred_box, score_map = self.box_head(opt_feat, True)
            outputs_coord = box_xyxy_to_cxcywh(pred_box)
            outputs_coord_new = outputs_coord.view(bs, Nq, 4)
            out = {'pred_boxes': outputs_coord_new, 'score_map': score_map}
            return out
        elif self.head_type == 'CENTER':
            score_map_ctr, bbox, size_map, offset_map = self.box_head(opt_feat, gt_score_map)
            outputs_coord = bbox
            outputs_coord_new = outputs_coord.view(bs, Nq, 4)
            out = {'pred_boxes': outputs_coord_new, 'score_map': score_map_ctr, 'size_map': size_map, 'offset_map': offset_map}
            return out
        else:
            raise NotImplementedError

def forward_head(self, cat_feature, gt_score_map=None):
    """
        cat_feature: output embeddings of the backbone, it can be (HW1+HW2, B, C) or (HW2, B, C)
        """
    enc_opt = cat_feature[:, -self.feat_len_s:]
    opt = enc_opt.unsqueeze(-1).permute((0, 3, 2, 1)).contiguous()
    bs, Nq, C, HW = opt.size()
    opt_feat = opt.view(-1, C, self.feat_sz_s, self.feat_sz_s)
    if self.head_type == 'CORNER':
        pred_box, score_map = self.box_head(opt_feat, True)
        outputs_coord = box_xyxy_to_cxcywh(pred_box)
        outputs_coord_new = outputs_coord.view(bs, Nq, 4)
        out = {'pred_boxes': outputs_coord_new, 'score_map': score_map}
        return out
    elif self.head_type == 'CENTER':
        score_map_ctr, bbox, size_map, offset_map = self.box_head(opt_feat, gt_score_map)
        outputs_coord = bbox
        outputs_coord_new = outputs_coord.view(bs, Nq, 4)
        out = {'pred_boxes': outputs_coord_new, 'score_map': score_map_ctr, 'size_map': size_map, 'offset_map': offset_map}
        return out
    else:
        raise NotImplementedError

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

def _sigmoid(x):
    y = torch.clamp(x.sigmoid_(), min=0.0001, max=1 - 0.0001)
    return y

class Attention(nn.Module):

    def __init__(self, dim, num_heads=8, qkv_bias=False, attn_drop=0.0, proj_drop=0.0, rpe=False, z_size=7, x_size=14):
        super().__init__()
        self.num_heads = num_heads
        head_dim = dim // num_heads
        self.scale = head_dim ** (-0.5)
        self.qkv = nn.Linear(dim, dim * 3, bias=qkv_bias)
        self.attn_drop = nn.Dropout(attn_drop)
        self.proj = nn.Linear(dim, dim)
        self.proj_drop = nn.Dropout(proj_drop)
        self.rpe = rpe
        if self.rpe:
            relative_position_index = generate_2d_concatenated_self_attention_relative_positional_encoding_index([z_size, z_size], [x_size, x_size])
            self.register_buffer('relative_position_index', relative_position_index)
            self.relative_position_bias_table = nn.Parameter(torch.empty((num_heads, relative_position_index.max() + 1)))
            trunc_normal_(self.relative_position_bias_table, std=0.02)

    def forward(self, x, mask=None, return_attention=False):
        B, N, C = x.shape
        qkv = self.qkv(x).reshape(B, N, 3, self.num_heads, C // self.num_heads).permute(2, 0, 3, 1, 4)
        q, k, v = qkv.unbind(0)
        attn = q @ k.transpose(-2, -1) * self.scale
        if self.rpe:
            relative_position_bias = self.relative_position_bias_table[:, self.relative_position_index].unsqueeze(0)
            attn += relative_position_bias
        if mask is not None:
            attn = attn.masked_fill(mask.unsqueeze(1).unsqueeze(2), float('-inf'))
        attn = attn.softmax(dim=-1)
        attn = self.attn_drop(attn)
        x = (attn @ v).transpose(1, 2).reshape(B, N, C)
        x = self.proj(x)
        x = self.proj_drop(x)
        if return_attention:
            return (x, attn)
        else:
            return x

def forward(self, x, mask=None, return_attention=False):
    B, N, C = x.shape
    qkv = self.qkv(x).reshape(B, N, 3, self.num_heads, C // self.num_heads).permute(2, 0, 3, 1, 4)
    q, k, v = qkv.unbind(0)
    attn = q @ k.transpose(-2, -1) * self.scale
    if self.rpe:
        relative_position_bias = self.relative_position_bias_table[:, self.relative_position_index].unsqueeze(0)
        attn += relative_position_bias
    if mask is not None:
        attn = attn.masked_fill(mask.unsqueeze(1).unsqueeze(2), float('-inf'))
    attn = attn.softmax(dim=-1)
    attn = self.attn_drop(attn)
    x = (attn @ v).transpose(1, 2).reshape(B, N, C)
    x = self.proj(x)
    x = self.proj_drop(x)
    if return_attention:
        return (x, attn)
    else:
        return x

class Attention_talking_head(nn.Module):

    def __init__(self, dim, num_heads=8, qkv_bias=False, qk_scale=None, attn_drop=0.0, proj_drop=0.0, rpe=True, z_size=7, x_size=14):
        super().__init__()
        self.num_heads = num_heads
        head_dim = dim // num_heads
        self.scale = qk_scale or head_dim ** (-0.5)
        self.qkv = nn.Linear(dim, dim * 3, bias=qkv_bias)
        self.attn_drop = nn.Dropout(attn_drop)
        self.proj = nn.Linear(dim, dim)
        self.proj_l = nn.Linear(num_heads, num_heads)
        self.proj_w = nn.Linear(num_heads, num_heads)
        self.proj_drop = nn.Dropout(proj_drop)
        self.rpe = rpe
        if self.rpe:
            relative_position_index = generate_2d_concatenated_self_attention_relative_positional_encoding_index([z_size, z_size], [x_size, x_size])
            self.register_buffer('relative_position_index', relative_position_index)
            self.relative_position_bias_table = nn.Parameter(torch.empty((num_heads, relative_position_index.max() + 1)))
            trunc_normal_(self.relative_position_bias_table, std=0.02)

    def forward(self, x, mask=None):
        B, N, C = x.shape
        qkv = self.qkv(x).reshape(B, N, 3, self.num_heads, C // self.num_heads).permute(2, 0, 3, 1, 4)
        q, k, v = (qkv[0] * self.scale, qkv[1], qkv[2])
        attn = q @ k.transpose(-2, -1)
        if self.rpe:
            relative_position_bias = self.relative_position_bias_table[:, self.relative_position_index].unsqueeze(0)
            attn += relative_position_bias
        if mask is not None:
            attn = attn.masked_fill(mask.unsqueeze(1).unsqueeze(2), float('-inf'))
        attn = self.proj_l(attn.permute(0, 2, 3, 1)).permute(0, 3, 1, 2)
        attn = attn.softmax(dim=-1)
        attn = self.proj_w(attn.permute(0, 2, 3, 1)).permute(0, 3, 1, 2)
        attn = self.attn_drop(attn)
        x = (attn @ v).transpose(1, 2).reshape(B, N, C)
        x = self.proj(x)
        x = self.proj_drop(x)
        return x

def forward(self, x, mask=None):
    B, N, C = x.shape
    qkv = self.qkv(x).reshape(B, N, 3, self.num_heads, C // self.num_heads).permute(2, 0, 3, 1, 4)
    q, k, v = (qkv[0] * self.scale, qkv[1], qkv[2])
    attn = q @ k.transpose(-2, -1)
    if self.rpe:
        relative_position_bias = self.relative_position_bias_table[:, self.relative_position_index].unsqueeze(0)
        attn += relative_position_bias
    if mask is not None:
        attn = attn.masked_fill(mask.unsqueeze(1).unsqueeze(2), float('-inf'))
    attn = self.proj_l(attn.permute(0, 2, 3, 1)).permute(0, 3, 1, 2)
    attn = attn.softmax(dim=-1)
    attn = self.proj_w(attn.permute(0, 2, 3, 1)).permute(0, 3, 1, 2)
    attn = self.attn_drop(attn)
    x = (attn @ v).transpose(1, 2).reshape(B, N, C)
    x = self.proj(x)
    x = self.proj_drop(x)
    return x

def generate_2d_relative_positional_encoding_index(z_shape, x_shape):
    """
        z_shape: (z_h, z_w)
        x_shape: (x_h, x_w)
    """
    z_2d_index_h, z_2d_index_w = torch.meshgrid(torch.arange(z_shape[0]), torch.arange(z_shape[1]))
    x_2d_index_h, x_2d_index_w = torch.meshgrid(torch.arange(x_shape[0]), torch.arange(x_shape[1]))
    z_2d_index_h = z_2d_index_h.flatten(0)
    z_2d_index_w = z_2d_index_w.flatten(0)
    x_2d_index_h = x_2d_index_h.flatten(0)
    x_2d_index_w = x_2d_index_w.flatten(0)
    diff_h = z_2d_index_h[:, None] - x_2d_index_h[None, :]
    diff_w = z_2d_index_w[:, None] - x_2d_index_w[None, :]
    diff = torch.stack((diff_h, diff_w), dim=-1)
    _, indices = torch.unique(diff.view(-1, 2), return_inverse=True, dim=0)
    return indices.view(z_shape[0] * z_shape[1], x_shape[0] * x_shape[1])

def generate_2d_concatenated_self_attention_relative_positional_encoding_index(z_shape, x_shape):
    """
        z_shape: (z_h, z_w)
        x_shape: (x_h, x_w)
    """
    z_2d_index_h, z_2d_index_w = torch.meshgrid(torch.arange(z_shape[0]), torch.arange(z_shape[1]))
    x_2d_index_h, x_2d_index_w = torch.meshgrid(torch.arange(x_shape[0]), torch.arange(x_shape[1]))
    z_2d_index_h = z_2d_index_h.flatten(0)
    z_2d_index_w = z_2d_index_w.flatten(0)
    x_2d_index_h = x_2d_index_h.flatten(0)
    x_2d_index_w = x_2d_index_w.flatten(0)
    concatenated_2d_index_h = torch.cat((z_2d_index_h, x_2d_index_h))
    concatenated_2d_index_w = torch.cat((z_2d_index_w, x_2d_index_w))
    diff_h = concatenated_2d_index_h[:, None] - concatenated_2d_index_h[None, :]
    diff_w = concatenated_2d_index_w[:, None] - concatenated_2d_index_w[None, :]
    z_len = z_shape[0] * z_shape[1]
    x_len = x_shape[0] * x_shape[1]
    a = torch.empty(z_len + x_len, dtype=torch.int64)
    a[:z_len] = 0
    a[z_len:] = 1
    b = a[:, None].repeat(1, z_len + x_len)
    c = a[None, :].repeat(z_len + x_len, 1)
    diff = torch.stack((diff_h, diff_w, b, c), dim=-1)
    _, indices = torch.unique(diff.view((z_len + x_len) * (z_len + x_len), 4), return_inverse=True, dim=0)
    return indices.view(z_len + x_len, z_len + x_len)

def generate_2d_concatenated_cross_attention_relative_positional_encoding_index(z_shape, x_shape):
    """
        z_shape: (z_h, z_w)
        x_shape: (x_h, x_w)
    """
    z_2d_index_h, z_2d_index_w = torch.meshgrid(torch.arange(z_shape[0]), torch.arange(z_shape[1]))
    x_2d_index_h, x_2d_index_w = torch.meshgrid(torch.arange(x_shape[0]), torch.arange(x_shape[1]))
    z_2d_index_h = z_2d_index_h.flatten(0)
    z_2d_index_w = z_2d_index_w.flatten(0)
    x_2d_index_h = x_2d_index_h.flatten(0)
    x_2d_index_w = x_2d_index_w.flatten(0)
    concatenated_2d_index_h = torch.cat((z_2d_index_h, x_2d_index_h))
    concatenated_2d_index_w = torch.cat((z_2d_index_w, x_2d_index_w))
    diff_h = x_2d_index_h[:, None] - concatenated_2d_index_h[None, :]
    diff_w = x_2d_index_w[:, None] - concatenated_2d_index_w[None, :]
    z_len = z_shape[0] * z_shape[1]
    x_len = x_shape[0] * x_shape[1]
    a = torch.empty(z_len + x_len, dtype=torch.int64)
    a[:z_len] = 0
    a[z_len:] = 1
    c = a[None, :].repeat(x_len, 1)
    diff = torch.stack((diff_h, diff_w, c), dim=-1)
    _, indices = torch.unique(diff.view(x_len * (z_len + x_len), 3), return_inverse=True, dim=0)
    return indices.view(x_len, z_len + x_len)

class RelativePosition2DEncoder(nn.Module):

    def __init__(self, num_heads, embed_size):
        super(RelativePosition2DEncoder, self).__init__()
        self.relative_position_bias_table = nn.Parameter(torch.empty((num_heads, embed_size)))
        trunc_normal_(self.relative_position_bias_table, std=0.02)

    def forward(self, attn_rpe_index):
        """
            Args:
                attn_rpe_index (torch.Tensor): (*), any shape containing indices, max(attn_rpe_index) < embed_size
            Returns:
                torch.Tensor: (1, num_heads, *)
        """
        return self.relative_position_bias_table[:, attn_rpe_index].unsqueeze(0)

def forward(self, attn_rpe_index):
    """
            Args:
                attn_rpe_index (torch.Tensor): (*), any shape containing indices, max(attn_rpe_index) < embed_size
            Returns:
                torch.Tensor: (1, num_heads, *)
        """
    return self.relative_position_bias_table[:, attn_rpe_index].unsqueeze(0)

def candidate_elimination(attn: torch.Tensor, tokens: torch.Tensor, lens_t: int, keep_ratio: float, global_index: torch.Tensor, box_mask_z: torch.Tensor):
    """
    Eliminate potential background candidates for computation reduction and noise cancellation.
    Args:
        attn (torch.Tensor): [B, num_heads, L_t + L_s, L_t + L_s], attention weights
        tokens (torch.Tensor):  [B, L_t + L_s, C], template and search region tokens
        lens_t (int): length of template
        keep_ratio (float): keep ratio of search region tokens (candidates)
        global_index (torch.Tensor): global index of search region tokens
        box_mask_z (torch.Tensor): template mask used to accumulate attention weights

    Returns:
        tokens_new (torch.Tensor): tokens after candidate elimination
        keep_index (torch.Tensor): indices of kept search region tokens
        removed_index (torch.Tensor): indices of removed search region tokens
    """
    lens_s = attn.shape[-1] - lens_t
    bs, hn, _, _ = attn.shape
    lens_keep = math.ceil(keep_ratio * lens_s)
    if lens_keep == lens_s:
        return (tokens, global_index, None)
    attn_t = attn[:, :, :lens_t, lens_t:]
    if box_mask_z is not None:
        box_mask_z = box_mask_z.unsqueeze(1).unsqueeze(-1).expand(-1, attn_t.shape[1], -1, attn_t.shape[-1])
        attn_t = attn_t[box_mask_z]
        attn_t = attn_t.view(bs, hn, -1, lens_s)
        attn_t = attn_t.mean(dim=2).mean(dim=1)
    else:
        attn_t = attn_t.mean(dim=2).mean(dim=1)
    sorted_attn, indices = torch.sort(attn_t, dim=1, descending=True)
    topk_attn, topk_idx = (sorted_attn[:, :lens_keep], indices[:, :lens_keep])
    non_topk_attn, non_topk_idx = (sorted_attn[:, lens_keep:], indices[:, lens_keep:])
    keep_index = global_index.gather(dim=1, index=topk_idx)
    removed_index = global_index.gather(dim=1, index=non_topk_idx)
    tokens_t = tokens[:, :lens_t]
    tokens_s = tokens[:, lens_t:]
    B, L, C = tokens_s.shape
    attentive_tokens = tokens_s.gather(dim=1, index=topk_idx.unsqueeze(-1).expand(B, -1, C))
    tokens_new = torch.cat([tokens_t, attentive_tokens], dim=1)
    return (tokens_new, keep_index, removed_index)

class PatchEmbed(nn.Module):
    """ 2D Image to Patch Embedding
    """

    def __init__(self, img_size=224, patch_size=16, in_chans=3, embed_dim=768, norm_layer=None, flatten=True):
        super().__init__()
        img_size = to_2tuple(img_size)
        patch_size = to_2tuple(patch_size)
        self.img_size = img_size
        self.patch_size = patch_size
        self.grid_size = (img_size[0] // patch_size[0], img_size[1] // patch_size[1])
        self.num_patches = self.grid_size[0] * self.grid_size[1]
        self.flatten = flatten
        self.proj = nn.Conv2d(in_chans, embed_dim, kernel_size=patch_size, stride=patch_size)
        self.norm = norm_layer(embed_dim) if norm_layer else nn.Identity()

    def forward(self, x):
        x = self.proj(x)
        if self.flatten:
            x = x.flatten(2).transpose(1, 2)
        x = self.norm(x)
        return x

def forward(self, x):
    x = self.proj(x)
    if self.flatten:
        x = x.flatten(2).transpose(1, 2)
    x = self.norm(x)
    return x

class AbsolutePositionalEmbedding(nn.Module):

    def __init__(self, dim, max_seq_len):
        super().__init__()
        self.emb = nn.Embedding(max_seq_len, dim)
        self.init_()

    def init_(self):
        nn.init.normal_(self.emb.weight, std=0.02)

    def forward(self, x):
        n = torch.arange(x.shape[1], device=x.device)
        return self.emb(n)[None, :, :]

def forward(self, x):
    n = torch.arange(x.shape[1], device=x.device)
    return self.emb(n)[None, :, :]

def max_neg_value(tensor):
    return -torch.finfo(tensor.dtype).max

class ScaleNorm(nn.Module):

    def __init__(self, dim, eps=1e-05):
        super().__init__()
        self.scale = dim ** (-0.5)
        self.eps = eps
        self.g = nn.Parameter(torch.ones(1))

    def forward(self, x):
        norm = torch.norm(x, dim=-1, keepdim=True) * self.scale
        return x / norm.clamp(min=self.eps) * self.g

def forward(self, x):
    norm = torch.norm(x, dim=-1, keepdim=True) * self.scale
    return x / norm.clamp(min=self.eps) * self.g

class RMSNorm(nn.Module):

    def __init__(self, dim, eps=1e-08):
        super().__init__()
        self.scale = dim ** (-0.5)
        self.eps = eps
        self.g = nn.Parameter(torch.ones(dim))

    def forward(self, x):
        norm = torch.norm(x, dim=-1, keepdim=True) * self.scale
        return x / norm.clamp(min=self.eps) * self.g

def forward(self, x):
    norm = torch.norm(x, dim=-1, keepdim=True) * self.scale
    return x / norm.clamp(min=self.eps) * self.g

class Attention(nn.Module):

    def __init__(self, dim, dim_head=DEFAULT_DIM_HEAD, heads=8, causal=False, mask=None, talking_heads=False, sparse_topk=None, use_entmax15=False, num_mem_kv=0, dropout=0.0, on_attn=False):
        super().__init__()
        if use_entmax15:
            raise NotImplementedError('Check out entmax activation instead of softmax activation!')
        self.scale = dim_head ** (-0.5)
        self.heads = heads
        self.causal = causal
        self.mask = mask
        inner_dim = dim_head * heads
        self.to_q = nn.Linear(dim, inner_dim, bias=False)
        self.to_k = nn.Linear(dim, inner_dim, bias=False)
        self.to_v = nn.Linear(dim, inner_dim, bias=False)
        self.dropout = nn.Dropout(dropout)
        self.talking_heads = talking_heads
        if talking_heads:
            self.pre_softmax_proj = nn.Parameter(torch.randn(heads, heads))
            self.post_softmax_proj = nn.Parameter(torch.randn(heads, heads))
        self.sparse_topk = sparse_topk
        self.attn_fn = F.softmax
        self.num_mem_kv = num_mem_kv
        if num_mem_kv > 0:
            self.mem_k = nn.Parameter(torch.randn(heads, num_mem_kv, dim_head))
            self.mem_v = nn.Parameter(torch.randn(heads, num_mem_kv, dim_head))
        self.attn_on_attn = on_attn
        self.to_out = nn.Sequential(nn.Linear(inner_dim, dim * 2), nn.GLU()) if on_attn else nn.Linear(inner_dim, dim)

    def forward(self, x, context=None, mask=None, context_mask=None, rel_pos=None, sinusoidal_emb=None, prev_attn=None, mem=None):
        b, n, _, h, talking_heads, device = (*x.shape, self.heads, self.talking_heads, x.device)
        kv_input = default(context, x)
        q_input = x
        k_input = kv_input
        v_input = kv_input
        if exists(mem):
            k_input = torch.cat((mem, k_input), dim=-2)
            v_input = torch.cat((mem, v_input), dim=-2)
        if exists(sinusoidal_emb):
            offset = k_input.shape[-2] - q_input.shape[-2]
            q_input = q_input + sinusoidal_emb(q_input, offset=offset)
            k_input = k_input + sinusoidal_emb(k_input)
        q = self.to_q(q_input)
        k = self.to_k(k_input)
        v = self.to_v(v_input)
        q, k, v = map(lambda t: rearrange(t, 'b n (h d) -> b h n d', h=h), (q, k, v))
        input_mask = None
        if any(map(exists, (mask, context_mask))):
            q_mask = default(mask, lambda: torch.ones((b, n), device=device).bool())
            k_mask = q_mask if not exists(context) else context_mask
            k_mask = default(k_mask, lambda: torch.ones((b, k.shape[-2]), device=device).bool())
            q_mask = rearrange(q_mask, 'b i -> b () i ()')
            k_mask = rearrange(k_mask, 'b j -> b () () j')
            input_mask = q_mask * k_mask
        if self.num_mem_kv > 0:
            mem_k, mem_v = map(lambda t: repeat(t, 'h n d -> b h n d', b=b), (self.mem_k, self.mem_v))
            k = torch.cat((mem_k, k), dim=-2)
            v = torch.cat((mem_v, v), dim=-2)
            if exists(input_mask):
                input_mask = F.pad(input_mask, (self.num_mem_kv, 0), value=True)
        dots = einsum('b h i d, b h j d -> b h i j', q, k) * self.scale
        mask_value = max_neg_value(dots)
        if exists(prev_attn):
            dots = dots + prev_attn
        pre_softmax_attn = dots
        if talking_heads:
            dots = einsum('b h i j, h k -> b k i j', dots, self.pre_softmax_proj).contiguous()
        if exists(rel_pos):
            dots = rel_pos(dots)
        if exists(input_mask):
            dots.masked_fill_(~input_mask, mask_value)
            del input_mask
        if self.causal:
            i, j = dots.shape[-2:]
            r = torch.arange(i, device=device)
            mask = rearrange(r, 'i -> () () i ()') < rearrange(r, 'j -> () () () j')
            mask = F.pad(mask, (j - i, 0), value=False)
            dots.masked_fill_(mask, mask_value)
            del mask
        if exists(self.sparse_topk) and self.sparse_topk < dots.shape[-1]:
            top, _ = dots.topk(self.sparse_topk, dim=-1)
            vk = top[..., -1].unsqueeze(-1).expand_as(dots)
            mask = dots < vk
            dots.masked_fill_(mask, mask_value)
            del mask
        attn = self.attn_fn(dots, dim=-1)
        post_softmax_attn = attn
        attn = self.dropout(attn)
        if talking_heads:
            attn = einsum('b h i j, h k -> b k i j', attn, self.post_softmax_proj).contiguous()
        out = einsum('b h i j, b h j d -> b h i d', attn, v)
        out = rearrange(out, 'b h n d -> b n (h d)')
        intermediates = Intermediates(pre_softmax_attn=pre_softmax_attn, post_softmax_attn=post_softmax_attn)
        return (self.to_out(out), intermediates)

def forward(self, x, context=None, mask=None, context_mask=None, rel_pos=None, sinusoidal_emb=None, prev_attn=None, mem=None):
    b, n, _, h, talking_heads, device = (*x.shape, self.heads, self.talking_heads, x.device)
    kv_input = default(context, x)
    q_input = x
    k_input = kv_input
    v_input = kv_input
    if exists(mem):
        k_input = torch.cat((mem, k_input), dim=-2)
        v_input = torch.cat((mem, v_input), dim=-2)
    if exists(sinusoidal_emb):
        offset = k_input.shape[-2] - q_input.shape[-2]
        q_input = q_input + sinusoidal_emb(q_input, offset=offset)
        k_input = k_input + sinusoidal_emb(k_input)
    q = self.to_q(q_input)
    k = self.to_k(k_input)
    v = self.to_v(v_input)
    q, k, v = map(lambda t: rearrange(t, 'b n (h d) -> b h n d', h=h), (q, k, v))
    input_mask = None
    if any(map(exists, (mask, context_mask))):
        q_mask = default(mask, lambda: torch.ones((b, n), device=device).bool())
        k_mask = q_mask if not exists(context) else context_mask
        k_mask = default(k_mask, lambda: torch.ones((b, k.shape[-2]), device=device).bool())
        q_mask = rearrange(q_mask, 'b i -> b () i ()')
        k_mask = rearrange(k_mask, 'b j -> b () () j')
        input_mask = q_mask * k_mask
    if self.num_mem_kv > 0:
        mem_k, mem_v = map(lambda t: repeat(t, 'h n d -> b h n d', b=b), (self.mem_k, self.mem_v))
        k = torch.cat((mem_k, k), dim=-2)
        v = torch.cat((mem_v, v), dim=-2)
        if exists(input_mask):
            input_mask = F.pad(input_mask, (self.num_mem_kv, 0), value=True)
    dots = einsum('b h i d, b h j d -> b h i j', q, k) * self.scale
    mask_value = max_neg_value(dots)
    if exists(prev_attn):
        dots = dots + prev_attn
    pre_softmax_attn = dots
    if talking_heads:
        dots = einsum('b h i j, h k -> b k i j', dots, self.pre_softmax_proj).contiguous()
    if exists(rel_pos):
        dots = rel_pos(dots)
    if exists(input_mask):
        dots.masked_fill_(~input_mask, mask_value)
        del input_mask
    if self.causal:
        i, j = dots.shape[-2:]
        r = torch.arange(i, device=device)
        mask = rearrange(r, 'i -> () () i ()') < rearrange(r, 'j -> () () () j')
        mask = F.pad(mask, (j - i, 0), value=False)
        dots.masked_fill_(mask, mask_value)
        del mask
    if exists(self.sparse_topk) and self.sparse_topk < dots.shape[-1]:
        top, _ = dots.topk(self.sparse_topk, dim=-1)
        vk = top[..., -1].unsqueeze(-1).expand_as(dots)
        mask = dots < vk
        dots.masked_fill_(mask, mask_value)
        del mask
    attn = self.attn_fn(dots, dim=-1)
    post_softmax_attn = attn
    attn = self.dropout(attn)
    if talking_heads:
        attn = einsum('b h i j, h k -> b k i j', attn, self.post_softmax_proj).contiguous()
    out = einsum('b h i j, b h j d -> b h i d', attn, v)
    out = rearrange(out, 'b h n d -> b n (h d)')
    intermediates = Intermediates(pre_softmax_attn=pre_softmax_attn, post_softmax_attn=post_softmax_attn)
    return (self.to_out(out), intermediates)

class TransformerWrapper(nn.Module):

    def __init__(self, *, num_tokens, max_seq_len, attn_layers, emb_dim=None, max_mem_len=0.0, emb_dropout=0.0, num_memory_tokens=None, tie_embedding=False, use_pos_emb=True):
        super().__init__()
        assert isinstance(attn_layers, AttentionLayers), 'attention layers must be one of Encoder or Decoder'
        dim = attn_layers.dim
        emb_dim = default(emb_dim, dim)
        self.max_seq_len = max_seq_len
        self.max_mem_len = max_mem_len
        self.num_tokens = num_tokens
        self.token_emb = nn.Embedding(num_tokens, emb_dim)
        self.pos_emb = AbsolutePositionalEmbedding(emb_dim, max_seq_len) if use_pos_emb and (not attn_layers.has_pos_emb) else always(0)
        self.emb_dropout = nn.Dropout(emb_dropout)
        self.project_emb = nn.Linear(emb_dim, dim) if emb_dim != dim else nn.Identity()
        self.attn_layers = attn_layers
        self.norm = nn.LayerNorm(dim)
        self.init_()
        self.to_logits = nn.Linear(dim, num_tokens) if not tie_embedding else lambda t: t @ self.token_emb.weight.t()
        num_memory_tokens = default(num_memory_tokens, 0)
        self.num_memory_tokens = num_memory_tokens
        if num_memory_tokens > 0:
            self.memory_tokens = nn.Parameter(torch.randn(num_memory_tokens, dim))
            if hasattr(attn_layers, 'num_memory_tokens'):
                attn_layers.num_memory_tokens = num_memory_tokens

    def init_(self):
        nn.init.normal_(self.token_emb.weight, std=0.02)

    def forward(self, x, return_embeddings=False, mask=None, return_mems=False, return_attn=False, mems=None, **kwargs):
        b, n, device, num_mem = (*x.shape, x.device, self.num_memory_tokens)
        x = self.token_emb(x)
        x += self.pos_emb(x)
        x = self.emb_dropout(x)
        x = self.project_emb(x)
        if num_mem > 0:
            mem = repeat(self.memory_tokens, 'n d -> b n d', b=b)
            x = torch.cat((mem, x), dim=1)
            if exists(mask):
                mask = F.pad(mask, (num_mem, 0), value=True)
        x, intermediates = self.attn_layers(x, mask=mask, mems=mems, return_hiddens=True, **kwargs)
        x = self.norm(x)
        mem, x = (x[:, :num_mem], x[:, num_mem:])
        out = self.to_logits(x) if not return_embeddings else x
        if return_mems:
            hiddens = intermediates.hiddens
            new_mems = list(map(lambda pair: torch.cat(pair, dim=-2), zip(mems, hiddens))) if exists(mems) else hiddens
            new_mems = list(map(lambda t: t[..., -self.max_mem_len:, :].detach(), new_mems))
            return (out, new_mems)
        if return_attn:
            attn_maps = list(map(lambda t: t.post_softmax_attn, intermediates.attn_intermediates))
            return (out, attn_maps)
        return out

def forward(self, x, return_embeddings=False, mask=None, return_mems=False, return_attn=False, mems=None, **kwargs):
    b, n, device, num_mem = (*x.shape, x.device, self.num_memory_tokens)
    x = self.token_emb(x)
    x += self.pos_emb(x)
    x = self.emb_dropout(x)
    x = self.project_emb(x)
    if num_mem > 0:
        mem = repeat(self.memory_tokens, 'n d -> b n d', b=b)
        x = torch.cat((mem, x), dim=1)
        if exists(mask):
            mask = F.pad(mask, (num_mem, 0), value=True)
    x, intermediates = self.attn_layers(x, mask=mask, mems=mems, return_hiddens=True, **kwargs)
    x = self.norm(x)
    mem, x = (x[:, :num_mem], x[:, num_mem:])
    out = self.to_logits(x) if not return_embeddings else x
    if return_mems:
        hiddens = intermediates.hiddens
        new_mems = list(map(lambda pair: torch.cat(pair, dim=-2), zip(mems, hiddens))) if exists(mems) else hiddens
        new_mems = list(map(lambda t: t[..., -self.max_mem_len:, :].detach(), new_mems))
        return (out, new_mems)
    if return_attn:
        attn_maps = list(map(lambda t: t.post_softmax_attn, intermediates.attn_intermediates))
        return (out, attn_maps)
    return out

def max_neg_value(t):
    return -torch.finfo(t.dtype).max

class LinearAttention(nn.Module):

    def __init__(self, dim, heads=4, dim_head=32):
        super().__init__()
        self.heads = heads
        hidden_dim = dim_head * heads
        self.to_qkv = nn.Conv2d(dim, hidden_dim * 3, 1, bias=False)
        self.to_out = nn.Conv2d(hidden_dim, dim, 1)

    def forward(self, x):
        b, c, h, w = x.shape
        qkv = self.to_qkv(x)
        q, k, v = rearrange(qkv, 'b (qkv heads c) h w -> qkv b heads c (h w)', heads=self.heads, qkv=3)
        k = k.softmax(dim=-1)
        context = torch.einsum('bhdn,bhen->bhde', k, v)
        out = torch.einsum('bhde,bhdn->bhen', context, q)
        out = rearrange(out, 'b heads c (h w) -> b (heads c) h w', heads=self.heads, h=h, w=w)
        return self.to_out(out)

def forward(self, x):
    b, c, h, w = x.shape
    qkv = self.to_qkv(x)
    q, k, v = rearrange(qkv, 'b (qkv heads c) h w -> qkv b heads c (h w)', heads=self.heads, qkv=3)
    k = k.softmax(dim=-1)
    context = torch.einsum('bhdn,bhen->bhde', k, v)
    out = torch.einsum('bhde,bhdn->bhen', context, q)
    out = rearrange(out, 'b heads c (h w) -> b (heads c) h w', heads=self.heads, h=h, w=w)
    return self.to_out(out)

class SpatialSelfAttention(nn.Module):

    def __init__(self, in_channels):
        super().__init__()
        self.in_channels = in_channels
        self.norm = Normalize(in_channels)
        self.q = torch.nn.Conv2d(in_channels, in_channels, kernel_size=1, stride=1, padding=0)
        self.k = torch.nn.Conv2d(in_channels, in_channels, kernel_size=1, stride=1, padding=0)
        self.v = torch.nn.Conv2d(in_channels, in_channels, kernel_size=1, stride=1, padding=0)
        self.proj_out = torch.nn.Conv2d(in_channels, in_channels, kernel_size=1, stride=1, padding=0)

    def forward(self, x):
        h_ = x
        h_ = self.norm(h_)
        q = self.q(h_)
        k = self.k(h_)
        v = self.v(h_)
        b, c, h, w = q.shape
        q = rearrange(q, 'b c h w -> b (h w) c')
        k = rearrange(k, 'b c h w -> b c (h w)')
        w_ = torch.einsum('bij,bjk->bik', q, k)
        w_ = w_ * int(c) ** (-0.5)
        w_ = torch.nn.functional.softmax(w_, dim=2)
        v = rearrange(v, 'b c h w -> b c (h w)')
        w_ = rearrange(w_, 'b i j -> b j i')
        h_ = torch.einsum('bij,bjk->bik', v, w_)
        h_ = rearrange(h_, 'b c (h w) -> b c h w', h=h)
        h_ = self.proj_out(h_)
        return x + h_

def forward(self, x):
    h_ = x
    h_ = self.norm(h_)
    q = self.q(h_)
    k = self.k(h_)
    v = self.v(h_)
    b, c, h, w = q.shape
    q = rearrange(q, 'b c h w -> b (h w) c')
    k = rearrange(k, 'b c h w -> b c (h w)')
    w_ = torch.einsum('bij,bjk->bik', q, k)
    w_ = w_ * int(c) ** (-0.5)
    w_ = torch.nn.functional.softmax(w_, dim=2)
    v = rearrange(v, 'b c h w -> b c (h w)')
    w_ = rearrange(w_, 'b i j -> b j i')
    h_ = torch.einsum('bij,bjk->bik', v, w_)
    h_ = rearrange(h_, 'b c (h w) -> b c h w', h=h)
    h_ = self.proj_out(h_)
    return x + h_

class CrossAttention(nn.Module):

    def __init__(self, query_dim, context_dim=None, heads=8, dim_head=64, dropout=0.0):
        super().__init__()
        inner_dim = dim_head * heads
        context_dim = default(context_dim, query_dim)
        self.scale = dim_head ** (-0.5)
        self.heads = heads
        self.to_q = nn.Linear(query_dim, inner_dim, bias=False)
        self.to_k = nn.Linear(context_dim, inner_dim, bias=False)
        self.to_v = nn.Linear(context_dim, inner_dim, bias=False)
        self.to_out = nn.Sequential(nn.Linear(inner_dim, query_dim), nn.Dropout(dropout))

    def forward(self, x, context=None, mask=None):
        h = self.heads
        q = self.to_q(x)
        context = default(context, x)
        k = self.to_k(context)
        v = self.to_v(context)
        q, k, v = map(lambda t: rearrange(t, 'b n (h d) -> (b h) n d', h=h), (q, k, v))
        sim = einsum('b i d, b j d -> b i j', q, k) * self.scale
        if exists(mask):
            mask = rearrange(mask, 'b ... -> b (...)')
            max_neg_value = -torch.finfo(sim.dtype).max
            mask = repeat(mask, 'b j -> (b h) () j', h=h)
            sim.masked_fill_(~mask, max_neg_value)
        attn = sim.softmax(dim=-1)
        out = einsum('b i j, b j d -> b i d', attn, v)
        out = rearrange(out, '(b h) n d -> b n (h d)', h=h)
        return self.to_out(out)

def forward(self, x, context=None, mask=None):
    h = self.heads
    q = self.to_q(x)
    context = default(context, x)
    k = self.to_k(context)
    v = self.to_v(context)
    q, k, v = map(lambda t: rearrange(t, 'b n (h d) -> (b h) n d', h=h), (q, k, v))
    sim = einsum('b i d, b j d -> b i j', q, k) * self.scale
    if exists(mask):
        mask = rearrange(mask, 'b ... -> b (...)')
        max_neg_value = -torch.finfo(sim.dtype).max
        mask = repeat(mask, 'b j -> (b h) () j', h=h)
        sim.masked_fill_(~mask, max_neg_value)
    attn = sim.softmax(dim=-1)
    out = einsum('b i j, b j d -> b i d', attn, v)
    out = rearrange(out, '(b h) n d -> b n (h d)', h=h)
    return self.to_out(out)

class SpatialTransformer(nn.Module):
    """
    Transformer block for image-like data.
    First, project the input (aka embedding)
    and reshape to b, t, d.
    Then apply standard transformer action.
    Finally, reshape to image
    """

    def __init__(self, in_channels, n_heads, d_head, depth=1, dropout=0.0, context_dim=None):
        super().__init__()
        self.in_channels = in_channels
        inner_dim = n_heads * d_head
        self.norm = Normalize(in_channels)
        self.proj_in = nn.Conv2d(in_channels, inner_dim, kernel_size=1, stride=1, padding=0)
        self.transformer_blocks = nn.ModuleList([BasicTransformerBlock(inner_dim, n_heads, d_head, dropout=dropout, context_dim=context_dim) for d in range(depth)])
        self.proj_out = zero_module(nn.Conv2d(inner_dim, in_channels, kernel_size=1, stride=1, padding=0))

    def forward(self, x, context=None):
        b, c, h, w = x.shape
        x_in = x
        x = self.norm(x)
        x = self.proj_in(x)
        x = rearrange(x, 'b c h w -> b (h w) c')
        for block in self.transformer_blocks:
            x = block(x, context=context)
        x = rearrange(x, 'b (h w) c -> b c h w', h=h, w=w)
        x = self.proj_out(x)
        return x + x_in

def forward(self, x, context=None):
    b, c, h, w = x.shape
    x_in = x
    x = self.norm(x)
    x = self.proj_in(x)
    x = rearrange(x, 'b c h w -> b (h w) c')
    for block in self.transformer_blocks:
        x = block(x, context=context)
    x = rearrange(x, 'b (h w) c -> b c h w', h=h, w=w)
    x = self.proj_out(x)
    return x + x_in

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

def __init__(self, parameters, deterministic=False):
    self.parameters = parameters
    self.mean, self.logvar = torch.chunk(parameters, 2, dim=1)
    self.logvar = torch.clamp(self.logvar, -30.0, 20.0)
    self.deterministic = deterministic
    self.std = torch.exp(0.5 * self.logvar)
    self.var = torch.exp(self.logvar)
    if self.deterministic:
        self.var = self.std = torch.zeros_like(self.mean).to(device=self.parameters.device)

def normal_kl(mean1, logvar1, mean2, logvar2):
    """
    source: https://github.com/openai/guided-diffusion/blob/27c20a8fab9cb472df5d6bdd6c8d11c8f430b924/guided_diffusion/losses.py#L12
    Compute the KL divergence between two gaussians.
    Shapes are automatically broadcasted, so batches can be compared to
    scalars, among other use cases.
    """
    tensor = None
    for obj in (mean1, logvar1, mean2, logvar2):
        if isinstance(obj, torch.Tensor):
            tensor = obj
            break
    assert tensor is not None, 'at least one argument must be a Tensor'
    logvar1, logvar2 = [x if isinstance(x, torch.Tensor) else torch.tensor(x).to(tensor) for x in (logvar1, logvar2)]
    return 0.5 * (-1.0 + logvar2 - logvar1 + torch.exp(logvar1 - logvar2) + (mean1 - mean2) ** 2 * torch.exp(-logvar2))

def measure_perplexity(predicted_indices, n_embed):
    encodings = F.one_hot(predicted_indices, n_embed).float().reshape(-1, n_embed)
    avg_probs = encodings.mean(0)
    perplexity = (-(avg_probs * torch.log(avg_probs + 1e-10)).sum()).exp()
    cluster_use = torch.sum(avg_probs > 0)
    return (perplexity, cluster_use)

class VQLPIPSWithDiscriminator(nn.Module):

    def __init__(self, disc_start, codebook_weight=1.0, pixelloss_weight=1.0, disc_num_layers=3, disc_in_channels=3, disc_factor=1.0, disc_weight=1.0, perceptual_weight=1.0, use_actnorm=False, disc_conditional=False, disc_ndf=64, disc_loss='hinge', n_classes=None, perceptual_loss='lpips', pixel_loss='l1'):
        super().__init__()
        assert disc_loss in ['hinge', 'vanilla']
        assert perceptual_loss in ['lpips', 'clips', 'dists']
        assert pixel_loss in ['l1', 'l2']
        self.codebook_weight = codebook_weight
        self.pixel_weight = pixelloss_weight
        if perceptual_loss == 'lpips':
            print(f'{self.__class__.__name__}: Running with LPIPS.')
            self.perceptual_loss = LPIPS().eval()
        else:
            raise ValueError(f'Unknown perceptual loss: >> {perceptual_loss} <<')
        self.perceptual_weight = perceptual_weight
        if pixel_loss == 'l1':
            self.pixel_loss = l1
        else:
            self.pixel_loss = l2
        self.discriminator = NLayerDiscriminator(input_nc=disc_in_channels, n_layers=disc_num_layers, use_actnorm=use_actnorm, ndf=disc_ndf).apply(weights_init)
        self.discriminator_iter_start = disc_start
        if disc_loss == 'hinge':
            self.disc_loss = hinge_d_loss
        elif disc_loss == 'vanilla':
            self.disc_loss = vanilla_d_loss
        else:
            raise ValueError(f"Unknown GAN loss '{disc_loss}'.")
        print(f'VQLPIPSWithDiscriminator running with {disc_loss} loss.')
        self.disc_factor = disc_factor
        self.discriminator_weight = disc_weight
        self.disc_conditional = disc_conditional
        self.n_classes = n_classes

    def calculate_adaptive_weight(self, nll_loss, g_loss, last_layer=None):
        if last_layer is not None:
            nll_grads = torch.autograd.grad(nll_loss, last_layer, retain_graph=True)[0]
            g_grads = torch.autograd.grad(g_loss, last_layer, retain_graph=True)[0]
        else:
            nll_grads = torch.autograd.grad(nll_loss, self.last_layer[0], retain_graph=True)[0]
            g_grads = torch.autograd.grad(g_loss, self.last_layer[0], retain_graph=True)[0]
        d_weight = torch.norm(nll_grads) / (torch.norm(g_grads) + 0.0001)
        d_weight = torch.clamp(d_weight, 0.0, 10000.0).detach()
        d_weight = d_weight * self.discriminator_weight
        return d_weight

    def forward(self, codebook_loss, inputs, reconstructions, optimizer_idx, global_step, last_layer=None, cond=None, split='train', predicted_indices=None):
        if not exists(codebook_loss):
            codebook_loss = torch.tensor([0.0]).to(inputs.device)
        rec_loss = self.pixel_loss(inputs.contiguous(), reconstructions.contiguous())
        if self.perceptual_weight > 0:
            p_loss = self.perceptual_loss(inputs.contiguous(), reconstructions.contiguous())
            rec_loss = rec_loss + self.perceptual_weight * p_loss
        else:
            p_loss = torch.tensor([0.0])
        nll_loss = rec_loss
        nll_loss = torch.mean(nll_loss)
        if optimizer_idx == 0:
            if cond is None:
                assert not self.disc_conditional
                logits_fake = self.discriminator(reconstructions.contiguous())
            else:
                assert self.disc_conditional
                logits_fake = self.discriminator(torch.cat((reconstructions.contiguous(), cond), dim=1))
            g_loss = -torch.mean(logits_fake)
            try:
                d_weight = self.calculate_adaptive_weight(nll_loss, g_loss, last_layer=last_layer)
            except RuntimeError:
                assert not self.training
                d_weight = torch.tensor(0.0)
            disc_factor = adopt_weight(self.disc_factor, global_step, threshold=self.discriminator_iter_start)
            loss = nll_loss + d_weight * disc_factor * g_loss + self.codebook_weight * codebook_loss.mean()
            log = {'{}/total_loss'.format(split): loss.clone().detach().mean(), '{}/quant_loss'.format(split): codebook_loss.detach().mean(), '{}/nll_loss'.format(split): nll_loss.detach().mean(), '{}/rec_loss'.format(split): rec_loss.detach().mean(), '{}/p_loss'.format(split): p_loss.detach().mean(), '{}/d_weight'.format(split): d_weight.detach(), '{}/disc_factor'.format(split): torch.tensor(disc_factor), '{}/g_loss'.format(split): g_loss.detach().mean()}
            if predicted_indices is not None:
                assert self.n_classes is not None
                with torch.no_grad():
                    perplexity, cluster_usage = measure_perplexity(predicted_indices, self.n_classes)
                log[f'{split}/perplexity'] = perplexity
                log[f'{split}/cluster_usage'] = cluster_usage
            return (loss, log)
        if optimizer_idx == 1:
            if cond is None:
                logits_real = self.discriminator(inputs.contiguous().detach())
                logits_fake = self.discriminator(reconstructions.contiguous().detach())
            else:
                logits_real = self.discriminator(torch.cat((inputs.contiguous().detach(), cond), dim=1))
                logits_fake = self.discriminator(torch.cat((reconstructions.contiguous().detach(), cond), dim=1))
            disc_factor = adopt_weight(self.disc_factor, global_step, threshold=self.discriminator_iter_start)
            d_loss = disc_factor * self.disc_loss(logits_real, logits_fake)
            log = {'{}/disc_loss'.format(split): d_loss.clone().detach().mean(), '{}/logits_real'.format(split): logits_real.detach().mean(), '{}/logits_fake'.format(split): logits_fake.detach().mean()}
            return (d_loss, log)

def calculate_adaptive_weight(self, nll_loss, g_loss, last_layer=None):
    if last_layer is not None:
        nll_grads = torch.autograd.grad(nll_loss, last_layer, retain_graph=True)[0]
        g_grads = torch.autograd.grad(g_loss, last_layer, retain_graph=True)[0]
    else:
        nll_grads = torch.autograd.grad(nll_loss, self.last_layer[0], retain_graph=True)[0]
        g_grads = torch.autograd.grad(g_loss, self.last_layer[0], retain_graph=True)[0]
    d_weight = torch.norm(nll_grads) / (torch.norm(g_grads) + 0.0001)
    d_weight = torch.clamp(d_weight, 0.0, 10000.0).detach()
    d_weight = d_weight * self.discriminator_weight
    return d_weight

def forward(self, codebook_loss, inputs, reconstructions, optimizer_idx, global_step, last_layer=None, cond=None, split='train', predicted_indices=None):
    if not exists(codebook_loss):
        codebook_loss = torch.tensor([0.0]).to(inputs.device)
    rec_loss = self.pixel_loss(inputs.contiguous(), reconstructions.contiguous())
    if self.perceptual_weight > 0:
        p_loss = self.perceptual_loss(inputs.contiguous(), reconstructions.contiguous())
        rec_loss = rec_loss + self.perceptual_weight * p_loss
    else:
        p_loss = torch.tensor([0.0])
    nll_loss = rec_loss
    nll_loss = torch.mean(nll_loss)
    if optimizer_idx == 0:
        if cond is None:
            assert not self.disc_conditional
            logits_fake = self.discriminator(reconstructions.contiguous())
        else:
            assert self.disc_conditional
            logits_fake = self.discriminator(torch.cat((reconstructions.contiguous(), cond), dim=1))
        g_loss = -torch.mean(logits_fake)
        try:
            d_weight = self.calculate_adaptive_weight(nll_loss, g_loss, last_layer=last_layer)
        except RuntimeError:
            assert not self.training
            d_weight = torch.tensor(0.0)
        disc_factor = adopt_weight(self.disc_factor, global_step, threshold=self.discriminator_iter_start)
        loss = nll_loss + d_weight * disc_factor * g_loss + self.codebook_weight * codebook_loss.mean()
        log = {'{}/total_loss'.format(split): loss.clone().detach().mean(), '{}/quant_loss'.format(split): codebook_loss.detach().mean(), '{}/nll_loss'.format(split): nll_loss.detach().mean(), '{}/rec_loss'.format(split): rec_loss.detach().mean(), '{}/p_loss'.format(split): p_loss.detach().mean(), '{}/d_weight'.format(split): d_weight.detach(), '{}/disc_factor'.format(split): torch.tensor(disc_factor), '{}/g_loss'.format(split): g_loss.detach().mean()}
        if predicted_indices is not None:
            assert self.n_classes is not None
            with torch.no_grad():
                perplexity, cluster_usage = measure_perplexity(predicted_indices, self.n_classes)
            log[f'{split}/perplexity'] = perplexity
            log[f'{split}/cluster_usage'] = cluster_usage
        return (loss, log)
    if optimizer_idx == 1:
        if cond is None:
            logits_real = self.discriminator(inputs.contiguous().detach())
            logits_fake = self.discriminator(reconstructions.contiguous().detach())
        else:
            logits_real = self.discriminator(torch.cat((inputs.contiguous().detach(), cond), dim=1))
            logits_fake = self.discriminator(torch.cat((reconstructions.contiguous().detach(), cond), dim=1))
        disc_factor = adopt_weight(self.disc_factor, global_step, threshold=self.discriminator_iter_start)
        d_loss = disc_factor * self.disc_loss(logits_real, logits_fake)
        log = {'{}/disc_loss'.format(split): d_loss.clone().detach().mean(), '{}/logits_real'.format(split): logits_real.detach().mean(), '{}/logits_fake'.format(split): logits_fake.detach().mean()}
        return (d_loss, log)

class LPIPSWithDiscriminator(nn.Module):

    def __init__(self, disc_start, logvar_init=0.0, kl_weight=1.0, pixelloss_weight=1.0, disc_num_layers=3, disc_in_channels=3, disc_factor=1.0, disc_weight=1.0, perceptual_weight=1.0, use_actnorm=False, disc_conditional=False, disc_loss='hinge'):
        super().__init__()
        assert disc_loss in ['hinge', 'vanilla']
        self.kl_weight = kl_weight
        self.pixel_weight = pixelloss_weight
        self.perceptual_loss = LPIPS().eval()
        self.perceptual_weight = perceptual_weight
        self.logvar = nn.Parameter(torch.ones(size=()) * logvar_init)
        self.discriminator = NLayerDiscriminator(input_nc=disc_in_channels, n_layers=disc_num_layers, use_actnorm=use_actnorm).apply(weights_init)
        self.discriminator_iter_start = disc_start
        self.disc_loss = hinge_d_loss if disc_loss == 'hinge' else vanilla_d_loss
        self.disc_factor = disc_factor
        self.discriminator_weight = disc_weight
        self.disc_conditional = disc_conditional

    def calculate_adaptive_weight(self, nll_loss, g_loss, last_layer=None):
        if last_layer is not None:
            nll_grads = torch.autograd.grad(nll_loss, last_layer, retain_graph=True)[0]
            g_grads = torch.autograd.grad(g_loss, last_layer, retain_graph=True)[0]
        else:
            nll_grads = torch.autograd.grad(nll_loss, self.last_layer[0], retain_graph=True)[0]
            g_grads = torch.autograd.grad(g_loss, self.last_layer[0], retain_graph=True)[0]
        d_weight = torch.norm(nll_grads) / (torch.norm(g_grads) + 0.0001)
        d_weight = torch.clamp(d_weight, 0.0, 10000.0).detach()
        d_weight = d_weight * self.discriminator_weight
        return d_weight

    def forward(self, inputs, reconstructions, posteriors, optimizer_idx, global_step, last_layer=None, cond=None, split='train', weights=None):
        rec_loss = torch.abs(inputs.contiguous() - reconstructions.contiguous())
        if self.perceptual_weight > 0:
            p_loss = self.perceptual_loss(inputs.contiguous(), reconstructions.contiguous())
            rec_loss = rec_loss + self.perceptual_weight * p_loss
        nll_loss = rec_loss / torch.exp(self.logvar) + self.logvar
        weighted_nll_loss = nll_loss
        if weights is not None:
            weighted_nll_loss = weights * nll_loss
        weighted_nll_loss = torch.sum(weighted_nll_loss) / weighted_nll_loss.shape[0]
        nll_loss = torch.sum(nll_loss) / nll_loss.shape[0]
        kl_loss = posteriors.kl()
        kl_loss = torch.sum(kl_loss) / kl_loss.shape[0]
        if optimizer_idx == 0:
            if cond is None:
                assert not self.disc_conditional
                logits_fake = self.discriminator(reconstructions.contiguous())
            else:
                assert self.disc_conditional
                logits_fake = self.discriminator(torch.cat((reconstructions.contiguous(), cond), dim=1))
            g_loss = -torch.mean(logits_fake)
            if self.disc_factor > 0.0:
                try:
                    d_weight = self.calculate_adaptive_weight(nll_loss, g_loss, last_layer=last_layer)
                except RuntimeError:
                    assert not self.training
                    d_weight = torch.tensor(0.0)
            else:
                d_weight = torch.tensor(0.0)
            disc_factor = adopt_weight(self.disc_factor, global_step, threshold=self.discriminator_iter_start)
            loss = weighted_nll_loss + self.kl_weight * kl_loss + d_weight * disc_factor * g_loss
            log = {'{}/total_loss'.format(split): loss.clone().detach().mean(), '{}/logvar'.format(split): self.logvar.detach(), '{}/kl_loss'.format(split): kl_loss.detach().mean(), '{}/nll_loss'.format(split): nll_loss.detach().mean(), '{}/rec_loss'.format(split): rec_loss.detach().mean(), '{}/d_weight'.format(split): d_weight.detach(), '{}/disc_factor'.format(split): torch.tensor(disc_factor), '{}/g_loss'.format(split): g_loss.detach().mean()}
            return (loss, log)
        if optimizer_idx == 1:
            if cond is None:
                logits_real = self.discriminator(inputs.contiguous().detach())
                logits_fake = self.discriminator(reconstructions.contiguous().detach())
            else:
                logits_real = self.discriminator(torch.cat((inputs.contiguous().detach(), cond), dim=1))
                logits_fake = self.discriminator(torch.cat((reconstructions.contiguous().detach(), cond), dim=1))
            disc_factor = adopt_weight(self.disc_factor, global_step, threshold=self.discriminator_iter_start)
            d_loss = disc_factor * self.disc_loss(logits_real, logits_fake)
            log = {'{}/disc_loss'.format(split): d_loss.clone().detach().mean(), '{}/logits_real'.format(split): logits_real.detach().mean(), '{}/logits_fake'.format(split): logits_fake.detach().mean()}
            return (d_loss, log)

def calculate_adaptive_weight(self, nll_loss, g_loss, last_layer=None):
    if last_layer is not None:
        nll_grads = torch.autograd.grad(nll_loss, last_layer, retain_graph=True)[0]
        g_grads = torch.autograd.grad(g_loss, last_layer, retain_graph=True)[0]
    else:
        nll_grads = torch.autograd.grad(nll_loss, self.last_layer[0], retain_graph=True)[0]
        g_grads = torch.autograd.grad(g_loss, self.last_layer[0], retain_graph=True)[0]
    d_weight = torch.norm(nll_grads) / (torch.norm(g_grads) + 0.0001)
    d_weight = torch.clamp(d_weight, 0.0, 10000.0).detach()
    d_weight = d_weight * self.discriminator_weight
    return d_weight

def forward(self, inputs, reconstructions, posteriors, optimizer_idx, global_step, last_layer=None, cond=None, split='train', weights=None):
    rec_loss = torch.abs(inputs.contiguous() - reconstructions.contiguous())
    if self.perceptual_weight > 0:
        p_loss = self.perceptual_loss(inputs.contiguous(), reconstructions.contiguous())
        rec_loss = rec_loss + self.perceptual_weight * p_loss
    nll_loss = rec_loss / torch.exp(self.logvar) + self.logvar
    weighted_nll_loss = nll_loss
    if weights is not None:
        weighted_nll_loss = weights * nll_loss
    weighted_nll_loss = torch.sum(weighted_nll_loss) / weighted_nll_loss.shape[0]
    nll_loss = torch.sum(nll_loss) / nll_loss.shape[0]
    kl_loss = posteriors.kl()
    kl_loss = torch.sum(kl_loss) / kl_loss.shape[0]
    if optimizer_idx == 0:
        if cond is None:
            assert not self.disc_conditional
            logits_fake = self.discriminator(reconstructions.contiguous())
        else:
            assert self.disc_conditional
            logits_fake = self.discriminator(torch.cat((reconstructions.contiguous(), cond), dim=1))
        g_loss = -torch.mean(logits_fake)
        if self.disc_factor > 0.0:
            try:
                d_weight = self.calculate_adaptive_weight(nll_loss, g_loss, last_layer=last_layer)
            except RuntimeError:
                assert not self.training
                d_weight = torch.tensor(0.0)
        else:
            d_weight = torch.tensor(0.0)
        disc_factor = adopt_weight(self.disc_factor, global_step, threshold=self.discriminator_iter_start)
        loss = weighted_nll_loss + self.kl_weight * kl_loss + d_weight * disc_factor * g_loss
        log = {'{}/total_loss'.format(split): loss.clone().detach().mean(), '{}/logvar'.format(split): self.logvar.detach(), '{}/kl_loss'.format(split): kl_loss.detach().mean(), '{}/nll_loss'.format(split): nll_loss.detach().mean(), '{}/rec_loss'.format(split): rec_loss.detach().mean(), '{}/d_weight'.format(split): d_weight.detach(), '{}/disc_factor'.format(split): torch.tensor(disc_factor), '{}/g_loss'.format(split): g_loss.detach().mean()}
        return (loss, log)
    if optimizer_idx == 1:
        if cond is None:
            logits_real = self.discriminator(inputs.contiguous().detach())
            logits_fake = self.discriminator(reconstructions.contiguous().detach())
        else:
            logits_real = self.discriminator(torch.cat((inputs.contiguous().detach(), cond), dim=1))
            logits_fake = self.discriminator(torch.cat((reconstructions.contiguous().detach(), cond), dim=1))
        disc_factor = adopt_weight(self.disc_factor, global_step, threshold=self.discriminator_iter_start)
        d_loss = disc_factor * self.disc_loss(logits_real, logits_fake)
        log = {'{}/disc_loss'.format(split): d_loss.clone().detach().mean(), '{}/logits_real'.format(split): logits_real.detach().mean(), '{}/logits_fake'.format(split): logits_fake.detach().mean()}
        return (d_loss, log)

def fspecial_gaussian(hsize, sigma):
    hsize = [hsize, hsize]
    siz = [(hsize[0] - 1.0) / 2.0, (hsize[1] - 1.0) / 2.0]
    std = sigma
    [x, y] = np.meshgrid(np.arange(-siz[1], siz[1] + 1), np.arange(-siz[0], siz[0] + 1))
    arg = -(x * x + y * y) / (2 * std * std)
    h = np.exp(arg)
    h[h < scipy.finfo(float).eps * h.max()] = 0
    sumh = h.sum()
    if sumh != 0:
        h = h / sumh
    return h

def imsave(img, img_path):
    img = np.squeeze(img)
    if img.ndim == 3:
        img = img[:, :, [2, 1, 0]]
    cv2.imwrite(img_path, img)

def imwrite(img, img_path):
    img = np.squeeze(img)
    if img.ndim == 3:
        img = img[:, :, [2, 1, 0]]
    cv2.imwrite(img_path, img)

def uint2tensor4(img):
    if img.ndim == 2:
        img = np.expand_dims(img, axis=2)
    return torch.from_numpy(np.ascontiguousarray(img)).permute(2, 0, 1).float().div(255.0).unsqueeze(0)

def uint2tensor3(img):
    if img.ndim == 2:
        img = np.expand_dims(img, axis=2)
    return torch.from_numpy(np.ascontiguousarray(img)).permute(2, 0, 1).float().div(255.0)

def single2tensor3(img):
    return torch.from_numpy(np.ascontiguousarray(img)).permute(2, 0, 1).float()

def single2tensor4(img):
    return torch.from_numpy(np.ascontiguousarray(img)).permute(2, 0, 1).float().unsqueeze(0)

def single2tensor5(img):
    return torch.from_numpy(np.ascontiguousarray(img)).permute(2, 0, 1, 3).float().unsqueeze(0)

def single32tensor5(img):
    return torch.from_numpy(np.ascontiguousarray(img)).float().unsqueeze(0).unsqueeze(0)

def single42tensor4(img):
    return torch.from_numpy(np.ascontiguousarray(img)).permute(2, 0, 1, 3).float()

def augment_img(img, mode=0):
    """Kai Zhang (github: https://github.com/cszn)
    """
    if mode == 0:
        return img
    elif mode == 1:
        return np.flipud(np.rot90(img))
    elif mode == 2:
        return np.flipud(img)
    elif mode == 3:
        return np.rot90(img, k=3)
    elif mode == 4:
        return np.flipud(np.rot90(img, k=2))
    elif mode == 5:
        return np.rot90(img)
    elif mode == 6:
        return np.rot90(img, k=2)
    elif mode == 7:
        return np.flipud(np.rot90(img, k=3))

def augment_img_tensor4(img, mode=0):
    """Kai Zhang (github: https://github.com/cszn)
    """
    if mode == 0:
        return img
    elif mode == 1:
        return img.rot90(1, [2, 3]).flip([2])
    elif mode == 2:
        return img.flip([2])
    elif mode == 3:
        return img.rot90(3, [2, 3])
    elif mode == 4:
        return img.rot90(2, [2, 3]).flip([2])
    elif mode == 5:
        return img.rot90(1, [2, 3])
    elif mode == 6:
        return img.rot90(2, [2, 3])
    elif mode == 7:
        return img.rot90(3, [2, 3]).flip([2])

def augment_img_tensor(img, mode=0):
    """Kai Zhang (github: https://github.com/cszn)
    """
    img_size = img.size()
    img_np = img.data.cpu().numpy()
    if len(img_size) == 3:
        img_np = np.transpose(img_np, (1, 2, 0))
    elif len(img_size) == 4:
        img_np = np.transpose(img_np, (2, 3, 1, 0))
    img_np = augment_img(img_np, mode=mode)
    img_tensor = torch.from_numpy(np.ascontiguousarray(img_np))
    if len(img_size) == 3:
        img_tensor = img_tensor.permute(2, 0, 1)
    elif len(img_size) == 4:
        img_tensor = img_tensor.permute(3, 2, 0, 1)
    return img_tensor.type_as(img)

def calculate_weights_indices(in_length, out_length, scale, kernel, kernel_width, antialiasing):
    if scale < 1 and antialiasing:
        kernel_width = kernel_width / scale
    x = torch.linspace(1, out_length, out_length)
    u = x / scale + 0.5 * (1 - 1 / scale)
    left = torch.floor(u - kernel_width / 2)
    P = math.ceil(kernel_width) + 2
    indices = left.view(out_length, 1).expand(out_length, P) + torch.linspace(0, P - 1, P).view(1, P).expand(out_length, P)
    distance_to_center = u.view(out_length, 1).expand(out_length, P) - indices
    if scale < 1 and antialiasing:
        weights = scale * cubic(distance_to_center * scale)
    else:
        weights = cubic(distance_to_center)
    weights_sum = torch.sum(weights, 1).view(out_length, 1)
    weights = weights / weights_sum.expand(out_length, P)
    weights_zero_tmp = torch.sum(weights == 0, 0)
    if not math.isclose(weights_zero_tmp[0], 0, rel_tol=1e-06):
        indices = indices.narrow(1, 1, P - 2)
        weights = weights.narrow(1, 1, P - 2)
    if not math.isclose(weights_zero_tmp[-1], 0, rel_tol=1e-06):
        indices = indices.narrow(1, 0, P - 2)
        weights = weights.narrow(1, 0, P - 2)
    weights = weights.contiguous()
    indices = indices.contiguous()
    sym_len_s = -indices.min() + 1
    sym_len_e = indices.max() - in_length
    indices = indices + sym_len_s - 1
    return (weights, indices, int(sym_len_s), int(sym_len_e))

def blur(x, k):
    """
    x: image, NxcxHxW
    k: kernel, Nx1xhxw
    """
    n, c = x.shape[:2]
    p1, p2 = ((k.shape[-2] - 1) // 2, (k.shape[-1] - 1) // 2)
    x = torch.nn.functional.pad(x, pad=(p1, p2, p1, p2), mode='replicate')
    k = k.repeat(1, c, 1, 1)
    k = k.view(-1, 1, k.shape[2], k.shape[3])
    x = x.view(1, -1, x.shape[2], x.shape[3])
    x = torch.nn.functional.conv2d(x, k, bias=None, stride=1, padding=0, groups=n * c)
    x = x.view(n, c, x.shape[2], x.shape[3])
    return x

def fspecial_gaussian(hsize, sigma):
    hsize = [hsize, hsize]
    siz = [(hsize[0] - 1.0) / 2.0, (hsize[1] - 1.0) / 2.0]
    std = sigma
    [x, y] = np.meshgrid(np.arange(-siz[1], siz[1] + 1), np.arange(-siz[0], siz[0] + 1))
    arg = -(x * x + y * y) / (2 * std * std)
    h = np.exp(arg)
    h[h < scipy.finfo(float).eps * h.max()] = 0
    sumh = h.sum()
    if sumh != 0:
        h = h / sumh
    return h

class AttentionPool2d(nn.Module):
    """
    Adapted from CLIP: https://github.com/openai/CLIP/blob/main/clip/model.py
    """

    def __init__(self, spacial_dim: int, embed_dim: int, num_heads_channels: int, output_dim: int=None):
        super().__init__()
        self.positional_embedding = nn.Parameter(th.randn(embed_dim, spacial_dim ** 2 + 1) / embed_dim ** 0.5)
        self.qkv_proj = conv_nd(1, embed_dim, 3 * embed_dim, 1)
        self.c_proj = conv_nd(1, embed_dim, output_dim or embed_dim, 1)
        self.num_heads = embed_dim // num_heads_channels
        self.attention = QKVAttention(self.num_heads)

    def forward(self, x):
        b, c, *_spatial = x.shape
        x = x.reshape(b, c, -1)
        x = th.cat([x.mean(dim=-1, keepdim=True), x], dim=-1)
        x = x + self.positional_embedding[None, :, :].to(x.dtype)
        x = self.qkv_proj(x)
        x = self.attention(x)
        x = self.c_proj(x)
        return x[:, :, 0]

def forward(self, x):
    b, c, *_spatial = x.shape
    x = x.reshape(b, c, -1)
    x = th.cat([x.mean(dim=-1, keepdim=True), x], dim=-1)
    x = x + self.positional_embedding[None, :, :].to(x.dtype)
    x = self.qkv_proj(x)
    x = self.attention(x)
    x = self.c_proj(x)
    return x[:, :, 0]

class Upsample(nn.Module):
    """
    An upsampling layer with an optional convolution.
    :param channels: channels in the inputs and outputs.
    :param use_conv: a bool determining if a convolution is applied.
    :param dims: determines if the signal is 1D, 2D, or 3D. If 3D, then
                 upsampling occurs in the inner-two dimensions.
    """

    def __init__(self, channels, use_conv, dims=2, out_channels=None, padding=1):
        super().__init__()
        self.channels = channels
        self.out_channels = out_channels or channels
        self.use_conv = use_conv
        self.dims = dims
        if use_conv:
            self.conv = conv_nd(dims, self.channels, self.out_channels, 3, padding=padding)

    def forward(self, x):
        assert x.shape[1] == self.channels
        if self.dims == 3:
            x = F.interpolate(x, (x.shape[2], x.shape[3] * 2, x.shape[4] * 2), mode='nearest')
        else:
            x = F.interpolate(x, scale_factor=2, mode='nearest')
        if self.use_conv:
            x = self.conv(x)
        return x

def forward(self, x):
    assert x.shape[1] == self.channels
    if self.dims == 3:
        x = F.interpolate(x, (x.shape[2], x.shape[3] * 2, x.shape[4] * 2), mode='nearest')
    else:
        x = F.interpolate(x, scale_factor=2, mode='nearest')
    if self.use_conv:
        x = self.conv(x)
    return x

class AttentionBlock(nn.Module):
    """
    An attention block that allows spatial positions to attend to each other.
    Originally ported from here, but adapted to the N-d case.
    https://github.com/hojonathanho/diffusion/blob/1e0dceb3b3495bbe19116a5e1b3596cd0706c543/diffusion_tf/models/unet.py#L66.
    """

    def __init__(self, channels, num_heads=1, num_head_channels=-1, use_checkpoint=False, use_new_attention_order=False):
        super().__init__()
        self.channels = channels
        if num_head_channels == -1:
            self.num_heads = num_heads
        else:
            assert channels % num_head_channels == 0, f'q,k,v channels {channels} is not divisible by num_head_channels {num_head_channels}'
            self.num_heads = channels // num_head_channels
        self.use_checkpoint = use_checkpoint
        self.norm = normalization(channels)
        self.qkv = conv_nd(1, channels, channels * 3, 1)
        if use_new_attention_order:
            self.attention = QKVAttention(self.num_heads)
        else:
            self.attention = QKVAttentionLegacy(self.num_heads)
        self.proj_out = zero_module(conv_nd(1, channels, channels, 1))

    def forward(self, x):
        return checkpoint(self._forward, (x,), self.parameters(), True)

    def _forward(self, x):
        b, c, *spatial = x.shape
        x = x.reshape(b, c, -1)
        qkv = self.qkv(self.norm(x))
        h = self.attention(qkv)
        h = self.proj_out(h)
        return (x + h).reshape(b, c, *spatial)

def _forward(self, x):
    b, c, *spatial = x.shape
    x = x.reshape(b, c, -1)
    qkv = self.qkv(self.norm(x))
    h = self.attention(qkv)
    h = self.proj_out(h)
    return (x + h).reshape(b, c, *spatial)

class QKVAttentionLegacy(nn.Module):
    """
    A module which performs QKV attention. Matches legacy QKVAttention + input/ouput heads shaping
    """

    def __init__(self, n_heads):
        super().__init__()
        self.n_heads = n_heads

    def forward(self, qkv):
        """
        Apply QKV attention.
        :param qkv: an [N x (H * 3 * C) x T] tensor of Qs, Ks, and Vs.
        :return: an [N x (H * C) x T] tensor after attention.
        """
        bs, width, length = qkv.shape
        assert width % (3 * self.n_heads) == 0
        ch = width // (3 * self.n_heads)
        q, k, v = qkv.reshape(bs * self.n_heads, ch * 3, length).split(ch, dim=1)
        scale = 1 / math.sqrt(math.sqrt(ch))
        weight = th.einsum('bct,bcs->bts', q * scale, k * scale)
        weight = th.softmax(weight.float(), dim=-1).type(weight.dtype)
        a = th.einsum('bts,bcs->bct', weight, v)
        return a.reshape(bs, -1, length)

    @staticmethod
    def count_flops(model, _x, y):
        return count_flops_attn(model, _x, y)

def forward(self, qkv):
    """
        Apply QKV attention.
        :param qkv: an [N x (H * 3 * C) x T] tensor of Qs, Ks, and Vs.
        :return: an [N x (H * C) x T] tensor after attention.
        """
    bs, width, length = qkv.shape
    assert width % (3 * self.n_heads) == 0
    ch = width // (3 * self.n_heads)
    q, k, v = qkv.reshape(bs * self.n_heads, ch * 3, length).split(ch, dim=1)
    scale = 1 / math.sqrt(math.sqrt(ch))
    weight = th.einsum('bct,bcs->bts', q * scale, k * scale)
    weight = th.softmax(weight.float(), dim=-1).type(weight.dtype)
    a = th.einsum('bts,bcs->bct', weight, v)
    return a.reshape(bs, -1, length)

class QKVAttention(nn.Module):
    """
    A module which performs QKV attention and splits in a different order.
    """

    def __init__(self, n_heads):
        super().__init__()
        self.n_heads = n_heads

    def forward(self, qkv):
        """
        Apply QKV attention.
        :param qkv: an [N x (3 * H * C) x T] tensor of Qs, Ks, and Vs.
        :return: an [N x (H * C) x T] tensor after attention.
        """
        bs, width, length = qkv.shape
        assert width % (3 * self.n_heads) == 0
        ch = width // (3 * self.n_heads)
        q, k, v = qkv.chunk(3, dim=1)
        scale = 1 / math.sqrt(math.sqrt(ch))
        weight = th.einsum('bct,bcs->bts', (q * scale).view(bs * self.n_heads, ch, length), (k * scale).view(bs * self.n_heads, ch, length))
        weight = th.softmax(weight.float(), dim=-1).type(weight.dtype)
        a = th.einsum('bts,bcs->bct', weight, v.reshape(bs * self.n_heads, ch, length))
        return a.reshape(bs, -1, length)

    @staticmethod
    def count_flops(model, _x, y):
        return count_flops_attn(model, _x, y)

def forward(self, qkv):
    """
        Apply QKV attention.
        :param qkv: an [N x (3 * H * C) x T] tensor of Qs, Ks, and Vs.
        :return: an [N x (H * C) x T] tensor after attention.
        """
    bs, width, length = qkv.shape
    assert width % (3 * self.n_heads) == 0
    ch = width // (3 * self.n_heads)
    q, k, v = qkv.chunk(3, dim=1)
    scale = 1 / math.sqrt(math.sqrt(ch))
    weight = th.einsum('bct,bcs->bts', (q * scale).view(bs * self.n_heads, ch, length), (k * scale).view(bs * self.n_heads, ch, length))
    weight = th.softmax(weight.float(), dim=-1).type(weight.dtype)
    a = th.einsum('bts,bcs->bct', weight, v.reshape(bs * self.n_heads, ch, length))
    return a.reshape(bs, -1, length)

class Upsample(nn.Module):

    def __init__(self, in_channels, with_conv):
        super().__init__()
        self.with_conv = with_conv
        if self.with_conv:
            self.conv = torch.nn.Conv2d(in_channels, in_channels, kernel_size=3, stride=1, padding=1)

    def forward(self, x):
        x = torch.nn.functional.interpolate(x, scale_factor=2.0, mode='nearest')
        if self.with_conv:
            x = self.conv(x)
        return x

def forward(self, x):
    x = torch.nn.functional.interpolate(x, scale_factor=2.0, mode='nearest')
    if self.with_conv:
        x = self.conv(x)
    return x

class AttnBlock(nn.Module):

    def __init__(self, in_channels):
        super().__init__()
        self.in_channels = in_channels
        self.norm = Normalize(in_channels)
        self.q = torch.nn.Conv2d(in_channels, in_channels, kernel_size=1, stride=1, padding=0)
        self.k = torch.nn.Conv2d(in_channels, in_channels, kernel_size=1, stride=1, padding=0)
        self.v = torch.nn.Conv2d(in_channels, in_channels, kernel_size=1, stride=1, padding=0)
        self.proj_out = torch.nn.Conv2d(in_channels, in_channels, kernel_size=1, stride=1, padding=0)

    def forward(self, x):
        h_ = x
        h_ = self.norm(h_)
        q = self.q(h_)
        k = self.k(h_)
        v = self.v(h_)
        b, c, h, w = q.shape
        q = q.reshape(b, c, h * w)
        q = q.permute(0, 2, 1)
        k = k.reshape(b, c, h * w)
        w_ = torch.bmm(q, k)
        w_ = w_ * int(c) ** (-0.5)
        w_ = torch.nn.functional.softmax(w_, dim=2)
        v = v.reshape(b, c, h * w)
        w_ = w_.permute(0, 2, 1)
        h_ = torch.bmm(v, w_)
        h_ = h_.reshape(b, c, h, w)
        h_ = self.proj_out(h_)
        return x + h_

def forward(self, x):
    h_ = x
    h_ = self.norm(h_)
    q = self.q(h_)
    k = self.k(h_)
    v = self.v(h_)
    b, c, h, w = q.shape
    q = q.reshape(b, c, h * w)
    q = q.permute(0, 2, 1)
    k = k.reshape(b, c, h * w)
    w_ = torch.bmm(q, k)
    w_ = w_ * int(c) ** (-0.5)
    w_ = torch.nn.functional.softmax(w_, dim=2)
    v = v.reshape(b, c, h * w)
    w_ = w_.permute(0, 2, 1)
    h_ = torch.bmm(v, w_)
    h_ = h_.reshape(b, c, h, w)
    h_ = self.proj_out(h_)
    return x + h_

class Resize(nn.Module):

    def __init__(self, in_channels=None, learned=False, mode='bilinear'):
        super().__init__()
        self.with_conv = learned
        self.mode = mode
        if self.with_conv:
            print(f'Note: {self.__class__.__name} uses learned downsampling and will ignore the fixed {mode} mode')
            raise NotImplementedError()
            assert in_channels is not None
            self.conv = torch.nn.Conv2d(in_channels, in_channels, kernel_size=4, stride=2, padding=1)

    def forward(self, x, scale_factor=1.0):
        if scale_factor == 1.0:
            return x
        else:
            x = torch.nn.functional.interpolate(x, mode=self.mode, align_corners=False, scale_factor=scale_factor)
        return x

def forward(self, x, scale_factor=1.0):
    if scale_factor == 1.0:
        return x
    else:
        x = torch.nn.functional.interpolate(x, mode=self.mode, align_corners=False, scale_factor=scale_factor)
    return x

def timestep_embedding(timesteps, dim, max_period=10000, repeat_only=False):
    """
    Create sinusoidal timestep embeddings.
    :param timesteps: a 1-D Tensor of N indices, one per batch element.
                      These may be fractional.
    :param dim: the dimension of the output.
    :param max_period: controls the minimum frequency of the embeddings.
    :return: an [N x dim] Tensor of positional embeddings.
    """
    if not repeat_only:
        half = dim // 2
        freqs = torch.exp(-math.log(max_period) * torch.arange(start=0, end=half, dtype=torch.float32) / half).to(device=timesteps.device)
        args = timesteps[:, None].float() * freqs[None]
        embedding = torch.cat([torch.cos(args), torch.sin(args)], dim=-1)
        if dim % 2:
            embedding = torch.cat([embedding, torch.zeros_like(embedding[:, :1])], dim=-1)
    else:
        embedding = repeat(timesteps, 'b -> b d', d=dim)
    return embedding

class VQModel(pl.LightningModule):

    def __init__(self, ddconfig, lossconfig, n_embed, embed_dim, ckpt_path=None, ignore_keys=[], image_key='image', colorize_nlabels=None, monitor=None, batch_resize_range=None, scheduler_config=None, lr_g_factor=1.0, remap=None, sane_index_shape=False, use_ema=False):
        super().__init__()
        self.embed_dim = embed_dim
        self.n_embed = n_embed
        self.image_key = image_key
        self.encoder = Encoder(**ddconfig)
        self.decoder = Decoder(**ddconfig)
        self.loss = instantiate_from_config(lossconfig)
        self.quantize = VectorQuantizer(n_embed, embed_dim, beta=0.25, remap=remap, sane_index_shape=sane_index_shape)
        self.quant_conv = torch.nn.Conv2d(ddconfig['z_channels'], embed_dim, 1)
        self.post_quant_conv = torch.nn.Conv2d(embed_dim, ddconfig['z_channels'], 1)
        if colorize_nlabels is not None:
            assert type(colorize_nlabels) == int
            self.register_buffer('colorize', torch.randn(3, colorize_nlabels, 1, 1))
        if monitor is not None:
            self.monitor = monitor
        self.batch_resize_range = batch_resize_range
        if self.batch_resize_range is not None:
            print(f'{self.__class__.__name__}: Using per-batch resizing in range {batch_resize_range}.')
        self.use_ema = use_ema
        if self.use_ema:
            self.model_ema = LitEma(self)
            print(f'Keeping EMAs of {len(list(self.model_ema.buffers()))}.')
        if ckpt_path is not None:
            self.init_from_ckpt(ckpt_path, ignore_keys=ignore_keys)
        self.scheduler_config = scheduler_config
        self.lr_g_factor = lr_g_factor

    @contextmanager
    def ema_scope(self, context=None):
        if self.use_ema:
            self.model_ema.store(self.parameters())
            self.model_ema.copy_to(self)
            if context is not None:
                print(f'{context}: Switched to EMA weights')
        try:
            yield None
        finally:
            if self.use_ema:
                self.model_ema.restore(self.parameters())
                if context is not None:
                    print(f'{context}: Restored training weights')

    def init_from_ckpt(self, path, ignore_keys=list()):
        sd = torch.load(path, map_location='cpu')['state_dict']
        keys = list(sd.keys())
        for k in keys:
            for ik in ignore_keys:
                if k.startswith(ik):
                    print('Deleting key {} from state_dict.'.format(k))
                    del sd[k]
        missing, unexpected = self.load_state_dict(sd, strict=False)
        print(f'Restored from {path} with {len(missing)} missing and {len(unexpected)} unexpected keys')
        if len(missing) > 0:
            print(f'Missing Keys: {missing}')
            print(f'Unexpected Keys: {unexpected}')

    def on_train_batch_end(self, *args, **kwargs):
        if self.use_ema:
            self.model_ema(self)

    def encode(self, x):
        h = self.encoder(x)
        h = self.quant_conv(h)
        quant, emb_loss, info = self.quantize(h)
        return (quant, emb_loss, info)

    def encode_to_prequant(self, x):
        h = self.encoder(x)
        h = self.quant_conv(h)
        return h

    def decode(self, quant):
        quant = self.post_quant_conv(quant)
        dec = self.decoder(quant)
        return dec

    def decode_code(self, code_b):
        quant_b = self.quantize.embed_code(code_b)
        dec = self.decode(quant_b)
        return dec

    def forward(self, input, return_pred_indices=False):
        quant, diff, (_, _, ind) = self.encode(input)
        dec = self.decode(quant)
        if return_pred_indices:
            return (dec, diff, ind)
        return (dec, diff)

    def get_input(self, batch, k):
        x = batch[k]
        if len(x.shape) == 3:
            x = x[..., None]
        x = x.permute(0, 3, 1, 2).to(memory_format=torch.contiguous_format).float()
        if self.batch_resize_range is not None:
            lower_size = self.batch_resize_range[0]
            upper_size = self.batch_resize_range[1]
            if self.global_step <= 4:
                new_resize = upper_size
            else:
                new_resize = np.random.choice(np.arange(lower_size, upper_size + 16, 16))
            if new_resize != x.shape[2]:
                x = F.interpolate(x, size=new_resize, mode='bicubic')
            x = x.detach()
        return x

    def training_step(self, batch, batch_idx, optimizer_idx):
        x = self.get_input(batch, self.image_key)
        xrec, qloss, ind = self(x, return_pred_indices=True)
        if optimizer_idx == 0:
            aeloss, log_dict_ae = self.loss(qloss, x, xrec, optimizer_idx, self.global_step, last_layer=self.get_last_layer(), split='train', predicted_indices=ind)
            self.log_dict(log_dict_ae, prog_bar=False, logger=True, on_step=True, on_epoch=True)
            return aeloss
        if optimizer_idx == 1:
            discloss, log_dict_disc = self.loss(qloss, x, xrec, optimizer_idx, self.global_step, last_layer=self.get_last_layer(), split='train')
            self.log_dict(log_dict_disc, prog_bar=False, logger=True, on_step=True, on_epoch=True)
            return discloss

    def validation_step(self, batch, batch_idx):
        log_dict = self._validation_step(batch, batch_idx)
        with self.ema_scope():
            log_dict_ema = self._validation_step(batch, batch_idx, suffix='_ema')
        return log_dict

    def _validation_step(self, batch, batch_idx, suffix=''):
        x = self.get_input(batch, self.image_key)
        xrec, qloss, ind = self(x, return_pred_indices=True)
        aeloss, log_dict_ae = self.loss(qloss, x, xrec, 0, self.global_step, last_layer=self.get_last_layer(), split='val' + suffix, predicted_indices=ind)
        discloss, log_dict_disc = self.loss(qloss, x, xrec, 1, self.global_step, last_layer=self.get_last_layer(), split='val' + suffix, predicted_indices=ind)
        rec_loss = log_dict_ae[f'val{suffix}/rec_loss']
        self.log(f'val{suffix}/rec_loss', rec_loss, prog_bar=True, logger=True, on_step=False, on_epoch=True, sync_dist=True)
        self.log(f'val{suffix}/aeloss', aeloss, prog_bar=True, logger=True, on_step=False, on_epoch=True, sync_dist=True)
        if version.parse(pl.__version__) >= version.parse('1.4.0'):
            del log_dict_ae[f'val{suffix}/rec_loss']
        self.log_dict(log_dict_ae)
        self.log_dict(log_dict_disc)
        return self.log_dict

    def configure_optimizers(self):
        lr_d = self.learning_rate
        lr_g = self.lr_g_factor * self.learning_rate
        print('lr_d', lr_d)
        print('lr_g', lr_g)
        opt_ae = torch.optim.Adam(list(self.encoder.parameters()) + list(self.decoder.parameters()) + list(self.quantize.parameters()) + list(self.quant_conv.parameters()) + list(self.post_quant_conv.parameters()), lr=lr_g, betas=(0.5, 0.9))
        opt_disc = torch.optim.Adam(self.loss.discriminator.parameters(), lr=lr_d, betas=(0.5, 0.9))
        if self.scheduler_config is not None:
            scheduler = instantiate_from_config(self.scheduler_config)
            print('Setting up LambdaLR scheduler...')
            scheduler = [{'scheduler': LambdaLR(opt_ae, lr_lambda=scheduler.schedule), 'interval': 'step', 'frequency': 1}, {'scheduler': LambdaLR(opt_disc, lr_lambda=scheduler.schedule), 'interval': 'step', 'frequency': 1}]
            return ([opt_ae, opt_disc], scheduler)
        return ([opt_ae, opt_disc], [])

    def get_last_layer(self):
        return self.decoder.conv_out.weight

    def log_images(self, batch, only_inputs=False, plot_ema=False, **kwargs):
        log = dict()
        x = self.get_input(batch, self.image_key)
        x = x.to(self.device)
        if only_inputs:
            log['inputs'] = x
            return log
        xrec, _ = self(x)
        if x.shape[1] > 3:
            assert xrec.shape[1] > 3
            x = self.to_rgb(x)
            xrec = self.to_rgb(xrec)
        log['inputs'] = x
        log['reconstructions'] = xrec
        if plot_ema:
            with self.ema_scope():
                xrec_ema, _ = self(x)
                if x.shape[1] > 3:
                    xrec_ema = self.to_rgb(xrec_ema)
                log['reconstructions_ema'] = xrec_ema
        return log

    def to_rgb(self, x):
        assert self.image_key == 'segmentation'
        if not hasattr(self, 'colorize'):
            self.register_buffer('colorize', torch.randn(3, x.shape[1], 1, 1).to(x))
        x = F.conv2d(x, weight=self.colorize)
        x = 2.0 * (x - x.min()) / (x.max() - x.min()) - 1.0
        return x

def get_input(self, batch, k):
    x = batch[k]
    if len(x.shape) == 3:
        x = x[..., None]
    x = x.permute(0, 3, 1, 2).to(memory_format=torch.contiguous_format).float()
    if self.batch_resize_range is not None:
        lower_size = self.batch_resize_range[0]
        upper_size = self.batch_resize_range[1]
        if self.global_step <= 4:
            new_resize = upper_size
        else:
            new_resize = np.random.choice(np.arange(lower_size, upper_size + 16, 16))
        if new_resize != x.shape[2]:
            x = F.interpolate(x, size=new_resize, mode='bicubic')
        x = x.detach()
    return x

class AutoencoderKL(pl.LightningModule):

    def __init__(self, ddconfig, lossconfig, embed_dim, ckpt_path=None, ignore_keys=[], image_key='image', colorize_nlabels=None, monitor=None):
        super().__init__()
        self.image_key = image_key
        self.encoder = Encoder(**ddconfig)
        self.decoder = Decoder(**ddconfig)
        self.loss = instantiate_from_config(lossconfig)
        assert ddconfig['double_z']
        self.quant_conv = torch.nn.Conv2d(2 * ddconfig['z_channels'], 2 * embed_dim, 1)
        self.post_quant_conv = torch.nn.Conv2d(embed_dim, ddconfig['z_channels'], 1)
        self.embed_dim = embed_dim
        if colorize_nlabels is not None:
            assert type(colorize_nlabels) == int
            self.register_buffer('colorize', torch.randn(3, colorize_nlabels, 1, 1))
        if monitor is not None:
            self.monitor = monitor
        if ckpt_path is not None:
            self.init_from_ckpt(ckpt_path, ignore_keys=ignore_keys)

    def init_from_ckpt(self, path, ignore_keys=list()):
        sd = torch.load(path, map_location='cpu')['state_dict']
        keys = list(sd.keys())
        for k in keys:
            for ik in ignore_keys:
                if k.startswith(ik):
                    print('Deleting key {} from state_dict.'.format(k))
                    del sd[k]
        self.load_state_dict(sd, strict=False)
        print(f'Restored from {path}')

    def encode(self, x):
        h = self.encoder(x)
        moments = self.quant_conv(h)
        posterior = DiagonalGaussianDistribution(moments)
        return posterior

    def decode(self, z):
        z = self.post_quant_conv(z)
        dec = self.decoder(z)
        return dec

    def forward(self, input, sample_posterior=True):
        posterior = self.encode(input)
        if sample_posterior:
            z = posterior.sample()
        else:
            z = posterior.mode()
        dec = self.decode(z)
        return (dec, posterior)

    def get_input(self, batch, k):
        x = batch[k]
        if len(x.shape) == 3:
            x = x[..., None]
        x = x.permute(0, 3, 1, 2).to(memory_format=torch.contiguous_format).float()
        return x

    def training_step(self, batch, batch_idx, optimizer_idx):
        inputs = self.get_input(batch, self.image_key)
        reconstructions, posterior = self(inputs)
        if optimizer_idx == 0:
            aeloss, log_dict_ae = self.loss(inputs, reconstructions, posterior, optimizer_idx, self.global_step, last_layer=self.get_last_layer(), split='train')
            self.log('aeloss', aeloss, prog_bar=True, logger=True, on_step=True, on_epoch=True)
            self.log_dict(log_dict_ae, prog_bar=False, logger=True, on_step=True, on_epoch=False)
            return aeloss
        if optimizer_idx == 1:
            discloss, log_dict_disc = self.loss(inputs, reconstructions, posterior, optimizer_idx, self.global_step, last_layer=self.get_last_layer(), split='train')
            self.log('discloss', discloss, prog_bar=True, logger=True, on_step=True, on_epoch=True)
            self.log_dict(log_dict_disc, prog_bar=False, logger=True, on_step=True, on_epoch=False)
            return discloss

    def validation_step(self, batch, batch_idx):
        inputs = self.get_input(batch, self.image_key)
        reconstructions, posterior = self(inputs)
        aeloss, log_dict_ae = self.loss(inputs, reconstructions, posterior, 0, self.global_step, last_layer=self.get_last_layer(), split='val')
        discloss, log_dict_disc = self.loss(inputs, reconstructions, posterior, 1, self.global_step, last_layer=self.get_last_layer(), split='val')
        self.log('val/rec_loss', log_dict_ae['val/rec_loss'])
        self.log_dict(log_dict_ae)
        self.log_dict(log_dict_disc)
        return self.log_dict

    def configure_optimizers(self):
        lr = self.learning_rate
        opt_ae = torch.optim.Adam(list(self.encoder.parameters()) + list(self.decoder.parameters()) + list(self.quant_conv.parameters()) + list(self.post_quant_conv.parameters()), lr=lr, betas=(0.5, 0.9))
        opt_disc = torch.optim.Adam(self.loss.discriminator.parameters(), lr=lr, betas=(0.5, 0.9))
        return ([opt_ae, opt_disc], [])

    def get_last_layer(self):
        return self.decoder.conv_out.weight

    @torch.no_grad()
    def log_images(self, batch, only_inputs=False, **kwargs):
        log = dict()
        x = self.get_input(batch, self.image_key)
        x = x.to(self.device)
        if not only_inputs:
            xrec, posterior = self(x)
            if x.shape[1] > 3:
                assert xrec.shape[1] > 3
                x = self.to_rgb(x)
                xrec = self.to_rgb(xrec)
            log['samples'] = self.decode(torch.randn_like(posterior.sample()))
            log['reconstructions'] = xrec
        log['inputs'] = x
        return log

    def to_rgb(self, x):
        assert self.image_key == 'segmentation'
        if not hasattr(self, 'colorize'):
            self.register_buffer('colorize', torch.randn(3, x.shape[1], 1, 1).to(x))
        x = F.conv2d(x, weight=self.colorize)
        x = 2.0 * (x - x.min()) / (x.max() - x.min()) - 1.0
        return x

def get_input(self, batch, k):
    x = batch[k]
    if len(x.shape) == 3:
        x = x[..., None]
    x = x.permute(0, 3, 1, 2).to(memory_format=torch.contiguous_format).float()
    return x

class NoisyLatentImageClassifier(pl.LightningModule):

    def __init__(self, diffusion_path, num_classes, ckpt_path=None, pool='attention', label_key=None, diffusion_ckpt_path=None, scheduler_config=None, weight_decay=0.01, log_steps=10, monitor='val/loss', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.num_classes = num_classes
        diffusion_config = natsorted(glob(os.path.join(diffusion_path, 'configs', '*-project.yaml')))[-1]
        self.diffusion_config = OmegaConf.load(diffusion_config).model
        self.diffusion_config.params.ckpt_path = diffusion_ckpt_path
        self.load_diffusion()
        self.monitor = monitor
        self.numd = self.diffusion_model.first_stage_model.encoder.num_resolutions - 1
        self.log_time_interval = self.diffusion_model.num_timesteps // log_steps
        self.log_steps = log_steps
        self.label_key = label_key if not hasattr(self.diffusion_model, 'cond_stage_key') else self.diffusion_model.cond_stage_key
        assert self.label_key is not None, 'label_key neither in diffusion model nor in model.params'
        if self.label_key not in __models__:
            raise NotImplementedError()
        self.load_classifier(ckpt_path, pool)
        self.scheduler_config = scheduler_config
        self.use_scheduler = self.scheduler_config is not None
        self.weight_decay = weight_decay

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

    def load_diffusion(self):
        model = instantiate_from_config(self.diffusion_config)
        self.diffusion_model = model.eval()
        self.diffusion_model.train = disabled_train
        for param in self.diffusion_model.parameters():
            param.requires_grad = False

    def load_classifier(self, ckpt_path, pool):
        model_config = deepcopy(self.diffusion_config.params.unet_config.params)
        model_config.in_channels = self.diffusion_config.params.unet_config.params.out_channels
        model_config.out_channels = self.num_classes
        if self.label_key == 'class_label':
            model_config.pool = pool
        self.model = __models__[self.label_key](**model_config)
        if ckpt_path is not None:
            print('#####################################################################')
            print(f'load from ckpt "{ckpt_path}"')
            print('#####################################################################')
            self.init_from_ckpt(ckpt_path)

    @torch.no_grad()
    def get_x_noisy(self, x, t, noise=None):
        noise = default(noise, lambda: torch.randn_like(x))
        continuous_sqrt_alpha_cumprod = None
        if self.diffusion_model.use_continuous_noise:
            continuous_sqrt_alpha_cumprod = self.diffusion_model.sample_continuous_noise_level(x.shape[0], t + 1)
        return self.diffusion_model.q_sample(x_start=x, t=t, noise=noise, continuous_sqrt_alpha_cumprod=continuous_sqrt_alpha_cumprod)

    def forward(self, x_noisy, t, *args, **kwargs):
        return self.model(x_noisy, t)

    @torch.no_grad()
    def get_input(self, batch, k):
        x = batch[k]
        if len(x.shape) == 3:
            x = x[..., None]
        x = rearrange(x, 'b h w c -> b c h w')
        x = x.to(memory_format=torch.contiguous_format).float()
        return x

    @torch.no_grad()
    def get_conditioning(self, batch, k=None):
        if k is None:
            k = self.label_key
        assert k is not None, 'Needs to provide label key'
        targets = batch[k].to(self.device)
        if self.label_key == 'segmentation':
            targets = rearrange(targets, 'b h w c -> b c h w')
            for down in range(self.numd):
                h, w = targets.shape[-2:]
                targets = F.interpolate(targets, size=(h // 2, w // 2), mode='nearest')
        return targets

    def compute_top_k(self, logits, labels, k, reduction='mean'):
        _, top_ks = torch.topk(logits, k, dim=1)
        if reduction == 'mean':
            return (top_ks == labels[:, None]).float().sum(dim=-1).mean().item()
        elif reduction == 'none':
            return (top_ks == labels[:, None]).float().sum(dim=-1)

    def on_train_epoch_start(self):
        self.diffusion_model.model.to('cpu')

    @torch.no_grad()
    def write_logs(self, loss, logits, targets):
        log_prefix = 'train' if self.training else 'val'
        log = {}
        log[f'{log_prefix}/loss'] = loss.mean()
        log[f'{log_prefix}/acc@1'] = self.compute_top_k(logits, targets, k=1, reduction='mean')
        log[f'{log_prefix}/acc@5'] = self.compute_top_k(logits, targets, k=5, reduction='mean')
        self.log_dict(log, prog_bar=False, logger=True, on_step=self.training, on_epoch=True)
        self.log('loss', log[f'{log_prefix}/loss'], prog_bar=True, logger=False)
        self.log('global_step', self.global_step, logger=False, on_epoch=False, prog_bar=True)
        lr = self.optimizers().param_groups[0]['lr']
        self.log('lr_abs', lr, on_step=True, logger=True, on_epoch=False, prog_bar=True)

    def shared_step(self, batch, t=None):
        x, *_ = self.diffusion_model.get_input(batch, k=self.diffusion_model.first_stage_key)
        targets = self.get_conditioning(batch)
        if targets.dim() == 4:
            targets = targets.argmax(dim=1)
        if t is None:
            t = torch.randint(0, self.diffusion_model.num_timesteps, (x.shape[0],), device=self.device).long()
        else:
            t = torch.full(size=(x.shape[0],), fill_value=t, device=self.device).long()
        x_noisy = self.get_x_noisy(x, t)
        logits = self(x_noisy, t)
        loss = F.cross_entropy(logits, targets, reduction='none')
        self.write_logs(loss.detach(), logits.detach(), targets.detach())
        loss = loss.mean()
        return (loss, logits, x_noisy, targets)

    def training_step(self, batch, batch_idx):
        loss, *_ = self.shared_step(batch)
        return loss

    def reset_noise_accs(self):
        self.noisy_acc = {t: {'acc@1': [], 'acc@5': []} for t in range(0, self.diffusion_model.num_timesteps, self.diffusion_model.log_every_t)}

    def on_validation_start(self):
        self.reset_noise_accs()

    @torch.no_grad()
    def validation_step(self, batch, batch_idx):
        loss, *_ = self.shared_step(batch)
        for t in self.noisy_acc:
            _, logits, _, targets = self.shared_step(batch, t)
            self.noisy_acc[t]['acc@1'].append(self.compute_top_k(logits, targets, k=1, reduction='mean'))
            self.noisy_acc[t]['acc@5'].append(self.compute_top_k(logits, targets, k=5, reduction='mean'))
        return loss

    def configure_optimizers(self):
        optimizer = AdamW(self.model.parameters(), lr=self.learning_rate, weight_decay=self.weight_decay)
        if self.use_scheduler:
            scheduler = instantiate_from_config(self.scheduler_config)
            print('Setting up LambdaLR scheduler...')
            scheduler = [{'scheduler': LambdaLR(optimizer, lr_lambda=scheduler.schedule), 'interval': 'step', 'frequency': 1}]
            return ([optimizer], scheduler)
        return optimizer

    @torch.no_grad()
    def log_images(self, batch, N=8, *args, **kwargs):
        log = dict()
        x = self.get_input(batch, self.diffusion_model.first_stage_key)
        log['inputs'] = x
        y = self.get_conditioning(batch)
        if self.label_key == 'class_label':
            y = log_txt_as_img((x.shape[2], x.shape[3]), batch['human_label'])
            log['labels'] = y
        if ismap(y):
            log['labels'] = self.diffusion_model.to_rgb(y)
            for step in range(self.log_steps):
                current_time = step * self.log_time_interval
                _, logits, x_noisy, _ = self.shared_step(batch, t=current_time)
                log[f'inputs@t{current_time}'] = x_noisy
                pred = F.one_hot(logits.argmax(dim=1), num_classes=self.num_classes)
                pred = rearrange(pred, 'b h w c -> b c h w')
                log[f'pred@t{current_time}'] = self.diffusion_model.to_rgb(pred)
        for key in log:
            log[key] = log[key][:N]
        return log

def compute_top_k(self, logits, labels, k, reduction='mean'):
    _, top_ks = torch.topk(logits, k, dim=1)
    if reduction == 'mean':
        return (top_ks == labels[:, None]).float().sum(dim=-1).mean().item()
    elif reduction == 'none':
        return (top_ks == labels[:, None]).float().sum(dim=-1)

class LatentDiffusion(DDPM):
    """main class"""

    def __init__(self, first_stage_config, cond_stage_config, num_timesteps_cond=None, cond_stage_key='image', cond_stage_trainable=False, concat_mode=True, cond_stage_forward=None, conditioning_key=None, scale_factor=1.0, scale_by_std=False, *args, **kwargs):
        self.num_timesteps_cond = default(num_timesteps_cond, 1)
        self.scale_by_std = scale_by_std
        assert self.num_timesteps_cond <= kwargs['timesteps']
        if conditioning_key is None:
            conditioning_key = 'concat' if concat_mode else 'crossattn'
        if cond_stage_config == '__is_unconditional__':
            conditioning_key = None
        ckpt_path = kwargs.pop('ckpt_path', None)
        ignore_keys = kwargs.pop('ignore_keys', [])
        super().__init__(*args, conditioning_key=conditioning_key, **kwargs)
        self.concat_mode = concat_mode
        self.cond_stage_trainable = cond_stage_trainable
        self.cond_stage_key = cond_stage_key
        try:
            self.num_downs = len(first_stage_config.params.ddconfig.ch_mult) - 1
        except:
            self.num_downs = 0
        if not scale_by_std:
            self.scale_factor = scale_factor
        else:
            self.register_buffer('scale_factor', torch.tensor(scale_factor))
        self.instantiate_first_stage(first_stage_config)
        self.instantiate_cond_stage(cond_stage_config)
        self.cond_stage_forward = cond_stage_forward
        self.clip_denoised = False
        self.bbox_tokenizer = None
        self.restarted_from_ckpt = False
        if ckpt_path is not None:
            self.init_from_ckpt(ckpt_path, ignore_keys)
            self.restarted_from_ckpt = True

    def make_cond_schedule(self):
        self.cond_ids = torch.full(size=(self.num_timesteps,), fill_value=self.num_timesteps - 1, dtype=torch.long)
        ids = torch.round(torch.linspace(0, self.num_timesteps - 1, self.num_timesteps_cond)).long()
        self.cond_ids[:self.num_timesteps_cond] = ids

    @rank_zero_only
    @torch.no_grad()
    def on_train_batch_start(self, batch, batch_idx, dataloader_idx):
        if self.scale_by_std and self.current_epoch == 0 and (self.global_step == 0) and (batch_idx == 0) and (not self.restarted_from_ckpt):
            assert self.scale_factor == 1.0, 'rather not use custom rescaling and std-rescaling simultaneously'
            print('### USING STD-RESCALING ###')
            x = super().get_input(batch, self.first_stage_key)
            x = x.to(self.device)
            encoder_posterior = self.encode_first_stage(x)
            z = self.get_first_stage_encoding(encoder_posterior).detach()
            del self.scale_factor
            self.register_buffer('scale_factor', 1.0 / z.flatten().std())
            print(f'setting self.scale_factor to {self.scale_factor}')
            print('### USING STD-RESCALING ###')

    def register_schedule(self, given_betas=None, beta_schedule='linear', timesteps=1000, linear_start=0.0001, linear_end=0.02, cosine_s=0.008):
        super().register_schedule(given_betas, beta_schedule, timesteps, linear_start, linear_end, cosine_s)
        self.shorten_cond_schedule = self.num_timesteps_cond > 1
        if self.shorten_cond_schedule:
            self.make_cond_schedule()

    def instantiate_first_stage(self, config):
        model = instantiate_from_config(config)
        self.first_stage_model = model.eval()
        self.first_stage_model.train = disabled_train
        for param in self.first_stage_model.parameters():
            param.requires_grad = False

    def instantiate_cond_stage(self, config):
        if not self.cond_stage_trainable:
            if config == '__is_first_stage__':
                print('Using first stage also as cond stage.')
                self.cond_stage_model = self.first_stage_model
            elif config == '__is_unconditional__':
                print(f'Training {self.__class__.__name__} as an unconditional model.')
                self.cond_stage_model = None
            else:
                model = instantiate_from_config(config)
                self.cond_stage_model = model.eval()
                self.cond_stage_model.train = disabled_train
                for param in self.cond_stage_model.parameters():
                    param.requires_grad = False
        else:
            assert config != '__is_first_stage__'
            assert config != '__is_unconditional__'
            model = instantiate_from_config(config)
            self.cond_stage_model = model

    def _get_denoise_row_from_list(self, samples, desc='', force_no_decoder_quantization=False):
        denoise_row = []
        for zd in tqdm(samples, desc=desc):
            denoise_row.append(self.decode_first_stage(zd.to(self.device), force_not_quantize=force_no_decoder_quantization))
        n_imgs_per_row = len(denoise_row)
        denoise_row = torch.stack(denoise_row)
        denoise_grid = rearrange(denoise_row, 'n b c h w -> b n c h w')
        denoise_grid = rearrange(denoise_grid, 'b n c h w -> (b n) c h w')
        denoise_grid = make_grid(denoise_grid, nrow=n_imgs_per_row)
        return denoise_grid

    def get_first_stage_encoding(self, encoder_posterior):
        if isinstance(encoder_posterior, DiagonalGaussianDistribution):
            z = encoder_posterior.sample()
        elif isinstance(encoder_posterior, torch.Tensor):
            z = encoder_posterior
        else:
            raise NotImplementedError(f"encoder_posterior of type '{type(encoder_posterior)}' not yet implemented")
        return self.scale_factor * z

    def get_learned_conditioning(self, c):
        if self.cond_stage_forward is None:
            if hasattr(self.cond_stage_model, 'encode') and callable(self.cond_stage_model.encode):
                c = self.cond_stage_model.encode(c)
                if isinstance(c, DiagonalGaussianDistribution):
                    c = c.mode()
            else:
                c = self.cond_stage_model(c)
        else:
            assert hasattr(self.cond_stage_model, self.cond_stage_forward)
            c = getattr(self.cond_stage_model, self.cond_stage_forward)(c)
        return c

    def meshgrid(self, h, w):
        y = torch.arange(0, h).view(h, 1, 1).repeat(1, w, 1)
        x = torch.arange(0, w).view(1, w, 1).repeat(h, 1, 1)
        arr = torch.cat([y, x], dim=-1)
        return arr

    def delta_border(self, h, w):
        """
        :param h: height
        :param w: width
        :return: normalized distance to image border,
         wtith min distance = 0 at border and max dist = 0.5 at image center
        """
        lower_right_corner = torch.tensor([h - 1, w - 1]).view(1, 1, 2)
        arr = self.meshgrid(h, w) / lower_right_corner
        dist_left_up = torch.min(arr, dim=-1, keepdims=True)[0]
        dist_right_down = torch.min(1 - arr, dim=-1, keepdims=True)[0]
        edge_dist = torch.min(torch.cat([dist_left_up, dist_right_down], dim=-1), dim=-1)[0]
        return edge_dist

    def get_weighting(self, h, w, Ly, Lx, device):
        weighting = self.delta_border(h, w)
        weighting = torch.clip(weighting, self.split_input_params['clip_min_weight'], self.split_input_params['clip_max_weight'])
        weighting = weighting.view(1, h * w, 1).repeat(1, 1, Ly * Lx).to(device)
        if self.split_input_params['tie_braker']:
            L_weighting = self.delta_border(Ly, Lx)
            L_weighting = torch.clip(L_weighting, self.split_input_params['clip_min_tie_weight'], self.split_input_params['clip_max_tie_weight'])
            L_weighting = L_weighting.view(1, 1, Ly * Lx).to(device)
            weighting = weighting * L_weighting
        return weighting

    def get_fold_unfold(self, x, kernel_size, stride, uf=1, df=1):
        """
        :param x: img of size (bs, c, h, w)
        :return: n img crops of size (n, bs, c, kernel_size[0], kernel_size[1])
        """
        bs, nc, h, w = x.shape
        Ly = (h - kernel_size[0]) // stride[0] + 1
        Lx = (w - kernel_size[1]) // stride[1] + 1
        if uf == 1 and df == 1:
            fold_params = dict(kernel_size=kernel_size, dilation=1, padding=0, stride=stride)
            unfold = torch.nn.Unfold(**fold_params)
            fold = torch.nn.Fold(output_size=x.shape[2:], **fold_params)
            weighting = self.get_weighting(kernel_size[0], kernel_size[1], Ly, Lx, x.device).to(x.dtype)
            normalization = fold(weighting).view(1, 1, h, w)
            weighting = weighting.view((1, 1, kernel_size[0], kernel_size[1], Ly * Lx))
        elif uf > 1 and df == 1:
            fold_params = dict(kernel_size=kernel_size, dilation=1, padding=0, stride=stride)
            unfold = torch.nn.Unfold(**fold_params)
            fold_params2 = dict(kernel_size=(kernel_size[0] * uf, kernel_size[0] * uf), dilation=1, padding=0, stride=(stride[0] * uf, stride[1] * uf))
            fold = torch.nn.Fold(output_size=(x.shape[2] * uf, x.shape[3] * uf), **fold_params2)
            weighting = self.get_weighting(kernel_size[0] * uf, kernel_size[1] * uf, Ly, Lx, x.device).to(x.dtype)
            normalization = fold(weighting).view(1, 1, h * uf, w * uf)
            weighting = weighting.view((1, 1, kernel_size[0] * uf, kernel_size[1] * uf, Ly * Lx))
        elif df > 1 and uf == 1:
            fold_params = dict(kernel_size=kernel_size, dilation=1, padding=0, stride=stride)
            unfold = torch.nn.Unfold(**fold_params)
            fold_params2 = dict(kernel_size=(kernel_size[0] // df, kernel_size[0] // df), dilation=1, padding=0, stride=(stride[0] // df, stride[1] // df))
            fold = torch.nn.Fold(output_size=(x.shape[2] // df, x.shape[3] // df), **fold_params2)
            weighting = self.get_weighting(kernel_size[0] // df, kernel_size[1] // df, Ly, Lx, x.device).to(x.dtype)
            normalization = fold(weighting).view(1, 1, h // df, w // df)
            weighting = weighting.view((1, 1, kernel_size[0] // df, kernel_size[1] // df, Ly * Lx))
        else:
            raise NotImplementedError
        return (fold, unfold, normalization, weighting)

    @torch.no_grad()
    def get_input(self, batch, k, return_first_stage_outputs=False, force_c_encode=False, cond_key=None, return_original_cond=False, bs=None):
        x = super().get_input(batch, k)
        if bs is not None:
            x = x[:bs]
        x = x.to(self.device)
        encoder_posterior = self.encode_first_stage(x)
        z = self.get_first_stage_encoding(encoder_posterior).detach()
        if self.model.conditioning_key is not None:
            if cond_key is None:
                cond_key = self.cond_stage_key
            if cond_key != self.first_stage_key:
                if cond_key in ['caption', 'coordinates_bbox']:
                    xc = batch[cond_key]
                elif cond_key == 'class_label':
                    xc = batch
                else:
                    xc = super().get_input(batch, cond_key).to(self.device)
            else:
                xc = x
            if not self.cond_stage_trainable or force_c_encode:
                if isinstance(xc, dict) or isinstance(xc, list):
                    c = self.get_learned_conditioning(xc)
                else:
                    c = self.get_learned_conditioning(xc.to(self.device))
            else:
                c = xc
            if bs is not None:
                c = c[:bs]
            if self.use_positional_encodings:
                pos_x, pos_y = self.compute_latent_shifts(batch)
                ckey = __conditioning_keys__[self.model.conditioning_key]
                c = {ckey: c, 'pos_x': pos_x, 'pos_y': pos_y}
        else:
            c = None
            xc = None
            if self.use_positional_encodings:
                pos_x, pos_y = self.compute_latent_shifts(batch)
                c = {'pos_x': pos_x, 'pos_y': pos_y}
        out = [z, c]
        if return_first_stage_outputs:
            xrec = self.decode_first_stage(z)
            out.extend([x, xrec])
        if return_original_cond:
            out.append(xc)
        return out

    @torch.no_grad()
    def decode_first_stage(self, z, predict_cids=False, force_not_quantize=False):
        if predict_cids:
            if z.dim() == 4:
                z = torch.argmax(z.exp(), dim=1).long()
            z = self.first_stage_model.quantize.get_codebook_entry(z, shape=None)
            z = rearrange(z, 'b h w c -> b c h w').contiguous()
        z = 1.0 / self.scale_factor * z
        if hasattr(self, 'split_input_params'):
            if self.split_input_params['patch_distributed_vq']:
                ks = self.split_input_params['ks']
                stride = self.split_input_params['stride']
                uf = self.split_input_params['vqf']
                bs, nc, h, w = z.shape
                if ks[0] > h or ks[1] > w:
                    ks = (min(ks[0], h), min(ks[1], w))
                    print('reducing Kernel')
                if stride[0] > h or stride[1] > w:
                    stride = (min(stride[0], h), min(stride[1], w))
                    print('reducing stride')
                fold, unfold, normalization, weighting = self.get_fold_unfold(z, ks, stride, uf=uf)
                z = unfold(z)
                z = z.view((z.shape[0], -1, ks[0], ks[1], z.shape[-1]))
                if isinstance(self.first_stage_model, VQModelInterface):
                    output_list = [self.first_stage_model.decode(z[:, :, :, :, i], force_not_quantize=predict_cids or force_not_quantize) for i in range(z.shape[-1])]
                else:
                    output_list = [self.first_stage_model.decode(z[:, :, :, :, i]) for i in range(z.shape[-1])]
                o = torch.stack(output_list, axis=-1)
                o = o * weighting
                o = o.view((o.shape[0], -1, o.shape[-1]))
                decoded = fold(o)
                decoded = decoded / normalization
                return decoded
            elif isinstance(self.first_stage_model, VQModelInterface):
                return self.first_stage_model.decode(z, force_not_quantize=predict_cids or force_not_quantize)
            else:
                return self.first_stage_model.decode(z)
        elif isinstance(self.first_stage_model, VQModelInterface):
            return self.first_stage_model.decode(z, force_not_quantize=predict_cids or force_not_quantize)
        else:
            return self.first_stage_model.decode(z)

    def differentiable_decode_first_stage(self, z, predict_cids=False, force_not_quantize=False):
        if predict_cids:
            if z.dim() == 4:
                z = torch.argmax(z.exp(), dim=1).long()
            z = self.first_stage_model.quantize.get_codebook_entry(z, shape=None)
            z = rearrange(z, 'b h w c -> b c h w').contiguous()
        z = 1.0 / self.scale_factor * z
        if hasattr(self, 'split_input_params'):
            if self.split_input_params['patch_distributed_vq']:
                ks = self.split_input_params['ks']
                stride = self.split_input_params['stride']
                uf = self.split_input_params['vqf']
                bs, nc, h, w = z.shape
                if ks[0] > h or ks[1] > w:
                    ks = (min(ks[0], h), min(ks[1], w))
                    print('reducing Kernel')
                if stride[0] > h or stride[1] > w:
                    stride = (min(stride[0], h), min(stride[1], w))
                    print('reducing stride')
                fold, unfold, normalization, weighting = self.get_fold_unfold(z, ks, stride, uf=uf)
                z = unfold(z)
                z = z.view((z.shape[0], -1, ks[0], ks[1], z.shape[-1]))
                if isinstance(self.first_stage_model, VQModelInterface):
                    output_list = [self.first_stage_model.decode(z[:, :, :, :, i], force_not_quantize=predict_cids or force_not_quantize) for i in range(z.shape[-1])]
                else:
                    output_list = [self.first_stage_model.decode(z[:, :, :, :, i]) for i in range(z.shape[-1])]
                o = torch.stack(output_list, axis=-1)
                o = o * weighting
                o = o.view((o.shape[0], -1, o.shape[-1]))
                decoded = fold(o)
                decoded = decoded / normalization
                return decoded
            elif isinstance(self.first_stage_model, VQModelInterface):
                return self.first_stage_model.decode(z, force_not_quantize=predict_cids or force_not_quantize)
            else:
                return self.first_stage_model.decode(z)
        elif isinstance(self.first_stage_model, VQModelInterface):
            return self.first_stage_model.decode(z, force_not_quantize=predict_cids or force_not_quantize)
        else:
            return self.first_stage_model.decode(z)

    @torch.no_grad()
    def encode_first_stage(self, x):
        if hasattr(self, 'split_input_params'):
            if self.split_input_params['patch_distributed_vq']:
                ks = self.split_input_params['ks']
                stride = self.split_input_params['stride']
                df = self.split_input_params['vqf']
                self.split_input_params['original_image_size'] = x.shape[-2:]
                bs, nc, h, w = x.shape
                if ks[0] > h or ks[1] > w:
                    ks = (min(ks[0], h), min(ks[1], w))
                    print('reducing Kernel')
                if stride[0] > h or stride[1] > w:
                    stride = (min(stride[0], h), min(stride[1], w))
                    print('reducing stride')
                fold, unfold, normalization, weighting = self.get_fold_unfold(x, ks, stride, df=df)
                z = unfold(x)
                z = z.view((z.shape[0], -1, ks[0], ks[1], z.shape[-1]))
                output_list = [self.first_stage_model.encode(z[:, :, :, :, i]) for i in range(z.shape[-1])]
                o = torch.stack(output_list, axis=-1)
                o = o * weighting
                o = o.view((o.shape[0], -1, o.shape[-1]))
                decoded = fold(o)
                decoded = decoded / normalization
                return decoded
            else:
                return self.first_stage_model.encode(x)
        else:
            return self.first_stage_model.encode(x)

    def shared_step(self, batch, **kwargs):
        x, c = self.get_input(batch, self.first_stage_key)
        loss = self(x, c)
        return loss

    def forward(self, x, c, *args, **kwargs):
        t = torch.randint(0, self.num_timesteps, (x.shape[0],), device=self.device).long()
        if self.model.conditioning_key is not None:
            assert c is not None
            if self.cond_stage_trainable:
                c = self.get_learned_conditioning(c)
            if self.shorten_cond_schedule:
                tc = self.cond_ids[t].to(self.device)
                c = self.q_sample(x_start=c, t=tc, noise=torch.randn_like(c.float()))
        return self.p_losses(x, c, t, *args, **kwargs)

    def _rescale_annotations(self, bboxes, crop_coordinates):

        def rescale_bbox(bbox):
            x0 = clamp((bbox[0] - crop_coordinates[0]) / crop_coordinates[2])
            y0 = clamp((bbox[1] - crop_coordinates[1]) / crop_coordinates[3])
            w = min(bbox[2] / crop_coordinates[2], 1 - x0)
            h = min(bbox[3] / crop_coordinates[3], 1 - y0)
            return (x0, y0, w, h)
        return [rescale_bbox(b) for b in bboxes]

    def apply_model(self, x_noisy, t, cond, return_ids=False):
        if isinstance(cond, dict):
            pass
        else:
            if not isinstance(cond, list):
                cond = [cond]
            key = 'c_concat' if self.model.conditioning_key == 'concat' else 'c_crossattn'
            cond = {key: cond}
        if hasattr(self, 'split_input_params'):
            assert len(cond) == 1
            assert not return_ids
            ks = self.split_input_params['ks']
            stride = self.split_input_params['stride']
            h, w = x_noisy.shape[-2:]
            fold, unfold, normalization, weighting = self.get_fold_unfold(x_noisy, ks, stride)
            z = unfold(x_noisy)
            z = z.view((z.shape[0], -1, ks[0], ks[1], z.shape[-1]))
            z_list = [z[:, :, :, :, i] for i in range(z.shape[-1])]
            if self.cond_stage_key in ['image', 'LR_image', 'segmentation', 'bbox_img'] and self.model.conditioning_key:
                c_key = next(iter(cond.keys()))
                c = next(iter(cond.values()))
                assert len(c) == 1
                c = c[0]
                c = unfold(c)
                c = c.view((c.shape[0], -1, ks[0], ks[1], c.shape[-1]))
                cond_list = [{c_key: [c[:, :, :, :, i]]} for i in range(c.shape[-1])]
            elif self.cond_stage_key == 'coordinates_bbox':
                assert 'original_image_size' in self.split_input_params, 'BoudingBoxRescaling is missing original_image_size'
                n_patches_per_row = int((w - ks[0]) / stride[0] + 1)
                full_img_h, full_img_w = self.split_input_params['original_image_size']
                num_downs = self.first_stage_model.encoder.num_resolutions - 1
                rescale_latent = 2 ** num_downs
                tl_patch_coordinates = [(rescale_latent * stride[0] * (patch_nr % n_patches_per_row) / full_img_w, rescale_latent * stride[1] * (patch_nr // n_patches_per_row) / full_img_h) for patch_nr in range(z.shape[-1])]
                patch_limits = [(x_tl, y_tl, rescale_latent * ks[0] / full_img_w, rescale_latent * ks[1] / full_img_h) for x_tl, y_tl in tl_patch_coordinates]
                patch_limits_tknzd = [torch.LongTensor(self.bbox_tokenizer._crop_encoder(bbox))[None].to(self.device) for bbox in patch_limits]
                print(patch_limits_tknzd[0].shape)
                assert isinstance(cond, dict), 'cond must be dict to be fed into model'
                cut_cond = cond['c_crossattn'][0][..., :-2].to(self.device)
                print(cut_cond.shape)
                adapted_cond = torch.stack([torch.cat([cut_cond, p], dim=1) for p in patch_limits_tknzd])
                adapted_cond = rearrange(adapted_cond, 'l b n -> (l b) n')
                print(adapted_cond.shape)
                adapted_cond = self.get_learned_conditioning(adapted_cond)
                print(adapted_cond.shape)
                adapted_cond = rearrange(adapted_cond, '(l b) n d -> l b n d', l=z.shape[-1])
                print(adapted_cond.shape)
                cond_list = [{'c_crossattn': [e]} for e in adapted_cond]
            else:
                cond_list = [cond for i in range(z.shape[-1])]
            output_list = [self.model(z_list[i], t, **cond_list[i]) for i in range(z.shape[-1])]
            assert not isinstance(output_list[0], tuple)
            o = torch.stack(output_list, axis=-1)
            o = o * weighting
            o = o.view((o.shape[0], -1, o.shape[-1]))
            x_recon = fold(o) / normalization
        else:
            x_recon = self.model(x_noisy, t, **cond)
        if isinstance(x_recon, tuple) and (not return_ids):
            return x_recon[0]
        else:
            return x_recon

    def _predict_eps_from_xstart(self, x_t, t, pred_xstart):
        return (extract_into_tensor(self.sqrt_recip_alphas_cumprod, t, x_t.shape) * x_t - pred_xstart) / extract_into_tensor(self.sqrt_recipm1_alphas_cumprod, t, x_t.shape)

    def _prior_bpd(self, x_start):
        """
        Get the prior KL term for the variational lower-bound, measured in
        bits-per-dim.
        This term can't be optimized, as it only depends on the encoder.
        :param x_start: the [N x C x ...] tensor of inputs.
        :return: a batch of [N] KL values (in bits), one per batch element.
        """
        batch_size = x_start.shape[0]
        t = torch.tensor([self.num_timesteps - 1] * batch_size, device=x_start.device)
        qt_mean, _, qt_log_variance = self.q_mean_variance(x_start, t)
        kl_prior = normal_kl(mean1=qt_mean, logvar1=qt_log_variance, mean2=0.0, logvar2=0.0)
        return mean_flat(kl_prior) / np.log(2.0)

    def p_losses(self, x_start, cond, t, noise=None):
        noise = default(noise, lambda: torch.randn_like(x_start))
        x_noisy = self.q_sample(x_start=x_start, t=t, noise=noise)
        model_output = self.apply_model(x_noisy, t, cond)
        loss_dict = {}
        prefix = 'train' if self.training else 'val'
        if self.parameterization == 'x0':
            target = x_start
        elif self.parameterization == 'eps':
            target = noise
        else:
            raise NotImplementedError()
        loss_simple = self.get_loss(model_output, target, mean=False).mean([1, 2, 3])
        loss_dict.update({f'{prefix}/loss_simple': loss_simple.mean()})
        logvar_t = self.logvar[t].to(self.device)
        loss = loss_simple / torch.exp(logvar_t) + logvar_t
        if self.learn_logvar:
            loss_dict.update({f'{prefix}/loss_gamma': loss.mean()})
            loss_dict.update({'logvar': self.logvar.data.mean()})
        loss = self.l_simple_weight * loss.mean()
        loss_vlb = self.get_loss(model_output, target, mean=False).mean(dim=(1, 2, 3))
        loss_vlb = (self.lvlb_weights[t] * loss_vlb).mean()
        loss_dict.update({f'{prefix}/loss_vlb': loss_vlb})
        loss += self.original_elbo_weight * loss_vlb
        loss_dict.update({f'{prefix}/loss': loss})
        return (loss, loss_dict)

    def p_mean_variance(self, x, c, t, clip_denoised: bool, return_codebook_ids=False, quantize_denoised=False, return_x0=False, score_corrector=None, corrector_kwargs=None):
        t_in = t
        model_out = self.apply_model(x, t_in, c, return_ids=return_codebook_ids)
        if score_corrector is not None:
            assert self.parameterization == 'eps'
            model_out = score_corrector.modify_score(self, model_out, x, t, c, **corrector_kwargs)
        if return_codebook_ids:
            model_out, logits = model_out
        if self.parameterization == 'eps':
            x_recon = self.predict_start_from_noise(x, t=t, noise=model_out)
        elif self.parameterization == 'x0':
            x_recon = model_out
        else:
            raise NotImplementedError()
        if clip_denoised:
            x_recon.clamp_(-1.0, 1.0)
        if quantize_denoised:
            x_recon, _, [_, _, indices] = self.first_stage_model.quantize(x_recon)
        model_mean, posterior_variance, posterior_log_variance = self.q_posterior(x_start=x_recon, x_t=x, t=t)
        if return_codebook_ids:
            return (model_mean, posterior_variance, posterior_log_variance, logits)
        elif return_x0:
            return (model_mean, posterior_variance, posterior_log_variance, x_recon)
        else:
            return (model_mean, posterior_variance, posterior_log_variance)

    @torch.no_grad()
    def p_sample(self, x, c, t, clip_denoised=False, repeat_noise=False, return_codebook_ids=False, quantize_denoised=False, return_x0=False, temperature=1.0, noise_dropout=0.0, score_corrector=None, corrector_kwargs=None):
        b, *_, device = (*x.shape, x.device)
        outputs = self.p_mean_variance(x=x, c=c, t=t, clip_denoised=clip_denoised, return_codebook_ids=return_codebook_ids, quantize_denoised=quantize_denoised, return_x0=return_x0, score_corrector=score_corrector, corrector_kwargs=corrector_kwargs)
        if return_codebook_ids:
            raise DeprecationWarning('Support dropped.')
            model_mean, _, model_log_variance, logits = outputs
        elif return_x0:
            model_mean, _, model_log_variance, x0 = outputs
        else:
            model_mean, _, model_log_variance = outputs
        noise = noise_like(x.shape, device, repeat_noise) * temperature
        if noise_dropout > 0.0:
            noise = torch.nn.functional.dropout(noise, p=noise_dropout)
        nonzero_mask = (1 - (t == 0).float()).reshape(b, *(1,) * (len(x.shape) - 1))
        if return_codebook_ids:
            return (model_mean + nonzero_mask * (0.5 * model_log_variance).exp() * noise, logits.argmax(dim=1))
        if return_x0:
            return (model_mean + nonzero_mask * (0.5 * model_log_variance).exp() * noise, x0)
        else:
            return model_mean + nonzero_mask * (0.5 * model_log_variance).exp() * noise

    @torch.no_grad()
    def progressive_denoising(self, cond, shape, verbose=True, callback=None, quantize_denoised=False, img_callback=None, mask=None, x0=None, temperature=1.0, noise_dropout=0.0, score_corrector=None, corrector_kwargs=None, batch_size=None, x_T=None, start_T=None, log_every_t=None):
        if not log_every_t:
            log_every_t = self.log_every_t
        timesteps = self.num_timesteps
        if batch_size is not None:
            b = batch_size if batch_size is not None else shape[0]
            shape = [batch_size] + list(shape)
        else:
            b = batch_size = shape[0]
        if x_T is None:
            img = torch.randn(shape, device=self.device)
        else:
            img = x_T
        intermediates = []
        if cond is not None:
            if isinstance(cond, dict):
                cond = {key: cond[key][:batch_size] if not isinstance(cond[key], list) else list(map(lambda x: x[:batch_size], cond[key])) for key in cond}
            else:
                cond = [c[:batch_size] for c in cond] if isinstance(cond, list) else cond[:batch_size]
        if start_T is not None:
            timesteps = min(timesteps, start_T)
        iterator = tqdm(reversed(range(0, timesteps)), desc='Progressive Generation', total=timesteps) if verbose else reversed(range(0, timesteps))
        if type(temperature) == float:
            temperature = [temperature] * timesteps
        for i in iterator:
            ts = torch.full((b,), i, device=self.device, dtype=torch.long)
            if self.shorten_cond_schedule:
                assert self.model.conditioning_key != 'hybrid'
                tc = self.cond_ids[ts].to(cond.device)
                cond = self.q_sample(x_start=cond, t=tc, noise=torch.randn_like(cond))
            img, x0_partial = self.p_sample(img, cond, ts, clip_denoised=self.clip_denoised, quantize_denoised=quantize_denoised, return_x0=True, temperature=temperature[i], noise_dropout=noise_dropout, score_corrector=score_corrector, corrector_kwargs=corrector_kwargs)
            if mask is not None:
                assert x0 is not None
                img_orig = self.q_sample(x0, ts)
                img = img_orig * mask + (1.0 - mask) * img
            if i % log_every_t == 0 or i == timesteps - 1:
                intermediates.append(x0_partial)
            if callback:
                callback(i)
            if img_callback:
                img_callback(img, i)
        return (img, intermediates)

    @torch.no_grad()
    def p_sample_loop(self, cond, shape, return_intermediates=False, x_T=None, verbose=True, callback=None, timesteps=None, quantize_denoised=False, mask=None, x0=None, img_callback=None, start_T=None, log_every_t=None):
        if not log_every_t:
            log_every_t = self.log_every_t
        device = self.betas.device
        b = shape[0]
        if x_T is None:
            img = torch.randn(shape, device=device)
        else:
            img = x_T
        intermediates = [img]
        if timesteps is None:
            timesteps = self.num_timesteps
        if start_T is not None:
            timesteps = min(timesteps, start_T)
        iterator = tqdm(reversed(range(0, timesteps)), desc='Sampling t', total=timesteps) if verbose else reversed(range(0, timesteps))
        if mask is not None:
            assert x0 is not None
            assert x0.shape[2:3] == mask.shape[2:3]
        for i in iterator:
            ts = torch.full((b,), i, device=device, dtype=torch.long)
            if self.shorten_cond_schedule:
                assert self.model.conditioning_key != 'hybrid'
                tc = self.cond_ids[ts].to(cond.device)
                cond = self.q_sample(x_start=cond, t=tc, noise=torch.randn_like(cond))
            img = self.p_sample(img, cond, ts, clip_denoised=self.clip_denoised, quantize_denoised=quantize_denoised)
            if mask is not None:
                img_orig = self.q_sample(x0, ts)
                img = img_orig * mask + (1.0 - mask) * img
            if i % log_every_t == 0 or i == timesteps - 1:
                intermediates.append(img)
            if callback:
                callback(i)
            if img_callback:
                img_callback(img, i)
        if return_intermediates:
            return (img, intermediates)
        return img

    @torch.no_grad()
    def sample(self, cond, batch_size=16, return_intermediates=False, x_T=None, verbose=True, timesteps=None, quantize_denoised=False, mask=None, x0=None, shape=None, **kwargs):
        if shape is None:
            shape = (batch_size, self.channels, self.image_size, self.image_size)
        if cond is not None:
            if isinstance(cond, dict):
                cond = {key: cond[key][:batch_size] if not isinstance(cond[key], list) else list(map(lambda x: x[:batch_size], cond[key])) for key in cond}
            else:
                cond = [c[:batch_size] for c in cond] if isinstance(cond, list) else cond[:batch_size]
        return self.p_sample_loop(cond, shape, return_intermediates=return_intermediates, x_T=x_T, verbose=verbose, timesteps=timesteps, quantize_denoised=quantize_denoised, mask=mask, x0=x0)

    @torch.no_grad()
    def sample_log(self, cond, batch_size, ddim, ddim_steps, **kwargs):
        if ddim:
            ddim_sampler = DDIMSampler(self)
            shape = (self.channels, self.image_size, self.image_size)
            samples, intermediates = ddim_sampler.sample(ddim_steps, batch_size, shape, cond, verbose=False, **kwargs)
        else:
            samples, intermediates = self.sample(cond=cond, batch_size=batch_size, return_intermediates=True, **kwargs)
        return (samples, intermediates)

    @torch.no_grad()
    def log_images(self, batch, N=8, n_row=4, sample=True, ddim_steps=200, ddim_eta=1.0, return_keys=None, quantize_denoised=True, inpaint=True, plot_denoise_rows=False, plot_progressive_rows=True, plot_diffusion_rows=True, **kwargs):
        use_ddim = ddim_steps is not None
        log = dict()
        z, c, x, xrec, xc = self.get_input(batch, self.first_stage_key, return_first_stage_outputs=True, force_c_encode=True, return_original_cond=True, bs=N)
        N = min(x.shape[0], N)
        n_row = min(x.shape[0], n_row)
        log['inputs'] = x
        log['reconstruction'] = xrec
        if self.model.conditioning_key is not None:
            if hasattr(self.cond_stage_model, 'decode'):
                xc = self.cond_stage_model.decode(c)
                log['conditioning'] = xc
            elif self.cond_stage_key in ['caption']:
                xc = log_txt_as_img((x.shape[2], x.shape[3]), batch['caption'])
                log['conditioning'] = xc
            elif self.cond_stage_key == 'class_label':
                xc = log_txt_as_img((x.shape[2], x.shape[3]), batch['human_label'])
                log['conditioning'] = xc
            elif isimage(xc):
                log['conditioning'] = xc
            if ismap(xc):
                log['original_conditioning'] = self.to_rgb(xc)
        if plot_diffusion_rows:
            diffusion_row = list()
            z_start = z[:n_row]
            for t in range(self.num_timesteps):
                if t % self.log_every_t == 0 or t == self.num_timesteps - 1:
                    t = repeat(torch.tensor([t]), '1 -> b', b=n_row)
                    t = t.to(self.device).long()
                    noise = torch.randn_like(z_start)
                    z_noisy = self.q_sample(x_start=z_start, t=t, noise=noise)
                    diffusion_row.append(self.decode_first_stage(z_noisy))
            diffusion_row = torch.stack(diffusion_row)
            diffusion_grid = rearrange(diffusion_row, 'n b c h w -> b n c h w')
            diffusion_grid = rearrange(diffusion_grid, 'b n c h w -> (b n) c h w')
            diffusion_grid = make_grid(diffusion_grid, nrow=diffusion_row.shape[0])
            log['diffusion_row'] = diffusion_grid
        if sample:
            with self.ema_scope('Plotting'):
                samples, z_denoise_row = self.sample_log(cond=c, batch_size=N, ddim=use_ddim, ddim_steps=ddim_steps, eta=ddim_eta)
            x_samples = self.decode_first_stage(samples)
            log['samples'] = x_samples
            if plot_denoise_rows:
                denoise_grid = self._get_denoise_row_from_list(z_denoise_row)
                log['denoise_row'] = denoise_grid
            if quantize_denoised and (not isinstance(self.first_stage_model, AutoencoderKL)) and (not isinstance(self.first_stage_model, IdentityFirstStage)):
                with self.ema_scope('Plotting Quantized Denoised'):
                    samples, z_denoise_row = self.sample_log(cond=c, batch_size=N, ddim=use_ddim, ddim_steps=ddim_steps, eta=ddim_eta, quantize_denoised=True)
                x_samples = self.decode_first_stage(samples.to(self.device))
                log['samples_x0_quantized'] = x_samples
            if inpaint:
                b, h, w = (z.shape[0], z.shape[2], z.shape[3])
                mask = torch.ones(N, h, w).to(self.device)
                mask[:, h // 4:3 * h // 4, w // 4:3 * w // 4] = 0.0
                mask = mask[:, None, ...]
                with self.ema_scope('Plotting Inpaint'):
                    samples, _ = self.sample_log(cond=c, batch_size=N, ddim=use_ddim, eta=ddim_eta, ddim_steps=ddim_steps, x0=z[:N], mask=mask)
                x_samples = self.decode_first_stage(samples.to(self.device))
                log['samples_inpainting'] = x_samples
                log['mask'] = mask
                with self.ema_scope('Plotting Outpaint'):
                    samples, _ = self.sample_log(cond=c, batch_size=N, ddim=use_ddim, eta=ddim_eta, ddim_steps=ddim_steps, x0=z[:N], mask=mask)
                x_samples = self.decode_first_stage(samples.to(self.device))
                log['samples_outpainting'] = x_samples
        if plot_progressive_rows:
            with self.ema_scope('Plotting Progressives'):
                img, progressives = self.progressive_denoising(c, shape=(self.channels, self.image_size, self.image_size), batch_size=N)
            prog_row = self._get_denoise_row_from_list(progressives, desc='Progressive Generation')
            log['progressive_row'] = prog_row
        if return_keys:
            if np.intersect1d(list(log.keys()), return_keys).shape[0] == 0:
                return log
            else:
                return {key: log[key] for key in return_keys}
        return log

    def configure_optimizers(self):
        lr = self.learning_rate
        params = list(self.model.parameters())
        if self.cond_stage_trainable:
            print(f'{self.__class__.__name__}: Also optimizing conditioner params!')
            params = params + list(self.cond_stage_model.parameters())
        if self.learn_logvar:
            print('Diffusion model optimizing logvar')
            params.append(self.logvar)
        opt = torch.optim.AdamW(params, lr=lr)
        if self.use_scheduler:
            assert 'target' in self.scheduler_config
            scheduler = instantiate_from_config(self.scheduler_config)
            print('Setting up LambdaLR scheduler...')
            scheduler = [{'scheduler': LambdaLR(opt, lr_lambda=scheduler.schedule), 'interval': 'step', 'frequency': 1}]
            return ([opt], scheduler)
        return opt

    @torch.no_grad()
    def to_rgb(self, x):
        x = x.float()
        if not hasattr(self, 'colorize'):
            self.colorize = torch.randn(3, x.shape[1], 1, 1).to(x)
        x = nn.functional.conv2d(x, weight=self.colorize)
        x = 2.0 * (x - x.min()) / (x.max() - x.min()) - 1.0
        return x

def meshgrid(self, h, w):
    y = torch.arange(0, h).view(h, 1, 1).repeat(1, w, 1)
    x = torch.arange(0, w).view(1, w, 1).repeat(h, 1, 1)
    arr = torch.cat([y, x], dim=-1)
    return arr

def delta_border(self, h, w):
    """
        :param h: height
        :param w: width
        :return: normalized distance to image border,
         wtith min distance = 0 at border and max dist = 0.5 at image center
        """
    lower_right_corner = torch.tensor([h - 1, w - 1]).view(1, 1, 2)
    arr = self.meshgrid(h, w) / lower_right_corner
    dist_left_up = torch.min(arr, dim=-1, keepdims=True)[0]
    dist_right_down = torch.min(1 - arr, dim=-1, keepdims=True)[0]
    edge_dist = torch.min(torch.cat([dist_left_up, dist_right_down], dim=-1), dim=-1)[0]
    return edge_dist

def get_weighting(self, h, w, Ly, Lx, device):
    weighting = self.delta_border(h, w)
    weighting = torch.clip(weighting, self.split_input_params['clip_min_weight'], self.split_input_params['clip_max_weight'])
    weighting = weighting.view(1, h * w, 1).repeat(1, 1, Ly * Lx).to(device)
    if self.split_input_params['tie_braker']:
        L_weighting = self.delta_border(Ly, Lx)
        L_weighting = torch.clip(L_weighting, self.split_input_params['clip_min_tie_weight'], self.split_input_params['clip_max_tie_weight'])
        L_weighting = L_weighting.view(1, 1, Ly * Lx).to(device)
        weighting = weighting * L_weighting
    return weighting

def rescale_bbox(bbox):
    x0 = clamp((bbox[0] - crop_coordinates[0]) / crop_coordinates[2])
    y0 = clamp((bbox[1] - crop_coordinates[1]) / crop_coordinates[3])
    w = min(bbox[2] / crop_coordinates[2], 1 - x0)
    h = min(bbox[3] / crop_coordinates[3], 1 - y0)
    return (x0, y0, w, h)

def srgb_gamma_correction(linear_image):
    """
    linear_image: np.ndarray
        shape: H*W*C
    """
    linear_image = np.clip(linear_image, 0, 1)
    gamma_corrected_image = np.where(linear_image <= 0.0031308, linear_image * 12.92, 1.055 * linear_image ** (1 / 2.4) - 0.055)
    gamma_corrected_image = np.clip(gamma_corrected_image, 0, 1)
    return gamma_corrected_image

def srgb_inv_gamma_correction(gamma_corrected_image):
    gamma_corrected_image = np.clip(gamma_corrected_image, 0, 1)
    linear_image = np.where(gamma_corrected_image <= 0.04045, gamma_corrected_image / 12.92, ((gamma_corrected_image + 0.055) / 1.055) ** 2.4)
    return linear_image

def generate_rays(insert_x, insert_y, int_ext_path, nerf_exp_dir):
    near = 0.01
    far = 1000.0
    origin = np.array([insert_x, insert_y, 0.0])
    cam_meta = np.load(int_ext_path)
    extrinsic = cam_meta[:, :12].reshape(-1, 3, 4)
    translation = extrinsic[:, :3, 3].copy()
    center = np.mean(translation, axis=0)
    bias = translation - center[None]
    radius = np.linalg.norm(bias, 2, -1, False).max()
    translation = (translation - center[None]) / radius
    extrinsic[:, :, 3] = translation
    origin = (origin - center) / radius
    dy = np.linspace(0, 1, 1280)
    dx = np.linspace(0, 1, 1280 * 4)
    u, v = np.meshgrid(dx, dy)
    u, v = (u.ravel()[..., None], v.ravel()[..., None])
    rays_d = skylatlong2world(u, v)
    rays_o = np.tile(origin[None], (len(rays_d), 1))
    bounds = np.array([[near, far]]).repeat(len(rays_d), axis=0)
    np.save(os.path.join(nerf_exp_dir, 'rays_o.npy'), rays_o.astype(np.float32))
    np.save(os.path.join(nerf_exp_dir, 'rays_d.npy'), rays_d.astype(np.float32))
    np.save(os.path.join(nerf_exp_dir, 'bounds.npy'), bounds.astype(np.float32))

def totensor(x: np.ndarray):
    if len(x.shape) == 3:
        return torch.from_numpy(x.astype(np.float32)).permute(2, 0, 1)
    return torch.from_numpy(x.astype(np.float32))

def srgb_gamma_correction(linear_image):
    """
    linear_image: np.ndarray
        shape: H*W*C
    """
    linear_image = np.clip(linear_image, 0, 1)
    gamma_corrected_image = np.where(linear_image <= 0.0031308, linear_image * 12.92, 1.055 * linear_image ** (1 / 2.4) - 0.055)
    gamma_corrected_image = np.clip(gamma_corrected_image, 0, 1)
    return gamma_corrected_image

def srgb_inv_gamma_correction(gamma_corrected_image):
    gamma_corrected_image = np.clip(gamma_corrected_image, 0, 1)
    linear_image = np.where(gamma_corrected_image <= 0.04045, gamma_corrected_image / 12.92, ((gamma_corrected_image + 0.055) / 1.055) ** 2.4)
    linear_image = np.clip(linear_image, 0, 1)
    return linear_image

def srgb_gamma_correction_torch(linear_image):
    """
    linear_image: torch.tensor
        shape: H*W*C
    """
    linear_image = torch.clamp(linear_image, 0, 1)
    gamma_corrected_image = torch.where(linear_image <= 0.0031308, linear_image * 12.92, 1.055 * linear_image ** (1 / 2.4) - 0.055)
    gamma_corrected_image = torch.clamp(gamma_corrected_image, 0, 1)
    return gamma_corrected_image

def srgb_inv_gamma_correction_torch(gamma_corrected_image):
    gamma_corrected_image = torch.clamp(gamma_corrected_image, 0, 1)
    linear_image = torch.where(gamma_corrected_image <= 0.04045, gamma_corrected_image / 12.92, ((gamma_corrected_image + 0.055) / 1.055) ** 2.4)
    linear_image = torch.clamp(linear_image, 0, 1)
    return linear_image

def random_sample_on_hemisphere(normal):
    random_direction = torch.rand(3).to('cuda')
    random_direction = random_direction / random_direction.norm()
    dot_product = torch.dot(random_direction, normal)
    if dot_product < 0:
        random_direction = -random_direction
    return random_direction

def random_samples_on_hemisphere(normal, num_samples):
    random_direction = torch.rand(num_samples, 3).to('cuda')
    random_direction = random_direction / random_direction.norm(p=2, dim=1, keepdim=True)
    dot_product = torch.einsum('ij,ij->i', random_direction, normal).unsqueeze(-1)
    random_direction = torch.where(dot_product < 0, -random_direction, random_direction)
    return random_direction

def get_rays(directions, c2w, use_np=True):
    """
    Get ray origin and normalized directions in world coordinate for all pixels in one image.
    Reference: https://www.scratchapixel.com/lessons/3d-basic-rendering/
               ray-tracing-generating-camera-rays/standard-coordinate-systems

    Inputs:
        directions: (H, W, 3) precomputed ray directions in camera coordinate
        c2w: (3, 4) transformation matrix from camera coordinate to world coordinate

    Outputs:
        rays_o: (H*W, 3), the origin of the rays in world coordinate
        rays_d: (H*W, 3), the normalized direction of the rays in world coordinate
    """
    if use_np:
        directions = torch.from_numpy(directions)
        c2w = torch.from_numpy(c2w)
    rays_d = directions @ c2w[:, :3].T
    rays_d = rays_d / torch.norm(rays_d, dim=-1, keepdim=True)
    rays_o = c2w[:, 3].expand(rays_d.shape)
    rays_d = rays_d.view(-1, 3)
    rays_o = rays_o.view(-1, 3)
    if use_np:
        rays_d = rays_d.numpy()
        rays_o = rays_o.numpy()
    return (rays_o, rays_d)

class UE4BRDF:

    def __init__(self, base_color, metallic, roughness, specular):
        self.base_color = torch.tensor(base_color, dtype=torch.float64).cuda()
        self.base_color = srgb_inv_gamma_correction_torch(self.base_color)
        self.metallic = torch.tensor(metallic, dtype=torch.float64).cuda()
        self.roughness = torch.tensor(roughness, dtype=torch.float64).cuda().clamp(min=0.0001)
        self.specular = torch.tensor(specular, dtype=torch.float64).cuda()
        self.c_diffuse = (1 - self.metallic) * self.base_color
        self.c_specular = (1 - self.metallic) * self.specular + self.metallic * self.base_color

    def lambertian_diffuse(self):
        return self.c_diffuse / np.pi

    def fresnel_schlick(self, h_dot_v):
        return self.c_specular + (1 - self.c_specular) * torch.pow(1 - h_dot_v, 5).repeat_interleave(3, dim=-1)

    def smith_g1(self, n_dot_v):
        k = pow(self.roughness + 1, 2) / 8
        return n_dot_v / (n_dot_v * (1 - k) + k)

    def geometry(self, n_dot_v, n_dot_l):
        return self.smith_g1(n_dot_v) * self.smith_g1(n_dot_l)

    def normal_distribution(self, n, h):
        roughness = pow(self.roughness, 2)
        n_cross_h = torch.cross(n, h, dim=1)
        n_dot_h = torch.einsum('ij,ij->i', n, h).unsqueeze(-1)
        a = n_dot_h * roughness
        k = roughness / (torch.einsum('ij,ij->i', n_cross_h, n_cross_h).unsqueeze(-1) + a * a)
        d = k * k * (1 / np.pi)
        return d

    def evaluate(self, normal, light_dir, view_dir):
        n_dot_l = torch.clamp(torch.dot(normal, light_dir), min=1e-05)
        n_dot_v = torch.clamp(torch.dot(normal, view_dir), min=1e-05)
        half_dir = (light_dir + view_dir) / torch.norm(light_dir + view_dir)
        h_dot_v = torch.clamp(torch.dot(half_dir, view_dir), min=1e-05)
        n_dot_h = torch.clamp(torch.dot(normal, half_dir), min=1e-05)
        diffuse_term = self.lambertian_diffuse()
        specular_term = self.fresnel_schlick(h_dot_v) * self.geometry(n_dot_l, n_dot_v) * self.normal_distribution(normal, half_dir) / (4 * n_dot_l * n_dot_v)
        return diffuse_term + specular_term

    def evaluate_parallel(self, normal, light_dir, view_dir):
        """
        Args:
            normal: [num_samples, 3]
            light_dir: [num_samples, 3]
            view_dir: [num_samples]
        """
        normal = normal.double()
        light_dir = light_dir.double()
        view_dir = view_dir.double()
        num_samples = normal.shape[0]
        n_dot_l = torch.clamp(torch.einsum('ij,ij->i', normal, light_dir).unsqueeze(-1), min=1e-05)
        n_dot_v = torch.clamp(torch.einsum('ij,ij->i', normal, view_dir).unsqueeze(-1), min=1e-05)
        half_dir = (light_dir + view_dir) / torch.norm(light_dir + view_dir, p=2, dim=1, keepdim=True)
        h_dot_v = torch.clamp(torch.einsum('ij,ij->i', half_dir, view_dir).unsqueeze(-1), min=1e-05)
        diffuse_term = self.lambertian_diffuse().expand(num_samples, 3)
        specular_term = self.fresnel_schlick(h_dot_v) * self.geometry(n_dot_l, n_dot_v) * self.normal_distribution(normal, half_dir) / (4 * n_dot_l * n_dot_v)
        brdf = diffuse_term + specular_term
        return brdf.float()

def __init__(self, base_color, metallic, roughness, specular):
    self.base_color = torch.tensor(base_color, dtype=torch.float64).cuda()
    self.base_color = srgb_inv_gamma_correction_torch(self.base_color)
    self.metallic = torch.tensor(metallic, dtype=torch.float64).cuda()
    self.roughness = torch.tensor(roughness, dtype=torch.float64).cuda().clamp(min=0.0001)
    self.specular = torch.tensor(specular, dtype=torch.float64).cuda()
    self.c_diffuse = (1 - self.metallic) * self.base_color
    self.c_specular = (1 - self.metallic) * self.specular + self.metallic * self.base_color

def normal_distribution(self, n, h):
    roughness = pow(self.roughness, 2)
    n_cross_h = torch.cross(n, h, dim=1)
    n_dot_h = torch.einsum('ij,ij->i', n, h).unsqueeze(-1)
    a = n_dot_h * roughness
    k = roughness / (torch.einsum('ij,ij->i', n_cross_h, n_cross_h).unsqueeze(-1) + a * a)
    d = k * k * (1 / np.pi)
    return d

def evaluate(self, normal, light_dir, view_dir):
    n_dot_l = torch.clamp(torch.dot(normal, light_dir), min=1e-05)
    n_dot_v = torch.clamp(torch.dot(normal, view_dir), min=1e-05)
    half_dir = (light_dir + view_dir) / torch.norm(light_dir + view_dir)
    h_dot_v = torch.clamp(torch.dot(half_dir, view_dir), min=1e-05)
    n_dot_h = torch.clamp(torch.dot(normal, half_dir), min=1e-05)
    diffuse_term = self.lambertian_diffuse()
    specular_term = self.fresnel_schlick(h_dot_v) * self.geometry(n_dot_l, n_dot_v) * self.normal_distribution(normal, half_dir) / (4 * n_dot_l * n_dot_v)
    return diffuse_term + specular_term

def evaluate_parallel(self, normal, light_dir, view_dir):
    """
        Args:
            normal: [num_samples, 3]
            light_dir: [num_samples, 3]
            view_dir: [num_samples]
        """
    normal = normal.double()
    light_dir = light_dir.double()
    view_dir = view_dir.double()
    num_samples = normal.shape[0]
    n_dot_l = torch.clamp(torch.einsum('ij,ij->i', normal, light_dir).unsqueeze(-1), min=1e-05)
    n_dot_v = torch.clamp(torch.einsum('ij,ij->i', normal, view_dir).unsqueeze(-1), min=1e-05)
    half_dir = (light_dir + view_dir) / torch.norm(light_dir + view_dir, p=2, dim=1, keepdim=True)
    h_dot_v = torch.clamp(torch.einsum('ij,ij->i', half_dir, view_dir).unsqueeze(-1), min=1e-05)
    diffuse_term = self.lambertian_diffuse().expand(num_samples, 3)
    specular_term = self.fresnel_schlick(h_dot_v) * self.geometry(n_dot_l, n_dot_v) * self.normal_distribution(normal, half_dir) / (4 * n_dot_l * n_dot_v)
    brdf = diffuse_term + specular_term
    return brdf.float()

class SkyModel(pl.LightningModule):

    def __init__(self, hypes):
        super().__init__()
        self.hypes = hypes
        downsample = hypes['dataset']['downsample']
        self.sky_H = hypes['dataset']['image_H'] // downsample // 2
        self.sky_W = hypes['dataset']['image_W'] // downsample
        self.teacher_prob = hypes['model']['teacher_prob']
        self.env_template = EnvironmentMap(self.sky_H, 'skylatlong')
        world_coord = self.env_template.worldCoordinates()
        self.pos_encoding = torch.from_numpy(np.stack([world_coord[0], world_coord[1], world_coord[2]], axis=-1))
        self.pos_encoding = self.pos_encoding.to('cuda')
        self.input_inv_gamma = hypes['model']['input_inv_gamma']
        self.input_add_pe = hypes['model']['input_add_pe']
        self.encoder_outdim = hypes['model']['ldr_encoder']['args']['layer_channels'][-1]
        self.feat_down = reduce(lambda x, y: x * y, hypes['model']['ldr_encoder']['args']['strides'])
        self.save_hyperparameters()
        self.ldr_encoder = build_module(hypes['model']['ldr_encoder'])
        self.shared_mlp = build_module(hypes['model']['shared_mlp'])
        self.latent_mlp = build_module(hypes['model']['latent_mlp'])
        self.latent_mlp_recon = build_module(hypes['model']['latent_mlp_recon'])
        self.peak_dir_mlp = build_module(hypes['model']['peak_dir_mlp'])
        self.peak_int_mlp = build_module(hypes['model']['peak_int_mlp'])
        self.ldr_decoder = nn.Sequential(build_module(hypes['model']['ldr_decoder']), nn.Sigmoid())
        self.hdr_decoder = build_module(hypes['model']['hdr_decoder'])
        self.ldr_recon_loss = build_loss(hypes['loss']['ldr_recon_loss'])
        self.hdr_recon_loss = build_loss(hypes['loss']['hdr_recon_loss'])
        self.peak_int_loss = build_loss(hypes['loss']['peak_int_loss'])
        self.peak_dir_loss = build_loss(hypes['loss']['peak_dir_loss'])
        self.fix_modules = hypes['model'].get('fix_modules', [])
        self.on_train_epoch_start()

    def encode_forward(self, x):
        """
        Encode LDR panorama to sky vector: 
            1) peak dir 
            2) peak int 
            3) latent vector
            where 1) and 2) can cat together
        
        deep vector -> shared vector -->    latent vector      --> recon deep vector 
                                     |
                                     .->  peak int/dir vector

        Should we add explicit inv gamma to the input?
        """
        if self.input_inv_gamma:
            x = srgb_inv_gamma_correction_torch(x)
        if self.input_add_pe:
            x = x + self.pos_encoding.permute(2, 0, 1)
        deep_feature = self.ldr_encoder(x)
        deep_vector = deep_feature.permute(0, 2, 3, 1).flatten(1)
        shared_vector = self.shared_mlp(deep_vector)
        peak_dir_vector = self.peak_dir_mlp(shared_vector)
        peak_int_vector = self.peak_int_mlp(shared_vector)
        latent_vector = self.latent_mlp(shared_vector)
        peak_dir_vector = peak_dir_vector / peak_dir_vector.norm(dim=1, keepdim=True)
        peak_vector = torch.cat([peak_dir_vector, peak_int_vector], dim=-1)
        return (peak_vector, latent_vector)

    def decode_forward(self, latent_vector, peak_vector, peak_vector_gt):
        use_gt_peak = False
        if self.training and np.random.rand() < self.teacher_prob:
            use_gt_peak = True
            peak_vector = peak_vector_gt
        B = peak_vector.shape[0]
        peak_dir_encoding, peak_int_encoding = self.build_peak_map(peak_vector)
        decoder_input = torch.cat([peak_dir_encoding, peak_int_encoding, self.pos_encoding.expand(B, -1, -1, -1)], dim=-1)
        decoder_input = decoder_input.permute(0, 3, 1, 2)
        recon_deep_vector = self.latent_mlp_recon(latent_vector)
        recon_deep_feature = recon_deep_vector.view(B, self.sky_H // self.feat_down, self.sky_W // self.feat_down, self.encoder_outdim).permute(0, 3, 1, 2)
        ldr_skypano_recon = self.ldr_decoder(recon_deep_feature)
        hdr_skypano_recon = self.hdr_decoder(decoder_input, recon_deep_feature)
        return (hdr_skypano_recon, ldr_skypano_recon, use_gt_peak)

    def build_peak_map(self, peak_vector):
        """
        Args:
            peak_vector: [B, 6]
                3 for peak dir, 3 for peak intensity

        Returns:
            peak encoding map: [B, 4, H, W]
                1 for peak dir using spherical gaussian lobe, 3 for peak intensity
        """
        dir_vector = peak_vector[..., :3]
        int_vector = peak_vector[..., 3:]
        dir_vector_expand = dir_vector.unsqueeze(1).unsqueeze(1).expand(-1, self.sky_H, self.sky_W, -1)
        peak_dir_encoding = torch.exp(100 * (torch.einsum('nhwc,nhwc->nhw', dir_vector_expand, self.pos_encoding.expand(dir_vector_expand.shape)) - 1)).unsqueeze(-1)
        sun_mask = torch.gt(peak_dir_encoding, 0.9).expand(-1, -1, -1, 3)
        int_vector_expand = int_vector.unsqueeze(1).unsqueeze(1).expand(-1, self.sky_H, self.sky_W, -1)
        peak_int_encoding = torch.where(sun_mask, int_vector_expand, 0)
        return (peak_dir_encoding, peak_int_encoding)

    def on_train_epoch_start(self):
        print(f'Module fixed in training: {self.fix_modules}.')
        for module in self.fix_modules:
            for p in eval(f'self.{module}').parameters():
                p.requires_grad_(False)
            eval(f'self.{module}').eval()

    def training_step(self, batch, batch_idx):
        ldr_skypano, hdr_skypano_gt, peak_vector_gt = batch
        peak_vector_pred, latent_vector = self.encode_forward(ldr_skypano)
        hdr_skypano_pred, ldr_skypano_recon, _ = self.decode_forward(latent_vector, peak_vector_pred, peak_vector_gt)
        ldr_recon_loss = self.ldr_recon_loss(ldr_skypano_recon, ldr_skypano)
        hdr_recon_loss = self.hdr_recon_loss(hdr_skypano_pred, hdr_skypano_gt)
        peak_dir_loss = self.peak_dir_loss(peak_vector_pred[..., :3], peak_vector_gt[..., :3])
        peak_int_loss = self.peak_int_loss(peak_vector_pred[..., 3:], peak_vector_gt[..., 3:])
        loss = hdr_recon_loss + peak_dir_loss + peak_int_loss + ldr_recon_loss
        self.log('train_loss', loss)
        self.log('hdr_recon_loss', hdr_recon_loss)
        self.log('ldr_recon_loss', ldr_recon_loss)
        self.log('peak_dir_loss', peak_dir_loss)
        self.log('peak_int_loss', peak_int_loss)
        log_info = f'|| loss: {loss:.3f} || hdr_recon_loss: {hdr_recon_loss:.3f}  || ldr_recon_loss: {ldr_recon_loss:.3f} || peak_dir_loss: {peak_dir_loss:.3f} ' + f'|| peak_int_loss: {peak_int_loss:.3f}'
        print(log_info)
        return loss

    def validation_step(self, batch, batch_idx):
        ldr_skypano, hdr_skypano_gt, peak_vector_gt = batch
        peak_vector_pred, latent_vector = self.encode_forward(ldr_skypano)
        hdr_skypano_pred, ldr_skypano_recon, _ = self.decode_forward(latent_vector, peak_vector_pred, peak_vector_pred)
        ldr_recon_loss = self.ldr_recon_loss(ldr_skypano_recon, ldr_skypano)
        hdr_recon_loss = self.hdr_recon_loss(hdr_skypano_pred, hdr_skypano_gt)
        loss = hdr_recon_loss
        self.log('val_loss', loss)
        return loss

    def test_step(self, batch, batch_idx):
        return self.validation_step(batch, batch_idx)

    def predict_step(self, batch, batch_idx):
        ldr_skypano, hdr_skypano_gt, peak_vector_gt = batch
        peak_vector_pred, latent_vector = self.encode_forward(ldr_skypano)
        hdr_skypano_pred, ldr_skypano_recon, _ = self.decode_forward(latent_vector, peak_vector_pred, peak_vector_pred)
        print(f'{batch_idx:0>3} \n                  HDRI Peak Intensity:\t\t {hdr_skypano_pred[0].flatten(1, 2).max(dim=-1)[0]} \n                  Peak Intensity Vector:\t {peak_vector_pred[0][3:]} \n                  Ground Truth Peak Intensity:\t {peak_vector_gt[0][3:]}')
        return_dict = {'ldr_skypano_input': ldr_skypano.permute(0, 2, 3, 1), 'ldr_skypano_pred': ldr_skypano_recon.permute(0, 2, 3, 1), 'hdr_skypano_gt': hdr_skypano_gt.permute(0, 2, 3, 1), 'hdr_skypano_pred': hdr_skypano_pred.permute(0, 2, 3, 1), 'batch_idx': batch_idx}
        return return_dict

    def configure_optimizers(self):
        optimizer = torch.optim.Adam(self.parameters(), lr=self.hypes['lr_schedule']['init_lr'])
        lr_scheduler = StepLR(optimizer=optimizer, step_size=self.hypes['lr_schedule']['decay_per_epoch'], gamma=self.hypes['lr_schedule']['decay_rate'])
        return ([optimizer], [lr_scheduler])

def encode_forward(self, x):
    """
        Encode LDR panorama to sky vector: 
            1) peak dir 
            2) peak int 
            3) latent vector
            where 1) and 2) can cat together
        
        deep vector -> shared vector -->    latent vector      --> recon deep vector 
                                     |
                                     .->  peak int/dir vector

        Should we add explicit inv gamma to the input?
        """
    if self.input_inv_gamma:
        x = srgb_inv_gamma_correction_torch(x)
    if self.input_add_pe:
        x = x + self.pos_encoding.permute(2, 0, 1)
    deep_feature = self.ldr_encoder(x)
    deep_vector = deep_feature.permute(0, 2, 3, 1).flatten(1)
    shared_vector = self.shared_mlp(deep_vector)
    peak_dir_vector = self.peak_dir_mlp(shared_vector)
    peak_int_vector = self.peak_int_mlp(shared_vector)
    latent_vector = self.latent_mlp(shared_vector)
    peak_dir_vector = peak_dir_vector / peak_dir_vector.norm(dim=1, keepdim=True)
    peak_vector = torch.cat([peak_dir_vector, peak_int_vector], dim=-1)
    return (peak_vector, latent_vector)

def decode_forward(self, latent_vector, peak_vector, peak_vector_gt):
    use_gt_peak = False
    if self.training and np.random.rand() < self.teacher_prob:
        use_gt_peak = True
        peak_vector = peak_vector_gt
    B = peak_vector.shape[0]
    peak_dir_encoding, peak_int_encoding = self.build_peak_map(peak_vector)
    decoder_input = torch.cat([peak_dir_encoding, peak_int_encoding, self.pos_encoding.expand(B, -1, -1, -1)], dim=-1)
    decoder_input = decoder_input.permute(0, 3, 1, 2)
    recon_deep_vector = self.latent_mlp_recon(latent_vector)
    recon_deep_feature = recon_deep_vector.view(B, self.sky_H // self.feat_down, self.sky_W // self.feat_down, self.encoder_outdim).permute(0, 3, 1, 2)
    ldr_skypano_recon = self.ldr_decoder(recon_deep_feature)
    hdr_skypano_recon = self.hdr_decoder(decoder_input, recon_deep_feature)
    return (hdr_skypano_recon, ldr_skypano_recon, use_gt_peak)

def build_peak_map(self, peak_vector):
    """
        Args:
            peak_vector: [B, 6]
                3 for peak dir, 3 for peak intensity

        Returns:
            peak encoding map: [B, 4, H, W]
                1 for peak dir using spherical gaussian lobe, 3 for peak intensity
        """
    dir_vector = peak_vector[..., :3]
    int_vector = peak_vector[..., 3:]
    dir_vector_expand = dir_vector.unsqueeze(1).unsqueeze(1).expand(-1, self.sky_H, self.sky_W, -1)
    peak_dir_encoding = torch.exp(100 * (torch.einsum('nhwc,nhwc->nhw', dir_vector_expand, self.pos_encoding.expand(dir_vector_expand.shape)) - 1)).unsqueeze(-1)
    sun_mask = torch.gt(peak_dir_encoding, 0.9).expand(-1, -1, -1, 3)
    int_vector_expand = int_vector.unsqueeze(1).unsqueeze(1).expand(-1, self.sky_H, self.sky_W, -1)
    peak_int_encoding = torch.where(sun_mask, int_vector_expand, 0)
    return (peak_dir_encoding, peak_int_encoding)

class SkyModelEnhanced(pl.LightningModule):

    def __init__(self, hypes):
        super().__init__()
        self.hypes = hypes
        downsample = hypes['dataset']['downsample']
        self.sky_H = hypes['dataset']['image_H'] // downsample // 2
        self.sky_W = hypes['dataset']['image_W'] // downsample
        self.teacher_prob = hypes['model']['teacher_prob']
        self.env_template = EnvironmentMap(self.sky_H, 'skylatlong')
        world_coord = self.env_template.worldCoordinates()
        self.pos_encoding = torch.from_numpy(np.stack([world_coord[0], world_coord[1], world_coord[2]], axis=-1))
        self.pos_encoding = self.pos_encoding.to('cuda')
        self.input_inv_gamma = hypes['model']['input_inv_gamma']
        self.input_add_pe = hypes['model']['input_add_pe']
        self.encoder_outdim = hypes['model']['ldr_encoder']['args']['layer_channels'][-1]
        self.feat_down = reduce(lambda x, y: x * y, hypes['model']['ldr_encoder']['args']['strides'])
        self.sum_lobe_thres = hypes['model'].get('sum_lobe_thres', 0.9)
        self.save_hyperparameters()
        self.ldr_encoder = build_module(hypes['model']['ldr_encoder'])
        self.shared_mlp = build_module(hypes['model']['shared_mlp'])
        self.latent_mlp = build_module(hypes['model']['latent_mlp'])
        self.latent_mlp_recon = build_module(hypes['model']['latent_mlp_recon'])
        self.peak_dir_mlp = build_module(hypes['model']['peak_dir_mlp'])
        self.peak_int_mlp = build_module(hypes['model']['peak_int_mlp'])
        self.ldr_decoder = nn.Sequential(build_module(hypes['model']['ldr_decoder']), nn.Sigmoid())
        self.hdr_decoder = build_module(hypes['model']['hdr_decoder'])
        self.ldr_recon_loss = build_loss(hypes['loss']['ldr_recon_loss'])
        self.hdr_recon_loss = build_loss(hypes['loss']['hdr_recon_loss'])
        self.peak_int_loss = build_loss(hypes['loss']['peak_int_loss'])
        self.peak_dir_loss = build_loss(hypes['loss']['peak_dir_loss'])
        self.fix_modules = hypes['model'].get('fix_modules', [])
        self.on_train_epoch_start()

    def encode_forward(self, x):
        """
        Encode LDR panorama to sky vector: 
            1) peak dir 
            2) peak int 
            3) latent vector
            where 1) and 2) can cat together
        
        deep vector -> shared vector -->    latent vector      --> recon deep vector 
                                     |
                                     .->  peak int/dir vector

        Should we add explicit inv gamma to the input?
        """
        if self.input_inv_gamma:
            x = srgb_inv_gamma_correction_torch(x)
        if self.input_add_pe:
            x = x + self.pos_encoding.permute(2, 0, 1)
        deep_feature = self.ldr_encoder(x)
        deep_vector = deep_feature.permute(0, 2, 3, 1).flatten(1)
        shared_vector = self.shared_mlp(deep_vector)
        peak_dir_vector = self.peak_dir_mlp(shared_vector)
        peak_int_vector = self.peak_int_mlp(shared_vector)
        latent_vector = self.latent_mlp(shared_vector)
        peak_dir_vector = peak_dir_vector / peak_dir_vector.norm(dim=1, keepdim=True)
        peak_vector = torch.cat([peak_dir_vector, peak_int_vector], dim=-1)
        return (peak_vector, latent_vector)

    def decode_forward(self, latent_vector, peak_vector, peak_vector_gt):
        use_gt_peak = False
        if self.training and np.random.rand() < self.teacher_prob:
            use_gt_peak = True
            peak_vector = peak_vector_gt
        B = peak_vector.shape[0]
        peak_dir_encoding, peak_int_encoding, sum_mask = self.build_peak_map(peak_vector)
        decoder_input = torch.cat([peak_dir_encoding, peak_int_encoding, self.pos_encoding.expand(B, -1, -1, -1)], dim=-1)
        decoder_input = decoder_input.permute(0, 3, 1, 2)
        recon_deep_vector = self.latent_mlp_recon(latent_vector)
        recon_deep_feature = recon_deep_vector.view(B, self.sky_H // self.feat_down, self.sky_W // self.feat_down, self.encoder_outdim).permute(0, 3, 1, 2)
        ldr_skypano_recon = self.ldr_decoder(recon_deep_feature)
        hdr_skypano_recon = self.hdr_decoder(decoder_input, recon_deep_feature)
        sum_mask = sum_mask.permute(0, 3, 1, 2)
        sun_peak_map = peak_dir_encoding.permute(0, 3, 1, 2) * peak_int_encoding.permute(0, 3, 1, 2)
        hdr_skypano_recon = torch.where(sum_mask, sun_peak_map, hdr_skypano_recon)
        return (hdr_skypano_recon, ldr_skypano_recon, use_gt_peak)

    def build_peak_map(self, peak_vector):
        """
        Args:
            peak_vector : [B, 6]
                3 for peak dir, 3 for peak intensity

        Returns:
            peak encoding map : [B, H, W, 4]
                1 for peak dir using spherical gaussian lobe, 3 for peak intensity

            sum_mask :[B, H, W, 3]
        """
        dir_vector = peak_vector[..., :3]
        int_vector = peak_vector[..., 3:]
        dir_vector_expand = dir_vector.unsqueeze(1).unsqueeze(1).expand(-1, self.sky_H, self.sky_W, -1)
        peak_dir_cosine = torch.einsum('nhwc,nhwc->nhw', dir_vector_expand, self.pos_encoding.expand(dir_vector_expand.shape)).unsqueeze(-1)
        peak_dir_encoding = torch.exp(100 * (peak_dir_cosine - 1))
        sun_mask = torch.gt(peak_dir_encoding, self.sum_lobe_thres).expand(-1, -1, -1, 3)
        int_vector_expand = int_vector.unsqueeze(1).unsqueeze(1).expand(-1, self.sky_H, self.sky_W, -1)
        peak_int_encoding = torch.where(sun_mask, int_vector_expand, 0)
        return (peak_dir_encoding, peak_int_encoding, sun_mask)

    def on_train_epoch_start(self):
        print(f'Module fixed in training: {self.fix_modules}.')
        for module in self.fix_modules:
            for p in eval(f'self.{module}').parameters():
                p.requires_grad_(False)
            eval(f'self.{module}').eval()

    def training_step(self, batch, batch_idx):
        ldr_skypano, hdr_skypano_gt, peak_vector_gt = batch
        peak_vector_pred, latent_vector = self.encode_forward(ldr_skypano)
        hdr_skypano_pred, ldr_skypano_recon, _ = self.decode_forward(latent_vector, peak_vector_pred, peak_vector_gt)
        ldr_recon_loss = self.ldr_recon_loss(ldr_skypano_recon, ldr_skypano)
        hdr_recon_loss = self.hdr_recon_loss(hdr_skypano_pred, hdr_skypano_gt)
        peak_dir_loss = self.peak_dir_loss(peak_vector_pred[..., :3], peak_vector_gt[..., :3])
        peak_int_loss = self.peak_int_loss(peak_vector_pred[..., 3:], peak_vector_gt[..., 3:])
        loss = hdr_recon_loss + peak_dir_loss + peak_int_loss + ldr_recon_loss
        self.log('train_loss', loss)
        self.log('hdr_recon_loss', hdr_recon_loss)
        self.log('ldr_recon_loss', ldr_recon_loss)
        self.log('peak_dir_loss', peak_dir_loss)
        self.log('peak_int_loss', peak_int_loss)
        log_info = f'|| loss: {loss:.3f} || hdr_recon_loss: {hdr_recon_loss:.3f}  || ldr_recon_loss: {ldr_recon_loss:.3f} || peak_dir_loss: {peak_dir_loss:.3f} ' + f'|| peak_int_loss: {peak_int_loss:.3f}'
        print(log_info)
        return loss

    def validation_step(self, batch, batch_idx):
        ldr_skypano, hdr_skypano_gt, peak_vector_gt = batch
        peak_vector_pred, latent_vector = self.encode_forward(ldr_skypano)
        hdr_skypano_pred, ldr_skypano_recon, _ = self.decode_forward(latent_vector, peak_vector_pred, peak_vector_pred)
        ldr_recon_loss = self.ldr_recon_loss(ldr_skypano_recon, ldr_skypano)
        hdr_recon_loss = self.hdr_recon_loss(hdr_skypano_pred, hdr_skypano_gt)
        peak_dir_loss = self.peak_dir_loss(peak_vector_pred[..., :3], peak_vector_gt[..., :3])
        peak_int_loss = self.peak_int_loss(peak_vector_pred[..., 3:], peak_vector_gt[..., 3:])
        loss = hdr_recon_loss + peak_dir_loss + peak_int_loss + ldr_recon_loss
        self.log('val_loss', loss)
        return loss

    def test_step(self, batch, batch_idx):
        return self.validation_step(batch, batch_idx)

    def predict_step(self, batch, batch_idx):
        ldr_skypano, hdr_skypano_gt, peak_vector_gt = batch
        peak_vector_pred, latent_vector = self.encode_forward(ldr_skypano)
        hdr_skypano_pred, ldr_skypano_recon, _ = self.decode_forward(latent_vector, peak_vector_pred, peak_vector_pred)
        print(f'{batch_idx:0>3} \n                  HDRI Peak Intensity:\t\t {hdr_skypano_pred[0].flatten(1, 2).max(dim=-1)[0]} \n                  Peak Intensity Vector:\t {peak_vector_pred[0][3:]} \n                  Ground Truth Peak Intensity:\t {peak_vector_gt[0][3:]}')
        return_dict = {'ldr_skypano_input': ldr_skypano.permute(0, 2, 3, 1), 'ldr_skypano_pred': ldr_skypano_recon.permute(0, 2, 3, 1), 'hdr_skypano_gt': hdr_skypano_gt.permute(0, 2, 3, 1), 'hdr_skypano_pred': hdr_skypano_pred.permute(0, 2, 3, 1), 'batch_idx': batch_idx}
        return return_dict

    def configure_optimizers(self):
        optimizer = torch.optim.Adam(self.parameters(), lr=self.hypes['lr_schedule']['init_lr'])
        lr_scheduler = StepLR(optimizer=optimizer, step_size=self.hypes['lr_schedule']['decay_per_epoch'], gamma=self.hypes['lr_schedule']['decay_rate'])
        return ([optimizer], [lr_scheduler])

def encode_forward(self, x):
    """
        Encode LDR panorama to sky vector: 
            1) peak dir 
            2) peak int 
            3) latent vector
            where 1) and 2) can cat together
        
        deep vector -> shared vector -->    latent vector      --> recon deep vector 
                                     |
                                     .->  peak int/dir vector

        Should we add explicit inv gamma to the input?
        """
    if self.input_inv_gamma:
        x = srgb_inv_gamma_correction_torch(x)
    if self.input_add_pe:
        x = x + self.pos_encoding.permute(2, 0, 1)
    deep_feature = self.ldr_encoder(x)
    deep_vector = deep_feature.permute(0, 2, 3, 1).flatten(1)
    shared_vector = self.shared_mlp(deep_vector)
    peak_dir_vector = self.peak_dir_mlp(shared_vector)
    peak_int_vector = self.peak_int_mlp(shared_vector)
    latent_vector = self.latent_mlp(shared_vector)
    peak_dir_vector = peak_dir_vector / peak_dir_vector.norm(dim=1, keepdim=True)
    peak_vector = torch.cat([peak_dir_vector, peak_int_vector], dim=-1)
    return (peak_vector, latent_vector)

def decode_forward(self, latent_vector, peak_vector, peak_vector_gt):
    use_gt_peak = False
    if self.training and np.random.rand() < self.teacher_prob:
        use_gt_peak = True
        peak_vector = peak_vector_gt
    B = peak_vector.shape[0]
    peak_dir_encoding, peak_int_encoding, sum_mask = self.build_peak_map(peak_vector)
    decoder_input = torch.cat([peak_dir_encoding, peak_int_encoding, self.pos_encoding.expand(B, -1, -1, -1)], dim=-1)
    decoder_input = decoder_input.permute(0, 3, 1, 2)
    recon_deep_vector = self.latent_mlp_recon(latent_vector)
    recon_deep_feature = recon_deep_vector.view(B, self.sky_H // self.feat_down, self.sky_W // self.feat_down, self.encoder_outdim).permute(0, 3, 1, 2)
    ldr_skypano_recon = self.ldr_decoder(recon_deep_feature)
    hdr_skypano_recon = self.hdr_decoder(decoder_input, recon_deep_feature)
    sum_mask = sum_mask.permute(0, 3, 1, 2)
    sun_peak_map = peak_dir_encoding.permute(0, 3, 1, 2) * peak_int_encoding.permute(0, 3, 1, 2)
    hdr_skypano_recon = torch.where(sum_mask, sun_peak_map, hdr_skypano_recon)
    return (hdr_skypano_recon, ldr_skypano_recon, use_gt_peak)

def build_peak_map(self, peak_vector):
    """
        Args:
            peak_vector : [B, 6]
                3 for peak dir, 3 for peak intensity

        Returns:
            peak encoding map : [B, H, W, 4]
                1 for peak dir using spherical gaussian lobe, 3 for peak intensity

            sum_mask :[B, H, W, 3]
        """
    dir_vector = peak_vector[..., :3]
    int_vector = peak_vector[..., 3:]
    dir_vector_expand = dir_vector.unsqueeze(1).unsqueeze(1).expand(-1, self.sky_H, self.sky_W, -1)
    peak_dir_cosine = torch.einsum('nhwc,nhwc->nhw', dir_vector_expand, self.pos_encoding.expand(dir_vector_expand.shape)).unsqueeze(-1)
    peak_dir_encoding = torch.exp(100 * (peak_dir_cosine - 1))
    sun_mask = torch.gt(peak_dir_encoding, self.sum_lobe_thres).expand(-1, -1, -1, 3)
    int_vector_expand = int_vector.unsqueeze(1).unsqueeze(1).expand(-1, self.sky_H, self.sky_W, -1)
    peak_int_encoding = torch.where(sun_mask, int_vector_expand, 0)
    return (peak_dir_encoding, peak_int_encoding, sun_mask)

class ScaledDotProductAttention(nn.Module):
    """
    Scaled Dot-Product Attention proposed in "Attention Is All You Need"
    Compute the dot products of the query with all keys, divide each by sqrt(dim),
    and apply a softmax function to obtain the weights on the values
    Args: dim, mask
        dim (int): dimention of attention
    Inputs: query, key, value, mask
        - **query** (batch, q_len, d_model): tensor containing projection
          vector for decoder.
        - **key** (batch, k_len, d_model): tensor containing projection
          vector for encoder.
        - **value** (batch, v_len, d_model): tensor containing features of the
          encoded input sequence.
    Returns: context, attn
        - **context**: tensor containing the context vector from
          attention mechanism.
        - **attn**: tensor containing the attention (alignment) from the
          encoder outputs.
    """

    def __init__(self, dim):
        super(ScaledDotProductAttention, self).__init__()
        self.sqrt_dim = np.sqrt(dim)

    def forward(self, query, key, value):
        score = torch.bmm(query, key.transpose(1, 2)) / self.sqrt_dim
        attn = F.softmax(score, -1)
        context = torch.bmm(attn, value)
        return context

def forward(self, query, key, value):
    score = torch.bmm(query, key.transpose(1, 2)) / self.sqrt_dim
    attn = F.softmax(score, -1)
    context = torch.bmm(attn, value)
    return context

class NaiveSingleView(nn.Module):

    def __init__(self, args):
        super().__init__()
        self.args = args
        view_args = args['view_setting']
        self.view_num = view_args['view_num']
        self.view_dis_deg = view_args['view_dis']
        self.view_dis_rad = [np.radians(x) for x in view_args['view_dis']]
        self.center_view = view_args['view_dis'].index(0)
        self.img_encoder = build_module(args['img_encoder'])
        self.shared_mlp = build_module(args['shared_mlp'])
        self.latent_mlp = build_module(args['latent_mlp'])
        self.peak_dir_mlp = build_module(args['peak_dir_mlp'])
        self.peak_int_mlp = build_module(args['peak_int_mlp'])

    def forward(self, x):
        """
        x: B, N_view, C, H, W
        """
        x = x[:, self.center_view, ...]
        x = self.img_encoder(x).permute(0, 2, 3, 1)
        x_flatten = x.flatten(1)
        deep_vector = self.shared_mlp(x_flatten)
        latent_vector = self.latent_mlp(deep_vector)
        peak_dir_vector = self.peak_dir_mlp(deep_vector)
        peak_int_vector = self.peak_int_mlp(deep_vector)
        peak_dir_vector = peak_dir_vector / peak_dir_vector.norm(dim=1, keepdim=True)
        peak_vector = torch.cat([peak_dir_vector, peak_int_vector], dim=-1)
        return (peak_vector, latent_vector)

def forward(self, x):
    """
        x: B, N_view, C, H, W
        """
    x = x[:, self.center_view, ...]
    x = self.img_encoder(x).permute(0, 2, 3, 1)
    x_flatten = x.flatten(1)
    deep_vector = self.shared_mlp(x_flatten)
    latent_vector = self.latent_mlp(deep_vector)
    peak_dir_vector = self.peak_dir_mlp(deep_vector)
    peak_int_vector = self.peak_int_mlp(deep_vector)
    peak_dir_vector = peak_dir_vector / peak_dir_vector.norm(dim=1, keepdim=True)
    peak_vector = torch.cat([peak_dir_vector, peak_int_vector], dim=-1)
    return (peak_vector, latent_vector)

class CatMultiView(nn.Module):

    def __init__(self, args):
        super().__init__()
        self.args = args
        view_args = args['view_setting']
        self.view_num = view_args['view_num']
        self.view_dis_deg = view_args['view_dis']
        self.sort_index = np.argsort(self.view_dis_deg)
        self.view_dis_rad = [np.radians(x) for x in view_args['view_dis']]
        self.center_view = view_args['view_dis'].index(0)
        self.img_encoder = build_module(args['img_encoder'])
        self.shared_mlp = build_module(args['shared_mlp'])
        self.latent_mlp = build_module(args['latent_mlp'])
        self.peak_dir_mlp = build_module(args['peak_dir_mlp'])
        self.peak_int_mlp = build_module(args['peak_int_mlp'])

    def forward(self, x):
        """
        x: B, N_view, C, H, W, suppose center view is the first 
        """
        B, N_view, C, H, W = x.shape
        x = x[:, self.sort_index, ...]
        x = x.permute(0, 2, 3, 1, 4).flatten(3)
        x = self.img_encoder(x).permute(0, 2, 3, 1)
        x_flatten = x.flatten(1)
        deep_vector = self.shared_mlp(x_flatten)
        latent_vector = self.latent_mlp(deep_vector)
        peak_dir_vector = self.peak_dir_mlp(deep_vector)
        peak_int_vector = self.peak_int_mlp(deep_vector)
        peak_dir_vector = peak_dir_vector / peak_dir_vector.norm(dim=1, keepdim=True)
        peak_vector = torch.cat([peak_dir_vector, peak_int_vector], dim=-1)
        return (peak_vector, latent_vector)

def forward(self, x):
    """
        x: B, N_view, C, H, W, suppose center view is the first 
        """
    B, N_view, C, H, W = x.shape
    x = x[:, self.sort_index, ...]
    x = x.permute(0, 2, 3, 1, 4).flatten(3)
    x = self.img_encoder(x).permute(0, 2, 3, 1)
    x_flatten = x.flatten(1)
    deep_vector = self.shared_mlp(x_flatten)
    latent_vector = self.latent_mlp(deep_vector)
    peak_dir_vector = self.peak_dir_mlp(deep_vector)
    peak_int_vector = self.peak_int_mlp(deep_vector)
    peak_dir_vector = peak_dir_vector / peak_dir_vector.norm(dim=1, keepdim=True)
    peak_vector = torch.cat([peak_dir_vector, peak_int_vector], dim=-1)
    return (peak_vector, latent_vector)

class AvgMultiView(nn.Module):
    """
    Avg is not suitable.

    use self.attention to fuse latent vector
    use max to fuse peak intensity
    use avg to fuse peak direction
    """

    def __init__(self, args):
        super().__init__()
        self.args = args
        view_args = args['view_setting']
        self.view_num = view_args['view_num']
        self.view_dis_deg = view_args['view_dis']
        self.view_dis_rad = [np.radians(x) for x in view_args['view_dis']]
        self.center_view = view_args['view_dis'].index(0)
        self.crop_H = view_args['camera_H'] // view_args['downsample_for_crop']
        self.crop_W = view_args['camera_W'] // view_args['downsample_for_crop']
        self.camera_vfov = np.degrees(np.arctan2(view_args['camera_H'] / 2, view_args['focal'])) * 2
        self.aspect_ratio = view_args['camera_W'] / view_args['camera_H']
        self.img_encoder = build_module(args['img_encoder'])
        self.shared_mlp = build_module(args['shared_mlp'])
        self.latent_mlp = build_module(args['latent_mlp'])
        int_channel = args['latent_mlp']['args']['layer_channels'][-1]
        self.att = ScaledDotProductAttention(int_channel)
        self.peak_dir_mlp = build_module(args['peak_dir_mlp'])
        self.peak_int_mlp = build_module(args['peak_int_mlp'])

    def forward(self, x):
        """
        x: B, N_view, C, H, W
        """
        B, N_view, _, _, _ = x.shape
        x = x.flatten(0, 1)
        x = self.img_encoder(x).permute(0, 2, 3, 1)
        x_flatten = x.flatten(1)
        deep_vector = self.shared_mlp(x_flatten)
        deep_vector = deep_vector.view(B, N_view, -1)
        latent_vector = self.latent_mlp(deep_vector)
        latent_vector = self.att(latent_vector[:, self.center_view:self.center_view + 1], latent_vector, latent_vector)
        peak_dir_vector = self.peak_dir_mlp(deep_vector)
        for i in range(self.view_num):
            azimuth_rad_i = self.view_dis_rad[i]
            rotation_mat_i = rotation_matrix(azimuth=azimuth_rad_i, elevation=0)
            inv_rotation_mat_i = rotation_matrix(azimuth=-azimuth_rad_i, elevation=0)
            inv_rotation_mat_i = torch.from_numpy(inv_rotation_mat_i).to(x.device).float()
            peak_dir_vector[:, i] = (inv_rotation_mat_i @ peak_dir_vector[:, i].T).T
        peak_dir_vector = peak_dir_vector / peak_dir_vector.norm(dim=-1, keepdim=True)
        peak_dir_vector_sum = peak_dir_vector.mean(dim=1)
        peak_dir_vector_avg = peak_dir_vector_sum / peak_dir_vector_sum.norm(dim=-1, keepdim=True)
        peak_int_vector = self.peak_int_mlp(deep_vector).mean(dim=1)
        peak_vector = torch.cat([peak_dir_vector_avg, peak_int_vector], dim=-1)
        return (peak_vector, latent_vector)

def forward(self, x):
    """
        x: B, N_view, C, H, W
        """
    B, N_view, _, _, _ = x.shape
    x = x.flatten(0, 1)
    x = self.img_encoder(x).permute(0, 2, 3, 1)
    x_flatten = x.flatten(1)
    deep_vector = self.shared_mlp(x_flatten)
    deep_vector = deep_vector.view(B, N_view, -1)
    latent_vector = self.latent_mlp(deep_vector)
    latent_vector = self.att(latent_vector[:, self.center_view:self.center_view + 1], latent_vector, latent_vector)
    peak_dir_vector = self.peak_dir_mlp(deep_vector)
    for i in range(self.view_num):
        azimuth_rad_i = self.view_dis_rad[i]
        rotation_mat_i = rotation_matrix(azimuth=azimuth_rad_i, elevation=0)
        inv_rotation_mat_i = rotation_matrix(azimuth=-azimuth_rad_i, elevation=0)
        inv_rotation_mat_i = torch.from_numpy(inv_rotation_mat_i).to(x.device).float()
        peak_dir_vector[:, i] = (inv_rotation_mat_i @ peak_dir_vector[:, i].T).T
    peak_dir_vector = peak_dir_vector / peak_dir_vector.norm(dim=-1, keepdim=True)
    peak_dir_vector_sum = peak_dir_vector.mean(dim=1)
    peak_dir_vector_avg = peak_dir_vector_sum / peak_dir_vector_sum.norm(dim=-1, keepdim=True)
    peak_int_vector = self.peak_int_mlp(deep_vector).mean(dim=1)
    peak_vector = torch.cat([peak_dir_vector_avg, peak_int_vector], dim=-1)
    return (peak_vector, latent_vector)

class AngleClassificationLoss(nn.Module):

    def __init__(self, args):
        super().__init__()
        self.weight = args['weight']
        self.num_bins = args['num_bins']
        self.cross_entropy = nn.CrossEntropyLoss()

    def forward(self, pred, target):
        """
        pred : torch.tensor
            unnormalized logits, shape [B, num_bins]
        target : torch.tensor
            shape [B, ], ground-truth angle in [0, 2pi]
        """
        bin_indices = (target / (2 * np.pi / self.num_bins)).floor().long()
        loss = self.cross_entropy(pred, bin_indices) * self.weight
        return loss

def forward(self, pred, target):
    """
        pred : torch.tensor
            unnormalized logits, shape [B, num_bins]
        target : torch.tensor
            shape [B, ], ground-truth angle in [0, 2pi]
        """
    bin_indices = (target / (2 * np.pi / self.num_bins)).floor().long()
    loss = self.cross_entropy(pred, bin_indices) * self.weight
    return loss

def is_projection_overlap(proj1, proj2):
    return max(proj1[0], proj2[0]) <= min(proj1[1], proj2[1])

def is_rectangles_overlap(rect1, rect2):
    for i in range(4):
        edge = rect1[i] - rect1[(i + 1) % 4]
        axis = np.array([-edge[1], edge[0]])
        axis /= np.linalg.norm(axis)
        proj1 = project_polygon_onto_axis(Polygon(rect1), axis)
        proj2 = project_polygon_onto_axis(Polygon(rect2), axis)
        if not is_projection_overlap(proj1, proj2):
            return False
    for i in range(4):
        edge = rect2[i] - rect2[(i + 1) % 4]
        axis = np.array([-edge[1], edge[0]])
        axis /= np.linalg.norm(axis)
        proj1 = project_polygon_onto_axis(Polygon(rect1), axis)
        proj2 = project_polygon_onto_axis(Polygon(rect2), axis)
        if not is_projection_overlap(proj1, proj2):
            return False
    return True

def calculate_car_corners(trajectory, car_length=4.5, car_width=2):
    T = trajectory.shape[0]
    corners_trajectory = np.zeros((T, 4, 2))
    for i in range(1, T):
        direction = trajectory[i] - trajectory[i - 1]
        if np.linalg.norm(direction) != 0:
            direction /= np.linalg.norm(direction)
        else:
            direction = np.array([1, 0])
        perpendicular = np.array([-direction[1], direction[0]])
        front = 0.5 * car_length * direction
        back = -0.5 * car_length * direction
        left = 0.5 * car_width * perpendicular
        right = -0.5 * car_width * perpendicular
        corners_trajectory[i, 0] = trajectory[i] + front + left
        corners_trajectory[i, 1] = trajectory[i] + front + right
        corners_trajectory[i, 2] = trajectory[i] + back + right
        corners_trajectory[i, 3] = trajectory[i] + back + left
    corners_trajectory[0] = corners_trajectory[1]
    return corners_trajectory

def project_polygon_onto_axis(polygon, axis):
    min_projection = float('inf')
    max_projection = float('-inf')
    for point in polygon.exterior.coords:
        projection = (point[0] * axis[0] + point[1] * axis[1]) / np.linalg.norm(axis)
        min_projection = min(min_projection, projection)
        max_projection = max(max_projection, projection)
    return (min_projection, max_projection)

def calculate_translation_vector(rect1, rect2, direction):
    axes = []
    for rect in [rect1, rect2]:
        for i in range(len(rect.exterior.coords) - 1):
            edge = np.subtract(rect.exterior.coords[i + 1], rect.exterior.coords[i])
            normal = [-edge[1], edge[0]]
            axes.append(normal / np.linalg.norm(normal))
    min_translation_vector = None
    min_translation_distance = float('inf')
    for axis in axes:
        min_proj_rect1, max_proj_rect1 = project_polygon_onto_axis(rect1, axis)
        min_proj_rect2, max_proj_rect2 = project_polygon_onto_axis(rect2, axis)
        if max_proj_rect1 < min_proj_rect2 or max_proj_rect2 < min_proj_rect1:
            return [0, 0]
        overlap = min(max_proj_rect1, max_proj_rect2) - max(min_proj_rect1, min_proj_rect2)
        translation_axis = np.multiply(axis, overlap)
        if np.dot(translation_axis, direction) < 0:
            translation_axis = np.multiply(translation_axis, -1)
        translation_distance = np.linalg.norm(translation_axis)
        if translation_distance < min_translation_distance:
            min_translation_distance = translation_distance
            min_translation_vector = translation_axis
    return min_translation_vector

def check_collision_and_revise_static(curr_trajectory, objects):
    N, T = (objects.shape[0], curr_trajectory.shape[0])
    if N == 0:
        return curr_trajectory
    car_length = 5
    car_width = 2.2
    safe_distance = 7
    obj_corners_trajectory = objects[:, None, :, :].repeat(T, axis=1)
    curr_corner_trajectory = calculate_car_corners(curr_trajectory, car_length, car_width)
    for j in range(N):
        for t in range(T):
            if is_rectangles_overlap(curr_corner_trajectory[t], obj_corners_trajectory[j, t]):
                direction = curr_trajectory[t] - curr_trajectory[t - 1]
                direction /= np.linalg.norm(direction)
                perpendicular = np.array([-direction[1], direction[0]])
                delta = calculate_translation_vector(Polygon(curr_corner_trajectory[t]), Polygon(obj_corners_trajectory[j, t]), perpendicular)
                curr_trajectory[t] += delta
    return curr_trajectory

def judge_priority(traj1, traj2):
    T = traj1.shape[0]
    traj2_new = traj2[0:1].repeat(T, axis=0)
    for t in range(T):
        if is_rectangles_overlap(traj1[t], traj2_new[t]):
            return 1
    return 2

def check_collision_and_revise_dynamic(input_trajectory):

    def judge_priority(traj1, traj2):
        T = traj1.shape[0]
        traj2_new = traj2[0:1].repeat(T, axis=0)
        for t in range(T):
            if is_rectangles_overlap(traj1[t], traj2_new[t]):
                return 1
        return 2

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

    def add_wait_timesteps(traj, t, wait_timesteps):
        traj_out = traj.copy()
        T = traj_out.shape[0]
        if t + wait_timesteps > T:
            traj_out = interpolate_uniformly(traj[:t], T)
        else:
            traj_out[:t + wait_timesteps] = interpolate_uniformly(traj[:t], t + wait_timesteps)
            traj_out[t + wait_timesteps:] = traj[t:-wait_timesteps]
        return traj_out
    valid_traj = []
    valid_record = []
    for item in input_trajectory:
        if item[0] is not None:
            valid_record.append(1)
            valid_traj.append(item)
        else:
            valid_record.append(0)
    curr_trajectory = np.array(valid_traj)
    car_length = 5
    car_width = 2.2
    safe_distance = 8
    N, T = (curr_trajectory.shape[0], curr_trajectory.shape[1])
    all_corners_trajectory = np.zeros((N, T, 4, 2))
    for n in range(N):
        all_corners_trajectory[n] = calculate_car_corners(curr_trajectory[n], car_length, car_width)
    revised_trajectory = curr_trajectory.copy()
    for i in range(N):
        for j in range(i + 1, N):
            for t in range(1, T):
                if is_rectangles_overlap(all_corners_trajectory[i, t], all_corners_trajectory[j, t]):
                    modify_idx = judge_priority(all_corners_trajectory[i], all_corners_trajectory[j])
                    collision_point = (curr_trajectory[i, t] + curr_trajectory[j, t]) / 2
                    if modify_idx == 1:
                        collision_speed = np.linalg.norm(curr_trajectory[j, t] - curr_trajectory[j, t - 1])
                        wait_timesteps = int(np.ceil(safe_distance / (collision_speed + 0.0001)))
                        curr_trajectory[i] = add_wait_timesteps(curr_trajectory[i], t, wait_timesteps)
                    if modify_idx == 2:
                        collision_speed = np.linalg.norm(curr_trajectory[i, t] - curr_trajectory[i, t - 1])
                        wait_timesteps = int(np.ceil(safe_distance / (collision_speed + 0.0001)))
                        curr_trajectory[j] = add_wait_timesteps(curr_trajectory[j], t, wait_timesteps)
                    break
    output = []
    num = 0
    for i in range(len(valid_record)):
        if valid_record[i] == 1:
            output.append(curr_trajectory[num])
            num += 1
        else:
            output.append(input_trajectory[i])
    return output

def hermite_spline(P0, P1, T0, T1, num_points=100):
    t = np.linspace(0, 1, num_points)
    h00 = 2 * t ** 3 - 3 * t ** 2 + 1
    h10 = t ** 3 - 2 * t ** 2 + t
    h01 = -2 * t ** 3 + 3 * t ** 2
    h11 = t ** 3 - t ** 2
    spline_points = h00[:, None] * P0 + h10[:, None] * T0 + h01[:, None] * P1 + h11[:, None] * T1
    return spline_points

def project_polygon_onto_axis(vertices, axis):
    min_val = max_val = np.dot(vertices[0], axis)
    for vertex in vertices[1:]:
        projection = np.dot(vertex, axis)
        min_val = min(min_val, projection)
        max_val = max(max_val, projection)
    return (min_val, max_val)

def is_projection_overlap(proj1, proj2):
    return max(proj1[0], proj2[0]) <= min(proj1[1], proj2[1])

def is_rectangles_overlap(rect1, rect2):
    for i in range(4):
        edge = rect1[i] - rect1[(i + 1) % 4]
        axis = np.array([-edge[1], edge[0]])
        axis /= np.linalg.norm(axis)
        proj1 = project_polygon_onto_axis(rect1, axis)
        proj2 = project_polygon_onto_axis(rect2, axis)
        if not is_projection_overlap(proj1, proj2):
            return False
    for i in range(4):
        edge = rect2[i] - rect2[(i + 1) % 4]
        axis = np.array([-edge[1], edge[0]])
        axis /= np.linalg.norm(axis)
        proj1 = project_polygon_onto_axis(rect1, axis)
        proj2 = project_polygon_onto_axis(rect2, axis)
        if not is_projection_overlap(proj1, proj2):
            return False
    return True

def calculate_car_corners(trajectory, car_length=4.5, car_width=2):
    T = trajectory.shape[0]
    corners_trajectory = np.zeros((T, 4, 2))
    for i in range(1, T):
        direction = trajectory[i] - trajectory[i - 1]
        direction /= np.linalg.norm(direction)
        perpendicular = np.array([-direction[1], direction[0]])
        front = 0.5 * car_length * direction
        back = -0.5 * car_length * direction
        left = 0.5 * car_width * perpendicular
        right = -0.5 * car_width * perpendicular
        corners_trajectory[i, 0] = trajectory[i] + front + left
        corners_trajectory[i, 1] = trajectory[i] + front + right
        corners_trajectory[i, 2] = trajectory[i] + back + right
        corners_trajectory[i, 3] = trajectory[i] + back + left
    corners_trajectory[0] = corners_trajectory[1]
    return corners_trajectory

def check_collision_and_revise_waste(all_trajectory):
    all_trajectory = np.array(all_trajectory)
    N, T = (all_trajectory.shape[0], all_trajectory.shape[1])
    car_length = 4.5
    car_width = 2.0
    safe_distance = 7
    all_corners_trajectory = np.zeros((N, T, 4, 2))
    for n in range(N):
        all_corners_trajectory[n] = calculate_car_corners(all_trajectory[n], car_length, car_width)
    for j in range(1, N):
        for t in range(T):
            if is_rectangles_overlap(all_corners_trajectory[0, t], all_corners_trajectory[j, t]):
                trajectory1 = all_trajectory[0]
                trajectory2 = all_trajectory[j]
                speed1 = np.linalg.norm(np.diff(trajectory1, axis=0))
                speed2 = np.linalg.norm(np.diff(trajectory2, axis=0))
                if is_tailgating(trajectory1, trajectory2) and speed1[t - 1] < speed2[t - 1]:
                    all_trajectory[0] = accerlate(all_trajectory[0], calculate_speed_increase(trajectory1, trajectory2))
                    break
                else:
                    collision_point = trajectory1[t]
                    for t_safe in range(t + 1, T):
                        if np.linalg.norm(trajectory2[t_safe] - collision_point) > safe_distance:
                            break
                    if t == T - 1:
                        all_trajectory[0] = deaccerlate_to_zero(all_trajectory[0])
                    else:
                        all_trajectory[0] = deaccerlate(all_trajectory[0], t / t_safe)
    return all_trajectory

def check_collision_and_revise(all_trajectory):
    all_trajectory = np.array(all_trajectory)
    N, T = (all_trajectory.shape[0], all_trajectory.shape[1])
    car_length = 4.5
    car_width = 2.0
    safe_distance = 7
    all_corners_trajectory = np.zeros((N, T, 4, 2))
    for n in range(N):
        all_corners_trajectory[n] = calculate_car_corners(all_trajectory[n], car_length, car_width)
    for j in range(1, N):
        for t in range(T):
            if is_rectangles_overlap(all_corners_trajectory[0, t], all_corners_trajectory[j, t]):
                trajectory1 = all_trajectory[0]
                trajectory2 = all_trajectory[j]
                speed1 = np.linalg.norm(np.diff(trajectory1, axis=0))
                speed2 = np.linalg.norm(np.diff(trajectory2, axis=0))
                if is_tailgating(trajectory1, trajectory2) and speed1[t - 1] < speed2[t - 1]:
                    return 'accerlate'
                else:
                    return 'deaccerlate'
    return 'no revise'

def get_distance_from_point_to_line(point, line_point1, line_point2):
    vec1 = line_point1 - point
    vec2 = line_point2 - point
    distance = np.abs(np.cross(vec1, vec2)) / np.linalg.norm(line_point1 - line_point2)
    return distance

