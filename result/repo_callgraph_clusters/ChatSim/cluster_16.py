# Cluster 16

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

def box_xyxy_to_xywh(box_xyxy: torch.Tensor) -> torch.Tensor:
    box_xywh = deepcopy(box_xyxy)
    box_xywh[2] = box_xywh[2] - box_xywh[0]
    box_xywh[3] = box_xywh[3] - box_xywh[1]
    return box_xywh

def is_good_key(key, cats):
    return any((c in key for c in cats))

def extract_overlapping_masks(mask_fnames, cur_i, fake_scores_table, max_overlaps_n=2):
    result_pairs = []
    result_scores = []
    mask_fname_a = mask_fnames[cur_i]
    mask_a = load_image(mask_fname_a, mode='L')[None, ...] > 0.5
    cur_score_a = fake_scores_table.loc[mask_fname_a, 'fake_score']
    for mask_fname_b in mask_fnames[cur_i + 1:]:
        mask_b = load_image(mask_fname_b, mode='L')[None, ...] > 0.5
        if not np.any(mask_a & mask_b):
            continue
        cur_score_b = fake_scores_table.loc[mask_fname_b, 'fake_score']
        result_pairs.append((mask_fname_a, mask_fname_b))
        result_scores.append(cur_score_b - cur_score_a)
        if len(result_pairs) >= max_overlaps_n:
            break
    return (result_pairs, result_scores)

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

def isin(ar1, ar2):
    return (ar1[..., None] == ar2).any(-1).float()

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

def odd_to_even(image):
    """
  To facilitate 2x2 downsampling segmentation, change an odd sized image into an even sized one.
  Works by mirroring the starting 1 pixel edge of the image on odd shaped sides.

  e.g. turn a 3x3x5 image into a 4x4x5 (the x and y are what are getting downsampled)
  
  For example: [ 3, 2, 4 ] => [ 3, 3, 2, 4 ] which is now easy to downsample.

  """
    shape = np.array(image.shape)
    offset = (shape % 2)[:2]
    if not np.any(offset):
        return image
    oddshape = image.shape[:2] + offset
    oddshape = np.append(oddshape, shape[2:])
    oddshape = oddshape.astype(int)
    newimg = np.empty(shape=oddshape, dtype=image.dtype)
    ox, oy = offset
    sx, sy = oddshape
    newimg[0, 0] = image[0, 0]
    newimg[ox:sx, 0] = image[:, 0]
    newimg[0, oy:sy] = image[0, :]
    return newimg

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

def isin(ar1, ar2):
    return (ar1[..., None] == ar2).any(-1).float()

class TensorList(list):
    """Container mainly used for lists of torch tensors. Extends lists with pytorch functionality."""

    def __init__(self, list_of_tensors=None):
        if list_of_tensors is None:
            list_of_tensors = list()
        super(TensorList, self).__init__(list_of_tensors)

    def __deepcopy__(self, memodict={}):
        return TensorList(copy.deepcopy(list(self), memodict))

    def __getitem__(self, item):
        if isinstance(item, int):
            return super(TensorList, self).__getitem__(item)
        elif isinstance(item, (tuple, list)):
            return TensorList([super(TensorList, self).__getitem__(i) for i in item])
        else:
            return TensorList(super(TensorList, self).__getitem__(item))

    def __add__(self, other):
        if TensorList._iterable(other):
            return TensorList([e1 + e2 for e1, e2 in zip(self, other)])
        return TensorList([e + other for e in self])

    def __radd__(self, other):
        if TensorList._iterable(other):
            return TensorList([e2 + e1 for e1, e2 in zip(self, other)])
        return TensorList([other + e for e in self])

    def __iadd__(self, other):
        if TensorList._iterable(other):
            for i, e2 in enumerate(other):
                self[i] += e2
        else:
            for i in range(len(self)):
                self[i] += other
        return self

    def __sub__(self, other):
        if TensorList._iterable(other):
            return TensorList([e1 - e2 for e1, e2 in zip(self, other)])
        return TensorList([e - other for e in self])

    def __rsub__(self, other):
        if TensorList._iterable(other):
            return TensorList([e2 - e1 for e1, e2 in zip(self, other)])
        return TensorList([other - e for e in self])

    def __isub__(self, other):
        if TensorList._iterable(other):
            for i, e2 in enumerate(other):
                self[i] -= e2
        else:
            for i in range(len(self)):
                self[i] -= other
        return self

    def __mul__(self, other):
        if TensorList._iterable(other):
            return TensorList([e1 * e2 for e1, e2 in zip(self, other)])
        return TensorList([e * other for e in self])

    def __rmul__(self, other):
        if TensorList._iterable(other):
            return TensorList([e2 * e1 for e1, e2 in zip(self, other)])
        return TensorList([other * e for e in self])

    def __imul__(self, other):
        if TensorList._iterable(other):
            for i, e2 in enumerate(other):
                self[i] *= e2
        else:
            for i in range(len(self)):
                self[i] *= other
        return self

    def __truediv__(self, other):
        if TensorList._iterable(other):
            return TensorList([e1 / e2 for e1, e2 in zip(self, other)])
        return TensorList([e / other for e in self])

    def __rtruediv__(self, other):
        if TensorList._iterable(other):
            return TensorList([e2 / e1 for e1, e2 in zip(self, other)])
        return TensorList([other / e for e in self])

    def __itruediv__(self, other):
        if TensorList._iterable(other):
            for i, e2 in enumerate(other):
                self[i] /= e2
        else:
            for i in range(len(self)):
                self[i] /= other
        return self

    def __matmul__(self, other):
        if TensorList._iterable(other):
            return TensorList([e1 @ e2 for e1, e2 in zip(self, other)])
        return TensorList([e @ other for e in self])

    def __rmatmul__(self, other):
        if TensorList._iterable(other):
            return TensorList([e2 @ e1 for e1, e2 in zip(self, other)])
        return TensorList([other @ e for e in self])

    def __imatmul__(self, other):
        if TensorList._iterable(other):
            for i, e2 in enumerate(other):
                self[i] @= e2
        else:
            for i in range(len(self)):
                self[i] @= other
        return self

    def __mod__(self, other):
        if TensorList._iterable(other):
            return TensorList([e1 % e2 for e1, e2 in zip(self, other)])
        return TensorList([e % other for e in self])

    def __rmod__(self, other):
        if TensorList._iterable(other):
            return TensorList([e2 % e1 for e1, e2 in zip(self, other)])
        return TensorList([other % e for e in self])

    def __pos__(self):
        return TensorList([+e for e in self])

    def __neg__(self):
        return TensorList([-e for e in self])

    def __le__(self, other):
        if TensorList._iterable(other):
            return TensorList([e1 <= e2 for e1, e2 in zip(self, other)])
        return TensorList([e <= other for e in self])

    def __ge__(self, other):
        if TensorList._iterable(other):
            return TensorList([e1 >= e2 for e1, e2 in zip(self, other)])
        return TensorList([e >= other for e in self])

    def concat(self, other):
        return TensorList(super(TensorList, self).__add__(other))

    def copy(self):
        return TensorList(super(TensorList, self).copy())

    def unroll(self):
        if not any((isinstance(t, TensorList) for t in self)):
            return self
        new_list = TensorList()
        for t in self:
            if isinstance(t, TensorList):
                new_list.extend(t.unroll())
            else:
                new_list.append(t)
        return new_list

    def list(self):
        return list(self)

    def attribute(self, attr: str, *args):
        return TensorList([getattr(e, attr, *args) for e in self])

    def apply(self, fn):
        return TensorList([fn(e) for e in self])

    def __getattr__(self, name):
        if not hasattr(torch.Tensor, name):
            raise AttributeError("'TensorList' object has not attribute '{}'".format(name))

        def apply_attr(*args, **kwargs):
            return TensorList([getattr(e, name)(*args, **kwargs) for e in self])
        return apply_attr

    @staticmethod
    def _iterable(a):
        return isinstance(a, (TensorList, list))

