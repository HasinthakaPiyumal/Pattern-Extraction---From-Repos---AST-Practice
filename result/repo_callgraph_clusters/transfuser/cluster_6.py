# Cluster 6

class ActorSink(AtomicBehavior):
    """
    Implementation for a behavior that will indefinitely destroy actors
    that wander near a given location within a specified threshold.

    Important parameters:
    - actor_type_list: Type of CARLA actors to be spawned
    - sink_location: Location (carla.location) at which actors will be deleted
    - threshold: Distance around sink_location in which actors will be deleted

    A parallel termination behavior has to be used.
    """

    def __init__(self, sink_location, threshold, name='ActorSink'):
        """
        Setup class members
        """
        super(ActorSink, self).__init__(name)
        self._sink_location = sink_location
        self._threshold = threshold

    def update(self):
        new_status = py_trees.common.Status.RUNNING
        CarlaDataProvider.remove_actors_in_surrounding(self._sink_location, self._threshold)
        return new_status

def update(self):
    new_status = py_trees.common.Status.RUNNING
    CarlaDataProvider.remove_actors_in_surrounding(self._sink_location, self._threshold)
    return new_status

