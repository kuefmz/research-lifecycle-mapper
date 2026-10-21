"""Deterministic, lossless source decoding; raw snapshot bytes are never rewritten."""

POLICY = "utf8-then-windows1252-v1"


def decode_text(data: bytes) -> tuple[str, str]:
    """Try strict UTF-8, then a recorded CP1252 interpretation of legacy text.

    CP1252 is a fallback hypothesis, not universal encoding detection. Undefined
    CP1252 bytes and binary/control characters are rejected, never replaced.
    """
    if b"\x00" in data:
        raise ValueError("Binary content")
    try:
        text = data.decode("utf-8")
        encoding = "utf-8"
    except UnicodeDecodeError:
        text = data.decode("cp1252")
        encoding = "windows-1252"
        if any(
            ord(char) < 32 and char not in "\t\r\n\f" or 127 <= ord(char) <= 159 for char in text
        ):
            raise ValueError("Binary control characters in legacy text")
    codec = "cp1252" if encoding == "windows-1252" else "utf-8"
    if text.encode(codec) != data:
        raise ValueError("Non-lossless decoding")
    return text, encoding
