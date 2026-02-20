# Cluster 5

# Node: items
class UploadText_args(object):
    """
    Attributes:
     - req_id
     - text
     - carrier

    """

    def __init__(self, req_id=None, text=None, carrier=None):
        self.req_id = req_id
        self.text = text
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.STRING:
                    self.text = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype70, _vtype71, _size69 = iprot.readMapBegin()
                    for _i73 in range(_size69):
                        _key74 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        _val75 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key74] = _val75
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('UploadText_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.text is not None:
            oprot.writeFieldBegin('text', TType.STRING, 2)
            oprot.writeString(self.text.encode('utf-8') if sys.version_info[0] == 2 else self.text)
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 3)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter76, viter77 in self.carrier.items():
                oprot.writeString(kiter76.encode('utf-8') if sys.version_info[0] == 2 else kiter76)
                oprot.writeString(viter77.encode('utf-8') if sys.version_info[0] == 2 else viter77)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

# Node: join
class UploadText_result(object):
    """
    Attributes:
     - se

    """

    def __init__(self, se=None):
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException()
                    self.se.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('UploadText_result')
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class UploadMovieReview_args(object):
    """
    Attributes:
     - req_id
     - movie_id
     - review_id
     - timestamp
     - carrier

    """

    def __init__(self, req_id=None, movie_id=None, review_id=None, timestamp=None, carrier=None):
        self.req_id = req_id
        self.movie_id = movie_id
        self.review_id = review_id
        self.timestamp = timestamp
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.STRING:
                    self.movie_id = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.I64:
                    self.review_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 4:
                if ftype == TType.I64:
                    self.timestamp = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 5:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype210, _vtype211, _size209 = iprot.readMapBegin()
                    for _i213 in range(_size209):
                        _key214 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        _val215 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key214] = _val215
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('UploadMovieReview_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.movie_id is not None:
            oprot.writeFieldBegin('movie_id', TType.STRING, 2)
            oprot.writeString(self.movie_id.encode('utf-8') if sys.version_info[0] == 2 else self.movie_id)
            oprot.writeFieldEnd()
        if self.review_id is not None:
            oprot.writeFieldBegin('review_id', TType.I64, 3)
            oprot.writeI64(self.review_id)
            oprot.writeFieldEnd()
        if self.timestamp is not None:
            oprot.writeFieldBegin('timestamp', TType.I64, 4)
            oprot.writeI64(self.timestamp)
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 5)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter216, viter217 in self.carrier.items():
                oprot.writeString(kiter216.encode('utf-8') if sys.version_info[0] == 2 else kiter216)
                oprot.writeString(viter217.encode('utf-8') if sys.version_info[0] == 2 else viter217)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class UploadMovieReview_result(object):
    """
    Attributes:
     - se

    """

    def __init__(self, se=None):
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException()
                    self.se.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('UploadMovieReview_result')
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class ReadMovieReviews_args(object):
    """
    Attributes:
     - req_id
     - movie_id
     - start
     - stop
     - carrier

    """

    def __init__(self, req_id=None, movie_id=None, start=None, stop=None, carrier=None):
        self.req_id = req_id
        self.movie_id = movie_id
        self.start = start
        self.stop = stop
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.STRING:
                    self.movie_id = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.I32:
                    self.start = iprot.readI32()
                else:
                    iprot.skip(ftype)
            elif fid == 4:
                if ftype == TType.I32:
                    self.stop = iprot.readI32()
                else:
                    iprot.skip(ftype)
            elif fid == 5:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype219, _vtype220, _size218 = iprot.readMapBegin()
                    for _i222 in range(_size218):
                        _key223 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        _val224 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key223] = _val224
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('ReadMovieReviews_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.movie_id is not None:
            oprot.writeFieldBegin('movie_id', TType.STRING, 2)
            oprot.writeString(self.movie_id.encode('utf-8') if sys.version_info[0] == 2 else self.movie_id)
            oprot.writeFieldEnd()
        if self.start is not None:
            oprot.writeFieldBegin('start', TType.I32, 3)
            oprot.writeI32(self.start)
            oprot.writeFieldEnd()
        if self.stop is not None:
            oprot.writeFieldBegin('stop', TType.I32, 4)
            oprot.writeI32(self.stop)
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 5)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter225, viter226 in self.carrier.items():
                oprot.writeString(kiter225.encode('utf-8') if sys.version_info[0] == 2 else kiter225)
                oprot.writeString(viter226.encode('utf-8') if sys.version_info[0] == 2 else viter226)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class ReadMovieReviews_result(object):
    """
    Attributes:
     - success
     - se

    """

    def __init__(self, success=None, se=None):
        self.success = success
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 0:
                if ftype == TType.LIST:
                    self.success = []
                    _etype230, _size227 = iprot.readListBegin()
                    for _i231 in range(_size227):
                        _elem232 = Review()
                        _elem232.read(iprot)
                        self.success.append(_elem232)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException()
                    self.se.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('ReadMovieReviews_result')
        if self.success is not None:
            oprot.writeFieldBegin('success', TType.LIST, 0)
            oprot.writeListBegin(TType.STRUCT, len(self.success))
            for iter233 in self.success:
                iter233.write(oprot)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class WritePlot_args(object):
    """
    Attributes:
     - req_id
     - plot_id
     - plot
     - carrier

    """

    def __init__(self, req_id=None, plot_id=None, plot=None, carrier=None):
        self.req_id = req_id
        self.plot_id = plot_id
        self.plot = plot
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.I64:
                    self.plot_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.STRING:
                    self.plot = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 4:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype292, _vtype293, _size291 = iprot.readMapBegin()
                    for _i295 in range(_size291):
                        _key296 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        _val297 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key296] = _val297
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('WritePlot_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.plot_id is not None:
            oprot.writeFieldBegin('plot_id', TType.I64, 2)
            oprot.writeI64(self.plot_id)
            oprot.writeFieldEnd()
        if self.plot is not None:
            oprot.writeFieldBegin('plot', TType.STRING, 3)
            oprot.writeString(self.plot.encode('utf-8') if sys.version_info[0] == 2 else self.plot)
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 4)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter298, viter299 in self.carrier.items():
                oprot.writeString(kiter298.encode('utf-8') if sys.version_info[0] == 2 else kiter298)
                oprot.writeString(viter299.encode('utf-8') if sys.version_info[0] == 2 else viter299)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class WritePlot_result(object):
    """
    Attributes:
     - se

    """

    def __init__(self, se=None):
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException()
                    self.se.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('WritePlot_result')
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class ReadPlot_args(object):
    """
    Attributes:
     - req_id
     - plot_id
     - carrier

    """

    def __init__(self, req_id=None, plot_id=None, carrier=None):
        self.req_id = req_id
        self.plot_id = plot_id
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.I64:
                    self.plot_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype301, _vtype302, _size300 = iprot.readMapBegin()
                    for _i304 in range(_size300):
                        _key305 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        _val306 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key305] = _val306
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('ReadPlot_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.plot_id is not None:
            oprot.writeFieldBegin('plot_id', TType.I64, 2)
            oprot.writeI64(self.plot_id)
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 3)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter307, viter308 in self.carrier.items():
                oprot.writeString(kiter307.encode('utf-8') if sys.version_info[0] == 2 else kiter307)
                oprot.writeString(viter308.encode('utf-8') if sys.version_info[0] == 2 else viter308)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class ReadPlot_result(object):
    """
    Attributes:
     - success
     - se

    """

    def __init__(self, success=None, se=None):
        self.success = success
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 0:
                if ftype == TType.STRING:
                    self.success = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException()
                    self.se.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('ReadPlot_result')
        if self.success is not None:
            oprot.writeFieldBegin('success', TType.STRING, 0)
            oprot.writeString(self.success.encode('utf-8') if sys.version_info[0] == 2 else self.success)
            oprot.writeFieldEnd()
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class WriteMovieInfo_args(object):
    """
    Attributes:
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

    def __init__(self, req_id=None, movie_id=None, title=None, casts=None, plot_id=None, thumbnail_ids=None, photo_ids=None, video_ids=None, avg_rating=None, num_rating=None, carrier=None):
        self.req_id = req_id
        self.movie_id = movie_id
        self.title = title
        self.casts = casts
        self.plot_id = plot_id
        self.thumbnail_ids = thumbnail_ids
        self.photo_ids = photo_ids
        self.video_ids = video_ids
        self.avg_rating = avg_rating
        self.num_rating = num_rating
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.STRING:
                    self.movie_id = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.STRING:
                    self.title = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 4:
                if ftype == TType.LIST:
                    self.casts = []
                    _etype312, _size309 = iprot.readListBegin()
                    for _i313 in range(_size309):
                        _elem314 = Cast()
                        _elem314.read(iprot)
                        self.casts.append(_elem314)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 5:
                if ftype == TType.I64:
                    self.plot_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 6:
                if ftype == TType.LIST:
                    self.thumbnail_ids = []
                    _etype318, _size315 = iprot.readListBegin()
                    for _i319 in range(_size315):
                        _elem320 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        self.thumbnail_ids.append(_elem320)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 7:
                if ftype == TType.LIST:
                    self.photo_ids = []
                    _etype324, _size321 = iprot.readListBegin()
                    for _i325 in range(_size321):
                        _elem326 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        self.photo_ids.append(_elem326)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 8:
                if ftype == TType.LIST:
                    self.video_ids = []
                    _etype330, _size327 = iprot.readListBegin()
                    for _i331 in range(_size327):
                        _elem332 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        self.video_ids.append(_elem332)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 9:
                if ftype == TType.DOUBLE:
                    self.avg_rating = iprot.readDouble()
                else:
                    iprot.skip(ftype)
            elif fid == 10:
                if ftype == TType.I32:
                    self.num_rating = iprot.readI32()
                else:
                    iprot.skip(ftype)
            elif fid == 11:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype334, _vtype335, _size333 = iprot.readMapBegin()
                    for _i337 in range(_size333):
                        _key338 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        _val339 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key338] = _val339
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('WriteMovieInfo_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.movie_id is not None:
            oprot.writeFieldBegin('movie_id', TType.STRING, 2)
            oprot.writeString(self.movie_id.encode('utf-8') if sys.version_info[0] == 2 else self.movie_id)
            oprot.writeFieldEnd()
        if self.title is not None:
            oprot.writeFieldBegin('title', TType.STRING, 3)
            oprot.writeString(self.title.encode('utf-8') if sys.version_info[0] == 2 else self.title)
            oprot.writeFieldEnd()
        if self.casts is not None:
            oprot.writeFieldBegin('casts', TType.LIST, 4)
            oprot.writeListBegin(TType.STRUCT, len(self.casts))
            for iter340 in self.casts:
                iter340.write(oprot)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        if self.plot_id is not None:
            oprot.writeFieldBegin('plot_id', TType.I64, 5)
            oprot.writeI64(self.plot_id)
            oprot.writeFieldEnd()
        if self.thumbnail_ids is not None:
            oprot.writeFieldBegin('thumbnail_ids', TType.LIST, 6)
            oprot.writeListBegin(TType.STRING, len(self.thumbnail_ids))
            for iter341 in self.thumbnail_ids:
                oprot.writeString(iter341.encode('utf-8') if sys.version_info[0] == 2 else iter341)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        if self.photo_ids is not None:
            oprot.writeFieldBegin('photo_ids', TType.LIST, 7)
            oprot.writeListBegin(TType.STRING, len(self.photo_ids))
            for iter342 in self.photo_ids:
                oprot.writeString(iter342.encode('utf-8') if sys.version_info[0] == 2 else iter342)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        if self.video_ids is not None:
            oprot.writeFieldBegin('video_ids', TType.LIST, 8)
            oprot.writeListBegin(TType.STRING, len(self.video_ids))
            for iter343 in self.video_ids:
                oprot.writeString(iter343.encode('utf-8') if sys.version_info[0] == 2 else iter343)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        if self.avg_rating is not None:
            oprot.writeFieldBegin('avg_rating', TType.DOUBLE, 9)
            oprot.writeDouble(self.avg_rating)
            oprot.writeFieldEnd()
        if self.num_rating is not None:
            oprot.writeFieldBegin('num_rating', TType.I32, 10)
            oprot.writeI32(self.num_rating)
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 11)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter344, viter345 in self.carrier.items():
                oprot.writeString(kiter344.encode('utf-8') if sys.version_info[0] == 2 else kiter344)
                oprot.writeString(viter345.encode('utf-8') if sys.version_info[0] == 2 else viter345)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class WriteMovieInfo_result(object):
    """
    Attributes:
     - se

    """

    def __init__(self, se=None):
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException()
                    self.se.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('WriteMovieInfo_result')
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class ReadMovieInfo_args(object):
    """
    Attributes:
     - req_id
     - movie_id
     - carrier

    """

    def __init__(self, req_id=None, movie_id=None, carrier=None):
        self.req_id = req_id
        self.movie_id = movie_id
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.STRING:
                    self.movie_id = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype347, _vtype348, _size346 = iprot.readMapBegin()
                    for _i350 in range(_size346):
                        _key351 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        _val352 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key351] = _val352
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('ReadMovieInfo_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.movie_id is not None:
            oprot.writeFieldBegin('movie_id', TType.STRING, 2)
            oprot.writeString(self.movie_id.encode('utf-8') if sys.version_info[0] == 2 else self.movie_id)
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 3)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter353, viter354 in self.carrier.items():
                oprot.writeString(kiter353.encode('utf-8') if sys.version_info[0] == 2 else kiter353)
                oprot.writeString(viter354.encode('utf-8') if sys.version_info[0] == 2 else viter354)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class ReadMovieInfo_result(object):
    """
    Attributes:
     - success
     - se

    """

    def __init__(self, success=None, se=None):
        self.success = success
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 0:
                if ftype == TType.STRUCT:
                    self.success = MovieInfo()
                    self.success.read(iprot)
                else:
                    iprot.skip(ftype)
            elif fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException()
                    self.se.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('ReadMovieInfo_result')
        if self.success is not None:
            oprot.writeFieldBegin('success', TType.STRUCT, 0)
            self.success.write(oprot)
            oprot.writeFieldEnd()
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class UpdateRating_args(object):
    """
    Attributes:
     - req_id
     - movie_id
     - sum_uncommitted_rating
     - num_uncommitted_rating
     - carrier

    """

    def __init__(self, req_id=None, movie_id=None, sum_uncommitted_rating=None, num_uncommitted_rating=None, carrier=None):
        self.req_id = req_id
        self.movie_id = movie_id
        self.sum_uncommitted_rating = sum_uncommitted_rating
        self.num_uncommitted_rating = num_uncommitted_rating
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.STRING:
                    self.movie_id = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.I32:
                    self.sum_uncommitted_rating = iprot.readI32()
                else:
                    iprot.skip(ftype)
            elif fid == 4:
                if ftype == TType.I32:
                    self.num_uncommitted_rating = iprot.readI32()
                else:
                    iprot.skip(ftype)
            elif fid == 5:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype356, _vtype357, _size355 = iprot.readMapBegin()
                    for _i359 in range(_size355):
                        _key360 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        _val361 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key360] = _val361
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('UpdateRating_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.movie_id is not None:
            oprot.writeFieldBegin('movie_id', TType.STRING, 2)
            oprot.writeString(self.movie_id.encode('utf-8') if sys.version_info[0] == 2 else self.movie_id)
            oprot.writeFieldEnd()
        if self.sum_uncommitted_rating is not None:
            oprot.writeFieldBegin('sum_uncommitted_rating', TType.I32, 3)
            oprot.writeI32(self.sum_uncommitted_rating)
            oprot.writeFieldEnd()
        if self.num_uncommitted_rating is not None:
            oprot.writeFieldBegin('num_uncommitted_rating', TType.I32, 4)
            oprot.writeI32(self.num_uncommitted_rating)
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 5)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter362, viter363 in self.carrier.items():
                oprot.writeString(kiter362.encode('utf-8') if sys.version_info[0] == 2 else kiter362)
                oprot.writeString(viter363.encode('utf-8') if sys.version_info[0] == 2 else viter363)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class UpdateRating_result(object):
    """
    Attributes:
     - se

    """

    def __init__(self, se=None):
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException()
                    self.se.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('UpdateRating_result')
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class User(object):
    """
    Attributes:
     - user_id
     - first_name
     - last_name
     - username
     - password
     - salt

    """

    def __init__(self, user_id=None, first_name=None, last_name=None, username=None, password=None, salt=None):
        self.user_id = user_id
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.password = password
        self.salt = salt

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.user_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.STRING:
                    self.first_name = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.STRING:
                    self.last_name = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 4:
                if ftype == TType.STRING:
                    self.username = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 5:
                if ftype == TType.STRING:
                    self.password = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 6:
                if ftype == TType.STRING:
                    self.salt = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('User')
        if self.user_id is not None:
            oprot.writeFieldBegin('user_id', TType.I64, 1)
            oprot.writeI64(self.user_id)
            oprot.writeFieldEnd()
        if self.first_name is not None:
            oprot.writeFieldBegin('first_name', TType.STRING, 2)
            oprot.writeString(self.first_name.encode('utf-8') if sys.version_info[0] == 2 else self.first_name)
            oprot.writeFieldEnd()
        if self.last_name is not None:
            oprot.writeFieldBegin('last_name', TType.STRING, 3)
            oprot.writeString(self.last_name.encode('utf-8') if sys.version_info[0] == 2 else self.last_name)
            oprot.writeFieldEnd()
        if self.username is not None:
            oprot.writeFieldBegin('username', TType.STRING, 4)
            oprot.writeString(self.username.encode('utf-8') if sys.version_info[0] == 2 else self.username)
            oprot.writeFieldEnd()
        if self.password is not None:
            oprot.writeFieldBegin('password', TType.STRING, 5)
            oprot.writeString(self.password.encode('utf-8') if sys.version_info[0] == 2 else self.password)
            oprot.writeFieldEnd()
        if self.salt is not None:
            oprot.writeFieldBegin('salt', TType.STRING, 6)
            oprot.writeString(self.salt.encode('utf-8') if sys.version_info[0] == 2 else self.salt)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class Review(object):
    """
    Attributes:
     - review_id
     - user_id
     - req_id
     - text
     - movie_id
     - rating
     - timestamp

    """

    def __init__(self, review_id=None, user_id=None, req_id=None, text=None, movie_id=None, rating=None, timestamp=None):
        self.review_id = review_id
        self.user_id = user_id
        self.req_id = req_id
        self.text = text
        self.movie_id = movie_id
        self.rating = rating
        self.timestamp = timestamp

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.review_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.I64:
                    self.user_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 4:
                if ftype == TType.STRING:
                    self.text = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 5:
                if ftype == TType.STRING:
                    self.movie_id = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 6:
                if ftype == TType.I32:
                    self.rating = iprot.readI32()
                else:
                    iprot.skip(ftype)
            elif fid == 7:
                if ftype == TType.I64:
                    self.timestamp = iprot.readI64()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('Review')
        if self.review_id is not None:
            oprot.writeFieldBegin('review_id', TType.I64, 1)
            oprot.writeI64(self.review_id)
            oprot.writeFieldEnd()
        if self.user_id is not None:
            oprot.writeFieldBegin('user_id', TType.I64, 2)
            oprot.writeI64(self.user_id)
            oprot.writeFieldEnd()
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 3)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.text is not None:
            oprot.writeFieldBegin('text', TType.STRING, 4)
            oprot.writeString(self.text.encode('utf-8') if sys.version_info[0] == 2 else self.text)
            oprot.writeFieldEnd()
        if self.movie_id is not None:
            oprot.writeFieldBegin('movie_id', TType.STRING, 5)
            oprot.writeString(self.movie_id.encode('utf-8') if sys.version_info[0] == 2 else self.movie_id)
            oprot.writeFieldEnd()
        if self.rating is not None:
            oprot.writeFieldBegin('rating', TType.I32, 6)
            oprot.writeI32(self.rating)
            oprot.writeFieldEnd()
        if self.timestamp is not None:
            oprot.writeFieldBegin('timestamp', TType.I64, 7)
            oprot.writeI64(self.timestamp)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class CastInfo(object):
    """
    Attributes:
     - cast_info_id
     - name
     - gender
     - intro

    """

    def __init__(self, cast_info_id=None, name=None, gender=None, intro=None):
        self.cast_info_id = cast_info_id
        self.name = name
        self.gender = gender
        self.intro = intro

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.cast_info_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.STRING:
                    self.name = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.BOOL:
                    self.gender = iprot.readBool()
                else:
                    iprot.skip(ftype)
            elif fid == 4:
                if ftype == TType.STRING:
                    self.intro = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('CastInfo')
        if self.cast_info_id is not None:
            oprot.writeFieldBegin('cast_info_id', TType.I64, 1)
            oprot.writeI64(self.cast_info_id)
            oprot.writeFieldEnd()
        if self.name is not None:
            oprot.writeFieldBegin('name', TType.STRING, 2)
            oprot.writeString(self.name.encode('utf-8') if sys.version_info[0] == 2 else self.name)
            oprot.writeFieldEnd()
        if self.gender is not None:
            oprot.writeFieldBegin('gender', TType.BOOL, 3)
            oprot.writeBool(self.gender)
            oprot.writeFieldEnd()
        if self.intro is not None:
            oprot.writeFieldBegin('intro', TType.STRING, 4)
            oprot.writeString(self.intro.encode('utf-8') if sys.version_info[0] == 2 else self.intro)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class Cast(object):
    """
    Attributes:
     - cast_id
     - character
     - cast_info_id

    """

    def __init__(self, cast_id=None, character=None, cast_info_id=None):
        self.cast_id = cast_id
        self.character = character
        self.cast_info_id = cast_info_id

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I32:
                    self.cast_id = iprot.readI32()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.STRING:
                    self.character = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.I64:
                    self.cast_info_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('Cast')
        if self.cast_id is not None:
            oprot.writeFieldBegin('cast_id', TType.I32, 1)
            oprot.writeI32(self.cast_id)
            oprot.writeFieldEnd()
        if self.character is not None:
            oprot.writeFieldBegin('character', TType.STRING, 2)
            oprot.writeString(self.character.encode('utf-8') if sys.version_info[0] == 2 else self.character)
            oprot.writeFieldEnd()
        if self.cast_info_id is not None:
            oprot.writeFieldBegin('cast_info_id', TType.I64, 3)
            oprot.writeI64(self.cast_info_id)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class MovieInfo(object):
    """
    Attributes:
     - movie_id
     - title
     - casts
     - plot_id
     - thumbnail_ids
     - photo_ids
     - video_ids
     - avg_rating
     - num_rating

    """

    def __init__(self, movie_id=None, title=None, casts=None, plot_id=None, thumbnail_ids=None, photo_ids=None, video_ids=None, avg_rating=None, num_rating=None):
        self.movie_id = movie_id
        self.title = title
        self.casts = casts
        self.plot_id = plot_id
        self.thumbnail_ids = thumbnail_ids
        self.photo_ids = photo_ids
        self.video_ids = video_ids
        self.avg_rating = avg_rating
        self.num_rating = num_rating

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.STRING:
                    self.movie_id = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.STRING:
                    self.title = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.LIST:
                    self.casts = []
                    _etype3, _size0 = iprot.readListBegin()
                    for _i4 in range(_size0):
                        _elem5 = Cast()
                        _elem5.read(iprot)
                        self.casts.append(_elem5)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 4:
                if ftype == TType.I64:
                    self.plot_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 5:
                if ftype == TType.LIST:
                    self.thumbnail_ids = []
                    _etype9, _size6 = iprot.readListBegin()
                    for _i10 in range(_size6):
                        _elem11 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        self.thumbnail_ids.append(_elem11)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 6:
                if ftype == TType.LIST:
                    self.photo_ids = []
                    _etype15, _size12 = iprot.readListBegin()
                    for _i16 in range(_size12):
                        _elem17 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        self.photo_ids.append(_elem17)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 7:
                if ftype == TType.LIST:
                    self.video_ids = []
                    _etype21, _size18 = iprot.readListBegin()
                    for _i22 in range(_size18):
                        _elem23 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        self.video_ids.append(_elem23)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 8:
                if ftype == TType.DOUBLE:
                    self.avg_rating = iprot.readDouble()
                else:
                    iprot.skip(ftype)
            elif fid == 9:
                if ftype == TType.I32:
                    self.num_rating = iprot.readI32()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('MovieInfo')
        if self.movie_id is not None:
            oprot.writeFieldBegin('movie_id', TType.STRING, 1)
            oprot.writeString(self.movie_id.encode('utf-8') if sys.version_info[0] == 2 else self.movie_id)
            oprot.writeFieldEnd()
        if self.title is not None:
            oprot.writeFieldBegin('title', TType.STRING, 2)
            oprot.writeString(self.title.encode('utf-8') if sys.version_info[0] == 2 else self.title)
            oprot.writeFieldEnd()
        if self.casts is not None:
            oprot.writeFieldBegin('casts', TType.LIST, 3)
            oprot.writeListBegin(TType.STRUCT, len(self.casts))
            for iter24 in self.casts:
                iter24.write(oprot)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        if self.plot_id is not None:
            oprot.writeFieldBegin('plot_id', TType.I64, 4)
            oprot.writeI64(self.plot_id)
            oprot.writeFieldEnd()
        if self.thumbnail_ids is not None:
            oprot.writeFieldBegin('thumbnail_ids', TType.LIST, 5)
            oprot.writeListBegin(TType.STRING, len(self.thumbnail_ids))
            for iter25 in self.thumbnail_ids:
                oprot.writeString(iter25.encode('utf-8') if sys.version_info[0] == 2 else iter25)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        if self.photo_ids is not None:
            oprot.writeFieldBegin('photo_ids', TType.LIST, 6)
            oprot.writeListBegin(TType.STRING, len(self.photo_ids))
            for iter26 in self.photo_ids:
                oprot.writeString(iter26.encode('utf-8') if sys.version_info[0] == 2 else iter26)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        if self.video_ids is not None:
            oprot.writeFieldBegin('video_ids', TType.LIST, 7)
            oprot.writeListBegin(TType.STRING, len(self.video_ids))
            for iter27 in self.video_ids:
                oprot.writeString(iter27.encode('utf-8') if sys.version_info[0] == 2 else iter27)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        if self.avg_rating is not None:
            oprot.writeFieldBegin('avg_rating', TType.DOUBLE, 8)
            oprot.writeDouble(self.avg_rating)
            oprot.writeFieldEnd()
        if self.num_rating is not None:
            oprot.writeFieldBegin('num_rating', TType.I32, 9)
            oprot.writeI32(self.num_rating)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class Page(object):
    """
    Attributes:
     - movie_info
     - reviews
     - cast_infos
     - plot

    """

    def __init__(self, movie_info=None, reviews=None, cast_infos=None, plot=None):
        self.movie_info = movie_info
        self.reviews = reviews
        self.cast_infos = cast_infos
        self.plot = plot

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.STRUCT:
                    self.movie_info = MovieInfo()
                    self.movie_info.read(iprot)
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.LIST:
                    self.reviews = []
                    _etype31, _size28 = iprot.readListBegin()
                    for _i32 in range(_size28):
                        _elem33 = Review()
                        _elem33.read(iprot)
                        self.reviews.append(_elem33)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.LIST:
                    self.cast_infos = []
                    _etype37, _size34 = iprot.readListBegin()
                    for _i38 in range(_size34):
                        _elem39 = CastInfo()
                        _elem39.read(iprot)
                        self.cast_infos.append(_elem39)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 4:
                if ftype == TType.STRING:
                    self.plot = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('Page')
        if self.movie_info is not None:
            oprot.writeFieldBegin('movie_info', TType.STRUCT, 1)
            self.movie_info.write(oprot)
            oprot.writeFieldEnd()
        if self.reviews is not None:
            oprot.writeFieldBegin('reviews', TType.LIST, 2)
            oprot.writeListBegin(TType.STRUCT, len(self.reviews))
            for iter40 in self.reviews:
                iter40.write(oprot)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        if self.cast_infos is not None:
            oprot.writeFieldBegin('cast_infos', TType.LIST, 3)
            oprot.writeListBegin(TType.STRUCT, len(self.cast_infos))
            for iter41 in self.cast_infos:
                iter41.write(oprot)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        if self.plot is not None:
            oprot.writeFieldBegin('plot', TType.STRING, 4)
            oprot.writeString(self.plot.encode('utf-8') if sys.version_info[0] == 2 else self.plot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class ServiceException(TException):
    """
    Attributes:
     - errorCode
     - message

    """

    def __init__(self, errorCode=None, message=None):
        self.errorCode = errorCode
        self.message = message

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I32:
                    self.errorCode = iprot.readI32()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.STRING:
                    self.message = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('ServiceException')
        if self.errorCode is not None:
            oprot.writeFieldBegin('errorCode', TType.I32, 1)
            oprot.writeI32(self.errorCode)
            oprot.writeFieldEnd()
        if self.message is not None:
            oprot.writeFieldBegin('message', TType.STRING, 2)
            oprot.writeString(self.message.encode('utf-8') if sys.version_info[0] == 2 else self.message)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __str__(self):
        return repr(self)

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class RegisterUser_args(object):
    """
    Attributes:
     - req_id
     - first_name
     - last_name
     - username
     - password
     - carrier

    """

    def __init__(self, req_id=None, first_name=None, last_name=None, username=None, password=None, carrier=None):
        self.req_id = req_id
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.password = password
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.STRING:
                    self.first_name = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.STRING:
                    self.last_name = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 4:
                if ftype == TType.STRING:
                    self.username = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 5:
                if ftype == TType.STRING:
                    self.password = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 6:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype88, _vtype89, _size87 = iprot.readMapBegin()
                    for _i91 in range(_size87):
                        _key92 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        _val93 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key92] = _val93
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('RegisterUser_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.first_name is not None:
            oprot.writeFieldBegin('first_name', TType.STRING, 2)
            oprot.writeString(self.first_name.encode('utf-8') if sys.version_info[0] == 2 else self.first_name)
            oprot.writeFieldEnd()
        if self.last_name is not None:
            oprot.writeFieldBegin('last_name', TType.STRING, 3)
            oprot.writeString(self.last_name.encode('utf-8') if sys.version_info[0] == 2 else self.last_name)
            oprot.writeFieldEnd()
        if self.username is not None:
            oprot.writeFieldBegin('username', TType.STRING, 4)
            oprot.writeString(self.username.encode('utf-8') if sys.version_info[0] == 2 else self.username)
            oprot.writeFieldEnd()
        if self.password is not None:
            oprot.writeFieldBegin('password', TType.STRING, 5)
            oprot.writeString(self.password.encode('utf-8') if sys.version_info[0] == 2 else self.password)
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 6)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter94, viter95 in self.carrier.items():
                oprot.writeString(kiter94.encode('utf-8') if sys.version_info[0] == 2 else kiter94)
                oprot.writeString(viter95.encode('utf-8') if sys.version_info[0] == 2 else viter95)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class RegisterUser_result(object):
    """
    Attributes:
     - se

    """

    def __init__(self, se=None):
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException()
                    self.se.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('RegisterUser_result')
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class RegisterUserWithId_args(object):
    """
    Attributes:
     - req_id
     - first_name
     - last_name
     - username
     - password
     - user_id
     - carrier

    """

    def __init__(self, req_id=None, first_name=None, last_name=None, username=None, password=None, user_id=None, carrier=None):
        self.req_id = req_id
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.password = password
        self.user_id = user_id
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.STRING:
                    self.first_name = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.STRING:
                    self.last_name = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 4:
                if ftype == TType.STRING:
                    self.username = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 5:
                if ftype == TType.STRING:
                    self.password = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 6:
                if ftype == TType.I64:
                    self.user_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 7:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype97, _vtype98, _size96 = iprot.readMapBegin()
                    for _i100 in range(_size96):
                        _key101 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        _val102 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key101] = _val102
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('RegisterUserWithId_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.first_name is not None:
            oprot.writeFieldBegin('first_name', TType.STRING, 2)
            oprot.writeString(self.first_name.encode('utf-8') if sys.version_info[0] == 2 else self.first_name)
            oprot.writeFieldEnd()
        if self.last_name is not None:
            oprot.writeFieldBegin('last_name', TType.STRING, 3)
            oprot.writeString(self.last_name.encode('utf-8') if sys.version_info[0] == 2 else self.last_name)
            oprot.writeFieldEnd()
        if self.username is not None:
            oprot.writeFieldBegin('username', TType.STRING, 4)
            oprot.writeString(self.username.encode('utf-8') if sys.version_info[0] == 2 else self.username)
            oprot.writeFieldEnd()
        if self.password is not None:
            oprot.writeFieldBegin('password', TType.STRING, 5)
            oprot.writeString(self.password.encode('utf-8') if sys.version_info[0] == 2 else self.password)
            oprot.writeFieldEnd()
        if self.user_id is not None:
            oprot.writeFieldBegin('user_id', TType.I64, 6)
            oprot.writeI64(self.user_id)
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 7)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter103, viter104 in self.carrier.items():
                oprot.writeString(kiter103.encode('utf-8') if sys.version_info[0] == 2 else kiter103)
                oprot.writeString(viter104.encode('utf-8') if sys.version_info[0] == 2 else viter104)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class RegisterUserWithId_result(object):
    """
    Attributes:
     - se

    """

    def __init__(self, se=None):
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException()
                    self.se.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('RegisterUserWithId_result')
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class Login_args(object):
    """
    Attributes:
     - req_id
     - username
     - password
     - carrier

    """

    def __init__(self, req_id=None, username=None, password=None, carrier=None):
        self.req_id = req_id
        self.username = username
        self.password = password
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.STRING:
                    self.username = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.STRING:
                    self.password = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 4:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype106, _vtype107, _size105 = iprot.readMapBegin()
                    for _i109 in range(_size105):
                        _key110 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        _val111 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key110] = _val111
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('Login_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.username is not None:
            oprot.writeFieldBegin('username', TType.STRING, 2)
            oprot.writeString(self.username.encode('utf-8') if sys.version_info[0] == 2 else self.username)
            oprot.writeFieldEnd()
        if self.password is not None:
            oprot.writeFieldBegin('password', TType.STRING, 3)
            oprot.writeString(self.password.encode('utf-8') if sys.version_info[0] == 2 else self.password)
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 4)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter112, viter113 in self.carrier.items():
                oprot.writeString(kiter112.encode('utf-8') if sys.version_info[0] == 2 else kiter112)
                oprot.writeString(viter113.encode('utf-8') if sys.version_info[0] == 2 else viter113)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class Login_result(object):
    """
    Attributes:
     - success
     - se

    """

    def __init__(self, success=None, se=None):
        self.success = success
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 0:
                if ftype == TType.STRING:
                    self.success = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException()
                    self.se.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('Login_result')
        if self.success is not None:
            oprot.writeFieldBegin('success', TType.STRING, 0)
            oprot.writeString(self.success.encode('utf-8') if sys.version_info[0] == 2 else self.success)
            oprot.writeFieldEnd()
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class UploadUserWithUserId_args(object):
    """
    Attributes:
     - req_id
     - user_id
     - carrier

    """

    def __init__(self, req_id=None, user_id=None, carrier=None):
        self.req_id = req_id
        self.user_id = user_id
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.I64:
                    self.user_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype115, _vtype116, _size114 = iprot.readMapBegin()
                    for _i118 in range(_size114):
                        _key119 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        _val120 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key119] = _val120
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('UploadUserWithUserId_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.user_id is not None:
            oprot.writeFieldBegin('user_id', TType.I64, 2)
            oprot.writeI64(self.user_id)
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 3)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter121, viter122 in self.carrier.items():
                oprot.writeString(kiter121.encode('utf-8') if sys.version_info[0] == 2 else kiter121)
                oprot.writeString(viter122.encode('utf-8') if sys.version_info[0] == 2 else viter122)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class UploadUserWithUserId_result(object):
    """
    Attributes:
     - se

    """

    def __init__(self, se=None):
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException()
                    self.se.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('UploadUserWithUserId_result')
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class UploadUserWithUsername_args(object):
    """
    Attributes:
     - req_id
     - username
     - carrier

    """

    def __init__(self, req_id=None, username=None, carrier=None):
        self.req_id = req_id
        self.username = username
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.STRING:
                    self.username = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype124, _vtype125, _size123 = iprot.readMapBegin()
                    for _i127 in range(_size123):
                        _key128 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        _val129 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key128] = _val129
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('UploadUserWithUsername_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.username is not None:
            oprot.writeFieldBegin('username', TType.STRING, 2)
            oprot.writeString(self.username.encode('utf-8') if sys.version_info[0] == 2 else self.username)
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 3)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter130, viter131 in self.carrier.items():
                oprot.writeString(kiter130.encode('utf-8') if sys.version_info[0] == 2 else kiter130)
                oprot.writeString(viter131.encode('utf-8') if sys.version_info[0] == 2 else viter131)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class UploadUserWithUsername_result(object):
    """
    Attributes:
     - se

    """

    def __init__(self, se=None):
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException()
                    self.se.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('UploadUserWithUsername_result')
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class UploadMovieId_args(object):
    """
    Attributes:
     - req_id
     - title
     - rating
     - carrier

    """

    def __init__(self, req_id=None, title=None, rating=None, carrier=None):
        self.req_id = req_id
        self.title = title
        self.rating = rating
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.STRING:
                    self.title = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.I32:
                    self.rating = iprot.readI32()
                else:
                    iprot.skip(ftype)
            elif fid == 4:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype52, _vtype53, _size51 = iprot.readMapBegin()
                    for _i55 in range(_size51):
                        _key56 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        _val57 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key56] = _val57
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('UploadMovieId_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.title is not None:
            oprot.writeFieldBegin('title', TType.STRING, 2)
            oprot.writeString(self.title.encode('utf-8') if sys.version_info[0] == 2 else self.title)
            oprot.writeFieldEnd()
        if self.rating is not None:
            oprot.writeFieldBegin('rating', TType.I32, 3)
            oprot.writeI32(self.rating)
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 4)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter58, viter59 in self.carrier.items():
                oprot.writeString(kiter58.encode('utf-8') if sys.version_info[0] == 2 else kiter58)
                oprot.writeString(viter59.encode('utf-8') if sys.version_info[0] == 2 else viter59)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class UploadMovieId_result(object):
    """
    Attributes:
     - se

    """

    def __init__(self, se=None):
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException()
                    self.se.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('UploadMovieId_result')
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class RegisterMovieId_args(object):
    """
    Attributes:
     - req_id
     - title
     - movie_id
     - carrier

    """

    def __init__(self, req_id=None, title=None, movie_id=None, carrier=None):
        self.req_id = req_id
        self.title = title
        self.movie_id = movie_id
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.STRING:
                    self.title = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.STRING:
                    self.movie_id = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 4:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype61, _vtype62, _size60 = iprot.readMapBegin()
                    for _i64 in range(_size60):
                        _key65 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        _val66 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key65] = _val66
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('RegisterMovieId_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.title is not None:
            oprot.writeFieldBegin('title', TType.STRING, 2)
            oprot.writeString(self.title.encode('utf-8') if sys.version_info[0] == 2 else self.title)
            oprot.writeFieldEnd()
        if self.movie_id is not None:
            oprot.writeFieldBegin('movie_id', TType.STRING, 3)
            oprot.writeString(self.movie_id.encode('utf-8') if sys.version_info[0] == 2 else self.movie_id)
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 4)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter67, viter68 in self.carrier.items():
                oprot.writeString(kiter67.encode('utf-8') if sys.version_info[0] == 2 else kiter67)
                oprot.writeString(viter68.encode('utf-8') if sys.version_info[0] == 2 else viter68)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class RegisterMovieId_result(object):
    """
    Attributes:
     - se

    """

    def __init__(self, se=None):
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException()
                    self.se.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('RegisterMovieId_result')
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class StoreReview_args(object):
    """
    Attributes:
     - req_id
     - review
     - carrier

    """

    def __init__(self, req_id=None, review=None, carrier=None):
        self.req_id = req_id
        self.review = review
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.STRUCT:
                    self.review = Review()
                    self.review.read(iprot)
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype178, _vtype179, _size177 = iprot.readMapBegin()
                    for _i181 in range(_size177):
                        _key182 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        _val183 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key182] = _val183
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('StoreReview_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.review is not None:
            oprot.writeFieldBegin('review', TType.STRUCT, 2)
            self.review.write(oprot)
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 3)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter184, viter185 in self.carrier.items():
                oprot.writeString(kiter184.encode('utf-8') if sys.version_info[0] == 2 else kiter184)
                oprot.writeString(viter185.encode('utf-8') if sys.version_info[0] == 2 else viter185)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class StoreReview_result(object):
    """
    Attributes:
     - se

    """

    def __init__(self, se=None):
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException()
                    self.se.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('StoreReview_result')
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class ReadReviews_args(object):
    """
    Attributes:
     - req_id
     - review_ids
     - carrier

    """

    def __init__(self, req_id=None, review_ids=None, carrier=None):
        self.req_id = req_id
        self.review_ids = review_ids
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.LIST:
                    self.review_ids = []
                    _etype189, _size186 = iprot.readListBegin()
                    for _i190 in range(_size186):
                        _elem191 = iprot.readI64()
                        self.review_ids.append(_elem191)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype193, _vtype194, _size192 = iprot.readMapBegin()
                    for _i196 in range(_size192):
                        _key197 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        _val198 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key197] = _val198
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('ReadReviews_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.review_ids is not None:
            oprot.writeFieldBegin('review_ids', TType.LIST, 2)
            oprot.writeListBegin(TType.I64, len(self.review_ids))
            for iter199 in self.review_ids:
                oprot.writeI64(iter199)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 3)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter200, viter201 in self.carrier.items():
                oprot.writeString(kiter200.encode('utf-8') if sys.version_info[0] == 2 else kiter200)
                oprot.writeString(viter201.encode('utf-8') if sys.version_info[0] == 2 else viter201)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class ReadReviews_result(object):
    """
    Attributes:
     - success
     - se

    """

    def __init__(self, success=None, se=None):
        self.success = success
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 0:
                if ftype == TType.LIST:
                    self.success = []
                    _etype205, _size202 = iprot.readListBegin()
                    for _i206 in range(_size202):
                        _elem207 = Review()
                        _elem207.read(iprot)
                        self.success.append(_elem207)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException()
                    self.se.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('ReadReviews_result')
        if self.success is not None:
            oprot.writeFieldBegin('success', TType.LIST, 0)
            oprot.writeListBegin(TType.STRUCT, len(self.success))
            for iter208 in self.success:
                iter208.write(oprot)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class ReadPage_args(object):
    """
    Attributes:
     - req_id
     - movie_id
     - review_start
     - review_stop
     - carrier

    """

    def __init__(self, req_id=None, movie_id=None, review_start=None, review_stop=None, carrier=None):
        self.req_id = req_id
        self.movie_id = movie_id
        self.review_start = review_start
        self.review_stop = review_stop
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.STRING:
                    self.movie_id = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.I32:
                    self.review_start = iprot.readI32()
                else:
                    iprot.skip(ftype)
            elif fid == 4:
                if ftype == TType.I32:
                    self.review_stop = iprot.readI32()
                else:
                    iprot.skip(ftype)
            elif fid == 5:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype365, _vtype366, _size364 = iprot.readMapBegin()
                    for _i368 in range(_size364):
                        _key369 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        _val370 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key369] = _val370
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('ReadPage_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.movie_id is not None:
            oprot.writeFieldBegin('movie_id', TType.STRING, 2)
            oprot.writeString(self.movie_id.encode('utf-8') if sys.version_info[0] == 2 else self.movie_id)
            oprot.writeFieldEnd()
        if self.review_start is not None:
            oprot.writeFieldBegin('review_start', TType.I32, 3)
            oprot.writeI32(self.review_start)
            oprot.writeFieldEnd()
        if self.review_stop is not None:
            oprot.writeFieldBegin('review_stop', TType.I32, 4)
            oprot.writeI32(self.review_stop)
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 5)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter371, viter372 in self.carrier.items():
                oprot.writeString(kiter371.encode('utf-8') if sys.version_info[0] == 2 else kiter371)
                oprot.writeString(viter372.encode('utf-8') if sys.version_info[0] == 2 else viter372)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class ReadPage_result(object):
    """
    Attributes:
     - success
     - se

    """

    def __init__(self, success=None, se=None):
        self.success = success
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 0:
                if ftype == TType.STRUCT:
                    self.success = Page()
                    self.success.read(iprot)
                else:
                    iprot.skip(ftype)
            elif fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException()
                    self.se.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('ReadPage_result')
        if self.success is not None:
            oprot.writeFieldBegin('success', TType.STRUCT, 0)
            self.success.write(oprot)
            oprot.writeFieldEnd()
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class WriteCastInfo_args(object):
    """
    Attributes:
     - req_id
     - cast_info_id
     - name
     - gender
     - intro
     - carrier

    """

    def __init__(self, req_id=None, cast_info_id=None, name=None, gender=None, intro=None, carrier=None):
        self.req_id = req_id
        self.cast_info_id = cast_info_id
        self.name = name
        self.gender = gender
        self.intro = intro
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.I64:
                    self.cast_info_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.STRING:
                    self.name = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 4:
                if ftype == TType.BOOL:
                    self.gender = iprot.readBool()
                else:
                    iprot.skip(ftype)
            elif fid == 5:
                if ftype == TType.STRING:
                    self.intro = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 6:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype260, _vtype261, _size259 = iprot.readMapBegin()
                    for _i263 in range(_size259):
                        _key264 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        _val265 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key264] = _val265
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('WriteCastInfo_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.cast_info_id is not None:
            oprot.writeFieldBegin('cast_info_id', TType.I64, 2)
            oprot.writeI64(self.cast_info_id)
            oprot.writeFieldEnd()
        if self.name is not None:
            oprot.writeFieldBegin('name', TType.STRING, 3)
            oprot.writeString(self.name.encode('utf-8') if sys.version_info[0] == 2 else self.name)
            oprot.writeFieldEnd()
        if self.gender is not None:
            oprot.writeFieldBegin('gender', TType.BOOL, 4)
            oprot.writeBool(self.gender)
            oprot.writeFieldEnd()
        if self.intro is not None:
            oprot.writeFieldBegin('intro', TType.STRING, 5)
            oprot.writeString(self.intro.encode('utf-8') if sys.version_info[0] == 2 else self.intro)
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 6)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter266, viter267 in self.carrier.items():
                oprot.writeString(kiter266.encode('utf-8') if sys.version_info[0] == 2 else kiter266)
                oprot.writeString(viter267.encode('utf-8') if sys.version_info[0] == 2 else viter267)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class WriteCastInfo_result(object):
    """
    Attributes:
     - se

    """

    def __init__(self, se=None):
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException()
                    self.se.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('WriteCastInfo_result')
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class ReadCastInfo_args(object):
    """
    Attributes:
     - req_id
     - cast_ids
     - carrier

    """

    def __init__(self, req_id=None, cast_ids=None, carrier=None):
        self.req_id = req_id
        self.cast_ids = cast_ids
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.LIST:
                    self.cast_ids = []
                    _etype271, _size268 = iprot.readListBegin()
                    for _i272 in range(_size268):
                        _elem273 = iprot.readI64()
                        self.cast_ids.append(_elem273)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype275, _vtype276, _size274 = iprot.readMapBegin()
                    for _i278 in range(_size274):
                        _key279 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        _val280 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key279] = _val280
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('ReadCastInfo_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.cast_ids is not None:
            oprot.writeFieldBegin('cast_ids', TType.LIST, 2)
            oprot.writeListBegin(TType.I64, len(self.cast_ids))
            for iter281 in self.cast_ids:
                oprot.writeI64(iter281)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 3)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter282, viter283 in self.carrier.items():
                oprot.writeString(kiter282.encode('utf-8') if sys.version_info[0] == 2 else kiter282)
                oprot.writeString(viter283.encode('utf-8') if sys.version_info[0] == 2 else viter283)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class ReadCastInfo_result(object):
    """
    Attributes:
     - success
     - se

    """

    def __init__(self, success=None, se=None):
        self.success = success
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 0:
                if ftype == TType.LIST:
                    self.success = []
                    _etype287, _size284 = iprot.readListBegin()
                    for _i288 in range(_size284):
                        _elem289 = CastInfo()
                        _elem289.read(iprot)
                        self.success.append(_elem289)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException()
                    self.se.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('ReadCastInfo_result')
        if self.success is not None:
            oprot.writeFieldBegin('success', TType.LIST, 0)
            oprot.writeListBegin(TType.STRUCT, len(self.success))
            for iter290 in self.success:
                iter290.write(oprot)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class UploadUserReview_args(object):
    """
    Attributes:
     - req_id
     - user_id
     - review_id
     - timestamp
     - carrier

    """

    def __init__(self, req_id=None, user_id=None, review_id=None, timestamp=None, carrier=None):
        self.req_id = req_id
        self.user_id = user_id
        self.review_id = review_id
        self.timestamp = timestamp
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.I64:
                    self.user_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.I64:
                    self.review_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 4:
                if ftype == TType.I64:
                    self.timestamp = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 5:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype235, _vtype236, _size234 = iprot.readMapBegin()
                    for _i238 in range(_size234):
                        _key239 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        _val240 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key239] = _val240
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('UploadUserReview_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.user_id is not None:
            oprot.writeFieldBegin('user_id', TType.I64, 2)
            oprot.writeI64(self.user_id)
            oprot.writeFieldEnd()
        if self.review_id is not None:
            oprot.writeFieldBegin('review_id', TType.I64, 3)
            oprot.writeI64(self.review_id)
            oprot.writeFieldEnd()
        if self.timestamp is not None:
            oprot.writeFieldBegin('timestamp', TType.I64, 4)
            oprot.writeI64(self.timestamp)
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 5)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter241, viter242 in self.carrier.items():
                oprot.writeString(kiter241.encode('utf-8') if sys.version_info[0] == 2 else kiter241)
                oprot.writeString(viter242.encode('utf-8') if sys.version_info[0] == 2 else viter242)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class UploadUserReview_result(object):
    """
    Attributes:
     - se

    """

    def __init__(self, se=None):
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException()
                    self.se.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('UploadUserReview_result')
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class ReadUserReviews_args(object):
    """
    Attributes:
     - req_id
     - user_id
     - start
     - stop
     - carrier

    """

    def __init__(self, req_id=None, user_id=None, start=None, stop=None, carrier=None):
        self.req_id = req_id
        self.user_id = user_id
        self.start = start
        self.stop = stop
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.I64:
                    self.user_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.I32:
                    self.start = iprot.readI32()
                else:
                    iprot.skip(ftype)
            elif fid == 4:
                if ftype == TType.I32:
                    self.stop = iprot.readI32()
                else:
                    iprot.skip(ftype)
            elif fid == 5:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype244, _vtype245, _size243 = iprot.readMapBegin()
                    for _i247 in range(_size243):
                        _key248 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        _val249 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key248] = _val249
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('ReadUserReviews_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.user_id is not None:
            oprot.writeFieldBegin('user_id', TType.I64, 2)
            oprot.writeI64(self.user_id)
            oprot.writeFieldEnd()
        if self.start is not None:
            oprot.writeFieldBegin('start', TType.I32, 3)
            oprot.writeI32(self.start)
            oprot.writeFieldEnd()
        if self.stop is not None:
            oprot.writeFieldBegin('stop', TType.I32, 4)
            oprot.writeI32(self.stop)
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 5)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter250, viter251 in self.carrier.items():
                oprot.writeString(kiter250.encode('utf-8') if sys.version_info[0] == 2 else kiter250)
                oprot.writeString(viter251.encode('utf-8') if sys.version_info[0] == 2 else viter251)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class ReadUserReviews_result(object):
    """
    Attributes:
     - success
     - se

    """

    def __init__(self, success=None, se=None):
        self.success = success
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 0:
                if ftype == TType.LIST:
                    self.success = []
                    _etype255, _size252 = iprot.readListBegin()
                    for _i256 in range(_size252):
                        _elem257 = Review()
                        _elem257.read(iprot)
                        self.success.append(_elem257)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException()
                    self.se.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('ReadUserReviews_result')
        if self.success is not None:
            oprot.writeFieldBegin('success', TType.LIST, 0)
            oprot.writeListBegin(TType.STRUCT, len(self.success))
            for iter258 in self.success:
                iter258.write(oprot)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class UploadText_args(object):
    """
    Attributes:
     - req_id
     - text
     - carrier

    """

    def __init__(self, req_id=None, text=None, carrier=None):
        self.req_id = req_id
        self.text = text
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.STRING:
                    self.text = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype133, _vtype134, _size132 = iprot.readMapBegin()
                    for _i136 in range(_size132):
                        _key137 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        _val138 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key137] = _val138
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('UploadText_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.text is not None:
            oprot.writeFieldBegin('text', TType.STRING, 2)
            oprot.writeString(self.text.encode('utf-8') if sys.version_info[0] == 2 else self.text)
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 3)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter139, viter140 in self.carrier.items():
                oprot.writeString(kiter139.encode('utf-8') if sys.version_info[0] == 2 else kiter139)
                oprot.writeString(viter140.encode('utf-8') if sys.version_info[0] == 2 else viter140)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class UploadText_result(object):
    """
    Attributes:
     - se

    """

    def __init__(self, se=None):
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException()
                    self.se.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('UploadText_result')
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class UploadRating_args(object):
    """
    Attributes:
     - req_id
     - rating
     - carrier

    """

    def __init__(self, req_id=None, rating=None, carrier=None):
        self.req_id = req_id
        self.rating = rating
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.I32:
                    self.rating = iprot.readI32()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype142, _vtype143, _size141 = iprot.readMapBegin()
                    for _i145 in range(_size141):
                        _key146 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        _val147 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key146] = _val147
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('UploadRating_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.rating is not None:
            oprot.writeFieldBegin('rating', TType.I32, 2)
            oprot.writeI32(self.rating)
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 3)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter148, viter149 in self.carrier.items():
                oprot.writeString(kiter148.encode('utf-8') if sys.version_info[0] == 2 else kiter148)
                oprot.writeString(viter149.encode('utf-8') if sys.version_info[0] == 2 else viter149)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class UploadRating_result(object):
    """
    Attributes:
     - se

    """

    def __init__(self, se=None):
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException()
                    self.se.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('UploadRating_result')
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class UploadMovieId_args(object):
    """
    Attributes:
     - req_id
     - movie_id
     - carrier

    """

    def __init__(self, req_id=None, movie_id=None, carrier=None):
        self.req_id = req_id
        self.movie_id = movie_id
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.STRING:
                    self.movie_id = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype151, _vtype152, _size150 = iprot.readMapBegin()
                    for _i154 in range(_size150):
                        _key155 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        _val156 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key155] = _val156
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('UploadMovieId_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.movie_id is not None:
            oprot.writeFieldBegin('movie_id', TType.STRING, 2)
            oprot.writeString(self.movie_id.encode('utf-8') if sys.version_info[0] == 2 else self.movie_id)
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 3)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter157, viter158 in self.carrier.items():
                oprot.writeString(kiter157.encode('utf-8') if sys.version_info[0] == 2 else kiter157)
                oprot.writeString(viter158.encode('utf-8') if sys.version_info[0] == 2 else viter158)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class UploadMovieId_result(object):
    """
    Attributes:
     - se

    """

    def __init__(self, se=None):
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException()
                    self.se.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('UploadMovieId_result')
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class UploadUniqueId_args(object):
    """
    Attributes:
     - req_id
     - unique_id
     - carrier

    """

    def __init__(self, req_id=None, unique_id=None, carrier=None):
        self.req_id = req_id
        self.unique_id = unique_id
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.I64:
                    self.unique_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype160, _vtype161, _size159 = iprot.readMapBegin()
                    for _i163 in range(_size159):
                        _key164 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        _val165 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key164] = _val165
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('UploadUniqueId_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.unique_id is not None:
            oprot.writeFieldBegin('unique_id', TType.I64, 2)
            oprot.writeI64(self.unique_id)
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 3)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter166, viter167 in self.carrier.items():
                oprot.writeString(kiter166.encode('utf-8') if sys.version_info[0] == 2 else kiter166)
                oprot.writeString(viter167.encode('utf-8') if sys.version_info[0] == 2 else viter167)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class UploadUniqueId_result(object):
    """
    Attributes:
     - se

    """

    def __init__(self, se=None):
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException()
                    self.se.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('UploadUniqueId_result')
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class UploadUserId_args(object):
    """
    Attributes:
     - req_id
     - user_id
     - carrier

    """

    def __init__(self, req_id=None, user_id=None, carrier=None):
        self.req_id = req_id
        self.user_id = user_id
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.I64:
                    self.user_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 4:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype169, _vtype170, _size168 = iprot.readMapBegin()
                    for _i172 in range(_size168):
                        _key173 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        _val174 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key173] = _val174
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('UploadUserId_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.user_id is not None:
            oprot.writeFieldBegin('user_id', TType.I64, 2)
            oprot.writeI64(self.user_id)
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 4)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter175, viter176 in self.carrier.items():
                oprot.writeString(kiter175.encode('utf-8') if sys.version_info[0] == 2 else kiter175)
                oprot.writeString(viter176.encode('utf-8') if sys.version_info[0] == 2 else viter176)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class UploadUserId_result(object):
    """
    Attributes:
     - se

    """

    def __init__(self, se=None):
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException()
                    self.se.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('UploadUserId_result')
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class UploadRating_args(object):
    """
    Attributes:
     - req_id
     - movie_id
     - rating
     - carrier

    """

    def __init__(self, req_id=None, movie_id=None, rating=None, carrier=None):
        self.req_id = req_id
        self.movie_id = movie_id
        self.rating = rating
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.STRING:
                    self.movie_id = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.I32:
                    self.rating = iprot.readI32()
                else:
                    iprot.skip(ftype)
            elif fid == 4:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype79, _vtype80, _size78 = iprot.readMapBegin()
                    for _i82 in range(_size78):
                        _key83 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        _val84 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key83] = _val84
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('UploadRating_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.movie_id is not None:
            oprot.writeFieldBegin('movie_id', TType.STRING, 2)
            oprot.writeString(self.movie_id.encode('utf-8') if sys.version_info[0] == 2 else self.movie_id)
            oprot.writeFieldEnd()
        if self.rating is not None:
            oprot.writeFieldBegin('rating', TType.I32, 3)
            oprot.writeI32(self.rating)
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 4)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter85, viter86 in self.carrier.items():
                oprot.writeString(kiter85.encode('utf-8') if sys.version_info[0] == 2 else kiter85)
                oprot.writeString(viter86.encode('utf-8') if sys.version_info[0] == 2 else viter86)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class UploadRating_result(object):
    """
    Attributes:
     - se

    """

    def __init__(self, se=None):
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException()
                    self.se.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('UploadRating_result')
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class UploadUniqueId_args(object):
    """
    Attributes:
     - req_id
     - carrier

    """

    def __init__(self, req_id=None, carrier=None):
        self.req_id = req_id
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype43, _vtype44, _size42 = iprot.readMapBegin()
                    for _i46 in range(_size42):
                        _key47 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        _val48 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key47] = _val48
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('UploadUniqueId_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 2)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter49, viter50 in self.carrier.items():
                oprot.writeString(kiter49.encode('utf-8') if sys.version_info[0] == 2 else kiter49)
                oprot.writeString(viter50.encode('utf-8') if sys.version_info[0] == 2 else viter50)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class UploadUniqueId_result(object):
    """
    Attributes:
     - se

    """

    def __init__(self, se=None):
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException()
                    self.se.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('UploadUniqueId_result')
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

def main():
    register_movies()
    register_users()
    processes = []
    for i in range(1):
        p = Process(target=worker)
        processes.append(p)
        p.start()
    for i in range(1):
        processes[i].join()
    print('finished')

# Node: register_movies
# Node: register_users
# Node: Process
# Node: start
class ReadHomeTimeline_args(object):
    """
    Attributes:
     - req_id
     - user_id
     - start
     - stop
     - carrier

    """

    def __init__(self, req_id=None, user_id=None, start=None, stop=None, carrier=None):
        self.req_id = req_id
        self.user_id = user_id
        self.start = start
        self.stop = stop
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.I64:
                    self.user_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.I32:
                    self.start = iprot.readI32()
                else:
                    iprot.skip(ftype)
            elif fid == 4:
                if ftype == TType.I32:
                    self.stop = iprot.readI32()
                else:
                    iprot.skip(ftype)
            elif fid == 5:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype172, _vtype173, _size171 = iprot.readMapBegin()
                    for _i175 in range(_size171):
                        _key176 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        _val177 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key176] = _val177
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('ReadHomeTimeline_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.user_id is not None:
            oprot.writeFieldBegin('user_id', TType.I64, 2)
            oprot.writeI64(self.user_id)
            oprot.writeFieldEnd()
        if self.start is not None:
            oprot.writeFieldBegin('start', TType.I32, 3)
            oprot.writeI32(self.start)
            oprot.writeFieldEnd()
        if self.stop is not None:
            oprot.writeFieldBegin('stop', TType.I32, 4)
            oprot.writeI32(self.stop)
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 5)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter178, viter179 in self.carrier.items():
                oprot.writeString(kiter178.encode('utf-8') if sys.version_info[0] == 2 else kiter178)
                oprot.writeString(viter179.encode('utf-8') if sys.version_info[0] == 2 else viter179)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class ReadHomeTimeline_result(object):
    """
    Attributes:
     - success
     - se

    """

    def __init__(self, success=None, se=None):
        self.success = success
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 0:
                if ftype == TType.LIST:
                    self.success = []
                    _etype183, _size180 = iprot.readListBegin()
                    for _i184 in range(_size180):
                        _elem185 = Post()
                        _elem185.read(iprot)
                        self.success.append(_elem185)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('ReadHomeTimeline_result')
        if self.success is not None:
            oprot.writeFieldBegin('success', TType.LIST, 0)
            oprot.writeListBegin(TType.STRUCT, len(self.success))
            for iter186 in self.success:
                iter186.write(oprot)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class WriteHomeTimeline_args(object):
    """
    Attributes:
     - req_id
     - post_id
     - user_id
     - timestamp
     - user_mentions_id
     - carrier

    """

    def __init__(self, req_id=None, post_id=None, user_id=None, timestamp=None, user_mentions_id=None, carrier=None):
        self.req_id = req_id
        self.post_id = post_id
        self.user_id = user_id
        self.timestamp = timestamp
        self.user_mentions_id = user_mentions_id
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.I64:
                    self.post_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.I64:
                    self.user_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 4:
                if ftype == TType.I64:
                    self.timestamp = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 5:
                if ftype == TType.LIST:
                    self.user_mentions_id = []
                    _etype190, _size187 = iprot.readListBegin()
                    for _i191 in range(_size187):
                        _elem192 = iprot.readI64()
                        self.user_mentions_id.append(_elem192)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 6:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype194, _vtype195, _size193 = iprot.readMapBegin()
                    for _i197 in range(_size193):
                        _key198 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        _val199 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key198] = _val199
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('WriteHomeTimeline_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.post_id is not None:
            oprot.writeFieldBegin('post_id', TType.I64, 2)
            oprot.writeI64(self.post_id)
            oprot.writeFieldEnd()
        if self.user_id is not None:
            oprot.writeFieldBegin('user_id', TType.I64, 3)
            oprot.writeI64(self.user_id)
            oprot.writeFieldEnd()
        if self.timestamp is not None:
            oprot.writeFieldBegin('timestamp', TType.I64, 4)
            oprot.writeI64(self.timestamp)
            oprot.writeFieldEnd()
        if self.user_mentions_id is not None:
            oprot.writeFieldBegin('user_mentions_id', TType.LIST, 5)
            oprot.writeListBegin(TType.I64, len(self.user_mentions_id))
            for iter200 in self.user_mentions_id:
                oprot.writeI64(iter200)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 6)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter201, viter202 in self.carrier.items():
                oprot.writeString(kiter201.encode('utf-8') if sys.version_info[0] == 2 else kiter201)
                oprot.writeString(viter202.encode('utf-8') if sys.version_info[0] == 2 else viter202)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class WriteHomeTimeline_result(object):
    """
    Attributes:
     - se

    """

    def __init__(self, se=None):
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('WriteHomeTimeline_result')
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class ComposeText_args(object):
    """
    Attributes:
     - req_id
     - text
     - carrier

    """

    def __init__(self, req_id=None, text=None, carrier=None):
        self.req_id = req_id
        self.text = text
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.STRING:
                    self.text = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype45, _vtype46, _size44 = iprot.readMapBegin()
                    for _i48 in range(_size44):
                        _key49 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        _val50 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key49] = _val50
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('ComposeText_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.text is not None:
            oprot.writeFieldBegin('text', TType.STRING, 2)
            oprot.writeString(self.text.encode('utf-8') if sys.version_info[0] == 2 else self.text)
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 3)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter51, viter52 in self.carrier.items():
                oprot.writeString(kiter51.encode('utf-8') if sys.version_info[0] == 2 else kiter51)
                oprot.writeString(viter52.encode('utf-8') if sys.version_info[0] == 2 else viter52)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class ComposeText_result(object):
    """
    Attributes:
     - success
     - se

    """

    def __init__(self, success=None, se=None):
        self.success = success
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 0:
                if ftype == TType.STRUCT:
                    self.success = TextServiceReturn()
                    self.success.read(iprot)
                else:
                    iprot.skip(ftype)
            elif fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('ComposeText_result')
        if self.success is not None:
            oprot.writeFieldBegin('success', TType.STRUCT, 0)
            self.success.write(oprot)
            oprot.writeFieldEnd()
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class ComposeMedia_args(object):
    """
    Attributes:
     - req_id
     - media_types
     - media_ids
     - carrier

    """

    def __init__(self, req_id=None, media_types=None, media_ids=None, carrier=None):
        self.req_id = req_id
        self.media_types = media_types
        self.media_ids = media_ids
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.LIST:
                    self.media_types = []
                    _etype377, _size374 = iprot.readListBegin()
                    for _i378 in range(_size374):
                        _elem379 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        self.media_types.append(_elem379)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.LIST:
                    self.media_ids = []
                    _etype383, _size380 = iprot.readListBegin()
                    for _i384 in range(_size380):
                        _elem385 = iprot.readI64()
                        self.media_ids.append(_elem385)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 4:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype387, _vtype388, _size386 = iprot.readMapBegin()
                    for _i390 in range(_size386):
                        _key391 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        _val392 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key391] = _val392
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('ComposeMedia_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.media_types is not None:
            oprot.writeFieldBegin('media_types', TType.LIST, 2)
            oprot.writeListBegin(TType.STRING, len(self.media_types))
            for iter393 in self.media_types:
                oprot.writeString(iter393.encode('utf-8') if sys.version_info[0] == 2 else iter393)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        if self.media_ids is not None:
            oprot.writeFieldBegin('media_ids', TType.LIST, 3)
            oprot.writeListBegin(TType.I64, len(self.media_ids))
            for iter394 in self.media_ids:
                oprot.writeI64(iter394)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 4)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter395, viter396 in self.carrier.items():
                oprot.writeString(kiter395.encode('utf-8') if sys.version_info[0] == 2 else kiter395)
                oprot.writeString(viter396.encode('utf-8') if sys.version_info[0] == 2 else viter396)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class ComposeMedia_result(object):
    """
    Attributes:
     - success
     - se

    """

    def __init__(self, success=None, se=None):
        self.success = success
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 0:
                if ftype == TType.LIST:
                    self.success = []
                    _etype400, _size397 = iprot.readListBegin()
                    for _i401 in range(_size397):
                        _elem402 = Media()
                        _elem402.read(iprot)
                        self.success.append(_elem402)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('ComposeMedia_result')
        if self.success is not None:
            oprot.writeFieldBegin('success', TType.LIST, 0)
            oprot.writeListBegin(TType.STRUCT, len(self.success))
            for iter403 in self.success:
                iter403.write(oprot)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class ComposeUrls_args(object):
    """
    Attributes:
     - req_id
     - urls
     - carrier

    """

    def __init__(self, req_id=None, urls=None, carrier=None):
        self.req_id = req_id
        self.urls = urls
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.LIST:
                    self.urls = []
                    _etype331, _size328 = iprot.readListBegin()
                    for _i332 in range(_size328):
                        _elem333 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        self.urls.append(_elem333)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype335, _vtype336, _size334 = iprot.readMapBegin()
                    for _i338 in range(_size334):
                        _key339 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        _val340 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key339] = _val340
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('ComposeUrls_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.urls is not None:
            oprot.writeFieldBegin('urls', TType.LIST, 2)
            oprot.writeListBegin(TType.STRING, len(self.urls))
            for iter341 in self.urls:
                oprot.writeString(iter341.encode('utf-8') if sys.version_info[0] == 2 else iter341)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 3)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter342, viter343 in self.carrier.items():
                oprot.writeString(kiter342.encode('utf-8') if sys.version_info[0] == 2 else kiter342)
                oprot.writeString(viter343.encode('utf-8') if sys.version_info[0] == 2 else viter343)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class ComposeUrls_result(object):
    """
    Attributes:
     - success
     - se

    """

    def __init__(self, success=None, se=None):
        self.success = success
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 0:
                if ftype == TType.LIST:
                    self.success = []
                    _etype347, _size344 = iprot.readListBegin()
                    for _i348 in range(_size344):
                        _elem349 = Url()
                        _elem349.read(iprot)
                        self.success.append(_elem349)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('ComposeUrls_result')
        if self.success is not None:
            oprot.writeFieldBegin('success', TType.LIST, 0)
            oprot.writeListBegin(TType.STRUCT, len(self.success))
            for iter350 in self.success:
                iter350.write(oprot)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class GetExtendedUrls_args(object):
    """
    Attributes:
     - req_id
     - shortened_urls
     - carrier

    """

    def __init__(self, req_id=None, shortened_urls=None, carrier=None):
        self.req_id = req_id
        self.shortened_urls = shortened_urls
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.LIST:
                    self.shortened_urls = []
                    _etype354, _size351 = iprot.readListBegin()
                    for _i355 in range(_size351):
                        _elem356 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        self.shortened_urls.append(_elem356)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype358, _vtype359, _size357 = iprot.readMapBegin()
                    for _i361 in range(_size357):
                        _key362 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        _val363 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key362] = _val363
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('GetExtendedUrls_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.shortened_urls is not None:
            oprot.writeFieldBegin('shortened_urls', TType.LIST, 2)
            oprot.writeListBegin(TType.STRING, len(self.shortened_urls))
            for iter364 in self.shortened_urls:
                oprot.writeString(iter364.encode('utf-8') if sys.version_info[0] == 2 else iter364)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 3)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter365, viter366 in self.carrier.items():
                oprot.writeString(kiter365.encode('utf-8') if sys.version_info[0] == 2 else kiter365)
                oprot.writeString(viter366.encode('utf-8') if sys.version_info[0] == 2 else viter366)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class GetExtendedUrls_result(object):
    """
    Attributes:
     - success
     - se

    """

    def __init__(self, success=None, se=None):
        self.success = success
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 0:
                if ftype == TType.LIST:
                    self.success = []
                    _etype370, _size367 = iprot.readListBegin()
                    for _i371 in range(_size367):
                        _elem372 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        self.success.append(_elem372)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('GetExtendedUrls_result')
        if self.success is not None:
            oprot.writeFieldBegin('success', TType.LIST, 0)
            oprot.writeListBegin(TType.STRING, len(self.success))
            for iter373 in self.success:
                oprot.writeString(iter373.encode('utf-8') if sys.version_info[0] == 2 else iter373)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class StorePost_args(object):
    """
    Attributes:
     - req_id
     - post
     - carrier

    """

    def __init__(self, req_id=None, post=None, carrier=None):
        self.req_id = req_id
        self.post = post
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.STRUCT:
                    self.post = Post()
                    self.post.read(iprot)
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype131, _vtype132, _size130 = iprot.readMapBegin()
                    for _i134 in range(_size130):
                        _key135 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        _val136 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key135] = _val136
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('StorePost_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.post is not None:
            oprot.writeFieldBegin('post', TType.STRUCT, 2)
            self.post.write(oprot)
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 3)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter137, viter138 in self.carrier.items():
                oprot.writeString(kiter137.encode('utf-8') if sys.version_info[0] == 2 else kiter137)
                oprot.writeString(viter138.encode('utf-8') if sys.version_info[0] == 2 else viter138)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class StorePost_result(object):
    """
    Attributes:
     - se

    """

    def __init__(self, se=None):
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('StorePost_result')
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class ReadPost_args(object):
    """
    Attributes:
     - req_id
     - post_id
     - carrier

    """

    def __init__(self, req_id=None, post_id=None, carrier=None):
        self.req_id = req_id
        self.post_id = post_id
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.I64:
                    self.post_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype140, _vtype141, _size139 = iprot.readMapBegin()
                    for _i143 in range(_size139):
                        _key144 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        _val145 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key144] = _val145
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('ReadPost_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.post_id is not None:
            oprot.writeFieldBegin('post_id', TType.I64, 2)
            oprot.writeI64(self.post_id)
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 3)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter146, viter147 in self.carrier.items():
                oprot.writeString(kiter146.encode('utf-8') if sys.version_info[0] == 2 else kiter146)
                oprot.writeString(viter147.encode('utf-8') if sys.version_info[0] == 2 else viter147)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class ReadPost_result(object):
    """
    Attributes:
     - success
     - se

    """

    def __init__(self, success=None, se=None):
        self.success = success
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 0:
                if ftype == TType.STRUCT:
                    self.success = Post()
                    self.success.read(iprot)
                else:
                    iprot.skip(ftype)
            elif fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('ReadPost_result')
        if self.success is not None:
            oprot.writeFieldBegin('success', TType.STRUCT, 0)
            self.success.write(oprot)
            oprot.writeFieldEnd()
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class ReadPosts_args(object):
    """
    Attributes:
     - req_id
     - post_ids
     - carrier

    """

    def __init__(self, req_id=None, post_ids=None, carrier=None):
        self.req_id = req_id
        self.post_ids = post_ids
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.LIST:
                    self.post_ids = []
                    _etype151, _size148 = iprot.readListBegin()
                    for _i152 in range(_size148):
                        _elem153 = iprot.readI64()
                        self.post_ids.append(_elem153)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype155, _vtype156, _size154 = iprot.readMapBegin()
                    for _i158 in range(_size154):
                        _key159 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        _val160 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key159] = _val160
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('ReadPosts_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.post_ids is not None:
            oprot.writeFieldBegin('post_ids', TType.LIST, 2)
            oprot.writeListBegin(TType.I64, len(self.post_ids))
            for iter161 in self.post_ids:
                oprot.writeI64(iter161)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 3)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter162, viter163 in self.carrier.items():
                oprot.writeString(kiter162.encode('utf-8') if sys.version_info[0] == 2 else kiter162)
                oprot.writeString(viter163.encode('utf-8') if sys.version_info[0] == 2 else viter163)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class ReadPosts_result(object):
    """
    Attributes:
     - success
     - se

    """

    def __init__(self, success=None, se=None):
        self.success = success
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 0:
                if ftype == TType.LIST:
                    self.success = []
                    _etype167, _size164 = iprot.readListBegin()
                    for _i168 in range(_size164):
                        _elem169 = Post()
                        _elem169.read(iprot)
                        self.success.append(_elem169)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('ReadPosts_result')
        if self.success is not None:
            oprot.writeFieldBegin('success', TType.LIST, 0)
            oprot.writeListBegin(TType.STRUCT, len(self.success))
            for iter170 in self.success:
                iter170.write(oprot)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class User(object):
    """
    Attributes:
     - user_id
     - first_name
     - last_name
     - username
     - password_hashed
     - salt

    """

    def __init__(self, user_id=None, first_name=None, last_name=None, username=None, password_hashed=None, salt=None):
        self.user_id = user_id
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.password_hashed = password_hashed
        self.salt = salt

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.user_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.STRING:
                    self.first_name = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.STRING:
                    self.last_name = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 4:
                if ftype == TType.STRING:
                    self.username = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 5:
                if ftype == TType.STRING:
                    self.password_hashed = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 6:
                if ftype == TType.STRING:
                    self.salt = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('User')
        if self.user_id is not None:
            oprot.writeFieldBegin('user_id', TType.I64, 1)
            oprot.writeI64(self.user_id)
            oprot.writeFieldEnd()
        if self.first_name is not None:
            oprot.writeFieldBegin('first_name', TType.STRING, 2)
            oprot.writeString(self.first_name.encode('utf-8') if sys.version_info[0] == 2 else self.first_name)
            oprot.writeFieldEnd()
        if self.last_name is not None:
            oprot.writeFieldBegin('last_name', TType.STRING, 3)
            oprot.writeString(self.last_name.encode('utf-8') if sys.version_info[0] == 2 else self.last_name)
            oprot.writeFieldEnd()
        if self.username is not None:
            oprot.writeFieldBegin('username', TType.STRING, 4)
            oprot.writeString(self.username.encode('utf-8') if sys.version_info[0] == 2 else self.username)
            oprot.writeFieldEnd()
        if self.password_hashed is not None:
            oprot.writeFieldBegin('password_hashed', TType.STRING, 5)
            oprot.writeString(self.password_hashed.encode('utf-8') if sys.version_info[0] == 2 else self.password_hashed)
            oprot.writeFieldEnd()
        if self.salt is not None:
            oprot.writeFieldBegin('salt', TType.STRING, 6)
            oprot.writeString(self.salt.encode('utf-8') if sys.version_info[0] == 2 else self.salt)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class ServiceException(TException):
    """
    Attributes:
     - errorCode
     - message

    """

    def __init__(self, errorCode=None, message=None):
        super(ServiceException, self).__setattr__('errorCode', errorCode)
        super(ServiceException, self).__setattr__('message', message)

    def __setattr__(self, *args):
        raise TypeError("can't modify immutable instance")

    def __delattr__(self, *args):
        raise TypeError("can't modify immutable instance")

    def __hash__(self):
        return hash(self.__class__) ^ hash((self.errorCode, self.message))

    @classmethod
    def read(cls, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (cls.thrift_spec is not None):
            return iprot._fast_decode(None, iprot, [cls, cls.thrift_spec])
        iprot.readStructBegin()
        errorCode = None
        message = None
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I32:
                    errorCode = iprot.readI32()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.STRING:
                    message = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()
        return cls(errorCode=errorCode, message=message)

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('ServiceException')
        if self.errorCode is not None:
            oprot.writeFieldBegin('errorCode', TType.I32, 1)
            oprot.writeI32(self.errorCode)
            oprot.writeFieldEnd()
        if self.message is not None:
            oprot.writeFieldBegin('message', TType.STRING, 2)
            oprot.writeString(self.message.encode('utf-8') if sys.version_info[0] == 2 else self.message)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __str__(self):
        return repr(self)

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class Media(object):
    """
    Attributes:
     - media_id
     - media_type

    """

    def __init__(self, media_id=None, media_type=None):
        self.media_id = media_id
        self.media_type = media_type

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.media_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.STRING:
                    self.media_type = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('Media')
        if self.media_id is not None:
            oprot.writeFieldBegin('media_id', TType.I64, 1)
            oprot.writeI64(self.media_id)
            oprot.writeFieldEnd()
        if self.media_type is not None:
            oprot.writeFieldBegin('media_type', TType.STRING, 2)
            oprot.writeString(self.media_type.encode('utf-8') if sys.version_info[0] == 2 else self.media_type)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class Url(object):
    """
    Attributes:
     - shortened_url
     - expanded_url

    """

    def __init__(self, shortened_url=None, expanded_url=None):
        self.shortened_url = shortened_url
        self.expanded_url = expanded_url

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.STRING:
                    self.shortened_url = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.STRING:
                    self.expanded_url = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('Url')
        if self.shortened_url is not None:
            oprot.writeFieldBegin('shortened_url', TType.STRING, 1)
            oprot.writeString(self.shortened_url.encode('utf-8') if sys.version_info[0] == 2 else self.shortened_url)
            oprot.writeFieldEnd()
        if self.expanded_url is not None:
            oprot.writeFieldBegin('expanded_url', TType.STRING, 2)
            oprot.writeString(self.expanded_url.encode('utf-8') if sys.version_info[0] == 2 else self.expanded_url)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class UserMention(object):
    """
    Attributes:
     - user_id
     - username

    """

    def __init__(self, user_id=None, username=None):
        self.user_id = user_id
        self.username = username

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.user_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.STRING:
                    self.username = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('UserMention')
        if self.user_id is not None:
            oprot.writeFieldBegin('user_id', TType.I64, 1)
            oprot.writeI64(self.user_id)
            oprot.writeFieldEnd()
        if self.username is not None:
            oprot.writeFieldBegin('username', TType.STRING, 2)
            oprot.writeString(self.username.encode('utf-8') if sys.version_info[0] == 2 else self.username)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class Creator(object):
    """
    Attributes:
     - user_id
     - username

    """

    def __init__(self, user_id=None, username=None):
        self.user_id = user_id
        self.username = username

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.user_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.STRING:
                    self.username = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('Creator')
        if self.user_id is not None:
            oprot.writeFieldBegin('user_id', TType.I64, 1)
            oprot.writeI64(self.user_id)
            oprot.writeFieldEnd()
        if self.username is not None:
            oprot.writeFieldBegin('username', TType.STRING, 2)
            oprot.writeString(self.username.encode('utf-8') if sys.version_info[0] == 2 else self.username)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class TextServiceReturn(object):
    """
    Attributes:
     - text
     - user_mentions
     - urls

    """

    def __init__(self, text=None, user_mentions=None, urls=None):
        self.text = text
        self.user_mentions = user_mentions
        self.urls = urls

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.STRING:
                    self.text = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.LIST:
                    self.user_mentions = []
                    _etype3, _size0 = iprot.readListBegin()
                    for _i4 in range(_size0):
                        _elem5 = UserMention()
                        _elem5.read(iprot)
                        self.user_mentions.append(_elem5)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.LIST:
                    self.urls = []
                    _etype9, _size6 = iprot.readListBegin()
                    for _i10 in range(_size6):
                        _elem11 = Url()
                        _elem11.read(iprot)
                        self.urls.append(_elem11)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('TextServiceReturn')
        if self.text is not None:
            oprot.writeFieldBegin('text', TType.STRING, 1)
            oprot.writeString(self.text.encode('utf-8') if sys.version_info[0] == 2 else self.text)
            oprot.writeFieldEnd()
        if self.user_mentions is not None:
            oprot.writeFieldBegin('user_mentions', TType.LIST, 2)
            oprot.writeListBegin(TType.STRUCT, len(self.user_mentions))
            for iter12 in self.user_mentions:
                iter12.write(oprot)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        if self.urls is not None:
            oprot.writeFieldBegin('urls', TType.LIST, 3)
            oprot.writeListBegin(TType.STRUCT, len(self.urls))
            for iter13 in self.urls:
                iter13.write(oprot)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class Post(object):
    """
    Attributes:
     - post_id
     - creator
     - req_id
     - text
     - user_mentions
     - media
     - urls
     - timestamp
     - post_type

    """

    def __init__(self, post_id=None, creator=None, req_id=None, text=None, user_mentions=None, media=None, urls=None, timestamp=None, post_type=None):
        self.post_id = post_id
        self.creator = creator
        self.req_id = req_id
        self.text = text
        self.user_mentions = user_mentions
        self.media = media
        self.urls = urls
        self.timestamp = timestamp
        self.post_type = post_type

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.post_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.STRUCT:
                    self.creator = Creator()
                    self.creator.read(iprot)
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 4:
                if ftype == TType.STRING:
                    self.text = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 5:
                if ftype == TType.LIST:
                    self.user_mentions = []
                    _etype17, _size14 = iprot.readListBegin()
                    for _i18 in range(_size14):
                        _elem19 = UserMention()
                        _elem19.read(iprot)
                        self.user_mentions.append(_elem19)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 6:
                if ftype == TType.LIST:
                    self.media = []
                    _etype23, _size20 = iprot.readListBegin()
                    for _i24 in range(_size20):
                        _elem25 = Media()
                        _elem25.read(iprot)
                        self.media.append(_elem25)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 7:
                if ftype == TType.LIST:
                    self.urls = []
                    _etype29, _size26 = iprot.readListBegin()
                    for _i30 in range(_size26):
                        _elem31 = Url()
                        _elem31.read(iprot)
                        self.urls.append(_elem31)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 8:
                if ftype == TType.I64:
                    self.timestamp = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 9:
                if ftype == TType.I32:
                    self.post_type = iprot.readI32()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('Post')
        if self.post_id is not None:
            oprot.writeFieldBegin('post_id', TType.I64, 1)
            oprot.writeI64(self.post_id)
            oprot.writeFieldEnd()
        if self.creator is not None:
            oprot.writeFieldBegin('creator', TType.STRUCT, 2)
            self.creator.write(oprot)
            oprot.writeFieldEnd()
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 3)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.text is not None:
            oprot.writeFieldBegin('text', TType.STRING, 4)
            oprot.writeString(self.text.encode('utf-8') if sys.version_info[0] == 2 else self.text)
            oprot.writeFieldEnd()
        if self.user_mentions is not None:
            oprot.writeFieldBegin('user_mentions', TType.LIST, 5)
            oprot.writeListBegin(TType.STRUCT, len(self.user_mentions))
            for iter32 in self.user_mentions:
                iter32.write(oprot)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        if self.media is not None:
            oprot.writeFieldBegin('media', TType.LIST, 6)
            oprot.writeListBegin(TType.STRUCT, len(self.media))
            for iter33 in self.media:
                iter33.write(oprot)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        if self.urls is not None:
            oprot.writeFieldBegin('urls', TType.LIST, 7)
            oprot.writeListBegin(TType.STRUCT, len(self.urls))
            for iter34 in self.urls:
                iter34.write(oprot)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        if self.timestamp is not None:
            oprot.writeFieldBegin('timestamp', TType.I64, 8)
            oprot.writeI64(self.timestamp)
            oprot.writeFieldEnd()
        if self.post_type is not None:
            oprot.writeFieldBegin('post_type', TType.I32, 9)
            oprot.writeI32(self.post_type)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class GetFollowers_args(object):
    """
    Attributes:
     - req_id
     - user_id
     - carrier

    """

    def __init__(self, req_id=None, user_id=None, carrier=None):
        self.req_id = req_id
        self.user_id = user_id
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.I64:
                    self.user_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype229, _vtype230, _size228 = iprot.readMapBegin()
                    for _i232 in range(_size228):
                        _key233 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        _val234 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key233] = _val234
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('GetFollowers_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.user_id is not None:
            oprot.writeFieldBegin('user_id', TType.I64, 2)
            oprot.writeI64(self.user_id)
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 3)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter235, viter236 in self.carrier.items():
                oprot.writeString(kiter235.encode('utf-8') if sys.version_info[0] == 2 else kiter235)
                oprot.writeString(viter236.encode('utf-8') if sys.version_info[0] == 2 else viter236)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class GetFollowers_result(object):
    """
    Attributes:
     - success
     - se

    """

    def __init__(self, success=None, se=None):
        self.success = success
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 0:
                if ftype == TType.LIST:
                    self.success = []
                    _etype240, _size237 = iprot.readListBegin()
                    for _i241 in range(_size237):
                        _elem242 = iprot.readI64()
                        self.success.append(_elem242)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('GetFollowers_result')
        if self.success is not None:
            oprot.writeFieldBegin('success', TType.LIST, 0)
            oprot.writeListBegin(TType.I64, len(self.success))
            for iter243 in self.success:
                oprot.writeI64(iter243)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class GetFollowees_args(object):
    """
    Attributes:
     - req_id
     - user_id
     - carrier

    """

    def __init__(self, req_id=None, user_id=None, carrier=None):
        self.req_id = req_id
        self.user_id = user_id
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.I64:
                    self.user_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype245, _vtype246, _size244 = iprot.readMapBegin()
                    for _i248 in range(_size244):
                        _key249 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        _val250 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key249] = _val250
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('GetFollowees_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.user_id is not None:
            oprot.writeFieldBegin('user_id', TType.I64, 2)
            oprot.writeI64(self.user_id)
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 3)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter251, viter252 in self.carrier.items():
                oprot.writeString(kiter251.encode('utf-8') if sys.version_info[0] == 2 else kiter251)
                oprot.writeString(viter252.encode('utf-8') if sys.version_info[0] == 2 else viter252)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class GetFollowees_result(object):
    """
    Attributes:
     - success
     - se

    """

    def __init__(self, success=None, se=None):
        self.success = success
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 0:
                if ftype == TType.LIST:
                    self.success = []
                    _etype256, _size253 = iprot.readListBegin()
                    for _i257 in range(_size253):
                        _elem258 = iprot.readI64()
                        self.success.append(_elem258)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('GetFollowees_result')
        if self.success is not None:
            oprot.writeFieldBegin('success', TType.LIST, 0)
            oprot.writeListBegin(TType.I64, len(self.success))
            for iter259 in self.success:
                oprot.writeI64(iter259)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class Follow_args(object):
    """
    Attributes:
     - req_id
     - user_id
     - followee_id
     - carrier

    """

    def __init__(self, req_id=None, user_id=None, followee_id=None, carrier=None):
        self.req_id = req_id
        self.user_id = user_id
        self.followee_id = followee_id
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.I64:
                    self.user_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.I64:
                    self.followee_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 4:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype261, _vtype262, _size260 = iprot.readMapBegin()
                    for _i264 in range(_size260):
                        _key265 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        _val266 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key265] = _val266
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('Follow_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.user_id is not None:
            oprot.writeFieldBegin('user_id', TType.I64, 2)
            oprot.writeI64(self.user_id)
            oprot.writeFieldEnd()
        if self.followee_id is not None:
            oprot.writeFieldBegin('followee_id', TType.I64, 3)
            oprot.writeI64(self.followee_id)
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 4)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter267, viter268 in self.carrier.items():
                oprot.writeString(kiter267.encode('utf-8') if sys.version_info[0] == 2 else kiter267)
                oprot.writeString(viter268.encode('utf-8') if sys.version_info[0] == 2 else viter268)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class Follow_result(object):
    """
    Attributes:
     - se

    """

    def __init__(self, se=None):
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('Follow_result')
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class Unfollow_args(object):
    """
    Attributes:
     - req_id
     - user_id
     - followee_id
     - carrier

    """

    def __init__(self, req_id=None, user_id=None, followee_id=None, carrier=None):
        self.req_id = req_id
        self.user_id = user_id
        self.followee_id = followee_id
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.I64:
                    self.user_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.I64:
                    self.followee_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 4:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype270, _vtype271, _size269 = iprot.readMapBegin()
                    for _i273 in range(_size269):
                        _key274 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        _val275 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key274] = _val275
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('Unfollow_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.user_id is not None:
            oprot.writeFieldBegin('user_id', TType.I64, 2)
            oprot.writeI64(self.user_id)
            oprot.writeFieldEnd()
        if self.followee_id is not None:
            oprot.writeFieldBegin('followee_id', TType.I64, 3)
            oprot.writeI64(self.followee_id)
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 4)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter276, viter277 in self.carrier.items():
                oprot.writeString(kiter276.encode('utf-8') if sys.version_info[0] == 2 else kiter276)
                oprot.writeString(viter277.encode('utf-8') if sys.version_info[0] == 2 else viter277)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class Unfollow_result(object):
    """
    Attributes:
     - se

    """

    def __init__(self, se=None):
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('Unfollow_result')
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class FollowWithUsername_args(object):
    """
    Attributes:
     - req_id
     - user_usernmae
     - followee_username
     - carrier

    """

    def __init__(self, req_id=None, user_usernmae=None, followee_username=None, carrier=None):
        self.req_id = req_id
        self.user_usernmae = user_usernmae
        self.followee_username = followee_username
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.STRING:
                    self.user_usernmae = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.STRING:
                    self.followee_username = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 4:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype279, _vtype280, _size278 = iprot.readMapBegin()
                    for _i282 in range(_size278):
                        _key283 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        _val284 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key283] = _val284
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('FollowWithUsername_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.user_usernmae is not None:
            oprot.writeFieldBegin('user_usernmae', TType.STRING, 2)
            oprot.writeString(self.user_usernmae.encode('utf-8') if sys.version_info[0] == 2 else self.user_usernmae)
            oprot.writeFieldEnd()
        if self.followee_username is not None:
            oprot.writeFieldBegin('followee_username', TType.STRING, 3)
            oprot.writeString(self.followee_username.encode('utf-8') if sys.version_info[0] == 2 else self.followee_username)
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 4)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter285, viter286 in self.carrier.items():
                oprot.writeString(kiter285.encode('utf-8') if sys.version_info[0] == 2 else kiter285)
                oprot.writeString(viter286.encode('utf-8') if sys.version_info[0] == 2 else viter286)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class FollowWithUsername_result(object):
    """
    Attributes:
     - se

    """

    def __init__(self, se=None):
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('FollowWithUsername_result')
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class UnfollowWithUsername_args(object):
    """
    Attributes:
     - req_id
     - user_usernmae
     - followee_username
     - carrier

    """

    def __init__(self, req_id=None, user_usernmae=None, followee_username=None, carrier=None):
        self.req_id = req_id
        self.user_usernmae = user_usernmae
        self.followee_username = followee_username
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.STRING:
                    self.user_usernmae = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.STRING:
                    self.followee_username = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 4:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype288, _vtype289, _size287 = iprot.readMapBegin()
                    for _i291 in range(_size287):
                        _key292 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        _val293 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key292] = _val293
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('UnfollowWithUsername_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.user_usernmae is not None:
            oprot.writeFieldBegin('user_usernmae', TType.STRING, 2)
            oprot.writeString(self.user_usernmae.encode('utf-8') if sys.version_info[0] == 2 else self.user_usernmae)
            oprot.writeFieldEnd()
        if self.followee_username is not None:
            oprot.writeFieldBegin('followee_username', TType.STRING, 3)
            oprot.writeString(self.followee_username.encode('utf-8') if sys.version_info[0] == 2 else self.followee_username)
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 4)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter294, viter295 in self.carrier.items():
                oprot.writeString(kiter294.encode('utf-8') if sys.version_info[0] == 2 else kiter294)
                oprot.writeString(viter295.encode('utf-8') if sys.version_info[0] == 2 else viter295)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class UnfollowWithUsername_result(object):
    """
    Attributes:
     - se

    """

    def __init__(self, se=None):
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('UnfollowWithUsername_result')
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class InsertUser_args(object):
    """
    Attributes:
     - req_id
     - user_id
     - carrier

    """

    def __init__(self, req_id=None, user_id=None, carrier=None):
        self.req_id = req_id
        self.user_id = user_id
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.I64:
                    self.user_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype297, _vtype298, _size296 = iprot.readMapBegin()
                    for _i300 in range(_size296):
                        _key301 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        _val302 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key301] = _val302
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('InsertUser_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.user_id is not None:
            oprot.writeFieldBegin('user_id', TType.I64, 2)
            oprot.writeI64(self.user_id)
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 3)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter303, viter304 in self.carrier.items():
                oprot.writeString(kiter303.encode('utf-8') if sys.version_info[0] == 2 else kiter303)
                oprot.writeString(viter304.encode('utf-8') if sys.version_info[0] == 2 else viter304)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class InsertUser_result(object):
    """
    Attributes:
     - se

    """

    def __init__(self, se=None):
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('InsertUser_result')
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class RegisterUser_args(object):
    """
    Attributes:
     - req_id
     - first_name
     - last_name
     - username
     - password
     - carrier

    """

    def __init__(self, req_id=None, first_name=None, last_name=None, username=None, password=None, carrier=None):
        self.req_id = req_id
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.password = password
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.STRING:
                    self.first_name = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.STRING:
                    self.last_name = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 4:
                if ftype == TType.STRING:
                    self.username = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 5:
                if ftype == TType.STRING:
                    self.password = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 6:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype54, _vtype55, _size53 = iprot.readMapBegin()
                    for _i57 in range(_size53):
                        _key58 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        _val59 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key58] = _val59
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('RegisterUser_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.first_name is not None:
            oprot.writeFieldBegin('first_name', TType.STRING, 2)
            oprot.writeString(self.first_name.encode('utf-8') if sys.version_info[0] == 2 else self.first_name)
            oprot.writeFieldEnd()
        if self.last_name is not None:
            oprot.writeFieldBegin('last_name', TType.STRING, 3)
            oprot.writeString(self.last_name.encode('utf-8') if sys.version_info[0] == 2 else self.last_name)
            oprot.writeFieldEnd()
        if self.username is not None:
            oprot.writeFieldBegin('username', TType.STRING, 4)
            oprot.writeString(self.username.encode('utf-8') if sys.version_info[0] == 2 else self.username)
            oprot.writeFieldEnd()
        if self.password is not None:
            oprot.writeFieldBegin('password', TType.STRING, 5)
            oprot.writeString(self.password.encode('utf-8') if sys.version_info[0] == 2 else self.password)
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 6)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter60, viter61 in self.carrier.items():
                oprot.writeString(kiter60.encode('utf-8') if sys.version_info[0] == 2 else kiter60)
                oprot.writeString(viter61.encode('utf-8') if sys.version_info[0] == 2 else viter61)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class RegisterUser_result(object):
    """
    Attributes:
     - se

    """

    def __init__(self, se=None):
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('RegisterUser_result')
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class RegisterUserWithId_args(object):
    """
    Attributes:
     - req_id
     - first_name
     - last_name
     - username
     - password
     - user_id
     - carrier

    """

    def __init__(self, req_id=None, first_name=None, last_name=None, username=None, password=None, user_id=None, carrier=None):
        self.req_id = req_id
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.password = password
        self.user_id = user_id
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.STRING:
                    self.first_name = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.STRING:
                    self.last_name = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 4:
                if ftype == TType.STRING:
                    self.username = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 5:
                if ftype == TType.STRING:
                    self.password = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 6:
                if ftype == TType.I64:
                    self.user_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 7:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype63, _vtype64, _size62 = iprot.readMapBegin()
                    for _i66 in range(_size62):
                        _key67 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        _val68 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key67] = _val68
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('RegisterUserWithId_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.first_name is not None:
            oprot.writeFieldBegin('first_name', TType.STRING, 2)
            oprot.writeString(self.first_name.encode('utf-8') if sys.version_info[0] == 2 else self.first_name)
            oprot.writeFieldEnd()
        if self.last_name is not None:
            oprot.writeFieldBegin('last_name', TType.STRING, 3)
            oprot.writeString(self.last_name.encode('utf-8') if sys.version_info[0] == 2 else self.last_name)
            oprot.writeFieldEnd()
        if self.username is not None:
            oprot.writeFieldBegin('username', TType.STRING, 4)
            oprot.writeString(self.username.encode('utf-8') if sys.version_info[0] == 2 else self.username)
            oprot.writeFieldEnd()
        if self.password is not None:
            oprot.writeFieldBegin('password', TType.STRING, 5)
            oprot.writeString(self.password.encode('utf-8') if sys.version_info[0] == 2 else self.password)
            oprot.writeFieldEnd()
        if self.user_id is not None:
            oprot.writeFieldBegin('user_id', TType.I64, 6)
            oprot.writeI64(self.user_id)
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 7)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter69, viter70 in self.carrier.items():
                oprot.writeString(kiter69.encode('utf-8') if sys.version_info[0] == 2 else kiter69)
                oprot.writeString(viter70.encode('utf-8') if sys.version_info[0] == 2 else viter70)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class RegisterUserWithId_result(object):
    """
    Attributes:
     - se

    """

    def __init__(self, se=None):
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('RegisterUserWithId_result')
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class Login_args(object):
    """
    Attributes:
     - req_id
     - username
     - password
     - carrier

    """

    def __init__(self, req_id=None, username=None, password=None, carrier=None):
        self.req_id = req_id
        self.username = username
        self.password = password
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.STRING:
                    self.username = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.STRING:
                    self.password = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 4:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype72, _vtype73, _size71 = iprot.readMapBegin()
                    for _i75 in range(_size71):
                        _key76 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        _val77 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key76] = _val77
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('Login_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.username is not None:
            oprot.writeFieldBegin('username', TType.STRING, 2)
            oprot.writeString(self.username.encode('utf-8') if sys.version_info[0] == 2 else self.username)
            oprot.writeFieldEnd()
        if self.password is not None:
            oprot.writeFieldBegin('password', TType.STRING, 3)
            oprot.writeString(self.password.encode('utf-8') if sys.version_info[0] == 2 else self.password)
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 4)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter78, viter79 in self.carrier.items():
                oprot.writeString(kiter78.encode('utf-8') if sys.version_info[0] == 2 else kiter78)
                oprot.writeString(viter79.encode('utf-8') if sys.version_info[0] == 2 else viter79)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class Login_result(object):
    """
    Attributes:
     - success
     - se

    """

    def __init__(self, success=None, se=None):
        self.success = success
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 0:
                if ftype == TType.STRING:
                    self.success = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('Login_result')
        if self.success is not None:
            oprot.writeFieldBegin('success', TType.STRING, 0)
            oprot.writeString(self.success.encode('utf-8') if sys.version_info[0] == 2 else self.success)
            oprot.writeFieldEnd()
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class ComposeCreatorWithUserId_args(object):
    """
    Attributes:
     - req_id
     - user_id
     - username
     - carrier

    """

    def __init__(self, req_id=None, user_id=None, username=None, carrier=None):
        self.req_id = req_id
        self.user_id = user_id
        self.username = username
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.I64:
                    self.user_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.STRING:
                    self.username = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 4:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype81, _vtype82, _size80 = iprot.readMapBegin()
                    for _i84 in range(_size80):
                        _key85 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        _val86 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key85] = _val86
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('ComposeCreatorWithUserId_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.user_id is not None:
            oprot.writeFieldBegin('user_id', TType.I64, 2)
            oprot.writeI64(self.user_id)
            oprot.writeFieldEnd()
        if self.username is not None:
            oprot.writeFieldBegin('username', TType.STRING, 3)
            oprot.writeString(self.username.encode('utf-8') if sys.version_info[0] == 2 else self.username)
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 4)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter87, viter88 in self.carrier.items():
                oprot.writeString(kiter87.encode('utf-8') if sys.version_info[0] == 2 else kiter87)
                oprot.writeString(viter88.encode('utf-8') if sys.version_info[0] == 2 else viter88)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class ComposeCreatorWithUserId_result(object):
    """
    Attributes:
     - success
     - se

    """

    def __init__(self, success=None, se=None):
        self.success = success
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 0:
                if ftype == TType.STRUCT:
                    self.success = Creator()
                    self.success.read(iprot)
                else:
                    iprot.skip(ftype)
            elif fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('ComposeCreatorWithUserId_result')
        if self.success is not None:
            oprot.writeFieldBegin('success', TType.STRUCT, 0)
            self.success.write(oprot)
            oprot.writeFieldEnd()
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class ComposeCreatorWithUsername_args(object):
    """
    Attributes:
     - req_id
     - username
     - carrier

    """

    def __init__(self, req_id=None, username=None, carrier=None):
        self.req_id = req_id
        self.username = username
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.STRING:
                    self.username = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype90, _vtype91, _size89 = iprot.readMapBegin()
                    for _i93 in range(_size89):
                        _key94 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        _val95 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key94] = _val95
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('ComposeCreatorWithUsername_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.username is not None:
            oprot.writeFieldBegin('username', TType.STRING, 2)
            oprot.writeString(self.username.encode('utf-8') if sys.version_info[0] == 2 else self.username)
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 3)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter96, viter97 in self.carrier.items():
                oprot.writeString(kiter96.encode('utf-8') if sys.version_info[0] == 2 else kiter96)
                oprot.writeString(viter97.encode('utf-8') if sys.version_info[0] == 2 else viter97)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class ComposeCreatorWithUsername_result(object):
    """
    Attributes:
     - success
     - se

    """

    def __init__(self, success=None, se=None):
        self.success = success
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 0:
                if ftype == TType.STRUCT:
                    self.success = Creator()
                    self.success.read(iprot)
                else:
                    iprot.skip(ftype)
            elif fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('ComposeCreatorWithUsername_result')
        if self.success is not None:
            oprot.writeFieldBegin('success', TType.STRUCT, 0)
            self.success.write(oprot)
            oprot.writeFieldEnd()
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class GetUserId_args(object):
    """
    Attributes:
     - req_id
     - username
     - carrier

    """

    def __init__(self, req_id=None, username=None, carrier=None):
        self.req_id = req_id
        self.username = username
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.STRING:
                    self.username = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype99, _vtype100, _size98 = iprot.readMapBegin()
                    for _i102 in range(_size98):
                        _key103 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        _val104 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key103] = _val104
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('GetUserId_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.username is not None:
            oprot.writeFieldBegin('username', TType.STRING, 2)
            oprot.writeString(self.username.encode('utf-8') if sys.version_info[0] == 2 else self.username)
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 3)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter105, viter106 in self.carrier.items():
                oprot.writeString(kiter105.encode('utf-8') if sys.version_info[0] == 2 else kiter105)
                oprot.writeString(viter106.encode('utf-8') if sys.version_info[0] == 2 else viter106)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class GetUserId_result(object):
    """
    Attributes:
     - success
     - se

    """

    def __init__(self, success=None, se=None):
        self.success = success
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 0:
                if ftype == TType.I64:
                    self.success = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('GetUserId_result')
        if self.success is not None:
            oprot.writeFieldBegin('success', TType.I64, 0)
            oprot.writeI64(self.success)
            oprot.writeFieldEnd()
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class ComposePost_args(object):
    """
    Attributes:
     - req_id
     - username
     - user_id
     - text
     - media_ids
     - media_types
     - post_type
     - carrier

    """

    def __init__(self, req_id=None, username=None, user_id=None, text=None, media_ids=None, media_types=None, post_type=None, carrier=None):
        self.req_id = req_id
        self.username = username
        self.user_id = user_id
        self.text = text
        self.media_ids = media_ids
        self.media_types = media_types
        self.post_type = post_type
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.STRING:
                    self.username = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.I64:
                    self.user_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 4:
                if ftype == TType.STRING:
                    self.text = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 5:
                if ftype == TType.LIST:
                    self.media_ids = []
                    _etype110, _size107 = iprot.readListBegin()
                    for _i111 in range(_size107):
                        _elem112 = iprot.readI64()
                        self.media_ids.append(_elem112)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 6:
                if ftype == TType.LIST:
                    self.media_types = []
                    _etype116, _size113 = iprot.readListBegin()
                    for _i117 in range(_size113):
                        _elem118 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        self.media_types.append(_elem118)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 7:
                if ftype == TType.I32:
                    self.post_type = iprot.readI32()
                else:
                    iprot.skip(ftype)
            elif fid == 8:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype120, _vtype121, _size119 = iprot.readMapBegin()
                    for _i123 in range(_size119):
                        _key124 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        _val125 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key124] = _val125
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('ComposePost_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.username is not None:
            oprot.writeFieldBegin('username', TType.STRING, 2)
            oprot.writeString(self.username.encode('utf-8') if sys.version_info[0] == 2 else self.username)
            oprot.writeFieldEnd()
        if self.user_id is not None:
            oprot.writeFieldBegin('user_id', TType.I64, 3)
            oprot.writeI64(self.user_id)
            oprot.writeFieldEnd()
        if self.text is not None:
            oprot.writeFieldBegin('text', TType.STRING, 4)
            oprot.writeString(self.text.encode('utf-8') if sys.version_info[0] == 2 else self.text)
            oprot.writeFieldEnd()
        if self.media_ids is not None:
            oprot.writeFieldBegin('media_ids', TType.LIST, 5)
            oprot.writeListBegin(TType.I64, len(self.media_ids))
            for iter126 in self.media_ids:
                oprot.writeI64(iter126)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        if self.media_types is not None:
            oprot.writeFieldBegin('media_types', TType.LIST, 6)
            oprot.writeListBegin(TType.STRING, len(self.media_types))
            for iter127 in self.media_types:
                oprot.writeString(iter127.encode('utf-8') if sys.version_info[0] == 2 else iter127)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        if self.post_type is not None:
            oprot.writeFieldBegin('post_type', TType.I32, 7)
            oprot.writeI32(self.post_type)
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 8)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter128, viter129 in self.carrier.items():
                oprot.writeString(kiter128.encode('utf-8') if sys.version_info[0] == 2 else kiter128)
                oprot.writeString(viter129.encode('utf-8') if sys.version_info[0] == 2 else viter129)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class ComposePost_result(object):
    """
    Attributes:
     - se

    """

    def __init__(self, se=None):
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('ComposePost_result')
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class WriteUserTimeline_args(object):
    """
    Attributes:
     - req_id
     - post_id
     - user_id
     - timestamp
     - carrier

    """

    def __init__(self, req_id=None, post_id=None, user_id=None, timestamp=None, carrier=None):
        self.req_id = req_id
        self.post_id = post_id
        self.user_id = user_id
        self.timestamp = timestamp
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.I64:
                    self.post_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.I64:
                    self.user_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 4:
                if ftype == TType.I64:
                    self.timestamp = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 5:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype204, _vtype205, _size203 = iprot.readMapBegin()
                    for _i207 in range(_size203):
                        _key208 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        _val209 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key208] = _val209
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('WriteUserTimeline_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.post_id is not None:
            oprot.writeFieldBegin('post_id', TType.I64, 2)
            oprot.writeI64(self.post_id)
            oprot.writeFieldEnd()
        if self.user_id is not None:
            oprot.writeFieldBegin('user_id', TType.I64, 3)
            oprot.writeI64(self.user_id)
            oprot.writeFieldEnd()
        if self.timestamp is not None:
            oprot.writeFieldBegin('timestamp', TType.I64, 4)
            oprot.writeI64(self.timestamp)
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 5)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter210, viter211 in self.carrier.items():
                oprot.writeString(kiter210.encode('utf-8') if sys.version_info[0] == 2 else kiter210)
                oprot.writeString(viter211.encode('utf-8') if sys.version_info[0] == 2 else viter211)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class WriteUserTimeline_result(object):
    """
    Attributes:
     - se

    """

    def __init__(self, se=None):
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('WriteUserTimeline_result')
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class ReadUserTimeline_args(object):
    """
    Attributes:
     - req_id
     - user_id
     - start
     - stop
     - carrier

    """

    def __init__(self, req_id=None, user_id=None, start=None, stop=None, carrier=None):
        self.req_id = req_id
        self.user_id = user_id
        self.start = start
        self.stop = stop
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.I64:
                    self.user_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.I32:
                    self.start = iprot.readI32()
                else:
                    iprot.skip(ftype)
            elif fid == 4:
                if ftype == TType.I32:
                    self.stop = iprot.readI32()
                else:
                    iprot.skip(ftype)
            elif fid == 5:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype213, _vtype214, _size212 = iprot.readMapBegin()
                    for _i216 in range(_size212):
                        _key217 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        _val218 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key217] = _val218
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('ReadUserTimeline_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.user_id is not None:
            oprot.writeFieldBegin('user_id', TType.I64, 2)
            oprot.writeI64(self.user_id)
            oprot.writeFieldEnd()
        if self.start is not None:
            oprot.writeFieldBegin('start', TType.I32, 3)
            oprot.writeI32(self.start)
            oprot.writeFieldEnd()
        if self.stop is not None:
            oprot.writeFieldBegin('stop', TType.I32, 4)
            oprot.writeI32(self.stop)
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 5)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter219, viter220 in self.carrier.items():
                oprot.writeString(kiter219.encode('utf-8') if sys.version_info[0] == 2 else kiter219)
                oprot.writeString(viter220.encode('utf-8') if sys.version_info[0] == 2 else viter220)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class ReadUserTimeline_result(object):
    """
    Attributes:
     - success
     - se

    """

    def __init__(self, success=None, se=None):
        self.success = success
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 0:
                if ftype == TType.LIST:
                    self.success = []
                    _etype224, _size221 = iprot.readListBegin()
                    for _i225 in range(_size221):
                        _elem226 = Post()
                        _elem226.read(iprot)
                        self.success.append(_elem226)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('ReadUserTimeline_result')
        if self.success is not None:
            oprot.writeFieldBegin('success', TType.LIST, 0)
            oprot.writeListBegin(TType.STRUCT, len(self.success))
            for iter227 in self.success:
                iter227.write(oprot)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class ComposeUserMentions_args(object):
    """
    Attributes:
     - req_id
     - usernames
     - carrier

    """

    def __init__(self, req_id=None, usernames=None, carrier=None):
        self.req_id = req_id
        self.usernames = usernames
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.LIST:
                    self.usernames = []
                    _etype308, _size305 = iprot.readListBegin()
                    for _i309 in range(_size305):
                        _elem310 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        self.usernames.append(_elem310)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype312, _vtype313, _size311 = iprot.readMapBegin()
                    for _i315 in range(_size311):
                        _key316 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        _val317 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key316] = _val317
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('ComposeUserMentions_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.usernames is not None:
            oprot.writeFieldBegin('usernames', TType.LIST, 2)
            oprot.writeListBegin(TType.STRING, len(self.usernames))
            for iter318 in self.usernames:
                oprot.writeString(iter318.encode('utf-8') if sys.version_info[0] == 2 else iter318)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 3)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter319, viter320 in self.carrier.items():
                oprot.writeString(kiter319.encode('utf-8') if sys.version_info[0] == 2 else kiter319)
                oprot.writeString(viter320.encode('utf-8') if sys.version_info[0] == 2 else viter320)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class ComposeUserMentions_result(object):
    """
    Attributes:
     - success
     - se

    """

    def __init__(self, success=None, se=None):
        self.success = success
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 0:
                if ftype == TType.LIST:
                    self.success = []
                    _etype324, _size321 = iprot.readListBegin()
                    for _i325 in range(_size321):
                        _elem326 = UserMention()
                        _elem326.read(iprot)
                        self.success.append(_elem326)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('ComposeUserMentions_result')
        if self.success is not None:
            oprot.writeFieldBegin('success', TType.LIST, 0)
            oprot.writeListBegin(TType.STRUCT, len(self.success))
            for iter327 in self.success:
                iter327.write(oprot)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class ComposeUniqueId_args(object):
    """
    Attributes:
     - req_id
     - post_type
     - carrier

    """

    def __init__(self, req_id=None, post_type=None, carrier=None):
        self.req_id = req_id
        self.post_type = post_type
        self.carrier = carrier

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.req_id = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.I32:
                    self.post_type = iprot.readI32()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.MAP:
                    self.carrier = {}
                    _ktype36, _vtype37, _size35 = iprot.readMapBegin()
                    for _i39 in range(_size35):
                        _key40 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        _val41 = iprot.readString().decode('utf-8', errors='replace') if sys.version_info[0] == 2 else iprot.readString()
                        self.carrier[_key40] = _val41
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('ComposeUniqueId_args')
        if self.req_id is not None:
            oprot.writeFieldBegin('req_id', TType.I64, 1)
            oprot.writeI64(self.req_id)
            oprot.writeFieldEnd()
        if self.post_type is not None:
            oprot.writeFieldBegin('post_type', TType.I32, 2)
            oprot.writeI32(self.post_type)
            oprot.writeFieldEnd()
        if self.carrier is not None:
            oprot.writeFieldBegin('carrier', TType.MAP, 3)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.carrier))
            for kiter42, viter43 in self.carrier.items():
                oprot.writeString(kiter42.encode('utf-8') if sys.version_info[0] == 2 else kiter42)
                oprot.writeString(viter43.encode('utf-8') if sys.version_info[0] == 2 else viter43)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

class ComposeUniqueId_result(object):
    """
    Attributes:
     - success
     - se

    """

    def __init__(self, success=None, se=None):
        self.success = success
        self.se = se

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and (self.thrift_spec is not None):
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            fname, ftype, fid = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 0:
                if ftype == TType.I64:
                    self.success = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 1:
                if ftype == TType.STRUCT:
                    self.se = ServiceException.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('ComposeUniqueId_result')
        if self.success is not None:
            oprot.writeFieldBegin('success', TType.I64, 0)
            oprot.writeI64(self.success)
            oprot.writeFieldEnd()
        if self.se is not None:
            oprot.writeFieldBegin('se', TType.STRUCT, 1)
            self.se.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

def __repr__(self):
    L = ['%s=%r' % (key, value) for key, value in self.__dict__.items()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

def printResults(results):
    result_type_count = {}
    for result in results:
        try:
            result_type_count[result] += 1
        except KeyError:
            result_type_count[result] = 1
    for result_type, count in result_type_count.items():
        if result_type == '' or result_type.startswith('Success'):
            print('Succeeded:', count)
        elif '500 Internal Server Error' in result_type:
            print('Failed:', count, 'Error:', 'Internal Server Error')
        else:
            print('Failed:', count, 'Error:', result_type.strip())

# Node: startswith
# Node: strip
