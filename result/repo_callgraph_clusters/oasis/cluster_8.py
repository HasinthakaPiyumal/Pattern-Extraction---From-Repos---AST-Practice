# Cluster 8

@dataclass
class Neo4jConfig:
    uri: str | None = None
    username: str | None = None
    password: str | None = None

    def is_valid(self) -> bool:
        return all([self.uri, self.username, self.password])

def is_valid(self) -> bool:
    return all([self.uri, self.username, self.password])

