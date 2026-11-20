"""Opt-in, policy-enforced network access outside the geometry runtime."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from http.client import HTTPSConnection
from typing import Any, Callable
from urllib.parse import quote, urlencode, urlsplit


_NAME = re.compile(r"[a-z][a-z0-9_-]{0,63}\Z")
_REPOSITORY = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
_SHA512 = re.compile(r"[0-9a-f]{128}\Z")
_ALLOWED_MODES = {"observation", "analysis"}
_MAX_AUDIT_RECEIPTS = 512


class GatewayError(ValueError):
    def __init__(self, code: str, status_code: int = 400):
        super().__init__(code)
        self.code = code
        self.status_code = status_code


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _digest(value: bytes) -> str:
    return hashlib.sha512(value).hexdigest()


def _positive_int(value: Any, maximum: int, code: str) -> int:
    if type(value) is not int or not 1 <= value <= maximum:
        raise GatewayError(code, 503)
    return value


class NetworkGateway:
    """Only dispatches configured operations; never grants lifecycle authority."""

    def __init__(
        self,
        services: dict[str, dict[str, Any]],
        inbound_token: str,
        *,
        credential_lookup: Callable[[str], str | None] = os.getenv,
        transport: Callable[..., tuple[int, bytes, str]] | None = None,
        clock: Callable[[], float] = time.monotonic,
        utcnow: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ):
        if not isinstance(inbound_token, str) or not inbound_token:
            raise GatewayError("INBOUND_AUTH_NOT_CONFIGURED", 503)
        if type(services) is not dict or not services:
            raise GatewayError("NO_NETWORK_SERVICES_CONFIGURED", 503)
        self._token = inbound_token
        self._credential_lookup = credential_lookup
        self._transport = transport or self._https_transport
        self._clock = clock
        self._utcnow = utcnow
        self._policies = {
            name: self._parse_service(name, raw) for name, raw in services.items()
        }
        self._lock = threading.Lock()
        self._rate_windows: dict[tuple[str, str], deque[float]] = defaultdict(deque)
        self._receipts: deque[dict[str, Any]] = deque(maxlen=_MAX_AUDIT_RECEIPTS)

    @classmethod
    def from_env(cls) -> "NetworkGateway":
        if os.getenv("SCANDOC_GATEWAY_ENABLED", "").lower() != "true":
            raise GatewayError("NETWORK_GATEWAY_DISABLED", 404)
        raw = os.getenv("SCANDOC_GATEWAY_SERVICES", "")
        try:
            services = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            raise GatewayError("NETWORK_SERVICE_CONFIGURATION_INVALID", 503) from None
        return cls(services, os.getenv("SCANDOC_GATEWAY_INBOUND_TOKEN", ""))

    @staticmethod
    def _parse_service(name: str, raw: Any) -> dict[str, Any]:
        if not isinstance(name, str) or not _NAME.fullmatch(name) or type(raw) is not dict:
            raise GatewayError("NETWORK_SERVICE_CONFIGURATION_INVALID", 503)
        required = {
            "base_url",
            "credential_env",
            "operations",
            "rate_limit_per_minute",
            "request_bytes",
            "response_bytes",
            "timeout_seconds",
        }
        optional = {"repositories", "models"}
        if set(raw) - required - optional or required - set(raw):
            raise GatewayError("NETWORK_SERVICE_CONFIGURATION_INVALID", 503)

        base_url = raw["base_url"]
        if not isinstance(base_url, str):
            raise GatewayError("NETWORK_SERVICE_CONFIGURATION_INVALID", 503)
        parsed = urlsplit(base_url)
        try:
            port = parsed.port
        except ValueError:
            raise GatewayError("NETWORK_SERVICE_CONFIGURATION_INVALID", 503) from None
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path not in ("", "/")
            or parsed.query
            or parsed.fragment
            or port not in (None, 443)
        ):
            raise GatewayError("NETWORK_SERVICE_CONFIGURATION_INVALID", 503)

        credential_env = raw["credential_env"]
        if not isinstance(credential_env, str) or not re.fullmatch(
            r"[A-Z][A-Z0-9_]{0,127}", credential_env
        ):
            raise GatewayError("NETWORK_SERVICE_CONFIGURATION_INVALID", 503)

        repositories = raw.get("repositories", [])
        if (
            type(repositories) is not list
            or not all(
                isinstance(repo, str) and _REPOSITORY.fullmatch(repo)
                for repo in repositories
            )
        ):
            raise GatewayError("NETWORK_SERVICE_CONFIGURATION_INVALID", 503)
        models = raw.get("models", [])
        if (
            type(models) is not list
            or not all(
                isinstance(model, str) and 1 <= len(model) <= 128
                for model in models
            )
        ):
            raise GatewayError("NETWORK_SERVICE_CONFIGURATION_INVALID", 503)

        operations = raw["operations"]
        if type(operations) is not dict or not operations:
            raise GatewayError("NETWORK_SERVICE_CONFIGURATION_INVALID", 503)
        parsed_operations = {}
        for operation, policy in operations.items():
            if (
                not isinstance(operation, str)
                or not _NAME.fullmatch(operation)
                or type(policy) is not dict
                or set(policy) != {"method", "path", "modes"}
            ):
                raise GatewayError("NETWORK_SERVICE_CONFIGURATION_INVALID", 503)
            method, path, modes = policy["method"], policy["path"], policy["modes"]
            if (
                method not in {"GET", "POST"}
                or not isinstance(path, str)
                or not path.startswith("/")
                or path.startswith("//")
                or "\\" in path
                or "?" in path
                or "#" in path
                or "%" in path
                or any(segment in {".", ".."} for segment in path.split("/"))
                or set(re.findall(r"\{([^{}]+)\}", path)) - {"repository"}
                or ("{" in re.sub(r"\{repository\}", "", path))
                or ("}" in re.sub(r"\{repository\}", "", path))
                or type(modes) is not list
                or not modes
                or not set(modes) <= _ALLOWED_MODES
                or (method == "POST" and "observation" in modes)
            ):
                raise GatewayError("NETWORK_SERVICE_CONFIGURATION_INVALID", 503)
            parsed_operations[operation] = {
                "method": method,
                "path": path,
                "modes": frozenset(modes),
            }

        rate = _positive_int(raw["rate_limit_per_minute"], 1000, "RATE_LIMIT_INVALID")
        request_bytes = _positive_int(raw["request_bytes"], 1_048_576, "REQUEST_LIMIT_INVALID")
        response_bytes = _positive_int(raw["response_bytes"], 4_194_304, "RESPONSE_LIMIT_INVALID")
        timeout = raw["timeout_seconds"]
        if type(timeout) not in (int, float) or not 0 < timeout <= 30:
            raise GatewayError("NETWORK_SERVICE_CONFIGURATION_INVALID", 503)
        return {
            "host": parsed.hostname,
            "operations": parsed_operations,
            "credential_env": credential_env,
            "repositories": frozenset(repositories),
            "models": frozenset(models),
            "rate": rate,
            "request_bytes": request_bytes,
            "response_bytes": response_bytes,
            "timeout": float(timeout),
        }

    @staticmethod
    def _https_transport(
        *,
        host: str,
        method: str,
        target: str,
        headers: dict[str, str],
        body: bytes | None,
        timeout: float,
        response_bytes: int,
    ) -> tuple[int, bytes, str]:
        connection = HTTPSConnection(host, port=443, timeout=timeout)
        try:
            connection.request(method, target, body=body, headers=headers)
            response = connection.getresponse()
            payload = response.read(response_bytes + 1)
            if len(payload) > response_bytes:
                raise GatewayError("UPSTREAM_RESPONSE_TOO_LARGE", 502)
            return response.status, payload, response.getheader("Content-Type", "")
        finally:
            connection.close()

    def _rate_limit(self, service: str, operation: str, limit: int) -> None:
        now = self._clock()
        with self._lock:
            window = self._rate_windows[(service, operation)]
            while window and now - window[0] >= 60:
                window.popleft()
            if len(window) >= limit:
                raise GatewayError("RATE_LIMIT_EXCEEDED", 429)
            window.append(now)

    def _record(
        self,
        service: str,
        operation: str,
        mode: str,
        request_digest: str,
        provenance: dict[str, Any],
        status: int | None,
        response_digest: str | None,
        outcome: str,
    ) -> dict[str, Any]:
        receipt_body = {
            "schema": "scandoc-network-receipt/1",
            "service": service,
            "operation": operation,
            "mode": mode,
            "request_digest": request_digest,
            "source_provenance": provenance,
            "upstream_status": status,
            "response_digest": response_digest,
            "outcome": outcome,
            "observed_at": self._utcnow().isoformat(),
            "receipt_kind": "temporal-observation-not-authority",
        }
        receipt = {**receipt_body, "receipt_digest": _digest(_canonical(receipt_body))}
        with self._lock:
            self._receipts.append(receipt)
        return receipt

    def receipts(self) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(receipt) for receipt in self._receipts]

    def dispatch(self, request: Any, authorization: str | None) -> dict[str, Any]:
        if not hmac.compare_digest(authorization or "", "Bearer " + self._token):
            raise GatewayError("AUTHENTICATION_REQUIRED", 401)
        return self._dispatch(request)

    def dispatch_internal(self, request: Any) -> dict[str, Any]:
        """Dispatch for trusted server code without exposing inbound auth tokens."""
        return self._dispatch(request)

    def _dispatch(self, request: Any) -> dict[str, Any]:
        expected = {
            "service",
            "operation",
            "mode",
            "data_classification",
            "provenance",
            "payload",
        }
        if type(request) is not dict or set(request) - (expected | {"repository"}) or not expected <= set(request):
            raise GatewayError("REQUEST_SCHEMA_INVALID", 400)
        service_name, operation_name, mode = (
            request["service"],
            request["operation"],
            request["mode"],
        )
        if not all(
            isinstance(value, str) and _NAME.fullmatch(value)
            for value in (service_name, operation_name, mode)
        ):
            raise GatewayError("REQUEST_SCHEMA_INVALID", 400)
        if mode not in _ALLOWED_MODES:
            raise GatewayError("AUTHORITY_MODE_FORBIDDEN", 403)
        classification = request["data_classification"]
        if not isinstance(classification, str) or classification not in {
            "public",
            "synthetic",
        }:
            raise GatewayError("DATA_CLASSIFICATION_FORBIDDEN", 403)

        provenance = request["provenance"]
        if (
            type(provenance) is not dict
            or set(provenance) != {"source", "revision", "sha512"}
            or not isinstance(provenance["source"], str)
            or not provenance["source"]
            or len(provenance["source"]) > 2048
            or not isinstance(provenance["revision"], str)
            or not provenance["revision"]
            or len(provenance["revision"]) > 256
            or not isinstance(provenance["sha512"], str)
            or not _SHA512.fullmatch(provenance["sha512"])
        ):
            raise GatewayError("PROVENANCE_REQUIRED", 400)
        try:
            policy = self._policies[service_name]
            operation = policy["operations"][operation_name]
        except KeyError:
            raise GatewayError("OPERATION_NOT_ALLOWLISTED", 403) from None
        if mode not in operation["modes"]:
            raise GatewayError("MODE_NOT_ALLOWLISTED", 403)

        repository = request.get("repository")
        path = operation["path"]
        if "{repository}" in path:
            if (
                not isinstance(repository, str)
                or not _REPOSITORY.fullmatch(repository)
                or repository not in policy["repositories"]
            ):
                raise GatewayError("REPOSITORY_NOT_ALLOWLISTED", 403)
            path = path.replace("{repository}", quote(repository, safe="/"))
        elif repository is not None:
            raise GatewayError("REPOSITORY_NOT_APPLICABLE", 400)

        method = operation["method"]
        payload = request["payload"]
        if policy["models"] and (
            type(payload) is not dict or payload.get("model") not in policy["models"]
        ):
            raise GatewayError("MODEL_NOT_ALLOWLISTED", 403)
        if method == "GET":
            if payload is None:
                query = ""
            elif type(payload) is dict and all(
                isinstance(key, str)
                and isinstance(value, (str, int, bool))
                and type(value) is not float
                for key, value in payload.items()
            ):
                query = urlencode(sorted(payload.items()))
            else:
                raise GatewayError("GET_PAYLOAD_INVALID", 400)
            target = path + (f"?{query}" if query else "")
            body = None
        else:
            try:
                body = _canonical(payload)
            except (TypeError, ValueError, UnicodeEncodeError):
                raise GatewayError("POST_PAYLOAD_INVALID", 400) from None
            if len(body) > policy["request_bytes"]:
                raise GatewayError("REQUEST_TOO_LARGE", 413)
            target = path
        encoded_request = _canonical(
            {
                "service": service_name,
                "operation": operation_name,
                "mode": mode,
                "classification": request["data_classification"],
                "provenance": provenance,
                "payload": payload,
                "repository": repository,
            }
        )
        if len(encoded_request) > policy["request_bytes"]:
            raise GatewayError("REQUEST_TOO_LARGE", 413)

        credential = self._credential_lookup(policy["credential_env"])
        if not credential:
            raise GatewayError("OUTBOUND_CREDENTIAL_NOT_CONFIGURED", 503)
        self._rate_limit(service_name, operation_name, policy["rate"])
        headers = {
            "Accept": "application/json",
            "User-Agent": "SCANDOC-Zero-Network-Gateway/1",
        }
        if body is not None:
            headers["Content-Type"] = "application/json"
        headers["Authorization"] = "Bearer " + credential
        request_digest = _digest(encoded_request)

        try:
            status, response_body, content_type = self._transport(
                host=policy["host"],
                method=method,
                target=target,
                headers=headers,
                body=body,
                timeout=policy["timeout"],
                response_bytes=policy["response_bytes"],
            )
            response_digest = _digest(response_body)
            receipt = self._record(
                service_name,
                operation_name,
                mode,
                request_digest,
                provenance,
                status,
                response_digest,
                "completed",
            )
        except Exception as error:
            receipt = self._record(
                service_name,
                operation_name,
                mode,
                request_digest,
                provenance,
                None,
                None,
                "transport-error",
            )
            if isinstance(error, GatewayError):
                error.receipt = receipt
                raise
            raise GatewayError("UPSTREAM_REQUEST_FAILED", 502) from None

        try:
            response = json.loads(response_body) if response_body else None
        except (json.JSONDecodeError, UnicodeDecodeError):
            response = response_body.decode("utf-8", errors="replace")
        return {
            "upstream_status": status,
            "content_type": content_type,
            "response": response,
            "receipt": receipt,
            "native_gate": "CLOSED",
            "writes_permitted": False,
        }
