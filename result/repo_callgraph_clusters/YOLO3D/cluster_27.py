# Cluster 27

class Albumentations:

    def __init__(self):
        self.transform = None
        try:
            import albumentations as A
            check_version(A.__version__, '1.0.3', hard=True)
            self.transform = A.Compose([A.Blur(p=0.01), A.MedianBlur(p=0.01), A.ToGray(p=0.01), A.CLAHE(p=0.01), A.RandomBrightnessContrast(p=0.0), A.RandomGamma(p=0.0), A.ImageCompression(quality_lower=75, p=0.0)], bbox_params=A.BboxParams(format='yolo', label_fields=['class_labels']))
            LOGGER.info(colorstr('albumentations: ') + ', '.join((f'{x}' for x in self.transform.transforms if x.p)))
        except ImportError:
            pass
        except Exception as e:
            LOGGER.info(colorstr('albumentations: ') + f'{e}')

    def __call__(self, im, labels, p=1.0):
        if self.transform and random.random() < p:
            new = self.transform(image=im, bboxes=labels[:, 1:], class_labels=labels[:, 0])
            im, labels = (new['image'], np.array([[c, *b] for c, b in zip(new['class_labels'], new['bboxes'])]))
        return (im, labels)

def __init__(self):
    self.transform = None
    try:
        import albumentations as A
        check_version(A.__version__, '1.0.3', hard=True)
        self.transform = A.Compose([A.Blur(p=0.01), A.MedianBlur(p=0.01), A.ToGray(p=0.01), A.CLAHE(p=0.01), A.RandomBrightnessContrast(p=0.0), A.RandomGamma(p=0.0), A.ImageCompression(quality_lower=75, p=0.0)], bbox_params=A.BboxParams(format='yolo', label_fields=['class_labels']))
        LOGGER.info(colorstr('albumentations: ') + ', '.join((f'{x}' for x in self.transform.transforms if x.p)))
    except ImportError:
        pass
    except Exception as e:
        LOGGER.info(colorstr('albumentations: ') + f'{e}')

def check_python(minimum='3.6.2'):
    check_version(platform.python_version(), minimum, name='Python ', hard=True)

class DetectedObject:
    """
    Processing image for NN input
    """

    def __init__(self, img, detection_class, box_2d, proj_matrix, label=None):
        if isinstance(proj_matrix, str):
            proj_matrix = get_P(proj_matrix)
        self.proj_matrix = proj_matrix
        self.theta_ray = self.calc_theta_ray(img, box_2d, proj_matrix)
        self.img = self.format_img(img, box_2d)
        self.label = label
        self.detection_class = detection_class

    def calc_theta_ray(self, img, box_2d, proj_matrix):
        """
        Calculate global angle of object, see paper
        """
        width = img.shape[1]
        fovx = 2 * np.arctan(width / (2 * proj_matrix[0][0]))
        center = (box_2d[1][0] + box_2d[0][0]) / 2
        dx = center - width / 2
        mult = 1
        if dx < 0:
            mult = -1
        dx = abs(dx)
        angle = np.arctan(2 * dx * np.tan(fovx / 2) / width)
        angle = angle * mult
        return angle

    def format_img(self, img, box_2d):
        normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        process = transforms.Compose([transforms.ToTensor(), normalize])
        pt1, pt2 = (box_2d[0], box_2d[1])
        crop = img[pt1[1]:pt2[1] + 1, pt1[0]:pt2[0] + 1]
        crop = cv2.resize(crop, (224, 224), interpolation=cv2.INTER_CUBIC)
        batch = process(crop)
        return batch

def format_img(self, img, box_2d):
    normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    process = transforms.Compose([transforms.ToTensor(), normalize])
    pt1, pt2 = (box_2d[0], box_2d[1])
    crop = img[pt1[1]:pt2[1] + 1, pt1[0]:pt2[0] + 1]
    crop = cv2.resize(crop, (224, 224), interpolation=cv2.INTER_CUBIC)
    batch = process(crop)
    return batch

class DetectedObject:
    """
    Processing image for NN input
    """

    def __init__(self, img, detection_class, box_2d, proj_matrix, label=None):
        if isinstance(proj_matrix, str):
            proj_matrix = get_P(proj_matrix)
        self.proj_matrix = proj_matrix
        self.theta_ray = self.calc_theta_ray(img, box_2d, proj_matrix)
        self.img = self.format_img(img, box_2d)
        self.label = label
        self.detection_class = detection_class

    def calc_theta_ray(self, img, box_2d, proj_matrix):
        """
        Calculate global angle of object, see paper
        """
        width = img.shape[1]
        fovx = 2 * np.arctan(width / (2 * proj_matrix[0][0]))
        center = (box_2d[1][0] + box_2d[0][0]) / 2
        dx = center - width / 2
        mult = 1
        if dx < 0:
            mult = -1
        dx = abs(dx)
        angle = np.arctan(2 * dx * np.tan(fovx / 2) / width)
        angle = angle * mult
        return angle

    def format_img(self, img, box_2d):
        normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        process = transforms.Compose([transforms.ToTensor(), normalize])
        pt1, pt2 = (box_2d[0], box_2d[1])
        crop = img[pt1[1]:pt2[1] + 1, pt1[0]:pt2[0] + 1]
        crop = cv2.resize(crop, (224, 224), interpolation=cv2.INTER_CUBIC)
        batch = process(crop)
        return batch

def format_img(self, img, box_2d):
    normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    process = transforms.Compose([transforms.ToTensor(), normalize])
    pt1, pt2 = (box_2d[0], box_2d[1])
    crop = img[pt1[1]:pt2[1] + 1, pt1[0]:pt2[0] + 1]
    crop = cv2.resize(crop, (224, 224), interpolation=cv2.INTER_CUBIC)
    batch = process(crop)
    return batch

