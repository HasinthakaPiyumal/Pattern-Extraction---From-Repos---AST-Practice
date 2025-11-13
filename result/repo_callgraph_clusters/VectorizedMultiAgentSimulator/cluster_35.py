# Cluster 35

class HeuristicPolicy(BaseHeuristicPolicy):

    def __init__(self, clf_epsilon=0.2, clf_slack=100.0, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.clf_epsilon = clf_epsilon
        self.clf_slack = clf_slack

    def compute_action(self, observation: Tensor, u_range: Tensor) -> Tensor:
        """
        QP inputs:
        These values need to computed apriri based on observation before passing into QP

        V: Lyapunov function value
        lfV: Lie derivative of Lyapunov function
        lgV: Lie derivative of Lyapunov function
        CLF_slack: CLF constraint slack variable

        QP outputs:
        u: action
        CLF_slack: CLF constraint slack variable, 0 if CLF constraint is satisfied
        """
        import cvxpy as cp
        from cvxpylayers.torch import CvxpyLayer
        self.n_env = observation.shape[0]
        self.device = observation.device
        agent_pos = observation[:, :2]
        agent_vel = observation[:, 2:4]
        goal_pos = -1.0 * (observation[:, 4:6] - agent_pos)
        V_value = (agent_pos[:, X] - goal_pos[:, X]) ** 2 + 0.5 * (agent_pos[:, X] - goal_pos[:, X]) * agent_vel[:, X] + agent_vel[:, X] ** 2 + (agent_pos[:, Y] - goal_pos[:, Y]) ** 2 + 0.5 * (agent_pos[:, Y] - goal_pos[:, Y]) * agent_vel[:, Y] + agent_vel[:, Y] ** 2
        LfV_val = (2 * (agent_pos[:, X] - goal_pos[:, X]) + agent_vel[:, X]) * agent_vel[:, X] + (2 * (agent_pos[:, Y] - goal_pos[:, Y]) + agent_vel[:, Y]) * agent_vel[:, Y]
        LgV_vals = torch.stack([0.5 * (agent_pos[:, X] - goal_pos[:, X]) + 2 * agent_vel[:, X], 0.5 * (agent_pos[:, Y] - goal_pos[:, Y]) + 2 * agent_vel[:, Y]], dim=1)
        u = cp.Variable(2)
        V_param = cp.Parameter(1)
        lfV_param = cp.Parameter(1)
        lgV_params = cp.Parameter(2)
        clf_slack = cp.Variable(1)
        constraints = []
        qp_objective = cp.Minimize(cp.sum_squares(u) + self.clf_slack * clf_slack ** 2)
        constraints += [u <= u_range]
        constraints += [u >= -u_range]
        constraints += [lfV_param + lgV_params @ u + self.clf_epsilon * V_param + clf_slack <= 0]
        QP_problem = cp.Problem(qp_objective, constraints)
        QP_controller = CvxpyLayer(QP_problem, parameters=[V_param, lfV_param, lgV_params], variables=[u])
        CVXpylayer_parameters = [V_value.unsqueeze(1), LfV_val.unsqueeze(1), LgV_vals]
        action = QP_controller(*CVXpylayer_parameters, solver_args={'max_iters': 500})[0]
        return action

def compute_action(self, observation: Tensor, u_range: Tensor) -> Tensor:
    """
        QP inputs:
        These values need to computed apriri based on observation before passing into QP

        V: Lyapunov function value
        lfV: Lie derivative of Lyapunov function
        lgV: Lie derivative of Lyapunov function
        CLF_slack: CLF constraint slack variable

        QP outputs:
        u: action
        CLF_slack: CLF constraint slack variable, 0 if CLF constraint is satisfied
        """
    import cvxpy as cp
    from cvxpylayers.torch import CvxpyLayer
    self.n_env = observation.shape[0]
    self.device = observation.device
    agent_pos = observation[:, :2]
    agent_vel = observation[:, 2:4]
    goal_pos = -1.0 * (observation[:, 4:6] - agent_pos)
    V_value = (agent_pos[:, X] - goal_pos[:, X]) ** 2 + 0.5 * (agent_pos[:, X] - goal_pos[:, X]) * agent_vel[:, X] + agent_vel[:, X] ** 2 + (agent_pos[:, Y] - goal_pos[:, Y]) ** 2 + 0.5 * (agent_pos[:, Y] - goal_pos[:, Y]) * agent_vel[:, Y] + agent_vel[:, Y] ** 2
    LfV_val = (2 * (agent_pos[:, X] - goal_pos[:, X]) + agent_vel[:, X]) * agent_vel[:, X] + (2 * (agent_pos[:, Y] - goal_pos[:, Y]) + agent_vel[:, Y]) * agent_vel[:, Y]
    LgV_vals = torch.stack([0.5 * (agent_pos[:, X] - goal_pos[:, X]) + 2 * agent_vel[:, X], 0.5 * (agent_pos[:, Y] - goal_pos[:, Y]) + 2 * agent_vel[:, Y]], dim=1)
    u = cp.Variable(2)
    V_param = cp.Parameter(1)
    lfV_param = cp.Parameter(1)
    lgV_params = cp.Parameter(2)
    clf_slack = cp.Variable(1)
    constraints = []
    qp_objective = cp.Minimize(cp.sum_squares(u) + self.clf_slack * clf_slack ** 2)
    constraints += [u <= u_range]
    constraints += [u >= -u_range]
    constraints += [lfV_param + lgV_params @ u + self.clf_epsilon * V_param + clf_slack <= 0]
    QP_problem = cp.Problem(qp_objective, constraints)
    QP_controller = CvxpyLayer(QP_problem, parameters=[V_param, lfV_param, lgV_params], variables=[u])
    CVXpylayer_parameters = [V_value.unsqueeze(1), LfV_val.unsqueeze(1), LgV_vals]
    action = QP_controller(*CVXpylayer_parameters, solver_args={'max_iters': 500})[0]
    return action

