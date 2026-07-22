#!/usr/bin/env python3

import base64
import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import ssl
import time
from collections import defaultdict, deque
from configparser import ConfigParser
from os import environ, path

import bottle
import ldap3
from bottle import (
    SimpleTemplate,
    get,
    post,
    redirect,
    request,
    response,
    route,
    static_file,
    template,
)
from ldap3 import (
    MODIFY_ADD,
    MODIFY_DELETE,
    SIMPLE,
    SUBTREE,
    Connection,
    Server,
    Tls,
)
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
VERSION = "3.0.0"

# ---------------------------------------------------------------------------
# Security: LDAP filter escaping (RFC 4515)
# ---------------------------------------------------------------------------

_LDAP_ESCAPE_RE = re.compile(r"[\x00*()\\]")
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

_CSRF_SECRET = secrets.token_bytes(32)


def _generate_csrf_token() -> str:
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("ascii")


def _get_csrf_cookie() -> str:
    token = request.get_cookie("csrf_token", secret=_CSRF_SECRET)
    if not token:
        token = _generate_csrf_token()
        response.set_cookie(
            "csrf_token",
            token,
            secret=_CSRF_SECRET,
            httponly=True,
            samesite="strict",
            secure=not environ.get("DEBUG"),
        )
    return token


def validate_csrf() -> bool:
    cookie_token = _get_csrf_cookie()
    form_token = request.forms.getunicode("csrf_token") or ""
    return hmac.compare_digest(cookie_token, form_token)


# ---------------------------------------------------------------------------
# Security: Admin session via signed cookie
# ---------------------------------------------------------------------------

_SESSION_SECRET = secrets.token_bytes(32)
_SESSION_MAX_AGE = 3600  # seconds


def _set_session(username: str, dn: str) -> None:
    """Store an admin session in a signed cookie."""
    payload = json.dumps(
        {"user": username, "dn": dn, "ts": int(time.time())}
    )
    response.set_cookie(
        "admin_session",
        payload,
        secret=_SESSION_SECRET,
        httponly=True,
        samesite="strict",
        secure=not environ.get("DEBUG"),
        max_age=_SESSION_MAX_AGE,
    )


def _get_session() -> dict | None:
    """Return the current admin session dict, or None."""
    data = request.get_cookie("admin_session", secret=_SESSION_SECRET)
    if not data:
        return None
    try:
        session = json.loads(data)
        if time.time() - session.get("ts", 0) > _SESSION_MAX_AGE:
            return None
        return session
    except (json.JSONDecodeError, ValueError):
        return None


def _require_admin():
    """Raise redirect to /login if there is no valid admin session."""
    if not _get_session():
        redirect("/login")


def _clear_session() -> None:
    response.delete_cookie("admin_session")


# ---------------------------------------------------------------------------
# Admin helpers
# ---------------------------------------------------------------------------


def _get_admin_ldap_section() -> str:
    """Return the LDAP config section name to use for admin operations."""
    if CONF.has_section("admin") and CONF["admin"].get("ldap_section"):
        return CONF["admin"]["ldap_section"]
    for key in CONF.sections():
        if key == "ldap" or key.startswith("ldap:"):
            return key
    raise Error("No LDAP section configured.")


def _check_admin_group(conn: Connection, user_dn: str) -> bool:
    """Return True if *user_dn* is a member of the admin group."""
    if not CONF.has_section("admin"):
        return False
    group_dn = CONF["admin"].get("admin_group_dn", "")
    if not group_dn:
        return False
    safe_dn = ldap_escape(user_dn)
    conn.search(
        group_dn,
        "(member=%s)" % safe_dn,
        SUBTREE,
        attributes=["dn"],
    )
    return len(conn.response) > 0


def _ldap_conf() -> ConfigParser:
    return CONF[_get_admin_ldap_section()]


