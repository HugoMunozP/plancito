/* =========================================================
   Plancito · página «Para una cita»
   - Arriba: ¿Qué le gusta a ella? + presupuesto → opciones con precio para dos
   - Abajo: ranking de 15 lugares (lo eliges tú en admin.html → data/manual/ranking.json)
   ========================================================= */
(function () {
  'use strict';

  const PERSONAS = 2;
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const soles = (v) => v === 0 ? 'Gratis' : 'S/ ' + (Math.round(v) === v ? v : v.toFixed(2));
  const linea = (d) => '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + d + '</svg>';
  const normal = (s) => String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const fmtISO = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Lima' });
  const hoy = () => fmtISO.format(new Date());
  const sumarDias = (iso, n) => { const d = new Date(iso + 'T12:00:00Z'); d.setUTCDate(d.getUTCDate() + n); return d.toISOString().slice(0, 10); };
  const DIAS = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
  const MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'set', 'oct', 'nov', 'dic'];
  const fecha = (iso) => { const d = new Date(iso + 'T12:00:00Z'); return DIAS[d.getUTCDay()] + ' ' + d.getUTCDate() + ' ' + MESES[d.getUTCMonth()]; };

  const GUSTOS = [
    ['cenar', 'Cena para sorprenderla', 'Los restaurantes mejor calificados', '<path d="M8 3v18M5 3v6a3 3 0 0 0 6 0V3"/><path d="M17 21V3c-2 1-3 4-3 7h3"/>'],
    ['bailar', 'Le gusta bailar', 'Bares y fiestas', '<path d="M9 18V5l11-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="17" cy="16" r="3"/>'],
    ['leer', 'Le encanta leer y lo cultural', 'Museos, teatro, expos y ferias', '<path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2z"/><path d="M4 19V5"/>'],
    ['aire', 'Sorprenderla al aire libre', 'Full days, paseos y planes gratis', '<path d="M12 3l6 9h-4l4 6H6l4-6H6z"/><path d="M12 18v4"/>'],
    ['cafe', 'Es de cafecito y conversar', 'Cafés con buena nota', '<path d="M4 9h12v5a5 5 0 0 1-5 5H9a5 5 0 0 1-5-5z"/><path d="M16 11h2a2 2 0 0 1 0 4h-2"/>'],
    ['reir', 'Le encanta reír', 'Stand up y comedia', '<circle cx="12" cy="12" r="9"/><path d="M8 14s1.5 2 4 2 4-2 4-2M9 9h.01M15 9h.01"/>']
  ];
  const TOPES = [['todos', 'Todos'], ['gratis', 'Gratis'], ['100', 'Hasta S/ 100'], ['200', 'Hasta S/ 200'], ['mas', 'Más de S/ 200']];
  const E = { gusto: 'cenar', tope: 'todos' };
  let LUGARES = [];
  let EVENTOS = [];
  let RANKING = [];

  // ---------- likes (por ahora en este navegador) ----------
  const VOTOS_KEY = 'plancito_votos';
  let VOTOS = {};
  try { VOTOS = JSON.parse(localStorage.getItem(VOTOS_KEY) || '{}') || {}; } catch (e) { VOTOS = {}; }
  const claveDe = (p) => p.url || p.nombre;
  function votar(clave, v) {
    VOTOS[clave] = VOTOS[clave] === v ? 0 : v;
    try { localStorage.setItem(VOTOS_KEY, JSON.stringify(VOTOS)); } catch (e) { /* sin almacenamiento */ }
  }

  // ---------- datos ----------
  const json = (u, def) => fetch(u, { cache: 'no-cache' }).then((r) => r.ok ? r.json() : def).catch(() => def);
  Promise.all([json('data/eventos.json', {}), json('data/lugares.json', {}), json('data/manual/eventos.json', []),
    json('data/manual/lugares.json', []), json('data/manual/ranking.json', [])]).then(([ev, lu, evm, lum, rk]) => {
    const lugar = (l) => ({
      nombre: l.nombre, lugar: l.lugar, categoria: l.categoria, tipo: l.tipo, precio: l.precio,
      calificacion: l.calificacion || 0, resenas: l.resenas || 0, imagen: l.imagen_local || l.imagen || '',
      url: l.url, fuente: l.fuente || 'Plancito', salidas: l.salidas || '', fotoAutor: l.foto_autor || '', siempre: true
    });
    LUGARES = (Array.isArray(lum) ? lum : []).filter((l) => !l.ejemplo).concat(lu.lugares || []).map(lugar)
      .filter((p) => p.nombre && typeof p.precio === 'number');
    const h = hoy();
    EVENTOS = (ev.eventos || []).concat((Array.isArray(evm) ? evm : []).map((e) => Object.assign({ fuente: 'Plancito' }, e)))
      .filter((e) => e.nombre && typeof e.precio === 'number' && (e.fin || e.inicio) >= h)
      .map((e) => ({
        nombre: e.nombre, lugar: e.lugar, categoria: e.categoria, tipo: e.tipo, precio: e.precio,
        imagen: e.imagen_local || e.imagen || '', url: e.url, fuente: e.fuente, inicio: e.inicio, fin: e.fin || e.inicio,
        hora: e.hora || '', siempre: false, calificacion: 0, resenas: 0
      }));
    RANKING = Array.isArray(rk) ? rk : [];
    render();
  });

  // ---------- reglas ----------
  const total = (p) => p.precio * PERSONAS;
  function sorpresaAuto(p) {
    const r = p.calificacion || 0;
    const n = p.resenas || 0;
    const base = r ? (n * r + 300 * 4.3) / (n + 300) : 4.45;
    return Math.max(60, Math.min(100, Math.round(70 + (base - 4.0) * 30 * 1.25)));
  }
  const porNota = (a, b) => (sorpresaAuto(b) - sorpresaAuto(a)) || (b.resenas - a.resenas) || (a.precio - b.precio);
  const porFecha = (a, b) => String(a.inicio).localeCompare(String(b.inicio)) || (a.precio - b.precio);
  const MES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'set', 'octubre', 'noviembre', 'diciembre'][+hoy().slice(5, 7) - 1];
  const aireBueno = (p) => !/privad/i.test(p.nombre) && !(/(enero|febrero|marzo|abril|mayo|junio|julio|agosto|setiembre|septiembre|octubre|noviembre|diciembre)/i.test(p.salidas || '') && !normal(p.salidas).includes(MES));
  const en14 = (p) => { const lim = sumarDias(hoy(), 14); return p.inicio <= lim; };

  function ranking() {
    if (RANKING.length) {
      const porClave = new Map(LUGARES.map((p) => [claveDe(p), p]));
      const porNombre = new Map(LUGARES.map((p) => [normal(p.nombre), p]));
      return RANKING.map((r) => {
        const p = porClave.get(r.clave) || porNombre.get(normal(r.nombre));
        return p ? Object.assign({}, p, { pct: Number(r.pct) || sorpresaAuto(p) }) : null;
      }).filter(Boolean).slice(0, 15);
    }
    const rest = LUGARES.filter((p) => p.tipo === 'restaurantes').sort(porNota).slice(0, 10);
    const aire = LUGARES.filter((p) => p.tipo === 'aire' && aireBueno(p)).sort(porNota).slice(0, 5);
    return rest.concat(aire).sort(porNota).map((p) => Object.assign({}, p, { pct: sorpresaAuto(p) }));
  }

  function opciones() {
    const tope = (p) => {
      const t = total(p);
      return E.tope === 'gratis' ? t === 0 : E.tope === '100' ? t <= 100 : E.tope === '200' ? t <= 200 : E.tope === 'mas' ? t > 200 : true;
    };
    const lugares = LUGARES.filter(tope);
    const eventos = EVENTOS.filter((p) => en14(p) && tope(p));
    const txt = (p) => normal(p.categoria + ' ' + p.nombre);
    switch (E.gusto) {
      case 'cenar': return lugares.filter((p) => p.tipo === 'restaurantes').sort(porNota).slice(0, 9);
      case 'bailar': return lugares.filter((p) => p.tipo === 'bar').sort(porNota).slice(0, 6)
        .concat(eventos.filter((p) => p.tipo === 'bar' || /fiesta|discoteca|salsa|baile/.test(txt(p))).sort(porFecha).slice(0, 3));
      case 'leer': return eventos.filter((p) => p.tipo === 'cultural' && /literatura|libro|feria|exposicion|museo|teatro|cultura|arte|poesia|danza/.test(txt(p))).sort(porFecha).slice(0, 9);
      case 'aire': return lugares.filter((p) => p.tipo === 'aire' && aireBueno(p)).sort((a, b) => (a.precio - b.precio) || porNota(a, b)).slice(0, 6)
        .concat(eventos.filter((p) => p.tipo === 'aire').sort(porFecha).slice(0, 3));
      case 'cafe': return lugares.filter((p) => p.tipo === 'cafe').sort(porNota).slice(0, 9);
      case 'reir': return eventos.filter((p) => /stand ?up|comedia|humor/.test(txt(p))).sort(porFecha).slice(0, 9);
      default: return [];
    }
  }

  // ---------- vista ----------
  const enlace = (p) => p.url ? ' href="' + esc(p.url) + '" target="_blank" rel="noopener sponsored"' : '';
  const foto = (p) => p.imagen
    ? '<img src="' + esc(p.imagen) + '" alt="" loading="lazy" referrerpolicy="no-referrer">'
    : '<span class="sin-foto">' + esc(p.categoria || '') + '</span>';
  const boton = (p) => p.fuente === 'Google Maps' ? 'Ver en Google Maps' : (p.siempre || p.precio === 0 ? 'Ver en ' + p.fuente : 'Ver y comprar en ' + p.fuente);

  function tarjeta(p) {
    const cuando = p.siempre ? (p.salidas ? 'Salidas: ' + p.salidas : 'Toda la semana') : (p.inicio === p.fin ? fecha(p.inicio) : 'Hasta el ' + fecha(p.fin)) + (p.hora ? ' · ' + p.hora : '');
    return '<article class="tarjeta"><a class="tarjeta-link"' + enlace(p) + ' aria-label="' + esc(p.nombre + ' · ' + boton(p)) + '"></a>' +
      '<div class="foto"><div class="portada-plan">' + foto(p) + '</div>' +
      '<span class="cat" style="background:#FFE1EC;color:#9D174D">' + esc(p.categoria || '') + '</span>' +
      '<span class="sticker">' + (total(p) ? soles(total(p)) : 'Gratis') + '</span></div>' +
      '<div class="cuerpo"><h4>' + esc(p.nombre) + '</h4>' +
      '<span class="cuando">' + esc(cuando) + (p.lugar ? ' · ' + esc(p.lugar) : '') + '</span>' +
      (p.calificacion ? '<span class="estrellas"><b>★ ' + p.calificacion.toFixed(1) + '</b>' + (p.resenas ? ' <small>(' + p.resenas.toLocaleString('es-PE') + ' reseñas)</small>' : '') + '</span>' : '') +
      '<span class="precio-dos">' + (total(p) ? soles(total(p)) + ' para dos' : 'Gratis') + '</span>' +
      '<span class="ir">' + esc(boton(p)) + ' →</span>' +
      (p.fotoAutor ? '<small class="credito">Foto: ' + esc(p.fotoAutor) + ' · Google Maps</small>' : '') + '</div></article>';
  }

  function filaRanking(p, i) {
    const v = VOTOS[claveDe(p)] || 0;
    const k = esc(claveDe(p));
    return '<li class="rk-item">' +
      '<span class="rk-num">' + (i + 1) + '</span>' +
      '<a class="rk-foto"' + enlace(p) + ' aria-label="' + esc(p.nombre) + '"><div class="portada-plan">' + foto(p) + '</div></a>' +
      '<div class="rk-info"><b>' + esc(p.nombre) + '</b>' +
      '<span>' + esc(p.categoria || '') + (p.lugar ? ' · ' + esc(p.lugar) : '') + (p.calificacion ? ' · ★ ' + p.calificacion.toFixed(1) : '') + '</span>' +
      '<span class="rk-precio">' + (total(p) ? soles(total(p)) + ' para dos' : 'Gratis') + '</span>' +
      '<div class="rk-barra" aria-hidden="true"><i style="width:' + p.pct + '%"></i></div></div>' +
      '<div class="rk-lado"><span class="rk-pct"><b>' + p.pct + '%</b><small>la sorprende</small></span>' +
      '<div class="rk-votos" role="group" aria-label="¿Te gustó ' + esc(p.nombre) + '?">' +
      '<button type="button" class="rk-voto" aria-pressed="' + (v === 1) + '" aria-label="Me gustó" data-voto="1" data-clave="' + k + '">' + linea('<path d="M7 11v9H4v-9zM7 11l4-8a2 2 0 0 1 3 2l-1 4h5a2 2 0 0 1 2 2.3l-1.2 7A2 2 0 0 1 16.8 20H7"/>') + '</button>' +
      '<button type="button" class="rk-voto no" aria-pressed="' + (v === -1) + '" aria-label="No me gustó" data-voto="-1" data-clave="' + k + '">' + linea('<path d="M17 13V4h3v9zM17 13l-4 8a2 2 0 0 1-3-2l1-4H6a2 2 0 0 1-2-2.3l1.2-7A2 2 0 0 1 7.2 4H17"/>') + '</button>' +
      '</div></div></li>';
  }

  function render() {
    $('gustos').innerHTML = GUSTOS.map(([k, t, d, ic]) => '<button type="button" class="gusto" aria-pressed="' + (E.gusto === k) + '" data-gusto="' + k + '">' + linea(ic) + '<span><b>' + t + '</b><small>' + d + '</small></span></button>').join('');
    $('topes').innerHTML = '<span class="mini-etiqueta">Presupuesto para dos</span>' + TOPES.map(([k, t]) => '<button type="button" class="chip' + (k === 'gratis' ? ' chip-gratis' : '') + '" aria-pressed="' + (E.tope === k) + '" data-tope="' + k + '">' + t + '</button>').join('');
    const g = GUSTOS.find((x) => x[0] === E.gusto);
    const ops = opciones();
    $('opciones').innerHTML = '<h3 class="cita-sub">' + esc(g[1]) + ' · ' + ops.length + (ops.length === 1 ? ' opción' : ' opciones') + '</h3>' +
      (ops.length ? '<div class="grilla cita-grilla">' + ops.map(tarjeta).join('') + '</div>'
        : '<div class="vacio">No hay opciones con ese presupuesto. Prueba con «Todos».</div>');
    $('ranking').innerHTML = ranking().map(filaRanking).join('');
  }

  document.addEventListener('click', (ev) => {
    const g = ev.target.closest('[data-gusto]');
    const t = ev.target.closest('[data-tope]');
    const v = ev.target.closest('[data-voto]');
    if (g) { E.gusto = g.dataset.gusto; render(); return; }
    if (t) { E.tope = t.dataset.tope; render(); return; }
    if (v) {
      votar(v.dataset.clave, +v.dataset.voto);
      render();
      const b = document.querySelector('[data-voto="' + v.dataset.voto + '"][data-clave="' + CSS.escape(v.dataset.clave) + '"]');
      if (b) b.focus();
    }
  });
  document.addEventListener('error', (ev) => {
    const img = ev.target;
    if (img.tagName === 'IMG' && img.closest('.portada-plan')) img.outerHTML = '<span class="sin-foto"></span>';
  }, true);
})();
