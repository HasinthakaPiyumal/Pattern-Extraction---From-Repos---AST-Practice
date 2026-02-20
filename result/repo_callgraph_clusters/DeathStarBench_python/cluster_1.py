# Cluster 1

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

def send_UploadText(self, req_id, text, carrier):
    self._oprot.writeMessageBegin('UploadText', TMessageType.CALL, self._seqid)
    args = UploadText_args()
    args.req_id = req_id
    args.text = text
    args.carrier = carrier
    args.write(self._oprot)
    self._oprot.writeMessageEnd()
    self._oprot.trans.flush()

# Node: writeMessageBegin
# Node: UploadText_args
# Node: write
# Node: writeMessageEnd
# Node: flush
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

# Node: readMessageBegin
# Node: TApplicationException
# Node: read
# Node: readMessageEnd
# Node: UploadText_result
class Processor(Iface, TProcessor):

    def __init__(self, handler):
        self._handler = handler
        self._processMap = {}
        self._processMap['UploadText'] = Processor.process_UploadText

    def process(self, iprot, oprot):
        name, type, seqid = iprot.readMessageBegin()
        if name not in self._processMap:
            iprot.skip(TType.STRUCT)
            iprot.readMessageEnd()
            x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
            oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
            x.write(oprot)
            oprot.writeMessageEnd()
            oprot.trans.flush()
            return
        else:
            self._processMap[name](self, seqid, iprot, oprot)
        return True

    def process_UploadText(self, seqid, iprot, oprot):
        args = UploadText_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = UploadText_result()
        try:
            self._handler.UploadText(args.req_id, args.text, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('UploadText', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

def process(self, iprot, oprot):
    name, type, seqid = iprot.readMessageBegin()
    if name not in self._processMap:
        iprot.skip(TType.STRUCT)
        iprot.readMessageEnd()
        x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
        oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
        x.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()
        return
    else:
        self._processMap[name](self, seqid, iprot, oprot)
    return True

def process_UploadText(self, seqid, iprot, oprot):
    args = UploadText_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = UploadText_result()
    try:
        self._handler.UploadText(args.req_id, args.text, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('UploadText', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

# Node: exception
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

# Node: UploadMovieReview_args
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

# Node: UploadMovieReview_result
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

# Node: ReadMovieReviews_args
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

# Node: ReadMovieReviews_result
class Processor(Iface, TProcessor):

    def __init__(self, handler):
        self._handler = handler
        self._processMap = {}
        self._processMap['UploadMovieReview'] = Processor.process_UploadMovieReview
        self._processMap['ReadMovieReviews'] = Processor.process_ReadMovieReviews

    def process(self, iprot, oprot):
        name, type, seqid = iprot.readMessageBegin()
        if name not in self._processMap:
            iprot.skip(TType.STRUCT)
            iprot.readMessageEnd()
            x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
            oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
            x.write(oprot)
            oprot.writeMessageEnd()
            oprot.trans.flush()
            return
        else:
            self._processMap[name](self, seqid, iprot, oprot)
        return True

    def process_UploadMovieReview(self, seqid, iprot, oprot):
        args = UploadMovieReview_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = UploadMovieReview_result()
        try:
            self._handler.UploadMovieReview(args.req_id, args.movie_id, args.review_id, args.timestamp, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('UploadMovieReview', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

    def process_ReadMovieReviews(self, seqid, iprot, oprot):
        args = ReadMovieReviews_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = ReadMovieReviews_result()
        try:
            result.success = self._handler.ReadMovieReviews(args.req_id, args.movie_id, args.start, args.stop, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('ReadMovieReviews', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

def process(self, iprot, oprot):
    name, type, seqid = iprot.readMessageBegin()
    if name not in self._processMap:
        iprot.skip(TType.STRUCT)
        iprot.readMessageEnd()
        x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
        oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
        x.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()
        return
    else:
        self._processMap[name](self, seqid, iprot, oprot)
    return True

def process_UploadMovieReview(self, seqid, iprot, oprot):
    args = UploadMovieReview_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = UploadMovieReview_result()
    try:
        self._handler.UploadMovieReview(args.req_id, args.movie_id, args.review_id, args.timestamp, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('UploadMovieReview', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

def process_ReadMovieReviews(self, seqid, iprot, oprot):
    args = ReadMovieReviews_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = ReadMovieReviews_result()
    try:
        result.success = self._handler.ReadMovieReviews(args.req_id, args.movie_id, args.start, args.stop, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('ReadMovieReviews', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

class Client(Iface):

    def __init__(self, iprot, oprot=None):
        self._iprot = self._oprot = iprot
        if oprot is not None:
            self._oprot = oprot
        self._seqid = 0

    def WritePlot(self, req_id, plot_id, plot, carrier):
        """
        Parameters:
         - req_id
         - plot_id
         - plot
         - carrier

        """
        self.send_WritePlot(req_id, plot_id, plot, carrier)
        self.recv_WritePlot()

    def send_WritePlot(self, req_id, plot_id, plot, carrier):
        self._oprot.writeMessageBegin('WritePlot', TMessageType.CALL, self._seqid)
        args = WritePlot_args()
        args.req_id = req_id
        args.plot_id = plot_id
        args.plot = plot
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_WritePlot(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = WritePlot_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.se is not None:
            raise result.se
        return

    def ReadPlot(self, req_id, plot_id, carrier):
        """
        Parameters:
         - req_id
         - plot_id
         - carrier

        """
        self.send_ReadPlot(req_id, plot_id, carrier)
        return self.recv_ReadPlot()

    def send_ReadPlot(self, req_id, plot_id, carrier):
        self._oprot.writeMessageBegin('ReadPlot', TMessageType.CALL, self._seqid)
        args = ReadPlot_args()
        args.req_id = req_id
        args.plot_id = plot_id
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_ReadPlot(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = ReadPlot_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.success is not None:
            return result.success
        if result.se is not None:
            raise result.se
        raise TApplicationException(TApplicationException.MISSING_RESULT, 'ReadPlot failed: unknown result')

def send_WritePlot(self, req_id, plot_id, plot, carrier):
    self._oprot.writeMessageBegin('WritePlot', TMessageType.CALL, self._seqid)
    args = WritePlot_args()
    args.req_id = req_id
    args.plot_id = plot_id
    args.plot = plot
    args.carrier = carrier
    args.write(self._oprot)
    self._oprot.writeMessageEnd()
    self._oprot.trans.flush()

# Node: WritePlot_args
def recv_WritePlot(self):
    iprot = self._iprot
    fname, mtype, rseqid = iprot.readMessageBegin()
    if mtype == TMessageType.EXCEPTION:
        x = TApplicationException()
        x.read(iprot)
        iprot.readMessageEnd()
        raise x
    result = WritePlot_result()
    result.read(iprot)
    iprot.readMessageEnd()
    if result.se is not None:
        raise result.se
    return

# Node: WritePlot_result
def send_ReadPlot(self, req_id, plot_id, carrier):
    self._oprot.writeMessageBegin('ReadPlot', TMessageType.CALL, self._seqid)
    args = ReadPlot_args()
    args.req_id = req_id
    args.plot_id = plot_id
    args.carrier = carrier
    args.write(self._oprot)
    self._oprot.writeMessageEnd()
    self._oprot.trans.flush()

# Node: ReadPlot_args
def recv_ReadPlot(self):
    iprot = self._iprot
    fname, mtype, rseqid = iprot.readMessageBegin()
    if mtype == TMessageType.EXCEPTION:
        x = TApplicationException()
        x.read(iprot)
        iprot.readMessageEnd()
        raise x
    result = ReadPlot_result()
    result.read(iprot)
    iprot.readMessageEnd()
    if result.success is not None:
        return result.success
    if result.se is not None:
        raise result.se
    raise TApplicationException(TApplicationException.MISSING_RESULT, 'ReadPlot failed: unknown result')

# Node: ReadPlot_result
class Processor(Iface, TProcessor):

    def __init__(self, handler):
        self._handler = handler
        self._processMap = {}
        self._processMap['WritePlot'] = Processor.process_WritePlot
        self._processMap['ReadPlot'] = Processor.process_ReadPlot

    def process(self, iprot, oprot):
        name, type, seqid = iprot.readMessageBegin()
        if name not in self._processMap:
            iprot.skip(TType.STRUCT)
            iprot.readMessageEnd()
            x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
            oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
            x.write(oprot)
            oprot.writeMessageEnd()
            oprot.trans.flush()
            return
        else:
            self._processMap[name](self, seqid, iprot, oprot)
        return True

    def process_WritePlot(self, seqid, iprot, oprot):
        args = WritePlot_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = WritePlot_result()
        try:
            self._handler.WritePlot(args.req_id, args.plot_id, args.plot, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('WritePlot', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

    def process_ReadPlot(self, seqid, iprot, oprot):
        args = ReadPlot_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = ReadPlot_result()
        try:
            result.success = self._handler.ReadPlot(args.req_id, args.plot_id, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('ReadPlot', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

def process(self, iprot, oprot):
    name, type, seqid = iprot.readMessageBegin()
    if name not in self._processMap:
        iprot.skip(TType.STRUCT)
        iprot.readMessageEnd()
        x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
        oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
        x.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()
        return
    else:
        self._processMap[name](self, seqid, iprot, oprot)
    return True

def process_WritePlot(self, seqid, iprot, oprot):
    args = WritePlot_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = WritePlot_result()
    try:
        self._handler.WritePlot(args.req_id, args.plot_id, args.plot, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('WritePlot', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

def process_ReadPlot(self, seqid, iprot, oprot):
    args = ReadPlot_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = ReadPlot_result()
    try:
        result.success = self._handler.ReadPlot(args.req_id, args.plot_id, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('ReadPlot', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

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

# Node: WriteMovieInfo_args
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

# Node: WriteMovieInfo_result
def send_ReadMovieInfo(self, req_id, movie_id, carrier):
    self._oprot.writeMessageBegin('ReadMovieInfo', TMessageType.CALL, self._seqid)
    args = ReadMovieInfo_args()
    args.req_id = req_id
    args.movie_id = movie_id
    args.carrier = carrier
    args.write(self._oprot)
    self._oprot.writeMessageEnd()
    self._oprot.trans.flush()

# Node: ReadMovieInfo_args
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

# Node: ReadMovieInfo_result
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

# Node: UpdateRating_args
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

# Node: UpdateRating_result
class Processor(Iface, TProcessor):

    def __init__(self, handler):
        self._handler = handler
        self._processMap = {}
        self._processMap['WriteMovieInfo'] = Processor.process_WriteMovieInfo
        self._processMap['ReadMovieInfo'] = Processor.process_ReadMovieInfo
        self._processMap['UpdateRating'] = Processor.process_UpdateRating

    def process(self, iprot, oprot):
        name, type, seqid = iprot.readMessageBegin()
        if name not in self._processMap:
            iprot.skip(TType.STRUCT)
            iprot.readMessageEnd()
            x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
            oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
            x.write(oprot)
            oprot.writeMessageEnd()
            oprot.trans.flush()
            return
        else:
            self._processMap[name](self, seqid, iprot, oprot)
        return True

    def process_WriteMovieInfo(self, seqid, iprot, oprot):
        args = WriteMovieInfo_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = WriteMovieInfo_result()
        try:
            self._handler.WriteMovieInfo(args.req_id, args.movie_id, args.title, args.casts, args.plot_id, args.thumbnail_ids, args.photo_ids, args.video_ids, args.avg_rating, args.num_rating, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('WriteMovieInfo', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

    def process_ReadMovieInfo(self, seqid, iprot, oprot):
        args = ReadMovieInfo_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = ReadMovieInfo_result()
        try:
            result.success = self._handler.ReadMovieInfo(args.req_id, args.movie_id, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('ReadMovieInfo', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

    def process_UpdateRating(self, seqid, iprot, oprot):
        args = UpdateRating_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = UpdateRating_result()
        try:
            self._handler.UpdateRating(args.req_id, args.movie_id, args.sum_uncommitted_rating, args.num_uncommitted_rating, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('UpdateRating', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

def process(self, iprot, oprot):
    name, type, seqid = iprot.readMessageBegin()
    if name not in self._processMap:
        iprot.skip(TType.STRUCT)
        iprot.readMessageEnd()
        x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
        oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
        x.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()
        return
    else:
        self._processMap[name](self, seqid, iprot, oprot)
    return True

def process_WriteMovieInfo(self, seqid, iprot, oprot):
    args = WriteMovieInfo_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = WriteMovieInfo_result()
    try:
        self._handler.WriteMovieInfo(args.req_id, args.movie_id, args.title, args.casts, args.plot_id, args.thumbnail_ids, args.photo_ids, args.video_ids, args.avg_rating, args.num_rating, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('WriteMovieInfo', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

def process_ReadMovieInfo(self, seqid, iprot, oprot):
    args = ReadMovieInfo_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = ReadMovieInfo_result()
    try:
        result.success = self._handler.ReadMovieInfo(args.req_id, args.movie_id, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('ReadMovieInfo', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

def process_UpdateRating(self, seqid, iprot, oprot):
    args = UpdateRating_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = UpdateRating_result()
    try:
        self._handler.UpdateRating(args.req_id, args.movie_id, args.sum_uncommitted_rating, args.num_uncommitted_rating, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('UpdateRating', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

# Node: UpdateRating
class Client(Iface):

    def __init__(self, iprot, oprot=None):
        self._iprot = self._oprot = iprot
        if oprot is not None:
            self._oprot = oprot
        self._seqid = 0

    def RegisterUser(self, req_id, first_name, last_name, username, password, carrier):
        """
        Parameters:
         - req_id
         - first_name
         - last_name
         - username
         - password
         - carrier

        """
        self.send_RegisterUser(req_id, first_name, last_name, username, password, carrier)
        self.recv_RegisterUser()

    def send_RegisterUser(self, req_id, first_name, last_name, username, password, carrier):
        self._oprot.writeMessageBegin('RegisterUser', TMessageType.CALL, self._seqid)
        args = RegisterUser_args()
        args.req_id = req_id
        args.first_name = first_name
        args.last_name = last_name
        args.username = username
        args.password = password
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_RegisterUser(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = RegisterUser_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.se is not None:
            raise result.se
        return

    def RegisterUserWithId(self, req_id, first_name, last_name, username, password, user_id, carrier):
        """
        Parameters:
         - req_id
         - first_name
         - last_name
         - username
         - password
         - user_id
         - carrier

        """
        self.send_RegisterUserWithId(req_id, first_name, last_name, username, password, user_id, carrier)
        self.recv_RegisterUserWithId()

    def send_RegisterUserWithId(self, req_id, first_name, last_name, username, password, user_id, carrier):
        self._oprot.writeMessageBegin('RegisterUserWithId', TMessageType.CALL, self._seqid)
        args = RegisterUserWithId_args()
        args.req_id = req_id
        args.first_name = first_name
        args.last_name = last_name
        args.username = username
        args.password = password
        args.user_id = user_id
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_RegisterUserWithId(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = RegisterUserWithId_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.se is not None:
            raise result.se
        return

    def Login(self, req_id, username, password, carrier):
        """
        Parameters:
         - req_id
         - username
         - password
         - carrier

        """
        self.send_Login(req_id, username, password, carrier)
        return self.recv_Login()

    def send_Login(self, req_id, username, password, carrier):
        self._oprot.writeMessageBegin('Login', TMessageType.CALL, self._seqid)
        args = Login_args()
        args.req_id = req_id
        args.username = username
        args.password = password
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_Login(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = Login_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.success is not None:
            return result.success
        if result.se is not None:
            raise result.se
        raise TApplicationException(TApplicationException.MISSING_RESULT, 'Login failed: unknown result')

    def UploadUserWithUserId(self, req_id, user_id, carrier):
        """
        Parameters:
         - req_id
         - user_id
         - carrier

        """
        self.send_UploadUserWithUserId(req_id, user_id, carrier)
        self.recv_UploadUserWithUserId()

    def send_UploadUserWithUserId(self, req_id, user_id, carrier):
        self._oprot.writeMessageBegin('UploadUserWithUserId', TMessageType.CALL, self._seqid)
        args = UploadUserWithUserId_args()
        args.req_id = req_id
        args.user_id = user_id
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_UploadUserWithUserId(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = UploadUserWithUserId_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.se is not None:
            raise result.se
        return

    def UploadUserWithUsername(self, req_id, username, carrier):
        """
        Parameters:
         - req_id
         - username
         - carrier

        """
        self.send_UploadUserWithUsername(req_id, username, carrier)
        self.recv_UploadUserWithUsername()

    def send_UploadUserWithUsername(self, req_id, username, carrier):
        self._oprot.writeMessageBegin('UploadUserWithUsername', TMessageType.CALL, self._seqid)
        args = UploadUserWithUsername_args()
        args.req_id = req_id
        args.username = username
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_UploadUserWithUsername(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = UploadUserWithUsername_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.se is not None:
            raise result.se
        return

def send_RegisterUser(self, req_id, first_name, last_name, username, password, carrier):
    self._oprot.writeMessageBegin('RegisterUser', TMessageType.CALL, self._seqid)
    args = RegisterUser_args()
    args.req_id = req_id
    args.first_name = first_name
    args.last_name = last_name
    args.username = username
    args.password = password
    args.carrier = carrier
    args.write(self._oprot)
    self._oprot.writeMessageEnd()
    self._oprot.trans.flush()

# Node: RegisterUser_args
def recv_RegisterUser(self):
    iprot = self._iprot
    fname, mtype, rseqid = iprot.readMessageBegin()
    if mtype == TMessageType.EXCEPTION:
        x = TApplicationException()
        x.read(iprot)
        iprot.readMessageEnd()
        raise x
    result = RegisterUser_result()
    result.read(iprot)
    iprot.readMessageEnd()
    if result.se is not None:
        raise result.se
    return

# Node: RegisterUser_result
def send_RegisterUserWithId(self, req_id, first_name, last_name, username, password, user_id, carrier):
    self._oprot.writeMessageBegin('RegisterUserWithId', TMessageType.CALL, self._seqid)
    args = RegisterUserWithId_args()
    args.req_id = req_id
    args.first_name = first_name
    args.last_name = last_name
    args.username = username
    args.password = password
    args.user_id = user_id
    args.carrier = carrier
    args.write(self._oprot)
    self._oprot.writeMessageEnd()
    self._oprot.trans.flush()

# Node: RegisterUserWithId_args
def recv_RegisterUserWithId(self):
    iprot = self._iprot
    fname, mtype, rseqid = iprot.readMessageBegin()
    if mtype == TMessageType.EXCEPTION:
        x = TApplicationException()
        x.read(iprot)
        iprot.readMessageEnd()
        raise x
    result = RegisterUserWithId_result()
    result.read(iprot)
    iprot.readMessageEnd()
    if result.se is not None:
        raise result.se
    return

# Node: RegisterUserWithId_result
def send_Login(self, req_id, username, password, carrier):
    self._oprot.writeMessageBegin('Login', TMessageType.CALL, self._seqid)
    args = Login_args()
    args.req_id = req_id
    args.username = username
    args.password = password
    args.carrier = carrier
    args.write(self._oprot)
    self._oprot.writeMessageEnd()
    self._oprot.trans.flush()

# Node: Login_args
def recv_Login(self):
    iprot = self._iprot
    fname, mtype, rseqid = iprot.readMessageBegin()
    if mtype == TMessageType.EXCEPTION:
        x = TApplicationException()
        x.read(iprot)
        iprot.readMessageEnd()
        raise x
    result = Login_result()
    result.read(iprot)
    iprot.readMessageEnd()
    if result.success is not None:
        return result.success
    if result.se is not None:
        raise result.se
    raise TApplicationException(TApplicationException.MISSING_RESULT, 'Login failed: unknown result')

# Node: Login_result
def send_UploadUserWithUserId(self, req_id, user_id, carrier):
    self._oprot.writeMessageBegin('UploadUserWithUserId', TMessageType.CALL, self._seqid)
    args = UploadUserWithUserId_args()
    args.req_id = req_id
    args.user_id = user_id
    args.carrier = carrier
    args.write(self._oprot)
    self._oprot.writeMessageEnd()
    self._oprot.trans.flush()

# Node: UploadUserWithUserId_args
def recv_UploadUserWithUserId(self):
    iprot = self._iprot
    fname, mtype, rseqid = iprot.readMessageBegin()
    if mtype == TMessageType.EXCEPTION:
        x = TApplicationException()
        x.read(iprot)
        iprot.readMessageEnd()
        raise x
    result = UploadUserWithUserId_result()
    result.read(iprot)
    iprot.readMessageEnd()
    if result.se is not None:
        raise result.se
    return

# Node: UploadUserWithUserId_result
def send_UploadUserWithUsername(self, req_id, username, carrier):
    self._oprot.writeMessageBegin('UploadUserWithUsername', TMessageType.CALL, self._seqid)
    args = UploadUserWithUsername_args()
    args.req_id = req_id
    args.username = username
    args.carrier = carrier
    args.write(self._oprot)
    self._oprot.writeMessageEnd()
    self._oprot.trans.flush()

# Node: UploadUserWithUsername_args
def recv_UploadUserWithUsername(self):
    iprot = self._iprot
    fname, mtype, rseqid = iprot.readMessageBegin()
    if mtype == TMessageType.EXCEPTION:
        x = TApplicationException()
        x.read(iprot)
        iprot.readMessageEnd()
        raise x
    result = UploadUserWithUsername_result()
    result.read(iprot)
    iprot.readMessageEnd()
    if result.se is not None:
        raise result.se
    return

# Node: UploadUserWithUsername_result
class Processor(Iface, TProcessor):

    def __init__(self, handler):
        self._handler = handler
        self._processMap = {}
        self._processMap['RegisterUser'] = Processor.process_RegisterUser
        self._processMap['RegisterUserWithId'] = Processor.process_RegisterUserWithId
        self._processMap['Login'] = Processor.process_Login
        self._processMap['UploadUserWithUserId'] = Processor.process_UploadUserWithUserId
        self._processMap['UploadUserWithUsername'] = Processor.process_UploadUserWithUsername

    def process(self, iprot, oprot):
        name, type, seqid = iprot.readMessageBegin()
        if name not in self._processMap:
            iprot.skip(TType.STRUCT)
            iprot.readMessageEnd()
            x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
            oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
            x.write(oprot)
            oprot.writeMessageEnd()
            oprot.trans.flush()
            return
        else:
            self._processMap[name](self, seqid, iprot, oprot)
        return True

    def process_RegisterUser(self, seqid, iprot, oprot):
        args = RegisterUser_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = RegisterUser_result()
        try:
            self._handler.RegisterUser(args.req_id, args.first_name, args.last_name, args.username, args.password, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('RegisterUser', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

    def process_RegisterUserWithId(self, seqid, iprot, oprot):
        args = RegisterUserWithId_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = RegisterUserWithId_result()
        try:
            self._handler.RegisterUserWithId(args.req_id, args.first_name, args.last_name, args.username, args.password, args.user_id, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('RegisterUserWithId', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

    def process_Login(self, seqid, iprot, oprot):
        args = Login_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = Login_result()
        try:
            result.success = self._handler.Login(args.req_id, args.username, args.password, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('Login', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

    def process_UploadUserWithUserId(self, seqid, iprot, oprot):
        args = UploadUserWithUserId_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = UploadUserWithUserId_result()
        try:
            self._handler.UploadUserWithUserId(args.req_id, args.user_id, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('UploadUserWithUserId', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

    def process_UploadUserWithUsername(self, seqid, iprot, oprot):
        args = UploadUserWithUsername_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = UploadUserWithUsername_result()
        try:
            self._handler.UploadUserWithUsername(args.req_id, args.username, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('UploadUserWithUsername', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

def process(self, iprot, oprot):
    name, type, seqid = iprot.readMessageBegin()
    if name not in self._processMap:
        iprot.skip(TType.STRUCT)
        iprot.readMessageEnd()
        x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
        oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
        x.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()
        return
    else:
        self._processMap[name](self, seqid, iprot, oprot)
    return True

def process_RegisterUser(self, seqid, iprot, oprot):
    args = RegisterUser_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = RegisterUser_result()
    try:
        self._handler.RegisterUser(args.req_id, args.first_name, args.last_name, args.username, args.password, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('RegisterUser', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

# Node: RegisterUser
def process_RegisterUserWithId(self, seqid, iprot, oprot):
    args = RegisterUserWithId_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = RegisterUserWithId_result()
    try:
        self._handler.RegisterUserWithId(args.req_id, args.first_name, args.last_name, args.username, args.password, args.user_id, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('RegisterUserWithId', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

def process_Login(self, seqid, iprot, oprot):
    args = Login_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = Login_result()
    try:
        result.success = self._handler.Login(args.req_id, args.username, args.password, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('Login', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

# Node: Login
def process_UploadUserWithUserId(self, seqid, iprot, oprot):
    args = UploadUserWithUserId_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = UploadUserWithUserId_result()
    try:
        self._handler.UploadUserWithUserId(args.req_id, args.user_id, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('UploadUserWithUserId', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

def process_UploadUserWithUsername(self, seqid, iprot, oprot):
    args = UploadUserWithUsername_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = UploadUserWithUsername_result()
    try:
        self._handler.UploadUserWithUsername(args.req_id, args.username, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('UploadUserWithUsername', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

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

# Node: UploadMovieId_args
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

# Node: UploadMovieId_result
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

# Node: RegisterMovieId_args
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

# Node: RegisterMovieId_result
class Processor(Iface, TProcessor):

    def __init__(self, handler):
        self._handler = handler
        self._processMap = {}
        self._processMap['UploadMovieId'] = Processor.process_UploadMovieId
        self._processMap['RegisterMovieId'] = Processor.process_RegisterMovieId

    def process(self, iprot, oprot):
        name, type, seqid = iprot.readMessageBegin()
        if name not in self._processMap:
            iprot.skip(TType.STRUCT)
            iprot.readMessageEnd()
            x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
            oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
            x.write(oprot)
            oprot.writeMessageEnd()
            oprot.trans.flush()
            return
        else:
            self._processMap[name](self, seqid, iprot, oprot)
        return True

    def process_UploadMovieId(self, seqid, iprot, oprot):
        args = UploadMovieId_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = UploadMovieId_result()
        try:
            self._handler.UploadMovieId(args.req_id, args.title, args.rating, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('UploadMovieId', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

    def process_RegisterMovieId(self, seqid, iprot, oprot):
        args = RegisterMovieId_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = RegisterMovieId_result()
        try:
            self._handler.RegisterMovieId(args.req_id, args.title, args.movie_id, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('RegisterMovieId', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

def process(self, iprot, oprot):
    name, type, seqid = iprot.readMessageBegin()
    if name not in self._processMap:
        iprot.skip(TType.STRUCT)
        iprot.readMessageEnd()
        x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
        oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
        x.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()
        return
    else:
        self._processMap[name](self, seqid, iprot, oprot)
    return True

def process_UploadMovieId(self, seqid, iprot, oprot):
    args = UploadMovieId_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = UploadMovieId_result()
    try:
        self._handler.UploadMovieId(args.req_id, args.title, args.rating, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('UploadMovieId', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

def process_RegisterMovieId(self, seqid, iprot, oprot):
    args = RegisterMovieId_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = RegisterMovieId_result()
    try:
        self._handler.RegisterMovieId(args.req_id, args.title, args.movie_id, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('RegisterMovieId', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

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

def send_StoreReview(self, req_id, review, carrier):
    self._oprot.writeMessageBegin('StoreReview', TMessageType.CALL, self._seqid)
    args = StoreReview_args()
    args.req_id = req_id
    args.review = review
    args.carrier = carrier
    args.write(self._oprot)
    self._oprot.writeMessageEnd()
    self._oprot.trans.flush()

# Node: StoreReview_args
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

# Node: StoreReview_result
def send_ReadReviews(self, req_id, review_ids, carrier):
    self._oprot.writeMessageBegin('ReadReviews', TMessageType.CALL, self._seqid)
    args = ReadReviews_args()
    args.req_id = req_id
    args.review_ids = review_ids
    args.carrier = carrier
    args.write(self._oprot)
    self._oprot.writeMessageEnd()
    self._oprot.trans.flush()

# Node: ReadReviews_args
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

# Node: ReadReviews_result
class Processor(Iface, TProcessor):

    def __init__(self, handler):
        self._handler = handler
        self._processMap = {}
        self._processMap['StoreReview'] = Processor.process_StoreReview
        self._processMap['ReadReviews'] = Processor.process_ReadReviews

    def process(self, iprot, oprot):
        name, type, seqid = iprot.readMessageBegin()
        if name not in self._processMap:
            iprot.skip(TType.STRUCT)
            iprot.readMessageEnd()
            x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
            oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
            x.write(oprot)
            oprot.writeMessageEnd()
            oprot.trans.flush()
            return
        else:
            self._processMap[name](self, seqid, iprot, oprot)
        return True

    def process_StoreReview(self, seqid, iprot, oprot):
        args = StoreReview_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = StoreReview_result()
        try:
            self._handler.StoreReview(args.req_id, args.review, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('StoreReview', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

    def process_ReadReviews(self, seqid, iprot, oprot):
        args = ReadReviews_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = ReadReviews_result()
        try:
            result.success = self._handler.ReadReviews(args.req_id, args.review_ids, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('ReadReviews', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

def process(self, iprot, oprot):
    name, type, seqid = iprot.readMessageBegin()
    if name not in self._processMap:
        iprot.skip(TType.STRUCT)
        iprot.readMessageEnd()
        x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
        oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
        x.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()
        return
    else:
        self._processMap[name](self, seqid, iprot, oprot)
    return True

def process_StoreReview(self, seqid, iprot, oprot):
    args = StoreReview_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = StoreReview_result()
    try:
        self._handler.StoreReview(args.req_id, args.review, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('StoreReview', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

def process_ReadReviews(self, seqid, iprot, oprot):
    args = ReadReviews_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = ReadReviews_result()
    try:
        result.success = self._handler.ReadReviews(args.req_id, args.review_ids, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('ReadReviews', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

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

# Node: ReadPage_args
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

# Node: ReadPage_result
class Processor(Iface, TProcessor):

    def __init__(self, handler):
        self._handler = handler
        self._processMap = {}
        self._processMap['ReadPage'] = Processor.process_ReadPage

    def process(self, iprot, oprot):
        name, type, seqid = iprot.readMessageBegin()
        if name not in self._processMap:
            iprot.skip(TType.STRUCT)
            iprot.readMessageEnd()
            x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
            oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
            x.write(oprot)
            oprot.writeMessageEnd()
            oprot.trans.flush()
            return
        else:
            self._processMap[name](self, seqid, iprot, oprot)
        return True

    def process_ReadPage(self, seqid, iprot, oprot):
        args = ReadPage_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = ReadPage_result()
        try:
            result.success = self._handler.ReadPage(args.req_id, args.movie_id, args.review_start, args.review_stop, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('ReadPage', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

def process(self, iprot, oprot):
    name, type, seqid = iprot.readMessageBegin()
    if name not in self._processMap:
        iprot.skip(TType.STRUCT)
        iprot.readMessageEnd()
        x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
        oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
        x.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()
        return
    else:
        self._processMap[name](self, seqid, iprot, oprot)
    return True

def process_ReadPage(self, seqid, iprot, oprot):
    args = ReadPage_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = ReadPage_result()
    try:
        result.success = self._handler.ReadPage(args.req_id, args.movie_id, args.review_start, args.review_stop, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('ReadPage', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

class Client(Iface):

    def __init__(self, iprot, oprot=None):
        self._iprot = self._oprot = iprot
        if oprot is not None:
            self._oprot = oprot
        self._seqid = 0

    def WriteCastInfo(self, req_id, cast_info_id, name, gender, intro, carrier):
        """
        Parameters:
         - req_id
         - cast_info_id
         - name
         - gender
         - intro
         - carrier

        """
        self.send_WriteCastInfo(req_id, cast_info_id, name, gender, intro, carrier)
        self.recv_WriteCastInfo()

    def send_WriteCastInfo(self, req_id, cast_info_id, name, gender, intro, carrier):
        self._oprot.writeMessageBegin('WriteCastInfo', TMessageType.CALL, self._seqid)
        args = WriteCastInfo_args()
        args.req_id = req_id
        args.cast_info_id = cast_info_id
        args.name = name
        args.gender = gender
        args.intro = intro
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_WriteCastInfo(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = WriteCastInfo_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.se is not None:
            raise result.se
        return

    def ReadCastInfo(self, req_id, cast_ids, carrier):
        """
        Parameters:
         - req_id
         - cast_ids
         - carrier

        """
        self.send_ReadCastInfo(req_id, cast_ids, carrier)
        return self.recv_ReadCastInfo()

    def send_ReadCastInfo(self, req_id, cast_ids, carrier):
        self._oprot.writeMessageBegin('ReadCastInfo', TMessageType.CALL, self._seqid)
        args = ReadCastInfo_args()
        args.req_id = req_id
        args.cast_ids = cast_ids
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_ReadCastInfo(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = ReadCastInfo_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.success is not None:
            return result.success
        if result.se is not None:
            raise result.se
        raise TApplicationException(TApplicationException.MISSING_RESULT, 'ReadCastInfo failed: unknown result')

def send_WriteCastInfo(self, req_id, cast_info_id, name, gender, intro, carrier):
    self._oprot.writeMessageBegin('WriteCastInfo', TMessageType.CALL, self._seqid)
    args = WriteCastInfo_args()
    args.req_id = req_id
    args.cast_info_id = cast_info_id
    args.name = name
    args.gender = gender
    args.intro = intro
    args.carrier = carrier
    args.write(self._oprot)
    self._oprot.writeMessageEnd()
    self._oprot.trans.flush()

# Node: WriteCastInfo_args
def recv_WriteCastInfo(self):
    iprot = self._iprot
    fname, mtype, rseqid = iprot.readMessageBegin()
    if mtype == TMessageType.EXCEPTION:
        x = TApplicationException()
        x.read(iprot)
        iprot.readMessageEnd()
        raise x
    result = WriteCastInfo_result()
    result.read(iprot)
    iprot.readMessageEnd()
    if result.se is not None:
        raise result.se
    return

# Node: WriteCastInfo_result
def send_ReadCastInfo(self, req_id, cast_ids, carrier):
    self._oprot.writeMessageBegin('ReadCastInfo', TMessageType.CALL, self._seqid)
    args = ReadCastInfo_args()
    args.req_id = req_id
    args.cast_ids = cast_ids
    args.carrier = carrier
    args.write(self._oprot)
    self._oprot.writeMessageEnd()
    self._oprot.trans.flush()

# Node: ReadCastInfo_args
def recv_ReadCastInfo(self):
    iprot = self._iprot
    fname, mtype, rseqid = iprot.readMessageBegin()
    if mtype == TMessageType.EXCEPTION:
        x = TApplicationException()
        x.read(iprot)
        iprot.readMessageEnd()
        raise x
    result = ReadCastInfo_result()
    result.read(iprot)
    iprot.readMessageEnd()
    if result.success is not None:
        return result.success
    if result.se is not None:
        raise result.se
    raise TApplicationException(TApplicationException.MISSING_RESULT, 'ReadCastInfo failed: unknown result')

# Node: ReadCastInfo_result
class Processor(Iface, TProcessor):

    def __init__(self, handler):
        self._handler = handler
        self._processMap = {}
        self._processMap['WriteCastInfo'] = Processor.process_WriteCastInfo
        self._processMap['ReadCastInfo'] = Processor.process_ReadCastInfo

    def process(self, iprot, oprot):
        name, type, seqid = iprot.readMessageBegin()
        if name not in self._processMap:
            iprot.skip(TType.STRUCT)
            iprot.readMessageEnd()
            x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
            oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
            x.write(oprot)
            oprot.writeMessageEnd()
            oprot.trans.flush()
            return
        else:
            self._processMap[name](self, seqid, iprot, oprot)
        return True

    def process_WriteCastInfo(self, seqid, iprot, oprot):
        args = WriteCastInfo_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = WriteCastInfo_result()
        try:
            self._handler.WriteCastInfo(args.req_id, args.cast_info_id, args.name, args.gender, args.intro, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('WriteCastInfo', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

    def process_ReadCastInfo(self, seqid, iprot, oprot):
        args = ReadCastInfo_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = ReadCastInfo_result()
        try:
            result.success = self._handler.ReadCastInfo(args.req_id, args.cast_ids, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('ReadCastInfo', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

def process(self, iprot, oprot):
    name, type, seqid = iprot.readMessageBegin()
    if name not in self._processMap:
        iprot.skip(TType.STRUCT)
        iprot.readMessageEnd()
        x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
        oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
        x.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()
        return
    else:
        self._processMap[name](self, seqid, iprot, oprot)
    return True

def process_WriteCastInfo(self, seqid, iprot, oprot):
    args = WriteCastInfo_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = WriteCastInfo_result()
    try:
        self._handler.WriteCastInfo(args.req_id, args.cast_info_id, args.name, args.gender, args.intro, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('WriteCastInfo', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

def process_ReadCastInfo(self, seqid, iprot, oprot):
    args = ReadCastInfo_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = ReadCastInfo_result()
    try:
        result.success = self._handler.ReadCastInfo(args.req_id, args.cast_ids, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('ReadCastInfo', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

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

# Node: UploadUserReview_args
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

# Node: UploadUserReview_result
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

# Node: ReadUserReviews_args
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

# Node: ReadUserReviews_result
class Processor(Iface, TProcessor):

    def __init__(self, handler):
        self._handler = handler
        self._processMap = {}
        self._processMap['UploadUserReview'] = Processor.process_UploadUserReview
        self._processMap['ReadUserReviews'] = Processor.process_ReadUserReviews

    def process(self, iprot, oprot):
        name, type, seqid = iprot.readMessageBegin()
        if name not in self._processMap:
            iprot.skip(TType.STRUCT)
            iprot.readMessageEnd()
            x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
            oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
            x.write(oprot)
            oprot.writeMessageEnd()
            oprot.trans.flush()
            return
        else:
            self._processMap[name](self, seqid, iprot, oprot)
        return True

    def process_UploadUserReview(self, seqid, iprot, oprot):
        args = UploadUserReview_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = UploadUserReview_result()
        try:
            self._handler.UploadUserReview(args.req_id, args.user_id, args.review_id, args.timestamp, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('UploadUserReview', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

    def process_ReadUserReviews(self, seqid, iprot, oprot):
        args = ReadUserReviews_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = ReadUserReviews_result()
        try:
            result.success = self._handler.ReadUserReviews(args.req_id, args.user_id, args.start, args.stop, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('ReadUserReviews', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

def process(self, iprot, oprot):
    name, type, seqid = iprot.readMessageBegin()
    if name not in self._processMap:
        iprot.skip(TType.STRUCT)
        iprot.readMessageEnd()
        x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
        oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
        x.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()
        return
    else:
        self._processMap[name](self, seqid, iprot, oprot)
    return True

def process_UploadUserReview(self, seqid, iprot, oprot):
    args = UploadUserReview_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = UploadUserReview_result()
    try:
        self._handler.UploadUserReview(args.req_id, args.user_id, args.review_id, args.timestamp, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('UploadUserReview', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

def process_ReadUserReviews(self, seqid, iprot, oprot):
    args = ReadUserReviews_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = ReadUserReviews_result()
    try:
        result.success = self._handler.ReadUserReviews(args.req_id, args.user_id, args.start, args.stop, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('ReadUserReviews', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

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

def send_UploadRating(self, req_id, rating, carrier):
    self._oprot.writeMessageBegin('UploadRating', TMessageType.CALL, self._seqid)
    args = UploadRating_args()
    args.req_id = req_id
    args.rating = rating
    args.carrier = carrier
    args.write(self._oprot)
    self._oprot.writeMessageEnd()
    self._oprot.trans.flush()

# Node: UploadRating_args
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

# Node: UploadRating_result
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

def send_UploadUniqueId(self, req_id, unique_id, carrier):
    self._oprot.writeMessageBegin('UploadUniqueId', TMessageType.CALL, self._seqid)
    args = UploadUniqueId_args()
    args.req_id = req_id
    args.unique_id = unique_id
    args.carrier = carrier
    args.write(self._oprot)
    self._oprot.writeMessageEnd()
    self._oprot.trans.flush()

# Node: UploadUniqueId_args
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

# Node: UploadUniqueId_result
def send_UploadUserId(self, req_id, user_id, carrier):
    self._oprot.writeMessageBegin('UploadUserId', TMessageType.CALL, self._seqid)
    args = UploadUserId_args()
    args.req_id = req_id
    args.user_id = user_id
    args.carrier = carrier
    args.write(self._oprot)
    self._oprot.writeMessageEnd()
    self._oprot.trans.flush()

# Node: UploadUserId_args
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

# Node: UploadUserId_result
class Processor(Iface, TProcessor):

    def __init__(self, handler):
        self._handler = handler
        self._processMap = {}
        self._processMap['UploadText'] = Processor.process_UploadText
        self._processMap['UploadRating'] = Processor.process_UploadRating
        self._processMap['UploadMovieId'] = Processor.process_UploadMovieId
        self._processMap['UploadUniqueId'] = Processor.process_UploadUniqueId
        self._processMap['UploadUserId'] = Processor.process_UploadUserId

    def process(self, iprot, oprot):
        name, type, seqid = iprot.readMessageBegin()
        if name not in self._processMap:
            iprot.skip(TType.STRUCT)
            iprot.readMessageEnd()
            x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
            oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
            x.write(oprot)
            oprot.writeMessageEnd()
            oprot.trans.flush()
            return
        else:
            self._processMap[name](self, seqid, iprot, oprot)
        return True

    def process_UploadText(self, seqid, iprot, oprot):
        args = UploadText_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = UploadText_result()
        try:
            self._handler.UploadText(args.req_id, args.text, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('UploadText', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

    def process_UploadRating(self, seqid, iprot, oprot):
        args = UploadRating_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = UploadRating_result()
        try:
            self._handler.UploadRating(args.req_id, args.rating, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('UploadRating', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

    def process_UploadMovieId(self, seqid, iprot, oprot):
        args = UploadMovieId_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = UploadMovieId_result()
        try:
            self._handler.UploadMovieId(args.req_id, args.movie_id, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('UploadMovieId', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

    def process_UploadUniqueId(self, seqid, iprot, oprot):
        args = UploadUniqueId_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = UploadUniqueId_result()
        try:
            self._handler.UploadUniqueId(args.req_id, args.unique_id, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('UploadUniqueId', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

    def process_UploadUserId(self, seqid, iprot, oprot):
        args = UploadUserId_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = UploadUserId_result()
        try:
            self._handler.UploadUserId(args.req_id, args.user_id, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('UploadUserId', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

def process(self, iprot, oprot):
    name, type, seqid = iprot.readMessageBegin()
    if name not in self._processMap:
        iprot.skip(TType.STRUCT)
        iprot.readMessageEnd()
        x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
        oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
        x.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()
        return
    else:
        self._processMap[name](self, seqid, iprot, oprot)
    return True

def process_UploadText(self, seqid, iprot, oprot):
    args = UploadText_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = UploadText_result()
    try:
        self._handler.UploadText(args.req_id, args.text, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('UploadText', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

def process_UploadRating(self, seqid, iprot, oprot):
    args = UploadRating_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = UploadRating_result()
    try:
        self._handler.UploadRating(args.req_id, args.rating, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('UploadRating', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

def process_UploadMovieId(self, seqid, iprot, oprot):
    args = UploadMovieId_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = UploadMovieId_result()
    try:
        self._handler.UploadMovieId(args.req_id, args.movie_id, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('UploadMovieId', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

def process_UploadUniqueId(self, seqid, iprot, oprot):
    args = UploadUniqueId_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = UploadUniqueId_result()
    try:
        self._handler.UploadUniqueId(args.req_id, args.unique_id, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('UploadUniqueId', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

def process_UploadUserId(self, seqid, iprot, oprot):
    args = UploadUserId_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = UploadUserId_result()
    try:
        self._handler.UploadUserId(args.req_id, args.user_id, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('UploadUserId', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

class Client(Iface):

    def __init__(self, iprot, oprot=None):
        self._iprot = self._oprot = iprot
        if oprot is not None:
            self._oprot = oprot
        self._seqid = 0

    def UploadRating(self, req_id, movie_id, rating, carrier):
        """
        Parameters:
         - req_id
         - movie_id
         - rating
         - carrier

        """
        self.send_UploadRating(req_id, movie_id, rating, carrier)
        self.recv_UploadRating()

    def send_UploadRating(self, req_id, movie_id, rating, carrier):
        self._oprot.writeMessageBegin('UploadRating', TMessageType.CALL, self._seqid)
        args = UploadRating_args()
        args.req_id = req_id
        args.movie_id = movie_id
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

def send_UploadRating(self, req_id, movie_id, rating, carrier):
    self._oprot.writeMessageBegin('UploadRating', TMessageType.CALL, self._seqid)
    args = UploadRating_args()
    args.req_id = req_id
    args.movie_id = movie_id
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

class Processor(Iface, TProcessor):

    def __init__(self, handler):
        self._handler = handler
        self._processMap = {}
        self._processMap['UploadRating'] = Processor.process_UploadRating

    def process(self, iprot, oprot):
        name, type, seqid = iprot.readMessageBegin()
        if name not in self._processMap:
            iprot.skip(TType.STRUCT)
            iprot.readMessageEnd()
            x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
            oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
            x.write(oprot)
            oprot.writeMessageEnd()
            oprot.trans.flush()
            return
        else:
            self._processMap[name](self, seqid, iprot, oprot)
        return True

    def process_UploadRating(self, seqid, iprot, oprot):
        args = UploadRating_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = UploadRating_result()
        try:
            self._handler.UploadRating(args.req_id, args.movie_id, args.rating, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('UploadRating', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

def process(self, iprot, oprot):
    name, type, seqid = iprot.readMessageBegin()
    if name not in self._processMap:
        iprot.skip(TType.STRUCT)
        iprot.readMessageEnd()
        x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
        oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
        x.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()
        return
    else:
        self._processMap[name](self, seqid, iprot, oprot)
    return True

def process_UploadRating(self, seqid, iprot, oprot):
    args = UploadRating_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = UploadRating_result()
    try:
        self._handler.UploadRating(args.req_id, args.movie_id, args.rating, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('UploadRating', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

class Client(Iface):

    def __init__(self, iprot, oprot=None):
        self._iprot = self._oprot = iprot
        if oprot is not None:
            self._oprot = oprot
        self._seqid = 0

    def UploadUniqueId(self, req_id, carrier):
        """
        Parameters:
         - req_id
         - carrier

        """
        self.send_UploadUniqueId(req_id, carrier)
        self.recv_UploadUniqueId()

    def send_UploadUniqueId(self, req_id, carrier):
        self._oprot.writeMessageBegin('UploadUniqueId', TMessageType.CALL, self._seqid)
        args = UploadUniqueId_args()
        args.req_id = req_id
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

def send_UploadUniqueId(self, req_id, carrier):
    self._oprot.writeMessageBegin('UploadUniqueId', TMessageType.CALL, self._seqid)
    args = UploadUniqueId_args()
    args.req_id = req_id
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

class Processor(Iface, TProcessor):

    def __init__(self, handler):
        self._handler = handler
        self._processMap = {}
        self._processMap['UploadUniqueId'] = Processor.process_UploadUniqueId

    def process(self, iprot, oprot):
        name, type, seqid = iprot.readMessageBegin()
        if name not in self._processMap:
            iprot.skip(TType.STRUCT)
            iprot.readMessageEnd()
            x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
            oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
            x.write(oprot)
            oprot.writeMessageEnd()
            oprot.trans.flush()
            return
        else:
            self._processMap[name](self, seqid, iprot, oprot)
        return True

    def process_UploadUniqueId(self, seqid, iprot, oprot):
        args = UploadUniqueId_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = UploadUniqueId_result()
        try:
            self._handler.UploadUniqueId(args.req_id, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('UploadUniqueId', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

def process(self, iprot, oprot):
    name, type, seqid = iprot.readMessageBegin()
    if name not in self._processMap:
        iprot.skip(TType.STRUCT)
        iprot.readMessageEnd()
        x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
        oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
        x.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()
        return
    else:
        self._processMap[name](self, seqid, iprot, oprot)
    return True

def process_UploadUniqueId(self, seqid, iprot, oprot):
    args = UploadUniqueId_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = UploadUniqueId_result()
    try:
        self._handler.UploadUniqueId(args.req_id, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('UploadUniqueId', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

class Client(Iface):

    def __init__(self, iprot, oprot=None):
        self._iprot = self._oprot = iprot
        if oprot is not None:
            self._oprot = oprot
        self._seqid = 0

    def ReadHomeTimeline(self, req_id, user_id, start, stop, carrier):
        """
        Parameters:
         - req_id
         - user_id
         - start
         - stop
         - carrier

        """
        self.send_ReadHomeTimeline(req_id, user_id, start, stop, carrier)
        return self.recv_ReadHomeTimeline()

    def send_ReadHomeTimeline(self, req_id, user_id, start, stop, carrier):
        self._oprot.writeMessageBegin('ReadHomeTimeline', TMessageType.CALL, self._seqid)
        args = ReadHomeTimeline_args()
        args.req_id = req_id
        args.user_id = user_id
        args.start = start
        args.stop = stop
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_ReadHomeTimeline(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = ReadHomeTimeline_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.success is not None:
            return result.success
        if result.se is not None:
            raise result.se
        raise TApplicationException(TApplicationException.MISSING_RESULT, 'ReadHomeTimeline failed: unknown result')

    def WriteHomeTimeline(self, req_id, post_id, user_id, timestamp, user_mentions_id, carrier):
        """
        Parameters:
         - req_id
         - post_id
         - user_id
         - timestamp
         - user_mentions_id
         - carrier

        """
        self.send_WriteHomeTimeline(req_id, post_id, user_id, timestamp, user_mentions_id, carrier)
        self.recv_WriteHomeTimeline()

    def send_WriteHomeTimeline(self, req_id, post_id, user_id, timestamp, user_mentions_id, carrier):
        self._oprot.writeMessageBegin('WriteHomeTimeline', TMessageType.CALL, self._seqid)
        args = WriteHomeTimeline_args()
        args.req_id = req_id
        args.post_id = post_id
        args.user_id = user_id
        args.timestamp = timestamp
        args.user_mentions_id = user_mentions_id
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_WriteHomeTimeline(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = WriteHomeTimeline_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.se is not None:
            raise result.se
        return

def send_ReadHomeTimeline(self, req_id, user_id, start, stop, carrier):
    self._oprot.writeMessageBegin('ReadHomeTimeline', TMessageType.CALL, self._seqid)
    args = ReadHomeTimeline_args()
    args.req_id = req_id
    args.user_id = user_id
    args.start = start
    args.stop = stop
    args.carrier = carrier
    args.write(self._oprot)
    self._oprot.writeMessageEnd()
    self._oprot.trans.flush()

# Node: ReadHomeTimeline_args
def recv_ReadHomeTimeline(self):
    iprot = self._iprot
    fname, mtype, rseqid = iprot.readMessageBegin()
    if mtype == TMessageType.EXCEPTION:
        x = TApplicationException()
        x.read(iprot)
        iprot.readMessageEnd()
        raise x
    result = ReadHomeTimeline_result()
    result.read(iprot)
    iprot.readMessageEnd()
    if result.success is not None:
        return result.success
    if result.se is not None:
        raise result.se
    raise TApplicationException(TApplicationException.MISSING_RESULT, 'ReadHomeTimeline failed: unknown result')

# Node: ReadHomeTimeline_result
def send_WriteHomeTimeline(self, req_id, post_id, user_id, timestamp, user_mentions_id, carrier):
    self._oprot.writeMessageBegin('WriteHomeTimeline', TMessageType.CALL, self._seqid)
    args = WriteHomeTimeline_args()
    args.req_id = req_id
    args.post_id = post_id
    args.user_id = user_id
    args.timestamp = timestamp
    args.user_mentions_id = user_mentions_id
    args.carrier = carrier
    args.write(self._oprot)
    self._oprot.writeMessageEnd()
    self._oprot.trans.flush()

# Node: WriteHomeTimeline_args
def recv_WriteHomeTimeline(self):
    iprot = self._iprot
    fname, mtype, rseqid = iprot.readMessageBegin()
    if mtype == TMessageType.EXCEPTION:
        x = TApplicationException()
        x.read(iprot)
        iprot.readMessageEnd()
        raise x
    result = WriteHomeTimeline_result()
    result.read(iprot)
    iprot.readMessageEnd()
    if result.se is not None:
        raise result.se
    return

# Node: WriteHomeTimeline_result
class Processor(Iface, TProcessor):

    def __init__(self, handler):
        self._handler = handler
        self._processMap = {}
        self._processMap['ReadHomeTimeline'] = Processor.process_ReadHomeTimeline
        self._processMap['WriteHomeTimeline'] = Processor.process_WriteHomeTimeline
        self._on_message_begin = None

    def on_message_begin(self, func):
        self._on_message_begin = func

    def process(self, iprot, oprot):
        name, type, seqid = iprot.readMessageBegin()
        if self._on_message_begin:
            self._on_message_begin(name, type, seqid)
        if name not in self._processMap:
            iprot.skip(TType.STRUCT)
            iprot.readMessageEnd()
            x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
            oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
            x.write(oprot)
            oprot.writeMessageEnd()
            oprot.trans.flush()
            return
        else:
            self._processMap[name](self, seqid, iprot, oprot)
        return True

    def process_ReadHomeTimeline(self, seqid, iprot, oprot):
        args = ReadHomeTimeline_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = ReadHomeTimeline_result()
        try:
            result.success = self._handler.ReadHomeTimeline(args.req_id, args.user_id, args.start, args.stop, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('ReadHomeTimeline', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

    def process_WriteHomeTimeline(self, seqid, iprot, oprot):
        args = WriteHomeTimeline_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = WriteHomeTimeline_result()
        try:
            self._handler.WriteHomeTimeline(args.req_id, args.post_id, args.user_id, args.timestamp, args.user_mentions_id, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('WriteHomeTimeline', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

def process(self, iprot, oprot):
    name, type, seqid = iprot.readMessageBegin()
    if self._on_message_begin:
        self._on_message_begin(name, type, seqid)
    if name not in self._processMap:
        iprot.skip(TType.STRUCT)
        iprot.readMessageEnd()
        x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
        oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
        x.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()
        return
    else:
        self._processMap[name](self, seqid, iprot, oprot)
    return True

# Node: _on_message_begin
def process_ReadHomeTimeline(self, seqid, iprot, oprot):
    args = ReadHomeTimeline_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = ReadHomeTimeline_result()
    try:
        result.success = self._handler.ReadHomeTimeline(args.req_id, args.user_id, args.start, args.stop, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('ReadHomeTimeline', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

def process_WriteHomeTimeline(self, seqid, iprot, oprot):
    args = WriteHomeTimeline_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = WriteHomeTimeline_result()
    try:
        self._handler.WriteHomeTimeline(args.req_id, args.post_id, args.user_id, args.timestamp, args.user_mentions_id, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('WriteHomeTimeline', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

# Node: WriteHomeTimeline
class Client(Iface):

    def __init__(self, iprot, oprot=None):
        self._iprot = self._oprot = iprot
        if oprot is not None:
            self._oprot = oprot
        self._seqid = 0

    def ComposeText(self, req_id, text, carrier):
        """
        Parameters:
         - req_id
         - text
         - carrier

        """
        self.send_ComposeText(req_id, text, carrier)
        return self.recv_ComposeText()

    def send_ComposeText(self, req_id, text, carrier):
        self._oprot.writeMessageBegin('ComposeText', TMessageType.CALL, self._seqid)
        args = ComposeText_args()
        args.req_id = req_id
        args.text = text
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_ComposeText(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = ComposeText_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.success is not None:
            return result.success
        if result.se is not None:
            raise result.se
        raise TApplicationException(TApplicationException.MISSING_RESULT, 'ComposeText failed: unknown result')

def send_ComposeText(self, req_id, text, carrier):
    self._oprot.writeMessageBegin('ComposeText', TMessageType.CALL, self._seqid)
    args = ComposeText_args()
    args.req_id = req_id
    args.text = text
    args.carrier = carrier
    args.write(self._oprot)
    self._oprot.writeMessageEnd()
    self._oprot.trans.flush()

# Node: ComposeText_args
def recv_ComposeText(self):
    iprot = self._iprot
    fname, mtype, rseqid = iprot.readMessageBegin()
    if mtype == TMessageType.EXCEPTION:
        x = TApplicationException()
        x.read(iprot)
        iprot.readMessageEnd()
        raise x
    result = ComposeText_result()
    result.read(iprot)
    iprot.readMessageEnd()
    if result.success is not None:
        return result.success
    if result.se is not None:
        raise result.se
    raise TApplicationException(TApplicationException.MISSING_RESULT, 'ComposeText failed: unknown result')

# Node: ComposeText_result
class Processor(Iface, TProcessor):

    def __init__(self, handler):
        self._handler = handler
        self._processMap = {}
        self._processMap['ComposeText'] = Processor.process_ComposeText
        self._on_message_begin = None

    def on_message_begin(self, func):
        self._on_message_begin = func

    def process(self, iprot, oprot):
        name, type, seqid = iprot.readMessageBegin()
        if self._on_message_begin:
            self._on_message_begin(name, type, seqid)
        if name not in self._processMap:
            iprot.skip(TType.STRUCT)
            iprot.readMessageEnd()
            x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
            oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
            x.write(oprot)
            oprot.writeMessageEnd()
            oprot.trans.flush()
            return
        else:
            self._processMap[name](self, seqid, iprot, oprot)
        return True

    def process_ComposeText(self, seqid, iprot, oprot):
        args = ComposeText_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = ComposeText_result()
        try:
            result.success = self._handler.ComposeText(args.req_id, args.text, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('ComposeText', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

def process(self, iprot, oprot):
    name, type, seqid = iprot.readMessageBegin()
    if self._on_message_begin:
        self._on_message_begin(name, type, seqid)
    if name not in self._processMap:
        iprot.skip(TType.STRUCT)
        iprot.readMessageEnd()
        x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
        oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
        x.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()
        return
    else:
        self._processMap[name](self, seqid, iprot, oprot)
    return True

def process_ComposeText(self, seqid, iprot, oprot):
    args = ComposeText_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = ComposeText_result()
    try:
        result.success = self._handler.ComposeText(args.req_id, args.text, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('ComposeText', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

# Node: ComposeText
class Client(Iface):

    def __init__(self, iprot, oprot=None):
        self._iprot = self._oprot = iprot
        if oprot is not None:
            self._oprot = oprot
        self._seqid = 0

    def ComposeMedia(self, req_id, media_types, media_ids, carrier):
        """
        Parameters:
         - req_id
         - media_types
         - media_ids
         - carrier

        """
        self.send_ComposeMedia(req_id, media_types, media_ids, carrier)
        return self.recv_ComposeMedia()

    def send_ComposeMedia(self, req_id, media_types, media_ids, carrier):
        self._oprot.writeMessageBegin('ComposeMedia', TMessageType.CALL, self._seqid)
        args = ComposeMedia_args()
        args.req_id = req_id
        args.media_types = media_types
        args.media_ids = media_ids
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_ComposeMedia(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = ComposeMedia_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.success is not None:
            return result.success
        if result.se is not None:
            raise result.se
        raise TApplicationException(TApplicationException.MISSING_RESULT, 'ComposeMedia failed: unknown result')

def send_ComposeMedia(self, req_id, media_types, media_ids, carrier):
    self._oprot.writeMessageBegin('ComposeMedia', TMessageType.CALL, self._seqid)
    args = ComposeMedia_args()
    args.req_id = req_id
    args.media_types = media_types
    args.media_ids = media_ids
    args.carrier = carrier
    args.write(self._oprot)
    self._oprot.writeMessageEnd()
    self._oprot.trans.flush()

# Node: ComposeMedia_args
def recv_ComposeMedia(self):
    iprot = self._iprot
    fname, mtype, rseqid = iprot.readMessageBegin()
    if mtype == TMessageType.EXCEPTION:
        x = TApplicationException()
        x.read(iprot)
        iprot.readMessageEnd()
        raise x
    result = ComposeMedia_result()
    result.read(iprot)
    iprot.readMessageEnd()
    if result.success is not None:
        return result.success
    if result.se is not None:
        raise result.se
    raise TApplicationException(TApplicationException.MISSING_RESULT, 'ComposeMedia failed: unknown result')

# Node: ComposeMedia_result
class Processor(Iface, TProcessor):

    def __init__(self, handler):
        self._handler = handler
        self._processMap = {}
        self._processMap['ComposeMedia'] = Processor.process_ComposeMedia
        self._on_message_begin = None

    def on_message_begin(self, func):
        self._on_message_begin = func

    def process(self, iprot, oprot):
        name, type, seqid = iprot.readMessageBegin()
        if self._on_message_begin:
            self._on_message_begin(name, type, seqid)
        if name not in self._processMap:
            iprot.skip(TType.STRUCT)
            iprot.readMessageEnd()
            x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
            oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
            x.write(oprot)
            oprot.writeMessageEnd()
            oprot.trans.flush()
            return
        else:
            self._processMap[name](self, seqid, iprot, oprot)
        return True

    def process_ComposeMedia(self, seqid, iprot, oprot):
        args = ComposeMedia_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = ComposeMedia_result()
        try:
            result.success = self._handler.ComposeMedia(args.req_id, args.media_types, args.media_ids, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('ComposeMedia', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

def process(self, iprot, oprot):
    name, type, seqid = iprot.readMessageBegin()
    if self._on_message_begin:
        self._on_message_begin(name, type, seqid)
    if name not in self._processMap:
        iprot.skip(TType.STRUCT)
        iprot.readMessageEnd()
        x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
        oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
        x.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()
        return
    else:
        self._processMap[name](self, seqid, iprot, oprot)
    return True

def process_ComposeMedia(self, seqid, iprot, oprot):
    args = ComposeMedia_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = ComposeMedia_result()
    try:
        result.success = self._handler.ComposeMedia(args.req_id, args.media_types, args.media_ids, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('ComposeMedia', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

# Node: ComposeMedia
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

def send_ComposeUrls(self, req_id, urls, carrier):
    self._oprot.writeMessageBegin('ComposeUrls', TMessageType.CALL, self._seqid)
    args = ComposeUrls_args()
    args.req_id = req_id
    args.urls = urls
    args.carrier = carrier
    args.write(self._oprot)
    self._oprot.writeMessageEnd()
    self._oprot.trans.flush()

# Node: ComposeUrls_args
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

# Node: ComposeUrls_result
def send_GetExtendedUrls(self, req_id, shortened_urls, carrier):
    self._oprot.writeMessageBegin('GetExtendedUrls', TMessageType.CALL, self._seqid)
    args = GetExtendedUrls_args()
    args.req_id = req_id
    args.shortened_urls = shortened_urls
    args.carrier = carrier
    args.write(self._oprot)
    self._oprot.writeMessageEnd()
    self._oprot.trans.flush()

# Node: GetExtendedUrls_args
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

# Node: GetExtendedUrls_result
class Processor(Iface, TProcessor):

    def __init__(self, handler):
        self._handler = handler
        self._processMap = {}
        self._processMap['ComposeUrls'] = Processor.process_ComposeUrls
        self._processMap['GetExtendedUrls'] = Processor.process_GetExtendedUrls
        self._on_message_begin = None

    def on_message_begin(self, func):
        self._on_message_begin = func

    def process(self, iprot, oprot):
        name, type, seqid = iprot.readMessageBegin()
        if self._on_message_begin:
            self._on_message_begin(name, type, seqid)
        if name not in self._processMap:
            iprot.skip(TType.STRUCT)
            iprot.readMessageEnd()
            x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
            oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
            x.write(oprot)
            oprot.writeMessageEnd()
            oprot.trans.flush()
            return
        else:
            self._processMap[name](self, seqid, iprot, oprot)
        return True

    def process_ComposeUrls(self, seqid, iprot, oprot):
        args = ComposeUrls_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = ComposeUrls_result()
        try:
            result.success = self._handler.ComposeUrls(args.req_id, args.urls, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('ComposeUrls', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

    def process_GetExtendedUrls(self, seqid, iprot, oprot):
        args = GetExtendedUrls_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = GetExtendedUrls_result()
        try:
            result.success = self._handler.GetExtendedUrls(args.req_id, args.shortened_urls, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('GetExtendedUrls', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

def process(self, iprot, oprot):
    name, type, seqid = iprot.readMessageBegin()
    if self._on_message_begin:
        self._on_message_begin(name, type, seqid)
    if name not in self._processMap:
        iprot.skip(TType.STRUCT)
        iprot.readMessageEnd()
        x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
        oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
        x.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()
        return
    else:
        self._processMap[name](self, seqid, iprot, oprot)
    return True

def process_ComposeUrls(self, seqid, iprot, oprot):
    args = ComposeUrls_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = ComposeUrls_result()
    try:
        result.success = self._handler.ComposeUrls(args.req_id, args.urls, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('ComposeUrls', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

# Node: ComposeUrls
def process_GetExtendedUrls(self, seqid, iprot, oprot):
    args = GetExtendedUrls_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = GetExtendedUrls_result()
    try:
        result.success = self._handler.GetExtendedUrls(args.req_id, args.shortened_urls, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('GetExtendedUrls', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

# Node: GetExtendedUrls
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

def send_StorePost(self, req_id, post, carrier):
    self._oprot.writeMessageBegin('StorePost', TMessageType.CALL, self._seqid)
    args = StorePost_args()
    args.req_id = req_id
    args.post = post
    args.carrier = carrier
    args.write(self._oprot)
    self._oprot.writeMessageEnd()
    self._oprot.trans.flush()

# Node: StorePost_args
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

# Node: StorePost_result
def send_ReadPost(self, req_id, post_id, carrier):
    self._oprot.writeMessageBegin('ReadPost', TMessageType.CALL, self._seqid)
    args = ReadPost_args()
    args.req_id = req_id
    args.post_id = post_id
    args.carrier = carrier
    args.write(self._oprot)
    self._oprot.writeMessageEnd()
    self._oprot.trans.flush()

# Node: ReadPost_args
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

# Node: ReadPost_result
def send_ReadPosts(self, req_id, post_ids, carrier):
    self._oprot.writeMessageBegin('ReadPosts', TMessageType.CALL, self._seqid)
    args = ReadPosts_args()
    args.req_id = req_id
    args.post_ids = post_ids
    args.carrier = carrier
    args.write(self._oprot)
    self._oprot.writeMessageEnd()
    self._oprot.trans.flush()

# Node: ReadPosts_args
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

# Node: ReadPosts_result
class Processor(Iface, TProcessor):

    def __init__(self, handler):
        self._handler = handler
        self._processMap = {}
        self._processMap['StorePost'] = Processor.process_StorePost
        self._processMap['ReadPost'] = Processor.process_ReadPost
        self._processMap['ReadPosts'] = Processor.process_ReadPosts
        self._on_message_begin = None

    def on_message_begin(self, func):
        self._on_message_begin = func

    def process(self, iprot, oprot):
        name, type, seqid = iprot.readMessageBegin()
        if self._on_message_begin:
            self._on_message_begin(name, type, seqid)
        if name not in self._processMap:
            iprot.skip(TType.STRUCT)
            iprot.readMessageEnd()
            x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
            oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
            x.write(oprot)
            oprot.writeMessageEnd()
            oprot.trans.flush()
            return
        else:
            self._processMap[name](self, seqid, iprot, oprot)
        return True

    def process_StorePost(self, seqid, iprot, oprot):
        args = StorePost_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = StorePost_result()
        try:
            self._handler.StorePost(args.req_id, args.post, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('StorePost', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

    def process_ReadPost(self, seqid, iprot, oprot):
        args = ReadPost_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = ReadPost_result()
        try:
            result.success = self._handler.ReadPost(args.req_id, args.post_id, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('ReadPost', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

    def process_ReadPosts(self, seqid, iprot, oprot):
        args = ReadPosts_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = ReadPosts_result()
        try:
            result.success = self._handler.ReadPosts(args.req_id, args.post_ids, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('ReadPosts', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

def process(self, iprot, oprot):
    name, type, seqid = iprot.readMessageBegin()
    if self._on_message_begin:
        self._on_message_begin(name, type, seqid)
    if name not in self._processMap:
        iprot.skip(TType.STRUCT)
        iprot.readMessageEnd()
        x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
        oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
        x.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()
        return
    else:
        self._processMap[name](self, seqid, iprot, oprot)
    return True

def process_StorePost(self, seqid, iprot, oprot):
    args = StorePost_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = StorePost_result()
    try:
        self._handler.StorePost(args.req_id, args.post, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('StorePost', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

def process_ReadPost(self, seqid, iprot, oprot):
    args = ReadPost_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = ReadPost_result()
    try:
        result.success = self._handler.ReadPost(args.req_id, args.post_id, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('ReadPost', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

def process_ReadPosts(self, seqid, iprot, oprot):
    args = ReadPosts_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = ReadPosts_result()
    try:
        result.success = self._handler.ReadPosts(args.req_id, args.post_ids, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('ReadPosts', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

class Client(Iface):

    def __init__(self, iprot, oprot=None):
        self._iprot = self._oprot = iprot
        if oprot is not None:
            self._oprot = oprot
        self._seqid = 0

    def GetFollowers(self, req_id, user_id, carrier):
        """
        Parameters:
         - req_id
         - user_id
         - carrier

        """
        self.send_GetFollowers(req_id, user_id, carrier)
        return self.recv_GetFollowers()

    def send_GetFollowers(self, req_id, user_id, carrier):
        self._oprot.writeMessageBegin('GetFollowers', TMessageType.CALL, self._seqid)
        args = GetFollowers_args()
        args.req_id = req_id
        args.user_id = user_id
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_GetFollowers(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = GetFollowers_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.success is not None:
            return result.success
        if result.se is not None:
            raise result.se
        raise TApplicationException(TApplicationException.MISSING_RESULT, 'GetFollowers failed: unknown result')

    def GetFollowees(self, req_id, user_id, carrier):
        """
        Parameters:
         - req_id
         - user_id
         - carrier

        """
        self.send_GetFollowees(req_id, user_id, carrier)
        return self.recv_GetFollowees()

    def send_GetFollowees(self, req_id, user_id, carrier):
        self._oprot.writeMessageBegin('GetFollowees', TMessageType.CALL, self._seqid)
        args = GetFollowees_args()
        args.req_id = req_id
        args.user_id = user_id
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_GetFollowees(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = GetFollowees_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.success is not None:
            return result.success
        if result.se is not None:
            raise result.se
        raise TApplicationException(TApplicationException.MISSING_RESULT, 'GetFollowees failed: unknown result')

    def Follow(self, req_id, user_id, followee_id, carrier):
        """
        Parameters:
         - req_id
         - user_id
         - followee_id
         - carrier

        """
        self.send_Follow(req_id, user_id, followee_id, carrier)
        self.recv_Follow()

    def send_Follow(self, req_id, user_id, followee_id, carrier):
        self._oprot.writeMessageBegin('Follow', TMessageType.CALL, self._seqid)
        args = Follow_args()
        args.req_id = req_id
        args.user_id = user_id
        args.followee_id = followee_id
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_Follow(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = Follow_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.se is not None:
            raise result.se
        return

    def Unfollow(self, req_id, user_id, followee_id, carrier):
        """
        Parameters:
         - req_id
         - user_id
         - followee_id
         - carrier

        """
        self.send_Unfollow(req_id, user_id, followee_id, carrier)
        self.recv_Unfollow()

    def send_Unfollow(self, req_id, user_id, followee_id, carrier):
        self._oprot.writeMessageBegin('Unfollow', TMessageType.CALL, self._seqid)
        args = Unfollow_args()
        args.req_id = req_id
        args.user_id = user_id
        args.followee_id = followee_id
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_Unfollow(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = Unfollow_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.se is not None:
            raise result.se
        return

    def FollowWithUsername(self, req_id, user_usernmae, followee_username, carrier):
        """
        Parameters:
         - req_id
         - user_usernmae
         - followee_username
         - carrier

        """
        self.send_FollowWithUsername(req_id, user_usernmae, followee_username, carrier)
        self.recv_FollowWithUsername()

    def send_FollowWithUsername(self, req_id, user_usernmae, followee_username, carrier):
        self._oprot.writeMessageBegin('FollowWithUsername', TMessageType.CALL, self._seqid)
        args = FollowWithUsername_args()
        args.req_id = req_id
        args.user_usernmae = user_usernmae
        args.followee_username = followee_username
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_FollowWithUsername(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = FollowWithUsername_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.se is not None:
            raise result.se
        return

    def UnfollowWithUsername(self, req_id, user_usernmae, followee_username, carrier):
        """
        Parameters:
         - req_id
         - user_usernmae
         - followee_username
         - carrier

        """
        self.send_UnfollowWithUsername(req_id, user_usernmae, followee_username, carrier)
        self.recv_UnfollowWithUsername()

    def send_UnfollowWithUsername(self, req_id, user_usernmae, followee_username, carrier):
        self._oprot.writeMessageBegin('UnfollowWithUsername', TMessageType.CALL, self._seqid)
        args = UnfollowWithUsername_args()
        args.req_id = req_id
        args.user_usernmae = user_usernmae
        args.followee_username = followee_username
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_UnfollowWithUsername(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = UnfollowWithUsername_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.se is not None:
            raise result.se
        return

    def InsertUser(self, req_id, user_id, carrier):
        """
        Parameters:
         - req_id
         - user_id
         - carrier

        """
        self.send_InsertUser(req_id, user_id, carrier)
        self.recv_InsertUser()

    def send_InsertUser(self, req_id, user_id, carrier):
        self._oprot.writeMessageBegin('InsertUser', TMessageType.CALL, self._seqid)
        args = InsertUser_args()
        args.req_id = req_id
        args.user_id = user_id
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_InsertUser(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = InsertUser_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.se is not None:
            raise result.se
        return

def send_GetFollowers(self, req_id, user_id, carrier):
    self._oprot.writeMessageBegin('GetFollowers', TMessageType.CALL, self._seqid)
    args = GetFollowers_args()
    args.req_id = req_id
    args.user_id = user_id
    args.carrier = carrier
    args.write(self._oprot)
    self._oprot.writeMessageEnd()
    self._oprot.trans.flush()

# Node: GetFollowers_args
def recv_GetFollowers(self):
    iprot = self._iprot
    fname, mtype, rseqid = iprot.readMessageBegin()
    if mtype == TMessageType.EXCEPTION:
        x = TApplicationException()
        x.read(iprot)
        iprot.readMessageEnd()
        raise x
    result = GetFollowers_result()
    result.read(iprot)
    iprot.readMessageEnd()
    if result.success is not None:
        return result.success
    if result.se is not None:
        raise result.se
    raise TApplicationException(TApplicationException.MISSING_RESULT, 'GetFollowers failed: unknown result')

# Node: GetFollowers_result
def send_GetFollowees(self, req_id, user_id, carrier):
    self._oprot.writeMessageBegin('GetFollowees', TMessageType.CALL, self._seqid)
    args = GetFollowees_args()
    args.req_id = req_id
    args.user_id = user_id
    args.carrier = carrier
    args.write(self._oprot)
    self._oprot.writeMessageEnd()
    self._oprot.trans.flush()

# Node: GetFollowees_args
def recv_GetFollowees(self):
    iprot = self._iprot
    fname, mtype, rseqid = iprot.readMessageBegin()
    if mtype == TMessageType.EXCEPTION:
        x = TApplicationException()
        x.read(iprot)
        iprot.readMessageEnd()
        raise x
    result = GetFollowees_result()
    result.read(iprot)
    iprot.readMessageEnd()
    if result.success is not None:
        return result.success
    if result.se is not None:
        raise result.se
    raise TApplicationException(TApplicationException.MISSING_RESULT, 'GetFollowees failed: unknown result')

# Node: GetFollowees_result
def send_Follow(self, req_id, user_id, followee_id, carrier):
    self._oprot.writeMessageBegin('Follow', TMessageType.CALL, self._seqid)
    args = Follow_args()
    args.req_id = req_id
    args.user_id = user_id
    args.followee_id = followee_id
    args.carrier = carrier
    args.write(self._oprot)
    self._oprot.writeMessageEnd()
    self._oprot.trans.flush()

# Node: Follow_args
def recv_Follow(self):
    iprot = self._iprot
    fname, mtype, rseqid = iprot.readMessageBegin()
    if mtype == TMessageType.EXCEPTION:
        x = TApplicationException()
        x.read(iprot)
        iprot.readMessageEnd()
        raise x
    result = Follow_result()
    result.read(iprot)
    iprot.readMessageEnd()
    if result.se is not None:
        raise result.se
    return

# Node: Follow_result
def send_Unfollow(self, req_id, user_id, followee_id, carrier):
    self._oprot.writeMessageBegin('Unfollow', TMessageType.CALL, self._seqid)
    args = Unfollow_args()
    args.req_id = req_id
    args.user_id = user_id
    args.followee_id = followee_id
    args.carrier = carrier
    args.write(self._oprot)
    self._oprot.writeMessageEnd()
    self._oprot.trans.flush()

# Node: Unfollow_args
def recv_Unfollow(self):
    iprot = self._iprot
    fname, mtype, rseqid = iprot.readMessageBegin()
    if mtype == TMessageType.EXCEPTION:
        x = TApplicationException()
        x.read(iprot)
        iprot.readMessageEnd()
        raise x
    result = Unfollow_result()
    result.read(iprot)
    iprot.readMessageEnd()
    if result.se is not None:
        raise result.se
    return

# Node: Unfollow_result
def send_FollowWithUsername(self, req_id, user_usernmae, followee_username, carrier):
    self._oprot.writeMessageBegin('FollowWithUsername', TMessageType.CALL, self._seqid)
    args = FollowWithUsername_args()
    args.req_id = req_id
    args.user_usernmae = user_usernmae
    args.followee_username = followee_username
    args.carrier = carrier
    args.write(self._oprot)
    self._oprot.writeMessageEnd()
    self._oprot.trans.flush()

# Node: FollowWithUsername_args
def recv_FollowWithUsername(self):
    iprot = self._iprot
    fname, mtype, rseqid = iprot.readMessageBegin()
    if mtype == TMessageType.EXCEPTION:
        x = TApplicationException()
        x.read(iprot)
        iprot.readMessageEnd()
        raise x
    result = FollowWithUsername_result()
    result.read(iprot)
    iprot.readMessageEnd()
    if result.se is not None:
        raise result.se
    return

# Node: FollowWithUsername_result
def send_UnfollowWithUsername(self, req_id, user_usernmae, followee_username, carrier):
    self._oprot.writeMessageBegin('UnfollowWithUsername', TMessageType.CALL, self._seqid)
    args = UnfollowWithUsername_args()
    args.req_id = req_id
    args.user_usernmae = user_usernmae
    args.followee_username = followee_username
    args.carrier = carrier
    args.write(self._oprot)
    self._oprot.writeMessageEnd()
    self._oprot.trans.flush()

# Node: UnfollowWithUsername_args
def recv_UnfollowWithUsername(self):
    iprot = self._iprot
    fname, mtype, rseqid = iprot.readMessageBegin()
    if mtype == TMessageType.EXCEPTION:
        x = TApplicationException()
        x.read(iprot)
        iprot.readMessageEnd()
        raise x
    result = UnfollowWithUsername_result()
    result.read(iprot)
    iprot.readMessageEnd()
    if result.se is not None:
        raise result.se
    return

# Node: UnfollowWithUsername_result
def send_InsertUser(self, req_id, user_id, carrier):
    self._oprot.writeMessageBegin('InsertUser', TMessageType.CALL, self._seqid)
    args = InsertUser_args()
    args.req_id = req_id
    args.user_id = user_id
    args.carrier = carrier
    args.write(self._oprot)
    self._oprot.writeMessageEnd()
    self._oprot.trans.flush()

# Node: InsertUser_args
def recv_InsertUser(self):
    iprot = self._iprot
    fname, mtype, rseqid = iprot.readMessageBegin()
    if mtype == TMessageType.EXCEPTION:
        x = TApplicationException()
        x.read(iprot)
        iprot.readMessageEnd()
        raise x
    result = InsertUser_result()
    result.read(iprot)
    iprot.readMessageEnd()
    if result.se is not None:
        raise result.se
    return

# Node: InsertUser_result
class Processor(Iface, TProcessor):

    def __init__(self, handler):
        self._handler = handler
        self._processMap = {}
        self._processMap['GetFollowers'] = Processor.process_GetFollowers
        self._processMap['GetFollowees'] = Processor.process_GetFollowees
        self._processMap['Follow'] = Processor.process_Follow
        self._processMap['Unfollow'] = Processor.process_Unfollow
        self._processMap['FollowWithUsername'] = Processor.process_FollowWithUsername
        self._processMap['UnfollowWithUsername'] = Processor.process_UnfollowWithUsername
        self._processMap['InsertUser'] = Processor.process_InsertUser
        self._on_message_begin = None

    def on_message_begin(self, func):
        self._on_message_begin = func

    def process(self, iprot, oprot):
        name, type, seqid = iprot.readMessageBegin()
        if self._on_message_begin:
            self._on_message_begin(name, type, seqid)
        if name not in self._processMap:
            iprot.skip(TType.STRUCT)
            iprot.readMessageEnd()
            x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
            oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
            x.write(oprot)
            oprot.writeMessageEnd()
            oprot.trans.flush()
            return
        else:
            self._processMap[name](self, seqid, iprot, oprot)
        return True

    def process_GetFollowers(self, seqid, iprot, oprot):
        args = GetFollowers_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = GetFollowers_result()
        try:
            result.success = self._handler.GetFollowers(args.req_id, args.user_id, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('GetFollowers', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

    def process_GetFollowees(self, seqid, iprot, oprot):
        args = GetFollowees_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = GetFollowees_result()
        try:
            result.success = self._handler.GetFollowees(args.req_id, args.user_id, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('GetFollowees', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

    def process_Follow(self, seqid, iprot, oprot):
        args = Follow_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = Follow_result()
        try:
            self._handler.Follow(args.req_id, args.user_id, args.followee_id, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('Follow', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

    def process_Unfollow(self, seqid, iprot, oprot):
        args = Unfollow_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = Unfollow_result()
        try:
            self._handler.Unfollow(args.req_id, args.user_id, args.followee_id, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('Unfollow', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

    def process_FollowWithUsername(self, seqid, iprot, oprot):
        args = FollowWithUsername_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = FollowWithUsername_result()
        try:
            self._handler.FollowWithUsername(args.req_id, args.user_usernmae, args.followee_username, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('FollowWithUsername', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

    def process_UnfollowWithUsername(self, seqid, iprot, oprot):
        args = UnfollowWithUsername_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = UnfollowWithUsername_result()
        try:
            self._handler.UnfollowWithUsername(args.req_id, args.user_usernmae, args.followee_username, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('UnfollowWithUsername', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

    def process_InsertUser(self, seqid, iprot, oprot):
        args = InsertUser_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = InsertUser_result()
        try:
            self._handler.InsertUser(args.req_id, args.user_id, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('InsertUser', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

def process(self, iprot, oprot):
    name, type, seqid = iprot.readMessageBegin()
    if self._on_message_begin:
        self._on_message_begin(name, type, seqid)
    if name not in self._processMap:
        iprot.skip(TType.STRUCT)
        iprot.readMessageEnd()
        x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
        oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
        x.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()
        return
    else:
        self._processMap[name](self, seqid, iprot, oprot)
    return True

def process_GetFollowers(self, seqid, iprot, oprot):
    args = GetFollowers_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = GetFollowers_result()
    try:
        result.success = self._handler.GetFollowers(args.req_id, args.user_id, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('GetFollowers', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

def process_GetFollowees(self, seqid, iprot, oprot):
    args = GetFollowees_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = GetFollowees_result()
    try:
        result.success = self._handler.GetFollowees(args.req_id, args.user_id, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('GetFollowees', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

def process_Follow(self, seqid, iprot, oprot):
    args = Follow_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = Follow_result()
    try:
        self._handler.Follow(args.req_id, args.user_id, args.followee_id, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('Follow', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

def process_Unfollow(self, seqid, iprot, oprot):
    args = Unfollow_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = Unfollow_result()
    try:
        self._handler.Unfollow(args.req_id, args.user_id, args.followee_id, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('Unfollow', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

def process_FollowWithUsername(self, seqid, iprot, oprot):
    args = FollowWithUsername_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = FollowWithUsername_result()
    try:
        self._handler.FollowWithUsername(args.req_id, args.user_usernmae, args.followee_username, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('FollowWithUsername', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

# Node: FollowWithUsername
def process_UnfollowWithUsername(self, seqid, iprot, oprot):
    args = UnfollowWithUsername_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = UnfollowWithUsername_result()
    try:
        self._handler.UnfollowWithUsername(args.req_id, args.user_usernmae, args.followee_username, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('UnfollowWithUsername', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

# Node: UnfollowWithUsername
def process_InsertUser(self, seqid, iprot, oprot):
    args = InsertUser_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = InsertUser_result()
    try:
        self._handler.InsertUser(args.req_id, args.user_id, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('InsertUser', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

# Node: InsertUser
class Client(Iface):

    def __init__(self, iprot, oprot=None):
        self._iprot = self._oprot = iprot
        if oprot is not None:
            self._oprot = oprot
        self._seqid = 0

    def RegisterUser(self, req_id, first_name, last_name, username, password, carrier):
        """
        Parameters:
         - req_id
         - first_name
         - last_name
         - username
         - password
         - carrier

        """
        self.send_RegisterUser(req_id, first_name, last_name, username, password, carrier)
        self.recv_RegisterUser()

    def send_RegisterUser(self, req_id, first_name, last_name, username, password, carrier):
        self._oprot.writeMessageBegin('RegisterUser', TMessageType.CALL, self._seqid)
        args = RegisterUser_args()
        args.req_id = req_id
        args.first_name = first_name
        args.last_name = last_name
        args.username = username
        args.password = password
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_RegisterUser(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = RegisterUser_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.se is not None:
            raise result.se
        return

    def RegisterUserWithId(self, req_id, first_name, last_name, username, password, user_id, carrier):
        """
        Parameters:
         - req_id
         - first_name
         - last_name
         - username
         - password
         - user_id
         - carrier

        """
        self.send_RegisterUserWithId(req_id, first_name, last_name, username, password, user_id, carrier)
        self.recv_RegisterUserWithId()

    def send_RegisterUserWithId(self, req_id, first_name, last_name, username, password, user_id, carrier):
        self._oprot.writeMessageBegin('RegisterUserWithId', TMessageType.CALL, self._seqid)
        args = RegisterUserWithId_args()
        args.req_id = req_id
        args.first_name = first_name
        args.last_name = last_name
        args.username = username
        args.password = password
        args.user_id = user_id
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_RegisterUserWithId(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = RegisterUserWithId_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.se is not None:
            raise result.se
        return

    def Login(self, req_id, username, password, carrier):
        """
        Parameters:
         - req_id
         - username
         - password
         - carrier

        """
        self.send_Login(req_id, username, password, carrier)
        return self.recv_Login()

    def send_Login(self, req_id, username, password, carrier):
        self._oprot.writeMessageBegin('Login', TMessageType.CALL, self._seqid)
        args = Login_args()
        args.req_id = req_id
        args.username = username
        args.password = password
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_Login(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = Login_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.success is not None:
            return result.success
        if result.se is not None:
            raise result.se
        raise TApplicationException(TApplicationException.MISSING_RESULT, 'Login failed: unknown result')

    def ComposeCreatorWithUserId(self, req_id, user_id, username, carrier):
        """
        Parameters:
         - req_id
         - user_id
         - username
         - carrier

        """
        self.send_ComposeCreatorWithUserId(req_id, user_id, username, carrier)
        return self.recv_ComposeCreatorWithUserId()

    def send_ComposeCreatorWithUserId(self, req_id, user_id, username, carrier):
        self._oprot.writeMessageBegin('ComposeCreatorWithUserId', TMessageType.CALL, self._seqid)
        args = ComposeCreatorWithUserId_args()
        args.req_id = req_id
        args.user_id = user_id
        args.username = username
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_ComposeCreatorWithUserId(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = ComposeCreatorWithUserId_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.success is not None:
            return result.success
        if result.se is not None:
            raise result.se
        raise TApplicationException(TApplicationException.MISSING_RESULT, 'ComposeCreatorWithUserId failed: unknown result')

    def ComposeCreatorWithUsername(self, req_id, username, carrier):
        """
        Parameters:
         - req_id
         - username
         - carrier

        """
        self.send_ComposeCreatorWithUsername(req_id, username, carrier)
        return self.recv_ComposeCreatorWithUsername()

    def send_ComposeCreatorWithUsername(self, req_id, username, carrier):
        self._oprot.writeMessageBegin('ComposeCreatorWithUsername', TMessageType.CALL, self._seqid)
        args = ComposeCreatorWithUsername_args()
        args.req_id = req_id
        args.username = username
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_ComposeCreatorWithUsername(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = ComposeCreatorWithUsername_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.success is not None:
            return result.success
        if result.se is not None:
            raise result.se
        raise TApplicationException(TApplicationException.MISSING_RESULT, 'ComposeCreatorWithUsername failed: unknown result')

    def GetUserId(self, req_id, username, carrier):
        """
        Parameters:
         - req_id
         - username
         - carrier

        """
        self.send_GetUserId(req_id, username, carrier)
        return self.recv_GetUserId()

    def send_GetUserId(self, req_id, username, carrier):
        self._oprot.writeMessageBegin('GetUserId', TMessageType.CALL, self._seqid)
        args = GetUserId_args()
        args.req_id = req_id
        args.username = username
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_GetUserId(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = GetUserId_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.success is not None:
            return result.success
        if result.se is not None:
            raise result.se
        raise TApplicationException(TApplicationException.MISSING_RESULT, 'GetUserId failed: unknown result')

def send_RegisterUser(self, req_id, first_name, last_name, username, password, carrier):
    self._oprot.writeMessageBegin('RegisterUser', TMessageType.CALL, self._seqid)
    args = RegisterUser_args()
    args.req_id = req_id
    args.first_name = first_name
    args.last_name = last_name
    args.username = username
    args.password = password
    args.carrier = carrier
    args.write(self._oprot)
    self._oprot.writeMessageEnd()
    self._oprot.trans.flush()

def recv_RegisterUser(self):
    iprot = self._iprot
    fname, mtype, rseqid = iprot.readMessageBegin()
    if mtype == TMessageType.EXCEPTION:
        x = TApplicationException()
        x.read(iprot)
        iprot.readMessageEnd()
        raise x
    result = RegisterUser_result()
    result.read(iprot)
    iprot.readMessageEnd()
    if result.se is not None:
        raise result.se
    return

def send_RegisterUserWithId(self, req_id, first_name, last_name, username, password, user_id, carrier):
    self._oprot.writeMessageBegin('RegisterUserWithId', TMessageType.CALL, self._seqid)
    args = RegisterUserWithId_args()
    args.req_id = req_id
    args.first_name = first_name
    args.last_name = last_name
    args.username = username
    args.password = password
    args.user_id = user_id
    args.carrier = carrier
    args.write(self._oprot)
    self._oprot.writeMessageEnd()
    self._oprot.trans.flush()

def recv_RegisterUserWithId(self):
    iprot = self._iprot
    fname, mtype, rseqid = iprot.readMessageBegin()
    if mtype == TMessageType.EXCEPTION:
        x = TApplicationException()
        x.read(iprot)
        iprot.readMessageEnd()
        raise x
    result = RegisterUserWithId_result()
    result.read(iprot)
    iprot.readMessageEnd()
    if result.se is not None:
        raise result.se
    return

def send_Login(self, req_id, username, password, carrier):
    self._oprot.writeMessageBegin('Login', TMessageType.CALL, self._seqid)
    args = Login_args()
    args.req_id = req_id
    args.username = username
    args.password = password
    args.carrier = carrier
    args.write(self._oprot)
    self._oprot.writeMessageEnd()
    self._oprot.trans.flush()

def recv_Login(self):
    iprot = self._iprot
    fname, mtype, rseqid = iprot.readMessageBegin()
    if mtype == TMessageType.EXCEPTION:
        x = TApplicationException()
        x.read(iprot)
        iprot.readMessageEnd()
        raise x
    result = Login_result()
    result.read(iprot)
    iprot.readMessageEnd()
    if result.success is not None:
        return result.success
    if result.se is not None:
        raise result.se
    raise TApplicationException(TApplicationException.MISSING_RESULT, 'Login failed: unknown result')

def send_ComposeCreatorWithUserId(self, req_id, user_id, username, carrier):
    self._oprot.writeMessageBegin('ComposeCreatorWithUserId', TMessageType.CALL, self._seqid)
    args = ComposeCreatorWithUserId_args()
    args.req_id = req_id
    args.user_id = user_id
    args.username = username
    args.carrier = carrier
    args.write(self._oprot)
    self._oprot.writeMessageEnd()
    self._oprot.trans.flush()

# Node: ComposeCreatorWithUserId_args
def recv_ComposeCreatorWithUserId(self):
    iprot = self._iprot
    fname, mtype, rseqid = iprot.readMessageBegin()
    if mtype == TMessageType.EXCEPTION:
        x = TApplicationException()
        x.read(iprot)
        iprot.readMessageEnd()
        raise x
    result = ComposeCreatorWithUserId_result()
    result.read(iprot)
    iprot.readMessageEnd()
    if result.success is not None:
        return result.success
    if result.se is not None:
        raise result.se
    raise TApplicationException(TApplicationException.MISSING_RESULT, 'ComposeCreatorWithUserId failed: unknown result')

# Node: ComposeCreatorWithUserId_result
def send_ComposeCreatorWithUsername(self, req_id, username, carrier):
    self._oprot.writeMessageBegin('ComposeCreatorWithUsername', TMessageType.CALL, self._seqid)
    args = ComposeCreatorWithUsername_args()
    args.req_id = req_id
    args.username = username
    args.carrier = carrier
    args.write(self._oprot)
    self._oprot.writeMessageEnd()
    self._oprot.trans.flush()

# Node: ComposeCreatorWithUsername_args
def recv_ComposeCreatorWithUsername(self):
    iprot = self._iprot
    fname, mtype, rseqid = iprot.readMessageBegin()
    if mtype == TMessageType.EXCEPTION:
        x = TApplicationException()
        x.read(iprot)
        iprot.readMessageEnd()
        raise x
    result = ComposeCreatorWithUsername_result()
    result.read(iprot)
    iprot.readMessageEnd()
    if result.success is not None:
        return result.success
    if result.se is not None:
        raise result.se
    raise TApplicationException(TApplicationException.MISSING_RESULT, 'ComposeCreatorWithUsername failed: unknown result')

# Node: ComposeCreatorWithUsername_result
def send_GetUserId(self, req_id, username, carrier):
    self._oprot.writeMessageBegin('GetUserId', TMessageType.CALL, self._seqid)
    args = GetUserId_args()
    args.req_id = req_id
    args.username = username
    args.carrier = carrier
    args.write(self._oprot)
    self._oprot.writeMessageEnd()
    self._oprot.trans.flush()

# Node: GetUserId_args
def recv_GetUserId(self):
    iprot = self._iprot
    fname, mtype, rseqid = iprot.readMessageBegin()
    if mtype == TMessageType.EXCEPTION:
        x = TApplicationException()
        x.read(iprot)
        iprot.readMessageEnd()
        raise x
    result = GetUserId_result()
    result.read(iprot)
    iprot.readMessageEnd()
    if result.success is not None:
        return result.success
    if result.se is not None:
        raise result.se
    raise TApplicationException(TApplicationException.MISSING_RESULT, 'GetUserId failed: unknown result')

# Node: GetUserId_result
class Processor(Iface, TProcessor):

    def __init__(self, handler):
        self._handler = handler
        self._processMap = {}
        self._processMap['RegisterUser'] = Processor.process_RegisterUser
        self._processMap['RegisterUserWithId'] = Processor.process_RegisterUserWithId
        self._processMap['Login'] = Processor.process_Login
        self._processMap['ComposeCreatorWithUserId'] = Processor.process_ComposeCreatorWithUserId
        self._processMap['ComposeCreatorWithUsername'] = Processor.process_ComposeCreatorWithUsername
        self._processMap['GetUserId'] = Processor.process_GetUserId
        self._on_message_begin = None

    def on_message_begin(self, func):
        self._on_message_begin = func

    def process(self, iprot, oprot):
        name, type, seqid = iprot.readMessageBegin()
        if self._on_message_begin:
            self._on_message_begin(name, type, seqid)
        if name not in self._processMap:
            iprot.skip(TType.STRUCT)
            iprot.readMessageEnd()
            x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
            oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
            x.write(oprot)
            oprot.writeMessageEnd()
            oprot.trans.flush()
            return
        else:
            self._processMap[name](self, seqid, iprot, oprot)
        return True

    def process_RegisterUser(self, seqid, iprot, oprot):
        args = RegisterUser_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = RegisterUser_result()
        try:
            self._handler.RegisterUser(args.req_id, args.first_name, args.last_name, args.username, args.password, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('RegisterUser', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

    def process_RegisterUserWithId(self, seqid, iprot, oprot):
        args = RegisterUserWithId_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = RegisterUserWithId_result()
        try:
            self._handler.RegisterUserWithId(args.req_id, args.first_name, args.last_name, args.username, args.password, args.user_id, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('RegisterUserWithId', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

    def process_Login(self, seqid, iprot, oprot):
        args = Login_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = Login_result()
        try:
            result.success = self._handler.Login(args.req_id, args.username, args.password, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('Login', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

    def process_ComposeCreatorWithUserId(self, seqid, iprot, oprot):
        args = ComposeCreatorWithUserId_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = ComposeCreatorWithUserId_result()
        try:
            result.success = self._handler.ComposeCreatorWithUserId(args.req_id, args.user_id, args.username, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('ComposeCreatorWithUserId', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

    def process_ComposeCreatorWithUsername(self, seqid, iprot, oprot):
        args = ComposeCreatorWithUsername_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = ComposeCreatorWithUsername_result()
        try:
            result.success = self._handler.ComposeCreatorWithUsername(args.req_id, args.username, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('ComposeCreatorWithUsername', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

    def process_GetUserId(self, seqid, iprot, oprot):
        args = GetUserId_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = GetUserId_result()
        try:
            result.success = self._handler.GetUserId(args.req_id, args.username, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('GetUserId', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

def process(self, iprot, oprot):
    name, type, seqid = iprot.readMessageBegin()
    if self._on_message_begin:
        self._on_message_begin(name, type, seqid)
    if name not in self._processMap:
        iprot.skip(TType.STRUCT)
        iprot.readMessageEnd()
        x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
        oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
        x.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()
        return
    else:
        self._processMap[name](self, seqid, iprot, oprot)
    return True

def process_RegisterUser(self, seqid, iprot, oprot):
    args = RegisterUser_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = RegisterUser_result()
    try:
        self._handler.RegisterUser(args.req_id, args.first_name, args.last_name, args.username, args.password, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('RegisterUser', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

def process_RegisterUserWithId(self, seqid, iprot, oprot):
    args = RegisterUserWithId_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = RegisterUserWithId_result()
    try:
        self._handler.RegisterUserWithId(args.req_id, args.first_name, args.last_name, args.username, args.password, args.user_id, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('RegisterUserWithId', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

def process_Login(self, seqid, iprot, oprot):
    args = Login_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = Login_result()
    try:
        result.success = self._handler.Login(args.req_id, args.username, args.password, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('Login', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

def process_ComposeCreatorWithUserId(self, seqid, iprot, oprot):
    args = ComposeCreatorWithUserId_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = ComposeCreatorWithUserId_result()
    try:
        result.success = self._handler.ComposeCreatorWithUserId(args.req_id, args.user_id, args.username, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('ComposeCreatorWithUserId', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

# Node: ComposeCreatorWithUserId
def process_ComposeCreatorWithUsername(self, seqid, iprot, oprot):
    args = ComposeCreatorWithUsername_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = ComposeCreatorWithUsername_result()
    try:
        result.success = self._handler.ComposeCreatorWithUsername(args.req_id, args.username, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('ComposeCreatorWithUsername', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

# Node: ComposeCreatorWithUsername
def process_GetUserId(self, seqid, iprot, oprot):
    args = GetUserId_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = GetUserId_result()
    try:
        result.success = self._handler.GetUserId(args.req_id, args.username, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('GetUserId', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

# Node: GetUserId
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

# Node: ComposePost_args
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

# Node: ComposePost_result
class Processor(Iface, TProcessor):

    def __init__(self, handler):
        self._handler = handler
        self._processMap = {}
        self._processMap['ComposePost'] = Processor.process_ComposePost
        self._on_message_begin = None

    def on_message_begin(self, func):
        self._on_message_begin = func

    def process(self, iprot, oprot):
        name, type, seqid = iprot.readMessageBegin()
        if self._on_message_begin:
            self._on_message_begin(name, type, seqid)
        if name not in self._processMap:
            iprot.skip(TType.STRUCT)
            iprot.readMessageEnd()
            x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
            oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
            x.write(oprot)
            oprot.writeMessageEnd()
            oprot.trans.flush()
            return
        else:
            self._processMap[name](self, seqid, iprot, oprot)
        return True

    def process_ComposePost(self, seqid, iprot, oprot):
        args = ComposePost_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = ComposePost_result()
        try:
            self._handler.ComposePost(args.req_id, args.username, args.user_id, args.text, args.media_ids, args.media_types, args.post_type, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('ComposePost', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

def process(self, iprot, oprot):
    name, type, seqid = iprot.readMessageBegin()
    if self._on_message_begin:
        self._on_message_begin(name, type, seqid)
    if name not in self._processMap:
        iprot.skip(TType.STRUCT)
        iprot.readMessageEnd()
        x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
        oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
        x.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()
        return
    else:
        self._processMap[name](self, seqid, iprot, oprot)
    return True

def process_ComposePost(self, seqid, iprot, oprot):
    args = ComposePost_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = ComposePost_result()
    try:
        self._handler.ComposePost(args.req_id, args.username, args.user_id, args.text, args.media_ids, args.media_types, args.post_type, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('ComposePost', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

# Node: ComposePost
class Client(Iface):

    def __init__(self, iprot, oprot=None):
        self._iprot = self._oprot = iprot
        if oprot is not None:
            self._oprot = oprot
        self._seqid = 0

    def WriteUserTimeline(self, req_id, post_id, user_id, timestamp, carrier):
        """
        Parameters:
         - req_id
         - post_id
         - user_id
         - timestamp
         - carrier

        """
        self.send_WriteUserTimeline(req_id, post_id, user_id, timestamp, carrier)
        self.recv_WriteUserTimeline()

    def send_WriteUserTimeline(self, req_id, post_id, user_id, timestamp, carrier):
        self._oprot.writeMessageBegin('WriteUserTimeline', TMessageType.CALL, self._seqid)
        args = WriteUserTimeline_args()
        args.req_id = req_id
        args.post_id = post_id
        args.user_id = user_id
        args.timestamp = timestamp
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_WriteUserTimeline(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = WriteUserTimeline_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.se is not None:
            raise result.se
        return

    def ReadUserTimeline(self, req_id, user_id, start, stop, carrier):
        """
        Parameters:
         - req_id
         - user_id
         - start
         - stop
         - carrier

        """
        self.send_ReadUserTimeline(req_id, user_id, start, stop, carrier)
        return self.recv_ReadUserTimeline()

    def send_ReadUserTimeline(self, req_id, user_id, start, stop, carrier):
        self._oprot.writeMessageBegin('ReadUserTimeline', TMessageType.CALL, self._seqid)
        args = ReadUserTimeline_args()
        args.req_id = req_id
        args.user_id = user_id
        args.start = start
        args.stop = stop
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_ReadUserTimeline(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = ReadUserTimeline_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.success is not None:
            return result.success
        if result.se is not None:
            raise result.se
        raise TApplicationException(TApplicationException.MISSING_RESULT, 'ReadUserTimeline failed: unknown result')

def send_WriteUserTimeline(self, req_id, post_id, user_id, timestamp, carrier):
    self._oprot.writeMessageBegin('WriteUserTimeline', TMessageType.CALL, self._seqid)
    args = WriteUserTimeline_args()
    args.req_id = req_id
    args.post_id = post_id
    args.user_id = user_id
    args.timestamp = timestamp
    args.carrier = carrier
    args.write(self._oprot)
    self._oprot.writeMessageEnd()
    self._oprot.trans.flush()

# Node: WriteUserTimeline_args
def recv_WriteUserTimeline(self):
    iprot = self._iprot
    fname, mtype, rseqid = iprot.readMessageBegin()
    if mtype == TMessageType.EXCEPTION:
        x = TApplicationException()
        x.read(iprot)
        iprot.readMessageEnd()
        raise x
    result = WriteUserTimeline_result()
    result.read(iprot)
    iprot.readMessageEnd()
    if result.se is not None:
        raise result.se
    return

# Node: WriteUserTimeline_result
def send_ReadUserTimeline(self, req_id, user_id, start, stop, carrier):
    self._oprot.writeMessageBegin('ReadUserTimeline', TMessageType.CALL, self._seqid)
    args = ReadUserTimeline_args()
    args.req_id = req_id
    args.user_id = user_id
    args.start = start
    args.stop = stop
    args.carrier = carrier
    args.write(self._oprot)
    self._oprot.writeMessageEnd()
    self._oprot.trans.flush()

# Node: ReadUserTimeline_args
def recv_ReadUserTimeline(self):
    iprot = self._iprot
    fname, mtype, rseqid = iprot.readMessageBegin()
    if mtype == TMessageType.EXCEPTION:
        x = TApplicationException()
        x.read(iprot)
        iprot.readMessageEnd()
        raise x
    result = ReadUserTimeline_result()
    result.read(iprot)
    iprot.readMessageEnd()
    if result.success is not None:
        return result.success
    if result.se is not None:
        raise result.se
    raise TApplicationException(TApplicationException.MISSING_RESULT, 'ReadUserTimeline failed: unknown result')

# Node: ReadUserTimeline_result
class Processor(Iface, TProcessor):

    def __init__(self, handler):
        self._handler = handler
        self._processMap = {}
        self._processMap['WriteUserTimeline'] = Processor.process_WriteUserTimeline
        self._processMap['ReadUserTimeline'] = Processor.process_ReadUserTimeline
        self._on_message_begin = None

    def on_message_begin(self, func):
        self._on_message_begin = func

    def process(self, iprot, oprot):
        name, type, seqid = iprot.readMessageBegin()
        if self._on_message_begin:
            self._on_message_begin(name, type, seqid)
        if name not in self._processMap:
            iprot.skip(TType.STRUCT)
            iprot.readMessageEnd()
            x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
            oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
            x.write(oprot)
            oprot.writeMessageEnd()
            oprot.trans.flush()
            return
        else:
            self._processMap[name](self, seqid, iprot, oprot)
        return True

    def process_WriteUserTimeline(self, seqid, iprot, oprot):
        args = WriteUserTimeline_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = WriteUserTimeline_result()
        try:
            self._handler.WriteUserTimeline(args.req_id, args.post_id, args.user_id, args.timestamp, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('WriteUserTimeline', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

    def process_ReadUserTimeline(self, seqid, iprot, oprot):
        args = ReadUserTimeline_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = ReadUserTimeline_result()
        try:
            result.success = self._handler.ReadUserTimeline(args.req_id, args.user_id, args.start, args.stop, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('ReadUserTimeline', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

def process(self, iprot, oprot):
    name, type, seqid = iprot.readMessageBegin()
    if self._on_message_begin:
        self._on_message_begin(name, type, seqid)
    if name not in self._processMap:
        iprot.skip(TType.STRUCT)
        iprot.readMessageEnd()
        x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
        oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
        x.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()
        return
    else:
        self._processMap[name](self, seqid, iprot, oprot)
    return True

def process_WriteUserTimeline(self, seqid, iprot, oprot):
    args = WriteUserTimeline_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = WriteUserTimeline_result()
    try:
        self._handler.WriteUserTimeline(args.req_id, args.post_id, args.user_id, args.timestamp, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('WriteUserTimeline', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

# Node: WriteUserTimeline
def process_ReadUserTimeline(self, seqid, iprot, oprot):
    args = ReadUserTimeline_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = ReadUserTimeline_result()
    try:
        result.success = self._handler.ReadUserTimeline(args.req_id, args.user_id, args.start, args.stop, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('ReadUserTimeline', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

class Client(Iface):

    def __init__(self, iprot, oprot=None):
        self._iprot = self._oprot = iprot
        if oprot is not None:
            self._oprot = oprot
        self._seqid = 0

    def ComposeUserMentions(self, req_id, usernames, carrier):
        """
        Parameters:
         - req_id
         - usernames
         - carrier

        """
        self.send_ComposeUserMentions(req_id, usernames, carrier)
        return self.recv_ComposeUserMentions()

    def send_ComposeUserMentions(self, req_id, usernames, carrier):
        self._oprot.writeMessageBegin('ComposeUserMentions', TMessageType.CALL, self._seqid)
        args = ComposeUserMentions_args()
        args.req_id = req_id
        args.usernames = usernames
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_ComposeUserMentions(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = ComposeUserMentions_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.success is not None:
            return result.success
        if result.se is not None:
            raise result.se
        raise TApplicationException(TApplicationException.MISSING_RESULT, 'ComposeUserMentions failed: unknown result')

def send_ComposeUserMentions(self, req_id, usernames, carrier):
    self._oprot.writeMessageBegin('ComposeUserMentions', TMessageType.CALL, self._seqid)
    args = ComposeUserMentions_args()
    args.req_id = req_id
    args.usernames = usernames
    args.carrier = carrier
    args.write(self._oprot)
    self._oprot.writeMessageEnd()
    self._oprot.trans.flush()

# Node: ComposeUserMentions_args
def recv_ComposeUserMentions(self):
    iprot = self._iprot
    fname, mtype, rseqid = iprot.readMessageBegin()
    if mtype == TMessageType.EXCEPTION:
        x = TApplicationException()
        x.read(iprot)
        iprot.readMessageEnd()
        raise x
    result = ComposeUserMentions_result()
    result.read(iprot)
    iprot.readMessageEnd()
    if result.success is not None:
        return result.success
    if result.se is not None:
        raise result.se
    raise TApplicationException(TApplicationException.MISSING_RESULT, 'ComposeUserMentions failed: unknown result')

# Node: ComposeUserMentions_result
class Processor(Iface, TProcessor):

    def __init__(self, handler):
        self._handler = handler
        self._processMap = {}
        self._processMap['ComposeUserMentions'] = Processor.process_ComposeUserMentions
        self._on_message_begin = None

    def on_message_begin(self, func):
        self._on_message_begin = func

    def process(self, iprot, oprot):
        name, type, seqid = iprot.readMessageBegin()
        if self._on_message_begin:
            self._on_message_begin(name, type, seqid)
        if name not in self._processMap:
            iprot.skip(TType.STRUCT)
            iprot.readMessageEnd()
            x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
            oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
            x.write(oprot)
            oprot.writeMessageEnd()
            oprot.trans.flush()
            return
        else:
            self._processMap[name](self, seqid, iprot, oprot)
        return True

    def process_ComposeUserMentions(self, seqid, iprot, oprot):
        args = ComposeUserMentions_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = ComposeUserMentions_result()
        try:
            result.success = self._handler.ComposeUserMentions(args.req_id, args.usernames, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('ComposeUserMentions', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

def process(self, iprot, oprot):
    name, type, seqid = iprot.readMessageBegin()
    if self._on_message_begin:
        self._on_message_begin(name, type, seqid)
    if name not in self._processMap:
        iprot.skip(TType.STRUCT)
        iprot.readMessageEnd()
        x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
        oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
        x.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()
        return
    else:
        self._processMap[name](self, seqid, iprot, oprot)
    return True

def process_ComposeUserMentions(self, seqid, iprot, oprot):
    args = ComposeUserMentions_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = ComposeUserMentions_result()
    try:
        result.success = self._handler.ComposeUserMentions(args.req_id, args.usernames, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('ComposeUserMentions', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

# Node: ComposeUserMentions
class Client(Iface):

    def __init__(self, iprot, oprot=None):
        self._iprot = self._oprot = iprot
        if oprot is not None:
            self._oprot = oprot
        self._seqid = 0

    def ComposeUniqueId(self, req_id, post_type, carrier):
        """
        Parameters:
         - req_id
         - post_type
         - carrier

        """
        self.send_ComposeUniqueId(req_id, post_type, carrier)
        return self.recv_ComposeUniqueId()

    def send_ComposeUniqueId(self, req_id, post_type, carrier):
        self._oprot.writeMessageBegin('ComposeUniqueId', TMessageType.CALL, self._seqid)
        args = ComposeUniqueId_args()
        args.req_id = req_id
        args.post_type = post_type
        args.carrier = carrier
        args.write(self._oprot)
        self._oprot.writeMessageEnd()
        self._oprot.trans.flush()

    def recv_ComposeUniqueId(self):
        iprot = self._iprot
        fname, mtype, rseqid = iprot.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iprot)
            iprot.readMessageEnd()
            raise x
        result = ComposeUniqueId_result()
        result.read(iprot)
        iprot.readMessageEnd()
        if result.success is not None:
            return result.success
        if result.se is not None:
            raise result.se
        raise TApplicationException(TApplicationException.MISSING_RESULT, 'ComposeUniqueId failed: unknown result')

def send_ComposeUniqueId(self, req_id, post_type, carrier):
    self._oprot.writeMessageBegin('ComposeUniqueId', TMessageType.CALL, self._seqid)
    args = ComposeUniqueId_args()
    args.req_id = req_id
    args.post_type = post_type
    args.carrier = carrier
    args.write(self._oprot)
    self._oprot.writeMessageEnd()
    self._oprot.trans.flush()

# Node: ComposeUniqueId_args
def recv_ComposeUniqueId(self):
    iprot = self._iprot
    fname, mtype, rseqid = iprot.readMessageBegin()
    if mtype == TMessageType.EXCEPTION:
        x = TApplicationException()
        x.read(iprot)
        iprot.readMessageEnd()
        raise x
    result = ComposeUniqueId_result()
    result.read(iprot)
    iprot.readMessageEnd()
    if result.success is not None:
        return result.success
    if result.se is not None:
        raise result.se
    raise TApplicationException(TApplicationException.MISSING_RESULT, 'ComposeUniqueId failed: unknown result')

# Node: ComposeUniqueId_result
class Processor(Iface, TProcessor):

    def __init__(self, handler):
        self._handler = handler
        self._processMap = {}
        self._processMap['ComposeUniqueId'] = Processor.process_ComposeUniqueId
        self._on_message_begin = None

    def on_message_begin(self, func):
        self._on_message_begin = func

    def process(self, iprot, oprot):
        name, type, seqid = iprot.readMessageBegin()
        if self._on_message_begin:
            self._on_message_begin(name, type, seqid)
        if name not in self._processMap:
            iprot.skip(TType.STRUCT)
            iprot.readMessageEnd()
            x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
            oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
            x.write(oprot)
            oprot.writeMessageEnd()
            oprot.trans.flush()
            return
        else:
            self._processMap[name](self, seqid, iprot, oprot)
        return True

    def process_ComposeUniqueId(self, seqid, iprot, oprot):
        args = ComposeUniqueId_args()
        args.read(iprot)
        iprot.readMessageEnd()
        result = ComposeUniqueId_result()
        try:
            result.success = self._handler.ComposeUniqueId(args.req_id, args.post_type, args.carrier)
            msg_type = TMessageType.REPLY
        except TTransport.TTransportException:
            raise
        except ServiceException as se:
            msg_type = TMessageType.REPLY
            result.se = se
        except TApplicationException as ex:
            logging.exception('TApplication exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = ex
        except Exception:
            logging.exception('Unexpected exception in handler')
            msg_type = TMessageType.EXCEPTION
            result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
        oprot.writeMessageBegin('ComposeUniqueId', msg_type, seqid)
        result.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()

def process(self, iprot, oprot):
    name, type, seqid = iprot.readMessageBegin()
    if self._on_message_begin:
        self._on_message_begin(name, type, seqid)
    if name not in self._processMap:
        iprot.skip(TType.STRUCT)
        iprot.readMessageEnd()
        x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % name)
        oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
        x.write(oprot)
        oprot.writeMessageEnd()
        oprot.trans.flush()
        return
    else:
        self._processMap[name](self, seqid, iprot, oprot)
    return True

def process_ComposeUniqueId(self, seqid, iprot, oprot):
    args = ComposeUniqueId_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = ComposeUniqueId_result()
    try:
        result.success = self._handler.ComposeUniqueId(args.req_id, args.post_type, args.carrier)
        msg_type = TMessageType.REPLY
    except TTransport.TTransportException:
        raise
    except ServiceException as se:
        msg_type = TMessageType.REPLY
        result.se = se
    except TApplicationException as ex:
        logging.exception('TApplication exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = ex
    except Exception:
        logging.exception('Unexpected exception in handler')
        msg_type = TMessageType.EXCEPTION
        result = TApplicationException(TApplicationException.INTERNAL_ERROR, 'Internal error')
    oprot.writeMessageBegin('ComposeUniqueId', msg_type, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

# Node: ComposeUniqueId
