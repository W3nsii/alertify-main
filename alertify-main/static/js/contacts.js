/* Emergency contacts: search, category filter, copy */
(function () {
  'use strict';
  var search = document.getElementById('c-search'), cat = '';
  function apply() {
    var q = (search.value || '').trim().toLowerCase(), any = false;
    document.querySelectorAll('.contact-group').forEach(function (g) {
      var visible = 0;
      if (cat && g.dataset.group !== cat) { g.hidden = true; return; }
      g.querySelectorAll('.contact-card').forEach(function (c) {
        var show = !q || c.dataset.search.indexOf(q) > -1;
        c.hidden = !show; if (show) visible++;
      });
      g.hidden = !visible; if (visible) any = true;
    });
    document.getElementById('c-empty').hidden = any;
  }
  search.addEventListener('input', apply);
  document.getElementById('c-chips').addEventListener('click', function (e) {
    var b = e.target.closest('.chip-btn'); if (!b) return;
    cat = b.dataset.cat;
    this.querySelectorAll('.chip-btn').forEach(function (x) { x.classList.toggle('active', x === b); });
    apply();
  });
  document.addEventListener('click', function (e) {
    var b = e.target.closest('.copy-btn'); if (!b) return;
    var t = b.dataset.copy;
    (navigator.clipboard ? navigator.clipboard.writeText(t) : Promise.reject()).then(function () {
      ALERTIFY.toast('Copied ' + t, 'success');
    }).catch(function () { ALERTIFY.toast(t, 'info'); });
  });
})();