def __deepcopy__(self, memodict={}):
    return TensorList(copy.deepcopy(list(self), memodict))

def is_image_file(filename):
    return any((filename.endswith(extension) for extension in IMG_EXTENSIONS))

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

class MotionAgent:

    def __init__(self, config):
        self.config = config
        self.motion_tracking = config.get('motion_tracking', False)

    def llm_reasoning_dependency(self, scene, message):
        """ LLM reasoning of Motion Agent, determine if the vehicle placement is depend on scene elements.
        Input:
            scene : Scene
                scene object.
            message : str
                language prompt to ChatSim.
        """
        try:
            q0 = 'I will provide an operation statement to add a vehicle, and you need to determine whether the position of the added car has any spatial dependency with other cars in my statement'
            q1 = "Only return a JSON format dictionary as your response, which contains a key 'dependency'. If the added car's position depends on other objects, set it to 1; otherwise, set it to 0."
            q2 = "An Example: Given statement 'add an Audi in the back which drives ahead', you should return {'dependency': 0}. This is because I only mention the added Audi."
            q3 = "An Example: Given statement 'add a Porsche at 2m to the right of the red Audi.', you should return {'dependency': 1}. This is because Porsche's position depends on Audi."
            q4 = "An Example: Given statement 'add a car in front of me.', you should return {'dependency': 0}. This is because 'me' is not other car in the scene."
            q5 = 'The statement is:' + message
            prompt_list = [q0, q1, q2, q3, q4, q5]
            result = openai.ChatCompletion.create(model='gpt-4', messages=[{'role': 'system', 'content': 'You are an assistant helping me to extract information from the operations.'}] + [{'role': 'user', 'content': q} for q in prompt_list])
            answer = result['choices'][0]['message']['content']
            print(f'{colored('[Motion Agent LLM] analyzing insertion scene dependency ', color='magenta', attrs=['bold'])}                     \n{colored('[Raw Response>>>]', attrs=['bold'])} {answer}')
            start = answer.index('{')
            answer = answer[start:]
            end = answer.rfind('}')
            answer = answer[:end + 1]
            placement_mode = eval(answer)
            print(f'{colored('[Extracted Response>>>]', attrs=['bold'])} {placement_mode} \n')
        except Exception as e:
            print(e)
            traceback.print_exc()
            return '[Motion Agent LLM] reasoning object dependency fails.'
        return placement_mode

    def llm_placement_wo_dependency(self, scene, message):
        try:
            q0 = 'I will provide you with an operation statement to add and place a vehicle, and I need you to extract 3 specific placement information from the statement, including: '
            q1 = " (1) 'mode', one of ['front', 'left front', 'left', 'right front', 'right', 'random'], representing approximate initial positions of the vehicle. If not specified, it defaults to 'random'."
            q2 = " (2) 'distance_constraint' indicates whether there's a constraint on the distance of the added vehicle. 0 means no constraint, 1 means there is a constraint." + " If there's no relevant information mentioned, it defaults to 0."
            q3 = " (3) 'distance_min_max' represents the range of constraints when 'distance_constraint' applicable. It should be a tuple in the format (min, max), for example, (9, 11) means the minimum distance is 9, and the maximum is 11." + " When there's 'distance_constraint' is 0, the default value is (4, 45). If distance is specified as a specific value 'x', 'distance_min_max' is (x, x+5)"
            q4 = "Just return the json dict with keys:'mode', 'distance_constraint', 'distance_min_max'. Do not return any code or discription."
            q5 = "An Example: Given operation statement: 'Add an Audi 7-10 meters ahead', you should return " + "{'mode':'front', 'distance_constraint': 1, 'distance_min_max':(7,10)}"
            q6 = "An Example: Given operation statement: 'Add an Porsche in the right front.', you should return " + "{'mode':'right front', 'distance_constraint': 0, 'distance_min_max':(4, 45)}"
            q7 = 'Note that you should not return any code or explanations, only provide a JSON dictionary.'
            q8 = 'The operation statement:' + message
            prompt_list = [q0, q1, q2, q3, q4, q5, q6, q7, q8]
            result = openai.ChatCompletion.create(model='gpt-4', messages=[{'role': 'system', 'content': 'You are an assistant helping me to determine how to place a car.'}] + [{'role': 'user', 'content': q} for q in prompt_list])
            answer = result['choices'][0]['message']['content']
            print(f'{colored('[Motion Agent LLM] deciding scene-independent object placement', color='magenta', attrs=['bold'])}                     \n{colored('[Raw Response>>>]', attrs=['bold'])} {answer}')
            start = answer.index('{')
            answer = answer[start:]
            end = answer.rfind('}')
            answer = answer[:end + 1]
            placement_prior = eval(answer)
            print(f'{colored('[Extracted Response>>>]', attrs=['bold'])} {placement_prior} \n')
        except Exception as e:
            print(e)
            traceback.print_exc()
            return '[Motion Agent LLM] deciding placement fails.'
        return placement_prior

    def llm_placement_w_dependency(self, scene, message, scene_object_description):
        try:
            q0 = 'I will provide you with an operation statement to add and place a vehicle, as well as information of other cars in the scene.'
            q1 = 'I need you to determine a specific position (x, y) for placement of the added car in my statement. '
            q2 = 'Information of other cars in the scene is a two-level dictionary, with the first level representing the different car id in the scene, ' + 'and the second level containing various information about that car, including the (x, y) of its world 3D coordinate, ' + 'its image coordinate (u, v) in an image frame, depth, and rgb color representation.'
            q3 = 'The dictionary is' + str(scene_object_description)
            q4 = 'I will also further inform you about the operations that have been previously performed on this scene. ' + 'You can use these past operations, along with the dictionary I provide, to generate the final position.'
            q5 = 'The previously performed operation is : ' + str(scene.past_operations)
            q6 = "If the car with key 'direction', and direction is close, 'behind' means keep the same 'y' and increase 'x' 10 meters. If direction is away, 'behind' means keep the same 'y' and decrease 'x' 10 meters." + "If the car with key 'direction', and direction is close, 'front' means keep the same 'y' and decrease 'x' 10 meters. If direction is away, 'front' means keep the same 'y' and increase 'x' 10 meters."
            q7 = "'left' means keep the same 'x' and increase 'y' 5m, 'right' means keep the same 'x' and decrease 'y' 5m."
            q8 = "You should return a placemenet positon in JSON dictionary with 2 keys: 'x', 'y'. Do not provide any code or explanations, only return the final JSON dictionary."
            q9 = 'The requirement is:' + message
            prompt_list = [q0, q1, q2, q3, q4, q5, q6, q7, q8, q9]
            result = openai.ChatCompletion.create(model='gpt-4', messages=[{'role': 'system', 'content': 'You are an assistant helping me to determine how to place a car.'}] + [{'role': 'user', 'content': q} for q in prompt_list])
            answer = result['choices'][0]['message']['content']
            print(f'{colored('[Motion Agent LLM] deciding scene-dependent object placement', color='magenta', attrs=['bold'])}                     \n{colored('[Raw Response>>>]', attrs=['bold'])} {answer}')
            start = answer.index('{')
            answer = answer[start:]
            end = answer.rfind('}')
            answer = answer[:end + 1]
            placement_prior = eval(answer)
            print(f'{colored('[Extracted Response>>>]', attrs=['bold'])} {placement_prior} \n')
        except Exception as e:
            print(e)
            traceback.print_exc()
            return '[Motion Agent LLM] deciding placement fails.'
        return placement_prior

    def llm_motion_planning(self, scene, message):
        try:
            q0 = 'I will provide you with an operation statement to add and place a vehicle, and I need you to determine the its motion situation from my statement, including: '
            q1 = "(1) 'action', one of ['static', 'random', 'straight', 'turn left', 'turn right']. If action not mentioned in the statement, it defaults to 'straight'." + "For example, the statement is 'add a black car in front of me', then the action is 'straight'."
            q2 = "(2) 'speed', the approximate speed of the vehicle, one of ['random', 'fast', 'slow']. If speed is not mentioned in the statement, it defaults to 'slow'."
            q3 = "(3) 'direction', one of ['away', 'close', 'random']. 'away' represents the direction away from oneself, and 'close' represents the direction toward oneself." + "For example, moving forward is 'away' from oneself, while moving towards oneself is 'close'. If direction is not mentioned in the statement, just return 'random'."
            q4 = "(4) 'wrong_way', if the vehicle drives in the wrong way, one of ['true'. 'false']. If the information is not mentioned in the statement, it defaults to 'false'."
            q4 = "An Example: Given the statement 'add a Tesla that is racing straight ahead in the right front of the scene', you should return {'action': 'straight', 'speed': 'fast', 'direction': 'away', 'wrong_way': 'false'}"
            q5 = "An Example: Given the statement 'add a yellow Audi in front of the scene', you should return {'action': 'static', 'speed': 'random', 'direction': 'away', 'wrong_way': 'false'}"
            q6 = "An Example: Given the statement 'add a Tesla coming from the front and driving in the wrong way', you should return {'action': 'straight', 'speed': 'random', 'direction': 'close', 'wrong_way': 'true'}"
            q7 = 'Note that there is no need to return any code or explanations; only provide a JSON dictionary. Do not include any additional statements.'
            q8 = 'The operation statement is:' + message
            prompt_list = [q0, q1, q2, q3, q4, q5, q6, q7, q8]
            result = openai.ChatCompletion.create(model='gpt-4', messages=[{'role': 'system', 'content': 'You are an assistant helping me to assess the motion situation for adding vehicles.'}] + [{'role': 'user', 'content': q} for q in prompt_list])
            answer = result['choices'][0]['message']['content']
            print(f'{colored('[Motion Agent LLM] finding motion prior', color='magenta', attrs=['bold'])}                     \n{colored('[Raw Response>>>]', attrs=['bold'])} {answer}')
            start = answer.index('{')
            answer = answer[start:]
            end = answer.rfind('}')
            answer = answer[:end + 1]
            motion_prior = eval(answer)
            if not motion_prior.get('wrong_way'):
                motion_prior['wrong_way'] = False
            print(f'{colored('[Extracted Response>>>]', attrs=['bold'])} {motion_prior} \n')
        except Exception as e:
            print(e)
            traceback.print_exc()
            return '[Motion Agent LLM] finding motion prior fails.'
        return motion_prior

    def func_placement_and_motion_single_vehicle(self, scene, added_car_name):
        added_car_id = added_car_name.lstrip('added_car_')
        transformed_map_data_ = transform_node_to_lane(scene.map_data)
        all_current_vertices_coord = scene.all_current_vertices_coord
        for added_traj in scene.all_trajectories:
            all_current_vertices_coord = np.vstack([all_current_vertices_coord, added_traj[0:1, 0:2]])
        one_added_car = scene.added_cars_dict[added_car_name]
        if one_added_car['need_placement_and_motion'] is True:
            scene.added_cars_dict[added_car_name]['need_placement_and_motion'] = False
            one_added_car = scene.added_cars_dict[added_car_name]
            transformed_map_data = deepcopy(transformed_map_data_)
            if one_added_car['wrong_way'] is True:
                transformed_map_data['centerline'][:, -1] = (transformed_map_data['centerline'][:, -1] + 1) % 2
                transformed_map_data['centerline'] = np.concatenate((transformed_map_data['centerline'][:, 2:4], transformed_map_data['centerline'][:, 0:2], transformed_map_data['centerline'][:, 4:]), axis=1)
                transformed_map_data['centerline'] = np.flip(transformed_map_data['centerline'], axis=0)
            if one_added_car.get('x') is None:
                placement_result = vehicle_placement(transformed_map_data, all_current_vertices_coord, one_added_car['direction'] if one_added_car['direction'] != 'random' else random.choice(['away', 'close']), one_added_car['mode'], one_added_car['distance_constraint'], one_added_car['distance_min_max'], 'default')
            else:
                placement_result = vehicle_placement_specific(transformed_map_data, all_current_vertices_coord, np.array([one_added_car['x'], one_added_car['y']]))
            if placement_result[0] is None:
                del scene.added_cars_dict[added_car_name]
                return
            one_added_car['placement_result'] = placement_result
            try:
                motion_result = vehicle_motion(transformed_map_data, scene.all_current_vertices[:, ::2, :2] if scene.all_current_vertices.shape[0] != 0 else scene.all_current_vertices, placement_result=one_added_car['placement_result'], high_level_action_direction=one_added_car['action'], high_level_action_speed=one_added_car['speed'], dt=1 / scene.fps, total_len=scene.frames)
            except ValueError as e:
                print(f'{colored('[Motion Agent] Error: Potentially no feasible destination can be found.', color='red', attrs=['bold'])} {e}')
                raise ValueError('No feasible destination can be found.')
            if motion_result[0] is None:
                del scene.added_cars_dict[added_car_name]
                return
            one_added_car['motion'] = motion_result
            scene.added_cars_dict[added_car_name] = one_added_car
            all_trajectories = []
            for one_car_name in scene.added_cars_dict.keys():
                all_trajectories.append(scene.added_cars_dict[one_car_name]['motion'][:, :2])
            all_trajectories_after_check_collision = check_collision_and_revise_dynamic(all_trajectories)
            all_trajectories_after_check_collision = all_trajectories
            scene.all_trajectories = all_trajectories_after_check_collision
            for idx, one_car_name in enumerate(scene.added_cars_dict.keys()):
                motion_result = all_trajectories_after_check_collision[idx]
                placement_result = scene.added_cars_dict[one_car_name]['placement_result']
                direction = np.zeros((motion_result.shape[0], 1))
                angle = np.arctan2(placement_result[-1] - placement_result[-3], placement_result[-2] - placement_result[-4])
                for i in range(motion_result.shape[0] - 1):
                    if motion_result[i, 0] == motion_result[i + 1, 0] and motion_result[i, 1] == motion_result[i + 1, 1]:
                        direction[i, 0] = angle
                    else:
                        direction[i, 0] = np.arctan2(motion_result[i + 1, 1] - motion_result[i, 1], motion_result[i + 1, 0] - motion_result[i, 0])
                direction[-1, 0] = direction[-2, 0]
                motion_result = np.concatenate((motion_result, direction), axis=1)
                if self.motion_tracking:
                    try:
                        from simulator import TrajectoryTracker
                    except ModuleNotFoundError:
                        error_msg1 = f'{colored('[ERROR]', color='red', attrs=['bold'])} Trajectory Tracking Module is not installed.\n'
                        error_msg2 = "\nYou can 1) Install Installation README's Step 5: Setup Trajectory Tracking Module"
                        error_msg3 = "\n     Or 2) set ['motion_agent']['motion_tracking'] to False in config.\n"
                        raise ModuleNotFoundError(error_msg1 + error_msg2 + error_msg3)
                    reference_line = interpolate_uniformly(motion_result, int(scene.frames * scene.fps / 10))
                    reference_line = [(reference_line[i, 0], reference_line[i, 1]) for i in range(reference_line.shape[0])]
                    init_state = (motion_result[0, 0], motion_result[0, 1], motion_result[0, 2], np.linalg.norm(np.array(reference_line[1]) - np.array(reference_line[0])) * 10)
                    pretrained_checkpoint_dir = './chatsim/foreground/drl-based-trajectory-tracking/submodules/drltt-assets/checkpoints/track/checkpoint'
                    trajectory_tracker = TrajectoryTracker(checkpoint_dir=pretrained_checkpoint_dir)
                    states, actions = trajectory_tracker.track_reference_line(reference_line=reference_line, init_state=init_state)
                    motion_result = np.stack(states)[:, :-1]
                    motion_result = interpolate_uniformly(motion_result, scene.frames)
                scene.added_cars_dict[one_car_name]['motion'] = motion_result

