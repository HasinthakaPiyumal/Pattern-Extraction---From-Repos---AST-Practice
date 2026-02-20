# Cluster 20

class Client(Iface):

    def __init__(self, iprot, oprot=None):
        self._iprot = self._oprot = iprot
        if oprot is not None:
            self._oprot = oprot
        self._seqid = 0

    def UploadMovieId(self, req_id, title, rating, carrier):
        """
        Parameters:
         - req_id
         - title
         - rating
         - carrier

        """
        self.send_UploadMovieId(req_id, title, rating, carrier)
        self.recv_UploadMovieId()

    def send_UploadMovieId(self, req_id, title, rating, carrier):
        self._oprot.writeMessageBegin('UploadMovieId', TMessageType.CALL, self._seqid)
        args = UploadMovieId_args()
        args.req_id = req_id
        args.title = title
        args.rating = rating
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

    def RegisterMovieId(self, req_id, title, movie_id, carrier):
        """
        Parameters:
         - req_id
         - title
         - movie_id
         - carrier

        """
        self.send_RegisterMovieId(req_id, title, movie_id, carrier)
        self.recv_RegisterMovieId()

    def send_RegisterMovieId(self, req_id, title, movie_id, carrier):
        self._oprot.writeMessageBegin('RegisterMovieId', TMessageType.CALL, self._seqid)
        args = RegisterMovieId_args()
        args.req_id = req_id
        args.title = title
        args.movie_id = movie_id
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_RegisterMovieId(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = RegisterMovieId_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.se is not None:
            raise result.se
        return

def RegisterMovieId(self, req_id, title, movie_id, carrier):
    """
        Parameters:
         - req_id
         - title
         - movie_id
         - carrier

        """
    self.send_RegisterMovieId(req_id, title, movie_id, carrier)
    self.recv_RegisterMovieId()

# Node: send_RegisterMovieId
# Node: recv_RegisterMovieId
