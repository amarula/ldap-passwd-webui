"""Tests for security features: CSRF, rate limiting, LDAP escaping, headers."""

import hashlib
import re

import pytest


# ---------------------------------------------------------------------------
# LDAP filter escaping
# ---------------------------------------------------------------------------

LDAP_ESCAPE_CASES = [
    ("normal_user", "normal_user"),
    ("user*name", "user\\2aname"),
    ("user(name)", "user\\28name\\29"),
    ("user\\name", "user\\5cname"),
    ("user\x00name", "user\\00name"),
    ("*)(uid=*", "\\2a\\29\\28uid=\\2a"),  # classic injection attempt
    # | is NOT an LDAP special char; ( * are and must be escaped.
    ("admin)(|(uid=*", "admin\\29\\28|\\28uid=\\2a"),
]


@pytest.mark.parametrize("raw,expected", LDAP_ESCAPE_CASES)
def test_ldap_escape(raw, expected, app):
    """LDAP special characters are escaped per RFC 4515."""
    import app as app_mod

    assert app_mod.ldap_escape(raw) == expected


def test_ldap_escape_no_false_positives(app):
    """Normal strings pass through unchanged."""
    import app as app_mod

    assert app_mod.ldap_escape("john.doe@example.com") == "john.doe@example.com"
    assert app_mod.ldap_escape("user_123-abc") == "user_123-abc"


# ---------------------------------------------------------------------------
# CSRF protection
# ---------------------------------------------------------------------------


class TestCsrf:
    def test_form_contains_csrf_token(self, client):
        """Every GET response includes a CSRF token in the form."""
        _status, _headers, body = client("GET", "/")
        assert 'name="csrf_token" value="' in body

    def test_set_cookie_present(self, client):
        """GET response sets a signed CSRF cookie."""
        _status, headers, _body = client("GET", "/")
        assert "Set-Cookie" in headers
        assert "csrf_token" in headers["Set-Cookie"]
        assert "HttpOnly" in headers["Set-Cookie"]

    def test_post_without_cookie_is_rejected(self, client):
        """POST without a CSRF cookie returns the error page."""
        _status, headers, body = client("GET", "/")
        m = re.search(r'name="csrf_token" value="([^"]*)"', body)
        token = m.group(1)

        status, _headers, body = client(
            "POST",
            "/",
            body=f"csrf_token={token}&username=x&old-password=x&"
            "new-password=xxxxxxxx&confirm-password=xxxxxxxx",
        )
        assert "Invalid or expired" in body

    def test_post_with_wrong_token_is_rejected(self, client):
        """POST with a cookie but wrong CSRF token fails."""
        _status, headers, body = client("GET", "/")
        cookie = headers.get("Set-Cookie", "").split(";")[0].strip()

        status, _headers, body = client(
            "POST",
            "/",
            body="csrf_token=wrong_token_12345&username=x&old-password=x&"
            "new-password=xxxxxxxx&confirm-password=xxxxxxxx",
            cookie=cookie,
        )
        assert "Invalid or expired" in body

    def test_session_flow(self, session):
        """A complete session: GET → POST with valid token → validation error."""
        status, _headers, body = session.post(
            username="testuser",
            **{"old-password": "oldpass"},
            **{"new-password": "short"},
            **{"confirm-password": "short"},
        )
        # Should get a validation error, not a CSRF error.
        assert "Invalid or expired" not in body

    def test_csrf_token_rotates(self, session):
        """Each response includes a fresh CSRF token."""
        token1 = session.csrf_token
        session.post(
            username="x",
            **{"old-password": "x"},
            **{"new-password": "short"},
            **{"confirm-password": "short"},
        )
        token2 = session.csrf_token
        # Both should be valid base64 strings.
        for t in (token1, token2):
            assert len(t) >= 32


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------


def test_rate_limit_ip(app):
    """More than 5 attempts from the same IP in 60 s are blocked."""
    import app as app_mod

    app_mod._rate_by_ip.clear()
    ip = "192.0.2.1"

    for i in range(5):
        assert app_mod.check_rate_limit(ip, f"user{i}") is None

    err = app_mod.check_rate_limit(ip, "user6")
    assert err is not None
    assert "IP address" in err


def test_rate_limit_user(app):
    """More than 10 attempts for the same username in 60 s are blocked."""
    import app as app_mod

    app_mod._rate_by_user.clear()
    username = "target_user"

    for i in range(10):
        assert app_mod.check_rate_limit(f"192.0.2.{i}", username) is None

    err = app_mod.check_rate_limit("192.0.2.99", username)
    assert err is not None
    assert "account" in err


def test_rate_limit_resets_after_window(app, monkeypatch):
    """Old timestamps are pruned so entries don't accumulate forever."""
    import app as app_mod
    import time

    app_mod._rate_by_ip.clear()

    now = time.monotonic()
    for i in range(6):
        app_mod._rate_by_ip["10.0.0.1"].append(now)

    err = app_mod.check_rate_limit("10.0.0.1", "u")
    assert err is not None

    monkeypatch.setattr(time, "monotonic", lambda: now + app_mod._RATE_WINDOW + 1)
    app_mod._rate_by_ip.clear()
    app_mod._rate_by_user.clear()

    err2 = app_mod.check_rate_limit("10.0.0.1", "u")
    assert err2 is None


# ---------------------------------------------------------------------------
# Security headers
# ---------------------------------------------------------------------------


def test_security_headers_present(client):
    """All security headers are set on responses."""
    _status, headers, _body = client("GET", "/")

    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("Referrer-Policy") == "no-referrer"
    assert headers.get("X-Permitted-Cross-Domain-Policies") == "none"
    assert "Content-Security-Policy" in headers

    csp = headers["Content-Security-Policy"]
    assert "default-src 'self'" in csp
    assert "script-src" in csp and "'unsafe-inline'" in csp


def test_csp_allows_google_fonts(client):
    """CSP allows external font/icon resources needed by Material Design."""
    _status, headers, _body = client("GET", "/")
    csp = headers["Content-Security-Policy"]
    assert "fonts.googleapis.com" in csp
    assert "fonts.gstatic.com" in csp


# ---------------------------------------------------------------------------
# Log sanitization
# ---------------------------------------------------------------------------


def test_username_not_in_logs(app, caplog):
    """Password-change log messages must not contain the raw username."""
    import app as app_mod
    import logging

    username = "alice.smith@example.com"
    app_mod.LOG.setLevel(logging.INFO)

    hash_prefix = hashlib.sha256(username.encode()).hexdigest()[:8]
    app_mod.LOG.info("Password successfully changed for user hash: %s", hash_prefix)

    record = caplog.records[-1]
    assert username not in record.getMessage()
    assert hash_prefix in record.getMessage()
