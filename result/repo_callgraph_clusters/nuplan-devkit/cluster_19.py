# Cluster 19

class TestNuPlanCli(unittest.TestCase):
    """
    Test nuplan cli with typer engine
    """

    def _get_ensure_file_downloaded_patch(self, expected_data_root: str, expected_remote_path: str) -> Callable[[str, str], str]:
        """
        Get the patch for ensure_file_downloaded.
        """

        def fxn(actual_data_root: str, actual_remote_path: str) -> str:
            """
            The patch for ensure_file_downloaded.
            """
            self.assertEqual(expected_data_root, actual_data_root)
            self.assertEqual(expected_remote_path, actual_remote_path)
            return actual_remote_path
        return fxn

    def test_db_info_info(self) -> None:
        """
        Test nuplan_cli.py db info command.
        """

        def _patch_get_db_description(log_name: str) -> DbDescription:
            """
            A patch for the get_db_description db function.
            """
            self.assertEqual('expected_log_name', log_name)
            return DbDescription(tables={'first_table': TableDescription(name='first_table', row_count=123, columns={'first_token': ColumnDescription(column_id=0, name='first_token', data_type='blob', nullable=False, is_primary_key=True), 'first_something': ColumnDescription(column_id=1, name='first_something', data_type='varchar(64)', nullable=True, is_primary_key=False)}), 'second_table': TableDescription(name='second_table', row_count=456, columns={'second_token': ColumnDescription(column_id=0, name='token', data_type='blob', nullable=False, is_primary_key=True), 'second_something': ColumnDescription(column_id=1, name='somthing', data_type='varchar(128)', nullable=True, is_primary_key=False)})})
        ensure_file_downloaded_patch = self._get_ensure_file_downloaded_patch('/data/sets/nuplan', 'expected_log_name')
        with mock.patch('nuplan.cli.db_cli.get_db_description', _patch_get_db_description), mock.patch('nuplan.cli.db_cli._ensure_file_downloaded', ensure_file_downloaded_patch):
            result = runner.invoke(cli, ['db', 'info', 'expected_log_name'])
            self.assertEqual(0, result.exit_code)
            strings_of_interest = ['table first_table: 123 rows', 'table second_table: 456 rows', 'column first_token: blob not null primary key', 'column first_something: varchar(64) null', 'column second_token: blob not null primary key', 'column second_something: varchar(128) null']
            result_stdout = result.stdout.lower()
            for string_of_interest in strings_of_interest:
                self.assertTrue(string_of_interest in result_stdout)

    def test_db_cli_duration(self) -> None:
        """
        Test nuplan_cli.py db duration command.
        """

        def _patch_db_duration(log_name: str) -> int:
            """
            A patch for the get_db_duration function.
            """
            self.assertEqual('expected_log_name', log_name)
            return int(125 * 1000000.0)
        ensure_file_downloaded_patch = self._get_ensure_file_downloaded_patch('/data/sets/nuplan', 'expected_log_name')
        with mock.patch('nuplan.cli.db_cli.get_db_duration_in_us', _patch_db_duration), mock.patch('nuplan.cli.db_cli._ensure_file_downloaded', ensure_file_downloaded_patch):
            result = runner.invoke(cli, ['db', 'duration', 'expected_log_name'])
            self.assertEqual(0, result.exit_code)
            self.assertTrue('00:02:05' in result.stdout)

    def test_db_cli_log_duration(self) -> None:
        """
        Test nuplan_cli.py db log-duration command.
        """

        def _patch_db_log_duration(log_name: str) -> Generator[Tuple[str, int], None, None]:
            """
            Patch for get_db_log_duration function.
            """
            self.assertEqual('expected_log_name', log_name)
            for i in range(0, 3, 1):
                yield (f'log_file_{i}', int((i + 1) * 67 * 1000000.0))
        ensure_file_downloaded_patch = self._get_ensure_file_downloaded_patch('/data/sets/nuplan', 'expected_log_name')
        with mock.patch('nuplan.cli.db_cli.get_db_log_duration', _patch_db_log_duration), mock.patch('nuplan.cli.db_cli._ensure_file_downloaded', ensure_file_downloaded_patch):
            result = runner.invoke(cli, ['db', 'log-duration', 'expected_log_name'])
            self.assertEqual(0, result.exit_code)
            strings_of_interest = ['log_file_0 is 00:01:07', 'log_file_1 is 00:02:14', 'log_file_2 is 00:03:21', '3 total logs']
            for string_of_interest in strings_of_interest:
                self.assertTrue(string_of_interest in result.stdout)

    def test_db_cli_log_vehicle(self) -> None:
        """
        Test nuplan_cli.py log-vehicle command.
        """

        def _patch_db_log_vehicles(log_name: str) -> Generator[Tuple[str, str], None, None]:
            """
            Patch for get_db_log_vehicles function.
            """
            self.assertEqual('expected_log_name', log_name)
            for i in range(0, 3, 1):
                yield (f'log_file_{i}', f'vehicle_{i}')
        ensure_file_downloaded_patch = self._get_ensure_file_downloaded_patch('/data/sets/nuplan', 'expected_log_name')
        with mock.patch('nuplan.cli.db_cli.get_db_log_vehicles', _patch_db_log_vehicles), mock.patch('nuplan.cli.db_cli._ensure_file_downloaded', ensure_file_downloaded_patch):
            result = runner.invoke(cli, ['db', 'log-vehicle', 'expected_log_name'])
            self.assertEqual(0, result.exit_code)
            for i in range(0, 3, 1):
                self.assertTrue(f'log_file_{i}, vehicle vehicle_{i}' in result.stdout)

    def test_db_cli_scenarios(self) -> None:
        """
        Test db_cli scenarios command.
        """

        def _patch_db_scenario_info(log_name: str) -> Generator[Tuple[str, int], None, None]:
            """
            Patch for get_db_scenario_info
            """
            self.assertEqual('expected_log_name', log_name)
            for i in range(0, 3, 1):
                yield (f'scenario_{i}', i + 5)
        ensure_file_downloaded_patch = self._get_ensure_file_downloaded_patch('/data/sets/nuplan', 'expected_log_name')
        with mock.patch('nuplan.cli.db_cli.get_db_scenario_info', _patch_db_scenario_info), mock.patch('nuplan.cli.db_cli._ensure_file_downloaded', ensure_file_downloaded_patch):
            result = runner.invoke(cli, ['db', 'scenarios', 'expected_log_name'])
            self.assertEqual(0, result.exit_code)
            strings_of_interest = ['scenario_0: 5', 'scenario_1: 6', 'scenario_2: 7', 'TOTAL: 18']
            for string_of_interest in strings_of_interest:
                self.assertTrue(string_of_interest in result.stdout)

def _patch_get_db_description(log_name: str) -> DbDescription:
    """
            A patch for the get_db_description db function.
            """
    self.assertEqual('expected_log_name', log_name)
    return DbDescription(tables={'first_table': TableDescription(name='first_table', row_count=123, columns={'first_token': ColumnDescription(column_id=0, name='first_token', data_type='blob', nullable=False, is_primary_key=True), 'first_something': ColumnDescription(column_id=1, name='first_something', data_type='varchar(64)', nullable=True, is_primary_key=False)}), 'second_table': TableDescription(name='second_table', row_count=456, columns={'second_token': ColumnDescription(column_id=0, name='token', data_type='blob', nullable=False, is_primary_key=True), 'second_something': ColumnDescription(column_id=1, name='somthing', data_type='varchar(128)', nullable=True, is_primary_key=False)})})

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

@classmethod
def from_buffer(cls, blob: BinaryIO) -> Image:
    """
        Instantiates Image from buffer.
        :param blob: Data to load.
        :return: An Image object.
        """
    return cls(PilImage.open(blob))

class LidarPointCloud:
    """Simple data class representing a point cloud."""

    def __init__(self, points: npt.NDArray[np.float32]) -> None:
        """
        Class for manipulating and viewing point clouds.
        :param points: <np.float: f, n>. Input point cloud matrix with f features per point and n points.
        """
        if points.ndim == 1:
            points = np.atleast_2d(points).T
        self.points = points

    @staticmethod
    def load_pcd_bin(pcd_bin: Union[str, IO[Any], ByteString], pcd_bin_version: int=1) -> npt.NDArray[np.float32]:
        """
        Loads from pcd binary format:
            version 1: a numpy array with 5 cols (x, y, z, intensity, ring).
            version 2: a numpy array with 6 cols (x, y, z, intensity, ring, lidar_id).
        :param pcd_bin: File path or a file-like object or raw bytes.
        :param pcd_bin_version: 1 or 2, see above.
        :return: <np.float: 6, n>. Point cloud matrix[(x, y, z, intensity, ring, lidar_id)].
        """
        if isinstance(pcd_bin, str):
            scan = np.fromfile(pcd_bin, dtype=np.float32)
        else:
            if not isinstance(pcd_bin, bytes):
                pcd_bin = pcd_bin.read()
            scan = np.frombuffer(pcd_bin, dtype=np.float32)
            scan = np.copy(scan)
        if pcd_bin_version == 1:
            points = scan.reshape((-1, 5))
            points = np.hstack((points, -1 * np.ones((points.shape[0], 1), dtype=np.float32)))
        elif pcd_bin_version == 2:
            points = scan.reshape((-1, 6))
        else:
            pytest.fail('Unknown pcd bin file version: %d' % pcd_bin_version)
        return points.T

    @staticmethod
    def load_pcd(pcd_data: Union[IO[Any], ByteString]) -> npt.NDArray[np.float32]:
        """
        Loads a pcd file.
        :param pcd_data: File path or a file-like object or raw bytes.
        :return: <np.float: 6, n>. Point cloud matrix[(x, y, z, intensity, ring, lidar_id)].
        """
        if not isinstance(pcd_data, bytes):
            pcd_data = pcd_data.read()
        return PointCloud.parse(pcd_data).to_pcd_bin2()

    @classmethod
    def from_file(cls, file_name: str) -> LidarPointCloud:
        """
        Instantiates from a .pcl, .pcd, .npy, or .bin file.
        :param file_name: Path of the pointcloud file on disk.
        :return: A LidarPointCloud object.
        """
        if file_name.endswith('.bin'):
            points = cls.load_pcd_bin(file_name, 1)
        elif file_name.endswith('.bin2'):
            points = cls.load_pcd_bin(file_name, 2)
        elif file_name.endswith('.pcl') or file_name.endswith('.pcd'):
            points = pcd_to_numpy(file_name).T
        elif file_name.endswith('.npy'):
            points = np.load(file_name)
        else:
            raise ValueError('Unsupported filetype {}'.format(file_name))
        return cls(points)

    @classmethod
    def from_buffer(cls, pcd_data: Union[IO[Any], ByteString], content_type: str='bin') -> LidarPointCloud:
        """
        Instantiates from buffer.
        :param pcd_data: File path or a file-like object or raw bytes.
        :param content_type: Type of the point cloud content, such as 'bin', 'bin2', 'pcd'.
        :return: A LidarPointCloud object.
        """
        if content_type == 'bin':
            return cls(cls.load_pcd_bin(pcd_data, 1))
        elif content_type == 'bin2':
            return cls(cls.load_pcd_bin(pcd_data, 2))
        elif content_type == 'pcd':
            return cls(cls.load_pcd(pcd_data))
        else:
            raise NotImplementedError('Not implemented content type: %s' % content_type)

    @classmethod
    def make_random(cls) -> LidarPointCloud:
        """
        Instantiates a random point cloud.
        :return: LidarPointCloud instance.
        """
        return LidarPointCloud(points=np.random.normal(0, 100, size=(4, 100)))

    def __eq__(self, other: object) -> bool:
        """
        Checks if two LidarPointCloud are equal.
        :param other: Other object.
        :return: True if both objects are equal otherwise False.
        """
        if not isinstance(other, LidarPointCloud):
            return NotImplemented
        return np.allclose(self.points, other.points, atol=1e-06)

    def copy(self) -> LidarPointCloud:
        """
        Creates a copy of self.
        :return: LidarPointCloud instance.
        """
        return LidarPointCloud(points=self.points.copy())

    def nbr_points(self) -> int:
        """
        Returns the number of points.
        :return: Number of points.
        """
        return int(self.points.shape[1])

    def subsample(self, ratio: float) -> None:
        """
        Sub-samples the pointcloud.
        :param ratio: Fraction to keep.
        """
        assert 0 < ratio < 1
        selected_ind = np.random.choice(np.arange(0, self.nbr_points()), size=int(self.nbr_points() * ratio))
        self.points = self.points[:, selected_ind]

    def remove_close(self, min_dist: float) -> None:
        """
        Removes points too close within a certain distance from origin from bird view (so dist = sqrt(x^2+y^2)).
        :param min_dist: The distance threshold.
        """
        dist_from_orig = np.linalg.norm(self.points[:2, :], axis=0)
        self.points = self.points[:, dist_from_orig >= min_dist]

    def radius_filter(self, radius: float) -> None:
        """
        Removes points outside the given radius.
        :param radius: Radius in meters.
        """
        keep = np.sqrt(self.points[0] ** 2 + self.points[1] ** 2) <= radius
        self.points = self.points[:, keep]

    def range_filter(self, xrange: Tuple[float, float]=(-np.inf, np.inf), yrange: Tuple[float, float]=(-np.inf, np.inf), zrange: Tuple[float, float]=(-np.inf, np.inf)) -> None:
        """
        Restricts points to specified ranges.
        :param xrange: (xmin, xmax).
        :param yrange: (ymin, ymax).
        :param zrange: (zmin, zmax).
        """
        keep_x = np.logical_and(xrange[0] <= self.points[0], self.points[0] <= xrange[1])
        keep_y = np.logical_and(yrange[0] <= self.points[1], self.points[1] <= yrange[1])
        keep_z = np.logical_and(zrange[0] <= self.points[2], self.points[2] <= zrange[1])
        keep = np.logical_and(keep_x, np.logical_and(keep_y, keep_z))
        self.points = self.points[:, keep]

    def translate(self, x: npt.NDArray[np.float64]) -> None:
        """
        Applies a translation to the point cloud.
        :param x: <np.float: 3,>. Translation in x, y, z.
        """
        self.points[:3] += x.reshape((-1, 1))

    def rotate(self, quaternion: Quaternion) -> None:
        """
        Applies a rotation.
        :param quaternion: Rotation to apply.
        """
        self.points[:3] = np.dot(quaternion.rotation_matrix.astype(np.float32), self.points[:3])

    def transform(self, transf_matrix: npt.NDArray[np.float64]) -> None:
        """
        Applies a homogeneous transform.
        :param transf_matrix: <np.float: 4, 4>. Homogeneous transformation matrix.
        """
        transf_matrix = transf_matrix.astype(np.float32)
        self.points[:3, :] = transf_matrix[:3, :3] @ self.points[:3] + transf_matrix[:3, 3].reshape((-1, 1))

    def scale(self, scale: Tuple[float, float, float]) -> None:
        """
        Scales the lidar xyz coordinates.
        :param scale: The scaling parameter.
        """
        scale_arr = np.array(scale)
        scale_arr.shape = (3, 1)
        self.points[:3, :] *= np.tile(scale_arr, (1, self.nbr_points()))

    def render_image(self, canvas_size: Tuple[int, int]=(1001, 1001), view: npt.NDArray[np.float64]=np.array([[10, 0, 0, 500], [0, 10, 0, 500], [0, 0, 10, 0]]), color_dim: int=2) -> Image.Image:
        """
        Renders pointcloud to an array with 3 channels appropriate for viewing as an image. The image is color coded
        according the color_dim dimension of points (typically the height).
        :param canvas_size: (width, height). Size of the canvas on which to render the image.
        :param view: <np.float: n, n>. Defines an arbitrary projection (n <= 4).
        :param color_dim: The dimension of the points to be visualized as color. Default is 2 for height.
        :return: A Image instance.
        """
        heights = self.points[2, :]
        points = view_points(self.points[:3, :], view, normalize=False)
        points[2, :] = heights
        mask = np.ones(points.shape[1], dtype=bool)
        mask = np.logical_and(mask, points[0, :] < canvas_size[0] - 1)
        mask = np.logical_and(mask, points[0, :] > 0)
        mask = np.logical_and(mask, points[1, :] < canvas_size[1] - 1)
        mask = np.logical_and(mask, points[1, :] > 0)
        points = points[:, mask]
        color_values = points[color_dim, :]
        color_values = 255.0 * (color_values - np.amin(color_values)) / (np.amax(color_values) - np.amin(color_values))
        points = np.int16(np.round(points[:2, :]))
        color_values = np.int16(np.round(color_values))
        cmap = [cm.jet(i / 255, bytes=True)[:3] for i in range(256)]
        render = np.tile(np.expand_dims(np.zeros(canvas_size, dtype=np.uint8), axis=2), [1, 1, 3])
        color_value_array: npt.NDArray[np.float64] = -1 * np.ones(canvas_size, dtype=float)
        for (col, row), color_value in zip(points.T, color_values.T):
            if color_value > color_value_array[row, col]:
                color_value_array[row, col] = color_value
                render[row, col] = cmap[color_value]
        return Image.fromarray(render)

    def render_height(self, ax: axes.Axes, view: npt.NDArray[np.float64]=np.eye(4), x_lim: Tuple[float, float]=(-20, 20), y_lim: Tuple[float, float]=(-20, 20), marker_size: float=1) -> None:
        """
        Very simple method that applies a transformation and then scatter plots the points colored by height (z-value).
        :param ax: Axes on which to render the points.
        :param view: <np.float: n, n>. Defines an arbitrary projection (n <= 4).
        :param x_lim: (min, max).
        :param y_lim: (min, max).
        :param marker_size: Marker size.
        """
        self._render_helper(self.points[2, :], ax, view, x_lim, y_lim, marker_size)

    def render_intensity(self, ax: axes.Axes, view: npt.NDArray[np.float64]=np.eye(4), x_lim: Tuple[float, float]=(-20, 20), y_lim: Tuple[float, float]=(-20, 20), marker_size: float=1) -> None:
        """
        Very simple method that applies a transformation and then scatter plots the points colored by intensity.
        :param ax: Axes on which to render the points.
        :param view: <np.float: n, n>. Defines an arbitrary projection (n <= 4).
        :param x_lim: (min, max).
        :param y_lim: (min, max).
        :param marker_size: Marker size.
        """
        self._render_helper(self.points[3, :], ax, view, x_lim, y_lim, marker_size)

    def render_label(self, ax: axes.Axes, id2color: Optional[Dict[int, Tuple[float, float, float, float]]]=None, view: npt.NDArray[np.float64]=np.eye(4), x_lim: Tuple[float, float]=(-20, 20), y_lim: Tuple[float, float]=(-20, 20), marker_size: float=1.0) -> None:
        """
        Very simple method that applies a transformation and then scatter plots the points. Each points is colored based
        on labels through the label color mapping, If no mapping provided, we use the rainbow function to assign
        the colors.
        :param id2color: {label_id : (R, G, B, A)}. Id to color mapping where RGBA is within [0, 255].
        :param ax: Axes on which to render the points.
        :param view: <np.float: n, n>. Defines an arbitrary projection (n <= 4).
        :param x_lim: (min, max).
        :param y_lim: (min, max).
        :param marker_size: Marker size.
        """
        label = self.points[-1]
        colors: Dict[int, Tuple[Any, ...]] = {}
        if id2color is None:
            unique_label = np.unique(label)
            color_rainbow = rainbow(len(unique_label), normalized=True)
            for label_id, c in zip(unique_label, color_rainbow):
                colors[label_id] = c
        else:
            for key, color in id2color.items():
                colors[key] = np.array(color) / 255.0
        color_list = list(map(lambda x: colors.get(x, np.array((1.0, 1.0, 1.0, 0.0))), label))
        self._render_helper(color_list, ax, view, x_lim, y_lim, marker_size)

    def _render_helper(self, colors: Union[npt.NDArray[np.float64], List[npt.NDArray[np.float64]]], ax: axes.Axes, view: npt.NDArray[np.float64], x_lim: Tuple[float, float], y_lim: Tuple[float, float], marker_size: float) -> None:
        """
        Helper function for rendering.
        :param colors: Array-like or list of colors or color input for scatter function.
        :param ax: Axes on which to render the points.
        :param view: <np.float: n, n>. Defines an arbitrary projection (n <= 4).
        :param x_lim: (min, max).
        :param y_lim: (min, max).
        :param marker_size: Marker size.
        """
        points = view_points(self.points[:3, :], view, normalize=False)
        ax.scatter(points[0, :], points[1, :], c=colors, s=marker_size)
        ax.set_xlim(x_lim)
        ax.set_ylim(y_lim)

@classmethod
def from_buffer(cls, pcd_data: Union[IO[Any], ByteString], content_type: str='bin') -> LidarPointCloud:
    """
        Instantiates from buffer.
        :param pcd_data: File path or a file-like object or raw bytes.
        :param content_type: Type of the point cloud content, such as 'bin', 'bin2', 'pcd'.
        :return: A LidarPointCloud object.
        """
    if content_type == 'bin':
        return cls(cls.load_pcd_bin(pcd_data, 1))
    elif content_type == 'bin2':
        return cls(cls.load_pcd_bin(pcd_data, 2))
    elif content_type == 'pcd':
        return cls(cls.load_pcd(pcd_data))
    else:
        raise NotImplementedError('Not implemented content type: %s' % content_type)

class PointCloud:
    """
    Class for raw .pcd file.
    """

    def __init__(self, header: PointCloudHeader, points: npt.NDArray[np.float64]) -> None:
        """
        PointCloud.
        :param header: Pointcloud header.
        :param points: <np.ndarray, X, N>. X columns, N points.
        """
        self._header = header
        self._points = points

    @property
    def header(self) -> PointCloudHeader:
        """
        Returns pointcloud header.
        :return: A PointCloudHeader instance.
        """
        return self._header

    @property
    def points(self) -> npt.NDArray[np.float64]:
        """
        Returns points.
        :return: <np.ndarray, X, N>. X columns, N points.
        """
        return self._points

    def save(self, file_path: str) -> None:
        """
        Saves to .pcd file.
        :param file_path: The path to the .pcd file.
        """
        with open(file_path, 'wb') as fp:
            fp.write('# .PCD v{} - Point Cloud Data file format\n'.format(self._header.version).encode('utf8'))
            for field in self._header._fields:
                value = getattr(self._header, field)
                if isinstance(value, list):
                    text = ' '.join(map(str, value))
                else:
                    text = str(value)
                fp.write('{} {}\n'.format(field.upper(), text).encode('utf8'))
            fp.write(self._points.tobytes())

    @classmethod
    def parse(cls, pcd_content: bytes) -> PointCloud:
        """
        Parses the pointcloud from byte stream.
        :param pcd_content: The byte stream that holds the pcd content.
        :return: A PointCloud object.
        """
        with BytesIO(pcd_content) as stream:
            header = cls.parse_header(stream)
            points = cls.parse_points(stream, header)
            return cls(header, points)

    @classmethod
    def parse_from_file(cls, pcd_file: str) -> PointCloud:
        """
        Parses the pointcloud from .pcd file on disk.
        :param pcd_file: The path to the .pcd file.
        :return: A PointCloud instance.
        """
        with open(pcd_file, 'rb') as stream:
            header = cls.parse_header(stream)
            points = cls.parse_points(stream, header)
            return cls(header, points)

    @staticmethod
    def parse_header(stream: IO[Any]) -> PointCloudHeader:
        """
        Parses the header of a pointcloud from byte IO stream.
        :param stream: Binary stream.
        :return: A PointCloudHeader instance.
        """
        headers_list = []
        while True:
            line = stream.readline().decode('utf8').strip()
            if line.startswith('#'):
                continue
            columns = line.split()
            key = columns[0].lower()
            val = columns[1:] if len(columns) > 2 else columns[1]
            headers_list.append((key, val))
            if key == 'data':
                break
        headers = dict(headers_list)
        headers['size'] = list(map(int, headers['size']))
        headers['count'] = list(map(int, headers['count']))
        headers['width'] = int(headers['width'])
        headers['height'] = int(headers['height'])
        headers['viewpoint'] = list(map(int, headers['viewpoint']))
        headers['points'] = int(headers['points'])
        header = PointCloudHeader(**headers)
        if any([c != 1 for c in header.count]):
            raise RuntimeError('"count" has to be 1')
        if not len(header.fields) == len(header.size) == len(header.type) == len(header.count):
            raise RuntimeError('fields/size/type/count field number are inconsistent')
        return header

    @staticmethod
    def parse_points(stream: IO[Any], header: PointCloudHeader) -> npt.NDArray[np.float64]:
        """
        Parses points from byte IO stream.
        :param stream: Byte stream that holds the points.
        :param header: <np.ndarray, X, N>. A numpy array that has X columns(features), N points.
        :return: Points of Point Cloud.
        """
        if header.data != 'binary':
            raise RuntimeError('Un-supported data foramt: {}. "binary" is expected.'.format(header.data))
        row_type = PointCloud.np_type(header)
        length = row_type.itemsize * header.points
        buff = stream.read(length)
        if len(buff) != length:
            raise RuntimeError('Incomplete pointcloud stream: {} bytes expected, {} got'.format(length, len(buff)))
        points = np.frombuffer(buff, row_type)
        return points

    @staticmethod
    def np_type(header: PointCloudHeader) -> np.dtype:
        """
        Helper function that translate column types in pointcloud to np types.
        :param header: A PointCloudHeader object.
        :return: np.dtype that holds the X features.
        """
        type_mapping = {'I': 'int', 'U': 'uint', 'F': 'float'}
        np_types = [type_mapping[t] + str(int(s) * 8) for t, s in zip(header.type, header.size)]
        return np.dtype([(f, getattr(np, nt)) for f, nt in zip(header.fields, np_types)])

    def to_pcd_bin(self) -> npt.NDArray[np.float32]:
        """
        Converts pointcloud to .pcd.bin format.
        :return: <np.float32, 5, N>, the point cloud in .pcd.bin format.
        """
        lidar_fields = ['x', 'y', 'z', 'intensity', 'ring']
        return np.array([np.array(self.points[f], dtype=np.float32) for f in lidar_fields])

    def to_pcd_bin2(self) -> npt.NDArray[np.float32]:
        """
        Converts pointcloud to .pcd.bin2 format.
        :return: <np.float32, 6, N>, the point cloud in .pcd.bin2 format.
        """
        lidar_fields = ['x', 'y', 'z', 'intensity', 'ring', 'lidar_info']
        return np.array([np.array(self.points[f], dtype=np.float32) for f in lidar_fields])

@classmethod
def parse(cls, pcd_content: bytes) -> PointCloud:
    """
        Parses the pointcloud from byte stream.
        :param pcd_content: The byte stream that holds the pcd content.
        :return: A PointCloud object.
        """
    with BytesIO(pcd_content) as stream:
        header = cls.parse_header(stream)
        points = cls.parse_points(stream, header)
        return cls(header, points)

@classmethod
def parse_from_file(cls, pcd_file: str) -> PointCloud:
    """
        Parses the pointcloud from .pcd file on disk.
        :param pcd_file: The path to the .pcd file.
        :return: A PointCloud instance.
        """
    with open(pcd_file, 'rb') as stream:
        header = cls.parse_header(stream)
        points = cls.parse_points(stream, header)
        return cls(header, points)

class UUID(TypeDecorator):
    """
    Use BLOB(16) for sqlite.(bigint for mysql and uuid for postgresql)
    """
    impl = BLOB
    cache_ok = True

    def load_dialect_impl(self, dialect: Dialect) -> TypeEngine:
        """Inherited, see superclass."""
        return dialect.type_descriptor(BLOB(16))

    def process_bind_param(self, value: Optional[str], dialect: Dialect) -> Optional[bytes]:
        """Inherited, see superclass."""
        if not value:
            return None
        return uuid.UUID(value).bytes

    def process_result_value(self, value: Optional[bytes], dialect: Dialect) -> Optional[str]:
        """Inherited, see superclass."""
        if not value:
            return None
        return value.hex()

def process_result_value(self, value: Optional[bytes], dialect: Dialect) -> Optional[str]:
    """Inherited, see superclass."""
    if not value:
        return None
    return value.hex()

class HexLen8(TypeDecorator):
    """
    Use BLOB(16) for sqlite.
    """
    impl = BLOB
    cache_ok = True

    def load_dialect_impl(self, dialect: Any) -> Any:
        """Inherited, see superclass."""
        return dialect.type_descriptor(BLOB(8))

    def process_bind_param(self, value: Any, dialect: Any) -> Optional[bytes]:
        """Inherited, see superclass."""
        if not value:
            return None
        return bytearray.fromhex(value)

    def process_result_value(self, value: Any, dialect: Any) -> Optional[str]:
        """Inherited, see superclass."""
        if not value:
            return None
        return value.hex()

def process_bind_param(self, value: Any, dialect: Any) -> Optional[bytes]:
    """Inherited, see superclass."""
    if not value:
        return None
    return bytearray.fromhex(value)

def process_result_value(self, value: Any, dialect: Any) -> Optional[str]:
    """Inherited, see superclass."""
    if not value:
        return None
    return value.hex()

