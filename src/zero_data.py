import os
import site
import stat
import sys
import sysconfig
from importlib import metadata


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
_trusted_read_roots = ()
_VERCEL_VENDOR_ROOT = "/var/task/_vendor"
_READ_ONLY_FLAGS = 0
for _flag in (
    "O_CLOEXEC", "O_NONBLOCK", "O_NOFOLLOW", "O_DIRECTORY",
    "O_LARGEFILE", "O_NOCTTY", "O_BINARY", "O_TEXT", "O_NOINHERIT",
):
    _READ_ONLY_FLAGS |= getattr(os, _flag, 0)


def _contains(root, path):
    return os.path.commonpath((root, path)) == root


def _discover_trusted_read_roots():
    paths = sysconfig.get_paths()
    candidates = [paths[key] for key in ("stdlib", "platstdlib", "purelib", "platlib")]
    candidates.extend(site.getsitepackages())
    if site.ENABLE_USER_SITE:
        candidates.append(site.getusersitepackages())
    roots = {os.path.realpath(path) for path in candidates if os.path.isdir(path)}

    # A Vercel vendor directory must contain an installed distribution backing
    # an already loaded module; neither sys.path nor the directory name is proof.
    vendor = os.path.realpath(_VERCEL_VENDOR_ROOT)
    if vendor == _VERCEL_VENDOR_ROOT and os.path.isdir(vendor):
        loaded_files = {
            os.path.realpath(module.__file__)
            for module in tuple(sys.modules.values())
            if isinstance(getattr(module, "__file__", None), str)
        }
        for distribution in metadata.distributions(path=[vendor]):
            if os.path.realpath(distribution.locate_file("")) != vendor:
                continue
            if any(
                _contains(vendor, filename) and filename in loaded_files
                for filename in (
                    os.path.realpath(distribution.locate_file(entry))
                    for entry in distribution.files or ()
                )
            ):
                roots.add(vendor)
                break
    return tuple(sorted(roots))


def _is_read_only_open(args):
    return (
        len(args) >= 3
        and args[1] in (None, "r")
        and type(args[2]) is int
        and args[2] & ~_READ_ONLY_FLAGS == 0
    )


def _is_trusted_package_read(path):
    if not isinstance(path, (str, bytes)):
        return False
    try:
        path = os.fsdecode(path)
        # The open audit event omits dir_fd, so relative paths cannot be
        # resolved safely against the current working directory.
        if not os.path.isabs(path) or ".." in path.split(os.sep):
            return False
        # realpath uses stat/readlink, not open or directory enumeration, so
        # containment checks do not recursively invoke this audit hook.
        canonical = os.path.realpath(path, strict=True)
        return any(_contains(root, canonical) for root in _trusted_read_roots)
    except (OSError, ValueError):
        return False


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
        if _is_read_only_open(args) and (
            _is_read_only_pipe_open(args) or _is_trusted_package_read(args[0])
        ):
            return
        _blocked_file_io_attempts += 1
        raise PermissionError("file I/O is disabled")
    elif event in _FILESYSTEM_EVENTS:
        if event == "os.listdir" and args and _is_trusted_package_read(args[0]):
            return
        _blocked_file_io_attempts += 1
        raise PermissionError("filesystem access is disabled")


def install_zero_data_guard():
    global _installed, _trusted_read_roots
    if not _installed:
        _trusted_read_roots = _discover_trusted_read_roots()
        sys.addaudithook(_deny_persistent_io)
        _installed = True


def assert_no_file_io():
    if _blocked_file_io_attempts:
        raise PermissionError(
            f"zero-data violation: {_blocked_file_io_attempts} file I/O attempt(s) blocked"
        )
