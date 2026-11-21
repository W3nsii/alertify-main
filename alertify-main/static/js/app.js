/* ALERTIFY — shared front-end behaviour */
(function () {
  'use strict';
  var csrf = (document.querySelector('meta[name="csrf-token"]') || {}).content || '';
  window.ALERTIFY = window.ALERTIFY || {};
  ALERTIFY.csrf = csrf;

  ALERTIFY.postJSON = function (url, body) {
    return fetch(url, {
      method: 'POST', credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf },
      body: JSON.stringify(body || {})
    }).then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (data) {
        if (!r.ok) { var e = new Error(data.error || 'Something went wrong. Please try again.'); e.data = data; throw e; }
        return data;
      });
    });
  };

  ALERTIFY.toast = function (msg, kind) {
    var root = document.getElementById('toast-root');
    if (!root) return;
    var t = document.createElement('div');
    t.className = 'toast toast-' + (kind || 'info');
    t.textContent = msg;
    root.appendChild(t);
    setTimeout(function () { t.classList.add('out'); }, 3200);
    setTimeout(function () { t.remove(); }, 3700);
  };

  ALERTIFY.esc = function (s) {
    var d = document.createElement('div'); d.textContent = s == null ? '' : String(s); return d.innerHTML;
  };

  // --- sidebar (mobile)
  var sidebar = document.getElementById('sidebar'), scrim = document.getElementById('scrim'),
      menuBtn = document.getElementById('menu-btn');
  function setNav(open) {
    if (!sidebar) return;
    sidebar.classList.toggle('open', open);
    if (scrim) scrim.hidden = !open;
    if (menuBtn) menuBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
    document.body.classList.toggle('nav-open', open);
  }
  if (menuBtn) menuBtn.addEventListener('click', function () { setNav(!sidebar.classList.contains('open')); });
  if (scrim) scrim.addEventListener('click', function () { setNav(false); });

  // --- dropdowns
  document.addEventListener('click', function (e) {
    var trigger = e.target.closest('[data-dropdown]');
    document.querySelectorAll('.menu.open').forEach(function (m) {
      if (!trigger || m.id !== trigger.dataset.dropdown) m.classList.remove('open');
    });
    if (trigger) {
      e.preventDefault();
      document.getElementById(trigger.dataset.dropdown).classList.toggle('open');
    } else if (!e.target.closest('.menu')) {
      document.querySelectorAll('.menu.open').forEach(function (m) { m.classList.remove('open'); });
    }
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      document.querySelectorAll('.menu.open').forEach(function (m) { m.classList.remove('open'); });
      setNav(false);
    }
  });

  // --- mark notifications read
  var markBtn = document.getElementById('mark-read');
  if (markBtn) markBtn.addEventListener('click', function () {
    ALERTIFY.postJSON('/notifications/read-all').then(function () {
      document.querySelectorAll('.notif-item.unread').forEach(function (n) { n.classList.remove('unread'); });
      var dc = document.querySelector('.dot-count'); if (dc) dc.remove();
      markBtn.remove();
    }).catch(function (err) { ALERTIFY.toast(err.message, 'error'); });
  });

  // --- confirm dialogs
  document.addEventListener('submit', function (e) {
    var f = e.target;
    if (f.dataset.confirm && !window.confirm(f.dataset.confirm)) { e.preventDefault(); return; }
    if (f.hasAttribute('data-logout')) {
      try { localStorage.removeItem('alertify_last_report'); } catch (x) {}
      if (navigator.serviceWorker && navigator.serviceWorker.controller) {
        navigator.serviceWorker.controller.postMessage({ type: 'clear-private' });
      }
    }
    if (f.hasAttribute('data-validate') && !f.checkValidity()) {
      e.preventDefault();
      var bad = f.querySelector(':invalid');
      if (bad) { bad.focus(); bad.reportValidity && bad.reportValidity(); }
    }
  }, true);

  // --- auto-dismiss success flashes
  setTimeout(function () {
    document.querySelectorAll('.flash-success, .flash-info').forEach(function (f) { f.classList.add('fade'); });
  }, 6000);

  // --- online / offline indicator
  var pill = document.getElementById('net-pill');
  function net() { if (pill) pill.hidden = navigator.onLine; }
  window.addEventListener('online', net); window.addEventListener('offline', net); net();

  // --- cache contacts for offline use
  if (navigator.onLine) {
    fetch('/api/contacts', { credentials: 'same-origin' }).then(function (r) { return r.json(); })
      .then(function (d) { try { localStorage.setItem('alertify_contacts', JSON.stringify(d.contacts)); } catch (e) {} })
      .catch(function () {});
  }

  // --- show / hide password: adds an eye button to every password field on the page.
  var EYE = '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/></svg>';
  var EYE_OFF = '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M17.94 17.94A10.1 10.1 0 0 1 12 19c-6.5 0-10-7-10-7a18.4 18.4 0 0 1 5.06-5.94M9.9 4.24A9.1 9.1 0 0 1 12 4c6.5 0 10 7 10 7a18.5 18.5 0 0 1-2.16 3.19M14.12 14.12a3 3 0 1 1-4.24-4.24"/><path d="M2 2l20 20"/></svg>';

  function addPasswordToggle(input) {
    var wrap = document.createElement('span');
    wrap.className = 'pw-wrap';
    input.parentNode.insertBefore(wrap, input);
    wrap.appendChild(input);

    var btn = document.createElement('button');
    btn.type = 'button';                       // never submits the form
    btn.className = 'pw-toggle';
    wrap.appendChild(btn);

    function update(shown) {
      input.type = shown ? 'text' : 'password';
      btn.innerHTML = shown ? EYE_OFF : EYE;
      btn.setAttribute('aria-label', shown ? 'Hide password' : 'Show password');
      btn.setAttribute('aria-pressed', shown ? 'true' : 'false');
    }
    btn.addEventListener('click', function (e) {
      e.preventDefault();                      // keep the surrounding <label> from refocusing oddly
      var pos = input.selectionStart;
      update(input.type === 'password');
      input.focus();
      if (pos != null) input.setSelectionRange(pos, pos);  // keep the cursor where it was
    });
    // Hide the password again before the form is sent, so the browser does not offer
    // to save it as plain text history.
    if (input.form) input.form.addEventListener('submit', function () { update(false); });
    update(false);
  }
  document.querySelectorAll('input[type="password"]').forEach(addPasswordToggle);

  // --- base map shared by every Leaflet map in the app (one place to change it).
  // OpenStreetMap's tile servers require a Referer header; app.py sends the site
  // origin via "Referrer-Policy: strict-origin-when-cross-origin" so tiles load.
  ALERTIFY.addBaseMap = function (map) {
    // Redraw when the map's box changes size (phone rotation, layout shifts, fonts
    // loading); otherwise Leaflet leaves grey, tile-less strips at the edges.
    if ('ResizeObserver' in window) {
      new ResizeObserver(function () { map.invalidateSize(); }).observe(map.getContainer());
    }
    return L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
  };

  // --- service worker
  if ('serviceWorker' in navigator && location.protocol !== 'file:') {
    window.addEventListener('load', function () { navigator.serviceWorker.register('/sw.js', { scope: '/' }).catch(function () {}); });
  }
})();
