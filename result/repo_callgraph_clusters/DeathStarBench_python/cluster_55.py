# Cluster 55

class Client(Iface):

    def __init__(self, iprot, oprot=None):
        self._iprot = self._oprot = iprot
        if oprot is not None:
            self._oprot = oprot
        self._seqid = 0

    def ComposePost(self, req_id, username, user_id, text, media_ids, media_types, post_type, carrier):
        """
        Parameters:
         - req_id
         - username
         - user_id
         - text
         - media_ids
         - media_types
         - post_type
         - carrier

        """
        self.send_ComposePost(req_id, username, user_id, text, media_ids, media_types, post_type, carrier)
        self.recv_ComposePost()

    def send_ComposePost(self, req_id, username, user_id, text, media_ids, media_types, post_type, carrier):
        self._oprot.writeMessageBegin('ComposePost', TMessageType.CALL, self._seqid)
        args = ComposePost_args()
        args.req_id = req_id
        args.username = username
        args.user_id = user_id
        args.text = text
        args.media_ids = media_ids
        args.media_types = media_types
        args.post_type = post_type
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_ComposePost(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = ComposePost_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.se is not None:
            raise result.se
        return

def ComposePost(self, req_id, username, user_id, text, media_ids, media_types, post_type, carrier):
    """
        Parameters:
         - req_id
         - username
         - user_id
         - text
         - media_ids
         - media_types
         - post_type
         - carrier

        """
    self.send_ComposePost(req_id, username, user_id, text, media_ids, media_types, post_type, carrier)
    self.recv_ComposePost()

# Node: send_ComposePost
# Node: recv_ComposePost
