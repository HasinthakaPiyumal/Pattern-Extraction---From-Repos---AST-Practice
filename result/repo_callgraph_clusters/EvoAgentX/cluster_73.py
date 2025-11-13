# Cluster 73

@dataclass
class Test:
    input: str
    output: str
    testtype: TestType

    def __post_init__(self):
        self.testtype = TestType(self.testtype)

def __post_init__(self):
    self.testtype = TestType(self.testtype)

