<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex, nofollow">
  <meta name="theme-color" content="#1b5e20">
  <meta name="color-scheme" content="light dark">

  <title>{{ page_title }}</title>

  <!-- Material Symbols (icons) -->
  <link rel="stylesheet"
        href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0">
  <!-- Roboto font -->
  <link rel="stylesheet"
        href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap">

  <link rel="stylesheet" href="{{ url('static', filename='style.css') }}">
</head>

<body>
  <div class="app-layout">
    <!-- App bar -->
    <header class="md-top-app-bar">
      <div class="md-top-app-bar__row">
        <span class="material-symbols-outlined md-top-app-bar__icon">lock</span>
        <span class="md-top-app-bar__title">{{ page_title }}</span>
      </div>
    </header>

    <!-- Main content -->
    <main class="md-main">
      <div class="md-card md-card--elevated">
        <div class="md-card__content">
          <form method="post" id="password-form" novalidate>
            <!-- CSRF token -->
            <input type="hidden" name="csrf_token" value="{{ csrf_token }}">

            <!-- Username -->
            <label class="md-field">
              <span class="md-field__icon material-symbols-outlined">person</span>
              <input class="md-field__input"
                     id="username"
                     name="username"
                     value="{{ get('username', '') }}"
                     type="text"
                     required
                     autofocus
                     autocomplete="username"
                     placeholder=" ">
              <span class="md-field__label">Username</span>
              <span class="md-field__outline"></span>
            </label>

            <!-- Old password -->
            <label class="md-field">
              <span class="md-field__icon material-symbols-outlined">lock_open</span>
              <input class="md-field__input md-field__input--password"
                     id="old-password"
                     name="old-password"
                     type="password"
                     required
                     autocomplete="current-password"
                     placeholder=" ">
              <span class="md-field__label">Current password</span>
              <span class="md-field__outline"></span>
              <button type="button"
                      class="md-field__trailing-icon md-visibility-toggle"
                      tabindex="-1"
                      aria-label="Show password">
                <span class="material-symbols-outlined">visibility</span>
              </button>
            </label>

            <!-- New password -->
            <label class="md-field">
              <span class="md-field__icon material-symbols-outlined">lock</span>
              <input class="md-field__input md-field__input--password"
                     id="new-password"
                     name="new-password"
                     type="password"
                     minlength="8"
                     required
                     autocomplete="new-password"
                     placeholder=" ">
              <span class="md-field__label">New password</span>
              <span class="md-field__outline"></span>
              <button type="button"
                      class="md-field__trailing-icon md-visibility-toggle"
                      tabindex="-1"
                      aria-label="Show password">
                <span class="material-symbols-outlined">visibility</span>
              </button>
            </label>

            <!-- Password strength meter -->
            <div class="md-strength-meter" id="strength-meter" aria-live="polite">
              <div class="md-strength-meter__track">
                <div class="md-strength-meter__fill" id="strength-fill" role="progressbar"
                     aria-valuenow="0" aria-valuemin="0" aria-valuemax="4"></div>
              </div>
              <span class="md-strength-meter__label" id="strength-label"></span>
            </div>

            <!-- Password requirements hint -->
            <div class="md-helper-text">
              <span class="material-symbols-outlined md-helper-text__icon">info</span>
              <span>At least 8 characters with uppercase, lowercase, digit, and special character</span>
            </div>

            <!-- Confirm new password -->
            <label class="md-field">
              <span class="md-field__icon material-symbols-outlined">lock_reset</span>
              <input class="md-field__input md-field__input--password"
                     id="confirm-password"
                     name="confirm-password"
                     type="password"
                     minlength="8"
                     required
                     autocomplete="new-password"
                     placeholder=" ">
              <span class="md-field__label">Confirm new password</span>
              <span class="md-field__outline"></span>
              <button type="button"
                      class="md-field__trailing-icon md-visibility-toggle"
                      tabindex="-1"
                      aria-label="Show password">
                <span class="material-symbols-outlined">visibility</span>
              </button>
            </label>

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

    // ── Password visibility toggle ──────────────────────────────────────
    document.querySelectorAll('.md-visibility-toggle').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var input = this.parentElement.querySelector('.md-field__input');
        var icon = this.querySelector('.material-symbols-outlined');
        if (input.type === 'password') {
          input.type = 'text';
          icon.textContent = 'visibility_off';
        } else {
          input.type = 'password';
          icon.textContent = 'visibility';
        }
      });
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
      if (pw.length >= 8) score++;
      if (pw.length >= 12) score++;
      if (/[A-Z]/.test(pw) && /[a-z]/.test(pw)) score++;
      if (/[0-9]/.test(pw)) score++;
      if (/[^A-Za-z0-9]/.test(pw)) score++;
      return Math.min(4, score);
    }

    newPassEl.addEventListener('input', function () {
      var s = calcStrength(this.value);
      strengthFill.style.width = (s / 4 * 100) + '%';
      strengthFill.style.backgroundColor = STRENGTH_COLORS[s];
      strengthLabel.textContent = STRENGTH_LABELS[s];
      strengthLabel.style.color = STRENGTH_COLORS[s];
      strengthFill.setAttribute('aria-valuenow', s);

      // Update match indicator
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
    % alerts = get('alerts', [])
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

      // Auto-dismiss after 6 seconds
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
