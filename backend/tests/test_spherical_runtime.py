import asyncio
import json
import unittest
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

from backend.main import SPHERICAL_BRIDGE, spherical_ignite


class FakeProcess:
    def __init__(self, result, returncode=0):
        self.result = result
        self.returncode = returncode

    async def communicate(self, payload):
        self.payload = payload
        return self.result, b""


class SphericalRuntimeTests(unittest.TestCase):
    def test_spherical_request_is_forwarded_to_node_and_decoded(self):
        expected = {"status": "ok", "sourceVerified": True}
        process = FakeProcess(json.dumps(expected).encode("utf-8"))
        payload = {"scenes": [{"id": "origin", "content": "topology"}]}
        create_process = AsyncMock(return_value=process)

        with patch("backend.main.shutil.which", return_value="/usr/bin/node"), patch(
            "backend.main.asyncio.create_subprocess_exec", create_process
        ):
            result = asyncio.run(spherical_ignite(payload))

        self.assertEqual(result, expected)
        create_process.assert_awaited_once_with(
            "/usr/bin/node",
            SPHERICAL_BRIDGE,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        self.assertEqual(json.loads(process.payload), payload)

    def test_invalid_scene_count_is_rejected_before_node_launch(self):
        with patch("backend.main.shutil.which") as find_node:
            with self.assertRaises(HTTPException) as error:
                asyncio.run(spherical_ignite({"scenes": []}))

        self.assertEqual(error.exception.status_code, 422)
        find_node.assert_not_called()

    def test_missing_node_runtime_returns_service_unavailable(self):
        with patch("backend.main.shutil.which", return_value=None):
            with self.assertRaises(HTTPException) as error:
                asyncio.run(
                    spherical_ignite({"scenes": [{"id": "origin", "content": "topology"}]})
                )

        self.assertEqual(error.exception.status_code, 503)

    def test_oversized_request_is_rejected(self):
        payload = {
            "scenes": [{"id": "origin", "content": "x" * (1024 * 1024)}]
        }
        with patch("backend.main.shutil.which") as find_node:
            with self.assertRaises(HTTPException) as error:
                asyncio.run(spherical_ignite(payload))

        self.assertEqual(error.exception.status_code, 413)
        find_node.assert_not_called()


if __name__ == "__main__":
    unittest.main()