# ---------------------------------------------------------------------------
# Security: In-memory rate limiter (sliding window)
# ---------------------------------------------------------------------------

_RATE_WINDOW = 60
_RATE_MAX_IP = 5
_RATE_MAX_USER = 10

_rate_by_ip: dict[str, deque] = defaultdict(lambda: deque())
_rate_by_user: dict[str, deque] = defaultdict(lambda: deque())


def _prune_window(dq: deque, cutoff: float) -> None:
    while dq and dq[0] < cutoff:
        dq.popleft()


def check_rate_limit(ip: str, username: str) -> str | None:
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
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Permitted-Cross-Domain-Policies"] = "none"

    if not environ.get("DEBUG"):
        response.headers[
            "Strict-Transport-Security"
        ] = "max-age=31536000; includeSubDomains"

    csp_parts = [
        "default-src 'self'",
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://unpkg.com",
        "font-src 'self' https://fonts.gstatic.com",
        "script-src 'self' 'unsafe-inline' https://unpkg.com",
        "img-src 'self' data:",
        "connect-src 'self'",
    ]
    response.headers["Content-Security-Policy"] = "; ".join(csp_parts)


# ---------------------------------------------------------------------------
# Routes — Public
# ---------------------------------------------------------------------------


@get("/")
def get_index():
    session = _get_session()
    return template(
        "index",
        csrf_token=_get_csrf_cookie(),
        password_policy=CONF["password"],
        admin_session=session,
    )


@post("/")
def post_index():
    form = request.forms.getunicode

    if not validate_csrf():
        LOG.warning("CSRF token validation failed from %s", request.remote_addr)
        return template(
            "index",
            csrf_token=_get_csrf_cookie(),
            password_policy=CONF["password"],
            alerts=[("error", "Invalid or expired form submission. Please try again.")],
        )

    username = form("username")
    rate_error = check_rate_limit(request.remote_addr, username)
    if rate_error:
        LOG.warning(
            "Rate limit hit from %s for user hash %s",
            request.remote_addr,
            hashlib.sha256(username.encode()).hexdigest()[:8],
        )
        response.status = 429
        return template(
            "index",
            csrf_token=_get_csrf_cookie(),
            password_policy=CONF["password"],
            username=username,
            alerts=[("error", bottle.html_escape(rate_error))],
        )

    def error(msg):
        return template(
            "index",
            csrf_token=_get_csrf_cookie(),
            password_policy=CONF["password"],
            username=username,
            alerts=[("error", bottle.html_escape(msg))],
        )

    new_pass = form("new-password")
    confirm_pass = form("confirm-password")

    if new_pass != confirm_pass:
        return error("Password doesn't match the confirmation!")

    pwd_policy = CONF["password"]
    min_len = pwd_policy.getint("min_length", 8)

    if len(new_pass) < min_len:
        return error(f"Password must be at least {min_len} characters long!")

    if pwd_policy.getboolean("require_uppercase", False):
        if not re.search(r"[A-Z]", new_pass):
            return error("Password must contain at least one uppercase letter!")
    if pwd_policy.getboolean("require_lowercase", False):
        if not re.search(r"[a-z]", new_pass):
            return error("Password must contain at least one lowercase letter!")
    if pwd_policy.getboolean("require_digit", False):
        if not re.search(r"[0-9]", new_pass):
            return error("Password must contain at least one digit!")
    if pwd_policy.getboolean("require_special", False):
        if not re.search(r"[^A-Za-z0-9]", new_pass):
            return error("Password must contain at least one special character!")

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

    return template(
        "index",
        csrf_token=_get_csrf_cookie(),
        password_policy=CONF["password"],
        alerts=[("success", "Password has been changed")],
    )


# ---------------------------------------------------------------------------
# Routes — Login / Logout
# ---------------------------------------------------------------------------


@get("/login")
def get_login():
    return template(
        "login",
        csrf_token=_get_csrf_cookie(),
    )


