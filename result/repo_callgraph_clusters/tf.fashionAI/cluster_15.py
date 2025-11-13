# Cluster 15

class _PerGraphState(object):
    """Gradient reduction related state of a Tensorflow graph."""

    def __init__(self):
        self._collected_grads_and_vars = defaultdict(list)
        self._current_tower_index = 0
        self._number_of_towers = 1
        self._loss_reduction = None
        self._variable_scope = None
        self._name_scope = None
        self._has_tower_optimizer_been_used = False

    def collect_gradients(self, grads_and_vars):
        self._collected_grads_and_vars[self._current_tower_index].append(grads_and_vars)

    def get_latest_gradients_from_all_towers(self):
        """Get gradients across towers for the last called optimizer."""
        grads_and_vars = []
        index_of_last_gradients = len(self._collected_grads_and_vars[self._current_tower_index]) - 1
        for tower_id in range(self._current_tower_index + 1):
            grads_and_vars.extend(self._collected_grads_and_vars[tower_id][index_of_last_gradients])
        return grads_and_vars

    def set_reduction_across_towers(self, loss_reduction, number_of_towers):
        self._loss_reduction = loss_reduction
        self._number_of_towers = number_of_towers

    @contextmanager
    def tower(self, tower_id, var_scope, name_scope):
        if tower_id == 0:
            self._variable_scope = var_scope
            self._name_scope = name_scope
        self._current_tower_index = tower_id
        yield

    @property
    def scopes_of_the_first_tower(self):
        return (self._variable_scope, self._name_scope)

    @property
    def is_the_last_tower(self):
        return self._current_tower_index == self._number_of_towers - 1

    @property
    def number_of_towers(self):
        return self._number_of_towers

    @property
    def loss_reduction(self):
        return self._loss_reduction

    @property
    def has_tower_optimizer_been_used(self):
        return self._has_tower_optimizer_been_used

    @has_tower_optimizer_been_used.setter
    def has_tower_optimizer_been_used(self, value):
        self._has_tower_optimizer_been_used = value

    def did_towers_have_same_optimizer_calls(self):
        total_number_of_grads = sum([len(grads) for _, grads in six.iteritems(self._collected_grads_and_vars)])
        return total_number_of_grads % self._number_of_towers == 0

def __init__(self):
    self._collected_grads_and_vars = defaultdict(list)
    self._current_tower_index = 0
    self._number_of_towers = 1
    self._loss_reduction = None
    self._variable_scope = None
    self._name_scope = None
    self._has_tower_optimizer_been_used = False

