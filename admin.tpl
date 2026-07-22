<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex, nofollow">
  <meta name="color-scheme" content="light dark">

  <title>{{ page_title }} — Admin</title>

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
        <span class="md-top-app-bar__title">Admin Panel</span>
        <div class="md-top-app-bar__actions">
          <span class="md-top-app-bar__user">{{ admin_session['user'] }}</span>
          <a href="/logout" class="md-top-app-bar__admin-link" title="Logout">
            <span class="material-symbols-outlined">logout</span>
          </a>
        </div>
      </div>
    </header>

    <main class="md-main md-main--admin">
      <div class="md-card md-card--elevated md-card--admin">
        <!-- Tab bar -->
        <nav class="md-tabs">
          <button class="md-tab md-tab--active" data-tab="tab-password">Change Password</button>
          <button class="md-tab" data-tab="tab-create-user">Create User</button>
          <button class="md-tab" data-tab="tab-groups">Groups</button>
        </nav>

        <div class="md-card__content">
          <!-- Tab: Change Password -->
          <div class="md-tab-panel md-tab-panel--active" id="tab-password">
            <div class="md-admin-hint">
              <span class="material-symbols-outlined">info</span>
              <span>Change any user's password. Leave target username empty to change your own.</span>
            </div>
            <form method="post" action="/admin/change-password" class="md-admin-form" novalidate>
              <input type="hidden" name="csrf_token" value="{{ csrf_token }}">

              <div class="md-field">
                <span class="md-field__icon material-symbols-outlined">person</span>
                <input class="md-field__input" name="target-user" type="text"
                       placeholder=" " aria-label="Target username (optional)">
                <span class="md-field__label">Target username (optional)</span>
                <span class="md-field__outline"></span>
              </div>

              <div class="md-field">
                <span class="md-field__icon material-symbols-outlined">lock</span>
                <input class="md-field__input md-field__input--password" name="new-password" type="password"
                       minlength="{{ password_policy['min_length'] }}" required
                       placeholder=" " aria-label="New password">
                <span class="md-field__label">New password</span>
                <span class="md-field__outline"></span>
                <button type="button" class="md-field__trailing-icon md-visibility-toggle"
                        aria-label="Show password">
                  <span class="material-symbols-outlined">visibility</span>
                </button>
              </div>

              <div class="md-field">
                <span class="md-field__icon material-symbols-outlined">lock_reset</span>
                <input class="md-field__input md-field__input--password" name="confirm-password" type="password"
                       minlength="{{ password_policy['min_length'] }}" required
                       placeholder=" " aria-label="Confirm new password">
                <span class="md-field__label">Confirm new password</span>
                <span class="md-field__outline"></span>
                <button type="button" class="md-field__trailing-icon md-visibility-toggle"
                        aria-label="Show password">
                  <span class="material-symbols-outlined">visibility</span>
                </button>
              </div>

              <div class="md-field">
                <span class="md-field__icon material-symbols-outlined">shield_person</span>
                <input class="md-field__input md-field__input--password" name="admin-password" type="password"
                       required placeholder=" " aria-label="Your admin password">
                <span class="md-field__label">Your admin password</span>
                <span class="md-field__outline"></span>
              </div>

              <div class="md-helper-text">
                <span class="material-symbols-outlined md-helper-text__icon">info</span>
                <span>{{! password_policy['description'] }}</span>
              </div>

              <button type="submit" class="md-filled-button">
                <span class="material-symbols-outlined">check_circle</span>
                <span>Update password</span>
              </button>
            </form>
          </div>

          <!-- Tab: Create User -->
          <div class="md-tab-panel" id="tab-create-user">
            <div class="md-admin-hint">
              <span class="material-symbols-outlined">info</span>
              <span>Create a new LDAP user account. All fields except email are required.</span>
            </div>
            <form method="post" action="/admin/create-user" class="md-admin-form" novalidate>
              <input type="hidden" name="csrf_token" value="{{ csrf_token }}">

              <div class="md-field">
                <span class="md-field__icon material-symbols-outlined">person</span>
                <input class="md-field__input" name="uid" type="text" required
                       placeholder=" " aria-label="Username">
                <span class="md-field__label">Username (uid)</span>
                <span class="md-field__outline"></span>
              </div>

              <div class="md-field">
                <span class="md-field__icon material-symbols-outlined">badge</span>
                <input class="md-field__input" name="cn" type="text" required
                       placeholder=" " aria-label="Full name">
                <span class="md-field__label">Full name (cn)</span>
                <span class="md-field__outline"></span>
              </div>

              <div class="md-field">
                <span class="md-field__icon material-symbols-outlined">badge</span>
                <input class="md-field__input" name="sn" type="text" required
                       placeholder=" " aria-label="Last name">
                <span class="md-field__label">Last name (sn)</span>
                <span class="md-field__outline"></span>
              </div>

              <div class="md-field">
                <span class="md-field__icon material-symbols-outlined">mail</span>
                <input class="md-field__input" name="mail" type="email"
                       placeholder=" " aria-label="Email">
                <span class="md-field__label">Email (optional)</span>
                <span class="md-field__outline"></span>
              </div>

              <div class="md-field">
                <span class="md-field__icon material-symbols-outlined">lock</span>
                <input class="md-field__input md-field__input--password" name="user-password" type="password"
                       required placeholder=" " aria-label="Password">
                <span class="md-field__label">Password</span>
                <span class="md-field__outline"></span>
                <button type="button" class="md-field__trailing-icon md-visibility-toggle"
                        aria-label="Show password">
                  <span class="material-symbols-outlined">visibility</span>
                </button>
              </div>

              <div class="md-field">
                <span class="md-field__icon material-symbols-outlined">shield_person</span>
                <input class="md-field__input md-field__input--password" name="admin-password" type="password"
                       required placeholder=" " aria-label="Your admin password">
                <span class="md-field__label">Your admin password</span>
                <span class="md-field__outline"></span>
              </div>

              <button type="submit" class="md-filled-button">
                <span class="material-symbols-outlined">person_add</span>
                <span>Create user</span>
              </button>
            </form>
          </div>

          <!-- Tab: Groups -->
          <div class="md-tab-panel" id="tab-groups">
            <div class="md-groups-layout">
              <div class="md-groups-left">
                <h3 class="md-groups__heading">Groups</h3>
                <button type="button" class="md-outlined-button" id="btn-refresh-groups">
                  <span class="material-symbols-outlined">refresh</span>
                  <span>Refresh</span>
                </button>
                <div class="md-groups-list" id="groups-list">
                  <p class="md-groups__empty">Click Refresh and enter your admin password to load groups.</p>
                </div>
              </div>

              <div class="md-groups-right">
                <div class="md-groups__section">
                  <h3 class="md-groups__heading">Add / Remove Member</h3>
                  <form method="post" action="/admin/modify-group" class="md-admin-form" novalidate>
                    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">

                    <div class="md-field">
                      <span class="md-field__icon material-symbols-outlined">group</span>
                      <input class="md-field__input" name="group-dn" type="text" required
                             placeholder=" " aria-label="Group DN">
                      <span class="md-field__label">Group DN</span>
                      <span class="md-field__outline"></span>
                    </div>

                    <div class="md-field">
                      <span class="md-field__icon material-symbols-outlined">person</span>
                      <input class="md-field__input" name="member-uid" type="text" required
                             placeholder=" " aria-label="Member username">
                      <span class="md-field__label">Member username</span>
                      <span class="md-field__outline"></span>
                    </div>

                    <div class="md-field">
                      <span class="md-field__icon material-symbols-outlined">shield_person</span>
                      <input class="md-field__input md-field__input--password" name="admin-password"
                             type="password" required placeholder=" "
                             aria-label="Your admin password">
                      <span class="md-field__label">Your admin password</span>
                      <span class="md-field__outline"></span>
                    </div>

                    <input type="hidden" name="action" value="add" id="group-action">

                    <div class="md-groups__actions">
                      <button type="submit" class="md-filled-button" onclick="document.getElementById('group-action').value='add'">
                        <span class="material-symbols-outlined">person_add</span>
                        <span>Add to group</span>
                      </button>
                      <button type="submit" class="md-outlined-button md-outlined-button--danger"
                              onclick="document.getElementById('group-action').value='remove'">
                        <span class="material-symbols-outlined">person_remove</span>
                        <span>Remove from group</span>
                      </button>
                    </div>
                  </form>
                </div>

                <div class="md-groups__section">
                  <h3 class="md-groups__heading">Create Group</h3>
                  <form method="post" action="/admin/create-group" class="md-admin-form" novalidate>
                    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">

                    <div class="md-field">
                      <span class="md-field__icon material-symbols-outlined">group_add</span>
                      <input class="md-field__input" name="group-name" type="text" required
                             placeholder=" " aria-label="Group name">
                      <span class="md-field__label">Group name (cn)</span>
                      <span class="md-field__outline"></span>
                    </div>

                    <div class="md-field">
                      <span class="md-field__icon material-symbols-outlined">shield_person</span>
                      <input class="md-field__input md-field__input--password" name="admin-password"
                             type="password" required placeholder=" "
                             aria-label="Your admin password">
                      <span class="md-field__label">Your admin password</span>
                      <span class="md-field__outline"></span>
                    </div>

                    <button type="submit" class="md-filled-button">
                      <span class="material-symbols-outlined">group_add</span>
                      <span>Create group</span>
                    </button>
                  </form>
                </div>
              </div>
            </div>
          </div>
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

    // ── Tab switching ──────────────────────────────────────────────────
    var tabs = document.querySelectorAll('.md-tab');
    var panels = document.querySelectorAll('.md-tab-panel');

    tabs.forEach(function (tab) {
      tab.addEventListener('click', function () {
        var target = this.getAttribute('data-tab');
        tabs.forEach(function (t) { t.classList.remove('md-tab--active'); });
        panels.forEach(function (p) { p.classList.remove('md-tab-panel--active'); });
        this.classList.add('md-tab--active');
        var panel = document.getElementById(target);
        if (panel) panel.classList.add('md-tab-panel--active');
      });
    });

    // ── Password visibility toggle ──────────────────────────────────────
    document.querySelectorAll('.md-visibility-toggle').forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        var field = this.closest('.md-field');
        var input = field.querySelector('.md-field__input');
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

    // ── Field click to focus ────────────────────────────────────────────
    document.querySelectorAll('.md-field').forEach(function (field) {
      field.addEventListener('click', function (e) {
        if (e.target.closest('button, a, [role="button"]')) return;
        var input = this.querySelector('.md-field__input');
        if (input) input.focus();
      });
    });

    // ── Refresh groups list ─────────────────────────────────────────────
    document.getElementById('btn-refresh-groups').addEventListener('click', function () {
      var pwd = prompt('Enter your admin password to load groups:');
      if (!pwd) return;

      var list = document.getElementById('groups-list');
      list.innerHTML = '<p class="md-groups__loading">Loading&hellip;</p>';

      fetch('/admin/groups?admin-password=' + encodeURIComponent(pwd))
        .then(function (r) {
          if (!r.ok) return r.json().then(function (e) { throw new Error(e.error); });
          return r.json();
        })
        .then(function (groups) {
          if (!groups.length) {
            list.innerHTML = '<p class="md-groups__empty">No groups found.</p>';
            return;
          }
          var html = '';
          groups.forEach(function (g) {
            var memberCount = Array.isArray(g.members) ? g.members.length : 0;
            html += '<div class="md-group-item" title="' + g.dn.replace(/&/g,'&amp;').replace(/</g,'&lt;') + '">';
            html += '<span class="md-group-item__icon material-symbols-outlined">group</span>';
            html += '<div class="md-group-item__info">';
            html += '<span class="md-group-item__name">' + g.cn.replace(/&/g,'&amp;').replace(/</g,'&lt;') + '</span>';
            html += '<span class="md-group-item__dn">' + g.dn.replace(/&/g,'&amp;').replace(/</g,'&lt;') + '</span>';
            html += '<span class="md-group-item__count">' + memberCount + ' member(s)</span>';
            html += '</div></div>';
          });
          list.innerHTML = html;
        })
        .catch(function (err) {
          list.innerHTML = '<p class="md-groups__error">Error: ' + (err.message || 'Failed to load groups').replace(/&/g,'&amp;').replace(/</g,'&lt;') + '</p>';
        });
    });

    // ── Snackbar ────────────────────────────────────────────────────────
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
  })();
  </script>
</body>
</html>
