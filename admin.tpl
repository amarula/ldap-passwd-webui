<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex, nofollow">
  <meta name="theme-color" content="{{ get('primary_color', '#2e7d32') }}">
  <meta name="color-scheme" content="light dark">

  <title>Admin Panel</title>

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
        <span class="material-symbols-outlined md-top-app-bar__icon">admin_panel_settings</span>
        <span class="md-top-app-bar__title">Admin Panel</span>
        <div class="md-top-app-bar__actions">
          <span class="md-top-app-bar__user">{{ admin_session['user'] }}</span>
          <a href="{{ base_path }}/logout" class="md-top-app-bar__admin-link" title="Logout">
            <span class="material-symbols-outlined">logout</span>
          </a>
        </div>
      </div>
    </header>

    <main class="md-main md-main--admin">
      <div class="md-card md-card--elevated md-card--admin">
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
            <form method="post" action="{{ base_path }}/admin/change-password" class="md-admin-form" novalidate>
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
                <button type="button" class="md-field__trailing-icon md-visibility-toggle" aria-label="Show password">
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
                <button type="button" class="md-field__trailing-icon md-visibility-toggle" aria-label="Show password">
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
              <span>Create a new LDAP user account and optionally add them to groups.</span>
            </div>
            <form method="post" action="{{ base_path }}/admin/create-user" id="create-user-form" class="md-admin-form" novalidate>
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
                <button type="button" class="md-field__trailing-icon md-visibility-toggle" aria-label="Show password">
                  <span class="material-symbols-outlined">visibility</span>
                </button>
              </div>

              <!-- Group assignment -->
              <div class="md-groups-checklist">
                <div class="md-groups-checklist__header">
                  <span class="material-symbols-outlined">groups</span>
                  <span>Add to groups (optional)</span>
                  <button type="button" class="md-outlined-button md-outlined-button--small" id="btn-load-groups">
                    <span class="material-symbols-outlined">refresh</span>
                    <span>Load groups</span>
                  </button>
                </div>
                <div class="md-groups-checklist__list" id="create-user-groups">
                  <p class="md-groups__empty">Click "Load groups" to see available groups.</p>
                </div>
                <input type="hidden" name="groups" id="selected-groups" value="">
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
                <div class="md-groups-toolbar">
                  <button type="button" class="md-outlined-button" id="btn-refresh-groups">
                    <span class="material-symbols-outlined">refresh</span>
                    <span>Refresh</span>
                  </button>
                </div>
                <div class="md-groups-list" id="groups-list">
                  <p class="md-groups__empty">Loading groups&hellip;</p>
                </div>
                <div class="md-groups-detail" id="group-detail" style="display:none">
                  <h4 class="md-groups__heading" id="detail-group-name"></h4>
                  <p class="md-groups__detail-dn" id="detail-group-dn"></p>
                  <div class="md-groups-detail__members" id="detail-group-members"></div>
                </div>
              </div>

              <div class="md-groups-right">
                <div class="md-groups__section">
                  <h3 class="md-groups__heading">User Group Membership</h3>
                  <div class="md-groups-toolbar">
                    <div class="md-field md-field--compact">
                      <input class="md-field__input" id="lookup-username" type="text"
                             placeholder=" " aria-label="Username to look up">
                      <span class="md-field__label">Username</span>
                      <span class="md-field__outline"></span>
                    </div>
                    <button type="button" class="md-outlined-button" id="btn-lookup-user">
                      <span class="material-symbols-outlined">search</span>
                      <span>Look up</span>
                    </button>
                  </div>
                  <div class="md-groups-list" id="user-groups-list">
                    <p class="md-groups__empty">Enter a username and click Look up to see their groups.</p>
                  </div>
                </div>

                <div class="md-groups__section">
                  <h3 class="md-groups__heading">Add / Remove Member</h3>
                  <form method="post" action="{{ base_path }}/admin/modify-group" class="md-admin-form" novalidate>
                    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">

                    <div class="md-field">
                      <span class="md-field__icon material-symbols-outlined">group</span>
                      <select class="md-field__input md-field__select" name="group-dn" id="modify-group-select" required
                              aria-label="Select group">
                        <option value="">Select a group...</option>
                      </select>
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
                  <form method="post" action="{{ base_path }}/admin/create-group" class="md-admin-form" novalidate>
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
    document.querySelectorAll('.md-tab').forEach(function (tab) {
      tab.addEventListener('click', function () {
        var target = this.getAttribute('data-tab');
        document.querySelectorAll('.md-tab').forEach(function (t) { t.classList.remove('md-tab--active'); });
        document.querySelectorAll('.md-tab-panel').forEach(function (p) { p.classList.remove('md-tab-panel--active'); });
        this.classList.add('md-tab--active');
        var panel = document.getElementById(target);
        if (panel) panel.classList.add('md-tab-panel--active');

        // Preload groups when switching to Create User or Groups tabs.
        if (target === 'tab-create-user') loadCreateUserGroups();
        if (target === 'tab-groups') loadGroupsTab();
      });
    });

    // ── Load groups tab content (debounced) ──────────────────────────
    var groupsTabLoaded = false;
    function loadGroupsTab() {
      if (groupsTabLoaded) return;
      groupsTabLoaded = true;
      refreshGroupsForTab();
    }

    // ── Password visibility toggle ──────────────────────────────────────
    document.querySelectorAll('.md-visibility-toggle').forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        var input = this.closest('.md-field').querySelector('.md-field__input');
        var icon = this.querySelector('.material-symbols-outlined');
        if (input.type === 'password') { input.type = 'text'; icon.textContent = 'visibility_off'; }
        else { input.type = 'password'; icon.textContent = 'visibility'; }
      });
    });

    // ── Field click to focus ────────────────────────────────────────────
    document.querySelectorAll('.md-field').forEach(function (field) {
      field.addEventListener('click', function (e) {
        if (e.target.closest('button, a, select, [role="button"]')) return;
        var input = this.querySelector('input');
        if (input) input.focus();
      });
    });

    // ── Escape HTML ─────────────────────────────────────────────────────
    function esc(s) {
      return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    }

    // ── Fetch groups JSON ───────────────────────────────────────────────
    function fetchGroups() {
      return fetch('{{ base_path }}/admin/groups')
        .then(function (r) {
          if (!r.ok) return r.json().then(function (e) { throw new Error(e.error); });
          return r.json();
        });
    }

    // ── Populate group select ───────────────────────────────────────────
    function populateGroupSelect(groups) {
      var sel = document.getElementById('modify-group-select');
      sel.innerHTML = '<option value="">Select a group...</option>';
      groups.forEach(function (g) {
        sel.innerHTML += '<option value="' + esc(g.dn) + '">' + esc(g.cn) + '</option>';
      });
    }

    // ── Render groups list ─────────────────────────────────────────────
    function renderGroupList(container, groups, clickHandler) {
      if (!groups.length) {
        container.innerHTML = '<p class="md-groups__empty">No groups found.</p>';
        return;
      }
      var html = '';
      groups.forEach(function (g, i) {
        var cnt = Array.isArray(g.members) ? g.members.length : 0;
        html += '<div class="md-group-item" data-dn="' + esc(g.dn) + '" data-cn="' + esc(g.cn) + '">';
        html += '<span class="md-group-item__icon material-symbols-outlined">group</span>';
        html += '<div class="md-group-item__info">';
        html += '<span class="md-group-item__name">' + esc(g.cn) + '</span>';
        html += '<span class="md-group-item__dn">' + esc(g.dn) + '</span>';
        html += '<span class="md-group-item__count">' + cnt + ' member(s)</span>';
        html += '</div></div>';
      });
      container.innerHTML = html;
      if (clickHandler) {
        container.querySelectorAll('.md-group-item').forEach(function (item) {
          item.addEventListener('click', function () { clickHandler(this); });
        });
      }
    }

    // ══════════════════════════════════════════════════════════════════
    // CREATE USER TAB — group checkboxes (preloaded)
    // ══════════════════════════════════════════════════════════════════

    var createUserGroupsLoaded = false;

    function renderCreateUserGroups(groups) {
      var container = document.getElementById('create-user-groups');
      if (!groups.length) {
        container.innerHTML = '<p class="md-groups__empty">No groups available.</p>';
        return;
      }
      var html = '';
      groups.forEach(function (g) {
        html += '<label class="md-checkbox">';
        html += '<input type="checkbox" name="create-user-group" value="' + esc(g.dn) + '">';
        html += '<span class="md-checkbox__label">' + esc(g.cn) + '</span>';
        html += '<span class="md-checkbox__dn">' + esc(g.dn) + '</span>';
        html += '</label>';
      });
      container.innerHTML = html;
      createUserGroupsLoaded = true;
    }

    function loadCreateUserGroups() {
      if (createUserGroupsLoaded) return;
      fetchGroups().then(function (groups) {
        renderCreateUserGroups(groups);
      }).catch(function (err) {
        document.getElementById('create-user-groups').innerHTML =
          '<p class="md-groups__error">' + esc(err.message || 'Error') + '</p>';
      });
    }

    // Refresh button as fallback.
    document.getElementById('btn-load-groups').addEventListener('click', function () {
      createUserGroupsLoaded = false;
      loadCreateUserGroups();
    });

    // Collect selected group DNs before form submit
    document.getElementById('create-user-form').addEventListener('submit', function () {
      var checked = this.querySelectorAll('input[name="create-user-group"]:checked');
      var dns = [];
      checked.forEach(function (cb) { dns.push(cb.value); });
      document.getElementById('selected-groups').value = dns.join('\n');
    });

    // ══════════════════════════════════════════════════════════════════
    // GROUPS TAB — shared refresh
    // ══════════════════════════════════════════════════════════════════

    function refreshGroupsForTab() {
      fetchGroups().then(function (groups) {
        // Populate left panel list
        var list = document.getElementById('groups-list');
        renderGroupList(list, groups, function (item) {
          // Show group detail
          var dn = item.getAttribute('data-dn');
          var cn = item.getAttribute('data-cn');
          document.getElementById('detail-group-name').textContent = cn;
          document.getElementById('detail-group-dn').textContent = dn;
          var g = groups.find(function (x) { return x.dn === dn; });
          var membersDiv = document.getElementById('detail-group-members');
          if (g) {
            var mHtml = '<ul class="md-members-list">';
            (g.members || []).forEach(function (m) {
              var name = m.match(/^cn=([^,]+)/);
              var display = name ? name[1] : m;
              mHtml += '<li>' + esc(display) + '</li>';
            });
            mHtml += '</ul>';
            membersDiv.innerHTML = mHtml;
          } else {
            membersDiv.innerHTML = '<p class="md-groups__empty">Select a group to see members.</p>';
          }
          document.getElementById('group-detail').style.display = 'block';
        });

        // Populate the modify-group select
        populateGroupSelect(groups);
      }).catch(function (err) {
        document.getElementById('groups-list').innerHTML =
          '<p class="md-groups__error">' + esc(err.message || 'Error') + '</p>';
      });
    }

    document.getElementById('btn-refresh-groups').addEventListener('click', refreshGroupsForTab);

    // ══════════════════════════════════════════════════════════════════
    // GROUPS TAB — user lookup
    // ══════════════════════════════════════════════════════════════════

    var lookupInput = document.getElementById('lookup-username');
    var lookupTimer = null;

    function lookupUserGroups(uid) {
      fetch('{{ base_path }}/admin/user-groups?username=' + encodeURIComponent(uid))
        .then(function (r) {
        if (!r.ok) return r.json().then(function (e) { throw new Error(e.error); });
        return r.json();
      }).then(function (data) {
        var container = document.getElementById('user-groups-list');
        if (!data.groups || !data.groups.length) {
          container.innerHTML = '<p class="md-groups__empty">User <strong>' + esc(uid) +
            '</strong> is not a member of any group.</p>';
          return;
        }
        var html = '<p class="md-groups__summary">' + esc(uid) + ' belongs to ' +
          data.groups.length + ' group(s):</p>';
        data.groups.forEach(function (g) {
          html += '<div class="md-group-item">';
          html += '<span class="md-group-item__icon material-symbols-outlined">group</span>';
          html += '<div class="md-group-item__info">';
          html += '<span class="md-group-item__name">' + esc(g.cn) + '</span>';
          html += '<span class="md-group-item__dn">' + esc(g.dn) + '</span>';
          html += '</div></div>';
        });
        container.innerHTML = html;
      }).catch(function (err) {
        document.getElementById('user-groups-list').innerHTML =
          '<p class="md-groups__error">' + esc(err.message || 'Error') + '</p>';
      });
    }

    document.getElementById('btn-lookup-user').addEventListener('click', function () {
      var val = lookupInput.value.trim();
      if (!val) return;
      // If the user typed a uid (no spaces, short), use it directly.
      // Otherwise search by name and pick the first match.
      if (val.indexOf(' ') === -1 && val.indexOf('@') === -1 && val.length < 20) {
        lookupUserGroups(val);
      } else {
        fetch('{{ base_path }}/admin/user-search?q=' + encodeURIComponent(val))
          .then(function (r) { return r.json(); })
          .then(function (data) {
            if (!data.users || !data.users.length) {
              document.getElementById('user-groups-list').innerHTML =
                '<p class="md-groups__empty">No users found matching <strong>' + esc(val) + '</strong>.</p>';
              return;
            }
            // Show all matches and pick first
            lookupUserGroups(data.users[0].uid);
          });
      }
    });

    // Autocomplete as user types
    lookupInput.addEventListener('input', function () {
      clearTimeout(lookupTimer);
      var val = this.value.trim();
      if (val.length < 2) return;
      lookupTimer = setTimeout(function () {
        fetch('{{ base_path }}/admin/user-search?q=' + encodeURIComponent(val))
          .then(function (r) { return r.json(); })
          .then(function (data) {
            var listId = 'lookup-suggestions';
            var old = document.getElementById(listId);
            if (old) old.remove();
            if (!data.users || !data.users.length) return;
            var dl = document.createElement('datalist');
            dl.id = listId;
            data.users.forEach(function (u) {
              var opt = document.createElement('option');
              opt.value = u.uid;
              opt.textContent = u.cn + ' (' + u.uid + ') ' + (u.mail || '');
              dl.appendChild(opt);
            });
            lookupInput.setAttribute('list', listId);
            lookupInput.parentNode.appendChild(dl);
          });
      }, 300);
    });

    // ══════════════════════════════════════════════════════════════════
    // ── Preload groups for the active tab on page load ──────────────
    // ══════════════════════════════════════════════════════════════════
    loadCreateUserGroups();
    loadGroupsTab();

    // ══════════════════════════════════════════════════════════════════
    // Snackbar
    // ══════════════════════════════════════════════════════════════════

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
