# Cluster 32

class Missile(PhysicalObject):
    """Missile."""

    def __init__(self, *args, **kwargs):
        super(Missile, self).__init__('missile.png', *args, **kwargs)

    def create_physical_entity(self):
        body = self._engine.CreateDynamicBody(position=self.physical_position, fixedRotation=True)
        body.CreatePolygonFixture(box=(self.width / 2.0 / self._world.physical_scale, self.height / 2.0 / self._world.physical_scale), density=1.0, friction=0.0, restitution=0.0)
        joint = box_2d.b2PrismaticJointDef()
        joint.Initialize(body, self._world.ground, body.worldCenter, (0.0, 1.0))
        joint.collideConnected = True
        self._engine.CreateJoint(joint)
        return body

    @classmethod
    def fire(cls, world, entity, impulse):
        """Fires a missile."""
        raise NotImplementedError

def create_physical_entity(self):
    body = self._engine.CreateDynamicBody(position=self.physical_position, fixedRotation=True)
    body.CreatePolygonFixture(box=(self.width / 2.0 / self._world.physical_scale, self.height / 2.0 / self._world.physical_scale), density=1.0, friction=0.0, restitution=0.0)
    joint = box_2d.b2PrismaticJointDef()
    joint.Initialize(body, self._world.ground, body.worldCenter, (0.0, 1.0))
    joint.collideConnected = True
    self._engine.CreateJoint(joint)
    return body

class Invader(PhysicalObject):
    """Invader."""
    TYPE_1 = 'invader_1'
    TYPE_2 = 'invader_2'
    TYPE_3 = 'invader_3'

    def __init__(self, *args, **kwargs):
        self._type = kwargs.pop('invader_type')
        kwargs.setdefault('color', (0, 255, 0))
        kwargs.setdefault('scale', 1)
        super(Invader, self).__init__('{}.png'.format(self._type), *args, **kwargs)

    def create_physical_entity(self):
        body = self._engine.CreateStaticBody(position=self.physical_position)
        body.CreatePolygonFixture(box=(self.width / 2.0 / self._world.physical_scale, self.height / 2.0 / self._world.physical_scale), density=1.0, friction=0.0, restitution=0.0)
        return body

def create_physical_entity(self):
    body = self._engine.CreateStaticBody(position=self.physical_position)
    body.CreatePolygonFixture(box=(self.width / 2.0 / self._world.physical_scale, self.height / 2.0 / self._world.physical_scale), density=1.0, friction=0.0, restitution=0.0)
    return body

class Shield(PhysicalObject):
    """Shield for the player."""

    def __init__(self, *args, **kwargs):
        self.health = kwargs.pop('health')
        kwargs.setdefault('color', (255, 240, 0))
        super(Shield, self).__init__('shield.png', *args, **kwargs)

    def create_physical_entity(self):
        body = self._engine.CreateStaticBody(position=self.physical_position)
        body.CreatePolygonFixture(box=(self.width / 2.0 / self._world.physical_scale, self.height / 2.0 / self._world.physical_scale), density=1.0, friction=0.0, restitution=0.0)
        return body

    def on_contact(self, other):
        """Shield loses health if anything touches it."""
        self.health -= 1
        if self.health <= 0:
            self.kill()

def create_physical_entity(self):
    body = self._engine.CreateStaticBody(position=self.physical_position)
    body.CreatePolygonFixture(box=(self.width / 2.0 / self._world.physical_scale, self.height / 2.0 / self._world.physical_scale), density=1.0, friction=0.0, restitution=0.0)
    return body

class PlayerShip(PhysicalObject):
    """Player ship."""

    def __init__(self, *args, **kwargs):
        super(PlayerShip, self).__init__('ship.png', *args, **kwargs)

    def create_physical_entity(self):
        body = self._engine.CreateDynamicBody(position=self.physical_position, linearDamping=0.99, fixedRotation=True)
        body.CreatePolygonFixture(box=(self.width / 2.0 / self._world.physical_scale, self.height / 2.0 / self._world.physical_scale), density=1.0, friction=0.0, restitution=0.0)
        joint = box_2d.b2PrismaticJointDef()
        joint.Initialize(body, self._world.ground, body.worldCenter, (1.0, 0.0))
        joint.collideConnected = True
        self._engine.CreateJoint(joint)
        return body

