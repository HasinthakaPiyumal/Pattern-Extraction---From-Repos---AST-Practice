# Cluster 8

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

# Node: send_WritePlot
# Node: recv_WritePlot
