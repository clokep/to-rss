import os
from datetime import timedelta

import requests
from requests_cache import CachedSession

USE_CACHE_DIR = os.getenv("USE_CACHE_DIR", "").lower() == "true"
DISABLE_CACHED_SESSION = os.getenv("DISABLE_CACHED_SESSION", "").lower() == "true"

# Built on first use, then reused. See get_session().
_session: requests.Session | None = None
_session_pid: int | None = None


def get_session() -> requests.Session:
    """
    Get the cached session, building it on first use in each process.

    The session is generated per process -- WSGI servers prefork.

    Workers in the same process share the session, which requests does not
    document as thread safe.
    """
    global _session, _session_pid

    if DISABLE_CACHED_SESSION:
        return requests.Session()

    pid = os.getpid()
    if _session is None or _session_pid != pid:
        _session = CachedSession(
            cache_name="to_rss_requests",
            backend="sqlite",
            use_cache_dir=USE_CACHE_DIR,
            serializer="pickle",
            # Let readers run during a write, and wait rather than fail when another
            # worker holds the write lock.
            wal=True,
            busy_timeout=5000,
            # Expire after 15 minutes.
            expire_after=timedelta(minutes=15),
            allowable_methods=("GET", "HEAD", "POST"),
            # Return old content if a failure occurs.
            stale_if_error=True,
        )

        # Nothing else expires rows on disk, so they pile up. Sessions are built once
        # per process, so this is the only moment cheap enough to sweep.
        _session.cache.delete(expired=True)

        _session_pid = pid

    return _session