def create_physical_entity(self):
    body = self._engine.CreateDynamicBody(position=self.physical_position, linearDamping=0.99, fixedRotation=True)
    body.CreatePolygonFixture(box=(self.width / 2.0 / self._world.physical_scale, self.height / 2.0 / self._world.physical_scale), density=1.0, friction=0.0, restitution=0.0)
    joint = box_2d.b2PrismaticJointDef()
    joint.Initialize(body, self._world.ground, body.worldCenter, (1.0, 0.0))
    joint.collideConnected = True
    self._engine.CreateJoint(joint)
    return body

class SideObstacle(PhysicalObject):
    """Side obstacle object."""

    def __init__(self, *args, **kwargs):
        kwargs['color'] = (80, 80, 80)
        super(SideObstacle, self).__init__('side_obstacle.png', *args, **kwargs)

    def create_physical_entity(self):
        body = self._engine.CreateStaticBody(position=self.physical_position)
        body.CreatePolygonFixture(box=(self.width / 2.0 / self._world.physical_scale, self.height / 2.0 / self._world.physical_scale), density=10.0, friction=0.0, restitution=0.0)
        return body

def create_physical_entity(self):
    body = self._engine.CreateStaticBody(position=self.physical_position)
    body.CreatePolygonFixture(box=(self.width / 2.0 / self._world.physical_scale, self.height / 2.0 / self._world.physical_scale), density=10.0, friction=0.0, restitution=0.0)
    return body

class Ball(PhysicalObject):
    """Ball object."""
    asset = 'ball.png'
    max_speed = 9.0

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('scale', 0.25)
        kwargs.setdefault('color', (208, 33, 82))
        super(Ball, self).__init__(self.asset, *args, **kwargs)

    def create_physical_entity(self):
        body = self._engine.CreateDynamicBody(position=self.physical_position, fixedRotation=True)
        body.CreateCircleFixture(radius=self.width / 2 / self._world.physical_scale, density=1.0, friction=0.0, restitution=1.0)
        return body

    def step(self):
        super(Ball, self).step()
        speed = self._body.linearVelocity.length
        if speed > self.max_speed:
            self._body.linearDamping = 0.5
        elif speed < self.max_speed:
            self._body.linearDamping = 0.0

    def on_contact(self, other):
        """Prevent the ball from bouncing in a straight line up and down."""
        velocity_x = self.body.linearVelocity[0]
        if abs(velocity_x) < 0.1:
            self.apply_impulse([self._world.np_random.uniform(-0.1, 0.1), 0.0])

def create_physical_entity(self):
    body = self._engine.CreateDynamicBody(position=self.physical_position, fixedRotation=True)
    body.CreateCircleFixture(radius=self.width / 2 / self._world.physical_scale, density=1.0, friction=0.0, restitution=1.0)
    return body

class Paddle(PhysicalObject):
    """Paddle object."""
    asset = 'paddle.png'

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('color', (255, 168, 0))
        super(Paddle, self).__init__(self.asset, *args, **kwargs)

    def create_physical_entity(self):
        body = self._engine.CreateDynamicBody(position=self.physical_position, angle=self.physical_rotation, linearDamping=0.99, fixedRotation=True)
        body.CreatePolygonFixture(box=(self.width / 2.0 / self._world.physical_scale, self.height / 2.0 / self._world.physical_scale), density=1.0, friction=0.0, restitution=0.0)
        joint = box_2d.b2PrismaticJointDef()
        joint.Initialize(body, self._world.ground, body.worldCenter, (1.0, 0.0))
        joint.collideConnected = True
        self._engine.CreateJoint(joint)
        return body

def create_physical_entity(self):
    body = self._engine.CreateDynamicBody(position=self.physical_position, angle=self.physical_rotation, linearDamping=0.99, fixedRotation=True)
    body.CreatePolygonFixture(box=(self.width / 2.0 / self._world.physical_scale, self.height / 2.0 / self._world.physical_scale), density=1.0, friction=0.0, restitution=0.0)
    joint = box_2d.b2PrismaticJointDef()
    joint.Initialize(body, self._world.ground, body.worldCenter, (1.0, 0.0))
    joint.collideConnected = True
    self._engine.CreateJoint(joint)
    return body