def func_placement_and_motion_single_vehicle(self, scene, added_car_name):
    added_car_id = added_car_name.lstrip('added_car_')
    transformed_map_data_ = transform_node_to_lane(scene.map_data)
    all_current_vertices_coord = scene.all_current_vertices_coord
    for added_traj in scene.all_trajectories:
        all_current_vertices_coord = np.vstack([all_current_vertices_coord, added_traj[0:1, 0:2]])
    one_added_car = scene.added_cars_dict[added_car_name]
    if one_added_car['need_placement_and_motion'] is True:
        scene.added_cars_dict[added_car_name]['need_placement_and_motion'] = False
        one_added_car = scene.added_cars_dict[added_car_name]
        transformed_map_data = deepcopy(transformed_map_data_)
        if one_added_car['wrong_way'] is True:
            transformed_map_data['centerline'][:, -1] = (transformed_map_data['centerline'][:, -1] + 1) % 2
            transformed_map_data['centerline'] = np.concatenate((transformed_map_data['centerline'][:, 2:4], transformed_map_data['centerline'][:, 0:2], transformed_map_data['centerline'][:, 4:]), axis=1)
            transformed_map_data['centerline'] = np.flip(transformed_map_data['centerline'], axis=0)
        if one_added_car.get('x') is None:
            placement_result = vehicle_placement(transformed_map_data, all_current_vertices_coord, one_added_car['direction'] if one_added_car['direction'] != 'random' else random.choice(['away', 'close']), one_added_car['mode'], one_added_car['distance_constraint'], one_added_car['distance_min_max'], 'default')
        else:
            placement_result = vehicle_placement_specific(transformed_map_data, all_current_vertices_coord, np.array([one_added_car['x'], one_added_car['y']]))
        if placement_result[0] is None:
            del scene.added_cars_dict[added_car_name]
            return
        one_added_car['placement_result'] = placement_result
        try:
            motion_result = vehicle_motion(transformed_map_data, scene.all_current_vertices[:, ::2, :2] if scene.all_current_vertices.shape[0] != 0 else scene.all_current_vertices, placement_result=one_added_car['placement_result'], high_level_action_direction=one_added_car['action'], high_level_action_speed=one_added_car['speed'], dt=1 / scene.fps, total_len=scene.frames)
        except ValueError as e:
            print(f'{colored('[Motion Agent] Error: Potentially no feasible destination can be found.', color='red', attrs=['bold'])} {e}')
            raise ValueError('No feasible destination can be found.')
        if motion_result[0] is None:
            del scene.added_cars_dict[added_car_name]
            return
        one_added_car['motion'] = motion_result
        scene.added_cars_dict[added_car_name] = one_added_car
        all_trajectories = []
        for one_car_name in scene.added_cars_dict.keys():
            all_trajectories.append(scene.added_cars_dict[one_car_name]['motion'][:, :2])
        all_trajectories_after_check_collision = check_collision_and_revise_dynamic(all_trajectories)
        all_trajectories_after_check_collision = all_trajectories
        scene.all_trajectories = all_trajectories_after_check_collision
        for idx, one_car_name in enumerate(scene.added_cars_dict.keys()):
            motion_result = all_trajectories_after_check_collision[idx]
            placement_result = scene.added_cars_dict[one_car_name]['placement_result']
            direction = np.zeros((motion_result.shape[0], 1))
            angle = np.arctan2(placement_result[-1] - placement_result[-3], placement_result[-2] - placement_result[-4])
            for i in range(motion_result.shape[0] - 1):
                if motion_result[i, 0] == motion_result[i + 1, 0] and motion_result[i, 1] == motion_result[i + 1, 1]:
                    direction[i, 0] = angle
                else:
                    direction[i, 0] = np.arctan2(motion_result[i + 1, 1] - motion_result[i, 1], motion_result[i + 1, 0] - motion_result[i, 0])
            direction[-1, 0] = direction[-2, 0]
            motion_result = np.concatenate((motion_result, direction), axis=1)
            if self.motion_tracking:
                try:
                    from simulator import TrajectoryTracker
                except ModuleNotFoundError:
                    error_msg1 = f'{colored('[ERROR]', color='red', attrs=['bold'])} Trajectory Tracking Module is not installed.\n'
                    error_msg2 = "\nYou can 1) Install Installation README's Step 5: Setup Trajectory Tracking Module"
                    error_msg3 = "\n     Or 2) set ['motion_agent']['motion_tracking'] to False in config.\n"
                    raise ModuleNotFoundError(error_msg1 + error_msg2 + error_msg3)
                reference_line = interpolate_uniformly(motion_result, int(scene.frames * scene.fps / 10))
                reference_line = [(reference_line[i, 0], reference_line[i, 1]) for i in range(reference_line.shape[0])]
                init_state = (motion_result[0, 0], motion_result[0, 1], motion_result[0, 2], np.linalg.norm(np.array(reference_line[1]) - np.array(reference_line[0])) * 10)
                pretrained_checkpoint_dir = './chatsim/foreground/drl-based-trajectory-tracking/submodules/drltt-assets/checkpoints/track/checkpoint'
                trajectory_tracker = TrajectoryTracker(checkpoint_dir=pretrained_checkpoint_dir)
                states, actions = trajectory_tracker.track_reference_line(reference_line=reference_line, init_state=init_state)
                motion_result = np.stack(states)[:, :-1]
                motion_result = interpolate_uniformly(motion_result, scene.frames)
            scene.added_cars_dict[one_car_name]['motion'] = motion_result

