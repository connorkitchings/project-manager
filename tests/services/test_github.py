"""Tests for GitHubClient using mocked HTTP responses."""

import base64
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
import requests

from project_manager.core.settings import Settings
from project_manager.services.github import GitHubAPIError, GitHubClient


def make_response(status_code: int, json_body=None, text_body: str = ""):
    """Build a mock requests.Response."""
    mock_resp = MagicMock(spec=requests.Response)
    mock_resp.status_code = status_code
    mock_resp.text = text_body
    if json_body is not None:
        mock_resp.json.return_value = json_body
    if status_code >= 400:
        mock_resp.raise_for_status.side_effect = requests.HTTPError(response=mock_resp)
    else:
        mock_resp.raise_for_status.return_value = None
    return mock_resp


@pytest.fixture
def client():
    return GitHubClient(Settings())


@pytest.fixture
def authed_client():
    return GitHubClient(Settings(github_token="test-token"))


# ---------------------------------------------------------------------------
# Auth header
# ---------------------------------------------------------------------------


def test_github_client_sets_auth_header(authed_client):
    assert authed_client.session.headers.get("Authorization") == "Bearer test-token"


def test_github_client_no_auth_header_without_token(client):
    assert "Authorization" not in client.session.headers


# ---------------------------------------------------------------------------
# get_file_text()
# ---------------------------------------------------------------------------


def test_get_file_text_decodes_base64(client):
    content = base64.b64encode(b"Hello world").decode()
    mock_resp = make_response(200, {"type": "file", "content": content})
    with patch.object(client.session, "request", return_value=mock_resp):
        result = client.get_file_text("owner", "repo", "README.md", "main")
    assert result == "Hello world"


def test_get_file_text_returns_none_for_404(client):
    mock_resp = make_response(404)
    mock_resp.raise_for_status.side_effect = (
        None  # 404 is handled before raise_for_status
    )
    with patch.object(client.session, "request", return_value=mock_resp):
        result = client.get_file_text("owner", "repo", "missing.md", "main")
    assert result is None


def test_get_file_text_returns_none_for_directory_type(client):
    mock_resp = make_response(200, {"type": "dir", "content": None})
    with patch.object(client.session, "request", return_value=mock_resp):
        result = client.get_file_text("owner", "repo", "docs/", "main")
    assert result is None


def test_get_file_text_returns_none_for_empty_content(client):
    mock_resp = make_response(200, {"type": "file", "content": ""})
    with patch.object(client.session, "request", return_value=mock_resp):
        result = client.get_file_text("owner", "repo", "empty.md", "main")
    assert result is None


# ---------------------------------------------------------------------------
# _request() error handling
# ---------------------------------------------------------------------------


def test_request_raises_github_api_error_on_500(client):
    mock_resp = make_response(
        500, {"message": "Internal Server Error"}, "Internal Server Error"
    )
    with patch.object(client.session, "request", return_value=mock_resp):
        with pytest.raises(GitHubAPIError) as exc_info:
            client._request("GET", "/repos/owner/repo")
    assert exc_info.value.status_code == 500


def test_request_raises_rate_limit_error_on_403(client):
    mock_resp = make_response(
        403,
        {"message": "API rate limit exceeded for ..."},
        "API rate limit exceeded",
    )
    with patch.object(client.session, "request", return_value=mock_resp):
        with pytest.raises(GitHubAPIError) as exc_info:
            client._request("GET", "/repos/owner/repo")
    assert "rate limit" in str(exc_info.value).lower()
    assert exc_info.value.status_code == 403


def test_request_returns_none_on_404_with_allow_not_found(client):
    mock_resp = make_response(404)
    mock_resp.raise_for_status.side_effect = None
    with patch.object(client.session, "request", return_value=mock_resp):
        result = client._request(
            "GET", "/repos/owner/repo/contents/missing", allow_not_found=True
        )
    assert result is None


# ---------------------------------------------------------------------------
# list_directory()
# ---------------------------------------------------------------------------


def test_list_directory_returns_entries(client):
    entries = [{"type": "file", "name": "README.md", "path": "README.md"}]
    mock_resp = make_response(200, entries)
    with patch.object(client.session, "request", return_value=mock_resp):
        result = client.list_directory("owner", "repo", "", "main")
    assert result == entries


def test_list_directory_returns_empty_for_404(client):
    mock_resp = make_response(404)
    mock_resp.raise_for_status.side_effect = None
    with patch.object(client.session, "request", return_value=mock_resp):
        result = client.list_directory("owner", "repo", "nonexistent/", "main")
    assert result == []


def test_list_directory_returns_empty_for_non_list_payload(client):
    mock_resp = make_response(200, {"type": "file", "name": "file.md"})
    with patch.object(client.session, "request", return_value=mock_resp):
        result = client.list_directory("owner", "repo", "file.md", "main")
    assert result == []


# ---------------------------------------------------------------------------
# get_recent_activity()
# ---------------------------------------------------------------------------


def test_get_recent_activity_parses_all_event_types(client):
    now_str = "2026-04-22T10:00:00Z"
    commits = [
        {
            "commit": {
                "message": "Fix bug\nMore details",
                "committer": {"date": now_str},
            },
            "html_url": "https://example.com/c/1",
        }
    ]
    pulls = [
        {
            "title": "Add feature",
            "html_url": "https://example.com/p/1",
            "updated_at": now_str,
        }
    ]
    issues = [
        {
            "title": "Track stale repos",
            "html_url": "https://example.com/i/1",
            "updated_at": now_str,
        }
    ]

    responses = [
        make_response(200, commits),
        make_response(200, pulls),
        make_response(200, issues),
    ]
    with patch.object(client.session, "request", side_effect=responses):
        activity = client.get_recent_activity("owner", "repo")

    assert len(activity.commits) == 1
    assert activity.commits[0].title == "Fix bug"
    assert len(activity.pull_requests) == 1
    assert activity.pull_requests[0].title == "Add feature"
    assert len(activity.issues) == 1
    assert activity.issues[0].title == "Track stale repos"
    assert activity.last_activity_at is not None


def test_get_recent_activity_filters_pr_linked_issues(client):
    now_str = "2026-04-22T10:00:00Z"
    issues_with_pr = [
        {
            "title": "Issue with PR link",
            "html_url": "https://example.com/i/1",
            "updated_at": now_str,
            "pull_request": {"url": "https://api.github.com/repos/owner/repo/pulls/1"},
        },
        {
            "title": "Real issue",
            "html_url": "https://example.com/i/2",
            "updated_at": now_str,
        },
    ]

    responses = [
        make_response(200, []),
        make_response(200, []),
        make_response(200, issues_with_pr),
    ]
    with patch.object(client.session, "request", side_effect=responses):
        activity = client.get_recent_activity("owner", "repo")

    assert len(activity.issues) == 1
    assert activity.issues[0].title == "Real issue"


def test_get_recent_activity_last_activity_at_is_max_timestamp(client):
    older_str = "2026-01-01T00:00:00Z"
    newer_str = "2026-04-22T10:00:00Z"
    commits = [
        {
            "commit": {"message": "Old commit", "committer": {"date": older_str}},
            "html_url": None,
        }
    ]
    pulls = [{"title": "New PR", "html_url": None, "updated_at": newer_str}]

    responses = [
        make_response(200, commits),
        make_response(200, pulls),
        make_response(200, []),
    ]
    with patch.object(client.session, "request", side_effect=responses):
        activity = client.get_recent_activity("owner", "repo")

    expected = datetime(2026, 4, 22, 10, 0, 0, tzinfo=timezone.utc)
    assert activity.last_activity_at == expected
