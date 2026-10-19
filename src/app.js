(function () {
  'use strict';
  var TRIP = JSON.parse(document.getElementById('trip-data').textContent);
  var GEO = JSON.parse(document.getElementById('geo-data').textContent);
  var $ = function (s, el) { return (el || document).querySelector(s); };
  var $$ = function (s, el) { return Array.prototype.slice.call((el || document).querySelectorAll(s)); };
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var mqWide = window.matchMedia('(min-width: 960px)');
  var ST = { reserve: 'Réservé', areserver: 'À réserver', optionnel: 'Optionnel', arbitrer: 'À arbitrer' };
  var ORDER = ['areserver', 'arbitrer', 'optionnel', 'reserve'];
  var dayById = {};
  TRIP.days.forEach(function (d) { dayById[d.id] = d; });
  var actById = {};
  TRIP.acts.forEach(function (a) { actById[a.id] = a; });
  function esc(s) { return String(s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function store(k, v) { try { if (v === undefined) return window.localStorage.getItem(k); window.localStorage.setItem(k, v); } catch (e) { return null; } return null; }

  /* ---------------- Statuts ---------------- */
  var overrides = {};
  var mode = 'local';
  var db = null;
  var readOnly = false;
  var LS = 'rm2027-statuts';
  function lsGet() { try { return JSON.parse(store(LS) || '{}') || {}; } catch (e) { return {}; } }
  function statusOf(id) { return overrides[id] || (actById[id] && actById[id].s); }

  function stControl(id) {
    var a = actById[id];
    var s = statusOf(id);
    var opts = ORDER.map(function (k) { return '<option value="' + k + '"' + (k === s ? ' selected' : '') + '>' + ST[k] + '</option>'; }).join('');
    return '<label class="st" data-act="' + id + '" data-s="' + s + '"><span class="ico" aria-hidden="true"></span><span class="st-txt">' + ST[s] + '</span><span class="st-caret" aria-hidden="true"></span>' +
      '<select aria-label="Statut : ' + esc(a.txt) + '">' + opts + '</select></label>';
  }

  function renderCounts() {
    var c = { reserve: 0, areserver: 0, optionnel: 0, arbitrer: 0 };
    TRIP.acts.forEach(function (a) { c[statusOf(a.id)]++; });
    $$('[data-count]').forEach(function (el) { el.textContent = c[el.dataset.count]; });
    return c;
  }

  function renderResa() {
    var host = $('#resa');
    var html = '';
    ORDER.forEach(function (k) {
      var items = TRIP.acts.filter(function (a) { return statusOf(a.id) === k; });
      html += '<div class="resa-group" data-s="' + k + '"><h3><span class="ico" aria-hidden="true"></span>' + ST[k] + ' <span class="n">' + items.length + '</span></h3>';
      if (!items.length) {
        html += '<p class="resa-empty">' + (k === 'reserve' ? 'Rien encore. Passez un élément à « Réservé » une fois la réservation confirmée.' : 'Aucun élément.') + '</p>';
      } else {
        html += '<ul class="resa-list">' + items.map(function (a) {
          var d = dayById[a.day];
          return '<li><button type="button" class="resa-day" data-goto="' + a.day + '"><span class="d">J' + d.n + ' · ' + esc(d.short) + '</span><span class="t">' + esc(a.txt) + '</span></button>' + stControl(a.id) + '</li>';
        }).join('') + '</ul>';
      }
      html += '</div>';
    });
    host.innerHTML = html;
  }

  function applyStatuses() {
    $$('.st[data-act]').forEach(function (el) {
      var s = statusOf(el.dataset.act);
      el.dataset.s = s;
      var sel = $('select', el);
      if (sel && sel.value !== s) sel.value = s;
      var t = $('.st-txt', el);
      if (t) t.textContent = ST[s];
    });
    $$('[data-tact]').forEach(function (li) {
      var s = statusOf(li.dataset.tact);
      li.dataset.s = s;
      var sr = $('.sr', li);
      if (sr) sr.textContent = ' (' + ST[s] + ')';
    });
    renderCounts();
    renderResa();
  }

  function setSync(kind) {
    var msg = {
      db: 'Statuts partagés : un changement est visible par vous deux. Touchez un statut pour le modifier.',
      local: 'Statuts enregistrés sur cet appareil uniquement. Touchez un statut pour le modifier.',
      ro: 'Lecture seule : vous pouvez consulter les statuts sans les modifier.',
      err: "Le statut n'a pas pu être enregistré. Réessayez dans un instant."
    }[kind];
    $('#sync').textContent = msg;
  }

  var chains = {};
  function queueWrite(id, v) {
    var path = id.indexOf('/') === -1 ? 'statuts/' + id : id;
    var p = (chains[id] || Promise.resolve()).catch(function () {}).then(function () {
      return db.doc(path).set({ s: v, t: Date.now() });
    });
    chains[id] = p;
    return p;
  }

  /* ---------------- Galerie photo d'une maison : visionneuse plein écran ---------------- */
  (function () {
    var lb, img, cap, cnt, list = [], idx = 0, x0 = null;
    var ICON = function (d) { return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="' + d + '" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'; };
    function build() {
      lb = document.createElement('dialog');
      lb.className = 'lb';
      lb.setAttribute('aria-label', 'Photos de la maison');
      lb.innerHTML = '<div class="lb-in"><div class="lb-top"><span class="lb-cnt mono" aria-live="polite"></span>' +
        '<button type="button" class="lb-x" aria-label="Fermer">' + ICON('M6 6l12 12M18 6L6 18') + '</button></div>' +
        '<figure class="lb-fig"><img alt="">' +
        '<button type="button" class="lb-nav lb-prev" aria-label="Photo précédente">' + ICON('M15 5l-7 7 7 7') + '</button>' +
        '<button type="button" class="lb-nav lb-next" aria-label="Photo suivante">' + ICON('M9 5l7 7-7 7') + '</button></figure>' +
        '<p class="lb-cap"></p></div>';
      document.body.appendChild(lb);
      img = lb.querySelector('img'); cap = lb.querySelector('.lb-cap'); cnt = lb.querySelector('.lb-cnt');
      lb.querySelector('.lb-x').addEventListener('click', function () { lb.close(); });
      lb.querySelector('.lb-prev').addEventListener('click', function () { show(idx - 1); });
      lb.querySelector('.lb-next').addEventListener('click', function () { show(idx + 1); });
      lb.addEventListener('keydown', function (e) {
        if (e.key === 'ArrowLeft') { e.preventDefault(); show(idx - 1); }
        else if (e.key === 'ArrowRight') { e.preventDefault(); show(idx + 1); }
      });
      var fig = lb.querySelector('.lb-fig');
      fig.addEventListener('touchstart', function (e) { x0 = e.touches[0].clientX; }, { passive: true });
      fig.addEventListener('touchend', function (e) {
        if (x0 === null) return;
        var dx = e.changedTouches[0].clientX - x0; x0 = null;
        if (Math.abs(dx) > 40) show(idx + (dx < 0 ? 1 : -1));
      }, { passive: true });
      lb.addEventListener('close', function () { document.documentElement.style.overflow = ''; });
    }
    function show(i) {
      idx = (i + list.length) % list.length;
      var it = list[idx];
      img.src = it.href; img.alt = it.cap;
      cap.textContent = it.cap;
      cnt.textContent = (idx + 1) + ' / ' + list.length;
      [idx + 1, idx - 1].forEach(function (j) { var n = list[(j + list.length) % list.length]; if (n) { var p = new Image(); p.src = n.href; } });
    }
    document.addEventListener('click', function (e) {
      var a = e.target.closest && e.target.closest('.gal-strip a');
      if (!a || typeof HTMLDialogElement === 'undefined') return;
      e.preventDefault();
      var g = a.closest('.gal');
      list = Array.prototype.map.call(g.querySelectorAll('.gal-strip a'), function (x) { return { href: x.getAttribute('href'), cap: x.dataset.cap }; });
      if (!lb) build();
      document.documentElement.style.overflow = 'hidden';
      lb.showModal();
      show(+a.dataset.i);
      lb.querySelector('.lb-next').focus();
    });
  })();

  /* ---------------- Demandes de logement (HomeExchange) ---------------- */
  var LGST = TRIP.lgst || {};
  var lgById = {};
  (TRIP.logements || []).forEach(function (x) { lgById[x.id] = x; });
  var lgOver = {};
  var LSL = 'rm2027-logements';
  function lgGet() { try { return JSON.parse(store(LSL) || '{}') || {}; } catch (e) { return {}; } }
  function lgStatus(id) { return lgOver[id] || (lgById[id] && lgById[id].s); }
  function applyLg() {
    $$('.st[data-lg]').forEach(function (el) {
      var s = lgStatus(el.dataset.lg);
      el.dataset.s = s;
      var sel = $('select', el);
      if (sel && sel.value !== s) sel.value = s;
      var t = $('.st-txt', el);
      if (t) t.textContent = LGST[s];
      var li = el.closest('.lg-item');
      if (li) li.dataset.s = s;
    });
    $$('.lg-group').forEach(function (g) {
      var n = $$('.lg-item', g).filter(function (li) { return li.dataset.s !== 'ecartee' && li.dataset.s !== 'refusee'; }).length;
      var c = $('h3 .n', g);
      if (c) c.textContent = n;
    });
  }
  function lgChange(sel) {
    var id = sel.closest('.st').dataset.lg;
    var v = sel.value;
    var prev = lgStatus(id);
    if (readOnly || !lgById[id] || !LGST[v]) { sel.value = prev; return; }
    lgOver[id] = v;
    applyLg();
    if (mode === 'db') {
      queueWrite('logements/' + id, v).catch(function (err) {
        lgOver[id] = prev;
        applyLg();
        if (err && err.code === 'invalid_argument') { readOnly = true; setSync('ro'); } else { setSync('err'); }
      });
    } else {
      var o = lgGet(); o[id] = v; store(LSL, JSON.stringify(o));
    }
  }

  document.addEventListener('change', function (e) {
    var sel = e.target.closest ? e.target.closest('.st select') : null;
    if (!sel) return;
    if (sel.closest('.st').dataset.lg) { lgChange(sel); return; }
    var id = sel.closest('.st').dataset.act;
    var v = sel.value;
    var prev = statusOf(id);
    if (readOnly) { sel.value = prev; return; }
    overrides[id] = v;
    applyStatuses();
    if (mode === 'db') {
      queueWrite(id, v).catch(function (err) {
        overrides[id] = prev;
        applyStatuses();
        if (err && err.code === 'invalid_argument') { readOnly = true; setSync('ro'); } else { setSync('err'); }
      });
    } else {
      var o = lsGet(); o[id] = v; store(LS, JSON.stringify(o));
    }
  });

  function useLocal() {
    mode = 'local';
    overrides = lsGet();
    lgOver = lgGet();
    applyStatuses();
    applyLg();
    setSync('local');
  }

  function initDb() {
    var c = window.claude;
    if (!c || typeof c.use !== 'function') { useLocal(); return; }
    Promise.resolve().then(function () { return c.use('db'); }).then(function (ns) {
      if (!ns) { useLocal(); return; }
      db = ns; mode = 'db'; setSync('db');
      try {
        db.collection('statuts').onSnapshot(function (snap) {
          var o = {};
          snap.docs.forEach(function (d) { var v = d.data(); if (v && ST[v.s] && actById[d.id]) o[d.id] = v.s; });
          overrides = o;
          applyStatuses();
        }, function () { useLocal(); });
        db.collection('logements').onSnapshot(function (snap) {
          var o = {};
          snap.docs.forEach(function (d) { var v = d.data(); if (v && LGST[v.s] && lgById[d.id]) o[d.id] = v.s; });
          lgOver = o;
          applyLg();
        }, function () {});
      } catch (e) { useLocal(); }
    }).catch(useLocal);
  }

  /* ---------------- Dates ---------------- */
  function isoToday() {
    var d = new Date();
    return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
  }
  function dayDiff(a, b) { return Math.round((Date.parse(b + 'T00:00:00Z') - Date.parse(a + 'T00:00:00Z')) / 86400000); }
  var today = isoToday();
  var todayDay = TRIP.days.filter(function (d) { return d.date === today; })[0] || null;

  function initToday() {
    var start = TRIP.days[0].date, end = TRIP.days[TRIP.days.length - 1].date;
    var btn = $('#btn-today');
    if (todayDay) {
      $('#count-n').textContent = 'J' + todayDay.n;
      $('#count-t').textContent = todayDay.title;
      btn.hidden = false;
      var card = document.getElementById('d-' + todayDay.id);
      card.classList.add('is-today');
      var tag = document.createElement('span');
      tag.className = 'tag tag-today'; tag.textContent = "Aujourd'hui";
      $('.day-date', card).appendChild(tag);
      var row = $('.row[data-day="' + todayDay.id + '"]');
      if (row) row.classList.add('is-today');
    } else if (today < start) {
      var n = dayDiff(today, start);
      $('#count-n').textContent = n;
      $('#count-t').textContent = n > 1 ? 'jours avant le départ' : 'jour avant le départ';
    } else if (today > end) {
      $('#count-n').textContent = '17';
      $('#count-t').textContent = 'jours de voyage, terminé';
    }
    btn.addEventListener('click', function () { goDay((todayDay || TRIP.days[0]).id); });
  }

  /* ---------------- Pages ---------------- */
  var PAGES = ['accueil', 'jours', 'suivi', 'infos', 'loin'];
  var ALIAS = { programme: 'jours', reservations: 'suivi', pratique: 'infos', sources: 'infos' };
  var page = null;
  function showPage(name) {
    if (page === name) return false;
    PAGES.forEach(function (p) { document.getElementById('v-' + p).hidden = p !== name; });
    $$('[data-nav]').forEach(function (a) {
      if (a.dataset.nav === name) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current');
    });
    page = name;
    var fx = document.getElementById('fx');
    if (fx) fx.setAttribute('data-page', name);
    if (name === 'jours') ensureMap();
    var cur = $('.nav-links [aria-current]');
    if (cur && cur.scrollIntoView && navOvf()) cur.scrollIntoView({ block: 'nearest', inline: 'nearest' });
    return true;
  }
  /* Onglets trop larges (très petits écrans) : défilement horizontal signalé par un fondu à droite */
  function navOvf() {
    var l = $('.nav-links');
    if (!l) return false;
    var o = l.scrollWidth > l.clientWidth + 1;
    l.classList.toggle('ovf', o && l.scrollLeft + l.clientWidth < l.scrollWidth - 2);
    return o;
  }
  window.addEventListener('resize', navOvf);
  (function () { var l = $('.nav-links'); if (l) l.addEventListener('scroll', navOvf, { passive: true }); })();
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(navOvf);
  navOvf();
  function route() {
    var h = (location.hash || '').replace('#', '');
    if (/^j\d{1,2}$/.test(h) && dayById[h]) {
      showPage('jours');
      select(h, { scroll: true, fly: true });
      return;
    }
    var m = /^lire-([a-z0-9-]+)$/.exec(h);
    if (m && document.getElementById('a-' + m[1])) {
      showPage('loin'); openEssay(m[1]); window.scrollTo(0, 0);
      return;
    }
    if (h === 'logements' || h === 'demandes') { showPage('suivi'); selectTab('lg'); window.scrollTo(0, 0); return; }
    if (/^lg-[a-z0-9-]+$/.test(h) && document.getElementById(h)) {
      showPage('suivi'); selectTab('lg');
      var card = document.getElementById(h);
      setTimeout(function () { card.scrollIntoView({ block: 'start' }); }, 0);
      return;
    }
    h = ALIAS[h] || h;
    if (PAGES.indexOf(h) < 0) h = 'accueil';
    if (h === 'loin') { showPage('loin'); openEssay(null); window.scrollTo(0, 0); return; }
    if (showPage(h)) window.scrollTo(0, 0);
  }
  function openEssay(slug) {
    var list = document.getElementById('essays-list');
    if (list) list.hidden = !!slug;
    $$('.essay').forEach(function (el) { el.hidden = el.id !== 'a-' + slug; });
  }
  function goDay(id) {
    try {
      if (location.hash === '#' + id) route(); else location.hash = id;
    } catch (e) { showPage('jours'); select(id, { scroll: true, fly: true }); }
  }
  window.addEventListener('hashchange', route);

  /* ---------------- Quiz de fin de dossier ---------------- */
  function quizScore(q) {
    var items = $$('.qz', q);
    var done = items.filter(function (li) { return li.dataset.done; }).length;
    if (done < items.length) return;
    var good = items.filter(function (li) { return li.dataset.res === 'ok'; }).length;
    var msg = good === items.length ? 'parfait, vous êtes prêts pour le voyage.'
      : good >= 3 ? "bien retenu. Un coup d'œil au dossier pour les détails ?"
      : 'réécoutez le podcast ou relisez le dossier avant le départ.';
    $('.qz-score', q).textContent = 'Score : ' + good + ' sur ' + items.length + ', ' + msg;
    $('.qz-end', q).hidden = false;
  }
  function quizAnswer(btn) {
    var li = btn.closest('.qz');
    if (!li || li.dataset.done) return;
    var ok = +li.dataset.ok, i = +btn.dataset.i, good = i === ok, okText = '';
    li.dataset.done = '1';
    li.dataset.res = good ? 'ok' : 'ko';
    $$('.qz-o', li).forEach(function (b) {
      var k = +b.dataset.i;
      b.disabled = true;
      if (k === ok) { b.classList.add('is-ok'); okText = b.lastElementChild.textContent; }
      if (k === i) { b.setAttribute('aria-pressed', 'true'); if (!good) b.classList.add('is-ko'); }
    });
    var why = $('.qz-why', li);
    $('.qz-v', why).textContent = good ? 'Bonne réponse.' : 'Pas tout à fait. Réponse : ' + okText + '.';
    why.hidden = false;
    quizScore(li.closest('.quiz'));
  }
  function quizReset(q) {
    $$('.qz', q).forEach(function (li) {
      delete li.dataset.done; delete li.dataset.res;
      $$('.qz-o', li).forEach(function (b) { b.disabled = false; b.classList.remove('is-ok', 'is-ko'); b.removeAttribute('aria-pressed'); });
      $('.qz-why', li).hidden = true;
    });
    $('.qz-end', q).hidden = true;
    q.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'start' });
    var first = $('.qz-o', q);
    if (first) first.focus({ preventScroll: true });
  }
  document.addEventListener('click', function (e) {
    if (!e.target.closest) return;
    var jump = e.target.closest('.qz-jump');
    if (jump) {
      e.preventDefault();
      var target = document.getElementById(jump.getAttribute('href').slice(1));
      if (target) target.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'start' });
      return;
    }
    var o = e.target.closest('.qz-o');
    if (o) { quizAnswer(o); return; }
    var r = e.target.closest('.qz-reset');
    if (r) quizReset(r.closest('.quiz'));
  });

  /* Onglets de la page Suivi : réservations ou demandes de logement (choix mémorisé sur l'appareil) */
  var TABKEY = 'rm2027-suivi-onglet';
  function selectTab(name, focus) {
    var tabs = $$('.tabs [role="tab"]');
    if (!tabs.some(function (b) { return b.dataset.tab === name; })) name = 'resa';
    tabs.forEach(function (b) {
      var on = b.dataset.tab === name;
      b.setAttribute('aria-selected', String(on));
      b.tabIndex = on ? 0 : -1;
      var panel = document.getElementById(b.getAttribute('aria-controls'));
      if (panel) panel.hidden = !on;
      if (on && focus) b.focus();
    });
    store(TABKEY, name);
  }
  document.addEventListener('click', function (e) {
    var b = e.target.closest ? e.target.closest('.tabs [role="tab"]') : null;
    if (b) selectTab(b.dataset.tab);
  });
  document.addEventListener('keydown', function (e) {
    var b = e.target.closest ? e.target.closest('.tabs [role="tab"]') : null;
    if (!b) return;
    var tabs = $$('.tabs [role="tab"]'), i = tabs.indexOf(b), j = -1;
    if (e.key === 'ArrowRight') j = (i + 1) % tabs.length;
    else if (e.key === 'ArrowLeft') j = (i - 1 + tabs.length) % tabs.length;
    else if (e.key === 'Home') j = 0;
    else if (e.key === 'End') j = tabs.length - 1;
    if (j < 0) return;
    e.preventDefault();
    selectTab(tabs[j].dataset.tab, true);
  });
  selectTab(store(TABKEY) || 'resa');

  /* Une ligne du tableau ouvre la journée */
  document.addEventListener('click', function (e) {
    if (!e.target.closest) return;
    if (e.target.closest('a')) return;
    var row = e.target.closest('.tab .row');
    if (row) goDay(row.dataset.day);
  });

  /* ---------------- Sélection d'un jour ---------------- */
  var selected = null;
  function scrollToDay(id) {
    var el = document.getElementById('d-' + id);
    if (el) el.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'start' });
  }
  function select(id, opt) {
    opt = opt || {};
    selected = id;
    $$('.day').forEach(function (c) { c.classList.toggle('is-sel', c.id === 'd-' + id); });
    if (opt.fly !== false && $('#prog').classList.contains('map-off')) toggleMap(true);
    if (opt.scroll) scrollToDay(id);
    if (opt.fly !== false) flyToDay(dayById[id]);
    else markSelection();
  }

  document.addEventListener('click', function (e) {
    var t = e.target.closest ? e.target.closest('[data-goto],[data-fly],[data-view],[data-copy]') : null;
    if (!t) return;
    if (t.dataset.goto) { if (popup) popup.remove(); goDay(t.dataset.goto); }
    else if (t.dataset.fly) { select(t.dataset.fly, { fly: true }); }
    else if (t.dataset.view) { setView(t.dataset.view, true); }
    else if (t.dataset.copy) { copy(t); }
  });

  function copy(btn) {
    var txt = btn.dataset.copy;
    var done = function () { btn.textContent = 'Copié'; setTimeout(function () { btn.textContent = 'Copier'; }, 1600); };
    var fallback = function () {
      var num = btn.parentElement.querySelector('.num');
      if (!num) return;
      var r = document.createRange(); r.selectNodeContents(num);
      var s = window.getSelection(); s.removeAllRanges(); s.addRange(r);
    };
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(txt).then(done, fallback);
      else fallback();
    } catch (e) { fallback(); }
  }

  /* ---------------- Carte ---------------- */
  var LIBS = ['https://cdn.jsdelivr.net/npm/maplibre-gl@4.7.1/dist/maplibre-gl.js', 'https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js'];
  /* Relief : tuiles d'altitude « terrarium » publiées avec la page (dossier terrain/).
     Les tuiles absentes (pleine mer) sont servies plates par le protocole relief://. */
  var RELIEF = GEO.terrain || null;
  var reliefKeys = {};
  if (RELIEF) RELIEF.keys.forEach(function (k) { reliefKeys[k] = true; });
  var flatBuf = null;
  function flatTile() {
    if (!flatBuf) {
      var s = atob(RELIEF.flat), u = new Uint8Array(s.length);
      for (var i = 0; i < s.length; i++) u[i] = s.charCodeAt(i);
      flatBuf = u.buffer;
    }
    return flatBuf.slice(0);
  }
  var reliefBase = (function () { try { return new URL('terrain/', document.baseURI).href; } catch (e) { return 'terrain/'; } })();
  function registerRelief() {
    if (!RELIEF || !window.maplibregl.addProtocol) return false;
    window.maplibregl.addProtocol('relief', function (params, ctl) {
      var key = params.url.slice('relief://'.length);
      if (!reliefKeys[key]) return Promise.resolve({ data: flatTile() });
      return fetch(reliefBase + key + '.png', { signal: ctl && ctl.signal })
        .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.arrayBuffer(); })
        .then(function (b) { return { data: b }; })
        .catch(function (err) {
          if (ctl && ctl.signal && ctl.signal.aborted) throw err;
          return { data: flatTile() };
        });
    });
    return true;
  }
  var K = Math.cos(20.7 * Math.PI / 180);
  var places = TRIP.places;
  var map = null, mapMode = 'none', popup = null, markers = {};
  var view = 'both';
  var tilted = store('rm2027-tilt') !== 'flat';
  var PITCH = 58;
  var shell = $('#map-shell');

  function padB(b, f) { var dx = (b[2] - b[0]) * f, dy = (b[3] - b[1]) * f; return [[b[0] - dx, b[1] - dy], [b[2] + dx, b[3] + dy]]; }
  var VIEWS = {
    reunion: padB(GEO.islands.reunion.bounds, 0.04),
    maurice: padB(GEO.islands.maurice.bounds, 0.02),
    both: [[55.15, -21.45], [57.85, -19.8]]
  };

  function arc(a, b, bend, n) {
    bend = bend == null ? 0.14 : bend; n = n || 20;
    var ax = a[0] * K, ay = a[1], bx = b[0] * K, by = b[1];
    var cx = (ax + bx) / 2 - (by - ay) * bend, cy = (ay + by) / 2 + (bx - ax) * bend;
    var out = [];
    for (var i = 0; i <= n; i++) {
      var t = i / n, u = 1 - t;
      out.push([(u * u * ax + 2 * u * t * cx + t * t * bx) / K, u * u * ay + 2 * u * t * cy + t * t * by]);
    }
    return out;
  }
  function ptsOf(d) { return d.pts.map(function (p) { return [places[p].lon, places[p].lat]; }); }
  function routeCoords(d) {
    var pts = ptsOf(d), out = [];
    for (var i = 1; i < pts.length; i++) {
      var seg = arc(pts[i - 1], pts[i], 0.12, 18);
      if (i > 1) seg.shift();
      out = out.concat(seg);
    }
    return out;
  }

  function geojson() {
    var land = { type: 'FeatureCollection', features: [] };
    var water = { type: 'FeatureCollection', features: [] };
    ['reunion', 'maurice'].forEach(function (k) {
      GEO.islands[k].land.forEach(function (poly) { land.features.push({ type: 'Feature', properties: { isl: k }, geometry: { type: 'Polygon', coordinates: poly } }); });
      GEO.islands[k].waterlines.forEach(function (w) {
        var i = w.d < 0.006 ? 0 : (w.d < 0.012 ? 1 : 2);
        water.features.push({ type: 'Feature', properties: { i: i }, geometry: { type: 'LineString', coordinates: w.c } });
      });
    });
    var routes = { type: 'FeatureCollection', features: [] };
    TRIP.days.forEach(function (d) {
      if (d.pts.length < 2) return;
      routes.features.push({ type: 'Feature', properties: { day: d.id }, geometry: { type: 'LineString', coordinates: routeCoords(d) } });
    });
    return { land: land, water: water, routes: routes };
  }

  function tok(n) { return getComputedStyle(document.documentElement).getPropertyValue(n).trim(); }

  function buildStyle() {
    var g = geojson();
    return {
      version: 8,
      sources: {
        land: { type: 'geojson', data: g.land },
        water: { type: 'geojson', data: g.water },
        routes: { type: 'geojson', data: g.routes }
      },
      layers: [
        { id: 'sea', type: 'background', paint: { 'background-color': tok('--sea') } },
        { id: 'waterlines', type: 'line', source: 'water', paint: { 'line-color': tok('--coast'), 'line-width': 0.8, 'line-opacity': ['match', ['get', 'i'], 0, 0.45, 1, 0.26, 0.13] } },
        { id: 'land', type: 'fill', source: 'land', paint: { 'fill-color': tok('--land') } },
        { id: 'coast', type: 'line', source: 'land', paint: { 'line-color': tok('--coast'), 'line-width': 1.3 } },
        { id: 'routes', type: 'line', source: 'routes', layout: { 'line-cap': 'round', 'line-join': 'round' }, paint: { 'line-color': tok('--route-faint'), 'line-width': 1.6, 'line-opacity': 0.75, 'line-dasharray': [2, 2] } },
        { id: 'routes-sel', type: 'line', source: 'routes', filter: ['==', ['get', 'day'], ''], layout: { 'line-cap': 'round', 'line-join': 'round' }, paint: { 'line-color': tok('--route'), 'line-width': 3.2 } }
      ]
    };
  }

  function restyle() {
    if (mapMode === 'svg') { svgRender(); return; }
    if (mapMode !== 'gl' || !map || !map.getLayer('sea')) return;
    map.setPaintProperty('sea', 'background-color', tok('--sea'));
    map.setPaintProperty('waterlines', 'line-color', tok('--coast'));
    map.setPaintProperty('land', 'fill-color', tok('--land'));
    map.setPaintProperty('coast', 'line-color', tok('--coast'));
    map.setPaintProperty('routes', 'line-color', tok('--route-faint'));
    map.setPaintProperty('routes-sel', 'line-color', tok('--route'));
    if (map.getLayer('hillshade')) {
      map.setPaintProperty('hillshade', 'hillshade-shadow-color', tok('--hs-shadow'));
      map.setPaintProperty('hillshade', 'hillshade-highlight-color', tok('--hs-light'));
      map.setPaintProperty('hillshade', 'hillshade-accent-color', tok('--hs-shadow'));
    }
  }
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', restyle);
  new MutationObserver(restyle).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });

  var SVG_PLANE = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M21 15.5v-2l-8-5V3.5a1.5 1.5 0 0 0-3 0V8.5l-8 5v2l8-2.5V18l-2 1.5V21l3.5-1 3.5 1v-1.5L13 18v-5z"/></svg>';
  var SVG_HOME = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3 2 11h3v9h5v-6h4v6h5v-9h3z"/></svg>';

  function markerEl(id) {
    var p = places[id];
    var el = document.createElement('button');
    el.type = 'button';
    el.className = 'mk ' + (p.hub ? 'mk-hub' : 'mk-stop') + ' isl-' + p.isl;
    el.setAttribute('aria-label', p.name);
    var inner = document.createElement('span');
    inner.className = 'mk-in';
    if (p.hub) inner.innerHTML = p.hub === 'air' ? SVG_PLANE : SVG_HOME;
    else inner.textContent = String(dayById[p.days[0]].n);
    el.appendChild(inner);
    el.addEventListener('click', function (ev) { ev.stopPropagation(); openPopup(id); });
    return el;
  }

  function openPopup(id) {
    var p = places[id];
    var html = '<div class="pop"><p class="pop-t">' + esc(p.name) + '</p>' + p.days.map(function (d) {
      var D = dayById[d];
      return '<button type="button" class="pop-day" data-goto="' + d + '">J' + D.n + ' · ' + esc(D.short) + ' · ' + esc(D.title) + '</button>';
    }).join('') + '</div>';
    if (!popup) popup = new window.maplibregl.Popup({ offset: 16, maxWidth: '260px', closeButton: true });
    popup.setLngLat([p.lon, p.lat]).setHTML(html).addTo(map);
  }

  function addLabels() {
    TRIP.labels.forEach(function (l) {
      var el = document.createElement('div');
      el.className = 'lbl lbl-' + l.k;
      el.textContent = l.t;
      new window.maplibregl.Marker({ element: el, anchor: l.k === 'peak' ? 'left' : 'center' }).setLngLat([l.lon, l.lat]).addTo(map);
    });
  }

  function zoomClass() {
    if (!map) return;
    var z = map.getZoom();
    shell.classList.toggle('map-far', z < 8.6);
    shell.classList.toggle('map-near', z >= 8.6);
  }

  function markSelection() {
    var d = selected ? dayById[selected] : null;
    var on = {};
    if (d) d.pts.forEach(function (p) { on[p] = true; });
    if (mapMode === 'gl') {
      Object.keys(markers).forEach(function (id) {
        var el = markers[id];
        el.classList.toggle('is-on', !!(d && on[id]));
        el.classList.toggle('is-off', !!(d && !on[id]));
      });
      if (map.getLayer('routes-sel')) map.setFilter('routes-sel', ['==', ['get', 'day'], selected || '']);
    } else if (mapMode === 'svg') {
      svgRender();
    }
  }

  function viewForDay(d) {
    if (d.isl === 'reunion' || d.isl === 'maurice') return d.isl;
    if (d.isl === 'both') return 'both';
    return d.n === 1 ? 'reunion' : 'both';
  }

  function setPressed() {
    $$('[data-view]').forEach(function (b) { b.setAttribute('aria-pressed', String(b.dataset.view === view)); });
  }

  function camera(bounds, maxZoom) {
    var wide = mqWide.matches;
    var pad = wide ? { top: 70, bottom: 50, left: 50, right: 50 } : { top: 58, bottom: 30, left: 26, right: 26 };
    var cam = map.cameraForBounds(bounds, { padding: pad, maxZoom: maxZoom || 12.2 });
    return cam;
  }

  /* Décalage de zoom en vue 3D : la vue inclinée tasse les îles entières, on peut rapprocher ;
     pour une journée, on recule un peu pour garder les marqueurs du premier plan dans le cadre. */
  function go(bounds, maxZoom, tiltOffset) {
    if (mapMode === 'svg') { svgRender(); return; }
    if (mapMode !== 'gl') return;
    var cam = camera(bounds, maxZoom);
    if (!cam) return;
    map.flyTo({ center: cam.center, zoom: cam.zoom + (tilted ? (tiltOffset == null ? -0.2 : tiltOffset) : 0), pitch: tilted ? PITCH : 0, bearing: 0, duration: reduceMotion ? 0 : 1400, essential: true });
  }

  function setView(v, move) {
    view = v;
    setPressed();
    if (move !== false) go(VIEWS[v], undefined, v === 'both' ? 0.2 : 0.45);
  }

  function flyToDay(d) {
    view = viewForDay(d);
    setPressed();
    markSelection();
    var pts = ptsOf(d);
    if (!pts.length) { go(VIEWS[view], undefined, view === 'both' ? 0.2 : 0.45); return; }
    var minx = 180, miny = 90, maxx = -180, maxy = -90;
    pts.forEach(function (p) { minx = Math.min(minx, p[0]); maxx = Math.max(maxx, p[0]); miny = Math.min(miny, p[1]); maxy = Math.max(maxy, p[1]); });
    var b = [[minx, miny], [maxx, maxy]];
    if (maxx - minx < 0.02 && maxy - miny < 0.02) b = [[minx - 0.03, miny - 0.03], [maxx + 0.03, maxy + 0.03]];
    go(d.isl === 'both' ? VIEWS.both : b, 12, d.isl === 'both' ? 0.2 : -0.2);
  }

  function hasWebGL() {
    try { var c = document.createElement('canvas'); return !!(c.getContext('webgl2') || c.getContext('webgl')); } catch (e) { return false; }
  }
  function loadScript(src) {
    return new Promise(function (res, rej) {
      var s = document.createElement('script'); s.src = src; s.async = true;
      s.onload = res; s.onerror = rej; document.head.appendChild(s);
    });
  }

  var LOCALE = {
    'NavigationControl.ResetBearing': 'Réorienter vers le nord', 'NavigationControl.ZoomIn': 'Zoomer', 'NavigationControl.ZoomOut': 'Dézoomer',
    'AttributionControl.ToggleAttribution': 'Afficher les crédits', 'Popup.Close': 'Fermer', 'ScaleControl.Meters': 'm', 'ScaleControl.Kilometers': 'km',
    'CooperativeGesturesHandler.MobileHelpText': 'Utilisez deux doigts pour déplacer la carte'
  };

  function initGL() {
    var loaded = false;
    try {
      map = new window.maplibregl.Map({
        container: 'map', style: buildStyle(), bounds: VIEWS.both, fitBoundsOptions: { padding: 30 },
        pitch: tilted ? PITCH : 0, maxPitch: 72, attributionControl: false, locale: LOCALE,
        maxBounds: [[53.6, -23.2], [59.6, -18.4]], dragRotate: true, touchPitch: true
      });
    } catch (e) { svgInit(); return; }
    mapMode = 'gl';
    map.addControl(new window.maplibregl.NavigationControl({ showZoom: mqWide.matches, visualizePitch: true }), 'bottom-right');
    map.addControl(new window.maplibregl.ScaleControl({ unit: 'metric', maxWidth: 90 }), 'bottom-right');
    map.on('load', function () {
      loaded = true;
      $('#map-msg').hidden = true;
      Object.keys(places).forEach(function (id) {
        var el = markerEl(id);
        markers[id] = el;
        new window.maplibregl.Marker({ element: el, anchor: 'center' }).setLngLat([places[id].lon, places[id].lat]).addTo(map);
      });
      addLabels();
      zoomClass();
      restyle();
      if (reliefOn) enableRelief();
      if (selected) flyToDay(dayById[selected]); else markSelection();
    });
    map.on('zoom', zoomClass);
    setTimeout(function () {
      if (!loaded) { try { map.remove(); } catch (e) { } map = null; svgInit(); }
    }, 12000);
  }

  /* Relief 3D (Copernicus DEM GLO-90) avec ombrage. Sans tuiles, la carte reste en vue inclinée 2D. */
  var reliefOn = false;
  var EXAG = 1.4;
  function enableRelief() {
    var src = { type: 'raster-dem', tiles: ['relief://{z}/{x}/{y}'], tileSize: 256, encoding: 'terrarium', minzoom: 5, maxzoom: 12 };
    try {
      map.addSource('dem', src);
      map.addSource('dem-hs', src);
      map.addLayer({ id: 'hillshade', type: 'hillshade', source: 'dem-hs', paint: {
        'hillshade-exaggeration': 0.5, 'hillshade-illumination-direction': 315,
        'hillshade-shadow-color': tok('--hs-shadow'), 'hillshade-highlight-color': tok('--hs-light'), 'hillshade-accent-color': tok('--hs-shadow')
      } }, 'coast');
      map.setTerrain({ source: 'dem', exaggeration: EXAG });
    } catch (e) { disableRelief(); }
  }
  function disableRelief() {
    try { map.setTerrain(null); } catch (e) { }
    try { if (map.getLayer('hillshade')) map.removeLayer('hillshade'); } catch (e) { }
  }

  /* Repli SVG si WebGL ou la bibliothèque ne sont pas disponibles */
  function svgInit() {
    mapMode = 'svg';
    $('#map-msg').hidden = true;
    var tilt = $('#btn-tilt'); if (tilt) tilt.hidden = true;
    var host = document.createElement('div');
    host.className = 'svg-map'; host.id = 'svg-map';
    $('#map').appendChild(host);
    svgRender();
  }
  function svgIsland(k) {
    var S = GEO.svg[k], P = S.proj;
    var proj = function (lon, lat) { return [((lon * P.k) - P.minx) * P.scale, (P.maxy - lat) * P.scale]; };
    var d = selected ? dayById[selected] : null;
    var on = {}; if (d) d.pts.forEach(function (p) { on[p] = true; });
    var out = '<svg viewBox="0 0 ' + S.w + ' ' + S.h + '" role="img" aria-label="' + (k === 'reunion' ? 'La Réunion' : 'Maurice') + '">';
    out += '<path d="' + S.d + '" fill="' + tok('--land') + '" stroke="' + tok('--coast') + '" stroke-width="1.5"/>';
    if (d && d.pts.length > 1 && d.pts.every(function (p) { return places[p].isl === k; })) {
      var line = routeCoords(d).map(function (c) { var q = proj(c[0], c[1]); return q[0].toFixed(1) + ',' + q[1].toFixed(1); }).join(' ');
      out += '<polyline points="' + line + '" fill="none" stroke="' + tok('--route') + '" stroke-width="3" stroke-linecap="round"/>';
    }
    Object.keys(places).forEach(function (id) {
      var p = places[id]; if (p.isl !== k) return;
      var q = proj(p.lon, p.lat);
      var col = p.hub ? tok('--ink') : (k === 'reunion' ? tok('--run') : tok('--mru'));
      var op = d && !on[id] ? 0.35 : 1;
      var r = d && on[id] ? 13 : 11;
      var dayTarget = p.days[0] || (d && on[id] ? d.id : '');
      out += '<g opacity="' + op + '"' + (dayTarget ? ' data-goto="' + dayTarget + '" style="cursor:pointer"' : '') + '><title>' + esc(p.name) + '</title><circle cx="' + q[0].toFixed(1) + '" cy="' + q[1].toFixed(1) + '" r="' + r + '" fill="' + col + '" stroke="' + tok('--surface') + '" stroke-width="2"/>' +
        '<text x="' + q[0].toFixed(1) + '" y="' + (q[1] + 4).toFixed(1) + '" text-anchor="middle" font-family="IBM Plex Mono, monospace" font-size="11" font-weight="600" fill="' + tok('--paper') + '">' + (p.hub ? (p.hub === 'air' ? 'A' : 'B') : dayById[p.days[0]].n) + '</text></g>';
    });
    return out + '</svg>';
  }
  function svgRender() {
    var host = $('#svg-map'); if (!host) return;
    var ks = view === 'both' ? ['reunion', 'maurice'] : [view];
    host.innerHTML = ks.map(svgIsland).join('');
  }

  var mapStarted = false;
  function ensureMap() {
    if (!mapStarted) { mapStarted = true; initMap(); return; }
    if (map && mapMode === 'gl') setTimeout(function () { map.resize(); }, 30);
  }
  function initMap() {
    if (!hasWebGL()) { svgInit(); return; }
    loadScript(LIBS[0]).catch(function () { return loadScript(LIBS[1]); }).then(function () {
      if (!window.maplibregl) { svgInit(); return; }
      try { reliefOn = registerRelief(); } catch (e) { reliefOn = false; }
      initGL();
    }).catch(function () { svgInit(); });
  }

  /* Boutons de la carte */
  var tiltBtn = $('#btn-tilt');
  tiltBtn.setAttribute('aria-pressed', String(tilted));
  tiltBtn.addEventListener('click', function () {
    tilted = !tilted;
    tiltBtn.setAttribute('aria-pressed', String(tilted));
    store('rm2027-tilt', tilted ? 'tilt' : 'flat');
    if (mapMode === 'gl') map.easeTo({ pitch: tilted ? PITCH : 0, duration: reduceMotion ? 0 : 600 });
  });

  function toggleMap(force) {
    var prog = $('#prog');
    var show = typeof force === 'boolean' ? force : prog.classList.contains('map-off');
    prog.classList.toggle('map-off', !show);
    var b = $('#btn-maptoggle');
    b.setAttribute('aria-expanded', String(show));
    b.textContent = show ? 'Masquer la carte' : 'Afficher la carte';
    if (show && map && mapMode === 'gl') setTimeout(function () { map.resize(); }, 30);
  }
  $('#btn-maptoggle').addEventListener('click', function () { toggleMap(); });
  mqWide.addEventListener('change', function () { if (map && mapMode === 'gl') setTimeout(function () { map.resize(); }, 50); });

  /* Démarrage */
  applyStatuses();
  initToday();
  initDb();
  route();
})();
