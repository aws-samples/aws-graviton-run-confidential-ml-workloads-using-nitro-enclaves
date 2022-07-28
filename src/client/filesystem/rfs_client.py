from fuse import LoggingMixIn, Operations


class RFSClient(Operations, LoggingMixIn):
    def __init__(self, rpc_client):
        self.rpc_client = rpc_client

    # Filesystem methods
    def access(self, path, mode):
        self.rpc_client.access(path, mode)

    def chmod(self, path, mode):
        return self.rpc_client.chmod(path, mode)

    def chown(self, path, uid, gid):
        return self.rpc_client.chown(path, uid, gid)

    def getattr(self, path, fh=None):
        return self.rpc_client.getattr(path, fh)

    def readdir(self, path, fh):
        return self.rpc_client.readdir(path, fh)

    def readlink(self, path):
        return self.rpc_client.readlink(path)

    def mknod(self, path, mode, dev):
        return self.rpc_client.mknod(path, mode, dev)

    def rmdir(self, path):
        return self.rpc_client.rmdir(path)

    def mkdir(self, path, mode):
        return self.rpc_client.mkdir(path, mode)

    def statfs(self, path):
        return self.rpc_client.statfs(path)

    def unlink(self, path):
        return self.rpc_client.unlink(path)

    def symlink(self, name, target):
        return self.rpc_client.symlink(name, target)

    def rename(self, old, new):
        return self.rpc_client.rename(old, new)

    def link(self, target, name):
        return self.rpc_client.link(target, name)

    def utimens(self, path, times=None):
        return self.rpc_client.utimens(path, times)

    # File methods
    def open(self, path, flags):
        return self.rpc_client.open(path, flags)

    def create(self, path, mode, fi=None):
        return self.rpc_client.create(path, mode, fi)

    def read(self, path, length, offset, fh):
        return self.rpc_client.read(path, length, offset, fh)

    def write(self, path, buf, offset, fh):
        return self.rpc_client.write(path, buf, offset, fh)

    def truncate(self, path, length, fh=None):
        return self.rpc_client.truncate(path, length, fh)

    def flush(self, path, fh):
        return self.rpc_client.flush(path, fh)

    def release(self, path, fh):
        return self.rpc_client.release(path, fh)

    def fsync(self, path, fdatasync, fh):
        return self.rpc_client.fsync(path, fdatasync, fh)
