# Cluster 37

def obtain_command_id():
    commaind_id = uuid.uuid4()
    return str(commaind_id)

class SocketClientConnector(ClientConnector):

    def __init__(self, host: str, port: int):
        self.sel = selectors.DefaultSelector()
        self.host = host
        self.port = port
        self.uuid = uuid.uuid4()

    def send(self, message: StateDTO) -> Action:
        try:
            return self._internal_send(message)
        except Exception as error:
            logger.info(f'error {error}')
            logger.info(traceback.format_exc())
            return Action(origin_command=message.command, suggested_command=message.command)
        finally:
            self.close()

    def _internal_send(self, command_to_send):
        self.start_connections(self.host, int(self.port))
        self.write(command_to_send)
        action = self.read()
        if action:
            return action
        return Action(origin_command=command_to_send.command, suggested_command=command_to_send.command)

    def start_connections(self, host, port):
        server_address = (host, port)
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.setblocking(False)
        client_socket.connect_ex(server_address)
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        data = types.SimpleNamespace(connid=self.uuid, outb=b'')
        self.sel.register(client_socket, events, data=data)

    def write(self, message: StateDTO):
        events = self.sel.select(timeout=5)
        key = events[0][0]
        client_socket = key.fileobj
        data = key.data
        self.sel.modify(client_socket, selectors.EVENT_WRITE, data)
        logger.info(f'echoing ${data}')
        data.outb = str(message.json())
        sent = client_socket.send(data.outb.encode('utf-8'))
        data.outb = data.outb[sent:]
        self.sel.modify(client_socket, selectors.EVENT_READ, data)

    def read(self) -> Optional[Action]:
        events = self.sel.select(timeout=6)
        if events and events[0]:
            key = events[0][0]
            client_socket = key.fileobj
            received_data = client_socket.recv(4024)
            if received_data:
                message = process_message(received_data)
                return message
        return None

    def close(self):
        self.sel.close()

def __init__(self, host: str, port: int):
    self.sel = selectors.DefaultSelector()
    self.host = host
    self.port = port
    self.uuid = uuid.uuid4()

def start_connections(self, host, port):
    server_address = (host, port)
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.setblocking(False)
    client_socket.connect_ex(server_address)
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    data = types.SimpleNamespace(connid=self.uuid, outb=b'')
    self.sel.register(client_socket, events, data=data)

class SocketServerConnector(ServerConnector):
    BUFFER_SIZE = 4024

    def __init__(self, server_status_datasource: ServerStatusDatasource):
        self.server_status_datasource = server_status_datasource
        self.sel = selectors.DefaultSelector()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def create_socket(self, host: str, port: int):
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((host, port))
        self.server_socket.listen()
        logger.info(f'Listening {host} {port}')
        self.server_socket.setblocking(False)

    def loop(self, process_message: Callable[[bytes], Action]):
        self.sel.register(self.server_socket, selectors.EVENT_READ, data=None)
        try:
            while self.server_status_datasource.running:
                events = self.sel.select(timeout=None)
                for key, mask in events:
                    if key.data is None:
                        self.__accept_wrapper(key.fileobj)
                    else:
                        self.__service_connection(key, mask, process_message)
            self.sel.unregister(self.server_socket)
            self.server_socket.close()
        except KeyboardInterrupt:
            logger.info('caught keyboard interrupt, exiting')
        finally:
            logger.info('server closed')
            self.sel.close()

    def __accept_wrapper(self, server_socket):
        connection, address = server_socket.accept()
        connection.setblocking(False)
        data = types.SimpleNamespace(addr=address, inb=b'', outb=b'')
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.sel.register(connection, events, data=data)

    def __service_connection(self, key, mask, process_message):
        fileobj = key.fileobj
        data = key.data
        if mask & selectors.EVENT_READ:
            data = self.__read(data, fileobj, process_message)
        if mask & selectors.EVENT_WRITE:
            self.__write(data, fileobj)

    @staticmethod
    def __write(data, server_socket):
        if data.outb:
            logger.info(f'sending from client ${data.outb}')
            server_socket.send(data.outb)
            data.outb = b''

    def __read(self, data, server_socket, process_message):
        recv_data = b''
        chewing = True
        logger.info(f'receiving from client')
        while chewing:
            part = server_socket.recv(self.BUFFER_SIZE)
            recv_data += part
            if len(part) < self.BUFFER_SIZE:
                chewing = False
        if recv_data:
            logger.info(f'receiving from client ${recv_data}')
            action = process_message(recv_data)
            data.outb = str(action.json()).encode('utf8')
        else:
            self.sel.unregister(server_socket)
            server_socket.close()
        return data

def __init__(self, server_status_datasource: ServerStatusDatasource):
    self.server_status_datasource = server_status_datasource
    self.sel = selectors.DefaultSelector()
    self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def create_socket(self, host: str, port: int):
    self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.server_socket.bind((host, port))
    self.server_socket.listen()
    logger.info(f'Listening {host} {port}')
    self.server_socket.setblocking(False)

def __accept_wrapper(self, server_socket):
    connection, address = server_socket.accept()
    connection.setblocking(False)
    data = types.SimpleNamespace(addr=address, inb=b'', outb=b'')
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    self.sel.register(connection, events, data=data)

class Example:
    """Stores an input, output pair and formats it to prime the model."""

    def __init__(self, inp, out):
        self.input = inp
        self.output = out
        self._id = uuid.uuid4().hex

    def get_input(self):
        """Returns the input of the example."""
        return self.input

    def get_output(self):
        """Returns the intended output of the example."""
        return self.output

    def get_id(self):
        """Returns the unique ID of the example."""
        return self._id

    def as_dict(self):
        return {'input': self.get_input(), 'output': self.get_output(), 'id': self.get_id()}

def __init__(self, inp, out):
    self.input = inp
    self.output = out
    self._id = uuid.uuid4().hex

