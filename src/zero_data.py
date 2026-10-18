import os
import site
import stat
import sys
import sysconfig


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
_trusted_package_roots = ()


def _discover_package_roots():
    candidates = {
        sysconfig.get_path("stdlib"),
        sysconfig.get_path("platstdlib"),
        sysconfig.get_path("purelib"),
        sysconfig.get_path("platlib"),
        *site.getsitepackages(),
    }
    if site.ENABLE_USER_SITE:
        candidates.add(site.getusersitepackages())
    # Vercel installs dependencies here, but only trust it when it is active.
    if "/var/task/_vendor" in sys.path:
        candidates.add("/var/task/_vendor")
    active_paths = {os.path.realpath(path) for path in sys.path if path}
    return tuple(
        sorted(
            {
                os.path.realpath(path)
                for path in candidates
                if path
                and os.path.isdir(path)
                and os.path.realpath(path) in active_paths
            }
        )
    )


def _is_read_only_open(args):
    if len(args) < 3 or args[1] not in (None, "r"):
        return False
    flags = args[2]
    allowed_flags = os.O_RDONLY
    for name in (
        "O_CLOEXEC", "O_NOFOLLOW", "O_NONBLOCK", "O_DIRECTORY",
        "O_LARGEFILE", "O_NOCTTY", "O_BINARY", "O_TEXT",
    ):
        allowed_flags |= getattr(os, name, 0)
    return (
        isinstance(flags, int)
        and not isinstance(flags, bool)
        and flags & os.O_ACCMODE == os.O_RDONLY
        and flags & ~allowed_flags == 0
    )


def _is_trusted_package_path(path):
    if not isinstance(path, (str, bytes)):
        return False
    path = os.fsdecode(path)
    # The audit event omits os.open's dir_fd, so relative paths are ambiguous.
    if not os.path.isabs(path):
        return False
    try:
        # realpath uses lstat/readlink, neither of which emits audited I/O events.
        path = os.path.realpath(path)
        return any(
            os.path.commonpath((root, path)) == root
            for root in _trusted_package_roots
        )
    except (OSError, ValueError):
        return False


def _is_read_only_pipe_open(args):
    if (
        not _is_read_only_open(args)
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
        if _is_read_only_pipe_open(args) or (
            _is_read_only_open(args) and _is_trusted_package_path(args[0])
        ):
            return
        _blocked_file_io_attempts += 1
        raise PermissionError("file I/O is disabled")
    elif event == "os.listdir" and args and _is_trusted_package_path(args[0]):
        # Importlib enumerates package directories when filling its finder cache.
        return
    elif event in _FILESYSTEM_EVENTS:
        _blocked_file_io_attempts += 1
        raise PermissionError("filesystem access is disabled")


def install_zero_data_guard():
    global _installed, _trusted_package_roots
    if not _installed:
        _trusted_package_roots = _discover_package_roots()
        sys.addaudithook(_deny_persistent_io)
        _installed = True


def assert_no_file_io():
    if _blocked_file_io_attempts:
        raise PermissionError(
            f"zero-data violation: {_blocked_file_io_attempts} file I/O attempt(s) blocked"
        )
