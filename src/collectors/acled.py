"""ACLED conflict and protest event data collection.

Uses OAuth 2.0 password-grant authentication against the official
ACLED API at ``https://acleddata.com/api/``.

References
----------
- API docs : https://acleddata.com/api-documentation/getting-started
- Token URL: https://acleddata.com/oauth/token
- Data URL : https://acleddata.com/api/acled/read
"""

from __future__ import annotations

import logging
import os
import time

import pandas as pd
import requests

logger = logging.getLogger(__name__)

_RETRYABLE_STATUS_CODES = {429, 500, 503}
_HTTP_TOO_MANY_REQUESTS = 429
_HTTP_FORBIDDEN = 403

_TOKEN_URL = "https://acleddata.com/oauth/token"  # noqa: S105
_DATA_URL = "https://acleddata.com/api/acled/read"


def _get_acled_token() -> str:
    """Obtain an OAuth 2.0 access token from the ACLED token endpoint.

    Reads ``ACLED_EMAIL`` and ``ACLED_PASSWORD`` from environment variables
    and performs a password-grant token request.

    Returns
    -------
    str
        Bearer access token.

    Raises
    ------
    ValueError
        If credentials are not set in the environment.
    requests.HTTPError
        If the token endpoint returns an HTTP error.
    """
    email = os.getenv("ACLED_EMAIL")
    password = os.getenv("ACLED_PASSWORD")

    if not email or not password:
        msg = "ACLED_EMAIL and ACLED_PASSWORD must be set in .env"
        raise ValueError(msg)

    resp = _fetch_with_retry(
        _TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "username": email,
            "password": password,
            "grant_type": "password",
            "client_id": "acled",
        },
        method="POST",
    )

    return str(resp.json()["access_token"])


def _fetch_with_retry(  # noqa: PLR0913
    url: str,
    *,
    headers: dict[str, str] | None = None,
    params: dict[str, str | int] | None = None,
    data: dict[str, str] | None = None,
    method: str = "GET",
    max_attempts: int = 3,
) -> requests.Response:
    """HTTP request with exponential backoff on transient failures.

    Parameters
    ----------
    url : str
        Request URL.
    headers : dict[str, str] | None
        HTTP headers.
    params : dict[str, str | int] | None
        Query-string parameters (used for GET requests).
    data : dict[str, str] | None
        Form-encoded body (used for POST requests).
    method : str
        HTTP method — ``"GET"`` (default) or ``"POST"``.
    max_attempts : int
        Maximum number of attempts before raising.

    Returns
    -------
    requests.Response
        Successful HTTP response.

    Raises
    ------
    requests.HTTPError
        If all retry attempts are exhausted or a non-retryable error occurs.
    """
    for attempt in range(max_attempts):
        if method.upper() == "POST":
            resp = requests.post(url, headers=headers, data=data, timeout=30)
        else:
            resp = requests.get(url, headers=headers, params=params, timeout=30)

        if resp.status_code == _HTTP_FORBIDDEN:
            msg = (
                "ACLED API returned 403 Forbidden. Your myACLED account may need "
                "Research tier access. Accounts with personal emails (gmail, etc.) "
                "are limited to Open tier which does NOT include API access. "
                "Re-register with an institutional email or contact "
                "sales@acleddata.com"
            )
            logger.error(msg)
            resp.raise_for_status()

        if resp.status_code not in _RETRYABLE_STATUS_CODES:
            resp.raise_for_status()
            return resp

        if attempt < max_attempts - 1:
            if resp.status_code == _HTTP_TOO_MANY_REQUESTS:
                wait = int(resp.headers.get("Retry-After", 1 * 2**attempt))
            else:
                wait = 1 * 2**attempt
            logger.warning(
                "ACLED API %s (attempt %d/%d), retrying in %ds",
                resp.status_code,
                attempt + 1,
                max_attempts,
                wait,
            )
            time.sleep(wait)

    resp.raise_for_status()
    return resp  # pragma: no cover — raise_for_status always raises here


def _validate_acled_response(data: dict) -> None:
    """Check ACLED JSON response for error indicators.

    ACLED may return HTTP 200 even on logical errors.  The JSON body
    contains ``"success": true/false`` and a numeric ``"status"`` field
    that should be checked separately.

    Parameters
    ----------
    data : dict
        Parsed JSON response from the ACLED API.

    Raises
    ------
    ValueError
        If the response indicates a logical error.
    """
    if data.get("success") is False:
        msg = f"ACLED API error: {data.get('error', data)}"
        raise ValueError(msg)

    status = data.get("status")
    if status is not None and status not in (0, 200):
        msg = f"ACLED API error (status={status}): {data.get('error', data)}"
        raise ValueError(msg)


