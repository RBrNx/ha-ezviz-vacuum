"""Tests for the integration's own EZVIZ session."""

from __future__ import annotations

import sys
import types
import unittest

from _loader import load


def _stub_pyezvizapi() -> None:
    """Provide the two pyezvizapi names cloud.py imports, without the library."""
    if "pyezvizapi" in sys.modules:
        return
    package = types.ModuleType("pyezvizapi")
    package.EzvizClient = object
    constants = types.ModuleType("pyezvizapi.constants")
    constants.DEFAULT_TIMEOUT = 25
    constants.REQUEST_HEADER = {
        "featureCode": "abc",
        "sessionId": "",
        "clientType": "3",
    }
    package.constants = constants
    sys.modules["pyezvizapi"] = package
    sys.modules["pyezvizapi.constants"] = constants


_stub_pyezvizapi()
cloud_module = load("cloud")


class FakeResponse:
    def __init__(self, status: int, body: dict) -> None:
        self.status_code = status
        self._body = body

    def json(self) -> dict:
        return self._body


class FakeHttp:
    """Answer with queued responses and record what was sent."""

    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = responses
        self.calls: list[dict] = []

    def request(self, method: str, url: str, **kwargs):
        self.calls.append({"method": method, "url": url, **kwargs})
        return self.responses.pop(0)


class FakeClient:
    """Public pyezvizapi client surface used by EzvizCloud."""

    def __init__(self) -> None:
        self._token = {"api_url": "api.example.test", "session_id": "old"}
        self.logins = 0

    def export_token(self) -> dict:
        return dict(self._token)

    def login(self, sms_code=None) -> dict:
        self.logins += 1
        self._token["session_id"] = "new"
        return dict(self._token)


class CloudTests(unittest.TestCase):
    def make(self, responses: list[FakeResponse]):
        client = FakeClient()
        cloud = cloud_module.EzvizCloud(client)
        cloud._http = FakeHttp(responses)
        return client, cloud

    def test_request_uses_own_session_with_current_session_id(self) -> None:
        client, cloud = self.make([FakeResponse(200, {"meta": {"code": 200}})])
        cloud.request("PUT", "/v3/x", data="1", headers={"Content-Type": "a/b"})
        call = cloud._http.calls[0]
        self.assertEqual(call["url"], "https://api.example.test/v3/x")
        self.assertEqual(call["headers"]["sessionId"], "old")
        self.assertEqual(call["headers"]["featureCode"], "abc")
        self.assertEqual(call["headers"]["Content-Type"], "a/b")
        self.assertEqual(client.logins, 0)

    def test_expired_session_is_renewed_once(self) -> None:
        client, cloud = self.make(
            [
                FakeResponse(401, {}),
                FakeResponse(200, {"meta": {"code": 401}}),
            ]
        )
        response = cloud.request("POST", "/v3/y")
        self.assertEqual(client.logins, 1)
        self.assertEqual(len(cloud._http.calls), 2)
        self.assertEqual(cloud._http.calls[1]["headers"]["sessionId"], "new")
        # The second answer is returned as is; no endless retries.
        self.assertEqual(response.json()["meta"]["code"], 401)

    def test_no_session_is_an_error(self) -> None:
        client, cloud = self.make([])
        client._token["session_id"] = None
        with self.assertRaises(cloud_module.EzvizCloudError):
            cloud.request("GET", "/v3/z")
