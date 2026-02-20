# Cluster 26

class Client(Iface):

    def __init__(self, iprot, oprot=None):
        self._iprot = self._oprot = iprot
        if oprot is not None:
            self._oprot = oprot
        self._seqid = 0

    def UploadUserReview(self, req_id, user_id, review_id, timestamp, carrier):
        """
        Parameters:
         - req_id
         - user_id
         - review_id
         - timestamp
         - carrier

        """
        self.send_UploadUserReview(req_id, user_id, review_id, timestamp, carrier)
        self.recv_UploadUserReview()

    def send_UploadUserReview(self, req_id, user_id, review_id, timestamp, carrier):
        self._oprot.writeMessageBegin('UploadUserReview', TMessageType.CALL, self._seqid)
        args = UploadUserReview_args()
        args.req_id = req_id
        args.user_id = user_id
        args.review_id = review_id
        args.timestamp = timestamp
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_UploadUserReview(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = UploadUserReview_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.se is not None:
            raise result.se
        return

    def ReadUserReviews(self, req_id, user_id, start, stop, carrier):
        """
        Parameters:
         - req_id
         - user_id
         - start
         - stop
         - carrier

        """
        self.send_ReadUserReviews(req_id, user_id, start, stop, carrier)
        return self.recv_ReadUserReviews()

    def send_ReadUserReviews(self, req_id, user_id, start, stop, carrier):
        self._oprot.writeMessageBegin('ReadUserReviews', TMessageType.CALL, self._seqid)
        args = ReadUserReviews_args()
        args.req_id = req_id
        args.user_id = user_id
        args.start = start
        args.stop = stop
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_ReadUserReviews(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = ReadUserReviews_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.success is not None:
            return result.success
        if result.se is not None:
            raise result.se
        raise TApplicationException(TApplicationException.MISSING_RESULT, 'ReadUserReviews failed: unknown result')

def UploadUserReview(self, req_id, user_id, review_id, timestamp, carrier):
    """
        Parameters:
         - req_id
         - user_id
         - review_id
         - timestamp
         - carrier

        """
    self.send_UploadUserReview(req_id, user_id, review_id, timestamp, carrier)
    self.recv_UploadUserReview()

# Node: send_UploadUserReview
# Node: recv_UploadUserReview