def _parse_event(event: dict) -> dict:
    """Map a raw ACLED event dict to the internal column schema.

    Parameters
    ----------
    event : dict
        Single event from the ACLED API ``data`` array.

    Returns
    -------
    dict
        Normalised event dictionary.
    """
    return {
        "event_id": event.get("event_id_cnty", ""),
        "event_date": event.get("event_date", ""),
        "event_type": event.get("event_type", ""),
        "sub_event_type": event.get("sub_event_type", ""),
        "disorder_type": event.get("disorder_type", ""),
        "actor1": event.get("actor1", ""),
        "actor2": event.get("actor2", ""),
        "assoc_actor_1": event.get("assoc_actor_1", ""),
        "assoc_actor_2": event.get("assoc_actor_2", ""),
        "inter1": str(event.get("inter1", "")),
        "location": event.get("location", ""),
        "latitude": float(event.get("latitude", 0)),
        "longitude": float(event.get("longitude", 0)),
        "geo_precision": int(event.get("geo_precision", 0)),
        "admin1": event.get("admin1", ""),
        "admin2": event.get("admin2", ""),
        "civilian_targeting": event.get("civilian_targeting", ""),
        "fatalities": int(event.get("fatalities", 0)),
        "notes": event.get("notes", ""),
        "source": event.get("source", ""),
        "tags": event.get("tags", ""),
    }


def _filter_by_keywords(events: list[dict], keywords: list[str]) -> list[dict]:
    """Post-filter events whose notes field contains any keyword (case-insensitive).

    Parameters
    ----------
    events : list[dict]
        Parsed event dictionaries.
    keywords : list[str]
        Keywords to match against the ``notes`` field.

    Returns
    -------
    list[dict]
        Filtered subset of events.
    """
    lowered = [kw.lower() for kw in keywords]
    return [
        ev for ev in events if any(kw in ev.get("notes", "").lower() for kw in lowered)
    ]


def query_acled(  # noqa: PLR0913
    country: str = "Colombia",
    event_types: list[str] | None = None,
    sub_event_types: list[str] | None = None,
    date_range: tuple[str, str] | None = None,
    notes_keywords: list[str] | None = None,
    limit: int = 5000,
) -> pd.DataFrame:
    """Query ACLED API for conflict and protest events.

    Uses OAuth 2.0 password-grant authentication and paginates
    automatically through all result pages.

    Parameters
    ----------
    country : str
        Country name to filter events.
    event_types : list[str] | None
        Event types to filter (e.g., ["Protests", "Riots"]).
    sub_event_types : list[str] | None
        Sub-event types to filter (pipe-separated in API query).
    date_range : tuple[str, str] | None
        Start and end dates as (YYYY-MM-DD, YYYY-MM-DD).
    notes_keywords : list[str] | None
        If provided, post-filter events where notes contain any keyword
        (case-insensitive, in-memory filtering).
    limit : int
        Maximum rows per API page (ACLED default is 5000).

    Returns
    -------
    pd.DataFrame
        DataFrame with ACLED event data.
    """
    access_token = _get_acled_token()

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    params: dict[str, str | int] = {
        "country": country,
        "limit": limit,
        "_format": "json",
    }

    if event_types:
        params["event_type"] = "|".join(event_types)

    if sub_event_types:
        params["sub_event_type"] = "|".join(sub_event_types)

    if date_range:
        params["event_date"] = f"{date_range[0]}|{date_range[1]}"
        params["event_date_where"] = "BETWEEN"

    all_events: list[dict] = []
    page = 1

    while True:
        params["page"] = page
        response = _fetch_with_retry(_DATA_URL, headers=headers, params=params)
        data = response.json()

        _validate_acled_response(data)

        batch = data.get("data", [])
        if not batch:
            break

        for event in batch:
            all_events.append(_parse_event(event))

        if len(batch) < limit:
            break

        page += 1
        time.sleep(1)  # respectful rate limiting between pages

    if notes_keywords:
        all_events = _filter_by_keywords(all_events, notes_keywords)

    return pd.DataFrame(all_events)