@post("/login")
def post_login():
    form = request.forms.getunicode

    if not validate_csrf():
        return template(
            "login",
            csrf_token=_get_csrf_cookie(),
            alerts=[("error", "Invalid or expired form submission.")],
        )

    username = form("username")
    password = form("password")

    if not username or not password:
        return template(
            "login",
            csrf_token=_get_csrf_cookie(),
            username=username,
            alerts=[("error", "Username and password are required.")],
        )

    try:
        conf = _ldap_conf()
        safe_uid = ldap_escape(username)

        # Bind as the user to verify credentials.
        user_dn = None
        with connect_ldap(conf) as c:
            user_dn = _find_user_dn(conf, c, safe_uid)

        if not user_dn:
            raise Error("Username or password is incorrect!")

        with connect_ldap(conf, authentication=SIMPLE, user=user_dn, password=password) as c:
            c.bind()
            # Check admin group membership.
            if not _check_admin_group(c, user_dn):
                raise Error(
                    "Access denied. You are not a member of the admin group."
                )

        # Authentication + authorization succeeded.
        _set_session(username, user_dn)
        LOG.info("Admin login: %s", hashlib.sha256(username.encode()).hexdigest()[:8])
        redirect("/admin")

    except Error as e:
        LOG.warning(
            "Failed admin login for user hash %s: %s",
            hashlib.sha256(username.encode()).hexdigest()[:8],
            e,
        )
        return template(
            "login",
            csrf_token=_get_csrf_cookie(),
            username=username,
            alerts=[("error", bottle.html_escape(str(e)))],
        )


@get("/logout")
def get_logout():
    _clear_session()
    redirect("/")


# ---------------------------------------------------------------------------
# Routes — Admin dashboard
# ---------------------------------------------------------------------------


@get("/admin")
def get_admin():
    _require_admin()
    session = _get_session()
    return template(
        "admin",
        csrf_token=_get_csrf_cookie(),
        password_policy=CONF["password"],
        admin_session=session,
    )


@post("/admin/change-password")
def post_admin_change_password():
    _require_admin()
    session = _get_session()
    form = request.forms.getunicode

    if not validate_csrf():
        return template(
            "admin",
            csrf_token=_get_csrf_cookie(),
            password_policy=CONF["password"],
            admin_session=session,
            alerts=[("error", "Invalid or expired form submission.")],
        )

    target_user = form("target-user") or session["user"]
    new_pass = form("new-password")
    confirm_pass = form("confirm-password")

    def error(msg):
        return template(
            "admin",
            csrf_token=_get_csrf_cookie(),
            password_policy=CONF["password"],
            admin_session=session,
            alerts=[("error", bottle.html_escape(msg))],
        )

    if new_pass != confirm_pass:
        return error("Password doesn't match the confirmation!")

    pwd_policy = CONF["password"]
    min_len = pwd_policy.getint("min_length", 8)

    if len(new_pass) < min_len:
        return error(f"Password must be at least {min_len} characters long!")

    if pwd_policy.getboolean("require_uppercase", False):
        if not re.search(r"[A-Z]", new_pass):
            return error("Password must contain at least one uppercase letter!")
    if pwd_policy.getboolean("require_lowercase", False):
        if not re.search(r"[a-z]", new_pass):
            return error("Password must contain at least one lowercase letter!")
    if pwd_policy.getboolean("require_digit", False):
        if not re.search(r"[0-9]", new_pass):
            return error("Password must contain at least one digit!")
    if pwd_policy.getboolean("require_special", False):
        if not re.search(r"[^A-Za-z0-9]", new_pass):
            return error("Password must contain at least one special character!")

    conf = _ldap_conf()
    safe_uid = ldap_escape(target_user)

    try:
        with connect_ldap(conf, authentication=SIMPLE, user=session["dn"],
                          password=form("admin-password")) as c:
            c.bind()
            user_dn = _find_user_dn(conf, c, safe_uid)
            if not user_dn:
                return error(f"User '{target_user}' not found.")
            c.extend.standard.modify_password(user_dn, None, new_pass)
    except (LDAPBindError, LDAPInvalidCredentialsResult):
        return error("Your admin password is incorrect!")
    except Error as e:
        return error(str(e))

    LOG.info(
        "Admin %s changed password for user hash %s",
        hashlib.sha256(session["user"].encode()).hexdigest()[:8],
        hashlib.sha256(target_user.encode()).hexdigest()[:8],
    )

    return template(
        "admin",
        csrf_token=_get_csrf_cookie(),
        password_policy=CONF["password"],
        admin_session=session,
        alerts=[("success", f"Password for {target_user} has been changed.")],
    )


