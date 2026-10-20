import io
from urllib.error import HTTPError

import pytest

from lifecycle_mapper import acquisition, corpus


def test_truncated_tree_uses_recursive_subtrees_and_reuses_tree_sha():
    calls = []

    def get(endpoint):
        calls.append(endpoint)
        if endpoint.endswith("/root?recursive=1"):
            return {"truncated": True, "tree": []}
        if endpoint.endswith("/root"):
            return {
                "tree": [
                    {"type": "tree", "path": "left", "sha": "same"},
                    {"type": "tree", "path": "right", "sha": "same"},
                ]
            }
        assert endpoint.endswith("/same?recursive=1")
        return {
            "truncated": False,
            "tree": [
                {"type": "blob", "path": "deep/file.py", "sha": "blob", "mode": "100644", "size": 1}
            ],
        }

    inventory = acquisition.tree_inventory("a/b", "root", get)
    assert [r["path"] for r in inventory] == ["left/deep/file.py", "right/deep/file.py"]
    assert len(calls) == 3


def clock(monkeypatch):
    now = [100.0]
    sleeps = []
    monkeypatch.setattr(corpus.time, "monotonic", lambda: now[0])
    monkeypatch.setattr(corpus.time, "time", lambda: now[0])

    def sleep(delay):
        now[0] += delay
        sleeps.append(delay)

    monkeypatch.setattr(corpus.time, "sleep", sleep)
    return now, sleeps


def test_successful_last_quota_response_waits_before_next_request(monkeypatch):
    now, sleeps = clock(monkeypatch)
    timestamps = []

    def get(endpoint, *, on_response, on_request):
        on_request()
        timestamps.append(now[0])
        on_response(
            {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "200"}
            if len(timestamps) == 1
            else {}
        )
        return {}

    monkeypatch.setattr(acquisition, "api_get", get)
    gate = corpus.PacedAPI()
    gate("/one")
    gate("/two")
    assert timestamps == [100.0, 202.0]
    assert gate.network_calls == 2 and gate.rate_limit_wait_seconds == 102
    assert max(sleeps) <= 60


def test_primary_resets_can_repeat_more_than_five_times(monkeypatch):
    now, _ = clock(monkeypatch)
    calls = []

    def get(endpoint, **kwargs):
        calls.append(now[0])
        kwargs["on_request"]()
        if len(calls) <= 6:
            raise acquisition.GitHubAPIError("rate-limit", 403, reset=str(now[0] + 10))
        return {"ok": True}

    monkeypatch.setattr(acquisition, "api_get", get)
    gate = corpus.PacedAPI()
    assert gate("/one") == {"ok": True}
    assert len(calls) == 7 and all(b - a >= 12 for a, b in zip(calls, calls[1:]))


def test_secondary_limit_body_is_classified_without_reclassifying_permission_errors(monkeypatch):
    def get(request, timeout):
        raise HTTPError(
            request.full_url,
            403,
            "forbidden",
            {},
            io.BytesIO(b'{"message":"You have exceeded a secondary rate limit"}'),
        )

    monkeypatch.setattr(acquisition, "urlopen", get)
    with pytest.raises(acquisition.GitHubAPIError, match="rate-limit"):
        acquisition.api_get("/repos/a/b")

    def denied(request, timeout):
        raise HTTPError(
            request.full_url,
            403,
            "forbidden",
            {},
            io.BytesIO(b'{"message":"Resource not accessible"}'),
        )

    monkeypatch.setattr(acquisition, "urlopen", denied)
    with pytest.raises(acquisition.GitHubAPIError, match="api-http-error"):
        acquisition.api_get("/repos/a/b")


def test_success_response_forwards_quota_and_counts_network_attempts(monkeypatch):
    class Response(io.BytesIO):
        headers = {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "200"}

    monkeypatch.setattr(acquisition, "urlopen", lambda request, timeout: Response(b'{"ok":true}'))
    seen = []
    attempts = []
    assert acquisition.api_get(
        "/repos/a/b", on_response=lambda h: seen.append(h), on_request=lambda: attempts.append(1)
    ) == {"ok": True}
    assert len(attempts) == 1 and seen[0]["X-RateLimit-Remaining"] == "0"


def test_transient_http_retry_also_respects_quota_reset(monkeypatch):
    now, _ = clock(monkeypatch)
    timestamps = []

    class Response(io.BytesIO):
        headers = {}

    def get(request, timeout):
        timestamps.append(now[0])
        if len(timestamps) == 1:
            raise HTTPError(
                request.full_url,
                503,
                "unavailable",
                {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "200"},
                io.BytesIO(b"{}"),
            )
        return Response(b'{"ok":true}')

    monkeypatch.setattr(acquisition, "urlopen", get)
    gate = corpus.PacedAPI()
    assert gate("/one") == {"ok": True}
    assert timestamps == [100.0, 202.0] and gate.network_calls == 2
