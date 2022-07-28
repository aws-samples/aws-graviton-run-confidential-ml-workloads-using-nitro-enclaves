class RPCException(Exception):
    def __init__(self, reason):
        self.reason = reason


class RPCResult:
    def __init__(self, data):
        self.data = data


class RPCEndpoint:
    def __init__(self, name, args):
        self.name = name
        self.args = args
