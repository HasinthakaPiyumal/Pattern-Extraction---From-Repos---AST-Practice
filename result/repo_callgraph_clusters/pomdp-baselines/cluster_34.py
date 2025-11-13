# Cluster 34

class SpaceInvaders(GymEnvironment):
    """Space invaders Gym environment."""
    worlds = {'baseline': SpaceInvadersWorld, 'single_line': SingleLineSpaceInvadersWorld, 'inf_shields': InfiniteShieldsSpaceInvadersWorld, 'offset_player': OffsetPlayerSpaceInvadersWorld, 'offset_player150': OffsetPlayer150SpaceInvadersWorld, 'random_offset_player': RandomOffsetPlayerSpaceInvadersWorld, 'side_obstacle': SideObstacleSpaceInvadersWorld, 'left_side_obstacle': LeftSideObstacleSpaceInvadersWorld, 'right_side_obstacle': RightSideObstacleSpaceInvadersWorld, 'random_side_obstacle': RandomSideObstacleSpaceInvadersWorld, 'single_invader': SingleInvaderSpaceInvadersWorld, 'one_color': OneColorSpaceInvadersWorld, 'scaled_80': Scaled80SpaceInvadersWorld, 'scaled_90': Scaled90SpaceInvadersWorld, 'scaled_95': Scaled95SpaceInvadersWorld, 'scaled_99': Scaled99SpaceInvadersWorld, 'random_scaled': RandomScaledSpaceInvadersWorld, 'offset_player_set_a': OffsetPlayerSetASpaceInvadersWorld, 'offset_player_set_b': OffsetPlayerSetBSpaceInvadersWorld, 'scaled_set_a': ScaledSetASpaceInvadersWorld, 'scaled_set_b': ScaledSetBSpaceInvadersWorld, 'action_strength_set_a': ActionStrengthSetASpaceInvadersWorld, 'action_strength_set_b': ActionStrengthSetBSpaceInvadersWorld, 'multi_parameter_set_a': MultiParameterSetASpaceInvadersWorld, 'multi_parameter_set_b': MultiParameterSetBSpaceInvadersWorld}

    def get_action_meanings(self):
        return ['NOOP', 'LEFT', 'RIGHT', 'FIRE']

    def get_keys_to_action(self):
        return {(): 0, (ord('a'),): 1, (ord('d'),): 2, (ord('s'),): 3, (ord('a'), ord('d')): 0}

def get_keys_to_action(self):
    return {(): 0, (ord('a'),): 1, (ord('d'),): 2, (ord('s'),): 3, (ord('a'), ord('d')): 0}

class Breakout(GymEnvironment):
    """Breakout Gym environment."""
    worlds = {'baseline': BreakoutWorld, 'offset_paddle_50': OffsetPaddle50BreakoutWorld, 'offset_paddle_75': OffsetPaddle75BreakoutWorld, 'offset_paddle_100': OffsetPaddle100BreakoutWorld, 'offset_paddle_125': OffsetPaddle125BreakoutWorld, 'offset_paddle_150': OffsetPaddle150BreakoutWorld, 'random_offset_paddle': RandomOffsetPaddleBreakoutWorld, 'physically_offset_paddle_125': PhysicallyOffsetPaddle125BreakoutWorld, 'obstacle': ObstacleBreakoutWorld, 'side_obstacle': SideObstacleBreakoutWorld, 'left_side_obstacle': LeftSideObstacleBreakoutWorld, 'right_side_obstacle': RightSideObstacleBreakoutWorld, 'random_side_obstacle': RandomSideObstacleBreakoutWorld, 'small_paddle': SmallPaddleBreakoutWorld, 'small10_paddle': Small10PaddleBreakoutWorld, 'small20_paddle': Small20PaddleBreakoutWorld, 'small30_paddle': Small30PaddleBreakoutWorld, 'random_small_paddle': RandomSmallPaddleBreakoutWorld, 'big_ball': BigBallBreakoutWorld, 'huge_ball': HugeBallBreakoutWorld, 'square_ball': SquareBallBreakoutWorld, 'one_color': OneColorBreakoutWorld, 'scaled_80': Scaled80BreakoutWorld, 'scaled_90': Scaled90BreakoutWorld, 'scaled_95': Scaled95BreakoutWorld, 'scaled_99': Scaled99BreakoutWorld, 'random_scaled': RandomScaledBreakoutWorld, 'offset_paddle_set_a': OffsetPaddleSetABreakoutWorld, 'offset_paddle_set_b': OffsetPaddleSetBBreakoutWorld, 'rotated_paddle_set_a': RotatedPaddleSetABreakoutWorld, 'rotated_paddle_set_b': RotatedPaddleSetBBreakoutWorld, 'offset_bricks_set_a': OffsetBricksSetABreakoutWorld, 'offset_bricks_set_b': OffsetBricksSetBBreakoutWorld, 'scaled_set_a': ScaledSetABreakoutWorld, 'scaled_set_b': ScaledSetBBreakoutWorld, 'action_strength_set_a': ActionStrengthSetABreakoutWorld, 'action_strength_set_b': ActionStrengthSetBBreakoutWorld, 'side_obstacle_set_a': SideObstacleSetABreakoutWorld, 'side_obstacle_set_b': SideObstacleSetBBreakoutWorld, 'multi_parameter_set_a': MultiParameterSetABreakoutWorld, 'multi_parameter_set_b': MultiParameterSetBBreakoutWorld, 'multi_parameter_set_c': MultiParameterSetCBreakoutWorld, 'multi_parameter_set_d': MultiParameterSetDBreakoutWorld}

    def get_action_meanings(self):
        return ['NOOP', 'LEFT', 'RIGHT']

    def get_keys_to_action(self):
        return {(): 0, (ord('a'),): 1, (ord('d'),): 2, (ord('a'), ord('d')): 0}

def get_keys_to_action(self):
    return {(): 0, (ord('a'),): 1, (ord('d'),): 2, (ord('a'), ord('d')): 0}

