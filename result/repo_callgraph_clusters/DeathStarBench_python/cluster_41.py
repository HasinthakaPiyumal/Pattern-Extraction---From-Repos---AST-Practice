# Cluster 41

class Client(Iface):

    def __init__(self, iprot, oprot=None):
        self._iprot = self._oprot = iprot
        if oprot is not None:
            self._oprot = oprot
        self._seqid = 0

    def StorePost(self, req_id, post, carrier):
        """
        Parameters:
         - req_id
         - post
         - carrier

        """
        self.send_StorePost(req_id, post, carrier)
        self.recv_StorePost()

    def send_StorePost(self, req_id, post, carrier):
        self._oprot.writeMessageBegin('StorePost', TMessageType.CALL, self._seqid)
        args = StorePost_args()
        args.req_id = req_id
        args.post = post
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_StorePost(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = StorePost_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.se is not None:
            raise result.se
        return

    def ReadPost(self, req_id, post_id, carrier):
        """
        Parameters:
         - req_id
         - post_id
         - carrier

        """
        self.send_ReadPost(req_id, post_id, carrier)
        return self.recv_ReadPost()

    def send_ReadPost(self, req_id, post_id, carrier):
        self._oprot.writeMessageBegin('ReadPost', TMessageType.CALL, self._seqid)
        args = ReadPost_args()
        args.req_id = req_id
        args.post_id = post_id
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_ReadPost(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = ReadPost_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.success is not None:
            return result.success
        if result.se is not None:
            raise result.se
        raise TApplicationException(TApplicationException.MISSING_RESULT, 'ReadPost failed: unknown result')

    def ReadPosts(self, req_id, post_ids, carrier):
        """
        Parameters:
         - req_id
         - post_ids
         - carrier

        """
        self.send_ReadPosts(req_id, post_ids, carrier)
        return self.recv_ReadPosts()

    def send_ReadPosts(self, req_id, post_ids, carrier):
        self._oprot.writeMessageBegin('ReadPosts', TMessageType.CALL, self._seqid)
        args = ReadPosts_args()
        args.req_id = req_id
        args.post_ids = post_ids
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_ReadPosts(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = ReadPosts_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.success is not None:
            return result.success
        if result.se is not None:
            raise result.se
        raise TApplicationException(TApplicationException.MISSING_RESULT, 'ReadPosts failed: unknown result')

def ReadPosts(self, req_id, post_ids, carrier):
    """
        Parameters:
         - req_id
         - post_ids
         - carrier

        """
    self.send_ReadPosts(req_id, post_ids, carrier)
    return self.recv_ReadPosts()

# Node: send_ReadPosts
# Node: recv_ReadPosts
