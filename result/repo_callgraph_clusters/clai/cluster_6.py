# Cluster 6

class ClaiClient:

    def __init__(self, host: str=LOCALHOST, port: int=DEFAULT_PORT, connector: ClientConnector=None):
        self.connector = connector
        if not connector:
            self.connector = SocketClientConnector(host=host, port=port)
        self.port = port
        self.host = host

    def send(self, message: StateDTO) -> Action:
        try:
            return self.connector.send(message)
        except Exception as exception:
            logger.info(f'error: {exception}')
            return Action(origin_command=message.command, suggested_command=message.command)

def __init__(self, host: str=LOCALHOST, port: int=DEFAULT_PORT, connector: ClientConnector=None):
    self.connector = connector
    if not connector:
        self.connector = SocketClientConnector(host=host, port=port)
    self.port = port
    self.host = host

