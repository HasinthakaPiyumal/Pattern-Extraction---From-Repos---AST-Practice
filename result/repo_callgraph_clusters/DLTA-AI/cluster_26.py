# Cluster 26

class Sam_Predictor:

    def __init__(self, model_type, checkpoint_path, device):
        self.model_type = model_type
        self.checkpoint_path = checkpoint_path
        self.device = device
        self.model = sam_model_registry[model_type](checkpoint=checkpoint_path)
        self.model.to(device=self.device)
        self.predictor = SamPredictor(self.model)
        self.image = None
        self.mask_logit = None

    def set_new_image(self, image):
        self.image = image
        self.predictor.set_image(image)

    def clear_logit(self):
        self.mask_logit = None

    def predict(self, point_coords=None, point_labels=None, box=None, multimask_output=True, image=None):
        if box is None:
            if self.mask_logit is None:
                masks, scores, logits = self.predictor.predict(point_coords=point_coords, point_labels=point_labels, multimask_output=multimask_output)
            else:
                masks, scores, logits = self.predictor.predict(point_coords=point_coords, point_labels=point_labels, mask_input=self.mask_logit[None, :, :], multimask_output=multimask_output)
        elif len(box) == 1:
            input_box = np.array(box[0])
            masks, scores, logits = self.predictor.predict(point_coords=point_coords, point_labels=point_labels, box=input_box[None, :], multimask_output=multimask_output)
        else:
            input_box = np.array(box[0])
            box_tensor = torch.tensor(box, device=self.predictor.device)
            box_transformed = self.predictor.transform.apply_boxes_torch(box_tensor, image.shape[:2])
            masks, scores, logits = self.predictor.predict_torch(point_coords=None, point_labels=None, boxes=box_transformed, multimask_output=False)
        if multimask_output:
            if box is not None and len(box) != 1:
                logits = torch.Tensor.cpu(logits).numpy().reshape(-1, logits.shape[-2], logits.shape[-1])
                masks = torch.Tensor.cpu(masks).numpy().reshape(-1, masks.shape[-2], masks.shape[-1])
                scores = torch.Tensor.cpu(scores).numpy().reshape(-1)
            self.mask_logit = logits[np.argmax(scores), :, :]
            mask = masks[np.argmax(scores), :, :]
            score = np.max(scores)
        return (mask, score)

    def predict_batch(self, boxes=None, image=None):
        boxes = np.array(boxes)
        input_boxes = torch.tensor(boxes, device=self.predictor.device)
        transformed_boxes = self.predictor.transform.apply_boxes_torch(input_boxes, image.shape[:2])
        masks, scores, logits = self.predictor.predict_torch(point_coords=None, point_labels=None, boxes=transformed_boxes, multimask_output=False)
        return (masks, scores)

    def check_image(self, new_image):
        if not np.array_equal(self.image, new_image):
            self.mask_logit = None
            self.image = new_image
            self.predictor.set_image(new_image)
            return False
        return True

    def get_all_shapes(self, image, iou_threshold):
        self.mask_generator = SamAutomaticMaskGenerator(model=self.model)
        sam_result = self.mask_generator.generate(image)
        shapes = mathOps.OURnms_areaBased_fromSAM(sam_result, iou_threshold=iou_threshold)
        return shapes

def get_all_shapes(self, image, iou_threshold):
    self.mask_generator = SamAutomaticMaskGenerator(model=self.model)
    sam_result = self.mask_generator.generate(image)
    shapes = mathOps.OURnms_areaBased_fromSAM(sam_result, iou_threshold=iou_threshold)
    return shapes

