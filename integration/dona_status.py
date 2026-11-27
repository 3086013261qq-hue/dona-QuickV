"""Numeric, request-bound additions to the existing authenticated failure snapshot.

No I/O, logs, credentials, model paths or generated text. Hooks are observational.
"""
import math

MAX_COUNT = 1_000_000_000


def _entry():
    import failure_status
    binding = failure_status.current()
    return binding.entry if binding else None


def _integer(value):
    return type(value) is int and 0 <= value <= MAX_COUNT


def reset():
    entry = _entry()
    if entry and entry.phase not in {"finished", "failed", "cancelled"}:
        entry.dona.pop("usage", None)
        entry.dona.pop("transferSeconds", None)
        entry.dona["streaming"] = False


def limit(value, *, retries=True, attempt=None):
    entry = _entry()
    if entry and _integer(value) and value <= 100:
        entry.dona["maxAttempts"] = value + 1 if retries else value
        if retries and _integer(attempt):
            entry.dona["retryCount"] = attempt
            entry.dona["retryMax"] = value
        elif not retries:
            entry.dona.pop("retryCount", None)
            entry.dona.pop("retryMax", None)


def progress():
    entry = _entry()
    if entry and entry.phase == "running":
        entry.dona["streaming"] = True


def usage(metadata, *, studio=False):
    """Copy only known raw provider counts. Never use text-length estimates."""
    entry = _entry()
    if not entry or metadata is None or entry.phase in {"finished", "failed", "cancelled"}:
        return
    names = ("promptTokenCount", "thoughtsTokenCount", "candidatesTokenCount", "totalTokenCount") if studio else (
        "prompt_token_count", "thoughts_token_count", "candidates_token_count", "total_token_count")
    counts = entry.dona.setdefault("usage", {})
    for name, key in zip(names, ("inputTokens", "thinkingTokens", "outputTokens", "totalTokens")):
        value = metadata.get(name) if isinstance(metadata, dict) else getattr(metadata, name, None)
        if _integer(value):
            counts[key] = max(counts.get(key, 0), value)


def success(ttft, gen_time):
    entry = _entry()
    # Successful-attempt generation/transfer duration, matching upstream gen_time;
    # excludes first-token wait, failed attempts and retry waits.
    if entry and entry.phase not in {"finished", "failed", "cancelled"}:
        if type(gen_time) in (int, float) and math.isfinite(gen_time) and 0 <= gen_time <= 86400:
            entry.dona["transferSeconds"] = round(gen_time, 3)


def snapshot(entry):
    data = {"version": 1, "attempt": min(MAX_COUNT, max(0, entry.attempt)),
            "streaming": entry.dona.get("streaming") is True}
    if "maxAttempts" in entry.dona:
        data["maxAttempts"] = entry.dona["maxAttempts"]
    for key in ("retryCount", "retryMax"):
        if key in entry.dona:
            data[key] = entry.dona[key]
    if entry.phase == "finished":
        data.update(entry.dona.get("usage", {}))
        if "thinkingTokens" in data and "outputTokens" in data:
            combined = data["thinkingTokens"] + data["outputTokens"]
            if _integer(combined):
                data["thinkingAndOutputTokens"] = combined
        if "transferSeconds" in entry.dona:
            data["transferSeconds"] = entry.dona["transferSeconds"]
    return {"dona": data}
