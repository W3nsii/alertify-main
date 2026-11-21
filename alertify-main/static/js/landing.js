/* Landing page: nav state and reveal-on-scroll */
(function () {
  'use strict';
  var nav = document.getElementById('lnav');
  function onScroll() { if (nav) nav.classList.toggle('scrolled', window.scrollY > 40); }
  window.addEventListener('scroll', onScroll, { passive: true }); onScroll();

  var t = document.getElementById('lnav-toggle'), links = document.getElementById('lnav-links');
  if (t) t.addEventListener('click', function () {
    var open = links.classList.toggle('open');
    t.setAttribute('aria-expanded', open ? 'true' : 'false');
  });

  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var els = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window && !reduce) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); } });
    }, { threshold: 0.15 });
    els.forEach(function (el) { io.observe(el); });
  } else {
    els.forEach(function (el) { el.classList.add('in'); });
  }

  // Guests: "Log in / Create account / Maybe later" popup.
  //  - The header "Log in" button always opens it; "Maybe later" just closes it.
  //  - Dashboard links open it once per visit; "Maybe later" continues as a guest.
  var modal = document.getElementById('start-modal');
  var openedFromHeader = false;

  function choseLater() {
    try { return sessionStorage.getItem('alertify-start') === 'later'; } catch (e) { return false; }
  }
  function rememberLater() {
    try { sessionStorage.setItem('alertify-start', 'later'); } catch (e) { /* storage blocked: ask again next time */ }
  }
  function openModal(fromHeader) {
    openedFromHeader = fromHeader;
    modal.showModal();
    modal.querySelector('input[name="email"]').focus();
  }

  if (modal && typeof modal.showModal === 'function') {
    document.querySelectorAll('[data-login]').forEach(function (btn) {
      btn.addEventListener('click', function (e) { e.preventDefault(); openModal(true); });
    });
    document.querySelectorAll('[data-start]').forEach(function (link) {
      link.addEventListener('click', function (e) {
        if (choseLater()) return;            // already chose "later": open the dashboard normally
        e.preventDefault();
        openModal(false);
      });
    });
    document.getElementById('start-later').addEventListener('click', function (e) {
      rememberLater();
      if (openedFromHeader) { e.preventDefault(); modal.close(); }  // stay on the home page
    });
    // Clicking the dark backdrop closes the popup.
    modal.addEventListener('click', function (e) { if (e.target === modal) modal.close(); });
  }
})();
