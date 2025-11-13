# Cluster 42

class PhysicalWorld(cocos.layer.Layer):
    """Physical world, which may be rendered."""
    fps = 50
    physical_scale = 32.0
    n_actions = 0

    def __init__(self, width, height):
        super(PhysicalWorld, self).__init__()
        self._contacts = ContactListener()
        self._filter = ContactFilter()
        self._engine = box_2d.b2World(gravity=(0, 0), contactListener=self._contacts, contactFilter=self._filter)
        self._width, self._height = (width, height)
        self._destroy_queue = []
        self.add(cocos.layer.ColorLayer(0, 0, 0, 255))
        self._batch = cocos.batch.BatchNode()
        self.add(self._batch)
        self.seed()
        self.create_world(self._batch)
        self.reset_world()
        self._terminal = False

    def create_world(self, parent):
        """Create the physical world."""
        raise NotImplementedError

    def reset_world(self):
        """Reset the world."""
        self._terminal = False

    def act(self, action):
        """Perform an external action in the world."""
        pass

    def seed(self, seed=None):
        """Setup random number generator."""
        self.np_random, seed = seeding.np_random(seed)
        return seed

    @property
    def is_terminal(self):
        return self._terminal

    @property
    def engine(self):
        """Physics engine world."""
        return self._engine

    @property
    def ground(self):
        """Ground body."""
        return self._ground

    @property
    def parameters(self):
        """World-defining parameters."""
        return {}

    def destroy_body(self, body):
        """Queue specific body for destruction."""
        self._destroy_queue.append(body)

    def process_destroy_queue(self):
        """Process any pending object destructions."""
        for body in self._destroy_queue:
            self._engine.DestroyBody(body)
        self._destroy_queue = []

    def step(self):
        """Perform one simulation step."""
        self.process_destroy_queue()
        self._engine.Step(1.0 / self.fps, 6 * 30, 2 * 30)
        self._engine.ClearForces()

        def step_node(node):
            if not isinstance(node, PhysicalObject):
                return
            node.step()
        self.walk(step_node)

def process_destroy_queue(self):
    """Process any pending object destructions."""
    for body in self._destroy_queue:
        self._engine.DestroyBody(body)
    self._destroy_queue = []

