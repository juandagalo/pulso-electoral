"""Tests for ACLED conflict and protest event data collection."""

from __future__ import annotations

import http
from unittest.mock import MagicMock, patch

import pytest
import requests

from collectors.acled import (
    _fetch_with_retry,
    _filter_by_keywords,
    _get_acled_token,
    _parse_event,
    _validate_acled_response,
    query_acled,
)

_ACLED_FIELD_COUNT = 21
_HTTP_OK = http.HTTPStatus.OK
_HTTP_ERROR_THRESHOLD = 400


@pytest.fixture
def sample_acled_event() -> dict:
    """A single raw ACLED API event dict with all 21 mapped fields."""
    return {
        "event_id_cnty": "COL12345",
        "event_date": "2026-03-15",
        "event_type": "Protests",
        "sub_event_type": "Peaceful protest",
        "disorder_type": "Demonstration",
        "actor1": "Protesters (Colombia)",
        "actor2": "",
        "assoc_actor_1": "Labor Group (Colombia)",
        "assoc_actor_2": "",
        "inter1": "6",
        "location": "Bogota",
        "latitude": "4.7110",
        "longitude": "-74.0721",
        "geo_precision": "1",
        "admin1": "Bogota",
        "admin2": "Bogota D.C.",
        "civilian_targeting": "",
        "fatalities": "0",
        "notes": "Thousands marched in Bogota against electoral reforms.",
        "source": "El Tiempo",
        "tags": "",
    }


@pytest.fixture
def parsed_acled_event() -> dict:
    """Expected output of _parse_event for sample_acled_event."""
    return {
        "event_id": "COL12345",
        "event_date": "2026-03-15",
        "event_type": "Protests",
        "sub_event_type": "Peaceful protest",
        "disorder_type": "Demonstration",
        "actor1": "Protesters (Colombia)",
        "actor2": "",
        "assoc_actor_1": "Labor Group (Colombia)",
        "assoc_actor_2": "",
        "inter1": 6,
        "location": "Bogota",
        "latitude": 4.7110,
        "longitude": -74.0721,
        "geo_precision": 1,
        "admin1": "Bogota",
        "admin2": "Bogota D.C.",
        "civilian_targeting": "",
        "fatalities": 0,
        "notes": "Thousands marched in Bogota against electoral reforms.",
        "source": "El Tiempo",
        "tags": "",
    }


def _make_response(status_code: int = 200, json_data: dict | None = None) -> MagicMock:
    """Create a mock requests.Response with the given status and JSON payload."""
    resp = MagicMock(spec=requests.Response)
    resp.status_code = status_code
    resp.headers = {}
    if json_data is not None:
        resp.json.return_value = json_data
    if status_code >= _HTTP_ERROR_THRESHOLD:
        resp.raise_for_status.side_effect = requests.HTTPError(response=resp)
    else:
        resp.raise_for_status.return_value = None
    return resp


# ---------------------------------------------------------------------------
# _get_acled_token
# ---------------------------------------------------------------------------


class TestGetAcledToken:
    """Tests for the _get_acled_token function."""

    @patch("collectors.acled._fetch_with_retry")
    @patch.dict("os.environ", {"ACLED_EMAIL": "user@test.com", "ACLED_PASSWORD": "s3cret"})
    def test_get_acled_token_success(self, mock_fetch: MagicMock) -> None:
        """Should return the access_token string on successful POST."""
        mock_fetch.return_value = _make_response(_HTTP_OK, {"access_token": "tok_abc123"})

        token = _get_acled_token()

        assert token == "tok_abc123"  # noqa: S105
        mock_fetch.assert_called_once()
        call_kwargs = mock_fetch.call_args
        assert call_kwargs.kwargs["method"] == "POST"

    @patch("collectors.acled._fetch_with_retry")
    @patch.dict("os.environ", {"ACLED_EMAIL": "user@test.com", "ACLED_PASSWORD": "bad"})
    def test_get_acled_token_failure(self, mock_fetch: MagicMock) -> None:
        """Should raise HTTPError when the token endpoint returns 401."""
        mock_fetch.side_effect = requests.HTTPError("401 Unauthorized")

        with pytest.raises(requests.HTTPError):
            _get_acled_token()


# ---------------------------------------------------------------------------
# _fetch_with_retry
# ---------------------------------------------------------------------------


