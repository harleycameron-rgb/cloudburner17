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


def _deny_persistent_io(event, args):
    global _blocked_file_io_attempts
    if event == "open":
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
