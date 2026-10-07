import sys


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
_blocked_file_io_attempts = 0


def _deny_persistent_io(event, args):
    global _blocked_file_io_attempts
    if event == "open":
        _blocked_file_io_attempts += 1
        raise PermissionError("file I/O is disabled")
    elif event in _MUTATION_EVENTS:
        _blocked_file_io_attempts += 1
        raise PermissionError("filesystem mutation is disabled")


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