class ProjectManager:

    def __init__(self, config):
        self.config = config

    def decompose_prompt(self, scene, user_prompt):
        """ decompose the prompt to the corresponding chatsim.agents.
        Input:
            scene : Scene
                scene object.
            user_prompt : str
                language prompt to ChatSim.
        Return:
            tasks : dict
                a dictionary of decomposed tasks.
        """
        q0 = 'I have a requirement of editing operations in an autonomous driving scenario, and I need your help to break it down into one or several supportable actions. The scene is large which means many vehicles can be contained. '
        q1 = 'The supportable five actions include adding vehicles ,                 deleting vehicles ,                 put back deleted vehicles,                 adjusting added vehicles ,                 viewpoint adjustment.'
        q2 = 'Please try to retain all the semantics and adjunct words from the original text. Each adding action should only contain one car. ' + 'Information about adding vehicles (such as their type, positions, driving status, speed, color, etc.) should be directly included within the adding action.'
        q3 = 'Split actions should be stored in a JSON dictonary. The key is action id and the value is specific action. They will be executed sequentially, and the broken operations should be independent with each other and do not rely on the detailed scene information.'
        q4 = "An example: the requirement is 'substitute the red car in the scene', you break it down and return" + "{ 1: 'Delete the red car from the scene', 2: 'Add a new car at the location where the red car was deleted' }."
        q5 = "An example: the requirement is 'delete the farthest car and add a red Audi in the right front', you break it down and return " + "{ 1: 'Delete the farthest car', 2: 'Add a red Audi in the right front' }"
        q6 = "An example: the requirement is 'delete all cars', you break it down and return " + "{ 1: 'Delete all the cars'} "
        q7 = 'I may provide very abstract requirements. For such requirements, you should analyze how to comply with the splitting of actions.'
        q8 = "An example (very abstract): the requirement is 'I want several cars driving slowly in the scene', you analyse and return " + "{ 1: 'Add one car driving slowly', 2 : 'Add one car driving slowly', 3 : 'Add one car driving slowly', 4 : 'Add one car driving slowly', 5 : 'Add one car driving slowly', 6 : 'Add one car driving slowly', 7 : 'Add one car driving slowly'} "
        q9 = 'The scene is large enough to contain more than 20 vehicles. So many vehicles can be added to the scene. Do not return any code or explanation; only a JSON dictionary is required.'
        q10 = 'Attention: the adjustments for one specific added vehicle should be included in one single output action. If there are multiple adjustments for one already added car, these adjustments must be merged in one action.'
        q11 = 'Attention: Do not appear information about the vehicles in the other broken actions.'
        q12 = 'The requirement is:' + user_prompt
        prompt_list = [q0, q1, q2, q3, q4, q5, q6, q7, q8, q9, q10, q11, q12]
        result = openai.ChatCompletion.create(model='gpt-4-turbo-preview', messages=[{'role': 'system', 'content': 'You are an assistant helping me to break down the operations.'}] + [{'role': 'user', 'content': q} for q in prompt_list])
        answer = result['choices'][0]['message']['content']
        print(f'{colored('[User prompt]', color='magenta', attrs=['bold'])} {user_prompt}\n')
        print(f'{colored('[Project Manager] decomposing tasks', color='magenta', attrs=['bold'])}                \n{colored('[Raw Response>>>]', attrs=['bold'])} {answer}')
        try:
            start = answer.index('{')
            answer = answer[start:]
            end = answer.rfind('}')
            answer = answer[:end + 1]
            tasks = eval(answer)
            print(f'{colored('[Extracted Response>>>]', attrs=['bold'])} {answer} \n')
        except Exception as e:
            print(e)
            traceback.print_exc()
            return 'Can not parse the requirement.'
        return tasks

    def dispatch_task(self, scene, task, tech_agents):
        """ dispatch the tasks to the corresponding chatsim.agents.
        Input:
            scene : Scene
                scene object.
            task : str
                a decomposed task, should be assigned to one/more agents
            tech_agents : dict
                a dictionary of technical agents, helping to reason the task
        Return:
            callback_message : str
                if encounter bugs, record them in callback_message to users
        """
        operation_category = {1: 'adding', 2: 'deleting', 3: 'adjusting the viewpoint', 4: 'putting back previously deleted vehicles', 5: 'operating on previously added vehicles'}
        q0 = 'I will provide you with an action, and you will help me determine which operation this action belongs to.'
        q1 = 'Operations include (1) adding (2) deleting, (3) adjusting the viewpoint, (4) putting back previously deleted vehicles, (5) operating on previously added vehicles.'
        q2 = "Return the information in JSON format, with a key named 'operation'."
        q3 = "An Example: Given action 'Remove the red car from the scene', you should return {'operation': 2}"
        q4 = "An Example: Given action 'Add a green Porsche at the location where the red car was removed', you should return {'operation': 1}"
        q5 = "An Example: Given action 'Put back the deleted white car', you should return {'operation': 4}"
        q6 = "An Example: Given action 'Move the car just added to the right by 2m', you should return {'operation': 5}"
        q7 = 'Note that you should not return any code or explanations, only provide a JSON dictionary.'
        q8 = task
        prompt_list = [q0, q1, q2, q3, q4, q5, q6, q7, q8]
        result = openai.ChatCompletion.create(model='gpt-4', messages=[{'role': 'system', 'content': 'You are an assistant helping me to classify operations.'}] + [{'role': 'user', 'content': q} for q in prompt_list])
        answer = result['choices'][0]['message']['content']
        print(f'{colored('[Project Manager] dispatching each task', color='magenta', attrs=['bold'])}                 \n{colored('[Raw Response>>>]', attrs=['bold'])} {answer}')
        start = answer.index('{')
        answer = answer[start:]
        end = answer.rfind('}')
        answer = answer[:end + 1]
        operation = eval(answer)['operation']
        print(f'{colored('[Extracted Response>>>]', attrs=['bold'])} {operation}. ({operation_category[operation]}) \n')
        if operation == 1:
            self.addition_operation(scene, task, tech_agents)
        elif operation == 2:
            self.deletion_operation(scene, task, tech_agents)
        elif operation == 3:
            self.view_adjust_operation(scene, task, tech_agents)
        elif operation == 4:
            self.put_back_deleted_operation(scene, task, tech_agents)
        elif operation == 5:
            self.revise_added_operation(scene, task, tech_agents)
        scene.past_operations.append(task)

    def addition_operation(self, scene, task, tech_agents):
        """ addition operation. 
        Participants: asset_select_agent, motion_agent

        Input:
            scene : Scene
                scene object.
            task : str
                a decomposed task, should be assigned to one/more agents
            tech_agents : dict
                a dictionary of technical agents, helping to reason the task
        Return:
            callback_message : str
                if encounter bugs, record them in callback_message to users
        """
        asset_select_agent = tech_agents['asset_select_agent']
        motion_agent = tech_agents['motion_agent']
        placement_mode = motion_agent.llm_reasoning_dependency(scene, task)
        if placement_mode['dependency'] == 0:
            placement_prior = motion_agent.llm_placement_wo_dependency(scene, task)
        else:
            valid_object_descriptors_for_cars_in_scene = ['x', 'y', 'u', 'v', 'depth', 'rgb']
            scene_object_description = {}
            for car_name, description_dict in scene.original_cars_dict.items():
                filtered_description_dict = {k: v for k, v in description_dict.items() if k in valid_object_descriptors_for_cars_in_scene}
                scene_object_description[car_name] = filtered_description_dict
            valid_object_descriptors_for_added_cars = ['color', 'type']
            for car_name, description_dict in scene.added_cars_dict.items():
                filtered_description_dict = {k: v for k, v in description_dict.items() if k in valid_object_descriptors_for_added_cars}
                filtered_description_dict['x'] = description_dict['placement_result'][0]
                filtered_description_dict['y'] = description_dict['placement_result'][1]
                filtered_description_dict['direction'] = description_dict['direction']
                scene_object_description[car_name] = filtered_description_dict
            placement_prior = motion_agent.llm_placement_w_dependency(scene, task, scene_object_description)
        asset_color_and_type = asset_select_agent.llm_selecting_asset(scene, task)
        motion_prior = motion_agent.llm_motion_planning(scene, task)
        added_car_name = scene.add_car({**asset_color_and_type, **placement_prior, **motion_prior})
        motion_agent.func_placement_and_motion_single_vehicle(scene, added_car_name)

    def deletion_operation(self, scene, task, tech_agents):
        """ deletion operation. 
        Participants: deletion_agent

        Input:
            scene : Scene
                scene object.
            task : str
                a decomposed task, should be assigned to one/more agents
            tech_agents : dict
                a dictionary of technical agents, helping to reason the task
        Return:
            callback_message : str
                if encounter bugs, record them in callback_message to users
        """
        deletion_agent = tech_agents['deletion_agent']
        valid_object_descriptors = ['u', 'v', 'depth', 'rgb']
        scene_object_description = {}
        for car_name, description_dict in scene.original_cars_dict.items():
            filtered_description_dict = {k: v for k, v in description_dict.items() if k in valid_object_descriptors}
            scene_object_description[car_name] = filtered_description_dict
        deletion_car_names = deletion_agent.llm_finding_deletion(scene, task, scene_object_description)
        for car_name in deletion_car_names:
            scene.remove_car(car_name)

    def view_adjust_operation(self, scene, task, tech_agents):
        """ view adjust operation. 
        Participants: view_adjust_agent

        Input:
            scene : Scene
                scene object.
            task : str
                a decomposed task, should be assigned to one/more agents
            tech_agents : dict
                a dictionary of technical agents, helping to reason the task
        Return:
            callback_message : str
                if encounter bugs, record them in callback_message to users
        """
        view_adjust_agent = tech_agents['view_adjust_agent']
        is_ego_motion = view_adjust_agent.llm_reasoning_ego_motion(scene, task)
        if is_ego_motion:
            start_frame_in_nerf, end_frame_in_nerf = view_adjust_agent.llm_view_motion_gen(scene, task)
            view_adjust_agent.func_generate_extrinsic(scene, start_frame_in_nerf, end_frame_in_nerf)
        else:
            delta_extrinsic = view_adjust_agent.llm_view_adjust(scene, task)
            view_adjust_agent.func_update_extrinsic(scene, delta_extrinsic)

    def put_back_deleted_operation(self, scene, task, tech_agents):
        """ put back deleted operation. 
        Participants: deletion_agent

        Input:
            scene : Scene
                scene object.
            task : str
                a decomposed task, should be assigned to one/more agents
            tech_agents : dict
                a dictionary of technical agents, helping to reason the task
        Return:
            callback_message : str
                if encounter bugs, record them in callback_message to users
        """
        deletion_agent = tech_agents['deletion_agent']
        valid_object_descriptors = ['u', 'v', 'depth', 'rgb']
        scene_object_description = {}
        for car_name, description_dict in scene.original_cars_dict.items():
            filtered_description_dict = {k: v for k, v in description_dict.items() if k in valid_object_descriptors}
            scene_object_description[car_name] = filtered_description_dict
        put_back_car_names = deletion_agent.llm_putting_back_deletion(scene, task, scene_object_description)
        for car_name in put_back_car_names:
            scene.removed_cars.remove(car_name)

    def revise_added_operation(self, scene, task, tech_agents):
        """ revised added vehicle 
        Participants: asset_select_agent, motion_agent

        Input:
            scene : Scene
                scene object.
            task : str
                a decomposed task, should be assigned to one/more agents
            tech_agents : dict
                a dictionary of technical agents, helping to reason the task
        Return:
            callback_message : str
                if encounter bugs, record them in callback_message to users
        """
        asset_select_agent = tech_agents['asset_select_agent']
        motion_agent = tech_agents['motion_agent']
        for added_car_name, added_car_info in scene.added_cars_dict.items():
            added_car_info['x'] = added_car_info['motion'][0][0]
            added_car_info['y'] = added_car_info['motion'][0][1]
        added_cars_short_dict = copy.deepcopy(scene.added_cars_dict)
        for added_car_name, added_car_info in added_cars_short_dict.items():
            added_car_info.pop('motion')
            if 'mode' in added_car_info:
                added_car_info.pop('mode')
                added_car_info.pop('distance_constraint')
                added_car_info.pop('distance_min_max')
                added_car_info.pop('need_placement_and_motion')
        modified_car_dict = asset_select_agent.llm_revise_added_cars(scene, task, added_cars_short_dict)
        for modified_car_name, modified_car_info in modified_car_dict.items():
            scene.added_cars_dict[modified_car_name]['color'] = modified_car_info['color']
            scene.added_cars_dict[modified_car_name]['type'] = modified_car_info['type']
            scene.added_cars_dict[modified_car_name]['need_placement_and_motion'] = False
            check_attributes = ['action', 'speed', 'direction', 'x', 'y']
            for attri in check_attributes:
                if scene.added_cars_dict[modified_car_name][attri] != modified_car_info[attri]:
                    scene.added_cars_dict[modified_car_name]['need_placement_and_motion'] = True
                    scene.added_cars_dict[modified_car_name][attri] = modified_car_info[attri]
            motion_agent.func_placement_and_motion_single_vehicle(scene, modified_car_name)

