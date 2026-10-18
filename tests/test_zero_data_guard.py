import importlib.util
import os
import subprocess
import sys
import textwrap
import unittest


SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))

FIXTURE = """
import os
import sys
from pathlib import Path
import zero_data

root = os.path.join(os.getcwd(), "installed")
os.mkdir(root)
package_file = os.path.join(root, "dependency.py")
with open(package_file, "w") as stream:
    stream.write("value = 42\\n")
outside = os.path.join(os.getcwd(), "private.txt")
with open(outside, "w") as stream:
    stream.write("private")
sys.path.insert(0, root)
zero_data.sysconfig.get_path = lambda name: root
zero_data.site.getsitepackages = lambda: [root]
zero_data.site.ENABLE_USER_SITE = False

def denied(operation):
    before = zero_data._blocked_file_io_attempts
    try:
        operation()
    except PermissionError:
        pass
    else:
        raise AssertionError("filesystem access was allowed")
    assert zero_data._blocked_file_io_attempts == before + 1
    try:
        zero_data.assert_no_file_io()
    except PermissionError:
        pass
    else:
        raise AssertionError("blocked access was not recorded")
"""


class ZeroDataGuardTests(unittest.TestCase):
    def run_isolated(self, code):
        # An unguarded outer process cleans up after the guarded child exits.
        wrapper = f"""
import subprocess
import sys
import tempfile
with tempfile.TemporaryDirectory() as directory:
    result = subprocess.run(
        [sys.executable, "-B", "-c", {textwrap.dedent(code)!r}],
        cwd=directory,
        timeout=30,
    )
sys.exit(result.returncode)
"""
        result = subprocess.run(
            [sys.executable, "-B", "-c", wrapper],
            env={**os.environ, "PYTHONPATH": SRC_DIR, "PYTHONDONTWRITEBYTECODE": "1"},
            capture_output=True,
            text=True,
            timeout=45,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def run_guarded(self, code, setup=""):
        self.run_isolated(
            FIXTURE
            + textwrap.dedent(setup)
            + "\nzero_data.install_zero_data_guard()\n"
            + textwrap.dedent(code)
        )

    def test_trusted_reads_and_lazy_import(self):
        self.run_guarded("""
            from dependency import value
            assert value == 42
            for path in (package_file, os.fsencode(package_file), Path(package_file)):
                with open(path, "rb") as stream:
                    assert stream.read() == b"value = 42\\n"
            fd = os.open(package_file, os.O_RDONLY | getattr(os, "O_CLOEXEC", 0))
            assert os.read(fd, 100) == b"value = 42\\n"
            os.close(fd)
            assert "dependency.py" in os.listdir(root)
            try:
                open(os.path.join(root, "missing"), "rb")
            except FileNotFoundError:
                pass
            else:
                raise AssertionError("missing dependency unexpectedly exists")
            zero_data.install_zero_data_guard()
            zero_data.assert_no_file_io()
        """)

    def test_canonical_installation_root(self):
        self.run_guarded("""
            assert zero_data._trusted_package_roots == (root,)
            with open(os.path.join(alias, "dependency.py")) as stream:
                assert stream.read() == "value = 42\\n"
            zero_data.assert_no_file_io()
        """, """
            alias = os.path.join(os.getcwd(), "installation-alias")
            os.symlink(root, alias)
            sys.path[0] = alias
            zero_data.sysconfig.get_path = lambda name: alias
            zero_data.site.getsitepackages = lambda: [alias]
        """)

    def test_unrelated_prefix_traversal_and_symlink_reads_are_denied(self):
        self.run_guarded("""
            for path in (
                outside,
                os.path.join(sibling, "private.txt"),
                os.path.join(root, "..", "private.txt"),
                os.path.join(root, "escape"),
                os.path.join(root, "escape-directory", "private.txt"),
            ):
                denied(lambda: open(path, "rb"))
                denied(lambda: os.open(path, os.O_RDONLY))
            denied(lambda: os.listdir(os.path.join(root, "escape-directory")))
        """, """
            sibling = root + "-untrusted"
            os.mkdir(sibling)
            with open(os.path.join(sibling, "private.txt"), "w") as stream:
                stream.write("private")
            os.symlink(outside, os.path.join(root, "escape"))
            os.symlink(os.getcwd(), os.path.join(root, "escape-directory"))
        """)

    def test_arbitrary_sys_path_and_named_directories_are_not_trusted(self):
        self.run_guarded("""
            for path in untrusted:
                denied(lambda: open(path))
                denied(lambda: os.listdir(os.path.dirname(path)))
            sys.path.append(os.path.dirname(outside))
            denied(lambda: open(outside))
            assert zero_data._trusted_package_roots == (root,)
        """, """
            untrusted = []
            for name in ("site-packages", "_vendor", "application"):
                directory = os.path.join(os.getcwd(), name)
                os.mkdir(directory)
                path = os.path.join(directory, "private.txt")
                with open(path, "w") as stream:
                    stream.write("private")
                sys.path.append(directory)
                untrusted.append(path)
        """)

    def test_writes_and_mutating_os_open_flags_are_denied(self):
        self.run_guarded("""
            for mode in ("w", "a", "x", "r+", "w+", "a+"):
                denied(lambda: open(package_file, mode))
            for flags in (
                os.O_WRONLY, os.O_RDWR, os.O_CREAT, os.O_TRUNC,
                os.O_APPEND, os.O_EXCL, os.O_RDONLY | os.O_CREAT,
                getattr(os, "O_TMPFILE", os.O_CREAT),
            ):
                denied(lambda: os.open(package_file, flags))
            denied(lambda: open(os.path.join(root, "new-file"), "w"))
            with open(package_file) as stream:
                assert stream.read() == "value = 42\\n"
        """)

    def test_relative_os_open_with_dir_fd_is_denied(self):
        self.run_guarded("""
            denied(lambda: os.open("dependency.py", os.O_RDONLY, dir_fd=outside_fd))
            denied(lambda: open("dependency.py"))
            os.close(outside_fd)
        """, """
            outside_fd = os.open(os.getcwd(), os.O_RDONLY)
            with open(os.path.join(os.getcwd(), "dependency.py"), "w") as stream:
                stream.write("private")
            os.chdir(root)
        """)

    def test_filesystem_mutations_and_enumeration_stay_denied(self):
        self.run_guarded("""
            for operation in (
                lambda: os.listdir(os.path.dirname(root)),
                lambda: os.scandir(root),
                lambda: os.mkdir(os.path.join(root, "new")),
                lambda: os.remove(package_file),
                lambda: os.rename(package_file, package_file + ".moved"),
                lambda: os.chmod(package_file, 0o600),
                lambda: os.truncate(package_file, 0),
                lambda: os.symlink(outside, os.path.join(root, "new-link")),
            ):
                denied(operation)
        """)

    def test_only_read_only_pipe_descriptors_are_allowed(self):
        self.run_guarded("""
            with open(reader, "rb", closefd=False) as stream:
                assert stream.read(4) == b"pipe"
            zero_data.assert_no_file_io()
            denied(lambda: open(writer, "w", closefd=False))
            denied(lambda: open(reader, "r+", closefd=False))
            denied(lambda: open(regular_fd, "r", closefd=False))
            denied(lambda: open(fifo, "r"))
            os.close(reader)
            os.close(writer)
            os.close(regular_fd)
        """, """
            reader, writer = os.pipe()
            os.write(writer, b"pipe")
            regular_fd = os.open(package_file, os.O_RDONLY)
            fifo = os.path.join(os.getcwd(), "fifo")
            os.mkfifo(fifo)
        """)

    def test_vercel_vendor_requires_exact_active_existing_root(self):
        self.run_isolated(FIXTURE + """
from unittest.mock import patch
vendor = "/var/task/_vendor"
realpath = os.path.realpath
isdir = os.path.isdir
def resolve(path, *args, **kwargs):
    return root if path == vendor else realpath(path, *args, **kwargs)
def existing(path):
    return path == vendor or isdir(path)
zero_data.sysconfig.get_path = lambda name: None
zero_data.site.getsitepackages = lambda: []
with patch.object(os.path, "realpath", resolve), patch.object(os.path, "isdir", existing):
    assert zero_data._discover_package_roots() == ()
    sys.path.append(vendor)
    assert zero_data._discover_package_roots() == (root,)
    with patch.object(os.path, "isdir", lambda path: False):
        assert zero_data._discover_package_roots() == ()
    zero_data.install_zero_data_guard()
with open(package_file) as stream:
    assert stream.read() == "value = 42\\n"
denied(lambda: open("/var/task/private.txt"))
zero_data.install_zero_data_guard()
assert zero_data._trusted_package_roots == (root,)
""")

    @unittest.skipUnless(
        importlib.util.find_spec("anyio") and importlib.util.find_spec("starlette"),
        "requires backend dependencies",
    )
    def test_lazy_anyio_backend_and_starlette_threadpool(self):
        self.run_isolated("""
            import asyncio
            import sys
            import anyio
            from starlette.applications import Starlette
            from starlette.concurrency import run_in_threadpool
            from starlette.responses import PlainTextResponse
            from starlette.routing import Route
            from zero_data import assert_no_file_io, install_zero_data_guard

            def robots(request):
                return PlainTextResponse("User-agent: *")

            app = Starlette(routes=[Route("/robots.txt", robots)])
            assert "anyio._backends._asyncio" not in sys.modules
            install_zero_data_guard()

            async def main():
                messages = []
                async def receive():
                    return {"type": "http.request", "body": b"", "more_body": False}
                async def send(message):
                    messages.append(message)
                await app({
                    "type": "http", "asgi": {"version": "3.0"},
                    "http_version": "1.1", "method": "GET", "scheme": "http",
                    "path": "/robots.txt", "query_string": b"", "headers": [],
                    "client": ("127.0.0.1", 12345), "server": ("test", 80),
                }, receive, send)
                assert messages[0]["status"] == 200
                assert messages[1]["body"] == b"User-agent: *"
                assert await run_in_threadpool(lambda: "User-agent: *") == "User-agent: *"
                assert await anyio.to_thread.run_sync(lambda: 42) == 42

            asyncio.run(main())
            assert "anyio._backends._asyncio" in sys.modules
            assert_no_file_io()
        """)


if __name__ == "__main__":
    unittest.main()