class HttpStore(BlobStore):
    """
    Http blob store. Load blobs from http file server.
    """

    def __init__(self, root_url: str) -> None:
        """
        Initialize HttpStore.
        :param root_url: Root URL containing data.
        """
        assert root_url.startswith('http://') or root_url.startswith('https://'), 'invalid url %s' % root_url
        self._root_url = root_url
        if not self._root_url.endswith('/'):
            self._root_url += '/'
        self._session = requests.Session()

    def _get(self, url: str) -> BinaryIO:
        """
        Get content from URL.
        :param url: URL containing the data.
        :return: Blob binary stream.
        """
        t0 = time.time()
        response = self._session.get(url)
        logger.debug('Done fetching {} in {} seconds.'.format(url, time.time() - t0))
        if response.status_code == 200:
            return io.BytesIO(response.content)
        else:
            logger.error('Can not load file from URL: {}'.format(url))
            raise RuntimeError('Can not load the file: %s from server, error: %d, msg: %s.' % (url, response.status_code, response.text))

    def get(self, key: str, check_for_compressed: bool=False) -> BinaryIO:
        """
        Get content from URL.
        :param key: File name.
        :param check_for_compressed: Flag that check for a "<key>+.gzip" file and extracts the <key> file.
        :return: Blob binary stream.
        """
        gzip_path = self._root_url + key + '.gzip'
        if check_for_compressed and self.exists(gzip_path):
            gzip_stream = self._get(gzip_path)
            content: BinaryIO = self._extract_gzip_content(gzip_stream)
        else:
            content = self._get(key)
        return content

    async def get_async(self, key: str) -> BinaryIO:
        """Inherited, see superclass."""
        raise NotImplementedError('Not today.')

    def exists(self, key: str) -> bool:
        """
        Tell if the blob exists.
        :param key: blob path or token.
        :return: True if the blob exists else False.
        """
        url = self._root_url + key
        response = self._session.head(url)
        return response.status_code == 200

    def put(self, key: str, value: BinaryIO) -> None:
        """Inherited, see superclass."""
        raise NotImplementedError("'Put' operation not supported for legacy HttpStore class")

    def save_to_disk(self, key: str, check_for_compressed: bool=False) -> None:
        """Inherited, see superclass."""
        super().save_to_disk(key, check_for_compressed=check_for_compressed)

def put(self, key: str, value: BinaryIO) -> None:
    """Inherited, see superclass."""
    raise NotImplementedError("'Put' operation not supported for legacy HttpStore class")

@dataclass(frozen=True)
class Camera(SensorDataTableRow):
    """
    A class representing a row in the Image table.
    Each field corresponds to a column in the row.
    """
    token: Optional[str]
    log_token: Optional[str]
    channel: Optional[str]
    model: Optional[str]
    translation: Optional[str]
    rotation: Optional[str]
    intrinsic: Optional[int]
    distortion: Optional[int]
    width: Optional[int]
    height: Optional[int]

    @classmethod
    def from_db_row(cls, row: sqlite3.Row) -> Camera:
        """
        A convenience method to convert a row from the Camera table into a row.
        :param row: A sqlite row.
        :return: A SensorDataTableRow Image.
        """
        keys: Set[str] = set(row.keys())
        return cls(token=row['token'].hex() if 'token' in keys else None, log_token=row['log_token'].hex() if 'log_token' in keys else None, channel=row['channel'] if 'channel' in keys else None, model=row['model'] if 'model' in keys else None, translation=row['translation'] if 'translation' in keys else None, rotation=row['rotation'] if 'rotation' in keys else None, intrinsic=row['intrinsic'] if 'intrinsic' in keys else None, distortion=row['distortion'] if 'distortion' in keys else None, width=row['width'] if 'width' in keys else None, height=row['height'] if 'height' in keys else None)

@classmethod
def from_db_row(cls, row: sqlite3.Row) -> Camera:
    """
        A convenience method to convert a row from the Camera table into a row.
        :param row: A sqlite row.
        :return: A SensorDataTableRow Image.
        """
    keys: Set[str] = set(row.keys())
    return cls(token=row['token'].hex() if 'token' in keys else None, log_token=row['log_token'].hex() if 'log_token' in keys else None, channel=row['channel'] if 'channel' in keys else None, model=row['model'] if 'model' in keys else None, translation=row['translation'] if 'translation' in keys else None, rotation=row['rotation'] if 'rotation' in keys else None, intrinsic=row['intrinsic'] if 'intrinsic' in keys else None, distortion=row['distortion'] if 'distortion' in keys else None, width=row['width'] if 'width' in keys else None, height=row['height'] if 'height' in keys else None)

def _get_table_columns_from_db(log_file: str, table_name: str) -> Generator[ColumnDescription, None, None]:
    """
    Get information about the columns that are present in the table.
    If the table does not exist, returns an empty generator.
    :param log_file: The log file to query.
    :param table_name: The table name to query.
    :return: A generator containing information about the columns in the table, ordered by column_id ascending.
    """
    query = f'\n    PRAGMA table_info({table_name});\n    '
    for row in execute_many(query, (), log_file):
        yield ColumnDescription(column_id=row['cid'], name=row['name'], data_type=row['type'], nullable=not row['notnull'], is_primary_key=row['pk'])

def _get_table_row_count_from_db(log_file: str, table_name: str) -> int:
    """
    Get the number of rows in a table.
    Raises an error if the table does not exist.
    :param log_file: The log file to query.
    :param table_name: The table name to examine.
    :return: The number of rows in the table.
    """
    query = f'\n    SELECT COUNT(*) AS cnt\n    FROM {table_name};\n    '
    result = execute_one(query, (), log_file)
    if result is None:
        raise ValueError(f'Table {table_name} does not exist.')
    return int(result['cnt'])

def _get_table_description(log_file: str, table_name: str) -> TableDescription:
    """
    Get a description of the table.
    :param log_file: The log file to query.
    :param table_name: The table name to examine.
    :return: A struct filled with information about the table.
    """
    return TableDescription(name=table_name, columns={tc.name: tc for tc in _get_table_columns_from_db(log_file, table_name)}, row_count=_get_table_row_count_from_db(log_file, table_name))

def _get_table_names_from_db(log_file: str) -> Generator[str, None, None]:
    """
    Get the names of tables in the DB.
    :param log_file: The log file to examine.
    :return: A generator containing the table names.
    """
    query = "\n    SELECT tbl_name\n    FROM sqlite_schema\n    WHERE type='table'\n    ORDER BY tbl_name ASC;\n    "
    for row in execute_many(query, (), log_file):
        yield row['tbl_name']

def get_db_description(log_file: str) -> DbDescription:
    """
    Get information about all tables that are present in the DB.
    :param log_file: The log file to describe.
    :return: A description of the tables present in the DB.
    """
    tables: Dict[str, TableDescription] = {}
    for table_name in _get_table_names_from_db(log_file):
        tables[table_name] = _get_table_description(log_file, table_name)
    return DbDescription(tables=tables)

def get_db_duration_in_us(log_file: str) -> int:
    """
    Get the duration of the database log in us, measured as (last_lidar_pc_timestamp) - (first_lidarpc_timestamp)
    :param log_file: The log file to query.
    :return: The db duration, in microseconds.
    """
    query = '\n    SELECT MAX(timestamp) - MIN(timestamp) AS diff_us\n    FROM lidar_pc;\n    '
    result = execute_one(query, (), log_file)
    return int(result['diff_us'])

def get_db_log_duration(log_file: str) -> Generator[Tuple[str, int], None, None]:
    """
    Get the duration of each log present in the database, measured as (last_lidar_pc_timestamp) - (first_lidarpc_timestamp)
    :param log_file: The log file to query.
    :return: A tuple of (log_name, duration) pair, one for each log file present in the DB, sorted by log name.
    """
    query = '\n    SELECT  l.logfile,\n            MAX(lp.timestamp) - MIN(lp.timestamp) AS duration_us\n    FROM log AS l\n    INNER JOIN scene AS s\n        ON s.log_token = l.token\n    INNER JOIN lidar_pc AS lp\n        ON lp.scene_token = s.token\n    GROUP BY l.logfile\n    ORDER BY l.logfile ASC;\n    '
    for row in execute_many(query, (), log_file):
        yield (row['logfile'], row['duration_us'])

def get_db_log_vehicles(log_file: str) -> Generator[Tuple[str, str], None, None]:
    """
    Get the vehicle used for each log file in the DB, sorted by log file name.
    :param log_file: The log file to query.
    :return: A tuple of (log_name, vehicle_name) for each log file in the database.
    """
    query = '\n    SELECT  logfile,\n            vehicle_name\n    FROM log\n    ORDER BY logfile ASC;\n    '
    for row in execute_many(query, (), log_file):
        yield (row['logfile'], row['vehicle_name'])

def get_db_scenario_info(log_file: str) -> Generator[Tuple[str, int], None, None]:
    """
    Get the scenario types present in the dictionary and the number of occurances, ordered by occurance count.
    :param log_file: The log file to query.
    :return: A generator of (scenario_tag, count) tuples, ordered by count desc.
    """
    query = '\n    SELECT  type,\n            COUNT(*) AS cnt\n    FROM scenario_tag\n    GROUP BY type\n    ORDER BY cnt DESC;\n    '
    for row in execute_many(query, (), log_file):
        yield (row['type'], row['cnt'])

@dataclass(frozen=True)
class Image(SensorDataTableRow):
    """
    A class representing a row in the Image table.
    Each field corresponds to a column in the row.
    """
    token: Optional[str]
    next_token: Optional[str]
    prev_token: Optional[str]
    ego_pose_token: Optional[str]
    camera_token: Optional[str]
    filename_jpg: Optional[str]
    timestamp: Optional[int]
    channel: Optional[str]

    @classmethod
    def from_db_row(cls, row: sqlite3.Row) -> Image:
        """
        A convenience method to convert a row from the Image table into a row.
        :param row: A sqlite row.
        :return: A SensorDataTableRow Image.
        """
        keys: Set[str] = set(row.keys())
        return cls(token=row['token'].hex() if 'token' in keys else None, next_token=row['next_token'].hex() if 'next_token' in keys and row['next_token'] is not None else None, prev_token=row['prev_token'].hex() if 'prev_token' in keys and row['prev_token'] is not None else None, ego_pose_token=row['ego_pose_token'].hex() if 'ego_pose_token' in keys else None, camera_token=row['camera_token'].hex() if 'camera_token' in keys else None, filename_jpg=row['filename_jpg'] if 'filename_jpg' in keys else None, timestamp=row['timestamp'] if 'timestamp' in keys else None, channel=row['channel'] if 'channel' in keys else None)

@classmethod
def from_db_row(cls, row: sqlite3.Row) -> Image:
    """
        A convenience method to convert a row from the Image table into a row.
        :param row: A sqlite row.
        :return: A SensorDataTableRow Image.
        """
    keys: Set[str] = set(row.keys())
    return cls(token=row['token'].hex() if 'token' in keys else None, next_token=row['next_token'].hex() if 'next_token' in keys and row['next_token'] is not None else None, prev_token=row['prev_token'].hex() if 'prev_token' in keys and row['prev_token'] is not None else None, ego_pose_token=row['ego_pose_token'].hex() if 'ego_pose_token' in keys else None, camera_token=row['camera_token'].hex() if 'camera_token' in keys else None, filename_jpg=row['filename_jpg'] if 'filename_jpg' in keys else None, timestamp=row['timestamp'] if 'timestamp' in keys else None, channel=row['channel'] if 'channel' in keys else None)

def get_sensor_token_by_index_from_db(log_file: str, sensor_source: SensorDataSource, index: int) -> Optional[str]:
    """
    Get the N-th sensor token ordered chronologically by timestamp from a particular channel.
    This is primarily used for unit testing.
    If the index does not exist (e.g. index = 10,000 in a log file with 1000 entries),
        then the result will be None.
    Only non-negative integer indexes are supported.
    :param log_file: The db file to query.
    :param sensor_source: Parameters for querying the correct table.
    :param index: The 0-indexed integer index of the lidarpc token to retrieve.
    :return: The token, if it exists.
    """
    if index < 0:
        raise ValueError(f'Index of {index} was supplied to get_lidarpc_token_by_index_from_db(), which is negative.')
    sensor_token = get_sensor_token(log_file, sensor_source.sensor_table, sensor_source.channel)
    query = f'\n    WITH ordered AS\n    (\n        SELECT  token,\n                lidar_token,\n                ROW_NUMBER() OVER (ORDER BY timestamp ASC) AS row_num\n        FROM {sensor_source.table}\n    )\n    SELECT token\n    FROM ordered\n    WHERE (row_num - 1) = ?\n        AND {sensor_source.sensor_token_column} = ?;\n    '
    result = execute_one(query, [index, bytearray.fromhex(sensor_token)], log_file)
    return None if result is None else str(result['token'].hex())

def get_end_sensor_time_from_db(log_file: str, sensor_source: SensorDataSource) -> int:
    """
    Get the timestamp of the last sensor data recorded in the log file.
    :param log_file: The db file to query.
    :param sensor_source: Parameters for querying the correct table.
    :return: The timestamp of the last sensor data.
    """
    query = f'\n    SELECT MAX(timestamp) AS max_time\n    FROM {sensor_source.table};\n    '
    result = execute_one(query, [], log_file)
    return int(result['max_time'])

def get_sensor_data_token_timestamp_from_db(log_file: str, sensor_source: SensorDataSource, token: str) -> Optional[int]:
    """
    Get the timestamp associated with an individual lidar_pc token.
    :param log_file: The db file to query.
    :param sensor_source: Parameters for querying the correct table.
    :param token: The token for which to grab the timestamp.
    :return: The timestamp associated with the token, if found.
    """
    query = f'\n    SELECT timestamp\n    FROM {sensor_source.table}\n    WHERE token = ?;\n    '
    result = execute_one(query, (bytearray.fromhex(token),), log_file)
    return None if result is None else int(result['timestamp'])

def get_sensor_token_map_name_from_db(log_file: str, sensor_source: SensorDataSource, token: str) -> Optional[str]:
    """
    Get the map name for a provided sensor token.
    :param log_file: The db file to query.
    :param sensor_source: Parameters for querying the correct table.
    :param token: The token for which to get the map name.
    :return: The map name for the token, if found.
    """
    query = f'\n    SELECT map_version\n    FROM log AS l\n    INNER JOIN {sensor_source.sensor_table} AS sensor\n        ON sensor.log_token = l.token\n    INNER JOIN {sensor_source.table} AS sensor_data\n        ON sensor_data.{sensor_source.sensor_token_column} = sensor.token\n    WHERE sensor_data.token = ?;\n    '
    result = execute_one(query, (bytearray.fromhex(token),), log_file)
    return None if result is None else result['map_version']

def get_sampled_sensor_tokens_in_time_window_from_db(log_file: str, sensor_source: SensorDataSource, start_timestamp: int, end_timestamp: int, subsample_interval: int) -> Generator[str, None, None]:
    """
    For every token in a window defined by [start_timestamp, end_timestamp], retrieve every `subsample_interval`-th sensor token, ordered in increasing order by timestamp.

    E.g. for this table
    ```
    token | timestamp
    -----------------
    1     | 0
    2     | 1
    3     | 2
    4     | 3
    5     | 4
    6     | 5
    7     | 6
    ```

    query with start_timestamp=1, end_timestamp=5, subsample_interval=2, table=lidar_pc, will return tokens
    [1, 3, 5].

    :param log_file: The db file to query.
    :param sensor_source: Parameters for querying the correct table.
    :param start_timestamp: The start of the window to sample, inclusive.
    :param end_timestamp: The end of the window to sample, inclusive.
    :param subsample_interval: The interval at which to sample.
    :return: A generator of lidar_pc tokens that fit the provided parameters.
    """
    sensor_token = get_sensor_token(log_file, sensor_source.sensor_table, sensor_source.channel)
    query = f'\n    WITH numbered AS\n    (\n        SELECT token, timestamp, ROW_NUMBER() OVER (ORDER BY timestamp ASC) AS row_num\n        FROM {sensor_source.table}\n        WHERE timestamp >= ?\n        AND timestamp <= ?\n        AND {sensor_source.sensor_token_column} == ?\n    )\n    SELECT token\n    FROM numbered\n    WHERE ((row_num - 1) % ?) = 0\n    ORDER BY timestamp ASC;\n    '
    for row in execute_many(query, (start_timestamp, end_timestamp, bytearray.fromhex(sensor_token), subsample_interval), log_file):
        yield row['token'].hex()

def get_sensor_data_from_sensor_data_tokens_from_db(log_file: str, sensor_source: SensorDataSource, sensor_class: Type[SensorDataTableRow], tokens: Union[Generator[str, None, None], List[str]]) -> Generator[SensorDataTableRow, None, None]:
    """
    Given a collection of sensor tokens, builds the corresponding sensor_class objects.
    This function makes no restrictions on the ordering of returned values.
    :param sensor_source: Parameters for querying the correct table.
    :param sensor_class: Class holding a row of the SensorData table.
    :param log_file: The db file to query.
    :param tokens: The tokens for which to build the sensor_class objects.
    :return: A generator yielding sensor_class objects.
    """
    if not isinstance(tokens, list):
        tokens = list(tokens)
    query = f'\n        SELECT *\n        FROM {sensor_source.table}\n        WHERE token IN ({('?,' * len(tokens))[:-1]});\n    '
    for row in execute_many(query, [bytearray.fromhex(t) for t in tokens], log_file):
        yield sensor_class.from_db_row(row)

def get_mission_goal_for_sensor_data_token_from_db(log_file: str, sensor_source: SensorDataSource, token: str) -> Optional[StateSE2]:
    """
    Get the goal pose for a given lidar_pc token.
    :param log_file: The db file to query.
    :param sensor_source: Parameters for querying the correct table.
    :param token: The token for which to query the goal state.
    :return: The goal state.
    """
    query = f'\n        SELECT  ep.x,\n                ep.y,\n                ep.qw,\n                ep.qx,\n                ep.qy,\n                ep.qz\n        FROM ego_pose AS ep\n        INNER JOIN scene AS s\n            ON s.goal_ego_pose_token = ep.token\n        INNER JOIN {sensor_source.table} AS sensor_data\n            ON sensor_data.scene_token = s.token\n        WHERE sensor_data.token = ?\n    '
    row = execute_one(query, (bytearray.fromhex(token),), log_file)
    if row is None:
        return None
    q = Quaternion(row['qw'], row['qx'], row['qy'], row['qz'])
    return StateSE2(row['x'], row['y'], q.yaw_pitch_roll[0])

def get_roadblock_ids_for_lidarpc_token_from_db(log_file: str, lidarpc_token: str) -> Optional[List[str]]:
    """
    Get the scene roadblock ids from the db for a given lidar_pc token.
    :param log_file: The db file to query.
    :param lidarpc_token: The token for which to query the current state.
    :return: List of roadblock ids as str.
    """
    query = '\n        SELECT  s.roadblock_ids\n        FROM scene AS s\n        INNER JOIN lidar_pc AS lp\n            ON lp.scene_token = s.token\n        WHERE lp.token = ?\n    '
    row = execute_one(query, (bytearray.fromhex(lidarpc_token),), log_file)
    if row is None:
        return None
    return str(row['roadblock_ids']).split(' ')

def get_statese2_for_lidarpc_token_from_db(log_file: str, token: str) -> Optional[StateSE2]:
    """
    Get the ego pose as a StateSE2 from the db for a given lidar_pc token.
    :param log_file: The db file to query.
    :param token: The token for which to query the current state.
    :return: The current ego state, as a StateSE2 object.
    """
    query = '\n        SELECT  ep.x,\n                ep.y,\n                ep.qw,\n                ep.qx,\n                ep.qy,\n                ep.qz\n        FROM ego_pose AS ep\n        INNER JOIN lidar_pc AS lp\n            ON lp.ego_pose_token = ep.token\n        WHERE lp.token = ?\n    '
    row = execute_one(query, (bytearray.fromhex(token),), log_file)
    if row is None:
        return None
    q = Quaternion(row['qw'], row['qx'], row['qy'], row['qz'])
    return StateSE2(row['x'], row['y'], q.yaw_pitch_roll[0])

def get_sampled_lidarpcs_from_db(log_file: str, initial_token: str, sensor_source: SensorDataSource, sample_indexes: Union[Generator[int, None, None], List[int]], future: bool) -> Generator[LidarPc, None, None]:
    """
    Given an anchor token, return the tokens of either the previous or future tokens, sampled by the provided indexes.

    The result is always sorted by timestamp ascending.

    For example, given the following table:
    token | timestamp
    -----------------
    0     | 0
    1     | 1
    2     | 2
    3     | 3
    4     | 4
    5     | 5
    6     | 6
    7     | 7
    8     | 8
    9     | 9
    10    | 10

    Some sample results:
    initial token | sample_indexes | future | returned tokens
    ---------------------------------------------------------
    5             | [0, 1, 2]      | True   | [5, 6, 7]
    5             | [0, 1, 2]      | False  | [3, 4, 5]
    7             | [0, 3, 12]     | False  | [4, 7]
    0             | [11]           | True   | []

    :param log_file: The db file to query.
    :param initial_token: The token on which to base the query.
    :param sensor_source: Parameters for querying the correct table.
    :param sample_indexes: The indexes for which to sample.
    :param future: If true, the indexes represent future times. If false, they represent previous times.
    :return: A generator of LidarPC objects representing the requested indexes
    """
    if not isinstance(sample_indexes, list):
        sample_indexes = list(sample_indexes)
    sensor_token = get_sensor_token(log_file, sensor_source.sensor_table, sensor_source.channel)
    order_direction = 'ASC' if future else 'DESC'
    order_cmp = '>=' if future else '<='
    query = f'\n        WITH initial_lidarpc AS\n        (\n            SELECT token, timestamp\n            FROM lidar_pc\n            WHERE token = ?\n        ),\n        ordered AS\n        (\n            SELECT  lp.token,\n                    lp.next_token,\n                    lp.prev_token,\n                    lp.ego_pose_token,\n                    lp.lidar_token,\n                    lp.scene_token,\n                    lp.filename,\n                    lp.timestamp,\n                    ROW_NUMBER() OVER (ORDER BY lp.timestamp {order_direction}) AS row_num\n            FROM lidar_pc AS lp\n            CROSS JOIN initial_lidarpc AS il\n            WHERE   lp.timestamp {order_cmp} il.timestamp\n            AND lp.lidar_token = ?\n        )\n        SELECT  token,\n                next_token,\n                prev_token,\n                ego_pose_token,\n                lidar_token,\n                scene_token,\n                filename,\n                timestamp\n        FROM ordered\n\n        -- ROW_NUMBER() starts at 1, where consumers will expect sample_indexes to be 0-indexed\n        WHERE (row_num - 1) IN ({('?,' * len(sample_indexes))[:-1]})\n\n        ORDER BY timestamp ASC;\n    '
    args = [bytearray.fromhex(initial_token), bytearray.fromhex(sensor_token)] + sample_indexes
    for row in execute_many(query, args, log_file):
        yield LidarPc.from_db_row(row)

def get_sampled_ego_states_from_db(log_file: str, initial_token: str, sensor_source: SensorDataSource, sample_indexes: Union[Generator[int, None, None], List[int]], future: bool) -> Generator[EgoState, None, None]:
    """
    Given an anchor token, retrieve the ego states associated with tokens order by time, sampled by the provided indexes.

    The result is always sorted by timestamp ascending.

    For example, given the following table:
    token | timestamp | ego_state
    -----------------------------
    0     | 0         | A
    1     | 1         | B
    2     | 2         | C
    3     | 3         | D
    4     | 4         | E
    5     | 5         | F
    6     | 6         | G
    7     | 7         | H
    8     | 8         | I
    9     | 9         | J
    10    | 10        | K

    Some sample results:
    initial token | sample_indexes | future | returned states
    ---------------------------------------------------------
    5             | [0, 1, 2]      | True   | [F, G, H]
    5             | [0, 1, 2]      | False  | [D, E, F]
    7             | [0, 3, 12]     | False  | [E, H]
    0             | [11]           | True   | []

    :param log_file: The db file to query.
    :param initial_token: The token on which to base the query.
    :param sample_indexes: The indexes for which to sample.
    :param future: If true, the indexes represent future times. If false, they represent previous times.
    :return: A generator of EgoState objects associated with the given LidarPCs.
    """
    if not isinstance(sample_indexes, list):
        sample_indexes = list(sample_indexes)
    sensor_token = get_sensor_token(log_file, sensor_source.sensor_table, sensor_source.channel)
    order_direction = 'ASC' if future else 'DESC'
    order_cmp = '>=' if future else '<='
    query = f'\n        WITH initial_lidarpc AS\n        (\n            SELECT token, timestamp\n            FROM lidar_pc\n            WHERE token = ?\n        ),\n        ordered AS\n        (\n            SELECT  lp.token,\n                    lp.next_token,\n                    lp.prev_token,\n                    lp.ego_pose_token,\n                    lp.lidar_token,\n                    lp.scene_token,\n                    lp.filename,\n                    lp.timestamp,\n                    ROW_NUMBER() OVER (ORDER BY lp.timestamp {order_direction}) AS row_num\n            FROM lidar_pc AS lp\n            CROSS JOIN initial_lidarpc AS il\n            WHERE   lp.timestamp {order_cmp} il.timestamp\n            AND lidar_token = ?\n        )\n        SELECT  ep.x,\n                ep.y,\n                ep.qw,\n                ep.qx,\n                ep.qy,\n                ep.qz,\n                -- ego_pose and lidar_pc timestamps are not the same, even when linked by token!\n                -- use the lidar_pc timestamp for compatibility with older code.\n                o.timestamp,\n                ep.vx,\n                ep.vy,\n                ep.acceleration_x,\n                ep.acceleration_y\n        FROM ego_pose AS ep\n        INNER JOIN ordered AS o\n            ON o.ego_pose_token = ep.token\n\n        -- ROW_NUMBER() starts at 1, where consumers will expect sample_indexes to be 0-indexed\n        WHERE (o.row_num - 1) IN ({('?,' * len(sample_indexes))[:-1]})\n\n        ORDER BY o.timestamp ASC;\n    '
    args = [bytearray.fromhex(initial_token), bytearray.fromhex(sensor_token)] + sample_indexes
    for row in execute_many(query, args, log_file):
        q = Quaternion(row['qw'], row['qx'], row['qy'], row['qz'])
        yield EgoState.build_from_rear_axle(StateSE2(row['x'], row['y'], q.yaw_pitch_roll[0]), tire_steering_angle=0.0, vehicle_parameters=get_pacifica_parameters(), time_point=TimePoint(row['timestamp']), rear_axle_velocity_2d=StateVector2D(row['vx'], y=row['vy']), rear_axle_acceleration_2d=StateVector2D(x=row['acceleration_x'], y=row['acceleration_y']))

def get_ego_state_for_lidarpc_token_from_db(log_file: str, token: str) -> EgoState:
    """
    Get the ego state associated with an individual lidar_pc token from the db.

    :param log_file: The log file to query.
    :param token: The lidar_pc token to query.
    :return: The EgoState associated with the LidarPC.
    """
    query = '\n        SELECT  ep.x,\n                ep.y,\n                ep.qw,\n                ep.qx,\n                ep.qy,\n                ep.qz,\n                -- ego_pose and lidar_pc timestamps are not the same, even when linked by token!\n                -- use lidar_pc timestamp for backwards compatibility.\n                lp.timestamp,\n                ep.vx,\n                ep.vy,\n                ep.acceleration_x,\n                ep.acceleration_y\n        FROM ego_pose AS ep\n        INNER JOIN lidar_pc AS lp\n            ON lp.ego_pose_token = ep.token\n        WHERE lp.token = ?\n    '
    row = execute_one(query, (bytearray.fromhex(token),), log_file)
    if row is None:
        return None
    q = Quaternion(row['qw'], row['qx'], row['qy'], row['qz'])
    return EgoState.build_from_rear_axle(StateSE2(row['x'], row['y'], q.yaw_pitch_roll[0]), tire_steering_angle=0.0, vehicle_parameters=get_pacifica_parameters(), time_point=TimePoint(row['timestamp']), rear_axle_velocity_2d=StateVector2D(row['vx'], y=row['vy']), rear_axle_acceleration_2d=StateVector2D(x=row['acceleration_x'], y=row['acceleration_y']))

def get_traffic_light_status_for_lidarpc_token_from_db(log_file: str, token: str) -> Generator[TrafficLightStatusData, None, None]:
    """
    Get the traffic light information associated with a given lidar_pc.
    :param log_file: The log file to query.
    :param token: The lidar_pc token for which to obtain the traffic light information.
    :return: The traffic light status data associated with the given lidar_pc.
    """
    query = '\n        SELECT  CASE WHEN tl.status == "green" THEN 0\n                     WHEN tl.status == "yellow" THEN 1\n                     WHEN tl.status == "red" THEN 2\n                     ELSE 3\n                END AS status,\n                tl.lane_connector_id,\n                lp.timestamp AS timestamp\n        FROM lidar_pc AS lp\n        INNER JOIN traffic_light_status AS tl\n            ON lp.token = tl.lidar_pc_token\n        WHERE lp.token = ?\n    '
    for row in execute_many(query, (bytearray.fromhex(token),), log_file):
        yield TrafficLightStatusData(status=TrafficLightStatusType(row['status']), lane_connector_id=row['lane_connector_id'], timestamp=row['timestamp'])

def get_tracked_objects_within_time_interval_from_db(log_file: str, start_timestamp: int, end_timestamp: int, filter_track_tokens: Optional[Set[str]]=None) -> Generator[TrackedObject, None, None]:
    """
    Gets all of the tracked objects between the provided timestamps, inclusive.
    Optionally filters on a user-provided set of track tokens.

    This query will not obtain the future waypoints.
    For that, call `get_future_waypoints_for_agents_from_db()`
    with the tokens of the agents of interest.

    :param log_file: The log file to query.
    :param start_timestamp: The starting timestamp for which to query, in uS.
    :param end_timestamp: The ending timestamp for which to query, in uS.
    :param filter_track_tokens: If provided, only agents with `track_tokens` present in the provided set will be returned.
      If not provided, then all agents present at every time stamp will be returned.
    :return: A generator of TrackedObjects, sorted by TimeStamp, then TrackedObject.
    """
    args: List[Union[int, bytearray]] = [start_timestamp, end_timestamp]
    filter_clause = ''
    if filter_track_tokens is not None:
        filter_clause = "\n            AND lb.track_token IN ({('?,'*len(filter_track_tokens))[:-1]})\n        "
        for token in filter_track_tokens:
            args.append(bytearray.fromhex(token))
    query = f'\n        SELECT  c.name AS category_name,\n                lb.x,\n                lb.y,\n                lb.z,\n                lb.yaw,\n                lb.width,\n                lb.length,\n                lb.height,\n                lb.vx,\n                lb.vy,\n                lb.token,\n                lb.track_token,\n                lp.timestamp\n        FROM lidar_box AS lb\n        INNER JOIN track AS t\n            ON t.token = lb.track_token\n        INNER JOIN category AS c\n            ON c.token = t.category_token\n        INNER JOIN lidar_pc AS lp\n            ON lp.token = lb.lidar_pc_token\n        WHERE lp.timestamp >= ?\n            AND lp.timestamp <= ?\n            {filter_clause}\n        ORDER BY lp.timestamp ASC, lb.track_token ASC;\n    '
    for row in execute_many(query, args, log_file):
        yield _parse_tracked_object_row(row)

