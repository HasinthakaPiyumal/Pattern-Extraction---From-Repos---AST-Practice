# Cluster 118

class DetectionTracksChallengeStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.InitializePlanner = channel.unary_unary('/challenge_protocol.DetectionTracksChallenge/InitializePlanner', request_serializer=challenge__pb2.PlannerInitializationLight.SerializeToString, response_deserializer=challenge__pb2.Empty.FromString)
        self.ComputeTrajectory = channel.unary_unary('/challenge_protocol.DetectionTracksChallenge/ComputeTrajectory', request_serializer=challenge__pb2.PlannerInput.SerializeToString, response_deserializer=challenge__pb2.Trajectory.FromString)

def __init__(self, channel):
    """Constructor.

        Args:
            channel: A grpc.Channel.
        """
    self.InitializePlanner = channel.unary_unary('/challenge_protocol.DetectionTracksChallenge/InitializePlanner', request_serializer=challenge__pb2.PlannerInitializationLight.SerializeToString, response_deserializer=challenge__pb2.Empty.FromString)
    self.ComputeTrajectory = channel.unary_unary('/challenge_protocol.DetectionTracksChallenge/ComputeTrajectory', request_serializer=challenge__pb2.PlannerInput.SerializeToString, response_deserializer=challenge__pb2.Trajectory.FromString)

class DetectionTracksChallenge(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def InitializePlanner(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/challenge_protocol.DetectionTracksChallenge/InitializePlanner', challenge__pb2.PlannerInitializationLight.SerializeToString, challenge__pb2.Empty.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def ComputeTrajectory(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/challenge_protocol.DetectionTracksChallenge/ComputeTrajectory', challenge__pb2.PlannerInput.SerializeToString, challenge__pb2.Trajectory.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

@staticmethod
def InitializePlanner(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
    return grpc.experimental.unary_unary(request, target, '/challenge_protocol.DetectionTracksChallenge/InitializePlanner', challenge__pb2.PlannerInitializationLight.SerializeToString, challenge__pb2.Empty.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

@staticmethod
def ComputeTrajectory(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
    return grpc.experimental.unary_unary(request, target, '/challenge_protocol.DetectionTracksChallenge/ComputeTrajectory', challenge__pb2.PlannerInput.SerializeToString, challenge__pb2.Trajectory.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

