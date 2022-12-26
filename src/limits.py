class Limits:
    def __init__(
        self,
        nodes: int,
        depth: int,
        time: int,
    ) -> None:
        self.limited = {"nodes": nodes, "depth": depth, "time": time}
