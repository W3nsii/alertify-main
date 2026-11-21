/* Dashboard: location capture + dynamic situation report */
(function () {
  'use strict';
  var cfg = window.ALERTIFY_DASH, esc = ALERTIFY.esc;
  var loc = { lat: null, lng: null, accuracy: null, source: null };
  var $ = function (id) { return document.getElementById(id); };
  var brgySel = $('barangay');

  // ---------------------------------------------------------------- map
  var map = null, userMarker = null, accCircle = null, pinMode = false;
  if (window.L) {
    map = L.map('mini-map', { zoomControl: true, attributionControl: true }).setView(cfg.center, 12);
    ALERTIFY.addBaseMap(map);
    var b = cfg.bounds;
    L.rectangle([[b.min_lat, b.min_lng], [b.max_lat, b.max_lng]], {
      color: '#C62828', weight: 1, dashArray: '4 6', fill: false, interactive: false
    }).addTo(map);
    map.on('click', function (e) {
      if (!pinMode) return;
      setLocation(e.latlng.lat, e.latlng.lng, null, 'map_pin');
      togglePin(false);
    });
  } else {
    $('mini-map').innerHTML = '<p class="map-fallback">Map unavailable offline. You can still select your barangay.</p>';
  }

  var userIcon = window.L && L.divIcon({ className: 'user-pin', html: '<span></span>', iconSize: [22, 22], iconAnchor: [11, 11] });

  function inCity(lat, lng) {
    var b = cfg.bounds;
    return lat >= b.min_lat && lat <= b.max_lat && lng >= b.min_lng && lng <= b.max_lng;
  }

  function setLocation(lat, lng, acc, source) {
    loc = { lat: lat, lng: lng, accuracy: acc, source: source };
    if (map) {
      if (userMarker) userMarker.setLatLng([lat, lng]);
      else userMarker = L.marker([lat, lng], { icon: userIcon, zIndexOffset: 1000 }).addTo(map);
      if (accCircle) { map.removeLayer(accCircle); accCircle = null; }
      if (acc) accCircle = L.circle([lat, lng], { radius: acc, color: '#C62828', weight: 1, fillOpacity: .08 }).addTo(map);
      map.setView([lat, lng], 15);
    }
    renderLoc();
  }

  function renderLoc() {
    var chip = $('loc-chip'), has = loc.lat !== null, brgy = brgySel.value;
    $('li-brgy').textContent = brgy || '—';
    $('btn-clear-loc').hidden = !has;
    if (has) {
      $('li-coords').textContent = loc.lat.toFixed(5) + ', ' + loc.lng.toFixed(5);
      $('li-acc').textContent = loc.source === 'gps'
        ? 'Device location' + (loc.accuracy ? ' · ±' + Math.round(loc.accuracy) + ' m' : '')
        : 'Pinned on map (manual)';
      var inside = inCity(loc.lat, loc.lng);
      $('li-status').innerHTML = inside ? 'Location set within Batangas City'
        : '<span class="warn-text">Outside Batangas City coverage</span>';
      chip.textContent = loc.source === 'gps' ? 'GPS shared' : 'Pinned';
      chip.className = 'chip ' + (inside ? 'chip-ok' : 'chip-warn');
    } else {
      $('li-coords').textContent = '—';
      $('li-acc').textContent = brgy ? 'Entered manually (barangay only)' : '—';
      $('li-status').textContent = brgy ? 'Barangay selected' : 'Not shared yet';
      chip.textContent = brgy ? 'Barangay only' : 'Not set';
      chip.className = 'chip ' + (brgy ? 'chip-ok' : '');
    }
  }

  // Use my location (explicit user action => browser permission prompt)
  $('btn-geo').addEventListener('click', function () {
    var btn = this;
    if (!navigator.geolocation) { ALERTIFY.toast('Location is not supported on this device. Pin your location or select a barangay.', 'error'); return; }
    btn.disabled = true; btn.classList.add('loading');
    $('li-status').textContent = 'Requesting permission…';
    navigator.geolocation.getCurrentPosition(function (pos) {
      btn.disabled = false; btn.classList.remove('loading');
      setLocation(pos.coords.latitude, pos.coords.longitude, pos.coords.accuracy, 'gps');
      if (!inCity(pos.coords.latitude, pos.coords.longitude)) {
        ALERTIFY.toast('Your location appears to be outside Batangas City. ALERTIFY covers Batangas City only.', 'error');
      } else {
        ALERTIFY.toast('Location shared.', 'success');
      }
    }, function (err) {
      btn.disabled = false; btn.classList.remove('loading');
      var msg = err.code === 1 ? 'Location permission was denied. You can pin your location on the map or select your barangay instead.'
        : 'Could not get your location. Try again outdoors, pin it on the map, or select your barangay.';
      $('li-status').textContent = 'Not shared';
      ALERTIFY.toast(msg, 'error');
      renderLoc();
    }, { enableHighAccuracy: true, timeout: 15000, maximumAge: 60000 });
  });

  function togglePin(on) {
    pinMode = on;
    $('pin-hint').hidden = !on;
    $('btn-pin').classList.toggle('active', on);
    $('btn-pin').innerHTML = on ? 'Cancel pinning' : $('btn-pin').dataset.label;
    if (map) map.getContainer().classList.toggle('pin-mode', on);
  }
  $('btn-pin').dataset.label = $('btn-pin').innerHTML;
  $('btn-pin').addEventListener('click', function () {
    if (!map) { ALERTIFY.toast('Map is not available right now.', 'error'); return; }
    togglePin(!pinMode);
  });
  $('btn-clear-loc').addEventListener('click', function () {
    loc = { lat: null, lng: null, accuracy: null, source: null };
    if (userMarker) { map.removeLayer(userMarker); userMarker = null; }
    if (accCircle) { map.removeLayer(accCircle); accCircle = null; }
    renderLoc();
  });

  try { if (!brgySel.value) { var saved = localStorage.getItem('alertify_brgy'); if (saved) brgySel.value = saved; } } catch (e) {}
  brgySel.addEventListener('change', function () {
    try { localStorage.setItem('alertify_brgy', brgySel.value); } catch (e) {}
    renderLoc();
  });
  renderLoc();

  // ---------------------------------------------------------------- questions
  var form = $('report-form'), qWrap = $('questions'), extra = $('extra'), current = null;

  function renderQuestions(code) {
    current = code;
    var qs = cfg.questions[code] || [], html = '';
    if (code === 'other') {
      html += '<label class="field q-block"><span class="q-label">What kind of emergency is it?</span>' +
        '<input type="text" id="other-type" maxlength="120" placeholder="e.g. gas leak, road accident, tsunami warning"></label>';
    }
    qs.forEach(function (q, i) {
      html += '<fieldset class="q-block" data-q="' + q.key + '" style="--d:' + (i * 50) + 'ms"><legend class="q-label">' +
        '<span class="q-n">' + (i + 1) + '</span>' + esc(q.label) + '</legend><div class="q-opts">';
      q.options.forEach(function (o) {
        var danger = (o.value === 'yes' && (q.key === 'trapped' || q.key === 'injured' || q.key === 'immediate_danger' || q.key === 'breathing'))
          || ['chest', 'above_head', 'heavy', 'major', 'same_building'].indexOf(o.value) > -1;
        html += '<label class="opt' + (danger ? ' opt-danger' : '') + '"><input type="radio" name="q_' + q.key + '" value="' +
          o.value + '"><span>' + esc(o.label) + '</span></label>';
      });
      html += '</div></fieldset>';
    });
    qWrap.innerHTML = html;
    extra.hidden = false;
    hideError();
  }

  form.querySelectorAll('input[name="category"]').forEach(function (r) {
    r.addEventListener('change', function () {
      form.querySelectorAll('.dz').forEach(function (d) { d.classList.toggle('selected', d.contains(r) && r.checked); });
      renderQuestions(r.value);
      qWrap.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    });
  });

  qWrap.addEventListener('change', function (e) {
    var fs = e.target.closest('.q-block');
    if (fs) fs.classList.remove('missing');
  });

  // people stepper
  var people = $('people');
  document.querySelectorAll('[data-step]').forEach(function (b) {
    b.addEventListener('click', function () {
      var v = (parseInt(people.value, 10) || 1) + parseInt(b.dataset.step, 10);
      people.value = Math.min(500, Math.max(1, v));
    });
  });

  function showError(msg) { var e = $('form-error'); e.textContent = msg; e.hidden = false; e.scrollIntoView({ behavior: 'smooth', block: 'center' }); }
  function hideError() { $('form-error').hidden = true; }

  // ---------------------------------------------------------------- submit
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    hideError();
    if (!current) { showError('Please select the disaster you are experiencing.'); return; }
    var answers = {}, missing = [];
    (cfg.questions[current] || []).forEach(function (q) {
      var c = form.querySelector('input[name="q_' + q.key + '"]:checked');
      var fs = qWrap.querySelector('[data-q="' + q.key + '"]');
      if (c) answers[q.key] = c.value;
      else if (q.required) { missing.push(q.label); if (fs) fs.classList.add('missing'); }
    });
    if (missing.length) { showError('Please answer all questions (' + missing.length + ' remaining).'); return; }
    if (loc.lat === null && !brgySel.value) {
      showError('Please share your location, pin it on the map, or select your barangay (Step 1).');
      $('loc-card').scrollIntoView({ behavior: 'smooth' });
      return;
    }
    var pc = parseInt(people.value, 10);
    if (!(pc >= 1 && pc <= 500)) { showError('Number of people must be between 1 and 500.'); return; }

    var payload = {
      category: current, answers: answers,
      special: Array.from(form.querySelectorAll('input[name="special"]:checked')).map(function (x) { return x.value; }),
      people_count: pc, description: $('description').value,
      other_type: ($('other-type') || {}).value || '',
      barangay: brgySel.value, lat: loc.lat, lng: loc.lng, accuracy: loc.accuracy,
      location_source: loc.lat !== null ? loc.source : 'manual'
    };
    var btn = $('submit-btn');
    btn.disabled = true; btn.classList.add('loading');
    ALERTIFY.postJSON(cfg.submitUrl, payload).then(function (res) {
      ALERTIFY.toast('Status submitted. Loading your guidance…', 'success');
      window.location.href = res.redirect;
    }).catch(function (err) {
      btn.disabled = false; btn.classList.remove('loading');
      showError(navigator.onLine ? err.message
        : 'You appear to be offline, so your report could not be sent. If you are in danger, call 911 — calls work without internet.');
    });
  });
})();
