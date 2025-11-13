# Cluster 10

class JointConstraint:
    """
    This is an uncollidable constraint that bounds two entities in the specified anchor points at the specified distance
    """

    def __init__(self, entity_a: vmas.simulator.core.Entity, entity_b: vmas.simulator.core.Entity, anchor_a: Tuple[float, float]=(0.0, 0.0), anchor_b: Tuple[float, float]=(0.0, 0.0), dist: float=0.0, rotate: bool=True, fixed_rotation: Optional[float]=None):
        assert entity_a != entity_b, 'Cannot join same entity'
        for anchor in (anchor_a, anchor_b):
            assert max(anchor) <= 1 and min(anchor) >= -1, f'Joint anchor points should be between -1 and 1, got {anchor}'
        assert dist >= 0, f'Joint dist must be >= 0, got {dist}'
        if fixed_rotation is not None:
            assert not rotate, 'If fixed rotation is provided, rotate should be False'
        if rotate:
            assert fixed_rotation is None, 'If you provide a fixed rotation, rotate should be False'
            fixed_rotation = 0.0
        self.entity_a = entity_a
        self.entity_b = entity_b
        self.anchor_a = anchor_a
        self.anchor_b = anchor_b
        self.dist = dist
        self.fixed_rotation = fixed_rotation
        self.rotate = rotate
        self._delta_anchor_tensor_map = {}

    def _delta_anchor_tensor(self, entity):
        if entity not in self._delta_anchor_tensor_map:
            if entity == self.entity_a:
                anchor = self.anchor_a
            elif entity == self.entity_b:
                anchor = self.anchor_b
            else:
                raise AssertionError()
            delta_anchor_tensor = torch.tensor(entity.shape.get_delta_from_anchor(anchor), device=entity.state.pos.device).unsqueeze(0).expand(entity.state.pos.shape)
            self._delta_anchor_tensor_map[entity] = delta_anchor_tensor
        self._delta_anchor_tensor_map[entity] = self._delta_anchor_tensor_map[entity].to(entity.state.pos.device)
        return self._delta_anchor_tensor_map[entity]

    def get_delta_anchor(self, entity: vmas.simulator.core.Entity):
        return vmas.simulator.utils.TorchUtils.rotate_vector(self._delta_anchor_tensor(entity), entity.state.rot)

    def pos_point(self, entity: vmas.simulator.core.Entity):
        return entity.state.pos + self.get_delta_anchor(entity)

    def render(self, env_index: int=0) -> List[Geom]:
        if self.dist == 0:
            return []
        from vmas.simulator import rendering
        geoms: List[rendering.Geom] = []
        joint_line = rendering.Line((-self.dist / 2, 0), (self.dist / 2, 0), width=UNCOLLIDABLE_JOINT_RENDERING_WIDTH)
        pos_point_a = self.pos_point(self.entity_a)[env_index]
        pos_point_b = self.pos_point(self.entity_b)[env_index]
        angle = torch.atan2(pos_point_b[vmas.simulator.utils.Y] - pos_point_a[vmas.simulator.utils.Y], pos_point_b[vmas.simulator.utils.X] - pos_point_a[vmas.simulator.utils.X])
        xform = rendering.Transform()
        xform.set_translation(*(pos_point_a + pos_point_b) / 2)
        xform.set_rotation(angle)
        joint_line.add_attr(xform)
        geoms.append(joint_line)
        return geoms

def pos_point(self, entity: vmas.simulator.core.Entity):
    return entity.state.pos + self.get_delta_anchor(entity)