class TestFetchWithRetry:
    """Tests for the _fetch_with_retry function."""

    @patch("collectors.acled.requests.get")
    def test_fetch_with_retry_success(self, mock_get: MagicMock) -> None:
        """Should return the response on a successful first attempt."""
        mock_get.return_value = _make_response(_HTTP_OK, {"data": []})

        resp = _fetch_with_retry(
            "https://acleddata.com/api/acled/read",
            headers={"Authorization": "Bearer tok"},
            params={"country": "Colombia"},
        )

        assert resp.status_code == _HTTP_OK
        mock_get.assert_called_once()

    @patch("collectors.acled.time.sleep")
    @patch("collectors.acled.requests.get")
    def test_fetch_with_retry_429_then_success(
        self, mock_get: MagicMock, mock_sleep: MagicMock
    ) -> None:
        """Should retry after 429, then succeed on the second attempt."""
        resp_429 = _make_response(429)
        resp_429.headers = {"Retry-After": "2"}
        resp_200 = _make_response(_HTTP_OK, {"data": []})
        mock_get.side_effect = [resp_429, resp_200]

        resp = _fetch_with_retry(
            "https://acleddata.com/api/acled/read",
            headers={},
            params={},
        )

        assert resp.status_code == _HTTP_OK
        assert mock_get.call_count == 2
        mock_sleep.assert_called_once_with(2)

    @patch("collectors.acled.time.sleep")
    @patch("collectors.acled.requests.get")
    def test_fetch_with_retry_exhausted(self, mock_get: MagicMock, mock_sleep: MagicMock) -> None:
        """Should raise HTTPError after all retry attempts are exhausted."""
        resp_500 = _make_response(500)
        mock_get.return_value = resp_500

        with pytest.raises(requests.HTTPError):
            _fetch_with_retry(
                "https://acleddata.com/api/acled/read",
                headers={},
                params={},
                max_attempts=3,
            )

        assert mock_get.call_count == 3

    @patch("collectors.acled.time.sleep")
    @patch("collectors.acled.requests.get")
    def test_fetch_with_retry_503_then_success(
        self, mock_get: MagicMock, mock_sleep: MagicMock
    ) -> None:
        """Should retry after 503 Service Unavailable, then succeed on the second attempt."""
        resp_503 = _make_response(503)
        resp_200 = _make_response(_HTTP_OK, {"data": []})
        mock_get.side_effect = [resp_503, resp_200]

        resp = _fetch_with_retry(
            "https://acleddata.com/api/acled/read",
            headers={},
            params={},
        )

        assert resp.status_code == _HTTP_OK
        assert mock_get.call_count == 2
        mock_sleep.assert_called_once_with(1)  # exponential backoff: 1 * 2**0 = 1


# ---------------------------------------------------------------------------
# _validate_acled_response
# ---------------------------------------------------------------------------


class TestValidateAcledResponse:
    """Tests for the _validate_acled_response function."""

    def test_validate_acled_response_success(self) -> None:
        """Should not raise when status is 200 or absent."""
        _validate_acled_response({"status": 200, "data": []})
        _validate_acled_response({"data": []})  # status key absent

    def test_validate_acled_response_error(self) -> None:
        """Should raise ValueError when the response indicates an error."""
        with pytest.raises(ValueError, match="ACLED API error"):
            _validate_acled_response({"status": 403, "error": "Invalid token"})


# ---------------------------------------------------------------------------
# _parse_event
# ---------------------------------------------------------------------------


class TestParseEvent:
    """Tests for the _parse_event function."""

    def test_parse_event(self, sample_acled_event: dict, parsed_acled_event: dict) -> None:
        """Should map all 21 fields correctly, including inter1 as int."""
        result = _parse_event(sample_acled_event)

        assert result == parsed_acled_event
        assert len(result) == _ACLED_FIELD_COUNT
        assert isinstance(result["inter1"], int)
        assert isinstance(result["geo_precision"], int)
        assert isinstance(result["fatalities"], int)
        assert isinstance(result["latitude"], float)
        assert isinstance(result["longitude"], float)


# ---------------------------------------------------------------------------
# _filter_by_keywords
# ---------------------------------------------------------------------------


class TestFilterByKeywords:
    """Tests for the _filter_by_keywords function."""

    def test_filter_by_keywords_match(self) -> None:
        """Should keep events whose notes contain a matching keyword."""
        events = [
            {"notes": "Protest in Bogota against electoral reform."},
            {"notes": "Armed clash in Cauca department."},
        ]
        result = _filter_by_keywords(events, ["electoral"])

        assert len(result) == 1
        assert "electoral" in result[0]["notes"]

    def test_filter_by_keywords_no_match(self) -> None:
        """Should filter out all events when no keywords match."""
        events = [
            {"notes": "Routine military patrol in Antioquia."},
            {"notes": "Agricultural dispute over land boundaries."},
        ]
        result = _filter_by_keywords(events, ["electoral", "protest"])

        assert result == []

    def test_filter_by_keywords_case_insensitive(self) -> None:
        """Should match keywords regardless of case."""
        events = [
            {"notes": "ELECTORAL violence reported in Cali."},
            {"notes": "Peaceful Protest in Medellin."},
        ]
        result = _filter_by_keywords(events, ["electoral", "protest"])

        assert len(result) == 2


# ---------------------------------------------------------------------------
# query_acled (integration with mocked HTTP)
# ---------------------------------------------------------------------------

_PAGE_SIZE = 5000


