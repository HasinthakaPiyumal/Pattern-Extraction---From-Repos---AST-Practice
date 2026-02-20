# Cluster 56

class Client(Iface):

    def __init__(self, iprot, oprot=None):
        self._iprot = self._oprot = iprot
        if oprot is not None:
            self._oprot = oprot
        self._seqid = 0

    def WriteUserTimeline(self, req_id, post_id, user_id, timestamp, carrier):
        """
        Parameters:
         - req_id
         - post_id
         - user_id
         - timestamp
         - carrier

        """
        self.send_WriteUserTimeline(req_id, post_id, user_id, timestamp, carrier)
        self.recv_WriteUserTimeline()

    def send_WriteUserTimeline(self, req_id, post_id, user_id, timestamp, carrier):
        self._oprot.writeMessageBegin('WriteUserTimeline', TMessageType.CALL, self._seqid)
        args = WriteUserTimeline_args()
        args.req_id = req_id
        args.post_id = post_id
        args.user_id = user_id
        args.timestamp = timestamp
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_WriteUserTimeline(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = WriteUserTimeline_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.se is not None:
            raise result.se
        return

    def ReadUserTimeline(self, req_id, user_id, start, stop, carrier):
        """
        Parameters:
         - req_id
         - user_id
         - start
         - stop
         - carrier

        """
        self.send_ReadUserTimeline(req_id, user_id, start, stop, carrier)
        return self.recv_ReadUserTimeline()

    def send_ReadUserTimeline(self, req_id, user_id, start, stop, carrier):
        self._oprot.writeMessageBegin('ReadUserTimeline', TMessageType.CALL, self._seqid)
        args = ReadUserTimeline_args()
        args.req_id = req_id
        args.user_id = user_id
        args.start = start
        args.stop = stop
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_ReadUserTimeline(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = ReadUserTimeline_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.success is not None:
            return result.success
        if result.se is not None:
            raise result.se
        raise TApplicationException(TApplicationException.MISSING_RESULT, 'ReadUserTimeline failed: unknown result')

def WriteUserTimeline(self, req_id, post_id, user_id, timestamp, carrier):
    """
        Parameters:
         - req_id
         - post_id
         - user_id
         - timestamp
         - carrier

        """
    self.send_WriteUserTimeline(req_id, post_id, user_id, timestamp, carrier)
    self.recv_WriteUserTimeline()

# Node: send_WriteUserTimeline
# Node: recv_WriteUserTimeline
