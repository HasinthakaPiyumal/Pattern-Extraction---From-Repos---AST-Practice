# Cluster 20

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

@property
def K_inv(self):
    return self.get_inverse_camera_matrix()

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

@property
def K_inv(self):
    return self.get_inverse_camera_matrix()

