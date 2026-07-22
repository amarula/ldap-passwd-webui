#!/usr/bin/env python3

import base64
import hashlib
import hmac
import logging
import os
import re
import secrets
import time
from collections import defaultdict, deque
from configparser import ConfigParser
from os import environ, path

import bottle
import ldap3
from bottle import SimpleTemplate, get, post, request, route, static_file, template
from ldap3 import SIMPLE, SUBTREE, Connection, Server, Tls
from ldap3.core.exceptions import (
    LDAPBindError,
    LDAPConstraintViolationResult,
    LDAPExceptionError,
    LDAPInvalidCredentialsResult,
    LDAPSocketOpenError,
    LDAPUserNameIsMandatoryError,
)

BASE_DIR = path.dirname(__file__)
LOG = logging.getLogger(__name__)
LOG_FORMAT = "%(asctime)s %(levelname)s: %(message)s"
VERSION = "2.2.0"

# ---------------------------------------------------------------------------
# Security: LDAP filter escaping (RFC 4515)
# ---------------------------------------------------------------------------

_LDAP_ESCAPE_RE = re.compile(r'[\x00*()\\]')
_LDAP_ESCAPE_MAP = {
    "\x00": "\\00",
    "*": "\\2a",
    "(": "\\28",
    ")": "\\29",
    "\\": "\\5c",
}


def ldap_escape(value: str) -> str:
    """Escape special characters in an LDAP filter value per RFC 4515."""
    return _LDAP_ESCAPE_RE.sub(lambda m: _LDAP_ESCAPE_MAP[m.group(0)], value)


# ---------------------------------------------------------------------------
# Security: CSRF protection via signed cookie
# ---------------------------------------------------------------------------

# Regenerated on every app restart — invalidates all previous tokens.
_CSRF_SECRET = secrets.token_bytes(32)


def _generate_csrf_token() -> str:
    """Return a fresh random CSRF token (base64-encoded)."""
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("ascii")


def _sign_token(token: str) -> str:
    """Return a HMAC-SHA256 signature of *token*."""
    return hmac.new(_CSRF_SECRET, token.encode(), hashlib.sha256).hexdigest()


def _get_csrf_cookie() -> str:
    """Retrieve the current CSRF cookie, or generate a new one."""
    token = request.get_cookie("csrf_token", secret=_CSRF_SECRET)
    if not token:
        token = _generate_csrf_token()
        bottle.response.set_cookie(
            "csrf_token",
            token,
            secret=_CSRF_SECRET,
            httponly=True,
            samesite="strict",
            secure=not environ.get("DEBUG"),
        )
    return token


def validate_csrf() -> bool:
    """Return True when the submitted CSRF token matches the cookie token."""
    cookie_token = _get_csrf_cookie()
    form_token = request.forms.getunicode("csrf_token") or ""
    return hmac.compare_digest(cookie_token, form_token)


# ---------------------------------------------------------------------------
# Security: In-memory rate limiter (sliding window)
# ---------------------------------------------------------------------------

_RATE_WINDOW = 60  # seconds
_RATE_MAX_IP = 5  # max attempts per window per IP
_RATE_MAX_USER = 10  # max attempts per window per username

_rate_by_ip: dict[str, deque] = defaultdict(lambda: deque())
_rate_by_user: dict[str, deque] = defaultdict(lambda: deque())


def _prune_window(dq: deque, cutoff: float) -> None:
    while dq and dq[0] < cutoff:
        dq.popleft()


def check_rate_limit(ip: str, username: str) -> str | None:
    """
    Return an error message when the rate limit is exceeded, or *None*.
    """
    now = time.monotonic()
    cutoff = now - _RATE_WINDOW

    ip_dq = _rate_by_ip[ip]
    _prune_window(ip_dq, cutoff)
    ip_dq.append(now)
    if len(ip_dq) > _RATE_MAX_IP:
        return "Too many attempts from this IP address. Please wait a minute and try again."

    user_dq = _rate_by_user[username]
    _prune_window(user_dq, cutoff)
    user_dq.append(now)
    if len(user_dq) > _RATE_MAX_USER:
        return "Too many attempts for this account. Please wait a minute and try again."

    return None


# ---------------------------------------------------------------------------
# Security: Response headers hook
# ---------------------------------------------------------------------------