def addition_operation(self, scene, task, tech_agents):
    """ addition operation. 
        Participants: asset_select_agent, motion_agent

        Input:
            scene : Scene
                scene object.
            task : str
                a decomposed task, should be assigned to one/more agents
            tech_agents : dict
                a dictionary of technical agents, helping to reason the task
        Return:
            callback_message : str
                if encounter bugs, record them in callback_message to users
        """
    asset_select_agent = tech_agents['asset_select_agent']
    motion_agent = tech_agents['motion_agent']
    placement_mode = motion_agent.llm_reasoning_dependency(scene, task)
    if placement_mode['dependency'] == 0:
        placement_prior = motion_agent.llm_placement_wo_dependency(scene, task)
    else:
        valid_object_descriptors_for_cars_in_scene = ['x', 'y', 'u', 'v', 'depth', 'rgb']
        scene_object_description = {}
        for car_name, description_dict in scene.original_cars_dict.items():
            filtered_description_dict = {k: v for k, v in description_dict.items() if k in valid_object_descriptors_for_cars_in_scene}
            scene_object_description[car_name] = filtered_description_dict
        valid_object_descriptors_for_added_cars = ['color', 'type']
        for car_name, description_dict in scene.added_cars_dict.items():
            filtered_description_dict = {k: v for k, v in description_dict.items() if k in valid_object_descriptors_for_added_cars}
            filtered_description_dict['x'] = description_dict['placement_result'][0]
            filtered_description_dict['y'] = description_dict['placement_result'][1]
            filtered_description_dict['direction'] = description_dict['direction']
            scene_object_description[car_name] = filtered_description_dict
        placement_prior = motion_agent.llm_placement_w_dependency(scene, task, scene_object_description)
    asset_color_and_type = asset_select_agent.llm_selecting_asset(scene, task)
    motion_prior = motion_agent.llm_motion_planning(scene, task)
    added_car_name = scene.add_car({**asset_color_and_type, **placement_prior, **motion_prior})
    motion_agent.func_placement_and_motion_single_vehicle(scene, added_car_name)

