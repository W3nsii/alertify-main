/* Evacuation center map + list */
(function () {
  'use strict';
  var cfg = window.ALERTIFY_EVAC, esc = ALERTIFY.esc;
  var $ = function (id) { return document.getElementById(id); };
  var centers = [], markers = {}, user = null, selectedId = null, onlySuitable = true;

  if (cfg.user && cfg.user[0] && cfg.user[1]) user = { lat: parseFloat(cfg.user[0]), lng: parseFloat(cfg.user[1]) };

  var map = null, layer = null, userMarker = null;
  if (window.L) {
    map = L.map('evac-map').setView(cfg.center, 12);
    ALERTIFY.addBaseMap(map);
    layer = L.featureGroup().addTo(map);
  } else {
    $('evac-map').innerHTML = '<p class="map-fallback">The map could not load (you may be offline). The list still works.</p>';
  }

  function hav(a, b, c, d) {
    var R = 6371, r = Math.PI / 180, dl = (c - a) * r, dn = (d - b) * r;
    var h = Math.sin(dl / 2) ** 2 + Math.cos(a * r) * Math.cos(c * r) * Math.sin(dn / 2) ** 2;
    return 2 * R * Math.asin(Math.sqrt(h));
  }

  function icon(c) {
    var cls = 'evac-pin ' + (c.verified ? 'is-verified' : 'is-pending') + (c.id === selectedId ? ' is-selected' : '');
    return L.divIcon({
      className: cls, iconSize: [30, 40], iconAnchor: [15, 38], popupAnchor: [0, -34],
      html: '<svg viewBox="0 0 30 40"><path d="M15 39s13-12.5 13-23A13 13 0 0 0 2 16c0 10.5 13 23 13 23z"/>' +
        '<path class="glyph" d="M8.5 17.5 15 11.5l6.5 6v6.5h-4v-4h-5v4h-4z"/></svg><i></i>'
    });
  }

  function dirLinks(c) {
    var o = user ? user.lat + '%2C' + user.lng : '';
    var osm = 'https://www.openstreetmap.org/directions?engine=fossgis_osrm_foot&route=' + o + '%3B' + c.lat + '%2C' + c.lng;
    var g = 'https://www.google.com/maps/dir/?api=1&destination=' + c.lat + ',' + c.lng + (user ? '&origin=' + user.lat + ',' + user.lng : '');
    return '<a class="btn btn-sm btn-red" target="_blank" rel="noopener" href="' + osm + '">Directions (OSM)</a>' +
      '<a class="btn btn-sm btn-outline" target="_blank" rel="noopener" href="' + g + '">Google Maps</a>';
  }

  function hazardName(h) { return cfg.hazardNames[h] || h; }

  function badges(c) {
    var h = $('f-hazard').value, out = '';
    out += c.verified ? '<span class="vbadge ok">Verified' + (c.verified_at ? ' · ' + esc(c.verified_at) : '') + '</span>'
      : '<span class="vbadge pending">Pending verification</span>';
    if (h) out += c.hazards.indexOf(h) > -1 ? '<span class="tag tag-green">Verified for ' + esc(hazardName(h).toLowerCase()) + '</span>'
      : '<span class="tag">' + esc(hazardName(h)) + ' suitability not verified</span>';
    if (c.operational_status && c.operational_status !== 'unknown')
      out += '<span class="tag tag-op-' + c.operational_status + '">' + esc(c.operational_status) + (c.status_updated_at ? ' · ' + esc(c.status_updated_at) : '') + '</span>';
    return out;
  }

  function detail(c) {
    var el = $('center-detail');
    el.hidden = false;
    el.innerHTML = '<button class="icon-btn sm cd-x" aria-label="Close">✕</button>' +
      '<h3>' + esc(c.name) + '</h3><p class="muted">' + esc(c.location || '') + (c.barangay ? ' · Brgy. ' + esc(c.barangay) : '') + '</p>' +
      '<div class="cl-tags">' + badges(c) + '</div>' +
      '<dl class="kv kv-row">' +
      '<div><dt>Capacity</dt><dd>' + (c.capacity_persons != null ? c.capacity_persons + ' persons / ' + c.capacity_families + ' families' : 'Not provided') + '</dd></div>' +
      '<div><dt>Distance</dt><dd>' + (c._d != null ? c._d.toFixed(2) + ' km (straight-line)' : 'Share your location') + '</dd></div>' +
      '<div><dt>Current status</dt><dd>' + (c.operational_status === 'unknown' ? 'Not confirmed — check with CDRRMO' : esc(c.operational_status)) + '</dd></div>' +
      '</dl>' +
      '<p class="tiny muted">Source: ' + esc(c.source || '') + (c.source_note ? ' — ' + esc(c.source_note) : '') + '</p>' +
      '<p class="tiny warn-text">Routes are not checked for hazards. Avoid flooded roads, landslide areas, and fallen power lines.</p>' +
      '<div class="row-actions">' + dirLinks(c) + '</div>';
    el.querySelector('.cd-x').onclick = function () { el.hidden = true; select(null); };
  }

  function select(id, pan) {
    selectedId = id;
    Object.keys(markers).forEach(function (k) {
      var c = centers.find(function (x) { return x.id == k; });
      markers[k].setIcon(icon(c));
    });
    document.querySelectorAll('.evac-item').forEach(function (li) { li.classList.toggle('active', li.dataset.id == id); });
    if (id == null) return;
    var c = centers.find(function (x) { return x.id == id; });
    if (!c) return;
    detail(c);
    if (map && pan !== false && c.lat) map.setView([c.lat, c.lng], 16);
    var li = document.querySelector('.evac-item[data-id="' + id + '"]');
    if (li) li.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  }

  function render() {
    var h = $('f-hazard').value, b = $('f-brgy').value, q = $('f-q').value.trim().toLowerCase();
    var hazardData = h && centers.some(function (c) { return c.hazards.indexOf(h) > -1; });
    var note = $('hazard-note');
    if (h) {
      note.hidden = false;
      note.innerHTML = hazardData
        ? '<label class="check"><input type="checkbox" id="only-suitable" ' + (onlySuitable ? 'checked' : '') + '> Show only centers verified for ' + esc(hazardName(h).toLowerCase()) + '</label>'
        : '<b>No center has been verified as suitable for ' + esc(hazardName(h).toLowerCase()) + ' yet.</b> All centers are listed. Confirm with the CDRRMO or your barangay which center is safe for this hazard.';
      var cb = $('only-suitable');
      if (cb) cb.onchange = function () { onlySuitable = cb.checked; render(); };
    } else note.hidden = true;

    centers.forEach(function (c) { c._d = user && c.lat != null ? hav(user.lat, user.lng, c.lat, c.lng) : null; });
    var list = centers.filter(function (c) {
      if (b && c.barangay !== b) return false;
      if (q && (c.name + ' ' + (c.location || '') + ' ' + (c.barangay || '')).toLowerCase().indexOf(q) < 0) return false;
      if (h && hazardData && onlySuitable && c.hazards.indexOf(h) < 0) return false;
      return true;
    });
    list.sort(function (x, y) {
      if (x._d != null && y._d != null) return x._d - y._d;
      return x.name.localeCompare(y.name);
    });

    $('evac-count').textContent = list.length + ' center' + (list.length === 1 ? '' : 's') + (user ? ' · sorted by distance' : '');
    $('evac-list').innerHTML = list.map(function (c, i) {
      return '<li class="evac-item' + (c.id === selectedId ? ' active' : '') + '" data-id="' + c.id + '" tabindex="0" role="button">' +
        '<div class="ei-main"><b>' + (user && i < 3 ? '<span class="near-n">' + (i + 1) + '</span>' : '') + esc(c.name) + '</b>' +
        '<small>' + esc(c.barangay || c.location || '') + '</small>' +
        '<div class="cl-tags">' + badges(c) + '</div></div>' +
        '<div class="ei-side">' + (c._d != null ? '<span class="dist">' + c._d.toFixed(1) + ' km</span>' : '') +
        (c.capacity_persons != null ? '<small>' + c.capacity_persons + ' persons</small>' : '') + '</div></li>';
    }).join('') || '<li class="muted pad">No centers match your filters.</li>';

    if (map) {
      layer.clearLayers(); markers = {};
      list.forEach(function (c) {
        if (c.lat == null) return;
        var mk = L.marker([c.lat, c.lng], { icon: icon(c), title: c.name, keyboard: true });
        mk.bindTooltip(c.name, { direction: 'top', offset: [0, -30] });
        mk.on('click', function () { select(c.id, false); });
        mk.addTo(layer); markers[c.id] = mk;
      });
      if (userMarker) userMarker.setLatLng([user.lat, user.lng]);
      else if (user) userMarker = L.marker([user.lat, user.lng], {
        icon: L.divIcon({ className: 'user-pin', html: '<span></span>', iconSize: [22, 22], iconAnchor: [11, 11] }), zIndexOffset: 2000
      }).addTo(map).bindTooltip('You are here');
    }
  }

  function fitView() {
    if (!map) return;
    if (user) {
      var near = centers.filter(function (c) { return c._d != null; }).sort(function (a, b) { return a._d - b._d; }).slice(0, 3);
      var pts = near.map(function (c) { return [c.lat, c.lng]; }).concat([[user.lat, user.lng]]);
      map.fitBounds(pts, { padding: [40, 40], maxZoom: 15 });
    } else if (layer.getLayers().length) {
      map.fitBounds(layer.getBounds(), { padding: [20, 20] });
    }
  }

  $('evac-list').addEventListener('click', function (e) {
    var li = e.target.closest('.evac-item'); if (li) select(parseInt(li.dataset.id, 10));
  });
  $('evac-list').addEventListener('keydown', function (e) {
    if (e.key === 'Enter' || e.key === ' ') { var li = e.target.closest('.evac-item'); if (li) { e.preventDefault(); select(parseInt(li.dataset.id, 10)); } }
  });
  ['f-hazard', 'f-brgy'].forEach(function (id) { $(id).addEventListener('change', function () { render(); fitView(); }); });
  $('f-q').addEventListener('input', render);

  $('btn-locate').addEventListener('click', function () {
    var btn = this;
    if (!navigator.geolocation) { ALERTIFY.toast('Location is not supported on this device.', 'error'); return; }
    btn.disabled = true; btn.classList.add('loading');
    navigator.geolocation.getCurrentPosition(function (p) {
      btn.disabled = false; btn.classList.remove('loading');
      user = { lat: p.coords.latitude, lng: p.coords.longitude };
      $('loc-note').textContent = 'Using your location (±' + Math.round(p.coords.accuracy) + ' m). Distances are straight-line estimates.';
      render(); fitView();
    }, function (err) {
      btn.disabled = false; btn.classList.remove('loading');
      ALERTIFY.toast(err.code === 1 ? 'Location permission denied. Filter by barangay instead.' : 'Could not get your location.', 'error');
    }, { enableHighAccuracy: true, timeout: 15000, maximumAge: 60000 });
  });

  // Small interface used by planner.js (the "Where should I go?" card).
  window.ALERTIFY_EVAC_MAP = {
    setUser: function (lat, lng) { user = { lat: lat, lng: lng }; render(); fitView(); },
    select: function (id) { select(id); },
    onMapClick: function (cb) { if (map) map.on('click', function (e) { cb(e.latlng.lat, e.latlng.lng); }); }
  };

  fetch(cfg.api, { credentials: 'same-origin' }).then(function (r) { return r.json(); }).then(function (d) {
    centers = d.centers;
    render(); fitView();
    if (cfg.focus) select(parseInt(cfg.focus, 10));
  }).catch(function () {
    $('evac-count').textContent = 'Could not load evacuation centers. Check your connection.';
  });
})();