def get_tracked_objects_for_lidarpc_token_from_db(log_file: str, token: str) -> Generator[TrackedObject, None, None]:
    """
    Get all tracked objects for a given lidar_pc.
    This includes both agents and static objects.
    The values are returned in random order.

    For agents, this query will not obtain the future waypoints.
    For that, call `get_future_waypoints_for_agents_from_db()`
        with the tokens of the agents of interest.

    :param log_file: The log file to query.
    :param token: The lidar_pc token for which to obtain the objects.
    :return: The tracked objects associated with the token.
    """
    query = '\n        SELECT  c.name AS category_name,\n                lb.x,\n                lb.y,\n                lb.z,\n                lb.yaw,\n                lb.width,\n                lb.length,\n                lb.height,\n                lb.vx,\n                lb.vy,\n                lb.token,\n                lb.track_token,\n                lp.timestamp\n        FROM lidar_box AS lb\n        INNER JOIN track AS t\n            ON t.token = lb.track_token\n        INNER JOIN category AS c\n            ON c.token = t.category_token\n        INNER JOIN lidar_pc AS lp\n            ON lp.token = lb.lidar_pc_token\n        WHERE lp.token = ?\n    '
    for row in execute_many(query, (bytearray.fromhex(token),), log_file):
        yield _parse_tracked_object_row(row)

def get_future_waypoints_for_agents_from_db(log_file: str, track_tokens: Union[Generator[str, None, None], List[str]], start_timestamp: int, end_timestamp: int) -> Generator[Tuple[str, Waypoint], None, None]:
    """
    Obtain the future waypoints for the selected agents from the DB in the provided time window.
    Results are sorted by track token, then by timestamp in ascending order.

    :param log_file: The log file to query.
    :param track_tokens: The track_tokens for which to query.
    :param start_timestamp: The starting timestamp for which to query.
    :param end_timestamp: The maximal time for which to query.
    :return: A generator of tuples of (track_token, Waypoint), sorted by track_token, then by timestamp in ascending order.
    """
    if not isinstance(track_tokens, list):
        track_tokens = list(track_tokens)
    query = f'\n        SELECT  lb.x,\n                lb.y,\n                lb.z,\n                lb.yaw,\n                lb.width,\n                lb.length,\n                lb.height,\n                lb.vx,\n                lb.vy,\n                lb.track_token,\n                lp.timestamp\n        FROM lidar_box AS lb\n        INNER JOIN lidar_pc AS lp\n            ON lp.token = lb.lidar_pc_token\n        WHERE   lp.timestamp >= ?\n            AND lp.timestamp <= ?\n            AND lb.track_token IN\n            ({('?,' * len(track_tokens))[:-1]})\n        ORDER BY lb.track_token ASC, lp.timestamp ASC;\n    '
    args = [start_timestamp, end_timestamp] + [bytearray.fromhex(t) for t in track_tokens]
    for row in execute_many(query, args, log_file):
        pose = StateSE2(row['x'], row['y'], row['yaw'])
        oriented_box = OrientedBox(pose, width=row['width'], height=row['height'], length=row['length'])
        velocity = StateVector2D(row['vx'], row['vy'])
        yield (row['track_token'].hex(), Waypoint(TimePoint(row['timestamp']), oriented_box, velocity))

def get_scenarios_from_db(log_file: str, filter_tokens: Optional[List[str]], filter_types: Optional[List[str]], filter_map_names: Optional[List[str]], include_invalid_mission_goals: bool=True, include_cameras: bool=False) -> Generator[sqlite3.Row, None, None]:
    """
    Get the scenarios present in the db file that match the specified filter criteria.
    If a filter is None, then it will be elided from the query.
    Results are sorted by timestamp ascending
    :param log_file: The log file to query.
    :param filter_tokens: If provided, the set of allowable tokens to return.
    :param filter_types: If provided, the set of allowable scenario types to return.
    :param filter_map_names: If provided, the set of allowable map names to return.
    :param include_cameras: If true, filter for lidar_pcs that has corresponding images.
    :param include_invalid_mission_goals: If true, then scenarios without a valid mission goal will be included
        (i.e. get_mission_goal_for_sensor_data_token_from_db(token) returns None)
        If False, then these scenarios will be filtered.
    :sensor_data_source: Table specification for data sourcing.
    :return: A sqlite3.Row object with the following fields:
        * token: The initial lidar_pc token of the scenario.
        * timestamp: The timestamp of the initial lidar_pc of the scenario.
        * map_name: The map name from which the scenario came.
        * scenario_type: One of the mapped scenario types for the scenario.
            This can be None if there are no matching rows in scenario_types table.
            If there are multiple matches, then one is selected from the set of allowable filter clauses at random.
    """
    filter_clauses = []
    args: List[Union[str, bytearray]] = []
    if filter_types is not None:
        filter_clauses.append(f'\n        st.type IN ({('?,' * len(filter_types))[:-1]})\n        ')
        args += filter_types
    if filter_tokens is not None:
        filter_clauses.append(f'\n        lp.token IN ({('?,' * len(filter_tokens))[:-1]})\n        ')
        args += [bytearray.fromhex(t) for t in filter_tokens]
    if filter_map_names is not None:
        filter_clauses.append(f'\n        l.map_version IN ({('?,' * len(filter_map_names))[:-1]})\n        ')
        args += filter_map_names
    if len(filter_clauses) > 0:
        filter_clause = 'WHERE ' + ' AND '.join(filter_clauses)
    else:
        filter_clause = ''
    if include_invalid_mission_goals:
        invalid_goals_joins = ''
    else:
        invalid_goals_joins = '\n        ---Join on ego_pose to filter scenarios that do not have a valid mission goal\n        INNER JOIN scene AS invalid_goal_scene\n            ON invalid_goal_scene.token = lp.scene_token\n        INNER JOIN ego_pose AS invalid_goal_ego_pose\n            ON invalid_goal_scene.goal_ego_pose_token = invalid_goal_ego_pose.token\n        '
    if include_cameras:
        matching_camera_clause = '\n        INNER JOIN image AS img\n            ON img.ego_pose_token = lp.ego_pose_token\n        '
    else:
        matching_camera_clause = ''
    query = f'\n        WITH ordered_scenes AS\n        (\n            SELECT  token,\n                    ROW_NUMBER() OVER (ORDER BY name ASC) AS row_num\n            FROM scene\n        ),\n        num_scenes AS\n        (\n            SELECT  COUNT(*) AS cnt\n            FROM scene\n        ),\n        valid_scenes AS\n        (\n            SELECT  o.token\n            FROM ordered_scenes AS o\n            CROSS JOIN num_scenes AS n\n\n            -- Define "valid" scenes as those that have at least 2 before and 2 after\n            -- Note that the token denotes the beginning of a scene\n            WHERE o.row_num >= 3 AND o.row_num < n.cnt - 1\n        )\n        SELECT  lp.token,\n                lp.timestamp,\n                l.map_version AS map_name,\n\n                -- scenarios can have multiple tags\n                -- Pick one arbitrarily from the list of acceptable tags\n                MAX(st.type) AS scenario_type\n        FROM lidar_pc AS lp\n        LEFT OUTER JOIN scenario_tag AS st\n            ON lp.token = st.lidar_pc_token\n        INNER JOIN lidar AS ld\n            ON ld.token = lp.lidar_token\n        INNER JOIN log AS l\n            ON ld.log_token = l.token\n        INNER JOIN valid_scenes AS vs\n            ON lp.scene_token = vs.token\n        {matching_camera_clause}\n        {invalid_goals_joins}\n        {filter_clause}\n        GROUP BY    lp.token,\n                    lp.timestamp,\n                    l.map_version\n        ORDER BY lp.timestamp ASC;\n    '
    for row in execute_many(query, args, log_file):
        yield row

def get_lidarpc_tokens_with_scenario_tag_from_db(log_file: str) -> Generator[Tuple[str, str], None, None]:
    """
    Get the LidarPc tokens that are tagged with a scenario from the DB, sorted by scenario_type in ascending order.
    :param log_file: The log file to query.
    :return: A generator of (scenario_tag, token) tuples where `token` is tagged with `scenario_tag`
    """
    query = '\n    SELECT  st.type,\n            lp.token\n    FROM lidar_pc AS lp\n    LEFT OUTER JOIN scenario_tag AS st\n        ON lp.token=st.lidar_pc_token\n    WHERE st.type IS NOT NULL\n    ORDER BY st.type ASC NULLS LAST;\n    '
    for row in execute_many(query, (), log_file):
        yield (str(row['type']), row['token'].hex())

def get_sensor_token(log_file: str, table: str, channel: str) -> str:
    """
    Get the sensor token of a particular channel for the given table.
    :param log_file: The DB file.
    :param table: The sensor table to query.
    :param channel: The channel to select.
    :return: The token of the sensor with the given channel.
    """
    q1 = f"\n        SELECT token\n        FROM {table}\n        WHERE channel == '{channel}';\n    "
    row = execute_one(q1, (), log_file)
    if row is None:
        raise RuntimeError(f'Channel {channel} not found in table {table}!')
    return str(row['token'].hex())

def get_images_from_lidar_tokens(log_file: str, tokens: List[str], channels: List[str], lookahead_window_us: int=50000, lookback_window_us: int=50000) -> Generator[Image, None, None]:
    """
    Get the images from the given channels for the given lidar_pc_tokens.
    Note: Both lookahead_window_us and lookback_window_us is defaulted to 50000us (0.05s). This means the search window
          is 0.1s centered around the queried lidar_pc timestamp. This is because lidar_pc are stored at 20hz and images
          are at 10hz for NuPlanDB. Hence, we can search the entire duration between lidar_pcs.
          Consider the example below where we want to query for images from the lidar_pc '4'. '|' represents a sample.

          iteration: 0    1    2    3   [4]   5    6
          timestamp: 0   0.05 0.1  0.15 0.2  0.25 0.3
          lidar_pc:  |    |    |    |    |    |    |
          Images:    |         |         |         |
          search window:            [---------]

          We set the search window to lookahead_window_us + lookback_window_us = 0.1s centered around lidar_pc '4'.
          This should guarantee that we retrieve the correct images associated with the queried lidar_pc.

    :param log_file: The log file to query.
    :param tokens: corresponding lidar_pc.
    :param channels: The channel to select.
    :param lookahead_window_us: [us] The time duration to look ahead relative to the lidar_pc for matching images.
    :param lookback_window_us: [us] The time duration to look back relative to the lidar_pc for matching images.
    :return: Images as a SensorDataTableRow.
    """
    query = f'\n            SELECT\n                img.token,\n                img.next_token,\n                img.prev_token,\n                img.ego_pose_token,\n                img.camera_token,\n                img.filename_jpg,\n                img.timestamp,\n                cam.channel\n            FROM image AS img\n              INNER JOIN lidar_pc AS lpc\n                ON  img.timestamp <= lpc.timestamp + ?\n                AND img.timestamp >= lpc.timestamp - ?\n              INNER JOIN camera AS cam\n                ON cam.token = img.camera_token\n            WHERE cam.channel IN ({('?,' * len(channels))[:-1]}) AND lpc.token IN ({('?,' * len(tokens))[:-1]})\n            ORDER BY lpc.timestamp ASC;\n    '
    args = [lookahead_window_us, lookback_window_us]
    args += channels
    args += [bytearray.fromhex(t) for t in tokens]
    for row in execute_many(query, args, log_file):
        yield Image.from_db_row(row)

def get_cameras(log_file: str, channels: List[str]) -> Generator[Camera, None, None]:
    """
    Get the cameras for the given channels.
    :param log_file: The log file to query.
    :param channels: The channel to select.
    :return: Cameras as a SensorDataTableRow.
    """
    query = f'\n            SELECT *\n            FROM camera AS cam\n            WHERE cam.channel IN ({('?,' * len(channels))[:-1]})\n    '
    for row in execute_many(query, channels, log_file):
        yield Camera.from_db_row(row)

@dataclass(frozen=True)
class LidarPc(SensorDataTableRow):
    """
    A class representing a row in the LidarPC table.
    Each field corresponds to a column in the row.
    """
    token: Optional[str]
    next_token: Optional[str]
    prev_token: Optional[str]
    ego_pose_token: Optional[str]
    lidar_token: Optional[str]
    scene_token: Optional[str]
    filename: Optional[str]
    timestamp: Optional[int]

    @classmethod
    def from_db_row(cls, row: sqlite3.Row) -> LidarPc:
        """
        A convenience method to convert a row from the LidarPc table into a row.
        """
        keys: Set[str] = set(row.keys())
        return cls(token=row['token'].hex() if 'token' in keys else None, next_token=row['next_token'].hex() if 'next_token' in keys else None, prev_token=row['prev_token'].hex() if 'prev_token' in keys else None, ego_pose_token=row['ego_pose_token'].hex() if 'ego_pose_token' in keys else None, lidar_token=row['lidar_token'].hex() if 'lidar_token' in keys else None, scene_token=row['scene_token'].hex() if 'scene_token' in keys else None, filename=row['filename'] if 'filename' in keys else None, timestamp=row['timestamp'] if 'timestamp' in keys else None)

@classmethod
def from_db_row(cls, row: sqlite3.Row) -> LidarPc:
    """
        A convenience method to convert a row from the LidarPc table into a row.
        """
    keys: Set[str] = set(row.keys())
    return cls(token=row['token'].hex() if 'token' in keys else None, next_token=row['next_token'].hex() if 'next_token' in keys else None, prev_token=row['prev_token'].hex() if 'prev_token' in keys else None, ego_pose_token=row['ego_pose_token'].hex() if 'ego_pose_token' in keys else None, lidar_token=row['lidar_token'].hex() if 'lidar_token' in keys else None, scene_token=row['scene_token'].hex() if 'scene_token' in keys else None, filename=row['filename'] if 'filename' in keys else None, timestamp=row['timestamp'] if 'timestamp' in keys else None)

def _int_to_token(val: Optional[int]) -> Optional[bytearray]:
    """
    Convert an int directly to a token bytearray.
    Intended for use only in this file.
    :param val: The int to convert.
    :return: The token bytearray.
    """
    return None if val is None else bytearray.fromhex('{:08d}'.format(val))

class TestSensorDataSource(unittest.TestCase):
    """Tests for the SensorDataSource class."""

    def test_initialization(self) -> None:
        """Tests correct initialization and raising of invalid configuration."""
        with self.assertRaisesRegex(AssertionError, 'Incompatible sensor_table: camera for table lidar_pc'):
            SensorDataSource('lidar_pc', 'camera', 'camera_token', '')
        with self.assertRaisesRegex(AssertionError, 'Incompatible sensor_table: lidar for table image'):
            SensorDataSource('image', 'lidar', 'lidar_token', '')
        with self.assertRaisesRegex(ValueError, 'Unknown requested sensor table: unknown'):
            SensorDataSource('unknown', '', '', '')
        with self.assertRaisesRegex(AssertionError, 'Incompatible sensor_token_column: lidar_token for sensor_table camera'):
            SensorDataSource('image', 'camera', 'lidar_token', '')
        _ = SensorDataSource('lidar_pc', 'lidar', 'lidar_token', '')
        valid_sensor_data_source = SensorDataSource('image', 'camera', 'camera_token', 'channel')
        self.assertEqual(valid_sensor_data_source.table, 'image')
        self.assertEqual(valid_sensor_data_source.sensor_table, 'camera')
        self.assertEqual(valid_sensor_data_source.sensor_token_column, 'camera_token')
        self.assertEqual(valid_sensor_data_source.channel, 'channel')

    def test_get_lidarpc_sensor_data(self) -> None:
        """Tests that utility function builds the correct object."""
        sensor_data = get_lidarpc_sensor_data()
        self.assertEqual(sensor_data.table, 'lidar_pc')
        self.assertEqual(sensor_data.sensor_table, 'lidar')
        self.assertEqual(sensor_data.sensor_token_column, 'lidar_token')
        self.assertEqual(sensor_data.channel, 'MergedPointCloud')

    def test_get_camera_channel_sensor_data(self) -> None:
        """Tests that utility function builds the correct object."""
        sensor_data = get_camera_channel_sensor_data('channel')
        self.assertEqual(sensor_data.table, 'image')
        self.assertEqual(sensor_data.sensor_table, 'camera')
        self.assertEqual(sensor_data.sensor_token_column, 'camera_token')
        self.assertEqual(sensor_data.channel, 'channel')

def test_initialization(self) -> None:
    """Tests correct initialization and raising of invalid configuration."""
    with self.assertRaisesRegex(AssertionError, 'Incompatible sensor_table: camera for table lidar_pc'):
        SensorDataSource('lidar_pc', 'camera', 'camera_token', '')
    with self.assertRaisesRegex(AssertionError, 'Incompatible sensor_table: lidar for table image'):
        SensorDataSource('image', 'lidar', 'lidar_token', '')
    with self.assertRaisesRegex(ValueError, 'Unknown requested sensor table: unknown'):
        SensorDataSource('unknown', '', '', '')
    with self.assertRaisesRegex(AssertionError, 'Incompatible sensor_token_column: lidar_token for sensor_table camera'):
        SensorDataSource('image', 'camera', 'lidar_token', '')
    _ = SensorDataSource('lidar_pc', 'lidar', 'lidar_token', '')
    valid_sensor_data_source = SensorDataSource('image', 'camera', 'camera_token', 'channel')
    self.assertEqual(valid_sensor_data_source.table, 'image')
    self.assertEqual(valid_sensor_data_source.sensor_table, 'camera')
    self.assertEqual(valid_sensor_data_source.sensor_token_column, 'camera_token')
    self.assertEqual(valid_sensor_data_source.channel, 'channel')

class TestNuPlanScenarioQueries(unittest.TestCase):
    """
    Test suite for the NuPlan scenario queries.
    """
    generation_parameters: DBGenerationParameters

    @staticmethod
    def getDBFilePath() -> Path:
        """
        Get the location for the temporary SQLite file used for the test DB.
        :return: The filepath for the test data.
        """
        return Path('/tmp/test_nuplan_scenario_queries.sqlite3')

    @classmethod
    def setUpClass(cls) -> None:
        """
        Create the mock DB data.
        """
        db_file_path = TestNuPlanScenarioQueries.getDBFilePath()
        if db_file_path.exists():
            db_file_path.unlink()
        cls.generation_parameters = DBGenerationParameters(num_lidars=1, num_cameras=2, num_sensor_data_per_sensor=50, num_lidarpc_per_image_ratio=2, num_scenes=10, num_traffic_lights_per_lidar_pc=5, num_agents_per_lidar_pc=3, num_static_objects_per_lidar_pc=2, scene_scenario_tag_mapping={5: ['first_tag'], 6: ['first_tag', 'second_tag'], 7: ['second_tag']}, file_path=str(db_file_path))
        generate_minimal_nuplan_db(cls.generation_parameters)

    def setUp(self) -> None:
        """
        The method to run before each test.
        """
        self.db_file_name = str(TestNuPlanScenarioQueries.getDBFilePath())
        self.sensor_source = SensorDataSource('lidar_pc', 'lidar', 'lidar_token', 'channel')

    @classmethod
    def tearDownClass(cls) -> None:
        """
        Destroy the mock DB data.
        """
        db_file_path = TestNuPlanScenarioQueries.getDBFilePath()
        if os.path.exists(db_file_path):
            os.remove(db_file_path)

    def test_get_sensor_token_from_index(self) -> None:
        """
        Test the get_sensor_token_from_index query.
        """
        for sample_index in [0, 12, 24]:
            retrieved_token = get_sensor_token_by_index_from_db(self.db_file_name, self.sensor_source, sample_index)
            self.assertEqual(sample_index / self.generation_parameters.num_lidars, str_token_to_int(retrieved_token))
        self.assertIsNone(get_sensor_token_by_index_from_db(self.db_file_name, self.sensor_source, 100000))
        with self.assertRaises(ValueError):
            get_sensor_token_by_index_from_db(self.db_file_name, self.sensor_source, -2)

    def test_get_end_sensor_time_from_db(self) -> None:
        """
        Test the get_end_sensor_time_from_db query.
        """
        log_end_time = get_end_sensor_time_from_db(self.db_file_name, sensor_source=self.sensor_source)
        self.assertEqual(49 * 1000000.0, log_end_time)

    def test_get_sensor_token_timestamp_from_db(self) -> None:
        """
        Test the get_sensor_data_token_timestamp_from_db query.
        """
        for token in [0, 3, 7]:
            expected_timestamp = token * 1000000.0
            actual_timestamp = get_sensor_data_token_timestamp_from_db(self.db_file_name, self.sensor_source, int_to_str_token(token))
            self.assertEqual(expected_timestamp, actual_timestamp)
        self.assertIsNone(get_sensor_data_token_timestamp_from_db(self.db_file_name, self.sensor_source, int_to_str_token(1000)))

    def test_get_sensor_token_map_name_from_db(self) -> None:
        """
        Test the get_sensor_token_map_name_from_db query.
        """
        for token in [0, 2, 6]:
            expected_map_name = 'map_version'
            actual_map_name = get_sensor_token_map_name_from_db(self.db_file_name, self.sensor_source, int_to_str_token(token))
            self.assertEqual(expected_map_name, actual_map_name)
        self.assertIsNone(get_sensor_token_map_name_from_db(self.db_file_name, self.sensor_source, int_to_str_token(1000)))

    def test_get_sampled_sensor_tokens_in_time_window_from_db(self) -> None:
        """
        Test the get_sampled_lidarpc_tokens_in_time_window_from_db query.
        """
        expected_tokens = [10, 13, 16, 19]
        actual_tokens = list((str_token_to_int(v) for v in get_sampled_sensor_tokens_in_time_window_from_db(log_file=self.db_file_name, sensor_source=self.sensor_source, start_timestamp=int(10 * 1000000.0), end_timestamp=int(20 * 1000000.0), subsample_interval=3)))
        self.assertEqual(expected_tokens, actual_tokens)

    def test_get_sensor_data_from_sensor_data_tokens_from_db(self) -> None:
        """
        Test the get_sensor_data_from_sensor_data_tokens_from_db query.
        """
        lidar_pc_tokens = [int_to_str_token(v) for v in [10, 13, 21]]
        image_tokens = [int_to_str_token(v) for v in [1100000]]
        lidar_pcs = [cast(LidarPc, sensor_data) for sensor_data in get_sensor_data_from_sensor_data_tokens_from_db(self.db_file_name, self.sensor_source, LidarPc, lidar_pc_tokens)]
        images = [cast(Image, sensor_data) for sensor_data in get_sensor_data_from_sensor_data_tokens_from_db(self.db_file_name, SensorDataSource('image', 'camera', 'camera_token', 'camera_0'), Image, image_tokens)]
        self.assertEqual(len(lidar_pc_tokens), len(lidar_pcs))
        self.assertEqual(len(image_tokens), len(images))
        lidar_pcs.sort(key=lambda x: int(x.timestamp))
        self.assertEqual(10, str_token_to_int(lidar_pcs[0].token))
        self.assertEqual(13, str_token_to_int(lidar_pcs[1].token))
        self.assertEqual(21, str_token_to_int(lidar_pcs[2].token))
        self.assertEqual(1100000, str_token_to_int(images[0].token))

    def test_get_lidar_transform_matrix_for_lidarpc_token_from_db(self) -> None:
        """
        Test the get_sensor_transform_matrix_for_sensor_data_token_from_db query.
        """
        for sample_token in [0, 30, 49]:
            xform_mat = get_sensor_transform_matrix_for_sensor_data_token_from_db(self.db_file_name, self.sensor_source, int_to_str_token(sample_token))
            self.assertIsNotNone(xform_mat)
            self.assertEqual(xform_mat[0, 3], 0)

    def test_get_mission_goal_for_sensor_data_token_from_db(self) -> None:
        """
        Test the get_mission_goal_for_sensor_data_token_from_db query.
        """
        query_lidarpc_token = int_to_str_token(12)
        expected_ego_pose_x = 14
        expected_ego_pose_y = 15
        result = get_mission_goal_for_sensor_data_token_from_db(self.db_file_name, self.sensor_source, query_lidarpc_token)
        self.assertIsNotNone(result)
        self.assertEqual(expected_ego_pose_x, result.x)
        self.assertEqual(expected_ego_pose_y, result.y)

    def test_get_roadblock_ids_for_lidarpc_token_from_db(self) -> None:
        """
        Test the get_roadblock_ids_for_lidarpc_token_from_db query.
        """
        result = get_roadblock_ids_for_lidarpc_token_from_db(self.db_file_name, int_to_str_token(0))
        self.assertEqual(result, ['0', '1', '2'])

    def test_get_statese2_for_lidarpc_token_from_db(self) -> None:
        """
        Test the get_statese2_for_lidarpc_token_from_db query.
        """
        query_lidarpc_token = int_to_str_token(13)
        expected_ego_pose_x = 13
        expected_ego_pose_y = 14
        result = get_statese2_for_lidarpc_token_from_db(self.db_file_name, query_lidarpc_token)
        self.assertIsNotNone(result)
        self.assertEqual(expected_ego_pose_x, result.x)
        self.assertEqual(expected_ego_pose_y, result.y)

    def test_get_sampled_lidarpcs_from_db(self) -> None:
        """
        Test the get_sampled_lidarpcs_from_db query.
        """
        test_cases = [{'initial_token': 5, 'sample_indexes': [0, 1, 2], 'future': True, 'expected_return_tokens': [5, 6, 7]}, {'initial_token': 5, 'sample_indexes': [0, 1, 2], 'future': False, 'expected_return_tokens': [3, 4, 5]}, {'initial_token': 7, 'sample_indexes': [0, 3, 12], 'future': False, 'expected_return_tokens': [4, 7]}, {'initial_token': 0, 'sample_indexes': [1000], 'future': True, 'expected_return_tokens': []}]
        for test_case in test_cases:
            initial_token = int_to_str_token(test_case['initial_token'])
            expected_return_tokens = [int_to_str_token(v) for v in test_case['expected_return_tokens']]
            actual_returned_lidarpcs = list(get_sampled_lidarpcs_from_db(self.db_file_name, initial_token, self.sensor_source, test_case['sample_indexes'], test_case['future']))
            self.assertEqual(len(expected_return_tokens), len(actual_returned_lidarpcs))
            for i in range(len(expected_return_tokens)):
                self.assertEqual(expected_return_tokens[i], actual_returned_lidarpcs[i].token)

    def test_get_sampled_ego_states_from_db(self) -> None:
        """
        Test the get_sampled_ego_states_from_db query.
        """
        test_cases = [{'initial_token': 5, 'sample_indexes': [0, 1, 2], 'future': True, 'expected_row_indexes': [5, 6, 7]}, {'initial_token': 5, 'sample_indexes': [0, 1, 2], 'future': False, 'expected_row_indexes': [3, 4, 5]}, {'initial_token': 7, 'sample_indexes': [0, 3, 12], 'future': False, 'expected_row_indexes': [4, 7]}, {'initial_token': 0, 'sample_indexes': [1000], 'future': True, 'expected_row_indexes': []}]
        for test_case in test_cases:
            initial_token = int_to_str_token(test_case['initial_token'])
            expected_row_indexes = test_case['expected_row_indexes']
            actual_returned_ego_states = list(get_sampled_ego_states_from_db(self.db_file_name, initial_token, self.sensor_source, test_case['sample_indexes'], test_case['future']))
            self.assertEqual(len(expected_row_indexes), len(actual_returned_ego_states))
            for i in range(len(expected_row_indexes)):
                self.assertEqual(expected_row_indexes[i] * 1000000.0, actual_returned_ego_states[i].time_point.time_us)

    def test_get_ego_state_for_lidarpc_token_from_db(self) -> None:
        """
        Test the get_ego_state_for_lidarpc_token_from_db query.
        """
        for sample_token in [0, 30, 49]:
            query_token = int_to_str_token(sample_token)
            returned_pose = get_ego_state_for_lidarpc_token_from_db(self.db_file_name, query_token)
            self.assertEqual(sample_token * 1000000.0, returned_pose.time_point.time_us)

    def test_get_traffic_light_status_for_lidarpc_token_from_db(self) -> None:
        """
        Test the get_traffic_light_status_for_lidarpc_token_from_db query.
        """
        for sample_token in [0, 30, 49]:
            query_token = int_to_str_token(sample_token)
            traffic_light_statuses = list(get_traffic_light_status_for_lidarpc_token_from_db(self.db_file_name, query_token))
            self.assertEqual(5, len(traffic_light_statuses))
            for tl_status in traffic_light_statuses:
                self.assertEqual(sample_token * 1000000.0, tl_status.timestamp)

    def test_get_tracked_objects_for_lidarpc_token_from_db(self) -> None:
        """
        Test the get_tracked_objects_for_token_from_db query.
        """
        for sample_token in [0, 30, 49]:
            query_token = int_to_str_token(sample_token)
            tracked_objects = list(get_tracked_objects_for_lidarpc_token_from_db(self.db_file_name, query_token))
            self.assertEqual(5, len(tracked_objects))
            agent_count = 0
            static_object_count = 0
            track_token_base_id = 600000
            token_base_id = 500000
            token_sample_step = 10000
            for idx, tracked_object in enumerate(tracked_objects):
                expected_track_token = track_token_base_id + idx
                expected_token = token_base_id + token_sample_step * sample_token + idx
                self.assertEqual(int_to_str_token(expected_track_token), tracked_object.track_token)
                self.assertEqual(int_to_str_token(expected_token), tracked_object.token)
                if isinstance(tracked_object, Agent):
                    agent_count += 1
                    self.assertEqual(TrackedObjectType.VEHICLE, tracked_object.tracked_object_type)
                    self.assertEqual(0, len(tracked_object.predictions))
                elif isinstance(tracked_object, StaticObject):
                    static_object_count += 1
                    self.assertEqual(TrackedObjectType.CZONE_SIGN, tracked_object.tracked_object_type)
                else:
                    raise ValueError(f'Unexpected type: {type(tracked_object)}')
            self.assertEqual(3, agent_count)
            self.assertEqual(2, static_object_count)

    def test_get_tracked_objects_within_time_interval_from_db(self) -> None:
        """
        Test the get_tracked_objects_within_time_interval_from_db query.
        """
        expected_num_windows = {0: 3, 30: 5, 48: 4}
        expected_backward_offset = {0: 0, 30: -2, 48: -2}
        for sample_token in expected_num_windows.keys():
            start_timestamp = int(1000000.0 * (sample_token - 2))
            end_timestamp = int(1000000.0 * (sample_token + 2))
            tracked_objects = list(get_tracked_objects_within_time_interval_from_db(self.db_file_name, start_timestamp, end_timestamp, filter_track_tokens=None))
            expected_num_tokens = expected_num_windows[sample_token] * 5
            self.assertEqual(expected_num_tokens, len(tracked_objects))
            agent_count = 0
            static_object_count = 0
            track_token_base_id = 600000
            token_base_id = 500000
            token_sample_step = 10000
            for idx, tracked_object in enumerate(tracked_objects):
                expected_track_token = track_token_base_id + idx % 5
                expected_token = token_base_id + token_sample_step * (sample_token + expected_backward_offset[sample_token] + math.floor(idx / 5)) + idx % 5
                self.assertEqual(int_to_str_token(expected_track_token), tracked_object.track_token)
                self.assertEqual(int_to_str_token(expected_token), tracked_object.token)
                if isinstance(tracked_object, Agent):
                    agent_count += 1
                    self.assertEqual(TrackedObjectType.VEHICLE, tracked_object.tracked_object_type)
                    self.assertEqual(0, len(tracked_object.predictions))
                elif isinstance(tracked_object, StaticObject):
                    static_object_count += 1
                    self.assertEqual(TrackedObjectType.CZONE_SIGN, tracked_object.tracked_object_type)
                else:
                    raise ValueError(f'Unexpected type: {type(tracked_object)}')
            self.assertEqual(3 * expected_num_windows[sample_token], agent_count)
            self.assertEqual(2 * expected_num_windows[sample_token], static_object_count)

    def test_get_future_waypoints_for_agents_from_db(self) -> None:
        """
        Test the get_future_waypoints_for_agents_from_db query.
        """
        track_tokens = [600000, 600001, 600002]
        start_timestamp = 0
        end_timestamp = int(20 * 1000000.0 - 1)
        query_output: Dict[str, List[Waypoint]] = {}
        for token, waypoint in get_future_waypoints_for_agents_from_db(self.db_file_name, (int_to_str_token(t) for t in track_tokens), start_timestamp, end_timestamp):
            if token not in query_output:
                query_output[token] = []
            query_output[token].append(waypoint)
        expected_keys = ['{:08d}'.format(t) for t in track_tokens]
        self.assertEqual(len(expected_keys), len(query_output))
        for expected_key in expected_keys:
            self.assertTrue(expected_key in query_output)
            collected_waypoints = query_output[expected_key]
            self.assertEqual(20, len(collected_waypoints))
            for i in range(0, len(collected_waypoints), 1):
                self.assertEqual(i * 1000000.0, collected_waypoints[i].time_point.time_us)

    def test_get_scenarios_from_db(self) -> None:
        """
        Test the get_scenarios_from_db_query.
        """
        no_filter_output: List[int] = []
        for row in get_scenarios_from_db(self.db_file_name, filter_tokens=None, filter_types=None, filter_map_names=None, include_invalid_mission_goals=False, include_cameras=False):
            no_filter_output.append(str_token_to_int(row['token'].hex()))
        self.assertEqual(list(range(10, 40, 1)), no_filter_output)
        filter_tokens = [int_to_str_token(v) for v in [15, 30]]
        tokens_filter_output: List[int] = []
        for row in get_scenarios_from_db(self.db_file_name, filter_tokens=filter_tokens, filter_types=None, filter_map_names=None, include_invalid_mission_goals=False, include_cameras=False):
            tokens_filter_output.append(row['token'].hex())
        self.assertEqual(filter_tokens, tokens_filter_output)
        filter_scenarios = ['first_tag']
        extracted_rows: List[Tuple[int, str]] = []
        for row in get_scenarios_from_db(self.db_file_name, filter_tokens=None, filter_types=filter_scenarios, filter_map_names=None, include_invalid_mission_goals=False, include_cameras=False):
            extracted_rows.append((str_token_to_int(row['token'].hex()), row['scenario_type']))
        self.assertEqual(2, len(extracted_rows))
        self.assertEqual(25, extracted_rows[0][0])
        self.assertEqual('first_tag', extracted_rows[0][1])
        self.assertEqual(30, extracted_rows[1][0])
        self.assertEqual('first_tag', extracted_rows[1][1])
        filter_scenarios = ['second_tag']
        extracted_rows = []
        for row in get_scenarios_from_db(self.db_file_name, filter_tokens=None, filter_types=filter_scenarios, filter_map_names=None, include_invalid_mission_goals=False, include_cameras=False):
            extracted_rows.append((str_token_to_int(row['token'].hex()), row['scenario_type']))
        self.assertEqual(2, len(extracted_rows))
        self.assertEqual(30, extracted_rows[0][0])
        self.assertEqual('second_tag', extracted_rows[0][1])
        self.assertEqual(35, extracted_rows[1][0])
        self.assertEqual('second_tag', extracted_rows[1][1])
        filter_maps = ['map_version']
        row_cnt = sum((1 for _ in get_scenarios_from_db(self.db_file_name, filter_tokens=None, filter_types=None, filter_map_names=filter_maps, include_invalid_mission_goals=False, include_cameras=False)))
        self.assertLess(0, row_cnt)
        filter_maps = ['map_that_does_not_exist']
        row_cnt = sum((1 for _ in get_scenarios_from_db(self.db_file_name, filter_tokens=None, filter_types=None, filter_map_names=filter_maps, include_invalid_mission_goals=False, include_cameras=False)))
        self.assertEqual(0, row_cnt)
        row_cnt = sum((1 for _ in get_scenarios_from_db(self.db_file_name, filter_tokens=None, filter_types=None, filter_map_names=None, include_invalid_mission_goals=False, include_cameras=True)))
        self.assertEqual(15, row_cnt)
        row_cnt = sum((1 for _ in get_scenarios_from_db(self.db_file_name, filter_tokens=[int_to_str_token(25)], filter_types=['first_tag'], filter_map_names=['map_version'], include_invalid_mission_goals=False, include_cameras=False)))
        self.assertEqual(1, row_cnt)

    def test_get_lidarpc_tokens_with_scenario_tag_from_db(self) -> None:
        """
        Test the get_lidarpc_tokens_with_scenario_tag_from_db query.
        """
        tuples = list(get_lidarpc_tokens_with_scenario_tag_from_db(self.db_file_name))
        self.assertEqual(4, len(tuples))
        expected_tuples = [('first_tag', int_to_str_token(25)), ('first_tag', int_to_str_token(30)), ('second_tag', int_to_str_token(30)), ('second_tag', int_to_str_token(35))]
        for tup in tuples:
            self.assertTrue(tup in expected_tuples)

    def test_get_sensor_token(self) -> None:
        """Test the get_lidarpc_token_from_index query."""
        retrieved_token = get_sensor_token(self.db_file_name, 'lidar', 'channel')
        self.assertEqual(700000, str_token_to_int(retrieved_token))
        with self.assertRaisesRegex(RuntimeError, 'Channel missing_channel not found in table lidar!'):
            self.assertIsNone(get_sensor_token(self.db_file_name, 'lidar', 'missing_channel'))

    def test_get_images_from_lidar_tokens(self) -> None:
        """Test the get_images_from_lidar_tokens query."""
        token = int_to_str_token(20)
        retrieved_images = list(get_images_from_lidar_tokens(self.db_file_name, [token], ['camera_0', 'camera_1'], 50000, 50000))
        self.assertEqual(2, len(retrieved_images))
        self.assertEqual(1100020, str_token_to_int(retrieved_images[0].token))
        self.assertEqual(1100070, str_token_to_int(retrieved_images[1].token))
        self.assertEqual('camera_0', retrieved_images[0].channel)
        self.assertEqual('camera_1', retrieved_images[1].channel)

    def test_get_cameras(self) -> None:
        """Test the get_cameras query."""
        retrieved_cameras = list(get_cameras(self.db_file_name, ['camera_0', 'camera_1']))
        self.assertEqual(2, len(retrieved_cameras))
        self.assertEqual(1000000, str_token_to_int(retrieved_cameras[0].token))
        self.assertEqual(1000001, str_token_to_int(retrieved_cameras[1].token))
        self.assertEqual('camera_0', retrieved_cameras[0].channel)
        self.assertEqual('camera_1', retrieved_cameras[1].channel)
        retrieved_cameras = list(get_cameras(self.db_file_name, ['camera_1']))
        self.assertEqual(1, len(retrieved_cameras))
        self.assertEqual(1000001, str_token_to_int(retrieved_cameras[0].token))
        self.assertEqual('camera_1', retrieved_cameras[0].channel)