def revise_added_operation(self, scene, task, tech_agents):
    """ revised added vehicle 
        Participants: asset_select_agent, motion_agent

        Input:
            scene : Scene
                scene object.
            task : str
                a decomposed task, should be assigned to one/more agents
            tech_agents : dict
                a dictionary of technical agents, helping to reason the task
        Return:
            callback_message : str
                if encounter bugs, record them in callback_message to users
        """
    asset_select_agent = tech_agents['asset_select_agent']
    motion_agent = tech_agents['motion_agent']
    for added_car_name, added_car_info in scene.added_cars_dict.items():
        added_car_info['x'] = added_car_info['motion'][0][0]
        added_car_info['y'] = added_car_info['motion'][0][1]
    added_cars_short_dict = copy.deepcopy(scene.added_cars_dict)
    for added_car_name, added_car_info in added_cars_short_dict.items():
        added_car_info.pop('motion')
        if 'mode' in added_car_info:
            added_car_info.pop('mode')
            added_car_info.pop('distance_constraint')
            added_car_info.pop('distance_min_max')
            added_car_info.pop('need_placement_and_motion')
    modified_car_dict = asset_select_agent.llm_revise_added_cars(scene, task, added_cars_short_dict)
    for modified_car_name, modified_car_info in modified_car_dict.items():
        scene.added_cars_dict[modified_car_name]['color'] = modified_car_info['color']
        scene.added_cars_dict[modified_car_name]['type'] = modified_car_info['type']
        scene.added_cars_dict[modified_car_name]['need_placement_and_motion'] = False
        check_attributes = ['action', 'speed', 'direction', 'x', 'y']
        for attri in check_attributes:
            if scene.added_cars_dict[modified_car_name][attri] != modified_car_info[attri]:
                scene.added_cars_dict[modified_car_name]['need_placement_and_motion'] = True
                scene.added_cars_dict[modified_car_name][attri] = modified_car_info[attri]
        motion_agent.func_placement_and_motion_single_vehicle(scene, modified_car_name)

