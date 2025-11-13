# Cluster 22

def makeServer(objCls, objArgs, url, APIList, serverPrivateKeyPath=None, clientPublicKeysDir=None, validateReturn=True, atomicCall=True):
    return GenesisRPCServer(objCls, objArgs, url, APIList, serverPrivateKeyPath, clientPublicKeysDir, validateReturn, atomicCall)

