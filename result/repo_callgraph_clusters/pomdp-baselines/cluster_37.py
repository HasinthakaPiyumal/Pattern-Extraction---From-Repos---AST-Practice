# Cluster 37

class RoboschoolTrackDistSuccessMixin(EnvBinarySuccessMixin):
    """Treat reaching certain distance on track as a success."""

    def is_success(self):
        """Returns True is current state indicates success, False otherwise

        x=100 correlates to the end of the track on Roboschool,
        but with the default 1000 max episode length most (all?) agents
        won't reach it (DD PPO2 Hopper reaches ~40), so we use something lower
        """
        target_dist = 20
        if self.robot_body.pose().xyz()[0] >= target_dist:
            return True
        else:
            return False

def is_success(self):
    """Returns True is current state indicates success, False otherwise

        x=100 correlates to the end of the track on Roboschool,
        but with the default 1000 max episode length most (all?) agents
        won't reach it (DD PPO2 Hopper reaches ~40), so we use something lower
        """
    target_dist = 20
    if self.robot_body.pose().xyz()[0] >= target_dist:
        return True
    else:
        return False

