# Cluster 39

class PhysicalObject(cocos.sprite.Sprite):
    """Sprite which is backed by a physical object."""

    def __init__(self, image, **kwargs):
        world = kwargs.pop('world', None)
        super(PhysicalObject, self).__init__(image, **kwargs)
        if world is not None:
            self._world = world
            self._engine = world.engine
            self._body = self.create_physical_entity()
            self._body.userData = self
        else:
            self._world = None
            self._engine = None
            self._body = None

    @property
    def body(self):
        """Physical body."""
        return self._body

    @property
    def physical_position(self):
        """Returns physical object position."""
        if getattr(self, '_body', None) is not None:
            return self._body.position
        return (self.position[0] / self._world.physical_scale, self.position[1] / self._world.physical_scale)

    @property
    def physical_rotation(self):
        """Returns physical object rotation (in radians)."""
        if getattr(self, '_body', None) is not None:
            return self._body.angle
        return -np.deg2rad(self.rotation)

    @property
    def visual_position(self):
        """Return visual object position."""
        if getattr(self, '_body', None) is None:
            return self.position
        return self._body.position * self._world.physical_scale

    @property
    def visual_rotation(self):
        """Return visual object rotation (in degrees)."""
        if getattr(self, '_body', None) is None:
            return self.rotation
        return -np.rad2deg(self._body.angle)

    def set_body_position(self, position):
        """Set object position."""
        self._body.position = (position[0] / self._world.physical_scale, position[1] / self._world.physical_scale)

    def stop_body(self):
        """Stop body movement."""
        self._body.linearVelocity = (0, 0)

    def create_physical_entity(self):
        """Create the entity in the physics engine."""
        raise NotImplementedError

    def step(self):
        """Update actual object based on physical entity."""
        if not self._body:
            return
        self.position = self.visual_position
        self.rotation = self.visual_rotation

    def kill(self):
        """Kill the given object."""
        if not self._body:
            return
        if self._engine is not None:
            self._world.destroy_body(self._body)
            self._body.userData = None
            self._body = None
        super(PhysicalObject, self).kill()

    def apply_impulse(self, vector):
        """Apply linear impulse to center of mass."""
        self._body.ApplyLinearImpulse(vector, self._body.worldCenter, True)

    def on_contact(self, other):
        """Handle contact with another body."""
        pass

    def should_collide(self, other):
        """Handle collision filtering with another body."""
        return True

def apply_impulse(self, vector):
    """Apply linear impulse to center of mass."""
    self._body.ApplyLinearImpulse(vector, self._body.worldCenter, True)

