"""Tests for the rendered UI — HTML structure, JS presence, accessibility."""

import re


class TestHtmlStructure:

    def test_material_design_card_present(self, client):
        """Page uses a Material Design card layout."""
        _s, _h, body = client("GET", "/change-password")
        assert "md-card" in body
        assert "md-card--elevated" in body

    def test_form_has_all_fields(self, client):
        """Form contains username, three password fields, and a submit button."""
        _s, _h, body = client("GET", "/change-password")
        assert 'id="username"' in body
        assert 'id="old-password"' in body
        assert 'id="new-password"' in body
        assert 'id="confirm-password"' in body
        assert 'type="submit"' in body

    def test_no_label_elements(self, client):
        """Field wrappers are <div>, not <label>, to avoid click interception."""
        _s, _h, body = client("GET", "/change-password")
        assert "<label " not in body

    def test_toggle_buttons_present(self, client):
        """Each password field has a visibility toggle button."""
        _s, _h, body = client("GET", "/change-password")
        # Old-password, new-password, confirm-password → 3 toggle buttons.
        # Count only HTML elements (not the CSS selector in the JS).
        assert body.count('class="md-field__trailing-icon md-visibility-toggle"') == 3

    def test_strength_meter_present(self, client):
        """New password field has a strength meter."""
        _s, _h, body = client("GET", "/change-password")
        assert 'id="strength-meter"' in body
        assert 'id="strength-fill"' in body
        assert 'id="strength-label"' in body

    def test_match_indicator_present(self, client):
        """Confirm password field has a match indicator."""
        _s, _h, body = client("GET", "/change-password")
        assert 'id="match-text"' in body

    def test_snackbar_present(self, client):
        """Alert snackbar element exists in the page."""
        _s, _h, body = client("GET", "/change-password")
        assert 'id="snackbar"' in body


class TestJavaScript:

    def test_policy_object_injected(self, client):
        """The JS POLICY object is present with correct defaults."""
        _s, _h, body = client("GET", "/change-password")
        assert "var POLICY = {" in body
        assert "minLength: 8" in body
        assert "requireUppercase: false" in body
        assert "requireLowercase: false" in body
        assert "requireDigit:     false" in body
        assert "requireSpecial:   false" in body

    def test_calc_strength_function_present(self, client):
        """The strength-calculating function is in the JS."""
        _s, _h, body = client("GET", "/change-password")
        assert "function calcStrength" in body

    def test_event_delegation_present(self, client):
        """Form uses event delegation for click handling."""
        _s, _h, body = client("GET", "/change-password")
        assert "addEventListener('click'" in body
        assert "closest('.md-visibility-toggle')" in body
        assert "visibility_off" in body

    def test_field_focus_delegation(self, client):
        """Clicking a field focuses its input."""
        _s, _h, body = client("GET", "/change-password")
        assert "closest('.md-field')" in body
        assert "input.focus()" in body

    def test_csp_allows_inline_scripts(self, client):
        """CSP script-src includes 'unsafe-inline' so inline JS can run."""
        _s, headers, _body = client("GET", "/change-password")
        csp = headers.get("Content-Security-Policy", "")
        assert "'unsafe-inline'" in csp


class TestAccessibility:

    def test_inputs_have_aria_labels(self, client):
        """All inputs have aria-label for screen readers."""
        _s, _h, body = client("GET", "/change-password")
        assert body.count('aria-label="') >= 4

    def test_toggle_buttons_have_aria_labels(self, client):
        """Toggle buttons have descriptive aria-label."""
        _s, _h, body = client("GET", "/change-password")
        assert 'aria-label="Show password"' in body

    def test_snackbar_has_aria_live(self, client):
        """Snackbar uses aria-live for screen reader announcements."""
        _s, _h, body = client("GET", "/change-password")
        assert 'aria-live="assertive"' in body

    def test_strength_meter_has_role(self, client):
        """Strength meter fill has role=progressbar."""
        _s, _h, body = client("GET", "/change-password")
        assert 'role="progressbar"' in body

    def test_noindex_meta(self, client):
        """Page has noindex, nofollow robots meta."""
        _s, _h, body = client("GET", "/change-password")
        assert 'name="robots" content="noindex, nofollow"' in body


class TestResponsiveDesign:

    def test_viewport_meta(self, client):
        """Page has responsive viewport meta tag."""
        _s, _h, body = client("GET", "/change-password")
        assert 'name="viewport"' in body
        assert "initial-scale=1" in body

    def test_color_scheme_meta(self, client):
        """Page supports light/dark color schemes."""
        _s, _h, body = client("GET", "/change-password")
        assert 'name="color-scheme"' in body
        assert "dark" in body

    def test_reduced_motion_css(self, client):
        """CSS includes prefers-reduced-motion support."""
        _s, _h, _body = client("GET", "/change-password")
        # Check the CSS file
        css_resp = client("GET", "/static/style.css")[2]
        assert "prefers-reduced-motion" in css_resp

    def test_dark_theme_css(self, client):
        """CSS includes dark theme via prefers-color-scheme."""
        css_resp = client("GET", "/static/style.css")[2]
        assert "prefers-color-scheme: dark" in css_resp
