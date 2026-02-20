# Cluster 21

class Client(Iface):

    def __init__(self, iprot, oprot=None):
        self._iprot = self._oprot = iprot
        if oprot is not None:
            self._oprot = oprot
        self._seqid = 0

    def StoreReview(self, req_id, review, carrier):
        """
        Parameters:
         - req_id
         - review
         - carrier

        """
        self.send_StoreReview(req_id, review, carrier)
        self.recv_StoreReview()

    def send_StoreReview(self, req_id, review, carrier):
        self._oprot.writeMessageBegin('StoreReview', TMessageType.CALL, self._seqid)
        args = StoreReview_args()
        args.req_id = req_id
        args.review = review
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_StoreReview(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = StoreReview_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.se is not None:
            raise result.se
        return

    def ReadReviews(self, req_id, review_ids, carrier):
        """
        Parameters:
         - req_id
         - review_ids
         - carrier

        """
        self.send_ReadReviews(req_id, review_ids, carrier)
        return self.recv_ReadReviews()

    def send_ReadReviews(self, req_id, review_ids, carrier):
        self._oprot.writeMessageBegin('ReadReviews', TMessageType.CALL, self._seqid)
        args = ReadReviews_args()
        args.req_id = req_id
        args.review_ids = review_ids
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_ReadReviews(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = ReadReviews_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.success is not None:
            return result.success
        if result.se is not None:
            raise result.se
        raise TApplicationException(TApplicationException.MISSING_RESULT, 'ReadReviews failed: unknown result')

def StoreReview(self, req_id, review, carrier):
    """
        Parameters:
         - req_id
         - review
         - carrier

        """
    self.send_StoreReview(req_id, review, carrier)
    self.recv_StoreReview()

# Node: send_StoreReview
# Node: recv_StoreReview
