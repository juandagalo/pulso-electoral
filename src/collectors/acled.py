"""ACLED conflict and protest event data collection."""

from __future__ import annotations

import logging
import os
import time

import pandas as pd
import requests

logger = logging.getLogger(__name__)

_RETRYABLE_STATUS_CODES = {429, 500, 503}
_HTTP_TOO_MANY_REQUESTS = 429


def _fetch_with_retry(
    url: str,
    headers: dict[str, str],
    params: dict[str, str | int],
    max_attempts: int = 3,
    method: str = "GET",
) -> requests.Response:
    """HTTP fetch with exponential backoff on transient failures.

    Parameters
    ----------
    url : str
        Request URL.
    headers : dict[str, str]
        HTTP headers.
    params : dict[str, str | int]
        Query parameters (GET) or form data (POST).
    max_attempts : int
        Maximum number of attempts before raising.
    method : str
        HTTP method, either "GET" or "POST".

    Returns
    -------
    requests.Response
        Successful HTTP response.

    Raises
    ------
    requests.HTTPError
        If all retry attempts are exhausted.
    """
    for attempt in range(max_attempts):
        if method == "POST":
            resp = requests.post(url, data=params, headers=headers, timeout=30)
        else:
            resp = requests.get(url, params=params, headers=headers, timeout=30)

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

    Parameters
    ----------
    data : dict
        Parsed JSON response from the ACLED API.

    Raises
    ------
    ValueError
        If the response contains an error status.
    """
    status = data.get("status")
    if status is not None and status not in (0, 200):
        msg = f"ACLED API error (status={status}): {data.get('error', data)}"
        raise ValueError(msg)


def _get_acled_token() -> str:
    """Obtain OAuth 2.0 access token from ACLED API.

    Reads ACLED_EMAIL and ACLED_PASSWORD from environment variables.
    Posts to the ACLED token endpoint to obtain a 24-hour bearer token.

    Returns
    -------
    str
        OAuth 2.0 access token.

    Raises
    ------
    ValueError
        If credentials are not set in environment.
    requests.HTTPError
        If token request fails.
    """
    email = os.getenv("ACLED_EMAIL")
    password = os.getenv("ACLED_PASSWORD")

    if not email or not password:
        msg = "ACLED_EMAIL and ACLED_PASSWORD must be set in .env"
        raise ValueError(msg)

    token_url = "https://acleddata.com/oauth/token"  # noqa: S105
    response = _fetch_with_retry(
        token_url,
        headers={},
        params={
            "username": email,
            "password": password,
            "grant_type": "password",
            "client_id": "acled",
        },
        method="POST",
    )
    token: str = response.json()["access_token"]
    return token


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
        "inter1": int(event.get("inter1", 0)),
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
    return [ev for ev in events if any(kw in ev.get("notes", "").lower() for kw in lowered)]


def query_acled(  # noqa: PLR0913
    country: str = "Colombia",
    event_types: list[str] | None = None,
    sub_event_types: list[str] | None = None,
    date_range: tuple[str, str] | None = None,
    notes_keywords: list[str] | None = None,
    limit: int = 5000,
) -> pd.DataFrame:
    """Query ACLED API for conflict and protest events.

    Uses OAuth 2.0 authentication and paginates automatically.

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

    base_url = "https://acleddata.com/api/acled/read"
    headers = {"Authorization": f"Bearer {access_token}"}

    params: dict[str, str | int] = {
        "country": country,
        "limit": limit,
        "inter_num": 1,
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
        response = _fetch_with_retry(base_url, headers=headers, params=params)
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
