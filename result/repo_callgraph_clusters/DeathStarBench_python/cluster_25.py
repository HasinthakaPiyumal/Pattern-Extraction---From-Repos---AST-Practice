# Cluster 25

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

def ReadCastInfo(self, req_id, cast_ids, carrier):
    """
        Parameters:
         - req_id
         - cast_ids
         - carrier

        """
    self.send_ReadCastInfo(req_id, cast_ids, carrier)
    return self.recv_ReadCastInfo()

# Node: send_ReadCastInfo
# Node: recv_ReadCastInfo
