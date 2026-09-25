import sys
from typing import Any

import pytest
from sentry_sdk.types import Event, Hint

from to_rss.sentry import ignore_client_disconnects


def exc_info(exc: BaseException) -> Any:
    """Build the same 3-tuple Sentry puts in the hint for a logged exception."""
    try:
        raise exc
    except BaseException:
        return sys.exc_info()


def exception_event(exc: BaseException) -> Event:
    return {"exception": {"values": [{"type": type(exc).__name__, "value": str(exc)}]}}


def log_event(message: str) -> Event:
    """Build a log event shaped like the one Sentry builds from a LogRecord."""
    return {"level": "error", "logentry": {"message": message, "formatted": message}}


def test_drops_write_error_exception() -> None:
    event = exception_event(OSError("write error"))
    hint: Hint = {"exc_info": exc_info(OSError("write error"))}

    assert ignore_client_disconnects(event, hint) is None


def test_drops_write_error_log_message() -> None:
    assert ignore_client_disconnects(log_event("OSError: write error"), {}) is None


def test_drops_write_error_with_a_timestamp_prefix() -> None:
    event = log_event("2026-09-25 12:00:00,123: OSError: write error")

    assert ignore_client_disconnects(event, {}) is None


def test_keeps_other_oserrors() -> None:
    err = OSError(28, "No space left on device")
    event = exception_event(err)
    hint: Hint = {"exc_info": exc_info(err)}

    assert ignore_client_disconnects(event, hint) == event


def test_keeps_other_exceptions() -> None:
    err = ValueError("write error")
    event = exception_event(err)
    hint: Hint = {"exc_info": exc_info(err)}

    assert ignore_client_disconnects(event, hint) == event


def test_keeps_unrelated_log_messages() -> None:
    event = log_event("Created empty feed for Wikipedia current events")

    assert ignore_client_disconnects(event, {}) == event


@pytest.mark.parametrize(
    "hint",
    [{}, {"exc_info": (None, None, None)}],
    ids=["no_exc_info", "empty_exc_info"],
)
def test_keeps_events_without_an_exception(hint: Hint) -> None:
    event: Event = {"level": "error"}

    assert ignore_client_disconnects(event, hint) == event
