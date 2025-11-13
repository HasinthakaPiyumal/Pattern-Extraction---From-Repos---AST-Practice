# Cluster 9

class WebSocketServerConnector(ServerConnector):

    def __init__(self):
        self.process_message = None
        self.server_socket = None

    def create_socket(self, host: str, port: int):
        self.server_socket = websockets.serve(self.manage_messages, host, port)

    def loop(self, process_message: Callable[[bytes], str]):
        self.process_message = process_message
        asyncio.get_event_loop().run_until_complete(self.server_socket)
        asyncio.get_event_loop().run_forever()

    async def manage_messages(self, websocket, path):
        data = await websocket.recv()
        logger.info(f' read from the web socket < {data}')
        action = self.process_message(data)
        print(f'> {action}')
        action_to_send = str(action.json()).encode('utf8')
        await websocket.send(action_to_send)

def create_socket(self, host: str, port: int):
    self.server_socket = websockets.serve(self.manage_messages, host, port)

