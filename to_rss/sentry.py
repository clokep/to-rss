"""
Sentry event filtering.

"""

from sentry_sdk.types import Event, Hint

# uWSGI raises OSError with this message when the client disconnects before the
# response has been written. PythonAnywhere does not allow its uWSGI config to be
# changed, so the event is dropped here instead.
CLIENT_DISCONNECT = "write error"


def ignore_client_disconnects(event: Event, hint: Hint) -> Event | None:
    """
    Return None to drop a client disconnect, or the event unchanged.

    Sentry receives these either as an exception, when the log record carries
    exc_info, or as a bare log message when it does not. Which one happens
    depends on the uWSGI config, which is not visible from here, so both are
    handled. Every other event is kept, including other OSErrors, so a full disk
    or a permissions problem still reaches Sentry.
    """
    exc_info = hint.get("exc_info")
    if exc_info is not None and exc_info[0] is not None:
        if isinstance(exc_info[1], OSError) and str(exc_info[1]) == CLIENT_DISCONNECT:
            return None
        return event

    message = (event.get("logentry") or {}).get("formatted", "")
    if isinstance(message, str) and message.strip().endswith(
        f"OSError: {CLIENT_DISCONNECT}"
    ):
        return None

    return event
