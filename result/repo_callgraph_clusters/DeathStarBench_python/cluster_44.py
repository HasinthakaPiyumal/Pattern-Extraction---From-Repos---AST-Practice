# Cluster 44

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

def __hash__(self):
    return hash(self.__class__) ^ hash((self.errorCode, self.message))

# Node: hash