class Brick(PhysicalObject):
    """Brick object."""

    def __init__(self, *args, **kwargs):
        self.row = kwargs.pop('row')
        self.column = kwargs.pop('column')
        kwargs['color'] = self.get_color()
        super(Brick, self).__init__('brick.png', *args, **kwargs)

    def get_color(self):
        """Brick color."""
        colors = {0: (255, 0, 0), 1: (255, 174, 0), 2: (252, 255, 0), 3: (0, 255, 0), 4: (0, 0, 255)}
        return colors.get(self.row, (0, 0, 0))

    def get_score(self):
        """Score if the brick is destroyed."""
        scores = {0: 10, 1: 7, 2: 5, 3: 3, 4: 1}
        return scores.get(self.row, 0)

    def get_restitution(self):
        restitution = {0: 1.5, 1: 1.3, 2: 1.2, 3: 1.15, 4: 1.1}
        return restitution.get(self.row, 1.0)

    def create_physical_entity(self):
        body = self._engine.CreateStaticBody(position=self.physical_position)
        body.CreatePolygonFixture(box=(self.width / 2.0 / self._world.physical_scale, self.height / 2.0 / self._world.physical_scale), density=1.0, friction=0.0, restitution=self.get_restitution())
        return body

    def on_contact(self, other):
        """Destroy the brick on contact with the ball."""
        if not isinstance(other, Ball):
            return
        self.kill()
        ball_velocity_x = other.body.linearVelocity[0]
        if abs(ball_velocity_x) < 0.2:
            other.apply_impulse([0.2 * np.sign(ball_velocity_x), 0.0])
        self._world._score += self.get_score()

def create_physical_entity(self):
    body = self._engine.CreateStaticBody(position=self.physical_position)
    body.CreatePolygonFixture(box=(self.width / 2.0 / self._world.physical_scale, self.height / 2.0 / self._world.physical_scale), density=1.0, friction=0.0, restitution=self.get_restitution())
    return body

class Obstacle(PhysicalObject):
    """Obstacle object."""

    def __init__(self, *args, **kwargs):
        kwargs['color'] = (80, 80, 80)
        super(Obstacle, self).__init__('obstacle.png', *args, **kwargs)

    def create_physical_entity(self):
        body = self._engine.CreateStaticBody(position=self.physical_position)
        body.CreatePolygonFixture(box=(self.width / 2.0 / self._world.physical_scale, self.height / 2.0 / self._world.physical_scale), density=10.0, friction=0.0, restitution=0.0)
        return body

def create_physical_entity(self):
    body = self._engine.CreateStaticBody(position=self.physical_position)
    body.CreatePolygonFixture(box=(self.width / 2.0 / self._world.physical_scale, self.height / 2.0 / self._world.physical_scale), density=10.0, friction=0.0, restitution=0.0)
    return body

class SideObstacle(PhysicalObject):
    """Side obstacle object."""

    def __init__(self, *args, **kwargs):
        image = pyglet.resource.image('side_obstacle.png')
        width = kwargs.pop('width', None)
        if width is not None:
            image = image.get_region(0, 0, width, image.height)
        kwargs['color'] = (80, 80, 80)
        super(SideObstacle, self).__init__(image, *args, **kwargs)

    def create_physical_entity(self):
        body = self._engine.CreateStaticBody(position=self.physical_position)
        body.CreatePolygonFixture(box=(self.width / 2.0 / self._world.physical_scale, self.height / 2.0 / self._world.physical_scale), density=10.0, friction=0.0, restitution=0.0)
        return body

def create_physical_entity(self):
    body = self._engine.CreateStaticBody(position=self.physical_position)
    body.CreatePolygonFixture(box=(self.width / 2.0 / self._world.physical_scale, self.height / 2.0 / self._world.physical_scale), density=10.0, friction=0.0, restitution=0.0)
    return body

class SquareBall(Ball):
    """A square ball object."""
    asset = 'square.png'

    def create_physical_entity(self):
        body = self._engine.CreateDynamicBody(position=self.physical_position, fixedRotation=True)
        body.CreatePolygonFixture(box=(self.width / 2.0 / self._world.physical_scale, self.height / 2.0 / self._world.physical_scale), density=1.0, friction=0.0, restitution=1.0)
        return body

def create_physical_entity(self):
    body = self._engine.CreateDynamicBody(position=self.physical_position, fixedRotation=True)
    body.CreatePolygonFixture(box=(self.width / 2.0 / self._world.physical_scale, self.height / 2.0 / self._world.physical_scale), density=1.0, friction=0.0, restitution=1.0)
    return body

