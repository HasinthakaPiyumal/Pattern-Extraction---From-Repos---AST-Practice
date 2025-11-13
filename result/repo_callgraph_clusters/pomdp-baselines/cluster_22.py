# Cluster 22

class TensorBoardOutputFormat(KVWriter):
    """
    Dumps key/value pairs into TensorBoard's numeric format.
    """

    def __init__(self, dir):
        os.makedirs(dir, exist_ok=True)
        self.step = 0
        self.writer = SummaryWriter(dir)

    def writekvs(self, kvs):
        for k, v in kvs.items():
            self.writer.add_scalar(k, v, self.step)
        self.writer.flush()

    def add_figure(self, tag, figure):
        self.writer.add_figure(tag, figure, self.step)

    def set_step(self, step):
        self.step = step

    def close(self):
        if self.writer:
            self.writer.Close()
            self.writer = None

def close(self):
    if self.writer:
        self.writer.Close()
        self.writer = None