def test_get_sensor_token(self) -> None:
    """Test the get_lidarpc_token_from_index query."""
    retrieved_token = get_sensor_token(self.db_file_name, 'lidar', 'channel')
    self.assertEqual(700000, str_token_to_int(retrieved_token))
    with self.assertRaisesRegex(RuntimeError, 'Channel missing_channel not found in table lidar!'):
        self.assertIsNone(get_sensor_token(self.db_file_name, 'lidar', 'missing_channel'))

class ValidationInterface:
    """
    A dummy interface class to use for testing.
    """

    def base_method(self, x: int) -> int:
        """
        Some method derived classes don't need to implement.
        :param x: The input.
        :return: The output.
        """
        return 1

    @abc.abstractmethod
    def implement_me(self, y: int) -> float:
        """
        Some method derived classes need to implement.
        :param y: The input.
        :return: The output.
        """
        raise NotImplementedError()

    def _private_method(self, a: float) -> float:
        """
        A private method.
        :param a: The input.
        :return: The output.
        """
        return a + 1.0

@abc.abstractmethod
def implement_me(self, y: int) -> float:
    """
        Some method derived classes need to implement.
        :param y: The input.
        :return: The output.
        """
    raise NotImplementedError()

class SecondValidationInterface:
    """
    Another dummy interface class to use for testing
    """

    @abc.abstractmethod
    def implement_me_2(self, q: float) -> str:
        """
        A method the derived class needs to implement.
        :param q: The input.
        :return: The output.
        """
        raise NotImplementedError()

@abc.abstractmethod
def implement_me_2(self, q: float) -> str:
    """
        A method the derived class needs to implement.
        :param q: The input.
        :return: The output.
        """
    raise NotImplementedError()

class TestInterfaceValidation(unittest.TestCase):
    """
    Tests that the interface_validation utils works properly.
    """

    def test_assert_class_properly_implements_interface_correct(self) -> None:
        """
        Tests that the validation passes when a class properly implements an interface.
        """
        assert_class_properly_implements_interface(ValidationInterface, CorrectConcrete)

    def test_assert_class_properly_implements_interface_swapped_args(self) -> None:
        """
        Tests that the validation fails if the args are swapped.
        """
        with self.assertRaisesRegex(TypeError, 'is not a subclass'):
            assert_class_properly_implements_interface(CorrectConcrete, ValidationInterface)

    def test_assert_class_properly_implements_interface_incorrect_method(self) -> None:
        """
        Tests that the validation fails when a class improperly implements an interface method.
        """
        with self.assertRaisesRegex(TypeError, 'Types in function signature.*do not match'):
            assert_class_properly_implements_interface(ValidationInterface, IncorrectConcrete)

    def test_assert_class_properly_implements_interface_missing_method(self) -> None:
        """
        Tests that the validation fails when a class missing the interface method is passed.
        """
        with self.assertRaisesRegex(TypeError, 'methods.*missing'):
            assert_class_properly_implements_interface(ValidationInterface, ConcreteMissingInterfaceMethod)

    def test_assert_class_properly_implements_interface_no_hierarchy(self) -> None:
        """
        Tests that the validation fails when the concrete does not derive from the interface.
        """
        with self.assertRaisesRegex(TypeError, 'is not a subclass'):
            assert_class_properly_implements_interface(ValidationInterface, ConcreteDoesNotDerive)

    def test_assert_class_properly_implements_interface_multiple_inheritance(self) -> None:
        """
        Tests that the validation passes with the multiple inheritance use case.
        """
        assert_class_properly_implements_interface(ValidationInterface, CorrectConcreteMulti)
        assert_class_properly_implements_interface(SecondValidationInterface, CorrectConcreteMulti)

def test_assert_class_properly_implements_interface_correct(self) -> None:
    """
        Tests that the validation passes when a class properly implements an interface.
        """
    assert_class_properly_implements_interface(ValidationInterface, CorrectConcrete)

def test_assert_class_properly_implements_interface_swapped_args(self) -> None:
    """
        Tests that the validation fails if the args are swapped.
        """
    with self.assertRaisesRegex(TypeError, 'is not a subclass'):
        assert_class_properly_implements_interface(CorrectConcrete, ValidationInterface)

def test_assert_class_properly_implements_interface_incorrect_method(self) -> None:
    """
        Tests that the validation fails when a class improperly implements an interface method.
        """
    with self.assertRaisesRegex(TypeError, 'Types in function signature.*do not match'):
        assert_class_properly_implements_interface(ValidationInterface, IncorrectConcrete)

def test_assert_class_properly_implements_interface_missing_method(self) -> None:
    """
        Tests that the validation fails when a class missing the interface method is passed.
        """
    with self.assertRaisesRegex(TypeError, 'methods.*missing'):
        assert_class_properly_implements_interface(ValidationInterface, ConcreteMissingInterfaceMethod)

def test_assert_class_properly_implements_interface_no_hierarchy(self) -> None:
    """
        Tests that the validation fails when the concrete does not derive from the interface.
        """
    with self.assertRaisesRegex(TypeError, 'is not a subclass'):
        assert_class_properly_implements_interface(ValidationInterface, ConcreteDoesNotDerive)

def test_assert_class_properly_implements_interface_multiple_inheritance(self) -> None:
    """
        Tests that the validation passes with the multiple inheritance use case.
        """
    assert_class_properly_implements_interface(ValidationInterface, CorrectConcreteMulti)
    assert_class_properly_implements_interface(SecondValidationInterface, CorrectConcreteMulti)

@dataclass
class TrafficLightStatusData:
    """Traffic light status."""
    status: TrafficLightStatusType
    lane_connector_id: int
    timestamp: int

    def serialize(self) -> Dict[str, Any]:
        """Serialize traffic light status."""
        return {'status': self.status.serialize(), 'lane_connector_id': self.lane_connector_id, 'timestamp': self.timestamp}

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> TrafficLightStatusData:
        """Deserialize a dict of data to this class."""
        return TrafficLightStatusData(status=TrafficLightStatusType.deserialize(data['status']), lane_connector_id=data['lane_connector_id'], timestamp=data['timestamp'])

@classmethod
def deserialize(cls, data: Dict[str, Any]) -> TrafficLightStatusData:
    """Deserialize a dict of data to this class."""
    return TrafficLightStatusData(status=TrafficLightStatusType.deserialize(data['status']), lane_connector_id=data['lane_connector_id'], timestamp=data['timestamp'])

