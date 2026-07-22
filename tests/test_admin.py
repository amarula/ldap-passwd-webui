"""Tests for admin login, session, and routes."""

import json
import re

import pytest


class TestAdminLogin:

    def test_login_page_renders(self, client):
        """GET /login returns the login form."""
        _s, _h, body = client("GET", "/login")
        assert "login-form" in body
        assert 'name="password"' in body

    def test_login_rejects_empty_credentials(self, client):
        """POST /login with no credentials returns an error."""
        _s, headers, body = client("GET", "/login")
        csrf = re.search(r'name="csrf_token" value="([^"]*)"', body).group(1)
        cookie = headers.get("Set-Cookie", "").split(";")[0].strip()

        _s2, _h2, body2 = client(
            "POST",
            "/login",
            body=f"csrf_token={csrf}&username=&password=",
            cookie=cookie,
        )
        assert "required" in body2.lower()


class TestAdminSession:

    def test_admin_redirects_when_no_session(self, client):
        """GET /admin returns 303 redirect when no session."""
        status, _h, _body = client("GET", "/admin")
        assert status.startswith("303")

    def test_logout_redirects(self, client):
        """GET /logout redirects to /."""
        status, _h, _body = client("GET", "/logout")
        assert status.startswith("303")

    def test_admin_routes_reject_without_session(self, client):
        """All admin POST routes require a valid session."""
        routes = [
            "/admin/change-password",
            "/admin/create-user",
            "/admin/create-group",
            "/admin/modify-group",
        ]
        for route in routes:
            _s, _h, body = client("GET", "/login")
            csrf = re.search(r'name="csrf_token" value="([^"]*)"', body).group(1)
            cookie = _h.get("Set-Cookie", "").split(";")[0].strip()

            status, _h2, body2 = client(
                "POST",
                route,
                body=f"csrf_token={csrf}&x=y",
                cookie=cookie,
            )
            assert status.startswith("303"), f"{route} should redirect"


class TestAdminPages:

    def test_login_form_structure(self, client):
        """Login page has username + password fields and a submit button."""
        _s, _h, body = client("GET", "/login")
        assert 'name="username"' in body
        assert 'name="password"' in body
        assert 'type="submit"' in body

    def test_login_has_csrf(self, client):
        """Login page includes a CSRF token."""
        _s, _h, body = client("GET", "/login")
        assert 'name="csrf_token" value="' in body

    def test_index_no_admin_link_without_session(self, client):
        """The main index does NOT show an admin link for anonymous users."""
        _s, _h, body = client("GET", "/")
        assert "admin_panel_settings" not in body


class TestSessionCookie:

    def test_set_session_creates_cookie(self, app):
        """_set_session writes a signed cookie."""
        import app as app_mod

        # Simulate the WSGI call cycle to get a response object.
        from bottle import response, request
        from io import BytesIO, StringIO

        env = {
            "REQUEST_METHOD": "GET",
            "PATH_INFO": "/",
            "SCRIPT_NAME": "",
            "SERVER_NAME": "lh",
            "SERVER_PORT": "80",
            "SERVER_PROTOCOL": "HTTP/1.1",
            "wsgi.version": (1, 0),
            "wsgi.url_scheme": "http",
            "wsgi.input": BytesIO(b""),
            "wsgi.errors": StringIO(),
            "CONTENT_LENGTH": "0",
            "CONTENT_TYPE": "text/html",
        }

        status = []
        headers = {}

        def start_response(s, h, exc=None):
            status.append(s)
            for k, v in h:
                headers[k] = v

        b"".join(app_mod.application(env, start_response))

        # Now the response is bound — set a session.
        app_mod._set_session("admin", "uid=admin,dc=example,dc=org")
        cookie = response.headerlist
        set_cookie = [v for k, v in cookie if k == "Set-Cookie"]
        assert any("admin_session" in c for c in set_cookie)

    def test_get_session_returns_none_without_cookie(self, app):
        """_get_session returns None when no cookie is set."""
        import app as app_mod

        # After a fresh request without a cookie, session should be None.
        from bottle import request
        from io import BytesIO, StringIO

        env = {
            "REQUEST_METHOD": "GET",
            "PATH_INFO": "/",
            "SCRIPT_NAME": "",
            "SERVER_NAME": "lh",
            "SERVER_PORT": "80",
            "SERVER_PROTOCOL": "HTTP/1.1",
            "wsgi.version": (1, 0),
            "wsgi.url_scheme": "http",
            "wsgi.input": BytesIO(b""),
            "wsgi.errors": StringIO(),
            "CONTENT_LENGTH": "0",
            "CONTENT_TYPE": "text/html",
        }
        s_list = []

        def sr(s, h, exc=None):
            s_list.append(s)

        b"".join(app_mod.application(env, sr))
        assert app_mod._get_session() is None


class TestCsrfOnAdminPages:

    def test_login_post_requires_csrf(self, client):
        """POST to /login without CSRF token shows error."""
        status, _h, body = client(
            "POST", "/login", body="username=test&password=test"
        )
        assert "Invalid or expired" in body


class TestConfig:

    def test_admin_section_optional(self, app):
        """App starts fine without an [admin] section."""
        import app as app_mod

        assert app_mod.CONF is not None

    def test_version_is_3(self, app):
        """Version bumped to 3.0.0 for the admin feature release."""
        import app as app_mod

        assert app_mod.VERSION == "3.0.0"
