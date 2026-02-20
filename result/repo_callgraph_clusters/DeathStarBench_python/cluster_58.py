# Cluster 58

class Client(Iface):

    def __init__(self, iprot, oprot=None):
        self._iprot = self._oprot = iprot
        if oprot is not None:
            self._oprot = oprot
        self._seqid = 0

    def ComposeUserMentions(self, req_id, usernames, carrier):
        """
        Parameters:
         - req_id
         - usernames
         - carrier

        """
        self.send_ComposeUserMentions(req_id, usernames, carrier)
        return self.recv_ComposeUserMentions()

    def send_ComposeUserMentions(self, req_id, usernames, carrier):
        self._oprot.writeMessageBegin('ComposeUserMentions', TMessageType.CALL, self._seqid)
        args = ComposeUserMentions_args()
        args.req_id = req_id
        args.usernames = usernames
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_ComposeUserMentions(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = ComposeUserMentions_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.success is not None:
            return result.success
        if result.se is not None:
            raise result.se
        raise TApplicationException(TApplicationException.MISSING_RESULT, 'ComposeUserMentions failed: unknown result')

def ComposeUserMentions(self, req_id, usernames, carrier):
    """
        Parameters:
         - req_id
         - usernames
         - carrier

        """
    self.send_ComposeUserMentions(req_id, usernames, carrier)
    return self.recv_ComposeUserMentions()

# Node: send_ComposeUserMentions
# Node: recv_ComposeUserMentions
