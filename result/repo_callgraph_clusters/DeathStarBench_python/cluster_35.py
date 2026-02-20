# Cluster 35

class Client(Iface):

    def __init__(self, iprot, oprot=None):
        self._iprot = self._oprot = iprot
        if oprot is not None:
            self._oprot = oprot
        self._seqid = 0

    def ComposeText(self, req_id, text, carrier):
        """
        Parameters:
         - req_id
         - text
         - carrier

        """
        self.send_ComposeText(req_id, text, carrier)
        return self.recv_ComposeText()

    def send_ComposeText(self, req_id, text, carrier):
        self._oprot.writeMessageBegin('ComposeText', TMessageType.CALL, self._seqid)
        args = ComposeText_args()
        args.req_id = req_id
        args.text = text
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_ComposeText(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = ComposeText_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.success is not None:
            return result.success
        if result.se is not None:
            raise result.se
        raise TApplicationException(TApplicationException.MISSING_RESULT, 'ComposeText failed: unknown result')

def ComposeText(self, req_id, text, carrier):
    """
        Parameters:
         - req_id
         - text
         - carrier

        """
    self.send_ComposeText(req_id, text, carrier)
    return self.recv_ComposeText()

# Node: send_ComposeText
# Node: recv_ComposeText
