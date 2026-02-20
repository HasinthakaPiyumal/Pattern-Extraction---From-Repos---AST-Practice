# Cluster 10

class Client(Iface):

    def __init__(self, iprot, oprot=None):
        self._iprot = self._oprot = iprot
        if oprot is not None:
            self._oprot = oprot
        self._seqid = 0

    def WriteMovieInfo(self, req_id, movie_id, title, casts, plot_id, thumbnail_ids, photo_ids, video_ids, avg_rating, num_rating, carrier):
        """
        Parameters:
         - req_id
         - movie_id
         - title
         - casts
         - plot_id
         - thumbnail_ids
         - photo_ids
         - video_ids
         - avg_rating
         - num_rating
         - carrier

        """
        self.send_WriteMovieInfo(req_id, movie_id, title, casts, plot_id, thumbnail_ids, photo_ids, video_ids, avg_rating, num_rating, carrier)
        self.recv_WriteMovieInfo()

    def send_WriteMovieInfo(self, req_id, movie_id, title, casts, plot_id, thumbnail_ids, photo_ids, video_ids, avg_rating, num_rating, carrier):
        self._oprot.writeMessageBegin('WriteMovieInfo', TMessageType.CALL, self._seqid)
        args = WriteMovieInfo_args()
        args.req_id = req_id
        args.movie_id = movie_id
        args.title = title
        args.casts = casts
        args.plot_id = plot_id
        args.thumbnail_ids = thumbnail_ids
        args.photo_ids = photo_ids
        args.video_ids = video_ids
        args.avg_rating = avg_rating
        args.num_rating = num_rating
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_WriteMovieInfo(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = WriteMovieInfo_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.se is not None:
            raise result.se
        return

    def ReadMovieInfo(self, req_id, movie_id, carrier):
        """
        Parameters:
         - req_id
         - movie_id
         - carrier

        """
        self.send_ReadMovieInfo(req_id, movie_id, carrier)
        return self.recv_ReadMovieInfo()

    def send_ReadMovieInfo(self, req_id, movie_id, carrier):
        self._oprot.writeMessageBegin('ReadMovieInfo', TMessageType.CALL, self._seqid)
        args = ReadMovieInfo_args()
        args.req_id = req_id
        args.movie_id = movie_id
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_ReadMovieInfo(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = ReadMovieInfo_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.success is not None:
            return result.success
        if result.se is not None:
            raise result.se
        raise TApplicationException(TApplicationException.MISSING_RESULT, 'ReadMovieInfo failed: unknown result')

    def UpdateRating(self, req_id, movie_id, sum_uncommitted_rating, num_uncommitted_rating, carrier):
        """
        Parameters:
         - req_id
         - movie_id
         - sum_uncommitted_rating
         - num_uncommitted_rating
         - carrier

        """
        self.send_UpdateRating(req_id, movie_id, sum_uncommitted_rating, num_uncommitted_rating, carrier)
        self.recv_UpdateRating()

    def send_UpdateRating(self, req_id, movie_id, sum_uncommitted_rating, num_uncommitted_rating, carrier):
        self._oprot.writeMessageBegin('UpdateRating', TMessageType.CALL, self._seqid)
        args = UpdateRating_args()
        args.req_id = req_id
        args.movie_id = movie_id
        args.sum_uncommitted_rating = sum_uncommitted_rating
        args.num_uncommitted_rating = num_uncommitted_rating
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_UpdateRating(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = UpdateRating_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.se is not None:
            raise result.se
        return

def WriteMovieInfo(self, req_id, movie_id, title, casts, plot_id, thumbnail_ids, photo_ids, video_ids, avg_rating, num_rating, carrier):
    """
        Parameters:
         - req_id
         - movie_id
         - title
         - casts
         - plot_id
         - thumbnail_ids
         - photo_ids
         - video_ids
         - avg_rating
         - num_rating
         - carrier

        """
    self.send_WriteMovieInfo(req_id, movie_id, title, casts, plot_id, thumbnail_ids, photo_ids, video_ids, avg_rating, num_rating, carrier)
    self.recv_WriteMovieInfo()

# Node: send_WriteMovieInfo
# Node: recv_WriteMovieInfo
