"""Tests for the HelioClient GraphQL client."""

import requests as req
import responses

from helio_api.client import HelioClient


@responses.activate
def test_query_success():
    """Successful GraphQL query returns (data, None, trace_id)."""
    responses.add(
        responses.POST,
        HelioClient.DEFAULT_API_URL,
        json={"data": {"user": {"remainingOptsThisMonth": 5}}},
        status=200,
        headers={"trace-id": "abc123"},
    )
    client = HelioClient("test-pat")
    data, errors, trace_id = client.query("query { user { remainingOptsThisMonth } }")
    assert data == {"user": {"remainingOptsThisMonth": 5}}
    assert errors is None
    assert trace_id == "abc123"


@responses.activate
def test_query_401():
    """401 response returns appropriate error."""
    responses.add(responses.POST, HelioClient.DEFAULT_API_URL, status=401)
    client = HelioClient("bad-pat")
    data, errors, trace_id = client.query("query { user { id } }")
    assert data is None
    assert errors == ["HTTP 401 Unauthorized - check your PAT token."]


@responses.activate
def test_query_429():
    """429 response returns quota exceeded error."""
    responses.add(responses.POST, HelioClient.DEFAULT_API_URL, status=429)
    client = HelioClient("test-pat")
    data, errors, trace_id = client.query("query { user { id } }")
    assert data is None
    assert errors == ["HTTP 429 - quota exceeded or rate limited."]


@responses.activate
def test_query_graphql_errors():
    """GraphQL errors in response body are extracted."""
    responses.add(
        responses.POST,
        HelioClient.DEFAULT_API_URL,
        json={"data": None, "errors": [{"message": "Not found"}]},
        status=200,
    )
    client = HelioClient("test-pat")
    data, errors, trace_id = client.query('query { simulation(id: "x") { id } }')
    assert errors == ["Not found"]


@responses.activate
def test_query_network_error():
    """Network errors are caught and returned as errors."""
    responses.add(
        responses.POST,
        HelioClient.DEFAULT_API_URL,
        body=req.exceptions.ConnectionError("connection refused"),
    )
    client = HelioClient("test-pat")
    data, errors, trace_id = client.query("query { user { id } }")
    assert data is None
    assert len(errors) == 1
    assert "Network error" in errors[0]


def test_custom_api_url():
    """Client accepts custom API URL."""
    client = HelioClient("pat", api_url="https://custom.example.com/graphql")
    assert client.api_url == "https://custom.example.com/graphql"


def test_default_api_url():
    """Client uses global production URL by default."""
    client = HelioClient("pat")
    assert "api.helioadditive.com" in client.api_url


def test_env_api_url(monkeypatch):
    """Client reads HELIO_API_URL env var when no explicit URL given."""
    monkeypatch.setenv("HELIO_API_URL", "https://api.helioam.cn/graphql")
    client = HelioClient("pat")
    assert client.api_url == "https://api.helioam.cn/graphql"


def test_explicit_url_overrides_env(monkeypatch):
    """Explicit api_url takes precedence over env var."""
    monkeypatch.setenv("HELIO_API_URL", "https://api.helioam.cn/graphql")
    client = HelioClient("pat", api_url="https://custom.example.com/graphql")
    assert client.api_url == "https://custom.example.com/graphql"


def test_headers_contain_auth():
    """Headers include Bearer token and client identifiers."""
    client = HelioClient("my-secret-token")
    headers = client._get_headers()
    assert headers["Authorization"] == "Bearer my-secret-token"
    assert headers["HelioAdditive-Client-Name"] == "PythonScript"
    assert headers["Content-Type"] == "application/json"