@bottle.hook("after_request")
def set_security_headers():
    """Add security-related HTTP headers to every response."""
    bottle.response.headers["X-Frame-Options"] = "DENY"
    bottle.response.headers["X-Content-Type-Options"] = "nosniff"
    bottle.response.headers["X-XSS-Protection"] = "1; mode=block"
    bottle.response.headers["Referrer-Policy"] = "no-referrer"
    bottle.response.headers["X-Permitted-Cross-Domain-Policies"] = "none"

    hsts_secs = 31536000 if not environ.get("DEBUG") else 0
    if hsts_secs:
        bottle.response.headers[
            "Strict-Transport-Security"
        ] = f"max-age={hsts_secs}; includeSubDomains"

    csp_parts = [
        "default-src 'self'",
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://unpkg.com",
        "font-src 'self' https://fonts.gstatic.com",
        "script-src 'self' https://unpkg.com",
        "img-src 'self' data:",
        "connect-src 'self'",
    ]
    bottle.response.headers["Content-Security-Policy"] = "; ".join(csp_parts)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@get("/")
def get_index():
    return index_tpl(csrf_token=_get_csrf_cookie())


@post("/")
def post_index():
    form = request.forms.getunicode

    # --- CSRF check ---------------------------------------------------------
    if not validate_csrf():
        LOG.warning("CSRF token validation failed from %s", request.remote_addr)
        return index_tpl(
            csrf_token=_get_csrf_cookie(),
            alerts=[("error", "Invalid or expired form submission. Please try again.")],
        )

    # --- Rate-limit check ---------------------------------------------------
    username = form("username")
    rate_error = check_rate_limit(request.remote_addr, username)
    if rate_error:
        LOG.warning("Rate limit hit from %s for user hash %s",
                     request.remote_addr,
                     hashlib.sha256(username.encode()).hexdigest()[:8])
        bottle.response.status = 429
        return index_tpl(
            csrf_token=_get_csrf_cookie(),
            username=username,
            alerts=[("error", bottle.html_escape(rate_error))],
        )

    # --- Helper to re-render with error -------------------------------------
    def error(msg):
        return index_tpl(
            csrf_token=_get_csrf_cookie(),
            username=username,
            alerts=[("error", bottle.html_escape(msg))],
        )

    # --- Validation ---------------------------------------------------------
    new_pass = form("new-password")
    confirm_pass = form("confirm-password")

    if new_pass != confirm_pass:
        return error("Password doesn't match the confirmation!")

    if len(new_pass) < 8:
        return error("Password must be at least 8 characters long!")

    # --- Password complexity ------------------------------------------------
    if not re.search(r"[A-Z]", new_pass):
        return error("Password must contain at least one uppercase letter!")
    if not re.search(r"[a-z]", new_pass):
        return error("Password must contain at least one lowercase letter!")
    if not re.search(r"[0-9]", new_pass):
        return error("Password must contain at least one digit!")
    if not re.search(r"[^A-Za-z0-9]", new_pass):
        return error(
            "Password must contain at least one special character (!@#$%^&* etc.)!"
        )

    # --- Perform password change --------------------------------------------
    try:
        change_passwords(username, form("old-password"), new_pass)
    except Error as e:
        LOG.warning(
            "Unsuccessful attempt to change password for user hash %s: %s",
            hashlib.sha256(username.encode()).hexdigest()[:8],
            e,
        )
        return error(str(e))

    LOG.info(
        "Password successfully changed for user hash: %s",
        hashlib.sha256(username.encode()).hexdigest()[:8],
    )

    return index_tpl(
        csrf_token=_get_csrf_cookie(),
        alerts=[("success", "Password has been changed")],
    )


