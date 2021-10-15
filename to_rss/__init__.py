import os
from datetime import timedelta

from flask import g

from requests_cache import CachedSession

use_cache_dir = os.getenv("USE_CACHE_DIR", "").lower() == "true"


def get_session():
    session = getattr(g, "_session", None)
    if session is None:
        session = g._session = session = CachedSession(
            # If a cache path is given in the environment, use it.
            cache_name="to_rss_cache",
            backend="sqlite",
            use_cache_dir=use_cache_dir,
            serializer="pickle",
            # Expire after 15 minutes.
            expire_after=timedelta(minutes=15),
            # Return old content if a failure occurs.
            stale_if_error=True,
        )

    return session
