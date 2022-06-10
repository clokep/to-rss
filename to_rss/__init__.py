import functools
import logging
import os
import re
from datetime import timedelta

from flask import g, request

import requests

from requests_cache import CachedSession

logger = logging.getLogger(__name__)

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


# Whether to report analytics.
REPORT_ANALYTICS = os.getenv("REPORT_ANALYTICS", "").lower() == "true"
API_ENDPOINT = "https://plausible.io/api/event"

# Regular expression used to parse the number of subscribers from a feed reader's
# User-Agent.
SUBSCRIBERS_REGEX = re.compile(r"(\d+) subscribers")


def _send_analytics():
    """
    Fetch the User-Agent, IP address, URL, and referrer for the current request.

    Submits them to the Plausible API for analytics.
    See https://plausible.io/docs/events-api

    Note that this doesn't get registered as a signal since it should only run on
    API pages.
    """
    if not REPORT_ANALYTICS:
        return

    user_agent = request.headers.get("User-Agent", "")

    # RSS readers usually include the number of subscribers, pull that out, then
    # sanitize the User-Agent.
    match = SUBSCRIBERS_REGEX.search(user_agent)
    subscribers = None
    if match:
        subscribers = int(match.group(1))
        user_agent = SUBSCRIBERS_REGEX.sub("N subscribers", user_agent)

    # Unpack the IP address from the reverse proxy, if one is being used.
    client_ip_address = request.headers.get("X-Real-IP") or request.remote_addr

    # Outgoing API data.
    headers = {
        "User-Agent": user_agent,
        "X-Forwarded-For": client_ip_address,
        "Content-Type": "application/json",
    }
    body = {
        "name": "pageview",
        "url": request.base_url,
        "domain": "to-rss.xyz",
    }

    # See https://plausible.io/docs/custom-event-goals#using-custom-props
    if subscribers is not None:
        body["props"] = {"subscribers": subscribers}

    # Send the API request.
    try:
        requests.post(API_ENDPOINT, headers=headers, json=body)
    except requests.RequestException:
        logger.warning("Unable to connect to plausible.io")


def report_page(f):
    """
    A decorator to mark a page as capturing page visits for analytics.

    Should be placed outside any caching.
    """

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        _send_analytics()
        return f(*args, **kwargs)

    return wrapper
