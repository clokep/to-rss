import os
from datetime import timedelta

from flask import g

from requests_cache import CachedSession

USE_CACHE_DIR = os.getenv("USE_CACHE_DIR", "").lower() == "true"


def get_session():
    """Get a CachedSession object (which is not shared across threads/subprocesses)."""
    session = getattr(g, "_session", None)
    if session is None:
        session = g._session = CachedSession(
            # If a cache path is given in the environment, use it.
            cache_name="to_rss_requests",
            backend="sqlite",
            use_cache_dir=USE_CACHE_DIR,
            serializer="pickle",
            # Expire after 15 minutes.
            expire_after=timedelta(minutes=15),
            allowable_methods=("GET", "HEAD", "POST"),
            # Return old content if a failure occurs.
            stale_if_error=True,
        )

    return session