class TestQueryAcled:
    """Tests for the query_acled orchestrator function."""

    @patch("collectors.acled.time.sleep")
    @patch("collectors.acled._fetch_with_retry")
    @patch("collectors.acled._get_acled_token")
    def test_query_acled_pagination(
        self,
        mock_token: MagicMock,
        mock_fetch: MagicMock,
        mock_sleep: MagicMock,
        sample_acled_event: dict,
    ) -> None:
        """Should paginate through multiple pages and collect all events."""
        mock_token.return_value = "tok_abc"

        page2_count = 100
        page1_data = {"status": 200, "data": [sample_acled_event] * _PAGE_SIZE}
        page2_data = {"status": 200, "data": [sample_acled_event] * page2_count}

        resp_page1 = _make_response(_HTTP_OK, page1_data)
        resp_page2 = _make_response(_HTTP_OK, page2_data)
        mock_fetch.side_effect = [resp_page1, resp_page2]

        df = query_acled(country="Colombia", limit=_PAGE_SIZE)

        expected_total = _PAGE_SIZE + page2_count
        assert len(df) == expected_total
        assert mock_fetch.call_count == 2
        # Verify pagination sleep was called between pages
        mock_sleep.assert_called_once_with(1)

    @patch("collectors.acled.time.sleep")
    @patch("collectors.acled._fetch_with_retry")
    @patch("collectors.acled._get_acled_token")
    def test_query_acled_with_sub_event_types(
        self,
        mock_token: MagicMock,
        mock_fetch: MagicMock,
        mock_sleep: MagicMock,
        sample_acled_event: dict,
    ) -> None:
        """Should pass sub_event_type parameter to the API."""
        mock_token.return_value = "tok_abc"

        resp = _make_response(_HTTP_OK, {"status": 200, "data": [sample_acled_event]})
        mock_fetch.return_value = resp

        query_acled(
            country="Colombia",
            sub_event_types=["Peaceful protest", "Violent demonstration"],
        )

        call_args = mock_fetch.call_args
        params = call_args.kwargs.get("params", call_args[1].get("params", {}))
        assert params["sub_event_type"] == "Peaceful protest|Violent demonstration"

    @patch("collectors.acled.time.sleep")
    @patch("collectors.acled._fetch_with_retry")
    @patch("collectors.acled._get_acled_token")
    def test_query_acled_with_notes_keywords(
        self,
        mock_token: MagicMock,
        mock_fetch: MagicMock,
        mock_sleep: MagicMock,
    ) -> None:
        """Should post-filter events using notes_keywords."""
        mock_token.return_value = "tok_abc"

        events = [
            {
                "event_id_cnty": "COL001",
                "event_date": "2026-03-15",
                "event_type": "Protests",
                "sub_event_type": "Peaceful protest",
                "disorder_type": "Demonstration",
                "actor1": "Protesters",
                "actor2": "",
                "assoc_actor_1": "",
                "assoc_actor_2": "",
                "inter1": "6",
                "location": "Bogota",
                "latitude": "4.711",
                "longitude": "-74.072",
                "geo_precision": "1",
                "admin1": "Bogota",
                "admin2": "Bogota",
                "civilian_targeting": "",
                "fatalities": "0",
                "notes": "Electoral protest in the capital.",
                "source": "Local",
                "tags": "",
            },
            {
                "event_id_cnty": "COL002",
                "event_date": "2026-03-16",
                "event_type": "Violence against civilians",
                "sub_event_type": "Attack",
                "disorder_type": "Political violence",
                "actor1": "Unknown",
                "actor2": "",
                "assoc_actor_1": "",
                "assoc_actor_2": "",
                "inter1": "1",
                "location": "Cali",
                "latitude": "3.451",
                "longitude": "-76.532",
                "geo_precision": "1",
                "admin1": "Valle del Cauca",
                "admin2": "Cali",
                "civilian_targeting": "Civilian targeting",
                "fatalities": "1",
                "notes": "Armed group attacked village near Cali.",
                "source": "Local media",
                "tags": "",
            },
        ]

        resp = _make_response(_HTTP_OK, {"status": 200, "data": events})
        mock_fetch.return_value = resp

        df = query_acled(country="Colombia", notes_keywords=["electoral"])

        # Only the first event matches the keyword "electoral"
        assert len(df) == 1
        assert df.iloc[0]["event_id"] == "COL001"


# ---------------------------------------------------------------------------
# DB schema -- acled_events 21-column verification
# ---------------------------------------------------------------------------


class TestAcledEventsSchema:
    """Verify the acled_events table has all 21 expected columns."""

    def test_acled_events_has_21_columns(self, temp_db: MagicMock) -> None:
        """The acled_events table should have exactly 21 columns."""
        columns_df = temp_db.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'acled_events' ORDER BY ordinal_position"
        ).fetchdf()

        column_names = columns_df["column_name"].tolist()
        expected = [
            "event_id",
            "event_date",
            "event_type",
            "sub_event_type",
            "disorder_type",
            "actor1",
            "actor2",
            "assoc_actor_1",
            "assoc_actor_2",
            "inter1",
            "location",
            "latitude",
            "longitude",
            "geo_precision",
            "admin1",
            "admin2",
            "civilian_targeting",
            "fatalities",
            "notes",
            "source",
            "tags",
        ]

        assert column_names == expected
        assert len(column_names) == _ACLED_FIELD_COUNT
