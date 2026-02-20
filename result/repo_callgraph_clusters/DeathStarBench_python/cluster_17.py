# Cluster 17

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

def UploadUserWithUserId(self, req_id, user_id, carrier):
    """
        Parameters:
         - req_id
         - user_id
         - carrier

        """
    self.send_UploadUserWithUserId(req_id, user_id, carrier)
    self.recv_UploadUserWithUserId()

# Node: send_UploadUserWithUserId
# Node: recv_UploadUserWithUserId
