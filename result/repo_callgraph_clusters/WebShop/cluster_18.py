# Cluster 18

class TensorBoardOutputFormat(KVWriter):
    """
    Dumps key/value pairs into TensorBoard's numeric format.
    """

    def __init__(self, dir):
        os.makedirs(dir, exist_ok=True)
        self.dir = dir
        self.step = 1
        prefix = 'events'
        path = osp.join(osp.abspath(dir), prefix)
        import tensorflow as tf
        from tensorflow.python import pywrap_tensorflow
        from tensorflow.core.util import event_pb2
        from tensorflow.python.util import compat
        self.tf = tf
        self.event_pb2 = event_pb2
        self.pywrap_tensorflow = pywrap_tensorflow
        self.writer = pywrap_tensorflow.EventsWriter(compat.as_bytes(path))

    def writekvs(self, kvs):

        def summary_val(k, v):
            kwargs = {'tag': k, 'simple_value': float(v)}
            return self.tf.Summary.Value(**kwargs)
        summary = self.tf.Summary(value=[summary_val(k, v) for k, v in kvs.items()])
        event = self.event_pb2.Event(wall_time=time.time(), summary=summary)
        event.step = self.step
        self.writer.WriteEvent(event)
        self.writer.Flush()
        self.step += 1

    def close(self):
        if self.writer:
            self.writer.Close()
            self.writer = None

def writekvs(self, kvs):

    def summary_val(k, v):
        kwargs = {'tag': k, 'simple_value': float(v)}
        return self.tf.Summary.Value(**kwargs)
    summary = self.tf.Summary(value=[summary_val(k, v) for k, v in kvs.items()])
    event = self.event_pb2.Event(wall_time=time.time(), summary=summary)
    event.step = self.step
    self.writer.WriteEvent(event)
    self.writer.Flush()
    self.step += 1

class ProfileKV:
    """
    Usage:
    with logger.ProfileKV("interesting_scope"):
        code
    """

    def __init__(self, n):
        self.n = 'wait_' + n

    def __enter__(self):
        self.t1 = time.time()

    def __exit__(self, type, value, traceback):
        Logger.CURRENT.name2val[self.n] += time.time() - self.t1

def __enter__(self):
    self.t1 = time.time()

def __exit__(self, type, value, traceback):
    Logger.CURRENT.name2val[self.n] += time.time() - self.t1

