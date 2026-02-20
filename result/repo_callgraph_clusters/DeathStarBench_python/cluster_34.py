# Cluster 34

class Client(Iface):

    def __init__(self, iprot, oprot=None):
        self._iprot = self._oprot = iprot
        if oprot is not None:
            self._oprot = oprot
        self._seqid = 0

    def ReadHomeTimeline(self, req_id, user_id, start, stop, carrier):
        """
        Parameters:
         - req_id
         - user_id
         - start
         - stop
         - carrier

        """
        self.send_ReadHomeTimeline(req_id, user_id, start, stop, carrier)
        return self.recv_ReadHomeTimeline()

    def send_ReadHomeTimeline(self, req_id, user_id, start, stop, carrier):
        self._oprot.writeMessageBegin('ReadHomeTimeline', TMessageType.CALL, self._seqid)
        args = ReadHomeTimeline_args()
        args.req_id = req_id
        args.user_id = user_id
        args.start = start
        args.stop = stop
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_ReadHomeTimeline(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = ReadHomeTimeline_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.success is not None:
            return result.success
        if result.se is not None:
            raise result.se
        raise TApplicationException(TApplicationException.MISSING_RESULT, 'ReadHomeTimeline failed: unknown result')

    def WriteHomeTimeline(self, req_id, post_id, user_id, timestamp, user_mentions_id, carrier):
        """
        Parameters:
         - req_id
         - post_id
         - user_id
         - timestamp
         - user_mentions_id
         - carrier

        """
        self.send_WriteHomeTimeline(req_id, post_id, user_id, timestamp, user_mentions_id, carrier)
        self.recv_WriteHomeTimeline()

    def send_WriteHomeTimeline(self, req_id, post_id, user_id, timestamp, user_mentions_id, carrier):
        self._oprot.writeMessageBegin('WriteHomeTimeline', TMessageType.CALL, self._seqid)
        args = WriteHomeTimeline_args()
        args.req_id = req_id
        args.post_id = post_id
        args.user_id = user_id
        args.timestamp = timestamp
        args.user_mentions_id = user_mentions_id
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_WriteHomeTimeline(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = WriteHomeTimeline_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.se is not None:
            raise result.se
        return

def WriteHomeTimeline(self, req_id, post_id, user_id, timestamp, user_mentions_id, carrier):
    """
        Parameters:
         - req_id
         - post_id
         - user_id
         - timestamp
         - user_mentions_id
         - carrier

        """
    self.send_WriteHomeTimeline(req_id, post_id, user_id, timestamp, user_mentions_id, carrier)
    self.recv_WriteHomeTimeline()

# Node: send_WriteHomeTimeline
# Node: recv_WriteHomeTimeline
