from __future__ import print_function

import os
import sys
import errno
import logging

from fuse import FUSE, FuseOSError, Operations


logging.basicConfig()


class OrdrinFs(Operations):

    def __init__(self, root):
        self.root = root

        self.logger = logging.getLogger('FUSE')
        self.logger.setLevel(logging.DEBUG)

    # Helpers
    # =======

    def _full_path(self, partial):
        if partial.startswith("/"):
            partial = partial[1:]
        path = os.path.join(self.root, partial)
        return path

    def _is_dir(self, path):
        return self._is_orderin or self._is_category or self._is_restaurant

    def _is_ronly(self, path):
        if self._is_restaurant(os.path.dirname(path)):
            rfile = os.path.basename(path)
            if rfile in ['order.out', 'menu']:
                return True
        return False

    def _is_orderin(self, path):
        return len(path.split('/')) == 0

    def _is_category(self, path):
        return len(path.split('/')) == 1

    def _is_restaurant(self, path):
        return len(path.split('/')) == 2

    # Filesystem methods
    # ==================

    def access(self, path, mode):
        self.logger.debug('access %s', path)
        full_path = self._full_path(path)
        if self._is_dir(path):
            return (mode & (os.R_OK | os.X_OK)) > 0
        elif self._is_ronly(path):
            return (mode & os.R_OK)
        elif self._is_orderin(path):
            return (mode & (os.R_OK | os.W_OK))

        if not os.access(full_path, mode):
            raise FuseOSError(errno.EACCES)

    def chmod(self, path, mode):
        self.logger.debug('chmod %s', path)
        full_path = self._full_path(path)
        return os.chmod(full_path, mode)

    def chown(self, path, uid, gid):
        self.logger.debug('chown %s', path)
        full_path = self._full_path(path)
        return os.chown(full_path, uid, gid)

    def getattr(self, path, fh=None):
        self.logger.debug('getattr %s', path)
        full_path = self._full_path(path)
        st = os.lstat(full_path)
        return dict((key, getattr(st, key))
                    for key in ('st_atime', 'st_ctime', 'st_gid', 'st_mode',
                    'st_mtime', 'st_nlink', 'st_size', 'st_uid'))

    def readdir(self, path, fh):
        self.logger.debug('readdir %s', path)
        full_path = self._full_path(path)

        dirents = ['.', '..']
        if os.path.isdir(full_path):
            dirents.extend(os.listdir(full_path))
        for r in dirents:
            yield r

    def readlink(self, path):
        self.logger.debug('readlink %s', path)
        pathname = os.readlink(self._full_path(path))
        if pathname.startswith("/"):
            # Path name is absolute, sanitize it.
            return os.path.relpath(pathname, self.root)
        else:
            return pathname

    def mknod(self, path, mode, dev):
        self.logger.debug('mknod %s', path)
        return os.mknod(self._full_path(path), mode, dev)

    def rmdir(self, path):
        self.logger.debug('rmdir %s', path)
        full_path = self._full_path(path)
        return os.rmdir(full_path)

    def mkdir(self, path, mode):
        self.logger.debug('mkdir %s', path)
        return os.mkdir(self._full_path(path), mode)

    def statfs(self, path):
        self.logger.debug('statfs %s', path)
        full_path = self._full_path(path)
        stv = os.statvfs(full_path)
        return dict((key, getattr(stv, key))
                    for key in ('f_bavail', 'f_bfree', 'f_blocks', 'f_bsize',
                                'f_favail', 'f_ffree', 'f_files', 'f_flag',
                                'f_frsize', 'f_namemax'))

    def unlink(self, path):
        self.logger.debug('unlink %s', path)
        return os.unlink(self._full_path(path))

    def symlink(self, target, name):
        self.logger.debug('symlink %s %s', target, name)
        return os.symlink(self._full_path(target), self._full_path(name))

    def rename(self, old, new):
        self.logger.debug('rename %s %s', old, new)
        return os.rename(self._full_path(old), self._full_path(new))

    def link(self, target, name):
        self.logger.debug('link %s %s', target, name)
        return os.link(self._full_path(target), self._full_path(name))

    def utimens(self, path, times=None):
        self.logger.debug('utimens %s', path)
        return os.utime(self._full_path(path), times)

    # File methods
    # ============

    def open(self, path, flags):
        self.logger.debug('open %s', path)
        full_path = self._full_path(path)
        return os.open(full_path, flags)

    def create(self, path, mode, fi=None):
        self.logger.debug('create %s', path)
        full_path = self._full_path(path)
        return os.open(full_path, os.O_WRONLY | os.O_CREAT, mode)

    def read(self, path, length, offset, fh):
        self.logger.debug('read %s', path)
        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, length)

    def write(self, path, buf, offset, fh):
        self.logger.debug('write %s', path)
        os.lseek(fh, offset, os.SEEK_SET)
        return os.write(fh, buf)

    def truncate(self, path, length, fh=None):
        self.logger.debug('truncate %s', path)
        full_path = self._full_path(path)
        with open(full_path, 'r+') as f:
            f.truncate(length)

    def flush(self, path, fh):
        self.logger.debug('flush %s', path)
        return os.fsync(fh)

    def release(self, path, fh):
        self.logger.debug('release %s', path)
        return os.close(fh)

    def fsync(self, path, fdatasync, fh):
        self.logger.debug('fsync %s', path)
        return self.flush(path, fh)


def main(mountpoint, root):
    FUSE(OrdrinFs(root), mountpoint, foreground=True)

if __name__ == '__main__':
    main(sys.argv[2], sys.argv[1])