class TimeDuration:
    """Class representing a time delta, with a microsecond resolution."""
    __slots__ = '_time_us'

    def __init__(self, *, time_us: int, _direct: bool=True) -> None:
        """Constructor, should not be called directly. Raises if the keyword parameter _direct is not set to false."""
        if _direct:
            raise RuntimeError("Don't initialize this class directly, use one of the constructors instead!")
        self._time_us = time_us

    @classmethod
    def from_us(cls, t_us: int) -> TimeDuration:
        """
        Constructs a TimeDuration from a value in microseconds.
        :param t_us: Time in microseconds.
        :return: TimeDuration.
        """
        assert isinstance(t_us, int), 'Microseconds must be an integer!'
        return cls(time_us=t_us, _direct=False)

    @classmethod
    def from_ms(cls, t_ms: float) -> TimeDuration:
        """
        Constructs a TimeDuration from a value in milliseconds.
        :param t_ms: Time in milliseconds.
        :return: TimeDuration.
        """
        return cls(time_us=int(t_ms * int(1000.0)), _direct=False)

    @classmethod
    def from_s(cls, t_s: float) -> TimeDuration:
        """
        Constructs a TimeDuration from a value in seconds.
        :param t_s: Time in seconds.
        :return: TimeDuration.
        """
        return cls(time_us=int(t_s * int(1000000.0)), _direct=False)

    @property
    def time_us(self) -> int:
        """
        :return: TimeDuration in microseconds.
        """
        return self._time_us

    @property
    def time_ms(self) -> float:
        """
        :return: TimeDuration in milliseconds.
        """
        return self._time_us / 1000.0

    @property
    def time_s(self) -> float:
        """
        :return: TimeDuration in seconds.
        """
        return self._time_us / 1000000.0

    def __add__(self, other: object) -> TimeDuration:
        """
        Adds a time duration to a time duration.
        :param other: time duration.
        :return: self + other if other is a TimeDuration.
        """
        if isinstance(other, TimeDuration):
            return TimeDuration.from_us(self.time_us + other.time_us)
        return NotImplemented

    def __sub__(self, other: object) -> TimeDuration:
        """
        Subtract a time duration from a time duration.
        :param other: time duration.
        :return: self - other if other is a TimeDuration.
        """
        if isinstance(other, TimeDuration):
            return TimeDuration.from_us(self.time_us - other.time_us)
        return NotImplemented

    def __mul__(self, other: object) -> TimeDuration:
        """
        Multiply a time duration by a scalar value.
        :param other: value to multiply.
        :return: self * other if other is a scalar.
        """
        if isinstance(other, (int, float)):
            return TimeDuration.from_s(self.time_s * other)
        return NotImplemented

    def __rmul__(self, other: object) -> TimeDuration:
        """
        Multiply a time duration by a scalar value.
        :param other: value to multiply.
        :return: self * other if other is a scalar.
        """
        if isinstance(other, (int, float)):
            return self * other
        return NotImplemented

    def __truediv__(self, other: object) -> TimeDuration:
        """
        Divides a time duration by a scalar value.
        :param other: value to divide for.
        :return: self / other if other is a scalar.
        """
        if isinstance(other, (int, float)):
            return TimeDuration.from_s(self.time_s / other)
        return NotImplemented

    def __floordiv__(self, other: object) -> TimeDuration:
        """
        Floor divides a time duration by a scalar value.
        :param other: value to divide for.
        :return: self // other if other is a scalar.
        """
        if isinstance(other, (int, float)):
            return TimeDuration.from_s(self.time_s // other)
        return NotImplemented

    def __gt__(self, other: TimeDuration) -> bool:
        """
        Self is greater than other.
        :param other: TimeDuration.
        :return: True if self > other, False otherwise.
        """
        if isinstance(other, TimeDuration):
            return self.time_us > other.time_us
        return NotImplemented

    def __ge__(self, other: object) -> bool:
        """
        Self is greater or equal than other.
        :param other: TimeDuration.
        :return: True if self >= other, False otherwise.
        """
        if isinstance(other, TimeDuration):
            return self.time_us >= other.time_us
        return NotImplemented

    def __lt__(self, other: TimeDuration) -> bool:
        """
        Self is less than other.
        :param other: TimeDuration.
        :return: True if self < other, False otherwise.
        """
        if isinstance(other, TimeDuration):
            return self.time_us < other.time_us
        return NotImplemented

    def __le__(self, other: TimeDuration) -> bool:
        """
        Self is less or equal than other.
        :param other: TimeDuration.
        :return: True if self <= other, False otherwise.
        """
        if isinstance(other, TimeDuration):
            return self.time_us <= other.time_us
        return NotImplemented

    def __eq__(self, other: object) -> bool:
        """
        Self is equal to other.
        :param other: TimeDuration.
        :return: True if self == other, False otherwise.
        """
        if not isinstance(other, TimeDuration):
            return NotImplemented
        return self.time_us == other.time_us

    def __hash__(self) -> int:
        """
        :return: hash for this object.
        """
        return hash(self.time_us)

    def __repr__(self) -> str:
        """
        :return: String representation.
        """
        return 'TimeDuration({}s)'.format(self.time_s)

@classmethod
def from_us(cls, t_us: int) -> TimeDuration:
    """
        Constructs a TimeDuration from a value in microseconds.
        :param t_us: Time in microseconds.
        :return: TimeDuration.
        """
    assert isinstance(t_us, int), 'Microseconds must be an integer!'
    return cls(time_us=t_us, _direct=False)

@classmethod
def from_ms(cls, t_ms: float) -> TimeDuration:
    """
        Constructs a TimeDuration from a value in milliseconds.
        :param t_ms: Time in milliseconds.
        :return: TimeDuration.
        """
    return cls(time_us=int(t_ms * int(1000.0)), _direct=False)

@classmethod
def from_s(cls, t_s: float) -> TimeDuration:
    """
        Constructs a TimeDuration from a value in seconds.
        :param t_s: Time in seconds.
        :return: TimeDuration.
        """
    return cls(time_us=int(t_s * int(1000000.0)), _direct=False)

class CarFootprint(OrientedBox):
    """Class that represent the car semantically, with geometry and relevant point of interest."""

    def __init__(self, center: StateSE2, vehicle_parameters: VehicleParameters):
        """
        :param center: The pose of ego in the specified frame
        :param vehicle_parameters: The parameters of ego
        """
        super().__init__(center=center, width=vehicle_parameters.width, length=vehicle_parameters.length, height=vehicle_parameters.height)
        self._vehicle_parameters = vehicle_parameters

    @property
    def vehicle_parameters(self) -> VehicleParameters:
        """
        :return: vehicle parameters corresponding to the footprint
        """
        return self._vehicle_parameters

    def get_point_of_interest(self, point_of_interest: OrientedBoxPointType) -> Point2D:
        """
        Getter for the point of interest of ego.
        :param point_of_interest: The query point of the car
        :return: The position of the query point.
        """
        return self.corner(point_of_interest)

    @property
    def oriented_box(self) -> OrientedBox:
        """
        Getter for Ego's OrientedBox
        :return: OrientedBox of Ego
        """
        return self

    @property
    def rear_axle_to_center_dist(self) -> float:
        """
        Getter for the distance from the rear axle to the center of mass of Ego.
        :return: Distance from rear axle to COG
        """
        return float(self._vehicle_parameters.rear_axle_to_center)

    @cached_property
    def rear_axle(self) -> StateSE2:
        """
        Getter for the pose at the middle of the rear axle
        :return: SE2 Pose of the rear axle.
        """
        return translate_longitudinally(self.oriented_box.center, -self.rear_axle_to_center_dist)

    @classmethod
    def build_from_rear_axle(cls, rear_axle_pose: StateSE2, vehicle_parameters: VehicleParameters) -> CarFootprint:
        """
        Construct Car Footprint from rear axle position
        :param rear_axle_pose: SE2 position of rear axle
        :param vehicle_parameters: parameters of vehicle
        :return: CarFootprint
        """
        center = translate_longitudinally(rear_axle_pose, vehicle_parameters.rear_axle_to_center)
        return cls(center=center, vehicle_parameters=vehicle_parameters)

    @classmethod
    def build_from_cog(cls, cog_pose: StateSE2, vehicle_parameters: VehicleParameters) -> CarFootprint:
        """
        Construct Car Footprint from COG position
        :param cog_pose: SE2 position of COG
        :param vehicle_parameters: parameters of vehicle
        :return: CarFootprint
        """
        cog_to_center = vehicle_parameters.rear_axle_to_center - vehicle_parameters.cog_position_from_rear_axle
        center = translate_longitudinally(cog_pose, cog_to_center)
        return cls(center=center, vehicle_parameters=vehicle_parameters)

    @classmethod
    def build_from_center(cls, center: StateSE2, vehicle_parameters: VehicleParameters) -> CarFootprint:
        """
        Construct Car Footprint from geometric center of vehicle
        :param center: SE2 position of geometric center of vehicle
        :param vehicle_parameters: parameters of vehicle
        :return: CarFootprint
        """
        return cls(center=center, vehicle_parameters=vehicle_parameters)

@cached_property
def rear_axle(self) -> StateSE2:
    """
        Getter for the pose at the middle of the rear axle
        :return: SE2 Pose of the rear axle.
        """
    return translate_longitudinally(self.oriented_box.center, -self.rear_axle_to_center_dist)

@classmethod
def build_from_rear_axle(cls, rear_axle_pose: StateSE2, vehicle_parameters: VehicleParameters) -> CarFootprint:
    """
        Construct Car Footprint from rear axle position
        :param rear_axle_pose: SE2 position of rear axle
        :param vehicle_parameters: parameters of vehicle
        :return: CarFootprint
        """
    center = translate_longitudinally(rear_axle_pose, vehicle_parameters.rear_axle_to_center)
    return cls(center=center, vehicle_parameters=vehicle_parameters)

@classmethod
def build_from_cog(cls, cog_pose: StateSE2, vehicle_parameters: VehicleParameters) -> CarFootprint:
    """
        Construct Car Footprint from COG position
        :param cog_pose: SE2 position of COG
        :param vehicle_parameters: parameters of vehicle
        :return: CarFootprint
        """
    cog_to_center = vehicle_parameters.rear_axle_to_center - vehicle_parameters.cog_position_from_rear_axle
    center = translate_longitudinally(cog_pose, cog_to_center)
    return cls(center=center, vehicle_parameters=vehicle_parameters)

@classmethod
def build_from_center(cls, center: StateSE2, vehicle_parameters: VehicleParameters) -> CarFootprint:
    """
        Construct Car Footprint from geometric center of vehicle
        :param center: SE2 position of geometric center of vehicle
        :param vehicle_parameters: parameters of vehicle
        :return: CarFootprint
        """
    return cls(center=center, vehicle_parameters=vehicle_parameters)

class OrientedBox:
    """Represents the physical space occupied by agents on the plane."""

    def __init__(self, center: StateSE2, length: float, width: float, height: float):
        """
        :param center: The pose of the geometrical center of the box
        :param length: The length of the OrientedBox
        :param width: The width of the OrientedBox
        :param height: The height of the OrientedBox
        """
        self._center = center
        self._length = length
        self._width = width
        self._height = height

    @property
    def dimensions(self) -> Dimension:
        """
        :return: Dimensions of this oriented box in meters
        """
        return Dimension(length=self.length, width=self.width, height=self.height)

    @lru_cache()
    def corner(self, point: OrientedBoxPointType) -> Point2D:
        """
        Extract a point of oriented box
        :param point: which point you want to query
        :return: Coordinates of a point on oriented box.
        """
        if point == OrientedBoxPointType.FRONT_LEFT:
            return translate_longitudinally_and_laterally(self.center, self.half_length, self.half_width).point
        elif point == OrientedBoxPointType.FRONT_RIGHT:
            return translate_longitudinally_and_laterally(self.center, self.half_length, -self.half_width).point
        elif point == OrientedBoxPointType.REAR_LEFT:
            return translate_longitudinally_and_laterally(self.center, -self.half_length, self.half_width).point
        elif point == OrientedBoxPointType.REAR_RIGHT:
            return translate_longitudinally_and_laterally(self.center, -self.half_length, -self.half_width).point
        elif point == OrientedBoxPointType.CENTER:
            return self._center.point
        elif point == OrientedBoxPointType.FRONT_BUMPER:
            return translate_longitudinally_and_laterally(self.center, self.half_length, 0.0).point
        elif point == OrientedBoxPointType.REAR_BUMPER:
            return translate_longitudinally_and_laterally(self.center, -self.half_length, 0.0).point
        elif point == OrientedBoxPointType.LEFT:
            return translate_longitudinally_and_laterally(self.center, 0, self.half_width).point
        elif point == OrientedBoxPointType.RIGHT:
            return translate_longitudinally_and_laterally(self.center, 0, -self.half_width).point
        else:
            raise RuntimeError(f'Unknown point: {point}!')

    def all_corners(self) -> List[Point2D]:
        """
        Return 4 corners of oriented box (FL, RL, RR, FR)
        :return: all corners of a oriented box in a list
        """
        return [self.corner(OrientedBoxPointType.FRONT_LEFT), self.corner(OrientedBoxPointType.REAR_LEFT), self.corner(OrientedBoxPointType.REAR_RIGHT), self.corner(OrientedBoxPointType.FRONT_RIGHT)]

    @property
    def width(self) -> float:
        """
        Returns the width of the OrientedBox
        :return: The width of the OrientedBox
        """
        return self._width

    @property
    def half_width(self) -> float:
        """
        Returns the half width of the OrientedBox
        :return: The half width of the OrientedBox
        """
        return self._width / 2.0

    @property
    def length(self) -> float:
        """
        Returns the length of the OrientedBox
        :return: The length of the OrientedBox
        """
        return self._length

    @property
    def half_length(self) -> float:
        """
        Returns the half length of the OrientedBox
        :return: The half length of the OrientedBox
        """
        return self._length / 2.0

    @property
    def height(self) -> float:
        """
        Returns the height of the OrientedBox
        :return: The height of the OrientedBox
        """
        return self._height

    @property
    def half_height(self) -> float:
        """
        Returns the half height of the OrientedBox
        :return: The half height of the OrientedBox
        """
        return self._height / 2.0

    @property
    def center(self) -> StateSE2:
        """
        Returns the pose of the center of the OrientedBox
        :return: The pose of the center
        """
        return self._center

    @cached_property
    def geometry(self) -> Polygon:
        """
        Returns the Polygon describing the OrientedBox, if not done yet it will build it lazily.
        :return: The Polygon of the OrientedBox
        """
        corners = [tuple(corner) for corner in self.all_corners()]
        return Polygon(corners)

    def __hash__(self) -> int:
        """
        :return: hash for this object
        """
        return hash((self.center, self.width, self.height, self.length))

    def __eq__(self, other: object) -> bool:
        """
        Compare two oriented boxes
        :param other: object
        :return: true if other and self is equal
        """
        if not isinstance(other, OrientedBox):
            return NotImplemented
        return math.isclose(self.width, other.width) and math.isclose(self.height, other.height) and math.isclose(self.length, other.length) and (self.center == other.center)

    @classmethod
    def from_new_pose(cls, box: OrientedBox, pose: StateSE2) -> OrientedBox:
        """
        Initializer that create the same oriented box in a different pose.
        :param box: A sample box
        :param pose: The new pose
        :return: A new OrientedBox
        """
        return cls(pose, box.length, box.width, box.height)

@classmethod
def from_new_pose(cls, box: OrientedBox, pose: StateSE2) -> OrientedBox:
    """
        Initializer that create the same oriented box in a different pose.
        :param box: A sample box
        :param pose: The new pose
        :return: A new OrientedBox
        """
    return cls(pose, box.length, box.width, box.height)

class EgoState(InterpolatableState):
    """Represent the current state of ego, along with its dynamic attributes."""

    def __init__(self, car_footprint: CarFootprint, dynamic_car_state: DynamicCarState, tire_steering_angle: float, is_in_auto_mode: bool, time_point: TimePoint):
        """
        :param car_footprint: The CarFootprint of Ego
        :param dynamic_car_state: The current dynamical state of ego
        :param tire_steering_angle: The current steering angle of the tires
        :param is_in_auto_mode: If the state refers to car in autonomous mode
        :param time_point: Time stamp of the state
        """
        self._car_footprint = car_footprint
        self._tire_steering_angle = tire_steering_angle
        self._is_in_auto_mode = is_in_auto_mode
        self._time_point = time_point
        self._dynamic_car_state = dynamic_car_state

    @cached_property
    def waypoint(self) -> Waypoint:
        """
        :return: waypoint corresponding to this ego state
        """
        return Waypoint(time_point=self.time_point, oriented_box=self.car_footprint, velocity=self.dynamic_car_state.rear_axle_velocity_2d)

    @staticmethod
    def deserialize(vector: List[Union[int, float]], vehicle: VehicleParameters) -> EgoState:
        """
        Deserialize object, ordering kept for backward compatibility
        :param vector: List of variables for deserialization
        :param vehicle: Vehicle parameters
        """
        if len(vector) != 9:
            raise RuntimeError(f'Expected a vector of size 9, got {len(vector)}')
        return EgoState.build_from_rear_axle(rear_axle_pose=StateSE2(vector[1], vector[2], vector[3]), rear_axle_velocity_2d=StateVector2D(vector[4], vector[5]), rear_axle_acceleration_2d=StateVector2D(vector[6], vector[7]), tire_steering_angle=vector[8], time_point=TimePoint(int(vector[0])), vehicle_parameters=vehicle)

    def __iter__(self) -> Iterable[Union[int, float]]:
        """Iterable over ego parameters"""
        return iter((self.time_us, self.rear_axle.x, self.rear_axle.y, self.rear_axle.heading, self.dynamic_car_state.rear_axle_velocity_2d.x, self.dynamic_car_state.rear_axle_velocity_2d.y, self.dynamic_car_state.rear_axle_acceleration_2d.x, self.dynamic_car_state.rear_axle_acceleration_2d.y, self.tire_steering_angle))

    def to_split_state(self) -> SplitState:
        """Inherited, see superclass."""
        linear_states = [self.time_us, self.rear_axle.x, self.rear_axle.y, self.dynamic_car_state.rear_axle_velocity_2d.x, self.dynamic_car_state.rear_axle_velocity_2d.y, self.dynamic_car_state.rear_axle_acceleration_2d.x, self.dynamic_car_state.rear_axle_acceleration_2d.y, self.tire_steering_angle]
        angular_states = [self.rear_axle.heading]
        fixed_state = [self.car_footprint.vehicle_parameters]
        return SplitState(linear_states, angular_states, fixed_state)

    @staticmethod
    def from_split_state(split_state: SplitState) -> EgoState:
        """Inherited, see superclass."""
        if len(split_state) != 10:
            raise RuntimeError(f'Expected a variable state vector of size 10, got {len(split_state)}')
        return EgoState.build_from_rear_axle(rear_axle_pose=StateSE2(split_state.linear_states[1], split_state.linear_states[2], split_state.angular_states[0]), rear_axle_velocity_2d=StateVector2D(split_state.linear_states[3], split_state.linear_states[4]), rear_axle_acceleration_2d=StateVector2D(split_state.linear_states[5], split_state.linear_states[6]), tire_steering_angle=split_state.linear_states[7], time_point=TimePoint(int(split_state.linear_states[0])), vehicle_parameters=split_state.fixed_states[0])

    @property
    def is_in_auto_mode(self) -> bool:
        """
        :return: True if ego is in auto mode, False otherwise.
        """
        return self._is_in_auto_mode

    @property
    def car_footprint(self) -> CarFootprint:
        """
        Getter for Ego's Car footprint
        :return: Ego's car footprint
        """
        return self._car_footprint

    @property
    def tire_steering_angle(self) -> float:
        """
        Getter for Ego's tire steering angle
        :return: Ego's tire steering angle
        """
        return self._tire_steering_angle

    @property
    def center(self) -> StateSE2:
        """
        Getter for Ego's center pose (center of mass)
        :return: Ego's center pose
        """
        return self._car_footprint.oriented_box.center

    @property
    def rear_axle(self) -> StateSE2:
        """
        Getter for Ego's rear axle pose (middle of the rear axle)
        :return: Ego's rear axle pose
        """
        return self.car_footprint.rear_axle

    @property
    def time_point(self) -> TimePoint:
        """
        Time stamp of the EgoState
        :return: EgoState time stamp
        """
        return self._time_point

    @property
    def time_us(self) -> int:
        """
        Time in micro seconds
        :return: [us].
        """
        return int(self.time_point.time_us)

    @property
    def time_seconds(self) -> float:
        """
        Time in seconds
        :return: [s]
        """
        return float(self.time_us * 1e-06)

    @property
    def dynamic_car_state(self) -> DynamicCarState:
        """
        Getter for the dynamic car state of Ego.
        :return: The dynamic car state
        """
        return self._dynamic_car_state

    @property
    def scene_object_metadata(self) -> SceneObjectMetadata:
        """
        :return: create scene object metadata
        """
        return SceneObjectMetadata(token='ego', track_token='ego', track_id=-1, timestamp_us=self.time_us)

    @cached_property
    def agent(self) -> AgentState:
        """
        Casts the EgoState to an Agent object.
        :return: An Agent object with the parameters of EgoState
        """
        return AgentState(metadata=self.scene_object_metadata, tracked_object_type=TrackedObjectType.EGO, oriented_box=self.car_footprint.oriented_box, velocity=self.dynamic_car_state.center_velocity_2d)

    @classmethod
    def build_from_rear_axle(cls, rear_axle_pose: StateSE2, rear_axle_velocity_2d: StateVector2D, rear_axle_acceleration_2d: StateVector2D, tire_steering_angle: float, time_point: TimePoint, vehicle_parameters: VehicleParameters, is_in_auto_mode: bool=True, angular_vel: float=0.0, angular_accel: float=0.0, tire_steering_rate: float=0.0) -> EgoState:
        """
        Initializer using raw parameters, assumes that the reference frame is CAR_POINT.REAR_AXLE
        :param rear_axle_pose: Pose of ego's rear axle
        :param rear_axle_velocity_2d: Vectorial velocity of Ego's rear axle
        :param rear_axle_acceleration_2d: Vectorial acceleration of Ego's rear axle
        :param angular_vel: Angular velocity of Ego
        :param angular_accel: Angular acceleration of Ego,
        :param tire_steering_angle: Angle of the tires
        :param is_in_auto_mode: True if ego is in auto mode, false otherwise
        :param time_point: Timestamp of the ego state
        :param vehicle_parameters: Vehicle parameters
        :param tire_steering_rate: Steering rate of tires [rad/s]
        :return: The initialized EgoState
        """
        car_footprint = CarFootprint.build_from_rear_axle(rear_axle_pose=rear_axle_pose, vehicle_parameters=vehicle_parameters)
        dynamic_ego_state = DynamicCarState.build_from_rear_axle(rear_axle_to_center_dist=car_footprint.rear_axle_to_center_dist, rear_axle_velocity_2d=rear_axle_velocity_2d, rear_axle_acceleration_2d=rear_axle_acceleration_2d, angular_velocity=angular_vel, angular_acceleration=angular_accel, tire_steering_rate=tire_steering_rate)
        return cls(car_footprint=car_footprint, dynamic_car_state=dynamic_ego_state, tire_steering_angle=tire_steering_angle, time_point=time_point, is_in_auto_mode=is_in_auto_mode)

    @classmethod
    def build_from_center(cls, center: StateSE2, center_velocity_2d: StateVector2D, center_acceleration_2d: StateVector2D, tire_steering_angle: float, time_point: TimePoint, vehicle_parameters: VehicleParameters, is_in_auto_mode: bool=True, angular_vel: float=0.0, angular_accel: float=0.0) -> EgoState:
        """
        Initializer using raw parameters, assumes that the reference frame is center frame
        :param center: Pose of ego center
        :param center_velocity_2d: Vectorial velocity of Ego's center
        :param center_acceleration_2d: Vectorial acceleration of Ego's center
        :param tire_steering_angle: Angle of the tires
        :param time_point: Timestamp of the ego state
        :param vehicle_parameters: Vehicle parameters
        :param is_in_auto_mode: True if ego is in auto mode, false otherwise, defaults to True
        :param angular_vel: Angular velocity of Ego, defaults to 0.0
        :param angular_accel: Angular acceleration of Ego, defaults to 0.0
        :return: The initialized EgoState
        """
        car_footprint = CarFootprint.build_from_center(center, vehicle_parameters)
        rear_axle_to_center_dist = car_footprint.rear_axle_to_center_dist
        displacement = StateVector2D(-rear_axle_to_center_dist, 0.0)
        rear_axle_velocity_2d = get_velocity_shifted(displacement, center_velocity_2d, angular_vel)
        rear_axle_acceleration_2d = get_acceleration_shifted(displacement, center_acceleration_2d, angular_vel, angular_accel)
        dynamic_ego_state = DynamicCarState.build_from_rear_axle(rear_axle_to_center_dist=rear_axle_to_center_dist, rear_axle_velocity_2d=rear_axle_velocity_2d, rear_axle_acceleration_2d=rear_axle_acceleration_2d, angular_velocity=angular_vel, angular_acceleration=angular_accel)
        return cls(car_footprint=car_footprint, dynamic_car_state=dynamic_ego_state, tire_steering_angle=tire_steering_angle, time_point=time_point, is_in_auto_mode=is_in_auto_mode)

@classmethod
def build_from_rear_axle(cls, rear_axle_pose: StateSE2, rear_axle_velocity_2d: StateVector2D, rear_axle_acceleration_2d: StateVector2D, tire_steering_angle: float, time_point: TimePoint, vehicle_parameters: VehicleParameters, is_in_auto_mode: bool=True, angular_vel: float=0.0, angular_accel: float=0.0, tire_steering_rate: float=0.0) -> EgoState:
    """
        Initializer using raw parameters, assumes that the reference frame is CAR_POINT.REAR_AXLE
        :param rear_axle_pose: Pose of ego's rear axle
        :param rear_axle_velocity_2d: Vectorial velocity of Ego's rear axle
        :param rear_axle_acceleration_2d: Vectorial acceleration of Ego's rear axle
        :param angular_vel: Angular velocity of Ego
        :param angular_accel: Angular acceleration of Ego,
        :param tire_steering_angle: Angle of the tires
        :param is_in_auto_mode: True if ego is in auto mode, false otherwise
        :param time_point: Timestamp of the ego state
        :param vehicle_parameters: Vehicle parameters
        :param tire_steering_rate: Steering rate of tires [rad/s]
        :return: The initialized EgoState
        """
    car_footprint = CarFootprint.build_from_rear_axle(rear_axle_pose=rear_axle_pose, vehicle_parameters=vehicle_parameters)
    dynamic_ego_state = DynamicCarState.build_from_rear_axle(rear_axle_to_center_dist=car_footprint.rear_axle_to_center_dist, rear_axle_velocity_2d=rear_axle_velocity_2d, rear_axle_acceleration_2d=rear_axle_acceleration_2d, angular_velocity=angular_vel, angular_acceleration=angular_accel, tire_steering_rate=tire_steering_rate)
    return cls(car_footprint=car_footprint, dynamic_car_state=dynamic_ego_state, tire_steering_angle=tire_steering_angle, time_point=time_point, is_in_auto_mode=is_in_auto_mode)

class Agent(AgentTemporalState, AgentState):
    """
    AgentState with future and past trajectory.
    """

    def __init__(self, tracked_object_type: TrackedObjectType, oriented_box: OrientedBox, velocity: StateVector2D, metadata: SceneObjectMetadata, angular_velocity: Optional[float]=None, predictions: Optional[List[PredictedTrajectory]]=None, past_trajectory: Optional[PredictedTrajectory]=None):
        """
        Representation of an Agent in the scene (Vehicles, Pedestrians, Bicyclists and GenericObjects).
        :param tracked_object_type: Type of the current agent.
        :param oriented_box: Geometrical representation of the Agent.
        :param velocity: Velocity (vectorial) of Agent.
        :param metadata: Agent's metadata.
        :param angular_velocity: The scalar angular velocity of the agent, if available.
        :param predictions: Optional list of (possibly multiple) predicted trajectories.
        :param past_trajectory: Optional past trajectory of this agent.
        """
        AgentTemporalState.__init__(self, initial_time_stamp=TimePoint(metadata.timestamp_us), predictions=predictions, past_trajectory=past_trajectory)
        AgentState.__init__(self, tracked_object_type=tracked_object_type, oriented_box=oriented_box, metadata=metadata, velocity=velocity, angular_velocity=angular_velocity)

    @classmethod
    def from_agent_state(cls, agent: AgentState) -> Agent:
        """
        Create Agent from AgentState.
        :param agent: input single agent state.
        :return: Agent with None for future and past trajectory.
        """
        return cls(tracked_object_type=agent.tracked_object_type, oriented_box=agent.box, velocity=agent.velocity, metadata=agent.metadata, angular_velocity=agent.angular_velocity, predictions=None, past_trajectory=None)

@classmethod
def from_agent_state(cls, agent: AgentState) -> Agent:
    """
        Create Agent from AgentState.
        :param agent: input single agent state.
        :return: Agent with None for future and past trajectory.
        """
    return cls(tracked_object_type=agent.tracked_object_type, oriented_box=agent.box, velocity=agent.velocity, metadata=agent.metadata, angular_velocity=agent.angular_velocity, predictions=None, past_trajectory=None)

def to_ego_center_from_scene(scene: Dict[str, Any], vehicle: VehicleParameters) -> StateSE2:
    """
    :param scene: from scene['ego'].
    :param vehicle: vehicle parameters.
    :return the extracted State in the center of ego's bounding box.
    """
    ego_pose = scene['pose']
    ego_x = ego_pose[0]
    ego_y = ego_pose[1]
    ego_heading = ego_pose[2]
    distance = vehicle.rear_axle_to_center
    return translate_longitudinally(StateSE2(ego_x, ego_y, ego_heading), distance)

class RemotePlanner(AbstractPlanner):
    """
    Remote planner delegates computation of trajectories to a docker container, with which communicates through
    grpc.
    """

    def __init__(self, submission_container_manager: Optional[SubmissionContainerManager]=None, submission_image: Optional[str]=None, container_name: Optional[str]=None, compute_trajectory_timeout: float=1) -> None:
        """
        Prepares the remote container for planning.
        :param submission_container_manager: Optional manager, if provided a container will be started by RemotePlanner
        :param submission_image: Docker image name for the submission_container_factory
        :param container_name: Name to assign to the submission container
        :param compute_trajectory_timeout: Timeout for computation of trajectory.
        """
        if submission_container_manager:
            missing_parameter_message = 'Parameters for SubmissionContainer are missing!'
            assert submission_image, missing_parameter_message
            assert container_name, missing_parameter_message
            self.port = None
        else:
            self.port = os.getenv('SUBMISSION_CONTAINER_PORT', 50051)
        self.submission_container_manager = submission_container_manager
        self.submission_image = submission_image
        self.container_name = container_name
        self._channel = None
        self._stub = None
        self.serialized_observation: Optional[List[bytes]] = None
        self.serialized_state: Optional[List[bytes]] = None
        self.sample_interval: Optional[float] = None
        self._compute_trajectory_timeout = compute_trajectory_timeout

    def __reduce__(self) -> Tuple[Type[RemotePlanner], Tuple[Optional[SubmissionContainerManager], Optional[str], Optional[str]]]:
        """
        :return: tuple of class and its constructor parameters, this is used to pickle the class
        """
        return (self.__class__, (self.submission_container_manager, self.submission_image, self.container_name))

    def name(self) -> str:
        """Inherited, see superclass."""
        return 'RemotePlanner'

    def observation_type(self) -> Type[Observation]:
        """Inherited, see superclass."""
        return DetectionsTracks

    @staticmethod
    def _planner_initializations_to_message(initialization: PlannerInitialization) -> chpb.PlannerInitializationLight:
        """
        Converts a PlannerInitialization to the message specified in the protocol files.
        :param initialization: The initialization parameters for the planner
        :return: A initialization message
        """
        try:
            mission_goal = proto_se2_from_se2(initialization.mission_goal)
        except AttributeError as e:
            logger.error('Mission goal was None!')
            raise e
        planner_initialization = chpb.PlannerInitializationLight(route_roadblock_ids=initialization.route_roadblock_ids, mission_goal=mission_goal, map_name=initialization.map_api.map_name)
        return planner_initialization

    def initialize(self, initialization: PlannerInitialization, timeout: float=5) -> None:
        """
        Creates the container manager, and runs the specified docker image. The communication port is created using
        the PID from the ray worker. Sends a request to initialize the remote planner.
        :param initialization: List of PlannerInitialization objects
        :param timeout: for planner initialization
        """
        if self.submission_container_manager:
            submission_container = try_n_times(self.submission_container_manager.get_submission_container, [self.submission_image, self.container_name, find_free_port_number()], {}, (docker.errors.APIError,), max_tries=10)
            self.port = submission_container.port
            submission_container.start()
            submission_container.wait_until_running(timeout=5)
        self._channel = grpc.insecure_channel(f'{NETWORK}:{self.port}')
        self._stub = chpb_grpc.DetectionTracksChallengeStub(self._channel)
        logger.info('Client sending planner initialization request...')
        planner_initializations_message = self._planner_initializations_to_message(initialization)
        logger.info(f'Trying to communicate on port {NETWORK}:{self.port}')
        try:
            _, _ = keep_trying(self._stub.InitializePlanner, [planner_initializations_message], {}, errors=(grpc.RpcError,), timeout=timeout)
        except Exception as e:
            submission_logger.error('Planner initialization failed!')
            submission_logger.error(e)
            raise e
        logger.info('Planner initialized!')

    def compute_planner_trajectory(self, current_input: PlannerInput) -> AbstractTrajectory:
        """
        Computes the ego vehicle trajectory.
        :param current_input: Planner input for which trajectory should be computed
        :return: Trajectory representing the predicted ego's position in future for every input iteration
        """
        logger.debug('Client sending planner input: %s' % current_input)
        trajectory = self._compute_trajectory(self._stub, current_input=current_input)
        return trajectory

    def _compute_trajectory(self, stub: chpb_grpc.DetectionTracksChallengeStub, current_input: PlannerInput) -> AbstractTrajectory:
        """
        Sends a request to compute the trajectory given the PlannerInput to the remote planner.
        :param stub: Service interface
        :param current_input: Planner input for which a trajectory should be computed.
        :return: Trajectory representing the predicted ego's position in future for every input iteration
        """
        logging.debug('Client sending observation...')
        self.serialized_state, self.serialized_observation, self.sample_interval = self._get_history_update(current_input)
        serialized_simulation_iteration = chpb.SimulationIteration(time_us=current_input.iteration.time_us, index=current_input.iteration.index)
        if self.sample_interval:
            serialized_buffer = chpb.SimulationHistoryBuffer(ego_states=self.serialized_state, observations=self.serialized_observation, sample_interval=self.sample_interval)
        else:
            serialized_buffer = chpb.SimulationHistoryBuffer(ego_states=self.serialized_state, observations=self.serialized_observation, sample_interval=None)
        tl_data = self._build_tl_message_from_planner_input(current_input)
        planner_input = chpb.PlannerInput(simulation_iteration=serialized_simulation_iteration, simulation_history_buffer=serialized_buffer, traffic_light_data=tl_data)
        try:
            trajectory_message = stub.ComputeTrajectory(planner_input, timeout=self._compute_trajectory_timeout)
        except grpc.RpcError as e:
            submission_logger.error('Trajectory computation service failed!')
            submission_logger.error(e)
            raise e
        return interp_traj_from_proto_traj(trajectory_message)

    def _get_history_update(self, planner_input: PlannerInput) -> Tuple[List[bytes], List[bytes], Optional[float]]:
        """
        Gets the new states and observations from the input. If no cache is present, the entire history is
        serialized, otherwise just the last element.
        :param planner_input: The input for planners
        :return: Tuple with new serialized state and observations.
        """
        keep_all_history = not self.serialized_state and (not self.serialized_observation)
        if keep_all_history:
            serialized_state = [pickle.dumps(state) for state in planner_input.history.ego_states]
            serialized_observation = [pickle.dumps(obs) for obs in planner_input.history.observations]
        else:
            last_ego_state, last_observations = planner_input.history.current_state
            serialized_state = [pickle.dumps(last_ego_state)]
            serialized_observation = [pickle.dumps(last_observations)]
        sample_interval = planner_input.history.sample_interval if not self.sample_interval else None
        return (serialized_state, serialized_observation, sample_interval)

    @staticmethod
    def _build_tl_message_from_planner_input(planner_input: PlannerInput) -> chpb.TrafficLightStatusData:
        tl_status_data: List[List[chpb.TrafficLightStatusData]]
        if planner_input.traffic_light_data is None:
            tl_status_data = [[]]
        else:
            tl_status_data = [proto_tl_status_data_from_tl_status_data(tl_status_data) for tl_status_data in planner_input.traffic_light_data]
        return tl_status_data

@staticmethod
def _build_tl_message_from_planner_input(planner_input: PlannerInput) -> chpb.TrafficLightStatusData:
    tl_status_data: List[List[chpb.TrafficLightStatusData]]
    if planner_input.traffic_light_data is None:
        tl_status_data = [[]]
    else:
        tl_status_data = [proto_tl_status_data_from_tl_status_data(tl_status_data) for tl_status_data in planner_input.traffic_light_data]
    return tl_status_data

class SkeletonTestSerializationCallback(unittest.TestCase):
    """Base class for TestsSerializationCallback* classes."""

    def _setUp(self) -> None:
        """Setup mocks for our tests."""
        self._serialization_type_to_extension_map = {'json': '.json', 'pickle': '.pkl.xz', 'msgpack': '.msgpack.xz'}
        self._serialization_type = getattr(self, '_serialization_type', '')
        self.assertIn(self._serialization_type, self._serialization_type_to_extension_map)
        self.output_folder = tempfile.TemporaryDirectory()
        self.callback = SerializationCallback(output_directory=self.output_folder.name, folder_name='sim', serialization_type=self._serialization_type, serialize_into_single_file=True)
        self.sim_manager = Mock(spec=AbstractSimulationTimeController)
        self.observation = Mock(spec=AbstractObservation)
        self.controller = Mock(spec=AbstractEgoController)
        super().setUp()

    @settings(deadline=None)
    @given(mock_timestamp=st.one_of(st.just(0), st.integers(min_value=1627066061949808, max_value=18446744073709551615)))
    def _dump_test_scenario(self, mock_timestamp: int) -> None:
        """
        Tests whether a scene can be dumped into a file and check that the keys are in the dumped scene.
        :param mock_timestamp: Mocked timestamp to pass to mock_get_traffic_light_status_at_iteration.
        """

        def mock_get_traffic_light_status_at_iteration(iteration: int) -> Generator[TrafficLightStatusData, None, None]:
            """Mocks MockAbstractScenario.get_traffic_light_status_at_iteration to return large numbers."""
            dummy_tl_data = TrafficLightStatusData(status=TrafficLightStatusType.GREEN, lane_connector_id=1, timestamp=mock_timestamp)
            yield dummy_tl_data
        scenario = MockAbstractScenario()
        scenario.get_traffic_light_status_at_iteration = Mock(spec=scenario.get_traffic_light_status_at_iteration)
        scenario.get_traffic_light_status_at_iteration.side_effect = mock_get_traffic_light_status_at_iteration
        self.setup = SimulationSetup(observations=self.observation, scenario=scenario, time_controller=self.sim_manager, ego_controller=self.controller)
        planner = Mock()
        planner.name = Mock(return_value='DummyPlanner')
        directory = self.callback._get_scenario_folder(planner.name(), scenario)
        self.assertEqual(str(directory), self.output_folder.name + '/sim/DummyPlanner/mock_scenario_type/mock_log_name/mock_scenario_name')
        self.callback.on_initialization_start(self.setup, planner)
        history = SimulationHistory(scenario.map_api, scenario.get_mission_goal())
        state_0 = EgoState.build_from_rear_axle(StateSE2(0, 0, 0), vehicle_parameters=scenario.ego_vehicle_parameters, rear_axle_velocity_2d=StateVector2D(x=0, y=0), rear_axle_acceleration_2d=StateVector2D(x=0, y=0), tire_steering_angle=0, time_point=TimePoint(0))
        state_1 = EgoState.build_from_rear_axle(StateSE2(0, 0, 0), vehicle_parameters=scenario.ego_vehicle_parameters, rear_axle_velocity_2d=StateVector2D(x=0, y=0), rear_axle_acceleration_2d=StateVector2D(x=0, y=0), tire_steering_angle=0, time_point=TimePoint(1000))
        history.add_sample(SimulationHistorySample(iteration=SimulationIteration(time_point=TimePoint(0), index=0), ego_state=state_0, trajectory=InterpolatedTrajectory(trajectory=[state_0, state_1]), observation=DetectionsTracks(TrackedObjects()), traffic_light_status=scenario.get_traffic_light_status_at_iteration(0)))
        history.add_sample(SimulationHistorySample(iteration=SimulationIteration(time_point=TimePoint(0), index=0), ego_state=state_1, trajectory=InterpolatedTrajectory(trajectory=[state_0, state_1]), observation=DetectionsTracks(TrackedObjects()), traffic_light_status=scenario.get_traffic_light_status_at_iteration(0)))
        for data in history.data:
            self.callback.on_step_end(self.setup, planner, data)
        self.callback.on_simulation_end(self.setup, planner, history)
        filename = 'mock_scenario_name' + self._serialization_type_to_extension_map[self._serialization_type]
        path = pathlib.Path(self.output_folder.name + '/sim/DummyPlanner/mock_scenario_type/mock_log_name/mock_scenario_name/' + filename)
        self.assertTrue(path.exists())
        if self._serialization_type == 'json':
            with open(path.absolute()) as f:
                data = json.load(f)
        elif self._serialization_type == 'msgpack':
            with lzma.open(str(path), 'rb') as f:
                data = msgpack.unpackb(f.read())
        elif self._serialization_type == 'pickle':
            with lzma.open(str(path), 'rb') as f:
                data = pickle.load(f)
        self.assertTrue(len(data) > 0)
        data = data[0]
        self.assertTrue('world' in data.keys())
        self.assertTrue('ego' in data.keys())
        self.assertTrue('trajectories' in data.keys())
        self.assertTrue('map' in data.keys())
        expected_traffic_light_data = next(scenario.get_traffic_light_status_at_iteration(0))
        actual_traffic_light_data_dict = data['traffic_light_status'][0]
        self.assertEqual(actual_traffic_light_data_dict['timestamp'], expected_traffic_light_data.timestamp)

def mock_get_traffic_light_status_at_iteration(iteration: int) -> Generator[TrafficLightStatusData, None, None]:
    """Mocks MockAbstractScenario.get_traffic_light_status_at_iteration to return large numbers."""
    dummy_tl_data = TrafficLightStatusData(status=TrafficLightStatusType.GREEN, lane_connector_id=1, timestamp=mock_timestamp)
    yield dummy_tl_data

class ScriptableTorchModuleWrapper(TorchModuleWrapper):
    """
    An interface representing a model that can be exported with TorchScript
    """

    def __init__(self, future_trajectory_sampling: TrajectorySampling, feature_builders: List[AbstractFeatureBuilder], target_builders: List[AbstractTargetBuilder]):
        """
        Construct a scriptable model with feature and target builders.
        :param future_trajectory_sampling: Parameters for a predicted trajectory.
        :param feature_builders: The list of builders which will compute features for this model.
        :param target_builders: The list of builders which will compute targets for this model.
        """
        super().__init__(future_trajectory_sampling=future_trajectory_sampling, feature_builders=feature_builders, target_builders=target_builders)

    @abstractmethod
    def scriptable_forward(self, tensor_data: Dict[str, torch.Tensor], list_tensor_data: Dict[str, List[torch.Tensor]], list_list_tensor_data: Dict[str, List[List[torch.Tensor]]]) -> Tuple[Dict[str, torch.Tensor], Dict[str, List[torch.Tensor]], Dict[str, List[List[torch.Tensor]]]]:
        """
        This method contains the logic that will be exported when scripted.
        It is expected that the input dictionaries contain the data as created by the supplied feature builders.
        :param tensor_data: The input tensor data to the function.
            This will come from the `scriptable_forward` methods in the provided feature builders.
        :param list_tensor_data: The input List[tensor] data to the function.
            This will come from the `scriptable_forward` methods in the provided feature builders.
        :param list_list_tensor_data: The input List[List[tensor]] data to the function.
            This will come from the `scriptable_forward` methods in the provided feature builders.
        :return: The output from the function.
        """
        raise NotImplementedError()

@abstractmethod
def scriptable_forward(self, tensor_data: Dict[str, torch.Tensor], list_tensor_data: Dict[str, List[torch.Tensor]], list_list_tensor_data: Dict[str, List[List[torch.Tensor]]]) -> Tuple[Dict[str, torch.Tensor], Dict[str, List[torch.Tensor]], Dict[str, List[List[torch.Tensor]]]]:
    """
        This method contains the logic that will be exported when scripted.
        It is expected that the input dictionaries contain the data as created by the supplied feature builders.
        :param tensor_data: The input tensor data to the function.
            This will come from the `scriptable_forward` methods in the provided feature builders.
        :param list_tensor_data: The input List[tensor] data to the function.
            This will come from the `scriptable_forward` methods in the provided feature builders.
        :param list_list_tensor_data: The input List[List[tensor]] data to the function.
            This will come from the `scriptable_forward` methods in the provided feature builders.
        :return: The output from the function.
        """
    raise NotImplementedError()

class ScriptableFeatureBuilder(torch.nn.Module, AbstractFeatureBuilder):
    """
    A FeatureBuilder that supports exporting via TorchScript.
    """

    @abstractmethod
    def scriptable_forward(self, tensor_data: Dict[str, torch.Tensor], list_tensor_data: Dict[str, List[torch.Tensor]], list_list_tensor_data: Dict[str, List[List[torch.Tensor]]]) -> Tuple[Dict[str, torch.Tensor], Dict[str, List[torch.Tensor]], Dict[str, List[List[torch.Tensor]]]]:
        """
        This method contains the logic that will be exported when scripted.
        :param tensor_data: The input tensor data to the function. This will be computed by the C++ engine as configured
            with `precomputed_feature_config()`
        :param list_tensor_data: The input List[tensor] data to the function. This will be computed by the C++ engine
            as configured with `precomputed_feature_config()`
        :param list_list_tensor_data: The input List[List[tensor]] data to the function. This will be computed by the C++ engine
            as configured with `precomputed_feature_config()`
        :return: The output from the function.
        """
        raise NotImplementedError()

    @abstractmethod
    def precomputed_feature_config(self) -> Dict[str, Dict[str, str]]:
        """
        Export the config used for the precomputed features.
        This method will be scripted and used by the C++ engine to determine which features will be computed as input to `scriptable_forward()`.
        :return: The config required for precomputed features. This is a dict of [method_name -> [method_parameter, parameter_value]]
        """
        raise NotImplementedError()

@abstractmethod
def scriptable_forward(self, tensor_data: Dict[str, torch.Tensor], list_tensor_data: Dict[str, List[torch.Tensor]], list_list_tensor_data: Dict[str, List[List[torch.Tensor]]]) -> Tuple[Dict[str, torch.Tensor], Dict[str, List[torch.Tensor]], Dict[str, List[List[torch.Tensor]]]]:
    """
        This method contains the logic that will be exported when scripted.
        :param tensor_data: The input tensor data to the function. This will be computed by the C++ engine as configured
            with `precomputed_feature_config()`
        :param list_tensor_data: The input List[tensor] data to the function. This will be computed by the C++ engine
            as configured with `precomputed_feature_config()`
        :param list_list_tensor_data: The input List[List[tensor]] data to the function. This will be computed by the C++ engine
            as configured with `precomputed_feature_config()`
        :return: The output from the function.
        """
    raise NotImplementedError()

@abstractmethod
def precomputed_feature_config(self) -> Dict[str, Dict[str, str]]:
    """
        Export the config used for the precomputed features.
        This method will be scripted and used by the C++ engine to determine which features will be computed as input to `scriptable_forward()`.
        :return: The config required for precomputed features. This is a dict of [method_name -> [method_parameter, parameter_value]]
        """
    raise NotImplementedError()

class BaseTab:
    """Base tab for other tabs."""

    def __init__(self, doc: Document, experiment_file_data: ExperimentFileData):
        """
        Base tabs for common properties.
        Metric board to render metrics.
        :doc: A bokeh HTML document.
        :param experiment_file_data: Experiment file data.
        """
        self._doc = doc
        self._experiment_file_data: ExperimentFileData = experiment_file_data
        self._simulation_scenario_keys: List[SimulationScenarioKey] = []
        self._experiment_file_active_index: List[int] = []
        self.scatter_signs = ['circle', 'diamond', 'plus', 'square', 'triangle', 'inverted_triangle', 'star', 'asterisk', 'dot_circle', 'diamond_cross']
        self.search_criteria_selection_size = base_tab_style['search_criteria_sizes']
        self.plot_sizes = base_tab_style['plot_sizes']
        self.simulation_figure_sizes = simulation_tile_style['figure_sizes']
        self.plot_frame_sizes = base_tab_style['plot_frame_sizes']
        self.window_width = 0
        self.window_height = 0
        self.planner_checkbox_group = CheckboxGroup(labels=[], active=[], inline=True, css_classes=['planner-checkbox-group'], sizing_mode='scale_both')
        self.planner_checkbox_group.on_click(self._click_planner_checkbox_group)

    def file_paths_on_change(self, experiment_file_data: ExperimentFileData, experiment_file_active_index: List[int]) -> None:
        """
        Interface to update layout when file_paths is changed.
        :param experiment_file_data: Experiment file data.
        :param experiment_file_active_index: Active indexes for experiment files.
        """
        raise NotImplementedError

    def _click_planner_checkbox_group(self, attr: Any) -> None:
        """
        Click event handler for planner_checkbox_group.
        :param attr: Clicked attributes.
        """
        raise NotImplementedError

    @property
    def experiment_file_data(self) -> ExperimentFileData:
        """Return experiment file data."""
        return self._experiment_file_data

    @experiment_file_data.setter
    def experiment_file_data(self, experiment_file_data: ExperimentFileData) -> None:
        """
        Update experiment file data.
        :param experiment_file_data: New experiment file data.
        """
        self._experiment_file_data = experiment_file_data

    @property
    def enable_planner_names(self) -> List[str]:
        """Return a list of enable planner names."""
        enable_planner_names = [self.planner_checkbox_group.labels[index] for index in self.planner_checkbox_group.active]
        return enable_planner_names

    def get_plot_cols(self, plot_width: int, default_col_width: int=1024, offset_width: int=0, default_ncols: int=0) -> int:
        """
        Return number of columns for a grid plot.
        :param plot_width: Plot width.
        :param default_col_width: The number of columns would be 1 if window width is lower than this value.
        :param offset_width: Additional offset width.
        :param default_ncols: Default number of columns.
        :return: Get a number of columns for a grid plot.
        """
        if default_ncols and (not self.window_width):
            return default_ncols
        window_width = self.window_width - offset_width
        if window_width <= default_col_width:
            return 1
        col_num = 1 + round((window_width - default_col_width) / plot_width)
        return col_num

    def get_scatter_sign(self, index: int) -> str:
        """
        Get scatter index sign based on the index.
        :param index: Index for the scatter sign.
        :return A scatter sign name.
        """
        index = index % len(self.scatter_signs)
        return self.scatter_signs[index]

    @staticmethod
    def get_scatter_render_func(scatter_sign: str, scatter_figure: Figure) -> Any:
        """
        Render a scatter plot.
        :param scatter_sign: Scatter sign.
        :param scatter_figure: Scatter figure.
        :return A scatter render function.
        """
        if scatter_sign == 'circle':
            renderer = scatter_figure.circle
        elif scatter_sign == 'diamond':
            renderer = scatter_figure.diamond
        elif scatter_sign == 'plus':
            renderer = scatter_figure.plus
        elif scatter_sign == 'square':
            renderer = scatter_figure.square
        elif scatter_sign == 'triangle':
            renderer = scatter_figure.triangle
        elif scatter_sign == 'inverted_triangle':
            renderer = scatter_figure.inverted_triangle
        elif scatter_sign == 'star':
            renderer = scatter_figure.star
        elif scatter_sign == 'asterisk':
            renderer = scatter_figure.asterisk
        elif scatter_sign == 'diamond_cross':
            renderer = scatter_figure.diamond_cross
        else:
            raise NotImplementedError(f'{scatter_sign} is not a valid option for scatter plots!')
        return renderer

    def get_file_path_last_name(self, index: int) -> str:
        """
        Get last name of a file path.
        :param index: Index for the file path.
        :return: A file path string name.
        """
        file_path = self._experiment_file_data.file_paths[index]
        default_experiment_file_path_stem = pathlib.Path(file_path.metric_main_path)
        if file_path.current_path is None:
            return str(default_experiment_file_path_stem.name)
        metric_path = pathlib.Path(file_path.current_path, file_path.metric_folder)
        if metric_path.exists():
            experiment_file_path_stem = file_path.current_path
        else:
            experiment_file_path_stem = default_experiment_file_path_stem
        return str(experiment_file_path_stem.name)

    def load_log_name(self, scenario_type: str) -> List[str]:
        """
        Load a list of log names based on the scenario type.
        :param scenario_type: A selected scenario type.
        :return a list of log names.
        """
        log_names = self._experiment_file_data.available_scenarios.get(scenario_type, [])
        sorted_log_names: List[str] = sorted(list(set(log_names)), reverse=False)
        return sorted_log_names

    def load_scenario_names(self, scenario_type: str, log_name: str) -> List[str]:
        """
        Load a list of scenario names based on the log name.
        :param scenario_type: A selected scenario type.
        :param log_name: A selected log name.
        :return a list of scenario names.
        """
        log_dict = self._experiment_file_data.available_scenarios.get(scenario_type, [])
        if not log_dict:
            return []
        scenario_names = log_dict.get(log_name, [])
        sorted_scenario_names: List[str] = sorted(list(set(scenario_names)), reverse=False)
        return sorted_scenario_names

    def _init_multi_search_criteria_selection(self, scenario_type_multi_choice: MultiChoice, metric_name_multi_choice: MultiChoice) -> None:
        """
        Init histogram and scenario selection options.
        :param scenario_type_multi_choice: Scenario type multi choice.
        :param metric_name_multi_choice: Metric type multi choice.
        """
        scenario_type_multi_choice.options = ['all'] + sorted(self.experiment_file_data.available_scenario_types)
        metric_name_multi_choice.options = sorted(self.experiment_file_data.available_metric_statistics_names)

    def search_metric_statistics_dataframe(self, scenario_types: Optional[List[str]]=None, metric_choices: Optional[List[str]]=None) -> List[SelectedMetricStatisticDataFrame]:
        """
        Search metric statistics dataframe based on scenario types and metric choices.
        :param scenario_types: A list of scenario types.
        :param metric_choices: A list of metric choices.
        :return: A list of selected metric statistic dataframe.
        """
        data: List[SelectedMetricStatisticDataFrame] = []
        if not scenario_types and (not metric_choices):
            return data
        for index, metric_statistics_dataframes in enumerate(self.experiment_file_data.metric_statistics_dataframes):
            for metric_statistics_dataframe in metric_statistics_dataframes:
                if metric_choices and metric_statistics_dataframe.metric_statistic_name not in metric_choices:
                    continue
                data.append(SelectedMetricStatisticDataFrame(dataframe_index=index, dataframe=metric_statistics_dataframe))
        return data

@staticmethod
def get_scatter_render_func(scatter_sign: str, scatter_figure: Figure) -> Any:
    """
        Render a scatter plot.
        :param scatter_sign: Scatter sign.
        :param scatter_figure: Scatter figure.
        :return A scatter render function.
        """
    if scatter_sign == 'circle':
        renderer = scatter_figure.circle
    elif scatter_sign == 'diamond':
        renderer = scatter_figure.diamond
    elif scatter_sign == 'plus':
        renderer = scatter_figure.plus
    elif scatter_sign == 'square':
        renderer = scatter_figure.square
    elif scatter_sign == 'triangle':
        renderer = scatter_figure.triangle
    elif scatter_sign == 'inverted_triangle':
        renderer = scatter_figure.inverted_triangle
    elif scatter_sign == 'star':
        renderer = scatter_figure.star
    elif scatter_sign == 'asterisk':
        renderer = scatter_figure.asterisk
    elif scatter_sign == 'diamond_cross':
        renderer = scatter_figure.diamond_cross
    else:
        raise NotImplementedError(f'{scatter_sign} is not a valid option for scatter plots!')
    return renderer

def is_valid_token(token: Any) -> bool:
    """
    Basic check that a scenario token is the right type/length.
    :token: parsed by hydra.
    :return: true if it looks valid, otherwise false.
    """
    if not isinstance(token, str) or len(token) != 16:
        return False
    try:
        return bytearray.fromhex(token).hex() == token
    except (TypeError, ValueError):
        return False

class MockAbstractScenario(AbstractScenario):
    """Mock abstract scenario class used for testing."""

    def __init__(self, initial_time_us: TimePoint=TimePoint(time_us=1621641671099), time_step: float=0.5, number_of_future_iterations: int=10, number_of_past_iterations: int=0, initial_velocity: StateVector2D=StateVector2D(x=1.0, y=0.0), fixed_acceleration: StateVector2D=StateVector2D(x=0.0, y=0.0), number_of_detections: int=10, initial_ego_state: StateSE2=StateSE2(x=0.0, y=0.0, heading=0.0), mission_goal: StateSE2=StateSE2(10, 0, 0), tracked_object_types: List[TrackedObjectType]=[TrackedObjectType.VEHICLE]):
        """
        Create mocked scenario where ego starts with an initial velocity [m/s] and has a constant acceleration
            throughout (0 m/s^2 by default). The ego does not turn.
        :param initial_time_us: initial time from start point of scenario [us]
        :param time_step: time step in [s]
        :param number_of_future_iterations: number of iterations in the future
        :param number_of_past_iterations: number of iterations in the past
        :param initial_velocity: [m/s] velocity assigned to the ego at iteration 0
        :param fixed_acceleration: [m/s^2] constant ego acceleration throughout scenario
        :param number_of_detections: number of detections in the scenario
        :param initial_ego_state: Initial state of ego
        :param mission_goal: Dummy mission goal
        :param tracked_object_types: Types of tracked objects to mock
        """
        self._initial_time_us = initial_time_us
        self._time_step = time_step
        self._number_of_past_iterations = number_of_past_iterations
        self._number_of_future_iterations = number_of_future_iterations
        self._current_iteration = number_of_past_iterations
        self._total_iterations = number_of_past_iterations + number_of_future_iterations + 1
        self._tracked_object_types = tracked_object_types
        start_time_us = max(TimePoint(int(number_of_past_iterations * time_step * 1000000.0)), initial_time_us)
        time_horizon = (number_of_past_iterations + number_of_future_iterations) * time_step
        history_buffer = SimulationHistoryBuffer.initialize_from_list(buffer_size=10, ego_states=[EgoState.build_from_rear_axle(StateSE2(x=initial_ego_state.x, y=initial_ego_state.y, heading=initial_ego_state.heading), time_point=start_time_us, rear_axle_velocity_2d=initial_velocity, tire_steering_angle=0.0, rear_axle_acceleration_2d=fixed_acceleration, vehicle_parameters=self.ego_vehicle_parameters)], observations=[DetectionsTracks(TrackedObjects())], sample_interval=time_step)
        planner_input = PlannerInput(iteration=SimulationIteration(start_time_us, 0), history=history_buffer)
        planner = SimplePlanner(horizon_seconds=time_horizon, sampling_time=time_step, acceleration=fixed_acceleration.array)
        self._ego_states = planner.compute_trajectory(planner_input).get_sampled_trajectory()
        self._tracked_objects = [DetectionsTracks(TrackedObjects([get_sample_agent(token=str(idx + type_idx * number_of_detections), agent_type=agent_type, num_future_states=0) for idx in range(number_of_detections) for type_idx, agent_type in enumerate(self._tracked_object_types)])) for _ in range(self._total_iterations)]
        self._sensors = [Sensors(pointcloud={LidarChannel.MERGED_PC: np.eye(3) for _ in range(number_of_detections)}, images=None) for _ in range(self._total_iterations)]
        if len(self._ego_states) != len(self._tracked_objects) or len(self._ego_states) != self._total_iterations:
            raise RuntimeError('The dimensions of detections and ego trajectory is not the same!')
        self._mission_goal = mission_goal
        self._map_api = MockAbstractMap()
        self._token_suffix = str(uuid.uuid4())

    @property
    def token(self) -> str:
        """Implemented. See interface."""
        return f'mock_token_{self._token_suffix}'

    @property
    def log_name(self) -> str:
        """Implemented. See interface."""
        return 'mock_log_name'

    @property
    def scenario_name(self) -> str:
        """Implemented. See interface."""
        return 'mock_scenario_name'

    @property
    def ego_vehicle_parameters(self) -> VehicleParameters:
        """Inherited, see superclass."""
        return get_pacifica_parameters()

    @property
    def scenario_type(self) -> str:
        """Implemented. See interface."""
        return 'mock_scenario_type'

    @property
    def map_api(self) -> AbstractMap:
        """Implemented. See interface."""
        return self._map_api

    @property
    def database_interval(self) -> float:
        """Inherited, see superclass."""
        return self._time_step

    def get_number_of_iterations(self) -> int:
        """Implemented. See interface."""
        return self._number_of_future_iterations

    def get_time_point(self, iteration: int) -> TimePoint:
        """Implemented. See interface."""
        return self._ego_states[self._current_iteration + iteration].time_point

    def get_lidar_to_ego_transform(self) -> Transform:
        """Implemented. See interface."""
        return np.eye(4)

    def get_mission_goal(self) -> Optional[StateSE2]:
        """Implemented. See interface."""
        return self._mission_goal

    def get_route_roadblock_ids(self) -> List[str]:
        """Implemented. See interface."""
        return []

    def get_expert_goal_state(self) -> StateSE2:
        """Implemented. See interface."""
        return self._mission_goal

    def get_tracked_objects_at_iteration(self, iteration: int, future_trajectory_sampling: Optional[TrajectorySampling]=None) -> DetectionsTracks:
        """Implemented. See interface."""
        return self._tracked_objects[self._current_iteration + iteration]

    def get_tracked_objects_within_time_window_at_iteration(self, iteration: int, past_time_horizon: float, future_time_horizon: float, filter_track_tokens: Optional[Set[str]]=None, future_trajectory_sampling: Optional[TrajectorySampling]=None) -> DetectionsTracks:
        """Implemented. See interface."""
        raise NotImplementedError

    def get_sensors_at_iteration(self, iteration: int, channels: Optional[List[SensorChannel]]=None) -> Sensors:
        """Implemented. See interface."""
        raise NotImplementedError

    def get_ego_state_at_iteration(self, iteration: int) -> EgoState:
        """Implemented. See interface."""
        return self._ego_states[self._current_iteration + iteration]

    def get_traffic_light_status_at_iteration(self, iteration: int) -> Generator[TrafficLightStatusData, None, None]:
        """Implemented. see interface."""
        dummy_data = TrafficLightStatusData(status=TrafficLightStatusType.GREEN, lane_connector_id=1, timestamp=1627066061949808)
        yield dummy_data

    def get_past_traffic_light_status_history(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[TrafficLightStatuses, None, None]:
        """Gets past traffic light status."""
        dummy_data = TrafficLightStatusData(status=TrafficLightStatusType.GREEN, lane_connector_id=1, timestamp=1627066061949808)
        num_samples = get_num_samples(num_samples, time_horizon, self.database_interval)
        for _ in range(num_samples):
            yield TrafficLightStatuses([dummy_data])

    def get_future_traffic_light_status_history(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[TrafficLightStatuses, None, None]:
        """Gets future traffic light status."""
        dummy_data = TrafficLightStatusData(status=TrafficLightStatusType.GREEN, lane_connector_id=1, timestamp=1627066061949808)
        num_samples = get_num_samples(num_samples, time_horizon, self.database_interval)
        for _ in range(num_samples):
            yield TrafficLightStatuses([dummy_data])

    def get_future_timestamps(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[TimePoint, None, None]:
        """Implemented. See interface."""
        ego_states = self.get_ego_future_trajectory(iteration=iteration, time_horizon=time_horizon, num_samples=num_samples)
        for state in ego_states:
            yield state.time_point

    def get_past_timestamps(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[TimePoint, None, None]:
        """Implemented. See interface."""
        ego_states = self.get_ego_past_trajectory(iteration=iteration, time_horizon=time_horizon, num_samples=num_samples)
        for state in ego_states:
            yield state.time_point

    def get_ego_future_trajectory(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[EgoState, None, None]:
        """Implemented. See interface."""
        num_samples = get_num_samples(num_samples, time_horizon, self.database_interval)
        indices = sample_indices_with_time_horizon(num_samples, time_horizon, self._time_step)
        assert self._number_of_future_iterations - iteration >= indices[-1], f'Requested time horizon of {time_horizon}s is too long! Scenario future has length {(self._number_of_future_iterations - iteration) * self._time_step}s from the iteration {iteration}'
        for idx in indices:
            yield self._ego_states[self._current_iteration + iteration + idx]

    def get_ego_past_trajectory(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[EgoState, None, None]:
        """Implemented. See interface."""
        num_samples = get_num_samples(num_samples, time_horizon, self.database_interval)
        indices = sample_indices_with_time_horizon(num_samples, time_horizon, self._time_step)
        assert self._current_iteration + iteration >= indices[-1], f'Requested time horizon of {time_horizon}s is too long! Scenario past has length {(self._current_iteration + iteration) * self._time_step}s from the iteration {iteration}'
        for idx in reversed(indices):
            yield self._ego_states[self._current_iteration + iteration - idx]

    def get_past_sensors(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None, channels: Optional[List[SensorChannel]]=None) -> Generator[Sensors, None, None]:
        """Implemented. See interface."""
        num_samples = get_num_samples(num_samples, time_horizon, self.database_interval)
        indices = sample_indices_with_time_horizon(num_samples, time_horizon, self._time_step)
        for idx in indices:
            yield self._sensors[self._current_iteration + iteration - idx - 1]

    def get_past_tracked_objects(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None, future_trajectory_sampling: Optional[TrajectorySampling]=None) -> Generator[DetectionsTracks, None, None]:
        """Implemented. See interface."""
        indices = sample_indices_with_time_horizon(num_samples, time_horizon, self._time_step)
        if self._current_iteration + iteration < indices[-1]:
            raise ValueError(f'Requested time horizon of {time_horizon}s is too long! Scenario past has length {(self._current_iteration + iteration) * self._time_step}s from the iteration {iteration}')
        for idx in reversed(indices):
            yield self._tracked_objects[self._current_iteration + iteration - idx]

    def get_future_tracked_objects(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None, future_trajectory_sampling: Optional[TrajectorySampling]=None) -> Generator[DetectionsTracks, None, None]:
        """Implemented. See interface."""
        indices = sample_indices_with_time_horizon(num_samples, time_horizon, self._time_step)
        assert self._number_of_future_iterations - iteration >= indices[-1], f'Requested time horizon of {time_horizon}s is too long! Scenario future has length {(self._number_of_future_iterations - iteration) * self._time_step}s from the iteration {iteration}'
        for idx in indices:
            yield self._tracked_objects[self._current_iteration + iteration + idx]

def get_traffic_light_status_at_iteration(self, iteration: int) -> Generator[TrafficLightStatusData, None, None]:
    """Implemented. see interface."""
    dummy_data = TrafficLightStatusData(status=TrafficLightStatusType.GREEN, lane_connector_id=1, timestamp=1627066061949808)
    yield dummy_data

class TestMockAbstractScenario(unittest.TestCase):
    """
    A class to test the MockAbstractScenario utility class.
    """

    def test_mock_abstract_scenario_implements_abstract_scenario(self) -> None:
        """
        Tests that the mock abstract scenario class properly implements the interface.
        """
        assert_class_properly_implements_interface(AbstractScenario, MockAbstractScenario)

def test_mock_abstract_scenario_implements_abstract_scenario(self) -> None:
    """
        Tests that the mock abstract scenario class properly implements the interface.
        """
    assert_class_properly_implements_interface(AbstractScenario, MockAbstractScenario)

class TestMockAbstractScenarioBuilder(unittest.TestCase):
    """
    A class to test the MockAbstractScenarioBuilder utility class.
    """

    def test_mock_abstract_scenario_builder_implements_abstract_scenario_builder(self) -> None:
        """
        Tests that the mock abstract scenario builder class properly implements the interface.
        """
        assert_class_properly_implements_interface(AbstractScenarioBuilder, MockAbstractScenarioBuilder)

def test_mock_abstract_scenario_builder_implements_abstract_scenario_builder(self) -> None:
    """
        Tests that the mock abstract scenario builder class properly implements the interface.
        """
    assert_class_properly_implements_interface(AbstractScenarioBuilder, MockAbstractScenarioBuilder)

class TestNuPlanScenarioBuilder(unittest.TestCase):
    """
    Tests scenario filtering and construction functionality.
    """

    def test_nuplan_scenario_builder_implements_abstract_scenario_builder(self) -> None:
        """
        Tests that the NuPlanScenarioBuilder implements the AbstractScenarioBuilder interface.
        """
        assert_class_properly_implements_interface(AbstractScenarioBuilder, NuPlanScenarioBuilder)

    def test_get_scenarios_no_filters(self) -> None:
        """
        Tests that the get_scenarios() method functions properly
        With no additional filters applied.
        """

        def db_file_patch(params: GetScenariosFromDbFileParams) -> ScenarioDict:
            """
            A patch for the get_scenarios_from_db_file method that validates the input args.
            """
            self.assertIsNone(params.filter_tokens)
            self.assertIsNone(params.filter_types)
            self.assertIsNone(params.filter_map_names)
            self.assertFalse(params.include_cameras)
            m1 = MockNuPlanScenario(token='a', scenario_type='type1')
            m2 = MockNuPlanScenario(token='b', scenario_type='type1')
            m3 = MockNuPlanScenario(token='c', scenario_type='type2')
            return {'type1': [m1, m2], 'type2': [m3]}

        def discover_log_dbs_patch(load_path: Union[List[str], str]) -> List[str]:
            """
            A patch for the discover_log_dbs method.
            """
            return ['filename']
        with mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_filter_utils.get_scenarios_from_db_file', db_file_patch), mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_builder.discover_log_dbs', discover_log_dbs_patch):
            scenario_builder = NuPlanScenarioBuilder(data_root='foo', map_root='bar', sensor_root='qux', db_files=None, map_version='baz', max_workers=None, verbose=False, scenario_mapping=None, vehicle_parameters=None, include_cameras=False)
            scenario_filter = ScenarioFilter(scenario_types=None, scenario_tokens=None, log_names=None, map_names=None, num_scenarios_per_type=None, limit_total_scenarios=None, expand_scenarios=False, remove_invalid_goals=False, shuffle=False, timestamp_threshold_s=None, ego_displacement_minimum_m=None, ego_start_speed_threshold=None, ego_stop_speed_threshold=None, speed_noise_tolerance=None, token_set_path=None, fraction_in_token_set_threshold=None)
            result = scenario_builder.get_scenarios(scenario_filter, Sequential())
            self.assertEqual(3, len(result))
            result.sort(key=lambda s: s.token)
            self.assertEqual('a', result[0].token)
            self.assertEqual('b', result[1].token)
            self.assertEqual('c', result[2].token)

    def test_get_scenarios_db_filters(self) -> None:
        """
        Tests that the get_scenarios() method functions properly with db filters applied.
        """

        def db_file_patch(params: GetScenariosFromDbFileParams) -> ScenarioDict:
            """
            A patch for the get_scenarios_from_db_file method.
            """
            self.assertEqual(params.filter_tokens, ['a', 'b', 'c', 'd', 'e', 'f'])
            self.assertEqual(params.filter_types, ['type1', 'type2', 'type3'])
            self.assertEqual(params.filter_map_names, ['map1', 'map2'])
            self.assertTrue(params.include_cameras)
            self.assertTrue(params.log_file_absolute_path in ['filename1', 'filename2'])
            m1 = MockNuPlanScenario(token='a', scenario_type='type1')
            m2 = MockNuPlanScenario(token='b', scenario_type='type1')
            m3 = MockNuPlanScenario(token='c', scenario_type='type2')
            return {'type1': [m1, m2], 'type2': [m3]}

        def discover_log_dbs_patch(load_path: Union[List[str], str]) -> List[str]:
            """
            A patch for the discover_log_dbs method.
            """
            return ['filename1', 'filename2', 'filename3']
        with mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_filter_utils.get_scenarios_from_db_file', db_file_patch), mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_builder.discover_log_dbs', discover_log_dbs_patch):
            scenario_builder = NuPlanScenarioBuilder(data_root='foo', map_root='bar', sensor_root='qux', db_files=None, map_version='baz', max_workers=None, verbose=False, scenario_mapping=None, vehicle_parameters=None, include_cameras=True)
            scenario_filter = ScenarioFilter(scenario_types=['type1', 'type2', 'type3'], scenario_tokens=['a', 'b', 'c', 'd', 'e', 'f'], log_names=['filename1', 'filename2'], map_names=['map1', 'map2'], num_scenarios_per_type=None, limit_total_scenarios=None, expand_scenarios=False, remove_invalid_goals=False, shuffle=False, timestamp_threshold_s=None, ego_displacement_minimum_m=None, ego_start_speed_threshold=None, ego_stop_speed_threshold=None, speed_noise_tolerance=None, token_set_path=None, fraction_in_token_set_threshold=None)
            result = scenario_builder.get_scenarios(scenario_filter, Sequential())
            self.assertEqual(6, len(result))
            result.sort(key=lambda s: s.token)
            self.assertEqual('a', result[0].token)
            self.assertEqual('a', result[1].token)
            self.assertEqual('b', result[2].token)
            self.assertEqual('b', result[3].token)
            self.assertEqual('c', result[4].token)
            self.assertEqual('c', result[5].token)

    def test_get_scenarios_num_scenarios_per_type_filter(self) -> None:
        """
        Tests that the get_scenarios() method functions properly
        With a num_scenarios_per_type filter applied.
        """

        def db_file_patch(params: GetScenariosFromDbFileParams) -> ScenarioDict:
            """
            A patch for the get_scenarios_from_db_file method
            """
            self.assertEqual(params.filter_tokens, ['a', 'b', 'c', 'd', 'e', 'f'])
            self.assertEqual(params.filter_types, ['type1', 'type2', 'type3'])
            self.assertEqual(params.filter_map_names, ['map1', 'map2'])
            self.assertEqual(params.include_cameras, False)
            self.assertTrue(params.log_file_absolute_path in ['filename1', 'filename2'])
            m1 = MockNuPlanScenario(token='a', scenario_type='type1')
            m2 = MockNuPlanScenario(token='b', scenario_type='type1')
            m3 = MockNuPlanScenario(token='c', scenario_type='type2')
            return {'type1': [m1, m2], 'type2': [m3]}

        def discover_log_dbs_patch(load_path: Union[List[str], str]) -> List[str]:
            """
            A patch for the discover_log_dbs method
            """
            return ['filename1', 'filename2', 'filename3']
        with mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_filter_utils.get_scenarios_from_db_file', db_file_patch), mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_builder.discover_log_dbs', discover_log_dbs_patch):
            scenario_builder = NuPlanScenarioBuilder(data_root='foo', map_root='bar', sensor_root='qux', db_files=None, map_version='baz', max_workers=None, verbose=False, scenario_mapping=None, vehicle_parameters=None, include_cameras=False)
            scenario_filter = ScenarioFilter(scenario_types=['type1', 'type2', 'type3'], scenario_tokens=['a', 'b', 'c', 'd', 'e', 'f'], log_names=['filename1', 'filename2'], map_names=['map1', 'map2'], num_scenarios_per_type=2, limit_total_scenarios=None, expand_scenarios=False, remove_invalid_goals=False, shuffle=False, timestamp_threshold_s=None, ego_displacement_minimum_m=None, ego_start_speed_threshold=None, ego_stop_speed_threshold=None, speed_noise_tolerance=None, token_set_path=None, fraction_in_token_set_threshold=None)
            result = scenario_builder.get_scenarios(scenario_filter, Sequential())
            self.assertEqual(4, len(result))
            self.assertEqual(2, sum((1 if s.scenario_type == 'type1' else 0 for s in result)))
            self.assertEqual(2, sum((1 if s.scenario_type == 'type2' else 0 for s in result)))

    def test_get_scenarios_total_num_scenarios_filter(self) -> None:
        """
        Tests that the get_scenarios() method functions properly
        With a total_num_scenarios filter.
        """

        def db_file_patch(params: GetScenariosFromDbFileParams) -> ScenarioDict:
            """
            A patch for the get_scenarios_from_db_file method
            """
            self.assertEqual(params.filter_tokens, ['a', 'b', 'c', 'd', 'e', 'f'])
            self.assertEqual(params.filter_types, ['type1', 'type2', 'type3'])
            self.assertEqual(params.filter_map_names, ['map1', 'map2'])
            self.assertFalse(params.include_cameras)
            self.assertTrue(params.log_file_absolute_path in ['filename1', 'filename2'])
            m1 = MockNuPlanScenario(token='a', scenario_type='type1')
            m2 = MockNuPlanScenario(token='b', scenario_type='type1')
            m3 = MockNuPlanScenario(token='c', scenario_type='type2')
            return {'type1': [m1, m2], 'type2': [m3]}

        def discover_log_dbs_patch(load_path: Union[List[str], str]) -> List[str]:
            """
            A patch for the discover_log_dbs method
            """
            return ['filename1', 'filename2', 'filename3']
        with mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_filter_utils.get_scenarios_from_db_file', db_file_patch), mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_builder.discover_log_dbs', discover_log_dbs_patch):
            scenario_builder = NuPlanScenarioBuilder(data_root='foo', map_root='bar', sensor_root='qux', db_files=None, map_version='baz', max_workers=None, verbose=False, scenario_mapping=None, vehicle_parameters=None, include_cameras=False)
            scenario_filter = ScenarioFilter(scenario_types=['type1', 'type2', 'type3'], scenario_tokens=['a', 'b', 'c', 'd', 'e', 'f'], log_names=['filename1', 'filename2'], map_names=['map1', 'map2'], num_scenarios_per_type=None, limit_total_scenarios=5, expand_scenarios=False, remove_invalid_goals=False, shuffle=False, timestamp_threshold_s=None, ego_displacement_minimum_m=None, ego_start_speed_threshold=None, ego_stop_speed_threshold=None, speed_noise_tolerance=None, token_set_path=None, fraction_in_token_set_threshold=None)
            result = scenario_builder.get_scenarios(scenario_filter, Sequential())
            self.assertEqual(5, len(result))

def test_nuplan_scenario_builder_implements_abstract_scenario_builder(self) -> None:
    """
        Tests that the NuPlanScenarioBuilder implements the AbstractScenarioBuilder interface.
        """
    assert_class_properly_implements_interface(AbstractScenarioBuilder, NuPlanScenarioBuilder)

class TestNuPlanScenario(unittest.TestCase):
    """
    Tests scenario for NuPlan
    """

    def _make_test_scenario(self) -> NuPlanScenario:
        """
        Creates a sample scenario to use for testing.
        """
        return NuPlanScenario(data_root='data_root/', log_file_load_path='data_root/log_name.db', initial_lidar_token=int_to_str_token(1234), initial_lidar_timestamp=2345, scenario_type='scenario_type', map_root='map_root', map_version='map_version', map_name='map_name', scenario_extraction_info=ScenarioExtractionInfo(scenario_name='scenario_name', scenario_duration=20, extraction_offset=1, subsample_ratio=0.5), ego_vehicle_parameters=get_pacifica_parameters(), sensor_root='sensor_root')

    def _get_sampled_sensor_tokens_in_time_window_patch(self, expected_log_file: str, expected_sensor_data_source: SensorDataSource, expected_start_timestamp: int, expected_end_timestamp: int, expected_subsample_step: int) -> Callable[[str, SensorDataSource, int, int, int], Generator[str, None, None]]:
        """
        Creates a patch for the get_sampled_lidarpc_tokens_in_time_window function that validates the arguments.
        :param expected_log_file: The log file name with which the function is expected to be called.
        :param expected_start_timestamp: The expected start timestamp with which the function is expected to be called.
        :param expected_end_timestamp: The expected end timestamp with which the function is expected to be called.
        :param expected_subsample_step: The expected subsample step with which the function is expected to be called.
        :return: The patch function.
        """

        def fxn(actual_log_file: str, actual_sensor_data_source: SensorDataSource, actual_start_timestamp: int, actual_end_timestamp: int, actual_subsample_step: int) -> Generator[str, None, None]:
            """
            The patch function for get_sampled_lidarpc_tokens_in_time_window.
            """
            self.assertEqual(expected_log_file, actual_log_file)
            self.assertEqual(expected_sensor_data_source, actual_sensor_data_source)
            self.assertEqual(expected_start_timestamp, actual_start_timestamp)
            self.assertEqual(expected_end_timestamp, actual_end_timestamp)
            self.assertEqual(expected_subsample_step, actual_subsample_step)
            num_tokens = int((expected_end_timestamp - expected_start_timestamp) / (expected_subsample_step * 1000000.0))
            for token in range(num_tokens):
                yield int_to_str_token(token)
        return fxn

    def _get_download_file_if_necessary_patch(self, expected_data_root: str, expected_log_file_load_path: str) -> Callable[[str, str], str]:
        """
        Creates a patch for the download_file_if_necessary function that validates the arguments.
        :param expected_data_root: The data_root with which the function is expected to be called.
        :param expected_log_file_load_path: The log_file_load_path with which the function is expected to be called.
        :return: The patch function.
        """

        def fxn(actual_data_root: str, actual_log_file_load_path: str) -> str:
            """
            The generated patch function.
            """
            self.assertEqual(expected_data_root, actual_data_root)
            self.assertEqual(expected_log_file_load_path, actual_log_file_load_path)
            return actual_log_file_load_path
        return fxn

    def _get_sensor_data_from_sensor_data_tokens_from_db_patch(self, expected_log_file: str, expected_sensor_data_source: SensorDataSource, expected_sensor_class: Type[SensorDataTableRow], expected_tokens: List[str]) -> Callable[[str, SensorDataSource, Type[SensorDataTableRow], List[str]], Generator[SensorDataTableRow, None, None]]:
        """
        Creates a patch for the get_images_from_lidar_tokens_patch function that validates the arguments.
        :param expected_log_file: The log file name with which the function is expected to be called.
        :param expected_sensor_data_source: The sensor source with which the function is expected to be called.
        :param expected_sensor_class: The sensor class with which the function is expected to be called.
        :param expected_tokens: The tokens with which the function is expected to be called.
        :return: The patch function.
        """

        def fxn(actual_log_file: str, actual_sensor_data_source: SensorDataSource, actual_sensor_class: Type[SensorDataTableRow], actual_tokens: List[str]) -> Generator[SensorDataTableRow, None, None]:
            """
            The patch function for get_sensor_data_from_sensor_data_tokens_from_db.
            """
            self.assertEqual(expected_log_file, actual_log_file)
            self.assertEqual(expected_sensor_data_source, actual_sensor_data_source)
            self.assertEqual(expected_sensor_class, actual_sensor_class)
            self.assertEqual(expected_tokens, actual_tokens)
            lidar_token = actual_tokens[0]
            if expected_sensor_class == LidarPc:
                yield LidarPc(token=lidar_token, next_token=lidar_token, prev_token=lidar_token, ego_pose_token=lidar_token, lidar_token=lidar_token, scene_token=lidar_token, filename=f'lidar_{lidar_token}', timestamp=str_token_to_int(lidar_token))
            elif expected_sensor_class == ImageDBRow.Image:
                camera_token = str_token_to_int(lidar_token) + CAMERA_OFFSET
                yield ImageDBRow.Image(token=int_to_str_token(camera_token), next_token=int_to_str_token(camera_token), prev_token=int_to_str_token(camera_token), ego_pose_token=int_to_str_token(camera_token), camera_token=int_to_str_token(camera_token), filename_jpg=f'image_{camera_token}', timestamp=camera_token, channel=CameraChannel.CAM_R0.value)
            else:
                self.fail(f'Unexpected type: {expected_sensor_class}.')
        return fxn

    def _load_point_cloud_patch(self, expected_lidar_pc: LidarPc, expected_local_store: LocalStore, expected_s3_store: S3Store) -> Callable[[LidarPc, LocalStore, S3Store], LidarPointCloud]:
        """
        Creates a patch for the _load_point_cloud function that validates the arguments.
        :param expected_lidar_pc: The lidar pc with which the function is expected to be called.
        :param expected_local_store: The LocalStore with which the function is expected to be called.
        :param expected_s3_store: The S3Store with which the function is expected to be called.
        :return: The patch function.
        """

        def fxn(actual_lidar_pc: LidarPc, actual_local_store: LocalStore, actual_s3_store: S3Store) -> LidarPointCloud:
            """
            The patch function for load_point_cloud.
            """
            self.assertEqual(expected_lidar_pc, actual_lidar_pc)
            self.assertEqual(expected_local_store, actual_local_store)
            self.assertEqual(expected_s3_store, actual_s3_store)
            return LidarPointCloud(np.eye(3))
        return fxn

    def _load_image_patch(self, expected_local_store: LocalStore, expected_s3_store: S3Store) -> Callable[[ImageDBRow.Image, LocalStore, S3Store], Image]:
        """
        Creates a patch for the _load_image_patch function and validates that argument is an Image object.
        :param expected_local_store: The LocalStore with which the function is expected to be called.
        :param expected_s3_store: The S3Store with which the function is expected to be called.
        :return: The patch function.
        """

        def fxn(actual_image: ImageDBRow.Image, actual_local_store: LocalStore, actual_s3_store: S3Store) -> Image:
            """
            The patch function for load_image.
            """
            self.assertEqual(expected_local_store, actual_local_store)
            self.assertEqual(expected_s3_store, actual_s3_store)
            self.assertTrue(isinstance(actual_image, ImageDBRow.Image))
            return Image(PilImg.new('RGB', (500, 500)))
        return fxn

    def _get_images_from_lidar_tokens_patch(self, expected_log_file: str, expected_tokens: List[str], expected_channels: List[str], expected_lookahead_window_us: int, expected_lookback_window_us: int) -> Callable[[str, List[str], List[str], int, int], Generator[ImageDBRow.Image, None, None]]:
        """
        Creates a patch for the get_images_from_lidar_tokens_patch function that validates the arguments.
        :param expected_log_file: The log file name with which the function is expected to be called.
        :param expected_tokens: The expected tokens with which the function is expected to be called.
        :param expected_channels: The expected channels with which the function is expected to be called.
        :param expected_lookahead_window_us: The expected lookahead window with which the function is expected to be called.
        :param expected_lookahead_window_us: The expected lookback window with which the function is expected to be called.
        :return: The patch function.
        """

        def fxn(actual_log_file: str, actual_tokens: List[str], actual_channels: List[str], actual_lookahead_window_us: int=50000, actual_lookback_window_us: int=50000) -> Generator[ImageDBRow.Image, None, None]:
            """
            The patch function for get_images_from_lidar_tokens.
            """
            self.assertEqual(expected_log_file, actual_log_file)
            self.assertEqual(expected_tokens, actual_tokens)
            self.assertEqual(expected_channels, actual_channels)
            self.assertEqual(expected_lookahead_window_us, actual_lookahead_window_us)
            self.assertEqual(expected_lookback_window_us, actual_lookback_window_us)
            for camera_token, channel in enumerate(actual_channels):
                if channel != LidarChannel.MERGED_PC.value:
                    yield ImageDBRow.Image(token=int_to_str_token(camera_token), next_token=int_to_str_token(camera_token), prev_token=int_to_str_token(camera_token), ego_pose_token=int_to_str_token(camera_token), camera_token=int_to_str_token(camera_token), filename_jpg=f'image_{camera_token}', timestamp=camera_token, channel=channel)
        return fxn

    def _get_sampled_lidarpcs_from_db_patch(self, expected_log_file: str, expected_initial_token: str, expected_sensor_data_source: SensorDataSource, expected_sample_indexes: Union[Generator[int, None, None], List[int]], expected_future: bool) -> Callable[[str, str, SensorDataSource, Union[Generator[int, None, None], List[int]], bool], Generator[LidarPc, None, None]]:
        """
        Creates a patch for the get_sampled_lidarpcs_from_db function that validates the arguments.
        :param expected_log_file: The log file name with which the function is expected to be called.
        :param expected_initial_token: The initial token name with which the function is expected to be called.
        :param expected_sensor_data_source: The sensor source with which the function is expected to be called.
        :param expected_sample_indexes: The sample indexes with which the function is expected to be called.
        :param expected_future: The future with which the function is expected to be called.
        :return: The patch function.
        """

        def fxn(actual_log_file: str, actual_initial_token: str, actual_sensor_data_source: SensorDataSource, actual_sample_indexes: Union[Generator[int, None, None], List[int]], actual_future: bool) -> Generator[LidarPc, None, None]:
            """
            The patch function for get_images_from_lidar_tokens.
            """
            self.assertEqual(expected_log_file, actual_log_file)
            self.assertEqual(expected_initial_token, actual_initial_token)
            self.assertEqual(expected_sensor_data_source, actual_sensor_data_source)
            self.assertEqual(expected_sample_indexes, actual_sample_indexes)
            self.assertEqual(expected_future, actual_future)
            for idx in actual_sample_indexes:
                lidar_token = int_to_str_token(idx)
                yield LidarPc(token=lidar_token, next_token=lidar_token, prev_token=lidar_token, ego_pose_token=lidar_token, lidar_token=lidar_token, scene_token=lidar_token, filename=f'lidar_{lidar_token}', timestamp=str_token_to_int(lidar_token))
        return fxn

    def test_implements_abstract_scenario_interface(self) -> None:
        """
        Tests that NuPlanScenario properly implements AbstractScenario interface.
        """
        assert_class_properly_implements_interface(AbstractScenario, NuPlanScenario)

    def test_token(self) -> None:
        """
        Tests that the token method works properly.
        """
        download_file_patch_fxn = self._get_download_file_if_necessary_patch(expected_data_root='data_root/', expected_log_file_load_path='data_root/log_name.db')
        with mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario.download_file_if_necessary', download_file_patch_fxn):
            scenario = self._make_test_scenario()
            self.assertEqual(int_to_str_token(1234), scenario.token)

    def test_log_name(self) -> None:
        """
        Tests that the log_name method works properly.
        """
        download_file_patch_fxn = self._get_download_file_if_necessary_patch(expected_data_root='data_root/', expected_log_file_load_path='data_root/log_name.db')
        with mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario.download_file_if_necessary', download_file_patch_fxn):
            scenario = self._make_test_scenario()
            self.assertEqual('log_name', scenario.log_name)

    def test_scenario_name(self) -> None:
        """
        Tests that the scenario_name method works properly.
        """
        download_file_patch_fxn = self._get_download_file_if_necessary_patch(expected_data_root='data_root/', expected_log_file_load_path='data_root/log_name.db')
        with mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario.download_file_if_necessary', download_file_patch_fxn):
            scenario = self._make_test_scenario()
            self.assertEqual(int_to_str_token(1234), scenario.scenario_name)

    def test_ego_vehicle_parameters(self) -> None:
        """
        Tests that the ego_vehicle_parameters method works properly.
        """
        download_file_patch_fxn = self._get_download_file_if_necessary_patch(expected_data_root='data_root/', expected_log_file_load_path='data_root/log_name.db')
        with mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario.download_file_if_necessary', download_file_patch_fxn):
            scenario = self._make_test_scenario()
            self.assertEqual(get_pacifica_parameters(), scenario.ego_vehicle_parameters)

    def test_scenario_type(self) -> None:
        """
        Tests that the scenario_type method works properly
        """
        download_file_patch_fxn = self._get_download_file_if_necessary_patch(expected_data_root='data_root/', expected_log_file_load_path='data_root/log_name.db')
        with mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario.download_file_if_necessary', download_file_patch_fxn):
            scenario = self._make_test_scenario()
            self.assertEqual('scenario_type', scenario.scenario_type)

    def test_database_interval(self) -> None:
        """
        Tests that the database_interval method works properly
        """
        download_file_patch_fxn = self._get_download_file_if_necessary_patch(expected_data_root='data_root/', expected_log_file_load_path='data_root/log_name.db')
        with mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario.download_file_if_necessary', download_file_patch_fxn):
            scenario = self._make_test_scenario()
            self.assertEqual(0.1, scenario.database_interval)

    def test_get_number_of_iterations(self) -> None:
        """
        Tests that the get_number_of_iterations method works properly
        """
        lidarpc_tokens_patch_fxn = self._get_sampled_sensor_tokens_in_time_window_patch(expected_log_file='data_root/log_name.db', expected_sensor_data_source=get_lidarpc_sensor_data(), expected_start_timestamp=int(1 * 1000000.0 + 2345), expected_end_timestamp=int(21 * 1000000.0 + 2345), expected_subsample_step=2)
        download_file_patch_fxn = self._get_download_file_if_necessary_patch(expected_data_root='data_root/', expected_log_file_load_path='data_root/log_name.db')
        with mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario.download_file_if_necessary', download_file_patch_fxn):
            with mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_utils.get_sampled_sensor_tokens_in_time_window_from_db', lidarpc_tokens_patch_fxn):
                scenario = self._make_test_scenario()
                self.assertEqual(10, scenario.get_number_of_iterations())

    def test_get_time_point(self) -> None:
        """
        Tests that the get_time_point method works properly
        """
        lidarpc_tokens_patch_fxn = self._get_sampled_sensor_tokens_in_time_window_patch(expected_log_file='data_root/log_name.db', expected_sensor_data_source=get_lidarpc_sensor_data(), expected_start_timestamp=int(1 * 1000000.0 + 2345), expected_end_timestamp=int(21 * 1000000.0 + 2345), expected_subsample_step=2)
        download_file_patch_fxn = self._get_download_file_if_necessary_patch(expected_data_root='data_root/', expected_log_file_load_path='data_root/log_name.db')
        for iter_val in [0, 3, 5]:

            def token_timestamp_patch(log_file: str, sensor_source: SensorDataSource, token: str) -> int:
                """
                The patch method for get_lidarpc_token_timstamp_from_db that validates the arguments.
                """
                self.assertEqual('data_root/log_name.db', log_file)
                self.assertEqual(SensorDataSource(table='lidar_pc', sensor_table='lidar', sensor_token_column='lidar_token', channel='MergedPointCloud'), sensor_source)
                self.assertEqual(int_to_str_token(iter_val), token)
                return int(str_token_to_int(iter_val) + 5)
            with mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario.download_file_if_necessary', download_file_patch_fxn), mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_utils.get_sampled_sensor_tokens_in_time_window_from_db', lidarpc_tokens_patch_fxn), mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario.get_sensor_data_token_timestamp_from_db', token_timestamp_patch):
                scenario = self._make_test_scenario()
                self.assertEqual(iter_val + 5, scenario.get_time_point(iter_val).time_us)

    def test_get_tracked_objects_at_iteration(self) -> None:
        """
        Tests that the get_tracked_objects_at_iteration method works properly
        """
        lidarpc_tokens_patch_fxn = self._get_sampled_sensor_tokens_in_time_window_patch(expected_log_file='data_root/log_name.db', expected_sensor_data_source=get_lidarpc_sensor_data(), expected_start_timestamp=int(1 * 1000000.0 + 2345), expected_end_timestamp=int(21 * 1000000.0 + 2345), expected_subsample_step=2)
        download_file_patch_fxn = self._get_download_file_if_necessary_patch(expected_data_root='data_root/', expected_log_file_load_path='data_root/log_name.db')
        ground_truth_predictions = TrajectorySampling(num_poses=10, time_horizon=5, interval_length=None)
        for iter_val in [0, 2, 3]:

            def get_token_timestamp_patch(log_file: str, sensor_source: SensorDataSource, token: str) -> int:
                """
                The patch for get_sensor_data_token_timestamp_from_db that validates the arguments and generates fake data.
                """
                self.assertEqual('data_root/log_name.db', log_file)
                self.assertEqual(SensorDataSource(table='lidar_pc', sensor_table='lidar', sensor_token_column='lidar_token', channel='MergedPointCloud'), sensor_source)
                self.assertEqual(int_to_str_token(iter_val), token)
                return int(iter_val * 1000000.0)

            def tracked_objects_for_token_patch(log_file: str, token: str) -> Generator[TrackedObject, None, None]:
                """
                The patch for get_tracked_objects_for_lidarpc_token that validates the arguments and generates fake data.
                """
                self.assertEqual('data_root/log_name.db', log_file)
                self.assertEqual(int_to_str_token(iter_val), token)
                for idx in range(0, 4, 1):
                    box = OrientedBox(center=StateSE2(x=10, y=10, heading=10), length=10, width=10, height=10)
                    metadata = SceneObjectMetadata(token=int_to_str_token(idx + str_token_to_int(token)), track_token=int_to_str_token(idx + str_token_to_int(token) + 100), track_id=None, timestamp_us=0, category_name='foo')
                    if idx < 2:
                        yield Agent(tracked_object_type=TrackedObjectType.VEHICLE, oriented_box=box, velocity=StateVector2D(x=10, y=10), metadata=metadata)
                    else:
                        yield StaticObject(tracked_object_type=TrackedObjectType.CZONE_SIGN, oriented_box=box, metadata=metadata)

            def interpolate_future_waypoints_patch(waypoints: List[InterpolatableState], time_horizon: float, interval_s: float) -> List[Optional[InterpolatableState]]:
                """
                The patch for interpolate_future_waypoints that validates the arguments and generates fake data.
                """
                self.assertEqual(4, len(waypoints))
                self.assertEqual(0.5, interval_s)
                self.assertEqual(5, time_horizon)
                return waypoints

            def future_waypoints_for_agents_patch(log_file: str, agents_tokens: List[str], start_time: int, end_time: int) -> Generator[Tuple[str, Waypoint], None, None]:
                """
                The patch for get_future_waypoints_for_agents_from_db that validates the arguments and generates fake data.
                """
                self.assertEqual('data_root/log_name.db', log_file)
                self.assertEqual(iter_val * 1000000.0, start_time)
                self.assertEqual((iter_val + 5.5) * 1000000.0, end_time)
                self.assertEqual(2, len(agents_tokens))
                check_tokens = [str_token_to_int(t) for t in agents_tokens]
                check_tokens.sort()
                self.assertEqual(iter_val + 100, check_tokens[0])
                self.assertEqual(iter_val + 100 + 1, check_tokens[1])
                for i in range(8):
                    waypoint = Waypoint(time_point=TimePoint(time_us=i), oriented_box=OrientedBox(center=StateSE2(x=i, y=i, heading=i), length=i, width=i, height=i), velocity=None)
                    token = check_tokens[0] if i < 4 else check_tokens[1]
                    yield (int_to_str_token(token), waypoint)
            with mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario.download_file_if_necessary', download_file_patch_fxn), mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_utils.get_sampled_sensor_tokens_in_time_window_from_db', lidarpc_tokens_patch_fxn), mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_utils.get_tracked_objects_for_lidarpc_token_from_db', tracked_objects_for_token_patch), mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_utils.get_future_waypoints_for_agents_from_db', future_waypoints_for_agents_patch), mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_utils.get_sensor_data_token_timestamp_from_db', get_token_timestamp_patch), mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_utils.interpolate_future_waypoints', interpolate_future_waypoints_patch):
                scenario = self._make_test_scenario()
                agents = scenario.get_tracked_objects_at_iteration(iter_val, ground_truth_predictions)
                objects = agents.tracked_objects.tracked_objects
                self.assertEqual(4, len(objects))
                objects.sort(key=lambda x: str_token_to_int(x.metadata.token))
                for i in range(0, 2, 1):
                    test_obj = objects[i]
                    self.assertTrue(isinstance(test_obj, Agent))
                    self.assertEqual(iter_val + i, str_token_to_int(test_obj.metadata.token))
                    self.assertEqual(iter_val + i + 100, str_token_to_int(test_obj.metadata.track_token))
                    self.assertEqual(TrackedObjectType.VEHICLE, test_obj.tracked_object_type)
                    self.assertIsNotNone(test_obj.predictions)
                    object_waypoints = test_obj.predictions[0].waypoints
                    self.assertEqual(4, len(object_waypoints))
                    for j in range(len(object_waypoints)):
                        self.assertEqual(j + i * len(object_waypoints), object_waypoints[j].x)
                for i in range(2, 4, 1):
                    test_obj = objects[i]
                    self.assertTrue(isinstance(test_obj, StaticObject))
                    self.assertEqual(iter_val + i, str_token_to_int(test_obj.metadata.token))
                    self.assertEqual(iter_val + i + 100, str_token_to_int(test_obj.metadata.track_token))
                    self.assertEqual(TrackedObjectType.CZONE_SIGN, test_obj.tracked_object_type)

    def test_get_tracked_objects_within_time_window_at_iteration(self) -> None:
        """
        Tests that the get_tracked_objects_within_time_window_at_iteration method works properly
        """
        lidarpc_tokens_patch_fxn = self._get_sampled_sensor_tokens_in_time_window_patch(expected_log_file='data_root/log_name.db', expected_sensor_data_source=get_lidarpc_sensor_data(), expected_start_timestamp=int(1 * 1000000.0 + 2345), expected_end_timestamp=int(21 * 1000000.0 + 2345), expected_subsample_step=2)
        download_file_patch_fxn = self._get_download_file_if_necessary_patch(expected_data_root='data_root/', expected_log_file_load_path='data_root/log_name.db')
        ground_truth_predictions = TrajectorySampling(num_poses=10, time_horizon=5, interval_length=None)
        for iter_val in [3, 4]:

            def get_token_timestamp_patch(log_file: str, sensor_source: SensorDataSource, token: str) -> int:
                """
                The patch for get_sensor_data_token_timestamp_from_db that validates the arguments and generates fake data.
                """
                self.assertEqual('data_root/log_name.db', log_file)
                self.assertEqual(SensorDataSource(table='lidar_pc', sensor_table='lidar', sensor_token_column='lidar_token', channel='MergedPointCloud'), sensor_source)
                self.assertEqual(int_to_str_token(iter_val), token)
                return int(iter_val * 1000000.0)

            def tracked_objects_within_time_interval_patch(log_file: str, start_timestamp: int, end_timestamp: int, filter_tokens: Optional[Set[str]]) -> Generator[TrackedObject, None, None]:
                """
                The patch for get_tracked_objects_for_lidarpc_token that validates the arguments and generates fake data.
                """
                self.assertEqual('data_root/log_name.db', log_file)
                self.assertEqual((iter_val - 2) * 1000000.0, start_timestamp)
                self.assertEqual((iter_val + 2) * 1000000.0, end_timestamp)
                self.assertIsNone(filter_tokens)
                for time_idx in range(-2, 3, 1):
                    for idx in range(0, 4, 1):
                        box = OrientedBox(center=StateSE2(x=10, y=10, heading=10), length=10, width=10, height=10)
                        metadata = SceneObjectMetadata(token=int_to_str_token(idx + iter_val), track_token=int_to_str_token(idx + iter_val + 100), track_id=None, timestamp_us=(iter_val + time_idx) * 1000000.0, category_name='foo')
                        if idx < 2:
                            yield Agent(tracked_object_type=TrackedObjectType.VEHICLE, oriented_box=box, velocity=StateVector2D(x=10, y=10), metadata=metadata)
                        else:
                            yield StaticObject(tracked_object_type=TrackedObjectType.CZONE_SIGN, oriented_box=box, metadata=metadata)

            def interpolate_future_waypoints_patch(waypoints: List[InterpolatableState], time_horizon: float, interval_s: float) -> List[Optional[InterpolatableState]]:
                """
                The patch for interpolate_future_waypoints that validates the arguments and generates fake data.
                """
                self.assertEqual(4, len(waypoints))
                self.assertEqual(0.5, interval_s)
                self.assertEqual(5, time_horizon)
                return waypoints

            def future_waypoints_for_agents_patch(log_file: str, agents_tokens: List[str], start_time: int, end_time: int) -> Generator[Tuple[str, Waypoint], None, None]:
                """
                The patch for get_future_waypoints_for_agents_from_db that validates the arguments and generates fake data.
                """
                self.assertEqual('data_root/log_name.db', log_file)
                self.assertEqual(end_time - start_time, 5.5 * 1000000.0)
                self.assertEqual(2, len(agents_tokens))
                check_tokens = [str_token_to_int(t) for t in agents_tokens]
                check_tokens.sort()
                self.assertEqual(iter_val + 100, check_tokens[0])
                self.assertEqual(iter_val + 100 + 1, check_tokens[1])
                for i in range(8):
                    waypoint = Waypoint(time_point=TimePoint(time_us=i), oriented_box=OrientedBox(center=StateSE2(x=i, y=i, heading=i), length=i, width=i, height=i), velocity=None)
                    token = check_tokens[0] if i < 4 else check_tokens[1]
                    yield (int_to_str_token(token), waypoint)
            with mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario.download_file_if_necessary', download_file_patch_fxn), mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_utils.get_sampled_sensor_tokens_in_time_window_from_db', lidarpc_tokens_patch_fxn), mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_utils.get_tracked_objects_within_time_interval_from_db', tracked_objects_within_time_interval_patch), mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_utils.get_future_waypoints_for_agents_from_db', future_waypoints_for_agents_patch), mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_utils.get_sensor_data_token_timestamp_from_db', get_token_timestamp_patch), mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_utils.interpolate_future_waypoints', interpolate_future_waypoints_patch):
                scenario = self._make_test_scenario()
                agents = scenario.get_tracked_objects_within_time_window_at_iteration(iter_val, 2, 2, future_trajectory_sampling=ground_truth_predictions)
                objects = agents.tracked_objects.tracked_objects
                self.assertEqual(20, len(objects))
                num_objects = 2
                for window in range(0, 5, 1):
                    for object_num in range(0, 2, 1):
                        start_agent_idx = window * 2
                        test_obj = objects[start_agent_idx + object_num]
                        self.assertTrue(isinstance(test_obj, Agent))
                        self.assertEqual(iter_val + object_num, str_token_to_int(test_obj.metadata.token))
                        self.assertEqual(iter_val + object_num + 100, str_token_to_int(test_obj.metadata.track_token))
                        self.assertEqual(TrackedObjectType.VEHICLE, test_obj.tracked_object_type)
                        self.assertIsNotNone(test_obj.predictions)
                        object_waypoints = test_obj.predictions[0].waypoints
                        self.assertEqual(4, len(object_waypoints))
                        for j in range(len(object_waypoints)):
                            self.assertEqual(j + object_num * len(object_waypoints), object_waypoints[j].x)
                        start_obj_idx = 10 + window * 2
                        test_obj = objects[start_obj_idx + object_num]
                        self.assertTrue(isinstance(test_obj, StaticObject))
                        self.assertEqual(iter_val + object_num + num_objects, str_token_to_int(test_obj.metadata.token))
                        self.assertEqual(iter_val + object_num + num_objects + 100, str_token_to_int(test_obj.metadata.track_token))
                        self.assertEqual(TrackedObjectType.CZONE_SIGN, test_obj.tracked_object_type)

    def test_nuplan_scenario_memory_usage(self) -> None:
        """
        Test that repeatedly creating and destroying nuplan scenario does not cause memory leaks.
        """
        starting_usage = 0
        ending_usage = 0
        num_iterations = 5
        download_file_patch_fxn = self._get_download_file_if_necessary_patch(expected_data_root='data_root/', expected_log_file_load_path='data_root/log_name.db')
        with mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario.download_file_if_necessary', download_file_patch_fxn):
            hpy = guppy.hpy()
            hpy.setrelheap()
            for i in range(0, num_iterations, 1):
                scenario = self._make_test_scenario()
                _ = scenario.token
                gc.collect()
                heap = hpy.heap()
                _ = heap.size
                if i == num_iterations - 2:
                    starting_usage = heap.size
                if i == num_iterations - 1:
                    ending_usage = heap.size
            memory_difference_in_mb = (ending_usage - starting_usage) / (1024 * 1024)
            max_allowable_growth_mb = max(0.1, 0.1 * starting_usage / (1024 * 1024))
            self.assertGreater(max_allowable_growth_mb, memory_difference_in_mb)

    @patch(f'{TEST_PATH}.LocalStore', autospec=True)
    @patch(f'{TEST_PATH}.S3Store', autospec=True)
    @patch(f'{TEST_PATH}.os.getenv')
    def test_get_sensors_at_iteration(self, mock_get_env: Mock, mock_s3_store: Mock, mock_local_store: Mock) -> None:
        """Test get_sensors_at_iteration."""
        mock_url = 'url'
        mock_get_env.side_effect = ['s3', mock_url]
        mock_s3_store.return_value = Mock(spec_set=S3Store)
        mock_local_store.return_value = Mock(spec_set=LocalStore)
        lidarpc_tokens_patch_fxn = self._get_sampled_sensor_tokens_in_time_window_patch(expected_log_file='data_root/log_name.db', expected_sensor_data_source=get_lidarpc_sensor_data(), expected_start_timestamp=int(1 * 1000000.0) + 2345, expected_end_timestamp=int(21 * 1000000.0) + 2345, expected_subsample_step=2)
        download_file_patch_fxn = self._get_download_file_if_necessary_patch(expected_data_root='data_root/', expected_log_file_load_path='data_root/log_name.db')
        with mock.patch(f'{TEST_PATH}.download_file_if_necessary', download_file_patch_fxn):
            scenario = self._make_test_scenario()
        for iter_val in [0, 3, 5]:
            lidar_token = int_to_str_token(iter_val)
            get_sensor_data_from_sensor_data_tokens_from_db_fxn = self._get_sensor_data_from_sensor_data_tokens_from_db_patch(expected_log_file='data_root/log_name.db', expected_sensor_data_source=get_lidarpc_sensor_data(), expected_sensor_class=LidarPc, expected_tokens=[lidar_token])
            get_images_from_lidar_tokens_fxn = self._get_images_from_lidar_tokens_patch(expected_log_file='data_root/log_name.db', expected_tokens=[lidar_token], expected_channels=[CameraChannel.CAM_R0.value, LidarChannel.MERGED_PC.value], expected_lookahead_window_us=50000, expected_lookback_window_us=50000)
            load_lidar_fxn = self._load_point_cloud_patch(LidarPc(token=lidar_token, next_token=lidar_token, prev_token=lidar_token, ego_pose_token=lidar_token, lidar_token=lidar_token, scene_token=lidar_token, filename=f'lidar_{lidar_token}', timestamp=str_token_to_int(lidar_token)), mock_local_store.return_value, mock_s3_store.return_value)
            load_image_fxn = self._load_image_patch(mock_local_store.return_value, mock_s3_store.return_value)
            with mock.patch(f'{TEST_PATH_UTILS}.get_sampled_sensor_tokens_in_time_window_from_db', lidarpc_tokens_patch_fxn), mock.patch(f'{TEST_PATH}.get_sensor_data_from_sensor_data_tokens_from_db', get_sensor_data_from_sensor_data_tokens_from_db_fxn), mock.patch(f'{TEST_PATH}.get_images_from_lidar_tokens', get_images_from_lidar_tokens_fxn), mock.patch(f'{TEST_PATH}.load_point_cloud', load_lidar_fxn), mock.patch(f'{TEST_PATH}.load_image', load_image_fxn):
                sensors = scenario.get_sensors_at_iteration(iter_val, [CameraChannel.CAM_R0, LidarChannel.MERGED_PC])
                self.assertEqual(LidarChannel.MERGED_PC, list(sensors.pointcloud.keys())[0])
                self.assertEqual(CameraChannel.CAM_R0, list(sensors.images.keys())[0])
                mock_local_store.assert_called_with('sensor_root')
                mock_s3_store.assert_called_with(f'{mock_url}/sensor_blobs', show_progress=True)

    @patch(f'{TEST_PATH}.LocalStore', autospec=True)
    @patch(f'{TEST_PATH}.S3Store', autospec=True)
    @patch(f'{TEST_PATH}.os.getenv')
    def test_get_past_sensors(self, mock_get_env: Mock, mock_s3_store: Mock, mock_local_store: Mock) -> None:
        """Test get_past_sensors."""
        mock_url = 'url'
        mock_get_env.side_effect = ['s3', mock_url]
        mock_s3_store.return_value = Mock(spec_set=S3Store)
        mock_local_store.return_value = Mock(spec_set=LocalStore)
        lidarpc_tokens_patch_fxn = self._get_sampled_sensor_tokens_in_time_window_patch(expected_log_file='data_root/log_name.db', expected_sensor_data_source=get_lidarpc_sensor_data(), expected_start_timestamp=int(1 * 1000000.0 + 2345), expected_end_timestamp=int(21 * 1000000.0 + 2345), expected_subsample_step=2)
        lidar_token = int_to_str_token(9)
        get_sampled_lidarpcs_from_db_fxn = self._get_sampled_lidarpcs_from_db_patch(expected_log_file='data_root/log_name.db', expected_initial_token=int_to_str_token(0), expected_sensor_data_source=get_lidarpc_sensor_data(), expected_sample_indexes=[9], expected_future=False)
        get_images_from_lidar_tokens_fxn = self._get_images_from_lidar_tokens_patch(expected_log_file='data_root/log_name.db', expected_tokens=[lidar_token], expected_channels=[CameraChannel.CAM_R0.value, LidarChannel.MERGED_PC.value], expected_lookahead_window_us=50000, expected_lookback_window_us=50000)
        download_file_patch_fxn = self._get_download_file_if_necessary_patch(expected_data_root='data_root/', expected_log_file_load_path='data_root/log_name.db')
        load_lidar_fxn = self._load_point_cloud_patch(LidarPc(token=lidar_token, next_token=lidar_token, prev_token=lidar_token, ego_pose_token=lidar_token, lidar_token=lidar_token, scene_token=lidar_token, filename=f'lidar_{lidar_token}', timestamp=str_token_to_int(lidar_token)), mock_local_store.return_value, mock_s3_store.return_value)
        load_image_fxn = self._load_image_patch(mock_local_store.return_value, mock_s3_store.return_value)
        with mock.patch(f'{TEST_PATH}.download_file_if_necessary', download_file_patch_fxn), mock.patch(f'{TEST_PATH_UTILS}.get_sampled_sensor_tokens_in_time_window_from_db', lidarpc_tokens_patch_fxn), mock.patch(f'{TEST_PATH}.get_sampled_lidarpcs_from_db', get_sampled_lidarpcs_from_db_fxn), mock.patch(f'{TEST_PATH}.get_images_from_lidar_tokens', get_images_from_lidar_tokens_fxn), mock.patch(f'{TEST_PATH}.load_point_cloud', load_lidar_fxn), mock.patch(f'{TEST_PATH}.load_image', load_image_fxn):
            scenario = self._make_test_scenario()
            past_sensors = list(scenario.get_past_sensors(iteration=0, time_horizon=0.4, num_samples=1, channels=[CameraChannel.CAM_R0, LidarChannel.MERGED_PC]))
            self.assertEqual(1, len(past_sensors))
            self.assertEqual(LidarChannel.MERGED_PC, list(past_sensors[0].pointcloud.keys())[0])
            self.assertEqual(CameraChannel.CAM_R0, list(past_sensors[0].images.keys())[0])
            mock_local_store.assert_called_with('sensor_root')
            mock_s3_store.assert_called_with(f'{mock_url}/sensor_blobs', show_progress=True)

    @patch(f'{TEST_PATH}.download_file_if_necessary', Mock())
    @patch(f'{TEST_PATH}.absolute_path_to_log_name', Mock())
    @patch(f'{TEST_PATH}.get_images_from_lidar_tokens', Mock(return_value=[]))
    @patch(f'{TEST_PATH}.NuPlanScenario._find_matching_lidar_pcs')
    @patch(f'{TEST_PATH}.load_point_cloud')
    @patch(f'{TEST_PATH}.load_image')
    def test_get_past_sensors_no_channels(self, mock_load_image: Mock, mock_load_point_cloud: Mock, mock__find_matching_lidar_pcs: Mock) -> None:
        """Test get_past_sensors when no channels are passed."""
        mock_lidar_pc = Mock(spec=LidarPc)
        mock_lidar_pc.token = 'token'
        mock_load_point_cloud.return_value = Mock(spec_set=LidarPointCloud)
        mock__find_matching_lidar_pcs.return_value = iter([mock_lidar_pc])
        scenario = self._make_test_scenario()
        past_sensors = list(scenario.get_past_sensors(iteration=0, time_horizon=0.4, num_samples=1, channels=None))
        mock__find_matching_lidar_pcs.assert_called_once()
        mock_load_point_cloud.assert_called_once()
        mock_load_image.assert_not_called()
        self.assertIsNone(past_sensors[0].images)
        self.assertIsNotNone(past_sensors[0].pointcloud)

    @patch(f'{TEST_PATH}.download_file_if_necessary', Mock())
    @patch(f'{TEST_PATH}.absolute_path_to_log_name', Mock())
    @patch(f'{TEST_PATH}.get_images_from_lidar_tokens', Mock(return_value=[]))
    @patch(f'{TEST_PATH}.extract_sensor_tokens_as_scenario', Mock(return_value=[None]))
    @patch(f'{TEST_PATH}.get_sensor_data_from_sensor_data_tokens_from_db')
    @patch(f'{TEST_PATH}.load_point_cloud')
    @patch(f'{TEST_PATH}.load_image')
    def test_get_sensors_at_iteration_no_channels(self, mock_load_image: Mock, mock_load_point_cloud: Mock, mock_get_sensor_data_from_sensor_data_tokens_from_db: Mock) -> None:
        """Test get_past_sensors when no channels are passed."""
        mock_lidar_pc = Mock(spec=LidarPc)
        mock_lidar_pc.token = 'token'
        mock_load_point_cloud.return_value = Mock(spec_set=LidarPointCloud)
        mock_get_sensor_data_from_sensor_data_tokens_from_db.return_value = iter([mock_lidar_pc])
        scenario = self._make_test_scenario()
        sensors = scenario.get_sensors_at_iteration(iteration=0, channels=None)
        mock_get_sensor_data_from_sensor_data_tokens_from_db.assert_called_once()
        mock_load_point_cloud.assert_called_once()
        mock_load_image.assert_not_called()
        self.assertIsNone(sensors.images)
        self.assertIsNotNone(sensors.pointcloud)

