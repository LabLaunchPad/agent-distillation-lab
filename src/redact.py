"""Stdlib-only redaction stub. Shot 2 calls redact() at capture time."""
import re

_PATTERNS = [
    (re.compile(r"sk-[A-Za-z0-9-_]{8,}"), "[REDACTED_API_KEY]"),
    (re.compile(r"(?i)bearer\s+[A-Za-z0-9\-._~+/]+=*"), "Bearer [REDACTED]"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "[REDACTED_PRIVATE_KEY]"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "[REDACTED_EMAIL]"),
]

def redact(text: str) -> str:
    # ponytail: naive regex sweep; upgrade to per-field scrubbers if FP rate matters.
    for rx, repl in _PATTERNS:
        text = rx.sub(repl, text)
    return text

if __name__ == "__main__":
    assert "[REDACTED_API_KEY]" in redact("key sk-abc123XYZ q")
    assert "[REDACTED_EMAIL]" in redact("a@b.com")
    print("redact ok")
