# Cluster 30

class Client(Iface):

    def __init__(self, iprot, oprot=None):
        self._iprot = self._oprot = iprot
        if oprot is not None:
            self._oprot = oprot
        self._seqid = 0

    def UploadText(self, req_id, text, carrier):
        """
        Parameters:
         - req_id
         - text
         - carrier

        """
        self.send_UploadText(req_id, text, carrier)
        self.recv_UploadText()

    def send_UploadText(self, req_id, text, carrier):
        self._oprot.writeMessageBegin('UploadText', TMessageType.CALL, self._seqid)
        args = UploadText_args()
        args.req_id = req_id
        args.text = text
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_UploadText(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = UploadText_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.se is not None:
            raise result.se
        return

    def UploadRating(self, req_id, rating, carrier):
        """
        Parameters:
         - req_id
         - rating
         - carrier

        """
        self.send_UploadRating(req_id, rating, carrier)
        self.recv_UploadRating()

    def send_UploadRating(self, req_id, rating, carrier):
        self._oprot.writeMessageBegin('UploadRating', TMessageType.CALL, self._seqid)
        args = UploadRating_args()
        args.req_id = req_id
        args.rating = rating
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_UploadRating(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = UploadRating_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.se is not None:
            raise result.se
        return

    def UploadMovieId(self, req_id, movie_id, carrier):
        """
        Parameters:
         - req_id
         - movie_id
         - carrier

        """
        self.send_UploadMovieId(req_id, movie_id, carrier)
        self.recv_UploadMovieId()

    def send_UploadMovieId(self, req_id, movie_id, carrier):
        self._oprot.writeMessageBegin('UploadMovieId', TMessageType.CALL, self._seqid)
        args = UploadMovieId_args()
        args.req_id = req_id
        args.movie_id = movie_id
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_UploadMovieId(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = UploadMovieId_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.se is not None:
            raise result.se
        return

    def UploadUniqueId(self, req_id, unique_id, carrier):
        """
        Parameters:
         - req_id
         - unique_id
         - carrier

        """
        self.send_UploadUniqueId(req_id, unique_id, carrier)
        self.recv_UploadUniqueId()

    def send_UploadUniqueId(self, req_id, unique_id, carrier):
        self._oprot.writeMessageBegin('UploadUniqueId', TMessageType.CALL, self._seqid)
        args = UploadUniqueId_args()
        args.req_id = req_id
        args.unique_id = unique_id
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_UploadUniqueId(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = UploadUniqueId_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.se is not None:
            raise result.se
        return

    def UploadUserId(self, req_id, user_id, carrier):
        """
        Parameters:
         - req_id
         - user_id
         - carrier

        """
        self.send_UploadUserId(req_id, user_id, carrier)
        self.recv_UploadUserId()

    def send_UploadUserId(self, req_id, user_id, carrier):
        self._oprot.writeMessageBegin('UploadUserId', TMessageType.CALL, self._seqid)
        args = UploadUserId_args()
        args.req_id = req_id
        args.user_id = user_id
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_UploadUserId(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = UploadUserId_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.se is not None:
            raise result.se
        return

def UploadUserId(self, req_id, user_id, carrier):
    """
        Parameters:
         - req_id
         - user_id
         - carrier

        """
    self.send_UploadUserId(req_id, user_id, carrier)
    self.recv_UploadUserId()

# Node: send_UploadUserId
# Node: recv_UploadUserId
