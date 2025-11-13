# Cluster 25

class DualQuaternion:

    @staticmethod
    def FromQT(q, t):
        return DualQuaternion(qe=0.5 * np.asarray(t)) * DualQuaternion(q)

    def __init__(self, q0=np.array((1.0, 0.0, 0.0, 0.0)), qe=np.zeros(4)):
        self.q0, self.qe = (Quaternion(q0), Quaternion(qe))

    def __add__(self, other):
        return DualQuaternion(self.q0 + other.q0, self.qe + other.qe)

    def __iadd__(self, other):
        self.q0 += other.q0
        self.qe += other.qe
        return self

    def __invert__(self):
        return DualQuaternion(~self.q0, ~self.qe)

    def __mul__(self, other):
        if isinstance(other, DualQuaternion):
            return DualQuaternion(self.q0 * other.q0, self.q0 * other.qe + self.qe * other.q0)
        elif isinstance(other, complex):
            return DualQuaternion(self.q0 * other.real, self.q0 * other.imag + self.qe * other.real)
        else:
            return DualQuaternion(other * self.q0, other * self.qe)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __imul__(self, other):
        tmp = self * other
        self.q0, self.qe = (tmp.q0, tmp.qe)
        return self

    def __neg__(self):
        return DualQuaternion(-self.q0, -self.qe)

    def __sub__(self, other):
        return DualQuaternion(self.q0 - other.q0, self.qe - other.qe)

    def __isub__(self, other):
        self.q0 -= other.q0
        self.qe -= other.qe
        return self

    def inverse(self):
        normsq = complex(q0.dot(q0), 2.0 * self.q0.q.dot(self.qe.q))
        inv_len_real = 1.0 / normsq.real
        return ~self * complex(inv_len_real, -normsq.imag * inv_len_real * inv_len_real)

    def norm(self):
        q0_norm = self.q0.norm()
        return complex(q0_norm, self.q0.dot(self.qe) / q0_norm)

    def normalize(self):
        norm = self.norm()
        inv_len_real = 1.0 / norm.real
        self *= complex(inv_len_real, -norm.imag * inv_len_real * inv_len_real)
        return self

    def getT(self):
        return 2 * (self.qe * ~self.q0).q[1:]

    def ToQT(self):
        return (self.q0, self.getT())

def ToQT(self):
    return (self.q0, self.getT())

class DualQuaternion:

    @staticmethod
    def FromQT(q, t):
        return DualQuaternion(qe=0.5 * np.asarray(t)) * DualQuaternion(q)

    def __init__(self, q0=np.array((1.0, 0.0, 0.0, 0.0)), qe=np.zeros(4)):
        self.q0, self.qe = (Quaternion(q0), Quaternion(qe))

    def __add__(self, other):
        return DualQuaternion(self.q0 + other.q0, self.qe + other.qe)

    def __iadd__(self, other):
        self.q0 += other.q0
        self.qe += other.qe
        return self

    def __invert__(self):
        return DualQuaternion(~self.q0, ~self.qe)

    def __mul__(self, other):
        if isinstance(other, DualQuaternion):
            return DualQuaternion(self.q0 * other.q0, self.q0 * other.qe + self.qe * other.q0)
        elif isinstance(other, complex):
            return DualQuaternion(self.q0 * other.real, self.q0 * other.imag + self.qe * other.real)
        else:
            return DualQuaternion(other * self.q0, other * self.qe)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __imul__(self, other):
        tmp = self * other
        self.q0, self.qe = (tmp.q0, tmp.qe)
        return self

    def __neg__(self):
        return DualQuaternion(-self.q0, -self.qe)

    def __sub__(self, other):
        return DualQuaternion(self.q0 - other.q0, self.qe - other.qe)

    def __isub__(self, other):
        self.q0 -= other.q0
        self.qe -= other.qe
        return self

    def inverse(self):
        normsq = complex(q0.dot(q0), 2.0 * self.q0.q.dot(self.qe.q))
        inv_len_real = 1.0 / normsq.real
        return ~self * complex(inv_len_real, -normsq.imag * inv_len_real * inv_len_real)

    def norm(self):
        q0_norm = self.q0.norm()
        return complex(q0_norm, self.q0.dot(self.qe) / q0_norm)

    def normalize(self):
        norm = self.norm()
        inv_len_real = 1.0 / norm.real
        self *= complex(inv_len_real, -norm.imag * inv_len_real * inv_len_real)
        return self

    def getT(self):
        return 2 * (self.qe * ~self.q0).q[1:]

    def ToQT(self):
        return (self.q0, self.getT())

def ToQT(self):
    return (self.q0, self.getT())

