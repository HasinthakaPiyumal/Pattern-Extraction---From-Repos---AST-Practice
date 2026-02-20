# Cluster 6

class Client(Iface):

    def __init__(self, iprot, oprot=None):
        self._iprot = self._oprot = iprot
        if oprot is not None:
            self._oprot = oprot
        self._seqid = 0

    def UploadMovieReview(self, req_id, movie_id, review_id, timestamp, carrier):
        """
        Parameters:
         - req_id
         - movie_id
         - review_id
         - timestamp
         - carrier

        """
        self.send_UploadMovieReview(req_id, movie_id, review_id, timestamp, carrier)
        self.recv_UploadMovieReview()

    def send_UploadMovieReview(self, req_id, movie_id, review_id, timestamp, carrier):
        self._oprot.writeMessageBegin('UploadMovieReview', TMessageType.CALL, self._seqid)
        args = UploadMovieReview_args()
        args.req_id = req_id
        args.movie_id = movie_id
        args.review_id = review_id
        args.timestamp = timestamp
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_UploadMovieReview(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = UploadMovieReview_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.se is not None:
            raise result.se
        return

    def ReadMovieReviews(self, req_id, movie_id, start, stop, carrier):
        """
        Parameters:
         - req_id
         - movie_id
         - start
         - stop
         - carrier

        """
        self.send_ReadMovieReviews(req_id, movie_id, start, stop, carrier)
        return self.recv_ReadMovieReviews()

    def send_ReadMovieReviews(self, req_id, movie_id, start, stop, carrier):
        self._oprot.writeMessageBegin('ReadMovieReviews', TMessageType.CALL, self._seqid)
        args = ReadMovieReviews_args()
        args.req_id = req_id
        args.movie_id = movie_id
        args.start = start
        args.stop = stop
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_ReadMovieReviews(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = ReadMovieReviews_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.success is not None:
            return result.success
        if result.se is not None:
            raise result.se
        raise TApplicationException(TApplicationException.MISSING_RESULT, 'ReadMovieReviews failed: unknown result')

def UploadMovieReview(self, req_id, movie_id, review_id, timestamp, carrier):
    """
        Parameters:
         - req_id
         - movie_id
         - review_id
         - timestamp
         - carrier

        """
    self.send_UploadMovieReview(req_id, movie_id, review_id, timestamp, carrier)
    self.recv_UploadMovieReview()

# Node: send_UploadMovieReview
# Node: recv_UploadMovieReview
