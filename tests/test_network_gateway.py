import hashlib
import json
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from src import multi_llm_council
from src.network_gateway import GatewayError, NetworkGateway


PROVENANCE = {
    "source": "https://example.test/research",
    "revision": "fixture-v1",
    "sha512": hashlib.sha512(b"fixture").hexdigest(),
}


def services(rate=5, response_bytes=4096):
    return {
        "github": {
            "base_url": "https://api.github.com",
            "credential_env": "GITHUB_APP_TOKEN",
            "repositories": ["team/private-repo"],
            "operations": {
                "contents": {
                    "method": "GET",
                    "path": "/repos/{repository}/contents",
                    "modes": ["observation"],
                }
            },
            "rate_limit_per_minute": rate,
            "request_bytes": 4096,
            "response_bytes": response_bytes,
            "timeout_seconds": 5,
        },
        "openrouter": {
            "base_url": "https://openrouter.ai",
            "credential_env": "OPENROUTER_KEY",
            "models": ["provider/model-a"],
            "operations": {
                "chat_completions": {
                    "method": "POST",
                    "path": "/api/v1/chat/completions",
                    "modes": ["analysis"],
                }
            },
            "rate_limit_per_minute": rate,
            "request_bytes": 4096,
            "response_bytes": response_bytes,
            "timeout_seconds": 5,
        },
    }


def request(service="github", operation="contents", mode="observation", **extra):
    return {
        "service": service,
        "operation": operation,
        "mode": mode,
        "data_classification": "public",
        "provenance": PROVENANCE,
        "payload": {"ref": "main"} if service == "github" else None,
        **extra,
    }


class NetworkGatewayTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.now = 0.0
        self.response = (200, b'{"ok":true}', "application/json")
        self.gateway = self.make_gateway()

    def make_gateway(self, **kwargs):
        def transport(**call):
            self.calls.append(call)
            if isinstance(self.response, Exception):
                raise self.response
            return self.response

        return NetworkGateway(
            services=kwargs.pop("policies", services()),
            inbound_token="inbound-" + "secret",
            credential_lookup=lambda name: "server-side-" + "secret",
            transport=kwargs.pop("transport", transport),
            clock=lambda: self.now,
            utcnow=lambda: datetime(2026, 1, 2, tzinfo=timezone.utc),
        )

    def dispatch(self, payload=None, authorization="Bearer " + "inbound-secret"):
        return self.gateway.dispatch(
            payload or request(repository="team/private-repo"),
            authorization,
        )

    def test_allowed_repository_request_uses_fixed_https_policy(self):
        result = self.dispatch()

        self.assertEqual(len(self.calls), 1)
        call = self.calls[0]
        self.assertEqual(call["host"], "api.github.com")
        self.assertEqual(call["method"], "GET")
        self.assertEqual(
            call["target"], "/repos/team/private-repo/contents?ref=main"
        )
        self.assertEqual(
            call["headers"]["Authorization"], "Bearer " + "server-side-secret"
        )
        receipt = result["receipt"]
        self.assertEqual(receipt["schema"], "scandoc-network-receipt/1")
        self.assertEqual(receipt["source_provenance"], PROVENANCE)
        self.assertEqual(receipt["receipt_kind"], "temporal-observation-not-authority")
        self.assertEqual(result["native_gate"], "CLOSED")
        self.assertFalse(result["writes_permitted"])
        self.assertNotIn("server-side-" + "secret", json.dumps(receipt))
        self.assertEqual(len(self.gateway.receipts()), 1)

    def test_inbound_authentication_is_required(self):
        with self.assertRaises(GatewayError) as raised:
            self.dispatch(authorization="wrong")

        self.assertEqual(raised.exception.status_code, 401)
        self.assertEqual(self.calls, [])

    def test_authority_and_personal_data_are_rejected(self):
        for payload, expected in (
            (request(mode="authority", repository="team/private-repo"), "AUTHORITY_MODE_FORBIDDEN"),
            (
                {
                    **request(repository="team/private-repo"),
                    "data_classification": "personal",
                },
                "DATA_CLASSIFICATION_FORBIDDEN",
            ),
        ):
            with self.subTest(expected=expected), self.assertRaises(GatewayError) as raised:
                self.dispatch(payload)
            self.assertEqual(raised.exception.code, expected)
        self.assertEqual(self.calls, [])

    def test_repository_operation_and_model_allowlists_are_enforced(self):
        for payload, expected in (
            (
                request(repository="team/other-repo"),
                "REPOSITORY_NOT_ALLOWLISTED",
            ),
            (
                request(operation="arbitrary", repository="team/private-repo"),
                "OPERATION_NOT_ALLOWLISTED",
            ),
            (
                request(
                    service="openrouter",
                    operation="chat_completions",
                    mode="analysis",
                    payload={"model": "provider/not-approved"},
                ),
                "MODEL_NOT_ALLOWLISTED",
            ),
        ):
            with self.subTest(expected=expected), self.assertRaises(GatewayError) as raised:
                self.dispatch(payload)
            self.assertEqual(raised.exception.code, expected)
        self.assertEqual(self.calls, [])

    def test_analysis_call_is_bounded_and_authorized_by_server_secret(self):
        result = self.dispatch(
            request(
                service="openrouter",
                operation="chat_completions",
                mode="analysis",
                payload={"model": "provider/model-a", "messages": []},
            )
        )

        call = self.calls[0]
        self.assertEqual(call["host"], "openrouter.ai")
        self.assertEqual(call["method"], "POST")
        self.assertEqual(call["target"], "/api/v1/chat/completions")
        self.assertEqual(json.loads(call["body"]), {"model": "provider/model-a", "messages": []})
        self.assertEqual(result["response"], {"ok": True})

    def test_untrusted_configuration_and_protocols_are_rejected(self):
        invalid = services()
        invalid["github"]["base_url"] = "http://api.github.com"
        with self.assertRaises(GatewayError):
            self.make_gateway(policies=invalid)

        invalid = services()
        invalid["github"]["operations"]["contents"]["path"] = "/repos/{repository}/../admin"
        with self.assertRaises(GatewayError):
            self.make_gateway(policies=invalid)

        invalid = services()
        invalid["github"]["base_url"] = "https://127.0.0.1"
        with self.assertRaises(GatewayError):
            self.make_gateway(policies=invalid)

    def test_rate_limit_and_expiry(self):
        self.gateway = self.make_gateway(policies=services(rate=1))
        self.dispatch()
        with self.assertRaises(GatewayError) as raised:
            self.dispatch()
        self.assertEqual(raised.exception.code, "RATE_LIMIT_EXCEEDED")
        self.now = 60.0
        self.dispatch()
        self.assertEqual(len(self.calls), 2)

    def test_oversized_and_failed_upstream_responses_get_audit_receipts(self):
        self.gateway = self.make_gateway(
            policies=services(response_bytes=4),
            transport=lambda **kwargs: (200, b"too large", "text/plain"),
        )
        with self.assertRaises(GatewayError) as raised:
            self.dispatch()
        self.assertEqual(raised.exception.code, "UPSTREAM_RESPONSE_TOO_LARGE")
        self.assertEqual(raised.exception.receipt["outcome"], "transport-error")

        self.gateway = self.make_gateway(
            transport=lambda **kwargs: (_ for _ in ()).throw(OSError("offline"))
        )
        with self.assertRaises(GatewayError) as raised:
            self.dispatch()
        self.assertEqual(raised.exception.code, "UPSTREAM_REQUEST_FAILED")
        self.assertEqual(raised.exception.receipt["outcome"], "transport-error")

    def test_upstream_response_never_returns_the_server_credential(self):
        self.gateway = self.make_gateway(
            transport=lambda **kwargs: (
                200,
                b'{"value":"server-side-secret"}',
                "application/json",
            )
        )
        with self.assertRaises(GatewayError) as raised:
            self.dispatch()
        self.assertEqual(
            raised.exception.code, "UPSTREAM_RESPONSE_CONTAINS_CREDENTIAL"
        )
        self.assertEqual(
            raised.exception.receipt["outcome"],
            "response-rejected-credential",
        )

    def test_receipt_digest_is_not_a_geometry_or_authority_commitment(self):
        result = self.dispatch()
        receipt = result["receipt"]
        digest = receipt.pop("receipt_digest")
        expected = hashlib.sha512(
            json.dumps(
                receipt,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            ).encode()
        ).hexdigest()
        self.assertEqual(digest, expected)
        self.assertEqual(result["native_gate"], "CLOSED")

    @patch.object(multi_llm_council.NetworkGateway, "from_env")
    def test_llm_council_uses_opt_in_gateway_and_explicit_classification(self, from_env):
        gateway = from_env.return_value
        gateway.dispatch_internal.return_value = {
            "upstream_status": 200,
            "response": {
                "choices": [{"message": {"content": " analysis "}}],
                "usage": {"total_tokens": 2},
            },
        }

        result = multi_llm_council.call_model(
            "provider/model-a",
            [{"role": "user", "content": "public prompt"}],
            data_classification="public",
        )

        self.assertEqual(result.content, "analysis")
        request = gateway.dispatch_internal.call_args.args[0]
        self.assertEqual(request["service"], "openrouter")
        self.assertEqual(request["mode"], "analysis")
        self.assertEqual(request["data_classification"], "public")
        self.assertEqual(request["provenance"]["source"], "caller-supplied-prompt")

    @patch.object(multi_llm_council.NetworkGateway, "from_env")
    def test_llm_council_fails_closed_without_classification_or_with_caller_key(
        self, from_env
    ):
        for kwargs in ({}, {"data_classification": "personal"}, {"api_key": "caller-key"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(RuntimeError):
                multi_llm_council.call_model(
                    "provider/model-a",
                    [{"role": "user", "content": "prompt"}],
                    **kwargs,
                )
        from_env.assert_not_called()


if __name__ == "__main__":
    unittest.main()
