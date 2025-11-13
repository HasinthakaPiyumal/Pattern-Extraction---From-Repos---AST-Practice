# Cluster 18

def array_to_blob(array):
    if IS_PYTHON3:
        return array.tostring()
    else:
        return np.getbuffer(array)

def array_to_blob(arr):
    return np.getbuffer(arr)

def array_to_blob(arr):
    return np.getbuffer(arr)

