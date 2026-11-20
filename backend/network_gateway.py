"""Authenticated HTTP boundary for the isolated SCANDOC network gateway."""

import asyncio
import json
import threading

from fastapi import APIRouter, HTTPException, Request

if __package__:
    from ..src.network_gateway import GatewayError, NetworkGateway
else:
    from network_gateway import GatewayError, NetworkGateway

router = APIRouter()
_gateway = None
_gateway_lock = threading.Lock()
_MAX_INBOUND_BYTES = 1_048_576


def _configured_gateway():
    global _gateway
    with _gateway_lock:
        if _gateway is None:
            _gateway = NetworkGateway.from_env()
        return _gateway


@router.post("/scandoc/network/dispatch")
async def dispatch_network_request(request: Request):
    raw = await request.body()
    if len(raw) > _MAX_INBOUND_BYTES:
        raise HTTPException(413, "Request body exceeds the gateway limit")
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(400, "A valid JSON request is required") from None

    try:
        gateway = _configured_gateway()
        result = await asyncio.to_thread(
            gateway.dispatch,
            payload,
            request.headers.get("authorization"),
        )
        return result
    except GatewayError as error:
        detail = {"code": error.code}
        receipt = getattr(error, "receipt", None)
        if receipt is not None:
            detail["receipt"] = receipt
        raise HTTPException(error.status_code, detail) from None
