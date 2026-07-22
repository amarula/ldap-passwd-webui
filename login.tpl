<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex, nofollow">
  <meta name="color-scheme" content="light dark">

  <title>{{ page_title }} — Admin Login</title>

  <link rel="stylesheet"
        href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0">
  <link rel="stylesheet"
        href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap">
  <link rel="stylesheet" href="{{ url('static', filename='style.css') }}">
</head>

<body>
  <div class="app-layout">
    <header class="md-top-app-bar">
      <div class="md-top-app-bar__row">
        <span class="material-symbols-outlined md-top-app-bar__icon">admin_panel_settings</span>
        <span class="md-top-app-bar__title">Admin Login</span>
        <a href="/" class="md-top-app-bar__admin-link" title="Back to password change">
          <span class="material-symbols-outlined">lock</span>
        </a>
      </div>
    </header>

    <main class="md-main">
      <div class="md-card md-card--elevated">
        <div class="md-card__content">
          <form method="post" id="login-form" novalidate>
            <input type="hidden" name="csrf_token" value="{{ csrf_token }}">

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

            <div class="md-field">
              <span class="md-field__icon material-symbols-outlined">lock</span>
              <input class="md-field__input md-field__input--password"
                     id="password"
                     name="password"
                     type="password"
                     required
                     autocomplete="current-password"
                     placeholder=" "
                     aria-label="Password">
              <span class="md-field__label">Password</span>
              <span class="md-field__outline"></span>
              <button type="button"
                      class="md-field__trailing-icon md-visibility-toggle"
                      aria-label="Show password"
                      onclick="var i=this.parentElement.querySelector('.md-field__input'),s=this.querySelector('.material-symbols-outlined');if(i.type==='password'){i.type='text';s.textContent='visibility_off'}else{i.type='password';s.textContent='visibility'}">
                <span class="material-symbols-outlined">visibility</span>
              </button>
            </div>

            <button type="submit" class="md-filled-button" id="submit-btn">
              <span class="material-symbols-outlined">login</span>
              <span>Sign in</span>
            </button>
          </form>
        </div>
      </div>
    </main>

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

    document.getElementById('login-form').addEventListener('click', function (e) {
      var toggleBtn = e.target.closest('.md-visibility-toggle');
      if (toggleBtn) { return; }
      var field = e.target.closest('.md-field');
      if (field && !e.target.closest('button, a')) {
        var input = field.querySelector('.md-field__input');
        if (input) input.focus();
      }
    });

    % alerts = get('alerts', [])
    % if alerts:
    (function () {
      var type = '{{ alerts[0][0] }}';
      document.getElementById('snackbar-text').textContent = '{{! alerts[0][1] }}';
      var icon = document.getElementById('snackbar-icon');
      var snackbar = document.getElementById('snackbar');
      if (type === 'error') {
        icon.textContent = 'error';
        snackbar.className = 'md-snackbar md-snackbar--error md-snackbar--show';
      } else {
        icon.textContent = 'check_circle';
        snackbar.className = 'md-snackbar md-snackbar--success md-snackbar--show';
      }
      setTimeout(function () { snackbar.classList.remove('md-snackbar--show'); }, 6000);
      document.getElementById('snackbar-dismiss').addEventListener('click', function () {
        snackbar.classList.remove('md-snackbar--show');
      });
    })();
    % end

    document.getElementById('login-form').addEventListener('submit', function () {
      var btn = document.getElementById('submit-btn');
      btn.classList.add('md-filled-button--loading');
      btn.disabled = true;
    });
  })();
  </script>
</body>
</html>
