import os
import sys


_WRITE_FLAGS = (
    os.O_WRONLY
    | os.O_RDWR
    | os.O_CREAT
    | os.O_TRUNC
    | os.O_APPEND
)
_MUTATION_EVENTS = {
    "os.chmod",
    "os.chown",
    "os.link",
    "os.mkdir",
    "os.remove",
    "os.rename",
    "os.rmdir",
    "os.symlink",
    "os.truncate",
}
_installed = False


def _deny_persistent_io(event, args):
    if event == "open":
        mode = args[1] if len(args) > 1 else None
        flags = args[2] if len(args) > 2 else 0
        if (mode and any(flag in mode for flag in "wax+")) or (
            isinstance(flags, int) and flags & _WRITE_FLAGS
        ):
            raise PermissionError("persistent file I/O is disabled")
    elif event in _MUTATION_EVENTS:
        raise PermissionError("persistent file I/O is disabled")


def install_zero_data_guard():
    global _installed
    if not _installed:
        sys.addaudithook(_deny_persistent_io)
        _installed = True
