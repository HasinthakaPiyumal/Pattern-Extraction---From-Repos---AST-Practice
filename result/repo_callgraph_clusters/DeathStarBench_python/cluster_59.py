# Cluster 59

class Client(Iface):

    def __init__(self, iprot, oprot=None):
        self._iprot = self._oprot = iprot
        if oprot is not None:
            self._oprot = oprot
        self._seqid = 0

    def ComposeUniqueId(self, req_id, post_type, carrier):
        """
        Parameters:
         - req_id
         - post_type
         - carrier

        """
        self.send_ComposeUniqueId(req_id, post_type, carrier)
        return self.recv_ComposeUniqueId()

    def send_ComposeUniqueId(self, req_id, post_type, carrier):
        self._oprot.writeMessageBegin('ComposeUniqueId', TMessageType.CALL, self._seqid)
        args = ComposeUniqueId_args()
        args.req_id = req_id
        args.post_type = post_type
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_ComposeUniqueId(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = ComposeUniqueId_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.success is not None:
            return result.success
        if result.se is not None:
            raise result.se
        raise TApplicationException(TApplicationException.MISSING_RESULT, 'ComposeUniqueId failed: unknown result')

def ComposeUniqueId(self, req_id, post_type, carrier):
    """
        Parameters:
         - req_id
         - post_type
         - carrier

        """
    self.send_ComposeUniqueId(req_id, post_type, carrier)
    return self.recv_ComposeUniqueId()

# Node: send_ComposeUniqueId
# Node: recv_ComposeUniqueId
