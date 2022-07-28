import builtins
import pickle
import sys

allowed_builtins = {
    "tuple",
    "list",
    "dict",
    "bytes",
    "str",
    "int",
    "FileNotFoundError",
    "TypeError",
    "ValueError",
    "Exception",
}

allowed_custom = {"RPCEndpoint", "RPCException", "RPCResult", "FuseOSError"}


class SafeUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        # Allow only safe classes from builtins
        if module == "builtins" and name in allowed_builtins:
            return getattr(builtins, name)

        # Allow only safe custom defined classes
        if name in allowed_custom:
            if not module in sys.modules:
                __import__(module)

            return getattr(sys.modules[module], name)

        # Deny use of any other class to prevent de-serialization security issues
        raise pickle.UnpicklingError("Usage of '%s.%s' is forbidden." % (module, name))
