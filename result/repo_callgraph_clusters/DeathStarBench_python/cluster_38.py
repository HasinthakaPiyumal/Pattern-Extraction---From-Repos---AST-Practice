# Cluster 38

class Client(Iface):

    def __init__(self, iprot, oprot=None):
        self._iprot = self._oprot = iprot
        if oprot is not None:
            self._oprot = oprot
        self._seqid = 0

    def ComposeUrls(self, req_id, urls, carrier):
        """
        Parameters:
         - req_id
         - urls
         - carrier

        """
        self.send_ComposeUrls(req_id, urls, carrier)
        return self.recv_ComposeUrls()

    def send_ComposeUrls(self, req_id, urls, carrier):
        self._oprot.writeMessageBegin('ComposeUrls', TMessageType.CALL, self._seqid)
        args = ComposeUrls_args()
        args.req_id = req_id
        args.urls = urls
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_ComposeUrls(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = ComposeUrls_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.success is not None:
            return result.success
        if result.se is not None:
            raise result.se
        raise TApplicationException(TApplicationException.MISSING_RESULT, 'ComposeUrls failed: unknown result')

    def GetExtendedUrls(self, req_id, shortened_urls, carrier):
        """
        Parameters:
         - req_id
         - shortened_urls
         - carrier

        """
        self.send_GetExtendedUrls(req_id, shortened_urls, carrier)
        return self.recv_GetExtendedUrls()

    def send_GetExtendedUrls(self, req_id, shortened_urls, carrier):
        self._oprot.writeMessageBegin('GetExtendedUrls', TMessageType.CALL, self._seqid)
        args = GetExtendedUrls_args()
        args.req_id = req_id
        args.shortened_urls = shortened_urls
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_GetExtendedUrls(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = GetExtendedUrls_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.success is not None:
            return result.success
        if result.se is not None:
            raise result.se
        raise TApplicationException(TApplicationException.MISSING_RESULT, 'GetExtendedUrls failed: unknown result')

def GetExtendedUrls(self, req_id, shortened_urls, carrier):
    """
        Parameters:
         - req_id
         - shortened_urls
         - carrier

        """
    self.send_GetExtendedUrls(req_id, shortened_urls, carrier)
    return self.recv_GetExtendedUrls()

# Node: send_GetExtendedUrls
# Node: recv_GetExtendedUrls
