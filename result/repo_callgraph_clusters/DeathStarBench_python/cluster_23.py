# Cluster 23

class Client(Iface):

    def __init__(self, iprot, oprot=None):
        self._iprot = self._oprot = iprot
        if oprot is not None:
            self._oprot = oprot
        self._seqid = 0

    def ReadPage(self, req_id, movie_id, review_start, review_stop, carrier):
        """
        Parameters:
         - req_id
         - movie_id
         - review_start
         - review_stop
         - carrier

        """
        self.send_ReadPage(req_id, movie_id, review_start, review_stop, carrier)
        return self.recv_ReadPage()

    def send_ReadPage(self, req_id, movie_id, review_start, review_stop, carrier):
        self._oprot.writeMessageBegin('ReadPage', TMessageType.CALL, self._seqid)
        args = ReadPage_args()
        args.req_id = req_id
        args.movie_id = movie_id
        args.review_start = review_start
        args.review_stop = review_stop
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_ReadPage(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = ReadPage_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.success is not None:
            return result.success
        if result.se is not None:
            raise result.se
        raise TApplicationException(TApplicationException.MISSING_RESULT, 'ReadPage failed: unknown result')

def ReadPage(self, req_id, movie_id, review_start, review_stop, carrier):
    """
        Parameters:
         - req_id
         - movie_id
         - review_start
         - review_stop
         - carrier

        """
    self.send_ReadPage(req_id, movie_id, review_start, review_stop, carrier)
    return self.recv_ReadPage()

# Node: send_ReadPage
# Node: recv_ReadPage
