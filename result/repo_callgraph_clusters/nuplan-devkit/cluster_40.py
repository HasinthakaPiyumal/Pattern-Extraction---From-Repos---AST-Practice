# Cluster 40

class Image:
    """
    A class to represent an image. This class is an analogue to LidarPointCloud. It is a class for manipulating and
    transforming an image. Any transformation functions (flip, scale, translate) should be added to this class in the
    future.
    """

    def __init__(self, image: PilImage.Image) -> None:
        """
        Constructor for the Image class.
        :param image: An image of type PIL.Image.Image.
        """
        self._image = image

    @property
    def as_pil(self) -> PilImage.Image:
        """
        Returns the image of type PIL.Image.Image in uint8, RGB format.
        :return: An image of type PIL.Image.Image.
        """
        return self._image

    @cached_property
    def as_numpy(self) -> npt.NDArray[np.uint8]:
        """
        Returns the image as a numpy array in uint8, RGB format.
        :return: An image as a numpy array.
        """
        return self.as_numpy_nocache()

    def as_numpy_nocache(self) -> npt.NDArray[np.uint8]:
        """
        Returns the image as a numpy array in uint8, RGB format. A non caching variation to save on memory if needed.
        :return: An image as a numpy array.
        """
        return np.array(self._image, dtype=np.uint8)

    @cached_property
    def as_cv2(self) -> npt.NDArray[np.uint8]:
        """
        Returns the image as a CV2 image in uint8, BGR format. It is a numpy array under the hood.
        This function is a convenience for to be used with cv2.imshow().
        :return: An image as a CV2 image.
        """
        return self.as_cv2_nocache()

    def as_cv2_nocache(self) -> npt.NDArray[np.uint8]:
        """
        Returns the image as a CV2 image in uint8, BGR format. It is a numpy array under the hood. This function
        is a convenience for to be used with cv2.imshow(). A non caching variation to save on memory if needed.
        :return: An image as a CV2 image.
        """
        return cast(npt.NDArray[np.uint8], cv2.cvtColor(np.array(self._image, dtype=np.uint8), cv2.COLOR_RGB2BGR))

    @classmethod
    def from_buffer(cls, blob: BinaryIO) -> Image:
        """
        Instantiates Image from buffer.
        :param blob: Data to load.
        :return: An Image object.
        """
        return cls(PilImage.open(blob))

@cached_property
def as_numpy(self) -> npt.NDArray[np.uint8]:
    """
        Returns the image as a numpy array in uint8, RGB format.
        :return: An image as a numpy array.
        """
    return self.as_numpy_nocache()

@cached_property
def as_cv2(self) -> npt.NDArray[np.uint8]:
    """
        Returns the image as a CV2 image in uint8, BGR format. It is a numpy array under the hood.
        This function is a convenience for to be used with cv2.imshow().
        :return: An image as a CV2 image.
        """
    return self.as_cv2_nocache()

class TestImage(unittest.TestCase):
    """Test suite for the Image class using synthetic image."""

    def setUp(self) -> None:
        """Inherited, see superclass"""
        pil_img: PilImg.Image = PilImg.new('RGB', (500, 500))
        self.image = Image(pil_img)

    def _test_numpy_type(self, img: Any) -> None:
        """
        Checks if the given object is a numpy array with dtype uint8.
        :param img: The image object to test. Type hint any because the test should be valid for all objects.
        """
        self.assertEqual(np.ndarray, type(img))
        self.assertEqual(np.uint8, img.dtype)
        self.assertNotEqual(np.float64, img.dtype)

    def test_as_pil(self) -> None:
        """Test the function as_pil."""
        img = self.image.as_pil
        self.assertEqual(PilImg.Image, type(img))

    def test_as_numpy_nocache(self) -> None:
        """Test the function as_numpy_nocache."""
        img = self.image.as_numpy_nocache()
        self._test_numpy_type(img)

    def test_as_numpy(self) -> None:
        """Test the function as_numpy_nocache."""
        img = self.image.as_numpy
        self._test_numpy_type(img)

    def test_as_cv2_nocache(self) -> None:
        """Test the function as_cv2_nocache."""
        img = self.image.as_cv2_nocache()
        self._test_numpy_type(img)

    def test_as_cv2(self) -> None:
        """Test the function as_numpy_nocache."""
        img = self.image.as_cv2
        self._test_numpy_type(img)

def test_as_numpy_nocache(self) -> None:
    """Test the function as_numpy_nocache."""
    img = self.image.as_numpy_nocache()
    self._test_numpy_type(img)

def test_as_numpy(self) -> None:
    """Test the function as_numpy_nocache."""
    img = self.image.as_numpy
    self._test_numpy_type(img)

def test_as_cv2_nocache(self) -> None:
    """Test the function as_cv2_nocache."""
    img = self.image.as_cv2_nocache()
    self._test_numpy_type(img)

def test_as_cv2(self) -> None:
    """Test the function as_numpy_nocache."""
    img = self.image.as_cv2
    self._test_numpy_type(img)

