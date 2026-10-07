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
_blocked_write_attempts = 0


def _deny_persistent_io(event, args):
    global _blocked_write_attempts
    if event == "open":
        mode = args[1] if len(args) > 1 else None
        flags = args[2] if len(args) > 2 else 0
        if (mode and any(flag in mode for flag in "wax+")) or (
            isinstance(flags, int) and flags & _WRITE_FLAGS
        ):
            _blocked_write_attempts += 1
            raise PermissionError("persistent file I/O is disabled")
    elif event in _MUTATION_EVENTS:
        _blocked_write_attempts += 1
        raise PermissionError("persistent file I/O is disabled")


def install_zero_data_guard():
    global _installed
    if not _installed:
        sys.addaudithook(_deny_persistent_io)
        _installed = True


def assert_no_write_attempts():
    if _blocked_write_attempts:
        raise PermissionError(
            f"zero-data violation: {_blocked_write_attempts} persistent write attempt(s) blocked"
        )
