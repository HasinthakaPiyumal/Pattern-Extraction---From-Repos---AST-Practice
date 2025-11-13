# Cluster 9

class BoxRegressor(object):

    def __init__(self, camera_matrix, pred_size, pred_keypoints, pred_distance):
        super(BoxRegressor, self).__init__()
        self.P = camera_matrix
        self.P_pseudo_inverse = np.linalg.pinv(self.P)
        self.pred_keypoints = pred_keypoints
        self.pred_size = pred_size
        self.pred_distance = pred_distance

    def _residuals(self, params):
        [h, w, l, x, y, z, rot_y] = params
        projected_keypoints = get_keypoints(np.array([x, y, z]), h, w, l, rot_y, self.P)
        resids_keypoints = projected_keypoints - self.pred_keypoints
        resids_keypoints = resids_keypoints.flatten()
        resids_size_regularization = np.array([h - self.pred_size[0], w - self.pred_size[1], l - self.pred_size[2]])
        resids_distance_regularization = np.array([np.linalg.norm(params[3:6]) - self.pred_distance])
        resids = np.append(resids_keypoints, 100 * resids_size_regularization)
        resids = np.append(resids, 10 * resids_distance_regularization)
        return resids

    def _initial_guess(self):
        h, w, l = self.pred_size
        img_keypoints_center_hom = [np.mean(self.pred_keypoints[:, 0]), np.mean(self.pred_keypoints[:, 1]), 1]
        l0 = np.dot(self.P_pseudo_inverse, img_keypoints_center_hom)
        l0 = l0[:3] / l0[3]
        if l0[2] < 0:
            l0[0] = -l0[0]
            l0[2] = -l0[2]
        [x0, y0, z0] = l0 / np.linalg.norm(l0) * self.pred_distance
        rot_y = -np.pi / 2
        return [h, w, l, x0, y0, z0, rot_y]

    def solve(self):
        x0 = self._initial_guess()
        ls_results = []
        costs = []
        for rot_y in [-2, -1, 0, 1]:
            x0[6] = rot_y * np.pi / 2
            ls_result = least_squares(self._residuals, x0, jac='3-point')
            ls_results.append(ls_result)
            costs.append(ls_result.cost)
        self.result = ls_results[np.argmin(costs)]
        params = self.result.x
        return params

def solve(self):
    x0 = self._initial_guess()
    ls_results = []
    costs = []
    for rot_y in [-2, -1, 0, 1]:
        x0[6] = rot_y * np.pi / 2
        ls_result = least_squares(self._residuals, x0, jac='3-point')
        ls_results.append(ls_result)
        costs.append(ls_result.cost)
    self.result = ls_results[np.argmin(costs)]
    params = self.result.x
    return params

