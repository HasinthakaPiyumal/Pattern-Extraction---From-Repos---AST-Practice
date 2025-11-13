# Cluster 5

class Channel:

    def __init__(self):
        self.receive_queue = asyncio.Queue()
        self.send_dict = AsyncSafeDict()

    async def receive_from(self):
        message = await self.receive_queue.get()
        return message

    async def send_to(self, message):
        message_id = message[0]
        await self.send_dict.put(message_id, message)

    async def write_to_receive_queue(self, action_info):
        message_id = str(uuid.uuid4())
        await self.receive_queue.put((message_id, action_info))
        return message_id

    async def read_from_send_queue(self, message_id):
        while True:
            if message_id in await self.send_dict.keys():
                message = await self.send_dict.pop(message_id, None)
                if message:
                    return message
            await asyncio.sleep(0.1)

def __init__(self):
    self.receive_queue = asyncio.Queue()
    self.send_dict = AsyncSafeDict()