def test_implements_abstract_scenario_interface(self) -> None:
    """
        Tests that NuPlanScenario properly implements AbstractScenario interface.
        """
    assert_class_properly_implements_interface(AbstractScenario, NuPlanScenario)

class CachedScenario(AbstractScenario):
    """
    A class representing a cached scenario.
    This class is backend-agnostic, and serves as a pointer to precomputed features.
    """

    def __init__(self, log_name: str, token: str, scenario_type: str) -> None:
        """
        Construct a cached scenario objet.
        :param log_name: The log name for the scenario.
        :param token: The token for the scenario.
        :param scenario_type: The scenario type.
        """
        self._log_name = log_name
        self._token = token
        self._scenario_type = scenario_type

    def __reduce__(self) -> Tuple[Type['CachedScenario'], Tuple[Any, ...]]:
        """
        Hints on how to reconstruct the object when pickling.
        :return: Object type and constructor arguments to be used.
        """
        return (self.__class__, (self._log_name, self._token, self._scenario_type))

    @property
    def token(self) -> str:
        """Inherited, see superclass."""
        return self._token

    @property
    def log_name(self) -> str:
        """Inherited, see superclass."""
        return self._log_name

    @property
    def scenario_name(self) -> str:
        """Inherited, see superclass."""
        raise NotImplementedError('CachedScenario does not implement scenario_name.')

    @property
    def ego_vehicle_parameters(self) -> VehicleParameters:
        """Inherited, see superclass."""
        raise NotImplementedError('CachedScenario does not implement ego_vehicle_parameters.')

    @property
    def scenario_type(self) -> str:
        """Inherited, see superclass."""
        return self._scenario_type

    @property
    def map_api(self) -> str:
        """Inherited, see superclass."""
        raise NotImplementedError('CachedScenario does not implement map_api.')

    @property
    def database_interval(self) -> float:
        """Inherited, see superclass."""
        raise NotImplementedError('CachedScenario does not implement database_interval.')

    @property
    def get_number_of_iterations(self) -> int:
        """Inherited, see superclass."""
        raise NotImplementedError('CachedScenario does not implement get_number_of_iterations.')

    def get_time_point(self) -> TimePoint:
        """Inherited, see superclass."""
        raise NotImplementedError('CachedScenario does not implement get_time_point.')

    def get_lidar_to_ego_transform(self) -> Transform:
        """Inherited, see superclass."""
        raise NotImplementedError('CachedScenario does not implement get_lidar_to_ego_transform.')

    def get_mission_goal(self) -> StateSE2:
        """Inherited, see superclass."""
        raise NotImplementedError('CachedScenario does not implement get_mission_goal.')

    def get_route_roadblock_ids(self) -> List[str]:
        """Inherited, see superclass."""
        raise NotImplementedError('CachedScenario does not implement get_route_roadblock_ids.')

    def get_expert_goal_state(self) -> StateSE2:
        """Inherited, see superclass."""
        raise NotImplementedError('CachedScenario does not implement get_expert_goal_state.')

    def get_tracked_objects_at_iteration(self, iteration: int, future_trajectory_sampling: Optional[TrajectorySampling]=None) -> DetectionsTracks:
        """Inherited, see superclass."""
        raise NotImplementedError('CachedScenario does not implement get_tracked_objects_at_iteration.')

    def get_tracked_objects_within_time_window_at_iteration(self, iteration: int, past_time_horizon: float, future_time_horizon: float, filter_track_tokens: Optional[Set[str]]=None, future_trajectory_sampling: Optional[TrajectorySampling]=None) -> DetectionsTracks:
        """Inherited, see superclass."""
        raise NotImplementedError('CachedScenario does not implement get_tracked_objects_within_time_window_at_iteration.')

    def get_sensors_at_iteration(self, iteration: int, channels: Optional[List[SensorChannel]]=None) -> Sensors:
        """Inherited, see superclass."""
        raise NotImplementedError('CachedScenario does not implement get_sensors_at_iteration.')

    def get_ego_state_at_iteration(self, iteration: int) -> EgoState:
        """Inherited, see superclass."""
        raise NotImplementedError('CachedScenario does not implement get_ego_state_at_iteration.')

    def get_traffic_light_status_at_iteration(self, iteration: int) -> Generator[TrafficLightStatusData, None, None]:
        """Inherited, see superclass."""
        raise NotImplementedError('CachedScenario does not implement get_traffic_light_status_at_iteration.')

    def get_past_traffic_light_status_history(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[TrafficLightStatuses, None, None]:
        """Inherited, see superclass."""
        raise NotImplementedError('CachedScenario does not implement get_past_traffic_light_status_history.')

    def get_future_traffic_light_status_history(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[TrafficLightStatuses, None, None]:
        """Inherited, see superclass."""
        raise NotImplementedError('CachedScenario does not implement get_future_traffic_light_status_history.')

    def get_future_timestamps(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[TimePoint, None, None]:
        """Inherited, see superclass."""
        raise NotImplementedError('CachedScenario does not implement get_future_timestamps.')

    def get_past_timestamps(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[TimePoint, None, None]:
        """Inherited, see superclass."""
        raise NotImplementedError('CachedScenario does not implement get_past_timestamps.')

    def get_ego_future_trajectory(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[EgoState, None, None]:
        """Inherited, see superclass."""
        raise NotImplementedError('CachedScenario does not implement get_ego_future_trajectory.')

    def get_ego_past_trajectory(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[EgoState, None, None]:
        """Inherited, see superclass."""
        raise NotImplementedError('CachedScenario does not implement get_ego_past_trajectory.')

    def get_past_sensors(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None, channels: Optional[List[SensorChannel]]=None) -> Generator[Sensors, None, None]:
        """Inherited, see superclass."""
        raise NotImplementedError('CachedScenario does not implement get_past_sensors.')

    def get_past_tracked_objects(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None, future_trajectory_sampling: Optional[TrajectorySampling]=None) -> Generator[DetectionsTracks, None, None]:
        """Inherited, see superclass."""
        raise NotImplementedError('CachedScenario does not implement get_past_tracked_objects.')

    def get_future_tracked_objects(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None, future_trajectory_sampling: Optional[TrajectorySampling]=None) -> Generator[DetectionsTracks, None, None]:
        """Inherited, see superclass."""
        raise NotImplementedError('CachedScenario does not implement get_future_tracked_objects.')

@property
def scenario_name(self) -> str:
    """Inherited, see superclass."""
    raise NotImplementedError('CachedScenario does not implement scenario_name.')

@property
def ego_vehicle_parameters(self) -> VehicleParameters:
    """Inherited, see superclass."""
    raise NotImplementedError('CachedScenario does not implement ego_vehicle_parameters.')

@property
def map_api(self) -> str:
    """Inherited, see superclass."""
    raise NotImplementedError('CachedScenario does not implement map_api.')

@property
def database_interval(self) -> float:
    """Inherited, see superclass."""
    raise NotImplementedError('CachedScenario does not implement database_interval.')

@property
def get_number_of_iterations(self) -> int:
    """Inherited, see superclass."""
    raise NotImplementedError('CachedScenario does not implement get_number_of_iterations.')

def get_time_point(self) -> TimePoint:
    """Inherited, see superclass."""
    raise NotImplementedError('CachedScenario does not implement get_time_point.')

def get_lidar_to_ego_transform(self) -> Transform:
    """Inherited, see superclass."""
    raise NotImplementedError('CachedScenario does not implement get_lidar_to_ego_transform.')

def get_mission_goal(self) -> StateSE2:
    """Inherited, see superclass."""
    raise NotImplementedError('CachedScenario does not implement get_mission_goal.')

def get_route_roadblock_ids(self) -> List[str]:
    """Inherited, see superclass."""
    raise NotImplementedError('CachedScenario does not implement get_route_roadblock_ids.')

def get_expert_goal_state(self) -> StateSE2:
    """Inherited, see superclass."""
    raise NotImplementedError('CachedScenario does not implement get_expert_goal_state.')

def get_tracked_objects_at_iteration(self, iteration: int, future_trajectory_sampling: Optional[TrajectorySampling]=None) -> DetectionsTracks:
    """Inherited, see superclass."""
    raise NotImplementedError('CachedScenario does not implement get_tracked_objects_at_iteration.')

def get_tracked_objects_within_time_window_at_iteration(self, iteration: int, past_time_horizon: float, future_time_horizon: float, filter_track_tokens: Optional[Set[str]]=None, future_trajectory_sampling: Optional[TrajectorySampling]=None) -> DetectionsTracks:
    """Inherited, see superclass."""
    raise NotImplementedError('CachedScenario does not implement get_tracked_objects_within_time_window_at_iteration.')

def get_sensors_at_iteration(self, iteration: int, channels: Optional[List[SensorChannel]]=None) -> Sensors:
    """Inherited, see superclass."""
    raise NotImplementedError('CachedScenario does not implement get_sensors_at_iteration.')

def get_ego_state_at_iteration(self, iteration: int) -> EgoState:
    """Inherited, see superclass."""
    raise NotImplementedError('CachedScenario does not implement get_ego_state_at_iteration.')

def get_traffic_light_status_at_iteration(self, iteration: int) -> Generator[TrafficLightStatusData, None, None]:
    """Inherited, see superclass."""
    raise NotImplementedError('CachedScenario does not implement get_traffic_light_status_at_iteration.')

def get_past_traffic_light_status_history(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[TrafficLightStatuses, None, None]:
    """Inherited, see superclass."""
    raise NotImplementedError('CachedScenario does not implement get_past_traffic_light_status_history.')

def get_future_traffic_light_status_history(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[TrafficLightStatuses, None, None]:
    """Inherited, see superclass."""
    raise NotImplementedError('CachedScenario does not implement get_future_traffic_light_status_history.')

def get_future_timestamps(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[TimePoint, None, None]:
    """Inherited, see superclass."""
    raise NotImplementedError('CachedScenario does not implement get_future_timestamps.')

def get_past_timestamps(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[TimePoint, None, None]:
    """Inherited, see superclass."""
    raise NotImplementedError('CachedScenario does not implement get_past_timestamps.')

def get_ego_future_trajectory(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[EgoState, None, None]:
    """Inherited, see superclass."""
    raise NotImplementedError('CachedScenario does not implement get_ego_future_trajectory.')

def get_ego_past_trajectory(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[EgoState, None, None]:
    """Inherited, see superclass."""
    raise NotImplementedError('CachedScenario does not implement get_ego_past_trajectory.')

def get_past_sensors(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None, channels: Optional[List[SensorChannel]]=None) -> Generator[Sensors, None, None]:
    """Inherited, see superclass."""
    raise NotImplementedError('CachedScenario does not implement get_past_sensors.')

def get_past_tracked_objects(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None, future_trajectory_sampling: Optional[TrajectorySampling]=None) -> Generator[DetectionsTracks, None, None]:
    """Inherited, see superclass."""
    raise NotImplementedError('CachedScenario does not implement get_past_tracked_objects.')

def get_future_tracked_objects(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None, future_trajectory_sampling: Optional[TrajectorySampling]=None) -> Generator[DetectionsTracks, None, None]:
    """Inherited, see superclass."""
    raise NotImplementedError('CachedScenario does not implement get_future_tracked_objects.')

class DetectionTracksChallengeServicer(object):
    """Missing associated documentation comment in .proto file."""

    def InitializePlanner(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def ComputeTrajectory(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

def InitializePlanner(self, request, context):
    """Missing associated documentation comment in .proto file."""
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

def ComputeTrajectory(self, request, context):
    """Missing associated documentation comment in .proto file."""
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

def proto_tl_status_type_from_tl_status_type(tl_status_type: TrafficLightStatusType) -> chpb.TrafficLightStatusType:
    """
    Serializes TrafficLightStatusType to a TrafficLightStatusType message
    :param tl_status_type: The TrafficLightStatusType object
    :return: The corresponding TrafficLightStatusType message
    """
    return chpb.TrafficLightStatusType(status_name=tl_status_type.serialize())

def proto_tl_status_data_from_tl_status_data(tl_status_data: TrafficLightStatusData) -> chpb.TrafficLightStatusData:
    """
    Serializes TrafficLightStatusData to a TrafficLightStatusData message
    :param tl_status_data: The TrafficLightStatusData object
    :return: The corresponding TrafficLightStatusData message
    """
    return chpb.TrafficLightStatusData(status=proto_tl_status_type_from_tl_status_type(tl_status_data.status), lane_connector_id=tl_status_data.lane_connector_id, timestamp=tl_status_data.timestamp)

def tl_status_data_from_proto_tl_status_data(tl_status_data: chpb.TrafficLightStatusData) -> TrafficLightStatusData:
    """
    Deserializes TrafficLightStatusType message to a TrafficLightStatusType object
    :param tl_status_data: The proto TrafficLightStatusType message
    :return: The corresponding TrafficLightStatusType object
    """
    return TrafficLightStatusData(status=tl_status_type_from_proto_tl_status_type(tl_status_data.status), lane_connector_id=tl_status_data.lane_connector_id, timestamp=tl_status_data.timestamp)

class TestProtoConverters(unittest.TestCase):
    """Tests proto converters by checking if composition is idempotent."""

    def test_trajectory_conversions(self) -> None:
        """Tests conversions between trajectory object and messages."""
        trajectory = InterpolatedTrajectory([get_sample_ego_state(StateSE2(0, 1, 2)), get_sample_ego_state(StateSE2(1, 2, 3), time_us=1)])
        result = interp_traj_from_proto_traj(proto_traj_from_inter_traj(trajectory))
        for result_state, trajectory_state in zip(result.get_sampled_trajectory(), trajectory.get_sampled_trajectory()):
            np.allclose(result_state.to_split_state().linear_states, trajectory_state.to_split_state().linear_states)
            np.allclose(result_state.to_split_state().angular_states, trajectory_state.to_split_state().angular_states)

    def test_tl_status_type_conversions(self) -> None:
        """Tests conversions between TL status data and messages."""
        tl_status_type = TrafficLightStatusType.RED
        result = tl_status_type_from_proto_tl_status_type(proto_tl_status_type_from_tl_status_type(tl_status_type))
        self.assertEqual(tl_status_type, result)

    def test_tl_status_data_conversions(self) -> None:
        """Tests conversions between TL status type and messages."""
        tl_status = TrafficLightStatusData(TrafficLightStatusType.RED, 123, 456)
        result = tl_status_data_from_proto_tl_status_data(proto_tl_status_data_from_tl_status_data(tl_status))
        self.assertEqual(tl_status, result)

def test_tl_status_type_conversions(self) -> None:
    """Tests conversions between TL status data and messages."""
    tl_status_type = TrafficLightStatusType.RED
    result = tl_status_type_from_proto_tl_status_type(proto_tl_status_type_from_tl_status_type(tl_status_type))
    self.assertEqual(tl_status_type, result)

def test_tl_status_data_conversions(self) -> None:
    """Tests conversions between TL status type and messages."""
    tl_status = TrafficLightStatusData(TrafficLightStatusType.RED, 123, 456)
    result = tl_status_data_from_proto_tl_status_data(proto_tl_status_data_from_tl_status_data(tl_status))
    self.assertEqual(tl_status, result)

