import os
import stat
import sys


_FILESYSTEM_EVENTS = {
    "os.chmod",
    "os.chown",
    "os.getxattr",
    "os.link",
    "os.listdir",
    "os.mkdir",
    "os.mkfifo",
    "os.mknod",
    "os.remove",
    "os.rename",
    "os.replace",
    "os.removexattr",
    "os.rmdir",
    "os.scandir",
    "os.setxattr",
    "os.symlink",
    "os.truncate",
    "os.utime",
}
_installed = False
_blocked_file_io_attempts = 0


def _is_read_only_pipe_open(args):
    if (
        len(args) < 2
        or not isinstance(args[0], int)
        or isinstance(args[0], bool)
        or args[1] != "r"
    ):
        return False
    try:
        descriptor = os.fstat(args[0])
    except OSError:
        return False
    return stat.S_ISFIFO(descriptor.st_mode)


def _deny_persistent_io(event, args):
    global _blocked_file_io_attempts
    if event == "open":
        if _is_read_only_pipe_open(args):
            return
        _blocked_file_io_attempts += 1
        raise PermissionError("file I/O is disabled")
    elif event in _FILESYSTEM_EVENTS:
        _blocked_file_io_attempts += 1
        raise PermissionError("filesystem access is disabled")


def install_zero_data_guard():
    global _installed
    if not _installed:
        sys.addaudithook(_deny_persistent_io)
        _installed = True


def assert_no_file_io():
    if _blocked_file_io_attempts:
        raise PermissionError(
            f"zero-data violation: {_blocked_file_io_attempts} file I/O attempt(s) blocked"
        )
