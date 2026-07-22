"""Test fixtures for ldap-passwd-webui."""

import os
import sys
import tempfile
from configparser import ConfigParser
from io import BytesIO

import pytest


def _build_config(**password_opts) -> ConfigParser:
    """Return a ConfigParser with the minimal required sections."""
    c = ConfigParser()
    c.add_section("html")
    c["html"]["page_title"] = "Test Password Change"
    c.add_section("password")
    c["password"]["min_length"] = password_opts.pop("min_length", "8")
    for key, val in password_opts.items():
        c["password"][key] = str(val).lower()
    c.add_section("server")
    c["server"]["server"] = "auto"
    c["server"]["host"] = "localhost"
    c["server"]["port"] = "8080"
    return c


def _write_config(config: ConfigParser) -> str:
    """Write *config* to a temp file and return the path."""
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".ini", delete=False, encoding="utf-8"
    )
    config.write(tmp)
    tmp.close()
    return tmp.name


def _clear_app_modules():
    """Remove cached app modules so the next import picks up fresh config."""
    for key in list(sys.modules):
        if key == "app" or str(key).startswith("app."):
            del sys.modules[key]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def config():
    """A fresh minimal ConfigParser (no complexity checks)."""
    return _build_config()


@pytest.fixture
def strict_config():
    """A ConfigParser with all complexity checks enabled."""
    return _build_config(
        require_uppercase="true",
        require_lowercase="true",
        require_digit="true",
        require_special="true",
    )


@pytest.fixture
def config_file(config):
    """Write *config* to a temp file, set ``CONF_FILE``, return the path."""
    path = _write_config(config)
    old = os.environ.get("CONF_FILE")
    os.environ["CONF_FILE"] = path
    os.environ["DEBUG"] = "1"
    yield path
    os.unlink(path)
    if old is not None:
        os.environ["CONF_FILE"] = old
    else:
        os.environ.pop("CONF_FILE", None)


@pytest.fixture
def app(config_file):
    """Return the Bottle WSGI application.

    Creates a fresh config file, sets ``CONF_FILE``, clears the module
    cache, and imports the app module.
    """
    _clear_app_modules()
    import app  # noqa: E402
    return app.application


@pytest.fixture
def client(app):
    """Return a callable that simulates a WSGI request.

    Usage::

        status, headers, body = client("GET", "/")
        status, headers, body = client("POST", "/", body="a=1&b=2")
    """

    def _call(method, path, body="", cookie=""):
        body_bytes = body.encode() if isinstance(body, str) else body
        environ = {
            "REQUEST_METHOD": method,
            "PATH_INFO": path,
            "SCRIPT_NAME": "",
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "8080",
            "SERVER_PROTOCOL": "HTTP/1.1",
            "wsgi.version": (1, 0),
            "wsgi.url_scheme": "http",
            "wsgi.input": BytesIO(body_bytes),
            "wsgi.errors": BytesIO(),
            "CONTENT_LENGTH": str(len(body_bytes)),
            "CONTENT_TYPE": "application/x-www-form-urlencoded",
        }
        if cookie:
            environ["HTTP_COOKIE"] = cookie

        status = []
        resp_headers = {}

        def start_response(s, h, exc_info=None):
            status.append(s)
            for k, v in h:
                resp_headers[k] = v

        resp_body = b"".join(app(environ, start_response))
        return status[0] if status else "", resp_headers, resp_body.decode()

    return _call


@pytest.fixture
def session(client):
    """Return an object with ``csrf_token``, ``cookie``, and a ``post()`` method.

    Initialized by fetching the form once (GET /).
    """

    class Session:
        def __init__(self):
            import re

            _status, headers, body = client("GET", "/")
            self.csrf_token = re.search(
                r'name="csrf_token" value="([^"]*)"', body
            ).group(1)
            self.cookie = headers.get("Set-Cookie", "").split(";")[0].strip()

        def post(self, **form_data):
            """POST / with the session CSRF token and *form_data*.

            Returns ``(status, headers, body)`` and updates the session
            cookie + token from the response.
            """
            import re
            from urllib.parse import urlencode

            form_data.setdefault("csrf_token", self.csrf_token)
            body_str = urlencode(form_data)
            status, headers, resp_body = client(
                "POST", "/", body=body_str, cookie=self.cookie
            )

            new_cookie = headers.get("Set-Cookie", "")
            if new_cookie:
                self.cookie = new_cookie.split(";")[0].strip()

            m = re.search(r'name="csrf_token" value="([^"]*)"', resp_body)
            if m:
                self.csrf_token = m.group(1)

            return status, headers, resp_body

    return Session()


# ---------------------------------------------------------------------------
# Helper to re-load app with a custom config for policy tests
# ---------------------------------------------------------------------------


@pytest.fixture
def load_app_with():
    """Return a function that writes *config* to a temp file, reloads the
    app module, and returns the fresh application object.

    Usage::

        app_mod = load_app_with(require_uppercase="true")
    """
    import importlib

    def _load(**password_opts):
        cfg = _build_config(**password_opts)
        path = _write_config(cfg)
        os.environ["CONF_FILE"] = path
        os.environ["DEBUG"] = "1"
        _clear_app_modules()
        import app as app_mod
        return app_mod

    yield _load
