# Cluster 119

def add_DetectionTracksChallengeServicer_to_server(servicer, server):
    rpc_method_handlers = {'InitializePlanner': grpc.unary_unary_rpc_method_handler(servicer.InitializePlanner, request_deserializer=challenge__pb2.PlannerInitializationLight.FromString, response_serializer=challenge__pb2.Empty.SerializeToString), 'ComputeTrajectory': grpc.unary_unary_rpc_method_handler(servicer.ComputeTrajectory, request_deserializer=challenge__pb2.PlannerInput.FromString, response_serializer=challenge__pb2.Trajectory.SerializeToString)}
    generic_handler = grpc.method_handlers_generic_handler('challenge_protocol.DetectionTracksChallenge', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))