@post("/admin/create-user")
def post_admin_create_user():
    _require_admin()
    session = _get_session()
    form = request.forms.getunicode

    if not validate_csrf():
        return template(
            "admin",
            csrf_token=_get_csrf_cookie(),
            password_policy=CONF["password"],
            admin_session=session,
            alerts=[("error", "Invalid or expired form submission.")],
        )

    uid = form("uid")
    cn = form("cn") or uid
    sn = form("sn") or uid
    mail = form("mail", "")
    user_password = form("user-password")
    admin_password = form("admin-password")

    def error(msg):
        return template(
            "admin",
            csrf_token=_get_csrf_cookie(),
            password_policy=CONF["password"],
            admin_session=session,
            alerts=[("error", bottle.html_escape(msg))],
        )

    if not uid or not user_password:
        return error("Username and password are required.")

    conf = _ldap_conf()
    safe_uid = ldap_escape(uid)

    try:
        with connect_ldap(conf, authentication=SIMPLE, user=session["dn"],
                          password=admin_password) as c:
            c.bind()

            # Check if the user already exists.
            if _find_user_dn(conf, c, safe_uid):
                return error(f"A user with uid '{uid}' already exists.")

            dn = "uid=%s,%s" % (safe_uid, conf["base"])
            attrs = {
                "objectClass": [
                    "top", "person", "organizationalPerson", "inetOrgPerson",
                ],
                "uid": uid,
                "cn": cn,
                "sn": sn,
                "userPassword": user_password,
            }
            if mail:
                attrs["mail"] = mail

            if not c.add(dn, attributes=attrs):
                result = c.result
                raise Error(
                    result.get("description", "Failed to create user.")
                )

    except (LDAPBindError, LDAPInvalidCredentialsResult):
        return error("Your admin password is incorrect!")
    except Error as e:
        LOG.error("Create user failed: %s", e)
        return error(str(e))

    LOG.info(
        "Admin %s created user %s",
        hashlib.sha256(session["user"].encode()).hexdigest()[:8],
        uid,
    )

    return template(
        "admin",
        csrf_token=_get_csrf_cookie(),
        password_policy=CONF["password"],
        admin_session=session,
        alerts=[("success", f"User '{uid}' created successfully.")],
    )