@route("/static/<filename>", name="static")
def serve_static(filename):
    return static_file(filename, root=path.join(BASE_DIR, "static"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def index_tpl(**kwargs):
    return template("index", **kwargs)


def connect_ldap(conf, **kwargs):
    tls_config = None
    if conf.getboolean("use_ssl", False) or conf.getboolean("use_tls", False):
        tls_kwargs = {}
        ca_file = conf.get("tls_ca_cert_file", None)
        if ca_file:
            tls_kwargs["ca_certs_file"] = ca_file
        req_cert = conf.get("tls_req_cert", "demand")
        tls_kwargs["validate"] = {
            "demand": ldap3.TlsValidateStrategy.DEMAND,
            "allow": ldap3.TlsValidateStrategy.ALLOW,
            "never": ldap3.TlsValidateStrategy.NEVER,
        }.get(req_cert, ldap3.TlsValidateStrategy.DEMAND)
        tls_config = Tls(**tls_kwargs)

    server = Server(
        host=conf["host"],
        port=conf.getint("port", None),
        use_ssl=conf.getboolean("use_ssl", False),
        tls=tls_config,
        connect_timeout=conf.getint("connect_timeout", 5),
    )

    return Connection(server, raise_exceptions=True, **kwargs)


def change_passwords(username, old_pass, new_pass):
    changed = []

    ldap_sections = [
        key
        for key in CONF.sections()
        if key == "ldap" or key.startswith("ldap:")
    ]

    for key in ldap_sections:
        LOG.debug(
            "Changing password in %s for user hash %s",
            key,
            hashlib.sha256(username.encode()).hexdigest()[:8],
        )
        try:
            change_password(CONF[key], username, old_pass, new_pass)
            changed.append(key)
        except Error as e:
            # Rollback previously changed LDAPs
            for rollback_key in reversed(changed):
                LOG.info(
                    "Reverting password change in %s for user hash %s",
                    rollback_key,
                    hashlib.sha256(username.encode()).hexdigest()[:8],
                )
                try:
                    change_password(CONF[rollback_key], username, new_pass, old_pass)
                except Error as e2:
                    LOG.error("%s: %s", e2.__class__.__name__, e2)
            raise e


def change_password(conf, *args):
    try:
        if conf.get("type") == "ad":
            change_password_ad(conf, *args)
        else:
            change_password_ldap(conf, *args)

    except (LDAPBindError, LDAPInvalidCredentialsResult, LDAPUserNameIsMandatoryError):
        raise Error("Username or password is incorrect!")

    except LDAPConstraintViolationResult as e:
        # Extract useful part of the error message (for Samba 4 / AD).
        msg = e.message.split("check_password_restrictions: ")[-1].capitalize()
        raise Error(msg)

    except LDAPSocketOpenError as e:
        LOG.error("%s: %s", e.__class__.__name__, e)
        raise Error("Unable to connect to the remote server.")

    except LDAPExceptionError as e:
        LOG.error("%s: %s", e.__class__.__name__, e)
        raise Error(
            "Encountered an unexpected error while communicating with the remote server."
        )


def change_password_ldap(conf, username, old_pass, new_pass):
    safe_uid = ldap_escape(username)

    with connect_ldap(conf) as c:
        user_dn = find_user_dn(conf, c, safe_uid)

    # Note: raises LDAPUserNameIsMandatoryError when user_dn is None.
    with connect_ldap(
        conf, authentication=SIMPLE, user=user_dn, password=old_pass
    ) as c:
        c.bind()
        c.extend.standard.modify_password(user_dn, old_pass, new_pass)


def change_password_ad(conf, username, old_pass, new_pass):
    safe_uid = ldap_escape(username)
    user = username + "@" + conf["ad_domain"]

    with connect_ldap(conf, authentication=SIMPLE, user=user, password=old_pass) as c:
        c.bind()
        user_dn = find_user_dn(conf, c, safe_uid)
        c.extend.microsoft.modify_password(user_dn, new_pass, old_pass)


def find_user_dn(conf, conn, uid):
    """Search for a user DN. *uid* must already be LDAP-escaped."""
    search_filter = conf["search_filter"].replace("{uid}", uid)
    conn.search(conf["base"], "(%s)" % search_filter, SUBTREE)

    return conn.response[0]["dn"] if conn.response else None


def read_config():
    config = ConfigParser()
    config.read([path.join(BASE_DIR, "settings.ini"), os.getenv("CONF_FILE", "")])

    return config


class Error(Exception):
    pass


# ---------------------------------------------------------------------------
# Application bootstrap
# ---------------------------------------------------------------------------

if environ.get("DEBUG"):
    bottle.debug(True)

# Set up logging.
logging.basicConfig(format=LOG_FORMAT)
LOG.setLevel(logging.INFO)
LOG.info("Starting ldap-passwd-webui %s", VERSION)

CONF = read_config()

bottle.TEMPLATE_PATH = [BASE_DIR]

# Set default attributes to pass into templates.
SimpleTemplate.defaults = dict(CONF["html"])
SimpleTemplate.defaults["url"] = bottle.url

# Run bottle internal server when invoked directly (mainly for development).
if __name__ == "__main__":
    bottle.run(**CONF["server"])
# Run bottle in application mode (in production under a WSGI server).
else:
    application = bottle.default_app()