def add_wait_timesteps(traj, t, wait_timesteps):
    traj_out = traj.copy()
    T = traj_out.shape[0]
    if t + wait_timesteps > T:
        traj_out = interpolate_uniformly(traj[:t], T)
    else:
        traj_out[:t + wait_timesteps] = interpolate_uniformly(traj[:t], t + wait_timesteps)
        traj_out[t + wait_timesteps:] = traj[t:-wait_timesteps]
    return traj_out

def calculate_speed_increase(front_car_traj, rear_car_traj, safe_distance=7):
    distances = np.linalg.norm(rear_car_traj - front_car_traj, axis=1)
    front_car_speeds = np.linalg.norm(np.diff(front_car_traj, axis=0), axis=1)
    rear_car_speeds = np.linalg.norm(np.diff(rear_car_traj, axis=0), axis=1)
    relative_speeds = rear_car_speeds - front_car_speeds
    time_to_collision = (distances[1:] - safe_distance) / relative_speeds
    min_time_to_collision = np.min(time_to_collision[relative_speeds > 0])
    if np.any(distances > safe_distance) or min_time_to_collision > 0:
        return 1.0
    speed_increase = 1 + (safe_distance - distances[1:]) / (relative_speeds * min_time_to_collision)
    return np.max(speed_increase)