@post("/admin/create-group")
def post_admin_create_group():
    _require_admin()
    session = _get_session()
    form = request.forms.getunicode

    if not validate_csrf():
        return template(
            "admin",
            csrf_token=_get_csrf_cookie(),
            password_policy=CONF["password"],
            admin_session=session,
            alerts=[("error", "Invalid or expired form submission.")],
        )

    group_name = form("group-name")
    group_base = (
        CONF["admin"].get("group_base_dn")
        if CONF.has_section("admin")
        else _ldap_conf()["base"]
    )
    admin_password = form("admin-password")

    def error(msg):
        return template(
            "admin",
            csrf_token=_get_csrf_cookie(),
            password_policy=CONF["password"],
            admin_session=session,
            alerts=[("error", bottle.html_escape(msg))],
        )

    if not group_name:
        return error("Group name is required.")

    safe_name = ldap_escape(group_name)
    conf = _ldap_conf()

    try:
        with connect_ldap(conf, authentication=SIMPLE, user=session["dn"],
                          password=admin_password) as c:
            c.bind()

            dn = "cn=%s,%s" % (safe_name, group_base)
            attrs = {
                "objectClass": ["top", "groupOfNames"],
                "cn": group_name,
                "member": session["dn"],
            }

            if not c.add(dn, attributes=attrs):
                result = c.result
                raise Error(
                    result.get("description", "Failed to create group.")
                )

    except (LDAPBindError, LDAPInvalidCredentialsResult):
        return error("Your admin password is incorrect!")
    except Error as e:
        LOG.error("Create group failed: %s", e)
        return error(str(e))

    LOG.info(
        "Admin %s created group %s",
        hashlib.sha256(session["user"].encode()).hexdigest()[:8],
        group_name,
    )

    return template(
        "admin",
        csrf_token=_get_csrf_cookie(),
        password_policy=CONF["password"],
        admin_session=session,
        alerts=[("success", f"Group '{group_name}' created successfully.")],
    )


@post("/admin/modify-group")
def post_admin_modify_group():
    _require_admin()
    session = _get_session()
    form = request.forms.getunicode

    if not validate_csrf():
        return template(
            "admin",
            csrf_token=_get_csrf_cookie(),
            password_policy=CONF["password"],
            admin_session=session,
            alerts=[("error", "Invalid or expired form submission.")],
        )

    action = form("action")  # "add" or "remove"
    group_dn = form("group-dn")
    member_uid = form("member-uid")
    admin_password = form("admin-password")

    def error(msg):
        return template(
            "admin",
            csrf_token=_get_csrf_cookie(),
            password_policy=CONF["password"],
            admin_session=session,
            alerts=[("error", bottle.html_escape(msg))],
        )

    if not group_dn or not member_uid:
        return error("Group and member username are required.")

    if action not in ("add", "remove"):
        return error("Invalid action.")

    conf = _ldap_conf()
    safe_uid = ldap_escape(member_uid)

    try:
        with connect_ldap(conf, authentication=SIMPLE, user=session["dn"],
                          password=admin_password) as c:
            c.bind()

            # Find the member's DN.
            member_dn = _find_user_dn(conf, c, safe_uid)
            if not member_dn:
                return error(f"User '{member_uid}' not found.")

            mod_op = MODIFY_ADD if action == "add" else MODIFY_DELETE
            c.modify(group_dn, {"member": [(mod_op, [member_dn])]})

            if not c.result.get("description", "").startswith("success"):
                raise Error(
                    c.result.get("description", "Failed to modify group membership.")
                )

    except (LDAPBindError, LDAPInvalidCredentialsResult):
        return error("Your admin password is incorrect!")
    except Error as e:
        LOG.error("Group modify failed: %s", e)
        return error(str(e))

    verb = "added to" if action == "add" else "removed from"
    LOG.info(
        "Admin %s %s user %s %s group %s",
        hashlib.sha256(session["user"].encode()).hexdigest()[:8],
        action,
        member_uid,
        verb,
        group_dn,
    )

    return template(
        "admin",
        csrf_token=_get_csrf_cookie(),
        password_policy=CONF["password"],
        admin_session=session,
        alerts=[("success", f"User '{member_uid}' {verb} the group.")],
    )


