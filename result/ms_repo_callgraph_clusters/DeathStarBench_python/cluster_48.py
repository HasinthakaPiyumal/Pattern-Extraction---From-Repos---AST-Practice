# Cluster 48

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

def GetFollowees(self, req_id, user_id, carrier):
    """
        Parameters:
         - req_id
         - user_id
         - carrier

        """
    self.send_GetFollowees(req_id, user_id, carrier)
    return self.recv_GetFollowees()

# Node: send_GetFollowees
# Node: recv_GetFollowees
