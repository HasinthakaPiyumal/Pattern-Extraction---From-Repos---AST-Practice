# Cluster 52

class CodeBlock:
    """
    Parameters
    ----------
    name : str
        逻辑名（日志、调试友好）
    func : Callable[[dict], Any]
        普通同步函数，输入 cfg 字典
    """

    def __init__(self, name: str, func: Callable[[Dict[str, Any]], Any]):
        self.name = name
        self._func = func

    def run(self, cfg: Dict[str, Any]) -> Any:
        """同步执行封装的函数。"""
        return self._func(cfg)

    def __call__(self, cfg: Dict[str, Any]) -> Any:
        return self.run(cfg)

    def __repr__(self):
        return f'<CodeBlock {self.name} (sync)>'

def run(self, cfg: Dict[str, Any]) -> Any:
    """同步执行封装的函数。"""
    return self._func(cfg)