@get("/admin/groups")
def get_admin_groups():
    """Return a JSON list of groups for the admin UI."""
    _require_admin()
    session = _get_session()
    form = request.query.getunicode
    admin_password = form("admin-password", "")

    if not admin_password:
        response.status = 400
        return {"error": "Admin password required"}

    conf = _ldap_conf()
    group_base = (
        CONF["admin"].get("group_base_dn")
        if CONF.has_section("admin")
        else conf["base"]
    )

    try:
        with connect_ldap(conf, authentication=SIMPLE, user=session["dn"],
                          password=admin_password) as c:
            c.bind()
            c.search(
                group_base,
                "(objectClass=groupOfNames)",
                SUBTREE,
                attributes=["cn", "member"],
            )
            groups = []
            for entry in c.response:
                groups.append({
                    "dn": entry.get("dn", ""),
                    "cn": entry.get("attributes", {}).get("cn", [""])[0],
                    "members": entry.get("attributes", {}).get("member", []),
                })

        response.content_type = "application/json"
        return json.dumps(groups)

    except (LDAPBindError, LDAPInvalidCredentialsResult):
        response.status = 401
        return {"error": "Admin password incorrect"}
    except Error as e:
        response.status = 500
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------


@route("/static/<filename>", name="static")
def serve_static(filename):
    return static_file(filename, root=path.join(BASE_DIR, "static"))


# ---------------------------------------------------------------------------
# LDAP helpers
# ---------------------------------------------------------------------------


def connect_ldap(conf, **kwargs):
    tls_config = None
    if conf.getboolean("use_ssl", False) or conf.getboolean("use_tls", False):
        tls_kwargs = {}
        ca_file = conf.get("tls_ca_cert_file", None)
        if ca_file:
            tls_kwargs["ca_certs_file"] = ca_file
        req_cert = conf.get("tls_req_cert", "demand")
        tls_kwargs["validate"] = {
            "demand": ssl.CERT_REQUIRED,
            "allow": ssl.CERT_OPTIONAL,
            "never": ssl.CERT_NONE,
        }.get(req_cert, ssl.CERT_REQUIRED)
        tls_config = Tls(**tls_kwargs)

    server = Server(
        host=conf["host"],
        port=conf.getint("port", None),
        use_ssl=conf.getboolean("use_ssl", False),
        tls=tls_config,
        connect_timeout=conf.getint("connect_timeout", 5),
    )

    return Connection(server, raise_exceptions=True, **kwargs)


def _find_user_dn(conf, conn, uid):
    """Search for a user DN. *uid* must already be LDAP-escaped."""
    search_filter = conf["search_filter"].replace("{uid}", uid)
    conn.search(conf["base"], "(%s)" % search_filter, SUBTREE)
    return conn.response[0]["dn"] if conn.response else None


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
        user_dn = _find_user_dn(conf, c, safe_uid)

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
        user_dn = _find_user_dn(conf, c, safe_uid)
        c.extend.microsoft.modify_password(user_dn, new_pass, old_pass)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


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

logging.basicConfig(format=LOG_FORMAT)
LOG.setLevel(logging.INFO)
LOG.info("Starting ldap-passwd-webui %s", VERSION)

CONF = read_config()

# Build a human-readable password policy description for the UI.
_pwd = CONF["password"]
_parts = ["At least " + _pwd.get("min_length", "8") + " characters"]
if _pwd.getboolean("require_uppercase", False):
    _parts.append("one uppercase letter")
if _pwd.getboolean("require_lowercase", False):
    _parts.append("one lowercase letter")
if _pwd.getboolean("require_digit", False):
    _parts.append("one digit")
if _pwd.getboolean("require_special", False):
    _parts.append("one special character")
requirements = _parts[1:]
if not requirements:
    _pwd["description"] = _parts[0]
elif len(requirements) == 1:
    _pwd["description"] = _parts[0] + " with " + requirements[0]
else:
    _pwd["description"] = (
        _parts[0] + " with " + ", ".join(requirements[:-1]) + " and " + requirements[-1]
    )

bottle.TEMPLATE_PATH = [BASE_DIR]

# Set default attributes to pass into templates.
SimpleTemplate.defaults = dict(CONF["html"])
SimpleTemplate.defaults["url"] = bottle.url

if __name__ == "__main__":
    bottle.run(**CONF["server"])
else:
    application = bottle.default_app()
