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

  <link rel="stylesheet"
        href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0">
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
    <header class="md-top-app-bar">
      <div class="md-top-app-bar__row">
        <span class="material-symbols-outlined md-top-app-bar__icon">{{ get('page_icon', 'lock') }}</span>
        <span class="md-top-app-bar__title">{{ page_title }}</span>
        <div class="md-top-app-bar__actions">
          % if get('admin_session'):
          <a href="{{ base_path }}/admin" class="md-top-app-bar__admin-link" title="Admin Panel">
            <span class="material-symbols-outlined">admin_panel_settings</span>
          </a>
          <a href="{{ base_path }}/logout" class="md-top-app-bar__admin-link" title="Logout">
            <span class="material-symbols-outlined">logout</span>
          </a>
          % end
        </div>
      </div>
    </header>

    <main class="md-main md-main--welcome">
      <div class="md-welcome-card">
        <div class="md-welcome-card__logo">
          <span class="material-symbols-outlined">{{ get('page_icon', 'lock') }}</span>
        </div>

        <h1 class="md-welcome-card__title">{{ page_title }}</h1>

        <p class="md-welcome-card__text">
          Use the options below to manage your account or administer the directory.
        </p>

        <div class="md-welcome-card__actions">
          <a href="{{ base_path }}/change-password" class="md-welcome-button">
            <span class="material-symbols-outlined md-welcome-button__icon">lock_reset</span>
            <span class="md-welcome-button__label">Change password</span>
            <span class="md-welcome-button__hint">Update your LDAP password</span>
            <span class="material-symbols-outlined md-welcome-button__arrow">arrow_forward</span>
          </a>

          <a href="{{ base_path }}/login" class="md-welcome-button">
            <span class="material-symbols-outlined md-welcome-button__icon">admin_panel_settings</span>
            <span class="md-welcome-button__label">Administration</span>
            <span class="md-welcome-button__hint">Manage users and groups</span>
            <span class="material-symbols-outlined md-welcome-button__arrow">arrow_forward</span>
          </a>
        </div>
      </div>
    </main>
  </div>
</body>
</html>
