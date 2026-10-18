import os
import subprocess
import sys
import textwrap
import unittest


SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))

_PRELUDE = """
import os
import sys
from pathlib import Path
import zero_data

base = Path(os.environ["GUARD_FIXTURE_DIR"])

def denied(operation):
    before = zero_data._blocked_file_io_attempts
    try:
        operation()
    except PermissionError:
        pass
    else:
        raise AssertionError("operation was allowed")
    assert zero_data._blocked_file_io_attempts == before + 1
    try:
        zero_data.assert_no_file_io()
    except PermissionError as error:
        assert str(before + 1) + " file I/O attempt(s) blocked" in str(error)
    else:
        raise AssertionError("blocked attempt was forgotten")

def fixture_install():
    root = base / "installed"
    root.mkdir()
    (root / "package.py").write_text("value = 17")
    zero_data.sysconfig.get_paths = lambda: dict.fromkeys(
        ("stdlib", "platstdlib", "purelib", "platlib"), str(root)
    )
    zero_data.site.getsitepackages = lambda: []
    zero_data.site.ENABLE_USER_SITE = False
    return root
"""


class ZeroDataGuardTests(unittest.TestCase):
    def run_isolated(self, code):
        # The outer child owns cleanup: the inner child's audit hook is permanent.
        wrapper = """
import os
import subprocess
import sys
import tempfile
with tempfile.TemporaryDirectory() as directory:
    result = subprocess.run(
        [sys.executable, "-B", "-c", sys.argv[1]],
        env={**os.environ, "GUARD_FIXTURE_DIR": directory},
    )
    sys.exit(result.returncode)
"""
        result = subprocess.run(
            [sys.executable, "-B", "-c", textwrap.dedent(wrapper),
             textwrap.dedent(_PRELUDE) + textwrap.dedent(code)],
            env={**os.environ, "PYTHONPATH": SRC_DIR, "PYTHONDONTWRITEBYTECODE": "1"},
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_installed_package_reads_and_idempotent_discovery(self):
        self.run_isolated("""
            import anyio
            package = Path(anyio.__file__)
            expected = package.read_bytes()
            zero_data.install_zero_data_guard()
            roots = zero_data._trusted_read_roots
            zero_data._discover_trusted_read_roots = lambda: 1 / 0
            zero_data.install_zero_data_guard()
            assert zero_data._trusted_read_roots == roots
            assert package.read_bytes() == expected
            assert open(os.fsencode(package), "rb").read() == expected
            fd = os.open(package, os.O_RDONLY | os.O_CLOEXEC)
            assert os.read(fd, len(expected)) == expected
            os.close(fd)
            zero_data.assert_no_file_io()
        """)

    def test_lazy_anyio_backend_import(self):
        self.run_isolated("""
            import anyio
            assert "anyio._backends._asyncio" not in sys.modules
            zero_data.install_zero_data_guard()
            import anyio._backends._asyncio
            zero_data.assert_no_file_io()
        """)

    def test_starlette_threadpool_lazily_imports_backend(self):
        self.run_isolated("""
            import asyncio
            import threading
            from starlette.concurrency import run_in_threadpool
            assert "anyio._backends._asyncio" not in sys.modules
            main_thread = threading.get_ident()
            zero_data.install_zero_data_guard()
            async def exercise():
                assert await run_in_threadpool(lambda: 17) == 17
                assert await run_in_threadpool(threading.get_ident) != main_thread
            asyncio.run(exercise())
            assert "anyio._backends._asyncio" in sys.modules
            zero_data.assert_no_file_io()
        """)

    def test_modes_flags_and_filesystem_mutations_are_denied(self):
        self.run_isolated("""
            root = fixture_install()
            target = root / "package.py"
            zero_data.install_zero_data_guard()
            for mode in ("w", "a", "x", "r+", "w+", "a+", "wb", "ab"):
                denied(lambda: open(target, mode))
            for flag in (
                os.O_WRONLY, os.O_RDWR, os.O_APPEND, os.O_CREAT, os.O_TRUNC,
                os.O_EXCL, getattr(os, "O_TMPFILE", os.O_CREAT),
            ):
                denied(lambda: os.open(target, os.O_RDONLY | flag))
            for args in (
                (str(target), "r", os.O_TRUNC),
                (str(target), None, os.O_CREAT),
                (str(target), "r", -1),
                (str(target), "r", 1 << 30),
                (str(target), "r", True),
                (str(target), "r"),
            ):
                denied(lambda: sys.audit("open", *args))
            for operation in (
                lambda: os.mkdir(root / "new"),
                lambda: os.remove(target),
                lambda: os.rename(target, root / "renamed"),
                lambda: os.chmod(target, 0o600),
                lambda: os.truncate(target, 0),
                lambda: os.listdir(base),
                lambda: os.scandir(root),
                lambda: os.symlink(target, root / "link"),
            ):
                denied(operation)
            assert target.read_text() == "value = 17"
            assert os.listdir(root) == ["package.py"]
        """)

    def test_unrelated_reads_and_path_escapes_are_denied(self):
        self.run_isolated("""
            root = fixture_install()
            outside = base / "secret"
            outside.write_text("not a dependency")
            sibling = base / "installed-extra"
            sibling.mkdir()
            (sibling / "secret").write_text("prefix escape")
            (root / "escape").symlink_to(outside)
            (root / "directory-escape").symlink_to(sibling, target_is_directory=True)
            (root / "loop").symlink_to(root / "loop")
            regular_fd = os.open(root / "package.py", os.O_RDONLY)
            directory_fd = os.open(root, os.O_RDONLY)
            os.chdir(root)
            zero_data.install_zero_data_guard()
            for path in (
                outside, sibling / "secret", root / "escape",
                root / "directory-escape" / "secret",
                root / ".." / "secret",
                root / ".." / "installed" / "package.py",
                root / "loop", base / "missing",
                os.fsencode(outside), SRC_FILE,
            ):
                denied(lambda: open(path, "rb"))
            denied(lambda: open(regular_fd, "r", closefd=False))
            denied(lambda: os.open("package.py", os.O_RDONLY, dir_fd=directory_fd))
            denied(lambda: open("package.py"))
            os.close(regular_fd)
            os.close(directory_fd)
        """.replace("SRC_FILE", repr(os.path.join(SRC_DIR, "zero_data.py"))))

    def test_arbitrary_sys_path_and_package_directory_names_are_not_trusted(self):
        self.run_isolated("""
            fixture_install()
            untrusted = []
            for name in ("site-packages", "_vendor", "application"):
                root = base / name
                root.mkdir()
                path = root / "fake.py"
                path.write_text("not installed")
                untrusted.append(path)
                sys.path.insert(0, str(root))
            zero_data.install_zero_data_guard()
            for path in untrusted:
                denied(lambda: open(path))
        """)

    def test_vendor_requires_distribution_backing_a_loaded_module(self):
        self.run_isolated("""
            import types
            fixture_install()
            vendor = base / "_vendor"
            vendor.mkdir()
            package = vendor / "fixture.py"
            package.write_text("value = 17")
            dist = vendor / "fixture-1.0.dist-info"
            dist.mkdir()
            (dist / "METADATA").write_text("Name: fixture\\nVersion: 1.0\\n")
            (dist / "RECORD").write_text("fixture.py,,\\n")
            zero_data._VERCEL_VENDOR_ROOT = str(vendor)
            assert str(vendor) not in zero_data._discover_trusted_read_roots()
            module = types.ModuleType("fixture")
            module.__file__ = str(package)
            sys.modules["fixture"] = module
            assert str(vendor) in zero_data._discover_trusted_read_roots()
            (dist / "RECORD").write_text("../secret,,\\n")
            assert str(vendor) not in zero_data._discover_trusted_read_roots()
            (dist / "RECORD").write_text("fixture.py,,\\n")
            zero_data.install_zero_data_guard()
            assert package.read_text() == "value = 17"
            denied(lambda: open(package, "w"))
            denied(lambda: open(base / "application.py"))
        """)

    def test_vendored_anyio_threadpool_and_vendor_symlink_rejection(self):
        self.run_isolated("""
            import asyncio
            import shutil
            from importlib import metadata
            vendor = base / "_vendor"
            vendor.mkdir()
            distribution = metadata.distribution("anyio")
            shutil.copytree(distribution.locate_file("anyio"), vendor / "anyio")
            for entry in distribution.files:
                if str(entry).endswith(".dist-info/METADATA"):
                    source = distribution.locate_file(entry).parent
                    shutil.copytree(source, vendor / source.name)
                    break
            sys.path.insert(0, str(vendor))
            from starlette.concurrency import run_in_threadpool
            import anyio
            assert str(vendor) in anyio.__file__
            assert "anyio._backends._asyncio" not in sys.modules
            alias = base / "vendor-alias"
            alias.symlink_to(vendor, target_is_directory=True)
            zero_data._VERCEL_VENDOR_ROOT = str(alias)
            assert str(vendor) not in zero_data._discover_trusted_read_roots()
            zero_data._VERCEL_VENDOR_ROOT = str(vendor)
            zero_data.install_zero_data_guard()
            assert str(vendor) in zero_data._trusted_read_roots
            async def exercise():
                assert await run_in_threadpool(lambda: 42) == 42
            asyncio.run(exercise())
            zero_data.assert_no_file_io()
        """)

    def test_read_only_pipes_preserved_without_descriptor_write_bypass(self):
        self.run_isolated("""
            read_fd, write_fd = os.pipe()
            os.write(write_fd, b"pipe data")
            os.close(write_fd)
            zero_data.install_zero_data_guard()
            pipe = os.fdopen(read_fd, "r")
            assert pipe.read() == "pipe data"
            pipe.close()
            zero_data.assert_no_file_io()
            read_fd, write_fd = os.pipe()
            denied(lambda: os.fdopen(write_fd, "w"))
            denied(lambda: sys.audit("open", read_fd, "r", os.O_TRUNC))
            denied(lambda: sys.audit("open", read_fd, "r", os.O_APPEND))
            os.close(read_fd)
            os.close(write_fd)
        """)
