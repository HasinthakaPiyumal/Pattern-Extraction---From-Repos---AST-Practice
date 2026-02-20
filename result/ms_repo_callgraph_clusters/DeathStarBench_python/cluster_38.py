# Cluster 38

class Client(Iface):

    def __init__(self, iprot, oprot=None):
        self._iprot = self._oprot = iprot
        if oprot is not None:
            self._oprot = oprot
        self._seqid = 0

    def ComposeMedia(self, req_id, media_types, media_ids, carrier):
        """
        Parameters:
         - req_id
         - media_types
         - media_ids
         - carrier

        """
        self.send_ComposeMedia(req_id, media_types, media_ids, carrier)
        return self.recv_ComposeMedia()

    def send_ComposeMedia(self, req_id, media_types, media_ids, carrier):
        self._oprot.writeMessageBegin('ComposeMedia', TMessageType.CALL, self._seqid)
        args = ComposeMedia_args()
        args.req_id = req_id
        args.media_types = media_types
        args.media_ids = media_ids
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_ComposeMedia(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = ComposeMedia_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.success is not None:
            return result.success
        if result.se is not None:
            raise result.se
        raise TApplicationException(TApplicationException.MISSING_RESULT, 'ComposeMedia failed: unknown result')

def ComposeMedia(self, req_id, media_types, media_ids, carrier):
    """
        Parameters:
         - req_id
         - media_types
         - media_ids
         - carrier

        """
    self.send_ComposeMedia(req_id, media_types, media_ids, carrier)
    return self.recv_ComposeMedia()

# Node: send_ComposeMedia
# Node: recv_ComposeMedia
