/* "Where should I go?" planner: location in -> nearest centers + what to do out. */
(function () {
  'use strict';
  var cfg = window.ALERTIFY_EVAC, esc = ALERTIFY.esc, evacMap = window.ALERTIFY_EVAC_MAP;
  var $ = function (id) { return document.getElementById(id); };
  var pinned = null;  // {lat, lng} from GPS or a map tap; cleared when the user types

  function stage() { return document.querySelector('input[name="p-stage"]:checked').value; }

  function setPinned(lat, lng, text) {
    pinned = { lat: lat, lng: lng };
    $('p-loc').value = text;
  }

  // Build the query string from whichever location the user gave us.
  function buildQuery() {
    var params = new URLSearchParams({ hazard: $('p-hazard').value, stage: stage() });
    if (pinned) {
      params.set('lat', pinned.lat.toFixed(6));
      params.set('lng', pinned.lng.toFixed(6));
    } else {
      var typed = $('p-loc').value.trim();
      if (!typed) return null;
      params.set('barangay', typed);
    }
    return params.toString();
  }

  function centerCard(c, i) {
    var badge = c.verified ? '<span class="vbadge ok">Verified</span>' : '<span class="vbadge pending">Pending verification</span>';
    var fit = c.suitable ? '<span class="tag tag-green">Verified for this hazard</span>' : '';
    var cap = c.capacity_persons != null ? c.capacity_persons + ' persons' : 'Capacity not provided';
    return '<li class="plan-center" data-id="' + c.id + '" tabindex="0" role="button">' +
      '<span class="plan-rank">' + (i + 1) + '</span>' +
      '<div class="plan-c-main"><b>' + esc(c.name) + '</b>' +
      '<small>' + esc(c.barangay ? 'Brgy. ' + c.barangay : (c.location || '')) + ' · ' + esc(cap) + '</small>' +
      '<div class="cl-tags">' + badge + fit + '</div></div>' +
      '<div class="plan-c-side"><span class="dist">' + c.distance_km.toFixed(1) + ' km</span>' +
      '<small>~' + c.walk_min + ' min walk</small></div></li>';
  }

  function listItems(lines) {
    return lines.map(function (t) { return '<li>' + esc(t) + '</li>'; }).join('');
  }

  function showPlan(d) {
    var box = $('planner-result');
    var warn = d.outside_city
      ? '<p class="note note-warn">This location looks outside Batangas City. ALERTIFY only lists Batangas City centers, so contact your local DRRMO.</p>' : '';
    var approx = d.origin.approximate
      ? '<p class="tiny muted">Position estimated from the evacuation centers in your barangay. Tap the map or use GPS for exact distances.</p>' : '';
    var isNow = d.stage === 'now';
    box.innerHTML = warn +
      '<div class="plan-grid">' +
      '<div><h3>Nearest evacuation centers</h3><p class="tiny muted">From: ' + esc(d.origin.label) + '</p>' + approx +
      '<ol class="plan-centers">' + (d.centers.map(centerCard).join('') || '<li class="muted">No centers found.</li>') + '</ol></div>' +
      '<div><h3>What to do ' + (isNow ? 'now' : 'to prepare') + '</h3>' +
      '<ol class="plan-steps">' + listItems(d.steps) + '</ol>' +
      (d.avoid.length ? '<h3 class="plan-avoid-h">' + (isNow ? 'Avoid' : 'Remember') + '</h3><ul class="plan-avoid">' + listItems(d.avoid) + '</ul>' : '') +
      '</div></div>';
    box.hidden = false;
    if (evacMap) evacMap.setUser(d.origin.lat, d.origin.lng);
  }

  // Clicking a suggested center highlights it on the map below.
  function selectFromList(e) {
    var li = e.target.closest('.plan-center');
    if (!li || !evacMap) return;
    evacMap.select(parseInt(li.dataset.id, 10));
    $('evac-map').scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  function requestPlan(e) {
    e.preventDefault();
    var query = buildQuery();
    if (!query) {
      ALERTIFY.toast('Enter your barangay, use GPS, or tap the map first.', 'error');
      $('p-loc').focus();
      return;
    }
    var btn = $('planner-form').querySelector('.planner-go');
    btn.disabled = true; btn.classList.add('loading');
    fetch(cfg.planApi + '?' + query, { credentials: 'same-origin' })
      .then(function (r) {
        return r.json().then(function (d) {
          if (!r.ok) throw new Error(d.error || 'Something went wrong.');
          return d;
        });
      })
      .then(showPlan)
      .catch(function (err) { ALERTIFY.toast(err.message || 'Could not load suggestions. Check your connection.', 'error'); })
      .then(function () { btn.disabled = false; btn.classList.remove('loading'); });
  }

  function useGps() {
    if (!navigator.geolocation) { ALERTIFY.toast('Location is not supported on this device.', 'error'); return; }
    navigator.geolocation.getCurrentPosition(function (p) {
      setPinned(p.coords.latitude, p.coords.longitude, 'My GPS location (±' + Math.round(p.coords.accuracy) + ' m)');
      $('planner-form').requestSubmit();
    }, function (err) {
      ALERTIFY.toast(err.code === 1 ? 'Location permission denied. Type your barangay instead.' : 'Could not get your location.', 'error');
    }, { enableHighAccuracy: true, timeout: 15000, maximumAge: 60000 });
  }

  $('planner-form').addEventListener('submit', requestPlan);
  $('p-loc').addEventListener('input', function () { pinned = null; });  // typing replaces a pinned point
  $('p-gps').addEventListener('click', useGps);
  $('planner-result').addEventListener('click', selectFromList);
  $('planner-result').addEventListener('keydown', function (e) { if (e.key === 'Enter') selectFromList(e); });

  if (evacMap) evacMap.onMapClick(function (lat, lng) {
    setPinned(lat, lng, 'Pinned on map (' + lat.toFixed(4) + ', ' + lng.toFixed(4) + ')');
    $('planner-form').requestSubmit();
  });
})();
