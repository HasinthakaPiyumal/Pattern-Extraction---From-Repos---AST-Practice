# Cluster 32

class StrValuedBaseEnum(Enum, metaclass=StrValuedEnumMeta):

    def __hash__(self):
        return hash(self.value)

    @property
    def value(self):
        return str(super().value)

    @classmethod
    @property
    def values(cls) -> set:
        if not hasattr(cls, '__VALUES'):
            cls.__VALUES = {i.value for i in cls}
        return cls.__VALUES

    def __eq__(self, other) -> bool:
        if isinstance(other, type(self)):
            return self.value == other.value
        elif isinstance(other, str):
            return self.value == other
        else:
            return False

    def __str__(self):
        return self.value

def __hash__(self):
    return hash(self.value)

