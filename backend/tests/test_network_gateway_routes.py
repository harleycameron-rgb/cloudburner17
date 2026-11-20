from unittest.mock import Mock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.main import NetworkGateway, dispatch_network_request


def build_client():
    app = FastAPI()
    app.post("/scandoc/network/dispatch")(dispatch_network_request)
    return TestClient(app)


def test_dispatch_route_authenticates_and_returns_gateway_result():
    gateway = Mock()
    gateway.dispatch.return_value = {
        "upstream_status": 200,
        "response": {"observed": True},
        "receipt": {"schema": "scandoc-network-receipt/1"},
        "native_gate": "CLOSED",
        "writes_permitted": False,
    }

    with patch.object(NetworkGateway, "from_env", return_value=gateway):
        response = build_client().post(
            "/scandoc/network/dispatch",
            json={"service": "research"},
            headers={"Authorization": "Bearer " + "test-inbound-token"},
        )

    assert response.status_code == 200
    assert response.json()["native_gate"] == "CLOSED"
    gateway.dispatch.assert_called_once_with(
        {"service": "research"}, "Bearer " + "test-inbound-token"
    )


def test_dispatch_route_limits_body_before_parsing():
    response = build_client().post(
        "/scandoc/network/dispatch",
        content=b"x" * (1_048_576 + 1),
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 413
