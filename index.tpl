<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex, nofollow">
  <meta name="theme-color" content="{{ get('primary_color', '#2e7d32') }}">
  <meta name="color-scheme" content="light dark">

  <title>{{ page_title }}</title>

  <!-- Material Symbols (icons) -->
  <link rel="stylesheet"
        href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0">
  <!-- Roboto font -->
  <link rel="stylesheet"
        href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap">

  <link rel="stylesheet" href="{{ url('static', filename='style.css') }}">

  % if get('primary_color'):
  <style>
    :root {
      --md-primary: {{ primary_color }};
    }
    @media (prefers-color-scheme: dark) {
      :root {
        --md-primary: {{ primary_color }};
      }
    }
  </style>
  % end
</head>

<body>
  <div class="app-layout">
    <!-- App bar -->
    <header class="md-top-app-bar">
      <div class="md-top-app-bar__row">
        <a href="{{ request.script_name }}/" class="md-top-app-bar__home-link" title="Home">
          <span class="material-symbols-outlined">arrow_back</span>
        </a>
        <span class="md-top-app-bar__title">{{ page_title }}</span>
        <span class="md-top-app-bar__spacer"></span>
        % if get('admin_session'):
        <a href="{{ request.script_name }}/admin" class="md-top-app-bar__admin-link" title="Admin Panel">
          <span class="material-symbols-outlined">admin_panel_settings</span>
        </a>
        % end
      </div>
    </header>

    <!-- Main content -->
    <main class="md-main">
      <div class="md-card md-card--elevated">
        <div class="md-card__content">
          <form method="post" action="{{ request.script_name }}/change-password" id="password-form" novalidate>
            <!-- CSRF token -->
            <input type="hidden" name="csrf_token" value="{{ csrf_token }}">

            <!-- Username -->
            <div class="md-field">
              <span class="md-field__icon material-symbols-outlined">person</span>
              <input class="md-field__input"
                     id="username"
                     name="username"
                     value="{{ get('username', '') }}"
                     type="text"
                     required
                     autofocus
                     autocomplete="username"
                     placeholder=" "
                     aria-label="Username">
              <span class="md-field__label">Username</span>
              <span class="md-field__outline"></span>
            </div>

            <!-- Old password -->
            <div class="md-field">
              <span class="md-field__icon material-symbols-outlined">lock_open</span>
              <input class="md-field__input md-field__input--password"
                     id="old-password"
                     name="old-password"
                     type="password"
                     required
                     autocomplete="current-password"
                     placeholder=" "
                     aria-label="Current password">
              <span class="md-field__label">Current password</span>
              <span class="md-field__outline"></span>
              <button type="button"
                      class="md-field__trailing-icon md-visibility-toggle"
                      aria-label="Show password">
                <span class="material-symbols-outlined">visibility</span>
              </button>
            </div>

            <!-- New password -->
            <div class="md-field">
              <span class="md-field__icon material-symbols-outlined">lock</span>
              <input class="md-field__input md-field__input--password"
                     id="new-password"
                     name="new-password"
                     type="password"
                     minlength="{{ password_policy['min_length'] }}"
                     required
                     autocomplete="new-password"
                     placeholder=" "
                     aria-label="New password">
              <span class="md-field__label">New password</span>
              <span class="md-field__outline"></span>
              <button type="button"
                      class="md-field__trailing-icon md-visibility-toggle"
                      aria-label="Show password">
                <span class="material-symbols-outlined">visibility</span>
              </button>
            </div>

            <!-- Password strength meter -->
            <div class="md-strength-meter" id="strength-meter" aria-live="polite">
              <div class="md-strength-meter__track">
                <div class="md-strength-meter__fill" id="strength-fill" role="progressbar"
                     aria-valuenow="0" aria-valuemin="0" aria-valuemax="4"></div>
              </div>
              <span class="md-strength-meter__label" id="strength-label"></span>
            </div>

            <!-- Password requirements hint (dynamic from config) -->
            <div class="md-helper-text">
              <span class="material-symbols-outlined md-helper-text__icon">info</span>
              <span id="policy-text">{{! password_policy['description'] }}</span>
            </div>

            <!-- Confirm new password -->
            <div class="md-field">
              <span class="md-field__icon material-symbols-outlined">lock_reset</span>
              <input class="md-field__input md-field__input--password"
                     id="confirm-password"
                     name="confirm-password"
                     type="password"
                     minlength="{{ password_policy['min_length'] }}"
                     required
                     autocomplete="new-password"
                     placeholder=" "
                     aria-label="Confirm new password">
              <span class="md-field__label">Confirm new password</span>
              <span class="md-field__outline"></span>
              <button type="button"
                      class="md-field__trailing-icon md-visibility-toggle"
                      aria-label="Show password">
                <span class="material-symbols-outlined">visibility</span>
              </button>
            </div>

            <!-- Password match indicator -->
            <div class="md-match-text" id="match-text" aria-live="polite"></div>

            <!-- Submit -->
            <button type="submit" class="md-filled-button" id="submit-btn">
              <span class="material-symbols-outlined">check_circle</span>
              <span>Update password</span>
            </button>
          </form>
        </div>
      </div>
    </main>

    <!-- Snackbar for alerts -->
    <div class="md-snackbar" id="snackbar" role="status" aria-live="assertive">
      <span class="md-snackbar__icon material-symbols-outlined" id="snackbar-icon"></span>
      <span class="md-snackbar__text" id="snackbar-text"></span>
      <button class="md-snackbar__dismiss" id="snackbar-dismiss" aria-label="Dismiss">
        <span class="material-symbols-outlined">close</span>
      </button>
    </div>
  </div>

  <script>
  (function () {
    'use strict';

    // ── Password policy from configuration ──────────────────────────────
    var POLICY = {
      minLength: {{ int(password_policy['min_length']) }},
      requireUppercase: {{ 'true' if password_policy.getboolean('require_uppercase', False) else 'false' }},
      requireLowercase: {{ 'true' if password_policy.getboolean('require_lowercase', False) else 'false' }},
      requireDigit:     {{ 'true' if password_policy.getboolean('require_digit', False) else 'false' }},
      requireSpecial:   {{ 'true' if password_policy.getboolean('require_special', False) else 'false' }}
    };

    // ── Form-level click delegation (one handler for everything) ──────
    document.getElementById('password-form').addEventListener('click', function (e) {
      // --- Password visibility toggle ---
      var toggleBtn = e.target.closest('.md-visibility-toggle');
      if (toggleBtn) {
        e.preventDefault();
        var field = toggleBtn.closest('.md-field');
        var input = field.querySelector('.md-field__input');
        var icon = toggleBtn.querySelector('.material-symbols-outlined');
        if (input.type === 'password') {
          input.type = 'text';
          icon.textContent = 'visibility_off';
          toggleBtn.setAttribute('aria-label', 'Hide password');
        } else {
          input.type = 'password';
          icon.textContent = 'visibility';
          toggleBtn.setAttribute('aria-label', 'Show password');
        }
        return;
      }

      // --- Field click to focus input ---
      var field = e.target.closest('.md-field');
      if (field && !e.target.closest('button, a')) {
        var input = field.querySelector('.md-field__input');
        if (input) input.focus();
      }
    });

    // ── Password strength meter ─────────────────────────────────────────
    var newPassEl = document.getElementById('new-password');
    var strengthFill = document.getElementById('strength-fill');
    var strengthLabel = document.getElementById('strength-label');
    var matchText = document.getElementById('match-text');
    var confirmPassEl = document.getElementById('confirm-password');

    var STRENGTH_LABELS = ['', 'Weak', 'Fair', 'Good', 'Strong'];
    var STRENGTH_COLORS = ['', 'var(--md-error)', 'var(--md-warning)', 'var(--md-info)', 'var(--md-success)'];

    function calcStrength(pw) {
      var score = 0;
      if (pw.length >= POLICY.minLength) score++;
      if (pw.length >= (POLICY.minLength + 4)) score++;

      var reqsSatisfied = 0, reqsTotal = 0;
      if (POLICY.requireUppercase)  { reqsTotal++; if (/[A-Z]/.test(pw)) reqsSatisfied++; }
      if (POLICY.requireLowercase)  { reqsTotal++; if (/[a-z]/.test(pw)) reqsSatisfied++; }
      if (POLICY.requireDigit)      { reqsTotal++; if (/[0-9]/.test(pw)) reqsSatisfied++; }
      if (POLICY.requireSpecial)    { reqsTotal++; if (/[^A-Za-z0-9]/.test(pw)) reqsSatisfied++; }

      if (reqsTotal > 0 && reqsSatisfied >= reqsTotal) score++;
      if (!POLICY.requireUppercase && /[A-Z]/.test(pw) && /[a-z]/.test(pw)) score++;
      if (!POLICY.requireDigit && /[0-9]/.test(pw)) score++;
      if (!POLICY.requireSpecial && /[^A-Za-z0-9]/.test(pw)) score++;

      return Math.min(4, score);
    }

    newPassEl.addEventListener('input', function () {
      var s = calcStrength(this.value);
      strengthFill.style.width = (s / 4 * 100) + '%';
      strengthFill.style.backgroundColor = STRENGTH_COLORS[s];
      strengthLabel.textContent = STRENGTH_LABELS[s];
      strengthLabel.style.color = STRENGTH_COLORS[s];
      strengthFill.setAttribute('aria-valuenow', s);

      checkMatch();
    });

    confirmPassEl.addEventListener('input', checkMatch);

    function checkMatch() {
      var newPw = newPassEl.value;
      var confirmPw = confirmPassEl.value;
      if (!confirmPw) {
        matchText.textContent = '';
        matchText.className = 'md-match-text';
      } else if (newPw === confirmPw) {
        matchText.textContent = 'Passwords match';
        matchText.className = 'md-match-text md-match-text--success';
      } else {
        matchText.textContent = 'Passwords do not match';
        matchText.className = 'md-match-text md-match-text--error';
      }
    }

    // ── Snackbar ────────────────────────────────────────────────────────
    % if alerts:
    (function () {
      var type = '{{ alerts[0][0] }}';
      var text = document.getElementById('snackbar-text');
      var icon = document.getElementById('snackbar-icon');
      var snackbar = document.getElementById('snackbar');

      text.textContent = '{{! alerts[0][1] }}';
      if (type === 'error') {
        icon.textContent = 'error';
        snackbar.className = 'md-snackbar md-snackbar--error md-snackbar--show';
      } else {
        icon.textContent = 'check_circle';
        snackbar.className = 'md-snackbar md-snackbar--success md-snackbar--show';
      }

      setTimeout(function () {
        snackbar.classList.remove('md-snackbar--show');
      }, 6000);

      document.getElementById('snackbar-dismiss').addEventListener('click', function () {
        snackbar.classList.remove('md-snackbar--show');
      });
    })();
    % end

    // ── Form submission UX ──────────────────────────────────────────────
    var form = document.getElementById('password-form');
    var submitBtn = document.getElementById('submit-btn');

    form.addEventListener('submit', function () {
      submitBtn.classList.add('md-filled-button--loading');
      submitBtn.disabled = true;
    });
  })();
  </script>
</body>
</html>
