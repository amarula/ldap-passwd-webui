"""Tests for password validation and config-driven policy."""

import re

import pytest


class TestPasswordValidation:

    def test_password_too_short(self, session):
        """Password under min_length (8) is rejected."""
        _status, _headers, body = session.post(
            username="u",
            **{"old-password": "old"},
            **{"new-password": "Ab1!"},
            **{"confirm-password": "Ab1!"},
        )
        assert "at least 8 characters" in body.lower()

    def test_password_mismatch(self, session):
        """New password and confirmation must match."""
        _status, _headers, body = session.post(
            username="u",
            **{"old-password": "old"},
            **{"new-password": "Abcdef12!"},
            **{"confirm-password": "Xyz9876#"},
        )
        assert "doesn't match" in body.lower() or "doesn&#039;t match" in body.lower()

    def test_password_meets_minimum_requirements(self, session):
        """8-char password with no class requirements passes local validation."""
        _status, _headers, body = session.post(
            username="u",
            **{"old-password": "old"},
            **{"new-password": "12345678"},
            **{"confirm-password": "12345678"},
        )
        # No LDAP configured → password change "succeeds" (zero iterations).
        # Check the snackbar text specifically, not the whole body (which
        # always contains the policy helper text).
        snackbar = re.search(r"text\.textContent\s*=\s*'([^']*)'", body)
        assert snackbar is not None
        msg = snackbar.group(1)
        assert "uppercase" not in msg.lower()
        assert "lowercase" not in msg.lower()
        assert "digit" not in msg.lower()
        assert "special" not in msg.lower()
        assert "8 character" not in msg.lower()


class TestConfigurablePolicy:

    def test_uppercase_required(self, load_app_with):
        """When require_uppercase is on, all-lowercase is rejected."""
        app_mod = load_app_with(
            require_uppercase="true",
            require_lowercase="true",
            require_digit="true",
            require_special="true",
        )
        from io import BytesIO

        # Helper to make WSGI calls against the freshly loaded app.
        def wsgi(method, path, body="", cookie=""):
            body_bytes = body.encode() if isinstance(body, str) else body
            env = {
                "REQUEST_METHOD": method,
                "PATH_INFO": path,
                "SCRIPT_NAME": "",
                "SERVER_NAME": "lh",
                "SERVER_PORT": "80",
                "SERVER_PROTOCOL": "HTTP/1.1",
                "wsgi.version": (1, 0),
                "wsgi.url_scheme": "http",
                "wsgi.input": BytesIO(body_bytes),
                "wsgi.errors": BytesIO(),
                "CONTENT_LENGTH": str(len(body_bytes)),
                "CONTENT_TYPE": "application/x-www-form-urlencoded",
            }
            if cookie:
                env["HTTP_COOKIE"] = cookie
            s = []
            h = {}

            def sr(st, hdrs, exc=None):
                s.append(st)
                for k, v in hdrs:
                    h[k] = v

            bd = b"".join(app_mod.application(env, sr))
            return s[0] if s else "", h, bd.decode()

        # GET
        _s1, hdrs1, body1 = wsgi("GET", "/")
        cookie = hdrs1.get("Set-Cookie", "").split(";")[0].strip()
        token = re.search(r'name="csrf_token" value="([^"]*)"', body1).group(1)

        def post(body_str):
            nonlocal cookie, token
            s, h, b = wsgi("POST", "/", body_str, cookie)
            if "Set-Cookie" in h:
                cookie = h["Set-Cookie"].split(";")[0].strip()
            m = re.search(r'name="csrf_token" value="([^"]*)"', b)
            if m:
                token = m.group(1)
            sm = re.search(r"text\.textContent\s*=\s*'([^']*)'", b)
            return sm.group(1) if sm else None

        msg = post(
            f"csrf_token={token}&username=u&old-password=o&"
            "new-password=alllowercase1!&confirm-password=alllowercase1!"
        )
        assert msg and "uppercase" in msg.lower()

        msg = post(
            f"csrf_token={token}&username=u&old-password=o&"
            "new-password=ALLUPPERCASE1!&confirm-password=ALLUPPERCASE1!"
        )
        assert msg and "lowercase" in msg.lower()

        msg = post(
            f"csrf_token={token}&username=u&old-password=o&"
            "new-password=NoDigitsHere!&confirm-password=NoDigitsHere!"
        )
        assert msg and "digit" in msg.lower()

        msg = post(
            f"csrf_token={token}&username=u&old-password=o&"
            "new-password=NoSpecial1&confirm-password=NoSpecial1"
        )
        assert msg and "special" in msg.lower()


class TestPolicyDescription:

    @pytest.mark.parametrize(
        "password_opts,expected_text",
        [
            ({}, "At least 8 characters"),
            (
                {"require_uppercase": "true"},
                "At least 8 characters with one uppercase letter",
            ),
            (
                {"require_uppercase": "true", "require_digit": "true"},
                "At least 8 characters with one uppercase letter and one digit",
            ),
            (
                {
                    "require_uppercase": "true",
                    "require_lowercase": "true",
                    "require_digit": "true",
                    "require_special": "true",
                },
                "At least 8 characters with one uppercase letter, "
                "one lowercase letter, one digit and one special character",
            ),
        ],
    )
    def test_policy_description(self, load_app_with, password_opts, expected_text):
        """Helper text reflects the configured policy."""
        import re
        from io import BytesIO

        app_mod = load_app_with(**password_opts)

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
            "wsgi.errors": BytesIO(),
            "CONTENT_LENGTH": "0",
            "CONTENT_TYPE": "application/x-www-form-urlencoded",
        }

        def sr(st, hdrs, exc=None):
            pass

        body = b"".join(app_mod.application(env, sr)).decode()
        m = re.search(r'id="policy-text">([^<]*)', body)
        assert m is not None, f"policy-text not found in: {body[:500]}"
        assert m.group(1) == expected_text
