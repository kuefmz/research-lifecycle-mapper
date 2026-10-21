import base64

import pytest

from lifecycle_mapper.acquisition import acquire, replay
from lifecycle_mapper.canonical import write_json
from lifecycle_mapper.text_decoding import decode_text


def test_windows_quotes_are_lossless_and_keep_lines():
    raw = b"% kinetics of the \x93allowed\x94 reactions\r\nrate = exp(x);\r\n"
    text, encoding = decode_text(raw)
    assert encoding == "windows-1252"
    assert "\u201callowed\u201d" in text
    assert text.encode("cp1252") == raw
    assert text.count("\n") == raw.count(b"\n")


def test_utf8_is_preferred():
    text = "temperature = 2; % \u00b5m\n"
    assert decode_text(text.encode()) == (text, "utf-8")


@pytest.mark.parametrize("raw", [b"\x00binary", b"\x93text\x01", b"\x81invalid"])
def test_binary_and_undefined_legacy_bytes_are_rejected(raw):
    with pytest.raises((ValueError, UnicodeDecodeError)):
        decode_text(raw)


@pytest.mark.parametrize("transport", ["api", "raw"])
def test_acquisition_and_replay_keep_raw_bytes_and_provenance(tmp_path, monkeypatch, transport):
    from lifecycle_mapper import acquisition

    raw = b"% kinetics of the \x93allowed\x94 reactions\r\nrate = exp(x);\r\n"
    commit = "a" * 40

    def api(endpoint):
        if "/branches/main" in endpoint:
            return {
                "commit": {
                    "sha": commit,
                    "commit": {"tree": {"sha": "b" * 40}},
                    "html_url": "https://github.com/a/b/commit/" + commit,
                }
            }
        if "/git/trees/" in endpoint:
            return {
                "tree": [
                    {
                        "path": "src/model.m",
                        "type": "blob",
                        "mode": "100644",
                        "sha": "c" * 40,
                        "size": len(raw),
                    }
                ],
                "truncated": False,
            }
        return {"encoding": "base64", "content": base64.b64encode(raw).decode()}

    monkeypatch.setattr(acquisition, "raw_get", lambda *args: raw)
    snapshot = tmp_path / "snapshot"
    manifest = acquire("https://github.com/a/b", snapshot, api_client=api, blob_transport=transport)
    entry = manifest["files"][0]
    assert entry["status"] == "captured"
    assert entry["text_encoding"] == "windows-1252"
    assert (snapshot / "content/src/model.m").read_bytes() == raw
    _, contents = replay(snapshot)
    assert contents["src/model.m"].encode("cp1252") == raw
    entry["text_encoding"] = "utf-8"
    write_json(snapshot / "manifest.json", manifest)
    with pytest.raises(ValueError, match="decoding provenance"):
        replay(snapshot)
    entry["text_encoding"] = "windows-1252"
    manifest["policy_version"] = "eligibility-4-txt-folder-density"
    write_json(snapshot / "manifest.json", manifest)
    with pytest.raises(UnicodeDecodeError):
        replay(snapshot)
